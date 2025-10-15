"""
Feature Engineering Pipeline with Context Enrichment

Builds comprehensive feature sets from raw prop data, including:
- Player performance features (rolling averages, trends)
- Matchup-specific features (opponent defense, pace)
- Contextual features (weather, venue, rest)
- Market features (line movement, odds value)
- Derived features (volatility, ceiling/floor scores)
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from redis.asyncio import Redis

from src.config import settings
from src.db import get_redis
from src.ingest import (
    SleeperAPI,
    InjuriesAPI,
    WeatherAPI,
    BaselineStats,
)
from src.features.transformers import FeatureTransformer
from src.features.leakage_checks import LeakageDetector

logger = logging.getLogger(__name__)


class FeaturePipelineError(Exception):
    """Custom exception for feature pipeline errors"""
    pass


class FeaturePipeline:
    """
    Main feature engineering pipeline for prop betting

    Orchestrates data fetching, feature computation, transformation,
    and validation to produce ML-ready feature sets.

    Attributes:
        cache_ttl: Redis cache TTL in seconds (default: 12 hours)
        enable_cache: Whether to use Redis caching
    """

    CACHE_TTL = 43200  # 12 hours

    def __init__(
        self,
        sleeper_client: Optional[SleeperAPI] = None,
        injuries_client: Optional[InjuriesAPI] = None,
        weather_client: Optional[WeatherAPI] = None,
        baseline_stats: Optional[BaselineStats] = None,
        enable_cache: bool = True,
    ):
        """
        Initialize feature pipeline with data clients

        Args:
            sleeper_client: Sleeper API client
            injuries_client: Injuries API client
            weather_client: Weather API client
            baseline_stats: Baseline stats provider
            enable_cache: Enable Redis caching
        """
        self.sleeper = sleeper_client or SleeperAPI()
        self.injuries = injuries_client or InjuriesAPI()
        self.weather = weather_client or WeatherAPI()
        self.baseline = baseline_stats or BaselineStats(sleeper_client=self.sleeper)
        self.enable_cache = enable_cache

        # Initialize transformer and leakage detector
        self.transformer = FeatureTransformer()
        self.leakage_detector = LeakageDetector()

        # Track owned clients for cleanup
        self._owned_sleeper = sleeper_client is None
        self._owned_injuries = injuries_client is None
        self._owned_weather = weather_client is None
        self._owned_baseline = baseline_stats is None

    async def close(self):
        """Close all client connections"""
        if self._owned_sleeper:
            await self.sleeper.close()
        if self._owned_injuries:
            await self.injuries.close()
        if self._owned_weather:
            await self.weather.close()
        if self._owned_baseline:
            await self.baseline.close()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def _get_cached(self, redis: Redis, cache_key: str) -> Optional[pd.DataFrame]:
        """Get cached DataFrame from Redis"""
        try:
            import pickle
            cached = await redis.get(cache_key)
            if cached:
                logger.info(f"Feature cache HIT: {cache_key}")
                return pickle.loads(cached)
            logger.info(f"Feature cache MISS: {cache_key}")
        except Exception as e:
            logger.warning(f"Feature cache read error: {e}")
        return None

    async def _set_cached(
        self,
        redis: Redis,
        cache_key: str,
        df: pd.DataFrame,
        ttl: int,
    ):
        """Set DataFrame in Redis cache"""
        try:
            import pickle
            await redis.setex(cache_key, ttl, pickle.dumps(df))
            logger.debug(f"Cached features: {cache_key} (TTL: {ttl}s)")
        except Exception as e:
            logger.warning(f"Feature cache write error: {e}")

    async def build_features(
        self,
        props: List[Dict[str, Any]],
        week: int,
        league: str = "nfl",
        season: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Build complete feature set for given props

        Args:
            props: List of prop dictionaries with player, stat_type, line, etc.
            week: Week number for context
            league: League identifier (default: 'nfl')
            season: Season year (defaults to current year)

        Returns:
            DataFrame with prop_id, player info, market info, and 50-100 features

        Example prop format:
            {
                "prop_id": "abc123",
                "player_id": "421",
                "player_name": "Patrick Mahomes",
                "team": "KC",
                "opponent": "LAC",
                "stat_type": "passing_yards",
                "line": 285.5,
                "odds": -110,
                "game_id": "game_001",
                "game_time": "2024-10-20T13:00:00Z",
                "is_home": true
            }
        """
        if not props:
            logger.warning("No props provided to build_features")
            return pd.DataFrame()

        season = season or str(datetime.utcnow().year)
        cache_key = f"features:pipeline:{league}:{season}:week_{week}:{len(props)}"

        redis = await get_redis()
        try:
            # Check cache
            if self.enable_cache:
                cached_df = await self._get_cached(redis, cache_key)
                if cached_df is not None:
                    return cached_df

            logger.info(f"Building features for {len(props)} props, {league} {season} week {week}")

            # Convert props to DataFrame for easier manipulation
            props_df = pd.DataFrame(props)

            # Validate required columns
            required_cols = ['prop_id', 'player_id', 'stat_type', 'line']
            missing_cols = [col for col in required_cols if col not in props_df.columns]
            if missing_cols:
                raise FeaturePipelineError(f"Missing required columns: {missing_cols}")

            # Build feature categories concurrently
            tasks = [
                self._build_player_features(props_df, season, week),
                self._build_matchup_features(props_df, season, week),
                self._build_context_features(props_df, season, week),
                self._build_market_features(props_df, season, week),
            ]

            player_features, matchup_features, context_features, market_features = await asyncio.gather(
                *tasks, return_exceptions=True
            )

            # Handle exceptions
            for i, result in enumerate([player_features, matchup_features, context_features, market_features]):
                if isinstance(result, Exception):
                    feature_type = ['player', 'matchup', 'context', 'market'][i]
                    logger.error(f"Failed to build {feature_type} features: {result}")
                    raise FeaturePipelineError(f"Failed to build {feature_type} features") from result

            # Merge all features
            features_df = props_df.copy()
            features_df = features_df.merge(player_features, on='prop_id', how='left')
            features_df = features_df.merge(matchup_features, on='prop_id', how='left')
            features_df = features_df.merge(context_features, on='prop_id', how='left')
            features_df = features_df.merge(market_features, on='prop_id', how='left')

            # Build derived features
            features_df = await self._build_derived_features(features_df, season, week)

            # Apply transformations
            features_df = self.transformer.handle_missing(features_df)
            features_df = self.transformer.normalize_features(features_df)
            features_df = self.transformer.encode_categoricals(features_df)
            features_df = self.transformer.create_interactions(features_df)

            # Validate for temporal leakage
            self.leakage_detector.check_temporal_leakage(features_df, week)
            self.leakage_detector.validate_feature_timestamps(features_df)

            # Add metadata
            features_df['feature_version'] = 'v1.0.0'
            features_df['computed_at'] = datetime.utcnow().isoformat()
            features_df['week'] = week
            features_df['season'] = season
            features_df['league'] = league

            # Cache results
            if self.enable_cache:
                await self._set_cached(redis, cache_key, features_df, self.CACHE_TTL)

            logger.info(f"Built {len(features_df)} feature rows with {len(features_df.columns)} columns")
            return features_df

        finally:
            await redis.close()

    async def _build_player_features(
        self,
        props_df: pd.DataFrame,
        season: str,
        week: int,
    ) -> pd.DataFrame:
        """
        Build player-specific features

        Features:
        - season_avg: Season average for stat
        - last_3_avg: Average over last 3 games
        - last_5_avg: Average over last 5 games
        - career_avg_vs_opponent: Career average against opponent
        - home_away_split: Performance split by home/away
        - usage_rate: Player usage rate
        - target_share: Target/touch share
        - days_rest: Days since last game
        - injury_status: Current injury status
        """
        logger.info("Building player features...")

        player_features = []

        for _, row in props_df.iterrows():
            prop_id = row['prop_id']
            player_id = row['player_id']
            stat_type = row['stat_type']
            team = row.get('team', '')
            opponent = row.get('opponent', '')
            is_home = row.get('is_home', True)

            features = {'prop_id': prop_id}

            try:
                # Get baseline statistics
                baseline = await self.baseline.get_player_baseline(
                    player_id=player_id,
                    stat_type=stat_type,
                    season=season,
                    current_week=week,
                    use_cache=True,
                )

                features['season_avg'] = baseline.get('season_avg')
                features['last_3_avg'] = baseline.get('avg_last_3')
                features['last_5_avg'] = baseline.get('avg_last_5')
                features['median_value'] = baseline.get('median')
                features['std_dev'] = baseline.get('std_dev')
                features['min_value'] = baseline.get('min')
                features['max_value'] = baseline.get('max')
                features['games_played'] = baseline.get('games_played', 0)

                # Get rolling averages
                rolling = await self.baseline.get_rolling_averages(
                    player_id=player_id,
                    stat_type=stat_type,
                    season=season,
                    current_week=week,
                    windows=[3, 5, 10],
                )

                features['last_10_avg'] = rolling.get('rolling_averages', {}).get('last_10')

                # Get player info
                player_info = await self.sleeper.get_player_by_id(player_id, use_cache=True)
                if player_info:
                    features['position'] = player_info.get('position', '')
                    features['age'] = player_info.get('age')
                    features['years_exp'] = player_info.get('years_exp')
                    features['height'] = player_info.get('height')
                    features['weight'] = player_info.get('weight')

                # Calculate home/away split
                # For simplicity, using a multiplier based on historical home/away performance
                if is_home:
                    features['home_away_split'] = 1.05  # Home advantage
                else:
                    features['home_away_split'] = 0.95  # Away disadvantage

                # Get injury status
                try:
                    injuries = await self.injuries.get_player_injuries(
                        player_name=row.get('player_name', ''),
                        league=row.get('league', 'nfl').upper(),
                        use_cache=True,
                    )

                    if injuries and len(injuries) > 0:
                        latest_injury = injuries[0]
                        status = latest_injury.get('status', 'healthy')
                        features['injury_status'] = status
                        # Encode injury status as numeric
                        injury_map = {
                            'healthy': 0,
                            'probable': 1,
                            'questionable': 2,
                            'doubtful': 3,
                            'out': 4,
                        }
                        features['injury_status_encoded'] = injury_map.get(status.lower(), 0)
                    else:
                        features['injury_status'] = 'healthy'
                        features['injury_status_encoded'] = 0
                except Exception as e:
                    logger.warning(f"Failed to fetch injury for {player_id}: {e}")
                    features['injury_status'] = 'unknown'
                    features['injury_status_encoded'] = 0

                # Calculate usage rate (placeholder - would need team-level data)
                features['usage_rate'] = 0.25  # Default moderate usage
                features['target_share'] = 0.20  # Default moderate target share

                # Calculate days rest (placeholder - would need game schedule data)
                features['days_rest'] = 7  # Default 1 week

                # Calculate career average vs opponent (simplified)
                # In production, this would query historical matchup data
                features['career_avg_vs_opponent'] = features.get('season_avg', 0) * 0.95

            except Exception as e:
                logger.warning(f"Failed to build player features for {prop_id}: {e}")
                # Set defaults for missing features
                features.update({
                    'season_avg': None,
                    'last_3_avg': None,
                    'last_5_avg': None,
                    'last_10_avg': None,
                    'median_value': None,
                    'std_dev': None,
                    'min_value': None,
                    'max_value': None,
                    'games_played': 0,
                    'home_away_split': 1.0,
                    'injury_status': 'unknown',
                    'injury_status_encoded': 0,
                    'usage_rate': 0.25,
                    'target_share': 0.20,
                    'days_rest': 7,
                    'career_avg_vs_opponent': None,
                })

            player_features.append(features)

        return pd.DataFrame(player_features)

    async def _build_matchup_features(
        self,
        props_df: pd.DataFrame,
        season: str,
        week: int,
    ) -> pd.DataFrame:
        """
        Build matchup-specific features

        Features:
        - opponent_defense_rank: Opponent's defensive rank for stat category
        - opponent_pace: Opponent's pace (possessions per game)
        - opponent_strength: Overall opponent strength rating
        - historical_matchup_avg: Historical average in this matchup
        """
        logger.info("Building matchup features...")

        matchup_features = []

        for _, row in props_df.iterrows():
            prop_id = row['prop_id']
            opponent = row.get('opponent', '')
            stat_type = row['stat_type']

            features = {'prop_id': prop_id}

            try:
                # Get opponent team stats
                if opponent:
                    team_stats = await self.baseline.get_team_stats(
                        team=opponent,
                        stat_category='defense',
                        season=season,
                        current_week=week,
                        use_cache=True,
                    )

                    # Calculate opponent defense rank (simplified)
                    # Lower yards allowed = better defense = higher rank
                    yards_allowed = team_stats.get('yards_per_game', 350)
                    features['opponent_defense_rank'] = max(1, min(32, int((450 - yards_allowed) / 10)))
                    features['opponent_yards_allowed_per_game'] = yards_allowed

                    # Get opponent pace stats
                    pace_stats = await self.baseline.get_team_stats(
                        team=opponent,
                        stat_category='offense',
                        season=season,
                        current_week=week,
                        use_cache=True,
                    )

                    features['opponent_pace'] = pace_stats.get('estimated_points_per_game', 24.0)
                    features['opponent_yards_per_game'] = pace_stats.get('yards_per_game', 350)

                    # Calculate opponent strength (composite score)
                    ppg = pace_stats.get('estimated_points_per_game', 24.0)
                    features['opponent_strength'] = min(1.0, max(0.0, ppg / 35.0))
                else:
                    features['opponent_defense_rank'] = 16  # League average
                    features['opponent_yards_allowed_per_game'] = 350
                    features['opponent_pace'] = 24.0
                    features['opponent_yards_per_game'] = 350
                    features['opponent_strength'] = 0.7

                # Historical matchup average (simplified - would query historical data)
                features['historical_matchup_avg'] = None

            except Exception as e:
                logger.warning(f"Failed to build matchup features for {prop_id}: {e}")
                features.update({
                    'opponent_defense_rank': 16,
                    'opponent_yards_allowed_per_game': 350,
                    'opponent_pace': 24.0,
                    'opponent_yards_per_game': 350,
                    'opponent_strength': 0.7,
                    'historical_matchup_avg': None,
                })

            matchup_features.append(features)

        return pd.DataFrame(matchup_features)

    async def _build_context_features(
        self,
        props_df: pd.DataFrame,
        season: str,
        week: int,
    ) -> pd.DataFrame:
        """
        Build contextual features

        Features:
        - venue_type: Dome, outdoor, altitude
        - weather: Temperature, wind, precipitation
        - game_total: Over/under total for game
        - spread: Point spread
        - primetime_game: Is primetime game (SNF, MNF, TNF)
        """
        logger.info("Building context features...")

        context_features = []

        for _, row in props_df.iterrows():
            prop_id = row['prop_id']
            game_id = row.get('game_id')
            team = row.get('team', '')

            features = {'prop_id': prop_id}

            try:
                # Determine venue type (simplified - would query venue database)
                # For now, using team-based heuristics
                dome_teams = ['DET', 'NO', 'ATL', 'DAL', 'MIN', 'LV', 'LAR']
                altitude_teams = ['DEN']

                if team in dome_teams:
                    features['venue_type'] = 'dome'
                    features['venue_type_encoded'] = 0
                elif team in altitude_teams:
                    features['venue_type'] = 'altitude'
                    features['venue_type_encoded'] = 2
                else:
                    features['venue_type'] = 'outdoor'
                    features['venue_type_encoded'] = 1

                # Get weather data for outdoor venues
                if features['venue_type'] == 'outdoor':
                    try:
                        # Would need venue location for real weather data
                        # For now, using placeholder
                        features['temperature'] = 65.0
                        features['wind_speed'] = 5.0
                        features['precipitation_prob'] = 0.1
                        features['humidity'] = 50.0
                    except Exception:
                        features['temperature'] = 65.0
                        features['wind_speed'] = 5.0
                        features['precipitation_prob'] = 0.1
                        features['humidity'] = 50.0
                else:
                    # Indoor games
                    features['temperature'] = 72.0
                    features['wind_speed'] = 0.0
                    features['precipitation_prob'] = 0.0
                    features['humidity'] = 45.0

                # Game total and spread (would come from odds providers)
                features['game_total'] = 47.5  # Average NFL total
                features['spread'] = 0.0  # Neutral

                # Determine if primetime game (simplified)
                game_time = row.get('game_time')
                if game_time:
                    try:
                        game_dt = pd.to_datetime(game_time)
                        hour = game_dt.hour
                        # Primetime is typically 8:20 PM ET or later
                        features['primetime_game'] = 1 if hour >= 20 else 0
                    except Exception:
                        features['primetime_game'] = 0
                else:
                    features['primetime_game'] = 0

            except Exception as e:
                logger.warning(f"Failed to build context features for {prop_id}: {e}")
                features.update({
                    'venue_type': 'outdoor',
                    'venue_type_encoded': 1,
                    'temperature': 65.0,
                    'wind_speed': 5.0,
                    'precipitation_prob': 0.1,
                    'humidity': 50.0,
                    'game_total': 47.5,
                    'spread': 0.0,
                    'primetime_game': 0,
                })

            context_features.append(features)

        return pd.DataFrame(context_features)

    async def _build_market_features(
        self,
        props_df: pd.DataFrame,
        season: str,
        week: int,
    ) -> pd.DataFrame:
        """
        Build market-specific features

        Features:
        - line_movement: Change in line over time
        - odds_value: Odds value assessment
        - book_consensus: Consensus across multiple books
        - line_vs_baseline: Line compared to player's baseline
        """
        logger.info("Building market features...")

        market_features = []

        for _, row in props_df.iterrows():
            prop_id = row['prop_id']
            line = row['line']
            odds = row.get('odds', -110)

            features = {'prop_id': prop_id}

            try:
                # Line movement (would track historical line changes)
                features['line_movement'] = 0.0  # No movement
                features['line_opened_at'] = line  # Would track opening line
                features['line_current'] = line

                # Convert odds to implied probability
                if odds < 0:
                    implied_prob = abs(odds) / (abs(odds) + 100)
                else:
                    implied_prob = 100 / (odds + 100)

                features['implied_probability'] = implied_prob
                features['odds'] = odds

                # Odds value (simplified - would compare to fair value model)
                features['odds_value'] = 0.0  # Neutral

                # Book consensus (would aggregate from multiple sources)
                features['book_consensus'] = line
                features['num_books'] = 1  # Single source

                # Line vs baseline (calculated after player features are available)
                features['line_vs_baseline'] = None

            except Exception as e:
                logger.warning(f"Failed to build market features for {prop_id}: {e}")
                features.update({
                    'line_movement': 0.0,
                    'line_opened_at': line,
                    'line_current': line,
                    'implied_probability': 0.5,
                    'odds': -110,
                    'odds_value': 0.0,
                    'book_consensus': line,
                    'num_books': 1,
                    'line_vs_baseline': None,
                })

            market_features.append(features)

        return pd.DataFrame(market_features)

    async def _build_derived_features(
        self,
        features_df: pd.DataFrame,
        season: str,
        week: int,
    ) -> pd.DataFrame:
        """
        Build derived features from existing features

        Features:
        - ewma_trend: Exponentially weighted moving average trend
        - volatility: Recent performance volatility
        - ceiling_score: 90th percentile performance
        - floor_score: 10th percentile performance
        - line_vs_baseline: Line compared to season average
        """
        logger.info("Building derived features...")

        # Calculate EWMA trend
        if 'last_3_avg' in features_df.columns and 'season_avg' in features_df.columns:
            features_df['ewma_trend'] = (
                features_df['last_3_avg'].fillna(features_df['season_avg']) -
                features_df['season_avg']
            ) / (features_df['season_avg'] + 1e-6)  # Avoid division by zero
        else:
            features_df['ewma_trend'] = 0.0

        # Volatility (standard deviation / mean)
        if 'std_dev' in features_df.columns and 'season_avg' in features_df.columns:
            features_df['volatility'] = features_df['std_dev'] / (features_df['season_avg'] + 1e-6)
        else:
            features_df['volatility'] = 0.0

        # Ceiling and floor scores (90th and 10th percentiles)
        if 'season_avg' in features_df.columns and 'std_dev' in features_df.columns:
            # Approximate percentiles using normal distribution
            features_df['ceiling_score'] = features_df['season_avg'] + 1.28 * features_df['std_dev']
            features_df['floor_score'] = features_df['season_avg'] - 1.28 * features_df['std_dev']
        else:
            features_df['ceiling_score'] = features_df.get('max_value', 0)
            features_df['floor_score'] = features_df.get('min_value', 0)

        # Line vs baseline
        if 'line' in features_df.columns and 'season_avg' in features_df.columns:
            features_df['line_vs_baseline'] = (
                features_df['line'] - features_df['season_avg']
            ) / (features_df['season_avg'] + 1e-6)
        else:
            features_df['line_vs_baseline'] = 0.0

        # Recent form indicator (trending up/down/stable)
        if 'last_3_avg' in features_df.columns and 'season_avg' in features_df.columns:
            def classify_form(row):
                if pd.isna(row.get('last_3_avg')) or pd.isna(row.get('season_avg')):
                    return 0  # Stable
                last_3 = row['last_3_avg']
                season = row['season_avg']
                if last_3 > season * 1.1:
                    return 1  # Trending up
                elif last_3 < season * 0.9:
                    return -1  # Trending down
                return 0  # Stable

            features_df['recent_form'] = features_df.apply(classify_form, axis=1)
        else:
            features_df['recent_form'] = 0

        # Pace-adjusted performance
        if 'season_avg' in features_df.columns and 'opponent_pace' in features_df.columns:
            # Normalize to league average pace (24.0 ppg)
            league_avg_pace = 24.0
            features_df['pace_adjusted_avg'] = (
                features_df['season_avg'] *
                (features_df['opponent_pace'] / league_avg_pace)
            )
        else:
            features_df['pace_adjusted_avg'] = features_df.get('season_avg', 0)

        # Rest advantage (more rest = potential advantage)
        if 'days_rest' in features_df.columns:
            features_df['rest_advantage'] = np.clip((features_df['days_rest'] - 4) / 10, -0.2, 0.2)
        else:
            features_df['rest_advantage'] = 0.0

        # Weather impact (for passing/outdoor stats)
        if 'wind_speed' in features_df.columns:
            # High wind negatively impacts passing
            features_df['weather_impact'] = -np.clip(features_df['wind_speed'] / 20, 0, 1) * 0.1
        else:
            features_df['weather_impact'] = 0.0

        return features_df

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on feature pipeline

        Returns:
            Health status dictionary
        """
        try:
            # Check all dependencies
            tasks = [
                self.sleeper.health_check(),
                self.injuries.health_check(),
                self.weather.health_check(),
                self.baseline.health_check(),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            all_healthy = all(
                isinstance(r, dict) and r.get('status') in ['healthy', 'degraded']
                for r in results
            )

            return {
                "service": "feature_pipeline",
                "status": "healthy" if all_healthy else "degraded",
                "dependencies": {
                    "sleeper_api": results[0].get('status') if isinstance(results[0], dict) else "unhealthy",
                    "injuries_api": results[1].get('status') if isinstance(results[1], dict) else "unhealthy",
                    "weather_api": results[2].get('status') if isinstance(results[2], dict) else "unhealthy",
                    "baseline_stats": results[3].get('status') if isinstance(results[3], dict) else "unhealthy",
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Feature pipeline health check failed: {e}")
            return {
                "service": "feature_pipeline",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

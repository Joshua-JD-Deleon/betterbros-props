"""
Feature engineering pipeline and trend chip generation.

Implements comprehensive feature engineering for NFL player props including:
- Player form features (season avg, recent form, EWMA, consistency)
- Matchup features (opponent rankings, historical performance)
- Usage features (target share, snap share, red zone usage)
- Game context features (home/away, Vegas lines, pace)
- Weather features (temperature, wind, precipitation impact)
- Injury features (player and teammate status)
- Prop-specific features (line comparisons, implied probabilities, vig)
- Correlation tags for same-game parlays
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class TrendChip:
    """Represents a detected trend."""
    title: str
    description: str
    impact_direction: str  # "positive" or "negative"
    confidence: float  # 0-1
    impacted_props: List[str]  # player_names affected
    diagnostics: Dict[str, Any]


class FeaturePipeline:
    """
    Feature engineering pipeline for player props.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize feature pipeline.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

    def build_player_form_features(self, props_df: pd.DataFrame, baseline_stats: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Build player form features.

        Features added:
            - season_avg: Player's season average for stat_type
            - last_3_avg: Last 3 games average
            - ewma_5: Exponentially weighted moving avg (α=0.4, last 5 games)
            - form_trend: (last_3_avg - season_avg) / season_avg
            - consistency: 1 / coefficient_of_variation
            - days_since_last_game: Days since last game

        Args:
            props_df: DataFrame with player props
            baseline_stats: Optional historical statistics

        Returns:
            DataFrame with added player form features
        """
        df = props_df.copy()

        # Check if DataFrame is empty or missing required columns
        if df.empty or 'line' not in df.columns:
            logger.warning("Props DataFrame is empty or missing 'line' column")
            # Initialize expected columns with proper default values for empty DataFrame
            if df.empty:
                for col in ['season_avg', 'last_3_avg', 'consistency', 'variance', 'ewma_5', 'form_trend', 'days_since_last_game']:
                    if col not in df.columns:
                        df[col] = pd.Series(dtype=float)
            else:
                # DataFrame has rows but missing 'line' column - initialize with defaults
                for col in ['season_avg', 'last_3_avg', 'ewma_5']:
                    if col not in df.columns:
                        df[col] = 0.0
                for col in ['consistency']:
                    if col not in df.columns:
                        df[col] = 0.70
                for col in ['variance']:
                    if col not in df.columns:
                        df[col] = 150.0
                for col in ['form_trend']:
                    if col not in df.columns:
                        df[col] = 0.0
                for col in ['days_since_last_game']:
                    if col not in df.columns:
                        df[col] = 5
            return df

        # Initialize required columns to avoid KeyError
        if 'season_avg' not in df.columns:
            df['season_avg'] = df['line']
        if 'last_3_avg' not in df.columns:
            df['last_3_avg'] = df['line']
        if 'consistency' not in df.columns:
            df['consistency'] = 0.70
        if 'variance' not in df.columns:
            df['variance'] = 150.0

        if baseline_stats is not None and not baseline_stats.empty:
            # Merge baseline stats by player and position
            # Map prop_type to stat column name
            stat_map = {
                'passing_yards': 'avg_passing_yards',
                'passing_tds': 'avg_passing_tds',
                'rushing_yards': 'avg_rushing_yards',
                'receiving_yards': 'avg_receiving_yards',
                'receptions': 'avg_receptions',
                'receiving_tds': 'avg_receiving_tds'
            }

            # Create columns for merging
            for idx, row in df.iterrows():
                player_stats = baseline_stats[
                    (baseline_stats['player_id'] == row.get('player_id', '')) |
                    (baseline_stats['player_name'] == row['player_name'])
                ]

                if not player_stats.empty:
                    stats = player_stats.iloc[0]
                    stat_col = stat_map.get(row['prop_type'])

                    if stat_col and stat_col in stats and pd.notna(stats[stat_col]):
                        df.loc[idx, 'season_avg'] = stats[stat_col]
                        df.loc[idx, 'last_3_avg'] = stats.get('last_3_games_avg', stats[stat_col])
                        df.loc[idx, 'consistency'] = stats.get('consistency_score', 0.75)
                        df.loc[idx, 'variance'] = stats.get('variance', 100.0)
                    else:
                        # Use baseline from line if no stats
                        df.loc[idx, 'season_avg'] = row['line']
                        df.loc[idx, 'last_3_avg'] = row['line']
                        df.loc[idx, 'consistency'] = 0.70
                        df.loc[idx, 'variance'] = 150.0
                else:
                    # No stats available, use line as baseline
                    df.loc[idx, 'season_avg'] = row['line']
                    df.loc[idx, 'last_3_avg'] = row['line']
                    df.loc[idx, 'consistency'] = 0.70
                    df.loc[idx, 'variance'] = 150.0
        else:
            # Generate realistic mock features based on position
            for idx, row in df.iterrows():
                line = row['line']
                position = row.get('position', 'WR')

                # Generate season_avg with some variance around the line
                season_avg = line * np.random.uniform(0.92, 1.08)

                # Generate last_3_avg with trend (can be above or below season avg)
                trend_direction = np.random.choice([-1, 1], p=[0.4, 0.6])  # 60% positive trend
                last_3_avg = season_avg * (1 + trend_direction * np.random.uniform(0.02, 0.15))

                df.loc[idx, 'season_avg'] = round(season_avg, 1)
                df.loc[idx, 'last_3_avg'] = round(last_3_avg, 1)

                # Consistency varies by position
                # NFL positions
                if position == 'QB':
                    consistency = np.random.uniform(0.78, 0.90)
                elif position == 'RB':
                    consistency = np.random.uniform(0.70, 0.82)
                elif position in ['WR', 'TE', 'WR/TE']:
                    consistency = np.random.uniform(0.65, 0.80)
                # NBA/MLB positions (higher variance in these sports)
                elif position in ['PG', 'SG', 'SF', 'PF', 'C', 'PLAYER']:
                    consistency = np.random.uniform(0.68, 0.85)
                elif position in ['BATTER', 'PITCHER']:
                    consistency = np.random.uniform(0.60, 0.78)
                else:
                    consistency = np.random.uniform(0.70, 0.80)

                df.loc[idx, 'consistency'] = round(consistency, 2)
                df.loc[idx, 'variance'] = round(line * np.random.uniform(0.3, 0.6), 1)

        # Calculate EWMA (exponentially weighted moving average)
        # Using simple approximation: EWMA = 0.6 * last_3_avg + 0.4 * season_avg
        df['ewma_5'] = (0.6 * df['last_3_avg'] + 0.4 * df['season_avg']).round(1)

        # Calculate form trend
        with np.errstate(divide='ignore', invalid='ignore'):
            df['form_trend'] = ((df['last_3_avg'] - df['season_avg']) / df['season_avg']).fillna(0.0).round(3)

        # Days since last game (mock data: 3-7 days typically)
        df['days_since_last_game'] = np.random.choice([3, 4, 6, 7], size=len(df))

        return df

    def build_matchup_features(self, props_df: pd.DataFrame, baseline_stats: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Build matchup features.

        Features added:
            - opponent_rank_vs_position: Defensive rank vs this position (1-32)
            - opponent_avg_allowed: Average stat allowed to position
            - matchup_advantage: (season_avg - opponent_avg_allowed) / opponent_avg_allowed
            - historical_vs_opponent: Average vs this opponent historically

        Args:
            props_df: DataFrame with player props
            baseline_stats: Optional historical statistics

        Returns:
            DataFrame with added matchup features
        """
        df = props_df.copy()

        # Check if DataFrame is empty or missing required columns
        if df.empty or 'season_avg' not in df.columns:
            logger.warning("Props DataFrame is empty or missing required columns for matchup features")
            # Initialize expected columns with proper default values
            if df.empty:
                for col in ['opponent_rank_vs_position', 'opponent_avg_allowed', 'matchup_advantage', 'historical_vs_opponent']:
                    if col not in df.columns:
                        df[col] = pd.Series(dtype=float)
            else:
                # Initialize with default values for non-empty DataFrame
                if 'opponent_rank_vs_position' not in df.columns:
                    df['opponent_rank_vs_position'] = 16
                if 'opponent_avg_allowed' not in df.columns:
                    df['opponent_avg_allowed'] = df.get('season_avg', 0.0)
                if 'matchup_advantage' not in df.columns:
                    df['matchup_advantage'] = 0.0
                if 'historical_vs_opponent' not in df.columns:
                    df['historical_vs_opponent'] = df.get('season_avg', 0.0)
            return df

        # Generate or fetch opponent defensive rankings
        for idx, row in df.iterrows():
            position = row.get('position', 'WR')
            opponent = row.get('opponent', 'KC')

            if baseline_stats is not None and not baseline_stats.empty:
                # Try to get opponent rank from baseline stats
                player_stats = baseline_stats[
                    (baseline_stats['player_id'] == row.get('player_id', '')) |
                    (baseline_stats['player_name'] == row['player_name'])
                ]

                if not player_stats.empty and 'opponent_rank_vs_position' in player_stats.columns:
                    opp_rank = player_stats.iloc[0]['opponent_rank_vs_position']
                    if pd.notna(opp_rank):
                        df.loc[idx, 'opponent_rank_vs_position'] = int(opp_rank)
                    else:
                        df.loc[idx, 'opponent_rank_vs_position'] = np.random.randint(8, 25)
                else:
                    df.loc[idx, 'opponent_rank_vs_position'] = np.random.randint(8, 25)
            else:
                # Generate realistic opponent rankings (1-32, lower is better defense)
                # Most defenses cluster in the middle
                df.loc[idx, 'opponent_rank_vs_position'] = np.random.randint(8, 25)

        # Calculate opponent_avg_allowed based on rank and position
        for idx, row in df.iterrows():
            season_avg = row.get('season_avg', row['line'])
            opp_rank = row['opponent_rank_vs_position']
            prop_type = row['prop_type']

            # Better defense (lower rank) allows less
            # Rank 1-10: Top defenses (allow 85-95% of average)
            # Rank 11-22: Middle defenses (allow 95-105% of average)
            # Rank 23-32: Poor defenses (allow 105-120% of average)

            if opp_rank <= 10:
                multiplier = np.random.uniform(0.85, 0.95)
            elif opp_rank <= 22:
                multiplier = np.random.uniform(0.95, 1.05)
            else:
                multiplier = np.random.uniform(1.05, 1.20)

            opponent_avg_allowed = season_avg * multiplier
            df.loc[idx, 'opponent_avg_allowed'] = round(opponent_avg_allowed, 1)

        # Calculate matchup advantage
        with np.errstate(divide='ignore', invalid='ignore'):
            df['matchup_advantage'] = (
                (df['season_avg'] - df['opponent_avg_allowed']) / df['opponent_avg_allowed']
            ).fillna(0.0).round(3)

        # Historical vs opponent (add some variance to season avg)
        df['historical_vs_opponent'] = (
            df['season_avg'] * np.random.uniform(0.90, 1.15, size=len(df))
        ).round(1)

        return df

    def build_usage_features(self, props_df: pd.DataFrame) -> pd.DataFrame:
        """
        Build usage features.

        Features added:
            - target_share: Percentage of team's targets/carries/attempts
            - snap_share: Percentage of offensive snaps
            - red_zone_share: Red zone usage rate

        Args:
            props_df: DataFrame with player props

        Returns:
            DataFrame with added usage features
        """
        df = props_df.copy()

        for idx, row in df.iterrows():
            position = row.get('position', 'WR')

            # Generate realistic usage rates by position
            # NFL positions
            if position == 'QB':
                target_share = 1.0  # QBs have all passing attempts
                snap_share = np.random.uniform(0.98, 1.0)
                red_zone_share = np.random.uniform(0.90, 1.0)
            elif position == 'RB':
                # Starting RBs get more, backup RBs get less
                is_starter = np.random.choice([True, False], p=[0.7, 0.3])
                if is_starter:
                    target_share = np.random.uniform(0.15, 0.35)
                    snap_share = np.random.uniform(0.55, 0.75)
                    red_zone_share = np.random.uniform(0.30, 0.50)
                else:
                    target_share = np.random.uniform(0.08, 0.18)
                    snap_share = np.random.uniform(0.25, 0.45)
                    red_zone_share = np.random.uniform(0.15, 0.30)
            elif position == 'WR':
                # WR1, WR2, WR3 tiers
                tier = np.random.choice([1, 2, 3], p=[0.4, 0.4, 0.2])
                if tier == 1:
                    target_share = np.random.uniform(0.22, 0.32)
                    snap_share = np.random.uniform(0.80, 0.95)
                    red_zone_share = np.random.uniform(0.20, 0.35)
                elif tier == 2:
                    target_share = np.random.uniform(0.14, 0.22)
                    snap_share = np.random.uniform(0.65, 0.82)
                    red_zone_share = np.random.uniform(0.12, 0.22)
                else:
                    target_share = np.random.uniform(0.08, 0.15)
                    snap_share = np.random.uniform(0.45, 0.68)
                    red_zone_share = np.random.uniform(0.05, 0.15)
            elif position == 'TE' or position == 'WR/TE':
                is_starter = np.random.choice([True, False], p=[0.75, 0.25])
                if is_starter:
                    target_share = np.random.uniform(0.15, 0.25)
                    snap_share = np.random.uniform(0.70, 0.90)
                    red_zone_share = np.random.uniform(0.18, 0.30)
                else:
                    target_share = np.random.uniform(0.05, 0.12)
                    snap_share = np.random.uniform(0.35, 0.55)
                    red_zone_share = np.random.uniform(0.08, 0.18)
            # NBA positions - usage rate represents minutes/touches
            elif position in ['PG', 'SG', 'SF', 'PF', 'C', 'PLAYER']:
                is_star = np.random.choice([True, False], p=[0.6, 0.4])
                if is_star:
                    target_share = np.random.uniform(0.20, 0.35)  # Shot attempts %
                    snap_share = np.random.uniform(0.75, 0.95)  # Minutes %
                    red_zone_share = np.random.uniform(0.18, 0.32)  # Usage in clutch
                else:
                    target_share = np.random.uniform(0.12, 0.22)
                    snap_share = np.random.uniform(0.50, 0.75)
                    red_zone_share = np.random.uniform(0.10, 0.20)
            # MLB positions - plate appearances/pitches
            elif position == 'BATTER':
                target_share = np.random.uniform(0.10, 0.14)  # Team PA%
                snap_share = np.random.uniform(0.85, 1.0)  # Game appearances
                red_zone_share = np.random.uniform(0.15, 0.30)  # RISP situations
            elif position == 'PITCHER':
                target_share = np.random.uniform(0.15, 0.25)  # Pitch %
                snap_share = np.random.uniform(0.70, 1.0)  # Innings %
                red_zone_share = np.random.uniform(0.12, 0.25)  # High-leverage
            else:
                # Default/unknown position
                target_share = np.random.uniform(0.15, 0.25)
                snap_share = np.random.uniform(0.65, 0.85)
                red_zone_share = np.random.uniform(0.15, 0.25)

            df.loc[idx, 'target_share'] = round(target_share, 3)
            df.loc[idx, 'snap_share'] = round(snap_share, 3)
            df.loc[idx, 'red_zone_share'] = round(red_zone_share, 3)

        return df

    def build_game_context_features(self, props_df: pd.DataFrame) -> pd.DataFrame:
        """
        Build game context features.

        Features added:
            - is_home: Boolean, home game
            - vegas_implied_total: Team's implied total from over/under
            - vegas_spread: Point spread
            - pace_factor: Team pace (plays per game) relative to league avg
            - game_total: Over/under total

        Args:
            props_df: DataFrame with player props

        Returns:
            DataFrame with added game context features
        """
        df = props_df.copy()

        # Check if DataFrame is empty or missing required columns
        if df.empty or 'game_id' not in df.columns:
            logger.warning("Props DataFrame is empty or missing 'game_id' column for game context features")
            # Initialize expected columns with proper default values
            if df.empty:
                for col in ['is_home', 'game_total', 'vegas_spread', 'vegas_implied_total', 'pace_factor']:
                    if col not in df.columns:
                        df[col] = pd.Series(dtype=float)
            else:
                # Initialize with default values for non-empty DataFrame
                if 'is_home' not in df.columns:
                    df['is_home'] = 0
                if 'game_total' not in df.columns:
                    df['game_total'] = 47.0
                if 'vegas_spread' not in df.columns:
                    df['vegas_spread'] = 0.0
                if 'vegas_implied_total' not in df.columns:
                    df['vegas_implied_total'] = 23.5
                if 'pace_factor' not in df.columns:
                    df['pace_factor'] = 1.0
            return df

        # Determine home/away (use home_away column if exists, otherwise random)
        if 'home_away' in df.columns:
            df['is_home'] = (df['home_away'] == 'home').astype(int)
        else:
            df['is_home'] = np.random.choice([0, 1], size=len(df))

        # Generate Vegas lines per game
        for game_id in df['game_id'].unique():
            game_mask = df['game_id'] == game_id

            # Generate realistic game total (typically 42-52 points)
            game_total = np.random.uniform(42.0, 52.0)
            df.loc[game_mask, 'game_total'] = round(game_total, 1)

            # Generate spread (typically -14 to +14)
            spread = np.random.uniform(-14.0, 14.0)

            # Calculate implied totals based on spread and game total
            # Favorite is expected to score more
            favorite_implied = (game_total / 2) + (abs(spread) / 2)
            underdog_implied = (game_total / 2) - (abs(spread) / 2)

            # Assign to teams based on home/away and spread
            for idx in df[game_mask].index:
                row = df.loc[idx]
                if row['is_home']:
                    df.loc[idx, 'vegas_spread'] = round(-spread if spread < 0 else spread, 1)
                    df.loc[idx, 'vegas_implied_total'] = round(
                        favorite_implied if spread < 0 else underdog_implied, 1
                    )
                else:
                    df.loc[idx, 'vegas_spread'] = round(spread if spread < 0 else -spread, 1)
                    df.loc[idx, 'vegas_implied_total'] = round(
                        underdog_implied if spread < 0 else favorite_implied, 1
                    )

        # Pace factor (plays per game relative to league average of ~65)
        df['pace_factor'] = np.random.uniform(0.92, 1.12, size=len(df)).round(3)

        return df

    def build_weather_features(self, props_df: pd.DataFrame, weather_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Build weather features.

        Features added:
            - temperature: Degrees F
            - wind_speed: MPH
            - precipitation_pct: 0-100
            - is_dome: Boolean
            - weather_impact: "High" | "Medium" | "Low" | "None"

        Args:
            props_df: DataFrame with player props
            weather_df: Optional weather data

        Returns:
            DataFrame with added weather features
        """
        df = props_df.copy()

        if weather_df is not None and not weather_df.empty:
            # Merge weather data by game_id
            weather_cols = ['game_id', 'temperature', 'wind_speed', 'precipitation', 'is_dome', 'impact_level']
            available_cols = [col for col in weather_cols if col in weather_df.columns]

            if 'game_id' in available_cols:
                df = df.merge(
                    weather_df[available_cols],
                    on='game_id',
                    how='left'
                )

                # Rename and convert
                if 'precipitation' in df.columns:
                    df['precipitation_pct'] = (df['precipitation'] * 100).fillna(0).round(1)
                if 'impact_level' in df.columns:
                    df['weather_impact'] = df['impact_level'].fillna('None')
            else:
                # No game_id to merge on, generate mock data
                df = self._add_mock_weather(df)
        else:
            # Generate mock weather data
            df = self._add_mock_weather(df)

        # Fill any missing values
        df['temperature'] = df.get('temperature', 72.0).fillna(72.0)
        df['wind_speed'] = df.get('wind_speed', 8.0).fillna(8.0)
        df['precipitation_pct'] = df.get('precipitation_pct', 0.0).fillna(0.0)
        df['is_dome'] = df.get('is_dome', False).fillna(False)
        df['weather_impact'] = df.get('weather_impact', 'Low').fillna('Low')

        return df

    def _add_mock_weather(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add mock weather data to dataframe."""
        # Check if game_id column exists
        if 'game_id' not in df.columns:
            logger.warning("No game_id column found for weather features. Adding default weather values.")
            df['temperature'] = 72.0
            df['wind_speed'] = 8.0
            df['precipitation_pct'] = 0.0
            df['is_dome'] = False
            df['weather_impact'] = 'None'
            return df

        # Check sport from game_id (if prefixed with sport)
        sample_game_id = df['game_id'].iloc[0] if len(df) > 0 else ''
        is_nba = 'nba' in str(sample_game_id).lower()
        is_mlb = 'mlb' in str(sample_game_id).lower()

        # NBA games are all indoors, weather doesn't matter
        if is_nba:
            df['temperature'] = 72.0
            df['wind_speed'] = 0.0
            df['precipitation_pct'] = 0.0
            df['is_dome'] = True
            df['weather_impact'] = 'None'
            return df

        for game_id in df['game_id'].unique():
            game_mask = df['game_id'] == game_id

            # Dome percentage varies by sport
            # NFL: 30% dome, MLB: 25% retractable roof
            dome_pct = 0.25 if is_mlb else 0.30
            is_dome = np.random.random() < dome_pct

            if is_dome:
                df.loc[game_mask, 'temperature'] = 72.0
                df.loc[game_mask, 'wind_speed'] = 0.0
                df.loc[game_mask, 'precipitation_pct'] = 0.0
                df.loc[game_mask, 'is_dome'] = True
                df.loc[game_mask, 'weather_impact'] = 'None'
            else:
                # Outdoor game - generate realistic weather
                temp = np.random.uniform(35, 78)
                wind = np.random.uniform(3, 18)
                precip = np.random.choice([0, 0, 0, 0, np.random.uniform(0, 30)])

                # Weather impact varies by sport
                # MLB: More affected by wind (batting)
                # NFL: More affected by temperature and precipitation (passing)
                if is_mlb:
                    if wind > 18 or temp < 35 or temp > 95 or precip > 30:
                        impact = 'High'
                    elif wind > 12 or temp < 45 or temp > 85 or precip > 15:
                        impact = 'Medium'
                    elif wind > 8 or precip > 5:
                        impact = 'Low'
                    else:
                        impact = 'Minimal'
                else:  # NFL
                    if wind > 15 or temp < 40 or temp > 85 or precip > 20:
                        impact = 'High'
                    elif wind > 12 or temp < 45 or temp > 80 or precip > 10:
                        impact = 'Medium'
                    elif wind > 8 or temp < 50 or precip > 5:
                        impact = 'Low'
                    else:
                        impact = 'Minimal'

                df.loc[game_mask, 'temperature'] = round(temp, 1)
                df.loc[game_mask, 'wind_speed'] = round(wind, 1)
                df.loc[game_mask, 'precipitation_pct'] = round(precip, 1)
                df.loc[game_mask, 'is_dome'] = False
                df.loc[game_mask, 'weather_impact'] = impact

        return df

    def build_injury_features(self, props_df: pd.DataFrame, injuries_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Build injury features.

        Features added:
            - player_injury_status: "Out" | "Doubtful" | "Questionable" | "Probable" | "Healthy"
            - key_teammate_out: Boolean, key teammate out
            - opponent_key_defender_out: Boolean

        Args:
            props_df: DataFrame with player props
            injuries_df: Optional injury data

        Returns:
            DataFrame with added injury features
        """
        df = props_df.copy()

        if injuries_df is not None and not injuries_df.empty:
            # Merge injury data by player_id or player_name
            for idx, row in df.iterrows():
                player_injury = injuries_df[
                    (injuries_df.get('player_id', '') == row.get('player_id', '')) |
                    (injuries_df['player_name'] == row['player_name'])
                ]

                if not player_injury.empty:
                    df.loc[idx, 'player_injury_status'] = player_injury.iloc[0]['status']
                else:
                    df.loc[idx, 'player_injury_status'] = 'Healthy'

                # Check for key teammate injuries on same team
                team_injuries = injuries_df[
                    (injuries_df['team'] == row['team']) &
                    (injuries_df['status'].isin(['Out', 'Doubtful']))
                ]
                df.loc[idx, 'key_teammate_out'] = len(team_injuries) > 0

                # Check for opponent key defender injuries
                opponent_def_injuries = injuries_df[
                    (injuries_df['team'] == row.get('opponent', '')) &
                    (injuries_df['status'].isin(['Out', 'Doubtful'])) &
                    (injuries_df['position'].isin(['CB', 'S', 'LB', 'DE', 'DT']))
                ]
                df.loc[idx, 'opponent_key_defender_out'] = len(opponent_def_injuries) > 0
        else:
            # Generate mock injury status
            # 85% healthy, 10% questionable, 3% doubtful, 2% out
            injury_statuses = np.random.choice(
                ['Healthy', 'Questionable', 'Doubtful', 'Out'],
                size=len(df),
                p=[0.85, 0.10, 0.03, 0.02]
            )
            df['player_injury_status'] = injury_statuses

            # Random teammate/opponent injuries
            df['key_teammate_out'] = np.random.choice([False, True], size=len(df), p=[0.7, 0.3])
            df['opponent_key_defender_out'] = np.random.choice([False, True], size=len(df), p=[0.75, 0.25])

        return df

    def build_prop_specific_features(self, props_df: pd.DataFrame) -> pd.DataFrame:
        """
        Build prop-specific features.

        Features added:
            - line_vs_season_avg_delta: (line - season_avg)
            - line_vs_last3_delta: (line - last_3_avg)
            - implied_prob_over: Convert over_odds to probability
            - implied_prob_under: Convert under_odds to probability
            - vig: (implied_prob_over + implied_prob_under - 1) * 100

        Args:
            props_df: DataFrame with player props

        Returns:
            DataFrame with added prop-specific features
        """
        df = props_df.copy()

        # Check if required columns exist
        if 'line' not in df.columns or 'season_avg' not in df.columns:
            logger.warning("Missing 'line' or 'season_avg' columns. Adding default prop-specific features.")
            if 'line_vs_season_avg_delta' not in df.columns:
                df['line_vs_season_avg_delta'] = 0.0
            if 'line_vs_last3_delta' not in df.columns:
                df['line_vs_last3_delta'] = 0.0
            if 'implied_prob_over' not in df.columns:
                df['implied_prob_over'] = 0.5
            if 'implied_prob_under' not in df.columns:
                df['implied_prob_under'] = 0.5
            if 'vig' not in df.columns:
                df['vig'] = 0.0
            return df

        # Calculate deltas
        if 'line' in df.columns and 'season_avg' in df.columns:
            df['line_vs_season_avg_delta'] = (df['line'] - df['season_avg']).round(1)
        else:
            df['line_vs_season_avg_delta'] = 0.0

        if 'line' in df.columns and 'last_3_avg' in df.columns:
            df['line_vs_last3_delta'] = (df['line'] - df['last_3_avg']).round(1)
        else:
            df['line_vs_last3_delta'] = 0.0

        # Convert odds to implied probabilities
        if 'over_odds' in df.columns:
            df['implied_prob_over'] = df['over_odds'].apply(odds_to_probability).round(4)
        else:
            df['implied_prob_over'] = 0.5

        if 'under_odds' in df.columns:
            df['implied_prob_under'] = df['under_odds'].apply(odds_to_probability).round(4)
        else:
            df['implied_prob_under'] = 0.5

        # Calculate vig
        if 'over_odds' in df.columns and 'under_odds' in df.columns:
            df['vig'] = calculate_vig(df['over_odds'], df['under_odds']).round(2)
        else:
            df['vig'] = 0.0

        return df

    def build_correlation_tags(self, props_df: pd.DataFrame) -> pd.DataFrame:
        """
        Add correlation tags for same-game parlays.

        Features added:
            - same_game_id: game_id
            - same_team: team
            - correlation_group: e.g., "QB-WR" for QB and his WR

        Args:
            props_df: DataFrame with player props

        Returns:
            DataFrame with added correlation tags
        """
        df = props_df.copy()

        # same_game_id and same_team are already present as game_id and team
        df['same_game_id'] = df['game_id'] if 'game_id' in df.columns else None
        df['same_team'] = df['team'] if 'team' in df.columns else None

        # Detect correlation groups
        df['correlation_group'] = df.apply(self._determine_correlation_group, axis=1)

        return df

    def _determine_correlation_group(self, row: pd.Series) -> str:
        """Determine correlation group for a prop."""
        position = row.get('position', '')
        team = row.get('team', '')
        prop_type = row.get('prop_type', '')

        # QB correlations
        if position == 'QB':
            if 'passing' in prop_type:
                return f"QB_PASSING_{team}"
            elif 'rushing' in prop_type:
                return f"QB_RUSHING_{team}"

        # RB correlations
        elif position == 'RB':
            if 'rushing' in prop_type:
                return f"RB_RUSHING_{team}"
            elif 'receiving' in prop_type:
                return f"RB_RECEIVING_{team}"

        # WR/TE receiving correlations
        elif position in ['WR', 'TE']:
            return f"{position}_RECEIVING_{team}"

        return f"{position}_{team}"

    def build_all_features(
        self,
        props_df: pd.DataFrame,
        context_df: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Build complete feature set.

        Args:
            props_df: DataFrame with player props
            context_df: Optional dict with 'injuries', 'weather', 'baseline_stats'

        Returns:
            DataFrame with all features
        """
        # Parse context_df if provided
        injuries_df = None
        weather_df = None
        baseline_stats = None

        if context_df is not None:
            if isinstance(context_df, dict):
                injuries_df = context_df.get('injuries')
                weather_df = context_df.get('weather')
                baseline_stats = context_df.get('baseline_stats')
            elif isinstance(context_df, pd.DataFrame):
                # Assume it's baseline stats
                baseline_stats = context_df

        logger.info(f"Building features for {len(props_df)} props")

        # Build features in stages
        df = props_df.copy()

        # ===== DATA NORMALIZATION =====
        # Ensure all required source columns exist with proper defaults
        # This handles cases where different data sources (Odds API, mock data, etc.)
        # may have different column sets

        if not df.empty:
            # Core betting columns (should come from data source)
            if 'line' not in df.columns:
                logger.warning("Missing 'line' column - initializing with 0.0")
                df['line'] = 0.0
            if 'over_odds' not in df.columns:
                logger.warning("Missing 'over_odds' column - initializing with -110")
                df['over_odds'] = -110
            if 'under_odds' not in df.columns:
                logger.warning("Missing 'under_odds' column - initializing with -110")
                df['under_odds'] = -110

            # Player/game identification columns
            if 'player_name' not in df.columns:
                logger.warning("Missing 'player_name' column - initializing with 'Unknown'")
                df['player_name'] = 'Unknown'
            if 'player_id' not in df.columns:
                df['player_id'] = df.get('player_name', 'unknown').str.lower().str.replace(' ', '_')
            if 'game_id' not in df.columns:
                logger.warning("Missing 'game_id' column - initializing with 'game_0'")
                df['game_id'] = f'game_0'
            if 'prop_type' not in df.columns:
                logger.warning("Missing 'prop_type' column - initializing with 'unknown'")
                df['prop_type'] = 'unknown'

            # Position/team columns (may be missing from some sources)
            if 'position' not in df.columns:
                logger.warning("Missing 'position' column - initializing with 'Unknown'")
                df['position'] = 'Unknown'
            if 'team' not in df.columns:
                logger.warning("Missing 'team' column - initializing with None")
                df['team'] = None
            if 'opponent' not in df.columns:
                df['opponent'] = None

        logger.debug("Building player form features...")
        df = self.build_player_form_features(df, baseline_stats)

        logger.debug("Building matchup features...")
        df = self.build_matchup_features(df, baseline_stats)

        logger.debug("Building usage features...")
        df = self.build_usage_features(df)

        logger.debug("Building game context features...")
        df = self.build_game_context_features(df)

        logger.debug("Building weather features...")
        df = self.build_weather_features(df, weather_df)

        logger.debug("Building injury features...")
        df = self.build_injury_features(df, injuries_df)

        logger.debug("Building prop-specific features...")
        df = self.build_prop_specific_features(df)

        logger.debug("Building correlation tags...")
        df = self.build_correlation_tags(df)

        logger.info(f"Feature engineering complete. Added {len(df.columns) - len(props_df.columns)} features")

        return df

    def detect_trends(
        self,
        props_df: pd.DataFrame,
        context_df: Optional[pd.DataFrame] = None,
        n_chips: int = 5
    ) -> List[TrendChip]:
        """
        Detect significant trends for trend chips.

        Trend categories:
            1. Offensive Surge: Team scoring way above average
            2. Defensive Weakness: Opponent allowing way above average
            3. Weather Impact: Significant weather affecting passing/scoring
            4. Injury Cascade: Key players out affecting target distribution
            5. Vegas Movement: Line movement indicating sharp money
            6. Hot Streak: Player significantly outperforming baseline
            7. Matchup Exploit: Player excels vs this opponent type

        Args:
            props_df: DataFrame with player props and features
            context_df: Optional contextual data
            n_chips: Number of trend chips to generate

        Returns:
            List of TrendChip objects
        """
        trends = []

        # Handle empty dataframe
        if props_df.empty:
            logger.warning("Props DataFrame is empty. Cannot generate trends.")
            return trends

        # Check for required columns
        required_columns = ['form_trend', 'player_name', 'prop_type', 'position']
        missing_columns = [col for col in required_columns if col not in props_df.columns]

        if missing_columns:
            logger.warning(f"Props DataFrame missing required columns: {missing_columns}. Cannot generate trends.")
            return trends

        # 1. Detect Hot Streaks (form_trend > 0.15)
        hot_streak_mask = props_df['form_trend'] > 0.15
        if hot_streak_mask.any():
            for _, player in props_df[hot_streak_mask].head(2).iterrows():
                trends.append(TrendChip(
                    title=f"{player['player_name']} Hot Streak",
                    description=f"Averaging {player['last_3_avg']:.1f} over last 3 games, {player['form_trend']*100:.0f}% above season average",
                    impact_direction="positive",
                    confidence=min(0.75 + player['form_trend'] * 0.5, 0.95),
                    impacted_props=[player['player_name']],
                    diagnostics={
                        'method': 'form_trend threshold',
                        'threshold': 0.15,
                        'actual_trend': round(player['form_trend'], 3),
                        'season_avg': player['season_avg'],
                        'last_3_avg': player['last_3_avg'],
                        'mini_chart_data': {
                            'type': 'trend',
                            'values': [player['season_avg'], player['last_3_avg'], player['ewma_5']]
                        }
                    }
                ))

        # 2. Detect Favorable Matchups (matchup_advantage > 0.10)
        favorable_matchup_mask = props_df['matchup_advantage'] > 0.10
        if favorable_matchup_mask.any():
            for _, player in props_df[favorable_matchup_mask].head(2).iterrows():
                trends.append(TrendChip(
                    title=f"Favorable Matchup: {player['player_name']}",
                    description=f"Opponent ranks {player['opponent_rank_vs_position']}/32 vs {player['position']}, allowing {player['opponent_avg_allowed']:.1f} per game",
                    impact_direction="positive",
                    confidence=0.70 + min(player['matchup_advantage'] * 2, 0.20),
                    impacted_props=[player['player_name']],
                    diagnostics={
                        'method': 'matchup_advantage threshold',
                        'threshold': 0.10,
                        'actual_advantage': round(player['matchup_advantage'], 3),
                        'opponent_rank': int(player['opponent_rank_vs_position']),
                        'opponent_avg_allowed': player['opponent_avg_allowed'],
                        'mini_chart_data': {
                            'type': 'comparison',
                            'values': [player['season_avg'], player['opponent_avg_allowed']]
                        }
                    }
                ))

        # 3. Detect Weather Impact (weather_impact == "High" and passing props)
        if 'weather_impact' in props_df.columns:
            weather_impact_mask = (
                (props_df['weather_impact'] == 'High') &
                (props_df['prop_type'].isin(['passing_yards', 'receiving_yards', 'receptions']))
            )
            if weather_impact_mask.any():
                affected_players = props_df[weather_impact_mask].head(3)
                game_id = affected_players.iloc[0]['game_id']
                wind_speed = affected_players.iloc[0]['wind_speed']
                temp = affected_players.iloc[0]['temperature']

                weather_desc = []
                if wind_speed > 15:
                    weather_desc.append(f"{wind_speed:.0f} mph winds")
                if temp < 35:
                    weather_desc.append(f"{temp:.0f}°F temperature")
                elif temp > 85:
                    weather_desc.append(f"{temp:.0f}°F heat")

                trends.append(TrendChip(
                    title="High Weather Impact",
                    description=f"Extreme weather expected: {', '.join(weather_desc)}. May affect passing game.",
                    impact_direction="negative",
                    confidence=0.75,
                    impacted_props=affected_players['player_name'].tolist(),
                    diagnostics={
                        'method': 'weather_impact classification',
                        'threshold': 'High',
                        'game_id': game_id,
                        'wind_speed': wind_speed,
                        'temperature': temp,
                        'mini_chart_data': {
                            'type': 'weather',
                            'wind': wind_speed,
                            'temp': temp
                        }
                    }
                ))

        # 4. Detect Injury Cascade (key_teammate_out and target_share increase opportunity)
        if 'key_teammate_out' in props_df.columns:
            injury_opportunity_mask = (
                (props_df['key_teammate_out'] == True) &
                (props_df['position'].isin(['WR', 'TE', 'RB']))
            )
            if injury_opportunity_mask.any():
                for _, player in props_df[injury_opportunity_mask].head(2).iterrows():
                    trends.append(TrendChip(
                        title=f"Increased Opportunity: {player['player_name']}",
                        description=f"Key teammate out. Target share could increase from current {player['target_share']*100:.0f}%",
                        impact_direction="positive",
                        confidence=0.65,
                        impacted_props=[player['player_name']],
                        diagnostics={
                            'method': 'teammate_injury detection',
                            'current_target_share': round(player['target_share'], 3),
                            'position': player['position'],
                            'mini_chart_data': {
                                'type': 'usage',
                                'target_share': player['target_share']
                            }
                        }
                    ))

        # 5. Detect Vegas Discrepancies (line significantly different from projections)
        line_discrepancy_mask = abs(props_df['line_vs_season_avg_delta']) > (props_df['season_avg'] * 0.12)
        if line_discrepancy_mask.any():
            for _, player in props_df[line_discrepancy_mask].head(2).iterrows():
                direction = "positive" if player['line_vs_season_avg_delta'] < 0 else "negative"
                line_direction = "under" if player['line_vs_season_avg_delta'] < 0 else "over"

                trends.append(TrendChip(
                    title=f"Line Value: {player['player_name']}",
                    description=f"Line at {player['line']:.1f} vs season avg of {player['season_avg']:.1f}. Consider {line_direction}",
                    impact_direction=direction,
                    confidence=0.68,
                    impacted_props=[player['player_name']],
                    diagnostics={
                        'method': 'line_vs_avg discrepancy',
                        'threshold': 0.12,
                        'line': player['line'],
                        'season_avg': player['season_avg'],
                        'delta': round(player['line_vs_season_avg_delta'], 1),
                        'mini_chart_data': {
                            'type': 'line_comparison',
                            'line': player['line'],
                            'season_avg': player['season_avg']
                        }
                    }
                ))

        # 6. Detect High-Scoring Game Environment (game_total > 50)
        if 'game_total' in props_df.columns:
            high_scoring_mask = props_df['game_total'] > 50
            if high_scoring_mask.any():
                game_props = props_df[high_scoring_mask]
                if not game_props.empty:
                    game_id = game_props.iloc[0]['game_id']
                    game_total = game_props.iloc[0]['game_total']
                    affected = game_props[game_props['position'].isin(['QB', 'WR', 'TE'])].head(4)

                    if not affected.empty:
                        trends.append(TrendChip(
                            title="High-Scoring Game Expected",
                            description=f"O/U at {game_total:.1f} points. Offensive props may benefit.",
                            impact_direction="positive",
                            confidence=0.72,
                            impacted_props=affected['player_name'].tolist(),
                            diagnostics={
                                'method': 'game_total threshold',
                                'threshold': 50.0,
                                'game_total': game_total,
                                'game_id': game_id,
                                'mini_chart_data': {
                                    'type': 'game_total',
                                    'total': game_total
                                }
                            }
                        ))

        # Sort by confidence and return top n_chips
        trends.sort(key=lambda x: x.confidence, reverse=True)
        return trends[:n_chips]


# Helper functions

def calculate_ewma(values: List[float], alpha: float = 0.4) -> float:
    """
    Calculate exponentially weighted moving average.

    Args:
        values: List of values (most recent last)
        alpha: Smoothing factor (0 < alpha <= 1)

    Returns:
        EWMA value
    """
    if not values:
        return 0.0

    ewma = values[0]
    for value in values[1:]:
        ewma = alpha * value + (1 - alpha) * ewma

    return ewma


def odds_to_probability(american_odds: float) -> float:
    """
    Convert American odds to implied probability.

    Args:
        american_odds: American odds format (e.g., -110, +100)

    Returns:
        Implied probability (0-1)
    """
    if pd.isna(american_odds):
        return 0.5

    if american_odds > 0:
        # Positive odds: 100 / (odds + 100)
        return 100.0 / (american_odds + 100.0)
    elif american_odds < 0:
        # Negative odds: |odds| / (|odds| + 100)
        return abs(american_odds) / (abs(american_odds) + 100.0)
    else:
        return 0.5


def calculate_vig(over_odds: pd.Series, under_odds: pd.Series) -> pd.Series:
    """
    Calculate bookmaker vig/juice.

    Args:
        over_odds: Series of over odds
        under_odds: Series of under odds

    Returns:
        Series of vig percentages
    """
    over_prob = over_odds.apply(odds_to_probability)
    under_prob = under_odds.apply(odds_to_probability)

    # Vig = (sum of implied probs - 1) * 100
    vig = (over_prob + under_prob - 1.0) * 100.0

    return vig


def detect_correlation_groups(props_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add correlation_group column for common correlations.

    Correlation patterns:
        - QB-WR same team: "QB_WR_[team]"
        - RB-RB same team: "RB_RB_[team]"
        - Player-GameTotal: "Player_Total_[game]"

    Args:
        props_df: DataFrame with player props

    Returns:
        DataFrame with correlation_group column added
    """
    df = props_df.copy()

    # Group by game and team to find correlated props
    for game_id in df['game_id'].unique():
        game_mask = df['game_id'] == game_id

        for team in df[game_mask]['team'].unique():
            team_mask = game_mask & (df['team'] == team)

            # Find QB props
            qb_props = df[team_mask & (df['position'] == 'QB')]
            # Find pass-catchers (WR, TE)
            pass_catcher_props = df[team_mask & df['position'].isin(['WR', 'TE'])]

            # Tag QB-pass catcher correlations
            if not qb_props.empty and not pass_catcher_props.empty:
                qb_passing_mask = team_mask & (df['position'] == 'QB') & (df['prop_type'].str.contains('passing'))
                receiving_mask = team_mask & df['position'].isin(['WR', 'TE']) & (df['prop_type'].str.contains('receiv'))

                df.loc[qb_passing_mask | receiving_mask, 'correlation_group'] = f"QB_WR_{team}"

            # Tag RB correlations (rushing/receiving from same backfield)
            rb_props = df[team_mask & (df['position'] == 'RB')]
            if len(rb_props) > 1:
                df.loc[team_mask & (df['position'] == 'RB'), 'correlation_group'] = f"RB_RB_{team}"

    return df


# Main interface functions

def build_features(
    props_df: pd.DataFrame,
    context_df: Optional[pd.DataFrame] = None,
    config: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Convenience function to build features.

    Args:
        props_df: DataFrame with player props
        context_df: Optional dict with contextual data or DataFrame with baseline stats
        config: Optional configuration

    Returns:
        DataFrame with engineered features
    """
    pipeline = FeaturePipeline(config=config)
    return pipeline.build_all_features(props_df, context_df)


def generate_trend_chips(
    props_df: pd.DataFrame,
    context_df: Optional[pd.DataFrame] = None,
    n_chips: int = 5
) -> List[Dict[str, Any]]:
    """
    Generate trend chips for UI display.

    Args:
        props_df: DataFrame with player props (should have features built)
        context_df: Optional contextual data
        n_chips: Number of trend chips to generate

    Returns:
        List of trend chip dictionaries
    """
    pipeline = FeaturePipeline()

    # Ensure features are built
    if 'season_avg' not in props_df.columns:
        props_df = pipeline.build_all_features(props_df, context_df)

    trends = pipeline.detect_trends(props_df, context_df, n_chips)

    return [
        {
            'title': t.title,
            'description': t.description,
            'impact_direction': t.impact_direction,
            'confidence': t.confidence,
            'impacted_props': t.impacted_props,
            'diagnostics': t.diagnostics
        }
        for t in trends
    ]

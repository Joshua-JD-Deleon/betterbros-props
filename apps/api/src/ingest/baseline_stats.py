"""
Baseline Stats Provider for calculating player and team statistical baselines
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from redis.asyncio import Redis

from src.config import settings
from src.db import get_redis
from src.ingest.sleeper_client import SleeperAPI

logger = logging.getLogger(__name__)


class BaselineStatsError(Exception):
    """Custom exception for Baseline Stats errors"""
    pass


class BaselineStats:
    """
    Provider for calculating baseline statistics for players and teams

    Computes rolling averages, season averages, and team-level stats
    with Redis caching for performance.

    Attributes:
        cache_ttl: Cache time-to-live in seconds (default: 24 hours)
    """

    CACHE_TTL = 86400  # 24 hours

    def __init__(
        self,
        sleeper_client: Optional[SleeperAPI] = None,
    ):
        """
        Initialize Baseline Stats provider

        Args:
            sleeper_client: Optional Sleeper API client instance
        """
        self.sleeper_client = sleeper_client or SleeperAPI()
        self._owned_sleeper = sleeper_client is None

    async def close(self):
        """Close resources"""
        if self._owned_sleeper:
            await self.sleeper_client.close()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def _get_cached(self, redis: Redis, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from Redis cache"""
        try:
            import json
            cached = await redis.get(cache_key)
            if cached:
                logger.info(f"Cache HIT: {cache_key}")
                return json.loads(cached)
            logger.info(f"Cache MISS: {cache_key}")
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        return None

    async def _set_cached(
        self,
        redis: Redis,
        cache_key: str,
        data: Dict[str, Any],
        ttl: int,
    ):
        """Set data in Redis cache"""
        try:
            import json
            await redis.setex(cache_key, ttl, json.dumps(data))
            logger.debug(f"Cached: {cache_key} (TTL: {ttl}s)")
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    def _calculate_stat_value(
        self,
        stats: Dict[str, Any],
        stat_type: str,
    ) -> Optional[float]:
        """
        Extract and calculate stat value from stats dictionary

        Args:
            stats: Stats dictionary
            stat_type: Stat type to calculate (e.g., 'points', 'pass_yd')

        Returns:
            Calculated stat value or None
        """
        # Normalize stat type
        stat_lower = stat_type.lower().replace(" ", "_")

        # Direct stat mapping
        stat_map = {
            # Passing
            "passing_yards": "pass_yd",
            "pass_yards": "pass_yd",
            "passing_tds": "pass_td",
            "pass_tds": "pass_td",
            "interceptions": "int",
            "ints": "int",
            # Rushing
            "rushing_yards": "rush_yd",
            "rush_yards": "rush_yd",
            "rushing_tds": "rush_td",
            "rush_tds": "rush_td",
            "carries": "rush_att",
            # Receiving
            "receiving_yards": "rec_yd",
            "rec_yards": "rec_yd",
            "receptions": "rec",
            "receiving_tds": "rec_td",
            "rec_tds": "rec_td",
            "targets": "rec_tgt",
            # Fantasy
            "fantasy_points": "pts_ppr",
            "points": "pts_ppr",
            "ppr_points": "pts_ppr",
        }

        # Get mapped stat or use original
        stat_key = stat_map.get(stat_lower, stat_lower)

        # Try to get value
        value = stats.get(stat_key)
        if value is not None:
            return float(value)

        # Try alternative calculations
        if stat_type.lower() in ["fantasy_points", "points"]:
            # Calculate fantasy points if not directly available
            pts = 0.0
            pts += stats.get("pass_yd", 0) * 0.04
            pts += stats.get("pass_td", 0) * 4
            pts += stats.get("int", 0) * -2
            pts += stats.get("rush_yd", 0) * 0.1
            pts += stats.get("rush_td", 0) * 6
            pts += stats.get("rec", 0) * 1  # PPR
            pts += stats.get("rec_yd", 0) * 0.1
            pts += stats.get("rec_td", 0) * 6
            return pts if pts > 0 else None

        return None

    async def get_player_baseline(
        self,
        player_id: str,
        stat_type: str,
        season: str,
        current_week: int,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Calculate baseline statistics for a player

        Computes season average, recent averages (3-game, 5-game),
        and volatility metrics.

        Args:
            player_id: Player ID
            stat_type: Stat type (e.g., 'passing_yards', 'receptions')
            season: Season year
            current_week: Current week number (to limit lookback)
            use_cache: Whether to use Redis cache

        Returns:
            Baseline statistics dictionary

        Example:
            {
                "player_id": "421",
                "stat_type": "passing_yards",
                "season": "2024",
                "season_avg": 285.5,
                "avg_last_3": 310.2,
                "avg_last_5": 295.8,
                "median": 280.0,
                "std_dev": 45.3,
                "min": 195.0,
                "max": 425.0,
                "games_played": 8,
                "trend": "up"
            }
        """
        cache_key = f"baseline:player:{player_id}:{stat_type}:{season}:week_{current_week}"
        redis = await get_redis()

        try:
            # Check cache
            if use_cache:
                cached = await self._get_cached(redis, cache_key)
                if cached:
                    return cached

            # Fetch stats for all weeks up to current week
            stat_values = []
            week_stats = []

            for week in range(1, current_week):
                try:
                    stats_data = await self.sleeper_client.get_player_stats(
                        player_id=player_id,
                        season=season,
                        week=week,
                        use_cache=True,
                    )

                    stats = stats_data.get("stats", {})
                    value = self._calculate_stat_value(stats, stat_type)

                    if value is not None and value > 0:
                        stat_values.append(value)
                        week_stats.append({
                            "week": week,
                            "value": value,
                        })

                except Exception as e:
                    logger.warning(f"Failed to fetch week {week} stats for {player_id}: {e}")
                    continue

            if not stat_values:
                # No data available
                result = {
                    "player_id": player_id,
                    "stat_type": stat_type,
                    "season": season,
                    "season_avg": None,
                    "avg_last_3": None,
                    "avg_last_5": None,
                    "median": None,
                    "std_dev": None,
                    "min": None,
                    "max": None,
                    "games_played": 0,
                    "trend": None,
                    "computed_at": datetime.utcnow().isoformat(),
                }
            else:
                # Calculate statistics
                import statistics

                season_avg = statistics.mean(stat_values)
                median = statistics.median(stat_values)
                std_dev = statistics.stdev(stat_values) if len(stat_values) > 1 else 0
                min_val = min(stat_values)
                max_val = max(stat_values)

                # Rolling averages
                avg_last_3 = statistics.mean(stat_values[-3:]) if len(stat_values) >= 3 else None
                avg_last_5 = statistics.mean(stat_values[-5:]) if len(stat_values) >= 5 else None

                # Trend detection (compare recent vs season avg)
                trend = None
                if avg_last_3:
                    if avg_last_3 > season_avg * 1.1:
                        trend = "up"
                    elif avg_last_3 < season_avg * 0.9:
                        trend = "down"
                    else:
                        trend = "stable"

                result = {
                    "player_id": player_id,
                    "stat_type": stat_type,
                    "season": season,
                    "season_avg": round(season_avg, 2),
                    "avg_last_3": round(avg_last_3, 2) if avg_last_3 else None,
                    "avg_last_5": round(avg_last_5, 2) if avg_last_5 else None,
                    "median": round(median, 2),
                    "std_dev": round(std_dev, 2),
                    "min": round(min_val, 2),
                    "max": round(max_val, 2),
                    "games_played": len(stat_values),
                    "trend": trend,
                    "week_by_week": week_stats,
                    "computed_at": datetime.utcnow().isoformat(),
                }

            # Cache the results
            if use_cache:
                await self._set_cached(redis, cache_key, result, self.CACHE_TTL)

            logger.info(f"Calculated baseline for player {player_id}, {stat_type}")
            return result

        finally:
            await redis.close()

    async def get_team_stats(
        self,
        team: str,
        stat_category: str,
        season: str,
        current_week: int,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Calculate team-level statistics

        Aggregates team performance metrics like pace, points per game,
        yards allowed, etc.

        Args:
            team: Team abbreviation
            stat_category: Category (e.g., 'offense', 'defense', 'pace')
            season: Season year
            current_week: Current week number
            use_cache: Whether to use Redis cache

        Returns:
            Team statistics dictionary

        Example:
            {
                "team": "KC",
                "category": "offense",
                "season": "2024",
                "points_per_game": 28.5,
                "yards_per_game": 385.2,
                "pass_yards_per_game": 285.5,
                "rush_yards_per_game": 99.7,
                "turnovers_per_game": 0.8,
                "games_played": 8
            }
        """
        cache_key = f"baseline:team:{team}:{stat_category}:{season}:week_{current_week}"
        redis = await get_redis()

        try:
            # Check cache
            if use_cache:
                cached = await self._get_cached(redis, cache_key)
                if cached:
                    return cached

            # Get all players on team
            players = await self.sleeper_client.get_nfl_players(use_cache=True)
            team_players = [
                p for p in players.values()
                if p.get("team") == team and p.get("active", False)
            ]

            # Aggregate team stats across all players and weeks
            team_totals = {
                "pass_yd": [],
                "rush_yd": [],
                "total_yd": [],
                "pass_td": [],
                "rush_td": [],
                "total_td": [],
                "int": [],
                "fumbles": [],
                "turnovers": [],
            }

            for week in range(1, current_week):
                week_totals = {
                    "pass_yd": 0,
                    "rush_yd": 0,
                    "pass_td": 0,
                    "rush_td": 0,
                    "int": 0,
                    "fumbles": 0,
                }

                for player in team_players:
                    try:
                        stats_data = await self.sleeper_client.get_player_stats(
                            player_id=player.get("player_id"),
                            season=season,
                            week=week,
                            use_cache=True,
                        )

                        stats = stats_data.get("stats", {})
                        week_totals["pass_yd"] += stats.get("pass_yd", 0)
                        week_totals["rush_yd"] += stats.get("rush_yd", 0)
                        week_totals["pass_td"] += stats.get("pass_td", 0)
                        week_totals["rush_td"] += stats.get("rush_td", 0)
                        week_totals["int"] += stats.get("int", 0)
                        week_totals["fumbles"] += stats.get("fum_lost", 0)

                    except Exception:
                        continue

                # Add week totals
                if week_totals["pass_yd"] > 0 or week_totals["rush_yd"] > 0:
                    team_totals["pass_yd"].append(week_totals["pass_yd"])
                    team_totals["rush_yd"].append(week_totals["rush_yd"])
                    team_totals["total_yd"].append(week_totals["pass_yd"] + week_totals["rush_yd"])
                    team_totals["pass_td"].append(week_totals["pass_td"])
                    team_totals["rush_td"].append(week_totals["rush_td"])
                    team_totals["total_td"].append(week_totals["pass_td"] + week_totals["rush_td"])
                    team_totals["int"].append(week_totals["int"])
                    team_totals["fumbles"].append(week_totals["fumbles"])
                    team_totals["turnovers"].append(week_totals["int"] + week_totals["fumbles"])

            games_played = len(team_totals["total_yd"])

            if games_played == 0:
                result = {
                    "team": team,
                    "category": stat_category,
                    "season": season,
                    "games_played": 0,
                    "computed_at": datetime.utcnow().isoformat(),
                }
            else:
                import statistics

                result = {
                    "team": team,
                    "category": stat_category,
                    "season": season,
                    "games_played": games_played,
                    "yards_per_game": round(statistics.mean(team_totals["total_yd"]), 1),
                    "pass_yards_per_game": round(statistics.mean(team_totals["pass_yd"]), 1),
                    "rush_yards_per_game": round(statistics.mean(team_totals["rush_yd"]), 1),
                    "total_tds_per_game": round(statistics.mean(team_totals["total_td"]), 1),
                    "pass_tds_per_game": round(statistics.mean(team_totals["pass_td"]), 1),
                    "rush_tds_per_game": round(statistics.mean(team_totals["rush_td"]), 1),
                    "turnovers_per_game": round(statistics.mean(team_totals["turnovers"]), 1),
                    "computed_at": datetime.utcnow().isoformat(),
                }

                # Estimated points per game (rough calculation)
                estimated_ppg = (
                    result["total_tds_per_game"] * 6.5 +  # TDs worth ~6.5 points (including extra points)
                    result["yards_per_game"] * 0.02  # Rough field goal contribution
                )
                result["estimated_points_per_game"] = round(estimated_ppg, 1)

            # Cache the results
            if use_cache:
                await self._set_cached(redis, cache_key, result, self.CACHE_TTL)

            logger.info(f"Calculated team stats for {team}, {stat_category}")
            return result

        finally:
            await redis.close()

    async def get_rolling_averages(
        self,
        player_id: str,
        stat_type: str,
        season: str,
        current_week: int,
        windows: List[int] = [3, 5, 10],
    ) -> Dict[str, Any]:
        """
        Get rolling averages for multiple windows

        Args:
            player_id: Player ID
            stat_type: Stat type
            season: Season year
            current_week: Current week number
            windows: List of window sizes (games)

        Returns:
            Dictionary with rolling averages for each window
        """
        baseline = await self.get_player_baseline(
            player_id=player_id,
            stat_type=stat_type,
            season=season,
            current_week=current_week,
        )

        week_by_week = baseline.get("week_by_week", [])
        if not week_by_week:
            return {
                "player_id": player_id,
                "stat_type": stat_type,
                "rolling_averages": {},
            }

        import statistics

        rolling_avgs = {}
        values = [w["value"] for w in week_by_week]

        for window in windows:
            if len(values) >= window:
                rolling_avgs[f"last_{window}"] = round(
                    statistics.mean(values[-window:]), 2
                )
            else:
                rolling_avgs[f"last_{window}"] = None

        return {
            "player_id": player_id,
            "stat_type": stat_type,
            "season": season,
            "rolling_averages": rolling_avgs,
            "games_available": len(values),
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Baseline Stats provider

        Returns:
            Health status dictionary
        """
        try:
            # Check if Sleeper client is healthy
            sleeper_health = await self.sleeper_client.health_check()

            if sleeper_health["status"] == "healthy":
                return {
                    "service": "baseline_stats",
                    "status": "healthy",
                    "dependencies": {
                        "sleeper_api": "healthy",
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                }
            else:
                return {
                    "service": "baseline_stats",
                    "status": "degraded",
                    "dependencies": {
                        "sleeper_api": "unhealthy",
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                }

        except Exception as e:
            logger.error(f"Baseline stats health check failed: {e}")
            return {
                "service": "baseline_stats",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

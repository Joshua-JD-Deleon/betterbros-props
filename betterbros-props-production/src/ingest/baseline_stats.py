"""
Historical baseline statistics loader.

Provides historical player performance data for feature engineering.
Includes caching and support for multiple stat types.
"""

from typing import Optional, List, Dict
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import logging
import random

logger = logging.getLogger(__name__)


class BaselineStatsLoader:
    """
    Loader for historical player statistics.
    """

    CACHE_DURATION_HOURS = 24  # Stats change less frequently

    def __init__(self, data_dir: Optional[Path] = None, mock_mode: bool = True, cache_dir: Optional[Path] = None):
        """
        Initialize baseline stats loader.

        Args:
            data_dir: Directory containing historical stats files
            mock_mode: If True, return mock data
            cache_dir: Directory for caching processed stats
        """
        self.data_dir = data_dir or Path("./data")
        self.mock_mode = mock_mode
        self.cache_dir = cache_dir or Path("./data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for baseline stats."""
        return self.cache_dir / f"baseline_stats_{cache_key}.parquet"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache file exists and is within duration limit."""
        if not cache_path.exists():
            return False

        file_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        return file_age < timedelta(hours=self.CACHE_DURATION_HOURS)

    def _get_mock_stats(self) -> pd.DataFrame:
        """
        Generate comprehensive mock historical stats.

        Returns:
            DataFrame with realistic player statistics
        """
        # Expanded player database with position-specific stats
        players_data = [
            # QBs
            {
                "player_id": "player_001",
                "player_name": "Patrick Mahomes",
                "position": "QB",
                "team": "KC",
                "season": 2024,
                "games_played": 16,
                "avg_passing_yards": 285.3,
                "avg_passing_tds": 2.1,
                "avg_rushing_yards": 15.2,
                "avg_receptions": None,
                "avg_receiving_yards": None,
                "avg_receiving_tds": None,
                "consistency_score": 0.82,
                "variance": 1250.5,
                "last_3_games_avg": 295.2,
                "opponent_rank_vs_position": None,
            },
            {
                "player_id": "player_002",
                "player_name": "Josh Allen",
                "position": "QB",
                "team": "BUF",
                "season": 2024,
                "games_played": 15,
                "avg_passing_yards": 270.8,
                "avg_passing_tds": 2.3,
                "avg_rushing_yards": 45.6,
                "avg_receptions": None,
                "avg_receiving_yards": None,
                "avg_receiving_tds": None,
                "consistency_score": 0.78,
                "variance": 1580.3,
                "last_3_games_avg": 265.8,
                "opponent_rank_vs_position": None,
            },
            {
                "player_id": "player_003",
                "player_name": "Lamar Jackson",
                "position": "QB",
                "team": "BAL",
                "season": 2024,
                "games_played": 16,
                "avg_passing_yards": 248.5,
                "avg_passing_tds": 1.9,
                "avg_rushing_yards": 68.2,
                "avg_receptions": None,
                "avg_receiving_yards": None,
                "avg_receiving_tds": None,
                "consistency_score": 0.75,
                "variance": 1420.8,
                "last_3_games_avg": 255.3,
                "opponent_rank_vs_position": None,
            },
            {
                "player_id": "player_004",
                "player_name": "Jalen Hurts",
                "position": "QB",
                "team": "PHI",
                "season": 2024,
                "games_played": 17,
                "avg_passing_yards": 262.3,
                "avg_passing_tds": 2.0,
                "avg_rushing_yards": 52.8,
                "avg_receptions": None,
                "avg_receiving_yards": None,
                "avg_receiving_tds": None,
                "consistency_score": 0.81,
                "variance": 1180.2,
                "last_3_games_avg": 278.5,
                "opponent_rank_vs_position": None,
            },
            {
                "player_id": "player_005",
                "player_name": "Joe Burrow",
                "position": "QB",
                "team": "CIN",
                "season": 2024,
                "games_played": 16,
                "avg_passing_yards": 278.9,
                "avg_passing_tds": 2.2,
                "avg_rushing_yards": 8.5,
                "avg_receptions": None,
                "avg_receiving_yards": None,
                "avg_receiving_tds": None,
                "consistency_score": 0.84,
                "variance": 1085.6,
                "last_3_games_avg": 289.3,
                "opponent_rank_vs_position": None,
            },
            # WRs
            {
                "player_id": "player_006",
                "player_name": "Tyreek Hill",
                "position": "WR",
                "team": "MIA",
                "season": 2024,
                "games_played": 17,
                "avg_passing_yards": None,
                "avg_passing_tds": None,
                "avg_rushing_yards": 5.3,
                "avg_receptions": 7.2,
                "avg_receiving_yards": 92.5,
                "avg_receiving_tds": 0.65,
                "consistency_score": 0.75,
                "variance": 380.2,
                "last_3_games_avg": 98.3,
                "opponent_rank_vs_position": 15,
            },
            {
                "player_id": "player_007",
                "player_name": "Stefon Diggs",
                "position": "WR",
                "team": "BUF",
                "season": 2024,
                "games_played": 16,
                "avg_passing_yards": None,
                "avg_passing_tds": None,
                "avg_rushing_yards": 3.8,
                "avg_receptions": 7.5,
                "avg_receiving_yards": 82.3,
                "avg_receiving_tds": 0.62,
                "consistency_score": 0.80,
                "variance": 420.8,
                "last_3_games_avg": 75.5,
                "opponent_rank_vs_position": 22,
            },
            {
                "player_id": "player_008",
                "player_name": "Justin Jefferson",
                "position": "WR",
                "team": "MIN",
                "season": 2024,
                "games_played": 16,
                "avg_passing_yards": None,
                "avg_passing_tds": None,
                "avg_rushing_yards": 2.1,
                "avg_receptions": 6.8,
                "avg_receiving_yards": 95.8,
                "avg_receiving_tds": 0.68,
                "consistency_score": 0.85,
                "variance": 325.5,
                "last_3_games_avg": 102.3,
                "opponent_rank_vs_position": 18,
            },
            {
                "player_id": "player_009",
                "player_name": "CeeDee Lamb",
                "position": "WR",
                "team": "DAL",
                "season": 2024,
                "games_played": 17,
                "avg_passing_yards": None,
                "avg_passing_tds": None,
                "avg_rushing_yards": 4.5,
                "avg_receptions": 8.2,
                "avg_receiving_yards": 88.7,
                "avg_receiving_tds": 0.70,
                "consistency_score": 0.78,
                "variance": 395.8,
                "last_3_games_avg": 92.5,
                "opponent_rank_vs_position": 12,
            },
            {
                "player_id": "player_010",
                "player_name": "Ja'Marr Chase",
                "position": "WR",
                "team": "CIN",
                "season": 2024,
                "games_played": 16,
                "avg_passing_yards": None,
                "avg_passing_tds": None,
                "avg_rushing_yards": 6.8,
                "avg_receptions": 6.5,
                "avg_receiving_yards": 89.2,
                "avg_receiving_tds": 0.75,
                "consistency_score": 0.73,
                "variance": 445.2,
                "last_3_games_avg": 95.8,
                "opponent_rank_vs_position": 20,
            },
            # TEs
            {
                "player_id": "player_011",
                "player_name": "Travis Kelce",
                "position": "TE",
                "team": "KC",
                "season": 2024,
                "games_played": 14,
                "avg_passing_yards": None,
                "avg_passing_tds": None,
                "avg_rushing_yards": 2.1,
                "avg_receptions": 6.8,
                "avg_receiving_yards": 78.9,
                "avg_receiving_tds": 0.58,
                "consistency_score": 0.88,
                "variance": 290.5,
                "last_3_games_avg": 72.5,
                "opponent_rank_vs_position": 8,
            },
            {
                "player_id": "player_012",
                "player_name": "Mark Andrews",
                "position": "TE",
                "team": "BAL",
                "season": 2024,
                "games_played": 15,
                "avg_passing_yards": None,
                "avg_passing_tds": None,
                "avg_rushing_yards": 1.5,
                "avg_receptions": 5.8,
                "avg_receiving_yards": 65.3,
                "avg_receiving_tds": 0.52,
                "consistency_score": 0.76,
                "variance": 335.8,
                "last_3_games_avg": 68.2,
                "opponent_rank_vs_position": 14,
            },
            {
                "player_id": "player_013",
                "player_name": "George Kittle",
                "position": "TE",
                "team": "SF",
                "season": 2024,
                "games_played": 16,
                "avg_passing_yards": None,
                "avg_passing_tds": None,
                "avg_rushing_yards": 3.2,
                "avg_receptions": 6.2,
                "avg_receiving_yards": 72.5,
                "avg_receiving_tds": 0.48,
                "consistency_score": 0.82,
                "variance": 310.2,
                "last_3_games_avg": 75.8,
                "opponent_rank_vs_position": 11,
            },
            # RBs
            {
                "player_id": "player_014",
                "player_name": "Christian McCaffrey",
                "position": "RB",
                "team": "SF",
                "season": 2024,
                "games_played": 16,
                "avg_passing_yards": None,
                "avg_passing_tds": None,
                "avg_rushing_yards": 98.5,
                "avg_receptions": 4.5,
                "avg_receiving_yards": 35.8,
                "avg_receiving_tds": 0.35,
                "consistency_score": 0.89,
                "variance": 485.3,
                "last_3_games_avg": 105.2,
                "opponent_rank_vs_position": 25,
            },
            {
                "player_id": "player_015",
                "player_name": "Derrick Henry",
                "position": "RB",
                "team": "TEN",
                "season": 2024,
                "games_played": 17,
                "avg_passing_yards": None,
                "avg_passing_tds": None,
                "avg_rushing_yards": 92.3,
                "avg_receptions": 1.8,
                "avg_receiving_yards": 12.5,
                "avg_receiving_tds": 0.10,
                "consistency_score": 0.78,
                "variance": 625.8,
                "last_3_games_avg": 88.5,
                "opponent_rank_vs_position": 18,
            },
            {
                "player_id": "player_016",
                "player_name": "Saquon Barkley",
                "position": "RB",
                "team": "NYG",
                "season": 2024,
                "games_played": 14,
                "avg_passing_yards": None,
                "avg_passing_tds": None,
                "avg_rushing_yards": 85.2,
                "avg_receptions": 3.8,
                "avg_receiving_yards": 28.5,
                "avg_receiving_tds": 0.25,
                "consistency_score": 0.72,
                "variance": 558.3,
                "last_3_games_avg": 92.8,
                "opponent_rank_vs_position": 16,
            },
        ]

        return pd.DataFrame(players_data)

    def load_player_stats(
        self,
        player_ids: Optional[List[str]] = None,
        seasons: Optional[List[int]] = None,
        stat_types: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Load historical statistics for players.

        Args:
            player_ids: List of player IDs to load (None = all)
            seasons: List of seasons to load (None = all available)
            stat_types: List of stat types to include (None = all)

        Returns:
            DataFrame with historical statistics:
                - player_id: Unique player identifier
                - player_name: Player full name
                - position: Player position
                - team: Current team
                - season: Season year
                - games_played: Number of games played
                - avg_[stat_type]: Average per game for each stat type
                - consistency_score: Measure of consistency (0-1)
                - variance: Statistical variance in performance
                - last_3_games_avg: Average for last 3 games
                - opponent_rank_vs_position: Opponent's rank vs position (1-32)
        """
        # Generate cache key
        cache_key = f"{'-'.join(player_ids or ['all'])}_{'-'.join(map(str, seasons or ['all']))}"
        cache_path = self._get_cache_path(cache_key)

        # Check cache
        if self._is_cache_valid(cache_path):
            logger.info(f"Loading baseline stats from cache: {cache_path}")
            df = pd.read_parquet(cache_path)
        elif self.mock_mode:
            logger.info("Using mock data for baseline stats")
            df = self._get_mock_stats()
        else:
            # Try to load from data directory
            try:
                stats_file = self.data_dir / "player_stats.parquet"
                if stats_file.exists():
                    logger.info(f"Loading player stats from {stats_file}")
                    df = pd.read_parquet(stats_file)
                else:
                    logger.warning(f"Stats file not found at {stats_file}, using mock data")
                    df = self._get_mock_stats()
            except Exception as e:
                logger.error(f"Error loading player stats: {e}, using mock data")
                df = self._get_mock_stats()

        # Apply filters
        if player_ids:
            df = df[df['player_id'].isin(player_ids)]

        if seasons:
            df = df[df['season'].isin(seasons)]

        if stat_types:
            # Keep only specified stat columns plus metadata
            metadata_cols = ['player_id', 'player_name', 'position', 'team', 'season',
                           'games_played', 'consistency_score', 'variance']
            stat_cols = [col for col in df.columns if any(st in col for st in stat_types)]
            keep_cols = list(set(metadata_cols + stat_cols))
            df = df[[col for col in keep_cols if col in df.columns]]

        # Cache the filtered results
        try:
            df.to_parquet(cache_path, index=False)
            logger.info(f"Cached baseline stats to {cache_path}")
        except Exception as e:
            logger.warning(f"Failed to cache baseline stats: {e}")

        return df

    def load_matchup_history(
        self,
        team: str,
        opponent: str,
        lookback_seasons: int = 3
    ) -> pd.DataFrame:
        """
        Load historical matchup data between teams.

        Args:
            team: Team abbreviation
            opponent: Opponent team abbreviation
            lookback_seasons: Number of past seasons to include

        Returns:
            DataFrame with historical matchup statistics:
                - season: Season year
                - week: Week number
                - team_score: Team's score
                - opponent_score: Opponent's score
                - total_yards: Team's total yards
                - passing_yards: Team's passing yards
                - rushing_yards: Team's rushing yards
                - turnovers: Team's turnovers
        """
        if self.mock_mode:
            # Generate realistic mock matchup history
            current_year = datetime.now().year
            matchups = []

            for i in range(lookback_seasons):
                season = current_year - 1 - i
                # Usually teams play 1-2 times per season
                num_games = random.choice([1, 2])

                for _ in range(num_games):
                    team_score = random.randint(17, 35)
                    opp_score = random.randint(14, 31)
                    total_yards = random.randint(300, 450)

                    matchups.append({
                        "season": season,
                        "week": random.randint(1, 17),
                        "team_score": team_score,
                        "opponent_score": opp_score,
                        "total_yards": total_yards,
                        "passing_yards": int(total_yards * random.uniform(0.55, 0.75)),
                        "rushing_yards": int(total_yards * random.uniform(0.25, 0.45)),
                        "turnovers": random.randint(0, 3),
                        "result": "W" if team_score > opp_score else "L"
                    })

            return pd.DataFrame(matchups)

        # TODO: Implement matchup history lookup from stored data
        return pd.DataFrame()

    def get_player_trend(self, player_id: str, stat_type: str, weeks: int = 4) -> Dict[str, float]:
        """
        Calculate trending statistics for a player.

        Args:
            player_id: Player identifier
            stat_type: Type of statistic to trend
            weeks: Number of weeks to analyze

        Returns:
            Dictionary with trend metrics:
                - current_avg: Current average
                - trend_direction: 1.0 (up), 0.0 (flat), -1.0 (down)
                - trend_strength: 0.0 to 1.0
                - volatility: Standard deviation
        """
        # For mock mode, return realistic trend data
        if self.mock_mode:
            direction = random.choice([1.0, 1.0, 0.0, -1.0])  # Bias toward upward
            return {
                "current_avg": random.uniform(50, 100),
                "trend_direction": direction,
                "trend_strength": random.uniform(0.3, 0.9),
                "volatility": random.uniform(5, 25),
            }

        # TODO: Implement actual trend calculation from historical data
        return {}


def fetch_player_baselines(
    player_names: List[str],
    stat_types: List[str],
    mock_mode: bool = True
) -> pd.DataFrame:
    """
    Fetch baseline statistics for specified players and stat types.

    Args:
        player_names: List of player names
        stat_types: List of stat types (e.g., ['passing_yards', 'rushing_yards'])
        mock_mode: Whether to use mock data

    Returns:
        DataFrame with baseline statistics including:
            - player_name: Player name
            - stat_type: Type of statistic
            - season_avg: Season average
            - last_3_games_avg: Recent 3-game average
            - opponent_rank_vs_position: Opponent defensive rank (1-32)
    """
    loader = BaselineStatsLoader(mock_mode=mock_mode)
    df = loader.load_player_stats(stat_types=stat_types)

    # Filter by player names if specified
    if player_names:
        df = df[df['player_name'].isin(player_names)]

    return df


def load_baseline_stats(
    player_ids: Optional[List[str]] = None,
    seasons: Optional[List[int]] = None,
    mock_mode: bool = True
) -> pd.DataFrame:
    """
    Convenience function to load baseline statistics.

    Args:
        player_ids: List of player IDs to load
        seasons: List of seasons to load
        mock_mode: Whether to use mock data

    Returns:
        DataFrame with historical statistics including:
            - player_name: Player full name
            - stat_type: Type of statistic
            - season_avg: Season average value
            - last_3_games_avg: Average over last 3 games
            - opponent_rank_vs_position: Defensive rank vs position (1-32)
    """
    loader = BaselineStatsLoader(mock_mode=mock_mode)
    return loader.load_player_stats(player_ids=player_ids, seasons=seasons)

"""
Injury data provider.

ToS Compliance:
- Uses only public injury reports (as required by NFL reporting rules)
- No unauthorized data scraping
- Respects API rate limits
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import httpx
import logging
import random
import time
import os

logger = logging.getLogger(__name__)


class InjuriesProvider:
    """
    Provider for fetching and managing injury data.
    """

    ESPN_API_BASE = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
    CACHE_DURATION_HOURS = 6
    RATE_LIMIT_DELAY = 1.0
    MAX_RETRIES = 3

    def __init__(self, mock_mode: bool = True, cache_dir: Optional[Path] = None):
        """
        Initialize injuries provider.

        Args:
            mock_mode: If True, return mock data
            cache_dir: Directory for caching API responses
        """
        self.mock_mode = mock_mode
        self.last_request_time = 0.0
        self.cache_dir = cache_dir or Path("./data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _rate_limit(self) -> None:
        """Implement rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()

    def _get_cache_path(self, week: int, season: int) -> Path:
        """Get cache file path for given week/season."""
        return self.cache_dir / f"injuries_{week}_{season}.parquet"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache file exists and is within duration limit."""
        if not cache_path.exists():
            return False

        file_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        return file_age < timedelta(hours=self.CACHE_DURATION_HOURS)

    def _get_mock_injuries(self) -> pd.DataFrame:
        """
        Generate mock injury data with realistic statuses and types.

        Returns:
            DataFrame with 5-10 mock injuries
        """
        # Common NFL injuries and affected body parts
        injury_types = [
            "Ankle", "Hamstring", "Knee", "Shoulder", "Concussion",
            "Quad", "Calf", "Back", "Ribs", "Wrist"
        ]

        players = [
            ("player_001", "Patrick Mahomes", "KC", "QB"),
            ("player_006", "Tyreek Hill", "MIA", "WR"),
            ("player_011", "Travis Kelce", "KC", "TE"),
            ("player_014", "Christian McCaffrey", "SF", "RB"),
            ("player_008", "Justin Jefferson", "MIN", "WR"),
            ("player_003", "Lamar Jackson", "BAL", "QB"),
            ("player_015", "Derrick Henry", "TEN", "RB"),
        ]

        # Randomly select 5-10 players for injuries
        num_injuries = random.randint(5, 10)
        selected_players = random.sample(players, min(num_injuries, len(players)))

        mock_data = []
        for player_id, player_name, team, position in selected_players:
            status = random.choice([
                "Out", "Out", "Doubtful", "Questionable",
                "Questionable", "Questionable", "Probable"
            ])

            mock_data.append({
                "player_id": player_id,
                "player_name": player_name,
                "team": team,
                "position": position,
                "status": status,
                "injury_type": random.choice(injury_types),
                "last_updated": datetime.now() - timedelta(hours=random.randint(1, 24)),
                "expected_impact": self._get_impact_level(status),
                "weeks_out": self._get_weeks_out(status),
            })

        return pd.DataFrame(mock_data)

    def _get_impact_level(self, status: str) -> str:
        """Determine expected impact level based on injury status."""
        impact_map = {
            "Out": "High",
            "Doubtful": "High",
            "Questionable": random.choice(["Medium", "Low"]),
            "Probable": random.choice(["Low", "Minimal"]),
        }
        return impact_map.get(status, "Unknown")

    def _get_weeks_out(self, status: str) -> Optional[int]:
        """Estimate weeks out based on status."""
        if status == "Out":
            return random.randint(1, 4)
        elif status == "Doubtful":
            return random.choice([0, 1])
        return None

    def _fetch_with_retry(self, url: str, params: Optional[Dict] = None) -> Dict:
        """
        Fetch data from API with exponential backoff retry logic.

        Args:
            url: API endpoint URL
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            httpx.HTTPError: If all retries fail
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                self._rate_limit()

                with httpx.Client(timeout=30.0) as client:
                    response = client.get(url, params=params)
                    response.raise_for_status()
                    return response.json()

            except httpx.HTTPError as e:
                if attempt == self.MAX_RETRIES - 1:
                    logger.error(f"API request failed after {self.MAX_RETRIES} attempts: {e}")
                    raise

                # Exponential backoff
                wait_time = 2 ** attempt
                logger.warning(f"API request failed (attempt {attempt + 1}/{self.MAX_RETRIES}), retrying in {wait_time}s")
                time.sleep(wait_time)

    def fetch_injury_report(
        self,
        week: int,
        season: int,
        teams: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Fetch injury report for specific week.

        Args:
            week: NFL week number
            season: Season year
            teams: Optional list of team abbreviations to filter

        Returns:
            DataFrame with injury information:
                - player_id: Unique player identifier
                - player_name: Player full name
                - team: Team abbreviation
                - position: Player position
                - status: Status (Out, Doubtful, Questionable, Probable)
                - injury_type: Type of injury (body part)
                - last_updated: Timestamp of last update
                - expected_impact: Impact level (High, Medium, Low, Minimal)
                - weeks_out: Estimated weeks out (None if questionable/probable)
        """
        # Check cache first
        cache_path = self._get_cache_path(week, season)
        if self._is_cache_valid(cache_path):
            logger.info(f"Loading injuries from cache: {cache_path}")
            df = pd.read_parquet(cache_path)
            if teams:
                df = df[df['team'].isin(teams)]
            return df

        if self.mock_mode:
            logger.info("Using mock data for injuries")
            df = self._get_mock_injuries()
        else:
            try:
                logger.info(f"Fetching injury data for week {week}, season {season}")
                # ESPN has a public injuries endpoint
                url = f"{self.ESPN_API_BASE}/injuries"
                data = self._fetch_with_retry(url)

                # Parse ESPN injury data
                injuries = []
                if 'injuries' in data:
                    for injury_data in data['injuries']:
                        player = injury_data.get('athlete', {})
                        team = injury_data.get('team', {})

                        injuries.append({
                            "player_id": player.get('id', ''),
                            "player_name": player.get('displayName', ''),
                            "team": team.get('abbreviation', ''),
                            "position": player.get('position', {}).get('abbreviation', ''),
                            "status": injury_data.get('status', 'Unknown'),
                            "injury_type": injury_data.get('type', 'Unknown'),
                            "last_updated": datetime.now(),
                            "expected_impact": self._get_impact_level(injury_data.get('status', '')),
                            "weeks_out": None,
                        })

                df = pd.DataFrame(injuries)

                if df.empty:
                    logger.warning("No injury data returned from API, using mock data")
                    df = self._get_mock_injuries()

            except Exception as e:
                logger.error(f"Error fetching injury data: {e}, falling back to mock data")
                df = self._get_mock_injuries()

        # Filter by teams if specified
        if teams:
            df = df[df['team'].isin(teams)]

        # Cache the results
        try:
            df.to_parquet(cache_path, index=False)
            logger.info(f"Cached injuries to {cache_path}")
        except Exception as e:
            logger.warning(f"Failed to cache injuries: {e}")

        return df

    def get_player_injury_history(
        self,
        player_id: str,
        lookback_weeks: int = 8
    ) -> pd.DataFrame:
        """
        Get injury history for a specific player.

        Args:
            player_id: Unique player identifier
            lookback_weeks: Number of weeks to look back

        Returns:
            DataFrame with historical injury data:
                - week: Week number
                - season: Season year
                - injury_status: Status at that time
                - injury_type: Type of injury
                - games_missed: Number of games missed
        """
        if self.mock_mode:
            # Generate mock historical data
            history = []
            for i in range(random.randint(1, 3)):
                week = random.randint(max(1, lookback_weeks - 4), lookback_weeks)
                history.append({
                    "week": week,
                    "season": 2025,
                    "injury_status": random.choice(["Questionable", "Probable", "Out"]),
                    "injury_type": random.choice(["Ankle", "Hamstring", "Knee"]),
                    "games_missed": random.randint(0, 2)
                })

            return pd.DataFrame(history)

        # TODO: Implement historical injury lookup from stored data
        return pd.DataFrame()

    def get_team_injury_summary(self, team: str, week: int, season: int) -> Dict[str, int]:
        """
        Get summary of injuries for a team.

        Args:
            team: Team abbreviation
            week: Week number
            season: Season year

        Returns:
            Dictionary with counts by status
        """
        df = self.fetch_injury_report(week=week, season=season, teams=[team])

        if df.empty:
            return {"Out": 0, "Doubtful": 0, "Questionable": 0, "Probable": 0}

        summary = df['status'].value_counts().to_dict()
        return summary


def fetch_injury_report(
    week: int,
    season: int,
    teams: Optional[List[str]] = None,
    mock_mode: bool = True
) -> pd.DataFrame:
    """
    Convenience function to fetch injury report.

    Args:
        week: NFL week number
        season: Season year
        teams: Optional list of teams to filter
        mock_mode: Whether to use mock data

    Returns:
        DataFrame with injury information including:
            - player_name: Player full name
            - team: Team abbreviation
            - status: Injury status (Out/Doubtful/Questionable/Probable)
            - injury_type: Type/location of injury
    """
    provider = InjuriesProvider(mock_mode=mock_mode)
    return provider.fetch_injury_report(week=week, season=season, teams=teams)

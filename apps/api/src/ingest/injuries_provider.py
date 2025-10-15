"""
Injuries Provider for fetching NFL injury reports
"""
import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
from redis.asyncio import Redis

from src.config import settings
from src.db import get_redis

logger = logging.getLogger(__name__)


class InjuryStatus(str, Enum):
    """NFL injury status designations"""
    OUT = "out"
    DOUBTFUL = "doubtful"
    QUESTIONABLE = "questionable"
    PROBABLE = "probable"
    HEALTHY = "healthy"
    IR = "ir"  # Injured Reserve
    PUP = "pup"  # Physically Unable to Perform
    SUSPENSION = "suspension"


class InjuriesAPIError(Exception):
    """Custom exception for Injuries API errors"""
    pass


class InjuriesAPI:
    """
    Async client for fetching NFL injury reports

    Provides methods to fetch injury data from multiple sources with
    Redis caching and normalization to standard format.

    Attributes:
        cache_ttl: Cache time-to-live in seconds (default: 6 hours)
    """

    # ESPN API for injury data (public endpoint)
    ESPN_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"

    # SportsRadar API (requires API key)
    SPORTSRADAR_BASE_URL = "https://api.sportradar.com/nfl/official/trial/v7/en"

    CACHE_TTL = 21600  # 6 hours

    def __init__(
        self,
        sportsradar_api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize Injuries API client

        Args:
            sportsradar_api_key: Optional SportsRadar API key
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.sportsradar_api_key = sportsradar_api_key or settings.SPORTSRADAR_API_KEY
        self.timeout = timeout
        self.max_retries = max_retries

        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "User-Agent": "BetterBros-Props/1.0",
                "Accept": "application/json",
            },
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
            ),
        )

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def _make_request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic

        Args:
            url: Full URL to request
            params: Query parameters
            retry_count: Current retry attempt

        Returns:
            JSON response data

        Raises:
            InjuriesAPIError: If request fails
        """
        try:
            logger.debug(f"Injuries API request: {url}")

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            logger.info(f"Injuries API success: {url}")
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.warning(f"Injuries API HTTP error: {e.response.status_code}")

            if e.response.status_code >= 500 and retry_count < self.max_retries:
                backoff = 2 ** retry_count
                await asyncio.sleep(backoff)
                return await self._make_request(url, params, retry_count + 1)

            raise InjuriesAPIError(f"HTTP {e.response.status_code}: {e.response.text}")

        except httpx.RequestError as e:
            logger.error(f"Injuries API request error: {e}")

            if retry_count < self.max_retries:
                backoff = 2 ** retry_count
                await asyncio.sleep(backoff)
                return await self._make_request(url, params, retry_count + 1)

            raise InjuriesAPIError(f"Request failed: {str(e)}")

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

    def _normalize_injury_status(self, status: str) -> InjuryStatus:
        """
        Normalize injury status from various sources to standard enum

        Args:
            status: Raw status string from API

        Returns:
            Normalized InjuryStatus enum
        """
        status_lower = status.lower().strip()

        # Mapping of various status strings to our enum
        status_map = {
            "out": InjuryStatus.OUT,
            "o": InjuryStatus.OUT,
            "doubtful": InjuryStatus.DOUBTFUL,
            "d": InjuryStatus.DOUBTFUL,
            "questionable": InjuryStatus.QUESTIONABLE,
            "q": InjuryStatus.QUESTIONABLE,
            "probable": InjuryStatus.PROBABLE,
            "p": InjuryStatus.PROBABLE,
            "healthy": InjuryStatus.HEALTHY,
            "active": InjuryStatus.HEALTHY,
            "ir": InjuryStatus.IR,
            "injured reserve": InjuryStatus.IR,
            "pup": InjuryStatus.PUP,
            "suspension": InjuryStatus.SUSPENSION,
            "suspended": InjuryStatus.SUSPENSION,
        }

        return status_map.get(status_lower, InjuryStatus.QUESTIONABLE)

    async def _fetch_espn_injuries(self, week: int) -> List[Dict[str, Any]]:
        """
        Fetch injuries from ESPN API

        Args:
            week: NFL week number

        Returns:
            List of injury records
        """
        try:
            # ESPN injuries endpoint
            url = f"{self.ESPN_BASE_URL}/injuries"
            data = await self._make_request(url)

            injuries = []
            teams = data.get("injuries", [])

            for team_data in teams:
                team_abbr = team_data.get("team", {}).get("abbreviation", "UNK")

                for injury in team_data.get("injuries", []):
                    athlete = injury.get("athlete", {})
                    player_id = athlete.get("id")
                    player_name = athlete.get("displayName", "Unknown")

                    status_raw = injury.get("status", {}).get("type", "")
                    status = self._normalize_injury_status(status_raw)

                    injury_type = injury.get("details", {}).get("type", "")
                    description = injury.get("details", {}).get("detail", "")

                    injuries.append({
                        "player_id": str(player_id) if player_id else None,
                        "player_name": player_name,
                        "team": team_abbr,
                        "status": status.value,
                        "injury_type": injury_type or None,
                        "description": description or None,
                        "source": "espn",
                    })

            logger.info(f"Fetched {len(injuries)} injuries from ESPN")
            return injuries

        except Exception as e:
            logger.error(f"Failed to fetch ESPN injuries: {e}")
            return []

    async def _fetch_sportsradar_injuries(
        self,
        season: str,
        week: int,
    ) -> List[Dict[str, Any]]:
        """
        Fetch injuries from SportsRadar API (requires API key)

        Args:
            season: Season year
            week: NFL week number

        Returns:
            List of injury records
        """
        if not self.sportsradar_api_key:
            logger.warning("SportsRadar API key not configured, skipping")
            return []

        try:
            # SportsRadar weekly injuries endpoint
            url = f"{self.SPORTSRADAR_BASE_URL}/seasons/{season}/REG/weeks/{week}/injuries.json"
            params = {"api_key": self.sportsradar_api_key}

            data = await self._make_request(url, params=params)

            injuries = []
            teams = data.get("teams", [])

            for team_data in teams:
                team_abbr = team_data.get("alias", "UNK")

                for player_data in team_data.get("players", []):
                    player_id = player_data.get("id")
                    player_name = player_data.get("name", "Unknown")

                    injury_data = player_data.get("injury", {})
                    status_raw = injury_data.get("status", "")
                    status = self._normalize_injury_status(status_raw)

                    injury_type = injury_data.get("description", "")

                    injuries.append({
                        "player_id": str(player_id) if player_id else None,
                        "player_name": player_name,
                        "team": team_abbr,
                        "status": status.value,
                        "injury_type": injury_type or None,
                        "description": None,
                        "source": "sportsradar",
                    })

            logger.info(f"Fetched {len(injuries)} injuries from SportsRadar")
            return injuries

        except Exception as e:
            logger.error(f"Failed to fetch SportsRadar injuries: {e}")
            return []

    async def get_injury_report(
        self,
        week: int,
        season: Optional[str] = None,
        team: Optional[str] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Fetch comprehensive injury report for a given week

        Aggregates injury data from multiple sources and normalizes format.
        Results are cached for 6 hours.

        Args:
            week: NFL week number (1-18)
            season: Season year (defaults to current year)
            team: Optional team filter (abbreviation)
            use_cache: Whether to use Redis cache

        Returns:
            Injury report with metadata

        Example:
            {
                "week": 5,
                "season": "2024",
                "injuries": [
                    {
                        "player_id": "421",
                        "player_name": "Patrick Mahomes",
                        "team": "KC",
                        "status": "questionable",
                        "injury_type": "ankle",
                        "description": "High ankle sprain",
                        "source": "espn"
                    }
                ],
                "last_updated": "2024-10-14T10:30:00Z",
                "source": "aggregated"
            }
        """
        if season is None:
            season = str(datetime.utcnow().year)

        cache_key = f"injuries:nfl:{season}:week_{week}"
        if team:
            cache_key += f":{team}"

        redis = await get_redis()

        try:
            # Check cache
            if use_cache:
                cached = await self._get_cached(redis, cache_key)
                if cached:
                    return cached

            # Fetch from multiple sources in parallel
            espn_task = self._fetch_espn_injuries(week)
            sportsradar_task = self._fetch_sportsradar_injuries(season, week)

            espn_injuries, sportsradar_injuries = await asyncio.gather(
                espn_task,
                sportsradar_task,
                return_exceptions=True,
            )

            # Handle exceptions from gather
            if isinstance(espn_injuries, Exception):
                logger.error(f"ESPN injuries failed: {espn_injuries}")
                espn_injuries = []
            if isinstance(sportsradar_injuries, Exception):
                logger.error(f"SportsRadar injuries failed: {sportsradar_injuries}")
                sportsradar_injuries = []

            # Merge and deduplicate injuries
            all_injuries = []
            seen_players = set()

            # Prioritize SportsRadar data (more reliable)
            for injury in sportsradar_injuries:
                player_key = f"{injury['player_name']}:{injury['team']}"
                if player_key not in seen_players:
                    all_injuries.append(injury)
                    seen_players.add(player_key)

            # Add ESPN data if not already present
            for injury in espn_injuries:
                player_key = f"{injury['player_name']}:{injury['team']}"
                if player_key not in seen_players:
                    all_injuries.append(injury)
                    seen_players.add(player_key)

            # Filter by team if specified
            if team:
                all_injuries = [
                    inj for inj in all_injuries
                    if inj["team"].upper() == team.upper()
                ]

            result = {
                "week": week,
                "season": season,
                "injuries": all_injuries,
                "total_injuries": len(all_injuries),
                "last_updated": datetime.utcnow().isoformat(),
                "source": "aggregated",
            }

            # Cache the results
            if use_cache:
                await self._set_cached(redis, cache_key, result, self.CACHE_TTL)

            logger.info(f"Compiled injury report: {len(all_injuries)} injuries for week {week}")
            return result

        finally:
            await redis.close()

    async def get_player_injury(
        self,
        player_name: str,
        week: int,
        season: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get injury information for a specific player

        Args:
            player_name: Player name to search for
            week: NFL week number
            season: Season year

        Returns:
            Player injury data or None if not found
        """
        report = await self.get_injury_report(week, season=season)

        for injury in report["injuries"]:
            if injury["player_name"].lower() == player_name.lower():
                return injury

        return None

    async def get_team_injuries(
        self,
        team: str,
        week: int,
        season: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all injuries for a specific team

        Args:
            team: Team abbreviation
            week: NFL week number
            season: Season year

        Returns:
            List of team injuries
        """
        report = await self.get_injury_report(week, season=season, team=team)
        return report["injuries"]

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on injury data sources

        Returns:
            Health status dictionary
        """
        try:
            # Test ESPN endpoint (always available)
            espn_injuries = await self._fetch_espn_injuries(week=1)

            sources_available = ["espn"]
            if self.sportsradar_api_key:
                sources_available.append("sportsradar")

            return {
                "service": "injuries_api",
                "status": "healthy",
                "sources_available": sources_available,
                "test_results": {
                    "espn": len(espn_injuries) > 0,
                },
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Injuries API health check failed: {e}")
            return {
                "service": "injuries_api",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

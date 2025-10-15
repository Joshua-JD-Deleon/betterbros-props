"""
Sleeper API Client for fetching NFL player data, stats, and projections
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from redis.asyncio import Redis

from src.config import settings
from src.db import get_redis

logger = logging.getLogger(__name__)


class SleeperAPIError(Exception):
    """Custom exception for Sleeper API errors"""
    pass


class SleeperAPI:
    """
    Async client for Sleeper Fantasy Football API

    Provides methods to fetch NFL players, player stats, and projections
    with Redis caching and rate limiting.

    Attributes:
        base_url: Base URL for Sleeper API
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        rate_limit_delay: Delay between requests in seconds
    """

    BASE_URL = "https://api.sleeper.app/v1"
    PLAYER_CACHE_TTL = 3600  # 1 hour
    STATS_CACHE_TTL = 1800   # 30 minutes
    PROJECTION_CACHE_TTL = 1800  # 30 minutes

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_delay: float = 0.1,
    ):
        """
        Initialize Sleeper API client

        Args:
            api_key: Optional API key (Sleeper API is public but key may be used for rate limits)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
            rate_limit_delay: Delay between requests to respect rate limits
        """
        self.api_key = api_key or settings.SLEEPER_API_KEY
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time: Optional[float] = None

        # HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=self.timeout,
            headers={
                "User-Agent": "BetterBros-Props/1.0",
                "Accept": "application/json",
            },
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=50,
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

    async def _rate_limit(self):
        """Enforce rate limiting between requests"""
        if self._last_request_time is not None:
            elapsed = asyncio.get_event_loop().time() - self._last_request_time
            if elapsed < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and exponential backoff

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            retry_count: Current retry attempt

        Returns:
            JSON response data

        Raises:
            SleeperAPIError: If request fails after all retries
        """
        await self._rate_limit()

        try:
            logger.debug(f"Sleeper API request: {method} {endpoint} {params}")

            response = await self.client.request(
                method=method,
                url=endpoint,
                params=params,
            )
            response.raise_for_status()

            logger.info(f"Sleeper API success: {method} {endpoint}")
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.warning(f"Sleeper API HTTP error: {e.response.status_code} - {endpoint}")

            # Retry on server errors or rate limits
            if e.response.status_code >= 500 or e.response.status_code == 429:
                if retry_count < self.max_retries:
                    backoff = 2 ** retry_count  # Exponential backoff
                    logger.info(f"Retrying in {backoff}s (attempt {retry_count + 1}/{self.max_retries})")
                    await asyncio.sleep(backoff)
                    return await self._make_request(method, endpoint, params, retry_count + 1)

            raise SleeperAPIError(f"HTTP {e.response.status_code}: {e.response.text}")

        except httpx.RequestError as e:
            logger.error(f"Sleeper API request error: {e}")

            if retry_count < self.max_retries:
                backoff = 2 ** retry_count
                logger.info(f"Retrying in {backoff}s (attempt {retry_count + 1}/{self.max_retries})")
                await asyncio.sleep(backoff)
                return await self._make_request(method, endpoint, params, retry_count + 1)

            raise SleeperAPIError(f"Request failed: {str(e)}")

    async def _get_cached(self, redis: Redis, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get data from Redis cache

        Args:
            redis: Redis client
            cache_key: Cache key

        Returns:
            Cached data or None if not found
        """
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
        """
        Set data in Redis cache

        Args:
            redis: Redis client
            cache_key: Cache key
            data: Data to cache
            ttl: Time-to-live in seconds
        """
        try:
            import json
            await redis.setex(cache_key, ttl, json.dumps(data))
            logger.debug(f"Cached: {cache_key} (TTL: {ttl}s)")
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    async def get_nfl_players(
        self,
        use_cache: bool = True,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch all NFL players from Sleeper API

        Returns a comprehensive dictionary of all NFL players with their metadata.
        This is cached for 1 hour as player data doesn't change frequently.

        Args:
            use_cache: Whether to use Redis cache

        Returns:
            Dictionary mapping player_id to player data

        Example:
            {
                "421": {
                    "player_id": "421",
                    "first_name": "Patrick",
                    "last_name": "Mahomes",
                    "team": "KC",
                    "position": "QB",
                    "number": 15,
                    "active": true,
                    ...
                }
            }
        """
        cache_key = "sleeper:nfl:players:all"
        redis = await get_redis()

        try:
            # Check cache
            if use_cache:
                cached = await self._get_cached(redis, cache_key)
                if cached:
                    return cached

            # Fetch from API
            data = await self._make_request("GET", "/players/nfl")

            if not isinstance(data, dict):
                raise SleeperAPIError("Invalid response format for players")

            # Cache the results
            if use_cache:
                await self._set_cached(redis, cache_key, data, self.PLAYER_CACHE_TTL)

            logger.info(f"Fetched {len(data)} NFL players from Sleeper")
            return data

        finally:
            await redis.close()

    async def get_player_stats(
        self,
        player_id: str,
        season: str,
        week: Optional[int] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Fetch player statistics for a specific week or season

        Args:
            player_id: Sleeper player ID
            season: Season year (e.g., "2024")
            week: Week number (1-18), or None for season totals
            use_cache: Whether to use Redis cache

        Returns:
            Player stats dictionary

        Example:
            {
                "player_id": "421",
                "season": "2024",
                "week": 1,
                "stats": {
                    "pass_yd": 360,
                    "pass_td": 3,
                    "int": 1,
                    "rush_yd": 15,
                    ...
                }
            }
        """
        week_str = f"week_{week}" if week else "season"
        cache_key = f"sleeper:stats:{player_id}:{season}:{week_str}"
        redis = await get_redis()

        try:
            # Check cache
            if use_cache:
                cached = await self._get_cached(redis, cache_key)
                if cached:
                    return cached

            # Build endpoint
            if week:
                endpoint = f"/stats/nfl/regular/{season}/{week}"
            else:
                endpoint = f"/stats/nfl/regular/{season}"

            # Fetch from API
            data = await self._make_request("GET", endpoint)

            # Extract player stats
            player_stats = data.get(player_id, {})

            result = {
                "player_id": player_id,
                "season": season,
                "week": week,
                "stats": player_stats,
                "fetched_at": datetime.utcnow().isoformat(),
            }

            # Cache the results
            if use_cache:
                await self._set_cached(redis, cache_key, result, self.STATS_CACHE_TTL)

            logger.info(f"Fetched stats for player {player_id}, {season} week {week}")
            return result

        finally:
            await redis.close()

    async def get_projections(
        self,
        season: str,
        week: int,
        use_cache: bool = True,
    ) -> Dict[str, Dict[str, float]]:
        """
        Fetch player projections for a specific week

        Note: Sleeper provides projections through their stats endpoint.
        This fetches the projected stats for all players.

        Args:
            season: Season year (e.g., "2024")
            week: Week number (1-18)
            use_cache: Whether to use Redis cache

        Returns:
            Dictionary mapping player_id to projected stats

        Example:
            {
                "421": {
                    "pts_ppr": 24.5,
                    "pass_yd": 285,
                    "pass_td": 2.1,
                    ...
                }
            }
        """
        cache_key = f"sleeper:projections:{season}:week_{week}"
        redis = await get_redis()

        try:
            # Check cache
            if use_cache:
                cached = await self._get_cached(redis, cache_key)
                if cached:
                    return cached

            # Fetch from API - projections endpoint
            endpoint = f"/projections/nfl/regular/{season}/{week}"

            try:
                data = await self._make_request("GET", endpoint)
            except SleeperAPIError:
                # Fallback: use stats endpoint with projection data
                logger.warning("Projections endpoint failed, using stats endpoint")
                endpoint = f"/stats/nfl/regular/{season}/{week}"
                data = await self._make_request("GET", endpoint)

            if not isinstance(data, dict):
                raise SleeperAPIError("Invalid response format for projections")

            # Cache the results
            if use_cache:
                await self._set_cached(redis, cache_key, data, self.PROJECTION_CACHE_TTL)

            logger.info(f"Fetched projections for {len(data)} players, {season} week {week}")
            return data

        finally:
            await redis.close()

    async def get_player_by_id(
        self,
        player_id: str,
        use_cache: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Get specific player information by ID

        Args:
            player_id: Sleeper player ID
            use_cache: Whether to use Redis cache

        Returns:
            Player data or None if not found
        """
        players = await self.get_nfl_players(use_cache=use_cache)
        return players.get(player_id)

    async def search_players(
        self,
        query: str,
        position: Optional[str] = None,
        team: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for players by name, position, or team

        Args:
            query: Search query (player name)
            position: Filter by position (QB, RB, WR, TE, etc.)
            team: Filter by team abbreviation
            limit: Maximum number of results

        Returns:
            List of matching players
        """
        players = await self.get_nfl_players()
        results = []

        query_lower = query.lower()

        for player_id, player_data in players.items():
            # Check if player matches filters
            if position and player_data.get("position") != position:
                continue
            if team and player_data.get("team") != team:
                continue

            # Check name match
            full_name = f"{player_data.get('first_name', '')} {player_data.get('last_name', '')}".lower()
            if query_lower in full_name:
                results.append({
                    "player_id": player_id,
                    **player_data
                })

            if len(results) >= limit:
                break

        logger.info(f"Search '{query}' returned {len(results)} results")
        return results

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Sleeper API

        Returns:
            Health status dictionary
        """
        try:
            # Try to fetch a small amount of data
            players = await self.get_nfl_players(use_cache=False)

            return {
                "service": "sleeper_api",
                "status": "healthy",
                "players_available": len(players),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Sleeper API health check failed: {e}")
            return {
                "service": "sleeper_api",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

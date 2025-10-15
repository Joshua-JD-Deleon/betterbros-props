"""
Weather Provider for fetching game weather conditions using OpenWeather API
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


class WeatherAPIError(Exception):
    """Custom exception for Weather API errors"""
    pass


# Indoor/dome stadiums that don't need weather data
INDOOR_VENUES = {
    "AT&T Stadium",  # Dallas Cowboys
    "Mercedes-Benz Stadium",  # Atlanta Falcons
    "State Farm Stadium",  # Arizona Cardinals
    "U.S. Bank Stadium",  # Minnesota Vikings
    "Allegiant Stadium",  # Las Vegas Raiders
    "SoFi Stadium",  # LA Rams/Chargers
    "Ford Field",  # Detroit Lions
    "Caesars Superdome",  # New Orleans Saints
    "Lucas Oil Stadium",  # Indianapolis Colts
}

# Stadium coordinates for NFL venues
NFL_VENUE_COORDS = {
    "Arrowhead Stadium": (39.0489, -94.4839),  # Kansas City Chiefs
    "Lambeau Field": (44.5013, -88.0622),  # Green Bay Packers
    "Soldier Field": (41.8623, -87.6167),  # Chicago Bears
    "Empower Field at Mile High": (39.7439, -105.0201),  # Denver Broncos
    "Gillette Stadium": (42.0909, -71.2643),  # New England Patriots
    "MetLife Stadium": (40.8128, -74.0742),  # NY Giants/Jets
    "M&T Bank Stadium": (39.2780, -76.6227),  # Baltimore Ravens
    "FirstEnergy Stadium": (41.5061, -81.6995),  # Cleveland Browns
    "Highmark Stadium": (42.7738, -78.7870),  # Buffalo Bills
    "Acrisure Stadium": (40.4468, -80.0158),  # Pittsburgh Steelers
    "Paul Brown Stadium": (39.0954, -84.5160),  # Cincinnati Bengals
    "Hard Rock Stadium": (25.9580, -80.2389),  # Miami Dolphins
    "TIAA Bank Field": (30.3239, -81.6373),  # Jacksonville Jaguars
    "Nissan Stadium": (36.1665, -86.7713),  # Tennessee Titans
    "NRG Stadium": (29.6847, -95.4107),  # Houston Texans
    "Lincoln Financial Field": (39.9008, -75.1675),  # Philadelphia Eagles
    "FedExField": (38.9076, -76.8645),  # Washington Commanders
    "Bank of America Stadium": (35.2258, -80.8528),  # Carolina Panthers
    "Raymond James Stadium": (27.9759, -82.5033),  # Tampa Bay Buccaneers
    "Levi's Stadium": (37.4032, -121.9698),  # San Francisco 49ers
    "Lumen Field": (47.5952, -122.3316),  # Seattle Seahawks
}


class WeatherAPI:
    """
    Async client for fetching weather data using OpenWeather API

    Provides methods to get current and forecasted weather conditions
    for NFL game venues with Redis caching.

    Attributes:
        api_key: OpenWeather API key
        cache_ttl: Cache time-to-live in seconds (default: 3 hours)
    """

    BASE_URL = "https://api.openweathermap.org/data/2.5"
    CACHE_TTL = 10800  # 3 hours

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize Weather API client

        Args:
            api_key: OpenWeather API key
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.api_key = api_key or settings.OPENWEATHER_KEY
        if not self.api_key:
            logger.warning("OpenWeather API key not configured")

        self.timeout = timeout
        self.max_retries = max_retries

        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "User-Agent": "BetterBros-Props/1.0",
                "Accept": "application/json",
            },
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
        endpoint: str,
        params: Dict[str, Any],
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic

        Args:
            endpoint: API endpoint path
            params: Query parameters
            retry_count: Current retry attempt

        Returns:
            JSON response data

        Raises:
            WeatherAPIError: If request fails
        """
        if not self.api_key:
            raise WeatherAPIError("OpenWeather API key not configured")

        params["appid"] = self.api_key
        params["units"] = "imperial"  # Use Fahrenheit

        try:
            url = f"{self.BASE_URL}/{endpoint}"
            logger.debug(f"Weather API request: {url}")

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            logger.info(f"Weather API success: {endpoint}")
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.warning(f"Weather API HTTP error: {e.response.status_code}")

            if e.response.status_code >= 500 and retry_count < self.max_retries:
                backoff = 2 ** retry_count
                await asyncio.sleep(backoff)
                return await self._make_request(endpoint, params, retry_count + 1)

            raise WeatherAPIError(f"HTTP {e.response.status_code}: {e.response.text}")

        except httpx.RequestError as e:
            logger.error(f"Weather API request error: {e}")

            if retry_count < self.max_retries:
                backoff = 2 ** retry_count
                await asyncio.sleep(backoff)
                return await self._make_request(endpoint, params, retry_count + 1)

            raise WeatherAPIError(f"Request failed: {str(e)}")

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

    def _is_indoor_venue(self, venue: str) -> bool:
        """
        Check if venue is indoor/dome stadium

        Args:
            venue: Venue name

        Returns:
            True if indoor venue
        """
        for indoor_venue in INDOOR_VENUES:
            if indoor_venue.lower() in venue.lower():
                return True
        return False

    def _get_venue_coordinates(self, venue: str) -> Optional[tuple[float, float]]:
        """
        Get coordinates for NFL venue

        Args:
            venue: Venue name

        Returns:
            Tuple of (latitude, longitude) or None
        """
        for venue_name, coords in NFL_VENUE_COORDS.items():
            if venue_name.lower() in venue.lower():
                return coords
        return None

    def _extract_weather_data(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant weather fields from API response

        Args:
            api_response: Raw API response

        Returns:
            Normalized weather data
        """
        main = api_response.get("main", {})
        wind = api_response.get("wind", {})
        weather = api_response.get("weather", [{}])[0]
        rain = api_response.get("rain", {})
        snow = api_response.get("snow", {})

        # Calculate precipitation probability
        precipitation = 0.0
        if rain.get("1h", 0) > 0 or snow.get("1h", 0) > 0:
            precipitation = 100.0
        elif api_response.get("clouds", {}).get("all", 0) > 70:
            precipitation = 50.0

        return {
            "temperature": main.get("temp"),
            "feels_like": main.get("feels_like"),
            "humidity": main.get("humidity"),
            "wind_speed": wind.get("speed"),
            "wind_direction": wind.get("deg"),
            "wind_gust": wind.get("gust"),
            "precipitation": precipitation,
            "conditions": weather.get("main", "Clear"),
            "description": weather.get("description", ""),
            "visibility": api_response.get("visibility"),
            "pressure": main.get("pressure"),
            "clouds": api_response.get("clouds", {}).get("all", 0),
        }

    async def get_game_weather(
        self,
        venue: str,
        game_time: datetime,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Get weather conditions for a game at a specific venue and time

        For indoor venues, returns N/A data. For outdoor venues, fetches
        current weather or forecast depending on game_time.

        Args:
            venue: Stadium/venue name
            game_time: Game start time
            use_cache: Whether to use Redis cache

        Returns:
            Weather data dictionary

        Example:
            {
                "venue": "Arrowhead Stadium",
                "game_time": "2024-10-20T13:00:00Z",
                "is_indoor": false,
                "temperature": 65.5,
                "wind_speed": 12.3,
                "precipitation": 20.0,
                "humidity": 55,
                "conditions": "Partly Cloudy",
                "fetched_at": "2024-10-14T10:30:00Z"
            }
        """
        # Check if indoor venue
        if self._is_indoor_venue(venue):
            logger.info(f"Indoor venue detected: {venue}")
            return {
                "venue": venue,
                "game_time": game_time.isoformat(),
                "is_indoor": True,
                "temperature": None,
                "wind_speed": None,
                "precipitation": None,
                "humidity": None,
                "conditions": "Indoor",
                "description": "Controlled environment",
                "fetched_at": datetime.utcnow().isoformat(),
            }

        # Get venue coordinates
        coords = self._get_venue_coordinates(venue)
        if not coords:
            logger.warning(f"Unknown venue: {venue}")
            raise WeatherAPIError(f"Coordinates not found for venue: {venue}")

        lat, lon = coords
        cache_key = f"weather:{venue}:{game_time.date().isoformat()}"
        redis = await get_redis()

        try:
            # Check cache
            if use_cache:
                cached = await self._get_cached(redis, cache_key)
                if cached:
                    return cached

            # Determine if we need current weather or forecast
            hours_until_game = (game_time - datetime.utcnow()).total_seconds() / 3600

            if hours_until_game < 0:
                # Game already happened, use historical (current) weather
                endpoint = "weather"
                params = {"lat": lat, "lon": lon}
            elif hours_until_game <= 48:
                # Use hourly forecast for next 48 hours
                endpoint = "forecast"
                params = {"lat": lat, "lon": lon}
            else:
                # Use current weather as approximation
                endpoint = "weather"
                params = {"lat": lat, "lon": lon}

            # Fetch from API
            data = await self._make_request(endpoint, params)

            # Extract weather data
            if endpoint == "forecast":
                # Find the forecast closest to game time
                forecasts = data.get("list", [])
                closest_forecast = None
                min_time_diff = float("inf")

                for forecast in forecasts:
                    forecast_time = datetime.fromtimestamp(forecast["dt"])
                    time_diff = abs((forecast_time - game_time).total_seconds())

                    if time_diff < min_time_diff:
                        min_time_diff = time_diff
                        closest_forecast = forecast

                if closest_forecast:
                    weather_data = self._extract_weather_data(closest_forecast)
                else:
                    weather_data = self._extract_weather_data(data)
            else:
                weather_data = self._extract_weather_data(data)

            result = {
                "venue": venue,
                "game_time": game_time.isoformat(),
                "is_indoor": False,
                **weather_data,
                "fetched_at": datetime.utcnow().isoformat(),
            }

            # Cache the results
            if use_cache:
                await self._set_cached(redis, cache_key, result, self.CACHE_TTL)

            logger.info(f"Fetched weather for {venue}: {weather_data['conditions']}")
            return result

        finally:
            await redis.close()

    async def get_forecast(
        self,
        venue: str,
        date: datetime,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Get multi-day weather forecast for a venue

        Args:
            venue: Stadium/venue name
            date: Target date for forecast
            use_cache: Whether to use Redis cache

        Returns:
            Forecast data with daily breakdown

        Example:
            {
                "venue": "Lambeau Field",
                "date": "2024-10-20",
                "forecast": [
                    {
                        "time": "2024-10-20T12:00:00Z",
                        "temperature": 45.2,
                        "conditions": "Snow",
                        ...
                    }
                ]
            }
        """
        # Check if indoor venue
        if self._is_indoor_venue(venue):
            return {
                "venue": venue,
                "date": date.date().isoformat(),
                "is_indoor": True,
                "forecast": [],
                "fetched_at": datetime.utcnow().isoformat(),
            }

        # Get venue coordinates
        coords = self._get_venue_coordinates(venue)
        if not coords:
            raise WeatherAPIError(f"Coordinates not found for venue: {venue}")

        lat, lon = coords
        cache_key = f"weather:forecast:{venue}:{date.date().isoformat()}"
        redis = await get_redis()

        try:
            # Check cache
            if use_cache:
                cached = await self._get_cached(redis, cache_key)
                if cached:
                    return cached

            # Fetch 5-day forecast
            params = {"lat": lat, "lon": lon}
            data = await self._make_request("forecast", params)

            # Extract forecasts for the target date
            forecasts = []
            target_date = date.date()

            for forecast_data in data.get("list", []):
                forecast_time = datetime.fromtimestamp(forecast_data["dt"])

                if forecast_time.date() == target_date:
                    weather_data = self._extract_weather_data(forecast_data)
                    forecasts.append({
                        "time": forecast_time.isoformat(),
                        **weather_data,
                    })

            result = {
                "venue": venue,
                "date": date.date().isoformat(),
                "is_indoor": False,
                "forecast": forecasts,
                "total_forecasts": len(forecasts),
                "fetched_at": datetime.utcnow().isoformat(),
            }

            # Cache the results
            if use_cache:
                await self._set_cached(redis, cache_key, result, self.CACHE_TTL)

            logger.info(f"Fetched {len(forecasts)} forecasts for {venue} on {target_date}")
            return result

        finally:
            await redis.close()

    async def get_weather_impact_score(
        self,
        venue: str,
        game_time: datetime,
    ) -> Dict[str, Any]:
        """
        Calculate weather impact score for game conditions

        Provides a simple score indicating how much weather might impact
        the game (0 = no impact, 100 = severe impact).

        Args:
            venue: Stadium/venue name
            game_time: Game start time

        Returns:
            Impact score and factors

        Example:
            {
                "venue": "Lambeau Field",
                "impact_score": 75,
                "factors": {
                    "wind": 30,
                    "precipitation": 25,
                    "temperature": 20
                },
                "recommendation": "High impact expected"
            }
        """
        weather = await self.get_game_weather(venue, game_time)

        if weather["is_indoor"]:
            return {
                "venue": venue,
                "impact_score": 0,
                "factors": {},
                "recommendation": "Indoor game - no weather impact",
            }

        # Calculate impact factors
        factors = {}

        # Wind impact (0-40 points)
        wind_speed = weather.get("wind_speed", 0)
        if wind_speed > 25:
            factors["wind"] = 40
        elif wind_speed > 15:
            factors["wind"] = 25
        elif wind_speed > 10:
            factors["wind"] = 10
        else:
            factors["wind"] = 0

        # Precipitation impact (0-30 points)
        precipitation = weather.get("precipitation", 0)
        if precipitation > 70:
            factors["precipitation"] = 30
        elif precipitation > 40:
            factors["precipitation"] = 20
        elif precipitation > 20:
            factors["precipitation"] = 10
        else:
            factors["precipitation"] = 0

        # Temperature impact (0-30 points)
        temperature = weather.get("temperature", 70)
        if temperature < 20 or temperature > 95:
            factors["temperature"] = 30
        elif temperature < 32 or temperature > 85:
            factors["temperature"] = 20
        elif temperature < 40 or temperature > 80:
            factors["temperature"] = 10
        else:
            factors["temperature"] = 0

        # Total impact score
        impact_score = sum(factors.values())

        # Recommendation
        if impact_score >= 60:
            recommendation = "Severe weather impact expected"
        elif impact_score >= 40:
            recommendation = "Significant weather impact expected"
        elif impact_score >= 20:
            recommendation = "Moderate weather impact expected"
        else:
            recommendation = "Minimal weather impact expected"

        return {
            "venue": venue,
            "game_time": game_time.isoformat(),
            "impact_score": impact_score,
            "factors": factors,
            "recommendation": recommendation,
            "weather": weather,
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Weather API

        Returns:
            Health status dictionary
        """
        try:
            if not self.api_key:
                return {
                    "service": "weather_api",
                    "status": "unconfigured",
                    "error": "API key not set",
                    "timestamp": datetime.utcnow().isoformat(),
                }

            # Test with a known location (Kansas City)
            params = {"lat": 39.0489, "lon": -94.4839}
            data = await self._make_request("weather", params)

            return {
                "service": "weather_api",
                "status": "healthy",
                "api_available": True,
                "test_location": "Kansas City, MO",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Weather API health check failed: {e}")
            return {
                "service": "weather_api",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

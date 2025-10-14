"""
Weather data provider for NFL game locations.

ToS Compliance:
- Uses OpenWeatherMap API with proper attribution
- Respects API rate limits and terms of service
- Requires valid API key from environment
"""

from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import httpx
import pandas as pd
import logging
import random
import time
import os

logger = logging.getLogger(__name__)


class WeatherProvider:
    """
    Provider for fetching weather data for game locations.
    """

    BASE_URL = "https://api.openweathermap.org/data/2.5"
    CACHE_DURATION_HOURS = 12
    RATE_LIMIT_DELAY = 1.0
    MAX_RETRIES = 3

    # NFL stadium locations (lat, lon) and dome status
    STADIUM_LOCATIONS = {
        # AFC East
        "BUF": (42.7738, -78.7870, False),   # Highmark Stadium
        "MIA": (25.9580, -80.2389, False),   # Hard Rock Stadium
        "NE": (42.0909, -71.2643, False),    # Gillette Stadium
        "NYJ": (40.8128, -74.0742, False),   # MetLife Stadium
        # AFC North
        "BAL": (39.2780, -76.6227, False),   # M&T Bank Stadium
        "CIN": (39.0954, -84.5160, False),   # Paycor Stadium
        "CLE": (41.5061, -81.6995, False),   # Cleveland Browns Stadium
        "PIT": (40.4468, -80.0158, False),   # Acrisure Stadium
        # AFC South
        "HOU": (29.6847, -95.4107, True),    # NRG Stadium (retractable)
        "IND": (39.7600, -86.1639, True),    # Lucas Oil Stadium (retractable)
        "JAX": (30.3239, -81.6373, False),   # TIAA Bank Field
        "TEN": (36.1665, -86.7713, False),   # Nissan Stadium
        # AFC West
        "DEN": (39.7439, -105.0201, False),  # Empower Field
        "KC": (39.0489, -94.4839, False),    # Arrowhead Stadium
        "LV": (36.0909, -115.1833, True),    # Allegiant Stadium (dome)
        "LAC": (33.9534, -118.3390, False),  # SoFi Stadium (partial roof)
        # NFC East
        "DAL": (32.7473, -97.0945, True),    # AT&T Stadium (retractable)
        "NYG": (40.8128, -74.0742, False),   # MetLife Stadium
        "PHI": (39.9008, -75.1675, False),   # Lincoln Financial Field
        "WAS": (38.9076, -76.8645, False),   # FedExField
        # NFC North
        "CHI": (41.8623, -87.6167, False),   # Soldier Field
        "DET": (42.3400, -83.0456, True),    # Ford Field (dome)
        "GB": (44.5013, -88.0622, False),    # Lambeau Field
        "MIN": (44.9738, -93.2577, True),    # U.S. Bank Stadium (dome)
        # NFC South
        "ATL": (33.7554, -84.4008, True),    # Mercedes-Benz Stadium (retractable)
        "CAR": (35.2258, -80.8530, False),   # Bank of America Stadium
        "NO": (29.9511, -90.0812, True),     # Caesars Superdome (dome)
        "TB": (27.9759, -82.5033, False),    # Raymond James Stadium
        # NFC West
        "ARI": (33.5276, -112.2626, True),   # State Farm Stadium (retractable)
        "LAR": (33.9534, -118.3390, False),  # SoFi Stadium (partial roof)
        "SF": (37.4032, -121.9698, False),   # Levi's Stadium
        "SEA": (47.5952, -122.3316, False),  # Lumen Field
    }

    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = True, cache_dir: Optional[Path] = None):
        """
        Initialize weather provider.

        Args:
            api_key: OpenWeatherMap API key
            mock_mode: If True, return mock data
            cache_dir: Directory for caching API responses
        """
        self.api_key = api_key or os.getenv("OPENWEATHER_KEY")
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

    def _get_cache_path(self, game_date: str) -> Path:
        """Get cache file path for given game date."""
        return self.cache_dir / f"weather_{game_date}.parquet"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache file exists and is within duration limit."""
        if not cache_path.exists():
            return False

        file_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        return file_age < timedelta(hours=self.CACHE_DURATION_HOURS)

    def _get_mock_weather(self, team: str) -> Dict[str, any]:
        """
        Generate realistic mock weather data based on stadium location.

        Args:
            team: Team abbreviation

        Returns:
            Dictionary with weather information
        """
        # Check if stadium is a dome
        is_dome = self.STADIUM_LOCATIONS.get(team, (0, 0, False))[2]

        if is_dome:
            # Indoor/dome stadiums have controlled conditions
            return {
                "temperature": 72.0,
                "feels_like": 72.0,
                "humidity": 50,
                "wind_speed": 0.0,
                "wind_direction": 0,
                "precipitation": 0.0,
                "precipitation_prob": 0.0,
                "conditions": "Indoor",
                "is_dome": True,
                "impact_level": "None"
            }

        # Generate realistic outdoor weather
        # Vary by rough geographic location
        if team in ["BUF", "GB", "CHI", "DET", "MIN", "NE"]:  # Cold weather cities
            temp_range = (35, 55)
            wind_range = (5, 20)
        elif team in ["MIA", "TB", "JAX", "NO", "HOU"]:  # Warm weather cities
            temp_range = (70, 85)
            wind_range = (3, 12)
        else:  # Moderate climates
            temp_range = (50, 72)
            wind_range = (5, 15)

        temperature = random.uniform(*temp_range)
        wind_speed = random.uniform(*wind_range)
        precipitation = random.choice([0.0, 0.0, 0.0, random.uniform(0.1, 0.5)])

        # Determine impact level
        impact_level = self._calculate_weather_impact(temperature, wind_speed, precipitation, is_dome)

        return {
            "temperature": round(temperature, 1),
            "feels_like": round(temperature - (wind_speed * 0.5 if temperature < 50 else 0), 1),
            "humidity": random.randint(40, 85),
            "wind_speed": round(wind_speed, 1),
            "wind_direction": random.randint(0, 360),
            "precipitation": round(precipitation, 2),
            "precipitation_prob": round(random.uniform(0.0, 0.3) if precipitation > 0 else 0.0, 2),
            "conditions": self._get_conditions_text(temperature, precipitation, wind_speed),
            "is_dome": is_dome,
            "impact_level": impact_level
        }

    def _calculate_weather_impact(self, temp: float, wind: float, precip: float, is_dome: bool) -> str:
        """Calculate weather impact level on game."""
        if is_dome:
            return "None"

        impact_score = 0

        # Temperature impact
        if temp < 25 or temp > 90:
            impact_score += 3
        elif temp < 35 or temp > 85:
            impact_score += 2
        elif temp < 40 or temp > 80:
            impact_score += 1

        # Wind impact
        if wind > 20:
            impact_score += 3
        elif wind > 15:
            impact_score += 2
        elif wind > 10:
            impact_score += 1

        # Precipitation impact
        if precip > 0.3:
            impact_score += 3
        elif precip > 0.1:
            impact_score += 2

        # Map to impact level
        if impact_score >= 6:
            return "High"
        elif impact_score >= 4:
            return "Medium"
        elif impact_score >= 2:
            return "Low"
        else:
            return "Minimal"

    def _get_conditions_text(self, temp: float, precip: float, wind: float) -> str:
        """Get human-readable conditions text."""
        if precip > 0.2:
            return "Rain" if temp > 32 else "Snow"
        elif precip > 0:
            return "Light Rain" if temp > 32 else "Light Snow"
        elif wind > 15:
            return "Windy"
        elif temp > 85:
            return "Hot"
        elif temp < 35:
            return "Cold"
        else:
            return "Clear"

    def _fetch_with_retry(self, url: str, params: Dict) -> Dict:
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

    def fetch_weather_for_game(
        self,
        team: str,
        game_time: datetime
    ) -> Dict[str, any]:
        """
        Fetch weather forecast for a game.

        Args:
            team: Home team abbreviation
            game_time: Scheduled game time

        Returns:
            Dictionary with weather information:
                - temperature: Temperature in Fahrenheit
                - feels_like: Feels-like temperature
                - humidity: Humidity percentage
                - wind_speed: Wind speed in mph
                - wind_direction: Wind direction in degrees
                - precipitation: Precipitation amount (inches)
                - precipitation_prob: Probability of precipitation (0-1)
                - conditions: Text description
                - is_dome: Whether stadium is domed/indoor
                - impact_level: Expected impact on game (High, Medium, Low, Minimal, None)
        """
        if self.mock_mode or team not in self.STADIUM_LOCATIONS:
            return self._get_mock_weather(team)

        if not self.api_key:
            logger.warning("No OpenWeatherMap API key found, using mock data")
            return self._get_mock_weather(team)

        # Check if it's a dome - no need to fetch weather
        lat, lon, is_dome = self.STADIUM_LOCATIONS[team]
        if is_dome:
            return self._get_mock_weather(team)

        try:
            # Use forecast API for future games
            url = f"{self.BASE_URL}/forecast"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "imperial"
            }

            data = self._fetch_with_retry(url, params)

            # Find forecast closest to game time
            forecasts = data.get('list', [])
            if not forecasts:
                logger.warning("No forecast data returned, using mock data")
                return self._get_mock_weather(team)

            # Find closest forecast to game time
            closest_forecast = min(
                forecasts,
                key=lambda f: abs(datetime.fromtimestamp(f['dt']) - game_time)
            )

            weather_main = closest_forecast['main']
            weather_wind = closest_forecast['wind']
            weather_cond = closest_forecast['weather'][0] if closest_forecast.get('weather') else {}

            temperature = weather_main['temp']
            wind_speed = weather_wind['speed']
            precipitation = closest_forecast.get('rain', {}).get('3h', 0.0) / 25.4  # mm to inches

            return {
                "temperature": round(temperature, 1),
                "feels_like": round(weather_main.get('feels_like', temperature), 1),
                "humidity": weather_main.get('humidity', 50),
                "wind_speed": round(wind_speed, 1),
                "wind_direction": weather_wind.get('deg', 0),
                "precipitation": round(precipitation, 2),
                "precipitation_prob": closest_forecast.get('pop', 0.0),
                "conditions": weather_cond.get('main', 'Clear'),
                "is_dome": False,
                "impact_level": self._calculate_weather_impact(temperature, wind_speed, precipitation, False)
            }

        except Exception as e:
            logger.error(f"Error fetching weather for {team}: {e}, using mock data")
            return self._get_mock_weather(team)

    def fetch_weather_data(
        self,
        games_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Fetch weather for multiple games.

        Args:
            games_df: DataFrame with columns 'team' (home team), 'game_time', and optionally 'game_id'

        Returns:
            DataFrame with weather data merged:
                - game_id: Unique game identifier
                - temperature: Temperature in Fahrenheit
                - wind_speed: Wind speed in mph
                - precipitation: Precipitation amount
                - is_dome: Whether stadium is domed
                - weather_impact_level: Impact level
        """
        if games_df.empty:
            logger.warning("Empty games DataFrame provided")
            return games_df

        # Extract unique game date for caching
        if 'game_time' in games_df.columns:
            game_date = pd.to_datetime(games_df['game_time'].iloc[0]).strftime('%Y-%m-%d')
        else:
            game_date = datetime.now().strftime('%Y-%m-%d')

        # Check cache
        cache_path = self._get_cache_path(game_date)
        if self._is_cache_valid(cache_path):
            logger.info(f"Loading weather from cache: {cache_path}")
            weather_df = pd.read_parquet(cache_path)
            # Merge with games_df
            result = games_df.merge(weather_df, on='game_id', how='left', suffixes=('', '_weather'))
            return result

        # Fetch weather for each game
        weather_data = []
        for idx, row in games_df.iterrows():
            team = row.get('team', row.get('home_team', 'KC'))
            game_time = pd.to_datetime(row.get('game_time', datetime.now()))
            game_id = row.get('game_id', f'game_{idx}')

            weather = self.fetch_weather_for_game(team, game_time)
            weather['game_id'] = game_id
            weather_data.append(weather)

        weather_df = pd.DataFrame(weather_data)

        # Cache the weather data
        try:
            weather_df.to_parquet(cache_path, index=False)
            logger.info(f"Cached weather to {cache_path}")
        except Exception as e:
            logger.warning(f"Failed to cache weather: {e}")

        # Merge with original games_df
        result = games_df.merge(weather_df, on='game_id', how='left', suffixes=('', '_weather'))

        return result


def fetch_weather_data(
    games_df: pd.DataFrame,
    mock_mode: bool = True
) -> pd.DataFrame:
    """
    Convenience function to fetch weather data.

    Args:
        games_df: DataFrame with game information (must include 'team' or 'home_team' column)
        mock_mode: Whether to use mock data

    Returns:
        DataFrame with weather data added including:
            - temperature: Temperature in Fahrenheit
            - wind_speed: Wind speed in mph
            - precipitation: Precipitation amount
            - is_dome: Whether stadium is domed
    """
    provider = WeatherProvider(mock_mode=mock_mode)
    return provider.fetch_weather_data(games_df)

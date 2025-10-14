"""
Data ingestion module for fetching player props and contextual data.

ToS Compliance:
- All API clients respect rate limits
- User credentials stored securely
- No data scraping, only official API endpoints

This module provides a unified interface for fetching:
- Player props from Sleeper API
- Injury reports from ESPN/public sources
- Weather data from OpenWeatherMap
- Historical baseline statistics

All functions support mock mode for development and testing.
"""

from .sleeper_client import fetch_current_props, SleeperClient
from .odds_api_client import (
    fetch_current_props_from_odds_api,
    test_odds_api_connection,
    OddsAPIClient
)
from .injuries_provider import fetch_injury_report, InjuriesProvider
from .weather_provider import fetch_weather_data, WeatherProvider
from .baseline_stats import (
    load_baseline_stats,
    fetch_player_baselines,
    BaselineStatsLoader
)

__all__ = [
    # Sleeper API
    "fetch_current_props",
    "SleeperClient",
    # The Odds API (RECOMMENDED for betting props)
    "fetch_current_props_from_odds_api",
    "test_odds_api_connection",
    "OddsAPIClient",
    # Injuries
    "fetch_injury_report",
    "InjuriesProvider",
    # Weather
    "fetch_weather_data",
    "WeatherProvider",
    # Baseline Stats
    "load_baseline_stats",
    "fetch_player_baselines",
    "BaselineStatsLoader",
]

"""
Data Ingestion Layer for BetterBros Props

Provides API clients for fetching player data, statistics, injuries,
weather conditions, and baseline statistics with Redis caching.

Exports:
    - SleeperAPI: NFL player data and stats from Sleeper
    - InjuriesAPI: NFL injury reports from multiple sources
    - WeatherAPI: Weather conditions using OpenWeather
    - BaselineStats: Player and team statistical baselines
    - All custom exceptions
"""
from src.ingest.sleeper_client import SleeperAPI, SleeperAPIError
from src.ingest.injuries_provider import (
    InjuriesAPI,
    InjuriesAPIError,
    InjuryStatus,
)
from src.ingest.weather_provider import WeatherAPI, WeatherAPIError
from src.ingest.baseline_stats import BaselineStats, BaselineStatsError

__all__ = [
    # API Clients
    "SleeperAPI",
    "InjuriesAPI",
    "WeatherAPI",
    "BaselineStats",
    # Exceptions
    "SleeperAPIError",
    "InjuriesAPIError",
    "WeatherAPIError",
    "BaselineStatsError",
    # Enums
    "InjuryStatus",
]


async def health_check_all() -> dict:
    """
    Perform health check on all ingestion services

    Returns:
        Dictionary with health status of all services
    """
    from datetime import datetime

    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "services": {},
    }

    # Check Sleeper API
    async with SleeperAPI() as sleeper:
        results["services"]["sleeper"] = await sleeper.health_check()

    # Check Injuries API
    async with InjuriesAPI() as injuries:
        results["services"]["injuries"] = await injuries.health_check()

    # Check Weather API
    async with WeatherAPI() as weather:
        results["services"]["weather"] = await weather.health_check()

    # Check Baseline Stats
    async with BaselineStats() as baseline:
        results["services"]["baseline_stats"] = await baseline.health_check()

    # Overall status
    all_healthy = all(
        service.get("status") in ["healthy", "degraded"]
        for service in results["services"].values()
    )

    results["overall_status"] = "healthy" if all_healthy else "unhealthy"
    results["healthy_count"] = sum(
        1 for service in results["services"].values()
        if service.get("status") == "healthy"
    )
    results["total_count"] = len(results["services"])

    return results

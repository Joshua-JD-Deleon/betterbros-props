# Data Ingestion Layer

Comprehensive data ingestion layer for BetterBros Props with API clients for fetching player data, statistics, injuries, weather conditions, and baseline statistics with Redis caching.

## Overview

The ingestion layer provides:
- **SleeperAPI**: NFL player data and statistics from Sleeper Fantasy Football API
- **InjuriesAPI**: NFL injury reports aggregated from multiple sources (ESPN, SportsRadar)
- **WeatherAPI**: Game weather conditions using OpenWeather API
- **BaselineStats**: Player and team statistical baselines with rolling averages

All clients feature:
- Async/await support with httpx
- Redis caching with configurable TTL
- Exponential backoff retry logic
- Rate limiting to respect API limits
- Comprehensive error handling
- Health check endpoints
- Type hints and docstrings

## Installation

Required dependencies:
```bash
pip install httpx redis pydantic pydantic-settings
```

## Environment Variables

Add to your `.env` file:

```bash
# Required
REDIS_URL=redis://localhost:6379

# Optional (but recommended)
SLEEPER_API_KEY=your_sleeper_key        # Optional - Sleeper API is mostly public
SPORTSRADAR_API_KEY=your_sportsradar_key  # For injury data
OPENWEATHER_KEY=your_openweather_key     # For weather data
```

## Usage Examples

### Sleeper API - Player Data & Stats

```python
from src.ingest import SleeperAPI

async with SleeperAPI() as sleeper:
    # Fetch all NFL players (cached for 1 hour)
    players = await sleeper.get_nfl_players()

    # Get specific player
    mahomes = await sleeper.get_player_by_id("421")

    # Search for players
    qbs = await sleeper.search_players("mahomes", position="QB")

    # Get player stats for a week
    stats = await sleeper.get_player_stats(
        player_id="421",
        season="2024",
        week=5
    )
    # Returns: {"player_id": "421", "stats": {"pass_yd": 360, "pass_td": 3, ...}}

    # Get projections
    projections = await sleeper.get_projections(
        season="2024",
        week=6
    )
    # Returns: {"421": {"pts_ppr": 24.5, "pass_yd": 285, ...}}

    # Health check
    health = await sleeper.health_check()
```

### Injuries API - Injury Reports

```python
from src.ingest import InjuriesAPI, InjuryStatus

async with InjuriesAPI() as injuries:
    # Get injury report for current week
    report = await injuries.get_injury_report(week=5)
    # Returns:
    # {
    #     "week": 5,
    #     "season": "2024",
    #     "injuries": [
    #         {
    #             "player_name": "Patrick Mahomes",
    #             "team": "KC",
    #             "status": "questionable",
    #             "injury_type": "ankle",
    #             "description": "High ankle sprain",
    #             "source": "espn"
    #         }
    #     ],
    #     "total_injuries": 45,
    #     "last_updated": "2024-10-14T10:30:00Z"
    # }

    # Get team injuries
    kc_injuries = await injuries.get_team_injuries(
        team="KC",
        week=5
    )

    # Get specific player injury
    player_injury = await injuries.get_player_injury(
        player_name="Patrick Mahomes",
        week=5
    )
```

### Weather API - Game Weather Conditions

```python
from src.ingest import WeatherAPI
from datetime import datetime

async with WeatherAPI() as weather:
    game_time = datetime(2024, 10, 20, 13, 0)

    # Get weather for outdoor game
    conditions = await weather.get_game_weather(
        venue="Arrowhead Stadium",
        game_time=game_time
    )
    # Returns:
    # {
    #     "venue": "Arrowhead Stadium",
    #     "is_indoor": false,
    #     "temperature": 65.5,
    #     "wind_speed": 12.3,
    #     "precipitation": 20.0,
    #     "humidity": 55,
    #     "conditions": "Partly Cloudy"
    # }

    # Indoor venues automatically return N/A
    indoor = await weather.get_game_weather(
        venue="AT&T Stadium",  # Dallas Cowboys
        game_time=game_time
    )
    # Returns: {"is_indoor": true, "conditions": "Indoor", ...}

    # Get weather impact score
    impact = await weather.get_weather_impact_score(
        venue="Lambeau Field",
        game_time=game_time
    )
    # Returns:
    # {
    #     "impact_score": 75,  # 0-100
    #     "factors": {
    #         "wind": 30,
    #         "precipitation": 25,
    #         "temperature": 20
    #     },
    #     "recommendation": "Severe weather impact expected"
    # }

    # Get forecast for a date
    forecast = await weather.get_forecast(
        venue="Lambeau Field",
        date=datetime(2024, 10, 20)
    )
```

### Baseline Stats - Player & Team Statistics

```python
from src.ingest import BaselineStats

async with BaselineStats() as baseline:
    # Get player baseline statistics
    stats = await baseline.get_player_baseline(
        player_id="421",
        stat_type="passing_yards",
        season="2024",
        current_week=6
    )
    # Returns:
    # {
    #     "player_id": "421",
    #     "stat_type": "passing_yards",
    #     "season_avg": 285.5,
    #     "avg_last_3": 310.2,
    #     "avg_last_5": 295.8,
    #     "median": 280.0,
    #     "std_dev": 45.3,
    #     "trend": "up",
    #     "games_played": 5
    # }

    # Get team statistics
    team_stats = await baseline.get_team_stats(
        team="KC",
        stat_category="offense",
        season="2024",
        current_week=6
    )
    # Returns:
    # {
    #     "team": "KC",
    #     "yards_per_game": 385.2,
    #     "pass_yards_per_game": 285.5,
    #     "rush_yards_per_game": 99.7,
    #     "total_tds_per_game": 2.8,
    #     "estimated_points_per_game": 28.5
    # }

    # Get rolling averages
    rolling = await baseline.get_rolling_averages(
        player_id="421",
        stat_type="passing_yards",
        season="2024",
        current_week=6,
        windows=[3, 5, 10]
    )
    # Returns: {"last_3": 310.2, "last_5": 295.8, "last_10": null}
```

## Caching Strategy

All clients use Redis for caching with appropriate TTLs:

| Data Type | TTL | Cache Key Pattern |
|-----------|-----|-------------------|
| NFL Players | 1 hour | `sleeper:nfl:players:all` |
| Player Stats | 30 min | `sleeper:stats:{player_id}:{season}:week_{week}` |
| Projections | 30 min | `sleeper:projections:{season}:week_{week}` |
| Injury Reports | 6 hours | `injuries:nfl:{season}:week_{week}` |
| Weather | 3 hours | `weather:{venue}:{date}` |
| Baseline Stats | 24 hours | `baseline:player:{player_id}:{stat}:{season}:week_{week}` |

To bypass cache:
```python
data = await sleeper.get_nfl_players(use_cache=False)
```

## Error Handling

All clients raise custom exceptions:

```python
from src.ingest import (
    SleeperAPIError,
    InjuriesAPIError,
    WeatherAPIError,
    BaselineStatsError
)

try:
    stats = await sleeper.get_player_stats("421", "2024", week=5)
except SleeperAPIError as e:
    logger.error(f"Failed to fetch stats: {e}")
    # Handle error appropriately
```

## Rate Limiting

Clients implement rate limiting to respect API limits:

- **SleeperAPI**: 0.1s delay between requests (configurable)
- **InjuriesAPI**: Exponential backoff on 429 responses
- **WeatherAPI**: Exponential backoff on rate limits

Configure rate limits:
```python
sleeper = SleeperAPI(rate_limit_delay=0.2)  # 200ms between requests
```

## Health Checks

All clients provide health check methods:

```python
from src.ingest import health_check_all

# Check all services
health = await health_check_all()
# Returns:
# {
#     "overall_status": "healthy",
#     "healthy_count": 4,
#     "total_count": 4,
#     "services": {
#         "sleeper": {"status": "healthy", ...},
#         "injuries": {"status": "healthy", ...},
#         "weather": {"status": "healthy", ...},
#         "baseline_stats": {"status": "healthy", ...}
#     }
# }

# Individual health checks
sleeper_health = await sleeper.health_check()
```

## Supported Stat Types

### Player Stats (Sleeper)
- **Passing**: `passing_yards`, `pass_tds`, `interceptions`
- **Rushing**: `rushing_yards`, `rush_tds`, `carries`
- **Receiving**: `receptions`, `receiving_yards`, `rec_tds`, `targets`
- **Fantasy**: `fantasy_points`, `ppr_points`

### Injury Statuses
- `OUT` - Player will not play
- `DOUBTFUL` - Unlikely to play
- `QUESTIONABLE` - Game-time decision
- `PROBABLE` - Likely to play
- `HEALTHY` - No injury concerns
- `IR` - Injured Reserve
- `PUP` - Physically Unable to Perform

## Indoor Venues

The following NFL venues are automatically marked as indoor (no weather data):
- AT&T Stadium (Dallas)
- Mercedes-Benz Stadium (Atlanta)
- State Farm Stadium (Arizona)
- U.S. Bank Stadium (Minnesota)
- Allegiant Stadium (Las Vegas)
- SoFi Stadium (LA)
- Ford Field (Detroit)
- Caesars Superdome (New Orleans)
- Lucas Oil Stadium (Indianapolis)

## Architecture

```
src/ingest/
├── __init__.py              # Package exports and health_check_all()
├── sleeper_client.py        # Sleeper API client
├── injuries_provider.py     # Injuries aggregation
├── weather_provider.py      # OpenWeather client
├── baseline_stats.py        # Statistical baselines
└── README.md               # This file
```

## Best Practices

1. **Use context managers** for automatic resource cleanup:
   ```python
   async with SleeperAPI() as sleeper:
       # Your code here
   ```

2. **Enable caching** in production to reduce API calls:
   ```python
   stats = await sleeper.get_player_stats(..., use_cache=True)
   ```

3. **Handle exceptions** gracefully:
   ```python
   try:
       data = await client.fetch_data()
   except APIError as e:
       logger.error(f"API error: {e}")
       # Use fallback or cached data
   ```

4. **Monitor health checks** to ensure services are operational:
   ```python
   health = await health_check_all()
   if health["overall_status"] != "healthy":
       alert_team(health)
   ```

5. **Reuse clients** when making multiple calls:
   ```python
   async with SleeperAPI() as sleeper:
       for player_id in player_ids:
           stats = await sleeper.get_player_stats(player_id, "2024", week=5)
   ```

## Testing

Run health checks to verify setup:

```python
import asyncio
from src.ingest import health_check_all

async def test():
    health = await health_check_all()
    print(health)

asyncio.run(test())
```

## Performance

- **Parallel requests**: Use `asyncio.gather()` for concurrent API calls
- **Connection pooling**: httpx clients maintain connection pools (20 keepalive, 50 max)
- **Caching**: Redis caching reduces API calls by 90%+ in production
- **Retry logic**: Exponential backoff prevents thundering herd

Example parallel fetching:
```python
async with SleeperAPI() as sleeper:
    tasks = [
        sleeper.get_player_stats(pid, "2024", week=5)
        for pid in player_ids
    ]
    results = await asyncio.gather(*tasks)
```

## Contributing

When adding new data sources:

1. Create a new client class following the existing pattern
2. Implement caching with appropriate TTL
3. Add retry logic with exponential backoff
4. Include health_check() method
5. Add comprehensive docstrings
6. Export from `__init__.py`
7. Update this README

## License

Part of BetterBros Props - Internal Use Only

"""
Example usage of the BetterBros Props data ingestion layer

This script demonstrates how to use all the ingestion clients to fetch
player data, stats, injuries, weather, and baseline statistics.
"""
import asyncio
import logging
from datetime import datetime, timedelta

from src.ingest import (
    SleeperAPI,
    InjuriesAPI,
    WeatherAPI,
    BaselineStats,
    health_check_all,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_sleeper_api():
    """Demonstrate Sleeper API usage"""
    logger.info("=== Sleeper API Demo ===")

    async with SleeperAPI() as sleeper:
        # Search for a player
        logger.info("Searching for Patrick Mahomes...")
        players = await sleeper.search_players("mahomes", position="QB", limit=3)

        for player in players:
            logger.info(f"Found: {player.get('first_name')} {player.get('last_name')} - {player.get('team')}")

        if players:
            player_id = players[0].get("player_id")

            # Get player stats for current season
            logger.info(f"\nFetching stats for player {player_id}...")
            stats = await sleeper.get_player_stats(
                player_id=player_id,
                season="2024",
                week=5,
            )

            logger.info(f"Week 5 Stats: {stats.get('stats')}")

            # Get projections
            logger.info("\nFetching projections for week 6...")
            projections = await sleeper.get_projections(
                season="2024",
                week=6,
            )

            if player_id in projections:
                logger.info(f"Week 6 Projections: {projections[player_id]}")


async def demo_injuries_api():
    """Demonstrate Injuries API usage"""
    logger.info("\n=== Injuries API Demo ===")

    async with InjuriesAPI() as injuries:
        # Get current week injury report
        logger.info("Fetching injury report for week 5...")
        report = await injuries.get_injury_report(week=5)

        logger.info(f"Total injuries: {report.get('total_injuries')}")
        logger.info(f"Last updated: {report.get('last_updated')}")

        # Show first 5 injuries
        for injury in report.get('injuries', [])[:5]:
            logger.info(
                f"  - {injury['player_name']} ({injury['team']}): "
                f"{injury['status']} - {injury.get('injury_type', 'N/A')}"
            )

        # Get specific team injuries
        logger.info("\nFetching Kansas City Chiefs injuries...")
        kc_injuries = await injuries.get_team_injuries(
            team="KC",
            week=5
        )

        if kc_injuries:
            logger.info(f"Chiefs injuries: {len(kc_injuries)}")
            for injury in kc_injuries:
                logger.info(f"  - {injury['player_name']}: {injury['status']}")
        else:
            logger.info("No injuries reported for KC")


async def demo_weather_api():
    """Demonstrate Weather API usage"""
    logger.info("\n=== Weather API Demo ===")

    async with WeatherAPI() as weather:
        # Get weather for an outdoor game
        game_time = datetime.utcnow() + timedelta(days=7)  # Next week

        logger.info(f"Fetching weather for Arrowhead Stadium on {game_time.date()}...")
        conditions = await weather.get_game_weather(
            venue="Arrowhead Stadium",
            game_time=game_time,
        )

        if not conditions.get("is_indoor"):
            logger.info(
                f"Temperature: {conditions.get('temperature')}°F, "
                f"Wind: {conditions.get('wind_speed')} mph, "
                f"Conditions: {conditions.get('conditions')}"
            )

        # Check indoor venue
        logger.info("\nFetching weather for AT&T Stadium (Dallas - indoor)...")
        indoor = await weather.get_game_weather(
            venue="AT&T Stadium",
            game_time=game_time,
        )

        logger.info(f"Indoor venue: {indoor.get('is_indoor')}")
        logger.info(f"Conditions: {indoor.get('conditions')}")

        # Get weather impact score
        logger.info("\nCalculating weather impact for Lambeau Field...")
        impact = await weather.get_weather_impact_score(
            venue="Lambeau Field",
            game_time=game_time,
        )

        logger.info(
            f"Impact Score: {impact.get('impact_score')}/100 - "
            f"{impact.get('recommendation')}"
        )
        logger.info(f"Factors: {impact.get('factors')}")


async def demo_baseline_stats():
    """Demonstrate Baseline Stats usage"""
    logger.info("\n=== Baseline Stats Demo ===")

    async with BaselineStats() as baseline:
        # Get player baseline
        logger.info("Fetching baseline stats for player...")

        # First get a player ID from Sleeper
        async with SleeperAPI() as sleeper:
            players = await sleeper.search_players("kelce", position="TE", limit=1)
            if not players:
                logger.warning("No players found")
                return

            player_id = players[0].get("player_id")
            player_name = f"{players[0].get('first_name')} {players[0].get('last_name')}"

            logger.info(f"Analyzing {player_name} (ID: {player_id})...")

        # Get baseline for receiving yards
        stats = await baseline.get_player_baseline(
            player_id=player_id,
            stat_type="receiving_yards",
            season="2024",
            current_week=6,
        )

        if stats.get("season_avg"):
            logger.info(f"Season Average: {stats.get('season_avg')} yards")
            logger.info(f"Last 3 Games: {stats.get('avg_last_3')} yards")
            logger.info(f"Last 5 Games: {stats.get('avg_last_5')} yards")
            logger.info(f"Trend: {stats.get('trend')}")
            logger.info(f"Standard Deviation: {stats.get('std_dev')}")
        else:
            logger.info("No baseline data available yet")

        # Get team stats
        logger.info("\nFetching Kansas City Chiefs team stats...")
        team_stats = await baseline.get_team_stats(
            team="KC",
            stat_category="offense",
            season="2024",
            current_week=6,
        )

        if team_stats.get("games_played"):
            logger.info(f"Games Played: {team_stats.get('games_played')}")
            logger.info(f"Yards/Game: {team_stats.get('yards_per_game')}")
            logger.info(f"Pass Yards/Game: {team_stats.get('pass_yards_per_game')}")
            logger.info(f"Rush Yards/Game: {team_stats.get('rush_yards_per_game')}")
            logger.info(f"Est. Points/Game: {team_stats.get('estimated_points_per_game')}")


async def demo_health_checks():
    """Demonstrate health check functionality"""
    logger.info("\n=== Health Checks ===")

    # Check all services
    health = await health_check_all()

    logger.info(f"Overall Status: {health.get('overall_status')}")
    logger.info(f"Healthy Services: {health.get('healthy_count')}/{health.get('total_count')}")

    # Show individual service status
    for service_name, service_health in health.get('services', {}).items():
        status = service_health.get('status')
        logger.info(f"  - {service_name}: {status}")

        if status != "healthy":
            logger.warning(f"    Error: {service_health.get('error', 'Unknown')}")


async def demo_parallel_fetching():
    """Demonstrate parallel API calls for performance"""
    logger.info("\n=== Parallel Fetching Demo ===")

    async with SleeperAPI() as sleeper:
        # Search for multiple players
        player_names = ["mahomes", "kelce", "hill"]

        logger.info(f"Searching for {len(player_names)} players in parallel...")

        # Create tasks for parallel execution
        tasks = [
            sleeper.search_players(name, limit=1)
            for name in player_names
        ]

        # Execute all searches concurrently
        results = await asyncio.gather(*tasks)

        logger.info(f"Found {sum(len(r) for r in results)} players")

        # Now fetch stats for all players in parallel
        player_ids = [r[0].get("player_id") for r in results if r]

        logger.info(f"Fetching stats for {len(player_ids)} players in parallel...")

        stats_tasks = [
            sleeper.get_player_stats(pid, "2024", week=5)
            for pid in player_ids
        ]

        all_stats = await asyncio.gather(*stats_tasks, return_exceptions=True)

        for i, stats in enumerate(all_stats):
            if isinstance(stats, Exception):
                logger.warning(f"Failed to fetch stats for player {i}: {stats}")
            else:
                logger.info(f"Player {i}: {len(stats.get('stats', {}))} stats fetched")


async def main():
    """Run all demos"""
    logger.info("Starting BetterBros Props Ingestion Layer Demo\n")

    try:
        # Run health checks first
        await demo_health_checks()

        # Run individual demos
        await demo_sleeper_api()
        await demo_injuries_api()
        await demo_weather_api()
        await demo_baseline_stats()

        # Demonstrate parallel fetching
        await demo_parallel_fetching()

        logger.info("\n=== Demo Complete ===")

    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())

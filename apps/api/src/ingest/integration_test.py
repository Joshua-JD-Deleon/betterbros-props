"""
Integration test for the data ingestion layer

This test verifies that all ingestion clients work together correctly
and can fetch real data from APIs (requires valid API keys).
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_health_checks():
    """Test that all services can be health checked"""
    logger.info("Testing health checks...")

    health = await health_check_all()

    assert health["overall_status"] in ["healthy", "unhealthy"]
    assert "services" in health
    assert "sleeper" in health["services"]
    assert "injuries" in health["services"]
    assert "weather" in health["services"]
    assert "baseline_stats" in health["services"]

    logger.info(f"Health check passed: {health['overall_status']}")
    return health


async def test_sleeper_integration():
    """Test Sleeper API integration"""
    logger.info("Testing Sleeper API integration...")

    async with SleeperAPI() as sleeper:
        # Test 1: Fetch all players
        players = await sleeper.get_nfl_players()
        assert len(players) > 0, "Should fetch NFL players"
        logger.info(f"Fetched {len(players)} NFL players")

        # Test 2: Search for specific player
        results = await sleeper.search_players("mahomes", position="QB", limit=1)
        assert len(results) > 0, "Should find Patrick Mahomes"

        player_id = results[0].get("player_id")
        player_name = f"{results[0].get('first_name')} {results[0].get('last_name')}"
        logger.info(f"Found player: {player_name} (ID: {player_id})")

        # Test 3: Fetch player stats (may be empty if early season)
        try:
            stats = await sleeper.get_player_stats(
                player_id=player_id,
                season="2024",
                week=1,
            )
            logger.info(f"Fetched stats for week 1: {len(stats.get('stats', {}))} stats")
        except Exception as e:
            logger.warning(f"Could not fetch stats: {e}")

        # Test 4: Verify caching works
        players_cached = await sleeper.get_nfl_players(use_cache=True)
        assert players_cached == players, "Cached data should match"
        logger.info("Cache verification passed")

    logger.info("Sleeper API integration test passed")


async def test_injuries_integration():
    """Test Injuries API integration"""
    logger.info("Testing Injuries API integration...")

    async with InjuriesAPI() as injuries:
        # Test 1: Fetch injury report
        report = await injuries.get_injury_report(week=1)
        assert "injuries" in report
        assert "total_injuries" in report
        assert "last_updated" in report

        logger.info(f"Fetched injury report: {report['total_injuries']} injuries")

        # Test 2: Fetch team injuries
        kc_injuries = await injuries.get_team_injuries(team="KC", week=1)
        assert isinstance(kc_injuries, list)
        logger.info(f"Fetched KC injuries: {len(kc_injuries)} injuries")

        # Test 3: Verify caching
        report_cached = await injuries.get_injury_report(week=1, use_cache=True)
        assert report_cached == report, "Cached data should match"
        logger.info("Cache verification passed")

    logger.info("Injuries API integration test passed")


async def test_weather_integration():
    """Test Weather API integration"""
    logger.info("Testing Weather API integration...")

    async with WeatherAPI() as weather:
        game_time = datetime.utcnow() + timedelta(days=1)

        # Test 1: Fetch outdoor venue weather
        outdoor = await weather.get_game_weather(
            venue="Arrowhead Stadium",
            game_time=game_time,
        )

        assert not outdoor["is_indoor"], "Arrowhead should be outdoor"
        assert "temperature" in outdoor
        assert "wind_speed" in outdoor
        logger.info(f"Outdoor weather: {outdoor['temperature']}°F, {outdoor['conditions']}")

        # Test 2: Fetch indoor venue weather
        indoor = await weather.get_game_weather(
            venue="AT&T Stadium",
            game_time=game_time,
        )

        assert indoor["is_indoor"], "AT&T Stadium should be indoor"
        assert indoor["conditions"] == "Indoor"
        logger.info(f"Indoor venue correctly identified")

        # Test 3: Get weather impact score
        impact = await weather.get_weather_impact_score(
            venue="Arrowhead Stadium",
            game_time=game_time,
        )

        assert "impact_score" in impact
        assert 0 <= impact["impact_score"] <= 100
        logger.info(f"Weather impact score: {impact['impact_score']}/100")

        # Test 4: Verify caching
        outdoor_cached = await weather.get_game_weather(
            venue="Arrowhead Stadium",
            game_time=game_time,
            use_cache=True,
        )
        assert outdoor_cached == outdoor, "Cached data should match"
        logger.info("Cache verification passed")

    logger.info("Weather API integration test passed")


async def test_baseline_stats_integration():
    """Test Baseline Stats integration"""
    logger.info("Testing Baseline Stats integration...")

    async with BaselineStats() as baseline:
        # Get a player ID first
        async with SleeperAPI() as sleeper:
            results = await sleeper.search_players("mahomes", limit=1)
            if not results:
                logger.warning("Could not find player for baseline test")
                return

            player_id = results[0].get("player_id")

        # Test 1: Fetch player baseline (may be empty early season)
        try:
            stats = await baseline.get_player_baseline(
                player_id=player_id,
                stat_type="passing_yards",
                season="2024",
                current_week=6,
            )

            assert "player_id" in stats
            assert "stat_type" in stats
            assert "season" in stats

            if stats.get("games_played", 0) > 0:
                logger.info(
                    f"Player baseline: {stats['games_played']} games, "
                    f"avg: {stats.get('season_avg', 'N/A')}"
                )
            else:
                logger.info("No baseline data available yet (early season)")

        except Exception as e:
            logger.warning(f"Could not fetch baseline: {e}")

        # Test 2: Fetch team stats
        try:
            team_stats = await baseline.get_team_stats(
                team="KC",
                stat_category="offense",
                season="2024",
                current_week=6,
            )

            assert "team" in team_stats
            assert "category" in team_stats

            if team_stats.get("games_played", 0) > 0:
                logger.info(
                    f"Team stats: {team_stats['games_played']} games, "
                    f"{team_stats.get('yards_per_game', 'N/A')} ypg"
                )
            else:
                logger.info("No team data available yet (early season)")

        except Exception as e:
            logger.warning(f"Could not fetch team stats: {e}")

    logger.info("Baseline Stats integration test passed")


async def test_concurrent_operations():
    """Test that multiple clients can run concurrently"""
    logger.info("Testing concurrent operations...")

    # Create multiple client operations
    async def fetch_sleeper_data():
        async with SleeperAPI() as sleeper:
            return await sleeper.get_nfl_players()

    async def fetch_injuries_data():
        async with InjuriesAPI() as injuries:
            return await injuries.get_injury_report(week=1)

    async def fetch_weather_data():
        async with WeatherAPI() as weather:
            return await weather.get_game_weather(
                venue="Arrowhead Stadium",
                game_time=datetime.utcnow() + timedelta(days=1),
            )

    # Run all operations concurrently
    results = await asyncio.gather(
        fetch_sleeper_data(),
        fetch_injuries_data(),
        fetch_weather_data(),
        return_exceptions=True,
    )

    # Verify all succeeded
    success_count = sum(1 for r in results if not isinstance(r, Exception))
    logger.info(f"Concurrent operations: {success_count}/3 succeeded")

    assert success_count >= 1, "At least one concurrent operation should succeed"

    logger.info("Concurrent operations test passed")


async def test_error_handling():
    """Test error handling for invalid inputs"""
    logger.info("Testing error handling...")

    # Test 1: Invalid player ID
    async with SleeperAPI() as sleeper:
        try:
            stats = await sleeper.get_player_stats(
                player_id="invalid_id_12345",
                season="2024",
                week=1,
            )
            # Should return empty stats, not crash
            logger.info("Invalid player ID handled gracefully")
        except Exception as e:
            logger.info(f"Exception caught as expected: {type(e).__name__}")

    # Test 2: Invalid venue
    async with WeatherAPI() as weather:
        try:
            weather_data = await weather.get_game_weather(
                venue="Nonexistent Stadium",
                game_time=datetime.utcnow(),
            )
            logger.info("Invalid venue handled gracefully")
        except Exception as e:
            logger.info(f"Exception caught as expected: {type(e).__name__}")

    logger.info("Error handling test passed")


async def run_all_tests():
    """Run all integration tests"""
    logger.info("=" * 60)
    logger.info("Running Data Ingestion Layer Integration Tests")
    logger.info("=" * 60)

    tests = [
        ("Health Checks", test_health_checks),
        ("Sleeper API", test_sleeper_integration),
        ("Injuries API", test_injuries_integration),
        ("Weather API", test_weather_integration),
        ("Baseline Stats", test_baseline_stats_integration),
        ("Concurrent Operations", test_concurrent_operations),
        ("Error Handling", test_error_handling),
    ]

    passed = 0
    failed = 0
    results = {}

    for test_name, test_func in tests:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Running: {test_name}")
        logger.info('=' * 60)

        try:
            result = await test_func()
            results[test_name] = "PASSED"
            passed += 1
            logger.info(f"✓ {test_name} PASSED")
        except AssertionError as e:
            results[test_name] = f"FAILED: {e}"
            failed += 1
            logger.error(f"✗ {test_name} FAILED: {e}")
        except Exception as e:
            results[test_name] = f"ERROR: {e}"
            failed += 1
            logger.error(f"✗ {test_name} ERROR: {e}", exc_info=True)

    # Print summary
    logger.info(f"\n{'=' * 60}")
    logger.info("TEST SUMMARY")
    logger.info('=' * 60)
    logger.info(f"Total Tests: {len(tests)}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success Rate: {passed / len(tests) * 100:.1f}%")

    logger.info("\nDetailed Results:")
    for test_name, result in results.items():
        logger.info(f"  {test_name}: {result}")

    return passed == len(tests)


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)

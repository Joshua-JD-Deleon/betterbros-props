"""
Tests for data ingestion modules.
"""

import pytest
import pandas as pd
from datetime import datetime
from src.ingest import (
    fetch_current_props,
    fetch_injury_report,
    fetch_weather_data,
    load_baseline_stats
)


class TestSleeperClient:
    """Tests for Sleeper API client."""

    def test_fetch_current_props_returns_dataframe(self):
        """Test fetching current props returns DataFrame."""
        props_df = fetch_current_props(week=1, season=2025, mock_mode=True)

        assert isinstance(props_df, pd.DataFrame)
        assert len(props_df) > 0

    def test_fetch_current_props_has_required_columns(self):
        """Test props DataFrame has all required columns."""
        props_df = fetch_current_props(week=1, season=2025, mock_mode=True)

        required_columns = [
            'player_id', 'player_name', 'team', 'position', 'opponent',
            'prop_type', 'line', 'over_odds', 'under_odds',
            'game_id', 'game_time', 'home_away'
        ]

        for col in required_columns:
            assert col in props_df.columns, f"Missing column: {col}"

    def test_fetch_current_props_has_minimum_rows(self):
        """Test that we get at least 20 props in mock mode."""
        props_df = fetch_current_props(week=1, season=2025, mock_mode=True)

        assert len(props_df) >= 20, "Should have at least 20 props"

    def test_fetch_current_props_prop_types(self):
        """Test various prop types are present."""
        props_df = fetch_current_props(week=1, season=2025, mock_mode=True)

        expected_prop_types = ['passing_yards', 'receiving_yards', 'rushing_yards', 'receptions']
        prop_types_present = props_df['prop_type'].unique()

        for prop_type in expected_prop_types:
            assert prop_type in prop_types_present, f"Missing prop type: {prop_type}"

    def test_fetch_current_props_odds_format(self):
        """Test that odds are in American format (negative or positive integers)."""
        props_df = fetch_current_props(week=1, season=2025, mock_mode=True)

        # Check over_odds
        assert all(isinstance(x, (int, float)) for x in props_df['over_odds'])
        # Check under_odds
        assert all(isinstance(x, (int, float)) for x in props_df['under_odds'])

    def test_fetch_current_props_no_missing_critical_fields(self):
        """Test that critical fields have no missing values."""
        props_df = fetch_current_props(week=1, season=2025, mock_mode=True)

        critical_fields = ['player_name', 'team', 'prop_type', 'line', 'over_odds', 'under_odds']

        for field in critical_fields:
            assert not props_df[field].isna().any(), f"Field {field} has missing values"


class TestInjuriesProvider:
    """Tests for injuries provider."""

    def test_fetch_injury_report_returns_dataframe(self):
        """Test fetching injury report returns DataFrame."""
        injuries_df = fetch_injury_report(week=1, season=2025, mock_mode=True)

        assert isinstance(injuries_df, pd.DataFrame)

    def test_fetch_injury_report_has_required_columns(self):
        """Test injuries DataFrame has all required columns."""
        injuries_df = fetch_injury_report(week=1, season=2025, mock_mode=True)

        required_columns = ['player_id', 'player_name', 'team', 'status', 'injury_type']

        for col in required_columns:
            assert col in injuries_df.columns, f"Missing column: {col}"

    def test_fetch_injury_report_status_values(self):
        """Test that injury status values are valid."""
        injuries_df = fetch_injury_report(week=1, season=2025, mock_mode=True)

        if not injuries_df.empty:
            valid_statuses = ['Out', 'Doubtful', 'Questionable', 'Probable']
            statuses = injuries_df['status'].unique()

            for status in statuses:
                assert status in valid_statuses, f"Invalid status: {status}"

    def test_fetch_injury_report_has_injuries(self):
        """Test that mock data returns 5-10 injuries."""
        injuries_df = fetch_injury_report(week=1, season=2025, mock_mode=True)

        assert len(injuries_df) >= 5, "Should have at least 5 injuries"
        assert len(injuries_df) <= 10, "Should have at most 10 injuries"

    def test_fetch_injury_report_team_filter(self):
        """Test filtering injuries by team."""
        injuries_df = fetch_injury_report(week=1, season=2025, teams=['KC'], mock_mode=True)

        if not injuries_df.empty:
            assert all(injuries_df['team'] == 'KC'), "Should only return injuries for KC"


class TestWeatherProvider:
    """Tests for weather provider."""

    def test_fetch_weather_data_returns_dataframe(self):
        """Test fetching weather data returns DataFrame."""
        # Create mock games dataframe
        games_df = pd.DataFrame({
            'game_id': ['game_001', 'game_002'],
            'team': ['KC', 'BUF'],
            'game_time': [pd.Timestamp('2025-10-11 13:00:00')] * 2
        })

        result_df = fetch_weather_data(games_df, mock_mode=True)

        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == len(games_df)

    def test_fetch_weather_data_has_weather_columns(self):
        """Test that weather columns are added."""
        games_df = pd.DataFrame({
            'game_id': ['game_001'],
            'team': ['KC'],
            'game_time': [pd.Timestamp('2025-10-11 13:00:00')]
        })

        result_df = fetch_weather_data(games_df, mock_mode=True)

        weather_columns = ['temperature', 'wind_speed', 'precipitation', 'is_dome']

        for col in weather_columns:
            assert col in result_df.columns, f"Missing weather column: {col}"

    def test_fetch_weather_data_dome_detection(self):
        """Test that dome stadiums are properly detected."""
        # Test the provider directly
        from src.ingest import WeatherProvider

        provider = WeatherProvider(mock_mode=True)
        weather = provider._get_mock_weather('LV')

        assert weather['is_dome'] == True, "LV should be marked as dome"
        assert weather['temperature'] == 72.0, "Dome should have controlled temp"

    def test_fetch_weather_data_outdoor_stadium(self):
        """Test outdoor stadium has varying weather."""
        from src.ingest import WeatherProvider

        provider = WeatherProvider(mock_mode=True)
        weather = provider._get_mock_weather('KC')

        assert weather['is_dome'] == False, "KC should not be marked as dome"
        # Outdoor stadiums have variable conditions
        assert 'temperature' in weather
        assert 'wind_speed' in weather


class TestBaselineStats:
    """Tests for baseline statistics loader."""

    def test_load_baseline_stats_returns_dataframe(self):
        """Test loading baseline stats returns DataFrame."""
        stats_df = load_baseline_stats(mock_mode=True)

        assert isinstance(stats_df, pd.DataFrame)
        assert len(stats_df) > 0

    def test_load_baseline_stats_has_required_columns(self):
        """Test stats DataFrame has all required columns."""
        stats_df = load_baseline_stats(mock_mode=True)

        required_columns = ['player_id', 'player_name', 'season', 'position', 'team']

        for col in required_columns:
            assert col in stats_df.columns, f"Missing column: {col}"

    def test_load_baseline_stats_has_multiple_players(self):
        """Test that we have stats for multiple players."""
        stats_df = load_baseline_stats(mock_mode=True)

        assert len(stats_df) >= 10, "Should have stats for at least 10 players"

    def test_load_baseline_stats_position_specific_stats(self):
        """Test that position-specific stats are present."""
        stats_df = load_baseline_stats(mock_mode=True)

        # QBs should have passing_yards
        qb_stats = stats_df[stats_df['position'] == 'QB']
        if not qb_stats.empty:
            assert 'avg_passing_yards' in qb_stats.columns
            assert qb_stats['avg_passing_yards'].notna().any()

        # WRs should have receiving_yards
        wr_stats = stats_df[stats_df['position'] == 'WR']
        if not wr_stats.empty:
            assert 'avg_receiving_yards' in wr_stats.columns
            assert wr_stats['avg_receiving_yards'].notna().any()

    def test_load_baseline_stats_player_filter(self):
        """Test filtering stats by player IDs."""
        stats_df = load_baseline_stats(player_ids=['player_001'], mock_mode=True)

        assert len(stats_df) > 0
        assert all(stats_df['player_id'] == 'player_001')


class TestCaching:
    """Tests for caching functionality."""

    def test_props_caching(self, tmp_path):
        """Test that props are cached properly."""
        from src.ingest import SleeperClient

        # Use temporary cache directory
        client = SleeperClient(mock_mode=True, cache_dir=tmp_path)

        # First fetch - should create cache
        df1 = client.fetch_props(week=1, season=2025)

        # Check cache file exists
        cache_file = tmp_path / "sleeper_1_2025.parquet"
        assert cache_file.exists(), "Cache file should be created"

        # Second fetch - should use cache
        df2 = client.fetch_props(week=1, season=2025)

        # Results should be identical
        pd.testing.assert_frame_equal(df1, df2)

    def test_injuries_caching(self, tmp_path):
        """Test that injuries are cached properly."""
        from src.ingest import InjuriesProvider

        provider = InjuriesProvider(mock_mode=True, cache_dir=tmp_path)

        # First fetch
        df1 = provider.fetch_injury_report(week=1, season=2025)

        # Check cache file exists
        cache_file = tmp_path / "injuries_1_2025.parquet"
        assert cache_file.exists(), "Cache file should be created"

    def test_weather_caching(self, tmp_path):
        """Test that weather is cached properly."""
        from src.ingest import WeatherProvider

        provider = WeatherProvider(mock_mode=True, cache_dir=tmp_path)

        games_df = pd.DataFrame({
            'game_id': ['game_001'],
            'team': ['KC'],
            'game_time': [pd.Timestamp('2025-10-11 13:00:00')]
        })

        # First fetch
        result1 = provider.fetch_weather_data(games_df)

        # Check cache exists
        cache_file = tmp_path / "weather_2025-10-11.parquet"
        assert cache_file.exists(), "Cache file should be created"


class TestErrorHandling:
    """Tests for error handling."""

    def test_empty_games_df_for_weather(self):
        """Test handling of empty games DataFrame."""
        empty_df = pd.DataFrame()
        result = fetch_weather_data(empty_df, mock_mode=True)

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_invalid_week_number(self):
        """Test that invalid week numbers are handled gracefully."""
        # Should not raise an error, just return data
        props_df = fetch_current_props(week=100, season=2025, mock_mode=True)

        assert isinstance(props_df, pd.DataFrame)
        assert len(props_df) > 0

    def test_default_week_and_season(self):
        """Test that default week and season work."""
        props_df = fetch_current_props(mock_mode=True)

        assert isinstance(props_df, pd.DataFrame)
        assert len(props_df) > 0


class TestDataTypes:
    """Tests for proper data types."""

    def test_props_dtypes(self):
        """Test that props have correct data types."""
        props_df = fetch_current_props(week=1, season=2025, mock_mode=True)

        # String columns
        assert props_df['player_name'].dtype == object
        assert props_df['team'].dtype == object
        assert props_df['prop_type'].dtype == object

        # Numeric columns
        assert pd.api.types.is_numeric_dtype(props_df['line'])
        assert pd.api.types.is_numeric_dtype(props_df['over_odds'])
        assert pd.api.types.is_numeric_dtype(props_df['under_odds'])

        # Datetime columns
        assert pd.api.types.is_datetime64_any_dtype(props_df['game_time'])

    def test_injury_dtypes(self):
        """Test that injuries have correct data types."""
        injuries_df = fetch_injury_report(week=1, season=2025, mock_mode=True)

        if not injuries_df.empty:
            assert injuries_df['player_name'].dtype == object
            assert injuries_df['team'].dtype == object
            assert injuries_df['status'].dtype == object

    def test_baseline_stats_dtypes(self):
        """Test that baseline stats have correct data types."""
        stats_df = load_baseline_stats(mock_mode=True)

        assert stats_df['player_name'].dtype == object
        assert pd.api.types.is_numeric_dtype(stats_df['games_played'])
        assert pd.api.types.is_numeric_dtype(stats_df['consistency_score'])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

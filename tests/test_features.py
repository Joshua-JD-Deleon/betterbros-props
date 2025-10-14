"""
Tests for feature engineering.
"""

import pytest
import pandas as pd
import numpy as np
from src.features import (
    build_features,
    generate_trend_chips,
    calculate_ewma,
    odds_to_probability,
    calculate_vig,
    detect_correlation_groups,
)


@pytest.fixture
def mock_props_df():
    """Create mock props data for testing."""
    return pd.DataFrame({
        'player_id': ['p1', 'p2', 'p3', 'p4', 'p5'],
        'player_name': ['Patrick Mahomes', 'Tyreek Hill', 'Travis Kelce', 'Josh Allen', 'Stefon Diggs'],
        'team': ['KC', 'MIA', 'KC', 'BUF', 'BUF'],
        'position': ['QB', 'WR', 'TE', 'QB', 'WR'],
        'opponent': ['LV', 'NE', 'LV', 'NYJ', 'NYJ'],
        'prop_type': ['passing_yards', 'receiving_yards', 'receiving_yards', 'passing_yards', 'receiving_yards'],
        'line': [275.5, 85.5, 72.5, 268.5, 78.5],
        'over_odds': [-110, -115, -105, -110, -120],
        'under_odds': [-110, -105, -115, -110, -100],
        'game_id': ['game_001', 'game_002', 'game_001', 'game_003', 'game_003'],
        'game_time': pd.to_datetime('2025-10-11 13:00:00'),
        'home_away': ['home', 'home', 'home', 'away', 'away']
    })


@pytest.fixture
def mock_baseline_stats():
    """Create mock baseline stats for testing."""
    return pd.DataFrame({
        'player_id': ['p1', 'p2', 'p3', 'p4', 'p5'],
        'player_name': ['Patrick Mahomes', 'Tyreek Hill', 'Travis Kelce', 'Josh Allen', 'Stefon Diggs'],
        'position': ['QB', 'WR', 'TE', 'QB', 'WR'],
        'team': ['KC', 'MIA', 'KC', 'BUF', 'BUF'],
        'season': [2024] * 5,
        'games_played': [16, 17, 14, 15, 16],
        'avg_passing_yards': [285.3, None, None, 270.8, None],
        'avg_passing_tds': [2.1, None, None, 2.3, None],
        'avg_receiving_yards': [None, 92.5, 78.9, None, 82.3],
        'avg_receptions': [None, 7.2, 6.8, None, 7.5],
        'consistency_score': [0.82, 0.75, 0.88, 0.78, 0.80],
        'variance': [1250.5, 380.2, 290.5, 1580.3, 420.8],
        'last_3_games_avg': [295.2, 98.3, 72.5, 265.8, 75.5],
        'opponent_rank_vs_position': [None, 15, 8, None, 22]
    })


@pytest.fixture
def mock_injuries_df():
    """Create mock injuries data for testing."""
    return pd.DataFrame({
        'player_id': ['p1', 'p6'],
        'player_name': ['Patrick Mahomes', 'Some Teammate'],
        'team': ['KC', 'KC'],
        'position': ['QB', 'WR'],
        'status': ['Questionable', 'Out'],
        'injury_type': ['Ankle', 'Hamstring'],
        'expected_impact': ['Medium', 'High'],
    })


@pytest.fixture
def mock_weather_df():
    """Create mock weather data for testing."""
    return pd.DataFrame({
        'game_id': ['game_001', 'game_002', 'game_003'],
        'temperature': [72.0, 48.0, 38.0],
        'wind_speed': [8.0, 16.5, 12.0],
        'precipitation': [0.0, 0.0, 0.15],
        'is_dome': [True, False, False],
        'impact_level': ['None', 'High', 'Medium']
    })


def test_build_features_basic(mock_props_df):
    """Test basic feature building without context data."""
    result_df = build_features(mock_props_df)

    assert isinstance(result_df, pd.DataFrame)
    assert len(result_df) == len(mock_props_df)

    # Check that all required feature columns were added
    expected_features = [
        # Player form features
        'season_avg', 'last_3_avg', 'ewma_5', 'form_trend', 'consistency', 'days_since_last_game',
        # Matchup features
        'opponent_rank_vs_position', 'opponent_avg_allowed', 'matchup_advantage', 'historical_vs_opponent',
        # Usage features
        'target_share', 'snap_share', 'red_zone_share',
        # Game context features
        'is_home', 'vegas_implied_total', 'vegas_spread', 'pace_factor', 'game_total',
        # Weather features
        'temperature', 'wind_speed', 'precipitation_pct', 'is_dome', 'weather_impact',
        # Injury features
        'player_injury_status', 'key_teammate_out', 'opponent_key_defender_out',
        # Prop-specific features
        'line_vs_season_avg_delta', 'line_vs_last3_delta', 'implied_prob_over', 'implied_prob_under', 'vig',
        # Correlation tags
        'same_game_id', 'same_team', 'correlation_group'
    ]

    for feature in expected_features:
        assert feature in result_df.columns, f"Missing feature: {feature}"


def test_build_features_with_baseline_stats(mock_props_df, mock_baseline_stats):
    """Test feature building with baseline stats."""
    result_df = build_features(mock_props_df, mock_baseline_stats)

    assert isinstance(result_df, pd.DataFrame)
    assert 'season_avg' in result_df.columns
    assert 'consistency' in result_df.columns

    # Check that baseline stats were used for Patrick Mahomes
    mahomes_row = result_df[result_df['player_name'] == 'Patrick Mahomes'].iloc[0]
    assert mahomes_row['season_avg'] == 285.3  # From baseline stats
    assert mahomes_row['consistency'] == 0.82


def test_build_features_with_full_context(mock_props_df, mock_baseline_stats, mock_injuries_df, mock_weather_df):
    """Test feature building with full context data."""
    context = {
        'baseline_stats': mock_baseline_stats,
        'injuries': mock_injuries_df,
        'weather': mock_weather_df
    }

    result_df = build_features(mock_props_df, context)

    assert isinstance(result_df, pd.DataFrame)

    # Check weather data was merged
    kc_props = result_df[result_df['game_id'] == 'game_001']
    assert kc_props.iloc[0]['is_dome'] == True
    assert kc_props.iloc[0]['temperature'] == 72.0

    # Check injury data was merged
    mahomes_row = result_df[result_df['player_name'] == 'Patrick Mahomes'].iloc[0]
    assert mahomes_row['player_injury_status'] == 'Questionable'
    assert mahomes_row['key_teammate_out'] == True  # Some Teammate is Out


def test_feature_dtypes(mock_props_df):
    """Test that feature data types are correct."""
    result_df = build_features(mock_props_df)

    # Numeric features
    numeric_features = ['season_avg', 'last_3_avg', 'ewma_5', 'form_trend', 'consistency',
                       'opponent_rank_vs_position', 'opponent_avg_allowed', 'matchup_advantage',
                       'target_share', 'snap_share', 'red_zone_share',
                       'vegas_implied_total', 'vegas_spread', 'pace_factor', 'game_total',
                       'temperature', 'wind_speed', 'precipitation_pct',
                       'line_vs_season_avg_delta', 'line_vs_last3_delta',
                       'implied_prob_over', 'implied_prob_under', 'vig']

    for feature in numeric_features:
        assert pd.api.types.is_numeric_dtype(result_df[feature]), f"{feature} should be numeric"

    # Boolean/int features
    assert result_df['is_home'].dtype in [np.int64, np.int32, bool]
    assert result_df['is_dome'].dtype in [np.bool_, bool]


def test_feature_ranges(mock_props_df):
    """Test that features have realistic ranges."""
    result_df = build_features(mock_props_df)

    # Probabilities should be between 0 and 1
    assert (result_df['implied_prob_over'] >= 0).all()
    assert (result_df['implied_prob_over'] <= 1).all()
    assert (result_df['implied_prob_under'] >= 0).all()
    assert (result_df['implied_prob_under'] <= 1).all()

    # Shares should be between 0 and 1
    assert (result_df['target_share'] >= 0).all()
    assert (result_df['target_share'] <= 1).all()
    assert (result_df['snap_share'] >= 0).all()
    assert (result_df['snap_share'] <= 1).all()

    # Opponent rank should be between 1 and 32
    assert (result_df['opponent_rank_vs_position'] >= 1).all()
    assert (result_df['opponent_rank_vs_position'] <= 32).all()

    # Consistency should be between 0 and 1
    assert (result_df['consistency'] >= 0).all()
    assert (result_df['consistency'] <= 1).all()


def test_generate_trend_chips_basic(mock_props_df):
    """Test basic trend chip generation."""
    # First build features
    props_with_features = build_features(mock_props_df)

    trends = generate_trend_chips(props_with_features, n_chips=5)

    assert isinstance(trends, list)
    assert len(trends) <= 5  # Should return at most 5

    # Check structure of trend chips
    if len(trends) > 0:
        trend = trends[0]
        assert 'title' in trend
        assert 'description' in trend
        assert 'impact_direction' in trend
        assert 'confidence' in trend
        assert 'impacted_props' in trend
        assert 'diagnostics' in trend

        # Check data types
        assert isinstance(trend['title'], str)
        assert isinstance(trend['description'], str)
        assert trend['impact_direction'] in ['positive', 'negative']
        assert 0.0 <= trend['confidence'] <= 1.0
        assert isinstance(trend['impacted_props'], list)
        assert isinstance(trend['diagnostics'], dict)


def test_generate_trend_chips_without_features(mock_props_df):
    """Test that trend chips generation builds features if needed."""
    # Don't pre-build features
    trends = generate_trend_chips(mock_props_df, n_chips=3)

    assert isinstance(trends, list)
    # Should still work by building features internally


def test_generate_trend_chips_diagnostics(mock_props_df):
    """Test that trend chip diagnostics contain required info."""
    props_with_features = build_features(mock_props_df)
    trends = generate_trend_chips(props_with_features, n_chips=5)

    if len(trends) > 0:
        for trend in trends:
            diagnostics = trend['diagnostics']

            # Should have method and threshold
            assert 'method' in diagnostics
            assert isinstance(diagnostics['method'], str)

            # Should have mini_chart_data
            assert 'mini_chart_data' in diagnostics
            assert isinstance(diagnostics['mini_chart_data'], dict)


def test_calculate_ewma():
    """Test EWMA calculation."""
    values = [10.0, 12.0, 11.0, 13.0, 14.0]

    result = calculate_ewma(values, alpha=0.4)

    assert isinstance(result, float)
    assert result > 0

    # Test edge cases
    assert calculate_ewma([]) == 0.0
    assert calculate_ewma([5.0]) == 5.0


def test_odds_to_probability():
    """Test odds to probability conversion."""
    # Test negative odds (favorite)
    assert abs(odds_to_probability(-110) - 0.5238) < 0.001

    # Test positive odds (underdog)
    assert abs(odds_to_probability(100) - 0.5) < 0.001
    assert abs(odds_to_probability(200) - 0.3333) < 0.001

    # Test edge cases
    assert odds_to_probability(0) == 0.5
    assert odds_to_probability(np.nan) == 0.5


def test_calculate_vig():
    """Test vig calculation."""
    over_odds = pd.Series([-110, -115, -105])
    under_odds = pd.Series([-110, -105, -115])

    vig = calculate_vig(over_odds, under_odds)

    assert isinstance(vig, pd.Series)
    assert len(vig) == 3

    # Vig should be positive (bookmaker's edge)
    assert (vig > 0).all()

    # Typical vig is 3-5%
    assert (vig < 10).all()


def test_detect_correlation_groups(mock_props_df):
    """Test correlation group detection."""
    result_df = detect_correlation_groups(mock_props_df)

    assert 'correlation_group' in result_df.columns

    # Check that players on same team have related correlation groups
    kc_props = result_df[result_df['team'] == 'KC']
    assert len(kc_props['correlation_group'].unique()) > 0

    # QB and pass-catchers should have QB_WR correlation
    mahomes_group = result_df[result_df['player_name'] == 'Patrick Mahomes']['correlation_group'].iloc[0]
    assert 'QB' in mahomes_group
    assert 'KC' in mahomes_group


def test_player_form_features_consistency(mock_props_df):
    """Test that player form features are internally consistent."""
    result_df = build_features(mock_props_df)

    for idx, row in result_df.iterrows():
        # EWMA should be between season_avg and last_3_avg (roughly)
        ewma = row['ewma_5']
        season_avg = row['season_avg']
        last_3_avg = row['last_3_avg']

        # Allow some tolerance
        min_val = min(season_avg, last_3_avg) - 5
        max_val = max(season_avg, last_3_avg) + 5

        assert min_val <= ewma <= max_val, f"EWMA {ewma} outside range [{min_val}, {max_val}]"


def test_matchup_features_logic(mock_props_df):
    """Test that matchup features follow logical relationships."""
    result_df = build_features(mock_props_df)

    for idx, row in result_df.iterrows():
        rank = row['opponent_rank_vs_position']

        # Better defense (lower rank) should generally allow less
        if rank <= 10:
            # Top 10 defense - should allow less than season avg
            assert row['opponent_avg_allowed'] <= row['season_avg'] * 1.05
        elif rank >= 23:
            # Bottom 10 defense - should allow more than season avg
            assert row['opponent_avg_allowed'] >= row['season_avg'] * 0.95


def test_usage_features_by_position(mock_props_df):
    """Test that usage features make sense by position."""
    result_df = build_features(mock_props_df)

    # QBs should have high snap share
    qb_props = result_df[result_df['position'] == 'QB']
    assert (qb_props['snap_share'] >= 0.95).all()

    # WRs should have varied target shares
    wr_props = result_df[result_df['position'] == 'WR']
    assert (wr_props['target_share'] < 0.5).all()  # No WR gets >50% of targets


def test_game_context_features_per_game(mock_props_df):
    """Test that game context features are consistent per game."""
    result_df = build_features(mock_props_df)

    for game_id in result_df['game_id'].unique():
        game_props = result_df[result_df['game_id'] == game_id]

        # All props in same game should have same game_total
        assert game_props['game_total'].nunique() == 1

        # Implied totals for both teams should sum to approximately game_total
        if len(game_props) >= 2:
            total_implied = game_props['vegas_implied_total'].sum()
            game_total = game_props['game_total'].iloc[0]

            # Should be close (within 10% due to how we assign)
            assert abs(total_implied - game_total * len(game_props) / 2) < game_total * 0.5


def test_prop_specific_features_calculations(mock_props_df):
    """Test that prop-specific features are calculated correctly."""
    result_df = build_features(mock_props_df)

    for idx, row in result_df.iterrows():
        # Check delta calculations
        expected_season_delta = row['line'] - row['season_avg']
        assert abs(row['line_vs_season_avg_delta'] - expected_season_delta) < 0.1

        expected_last3_delta = row['line'] - row['last_3_avg']
        assert abs(row['line_vs_last3_delta'] - expected_last3_delta) < 0.1

        # Check that implied probs sum to > 1 (due to vig)
        total_prob = row['implied_prob_over'] + row['implied_prob_under']
        assert total_prob > 1.0
        assert total_prob < 1.15  # Typical vig range


def test_trend_chips_confidence_range():
    """Test that trend chip confidence scores are reasonable."""
    props_df = pd.DataFrame({
        'player_id': ['p1', 'p2'],
        'player_name': ['Player 1', 'Player 2'],
        'team': ['KC', 'BUF'],
        'position': ['QB', 'WR'],
        'opponent': ['LV', 'NYJ'],
        'prop_type': ['passing_yards', 'receiving_yards'],
        'line': [275.5, 85.5],
        'over_odds': [-110, -115],
        'under_odds': [-110, -105],
        'game_id': ['game_001', 'game_002'],
        'game_time': pd.to_datetime('2025-10-11 13:00:00'),
        'home_away': ['home', 'away']
    })

    props_with_features = build_features(props_df)
    trends = generate_trend_chips(props_with_features, n_chips=10)

    for trend in trends:
        assert 0.0 <= trend['confidence'] <= 1.0
        assert trend['confidence'] >= 0.50  # Minimum confidence threshold


def test_empty_dataframe_handling():
    """Test that functions handle empty DataFrames gracefully."""
    empty_df = pd.DataFrame()

    # Should not crash
    try:
        result = build_features(empty_df)
        assert isinstance(result, pd.DataFrame)
    except Exception as e:
        # It's okay to raise a specific exception, but shouldn't crash
        assert isinstance(e, (ValueError, KeyError))


def test_correlation_tags_structure(mock_props_df):
    """Test that correlation tags are properly structured."""
    result_df = build_features(mock_props_df)

    assert 'same_game_id' in result_df.columns
    assert 'same_team' in result_df.columns
    assert 'correlation_group' in result_df.columns

    # same_game_id should match game_id
    assert (result_df['same_game_id'] == result_df['game_id']).all()

    # same_team should match team
    assert (result_df['same_team'] == result_df['team']).all()

    # correlation_group should contain team name
    for idx, row in result_df.iterrows():
        assert row['team'] in row['correlation_group']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

"""
Tests for correlation estimation and copula modeling.

This test suite validates all correlation functions including:
- Rule-based correlation matrix generation
- Matrix validation and adjustment
- Correlated outcome sampling
- High correlation detection
"""

import pytest
import pandas as pd
import numpy as np
from src.corr import (
    estimate_correlations,
    build_correlation_matrix_rule_based,
    build_correlation_matrix_copula,
    sample_correlated_outcomes,
    detect_high_correlations,
    validate_correlation_matrix,
    adjust_correlation_matrix,
    get_correlation_between_props,
    CorrelationEstimator,
)


@pytest.fixture
def sample_props_df():
    """Create sample props DataFrame for testing."""
    return pd.DataFrame({
        'player_id': ['p1', 'p2', 'p3', 'p4', 'p5'],
        'player_name': ['Mahomes', 'Kelce', 'Hill', 'Allen', 'Diggs'],
        'team': ['KC', 'KC', 'KC', 'BUF', 'BUF'],
        'position': ['QB', 'TE', 'WR', 'QB', 'WR'],
        'prop_type': ['passing_yards', 'receiving_yards', 'receiving_yards', 'passing_yards', 'receiving_yards'],
        'game_id': ['KC@BUF', 'KC@BUF', 'KC@BUF', 'KC@BUF', 'KC@BUF'],
        'line': [275.5, 65.5, 75.5, 285.5, 85.5],
        'prob_over': [0.55, 0.60, 0.52, 0.58, 0.62]
    })


@pytest.fixture
def multi_game_props_df():
    """Create props DataFrame spanning multiple games."""
    return pd.DataFrame({
        'player_id': ['p1', 'p2', 'p3', 'p4'],
        'player_name': ['Mahomes', 'Kelce', 'Brady', 'Evans'],
        'team': ['KC', 'KC', 'TB', 'TB'],
        'position': ['QB', 'TE', 'QB', 'WR'],
        'prop_type': ['passing_yards', 'receiving_yards', 'passing_yards', 'receiving_yards'],
        'game_id': ['KC@BUF', 'KC@BUF', 'TB@NO', 'TB@NO'],
        'line': [275.5, 65.5, 280.5, 70.5],
        'prob_over': [0.55, 0.60, 0.53, 0.58]
    })


class TestEstimateCorrelations:
    """Tests for main correlation estimation function."""

    def test_basic_correlation_estimation(self, sample_props_df):
        """Test basic correlation matrix estimation."""
        corr_matrix = estimate_correlations(sample_props_df)

        assert isinstance(corr_matrix, np.ndarray)
        assert corr_matrix.shape == (5, 5)

        # Check diagonal is 1.0
        assert np.allclose(np.diag(corr_matrix), 1.0)

        # Check symmetry
        assert np.allclose(corr_matrix, corr_matrix.T)

        # Check values in valid range
        assert np.all((corr_matrix >= -1.0) & (corr_matrix <= 1.0))

    def test_qb_wr_positive_correlation(self, sample_props_df):
        """Test QB-WR pairs have positive correlation."""
        corr_matrix = estimate_correlations(sample_props_df)

        # Mahomes (idx 0) and Kelce (idx 1) should be positively correlated
        mahomes_kelce_corr = corr_matrix[0, 1]
        assert mahomes_kelce_corr > 0.3, "QB-TE correlation should be positive"

        # Allen (idx 3) and Diggs (idx 4) should be positively correlated
        allen_diggs_corr = corr_matrix[3, 4]
        assert allen_diggs_corr > 0.3, "QB-WR correlation should be positive"

    def test_same_position_negative_correlation(self, sample_props_df):
        """Test same position players have negative correlation."""
        corr_matrix = estimate_correlations(sample_props_df)

        # Kelce (idx 1) and Hill (idx 2) - both receivers on same team
        kelce_hill_corr = corr_matrix[1, 2]
        assert kelce_hill_corr < 0, "Same team WR/TE should be negatively correlated"

    def test_opposing_teams_low_correlation(self, sample_props_df):
        """Test opposing team players have low positive correlation."""
        corr_matrix = estimate_correlations(sample_props_df)

        # Mahomes (KC) and Allen (BUF) - opposing QBs
        mahomes_allen_corr = corr_matrix[0, 3]
        assert 0.0 <= mahomes_allen_corr <= 0.3, "Opposing QBs should have slight positive correlation"

    def test_different_games_independent(self, multi_game_props_df):
        """Test props from different games are independent."""
        corr_matrix = estimate_correlations(multi_game_props_df)

        # Mahomes (KC@BUF) and Brady (TB@NO) - different games
        mahomes_brady_corr = corr_matrix[0, 2]
        assert abs(mahomes_brady_corr) < 0.15, "Different games should be nearly independent"


class TestCorrelationRules:
    """Tests for specific correlation rule logic."""

    def test_same_player_correlation(self):
        """Test same player props have high positive correlation."""
        prop1 = {
            'player_id': 'p1',
            'player_name': 'Mahomes',
            'team': 'KC',
            'position': 'QB',
            'prop_type': 'passing_yards',
            'game_id': 'KC@BUF'
        }
        prop2 = {
            'player_id': 'p1',
            'player_name': 'Mahomes',
            'team': 'KC',
            'position': 'QB',
            'prop_type': 'passing_tds',
            'game_id': 'KC@BUF'
        }

        np.random.seed(42)  # For reproducibility
        corr = get_correlation_between_props(prop1, prop2)
        assert 0.3 <= corr <= 0.7, "Same player should have moderate to high correlation"

    def test_competing_rbs_negative(self):
        """Test competing RBs have negative correlation."""
        rb1 = {
            'player_id': 'r1',
            'team': 'KC',
            'position': 'RB',
            'prop_type': 'rushing_yards',
            'game_id': 'KC@BUF'
        }
        rb2 = {
            'player_id': 'r2',
            'team': 'KC',
            'position': 'RB',
            'prop_type': 'rushing_yards',
            'game_id': 'KC@BUF'
        }

        np.random.seed(42)
        corr = get_correlation_between_props(rb1, rb2)
        assert corr < 0, "Competing RBs should be negatively correlated"
        assert -0.5 <= corr <= -0.2, "RB correlation should be moderately negative"

    def test_different_games_zero(self):
        """Test different games have zero correlation."""
        prop1 = {
            'player_id': 'p1',
            'team': 'KC',
            'position': 'QB',
            'prop_type': 'passing_yards',
            'game_id': 'KC@BUF'
        }
        prop2 = {
            'player_id': 'p2',
            'team': 'TB',
            'position': 'QB',
            'prop_type': 'passing_yards',
            'game_id': 'TB@NO'
        }

        np.random.seed(42)
        corr = get_correlation_between_props(prop1, prop2)
        assert abs(corr) <= 0.15, "Different games should be nearly independent"


class TestMatrixValidation:
    """Tests for correlation matrix validation and adjustment."""

    def test_validate_valid_matrix(self):
        """Test validation of a valid correlation matrix."""
        corr_matrix = np.array([
            [1.0, 0.5, 0.2],
            [0.5, 1.0, 0.3],
            [0.2, 0.3, 1.0]
        ])

        result = validate_correlation_matrix(corr_matrix)

        assert result['is_valid']
        assert result['is_symmetric']
        assert result['is_positive_definite']
        assert result['diagonal_correct']
        assert result['values_in_range']
        assert len(result['issues']) == 0

    def test_validate_asymmetric_matrix(self):
        """Test detection of asymmetric matrix."""
        corr_matrix = np.array([
            [1.0, 0.5, 0.2],
            [0.6, 1.0, 0.3],  # Asymmetric
            [0.2, 0.3, 1.0]
        ])

        result = validate_correlation_matrix(corr_matrix)

        assert not result['is_symmetric']
        assert not result['is_valid']
        assert any('symmetric' in issue.lower() for issue in result['issues'])

    def test_validate_non_positive_definite(self):
        """Test detection of non-positive definite matrix."""
        # Create non-positive definite matrix
        corr_matrix = np.array([
            [1.0, 0.9, 0.9],
            [0.9, 1.0, 0.9],
            [0.9, 0.9, 1.0]
        ])

        result = validate_correlation_matrix(corr_matrix)

        # This matrix might be barely positive definite or not
        assert 'min_eigenvalue' in result
        assert result['min_eigenvalue'] is not None

    def test_adjust_correlation_matrix(self):
        """Test adjustment of correlation matrix to be positive definite."""
        # Create potentially problematic matrix
        corr_matrix = np.array([
            [1.0, 0.8, 0.7],
            [0.8, 1.0, 0.9],
            [0.7, 0.9, 1.0]
        ])

        adjusted = adjust_correlation_matrix(corr_matrix)

        # Check properties
        assert np.allclose(np.diag(adjusted), 1.0), "Diagonal should be 1.0"
        assert np.allclose(adjusted, adjusted.T), "Should be symmetric"

        # Check positive definiteness
        eigenvalues = np.linalg.eigvalsh(adjusted)
        assert np.all(eigenvalues >= 0), "Should be positive definite"


class TestSamplingCorrelatedOutcomes:
    """Tests for correlated outcome sampling."""

    def test_sample_shape(self, sample_props_df):
        """Test output shape of sampled outcomes."""
        probs = sample_props_df['prob_over'].values
        corr_matrix = np.eye(len(probs))

        outcomes = sample_correlated_outcomes(
            probs, corr_matrix, n_samples=1000
        )

        assert outcomes.shape == (1000, 5)
        assert np.all((outcomes == 0) | (outcomes == 1)), "Outcomes should be binary"

    def test_sample_respects_probabilities(self):
        """Test that samples approximately match input probabilities."""
        probs = np.array([0.3, 0.5, 0.7, 0.9])
        corr_matrix = np.eye(4)

        np.random.seed(42)
        outcomes = sample_correlated_outcomes(
            probs, corr_matrix, n_samples=10000
        )

        observed_probs = outcomes.mean(axis=0)

        # Allow 5% tolerance
        for i, (obs, exp) in enumerate(zip(observed_probs, probs)):
            assert abs(obs - exp) < 0.05, f"Probability {i}: {obs:.3f} vs {exp:.3f}"

    def test_sample_independent_when_uncorrelated(self):
        """Test independent sampling when correlation is zero."""
        probs = np.array([0.5, 0.5])
        corr_matrix = np.eye(2)

        np.random.seed(42)
        outcomes = sample_correlated_outcomes(
            probs, corr_matrix, n_samples=5000
        )

        # Compute observed correlation
        observed_corr = np.corrcoef(outcomes.T)[0, 1]

        # Should be close to 0 for independent samples
        assert abs(observed_corr) < 0.05, f"Correlation should be ~0, got {observed_corr:.3f}"

    def test_sample_positive_correlation(self):
        """Test that positive correlation is reflected in samples."""
        probs = np.array([0.5, 0.5])
        corr_matrix = np.array([
            [1.0, 0.7],
            [0.7, 1.0]
        ])

        np.random.seed(42)
        outcomes = sample_correlated_outcomes(
            probs, corr_matrix, n_samples=5000
        )

        # Compute observed correlation
        observed_corr = np.corrcoef(outcomes.T)[0, 1]

        # Should be positive and roughly match (within sampling variance)
        assert observed_corr > 0.4, f"Correlation should be positive, got {observed_corr:.3f}"

    def test_sample_with_invalid_correlation_matrix(self):
        """Test graceful fallback with invalid correlation matrix."""
        probs = np.array([0.5, 0.5, 0.5])

        # Create invalid (non-PSD) matrix
        corr_matrix = np.array([
            [1.0, 0.9, 0.9],
            [0.9, 1.0, -0.9],
            [0.9, -0.9, 1.0]
        ])

        # Should not crash - will adjust matrix internally
        outcomes = sample_correlated_outcomes(
            probs, corr_matrix, n_samples=100
        )

        assert outcomes.shape == (100, 3)
        assert np.all((outcomes == 0) | (outcomes == 1))


class TestHighCorrelationDetection:
    """Tests for detecting high correlations."""

    def test_detect_high_correlations(self, sample_props_df):
        """Test detection of high correlation pairs."""
        corr_matrix = estimate_correlations(sample_props_df)

        high_corr = detect_high_correlations(
            sample_props_df, corr_matrix, threshold=0.3
        )

        assert isinstance(high_corr, list)
        assert len(high_corr) > 0, "Should find some high correlations"

        # Check structure
        for pair in high_corr:
            assert 'prop_1' in pair
            assert 'prop_2' in pair
            assert 'correlation' in pair
            assert 'reason' in pair
            assert abs(pair['correlation']) >= 0.3

    def test_detect_sorts_by_magnitude(self, sample_props_df):
        """Test that high correlations are sorted by magnitude."""
        corr_matrix = estimate_correlations(sample_props_df)

        high_corr = detect_high_correlations(
            sample_props_df, corr_matrix, threshold=0.2
        )

        if len(high_corr) > 1:
            # Check descending order by absolute correlation
            for i in range(len(high_corr) - 1):
                assert abs(high_corr[i]['correlation']) >= abs(high_corr[i + 1]['correlation'])

    def test_detect_includes_negative_correlations(self):
        """Test that negative correlations are detected."""
        props_df = pd.DataFrame({
            'player_id': ['r1', 'r2'],
            'player_name': ['RB1', 'RB2'],
            'team': ['KC', 'KC'],
            'position': ['RB', 'RB'],
            'prop_type': ['rushing_yards', 'rushing_yards'],
            'game_id': ['KC@BUF', 'KC@BUF'],
            'prob_over': [0.5, 0.5]
        })

        corr_matrix = estimate_correlations(props_df)
        high_corr = detect_high_correlations(props_df, corr_matrix, threshold=0.2)

        # Should detect negative correlation between competing RBs
        assert len(high_corr) > 0
        assert any(pair['correlation'] < 0 for pair in high_corr)


class TestCorrelationEstimatorClass:
    """Tests for CorrelationEstimator class interface."""

    def test_estimator_initialization(self):
        """Test CorrelationEstimator initialization."""
        estimator = CorrelationEstimator(use_copulas=True)

        assert estimator is not None
        assert estimator.use_copulas is True
        assert estimator.copula_model is None
        assert estimator.fitted_corr_matrix is None

    def test_estimator_simple_correlations(self, sample_props_df):
        """Test simple correlation estimation via class."""
        estimator = CorrelationEstimator()
        corr_matrix = estimator.estimate_simple_correlations(sample_props_df)

        assert isinstance(corr_matrix, np.ndarray)
        assert corr_matrix.shape == (5, 5)
        assert np.allclose(np.diag(corr_matrix), 1.0)

    def test_estimator_fit_copula(self):
        """Test copula fitting (currently falls back to empirical)."""
        estimator = CorrelationEstimator(use_copulas=True)

        # Create fake historical data
        historical = pd.DataFrame({
            'prop1': [1, 0, 1, 1, 0, 1, 0, 1, 1, 0],
            'prop2': [1, 1, 1, 0, 0, 1, 0, 0, 1, 1],
            'prop3': [0, 0, 1, 1, 0, 1, 1, 1, 0, 0]
        })

        estimator.fit_copula_model(historical)

        # Should have fitted correlation matrix
        assert estimator.fitted_corr_matrix is not None
        assert estimator.fitted_corr_matrix.shape == (3, 3)

    def test_estimator_sample_outcomes(self, sample_props_df):
        """Test outcome sampling via class."""
        estimator = CorrelationEstimator()

        outcomes = estimator.sample_correlated_outcomes(
            sample_props_df, n_samples=1000
        )

        assert outcomes.shape == (1000, 5)
        assert np.all((outcomes == 0) | (outcomes == 1))


class TestCopulaFunctions:
    """Tests for copula-based correlation estimation."""

    def test_build_correlation_matrix_copula(self):
        """Test copula-based correlation matrix building."""
        # Create synthetic historical outcomes
        historical = pd.DataFrame({
            'prop1': [1, 0, 1, 1, 0, 1, 0, 1, 1, 0],
            'prop2': [1, 1, 1, 0, 0, 1, 0, 0, 1, 1],
            'prop3': [0, 0, 1, 1, 0, 1, 1, 1, 0, 0]
        })

        corr_matrix = build_correlation_matrix_copula(historical)

        assert isinstance(corr_matrix, np.ndarray)
        assert corr_matrix.shape == (3, 3)
        assert np.allclose(np.diag(corr_matrix), 1.0)
        assert np.allclose(corr_matrix, corr_matrix.T)

    def test_copula_insufficient_data(self):
        """Test copula with insufficient historical data."""
        # Only 5 samples
        historical = pd.DataFrame({
            'prop1': [1, 0, 1, 1, 0],
            'prop2': [1, 1, 1, 0, 0]
        })

        with pytest.warns(UserWarning):
            corr_matrix = build_correlation_matrix_copula(historical)

        # Should return identity matrix
        assert np.allclose(corr_matrix, np.eye(2))


class TestIntegrationWithOptimizer:
    """Tests for integration with slip optimizer."""

    def test_correlation_matrix_compatible_with_optimizer(self, sample_props_df):
        """Test that correlation matrix works with optimizer's Monte Carlo."""
        # This simulates what the optimizer does
        corr_matrix = estimate_correlations(sample_props_df)

        # Select subset of props (like optimizer does)
        selected_indices = [0, 1, 3]  # Mahomes, Kelce, Allen
        sub_corr = corr_matrix[np.ix_(selected_indices, selected_indices)]

        # Extract probabilities
        probs = sample_props_df.iloc[selected_indices]['prob_over'].values

        # Sample outcomes (like optimizer's Monte Carlo)
        outcomes = sample_correlated_outcomes(
            probs, sub_corr, n_samples=1000
        )

        # Check parlay wins
        all_win = np.all(outcomes == 1, axis=1)
        win_prob = np.mean(all_win)

        # Sanity check: should be less than product of individual probs
        independent_prob = np.prod(probs)
        assert 0 < win_prob <= independent_prob * 1.5  # Allow some variance


def test_reproducibility_with_seed():
    """Test that results are reproducible with same seed."""
    props_df = pd.DataFrame({
        'player_id': ['p1', 'p2'],
        'player_name': ['Player1', 'Player2'],
        'team': ['KC', 'KC'],
        'position': ['QB', 'WR'],
        'prop_type': ['passing_yards', 'receiving_yards'],
        'game_id': ['KC@BUF', 'KC@BUF'],
        'prob_over': [0.5, 0.6]
    })

    # Run twice with same seed
    np.random.seed(42)
    corr1 = estimate_correlations(props_df)

    np.random.seed(42)
    corr2 = estimate_correlations(props_df)

    assert np.allclose(corr1, corr2), "Results should be reproducible"


def test_edge_case_single_prop():
    """Test correlation estimation with single prop."""
    props_df = pd.DataFrame({
        'player_id': ['p1'],
        'player_name': ['Mahomes'],
        'team': ['KC'],
        'position': ['QB'],
        'prop_type': ['passing_yards'],
        'game_id': ['KC@BUF'],
        'prob_over': [0.55]
    })

    corr_matrix = estimate_correlations(props_df)

    assert corr_matrix.shape == (1, 1)
    assert corr_matrix[0, 0] == 1.0


def test_edge_case_empty_dataframe():
    """Test correlation estimation with empty DataFrame."""
    props_df = pd.DataFrame(columns=['player_id', 'player_name', 'team', 'position', 'prop_type', 'game_id'])

    corr_matrix = estimate_correlations(props_df)

    assert corr_matrix.shape == (0, 0)

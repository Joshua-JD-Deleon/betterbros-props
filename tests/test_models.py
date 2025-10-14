"""
Tests for probability models.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile

from src.models import (
    estimate_probabilities,
    GradientBoostingModel,
    BayesianModel,
    CalibrationEvaluator,
    calibrate_probabilities,
    estimate_uncertainty,
    train_gbm,
    predict_gbm
)


@pytest.fixture
def sample_props_df():
    """Sample props dataframe for testing."""
    return pd.DataFrame({
        'player_id': ['p1', 'p2', 'p3', 'p4', 'p5'],
        'player_name': ['Player 1', 'Player 2', 'Player 3', 'Player 4', 'Player 5'],
        'line': [250.5, 75.5, 50.5, 125.5, 200.5],
        'over_odds': [-110, -115, -105, -120, -108],
        'under_odds': [-110, -105, -115, -100, -112],
        'implied_prob_over': [0.524, 0.535, 0.512, 0.545, 0.519],
        'line_zscore': [-0.5, 0.2, -0.8, 0.1, -0.3],
        'recent_form': [0.65, 0.55, 0.72, 0.48, 0.60],
        'matchup_difficulty': [0.4, 0.6, 0.3, 0.7, 0.5],
        'injury_risk': [0.0, 0.1, 0.0, 0.2, 0.0],
        'weather_impact': [0.0, -0.05, 0.0, 0.0, 0.03]
    })


@pytest.fixture
def sample_training_data():
    """Sample training data for model testing."""
    np.random.seed(42)
    n_samples = 100

    return pd.DataFrame({
        'player_id': [f'p{i}' for i in range(n_samples)],
        'team': np.random.choice(['KC', 'BUF', 'SF', 'DAL'], n_samples),
        'line_zscore': np.random.randn(n_samples),
        'recent_form': np.random.uniform(0.3, 0.8, n_samples),
        'matchup_difficulty': np.random.uniform(0.2, 0.8, n_samples),
        'injury_risk': np.random.choice([0, 0.1, 0.2], n_samples),
        'weather_impact': np.random.uniform(-0.1, 0.1, n_samples),
        'outcome': np.random.choice([0, 1], n_samples)
    })


def test_estimate_probabilities_basic(sample_props_df):
    """Test basic probability estimation."""
    result_df = estimate_probabilities(sample_props_df)

    # Check returned dataframe
    assert isinstance(result_df, pd.DataFrame)
    assert len(result_df) == len(sample_props_df)

    # Check required columns
    required_cols = ['prob_over', 'prob_under', 'ci_lower', 'ci_upper', 'sigma', 'ci_width', 'drivers']
    for col in required_cols:
        assert col in result_df.columns, f"Missing column: {col}"


def test_probabilities_valid_range(sample_props_df):
    """Test that probabilities are in valid [0, 1] range."""
    result_df = estimate_probabilities(sample_props_df)

    # Check probabilities are valid
    assert (result_df['prob_over'] >= 0).all()
    assert (result_df['prob_over'] <= 1).all()
    assert (result_df['prob_under'] >= 0).all()
    assert (result_df['prob_under'] <= 1).all()

    # Check prob_over + prob_under = 1
    prob_sum = result_df['prob_over'] + result_df['prob_under']
    assert np.allclose(prob_sum, 1.0, atol=1e-6)


def test_confidence_intervals_valid(sample_props_df):
    """Test that confidence intervals are valid."""
    result_df = estimate_probabilities(sample_props_df)

    # Check CI bounds are valid
    assert (result_df['ci_lower'] >= 0).all()
    assert (result_df['ci_upper'] <= 1).all()
    assert (result_df['ci_lower'] <= result_df['prob_over']).all()
    assert (result_df['ci_upper'] >= result_df['prob_over']).all()

    # Check CI width
    expected_width = result_df['ci_upper'] - result_df['ci_lower']
    assert np.allclose(result_df['ci_width'], expected_width)


def test_gbm_model_initialization():
    """Test GBM model initialization."""
    model = GradientBoostingModel()
    assert model is not None
    assert model.model_type == "lightgbm"
    assert model.model is None
    assert model.feature_columns is None


def test_gbm_model_training(sample_training_data):
    """Test GBM model training."""
    feature_cols = ['line_zscore', 'recent_form', 'matchup_difficulty', 'injury_risk', 'weather_impact']
    X = sample_training_data[feature_cols]
    y = sample_training_data['outcome']

    model = GradientBoostingModel(model_type="lightgbm")
    metrics = model.train(X, y, validation_split=0.2)

    # Check metrics returned
    assert 'train_auc' in metrics
    assert 'val_auc' in metrics
    assert 'train_logloss' in metrics
    assert 'val_logloss' in metrics

    # Check model is trained
    assert model.model is not None
    assert model.feature_columns == feature_cols


def test_gbm_model_prediction(sample_training_data, sample_props_df):
    """Test GBM model prediction."""
    feature_cols = ['line_zscore', 'recent_form', 'matchup_difficulty', 'injury_risk', 'weather_impact']
    X = sample_training_data[feature_cols]
    y = sample_training_data['outcome']

    model = GradientBoostingModel()
    model.train(X, y)

    # Predict on new data
    X_new = sample_props_df[feature_cols]
    probs = model.predict_proba(X_new)

    # Check predictions
    assert len(probs) == len(X_new)
    assert (probs >= 0).all()
    assert (probs <= 1).all()


def test_gbm_model_feature_importance(sample_training_data):
    """Test feature importance extraction."""
    feature_cols = ['line_zscore', 'recent_form', 'matchup_difficulty', 'injury_risk', 'weather_impact']
    X = sample_training_data[feature_cols]
    y = sample_training_data['outcome']

    model = GradientBoostingModel()
    model.train(X, y)

    importance = model.get_feature_importance(top_n=3)

    assert isinstance(importance, pd.DataFrame)
    assert len(importance) <= 3
    if not importance.empty:
        assert 'feature' in importance.columns
        assert 'importance' in importance.columns


def test_gbm_model_save_load(sample_training_data):
    """Test model save and load."""
    feature_cols = ['line_zscore', 'recent_form', 'matchup_difficulty']
    X = sample_training_data[feature_cols]
    y = sample_training_data['outcome']

    # Train model
    model = GradientBoostingModel()
    model.train(X, y)

    # Save model
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "test_model.pkl"
        model.save(save_path)

        # Load model
        loaded_model = GradientBoostingModel()
        loaded_model.load(save_path)

        assert loaded_model.feature_columns == feature_cols
        assert loaded_model.model is not None


def test_train_gbm_convenience_function(sample_training_data):
    """Test train_gbm convenience function."""
    data = sample_training_data.copy()
    data['hit'] = data['outcome']

    result = train_gbm(data, target='hit')

    assert 'model' in result
    assert 'feature_importance' in result
    assert 'metrics' in result
    assert isinstance(result['model'], GradientBoostingModel)


def test_predict_gbm_convenience_function(sample_training_data, sample_props_df):
    """Test predict_gbm convenience function."""
    data = sample_training_data.copy()
    data['hit'] = data['outcome']

    # Train model
    model_dict = train_gbm(data, target='hit')

    # Predict
    feature_cols = [c for c in data.columns if c not in ['hit', 'player_id', 'team', 'outcome']]
    X_new = sample_props_df[feature_cols]
    probs = predict_gbm(model_dict, X_new)

    assert len(probs) == len(X_new)
    assert (probs >= 0).all()
    assert (probs <= 1).all()


def test_bayesian_model_initialization():
    """Test Bayesian model initialization."""
    model = BayesianModel()
    assert model is not None
    assert model.is_fitted is False


def test_calibration_evaluator():
    """Test calibration evaluator."""
    np.random.seed(42)
    y_true = np.random.choice([0, 1], 100)
    y_pred = np.random.uniform(0.3, 0.7, 100)

    evaluator = CalibrationEvaluator(n_bins=10)
    metrics = evaluator.evaluate_calibration(y_true, y_pred)

    assert 'ece' in metrics
    assert 'mce' in metrics
    assert 'brier_score' in metrics
    assert 'log_loss' in metrics
    assert 'calibration_curve' in metrics

    # Check metrics are valid
    assert 0 <= metrics['ece'] <= 1
    assert 0 <= metrics['mce'] <= 1
    assert metrics['brier_score'] >= 0


def test_calibrate_probabilities():
    """Test probability calibration function."""
    np.random.seed(42)
    raw_probs = np.random.uniform(0.3, 0.7, 100)
    true_labels = np.random.choice([0, 1], 100)

    calibrated_probs, metrics = calibrate_probabilities(raw_probs, true_labels, method="isotonic")

    assert len(calibrated_probs) == len(raw_probs)
    assert (calibrated_probs >= 0).all()
    assert (calibrated_probs <= 1).all()
    assert metrics['calibration_method'] == 'isotonic'


def test_calibrate_probabilities_without_labels():
    """Test calibration without labels returns uncalibrated."""
    np.random.seed(42)
    raw_probs = np.random.uniform(0.3, 0.7, 100)

    calibrated_probs, metrics = calibrate_probabilities(raw_probs, true_labels=None)

    assert np.allclose(calibrated_probs, raw_probs)
    assert metrics['calibration_method'] == 'none'


def test_estimate_uncertainty():
    """Test uncertainty estimation."""
    probs = np.array([0.5, 0.6, 0.7, 0.4, 0.55])

    ci_lower, ci_upper = estimate_uncertainty(probs, method="beta_binomial")

    assert len(ci_lower) == len(probs)
    assert len(ci_upper) == len(probs)
    assert (ci_lower >= 0).all()
    assert (ci_upper <= 1).all()
    assert (ci_lower <= probs).all()
    assert (ci_upper >= probs).all()


def test_heuristic_probabilities_use_features(sample_props_df):
    """Test that heuristic probabilities adjust based on features."""
    result_df = estimate_probabilities(sample_props_df)

    # Check that probabilities vary (not all the same)
    assert result_df['prob_over'].nunique() > 1

    # Check that some props have clearly different probabilities
    prob_range = result_df['prob_over'].max() - result_df['prob_over'].min()
    assert prob_range > 0.1, "Probabilities should vary based on features"


def test_estimate_probabilities_with_models(sample_training_data, sample_props_df):
    """Test probability estimation with trained models."""
    # Train a model
    feature_cols = ['line_zscore', 'recent_form', 'matchup_difficulty', 'injury_risk', 'weather_impact']
    X = sample_training_data[feature_cols]
    y = sample_training_data['outcome']

    model = GradientBoostingModel()
    model.train(X, y)

    # Estimate probabilities using trained model
    result_df = estimate_probabilities(sample_props_df, models=[model])

    assert 'prob_over' in result_df.columns
    assert (result_df['prob_over'] >= 0).all()
    assert (result_df['prob_over'] <= 1).all()


def test_calibration_alert():
    """Test calibration drift detection."""
    np.random.seed(42)

    evaluator = CalibrationEvaluator()

    # Create well-calibrated data
    good_data = pd.DataFrame({
        'predicted_prob': np.random.uniform(0.4, 0.6, 50),
        'outcome': np.random.choice([0, 1], 50)
    })

    alert = evaluator.check_calibration_alert(good_data, threshold=0.15)
    # May or may not trigger - depends on random data

    # Test with insufficient data
    small_data = good_data.head(10)
    alert = evaluator.check_calibration_alert(small_data)
    assert alert is None  # Should not alert with < 20 samples


def test_estimate_probabilities_includes_drivers(sample_props_df):
    """Test that drivers are included when requested."""
    result_df = estimate_probabilities(sample_props_df, include_drivers=True)

    assert 'drivers' in result_df.columns
    assert isinstance(result_df['drivers'].iloc[0], list)


def test_ensemble_methods(sample_props_df):
    """Test different ensemble methods."""
    # Create mock models
    class MockModel:
        def predict_proba(self, X):
            return np.random.uniform(0.4, 0.6, len(X))

    models = [MockModel() for _ in range(3)]

    # Test average
    result_avg = estimate_probabilities(sample_props_df, models=models, ensemble_method="average")
    assert 'prob_over' in result_avg.columns

    # Test median
    result_med = estimate_probabilities(sample_props_df, models=models, ensemble_method="median")
    assert 'prob_over' in result_med.columns


def test_sigma_calculation(sample_props_df):
    """Test that sigma (uncertainty) is calculated."""
    result_df = estimate_probabilities(sample_props_df)

    assert 'sigma' in result_df.columns
    assert (result_df['sigma'] > 0).all()
    assert (result_df['sigma'] < 0.5).all()  # Should be reasonable values


def test_ev_variation(sample_props_df):
    """Test that some props have clearly good/bad EV."""
    result_df = estimate_probabilities(sample_props_df)

    # Add EV calculation (simplified)
    # EV = prob_over * payout_over - (1 - prob_over)
    # For -110 odds, payout is ~0.91
    result_df['ev_over'] = result_df['prob_over'] * 0.91 - (1 - result_df['prob_over'])

    # Should have some variation in EV
    ev_range = result_df['ev_over'].max() - result_df['ev_over'].min()
    assert ev_range > 0.05, "Should have varied EV across props"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

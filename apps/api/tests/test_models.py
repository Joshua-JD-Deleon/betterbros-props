"""
Tests for ML models

Tests basic functionality of GBM, Bayesian, Calibration, and Ensemble models.
"""
import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import train_test_split

from src.models import (
    GradientBoostingModel,
    BayesianModel,
    CalibrationPipeline,
    EnsemblePredictor,
)


@pytest.fixture
def synthetic_data():
    """Generate synthetic training data"""
    np.random.seed(42)
    n_samples = 500

    X = pd.DataFrame({
        "feature_1": np.random.uniform(0, 10, n_samples),
        "feature_2": np.random.uniform(-5, 5, n_samples),
        "feature_3": np.random.randint(0, 3, n_samples),
        "feature_4": np.random.normal(0, 1, n_samples),
    })

    # Generate outcome based on features
    logit = -1 + 0.5 * X["feature_1"] - 0.3 * X["feature_2"] + np.random.normal(0, 2, n_samples)
    y = (1 / (1 + np.exp(-logit)) > 0.5).astype(int)

    return X, y


@pytest.fixture
def synthetic_data_with_players():
    """Generate synthetic data with player IDs"""
    np.random.seed(42)
    n_samples = 500
    n_players = 20

    player_ids = [f"player_{i:03d}" for i in range(n_players)]

    df = pd.DataFrame({
        "player_id": np.random.choice(player_ids, n_samples),
        "feature_1": np.random.uniform(0, 10, n_samples),
        "feature_2": np.random.uniform(-5, 5, n_samples),
        "feature_3": np.random.randint(0, 3, n_samples),
        "feature_4": np.random.normal(0, 1, n_samples),
    })

    # Generate outcome
    logit = -1 + 0.5 * df["feature_1"] - 0.3 * df["feature_2"] + np.random.normal(0, 2, n_samples)
    df["outcome"] = (1 / (1 + np.exp(-logit)) > 0.5).astype(int)

    return df


class TestGradientBoostingModel:
    """Tests for GradientBoostingModel"""

    def test_initialization(self):
        """Test model initialization"""
        gbm = GradientBoostingModel(model_type="xgboost")
        assert gbm.model_type == "xgboost"
        assert gbm.model is None

    def test_train_xgboost(self, synthetic_data):
        """Test training XGBoost model"""
        X, y = synthetic_data
        gbm = GradientBoostingModel(model_type="xgboost")

        metrics = gbm.train(X, y, cv_splits=3, verbose=False)

        assert "cv_log_loss_mean" in metrics
        assert "cv_auc_mean" in metrics
        assert metrics["cv_auc_mean"] > 0.5  # Better than random
        assert gbm.model is not None
        assert gbm.feature_names == list(X.columns)

    def test_train_lightgbm(self, synthetic_data):
        """Test training LightGBM model"""
        X, y = synthetic_data
        gbm = GradientBoostingModel(model_type="lightgbm")

        metrics = gbm.train(X, y, cv_splits=3, verbose=False)

        assert metrics["cv_auc_mean"] > 0.5
        assert gbm.model is not None

    def test_predict_proba(self, synthetic_data):
        """Test probability predictions"""
        X, y = synthetic_data
        X_train, X_test = train_test_split(X, test_size=0.2, random_state=42)
        y_train, y_test = train_test_split(y, test_size=0.2, random_state=42)

        gbm = GradientBoostingModel(model_type="xgboost")
        gbm.train(X_train, y_train, cv_splits=2, verbose=False)

        probs = gbm.predict_proba(X_test)

        assert len(probs) == len(X_test)
        assert np.all((probs >= 0) & (probs <= 1))

    def test_feature_importance(self, synthetic_data):
        """Test feature importance extraction"""
        X, y = synthetic_data
        gbm = GradientBoostingModel(model_type="xgboost")
        gbm.train(X, y, cv_splits=2, verbose=False)

        importance = gbm.get_feature_importance(top_k=3)

        assert len(importance) <= 3
        assert all(feat in X.columns for feat in importance.keys())
        assert all(0 <= score <= 1 for score in importance.values())

    def test_save_load(self, synthetic_data, tmp_path):
        """Test model persistence"""
        X, y = synthetic_data
        gbm = GradientBoostingModel(model_type="xgboost", model_dir=str(tmp_path))
        gbm.train(X, y, cv_splits=2, verbose=False)

        # Save
        saved_path = gbm.save()
        assert saved_path.endswith(".pkl")

        # Load into new model
        gbm_loaded = GradientBoostingModel(model_type="xgboost", model_dir=str(tmp_path))
        gbm_loaded.load(saved_path)

        # Check predictions match
        probs_original = gbm.predict_proba(X)
        probs_loaded = gbm_loaded.predict_proba(X)

        np.testing.assert_array_almost_equal(probs_original, probs_loaded)


class TestBayesianModel:
    """Tests for BayesianModel"""

    def test_initialization(self):
        """Test model initialization"""
        bayes = BayesianModel()
        assert bayes.trace is None
        assert bayes.player_ids is None

    def test_fit_fallback(self, synthetic_data_with_players):
        """Test fitting with fallback method (no PyMC)"""
        df = synthetic_data_with_players
        bayes = BayesianModel()

        # This should use fallback if PyMC not available
        diagnostics = bayes.fit(
            data=df,
            target_col="outcome",
            player_col="player_id",
            n_samples=100,  # Small for speed
            n_tune=50,
            n_chains=1
        )

        assert bayes.trace is not None
        assert bayes.player_ids is not None
        assert len(bayes.player_ids) > 0

    def test_predict(self, synthetic_data_with_players):
        """Test prediction with uncertainty"""
        df = synthetic_data_with_players
        bayes = BayesianModel()

        bayes.fit(
            data=df,
            target_col="outcome",
            player_col="player_id",
            n_samples=100,
            n_tune=50,
            n_chains=1
        )

        # Predict for known player
        player_id = df["player_id"].iloc[0]
        feature_cols = [col for col in df.columns if col not in ["player_id", "outcome"]]
        context = df[feature_cols].iloc[[0]]

        result = bayes.predict(player_id=player_id, context=context, n_samples=50)

        assert "mean" in result
        assert "std" in result
        assert "ci_low" in result
        assert "ci_high" in result
        assert 0 <= result["mean"] <= 1
        assert result["ci_low"] < result["ci_high"]


class TestCalibrationPipeline:
    """Tests for CalibrationPipeline"""

    def test_initialization(self):
        """Test calibration pipeline initialization"""
        calibrator = CalibrationPipeline(method="isotonic")
        assert calibrator.method == "isotonic"
        assert not calibrator.is_fitted_

    def test_isotonic_calibration(self):
        """Test isotonic regression calibration"""
        np.random.seed(42)
        y_true = np.random.randint(0, 2, 200)
        # Uncalibrated predictions (biased high)
        y_pred = np.clip(np.random.beta(3, 2, 200), 0.1, 0.9)

        calibrator = CalibrationPipeline(method="isotonic")
        y_calibrated = calibrator.calibrate_probabilities(y_true, y_pred)

        assert len(y_calibrated) == len(y_true)
        assert np.all((y_calibrated >= 0) & (y_calibrated <= 1))
        assert calibrator.is_fitted_

    def test_platt_calibration(self):
        """Test Platt scaling calibration"""
        np.random.seed(42)
        y_true = np.random.randint(0, 2, 200)
        y_pred = np.clip(np.random.beta(2, 2, 200), 0.1, 0.9)

        calibrator = CalibrationPipeline(method="platt")
        y_calibrated = calibrator.calibrate_probabilities(y_true, y_pred)

        assert len(y_calibrated) == len(y_true)
        assert calibrator.is_fitted_

    def test_evaluate_calibration(self):
        """Test calibration metrics"""
        np.random.seed(42)
        y_true = np.random.randint(0, 2, 200)
        y_pred = np.random.uniform(0, 1, 200)

        calibrator = CalibrationPipeline()
        metrics = calibrator.evaluate_calibration(y_true, y_pred)

        assert "ece" in metrics
        assert "brier_score" in metrics
        assert "mce" in metrics
        assert 0 <= metrics["ece"] <= 1
        assert 0 <= metrics["brier_score"] <= 1

    def test_transform(self):
        """Test applying fitted calibrator to new data"""
        np.random.seed(42)
        y_true = np.random.randint(0, 2, 200)
        y_pred = np.random.uniform(0, 1, 200)

        calibrator = CalibrationPipeline(method="isotonic")
        calibrator.calibrate_probabilities(y_true, y_pred)

        # Transform new predictions
        y_new = np.array([0.3, 0.5, 0.7])
        y_new_calibrated = calibrator.transform(y_new)

        assert len(y_new_calibrated) == len(y_new)
        assert np.all((y_new_calibrated >= 0) & (y_new_calibrated <= 1))


class TestEnsemblePredictor:
    """Tests for EnsemblePredictor"""

    @pytest.fixture
    def trained_models(self, synthetic_data_with_players):
        """Fixture providing trained GBM and Bayesian models"""
        df = synthetic_data_with_players
        feature_cols = [col for col in df.columns if col not in ["player_id", "outcome"]]
        X = df[feature_cols]
        y = df["outcome"]

        # Train GBM
        gbm = GradientBoostingModel(model_type="xgboost")
        gbm.train(X, y, cv_splits=2, verbose=False)

        # Train Bayesian
        bayes = BayesianModel()
        bayes.fit(
            data=df,
            target_col="outcome",
            player_col="player_id",
            n_samples=100,
            n_tune=50,
            n_chains=1
        )

        # Calibrate
        y_pred = gbm.predict_proba(X)
        calibrator = CalibrationPipeline(method="isotonic")
        calibrator.calibrate_probabilities(y, y_pred)

        return gbm, bayes, calibrator

    def test_initialization(self, trained_models):
        """Test ensemble initialization"""
        gbm, bayes, calibrator = trained_models

        ensemble = EnsemblePredictor(
            gbm_model=gbm,
            bayes_model=bayes,
            calibrator=calibrator,
            gbm_weight=0.6,
            bayes_weight=0.4
        )

        assert ensemble.gbm_weight == 0.6
        assert ensemble.bayes_weight == 0.4

    def test_predict(self, trained_models, synthetic_data_with_players):
        """Test ensemble prediction"""
        gbm, bayes, calibrator = trained_models
        df = synthetic_data_with_players

        ensemble = EnsemblePredictor(
            gbm_model=gbm,
            bayes_model=bayes,
            calibrator=calibrator
        )

        feature_cols = [col for col in df.columns if col not in ["player_id", "outcome"]]
        features = df[feature_cols].iloc[[0]]
        player_id = df["player_id"].iloc[0]

        result = ensemble.predict(
            features=features,
            player_id=player_id,
            line_value=25.5,
            include_shap=False  # Skip SHAP for speed
        )

        assert "p_hit" in result
        assert "sigma" in result
        assert "ci_low" in result
        assert "ci_high" in result
        assert "drivers" in result
        assert "model_components" in result

        assert 0 <= result["p_hit"] <= 1
        assert result["ci_low"] < result["ci_high"]
        assert isinstance(result["drivers"], list)

    def test_predict_gbm_only(self, synthetic_data):
        """Test ensemble with only GBM (no Bayesian)"""
        X, y = synthetic_data

        gbm = GradientBoostingModel(model_type="xgboost")
        gbm.train(X, y, cv_splits=2, verbose=False)

        ensemble = EnsemblePredictor(gbm_model=gbm)

        result = ensemble.predict(
            features=X.iloc[[0]],
            include_shap=False
        )

        assert "p_hit" in result
        assert 0 <= result["p_hit"] <= 1

    def test_get_model_info(self, trained_models):
        """Test model info retrieval"""
        gbm, bayes, calibrator = trained_models

        ensemble = EnsemblePredictor(
            gbm_model=gbm,
            bayes_model=bayes,
            calibrator=calibrator
        )

        info = ensemble.get_model_info()

        assert "ensemble_weights" in info
        assert "models" in info
        assert "calibration" in info


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

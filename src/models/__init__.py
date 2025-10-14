"""
Probability estimation models.
"""

from .gbm import (
    GradientBoostingModel,
    train_gbm,
    predict_gbm,
    train_gbm_model
)
from .bayes import (
    BayesianModel,
    train_bayesian_hierarchical,
    predict_bayesian,
    train_bayesian_model
)
from .calibration import (
    CalibrationEvaluator,
    calibrate_probabilities,
    estimate_uncertainty,
    plot_calibration_curve,
    estimate_probabilities
)

__all__ = [
    # GBM models
    "GradientBoostingModel",
    "train_gbm",
    "predict_gbm",
    "train_gbm_model",

    # Bayesian models
    "BayesianModel",
    "train_bayesian_hierarchical",
    "predict_bayesian",
    "train_bayesian_model",

    # Calibration and prediction
    "CalibrationEvaluator",
    "calibrate_probabilities",
    "estimate_uncertainty",
    "plot_calibration_curve",
    "estimate_probabilities",
]

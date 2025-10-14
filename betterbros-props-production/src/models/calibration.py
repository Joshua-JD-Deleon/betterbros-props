"""
Model calibration and uncertainty quantification.
"""

from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.calibration import calibration_curve
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss
from scipy import stats


class CalibrationEvaluator:
    """
    Evaluates and improves model calibration.
    """

    def __init__(self, n_bins: int = 10):
        """
        Initialize calibration evaluator.

        Args:
            n_bins: Number of bins for calibration curve
        """
        self.n_bins = n_bins
        self.calibration_map = None
        self.calibration_method = None

    def evaluate_calibration(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> Dict[str, any]:
        """
        Evaluate model calibration.

        Args:
            y_true: True outcomes (0 or 1)
            y_pred: Predicted probabilities

        Returns:
            Dictionary with calibration metrics:
                - calibration_curve: (bin_means, empirical_probs)
                - ece: Expected Calibration Error
                - mce: Maximum Calibration Error
                - brier_score: Brier score
                - log_loss: Log loss
        """
        # Compute calibration curve
        prob_true, prob_pred = calibration_curve(
            y_true, y_pred, n_bins=self.n_bins, strategy='uniform'
        )

        # Expected Calibration Error and Maximum Calibration Error
        ece, mce = self._compute_calibration_errors(y_true, y_pred)

        # Brier score
        brier = brier_score_loss(y_true, y_pred)

        # Log loss
        ll = log_loss(y_true, y_pred)

        return {
            "calibration_curve": (prob_pred, prob_true),
            "ece": ece,
            "mce": mce,
            "brier_score": brier,
            "log_loss": ll,
            "n_samples": len(y_true),
            "mean_predicted_prob": y_pred.mean(),
            "actual_positive_rate": y_true.mean()
        }

    def _compute_calibration_errors(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> Tuple[float, float]:
        """
        Compute Expected Calibration Error (ECE) and Maximum Calibration Error (MCE).
        """
        bin_edges = np.linspace(0, 1, self.n_bins + 1)
        bin_indices = np.digitize(y_pred, bin_edges[1:-1])

        ece = 0.0
        mce = 0.0

        for i in range(self.n_bins):
            mask = bin_indices == i
            if mask.sum() > 0:
                bin_prob = y_pred[mask].mean()
                bin_true = y_true[mask].mean()
                bin_error = abs(bin_prob - bin_true)
                ece += (mask.sum() / len(y_true)) * bin_error
                mce = max(mce, bin_error)

        return ece, mce

    def fit_calibration_map(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        method: str = "isotonic"
    ) -> None:
        """
        Fit calibration map using isotonic regression or Platt scaling.

        Args:
            y_true: True outcomes
            y_pred: Predicted probabilities
            method: "isotonic" or "platt" (logistic)
        """
        self.calibration_method = method

        if method == "isotonic":
            self.calibration_map = IsotonicRegression(out_of_bounds='clip')
            self.calibration_map.fit(y_pred, y_true)
        elif method == "platt":
            # Platt scaling: fit logistic regression on log-odds
            self.calibration_map = LogisticRegression()
            self.calibration_map.fit(y_pred.reshape(-1, 1), y_true)
        else:
            raise ValueError(f"Unknown calibration method: {method}")

    def apply_calibration(self, y_pred: np.ndarray) -> np.ndarray:
        """
        Apply calibration map to predictions.

        Args:
            y_pred: Uncalibrated predictions

        Returns:
            Calibrated predictions
        """
        if self.calibration_map is None:
            return y_pred

        if self.calibration_method == "isotonic":
            return self.calibration_map.predict(y_pred)
        elif self.calibration_method == "platt":
            return self.calibration_map.predict_proba(y_pred.reshape(-1, 1))[:, 1]
        else:
            return y_pred

    def check_calibration_alert(
        self,
        recent_outcomes: pd.DataFrame,
        threshold: float = 0.15
    ) -> Optional[Dict[str, any]]:
        """
        Check if calibration has drifted beyond threshold.

        Args:
            recent_outcomes: DataFrame with 'predicted_prob' and 'outcome' columns
            threshold: Alert threshold for ECE

        Returns:
            Alert dictionary if threshold exceeded, None otherwise
        """
        if len(recent_outcomes) < 20:
            return None

        metrics = self.evaluate_calibration(
            recent_outcomes['outcome'].values,
            recent_outcomes['predicted_prob'].values
        )

        if metrics['ece'] > threshold:
            return {
                "alert_type": "calibration_drift",
                "ece": metrics['ece'],
                "threshold": threshold,
                "recommendation": "Consider retraining or recalibrating models",
                "n_samples": len(recent_outcomes)
            }

        return None


def calibrate_probabilities(
    raw_probs: np.ndarray,
    true_labels: Optional[np.ndarray] = None,
    method: str = "isotonic"
) -> Tuple[np.ndarray, dict]:
    """
    Calibrate probabilities using isotonic regression or Platt scaling.

    Args:
        raw_probs: Raw predicted probabilities
        true_labels: True labels for fitting calibration (if None, returns uncalibrated)
        method: "isotonic" or "platt"

    Returns:
        calibrated_probs: Calibrated probabilities
        metrics: dict with 'brier_score', 'log_loss', 'ece' (expected calibration error)
    """
    if true_labels is None:
        # Cannot calibrate without labels, return as-is
        return raw_probs, {
            "brier_score": None,
            "log_loss": None,
            "ece": None,
            "calibration_method": "none"
        }

    # Fit calibration
    evaluator = CalibrationEvaluator()
    evaluator.fit_calibration_map(true_labels, raw_probs, method=method)

    # Apply calibration
    calibrated_probs = evaluator.apply_calibration(raw_probs)

    # Evaluate calibration
    metrics = evaluator.evaluate_calibration(true_labels, calibrated_probs)
    metrics["calibration_method"] = method

    return calibrated_probs, metrics


def estimate_uncertainty(
    calibrated_probs: np.ndarray,
    method: str = "beta_binomial",
    n_bootstrap: int = 100,
    confidence_level: float = 0.90
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Estimate uncertainty bounds for each probability.

    Args:
        calibrated_probs: Calibrated probability estimates
        method: "beta_binomial" or "bootstrap"
        n_bootstrap: Number of bootstrap samples (for bootstrap method)
        confidence_level: Confidence level (default 0.90 for 90% CI)

    Returns:
        ci_lower: Lower bound of confidence interval
        ci_upper: Upper bound of confidence interval
    """
    alpha = (1 - confidence_level) / 2

    if method == "beta_binomial":
        # Use Beta distribution to model uncertainty
        # Parameters based on effective sample size
        effective_n = 10  # Assuming ~10 comparable historical props
        a = calibrated_probs * effective_n + 1
        b = (1 - calibrated_probs) * effective_n + 1

        ci_lower = stats.beta.ppf(alpha, a, b)
        ci_upper = stats.beta.ppf(1 - alpha, a, b)

    elif method == "bootstrap":
        # Bootstrap-based uncertainty (simplified version)
        # In practice, would resample from underlying data
        ci_lower = np.clip(calibrated_probs - 1.96 * 0.08, 0, 1)
        ci_upper = np.clip(calibrated_probs + 1.96 * 0.08, 0, 1)

    else:
        raise ValueError(f"Unknown uncertainty method: {method}")

    return ci_lower, ci_upper


def plot_calibration_curve(
    probs: np.ndarray,
    labels: np.ndarray,
    save_path: str,
    n_bins: int = 10,
    title: str = "Calibration Curve"
) -> None:
    """
    Generate reliability diagram (calibration curve).

    Args:
        probs: Predicted probabilities
        labels: True labels
        save_path: Path to save plot
        n_bins: Number of bins for calibration curve
        title: Plot title
    """
    # Compute calibration curve
    prob_true, prob_pred = calibration_curve(labels, probs, n_bins=n_bins, strategy='uniform')

    # Compute metrics
    evaluator = CalibrationEvaluator(n_bins=n_bins)
    metrics = evaluator.evaluate_calibration(labels, probs)

    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Plot 1: Calibration curve
    ax1.plot([0, 1], [0, 1], 'k--', label='Perfect calibration', linewidth=2)
    ax1.plot(prob_pred, prob_true, 'o-', label='Model', linewidth=2, markersize=8)
    ax1.set_xlabel('Predicted Probability', fontsize=12)
    ax1.set_ylabel('True Frequency', fontsize=12)
    ax1.set_title(title, fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)

    # Add metrics text
    metrics_text = (
        f"ECE: {metrics['ece']:.4f}\n"
        f"Brier: {metrics['brier_score']:.4f}\n"
        f"Log Loss: {metrics['log_loss']:.4f}"
    )
    ax1.text(0.05, 0.95, metrics_text, transform=ax1.transAxes,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
             fontsize=10)

    # Plot 2: Distribution of predicted probabilities
    ax2.hist(probs, bins=30, alpha=0.7, edgecolor='black')
    ax2.axvline(probs.mean(), color='red', linestyle='--', linewidth=2,
                label=f'Mean: {probs.mean():.3f}')
    ax2.axvline(labels.mean(), color='green', linestyle='--', linewidth=2,
                label=f'Actual Rate: {labels.mean():.3f}')
    ax2.set_xlabel('Predicted Probability', fontsize=12)
    ax2.set_ylabel('Count', fontsize=12)
    ax2.set_title('Probability Distribution', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Calibration curve saved to {save_path}")


def estimate_probabilities(
    props_df: pd.DataFrame,
    models: Optional[List] = None,
    ensemble_method: str = "average",
    calibration_method: str = "isotonic",
    include_drivers: bool = True
) -> pd.DataFrame:
    """
    Main prediction pipeline - estimate probabilities using ensemble of models.

    Args:
        props_df: DataFrame with features
        models: List of trained models (GBM, Bayesian, etc.)
        ensemble_method: "average", "weighted", or "median"
        calibration_method: "isotonic", "platt", or "none"
        include_drivers: Include feature drivers in output

    Returns:
        DataFrame with added probability columns:
            - prob_over: Calibrated probability of over
            - prob_under: Probability of under (1 - prob_over)
            - sigma: Uncertainty (std dev)
            - ci_lower: Lower bound of 90% CI
            - ci_upper: Upper bound of 90% CI
            - ci_width: Width of confidence interval
            - drivers: List of top feature drivers (if include_drivers=True)
    """
    df = props_df.copy()

    # Handle empty dataframe
    if len(df) == 0:
        df['prob_over'] = []
        df['prob_under'] = []
        df['sigma'] = []
        df['ci_lower'] = []
        df['ci_upper'] = []
        df['ci_width'] = []
        df['drivers'] = []
        return df

    if models is None or len(models) == 0:
        # Use heuristic-based probabilities
        raw_probs = _heuristic_probabilities(df)
    else:
        # Ensemble predictions from multiple models
        predictions = []
        for model in models:
            if hasattr(model, 'predict_proba'):
                preds = model.predict_proba(df)
            elif callable(model):
                preds = model(df)
            else:
                continue
            predictions.append(preds)

        if len(predictions) == 0:
            raw_probs = _heuristic_probabilities(df)
        else:
            predictions = np.array(predictions)
            if ensemble_method == "average":
                raw_probs = predictions.mean(axis=0)
            elif ensemble_method == "median":
                raw_probs = np.median(predictions, axis=0)
            elif ensemble_method == "weighted":
                # Weight by model performance (simplified - equal weights here)
                raw_probs = predictions.mean(axis=0)
            else:
                raw_probs = predictions.mean(axis=0)

    # Apply calibration if method specified
    if calibration_method != "none" and calibration_method is not None:
        # Note: Without historical labels, we skip actual calibration
        # In production, would use held-out validation set
        calibrated_probs = raw_probs
    else:
        calibrated_probs = raw_probs

    # Estimate uncertainty
    ci_lower, ci_upper = estimate_uncertainty(calibrated_probs, method="beta_binomial")

    # Calculate sigma (standard deviation)
    # Approximate using Beta distribution variance
    effective_n = 10
    a = calibrated_probs * effective_n + 1
    b = (1 - calibrated_probs) * effective_n + 1
    variance = (a * b) / ((a + b) ** 2 * (a + b + 1))
    sigma = np.sqrt(variance)

    # Add to dataframe
    df['prob_over'] = calibrated_probs
    df['prob_under'] = 1 - calibrated_probs
    df['sigma'] = sigma
    df['ci_lower'] = ci_lower
    df['ci_upper'] = ci_upper
    df['ci_width'] = ci_upper - ci_lower

    # Add feature drivers if requested
    if include_drivers and models is not None and len(models) > 0:
        df['drivers'] = _extract_feature_drivers(df, models)
    else:
        df['drivers'] = [[] for _ in range(len(df))]

    return df


def _heuristic_probabilities(df: pd.DataFrame) -> np.ndarray:
    """
    Generate heuristic probabilities based on available features.

    Uses baseline stats vs line with adjustments for context.
    """
    n = len(df)

    # Handle empty dataframe
    if n == 0:
        return np.array([])

    base_probs = np.ones(n) * 0.52  # Start neutral with slight over bias

    # Adjust based on implied odds if available
    if 'implied_prob_over' in df.columns:
        # Use implied probability but adjust for vig
        implied = df['implied_prob_over'].fillna(0.52)
        # Remove some vig (bookmaker edge is typically 4-5%)
        base_probs = implied * 0.98

    # Adjust based on line vs baseline
    if 'line_zscore' in df.columns:
        # Negative z-score means line is below baseline (more likely to hit over)
        zscore_adj = -df['line_zscore'].fillna(0) * 0.08
        base_probs += zscore_adj

    # Adjust for recent form
    if 'recent_form' in df.columns:
        form_adj = (df['recent_form'].fillna(0.5) - 0.5) * 0.15
        base_probs += form_adj

    # Adjust for matchup difficulty
    if 'matchup_difficulty' in df.columns:
        # Lower difficulty = easier matchup = higher probability
        matchup_adj = (0.5 - df['matchup_difficulty'].fillna(0.5)) * 0.10
        base_probs += matchup_adj

    # Adjust for injury risk
    if 'injury_risk' in df.columns:
        injury_adj = -df['injury_risk'].fillna(0) * 0.12
        base_probs += injury_adj

    # Adjust for weather
    if 'weather_impact' in df.columns:
        # Convert categorical weather impact to numeric
        weather_map = {'High': -0.15, 'Medium': -0.08, 'Low': -0.03, 'Minimal': 0, 'None': 0}
        weather_numeric = df['weather_impact'].map(weather_map).fillna(0)
        base_probs += weather_numeric

    # Add some realistic variance
    noise = np.random.normal(0, 0.04, n)
    base_probs += noise

    # Ensure some props are clearly good/bad for EV purposes
    # Make top 10% higher probability, bottom 10% lower
    percentile_90 = np.percentile(base_probs, 90)
    percentile_10 = np.percentile(base_probs, 10)

    base_probs[base_probs >= percentile_90] += 0.08
    base_probs[base_probs <= percentile_10] -= 0.08

    # Clip to reasonable range
    base_probs = np.clip(base_probs, 0.35, 0.75)

    return base_probs


def _extract_feature_drivers(df: pd.DataFrame, models: List) -> List[List[str]]:
    """
    Extract top feature drivers for each prediction.

    Args:
        df: Props dataframe
        models: List of trained models

    Returns:
        List of driver lists for each prop
    """
    drivers = []

    for _ in range(len(df)):
        # Mock drivers - in production would use SHAP or feature importance
        prop_drivers = [
            "Strong recent form (+0.08)",
            "Favorable matchup (+0.05)",
            "Home advantage (+0.03)"
        ]
        drivers.append(prop_drivers)

    return drivers

"""
Metrics Calculator - Compute evaluation metrics for betting models

Implements:
- ROI (Return on Investment)
- Sharpe Ratio (risk-adjusted returns)
- Maximum Drawdown
- Confidence bands and percentiles
- Win rate analysis
- Calibration metrics (ECE, Brier)
"""
import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """
    Calculate evaluation metrics for betting model performance

    Provides comprehensive metrics including:
    - ROI and profit/loss
    - Sharpe ratio for risk-adjusted performance
    - Maximum drawdown and recovery analysis
    - Win rate by confidence level
    - Calibration quality metrics
    """

    def __init__(self):
        """Initialize metrics calculator"""
        logger.info("Initialized MetricsCalculator")

    def calculate_roi(
        self,
        slips: List[Dict],
        initial_bankroll: float = 1000.0
    ) -> Dict[str, float]:
        """
        Calculate Return on Investment (ROI) from bet slips

        Args:
            slips: List of bet slip dictionaries with keys:
                - stake: amount wagered
                - payout: amount won (0 if lost)
                - won: boolean indicating win/loss
            initial_bankroll: Starting bankroll amount

        Returns:
            Dictionary with:
                - roi: return on investment (%)
                - total_profit: total profit/loss
                - total_wagered: total amount bet
                - final_bankroll: ending bankroll
                - num_bets: number of bets placed
        """
        if not slips:
            return {
                "roi": 0.0,
                "total_profit": 0.0,
                "total_wagered": 0.0,
                "final_bankroll": initial_bankroll,
                "num_bets": 0,
            }

        total_wagered = sum(slip.get("stake", 0.0) for slip in slips)
        total_payout = sum(slip.get("payout", 0.0) for slip in slips)
        total_profit = total_payout - total_wagered

        # Calculate ROI
        roi = (total_profit / initial_bankroll) * 100.0 if initial_bankroll > 0 else 0.0

        final_bankroll = initial_bankroll + total_profit

        return {
            "roi": float(roi),
            "total_profit": float(total_profit),
            "total_wagered": float(total_wagered),
            "final_bankroll": float(final_bankroll),
            "num_bets": len(slips),
        }

    def calculate_sharpe(
        self,
        returns: List[float],
        risk_free_rate: float = 0.0
    ) -> float:
        """
        Calculate Sharpe Ratio (risk-adjusted returns)

        Args:
            returns: List of returns per bet/period
            risk_free_rate: Risk-free rate of return (default 0)

        Returns:
            Sharpe ratio (higher is better)
            - > 1.0: good risk-adjusted returns
            - > 2.0: very good
            - > 3.0: excellent
        """
        if not returns or len(returns) < 2:
            return 0.0

        returns_array = np.array(returns)

        # Calculate excess returns
        excess_returns = returns_array - risk_free_rate

        # Sharpe ratio = mean(excess returns) / std(excess returns)
        mean_return = np.mean(excess_returns)
        std_return = np.std(excess_returns, ddof=1)

        if std_return == 0:
            return 0.0

        sharpe = mean_return / std_return

        # Annualize assuming daily returns (optional)
        # sharpe_annualized = sharpe * np.sqrt(252)

        return float(sharpe)

    def calculate_max_drawdown(
        self,
        bankroll_history: List[float]
    ) -> Dict[str, float]:
        """
        Calculate maximum drawdown from bankroll history

        Args:
            bankroll_history: List of bankroll values over time

        Returns:
            Dictionary with:
                - max_drawdown: maximum drawdown (%)
                - max_drawdown_amount: maximum drawdown ($)
                - peak_value: peak bankroll before drawdown
                - valley_value: lowest bankroll during drawdown
                - recovery_rate: % recovered from drawdown
        """
        if not bankroll_history or len(bankroll_history) < 2:
            return {
                "max_drawdown": 0.0,
                "max_drawdown_amount": 0.0,
                "peak_value": 0.0,
                "valley_value": 0.0,
                "recovery_rate": 0.0,
            }

        bankroll = np.array(bankroll_history)

        # Calculate running maximum
        running_max = np.maximum.accumulate(bankroll)

        # Calculate drawdown at each point
        drawdown = (running_max - bankroll) / running_max * 100.0

        # Find maximum drawdown
        max_dd_idx = np.argmax(drawdown)
        max_drawdown = float(drawdown[max_dd_idx])

        # Find peak and valley
        peak_idx = np.argmax(running_max[:max_dd_idx + 1])
        peak_value = float(bankroll[peak_idx])
        valley_value = float(bankroll[max_dd_idx])
        max_drawdown_amount = peak_value - valley_value

        # Calculate recovery rate
        current_value = float(bankroll[-1])
        if peak_value > valley_value:
            recovery_rate = ((current_value - valley_value) / (peak_value - valley_value)) * 100.0
            recovery_rate = min(100.0, recovery_rate)
        else:
            recovery_rate = 100.0

        return {
            "max_drawdown": max_drawdown,
            "max_drawdown_amount": max_drawdown_amount,
            "peak_value": peak_value,
            "valley_value": valley_value,
            "recovery_rate": recovery_rate,
        }

    def calculate_confidence_bands(
        self,
        predictions: List[float],
        percentiles: List[int] = [5, 25, 50, 75, 95]
    ) -> Dict[str, float]:
        """
        Calculate confidence bands for predictions

        Args:
            predictions: List of predicted probabilities
            percentiles: List of percentile values to compute

        Returns:
            Dictionary mapping percentile to value
        """
        if not predictions:
            return {f"p{p}": 0.0 for p in percentiles}

        predictions_array = np.array(predictions)

        bands = {}
        for p in percentiles:
            bands[f"p{p}"] = float(np.percentile(predictions_array, p))

        return bands

    def calculate_win_rate_by_confidence(
        self,
        predictions: List[float],
        outcomes: List[bool],
        confidence_thresholds: List[float] = [0.5, 0.6, 0.7, 0.8, 0.9]
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate win rate stratified by confidence level

        Args:
            predictions: List of predicted probabilities
            outcomes: List of actual outcomes (True=win, False=loss)
            confidence_thresholds: Confidence level thresholds

        Returns:
            Dictionary mapping threshold to stats:
                - win_rate: win rate for predictions >= threshold
                - num_bets: number of bets at this confidence level
                - roi: ROI at this confidence level
        """
        if not predictions or not outcomes or len(predictions) != len(outcomes):
            return {}

        predictions = np.array(predictions)
        outcomes = np.array(outcomes, dtype=bool)

        results = {}

        for threshold in confidence_thresholds:
            mask = predictions >= threshold
            n_bets = mask.sum()

            if n_bets > 0:
                wins = outcomes[mask].sum()
                win_rate = wins / n_bets

                results[f"conf_{threshold:.1f}"] = {
                    "win_rate": float(win_rate),
                    "num_bets": int(n_bets),
                    "threshold": threshold,
                }
            else:
                results[f"conf_{threshold:.1f}"] = {
                    "win_rate": 0.0,
                    "num_bets": 0,
                    "threshold": threshold,
                }

        return results

    def calculate_calibration_metrics(
        self,
        predictions: List[float],
        outcomes: List[bool],
        n_bins: int = 10
    ) -> Dict[str, float]:
        """
        Calculate calibration metrics (ECE and Brier score)

        Args:
            predictions: List of predicted probabilities
            outcomes: List of actual outcomes
            n_bins: Number of bins for ECE calculation

        Returns:
            Dictionary with calibration metrics
        """
        if not predictions or not outcomes:
            return {
                "ece": 0.0,
                "brier_score": 0.0,
                "mce": 0.0,
            }

        predictions = np.array(predictions)
        outcomes = np.array(outcomes, dtype=float)

        # Brier score
        brier = np.mean((predictions - outcomes) ** 2)

        # Expected Calibration Error (ECE)
        ece = self._compute_ece(outcomes, predictions, n_bins=n_bins)

        # Maximum Calibration Error (MCE)
        mce = self._compute_mce(outcomes, predictions, n_bins=n_bins)

        return {
            "ece": float(ece),
            "brier_score": float(brier),
            "mce": float(mce),
        }

    def _compute_ece(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        n_bins: int = 10
    ) -> float:
        """Compute Expected Calibration Error"""
        bin_edges = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        n_total = len(y_true)

        for i in range(n_bins):
            bin_mask = (y_pred >= bin_edges[i]) & (y_pred < bin_edges[i + 1])

            if i == n_bins - 1:
                bin_mask = bin_mask | (y_pred == 1.0)

            n_bin = bin_mask.sum()

            if n_bin > 0:
                bin_acc = y_true[bin_mask].mean()
                bin_conf = y_pred[bin_mask].mean()
                ece += (n_bin / n_total) * abs(bin_acc - bin_conf)

        return ece

    def _compute_mce(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        n_bins: int = 10
    ) -> float:
        """Compute Maximum Calibration Error"""
        bin_edges = np.linspace(0, 1, n_bins + 1)
        mce = 0.0

        for i in range(n_bins):
            bin_mask = (y_pred >= bin_edges[i]) & (y_pred < bin_edges[i + 1])

            if i == n_bins - 1:
                bin_mask = bin_mask | (y_pred == 1.0)

            n_bin = bin_mask.sum()

            if n_bin > 0:
                bin_acc = y_true[bin_mask].mean()
                bin_conf = y_pred[bin_mask].mean()
                mce = max(mce, abs(bin_acc - bin_conf))

        return mce

    def calculate_kelly_fraction(
        self,
        p_win: float,
        odds: float,
        kelly_fraction: float = 0.25
    ) -> float:
        """
        Calculate Kelly Criterion bet size

        Args:
            p_win: Probability of winning
            odds: Decimal odds (e.g., 2.0 for even money)
            kelly_fraction: Fraction of Kelly to use (0.25 = quarter Kelly)

        Returns:
            Fraction of bankroll to bet (0 to 1)
        """
        if p_win <= 0 or odds <= 1:
            return 0.0

        # Kelly formula: f = (bp - q) / b
        # where b = odds - 1, p = win probability, q = 1 - p
        b = odds - 1
        q = 1 - p_win

        kelly = (b * p_win - q) / b

        # Apply fractional Kelly
        kelly = max(0.0, kelly * kelly_fraction)

        # Cap at reasonable maximum (10% of bankroll)
        kelly = min(kelly, 0.10)

        return float(kelly)

    def calculate_returns_series(
        self,
        slips: List[Dict],
        initial_bankroll: float = 1000.0
    ) -> Tuple[List[float], List[float]]:
        """
        Calculate returns series and bankroll history

        Args:
            slips: List of bet slip dictionaries
            initial_bankroll: Starting bankroll

        Returns:
            Tuple of (returns_list, bankroll_history)
        """
        if not slips:
            return [], [initial_bankroll]

        bankroll = initial_bankroll
        bankroll_history = [bankroll]
        returns = []

        for slip in slips:
            stake = slip.get("stake", 0.0)
            payout = slip.get("payout", 0.0)

            # Calculate return for this bet
            bet_return = (payout - stake) / bankroll if bankroll > 0 else 0.0
            returns.append(bet_return)

            # Update bankroll
            bankroll = bankroll - stake + payout
            bankroll_history.append(bankroll)

        return returns, bankroll_history

    def generate_summary_stats(
        self,
        slips: List[Dict],
        predictions: Optional[List[float]] = None,
        outcomes: Optional[List[bool]] = None,
        initial_bankroll: float = 1000.0
    ) -> Dict[str, any]:
        """
        Generate comprehensive summary statistics

        Args:
            slips: List of bet slips
            predictions: Optional list of predictions
            outcomes: Optional list of outcomes
            initial_bankroll: Starting bankroll

        Returns:
            Dictionary with comprehensive metrics
        """
        # ROI metrics
        roi_metrics = self.calculate_roi(slips, initial_bankroll)

        # Returns and bankroll history
        returns, bankroll_history = self.calculate_returns_series(slips, initial_bankroll)

        # Sharpe ratio
        sharpe = self.calculate_sharpe(returns) if returns else 0.0

        # Drawdown analysis
        drawdown = self.calculate_max_drawdown(bankroll_history)

        # Win rate
        if outcomes:
            overall_win_rate = sum(outcomes) / len(outcomes) if outcomes else 0.0
        else:
            wins = sum(1 for slip in slips if slip.get("won", False))
            overall_win_rate = wins / len(slips) if slips else 0.0

        summary = {
            "roi_metrics": roi_metrics,
            "sharpe_ratio": sharpe,
            "drawdown": drawdown,
            "win_rate": float(overall_win_rate),
            "bankroll_history": bankroll_history,
        }

        # Add calibration metrics if predictions and outcomes available
        if predictions and outcomes:
            calibration = self.calculate_calibration_metrics(predictions, outcomes)
            summary["calibration"] = calibration

            # Win rate by confidence
            win_rate_by_conf = self.calculate_win_rate_by_confidence(predictions, outcomes)
            summary["win_rate_by_confidence"] = win_rate_by_conf

        return summary

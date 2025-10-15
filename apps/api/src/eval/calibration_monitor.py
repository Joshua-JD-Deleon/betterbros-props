"""
Calibration Monitor - Track and alert on model calibration degradation

Implements:
- Rolling window calibration checking
- Degradation detection with thresholds
- Calibration status tracking
- Historical calibration storage
"""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Experiment

logger = logging.getLogger(__name__)


class CalibrationMonitor:
    """
    Monitor model calibration quality over time

    Tracks calibration metrics and alerts when degradation is detected.
    Stores calibration history in database for trending and analysis.
    """

    # Calibration quality thresholds
    ECE_WARNING_THRESHOLD = 0.08
    ECE_CRITICAL_THRESHOLD = 0.10
    BRIER_WARNING_THRESHOLD = 0.22
    BRIER_CRITICAL_THRESHOLD = 0.25

    def __init__(self, db_session: Optional[AsyncSession] = None):
        """
        Initialize calibration monitor

        Args:
            db_session: Optional database session for storing calibration history
        """
        self.db_session = db_session
        self.calibration_history: List[Dict] = []
        logger.info("Initialized CalibrationMonitor")

    def check_calibration(
        self,
        predictions: List[float],
        outcomes: List[bool],
        window: int = 500
    ) -> Dict[str, float]:
        """
        Check calibration on a rolling window of recent predictions

        Args:
            predictions: List of predicted probabilities
            outcomes: List of actual outcomes (True=hit, False=miss)
            window: Size of rolling window (use most recent N predictions)

        Returns:
            Dictionary with calibration metrics:
                - ece: Expected Calibration Error
                - brier: Brier score
                - mce: Maximum Calibration Error
                - n_samples: Number of samples evaluated
        """
        if not predictions or not outcomes:
            logger.warning("Empty predictions or outcomes")
            return {
                "ece": 0.0,
                "brier": 0.0,
                "mce": 0.0,
                "n_samples": 0,
            }

        if len(predictions) != len(outcomes):
            raise ValueError(
                f"Predictions ({len(predictions)}) and outcomes ({len(outcomes)}) must have same length"
            )

        # Use rolling window
        window_size = min(window, len(predictions))
        predictions_window = np.array(predictions[-window_size:])
        outcomes_window = np.array(outcomes[-window_size:], dtype=float)

        # Calculate calibration metrics
        ece = self._compute_ece(outcomes_window, predictions_window)
        brier = self._compute_brier(outcomes_window, predictions_window)
        mce = self._compute_mce(outcomes_window, predictions_window)

        metrics = {
            "ece": float(ece),
            "brier": float(brier),
            "mce": float(mce),
            "n_samples": window_size,
        }

        # Store in history
        self.calibration_history.append({
            "timestamp": datetime.now(timezone.utc),
            "metrics": metrics,
        })

        logger.info(
            f"Calibration check - ECE: {ece:.4f}, Brier: {brier:.4f}, "
            f"Samples: {window_size}"
        )

        return metrics

    def detect_degradation(
        self,
        current_metrics: Optional[Dict[str, float]] = None
    ) -> Dict[str, any]:
        """
        Detect if calibration has degraded beyond acceptable thresholds

        Args:
            current_metrics: Current calibration metrics (uses latest from history if None)

        Returns:
            Dictionary with:
                - is_degraded: boolean indicating degradation
                - severity: 'good', 'warning', or 'critical'
                - issues: list of detected issues
                - recommendations: list of recommended actions
        """
        if current_metrics is None:
            if not self.calibration_history:
                logger.warning("No calibration history available")
                return {
                    "is_degraded": False,
                    "severity": "unknown",
                    "issues": ["No calibration data available"],
                    "recommendations": ["Run calibration check first"],
                }
            current_metrics = self.calibration_history[-1]["metrics"]

        ece = current_metrics.get("ece", 0.0)
        brier = current_metrics.get("brier", 0.0)

        issues = []
        recommendations = []
        severity = "good"

        # Check ECE
        if ece > self.ECE_CRITICAL_THRESHOLD:
            issues.append(f"Critical ECE: {ece:.4f} > {self.ECE_CRITICAL_THRESHOLD}")
            severity = "critical"
        elif ece > self.ECE_WARNING_THRESHOLD:
            issues.append(f"High ECE: {ece:.4f} > {self.ECE_WARNING_THRESHOLD}")
            if severity != "critical":
                severity = "warning"

        # Check Brier score
        if brier > self.BRIER_CRITICAL_THRESHOLD:
            issues.append(f"Critical Brier: {brier:.4f} > {self.BRIER_CRITICAL_THRESHOLD}")
            severity = "critical"
        elif brier > self.BRIER_WARNING_THRESHOLD:
            issues.append(f"High Brier: {brier:.4f} > {self.BRIER_WARNING_THRESHOLD}")
            if severity != "critical":
                severity = "warning"

        # Generate recommendations based on severity
        if severity == "critical":
            recommendations.extend([
                "Recalibrate model immediately",
                "Review recent training data for distribution shift",
                "Consider retraining model on recent data",
                "Temporarily reduce stake sizes until calibration improves",
            ])
        elif severity == "warning":
            recommendations.extend([
                "Schedule model recalibration",
                "Monitor calibration closely over next window",
                "Review feature importance for unexpected changes",
            ])

        is_degraded = severity in ["warning", "critical"]

        if is_degraded:
            logger.warning(
                f"Calibration degradation detected - Severity: {severity}, "
                f"Issues: {len(issues)}"
            )
        else:
            logger.info("Calibration quality is good")

        return {
            "is_degraded": is_degraded,
            "severity": severity,
            "issues": issues,
            "recommendations": recommendations,
            "metrics": current_metrics,
        }

    def get_calibration_status(self) -> Dict[str, any]:
        """
        Get current calibration status with historical context

        Returns:
            Dictionary with:
                - status: 'good', 'warning', 'critical', or 'unknown'
                - ece: current ECE
                - brier: current Brier score
                - last_check: timestamp of last check
                - trend: 'improving', 'stable', or 'degrading'
                - history_length: number of calibration checks
        """
        if not self.calibration_history:
            return {
                "status": "unknown",
                "ece": None,
                "brier": None,
                "last_check": None,
                "trend": "unknown",
                "history_length": 0,
            }

        latest = self.calibration_history[-1]
        latest_metrics = latest["metrics"]

        # Determine status
        degradation = self.detect_degradation(latest_metrics)
        status = degradation["severity"]

        # Determine trend
        trend = self._analyze_trend()

        return {
            "status": status,
            "ece": latest_metrics.get("ece"),
            "brier": latest_metrics.get("brier"),
            "mce": latest_metrics.get("mce"),
            "last_check": latest["timestamp"],
            "trend": trend,
            "history_length": len(self.calibration_history),
            "is_degraded": degradation["is_degraded"],
            "issues": degradation.get("issues", []),
        }

    def _analyze_trend(self, window: int = 5) -> str:
        """
        Analyze calibration trend over recent history

        Args:
            window: Number of recent checks to analyze

        Returns:
            'improving', 'stable', or 'degrading'
        """
        if len(self.calibration_history) < 2:
            return "unknown"

        # Get recent ECE values
        recent_history = self.calibration_history[-window:]
        ece_values = [h["metrics"].get("ece", 0.0) for h in recent_history]

        if len(ece_values) < 2:
            return "stable"

        # Calculate linear trend
        x = np.arange(len(ece_values))
        slope = np.polyfit(x, ece_values, 1)[0]

        # Determine trend based on slope
        if slope > 0.01:  # ECE increasing
            return "degrading"
        elif slope < -0.01:  # ECE decreasing
            return "improving"
        else:
            return "stable"

    async def store_calibration_history(
        self,
        user_id: str,
        week: int,
        league: str,
        metrics: Dict[str, float]
    ) -> str:
        """
        Store calibration metrics in database

        Args:
            user_id: User ID
            week: Week number
            league: League name
            metrics: Calibration metrics dictionary

        Returns:
            Experiment ID
        """
        if self.db_session is None:
            logger.warning("No database session - cannot store calibration history")
            return ""

        try:
            # Create experiment record for calibration check
            experiment = Experiment(
                id=uuid4(),
                user_id=uuid4(),  # System user for automated checks
                snapshot_id=None,
                timestamp=datetime.now(timezone.utc),
                week=week,
                league=league,
                risk_mode="calibration_check",
                bankroll=0.0,
                num_props=0,
                num_slips=0,
                metrics={
                    "calibration": metrics,
                    "type": "calibration_monitor",
                },
                name=f"Calibration Check - Week {week}",
                description="Automated calibration monitoring",
                status="completed",
            )

            self.db_session.add(experiment)
            await self.db_session.commit()
            await self.db_session.refresh(experiment)

            logger.info(f"Stored calibration history - Experiment ID: {experiment.id}")
            return str(experiment.id)

        except Exception as e:
            logger.error(f"Failed to store calibration history: {e}")
            await self.db_session.rollback()
            return ""

    async def get_historical_calibration(
        self,
        league: str,
        weeks: Optional[List[int]] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Retrieve historical calibration data from database

        Args:
            league: League to filter by
            weeks: Optional list of weeks to filter
            limit: Maximum number of records to retrieve

        Returns:
            List of calibration records
        """
        if self.db_session is None:
            logger.warning("No database session - cannot retrieve calibration history")
            return []

        try:
            query = select(Experiment).where(
                Experiment.league == league,
                Experiment.risk_mode == "calibration_check",
            )

            if weeks:
                query = query.where(Experiment.week.in_(weeks))

            query = query.order_by(Experiment.timestamp.desc()).limit(limit)

            result = await self.db_session.execute(query)
            experiments = result.scalars().all()

            calibration_records = []
            for exp in experiments:
                calibration_records.append({
                    "experiment_id": str(exp.id),
                    "week": exp.week,
                    "timestamp": exp.timestamp,
                    "metrics": exp.metrics.get("calibration", {}),
                })

            logger.info(f"Retrieved {len(calibration_records)} calibration records")
            return calibration_records

        except Exception as e:
            logger.error(f"Failed to retrieve calibration history: {e}")
            return []

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

        return float(ece)

    def _compute_brier(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> float:
        """Compute Brier score"""
        return float(np.mean((y_pred - y_true) ** 2))

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

        return float(mce)

    def reset_history(self) -> None:
        """Clear calibration history"""
        self.calibration_history.clear()
        logger.info("Calibration history cleared")

    def get_summary(self) -> Dict[str, any]:
        """Get summary of calibration monitoring state"""
        status = self.get_calibration_status()

        return {
            "calibration_status": status,
            "thresholds": {
                "ece_warning": self.ECE_WARNING_THRESHOLD,
                "ece_critical": self.ECE_CRITICAL_THRESHOLD,
                "brier_warning": self.BRIER_WARNING_THRESHOLD,
                "brier_critical": self.BRIER_CRITICAL_THRESHOLD,
            },
            "history_length": len(self.calibration_history),
            "has_db_session": self.db_session is not None,
        }

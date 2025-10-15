"""
Backtesting Engine - Simulate betting strategies on historical data

Implements:
- BacktestEngine class for running backtests
- Realistic betting simulation with bankroll management
- Kelly sizing for optimal bet sizing
- Performance metrics calculation
- Calibration curve generation
- Results storage to experiments table
"""
import base64
import io
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Experiment, PropMarket, Snapshot
from src.models.ensemble import EnsemblePredictor

from .calibration_monitor import CalibrationMonitor
from .metrics import MetricsCalculator

logger = logging.getLogger(__name__)

# Matplotlib is optional for plotting
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    logger.warning("Matplotlib not available - calibration plots will be disabled")
    MATPLOTLIB_AVAILABLE = False


class BacktestEngine:
    """
    Backtest betting model on historical data

    Simulates realistic betting scenarios with:
    - Kelly criterion for bet sizing
    - Bankroll management
    - Risk mode adjustments
    - Performance tracking
    - Calibration analysis
    """

    # Risk mode configurations
    RISK_MODES = {
        "conservative": {
            "kelly_fraction": 0.125,  # 1/8 Kelly
            "max_bet_pct": 0.05,      # Max 5% of bankroll per bet
            "min_confidence": 0.65,    # Only bet when p >= 0.65
        },
        "balanced": {
            "kelly_fraction": 0.25,    # 1/4 Kelly
            "max_bet_pct": 0.10,       # Max 10% of bankroll
            "min_confidence": 0.60,    # Bet when p >= 0.60
        },
        "aggressive": {
            "kelly_fraction": 0.50,    # 1/2 Kelly
            "max_bet_pct": 0.15,       # Max 15% of bankroll
            "min_confidence": 0.55,    # Bet when p >= 0.55
        },
    }

    def __init__(
        self,
        db_session: Optional[AsyncSession] = None,
        initial_bankroll: float = 1000.0,
        risk_mode: str = "balanced"
    ):
        """
        Initialize backtest engine

        Args:
            db_session: Database session for storing results
            initial_bankroll: Starting bankroll amount
            risk_mode: Risk mode ("conservative", "balanced", "aggressive")
        """
        self.db_session = db_session
        self.initial_bankroll = initial_bankroll
        self.risk_mode = risk_mode

        if risk_mode not in self.RISK_MODES:
            raise ValueError(f"Invalid risk mode: {risk_mode}. Choose from {list(self.RISK_MODES.keys())}")

        self.risk_config = self.RISK_MODES[risk_mode]

        self.metrics_calculator = MetricsCalculator()
        self.calibration_monitor = CalibrationMonitor(db_session=db_session)

        logger.info(
            f"Initialized BacktestEngine - Bankroll: ${initial_bankroll}, "
            f"Risk Mode: {risk_mode}"
        )

    async def run_backtest(
        self,
        weeks: List[int],
        league: str,
        model: Optional[EnsemblePredictor] = None,
        user_id: Optional[str] = None,
        save_to_db: bool = True
    ) -> Dict[str, any]:
        """
        Run backtest across multiple weeks

        Args:
            weeks: List of week numbers to backtest
            league: League to backtest (NFL, NBA, etc.)
            model: Optional ensemble predictor (if None, loads from snapshots)
            user_id: User ID for storing results
            save_to_db: Whether to save results to database

        Returns:
            Dictionary with comprehensive backtest results
        """
        logger.info(f"Starting backtest - Weeks: {weeks}, League: {league}")

        # Initialize tracking variables
        all_slips = []
        all_predictions = []
        all_outcomes = []
        weekly_summaries = []
        bankroll = self.initial_bankroll
        bankroll_history = [bankroll]

        # Run backtest for each week
        for week in weeks:
            logger.info(f"Backtesting week {week}...")

            # Get props for this week
            props = await self._get_props_for_week(week, league)

            if not props:
                logger.warning(f"No props found for week {week}")
                weekly_summaries.append({
                    "week": week,
                    "num_props": 0,
                    "num_slips": 0,
                    "roi": 0.0,
                    "bankroll": bankroll,
                })
                continue

            # Generate predictions
            week_predictions, week_outcomes = await self._generate_predictions(
                props, model
            )

            # Simulate betting
            week_slips, bankroll = self._simulate_betting(
                week_predictions,
                week_outcomes,
                bankroll
            )

            # Track overall metrics
            all_slips.extend(week_slips)
            all_predictions.extend(week_predictions)
            all_outcomes.extend(week_outcomes)
            bankroll_history.append(bankroll)

            # Calculate weekly metrics
            weekly_roi = self.metrics_calculator.calculate_roi(
                week_slips, self.initial_bankroll
            )

            weekly_summaries.append({
                "week": week,
                "num_props": len(props),
                "num_slips": len(week_slips),
                "roi": weekly_roi["roi"],
                "profit": weekly_roi["total_profit"],
                "bankroll": bankroll,
                "win_rate": sum(1 for slip in week_slips if slip["won"]) / len(week_slips) if week_slips else 0.0,
            })

            logger.info(
                f"Week {week} complete - ROI: {weekly_roi['roi']:.2f}%, "
                f"Bankroll: ${bankroll:.2f}"
            )

        # Calculate overall metrics
        overall_metrics = self._calculate_overall_metrics(
            all_slips,
            all_predictions,
            all_outcomes,
            bankroll_history
        )

        # Generate calibration plots
        calibration_plot = self._generate_calibration_plot(
            all_predictions, all_outcomes
        ) if MATPLOTLIB_AVAILABLE else None

        # Compile results
        results = {
            "backtest_summary": {
                "weeks": weeks,
                "league": league,
                "risk_mode": self.risk_mode,
                "initial_bankroll": self.initial_bankroll,
                "final_bankroll": bankroll,
                "total_profit": bankroll - self.initial_bankroll,
                "num_weeks": len(weeks),
                "total_bets": len(all_slips),
            },
            "overall_metrics": overall_metrics,
            "weekly_summary": weekly_summaries,
            "bankroll_history": bankroll_history,
            "calibration_plot": calibration_plot,
        }

        # Save to database
        if save_to_db and self.db_session and user_id:
            experiment_id = await self._save_to_experiments(
                user_id=user_id,
                weeks=weeks,
                league=league,
                metrics=overall_metrics,
                num_props=sum(w["num_props"] for w in weekly_summaries),
                num_slips=len(all_slips),
            )
            results["experiment_id"] = experiment_id

        logger.info(
            f"Backtest complete - Final ROI: {overall_metrics['roi_metrics']['roi']:.2f}%, "
            f"Sharpe: {overall_metrics['sharpe_ratio']:.2f}"
        )

        return results

    async def _get_props_for_week(
        self,
        week: int,
        league: str
    ) -> List[Dict]:
        """
        Retrieve props for a specific week from database

        Args:
            week: Week number
            league: League name

        Returns:
            List of prop dictionaries
        """
        if not self.db_session:
            logger.warning("No database session - cannot retrieve props")
            return []

        try:
            from sqlalchemy import select

            # Query for props
            query = select(PropMarket).where(
                PropMarket.week == week,
                PropMarket.league == league,
                PropMarket.is_active == True,
            )

            result = await self.db_session.execute(query)
            props = result.scalars().all()

            # Convert to dictionaries
            prop_dicts = []
            for prop in props:
                prop_dicts.append({
                    "id": str(prop.id),
                    "player_name": prop.player_name,
                    "market_type": prop.market_type,
                    "line": prop.line,
                    "team": prop.team,
                    "opponent": prop.opponent,
                    "platform": prop.platform,
                    # Mock actual outcome for backtesting
                    # In production, this would come from actual game results
                    "actual_value": self._mock_actual_outcome(prop),
                })

            logger.info(f"Retrieved {len(prop_dicts)} props for week {week}")
            return prop_dicts

        except Exception as e:
            logger.error(f"Failed to retrieve props: {e}")
            return []

    def _mock_actual_outcome(self, prop: PropMarket) -> float:
        """
        Mock actual outcome for backtesting

        In production, this should be replaced with actual game results
        """
        # For now, generate random outcome based on line
        # This is a placeholder - replace with actual results data
        np.random.seed(hash(str(prop.id)) % (2**32))

        # Generate outcome with some variance around the line
        variance = prop.line * 0.3
        actual = np.random.normal(prop.line, variance)

        return float(max(0, actual))

    async def _generate_predictions(
        self,
        props: List[Dict],
        model: Optional[EnsemblePredictor]
    ) -> Tuple[List[float], List[bool]]:
        """
        Generate predictions for props

        Args:
            props: List of prop dictionaries
            model: Optional model to use for predictions

        Returns:
            Tuple of (predictions, outcomes)
        """
        predictions = []
        outcomes = []

        for prop in props:
            # Generate prediction
            if model:
                # Use provided model
                # Note: This is simplified - in production, you'd extract features
                # from the prop and use the model properly
                p_hit = self._mock_prediction(prop)
            else:
                # Mock prediction for testing
                p_hit = self._mock_prediction(prop)

            predictions.append(p_hit)

            # Determine outcome
            actual_value = prop.get("actual_value", 0.0)
            line = prop.get("line", 0.0)
            outcome = actual_value > line  # Over bet

            outcomes.append(outcome)

        return predictions, outcomes

    def _mock_prediction(self, prop: Dict) -> float:
        """Generate mock prediction for testing"""
        # Placeholder prediction based on prop hash
        np.random.seed(hash(str(prop.get("id", ""))) % (2**32))
        return float(np.random.beta(5, 5))  # Centered around 0.5

    def _simulate_betting(
        self,
        predictions: List[float],
        outcomes: List[bool],
        current_bankroll: float
    ) -> Tuple[List[Dict], float]:
        """
        Simulate betting with Kelly sizing

        Args:
            predictions: List of predicted probabilities
            outcomes: List of actual outcomes
            current_bankroll: Current bankroll amount

        Returns:
            Tuple of (bet_slips, final_bankroll)
        """
        slips = []
        bankroll = current_bankroll

        kelly_fraction = self.risk_config["kelly_fraction"]
        max_bet_pct = self.risk_config["max_bet_pct"]
        min_confidence = self.risk_config["min_confidence"]

        for p_hit, outcome in zip(predictions, outcomes):
            # Only bet if confidence exceeds threshold
            if p_hit < min_confidence:
                continue

            # Calculate Kelly bet size
            # Assuming even money odds (2.0 decimal odds)
            odds = 2.0
            kelly_size = self.metrics_calculator.calculate_kelly_fraction(
                p_win=p_hit,
                odds=odds,
                kelly_fraction=kelly_fraction
            )

            # Calculate stake
            stake = bankroll * kelly_size
            max_stake = bankroll * max_bet_pct
            stake = min(stake, max_stake)

            # Skip if stake too small
            if stake < 1.0:
                continue

            # Calculate payout
            if outcome:
                payout = stake * odds
                profit = payout - stake
            else:
                payout = 0.0
                profit = -stake

            # Update bankroll
            bankroll += profit

            # Record slip
            slips.append({
                "p_hit": p_hit,
                "stake": stake,
                "payout": payout,
                "profit": profit,
                "won": outcome,
                "odds": odds,
                "bankroll_after": bankroll,
            })

            # Stop betting if bankroll depleted
            if bankroll <= 0:
                logger.warning("Bankroll depleted - stopping betting")
                break

        return slips, bankroll

    def _calculate_overall_metrics(
        self,
        slips: List[Dict],
        predictions: List[float],
        outcomes: List[bool],
        bankroll_history: List[float]
    ) -> Dict[str, any]:
        """Calculate comprehensive metrics for backtest"""
        metrics = self.metrics_calculator.generate_summary_stats(
            slips=slips,
            predictions=predictions,
            outcomes=outcomes,
            initial_bankroll=self.initial_bankroll
        )

        # Add backtest-specific metrics
        metrics["backtest_config"] = {
            "risk_mode": self.risk_mode,
            "kelly_fraction": self.risk_config["kelly_fraction"],
            "max_bet_pct": self.risk_config["max_bet_pct"],
            "min_confidence": self.risk_config["min_confidence"],
        }

        return metrics

    def _generate_calibration_plot(
        self,
        predictions: List[float],
        outcomes: List[bool]
    ) -> Optional[str]:
        """
        Generate calibration curve plot

        Returns:
            Base64-encoded PNG image string
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            from sklearn.calibration import calibration_curve

            # Generate calibration curve
            fraction_of_positives, mean_predicted_value = calibration_curve(
                outcomes, predictions, n_bins=10, strategy="uniform"
            )

            # Create plot
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

            # Calibration curve
            ax1.plot([0, 1], [0, 1], "k--", label="Perfect calibration", linewidth=2)
            ax1.plot(
                mean_predicted_value,
                fraction_of_positives,
                "s-",
                label="Model",
                linewidth=2,
                markersize=8
            )
            ax1.set_xlabel("Mean Predicted Probability", fontsize=12)
            ax1.set_ylabel("Fraction of Positives", fontsize=12)
            ax1.set_title("Calibration Curve (Reliability Diagram)", fontsize=14, fontweight="bold")
            ax1.legend(loc="best")
            ax1.grid(alpha=0.3)

            # Prediction distribution
            ax2.hist(predictions, bins=30, alpha=0.7, edgecolor="black")
            ax2.set_xlabel("Predicted Probability", fontsize=12)
            ax2.set_ylabel("Frequency", fontsize=12)
            ax2.set_title("Prediction Distribution", fontsize=14, fontweight="bold")
            ax2.grid(alpha=0.3)

            plt.tight_layout()

            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format="png", dpi=100, bbox_inches="tight")
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode("utf-8")
            plt.close(fig)

            return image_base64

        except Exception as e:
            logger.error(f"Failed to generate calibration plot: {e}")
            return None

    async def _save_to_experiments(
        self,
        user_id: str,
        weeks: List[int],
        league: str,
        metrics: Dict,
        num_props: int,
        num_slips: int
    ) -> str:
        """
        Save backtest results to experiments table

        Returns:
            Experiment ID
        """
        if not self.db_session:
            logger.warning("No database session - cannot save to experiments")
            return ""

        try:
            # Create experiment record
            experiment = Experiment(
                id=uuid4(),
                user_id=uuid4(),  # Use provided user_id in production
                snapshot_id=None,
                timestamp=datetime.now(timezone.utc),
                week=weeks[0] if weeks else 0,
                league=league,
                risk_mode=self.risk_mode,
                bankroll=self.initial_bankroll,
                num_props=num_props,
                num_slips=num_slips,
                metrics=metrics,
                name=f"Backtest - {league} Weeks {min(weeks)}-{max(weeks)}",
                description=f"Backtest with {self.risk_mode} risk mode",
                status="completed",
            )

            self.db_session.add(experiment)
            await self.db_session.commit()
            await self.db_session.refresh(experiment)

            logger.info(f"Saved backtest to experiments - ID: {experiment.id}")
            return str(experiment.id)

        except Exception as e:
            logger.error(f"Failed to save to experiments: {e}")
            await self.db_session.rollback()
            return ""

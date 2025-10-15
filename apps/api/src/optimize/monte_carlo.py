"""
Monte Carlo simulation for parlay outcome prediction
"""
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from src.types import ModelPrediction, PropLeg


@dataclass
class SimulationResult:
    """Results from Monte Carlo simulation"""
    # Basic statistics
    mean_payout: float
    median_payout: float
    std_dev: float

    # Probability metrics
    win_probability: float
    loss_probability: float

    # Expected value
    expected_value: float
    ev_percentage: float

    # Risk metrics
    variance: float
    var_95: float  # Value at Risk at 95% confidence
    cvar_95: float  # Conditional VaR (expected shortfall)

    # Distribution percentiles
    percentile_5: float
    percentile_25: float
    percentile_50: float
    percentile_75: float
    percentile_95: float
    percentile_99: float

    # Simulation metadata
    n_simulations: int
    n_legs: int

    # Raw samples for further analysis (optional)
    samples: Optional[np.ndarray] = None


class CorrelatedSampler:
    """
    Generate correlated random samples for parlay legs

    Uses Gaussian copula approach to generate correlated samples
    while preserving marginal distributions.
    """

    def __init__(self, correlation_matrix: Optional[np.ndarray] = None):
        """
        Initialize correlated sampler

        Args:
            correlation_matrix: NxN correlation matrix for N legs
                               If None, assumes independence
        """
        self.correlation_matrix = correlation_matrix

    def sample(
        self,
        predictions: List[ModelPrediction],
        n_samples: int,
        seed: Optional[int] = None,
    ) -> np.ndarray:
        """
        Generate correlated samples for predictions

        Args:
            predictions: List of model predictions with probabilities
            n_samples: Number of samples to generate
            seed: Random seed for reproducibility

        Returns:
            Array of shape (n_samples, n_legs) with 1 for success, 0 for failure
        """
        if seed is not None:
            np.random.seed(seed)

        n_legs = len(predictions)

        if self.correlation_matrix is not None and self.correlation_matrix.shape[0] == n_legs:
            # Generate correlated samples using Gaussian copula
            samples = self._generate_correlated_samples(predictions, n_samples)
        else:
            # Generate independent samples
            samples = self._generate_independent_samples(predictions, n_samples)

        return samples

    def _generate_independent_samples(
        self,
        predictions: List[ModelPrediction],
        n_samples: int,
    ) -> np.ndarray:
        """Generate independent samples (no correlation)"""
        n_legs = len(predictions)
        samples = np.zeros((n_samples, n_legs), dtype=int)

        for i, pred in enumerate(predictions):
            # Sample from Bernoulli distribution
            samples[:, i] = np.random.binomial(1, pred.prob_over, n_samples)

        return samples

    def _generate_correlated_samples(
        self,
        predictions: List[ModelPrediction],
        n_samples: int,
    ) -> np.ndarray:
        """Generate correlated samples using Gaussian copula"""
        n_legs = len(predictions)

        # Generate correlated normal samples
        mean = np.zeros(n_legs)
        try:
            # Use Cholesky decomposition for efficiency
            L = np.linalg.cholesky(self.correlation_matrix)
            z = np.random.normal(0, 1, (n_samples, n_legs))
            corr_normals = z @ L.T
        except np.linalg.LinAlgError:
            # If Cholesky fails, fall back to eigenvalue decomposition
            eigenvalues, eigenvectors = np.linalg.eigh(self.correlation_matrix)
            eigenvalues = np.maximum(eigenvalues, 1e-10)  # Ensure positive
            L = eigenvectors @ np.diag(np.sqrt(eigenvalues))
            z = np.random.normal(0, 1, (n_samples, n_legs))
            corr_normals = z @ L.T

        # Transform to uniform [0, 1]
        from scipy.stats import norm
        uniform_samples = norm.cdf(corr_normals)

        # Transform to Bernoulli outcomes
        samples = np.zeros((n_samples, n_legs), dtype=int)
        for i, pred in enumerate(predictions):
            samples[:, i] = (uniform_samples[:, i] < pred.prob_over).astype(int)

        return samples


class MonteCarloSimulator:
    """
    Monte Carlo simulator for parlay outcomes

    Simulates thousands of possible outcomes accounting for:
    - Individual leg probabilities
    - Correlations between legs
    - Payout structure
    """

    def __init__(self, default_n_sims: int = 10000, seed: Optional[int] = None):
        """
        Initialize simulator

        Args:
            default_n_sims: Default number of simulations
            seed: Random seed for reproducibility
        """
        self.default_n_sims = default_n_sims
        self.seed = seed

    def simulate_slip(
        self,
        legs: List[PropLeg],
        predictions: List[ModelPrediction],
        payout_multiplier: float,
        stake: float = 10.0,
        correlation_matrix: Optional[np.ndarray] = None,
        n_sims: Optional[int] = None,
    ) -> SimulationResult:
        """
        Simulate outcomes for a parlay slip

        Args:
            legs: List of prop legs in the parlay
            predictions: Predictions for each leg
            payout_multiplier: Payout multiplier (e.g., 3.0 for 3x)
            stake: Stake amount in dollars
            correlation_matrix: Optional correlation matrix between legs
            n_sims: Number of simulations (uses default if None)

        Returns:
            SimulationResult with outcome statistics
        """
        if n_sims is None:
            n_sims = self.default_n_sims

        # Validate inputs
        if len(legs) != len(predictions):
            raise ValueError("Number of legs must match number of predictions")

        # Generate correlated samples
        sampler = CorrelatedSampler(correlation_matrix)
        samples = sampler.sample(predictions, n_sims, self.seed)

        # Calculate outcomes
        # Parlay wins only if ALL legs hit
        all_legs_hit = np.all(samples == 1, axis=1)
        payouts = np.where(all_legs_hit, stake * payout_multiplier, 0.0)

        # Calculate profit (payout - stake)
        profits = payouts - stake

        # Calculate statistics
        mean_payout = np.mean(payouts)
        median_payout = np.median(payouts)
        std_dev = np.std(profits)
        variance = np.var(profits)

        win_probability = np.mean(all_legs_hit)
        loss_probability = 1 - win_probability

        expected_value = np.mean(profits)
        ev_percentage = expected_value / stake if stake > 0 else 0.0

        # Risk metrics
        var_95 = np.percentile(profits, 5)  # 5th percentile (95% VaR)
        losses = profits[profits < 0]
        cvar_95 = np.mean(losses) if len(losses) > 0 else 0.0

        # Percentiles
        percentiles = np.percentile(profits, [5, 25, 50, 75, 95, 99])

        return SimulationResult(
            mean_payout=float(mean_payout),
            median_payout=float(median_payout),
            std_dev=float(std_dev),
            win_probability=float(win_probability),
            loss_probability=float(loss_probability),
            expected_value=float(expected_value),
            ev_percentage=float(ev_percentage),
            variance=float(variance),
            var_95=float(var_95),
            cvar_95=float(cvar_95),
            percentile_5=float(percentiles[0]),
            percentile_25=float(percentiles[1]),
            percentile_50=float(percentiles[2]),
            percentile_75=float(percentiles[3]),
            percentile_95=float(percentiles[4]),
            percentile_99=float(percentiles[5]),
            n_simulations=n_sims,
            n_legs=len(legs),
            samples=profits,  # Store for further analysis
        )

    def simulate_multiple_slips(
        self,
        slips: List[Dict],
        n_sims: Optional[int] = None,
    ) -> List[SimulationResult]:
        """
        Simulate multiple slips in parallel

        Args:
            slips: List of slip dicts with 'legs', 'predictions', 'payout_multiplier', etc.
            n_sims: Number of simulations per slip

        Returns:
            List of SimulationResult, one per slip
        """
        results = []
        for slip in slips:
            result = self.simulate_slip(
                legs=slip["legs"],
                predictions=slip["predictions"],
                payout_multiplier=slip["payout_multiplier"],
                stake=slip.get("stake", 10.0),
                correlation_matrix=slip.get("correlation_matrix"),
                n_sims=n_sims,
            )
            results.append(result)

        return results

    def calculate_portfolio_ev(
        self,
        slips: List[Dict],
        n_sims: Optional[int] = None,
    ) -> Tuple[float, float, np.ndarray]:
        """
        Calculate expected value and variance for a portfolio of slips

        Args:
            slips: List of slip dicts
            n_sims: Number of simulations

        Returns:
            (portfolio_ev, portfolio_variance, profit_distribution)
        """
        results = self.simulate_multiple_slips(slips, n_sims)

        # Sum profits across all slips for each simulation
        portfolio_profits = np.zeros(results[0].n_simulations)
        for result in results:
            portfolio_profits += result.samples

        portfolio_ev = np.mean(portfolio_profits)
        portfolio_variance = np.var(portfolio_profits)

        return portfolio_ev, portfolio_variance, portfolio_profits

    def stress_test(
        self,
        legs: List[PropLeg],
        predictions: List[ModelPrediction],
        payout_multiplier: float,
        stake: float = 10.0,
        prob_adjustment: float = -0.05,  # Reduce all probs by 5%
        n_sims: Optional[int] = None,
    ) -> SimulationResult:
        """
        Stress test slip under adverse conditions

        Args:
            legs: Prop legs
            predictions: Model predictions
            payout_multiplier: Payout multiplier
            stake: Stake amount
            prob_adjustment: Adjustment to apply to all probabilities (negative = pessimistic)
            n_sims: Number of simulations

        Returns:
            SimulationResult under stress conditions
        """
        # Create adjusted predictions
        adjusted_predictions = []
        for pred in predictions:
            # Create copy with adjusted probability
            adjusted_pred = ModelPrediction(
                prop_leg_id=pred.prop_leg_id,
                player_id=pred.player_id,
                stat_type=pred.stat_type,
                predicted_value=pred.predicted_value,
                line_value=pred.line_value,
                prob_over=max(0.01, min(0.99, pred.prob_over + prob_adjustment)),
                prob_under=max(0.01, min(0.99, pred.prob_under - prob_adjustment)),
                confidence=pred.confidence,
                edge=pred.edge,
                model_type=pred.model_type,
                model_version=pred.model_version,
            )
            adjusted_predictions.append(adjusted_pred)

        # Run simulation with adjusted probabilities
        return self.simulate_slip(
            legs=legs,
            predictions=adjusted_predictions,
            payout_multiplier=payout_multiplier,
            stake=stake,
            correlation_matrix=None,  # Stress test assumes independence
            n_sims=n_sims,
        )

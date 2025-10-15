"""
Kelly Criterion stake sizing for optimal bankroll management
"""
import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class KellyResult:
    """Result from Kelly calculation"""
    full_kelly: float  # Full Kelly stake as fraction of bankroll
    fractional_kelly: float  # Fractional Kelly stake (typically 1/4)
    stake_amount: float  # Actual dollar amount to stake
    edge: float  # Expected edge
    variance: float  # Outcome variance
    is_clamped: bool  # Whether stake was clamped to min/max
    reason: Optional[str] = None  # Reason for clamping or rejection


class KellyCriterion:
    """
    Kelly Criterion stake sizing calculator

    The Kelly Criterion optimizes bet sizing to maximize logarithmic growth
    of bankroll. For parlays, we use fractional Kelly to reduce volatility.

    Classic Kelly formula:
        f* = (p * b - q) / b

    Where:
        f* = fraction of bankroll to wager
        p = probability of winning
        q = probability of losing (1 - p)
        b = odds received on wager (payout - 1)

    For multiple-outcome parlays with variance, we use:
        f* = edge / variance
    """

    def __init__(
        self,
        min_stake: float = 5.0,
        max_stake: float = 50.0,
        kelly_fraction: float = 0.25,
        max_kelly: float = 0.10,  # Never bet more than 10% of bankroll
        min_edge_threshold: float = 0.01,  # Require 1% minimum edge
    ):
        """
        Initialize Kelly calculator

        Args:
            min_stake: Minimum bet amount in dollars
            max_stake: Maximum bet amount in dollars
            kelly_fraction: Fraction of Kelly to use (0.25 = 1/4 Kelly)
            max_kelly: Maximum fraction of bankroll to risk
            min_edge_threshold: Minimum edge required to stake
        """
        self.min_stake = min_stake
        self.max_stake = max_stake
        self.kelly_fraction = kelly_fraction
        self.max_kelly = max_kelly
        self.min_edge_threshold = min_edge_threshold

    def calculate_stake(
        self,
        ev: float,
        variance: float,
        bankroll: float,
        win_prob: Optional[float] = None,
        payout_multiplier: Optional[float] = None,
    ) -> KellyResult:
        """
        Calculate optimal stake size using Kelly Criterion

        Args:
            ev: Expected value as a fraction (e.g., 0.15 for 15% EV)
            variance: Variance of the outcome distribution
            bankroll: Current bankroll in dollars
            win_prob: Optional probability of winning (for classic Kelly)
            payout_multiplier: Optional payout multiplier (e.g., 3.0 for 3x)

        Returns:
            KellyResult with recommended stake
        """
        # Check minimum edge threshold
        if ev < self.min_edge_threshold:
            return KellyResult(
                full_kelly=0.0,
                fractional_kelly=0.0,
                stake_amount=0.0,
                edge=ev,
                variance=variance,
                is_clamped=True,
                reason=f"Edge {ev:.3f} below minimum threshold {self.min_edge_threshold}"
            )

        # Use classic Kelly if win_prob and payout provided
        if win_prob is not None and payout_multiplier is not None:
            full_kelly = self._classic_kelly(win_prob, payout_multiplier)
        else:
            # Use EV/variance formula for complex parlays
            full_kelly = self._kelly_from_variance(ev, variance)

        # Apply fractional Kelly
        fractional_kelly = full_kelly * self.kelly_fraction

        # Cap at maximum Kelly
        if fractional_kelly > self.max_kelly:
            fractional_kelly = self.max_kelly
            reason = f"Capped at {self.max_kelly:.1%} max Kelly"
        else:
            reason = None

        # Convert to dollar amount
        stake_amount = fractional_kelly * bankroll

        # Apply min/max clamps
        is_clamped = False
        if stake_amount < self.min_stake:
            stake_amount = self.min_stake
            is_clamped = True
            reason = f"Raised to minimum stake ${self.min_stake}"
        elif stake_amount > self.max_stake:
            stake_amount = self.max_stake
            is_clamped = True
            reason = f"Lowered to maximum stake ${self.max_stake}"

        return KellyResult(
            full_kelly=full_kelly,
            fractional_kelly=fractional_kelly,
            stake_amount=round(stake_amount, 2),
            edge=ev,
            variance=variance,
            is_clamped=is_clamped,
            reason=reason,
        )

    def _classic_kelly(self, win_prob: float, payout_multiplier: float) -> float:
        """
        Classic Kelly formula for binary outcomes

        Args:
            win_prob: Probability of winning (0 to 1)
            payout_multiplier: Payout if win (e.g., 3.0 for 3x)

        Returns:
            Fraction of bankroll to wager
        """
        if win_prob <= 0 or win_prob >= 1:
            return 0.0

        lose_prob = 1 - win_prob
        b = payout_multiplier - 1  # Net odds

        if b <= 0:
            return 0.0

        # f* = (p * b - q) / b
        kelly = (win_prob * b - lose_prob) / b

        return max(0.0, kelly)

    def _kelly_from_variance(self, ev: float, variance: float) -> float:
        """
        Calculate Kelly fraction from EV and variance

        This is used for complex parlays where we have the full
        distribution rather than simple win/lose probabilities.

        Formula: f* = edge / variance

        Args:
            ev: Expected value as fraction
            variance: Variance of outcome distribution

        Returns:
            Fraction of bankroll to wager
        """
        if variance <= 0:
            return 0.0

        kelly = ev / variance

        return max(0.0, kelly)

    def calculate_multi_bet_stakes(
        self,
        bets: list[dict],
        bankroll: float,
        allocation_method: str = "equal_kelly",
    ) -> list[KellyResult]:
        """
        Calculate stakes for multiple simultaneous bets

        Args:
            bets: List of dicts with 'ev', 'variance', 'win_prob', 'payout_multiplier'
            bankroll: Total bankroll available
            allocation_method: How to allocate across bets
                - 'equal_kelly': Each bet gets independent Kelly fraction
                - 'scaled_kelly': Scale Kelly to ensure total < max_kelly
                - 'priority': Rank by EV and allocate sequentially

        Returns:
            List of KellyResult for each bet
        """
        if not bets:
            return []

        results = []

        if allocation_method == "equal_kelly":
            # Independent Kelly for each bet
            for bet in bets:
                result = self.calculate_stake(
                    ev=bet.get("ev", 0.0),
                    variance=bet.get("variance", 1.0),
                    bankroll=bankroll,
                    win_prob=bet.get("win_prob"),
                    payout_multiplier=bet.get("payout_multiplier"),
                )
                results.append(result)

        elif allocation_method == "scaled_kelly":
            # Calculate all Kelly fractions first
            kelly_fractions = []
            for bet in bets:
                result = self.calculate_stake(
                    ev=bet.get("ev", 0.0),
                    variance=bet.get("variance", 1.0),
                    bankroll=bankroll,
                    win_prob=bet.get("win_prob"),
                    payout_multiplier=bet.get("payout_multiplier"),
                )
                kelly_fractions.append(result.fractional_kelly)

            # Scale if total exceeds max_kelly
            total_kelly = sum(kelly_fractions)
            if total_kelly > self.max_kelly:
                scale_factor = self.max_kelly / total_kelly
                for i, bet in enumerate(bets):
                    scaled_kelly = kelly_fractions[i] * scale_factor
                    stake = scaled_kelly * bankroll
                    stake = max(self.min_stake, min(self.max_stake, stake))

                    results.append(KellyResult(
                        full_kelly=kelly_fractions[i] / self.kelly_fraction,
                        fractional_kelly=scaled_kelly,
                        stake_amount=round(stake, 2),
                        edge=bet.get("ev", 0.0),
                        variance=bet.get("variance", 1.0),
                        is_clamped=True,
                        reason=f"Scaled by {scale_factor:.3f} to fit max Kelly"
                    ))
            else:
                # No scaling needed
                for bet in bets:
                    result = self.calculate_stake(
                        ev=bet.get("ev", 0.0),
                        variance=bet.get("variance", 1.0),
                        bankroll=bankroll,
                        win_prob=bet.get("win_prob"),
                        payout_multiplier=bet.get("payout_multiplier"),
                    )
                    results.append(result)

        elif allocation_method == "priority":
            # Sort by EV and allocate sequentially
            sorted_bets = sorted(
                enumerate(bets),
                key=lambda x: x[1].get("ev", 0.0),
                reverse=True
            )

            remaining_bankroll = bankroll
            temp_results = [None] * len(bets)

            for idx, bet in sorted_bets:
                result = self.calculate_stake(
                    ev=bet.get("ev", 0.0),
                    variance=bet.get("variance", 1.0),
                    bankroll=remaining_bankroll,
                    win_prob=bet.get("win_prob"),
                    payout_multiplier=bet.get("payout_multiplier"),
                )
                temp_results[idx] = result
                remaining_bankroll = max(0, remaining_bankroll - result.stake_amount)

            results = temp_results

        return results

    def fractional_kelly(self, fraction: float = 0.25) -> 'KellyCriterion':
        """
        Create new Kelly calculator with different fraction

        Args:
            fraction: Kelly fraction to use (e.g., 0.25 for 1/4 Kelly)

        Returns:
            New KellyCriterion instance with updated fraction
        """
        return KellyCriterion(
            min_stake=self.min_stake,
            max_stake=self.max_stake,
            kelly_fraction=fraction,
            max_kelly=self.max_kelly,
            min_edge_threshold=self.min_edge_threshold,
        )

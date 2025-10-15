"""
Correlation constraints for parlay construction

Enforces correlation limits and diversity requirements to build
robust, uncorrelated parlays.
"""
import logging
from typing import Dict, List, Tuple, Optional, Literal
from enum import Enum

import numpy as np

from src.types import PropLeg
from src.corr.correlation import CorrelationAnalyzer

logger = logging.getLogger(__name__)


class CorrelationWarningLevel(str, Enum):
    """Warning levels for correlation strength"""
    GREEN = "green"  # OK, low correlation
    YELLOW = "yellow"  # Warning, moderate correlation
    RED = "red"  # Block, high correlation


class CorrelationConstraints:
    """
    Enforces correlation constraints for parlay optimization

    Implements tiered correlation thresholds:
    - GREEN (|ρ| < 0.35): OK, no penalty
    - YELLOW (0.35 ≤ |ρ| < 0.75): Warning, soft penalty
    - RED (|ρ| ≥ 0.75): Block, hard constraint
    """

    def __init__(
        self,
        green_threshold: float = 0.35,
        yellow_threshold: float = 0.75,
        correlation_analyzer: Optional[CorrelationAnalyzer] = None
    ):
        """
        Initialize correlation constraints

        Args:
            green_threshold: Maximum correlation for GREEN level
            yellow_threshold: Minimum correlation for RED level
            correlation_analyzer: Optional correlation analyzer instance
        """
        self.green_threshold = green_threshold
        self.yellow_threshold = yellow_threshold

        if correlation_analyzer is None:
            self.correlation_analyzer = CorrelationAnalyzer()
        else:
            self.correlation_analyzer = correlation_analyzer

        # Validation
        if not 0 < green_threshold < yellow_threshold <= 1:
            raise ValueError(
                f"Thresholds must satisfy 0 < green < yellow <= 1, "
                f"got green={green_threshold}, yellow={yellow_threshold}"
            )

    async def check_correlation(
        self,
        leg_a: PropLeg,
        leg_b: PropLeg
    ) -> Tuple[float, CorrelationWarningLevel]:
        """
        Check correlation between two prop legs

        Args:
            leg_a: First prop leg
            leg_b: Second prop leg

        Returns:
            Tuple of (correlation_coefficient, warning_level)
        """
        # Get correlation
        correlation = await self.correlation_analyzer.get_pairwise_correlation(
            leg_a, leg_b
        )

        # Determine warning level based on absolute correlation
        abs_corr = abs(correlation)

        if abs_corr < self.green_threshold:
            level = CorrelationWarningLevel.GREEN
        elif abs_corr < self.yellow_threshold:
            level = CorrelationWarningLevel.YELLOW
        else:
            level = CorrelationWarningLevel.RED

        return correlation, level

    async def enforce_diversity(
        self,
        legs: List[PropLeg],
        min_games: int = 2,
        min_players: int = 2,
        max_same_game: int = 2,
        max_same_player: int = 1,
        max_same_team: int = 3
    ) -> Tuple[bool, List[str]]:
        """
        Ensure props come from diverse games and players

        Args:
            legs: List of prop legs to check
            min_games: Minimum number of unique games required
            min_players: Minimum number of unique players required
            max_same_game: Maximum props allowed from same game
            max_same_player: Maximum props allowed for same player
            max_same_team: Maximum props allowed from same team

        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        violations = []

        # Count unique entities
        games = [leg.game_id for leg in legs]
        players = [leg.player_id for leg in legs]
        teams = [leg.team for leg in legs]

        unique_games = len(set(games))
        unique_players = len(set(players))

        # Check minimum diversity
        if unique_games < min_games:
            violations.append(
                f"Requires {min_games} games, but only {unique_games} present"
            )

        if unique_players < min_players:
            violations.append(
                f"Requires {min_players} players, but only {unique_players} present"
            )

        # Check maximum concentration
        from collections import Counter

        game_counts = Counter(games)
        for game_id, count in game_counts.items():
            if count > max_same_game:
                violations.append(
                    f"Game {game_id} has {count} props (max: {max_same_game})"
                )

        player_counts = Counter(players)
        for player_id, count in player_counts.items():
            if count > max_same_player:
                # Find player name for better error message
                player_name = next(
                    (leg.player_name for leg in legs if leg.player_id == player_id),
                    player_id
                )
                violations.append(
                    f"Player {player_name} has {count} props (max: {max_same_player})"
                )

        team_counts = Counter(teams)
        for team, count in team_counts.items():
            if count > max_same_team:
                violations.append(
                    f"Team {team} has {count} props (max: {max_same_team})"
                )

        is_valid = len(violations) == 0
        return is_valid, violations

    def same_player_same_stat_block(
        self,
        legs: List[PropLeg]
    ) -> Tuple[bool, List[str]]:
        """
        Prevent duplicate prop types for same player

        Args:
            legs: List of prop legs to check

        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        violations = []
        seen = set()

        for leg in legs:
            key = (leg.player_id, leg.stat_type, leg.direction)
            if key in seen:
                violations.append(
                    f"Duplicate prop: {leg.player_name} {leg.stat_type} {leg.direction}"
                )
            seen.add(key)

        is_valid = len(violations) == 0
        return is_valid, violations

    async def check_all_constraints(
        self,
        legs: List[PropLeg],
        allow_yellow: bool = True,
        **diversity_kwargs
    ) -> Tuple[bool, Dict]:
        """
        Check all constraints on a set of prop legs

        Args:
            legs: List of prop legs
            allow_yellow: Whether to allow YELLOW correlation level
            **diversity_kwargs: Additional arguments for enforce_diversity

        Returns:
            Tuple of (is_valid, constraint_report)
        """
        report = {
            "is_valid": True,
            "violations": [],
            "warnings": [],
            "correlation_matrix": None,
            "max_correlation": 0.0,
        }

        n_legs = len(legs)

        # Check same player/same stat
        is_valid, violations = self.same_player_same_stat_block(legs)
        if not is_valid:
            report["is_valid"] = False
            report["violations"].extend(violations)

        # Check diversity constraints
        is_valid, violations = await self.enforce_diversity(legs, **diversity_kwargs)
        if not is_valid:
            report["is_valid"] = False
            report["violations"].extend(violations)

        # Check pairwise correlations
        if n_legs >= 2:
            correlation_matrix = await self.correlation_analyzer.estimate_correlation_matrix(
                legs,
                use_cache=False
            )
            report["correlation_matrix"] = correlation_matrix.tolist()

            # Check all pairs
            max_corr = 0.0
            for i in range(n_legs):
                for j in range(i + 1, n_legs):
                    corr = correlation_matrix[i, j]
                    abs_corr = abs(corr)

                    if abs_corr > max_corr:
                        max_corr = abs_corr

                    # Determine warning level
                    if abs_corr >= self.yellow_threshold:
                        # RED level - block
                        report["is_valid"] = False
                        report["violations"].append(
                            f"High correlation ({corr:.3f}) between "
                            f"{legs[i].player_name} {legs[i].stat_type} and "
                            f"{legs[j].player_name} {legs[j].stat_type}"
                        )
                    elif abs_corr >= self.green_threshold:
                        # YELLOW level
                        if not allow_yellow:
                            report["is_valid"] = False
                            report["violations"].append(
                                f"Moderate correlation ({corr:.3f}) between "
                                f"{legs[i].player_name} {legs[i].stat_type} and "
                                f"{legs[j].player_name} {legs[j].stat_type} "
                                f"(yellow not allowed)"
                            )
                        else:
                            report["warnings"].append(
                                f"Moderate correlation ({corr:.3f}) between "
                                f"{legs[i].player_name} {legs[i].stat_type} and "
                                f"{legs[j].player_name} {legs[j].stat_type}"
                            )

            report["max_correlation"] = float(max_corr)

        return report["is_valid"], report

    async def compute_correlation_penalty(
        self,
        legs: List[PropLeg],
        penalty_weight: float = 0.1
    ) -> float:
        """
        Compute soft penalty for YELLOW correlations

        Used in optimization to discourage (but not block) moderate correlations.

        Args:
            legs: List of prop legs
            penalty_weight: Weight for penalty term

        Returns:
            Penalty value (higher = worse)
        """
        if len(legs) < 2:
            return 0.0

        correlation_matrix = await self.correlation_analyzer.estimate_correlation_matrix(
            legs,
            use_cache=False
        )

        # Sum of squared correlations in YELLOW range
        penalty = 0.0
        for i in range(len(legs)):
            for j in range(i + 1, len(legs)):
                abs_corr = abs(correlation_matrix[i, j])

                if self.green_threshold <= abs_corr < self.yellow_threshold:
                    # YELLOW correlation - apply soft penalty
                    # Penalty increases quadratically with correlation strength
                    normalized_corr = (abs_corr - self.green_threshold) / (
                        self.yellow_threshold - self.green_threshold
                    )
                    penalty += normalized_corr ** 2

        return penalty * penalty_weight

    def get_correlation_color(self, correlation: float) -> CorrelationWarningLevel:
        """
        Get warning level color for a correlation value

        Args:
            correlation: Correlation coefficient

        Returns:
            Warning level
        """
        abs_corr = abs(correlation)

        if abs_corr < self.green_threshold:
            return CorrelationWarningLevel.GREEN
        elif abs_corr < self.yellow_threshold:
            return CorrelationWarningLevel.YELLOW
        else:
            return CorrelationWarningLevel.RED

    async def filter_valid_combinations(
        self,
        all_legs: List[PropLeg],
        combo_size: int,
        allow_yellow: bool = True,
        max_combinations: int = 10000
    ) -> List[List[PropLeg]]:
        """
        Generate all valid combinations of props satisfying constraints

        Args:
            all_legs: Pool of all available prop legs
            combo_size: Size of combinations to generate
            allow_yellow: Whether to allow YELLOW correlations
            max_combinations: Maximum combinations to check

        Returns:
            List of valid prop combinations
        """
        from itertools import combinations

        valid_combinations = []
        checked = 0

        for combo in combinations(all_legs, combo_size):
            if checked >= max_combinations:
                logger.warning(
                    f"Reached max combinations limit ({max_combinations}). "
                    f"Stopping search."
                )
                break

            checked += 1
            combo_list = list(combo)

            # Check constraints
            is_valid, _ = await self.check_all_constraints(
                combo_list,
                allow_yellow=allow_yellow
            )

            if is_valid:
                valid_combinations.append(combo_list)

        logger.info(
            f"Found {len(valid_combinations)} valid combinations "
            f"out of {checked} checked"
        )

        return valid_combinations

    def get_thresholds(self) -> Dict:
        """
        Get current correlation thresholds

        Returns:
            Dictionary with threshold values
        """
        return {
            "green_threshold": self.green_threshold,
            "yellow_threshold": self.yellow_threshold,
            "green_range": f"0 to {self.green_threshold}",
            "yellow_range": f"{self.green_threshold} to {self.yellow_threshold}",
            "red_range": f"{self.yellow_threshold} to 1.0",
        }

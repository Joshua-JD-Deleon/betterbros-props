"""
Slip optimization constraints and validation
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from src.types import PropLeg


@dataclass
class SlipConstraints:
    """
    Constraints for parlay slip optimization

    These constraints ensure that optimized slips meet risk management
    and diversification requirements while respecting platform limits.
    """

    # Leg limits
    min_legs: int = 2
    max_legs: int = 5

    # Diversification requirements
    min_distinct_games: int = 2
    max_props_per_game: int = 2
    max_props_per_player: int = 1

    # Stat correlation blocking
    same_player_stat_block: bool = True  # Block correlated stats from same player

    # Correlation limits
    max_correlation: float = 0.3
    max_avg_correlation: float = 0.15

    # EV requirements
    min_ev: float = 0.10  # 10% minimum expected value
    min_edge_per_leg: float = 0.03  # 3% minimum edge per leg

    # Confidence thresholds
    min_confidence: float = 0.60

    # Diversity scoring
    diversity_target: float = 0.75  # Target ratio of unique games to legs

    # Team and position limits
    max_team_exposure: int = 3
    min_distinct_teams: int = 2

    def validate_slip(
        self,
        legs: List[PropLeg],
        correlations: Optional[Dict[tuple, float]] = None,
        ev: Optional[float] = None,
        confidence: Optional[float] = None,
    ) -> tuple[bool, List[str]]:
        """
        Validate a slip against all constraints

        Args:
            legs: List of prop legs in the slip
            correlations: Dict mapping (leg_id_1, leg_id_2) -> correlation
            ev: Expected value of the slip
            confidence: Combined confidence score

        Returns:
            (is_valid, list_of_violations)
        """
        violations = []

        # Check leg count
        if len(legs) < self.min_legs:
            violations.append(f"Too few legs: {len(legs)} < {self.min_legs}")
        if len(legs) > self.max_legs:
            violations.append(f"Too many legs: {len(legs)} > {self.max_legs}")

        # Check game diversity
        game_ids = [leg.game_id for leg in legs]
        unique_games = len(set(game_ids))

        if unique_games < self.min_distinct_games:
            violations.append(
                f"Insufficient game diversity: {unique_games} < {self.min_distinct_games}"
            )

        # Check props per game
        game_counts = {}
        for game_id in game_ids:
            game_counts[game_id] = game_counts.get(game_id, 0) + 1

        max_in_game = max(game_counts.values()) if game_counts else 0
        if max_in_game > self.max_props_per_game:
            violations.append(
                f"Too many props in one game: {max_in_game} > {self.max_props_per_game}"
            )

        # Check props per player
        player_counts = {}
        for leg in legs:
            player_counts[leg.player_id] = player_counts.get(leg.player_id, 0) + 1

        max_per_player = max(player_counts.values()) if player_counts else 0
        if max_per_player > self.max_props_per_player:
            violations.append(
                f"Too many props from one player: {max_per_player} > {self.max_props_per_player}"
            )

        # Check same player stat correlations
        if self.same_player_stat_block:
            for player_id, count in player_counts.items():
                if count > 1:
                    player_stats = [
                        leg.stat_type for leg in legs if leg.player_id == player_id
                    ]
                    # Block highly correlated stats
                    correlated_combos = [
                        ("points", "field_goals_made"),
                        ("points", "three_pointers_made"),
                        ("assists", "turnovers"),
                        ("rebounds", "defensive_rebounds"),
                        ("passing_yards", "passing_attempts"),
                        ("rushing_yards", "rushing_attempts"),
                    ]
                    for stat1, stat2 in correlated_combos:
                        if stat1 in player_stats and stat2 in player_stats:
                            violations.append(
                                f"Correlated stats from same player: {stat1} + {stat2}"
                            )

        # Check team exposure
        team_counts = {}
        for leg in legs:
            team_counts[leg.team] = team_counts.get(leg.team, 0) + 1

        max_team = max(team_counts.values()) if team_counts else 0
        if max_team > self.max_team_exposure:
            violations.append(
                f"Too much team exposure: {max_team} > {self.max_team_exposure}"
            )

        unique_teams = len(team_counts)
        if unique_teams < self.min_distinct_teams:
            violations.append(
                f"Insufficient team diversity: {unique_teams} < {self.min_distinct_teams}"
            )

        # Check correlations if provided
        if correlations:
            max_corr = 0.0
            total_corr = 0.0
            pair_count = 0

            for i, leg1 in enumerate(legs):
                for j, leg2 in enumerate(legs[i+1:], start=i+1):
                    key = (leg1.id, leg2.id)
                    reverse_key = (leg2.id, leg1.id)
                    corr = correlations.get(key, correlations.get(reverse_key, 0.0))

                    max_corr = max(max_corr, abs(corr))
                    total_corr += abs(corr)
                    pair_count += 1

            if max_corr > self.max_correlation:
                violations.append(
                    f"Correlation too high: {max_corr:.3f} > {self.max_correlation}"
                )

            if pair_count > 0:
                avg_corr = total_corr / pair_count
                if avg_corr > self.max_avg_correlation:
                    violations.append(
                        f"Average correlation too high: {avg_corr:.3f} > {self.max_avg_correlation}"
                    )

        # Check EV if provided
        if ev is not None and ev < self.min_ev:
            violations.append(f"EV too low: {ev:.3f} < {self.min_ev}")

        # Check confidence if provided
        if confidence is not None and confidence < self.min_confidence:
            violations.append(
                f"Confidence too low: {confidence:.3f} < {self.min_confidence}"
            )

        return len(violations) == 0, violations

    def calculate_diversity_score(self, legs: List[PropLeg]) -> float:
        """
        Calculate diversity score for a slip

        Score is based on:
        - Unique games vs total legs
        - Unique players vs total legs
        - Unique stat types vs total legs
        - Team distribution evenness

        Returns:
            Float between 0.0 (no diversity) and 1.0 (max diversity)
        """
        if not legs:
            return 0.0

        n_legs = len(legs)

        # Game diversity
        unique_games = len(set(leg.game_id for leg in legs))
        game_score = unique_games / n_legs

        # Player diversity
        unique_players = len(set(leg.player_id for leg in legs))
        player_score = unique_players / n_legs

        # Stat type diversity
        unique_stats = len(set(leg.stat_type for leg in legs))
        stat_score = unique_stats / n_legs

        # Team distribution (Gini coefficient style)
        team_counts = {}
        for leg in legs:
            team_counts[leg.team] = team_counts.get(leg.team, 0) + 1

        if len(team_counts) > 1:
            # Perfect balance = 1.0, all in one team = 0.0
            max_team = max(team_counts.values())
            team_score = 1.0 - (max_team - n_legs / len(team_counts)) / n_legs
        else:
            team_score = 0.0

        # Weighted average
        diversity = (
            0.35 * game_score +
            0.30 * player_score +
            0.20 * stat_score +
            0.15 * team_score
        )

        return min(1.0, diversity)


def create_constraints_for_risk_mode(
    risk_mode: str,
    bankroll: Optional[float] = None
) -> SlipConstraints:
    """
    Create constraint set based on risk mode

    Args:
        risk_mode: 'aggressive', 'moderate', or 'conservative'
        bankroll: Optional bankroll for context-aware constraints

    Returns:
        SlipConstraints configured for the risk mode
    """
    if risk_mode == "aggressive":
        return SlipConstraints(
            min_legs=2,
            max_legs=8,
            min_distinct_games=2,
            max_props_per_game=3,
            max_props_per_player=2,
            same_player_stat_block=False,
            max_correlation=0.5,
            max_avg_correlation=0.3,
            min_ev=0.05,
            min_edge_per_leg=0.02,
            min_confidence=0.55,
            diversity_target=0.60,
            max_team_exposure=4,
            min_distinct_teams=2,
        )

    elif risk_mode == "conservative":
        return SlipConstraints(
            min_legs=2,
            max_legs=4,
            min_distinct_games=3,
            max_props_per_game=1,
            max_props_per_player=1,
            same_player_stat_block=True,
            max_correlation=0.15,
            max_avg_correlation=0.08,
            min_ev=0.15,
            min_edge_per_leg=0.05,
            min_confidence=0.70,
            diversity_target=0.90,
            max_team_exposure=2,
            min_distinct_teams=3,
        )

    else:  # moderate (default)
        return SlipConstraints(
            min_legs=2,
            max_legs=6,
            min_distinct_games=2,
            max_props_per_game=2,
            max_props_per_player=1,
            same_player_stat_block=True,
            max_correlation=0.30,
            max_avg_correlation=0.15,
            min_ev=0.10,
            min_edge_per_leg=0.03,
            min_confidence=0.62,
            diversity_target=0.75,
            max_team_exposure=3,
            min_distinct_teams=2,
        )

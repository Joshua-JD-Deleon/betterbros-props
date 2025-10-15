"""
Generate safer alternative versions of parlay slips
"""
from copy import deepcopy
from dataclasses import dataclass
from typing import List, Optional, Tuple
from src.types import ModelPrediction, PropLeg


@dataclass
class SaferAlternative:
    """A safer alternative to an original slip"""
    legs: List[PropLeg]
    predictions: List[ModelPrediction]
    removed_legs: List[str]  # IDs of removed legs
    reason: str
    risk_reduction: float  # How much risk was reduced (0-1)
    ev_impact: float  # Change in EV (can be negative)


class SaferAlternativeGenerator:
    """
    Generate safer alternatives to risky parlay slips

    Strategies:
    1. Remove highest correlation pairs
    2. Remove lowest confidence legs
    3. Remove legs from same game
    4. Remove highest variance legs
    5. Reduce leg count to lower risk
    """

    def __init__(self, min_legs: int = 2):
        """
        Initialize generator

        Args:
            min_legs: Minimum number of legs to keep
        """
        self.min_legs = min_legs

    def generate_safer_version(
        self,
        legs: List[PropLeg],
        predictions: List[ModelPrediction],
        correlation_matrix: Optional[dict] = None,
        max_alternatives: int = 3,
    ) -> List[SaferAlternative]:
        """
        Generate safer alternatives to a slip

        Args:
            legs: Original prop legs
            predictions: Predictions for legs
            correlation_matrix: Dict mapping (leg_id_1, leg_id_2) -> correlation
            max_alternatives: Maximum number of alternatives to generate

        Returns:
            List of SaferAlternative slips
        """
        if len(legs) <= self.min_legs:
            return []  # Already at minimum

        alternatives = []

        # Strategy 1: Remove highest correlation pairs
        if correlation_matrix:
            alt = self._remove_correlated_legs(legs, predictions, correlation_matrix)
            if alt:
                alternatives.append(alt)

        # Strategy 2: Remove lowest confidence leg
        alt = self._remove_lowest_confidence(legs, predictions)
        if alt:
            alternatives.append(alt)

        # Strategy 3: Keep only distinct games
        alt = self._keep_distinct_games(legs, predictions)
        if alt:
            alternatives.append(alt)

        # Strategy 4: Remove highest variance legs
        alt = self._remove_high_variance(legs, predictions)
        if alt:
            alternatives.append(alt)

        # Strategy 5: Reduce to conservative leg count (3 legs)
        alt = self._reduce_to_conservative(legs, predictions)
        if alt:
            alternatives.append(alt)

        # Sort by best risk/reward tradeoff
        alternatives = self._rank_alternatives(alternatives)

        return alternatives[:max_alternatives]

    def _remove_correlated_legs(
        self,
        legs: List[PropLeg],
        predictions: List[ModelPrediction],
        correlation_matrix: dict,
    ) -> Optional[SaferAlternative]:
        """Remove leg from highest correlation pair"""
        max_corr = 0.0
        leg_to_remove_idx = None

        # Find highest correlation pair
        for i in range(len(legs)):
            for j in range(i + 1, len(legs)):
                key = (legs[i].id, legs[j].id)
                reverse_key = (legs[j].id, legs[i].id)
                corr = abs(correlation_matrix.get(key, correlation_matrix.get(reverse_key, 0.0)))

                if corr > max_corr:
                    max_corr = corr
                    # Remove the leg with lower confidence
                    if predictions[i].confidence < predictions[j].confidence:
                        leg_to_remove_idx = i
                    else:
                        leg_to_remove_idx = j

        if leg_to_remove_idx is None or max_corr < 0.2:
            return None  # No significant correlation to remove

        new_legs = [leg for i, leg in enumerate(legs) if i != leg_to_remove_idx]
        new_predictions = [pred for i, pred in enumerate(predictions) if i != leg_to_remove_idx]

        if len(new_legs) < self.min_legs:
            return None

        return SaferAlternative(
            legs=new_legs,
            predictions=new_predictions,
            removed_legs=[legs[leg_to_remove_idx].id],
            reason=f"Removed leg with {max_corr:.2f} correlation to reduce risk",
            risk_reduction=max_corr * 0.5,  # Estimate
            ev_impact=-predictions[leg_to_remove_idx].edge,
        )

    def _remove_lowest_confidence(
        self,
        legs: List[PropLeg],
        predictions: List[ModelPrediction],
    ) -> Optional[SaferAlternative]:
        """Remove the leg with lowest confidence"""
        if len(legs) <= self.min_legs:
            return None

        # Find lowest confidence
        min_conf = float('inf')
        min_idx = 0
        for i, pred in enumerate(predictions):
            if pred.confidence < min_conf:
                min_conf = pred.confidence
                min_idx = i

        new_legs = [leg for i, leg in enumerate(legs) if i != min_idx]
        new_predictions = [pred for i, pred in enumerate(predictions) if i != min_idx]

        return SaferAlternative(
            legs=new_legs,
            predictions=new_predictions,
            removed_legs=[legs[min_idx].id],
            reason=f"Removed lowest confidence leg ({min_conf:.1%})",
            risk_reduction=(1.0 - min_conf) * 0.3,
            ev_impact=-predictions[min_idx].edge,
        )

    def _keep_distinct_games(
        self,
        legs: List[PropLeg],
        predictions: List[ModelPrediction],
    ) -> Optional[SaferAlternative]:
        """Keep only one leg per game"""
        game_to_legs = {}
        for i, leg in enumerate(legs):
            if leg.game_id not in game_to_legs:
                game_to_legs[leg.game_id] = []
            game_to_legs[leg.game_id].append((i, leg, predictions[i]))

        # If already distinct, no alternative needed
        if all(len(legs_list) == 1 for legs_list in game_to_legs.values()):
            return None

        # Keep best leg from each game
        new_legs = []
        new_predictions = []
        removed_ids = []

        for game_id, legs_list in game_to_legs.items():
            if len(legs_list) == 1:
                idx, leg, pred = legs_list[0]
                new_legs.append(leg)
                new_predictions.append(pred)
            else:
                # Keep highest confidence leg
                legs_list.sort(key=lambda x: x[2].confidence, reverse=True)
                new_legs.append(legs_list[0][1])
                new_predictions.append(legs_list[0][2])

                # Track removed legs
                for idx, leg, pred in legs_list[1:]:
                    removed_ids.append(leg.id)

        if len(new_legs) < self.min_legs or not removed_ids:
            return None

        return SaferAlternative(
            legs=new_legs,
            predictions=new_predictions,
            removed_legs=removed_ids,
            reason="Kept only one leg per game for diversification",
            risk_reduction=0.25,
            ev_impact=sum(-predictions[i].edge for i, leg in enumerate(legs) if leg.id in removed_ids),
        )

    def _remove_high_variance(
        self,
        legs: List[PropLeg],
        predictions: List[ModelPrediction],
    ) -> Optional[SaferAlternative]:
        """Remove leg with highest variance/uncertainty"""
        if len(legs) <= self.min_legs:
            return None

        # Use confidence as inverse of variance
        # Lower confidence = higher variance
        max_variance_idx = min(range(len(predictions)), key=lambda i: predictions[i].confidence)

        new_legs = [leg for i, leg in enumerate(legs) if i != max_variance_idx]
        new_predictions = [pred for i, pred in enumerate(predictions) if i != max_variance_idx]

        return SaferAlternative(
            legs=new_legs,
            predictions=new_predictions,
            removed_legs=[legs[max_variance_idx].id],
            reason="Removed highest variance leg",
            risk_reduction=(1.0 - predictions[max_variance_idx].confidence) * 0.4,
            ev_impact=-predictions[max_variance_idx].edge,
        )

    def _reduce_to_conservative(
        self,
        legs: List[PropLeg],
        predictions: List[ModelPrediction],
        target_legs: int = 3,
    ) -> Optional[SaferAlternative]:
        """Reduce slip to conservative number of legs (3)"""
        if len(legs) <= target_legs:
            return None

        # Sort by confidence * edge score
        scored_legs = [
            (i, leg, pred, pred.confidence * (1 + pred.edge))
            for i, (leg, pred) in enumerate(zip(legs, predictions))
        ]
        scored_legs.sort(key=lambda x: x[3], reverse=True)

        # Keep top N legs
        keep_indices = set(x[0] for x in scored_legs[:target_legs])

        new_legs = [leg for i, leg in enumerate(legs) if i in keep_indices]
        new_predictions = [pred for i, pred in enumerate(predictions) if i in keep_indices]
        removed_ids = [leg.id for i, leg in enumerate(legs) if i not in keep_indices]

        if not removed_ids:
            return None

        return SaferAlternative(
            legs=new_legs,
            predictions=new_predictions,
            removed_legs=removed_ids,
            reason=f"Reduced to conservative {target_legs}-leg parlay",
            risk_reduction=0.3 + 0.1 * len(removed_ids),
            ev_impact=sum(-predictions[i].edge for i, leg in enumerate(legs) if i not in keep_indices),
        )

    def _rank_alternatives(
        self,
        alternatives: List[SaferAlternative],
    ) -> List[SaferAlternative]:
        """
        Rank alternatives by risk/reward tradeoff

        Score = risk_reduction - 0.5 * abs(ev_impact)
        Higher is better (more risk reduction with less EV loss)
        """
        def score(alt: SaferAlternative) -> float:
            return alt.risk_reduction - 0.5 * abs(alt.ev_impact)

        return sorted(alternatives, key=score, reverse=True)

    def create_ladder(
        self,
        legs: List[PropLeg],
        predictions: List[ModelPrediction],
        min_legs: int = 2,
    ) -> List[SaferAlternative]:
        """
        Create a ladder of slips from aggressive to conservative

        Returns slips with decreasing leg counts: N, N-1, N-2, ..., min_legs

        Args:
            legs: Original prop legs
            predictions: Predictions for legs
            min_legs: Minimum legs to include

        Returns:
            List of alternatives ordered from most legs to least
        """
        ladder = []

        # Sort legs by confidence * edge
        scored = [
            (leg, pred, pred.confidence * (1 + pred.edge))
            for leg, pred in zip(legs, predictions)
        ]
        scored.sort(key=lambda x: x[2], reverse=True)

        # Create slips of decreasing size
        for n_legs in range(len(legs) - 1, min_legs - 1, -1):
            ladder_legs = [x[0] for x in scored[:n_legs]]
            ladder_preds = [x[1] for x in scored[:n_legs]]
            removed = [x[0].id for x in scored[n_legs:]]

            ladder.append(SaferAlternative(
                legs=ladder_legs,
                predictions=ladder_preds,
                removed_legs=removed,
                reason=f"{n_legs}-leg version (removed {len(removed)} legs)",
                risk_reduction=0.15 * len(removed),
                ev_impact=sum(-x[1].edge for x in scored[n_legs:]),
            ))

        return ladder

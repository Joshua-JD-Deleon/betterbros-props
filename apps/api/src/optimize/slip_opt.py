"""
Parlay slip optimizer with EV maximization, correlation penalties, and Kelly sizing
"""
import time
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from itertools import combinations

from src.types import ModelPrediction, PropLeg, ParlayCandidate
from .constraints import SlipConstraints, create_constraints_for_risk_mode
from .kelly import KellyCriterion, KellyResult
from .monte_carlo import MonteCarloSimulator, SimulationResult
from .safer_alt import SaferAlternativeGenerator


@dataclass
class OptimizedSlip:
    """An optimized parlay slip with full metrics"""
    legs: List[PropLeg]
    predictions: List[ModelPrediction]

    # Objective function components
    expected_value: float
    ev_percentage: float
    correlation_penalty: float
    diversity_score: float
    adjusted_score: float  # Final optimization score

    # Simulation results
    win_probability: float
    variance: float
    var_95: float
    simulation: Optional[SimulationResult] = None

    # Kelly sizing
    kelly_result: Optional[KellyResult] = None
    recommended_stake: float = 10.0

    # Risk metrics
    max_correlation: float = 0.0
    avg_correlation: float = 0.0

    # Constraint violations
    is_valid: bool = True
    violations: List[str] = field(default_factory=list)

    # Metadata
    rank: int = 0
    payout_multiplier: float = 1.0


class SlipOptimizer:
    """
    Parlay slip optimizer with advanced optimization strategies

    Objective function:
        maximize: EV - λ * Σ|ρ_ij| + μ * DiversityScore

    Where:
        - EV = expected value from Monte Carlo simulation
        - λ = correlation penalty weight
        - ρ_ij = pairwise correlations between legs
        - μ = diversity bonus weight
        - DiversityScore = # unique games / # legs
    """

    def __init__(
        self,
        correlation_penalty_weight: float = 0.15,
        diversity_bonus_weight: float = 0.05,
        n_simulations: int = 10000,
        kelly_fraction: float = 0.25,
    ):
        """
        Initialize optimizer

        Args:
            correlation_penalty_weight: λ in objective function
            diversity_bonus_weight: μ in objective function
            n_simulations: Monte Carlo simulations per slip
            kelly_fraction: Fractional Kelly to use (0.25 = 1/4 Kelly)
        """
        self.correlation_penalty_weight = correlation_penalty_weight
        self.diversity_bonus_weight = diversity_bonus_weight
        self.n_simulations = n_simulations

        self.simulator = MonteCarloSimulator(default_n_sims=n_simulations)
        self.kelly = KellyCriterion(kelly_fraction=kelly_fraction)
        self.safer_gen = SaferAlternativeGenerator()

    def optimize_slips(
        self,
        props: List[Dict],
        predictions: Dict[str, ModelPrediction],
        correlations: Dict[Tuple[str, str], float],
        risk_mode: str = "moderate",
        bankroll: float = 1000.0,
        payout_multiplier: float = 3.0,
        top_n: int = 10,
        algorithm: str = "greedy",
    ) -> List[OptimizedSlip]:
        """
        Optimize parlay slips from available props

        Args:
            props: List of available props (dicts with leg info)
            predictions: Dict mapping prop_leg_id -> ModelPrediction
            correlations: Dict mapping (leg_id_1, leg_id_2) -> correlation
            risk_mode: 'aggressive', 'moderate', or 'conservative'
            bankroll: Available bankroll for Kelly sizing
            payout_multiplier: Payout multiplier (e.g., 3.0 for 3x)
            top_n: Number of top slips to return
            algorithm: Optimization algorithm ('greedy', 'genetic', 'beam_search')

        Returns:
            List of top N OptimizedSlip instances, sorted by adjusted score
        """
        start_time = time.time()

        # Create constraints for risk mode
        constraints = create_constraints_for_risk_mode(risk_mode, bankroll)

        # Update penalty weights based on risk mode
        if risk_mode == "aggressive":
            self.correlation_penalty_weight = 0.05
        elif risk_mode == "conservative":
            self.correlation_penalty_weight = 0.30
        else:  # moderate
            self.correlation_penalty_weight = 0.15

        # Convert props to PropLeg objects
        legs = self._convert_props_to_legs(props)

        # Filter legs by minimum criteria
        filtered_legs = self._filter_legs(legs, predictions, constraints)

        if len(filtered_legs) < constraints.min_legs:
            return []

        # Choose optimization algorithm
        if algorithm == "greedy":
            candidates = self._optimize_greedy(
                filtered_legs, predictions, correlations, constraints, payout_multiplier, bankroll
            )
        elif algorithm == "genetic":
            candidates = self._optimize_genetic(
                filtered_legs, predictions, correlations, constraints, payout_multiplier, bankroll
            )
        elif algorithm == "beam_search":
            candidates = self._optimize_beam_search(
                filtered_legs, predictions, correlations, constraints, payout_multiplier, bankroll
            )
        else:
            # Default to greedy
            candidates = self._optimize_greedy(
                filtered_legs, predictions, correlations, constraints, payout_multiplier, bankroll
            )

        # Sort by adjusted score
        candidates.sort(key=lambda x: x.adjusted_score, reverse=True)

        # Assign ranks
        for i, candidate in enumerate(candidates[:top_n]):
            candidate.rank = i + 1

        elapsed = time.time() - start_time
        print(f"Optimization completed in {elapsed:.2f}s, evaluated {len(candidates)} candidates")

        return candidates[:top_n]

    def _convert_props_to_legs(self, props: List[Dict]) -> List[PropLeg]:
        """Convert prop dicts to PropLeg objects"""
        legs = []
        for prop in props:
            leg = PropLeg(
                id=prop.get("id", prop.get("prop_leg_id", "")),
                player_id=prop.get("player_id", ""),
                player_name=prop.get("player_name", ""),
                stat_type=prop.get("stat_type", ""),
                line=prop.get("line", 0.0),
                direction=prop.get("direction", "over"),
                odds=prop.get("odds"),
                team=prop.get("team", ""),
                opponent=prop.get("opponent", ""),
                game_id=prop.get("game_id", ""),
                position=prop.get("position"),
            )
            legs.append(leg)
        return legs

    def _filter_legs(
        self,
        legs: List[PropLeg],
        predictions: Dict[str, ModelPrediction],
        constraints: SlipConstraints,
    ) -> List[PropLeg]:
        """Filter legs by minimum edge and confidence"""
        filtered = []
        for leg in legs:
            pred = predictions.get(leg.id)
            if not pred:
                continue

            if pred.edge >= constraints.min_edge_per_leg and pred.confidence >= constraints.min_confidence:
                filtered.append(leg)

        return filtered

    def _optimize_greedy(
        self,
        legs: List[PropLeg],
        predictions: Dict[str, ModelPrediction],
        correlations: Dict[Tuple[str, str], float],
        constraints: SlipConstraints,
        payout_multiplier: float,
        bankroll: float,
    ) -> List[OptimizedSlip]:
        """
        Greedy optimization algorithm

        Builds slips by starting with best legs and adding compatible ones
        """
        candidates = []

        # Sort legs by edge * confidence
        sorted_legs = sorted(
            legs,
            key=lambda leg: predictions[leg.id].edge * predictions[leg.id].confidence,
            reverse=True
        )

        # Try building slips starting from each high-value leg
        for start_idx in range(min(10, len(sorted_legs))):
            for n_legs in range(constraints.min_legs, constraints.max_legs + 1):
                slip_legs = self._build_greedy_slip(
                    sorted_legs[start_idx:],
                    predictions,
                    correlations,
                    constraints,
                    n_legs,
                )

                if slip_legs:
                    slip = self._evaluate_slip(
                        slip_legs, predictions, correlations, constraints, payout_multiplier, bankroll
                    )
                    if slip.is_valid:
                        candidates.append(slip)

        # Also try random combinations for diversity
        for _ in range(20):
            n_legs = np.random.randint(constraints.min_legs, constraints.max_legs + 1)
            if len(legs) >= n_legs:
                random_legs = np.random.choice(legs, size=n_legs, replace=False).tolist()
                slip = self._evaluate_slip(
                    random_legs, predictions, correlations, constraints, payout_multiplier, bankroll
                )
                if slip.is_valid:
                    candidates.append(slip)

        return candidates

    def _build_greedy_slip(
        self,
        available_legs: List[PropLeg],
        predictions: Dict[str, ModelPrediction],
        correlations: Dict[Tuple[str, str], float],
        constraints: SlipConstraints,
        target_legs: int,
    ) -> Optional[List[PropLeg]]:
        """Build a slip greedily from available legs"""
        slip_legs = []

        for leg in available_legs:
            if len(slip_legs) >= target_legs:
                break

            # Check if adding this leg violates constraints
            test_legs = slip_legs + [leg]
            is_valid, _ = constraints.validate_slip(
                test_legs,
                correlations=correlations,
                ev=None,  # Will check later
                confidence=None,
            )

            if is_valid:
                slip_legs.append(leg)

        if len(slip_legs) >= constraints.min_legs:
            return slip_legs
        return None

    def _optimize_genetic(
        self,
        legs: List[PropLeg],
        predictions: Dict[str, ModelPrediction],
        correlations: Dict[Tuple[str, str], float],
        constraints: SlipConstraints,
        payout_multiplier: float,
        bankroll: float,
        population_size: int = 50,
        generations: int = 20,
    ) -> List[OptimizedSlip]:
        """
        Genetic algorithm optimization

        Evolves population of slips over multiple generations
        """
        # Initialize population with random slips
        population = []
        for _ in range(population_size):
            n_legs = np.random.randint(constraints.min_legs, constraints.max_legs + 1)
            if len(legs) >= n_legs:
                random_legs = np.random.choice(legs, size=n_legs, replace=False).tolist()
                slip = self._evaluate_slip(
                    random_legs, predictions, correlations, constraints, payout_multiplier, bankroll
                )
                population.append(slip)

        # Evolve over generations
        for generation in range(generations):
            # Sort by fitness
            population.sort(key=lambda x: x.adjusted_score, reverse=True)

            # Keep top 50%
            survivors = population[:population_size // 2]

            # Generate offspring
            offspring = []
            for _ in range(population_size - len(survivors)):
                # Select two parents
                parent1 = np.random.choice(survivors)
                parent2 = np.random.choice(survivors)

                # Crossover
                child_legs = self._crossover(parent1.legs, parent2.legs)

                # Mutate
                if np.random.random() < 0.2:
                    child_legs = self._mutate(child_legs, legs)

                # Evaluate
                child = self._evaluate_slip(
                    child_legs, predictions, correlations, constraints, payout_multiplier, bankroll
                )
                offspring.append(child)

            population = survivors + offspring

        # Return all evaluated slips
        return population

    def _crossover(self, legs1: List[PropLeg], legs2: List[PropLeg]) -> List[PropLeg]:
        """Crossover two parent slips"""
        # Combine and deduplicate
        combined = list(set(legs1 + legs2))

        # Take random subset
        n_legs = np.random.randint(2, min(6, len(combined)) + 1)
        return list(np.random.choice(combined, size=min(n_legs, len(combined)), replace=False))

    def _mutate(self, slip_legs: List[PropLeg], available_legs: List[PropLeg]) -> List[PropLeg]:
        """Mutate a slip by replacing a random leg"""
        if not slip_legs or not available_legs:
            return slip_legs

        # Remove random leg
        mutated = slip_legs.copy()
        if mutated:
            mutated.pop(np.random.randint(len(mutated)))

        # Add random leg
        available = [leg for leg in available_legs if leg not in mutated]
        if available:
            mutated.append(np.random.choice(available))

        return mutated

    def _optimize_beam_search(
        self,
        legs: List[PropLeg],
        predictions: Dict[str, ModelPrediction],
        correlations: Dict[Tuple[str, str], float],
        constraints: SlipConstraints,
        payout_multiplier: float,
        bankroll: float,
        beam_width: int = 10,
    ) -> List[OptimizedSlip]:
        """
        Beam search optimization

        Maintains top K partial slips at each level
        """
        # Start with single legs
        beams = [[leg] for leg in legs[:beam_width * 2]]

        all_candidates = []

        for level in range(1, constraints.max_legs):
            new_beams = []

            for beam in beams:
                # Try adding each available leg
                for leg in legs:
                    if leg in beam:
                        continue

                    new_beam = beam + [leg]

                    # Check constraints
                    is_valid, _ = constraints.validate_slip(
                        new_beam, correlations=correlations
                    )

                    if is_valid:
                        # Evaluate
                        slip = self._evaluate_slip(
                            new_beam, predictions, correlations, constraints, payout_multiplier, bankroll
                        )

                        if slip.is_valid:
                            new_beams.append(new_beam)
                            if len(new_beam) >= constraints.min_legs:
                                all_candidates.append(slip)

            # Keep top K beams
            new_beams.sort(key=lambda b: sum(predictions[leg.id].edge for leg in b), reverse=True)
            beams = new_beams[:beam_width]

            if not beams:
                break

        return all_candidates

    def _evaluate_slip(
        self,
        legs: List[PropLeg],
        predictions: Dict[str, ModelPrediction],
        correlations: Dict[Tuple[str, str], float],
        constraints: SlipConstraints,
        payout_multiplier: float,
        bankroll: float,
    ) -> OptimizedSlip:
        """
        Evaluate a slip and calculate all metrics

        This is where the objective function is calculated
        """
        # Get predictions for legs
        leg_predictions = [predictions[leg.id] for leg in legs]

        # Build correlation matrix
        n_legs = len(legs)
        corr_matrix = np.zeros((n_legs, n_legs))
        for i in range(n_legs):
            for j in range(n_legs):
                if i == j:
                    corr_matrix[i, j] = 1.0
                else:
                    key = (legs[i].id, legs[j].id)
                    reverse_key = (legs[j].id, legs[i].id)
                    corr_matrix[i, j] = correlations.get(key, correlations.get(reverse_key, 0.0))

        # Calculate correlation metrics
        corr_sum = 0.0
        pair_count = 0
        max_corr = 0.0

        for i in range(n_legs):
            for j in range(i + 1, n_legs):
                corr = abs(corr_matrix[i, j])
                corr_sum += corr
                pair_count += 1
                max_corr = max(max_corr, corr)

        avg_corr = corr_sum / pair_count if pair_count > 0 else 0.0

        # Run Monte Carlo simulation
        simulation = self.simulator.simulate_slip(
            legs=legs,
            predictions=leg_predictions,
            payout_multiplier=payout_multiplier,
            stake=10.0,  # Base stake for EV calculation
            correlation_matrix=corr_matrix,
            n_sims=self.n_simulations,
        )

        # Calculate diversity score
        diversity = constraints.calculate_diversity_score(legs)

        # Calculate objective function
        # maximize: EV - λ * Σ|ρ_ij| + μ * DiversityScore
        correlation_penalty = self.correlation_penalty_weight * corr_sum
        diversity_bonus = self.diversity_bonus_weight * diversity
        adjusted_score = simulation.ev_percentage - correlation_penalty + diversity_bonus

        # Validate against constraints
        is_valid, violations = constraints.validate_slip(
            legs,
            correlations=correlations,
            ev=simulation.ev_percentage,
            confidence=simulation.win_probability,
        )

        # Kelly sizing
        kelly_result = self.kelly.calculate_stake(
            ev=simulation.ev_percentage,
            variance=simulation.variance,
            bankroll=bankroll,
            win_prob=simulation.win_probability,
            payout_multiplier=payout_multiplier,
        )

        return OptimizedSlip(
            legs=legs,
            predictions=leg_predictions,
            expected_value=simulation.expected_value,
            ev_percentage=simulation.ev_percentage,
            correlation_penalty=correlation_penalty,
            diversity_score=diversity,
            adjusted_score=adjusted_score,
            win_probability=simulation.win_probability,
            variance=simulation.variance,
            var_95=simulation.var_95,
            simulation=simulation,
            kelly_result=kelly_result,
            recommended_stake=kelly_result.stake_amount,
            max_correlation=max_corr,
            avg_correlation=avg_corr,
            is_valid=is_valid,
            violations=violations,
            payout_multiplier=payout_multiplier,
        )

    def generate_safer_alternatives(
        self,
        slip: OptimizedSlip,
        correlations: Dict[Tuple[str, str], float],
    ) -> List[OptimizedSlip]:
        """
        Generate safer alternatives for a slip

        Args:
            slip: Original optimized slip
            correlations: Correlation matrix

        Returns:
            List of safer alternative slips
        """
        alternatives = self.safer_gen.generate_safer_version(
            legs=slip.legs,
            predictions=slip.predictions,
            correlation_matrix=correlations,
            max_alternatives=3,
        )

        # Convert to OptimizedSlip
        # (Would need to re-evaluate each alternative - simplified here)
        return []  # Placeholder

"""
Example usage of the parlay slip optimizer

This demonstrates how to use the optimizer in production.
"""
import numpy as np
from datetime import datetime
from typing import Dict, List

from src.types import (
    ModelPrediction,
    PropLeg,
    BetDirection,
    ModelType,
)
from src.optimize import (
    SlipOptimizer,
    SlipConstraints,
    create_constraints_for_risk_mode,
    MonteCarloSimulator,
    KellyCriterion,
    SaferAlternativeGenerator,
)


def create_sample_props() -> List[Dict]:
    """Create sample prop data for testing"""
    props = [
        {
            "id": "leg_1",
            "player_id": "player_1",
            "player_name": "LeBron James",
            "stat_type": "points",
            "line": 25.5,
            "direction": "over",
            "team": "LAL",
            "opponent": "BOS",
            "game_id": "game_1",
            "position": "F",
        },
        {
            "id": "leg_2",
            "player_id": "player_2",
            "player_name": "Stephen Curry",
            "stat_type": "three_pointers",
            "line": 4.5,
            "direction": "over",
            "team": "GSW",
            "opponent": "PHX",
            "game_id": "game_2",
            "position": "G",
        },
        {
            "id": "leg_3",
            "player_id": "player_3",
            "player_name": "Giannis Antetokounmpo",
            "stat_type": "rebounds",
            "line": 11.5,
            "direction": "over",
            "team": "MIL",
            "opponent": "CHI",
            "game_id": "game_3",
            "position": "F",
        },
        {
            "id": "leg_4",
            "player_id": "player_4",
            "player_name": "Luka Doncic",
            "stat_type": "assists",
            "line": 8.5,
            "direction": "over",
            "team": "DAL",
            "opponent": "HOU",
            "game_id": "game_4",
            "position": "G",
        },
        {
            "id": "leg_5",
            "player_id": "player_5",
            "player_name": "Joel Embiid",
            "stat_type": "points",
            "line": 28.5,
            "direction": "over",
            "team": "PHI",
            "opponent": "MIA",
            "game_id": "game_5",
            "position": "C",
        },
        {
            "id": "leg_6",
            "player_id": "player_1",
            "player_name": "LeBron James",
            "stat_type": "assists",
            "line": 7.5,
            "direction": "over",
            "team": "LAL",
            "opponent": "BOS",
            "game_id": "game_1",
            "position": "F",
        },
    ]
    return props


def create_sample_predictions() -> Dict[str, ModelPrediction]:
    """Create sample predictions for props"""
    predictions = {
        "leg_1": ModelPrediction(
            prop_leg_id="leg_1",
            player_id="player_1",
            stat_type="points",
            predicted_value=27.2,
            line_value=25.5,
            prob_over=0.68,
            prob_under=0.32,
            confidence=0.72,
            edge=0.08,
            model_type=ModelType.ENSEMBLE,
            model_version="v1.0.0",
        ),
        "leg_2": ModelPrediction(
            prop_leg_id="leg_2",
            player_id="player_2",
            stat_type="three_pointers",
            predicted_value=5.1,
            line_value=4.5,
            prob_over=0.65,
            prob_under=0.35,
            confidence=0.68,
            edge=0.06,
            model_type=ModelType.ENSEMBLE,
            model_version="v1.0.0",
        ),
        "leg_3": ModelPrediction(
            prop_leg_id="leg_3",
            player_id="player_3",
            stat_type="rebounds",
            predicted_value=12.8,
            line_value=11.5,
            prob_over=0.70,
            prob_under=0.30,
            confidence=0.75,
            edge=0.10,
            model_type=ModelType.ENSEMBLE,
            model_version="v1.0.0",
        ),
        "leg_4": ModelPrediction(
            prop_leg_id="leg_4",
            player_id="player_4",
            stat_type="assists",
            predicted_value=9.3,
            line_value=8.5,
            prob_over=0.64,
            prob_under=0.36,
            confidence=0.66,
            edge=0.05,
            model_type=ModelType.ENSEMBLE,
            model_version="v1.0.0",
        ),
        "leg_5": ModelPrediction(
            prop_leg_id="leg_5",
            player_id="player_5",
            stat_type="points",
            predicted_value=30.5,
            line_value=28.5,
            prob_over=0.66,
            prob_under=0.34,
            confidence=0.69,
            edge=0.07,
            model_type=ModelType.ENSEMBLE,
            model_version="v1.0.0",
        ),
        "leg_6": ModelPrediction(
            prop_leg_id="leg_6",
            player_id="player_1",
            stat_type="assists",
            line_value=7.5,
            predicted_value=8.2,
            prob_over=0.63,
            prob_under=0.37,
            confidence=0.65,
            edge=0.04,
            model_type=ModelType.ENSEMBLE,
            model_version="v1.0.0",
        ),
    }
    return predictions


def create_sample_correlations() -> Dict:
    """Create sample correlation matrix"""
    correlations = {
        # Same player correlations (LeBron points + assists)
        ("leg_1", "leg_6"): 0.35,
        ("leg_6", "leg_1"): 0.35,

        # Same game negative correlation (guards vs forwards)
        ("leg_1", "leg_2"): -0.05,
        ("leg_2", "leg_1"): -0.05,

        # Low correlations for other pairs
        ("leg_1", "leg_3"): 0.02,
        ("leg_1", "leg_4"): 0.01,
        ("leg_1", "leg_5"): 0.03,
        ("leg_2", "leg_3"): 0.01,
        ("leg_2", "leg_4"): 0.04,
        ("leg_2", "leg_5"): -0.02,
        ("leg_3", "leg_4"): 0.02,
        ("leg_3", "leg_5"): 0.05,
        ("leg_4", "leg_5"): 0.01,
    }
    return correlations


def example_basic_optimization():
    """Example: Basic slip optimization"""
    print("=" * 60)
    print("Example 1: Basic Slip Optimization")
    print("=" * 60)

    # Setup
    props = create_sample_props()
    predictions = create_sample_predictions()
    correlations = create_sample_correlations()

    # Initialize optimizer
    optimizer = SlipOptimizer(
        correlation_penalty_weight=0.15,
        diversity_bonus_weight=0.05,
        n_simulations=10000,
        kelly_fraction=0.25,
    )

    # Optimize
    slips = optimizer.optimize_slips(
        props=props,
        predictions=predictions,
        correlations=correlations,
        risk_mode="moderate",
        bankroll=1000.0,
        payout_multiplier=3.0,
        top_n=5,
        algorithm="greedy",
    )

    # Display results
    print(f"\nFound {len(slips)} optimized slips:\n")

    for i, slip in enumerate(slips, 1):
        print(f"Slip #{i} (Rank {slip.rank})")
        print(f"  Legs: {len(slip.legs)}")
        for leg in slip.legs:
            print(f"    - {leg.player_name}: {leg.stat_type} {leg.direction} {leg.line}")

        print(f"  EV: {slip.ev_percentage:.2%}")
        print(f"  Win Probability: {slip.win_probability:.2%}")
        print(f"  Recommended Stake: ${slip.recommended_stake:.2f}")
        print(f"  Diversity Score: {slip.diversity_score:.2f}")
        print(f"  Max Correlation: {slip.max_correlation:.3f}")
        print(f"  Adjusted Score: {slip.adjusted_score:.4f}")

        if slip.violations:
            print(f"  Violations: {', '.join(slip.violations)}")

        print()


def example_risk_modes():
    """Example: Compare different risk modes"""
    print("=" * 60)
    print("Example 2: Risk Mode Comparison")
    print("=" * 60)

    props = create_sample_props()
    predictions = create_sample_predictions()
    correlations = create_sample_correlations()

    optimizer = SlipOptimizer()

    for risk_mode in ["conservative", "moderate", "aggressive"]:
        print(f"\n{risk_mode.upper()} Mode:")

        slips = optimizer.optimize_slips(
            props=props,
            predictions=predictions,
            correlations=correlations,
            risk_mode=risk_mode,
            bankroll=1000.0,
            payout_multiplier=3.0,
            top_n=1,
            algorithm="greedy",
        )

        if slips:
            slip = slips[0]
            print(f"  Legs: {len(slip.legs)}")
            print(f"  EV: {slip.ev_percentage:.2%}")
            print(f"  Win Prob: {slip.win_probability:.2%}")
            print(f"  Stake: ${slip.recommended_stake:.2f}")
            print(f"  Max Correlation: {slip.max_correlation:.3f}")


def example_monte_carlo():
    """Example: Direct Monte Carlo simulation"""
    print("=" * 60)
    print("Example 3: Monte Carlo Simulation")
    print("=" * 60)

    props = create_sample_props()[:3]  # Use first 3 legs
    predictions = create_sample_predictions()

    # Convert to PropLeg objects
    legs = []
    leg_predictions = []
    for prop in props:
        leg = PropLeg(
            id=prop["id"],
            player_id=prop["player_id"],
            player_name=prop["player_name"],
            stat_type=prop["stat_type"],
            line=prop["line"],
            direction=BetDirection.OVER,
            team=prop["team"],
            opponent=prop["opponent"],
            game_id=prop["game_id"],
            position=prop.get("position"),
        )
        legs.append(leg)
        leg_predictions.append(predictions[prop["id"]])

    # Run simulation
    simulator = MonteCarloSimulator(default_n_sims=10000)
    result = simulator.simulate_slip(
        legs=legs,
        predictions=leg_predictions,
        payout_multiplier=3.0,
        stake=10.0,
    )

    print("\nSimulation Results:")
    print(f"  Win Probability: {result.win_probability:.2%}")
    print(f"  Expected Value: ${result.expected_value:.2f}")
    print(f"  EV Percentage: {result.ev_percentage:.2%}")
    print(f"  Variance: {result.variance:.2f}")
    print(f"  VaR (95%): ${result.var_95:.2f}")
    print(f"\n  Percentiles:")
    print(f"    5th:  ${result.percentile_5:.2f}")
    print(f"    25th: ${result.percentile_25:.2f}")
    print(f"    50th: ${result.percentile_50:.2f}")
    print(f"    75th: ${result.percentile_75:.2f}")
    print(f"    95th: ${result.percentile_95:.2f}")


def example_kelly_sizing():
    """Example: Kelly Criterion stake sizing"""
    print("=" * 60)
    print("Example 4: Kelly Criterion Stake Sizing")
    print("=" * 60)

    kelly = KellyCriterion(
        min_stake=5.0,
        max_stake=50.0,
        kelly_fraction=0.25,
    )

    scenarios = [
        {"ev": 0.15, "variance": 0.5, "bankroll": 1000, "desc": "High EV, Moderate Risk"},
        {"ev": 0.08, "variance": 0.3, "bankroll": 1000, "desc": "Moderate EV, Low Risk"},
        {"ev": 0.20, "variance": 1.2, "bankroll": 1000, "desc": "High EV, High Risk"},
        {"ev": 0.05, "variance": 0.2, "bankroll": 500, "desc": "Low EV, Low Bankroll"},
    ]

    for scenario in scenarios:
        result = kelly.calculate_stake(
            ev=scenario["ev"],
            variance=scenario["variance"],
            bankroll=scenario["bankroll"],
        )

        print(f"\n{scenario['desc']}:")
        print(f"  Full Kelly: {result.full_kelly:.2%} of bankroll")
        print(f"  Fractional Kelly (1/4): {result.fractional_kelly:.2%}")
        print(f"  Recommended Stake: ${result.stake_amount:.2f}")
        if result.reason:
            print(f"  Note: {result.reason}")


def example_safer_alternatives():
    """Example: Generate safer alternatives"""
    print("=" * 60)
    print("Example 5: Safer Alternative Generation")
    print("=" * 60)

    props = create_sample_props()
    predictions = create_sample_predictions()
    correlations = create_sample_correlations()

    # Create a risky slip (all 6 legs)
    legs = []
    leg_predictions = []
    for prop in props:
        leg = PropLeg(
            id=prop["id"],
            player_id=prop["player_id"],
            player_name=prop["player_name"],
            stat_type=prop["stat_type"],
            line=prop["line"],
            direction=BetDirection.OVER,
            team=prop["team"],
            opponent=prop["opponent"],
            game_id=prop["game_id"],
            position=prop.get("position"),
        )
        legs.append(leg)
        leg_predictions.append(predictions[prop["id"]])

    print(f"Original Slip: {len(legs)} legs")
    for leg in legs:
        print(f"  - {leg.player_name}: {leg.stat_type}")

    # Generate safer alternatives
    safer_gen = SaferAlternativeGenerator()
    alternatives = safer_gen.generate_safer_version(
        legs=legs,
        predictions=leg_predictions,
        correlation_matrix=correlations,
        max_alternatives=3,
    )

    print(f"\nGenerated {len(alternatives)} safer alternatives:\n")

    for i, alt in enumerate(alternatives, 1):
        print(f"Alternative #{i}:")
        print(f"  Reason: {alt.reason}")
        print(f"  Legs: {len(alt.legs)}")
        print(f"  Removed: {len(alt.removed_legs)} legs")
        print(f"  Risk Reduction: {alt.risk_reduction:.2%}")
        print(f"  EV Impact: {alt.ev_impact:.3f}")
        print()


if __name__ == "__main__":
    # Run all examples
    example_basic_optimization()
    example_risk_modes()
    example_monte_carlo()
    example_kelly_sizing()
    example_safer_alternatives()

    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)

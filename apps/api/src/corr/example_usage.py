"""
Example usage of the correlation modeling system

Demonstrates how to use the correlation analysis, copula modeling,
and sampling components for parlay analysis.
"""
import asyncio
import numpy as np
from datetime import datetime

from src.types import PropLeg, BetDirection
from src.corr import (
    CorrelationAnalyzer,
    CopulaModel,
    CopulaType,
    CorrelatedSampler,
    CorrelationConstraints,
    CorrelationWarningLevel,
)


async def example_basic_correlation_analysis():
    """Example 1: Basic correlation analysis"""
    print("\n" + "="*80)
    print("Example 1: Basic Correlation Analysis")
    print("="*80)

    # Create sample props
    props = [
        PropLeg(
            id="1",
            player_id="mahomes",
            player_name="Patrick Mahomes",
            stat_type="passing_yards",
            line=275.5,
            direction=BetDirection.OVER,
            odds=1.9,
            team="KC",
            opponent="LAC",
            game_id="game_1",
            position="QB"
        ),
        PropLeg(
            id="2",
            player_id="mahomes",
            player_name="Patrick Mahomes",
            stat_type="passing_tds",
            line=2.5,
            direction=BetDirection.OVER,
            odds=1.85,
            team="KC",
            opponent="LAC",
            game_id="game_1",
            position="QB"
        ),
        PropLeg(
            id="3",
            player_id="kelce",
            player_name="Travis Kelce",
            stat_type="receptions",
            line=5.5,
            direction=BetDirection.OVER,
            odds=1.95,
            team="KC",
            opponent="LAC",
            game_id="game_1",
            position="TE"
        ),
    ]

    # Initialize analyzer (without Redis for example)
    analyzer = CorrelationAnalyzer(redis_client=None)

    # Estimate correlation matrix
    corr_matrix = await analyzer.estimate_correlation_matrix(props, use_cache=False)

    print("\nProp Legs:")
    for i, prop in enumerate(props):
        print(f"  {i}: {prop.player_name} {prop.stat_type} {prop.direction}")

    print("\nCorrelation Matrix:")
    print(corr_matrix)

    # Get pairwise correlations
    print("\nPairwise Correlations:")
    for i in range(len(props)):
        for j in range(i + 1, len(props)):
            corr = await analyzer.get_pairwise_correlation(props[i], props[j])
            print(
                f"  {props[i].player_name} {props[i].stat_type} <-> "
                f"{props[j].player_name} {props[j].stat_type}: {corr:.3f}"
            )

    # Get correlation statistics
    stats = await analyzer.get_correlation_stats(props)
    print("\nCorrelation Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value:.4f}")


async def example_copula_modeling():
    """Example 2: Copula modeling and sampling"""
    print("\n" + "="*80)
    print("Example 2: Copula Modeling and Sampling")
    print("="*80)

    # Define correlation matrix
    correlation_matrix = np.array([
        [1.0, 0.65, 0.45],
        [0.65, 1.0, 0.50],
        [0.45, 0.50, 1.0]
    ])

    print("\nTarget Correlation Matrix:")
    print(correlation_matrix)

    # Fit Gaussian copula
    copula = CopulaModel(copula_type=CopulaType.GAUSSIAN, random_seed=42)
    copula.fit_copula(
        correlation_matrix=correlation_matrix,
        variable_names=["yards", "tds", "completions"]
    )

    print(f"\nFitted {copula.copula_type} copula with {copula.n_variables} variables")

    # Generate samples
    n_samples = 10000
    samples = copula.sample(n_samples=n_samples, return_uniform=True)

    print(f"\nGenerated {n_samples} samples")
    print(f"Sample shape: {samples.shape}")
    print(f"Sample range: [{samples.min():.3f}, {samples.max():.3f}]")

    # Validate samples
    validation = copula.validate_samples(samples, target_correlation=correlation_matrix)

    print("\nValidation Results:")
    print(f"  Frobenius norm error: {validation['frobenius_norm_error']:.6f}")
    print(f"  Max elementwise error: {validation['max_elementwise_error']:.6f}")


async def example_correlated_sampling():
    """Example 3: Correlated binary outcome sampling"""
    print("\n" + "="*80)
    print("Example 3: Correlated Binary Outcome Sampling")
    print("="*80)

    # Create sample props
    props = [
        PropLeg(
            id="1",
            player_id="lebron",
            player_name="LeBron James",
            stat_type="points",
            line=25.5,
            direction=BetDirection.OVER,
            odds=1.9,
            team="LAL",
            opponent="GSW",
            game_id="game_1",
            position="F"
        ),
        PropLeg(
            id="2",
            player_id="lebron",
            player_name="LeBron James",
            stat_type="rebounds",
            line=7.5,
            direction=BetDirection.OVER,
            odds=1.85,
            team="LAL",
            opponent="GSW",
            game_id="game_1",
            position="F"
        ),
        PropLeg(
            id="3",
            player_id="curry",
            player_name="Stephen Curry",
            stat_type="points",
            line=28.5,
            direction=BetDirection.OVER,
            odds=1.92,
            team="GSW",
            opponent="LAL",
            game_id="game_1",
            position="G"
        ),
    ]

    # Model-predicted probabilities
    probabilities = [0.58, 0.52, 0.61]

    print("\nProp Legs and Probabilities:")
    for prop, prob in zip(props, probabilities):
        print(f"  {prop.player_name} {prop.stat_type} {prop.direction}: P={prob:.2f}")

    # Initialize sampler (without Redis for example)
    sampler = CorrelatedSampler(
        redis_client=None,
        copula_type=CopulaType.GAUSSIAN,
        random_seed=42
    )

    # Generate correlated samples
    n_sims = 10000
    samples = await sampler.generate_samples(
        props=props,
        probabilities=probabilities,
        n_sims=n_sims,
        use_cache=False
    )

    print(f"\nGenerated {n_sims} correlated binary samples")
    print(f"Sample shape: {samples.shape}")

    # Analyze results
    print("\nEmpirical Hit Rates:")
    for i, (prop, prob) in enumerate(zip(props, probabilities)):
        empirical_rate = samples[:, i].mean()
        print(
            f"  {prop.player_name} {prop.stat_type}: "
            f"Empirical={empirical_rate:.4f}, Target={prob:.4f}, "
            f"Error={abs(empirical_rate - prob):.4f}"
        )

    # Parlay analysis
    all_hit = (samples.sum(axis=1) == len(props)).mean()
    independent_prob = np.prod(probabilities)

    print(f"\nParlay Analysis (all {len(props)} props hit):")
    print(f"  Correlated probability: {all_hit:.4f}")
    print(f"  Independent probability: {independent_prob:.4f}")
    print(f"  Correlation impact: {all_hit - independent_prob:.4f}")

    # Sample statistics
    stats = await sampler.get_sample_statistics(samples, props)
    print(f"\nAverage props hit per simulation: {stats['avg_props_hit']:.2f}")


async def example_constraint_checking():
    """Example 4: Correlation constraint enforcement"""
    print("\n" + "="*80)
    print("Example 4: Correlation Constraint Enforcement")
    print("="*80)

    # Create props with varying correlation levels
    props_green = [
        PropLeg(
            id="1",
            player_id="player1",
            player_name="Player One",
            stat_type="points",
            line=20.5,
            direction=BetDirection.OVER,
            odds=1.9,
            team="TEAM1",
            opponent="TEAM2",
            game_id="game_1",
            position="G"
        ),
        PropLeg(
            id="2",
            player_id="player2",
            player_name="Player Two",
            stat_type="rebounds",
            line=8.5,
            direction=BetDirection.OVER,
            odds=1.85,
            team="TEAM2",
            opponent="TEAM1",
            game_id="game_2",
            position="F"
        ),
    ]

    props_red = [
        PropLeg(
            id="1",
            player_id="mahomes",
            player_name="Patrick Mahomes",
            stat_type="passing_yards",
            line=275.5,
            direction=BetDirection.OVER,
            odds=1.9,
            team="KC",
            opponent="LAC",
            game_id="game_1",
            position="QB"
        ),
        PropLeg(
            id="2",
            player_id="mahomes",
            player_name="Patrick Mahomes",
            stat_type="passing_yards",
            line=275.5,
            direction=BetDirection.OVER,
            odds=1.9,
            team="KC",
            opponent="LAC",
            game_id="game_1",
            position="QB"
        ),
    ]

    # Initialize constraints
    constraints = CorrelationConstraints(
        green_threshold=0.35,
        yellow_threshold=0.75
    )

    print("\nCorrelation Thresholds:")
    thresholds = constraints.get_thresholds()
    for key, value in thresholds.items():
        print(f"  {key}: {value}")

    # Test GREEN correlation
    print("\nTest 1: Low correlation (GREEN)")
    is_valid, report = await constraints.check_all_constraints(
        props_green,
        allow_yellow=True
    )
    print(f"  Valid: {is_valid}")
    print(f"  Max correlation: {report['max_correlation']:.3f}")
    if report['violations']:
        print(f"  Violations: {report['violations']}")

    # Test RED correlation (duplicate prop)
    print("\nTest 2: Same player/stat (RED)")
    is_valid, violations = constraints.same_player_same_stat_block(props_red)
    print(f"  Valid: {is_valid}")
    if violations:
        print(f"  Violations: {violations}")

    # Test diversity constraints
    print("\nTest 3: Diversity constraints")
    is_valid, violations = await constraints.enforce_diversity(
        props_green,
        min_games=2,
        min_players=2,
        max_same_game=2
    )
    print(f"  Valid: {is_valid}")
    if violations:
        print(f"  Violations: {violations}")


async def example_full_workflow():
    """Example 5: Complete workflow"""
    print("\n" + "="*80)
    print("Example 5: Complete Workflow - Parlay Analysis")
    print("="*80)

    # Define a 4-leg parlay
    props = [
        PropLeg(
            id="1",
            player_id="mahomes",
            player_name="Patrick Mahomes",
            stat_type="passing_yards",
            line=275.5,
            direction=BetDirection.OVER,
            odds=1.9,
            team="KC",
            opponent="LAC",
            game_id="game_1",
            position="QB"
        ),
        PropLeg(
            id="2",
            player_id="kelce",
            player_name="Travis Kelce",
            stat_type="receptions",
            line=5.5,
            direction=BetDirection.OVER,
            odds=1.95,
            team="KC",
            opponent="LAC",
            game_id="game_1",
            position="TE"
        ),
        PropLeg(
            id="3",
            player_id="herbert",
            player_name="Justin Herbert",
            stat_type="passing_yards",
            line=268.5,
            direction=BetDirection.OVER,
            odds=1.92,
            team="LAC",
            opponent="KC",
            game_id="game_1",
            position="QB"
        ),
        PropLeg(
            id="4",
            player_id="allen",
            player_name="Keenan Allen",
            stat_type="receiving_yards",
            line=62.5,
            direction=BetDirection.OVER,
            odds=1.88,
            team="LAC",
            opponent="KC",
            game_id="game_1",
            position="WR"
        ),
    ]

    probabilities = [0.55, 0.60, 0.52, 0.58]

    print("\n4-Leg Parlay:")
    for i, (prop, prob) in enumerate(zip(props, probabilities)):
        print(
            f"  {i+1}. {prop.player_name} {prop.stat_type} {prop.direction} "
            f"{prop.line} (P={prob:.2f})"
        )

    # Step 1: Check constraints
    print("\nStep 1: Checking constraints...")
    constraints = CorrelationConstraints()
    is_valid, report = await constraints.check_all_constraints(
        props,
        allow_yellow=True,
        min_games=1,
        max_same_game=4
    )

    print(f"  Valid: {is_valid}")
    print(f"  Max correlation: {report['max_correlation']:.3f}")
    if report['warnings']:
        print(f"  Warnings: {len(report['warnings'])}")
    if report['violations']:
        print(f"  Violations: {report['violations']}")

    # Step 2: Analyze correlation structure
    print("\nStep 2: Analyzing correlation structure...")
    analyzer = CorrelationAnalyzer(redis_client=None)
    corr_matrix = await analyzer.estimate_correlation_matrix(props, use_cache=False)

    print("  Correlation matrix:")
    for i in range(len(props)):
        row_str = "    "
        for j in range(len(props)):
            row_str += f"{corr_matrix[i, j]:6.3f} "
        print(row_str)

    # Step 3: Generate correlated samples
    print("\nStep 3: Running Monte Carlo simulation...")
    sampler = CorrelatedSampler(redis_client=None, random_seed=42)

    samples = await sampler.generate_samples(
        props=props,
        probabilities=probabilities,
        n_sims=10000,
        correlation_matrix=corr_matrix,
        use_cache=False
    )

    # Step 4: Analyze results
    print("\nStep 4: Analyzing results...")

    # Individual hit rates
    print("\n  Individual prop performance:")
    for i, (prop, prob) in enumerate(zip(props, probabilities)):
        empirical = samples[:, i].mean()
        print(
            f"    {prop.player_name} {prop.stat_type}: "
            f"{empirical:.4f} (target: {prob:.4f})"
        )

    # Parlay outcomes
    print("\n  Parlay outcomes:")
    for n_hits in range(len(props) + 1):
        hit_rate = (samples.sum(axis=1) == n_hits).mean()
        print(f"    {n_hits}/{len(props)} props hit: {hit_rate:.4f}")

    # Win probability
    all_hit = (samples.sum(axis=1) == len(props)).mean()
    independent_prob = np.prod(probabilities)

    print(f"\n  Parlay win probability:")
    print(f"    Correlated: {all_hit:.4f}")
    print(f"    Independent: {independent_prob:.4f}")
    print(f"    Impact: {all_hit - independent_prob:+.4f}")

    # Expected value (assuming 3x payout for 4-leg parlay)
    payout = 3.0
    ev_correlated = all_hit * payout - 1
    ev_independent = independent_prob * payout - 1

    print(f"\n  Expected value (3x payout):")
    print(f"    Correlated EV: {ev_correlated:+.4f}")
    print(f"    Independent EV: {ev_independent:+.4f}")

    # Correlation penalty
    penalty = await constraints.compute_correlation_penalty(props)
    print(f"\n  Correlation penalty: {penalty:.4f}")


async def main():
    """Run all examples"""
    print("\n" + "#"*80)
    print("# Correlation Modeling System - Usage Examples")
    print("#"*80)

    await example_basic_correlation_analysis()
    await example_copula_modeling()
    await example_correlated_sampling()
    await example_constraint_checking()
    await example_full_workflow()

    print("\n" + "#"*80)
    print("# Examples completed successfully!")
    print("#"*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

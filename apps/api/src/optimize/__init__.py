"""
Parlay slip optimization module

This module provides comprehensive parlay slip optimization with:
- EV maximization with correlation penalties
- Monte Carlo simulation for outcome prediction
- Kelly Criterion stake sizing
- Risk-based constraint systems
- Safer alternative generation

Main Components:
- SlipOptimizer: Main optimization engine
- SlipConstraints: Constraint validation and configuration
- KellyCriterion: Optimal stake sizing
- MonteCarloSimulator: Outcome simulation
- SaferAlternativeGenerator: Risk reduction alternatives
"""

from .slip_opt import SlipOptimizer, OptimizedSlip
from .constraints import (
    SlipConstraints,
    create_constraints_for_risk_mode,
)
from .kelly import KellyCriterion, KellyResult
from .monte_carlo import (
    MonteCarloSimulator,
    SimulationResult,
    CorrelatedSampler,
)
from .safer_alt import (
    SaferAlternativeGenerator,
    SaferAlternative,
)


__all__ = [
    # Main optimizer
    "SlipOptimizer",
    "OptimizedSlip",

    # Constraints
    "SlipConstraints",
    "create_constraints_for_risk_mode",

    # Kelly sizing
    "KellyCriterion",
    "KellyResult",

    # Monte Carlo simulation
    "MonteCarloSimulator",
    "SimulationResult",
    "CorrelatedSampler",

    # Safer alternatives
    "SaferAlternativeGenerator",
    "SaferAlternative",
]


# Quick-start example usage
"""
Example Usage:

```python
from src.optimize import (
    SlipOptimizer,
    create_constraints_for_risk_mode,
    MonteCarloSimulator,
    KellyCriterion,
)

# Initialize optimizer
optimizer = SlipOptimizer(
    correlation_penalty_weight=0.15,
    diversity_bonus_weight=0.05,
    n_simulations=10000,
    kelly_fraction=0.25,
)

# Optimize slips
optimized_slips = optimizer.optimize_slips(
    props=available_props,
    predictions=predictions_dict,
    correlations=correlation_matrix,
    risk_mode="moderate",  # or 'aggressive', 'conservative'
    bankroll=1000.0,
    payout_multiplier=3.0,
    top_n=10,
    algorithm="greedy",  # or 'genetic', 'beam_search'
)

# Access top slip
best_slip = optimized_slips[0]
print(f"EV: {best_slip.ev_percentage:.2%}")
print(f"Win Probability: {best_slip.win_probability:.2%}")
print(f"Recommended Stake: ${best_slip.recommended_stake}")
print(f"Diversity Score: {best_slip.diversity_score:.2f}")

# Generate safer alternatives
from src.optimize import SaferAlternativeGenerator

safer_gen = SaferAlternativeGenerator()
alternatives = safer_gen.generate_safer_version(
    legs=best_slip.legs,
    predictions=best_slip.predictions,
    correlation_matrix=correlations,
)

for alt in alternatives:
    print(f"Alternative: {alt.reason}")
    print(f"Risk Reduction: {alt.risk_reduction:.2%}")
    print(f"EV Impact: {alt.ev_impact:.3f}")
```

Risk Modes:
- **Aggressive**: Higher leg counts, looser correlations, lower EV threshold
  - max_legs=8, max_correlation=0.5, min_ev=0.05

- **Moderate**: Balanced risk/reward (default)
  - max_legs=6, max_correlation=0.3, min_ev=0.10

- **Conservative**: Lower risk, higher quality
  - max_legs=4, max_correlation=0.15, min_ev=0.15

Optimization Algorithms:
- **greedy**: Fast, good results (recommended for real-time)
- **genetic**: Slower, excellent results (best for batch optimization)
- **beam_search**: Moderate speed, comprehensive search
"""

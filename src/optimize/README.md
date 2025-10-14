# Slip Optimization Engine

The slip optimization engine generates optimized prop betting slips/parlays using sophisticated correlation handling, Monte Carlo simulation, and Kelly criterion bankroll management.

## Features

### Core Optimization
- **Greedy Construction Algorithm**: Builds slips by iteratively selecting props that maximize an objective function combining expected value, correlation penalties, and diversity bonuses
- **Monte Carlo Simulation**: Uses Gaussian copula to simulate correlated outcomes and compute realistic win probabilities
- **Kelly Criterion**: Calculates optimal bet sizes based on edge and bankroll with fractional Kelly for safety

### Risk Modes
Three risk profiles with different parameters:

| Mode | Max Legs | Min Prob | Min Edge | Correlation Penalty | Kelly Fraction |
|------|----------|----------|----------|---------------------|----------------|
| Conservative | 4 | 0.65 | 1.08 | 1.0 | 0.25 |
| Balanced | 6 | 0.55 | 1.05 | 0.6 | 0.5 |
| Aggressive | 8 | 0.45 | 1.03 | 0.3 | 0.75 |

### Correlation Handling
- **Hard Blocks**: Prevents combining props with |ρ| > 0.75
- **Soft Penalties**: Penalizes correlations |ρ| > 0.35 in objective function
- **Gaussian Copula**: Models correlated binary outcomes via Cholesky decomposition
- **Correlation Notes**: Generates human-readable warnings for significant correlations

### Constraints
- Maximum props from same game (default: 3)
- Maximum props from same team (default: 2)
- Minimum 2 distinct games per slip
- No duplicate player-stat combinations
- Confidence interval penalties for uncertain props

### Diversity Scoring
Diversity = 0.4 × (unique teams / num legs) + 0.3 × (unique games / num legs) + 0.3 × (unique positions / num legs)

Higher diversity_target parameter increases weight of diversity in optimization.

### Safer Alternatives
For slips with 3+ legs, automatically generates "safer" variant by removing the lowest probability leg.

## Usage

### Basic Example

```python
from src.optimize import optimize_slips
import pandas as pd
import numpy as np

# Prepare props data
props_df = pd.DataFrame({
    'player_id': ['p1', 'p2', 'p3'],
    'player_name': ['Mahomes', 'Kelce', 'Allen'],
    'team': ['KC', 'KC', 'BUF'],
    'game_id': ['g1', 'g1', 'g2'],
    'position': ['QB', 'TE', 'QB'],
    'prop_type': ['passing_yards', 'receiving_yards', 'passing_yards'],
    'line': [275.5, 65.5, 285.5],
    'over_odds': [-110, -115, -105],
    'prob_over': [0.60, 0.65, 0.58],
    'ci_lower': [0.52, 0.57, 0.50],
    'ci_upper': [0.68, 0.73, 0.66]
})

# Correlation matrix (can use src.corr.estimate_correlations)
corr_matrix = np.eye(len(props_df))

# Generate optimized slips
slips = optimize_slips(
    props_df=props_df,
    corr_matrix=corr_matrix,
    bankroll=100.0,
    diversity_target=0.5,
    n_slips=5,
    risk_mode="balanced"
)

# Examine results
for slip in slips:
    print(f"Slip {slip['slip_id']}:")
    print(f"  Legs: {slip['num_legs']}")
    print(f"  Odds: {slip['total_odds']:.2f}")
    print(f"  Win Prob: {slip['correlation_adjusted_prob']:.1%}")
    print(f"  EV: {slip['expected_value']:.3f}")
    print(f"  Suggested Bet: ${slip['suggested_bet']:.2f}")
```

### What-If Analysis

```python
from src.optimize import apply_what_if_adjustments

# Adjust probabilities for scenario analysis
deltas = {
    0: 0.05,   # Increase leg 0 probability by 5%
    2: -0.03   # Decrease leg 2 probability by 3%
}

adjusted = apply_what_if_adjustments(
    legs=slip['legs'],
    deltas=deltas,
    corr_matrix=corr_matrix,
    indices=selected_indices  # Original indices
)

print(f"Original EV: {slip['expected_value']:.3f}")
print(f"Adjusted EV: {adjusted['expected_value']:.3f}")
```

### Custom Constraints

```python
from src.optimize import SlipConstraints, optimize_slips

constraints = SlipConstraints(
    min_legs=2,
    max_legs=4,
    min_total_odds=2.0,
    max_total_odds=25.0,
    max_same_game_legs=2,
    max_per_team=1,
    disallow_same_player_same_stat=True
)

# Note: constraints are auto-configured based on risk_mode
# For custom constraints, use the lower-level API
```

## Output Structure

Each slip dictionary contains:

```python
{
    'slip_id': str,                        # Unique identifier
    'legs': List[dict],                    # Individual prop legs
    'num_legs': int,                       # Number of legs
    'total_odds': float,                   # Decimal odds (e.g., 6.5)
    'raw_win_prob': float,                 # Naive probability (product)
    'correlation_adjusted_prob': float,    # Monte Carlo adjusted
    'expected_value': float,               # total_odds × adjusted_prob
    'variance': float,                     # Outcome variance
    'value_at_risk_95': float,            # 95% VaR (probability of loss)
    'suggested_bet': float,                # Kelly criterion bet ($)
    'risk_level': str,                     # Risk mode used
    'diversity_score': float,              # 0-1 diversity measure
    'correlation_notes': List[str],        # Correlation warnings
    'safer_alternative': dict              # Safer variant (if applicable)
}
```

Each leg contains:

```python
{
    'player_id': str,
    'player_name': str,
    'prop_type': str,
    'line': float,
    'direction': str,                      # 'over' or 'under'
    'prob': float,                         # Win probability
    'odds': float,                         # American odds
    'team': str,
    'game_id': str,
    'position': str
}
```

## Algorithm Details

### 1. Filtering Phase
- Filter props by minimum probability (mode-specific)
- Filter by minimum edge (EV > threshold)
- Apply confidence interval penalties to reduce uncertainty

### 2. Greedy Construction
For each slip:
1. Sort props by expected value
2. Select starting prop (with geometric distribution randomness)
3. Iteratively add props that maximize:
   ```
   score = EV - λ × correlation_penalty + μ × diversity_boost
   ```
4. Enforce hard constraints at each step
5. Reject if final EV < threshold

### 3. Monte Carlo Adjustment
1. Extract correlation submatrix for selected props
2. Ensure positive semi-definite via eigenvalue decomposition
3. Generate 10,000 correlated normal samples via Cholesky
4. Transform to uniform via Gaussian CDF
5. Transform to Bernoulli outcomes
6. Compute empirical win probability and variance

### 4. Kelly Sizing
```
Kelly fraction = (p × b - q) / b
where b = decimal_odds - 1, q = 1 - p

Suggested bet = kelly_fraction × bankroll × fractional_kelly
Clamped to [$5, $50]
```

## Performance Considerations

- Monte Carlo simulation: 10,000 samples per slip (adjustable)
- Greedy algorithm: O(n² × m) where n = props, m = max_legs
- Correlation matrix: O(n²) space
- Slip generation: Parallelizable (different seeds)

## Integration

The optimizer integrates with:
- **src.corr**: Correlation estimation
- **src.models**: Probability predictions
- **src.config**: User preferences and constraints
- **app.main**: Streamlit UI

## Testing

Comprehensive test suite in `tests/test_optimizer.py`:
- Basic slip generation
- Risk mode enforcement
- Correlation blocking
- Diversity scoring
- Kelly criterion calculation
- Monte Carlo simulation
- What-if adjustments
- Constraint enforcement

Run tests:
```bash
pytest tests/test_optimizer.py -v
```

## Future Enhancements

- [ ] Integer programming for global optimization
- [ ] Advanced copula models (t-copula, vine copulas)
- [ ] Multi-objective optimization (Pareto frontier)
- [ ] Dynamic correlation estimation from historical data
- [ ] Bankroll allocation across multiple slips
- [ ] Live probability updates and re-optimization

# Correlation System Quick Start Guide

## 30-Second Overview

The correlation system models dependencies between prop legs using:
- **Copulas** for multivariate distributions
- **Spearman correlation** from historical data
- **Domain knowledge** for sport-specific adjustments
- **Constraint enforcement** to prevent over-correlated parlays

## Quick Installation

```bash
cd /Users/joshuadeleon/BetterBros\ Bets/apps/api
pip install scipy==1.11.4 copulas==0.10.1
```

## 5-Minute Tutorial

### Step 1: Import the System

```python
from src.corr import (
    CorrelationAnalyzer,
    CorrelatedSampler,
    CorrelationConstraints
)
from src.types import PropLeg, BetDirection
```

### Step 2: Define Your Props

```python
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
]
```

### Step 3: Check Constraints

```python
constraints = CorrelationConstraints()
is_valid, report = await constraints.check_all_constraints(props)

if not is_valid:
    print("Invalid:", report["violations"])
else:
    print("Valid parlay!")
```

### Step 4: Run Simulation

```python
sampler = CorrelatedSampler()
probabilities = [0.55, 0.60]  # From your model

samples = await sampler.generate_samples(
    props=props,
    probabilities=probabilities,
    n_sims=10000
)

# Win probability
win_prob = (samples.sum(axis=1) == len(props)).mean()
print(f"Parlay win probability: {win_prob:.4f}")
```

## Common Use Cases

### Use Case 1: Validate a Parlay

```python
# Check if parlay satisfies correlation constraints
constraints = CorrelationConstraints()
is_valid, report = await constraints.check_all_constraints(
    props,
    min_games=2,
    max_same_player=1
)
```

### Use Case 2: Estimate Win Probability

```python
# Get correlated win probability (more accurate than independent)
sampler = CorrelatedSampler(redis_client=redis)
samples = await sampler.generate_samples(props, probabilities, n_sims=10000)
win_prob = (samples.sum(axis=1) == len(props)).mean()
```

### Use Case 3: Analyze Correlation Structure

```python
# Get correlation matrix
analyzer = CorrelationAnalyzer(redis_client=redis)
corr_matrix = await analyzer.estimate_correlation_matrix(props)
print(corr_matrix)
```

### Use Case 4: Filter Valid Combinations

```python
# Find all valid 3-leg combinations from a pool
valid_combos = await constraints.filter_valid_combinations(
    all_legs=available_props,
    combo_size=3,
    allow_yellow=True
)
```

## Key Parameters

### Correlation Thresholds
```python
CorrelationConstraints(
    green_threshold=0.35,   # Low correlation (OK)
    yellow_threshold=0.75   # High correlation (Block)
)
```

### Diversity Requirements
```python
constraints.enforce_diversity(
    legs=props,
    min_games=2,              # At least 2 games
    min_players=2,            # At least 2 players
    max_same_game=2,          # Max 2 props per game
    max_same_player=1,        # Max 1 prop per player
    max_same_team=3           # Max 3 props per team
)
```

### Sample Generation
```python
sampler.generate_samples(
    props=props,
    probabilities=probabilities,
    n_sims=10000,            # Number of simulations
    use_cache=True,          # Use Redis cache
    cache_key_suffix="snap_123"  # Snapshot ID
)
```

## Built-in Correlations

### NFL
- passing_yards ↔ passing_tds: **0.65**
- passing_yards ↔ completions: **0.75**
- rushing_yards ↔ rushing_tds: **0.60**
- receptions ↔ receiving_yards: **0.75**

### NBA
- points ↔ field_goals_made: **0.85**
- rebounds ↔ minutes: **0.55**
- assists ↔ minutes: **0.50**

### MLB
- strikeouts ↔ innings_pitched: **0.75**
- hits ↔ total_bases: **0.80**
- home_runs ↔ rbis: **0.60**

### Game Context
- Same game props: **+0.40** boost
- Opposing players: **-0.25** penalty

## Performance Tips

### ✅ DO: Use Redis Caching
```python
from src.db.session import get_redis
redis = await get_redis()
analyzer = CorrelationAnalyzer(redis_client=redis)
```

### ✅ DO: Provide Snapshot IDs
```python
corr_matrix = await analyzer.estimate_correlation_matrix(
    props,
    snapshot_id="snapshot_20241014_001"  # Enables caching
)
```

### ✅ DO: Batch Async Operations
```python
results = await asyncio.gather(
    analyzer.estimate_correlation_matrix(props_1),
    analyzer.estimate_correlation_matrix(props_2),
    analyzer.estimate_correlation_matrix(props_3)
)
```

### ❌ DON'T: Disable Caching in Production
```python
# Bad - recomputes every time
corr_matrix = await analyzer.estimate_correlation_matrix(
    props,
    use_cache=False  # Don't do this in production!
)
```

### ❌ DON'T: Run Sequential When You Can Batch
```python
# Bad - slow
for props in all_props:
    corr = await analyzer.estimate_correlation_matrix(props)

# Good - fast
results = await asyncio.gather(
    *[analyzer.estimate_correlation_matrix(p) for p in all_props]
)
```

## Interpretation Guide

### Correlation Levels

| Range | Color | Meaning | Action |
|-------|-------|---------|--------|
| \|ρ\| < 0.35 | 🟢 GREEN | Low correlation | Allow |
| 0.35 ≤ \|ρ\| < 0.75 | 🟡 YELLOW | Moderate | Warn, apply soft penalty |
| \|ρ\| ≥ 0.75 | 🔴 RED | High correlation | Block |

### Sample Statistics

```python
stats = await sampler.get_sample_statistics(samples, props)

# Key metrics:
# - hit_rates: Individual prop success rates
# - empirical_correlation: Actual correlation in samples
# - all_props_hit_rate: Parlay win probability
# - avg_props_hit: Average legs that hit
```

## Troubleshooting

### "Copula fitting failed"
→ Falls back to independent sampling automatically

### "Correlation matrix not positive semi-definite"
→ Automatically corrected using eigenvalue decomposition

### "Redis connection error"
→ System works without Redis, just slower (no caching)

### "High correlation warning"
→ Either remove correlated props or accept YELLOW penalty

## Next Steps

1. **Read Full Docs**: See [README.md](README.md) for comprehensive guide
2. **Run Examples**: Execute `python3 -m src.corr.example_usage`
3. **Check Installation**: Review [INSTALLATION.md](INSTALLATION.md)
4. **Integrate API**: Use patterns from example_usage.py

## API Cheat Sheet

```python
# Correlation Analysis
analyzer = CorrelationAnalyzer(redis_client=redis)
corr_matrix = await analyzer.estimate_correlation_matrix(props)
corr = await analyzer.get_pairwise_correlation(prop1, prop2)
stats = await analyzer.get_correlation_stats(props)

# Sampling
sampler = CorrelatedSampler(redis_client=redis)
samples = await sampler.generate_samples(props, probs, n_sims=10000)
stats = await sampler.get_sample_statistics(samples, props)

# Constraints
constraints = CorrelationConstraints()
corr, level = await constraints.check_correlation(prop1, prop2)
is_valid, violations = await constraints.enforce_diversity(props)
is_valid, report = await constraints.check_all_constraints(props)

# Copula (Advanced)
copula = CopulaModel(copula_type=CopulaType.GAUSSIAN)
copula.fit_copula(correlation_matrix=corr_matrix)
samples = copula.sample(n_samples=10000)
```

## File Locations

```
/Users/joshuadeleon/BetterBros Bets/apps/api/src/corr/
├── correlation.py      # Correlation analysis
├── copula.py           # Copula models
├── sampler.py          # Monte Carlo sampling
├── constraints.py      # Constraint enforcement
├── __init__.py         # Public API
├── example_usage.py    # Complete examples
├── README.md           # Full documentation
├── INSTALLATION.md     # Setup guide
└── QUICKSTART.md       # This file
```

## Getting Help

1. Check the examples: `example_usage.py`
2. Read the docs: `README.md`
3. Review source code (well-documented)
4. Check GitHub repo: https://github.com/Joshua-JD-Deleon/betterbros-props

---

**You're ready to go! Start with the examples and integrate into your workflow.**

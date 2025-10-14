# Feature Engineering Pipeline

Comprehensive feature engineering system for NFL player props analysis.

## Overview

The feature engineering pipeline transforms raw player props data into a rich feature set suitable for ML models and trend analysis. It integrates multiple data sources (baseline stats, injuries, weather) to create 37+ engineered features across 7 categories.

## Architecture

```
Input: Props DataFrame
  ↓
Context Data:
  - Baseline Stats (historical averages)
  - Injuries (current status)
  - Weather (game conditions)
  ↓
Feature Engineering Pipeline
  ├── Player Form Features (6)
  ├── Matchup Features (4)
  ├── Usage Features (3)
  ├── Game Context Features (5)
  ├── Weather Features (5)
  ├── Injury Features (3)
  ├── Prop-Specific Features (5)
  └── Correlation Tags (3)
  ↓
Output: Enhanced Props DataFrame + Trend Chips
```

## Feature Categories

### 1. Player Form Features (6 features)

Captures player's recent performance and consistency:

- **season_avg**: Player's season average for the stat type
- **last_3_avg**: Average over last 3 games
- **ewma_5**: Exponentially weighted moving average (α=0.4, last 5 games)
- **form_trend**: Percentage change from season avg to last 3 games
- **consistency**: Reliability score (1 / coefficient of variation)
- **days_since_last_game**: Rest days since previous game

**Use Cases**: Identify hot/cold streaks, assess reliability, consider fatigue

### 2. Matchup Features (4 features)

Evaluates matchup difficulty:

- **opponent_rank_vs_position**: Defensive rank vs this position (1-32, lower = better defense)
- **opponent_avg_allowed**: Average stat allowed to this position
- **matchup_advantage**: Player avg vs opponent avg allowed (percentage)
- **historical_vs_opponent**: Player's historical performance vs this opponent

**Use Cases**: Exploit weak defenses, fade tough matchups, historical trends

### 3. Usage Features (3 features)

Measures player's role in offense:

- **target_share**: Percentage of team's targets/carries/attempts
- **snap_share**: Percentage of offensive snaps played
- **red_zone_share**: Red zone usage rate (TD opportunity)

**Use Cases**: Identify primary options, assess volume reliability, TD upside

### 4. Game Context Features (5 features)

Captures game environment:

- **is_home**: Boolean, home game advantage
- **vegas_implied_total**: Team's implied point total from O/U
- **vegas_spread**: Point spread (positive = underdog)
- **pace_factor**: Team pace relative to league average
- **game_total**: Over/under total points

**Use Cases**: Game script predictions, high-scoring environments, pace-up spots

### 5. Weather Features (5 features)

Weather impact on outdoor games:

- **temperature**: Degrees Fahrenheit
- **wind_speed**: Miles per hour
- **precipitation_pct**: Precipitation probability (0-100)
- **is_dome**: Boolean, indoor/dome stadium
- **weather_impact**: Categorical severity ("High", "Medium", "Low", "None")

**Use Cases**: Fade passing in high winds, cold weather games, dome games

### 6. Injury Features (3 features)

Injury context affecting props:

- **player_injury_status**: Player's status ("Out", "Doubtful", "Questionable", "Probable", "Healthy")
- **key_teammate_out**: Boolean, key teammate sidelined
- **opponent_key_defender_out**: Boolean, key defender out

**Use Cases**: Increased opportunity plays, injury risk assessment, defensive weakness exploitation

### 7. Prop-Specific Features (5 features)

Betting line analysis:

- **line_vs_season_avg_delta**: How far line differs from season average
- **line_vs_last3_delta**: How far line differs from recent form
- **implied_prob_over**: Probability implied by over odds
- **implied_prob_under**: Probability implied by under odds
- **vig**: Bookmaker's edge (juice)

**Use Cases**: Line value identification, market inefficiencies, sharp vs public money

### 8. Correlation Tags (3 features)

For same-game parlay analysis:

- **same_game_id**: Game identifier for correlations
- **same_team**: Team identifier
- **correlation_group**: Specific correlation type (e.g., "QB_PASSING_KC", "WR_RECEIVING_KC")

**Use Cases**: Positive correlations (QB + WR), negative correlations (opposing RBs), game environment parlays

## Trend Chips

Automated trend detection system that surfaces actionable insights:

### Trend Categories

1. **Hot Streak**: Player significantly outperforming baseline (form_trend > 15%)
2. **Favorable Matchup**: Exploitable defensive weakness (matchup_advantage > 10%)
3. **Weather Impact**: Extreme conditions affecting props (weather_impact = "High")
4. **Injury Cascade**: Increased opportunity from teammate injuries
5. **Vegas Discrepancy**: Line significantly different from projections (>12% delta)
6. **High-Scoring Game**: Game total > 50 points benefiting offensive props
7. **Usage Spike**: Increased target share due to lineup changes

### Trend Chip Structure

```python
{
    'title': str,                    # "Patrick Mahomes Hot Streak"
    'description': str,              # Detailed explanation
    'impact_direction': str,         # "positive" or "negative"
    'confidence': float,             # 0.0 to 1.0
    'impacted_props': List[str],     # Player names affected
    'diagnostics': {
        'method': str,               # Detection method used
        'threshold': float,          # Threshold that triggered detection
        'data_points': int,          # Number of data points analyzed
        'mini_chart_data': dict      # Data for visualization
    }
}
```

## Usage

### Basic Usage

```python
from src.features import build_features, generate_trend_chips
from src.ingest.sleeper_client import fetch_current_props

# Fetch props
props_df = fetch_current_props(week=6, season=2024, mock_mode=True)

# Build features (with mock data)
props_with_features = build_features(props_df)

# Generate trend chips
trends = generate_trend_chips(props_with_features, n_chips=5)
```

### With Context Data

```python
from src.ingest.baseline_stats import load_baseline_stats
from src.ingest.injuries_provider import fetch_injury_report
from src.ingest.weather_provider import fetch_weather_data

# Load context data
baseline_stats = load_baseline_stats(mock_mode=True)
injuries_df = fetch_injury_report(week=6, season=2024, mock_mode=True)
weather_df = fetch_weather_data(props_df[['game_id', 'team', 'game_time']], mock_mode=True)

# Build features with context
context_data = {
    'baseline_stats': baseline_stats,
    'injuries': injuries_df,
    'weather': weather_df
}

props_with_features = build_features(props_df, context_data)
trends = generate_trend_chips(props_with_features, context_data, n_chips=5)
```

### Custom Configuration

```python
# Custom EWMA alpha, thresholds, etc.
config = {
    'ewma_alpha': 0.5,
    'hot_streak_threshold': 0.20,
    'matchup_advantage_threshold': 0.15
}

props_with_features = build_features(props_df, context_data, config=config)
```

## Helper Functions

### calculate_ewma()

```python
from src.features import calculate_ewma

values = [10.0, 12.0, 11.0, 13.0, 14.0]
ewma = calculate_ewma(values, alpha=0.4)  # Returns weighted average
```

### odds_to_probability()

```python
from src.features import odds_to_probability

prob_over = odds_to_probability(-110)  # Returns 0.5238
prob_under = odds_to_probability(100)  # Returns 0.5
```

### calculate_vig()

```python
from src.features import calculate_vig
import pandas as pd

over_odds = pd.Series([-110, -115, -105])
under_odds = pd.Series([-110, -105, -115])

vig = calculate_vig(over_odds, under_odds)  # Returns bookmaker's edge %
```

### detect_correlation_groups()

```python
from src.features import detect_correlation_groups

# Adds correlation_group column
props_with_corr = detect_correlation_groups(props_df)
```

## Integration with Models

The engineered features are designed for seamless integration with the models module:

```python
from src.models import train_model, predict
from src.features import build_features

# Build features
props_with_features = build_features(props_df, context_data)

# Select features for modeling
feature_cols = [
    'season_avg', 'last_3_avg', 'form_trend', 'consistency',
    'opponent_rank_vs_position', 'matchup_advantage',
    'target_share', 'snap_share', 'vegas_implied_total',
    'weather_impact', 'implied_prob_over'
]

# Train model
model = train_model(props_with_features, feature_cols, target='actual_result')

# Make predictions
predictions = predict(model, props_with_features[feature_cols])
```

## Mock Data Strategy

When real data isn't available, the pipeline generates realistic mock data:

- **Player Form**: Varies around line value with position-appropriate consistency
- **Matchups**: Generates defensive rankings with normal distribution (mean ~16)
- **Usage**: Position-appropriate tiers (WR1, WR2, WR3, etc.)
- **Weather**: Geographic-appropriate conditions (cold in Buffalo, warm in Miami)
- **Injuries**: Realistic status distribution (85% healthy, 10% questionable, etc.)
- **Vegas Lines**: Standard ranges (totals 42-52, spreads ±14)

## Performance

- **Processing Speed**: ~0.02-0.05 seconds per prop (37 features)
- **Memory Usage**: ~5-10 MB for 100 props with full features
- **Caching**: Context data cached for 1-24 hours depending on type
- **Scalability**: Tested with 500+ props, linear scaling

## Testing

Comprehensive test suite in `tests/test_features.py`:

- 20 test cases covering all feature categories
- Data type validation
- Logical consistency checks
- Edge case handling
- Integration tests with context data

Run tests:
```bash
pytest tests/test_features.py -v
```

## Examples

See `examples/feature_pipeline_demo.py` for a complete demonstration including:
- Data ingestion
- Feature engineering
- Trend chip generation
- Feature analysis and reporting

Run demo:
```bash
PYTHONPATH=/path/to/nfl-props-analyzer python examples/feature_pipeline_demo.py
```

## Future Enhancements

Potential additions for production:

1. **Advanced Form Features**
   - Home/away splits
   - Divisional game adjustments
   - Rest days vs performance correlation

2. **Deep Matchup Analysis**
   - Shadow coverage rates
   - Blitz tendency vs position
   - Coverage scheme vulnerabilities

3. **Advanced Usage Metrics**
   - Route tree diversity
   - Air yards vs YAC splits
   - Target quality (catchable ball rate)

4. **Game Script Predictions**
   - Expected pass rate by game script
   - Garbage time adjustments
   - Comeback probability

5. **Market Analysis**
   - Line movement tracking
   - Steam moves detection
   - Sharp vs public money indicators

6. **Ensemble Trends**
   - Multi-factor trend combinations
   - Trend strength scoring
   - Historical trend success rates

## API Reference

### build_features()

```python
def build_features(
    props_df: pd.DataFrame,
    context_df: Optional[pd.DataFrame] = None,
    config: Optional[Dict[str, Any]] = None
) -> pd.DataFrame
```

**Parameters:**
- `props_df`: DataFrame with player props (required columns: player_name, team, position, opponent, prop_type, line, over_odds, under_odds, game_id)
- `context_df`: Optional context data (dict with keys: 'baseline_stats', 'injuries', 'weather')
- `config`: Optional configuration dict

**Returns:** DataFrame with original columns + 37 engineered features

### generate_trend_chips()

```python
def generate_trend_chips(
    props_df: pd.DataFrame,
    context_df: Optional[pd.DataFrame] = None,
    n_chips: int = 5
) -> List[Dict[str, Any]]
```

**Parameters:**
- `props_df`: DataFrame with props (should have features built)
- `context_df`: Optional context data
- `n_chips`: Number of trend chips to generate (default: 5)

**Returns:** List of trend chip dictionaries sorted by confidence

## License

Part of NFL Props Analyzer - See main project LICENSE

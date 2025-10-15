# Feature Engineering Pipeline

Comprehensive feature engineering system for prop betting predictions with context enrichment, leakage detection, and versioned storage.

## Overview

The feature pipeline transforms raw prop data into ML-ready feature sets with 50-100 engineered features across multiple categories:

- **Player Features**: Performance metrics, trends, and splits
- **Matchup Features**: Opponent strength, defense rankings, pace
- **Context Features**: Weather, venue, rest, primetime effects
- **Market Features**: Line movement, odds value, consensus
- **Derived Features**: Volatility, EWMA trends, ceiling/floor scores

## Architecture

```
src/features/
├── pipeline.py          # Main FeaturePipeline orchestrator
├── transformers.py      # Feature normalization, encoding, interactions
├── leakage_checks.py    # Temporal and target leakage detection
├── feature_store.py     # Versioned feature persistence (Parquet)
├── example_usage.py     # Usage examples
└── __init__.py         # Module exports
```

## Quick Start

### Basic Usage

```python
from src.features import FeaturePipeline

# Define props
props = [
    {
        'prop_id': 'prop_001',
        'player_id': '421',
        'player_name': 'Patrick Mahomes',
        'team': 'KC',
        'opponent': 'LAC',
        'stat_type': 'passing_yards',
        'line': 285.5,
        'odds': -110,
        'game_id': 'game_001',
        'game_time': '2024-10-20T13:00:00Z',
        'is_home': True,
        'league': 'nfl',
    },
]

# Build features
async with FeaturePipeline() as pipeline:
    features_df = await pipeline.build_features(
        props=props,
        week=8,
        league='nfl',
        season='2024',
    )

print(features_df.shape)  # (1, 87) - 87 features generated
```

### Using Feature Store

```python
from src.features import FeatureStore

store = FeatureStore()

# Save features
await store.save_features(
    snapshot_id='nfl-2024-week8',
    features=features_df,
    metadata={'week': 8, 'season': '2024'},
)

# Load features
loaded_df = await store.load_features('nfl-2024-week8')

# List snapshots
snapshots = await store.list_snapshots()
```

## Feature Categories

### 1. Player Features

Performance-based features computed from historical data:

| Feature | Description | Source |
|---------|-------------|--------|
| `season_avg` | Season average for stat type | BaselineStats |
| `last_3_avg` | Last 3 games average | BaselineStats |
| `last_5_avg` | Last 5 games average | BaselineStats |
| `last_10_avg` | Last 10 games average | BaselineStats |
| `median_value` | Season median | BaselineStats |
| `std_dev` | Standard deviation | BaselineStats |
| `min_value` | Minimum value | BaselineStats |
| `max_value` | Maximum value | BaselineStats |
| `games_played` | Total games played | BaselineStats |
| `home_away_split` | Home vs away multiplier | Computed |
| `usage_rate` | Player usage rate | Estimated |
| `target_share` | Target/touch share | Estimated |
| `days_rest` | Days since last game | Schedule data |
| `injury_status` | Current injury status | InjuriesAPI |
| `injury_status_encoded` | Encoded injury (0-4) | Encoded |
| `career_avg_vs_opponent` | Historical vs opponent | Historical data |
| `position` | Player position | SleeperAPI |
| `age` | Player age | SleeperAPI |
| `years_exp` | Years of experience | SleeperAPI |
| `height` | Player height | SleeperAPI |
| `weight` | Player weight | SleeperAPI |

### 2. Matchup Features

Opponent and matchup-specific features:

| Feature | Description | Source |
|---------|-------------|--------|
| `opponent_defense_rank` | Opponent defensive rank (1-32) | BaselineStats |
| `opponent_pace` | Opponent pace (possessions/game) | BaselineStats |
| `opponent_strength` | Overall opponent strength (0-1) | Computed |
| `opponent_yards_allowed_per_game` | Defensive yards allowed | BaselineStats |
| `opponent_yards_per_game` | Offensive yards | BaselineStats |
| `historical_matchup_avg` | Historical avg in matchup | Historical data |

### 3. Context Features

Environmental and situational features:

| Feature | Description | Source |
|---------|-------------|--------|
| `venue_type` | Dome, outdoor, altitude | Venue database |
| `venue_type_encoded` | Encoded venue (0-2) | Encoded |
| `temperature` | Temperature (F) | WeatherAPI |
| `wind_speed` | Wind speed (mph) | WeatherAPI |
| `precipitation_prob` | Precipitation probability | WeatherAPI |
| `humidity` | Humidity percentage | WeatherAPI |
| `game_total` | Over/under total | Odds providers |
| `spread` | Point spread | Odds providers |
| `primetime_game` | Is primetime (1/0) | Game time |

### 4. Market Features

Betting market and line features:

| Feature | Description | Source |
|---------|-------------|--------|
| `line_movement` | Line change over time | Line tracking |
| `line_opened_at` | Opening line | Line history |
| `line_current` | Current line | Current market |
| `implied_probability` | Implied prob from odds | Computed |
| `odds` | American odds | Market data |
| `odds_value` | Value assessment | Computed |
| `book_consensus` | Consensus line | Multiple books |
| `num_books` | Number of books | Market data |
| `line_vs_baseline` | Line relative to baseline | Computed |

### 5. Derived Features

Computed features from base features:

| Feature | Description | Calculation |
|---------|-------------|-------------|
| `ewma_trend` | EWMA trend indicator | (last_3 - season) / season |
| `volatility` | Performance volatility | std_dev / season_avg |
| `ceiling_score` | 90th percentile (approx) | season_avg + 1.28 * std_dev |
| `floor_score` | 10th percentile (approx) | season_avg - 1.28 * std_dev |
| `recent_form` | Trending indicator | -1, 0, 1 (down/stable/up) |
| `pace_adjusted_avg` | Pace-adjusted average | season_avg * (opp_pace / 24) |
| `rest_advantage` | Rest days advantage | (days_rest - 4) / 10 |
| `weather_impact` | Weather impact score | -wind_speed / 20 * 0.1 |

### 6. Interaction Features

Cross-feature interactions (top 10):

| Feature | Description |
|---------|-------------|
| `season_avg_x_opponent_defense_rank` | Performance vs defense quality |
| `last_3_avg_x_opponent_strength` | Recent form vs opponent |
| `line_vs_baseline_x_recent_form` | Line value vs form |
| `line_vs_baseline_x_ewma_trend` | Line value vs trend |
| `opponent_pace_x_usage_rate` | Pace impact on usage |
| `opponent_pace_x_target_share` | Pace impact on targets |
| `wind_speed_x_season_avg` | Weather impact on passing |
| `temperature_x_season_avg` | Temperature impact |
| `home_away_split_x_opponent_strength` | Home advantage vs opponent |
| `volatility_x_line_vs_baseline` | Risk vs line position |

## Leakage Detection

The pipeline includes comprehensive leakage detection to prevent data contamination:

### Temporal Leakage

Ensures no future data is used in features:

```python
from src.features import LeakageDetector

detector = LeakageDetector(strict_mode=True)
detector.check_temporal_leakage(features_df, current_week=8)
```

**Checks:**
- No features reference weeks beyond current week
- No future timestamps in feature computation
- `computed_at` is before `game_time`
- Baseline stats computed from past games only

### Target Leakage

Prevents target variable information in features:

```python
detector.check_target_leakage(features_df, target_col='actual_value')
```

**Checks:**
- No forbidden columns (actual_value, game_outcome, bet_result, etc.)
- No suspicious patterns (result_, outcome_, final_, etc.)
- No perfect correlations with target
- No outcome indicators (won, lost, profit, etc.)

### Timestamp Validation

```python
detector.validate_feature_timestamps(features_df)
```

**Checks:**
- Valid timestamp formats
- No future computed_at timestamps
- Logical timestamp ordering
- Consistent time periods

## Feature Store

Versioned feature persistence with metadata tracking.

### Storage Structure

```
/data/snapshots/{snapshot_id}/
├── features.parquet     # Main feature data (columnar)
├── metadata.json        # Snapshot metadata
├── schema.json          # Feature schema
└── statistics.json      # Feature statistics
```

### API

#### Save Features

```python
store = FeatureStore()

save_info = await store.save_features(
    snapshot_id='nfl-2024-week8',
    features=features_df,
    metadata={
        'week': 8,
        'season': '2024',
        'league': 'nfl',
        'description': 'Week 8 NFL props',
    },
    compression='snappy',
)

# Returns: {'snapshot_id', 'path', 'rows', 'columns', 'size_bytes', ...}
```

#### Load Features

```python
# Load all features
features_df = await store.load_features('nfl-2024-week8')

# Load specific columns only (more efficient)
features_df = await store.load_features(
    'nfl-2024-week8',
    columns=['prop_id', 'season_avg', 'last_3_avg', 'line_vs_baseline']
)
```

#### Snapshot Management

```python
# List all snapshots
snapshots = await store.list_snapshots()

# Get metadata
metadata = await store.get_metadata('nfl-2024-week8')

# Get schema
schema = await store.get_schema('nfl-2024-week8')

# Get statistics
stats = await store.get_statistics('nfl-2024-week8')

# Check existence
exists = await store.snapshot_exists('nfl-2024-week8')

# Delete snapshot
await store.delete_snapshot('nfl-2024-week8')

# Storage info
info = await store.get_storage_info()
```

## Feature Transformations

### Normalization

Z-score normalization for numeric features:

```python
from src.features import FeatureTransformer

transformer = FeatureTransformer()

# Fit and transform (training)
features_df = transformer.normalize_features(features_df, fit=True)

# Transform only (inference)
features_df = transformer.normalize_features(features_df, fit=False)
```

Creates `{feature}_normalized` columns with standardized values.

### Categorical Encoding

Label and one-hot encoding:

```python
# Encodes: position, injury_status, venue_type, stat_type
features_df = transformer.encode_categoricals(features_df, fit=True)
```

Creates:
- `{feature}_encoded` columns with label encoding
- One-hot dummy columns for nominal features (e.g., position_QB, position_RB)

### Missing Value Handling

Smart imputation strategies:

```python
# Smart strategy (domain knowledge)
features_df = transformer.handle_missing(features_df, strategy='smart')

# Other strategies: 'mean', 'median', 'zero'
```

**Smart strategy rules:**
- Performance metrics: 0
- Variability metrics: median
- Rates/shares: league average
- Context features: neutral values

### Feature Interactions

Create cross-feature interactions:

```python
features_df = transformer.create_interactions(
    features_df,
    max_interactions=10
)
```

### Feature Selection

Select specific feature groups:

```python
# Select only player performance features
selected_df = transformer.select_features(
    features_df,
    feature_groups=['player_performance', 'matchup_quality']
)

# Available groups:
# - player_performance
# - player_context
# - matchup_quality
# - environmental
# - market_signals
# - derived_metrics
```

### Feature Validation

Validate feature DataFrame:

```python
is_valid, issues = transformer.validate_features(features_df)

if not is_valid:
    for issue in issues:
        print(f"Issue: {issue}")
```

**Validation checks:**
- No infinite values
- No extremely high variance
- No constant columns
- Required columns present

## Caching

The pipeline uses Redis caching extensively:

- **Feature Pipeline**: 12-hour TTL for intermediate results
- **Baseline Stats**: 24-hour TTL for player statistics
- **Sleeper API**: 1-hour TTL for player data, 30-min for stats
- **Injuries API**: 1-hour TTL for injury reports
- **Weather API**: 6-hour TTL for weather forecasts
- **Feature Store**: 1-hour TTL for loaded snapshots

Cache keys are structured: `{service}:{resource}:{identifier}`

## Error Handling

### Custom Exceptions

```python
from src.features import (
    FeaturePipelineError,
    LeakageError,
    FeatureStoreError,
)

try:
    features_df = await pipeline.build_features(props, week=8)
except FeaturePipelineError as e:
    logger.error(f"Pipeline failed: {e}")

try:
    detector.check_temporal_leakage(features_df, week=8)
except LeakageError as e:
    logger.error(f"Leakage detected: {e}")

try:
    await store.save_features(snapshot_id, features_df)
except FeatureStoreError as e:
    logger.error(f"Storage failed: {e}")
```

### Non-Strict Mode

For development, use non-strict leakage detection:

```python
detector = LeakageDetector(strict_mode=False)
detector.check_temporal_leakage(features_df, week=8)
# Logs warnings instead of raising exceptions
```

## Performance

### Benchmarks

Typical performance on 100 props:

- Feature building: 5-10 seconds
- Transformations: 1-2 seconds
- Save to store: 0.5-1 seconds
- Load from store: 0.2-0.5 seconds (cached: 0.05s)

### Optimization Tips

1. **Use caching**: Enable Redis caching for repeated queries
2. **Batch processing**: Process props in batches of 50-100
3. **Column selection**: Load only needed columns from feature store
4. **Async operations**: Pipeline uses asyncio for parallel data fetching
5. **Parquet compression**: Use 'snappy' for balance of speed/size

## Integration with ML Pipeline

### Training Pipeline

```python
from src.features import FeaturePipeline, FeatureStore, FeatureTransformer

# 1. Build features for training data
async with FeaturePipeline() as pipeline:
    train_features = await pipeline.build_features(
        props=train_props,
        week=current_week - 1,
        league='nfl',
    )

# 2. Transform features
transformer = FeatureTransformer()
train_features = transformer.handle_missing(train_features)
train_features = transformer.normalize_features(train_features, fit=True)
train_features = transformer.encode_categoricals(train_features, fit=True)
train_features = transformer.create_interactions(train_features)

# 3. Save for reproducibility
store = FeatureStore()
await store.save_features('train_week7', train_features)

# 4. Train model
X_train = train_features[feature_columns]
y_train = train_features['target']
model.fit(X_train, y_train)
```

### Inference Pipeline

```python
# 1. Build features for new props
async with FeaturePipeline() as pipeline:
    inference_features = await pipeline.build_features(
        props=new_props,
        week=current_week,
        league='nfl',
    )

# 2. Transform (using fitted transformers)
inference_features = transformer.handle_missing(inference_features)
inference_features = transformer.normalize_features(inference_features, fit=False)
inference_features = transformer.encode_categoricals(inference_features, fit=False)
inference_features = transformer.create_interactions(inference_features)

# 3. Predict
X_inference = inference_features[feature_columns]
predictions = model.predict(X_inference)
```

## Examples

See `example_usage.py` for complete examples:

```bash
cd /Users/joshuadeleon/BetterBros\ Bets/apps/api
python -m src.features.example_usage
```

Examples included:
1. Basic feature pipeline
2. Feature store usage
3. Leakage detection
4. Feature transformations
5. Full end-to-end workflow

## Testing

Run tests:

```bash
pytest apps/api/tests/features/
```

## Contributing

When adding new features:

1. Add feature computation to appropriate method in `pipeline.py`
2. Update feature lists in `transformers.py` if needed
3. Add leakage checks if feature is time-sensitive
4. Document feature in this README
5. Add example usage in `example_usage.py`
6. Write tests

## License

Copyright 2024 BetterBros Props. All rights reserved.

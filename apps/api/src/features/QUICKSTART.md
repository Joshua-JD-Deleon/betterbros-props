# Feature Engineering Pipeline - Quick Start Guide

Get up and running with the feature engineering pipeline in 5 minutes.

## Installation

1. Install required packages:
```bash
cd /Users/joshuadeleon/BetterBros\ Bets
pip install pandas numpy pyarrow scikit-learn redis
```

2. Ensure Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

3. Verify environment variables are set in `.env`:
```bash
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql+asyncpg://...
SLEEPER_API_KEY=...
OPENWEATHER_KEY=...
```

## Basic Usage

### 1. Build Features

```python
import asyncio
from src.features import FeaturePipeline

async def build_features():
    # Define your props
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

    print(f"Built {len(features_df)} rows with {len(features_df.columns)} features")
    return features_df

# Run
features = asyncio.run(build_features())
```

### 2. Save to Feature Store

```python
from src.features import FeatureStore

async def save_features(features_df):
    store = FeatureStore()

    snapshot_id = 'nfl-2024-week8'
    await store.save_features(
        snapshot_id=snapshot_id,
        features=features_df,
        metadata={'week': 8, 'season': '2024'},
    )

    print(f"Saved snapshot: {snapshot_id}")

# Run
asyncio.run(save_features(features))
```

### 3. Load from Feature Store

```python
async def load_features():
    store = FeatureStore()

    # Load all features
    features_df = await store.load_features('nfl-2024-week8')

    # Or load specific columns only
    features_df = await store.load_features(
        'nfl-2024-week8',
        columns=['prop_id', 'season_avg', 'last_3_avg', 'line_vs_baseline']
    )

    return features_df

# Run
features = asyncio.run(load_features())
```

## Common Workflows

### Training Pipeline

```python
import asyncio
from src.features import FeaturePipeline, FeatureStore, FeatureTransformer

async def training_workflow(train_props):
    # 1. Build features
    async with FeaturePipeline() as pipeline:
        features_df = await pipeline.build_features(
            props=train_props,
            week=7,
            league='nfl',
        )

    # 2. Transform
    transformer = FeatureTransformer()
    features_df = transformer.handle_missing(features_df)
    features_df = transformer.normalize_features(features_df, fit=True)
    features_df = transformer.encode_categoricals(features_df, fit=True)

    # 3. Save
    store = FeatureStore()
    await store.save_features('train_week7', features_df)

    # 4. Use for training
    feature_cols = [col for col in features_df.columns
                   if col not in ['prop_id', 'player_name', 'target']]
    X_train = features_df[feature_cols]
    y_train = features_df['target']  # Add your target

    return X_train, y_train

# Run
X_train, y_train = asyncio.run(training_workflow(train_props))
```

### Inference Pipeline

```python
async def inference_workflow(new_props, transformer):
    # 1. Build features
    async with FeaturePipeline() as pipeline:
        features_df = await pipeline.build_features(
            props=new_props,
            week=8,
            league='nfl',
        )

    # 2. Transform (using fitted transformer)
    features_df = transformer.handle_missing(features_df)
    features_df = transformer.normalize_features(features_df, fit=False)
    features_df = transformer.encode_categoricals(features_df, fit=False)

    # 3. Get features for prediction
    feature_cols = [col for col in features_df.columns
                   if col not in ['prop_id', 'player_name']]
    X_inference = features_df[feature_cols]

    return X_inference, features_df

# Run
X_inference, features_df = asyncio.run(inference_workflow(new_props, transformer))
```

## Key Features to Use

### Most Important Features

For quick prototyping, focus on these high-value features:

**Performance Features:**
- `season_avg` - Season average
- `last_3_avg` - Recent form (last 3 games)
- `last_5_avg` - Medium-term form
- `std_dev` - Volatility

**Value Features:**
- `line_vs_baseline` - Line compared to baseline
- `ewma_trend` - Momentum indicator
- `recent_form` - Trending up/down/stable

**Matchup Features:**
- `opponent_defense_rank` - Defense quality
- `opponent_strength` - Overall opponent strength
- `opponent_pace` - Game pace

**Context Features:**
- `is_home` - Home advantage
- `primetime_game` - Primetime effect
- `weather_impact` - Weather adjustment

**Derived Features:**
- `volatility` - Risk metric
- `ceiling_score` - Upside potential
- `floor_score` - Downside risk

### Example Feature Selection

```python
# Select minimal feature set
essential_features = [
    'prop_id', 'player_name', 'line',
    'season_avg', 'last_3_avg', 'std_dev',
    'line_vs_baseline', 'opponent_strength',
    'is_home', 'volatility',
]

df_minimal = features_df[essential_features]
```

## Validation & Quality Checks

### Check for Leakage

```python
from src.features import LeakageDetector

detector = LeakageDetector(strict_mode=True)
detector.check_temporal_leakage(features_df, current_week=8)
detector.check_target_leakage(features_df)

# Generate report
print(detector.generate_report())
```

### Validate Features

```python
transformer = FeatureTransformer()
is_valid, issues = transformer.validate_features(features_df)

if not is_valid:
    print("Issues found:")
    for issue in issues:
        print(f"  - {issue}")
```

## Troubleshooting

### Redis Connection Error

```python
# Check Redis is running
redis-cli ping

# Check REDIS_URL in .env
echo $REDIS_URL
```

### Missing Player Data

```python
# If player_id is not found in Sleeper:
# - Verify player_id is correct Sleeper ID
# - Check player is active in current season
# - Pipeline will use default values for missing data
```

### Feature Store Path

```python
# Default path: /Users/joshuadeleon/BetterBros Bets/data/snapshots
# Create directory if needed:
mkdir -p /Users/joshuadeleon/BetterBros\ Bets/data/snapshots
```

### Import Errors

```python
# Ensure you're in the correct directory
cd /Users/joshuadeleon/BetterBros\ Bets/apps/api

# Ensure PYTHONPATH includes apps/api
export PYTHONPATH=$PYTHONPATH:/Users/joshuadeleon/BetterBros\ Bets/apps/api
```

## Performance Tips

1. **Enable Caching**: Always use Redis caching in production
2. **Batch Props**: Process 50-100 props at a time
3. **Column Selection**: Load only needed columns from feature store
4. **Reuse Clients**: Use context managers or reuse client instances
5. **Parallel Processing**: Pipeline uses async for parallel fetching

## Next Steps

1. Read full documentation: `README.md`
2. Run examples: `python -m src.features.example_usage`
3. Review feature catalog in README
4. Integrate with your ML pipeline
5. Set up monitoring and logging

## Support

- Documentation: `/apps/api/src/features/README.md`
- Examples: `/apps/api/src/features/example_usage.py`
- Implementation Details: `/apps/api/src/features/IMPLEMENTATION_SUMMARY.md`

## Quick Reference

```python
# Import everything
from src.features import (
    FeaturePipeline,
    FeatureStore,
    FeatureTransformer,
    LeakageDetector,
)

# Build features
async with FeaturePipeline() as pipeline:
    df = await pipeline.build_features(props, week=8)

# Transform
transformer = FeatureTransformer()
df = transformer.handle_missing(df)
df = transformer.normalize_features(df, fit=True)

# Store
store = FeatureStore()
await store.save_features('snapshot_id', df)
df = await store.load_features('snapshot_id')

# Validate
detector = LeakageDetector()
detector.check_temporal_leakage(df, week=8)
```

That's it! You're ready to use the feature engineering pipeline.

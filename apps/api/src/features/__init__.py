"""
Feature Engineering Module for BetterBros Props

Provides comprehensive feature engineering pipeline with:
- Player performance features (rolling averages, trends, splits)
- Matchup features (opponent strength, pace, defense rankings)
- Contextual features (weather, venue, rest, primetime)
- Market features (line movement, odds value, consensus)
- Derived features (volatility, ceiling/floor, EWMA trends)

Includes:
- Leakage detection to prevent temporal and target leakage
- Feature transformations (normalization, encoding, interactions)
- Feature store for versioned snapshot persistence

Usage:
    from src.features import FeaturePipeline, FeatureStore

    async with FeaturePipeline() as pipeline:
        features_df = await pipeline.build_features(
            props=props_list,
            week=8,
            league='nfl',
            season='2024',
        )

    store = FeatureStore()
    await store.save_features('snapshot-week8', features_df)
"""
from src.features.pipeline import FeaturePipeline, FeaturePipelineError
from src.features.transformers import FeatureTransformer
from src.features.leakage_checks import LeakageDetector, LeakageError
from src.features.feature_store import FeatureStore, FeatureStoreError

__all__ = [
    # Main Pipeline
    "FeaturePipeline",
    "FeaturePipelineError",
    # Transformers
    "FeatureTransformer",
    # Leakage Detection
    "LeakageDetector",
    "LeakageError",
    # Feature Store
    "FeatureStore",
    "FeatureStoreError",
]

__version__ = "1.0.0"

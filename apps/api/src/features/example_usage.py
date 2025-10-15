"""
Example Usage of Feature Engineering Pipeline

Demonstrates how to use the feature pipeline to build engineered features
for prop betting predictions.
"""
import asyncio
import logging
from datetime import datetime, timedelta

from src.features import (
    FeaturePipeline,
    FeatureStore,
    LeakageDetector,
    FeatureTransformer,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_basic_pipeline():
    """
    Example 1: Basic feature pipeline usage
    """
    logger.info("=" * 80)
    logger.info("Example 1: Basic Feature Pipeline")
    logger.info("=" * 80)

    # Sample prop data
    props = [
        {
            'prop_id': 'prop_001',
            'player_id': '421',  # Patrick Mahomes
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
        {
            'prop_id': 'prop_002',
            'player_id': '536',  # Justin Jefferson
            'player_name': 'Justin Jefferson',
            'team': 'MIN',
            'opponent': 'DET',
            'stat_type': 'receiving_yards',
            'line': 78.5,
            'odds': -115,
            'game_id': 'game_002',
            'game_time': '2024-10-20T16:25:00Z',
            'is_home': False,
            'league': 'nfl',
        },
        {
            'prop_id': 'prop_003',
            'player_id': '4866',  # Christian McCaffrey
            'player_name': 'Christian McCaffrey',
            'team': 'SF',
            'opponent': 'SEA',
            'stat_type': 'rushing_yards',
            'line': 85.5,
            'odds': -105,
            'game_id': 'game_003',
            'game_time': '2024-10-20T20:20:00Z',
            'is_home': True,
            'league': 'nfl',
        },
    ]

    # Initialize pipeline
    async with FeaturePipeline() as pipeline:
        logger.info("Building features for props...")

        # Build features
        features_df = await pipeline.build_features(
            props=props,
            week=8,
            league='nfl',
            season='2024',
        )

        logger.info(f"\nFeature DataFrame shape: {features_df.shape}")
        logger.info(f"Columns: {len(features_df.columns)}")
        logger.info(f"\nSample features (first 10 columns):")
        logger.info(features_df.iloc[:, :10].to_string())

        # Show feature categories
        logger.info(f"\nFeature summary:")
        logger.info(f"- Player features: season_avg, last_3_avg, last_5_avg, etc.")
        logger.info(f"- Matchup features: opponent_defense_rank, opponent_pace, etc.")
        logger.info(f"- Context features: venue_type, weather, game_total, etc.")
        logger.info(f"- Market features: line_movement, implied_probability, etc.")
        logger.info(f"- Derived features: ewma_trend, volatility, ceiling_score, etc.")

        return features_df


async def example_feature_store():
    """
    Example 2: Using the feature store
    """
    logger.info("\n" + "=" * 80)
    logger.info("Example 2: Feature Store")
    logger.info("=" * 80)

    # Build features first
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

    async with FeaturePipeline() as pipeline:
        features_df = await pipeline.build_features(
            props=props,
            week=8,
            league='nfl',
            season='2024',
        )

    # Initialize feature store
    store = FeatureStore()

    # Save features
    snapshot_id = f"nfl-2024-week8-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    logger.info(f"Saving features to snapshot: {snapshot_id}")

    save_info = await store.save_features(
        snapshot_id=snapshot_id,
        features=features_df,
        metadata={
            'week': 8,
            'season': '2024',
            'league': 'nfl',
            'description': 'Example feature snapshot for week 8',
        },
    )

    logger.info(f"Save info: {save_info}")

    # Load features back
    logger.info(f"\nLoading features from snapshot...")
    loaded_features = await store.load_features(snapshot_id)

    logger.info(f"Loaded {len(loaded_features)} rows, {len(loaded_features.columns)} columns")

    # Get metadata
    metadata = await store.get_metadata(snapshot_id)
    logger.info(f"\nSnapshot metadata:")
    for key, value in metadata.items():
        if key != 'feature_names':  # Skip long list
            logger.info(f"  {key}: {value}")

    # Get statistics
    statistics = await store.get_statistics(snapshot_id)
    logger.info(f"\nSnapshot statistics:")
    logger.info(f"  Total rows: {statistics['total_rows']}")
    logger.info(f"  Memory usage: {statistics['memory_usage_bytes'] / 1024:.2f} KB")
    logger.info(f"  Missing values: {len(statistics['missing_values'])} columns with missing data")

    # List all snapshots
    all_snapshots = await store.list_snapshots()
    logger.info(f"\nTotal snapshots in store: {len(all_snapshots)}")

    # Cleanup (optional)
    # await store.delete_snapshot(snapshot_id)
    # logger.info(f"Deleted snapshot: {snapshot_id}")


async def example_leakage_detection():
    """
    Example 3: Leakage detection
    """
    logger.info("\n" + "=" * 80)
    logger.info("Example 3: Leakage Detection")
    logger.info("=" * 80)

    # Build features
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
            'game_time': (datetime.utcnow() + timedelta(days=1)).isoformat(),
            'is_home': True,
            'league': 'nfl',
        },
    ]

    async with FeaturePipeline() as pipeline:
        features_df = await pipeline.build_features(
            props=props,
            week=8,
            league='nfl',
            season='2024',
        )

    # Initialize leakage detector
    detector = LeakageDetector(strict_mode=False)  # Non-strict for demo

    # Check temporal leakage
    logger.info("Checking temporal leakage...")
    detector.check_temporal_leakage(features_df, current_week=8)

    # Check target leakage
    logger.info("Checking target leakage...")
    detector.check_target_leakage(features_df)

    # Validate timestamps
    logger.info("Validating feature timestamps...")
    detector.validate_feature_timestamps(features_df)

    # Check distributions
    logger.info("Checking feature distributions...")
    detector.check_feature_distributions(features_df)

    # Generate report
    report = detector.generate_report()
    logger.info(f"\n{report}")


async def example_feature_transformations():
    """
    Example 4: Feature transformations
    """
    logger.info("\n" + "=" * 80)
    logger.info("Example 4: Feature Transformations")
    logger.info("=" * 80)

    # Build features
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
            'position': 'QB',
        },
    ]

    async with FeaturePipeline() as pipeline:
        features_df = await pipeline.build_features(
            props=props,
            week=8,
            league='nfl',
            season='2024',
        )

    # Initialize transformer
    transformer = FeatureTransformer()

    # Show original shape
    logger.info(f"Original shape: {features_df.shape}")

    # Handle missing values
    logger.info("\nHandling missing values...")
    features_df = transformer.handle_missing(features_df, strategy='smart')

    # Normalize features
    logger.info("Normalizing features...")
    features_df = transformer.normalize_features(features_df, fit=True)

    # Encode categoricals
    logger.info("Encoding categorical features...")
    features_df = transformer.encode_categoricals(features_df, fit=True)

    # Create interactions
    logger.info("Creating interaction features...")
    features_df = transformer.create_interactions(features_df, max_interactions=10)

    logger.info(f"\nFinal shape after transformations: {features_df.shape}")

    # Validate features
    is_valid, issues = transformer.validate_features(features_df)
    if is_valid:
        logger.info("Feature validation: PASSED")
    else:
        logger.warning(f"Feature validation issues found:")
        for issue in issues:
            logger.warning(f"  - {issue}")

    # Show feature groups
    groups = transformer.get_feature_importance_groups()
    logger.info(f"\nFeature groups:")
    for group_name, features in groups.items():
        available = [f for f in features if f in features_df.columns]
        logger.info(f"  {group_name}: {len(available)} features")


async def example_full_workflow():
    """
    Example 5: Full end-to-end workflow
    """
    logger.info("\n" + "=" * 80)
    logger.info("Example 5: Full End-to-End Workflow")
    logger.info("=" * 80)

    # 1. Define props
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
        {
            'prop_id': 'prop_002',
            'player_id': '536',
            'player_name': 'Justin Jefferson',
            'team': 'MIN',
            'opponent': 'DET',
            'stat_type': 'receiving_yards',
            'line': 78.5,
            'odds': -115,
            'game_id': 'game_002',
            'game_time': '2024-10-20T16:25:00Z',
            'is_home': False,
            'league': 'nfl',
        },
    ]

    # 2. Build features with pipeline
    logger.info("Step 1: Building features with pipeline...")
    async with FeaturePipeline() as pipeline:
        features_df = await pipeline.build_features(
            props=props,
            week=8,
            league='nfl',
            season='2024',
        )

    logger.info(f"Built features: {features_df.shape}")

    # 3. Validate for leakage
    logger.info("\nStep 2: Validating for leakage...")
    detector = LeakageDetector(strict_mode=False)
    detector.check_temporal_leakage(features_df, current_week=8)
    detector.check_target_leakage(features_df)
    logger.info("Leakage checks passed")

    # 4. Apply transformations
    logger.info("\nStep 3: Applying transformations...")
    transformer = FeatureTransformer()
    features_df = transformer.handle_missing(features_df, strategy='smart')
    features_df = transformer.normalize_features(features_df, fit=True)
    features_df = transformer.encode_categoricals(features_df, fit=True)
    features_df = transformer.create_interactions(features_df)
    logger.info(f"Transformed features: {features_df.shape}")

    # 5. Save to feature store
    logger.info("\nStep 4: Saving to feature store...")
    store = FeatureStore()
    snapshot_id = f"nfl-2024-week8-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    await store.save_features(
        snapshot_id=snapshot_id,
        features=features_df,
        metadata={
            'week': 8,
            'season': '2024',
            'league': 'nfl',
            'workflow': 'full_pipeline',
        },
    )
    logger.info(f"Saved to snapshot: {snapshot_id}")

    # 6. Verify by loading back
    logger.info("\nStep 5: Verifying storage...")
    loaded_df = await store.load_features(snapshot_id)
    assert len(loaded_df) == len(features_df)
    logger.info("Verification passed")

    logger.info("\nWorkflow completed successfully!")
    logger.info(f"Final feature set: {len(loaded_df)} props, {len(loaded_df.columns)} features")

    return snapshot_id


async def main():
    """Run all examples"""
    try:
        # Run examples
        await example_basic_pipeline()
        await example_feature_store()
        await example_leakage_detection()
        await example_feature_transformations()
        await example_full_workflow()

        logger.info("\n" + "=" * 80)
        logger.info("All examples completed successfully!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())

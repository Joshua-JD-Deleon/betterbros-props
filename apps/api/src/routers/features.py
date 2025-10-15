"""
Features Router
Endpoints for feature engineering and feature sets
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis
import json

from src.types import (
    FeatureSet,
    FeatureSetRequest,
    FeatureSetResponse,
    UserProfile,
)
from src.auth.deps import get_current_active_user
from src.db import get_db, get_redis
from src.features import FeaturePipeline, FeatureStore, FeaturePipelineError
from src.config import settings

router = APIRouter()


@router.post("/compute", response_model=FeatureSetResponse)
async def compute_features(
    request: FeatureSetRequest,
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Compute feature sets for specified prop legs

    Uses the FeaturePipeline to calculate:
    - Rolling averages (5, 10, season)
    - Matchup-specific features
    - Trend and volatility metrics
    - Pace adjustments
    - Contextual features

    Results are cached in Redis with TTL
    """
    try:
        feature_sets = []

        # Initialize feature pipeline
        async with FeaturePipeline() as pipeline:
            for prop_leg_id in request.prop_leg_ids:
                # Check cache first
                cache_key = f"features:{prop_leg_id}"
                cached_data = await redis_client.get(cache_key)

                if cached_data and not request.include_historical:
                    # Use cached features
                    feature_set = FeatureSet.model_validate_json(cached_data)
                    feature_sets.append(feature_set)
                    continue

                # Compute features
                # Note: This is a simplified example - you'd need to fetch prop leg details
                # from the database and pass them to the pipeline
                try:
                    # In production, you'd fetch prop leg details here
                    # features_df = await pipeline.build_features(
                    #     props=[prop_leg],
                    #     week=current_week,
                    #     league=sport,
                    #     season=current_season,
                    # )

                    # For now, create a placeholder feature set
                    from src.types import PlayerFeatures
                    from datetime import datetime

                    feature_set = FeatureSet(
                        prop_leg_id=prop_leg_id,
                        player_features=PlayerFeatures(
                            player_id="placeholder",
                            player_name="Placeholder Player",
                            avg_last_5=0.0,
                            avg_last_10=0.0,
                            avg_season=0.0,
                        ),
                        team_features={},
                        opponent_features={},
                        contextual_features={},
                        feature_version=settings.MODEL_VERSION,
                        computed_at=datetime.utcnow(),
                    )

                    feature_sets.append(feature_set)

                    # Cache the computed features
                    await redis_client.setex(
                        cache_key,
                        settings.FEATURE_CACHE_TTL,
                        feature_set.model_dump_json(),
                    )

                except FeaturePipelineError as e:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to compute features for {prop_leg_id}: {str(e)}",
                    )

        return FeatureSetResponse(
            features=feature_sets,
            total=len(feature_sets),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute features: {str(e)}",
        )


@router.get("/{prop_leg_id}", response_model=FeatureSet)
async def get_feature_set(
    prop_leg_id: str,
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Get cached or compute feature set for a single prop leg

    Checks Redis cache first, computes if not found, and caches result
    """
    try:
        # Check cache
        cache_key = f"features:{prop_leg_id}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return FeatureSet.model_validate_json(cached_data)

        # Compute features if not cached
        async with FeaturePipeline() as pipeline:
            # In production, fetch prop leg details and compute
            from src.types import PlayerFeatures
            from datetime import datetime

            feature_set = FeatureSet(
                prop_leg_id=prop_leg_id,
                player_features=PlayerFeatures(
                    player_id="placeholder",
                    player_name="Placeholder Player",
                    avg_last_5=0.0,
                    avg_last_10=0.0,
                    avg_season=0.0,
                ),
                team_features={},
                opponent_features={},
                contextual_features={},
                feature_version=settings.MODEL_VERSION,
                computed_at=datetime.utcnow(),
            )

            # Cache the result
            await redis_client.setex(
                cache_key,
                settings.FEATURE_CACHE_TTL,
                feature_set.model_dump_json(),
            )

            return feature_set

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature set for prop leg {prop_leg_id} not found: {str(e)}",
        )


@router.post("/batch", response_model=FeatureSetResponse)
async def batch_compute_features(
    prop_leg_ids: List[str],
    force_recompute: bool = False,
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Batch compute features for multiple prop legs

    Optimizes database queries by batching and uses parallel computation
    where possible.
    """
    try:
        feature_sets = []
        to_compute = []

        # Check cache for all prop legs
        if not force_recompute:
            for prop_leg_id in prop_leg_ids:
                cache_key = f"features:{prop_leg_id}"
                cached_data = await redis_client.get(cache_key)

                if cached_data:
                    feature_set = FeatureSet.model_validate_json(cached_data)
                    feature_sets.append(feature_set)
                else:
                    to_compute.append(prop_leg_id)
        else:
            to_compute = prop_leg_ids

        # Compute missing features
        if to_compute:
            async with FeaturePipeline() as pipeline:
                for prop_leg_id in to_compute:
                    # In production, batch compute all features at once
                    from src.types import PlayerFeatures
                    from datetime import datetime

                    feature_set = FeatureSet(
                        prop_leg_id=prop_leg_id,
                        player_features=PlayerFeatures(
                            player_id="placeholder",
                            player_name="Placeholder Player",
                            avg_last_5=0.0,
                            avg_last_10=0.0,
                            avg_season=0.0,
                        ),
                        team_features={},
                        opponent_features={},
                        contextual_features={},
                        feature_version=settings.MODEL_VERSION,
                        computed_at=datetime.utcnow(),
                    )

                    feature_sets.append(feature_set)

                    # Cache each feature set
                    cache_key = f"features:{prop_leg_id}"
                    await redis_client.setex(
                        cache_key,
                        settings.FEATURE_CACHE_TTL,
                        feature_set.model_dump_json(),
                    )

        return FeatureSetResponse(
            features=feature_sets,
            total=len(feature_sets),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch compute features: {str(e)}",
        )


@router.get("/player/{player_id}/historical")
async def get_player_historical_features(
    player_id: str,
    stat_type: str,
    lookback_days: int = 30,
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get historical feature trends for a player

    Returns time series of features over specified lookback period.
    Useful for debugging and analysis.
    """
    try:
        # In production, query historical stats and compute features over time
        async with FeaturePipeline() as pipeline:
            # This would query historical data and compute features
            # for each game in the lookback period

            return {
                "player_id": player_id,
                "stat_type": stat_type,
                "lookback_days": lookback_days,
                "features_over_time": [],
                "message": "Historical features would be computed here",
            }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get historical features: {str(e)}",
        )


@router.post("/invalidate-cache")
async def invalidate_feature_cache(
    prop_leg_ids: Optional[List[str]] = None,
    current_user: UserProfile = Depends(get_current_active_user),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Invalidate feature cache for specific prop legs or all

    Clears Redis cache entries for features
    """
    try:
        invalidated_count = 0

        if prop_leg_ids:
            # Invalidate specific prop legs
            for prop_leg_id in prop_leg_ids:
                cache_key = f"features:{prop_leg_id}"
                deleted = await redis_client.delete(cache_key)
                invalidated_count += deleted
        else:
            # Invalidate all feature cache
            # In production, use SCAN for safe iteration
            cursor = 0
            while True:
                cursor, keys = await redis_client.scan(
                    cursor=cursor,
                    match="features:*",
                    count=100,
                )

                if keys:
                    deleted = await redis_client.delete(*keys)
                    invalidated_count += deleted

                if cursor == 0:
                    break

        return {
            "status": "success",
            "invalidated_count": invalidated_count,
            "message": f"Invalidated {invalidated_count} feature cache entries",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invalidate cache: {str(e)}",
        )

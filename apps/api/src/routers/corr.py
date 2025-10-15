"""
Correlations Router
Endpoints for computing correlations between prop legs
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis
from datetime import datetime

from src.types import (
    CorrelationMatrix,
    CorrelationRequest,
    CorrelationPair,
    UserProfile,
)
from src.auth.deps import get_current_active_user
from src.db import get_db, get_redis
from src.corr import CorrelationAnalyzer, CopulaModel, CorrelatedSampler
from src.config import settings

router = APIRouter()


@router.post("/", response_model=CorrelationMatrix)
async def compute_correlations(
    request: CorrelationRequest,
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Compute correlation matrix for specified prop legs

    Uses CorrelationAnalyzer to:
    - Calculate pairwise Spearman correlations
    - Compute statistical significance (p-values)
    - Filter by minimum sample size
    - Apply domain-specific adjustments

    Results are cached with TTL
    """
    try:
        # Check cache first
        cache_key = f"correlation_matrix:{'-'.join(sorted(request.prop_leg_ids))}:{request.lookback_days}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return CorrelationMatrix.model_validate_json(cached_data)

        # Initialize correlation analyzer
        analyzer = CorrelationAnalyzer(db_session=db, redis_client=redis_client)

        # Compute correlations
        # In production, fetch historical data and compute actual correlations
        # correlation_df = await analyzer.compute_correlations(
        #     prop_leg_ids=request.prop_leg_ids,
        #     lookback_days=request.lookback_days,
        #     min_sample_size=request.min_sample_size,
        # )

        # For now, create placeholder correlations
        correlations = []
        for i, leg_id_1 in enumerate(request.prop_leg_ids):
            for leg_id_2 in request.prop_leg_ids[i+1:]:
                correlation = CorrelationPair(
                    leg_id_1=leg_id_1,
                    leg_id_2=leg_id_2,
                    player_1=f"Player {i+1}",
                    player_2=f"Player {i+2}",
                    stat_type_1="points",
                    stat_type_2="points",
                    correlation=0.15,
                    sample_size=30,
                    p_value=0.05,
                    is_significant=True,
                )
                correlations.append(correlation)

        correlation_matrix = CorrelationMatrix(
            prop_leg_ids=request.prop_leg_ids,
            correlations=correlations,
            computed_at=datetime.utcnow(),
            lookback_days=request.lookback_days,
            min_sample_size=request.min_sample_size,
        )

        # Cache the result
        await redis_client.setex(
            cache_key,
            settings.REDIS_CACHE_TTL,
            correlation_matrix.model_dump_json(),
        )

        return correlation_matrix

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute correlations: {str(e)}",
        )


@router.get("/{prop_leg_id}/related")
async def get_related_props(
    prop_leg_id: str,
    min_correlation: float = 0.3,
    max_results: int = 10,
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Find props with highest correlation to specified prop leg

    Returns top correlated props sorted by absolute correlation value
    """
    try:
        analyzer = CorrelationAnalyzer(db_session=db, redis_client=redis_client)

        # In production, query correlation database
        # related = await analyzer.find_related_props(
        #     prop_leg_id=prop_leg_id,
        #     min_correlation=min_correlation,
        #     limit=max_results,
        # )

        return {
            "prop_leg_id": prop_leg_id,
            "related_props": [
                {
                    "prop_leg_id": f"related_{i}",
                    "player_name": f"Related Player {i}",
                    "stat_type": "points",
                    "correlation": 0.5 - (i * 0.05),
                    "sample_size": 30,
                    "p_value": 0.01,
                }
                for i in range(min(5, max_results))
            ],
            "min_correlation": min_correlation,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find related props: {str(e)}",
        )


@router.post("/matrix")
async def get_correlation_matrix(
    prop_leg_ids: List[str],
    lookback_days: int = 30,
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Get full correlation matrix for a set of prop legs

    Returns matrix format suitable for visualization
    """
    try:
        analyzer = CorrelationAnalyzer(db_session=db, redis_client=redis_client)

        # In production, compute full correlation matrix
        # matrix = await analyzer.compute_matrix(
        #     prop_leg_ids=prop_leg_ids,
        #     lookback_days=lookback_days,
        # )

        # Create placeholder matrix
        n = len(prop_leg_ids)
        matrix = [[0.0] * n for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix[i][j] = 1.0
                else:
                    matrix[i][j] = 0.15

        return {
            "matrix": matrix,
            "prop_leg_ids": prop_leg_ids,
            "lookback_days": lookback_days,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get correlation matrix: {str(e)}",
        )


@router.get("/player/{player_id}/stats")
async def get_player_stat_correlations(
    player_id: str,
    lookback_days: int = 30,
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get correlations between different stat types for a player

    Useful for understanding player tendencies (e.g., points-rebounds correlation)
    """
    try:
        analyzer = CorrelationAnalyzer(db_session=db)

        # In production, fetch historical stats and compute correlations
        # correlations = await analyzer.compute_player_stat_correlations(
        #     player_id=player_id,
        #     lookback_days=lookback_days,
        # )

        return {
            "player_id": player_id,
            "stat_correlations": [
                {"stat_1": "points", "stat_2": "rebounds", "correlation": -0.12},
                {"stat_1": "points", "stat_2": "assists", "correlation": 0.25},
                {"stat_1": "rebounds", "stat_2": "assists", "correlation": -0.08},
            ],
            "lookback_days": lookback_days,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get player stat correlations: {str(e)}",
        )


@router.post("/team/{team_id}/player-correlations")
async def get_team_player_correlations(
    team_id: str,
    stat_type: str,
    lookback_days: int = 30,
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get correlations between players on the same team

    Identifies substitution patterns and usage interactions
    """
    try:
        analyzer = CorrelationAnalyzer(db_session=db)

        # In production, analyze team player correlations
        # correlations = await analyzer.compute_team_player_correlations(
        #     team_id=team_id,
        #     stat_type=stat_type,
        #     lookback_days=lookback_days,
        # )

        return {
            "team_id": team_id,
            "stat_type": stat_type,
            "player_correlations": [
                {
                    "player_1": "Player A",
                    "player_2": "Player B",
                    "correlation": -0.35,
                    "reason": "Substitution pattern - rarely play together",
                },
                {
                    "player_1": "Player C",
                    "player_2": "Player D",
                    "correlation": 0.45,
                    "reason": "High usage together - pick and roll combination",
                },
            ],
            "lookback_days": lookback_days,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team player correlations: {str(e)}",
        )


@router.delete("/cache")
async def clear_correlation_cache(
    current_user: UserProfile = Depends(get_current_active_user),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Clear all cached correlation data

    Invalidates Redis cache for correlations
    """
    try:
        cleared_count = 0

        # Use SCAN for safe iteration over cache keys
        cursor = 0
        while True:
            cursor, keys = await redis_client.scan(
                cursor=cursor,
                match="correlation*",
                count=100,
            )

            if keys:
                deleted = await redis_client.delete(*keys)
                cleared_count += deleted

            if cursor == 0:
                break

        return {
            "status": "success",
            "cleared_count": cleared_count,
            "message": f"Cleared {cleared_count} correlation cache entries",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}",
        )

"""
Snapshots Router
Endpoints for managing snapshots of props and predictions
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from src.types import (
    Snapshot,
    SnapshotCreate,
    SnapshotResponse,
    Sport,
    UserProfile,
    PropMarket,
    ModelPrediction,
    CorrelationMatrix,
)
from src.auth.deps import get_current_active_user
from src.db import get_db, get_redis
from src.snapshots import SnapshotManager, SnapshotError

router = APIRouter()


@router.get("/", response_model=SnapshotResponse)
async def list_snapshots(
    sport: Optional[Sport] = None,
    tag: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    List snapshots with filtering

    Retrieves user's snapshots with optional filters for sport and tags
    """
    try:
        manager = SnapshotManager(db=db, redis_client=redis_client)

        offset = (page - 1) * page_size
        snapshots, total = await manager.list_snapshots(
            user_id=current_user.user_id,
            sport=sport,
            tag=tag,
            limit=page_size,
            offset=offset,
        )

        return SnapshotResponse(
            snapshots=snapshots,
            total=total,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list snapshots: {str(e)}",
        )


@router.get("/{snapshot_id}", response_model=Snapshot)
async def get_snapshot(
    snapshot_id: str,
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Get detailed snapshot information

    Returns complete snapshot with all metadata
    """
    try:
        manager = SnapshotManager(db=db, redis_client=redis_client)

        snapshot = await manager.get_snapshot(
            snapshot_id=snapshot_id,
            user_id=current_user.user_id,
        )

        if not snapshot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Snapshot {snapshot_id} not found",
            )

        return snapshot

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get snapshot: {str(e)}",
        )


@router.post("/", response_model=Snapshot, status_code=status.HTTP_201_CREATED)
async def create_snapshot(
    request: SnapshotCreate,
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Create a new snapshot

    Captures current state of:
    - Prop markets
    - Model predictions
    - Correlation matrix
    - Context data
    """
    try:
        manager = SnapshotManager(db=db, redis_client=redis_client)

        # In production, fetch actual prop markets and predictions
        # For now, create placeholders
        prop_markets = []
        predictions = []
        correlations = None

        # Fetch data for the requested prop legs
        # prop_markets = await get_prop_markets(request.prop_leg_ids, db)
        # predictions = await get_predictions(request.prop_leg_ids, redis_client)
        # correlations = await compute_correlations(request.prop_leg_ids, db)

        snapshot = await manager.create_snapshot(
            name=request.name,
            user_id=current_user.user_id,
            sport=request.sport,
            prop_markets=prop_markets,
            predictions=predictions,
            correlations=correlations,
            description=request.description,
            game_date=request.game_date,
            tags=request.tags,
        )

        return snapshot

    except SnapshotError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create snapshot: {str(e)}",
        )


@router.put("/{snapshot_id}", response_model=Snapshot)
async def update_snapshot(
    snapshot_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[list[str]] = None,
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Update snapshot metadata (name, description, tags)

    Only mutable fields can be updated. Snapshot data is immutable.
    """
    try:
        manager = SnapshotManager(db=db, redis_client=redis_client)

        snapshot = await manager.update_snapshot(
            snapshot_id=snapshot_id,
            user_id=current_user.user_id,
            name=name,
            description=description,
            tags=tags,
        )

        if not snapshot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Snapshot {snapshot_id} not found or is locked",
            )

        return snapshot

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update snapshot: {str(e)}",
        )


@router.delete("/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_snapshot(
    snapshot_id: str,
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Delete a snapshot

    Cannot delete locked snapshots
    """
    try:
        manager = SnapshotManager(db=db, redis_client=redis_client)

        deleted = await manager.delete_snapshot(
            snapshot_id=snapshot_id,
            user_id=current_user.user_id,
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Snapshot {snapshot_id} not found or is locked",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete snapshot: {str(e)}",
        )


@router.post("/{snapshot_id}/lock")
async def lock_snapshot(
    snapshot_id: str,
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Lock snapshot to prevent modifications

    Locked snapshots cannot be updated or deleted
    """
    try:
        manager = SnapshotManager(db=db, redis_client=redis_client)

        locked = await manager.lock_snapshot(
            snapshot_id=snapshot_id,
            user_id=current_user.user_id,
        )

        if not locked:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Snapshot {snapshot_id} not found",
            )

        return {
            "snapshot_id": snapshot_id,
            "is_locked": True,
            "message": "Snapshot locked successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to lock snapshot: {str(e)}",
        )


@router.post("/{snapshot_id}/compare/{other_snapshot_id}")
async def compare_snapshots(
    snapshot_id: str,
    other_snapshot_id: str,
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Compare two snapshots

    Analyzes differences in:
    - Markets count
    - Predictions count
    - Average confidence
    - Time delta
    """
    try:
        manager = SnapshotManager(db=db, redis_client=redis_client)

        comparison = await manager.compare_snapshots(
            snapshot_id_1=snapshot_id,
            snapshot_id_2=other_snapshot_id,
            user_id=current_user.user_id,
        )

        if not comparison:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both snapshots not found",
            )

        return comparison

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare snapshots: {str(e)}",
        )


@router.get("/{snapshot_id}/outcomes")
async def get_snapshot_outcomes(
    snapshot_id: str,
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Get actual outcomes for props in a snapshot

    Compares predictions to actual results and calculates accuracy metrics
    """
    try:
        manager = SnapshotManager(db=db, redis_client=redis_client)

        # Get snapshot data
        snapshot_data = await manager.get_snapshot_data(
            snapshot_id=snapshot_id,
            user_id=current_user.user_id,
        )

        if not snapshot_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Snapshot {snapshot_id} not found",
            )

        # In production, fetch actual game results and compare
        # outcomes = await fetch_outcomes_for_snapshot(snapshot_data)
        # accuracy = calculate_accuracy_metrics(snapshot_data, outcomes)

        return {
            "snapshot_id": snapshot_id,
            "outcomes": [
                {
                    "prop_leg_id": "leg_1",
                    "player_name": "Player 1",
                    "predicted_value": 25.5,
                    "actual_value": 27.0,
                    "line": 24.5,
                    "prediction": "over",
                    "result": "over",
                    "correct": True,
                },
            ],
            "accuracy_metrics": {
                "total_props": 15,
                "correct_predictions": 10,
                "accuracy": 0.667,
                "brier_score": 0.18,
                "avg_predicted_prob": 0.62,
                "avg_actual_prob": 0.64,
            },
            "game_date": snapshot_data.get("game_date"),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get snapshot outcomes: {str(e)}",
        )


@router.get("/{snapshot_id}/export")
async def export_snapshot(
    snapshot_id: str,
    format: str = "json",
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Export snapshot data in various formats

    Supports: json, csv
    """
    try:
        manager = SnapshotManager(db=db, redis_client=redis_client)

        snapshot_data = await manager.get_snapshot_data(
            snapshot_id=snapshot_id,
            user_id=current_user.user_id,
        )

        if not snapshot_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Snapshot {snapshot_id} not found",
            )

        if format == "json":
            return snapshot_data
        elif format == "csv":
            # In production, convert to CSV format
            return {
                "format": "csv",
                "download_url": f"/snapshots/{snapshot_id}/download.csv",
                "message": "CSV export not yet implemented",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format: {format}",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export snapshot: {str(e)}",
        )

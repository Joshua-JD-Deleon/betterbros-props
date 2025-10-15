"""
Snapshot Manager for capturing and managing point-in-time data

Handles:
- Creating snapshots of prop markets and predictions
- Storing snapshot data in database
- Comparing snapshots over time
- Analyzing outcomes against snapshots
"""
import json
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import redis.asyncio as redis

from src.db import Snapshot as SnapshotModel
from src.types import (
    Snapshot,
    SnapshotCreate,
    PropMarket,
    ModelPrediction,
    CorrelationMatrix,
    Sport,
)


class SnapshotError(Exception):
    """Base exception for snapshot operations"""
    pass


class SnapshotManager:
    """
    Manages snapshots of prop markets and predictions

    Snapshots capture a point-in-time view of:
    - Prop markets available
    - Model predictions
    - Correlation matrices
    - Context data

    This enables:
    - Historical analysis
    - Model performance tracking
    - What-if comparisons
    - Audit trails
    """

    def __init__(self, db: AsyncSession, redis_client: Optional[redis.Redis] = None):
        """
        Initialize snapshot manager

        Args:
            db: Database session
            redis_client: Optional Redis client for caching
        """
        self.db = db
        self.redis = redis_client

    async def create_snapshot(
        self,
        name: str,
        user_id: str,
        sport: Sport,
        prop_markets: List[PropMarket],
        predictions: List[ModelPrediction],
        correlations: Optional[CorrelationMatrix] = None,
        description: Optional[str] = None,
        game_date: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
    ) -> Snapshot:
        """
        Create a new snapshot

        Args:
            name: Snapshot name
            user_id: User creating the snapshot
            sport: Sport for this snapshot
            prop_markets: List of prop markets to snapshot
            predictions: List of predictions to snapshot
            correlations: Optional correlation matrix
            description: Optional description
            game_date: Optional game date
            tags: Optional tags for categorization

        Returns:
            Created snapshot

        Raises:
            SnapshotError: If snapshot creation fails
        """
        try:
            # Serialize data
            prop_market_ids = [pm.id for pm in prop_markets]
            prediction_ids = [pred.prop_leg_id for pred in predictions]

            # Store full data as JSON
            markets_data = [pm.model_dump() for pm in prop_markets]
            predictions_data = [pred.model_dump() for pred in predictions]
            correlations_data = correlations.model_dump() if correlations else None

            # Create database record
            snapshot_db = SnapshotModel(
                name=name,
                description=description,
                user_id=user_id,
                sport=sport.value,
                game_date=game_date,
                tags=tags or [],
                prop_market_ids=prop_market_ids,
                prediction_ids=prediction_ids,
                markets_data=markets_data,
                predictions_data=predictions_data,
                correlations_data=correlations_data,
                is_locked=False,
                created_at=datetime.utcnow(),
            )

            self.db.add(snapshot_db)
            await self.db.commit()
            await self.db.refresh(snapshot_db)

            # Convert to Pydantic model
            snapshot = Snapshot(
                id=snapshot_db.id,
                name=snapshot_db.name,
                description=snapshot_db.description,
                prop_markets=prop_market_ids,
                predictions=prediction_ids,
                correlations=str(snapshot_db.id) if correlations else None,
                sport=Sport(snapshot_db.sport),
                created_by=snapshot_db.user_id,
                created_at=snapshot_db.created_at,
                game_date=snapshot_db.game_date,
                is_locked=snapshot_db.is_locked,
                tags=snapshot_db.tags,
            )

            # Cache in Redis if available
            if self.redis:
                await self._cache_snapshot(snapshot_db.id, snapshot)

            return snapshot

        except Exception as e:
            await self.db.rollback()
            raise SnapshotError(f"Failed to create snapshot: {str(e)}") from e

    async def get_snapshot(self, snapshot_id: str, user_id: Optional[str] = None) -> Optional[Snapshot]:
        """
        Get a snapshot by ID

        Args:
            snapshot_id: Snapshot ID
            user_id: Optional user ID for access control

        Returns:
            Snapshot if found, None otherwise
        """
        # Check cache first
        if self.redis:
            cached = await self._get_cached_snapshot(snapshot_id)
            if cached:
                # Verify user access if needed
                if user_id and cached.created_by != user_id:
                    return None
                return cached

        # Query database
        query = select(SnapshotModel).where(SnapshotModel.id == snapshot_id)
        if user_id:
            query = query.where(SnapshotModel.user_id == user_id)

        result = await self.db.execute(query)
        snapshot_db = result.scalar_one_or_none()

        if not snapshot_db:
            return None

        # Convert to Pydantic model
        snapshot = Snapshot(
            id=snapshot_db.id,
            name=snapshot_db.name,
            description=snapshot_db.description,
            prop_markets=snapshot_db.prop_market_ids,
            predictions=snapshot_db.prediction_ids,
            correlations=str(snapshot_db.id) if snapshot_db.correlations_data else None,
            sport=Sport(snapshot_db.sport),
            created_by=snapshot_db.user_id,
            created_at=snapshot_db.created_at,
            game_date=snapshot_db.game_date,
            is_locked=snapshot_db.is_locked,
            tags=snapshot_db.tags,
        )

        # Cache it
        if self.redis:
            await self._cache_snapshot(snapshot_id, snapshot)

        return snapshot

    async def list_snapshots(
        self,
        user_id: str,
        sport: Optional[Sport] = None,
        tag: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[Snapshot], int]:
        """
        List snapshots for a user

        Args:
            user_id: User ID
            sport: Optional sport filter
            tag: Optional tag filter
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            Tuple of (snapshots list, total count)
        """
        # Build query
        query = select(SnapshotModel).where(SnapshotModel.user_id == user_id)

        if sport:
            query = query.where(SnapshotModel.sport == sport.value)

        if tag:
            query = query.where(SnapshotModel.tags.contains([tag]))

        # Get total count
        from sqlalchemy import func
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.order_by(SnapshotModel.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        snapshots_db = result.scalars().all()

        # Convert to Pydantic models
        snapshots = [
            Snapshot(
                id=s.id,
                name=s.name,
                description=s.description,
                prop_markets=s.prop_market_ids,
                predictions=s.prediction_ids,
                correlations=str(s.id) if s.correlations_data else None,
                sport=Sport(s.sport),
                created_by=s.user_id,
                created_at=s.created_at,
                game_date=s.game_date,
                is_locked=s.is_locked,
                tags=s.tags,
            )
            for s in snapshots_db
        ]

        return snapshots, total

    async def update_snapshot(
        self,
        snapshot_id: str,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[Snapshot]:
        """
        Update snapshot metadata

        Args:
            snapshot_id: Snapshot ID
            user_id: User ID (for access control)
            name: New name
            description: New description
            tags: New tags

        Returns:
            Updated snapshot if successful, None if not found or locked
        """
        # Get snapshot
        query = select(SnapshotModel).where(
            and_(
                SnapshotModel.id == snapshot_id,
                SnapshotModel.user_id == user_id,
            )
        )
        result = await self.db.execute(query)
        snapshot_db = result.scalar_one_or_none()

        if not snapshot_db or snapshot_db.is_locked:
            return None

        # Update fields
        if name is not None:
            snapshot_db.name = name
        if description is not None:
            snapshot_db.description = description
        if tags is not None:
            snapshot_db.tags = tags

        snapshot_db.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(snapshot_db)

        # Convert to Pydantic model
        snapshot = Snapshot(
            id=snapshot_db.id,
            name=snapshot_db.name,
            description=snapshot_db.description,
            prop_markets=snapshot_db.prop_market_ids,
            predictions=snapshot_db.prediction_ids,
            correlations=str(snapshot_db.id) if snapshot_db.correlations_data else None,
            sport=Sport(snapshot_db.sport),
            created_by=snapshot_db.user_id,
            created_at=snapshot_db.created_at,
            game_date=snapshot_db.game_date,
            is_locked=snapshot_db.is_locked,
            tags=snapshot_db.tags,
        )

        # Invalidate cache
        if self.redis:
            await self._invalidate_cache(snapshot_id)

        return snapshot

    async def delete_snapshot(self, snapshot_id: str, user_id: str) -> bool:
        """
        Delete a snapshot

        Args:
            snapshot_id: Snapshot ID
            user_id: User ID (for access control)

        Returns:
            True if deleted, False if not found or locked
        """
        query = select(SnapshotModel).where(
            and_(
                SnapshotModel.id == snapshot_id,
                SnapshotModel.user_id == user_id,
            )
        )
        result = await self.db.execute(query)
        snapshot_db = result.scalar_one_or_none()

        if not snapshot_db or snapshot_db.is_locked:
            return False

        await self.db.delete(snapshot_db)
        await self.db.commit()

        # Invalidate cache
        if self.redis:
            await self._invalidate_cache(snapshot_id)

        return True

    async def lock_snapshot(self, snapshot_id: str, user_id: str) -> bool:
        """
        Lock a snapshot to prevent modifications

        Args:
            snapshot_id: Snapshot ID
            user_id: User ID (for access control)

        Returns:
            True if locked, False if not found
        """
        query = select(SnapshotModel).where(
            and_(
                SnapshotModel.id == snapshot_id,
                SnapshotModel.user_id == user_id,
            )
        )
        result = await self.db.execute(query)
        snapshot_db = result.scalar_one_or_none()

        if not snapshot_db:
            return False

        snapshot_db.is_locked = True
        snapshot_db.updated_at = datetime.utcnow()

        await self.db.commit()

        # Invalidate cache
        if self.redis:
            await self._invalidate_cache(snapshot_id)

        return True

    async def get_snapshot_data(self, snapshot_id: str, user_id: Optional[str] = None) -> Optional[Dict]:
        """
        Get full snapshot data including markets and predictions

        Args:
            snapshot_id: Snapshot ID
            user_id: Optional user ID for access control

        Returns:
            Dictionary with full snapshot data
        """
        query = select(SnapshotModel).where(SnapshotModel.id == snapshot_id)
        if user_id:
            query = query.where(SnapshotModel.user_id == user_id)

        result = await self.db.execute(query)
        snapshot_db = result.scalar_one_or_none()

        if not snapshot_db:
            return None

        return {
            "id": snapshot_db.id,
            "name": snapshot_db.name,
            "description": snapshot_db.description,
            "sport": snapshot_db.sport,
            "created_by": snapshot_db.user_id,
            "created_at": snapshot_db.created_at.isoformat(),
            "game_date": snapshot_db.game_date.isoformat() if snapshot_db.game_date else None,
            "is_locked": snapshot_db.is_locked,
            "tags": snapshot_db.tags,
            "markets": snapshot_db.markets_data,
            "predictions": snapshot_db.predictions_data,
            "correlations": snapshot_db.correlations_data,
        }

    async def compare_snapshots(
        self,
        snapshot_id_1: str,
        snapshot_id_2: str,
        user_id: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Compare two snapshots

        Args:
            snapshot_id_1: First snapshot ID
            snapshot_id_2: Second snapshot ID
            user_id: Optional user ID for access control

        Returns:
            Comparison analysis dictionary
        """
        # Get both snapshots
        snapshot_1_data = await self.get_snapshot_data(snapshot_id_1, user_id)
        snapshot_2_data = await self.get_snapshot_data(snapshot_id_2, user_id)

        if not snapshot_1_data or not snapshot_2_data:
            return None

        # Basic comparison
        comparison = {
            "snapshot_1": {
                "id": snapshot_1_data["id"],
                "name": snapshot_1_data["name"],
                "created_at": snapshot_1_data["created_at"],
            },
            "snapshot_2": {
                "id": snapshot_2_data["id"],
                "name": snapshot_2_data["name"],
                "created_at": snapshot_2_data["created_at"],
            },
            "metrics": {
                "markets_count_delta": len(snapshot_2_data["markets"]) - len(snapshot_1_data["markets"]),
                "predictions_count_delta": len(snapshot_2_data["predictions"]) - len(snapshot_1_data["predictions"]),
            },
            "time_delta_hours": (
                datetime.fromisoformat(snapshot_2_data["created_at"]) -
                datetime.fromisoformat(snapshot_1_data["created_at"])
            ).total_seconds() / 3600,
        }

        # Compare average prediction confidence if available
        if snapshot_1_data["predictions"] and snapshot_2_data["predictions"]:
            avg_conf_1 = sum(p.get("confidence", 0) for p in snapshot_1_data["predictions"]) / len(snapshot_1_data["predictions"])
            avg_conf_2 = sum(p.get("confidence", 0) for p in snapshot_2_data["predictions"]) / len(snapshot_2_data["predictions"])
            comparison["metrics"]["avg_confidence_delta"] = avg_conf_2 - avg_conf_1

        return comparison

    async def _cache_snapshot(self, snapshot_id: str, snapshot: Snapshot) -> None:
        """Cache snapshot in Redis"""
        if not self.redis:
            return

        try:
            cache_key = f"snapshot:{snapshot_id}"
            await self.redis.setex(
                cache_key,
                3600,  # 1 hour TTL
                snapshot.model_dump_json(),
            )
        except Exception:
            # Don't fail if caching fails
            pass

    async def _get_cached_snapshot(self, snapshot_id: str) -> Optional[Snapshot]:
        """Get cached snapshot from Redis"""
        if not self.redis:
            return None

        try:
            cache_key = f"snapshot:{snapshot_id}"
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                return Snapshot.model_validate_json(cached_data)
        except Exception:
            # Don't fail if cache read fails
            pass

        return None

    async def _invalidate_cache(self, snapshot_id: str) -> None:
        """Invalidate cached snapshot"""
        if not self.redis:
            return

        try:
            cache_key = f"snapshot:{snapshot_id}"
            await self.redis.delete(cache_key)
        except Exception:
            # Don't fail if cache invalidation fails
            pass

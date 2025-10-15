"""
Feature Store for Persisting and Retrieving Engineered Features

Provides versioned storage of feature snapshots with metadata tracking,
using Parquet format for efficient columnar storage.
"""
import asyncio
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from redis.asyncio import Redis

from src.config import settings
from src.db import get_redis

logger = logging.getLogger(__name__)


class FeatureStoreError(Exception):
    """Custom exception for feature store errors"""
    pass


class FeatureStore:
    """
    Feature store for managing engineered feature snapshots

    Provides:
    - Versioned feature storage in Parquet format
    - Metadata tracking (schema, statistics, lineage)
    - Fast retrieval with Redis caching
    - Snapshot management (list, delete, archive)

    Storage structure:
        /data/snapshots/{snapshot_id}/
            features.parquet       - Main feature data
            metadata.json          - Snapshot metadata
            schema.json            - Feature schema
            statistics.json        - Feature statistics
    """

    DEFAULT_BASE_PATH = Path("/Users/joshuadeleon/BetterBros Bets/data/snapshots")
    CACHE_TTL = 3600  # 1 hour cache for features

    def __init__(
        self,
        base_path: Optional[Path] = None,
        enable_cache: bool = True,
    ):
        """
        Initialize feature store

        Args:
            base_path: Base directory for feature storage
            enable_cache: Enable Redis caching for fast retrieval
        """
        self.base_path = base_path or self.DEFAULT_BASE_PATH
        self.enable_cache = enable_cache

        # Create base directory if it doesn't exist
        self.base_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized feature store at {self.base_path}")

    def _get_snapshot_path(self, snapshot_id: str) -> Path:
        """Get path for a specific snapshot"""
        return self.base_path / snapshot_id

    def _get_features_path(self, snapshot_id: str) -> Path:
        """Get path for features.parquet file"""
        return self._get_snapshot_path(snapshot_id) / "features.parquet"

    def _get_metadata_path(self, snapshot_id: str) -> Path:
        """Get path for metadata.json file"""
        return self._get_snapshot_path(snapshot_id) / "metadata.json"

    def _get_schema_path(self, snapshot_id: str) -> Path:
        """Get path for schema.json file"""
        return self._get_snapshot_path(snapshot_id) / "schema.json"

    def _get_statistics_path(self, snapshot_id: str) -> Path:
        """Get path for statistics.json file"""
        return self._get_snapshot_path(snapshot_id) / "statistics.json"

    async def save_features(
        self,
        snapshot_id: str,
        features: pd.DataFrame,
        metadata: Optional[Dict[str, Any]] = None,
        compression: str = 'snappy',
    ) -> Dict[str, Any]:
        """
        Save feature snapshot to persistent storage

        Args:
            snapshot_id: Unique identifier for this snapshot
            features: Feature DataFrame to save
            metadata: Optional metadata dictionary
            compression: Compression algorithm for Parquet (snappy, gzip, etc.)

        Returns:
            Dictionary with save information

        Example:
            {
                "snapshot_id": "2024-10-14-week8-nfl",
                "path": "/data/snapshots/2024-10-14-week8-nfl/features.parquet",
                "rows": 1234,
                "columns": 87,
                "size_bytes": 524288,
                "compression": "snappy",
                "created_at": "2024-10-14T12:00:00Z"
            }
        """
        logger.info(f"Saving feature snapshot: {snapshot_id}")

        try:
            # Create snapshot directory
            snapshot_path = self._get_snapshot_path(snapshot_id)
            snapshot_path.mkdir(parents=True, exist_ok=True)

            # Save features to Parquet
            features_path = self._get_features_path(snapshot_id)
            features.to_parquet(
                features_path,
                engine='pyarrow',
                compression=compression,
                index=False,
            )

            # Calculate file size
            file_size = features_path.stat().st_size

            # Generate and save schema
            schema = self._extract_schema(features)
            schema_path = self._get_schema_path(snapshot_id)
            import json
            with open(schema_path, 'w') as f:
                json.dump(schema, f, indent=2)

            # Generate and save statistics
            statistics = self._compute_statistics(features)
            stats_path = self._get_statistics_path(snapshot_id)
            with open(stats_path, 'w') as f:
                json.dump(statistics, f, indent=2)

            # Create metadata
            if metadata is None:
                metadata = {}

            metadata.update({
                'snapshot_id': snapshot_id,
                'rows': len(features),
                'columns': len(features.columns),
                'feature_names': list(features.columns),
                'size_bytes': file_size,
                'compression': compression,
                'created_at': datetime.utcnow().isoformat(),
                'schema_version': '1.0.0',
            })

            # Save metadata
            metadata_path = self._get_metadata_path(snapshot_id)
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            # Cache in Redis
            if self.enable_cache:
                await self._cache_features(snapshot_id, features)

            logger.info(
                f"Saved snapshot {snapshot_id}: "
                f"{len(features)} rows, {len(features.columns)} columns, "
                f"{file_size / 1024:.2f} KB"
            )

            return {
                'snapshot_id': snapshot_id,
                'path': str(features_path),
                'rows': len(features),
                'columns': len(features.columns),
                'size_bytes': file_size,
                'compression': compression,
                'created_at': metadata['created_at'],
            }

        except Exception as e:
            logger.error(f"Failed to save feature snapshot {snapshot_id}: {e}")
            raise FeatureStoreError(f"Failed to save features: {str(e)}") from e

    async def load_features(
        self,
        snapshot_id: str,
        columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Load feature snapshot from storage

        Args:
            snapshot_id: Snapshot identifier
            columns: Optional list of columns to load (for efficiency)

        Returns:
            Feature DataFrame

        Raises:
            FeatureStoreError: If snapshot not found or load fails
        """
        logger.info(f"Loading feature snapshot: {snapshot_id}")

        try:
            # Check cache first
            if self.enable_cache:
                cached_features = await self._get_cached_features(snapshot_id)
                if cached_features is not None:
                    if columns:
                        return cached_features[columns]
                    return cached_features

            # Load from disk
            features_path = self._get_features_path(snapshot_id)

            if not features_path.exists():
                raise FeatureStoreError(f"Snapshot not found: {snapshot_id}")

            # Load with optional column filtering
            features = pd.read_parquet(
                features_path,
                engine='pyarrow',
                columns=columns,
            )

            # Cache for future use
            if self.enable_cache and columns is None:
                await self._cache_features(snapshot_id, features)

            logger.info(f"Loaded snapshot {snapshot_id}: {len(features)} rows, {len(features.columns)} columns")
            return features

        except FeatureStoreError:
            raise
        except Exception as e:
            logger.error(f"Failed to load feature snapshot {snapshot_id}: {e}")
            raise FeatureStoreError(f"Failed to load features: {str(e)}") from e

    async def get_metadata(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Get metadata for a snapshot

        Args:
            snapshot_id: Snapshot identifier

        Returns:
            Metadata dictionary
        """
        metadata_path = self._get_metadata_path(snapshot_id)

        if not metadata_path.exists():
            raise FeatureStoreError(f"Snapshot metadata not found: {snapshot_id}")

        import json
        with open(metadata_path, 'r') as f:
            return json.load(f)

    async def get_schema(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Get schema for a snapshot

        Args:
            snapshot_id: Snapshot identifier

        Returns:
            Schema dictionary
        """
        schema_path = self._get_schema_path(snapshot_id)

        if not schema_path.exists():
            raise FeatureStoreError(f"Snapshot schema not found: {snapshot_id}")

        import json
        with open(schema_path, 'r') as f:
            return json.load(f)

    async def get_statistics(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Get statistics for a snapshot

        Args:
            snapshot_id: Snapshot identifier

        Returns:
            Statistics dictionary
        """
        stats_path = self._get_statistics_path(snapshot_id)

        if not stats_path.exists():
            raise FeatureStoreError(f"Snapshot statistics not found: {snapshot_id}")

        import json
        with open(stats_path, 'r') as f:
            return json.load(f)

    async def list_snapshots(self) -> List[Dict[str, Any]]:
        """
        List all available snapshots

        Returns:
            List of snapshot metadata dictionaries
        """
        snapshots = []

        for snapshot_dir in self.base_path.iterdir():
            if snapshot_dir.is_dir():
                snapshot_id = snapshot_dir.name
                try:
                    metadata = await self.get_metadata(snapshot_id)
                    snapshots.append(metadata)
                except Exception as e:
                    logger.warning(f"Failed to load metadata for {snapshot_id}: {e}")

        # Sort by creation date (newest first)
        snapshots.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        return snapshots

    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        Delete a snapshot and all its files

        Args:
            snapshot_id: Snapshot identifier

        Returns:
            True if deleted successfully
        """
        logger.info(f"Deleting snapshot: {snapshot_id}")

        snapshot_path = self._get_snapshot_path(snapshot_id)

        if not snapshot_path.exists():
            raise FeatureStoreError(f"Snapshot not found: {snapshot_id}")

        try:
            # Remove from cache
            if self.enable_cache:
                await self._invalidate_cache(snapshot_id)

            # Delete directory
            shutil.rmtree(snapshot_path)

            logger.info(f"Deleted snapshot {snapshot_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete snapshot {snapshot_id}: {e}")
            raise FeatureStoreError(f"Failed to delete snapshot: {str(e)}") from e

    async def snapshot_exists(self, snapshot_id: str) -> bool:
        """
        Check if a snapshot exists

        Args:
            snapshot_id: Snapshot identifier

        Returns:
            True if snapshot exists
        """
        features_path = self._get_features_path(snapshot_id)
        return features_path.exists()

    def _extract_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract schema information from DataFrame"""
        schema = {
            'columns': [],
            'total_columns': len(df.columns),
            'dtypes': {},
        }

        for col in df.columns:
            dtype = str(df[col].dtype)
            schema['columns'].append({
                'name': col,
                'dtype': dtype,
                'nullable': df[col].isna().any(),
            })
            schema['dtypes'][col] = dtype

        return schema

    def _compute_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute summary statistics for DataFrame"""
        stats = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'memory_usage_bytes': int(df.memory_usage(deep=True).sum()),
            'missing_values': {},
            'numeric_summary': {},
        }

        # Missing value counts
        for col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                stats['missing_values'][col] = {
                    'count': int(missing_count),
                    'percentage': float(missing_count / len(df) * 100),
                }

        # Numeric column statistics
        numeric_cols = df.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            if col in df.columns:
                try:
                    stats['numeric_summary'][col] = {
                        'mean': float(df[col].mean()) if not df[col].isna().all() else None,
                        'std': float(df[col].std()) if not df[col].isna().all() else None,
                        'min': float(df[col].min()) if not df[col].isna().all() else None,
                        'max': float(df[col].max()) if not df[col].isna().all() else None,
                        'median': float(df[col].median()) if not df[col].isna().all() else None,
                    }
                except Exception:
                    pass

        return stats

    async def _cache_features(self, snapshot_id: str, features: pd.DataFrame):
        """Cache features in Redis"""
        try:
            import pickle
            cache_key = f"feature_store:snapshot:{snapshot_id}"
            redis = await get_redis()

            try:
                serialized = pickle.dumps(features)
                await redis.setex(cache_key, self.CACHE_TTL, serialized)
                logger.debug(f"Cached features for {snapshot_id}")
            finally:
                await redis.close()

        except Exception as e:
            logger.warning(f"Failed to cache features: {e}")

    async def _get_cached_features(self, snapshot_id: str) -> Optional[pd.DataFrame]:
        """Get cached features from Redis"""
        try:
            import pickle
            cache_key = f"feature_store:snapshot:{snapshot_id}"
            redis = await get_redis()

            try:
                cached = await redis.get(cache_key)
                if cached:
                    logger.info(f"Cache HIT for snapshot {snapshot_id}")
                    return pickle.loads(cached)
                logger.info(f"Cache MISS for snapshot {snapshot_id}")
            finally:
                await redis.close()

        except Exception as e:
            logger.warning(f"Failed to retrieve cached features: {e}")

        return None

    async def _invalidate_cache(self, snapshot_id: str):
        """Invalidate cached features"""
        try:
            cache_key = f"feature_store:snapshot:{snapshot_id}"
            redis = await get_redis()

            try:
                await redis.delete(cache_key)
                logger.debug(f"Invalidated cache for {snapshot_id}")
            finally:
                await redis.close()

        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")

    async def get_storage_info(self) -> Dict[str, Any]:
        """
        Get information about feature store storage

        Returns:
            Storage information dictionary
        """
        snapshots = await self.list_snapshots()

        total_size = 0
        for snapshot in snapshots:
            total_size += snapshot.get('size_bytes', 0)

        return {
            'base_path': str(self.base_path),
            'total_snapshots': len(snapshots),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'snapshots': snapshots,
        }

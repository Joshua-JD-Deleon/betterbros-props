"""
Snapshot management for preserving analysis state with immutable snapshots.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import json
import yaml
import pandas as pd


class SnapshotManager:
    """
    Manages immutable snapshots of analysis state.
    """

    def __init__(self, snapshots_dir: Optional[Path] = None):
        """
        Initialize snapshot manager.

        Args:
            snapshots_dir: Directory to store snapshots
        """
        self.snapshots_dir = snapshots_dir or Path("./data/snapshots")
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def create_snapshot(
        self,
        props_df: pd.DataFrame,
        slips: List[dict],
        config: dict,
        week: Optional[int] = None,
        season: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create an immutable snapshot of current analysis state.

        Args:
            props_df: DataFrame with props and probabilities
            slips: List of generated slips
            config: Configuration settings used
            week: Optional week number
            season: Optional season year
            metadata: Optional additional metadata

        Returns:
            Snapshot ID (e.g., "2025_W5_20251011_143052")
        """
        # Generate snapshot ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if week and season:
            snapshot_id = f"{season}_W{week}_{timestamp}"
        else:
            snapshot_id = f"snapshot_{timestamp}"

        snapshot_path = self.snapshots_dir / snapshot_id
        snapshot_path.mkdir(exist_ok=True)

        # Save props as parquet
        props_path = snapshot_path / "props.parquet"
        props_df.to_parquet(props_path, index=False)

        # Save slips as JSON
        slips_path = snapshot_path / "slips.json"
        with open(slips_path, 'w') as f:
            json.dump(slips, f, indent=2, default=str)

        # Save config as YAML
        config_path = snapshot_path / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

        # Build metadata
        full_metadata = {
            "snapshot_id": snapshot_id,
            "timestamp": datetime.now().isoformat(),
            "week": week,
            "season": season,
            "num_props": len(props_df),
            "num_slips": len(slips),
            "props_columns": list(props_df.columns),
            "config_keys": list(config.keys()) if config else [],
        }

        # Merge with additional metadata
        if metadata:
            full_metadata.update(metadata)

        # Save metadata as JSON
        metadata_path = snapshot_path / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(full_metadata, f, indent=2, default=str)

        print(f"Created snapshot: {snapshot_id}")
        return snapshot_id

    def load_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Load a snapshot by ID.

        Args:
            snapshot_id: Snapshot identifier

        Returns:
            Dictionary with snapshot components:
                - props_df: Props DataFrame
                - slips: List of slips
                - config: Configuration dict
                - metadata: Metadata dict
        """
        snapshot_path = self.snapshots_dir / snapshot_id

        if not snapshot_path.exists():
            raise FileNotFoundError(f"Snapshot {snapshot_id} not found at {snapshot_path}")

        # Load props
        props_path = snapshot_path / "props.parquet"
        if props_path.exists():
            props_df = pd.read_parquet(props_path)
        else:
            raise FileNotFoundError(f"Props file not found in snapshot {snapshot_id}")

        # Load slips
        slips_path = snapshot_path / "slips.json"
        if slips_path.exists():
            with open(slips_path, 'r') as f:
                slips = json.load(f)
        else:
            slips = []

        # Load config
        config_path = snapshot_path / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        else:
            config = {}

        # Load metadata
        metadata_path = snapshot_path / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {}

        return {
            "props_df": props_df,
            "slips": slips,
            "config": config,
            "metadata": metadata
        }

    def list_snapshots(self) -> List[Dict[str, Any]]:
        """
        List all available snapshots with metadata.

        Returns:
            List of metadata dictionaries, sorted by timestamp (newest first)
        """
        snapshots = []

        # Find all snapshot directories
        for snapshot_dir in self.snapshots_dir.iterdir():
            if not snapshot_dir.is_dir():
                continue

            metadata_file = snapshot_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    snapshots.append(metadata)
            else:
                # Create minimal metadata from directory name
                snapshots.append({
                    "snapshot_id": snapshot_dir.name,
                    "timestamp": None,
                    "num_props": None,
                    "num_slips": None
                })

        # Sort by timestamp (newest first)
        snapshots.sort(
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )

        return snapshots

    def delete_snapshot(self, snapshot_id: str) -> None:
        """
        Delete a snapshot.

        Args:
            snapshot_id: Snapshot identifier
        """
        import shutil

        snapshot_path = self.snapshots_dir / snapshot_id

        if not snapshot_path.exists():
            raise FileNotFoundError(f"Snapshot {snapshot_id} not found")

        shutil.rmtree(snapshot_path)
        print(f"Deleted snapshot: {snapshot_id}")

    def cleanup_old_snapshots(self, retention_days: int = 30) -> int:
        """
        Remove snapshots older than retention period.

        Args:
            retention_days: Number of days to retain

        Returns:
            Number of snapshots removed
        """
        from datetime import timedelta
        import shutil

        cutoff_date = datetime.now() - timedelta(days=retention_days)
        removed_count = 0

        for snapshot_dir in self.snapshots_dir.iterdir():
            if not snapshot_dir.is_dir():
                continue

            metadata_file = snapshot_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)

                timestamp_str = metadata.get('timestamp')
                if timestamp_str:
                    try:
                        created_at = datetime.fromisoformat(timestamp_str)
                        if created_at < cutoff_date:
                            shutil.rmtree(snapshot_dir)
                            removed_count += 1
                            print(f"Removed old snapshot: {snapshot_dir.name}")
                    except ValueError:
                        # Skip if timestamp can't be parsed
                        pass

        return removed_count

    def get_latest_snapshot(
        self,
        week: Optional[int] = None,
        season: Optional[int] = None
    ) -> Optional[str]:
        """
        Get the ID of the most recent snapshot.

        Args:
            week: Optional week filter
            season: Optional season filter

        Returns:
            Snapshot ID or None if no snapshots found
        """
        snapshots = self.list_snapshots()

        if not snapshots:
            return None

        # Filter by week/season if provided
        if week is not None or season is not None:
            snapshots = [
                s for s in snapshots
                if (week is None or s.get('week') == week)
                and (season is None or s.get('season') == season)
            ]

        if not snapshots:
            return None

        return snapshots[0]['snapshot_id']

    def compare_snapshots(
        self,
        snapshot_id1: str,
        snapshot_id2: str
    ) -> Dict[str, Any]:
        """
        Compare two snapshots.

        Args:
            snapshot_id1: First snapshot ID
            snapshot_id2: Second snapshot ID

        Returns:
            Dictionary with comparison results
        """
        snap1 = self.load_snapshot(snapshot_id1)
        snap2 = self.load_snapshot(snapshot_id2)

        comparison = {
            'snapshot_1': snapshot_id1,
            'snapshot_2': snapshot_id2,
            'num_props': {
                'snapshot_1': len(snap1['props_df']),
                'snapshot_2': len(snap2['props_df']),
                'diff': len(snap2['props_df']) - len(snap1['props_df'])
            },
            'num_slips': {
                'snapshot_1': len(snap1['slips']),
                'snapshot_2': len(snap2['slips']),
                'diff': len(snap2['slips']) - len(snap1['slips'])
            }
        }

        # Compare average probabilities if available
        if 'prob_over' in snap1['props_df'].columns and 'prob_over' in snap2['props_df'].columns:
            comparison['avg_prob_over'] = {
                'snapshot_1': snap1['props_df']['prob_over'].mean(),
                'snapshot_2': snap2['props_df']['prob_over'].mean(),
                'diff': snap2['props_df']['prob_over'].mean() - snap1['props_df']['prob_over'].mean()
            }

        # Compare average odds if available
        if snap1['slips'] and snap2['slips']:
            avg_odds_1 = sum(s.get('total_odds', 0) for s in snap1['slips']) / len(snap1['slips'])
            avg_odds_2 = sum(s.get('total_odds', 0) for s in snap2['slips']) / len(snap2['slips'])
            comparison['avg_total_odds'] = {
                'snapshot_1': avg_odds_1,
                'snapshot_2': avg_odds_2,
                'diff': avg_odds_2 - avg_odds_1
            }

        return comparison


# Convenience functions
def lock_snapshot(
    props_df: pd.DataFrame,
    slips: List[dict],
    config: dict,
    week: Optional[int] = None,
    season: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
    snapshots_dir: Optional[Path] = None
) -> str:
    """
    Convenience function to create an immutable snapshot.

    Args:
        props_df: Props DataFrame
        slips: List of slips
        config: Configuration dict
        week: Optional week number
        season: Optional season year
        metadata: Optional metadata
        snapshots_dir: Optional snapshots directory

    Returns:
        Snapshot ID
    """
    manager = SnapshotManager(snapshots_dir=snapshots_dir)
    return manager.create_snapshot(
        props_df=props_df,
        slips=slips,
        config=config,
        week=week,
        season=season,
        metadata=metadata
    )


def load_snapshot(
    snapshot_id: str,
    snapshots_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Convenience function to load a snapshot.

    Args:
        snapshot_id: Snapshot identifier
        snapshots_dir: Optional snapshots directory

    Returns:
        Dictionary with snapshot data
    """
    manager = SnapshotManager(snapshots_dir=snapshots_dir)
    return manager.load_snapshot(snapshot_id)


def list_snapshots(snapshots_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Convenience function to list snapshots.

    Args:
        snapshots_dir: Optional snapshots directory

    Returns:
        List of snapshot metadata
    """
    manager = SnapshotManager(snapshots_dir=snapshots_dir)
    return manager.list_snapshots()


def delete_snapshot(
    snapshot_id: str,
    snapshots_dir: Optional[Path] = None
) -> None:
    """
    Convenience function to delete a snapshot.

    Args:
        snapshot_id: Snapshot identifier
        snapshots_dir: Optional snapshots directory
    """
    manager = SnapshotManager(snapshots_dir=snapshots_dir)
    manager.delete_snapshot(snapshot_id)

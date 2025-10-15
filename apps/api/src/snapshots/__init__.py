"""
Snapshot Management Module

Provides functionality for creating, managing, and analyzing snapshots
of prop markets and predictions at specific points in time.
"""
from .snapshot import SnapshotManager, SnapshotError

__all__ = [
    "SnapshotManager",
    "SnapshotError",
]

__version__ = "1.0.0"

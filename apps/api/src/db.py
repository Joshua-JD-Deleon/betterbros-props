"""
Database connection and health check utilities (backward compatibility)

This module provides backward compatibility with the old API.
All functionality has been moved to src/db/models.py and src/db/session.py

Usage:
    from src.db import Base, get_db, get_redis, check_db_connection
"""
# Import everything from new structure for backward compatibility
from src.db import (
    Base,
    User,
    Experiment,
    Snapshot,
    SavedSlip,
    PropMarket,
    engine,
    AsyncSessionLocal,
    get_db,
    get_db_session,
    get_redis,
    get_redis_client,
    check_db_connection,
    check_redis_connection,
    check_all_connections,
    init_connections,
    close_connections,
    init_db,
    close_db,
    init_redis,
    close_redis,
    get_db_info,
    get_redis_info,
)

__all__ = [
    # Models
    "Base",
    "User",
    "Experiment",
    "Snapshot",
    "SavedSlip",
    "PropMarket",
    # Session
    "engine",
    "AsyncSessionLocal",
    "get_db",
    "get_db_session",
    "get_redis",
    "get_redis_client",
    # Health checks
    "check_db_connection",
    "check_redis_connection",
    "check_all_connections",
    # Lifecycle
    "init_connections",
    "close_connections",
    "init_db",
    "close_db",
    "init_redis",
    "close_redis",
    # Info
    "get_db_info",
    "get_redis_info",
]

"""
Database package - SQLAlchemy models and session management

Exports:
    - All models (User, Experiment, Snapshot, SavedSlip, PropMarket)
    - Base for model declaration
    - Session dependencies (get_db, get_redis)
    - Connection lifecycle functions
    - Health check utilities
"""
from src.db.models import (
    Base,
    User,
    Experiment,
    Snapshot,
    SavedSlip,
    PropMarket,
)
from src.db.session import (
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

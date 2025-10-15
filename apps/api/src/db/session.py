"""
Database session management and connection utilities

Provides async database session factory, Redis connection pool,
and health check functions for FastAPI dependency injection.
"""
import logging
from typing import AsyncGenerator, Optional

from redis.asyncio import Redis, ConnectionPool
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool, QueuePool

from src.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Database Engine and Session Factory
# ============================================================================

def create_engine() -> AsyncEngine:
    """
    Create async database engine with proper configuration

    Uses connection pooling for production, NullPool for testing.
    """
    # Determine pool class based on environment
    if settings.ENVIRONMENT == "test":
        pool_class = NullPool
        pool_size = 0
        max_overflow = 0
    else:
        pool_class = QueuePool
        pool_size = settings.DATABASE_POOL_SIZE
        max_overflow = settings.DATABASE_MAX_OVERFLOW

    engine = create_async_engine(
        str(settings.DATABASE_URL),
        echo=settings.ENVIRONMENT == "development",
        pool_pre_ping=True,  # Enable pessimistic disconnect handling
        pool_size=pool_size,
        max_overflow=max_overflow,
        poolclass=pool_class,
        connect_args={
            "server_settings": {
                "application_name": "betterbros_api",
                "jit": "off",  # Disable JIT for more predictable performance
            },
            "command_timeout": 60,
            "timeout": 10,
        },
    )

    logger.info(
        f"Created database engine for {settings.ENVIRONMENT} environment "
        f"(pool_size={pool_size}, max_overflow={max_overflow})"
    )

    return engine


# Global engine instance
engine = create_engine()

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ============================================================================
# FastAPI Dependencies
# ============================================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()

    Yields:
        AsyncSession: Database session

    Note:
        Session is automatically closed after request completes.
        Uncommitted transactions are rolled back on error.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def get_db_session() -> AsyncSession:
    """
    Get a database session directly (not as a dependency)

    Usage:
        async with get_db_session() as session:
            result = await session.execute(query)

    Returns:
        AsyncSession: Database session context manager
    """
    return AsyncSessionLocal()


# ============================================================================
# Redis Connection Pool
# ============================================================================

def create_redis_pool() -> ConnectionPool:
    """
    Create Redis connection pool with proper configuration

    Returns:
        ConnectionPool: Redis connection pool
    """
    pool = ConnectionPool.from_url(
        settings.redis_url_str,
        max_connections=settings.REDIS_MAX_CONNECTIONS,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_keepalive=True,
        health_check_interval=30,
    )

    logger.info(
        f"Created Redis connection pool (max_connections={settings.REDIS_MAX_CONNECTIONS})"
    )

    return pool


# Global Redis connection pool
redis_pool = create_redis_pool()


async def get_redis() -> AsyncGenerator[Redis, None]:
    """
    FastAPI dependency for Redis client

    Usage:
        @app.get("/cached")
        async def get_cached(redis: Redis = Depends(get_redis)):
            value = await redis.get("key")
            return {"value": value}

    Yields:
        Redis: Redis client instance
    """
    redis_client = Redis(connection_pool=redis_pool)
    try:
        yield redis_client
    finally:
        await redis_client.close()


async def get_redis_client() -> Redis:
    """
    Get a Redis client directly (not as a dependency)

    Usage:
        redis = await get_redis_client()
        try:
            value = await redis.get("key")
        finally:
            await redis.close()

    Returns:
        Redis: Redis client instance
    """
    return Redis(connection_pool=redis_pool)


# ============================================================================
# Health Checks
# ============================================================================

async def check_db_connection() -> tuple[bool, Optional[str]]:
    """
    Check if database connection is healthy

    Returns:
        tuple: (is_healthy, error_message)

    Example:
        healthy, error = await check_db_connection()
        if not healthy:
            logger.error(f"Database unhealthy: {error}")
    """
    try:
        async with AsyncSessionLocal() as session:
            # Execute simple query
            result = await session.execute(text("SELECT 1"))
            result.scalar()

            # Check connection pool stats
            pool = engine.pool
            logger.debug(
                f"Database pool stats - "
                f"size: {pool.size()}, "
                f"checked_in: {pool.checkedin()}, "
                f"checked_out: {pool.checkedout()}, "
                f"overflow: {pool.overflow()}"
            )

        return True, None
    except Exception as e:
        error_msg = f"Database health check failed: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


async def check_redis_connection() -> tuple[bool, Optional[str]]:
    """
    Check if Redis connection is healthy

    Returns:
        tuple: (is_healthy, error_message)

    Example:
        healthy, error = await check_redis_connection()
        if not healthy:
            logger.error(f"Redis unhealthy: {error}")
    """
    redis_client = None
    try:
        redis_client = Redis(connection_pool=redis_pool)

        # Ping Redis
        response = await redis_client.ping()
        if not response:
            raise Exception("Redis ping returned False")

        # Check info
        info = await redis_client.info()
        logger.debug(
            f"Redis stats - "
            f"connected_clients: {info.get('connected_clients')}, "
            f"used_memory_human: {info.get('used_memory_human')}"
        )

        return True, None
    except Exception as e:
        error_msg = f"Redis health check failed: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    finally:
        if redis_client:
            await redis_client.close()


async def check_all_connections() -> dict[str, tuple[bool, Optional[str]]]:
    """
    Check all connection health (database and Redis)

    Returns:
        dict: Dictionary with health status for each service

    Example:
        health = await check_all_connections()
        if not all(status[0] for status in health.values()):
            logger.error("Some services are unhealthy")
    """
    db_health = await check_db_connection()
    redis_health = await check_redis_connection()

    return {
        "database": db_health,
        "redis": redis_health,
    }


# ============================================================================
# Lifecycle Management
# ============================================================================

async def init_db():
    """
    Initialize database connection

    Should be called on application startup.
    """
    logger.info("Initializing database connection...")

    # Test connection
    healthy, error = await check_db_connection()
    if not healthy:
        logger.error(f"Failed to connect to database: {error}")
        raise Exception(f"Database connection failed: {error}")

    logger.info("Database connection initialized successfully")


async def close_db():
    """
    Close database connection and cleanup

    Should be called on application shutdown.
    """
    logger.info("Closing database connection...")

    await engine.dispose()

    logger.info("Database connection closed")


async def init_redis():
    """
    Initialize Redis connection

    Should be called on application startup.
    """
    logger.info("Initializing Redis connection...")

    # Test connection
    healthy, error = await check_redis_connection()
    if not healthy:
        logger.error(f"Failed to connect to Redis: {error}")
        raise Exception(f"Redis connection failed: {error}")

    logger.info("Redis connection initialized successfully")


async def close_redis():
    """
    Close Redis connection pool

    Should be called on application shutdown.
    """
    logger.info("Closing Redis connection...")

    await redis_pool.disconnect()

    logger.info("Redis connection closed")


async def init_connections():
    """
    Initialize all connections (database and Redis)

    Should be called on application startup.
    """
    await init_db()
    await init_redis()


async def close_connections():
    """
    Close all connections (database and Redis)

    Should be called on application shutdown.
    """
    await close_db()
    await close_redis()


# ============================================================================
# Utility Functions
# ============================================================================

async def get_db_info() -> dict:
    """
    Get database connection information

    Returns:
        dict: Database connection stats
    """
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "url": str(settings.DATABASE_URL).split("@")[-1],  # Hide credentials
    }


async def get_redis_info() -> dict:
    """
    Get Redis connection information

    Returns:
        dict: Redis connection stats
    """
    redis_client = None
    try:
        redis_client = Redis(connection_pool=redis_pool)
        info = await redis_client.info()

        return {
            "version": info.get("redis_version"),
            "connected_clients": info.get("connected_clients"),
            "used_memory_human": info.get("used_memory_human"),
            "uptime_in_days": info.get("uptime_in_days"),
        }
    finally:
        if redis_client:
            await redis_client.close()

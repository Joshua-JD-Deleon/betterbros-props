# BetterBros Props - Database Layer Documentation

Complete guide to the SQLAlchemy database layer with PostgreSQL and Redis.

## Table of Contents

- [Overview](#overview)
- [Database Schema](#database-schema)
- [Models](#models)
- [Session Management](#session-management)
- [Migrations](#migrations)
- [Usage Examples](#usage-examples)
- [Best Practices](#best-practices)

## Overview

The BetterBros Props database layer uses:

- **PostgreSQL** for relational data storage
- **SQLAlchemy 2.0** with async support
- **Alembic** for database migrations
- **Redis** for caching and session storage
- **UUID** primary keys for scalability
- **JSONB** for flexible nested data

### Architecture

```
src/db/
├── models.py      # SQLAlchemy models
├── session.py     # Session factory and connection management
└── __init__.py    # Public API exports

alembic/
├── versions/
│   └── 001_initial_schema.py  # Initial migration
└── env.py         # Alembic configuration
```

## Database Schema

### Tables

1. **users** - User accounts and subscriptions
2. **snapshots** - Data snapshots for versioning
3. **experiments** - ML experiments and backtests
4. **saved_slips** - User-saved parlay slips
5. **prop_markets** - Prop betting markets

### Entity Relationship Diagram

```
┌─────────────┐
│    users    │
└──────┬──────┘
       │ 1
       │
       │ N
┌──────┴──────────┐
│   experiments   │
│   saved_slips   │
└──────┬──────────┘
       │ N
       │
       │ 1
┌──────┴──────────┐
│   snapshots     │
└──────┬──────────┘
       │ 1
       │
       │ N
┌──────┴──────────┐
│  prop_markets   │
└─────────────────┘
```

## Models

### User

Stores user account information integrated with Clerk or Supabase.

```python
from src.db import User

user = User(
    clerk_user_id="user_abc123",
    email="user@example.com",
    subscription_tier="pro",
    subscription_status="active"
)
```

**Fields:**
- `id` (UUID) - Primary key
- `clerk_user_id` (String) - Clerk user ID (if using Clerk)
- `supabase_user_id` (UUID) - Supabase user ID (if using Supabase)
- `email` (String) - User email (unique)
- `username` (String) - Username (unique, optional)
- `subscription_tier` (String) - free, pro, enterprise
- `subscription_status` (String) - active, cancelled, past_due, trialing
- `is_active` (Boolean) - Account active status
- `created_at` (DateTime) - Account creation timestamp
- `updated_at` (DateTime) - Last update timestamp

**Indexes:**
- `email`, `clerk_user_id`, `supabase_user_id`, `(subscription_tier, subscription_status)`

### Snapshot

Captures state of props/predictions at a point in time.

```python
from src.db import Snapshot

snapshot = Snapshot(
    snapshot_id="nfl-week-5-2024",
    week=5,
    league="NFL",
    config={"risk_mode": "balanced"},
    model_version="v1.2.0"
)
```

**Fields:**
- `id` (UUID) - Primary key
- `snapshot_id` (String) - Unique identifier (unique)
- `week` (Integer) - Week number
- `league` (String) - NFL, NBA, MLB, NHL
- `config` (JSONB) - Configuration parameters
- `features_path` (String) - Path to feature data
- `model_version` (String) - Model version used
- `is_locked` (Boolean) - Lock to prevent modifications
- `created_at` (DateTime) - Creation timestamp

**Indexes:**
- `snapshot_id`, `(week, league)`, `created_at`, `game_date`

### Experiment

Tracks ML experiments and backtesting runs.

```python
from src.db import Experiment

experiment = Experiment(
    user_id=user.id,
    snapshot_id=snapshot.id,
    week=5,
    league="NFL",
    risk_mode="aggressive",
    bankroll=1000.0,
    metrics={
        "roi": 0.15,
        "win_rate": 0.62,
        "sharpe": 1.8
    }
)
```

**Fields:**
- `id` (UUID) - Primary key
- `user_id` (UUID) - Foreign key to users
- `snapshot_id` (UUID) - Foreign key to snapshots
- `timestamp` (DateTime) - Experiment run time
- `week` (Integer) - Week number
- `league` (String) - League
- `risk_mode` (String) - conservative, balanced, aggressive
- `bankroll` (Float) - Simulated bankroll
- `metrics` (JSONB) - Experiment results
- `status` (String) - draft, running, completed, failed

**Indexes:**
- `user_id`, `snapshot_id`, `(week, league)`, `timestamp`, `status`

### SavedSlip

User-saved parlay slips with predictions.

```python
from src.db import SavedSlip

slip = SavedSlip(
    user_id=user.id,
    snapshot_id=snapshot.id,
    legs=[
        {"player": "Patrick Mahomes", "stat": "passing_yards", "line": 275.5},
        {"player": "Travis Kelce", "stat": "receptions", "line": 5.5}
    ],
    ev=1.45,
    stake=50.0,
    platform="prizepicks"
)
```

**Fields:**
- `id` (UUID) - Primary key
- `user_id` (UUID) - Foreign key to users
- `snapshot_id` (UUID) - Foreign key to snapshots
- `legs` (JSONB) - Array of prop legs
- `ev` (Float) - Expected value
- `variance` (Float) - Variance
- `var_95` (Float) - 95% Value at Risk
- `stake` (Float) - Recommended stake
- `correlations` (JSONB) - Correlation matrix
- `is_placed` (Boolean) - Whether slip was placed

**Indexes:**
- `user_id`, `snapshot_id`, `created_at`, `ev`, `is_placed`

### PropMarket

Individual prop markets from platforms.

```python
from src.db import PropMarket

prop = PropMarket(
    snapshot_id=snapshot.id,
    week=5,
    league="NFL",
    player_name="Patrick Mahomes",
    market_type="passing_yards",
    line=275.5,
    odds=-110,
    platform="prizepicks"
)
```

**Fields:**
- `id` (UUID) - Primary key
- `snapshot_id` (UUID) - Foreign key to snapshots
- `week` (Integer) - Week number
- `league` (String) - League
- `player_name` (String) - Player name
- `team` (String) - Team abbreviation
- `market_type` (String) - Stat type
- `line` (Float) - Line value
- `odds` (Float) - Decimal odds
- `platform` (String) - Platform name
- `is_active` (Boolean) - Active status

**Indexes:**
- `(week, league)`, `player_name`, `market_type`, `platform`, `is_active`
- Composite: `(week, league, player_name)`, `(platform, is_active)`

## Session Management

### Database Sessions

Use the `get_db()` dependency for FastAPI routes:

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.db import get_db, User

@app.get("/users/{user_id}")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    return user
```

For non-FastAPI contexts:

```python
from src.db import get_db_session

async with get_db_session() as session:
    result = await session.execute(select(User))
    users = result.scalars().all()
```

### Redis Sessions

Use the `get_redis()` dependency:

```python
from fastapi import Depends
from redis.asyncio import Redis
from src.db import get_redis

@app.get("/cached/{key}")
async def get_cached(
    key: str,
    redis: Redis = Depends(get_redis)
):
    value = await redis.get(key)
    return {"value": value}
```

For non-FastAPI contexts:

```python
from src.db import get_redis_client

redis = await get_redis_client()
try:
    value = await redis.get("key")
finally:
    await redis.close()
```

### Connection Lifecycle

Initialize connections on startup:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.db import init_connections, close_connections

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_connections()
    yield
    # Shutdown
    await close_connections()

app = FastAPI(lifespan=lifespan)
```

## Migrations

### Using Alembic Directly

```bash
# Create a new migration
alembic revision -m "add new field"

# Upgrade to latest
alembic upgrade head

# Downgrade one version
alembic downgrade -1

# Show current version
alembic current

# Show history
alembic history
```

### Using the Migration Script

```bash
# Initialize database (run all migrations)
python scripts/db_migrate.py init

# Upgrade to latest
python scripts/db_migrate.py upgrade

# Downgrade one migration
python scripts/db_migrate.py downgrade

# Reset database (WARNING: deletes all data)
python scripts/db_migrate.py reset

# Show migration status
python scripts/db_migrate.py status

# Show migration history
python scripts/db_migrate.py history
```

### Creating New Migrations

1. Modify models in `src/db/models.py`
2. Generate migration:

```bash
alembic revision --autogenerate -m "describe changes"
```

3. Review generated migration in `alembic/versions/`
4. Apply migration:

```bash
alembic upgrade head
```

## Usage Examples

### Creating Records

```python
from sqlalchemy import select
from src.db import get_db, User, Experiment

async def create_experiment(db: AsyncSession):
    # Create user
    user = User(
        clerk_user_id="user_123",
        email="user@example.com",
        subscription_tier="pro"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create experiment
    experiment = Experiment(
        user_id=user.id,
        week=5,
        league="NFL",
        risk_mode="balanced",
        bankroll=1000.0,
        timestamp=datetime.utcnow(),
        metrics={"roi": 0.15}
    )
    db.add(experiment)
    await db.commit()
    await db.refresh(experiment)

    return experiment
```

### Querying Records

```python
from sqlalchemy import select, and_, or_
from src.db import PropMarket

async def get_active_props(db: AsyncSession, week: int, league: str):
    # Simple query
    result = await db.execute(
        select(PropMarket)
        .where(
            and_(
                PropMarket.week == week,
                PropMarket.league == league,
                PropMarket.is_active == True
            )
        )
        .order_by(PropMarket.player_name)
    )
    props = result.scalars().all()
    return props
```

### Updating Records

```python
async def update_experiment_metrics(
    db: AsyncSession,
    experiment_id: UUID,
    metrics: dict
):
    result = await db.execute(
        select(Experiment).where(Experiment.id == experiment_id)
    )
    experiment = result.scalar_one()

    experiment.metrics = metrics
    experiment.status = "completed"

    await db.commit()
    await db.refresh(experiment)
    return experiment
```

### Deleting Records

```python
async def delete_old_props(db: AsyncSession, cutoff_date: datetime):
    result = await db.execute(
        select(PropMarket).where(PropMarket.created_at < cutoff_date)
    )
    props = result.scalars().all()

    for prop in props:
        await db.delete(prop)

    await db.commit()
    return len(props)
```

### Joining Tables

```python
async def get_user_experiments(db: AsyncSession, user_id: UUID):
    result = await db.execute(
        select(Experiment, Snapshot)
        .join(Snapshot, Experiment.snapshot_id == Snapshot.id)
        .where(Experiment.user_id == user_id)
        .order_by(Experiment.created_at.desc())
    )
    return result.all()
```

### Aggregations

```python
from sqlalchemy import func

async def get_user_stats(db: AsyncSession, user_id: UUID):
    result = await db.execute(
        select(
            func.count(Experiment.id).label("total_experiments"),
            func.avg(Experiment.metrics["roi"].as_float()).label("avg_roi"),
            func.sum(Experiment.num_slips).label("total_slips")
        )
        .where(Experiment.user_id == user_id)
    )
    stats = result.first()
    return stats
```

### Using Redis Cache

```python
import json
from src.db import get_redis_client

async def get_or_cache_props(week: int, league: str):
    redis = await get_redis_client()
    try:
        # Check cache
        cache_key = f"props:{league}:{week}"
        cached = await redis.get(cache_key)

        if cached:
            return json.loads(cached)

        # Fetch from database
        async with get_db_session() as db:
            result = await db.execute(
                select(PropMarket)
                .where(
                    and_(
                        PropMarket.week == week,
                        PropMarket.league == league
                    )
                )
            )
            props = result.scalars().all()

        # Cache for 5 minutes
        await redis.setex(
            cache_key,
            300,
            json.dumps([prop.dict() for prop in props])
        )

        return props
    finally:
        await redis.close()
```

## Best Practices

### 1. Always Use Async/Await

```python
# Good
async def get_user(db: AsyncSession, user_id: UUID):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

# Bad - Don't use sync methods
def get_user_sync(db: Session, user_id: UUID):
    return db.query(User).filter(User.id == user_id).first()
```

### 2. Use Context Managers

```python
# Good
async with get_db_session() as session:
    # Use session
    pass

# Bad - Manual cleanup
session = get_db_session()
try:
    # Use session
    pass
finally:
    await session.close()
```

### 3. Use Proper Error Handling

```python
from sqlalchemy.exc import IntegrityError, NoResultFound

async def create_user_safe(db: AsyncSession, email: str):
    try:
        user = User(email=email, clerk_user_id="user_123")
        db.add(user)
        await db.commit()
        return user
    except IntegrityError:
        await db.rollback()
        # Email already exists
        raise ValueError("Email already registered")
    except Exception as e:
        await db.rollback()
        raise
```

### 4. Use Indexes for Queries

Always query on indexed fields for performance:

```python
# Good - queries on indexed fields
await db.execute(
    select(PropMarket)
    .where(
        and_(
            PropMarket.week == week,      # indexed
            PropMarket.league == league,  # indexed
            PropMarket.is_active == True  # indexed
        )
    )
)

# Avoid - queries on non-indexed fields
await db.execute(
    select(PropMarket)
    .where(PropMarket.notes.like("%pattern%"))  # not indexed
)
```

### 5. Batch Operations

```python
# Good - bulk insert
props = [
    PropMarket(week=5, league="NFL", player_name=f"Player {i}", ...)
    for i in range(100)
]
db.add_all(props)
await db.commit()

# Bad - individual inserts in loop
for i in range(100):
    prop = PropMarket(week=5, league="NFL", player_name=f"Player {i}", ...)
    db.add(prop)
    await db.commit()  # Don't commit in loop!
```

### 6. Use JSONB Efficiently

```python
# Query JSONB fields
result = await db.execute(
    select(Experiment)
    .where(Experiment.metrics["roi"].as_float() > 0.1)
)

# Update JSONB fields
experiment.metrics = {**experiment.metrics, "new_metric": 0.5}
```

### 7. Connection Pool Management

Monitor connection pool health:

```python
from src.db import get_db_info

info = await get_db_info()
print(f"Pool size: {info['pool_size']}")
print(f"Checked out: {info['checked_out']}")
print(f"Overflow: {info['overflow']}")
```

### 8. Use Transactions

```python
async def transfer_credits(
    db: AsyncSession,
    from_user_id: UUID,
    to_user_id: UUID,
    amount: float
):
    async with db.begin():
        # Both operations succeed or both fail
        from_user = await db.get(User, from_user_id)
        to_user = await db.get(User, to_user_id)

        from_user.credits -= amount
        to_user.credits += amount

        # Automatically commits on success, rolls back on exception
```

### 9. Health Checks

```python
from src.db import check_all_connections

@app.get("/health")
async def health_check():
    health = await check_all_connections()

    all_healthy = all(status[0] for status in health.values())

    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "checks": {
            name: {"healthy": status[0], "error": status[1]}
            for name, status in health.items()
        }
    }
```

### 10. Testing

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def test_db():
    """Create test database session"""
    engine = create_async_engine("postgresql+asyncpg://localhost/test_db")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


async def test_create_user(test_db):
    user = User(clerk_user_id="test_123", email="test@example.com")
    test_db.add(user)
    await test_db.commit()

    result = await test_db.execute(select(User).where(User.email == "test@example.com"))
    found_user = result.scalar_one()

    assert found_user.email == "test@example.com"
```

## Performance Tips

1. **Use connection pooling** - Already configured in session.py
2. **Index frequently queried fields** - Already indexed in models
3. **Use JSONB for flexible data** - Already implemented
4. **Cache expensive queries in Redis** - Use get_redis()
5. **Batch operations** - Use add_all() and bulk methods
6. **Use select with specific columns** - Only fetch what you need
7. **Monitor slow queries** - Enable SQL logging in development
8. **Use database-side aggregations** - Use func.count(), func.sum(), etc.

## Troubleshooting

### Connection Issues

```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Check Redis is running
redis-cli ping
```

### Migration Issues

```bash
# Reset to clean state
python scripts/db_migrate.py reset

# Check current version
alembic current

# Show migration history
alembic history --verbose
```

### Performance Issues

```python
# Enable SQL logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

## Additional Resources

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)

# Database Layer - Complete Implementation

The complete database layer for BetterBros Props has been successfully implemented with production-ready features.

## Files Created

### Core Database Files
```
src/db/
├── __init__.py           # Public API exports
├── models.py             # SQLAlchemy models (User, Snapshot, Experiment, SavedSlip, PropMarket)
└── session.py            # Session factory, connection management, health checks
```

### Migration Files
```
alembic/
├── env.py                            # Updated with model imports
└── versions/
    └── 001_initial_schema.py         # Initial database schema
```

### Scripts
```
scripts/
└── db_migrate.py         # Database management script (init, upgrade, downgrade, reset)
```

### Tests
```
tests/
└── test_db.py           # Comprehensive test suite for all models
```

### Documentation
```
DATABASE.md                     # Complete documentation (schema, usage, examples)
DB_QUICK_REFERENCE.md          # Quick reference guide
DATABASE_IMPLEMENTATION.md      # Implementation summary
README_DATABASE.md             # This file
```

## Quick Start

### 1. Install Dependencies

Dependencies are already listed in `requirements.txt`:
```bash
pip install -r requirements.txt
```

Required packages:
- sqlalchemy[asyncio]==2.0.25
- asyncpg==0.29.0
- alembic==1.13.1
- redis[hiredis]==5.0.1

### 2. Configure Environment

Set these variables in `.env` (see `.env.example`):
```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/betterbros_props
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50
REDIS_CACHE_TTL=300
```

### 3. Initialize Database

```bash
# Using the migration script (recommended)
python scripts/db_migrate.py init

# Or using Alembic directly
alembic upgrade head
```

### 4. Verify Installation

```bash
# Check migration status
python scripts/db_migrate.py status

# Run tests (requires test dependencies)
pytest tests/test_db.py -v
```

## Models

### User
Stores user accounts with Clerk/Supabase authentication support.

**Key Fields:**
- `clerk_user_id` or `supabase_user_id` (one required)
- `email` (unique, indexed)
- `subscription_tier`: "free", "pro", "enterprise"
- `subscription_status`: "active", "cancelled", "past_due", "trialing"
- `user_metadata` (JSONB for flexible data)

### Snapshot
Captures state of props/predictions at a point in time for reproducibility.

**Key Fields:**
- `snapshot_id` (unique identifier like "nfl-week-5-2024")
- `week`, `league` (indexed for queries)
- `config` (JSONB for configuration)
- `model_version` (tracks which model was used)
- `features_path` (path to feature data)

### Experiment
Tracks ML experiments and backtesting runs.

**Key Fields:**
- `user_id` (foreign key to users)
- `snapshot_id` (foreign key to snapshots, optional)
- `week`, `league` (indexed)
- `risk_mode`: "conservative", "balanced", "aggressive"
- `bankroll`, `num_props`, `num_slips`
- `metrics` (JSONB for flexible metrics storage)
- `status`: "draft", "running", "completed", "failed"

### SavedSlip
User-saved parlay slips with edge calculations.

**Key Fields:**
- `user_id` (foreign key to users)
- `snapshot_id` (foreign key to snapshots, optional)
- `legs` (JSONB array of prop legs)
- `ev` (expected value, indexed)
- `variance`, `var_95` (risk metrics)
- `stake` (recommended stake amount)
- `correlations` (JSONB correlation matrix)
- `is_placed`, `platform` (tracking)

### PropMarket
Individual prop betting markets from platforms.

**Key Fields:**
- `week`, `league` (indexed)
- `player_name`, `player_id` (indexed)
- `market_type` (stat type: passing_yards, points, etc.)
- `line`, `odds`
- `platform`: "prizepicks", "underdog", etc.
- `is_active` (boolean, indexed)
- `extra_metadata` (JSONB for platform-specific data)

## Usage Examples

### Import Models

```python
from src.db import (
    User, Snapshot, Experiment, SavedSlip, PropMarket,
    get_db, get_redis,  # FastAPI dependencies
    init_connections, close_connections  # Lifecycle
)
```

### FastAPI Integration

```python
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from src.db import init_connections, close_connections, get_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_connections()
    yield
    # Shutdown
    await close_connections()

app = FastAPI(lifespan=lifespan)

@app.get("/users/{user_id}")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()
```

### Create Records

```python
from src.db import User

async def create_user(db: AsyncSession):
    user = User(
        clerk_user_id="user_123",
        email="user@example.com",
        subscription_tier="pro"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
```

### Query Records

```python
from sqlalchemy import select, and_
from src.db import PropMarket

async def get_active_props(db: AsyncSession, week: int, league: str):
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
        .limit(50)
    )
    return result.scalars().all()
```

### Redis Caching

```python
from fastapi import Depends
from redis.asyncio import Redis
from src.db import get_redis
import json

@app.get("/cached/{key}")
async def get_cached(
    key: str,
    redis: Redis = Depends(get_redis)
):
    # Try cache first
    cached = await redis.get(key)
    if cached:
        return json.loads(cached)

    # Compute value
    value = expensive_operation()

    # Cache for 5 minutes
    await redis.setex(key, 300, json.dumps(value))
    return value
```

## Database Schema

```
users
├── id (UUID, PK)
├── clerk_user_id (String, unique, indexed)
├── supabase_user_id (UUID, unique, indexed)
├── email (String, unique, indexed)
├── subscription_tier, subscription_status (indexed together)
└── user_metadata (JSONB)

snapshots
├── id (UUID, PK)
├── snapshot_id (String, unique, indexed)
├── week, league (indexed together)
├── config (JSONB)
└── model_version (String)

experiments
├── id (UUID, PK)
├── user_id (UUID, FK→users.id, CASCADE, indexed)
├── snapshot_id (UUID, FK→snapshots.id, SET NULL, indexed)
├── week, league (indexed together)
├── metrics (JSONB)
└── status (String, indexed)

saved_slips
├── id (UUID, PK)
├── user_id (UUID, FK→users.id, CASCADE, indexed)
├── snapshot_id (UUID, FK→snapshots.id, SET NULL, indexed)
├── legs (JSONB)
├── ev (Float, indexed)
├── correlations (JSONB)
└── is_placed (Boolean, indexed)

prop_markets
├── id (UUID, PK)
├── snapshot_id (UUID, FK→snapshots.id, SET NULL, indexed)
├── week, league (indexed together)
├── player_name (String, indexed)
├── market_type (String, indexed)
├── platform (String, indexed)
├── is_active (Boolean, indexed)
├── extra_metadata (JSONB)
└── Composite: (week, league, player_name), (platform, is_active)
```

## Migration Commands

```bash
# Initialize database (first time)
python scripts/db_migrate.py init

# Upgrade to latest migration
python scripts/db_migrate.py upgrade
# or: alembic upgrade head

# Downgrade one migration
python scripts/db_migrate.py downgrade
# or: alembic downgrade -1

# Check current version
python scripts/db_migrate.py status
# or: alembic current

# View migration history
python scripts/db_migrate.py history
# or: alembic history

# Reset database (WARNING: deletes all data!)
python scripts/db_migrate.py reset

# Create new migration (after modifying models)
alembic revision --autogenerate -m "description"
```

## Features

### Production-Ready
- ✅ Async/await throughout
- ✅ Connection pooling configured
- ✅ Proper error handling and rollback
- ✅ Health check functions
- ✅ FastAPI dependency injection
- ✅ Graceful startup/shutdown

### Database Best Practices
- ✅ UUID primary keys for scalability
- ✅ Proper indexes on frequently queried fields
- ✅ Composite indexes for multi-field queries
- ✅ Foreign keys with cascade rules
- ✅ Check constraints for data integrity
- ✅ JSONB for flexible nested data
- ✅ Timestamps with timezone

### Developer Experience
- ✅ Comprehensive documentation
- ✅ Full test coverage
- ✅ Quick reference guide
- ✅ Migration management script
- ✅ Type hints throughout
- ✅ Clear code comments

## Testing

Run the test suite:

```bash
# All database tests
pytest tests/test_db.py -v

# With coverage
pytest tests/test_db.py --cov=src/db --cov-report=html

# Specific test
pytest tests/test_db.py::test_create_user_clerk -v
```

Tests cover:
- Model creation and validation
- Unique constraints
- Foreign key relationships
- Cascade deletes
- JSONB fields
- Complex queries (joins, aggregations)

## Documentation

- **[DATABASE.md](./DATABASE.md)** - Complete documentation with examples
- **[DB_QUICK_REFERENCE.md](./DB_QUICK_REFERENCE.md)** - Quick reference for common patterns
- **[DATABASE_IMPLEMENTATION.md](./DATABASE_IMPLEMENTATION.md)** - Implementation details and architecture

## Key Changes from Original Plan

1. **Renamed `metadata` fields** to avoid SQLAlchemy reserved names:
   - User: `user_metadata` (JSONB)
   - PropMarket: `extra_metadata` (JSONB)

2. **Added additional fields** for better functionality:
   - User: `username`, `full_name`, `is_verified`, `last_login_at`
   - All models: Better timestamp tracking

3. **Improved indexes** with composite indexes for common query patterns

## Next Steps

### Immediate Integration

1. **Update FastAPI app** (`main.py`):
   ```python
   from contextlib import asynccontextmanager
   from src.db import init_connections, close_connections

   @asynccontextmanager
   async def lifespan(app: FastAPI):
       await init_connections()
       yield
       await close_connections()

   app = FastAPI(lifespan=lifespan)
   ```

2. **Add health check endpoint**:
   ```python
   from src.db import check_all_connections

   @app.get("/health")
   async def health():
       health = await check_all_connections()
       return {
           "status": "healthy" if all(h[0] for h in health.values()) else "unhealthy",
           "database": health["database"][0],
           "redis": health["redis"][0]
       }
   ```

3. **Use in routers** - Replace placeholder DB logic with actual models

### Future Enhancements

- Add soft deletes if needed
- Implement audit logging
- Add read replicas for scaling
- Add database monitoring
- Implement connection pool monitoring
- Add more indexes based on actual query patterns

## Troubleshooting

### Import Errors
Make sure you're in the correct directory and dependencies are installed:
```bash
cd apps/api
pip install -r requirements.txt
python -c "from src.db import User; print('✓ Import successful')"
```

### Connection Errors
Check PostgreSQL and Redis are running:
```bash
pg_isready -h localhost -p 5432
redis-cli ping
```

### Migration Errors
Check current status and history:
```bash
python scripts/db_migrate.py status
python scripts/db_migrate.py history
```

## Support

For issues or questions:
1. Check the comprehensive [DATABASE.md](./DATABASE.md)
2. Review [DB_QUICK_REFERENCE.md](./DB_QUICK_REFERENCE.md) for common patterns
3. Look at test examples in [tests/test_db.py](./tests/test_db.py)
4. Consult [SQLAlchemy 2.0 docs](https://docs.sqlalchemy.org/en/20/)

## Summary

The database layer is complete and production-ready with:

- ✅ 5 SQLAlchemy models with proper relationships
- ✅ Async session management with connection pooling
- ✅ Redis integration for caching
- ✅ Alembic migrations with initial schema
- ✅ Management script for easy migrations
- ✅ Comprehensive test suite
- ✅ Full documentation and examples
- ✅ Health check utilities
- ✅ Best practices throughout

All files have been validated and are ready for use. The implementation follows industry best practices and is optimized for the BetterBros Props use case.

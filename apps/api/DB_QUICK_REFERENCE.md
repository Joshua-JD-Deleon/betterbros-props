# Database Layer Quick Reference

Fast reference guide for common database operations.

## Quick Start

```bash
# Initialize database (run migrations)
python scripts/db_migrate.py init

# Check status
python scripts/db_migrate.py status
```

## Import Models

```python
from src.db import User, Experiment, Snapshot, SavedSlip, PropMarket
from src.db import get_db, get_redis  # FastAPI dependencies
```

## Common Patterns

### Create Record

```python
from src.db import User, get_db

@app.post("/users")
async def create_user(db: AsyncSession = Depends(get_db)):
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

# Single record
result = await db.execute(
    select(User).where(User.email == "user@example.com")
)
user = result.scalar_one_or_none()

# Multiple records
result = await db.execute(
    select(PropMarket)
    .where(
        and_(
            PropMarket.week == 5,
            PropMarket.league == "NFL",
            PropMarket.is_active == True
        )
    )
    .order_by(PropMarket.player_name)
    .limit(50)
)
props = result.scalars().all()
```

### Update Record

```python
result = await db.execute(
    select(User).where(User.id == user_id)
)
user = result.scalar_one()

user.subscription_tier = "enterprise"
await db.commit()
await db.refresh(user)
```

### Delete Record

```python
result = await db.execute(
    select(PropMarket).where(PropMarket.id == prop_id)
)
prop = result.scalar_one()

await db.delete(prop)
await db.commit()
```

### Join Tables

```python
result = await db.execute(
    select(Experiment, Snapshot)
    .join(Snapshot, Experiment.snapshot_id == Snapshot.id)
    .where(Experiment.user_id == user_id)
)
for experiment, snapshot in result.all():
    print(f"{experiment.name} - {snapshot.snapshot_id}")
```

### Aggregations

```python
from sqlalchemy import func

result = await db.execute(
    select(
        func.count(Experiment.id),
        func.avg(Experiment.metrics["roi"].as_float())
    )
    .where(Experiment.user_id == user_id)
)
count, avg_roi = result.first()
```

### JSONB Queries

```python
# Query JSONB field
result = await db.execute(
    select(Experiment)
    .where(Experiment.metrics["roi"].as_float() > 0.1)
)

# Update JSONB field
experiment.metrics = {**experiment.metrics, "new_key": "value"}
await db.commit()
```

## Redis Cache

```python
from src.db import get_redis

@app.get("/cached/{key}")
async def get_cached(key: str, redis: Redis = Depends(get_redis)):
    # Get from cache
    value = await redis.get(key)
    if value:
        return {"value": value}

    # Compute value
    value = expensive_operation()

    # Cache for 5 minutes
    await redis.setex(key, 300, value)
    return {"value": value}
```

## Health Checks

```python
from src.db import check_all_connections

@app.get("/health")
async def health():
    health = await check_all_connections()
    return {
        "database": health["database"][0],
        "redis": health["redis"][0]
    }
```

## Migrations

```bash
# Create migration
alembic revision --autogenerate -m "add new field"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Reset database (WARNING: deletes all data)
python scripts/db_migrate.py reset
```

## Connection Lifecycle

```python
from src.db import init_connections, close_connections

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_connections()
    yield
    await close_connections()

app = FastAPI(lifespan=lifespan)
```

## Error Handling

```python
from sqlalchemy.exc import IntegrityError, NoResultFound

try:
    db.add(user)
    await db.commit()
except IntegrityError:
    await db.rollback()
    raise HTTPException(400, "Email already exists")
except Exception as e:
    await db.rollback()
    raise HTTPException(500, f"Database error: {e}")
```

## Batch Operations

```python
# Bulk insert
props = [
    PropMarket(week=5, league="NFL", player_name=f"Player {i}", ...)
    for i in range(100)
]
db.add_all(props)
await db.commit()
```

## Transactions

```python
async with db.begin():
    # Multiple operations in transaction
    user.credits -= 100
    experiment = Experiment(user_id=user.id, ...)
    db.add(experiment)
    # Automatically commits or rolls back
```

## Model Quick Reference

### User
- `clerk_user_id` or `supabase_user_id` (required, one of)
- `email` (required, unique)
- `subscription_tier`: "free", "pro", "enterprise"
- Relationships: `experiments`, `saved_slips`

### Snapshot
- `snapshot_id` (required, unique)
- `week`, `league` (required)
- `config` (JSONB)
- `model_version`
- Relationships: `experiments`, `saved_slips`, `prop_markets`

### Experiment
- `user_id`, `week`, `league` (required)
- `risk_mode`: "conservative", "balanced", "aggressive"
- `bankroll`, `num_props`, `num_slips`
- `metrics` (JSONB)
- Relationships: `user`, `snapshot`

### SavedSlip
- `user_id` (required)
- `legs` (JSONB array)
- `ev`, `variance`, `stake`
- `correlations` (JSONB)
- `is_placed`, `platform`
- Relationships: `user`, `snapshot`

### PropMarket
- `week`, `league`, `player_name`, `market_type`, `line`, `platform` (required)
- `team`, `opponent`, `odds`
- `is_active`
- `metadata` (JSONB)
- Relationships: `snapshot`

## Indexed Fields (Use for WHERE clauses)

- **User**: email, clerk_user_id, supabase_user_id, (subscription_tier, subscription_status)
- **Snapshot**: snapshot_id, (week, league), created_at, game_date
- **Experiment**: user_id, snapshot_id, (week, league), timestamp, status
- **SavedSlip**: user_id, snapshot_id, created_at, ev, is_placed
- **PropMarket**: (week, league), player_name, market_type, platform, is_active, (week, league, player_name)

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/betterbros_props
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50
REDIS_CACHE_TTL=300
```

## Testing

```bash
# Run database tests
pytest tests/test_db.py -v

# Run with coverage
pytest tests/test_db.py --cov=src/db --cov-report=html
```

## Common Issues

**Import Error**: Make sure you're importing from `src.db`, not `src.db.models`

**Connection Error**: Check PostgreSQL/Redis are running
```bash
pg_isready -h localhost -p 5432
redis-cli ping
```

**Migration Error**: Check alembic version matches
```bash
alembic current
alembic history
```

**Pool Exhausted**: Increase pool size in settings or check for connection leaks

## Performance Tips

1. Always query indexed fields
2. Use `limit()` for large result sets
3. Use `add_all()` for bulk inserts
4. Cache expensive queries in Redis
5. Use database aggregations instead of Python loops
6. Monitor connection pool with `get_db_info()`

## Documentation

- Full docs: [DATABASE.md](./DATABASE.md)
- Models: [src/db/models.py](./src/db/models.py)
- Session: [src/db/session.py](./src/db/session.py)
- Tests: [tests/test_db.py](./tests/test_db.py)

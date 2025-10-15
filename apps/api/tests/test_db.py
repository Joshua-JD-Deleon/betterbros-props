"""
Tests for database models and session management

Run with: pytest tests/test_db.py -v
"""
import pytest
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import IntegrityError

from src.db.models import Base, User, Snapshot, Experiment, SavedSlip, PropMarket


# Test database URL (use in-memory SQLite for fast tests, or test PostgreSQL)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def session(engine):
    """Create test database session"""
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest.fixture
async def sample_user(session: AsyncSession):
    """Create a sample user for testing"""
    user = User(
        clerk_user_id="test_user_123",
        email="test@example.com",
        username="testuser",
        subscription_tier="pro",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def sample_snapshot(session: AsyncSession):
    """Create a sample snapshot for testing"""
    snapshot = Snapshot(
        snapshot_id="test-nfl-week-5",
        week=5,
        league="NFL",
        config={"risk_mode": "balanced"},
        model_version="v1.0.0",
    )
    session.add(snapshot)
    await session.commit()
    await session.refresh(snapshot)
    return snapshot


# ============================================================================
# User Model Tests
# ============================================================================

@pytest.mark.asyncio
async def test_create_user_clerk(session: AsyncSession):
    """Test creating user with Clerk authentication"""
    user = User(
        clerk_user_id="clerk_123",
        email="clerk@example.com",
        subscription_tier="free",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    assert user.id is not None
    assert user.clerk_user_id == "clerk_123"
    assert user.email == "clerk@example.com"
    assert user.subscription_tier == "free"
    assert user.is_active is True
    assert user.created_at is not None


@pytest.mark.asyncio
async def test_create_user_supabase(session: AsyncSession):
    """Test creating user with Supabase authentication"""
    supabase_id = uuid4()
    user = User(
        supabase_user_id=supabase_id,
        email="supabase@example.com",
        subscription_tier="pro",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    assert user.supabase_user_id == supabase_id
    assert user.email == "supabase@example.com"


@pytest.mark.asyncio
async def test_user_unique_email(session: AsyncSession):
    """Test that email must be unique"""
    user1 = User(
        clerk_user_id="user1",
        email="duplicate@example.com",
    )
    session.add(user1)
    await session.commit()

    # Try to create another user with same email
    user2 = User(
        clerk_user_id="user2",
        email="duplicate@example.com",
    )
    session.add(user2)

    with pytest.raises(IntegrityError):
        await session.commit()


@pytest.mark.asyncio
async def test_user_relationships(session: AsyncSession, sample_user: User):
    """Test user relationships with experiments and saved slips"""
    # Create experiment
    experiment = Experiment(
        user_id=sample_user.id,
        week=5,
        league="NFL",
        timestamp=datetime.utcnow(),
        risk_mode="balanced",
        bankroll=1000.0,
    )
    session.add(experiment)

    # Create saved slip
    slip = SavedSlip(
        user_id=sample_user.id,
        legs=[{"player": "Test", "stat": "points", "line": 20.5}],
        ev=1.5,
    )
    session.add(slip)

    await session.commit()
    await session.refresh(sample_user)

    # Check relationships
    assert len(sample_user.experiments) == 1
    assert len(sample_user.saved_slips) == 1


# ============================================================================
# Snapshot Model Tests
# ============================================================================

@pytest.mark.asyncio
async def test_create_snapshot(session: AsyncSession):
    """Test creating snapshot"""
    snapshot = Snapshot(
        snapshot_id="nfl-2024-week-10",
        week=10,
        league="NFL",
        season="2024",
        config={"risk_mode": "aggressive"},
        model_version="v2.0.0",
    )
    session.add(snapshot)
    await session.commit()
    await session.refresh(snapshot)

    assert snapshot.id is not None
    assert snapshot.snapshot_id == "nfl-2024-week-10"
    assert snapshot.week == 10
    assert snapshot.league == "NFL"
    assert snapshot.config["risk_mode"] == "aggressive"


@pytest.mark.asyncio
async def test_snapshot_unique_id(session: AsyncSession):
    """Test that snapshot_id must be unique"""
    snapshot1 = Snapshot(
        snapshot_id="duplicate-snapshot",
        week=5,
        league="NFL",
    )
    session.add(snapshot1)
    await session.commit()

    # Try to create another with same snapshot_id
    snapshot2 = Snapshot(
        snapshot_id="duplicate-snapshot",
        week=6,
        league="NFL",
    )
    session.add(snapshot2)

    with pytest.raises(IntegrityError):
        await session.commit()


# ============================================================================
# Experiment Model Tests
# ============================================================================

@pytest.mark.asyncio
async def test_create_experiment(
    session: AsyncSession,
    sample_user: User,
    sample_snapshot: Snapshot
):
    """Test creating experiment"""
    experiment = Experiment(
        user_id=sample_user.id,
        snapshot_id=sample_snapshot.id,
        timestamp=datetime.utcnow(),
        week=5,
        league="NFL",
        risk_mode="balanced",
        bankroll=1000.0,
        num_props=50,
        num_slips=10,
        metrics={"roi": 0.15, "win_rate": 0.62, "sharpe": 1.8},
    )
    session.add(experiment)
    await session.commit()
    await session.refresh(experiment)

    assert experiment.id is not None
    assert experiment.user_id == sample_user.id
    assert experiment.snapshot_id == sample_snapshot.id
    assert experiment.metrics["roi"] == 0.15
    assert experiment.status == "completed"


@pytest.mark.asyncio
async def test_experiment_cascade_delete(
    session: AsyncSession,
    sample_user: User
):
    """Test that experiments are deleted when user is deleted"""
    experiment = Experiment(
        user_id=sample_user.id,
        week=5,
        league="NFL",
        timestamp=datetime.utcnow(),
        risk_mode="balanced",
        bankroll=1000.0,
    )
    session.add(experiment)
    await session.commit()

    # Delete user
    await session.delete(sample_user)
    await session.commit()

    # Experiment should be deleted too
    result = await session.execute(select(Experiment))
    experiments = result.scalars().all()
    assert len(experiments) == 0


# ============================================================================
# SavedSlip Model Tests
# ============================================================================

@pytest.mark.asyncio
async def test_create_saved_slip(
    session: AsyncSession,
    sample_user: User,
    sample_snapshot: Snapshot
):
    """Test creating saved slip"""
    slip = SavedSlip(
        user_id=sample_user.id,
        snapshot_id=sample_snapshot.id,
        legs=[
            {"player": "Patrick Mahomes", "stat": "passing_yards", "line": 275.5},
            {"player": "Travis Kelce", "stat": "receptions", "line": 5.5}
        ],
        ev=1.45,
        variance=0.8,
        var_95=0.15,
        stake=50.0,
        correlations={"mahomes-kelce": 0.3},
        platform="prizepicks",
    )
    session.add(slip)
    await session.commit()
    await session.refresh(slip)

    assert slip.id is not None
    assert slip.user_id == sample_user.id
    assert len(slip.legs) == 2
    assert slip.ev == 1.45
    assert slip.platform == "prizepicks"


@pytest.mark.asyncio
async def test_saved_slip_query_by_ev(
    session: AsyncSession,
    sample_user: User
):
    """Test querying slips by EV"""
    # Create slips with different EVs
    for ev in [1.2, 1.5, 1.8]:
        slip = SavedSlip(
            user_id=sample_user.id,
            legs=[{"test": "data"}],
            ev=ev,
        )
        session.add(slip)
    await session.commit()

    # Query slips with EV > 1.4
    result = await session.execute(
        select(SavedSlip)
        .where(SavedSlip.ev > 1.4)
        .order_by(SavedSlip.ev)
    )
    slips = result.scalars().all()

    assert len(slips) == 2
    assert slips[0].ev == 1.5
    assert slips[1].ev == 1.8


# ============================================================================
# PropMarket Model Tests
# ============================================================================

@pytest.mark.asyncio
async def test_create_prop_market(
    session: AsyncSession,
    sample_snapshot: Snapshot
):
    """Test creating prop market"""
    prop = PropMarket(
        snapshot_id=sample_snapshot.id,
        week=5,
        league="NFL",
        player_id="player_123",
        player_name="Patrick Mahomes",
        team="KC",
        opponent="LV",
        market_type="passing_yards",
        line=275.5,
        odds=-110,
        platform="prizepicks",
    )
    session.add(prop)
    await session.commit()
    await session.refresh(prop)

    assert prop.id is not None
    assert prop.player_name == "Patrick Mahomes"
    assert prop.line == 275.5
    assert prop.is_active is True


@pytest.mark.asyncio
async def test_query_props_by_week_league(session: AsyncSession):
    """Test querying props by week and league"""
    # Create props for different weeks/leagues
    props_data = [
        {"week": 5, "league": "NFL", "player_name": "Player A"},
        {"week": 5, "league": "NFL", "player_name": "Player B"},
        {"week": 6, "league": "NFL", "player_name": "Player C"},
        {"week": 5, "league": "NBA", "player_name": "Player D"},
    ]

    for data in props_data:
        prop = PropMarket(
            week=data["week"],
            league=data["league"],
            player_name=data["player_name"],
            market_type="points",
            line=20.5,
            platform="test",
        )
        session.add(prop)
    await session.commit()

    # Query NFL Week 5 props
    result = await session.execute(
        select(PropMarket)
        .where(PropMarket.week == 5)
        .where(PropMarket.league == "NFL")
    )
    props = result.scalars().all()

    assert len(props) == 2


@pytest.mark.asyncio
async def test_prop_market_jsonb_metadata(session: AsyncSession):
    """Test storing and querying JSONB metadata"""
    prop = PropMarket(
        week=5,
        league="NFL",
        player_name="Test Player",
        market_type="points",
        line=20.5,
        platform="test",
        metadata={
            "source": "api",
            "confidence": 0.85,
            "last_updated": "2024-10-14"
        }
    )
    session.add(prop)
    await session.commit()
    await session.refresh(prop)

    assert prop.metadata["source"] == "api"
    assert prop.metadata["confidence"] == 0.85


# ============================================================================
# Complex Query Tests
# ============================================================================

@pytest.mark.asyncio
async def test_join_experiments_with_snapshots(
    session: AsyncSession,
    sample_user: User,
    sample_snapshot: Snapshot
):
    """Test joining experiments with snapshots"""
    experiment = Experiment(
        user_id=sample_user.id,
        snapshot_id=sample_snapshot.id,
        week=5,
        league="NFL",
        timestamp=datetime.utcnow(),
        risk_mode="balanced",
        bankroll=1000.0,
    )
    session.add(experiment)
    await session.commit()

    # Join query
    result = await session.execute(
        select(Experiment, Snapshot)
        .join(Snapshot, Experiment.snapshot_id == Snapshot.id)
        .where(Experiment.user_id == sample_user.id)
    )
    rows = result.all()

    assert len(rows) == 1
    exp, snap = rows[0]
    assert exp.snapshot_id == snap.id


@pytest.mark.asyncio
async def test_aggregate_user_experiments(
    session: AsyncSession,
    sample_user: User
):
    """Test aggregating experiment metrics"""
    from sqlalchemy import func

    # Create multiple experiments
    for i in range(3):
        experiment = Experiment(
            user_id=sample_user.id,
            week=5 + i,
            league="NFL",
            timestamp=datetime.utcnow(),
            risk_mode="balanced",
            bankroll=1000.0,
            num_slips=10 * (i + 1),
        )
        session.add(experiment)
    await session.commit()

    # Aggregate query
    result = await session.execute(
        select(
            func.count(Experiment.id).label("total"),
            func.sum(Experiment.num_slips).label("total_slips"),
        )
        .where(Experiment.user_id == sample_user.id)
    )
    stats = result.first()

    assert stats.total == 3
    assert stats.total_slips == 60  # 10 + 20 + 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

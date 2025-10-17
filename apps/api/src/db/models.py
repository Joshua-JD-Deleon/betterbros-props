"""
SQLAlchemy models for BetterBros Props database

All models use best practices:
- UUID primary keys for scalability
- Proper indexes on frequently queried fields
- JSONB for flexible/nested data
- Timestamps with timezone
- Foreign key relationships with proper cascades
"""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    Index,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class User(Base):
    """
    User model - stores user account information

    Integrated with Clerk/Supabase for authentication.
    clerk_user_id or supabase_user_id is the external auth provider ID.
    """
    __tablename__ = "users"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )

    # Authentication provider IDs
    clerk_user_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
        comment="Clerk user ID if using Clerk auth",
    )
    supabase_user_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        nullable=True,
        index=True,
        comment="Supabase user ID if using Supabase auth",
    )

    # User information
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
    )
    full_name: Mapped[Optional[str]] = mapped_column(String(255))

    # Subscription
    subscription_tier: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="free",
        comment="Subscription tier: free, pro, enterprise",
    )
    subscription_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
        comment="Status: active, cancelled, past_due, trialing",
    )
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Metadata
    user_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    experiments: Mapped[list["Experiment"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    saved_slips: Mapped[list["SavedSlip"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_clerk_id", "clerk_user_id"),
        Index("idx_users_supabase_id", "supabase_user_id"),
        Index("idx_users_subscription", "subscription_tier", "subscription_status"),
        CheckConstraint(
            "(clerk_user_id IS NOT NULL) OR (supabase_user_id IS NOT NULL)",
            name="check_user_has_auth_id",
        ),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, tier={self.subscription_tier})>"


class Snapshot(Base):
    """
    Snapshot model - captures state of props/predictions at a point in time

    Used for versioning, backtesting, and reproducing results.
    """
    __tablename__ = "snapshots"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Unique snapshot identifier (can be human-readable)
    snapshot_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique identifier like 'nfl-week-5-2024' or UUID",
    )

    # Sport and time context
    week: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Week number for the sport season",
    )
    league: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="League: NFL, NBA, MLB, NHL",
    )
    season: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Season identifier like '2024' or '2023-24'",
    )

    # Configuration and data
    config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Snapshot configuration and parameters",
    )

    # Feature and model information
    features_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Path to feature data (S3, local, etc.)",
    )
    model_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="v1.0.0",
        comment="Model version used for predictions",
    )

    # Metadata
    name: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_locked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Lock snapshot to prevent modifications",
    )
    tags: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Tags for categorization and search",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    game_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Date of games in this snapshot",
    )

    # Relationships
    experiments: Mapped[list["Experiment"]] = relationship(back_populates="snapshot")
    saved_slips: Mapped[list["SavedSlip"]] = relationship(back_populates="snapshot")
    prop_markets: Mapped[list["PropMarket"]] = relationship(back_populates="snapshot")

    # Indexes
    __table_args__ = (
        Index("idx_snapshots_snapshot_id", "snapshot_id"),
        Index("idx_snapshots_week_league", "week", "league"),
        Index("idx_snapshots_created_at", "created_at"),
        Index("idx_snapshots_game_date", "game_date"),
    )

    def __repr__(self) -> str:
        return f"<Snapshot(snapshot_id={self.snapshot_id}, week={self.week}, league={self.league})>"


class Experiment(Base):
    """
    Experiment model - tracks ML experiments and backtesting runs

    Stores configuration, metrics, and results for experiments.
    """
    __tablename__ = "experiments"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    snapshot_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("snapshots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Experiment context
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="When the experiment was run",
    )
    week: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    league: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Configuration
    risk_mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="balanced",
        comment="Risk mode: conservative, balanced, aggressive",
    )
    bankroll: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1000.0,
        comment="Simulated bankroll for the experiment",
    )
    num_props: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of props analyzed",
    )
    num_slips: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of slips/parlays generated",
    )

    # Results and metrics
    metrics: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Experiment metrics: ROI, win rate, sharpe, etc.",
    )

    # Metadata
    name: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="completed",
        comment="Status: draft, running, completed, failed",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="experiments")
    snapshot: Mapped[Optional["Snapshot"]] = relationship(back_populates="experiments")

    # Indexes
    __table_args__ = (
        Index("idx_experiments_user_id", "user_id"),
        Index("idx_experiments_snapshot_id", "snapshot_id"),
        Index("idx_experiments_week_league", "week", "league"),
        Index("idx_experiments_timestamp", "timestamp"),
        Index("idx_experiments_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Experiment(id={self.id}, user_id={self.user_id}, week={self.week})>"


class SavedSlip(Base):
    """
    SavedSlip model - user-saved parlay slips with predictions

    Stores optimized parlay combinations with edge metrics.
    """
    __tablename__ = "saved_slips"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    snapshot_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("snapshots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Slip data
    legs: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        comment="Array of prop legs in the parlay",
    )

    # Edge metrics
    ev: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Expected value of the parlay",
    )
    variance: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Variance of the parlay",
    )
    var_95: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="95% Value at Risk",
    )
    stake: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Recommended stake amount",
    )

    # Correlation data
    correlations: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Correlation matrix for legs",
    )

    # Metadata
    name: Mapped[Optional[str]] = mapped_column(String(255))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_placed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the slip was actually placed",
    )
    platform: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Platform where placed: prizepicks, underdog, etc.",
    )
    tags: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    placed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the slip was placed",
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="saved_slips")
    snapshot: Mapped[Optional["Snapshot"]] = relationship(back_populates="saved_slips")

    # Indexes
    __table_args__ = (
        Index("idx_saved_slips_user_id", "user_id"),
        Index("idx_saved_slips_snapshot_id", "snapshot_id"),
        Index("idx_saved_slips_created_at", "created_at"),
        Index("idx_saved_slips_ev", "ev"),
        Index("idx_saved_slips_is_placed", "is_placed"),
    )

    def __repr__(self) -> str:
        return f"<SavedSlip(id={self.id}, user_id={self.user_id}, ev={self.ev})>"


class PropMarket(Base):
    """
    PropMarket model - individual prop markets from various platforms

    Stores prop betting lines from PrizePicks, Underdog, etc.
    """
    __tablename__ = "prop_markets"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Foreign keys
    snapshot_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("snapshots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Sport and time context
    sport: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        comment="Sport: NFL, NBA, MLB, NHL",
    )
    week: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    league: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    season: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Prop details
    player_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="External player ID from data source",
    )
    player_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    position: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Player position: QB, RB, WR, PG, C, SP, etc.",
    )
    team: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    opponent: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Market details
    market_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Stat type: Passing Yards, Points, Strikeouts, Power Play Points, etc. See STATS_REFERENCE.md for all supported stats",
    )
    stat_category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Stat category: Passing, Scoring, Pitching, Skater, etc.",
    )
    line: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="The line value",
    )
    odds: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Decimal odds if available",
    )

    # Platform
    platform: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Platform: prizepicks, underdog, etc.",
    )
    external_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="External ID from the platform",
    )

    # Game context
    game_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    game_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    # Metadata
    extra_metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional platform-specific data",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    snapshot: Mapped[Optional["Snapshot"]] = relationship(back_populates="prop_markets")

    # Indexes
    __table_args__ = (
        Index("idx_prop_markets_sport", "sport"),
        Index("idx_prop_markets_week_league", "week", "league"),
        Index("idx_prop_markets_player_name", "player_name"),
        Index("idx_prop_markets_market_type", "market_type"),
        Index("idx_prop_markets_stat_category", "stat_category"),
        Index("idx_prop_markets_platform", "platform"),
        Index("idx_prop_markets_game_date", "game_date"),
        Index("idx_prop_markets_is_active", "is_active"),
        Index("idx_prop_markets_snapshot_id", "snapshot_id"),
        # Composite indexes for common multi-sport queries
        Index("idx_prop_markets_sport_week", "sport", "week"),
        Index("idx_prop_markets_sport_active", "sport", "is_active"),
        Index("idx_prop_markets_sport_market_type", "sport", "market_type"),
        Index("idx_prop_markets_sport_category", "sport", "stat_category"),
        Index("idx_prop_markets_week_league_player", "week", "league", "player_name"),
        Index("idx_prop_markets_platform_active", "platform", "is_active"),
    )

    def __repr__(self) -> str:
        return (
            f"<PropMarket(sport={self.sport}, player={self.player_name}, market={self.market_type}, "
            f"line={self.line}, platform={self.platform})>"
        )

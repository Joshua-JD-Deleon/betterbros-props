"""
Pydantic schemas for database models

These schemas provide validation and serialization for database operations.
They mirror the SQLAlchemy models but with proper validation.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, model_validator

from ..types import (
    Sport,
    StatCategory,
    validate_stat_type_for_sport,
    get_category_for_stat,
    SPORT_STAT_TYPES,
)


# ============================================================================
# PropMarket Schemas
# ============================================================================

class PropMarketBase(BaseModel):
    """Base schema for PropMarket with common fields"""
    model_config = ConfigDict(from_attributes=True)

    sport: Sport = Field(..., description="Sport: NFL, NBA, MLB, NHL")
    week: int = Field(..., ge=1, description="Week number for the sport season")
    league: str = Field(..., description="League: NFL, NBA, MLB, NHL")
    season: Optional[str] = Field(None, description="Season identifier like '2024' or '2023-24'")

    # Prop details
    player_id: Optional[str] = Field(None, description="External player ID from data source")
    player_name: str = Field(..., min_length=1, max_length=255, description="Player name")
    position: Optional[str] = Field(None, max_length=10, description="Player position: QB, RB, WR, PG, C, SP, etc.")
    team: Optional[str] = Field(None, max_length=100, description="Team abbreviation")
    opponent: Optional[str] = Field(None, max_length=100, description="Opponent abbreviation")

    # Market details
    market_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Stat type - must be valid for the sport. See STATS_REFERENCE.md"
    )
    stat_category: Optional[StatCategory] = Field(None, description="Stat category for filtering")
    line: float = Field(..., description="The line value")
    odds: Optional[float] = Field(None, description="Decimal odds if available")

    # Platform
    platform: str = Field(..., max_length=50, description="Platform: prizepicks, underdog, etc.")
    external_id: Optional[str] = Field(None, max_length=255, description="External ID from the platform")

    # Game context
    game_id: Optional[str] = Field(None, max_length=255)
    game_date: Optional[datetime] = Field(None, description="Game date with timezone")

    # Status
    is_active: bool = Field(True, description="Whether the prop is currently active")

    @model_validator(mode='after')
    def validate_market_type(self) -> 'PropMarketBase':
        """Validate that market_type is valid for the sport"""
        if not validate_stat_type_for_sport(self.sport, self.market_type):
            valid_stats = [s.value for s in SPORT_STAT_TYPES[self.sport]]
            raise ValueError(
                f"Invalid market_type '{self.market_type}' for sport {self.sport.value}. "
                f"Valid options: {', '.join(valid_stats)}"
            )

        # Auto-populate stat_category if not provided
        if self.stat_category is None:
            self.stat_category = get_category_for_stat(self.sport, self.market_type)

        return self


class PropMarketCreate(PropMarketBase):
    """Schema for creating a new PropMarket"""
    snapshot_id: Optional[UUID] = Field(None, description="Optional snapshot to associate with")
    extra_metadata: Optional[dict] = Field(None, description="Additional platform-specific data")


class PropMarketUpdate(BaseModel):
    """Schema for updating a PropMarket"""
    model_config = ConfigDict(from_attributes=True)

    line: Optional[float] = None
    odds: Optional[float] = None
    is_active: Optional[bool] = None
    game_date: Optional[datetime] = None
    extra_metadata: Optional[dict] = None


class PropMarketResponse(PropMarketBase):
    """Schema for PropMarket responses"""
    id: UUID
    snapshot_id: Optional[UUID]
    extra_metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Snapshot Schemas
# ============================================================================

class SnapshotBase(BaseModel):
    """Base schema for Snapshot"""
    model_config = ConfigDict(from_attributes=True)

    snapshot_id: str = Field(..., min_length=1, max_length=255, description="Unique identifier")
    week: int = Field(..., ge=1, description="Week number")
    league: str = Field(..., max_length=50, description="League: NFL, NBA, MLB, NHL")
    season: Optional[str] = Field(None, max_length=20)

    config: dict = Field(default_factory=dict, description="Snapshot configuration")
    features_path: Optional[str] = Field(None, max_length=500)
    model_version: str = Field("v1.0.0", max_length=50)

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    is_locked: bool = False
    tags: Optional[list] = None


class SnapshotCreate(SnapshotBase):
    """Schema for creating a new Snapshot"""
    game_date: Optional[datetime] = None


class SnapshotUpdate(BaseModel):
    """Schema for updating a Snapshot"""
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = None
    description: Optional[str] = None
    is_locked: Optional[bool] = None
    tags: Optional[list] = None
    config: Optional[dict] = None


class SnapshotResponse(SnapshotBase):
    """Schema for Snapshot responses"""
    id: UUID
    created_at: datetime
    game_date: Optional[datetime]


# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseModel):
    """Base schema for User"""
    model_config = ConfigDict(from_attributes=True)

    email: str = Field(..., max_length=255)
    username: Optional[str] = Field(None, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)


class UserCreate(UserBase):
    """Schema for creating a new User"""
    clerk_user_id: Optional[str] = Field(None, max_length=255)
    supabase_user_id: Optional[UUID] = None
    subscription_tier: str = Field("free", max_length=50)


class UserUpdate(BaseModel):
    """Schema for updating a User"""
    model_config = ConfigDict(from_attributes=True)

    username: Optional[str] = None
    full_name: Optional[str] = None
    subscription_tier: Optional[str] = None
    subscription_status: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for User responses"""
    id: UUID
    clerk_user_id: Optional[str]
    supabase_user_id: Optional[UUID]
    subscription_tier: str
    subscription_status: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime]


# ============================================================================
# Experiment Schemas
# ============================================================================

class ExperimentBase(BaseModel):
    """Base schema for Experiment"""
    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime
    week: int = Field(..., ge=1)
    league: str = Field(..., max_length=50)

    risk_mode: str = Field("balanced", max_length=50)
    bankroll: float = Field(1000.0, gt=0)
    num_props: int = Field(0, ge=0)
    num_slips: int = Field(0, ge=0)

    metrics: dict = Field(default_factory=dict)
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: str = Field("completed", max_length=50)


class ExperimentCreate(ExperimentBase):
    """Schema for creating a new Experiment"""
    user_id: UUID
    snapshot_id: Optional[UUID] = None


class ExperimentUpdate(BaseModel):
    """Schema for updating an Experiment"""
    model_config = ConfigDict(from_attributes=True)

    metrics: Optional[dict] = None
    status: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None


class ExperimentResponse(ExperimentBase):
    """Schema for Experiment responses"""
    id: UUID
    user_id: UUID
    snapshot_id: Optional[UUID]
    created_at: datetime


# ============================================================================
# SavedSlip Schemas
# ============================================================================

class SavedSlipBase(BaseModel):
    """Base schema for SavedSlip"""
    model_config = ConfigDict(from_attributes=True)

    legs: list = Field(..., description="Array of prop legs in the parlay")
    ev: float = Field(..., description="Expected value of the parlay")
    variance: Optional[float] = None
    var_95: Optional[float] = None
    stake: Optional[float] = None

    correlations: Optional[dict] = None
    name: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    is_placed: bool = False
    platform: Optional[str] = Field(None, max_length=50)
    tags: Optional[list] = None


class SavedSlipCreate(SavedSlipBase):
    """Schema for creating a new SavedSlip"""
    user_id: UUID
    snapshot_id: Optional[UUID] = None


class SavedSlipUpdate(BaseModel):
    """Schema for updating a SavedSlip"""
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = None
    notes: Optional[str] = None
    is_placed: Optional[bool] = None
    placed_at: Optional[datetime] = None
    tags: Optional[list] = None


class SavedSlipResponse(SavedSlipBase):
    """Schema for SavedSlip responses"""
    id: UUID
    user_id: UUID
    snapshot_id: Optional[UUID]
    created_at: datetime
    placed_at: Optional[datetime]

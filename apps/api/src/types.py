"""
Comprehensive Pydantic models for all API request/response bodies
"""
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


# ============================================================================
# Enums and Literals
# ============================================================================

class Sport(str, Enum):
    NBA = "nba"
    NFL = "nfl"
    MLB = "mlb"
    NHL = "nhl"


class PropType(str, Enum):
    OVER_UNDER = "over_under"
    GOAL_SCORER = "goal_scorer"
    COMBO = "combo"


class BetDirection(str, Enum):
    OVER = "over"
    UNDER = "under"
    YES = "yes"
    NO = "no"


class Platform(str, Enum):
    PRIZEPICKS = "prizepicks"
    UNDERDOG = "underdog"


class ModelType(str, Enum):
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    NEURAL_NET = "neural_net"
    ENSEMBLE = "ensemble"


class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# Core Data Models
# ============================================================================

class Player(BaseModel):
    """Player information"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    team: str
    position: str
    jersey_number: Optional[str] = None


class Team(BaseModel):
    """Team information"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    abbreviation: str
    sport: Sport


class Game(BaseModel):
    """Game/Match information"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    sport: Sport
    home_team: Team
    away_team: Team
    start_time: datetime
    venue: Optional[str] = None
    status: Literal["scheduled", "in_progress", "completed", "postponed"] = "scheduled"


# ============================================================================
# Props and Markets
# ============================================================================

class PropLeg(BaseModel):
    """Individual prop leg in a market"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    player_id: str
    player_name: str
    stat_type: str = Field(..., description="e.g., 'points', 'rebounds', 'assists'")
    line: float = Field(..., description="The line value")
    direction: BetDirection
    odds: Optional[float] = Field(None, description="Decimal odds if available")

    # Metadata
    team: str
    opponent: str
    game_id: str
    position: Optional[str] = None


class PropMarket(BaseModel):
    """Complete prop market from a platform"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    platform: Platform
    sport: Sport
    prop_type: PropType
    legs: List[PropLeg]
    payout_multiplier: float = Field(..., description="e.g., 3.0 for 3x payout")

    # Timestamps
    created_at: datetime
    start_time: datetime
    expires_at: Optional[datetime] = None

    # Metadata
    is_active: bool = True
    min_legs: int = Field(default=2)
    max_legs: int = Field(default=6)


class PropMarketCreate(BaseModel):
    """Request to create/import prop markets"""
    platform: Platform
    sport: Sport
    markets: List[Dict[str, Any]] = Field(..., description="Raw market data from platform")


class PropMarketResponse(BaseModel):
    """Response with prop markets"""
    markets: List[PropMarket]
    total: int
    page: int = 1
    page_size: int = 50


# ============================================================================
# Context Data
# ============================================================================

class InjuryReport(BaseModel):
    """Player injury information"""
    player_id: str
    player_name: str
    status: Literal["out", "doubtful", "questionable", "probable", "healthy"]
    injury_type: Optional[str] = None
    updated_at: datetime


class TeamStats(BaseModel):
    """Team-level statistics"""
    team_id: str
    pace: Optional[float] = None
    offensive_rating: Optional[float] = None
    defensive_rating: Optional[float] = None
    net_rating: Optional[float] = None

    # Additional sport-specific stats
    additional_stats: Dict[str, float] = Field(default_factory=dict)


class WeatherData(BaseModel):
    """Weather data for outdoor games"""
    temperature: Optional[float] = Field(None, description="Temperature in Fahrenheit")
    wind_speed: Optional[float] = Field(None, description="Wind speed in mph")
    precipitation: Optional[float] = Field(None, description="Precipitation probability")
    humidity: Optional[float] = None
    conditions: Optional[str] = None


class VenueData(BaseModel):
    """Venue/stadium information"""
    venue_id: str
    name: str
    location: str
    capacity: Optional[int] = None
    surface_type: Optional[str] = None
    is_indoor: bool = False


class ContextData(BaseModel):
    """Contextual data for a game or player"""
    model_config = ConfigDict(from_attributes=True)

    game_id: str
    sport: Sport

    # Injuries
    injuries: List[InjuryReport] = Field(default_factory=list)

    # Team context
    home_team_stats: Optional[TeamStats] = None
    away_team_stats: Optional[TeamStats] = None

    # Environmental
    weather: Optional[WeatherData] = None
    venue: Optional[VenueData] = None

    # Rest and travel
    home_team_rest_days: Optional[int] = None
    away_team_rest_days: Optional[int] = None
    away_team_travel_distance: Optional[float] = None

    # Recent form
    home_team_last_5: Optional[str] = Field(None, description="e.g., 'W-W-L-W-L'")
    away_team_last_5: Optional[str] = None

    # Meta
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class ContextDataRequest(BaseModel):
    """Request for context data"""
    game_ids: List[str]
    sport: Sport
    include_injuries: bool = True
    include_weather: bool = True
    include_team_stats: bool = True


# ============================================================================
# Features
# ============================================================================

class PlayerFeatures(BaseModel):
    """Feature set for a single player"""
    player_id: str
    player_name: str

    # Rolling averages
    avg_last_5: Optional[float] = None
    avg_last_10: Optional[float] = None
    avg_season: Optional[float] = None

    # Matchup-specific
    avg_vs_opponent: Optional[float] = None
    avg_home_away: Optional[float] = None

    # Trend features
    trend_slope: Optional[float] = None
    recent_volatility: Optional[float] = None

    # Usage and pace
    usage_rate: Optional[float] = None
    pace_adjusted: Optional[float] = None

    # Additional features
    features: Dict[str, float] = Field(default_factory=dict)


class FeatureSet(BaseModel):
    """Complete feature set for prediction"""
    model_config = ConfigDict(from_attributes=True)

    prop_leg_id: str
    player_features: PlayerFeatures
    team_features: Dict[str, float] = Field(default_factory=dict)
    opponent_features: Dict[str, float] = Field(default_factory=dict)
    contextual_features: Dict[str, float] = Field(default_factory=dict)

    # Metadata
    feature_version: str = Field(default="v1.0.0")
    computed_at: datetime = Field(default_factory=datetime.utcnow)


class FeatureSetRequest(BaseModel):
    """Request to compute features"""
    prop_leg_ids: List[str]
    include_historical: bool = True
    lookback_days: int = Field(default=30, ge=1, le=365)


class FeatureSetResponse(BaseModel):
    """Response with computed features"""
    features: List[FeatureSet]
    total: int


# ============================================================================
# Model Predictions
# ============================================================================

class DistributionStats(BaseModel):
    """Statistical distribution of predictions"""
    mean: float
    median: float
    std_dev: float
    percentile_25: float
    percentile_75: float
    percentile_90: float
    min_value: float
    max_value: float


class ModelPrediction(BaseModel):
    """Prediction from ML model"""
    model_config = ConfigDict(from_attributes=True)

    prop_leg_id: str
    player_id: str
    stat_type: str

    # Point prediction
    predicted_value: float
    line_value: float

    # Probabilities
    prob_over: float = Field(..., ge=0.0, le=1.0)
    prob_under: float = Field(..., ge=0.0, le=1.0)

    # Confidence and edges
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence")
    edge: float = Field(..., description="Expected edge over the line")
    kelly_fraction: Optional[float] = Field(None, description="Suggested Kelly stake")

    # Distribution
    distribution: Optional[DistributionStats] = None

    # Model metadata
    model_type: ModelType
    model_version: str
    feature_importance: Optional[Dict[str, float]] = None

    # Timestamps
    predicted_at: datetime = Field(default_factory=datetime.utcnow)


class ModelPredictionRequest(BaseModel):
    """Request for model predictions"""
    prop_leg_ids: List[str]
    model_type: Optional[ModelType] = None
    use_ensemble: bool = True


class ModelPredictionResponse(BaseModel):
    """Response with model predictions"""
    predictions: List[ModelPrediction]
    total: int
    model_version: str


# ============================================================================
# Correlations
# ============================================================================

class CorrelationPair(BaseModel):
    """Correlation between two prop legs"""
    leg_id_1: str
    leg_id_2: str
    player_1: str
    player_2: str
    stat_type_1: str
    stat_type_2: str

    correlation: float = Field(..., ge=-1.0, le=1.0)
    sample_size: int
    p_value: Optional[float] = None
    is_significant: bool = False


class CorrelationMatrix(BaseModel):
    """Matrix of correlations for a set of props"""
    model_config = ConfigDict(from_attributes=True)

    prop_leg_ids: List[str]
    correlations: List[CorrelationPair]

    # Metadata
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    lookback_days: int = 30
    min_sample_size: int = 10


class CorrelationRequest(BaseModel):
    """Request to compute correlations"""
    prop_leg_ids: List[str] = Field(..., min_length=2, max_length=20)
    lookback_days: int = Field(default=30, ge=7, le=365)
    min_sample_size: int = Field(default=10, ge=5)


# ============================================================================
# Optimization
# ============================================================================

class OptimizationConstraints(BaseModel):
    """Constraints for parlay optimization"""
    min_legs: int = Field(default=2, ge=2)
    max_legs: int = Field(default=5, le=6)
    min_edge: float = Field(default=0.05, description="Minimum edge per leg")
    min_confidence: float = Field(default=0.6, ge=0.0, le=1.0)
    max_correlation: float = Field(default=0.3, ge=0.0, le=1.0)

    # Risk management
    max_player_exposure: int = Field(default=1, description="Max legs from same player")
    max_team_exposure: int = Field(default=3, description="Max legs from same team")
    max_game_exposure: int = Field(default=2, description="Max legs from same game")

    # Diversity
    require_diverse_stats: bool = Field(default=True)
    require_diverse_games: bool = Field(default=True)


class ParlayCandidate(BaseModel):
    """Optimized parlay candidate"""
    prop_leg_ids: List[str]
    legs: List[PropLeg]
    predictions: List[ModelPrediction]

    # Scoring
    expected_value: float
    total_edge: float
    win_probability: float
    combined_confidence: float
    kelly_stake: Optional[float] = None

    # Risk metrics
    max_correlation: float
    diversification_score: float

    # Rankings
    rank: int
    score: float = Field(..., description="Composite optimization score")


class OptimizationRequest(BaseModel):
    """Request to optimize parlays"""
    prop_leg_ids: List[str] = Field(..., min_length=2)
    constraints: OptimizationConstraints = Field(default_factory=OptimizationConstraints)
    top_k: int = Field(default=10, ge=1, le=100, description="Number of candidates to return")
    algorithm: Literal["greedy", "genetic", "milp"] = "greedy"


class OptimizationResponse(BaseModel):
    """Response with optimized parlays"""
    candidates: List[ParlayCandidate]
    total_evaluated: int
    computation_time_ms: float


# ============================================================================
# Slip Detection
# ============================================================================

class SlipDriver(BaseModel):
    """Driver for a slip/edge opportunity"""
    type: Literal["market_inefficiency", "model_edge", "correlation_play", "injury_impact", "line_movement"]
    description: str
    impact_score: float = Field(..., ge=0.0, le=1.0)


class SlipCandidate(BaseModel):
    """Slip/edge opportunity candidate"""
    model_config = ConfigDict(from_attributes=True)

    prop_leg_id: str
    player_name: str
    stat_type: str
    line: float
    direction: BetDirection

    # Edge metrics
    edge: float
    confidence: float
    expected_value: float

    # Drivers
    drivers: List[SlipDriver]
    primary_driver: str

    # Risk
    risk_score: float = Field(..., ge=0.0, le=1.0)
    volatility: float

    # Meta
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class SlipDetectionRequest(BaseModel):
    """Request to detect slip opportunities"""
    min_edge: float = Field(default=0.1, ge=0.0)
    min_confidence: float = Field(default=0.65, ge=0.0, le=1.0)
    max_risk: float = Field(default=0.5, ge=0.0, le=1.0)
    top_k: int = Field(default=20, ge=1, le=100)


class SlipDetectionResponse(BaseModel):
    """Response with slip candidates"""
    slips: List[SlipCandidate]
    total_evaluated: int


# ============================================================================
# Backtesting and Evaluation
# ============================================================================

class BacktestConfig(BaseModel):
    """Configuration for backtesting"""
    start_date: datetime
    end_date: datetime
    strategy: Literal["all_edges", "threshold", "optimized_parlays"]

    # Strategy parameters
    min_edge: float = 0.05
    min_confidence: float = 0.6
    parlay_constraints: Optional[OptimizationConstraints] = None

    # Execution
    simulated_bankroll: float = 10000.0
    stake_method: Literal["fixed", "kelly", "kelly_fraction"] = "kelly_fraction"
    kelly_multiplier: float = 0.25


class BacktestResult(BaseModel):
    """Results from backtesting"""
    model_config = ConfigDict(from_attributes=True)

    config: BacktestConfig

    # Performance metrics
    total_bets: int
    winning_bets: int
    losing_bets: int
    win_rate: float

    # Financial metrics
    total_wagered: float
    total_profit: float
    roi: float
    sharpe_ratio: Optional[float] = None
    max_drawdown: float

    # Per-bet metrics
    avg_edge: float
    avg_confidence: float
    avg_odds: float

    # Calibration
    calibration_score: Optional[float] = None
    brier_score: Optional[float] = None

    # Time series
    daily_pnl: Optional[List[Dict[str, Any]]] = None
    equity_curve: Optional[List[Dict[str, Any]]] = None

    # Meta
    computed_at: datetime = Field(default_factory=datetime.utcnow)


class BacktestRequest(BaseModel):
    """Request to run backtest"""
    config: BacktestConfig
    model_version: Optional[str] = None


# ============================================================================
# Snapshots and Versioning
# ============================================================================

class Snapshot(BaseModel):
    """Snapshot of props, predictions, and context at a point in time"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None

    # Data
    prop_markets: List[str] = Field(..., description="List of prop market IDs")
    predictions: List[str] = Field(..., description="List of prediction IDs")
    correlations: Optional[str] = Field(None, description="Correlation matrix ID")

    # Metadata
    sport: Sport
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    game_date: Optional[datetime] = None

    # Status
    is_locked: bool = False
    tags: List[str] = Field(default_factory=list)


class SnapshotCreate(BaseModel):
    """Request to create a snapshot"""
    name: str
    description: Optional[str] = None
    sport: Sport
    game_date: Optional[datetime] = None
    prop_leg_ids: List[str]
    tags: List[str] = Field(default_factory=list)


class SnapshotResponse(BaseModel):
    """Response with snapshots"""
    snapshots: List[Snapshot]
    total: int


# ============================================================================
# Experiments and A/B Testing
# ============================================================================

class ExperimentConfig(BaseModel):
    """Configuration for an experiment"""
    model_type: ModelType
    hyperparameters: Dict[str, Any]
    feature_set_version: str
    training_data_filter: Optional[Dict[str, Any]] = None


class Experiment(BaseModel):
    """ML experiment tracking"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    status: ExperimentStatus

    # Configuration
    config: ExperimentConfig

    # Results
    metrics: Dict[str, float] = Field(default_factory=dict)
    validation_metrics: Optional[Dict[str, float]] = None
    backtest_results: Optional[BacktestResult] = None

    # Metadata
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Artifacts
    model_artifact_url: Optional[str] = None
    logs_url: Optional[str] = None


class ExperimentCreate(BaseModel):
    """Request to create an experiment"""
    name: str
    description: Optional[str] = None
    config: ExperimentConfig


class ExperimentResponse(BaseModel):
    """Response with experiments"""
    experiments: List[Experiment]
    total: int


# ============================================================================
# API Keys Management
# ============================================================================

class ApiKeySource(str, Enum):
    PRIZEPICKS = "prizepicks"
    UNDERDOG = "underdog"
    ESPN = "espn"
    NBA_STATS = "nba_stats"
    SPORTSRADAR = "sportsradar"


class ApiKey(BaseModel):
    """API key configuration"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    source: ApiKeySource
    name: str

    # Key is encrypted in storage, never returned in full
    key_preview: str = Field(..., description="Last 4 characters of key")

    # Status
    is_active: bool = True
    is_valid: Optional[bool] = None
    last_validated_at: Optional[datetime] = None

    # Usage
    rate_limit: Optional[int] = None
    requests_made: int = 0
    last_used_at: Optional[datetime] = None

    # Metadata
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ApiKeyCreate(BaseModel):
    """Request to create/update an API key"""
    source: ApiKeySource
    name: str
    key: str = Field(..., description="The actual API key (will be encrypted)")


class ApiKeyResponse(BaseModel):
    """Response with API keys"""
    keys: List[ApiKey]
    total: int


# ============================================================================
# What-If Analysis
# ============================================================================

class WhatIfScenario(BaseModel):
    """What-if scenario parameters"""
    player_id: str
    stat_type: str

    # Adjustments
    injury_status: Optional[Literal["out", "questionable", "healthy"]] = None
    usage_rate_adjustment: Optional[float] = Field(None, description="e.g., +0.05 for 5% increase")
    pace_adjustment: Optional[float] = None
    matchup_difficulty: Optional[Literal["easy", "average", "hard"]] = None

    # Custom overrides
    custom_features: Optional[Dict[str, float]] = None


class WhatIfResult(BaseModel):
    """Result from what-if analysis"""
    scenario: WhatIfScenario
    baseline_prediction: ModelPrediction
    adjusted_prediction: ModelPrediction

    # Deltas
    delta_predicted_value: float
    delta_prob_over: float
    delta_edge: float

    # Explanation
    impact_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="Feature-level impact of adjustments"
    )


class WhatIfRequest(BaseModel):
    """Request for what-if analysis"""
    prop_leg_id: str
    scenarios: List[WhatIfScenario]


class WhatIfResponse(BaseModel):
    """Response with what-if results"""
    results: List[WhatIfResult]


# ============================================================================
# Historical Data
# ============================================================================

class HistoricalPerformance(BaseModel):
    """Historical performance of a player for a stat"""
    player_id: str
    player_name: str
    stat_type: str

    games: List[Dict[str, Any]] = Field(..., description="Game-by-game performance")

    # Aggregates
    avg_value: float
    median_value: float
    std_dev: float
    min_value: float
    max_value: float

    # Splits
    home_avg: Optional[float] = None
    away_avg: Optional[float] = None
    vs_opponent_avg: Optional[float] = None

    # Meta
    sample_size: int
    date_range_start: datetime
    date_range_end: datetime


class HistoricalRequest(BaseModel):
    """Request for historical data"""
    player_id: str
    stat_types: List[str]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    opponent_team_id: Optional[str] = None


class HistoricalResponse(BaseModel):
    """Response with historical data"""
    performances: List[HistoricalPerformance]


# ============================================================================
# Authentication
# ============================================================================

class UserProfile(BaseModel):
    """User profile information"""
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None

    # Subscription
    subscription_tier: Literal["free", "pro", "enterprise"] = "free"
    is_active: bool = True

    # Metadata
    created_at: datetime
    last_login_at: Optional[datetime] = None


class TokenResponse(BaseModel):
    """Authentication token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfile


# ============================================================================
# Export Formats
# ============================================================================

class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"


class ExportRequest(BaseModel):
    """Request to export data"""
    snapshot_id: Optional[str] = None
    prop_leg_ids: Optional[List[str]] = None
    include_predictions: bool = True
    include_features: bool = False
    format: ExportFormat = ExportFormat.JSON


class ExportResponse(BaseModel):
    """Response with export data or download URL"""
    download_url: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    format: ExportFormat
    expires_at: Optional[datetime] = None

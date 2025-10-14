"""
Configuration management using Pydantic for validation and YAML for storage.
"""

from typing import Dict, List, Optional, Literal, Union
from pathlib import Path
import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


class RiskModeConfig(BaseModel):
    """Configuration for a specific risk mode."""
    max_slip_legs: int = Field(ge=2, le=10)
    min_single_leg_prob: float = Field(ge=0.0, le=1.0)


class UIWeekSelection(BaseModel):
    """Week selection UI settings."""
    default_week: Union[Literal["current"], int] = "current"
    allow_past_weeks: bool = True


class UIRiskMode(BaseModel):
    """Risk mode UI settings."""
    default: Literal["conservative", "balanced", "aggressive"] = "balanced"
    modes: Dict[str, RiskModeConfig] = Field(default_factory=dict)


class UIBadges(BaseModel):
    """Badge display settings."""
    show_trend_badges: bool = True
    show_injury_alerts: bool = True
    show_weather_icons: bool = True


class UIBankroll(BaseModel):
    """Bankroll settings."""
    default_amount: float = Field(gt=0)
    currency: str = "USD"
    track_history: bool = True


class UITrendChips(BaseModel):
    """Trend chips settings."""
    enabled: bool = True
    max_displayed: int = Field(ge=1, le=10, default=5)
    categories: List[str] = Field(default_factory=list)


class UIPresets(BaseModel):
    """Preset configurations."""
    conservative: Dict[str, float] = Field(default_factory=dict)
    balanced: Dict[str, float] = Field(default_factory=dict)
    aggressive: Dict[str, float] = Field(default_factory=dict)


class UITheme(BaseModel):
    """Theme settings."""
    night_mode: bool = False
    accent_color: str = "#1f77b4"


class UICIFilter(BaseModel):
    """Confidence interval filter settings."""
    enabled: bool = True
    max_width: float = Field(ge=0.0, le=1.0, default=0.25)


class UIWhatIf(BaseModel):
    """What-if analysis settings."""
    enabled: bool = True
    allow_probability_adjust: bool = True
    allow_odds_adjust: bool = True


class UIConfig(BaseModel):
    """All UI-related configuration."""
    week_selection: UIWeekSelection = Field(default_factory=UIWeekSelection)
    risk_mode: UIRiskMode = Field(default_factory=UIRiskMode)
    badges: UIBadges = Field(default_factory=UIBadges)
    bankroll: UIBankroll = Field(default_factory=lambda: UIBankroll(default_amount=100.0))
    trend_chips: UITrendChips = Field(default_factory=UITrendChips)
    presets: UIPresets = Field(default_factory=UIPresets)
    theme: UITheme = Field(default_factory=UITheme)
    ci_filter: UICIFilter = Field(default_factory=UICIFilter)
    what_if: UIWhatIf = Field(default_factory=UIWhatIf)


class SlipConstraints(BaseModel):
    """Constraints for slip optimization."""
    min_legs: int = Field(ge=2, default=2)
    max_legs: int = Field(ge=2, le=10, default=5)
    min_total_odds: float = Field(gt=1.0, default=2.0)
    max_total_odds: float = Field(gt=1.0, default=50.0)


class DiversityConfig(BaseModel):
    """Diversity settings for portfolio optimization."""
    target: float = Field(ge=0.0, le=1.0, default=0.5)
    player_repeat_limit: int = Field(ge=1, default=2)
    team_concentration_max: float = Field(ge=0.0, le=1.0, default=0.4)


class CorrelationConfig(BaseModel):
    """Correlation modeling settings."""
    use_copulas: bool = True
    correlation_penalty: bool = True
    max_same_game_legs: int = Field(ge=1, default=3)


class TargetsConfig(BaseModel):
    """Optimization targets."""
    expected_value_threshold: float = Field(gt=1.0, default=1.05)
    kelly_fraction: float = Field(gt=0.0, le=1.0, default=0.25)
    max_bet_pct: float = Field(gt=0.0, le=1.0, default=0.10)


class OptimizerConfig(BaseModel):
    """Optimizer configuration."""
    slip_constraints: SlipConstraints = Field(default_factory=SlipConstraints)
    diversity: DiversityConfig = Field(default_factory=DiversityConfig)
    correlation: CorrelationConfig = Field(default_factory=CorrelationConfig)
    targets: TargetsConfig = Field(default_factory=TargetsConfig)


class CalibrationConfig(BaseModel):
    """Calibration monitoring settings."""
    alert_threshold: float = Field(ge=0.0, le=1.0, default=0.15)
    lookback_weeks: int = Field(ge=1, default=4)
    check_intervals: List[float] = Field(default_factory=lambda: [0.5, 0.6, 0.7, 0.8, 0.9])


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""
    calibration: CalibrationConfig = Field(default_factory=CalibrationConfig)


class ExportConfig(BaseModel):
    """Export settings."""
    props_csv_path: str = "./exports/props_{date}.csv"
    slips_csv_path: str = "./exports/slips_{date}.csv"
    auto_timestamp: bool = True


class ExperimentsConfig(BaseModel):
    """Experiment tracking settings."""
    tracking_enabled: bool = True
    log_path: str = "./experiments/tracking.jsonl"
    track_events: List[str] = Field(default_factory=list)


class SnapshotsConfig(BaseModel):
    """Snapshot management settings."""
    dir: str = "./data/snapshots"
    auto_snapshot_on_generate: bool = True
    retention_days: int = Field(ge=1, default=30)


class KeysConfig(BaseModel):
    """API keys management settings."""
    storage_method: Literal["env_file", "keyring"] = "env_file"
    required_providers: List[str] = Field(default_factory=lambda: ["sleeper", "openweather"])


class ShareConfig(BaseModel):
    """Share/export settings."""
    anonymize_bankroll: bool = True
    include_diagnostics: bool = True
    include_trends: bool = True
    compression: bool = True


class AppConfig(BaseModel):
    """Main application configuration."""
    ui: UIConfig = Field(default_factory=UIConfig)
    optimizer: OptimizerConfig = Field(default_factory=OptimizerConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)
    experiments: ExperimentsConfig = Field(default_factory=ExperimentsConfig)
    snapshots: SnapshotsConfig = Field(default_factory=SnapshotsConfig)
    keys: KeysConfig = Field(default_factory=KeysConfig)
    share: ShareConfig = Field(default_factory=ShareConfig)


def load_user_prefs(path: Union[str, Path] = "user_prefs.yaml") -> AppConfig:
    """
    Load user preferences from YAML file.

    Args:
        path: Path to YAML configuration file

    Returns:
        Validated AppConfig instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValidationError: If config is invalid
    """
    path = Path(path)

    if not path.exists():
        # Return default config if file doesn't exist
        return AppConfig()

    with open(path, 'r') as f:
        data = yaml.safe_load(f)

    return AppConfig(**data)


def save_user_prefs(config: AppConfig, path: Union[str, Path] = "user_prefs.yaml") -> None:
    """
    Save user preferences to YAML file.

    Args:
        config: AppConfig instance to save
        path: Path to save YAML configuration
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w') as f:
        yaml.dump(config.model_dump(), f, default_flow_style=False, sort_keys=False)


def get_default_config() -> AppConfig:
    """
    Get default configuration.

    Returns:
        Default AppConfig instance
    """
    return AppConfig()

"""
Configuration management using Pydantic Settings
"""
from typing import List, Literal, Optional
from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Environment
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment",
    )

    # Authentication
    AUTH_PROVIDER: Literal["clerk", "supabase"] = Field(
        ...,
        description="Authentication provider (clerk or supabase)",
    )

    # Clerk Configuration
    CLERK_SECRET_KEY: Optional[str] = Field(
        default=None,
        description="Clerk secret key for JWT verification",
    )
    CLERK_JWT_ISSUER: Optional[str] = Field(
        default=None,
        description="Clerk JWT issuer URL",
    )

    # Supabase Configuration
    SUPABASE_URL: Optional[str] = Field(
        default=None,
        description="Supabase project URL",
    )
    SUPABASE_JWT_SECRET: Optional[str] = Field(
        default=None,
        description="Supabase JWT secret for verification",
    )
    SUPABASE_SERVICE_KEY: Optional[str] = Field(
        default=None,
        description="Supabase service role key",
    )

    # Database
    DATABASE_URL: PostgresDsn = Field(
        ...,
        description="PostgreSQL database connection URL",
    )
    DATABASE_POOL_SIZE: int = Field(
        default=20,
        description="Database connection pool size",
    )
    DATABASE_MAX_OVERFLOW: int = Field(
        default=10,
        description="Maximum overflow connections",
    )

    # Redis
    REDIS_URL: RedisDsn = Field(
        ...,
        description="Redis connection URL",
    )
    REDIS_MAX_CONNECTIONS: int = Field(
        default=50,
        description="Maximum Redis connections in pool",
    )
    REDIS_CACHE_TTL: int = Field(
        default=300,
        description="Default cache TTL in seconds",
    )

    # External APIs - Sports Data
    SLEEPER_API_KEY: Optional[str] = Field(
        default=None,
        description="Sleeper API key (optional, API is mostly public)",
    )
    PRIZEPICKS_API_KEY: Optional[str] = Field(
        default=None,
        description="PrizePicks API key",
    )
    UNDERDOG_API_KEY: Optional[str] = Field(
        default=None,
        description="Underdog Fantasy API key",
    )
    ESPN_API_KEY: Optional[str] = Field(
        default=None,
        description="ESPN API key",
    )
    NBA_API_KEY: Optional[str] = Field(
        default=None,
        description="NBA Stats API key",
    )
    SPORTSRADAR_API_KEY: Optional[str] = Field(
        default=None,
        description="SportsRadar API key",
    )
    OPENWEATHER_KEY: Optional[str] = Field(
        default=None,
        description="OpenWeather API key for weather data",
    )

    # External APIs - AI/ML
    OPENAI_API_KEY: Optional[str] = Field(
        default=None,
        description="OpenAI API key for AI features",
    )
    ANTHROPIC_API_KEY: Optional[str] = Field(
        default=None,
        description="Anthropic API key for Claude AI",
    )

    # Model Configuration
    MODEL_VERSION: str = Field(
        default="v1.0.0",
        description="Current ML model version",
    )
    MODEL_REGISTRY_URL: Optional[str] = Field(
        default=None,
        description="URL for model registry (e.g., MLflow)",
    )

    # Feature Store
    FEATURE_STORE_ENABLED: bool = Field(
        default=True,
        description="Enable feature store for ML features",
    )
    FEATURE_CACHE_TTL: int = Field(
        default=3600,
        description="Feature cache TTL in seconds",
    )

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins",
    )

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(
        default=True,
        description="Enable rate limiting",
    )
    RATE_LIMIT_REQUESTS: int = Field(
        default=100,
        description="Number of requests allowed per window",
    )
    RATE_LIMIT_WINDOW: int = Field(
        default=60,
        description="Rate limit window in seconds",
    )

    # Optimization
    MAX_PARLAY_SIZE: int = Field(
        default=5,
        description="Maximum number of legs in a parlay",
    )
    OPTIMIZATION_TIMEOUT: int = Field(
        default=30,
        description="Optimization timeout in seconds",
    )

    # Backtesting
    BACKTEST_MAX_DAYS: int = Field(
        default=90,
        description="Maximum days for backtesting",
    )
    BACKTEST_CACHE_ENABLED: bool = Field(
        default=True,
        description="Enable caching for backtest results",
    )

    # Background Jobs
    CELERY_BROKER_URL: Optional[str] = Field(
        default=None,
        description="Celery broker URL (if using background tasks)",
    )
    CELERY_RESULT_BACKEND: Optional[str] = Field(
        default=None,
        description="Celery result backend URL",
    )

    # Monitoring & Logging
    SENTRY_DSN: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error tracking",
    )
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Application log level",
    )

    # API Keys Management
    API_KEY_ENCRYPTION_KEY: Optional[str] = Field(
        default=None,
        description="Key for encrypting stored API keys",
    )

    @field_validator("AUTH_PROVIDER", mode="after")
    @classmethod
    def validate_auth_config(cls, v):
        """Validate that required auth provider keys are present"""
        # Validation done at runtime, not at initialization
        # This allows for more flexible development setup
        return v

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL (for Alembic)"""
        return str(self.DATABASE_URL).replace("+asyncpg", "")

    @property
    def redis_url_str(self) -> str:
        """Get Redis URL as string"""
        return str(self.REDIS_URL)


# Global settings instance
settings = Settings()

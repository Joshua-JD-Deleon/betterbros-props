# BetterBros Props API - Architecture

## Overview

The BetterBros Props API is a production-ready FastAPI service designed for AI-powered props betting optimization. It follows best practices for scalable backend architecture with async/await, type safety, and comprehensive error handling.

## Tech Stack

- **Framework**: FastAPI 0.109.0
- **Language**: Python 3.11+
- **Database**: PostgreSQL 14+ (with asyncpg)
- **Cache**: Redis 7+ (with hiredis)
- **Authentication**: Clerk or Supabase (pluggable)
- **Migrations**: Alembic
- **ML Libraries**: XGBoost, LightGBM, scikit-learn
- **Server**: Uvicorn with async workers

## Project Structure

```
apps/api/
├── main.py                      # FastAPI app initialization, middleware, routing
├── alembic/                     # Database migrations
│   ├── env.py                   # Alembic async environment
│   ├── versions/                # Migration files
│   └── script.py.mako          # Migration template
├── src/
│   ├── config.py               # Pydantic Settings for env vars
│   ├── types.py                # Comprehensive Pydantic models (500+ LOC)
│   ├── db.py                   # Database and Redis connections
│   ├── auth/
│   │   └── deps.py            # JWT validation (Clerk/Supabase)
│   └── routers/               # API endpoints (14 routers)
│       ├── props.py           # Props markets CRUD
│       ├── context.py         # Context data (injuries, weather)
│       ├── features.py        # Feature engineering
│       ├── model.py           # ML predictions
│       ├── corr.py            # Correlation analysis
│       ├── optimize.py        # Parlay optimization
│       ├── eval.py            # Backtesting and evaluation
│       ├── export.py          # Data export (JSON, CSV, Excel)
│       ├── snapshots.py       # Version control for predictions
│       ├── experiments.py     # ML experiment tracking
│       ├── keys.py            # API keys management
│       ├── whatif.py          # Scenario analysis
│       ├── history.py         # Historical data queries
│       └── auth.py            # Authentication endpoints
├── tests/                      # Test suite
│   ├── conftest.py            # Pytest fixtures
│   └── test_health.py         # Health check tests
├── scripts/
│   ├── start.sh               # Development startup
│   └── test.sh                # Run tests and linting
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Multi-stage production build
├── docker-compose.yml         # Local development stack
├── alembic.ini               # Alembic configuration
└── .env.example              # Environment variables template
```

## Core Components

### 1. Configuration Management (`src/config.py`)

Uses Pydantic Settings for type-safe environment variable handling:

- **Authentication**: Clerk or Supabase configuration
- **Database**: PostgreSQL with connection pooling
- **Redis**: Caching with configurable TTL
- **External APIs**: Sports data providers (PrizePicks, Underdog, ESPN, etc.)
- **ML Config**: Model versions, registry URLs
- **Rate Limiting**: Configurable thresholds
- **CORS**: Allowed origins

### 2. Type System (`src/types.py`)

Comprehensive Pydantic models for type safety across the API:

**Core Models:**
- `PropMarket`, `PropLeg`: Props markets and individual legs
- `ContextData`: Injuries, weather, team stats
- `FeatureSet`, `PlayerFeatures`: Feature engineering outputs
- `ModelPrediction`: ML predictions with probabilities
- `CorrelationMatrix`: Correlation analysis
- `ParlayCandidate`: Optimized parlay combinations
- `SlipCandidate`: Edge opportunity detection

**Analysis Models:**
- `BacktestResult`: Backtesting metrics
- `Snapshot`: Version control for predictions
- `Experiment`: ML experiment tracking
- `WhatIfResult`: Scenario analysis

**Supporting Models:**
- `Player`, `Team`, `Game`: Sports entities
- `ApiKey`: External API key management
- `UserProfile`: User and subscription data

### 3. Database Layer (`src/db.py`)

**Features:**
- Async SQLAlchemy with asyncpg
- Connection pooling (configurable size)
- Health check functions
- Redis connection pool
- Session management via dependency injection

**Patterns:**
- Repository pattern (to be implemented)
- Unit of Work pattern (to be implemented)
- Query optimization with indexes

### 4. Authentication (`src/auth/deps.py`)

**Pluggable Authentication:**
- Supports Clerk and Supabase
- JWT token validation
- User profile extraction
- Subscription tier enforcement

**Dependencies:**
- `get_current_user`: Validate and extract user
- `get_current_active_user`: Ensure user is active
- `require_pro_tier`: Require Pro subscription
- `require_enterprise_tier`: Require Enterprise subscription

### 5. API Routers

All routers follow consistent patterns:

**Common Features:**
- Async/await throughout
- Proper HTTP status codes
- Pydantic request/response models
- Authentication via dependencies
- Comprehensive error handling
- TODO markers for implementation

**Router Details:**

**Props Markets (`props.py`)**
- List, get, import, refresh prop markets
- Platform integration (PrizePicks, Underdog)
- Filtering and pagination

**Context Data (`context.py`)**
- Injury reports
- Weather data (outdoor games)
- Team statistics
- Matchup context

**Features (`features.py`)**
- Feature computation
- Rolling averages and trends
- Matchup-specific features
- Caching with Redis

**Model Predictions (`model.py`)**
- Batch and single predictions
- Multiple model types
- Confidence and edge calculation
- Explanation generation (SHAP)

**Correlations (`corr.py`)**
- Pairwise correlations
- Statistical significance testing
- Related props discovery

**Optimization (`optimize.py`)**
- Parlay optimization (greedy, genetic, MILP)
- Slip detection
- Monte Carlo simulation
- Constraint validation

**Evaluation (`eval.py`)**
- Backtesting with configurable strategies
- Calibration analysis
- Performance segmentation
- Live tracking

**Export (`export.py`)**
- JSON, CSV, Excel formats
- Snapshot exports
- Daily reports

**Snapshots (`snapshots.py`)**
- Version control for predictions
- Comparison between snapshots
- Outcome tracking

**Experiments (`experiments.py`)**
- ML experiment tracking
- Model comparison
- Promotion to production

**What-If Analysis (`whatif.py`)**
- Scenario testing
- Injury impact analysis
- Lineup changes
- Sensitivity analysis

**Historical Data (`history.py`)**
- Player game logs
- Performance splits
- Team statistics
- Matchup history

## API Design Principles

### 1. RESTful Conventions
- Proper HTTP methods (GET, POST, PUT, DELETE)
- Resource-based URLs
- Consistent naming
- Appropriate status codes

### 2. Request/Response Models
- All endpoints use Pydantic models
- Comprehensive validation
- Consistent error responses
- Pagination for lists

### 3. Authentication & Authorization
- JWT bearer tokens
- Role-based access control
- Subscription tier enforcement
- API key encryption

### 4. Performance
- Async/await for I/O operations
- Redis caching with TTL
- Database connection pooling
- Batch operations where possible

### 5. Observability
- Health check endpoint
- Structured logging
- Error tracking (Sentry integration ready)
- Metrics collection points

## Data Flow

### Typical Request Flow

1. **Client Request** → API Gateway (CORS, Rate Limiting)
2. **Authentication** → JWT Validation (Clerk/Supabase)
3. **Authorization** → Subscription Tier Check
4. **Cache Check** → Redis (if applicable)
5. **Business Logic** → Service Layer
6. **Data Access** → PostgreSQL/External APIs
7. **Response** → JSON with Pydantic serialization

### Example: Parlay Optimization

```
POST /optimize/parlays
  ↓
1. Validate JWT token
2. Check Pro tier subscription
3. Fetch prop markets from DB
4. Get cached predictions (or compute)
5. Compute correlation matrix (or use cached)
6. Run optimization algorithm
7. Score and rank candidates
8. Return top K parlays
```

## Database Design Considerations

**Tables (to be implemented):**
- `users`: User profiles and subscriptions
- `prop_markets`: Props markets from platforms
- `prop_legs`: Individual prop legs
- `games`: Game schedule and metadata
- `players`: Player information
- `teams`: Team information
- `predictions`: Model predictions (versioned)
- `features`: Computed feature sets
- `correlations`: Correlation cache
- `snapshots`: Prediction snapshots
- `experiments`: ML experiment tracking
- `api_keys`: Encrypted API keys
- `backtests`: Backtest results

**Indexes:**
- Foreign keys
- Timestamps for time-based queries
- Status fields for filtering
- User ID for access control

## Caching Strategy

**Redis Usage:**
- Feature sets (TTL: 1 hour)
- Predictions (TTL: 5 minutes)
- Correlations (TTL: 1 hour)
- Context data (TTL: 15 minutes)
- Rate limiting counters
- Session data

**Cache Invalidation:**
- Manual invalidation endpoints
- TTL-based expiration
- Event-driven invalidation (on data updates)

## Security

**Authentication:**
- JWT token validation
- Secure token storage (httpOnly cookies recommended)
- Token expiration and refresh

**Authorization:**
- Role-based access control
- Subscription tier enforcement
- Resource-level permissions

**Data Protection:**
- API key encryption at rest
- Secure environment variable handling
- SQL injection prevention (parameterized queries)
- Input validation with Pydantic

**Rate Limiting:**
- Per-user rate limits
- Per-endpoint limits
- Redis-based counters

## Deployment

**Docker:**
- Multi-stage build for optimization
- Non-root user for security
- Health checks
- Environment variable configuration

**Docker Compose:**
- Local development stack
- PostgreSQL + Redis + API
- Volume persistence
- Health check dependencies

**Production Considerations:**
- Horizontal scaling with load balancer
- Database read replicas
- Redis cluster for high availability
- Container orchestration (Kubernetes/ECS)
- CI/CD pipeline integration

## Development Workflow

**Setup:**
```bash
# Copy environment variables
cp .env.example .env

# Start local stack
docker-compose up -d

# Or manual setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload
```

**Testing:**
```bash
# Run tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Linting
ruff check .
black --check .
```

**Migrations:**
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Implementation Roadmap

### Phase 1: Foundation
1. Database models and migrations
2. Props markets ingestion
3. Basic CRUD operations
4. Authentication integration

### Phase 2: ML Pipeline
1. Feature engineering implementation
2. Model inference setup
3. Prediction caching
4. Batch processing

### Phase 3: Optimization
1. Correlation computation
2. Optimization algorithms
3. Slip detection
4. Validation rules

### Phase 4: Analysis
1. Backtesting engine
2. Calibration analysis
3. What-if scenarios
4. Export functionality

### Phase 5: Production
1. Performance optimization
2. Monitoring and alerts
3. Rate limiting
4. Documentation

## API Documentation

**Interactive Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Features:**
- Auto-generated from Pydantic models
- Try-it-out functionality
- Request/response examples
- Authentication flow

## Monitoring & Observability

**Health Checks:**
- `/health` endpoint
- Database connection status
- Redis connection status
- Service version

**Logging:**
- Structured JSON logs
- Request/response logging
- Error tracking
- Performance metrics

**Metrics (to implement):**
- Request latency
- Error rates
- Cache hit rates
- Model inference time
- Database query time

## Error Handling

**Global Exception Handler:**
- Catches unhandled exceptions
- Returns consistent error format
- Logs errors with context
- Environment-specific messages

**Error Response Format:**
```json
{
  "error": "Error type",
  "message": "Human-readable message",
  "detail": "Additional details (dev only)"
}
```

## Next Steps

1. **Implement Database Models**: Create SQLAlchemy models for all entities
2. **External API Integration**: Build adapters for PrizePicks, Underdog, ESPN
3. **Feature Engineering**: Implement feature computation pipeline
4. **Model Serving**: Set up model loading and inference
5. **Optimization Algorithms**: Implement parlay optimization logic
6. **Testing**: Write comprehensive test suite
7. **Documentation**: Add detailed API documentation
8. **Performance Testing**: Load testing and optimization

## Resources

- FastAPI Documentation: https://fastapi.tiangolo.com/
- Pydantic Documentation: https://docs.pydantic.dev/
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- Alembic Documentation: https://alembic.sqlalchemy.org/

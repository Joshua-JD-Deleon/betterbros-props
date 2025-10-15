# BetterBros Props API

AI-powered props betting optimization platform backend API built with FastAPI.

## Features

- **Props Markets**: Fetch and manage prop markets from PrizePicks, Underdog, etc.
- **ML Predictions**: Generate predictions with multiple model types (XGBoost, LightGBM, Neural Networks)
- **Context Data**: Incorporate injuries, weather, team stats, and more
- **Feature Engineering**: Automated feature computation with caching
- **Correlations**: Calculate prop leg correlations for risk management
- **Optimization**: Build optimal parlays with configurable constraints
- **Backtesting**: Evaluate strategies with historical data
- **What-If Analysis**: Scenario testing and sensitivity analysis
- **Snapshots**: Version control for predictions and analysis
- **Experiments**: Track and compare ML experiments

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+

### Installation

1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run database migrations:
   ```bash
   alembic upgrade head
   ```

6. Start the server:
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at `http://localhost:8000`

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
apps/api/
├── main.py                 # FastAPI application entry point
├── alembic/               # Database migrations
│   ├── env.py
│   └── versions/
├── src/
│   ├── config.py          # Configuration management
│   ├── types.py           # Pydantic models
│   ├── db.py              # Database setup
│   ├── auth/
│   │   └── deps.py        # Authentication dependencies
│   └── routers/           # API endpoints
│       ├── props.py       # Props markets
│       ├── context.py     # Context data
│       ├── features.py    # Feature engineering
│       ├── model.py       # ML predictions
│       ├── corr.py        # Correlations
│       ├── optimize.py    # Parlay optimization
│       ├── eval.py        # Backtesting
│       ├── export.py      # Data export
│       ├── snapshots.py   # Snapshots
│       ├── experiments.py # ML experiments
│       ├── keys.py        # API keys management
│       ├── whatif.py      # What-if analysis
│       ├── history.py     # Historical data
│       └── auth.py        # Authentication
├── requirements.txt
├── alembic.ini
└── .env.example
```

## Authentication

The API supports two authentication providers:

### Clerk

Set in `.env`:
```
AUTH_PROVIDER=clerk
CLERK_SECRET_KEY=your_clerk_secret_key
CLERK_JWT_ISSUER=https://your-app.clerk.accounts.dev
```

### Supabase

Set in `.env`:
```
AUTH_PROVIDER=supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_JWT_SECRET=your_supabase_jwt_secret
```

## Key Endpoints

### Props Markets
- `GET /props` - List prop markets
- `POST /props/import` - Import markets from platforms
- `POST /props/refresh` - Refresh markets

### Predictions
- `POST /model/predict` - Generate predictions
- `POST /model/batch` - Batch predictions
- `POST /model/explain/{prop_leg_id}` - Explain prediction

### Optimization
- `POST /optimize/parlays` - Optimize parlay combinations
- `POST /optimize/slips` - Detect edge opportunities
- `POST /optimize/validate-parlay` - Validate parlay

### Backtesting
- `POST /eval/backtest` - Run backtest
- `POST /eval/calibration` - Evaluate calibration
- `GET /eval/live-tracking` - Track live performance

### What-If Analysis
- `POST /whatif` - Run scenario analysis
- `POST /whatif/injury-impact` - Analyze injury impact
- `POST /whatif/lineup-change` - Analyze lineup changes

## Environment Variables

See `.env.example` for full list of configuration options.

### Required
- `AUTH_PROVIDER` - Authentication provider (clerk/supabase)
- `DATABASE_URL` - PostgreSQL connection URL
- `REDIS_URL` - Redis connection URL

### Optional
- External API keys for data sources
- Model configuration
- Rate limiting settings
- Monitoring integration (Sentry)

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
ruff check . --fix
```

### Database Migrations

Create new migration:
```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback:
```bash
alembic downgrade -1
```

## Health Check

Check API health:
```bash
curl http://localhost:8000/health
```

Response includes database and Redis connection status.

## TODOs

All endpoints currently return stub responses marked with `TODO: Implementation`.

Priority implementation order:
1. Database models and migrations
2. Props markets ingestion
3. Feature engineering pipeline
4. Model inference
5. Optimization algorithms
6. Backtesting engine

## License

Proprietary - BetterBros

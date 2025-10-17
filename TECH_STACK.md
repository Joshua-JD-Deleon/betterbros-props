# BetterBros Bets - Tech Stack & Value Summary

## Frontend Stack

- **Framework**: Next.js 15 (App Router) with React 18
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS with shadcn/ui component library
- **Animations**: Framer Motion for smooth UI transitions
- **State Management**: Zustand for client-side state (bet slip management)
- **Development Server**: Running on localhost:3001

## Backend Stack (FastAPI + Python)

- **API Framework**: FastAPI 0.109 (async, high performance)
- **Database**: PostgreSQL 14+ with SQLAlchemy 2.0 (async ORM)
- **Cache Layer**: Redis 5.0 with async client
- **Authentication**: JWT with Clerk/Supabase integration
- **Migrations**: Alembic for schema management

## Advanced Statistical & ML Methods

### 1. Machine Learning Models

#### Bayesian Hierarchical Model (`models/bayes.py`)
- **Framework**: PyMC (probabilistic programming)
- **Method**: MCMC sampling with NUTS algorithm
- **Features**:
  - Player-level random effects (individual skill modeling)
  - League-level feature coefficients
  - Full posterior distributions for uncertainty quantification
  - Convergence diagnostics (R-hat, ESS, divergences)
  - 95% and 67% credible intervals
  - Handles unseen players via population hyperprior

#### Gradient Boosting Models (`models/gbm.py`)
- **Frameworks**: XGBoost 2.0.3 + LightGBM 4.2.0
- **Features**:
  - Tree-based ensemble learning
  - Handles non-linear relationships
  - Built-in feature importance
  - Fast prediction at scale

#### Ensemble Predictor (`models/ensemble.py`)
- **Method**: Weighted ensemble combining Bayesian + GBM
- **Features**:
  - Learned ensemble weights via grid search
  - Model disagreement as additional uncertainty
  - SHAP-based feature attribution for interpretability
  - Confidence intervals from Bayesian posterior
  - Edge calculation for betting decisions

### 2. Correlation & Copula Modeling (`corr/copula.py`)

- **Methods**: Gaussian, t-copula, Clayton, Frank copulas
- **Purpose**: Model joint distributions of correlated prop outcomes
- **Uses**:
  - Monte Carlo simulation with proper correlation structure
  - Multi-prop parlay analysis
  - Portfolio-level risk assessment

### 3. Monte Carlo Simulation (`optimize/monte_carlo.py`)

- **Features**:
  - 10,000+ simulation runs per slip
  - Correlated sampling via Gaussian copula
  - Risk metrics: VaR, CVaR, variance
  - Stress testing with probability adjustments
  - Portfolio-level EV and variance calculation

### 4. Advanced Feature Engineering (`features/pipeline.py`)

**50-100+ Features Per Prop Including:**

#### Player Features
- Rolling averages (3, 5, 10 game windows)
- Season/career statistics
- Home/away splits
- Usage rate & target share
- Injury status encoding
- Days rest calculations

#### Matchup Features
- Opponent defensive rankings
- Pace-adjusted metrics
- Historical matchup performance
- Defensive yards allowed

#### Contextual Features
- Venue type (dome/outdoor/altitude)
- Weather conditions (temp, wind, precipitation)
- Game totals & spreads
- Primetime game indicators

#### Market Features
- Line movement tracking
- Implied probability from odds
- Multi-book consensus
- Line vs. baseline deviation

#### Derived Features
- EWMA trend indicators
- Volatility metrics (CV)
- Ceiling/floor scores (percentiles)
- Pace-adjusted performance
- Rest advantage calculations
- Weather impact modeling

### 5. Model Calibration & Monitoring (`eval/calibration_monitor.py`)

- **Metrics**:
  - Expected Calibration Error (ECE)
  - Brier score
  - Maximum Calibration Error (MCE)
- **Features**:
  - Rolling window calibration checking
  - Degradation detection with warning/critical thresholds
  - Trend analysis (improving/stable/degrading)
  - Automated recalibration recommendations
  - Historical calibration storage

### 6. Bankroll Optimization (`optimize/kelly.py`)

- **Method**: Kelly Criterion with fractional Kelly (default 0.25)
- **Formulas**:
  - Classic Kelly: `f* = (p*b - q) / b`
  - Variance-based Kelly: `f* = edge / variance`
- **Features**:
  - Min/max stake clamping ($5-$50)
  - Maximum bankroll fraction limits (10%)
  - Minimum edge thresholds (1%)
  - Multi-bet allocation strategies:
    - Equal Kelly (independent)
    - Scaled Kelly (total < max)
    - Priority-based (EV-ranked sequential)

### 7. Statistical Libraries

- **Core**: NumPy 1.26, Pandas 2.1, SciPy 1.11
- **ML**: scikit-learn 1.4, statsmodels 0.14
- **Advanced**: PyMC 5.10 (Bayesian), Copulas 0.10 (multivariate)
- **Interpretability**: SHAP 0.44 (Shapley values)

## Data Ingestion

- **Sleeper API**: Player data, stats, rosters
- **Injuries API**: Real-time injury updates
- **Weather API**: Game-day conditions
- **Baseline Stats**: Historical performance baselines

## Key Value Propositions

### 1. Sophisticated Quantitative Foundation

- Combines frequentist (GBM) and Bayesian approaches for robust predictions
- Full uncertainty quantification (not just point estimates)
- Proper correlation modeling for multi-leg parlays

### 2. Advanced Risk Management

- Kelly Criterion for mathematically optimal stake sizing
- Monte Carlo simulation with 10K+ samples
- VaR and CVaR for downside risk assessment
- Calibration monitoring prevents model degradation

### 3. Interpretability & Trust

- SHAP values explain every prediction
- Feature importance rankings
- Confidence intervals on all predictions
- Transparent model versioning

### 4. Production-Ready Architecture

- Async/await throughout (FastAPI + SQLAlchemy)
- Redis caching (12hr TTL on features)
- Temporal leakage detection
- Comprehensive health checks

### 5. Comprehensive Feature Set

- 50-100 features per prop
- Multi-source data aggregation
- Contextual enrichment (weather, injuries, venue)
- Market-aware (line movement, consensus)

## Current Development Status

- ✅ **Frontend**: Fully implemented with modern Next.js 15 + Tailwind
- ✅ **Backend ML Core**: Complete with Bayesian, GBM, ensemble, copulas
- ✅ **Feature Engineering**: 50-100 feature pipeline with contextual enrichment
- ✅ **Optimization**: Kelly criterion, Monte Carlo, slip optimization
- ✅ **Monitoring**: Calibration tracking, degradation detection
- ⏳ **Data Pipeline**: Ingest layer built, needs real API keys
- ⏳ **Database**: Schema ready, Docker setup available
- ⏳ **Testing**: Currently using mock data for UI development

## Technical Differentiation

Most betting tools use simple odds calculators or basic probability models.

**BetterBros employs institutional-grade quantitative finance techniques:**

- **Hierarchical Bayesian models** (similar to sports analytics research)
- **Copula-based correlation modeling** (from quantitative finance)
- **Kelly Criterion** (optimal growth theory from information theory)
- **SHAP interpretability** (cutting-edge ML explainability)
- **Calibration monitoring** (production ML best practices)

This is the kind of infrastructure typically found at professional sports betting syndicates, now accessible for individual bettors.

---

## Current Stack Status

The app is currently **UI-ready with mock data** and needs either Docker installation for full backend or can continue testing with the mock data already integrated into the components.

### Running Services

When fully deployed:
- **Web**: http://localhost:3001 (Next.js)
- **API**: http://localhost:8000 (FastAPI)
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Database**: PostgreSQL on port 5432
- **Cache**: Redis on port 6379

### Docker Commands

Start all backend services:
```bash
cd infra
docker-compose -f docker-compose.backend.yml up -d
```

Stop all services:
```bash
cd infra
docker-compose -f docker-compose.backend.yml down
```

Check service health:
```bash
docker ps
docker logs betterbros-api
```

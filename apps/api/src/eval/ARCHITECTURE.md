# Evaluation System Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Evaluation System                             │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Backtest    │  │ Calibration  │  │   Metrics    │          │
│  │   Engine     │  │   Monitor    │  │ Calculator   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                  │
│         └──────────────────┴──────────────────┘                  │
│                            │                                     │
│                    ┌───────┴────────┐                           │
│                    │     Reports    │                           │
│                    │    Generator   │                           │
│                    └────────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │
        ┌────────────────────┴─────────────────────┐
        │                                           │
   ┌────┴─────┐                              ┌─────┴──────┐
   │ Database │                              │   Models   │
   │          │                              │            │
   │ - Experiments                           │ - Ensemble │
   │ - PropMarkets                           │ - GBM      │
   │ - Snapshots                             │ - Bayesian │
   └──────────┘                              └────────────┘
```

## Component Architecture

### 1. BacktestEngine

```
┌─────────────────────────────────────────┐
│         BacktestEngine                  │
├─────────────────────────────────────────┤
│                                         │
│  Input:                                 │
│    - weeks: List[int]                   │
│    - league: str                        │
│    - model: EnsemblePredictor           │
│    - risk_mode: str                     │
│                                         │
│  Process:                               │
│    1. Load props from database          │
│    2. Generate predictions              │
│    3. Simulate betting (Kelly sizing)   │
│    4. Track bankroll                    │
│    5. Calculate metrics                 │
│    6. Generate calibration plots        │
│                                         │
│  Output:                                │
│    - overall_metrics                    │
│    - weekly_summary                     │
│    - bankroll_history                   │
│    - calibration_plot                   │
│                                         │
└─────────────────────────────────────────┘
        │
        ├─► MetricsCalculator
        ├─► CalibrationMonitor
        └─► Database (Experiments table)
```

### 2. CalibrationMonitor

```
┌─────────────────────────────────────────┐
│      CalibrationMonitor                 │
├─────────────────────────────────────────┤
│                                         │
│  Input:                                 │
│    - predictions: List[float]           │
│    - outcomes: List[bool]               │
│    - window: int                        │
│                                         │
│  Process:                               │
│    1. Rolling window selection          │
│    2. Compute ECE, Brier, MCE          │
│    3. Detect degradation                │
│    4. Analyze trend                     │
│    5. Generate recommendations          │
│                                         │
│  Output:                                │
│    - calibration_metrics                │
│    - degradation_status                 │
│    - trend_analysis                     │
│    - recommendations                    │
│                                         │
│  State:                                 │
│    - calibration_history                │
│    - db_session                         │
│                                         │
└─────────────────────────────────────────┘
```

### 3. MetricsCalculator

```
┌─────────────────────────────────────────┐
│       MetricsCalculator                 │
├─────────────────────────────────────────┤
│                                         │
│  ROI Metrics:                           │
│    ├─ Total profit/loss                 │
│    ├─ ROI percentage                    │
│    ├─ Final bankroll                    │
│    └─ Number of bets                    │
│                                         │
│  Risk Metrics:                          │
│    ├─ Sharpe ratio                      │
│    ├─ Max drawdown                      │
│    ├─ Recovery rate                     │
│    └─ Volatility                        │
│                                         │
│  Calibration Metrics:                   │
│    ├─ ECE                               │
│    ├─ Brier score                       │
│    └─ MCE                               │
│                                         │
│  Win Rate Analysis:                     │
│    ├─ Overall win rate                  │
│    ├─ By confidence level               │
│    └─ Confidence bands                  │
│                                         │
│  Bet Sizing:                            │
│    └─ Kelly fraction                    │
│                                         │
└─────────────────────────────────────────┘
```

### 4. ReportGenerator

```
┌─────────────────────────────────────────┐
│        ReportGenerator                  │
├─────────────────────────────────────────┤
│                                         │
│  Report Types:                          │
│    ├─ Weekly Report (Markdown)          │
│    ├─ Calibration Report (Markdown)     │
│    ├─ CSV Export                        │
│    └─ Multi-week Summary                │
│                                         │
│  Sections:                              │
│    ├─ Executive Summary                 │
│    ├─ ROI Analysis                      │
│    ├─ Risk Analysis                     │
│    ├─ Calibration Quality               │
│    ├─ Win Rate Breakdown                │
│    └─ Recommendations                   │
│                                         │
│  Outputs:                               │
│    ├─ Markdown files                    │
│    ├─ CSV files                         │
│    └─ Summary tables                    │
│                                         │
└─────────────────────────────────────────┘
```

## Data Flow

### Backtest Workflow

```
Start
  │
  ├─► Load Props from Database
  │     │
  │     └─► PropMarket table (week, league)
  │
  ├─► Generate Predictions
  │     │
  │     └─► EnsemblePredictor (features → p_hit)
  │
  ├─► Simulate Betting
  │     │
  │     ├─► Calculate Kelly fraction
  │     ├─► Apply risk mode constraints
  │     ├─► Execute bets
  │     └─► Update bankroll
  │
  ├─► Calculate Metrics
  │     │
  │     ├─► ROI metrics
  │     ├─► Sharpe ratio
  │     ├─► Max drawdown
  │     └─► Calibration metrics
  │
  ├─► Generate Reports
  │     │
  │     └─► Weekly report (markdown)
  │
  └─► Save to Database
        │
        └─► Experiments table
```

### Calibration Monitoring Workflow

```
Start
  │
  ├─► Collect Predictions & Outcomes
  │
  ├─► Apply Rolling Window
  │     │
  │     └─► Most recent N samples
  │
  ├─► Compute Calibration Metrics
  │     │
  │     ├─► ECE (binned accuracy vs confidence)
  │     ├─► Brier score (MSE of probabilities)
  │     └─► MCE (max error across bins)
  │
  ├─► Detect Degradation
  │     │
  │     ├─► Compare vs thresholds
  │     ├─► Classify severity
  │     └─► Generate recommendations
  │
  ├─► Analyze Trend
  │     │
  │     └─► Linear regression on recent history
  │
  ├─► Update History
  │     │
  │     └─► Append to calibration_history
  │
  └─► Store in Database (optional)
        │
        └─► Experiments table (calibration_check)
```

## Risk Mode Decision Tree

```
                    Risk Mode Selection
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   Conservative        Balanced          Aggressive
        │                  │                  │
    ┌───┴───┐          ┌───┴───┐         ┌───┴───┐
    │       │          │       │         │       │
  1/8 K   5% max    1/4 K   10% max   1/2 K   15% max
    │       │          │       │         │       │
  p≥0.65  Low risk  p≥0.60  Medium    p≥0.55  High risk
                            risk

K = Kelly fraction
max = Maximum bet as % of bankroll
p = Minimum confidence threshold
```

## Metric Calculation Pipeline

```
Bet Slips
    │
    ├─► ROI Pipeline
    │     │
    │     ├─► Sum stakes
    │     ├─► Sum payouts
    │     └─► Calculate ROI = (profit / initial) × 100
    │
    ├─► Returns Pipeline
    │     │
    │     ├─► Calculate per-bet returns
    │     ├─► Mean(returns)
    │     └─► Std(returns)
    │           │
    │           └─► Sharpe = Mean / Std
    │
    ├─► Drawdown Pipeline
    │     │
    │     ├─► Build bankroll history
    │     ├─► Compute running max
    │     ├─► Find max (peak - current) / peak
    │     └─► Calculate recovery rate
    │
    └─► Calibration Pipeline
          │
          ├─► ECE = Σ |accuracy_bin - confidence_bin| × (n_bin / n_total)
          ├─► Brier = Mean((prediction - outcome)²)
          └─► MCE = Max |accuracy_bin - confidence_bin|
```

## Database Schema Integration

```
┌─────────────────────────────────────────────────────────┐
│                    experiments                          │
├─────────────────────────────────────────────────────────┤
│ id              UUID (PK)                               │
│ user_id         UUID (FK → users.id)                    │
│ snapshot_id     UUID (FK → snapshots.id, nullable)      │
│ timestamp       TIMESTAMP WITH TIMEZONE                 │
│ week            INTEGER                                 │
│ league          VARCHAR(50)                             │
│ risk_mode       VARCHAR(50)  ← "balanced", etc.         │
│ bankroll        FLOAT        ← Initial bankroll         │
│ num_props       INTEGER                                 │
│ num_slips       INTEGER                                 │
│ metrics         JSONB        ← All calculated metrics   │
│   ├─ roi_metrics                                        │
│   ├─ sharpe_ratio                                       │
│   ├─ drawdown                                           │
│   ├─ calibration                                        │
│   ├─ win_rate                                           │
│   └─ backtest_config                                    │
│ name            VARCHAR(255)                            │
│ description     TEXT                                    │
│ status          VARCHAR(50)  ← "completed", "running"   │
│ created_at      TIMESTAMP WITH TIMEZONE                 │
└─────────────────────────────────────────────────────────┘
```

## Error Handling Strategy

```
Try-Catch Hierarchy:

1. Database Operations
   ├─ Rollback on error
   ├─ Log error details
   └─ Return empty/default values

2. Prediction Generation
   ├─ Fallback to mock predictions
   ├─ Log warning
   └─ Continue backtest

3. Metrics Calculation
   ├─ Return partial results
   ├─ Log which metric failed
   └─ Include error in report

4. Report Generation
   ├─ Generate text report even if plots fail
   └─ Log warning about missing visualizations
```

## Performance Optimization

```
Optimization Techniques:

1. Database
   ├─ Use async operations
   ├─ Batch queries where possible
   ├─ Index on week, league, user_id
   └─ Connection pooling

2. Numpy Operations
   ├─ Vectorized calculations
   ├─ Pre-allocate arrays
   └─ Avoid Python loops

3. Memory Management
   ├─ Stream large datasets
   ├─ Clear plots after encoding
   └─ Garbage collection for long-running backtests

4. Caching
   ├─ Cache model predictions (optional)
   ├─ Cache calibration computations
   └─ Cache report templates
```

## Testing Strategy

```
Testing Pyramid:

Unit Tests (70%)
├─ Metrics calculation
├─ Calibration computation
├─ Kelly sizing
├─ Degradation detection
└─ Report formatting

Integration Tests (20%)
├─ Database operations
├─ Multi-week backtests
├─ End-to-end workflow
└─ Model integration

System Tests (10%)
├─ Performance under load
├─ Memory usage
└─ Concurrent backtests
```

## Deployment Considerations

```
Production Checklist:

✓ Environment Variables
  ├─ DATABASE_URL
  ├─ REDIS_URL
  └─ OUTPUT_DIRECTORY

✓ Dependencies
  ├─ numpy
  ├─ pandas
  ├─ scikit-learn
  ├─ sqlalchemy
  └─ matplotlib (optional)

✓ Database Migrations
  └─ Experiments table ready

✓ Monitoring
  ├─ Log aggregation
  ├─ Error tracking
  └─ Performance metrics

✓ Scaling
  ├─ Async operations
  ├─ Connection pooling
  └─ Horizontal scaling ready
```

## Future Architecture

```
Planned Enhancements:

1. Real-time Dashboard
   ├─ WebSocket updates
   ├─ Live calibration monitoring
   └─ Interactive charts

2. Distributed Backtesting
   ├─ Task queue (Celery)
   ├─ Parallel week processing
   └─ Result aggregation

3. ML-Driven Risk Management
   ├─ Dynamic Kelly adjustment
   ├─ Portfolio optimization
   └─ Automated rebalancing

4. Advanced Analytics
   ├─ Monte Carlo simulation
   ├─ Scenario analysis
   └─ Sensitivity testing
```

---

**Architecture Version:** 1.0.0
**Last Updated:** 2025-10-14
**Status:** Production Ready

# Quick Reference Guide - Evaluation System

## File Structure

```
/Users/joshuadeleon/BetterBros Bets/apps/api/src/eval/
├── __init__.py                   (1.4KB) - Package exports
├── backtest.py                   (18KB)  - Backtesting engine
├── calibration_monitor.py        (15KB)  - Calibration tracking
├── metrics.py                    (14KB)  - Metrics calculation
├── reports.py                    (16KB)  - Report generation
├── example_usage.py              (10KB)  - Usage examples
├── test_imports.py               (4KB)   - Import tests
├── README.md                     (12KB)  - Full documentation
├── ARCHITECTURE.md               (17KB)  - System architecture
├── IMPLEMENTATION_SUMMARY.md     (10KB)  - Implementation details
└── QUICK_REFERENCE.md            (this file)
```

## 1-Minute Quick Start

```python
from src.eval import BacktestEngine, CalibrationMonitor
from src.db import get_db_session

# Run a backtest
async with get_db_session() as db:
    engine = BacktestEngine(db_session=db, risk_mode="balanced")
    results = await engine.run_backtest(weeks=[1,2,3], league="NFL")
    print(f"ROI: {results['overall_metrics']['roi_metrics']['roi']:.2f}%")
```

## Common Operations

### Run Backtest (Conservative)
```python
engine = BacktestEngine(
    db_session=db,
    initial_bankroll=1000.0,
    risk_mode="conservative"
)
results = await engine.run_backtest(weeks=[1, 2, 3], league="NFL")
```

### Check Calibration
```python
monitor = CalibrationMonitor(db_session=db)
metrics = monitor.check_calibration(predictions, outcomes, window=500)
status = monitor.get_calibration_status()
print(f"Status: {status['status']}, Trend: {status['trend']}")
```

### Calculate ROI
```python
calculator = MetricsCalculator()
roi = calculator.calculate_roi(slips, initial_bankroll=1000.0)
print(f"ROI: {roi['roi']:.2f}%, Profit: ${roi['total_profit']:.2f}")
```

### Generate Report
```python
generator = ReportGenerator(output_dir="./reports")
report = generator.generate_weekly_report(week=5, league="NFL", metrics=results)
filepath = generator.save_report(report, "week5_report.md")
```

## Key Metrics at a Glance

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| **ROI** | > 10% | 5-10% | < 5% |
| **Sharpe** | > 2.0 | 1.0-2.0 | < 1.0 |
| **ECE** | < 0.05 | 0.05-0.08 | > 0.08 |
| **Brier** | < 0.20 | 0.20-0.22 | > 0.22 |
| **Max DD** | < 15% | 15-30% | > 30% |
| **Win Rate** | > 60% | 50-60% | < 50% |

## Risk Modes

| Mode | Kelly | Max Bet | Min Conf | Use Case |
|------|-------|---------|----------|----------|
| **Conservative** | 1/8 | 5% | 0.65 | New users, uncertain models |
| **Balanced** | 1/4 | 10% | 0.60 | Default, proven models |
| **Aggressive** | 1/2 | 15% | 0.55 | High confidence, experts |

## Backtest Results Structure

```python
{
    "backtest_summary": {
        "weeks": [1, 2, 3],
        "league": "NFL",
        "risk_mode": "balanced",
        "initial_bankroll": 1000.0,
        "final_bankroll": 1155.0,
        "total_profit": 155.0,
        "total_bets": 125
    },
    "overall_metrics": {
        "roi_metrics": {...},
        "sharpe_ratio": 1.85,
        "drawdown": {...},
        "calibration": {...},
        "win_rate": 0.68
    },
    "weekly_summary": [...],
    "bankroll_history": [1000, 1025, 1050, ...],
    "calibration_plot": "base64_png..."
}
```

## Calibration Status Response

```python
{
    "status": "good",           # good, warning, critical
    "ece": 0.045,
    "brier": 0.185,
    "mce": 0.082,
    "trend": "stable",          # improving, stable, degrading
    "last_check": datetime(...),
    "history_length": 15,
    "is_degraded": False
}
```

## Common Workflows

### Weekly Backtest Workflow
```python
# 1. Initialize
engine = BacktestEngine(db_session=db, risk_mode="balanced")

# 2. Run backtest
results = await engine.run_backtest(weeks=[5], league="NFL")

# 3. Generate report
generator = ReportGenerator()
report = generator.generate_weekly_report(
    week=5, league="NFL", metrics=results['overall_metrics']
)

# 4. Save report
generator.save_report(report, f"week5_report_{datetime.now():%Y%m%d}.md")

# 5. Check calibration
monitor = CalibrationMonitor(db_session=db)
status = monitor.get_calibration_status()

# 6. Alert if degraded
if status['is_degraded']:
    print(f"ALERT: Calibration {status['status']}")
```

### Multi-Week Comparison
```python
results_by_mode = {}
for mode in ["conservative", "balanced", "aggressive"]:
    engine = BacktestEngine(db_session=db, risk_mode=mode)
    results = await engine.run_backtest(weeks=[1,2,3], league="NFL")
    results_by_mode[mode] = results

# Compare
for mode, results in results_by_mode.items():
    roi = results['overall_metrics']['roi_metrics']['roi']
    sharpe = results['overall_metrics']['sharpe_ratio']
    print(f"{mode}: ROI={roi:.1f}%, Sharpe={sharpe:.2f}")
```

### Calibration Monitoring Loop
```python
monitor = CalibrationMonitor(db_session=db)

while True:
    # Get recent predictions
    predictions, outcomes = get_recent_predictions(window=500)

    # Check calibration
    metrics = monitor.check_calibration(predictions, outcomes)

    # Detect degradation
    degradation = monitor.detect_degradation(metrics)

    if degradation['is_degraded']:
        # Send alert
        send_alert(
            severity=degradation['severity'],
            issues=degradation['issues'],
            recommendations=degradation['recommendations']
        )

    await asyncio.sleep(3600)  # Check hourly
```

## Troubleshooting Quick Fixes

### Problem: Negative ROI
```python
# Solution: More conservative
engine = BacktestEngine(risk_mode="conservative")
# Or increase min confidence
# Filter predictions: [p for p in predictions if p >= 0.65]
```

### Problem: High ECE (> 0.08)
```python
# Solution: Recalibrate model
from src.models.calibration import CalibrationPipeline
calibrator = CalibrationPipeline(method="isotonic")
calibrated = calibrator.calibrate_probabilities(y_true, y_pred)
```

### Problem: Large Drawdown
```python
# Solution: Reduce bet sizes
# Switch to conservative mode or reduce max_bet_pct
BacktestEngine.RISK_MODES["balanced"]["max_bet_pct"] = 0.05
```

### Problem: Low Sharpe
```python
# Solution: Filter low-confidence bets
# Only bet when p > 0.65 or use conservative mode
calculator = MetricsCalculator()
kelly = calculator.calculate_kelly_fraction(p_win, odds, kelly_fraction=0.125)
```

## Import Shortcuts

```python
# Full import
from src.eval import (
    BacktestEngine,
    CalibrationMonitor,
    MetricsCalculator,
    ReportGenerator,
)

# Specific imports
from src.eval.backtest import BacktestEngine
from src.eval.calibration_monitor import CalibrationMonitor
from src.eval.metrics import MetricsCalculator
from src.eval.reports import ReportGenerator
```

## Database Queries

### Get Recent Experiments
```python
from sqlalchemy import select
from src.db.models import Experiment

query = select(Experiment).where(
    Experiment.league == "NFL",
    Experiment.week.in_([1, 2, 3])
).order_by(Experiment.timestamp.desc())

result = await db.execute(query)
experiments = result.scalars().all()
```

### Get Calibration History
```python
history = await monitor.get_historical_calibration(
    league="NFL",
    weeks=[1, 2, 3, 4, 5],
    limit=100
)
```

## Environment Setup

```bash
# Install dependencies
pip install numpy pandas scikit-learn sqlalchemy matplotlib

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db"
export REDIS_URL="redis://localhost:6379"
```

## Configuration

```python
# Custom risk mode
BacktestEngine.RISK_MODES["ultra_conservative"] = {
    "kelly_fraction": 0.0625,  # 1/16 Kelly
    "max_bet_pct": 0.03,       # Max 3%
    "min_confidence": 0.70,    # p >= 0.70
}

# Custom thresholds
CalibrationMonitor.ECE_WARNING_THRESHOLD = 0.07
CalibrationMonitor.ECE_CRITICAL_THRESHOLD = 0.09
```

## Output Files

### Weekly Report (Markdown)
```
reports/
└── week5_report_20251014.md
    ├─ Executive Summary
    ├─ ROI Analysis
    ├─ Risk Metrics
    ├─ Calibration Quality
    └─ Recommendations
```

### CSV Export
```python
generator.export_to_csv(
    data=weekly_summaries,
    filepath="backtest_results.csv"
)
# Creates: reports/backtest_results.csv
```

## Performance Tips

1. **Batch Database Queries**: Load all props at once
2. **Use Async Operations**: Leverage async/await
3. **Cache Predictions**: Store intermediate results
4. **Limit History**: Don't store unlimited calibration checks
5. **Cleanup Plots**: Close matplotlib figures after encoding

## Error Handling

```python
try:
    results = await engine.run_backtest(weeks=[1,2,3], league="NFL")
except Exception as e:
    logger.error(f"Backtest failed: {e}")
    # Fallback behavior
    results = {"error": str(e)}
```

## Testing Commands

```bash
# Run import tests
python3 apps/api/src/eval/test_imports.py

# Run example usage
python3 -m src.eval.example_usage

# Check code style
flake8 apps/api/src/eval/

# Type checking
mypy apps/api/src/eval/
```

## Key Functions Reference

| Function | Purpose | Returns |
|----------|---------|---------|
| `run_backtest()` | Simulate betting | Comprehensive results dict |
| `check_calibration()` | Compute calibration metrics | ECE, Brier, MCE |
| `detect_degradation()` | Check if model degraded | Status, issues, recommendations |
| `calculate_roi()` | Compute returns | ROI %, profit, bankroll |
| `calculate_sharpe()` | Risk-adjusted returns | Sharpe ratio |
| `calculate_max_drawdown()` | Worst loss period | Max DD %, recovery rate |
| `generate_weekly_report()` | Create markdown report | Report string |

## Best Practices Summary

1. ✅ Start with conservative risk mode
2. ✅ Backtest 4+ weeks for significance
3. ✅ Monitor calibration every 500 predictions
4. ✅ Recalibrate when ECE > 0.08
5. ✅ Use 1/4 Kelly for safety
6. ✅ Set max drawdown limit at 30%
7. ✅ Review Sharpe ratio, not just ROI
8. ✅ Generate reports for every backtest
9. ✅ Store results in database
10. ✅ Alert on calibration degradation

## Next Steps

1. **Run Your First Backtest**: Use example_usage.py
2. **Review Results**: Check ROI, Sharpe, calibration
3. **Adjust Risk Mode**: Based on results
4. **Set Up Monitoring**: Implement calibration checks
5. **Generate Reports**: Weekly summaries
6. **Integrate with Pipeline**: Connect to production models

---

**For Full Documentation**: See README.md
**For Architecture Details**: See ARCHITECTURE.md
**For Implementation Notes**: See IMPLEMENTATION_SUMMARY.md
**For Examples**: Run example_usage.py

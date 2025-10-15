# Evaluation Module - Backtesting & Calibration Monitoring

Comprehensive evaluation system for betting models with realistic backtesting, calibration monitoring, and performance reporting.

## Overview

The evaluation module provides four main components:

1. **BacktestEngine** - Simulate betting strategies on historical data
2. **CalibrationMonitor** - Track and alert on model calibration degradation
3. **MetricsCalculator** - Calculate performance metrics (ROI, Sharpe, etc.)
4. **ReportGenerator** - Generate markdown and CSV reports

## Installation

```bash
pip install numpy pandas scikit-learn matplotlib sqlalchemy
```

## Quick Start

### Running a Backtest

```python
from src.eval import BacktestEngine
from src.db import get_db_session

async with get_db_session() as db:
    # Initialize engine
    engine = BacktestEngine(
        db_session=db,
        initial_bankroll=1000.0,
        risk_mode="balanced"  # conservative, balanced, aggressive
    )

    # Run backtest
    results = await engine.run_backtest(
        weeks=[1, 2, 3, 4, 5],
        league="NFL",
        user_id="user_123",
        save_to_db=True
    )

    # Access results
    print(f"ROI: {results['overall_metrics']['roi_metrics']['roi']:.2f}%")
    print(f"Sharpe: {results['overall_metrics']['sharpe_ratio']:.2f}")
    print(f"Win Rate: {results['overall_metrics']['win_rate'] * 100:.1f}%")
```

### Monitoring Calibration

```python
from src.eval import CalibrationMonitor

monitor = CalibrationMonitor(db_session=db)

# Check calibration on recent predictions
metrics = monitor.check_calibration(
    predictions=predictions,  # List[float]
    outcomes=outcomes,        # List[bool]
    window=500
)

# Detect degradation
degradation = monitor.detect_degradation(metrics)

if degradation['is_degraded']:
    print(f"Status: {degradation['severity']}")
    print(f"Issues: {degradation['issues']}")
    print(f"Recommendations: {degradation['recommendations']}")

# Get overall status
status = monitor.get_calibration_status()
print(f"Status: {status['status']}")
print(f"Trend: {status['trend']}")  # improving, stable, degrading
```

### Calculating Metrics

```python
from src.eval import MetricsCalculator

calculator = MetricsCalculator()

# ROI calculation
roi = calculator.calculate_roi(
    slips=[
        {"stake": 50.0, "payout": 100.0, "won": True},
        {"stake": 75.0, "payout": 0.0, "won": False},
    ],
    initial_bankroll=1000.0
)

# Sharpe ratio
returns, bankroll_history = calculator.calculate_returns_series(slips)
sharpe = calculator.calculate_sharpe(returns)

# Drawdown analysis
drawdown = calculator.calculate_max_drawdown(bankroll_history)

# Win rate by confidence
win_rates = calculator.calculate_win_rate_by_confidence(
    predictions=[0.75, 0.55, 0.85],
    outcomes=[True, False, True],
    confidence_thresholds=[0.5, 0.6, 0.7, 0.8]
)
```

### Generating Reports

```python
from src.eval import ReportGenerator

generator = ReportGenerator(output_dir="./reports")

# Weekly report
report = generator.generate_weekly_report(
    week=5,
    league="NFL",
    metrics=backtest_results['overall_metrics']
)

# Save to file
filepath = generator.save_report(report, "week5_report.md")

# Calibration report
cal_report = generator.generate_calibration_report(calibration_data)

# Export to CSV
generator.export_to_csv(
    data=weekly_summaries,
    filepath="weekly_results.csv"
)
```

## Backtest Engine Features

### Risk Modes

The backtest engine supports three risk modes with different Kelly fractions and bet sizing:

| Risk Mode | Kelly Fraction | Max Bet % | Min Confidence |
|-----------|----------------|-----------|----------------|
| Conservative | 1/8 Kelly (0.125) | 5% | 0.65 |
| Balanced | 1/4 Kelly (0.25) | 10% | 0.60 |
| Aggressive | 1/2 Kelly (0.50) | 15% | 0.55 |

### Backtest Results

The backtest returns comprehensive results including:

```python
{
    "backtest_summary": {
        "weeks": [1, 2, 3, 4, 5],
        "league": "NFL",
        "risk_mode": "balanced",
        "initial_bankroll": 1000.0,
        "final_bankroll": 1155.0,
        "total_profit": 155.0,
        "num_weeks": 5,
        "total_bets": 125
    },
    "overall_metrics": {
        "roi_metrics": {...},
        "sharpe_ratio": 1.85,
        "drawdown": {...},
        "calibration": {...},
        "win_rate": 0.68,
        "win_rate_by_confidence": {...}
    },
    "weekly_summary": [...],
    "bankroll_history": [...],
    "calibration_plot": "base64_encoded_png"
}
```

## Calibration Monitoring

### Calibration Metrics

- **ECE (Expected Calibration Error)**: Measures average calibration error across probability bins
  - < 0.05: Excellent
  - < 0.08: Good
  - < 0.10: Fair
  - \> 0.10: Poor (critical threshold)

- **Brier Score**: Mean squared error of probability predictions
  - < 0.20: Excellent
  - < 0.22: Good
  - < 0.25: Fair
  - \> 0.25: Poor (critical threshold)

- **MCE (Maximum Calibration Error)**: Maximum error across any bin

### Degradation Detection

The monitor automatically detects calibration degradation and provides:

```python
{
    "is_degraded": True,
    "severity": "warning",  # good, warning, critical
    "issues": [
        "High ECE: 0.0852 > 0.08"
    ],
    "recommendations": [
        "Schedule model recalibration",
        "Monitor calibration closely over next window",
        "Review feature importance for unexpected changes"
    ]
}
```

### Calibration Status

Track calibration over time with trend analysis:

```python
{
    "status": "warning",
    "ece": 0.0852,
    "brier": 0.2103,
    "last_check": datetime(...),
    "trend": "degrading",  # improving, stable, degrading
    "history_length": 15
}
```

## Metrics Calculator

### Available Metrics

#### ROI Metrics
- Total profit/loss
- Return on investment (%)
- Total wagered
- Final bankroll
- Number of bets

#### Risk-Adjusted Returns
- **Sharpe Ratio**: Risk-adjusted performance metric
  - \> 3.0: Excellent
  - \> 2.0: Very good
  - \> 1.0: Good
  - < 1.0: Fair/Poor

#### Drawdown Analysis
- Maximum drawdown (%)
- Drawdown amount ($)
- Peak and valley values
- Recovery rate

#### Calibration Quality
- Expected Calibration Error (ECE)
- Brier score
- Maximum Calibration Error (MCE)

#### Win Rate Analysis
- Overall win rate
- Win rate by confidence level
- Number of bets per confidence band

### Kelly Criterion

The calculator implements Kelly bet sizing:

```python
kelly_fraction = calculator.calculate_kelly_fraction(
    p_win=0.65,           # Probability of winning
    odds=2.0,             # Decimal odds
    kelly_fraction=0.25   # Use 1/4 Kelly
)
```

## Report Generator

### Weekly Report Format

```markdown
# Backtest Report - NFL Week 5

## Executive Summary
**Overall Performance:** Good

- **ROI:** 15.50%
- **Win Rate:** 68.0%
- **Sharpe Ratio:** 1.85

## Return on Investment
- **Total Profit:** $155.00
- **Total Wagered:** $500.00
- **Final Bankroll:** $1155.00

## Risk Analysis
**Sharpe Ratio:** 1.850 (Good)

**Drawdown Analysis:**
- Max Drawdown: 8.50%
- Drawdown Amount: $85.00

## Calibration Quality
**Overall Quality:** Excellent

- **Expected Calibration Error (ECE):** 0.0450
- **Brier Score:** 0.1850

## Recommendations
- Strong performance - consider scaling up bet sizes gradually
- Calibration is excellent - maintain current calibration approach
```

### Export Options

- **Markdown**: Human-readable reports with formatting
- **CSV**: Structured data for analysis in Excel/Python
- **JSON**: Programmatic access to metrics

## Database Integration

### Storing Backtest Results

Results are automatically saved to the `experiments` table:

```python
experiment = Experiment(
    user_id=user_id,
    week=week,
    league=league,
    risk_mode="balanced",
    bankroll=1000.0,
    num_props=250,
    num_slips=125,
    metrics={...},
    status="completed"
)
```

### Storing Calibration History

Calibration checks are stored for historical trending:

```python
await monitor.store_calibration_history(
    user_id=user_id,
    week=week,
    league=league,
    metrics=calibration_metrics
)

# Retrieve historical data
history = await monitor.get_historical_calibration(
    league="NFL",
    weeks=[1, 2, 3, 4, 5]
)
```

## Best Practices

### Backtesting

1. **Use Realistic Scenarios**: Start with conservative bankroll and risk mode
2. **Multiple Weeks**: Test across at least 4-6 weeks for statistical significance
3. **Risk Management**: Never exceed 10% of bankroll on single bet
4. **Monitor Drawdown**: If drawdown > 30%, review strategy

### Calibration Monitoring

1. **Regular Checks**: Check calibration every 500-1000 predictions
2. **Rolling Windows**: Use rolling windows to detect recent degradation
3. **Trend Analysis**: Monitor trend over 5+ checks
4. **Recalibration**: Recalibrate when ECE > 0.08 or Brier > 0.22

### Performance Evaluation

1. **Look at Sharpe**: ROI alone isn't enough - consider risk-adjusted returns
2. **Calibration First**: Poor calibration = unreliable predictions
3. **Win Rate by Confidence**: Higher confidence should mean higher win rate
4. **Drawdown Recovery**: Track how quickly system recovers from losses

## Advanced Usage

### Custom Risk Modes

```python
# Modify risk mode configuration
BacktestEngine.RISK_MODES["custom"] = {
    "kelly_fraction": 0.20,
    "max_bet_pct": 0.08,
    "min_confidence": 0.62,
}

engine = BacktestEngine(risk_mode="custom")
```

### Calibration Thresholds

```python
# Adjust thresholds
CalibrationMonitor.ECE_WARNING_THRESHOLD = 0.07
CalibrationMonitor.ECE_CRITICAL_THRESHOLD = 0.09
CalibrationMonitor.BRIER_WARNING_THRESHOLD = 0.20
CalibrationMonitor.BRIER_CRITICAL_THRESHOLD = 0.23
```

### Multi-Week Analysis

```python
# Generate summary across multiple weeks
weekly_results = []
for week in range(1, 18):
    results = await engine.run_backtest(weeks=[week], league="NFL")
    weekly_results.append(results['overall_metrics'])

# Generate comparison report
summary = generator.generate_summary_table(weekly_results)
```

## Examples

See `example_usage.py` for comprehensive examples including:
- Basic backtesting
- Comparing risk modes
- Calibration monitoring
- Metrics calculation
- Report generation

Run examples:
```bash
python -m src.eval.example_usage
```

## API Reference

### BacktestEngine

```python
BacktestEngine(
    db_session: Optional[AsyncSession] = None,
    initial_bankroll: float = 1000.0,
    risk_mode: str = "balanced"
)

async run_backtest(
    weeks: List[int],
    league: str,
    model: Optional[EnsemblePredictor] = None,
    user_id: Optional[str] = None,
    save_to_db: bool = True
) -> Dict[str, any]
```

### CalibrationMonitor

```python
CalibrationMonitor(db_session: Optional[AsyncSession] = None)

check_calibration(
    predictions: List[float],
    outcomes: List[bool],
    window: int = 500
) -> Dict[str, float]

detect_degradation(
    current_metrics: Optional[Dict[str, float]] = None
) -> Dict[str, any]

get_calibration_status() -> Dict[str, any]
```

### MetricsCalculator

```python
MetricsCalculator()

calculate_roi(slips: List[Dict], initial_bankroll: float) -> Dict
calculate_sharpe(returns: List[float]) -> float
calculate_max_drawdown(bankroll_history: List[float]) -> Dict
calculate_win_rate_by_confidence(predictions, outcomes) -> Dict
calculate_calibration_metrics(predictions, outcomes) -> Dict
```

### ReportGenerator

```python
ReportGenerator(output_dir: Optional[str] = None)

generate_weekly_report(week, league, metrics) -> str
generate_calibration_report(calibration_data) -> str
export_to_csv(data: List[Dict], filepath: str) -> str
save_report(report: str, filename: str) -> str
```

## Troubleshooting

### Low Sharpe Ratio
- Review bet sizing - may be too aggressive
- Check calibration - poor calibration leads to volatile returns
- Increase min_confidence threshold

### High Calibration Error
- Recalibrate model on recent data
- Check for distribution shift in features
- Review feature importance

### Large Drawdowns
- Reduce risk mode (aggressive → balanced → conservative)
- Increase min_confidence threshold
- Implement stop-loss rules

## Contributing

When adding new metrics or features:
1. Add comprehensive docstrings
2. Include type hints
3. Add unit tests
4. Update README with examples
5. Follow existing code style

## License

Proprietary - BetterBros Props

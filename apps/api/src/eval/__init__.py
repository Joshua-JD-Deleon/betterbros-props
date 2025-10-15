"""
Evaluation Package - Backtesting and calibration monitoring

Provides comprehensive tools for evaluating betting model performance:
- Backtest engine for historical simulation
- Calibration monitoring and degradation detection
- Metrics calculation (ROI, Sharpe, drawdown, etc.)
- Report generation (markdown and CSV)

Usage:
    from src.eval import BacktestEngine, CalibrationMonitor, MetricsCalculator

    # Run backtest
    engine = BacktestEngine(
        db_session=db,
        initial_bankroll=1000.0,
        risk_mode="balanced"
    )
    results = await engine.run_backtest(weeks=[1, 2, 3], league="NFL")

    # Monitor calibration
    monitor = CalibrationMonitor(db_session=db)
    calibration = monitor.check_calibration(predictions, outcomes, window=500)
    status = monitor.get_calibration_status()

    # Calculate metrics
    calculator = MetricsCalculator()
    roi = calculator.calculate_roi(slips, initial_bankroll=1000.0)
    sharpe = calculator.calculate_sharpe(returns)

    # Generate reports
    generator = ReportGenerator(output_dir="./reports")
    report = generator.generate_weekly_report(week=1, league="NFL", metrics=results)
"""
from .backtest import BacktestEngine
from .calibration_monitor import CalibrationMonitor
from .metrics import MetricsCalculator
from .reports import ReportGenerator

__all__ = [
    "BacktestEngine",
    "CalibrationMonitor",
    "MetricsCalculator",
    "ReportGenerator",
]

__version__ = "1.0.0"

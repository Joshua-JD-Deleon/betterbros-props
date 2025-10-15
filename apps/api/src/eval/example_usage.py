"""
Example usage of the backtesting and calibration monitoring system

Demonstrates:
- Running backtests with different risk modes
- Monitoring calibration quality
- Generating reports
- Calculating metrics
- Detecting calibration degradation
"""
import asyncio
from datetime import datetime

from src.db import get_db_session
from src.eval import (
    BacktestEngine,
    CalibrationMonitor,
    MetricsCalculator,
    ReportGenerator,
)


async def example_basic_backtest():
    """Run a basic backtest for multiple weeks"""
    print("=" * 60)
    print("EXAMPLE 1: Basic Backtest")
    print("=" * 60)

    async with get_db_session() as db:
        # Initialize backtest engine
        engine = BacktestEngine(
            db_session=db,
            initial_bankroll=1000.0,
            risk_mode="balanced"
        )

        # Run backtest for weeks 1-5
        results = await engine.run_backtest(
            weeks=[1, 2, 3, 4, 5],
            league="NFL",
            user_id="example_user_123",
            save_to_db=True
        )

        # Print summary
        print("\nBacktest Summary:")
        print(f"  Initial Bankroll: ${results['backtest_summary']['initial_bankroll']:.2f}")
        print(f"  Final Bankroll:   ${results['backtest_summary']['final_bankroll']:.2f}")
        print(f"  Total Profit:     ${results['backtest_summary']['total_profit']:.2f}")
        print(f"  Total Bets:       {results['backtest_summary']['total_bets']}")

        print("\nOverall Metrics:")
        roi = results['overall_metrics']['roi_metrics']
        print(f"  ROI:              {roi['roi']:.2f}%")
        print(f"  Sharpe Ratio:     {results['overall_metrics']['sharpe_ratio']:.2f}")
        print(f"  Win Rate:         {results['overall_metrics']['win_rate'] * 100:.1f}%")

        print("\nCalibration Metrics:")
        cal = results['overall_metrics']['calibration']
        print(f"  ECE:              {cal['ece']:.4f}")
        print(f"  Brier Score:      {cal['brier_score']:.4f}")

        print("\nWeekly Breakdown:")
        for week_summary in results['weekly_summary']:
            print(f"  Week {week_summary['week']}: "
                  f"ROI={week_summary['roi']:.1f}%, "
                  f"Bets={week_summary['num_slips']}, "
                  f"Bankroll=${week_summary['bankroll']:.2f}")

        return results


async def example_compare_risk_modes():
    """Compare performance across different risk modes"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Compare Risk Modes")
    print("=" * 60)

    risk_modes = ["conservative", "balanced", "aggressive"]
    results_by_mode = {}

    async with get_db_session() as db:
        for risk_mode in risk_modes:
            print(f"\nTesting {risk_mode} mode...")

            engine = BacktestEngine(
                db_session=db,
                initial_bankroll=1000.0,
                risk_mode=risk_mode
            )

            results = await engine.run_backtest(
                weeks=[1, 2, 3],
                league="NFL",
                save_to_db=False
            )

            results_by_mode[risk_mode] = results

        # Compare results
        print("\n" + "-" * 60)
        print("Comparison:")
        print("-" * 60)
        print(f"{'Risk Mode':<15} {'ROI':<10} {'Sharpe':<10} {'Max DD':<10} {'Win Rate':<10}")
        print("-" * 60)

        for mode, results in results_by_mode.items():
            roi = results['overall_metrics']['roi_metrics']['roi']
            sharpe = results['overall_metrics']['sharpe_ratio']
            max_dd = results['overall_metrics']['drawdown']['max_drawdown']
            win_rate = results['overall_metrics']['win_rate']

            print(f"{mode:<15} {roi:>8.1f}% {sharpe:>8.2f}  {max_dd:>8.1f}% {win_rate * 100:>8.1f}%")


async def example_calibration_monitoring():
    """Monitor calibration quality over time"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Calibration Monitoring")
    print("=" * 60)

    # Simulate predictions and outcomes
    import numpy as np

    np.random.seed(42)

    # Generate well-calibrated predictions
    predictions = list(np.random.beta(5, 5, size=1000))
    outcomes = [p > np.random.random() for p in predictions]

    print(f"\nGenerated {len(predictions)} predictions")

    async with get_db_session() as db:
        # Initialize monitor
        monitor = CalibrationMonitor(db_session=db)

        # Check calibration
        metrics = monitor.check_calibration(
            predictions=predictions,
            outcomes=outcomes,
            window=500
        )

        print("\nCalibration Metrics:")
        print(f"  ECE:              {metrics['ece']:.4f}")
        print(f"  Brier Score:      {metrics['brier']:.4f}")
        print(f"  MCE:              {metrics['mce']:.4f}")
        print(f"  Samples:          {metrics['n_samples']}")

        # Check for degradation
        degradation = monitor.detect_degradation(metrics)

        print("\nDegradation Analysis:")
        print(f"  Status:           {degradation['severity'].upper()}")
        print(f"  Is Degraded:      {degradation['is_degraded']}")

        if degradation['issues']:
            print("\n  Issues:")
            for issue in degradation['issues']:
                print(f"    - {issue}")

        if degradation['recommendations']:
            print("\n  Recommendations:")
            for rec in degradation['recommendations']:
                print(f"    - {rec}")

        # Get calibration status
        status = monitor.get_calibration_status()

        print("\nCalibration Status:")
        print(f"  Current Status:   {status['status'].upper()}")
        print(f"  Trend:            {status['trend'].capitalize()}")
        print(f"  History Length:   {status['history_length']}")


async def example_metrics_calculation():
    """Calculate various performance metrics"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Metrics Calculation")
    print("=" * 60)

    # Sample bet slips
    slips = [
        {"stake": 50.0, "payout": 100.0, "won": True},
        {"stake": 75.0, "payout": 0.0, "won": False},
        {"stake": 100.0, "payout": 200.0, "won": True},
        {"stake": 60.0, "payout": 120.0, "won": True},
        {"stake": 80.0, "payout": 0.0, "won": False},
    ]

    calculator = MetricsCalculator()

    # Calculate ROI
    roi_metrics = calculator.calculate_roi(slips, initial_bankroll=1000.0)

    print("\nROI Metrics:")
    print(f"  ROI:              {roi_metrics['roi']:.2f}%")
    print(f"  Total Profit:     ${roi_metrics['total_profit']:.2f}")
    print(f"  Total Wagered:    ${roi_metrics['total_wagered']:.2f}")
    print(f"  Final Bankroll:   ${roi_metrics['final_bankroll']:.2f}")
    print(f"  Number of Bets:   {roi_metrics['num_bets']}")

    # Calculate returns and Sharpe ratio
    returns, bankroll_history = calculator.calculate_returns_series(
        slips, initial_bankroll=1000.0
    )

    sharpe = calculator.calculate_sharpe(returns)

    print(f"\nSharpe Ratio:       {sharpe:.3f}")

    # Calculate drawdown
    drawdown = calculator.calculate_max_drawdown(bankroll_history)

    print("\nDrawdown Analysis:")
    print(f"  Max Drawdown:     {drawdown['max_drawdown']:.2f}%")
    print(f"  Drawdown Amount:  ${drawdown['max_drawdown_amount']:.2f}")
    print(f"  Peak Value:       ${drawdown['peak_value']:.2f}")
    print(f"  Valley Value:     ${drawdown['valley_value']:.2f}")
    print(f"  Recovery Rate:    {drawdown['recovery_rate']:.1f}%")

    # Win rate by confidence
    predictions = [0.75, 0.55, 0.85, 0.70, 0.60]
    outcomes = [True, False, True, True, False]

    win_rate_by_conf = calculator.calculate_win_rate_by_confidence(
        predictions, outcomes
    )

    print("\nWin Rate by Confidence:")
    for conf_key, stats in sorted(win_rate_by_conf.items()):
        print(f"  {conf_key}: "
              f"Win Rate={stats['win_rate'] * 100:.1f}%, "
              f"Bets={stats['num_bets']}")


async def example_report_generation():
    """Generate evaluation reports"""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Report Generation")
    print("=" * 60)

    # Sample metrics
    metrics = {
        "roi_metrics": {
            "roi": 15.5,
            "total_profit": 155.0,
            "total_wagered": 500.0,
            "final_bankroll": 1155.0,
            "num_bets": 25,
        },
        "sharpe_ratio": 1.85,
        "win_rate": 0.68,
        "calibration": {
            "ece": 0.045,
            "brier_score": 0.185,
            "mce": 0.082,
        },
        "drawdown": {
            "max_drawdown": 8.5,
            "max_drawdown_amount": 85.0,
            "peak_value": 1200.0,
            "valley_value": 1115.0,
            "recovery_rate": 92.0,
        },
        "win_rate_by_confidence": {
            "conf_0.6": {"win_rate": 0.62, "num_bets": 20, "threshold": 0.6},
            "conf_0.7": {"win_rate": 0.75, "num_bets": 12, "threshold": 0.7},
            "conf_0.8": {"win_rate": 0.85, "num_bets": 5, "threshold": 0.8},
        },
    }

    generator = ReportGenerator(output_dir="./reports")

    # Generate weekly report
    report = generator.generate_weekly_report(
        week=5,
        league="NFL",
        metrics=metrics,
        include_details=True
    )

    print("\nWeekly Report Generated:")
    print("-" * 60)
    print(report)
    print("-" * 60)

    # Save report
    filepath = generator.save_report(
        report=report,
        filename=f"backtest_week_5_{datetime.now().strftime('%Y%m%d')}.md"
    )

    if filepath:
        print(f"\nReport saved to: {filepath}")

    # Generate calibration report
    calibration_data = {
        "status": "good",
        "ece": 0.045,
        "brier": 0.185,
        "trend": "stable",
        "is_degraded": False,
        "history_length": 10,
    }

    cal_report = generator.generate_calibration_report(calibration_data)

    print("\nCalibration Report:")
    print("-" * 60)
    print(cal_report)
    print("-" * 60)


async def main():
    """Run all examples"""
    print("\n")
    print("=" * 60)
    print("BACKTESTING AND CALIBRATION MONITORING EXAMPLES")
    print("=" * 60)

    try:
        # Run examples
        await example_basic_backtest()
        await example_compare_risk_modes()
        await example_calibration_monitoring()
        await example_metrics_calculation()
        await example_report_generation()

        print("\n" + "=" * 60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 60)

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

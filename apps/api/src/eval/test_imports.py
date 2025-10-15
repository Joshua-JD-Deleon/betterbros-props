"""
Quick test to verify all modules import correctly
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")

    try:
        from src.eval import (
            BacktestEngine,
            CalibrationMonitor,
            MetricsCalculator,
            ReportGenerator,
        )
        print("✓ Main package imports successful")

        # Test individual modules
        from src.eval.backtest import BacktestEngine as BE
        print("✓ backtest.py imports successful")

        from src.eval.calibration_monitor import CalibrationMonitor as CM
        print("✓ calibration_monitor.py imports successful")

        from src.eval.metrics import MetricsCalculator as MC
        print("✓ metrics.py imports successful")

        from src.eval.reports import ReportGenerator as RG
        print("✓ reports.py imports successful")

        # Test instantiation
        calculator = MetricsCalculator()
        print("✓ MetricsCalculator instantiation successful")

        monitor = CalibrationMonitor()
        print("✓ CalibrationMonitor instantiation successful")

        generator = ReportGenerator()
        print("✓ ReportGenerator instantiation successful")

        # BacktestEngine requires db_session, so just check class exists
        assert BacktestEngine is not None
        print("✓ BacktestEngine class accessible")

        print("\n" + "=" * 50)
        print("ALL IMPORT TESTS PASSED!")
        print("=" * 50)

        return True

    except Exception as e:
        print(f"\n✗ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_basic_functionality():
    """Test basic functionality without database"""
    print("\nTesting basic functionality...")

    try:
        from src.eval import MetricsCalculator, ReportGenerator

        # Test metrics calculator
        calculator = MetricsCalculator()

        # Test ROI calculation
        slips = [
            {"stake": 50.0, "payout": 100.0, "won": True},
            {"stake": 75.0, "payout": 0.0, "won": False},
        ]

        roi = calculator.calculate_roi(slips, initial_bankroll=1000.0)
        assert "roi" in roi
        assert "total_profit" in roi
        print(f"✓ ROI calculation works - ROI: {roi['roi']:.2f}%")

        # Test Sharpe calculation
        returns = [0.05, -0.02, 0.03, 0.01, -0.01]
        sharpe = calculator.calculate_sharpe(returns)
        assert isinstance(sharpe, float)
        print(f"✓ Sharpe calculation works - Sharpe: {sharpe:.3f}")

        # Test drawdown
        bankroll_history = [1000, 1050, 1020, 980, 1030, 1100]
        drawdown = calculator.calculate_max_drawdown(bankroll_history)
        assert "max_drawdown" in drawdown
        print(f"✓ Drawdown calculation works - Max DD: {drawdown['max_drawdown']:.2f}%")

        # Test report generator
        generator = ReportGenerator()

        metrics = {
            "roi_metrics": roi,
            "sharpe_ratio": sharpe,
            "win_rate": 0.65,
            "calibration": {
                "ece": 0.045,
                "brier_score": 0.185,
                "mce": 0.082,
            },
        }

        report = generator.generate_weekly_report(
            week=1,
            league="NFL",
            metrics=metrics
        )
        assert len(report) > 0
        assert "Backtest Report" in report
        print("✓ Report generation works")

        print("\n" + "=" * 50)
        print("ALL FUNCTIONALITY TESTS PASSED!")
        print("=" * 50)

        return True

    except Exception as e:
        print(f"\n✗ Functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_imports()
    if success:
        test_basic_functionality()

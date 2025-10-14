"""
Evaluation and backtesting module.
"""

from .backtest import (
    evaluate_backtest,
    BacktestEngine,
    filter_by_ci_width,
    profile_history,
    simulate_week,
    generate_mock_outcomes,
    calculate_calibration_metrics,
    generate_weekly_report,
)

from .exports import (
    export_props_csv,
    export_slips_csv,
    import_props_csv,
    import_slips_csv,
    export_backtest_results_csv,
)

from .experiments import (
    ExperimentTracker,
    record_experiment,
    query_experiments,
    EVENT_TYPES,
)

__all__ = [
    # Backtest
    "evaluate_backtest",
    "BacktestEngine",
    "filter_by_ci_width",
    "profile_history",
    "simulate_week",
    "generate_mock_outcomes",
    "calculate_calibration_metrics",
    "generate_weekly_report",
    # Exports
    "export_props_csv",
    "export_slips_csv",
    "import_props_csv",
    "import_slips_csv",
    "export_backtest_results_csv",
    # Experiments
    "ExperimentTracker",
    "record_experiment",
    "query_experiments",
    "EVENT_TYPES",
]

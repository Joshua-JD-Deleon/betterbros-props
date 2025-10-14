"""
Tests for evaluation and backtesting.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

from src.eval import (
    evaluate_backtest,
    filter_by_ci_width,
    profile_history,
    calculate_calibration_metrics,
    generate_weekly_report,
    export_props_csv,
    export_slips_csv,
    import_props_csv,
    import_slips_csv,
    export_backtest_results_csv,
    record_experiment,
    query_experiments,
    EVENT_TYPES,
)

from src.snapshots import (
    lock_snapshot,
    load_snapshot,
    list_snapshots,
    SnapshotManager,
)


def test_evaluate_backtest():
    """Test backtest evaluation with mock mode."""
    results = evaluate_backtest(
        start_week=1,
        end_week=3,
        season=2024,
        initial_bankroll=100.0,
        risk_mode='balanced',
        mock_mode=True
    )

    # Check required fields
    assert isinstance(results, dict)
    assert 'total_return' in results
    assert 'win_rate' in results
    assert 'avg_roi_per_slip' in results
    assert 'sharpe_ratio' in results
    assert 'max_drawdown' in results
    assert 'total_slips' in results
    assert 'winning_slips' in results
    assert 'final_bankroll' in results
    assert 'bankroll_history' in results
    assert 'calibration_metrics' in results
    assert 'best_slip' in results
    assert 'worst_slip' in results
    assert 'by_risk_mode' in results
    assert 'by_leg_count' in results

    # Check types
    assert isinstance(results['total_return'], float)
    assert isinstance(results['win_rate'], float)
    assert isinstance(results['total_slips'], int)
    assert isinstance(results['bankroll_history'], pd.DataFrame)

    # Check calibration metrics
    calibration = results['calibration_metrics']
    assert 'ece' in calibration
    assert 'mce' in calibration
    assert 'brier_score' in calibration
    assert 'log_loss' in calibration
    assert 'bins' in calibration

    # Check that some slips were generated
    assert results['total_slips'] > 0


def test_filter_by_ci_width():
    """Test CI width filtering."""
    props_df = pd.DataFrame({
        'player_id': ['p1', 'p2', 'p3', 'p4'],
        'ci_lower': [0.40, 0.35, 0.50, 0.45],
        'ci_upper': [0.70, 0.75, 0.62, 0.80],
    })
    # widths: 0.30, 0.40, 0.12, 0.35
    props_df['ci_width'] = props_df['ci_upper'] - props_df['ci_lower']

    # Filter with max_width = 0.25
    filtered = filter_by_ci_width(props_df, max_width=0.25)

    assert len(filtered) < len(props_df)
    assert (filtered['ci_width'] <= 0.25).all()
    assert len(filtered) == 1  # Only p3 has width <= 0.25


def test_filter_by_ci_width_auto_calculate():
    """Test CI width filtering with auto-calculation."""
    props_df = pd.DataFrame({
        'player_id': ['p1', 'p2', 'p3'],
        'ci_lower': [0.40, 0.35, 0.50],
        'ci_upper': [0.70, 0.75, 0.62],
    })

    # Should auto-calculate ci_width
    filtered = filter_by_ci_width(props_df, max_width=0.25)

    assert 'ci_width' in filtered.columns
    assert (filtered['ci_width'] <= 0.25).all()


def test_profile_history():
    """Test history profiling."""
    profile = profile_history(lookback_weeks=4)

    assert isinstance(profile, dict)
    assert 'calibration_ece' in profile
    assert 'brier_score' in profile
    assert 'accuracy' in profile
    assert 'by_prop_type' in profile
    assert 'weeks_analyzed' in profile


def test_calculate_calibration_metrics():
    """Test calibration metric calculation."""
    # Perfect calibration
    predicted = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
    outcomes = [1, 0, 1, 0, 1, 0, 1, 0]  # 50% win rate

    metrics = calculate_calibration_metrics(predicted, outcomes)

    assert isinstance(metrics, dict)
    assert 'ece' in metrics
    assert 'mce' in metrics
    assert 'brier_score' in metrics
    assert 'log_loss' in metrics
    assert 'bins' in metrics

    # ECE should be low for perfect calibration
    assert metrics['ece'] < 0.1

    # Brier score should be reasonable
    assert 0 <= metrics['brier_score'] <= 1


def test_calculate_calibration_metrics_empty():
    """Test calibration with empty inputs."""
    metrics = calculate_calibration_metrics([], [])

    assert metrics['ece'] == 0.0
    assert metrics['mce'] == 0.0
    assert metrics['brier_score'] == 0.0
    assert metrics['log_loss'] == 0.0
    assert len(metrics['bins']) == 0


def test_export_import_props_csv():
    """Test CSV export and import roundtrip for props."""
    with tempfile.TemporaryDirectory() as tmpdir:
        props_df = pd.DataFrame({
            'player_name': ['Player A', 'Player B', 'Player C'],
            'team': ['KC', 'SF', 'BUF'],
            'position': ['QB', 'RB', 'WR'],
            'prop_type': ['passing_yards', 'rushing_yards', 'receiving_yards'],
            'line': [250.5, 75.5, 60.5],
            'prob_over': [0.55, 0.60, 0.65],
            'ci_lower': [0.50, 0.55, 0.60],
            'ci_upper': [0.60, 0.65, 0.70],
            'over_odds': [-110, -120, 100],
            'under_odds': [-110, 100, -120],
        })

        csv_path = Path(tmpdir) / "props.csv"

        # Export
        export_props_csv(props_df, str(csv_path))

        assert csv_path.exists()

        # Import
        imported_df = import_props_csv(str(csv_path))

        assert len(imported_df) == len(props_df)
        assert 'player_name' in imported_df.columns
        assert 'prob_over' in imported_df.columns


def test_export_import_slips_csv():
    """Test CSV export and import roundtrip for slips."""
    with tempfile.TemporaryDirectory() as tmpdir:
        slips = [
            {
                'slip_id': 'slip1',
                'num_legs': 3,
                'total_odds': 6.5,
                'raw_win_prob': 0.45,
                'correlation_adjusted_prob': 0.42,
                'expected_value': 2.73,
                'suggested_bet': 10.0,
                'risk_level': 'balanced',
                'diversity_score': 0.7,
                'legs': [
                    {
                        'player_name': 'Player A',
                        'prop_type': 'passing_yards',
                        'line': 250.5,
                        'direction': 'over',
                        'prob': 0.60,
                        'odds': -110
                    },
                    {
                        'player_name': 'Player B',
                        'prop_type': 'rushing_yards',
                        'line': 75.5,
                        'direction': 'over',
                        'prob': 0.65,
                        'odds': -120
                    }
                ]
            }
        ]

        csv_path = Path(tmpdir) / "slips.csv"

        # Export
        export_slips_csv(slips, str(csv_path))

        assert csv_path.exists()

        # Import
        imported_slips = import_slips_csv(str(csv_path))

        assert len(imported_slips) == len(slips)
        assert imported_slips[0]['slip_id'] == 'slip1'
        assert imported_slips[0]['num_legs'] == 3
        assert len(imported_slips[0]['legs']) == 2


def test_export_backtest_results():
    """Test exporting backtest results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results = evaluate_backtest(
            start_week=1,
            end_week=2,
            season=2024,
            initial_bankroll=100.0,
            mock_mode=True
        )

        csv_path = Path(tmpdir) / "backtest_results.csv"

        export_backtest_results_csv(results, str(csv_path))

        # Check that files were created
        assert (Path(tmpdir) / "backtest_results_summary.csv").exists()
        assert (Path(tmpdir) / "backtest_results_bankroll_history.csv").exists()


def test_generate_weekly_report():
    """Test generating weekly markdown report."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results = evaluate_backtest(
            start_week=1,
            end_week=2,
            season=2024,
            initial_bankroll=100.0,
            mock_mode=True
        )

        report_path = Path(tmpdir) / "weekly_report.md"

        generate_weekly_report(results, str(report_path))

        assert report_path.exists()

        # Check content
        content = report_path.read_text()
        assert "Backtest Weekly Summary" in content
        assert "Performance Metrics" in content
        assert "Calibration Analysis" in content
        assert "Recommendations" in content


def test_experiment_tracking_jsonl():
    """Test experiment tracking with JSONL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tracking_dir = Path(tmpdir)

        # Record events
        record_experiment({
            'event_type': EVENT_TYPES['SLIP_GENERATED'],
            'week': 5,
            'season': 2024,
            'risk_mode': 'balanced',
            'num_slips': 5,
            'metrics': {'win_rate': 0.60}
        }, tracking_dir=tracking_dir)

        record_experiment({
            'event_type': EVENT_TYPES['BACKTEST_RUN'],
            'week': 5,
            'season': 2024,
            'risk_mode': 'aggressive',
            'metrics': {'total_return': 15.5}
        }, tracking_dir=tracking_dir)

        # Query experiments
        df = query_experiments(tracking_dir=tracking_dir)

        assert len(df) == 2
        assert 'event_type' in df.columns
        assert 'timestamp' in df.columns


def test_experiment_tracking_filters():
    """Test experiment tracking with filters."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tracking_dir = Path(tmpdir)

        # Record multiple events
        for week in [1, 2, 3]:
            record_experiment({
                'event_type': EVENT_TYPES['SLIP_GENERATED'],
                'week': week,
                'season': 2024,
                'risk_mode': 'balanced'
            }, tracking_dir=tracking_dir)

        # Filter by week
        df = query_experiments(
            filters={'week': 2},
            tracking_dir=tracking_dir
        )

        assert len(df) == 1
        assert df.iloc[0]['week'] == 2


def test_snapshot_create_and_load():
    """Test creating and loading snapshots."""
    with tempfile.TemporaryDirectory() as tmpdir:
        snapshots_dir = Path(tmpdir) / "snapshots"

        props_df = pd.DataFrame({
            'player_id': ['p1', 'p2'],
            'prob_over': [0.55, 0.60]
        })

        slips = [
            {'slip_id': 'slip1', 'num_legs': 2}
        ]

        config = {
            'risk_mode': 'balanced',
            'bankroll': 100.0
        }

        # Create snapshot
        snapshot_id = lock_snapshot(
            props_df=props_df,
            slips=slips,
            config=config,
            week=5,
            season=2024,
            snapshots_dir=snapshots_dir
        )

        assert snapshot_id.startswith("2024_W5_")

        # Load snapshot
        loaded = load_snapshot(snapshot_id, snapshots_dir=snapshots_dir)

        assert 'props_df' in loaded
        assert 'slips' in loaded
        assert 'config' in loaded
        assert 'metadata' in loaded

        assert len(loaded['props_df']) == 2
        assert len(loaded['slips']) == 1
        assert loaded['config']['risk_mode'] == 'balanced'


def test_snapshot_list():
    """Test listing snapshots."""
    with tempfile.TemporaryDirectory() as tmpdir:
        snapshots_dir = Path(tmpdir) / "snapshots"

        manager = SnapshotManager(snapshots_dir=snapshots_dir)

        # Create multiple snapshots
        for week in [1, 2, 3]:
            props_df = pd.DataFrame({'player_id': ['p1']})
            slips = []
            config = {}

            manager.create_snapshot(
                props_df=props_df,
                slips=slips,
                config=config,
                week=week,
                season=2024
            )

        # List snapshots
        snapshots = manager.list_snapshots()

        assert len(snapshots) >= 3
        assert all('snapshot_id' in s for s in snapshots)
        assert all('timestamp' in s for s in snapshots)


def test_snapshot_cleanup():
    """Test cleaning up old snapshots."""
    with tempfile.TemporaryDirectory() as tmpdir:
        snapshots_dir = Path(tmpdir) / "snapshots"
        manager = SnapshotManager(snapshots_dir=snapshots_dir)

        # Create snapshot
        props_df = pd.DataFrame({'player_id': ['p1']})
        slips = []
        config = {}

        manager.create_snapshot(
            props_df=props_df,
            slips=slips,
            config=config,
            week=1,
            season=2024
        )

        # Try to cleanup (should keep recent snapshots)
        removed = manager.cleanup_old_snapshots(retention_days=30)

        # Should not remove recent snapshots
        assert removed == 0

        # List should still have snapshots
        snapshots = manager.list_snapshots()
        assert len(snapshots) >= 1


def test_snapshot_compare():
    """Test comparing snapshots."""
    with tempfile.TemporaryDirectory() as tmpdir:
        snapshots_dir = Path(tmpdir) / "snapshots"
        manager = SnapshotManager(snapshots_dir=snapshots_dir)

        # Create two snapshots with different data
        props_df1 = pd.DataFrame({
            'player_id': ['p1', 'p2'],
            'prob_over': [0.55, 0.60]
        })
        slips1 = [{'slip_id': 'slip1'}]
        config1 = {}

        snapshot_id1 = manager.create_snapshot(
            props_df=props_df1,
            slips=slips1,
            config=config1,
            week=1,
            season=2024
        )

        props_df2 = pd.DataFrame({
            'player_id': ['p1', 'p2', 'p3'],
            'prob_over': [0.60, 0.65, 0.70]
        })
        slips2 = [{'slip_id': 'slip1'}, {'slip_id': 'slip2'}]
        config2 = {}

        snapshot_id2 = manager.create_snapshot(
            props_df=props_df2,
            slips=slips2,
            config=config2,
            week=2,
            season=2024
        )

        # Compare snapshots
        comparison = manager.compare_snapshots(snapshot_id1, snapshot_id2)

        assert 'num_props' in comparison
        assert comparison['num_props']['diff'] == 1  # 3 - 2

        assert 'num_slips' in comparison
        assert comparison['num_slips']['diff'] == 1  # 2 - 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

#!/usr/bin/env python3
"""
CLI entry point for running weekly analysis.

Usage:
    python scripts/run_week.py --week 5 --season 2025
    python scripts/run_week.py --mode backtest
"""

import argparse
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import load_user_prefs
from src.ingest import fetch_current_props
from src.features import build_features
from src.models import estimate_probabilities
from src.corr import estimate_correlations
from src.optimize import optimize_slips
from src.eval import evaluate_backtest
from src.snapshots import lock_snapshot


def run_week_analysis(week: int, season: int, bankroll: float = 100.0):
    """
    Run analysis for a specific week.

    Args:
        week: NFL week number
        season: Season year
        bankroll: Bankroll amount
    """
    print(f"Running analysis for Week {week}, {season} season")
    print(f"Bankroll: ${bankroll:.2f}")
    print("-" * 50)

    # Load config
    config = load_user_prefs()

    # Fetch props
    print("Fetching props...")
    props_df = fetch_current_props(week=week, season=season, mock_mode=True)
    print(f"Fetched {len(props_df)} props")

    # Build features
    print("Building features...")
    props_df = build_features(props_df)

    # Estimate probabilities
    print("Estimating probabilities...")
    props_df = estimate_probabilities(props_df)

    # Estimate correlations
    print("Estimating correlations...")
    corr_matrix = estimate_correlations(props_df)

    # Optimize slips
    print("Optimizing slips...")
    slips = optimize_slips(
        props_df,
        corr_matrix,
        bankroll=bankroll,
        diversity_target=config.optimizer.diversity.target,
        n_slips=5
    )

    print(f"\nGenerated {len(slips)} optimized slips:")
    for i, slip in enumerate(slips, 1):
        print(f"\n{i}. {slip['risk_level'].upper()} Slip:")
        print(f"   EV: {slip['expected_value']:.2f}x")
        print(f"   Odds: {slip['total_odds']:.2f}")
        print(f"   Probability: {slip['correlation_adjusted_prob']:.1%}")
        print(f"   Suggested Bet: ${slip['suggested_bet']:.2f}")
        print(f"   Legs: {len(slip['legs'])}")
        for leg in slip['legs']:
            print(f"      - {leg['player_name']}: {leg['prop_type']} {leg['direction']} {leg['line']}")

    # Save snapshot
    snapshot_id = lock_snapshot(props_df, slips, {})
    print(f"\nSnapshot saved: {snapshot_id}")

    return props_df, slips


def run_backtest_mode(start_week: int, end_week: int, season: int, bankroll: float):
    """
    Run backtest mode.

    Args:
        start_week: Starting week
        end_week: Ending week
        season: Season year
        bankroll: Initial bankroll
    """
    print(f"Running backtest: Weeks {start_week}-{end_week}, {season} season")
    print(f"Initial Bankroll: ${bankroll:.2f}")
    print("-" * 50)

    results = evaluate_backtest(
        start_week=start_week,
        end_week=end_week,
        season=season,
        initial_bankroll=bankroll
    )

    print("\n=== BACKTEST RESULTS ===")
    print(f"Total Return: {results['total_return']:.1f}%")
    print(f"Final Bankroll: ${results['final_bankroll']:.2f}")
    print(f"Win Rate: {results['win_rate']:.1%}")
    print(f"Total Bets: {results['total_bets']}")
    print(f"Winning Bets: {results['winning_bets']}")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {results['max_drawdown']:.1f}%")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="NFL Props Analyzer CLI")

    parser.add_argument(
        "--mode",
        choices=["analyze", "backtest"],
        default="analyze",
        help="Mode to run (analyze or backtest)"
    )
    parser.add_argument(
        "--week",
        type=int,
        default=1,
        help="Week number (for analyze mode)"
    )
    parser.add_argument(
        "--season",
        type=int,
        default=2025,
        help="Season year"
    )
    parser.add_argument(
        "--bankroll",
        type=float,
        default=100.0,
        help="Bankroll amount"
    )
    parser.add_argument(
        "--start-week",
        type=int,
        default=1,
        help="Start week (for backtest mode)"
    )
    parser.add_argument(
        "--end-week",
        type=int,
        default=10,
        help="End week (for backtest mode)"
    )

    args = parser.parse_args()

    if args.mode == "analyze":
        run_week_analysis(args.week, args.season, args.bankroll)
    elif args.mode == "backtest":
        run_backtest_mode(args.start_week, args.end_week, args.season, args.bankroll)


if __name__ == "__main__":
    main()

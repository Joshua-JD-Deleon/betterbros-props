"""
Backtesting engine for evaluating strategy performance with comprehensive metrics.
"""

from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import json
from dataclasses import dataclass


@dataclass
class BacktestResults:
    """Structured backtest results."""
    total_return: float
    win_rate: float
    avg_roi_per_slip: float
    sharpe_ratio: float
    max_drawdown: float
    total_slips: int
    winning_slips: int
    final_bankroll: float
    bankroll_history: pd.DataFrame
    calibration_metrics: Dict[str, Any]
    best_slip: Dict[str, Any]
    worst_slip: Dict[str, Any]
    by_risk_mode: Dict[str, Any]
    by_leg_count: Dict[str, Any]


class BacktestEngine:
    """
    Engine for backtesting slip strategies on historical data.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize backtest engine.

        Args:
            data_dir: Directory containing historical data
        """
        self.data_dir = data_dir or Path("./data")
        self.results = []

    def load_historical_slates(
        self,
        start_week: int,
        end_week: int,
        season: int
    ) -> List[pd.DataFrame]:
        """
        Load historical prop slates.

        Args:
            start_week: Starting week
            end_week: Ending week
            season: Season year

        Returns:
            List of DataFrames, one per week
        """
        # Try to load from snapshots first
        snapshots_dir = self.data_dir / "snapshots"
        slates = []

        for week in range(start_week, end_week + 1):
            snapshot_pattern = f"{season}_W{week}_*"
            snapshot_files = list(snapshots_dir.glob(snapshot_pattern))

            if snapshot_files:
                # Load from snapshot
                snapshot_path = snapshot_files[0]
                props_file = snapshot_path / "props.parquet"
                if props_file.exists():
                    slate = pd.read_parquet(props_file)
                    slate['week'] = week
                    slate['season'] = season
                    slates.append(slate)
                    continue

            # Generate mock slate if no snapshot
            slate = self._generate_mock_slate(week, season)
            slates.append(slate)

        return slates

    def _generate_mock_slate(self, week: int, season: int) -> pd.DataFrame:
        """Generate realistic mock slate for testing."""
        np.random.seed(week * season)  # Consistent per week

        n_props = np.random.randint(50, 100)
        prop_types = ['passing_yards', 'rushing_yards', 'receiving_yards',
                     'passing_tds', 'receptions', 'rushing_tds']

        data = {
            "player_id": [f"p{i:03d}" for i in range(n_props)],
            "player_name": [f"Player_{i}" for i in range(n_props)],
            "prop_type": np.random.choice(prop_types, n_props),
            "line": np.random.uniform(50, 300, n_props),
            "prob_over": np.random.uniform(0.40, 0.75, n_props),
            "ci_lower": np.random.uniform(0.30, 0.60, n_props),
            "ci_upper": np.random.uniform(0.50, 0.85, n_props),
            "over_odds": np.random.choice([-120, -110, 100, 110, 120], n_props),
            "team": np.random.choice(['KC', 'SF', 'BUF', 'PHI', 'DAL', 'MIA'], n_props),
            "game_id": np.random.choice([f"g{i}" for i in range(8)], n_props),
            "position": np.random.choice(['QB', 'RB', 'WR', 'TE'], n_props),
            "week": week,
            "season": season
        }

        slate = pd.DataFrame(data)

        # Generate realistic actual outcomes based on probabilities
        slate['actual_outcome'] = (
            np.random.random(n_props) < slate['prob_over']
        ).astype(int)

        return slate

    def run_backtest(
        self,
        start_week: int,
        end_week: int,
        season: int,
        initial_bankroll: float = 100.0,
        risk_mode: str = "balanced",
        mock_mode: bool = True
    ) -> Dict[str, Any]:
        """
        Run comprehensive backtest over date range.

        Args:
            start_week: Starting week
            end_week: Ending week
            season: Season year
            initial_bankroll: Starting bankroll
            risk_mode: Risk mode for slip generation
            mock_mode: Use mock outcomes vs actual results

        Returns:
            Dictionary with comprehensive backtest results
        """
        slates = self.load_historical_slates(start_week, end_week, season)

        bankroll = initial_bankroll
        bankroll_history_data = []
        all_slips = []

        predicted_probs = []
        actual_outcomes = []

        by_leg_count = {}
        by_risk_mode = {risk_mode: {'slips': 0, 'wins': 0, 'profit': 0}}

        for week_num, slate in enumerate(slates, start=start_week):
            week_result = simulate_week(
                week=week_num,
                season=season,
                slate=slate,
                bankroll=bankroll,
                risk_mode=risk_mode,
                mock_mode=mock_mode
            )

            # Update bankroll
            bankroll += week_result['net_profit']

            # Record history
            bankroll_history_data.append({
                'week': week_num,
                'season': season,
                'starting_bankroll': bankroll - week_result['net_profit'],
                'ending_bankroll': bankroll,
                'total_wagered': week_result['total_wagered'],
                'total_won': week_result['total_won'],
                'net_profit': week_result['net_profit'],
                'num_slips': len(week_result['slips'])
            })

            # Track slips
            for slip in week_result['slips']:
                all_slips.append(slip)
                predicted_probs.append(slip['correlation_adjusted_prob'])
                actual_outcomes.append(1 if slip['outcome'] == 'win' else 0)

                # By leg count
                leg_count = slip['num_legs']
                if leg_count not in by_leg_count:
                    by_leg_count[leg_count] = {'slips': 0, 'wins': 0, 'profit': 0}
                by_leg_count[leg_count]['slips'] += 1
                if slip['outcome'] == 'win':
                    by_leg_count[leg_count]['wins'] += 1
                by_leg_count[leg_count]['profit'] += slip['payout'] - slip['suggested_bet']

                # By risk mode
                by_risk_mode[risk_mode]['slips'] += 1
                if slip['outcome'] == 'win':
                    by_risk_mode[risk_mode]['wins'] += 1
                by_risk_mode[risk_mode]['profit'] += slip['payout'] - slip['suggested_bet']

        # Calculate overall metrics
        total_slips = len(all_slips)
        winning_slips = sum(1 for s in all_slips if s['outcome'] == 'win')
        win_rate = (winning_slips / total_slips) if total_slips > 0 else 0

        total_return = ((bankroll - initial_bankroll) / initial_bankroll) * 100

        # Average ROI per slip
        slip_rois = [
            ((s['payout'] - s['suggested_bet']) / s['suggested_bet']) * 100
            for s in all_slips
        ]
        avg_roi_per_slip = np.mean(slip_rois) if slip_rois else 0

        # Sharpe ratio
        bankroll_history = pd.DataFrame(bankroll_history_data)
        if len(bankroll_history) > 1:
            returns = bankroll_history['net_profit'] / bankroll_history['starting_bankroll']
            sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(17) if np.std(returns) > 0 else 0
        else:
            sharpe = 0

        # Max drawdown
        peak = np.maximum.accumulate(bankroll_history['ending_bankroll'])
        drawdown = (bankroll_history['ending_bankroll'] - peak) / peak
        max_drawdown = abs(drawdown.min()) * 100 if len(drawdown) > 0 else 0

        # Calibration metrics
        calibration = calculate_calibration_metrics(predicted_probs, actual_outcomes)

        # Best and worst slips
        best_slip = max(all_slips, key=lambda s: (s['payout'] - s['suggested_bet']) / s['suggested_bet']) if all_slips else {}
        worst_slip = min(all_slips, key=lambda s: (s['payout'] - s['suggested_bet']) / s['suggested_bet']) if all_slips else {}

        # Format by_leg_count
        by_leg_count_formatted = {}
        for leg_count, data in by_leg_count.items():
            by_leg_count_formatted[f"{leg_count}_legs"] = {
                'total_slips': data['slips'],
                'winning_slips': data['wins'],
                'win_rate': data['wins'] / data['slips'] if data['slips'] > 0 else 0,
                'total_profit': data['profit'],
                'avg_profit_per_slip': data['profit'] / data['slips'] if data['slips'] > 0 else 0
            }

        # Format by_risk_mode
        by_risk_mode_formatted = {}
        for mode, data in by_risk_mode.items():
            by_risk_mode_formatted[mode] = {
                'total_slips': data['slips'],
                'winning_slips': data['wins'],
                'win_rate': data['wins'] / data['slips'] if data['slips'] > 0 else 0,
                'total_profit': data['profit'],
                'avg_profit_per_slip': data['profit'] / data['slips'] if data['slips'] > 0 else 0
            }

        return {
            'total_return': total_return,
            'win_rate': win_rate,
            'avg_roi_per_slip': avg_roi_per_slip,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'total_slips': total_slips,
            'winning_slips': winning_slips,
            'final_bankroll': bankroll,
            'bankroll_history': bankroll_history,
            'calibration_metrics': calibration,
            'best_slip': best_slip,
            'worst_slip': worst_slip,
            'by_risk_mode': by_risk_mode_formatted,
            'by_leg_count': by_leg_count_formatted,
            'all_slips': all_slips  # For detailed analysis
        }


def evaluate_backtest(
    start_week: int = 1,
    end_week: int = 10,
    season: int = 2024,
    initial_bankroll: float = 100.0,
    risk_mode: str = "balanced",
    mock_mode: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to run backtest.

    Args:
        start_week: Starting week
        end_week: Ending week
        season: Season year
        initial_bankroll: Starting bankroll
        risk_mode: Risk mode for slip generation
        mock_mode: Use mock outcomes

    Returns:
        Dictionary with backtest results
    """
    engine = BacktestEngine()
    return engine.run_backtest(
        start_week=start_week,
        end_week=end_week,
        season=season,
        initial_bankroll=initial_bankroll,
        risk_mode=risk_mode,
        mock_mode=mock_mode
    )


def simulate_week(
    week: int,
    season: int,
    slate: pd.DataFrame,
    bankroll: float,
    risk_mode: str,
    mock_mode: bool
) -> Dict[str, Any]:
    """
    Simulate one week of betting.

    Args:
        week: Week number
        season: Season year
        slate: Props DataFrame with actual outcomes
        bankroll: Current bankroll
        risk_mode: Risk mode
        mock_mode: Use mock slip generation

    Returns:
        {
            'slips': List[dict],
            'total_wagered': float,
            'total_won': float,
            'net_profit': float,
            'ending_bankroll': float
        }
    """
    # Generate slips for the week
    slips = _generate_slips_for_slate(slate, bankroll, risk_mode)

    # Generate outcomes
    slips_with_outcomes = generate_mock_outcomes(slips, slate) if mock_mode else slips

    # Calculate results
    total_wagered = sum(s['suggested_bet'] for s in slips_with_outcomes)
    total_won = sum(s['payout'] for s in slips_with_outcomes if s['outcome'] == 'win')
    net_profit = total_won - total_wagered

    return {
        'slips': slips_with_outcomes,
        'total_wagered': total_wagered,
        'total_won': total_won,
        'net_profit': net_profit,
        'ending_bankroll': bankroll + net_profit
    }


def generate_mock_outcomes(slips: List[Dict[str, Any]], slate: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Generate realistic mock outcomes for slips based on probabilities.

    Uses actual probabilities with randomness to simulate real-world variance.

    Args:
        slips: List of slip dictionaries
        slate: Props DataFrame with actual_outcome column

    Returns:
        Slips with added 'outcome' and 'payout' fields
    """
    slips_with_outcomes = []

    for slip in slips:
        slip_copy = slip.copy()

        # Check each leg
        all_legs_hit = True
        for leg in slip['legs']:
            player_id = leg['player_id']

            # Look up actual outcome from slate
            matching_props = slate[slate['player_id'] == player_id]
            if len(matching_props) > 0:
                # Use actual outcome with small amount of noise
                prob = leg['prob']
                # Add some variance: 10% chance to flip outcome
                flip_chance = 0.10
                actual_outcome = matching_props.iloc[0]['actual_outcome']

                if np.random.random() < flip_chance:
                    leg_hit = not actual_outcome
                else:
                    leg_hit = actual_outcome
            else:
                # Use probability directly
                leg_hit = np.random.random() < leg['prob']

            if not leg_hit:
                all_legs_hit = False
                break

        # Determine outcome and payout
        if all_legs_hit:
            slip_copy['outcome'] = 'win'
            slip_copy['payout'] = slip['suggested_bet'] * slip['total_odds']
        else:
            slip_copy['outcome'] = 'loss'
            slip_copy['payout'] = 0.0

        slips_with_outcomes.append(slip_copy)

    return slips_with_outcomes


def _generate_slips_for_slate(
    slate: pd.DataFrame,
    bankroll: float,
    risk_mode: str
) -> List[Dict[str, Any]]:
    """Generate slips for a slate using simple greedy approach."""
    from src.optimize import optimize_slips
    from src.corr import build_correlation_matrix_rule_based as build_correlation_matrix

    # Build correlation matrix
    corr_matrix = build_correlation_matrix(slate)

    # Generate slips
    try:
        slips = optimize_slips(
            props_df=slate,
            corr_matrix=corr_matrix,
            bankroll=bankroll,
            diversity_target=0.5,
            n_slips=5,
            risk_mode=risk_mode
        )
    except Exception as e:
        # Fallback to simple mock slips
        slips = _generate_simple_mock_slips(slate, bankroll)

    return slips


def _generate_simple_mock_slips(slate: pd.DataFrame, bankroll: float) -> List[Dict[str, Any]]:
    """Generate simple mock slips without optimizer."""
    n_slips = min(5, len(slate) // 3)
    slips = []

    for i in range(n_slips):
        n_legs = np.random.randint(2, 5)
        sampled = slate.sample(min(n_legs, len(slate)))

        legs = []
        total_odds = 1.0
        win_prob = 1.0

        for _, prop in sampled.iterrows():
            leg = {
                'player_id': prop['player_id'],
                'player_name': prop.get('player_name', 'Unknown'),
                'prop_type': prop['prop_type'],
                'line': prop['line'],
                'direction': 'over',
                'prob': float(prop['prob_over']),
                'odds': float(prop.get('over_odds', -110)),
                'team': prop.get('team', 'UNK'),
                'game_id': prop.get('game_id', 'UNK'),
                'position': prop.get('position', 'UNK')
            }
            legs.append(leg)

            # Convert odds to decimal
            odds = leg['odds']
            decimal_odds = (odds / 100 + 1) if odds > 0 else (100 / abs(odds) + 1)
            total_odds *= decimal_odds
            win_prob *= leg['prob']

        slips.append({
            'slip_id': f'mock_{i}',
            'legs': legs,
            'num_legs': len(legs),
            'total_odds': total_odds,
            'raw_win_prob': win_prob,
            'correlation_adjusted_prob': win_prob * 0.9,  # Simple penalty
            'expected_value': total_odds * win_prob * 0.9,
            'suggested_bet': min(10.0, bankroll * 0.02),
            'risk_level': 'balanced',
            'diversity_score': 0.6
        })

    return slips


def calculate_calibration_metrics(
    predicted_probs: List[float],
    outcomes: List[int]
) -> Dict[str, Any]:
    """
    Calculate calibration metrics for probability predictions.

    Args:
        predicted_probs: List of predicted probabilities
        outcomes: List of actual outcomes (0 or 1)

    Returns:
        {
            'ece': float,  # Expected Calibration Error
            'mce': float,  # Maximum Calibration Error
            'brier_score': float,
            'log_loss': float,
            'bins': List[dict]  # Per-bin calibration
        }
    """
    if len(predicted_probs) == 0:
        return {
            'ece': 0.0,
            'mce': 0.0,
            'brier_score': 0.0,
            'log_loss': 0.0,
            'bins': []
        }

    predicted_probs = np.array(predicted_probs)
    outcomes = np.array(outcomes)

    # Brier score
    brier_score = np.mean((predicted_probs - outcomes) ** 2)

    # Log loss (clip to avoid log(0))
    epsilon = 1e-15
    clipped_probs = np.clip(predicted_probs, epsilon, 1 - epsilon)
    log_loss = -np.mean(outcomes * np.log(clipped_probs) + (1 - outcomes) * np.log(1 - clipped_probs))

    # Calibration binning (10 bins)
    n_bins = 10
    bins = []
    bin_edges = np.linspace(0, 1, n_bins + 1)

    ece = 0.0
    mce = 0.0

    for i in range(n_bins):
        bin_lower = bin_edges[i]
        bin_upper = bin_edges[i + 1]

        # Find predictions in this bin
        in_bin = (predicted_probs >= bin_lower) & (predicted_probs < bin_upper)

        if i == n_bins - 1:  # Last bin includes upper edge
            in_bin = (predicted_probs >= bin_lower) & (predicted_probs <= bin_upper)

        n_in_bin = np.sum(in_bin)

        if n_in_bin > 0:
            bin_pred_probs = predicted_probs[in_bin]
            bin_outcomes = outcomes[in_bin]

            avg_predicted = np.mean(bin_pred_probs)
            avg_actual = np.mean(bin_outcomes)

            bin_error = abs(avg_predicted - avg_actual)

            # ECE: weighted by bin size
            ece += (n_in_bin / len(predicted_probs)) * bin_error

            # MCE: maximum across bins
            mce = max(mce, bin_error)

            bins.append({
                'bin_lower': float(bin_lower),
                'bin_upper': float(bin_upper),
                'count': int(n_in_bin),
                'avg_predicted': float(avg_predicted),
                'avg_actual': float(avg_actual),
                'error': float(bin_error)
            })

    return {
        'ece': float(ece),
        'mce': float(mce),
        'brier_score': float(brier_score),
        'log_loss': float(log_loss),
        'bins': bins
    }


def filter_by_ci_width(
    props_df: pd.DataFrame,
    max_width: float = 0.25
) -> pd.DataFrame:
    """
    Filter props by confidence interval width.

    Args:
        props_df: DataFrame with CI bounds
        max_width: Maximum allowed CI width

    Returns:
        Filtered DataFrame
    """
    if 'ci_width' not in props_df.columns:
        if 'ci_lower' in props_df.columns and 'ci_upper' in props_df.columns:
            props_df = props_df.copy()
            props_df['ci_width'] = props_df['ci_upper'] - props_df['ci_lower']
        else:
            return props_df

    return props_df[props_df['ci_width'] <= max_width].copy()


def profile_history(
    db_path: Optional[Path] = None,
    lookback_weeks: int = 4
) -> Dict[str, Any]:
    """
    Profile historical predictions vs outcomes.

    Args:
        db_path: Path to database with historical predictions
        lookback_weeks: Number of weeks to analyze

    Returns:
        Dictionary with profiling metrics
    """
    # TODO: Load from database when available
    # Mock results for now
    return {
        "calibration_ece": 0.08,
        "brier_score": 0.18,
        "log_loss": 0.52,
        "accuracy": 0.65,
        "by_prop_type": {
            "passing_yards": {"accuracy": 0.68, "brier": 0.16},
            "rushing_yards": {"accuracy": 0.62, "brier": 0.19},
            "receiving_yards": {"accuracy": 0.64, "brier": 0.18}
        },
        "weeks_analyzed": lookback_weeks
    }


def generate_weekly_report(backtest_results: Dict[str, Any], output_path: str) -> None:
    """
    Generate markdown report summarizing backtest.

    Args:
        backtest_results: Results from evaluate_backtest
        output_path: Path to save markdown report
    """
    report_lines = [
        "# Backtest Weekly Summary",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Performance Metrics",
        "",
        f"- **Total Return**: {backtest_results['total_return']:.2f}%",
        f"- **Win Rate**: {backtest_results['win_rate'] * 100:.2f}%",
        f"- **Average ROI per Slip**: {backtest_results['avg_roi_per_slip']:.2f}%",
        f"- **Sharpe Ratio**: {backtest_results['sharpe_ratio']:.3f}",
        f"- **Max Drawdown**: {backtest_results['max_drawdown']:.2f}%",
        f"- **Total Slips**: {backtest_results['total_slips']}",
        f"- **Winning Slips**: {backtest_results['winning_slips']}",
        f"- **Final Bankroll**: ${backtest_results['final_bankroll']:.2f}",
        "",
        "## Calibration Analysis",
        "",
        f"- **Expected Calibration Error (ECE)**: {backtest_results['calibration_metrics']['ece']:.4f}",
        f"- **Maximum Calibration Error (MCE)**: {backtest_results['calibration_metrics']['mce']:.4f}",
        f"- **Brier Score**: {backtest_results['calibration_metrics']['brier_score']:.4f}",
        f"- **Log Loss**: {backtest_results['calibration_metrics']['log_loss']:.4f}",
        "",
        "### Calibration by Probability Bin",
        "",
        "| Bin Range | Count | Avg Predicted | Avg Actual | Error |",
        "|-----------|-------|---------------|------------|-------|"
    ]

    for bin_data in backtest_results['calibration_metrics']['bins']:
        report_lines.append(
            f"| {bin_data['bin_lower']:.2f}-{bin_data['bin_upper']:.2f} | "
            f"{bin_data['count']} | {bin_data['avg_predicted']:.3f} | "
            f"{bin_data['avg_actual']:.3f} | {bin_data['error']:.3f} |"
        )

    report_lines.extend([
        "",
        "## Best Performing Slip",
        ""
    ])

    if backtest_results.get('best_slip'):
        best = backtest_results['best_slip']
        roi = ((best['payout'] - best['suggested_bet']) / best['suggested_bet']) * 100
        report_lines.extend([
            f"- **Slip ID**: {best['slip_id']}",
            f"- **Legs**: {best['num_legs']}",
            f"- **Odds**: {best['total_odds']:.2f}",
            f"- **Bet**: ${best['suggested_bet']:.2f}",
            f"- **Payout**: ${best['payout']:.2f}",
            f"- **ROI**: {roi:.2f}%",
            ""
        ])

    report_lines.extend([
        "## Worst Performing Slip",
        ""
    ])

    if backtest_results.get('worst_slip'):
        worst = backtest_results['worst_slip']
        roi = ((worst['payout'] - worst['suggested_bet']) / worst['suggested_bet']) * 100
        report_lines.extend([
            f"- **Slip ID**: {worst['slip_id']}",
            f"- **Legs**: {worst['num_legs']}",
            f"- **Odds**: {worst['total_odds']:.2f}",
            f"- **Bet**: ${worst['suggested_bet']:.2f}",
            f"- **Payout**: ${worst['payout']:.2f}",
            f"- **ROI**: {roi:.2f}%",
            ""
        ])

    report_lines.extend([
        "## Performance by Leg Count",
        "",
        "| Legs | Slips | Wins | Win Rate | Total Profit | Avg Profit/Slip |",
        "|------|-------|------|----------|--------------|-----------------|"
    ])

    for leg_key, data in sorted(backtest_results['by_leg_count'].items()):
        report_lines.append(
            f"| {leg_key} | {data['total_slips']} | {data['winning_slips']} | "
            f"{data['win_rate'] * 100:.1f}% | ${data['total_profit']:.2f} | "
            f"${data['avg_profit_per_slip']:.2f} |"
        )

    report_lines.extend([
        "",
        "## Recommendations",
        ""
    ])

    # Generate recommendations
    ece = backtest_results['calibration_metrics']['ece']
    if ece > 0.15:
        report_lines.append("- **HIGH ECE**: Model calibration needs improvement. Consider recalibration.")
    elif ece > 0.10:
        report_lines.append("- **MODERATE ECE**: Model calibration is acceptable but could be improved.")
    else:
        report_lines.append("- **GOOD ECE**: Model is well-calibrated.")

    win_rate = backtest_results['win_rate']
    if win_rate < 0.30:
        report_lines.append("- **LOW WIN RATE**: Consider more conservative slip construction or higher probability thresholds.")

    max_dd = backtest_results['max_drawdown']
    if max_dd > 30:
        report_lines.append("- **HIGH DRAWDOWN**: Consider reducing bet sizes or using more conservative Kelly fractions.")

    # Write to file
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))

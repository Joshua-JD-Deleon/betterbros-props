"""
CSV export functions for props and slips.
"""

from typing import List, Dict, Any
from pathlib import Path
import pandas as pd
import json
from datetime import datetime


def export_props_csv(props_df: pd.DataFrame, path: str) -> None:
    """
    Export props to CSV.

    Args:
        props_df: Props DataFrame
        path: Output CSV path

    Columns exported: player_name, team, position, prop_type, line, prob_over,
                     ci_lower, ci_upper, ev, edge, over_odds, under_odds
    """
    # Select and rename columns
    export_cols = {
        'player_name': 'Player Name',
        'team': 'Team',
        'position': 'Position',
        'prop_type': 'Prop Type',
        'line': 'Line',
        'prob_over': 'Prob Over',
        'ci_lower': 'CI Lower',
        'ci_upper': 'CI Upper',
    }

    # Build export DataFrame
    export_df = pd.DataFrame()

    for col, display_name in export_cols.items():
        if col in props_df.columns:
            export_df[display_name] = props_df[col]
        else:
            export_df[display_name] = None

    # Calculate EV if odds available
    if 'over_odds' in props_df.columns and 'prob_over' in props_df.columns:
        decimal_odds = props_df['over_odds'].apply(_american_to_decimal)
        export_df['EV'] = props_df['prob_over'] * decimal_odds
        export_df['Edge'] = export_df['EV'] - 1.0
    else:
        export_df['EV'] = None
        export_df['Edge'] = None

    # Add odds
    if 'over_odds' in props_df.columns:
        export_df['Over Odds'] = props_df['over_odds']
    else:
        export_df['Over Odds'] = None

    if 'under_odds' in props_df.columns:
        export_df['Under Odds'] = props_df['under_odds']
    else:
        export_df['Under Odds'] = None

    # Ensure directory exists
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    export_df.to_csv(path, index=False)

    print(f"Exported {len(export_df)} props to {path}")


def export_slips_csv(slips: List[Dict[str, Any]], path: str) -> None:
    """
    Export slips to CSV.

    Each row is one slip with columns:
    slip_id, num_legs, total_odds, win_prob, expected_value, suggested_bet,
    risk_level, diversity_score, legs (JSON string of leg details)

    Args:
        slips: List of slip dictionaries
        path: Output CSV path
    """
    if not slips:
        print("No slips to export")
        return

    # Build rows
    rows = []
    for slip in slips:
        row = {
            'Slip ID': slip.get('slip_id', 'unknown'),
            'Num Legs': slip.get('num_legs', len(slip.get('legs', []))),
            'Total Odds': slip.get('total_odds', 0.0),
            'Raw Win Prob': slip.get('raw_win_prob', 0.0),
            'Adjusted Win Prob': slip.get('correlation_adjusted_prob', slip.get('raw_win_prob', 0.0)),
            'Expected Value': slip.get('expected_value', 0.0),
            'Suggested Bet': slip.get('suggested_bet', 0.0),
            'Risk Level': slip.get('risk_level', 'unknown'),
            'Diversity Score': slip.get('diversity_score', 0.0),
        }

        # Add leg details as JSON string
        legs = slip.get('legs', [])
        leg_summary = []
        for leg in legs:
            leg_info = {
                'player': leg.get('player_name', 'Unknown'),
                'prop': leg.get('prop_type', 'unknown'),
                'line': leg.get('line', 0),
                'direction': leg.get('direction', 'over'),
                'prob': leg.get('prob', 0.0),
                'odds': leg.get('odds', 0)
            }
            leg_summary.append(leg_info)

        row['Legs (JSON)'] = json.dumps(leg_summary)

        # Add human-readable legs summary
        leg_strings = [
            f"{leg.get('player_name', 'Unknown')} {leg.get('prop_type', '')} "
            f"{leg.get('direction', 'over')} {leg.get('line', 0)}"
            for leg in legs
        ]
        row['Legs Summary'] = ' | '.join(leg_strings)

        rows.append(row)

    # Create DataFrame
    export_df = pd.DataFrame(rows)

    # Ensure directory exists
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    export_df.to_csv(path, index=False)

    print(f"Exported {len(export_df)} slips to {path}")


def import_props_csv(path: str) -> pd.DataFrame:
    """
    Import props from CSV.

    Args:
        path: CSV file path

    Returns:
        Props DataFrame
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Props CSV not found: {path}")

    df = pd.read_csv(path)

    # Reverse column name mapping
    rename_map = {
        'Player Name': 'player_name',
        'Team': 'team',
        'Position': 'position',
        'Prop Type': 'prop_type',
        'Line': 'line',
        'Prob Over': 'prob_over',
        'CI Lower': 'ci_lower',
        'CI Upper': 'ci_upper',
        'EV': 'ev',
        'Edge': 'edge',
        'Over Odds': 'over_odds',
        'Under Odds': 'under_odds'
    }

    df = df.rename(columns=rename_map)

    return df


def import_slips_csv(path: str) -> List[Dict[str, Any]]:
    """
    Import slips from CSV.

    Args:
        path: CSV file path

    Returns:
        List of slip dictionaries
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Slips CSV not found: {path}")

    df = pd.read_csv(path)

    slips = []
    for _, row in df.iterrows():
        slip = {
            'slip_id': row['Slip ID'],
            'num_legs': int(row['Num Legs']),
            'total_odds': float(row['Total Odds']),
            'raw_win_prob': float(row['Raw Win Prob']),
            'correlation_adjusted_prob': float(row['Adjusted Win Prob']),
            'expected_value': float(row['Expected Value']),
            'suggested_bet': float(row['Suggested Bet']),
            'risk_level': row['Risk Level'],
            'diversity_score': float(row['Diversity Score']),
        }

        # Parse legs JSON
        if 'Legs (JSON)' in row and pd.notna(row['Legs (JSON)']):
            slip['legs'] = json.loads(row['Legs (JSON)'])
        else:
            slip['legs'] = []

        slips.append(slip)

    return slips


def _american_to_decimal(american_odds: float) -> float:
    """Convert American odds to decimal odds."""
    if american_odds > 0:
        return (american_odds / 100) + 1
    else:
        return (100 / abs(american_odds)) + 1


def export_backtest_results_csv(backtest_results: Dict[str, Any], path: str) -> None:
    """
    Export backtest results to CSV.

    Args:
        backtest_results: Results from evaluate_backtest
        path: Output CSV path
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Export bankroll history
    bankroll_df = backtest_results['bankroll_history']
    bankroll_path = path.parent / f"{path.stem}_bankroll_history.csv"
    bankroll_df.to_csv(bankroll_path, index=False)
    print(f"Exported bankroll history to {bankroll_path}")

    # Export all slips
    all_slips = backtest_results.get('all_slips', [])
    if all_slips:
        slips_path = path.parent / f"{path.stem}_all_slips.csv"
        export_slips_csv(all_slips, str(slips_path))

    # Export summary metrics
    summary_data = {
        'Metric': [
            'Total Return (%)',
            'Win Rate (%)',
            'Avg ROI per Slip (%)',
            'Sharpe Ratio',
            'Max Drawdown (%)',
            'Total Slips',
            'Winning Slips',
            'Final Bankroll',
            'ECE',
            'Brier Score',
            'Log Loss'
        ],
        'Value': [
            backtest_results['total_return'],
            backtest_results['win_rate'] * 100,
            backtest_results['avg_roi_per_slip'],
            backtest_results['sharpe_ratio'],
            backtest_results['max_drawdown'],
            backtest_results['total_slips'],
            backtest_results['winning_slips'],
            backtest_results['final_bankroll'],
            backtest_results['calibration_metrics']['ece'],
            backtest_results['calibration_metrics']['brier_score'],
            backtest_results['calibration_metrics']['log_loss']
        ]
    }

    summary_df = pd.DataFrame(summary_data)
    summary_path = path.parent / f"{path.stem}_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    print(f"Exported summary to {summary_path}")

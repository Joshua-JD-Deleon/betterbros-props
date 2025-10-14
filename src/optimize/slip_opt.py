"""
Slip portfolio optimization with constraints and diversity targets.
Implements sophisticated correlation handling, Monte Carlo simulation,
and Kelly criterion bankroll management.
"""

from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
from scipy.stats import norm
import uuid


@dataclass
class SlipConstraints:
    """Constraints for slip optimization."""
    min_legs: int = 2
    max_legs: int = 5
    min_total_odds: float = 2.0
    max_total_odds: float = 50.0
    max_same_game_legs: int = 3
    max_per_team: int = 2
    player_repeat_limit: int = 2
    team_concentration_max: float = 0.4
    min_expected_value: float = 1.05
    disallow_same_player_same_stat: bool = True


@dataclass
class Slip:
    """Represents an optimized slip."""
    slip_id: str
    legs: List[Dict[str, Any]]
    num_legs: int
    total_odds: float
    raw_win_prob: float
    correlation_adjusted_prob: float
    expected_value: float
    variance: float
    value_at_risk_95: float
    suggested_bet: float
    risk_level: str
    diversity_score: float
    correlation_notes: List[str]


# Risk mode configuration
RISK_MODES = {
    "conservative": {
        "max_legs": 4,
        "min_prob": 0.65,
        "min_edge": 1.08,
        "corr_penalty": 1.0,
        "kelly_fraction": 0.25,
    },
    "balanced": {
        "max_legs": 6,
        "min_prob": 0.55,
        "min_edge": 1.05,
        "corr_penalty": 0.6,
        "kelly_fraction": 0.5,
    },
    "aggressive": {
        "max_legs": 8,
        "min_prob": 0.45,
        "min_edge": 1.03,
        "corr_penalty": 0.3,
        "kelly_fraction": 0.75,
    }
}


def optimize_slips(
    props_df: pd.DataFrame,
    corr_matrix: np.ndarray,
    bankroll: float,
    diversity_target: float = 0.5,
    n_slips: int = 5,
    risk_mode: str = "balanced",
    min_legs: int = None,
    max_legs: int = None,
    min_odds: float = None,
    max_odds: float = None
) -> List[dict]:
    """
    Generate optimized prop slips/parlays.

    Args:
        props_df: DataFrame with columns [player_name, prop_type, line, prob_over, ci_lower, ci_upper, over_odds, ...]
        corr_matrix: NxN correlation matrix between props
        bankroll: Total bankroll ($)
        diversity_target: 0-1, higher = more diverse (spread across teams/games/positions)
        n_slips: Number of different slips to generate
        risk_mode: "conservative" | "balanced" | "aggressive"
        min_legs: Minimum legs per slip (overrides risk_mode default)
        max_legs: Maximum legs per slip (overrides risk_mode default)
        min_odds: Minimum total odds (overrides default)
        max_odds: Maximum total odds (overrides default)

    Returns:
        List of slip dicts with complete analysis
    """
    if risk_mode not in RISK_MODES:
        raise ValueError(f"Invalid risk_mode: {risk_mode}. Must be one of {list(RISK_MODES.keys())}")

    mode_config = RISK_MODES[risk_mode]

    # Update constraints based on risk mode and user overrides
    constraints = SlipConstraints(
        min_legs=min_legs if min_legs is not None else 2,
        max_legs=max_legs if max_legs is not None else mode_config["max_legs"],
        min_total_odds=min_odds if min_odds is not None else 2.0,
        max_total_odds=max_odds if max_odds is not None else 50.0,
        min_expected_value=mode_config["min_edge"]
    )

    # Filter props by minimum probability and edge
    filtered_props = _filter_props_by_risk_mode(props_df, mode_config)

    if len(filtered_props) < constraints.min_legs:
        return []

    slips = []
    used_combinations = set()

    # Generate diverse slips with different seeds
    for i in range(n_slips * 3):  # Generate more, keep best
        seed = i
        slip = _construct_single_slip(
            filtered_props,
            corr_matrix,
            constraints,
            bankroll,
            diversity_target,
            mode_config,
            risk_mode,
            seed,
            existing_slips=slips
        )

        if slip is not None:
            # Check for duplicates
            leg_key = tuple(sorted([leg['player_id'] + leg['prop_type'] for leg in slip.legs]))
            if leg_key not in used_combinations:
                used_combinations.add(leg_key)
                slips.append(slip)

        if len(slips) >= n_slips:
            break

    # Sort by expected value
    slips.sort(key=lambda s: s.expected_value, reverse=True)

    # Return top N as dictionaries
    result = []
    for slip in slips[:n_slips]:
        slip_dict = asdict(slip)

        # Add safer alternative
        safer_slip = _create_safer_alternative(slip, mode_config, bankroll)
        if safer_slip:
            slip_dict['safer_alternative'] = asdict(safer_slip)

        result.append(slip_dict)

    return result


def _filter_props_by_risk_mode(
    props_df: pd.DataFrame,
    mode_config: dict
) -> pd.DataFrame:
    """Filter props based on risk mode parameters."""
    filtered = props_df.copy()

    # Filter by minimum probability
    filtered = filtered[filtered['prob_over'] >= mode_config['min_prob']]

    # Filter by minimum edge (EV > threshold)
    if 'over_odds' in filtered.columns:
        filtered['decimal_odds'] = filtered['over_odds'].apply(_american_to_decimal)
        filtered['ev'] = filtered['prob_over'] * filtered['decimal_odds']
        filtered = filtered[filtered['ev'] >= mode_config['min_edge']]

    # Penalize wide confidence intervals (uncertainty)
    if 'ci_lower' in filtered.columns and 'ci_upper' in filtered.columns:
        filtered['ci_width'] = filtered['ci_upper'] - filtered['ci_lower']
        # Reduce probability by uncertainty penalty
        filtered['prob_adjusted'] = filtered['prob_over'] * (1 - filtered['ci_width'] * 0.3)
        filtered['prob_adjusted'] = filtered['prob_adjusted'].clip(0.01, 0.99)
    else:
        filtered['prob_adjusted'] = filtered['prob_over']

    return filtered.reset_index(drop=True)


def _construct_single_slip(
    props_df: pd.DataFrame,
    corr_matrix: np.ndarray,
    constraints: SlipConstraints,
    bankroll: float,
    diversity_target: float,
    mode_config: dict,
    risk_mode: str,
    seed: int,
    existing_slips: List[Slip]
) -> Optional[Slip]:
    """Construct a single optimized slip using greedy algorithm."""
    np.random.seed(seed)

    # Start with highest EV prop
    props_df = props_df.copy()
    props_df['ev'] = props_df['prob_adjusted'] * props_df['decimal_odds']
    props_df = props_df.sort_values('ev', ascending=False)

    # Select starting prop with some randomness
    start_idx = min(np.random.geometric(0.3) - 1, len(props_df) - 1)
    selected_indices = [start_idx]
    selected_props = [props_df.iloc[start_idx]]

    # Greedy construction: add legs that maximize objective
    max_legs = min(constraints.max_legs, mode_config['max_legs'])

    for _ in range(max_legs - 1):
        best_idx = None
        best_score = -np.inf

        for idx in range(len(props_df)):
            if idx in selected_indices:
                continue

            candidate_props = selected_props + [props_df.iloc[idx]]
            candidate_indices = selected_indices + [idx]

            # Check constraints
            if not _check_constraints(candidate_props, constraints, props_df):
                continue

            # Check correlation blocks
            if _has_blocked_correlation(candidate_indices, corr_matrix, threshold=0.75):
                continue

            # Compute objective score
            ev_score = props_df.iloc[idx]['ev']
            corr_penalty = _compute_correlation_penalty(
                candidate_indices, corr_matrix, mode_config['corr_penalty']
            )
            diversity_boost = _compute_diversity_boost(
                candidate_props, diversity_target
            )

            score = ev_score - corr_penalty + diversity_boost

            if score > best_score:
                best_score = score
                best_idx = idx

        if best_idx is None:
            break

        selected_indices.append(best_idx)
        selected_props.append(props_df.iloc[best_idx])

    # Require minimum legs
    if len(selected_indices) < constraints.min_legs:
        return None

    # Build slip legs
    legs = []
    for idx in selected_indices:
        prop = props_df.iloc[idx]
        leg = {
            'player_id': prop['player_id'],
            'player_name': prop['player_name'],
            'prop_type': prop['prop_type'],
            'line': prop['line'],
            'direction': 'over',
            'prob': float(prop['prob_adjusted']),
            'odds': float(prop['over_odds']),
            'team': prop.get('team', 'UNK'),
            'game_id': prop.get('game_id', 'UNK'),
            'position': prop.get('position', 'UNK')
        }
        legs.append(leg)

    # Compute slip metrics
    raw_win_prob = np.prod([leg['prob'] for leg in legs])
    total_odds = np.prod([_american_to_decimal(leg['odds']) for leg in legs])

    # Monte Carlo simulation for correlation adjustment
    mc_results = compute_correlation_adjusted_prob(
        legs, selected_indices, corr_matrix, props_df
    )

    adjusted_prob = mc_results['adjusted_prob']
    variance = mc_results['variance']
    var_95 = mc_results['var_95']

    # Check odds constraints
    if total_odds < constraints.min_total_odds or total_odds > constraints.max_total_odds:
        return None

    # Expected value
    ev = total_odds * adjusted_prob

    # Check minimum EV
    if ev < constraints.min_expected_value:
        return None

    # Kelly criterion bet sizing
    suggested_bet = calculate_kelly_stake(
        adjusted_prob, total_odds, bankroll, mode_config['kelly_fraction']
    )

    # Diversity score
    diversity_score = compute_diversity_score(legs)

    # Correlation notes
    corr_notes = _generate_correlation_notes(selected_indices, corr_matrix, props_df)

    return Slip(
        slip_id=str(uuid.uuid4())[:8],
        legs=legs,
        num_legs=len(legs),
        total_odds=float(total_odds),
        raw_win_prob=float(raw_win_prob),
        correlation_adjusted_prob=float(adjusted_prob),
        expected_value=float(ev),
        variance=float(variance),
        value_at_risk_95=float(var_95),
        suggested_bet=float(suggested_bet),
        risk_level=risk_mode,
        diversity_score=float(diversity_score),
        correlation_notes=corr_notes
    )


def _check_constraints(
    props: List[pd.Series],
    constraints: SlipConstraints,
    props_df: pd.DataFrame
) -> bool:
    """Check if props satisfy constraints."""
    # Max same game
    if 'game_id' in props[0]:
        game_counts = {}
        for prop in props:
            game_id = prop.get('game_id', 'UNK')
            game_counts[game_id] = game_counts.get(game_id, 0) + 1
        if max(game_counts.values()) > constraints.max_same_game_legs:
            return False

    # Max per team
    if 'team' in props[0]:
        team_counts = {}
        for prop in props:
            team = prop.get('team', 'UNK')
            team_counts[team] = team_counts.get(team, 0) + 1
        if max(team_counts.values()) > constraints.max_per_team:
            return False

    # Disallow same player same stat
    if constraints.disallow_same_player_same_stat:
        player_props = set()
        for prop in props:
            key = (prop['player_id'], prop['prop_type'])
            if key in player_props:
                return False
            player_props.add(key)

    return True


def _has_blocked_correlation(
    indices: List[int],
    corr_matrix: np.ndarray,
    threshold: float = 0.75
) -> bool:
    """Check if any pair has correlation above blocking threshold."""
    for i in range(len(indices)):
        for j in range(i + 1, len(indices)):
            if abs(corr_matrix[indices[i], indices[j]]) > threshold:
                return True
    return False


def _compute_correlation_penalty(
    indices: List[int],
    corr_matrix: np.ndarray,
    lambda_factor: float
) -> float:
    """Compute soft penalty for correlations."""
    penalty = 0.0
    for i in range(len(indices)):
        for j in range(i + 1, len(indices)):
            corr = abs(corr_matrix[indices[i], indices[j]])
            if corr > 0.35:
                penalty += lambda_factor * corr
    return penalty


def _compute_diversity_boost(
    props: List[pd.Series],
    diversity_target: float
) -> float:
    """Compute diversity boost for objective function."""
    if len(props) <= 1:
        return 0.0

    # Count unique teams, games, positions
    unique_teams = len(set(p.get('team', 'UNK') for p in props))
    unique_games = len(set(p.get('game_id', 'UNK') for p in props))
    unique_positions = len(set(p.get('position', 'UNK') for p in props))

    n_legs = len(props)
    diversity = (
        0.4 * (unique_teams / n_legs) +
        0.3 * (unique_games / n_legs) +
        0.3 * (unique_positions / n_legs)
    )

    # Boost based on target
    mu = diversity_target * 2.0  # Scale factor
    return mu * diversity


def compute_correlation_adjusted_prob(
    legs: List[dict],
    indices: List[int],
    corr_matrix: np.ndarray,
    props_df: pd.DataFrame,
    n_samples: int = 10000
) -> dict:
    """
    Monte Carlo simulation of correlated outcomes using Gaussian copula.

    Returns:
        dict with adjusted_prob, variance, var_95
    """
    n_props = len(legs)
    probs = np.array([leg['prob'] for leg in legs])

    # Extract correlation submatrix for selected props
    sub_corr = corr_matrix[np.ix_(indices, indices)]

    # Ensure positive semi-definite
    sub_corr = _make_positive_semidefinite(sub_corr)

    # Generate correlated normal samples via Cholesky decomposition
    try:
        L = np.linalg.cholesky(sub_corr)
        standard_normals = np.random.randn(n_samples, n_props)
        correlated_normals = standard_normals @ L.T
    except np.linalg.LinAlgError:
        # Fall back to eigenvalue decomposition
        eigenvalues, eigenvectors = np.linalg.eigh(sub_corr)
        eigenvalues = np.maximum(eigenvalues, 1e-10)
        L = eigenvectors @ np.diag(np.sqrt(eigenvalues))
        standard_normals = np.random.randn(n_samples, n_props)
        correlated_normals = standard_normals @ L.T

    # Transform to uniform via Gaussian CDF
    uniform_samples = norm.cdf(correlated_normals)

    # Transform to Bernoulli outcomes
    outcomes = (uniform_samples < probs[None, :]).astype(int)

    # All legs win
    all_win = np.all(outcomes == 1, axis=1)

    # Compute statistics
    adjusted_prob = np.mean(all_win)
    variance = np.var(all_win.astype(float))

    # Value at Risk (95th percentile loss)
    # For binary outcome: VaR is either 0 (lose entire bet) or 0 (win)
    # We calculate probability of loss
    prob_loss = 1 - adjusted_prob
    var_95 = prob_loss if prob_loss > 0.05 else 0.0

    return {
        'adjusted_prob': adjusted_prob,
        'variance': variance,
        'var_95': var_95
    }


def _make_positive_semidefinite(matrix: np.ndarray, epsilon: float = 1e-6) -> np.ndarray:
    """Ensure matrix is positive semi-definite."""
    eigenvalues, eigenvectors = np.linalg.eigh(matrix)
    eigenvalues = np.maximum(eigenvalues, epsilon)
    return eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T


def calculate_kelly_stake(
    prob: float,
    decimal_odds: float,
    bankroll: float,
    fraction: float
) -> float:
    """
    Kelly criterion with fractional Kelly for safety.

    Kelly fraction = (p * b - q) / b where b = decimal_odds - 1

    Args:
        prob: Win probability
        decimal_odds: Decimal odds (e.g., 6.5)
        bankroll: Total bankroll
        fraction: Fractional Kelly (0.25 = quarter Kelly)

    Returns:
        Suggested bet amount clamped to [$5, $50]
    """
    b = decimal_odds - 1
    q = 1 - prob

    # Kelly criterion
    if prob * b <= q:
        return 5.0  # Minimum bet

    kelly_fraction_raw = (prob * b - q) / b
    kelly_stake = kelly_fraction_raw * bankroll

    # Apply fractional Kelly
    suggested = kelly_stake * fraction

    # Clamp to reasonable range
    return float(np.clip(suggested, 5.0, 50.0))


def compute_diversity_score(legs: List[dict]) -> float:
    """
    Calculate diversity across teams/games/positions.

    Returns:
        Diversity score between 0 and 1
    """
    if len(legs) <= 1:
        return 1.0

    n_legs = len(legs)
    unique_teams = len(set(leg.get('team', 'UNK') for leg in legs))
    unique_games = len(set(leg.get('game_id', 'UNK') for leg in legs))
    unique_positions = len(set(leg.get('position', 'UNK') for leg in legs))

    diversity = (
        0.4 * (unique_teams / n_legs) +
        0.3 * (unique_games / n_legs) +
        0.3 * (unique_positions / n_legs)
    )

    return diversity


def _generate_correlation_notes(
    indices: List[int],
    corr_matrix: np.ndarray,
    props_df: pd.DataFrame
) -> List[str]:
    """Generate human-readable correlation warnings."""
    notes = []

    for i in range(len(indices)):
        for j in range(i + 1, len(indices)):
            corr = corr_matrix[indices[i], indices[j]]

            if abs(corr) > 0.5:
                prop1 = props_df.iloc[indices[i]]
                prop2 = props_df.iloc[indices[j]]

                direction = "positive" if corr > 0 else "negative"
                note = f"{direction.capitalize()} correlation ({corr:.2f}): {prop1['player_name']} {prop1['prop_type']} + {prop2['player_name']} {prop2['prop_type']}"
                notes.append(note)

    return notes


def _create_safer_alternative(
    slip: Slip,
    mode_config: dict,
    bankroll: float
) -> Optional[Slip]:
    """Create a safer variant by removing the lowest probability leg."""
    if slip.num_legs <= 2:
        return None

    # Find leg with lowest probability
    min_prob_idx = np.argmin([leg['prob'] for leg in slip.legs])

    # Create new slip without that leg
    safer_legs = [leg for i, leg in enumerate(slip.legs) if i != min_prob_idx]

    # Recalculate metrics
    raw_prob = np.prod([leg['prob'] for leg in safer_legs])
    total_odds = np.prod([_american_to_decimal(leg['odds']) for leg in safer_legs])

    # Assume similar correlation adjustment ratio
    adj_ratio = slip.correlation_adjusted_prob / slip.raw_win_prob
    adjusted_prob = raw_prob * adj_ratio

    ev = total_odds * adjusted_prob
    suggested_bet = calculate_kelly_stake(
        adjusted_prob, total_odds, bankroll, mode_config['kelly_fraction']
    )

    diversity = compute_diversity_score(safer_legs)

    return Slip(
        slip_id=slip.slip_id + "_safer",
        legs=safer_legs,
        num_legs=len(safer_legs),
        total_odds=float(total_odds),
        raw_win_prob=float(raw_prob),
        correlation_adjusted_prob=float(adjusted_prob),
        expected_value=float(ev),
        variance=slip.variance * 0.8,  # Estimate
        value_at_risk_95=1 - adjusted_prob,
        suggested_bet=float(suggested_bet),
        risk_level="conservative" if slip.risk_level == "balanced" else slip.risk_level,
        diversity_score=float(diversity),
        correlation_notes=[]
    )


def apply_what_if_adjustments(
    legs: List[dict],
    deltas: dict,
    corr_matrix: np.ndarray = None,
    indices: List[int] = None
) -> dict:
    """
    Adjust leg probabilities by delta dict and re-simulate.

    Args:
        legs: List of leg dicts from slip
        deltas: {leg_idx: delta_prob} e.g., {0: 0.05, 2: -0.03}
        corr_matrix: Optional correlation matrix for re-simulation
        indices: Optional indices into correlation matrix

    Returns:
        Updated slip metrics
    """
    adjusted_legs = []
    for i, leg in enumerate(legs):
        adj_leg = leg.copy()
        if i in deltas:
            delta = deltas[i]
            adj_leg['prob'] = np.clip(leg['prob'] + delta, 0.01, 0.99)
            adj_leg['adjusted'] = True
            adj_leg['adjustment'] = delta
        adjusted_legs.append(adj_leg)

    # Recalculate metrics
    raw_prob = np.prod([leg['prob'] for leg in adjusted_legs])
    total_odds = np.prod([_american_to_decimal(leg['odds']) for leg in adjusted_legs])

    # Re-run Monte Carlo if correlation matrix provided
    if corr_matrix is not None and indices is not None:
        mc_results = compute_correlation_adjusted_prob(
            adjusted_legs, indices, corr_matrix, None
        )
        adjusted_prob = mc_results['adjusted_prob']
        variance = mc_results['variance']
        var_95 = mc_results['var_95']
    else:
        # Simple adjustment
        adjusted_prob = raw_prob
        variance = raw_prob * (1 - raw_prob)
        var_95 = 1 - adjusted_prob

    ev = total_odds * adjusted_prob

    return {
        'legs': adjusted_legs,
        'num_legs': len(adjusted_legs),
        'total_odds': float(total_odds),
        'raw_win_prob': float(raw_prob),
        'correlation_adjusted_prob': float(adjusted_prob),
        'expected_value': float(ev),
        'variance': float(variance),
        'value_at_risk_95': float(var_95),
        'what_if_scenario': True
    }


def _american_to_decimal(american_odds: float) -> float:
    """Convert American odds to decimal odds."""
    if american_odds > 0:
        return (american_odds / 100) + 1
    else:
        return (100 / abs(american_odds)) + 1


# Legacy compatibility functions
def optimize_slips_legacy(
    props_df: pd.DataFrame,
    corr_matrix: np.ndarray,
    constraints: Optional[SlipConstraints] = None,
    bankroll: float = 100.0,
    diversity_target: float = 0.5,
    n_slips: int = 5
) -> List[Dict[str, Any]]:
    """
    Legacy convenience function for backward compatibility.
    """
    return optimize_slips(
        props_df=props_df,
        corr_matrix=corr_matrix,
        bankroll=bankroll,
        diversity_target=diversity_target,
        n_slips=n_slips,
        risk_mode="balanced"
    )


def apply_what_if_adjustments_legacy(
    slip: Dict[str, Any],
    adjustments: Dict[int, float]
) -> Dict[str, Any]:
    """
    Legacy what-if adjustment function.

    Args:
        slip: Slip dictionary
        adjustments: Dictionary mapping leg index to probability adjustment

    Returns:
        New slip with adjusted probabilities
    """
    adjusted_slip = slip.copy()
    adjusted_legs = [leg.copy() for leg in slip['legs']]

    new_total_prob = 1.0
    for i, leg in enumerate(adjusted_legs):
        if i in adjustments:
            adjustment = adjustments[i]
            leg['probability'] = np.clip(leg.get('probability', leg.get('prob', 0.5)) + adjustment, 0.01, 0.99)
            leg['adjusted'] = True
            leg['adjustment'] = adjustment
        new_total_prob *= leg.get('probability', leg.get('prob', 0.5))

    adjusted_slip['legs'] = adjusted_legs
    adjusted_slip['total_probability'] = new_total_prob
    adjusted_slip['raw_win_prob'] = new_total_prob
    adjusted_slip['expected_value'] = adjusted_slip.get('total_odds', 1.0) * new_total_prob
    adjusted_slip['what_if_scenario'] = True

    return adjusted_slip

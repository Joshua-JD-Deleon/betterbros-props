"""
Correlation estimation and copula modeling for prop dependencies.

This module provides sophisticated correlation modeling between NFL props
to improve parlay optimization and risk assessment. It uses rule-based
heuristics and Gaussian copulas for sampling correlated outcomes.
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from scipy.stats import norm
from scipy.linalg import cholesky, LinAlgError
import warnings


def estimate_correlations(props_df: pd.DataFrame) -> np.ndarray:
    """
    Estimate correlation matrix between props using rule-based heuristics.

    This is the primary entry point for correlation estimation. It delegates
    to build_correlation_matrix_rule_based() for the actual computation.

    Args:
        props_df: DataFrame with prop details including:
                 - player_id: Unique player identifier
                 - player_name: Player's name
                 - team: Team abbreviation (e.g., 'KC', 'BUF')
                 - position: Player position (e.g., 'QB', 'WR', 'RB')
                 - prop_type: Type of prop (e.g., 'passing_yards', 'receiving_yards')
                 - game_id: Unique game identifier
                 - opponent: Optional opposing team

    Returns:
        NxN correlation matrix as numpy array where N = len(props_df)
        - Diagonal elements are 1.0
        - Matrix is symmetric
        - Values range from -1 to 1

    Example:
        >>> props = pd.DataFrame({
        ...     'player_id': ['p1', 'p2'],
        ...     'player_name': ['Mahomes', 'Kelce'],
        ...     'team': ['KC', 'KC'],
        ...     'position': ['QB', 'TE'],
        ...     'prop_type': ['passing_yards', 'receiving_yards'],
        ...     'game_id': ['KC@BUF', 'KC@BUF']
        ... })
        >>> corr_matrix = estimate_correlations(props)
        >>> corr_matrix.shape
        (2, 2)
    """
    return build_correlation_matrix_rule_based(props_df)


def build_correlation_matrix_rule_based(props_df: pd.DataFrame) -> np.ndarray:
    """
    Build correlation matrix using NFL-specific heuristic rules.

    This is the primary method when historical outcomes aren't available.
    It uses domain knowledge about NFL player/team relationships to estimate
    realistic correlations.

    Correlation Rules:
    1. Same player, different stats: 0.3-0.5 (moderate positive)
    2. QB and his WRs/TEs: 0.4-0.6 (positive - QB success helps receivers)
    3. RBs on same team: -0.2 to -0.4 (negative - touches are zero-sum)
    4. Players on same team, same position: -0.1 to -0.3 (slight negative)
    5. Opposing team players: 0.0 to 0.2 (slight positive if shootout)
    6. Player and game total: 0.3-0.5 (positive)
    7. Different games: 0.0 (independent)
    8. Same game, different teams: 0.1-0.3 (positive if high-scoring)

    Args:
        props_df: DataFrame with prop details (see estimate_correlations)

    Returns:
        NxN symmetric correlation matrix
    """
    n_props = len(props_df)
    corr_matrix = np.eye(n_props)

    # Compute pairwise correlations
    for i in range(n_props):
        for j in range(i + 1, n_props):
            prop1 = props_df.iloc[i].to_dict()
            prop2 = props_df.iloc[j].to_dict()

            corr = get_correlation_between_props(prop1, prop2)

            corr_matrix[i, j] = corr
            corr_matrix[j, i] = corr

    # Ensure positive definiteness
    corr_matrix = adjust_correlation_matrix(corr_matrix)

    return corr_matrix


def get_correlation_between_props(prop1: dict, prop2: dict) -> float:
    """
    Calculate correlation between two props based on their relationship.

    Uses NFL-specific domain knowledge to estimate realistic correlations
    based on player relationships, team dynamics, and game context.

    Args:
        prop1: First prop as dict with keys: player_id, team, position,
               prop_type, game_id, etc.
        prop2: Second prop as dict with same structure

    Returns:
        Correlation value between -1 and 1

    Rules Applied:
    - Same player, different stats (e.g., Mahomes Pass Yds + Pass TDs): 0.45
    - QB and his WR/TE (same team): 0.50
    - QB and opposing WR: 0.15
    - Two WRs same team: -0.25 (competing for targets)
    - Two RBs same team: -0.35 (competing for carries)
    - RB and QB same team: 0.20 (game script correlation)
    - Player and team total: 0.40
    - Same game different teams: 0.20
    - Different games: 0.00

    Noise: ±0.05 added to avoid perfect patterns
    """
    # Extract fields with defaults
    player1_id = prop1.get('player_id', '')
    player2_id = prop2.get('player_id', '')
    team1 = prop1.get('team', '')
    team2 = prop2.get('team', '')
    position1 = prop1.get('position', '')
    position2 = prop2.get('position', '')
    prop_type1 = prop1.get('prop_type', '')
    prop_type2 = prop2.get('prop_type', '')
    game1 = prop1.get('game_id', '')
    game2 = prop2.get('game_id', '')

    # Add small random noise for variation
    noise = np.random.uniform(-0.05, 0.05)

    # Rule 1: Same player, different stats
    if player1_id and player2_id and player1_id == player2_id:
        base_corr = 0.45
        # Higher for closely related stats
        if _are_related_stats(prop_type1, prop_type2):
            base_corr = 0.55
        return np.clip(base_corr + noise, 0.3, 0.7)

    # Rule 7: Different games - independent
    if game1 and game2 and game1 != game2:
        return np.clip(0.0 + noise, -0.1, 0.1)

    # Same game rules
    if game1 and game2 and game1 == game2:
        same_team = (team1 == team2)

        # Rule 2: QB and his WR/TE
        if same_team and _is_qb_receiver_pair(position1, position2, prop_type1, prop_type2):
            return np.clip(0.50 + noise, 0.4, 0.6)

        # Rule 3: Two RBs same team (competing for carries)
        if same_team and position1 == 'RB' and position2 == 'RB':
            return np.clip(-0.35 + noise, -0.45, -0.25)

        # Rule 4: Competing receivers (WR/WR, TE/TE, or WR/TE same team)
        if same_team and position1 in ['WR', 'TE'] and position2 in ['WR', 'TE']:
            return np.clip(-0.25 + noise, -0.35, -0.15)

        # Rule: RB and QB same team (positive game script)
        if same_team and ((position1 == 'RB' and position2 == 'QB') or
                         (position1 == 'QB' and position2 == 'RB')):
            return np.clip(0.20 + noise, 0.10, 0.30)
        # Rule 5: Opposing team players (shootout effect)
        if not same_team:
            # Higher correlation for skill positions in potential shootouts
            if position1 in ['QB', 'WR', 'TE', 'RB'] and position2 in ['QB', 'WR', 'TE', 'RB']:
                return np.clip(0.15 + noise, 0.05, 0.25)
            return np.clip(0.10 + noise, 0.0, 0.2)

        # Rule 8: Same game, same team (general positive)
        if same_team:
            return np.clip(0.20 + noise, 0.10, 0.30)

    # Default: very low correlation
    return np.clip(0.05 + noise, -0.05, 0.15)


def _are_related_stats(stat1: str, stat2: str) -> bool:
    """Check if two stat types are closely related."""
    related_groups = [
        {'passing_yards', 'passing_tds', 'pass_completions', 'pass_attempts'},
        {'receiving_yards', 'receiving_tds', 'receptions', 'targets'},
        {'rushing_yards', 'rushing_tds', 'rushing_attempts'},
        {'total_yards', 'all_purpose_yards'}
    ]

    for group in related_groups:
        if stat1 in group and stat2 in group:
            return True
    return False


def _is_qb_receiver_pair(pos1: str, pos2: str, stat1: str, stat2: str) -> bool:
    """Check if props represent a QB and his receiver."""
    # Check positions
    is_qb_wr = (pos1 == 'QB' and pos2 in ['WR', 'TE']) or \
               (pos2 == 'QB' and pos1 in ['WR', 'TE'])

    if not is_qb_wr:
        return False

    # Check stat types (passing stats paired with receiving stats)
    passing_stats = {'passing_yards', 'passing_tds', 'pass_completions', 'pass_attempts'}
    receiving_stats = {'receiving_yards', 'receiving_tds', 'receptions', 'targets'}

    is_passing_receiving = (stat1 in passing_stats and stat2 in receiving_stats) or \
                           (stat2 in passing_stats and stat1 in receiving_stats)

    return is_passing_receiving


def build_correlation_matrix_copula(
    historical_outcomes: pd.DataFrame,
    method: str = "gaussian"
) -> np.ndarray:
    """
    Fit copula to historical prop outcomes and estimate correlations.

    This method uses actual historical data to learn correlation patterns.
    Currently a stub that will return empirical correlations.

    Args:
        historical_outcomes: DataFrame with columns = prop_ids, rows = weeks,
                            values = 1 (hit) or 0 (miss)
        method: Copula type - "gaussian" | "t" | "clayton"

    Returns:
        Correlation matrix estimated from copula or empirical data

    Note: Full copula implementation requires the 'copulas' library.
          This stub computes empirical correlation as fallback.
    """
    if len(historical_outcomes) < 10:
        warnings.warn("Insufficient historical data for copula fitting. Need at least 10 samples.")
        n_props = historical_outcomes.shape[1]
        return np.eye(n_props)

    # Compute empirical correlation
    try:
        corr_matrix = historical_outcomes.corr().values

        # Ensure valid correlation matrix
        corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
        np.fill_diagonal(corr_matrix, 1.0)

        # Ensure symmetry
        corr_matrix = (corr_matrix + corr_matrix.T) / 2

        # Ensure positive definiteness
        corr_matrix = adjust_correlation_matrix(corr_matrix)

        return corr_matrix

    except Exception as e:
        warnings.warn(f"Failed to compute empirical correlation: {e}")
        n_props = historical_outcomes.shape[1]
        return np.eye(n_props)


def sample_correlated_outcomes(
    probabilities: np.ndarray,
    correlation_matrix: np.ndarray,
    n_samples: int = 10000,
    method: str = "gaussian_copula"
) -> np.ndarray:
    """
    Sample correlated Bernoulli outcomes using Gaussian copula.

    This is the core function for Monte Carlo simulation of correlated
    prop outcomes. It uses the copula approach to properly model
    dependencies between binary outcomes.

    Algorithm:
    1. Use Gaussian copula approach:
       - Apply Cholesky decomposition of correlation matrix
       - Sample from multivariate normal
       - Transform to uniforms via normal CDF
       - Apply inverse Bernoulli CDF (threshold at probability)
    2. Fallback to independent sampling if matrix not positive definite

    Args:
        probabilities: Array of individual hit probabilities [N]
        correlation_matrix: NxN correlation matrix
        n_samples: Number of Monte Carlo samples
        method: Sampling method - "gaussian_copula" | "cholesky" | "independent"

    Returns:
        (n_samples, N) array of binary outcomes (0 or 1)

    Example:
        >>> probs = np.array([0.6, 0.7, 0.55])
        >>> corr = np.eye(3)
        >>> outcomes = sample_correlated_outcomes(probs, corr, n_samples=1000)
        >>> outcomes.shape
        (1000, 3)
        >>> np.all((outcomes == 0) | (outcomes == 1))
        True
    """
    n_props = len(probabilities)

    # Validate inputs
    if correlation_matrix.shape != (n_props, n_props):
        raise ValueError(f"Correlation matrix shape {correlation_matrix.shape} doesn't match "
                        f"probabilities length {n_props}")

    if not np.allclose(correlation_matrix, correlation_matrix.T):
        warnings.warn("Correlation matrix not symmetric. Symmetrizing...")
        correlation_matrix = (correlation_matrix + correlation_matrix.T) / 2

    # Ensure positive definiteness
    correlation_matrix = _make_positive_definite(correlation_matrix)

    # Method 1: Gaussian copula with Cholesky (preferred)
    if method in ["gaussian_copula", "cholesky"]:
        try:
            # Cholesky decomposition
            L = cholesky(correlation_matrix, lower=True)

            # Sample standard normal
            standard_normals = np.random.randn(n_samples, n_props)

            # Apply correlation structure
            correlated_normals = standard_normals @ L.T

            # Transform to uniform via Gaussian CDF
            uniform_samples = norm.cdf(correlated_normals)

            # Transform to Bernoulli via inverse CDF (threshold)
            outcomes = (uniform_samples < probabilities[None, :]).astype(int)

            return outcomes

        except LinAlgError as e:
            warnings.warn(f"Cholesky decomposition failed: {e}. Using eigenvalue method.")

    # Method 2: Eigenvalue decomposition fallback
    try:
        eigenvalues, eigenvectors = np.linalg.eigh(correlation_matrix)
        eigenvalues = np.maximum(eigenvalues, 1e-10)  # Ensure positive
        L = eigenvectors @ np.diag(np.sqrt(eigenvalues))

        standard_normals = np.random.randn(n_samples, n_props)
        correlated_normals = standard_normals @ L.T
        uniform_samples = norm.cdf(correlated_normals)
        outcomes = (uniform_samples < probabilities[None, :]).astype(int)

        return outcomes

    except Exception as e:
        warnings.warn(f"Correlated sampling failed: {e}. Falling back to independent sampling.")

    # Method 3: Independent sampling fallback
    outcomes = np.random.binomial(1, probabilities[None, :], size=(n_samples, n_props))
    return outcomes


def validate_correlation_matrix(corr_matrix: np.ndarray) -> dict:
    """
    Validate correlation matrix properties and diagnose issues.

    Checks:
    - Symmetry
    - Diagonal elements = 1.0
    - Values in [-1, 1]
    - Positive definiteness (all eigenvalues >= 0)

    Args:
        corr_matrix: NxN correlation matrix to validate

    Returns:
        Dictionary with validation results:
        {
            'is_valid': bool - Overall validity
            'is_symmetric': bool - Matrix is symmetric
            'is_positive_definite': bool - All eigenvalues positive
            'diagonal_correct': bool - Diagonal elements are 1.0
            'values_in_range': bool - All values in [-1, 1]
            'min_eigenvalue': float - Smallest eigenvalue
            'max_correlation': float - Largest off-diagonal correlation
            'issues': List[str] - Human-readable issue descriptions
        }
    """
    issues = []

    # Check square matrix
    if corr_matrix.ndim != 2 or corr_matrix.shape[0] != corr_matrix.shape[1]:
        issues.append("Matrix is not square")
        return {
            'is_valid': False,
            'is_symmetric': False,
            'is_positive_definite': False,
            'diagonal_correct': False,
            'values_in_range': False,
            'min_eigenvalue': None,
            'max_correlation': None,
            'issues': issues
        }

    # Check symmetry
    is_symmetric = np.allclose(corr_matrix, corr_matrix.T)
    if not is_symmetric:
        issues.append("Matrix is not symmetric")

    # Check diagonal
    diagonal_correct = np.allclose(np.diag(corr_matrix), 1.0)
    if not diagonal_correct:
        issues.append("Diagonal elements are not all 1.0")

    # Check value range
    values_in_range = np.all((corr_matrix >= -1.0) & (corr_matrix <= 1.0))
    if not values_in_range:
        issues.append("Contains values outside [-1, 1] range")

    # Check positive definiteness
    try:
        eigenvalues = np.linalg.eigvalsh(corr_matrix)
        min_eigenvalue = float(np.min(eigenvalues))
        is_positive_definite = min_eigenvalue >= -1e-10  # Small tolerance

        if not is_positive_definite:
            issues.append(f"Matrix is not positive definite (min eigenvalue: {min_eigenvalue:.6f})")
    except np.linalg.LinAlgError:
        min_eigenvalue = None
        is_positive_definite = False
        issues.append("Failed to compute eigenvalues")

    # Find max correlation
    n = corr_matrix.shape[0]
    if n > 1:
        off_diagonal = corr_matrix[~np.eye(n, dtype=bool)]
        max_correlation = float(np.max(np.abs(off_diagonal)))

        if max_correlation > 0.95:
            issues.append(f"Very high correlation detected: {max_correlation:.3f}")
    else:
        max_correlation = 0.0

    # Overall validity
    is_valid = (is_symmetric and diagonal_correct and values_in_range and is_positive_definite)

    return {
        'is_valid': is_valid,
        'is_symmetric': is_symmetric,
        'is_positive_definite': is_positive_definite,
        'diagonal_correct': diagonal_correct,
        'values_in_range': values_in_range,
        'min_eigenvalue': min_eigenvalue,
        'max_correlation': max_correlation,
        'issues': issues
    }


def adjust_correlation_matrix(
    corr_matrix: np.ndarray,
    min_eigenvalue: float = 0.0001
) -> np.ndarray:
    """
    Adjust correlation matrix to ensure positive definiteness.

    Uses eigenvalue clipping to make the matrix positive definite while
    preserving as much of the correlation structure as possible.

    Algorithm:
    1. Compute eigenvalue decomposition
    2. Clip negative eigenvalues to min_eigenvalue
    3. Reconstruct matrix
    4. Rescale to ensure diagonal = 1.0

    Args:
        corr_matrix: NxN correlation matrix (possibly not positive definite)
        min_eigenvalue: Minimum allowed eigenvalue (default: 0.0001)

    Returns:
        Adjusted positive definite correlation matrix
    """
    try:
        # Ensure symmetry first
        corr_matrix = (corr_matrix + corr_matrix.T) / 2

        # Eigenvalue decomposition
        eigenvalues, eigenvectors = np.linalg.eigh(corr_matrix)

        # Clip eigenvalues
        eigenvalues_clipped = np.maximum(eigenvalues, min_eigenvalue)

        # Reconstruct matrix
        adjusted_matrix = eigenvectors @ np.diag(eigenvalues_clipped) @ eigenvectors.T

        # Rescale to ensure diagonal is 1.0
        d = np.sqrt(np.diag(adjusted_matrix))
        d[d < 1e-10] = 1.0  # Avoid division by zero

        adjusted_matrix = adjusted_matrix / d[:, None] / d[None, :]

        # Final symmetrization
        adjusted_matrix = (adjusted_matrix + adjusted_matrix.T) / 2

        # Ensure diagonal is exactly 1.0
        np.fill_diagonal(adjusted_matrix, 1.0)

        return adjusted_matrix

    except np.linalg.LinAlgError:
        warnings.warn("Failed to adjust correlation matrix. Returning identity.")
        return np.eye(corr_matrix.shape[0])


def _make_positive_definite(matrix: np.ndarray, epsilon: float = 1e-6) -> np.ndarray:
    """
    Internal helper to ensure matrix is positive definite.
    Similar to adjust_correlation_matrix but with different default parameters.
    """
    return adjust_correlation_matrix(matrix, min_eigenvalue=epsilon)


def detect_high_correlations(
    props_df: pd.DataFrame,
    corr_matrix: np.ndarray,
    threshold: float = 0.5
) -> List[dict]:
    """
    Find pairs of props with high correlation (positive or negative).

    Useful for identifying risky parlay combinations or finding
    complementary props for diversification.

    Args:
        props_df: DataFrame with prop details (must have player_name, prop_type)
        corr_matrix: NxN correlation matrix
        threshold: Minimum absolute correlation to report (default: 0.5)

    Returns:
        List of dicts with high correlation pairs:
        [
            {
                'prop_1': str,  # e.g., "Mahomes passing_yards"
                'prop_2': str,  # e.g., "Kelce receiving_yards"
                'correlation': float,  # e.g., 0.52
                'reason': str  # e.g., "Same team QB-WR"
            },
            ...
        ]
        Sorted by absolute correlation (highest first)
    """
    high_corr_pairs = []
    n_props = len(props_df)

    # Iterate over upper triangle (avoid duplicates)
    for i in range(n_props):
        for j in range(i + 1, n_props):
            corr = corr_matrix[i, j]

            if abs(corr) >= threshold:
                prop1 = props_df.iloc[i]
                prop2 = props_df.iloc[j]

                # Generate human-readable labels
                prop1_label = f"{prop1.get('player_name', 'Unknown')} {prop1.get('prop_type', '')}"
                prop2_label = f"{prop2.get('player_name', 'Unknown')} {prop2.get('prop_type', '')}"

                # Determine reason
                reason = _get_correlation_reason(prop1.to_dict(), prop2.to_dict(), corr)

                high_corr_pairs.append({
                    'prop_1': prop1_label,
                    'prop_2': prop2_label,
                    'correlation': float(corr),
                    'reason': reason
                })

    # Sort by absolute correlation
    high_corr_pairs.sort(key=lambda x: abs(x['correlation']), reverse=True)

    return high_corr_pairs


def _get_correlation_reason(prop1: dict, prop2: dict, corr: float) -> str:
    """Generate human-readable explanation for correlation."""
    player1 = prop1.get('player_id', '')
    player2 = prop2.get('player_id', '')
    team1 = prop1.get('team', '')
    team2 = prop2.get('team', '')
    pos1 = prop1.get('position', '')
    pos2 = prop2.get('position', '')
    game1 = prop1.get('game_id', '')
    game2 = prop2.get('game_id', '')

    corr_type = "Positive" if corr > 0 else "Negative"

    # Same player
    if player1 and player2 and player1 == player2:
        return f"{corr_type}: Same player, related stats"

    # Different games
    if game1 and game2 and game1 != game2:
        return "Independent: Different games"

    # Same game, same team
    if game1 == game2 and team1 == team2:
        if _is_qb_receiver_pair(pos1, pos2, prop1.get('prop_type', ''), prop2.get('prop_type', '')):
            return f"{corr_type}: Same team QB-WR/TE connection"
        if pos1 == 'RB' and pos2 == 'RB':
            return f"{corr_type}: Competing RBs (zero-sum carries)"
        if pos1 == pos2 and pos1 in ['WR', 'TE']:
            return f"{corr_type}: Same position competing for targets"
        return f"{corr_type}: Same team, same game"

    # Same game, different teams
    if game1 == game2 and team1 != team2:
        return f"{corr_type}: Same game, opposing teams (game script)"

    return f"{corr_type}: General correlation"


# Convenience class for backward compatibility
class CorrelationEstimator:
    """
    Object-oriented interface for correlation estimation.

    This class provides a stateful way to work with correlations,
    maintaining copula models and configuration.
    """

    def __init__(self, use_copulas: bool = True):
        """
        Initialize correlation estimator.

        Args:
            use_copulas: Whether to attempt copula fitting (currently uses fallback)
        """
        self.use_copulas = use_copulas
        self.copula_model = None
        self.fitted_corr_matrix = None

    def estimate_simple_correlations(self, props_df: pd.DataFrame) -> np.ndarray:
        """
        Estimate correlations using rule-based approach.

        Args:
            props_df: DataFrame with prop details

        Returns:
            NxN correlation matrix
        """
        return build_correlation_matrix_rule_based(props_df)

    def fit_copula_model(self, historical_outcomes: pd.DataFrame) -> None:
        """
        Fit copula model to historical data.

        Args:
            historical_outcomes: DataFrame with historical prop outcomes (0/1)
        """
        if not self.use_copulas:
            return

        # Compute and store empirical correlation
        self.fitted_corr_matrix = build_correlation_matrix_copula(historical_outcomes)

    def sample_correlated_outcomes(
        self,
        props_df: pd.DataFrame,
        n_samples: int = 10000
    ) -> np.ndarray:
        """
        Sample correlated outcomes for Monte Carlo simulation.

        Args:
            props_df: DataFrame with prob_over column
            n_samples: Number of samples to generate

        Returns:
            (n_samples, n_props) array of binary outcomes
        """
        probs = props_df['prob_over'].values

        # Use fitted correlation if available, otherwise estimate
        if self.fitted_corr_matrix is not None:
            corr_matrix = self.fitted_corr_matrix
        else:
            corr_matrix = self.estimate_simple_correlations(props_df)

        return sample_correlated_outcomes(probs, corr_matrix, n_samples)


# Additional helper for copula building (stub for future expansion)
def build_copula_model(
    historical_outcomes: pd.DataFrame,
    copula_type: str = "gaussian"
):
    """
    Build copula model from historical data.

    This is a stub for future expansion with full copula library support.
    Currently returns correlation matrix via empirical method.

    Args:
        historical_outcomes: DataFrame with historical prop outcomes
        copula_type: Type of copula ("gaussian", "t", "vine")

    Returns:
        Correlation matrix or None
    """
    if len(historical_outcomes) < 10:
        return None

    return build_correlation_matrix_copula(historical_outcomes, method=copula_type)

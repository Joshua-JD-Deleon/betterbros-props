"""
Correlation analysis module for prop legs using rank correlation methods

Implements empirical correlation estimation with domain-specific adjustments:
- Spearman rank correlation from historical residuals
- Same-game correlation boosts
- Same-player different-stat correlations
- Opposing-player negative correlations
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from redis.asyncio import Redis

from src.types import PropLeg
from src.db.session import get_redis_client

logger = logging.getLogger(__name__)


class CorrelationAnalyzer:
    """
    Analyzes and estimates correlation matrices for prop legs

    Uses historical data combined with domain knowledge to estimate
    pairwise correlations between prop legs.
    """

    def __init__(
        self,
        redis_client: Optional[Redis] = None,
        cache_ttl: int = 3600,
        min_sample_size: int = 10
    ):
        """
        Initialize correlation analyzer

        Args:
            redis_client: Redis client for caching (optional)
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
            min_sample_size: Minimum samples required for empirical correlation
        """
        self.redis_client = redis_client
        self.cache_ttl = cache_ttl
        self.min_sample_size = min_sample_size

        # Domain knowledge correlation adjustments
        self.same_game_boost = 0.4  # Correlation boost for props in same game
        self.same_player_correlations = {
            # NFL quarterback correlations
            ("passing_yards", "passing_tds"): 0.65,
            ("passing_yards", "completions"): 0.75,
            ("passing_tds", "completions"): 0.55,
            ("passing_attempts", "completions"): 0.85,

            # NFL running back correlations
            ("rushing_yards", "rushing_tds"): 0.60,
            ("rushing_yards", "carries"): 0.80,
            ("receptions", "receiving_yards"): 0.70,

            # NFL wide receiver correlations
            ("receptions", "receiving_yards"): 0.75,
            ("receptions", "receiving_tds"): 0.50,
            ("receiving_yards", "receiving_tds"): 0.55,

            # NBA player correlations
            ("points", "field_goals_made"): 0.85,
            ("points", "free_throws_made"): 0.60,
            ("rebounds", "minutes"): 0.55,
            ("assists", "minutes"): 0.50,
            ("points", "minutes"): 0.65,
            ("rebounds", "blocks"): 0.45,
            ("steals", "assists"): 0.35,

            # MLB pitcher correlations
            ("strikeouts", "innings_pitched"): 0.75,
            ("walks", "hits_allowed"): 0.40,

            # MLB batter correlations
            ("hits", "total_bases"): 0.80,
            ("hits", "rbis"): 0.50,
            ("home_runs", "rbis"): 0.60,
        }

        # Opposing player correlation (negative for QB vs opposing defense)
        self.opposing_player_penalty = -0.25

    async def estimate_correlation_matrix(
        self,
        props: List[PropLeg],
        snapshot_id: Optional[str] = None,
        use_cache: bool = True
    ) -> np.ndarray:
        """
        Estimate full correlation matrix for a list of prop legs

        Args:
            props: List of prop legs to analyze
            snapshot_id: Optional snapshot ID for cache keying
            use_cache: Whether to use Redis cache

        Returns:
            Correlation matrix (n_props x n_props) as numpy array
        """
        n_props = len(props)

        if n_props == 0:
            return np.array([[]])

        if n_props == 1:
            return np.array([[1.0]])

        # Try to load from cache
        if use_cache and self.redis_client and snapshot_id:
            cache_key = self._get_cache_key(snapshot_id)
            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    logger.info(f"Loaded correlation matrix from cache: {cache_key}")
                    # Deserialize numpy array from bytes
                    corr_matrix = np.frombuffer(eval(cached), dtype=np.float64).reshape(n_props, n_props)
                    return corr_matrix
            except Exception as e:
                logger.warning(f"Failed to load from cache: {e}")

        # Build correlation matrix
        corr_matrix = np.eye(n_props)  # Start with identity matrix

        for i in range(n_props):
            for j in range(i + 1, n_props):
                correlation = await self._estimate_pairwise_correlation(
                    props[i], props[j]
                )
                corr_matrix[i, j] = correlation
                corr_matrix[j, i] = correlation  # Symmetric matrix

        # Ensure matrix is positive semi-definite
        corr_matrix = self._ensure_positive_semidefinite(corr_matrix)

        # Cache the result
        if use_cache and self.redis_client and snapshot_id:
            cache_key = self._get_cache_key(snapshot_id)
            try:
                # Serialize numpy array to bytes
                await self.redis_client.setex(
                    cache_key,
                    self.cache_ttl,
                    str(corr_matrix.tobytes())
                )
                logger.info(f"Cached correlation matrix: {cache_key}")
            except Exception as e:
                logger.warning(f"Failed to cache correlation matrix: {e}")

        return corr_matrix

    async def _estimate_pairwise_correlation(
        self,
        leg_a: PropLeg,
        leg_b: PropLeg
    ) -> float:
        """
        Estimate correlation between two prop legs

        Combines empirical correlation from historical data with
        domain-specific adjustments.

        Args:
            leg_a: First prop leg
            leg_b: Second prop leg

        Returns:
            Correlation coefficient between -1 and 1
        """
        # Start with base empirical correlation
        base_correlation = 0.0

        # Try to get empirical correlation from historical data
        empirical_corr = await self._get_empirical_correlation(leg_a, leg_b)
        if empirical_corr is not None:
            base_correlation = empirical_corr

        # Apply domain-specific adjustments
        adjusted_correlation = base_correlation

        # Same game boost
        if leg_a.game_id == leg_b.game_id:
            adjusted_correlation += self.same_game_boost
            logger.debug(
                f"Same game boost: {leg_a.player_name} vs {leg_b.player_name} "
                f"(+{self.same_game_boost})"
            )

        # Same player, different stats
        if leg_a.player_id == leg_b.player_id and leg_a.stat_type != leg_b.stat_type:
            stat_pair = self._normalize_stat_pair(leg_a.stat_type, leg_b.stat_type)
            if stat_pair in self.same_player_correlations:
                known_corr = self.same_player_correlations[stat_pair]
                # Blend with empirical correlation if available
                if empirical_corr is not None:
                    adjusted_correlation = 0.6 * known_corr + 0.4 * empirical_corr
                else:
                    adjusted_correlation = known_corr
                logger.debug(
                    f"Same player correlation: {leg_a.player_name} "
                    f"{leg_a.stat_type} vs {leg_b.stat_type} = {adjusted_correlation:.3f}"
                )

        # Opposing players (QB vs opposing defense, etc.)
        if self._are_opposing_players(leg_a, leg_b):
            adjusted_correlation += self.opposing_player_penalty
            logger.debug(
                f"Opposing player penalty: {leg_a.player_name} vs {leg_b.player_name} "
                f"({self.opposing_player_penalty})"
            )

        # Clamp to valid correlation range
        adjusted_correlation = np.clip(adjusted_correlation, -1.0, 1.0)

        return adjusted_correlation

    async def _get_empirical_correlation(
        self,
        leg_a: PropLeg,
        leg_b: PropLeg
    ) -> Optional[float]:
        """
        Calculate empirical Spearman rank correlation from historical data

        This would typically query a database for historical residuals
        (actual - predicted) for both props and compute rank correlation.

        Args:
            leg_a: First prop leg
            leg_b: Second prop leg

        Returns:
            Spearman correlation coefficient or None if insufficient data
        """
        # TODO: Implement database query for historical residuals
        # For now, return None to use domain knowledge only

        # Placeholder for future implementation:
        # 1. Query historical performances for both players/stats
        # 2. Filter to common games/dates (last N games)
        # 3. Calculate residuals: actual - predicted
        # 4. Compute Spearman rank correlation
        # 5. Return correlation if sample size >= min_sample_size

        # Example implementation structure:
        # residuals_a = await self._get_historical_residuals(leg_a)
        # residuals_b = await self._get_historical_residuals(leg_b)
        #
        # if len(residuals_a) >= self.min_sample_size:
        #     correlation, p_value = spearmanr(residuals_a, residuals_b)
        #     if p_value < 0.05:  # Significant correlation
        #         return correlation

        return None

    def _normalize_stat_pair(self, stat_a: str, stat_b: str) -> Tuple[str, str]:
        """
        Normalize stat pair to canonical order for lookup

        Args:
            stat_a: First stat type
            stat_b: Second stat type

        Returns:
            Tuple of (stat1, stat2) in canonical order
        """
        stats = sorted([stat_a.lower(), stat_b.lower()])
        return (stats[0], stats[1])

    def _are_opposing_players(self, leg_a: PropLeg, leg_b: PropLeg) -> bool:
        """
        Check if two prop legs involve opposing players

        Args:
            leg_a: First prop leg
            leg_b: Second prop leg

        Returns:
            True if players are on opposing teams in the same game
        """
        # Same game, different teams
        if leg_a.game_id != leg_b.game_id:
            return False

        if leg_a.team == leg_b.team:
            return False

        # Check for specific opposing matchups (QB vs opposing defense stats, etc.)
        # This could be expanded based on sport-specific logic
        return leg_a.team == leg_b.opponent and leg_b.team == leg_a.opponent

    def _ensure_positive_semidefinite(self, matrix: np.ndarray) -> np.ndarray:
        """
        Ensure correlation matrix is positive semi-definite

        Uses eigenvalue decomposition to fix any negative eigenvalues
        while preserving the correlation structure.

        Args:
            matrix: Correlation matrix

        Returns:
            Adjusted positive semi-definite matrix
        """
        # Check if already positive semi-definite
        eigenvalues = np.linalg.eigvalsh(matrix)
        if np.all(eigenvalues >= -1e-10):  # Allow small numerical errors
            return matrix

        logger.warning(
            f"Correlation matrix not positive semi-definite. "
            f"Min eigenvalue: {eigenvalues.min():.6f}. Adjusting..."
        )

        # Eigenvalue decomposition
        eigenvalues, eigenvectors = np.linalg.eigh(matrix)

        # Set negative eigenvalues to small positive value
        eigenvalues[eigenvalues < 0] = 1e-10

        # Reconstruct matrix
        adjusted_matrix = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T

        # Rescale to ensure diagonal is 1
        scaling = np.sqrt(np.diag(adjusted_matrix))
        adjusted_matrix = adjusted_matrix / scaling[:, None] / scaling[None, :]

        # Ensure symmetry
        adjusted_matrix = (adjusted_matrix + adjusted_matrix.T) / 2

        return adjusted_matrix

    def _get_cache_key(self, snapshot_id: str) -> str:
        """Generate Redis cache key for correlation matrix"""
        return f"correlation:matrix:{snapshot_id}"

    async def get_pairwise_correlation(
        self,
        leg_a: PropLeg,
        leg_b: PropLeg
    ) -> float:
        """
        Get correlation between two specific prop legs

        Args:
            leg_a: First prop leg
            leg_b: Second prop leg

        Returns:
            Correlation coefficient
        """
        return await self._estimate_pairwise_correlation(leg_a, leg_b)

    async def get_correlation_stats(
        self,
        props: List[PropLeg]
    ) -> Dict[str, float]:
        """
        Get summary statistics about correlation structure

        Args:
            props: List of prop legs

        Returns:
            Dictionary with correlation statistics
        """
        if len(props) < 2:
            return {
                "mean_correlation": 0.0,
                "max_correlation": 0.0,
                "min_correlation": 0.0,
                "median_correlation": 0.0,
            }

        corr_matrix = await self.estimate_correlation_matrix(props, use_cache=False)

        # Extract upper triangle (excluding diagonal)
        upper_triangle = corr_matrix[np.triu_indices_from(corr_matrix, k=1)]

        return {
            "mean_correlation": float(np.mean(upper_triangle)),
            "max_correlation": float(np.max(upper_triangle)),
            "min_correlation": float(np.min(upper_triangle)),
            "median_correlation": float(np.median(upper_triangle)),
            "std_correlation": float(np.std(upper_triangle)),
        }

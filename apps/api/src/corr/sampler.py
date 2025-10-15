"""
Correlated sampling for Monte Carlo simulation of prop outcomes

Generates correlated binary outcomes for prop legs using copulas,
with Redis caching for performance.
"""
import logging
import hashlib
import json
from typing import Dict, List, Optional

import numpy as np
from redis.asyncio import Redis
from scipy import stats

from src.types import PropLeg
from src.corr.copula import CopulaModel, CopulaType
from src.corr.correlation import CorrelationAnalyzer

logger = logging.getLogger(__name__)


class CorrelatedSampler:
    """
    Generates correlated samples for prop outcome simulation

    Uses copula models to preserve correlation structure when
    simulating binary outcomes for multiple correlated props.
    """

    def __init__(
        self,
        redis_client: Optional[Redis] = None,
        cache_ttl: int = 3600,
        copula_type: CopulaType = CopulaType.GAUSSIAN,
        random_seed: Optional[int] = None
    ):
        """
        Initialize correlated sampler

        Args:
            redis_client: Redis client for caching samples
            cache_ttl: Cache TTL in seconds (default: 1 hour)
            copula_type: Type of copula to use for sampling
            random_seed: Random seed for reproducibility
        """
        self.redis_client = redis_client
        self.cache_ttl = cache_ttl
        self.copula_type = copula_type
        self.random_seed = random_seed
        self.correlation_analyzer = CorrelationAnalyzer(
            redis_client=redis_client,
            cache_ttl=cache_ttl
        )

    async def generate_samples(
        self,
        props: List[PropLeg],
        probabilities: List[float],
        n_sims: int = 10000,
        correlation_matrix: Optional[np.ndarray] = None,
        use_cache: bool = True,
        cache_key_suffix: Optional[str] = None
    ) -> np.ndarray:
        """
        Generate correlated binary outcome samples for props

        Args:
            props: List of prop legs
            probabilities: Hit probabilities for each prop (must match props length)
            n_sims: Number of simulations to run
            correlation_matrix: Optional pre-computed correlation matrix
            use_cache: Whether to use Redis cache
            cache_key_suffix: Optional suffix for cache key (e.g., snapshot_id)

        Returns:
            Binary outcome array of shape (n_sims, n_props)
            where 1 = hit, 0 = miss

        Raises:
            ValueError: If probabilities length doesn't match props length
        """
        n_props = len(props)

        if len(probabilities) != n_props:
            raise ValueError(
                f"Probabilities length ({len(probabilities)}) must match "
                f"props length ({n_props})"
            )

        # Validate probabilities
        for i, p in enumerate(probabilities):
            if not 0 <= p <= 1:
                raise ValueError(
                    f"Probability at index {i} = {p} is not in [0, 1]"
                )

        # Handle edge cases
        if n_props == 0:
            return np.array([]).reshape(n_sims, 0)

        if n_props == 1:
            # Single prop - no correlation needed
            return self._generate_independent_samples(probabilities[0], n_sims)

        # Try to load from cache
        if use_cache and self.redis_client:
            cache_key = self._get_cache_key(
                props,
                probabilities,
                n_sims,
                correlation_matrix,
                cache_key_suffix
            )
            cached_samples = await self._load_from_cache(cache_key)
            if cached_samples is not None:
                logger.info(f"Loaded {n_sims} samples from cache: {cache_key}")
                return cached_samples

        # Get or compute correlation matrix
        if correlation_matrix is None:
            correlation_matrix = await self.correlation_analyzer.estimate_correlation_matrix(
                props,
                snapshot_id=cache_key_suffix
            )

        # Generate correlated samples
        samples = await self._generate_correlated_samples(
            probabilities,
            correlation_matrix,
            n_sims
        )

        # Cache the samples
        if use_cache and self.redis_client:
            cache_key = self._get_cache_key(
                props,
                probabilities,
                n_sims,
                correlation_matrix,
                cache_key_suffix
            )
            await self._save_to_cache(cache_key, samples)

        return samples

    async def _generate_correlated_samples(
        self,
        probabilities: List[float],
        correlation_matrix: np.ndarray,
        n_sims: int
    ) -> np.ndarray:
        """
        Generate correlated binary samples using copula

        Args:
            probabilities: Hit probabilities for each prop
            correlation_matrix: Correlation matrix
            n_sims: Number of simulations

        Returns:
            Binary outcome array (n_sims, n_props)
        """
        n_props = len(probabilities)

        # Fit copula from correlation matrix
        copula = CopulaModel(
            copula_type=self.copula_type,
            random_seed=self.random_seed
        )

        try:
            copula.fit_copula(
                correlation_matrix=correlation_matrix,
                variable_names=[f"prop_{i}" for i in range(n_props)]
            )
        except Exception as e:
            logger.error(f"Failed to fit copula: {e}. Using independent sampling.")
            return self._generate_independent_samples_multiple(probabilities, n_sims)

        # Sample from copula (returns uniform marginals)
        try:
            uniform_samples = copula.sample(n_sims, return_uniform=True)
        except Exception as e:
            logger.error(f"Failed to sample from copula: {e}. Using independent sampling.")
            return self._generate_independent_samples_multiple(probabilities, n_sims)

        # Transform uniform samples to binary outcomes using inverse CDF
        # For Bernoulli: outcome = 1 if u < p, else 0
        binary_samples = np.zeros((n_sims, n_props), dtype=int)

        for i, prob in enumerate(probabilities):
            binary_samples[:, i] = (uniform_samples[:, i] < prob).astype(int)

        # Log actual correlation for validation
        empirical_corr = np.corrcoef(binary_samples.T)
        logger.debug(
            f"Generated {n_sims} correlated samples. "
            f"Max correlation diff: {np.max(np.abs(empirical_corr - correlation_matrix)):.4f}"
        )

        return binary_samples

    def _generate_independent_samples(
        self,
        probability: float,
        n_sims: int
    ) -> np.ndarray:
        """
        Generate independent binary samples for single prop

        Args:
            probability: Hit probability
            n_sims: Number of simulations

        Returns:
            Binary outcome array of shape (n_sims, 1)
        """
        if self.random_seed is not None:
            np.random.seed(self.random_seed)

        samples = np.random.binomial(1, probability, size=(n_sims, 1))
        return samples

    def _generate_independent_samples_multiple(
        self,
        probabilities: List[float],
        n_sims: int
    ) -> np.ndarray:
        """
        Generate independent binary samples for multiple props (fallback)

        Args:
            probabilities: Hit probabilities
            n_sims: Number of simulations

        Returns:
            Binary outcome array of shape (n_sims, n_props)
        """
        if self.random_seed is not None:
            np.random.seed(self.random_seed)

        n_props = len(probabilities)
        samples = np.zeros((n_sims, n_props), dtype=int)

        for i, prob in enumerate(probabilities):
            samples[:, i] = np.random.binomial(1, prob, size=n_sims)

        return samples

    def _get_cache_key(
        self,
        props: List[PropLeg],
        probabilities: List[float],
        n_sims: int,
        correlation_matrix: Optional[np.ndarray] = None,
        suffix: Optional[str] = None
    ) -> str:
        """
        Generate cache key for samples

        Cache key is based on:
        - Sorted prop IDs
        - Probabilities
        - Number of simulations
        - Correlation matrix hash
        - Optional suffix

        Args:
            props: List of prop legs
            probabilities: Hit probabilities
            n_sims: Number of simulations
            correlation_matrix: Correlation matrix (optional)
            suffix: Optional suffix (e.g., snapshot_id)

        Returns:
            Cache key string
        """
        # Sort prop IDs for consistent caching
        prop_ids = sorted([prop.id for prop in props])

        # Create dictionary for hashing
        key_data = {
            "prop_ids": prop_ids,
            "probabilities": [round(p, 6) for p in probabilities],
            "n_sims": n_sims,
        }

        if correlation_matrix is not None:
            # Hash correlation matrix
            corr_hash = hashlib.md5(
                correlation_matrix.tobytes()
            ).hexdigest()[:16]
            key_data["corr_hash"] = corr_hash

        if suffix:
            key_data["suffix"] = suffix

        # Create hash of key data
        key_json = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.sha256(key_json.encode()).hexdigest()[:32]

        return f"samples:{key_hash}"

    async def _load_from_cache(self, cache_key: str) -> Optional[np.ndarray]:
        """
        Load samples from Redis cache

        Args:
            cache_key: Cache key

        Returns:
            Cached samples or None if not found
        """
        try:
            cached = await self.redis_client.get(cache_key)
            if cached:
                # Deserialize
                samples_dict = json.loads(cached)
                samples = np.array(samples_dict["samples"], dtype=int)
                return samples
            return None
        except Exception as e:
            logger.warning(f"Failed to load samples from cache: {e}")
            return None

    async def _save_to_cache(self, cache_key: str, samples: np.ndarray):
        """
        Save samples to Redis cache

        Args:
            cache_key: Cache key
            samples: Samples to cache
        """
        try:
            # Serialize samples
            samples_dict = {
                "samples": samples.tolist(),
                "shape": samples.shape,
            }
            await self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(samples_dict)
            )
            logger.info(f"Cached samples: {cache_key}")
        except Exception as e:
            logger.warning(f"Failed to cache samples: {e}")

    async def get_sample_statistics(
        self,
        samples: np.ndarray,
        props: List[PropLeg]
    ) -> Dict:
        """
        Compute statistics about generated samples

        Args:
            samples: Binary outcome array (n_sims, n_props)
            props: List of prop legs

        Returns:
            Dictionary with sample statistics
        """
        n_sims, n_props = samples.shape

        # Hit rates for each prop
        hit_rates = samples.mean(axis=0)

        # Empirical correlation
        empirical_corr = np.corrcoef(samples.T)

        # Parlay hit rates (all props hit)
        all_hit_rate = (samples.sum(axis=1) == n_props).mean()

        # Average number of hits
        avg_hits = samples.sum(axis=1).mean()

        return {
            "n_sims": n_sims,
            "n_props": n_props,
            "hit_rates": hit_rates.tolist(),
            "empirical_correlation": empirical_corr.tolist(),
            "all_props_hit_rate": float(all_hit_rate),
            "avg_props_hit": float(avg_hits),
            "prop_names": [f"{p.player_name} {p.stat_type}" for p in props],
        }

    async def validate_samples(
        self,
        samples: np.ndarray,
        target_probabilities: List[float],
        target_correlation: np.ndarray,
        tolerance: float = 0.05
    ) -> Dict:
        """
        Validate generated samples against targets

        Args:
            samples: Generated samples
            target_probabilities: Expected hit probabilities
            target_correlation: Expected correlation matrix
            tolerance: Tolerance for validation

        Returns:
            Validation results dictionary
        """
        # Empirical probabilities
        empirical_probs = samples.mean(axis=0)
        prob_errors = np.abs(empirical_probs - target_probabilities)

        # Empirical correlation
        empirical_corr = np.corrcoef(samples.T)
        corr_errors = np.abs(empirical_corr - target_correlation)

        # Remove diagonal from correlation errors
        np.fill_diagonal(corr_errors, 0)

        validation = {
            "probability_validation": {
                "target": target_probabilities,
                "empirical": empirical_probs.tolist(),
                "max_error": float(np.max(prob_errors)),
                "mean_error": float(np.mean(prob_errors)),
                "within_tolerance": bool(np.all(prob_errors <= tolerance)),
            },
            "correlation_validation": {
                "max_error": float(np.max(corr_errors)),
                "mean_error": float(np.mean(corr_errors)),
                "frobenius_norm": float(np.linalg.norm(corr_errors, ord='fro')),
                "within_tolerance": bool(np.all(corr_errors <= tolerance)),
            },
        }

        return validation

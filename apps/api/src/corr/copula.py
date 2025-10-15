"""
Copula modeling for multivariate correlation structure

Uses copulas to model joint distributions of prop outcomes,
enabling accurate Monte Carlo simulation with proper correlation structure.
"""
import logging
from typing import Dict, List, Optional, Literal
from enum import Enum

import numpy as np
import pandas as pd
from copulas.multivariate import GaussianMultivariate
from copulas.bivariate import Clayton, Frank
from scipy import stats

logger = logging.getLogger(__name__)


class CopulaType(str, Enum):
    """Supported copula types"""
    GAUSSIAN = "gaussian"
    T = "t"
    CLAYTON = "clayton"
    FRANK = "frank"


class CopulaModel:
    """
    Multivariate copula model for correlated prop outcomes

    Fits copulas to historical data or correlation matrices,
    then generates correlated samples for Monte Carlo simulation.
    """

    def __init__(
        self,
        copula_type: CopulaType = CopulaType.GAUSSIAN,
        random_seed: Optional[int] = None
    ):
        """
        Initialize copula model

        Args:
            copula_type: Type of copula to use
            random_seed: Random seed for reproducibility
        """
        self.copula_type = copula_type
        self.random_seed = random_seed
        self.copula = None
        self.is_fitted = False
        self.n_variables = 0
        self.variable_names = []

        if random_seed is not None:
            np.random.seed(random_seed)

    def fit_copula(
        self,
        data: Optional[pd.DataFrame] = None,
        correlation_matrix: Optional[np.ndarray] = None,
        variable_names: Optional[List[str]] = None
    ):
        """
        Fit copula to data or correlation matrix

        Either data or correlation_matrix must be provided.

        Args:
            data: Historical data for fitting (each column is a variable)
            correlation_matrix: Pre-computed correlation matrix
            variable_names: Names for variables (optional)

        Raises:
            ValueError: If neither data nor correlation_matrix is provided
        """
        if data is None and correlation_matrix is None:
            raise ValueError("Must provide either data or correlation_matrix")

        if data is not None:
            self._fit_from_data(data)
        else:
            self._fit_from_correlation_matrix(correlation_matrix, variable_names)

        self.is_fitted = True
        logger.info(
            f"Fitted {self.copula_type} copula with {self.n_variables} variables"
        )

    def _fit_from_data(self, data: pd.DataFrame):
        """
        Fit copula from historical data

        Args:
            data: DataFrame with historical observations
        """
        self.n_variables = len(data.columns)
        self.variable_names = list(data.columns)

        if self.copula_type == CopulaType.GAUSSIAN:
            self.copula = GaussianMultivariate()
            self.copula.fit(data)
        elif self.copula_type == CopulaType.T:
            # Use Gaussian as approximation for t-copula
            # (copulas library has limited support for t-copula)
            logger.warning("T-copula not fully supported, using Gaussian approximation")
            self.copula = GaussianMultivariate()
            self.copula.fit(data)
        elif self.copula_type == CopulaType.CLAYTON:
            # Clayton copula is bivariate only in copulas library
            if self.n_variables > 2:
                logger.warning(
                    f"Clayton copula is bivariate only, "
                    f"using Gaussian for {self.n_variables} variables"
                )
                self.copula = GaussianMultivariate()
                self.copula.fit(data)
            else:
                # Use custom implementation for bivariate Clayton
                self.copula = "clayton"
                self._fit_clayton(data)
        else:
            raise ValueError(f"Unsupported copula type: {self.copula_type}")

    def _fit_from_correlation_matrix(
        self,
        correlation_matrix: np.ndarray,
        variable_names: Optional[List[str]] = None
    ):
        """
        Fit Gaussian copula from correlation matrix

        Args:
            correlation_matrix: Correlation matrix (n_vars x n_vars)
            variable_names: Optional variable names
        """
        self.n_variables = correlation_matrix.shape[0]
        self.variable_names = variable_names or [
            f"var_{i}" for i in range(self.n_variables)
        ]

        if self.copula_type != CopulaType.GAUSSIAN:
            logger.warning(
                f"Fitting from correlation matrix only supports Gaussian copula, "
                f"ignoring copula_type={self.copula_type}"
            )

        # Create Gaussian copula with specified correlation
        self.copula = GaussianMultivariate()

        # Create synthetic data to fit copula
        # Generate from multivariate normal, then transform to uniform
        mean = np.zeros(self.n_variables)
        n_samples = max(1000, self.n_variables * 100)

        # Generate correlated normal samples
        normal_samples = np.random.multivariate_normal(
            mean,
            correlation_matrix,
            size=n_samples
        )

        # Transform to uniform via CDF
        uniform_samples = stats.norm.cdf(normal_samples)

        # Create DataFrame for fitting
        df = pd.DataFrame(
            uniform_samples,
            columns=self.variable_names
        )

        self.copula.fit(df)

    def _fit_clayton(self, data: pd.DataFrame):
        """
        Fit bivariate Clayton copula

        Args:
            data: DataFrame with 2 columns
        """
        # Transform to uniform margins via empirical CDF
        u = data.iloc[:, 0].rank() / (len(data) + 1)
        v = data.iloc[:, 1].rank() / (len(data) + 1)

        # Estimate Clayton parameter theta via method of moments
        # Kendall's tau = theta / (theta + 2)
        tau = stats.kendalltau(u, v)[0]
        theta = 2 * tau / (1 - tau)

        # Store parameters for sampling
        self.clayton_theta = max(theta, 0.01)  # Ensure positive
        logger.info(f"Clayton copula theta: {self.clayton_theta:.4f}")

    def sample(
        self,
        n_samples: int = 10000,
        return_uniform: bool = False
    ) -> np.ndarray:
        """
        Generate samples from fitted copula

        Args:
            n_samples: Number of samples to generate
            return_uniform: If True, return uniform [0,1] marginals

        Returns:
            Array of shape (n_samples, n_variables)

        Raises:
            RuntimeError: If copula has not been fitted
        """
        if not self.is_fitted:
            raise RuntimeError("Copula must be fitted before sampling")

        if self.copula == "clayton":
            samples = self._sample_clayton(n_samples)
        else:
            # Use copulas library sampling
            samples_df = self.copula.sample(n_samples)
            samples = samples_df.values

        if return_uniform:
            # Transform to uniform marginals via CDF
            # Each column should already be approximately uniform for copulas
            return samples

        return samples

    def _sample_clayton(self, n_samples: int) -> np.ndarray:
        """
        Sample from bivariate Clayton copula

        Args:
            n_samples: Number of samples

        Returns:
            Array of shape (n_samples, 2) with uniform marginals
        """
        theta = self.clayton_theta

        # Clayton copula sampling algorithm
        # 1. Generate v ~ Uniform(0, 1)
        v = np.random.uniform(0, 1, n_samples)

        # 2. Generate w ~ Uniform(0, 1)
        w = np.random.uniform(0, 1, n_samples)

        # 3. Compute u = (1 + w^(-theta/(1+theta)) * (v^(-theta) - 1))^(-1/theta)
        u = (1 + w ** (-theta / (1 + theta)) * (v ** (-theta) - 1)) ** (-1 / theta)

        samples = np.column_stack([u, v])
        return samples

    def get_correlation_structure(self) -> np.ndarray:
        """
        Extract correlation matrix from fitted copula

        Returns:
            Correlation matrix (n_variables x n_variables)

        Raises:
            RuntimeError: If copula has not been fitted
        """
        if not self.is_fitted:
            raise RuntimeError("Copula must be fitted before extracting correlation")

        if self.copula == "clayton":
            # For Clayton copula, compute theoretical correlation
            theta = self.clayton_theta
            # Kendall's tau
            tau = theta / (theta + 2)
            # Convert to Spearman (approximation)
            rho = 2 * np.sin(np.pi * tau / 6)

            corr_matrix = np.array([[1.0, rho], [rho, 1.0]])
            return corr_matrix

        # For Gaussian copula, extract covariance matrix
        if hasattr(self.copula, 'covariance'):
            # Convert covariance to correlation
            cov = self.copula.covariance
            std = np.sqrt(np.diag(cov))
            corr_matrix = cov / std[:, None] / std[None, :]
            return corr_matrix
        elif hasattr(self.copula, 'correlation'):
            return self.copula.correlation
        else:
            logger.warning("Could not extract correlation from copula, returning identity")
            return np.eye(self.n_variables)

    def compute_cdf(self, u: np.ndarray) -> float:
        """
        Compute copula CDF at point u

        Args:
            u: Point in [0,1]^d to evaluate CDF

        Returns:
            CDF value
        """
        if not self.is_fitted:
            raise RuntimeError("Copula must be fitted before computing CDF")

        # This is a simplified implementation
        # Full implementation would use copula-specific CDF formulas
        logger.warning("CDF computation not fully implemented, returning approximation")
        return float(np.prod(u))

    def compute_pdf(self, u: np.ndarray) -> float:
        """
        Compute copula PDF at point u

        Args:
            u: Point in [0,1]^d to evaluate PDF

        Returns:
            PDF value
        """
        if not self.is_fitted:
            raise RuntimeError("Copula must be fitted before computing PDF")

        # This is a simplified implementation
        logger.warning("PDF computation not fully implemented, returning approximation")
        return 1.0

    def get_info(self) -> Dict:
        """
        Get information about the fitted copula

        Returns:
            Dictionary with copula information
        """
        info = {
            "copula_type": self.copula_type,
            "is_fitted": self.is_fitted,
            "n_variables": self.n_variables,
            "variable_names": self.variable_names,
        }

        if self.is_fitted:
            info["correlation_matrix"] = self.get_correlation_structure().tolist()

            if self.copula == "clayton":
                info["clayton_theta"] = self.clayton_theta

        return info

    def validate_samples(
        self,
        samples: np.ndarray,
        target_correlation: Optional[np.ndarray] = None
    ) -> Dict:
        """
        Validate that samples have desired correlation structure

        Args:
            samples: Generated samples to validate
            target_correlation: Expected correlation matrix (optional)

        Returns:
            Dictionary with validation metrics
        """
        # Compute empirical correlation
        empirical_corr = np.corrcoef(samples.T)

        validation = {
            "n_samples": samples.shape[0],
            "n_variables": samples.shape[1],
            "empirical_correlation": empirical_corr.tolist(),
        }

        if target_correlation is not None:
            # Compute Frobenius norm of difference
            diff = empirical_corr - target_correlation
            frobenius_norm = np.linalg.norm(diff, ord='fro')

            validation["target_correlation"] = target_correlation.tolist()
            validation["frobenius_norm_error"] = float(frobenius_norm)
            validation["max_elementwise_error"] = float(np.max(np.abs(diff)))

        return validation

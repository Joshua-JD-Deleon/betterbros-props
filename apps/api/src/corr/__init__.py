"""
Correlation modeling system for prop analysis

Implements comprehensive correlation analysis using:
- Spearman rank correlation from historical data
- Domain-specific correlation adjustments
- Copula models for multivariate dependencies
- Correlated Monte Carlo sampling
- Constraint enforcement for parlay construction
"""
from src.corr.correlation import CorrelationAnalyzer
from src.corr.copula import CopulaModel, CopulaType
from src.corr.sampler import CorrelatedSampler
from src.corr.constraints import (
    CorrelationConstraints,
    CorrelationWarningLevel,
)

__all__ = [
    # Correlation analysis
    "CorrelationAnalyzer",

    # Copula modeling
    "CopulaModel",
    "CopulaType",

    # Sampling
    "CorrelatedSampler",

    # Constraints
    "CorrelationConstraints",
    "CorrelationWarningLevel",
]

__version__ = "1.0.0"

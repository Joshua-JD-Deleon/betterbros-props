"""
Correlation modeling module for NFL prop dependencies.

This module provides tools for estimating and working with correlations
between player props, enabling better parlay construction and risk assessment.
"""

from .correlation import (
    estimate_correlations,
    build_correlation_matrix_rule_based,
    build_correlation_matrix_copula,
    sample_correlated_outcomes,
    detect_high_correlations,
    validate_correlation_matrix,
    adjust_correlation_matrix,
    get_correlation_between_props,
    CorrelationEstimator,
    build_copula_model,
)

__all__ = [
    "estimate_correlations",
    "build_correlation_matrix_rule_based",
    "build_correlation_matrix_copula",
    "sample_correlated_outcomes",
    "detect_high_correlations",
    "validate_correlation_matrix",
    "adjust_correlation_matrix",
    "get_correlation_between_props",
    "CorrelationEstimator",
    "build_copula_model",
]

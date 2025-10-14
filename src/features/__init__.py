"""
Feature engineering and trend detection module.
"""

from .pipeline import (
    build_features,
    generate_trend_chips,
    FeaturePipeline,
    calculate_ewma,
    odds_to_probability,
    calculate_vig,
    detect_correlation_groups,
)

__all__ = [
    "build_features",
    "generate_trend_chips",
    "FeaturePipeline",
    "calculate_ewma",
    "odds_to_probability",
    "calculate_vig",
    "detect_correlation_groups",
]

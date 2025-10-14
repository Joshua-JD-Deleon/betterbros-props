"""
Portfolio optimization module.
"""

from .slip_opt import (
    optimize_slips,
    SlipConstraints,
    Slip,
    apply_what_if_adjustments,
    compute_correlation_adjusted_prob,
    calculate_kelly_stake,
    compute_diversity_score,
    # Legacy compatibility
    optimize_slips_legacy,
    apply_what_if_adjustments_legacy
)

__all__ = [
    "optimize_slips",
    "SlipConstraints",
    "Slip",
    "apply_what_if_adjustments",
    "compute_correlation_adjusted_prob",
    "calculate_kelly_stake",
    "compute_diversity_score",
    # Legacy
    "optimize_slips_legacy",
    "apply_what_if_adjustments_legacy",
]

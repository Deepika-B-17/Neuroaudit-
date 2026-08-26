"""
NeuroAudit Machine Learning & Empirical Validation Module (Phase 4 Scaffold).

Provides clean data structures and interfaces for dataset compilation,
epoch extraction, and leakage-free cross-validation for empirical privacy risk assessment.
"""

from .dataset_builder import feature_dict_to_vector, FEATURE_NAMES

__all__ = [
    "feature_dict_to_vector",
    "FEATURE_NAMES",
]

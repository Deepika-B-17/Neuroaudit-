"""
Dataset compilation and feature vector conversion utilities for NeuroAudit ML.

Maps the dictionary outputs of the Phase 2 feature extraction engine
into canonical fixed-length 1D numerical feature vectors (D=19).
"""

import numpy as np

# 19 canonical continuous feature names matching ML_FEATURE_SCHEMA.md
FEATURE_NAMES: list[str] = [
    "bp_delta_rel",
    "bp_theta_rel",
    "bp_alpha_rel",
    "bp_beta_rel",
    "bp_gamma_rel",
    "faa",
    "theta_beta_ratio",
    "theta_alpha_ratio",
    "engagement_index",
    "iapf_hz",
    "de_delta",
    "de_theta",
    "de_alpha",
    "de_beta",
    "de_gamma",
    "hjorth_activity",
    "hjorth_mobility",
    "hjorth_complexity",
    "bui",
]


def feature_dict_to_vector(features: dict) -> np.ndarray:
    """
    Convert output dictionary from extract_features_from_raw() into a 1D numpy float64 array of shape (19,).

    Parameters
    ----------
    features : dict
        Extracted features dictionary from pipeline.features.extract_features_from_raw.

    Returns
    -------
    np.ndarray
        1D array of length 19 with all values guaranteed finite.
    """
    bp = features.get("global_band_powers", {})
    de = features.get("differential_entropy", {})

    vector = [
        float(bp.get("delta", 20.0)),
        float(bp.get("theta", 20.0)),
        float(bp.get("alpha", 20.0)),
        float(bp.get("beta",  20.0)),
        float(bp.get("gamma", 20.0)),
        float(features.get("frontal_alpha_asymmetry", 0.0)),
        float(features.get("theta_beta_ratio", 1.0)),
        float(features.get("theta_alpha_ratio", 1.0)),
        float(features.get("engagement_index", 0.5)),
        float(features.get("iapf_hz", 10.0)),
        float(de.get("delta", 0.0)),
        float(de.get("theta", 0.0)),
        float(de.get("alpha", 0.0)),
        float(de.get("beta",  0.0)),
        float(de.get("gamma", 0.0)),
        float(features.get("hjorth_activity", 0.0)),
        float(features.get("hjorth_mobility", 1.0)),
        float(features.get("hjorth_complexity", 1.0)),
        float(features.get("biometric_uniqueness_index", 0.5)),
    ]

    arr = np.array(vector, dtype=np.float64)
    # Sanitize any unexpected non-finite elements with fallback 0.0
    arr = np.where(np.isnan(arr) | np.isinf(arr), 0.0, arr)
    return arr

"""
Unit tests for Baseline Risk Scoring & Aggregation Methodology (Phase 3).

Verifies boundary constraints, mathematical weighting, contributor attributions,
deterministic scoring, and resilience to degenerate / missing inputs.
"""

import os
import sys
import unittest
import numpy as np

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from pipeline.models import compute_dimension_risks
from pipeline.scoring import aggregate_privacy_risk


class TestBaselineRiskScoring(unittest.TestCase):
    """Test suite for Phase 3 Baseline Risk Methodology."""

    def setUp(self):
        self.sample_features = {
            "global_band_powers": {
                "delta": 15.0,
                "theta": 22.0,
                "alpha": 30.0,
                "beta": 20.0,
                "gamma": 13.0,
            },
            "frontal_alpha_asymmetry": 0.45,
            "theta_beta_ratio": 1.10,
            "theta_alpha_ratio": 0.73,
            "engagement_index": 0.38,
            "iapf_hz": 10.2,
            "differential_entropy": {
                "delta": 1.2,
                "theta": 1.5,
                "alpha": 2.1,
                "beta": 1.8,
                "gamma": 1.0,
            },
            "hjorth_activity": 0.00015,
            "hjorth_mobility": 0.12,
            "hjorth_complexity": 1.35,
            "biometric_uniqueness_index": 0.85,
            "channel_count": 8,
            "sampling_rate": 250.0,
            "duration_sec": 60.0,
        }
        self.sample_metadata = {
            "n_channels": 8,
            "duration_sec": 60.0,
            "sfreq": 250.0,
            "quality_report": {"sufficient_for_assessment": True},
        }

    def test_dimension_score_bounds_and_structure(self):
        """Test that all 4 dimensions produce scores within [0, 100] and expected keys."""
        dims = compute_dimension_risks(self.sample_features, self.sample_metadata)
        self.assertEqual(len(dims), 4)

        dim_keys = [d["key"] for d in dims]
        self.assertEqual(dim_keys, ["identity", "emotion", "stress", "workload"])

        for dim in dims:
            self.assertIn("score", dim)
            self.assertIn("level", dim)
            self.assertIn("contributors", dim)
            self.assertIn("contributing_indicators", dim)
            self.assertIn(dim["level"], ["LOW", "MEDIUM", "HIGH"])
            self.assertGreaterEqual(dim["score"], 0)
            self.assertLessEqual(dim["score"], 100)
            self.assertTrue(np.isfinite(dim["score"]))

    def test_contributor_breakdown_math(self):
        """Test that structured contributors match the actual dimension formulas."""
        dims = compute_dimension_risks(self.sample_features, self.sample_metadata)
        dim_map = {d["key"]: d for d in dims}

        # 1. Identity
        id_dim = dim_map["identity"]
        id_contrib_sum = sum(c["contribution"] for c in id_dim["contributors"])
        expected_id_score = int(np.clip(round(id_contrib_sum), 20, 96))
        self.assertEqual(id_dim["score"], expected_id_score)

        # 2. Emotion
        em_dim = dim_map["emotion"]
        em_contrib_sum = sum(c["contribution"] for c in em_dim["contributors"])
        expected_em_score = int(np.clip(round(em_contrib_sum), 18, 94))
        self.assertEqual(em_dim["score"], expected_em_score)

        # 3. Stress
        st_dim = dim_map["stress"]
        st_contrib_sum = sum(c["contribution"] for c in st_dim["contributors"])
        expected_st_score = int(np.clip(round(st_contrib_sum), 15, 95))
        self.assertEqual(st_dim["score"], expected_st_score)

        # 4. Workload
        wl_dim = dim_map["workload"]
        wl_contrib_sum = sum(c["contribution"] for c in wl_dim["contributors"])
        expected_wl_score = int(np.clip(round(wl_contrib_sum), 15, 95))
        self.assertEqual(wl_dim["score"], expected_wl_score)

    def test_overall_composite_risk_weighting(self):
        """Test exact linear weighting: 30% ID + 25% EM + 25% ST + 20% WL clipped to [10, 98]."""
        dims = compute_dimension_risks(self.sample_features, self.sample_metadata)
        dim_map = {d["key"]: d for d in dims}

        summary = aggregate_privacy_risk(dims, self.sample_features, self.sample_metadata)
        overall = summary["overallRisk"]

        id_score = dim_map["identity"]["score"]
        em_score = dim_map["emotion"]["score"]
        st_score = dim_map["stress"]["score"]
        wl_score = dim_map["workload"]["score"]

        expected_weighted = int(round(
            0.30 * id_score +
            0.25 * em_score +
            0.25 * st_score +
            0.20 * wl_score
        ))
        expected_overall = max(10, min(98, expected_weighted))

        self.assertEqual(overall, expected_overall)
        self.assertGreaterEqual(overall, 10)
        self.assertLessEqual(overall, 98)

    def test_empty_and_missing_features_fallback(self):
        """Test scoring with empty features dict does not crash and yields valid bounded scores."""
        empty_features = {}
        empty_metadata = {}
        dims = compute_dimension_risks(empty_features, empty_metadata)
        self.assertEqual(len(dims), 4)

        for dim in dims:
            self.assertTrue(np.isfinite(dim["score"]))
            self.assertGreaterEqual(dim["score"], 0)
            self.assertLessEqual(dim["score"], 100)

        summary = aggregate_privacy_risk(dims, empty_features, empty_metadata)
        self.assertTrue(np.isfinite(summary["overallRisk"]))
        self.assertIn(summary["riskLevel"], ["LOW", "MEDIUM", "HIGH"])

    def test_extreme_and_zero_values(self):
        """Test extreme/zero feature values produce safe finite bounded scores."""
        extreme_features = {
            "global_band_powers": {"delta": 0.0, "theta": 0.0, "alpha": 0.0, "beta": 100.0, "gamma": 0.0},
            "frontal_alpha_asymmetry": 100.0,
            "theta_beta_ratio": 0.0,
            "theta_alpha_ratio": 0.0,
            "engagement_index": 10.0,
            "iapf_hz": 0.0,
            "hjorth_complexity": 50.0,
            "biometric_uniqueness_index": 10.0,
            "channel_count": 128,
            "duration_sec": 3600.0,
        }
        dims = compute_dimension_risks(extreme_features, self.sample_metadata)
        for dim in dims:
            self.assertTrue(np.isfinite(dim["score"]))
            self.assertGreaterEqual(dim["score"], 0)
            self.assertLessEqual(dim["score"], 100)

        summary = aggregate_privacy_risk(dims, extreme_features, self.sample_metadata)
        self.assertGreaterEqual(summary["overallRisk"], 10)
        self.assertLessEqual(summary["overallRisk"], 98)

    def test_deterministic_scoring(self):
        """Test that same inputs produce bit-exact identical score outputs."""
        dims1 = compute_dimension_risks(self.sample_features, self.sample_metadata)
        dims2 = compute_dimension_risks(self.sample_features, self.sample_metadata)
        self.assertEqual(dims1, dims2)

        sum1 = aggregate_privacy_risk(dims1, self.sample_features, self.sample_metadata)
        sum2 = aggregate_privacy_risk(dims2, self.sample_features, self.sample_metadata)
        self.assertEqual(sum1, sum2)


if __name__ == "__main__":
    unittest.main()

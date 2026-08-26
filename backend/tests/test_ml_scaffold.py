"""
Unit tests for Machine Learning scaffolding and feature vectorization (Phase 4).
"""

import os
import sys
import unittest
import numpy as np
import mne

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from pipeline.features import extract_features_from_raw
from ml.dataset_builder import feature_dict_to_vector, FEATURE_NAMES
from ml.evaluate import ExperimentMetrics, compute_inference_advantage
from samples.generate_samples import generate_synthetic_eeg


class TestMLScaffold(unittest.TestCase):
    def test_feature_vector_shape_and_names(self):
        """Test conversion of feature dict to 19-dimensional float64 vector."""
        data, ch_names, sfreq = generate_synthetic_eeg(duration_sec=3.0, n_channels=8, profile="resting")
        info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types="eeg")
        raw = mne.io.RawArray(data, info, verbose=False)
        features = extract_features_from_raw(raw)

        vec = feature_dict_to_vector(features)
        self.assertEqual(vec.shape, (19,))
        self.assertEqual(len(FEATURE_NAMES), 19)
        self.assertTrue(np.all(np.isfinite(vec)))

    def test_inference_advantage_computation(self):
        """Test calculation of normalized adversary advantage gamma."""
        # 10 subjects: chance is 0.10
        # If classifier gets 0.10, advantage is 0.0
        self.assertEqual(compute_inference_advantage(0.10, 10), 0.0)
        # If classifier gets 1.0 (perfect), advantage is 1.0
        self.assertEqual(compute_inference_advantage(1.0, 10), 1.0)
        # If classifier gets 0.55 on 10 classes: (0.55 - 0.10) / 0.90 = 0.50
        self.assertAlmostEqual(compute_inference_advantage(0.55, 10), 0.50)

    def test_experiment_metrics_container(self):
        """Test ExperimentMetrics dataclass instantiation."""
        metrics = ExperimentMetrics(
            dataset_name="PhysioNet EEGBCI",
            n_subjects=10,
            n_samples=500,
            chance_accuracy=0.10,
            top1_accuracy=0.68,
            balanced_accuracy=0.65,
            macro_precision=0.66,
            macro_recall=0.65,
            macro_f1=0.65,
            inference_advantage_gamma=compute_inference_advantage(0.65, 10),
            model_name="Random Forest",
        )
        self.assertEqual(metrics.n_subjects, 10)
        self.assertAlmostEqual(metrics.inference_advantage_gamma, 0.6111, places=3)


if __name__ == "__main__":
    unittest.main()

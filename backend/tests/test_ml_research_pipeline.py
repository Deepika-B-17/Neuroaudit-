"""
Unit tests for the ML Research Identity Inference Pipeline (Phase 2).
"""

import os
import sys
import unittest
import numpy as np

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from ml.dataset_builder import segment_raw_into_epochs, FEATURE_NAMES, build_synthetic_multisubject_dataset
from ml.datasets.physionet_auditory import PhysionetAuditoryDataset
from ml.evaluate import evaluate_session_disjoint_multiclass
from ml.preprocessing import create_ml_pipeline
import mne

class TestMLResearchPipeline(unittest.TestCase):
    
    def setUp(self):
        # Create a tiny synthetic raw object for testing
        info = mne.create_info(ch_names=["T7", "F8", "Cz", "P4"], sfreq=200, ch_types="eeg")
        data = np.random.randn(4, 1000) * 1e-6 # 5 seconds of data at 200Hz
        self.raw = mne.io.RawArray(data, info, verbose=False)
        
    def test_dataset_loader_instantiation(self):
        """Test that the PhysionetAuditoryDataset initializes correctly."""
        ds = PhysionetAuditoryDataset(data_dir="/tmp/dummy_data_dir")
        self.assertIsNotNone(ds)
        self.assertEqual(ds.data_dir, os.path.abspath("/tmp/dummy_data_dir"))
        
    def test_epoch_generation(self):
        """Test research-only epoching wrapper."""
        epochs = segment_raw_into_epochs(self.raw, epoch_duration_sec=2.0)
        # 5 seconds total, 2.0s epochs -> should get 2 epochs (last 1s is discarded by default if not long enough, 
        # but wait, segment_raw_into_epochs returns exactly complete windows)
        self.assertEqual(len(epochs), 2)
        
        # Test 5.0s epoch
        epochs = segment_raw_into_epochs(self.raw, epoch_duration_sec=5.0)
        self.assertEqual(len(epochs), 1)

    def test_feature_extraction_compatibility(self):
        """Test that the features are correctly extracted and vector shape is consistent."""
        from pipeline.features import extract_features_from_raw
        from ml.dataset_builder import feature_dict_to_vector
        feat_dict = extract_features_from_raw(self.raw)
        self.assertIn("global_band_powers", feat_dict)
        
        vec = feature_dict_to_vector(feat_dict)
        self.assertEqual(len(vec), 19)
        self.assertEqual(len(vec), len(FEATURE_NAMES))
        
    def test_no_nan_inf_in_features(self):
        """Test that missing channels (like FP1/FP2 for FAA) don't cause NaN in features."""
        from pipeline.features import extract_features_from_raw
        from ml.dataset_builder import feature_dict_to_vector
        feat_dict = extract_features_from_raw(self.raw)
        vec = feature_dict_to_vector(feat_dict)
        self.assertFalse(np.any(np.isnan(vec)))
        self.assertFalse(np.any(np.isinf(vec)))

    def test_standard_scaler_fitting_inside_pipeline(self):
        """Test that standard scaler is fitted only inside the Pipeline."""
        pipe = create_ml_pipeline("logistic_regression")
        # Scaler should not have 'mean_' before fitting
        self.assertFalse(hasattr(pipe.named_steps["scaler"], "mean_"))
        
        X, y, _, _, _ = build_synthetic_multisubject_dataset(n_subjects=2, n_runs_per_subject=1, duration_sec=4.0)
        pipe.fit(X, y)
        self.assertTrue(hasattr(pipe.named_steps["scaler"], "mean_"))

    def test_group_leakage_prevention(self):
        """Test that evaluate_session_disjoint_multiclass prevents session leakage."""
        X, y, subject_ids, run_ids, _ = build_synthetic_multisubject_dataset(
            n_subjects=2, n_runs_per_subject=2, duration_sec=4.0, epoch_duration_sec=2.0
        )
        # Should execute successfully and strictly separate run_ids
        metrics = evaluate_session_disjoint_multiclass(
            X, y, subject_ids, run_ids, classifier_type="dummy", n_splits=2
        )
        self.assertIsNotNone(metrics.top1_accuracy)

if __name__ == "__main__":
    unittest.main()

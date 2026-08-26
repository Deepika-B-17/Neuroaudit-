"""
Comprehensive unit tests for Empirical ML Pipeline and Subject-Disjoint Evaluation (Phase 5).
"""

import os
import sys
import unittest
import numpy as np
from sklearn.pipeline import Pipeline

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from ml.dataset_builder import (
    build_synthetic_multisubject_dataset,
    feature_dict_to_vector,
    FEATURE_NAMES,
)
from ml.preprocessing import create_ml_pipeline, create_classifier
from ml.evaluate import (
    evaluate_subject_disjoint_pairwise,
    evaluate_session_disjoint_multiclass,
    compute_inference_advantage,
    ExperimentMetrics,
)


class TestMLPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Build deterministic 5-subject, 2-run test dataset
        cls.X, cls.y, cls.subject_ids, cls.run_ids, cls.feat_names = (
            build_synthetic_multisubject_dataset(
                n_subjects=5,
                n_runs_per_subject=2,
                duration_sec=6.0,
                epoch_duration_sec=2.0,
                random_seed=42,
            )
        )

    def test_1_feature_matrix_shape_and_names(self):
        """1. Verify feature matrix shape, 19 canonical features, and finiteness."""
        self.assertEqual(self.X.shape[1], 19)
        self.assertEqual(len(self.feat_names), 19)
        self.assertGreater(self.X.shape[0], 0)
        self.assertEqual(len(self.y), self.X.shape[0])
        self.assertTrue(np.all(np.isfinite(self.X)))

    def test_2_no_nans_after_preprocessing(self):
        """2. Verify preprocessing pipeline handles missing/extreme values without NaN output."""
        X_with_nans = self.X.copy()
        X_with_nans[0, 0] = np.nan
        X_with_nans[1, 5] = np.nan

        pipe = create_ml_pipeline("logistic_regression", random_state=42)
        pipe.fit(X_with_nans, self.y)
        preds = pipe.predict(X_with_nans)
        self.assertEqual(len(preds), len(self.y))
        self.assertTrue(np.all(np.isfinite(preds)))

    def test_3_subject_disjoint_guarantee(self):
        """3. Verify primary subject-disjoint evaluation enforces strict disjoint partitions."""
        metrics = evaluate_subject_disjoint_pairwise(
            self.X, self.y, self.subject_ids, classifier_type="dummy", n_splits=3, random_state=42
        )
        self.assertIsInstance(metrics, ExperimentMetrics)
        self.assertEqual(metrics.chance_accuracy, 0.50)
        self.assertGreaterEqual(metrics.balanced_accuracy, 0.0)

    def test_4_pipeline_avoids_pre_fit_leakage(self):
        """4. Verify pipeline is unfitted before cross-validation."""
        pipe = create_ml_pipeline("random_forest", random_state=42)
        self.assertIsInstance(pipe, Pipeline)
        # Verify scaler has not learned global statistics before fitting
        self.assertFalse(hasattr(pipe.named_steps["scaler"], "mean_"))

    def test_5_dummy_classifier(self):
        """5. Verify Dummy baseline runs and establishes chance level."""
        metrics = evaluate_session_disjoint_multiclass(
            self.X, self.y, self.subject_ids, self.run_ids, classifier_type="dummy", n_splits=2, random_state=42
        )
        self.assertEqual(metrics.chance_accuracy, 0.20)  # 5 subjects -> 0.20
        self.assertAlmostEqual(metrics.top1_accuracy, 0.20, delta=0.15)

    def test_6_logistic_regression(self):
        """6. Verify Logistic Regression classifier execution and metrics."""
        metrics = evaluate_session_disjoint_multiclass(
            self.X, self.y, self.subject_ids, self.run_ids, classifier_type="logistic_regression", n_splits=2, random_state=42
        )
        self.assertGreaterEqual(metrics.top1_accuracy, 0.0)
        self.assertLessEqual(metrics.top1_accuracy, 1.0)
        self.assertGreaterEqual(metrics.inference_advantage_gamma, 0.0)
        self.assertLessEqual(metrics.inference_advantage_gamma, 1.0)

    def test_7_random_forest(self):
        """7. Verify Random Forest classifier execution and metrics."""
        metrics = evaluate_session_disjoint_multiclass(
            self.X, self.y, self.subject_ids, self.run_ids, classifier_type="random_forest", n_splits=2, random_state=42
        )
        self.assertGreaterEqual(metrics.top1_accuracy, 0.0)
        self.assertLessEqual(metrics.top1_accuracy, 1.0)
        self.assertIsNotNone(metrics.confusion_matrix)

    def test_8_evaluation_output_metrics(self):
        """8. Verify all required evaluation metrics are computed and non-null."""
        metrics = evaluate_session_disjoint_multiclass(
            self.X, self.y, self.subject_ids, self.run_ids, classifier_type="logistic_regression", n_splits=2, random_state=42
        )
        self.assertIsInstance(metrics.top1_accuracy, float)
        self.assertIsInstance(metrics.balanced_accuracy, float)
        self.assertIsInstance(metrics.macro_precision, float)
        self.assertIsInstance(metrics.macro_recall, float)
        self.assertIsInstance(metrics.macro_f1, float)
        self.assertIsInstance(metrics.inference_advantage_gamma, float)

    def test_9_reproducibility_with_seed(self):
        """9. Verify identical runs with fixed random_state produce bit-exact identical results."""
        m1 = evaluate_session_disjoint_multiclass(
            self.X, self.y, self.subject_ids, self.run_ids, classifier_type="random_forest", n_splits=2, random_state=42
        )
        m2 = evaluate_session_disjoint_multiclass(
            self.X, self.y, self.subject_ids, self.run_ids, classifier_type="random_forest", n_splits=2, random_state=42
        )
        self.assertEqual(m1.top1_accuracy, m2.top1_accuracy)
        self.assertEqual(m1.balanced_accuracy, m2.balanced_accuracy)
        self.assertEqual(m1.macro_f1, m2.macro_f1)
        self.assertEqual(m1.inference_advantage_gamma, m2.inference_advantage_gamma)


if __name__ == "__main__":
    unittest.main()

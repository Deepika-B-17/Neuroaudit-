import os
import sys
import io
import unittest
import json
import tempfile
import numpy as np

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from database import init_db, save_audit, get_audit, list_audits
from pipeline import (
    load_eeg_file,
    extract_features_from_raw,
    compute_dimension_risks,
    aggregate_privacy_risk,
    generate_recommendations,
    analyze_eeg_pipeline
)
from reports import generate_pdf_report
from samples.generate_samples import generate_synthetic_eeg, write_edf_file, ensure_sample_files
from app import app

class TestNeuroAuditBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_sample_files()
        cls.client = app.test_client()

    def test_synthetic_eeg_and_features(self):
        """Test synthetic EEG creation and feature extraction."""
        data, ch_names, sfreq = generate_synthetic_eeg(duration_sec=5.0, n_channels=8, profile="resting")
        self.assertEqual(len(ch_names), 8)
        self.assertEqual(data.shape[0], 8)
        self.assertEqual(data.shape[1], int(5.0 * sfreq))

        with tempfile.NamedTemporaryFile(suffix=".edf", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            write_edf_file(tmp_path, data, ch_names, sfreq)
            self.assertTrue(os.path.exists(tmp_path))

            # Load EEG
            raw, metadata, preview_traces, quality_report = load_eeg_file(tmp_path)
            self.assertEqual(metadata["n_channels"], 8)
            self.assertIn("FP1", preview_traces)

            # Features
            features = extract_features_from_raw(raw)
            self.assertIn("global_band_powers", features)
            self.assertIn("frontal_alpha_asymmetry", features)
            self.assertIn("iapf_hz", features)

            # Models
            dimensions = compute_dimension_risks(features, metadata)
            self.assertEqual(len(dimensions), 4)

            # Scoring
            summary = aggregate_privacy_risk(dimensions, features, metadata)
            self.assertIn("overallRisk", summary)
            self.assertIn(summary["riskLevel"], ["LOW", "MEDIUM", "HIGH"])

            # Recommendations
            recs = generate_recommendations(dimensions, summary["overallRisk"], summary["riskLevel"])
            self.assertTrue(len(recs) >= 3)
            self.assertEqual(recs[0]["number"], "01")

            # PDF Generation
            audit_obj = {
                "auditName": "Test Audit",
                "fileName": "test.edf",
                "analysisDate": "22 Aug 2026",
                "status": "Complete",
                "overallRisk": summary["overallRisk"],
                "riskLevel": summary["riskLevel"],
                "executiveSummary": summary["executiveSummary"],
                "overallSummary": summary["overallSummary"],
                "keyFindings": summary["keyFindings"],
                "dimensions": dimensions,
                "recommendations": recs,
                "disclaimer": summary["disclaimer"]
            }
            pdf_bytes = generate_pdf_report(audit_obj)
            self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_api_health(self):
        """Test /api/health endpoint."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "healthy")

    def test_api_samples_and_load(self):
        """Test /api/samples and /api/samples/load."""
        res = self.client.get("/api/samples")
        self.assertEqual(res.status_code, 200)
        samples = res.get_json()["samples"]
        self.assertTrue(len(samples) >= 3)

        load_res = self.client.post("/api/samples/load", json={"sample_id": "session_a_rest_eeg.edf", "auditName": "API Test"})
        self.assertEqual(load_res.status_code, 200)
        audit_data = load_res.get_json()
        self.assertIn("session_id", audit_data)
        self.assertEqual(audit_data["auditName"], "API Test")
        session_id = audit_data["session_id"]

        # Test GET /api/analysis/<session_id>
        analysis_res = self.client.get(f"/api/analysis/{session_id}")
        self.assertEqual(analysis_res.status_code, 200)
        self.assertEqual(analysis_res.get_json()["session_id"], session_id)

        # Test GET /api/report/<session_id>/download
        pdf_res = self.client.get(f"/api/report/{session_id}/download")
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res.mimetype, "application/pdf")
        self.assertTrue(pdf_res.data.startswith(b"%PDF"))

    def test_short_signal_processing(self):
        """Test short duration EEG processing (0.5s) without filter crash."""
        import mne
        data, ch_names, sfreq = generate_synthetic_eeg(duration_sec=0.5, n_channels=8, profile="resting")
        info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types="eeg")
        raw_obj = mne.io.RawArray(data, info, verbose=False)
        with tempfile.NamedTemporaryFile(suffix="-raw.fif", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            raw_obj.save(tmp_path, overwrite=True, verbose=False)
            raw, metadata, preview_traces, quality_report = load_eeg_file(tmp_path)
            self.assertEqual(metadata["duration_sec"], 0.5)
            self.assertFalse(quality_report["passed"])  # Flagged by quality gate for < 2.0s
            features = extract_features_from_raw(raw)
            self.assertIn("iapf_hz", features)
            self.assertTrue(np.isfinite(features["theta_beta_ratio"]))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_too_short_signal_rejection(self):
        """Test that sub-0.2s recordings fail gracefully with a clear ValueError."""
        import mne
        data, ch_names, sfreq = generate_synthetic_eeg(duration_sec=0.1, n_channels=8, profile="resting")
        info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types="eeg")
        raw_obj = mne.io.RawArray(data, info, verbose=False)
        with tempfile.NamedTemporaryFile(suffix="-raw.fif", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            raw_obj.save(tmp_path, overwrite=True, verbose=False)
            with self.assertRaises(ValueError) as ctx:
                load_eeg_file(tmp_path)
            self.assertIn("too short", str(ctx.exception).lower())
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_upload_security_and_validation(self):
        """Test file upload validation (empty file, invalid extension, missing file)."""
        # 1. Missing file field
        res = self.client.post("/api/upload", data={})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertEqual(data["error"]["code"], "MISSING_FILE")

        # 2. Unsupported extension
        res = self.client.post(
            "/api/upload",
            data={"file": (io.BytesIO(b"dummy data"), "malicious_script.exe")},
            content_type="multipart/form-data",
        )
        self.assertEqual(res.status_code, 415)
        data = res.get_json()
        self.assertEqual(data["error"]["code"], "UNSUPPORTED_FILE_TYPE")

        # 3. Empty file (0 bytes)
        res = self.client.post(
            "/api/upload",
            data={"file": (io.BytesIO(b""), "empty.edf")},
            content_type="multipart/form-data",
        )
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertEqual(data["error"]["code"], "EMPTY_FILE")

    def test_structured_error_responses(self):
        """Test structured error format on non-existent resources."""
        res = self.client.get("/api/analysis/non_existent_session_123")
        self.assertEqual(res.status_code, 404)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"]["code"], "SESSION_NOT_FOUND")

    def test_upload_cleanup(self):
        """Test the upload cleanup utility."""
        from app import cleanup_old_uploads, UPLOADS_DIR
        # Run cleanup with 0 max age hours to simulate removing expired files
        removed = cleanup_old_uploads(max_age_hours=0)
        self.assertIsInstance(removed, int)

if __name__ == "__main__":
    unittest.main()

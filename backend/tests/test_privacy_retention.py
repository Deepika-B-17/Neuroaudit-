"""
Privacy and Data Retention Tests for NeuroAudit.

Verifies:
1. Whitelist and loader support for .edf, .fif, .bdf, .set
2. Immediate deletion of temporary files upon successful upload
3. Immediate deletion of temporary files upon failure (error-path cleanup)
4. Database privacy:
   - No preview_traces stored in SQLite
   - No file_path stored for new records in SQLite
   - No raw EEG signal stored in SQLite
   - Immediate API response still provides preview_traces for frontend visualization
5. PDF generation and download route work properly
6. Deterministic scoring consistency
"""

import os
import io
import json
import sqlite3
import tempfile
import unittest
import numpy as np

from backend.app import app, ALLOWED_EXTENSIONS
from backend.database.db import get_audit, get_db_connection, save_audit, init_db
from backend.pipeline.eeg_loader import load_eeg_file, check_eeg_quality
from backend.pipeline import analyze_eeg_pipeline
from backend.reports.pdf_generator import generate_pdf_report


class TestPrivacyAndRetention(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()
        cls.sample_edf = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "samples", "session_a_rest_eeg.edf"
        )
        cls.sample_fif = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "samples", "session_a_rest_eeg-raw.fif"
        )

    def test_1_supported_eeg_formats_whitelist(self):
        """Verify that .edf, .fif, .bdf, .set are all explicitly allowed."""
        expected_formats = {".edf", ".fif", ".bdf", ".set"}
        self.assertTrue(expected_formats.issubset(ALLOWED_EXTENSIONS))

    def test_2_eeg_loader_supported_formats(self):
        """Verify that the loader can load both sample .edf and .fif files."""
        self.assertTrue(os.path.exists(self.sample_edf), "sample edf missing")
        self.assertTrue(os.path.exists(self.sample_fif), "sample fif missing")

        # Test EDF loading
        raw_edf, meta_edf, traces_edf, qual_edf = load_eeg_file(self.sample_edf)
        self.assertIsNotNone(raw_edf)
        self.assertIn("sfreq", meta_edf)
        self.assertIsInstance(traces_edf, dict)

        # Test FIF loading
        raw_fif, meta_fif, traces_fif, qual_fif = load_eeg_file(self.sample_fif)
        self.assertIsNotNone(raw_fif)
        self.assertIn("sfreq", meta_fif)
        self.assertIsInstance(traces_fif, dict)

    def test_3_immediate_deletion_on_success(self):
        """Verify temporary uploaded file is immediately deleted after successful upload."""
        uploads_dir = app.config.get("UPLOAD_FOLDER", os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads"))
        
        with open(self.sample_edf, "rb") as f:
            file_bytes = f.read()

        response = self.client.post(
            "/api/upload",
            data={
                "file": (io.BytesIO(file_bytes), "test_privacy_upload.edf"),
                "auditName": "Privacy Test Audit",
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        session_id = data["session_id"]

        # 1. API response includes preview_traces for immediate frontend display
        self.assertIn("preview_traces", data["features"])
        self.assertGreater(len(data["features"]["preview_traces"]), 0)

        # 2. fileName is clean (no path, no UUID prefix)
        self.assertEqual(data["fileName"], "test_privacy_upload.edf")

        # 3. uploads/ folder does NOT contain any file matching this session or filename
        files_in_uploads = os.listdir(uploads_dir)
        self.assertEqual(len(files_in_uploads), 0, f"Uploads directory should be empty: {files_in_uploads}")

        # 4. Check SQLite database content
        record = get_audit(session_id)
        self.assertIsNotNone(record)
        
        # Verify db.py get_audit returns empty filePath and anonymous fileName
        conn = get_db_connection()
        try:
            row = conn.execute("SELECT file_name, file_path, features FROM audits WHERE session_id = ?", (session_id,)).fetchone()
            self.assertEqual(row["file_path"], "", "file_path in SQLite must be empty string")
            self.assertEqual(row["file_name"], "EEG Recording", "file_name in SQLite must be anonymous label")
            
            stored_features = json.loads(row["features"])
            self.assertNotIn("preview_traces", stored_features, "preview_traces must NOT be in SQLite features")
        finally:
            conn.close()

    def test_4_immediate_deletion_on_failure(self):
        """Verify temporary uploaded file is deleted even if EEG parsing / pipeline fails."""
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
        
        # Send corrupted / invalid EEG file content
        corrupted_bytes = b"CORRUPTED_EEG_DATA_NOT_VALID_HEADER" * 50

        response = self.client.post(
            "/api/upload",
            data={
                "file": (io.BytesIO(corrupted_bytes), "corrupted_test.edf"),
                "auditName": "Failure Path Audit",
            },
            content_type="multipart/form-data",
        )
        # Should fail with 422 or 500
        self.assertIn(response.status_code, (422, 500))

        # Check uploads directory is completely clean
        files_in_uploads = os.listdir(uploads_dir)
        self.assertEqual(len(files_in_uploads), 0, f"Uploads directory must be clean after error: {files_in_uploads}")

    def test_5_pdf_generation_and_download(self):
        """Verify PDF generation and PDF download route work after changes."""
        # Use known audit from test_3 or run analyze pipeline
        audit = analyze_eeg_pipeline(self.sample_edf, audit_name="PDF Test")
        save_audit(audit)

        session_id = audit["session_id"]
        pdf_bytes = generate_pdf_report(audit)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"), "Must produce valid PDF binary")

        # Test download endpoint
        res = self.client.get(f"/api/report/{session_id}/download")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "application/pdf")
        self.assertIn("Content-Disposition", res.headers)
        self.assertTrue(res.data.startswith(b"%PDF"))

    def test_6_score_consistency_with_previous(self):
        """Verify heuristic risk score on sample_edf is deterministic and identical."""
        res1 = analyze_eeg_pipeline(self.sample_edf, audit_name="Score Test 1")
        res2 = analyze_eeg_pipeline(self.sample_edf, audit_name="Score Test 2")

        self.assertEqual(res1["overallRisk"], res2["overallRisk"])
        self.assertEqual(res1["riskLevel"], res2["riskLevel"])
        for d1, d2 in zip(res1["dimensions"], res2["dimensions"]):
            self.assertEqual(d1["score"], d2["score"])
            self.assertEqual(d1["level"], d2["level"])

    def test_7_original_filename_not_persisted_in_db(self):
        """
        Verify uploading S001R01.edf does not persist 'S001R01.edf' into SQLite.
        Verifies:
        - API response still returns fileName for active frontend session
        - Persisted SQLite row has file_name == 'EEG Recording'
        - 'S001R01.edf' is NOT stored in file_name
        - Retrieved record via get_audit has fileName == 'EEG Recording'
        - PDF generation and download work using the persisted anonymous label
        """
        with open(self.sample_edf, "rb") as f:
            file_bytes = f.read()

        response = self.client.post(
            "/api/upload",
            data={
                "file": (io.BytesIO(file_bytes), "S001R01.edf"),
                "auditName": "Subject Anonymity Test",
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        session_id = data["session_id"]

        # Active frontend session receives fileName in immediate response
        self.assertEqual(data["fileName"], "S001R01.edf")

        # Query database row directly
        conn = get_db_connection()
        try:
            row = conn.execute(
                "SELECT file_name, file_path FROM audits WHERE session_id = ?",
                (session_id,)
            ).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["file_name"], "EEG Recording")
            self.assertNotIn("S001R01", row["file_name"])
            self.assertEqual(row["file_path"], "")
        finally:
            conn.close()

        # Retrieve record via API / get_audit
        retrieved = get_audit(session_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["fileName"], "EEG Recording")

        # PDF download using persisted record
        pdf_res = self.client.get(f"/api/report/{session_id}/download")
        self.assertEqual(pdf_res.status_code, 200)
        self.assertIn("NeuroAudit_Report_EEG Recording", pdf_res.headers.get("Content-Disposition", ""))

    def test_8_all_persisted_audit_records_are_anonymized(self):
        """Verify the database invariant: every existing row in audits has file_name == 'EEG Recording'."""
        conn = get_db_connection()
        try:
            rows = conn.execute("SELECT file_name FROM audits").fetchall()
            self.assertGreater(len(rows), 0, "Database should contain audit records")
            for r in rows:
                self.assertEqual(r["file_name"], "EEG Recording")
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()

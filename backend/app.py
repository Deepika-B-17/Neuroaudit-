"""
NeuroAudit — Master Flask Application & REST API (Phase 2)

Phase 2 additions
-----------------
- Secure file upload: werkzeug secure_filename, 50 MB limit, extension whitelist
- Descriptive HTTP error responses (JSON) for all error cases
- /api/simulate/<session_id>/<control_id>  — mitigation simulation endpoint
- /api/explain/<session_id>                — explainability endpoint
- GET /                                    — API discovery endpoint
"""

import os
import sys
import io
import uuid
import logging
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

from database  import init_db, save_audit, get_audit, list_audits
from pipeline  import analyze_eeg_pipeline, PRIVACY_DISCLAIMER, MitigationSimulator
from reports   import generate_pdf_report
from samples   import ensure_sample_files, SAMPLES_DIR

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("NeuroAudit")

# ---------------------------------------------------------------------------
# Upload configuration
# ---------------------------------------------------------------------------
UPLOADS_DIR          = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS   = {".edf", ".fif", ".bdf", ".set"}
MAX_UPLOAD_BYTES     = 50 * 1024 * 1024   # 50 MB
os.makedirs(UPLOADS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES   # enforced by Flask/Werkzeug
CORS(app, resources={r"/api/*": {"origins": "*"}})


import re

# ---------------------------------------------------------------------------
# Helpers & Security Sanitization
# ---------------------------------------------------------------------------

def _sanitize_error_message(msg: str) -> str:
    """Strip absolute filesystem paths to avoid exposing host filesystem structure."""
    if not msg:
        return ""
    # Strip Windows & Unix paths
    sanitized = re.sub(r'[A-Za-z]:\\[\w\\\.-]+', '[path]', str(msg))
    sanitized = re.sub(r'/[\w/\.-]+', '[path]', sanitized)
    return sanitized.strip()


def _json_error(message: str, details: str = "", status: int = 400, code: str = "ERROR"):
    """Produce a structured, sanitized JSON error response."""
    clean_message = _sanitize_error_message(message)
    clean_details = _sanitize_error_message(details) if details else ""
    body = {
        "success": False,
        "error": {
            "code": code,
            "message": clean_message,
        },
    }
    if clean_details:
        body["error"]["details"] = clean_details
        body["details"] = clean_details
    else:
        body["details"] = clean_message

    return jsonify(body), status


def _allowed_file(filename: str) -> bool:
    ext = os.path.splitext(filename.lower())[1]
    return ext in ALLOWED_EXTENSIONS


def cleanup_old_uploads(max_age_hours: int = 24) -> int:
    """
    Safely remove uploaded temporary files older than max_age_hours.
    Database audit records remain intact because all features and metadata
    are persisted in SQLite.
    """
    now = datetime.utcnow().timestamp()
    removed_count = 0
    try:
        if os.path.exists(UPLOADS_DIR):
            for fname in os.listdir(UPLOADS_DIR):
                fpath = os.path.join(UPLOADS_DIR, fname)
                if os.path.isfile(fpath):
                    mtime = os.path.getmtime(fpath)
                    if (now - mtime) > (max_age_hours * 3600):
                        try:
                            os.remove(fpath)
                            removed_count += 1
                        except Exception:
                            pass
    except Exception as exc:
        logger.warning("Upload cleanup error: %s", exc)
    return removed_count


def _cleanup(path: str) -> None:
    """Remove a temporary file if it exists."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Database initialisation + sample seeding
# ---------------------------------------------------------------------------

def seed_initial_audits():
    """Seed benchmark audits on first startup (only if DB is empty)."""
    ensure_sample_files()
    if list_audits(limit=1):
        return   # already seeded

    logger.info("Seeding benchmark audits …")
    sample_configs = [
        ("session_a_rest_eeg.edf", "Clinical cohort session A",
         "Resting-state baseline recording — 8 channels, 30 s, 10-20 montage."),
        ("pilot_rest_02.edf",      "Pilot study — rest-state",
         "High-arousal stress protocol — 8 channels, 25 s, elevated beta activity."),
        ("dual_task_block3.edf",   "Workload dual-task trial",
         "Cognitive dual-task recording — 8 channels, 35 s, frontal theta surge."),
    ]
    for fname, name, desc in sample_configs:
        fpath = os.path.join(SAMPLES_DIR, fname)
        if not os.path.exists(fpath):
            continue
        try:
            result = analyze_eeg_pipeline(fpath, audit_name=name, description=desc)
            save_audit(result)
            logger.info("Seeded: %s  (Risk %d — %s)", name, result["overallRisk"], result["riskLevel"])
        except Exception as exc:
            logger.warning("Could not seed %s: %s", fname, exc)


init_db()
seed_initial_audits()


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def api_root():
    """API discovery endpoint."""
    return jsonify({
        "service":     "NeuroAudit API",
        "version":     "2.0.0",
        "phase":       "Phase 1 — Stabilization & Baseline",
        "endpoints": [
            "GET  /api/health",
            "POST /api/upload",
            "GET  /api/analysis/<session_id>",
            "GET  /api/recommendations/<session_id>",
            "GET  /api/explain/<session_id>",
            "GET  /api/simulate/<session_id>/<control_id>",
            "GET  /api/report/<session_id>/download",
            "GET  /api/audits",
            "GET  /api/samples",
            "POST /api/samples/load",
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }), 200


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health and status check."""
    return jsonify({
        "status":    "healthy",
        "service":   "NeuroAudit API",
        "version":   "2.0.0",
        "phase":     "Phase 1 — Stabilization & Baseline",
        "timestamp": datetime.utcnow().isoformat(),
    }), 200


@app.route("/api/upload", methods=["POST"])
def upload_eeg():
    """
    Accept an EEG file upload, run the full analysis pipeline, persist to DB.

    Form fields:
        file        — EEG file (.edf | .fif | .bdf | .set), max 50 MB
        auditName   — optional human-readable audit name
        description — optional description / study context
    """
    if "file" not in request.files:
        return _json_error(
            "No EEG file provided.",
            "Include a 'file' field in the multipart/form-data request.",
            status=400,
            code="MISSING_FILE",
        )

    file = request.files["file"]
    if not file or not file.filename:
        return _json_error(
            "File has an empty filename.",
            "Please select a valid EEG recording file.",
            status=400,
            code="EMPTY_FILENAME",
        )

    # --- Extension whitelist ------------------------------------------------
    if not _allowed_file(file.filename):
        ext = os.path.splitext(file.filename.lower())[1] or "(none)"
        return _json_error(
            f"Unsupported file type: '{ext}'.",
            f"Accepted formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}.",
            status=415,
            code="UNSUPPORTED_FILE_TYPE",
        )

    # --- Secure filename + store with path traversal protection -------------
    raw_name = os.path.basename(file.filename)
    safe_name = secure_filename(raw_name)
    ext = os.path.splitext(file.filename.lower())[1]
    if not safe_name:
        safe_name = f"recording{ext}"

    file_uuid   = uuid.uuid4().hex[:8]
    stored_name = f"{file_uuid}_{safe_name}"
    file_path   = os.path.abspath(os.path.join(UPLOADS_DIR, stored_name))

    # Path traversal assertion
    uploads_root = os.path.abspath(UPLOADS_DIR)
    if not file_path.startswith(uploads_root):
        return _json_error(
            "Invalid file path detected.",
            "Filename violates path security restrictions.",
            status=400,
            code="INVALID_PATH",
        )

    try:
        file.save(file_path)
    except Exception as exc:
        logger.error("Failed to save upload: %s", exc)
        return _json_error("Failed to save uploaded file.", status=500, code="STORAGE_ERROR")

    # Check for empty file (0 bytes)
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        _cleanup(file_path)
        return _json_error(
            "Uploaded file is empty (0 bytes).",
            "Please upload a non-empty EEG recording.",
            status=400,
            code="EMPTY_FILE",
        )

    audit_name  = request.form.get("auditName", "").strip() or f"Audit — {safe_name}"
    description = request.form.get("description", "").strip()

    logger.info("Upload received: %s (%d bytes) → %s", file.filename, file_size, stored_name)

    try:
        audit_result = analyze_eeg_pipeline(file_path, audit_name=audit_name, description=description)
        save_audit(audit_result)
        # Periodically clean up old temporary uploads (older than 24h)
        cleanup_old_uploads()
        logger.info(
            "Audit complete: %s  Risk=%d (%s)",
            audit_result["session_id"], audit_result["overallRisk"], audit_result["riskLevel"],
        )
        return jsonify(audit_result), 200

    except ValueError as exc:
        # EEG parsing / validation error (unsupported format, corrupt file, too short, etc.)
        _cleanup(file_path)
        logger.warning("EEG validation failed for %s: %s", file.filename, exc)
        return _json_error(
            "Failed to parse EEG file.",
            str(exc),
            status=422,
            code="INVALID_EEG_FILE",
        )

    except Exception as exc:
        _cleanup(file_path)
        logger.error("Pipeline error on %s: %s", file.filename, exc, exc_info=True)
        return _json_error(
            "EEG analysis pipeline failed.",
            "The signal processing pipeline encountered an unexpected error.",
            status=500,
            code="PIPELINE_ERROR",
        )


@app.route("/api/analysis/<session_id>", methods=["GET"])
def get_analysis(session_id: str):
    """Retrieve full analysis results by session_id."""
    audit = get_audit(session_id)
    if not audit:
        return _json_error(
            f"Audit session '{session_id}' not found.",
            status=404,
            code="SESSION_NOT_FOUND",
        )

    audit["recentAudits"] = list_audits(limit=5)
    audit["disclaimer"]   = PRIVACY_DISCLAIMER
    return jsonify(audit), 200


@app.route("/api/recommendations/<session_id>", methods=["GET"])
def get_audit_recommendations(session_id: str):
    """Retrieve structured privacy-mitigation recommendations for an audit."""
    audit = get_audit(session_id)
    if not audit:
        return _json_error(
            f"Audit session '{session_id}' not found.",
            status=404,
            code="SESSION_NOT_FOUND",
        )

    return jsonify({
        "session_id":     session_id,
        "recommendations": audit.get("recommendations", []),
    }), 200


@app.route("/api/explain/<session_id>", methods=["GET"])
def get_explainability(session_id: str):
    """Return per-dimension explainability blocks for an audit."""
    audit = get_audit(session_id)
    if not audit:
        return _json_error(
            f"Audit session '{session_id}' not found.",
            status=404,
            code="SESSION_NOT_FOUND",
        )

    return jsonify({
        "session_id":    session_id,
        "explainability": audit.get("explainability", []),
        "quality_report": audit.get("qualityReport", {}),
    }), 200


@app.route("/api/simulate/<session_id>/<control_id>", methods=["GET"])
def simulate_mitigation(session_id: str, control_id: str):
    """
    Return a mitigation simulation for a given control.

    Phase 2: always returns REQUIRES_EMPIRICAL_VALIDATION.
    Phase 3 will inject empirically validated risk-delta functions.
    """
    audit = get_audit(session_id)
    if not audit:
        return _json_error(
            f"Audit session '{session_id}' not found.",
            status=404,
            code="SESSION_NOT_FOUND",
        )

    current_risk = audit.get("overallRisk", 50)
    simulation   = MitigationSimulator.simulate(control_id, current_risk)
    return jsonify(simulation.to_dict()), 200


@app.route("/api/report/<session_id>/download", methods=["GET"])
def download_pdf_report(session_id: str):
    """Generate and stream a publication-grade PDF audit report."""
    audit = get_audit(session_id)
    if not audit:
        return _json_error(
            f"Audit session '{session_id}' not found.",
            status=404,
            code="SESSION_NOT_FOUND",
        )

    try:
        pdf_bytes = generate_pdf_report(audit)
        filename  = (
            f"NeuroAudit_Report_"
            f"{audit['fileName'].replace('.edf', '').replace('.fif', '')}_{session_id}.pdf"
        )
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as exc:
        logger.error("PDF generation failed: %s", exc, exc_info=True)
        return _json_error(
            "Failed to generate PDF report.",
            "An error occurred while compiling the ReportLab document.",
            status=500,
            code="PDF_GENERATION_FAILED",
        )


@app.route("/api/audits", methods=["GET"])
def get_recent_audits():
    """List recent audits from the database."""
    limit  = request.args.get("limit", 20, type=int)
    audits = list_audits(limit=limit)
    return jsonify({"audits": audits}), 200


@app.route("/api/samples", methods=["GET"])
def list_benchmark_samples():
    """List pre-configured benchmark EEG sample files."""
    ensure_sample_files()
    samples = [
        {
            "id":          "session_a_rest_eeg.edf",
            "name":        "Clinical cohort session A",
            "fileName":    "session_a_rest_eeg.edf",
            "description": "Resting-state EEG baseline (8 channels, 30 s). "
                           "Synthetic benchmark — individual alpha rhythm profile.",
            "duration":    "30s",
            "profile":     "Resting Baseline",
            "data_type":   "SYNTHETIC_BENCHMARK",
        },
        {
            "id":          "pilot_rest_02.edf",
            "name":        "Pilot study — rest-state",
            "fileName":    "pilot_rest_02.edf",
            "description": "Stress-protocol EEG (8 channels, 25 s). "
                           "Synthetic benchmark — elevated beta, suppressed alpha.",
            "duration":    "25s",
            "profile":     "Stress / Affective",
            "data_type":   "SYNTHETIC_BENCHMARK",
        },
        {
            "id":          "dual_task_block3.edf",
            "name":        "Workload dual-task trial",
            "fileName":    "dual_task_block3.edf",
            "description": "Workload EEG (8 channels, 35 s). "
                           "Synthetic benchmark — frontal theta surge, engagement elevation.",
            "duration":    "35s",
            "profile":     "Cognitive Workload",
            "data_type":   "SYNTHETIC_BENCHMARK",
        },
    ]
    return jsonify({"samples": samples}), 200


@app.route("/api/samples/load", methods=["POST"])
def load_sample_audit():
    """Load a benchmark EEG sample and run full analysis."""
    ensure_sample_files()
    data       = request.get_json() or {}
    sample_id  = data.get("sample_id", "session_a_rest_eeg.edf")
    audit_name = data.get("auditName",  "").strip()
    description = data.get("description", "").strip()

    file_path = os.path.join(SAMPLES_DIR, sample_id)
    if not os.path.exists(file_path):
        return _json_error(
            f"Sample file '{sample_id}' not found.",
            "Use GET /api/samples to list available samples.",
            status=404,
            code="SAMPLE_NOT_FOUND",
        )

    try:
        audit_result = analyze_eeg_pipeline(
            file_path,
            audit_name=audit_name or f"Sample Audit — {sample_id}",
            description=description or
                "Benchmark sample audit generated from synthetic EEG data (SYNTHETIC_BENCHMARK).",
        )
        save_audit(audit_result)
        return jsonify(audit_result), 200
    except Exception as exc:
        logger.error("Sample analysis failed: %s", exc, exc_info=True)
        return _json_error(
            "Failed to analyze sample EEG.",
            str(exc),
            status=500,
            code="SAMPLE_ANALYSIS_FAILED",
        )


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(413)
def request_entity_too_large(exc):
    return _json_error(
        "Uploaded file exceeds the 50 MB size limit.",
        "Please compress or truncate the EEG recording before uploading.",
        status=413,
        code="PAYLOAD_TOO_LARGE",
    )


@app.errorhandler(404)
def not_found(exc):
    return _json_error(
        "Endpoint not found.",
        str(exc),
        status=404,
        code="ENDPOINT_NOT_FOUND",
    )


@app.errorhandler(405)
def method_not_allowed(exc):
    return _json_error(
        "HTTP method not allowed for this endpoint.",
        str(exc),
        status=405,
        code="METHOD_NOT_ALLOWED",
    )


@app.errorhandler(500)
def internal_error(exc):
    logger.error("Internal server error: %s", exc, exc_info=True)
    return _json_error(
        "Internal server error.",
        "An unexpected internal error occurred on the server.",
        status=500,
        code="INTERNAL_SERVER_ERROR",
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("Starting NeuroAudit API server on http://127.0.0.1:%d", port)
    app.run(host="0.0.0.0", port=port, debug=False)

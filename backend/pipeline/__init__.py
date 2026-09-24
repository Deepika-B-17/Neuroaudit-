"""
NeuroAudit Signal Processing & Privacy Risk Pipeline Package.

Phase 2 changes
---------------
- load_eeg_file now returns (raw, metadata, preview_traces, quality_report)
- analyze_eeg_pipeline stores quality_report in the audit result dict
- explain_dimension_risk is exported for the API layer
- MitigationSimulator is exported for the API layer
"""

from .eeg_loader       import load_eeg_file, generate_preview_traces, check_eeg_quality
from .features         import extract_features_from_raw
from .models           import compute_dimension_risks
from .scoring          import aggregate_privacy_risk, PRIVACY_DISCLAIMER
from .recommendations  import (
    generate_recommendations,
    explain_dimension_risk,
    MitigationSimulator,
)


def analyze_eeg_pipeline(
    file_path:  str,
    audit_name: str = "",
    description: str = "",
) -> dict:
    """
    Run the full end-to-end NeuroAudit analysis pipeline on an EEG file.

    Steps
    -----
    1. Load & preprocess EEG  (bandpass + notch filter)
    2. EEG quality gate       (check_eeg_quality)
    3. Feature extraction     (16 algorithms / 20 outputs)
    4. Heuristic risk models  (Identity, Emotion, Stress, Workload)
    5. Risk aggregation       (weighted sum + narratives)
    6. Recommendation engine  (Privacy Mitigation Engine)

    Returns a flat dict that is written directly to SQLite and returned
    to the frontend via the Flask REST API.
    """
    import os
    import uuid
    from datetime import datetime

    file_name  = os.path.basename(file_path)
    session_id = f"na_{uuid.uuid4().hex[:12]}"

    # Step 1: Load, normalise, filter
    raw, metadata, preview_traces, quality_report = load_eeg_file(file_path)

    # Step 2: Feature extraction (NaN-safe)
    features = extract_features_from_raw(raw)

    # Step 3: Heuristic risk dimensions
    # Pass quality_report inside metadata so models can flag low-quality results
    metadata["quality_report"] = quality_report
    dimensions = compute_dimension_risks(features, metadata)

    # Step 4: Risk aggregation & executive narratives
    risk_summary = aggregate_privacy_risk(dimensions, features, metadata)

    # Step 5: Recommendation engine
    recommendations = generate_recommendations(
        dimensions,
        risk_summary["overallRisk"],
        risk_summary["riskLevel"],
    )

    # Step 6: Per-dimension explainability blocks
    explainability = [explain_dimension_risk(d) for d in dimensions]

    # Human-readable date
    now      = datetime.utcnow()
    date_str = now.strftime("%d %b %Y")

    # Features for the immediate API response (includes preview_traces for frontend)
    features_api = {
        **features,
        "preview_traces": preview_traces,
        "metadata":       metadata,
    }

    # Features for database persistence (excludes preview_traces and server paths)
    metadata_for_db = {k: v for k, v in metadata.items() if k != "quality_report"}
    metadata_for_db.pop("file_size", None)  # already stored as a top-level column
    features_for_db = {
        **features,
        "metadata": metadata_for_db,
    }

    audit_result = {
        "session_id":      session_id,
        "auditName":       audit_name or f"Audit — {file_name}",
        "fileName":        file_name,
        "fileSize":        metadata["file_size"],
        "description":     description,
        "analysisDate":    date_str,
        "createdAt":       now.isoformat(),
        "status":          "Complete",

        # Risk
        "overallRisk":     risk_summary["overallRisk"],
        "riskLevel":       risk_summary["riskLevel"],
        "overallSummary":  risk_summary["overallSummary"],
        "executiveSummary": risk_summary["executiveSummary"],
        "keyFindings":     risk_summary["keyFindings"],

        # Dimensions + explainability
        "dimensions":      dimensions,
        "explainability":  explainability,

        # Full features for API response (includes preview_traces)
        "features":        features_api,

        # Privacy-safe features for database (excludes preview_traces)
        "_features_for_db": features_for_db,

        # Quality gate results
        "qualityReport":   quality_report,

        # Recommendations
        "recommendations": recommendations,

        # Legal
        "disclaimer":      PRIVACY_DISCLAIMER,
    }

    return audit_result


__all__ = [
    # Loader
    "load_eeg_file",
    "generate_preview_traces",
    "check_eeg_quality",
    # Features
    "extract_features_from_raw",
    # Models
    "compute_dimension_risks",
    # Scoring
    "aggregate_privacy_risk",
    "PRIVACY_DISCLAIMER",
    # Recommendations
    "generate_recommendations",
    "explain_dimension_risk",
    "MitigationSimulator",
    # Pipeline
    "analyze_eeg_pipeline",
]

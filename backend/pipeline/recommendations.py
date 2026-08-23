"""
NeuroAudit Phase 2 — Privacy Mitigation Engine

Replaces the Phase 1 simplistic recommendation generator with a
structured, evidence-driven engine that produces research-grade
privacy controls.

Design principles
-----------------
1. Every recommendation is *dimension-specific* — a control is only
   emitted when there is heuristic evidence that it is relevant to the
   specific risk profile detected in the audit.
2. Evidence is stated explicitly for each recommendation so the reader
   can judge its reliability.
3. Quantitative risk-reduction claims are NOT made unless experimentally
   validated.  Where no validation exists the field ``expected_impact``
   is set to ``"REQUIRES_EMPIRICAL_VALIDATION"``.
4. All priority weights are labelled ``HEURISTIC_BASELINE``.
5. A ``MitigationSimulator`` class provides the architecture for future
   empirically-validated risk-delta calculations (Phase 3).

Recommendation structure (all fields present in every record)
-------------------------------------------------------------
{
    "id"              : str   — stable machine-readable identifier
    "number"          : str   — display order "01", "02", …
    "risk_dimension"  : str   — "IDENTITY" | "EMOTION" | "STRESS" | "WORKLOAD" | "GLOBAL"
    "title"           : str   — concise control name
    "priority"        : str   — "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
    "severity"        : str   — dimension risk level that triggered this control
    "evidence"        : list  — heuristic indicators supporting the recommendation
    "threat"          : str   — specific privacy-threat scenario
    "why"             : str   — rationale in plain language (backward-compat alias for "reason")
    "control"         : str   — control family
    "reason"          : str   — scientific/heuristic justification
    "implementation"  : list  — concrete implementation steps
    "action"          : str   — backward-compat summary of implementation
    "expected_impact" : str   — "HIGH" | "MEDIUM" | "LOW" | "REQUIRES_EMPIRICAL_VALIDATION"
    "residual_risk"   : str   — "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN"
    "evidence_status" : str   — "HEURISTIC_BASELINE" | "EMPIRICAL" | "MIXED"
}
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


# ---------------------------------------------------------------------------
# Priority scoring (HEURISTIC_BASELINE)
# ---------------------------------------------------------------------------
# Priority is computed from three factors:
#   severity_weight   : HIGH→3, MEDIUM→2, LOW→1
#   sensitivity_weight: how sensitive the inferred attribute is (hard-coded
#                        by dimension — labelled HEURISTIC_BASELINE)
#   exposure_weight   : score itself normalised to [0, 1]
#
# Final priority thresholds (HEURISTIC_BASELINE):
#   composite >= 7.0  → CRITICAL
#   composite >= 4.5  → HIGH
#   composite >= 2.5  → MEDIUM
#   else              → LOW

_SENSITIVITY_WEIGHT = {
    "IDENTITY": 3,    # uniquely identifying — highest sensitivity
    "EMOTION":  2,    # sensitive personal attribute
    "STRESS":   2,    # sensitive personal/health attribute
    "WORKLOAD": 1,    # contextual cognitive attribute
    "GLOBAL":   2,    # cross-cutting
}

_SEVERITY_WEIGHT = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
_PRIORITY_ORDER  = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


def _compute_priority(dimension: str, severity: str, score: int) -> str:
    """
    Compute recommendation priority from dimension sensitivity, severity, and
    normalised risk score.  All weights are HEURISTIC_BASELINE.
    """
    sw  = _SENSITIVITY_WEIGHT.get(dimension, 2)
    sev = _SEVERITY_WEIGHT.get(severity, 1)
    exp = score / 100.0
    composite = sw * sev * (1.0 + exp)   # range ~ [1, 12]

    if composite >= 7.0:
        return "CRITICAL"
    if composite >= 4.5:
        return "HIGH"
    if composite >= 2.5:
        return "MEDIUM"
    return "LOW"


# ---------------------------------------------------------------------------
# Mitigation Simulator (Phase 2 architecture; Phase 3 will fill estimates)
# ---------------------------------------------------------------------------

@dataclass
class MitigationSimulation:
    """
    Represents the projected risk after applying a specific control.

    In Phase 2, all ``projected_reduction`` values are None because no
    empirical validation has been performed.  The architecture is prepared
    so Phase 3 can populate these from experimental results.
    """
    control_id:           str
    current_risk:         int
    projected_reduction:  float | None   = None   # None = not yet validated
    projected_risk:       int   | None   = None   # None = not yet validated
    validation_status:    str           = "REQUIRES_EMPIRICAL_VALIDATION"
    notes:                str           = (
        "Projected risk reduction requires empirical validation. "
        "No quantitative estimate is provided at the HEURISTIC_BASELINE stage."
    )

    def to_dict(self) -> dict:
        return {
            "control_id":          self.control_id,
            "current_risk":        self.current_risk,
            "projected_reduction": self.projected_reduction,
            "projected_risk":      self.projected_risk,
            "validation_status":   self.validation_status,
            "notes":               self.notes,
        }


class MitigationSimulator:
    """
    Phase 2 stub for 'What if I apply this control?' simulations.

    ``simulate()`` always returns REQUIRES_EMPIRICAL_VALIDATION in Phase 2.
    Phase 3 will inject empirically-derived risk-delta functions per control.
    """

    # Registry for future empirical deltas:  control_id → callable(score) → delta
    _empirical_deltas: dict = {}

    @classmethod
    def register_empirical_delta(cls, control_id: str, fn) -> None:
        """Register an experimentally validated risk-reduction function."""
        cls._empirical_deltas[control_id] = fn

    @classmethod
    def simulate(cls, control_id: str, current_risk: int) -> MitigationSimulation:
        """
        Return the projected risk after applying ``control_id``.

        Phase 2: always returns REQUIRES_EMPIRICAL_VALIDATION.
        Phase 3: populate ``_empirical_deltas`` to return real estimates.
        """
        if control_id in cls._empirical_deltas:
            delta = cls._empirical_deltas[control_id](current_risk)
            proj  = max(0, min(100, int(round(current_risk - delta))))
            return MitigationSimulation(
                control_id=control_id,
                current_risk=current_risk,
                projected_reduction=delta,
                projected_risk=proj,
                validation_status="EMPIRICAL",
                notes="Reduction estimate derived from empirical validation study.",
            )
        return MitigationSimulation(
            control_id=control_id,
            current_risk=current_risk,
        )


# ---------------------------------------------------------------------------
# Control catalogue  (Parts D & G)
# ---------------------------------------------------------------------------
# Each entry is a template that is rendered into a full recommendation dict
# when the corresponding trigger condition is met.

def _mk_rec(
    *,
    rec_id:      str,
    dimension:   str,
    title:       str,
    control:     str,
    threat:      str,
    reason:      str,
    implementation: List[str],
    expected_impact: str,
    residual_risk:   str,
    evidence_status: str = "HEURISTIC_BASELINE",
) -> dict:
    """Construct a partial recommendation template."""
    return {
        "id":               rec_id,
        "risk_dimension":   dimension,
        "title":            title,
        "control":          control,
        "threat":           threat,
        "reason":           reason,
        "implementation":   implementation,
        "expected_impact":  expected_impact,
        "residual_risk":    residual_risk,
        "evidence_status":  evidence_status,
    }


# IDENTITY controls
_CTRL_IDENTITY_RBAC = _mk_rec(
    rec_id="identity-rbac",
    dimension="IDENTITY",
    title="Restrict Raw EEG Access & Enforce RBAC",
    control="Raw EEG access restriction",
    threat=(
        "Subject identification or cross-session linkage by an adversary with "
        "access to raw EEG and a pre-trained biometric fingerprinting model."
    ),
    reason=(
        "Raw EEG time-series retain spectral and spatial characteristics "
        "(IAPF, covariance topology) that are associated with biometric "
        "fingerprintability in published research (Marcel & Millán 2007). "
        "Restricting access is expected to reduce exposure, but the degree "
        "of reduction is not experimentally validated in this system."
    ),
    implementation=[
        "Enforce Role-Based Access Control (RBAC) — restrict raw EEG to named investigators.",
        "Separate storage of raw files from derived feature tables.",
        "Log every access event with timestamp, user ID, and purpose.",
        "Require ethics-board justification for raw file access beyond original protocol.",
    ],
    expected_impact="HIGH",
    residual_risk="MEDIUM",
)

_CTRL_IDENTITY_ENCRYPT = _mk_rec(
    rec_id="identity-encrypt",
    dimension="IDENTITY",
    title="Encrypt Stored EEG at Rest and in Transit",
    control="Encryption at rest and in transit",
    threat=(
        "Exfiltration of raw EEG files enabling offline re-identification."
    ),
    reason=(
        "Stored EEG recordings are long-lived privacy assets. Encryption "
        "at rest mitigates the impact of unauthorised file access; "
        "encryption in transit prevents interception. "
        "Expected to reduce effective exposure from file exfiltration; "
        "does not address in-process or authorised-user threats."
    ),
    implementation=[
        "Encrypt all EDF/FIF files at rest with AES-256 under managed keys.",
        "Enforce TLS 1.3 for all network transfers of EEG data.",
        "Rotate encryption keys on a defined schedule.",
        "Ensure key management is separate from the data store.",
    ],
    expected_impact="HIGH",
    residual_risk="LOW",
)

_CTRL_IDENTITY_PSEUDONYM = _mk_rec(
    rec_id="identity-pseudonymize",
    dimension="IDENTITY",
    title="Pseudonymize Participant Identifiers",
    control="Metadata minimization and pseudonymization",
    threat=(
        "Cross-dataset linkage using participant codes, demographic fields, "
        "or task metadata embedded in EDF file headers."
    ),
    reason=(
        "Direct identifiers in EDF headers combined with distinctive neural "
        "signal features facilitate cross-dataset linkage. Cryptographic "
        "pseudonymization separates the identity key from the signal file. "
        "This is standard practice in research ethics compliance."
    ),
    implementation=[
        "Strip all personal identifiers from EDF headers before archiving.",
        "Replace participant codes with cryptographically randomised study hashes.",
        "Store the identity→hash mapping in a separate HSM or key vault.",
        "Treat the mapping table as a restricted asset subject to the same RBAC as raw EEG.",
    ],
    expected_impact="HIGH",
    residual_risk="MEDIUM",
)

_CTRL_IDENTITY_CH_MIN = _mk_rec(
    rec_id="identity-channel-min",
    dimension="IDENTITY",
    title="Minimise Channel Coverage in Shared Datasets",
    control="Channel minimization",
    threat=(
        "Higher-density recordings (≥16 channels) provide richer spatial "
        "covariance structure that is easier to fingerprint across sessions."
    ),
    reason=(
        "Biometric fingerprintability is expected to decrease with fewer "
        "channels; however, the specific reduction has not been experimentally "
        "validated in this system. This should be evaluated for reduction "
        "before being cited as a quantitative mitigation."
    ),
    implementation=[
        "Share only the minimal channel set required for the analysis.",
        "Consider releasing feature-level summaries rather than full raw montages.",
        "Document the channel selection rationale in the data-sharing agreement.",
    ],
    expected_impact="REQUIRES_EMPIRICAL_VALIDATION",
    residual_risk="UNKNOWN",
)

_CTRL_IDENTITY_BIOMETRIC_TEST = _mk_rec(
    rec_id="identity-biometric-test",
    dimension="IDENTITY",
    title="Conduct Biometric Re-identification Testing Before Sharing",
    control="Biometric re-identification testing",
    threat=(
        "An external collaborator applies a biometric fingerprinting model "
        "to a shared dataset and re-identifies participants."
    ),
    reason=(
        "Proactive re-identification testing quantifies the actual exposure "
        "before data is shared externally. This converts a heuristic risk "
        "estimate into an empirical measurement."
    ),
    implementation=[
        "Apply one or more published EEG biometric models to the dataset.",
        "Report the identification accuracy in the data-sharing documentation.",
        "Apply additional controls if accuracy exceeds an agreed threshold.",
        "Repeat testing after applying any anonymisation technique.",
    ],
    expected_impact="HIGH",
    residual_risk="MEDIUM",
    evidence_status="MIXED",
)

# EMOTION controls
_CTRL_EMOTION_SECONDARY = _mk_rec(
    rec_id="emotion-secondary-use",
    dimension="EMOTION",
    title="Restrict Secondary Use of Frontal EEG Data",
    control="Secondary-use restriction",
    threat=(
        "A secondary researcher applies an affective decoding model to "
        "frontal EEG channels shared for a different stated purpose."
    ),
    reason=(
        "Frontal EEG containing FAA-supporting channels (FP1, FP2, F3, F4) "
        "is the primary substrate for affective state decoding. Restricting "
        "the scope of downstream use is expected to reduce unintended "
        "emotional disclosure, though empirical quantification is pending."
    ),
    implementation=[
        "Specify permitted uses of shared EEG in data-access agreements.",
        "Include explicit prohibitions on affective inference beyond the approved protocol.",
        "Monitor for secondary publications citing unexpected emotional analyses.",
        "Require notification if downstream researchers apply machine-learning models.",
    ],
    expected_impact="MEDIUM",
    residual_risk="MEDIUM",
)

_CTRL_EMOTION_SPECTRAL_MASK = _mk_rec(
    rec_id="emotion-spectral-masking",
    dimension="EMOTION",
    title="Apply Spectral Obfuscation on Frontal Channels",
    control="Privacy-preserving transformation",
    threat=(
        "Affective state inference using frontal alpha asymmetry from "
        "channels FP1, FP2, F3, or F4."
    ),
    reason=(
        "Targeted differential privacy noise injection or band-stop attenuation "
        "of the alpha band on frontal channels is expected to reduce FAA-based "
        "inference. The effectiveness depends on the noise magnitude, which "
        "must be calibrated against signal utility; this is not yet validated "
        "in this system."
    ),
    implementation=[
        "Apply calibrated Laplacian or Gaussian noise to alpha-band components of frontal channels.",
        "Alternatively, apply band-stop filtering at the IAPF ± 1 Hz on frontal channels.",
        "Validate that study-relevant features (e.g., event-related potentials) remain intact.",
        "Document obfuscation parameters in the data provenance record.",
    ],
    expected_impact="REQUIRES_EMPIRICAL_VALIDATION",
    residual_risk="UNKNOWN",
)

_CTRL_EMOTION_FEATURE_RELEASE = _mk_rec(
    rec_id="emotion-feature-release",
    dimension="EMOTION",
    title="Release Feature Summaries Instead of Raw Frontal EEG",
    control="Feature-level sharing",
    threat=(
        "Training an affective model directly on shared raw EEG signals."
    ),
    reason=(
        "Releasing aggregated spectral features (e.g., band-power averages) "
        "rather than raw time-series removes the temporal detail that affective "
        "models exploit. The degree of protection is use-case dependent and "
        "should be evaluated before being cited as sufficient mitigation."
    ),
    implementation=[
        "Derive and share band-power summary tables rather than raw EDF files.",
        "Ensure derived features cannot reconstruct the original signal.",
        "Include a data provenance note explaining what was removed.",
    ],
    expected_impact="REQUIRES_EMPIRICAL_VALIDATION",
    residual_risk="UNKNOWN",
)

# STRESS controls
_CTRL_STRESS_INFERENCE_RESTRICT = _mk_rec(
    rec_id="stress-inference-restrict",
    dimension="STRESS",
    title="Restrict Automated Stress Inference Access",
    control="Inference-access restriction",
    threat=(
        "Automated inference of participant stress levels from EEG beta/alpha "
        "patterns without participant consent, particularly in occupational or "
        "clinical contexts."
    ),
    reason=(
        "Stress is a sensitive personal health attribute. EEG beta-band "
        "elevation and alpha suppression are heuristic indicators of stress "
        "that could be exploited by automated screening tools. Restricting "
        "downstream model application is expected to reduce exposure."
    ),
    implementation=[
        "Prohibit automated stress inference in data-access agreements.",
        "Disallow release of data alongside stress-labelled annotations.",
        "Audit downstream analyses for stress classification outputs.",
    ],
    expected_impact="HIGH",
    residual_risk="MEDIUM",
)

_CTRL_STRESS_PURPOSE_LIMIT = _mk_rec(
    rec_id="stress-purpose-limitation",
    dimension="STRESS",
    title="Enforce Purpose Limitation for Stress-Sensitive EEG",
    control="Purpose limitation",
    threat=(
        "An EEG dataset collected for cognitive neuroscience is re-used for "
        "workplace stress monitoring or insurance risk assessment."
    ),
    reason=(
        "Purpose limitation (GDPR Art. 5(1)(b)) requires that personal data "
        "not be processed for purposes incompatible with the original. "
        "EEG with detectable stress markers is particularly at risk of "
        "contextual integrity violations."
    ),
    implementation=[
        "Define and document the specific processing purpose at collection.",
        "Include purpose-limitation clauses in participant consent forms.",
        "Restrict access requests that do not align with the original purpose.",
        "Establish a governance review process for secondary-use applications.",
    ],
    expected_impact="HIGH",
    residual_risk="LOW",
)

_CTRL_STRESS_PP_PROCESSING = _mk_rec(
    rec_id="stress-pp-processing",
    dimension="STRESS",
    title="Adopt Privacy-Preserving Processing for Shared Stress-Sensitive Data",
    control="Privacy-preserving processing",
    threat=(
        "A collaborator trains a stress-classification model using shared EEG."
    ),
    reason=(
        "Federated learning with (ε, δ)-differential privacy guarantees "
        "is expected to reduce leakage of stress-related patterns during "
        "collaborative model training. The privacy budget must be tuned for "
        "the specific use case; generic ε values are not provided here."
    ),
    implementation=[
        "Adopt a federated learning framework (e.g., PySyft, FATE) for multi-site analyses.",
        "Apply differential privacy with a defined and documented privacy budget (ε, δ).",
        "Validate that model utility is acceptable at the chosen privacy budget.",
        "Report the privacy budget and validation results in publications.",
    ],
    expected_impact="REQUIRES_EMPIRICAL_VALIDATION",
    residual_risk="UNKNOWN",
)

# WORKLOAD controls
_CTRL_WORKLOAD_MONITOR_MISUSE = _mk_rec(
    rec_id="workload-monitor-misuse",
    dimension="WORKLOAD",
    title="Prevent Workplace Monitoring Misuse of Workload EEG",
    control="Misuse prevention and purpose limitation",
    threat=(
        "EEG cognitive-load data collected in a research context is re-used "
        "for employee performance evaluation, productivity monitoring, or "
        "workplace AI surveillance."
    ),
    reason=(
        "Mental workload inference from EEG is particularly sensitive in "
        "occupational contexts, where it could affect employment decisions "
        "without explicit informed consent. This is a known AI-ethics risk "
        "(Bryson & Winfield 2017)."
    ),
    implementation=[
        "Explicitly prohibit workplace or performance monitoring applications in consent forms.",
        "Include contractual prohibition on occupational deployment in data-sharing agreements.",
        "Monitor for downstream commercial applications by grantees.",
        "Flag any workload-labelled datasets for enhanced governance review before sharing.",
    ],
    expected_impact="HIGH",
    residual_risk="MEDIUM",
)

_CTRL_WORKLOAD_ACCESS_LOG = _mk_rec(
    rec_id="workload-access-logging",
    dimension="WORKLOAD",
    title="Implement Access Logging for Workload-Labelled EEG",
    control="Access logging and audit trail",
    threat=(
        "Unauthorised or undisclosed access to workload-sensitive EEG data."
    ),
    reason=(
        "Access logging creates an audit trail that detects unauthorised use "
        "and supports post-hoc accountability. It does not prevent access "
        "but makes unauthorised access attributable."
    ),
    implementation=[
        "Log every read/write access to workload-labelled EEG files.",
        "Capture: timestamp, user identity, operation, and stated purpose.",
        "Review logs periodically for anomalous access patterns.",
        "Retain logs for a defined period consistent with ethics commitments.",
    ],
    expected_impact="MEDIUM",
    residual_risk="MEDIUM",
)

_CTRL_WORKLOAD_DATA_MIN = _mk_rec(
    rec_id="workload-data-minimization",
    dimension="WORKLOAD",
    title="Minimise Retention of Workload-Task EEG Beyond Study Needs",
    control="Data minimization and retention limits",
    threat=(
        "Long-term storage of cognitive-load recordings extending the window "
        "of potential re-use or exfiltration."
    ),
    reason=(
        "Data minimisation reduces the attack surface over time. "
        "Shorter retention windows limit the period during which novel "
        "inference techniques (not available at collection time) could be "
        "applied to the data."
    ),
    implementation=[
        "Define a maximum retention period at the start of the study.",
        "Archive or destroy raw files once initial analysis is complete.",
        "Apply automated lifecycle rules in the storage system.",
        "Document the retention policy in the Data Management Plan.",
    ],
    expected_impact="MEDIUM",
    residual_risk="LOW",
)

# GLOBAL controls (apply regardless of which dimension is elevated)
_CTRL_GLOBAL_ENCRYPT = _mk_rec(
    rec_id="global-encrypt",
    dimension="GLOBAL",
    title="Encrypt All Stored Neural Data (AES-256 / TLS 1.3)",
    control="Encryption at rest and in transit",
    threat="Exfiltration of any EEG file from the storage system or network.",
    reason=(
        "AES-256 at rest and TLS 1.3 in transit are baseline controls for any "
        "sensitive personal data. Neural recordings are classified as sensitive "
        "personal data under GDPR (Recital 35 — health data)."
    ),
    implementation=[
        "Encrypt all EEG files at rest with AES-256 under HSM-managed keys.",
        "Enforce TLS 1.3 for all API, file transfer, and web interfaces.",
        "Audit encryption coverage during security reviews.",
    ],
    expected_impact="HIGH",
    residual_risk="LOW",
)

_CTRL_GLOBAL_RETENTION = _mk_rec(
    rec_id="global-retention",
    dimension="GLOBAL",
    title="Enforce Automated Data Retention and Purging Policy",
    control="Data minimization and retention limits",
    threat="Accumulation of long-lived neural archives exploitable by future AI models.",
    reason=(
        "New inference techniques may be able to extract sensitive information "
        "from EEG recordings that could not be decoded at the time of collection. "
        "Limiting retention reduces the future risk surface."
    ),
    implementation=[
        "Define retention periods aligned to the ethics approval.",
        "Implement automated expiry rules in the storage infrastructure.",
        "Notify data custodians before scheduled deletion for review.",
        "Document all retention decisions in the audit log.",
    ],
    expected_impact="MEDIUM",
    residual_risk="LOW",
)

_CTRL_GLOBAL_FEDERATED = _mk_rec(
    rec_id="global-federated",
    dimension="GLOBAL",
    title="Adopt Federated Learning for Multi-Site EEG Analysis",
    control="Privacy-preserving federated processing",
    threat=(
        "Centralising raw EEG from multiple sites amplifies re-identification "
        "risk through cross-cohort linkage."
    ),
    reason=(
        "Federated learning keeps raw data on-site and shares only model gradients, "
        "which is expected to reduce raw-data exposure during collaborative analyses. "
        "The privacy guarantee depends on the differential-privacy budget applied "
        "to gradient updates; this requires per-study calibration."
    ),
    implementation=[
        "Adopt a federated framework (e.g., Flower, PySyft, FATE).",
        "Apply differential privacy with a documented (ε, δ) budget.",
        "Validate model utility at the chosen privacy budget before deployment.",
        "Publish the privacy budget alongside model performance results.",
    ],
    expected_impact="REQUIRES_EMPIRICAL_VALIDATION",
    residual_risk="UNKNOWN",
)


# ---------------------------------------------------------------------------
# Recommendation generator
# ---------------------------------------------------------------------------

def generate_recommendations(
    dimensions: list,
    overall_risk: int,
    risk_level: str,
) -> list:
    """
    Generate a prioritised list of structured privacy-mitigation recommendations.

    Parameters
    ----------
    dimensions   : list of RiskDimension dicts (from compute_dimension_risks)
    overall_risk : int  — overall privacy risk score (0–100)
    risk_level   : str  — "LOW" | "MEDIUM" | "HIGH"

    Returns
    -------
    list[dict]  — ordered list of recommendation dicts, CRITICAL first.
    """
    dim_map = {d["key"]: d for d in dimensions}
    id_dim  = dim_map.get("identity",  {})
    em_dim  = dim_map.get("emotion",   {})
    st_dim  = dim_map.get("stress",    {})
    wl_dim  = dim_map.get("workload",  {})

    id_score  = id_dim.get("score", 0)
    em_score  = em_dim.get("score", 0)
    st_score  = st_dim.get("score", 0)
    wl_score  = wl_dim.get("score", 0)

    id_level  = id_dim.get("level", "LOW")
    em_level  = em_dim.get("level", "LOW")
    st_level  = st_dim.get("level", "LOW")
    wl_level  = wl_dim.get("level", "LOW")

    selected: list[tuple[dict, list, str, str, int]] = []
    # Each entry: (template, evidence_list, dimension_key, severity, score)

    # ---- IDENTITY --------------------------------------------------------
    if id_score >= 65 or overall_risk >= 65:
        selected.append((_CTRL_IDENTITY_RBAC, [
            f"Biometric Uniqueness Index indicates elevated spatial covariance distinctiveness.",
            f"Identity risk score: {id_score}/100 (heuristic baseline).",
        ], "IDENTITY", id_level, id_score))

    if id_score >= 50:
        selected.append((_CTRL_IDENTITY_ENCRYPT, [
            f"Identity risk score: {id_score}/100 indicates the recording contains "
            "signal characteristics associated with biometric fingerprintability.",
        ], "IDENTITY", id_level, id_score))

    if id_score >= 50:
        selected.append((_CTRL_IDENTITY_PSEUDONYM, [
            f"Distinct spectral features (IAPF, covariance topology) increase "
            "the risk of cross-dataset linkage when combined with metadata.",
        ], "IDENTITY", id_level, id_score))

    if id_score >= 70:
        selected.append((_CTRL_IDENTITY_CH_MIN, [
            f"Recording has sufficient channels to support a rich spatial "
            "covariance signature.",
            f"Identity risk score: {id_score}/100.",
        ], "IDENTITY", id_level, id_score))

    if id_score >= 60 or overall_risk >= 60:
        selected.append((_CTRL_IDENTITY_BIOMETRIC_TEST, [
            f"High heuristic identity risk ({id_score}/100) warrants empirical "
            "validation of actual re-identification accuracy before sharing.",
        ], "IDENTITY", id_level, id_score))

    # ---- EMOTION ---------------------------------------------------------
    if em_score >= 50:
        selected.append((_CTRL_EMOTION_SECONDARY, [
            f"Frontal channel features (FAA, beta/gamma relative power) indicate "
            f"{em_level.lower()} affective decoding vulnerability.",
            f"Emotion risk score: {em_score}/100 (heuristic baseline).",
        ], "EMOTION", em_level, em_score))

    if em_score >= 60 or st_score >= 60:
        selected.append((_CTRL_EMOTION_SPECTRAL_MASK, [
            f"Emotion risk: {em_score}/100; Stress risk: {st_score}/100.",
            "Frontal alpha asymmetry and beta/gamma elevation are primary "
            "affective decoding indicators.",
        ], "EMOTION", em_level, em_score))

    if em_score >= 40:
        selected.append((_CTRL_EMOTION_FEATURE_RELEASE, [
            f"Emotion risk score: {em_score}/100 suggests frontal raw EEG contains "
            "affective-decoding-relevant structure.",
        ], "EMOTION", em_level, em_score))

    # ---- STRESS ----------------------------------------------------------
    if st_score >= 50:
        selected.append((_CTRL_STRESS_INFERENCE_RESTRICT, [
            f"Beta elevation and alpha suppression indicators reach {st_level.lower()} level.",
            f"Stress risk score: {st_score}/100 (heuristic baseline).",
        ], "STRESS", st_level, st_score))

    if st_score >= 40:
        selected.append((_CTRL_STRESS_PURPOSE_LIMIT, [
            f"Stress risk score: {st_score}/100 indicates the recording may "
            "support stress-related inference.",
            "Stress is classified as a sensitive health attribute.",
        ], "STRESS", st_level, st_score))

    if overall_risk >= 50:
        selected.append((_CTRL_STRESS_PP_PROCESSING, [
            f"Overall risk score: {overall_risk}/100 warrants privacy-preserving "
            "processing for any multi-site collaborative analysis.",
        ], "STRESS", st_level, st_score))

    # ---- WORKLOAD --------------------------------------------------------
    if wl_score >= 40:
        selected.append((_CTRL_WORKLOAD_MONITOR_MISUSE, [
            f"Cognitive workload markers (theta elevation, engagement index) "
            f"reach {wl_level.lower()} level.",
            f"Workload risk score: {wl_score}/100 (heuristic baseline).",
        ], "WORKLOAD", wl_level, wl_score))

    if wl_score >= 30:
        selected.append((_CTRL_WORKLOAD_ACCESS_LOG, [
            f"Workload risk score: {wl_score}/100.",
            "Occupational misuse of cognitive-load data is a documented AI-ethics risk.",
        ], "WORKLOAD", wl_level, wl_score))

    if wl_score >= 30:
        selected.append((_CTRL_WORKLOAD_DATA_MIN, [
            f"Workload risk score: {wl_score}/100.",
            "Future inference techniques may be able to extract more from retained data.",
        ], "WORKLOAD", wl_level, wl_score))

    # ---- GLOBAL ----------------------------------------------------------
    selected.append((_CTRL_GLOBAL_ENCRYPT, [
        "Neural recordings are sensitive personal data under GDPR Recital 35.",
        f"Overall risk: {overall_risk}/100.",
    ], "GLOBAL", risk_level, overall_risk))

    selected.append((_CTRL_GLOBAL_RETENTION, [
        f"Overall risk: {overall_risk}/100.",
        "Long retention windows expand future AI inference risk.",
    ], "GLOBAL", risk_level, overall_risk))

    if overall_risk >= 50:
        selected.append((_CTRL_GLOBAL_FEDERATED, [
            f"Overall risk: {overall_risk}/100 makes centralised raw-data aggregation inadvisable.",
        ], "GLOBAL", risk_level, overall_risk))

    # ---- Deduplicate by control id ----------------------------------------
    seen: set[str] = set()
    unique: list[tuple] = []
    for entry in selected:
        tmpl = entry[0]
        if tmpl["id"] not in seen:
            seen.add(tmpl["id"])
            unique.append(entry)

    # ---- Render + prioritise ----------------------------------------------
    rendered: list[dict] = []
    for (tmpl, evidence, dimension, severity, score) in unique:
        priority = _compute_priority(dimension, severity, score)
        action_summary = "; ".join(tmpl["implementation"][:2])
        why_text = tmpl["reason"]

        rec = {
            "id":             tmpl["id"],
            "risk_dimension": dimension,
            "title":          tmpl["title"],
            "priority":       priority,
            "severity":       severity,
            "evidence":       evidence,
            "threat":         tmpl["threat"],
            # Backward-compat aliases for frontend / PDF:
            "why":            why_text,
            "action":         action_summary,
            # Full structured fields:
            "control":        tmpl["control"],
            "reason":         why_text,
            "implementation": tmpl["implementation"],
            "expected_impact": tmpl["expected_impact"],
            "residual_risk":  tmpl["residual_risk"],
            "evidence_status": tmpl["evidence_status"],
        }
        rendered.append(rec)

    # Sort: CRITICAL → HIGH → MEDIUM → LOW
    rendered.sort(key=lambda r: _PRIORITY_ORDER.get(r["priority"], 99))

    # Assign sequential numbers
    for idx, rec in enumerate(rendered):
        rec["number"] = f"{idx + 1:02d}"

    return rendered


# ---------------------------------------------------------------------------
# Explainability helper (Part F)
# ---------------------------------------------------------------------------

def explain_dimension_risk(dimension: dict) -> dict:
    """
    Return a structured explainability block for a single risk dimension.

    The block lists the heuristic indicators that contributed to the score
    and explicitly labels them as HEURISTIC_BASELINE estimates.

    Returns
    -------
    dict with keys:
        dimension_label     : str
        score               : int
        level               : str
        why_elevated        : str   — plain-language explanation
        contributing_indicators : list[str]
        model_type          : str
        caution             : str   — standard epistemological caveat
    """
    label    = dimension.get("label", "Unknown")
    score    = dimension.get("score", 0)
    level    = dimension.get("level", "LOW")
    model    = dimension.get("model_type", "HEURISTIC_BASELINE")
    inds     = dimension.get("contributing_indicators", [])
    explain  = dimension.get("explanation", "")

    if score >= 70:
        why = f"The heuristic baseline indicates {level.lower()} {label.lower()}-related inference exposure."
    elif score >= 40:
        why = f"The heuristic baseline indicates moderate {label.lower()}-related inference exposure."
    else:
        why = f"The heuristic baseline indicates low {label.lower()}-related inference exposure."

    return {
        "dimension_label":          label,
        "score":                    score,
        "level":                    level,
        "why_elevated":             why,
        "contributing_indicators":  inds if inds else [explain],
        "model_type":               model,
        "caution": (
            "These are heuristic indicators computed from signal spectral features. "
            "They do not constitute a clinical diagnosis, a confirmed privacy "
            "determination, or a prediction of actual attack success probability."
        ),
    }

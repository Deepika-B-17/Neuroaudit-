"""
Heuristic privacy risk dimension calculators for NeuroAudit.

IMPORTANT — Classification of this module
==========================================
All four scoring functions in this module are HEURISTIC_BASELINE models.
They are NOT trained machine-learning models.  No labelled dataset was used
to fit any parameters.  All weights, offsets, and clipping bounds are set by
domain-knowledge heuristics and are explicitly labelled as such.

The module is structured so that each heuristic can be replaced by a trained
inference function in Phase 3 (ML integration) without touching the pipeline
coordinator or the scoring aggregator.

Naming-fix notice (Phase 2)
============================
The Phase 1 audit identified a misleading variable name in the Emotion risk
calculator:

  Old name: de_beta_gamma   (suggested "Differential Entropy" of beta/gamma)
  Actual:   (rel_beta + rel_gamma) / 100.0
            i.e. the sum of RELATIVE BAND POWERS for beta and gamma,
            scaled to [0, 1].

The variable has been renamed to ``beta_gamma_rel_power`` with an explicit
comment.  The numerical formula is UNCHANGED.

Scientific references per dimension are cited inline.
"""

import numpy as np


# ---------------------------------------------------------------------------
# Risk-level thresholds (HEURISTIC_BASELINE)
# ---------------------------------------------------------------------------
# Justification: Symmetric tercile split of the [0, 100] score range.
# These thresholds have not been calibrated against validated privacy-exposure
# ground-truth labels.

_HIGH_THRESHOLD   = 70
_MEDIUM_THRESHOLD = 40


def _level(score: int) -> str:
    if score >= _HIGH_THRESHOLD:
        return "HIGH"
    if score >= _MEDIUM_THRESHOLD:
        return "MEDIUM"
    return "LOW"


def _clip_score(value: float, lo: int, hi: int) -> int:
    """Round and clip a raw score to the integer interval [lo, hi]."""
    return int(np.clip(round(value), lo, hi))


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def compute_dimension_risks(features: dict, metadata: dict) -> list:
    """
    Compute four privacy risk dimension scores from extracted EEG features.

    Parameters
    ----------
    features : dict
        Output of ``extract_features_from_raw()``.
    metadata : dict
        Recording metadata from ``load_eeg_file()``.

    Returns
    -------
    list[dict]
        Four RiskDimension dicts: [identity, emotion, stress, workload].
        Each dict includes:
          key, label, score (0-100), level, summary, explanation, concern,
          contributing_indicators, model_type.
    """
    # ---- Unpack features ---------------------------------------------------
    band_powers = features.get("global_band_powers", {})
    rel_delta = band_powers.get("delta", 20.0)   # noqa: F841  (available for future use)
    rel_theta = band_powers.get("theta", 20.0)
    rel_alpha = band_powers.get("alpha", 20.0)
    rel_beta  = band_powers.get("beta",  20.0)
    rel_gamma = band_powers.get("gamma", 20.0)

    faa              = features.get("frontal_alpha_asymmetry",   0.0)
    tbr              = features.get("theta_beta_ratio",          1.0)
    iapf             = features.get("iapf_hz",                  10.0)
    bui              = features.get("biometric_uniqueness_index", 0.5)
    hjorth_complexity = features.get("hjorth_complexity",         1.0)
    engagement_val   = features.get("engagement_index",          0.5)
    n_channels       = features.get("channel_count",              8)
    duration_sec     = features.get("duration_sec",              60.0)

    quality_ok = metadata.get("quality_report", {}).get("sufficient_for_assessment", True)

    # =========================================================================
    # Dimension 1 — Identity Privacy Risk (Biometric Fingerprintability)
    # =========================================================================
    # Scientific basis
    # ----------------
    # EEG spectral features are stable within-subject and discriminable
    # between subjects, supporting re-identification across sessions.
    # Key biometric markers: IAPF (Klimesch 1999; Poulos et al. 2002),
    # spatial covariance structure (Marcel & Millán 2007).
    #
    # Heuristic formula (HEURISTIC_BASELINE)
    # ----------------------------------------
    # ch_factor   : more recording channels → richer spatial signature
    # dur_factor  : longer recording → more stable frequency fingerprint
    # iapf_dist   : deviation of IAPF from population mean (10 Hz) → individuality
    # bui         : eigenvalue spread of correlation matrix → unique topology
    #
    # Weights [40, 30, 15, 15] and reference values (16 ch, 30 s, 10 Hz, 2.5 Hz
    # spread) are chosen by domain heuristic; not validated against labelled data.

    ch_factor    = min(1.0, n_channels / 16.0)
    dur_factor   = min(1.0, duration_sec / 30.0)
    iapf_dist    = abs(iapf - 10.0) / 2.5          # population mean = 10 Hz (HEURISTIC_BASELINE)

    id_base = (
        (bui         * 40.0) +
        (ch_factor   * 30.0) +
        (dur_factor  * 15.0) +
        (iapf_dist   * 15.0)
    )
    id_score = _clip_score(id_base, 20, 96)
    id_level = _level(id_score)

    id_dim = {
        "key":   "identity",
        "label": "Identity",
        "score": id_score,
        "level": id_level,
        "summary": "Potential for identity-related inference from EEG signal structure.",
        "explanation": (
            f"The heuristic baseline estimates {id_level.lower()} identity-related privacy "
            f"exposure based on signal characteristics that are associated with biometric "
            f"fingerprintability in published literature. "
            f"Individual alpha peak frequency: {iapf:.2f} Hz; "
            f"biometric uniqueness index: {bui:.3f}; "
            f"{n_channels} channels recorded over {duration_sec:.1f}s. "
            f"These are heuristic indicators, not experimentally validated identifiability scores."
        ),
        "concern": (
            "Raw EEG recordings that are retained alongside linking metadata "
            "(participant codes, timestamps, task logs) may contain signal "
            "characteristics that could support subject re-identification under "
            "an appropriately trained model."
        ),
        "contributing_indicators": [
            f"Biometric Uniqueness Index: {bui:.3f}  [weight 40% — HEURISTIC_BASELINE]",
            f"Channel count: {n_channels}  [weight 30% — HEURISTIC_BASELINE]",
            f"Recording duration: {duration_sec:.1f}s  [weight 15% — HEURISTIC_BASELINE]",
            f"IAPF deviation from 10 Hz: {iapf_dist:.3f}  [weight 15% — HEURISTIC_BASELINE]",
        ],
        "contributors": [
            {
                "feature": "Biometric Uniqueness Index (BUI)",
                "raw_value": round(float(bui), 4),
                "normalized_value": round(float(bui), 4),
                "weight": 0.40,
                "contribution": round(float(bui * 40.0), 2),
            },
            {
                "feature": "Channel Count Factor",
                "raw_value": int(n_channels),
                "normalized_value": round(float(ch_factor), 4),
                "weight": 0.30,
                "contribution": round(float(ch_factor * 30.0), 2),
            },
            {
                "feature": "Recording Duration Factor",
                "raw_value": round(float(duration_sec), 2),
                "normalized_value": round(float(dur_factor), 4),
                "weight": 0.15,
                "contribution": round(float(dur_factor * 15.0), 2),
            },
            {
                "feature": "IAPF Deviation from 10Hz",
                "raw_value": round(float(iapf), 2),
                "normalized_value": round(float(iapf_dist), 4),
                "weight": 0.15,
                "contribution": round(float(iapf_dist * 15.0), 2),
            },
        ],
        "model_type": "HEURISTIC_BASELINE",
        "quality_qualified": not quality_ok,
    }

    # =========================================================================
    # Dimension 2 — Emotion Privacy Risk (Affective Decoding Vulnerability)
    # =========================================================================
    # Scientific basis
    # ----------------
    # Frontal Alpha Asymmetry (FAA) is a marker of affective valence in the
    # approach-withdrawal model (Davidson 1998; Harmon-Jones & Allen 1998).
    # Elevated beta/gamma activity is associated with high arousal states
    # (Ray & Cole 1985; Müller et al. 2000).
    #
    # Heuristic formula (HEURISTIC_BASELINE)
    # ----------------------------------------
    # faa_mag              : |FAA| magnitude (clamped at 2.0) — asymmetry strength
    # beta_gamma_rel_power : sum of relative beta + gamma band powers / 100
    #                        → normalised high-arousal indicator
    #                        NOTE: This uses RELATIVE BAND POWER, NOT Differential Entropy.
    #                        The variable was previously misnamed "de_beta_gamma" in Phase 1;
    #                        it has been renamed here to avoid ambiguity.
    # ch_spatial_factor    : channel count relative to 8-channel minimum for FAA

    faa_mag = min(2.0, abs(faa))

    # RENAMED from de_beta_gamma → beta_gamma_rel_power
    # Formula: (rel_beta + rel_gamma) / 100.0  ∈ [0, 1]
    # This is the combined relative power of beta and gamma bands, scaled to [0,1].
    # It is NOT Differential Entropy.  The actual Differential Entropy values are
    # in features["differential_entropy"] and are currently not wired into this score.
    beta_gamma_rel_power = (rel_beta + rel_gamma) / 100.0

    ch_spatial_factor = min(1.0, n_channels / 8.0)

    emotion_base = (
        (faa_mag / 2.0 * 45.0)          +   # FAA contribution [45%]
        (beta_gamma_rel_power * 40.0)    +   # Beta+Gamma relative power [40%]
        (ch_spatial_factor * 15.0)           # Channel coverage [15%]
    )
    emotion_score = _clip_score(emotion_base, 18, 94)
    emotion_level = _level(emotion_score)

    emotion_dim = {
        "key":   "emotion",
        "label": "Emotion",
        "score": emotion_score,
        "level": emotion_level,
        "summary": "Potential for emotion-related inference from frontal EEG patterns.",
        "explanation": (
            f"The heuristic baseline indicates {emotion_level.lower()} emotion-related "
            f"privacy exposure based on frontal spectral asymmetry and high-frequency "
            f"band activity. "
            f"Frontal Alpha Asymmetry (FAA): {faa:+.3f}; "
            f"Beta + Gamma relative power: {rel_beta + rel_gamma:.1f}%. "
            f"These are heuristic indicators of affective decoding vulnerability, not "
            f"confirmed emotional state classifications."
        ),
        "concern": (
            "EEG recordings that contain frontal channel data may allow affective state "
            "inference under appropriately trained decoding models. Sharing minimally "
            "processed frontal EEG beyond the original research purpose is expected to "
            "increase this exposure."
        ),
        "contributing_indicators": [
            f"FAA magnitude |{faa:+.3f}|  [weight 45% — HEURISTIC_BASELINE]",
            f"Beta + Gamma relative power: {rel_beta + rel_gamma:.1f}%  [weight 40% — HEURISTIC_BASELINE]",
            f"Channel spatial factor: {ch_spatial_factor:.2f}  [weight 15% — HEURISTIC_BASELINE]",
        ],
        "contributors": [
            {
                "feature": "Frontal Alpha Asymmetry Magnitude",
                "raw_value": round(float(faa), 4),
                "normalized_value": round(float(faa_mag / 2.0), 4),
                "weight": 0.45,
                "contribution": round(float(faa_mag / 2.0 * 45.0), 2),
            },
            {
                "feature": "Beta + Gamma Relative Power",
                "raw_value": round(float(rel_beta + rel_gamma), 2),
                "normalized_value": round(float(beta_gamma_rel_power), 4),
                "weight": 0.40,
                "contribution": round(float(beta_gamma_rel_power * 40.0), 2),
            },
            {
                "feature": "Channel Spatial Factor",
                "raw_value": int(n_channels),
                "normalized_value": round(float(ch_spatial_factor), 4),
                "weight": 0.15,
                "contribution": round(float(ch_spatial_factor * 15.0), 2),
            },
        ],
        "model_type": "HEURISTIC_BASELINE",
        "quality_qualified": not quality_ok,
    }

    # =========================================================================
    # Dimension 3 — Stress Privacy Risk (Autonomic & Mental Stress Exposure)
    # =========================================================================
    # Scientific basis
    # ----------------
    # Acute mental stress is associated with beta-band elevation and alpha-band
    # suppression (Aftanas & Golocheikine 2001; Seo & Lee 2010).
    # Hjorth complexity increases with high-frequency, irregular activity
    # characteristic of sympathetic arousal (Hjorth 1970).
    #
    # Heuristic formula (HEURISTIC_BASELINE)
    # ----------------------------------------
    # beta_elevation   : excess beta above 12% baseline (HEURISTIC_BASELINE threshold)
    # alpha_suppression: deficit of alpha below 25% baseline (HEURISTIC_BASELINE threshold)
    # complexity_factor: Hjorth complexity above 0.8 offset (HEURISTIC_BASELINE threshold)

    beta_elevation    = max(0.0, (rel_beta  - 12.0) / 25.0)   # HEURISTIC_BASELINE: baseline 12 %, scale 25 %
    alpha_suppression = max(0.0, (25.0 - rel_alpha) / 25.0)   # HEURISTIC_BASELINE: baseline 25 %, scale 25 %
    complexity_factor = min(1.0, max(0.0, (hjorth_complexity - 0.8) / 1.5))  # HEURISTIC_BASELINE

    stress_base = (
        (beta_elevation    * 45.0) +    # Beta elevation [45%]
        (alpha_suppression * 30.0) +    # Alpha suppression [30%]
        (complexity_factor * 25.0)      # Signal complexity [25%]
    )
    stress_score = _clip_score(stress_base, 15, 95)
    stress_level = _level(stress_score)

    stress_dim = {
        "key":   "stress",
        "label": "Stress",
        "score": stress_score,
        "level": stress_level,
        "summary": "Potential for stress-related inference from spectral and complexity markers.",
        "explanation": (
            f"The heuristic baseline indicates {stress_level.lower()} stress-related "
            f"privacy exposure based on spectral characteristics associated with "
            f"sympathetic arousal in the neuroscientific literature. "
            f"Beta relative power: {rel_beta:.1f}% (baseline 12%); "
            f"Alpha relative power: {rel_alpha:.1f}% (baseline 25%); "
            f"Hjorth complexity: {hjorth_complexity:.3f} (offset 0.8). "
            f"This is a heuristic indicator, not a clinical stress diagnosis."
        ),
        "concern": (
            "EEG channel-level data that contains stress-related spectral markers "
            "may support automated inference of participant stress levels under "
            "appropriate trained models, particularly when combined with task "
            "timestamps or performance data."
        ),
        "contributing_indicators": [
            f"Beta elevation above 12% baseline: {beta_elevation:.3f}  [weight 45% — HEURISTIC_BASELINE]",
            f"Alpha suppression below 25% baseline: {alpha_suppression:.3f}  [weight 30% — HEURISTIC_BASELINE]",
            f"Hjorth complexity factor: {complexity_factor:.3f}  [weight 25% — HEURISTIC_BASELINE]",
        ],
        "contributors": [
            {
                "feature": "Beta Power Elevation (>12%)",
                "raw_value": round(float(rel_beta), 2),
                "normalized_value": round(float(beta_elevation), 4),
                "weight": 0.45,
                "contribution": round(float(beta_elevation * 45.0), 2),
            },
            {
                "feature": "Alpha Power Suppression (<25%)",
                "raw_value": round(float(rel_alpha), 2),
                "normalized_value": round(float(alpha_suppression), 4),
                "weight": 0.30,
                "contribution": round(float(alpha_suppression * 30.0), 2),
            },
            {
                "feature": "Hjorth Complexity Factor (>0.8)",
                "raw_value": round(float(hjorth_complexity), 4),
                "normalized_value": round(float(complexity_factor), 4),
                "weight": 0.25,
                "contribution": round(float(complexity_factor * 25.0), 2),
            },
        ],
        "model_type": "HEURISTIC_BASELINE",
        "quality_qualified": not quality_ok,
    }

    # =========================================================================
    # Dimension 4 — Mental Workload Privacy Risk (Cognitive Load Exposure)
    # =========================================================================
    # Scientific basis
    # ----------------
    # Frontal midline theta elevation is a robust marker of working memory
    # and cognitive load (Gevins et al. 1997; Onton et al. 2005).
    # The Pope Engagement Index (beta / (theta + alpha)) tracks active task
    # engagement (Pope, Bogart & Bartolome 1995).
    # The Theta/Beta ratio is used as a complementary load index
    # (Barry et al. 2003).
    #
    # Heuristic formula (HEURISTIC_BASELINE)
    # ----------------------------------------
    # theta_elevation  : theta relative power normalised to 30% saturation
    # engagement_factor: EI normalised to 1.2 saturation
    # tbr_factor       : TBR above 0.5 baseline, scale 2.0

    theta_elevation  = min(1.0, rel_theta / 30.0)                              # HEURISTIC_BASELINE
    engagement_factor = min(1.0, engagement_val / 1.2)                         # HEURISTIC_BASELINE
    tbr_factor        = min(1.0, max(0.0, (tbr - 0.5) / 2.0))                  # HEURISTIC_BASELINE

    workload_base = (
        (theta_elevation   * 35.0) +    # Theta elevation [35%]
        (engagement_factor * 35.0) +    # Engagement index [35%]
        (tbr_factor        * 30.0)      # Theta/Beta ratio [30%]
    )
    workload_score = _clip_score(workload_base, 15, 95)
    workload_level = _level(workload_score)

    workload_dim = {
        "key":   "workload",
        "label": "Mental Workload",
        "score": workload_score,
        "level": workload_level,
        "summary": "Potential for cognitive workload inference from theta and engagement markers.",
        "explanation": (
            f"The heuristic baseline indicates {workload_level.lower()} cognitive workload "
            f"privacy exposure based on theta-band elevation and engagement-index markers "
            f"associated with mental workload in published research. "
            f"Theta relative power: {rel_theta:.1f}%; "
            f"Theta/Beta ratio: {tbr:.3f}; "
            f"Engagement Index: {engagement_val:.3f}. "
            f"This is a heuristic indicator, not a validated workload measurement."
        ),
        "concern": (
            "EEG data containing frontal theta and engagement markers could support "
            "inference of cognitive load and task demand under trained models. "
            "Combining this data with interaction logs or performance records is "
            "expected to increase this exposure."
        ),
        "contributing_indicators": [
            f"Theta elevation (normalised): {theta_elevation:.3f}  [weight 35% — HEURISTIC_BASELINE]",
            f"Engagement Index factor: {engagement_factor:.3f}  [weight 35% — HEURISTIC_BASELINE]",
            f"Theta/Beta ratio factor: {tbr_factor:.3f}  [weight 30% — HEURISTIC_BASELINE]",
        ],
        "contributors": [
            {
                "feature": "Theta Power Elevation",
                "raw_value": round(float(rel_theta), 2),
                "normalized_value": round(float(theta_elevation), 4),
                "weight": 0.35,
                "contribution": round(float(theta_elevation * 35.0), 2),
            },
            {
                "feature": "Pope Engagement Index",
                "raw_value": round(float(engagement_val), 4),
                "normalized_value": round(float(engagement_factor), 4),
                "weight": 0.35,
                "contribution": round(float(engagement_factor * 35.0), 2),
            },
            {
                "feature": "Theta/Beta Ratio (>0.5)",
                "raw_value": round(float(tbr), 4),
                "normalized_value": round(float(tbr_factor), 4),
                "weight": 0.30,
                "contribution": round(float(tbr_factor * 30.0), 2),
            },
        ],
        "model_type": "HEURISTIC_BASELINE",
        "quality_qualified": not quality_ok,
    }

    return [id_dim, emotion_dim, stress_dim, workload_dim]

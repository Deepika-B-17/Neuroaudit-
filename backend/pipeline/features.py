"""
EEG feature extraction for NeuroAudit.

Implements 16 feature-extraction algorithms producing 20 numerical outputs.

Feature inventory (all computed on preprocessed MNE Raw):
  1-5.  Absolute band powers  — Delta, Theta, Alpha, Beta, Gamma  (via Welch PSD)
  6.    Relative band powers   — normalised to 0-100 %  (5 values from bands above)
  7.    Power Spectral Density — Welch periodogram  (intermediate; basis for bands)
  8.    Frontal Alpha Asymmetry (FAA)
  9.    Theta/Beta Ratio (TBR)
  10.   Theta/Alpha Ratio (TAR)
  11.   Engagement Index (EI)  — Pope, Bogart & Bartolome (1995)
  12.   Individual Alpha Peak Frequency (IAPF)
  13.   Differential Entropy (DE) — per band (5 values)
  14.   Hjorth Activity
  15.   Hjorth Mobility
  16.   Hjorth Complexity
  (Composite) Biometric Uniqueness Index (BUI) — eigenvalue spread of corr matrix

Note on counting: items 1-5 and their relative-power forms share the same
PSD computation; the feature *dictionary* contains 20 distinct numeric
scalars / sub-values.

Scientific references are documented inline per feature.
"""

import numpy as np
from scipy import signal

# ---------------------------------------------------------------------------
# Frequency band definitions
# ---------------------------------------------------------------------------

FREQ_BANDS = {
    "delta": (0.5,  4.0),
    "theta": (4.0,  8.0),
    "alpha": (8.0, 13.0),
    "beta":  (13.0, 30.0),
    "gamma": (30.0, 45.0),
}


# ---------------------------------------------------------------------------
# NaN / Inf sanitiser
# ---------------------------------------------------------------------------

def _safe_scalar(value: float, fallback: float = 0.0) -> float:
    """Replace NaN or Inf with *fallback*; round to 6 significant figures."""
    if not np.isfinite(value):
        return fallback
    return float(value)


def _sanitize_array(arr: np.ndarray, fill: float = 0.0) -> np.ndarray:
    """Replace all NaN and Inf values in *arr* with *fill*."""
    arr = np.where(np.isnan(arr), fill, arr)
    arr = np.where(np.isinf(arr), fill, arr)
    return arr


# Compatibility helper for numpy trapz/trapezoid
_trapz = getattr(np, "trapezoid", getattr(np, "trapz", None))


# ---------------------------------------------------------------------------
# Main extraction function
# ---------------------------------------------------------------------------

def extract_features_from_raw(raw) -> dict:
    """
    Extract all 16 feature algorithms from a preprocessed MNE Raw instance.

    Returns a flat dict of features, all values guaranteed finite (no NaN/Inf).

    The returned dict key ``global_band_powers`` contains *relative* band
    powers as percentages (0-100).  The internal ``band_powers_abs`` variable
    holds the absolute µV² values used for ratio calculations.
    """
    sfreq      = float(raw.info.get("sfreq", 0.0))
    if sfreq <= 0:
        raise ValueError(f"Invalid sampling rate sfreq={sfreq}: must be positive.")

    data       = raw.get_data()              # (n_channels, n_times)  [V]
    if data.ndim != 2 or data.shape[0] == 0 or data.shape[1] == 0:
        raise ValueError("EEG data must be a 2D array with at least 1 channel and 1 sample.")

    ch_names   = [ch.upper() for ch in raw.ch_names]
    n_channels, n_times = data.shape

    # Sanitise raw data first
    data = _sanitize_array(data)

    # -------------------------------------------------------------------------
    # Features 1-7: Welch PSD + Band Powers
    # Reference: Welch (1967), IEEE Trans. Audio Electroacoust.
    # -------------------------------------------------------------------------
    # Window length: 2-second segments (standard for EEG PSD estimation)
    nperseg = min(n_times, int(sfreq * 2))
    if nperseg < 16:
        nperseg = n_times   # fall back for very short signals
    if nperseg < 1:
        nperseg = 1

    freqs, psd = signal.welch(data, fs=sfreq, nperseg=nperseg, axis=-1)
    psd = _sanitize_array(psd)

    # Absolute band power per channel: ∫ PSD(f) df  (trapezoid rule)
    band_powers_abs: dict[str, np.ndarray] = {}
    for band, (fmin, fmax) in FREQ_BANDS.items():
        idx = np.logical_and(freqs >= fmin, freqs <= fmax)
        if np.any(idx):
            if np.count_nonzero(idx) == 1:
                # Single frequency bin fallback
                bp = psd[:, idx].squeeze(axis=-1)
            else:
                bp = _trapz(psd[:, idx], freqs[idx], axis=-1)
        else:
            bp = np.zeros(n_channels)
        band_powers_abs[band] = np.maximum(0.0, _sanitize_array(bp))

    # Relative band powers normalised to total power (summed across all 5 bands)
    total_power = np.sum(list(band_powers_abs.values()), axis=0) + 1e-12
    band_powers_rel = {
        band: band_powers_abs[band] / total_power
        for band in FREQ_BANDS
    }

    # Global averages → 0-100 % (mean across channels)
    global_band_powers = {
        band: _safe_scalar(float(np.mean(band_powers_rel[band])) * 100.0)
        for band in FREQ_BANDS
    }

    # Shorthand scalars for downstream calculations
    rel_delta = global_band_powers["delta"]
    rel_theta = global_band_powers["theta"]
    rel_alpha = global_band_powers["alpha"]
    rel_beta  = global_band_powers["beta"]
    rel_gamma = global_band_powers["gamma"]

    # -------------------------------------------------------------------------
    # Feature 8: Frontal Alpha Asymmetry (FAA)
    # Formula: FAA = ln(α_right) − ln(α_left)
    # Reference: Davidson (1998, 2004) — approach-withdrawal affective model
    # Channels: FP2/F4 (right), FP1/F3 (left)
    #
    # Bug fix (Phase 2): The original f3_idx lookup used "FP1" as a fallback
    # candidate, which could return the same electrode index as fp1_idx, making
    # the elif branch compute FAA between an electrode and itself (→ always 0).
    # Corrected to use distinct right-hemisphere candidates only.
    # -------------------------------------------------------------------------
    def get_ch_index(*candidates):
        for cand in candidates:
            cu = cand.upper()
            for idx, ch in enumerate(ch_names):
                if cu in ch:
                    return idx
        return None

    fp1_idx = get_ch_index("FP1", "F3", "F7")   # left hemisphere
    fp2_idx = get_ch_index("FP2", "F4", "F8")   # right hemisphere
    # Secondary FAA pair: F3 (left) / F4 (right) — no cross-hemisphere fallbacks
    f3_idx  = get_ch_index("F3",  "AF3", "FC1")  # FIXED: removed "FP1" fallback
    f4_idx  = get_ch_index("F4",  "AF4", "FC2")  # FIXED: removed "FP2" fallback

    if fp2_idx is not None and fp1_idx is not None and fp2_idx != fp1_idx:
        # Primary pair: FP2 (right) vs FP1 (left)
        right_alpha = max(1e-9, float(band_powers_abs["alpha"][fp2_idx]))
        left_alpha  = max(1e-9, float(band_powers_abs["alpha"][fp1_idx]))
    elif (f4_idx is not None and f3_idx is not None
          and f4_idx != f3_idx and f4_idx != fp1_idx and f3_idx != fp2_idx):
        # Secondary pair: F4 (right) vs F3 (left)
        right_alpha = max(1e-9, float(band_powers_abs["alpha"][f4_idx]))
        left_alpha  = max(1e-9, float(band_powers_abs["alpha"][f3_idx]))
    else:
        # Fallback: no valid asymmetric pair found → FAA = 0 (symmetric assumption)
        mean_alpha  = max(1e-9, float(np.mean(band_powers_abs["alpha"])))
        right_alpha = mean_alpha
        left_alpha  = mean_alpha

    faa = _safe_scalar(np.log(right_alpha) - np.log(left_alpha))

    # -------------------------------------------------------------------------
    # Features 9 & 10: Theta/Beta Ratio (TBR) and Theta/Alpha Ratio (TAR)
    # Reference: Barry et al. (2003) Clin. Neurophysiol.
    # -------------------------------------------------------------------------
    global_theta_abs = _safe_scalar(float(np.mean(band_powers_abs["theta"])))
    global_beta_abs  = _safe_scalar(float(np.mean(band_powers_abs["beta"])))  + 1e-12
    global_alpha_abs = _safe_scalar(float(np.mean(band_powers_abs["alpha"]))) + 1e-12
    global_gamma_abs = _safe_scalar(float(np.mean(band_powers_abs["gamma"])))

    # Guard theta against negative values (can occur after NaN sanitisation on
    # very short or near-flat signals) before using it in ratio denominators.
    global_theta_abs_safe = max(0.0, global_theta_abs)

    tbr = _safe_scalar(global_theta_abs_safe / global_beta_abs)
    tar = _safe_scalar(global_theta_abs_safe / global_alpha_abs)

    # -------------------------------------------------------------------------
    # Feature 11: Engagement Index (EI)
    # Formula: EI = β / (θ + α)
    # Reference: Pope, Bogart & Bartolome (1995) Biol. Psychol.
    # -------------------------------------------------------------------------
    engagement_index = _safe_scalar(
        global_beta_abs / (global_theta_abs_safe + global_alpha_abs + 1e-12)
    )

    # -------------------------------------------------------------------------
    # Feature 12: Individual Alpha Peak Frequency (IAPF)
    # Formula: argmax PSD in [7.5, 12.5] Hz (average across channels)
    # Reference: Klimesch (1999); Posthuma et al. (2001) — biometric stability
    # -------------------------------------------------------------------------
    alpha_mask = np.logical_and(freqs >= 7.5, freqs <= 12.5)
    if np.any(alpha_mask):
        alpha_psd_avg = np.mean(psd[:, alpha_mask], axis=0)
        alpha_psd_avg = _sanitize_array(alpha_psd_avg, fill=0.0)
        iapf = _safe_scalar(float(freqs[alpha_mask][np.argmax(alpha_psd_avg)]))
    else:
        iapf = 10.0   # population fallback

    # -------------------------------------------------------------------------
    # Feature 13: Differential Entropy (DE) per band
    # Formula: DE = 0.5 · ln(2πe · Var(P_band))
    # where Var is computed over the spatial distribution of band power values.
    # Reference: Duan, Lu et al. (2013) — SEED affective EEG dataset
    #
    # Implementation note:
    #   This computes DE over the *spatial variance* of absolute band power
    #   across recording channels (not over a band-filtered time series).
    #   For a single-channel recording the variance is 0 → DE is a constant.
    #   A full per-channel, per-epoch DE would require epoching; that is
    #   beyond the current pipeline scope and is flagged for Phase 3.
    # -------------------------------------------------------------------------
    de_scores: dict[str, float] = {}
    for band in FREQ_BANDS:
        spatial_var = float(np.var(band_powers_abs[band])) + 1e-9
        de_scores[band] = _safe_scalar(0.5 * np.log(2.0 * np.pi * np.e * spatial_var))

    # -------------------------------------------------------------------------
    # Features 14-16: Hjorth Parameters (Activity, Mobility, Complexity)
    # Reference: Hjorth (1970) Electroencephalogr. Clin. Neurophysiol.
    #
    # Activity   = Var(x)            — signal power
    # Mobility   = sqrt(Var(x') / Var(x))   — mean frequency estimator
    # Complexity  = Mobility(x') / Mobility(x) — spectral bandwidth ratio
    # -------------------------------------------------------------------------
    diff1 = np.diff(data, axis=-1) if n_times >= 2 else np.zeros_like(data)
    diff2 = np.diff(diff1, axis=-1) if n_times >= 3 else np.zeros_like(data)

    var0 = np.maximum(1e-12, _sanitize_array(np.var(data,  axis=-1)) + 1e-12)
    var1 = np.maximum(1e-12, _sanitize_array(np.var(diff1, axis=-1)) + 1e-12)
    var2 = np.maximum(1e-12, _sanitize_array(np.var(diff2, axis=-1)) + 1e-12)

    activity   = _safe_scalar(float(np.mean(var0)))
    mobility   = _safe_scalar(float(np.mean(np.sqrt(var1 / var0))))
    complexity = _safe_scalar(
        float(np.mean(np.sqrt(var2 / var1) / (np.sqrt(var1 / var0) + 1e-12)))
    )

    # -------------------------------------------------------------------------
    # Feature (Composite): Biometric Uniqueness Index (BUI)
    # Formula: std(eigvals(R)) / (mean(|R|) + ε)
    # where R = Pearson correlation matrix of all channels
    # Reference: Marcel & Millán (2007) J. Mach. Learn. Res.
    # -------------------------------------------------------------------------
    if n_channels > 1:
        with np.errstate(divide='ignore', invalid='ignore'):
            corr_matrix = np.corrcoef(data)
        corr_matrix = _sanitize_array(corr_matrix, fill=0.0)
        eigenvalues = np.linalg.eigvalsh(corr_matrix)
        eigenvalues = _sanitize_array(eigenvalues, fill=0.0)
        bui = _safe_scalar(
            float(np.std(eigenvalues)) /
            (float(np.mean(np.abs(corr_matrix))) + 1e-6)
        )
    else:
        bui = 0.5   # single-channel fallback (no spatial information)

    # -------------------------------------------------------------------------
    # Assemble final feature dict
    # All values are finite floats (guaranteed by _safe_scalar / _sanitize_array)
    # -------------------------------------------------------------------------
    features = {
        # Band powers (relative, 0-100 %)
        "global_band_powers": global_band_powers,

        # FAA
        "frontal_alpha_asymmetry": round(faa, 4),

        # Ratios
        "theta_beta_ratio":   round(tbr, 3),
        "theta_alpha_ratio":  round(tar, 3),
        "engagement_index":   round(engagement_index, 3),

        # IAPF
        "iapf_hz": round(iapf, 2),

        # Differential entropy (spatial, per band)
        "differential_entropy": {k: round(v, 3) for k, v in de_scores.items()},

        # Hjorth
        "hjorth_activity":   round(activity,   6),
        "hjorth_mobility":   round(mobility,   4),
        "hjorth_complexity": round(complexity, 4),

        # Biometric uniqueness
        "biometric_uniqueness_index": round(bui, 3),

        # Recording metadata echoed for convenience
        "channel_count":  n_channels,
        "sampling_rate":  sfreq,
        "duration_sec":   round(float(n_times / sfreq), 2),
    }

    return features

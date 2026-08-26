"""
EEG file loader, preprocessor, and preview-trace generator for NeuroAudit.

Responsibilities:
  1. Load raw EEG files via MNE-Python (EDF, FIF, BDF, SET).
  2. Normalise channel names to standard 10-20 notation.
  3. Apply bandpass (0.5-45 Hz) and notch (50/60 Hz) FIR filters.
  4. Run a formal quality gate before feature extraction.
  5. Generate downsampled, amplitude-normalised preview traces for the UI.

The quality gate produces a structured *quality_report* dict that is stored
in the audit record.  If quality is insufficient the pipeline still runs but
the risk-scoring layer is informed so it can qualify its conclusions.
"""

import os
import re
import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STANDARD_CHANNELS = [
    "FP1", "FP2", "F3", "F4", "C3", "C4", "P3", "P4",
    "O1",  "O2",  "FZ", "CZ", "PZ", "T3", "T4", "T5", "T6",
]

# Quality thresholds (labelled HEURISTIC_BASELINE — no empirical calibration yet)
QC_MIN_DURATION_SEC    = 2.0    # recordings shorter than this cannot support stable PSD
QC_MIN_SFREQ_HZ        = 64.0   # minimum sampling rate for band decomposition up to 30 Hz
QC_MIN_CHANNELS        = 1      # absolute minimum; meaningful analysis needs >= 4
QC_RECOMMENDED_CH      = 4      # below this spatial features degrade significantly
QC_FLATLINE_THRESHOLD  = 1e-9   # std dev below which a channel is considered flat (V)
QC_AMPLITUDE_MAX_V     = 500e-6 # > 500 µV almost certainly clipping / artefact
QC_AMPLITUDE_MIN_V     = 1e-9   # below this channel is effectively flatlined


# ---------------------------------------------------------------------------
# Channel normalisation
# ---------------------------------------------------------------------------

def sanitize_channel_name(ch_name: str) -> str:
    """
    Normalise a raw EDF channel label to uppercase 10-20 notation.

    Examples:
      'EEG Fp1-Ref'  →  'FP1'
      'EEG F3-A1'    →  'F3'
    """
    clean = re.sub(r'^(EEG\s*|EEG-|EEG_)', '', ch_name, flags=re.IGNORECASE)
    clean = re.sub(r'(-REF|-LE|-A1|-A2|\.)$', '', clean, flags=re.IGNORECASE)
    return clean.strip().upper()


# ---------------------------------------------------------------------------
# Quality gate
# ---------------------------------------------------------------------------

def check_eeg_quality(raw, metadata: dict) -> dict:
    """
    Evaluate recording quality before feature extraction.

    Returns a *quality_report* dict containing:
      - passed          : bool — overall gate result
      - flags           : list of str — individual issues found
      - warnings        : list of str — non-critical concerns
      - sufficient_for_assessment : bool — whether risk scores should be trusted
      - details         : dict  — numeric quality metrics

    All thresholds are HEURISTIC_BASELINE values; they have not been
    validated against a calibration dataset.
    """
    flags    = []
    warnings = []

    sfreq        = metadata.get("sfreq", 0.0)
    duration_sec = metadata.get("duration_sec", 0.0)
    n_channels   = metadata.get("n_channels", 0)

    # 1. Duration
    if duration_sec < QC_MIN_DURATION_SEC:
        flags.append(
            f"Recording duration ({duration_sec:.1f}s) is below the minimum "
            f"required for stable PSD estimation ({QC_MIN_DURATION_SEC}s). "
            "Feature extraction results will be unreliable."
        )
    elif duration_sec < 5.0:
        warnings.append(
            f"Short recording ({duration_sec:.1f}s). PSD estimates may have "
            "high variance; results should be interpreted cautiously."
        )

    # 2. Sampling rate
    if sfreq < QC_MIN_SFREQ_HZ:
        flags.append(
            f"Sampling rate ({sfreq} Hz) is below the minimum required "
            f"({QC_MIN_SFREQ_HZ} Hz) to resolve the beta band (13-30 Hz)."
        )

    # 3. Channel count
    if n_channels < QC_MIN_CHANNELS:
        flags.append("No usable channels found in the recording.")
    elif n_channels < QC_RECOMMENDED_CH:
        warnings.append(
            f"Only {n_channels} channel(s) present. Spatial features "
            "(FAA, biometric uniqueness index) are less reliable with fewer "
            f"than {QC_RECOMMENDED_CH} channels."
        )

    # 4. Per-channel signal integrity
    data = raw.get_data()   # shape: (n_ch, n_times)
    n_flat      = 0
    n_clipped   = 0
    nan_count   = int(np.sum(np.isnan(data)))
    inf_count   = int(np.sum(np.isinf(data)))

    for i in range(data.shape[0]):
        ch_std  = np.std(data[i])
        ch_max  = np.max(np.abs(data[i]))
        if ch_std < QC_FLATLINE_THRESHOLD:
            n_flat += 1
        if ch_max > QC_AMPLITUDE_MAX_V:
            n_clipped += 1

    if n_flat > 0:
        pct = 100.0 * n_flat / max(n_channels, 1)
        flags.append(
            f"{n_flat} of {n_channels} channels ({pct:.0f}%) appear flat "
            "(std dev < 1 nV). These channels contribute no signal information."
        )

    if n_clipped > 0:
        warnings.append(
            f"{n_clipped} channel(s) contain amplitude values above "
            f"{QC_AMPLITUDE_MAX_V * 1e6:.0f} µV, which may indicate "
            "clipping or movement artefacts."
        )

    if nan_count > 0:
        flags.append(f"Signal matrix contains {nan_count} NaN values.")

    if inf_count > 0:
        flags.append(f"Signal matrix contains {inf_count} Inf values.")

    # 5. Determine overall gate result
    passed = len(flags) == 0
    sufficient_for_assessment = passed and n_channels >= QC_RECOMMENDED_CH

    if not sufficient_for_assessment and passed:
        # Passed hard gate but spatial features will be degraded
        warnings.append(
            "Recording passed quality checks but has fewer than the recommended "
            f"{QC_RECOMMENDED_CH} channels. Identity and emotion risk scores "
            "that rely on spatial covariance will have reduced reliability."
        )

    return {
        "passed":                   passed,
        "sufficient_for_assessment": sufficient_for_assessment,
        "flags":                    flags,
        "warnings":                 warnings,
        "details": {
            "duration_sec":   duration_sec,
            "sfreq_hz":       sfreq,
            "n_channels":     n_channels,
            "n_flat_channels": n_flat,
            "n_clipped_channels": n_clipped,
            "nan_count":      nan_count,
            "inf_count":      inf_count,
        },
        "thresholds_label": "HEURISTIC_BASELINE",
    }


# ---------------------------------------------------------------------------
# EEG loader & preprocessor
# ---------------------------------------------------------------------------

def load_eeg_file(file_path: str):
    """
    Load an EEG file, normalise channel names, apply FIR filtering,
    run the quality gate, and generate preview traces.

    Returns:
        raw              : mne.io.Raw (filtered, preloaded)
        metadata         : dict  — recording metadata
        preview_traces   : dict  — channel → list[float] for UI rendering
        quality_report   : dict  — output of check_eeg_quality()

    Raises:
        FileNotFoundError  — if the file does not exist.
        ValueError         — if MNE cannot parse the file.
    """
    import mne
    mne.set_log_level("ERROR")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"EEG file not found: {file_path}")

    # --- Load ---------------------------------------------------------------
    try:
        raw = mne.io.read_raw_edf(file_path, preload=True, verbose=False)
    except Exception as edf_err:
        try:
            raw = mne.io.read_raw(file_path, preload=True, verbose=False)
        except Exception as generic_err:
            raise ValueError(
                f"Unable to parse EEG file '{os.path.basename(file_path)}'. "
                f"EDF error: {edf_err}. Generic error: {generic_err}"
            )

    # --- Channel normalisation ----------------------------------------------
    rename_dict = {}
    for ch in raw.ch_names:
        clean = sanitize_channel_name(ch)
        if clean != ch:
            rename_dict[ch] = clean

    # Avoid collision with channels that are already correctly named
    existing = set(raw.ch_names) - set(rename_dict.keys())
    safe_rename: dict[str, str] = {}
    used: set[str] = set()
    for old, new in rename_dict.items():
        if new not in existing and new not in used:
            safe_rename[old] = new
            used.add(new)

    if safe_rename:
        raw.rename_channels(safe_rename, verbose=False)

    # --- Basic preprocessing ------------------------------------------------
    sfreq        = float(raw.info["sfreq"])
    n_times      = raw.n_times
    duration_sec = float(n_times / sfreq)

    # Bandpass 0.5–45 Hz (FIR, firwin)
    try:
        filt_len = (
            "auto"
            if duration_sec >= 10.0
            else f"{max(0.5, duration_sec - 0.2):.1f}s"
        )
        raw.filter(
            l_freq=0.5, h_freq=45.0,
            filter_length=filt_len,
            fir_design="firwin",
            verbose=False,
        )
    except Exception:
        pass   # If filtering fails (e.g. extremely short signal) continue

    # Notch 50 & 60 Hz
    try:
        if duration_sec >= 5.0:
            raw.notch_filter(
                freqs=[50.0, 60.0],
                filter_length=filt_len,
                fir_design="firwin",
                verbose=False,
            )
    except Exception:
        pass

    # --- Metadata -----------------------------------------------------------
    metadata = {
        "sfreq":          sfreq,
        "n_channels":     len(raw.ch_names),
        "duration_sec":   round(duration_sec, 2),
        "channel_names":  list(raw.ch_names),
        "file_size":      os.path.getsize(file_path),
        "highpass":       raw.info.get("highpass", 0.5),
        "lowpass":        raw.info.get("lowpass",  45.0),
    }

    # --- Quality gate -------------------------------------------------------
    quality_report = check_eeg_quality(raw, metadata)

    # --- Preview traces -----------------------------------------------------
    preview_traces = generate_preview_traces(
        raw,
        preview_duration_sec=min(8.0, duration_sec),
        n_points=200,
    )

    return raw, metadata, preview_traces, quality_report


# ---------------------------------------------------------------------------
# Preview trace generator
# ---------------------------------------------------------------------------

def generate_preview_traces(
    raw,
    preview_duration_sec: float = 8.0,
    n_points: int = 200,
) -> dict:
    """
    Extract downsampled, zero-mean, amplitude-normalised channel segments
    for frontend SVG / Recharts rendering.

    Normalisation formula per channel:
        norm = clip((x - mean(x)) / (3 * std(x)), -1.5, 1.5)

    Returns ``{}`` when the recording contains no samples.
    """
    sfreq       = raw.info["sfreq"]
    max_samples = int(preview_duration_sec * sfreq)
    data        = raw.get_data()

    n_samples = min(data.shape[1], max_samples)
    if n_samples == 0:
        return {}

    segment    = data[:, :n_samples]
    step       = max(1, n_samples // n_points)
    downsampled = segment[:, ::step][:, :n_points]

    traces: dict[str, list[float]] = {}
    for idx, ch_name in enumerate(raw.ch_names):
        sig     = downsampled[idx]
        sig_std = np.std(sig)
        if sig_std > 1e-8:
            norm = np.clip((sig - np.mean(sig)) / (3.0 * sig_std), -1.5, 1.5)
        else:
            norm = np.zeros_like(sig)
        traces[ch_name] = [round(float(v), 3) for v in norm]

    return traces

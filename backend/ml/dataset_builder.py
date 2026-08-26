"""
Dataset compilation and feature vector conversion utilities for NeuroAudit ML.

Maps MNE Raw recordings into windowed epoch segments, extracts the 19-dimensional
feature representations via pipeline.features, and constructs structured matrices.
"""

import numpy as np
import mne
from pipeline.features import extract_features_from_raw
from pipeline.eeg_loader import sanitize_channel_name

# 19 canonical continuous feature names matching ML_FEATURE_SCHEMA.md
FEATURE_NAMES: list[str] = [
    "bp_delta_rel",
    "bp_theta_rel",
    "bp_alpha_rel",
    "bp_beta_rel",
    "bp_gamma_rel",
    "faa",
    "theta_beta_ratio",
    "theta_alpha_ratio",
    "engagement_index",
    "iapf_hz",
    "de_delta",
    "de_theta",
    "de_alpha",
    "de_beta",
    "de_gamma",
    "hjorth_activity",
    "hjorth_mobility",
    "hjorth_complexity",
    "bui",
]


def feature_dict_to_vector(features: dict) -> np.ndarray:
    """
    Convert output dictionary from extract_features_from_raw() into a 1D numpy float64 array of shape (19,).

    Parameters
    ----------
    features : dict
        Extracted features dictionary from pipeline.features.extract_features_from_raw.

    Returns
    -------
    np.ndarray
        1D array of length 19 with all values guaranteed finite.
    """
    bp = features.get("global_band_powers", {})
    de = features.get("differential_entropy", {})

    vector = [
        float(bp.get("delta", 20.0)),
        float(bp.get("theta", 20.0)),
        float(bp.get("alpha", 20.0)),
        float(bp.get("beta",  20.0)),
        float(bp.get("gamma", 20.0)),
        float(features.get("frontal_alpha_asymmetry", 0.0)),
        float(features.get("theta_beta_ratio", 1.0)),
        float(features.get("theta_alpha_ratio", 1.0)),
        float(features.get("engagement_index", 0.5)),
        float(features.get("iapf_hz", 10.0)),
        float(de.get("delta", 0.0)),
        float(de.get("theta", 0.0)),
        float(de.get("alpha", 0.0)),
        float(de.get("beta",  0.0)),
        float(de.get("gamma", 0.0)),
        float(features.get("hjorth_activity", 0.0)),
        float(features.get("hjorth_mobility", 1.0)),
        float(features.get("hjorth_complexity", 1.0)),
        float(features.get("biometric_uniqueness_index", 0.5)),
    ]

    arr = np.array(vector, dtype=np.float64)
    # Sanitize any unexpected non-finite elements with fallback 0.0
    arr = np.where(np.isnan(arr) | np.isinf(arr), 0.0, arr)
    return arr


def segment_raw_into_epochs(raw: mne.io.BaseRaw, epoch_duration_sec: float = 2.0, overlap_sec: float = 0.0) -> list[mne.io.RawArray]:
    """
    Segment a continuous MNE Raw instance into fixed-duration windowed RawArray epochs.

    Parameters
    ----------
    raw : mne.io.BaseRaw
        Continuous filtered EEG recording.
    epoch_duration_sec : float
        Length of each epoch in seconds (default: 2.0s).
    overlap_sec : float
        Overlap between consecutive epochs in seconds (default: 0.0s).

    Returns
    -------
    list[mne.io.RawArray]
        List of epoch RawArray instances.
    """
    sfreq = float(raw.info["sfreq"])
    data = raw.get_data()
    n_channels, total_samples = data.shape

    step_samples = int((epoch_duration_sec - overlap_sec) * sfreq)
    window_samples = int(epoch_duration_sec * sfreq)

    if window_samples > total_samples or window_samples <= 0 or step_samples <= 0:
        # If signal is shorter than one full window, return the raw object itself if valid
        return [raw]

    epochs = []
    ch_names = list(raw.ch_names)
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types="eeg")

    for start_idx in range(0, total_samples - window_samples + 1, step_samples):
        segment_data = data[:, start_idx : start_idx + window_samples]
        epoch_raw = mne.io.RawArray(segment_data, info, verbose=False)
        epochs.append(epoch_raw)

    return epochs


def extract_features_from_epochs(epochs: list[mne.io.RawArray]) -> np.ndarray:
    """
    Extract 19-dimensional feature vectors across a list of epoch segments.

    Returns
    -------
    np.ndarray
        Matrix of shape (M, 19) where M is the number of epochs.
    """
    if not epochs:
        return np.empty((0, len(FEATURE_NAMES)), dtype=np.float64)

    rows = []
    for epoch in epochs:
        feat_dict = extract_features_from_raw(epoch)
        vec = feature_dict_to_vector(feat_dict)
        rows.append(vec)

    return np.vstack(rows)


def build_dataset_from_recordings(recordings: list[dict], epoch_duration_sec: float = 2.0) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str]]:
    """
    Compile feature matrix X, subject labels y, subject_ids, and run_ids from multiple EEG recordings.

    Parameters
    ----------
    recordings : list[dict]
        Each dict must contain:
          - 'raw': mne.io.BaseRaw instance
          - 'subject_id': str or int
          - 'run_id': str or int
    epoch_duration_sec : float
        Duration of each analysis window in seconds.

    Returns
    -------
    X : np.ndarray (M, 19)
    y : np.ndarray (M,) categorical integer labels
    subject_ids : np.ndarray (M,) string subject identifiers
    run_ids : np.ndarray (M,) string run identifiers
    feature_names : list[str]
    """
    X_list, y_list, subj_list, run_list = [], [], [], []

    # Map unique subject identifiers to integers
    unique_subjs = sorted(list(set(str(r["subject_id"]) for r in recordings)))
    subj_to_int = {s: i for i, s in enumerate(unique_subjs)}

    for item in recordings:
        raw = item["raw"]
        s_id = str(item["subject_id"])
        r_id = str(item["run_id"])
        int_label = subj_to_int[s_id]

        epochs = segment_raw_into_epochs(raw, epoch_duration_sec=epoch_duration_sec)
        feat_matrix = extract_features_from_epochs(epochs)

        n_epochs = feat_matrix.shape[0]
        if n_epochs > 0:
            X_list.append(feat_matrix)
            y_list.extend([int_label] * n_epochs)
            subj_list.extend([s_id] * n_epochs)
            run_list.extend([r_id] * n_epochs)

    if not X_list:
        return (
            np.empty((0, len(FEATURE_NAMES))),
            np.empty((0,), dtype=int),
            np.empty((0,), dtype=str),
            np.empty((0,), dtype=str),
            FEATURE_NAMES,
        )

    X = np.vstack(X_list)
    y = np.array(y_list, dtype=int)
    subject_ids = np.array(subj_list, dtype=object)
    run_ids = np.array(run_list, dtype=object)

    return X, y, subject_ids, run_ids, FEATURE_NAMES


def build_synthetic_multisubject_dataset(
    n_subjects: int = 5,
    n_runs_per_subject: int = 2,
    duration_sec: float = 10.0,
    epoch_duration_sec: float = 2.0,
    random_seed: int = 42,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str]]:
    """
    Generate a deterministic synthetic multi-subject multi-session dataset
    with subject-specific distinct frequency and spatial signatures for unit testing and offline validation.
    """
    np.random.seed(random_seed)
    recordings = []
    sfreq = 160.0
    n_channels = 8
    ch_names = ["FP1", "FP2", "C3", "C4", "P3", "P4", "O1", "O2"]
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types="eeg")
    n_samples = int(duration_sec * sfreq)
    t = np.arange(n_samples) / sfreq

    for subj_idx in range(n_subjects):
        subj_id = f"S{subj_idx+1:03d}"
        # Unique individual alpha peak frequency per subject (e.g. 8.5 to 11.5 Hz)
        subj_iapf = 8.5 + (subj_idx * 0.7)
        # Subject-specific spatial weight matrix
        spatial_mix = np.random.randn(n_channels, 3)

        for run_idx in range(n_runs_per_subject):
            run_id = f"Run_{run_idx+1}"
            # Core oscillatory sources
            src_alpha = np.sin(2 * np.pi * subj_iapf * t)
            src_theta = 0.5 * np.sin(2 * np.pi * 6.0 * t + run_idx)
            src_beta = 0.3 * np.sin(2 * np.pi * 22.0 * t)
            sources = np.vstack([src_alpha, src_theta, src_beta])  # (3, n_samples)

            # Spatial projection + pink/white noise
            noise = np.random.randn(n_channels, n_samples) * 0.2
            eeg_data = (spatial_mix @ sources + noise) * 1e-5

            raw_obj = mne.io.RawArray(eeg_data, info, verbose=False)
            recordings.append({
                "raw": raw_obj,
                "subject_id": subj_id,
                "run_id": f"{subj_id}_{run_id}",
            })

    return build_dataset_from_recordings(recordings, epoch_duration_sec=epoch_duration_sec)

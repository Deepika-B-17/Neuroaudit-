import os
import numpy as np
import mne
import pyedflib

SAMPLES_DIR = os.path.dirname(__file__)

def generate_synthetic_eeg(
    duration_sec: float = 30.0,
    sfreq: float = 256.0,
    n_channels: int = 8,
    profile: str = "resting"
) -> tuple[np.ndarray, list[str], float]:
    """
    Generate realistic multi-channel EEG signal with authentic frequency characteristics.
    Returns (data, ch_names, sfreq).
    """
    ch_names = ["FP1", "FP2", "F3", "F4", "C3", "C4", "P3", "P4"][:n_channels]
    n_samples = int(duration_sec * sfreq)
    times = np.arange(n_samples) / sfreq

    data = np.zeros((n_channels, n_samples))

    if profile == "resting":
        seed = 42
        alpha_amp = 25e-6   # Dominant posterior alpha
        theta_amp = 10e-6
        beta_amp = 8e-6
        gamma_amp = 3e-6
        iapf = 10.2
        faa_bias = -0.15    # Moderate asymmetry
    elif profile == "stress_high":
        seed = 101
        alpha_amp = 8e-6    # Suppressed alpha
        theta_amp = 12e-6
        beta_amp = 28e-6    # High beta surge
        gamma_amp = 14e-6   # High gamma
        iapf = 11.4
        faa_bias = -0.45    # Strong right-frontal withdrawal / stress bias
    else: # workload
        seed = 202
        alpha_amp = 10e-6
        theta_amp = 32e-6   # Frontal theta surge
        beta_amp = 18e-6    # Task engagement beta
        gamma_amp = 6e-6
        iapf = 9.6
        faa_bias = 0.25     # Left frontal approach / active engagement

    rng = np.random.RandomState(seed)

    for i, ch in enumerate(ch_names):
        # 1/f Pink Noise Baseline
        white = rng.randn(n_samples)
        pink = np.cumsum(white) * 0.05
        pink = pink - np.mean(pink)
        pink = (pink / (np.std(pink) + 1e-9)) * 10e-6

        # Channel-specific phase offsets
        phase_offset = rng.uniform(0, 2 * np.pi)

        # Alpha rhythm (8-13 Hz) - stronger in posterior P3, P4
        ch_alpha_weight = 1.6 if ch in ["P3", "P4", "O1", "O2"] else 0.8
        if ch == "FP2":
            ch_alpha_weight *= (1.0 + faa_bias)
        elif ch == "FP1":
            ch_alpha_weight *= (1.0 - faa_bias)
        alpha_wave = ch_alpha_weight * alpha_amp * np.sin(2 * np.pi * iapf * times + phase_offset)

        # Theta rhythm (4-8 Hz) - stronger in frontal F3, F4, FP1, FP2
        ch_theta_weight = 1.5 if "F" in ch else 0.8
        theta_wave = ch_theta_weight * theta_amp * np.sin(2 * np.pi * 6.0 * times + phase_offset * 1.5)

        # Beta rhythm (13-30 Hz) - stronger in central/frontal
        ch_beta_weight = 1.4 if ("C" in ch or "F" in ch) else 0.9
        beta_wave = ch_beta_weight * beta_amp * np.sin(2 * np.pi * 22.0 * times + phase_offset * 2.0)

        # Gamma rhythm (30-45 Hz)
        gamma_wave = gamma_amp * np.sin(2 * np.pi * 38.0 * times + phase_offset * 2.5)

        # Combine (in Volts)
        channel_signal = pink + alpha_wave + theta_wave + beta_wave + gamma_wave
        data[i] = channel_signal

    return data, ch_names, sfreq

def write_edf_file(file_path: str, data: np.ndarray, ch_names: list[str], sfreq: float):
    """Write EEG data array to a valid .edf file using pyedflib."""
    n_channels = len(ch_names)
    channel_info = []
    
    # Convert from Volts to microvolts for standard EDF recording
    data_uv = data * 1e6
    
    for ch in ch_names:
        ch_dict = {
            'label': ch,
            'dimension': 'uV',
            'sample_frequency': sfreq,
            'physical_max': 500.0,
            'physical_min': -500.0,
            'digital_max': 32767,
            'digital_min': -32768,
            'transducer': 'AgAgCl',
            'prefilter': 'HP:0.1Hz_LP:70Hz'
        }
        channel_info.append(ch_dict)

    with pyedflib.EdfWriter(file_path, n_channels, file_type=pyedflib.FILETYPE_EDFPLUS) as f:
        f.setSignalHeaders(channel_info)
        f.setPatientCode("SUBJ_NEURO_001")
        f.setPatientName("Subject_001")
        f.setRecordingAdditional("NeuroAudit_Privacy_Benchmark")
        f.writeSamples(data_uv)

def ensure_sample_files():
    """Create benchmark EDF sample files if they do not exist."""
    os.makedirs(SAMPLES_DIR, exist_ok=True)

    sample_configs = [
        {
            "filename": "session_a_rest_eeg.edf",
            "name": "Clinical cohort session A",
            "profile": "resting",
            "duration": 30.0
        },
        {
            "filename": "pilot_rest_02.edf",
            "name": "Pilot study — rest-state",
            "profile": "stress_high",
            "duration": 25.0
        },
        {
            "filename": "dual_task_block3.edf",
            "name": "Workload dual-task trial",
            "profile": "workload",
            "duration": 35.0
        }
    ]

    created = []
    for cfg in sample_configs:
        file_path = os.path.join(SAMPLES_DIR, cfg["filename"])
        if not os.path.exists(file_path):
            data, ch_names, sfreq = generate_synthetic_eeg(duration_sec=cfg["duration"], profile=cfg["profile"])
            write_edf_file(file_path, data, ch_names, sfreq)
            created.append(cfg["filename"])

    return created

if __name__ == "__main__":
    files = ensure_sample_files()
    print(f"Generated sample EDF files: {files}")

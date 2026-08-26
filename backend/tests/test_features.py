"""
Unit tests for EEG feature extraction pipeline (Phase 2).

Verifies numerical stability, reproducibility, edge case resilience,
and key structure for all 16 feature extraction algorithms.
"""

import os
import sys
import unittest
import numpy as np
import mne

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from pipeline.features import extract_features_from_raw, FREQ_BANDS
from samples.generate_samples import generate_synthetic_eeg


def _create_raw(data: np.ndarray, ch_names: list[str], sfreq: float) -> mne.io.RawArray:
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types="eeg")
    return mne.io.RawArray(data, info, verbose=False)


def _assert_all_finite(test_case: unittest.TestCase, obj, path=""):
    """Recursively assert that all numbers in a nested dict/list are finite (no NaN/Inf)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            _assert_all_finite(test_case, v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            _assert_all_finite(test_case, v, f"{path}[{i}]")
    elif isinstance(obj, (int, float, np.floating, np.integer)):
        test_case.assertTrue(
            np.isfinite(obj),
            f"Non-finite value encountered at {path}: {obj}"
        )


class TestEEGFeatures(unittest.TestCase):
    """Test suite covering stability, correctness, edge cases, and reproducibility."""

    EXPECTED_KEYS = {
        "global_band_powers",
        "frontal_alpha_asymmetry",
        "theta_beta_ratio",
        "theta_alpha_ratio",
        "engagement_index",
        "iapf_hz",
        "differential_entropy",
        "hjorth_activity",
        "hjorth_mobility",
        "hjorth_complexity",
        "biometric_uniqueness_index",
        "channel_count",
        "sampling_rate",
        "duration_sec",
    }

    def test_normal_synthetic_eeg(self):
        """1. Test feature extraction on standard multi-channel synthetic EEG."""
        data, ch_names, sfreq = generate_synthetic_eeg(duration_sec=5.0, n_channels=8, profile="resting")
        raw = _create_raw(data, ch_names, sfreq)
        features = extract_features_from_raw(raw)

        # Check all expected top-level keys
        for key in self.EXPECTED_KEYS:
            self.assertIn(key, features)

        # Check sub-dictionaries
        for band in FREQ_BANDS:
            self.assertIn(band, features["global_band_powers"])
            self.assertIn(band, features["differential_entropy"])

        # Check finiteness
        _assert_all_finite(self, features)

        # Check logical bounds
        self.assertEqual(features["channel_count"], 8)
        self.assertEqual(features["sampling_rate"], sfreq)
        self.assertAlmostEqual(features["duration_sec"], 5.0, places=1)
        self.assertGreaterEqual(features["iapf_hz"], 7.0)
        self.assertLessEqual(features["iapf_hz"], 13.0)

    def test_short_valid_eeg(self):
        """2. Test very short but valid EEG (0.3s)."""
        sfreq = 250.0
        n_times = int(0.3 * sfreq)
        np.random.seed(42)
        data = np.random.randn(8, n_times) * 1e-5
        ch_names = ["FP1", "FP2", "C3", "C4", "P3", "P4", "O1", "O2"]
        raw = _create_raw(data, ch_names, sfreq)
        features = extract_features_from_raw(raw)

        self.assertEqual(set(self.EXPECTED_KEYS), set(features.keys()))
        _assert_all_finite(self, features)
        self.assertAlmostEqual(features["duration_sec"], 0.3, places=2)

    def test_constant_near_constant_signal(self):
        """3. Test constant (flat line) and near-constant signals."""
        sfreq = 250.0
        n_times = 500
        # Exactly constant signal (zeros)
        data_zeros = np.zeros((8, n_times))
        ch_names = ["FP1", "FP2", "F3", "F4", "C3", "C4", "P3", "P4"]
        raw_zeros = _create_raw(data_zeros, ch_names, sfreq)
        features_zeros = extract_features_from_raw(raw_zeros)
        _assert_all_finite(self, features_zeros)

        # Non-zero constant signal (DC offset)
        data_dc = np.ones((8, n_times)) * 42.0
        raw_dc = _create_raw(data_dc, ch_names, sfreq)
        features_dc = extract_features_from_raw(raw_dc)
        _assert_all_finite(self, features_dc)

    def test_zero_power_edge_cases(self):
        """4. Test zero-power edge cases where specific bands have zero power."""
        sfreq = 250.0
        n_times = 1000
        t = np.arange(n_times) / sfreq
        # Pure 10 Hz sine wave (only alpha band active, others ~zero)
        pure_alpha = np.sin(2 * np.pi * 10.0 * t)
        data = np.tile(pure_alpha, (8, 1)) * 1e-5
        ch_names = ["FP1", "FP2", "F3", "F4", "C3", "C4", "P3", "P4"]
        raw = _create_raw(data, ch_names, sfreq)
        features = extract_features_from_raw(raw)

        _assert_all_finite(self, features)
        # Alpha should be dominant
        self.assertGreater(features["global_band_powers"]["alpha"], 50.0)
        self.assertAlmostEqual(features["iapf_hz"], 10.0, delta=0.5)

    def test_missing_and_nonstandard_channels(self):
        """5. Test missing standard 10-20 channels (arbitrary channel names)."""
        sfreq = 200.0
        data = np.random.randn(4, 600) * 1e-5
        ch_names = ["CHANNEL_A", "CHANNEL_B", "CHANNEL_C", "CHANNEL_D"]
        raw = _create_raw(data, ch_names, sfreq)
        features = extract_features_from_raw(raw)

        _assert_all_finite(self, features)
        # FAA should fallback safely to 0.0 when no frontal pairs are identifiable
        self.assertEqual(features["frontal_alpha_asymmetry"], 0.0)
        self.assertEqual(features["channel_count"], 4)

    def test_single_channel_eeg(self):
        """Test single-channel recording fallback handling."""
        sfreq = 250.0
        data = np.random.randn(1, 500) * 1e-5
        raw = _create_raw(data, ["Cz"], sfreq)
        features = extract_features_from_raw(raw)

        _assert_all_finite(self, features)
        self.assertEqual(features["channel_count"], 1)
        # BUI single-channel fallback is 0.5
        self.assertEqual(features["biometric_uniqueness_index"], 0.5)
        # FAA single-channel fallback is 0.0
        self.assertEqual(features["frontal_alpha_asymmetry"], 0.0)

    def test_multiple_sampling_rates(self):
        """6. Test feature extraction across different sampling rates."""
        for sfreq in [100.0, 128.0, 250.0, 500.0, 1000.0]:
            data = np.random.randn(4, int(sfreq * 2.0)) * 1e-5
            ch_names = ["FP1", "FP2", "O1", "O2"]
            raw = _create_raw(data, ch_names, sfreq)
            features = extract_features_from_raw(raw)
            _assert_all_finite(self, features)
            self.assertEqual(features["sampling_rate"], sfreq)

    def test_reproducibility(self):
        """7. Test reproducibility: running the same deterministic EEG produces identical results."""
        np.random.seed(12345)
        sfreq = 250.0
        t = np.arange(1250) / sfreq
        # Deterministic multi-component signal
        sig1 = 10 * np.sin(2 * np.pi * 10 * t) + 5 * np.sin(2 * np.pi * 20 * t)
        sig2 = 8 * np.sin(2 * np.pi * 6 * t) + 3 * np.cos(2 * np.pi * 15 * t)
        data = np.vstack([sig1, sig2, sig1 * 0.9, sig2 * 1.1]) * 1e-6
        ch_names = ["FP1", "FP2", "F3", "F4"]

        raw1 = _create_raw(data.copy(), ch_names, sfreq)
        raw2 = _create_raw(data.copy(), ch_names, sfreq)

        features1 = extract_features_from_raw(raw1)
        features2 = extract_features_from_raw(raw2)

        # Exact dictionary equality
        self.assertEqual(features1, features2)

    def test_invalid_inputs_rejected(self):
        """8. Test that invalid sampling rate or empty array raises ValueError."""
        class MockRaw:
            def __init__(self, data, sfreq, ch_names):
                self._data = data
                self.info = {"sfreq": sfreq}
                self.ch_names = ch_names
            def get_data(self):
                return self._data

        # sfreq <= 0
        raw_bad_sfreq = MockRaw(np.ones((1, 100)), 0.0, ["C3"])
        with self.assertRaises(ValueError):
            extract_features_from_raw(raw_bad_sfreq)

        # Empty data array
        raw_empty = MockRaw(np.zeros((0, 0)), 250.0, [])
        with self.assertRaises(ValueError):
            extract_features_from_raw(raw_empty)


if __name__ == "__main__":
    unittest.main()

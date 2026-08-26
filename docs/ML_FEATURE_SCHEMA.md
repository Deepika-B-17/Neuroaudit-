# NeuroAudit — Machine Learning Feature Schema & Vectorization Plan

**Document Version:** 1.0.0 (Phase 4)  
**Date:** August 2026  
**Status:** Feature Schema Specification  
**Source Module:** [`backend/pipeline/features.py`](file:///c:/Users/DINESH/Downloads/neuro/backend/pipeline/features.py)  

---

## 1. Feature Vector Architecture

Each temporal epoch (e.g., 2.0-second EEG window) is transformed into a fixed-length $D = 19$-dimensional continuous numerical feature vector:

$$\mathbf{x} \in \mathbb{R}^{19}$$

All 19 features are derived exclusively from the existing, validated Phase 2 feature extraction pipeline without introducing any unverified new algorithms.

---

## 2. Feature Schema Catalog

| Index | Feature Key / Column Name | Source in `features.py` | Data Type | Theoretical Range | Typical Empirical Range | Description |
|:---:|---|---|:---:|:---:|:---:|---|
| `0` | `bp_delta_rel` | `global_band_powers["delta"]` | `float64` | $[0.0, 100.0]$ | $[5.0, 60.0]$ | Relative Delta Power (0.5–4.0 Hz) |
| `1` | `bp_theta_rel` | `global_band_powers["theta"]` | `float64` | $[0.0, 100.0]$ | $[5.0, 45.0]$ | Relative Theta Power (4.0–8.0 Hz) |
| `2` | `bp_alpha_rel` | `global_band_powers["alpha"]` | `float64` | $[0.0, 100.0]$ | $[5.0, 70.0]$ | Relative Alpha Power (8.0–13.0 Hz) |
| `3` | `bp_beta_rel` | `global_band_powers["beta"]` | `float64` | $[0.0, 100.0]$ | $[5.0, 40.0]$ | Relative Beta Power (13.0–30.0 Hz) |
| `4` | `bp_gamma_rel` | `global_band_powers["gamma"]` | `float64` | $[0.0, 100.0]$ | $[0.5, 25.0]$ | Relative Gamma Power (30.0–45.0 Hz) |
| `5` | `faa` | `frontal_alpha_asymmetry` | `float64` | $[-\infty, +\infty]$ | $[-2.5, +2.5]$ | Frontal Alpha Asymmetry ($\ln(\alpha_R) - \ln(\alpha_L)$) |
| `6` | `theta_beta_ratio` | `theta_beta_ratio` | `float64` | $[0.0, +\infty]$ | $[0.2, 5.0]$ | Ratio of Theta to Beta Power |
| `7` | `theta_alpha_ratio` | `theta_alpha_ratio` | `float64` | $[0.0, +\infty]$ | $[0.1, 4.0]$ | Ratio of Theta to Alpha Power |
| `8` | `engagement_index` | `engagement_index` | `float64` | $[0.0, +\infty]$ | $[0.05, 1.5]$ | Pope Engagement Index ($\beta / (\theta + \alpha)$) |
| `9` | `iapf_hz` | `iapf_hz` | `float64` | $[7.5, 12.5]$ | $[8.0, 12.0]$ | Individual Alpha Peak Frequency (Hz) |
| `10` | `de_delta` | `differential_entropy["delta"]` | `float64` | $[-\infty, +\infty]$ | $[-5.0, +8.0]$ | Spatial Differential Entropy in Delta Band |
| `11` | `de_theta` | `differential_entropy["theta"]` | `float64` | $[-\infty, +\infty]$ | $[-5.0, +8.0]$ | Spatial Differential Entropy in Theta Band |
| `12` | `de_alpha` | `differential_entropy["alpha"]` | `float64` | $[-\infty, +\infty]$ | $[-5.0, +8.0]$ | Spatial Differential Entropy in Alpha Band |
| `13` | `de_beta` | `differential_entropy["beta"]` | `float64` | $[-\infty, +\infty]$ | $[-5.0, +8.0]$ | Spatial Differential Entropy in Beta Band |
| `14` | `de_gamma` | `differential_entropy["gamma"]` | `float64` | $[-\infty, +\infty]$ | $[-5.0, +8.0]$ | Spatial Differential Entropy in Gamma Band |
| `15` | `hjorth_activity` | `hjorth_activity` | `float64` | $[0.0, +\infty]$ | $[10^{-8}, 10^{-2}]$ | Mean Signal Power / Variance |
| `16` | `hjorth_mobility` | `hjorth_mobility` | `float64` | $[0.0, +\infty]$ | $[0.01, 1.0]$ | Normalized Mean Frequency Estimator |
| `17` | `hjorth_complexity` | `hjorth_complexity` | `float64` | $[0.0, +\infty]$ | $[0.8, 3.5]$ | Spectral Bandwidth Ratio |
| `18` | `bui` | `biometric_uniqueness_index` | `float64` | $[0.0, +\infty]$ | $[0.2, 3.0]$ | Spatial Correlation Eigenvalue Spread |

---

## 3. Preprocessing & Normalization Protocol

### 3.1 Missing Value Policy
Thanks to the Phase 2 numerical hardening in `features.py`, feature extraction produces 100% finite outputs (`_safe_scalar`, `_sanitize_array`). In the event of any unexpected `NaN` or missing attribute during dataset aggregation:
1. Impute using median of the corresponding feature column computed **strictly on the training fold**.
2. Reject the individual epoch if more than 3 attributes require imputation.

### 3.2 Feature Scaling (Zero Data Leakage Rule)
* **Transformation:** Z-score standardization:
  $$x_{\text{norm}} = \frac{x - \mu_{\text{train}}}{\sigma_{\text{train}} + \epsilon}$$
* **Leakage Prevention Rule:**
  `StandardScaler` parameters $(\mu_{\text{train}}, \sigma_{\text{train}})$ MUST be fitted strictly on the training partition within each cross-validation fold and then applied to transform test fold epochs.
  Computing scaling parameters on the full dataset before splitting is strictly prohibited.

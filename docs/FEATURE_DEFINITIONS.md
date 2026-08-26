# NeuroAudit — EEG Feature Definitions & Algorithmic Specification

**Document Version:** 1.0.0 (Phase 2)  
**Date:** August 2026  
**Status:** Validated & Documented  
**Implementation File:** [`backend/pipeline/features.py`](file:///c:/Users/DINESH/Downloads/neuro/backend/pipeline/features.py)  
**Test Suite:** [`backend/tests/test_features.py`](file:///c:/Users/DINESH/Downloads/neuro/backend/tests/test_features.py)  

---

## 1. Overview

NeuroAudit computes 16 feature extraction algorithms producing 20 distinct numerical values from preprocessed multichannel electroencephalographic (EEG) recordings. 

All features are extracted deterministically from continuous MNE `Raw` data structures that have been bandpass-filtered (0.5–45.0 Hz) and notch-filtered (50/60 Hz powerline attenuation).

> [!NOTE]
> **Research Language & Scientific Scope:**
> Features in this catalog represent signal-processing representations historically associated with physiological, cognitive, and affective states in neuroscientific literature. In this phase of NeuroAudit, all risk assessments driven by these features are **heuristic baseline indicators**. They do not constitute diagnostic classifications, definitive emotion determinations, or identity authentication proofs.

---

## 2. Feature Master Table

| Feature Name | Implementation Location | Input Signal / Channels | Frequency Band(s) | Mathematical Formula / Method | Output Key & Structure | Units / Range | Used By Risk Dimension | Scientific Interpretation | Implementation Limitations |
|---|---|---|---|---|---|---|---|---|---|
| **Welch Power Spectral Density (PSD)** | `features.py:93` | All EEG channels, $(C, T)$ continuous array | 0.5–45.0 Hz | Welch's modified periodogram: average of windowed FFTs with 2s segments and 50% overlap | Intermediate `(freqs, psd)` | $\mu\text{V}^2/\text{Hz}$ or $\text{V}^2/\text{Hz}$ | Foundational to all band metrics | Frequency-domain power distribution of neural oscillations. | Stationary assumption over 2s window length. |
| **Absolute Band Powers** | `features.py:97-105` | All EEG channels | $\delta$ (0.5–4 Hz)<br>$\theta$ (4–8 Hz)<br>$\alpha$ (8–13 Hz)<br>$\beta$ (13–30 Hz)<br>$\gamma$ (30–45 Hz) | Numerical trapezoidal integration: $\int_{f_{min}}^{f_{max}} \text{PSD}(f) df$ per channel | `band_powers_abs` (internal dict of 5 float arrays) | $\mu\text{V}^2$ | All Dimensions | Total oscillatory power in canonical neurological frequency bands. | Sensitive to absolute amplitude variations and scalp impedance differences. |
| **Relative Band Powers** | `features.py:108-117` | All EEG channels | $\delta, \theta, \alpha, \beta, \gamma$ | $\frac{P_{\text{band}}}{\sum_{k} P_k} \times 100$, averaged across channels | `global_band_powers` (dict with 5 keys: `delta`, `theta`, `alpha`, `beta`, `gamma`) | $\%$ (0.0 to 100.0) | Emotion ($\beta, \gamma$), Stress ($\beta, \alpha$), Workload ($\theta$) | Proportional spectral composition normalized against total broadband power. | Ratios are mutually dependent (sum = 100%); elevation in one band depresses relative share of others. |
| **Frontal Alpha Asymmetry (FAA)** | `features.py:127-166` | Frontal pairs: FP2/FP1 or F4/F3 (with AF4/AF3, FC2/FC1 fallbacks) | $\alpha$ (8.0–13.0 Hz) | $\text{FAA} = \ln(\alpha_{\text{right}}) - \ln(\alpha_{\text{left}})$ | `frontal_alpha_asymmetry` (float) | Dimensionless ($\approx -4.0$ to $+4.0$) | Emotion Privacy Risk | Candidate metric associated with affective valence under the Davidson approach-withdrawal model (Davidson, 1998). | Requires accurate frontal electrode placement. When no valid frontal asymmetric pairs exist, falls back to 0.0. |
| **Theta/Beta Ratio (TBR)** | `features.py:170-182` | Channel-averaged absolute powers | $\theta$ (4–8 Hz), $\beta$ (13–30 Hz) | $\text{TBR} = \frac{\bar{P}_{\theta}}{\bar{P}_{\beta} + \epsilon}$ | `theta_beta_ratio` (float) | Dimensionless ($\ge 0.0$) | Mental Workload Privacy Risk | Associated with cognitive control, attentional allocation, and task engagement (Barry et al., 2003). | Global channel average rather than frontal-midline specific channel calculation. |
| **Theta/Alpha Ratio (TAR)** | `features.py:170-182` | Channel-averaged absolute powers | $\theta$ (4–8 Hz), $\alpha$ (8–13 Hz) | $\text{TAR} = \frac{\bar{P}_{\theta}}{\bar{P}_{\alpha} + \epsilon}$ | `theta_alpha_ratio` (float) | Dimensionless ($\ge 0.0$) | Auxiliary Cognitive State Indicator | Associated with drowsiness, relaxed awareness, and transition states. | Sensitive to baseline individual alpha peak variations. |
| **Engagement Index (EI)** | `features.py:185-192` | Channel-averaged absolute powers | $\beta$ (13–30 Hz), $\theta$ (4–8 Hz), $\alpha$ (8–13 Hz) | $\text{EI} = \frac{\bar{P}_{\beta}}{\bar{P}_{\theta} + \bar{P}_{\alpha} + \epsilon}$ (Pope et al., 1995) | `engagement_index` (float) | Dimensionless ($\ge 0.0$) | Mental Workload Privacy Risk | Task engagement index designed for adaptive automation and cognitive state monitoring. | High-frequency electromyographic (EMG) artifact in beta band can artificially elevate EI. |
| **Individual Alpha Peak Frequency (IAPF)** | `features.py:194-204` | Channel-averaged PSD | Search range: 7.5–12.5 Hz | $\text{IAPF} = \arg\max_{f \in [7.5, 12.5]} \overline{\text{PSD}}(f)$ | `iapf_hz` (float) | $\text{Hz}$ (7.5 to 12.5) | Identity Privacy Risk | Stable neurophysiological trait associated with cognitive capability and subject distinctiveness (Klimesch, 1999). | Frequency resolution bounded by Welch window length ($0.5\text{ Hz}$ for $N=2\text{s}$). |
| **Differential Entropy (DE)** | `features.py:207-223` | Per-band channel power vector | $\delta, \theta, \alpha, \beta, \gamma$ | $\text{DE}_{\text{band}} = \frac{1}{2}\ln(2\pi e \cdot \text{Var}_{ch}(P_{\text{band}, ch}) + \epsilon)$ | `differential_entropy` (dict with 5 band keys) | Nats ($-\infty$ to $+\infty$, typically $-10.0$ to $+10.0$) | Candidate Complexity Feature (available downstream) | Captures spatial dispersion / channel-to-channel variance of band power distribution across the scalp. | **Spatial variance implementation**, not traditional temporal time-series segment DE. For single-channel data, variance is 0. |
| **Hjorth Activity** | `features.py:225-244` | Multichannel continuous data $(C, T)$ | Broadband (0.5–45 Hz) | $\text{Activity} = \overline{\text{Var}(x(t))}$ across channels | `hjorth_activity` (float) | $\mu\text{V}^2$ or $\text{V}^2$ ($\ge 0.0$) | Signal Power / Amplitude Indicator | Proportional to mean signal energy and overall amplitude variance (Hjorth, 1970). | Sensitive to baseline sensor impedance and overall signal scaling. |
| **Hjorth Mobility** | `features.py:225-244` | Multichannel continuous data $(C, T)$ | Broadband (0.5–45 Hz) | $\text{Mobility} = \overline{\sqrt{\frac{\text{Var}(x'(t))}{\text{Var}(x(t))}}}$ | `hjorth_mobility` (float) | Dimensionless ($\ge 0.0$) | Mean Frequency Estimator | Normalized estimate of mean frequency / derivative rate of change. | High-frequency noise can disproportionately elevate the derivative variance $\text{Var}(x'(t))$. |
| **Hjorth Complexity** | `features.py:225-244` | Multichannel continuous data $(C, T)$ | Broadband (0.5–45 Hz) | $\text{Complexity} = \frac{\text{Mobility}(x'(t))}{\text{Mobility}(x(t))}$ | `hjorth_complexity` (float) | Dimensionless ($\ge 0.0$) | Stress Privacy Risk | Measures spectral bandwidth and signal irregularities relative to a pure sine wave ($\text{Complexity}=1.0$). | Sensitive to high-order derivative noise in uncleaned or low-sampling-rate signals. |
| **Biometric Uniqueness Index (BUI)** | `features.py:246-262` | Multichannel continuous data $(C, T)$ | Broadband (0.5–45 Hz) | $\text{BUI} = \frac{\text{std}(\text{eigvals}(R))}{\text{mean}(\|R\|) + \epsilon}$ where $R = \text{Corr}(X)$ | `biometric_uniqueness_index` (float) | Dimensionless ($\ge 0.0$) | Identity Privacy Risk | Candidate biometric distinctiveness indicator measuring non-uniformity of spatial inter-channel correlation structure. | Empirical heuristic indicator. Does NOT prove individual identity or verify authentication. Single-channel fallback = 0.5. |

---

## 3. In-Depth Analysis of Key Metric Implementations

### 3.1 Differential Entropy (DE) — Spatial vs. Temporal Implementation Scope

In affective computing literature (e.g., SEED dataset benchmarks; Duan et al., 2013; Zheng & Lu, 2015), Differential Entropy is computed on bandpass-filtered **temporal time-series epochs** under the assumption of asymptotic Gaussian distribution:
$$h(X) = \frac{1}{2} \ln(2\pi e \sigma^2)$$
where $\sigma^2$ is the temporal variance of the bandpass-filtered signal for a specific channel epoch.

**Current Implementation Scope in NeuroAudit:**
In `backend/pipeline/features.py`, DE is currently implemented over the **spatial variance** of absolute band power across electrodes:
$$\text{spatial\_var} = \text{Var}_{ch \in C}\left(P_{\text{band}, ch}\right)$$
$$\text{DE}_{\text{band}} = \frac{1}{2} \ln\left(2\pi e \cdot (\text{spatial\_var} + 10^{-9})\right)$$

- **Purpose:** Measures cross-channel topographical heterogeneity in spectral power.
- **Scientific Caveat:** This is a spatial dispersion metric, NOT standard temporal segment DE. Single-channel recordings will yield a constant value ($\frac{1}{2}\ln(2\pi e \cdot 10^{-9}) \approx -9.67$).

---

### 3.2 Biometric Uniqueness Index (BUI) — Candidate Distinctiveness Indicator

- **Algorithmic Basis:** Spatial cross-channel Pearson correlation matrix $R \in \mathbb{R}^{C \times C}$, where $R_{ij} = \text{Corr}(X_i, X_j)$. The eigenvalues $\lambda_1, \dots, \lambda_C = \text{eigvalsh}(R)$ represent the principal spatial dispersion modes.
- **Formula:**
  $$\text{BUI} = \frac{\text{std}(\lambda_1, \dots, \lambda_C)}{\text{mean}(|R|) + 10^{-6}}$$
- **Scientific Interpretation:** A signal with highly differentiated, non-uniform spatial inter-channel coupling exhibits higher eigenvalue dispersion, reflecting idiosyncratic spatial potential distribution across the scalp.
- **Crucial Caution:** BUI is a candidate biometric distinctiveness feature and heuristic indicator. It does NOT identify a subject, prove subject identity, or guarantee biometric re-identification performance without an empirical trained classifier.

---

### 3.3 Frontal Alpha Asymmetry (FAA) & Electrode Pair Resolution

- **Theoretical Basis:** Frontal EEG alpha power is inversely related to cortical activity. Greater left-frontal activity (lower left alpha) is associated with approach motivation and positive valence; greater right-frontal activity (lower right alpha) is associated with withdrawal motivation (Davidson, 1998, 2004).
- **Asymmetry Formula:** $\text{FAA} = \ln(\alpha_{\text{right}}) - \ln(\alpha_{\text{left}})$.
- **Electrode Resolution Priority:**
  1. Primary Pair: `FP2` (right) vs. `FP1` (left)
  2. Secondary Pair: `F4` (right) vs. `F3` (left)
  3. Frontal Candidates: `AF4`/`AF3`, `FC2`/`FC1`, `F8`/`F7`
  4. Symmetric Fallback: If no distinct asymmetric pair is found, returns $0.0$.

---

## 4. Feature Quality & Validation Summary Matrix

This matrix distinguishes between signal-processing implementation status, numerical stability verification, test coverage, documentation, and empirical project-level scientific validation.

| Feature Identifier | Implemented | Numerically Stable | Test Suite Verified | Documented | Empirical Research Validation in Current Project |
|---|:---:|:---:|:---:|:---:|:---:|
| `welch_psd` | **YES** | **YES** | **YES** | **YES** | **NO** (Heuristic intermediate) |
| `band_powers_abs` | **YES** | **YES** | **YES** | **YES** | **NO** (Heuristic baseline) |
| `global_band_powers` | **YES** | **YES** | **YES** | **YES** | **NO** (Heuristic baseline) |
| `frontal_alpha_asymmetry` | **YES** | **YES** | **YES** | **YES** | **NO** (Literature-inspired heuristic) |
| `theta_beta_ratio` | **YES** | **YES** | **YES** | **YES** | **NO** (Literature-inspired heuristic) |
| `theta_alpha_ratio` | **YES** | **YES** | **YES** | **YES** | **NO** (Literature-inspired heuristic) |
| `engagement_index` | **YES** | **YES** | **YES** | **YES** | **NO** (Literature-inspired heuristic) |
| `iapf_hz` | **YES** | **YES** | **YES** | **YES** | **NO** (Literature-inspired heuristic) |
| `differential_entropy` (spatial) | **YES** | **YES** | **YES** | **YES** | **NO** (Spatial heuristic metric) |
| `hjorth_activity` | **YES** | **YES** | **YES** | **YES** | **NO** (Classical signal descriptor) |
| `hjorth_mobility` | **YES** | **YES** | **YES** | **YES** | **NO** (Classical signal descriptor) |
| `hjorth_complexity` | **YES** | **YES** | **YES** | **YES** | **NO** (Classical signal descriptor) |
| `biometric_uniqueness_index` | **YES** | **YES** | **YES** | **YES** | **NO** (Heuristic candidate indicator) |

> [!IMPORTANT]
> **Clarification on Research Validation:**
> In this table, **"Empirical Research Validation in Current Project"** requires formal validation against labelled empirical datasets with cross-validation in this specific codebase. While these algorithms are established in peer-reviewed neuroscience literature, they operate strictly within the **Heuristic Baseline** in NeuroAudit until ML classifiers and calibration models are incorporated.

---

## 5. Numerical Stability Guarantees

The feature extraction engine guarantees that `extract_features_from_raw()` satisfies the following numerical stability properties:

1. **Zero Division Prevention:** All ratio denominators incorporate safe strictly positive epsilons ($+ 10^{-12}$ or $+ 10^{-6}$).
2. **Logarithm Boundary Guards:** All logarithmic inputs are clamped to strictly positive values ($\max(10^{-9}, x)$).
3. **Finite Output Assurance:** Every float output is filtered through `_safe_scalar()` and `_sanitize_array()`, ensuring no `NaN`, `+Inf`, or `-Inf` escapes the engine.
4. **Resilience to Degenerate Signals:** Constant (DC flatline), zero-power, very short ($< 0.5\text{s}$), and single-channel recordings execute cleanly without runtime crashes or uncaught exceptions.
5. **Exact Reproducibility:** Extraction is 100% deterministic with zero stochastic components or unseeded randomness.

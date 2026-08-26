# NeuroAudit — Research Dataset Selection & Evaluation Specification

**Document Version:** 1.0.0 (Phase 4)  
**Date:** August 2026  
**Status:** Dataset Selection & Preparation Specification  
**Primary Research Focus:** Subject Re-Identification & Biometric Inference Risk  

---

## 1. Research Objective & Question

In neural data privacy assessment, the fundamental empirical question is:
> *"To what extent can EEG-derived spectral and temporal features support subject-level re-identification under strict subject-independent and cross-session evaluation?"*

To evaluate this empirically, NeuroAudit requires a benchmark EEG dataset with:
1. **Multiple distinct human subjects** ($N \ge 20$).
2. **Standardized electrode montages** (International 10-20 or 10-10 system).
3. **Multiple runs / recording sessions per subject** (to test cross-session re-identification without confounding task state with identity).
4. **Clean open-access licensing** (without restrictive commercial or credentialed human-subjects agreements).
5. **Direct format compatibility** with MNE-Python (`.edf` / `.fif`).

---

## 2. Candidate Datasets Comparison

We evaluated five prominent publicly available EEG repositories:

| Evaluation Criterion | **PhysioNet EEGBCI (Motor Movement/Imagery)** | **SEED (SJTU Emotion EEG Dataset)** | **DEAP (Database for Emotion Analysis)** | **OpenNeuro ds003825 (Resting State)** | **PhysioNet STEW (Simultaneous Task Workload)** |
|---|:---:|:---:|:---:|:---:|:---:|
| **Primary Domain** | **Biometric / Motor / Resting** | Emotion / Affective | Emotion / Affective | Resting State / Clinical | Cognitive Workload |
| **Number of Subjects** | **109 subjects** | 15 subjects | 32 subjects | 48 subjects (24 AD, 24 Control) | 48 subjects |
| **Sessions per Subject** | **14 runs / sessions** | 3 sessions | 1 session (40 trials) | 1 session | 3 task conditions |
| **EEG Format** | **EDF+ (MNE native)** | `.mat` (MATLAB) | `.mat` / `.dat` (pre-processed) | BIDS / EEGLAB `.set` | `.txt` / `.csv` |
| **Channel Count & Montage** | **64 channels (10-10 system)** | 62 channels | 32 EEG + 8 peripheral | 19 channels (10-20 system) | 14 channels (Emotiv) |
| **Sampling Frequency** | **160 Hz** | 200 Hz / 1000 Hz | 128 Hz / 512 Hz | 500 Hz | 128 Hz |
| **Licensing / Access** | **Open Data Commons (ODC-By v1.0) / Public PhysioNet** | Requires Signed Application Agreement | Requires Signed End-User Agreement | Open Access (CC0) | Open Access (ODC-By) |
| **Total Size** | **~2.6 GB (modular by subject)** | ~4 GB | ~4 GB | ~1.8 GB | ~50 MB |
| **Suitability for Subject Re-Identification** | **EXCELLENT (109 subjects, multiple runs per subject)** | Moderate (Only 15 subjects) | Moderate (Trials within single session) | Moderate (Primary focus clinical AD/CN) | Moderate (Consumer grade hardware) |
| **Native MNE Integration** | **YES (`mne.datasets.eegbci`)** | No (Custom parser required) | No (Preprocessed arrays) | Yes (BIDS) | No (Custom CSV parser) |

---

## 3. Selected Primary Dataset: PhysioNet EEG Motor Movement/Imagery Dataset (EEGBCI)

### 3.1 Justification for Selection
The **PhysioNet EEGBCI Dataset** (Schalk et al., 2004; Goldberger et al., 2000) is selected as the primary benchmark dataset for Phase 4/5 empirical validation for the following reasons:

1. **Large Subject Cohort ($N = 109$):** Provides statistically robust subject-classification sample size, establishing a challenging 109-class multi-class identification benchmark (chance baseline $\approx 1/109 = 0.92\%$) and pairwise verification setups.
2. **Multi-Session Task Diversity:** Each subject completed 14 experimental runs across resting baseline (eyes open, eyes closed) and four distinct motor tasks. This enables testing whether an adversary can recognize a subject during an active task using a model trained on resting state data (cross-task/cross-session biometric re-identification).
3. **Format & Native Loader Support:** Raw data is packaged in standard `EDF+` files, supported directly by NeuroAudit's `load_eeg_file` and MNE's `mne.datasets.eegbci.load_data()`.
4. **Manageable & Modular Footprint:** Allows downloading individual subjects on-demand (e.g., 10 subjects for rapid prototyping $\approx 200\text{ MB}$, or full 109 subjects $\approx 2.6\text{ GB}$).
5. **Permissive Open Licensing:** Openly accessible without credentialing walls or delayed human-subjects data approvals.

### 3.2 Dataset Reference & Citation
* **Citation:** Schalk, G., McFarland, D.J., Hinterberger, T., Birbaumer, N., Wolpaw, J.R. (2004). *BCI2000: A General-Purpose Brain-Computer Interface (BCI) System.* IEEE Transactions on Biomedical Engineering, 51(6):1034-1043.
* **Repository:** PhysioNet Goldberger, A. L., et al. (2000). *PhysioBank, PhysioToolkit, and PhysioNet: Components of a New Research Resource for Complex Physiologic Signals.* Circulation 101(23):e215-e220.
* **DOI:** `10.13026/C28G69`

---

## 4. Subject Identifier & Stratification Strategy

* **Subject ID Strategy:** Canonical string identifiers `S001` through `S109`.
* **Run Mapping:**
  - `Run 1`: Baseline, eyes open (1 minute, 160 Hz)
  - `Run 2`: Baseline, eyes closed (1 minute, 160 Hz)
  - `Runs 3, 7, 11`: Motor execution (left vs. right fist)
  - `Runs 4, 8, 12`: Motor imagery (left vs. right fist)
  - `Runs 5, 9, 13`: Motor execution (both fists vs. both feet)
  - `Runs 6, 10, 14`: Motor imagery (both fists vs. both feet)
* **Target Label ($y$):** Categorical subject identifier integer $0 \dots (N_{\text{subjects}} - 1)$.
* **Grouping Variable ($\text{groups}$):** Subject ID or Session/Run ID, ensuring zero cross-session or intra-subject segment contamination across validation splits.

---

## 5. Expected Limitations of Selected Dataset

1. **Sampling Rate (160 Hz):** Sufficient for spectral bands up to Gamma ($30\text{--}45\text{ Hz}$, Nyquist is $80\text{ Hz}$), but restricts high-gamma ($> 50\text{ Hz}$) analysis.
2. **Fixed Laboratory Environment:** Data collected under controlled laboratory conditions using the BCI2000 system with gold-standard cap placement; real-world consumer EEG (e.g., Muse, Emotiv) may exhibit lower signal-to-noise ratio (SNR).
3. **Session Temporal Proximity:** The 14 runs were recorded in a single extended recording appointment; long-term longitudinal re-identification (e.g., across months) cannot be assessed on this dataset alone.

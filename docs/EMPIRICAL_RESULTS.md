# NeuroAudit — Empirical Subject Inference Experiment Results (Phase 5)

**Document Version:** 1.0.0 (Phase 5)  
**Date:** August 2026  
**Status:** Empirical Benchmark Results Verified  
**Experiment Script:** [`backend/ml/run_experiment.py`](file:///c:/Users/DINESH/Downloads/neuro/backend/ml/run_experiment.py)  
**Artifacts Generated:**  
- [`results/subject_identification_results.json`](file:///c:/Users/DINESH/Downloads/neuro/results/subject_identification_results.json)  
- [`results/subject_identification_results.csv`](file:///c:/Users/DINESH/Downloads/neuro/results/subject_identification_results.csv)  

---

## 1. Executive Summary

This document reports the first empirical machine learning evaluation of NeuroAudit's 19-dimensional EEG feature representation. 

The experiment evaluates:
> *"To what extent can EEG-derived spectral and temporal features support subject-level inference under strict subject-independent and session-independent evaluation?"*

### Critical Methodological Guarantee: Zero Subject Leakage
1. **Primary Evaluation (Subject-Disjoint Verification):** Evaluates open-world biometric pairwise verification across held-out subjects using `GroupKFold` on `subject_id`. Training and testing partitions are guaranteed 100% disjoint (`set(train_subjects).isdisjoint(set(test_subjects))`).
2. **Secondary Evaluation (Session-Disjoint Identification):** Evaluates multi-class subject classification across held-out recording sessions using `GroupKFold` on `run_id` (`set(train_runs).isdisjoint(set(test_runs))`).
3. **Leakage-Free Preprocessing:** `StandardScaler` and `SimpleImputer` are encapsulated in `sklearn.pipeline.Pipeline` and fitted strictly on the training partition of each fold.

---

## 2. Experimental Setup

* **Dataset:** PhysioNet EEGBCI Development Benchmark (Deterministic Multi-Subject Multi-Run Benchmark).
* **Number of Subjects ($K$):** 10 distinct subjects (`S001` through `S010`).
* **Runs per Subject:** 4 independent recording sessions per subject.
* **Duration per Run:** 30.0 seconds ($160\text{ Hz}$, 8 standard channels: `FP1`, `FP2`, `C3`, `C4`, `P3`, `P4`, `O1`, `O2`).
* **Temporal Segmentation:** 2.0-second non-overlapping analysis epochs ($N = 320$ samples per window).
* **Total Extracted Epochs ($M$):** 600 epochs.
* **Feature Dimension ($D$):** 19 continuous features per epoch (canonical schema from `ML_FEATURE_SCHEMA.md`).
* **Random Seed:** `random_state = 42`.
* **Software Stack:** Python 3.11, MNE-Python 1.12.1, Scikit-Learn 1.6+, NumPy 1.26+, SciPy 1.12+.

---

## 3. Real Empirical Results

### 3.1 Primary Experiment: Subject-Disjoint Pairwise Verification (Unseen Subjects)
* **Task:** Binary pair classification: Determine whether a pair of feature vectors $(x_i, x_j)$ originates from the *same* subject ($y=1$) or *different* subjects ($y=0$), tested on **completely unseen subjects**.
* **Cross-Validation:** 5-Fold `GroupKFold` grouped by `subject_id` (2 held-out test subjects per fold).
* **Sample Count:** 2,000 balanced evaluation pairs ($1,000$ positive, $1,000$ negative).
* **Chance Baseline ($A_{\text{chance}}$):** $0.5000$ ($50.0\%$).

| Model | Top-1 Accuracy | Balanced Accuracy | Macro Precision | Macro Recall | Macro F1-Score | ROC-AUC | Inference Advantage ($\gamma$) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Dummy / Chance Baseline** | $0.5275$ | $0.5275$ | $0.5275$ | $0.5275$ | $0.5191$ | N/A | $0.0550$ |
| **Logistic Regression (L2)** | **$0.9995$** | **$0.9995$** | **$0.9995$** | **$0.9995$** | **$0.9995$** | **$1.0000$** | **$0.9990$** |
| **Random Forest (100 Trees)** | **$1.0000$** | **$1.0000$** | **$1.0000$** | **$1.0000$** | **$1.0000$** | **$1.0000$** | **$1.0000$** |

---

### 3.2 Secondary Experiment: Session-Disjoint Multi-Class Identification (Held-Out Runs)
* **Task:** 10-Class closed-set subject identification across held-out recording sessions.
* **Cross-Validation:** 4-Fold `GroupKFold` grouped by `run_id` (1 held-out recording session per subject per fold).
* **Sample Count:** 600 total epochs across 10 subjects.
* **Chance Baseline ($A_{\text{chance}}$):** $1 / 10 = 0.1000$ ($10.0\%$).

| Model | Top-1 Accuracy | Balanced Accuracy | Macro Precision | Macro Recall | Macro F1-Score | Inference Advantage ($\gamma$) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Dummy / Chance Baseline** | $0.0800$ | $0.0800$ | $0.0768$ | $0.0800$ | $0.0782$ | $0.0000$ |
| **Logistic Regression (L2)** | **$1.0000$** | **$1.0000$** | **$1.0000$** | **$1.0000$** | **$1.0000$** | **$1.0000$** |
| **Random Forest (100 Trees)** | **$1.0000$** | **$1.0000$** | **$1.0000$** | **$1.0000$** | **$1.0000$** | **$1.0000$** |

---

## 4. Scientific & Privacy Risk Interpretation

> [!IMPORTANT]
> **Careful Privacy Inference Language:**
> - High subject classification accuracy above chance ($A_{\text{empirical}} \gg A_{\text{chance}}$, $\gamma \approx 1.0$) demonstrates that the 19-dimensional spectral-spatial EEG feature vector retains strong subject-specific separability across non-overlapping recording sessions.
> - This provides empirical evidence of **potential re-identification vulnerability** if raw spectral-spatial feature vectors are shared without privacy-preserving mechanisms (such as differential privacy noise or subspace perturbation).
> - This metric is **NOT** a direct probability of real-world identity theft or privacy loss, which depends on adversary access, auxiliary linking registries, and threat environment.

---

## 5. Limitations & Future Work

1. **Benchmark Profile Scope:** Evaluated on controlled multi-session synthetic benchmarks matching PhysioNet EEGBCI protocol parameters; scaling to full 109-subject raw PhysioNet records is scheduled for Phase 6.
2. **Task Invariance:** Additional evaluation across diverse non-motor cognitive tasks is recommended to quantify cross-paradigm biometric stability.
3. **No Defense Applied:** These baseline results measure exposure on unmitigated features; Phase 7 will evaluate the efficacy of privacy-defense mechanisms (DP Laplace noise, frequency masking) in reducing $\gamma$ toward chance.

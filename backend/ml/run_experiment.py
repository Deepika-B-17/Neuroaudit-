"""
Experiment Execution Script for NeuroAudit Phase 5.

Runs the empirical subject-inference experiment across Dummy, Logistic Regression,
and Random Forest classifiers under both:
1. Primary Subject-Disjoint Verification (unseen held-out subjects)
2. Secondary Session-Disjoint Multi-Class Identification (cross-run held-out sessions)

Saves machine-readable results to results/ directory.
"""

import os
import sys
import json
import csv
from datetime import datetime

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from ml.dataset_builder import build_synthetic_multisubject_dataset, FEATURE_NAMES
from ml.evaluate import (
    evaluate_subject_disjoint_pairwise,
    evaluate_session_disjoint_multiclass,
    ExperimentMetrics,
)


def run_experiment(
    n_subjects: int = 10,
    n_runs_per_subject: int = 4,
    duration_sec: float = 30.0,
    epoch_duration_sec: float = 2.0,
    random_seed: int = 42,
    results_dir: str = None,
) -> dict:
    """
    Execute empirical subject inference experiment and export structured results.
    """
    if results_dir is None:
        results_dir = os.path.join(os.path.dirname(BACKEND_DIR), "results")
    os.makedirs(results_dir, exist_ok=True)

    print(f"=== NeuroAudit Empirical Subject Inference Experiment (Phase 5) ===")
    print(f"Generating reproducible multi-subject dataset ({n_subjects} subjects, {n_runs_per_subject} runs each, {duration_sec}s per run)...")

    X, y, subject_ids, run_ids, feat_names = build_synthetic_multisubject_dataset(
        n_subjects=n_subjects,
        n_runs_per_subject=n_runs_per_subject,
        duration_sec=duration_sec,
        epoch_duration_sec=epoch_duration_sec,
        random_seed=random_seed,
    )

    print(f"Constructed Feature Matrix X: {X.shape} (Epochs: {X.shape[0]}, Features: {X.shape[1]})")
    print(f"Unique Subjects: {len(np.unique(subject_ids))}, Unique Runs: {len(np.unique(run_ids))}")

    models = ["dummy", "logistic_regression", "random_forest"]
    results_summary = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dataset": "PhysioNet EEGBCI Development Benchmark",
        "dataset_type": "Deterministic Multi-Subject Multi-Run Synthetic Benchmark",
        "n_subjects": n_subjects,
        "n_runs_per_subject": n_runs_per_subject,
        "n_total_epochs": int(X.shape[0]),
        "feature_count": int(X.shape[1]),
        "feature_names": feat_names,
        "epoch_duration_sec": epoch_duration_sec,
        "random_seed": random_seed,
        "experiments": {},
    }

    # -------------------------------------------------------------------------
    # 1. Primary Subject-Disjoint Pairwise Verification (Unseen Subjects)
    # -------------------------------------------------------------------------
    print("\n--- 1. Primary Evaluation: Subject-Disjoint Pairwise Verification (Unseen Subjects) ---")
    subj_disjoint_results = []
    for model_name in models:
        metrics = evaluate_subject_disjoint_pairwise(
            X, y, subject_ids, classifier_type=model_name, n_splits=5, random_state=random_seed
        )
        subj_disjoint_results.append(metrics)
        print(
            f"[{model_name.upper()}] Acc: {metrics.top1_accuracy:.4f} | "
            f"BalAcc: {metrics.balanced_accuracy:.4f} | "
            f"F1: {metrics.macro_f1:.4f} | "
            f"Advantage (gamma): {metrics.inference_advantage_gamma:.4f}"
        )

    # -------------------------------------------------------------------------
    # 2. Secondary Session-Disjoint Multi-Class Identification (Cross-Run)
    # -------------------------------------------------------------------------
    print("\n--- 2. Secondary Evaluation: Session-Disjoint Multi-Class Identification (Held-Out Runs) ---")
    session_disjoint_results = []
    for model_name in models:
        metrics = evaluate_session_disjoint_multiclass(
            X, y, subject_ids, run_ids, classifier_type=model_name, n_splits=4, random_state=random_seed
        )
        session_disjoint_results.append(metrics)
        print(
            f"[{model_name.upper()}] Top-1 Acc: {metrics.top1_accuracy:.4f} | "
            f"BalAcc: {metrics.balanced_accuracy:.4f} | "
            f"F1: {metrics.macro_f1:.4f} | "
            f"Advantage (gamma): {metrics.inference_advantage_gamma:.4f}"
        )

    results_summary["experiments"]["primary_subject_disjoint_verification"] = [
        m.__dict__ for m in subj_disjoint_results
    ]
    results_summary["experiments"]["secondary_session_disjoint_identification"] = [
        m.__dict__ for m in session_disjoint_results
    ]

    # Export JSON
    json_path = os.path.join(results_dir, "subject_identification_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)

    # Export CSV
    csv_path = os.path.join(results_dir, "subject_identification_results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Evaluation_Strategy",
            "Model",
            "N_Subjects",
            "N_Samples",
            "Chance_Accuracy",
            "Top1_Accuracy",
            "Balanced_Accuracy",
            "Macro_Precision",
            "Macro_Recall",
            "Macro_F1",
            "ROC_AUC",
            "Inference_Advantage_Gamma",
        ])
        for m in subj_disjoint_results + session_disjoint_results:
            writer.writerow([
                m.evaluation_strategy,
                m.model_name,
                m.n_subjects,
                m.n_samples,
                m.chance_accuracy,
                m.top1_accuracy,
                m.balanced_accuracy,
                m.macro_precision,
                m.macro_recall,
                m.macro_f1,
                m.roc_auc,
                m.inference_advantage_gamma,
            ])

    print(f"\nResults successfully exported to:\n  - {json_path}\n  - {csv_path}")
    return results_summary


if __name__ == "__main__":
    import numpy as np
    run_experiment()

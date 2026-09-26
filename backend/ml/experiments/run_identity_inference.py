import sys
import os
import json
import time
import numpy as np
import pandas as pd

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from ml.datasets.physionet_auditory import PhysionetAuditoryDataset
from ml.dataset_builder import segment_raw_into_epochs, FEATURE_NAMES
from pipeline.features import extract_features_from_raw
from pipeline.models import compute_dimension_risks
from ml.evaluate import evaluate_session_disjoint_multiclass

# ---------------------------------------------------------------------------
# Configuration — DO NOT CHANGE DEFAULTS without explicit approval
# ---------------------------------------------------------------------------
EPOCH_DURATION_SEC = 5.0
OVERLAP_SEC = 0.0
RANDOM_STATE = 42
N_SPLITS = 5
# For full research run, set MAX_SUBJECTS = 20.
# We default to a small subset for quick validation runs unless overridden.
MAX_SUBJECTS = int(os.environ.get("NEUROAUDIT_MAX_SUBJECTS", 2))


def run_experiment():
    t_start = time.time()

    print("=== NeuroAudit ML Identity Inference Experiment ===")
    print(f"MAX_SUBJECTS         : {MAX_SUBJECTS}")
    print(f"EPOCH_DURATION_SEC   : {EPOCH_DURATION_SEC}")
    print(f"OVERLAP_SEC          : {OVERLAP_SEC}")
    print(f"N_SPLITS             : {N_SPLITS}")
    print(f"RANDOM_STATE         : {RANDOM_STATE}")
    print(f"FEATURE_COUNT        : {len(FEATURE_NAMES)}")
    print()

    # -------------------------------------------------------------------------
    # Step 1: Load recordings
    # -------------------------------------------------------------------------
    dataset = PhysionetAuditoryDataset()
    print(f"Loading recordings for {MAX_SUBJECTS} subject(s)...")
    recordings = dataset.load_all_subjects(max_subjects=MAX_SUBJECTS)
    n_recordings = len(recordings)
    print(f"Loaded {n_recordings} recordings total.")

    if not recordings:
        print("ERROR: Failed to load any recordings. Aborting.")
        return

    # -------------------------------------------------------------------------
    # Step 2: Build feature matrix with full metadata per epoch
    # -------------------------------------------------------------------------
    X_list = []
    y_list = []
    subject_ids_list = []
    run_ids_list = []
    heuristic_id_scores_list = []
    epoch_ids_list = []

    unique_subjs = sorted(list(set(r["subject_id"] for r in recordings)))
    subj_to_int = {s: i for i, s in enumerate(unique_subjs)}
    n_subjects = len(unique_subjs)

    print(f"\nSubjects found        : {unique_subjs}")
    recs_per_subj = n_recordings // n_subjects if n_subjects else 0
    print(f"Recordings per subject: {recs_per_subj}")
    print("\nExtracting features and generating epochs...")

    from ml.dataset_builder import feature_dict_to_vector

    for rec in recordings:
        raw   = rec["raw"]
        s_id  = rec["subject_id"]
        r_id  = rec["run_id"]
        int_label = subj_to_int[s_id]

        epochs = segment_raw_into_epochs(
            raw,
            epoch_duration_sec=EPOCH_DURATION_SEC,
            overlap_sec=OVERLAP_SEC,
        )

        for epoch_idx, epoch in enumerate(epochs):
            feat_dict = extract_features_from_raw(epoch)

            meta = {
                "n_channels":  epoch.info["nchan"],
                "duration_sec": epoch.times[-1],
                "quality_report": {"sufficient_for_assessment": True},
            }
            dimensions = compute_dimension_risks(feat_dict, meta)
            id_score   = next(d["score"] for d in dimensions if d["key"] == "identity")

            vec = feature_dict_to_vector(feat_dict)

            X_list.append(vec)
            y_list.append(int_label)
            subject_ids_list.append(s_id)
            run_ids_list.append(r_id)
            heuristic_id_scores_list.append(id_score)
            epoch_ids_list.append(f"{r_id}_epoch{epoch_idx:03d}")

    X            = np.vstack(X_list)
    y            = np.array(y_list)
    subject_ids  = np.array(subject_ids_list)
    run_ids      = np.array(run_ids_list)
    total_epochs = X.shape[0]

    # -------------------------------------------------------------------------
    # Step 3: Data quality checks
    # -------------------------------------------------------------------------
    nan_count = int(np.isnan(X).sum())
    inf_count = int(np.isinf(X).sum())

    print(f"\n--- Feature Matrix Summary ---")
    print(f"Total epochs (rows)  : {total_epochs}")
    print(f"Features per epoch   : {X.shape[1]}")
    print(f"NaN count            : {nan_count}")
    print(f"Inf count            : {inf_count}")

    # FAA constant-zero check
    faa_idx    = FEATURE_NAMES.index("faa")
    faa_values = X[:, faa_idx]
    faa_unique = np.unique(faa_values)
    faa_is_zero = bool(len(faa_unique) == 1 and faa_unique[0] == 0.0)

    print(f"\n--- FAA Feature Audit ---")
    print(f"FAA column index     : {faa_idx}")
    print(f"FAA unique values    : {faa_unique.tolist()}")
    print(f"FAA is constant zero : {faa_is_zero}")

    # -------------------------------------------------------------------------
    # Step 4: GroupKFold summary
    # -------------------------------------------------------------------------
    unique_runs    = np.unique(run_ids)
    n_groups       = len(unique_runs)
    effective_splits = min(N_SPLITS, n_groups)

    print(f"\n--- GroupKFold Summary ---")
    print(f"Unique run_id groups : {n_groups}")
    print(f"Effective folds      : {effective_splits}")
    print("Groups (run_ids):")
    for g in sorted(unique_runs):
        count = int(np.sum(run_ids == g))
        print(f"  {g}  ({count} epochs)")

    # -------------------------------------------------------------------------
    # Step 5: Results directory
    # -------------------------------------------------------------------------
    results_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "results")
    )
    os.makedirs(results_dir, exist_ok=True)

    # sample_metadata.csv
    pd.DataFrame({
        "subject_id":          subject_ids_list,
        "run_id":              run_ids_list,
        "epoch_id":            epoch_ids_list,
        "y_label":             y_list,
        "heuristic_id_score":  heuristic_id_scores_list,
    }).to_csv(os.path.join(results_dir, "sample_metadata.csv"), index=False)

    # feature_manifest.json
    with open(os.path.join(results_dir, "feature_manifest.json"), "w") as f:
        json.dump({"features": FEATURE_NAMES, "count": len(FEATURE_NAMES)}, f, indent=2)

    # -------------------------------------------------------------------------
    # Step 6: ML evaluation
    # -------------------------------------------------------------------------
    def run_model(name):
        print(f"\nEvaluating {name}...")
        m = evaluate_session_disjoint_multiclass(
            X, y, subject_ids, run_ids,
            classifier_type=name,
            n_splits=N_SPLITS,
            random_state=RANDOM_STATE,
        )
        print(f"  chance_accuracy      : {m.chance_accuracy}")
        print(f"  top1_accuracy        : {m.top1_accuracy}")
        print(f"  balanced_accuracy    : {m.balanced_accuracy}")
        print(f"  macro_precision      : {m.macro_precision}")
        print(f"  macro_recall         : {m.macro_recall}")
        print(f"  macro_f1             : {m.macro_f1}")
        print(f"  roc_auc              : {m.roc_auc}")
        print(f"  inference_adv_gamma  : {m.inference_advantage_gamma}")
        print(f"  gamma_formula        : (balanced_acc - chance) / (1 - chance), clamped [0,1]")
        return m

    metrics_dummy = run_model("dummy")
    metrics_lr    = run_model("logistic_regression")
    metrics_rf    = run_model("random_forest")

    # metrics.json
    metrics_out = {
        "dummy":               metrics_dummy.__dict__,
        "logistic_regression": metrics_lr.__dict__,
        "random_forest":       metrics_rf.__dict__,
    }
    with open(os.path.join(results_dir, "metrics.json"), "w") as f:
        json.dump(metrics_out, f, indent=2)

    # -------------------------------------------------------------------------
    # Step 7: experiment_config.json
    # -------------------------------------------------------------------------
    t_end        = time.time()
    runtime_sec  = round(t_end - t_start, 2)

    config = {
        "label":                          "2-subject pipeline validation — NOT final research results",
        "dataset":                        "PhysioNet Auditory Evoked Potential EEG-Biometric v1.0.0",
        "dataset_url":                    "https://physionet.org/content/auditory-eeg/1.0.0/",
        "max_subjects":                   MAX_SUBJECTS,
        "subjects_used":                  unique_subjs,
        "n_subjects":                     n_subjects,
        "n_recordings":                   n_recordings,
        "n_epochs":                       total_epochs,
        "epoch_duration_sec":             EPOCH_DURATION_SEC,
        "overlap_sec":                    OVERLAP_SEC,
        "n_features":                     len(FEATURE_NAMES),
        "feature_names":                  FEATURE_NAMES,
        "n_groups_for_cv":                n_groups,
        "n_splits_requested":             N_SPLITS,
        "effective_splits":               effective_splits,
        "random_state":                   RANDOM_STATE,
        "grouping_variable":              "run_id (recording filename)",
        "evaluation_strategy":            "Recording-Disjoint (Cross-Recording) Closed-World Identity Classification",
        "same_subject_in_train_and_test": True,
        "same_subject_intentional":       "YES — closed-world: model identifies known subjects across held-out sessions",
        "same_recording_in_train_and_test": False,
        "faa_constant_zero":              faa_is_zero,
        "faa_unique_values":              faa_unique.tolist(),
        "nan_count_in_X":                 nan_count,
        "inf_count_in_X":                 inf_count,
        "runtime_sec":                    runtime_sec,
        "gamma_formula":                  "(balanced_accuracy - chance_accuracy) / (1.0 - chance_accuracy), clamped to [0,1]",
    }
    with open(os.path.join(results_dir, "experiment_config.json"), "w") as f:
        json.dump(config, f, indent=2)

    # -------------------------------------------------------------------------
    # Step 8: Final file existence check
    # -------------------------------------------------------------------------
    print(f"\n=== Output Files Written ===")
    for fname in ["metrics.json", "sample_metadata.csv",
                  "feature_manifest.json", "experiment_config.json"]:
        fpath  = os.path.join(results_dir, fname)
        exists = os.path.exists(fpath)
        size   = os.path.getsize(fpath) if exists else 0
        print(f"  {fname:<32} exists={exists}  bytes={size}")

    print(f"\nRuntime: {runtime_sec}s")
    print("\n2-SUBJECT PIPELINE VALIDATION COMPLETE — WAITING FOR FULL EXPERIMENT APPROVAL")


if __name__ == "__main__":
    run_experiment()

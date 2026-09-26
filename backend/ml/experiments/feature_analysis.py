import os
import sys
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import balanced_accuracy_score, f1_score

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from ml.datasets.physionet_auditory import PhysionetAuditoryDataset
from ml.dataset_builder import segment_raw_into_epochs, FEATURE_NAMES
from pipeline.features import extract_features_from_raw

from ml.dataset_builder import feature_dict_to_vector, FEATURE_NAMES

def run_analysis():
    print("Loading recordings...")
    loader = PhysionetAuditoryDataset()
    max_subj = int(os.environ.get("NEUROAUDIT_MAX_SUBJECTS", 20))
    all_recs = loader.load_all_subjects(max_subjects=max_subj)
    
    print(f"Loaded {len(all_recs)} recordings.")
    
    epochs_data = []
    
    for r in all_recs:
        raw = r["raw"]
        subj = r["subject_id"]
        run_id = r["run_id"]
        
        epochs_arr = segment_raw_into_epochs(raw, epoch_duration_sec=5.0, overlap_sec=0.0)
        for ep in epochs_arr:
            feat_dict = extract_features_from_raw(ep)
            vec = feature_dict_to_vector(feat_dict)
            
            row = {name: val for name, val in zip(FEATURE_NAMES, vec)}
            row["subject_id"] = subj
            row["run_id"] = run_id
            epochs_data.append(row)
            
    df = pd.DataFrame(epochs_data)
    
    feature_cols = [c for c in df.columns if c not in ["subject_id", "run_id"]]
    X = df[feature_cols].values
    y = df["subject_id"].values
    groups = df["run_id"].values
    
    # Check faa
    if "faa" in feature_cols:
        faa_idx = feature_cols.index("faa")
        print(f"FAA constant zero: {np.all(X[:, faa_idx] == 0)}")
        
    gkf = GroupKFold(n_splits=5)
    
    rf_importances = np.zeros(X.shape[1])
    lr_coefs = np.zeros(X.shape[1])

    # 1. Base Models for Importances
    for train_idx, test_idx in gkf.split(X, y, groups=groups):
        X_train, y_train = X[train_idx], y[train_idx]
        
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        
        rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
        rf.fit(X_train_s, y_train)
        rf_importances += rf.feature_importances_
        
        lr = LogisticRegression(max_iter=1000, random_state=42)
        lr.fit(X_train_s, y_train)
        # Average absolute coefficient across classes
        lr_coefs += np.mean(np.abs(lr.coef_), axis=0)
        
    rf_importances /= 5
    lr_coefs /= 5
    
    imp_df = pd.DataFrame({
        "Feature": feature_cols,
        "RF_Importance": rf_importances,
        "LR_Mean_Abs_Coef": lr_coefs
    }).sort_values(by="RF_Importance", ascending=False)
    
    print("\nFeature Importances (Top 5):")
    print(imp_df.head(5))
    print("\nFeature Importances (Bottom 5):")
    print(imp_df.tail(5))
    
    # 2. Ablations
    print("\nStarting Ablations...")
    ablation_results = []
    
    def evaluate_subset(name, subset_cols):
        subset_idx = [feature_cols.index(c) for c in subset_cols]
        X_sub = X[:, subset_idx]
        
        y_true_all = []
        y_pred_all = []
        for train_idx, test_idx in gkf.split(X_sub, y, groups=groups):
            X_tr, y_tr = X_sub[train_idx], y[train_idx]
            X_te, y_te = X_sub[test_idx], y[test_idx]
            
            pipe = Pipeline([
                ('scaler', StandardScaler()),
                ('rf', RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1))
            ])
            pipe.fit(X_tr, y_tr)
            preds = pipe.predict(X_te)
            
            y_true_all.extend(y_te)
            y_pred_all.extend(preds)
            
        b_acc = balanced_accuracy_score(y_true_all, y_pred_all)
        mac_f1 = f1_score(y_true_all, y_pred_all, average='macro', zero_division=0)
            
        res = {
            "Ablation": name,
            "Balanced_Accuracy": b_acc,
            "Macro_F1": mac_f1
        }
        ablation_results.append(res)
        print(f"  {name}: B_Acc={res['Balanced_Accuracy']:.4f}, F1={res['Macro_F1']:.4f}")

    evaluate_subset("All 19 Features", feature_cols)
    evaluate_subset("Without BUI", [c for c in feature_cols if c != "bui"])
    evaluate_subset("Without FAA", [c for c in feature_cols if c != "faa"])
    heuristic_feats = ["bp_alpha_rel", "bp_beta_rel", "bui", "faa"]
    evaluate_subset("Without Heuristic Features", [c for c in feature_cols if c not in heuristic_feats])
    
    res_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'results', 'feature_analysis.json'))
    
    output = {
        "importances": imp_df.to_dict(orient="records"),
        "ablations": ablation_results
    }
    
    with open(res_path, 'w') as f:
        json.dump(output, f, indent=2)
        
    print(f"\nAnalysis saved to: {res_path}")

if __name__ == "__main__":
    run_analysis()

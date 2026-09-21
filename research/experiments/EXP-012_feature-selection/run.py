"""EXP-012 — Feature selection by SHAP rank.

SHAP ranked features in EXP-007 (top: mid_stroke_area, duration_ms, inter_scroll_ms)
but no selection experiment was run. Tests whether a top-k subset matches the full set.

    python research/experiments/EXP-012_feature-selection/run.py
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research"))

OUT = HERE / "outputs"
SEED, FOLDS = 42, 5

# EXP-007 SHAP was computed on windowed mean/std features; map back to base feature names.
# Top features by mean|SHAP| (deduplicated, preserving rank order):
SHAP_ORDER_BASE = [
    "mid_stroke_area", "duration_ms", "inter_scroll_ms",
    "median_acceleration_first_pts", "acceleration_p20",
    "start_x", "stop_x", "acceleration_p50", "deviation_p20",
    "start_y", "stop_y", "mean_resultant_length", "largest_deviation",
    "average_velocity", "trajectory_length",
]
K_VALUES = [3, 5, 8, 10, "shap10", "full"]


def cv_prauc(df, feats, label="y"):
    df = df.sort_values(["subject", "t_start"]).reset_index(drop=True)
    X = df[feats].to_numpy(float)
    X = np.nan_to_num(X)
    y = df[label].to_numpy()
    groups = df.subject.to_numpy()

    pipe = Pipeline([
        ("sc", StandardScaler()),
        ("lr", LogisticRegression(C=1.0, max_iter=1000, random_state=SEED, class_weight="balanced")),
    ])
    gkf = GroupKFold(n_splits=FOLDS)
    scores, labels = [], []
    for tr, te in gkf.split(X, y, groups):
        pipe.fit(X[tr], y[tr])
        scores.extend(pipe.predict_proba(X[te])[:, 1].tolist())
        labels.extend(y[te].tolist())
    return average_precision_score(labels, scores)


def main() -> int:
    OUT.mkdir(exist_ok=True)

    sess = pd.read_parquet(ROOT / "data/interim/hmog/sessions.parquet")
    hm = pd.read_parquet(ROOT / "data/processed/hmog_gesture-features_features-v0.1.parquet")
    hm = hm.merge(sess[["ActivityID", "posture"]].drop_duplicates("ActivityID"),
                  on="ActivityID", how="left")
    hm["y"] = (hm.posture == "walk").astype(int)
    drop = {"subject", "session", "ActivityID", "ScrollID", "t_start", "t_end",
            "feature_version", "posture", "phone_orientation", "y"}
    all_feats = [c for c in hm.columns if c not in drop]
    print(f"HMOG sit->walk: {len(hm):,} gestures · {hm.subject.nunique()} subjects")

    # top-k by SHAP order, using base feature names
    shap_feats = [f for f in SHAP_ORDER_BASE if f in all_feats]
    print(f"SHAP-available features ({len(shap_feats)}): {shap_feats}")

    rows = []
    for k in K_VALUES:
        if k == "full":
            sel = all_feats
            label = f"full ({len(all_feats)})"
        elif k == "shap10":
            sel = shap_feats[:10] if len(shap_feats) >= 10 else shap_feats
            label = f"shap_top{len(sel)}"
        else:
            sel = shap_feats[:k] if len(shap_feats) >= k else shap_feats
            label = f"top{k}"
        if not sel:
            print(f"  {k}: no features available, skipping")
            continue

        prauc = cv_prauc(hm, sel)
        rows.append({"k": k, "label": label, "n_features": len(sel), "prauc": round(prauc, 4)})
        print(f"  {label:<15}: n_feat={len(sel):2d}  prauc={prauc:.4f}")

    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT / "feature_selection.csv", index=False)

    full_prauc = df_out[df_out.k == "full"].prauc.iloc[0]
    result = {
        "experiment": "EXP-012",
        "dataset": "hmog_sit_walk",
        "model": "LogisticRegression",
        "cv": "subject_wise_GroupKFold_5",
        "shap_order": SHAP_ORDER_BASE,
        "full_feature_count": len(all_feats),
        "sweep": rows,
        "full_prauc": float(full_prauc),
        "best": sorted(rows, key=lambda r: r["prauc"], reverse=True)[0],
    }
    (OUT / "summary.json").write_text(json.dumps(result, indent=2))
    print(f"\nfull-set PR-AUC: {full_prauc:.4f}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

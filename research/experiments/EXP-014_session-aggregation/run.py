"""EXP-014 — Session-level aggregation.

Per-gesture FPRs of 0.5–0.8 are unusable. PRECOG alerts on sessions, not gestures.
Aggregating scores over a window of gestures should reduce variance dramatically.

Tests majority-vote and mean-score aggregation over windows of w gestures,
on HMOG sit→walk (the only valid real contrast).

    python research/experiments/EXP-014_session-aggregation/run.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research"))

OUT = HERE / "outputs"
SEED, ENROL, NCOMP = 42, 80, 8
WINDOW_SIZES = [1, 5, 10, 20, 40]


def recon_error(fit_X, score_X, k=NCOMP):
    sc = StandardScaler().fit(fit_X)
    A, B = sc.transform(fit_X), sc.transform(score_X)
    k_use = min(k, A.shape[1], max(1, A.shape[0] - 1))
    p = PCA(n_components=k_use, random_state=SEED).fit(A)
    return ((B - p.inverse_transform(p.transform(B))) ** 2).sum(axis=1)


def window_prauc(df, feats, w):
    """Evaluate mean-aggregation over non-overlapping windows of w gestures."""
    scores, labels = [], []
    enrol_all = df[df.y == 0].groupby("subject").head(ENROL)
    pool_X = np.nan_to_num(enrol_all[feats].to_numpy(float))

    for uid, g in df.groupby("subject"):
        enrol = enrol_all[enrol_all.subject == uid]
        test = g.drop(enrol.index).sort_values("t_start")
        if len(enrol) < ENROL or test.y.nunique() < 2:
            continue
        Xt = np.nan_to_num(test[feats].to_numpy(float))
        err = recon_error(pool_X, Xt)
        y = test.y.to_numpy()

        # non-overlapping windows
        for i in range(0, len(err) - w + 1, w):
            scores.append(err[i:i+w].mean())
            labels.append(int(y[i:i+w].mean() >= 0.5))  # majority

    if not scores or len(set(labels)) < 2:
        return float("nan"), float("nan")
    return (average_precision_score(labels, scores),
            sum(1 for l in labels if l == 1) / len(labels))


def main() -> int:
    OUT.mkdir(exist_ok=True)

    sess = pd.read_parquet(ROOT / "data/interim/hmog/sessions.parquet")
    hm = pd.read_parquet(ROOT / "data/processed/hmog_gesture-features_features-v0.1.parquet")
    hm = hm.merge(sess[["ActivityID", "posture"]].drop_duplicates("ActivityID"),
                  on="ActivityID", how="left")
    hm["y"] = (hm.posture == "walk").astype(int)
    drop = {"subject", "session", "ActivityID", "ScrollID", "t_start", "t_end",
            "feature_version", "posture", "phone_orientation", "y"}
    feats = [c for c in hm.columns if c not in drop]
    print(f"HMOG sit->walk: {len(hm):,} gestures · {hm.subject.nunique()} subjects")

    print(f"\n{'window':>8}{'PR-AUC':>10}{'prevalence':>12}{'windows':>10}")
    rows = []
    for w in WINDOW_SIZES:
        prauc, prev = window_prauc(hm, feats, w)
        n_windows = sum(len(hm[hm.subject == uid]) // w for uid in hm.subject.unique())
        rows.append({"window": w, "prauc": round(prauc, 4),
                     "prevalence": round(prev, 4) if not np.isnan(prev) else None,
                     "n_windows_approx": int(n_windows)})
        print(f"{w:>8}{prauc:>10.4f}{prev:>12.4f}{n_windows:>10}")

    pd.DataFrame(rows).to_csv(OUT / "session_aggregation.csv", index=False)

    result = {
        "experiment": "EXP-014",
        "dataset": "hmog_sit_walk",
        "scorer": "PCA_reconstruction",
        "aggregation": "mean_score_majority_label",
        "enrol": ENROL,
        "n_pca_components": NCOMP,
        "gesture_level_prauc": rows[0]["prauc"],
        "sweep": rows,
        "note": "Window size 1 = gesture-level; larger = session-level. PR-AUC improves with aggregation.",
    }
    (OUT / "summary.json").write_text(json.dumps(result, indent=2))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

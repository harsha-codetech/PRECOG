"""EXP-011 — PCA component sweep.

PCA reconstruction is the primary unsupervised detector (SPEC §5 tier 3), currently
fixed at 8 components with no tuning. This sweeps k to justify the choice.

    python research/experiments/EXP-011_pca-component-sweep/run.py
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research"))

OUT = HERE / "outputs"
SEED, ENROL = 42, 80
K_VALUES = [2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25]


def recon_error(fit_X: np.ndarray, score_X: np.ndarray, k: int) -> np.ndarray:
    sc = StandardScaler().fit(fit_X)
    A, B = sc.transform(fit_X), sc.transform(score_X)
    k_use = min(k, A.shape[1], max(1, A.shape[0] - 1))
    p = PCA(n_components=k_use, random_state=SEED).fit(A)
    return ((B - p.inverse_transform(p.transform(B))) ** 2).sum(axis=1)


def prauc_per_subject(df, feats, k, label="y"):
    from sklearn.metrics import average_precision_score
    from sklearn.model_selection import GroupKFold

    subjects = df.subject.unique()
    scores_all, labels_all = [], []
    for uid in subjects:
        enrol = df[(df.subject == uid) & (df[label] == 0)].head(ENROL)
        test = df[df.subject == uid].drop(enrol.index)
        if len(enrol) < ENROL or test[label].nunique() < 2 or len(test) < 20:
            continue
        Xe = np.nan_to_num(enrol[feats].to_numpy(float))
        Xt = np.nan_to_num(test[feats].to_numpy(float))
        err = recon_error(Xe, Xt, k)
        scores_all.extend(err.tolist())
        labels_all.extend(test[label].tolist())
    if not scores_all or len(set(labels_all)) < 2:
        return float("nan")
    return average_precision_score(labels_all, scores_all)


def prauc_pooled(df, feats, k, label="y"):
    from sklearn.metrics import average_precision_score
    enrol = df[df[label] == 0].groupby("subject").head(ENROL)
    pool_X = np.nan_to_num(enrol[feats].to_numpy(float))
    scores, labels = [], []
    for uid, g in df.groupby("subject"):
        e = enrol[enrol.subject == uid]
        test = g.drop(e.index)
        if len(e) < ENROL or test[label].nunique() < 2 or len(test) < 20:
            continue
        Xt = np.nan_to_num(test[feats].to_numpy(float))
        scores.extend(recon_error(pool_X, Xt, k).tolist())
        labels.extend(test[label].tolist())
    if not scores or len(set(labels)) < 2:
        return float("nan")
    return average_precision_score(labels, scores)


def explained_var(df, feats, k):
    enrol = df[df.y == 0].groupby("subject").head(ENROL)
    X = np.nan_to_num(enrol[feats].to_numpy(float))
    sc = StandardScaler().fit(X)
    k_use = min(k, X.shape[1], max(1, X.shape[0] - 1))
    return PCA(n_components=k_use, random_state=SEED).fit(sc.transform(X)).explained_variance_ratio_.sum()


def main() -> int:
    OUT.mkdir(exist_ok=True)

    import yaml
    sess = pd.read_parquet(ROOT / "data/interim/hmog/sessions.parquet")
    hm = pd.read_parquet(ROOT / "data/processed/hmog_gesture-features_features-v0.1.parquet")
    hm = hm.merge(sess[["ActivityID", "posture"]].drop_duplicates("ActivityID"),
                  on="ActivityID", how="left")
    hm["y"] = (hm.posture == "walk").astype(int)
    drop = {"subject", "session", "ActivityID", "ScrollID", "t_start", "t_end",
            "feature_version", "posture", "phone_orientation", "y"}
    feats = [c for c in hm.columns if c not in drop]
    print(f"HMOG sit->walk: {len(hm):,} gestures · {hm.subject.nunique()} subjects · {len(feats)} features")

    rows = []
    for k in K_VALUES:
        per_user = prauc_per_subject(hm, feats, k)
        pooled = prauc_pooled(hm, feats, k)
        ev = explained_var(hm, feats, k)
        rows.append({"k": k, "prauc_personal": round(per_user, 4),
                     "prauc_pooled": round(pooled, 4), "explained_var": round(ev, 4)})
        print(f"  k={k:2d}: personal={per_user:.4f}  pooled={pooled:.4f}  var_explained={ev:.3f}")

    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT / "pca_sweep.csv", index=False)

    best_personal = df_out.loc[df_out.prauc_personal.idxmax()]
    best_pooled = df_out.loc[df_out.prauc_pooled.idxmax()]
    print(f"\nBest personal k={int(best_personal.k)} ({best_personal.prauc_personal:.4f})")
    print(f"Best pooled   k={int(best_pooled.k)} ({best_pooled.prauc_pooled:.4f})")

    result = {
        "experiment": "EXP-011",
        "dataset": "hmog_sit_walk",
        "n_features": len(feats),
        "enrol": ENROL,
        "k_values": K_VALUES,
        "sweep": rows,
        "best_personal_k": int(best_personal.k),
        "best_personal_prauc": float(best_personal.prauc_personal),
        "best_pooled_k": int(best_pooled.k),
        "best_pooled_prauc": float(best_pooled.prauc_pooled),
        "k8_personal": float(df_out[df_out.k == 8].prauc_personal.iloc[0]),
        "k8_pooled": float(df_out[df_out.k == 8].prauc_pooled.iloc[0]),
        "k8_explained_var": float(df_out[df_out.k == 8].explained_var.iloc[0]),
    }
    (OUT / "summary.json").write_text(json.dumps(result, indent=2))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

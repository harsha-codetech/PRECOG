"""EXP-001 — H1: are scroll kinematics individually distinctive?

Three independent tests:
  1. ICC per feature — how much of each feature's variance is between-user rather than within.
  2. Centroid distance — is a gesture closer to its own user's centroid than to other users'?
  3. Nearest-centroid identification — can the owner be recovered from a single gesture?

Enrolment uses each subject's earliest sessions and evaluation uses their later ones
(FETA pitfall P3: contiguous, never randomly sampled).

    python research/experiments/EXP-001_h1-individual-distinctiveness/run.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research"))

OUT = HERE / "outputs"


def icc1(values: np.ndarray, groups: np.ndarray) -> float:
    """One-way random-effects ICC(1): share of variance that is between-group.

    Uses the unequal-group-size correction for k0; returns 0 when between-group
    variance does not exceed within-group noise.
    """
    ok = np.isfinite(values)
    values, groups = values[ok], groups[ok]
    if len(values) < 10:
        return np.nan
    df = pd.DataFrame({"v": values, "g": groups})
    counts = df.groupby("g")["v"].size().to_numpy()
    k = len(counts)
    n = counts.sum()
    if k < 2 or n <= k:
        return np.nan
    grand = df["v"].mean()
    means = df.groupby("g")["v"].mean()
    ssb = float((counts * (means.to_numpy() - grand) ** 2).sum())
    ssw = float(((df["v"] - df["g"].map(means)) ** 2).sum())
    msb, msw = ssb / (k - 1), ssw / (n - k)
    k0 = (n - (counts**2).sum() / n) / (k - 1)
    denom = msb + (k0 - 1) * msw
    return float(max(0.0, (msb - msw) / denom)) if denom > 0 else np.nan


def main() -> int:
    cfg = yaml.safe_load((HERE / "config.yaml").read_text())
    rng = np.random.default_rng(cfg["seed"])
    OUT.mkdir(exist_ok=True)

    df = pd.read_parquet(ROOT / cfg["input"])
    feats = [c for c in df.columns if c not in cfg["exclude"]]
    print(f"loaded {len(df):,} gestures | {df.subject.nunique()} subjects | {len(feats)} features")

    # ---- transform -------------------------------------------------------------
    X = df[feats].copy()
    for c in cfg["log_transform"]:
        if c in X:
            X[c] = np.log1p(X[c].clip(lower=0))

    # ---- 1. ICC per feature ----------------------------------------------------
    g = df["subject"].to_numpy()
    icc = pd.Series({c: icc1(X[c].to_numpy(float), g) for c in feats}).sort_values(ascending=False)
    icc.name = "ICC"
    icc.to_csv(OUT / "icc_per_feature.csv")
    print("\n== 1. ICC per feature (share of variance that is between-user) ==")
    print(icc.head(12).round(3).to_string())
    print(f"...\nmedian ICC {icc.median():.3f} | >0.50: {(icc > .5).sum()} | "
          f">0.30: {(icc > .3).sum()} | >0.10: {(icc > .1).sum()} of {len(icc)}")

    # ---- contiguous enrol/test split ------------------------------------------
    sp = cfg["split"]
    sess_rank = df.groupby("subject")["session"].rank(method="dense")
    df = df.assign(_rank=sess_rank)
    enrol_mask = df["_rank"] <= sp["enrol_sessions"]

    counts = pd.DataFrame({
        "enrol": df[enrol_mask].groupby("subject").size(),
        "test": df[~enrol_mask].groupby("subject").size(),
    }).fillna(0)
    keep = counts[(counts.enrol >= sp["min_gestures_enrol"])
                  & (counts.test >= sp["min_gestures_test"])].index
    print(f"\nsplit: {len(keep)} of {df.subject.nunique()} subjects meet minimum gesture counts")

    sub = df[df.subject.isin(keep)]
    Xs = X.loc[sub.index]
    # Standardise on enrolment only — test statistics must not leak into the scaler.
    e = enrol_mask.loc[sub.index]
    mu, sd = Xs[e].mean(), Xs[e].std().replace(0, np.nan)
    Z = ((Xs - mu) / sd)
    good = [c for c in Z.columns if Z[c].notna().all()]
    Z = Z[good]
    print(f"multivariate space: {len(good)} features "
          f"(dropped {len(feats) - len(good)} with nulls or zero variance)")

    centroids = Z[e].groupby(sub.loc[e, "subject"]).mean()
    Zt = Z[~e]
    yt = sub.loc[~e, "subject"].to_numpy()

    # ---- 2. own-centroid vs other-centroid distance ----------------------------
    D = np.linalg.norm(Zt.to_numpy()[:, None, :] - centroids.to_numpy()[None, :, :], axis=2)
    ids = centroids.index.to_numpy()
    own_idx = np.searchsorted(ids, yt)
    own = D[np.arange(len(yt)), own_idx]
    other = D.copy()
    other[np.arange(len(yt)), own_idx] = np.nan
    other_mean = np.nanmean(other, axis=1)

    closer = float((own < other_mean).mean())
    # Rank-based separability: P(own distance < a random other-user distance).
    auc = float((own[:, None] < other).mean())
    print("\n== 2. distance to own centroid vs others ==")
    print(f"own   : median {np.median(own):.3f}")
    print(f"others: median {np.nanmedian(other_mean):.3f}")
    print(f"gestures closer to own centroid than mean-other: {closer:.1%}  (chance 50%)")
    print(f"separability AUC: {auc:.3f}  (chance 0.500)")

    # ---- 3. nearest-centroid identification ------------------------------------
    pred = ids[np.argmin(D, axis=1)]
    acc = float((pred == yt).mean())
    rank = (D < own[:, None]).sum(axis=1) + 1
    top5 = float((rank <= 5).mean())
    chance = 1.0 / len(ids)
    print("\n== 3. nearest-centroid identification (single gesture) ==")
    print(f"top-1 accuracy: {acc:.1%}   (chance {chance:.1%}, {acc / chance:.1f}x)")
    print(f"top-5 accuracy: {top5:.1%}   (chance {5 * chance:.1%})")
    print(f"median rank of true user: {np.median(rank):.0f} of {len(ids)}")

    # ---- confound check --------------------------------------------------------
    post = sub.loc[~e].assign(correct=(pred == yt))
    if "posture" not in post:
        pass
    per_user = pd.Series((pred == yt), index=sub.loc[~e].index).groupby(sub.loc[~e, "subject"]).mean()
    print(f"\nper-subject accuracy: median {per_user.median():.1%} "
          f"| worst {per_user.min():.1%} | best {per_user.max():.1%}")

    summary = {
        "experiment": cfg["experiment"],
        "feature_version": cfg["feature_version"],
        "seed": cfg["seed"],
        "n_gestures": int(len(df)),
        "n_subjects_total": int(df.subject.nunique()),
        "n_subjects_evaluated": int(len(keep)),
        "n_features_multivariate": len(good),
        "icc_median": float(icc.median()),
        "icc_above_0.5": int((icc > .5).sum()),
        "icc_above_0.3": int((icc > .3).sum()),
        "icc_top5": icc.head(5).round(4).to_dict(),
        "closer_to_own_centroid": closer,
        "separability_auc": auc,
        "identification_top1": acc,
        "identification_top5": top5,
        "identification_chance": chance,
        "per_subject_accuracy_median": float(per_user.median()),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    per_user.rename("accuracy").to_csv(OUT / "per_subject_accuracy.csv")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

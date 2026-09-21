"""EXP-005a — H5.3: do H1 and H2 replicate on FETA?

This is the fully pre-specified part of EXP-005. It needs no behavioural contrast and
therefore carries no deviation from PREREGISTRATION.md.

H1 — are scroll kinematics individually distinctive? (EXP-001 method: ICC per feature,
     nearest-centroid identification on a contiguous split)
H2 — do personal baselines converge? (EXP-002 method: Spearman stability of held-out
     deviation scores against the full-baseline scores)

FETA differs from HMOG in ways that matter for interpretation: 138 users rather than 99,
~30 sessions each rather than 8, real pressure values (excluded anyway), and no orientation
field (deviation D1).

    python research/experiments/EXP-005_feta-replication/run_replication.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research"))
sys.path.insert(0, str(ROOT / "research/experiments/EXP-001_h1-individual-distinctiveness"))

from precog.baseline.engine import PersonalBaseline  # noqa: E402
from precog.deviation.score import score  # noqa: E402
from run import icc1  # noqa: E402

OUT = HERE / "outputs"
INPUT = ROOT / "data/processed/feta_gesture-features_features-v0.1.parquet"

# Fixed by pre-registration; not re-derived on FETA.
ENROL_GESTURES = 80
HOLDOUT = 40
GRID = [5, 10, 15, 20, 30, 40, 60, 80, 100, 150, 200]
STABILITY_TARGET = 0.95

LOG_TRANSFORM = ["duration_ms", "trajectory_length", "end_to_end_distance", "average_velocity",
                 "velocity_p20", "velocity_p50", "velocity_p80", "largest_deviation",
                 "deviation_p20", "deviation_p50", "deviation_p80", "inter_scroll_ms"]
# phone_orientation: constant in FETA (deviation D1). subject/session/ids are not features.
EXCLUDE = {"subject", "session", "t_start", "t_end", "feature_version", "phone_orientation"}


def main() -> int:
    if not INPUT.exists():
        print(f"missing {INPUT}\nrun scripts/extract_feta.py first")
        return 1
    OUT.mkdir(exist_ok=True)
    bcfg = yaml.safe_load((ROOT / "config/baseline.yaml").read_text())

    df = pd.read_parquet(INPUT).sort_values(["subject", "t_start"]).reset_index(drop=True)
    feats = [c for c in df.columns if c not in EXCLUDE]
    print(f"FETA: {len(df):,} gestures | {df.subject.nunique()} subjects | {len(feats)} features")
    print(f"sessions/subject: median {df.groupby('subject').session.nunique().median():.0f}\n")

    # ---------- H1a: ICC per feature ----------
    X = df[feats].copy()
    for c in LOG_TRANSFORM:
        if c in X:
            X[c] = np.log1p(X[c].clip(lower=0))
    g = df["subject"].to_numpy()
    icc = pd.Series({c: icc1(X[c].to_numpy(float), g) for c in feats}).sort_values(ascending=False)
    icc.to_csv(OUT / "icc_per_feature.csv")
    print("== H1a · ICC per feature (share of variance that is between-user) ==")
    print(icc.head(10).round(3).to_string())
    print(f"median ICC {icc.median():.3f} | >0.50: {(icc > .5).sum()} | "
          f">0.30: {(icc > .3).sum()} of {len(icc)}   [HMOG: median 0.161, 3 above 0.50]\n")

    # ---------- H1b: nearest-centroid identification (contiguous split) ----------
    rank = df.groupby("subject")["session"].rank(method="dense")
    enrol_m = (rank <= df.groupby("subject")["session"].transform("nunique") * 0.5)
    mu, sd = X[enrol_m].mean(), X[enrol_m].std().replace(0, np.nan)
    Z = (X - mu) / sd
    good = [c for c in Z.columns if Z[c].notna().all()]
    Z = Z[good]
    cen = Z[enrol_m].groupby(df.loc[enrol_m, "subject"]).mean()
    Zt, yt = Z[~enrol_m].to_numpy(), df.loc[~enrol_m, "subject"].to_numpy()
    ids = cen.index.to_numpy()

    D = np.linalg.norm(Zt[:, None, :] - cen.to_numpy()[None, :, :], axis=2)
    own_i = np.searchsorted(ids, yt)
    own = D[np.arange(len(yt)), own_i]
    other = D.copy()
    other[np.arange(len(yt)), own_i] = np.nan
    pred = ids[np.argmin(D, axis=1)]
    acc = float((pred == yt).mean())
    auc = float((own[:, None] < other).mean())
    closer = float((own < np.nanmean(other, axis=1)).mean())
    chance = 1 / len(ids)
    per_user = pd.Series(pred == yt, index=df.loc[~enrol_m].index).groupby(
        df.loc[~enrol_m, "subject"]).mean()
    per_user.rename("accuracy").to_csv(OUT / "per_subject_accuracy.csv")

    print(f"== H1b · single-gesture identification, {len(ids)} subjects ==")
    print(f"multivariate space: {len(good)} features")
    print(f"top-1 {acc:.1%}  (chance {chance:.1%}, {acc / chance:.1f}x)   [HMOG: 15.0%, 14.8x]")
    print(f"separability AUC {auc:.3f}   [HMOG: 0.787]")
    print(f"closer to own centroid {closer:.1%}   [HMOG: 88.5%]")
    print(f"per-subject accuracy: median {per_user.median():.1%} "
          f"worst {per_user.min():.1%} best {per_user.max():.1%}   [HMOG: 9.8% / 0% / 65.9%]\n")

    # ---------- H2: baseline convergence ----------
    counts = df.groupby("subject").size()
    eligible = counts[counts >= 20 + HOLDOUT].index
    rows = []
    for uid in eligible:
        gi = df[df.subject == uid]
        hold, enrol = gi.iloc[-HOLDOUT:], gi.iloc[:-HOLDOUT]
        full = PersonalBaseline(feats, bcfg).fit(enrol)
        s_full = score(hold[feats], full)["deviation_z"]
        for n in GRID:
            if n > len(enrol):
                break
            bn = PersonalBaseline(feats, bcfg).fit(enrol.iloc[:n])
            s_n = score(hold[feats], bn)["deviation_z"]
            ok = s_n.notna() & s_full.notna()
            rho = spearmanr(s_n[ok], s_full[ok]).statistic if ok.sum() > 5 else np.nan
            rows.append({"subject": uid, "n": n, "spearman": rho})
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "convergence.csv", index=False)
    agg = res.groupby("n").agg(subjects=("subject", "nunique"),
                               median=("spearman", "median"),
                               p25=("spearman", lambda s: s.quantile(.25))).round(3)
    print("== H2 · baseline convergence ==")
    print(agg.to_string())
    hit = agg["median"][agg["median"] >= STABILITY_TARGET]
    hit25 = agg["p25"][agg["p25"] >= STABILITY_TARGET]
    n_star = int(hit.index[0]) if len(hit) else None
    n_star25 = int(hit25.index[0]) if len(hit25) else None
    print(f"\nmedian subject reaches rho >= {STABILITY_TARGET} at n = {n_star}   [HMOG: 80]")
    print(f"75% of subjects by n = {n_star25}   [HMOG: 150]")

    (OUT / "summary_replication.json").write_text(json.dumps({
        "experiment": "EXP-005a", "dataset": "FETA",
        "n_gestures": int(len(df)), "n_subjects": int(df.subject.nunique()),
        "n_features": len(feats), "n_features_multivariate": len(good),
        "icc_median": float(icc.median()),
        "icc_above_0.5": int((icc > .5).sum()), "icc_above_0.3": int((icc > .3).sum()),
        "identification_top1": acc, "identification_chance": chance,
        "separability_auc": auc, "closer_to_own_centroid": closer,
        "per_subject_accuracy_median": float(per_user.median()),
        "per_subject_accuracy_min": float(per_user.min()),
        "per_subject_accuracy_max": float(per_user.max()),
        "convergence_n_star_median": n_star, "convergence_n_star_p25": n_star25,
        "hmog_reference": {"icc_median": 0.161, "top1": 0.150, "auc": 0.787,
                           "n_star": 80, "per_subject_median": 0.098},
    }, indent=2))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

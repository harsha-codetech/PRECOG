"""EXP-002 — H2: how many gestures does a personal baseline need?

Builds each subject's baseline from their first n gestures (temporal order, never random)
and asks when the deviation scores it produces on held-out gestures stop changing. The
answer sets `min_samples` in the baseline config and settles the 7-vs-14-day question in
SPEC.md §10 with evidence rather than a guess.

Two convergence measures:
  1. Score stability  — Spearman correlation between scores from baseline(n) and
     baseline(full) on the same held-out gestures. This is what actually matters: a
     baseline is converged when it stops changing its mind.
  2. Centroid drift   — how far the baseline's median vector still moves, in MAD units.

    python research/experiments/EXP-002_h2-baseline-convergence/run.py
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

from precog.baseline.engine import PersonalBaseline  # noqa: E402
from precog.deviation.score import score  # noqa: E402

OUT = HERE / "outputs"
GRID = [5, 10, 15, 20, 30, 40, 60, 80, 100, 150, 200]
HOLDOUT = 40
STABILITY_TARGET = 0.95


def load() -> tuple[pd.DataFrame, list[str], dict]:
    bcfg = yaml.safe_load((ROOT / "config/baseline.yaml").read_text())
    df = pd.read_parquet(ROOT / "data/processed/hmog_gesture-features_features-v0.1.parquet")
    sess = pd.read_parquet(ROOT / "data/interim/hmog/sessions.parquet")
    post = sess[["ActivityID", "posture"]].drop_duplicates("ActivityID")
    df = df.merge(post, on="ActivityID", how="left")
    drop = {"subject", "session", "ActivityID", "ScrollID", "t_start", "t_end",
            "feature_version", "posture"}
    feats = [c for c in df.columns if c not in drop]
    return df.sort_values(["subject", "t_start"]).reset_index(drop=True), feats, bcfg


def main() -> int:
    OUT.mkdir(exist_ok=True)
    df, feats, bcfg = load()
    print(f"loaded {len(df):,} gestures | {df.subject.nunique()} subjects | {len(feats)} features")

    counts = df.groupby("subject").size()
    eligible = counts[counts >= GRID[3] + HOLDOUT].index
    print(f"eligible (>= {GRID[3] + HOLDOUT} gestures): {len(eligible)} subjects\n")

    rows = []
    for uid in eligible:
        g = df[df.subject == uid]
        hold, enrol = g.iloc[-HOLDOUT:], g.iloc[:-HOLDOUT]
        full = PersonalBaseline(feats, bcfg).fit(enrol)
        s_full = score(hold[feats], full)["deviation_z"]

        for n in GRID:
            if n > len(enrol):
                break
            bn = PersonalBaseline(feats, bcfg).fit(enrol.iloc[:n])
            s_n = score(hold[feats], bn)["deviation_z"]
            ok = s_n.notna() & s_full.notna()
            rho = spearmanr(s_n[ok], s_full[ok]).statistic if ok.sum() > 5 else np.nan
            drift = float(np.nanmean(np.abs(
                bn.global_["median"].to_numpy() - full.global_["median"].to_numpy()
            ) / (full.global_["mad"].to_numpy() + 1e-9)))
            rows.append({"subject": uid, "n": n, "spearman": rho, "drift_mad": drift,
                         "n_enrol": len(enrol)})

    res = pd.DataFrame(rows)
    res.to_csv(OUT / "convergence_per_subject.csv", index=False)

    agg = res.groupby("n").agg(
        subjects=("subject", "nunique"),
        spearman_median=("spearman", "median"),
        spearman_p25=("spearman", lambda s: s.quantile(.25)),
        drift_median=("drift_mad", "median"),
    ).round(3)
    print("== convergence toward the full baseline ==")
    print(agg.to_string())

    med, p25 = agg["spearman_median"], agg["spearman_p25"]
    hit = med[med >= STABILITY_TARGET]
    hit25 = p25[p25 >= STABILITY_TARGET]
    n_star = int(hit.index[0]) if len(hit) else None
    n_star25 = int(hit25.index[0]) if len(hit25) else None

    print(f"\nmedian subject reaches rho >= {STABILITY_TARGET} at n = {n_star} gestures")
    if n_star25:
        print(f"75% of subjects reach it by n = {n_star25} gestures")
    else:
        print(f"the 25th-percentile subject never reaches {STABILITY_TARGET} within this grid")

    per_sess = df.groupby(["subject", "session"]).size()
    rate = float(per_sess.median())
    print(f"\nobserved: median {rate:.0f} gestures per reading session")
    if n_star:
        print(f"  n={n_star} ~ {n_star / rate:.1f} sessions")
    if n_star25:
        print(f"  n={n_star25} ~ {n_star25 / rate:.1f} sessions")

    summary = {
        "experiment": "EXP-002",
        "baseline_version": bcfg["baseline_version"],
        "feature_version": "features-v0.1",
        "holdout_gestures": HOLDOUT,
        "stability_target": STABILITY_TARGET,
        "n_subjects": int(len(eligible)),
        "n_star_median_subject": n_star,
        "n_star_p25_subject": n_star25,
        "gestures_per_session_median": rate,
        "curve": agg.reset_index().to_dict("records"),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

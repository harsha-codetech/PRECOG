"""EXP-003 — H3: personalized baseline vs global threshold.

The central claim. At matched sensitivity, does comparing a person against their own
normal produce fewer false alarms than comparing them against the population?

Design. No dataset carries compulsive-use labels, so anomalies are injected into real
held-out gestures: negatives are genuine untouched gestures, positives are real gestures
with a controlled behavioural shift applied. The shift is scaled by the POPULATION MAD so
the same physical change is applied to every subject — scaling by personal spread would
define the anomaly in personalized terms and rig the result.

Semi-synthetic by necessity. This tests the detector, not the clinical reality of
compulsive scrolling, and is reported as such.

    python research/experiments/EXP-003_h3-personalized-vs-global/run.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.stats import wilcoxon

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research"))

from precog.baseline.engine import PersonalBaseline  # noqa: E402
from precog.deviation.score import score  # noqa: E402

OUT = HERE / "outputs"


def fpr_at_sensitivity(scores: np.ndarray, labels: np.ndarray, target: float) -> float:
    """False-positive rate at the threshold that first achieves `target` sensitivity."""
    pos, neg = scores[labels == 1], scores[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return np.nan
    thr = np.quantile(pos, 1 - target)  # threshold catching `target` of positives
    return float((neg >= thr).mean())


def cliffs_delta(a: np.ndarray, b: np.ndarray) -> float:
    """Non-parametric effect size in [-1, 1]. Negative = a tends below b."""
    gt = sum((x > y) for x in a for y in b)
    lt = sum((x < y) for x in a for y in b)
    return (gt - lt) / (len(a) * len(b))


def main() -> int:
    cfg = yaml.safe_load((HERE / "config.yaml").read_text())
    bcfg = yaml.safe_load((ROOT / "config/baseline.yaml").read_text())
    rng = np.random.default_rng(cfg["seed"])
    OUT.mkdir(exist_ok=True)

    df = pd.read_parquet(ROOT / cfg["input"])
    drop = {"subject", "session", "ActivityID", "ScrollID", "t_start", "t_end", "feature_version"}
    feats = [c for c in df.columns if c not in drop]
    df = df.sort_values(["subject", "t_start"]).reset_index(drop=True)
    print(f"loaded {len(df):,} gestures | {df.subject.nunique()} subjects | {len(feats)} features")

    sp, ev, pb = cfg["split"], cfg["evaluation"], cfg["perturbation"]
    counts = df.groupby("subject").size()
    keep = counts[counts >= sp["enrol_gestures"] + sp["min_holdout"]].index
    print(f"eligible (>= {sp['enrol_gestures'] + sp['min_holdout']} gestures): {len(keep)} subjects")

    enrol = df[df.subject.isin(keep)].groupby("subject").head(sp["enrol_gestures"])
    hold = df[df.subject.isin(keep)].groupby("subject").tail(-sp["enrol_gestures"])

    # Population MAD sets the perturbation scale; population baseline is the global arm.
    pop_mad = (enrol[feats] - enrol[feats].median()).abs().median()
    global_baseline = PersonalBaseline(feats, bcfg).fit(enrol)
    print(f"global baseline fitted on {len(enrol):,} enrolment gestures from all subjects\n")

    rows = []
    for sev in pb["severities"]:
        for uid in keep:
            h = hold[hold.subject == uid]
            if len(h) < sp["min_holdout"]:
                continue
            n_pos = int(len(h) * pb["positive_fraction"])
            idx = rng.permutation(len(h))
            labels = np.zeros(len(h), int)
            labels[idx[:n_pos]] = 1

            X = h[feats].copy().reset_index(drop=True)
            for f, d in pb["direction"].items():
                if f in X.columns and np.isfinite(pop_mad.get(f, np.nan)):
                    X.loc[labels == 1, f] = X.loc[labels == 1, f] + sev * d * pop_mad[f]

            personal = PersonalBaseline(feats, bcfg).fit(enrol[enrol.subject == uid])
            s_p = score(X, personal)["deviation"].to_numpy()
            s_g = score(X, global_baseline)["deviation"].to_numpy()

            rows.append({
                "severity": sev, "subject": uid, "n": len(h),
                "fpr_personal": fpr_at_sensitivity(s_p, labels, ev["target_sensitivity"]),
                "fpr_global": fpr_at_sensitivity(s_g, labels, ev["target_sensitivity"]),
            })

    res = pd.DataFrame(rows).dropna()
    res["delta"] = res["fpr_personal"] - res["fpr_global"]
    res.to_csv(OUT / "fpr_per_subject.csv", index=False)

    print(f"== FPR at {ev['target_sensitivity']:.0%} sensitivity (lower is better) ==")
    print(f"{'sev':>5} {'n':>4} {'personal':>9} {'global':>8} {'delta':>8} "
          f"{'wins':>6} {'p':>10} {'cliffs d':>9}")
    summary = []
    for sev, g in res.groupby("severity"):
        if len(g) < ev["min_subjects"]:
            continue
        p = wilcoxon(g.fpr_personal, g.fpr_global).pvalue if g.delta.abs().sum() > 0 else 1.0
        d = cliffs_delta(g.fpr_personal.to_numpy(), g.fpr_global.to_numpy())
        wins = float((g.delta < 0).mean())
        print(f"{sev:>5} {len(g):>4} {g.fpr_personal.median():>9.3f} "
              f"{g.fpr_global.median():>8.3f} {g.delta.median():>8.3f} "
              f"{wins:>5.0%} {p:>10.2e} {d:>9.3f}")
        summary.append({
            "severity": float(sev), "n_subjects": int(len(g)),
            "fpr_personal_median": float(g.fpr_personal.median()),
            "fpr_global_median": float(g.fpr_global.median()),
            "delta_median": float(g.delta.median()),
            "subjects_personal_better": wins,
            "wilcoxon_p": float(p), "cliffs_delta": float(d),
        })

    out = {
        "experiment": cfg["experiment"],
        "design": "semi-synthetic: real negatives, injected positives (population-MAD scaled)",
        "feature_version": cfg["feature_version"],
        "baseline_version": bcfg["baseline_version"],
        "seed": cfg["seed"],
        "target_sensitivity": ev["target_sensitivity"],
        "n_subjects": int(res.subject.nunique()),
        "by_severity": summary,
    }
    (OUT / "summary.json").write_text(json.dumps(out, indent=2))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

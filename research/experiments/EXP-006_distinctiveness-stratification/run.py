"""EXP-006 — does personalization help the people who actually have a signature?

EXP-003 found no personalization benefit on average (C-B = 0.000, p=0.33). But EXP-001
showed the population splits sharply: per-subject identification accuracy ranged 0% to
65.9%. A quarter of subjects have essentially no stable scroll signature, and for them a
personal baseline cannot possibly beat a global one.

So the average may be hiding a real effect. This asks whether the personalization advantage
concentrates in the distinctive subjects.

Design mirrors EXP-003 arm 2 exactly — the only valid arm — using the real sit->walk
behavioural change with ground-truth labels, then stratifies by distinctiveness measured
independently in EXP-001.

    python research/experiments/EXP-006_distinctiveness-stratification/run.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.stats import spearmanr, wilcoxon

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research"))
sys.path.insert(0, str(ROOT / "research/experiments/EXP-003_h3-personalized-vs-global"))

from precog.baseline.engine import PersonalBaseline  # noqa: E402
from precog.deviation.score import score  # noqa: E402
from run import cliffs_delta, fpr_at_sensitivity  # noqa: E402

OUT = HERE / "outputs"
ENROL = 80
MIN_WALK = 20
SENSITIVITY = 0.80


def main() -> int:
    OUT.mkdir(exist_ok=True)
    bcfg = yaml.safe_load((ROOT / "config/baseline.yaml").read_text())

    df = pd.read_parquet(ROOT / "data/processed/hmog_gesture-features_features-v0.1.parquet")
    sess = pd.read_parquet(ROOT / "data/interim/hmog/sessions.parquet")
    df = df.merge(sess[["ActivityID", "posture"]].drop_duplicates("ActivityID"),
                  on="ActivityID", how="left")
    drop = {"subject", "session", "ActivityID", "ScrollID", "t_start", "t_end",
            "feature_version", "posture"}
    feats = [c for c in df.columns if c not in drop]
    df = df.sort_values(["subject", "t_start"]).reset_index(drop=True)

    dist = pd.read_csv(
        ROOT / "research/experiments/EXP-001_h1-individual-distinctiveness"
             / "outputs/per_subject_accuracy.csv"
    ).set_index("subject")["accuracy"]

    sit, walk = df[df.posture == "sit"], df[df.posture == "walk"]
    ns, nw = sit.groupby("subject").size(), walk.groupby("subject").size()
    keep = [u for u in ns.index
            if ns.get(u, 0) >= ENROL + 30 and nw.get(u, 0) >= MIN_WALK and u in dist.index]
    print(f"{len(keep)} subjects with enough sitting + walking data and a distinctiveness score")

    enrol = sit[sit.subject.isin(keep)].groupby("subject").head(ENROL)
    global_baseline = PersonalBaseline(feats, bcfg).fit(enrol)

    rows = []
    for uid in keep:
        neg = sit[sit.subject == uid].iloc[ENROL:]
        pos = walk[walk.subject == uid]
        X = pd.concat([neg[feats], pos[feats]]).reset_index(drop=True)
        lab = np.r_[np.zeros(len(neg), int), np.ones(len(pos), int)]
        personal = PersonalBaseline(feats, bcfg).fit(enrol[enrol.subject == uid])
        rows.append({
            "subject": uid,
            "distinctiveness": float(dist.loc[uid]),
            "fpr_personal": fpr_at_sensitivity(score(X, personal)["deviation"].to_numpy(),
                                               lab, SENSITIVITY),
            "fpr_global": fpr_at_sensitivity(score(X, global_baseline)["deviation"].to_numpy(),
                                             lab, SENSITIVITY),
        })

    r = pd.DataFrame(rows).dropna()
    r["delta"] = r.fpr_personal - r.fpr_global          # negative = personalization wins
    r.to_csv(OUT / "stratified.csv", index=False)

    rho, p_rho = spearmanr(r.distinctiveness, r.delta)
    print(f"\n== does the advantage scale with distinctiveness? ==")
    print(f"Spearman(distinctiveness, C-B) = {rho:+.3f}   p = {p_rho:.3f}")
    print("  (negative rho would mean: more distinctive -> personalization helps more)")

    r["quartile"] = pd.qcut(r.distinctiveness, 4,
                            labels=["Q1 lowest", "Q2", "Q3", "Q4 highest"])
    print(f"\n== FPR at {SENSITIVITY:.0%} sensitivity, by distinctiveness quartile ==")
    print(f"{'quartile':<12}{'n':>4}{'distinct':>10}{'personal':>10}{'global':>9}"
          f"{'C-B':>8}{'p':>9}{'wins':>7}")
    strata = []
    for q, g in r.groupby("quartile", observed=True):
        p = wilcoxon(g.fpr_personal, g.fpr_global).pvalue if g.delta.abs().sum() > 0 else 1.0
        print(f"{str(q):<12}{len(g):>4}{g.distinctiveness.median():>10.3f}"
              f"{g.fpr_personal.median():>10.3f}{g.fpr_global.median():>9.3f}"
              f"{g.delta.median():>+8.3f}{p:>9.3f}{(g.delta < 0).mean():>6.0%}")
        strata.append({
            "quartile": str(q), "n": int(len(g)),
            "distinctiveness_median": float(g.distinctiveness.median()),
            "fpr_personal_median": float(g.fpr_personal.median()),
            "fpr_global_median": float(g.fpr_global.median()),
            "delta_median": float(g.delta.median()),
            "wilcoxon_p": float(p),
            "subjects_personal_better": float((g.delta < 0).mean()),
            "cliffs_delta": float(cliffs_delta(g.fpr_personal.to_numpy(),
                                               g.fpr_global.to_numpy())),
        })

    top = r[r.quartile == "Q4 highest"]
    print(f"\ntop quartile only (n={len(top)}, distinctiveness >= "
          f"{top.distinctiveness.min():.3f}):")
    print(f"  personalized {top.fpr_personal.median():.3f} vs global "
          f"{top.fpr_global.median():.3f}  ->  {top.delta.median():+.3f}")

    (OUT / "summary.json").write_text(json.dumps({
        "experiment": "EXP-006",
        "design": "real sit->walk change, stratified by EXP-001 distinctiveness",
        "n_subjects": int(len(r)),
        "target_sensitivity": SENSITIVITY,
        "spearman_distinctiveness_vs_delta": float(rho),
        "spearman_p": float(p_rho),
        "by_quartile": strata,
    }, indent=2))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

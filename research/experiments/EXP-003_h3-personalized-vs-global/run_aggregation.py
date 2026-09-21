"""EXP-003b — does aggregation make the detector usable?

run.py showed personalization wins at every severity, but with absolute FPRs of 0.60-0.81
at 80% sensitivity. A single gesture carries too little signal to alert on — consistent
with EXP-001, where single-gesture identification reached only 15%.

PRECOG does not alert per gesture; it scores a window. So this sweeps window size k and
asks where the detector becomes usable, and whether the personalization advantage survives
aggregation or washes out.

FETA pitfall P5 requires reporting single-gesture performance alongside any aggregated
figure, so both are kept.

    python research/experiments/EXP-003_h3-personalized-vs-global/run_aggregation.py
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
from run import cliffs_delta, fpr_at_sensitivity  # noqa: E402

OUT = HERE / "outputs"
WINDOWS = [1, 3, 5, 10, 20]
SEVERITY = 1.5


def windowed(values: np.ndarray, labels: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """Mean deviation over non-overlapping windows of k gestures.

    A window is labelled positive only if every gesture in it is positive, so mixed
    windows are discarded rather than diluting either class.
    """
    n = (len(values) // k) * k
    if n == 0:
        return np.array([]), np.array([])
    v = values[:n].reshape(-1, k).mean(axis=1)
    lab = labels[:n].reshape(-1, k)
    pure = (lab.mean(axis=1) == 0) | (lab.mean(axis=1) == 1)
    return v[pure], lab.mean(axis=1)[pure].astype(int)


def main() -> int:
    cfg = yaml.safe_load((HERE / "config.yaml").read_text())
    bcfg = yaml.safe_load((ROOT / "config/baseline.yaml").read_text())
    rng = np.random.default_rng(cfg["seed"])
    OUT.mkdir(exist_ok=True)

    df = pd.read_parquet(ROOT / cfg["input"])
    drop = {"subject", "session", "ActivityID", "ScrollID", "t_start", "t_end", "feature_version"}
    feats = [c for c in df.columns if c not in drop]
    df = df.sort_values(["subject", "t_start"]).reset_index(drop=True)

    sp, ev, pb = cfg["split"], cfg["evaluation"], cfg["perturbation"]
    counts = df.groupby("subject").size()
    keep = counts[counts >= sp["enrol_gestures"] + sp["min_holdout"]].index
    enrol = df[df.subject.isin(keep)].groupby("subject").head(sp["enrol_gestures"])
    hold = df[df.subject.isin(keep)].groupby("subject").tail(-sp["enrol_gestures"])

    pop_mad = (enrol[feats] - enrol[feats].median()).abs().median()
    global_baseline = PersonalBaseline(feats, bcfg).fit(enrol)
    print(f"{len(keep)} subjects | severity {SEVERITY} | sensitivity {ev['target_sensitivity']:.0%}\n")

    rows = []
    for uid in keep:
        h = hold[hold.subject == uid]
        if len(h) < sp["min_holdout"]:
            continue
        # Positives arrive in a contiguous run, as a real behavioural episode would —
        # not scattered at random. This is what makes windowing meaningful.
        n_pos = int(len(h) * pb["positive_fraction"])
        start = rng.integers(0, max(1, len(h) - n_pos))
        labels = np.zeros(len(h), int)
        labels[start:start + n_pos] = 1

        X = h[feats].copy().reset_index(drop=True)
        for f, d in pb["direction"].items():
            if f in X.columns and np.isfinite(pop_mad.get(f, np.nan)):
                X.loc[labels == 1, f] = X.loc[labels == 1, f] + SEVERITY * d * pop_mad[f]

        personal = PersonalBaseline(feats, bcfg).fit(enrol[enrol.subject == uid])
        s_p = score(X, personal)["deviation"].to_numpy()
        s_g = score(X, global_baseline)["deviation"].to_numpy()

        for k in WINDOWS:
            vp, lp = windowed(s_p, labels, k)
            vg, lg = windowed(s_g, labels, k)
            if len(set(lp)) < 2 or len(set(lg)) < 2:
                continue
            rows.append({
                "k": k, "subject": uid, "n_windows": len(vp),
                "fpr_personal": fpr_at_sensitivity(vp, lp, ev["target_sensitivity"]),
                "fpr_global": fpr_at_sensitivity(vg, lg, ev["target_sensitivity"]),
            })

    res = pd.DataFrame(rows).dropna()
    res["delta"] = res.fpr_personal - res.fpr_global
    res.to_csv(OUT / "fpr_by_window.csv", index=False)

    print("== FPR at matched sensitivity, by window size ==")
    print(f"{'k':>3} {'subj':>5} {'personal':>9} {'global':>8} {'delta':>8} "
          f"{'wins':>6} {'p':>10} {'cliffs d':>9}")
    summary = []
    for k, g in res.groupby("k"):
        if len(g) < ev["min_subjects"]:
            continue
        p = wilcoxon(g.fpr_personal, g.fpr_global).pvalue if g.delta.abs().sum() > 0 else 1.0
        d = cliffs_delta(g.fpr_personal.to_numpy(), g.fpr_global.to_numpy())
        print(f"{k:>3} {len(g):>5} {g.fpr_personal.median():>9.3f} {g.fpr_global.median():>8.3f} "
              f"{g.delta.median():>8.3f} {(g.delta < 0).mean():>5.0%} {p:>10.2e} {d:>9.3f}")
        summary.append({
            "window": int(k), "n_subjects": int(len(g)),
            "fpr_personal_median": float(g.fpr_personal.median()),
            "fpr_global_median": float(g.fpr_global.median()),
            "delta_median": float(g.delta.median()),
            "subjects_personal_better": float((g.delta < 0).mean()),
            "wilcoxon_p": float(p), "cliffs_delta": float(d),
        })

    (OUT / "summary_aggregation.json").write_text(json.dumps({
        "experiment": "EXP-003b", "severity": SEVERITY,
        "target_sensitivity": ev["target_sensitivity"],
        "positives": "contiguous run", "by_window": summary,
    }, indent=2))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

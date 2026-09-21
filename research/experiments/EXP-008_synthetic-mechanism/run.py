"""EXP-008 — does the EXP-003 explanation hold?

EXP-003 found personalization gave no benefit on sit->walk and proposed a reason: walking
changes behaviour in a POPULATION-CONSISTENT way, so a global model already captures it and
a personal baseline has nothing to add. That was an inference from a null, which is weak.

A generator can test it directly. Two anomaly types, identical except for what scales them:

    population_consistent : the same physical shift for every user      (tau-scaled)
    person_relative       : a shift scaled to each user's own spread    (sigma-scaled)

PREDICTION — personalization should help for person_relative and not for
population_consistent. If that holds, EXP-003's explanation is confirmed rather than assumed.

Synthetic results are NOT evidence that PRECOG works on people. They test a mechanism.

    python research/experiments/EXP-008_synthetic-mechanism/run.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.stats import wilcoxon
from sklearn.metrics import average_precision_score
from sklearn.model_selection import GroupKFold

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research"))
sys.path.insert(0, str(ROOT / "research/experiments/EXP-003_h3-personalized-vs-global"))

from precog.baseline.engine import PersonalBaseline  # noqa: E402
from precog.deviation.score import score  # noqa: E402
from precog.synthetic.generator import PopulationModel, enforce, generate, inject  # noqa: E402
from run import cliffs_delta, fpr_at_sensitivity  # noqa: E402

OUT = HERE / "outputs"
ENROL = 80
SENS = 0.80
DROP = {"subject", "session", "t_start", "t_end", "feature_version", "phone_orientation",
        "context", "day", "is_anomalous_session", "y"}


def evaluate(df: pd.DataFrame, feats: list[str], bcfg: dict) -> pd.DataFrame:
    """A / B / C arms on one injected dataset, per subject."""
    df = df.sort_values(["subject", "t_start"]).reset_index(drop=True)
    enrol = df[df.y == 0].groupby("subject").head(ENROL)
    gb = PersonalBaseline(feats, bcfg).fit(enrol)
    rows = []
    for uid, g in df.groupby("subject"):
        idx = set(enrol[enrol.subject == uid].index)
        test = g[~g.index.isin(idx)]
        if test.y.nunique() < 2 or len(test) < 40:
            continue
        lab = test.y.to_numpy()
        pbl = PersonalBaseline(feats, bcfg).fit(enrol[enrol.subject == uid])
        rows.append({
            "subject": uid,
            "A": fpr_at_sensitivity(test["average_velocity"].to_numpy(), lab, SENS),
            "B": fpr_at_sensitivity(score(test[feats], gb)["deviation"].to_numpy(), lab, SENS),
            "C": fpr_at_sensitivity(score(test[feats], pbl)["deviation"].to_numpy(), lab, SENS),
        })
    return pd.DataFrame(rows).dropna()


def main() -> int:
    OUT.mkdir(exist_ok=True)
    cfg = yaml.safe_load((ROOT / "config/synthetic.yaml").read_text())
    bcfg = yaml.safe_load((ROOT / "config/baseline.yaml").read_text())
    rng = np.random.default_rng(cfg["seed"])

    real = pd.read_parquet(ROOT / cfg["fit_from"])
    feats = [c for c in real.columns if c not in DROP]
    pop = PopulationModel(real, feats)
    print(f"population fitted from {cfg['fit_from']}")
    print(f"  {len(real):,} real gestures · {real.subject.nunique()} subjects · {len(feats)} features\n")

    base = generate(pop, cfg, rng)
    print(f"generated: {len(base):,} gestures · {base.subject.nunique()} users · "
          f"{base.session.nunique()} sessions each · {cfg['population']['days_span']} days")
    print(f"anomalous sessions: {base.is_anomalous_session.mean():.1%} of all sessions\n")

    results = []
    print("== FPR at 80% sensitivity (lower is better) · A fixed / B global / C personalized ==")
    print(f"{'anomaly type':<24}{'mag':>5}{'A':>8}{'B':>8}{'C':>8}{'C-B':>9}{'p':>10}{'cliffs_d':>10}")
    for kind in cfg["anomaly"]["types"]:
        for mag in cfg["anomaly"]["magnitudes"]:
            inj = enforce(inject(base, pop, cfg, kind, mag), cfg)
            r = evaluate(inj, feats, bcfg)
            if len(r) < 30:
                continue
            d = r.C - r.B
            p = wilcoxon(r.C, r.B).pvalue if d.abs().sum() > 0 else 1.0
            cd = cliffs_delta(r.C.to_numpy(), r.B.to_numpy())
            print(f"{kind:<24}{mag:>5}{r.A.median():>8.3f}{r.B.median():>8.3f}"
                  f"{r.C.median():>8.3f}{d.median():>+9.3f}{p:>10.2e}{cd:>+10.3f}")
            results.append({
                "anomaly_type": kind, "magnitude": float(mag), "n_subjects": int(len(r)),
                "fpr_A": float(r.A.median()), "fpr_B": float(r.B.median()),
                "fpr_C": float(r.C.median()),
                "C_minus_B": float(d.median()), "wilcoxon_p": float(p), "cliffs_delta": float(cd),
                "C_better_pct": float((d < 0).mean()),
            })

    # ---- XGBoost sanity arm: can a trained model separate the injected classes at all? ----
    print("\n== XGBoost (subject-wise 5-fold), magnitude 1.5 ==")
    from xgboost import XGBClassifier
    xgb_rows = []
    for kind in cfg["anomaly"]["types"]:
        inj = enforce(inject(base, pop, cfg, kind, 1.5), cfg)
        X, y, g = inj[feats].to_numpy(), inj.y.to_numpy(), inj.subject.to_numpy()
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        scores = []
        for tr, te in GroupKFold(n_splits=5).split(X, y, g):
            m = XGBClassifier(n_estimators=250, max_depth=4, learning_rate=0.08,
                              subsample=0.8, colsample_bytree=0.8, eval_metric="aucpr",
                              tree_method="hist", n_jobs=-1, random_state=cfg["seed"])
            m.fit(X[tr], y[tr], verbose=False)
            scores.append(average_precision_score(y[te], m.predict_proba(X[te])[:, 1]))
        print(f"  {kind:<24} PR-AUC {np.mean(scores):.3f} ± {np.std(scores):.3f}   "
              f"(prevalence {y.mean():.3f})")
        xgb_rows.append({"anomaly_type": kind, "prauc": float(np.mean(scores)),
                         "prauc_sd": float(np.std(scores)), "prevalence": float(y.mean())})

    pd.DataFrame(results).to_csv(OUT / "mechanism.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps({
        "experiment": "EXP-008", "status": "MECHANISM TEST — synthetic, not evidence",
        "synthetic_version": cfg["synthetic_version"], "seed": cfg["seed"],
        "fitted_from": cfg["fit_from"],
        "n_users": cfg["population"]["n_users"],
        "deviation_arms": results, "xgboost": xgb_rows,
    }, indent=2))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

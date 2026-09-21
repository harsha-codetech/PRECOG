"""EXP-005b — is the H2 failure caused by temporal drift?

EXP-005a found FETA baselines never reach rho >= 0.95 where HMOG reached it at n = 80.
The proposed explanation was the observation window: FETA spans 31 days, HMOG spans a few.
That was an inference. This measures it.

Two tests:

  A · Window-matched convergence — restrict FETA to each user's first 8 sessions, matching
      HMOG's span, and re-run the EXP-002 curve. If convergence then resembles HMOG's, the
      window is the cause rather than anything intrinsic to FETA.

  B · Deviation vs elapsed time — enrol on a user's first 80 gestures, then score their
      later gestures binned by days since enrolment ended. A baseline that stays valid
      produces a flat line; drift produces a rising one.

    python research/experiments/EXP-005_feta-replication/run_drift.py
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
INPUT = ROOT / "data/processed/feta_gesture-features_features-v0.1.parquet"
EXCLUDE = {"subject", "session", "t_start", "t_end", "feature_version", "phone_orientation"}
GRID = [5, 10, 15, 20, 30, 40, 60, 80, 100, 150, 200]
HOLDOUT = 40
ENROL = 80
HMOG_SESSIONS = 8
DAY_BINS = [0, 1, 3, 7, 14, 21, 32]


def convergence(df: pd.DataFrame, feats: list[str], bcfg: dict) -> pd.DataFrame:
    rows = []
    for uid, g in df.groupby("subject"):
        if len(g) < 20 + HOLDOUT:
            continue
        hold, enrol = g.iloc[-HOLDOUT:], g.iloc[:-HOLDOUT]
        full = PersonalBaseline(feats, bcfg).fit(enrol)
        s_full = score(hold[feats], full)["deviation_z"]
        for n in GRID:
            if n > len(enrol):
                break
            bn = PersonalBaseline(feats, bcfg).fit(enrol.iloc[:n])
            s_n = score(hold[feats], bn)["deviation_z"]
            ok = s_n.notna() & s_full.notna()
            rows.append({"subject": uid, "n": n,
                         "spearman": spearmanr(s_n[ok], s_full[ok]).statistic
                         if ok.sum() > 5 else np.nan})
    return pd.DataFrame(rows)


def main() -> int:
    OUT.mkdir(exist_ok=True)
    bcfg = yaml.safe_load((ROOT / "config/baseline.yaml").read_text())
    df = pd.read_parquet(INPUT).sort_values(["subject", "t_start"]).reset_index(drop=True)
    feats = [c for c in df.columns if c not in EXCLUDE]
    print(f"FETA: {len(df):,} gestures | {df.subject.nunique()} subjects\n")

    span = df.groupby("subject").t_start.agg(lambda s: (s.max() - s.min()) / 86400000)
    print(f"observation span per subject: median {span.median():.1f} days "
          f"(p25 {span.quantile(.25):.1f}, p75 {span.quantile(.75):.1f})")
    print(f"HMOG reference span: ~8 sessions over a few days\n")

    # ---------- A · window-matched ----------
    rank = df.groupby("subject")["session"].rank(method="dense")
    matched = df[rank <= HMOG_SESSIONS]
    print(f"== A · window-matched to HMOG (first {HMOG_SESSIONS} sessions) ==")
    ms = matched.groupby("subject").t_start.agg(lambda s: (s.max() - s.min()) / 86400000)
    print(f"matched span: median {ms.median():.1f} days | "
          f"{matched.subject.nunique()} subjects | {len(matched):,} gestures")

    full_curve = convergence(df, feats, bcfg).groupby("n").spearman.median()
    match_curve = convergence(matched, feats, bcfg).groupby("n").spearman.median()
    comp = pd.DataFrame({"full_31d": full_curve.round(3),
                         "matched_8sess": match_curve.round(3)})
    comp["delta"] = (comp.matched_8sess - comp.full_31d).round(3)
    print(comp.to_string())

    def first_at(c, t=0.95):
        hit = c[c >= t]
        return int(hit.index[0]) if len(hit) else None
    n_full, n_match = first_at(full_curve), first_at(match_curve)
    print(f"\nrho >= 0.95 reached at:  full-span n = {n_full}   window-matched n = {n_match}"
          f"   [HMOG: 80]")

    # ---------- B · deviation vs elapsed days ----------
    print(f"\n== B · deviation vs days since enrolment (enrol = first {ENROL} gestures) ==")
    rows = []
    for uid, g in df.groupby("subject"):
        if len(g) < ENROL + 40:
            continue
        enrol, later = g.iloc[:ENROL], g.iloc[ENROL:]
        b = PersonalBaseline(feats, bcfg).fit(enrol)
        t0 = enrol.t_start.max()
        d = score(later[feats], b)["deviation"]
        days = (later.t_start.to_numpy() - t0) / 86400000
        rows.append(pd.DataFrame({"subject": uid, "days": days, "dev": d.to_numpy()}))
    later = pd.concat(rows, ignore_index=True).dropna()
    later["bin"] = pd.cut(later.days, DAY_BINS, right=False)

    agg = later.groupby("bin", observed=True).agg(
        gestures=("dev", "size"), subjects=("subject", "nunique"),
        dev_median=("dev", "median")).round(3)
    base = agg.dev_median.iloc[0]
    agg["vs_first_bin"] = (agg.dev_median / base).round(3)
    print(agg.to_string())

    rho, p = spearmanr(later.days, later.dev)
    print(f"\nSpearman(days, deviation) = {rho:+.3f}  p = {p:.2e}")
    print("  positive = the baseline degrades as time passes (drift)")

    (OUT / "summary_drift.json").write_text(json.dumps({
        "experiment": "EXP-005b", "status": "exploratory diagnostic",
        "span_days_median": float(span.median()),
        "convergence_n_star_full": n_full,
        "convergence_n_star_window_matched": n_match,
        "hmog_n_star": 80,
        "curve_full": {str(k): (None if pd.isna(v) else float(v)) for k, v in full_curve.items()},
        "curve_matched": {str(k): (None if pd.isna(v) else float(v)) for k, v in match_curve.items()},
        "drift_spearman": float(rho), "drift_p": float(p),
        "deviation_by_day_bin": {str(k): float(v) for k, v in agg.dev_median.items()},
    }, indent=2))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

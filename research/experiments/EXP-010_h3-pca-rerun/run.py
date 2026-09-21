"""EXP-010 — re-test H3 with the better detector.

EXP-003 concluded personalization gives no benefit over a global model. That null was
measured with Mahalanobis, which EXP-009 then showed is the WEAKER detector — third of four,
beaten by PCA reconstruction error on every condition tested.

A null obtained with a weak instrument is not a settled null. This repeats the comparison
with PCA reconstruction as the scorer, on the one valid real contrast plus both synthetic
conditions, and reports Mahalanobis alongside so the two are directly comparable.

Arms, all scored as reconstruction error at matched 80% sensitivity:
    A  fixed univariate threshold (average_velocity)   - reference only; circular on synthetic
    B  GLOBAL   PCA fitted on all users' enrolment gestures pooled
    C  PERSONAL PCA fitted on that user's enrolment gestures alone

Personalization here means both the projection and the scaler are the person's own.

    python research/experiments/EXP-010_h3-pca-rerun/run.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.stats import wilcoxon
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research"))

from precog.baseline.engine import PersonalBaseline  # noqa: E402
from precog.deviation.score import score as dev_score  # noqa: E402
from precog.synthetic.generator import PopulationModel, enforce, generate, inject  # noqa: E402


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


_e3 = _load("exp003_run", "research/experiments/EXP-003_h3-personalized-vs-global/run.py")
fpr_at_sensitivity, cliffs_delta = _e3.fpr_at_sensitivity, _e3.cliffs_delta

OUT = HERE / "outputs"
SEED, SENS, ENROL, NCOMP = 42, 0.80, 80, 8


def recon_error(fit_X: np.ndarray, score_X: np.ndarray, n_comp: int) -> np.ndarray:
    """Squared reconstruction error under a PCA fitted on `fit_X`."""
    sc = StandardScaler().fit(fit_X)
    A, B = sc.transform(fit_X), sc.transform(score_X)
    k = min(n_comp, A.shape[1], max(1, A.shape[0] - 1))
    p = PCA(n_components=k, random_state=SEED).fit(A)
    return ((B - p.inverse_transform(p.transform(B))) ** 2).sum(axis=1)


def compare(df: pd.DataFrame, feats: list[str], bcfg: dict, label="y") -> pd.DataFrame:
    """Per-subject FPR for each arm, under both PCA and Mahalanobis."""
    df = df.sort_values(["subject", "t_start"]).reset_index(drop=True)
    enrol = df[df[label] == 0].groupby("subject").head(ENROL)

    pooled = np.nan_to_num(enrol[feats].to_numpy(float), nan=0.0, posinf=0.0, neginf=0.0)
    global_mah = PersonalBaseline(feats, bcfg).fit(enrol)

    rows = []
    for uid, g in df.groupby("subject"):
        e = enrol[enrol.subject == uid]
        test = g.drop(e.index)
        if len(e) < ENROL or test[label].nunique() < 2 or len(test) < 40:
            continue
        lab = test[label].to_numpy()
        Xe = np.nan_to_num(e[feats].to_numpy(float), nan=0.0, posinf=0.0, neginf=0.0)
        Xt = np.nan_to_num(test[feats].to_numpy(float), nan=0.0, posinf=0.0, neginf=0.0)

        rows.append({
            "subject": uid,
            "A": fpr_at_sensitivity(test["average_velocity"].to_numpy(), lab, SENS),
            "B_pca": fpr_at_sensitivity(recon_error(pooled, Xt, NCOMP), lab, SENS),
            "C_pca": fpr_at_sensitivity(recon_error(Xe, Xt, NCOMP), lab, SENS),
            "B_mah": fpr_at_sensitivity(
                dev_score(test[feats], global_mah)["deviation"].to_numpy(), lab, SENS),
            "C_mah": fpr_at_sensitivity(
                dev_score(test[feats], PersonalBaseline(feats, bcfg).fit(e))["deviation"].to_numpy(),
                lab, SENS),
        })
    return pd.DataFrame(rows).dropna()


def report(name: str, r: pd.DataFrame) -> dict:
    print(f"\n--- {name} · n = {len(r)} subjects · FPR at {SENS:.0%} sensitivity ---")
    print(f"{'scorer':<14}{'B global':>10}{'C personal':>12}{'C-B':>9}{'p':>11}{'cliffs_d':>10}")
    out = {"n_subjects": int(len(r))}
    for tag, b, c in (("PCA recon", "B_pca", "C_pca"), ("Mahalanobis", "B_mah", "C_mah")):
        d = r[c] - r[b]
        p = wilcoxon(r[c], r[b]).pvalue if d.abs().sum() > 0 else 1.0
        cd = cliffs_delta(r[c].to_numpy(), r[b].to_numpy())
        print(f"{tag:<14}{r[b].median():>10.3f}{r[c].median():>12.3f}"
              f"{d.median():>+9.3f}{p:>11.2e}{cd:>+10.3f}")
        out[tag] = {"B": float(r[b].median()), "C": float(r[c].median()),
                    "delta": float(d.median()), "p": float(p), "cliffs_delta": float(cd),
                    "C_better_pct": float((d < 0).mean())}
    print(f"{'(A threshold)':<14}{r.A.median():>10.3f}")
    out["A_threshold"] = float(r.A.median())
    return out


def main() -> int:
    OUT.mkdir(exist_ok=True)
    bcfg = yaml.safe_load((ROOT / "config/baseline.yaml").read_text())
    results = {}

    # ---------- real: HMOG sit -> walk (the only valid real contrast) ----------
    print("=" * 62)
    print("H3 RE-TEST · PCA reconstruction vs Mahalanobis")
    print("=" * 62)
    sess = pd.read_parquet(ROOT / "data/interim/hmog/sessions.parquet")
    hm = pd.read_parquet(ROOT / "data/processed/hmog_gesture-features_features-v0.1.parquet")
    hm = hm.merge(sess[["ActivityID", "posture"]].drop_duplicates("ActivityID"),
                  on="ActivityID", how="left")
    hm["y"] = (hm.posture == "walk").astype(int)
    drop = {"subject", "session", "ActivityID", "ScrollID", "t_start", "t_end",
            "feature_version", "posture", "phone_orientation", "y"}
    hfeats = [c for c in hm.columns if c not in drop]
    results["hmog_sit_walk"] = report("HMOG sit->walk (REAL)", compare(hm, hfeats, bcfg))

    # ---------- synthetic: both mechanisms ----------
    scfg = yaml.safe_load((ROOT / "config/synthetic.yaml").read_text())
    rng = np.random.default_rng(scfg["seed"])
    real = pd.read_parquet(ROOT / scfg["fit_from"])
    sfeats = [c for c in real.columns if c not in {
        "subject", "session", "t_start", "t_end", "feature_version", "phone_orientation"}]
    pop = PopulationModel(real, sfeats)
    base = generate(pop, scfg, rng)
    for kind in scfg["anomaly"]["types"]:
        inj = enforce(inject(base, pop, scfg, kind, 1.5), scfg)
        results[f"synthetic_{kind}"] = report(f"synthetic {kind} (mag 1.5)",
                                              compare(inj, sfeats, bcfg))

    (OUT / "summary.json").write_text(json.dumps({
        "experiment": "EXP-010", "supersedes_scorer_in": "EXP-003",
        "n_components": NCOMP, "sensitivity": SENS, "enrol": ENROL, "seed": SEED,
        "results": results,
    }, indent=2))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

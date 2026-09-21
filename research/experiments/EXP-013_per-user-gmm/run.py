"""EXP-013 — Per-user GMM vs single-Gaussian baseline.

Current Mahalanobis baseline assumes a single Gaussian per user (EXP-003/010).
Lamb et al. note users have multiple behavioural modes (sit/stand/walk) which
the generator also includes as 'context shifts'. A 2-component GMM may fit better.

Compares FPR at 80% sensitivity: single-Gaussian (Mahalanobis) vs GMM-2 scoring.

    python research/experiments/EXP-013_per-user-gmm/run.py
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
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research"))

from precog.synthetic.generator import PopulationModel, enforce, generate, inject  # noqa

OUT = HERE / "outputs"
SEED, ENROL, SENS = 42, 80, 0.80


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


_e3 = _load("exp003_run2", "research/experiments/EXP-003_h3-personalized-vs-global/run.py")
fpr_at_sensitivity = _e3.fpr_at_sensitivity


def gmm_score(fit_X: np.ndarray, score_X: np.ndarray, n_components: int = 2) -> np.ndarray:
    """Negative log-likelihood under a GMM as anomaly score (higher = more anomalous)."""
    sc = StandardScaler().fit(fit_X)
    A, B = sc.transform(fit_X), sc.transform(score_X)
    n_comp = min(n_components, max(1, A.shape[0] // 2))
    gm = GaussianMixture(n_components=n_comp, covariance_type="full",
                         random_state=SEED, n_init=3).fit(A)
    return -gm.score_samples(B)


def mah_score(fit_X: np.ndarray, score_X: np.ndarray) -> np.ndarray:
    from sklearn.covariance import LedoitWolf
    sc = StandardScaler().fit(fit_X)
    A, B = sc.transform(fit_X), sc.transform(score_X)
    try:
        cov = LedoitWolf().fit(A)
        diff = B - cov.location_
        return np.einsum("ij,jk,ik->i", diff, np.linalg.inv(cov.covariance_), diff)
    except Exception:
        return np.linalg.norm(B - A.mean(axis=0), axis=1)


def compare(df: pd.DataFrame, feats: list, label: str = "y") -> pd.DataFrame:
    rows = []
    for uid, g in df.groupby("subject"):
        enrol = g[g[label] == 0].head(ENROL)
        test = g.drop(enrol.index)
        if len(enrol) < ENROL or test[label].nunique() < 2 or len(test) < 20:
            continue
        Xe = np.nan_to_num(enrol[feats].to_numpy(float))
        Xt = np.nan_to_num(test[feats].to_numpy(float))
        lab = test[label].to_numpy()
        rows.append({
            "subject": uid,
            "mah": fpr_at_sensitivity(mah_score(Xe, Xt), lab, SENS),
            "gmm2": fpr_at_sensitivity(gmm_score(Xe, Xt, 2), lab, SENS),
            "gmm3": fpr_at_sensitivity(gmm_score(Xe, Xt, 3), lab, SENS),
        })
    return pd.DataFrame(rows).dropna()


def report(name, r):
    print(f"\n--- {name} · n={len(r)} ---")
    print(f"{'scorer':<12}{'median FPR':>12}{'vs mah':>10}{'p':>12}")
    for col, label in [("mah", "Mahalanobis"), ("gmm2", "GMM-2"), ("gmm3", "GMM-3")]:
        med = r[col].median()
        if col == "mah":
            print(f"{label:<12}{med:>12.3f}{'—':>10}{'—':>12}")
        else:
            d = r[col] - r.mah
            p = wilcoxon(r[col], r.mah).pvalue if d.abs().sum() > 0 else 1.0
            print(f"{label:<12}{med:>12.3f}{d.median():>+10.3f}{p:>12.2e}")
    return {col: float(r[col].median()) for col in ("mah", "gmm2", "gmm3")}


def main() -> int:
    OUT.mkdir(exist_ok=True)
    results = {}

    # HMOG sit→walk (the only valid real contrast)
    sess = pd.read_parquet(ROOT / "data/interim/hmog/sessions.parquet")
    hm = pd.read_parquet(ROOT / "data/processed/hmog_gesture-features_features-v0.1.parquet")
    hm = hm.merge(sess[["ActivityID", "posture"]].drop_duplicates("ActivityID"),
                  on="ActivityID", how="left")
    hm["y"] = (hm.posture == "walk").astype(int)
    drop = {"subject", "session", "ActivityID", "ScrollID", "t_start", "t_end",
            "feature_version", "posture", "phone_orientation", "y"}
    feats = [c for c in hm.columns if c not in drop]
    print(f"HMOG sit->walk: {len(hm):,} gestures · {hm.subject.nunique()} subjects")
    results["hmog_sit_walk"] = report("HMOG sit->walk", compare(hm, feats))

    # Synthetic — person_relative mag 1.5 (most relevant test bed)
    scfg = yaml.safe_load((ROOT / "config/synthetic.yaml").read_text())
    rng = np.random.default_rng(scfg["seed"])
    real = pd.read_parquet(ROOT / scfg["fit_from"])
    sfeats = [c for c in real.columns if c not in {
        "subject", "session", "t_start", "t_end", "feature_version", "phone_orientation"}]
    pop = PopulationModel(real, sfeats)
    base = generate(pop, scfg, rng)

    for kind in ["person_relative", "population_consistent"]:
        inj = enforce(inject(base, pop, scfg, kind, 1.5), scfg)
        r = compare(inj, sfeats)
        results[f"synthetic_{kind}"] = report(f"synthetic {kind} mag1.5", r)

    (OUT / "summary.json").write_text(json.dumps({
        "experiment": "EXP-013",
        "sensitivity": SENS,
        "enrol": ENROL,
        "seed": SEED,
        "note": "FPR at 80% sensitivity — lower is better",
        "results": results,
    }, indent=2))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

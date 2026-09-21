"""EXP-009 — the complete model ladder, supervised and unsupervised.

Fills two gaps.

SUPERVISED LADDER. EXP-007 jumped from a single threshold straight to XGBoost, leaving no
interpretable rungs between. Each model here is justified by prior art rather than by wanting
more models:
    LogR, DT   - the blueprint's named interpretable baselines
    NB         - assumes feature independence, the exact assumption that broke the mean-z
                 scorer (AUC 0.545 vs Mahalanobis 0.868). Included to demonstrate the failure
                 rather than assert it
    k-NN       - Touchalytics' own classifier; makes comparison with Frank et al. direct
    RF         - Time2Stop's classifier; the blueprint calls benchmarking against it mandatory
    XGBoost    - carried over from EXP-007
    +PCA       - signal dilution has bitten three times; tests whether a principled projection
                 beats the hand-picked 6-feature Mahalanobis core

UNSUPERVISED ARM. PRECOG has no labels at inference, so this is what it actually is in
production. Isolation Forest and One-Class SVM are both named in the blueprint and were
entirely missing until now.

Contrasts used are only those with trustworthy labels: HMOG sit->walk (the one valid real
contrast after EXP-007's leakage finding) and the EXP-008 synthetic conditions.

    python research/experiments/EXP-009_model-ladder/run.py
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM
from sklearn.tree import DecisionTreeClassifier

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research"))

from precog.baseline.engine import PersonalBaseline  # noqa: E402
from precog.deviation.score import score as dev_score  # noqa: E402
from precog.synthetic.generator import PopulationModel, enforce, generate, inject  # noqa: E402


def _load(name: str, rel: str):
    """Both EXP-003 and EXP-007 define run.py, so import each by path rather than by name."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_e3 = _load("exp003_run", "research/experiments/EXP-003_h3-personalized-vs-global/run.py")
_e7 = _load("exp007_run", "research/experiments/EXP-007_models/run.py")
fpr_at_sensitivity = _e3.fpr_at_sensitivity
cliffs_delta = _e3.cliffs_delta

OUT = HERE / "outputs"
SEED = 42
SENS = 0.80
ENROL = 80
OCSVM_CAP = 400          # One-Class SVM is superlinear; cap per-user training size


def supervised_models(seed: int) -> dict:
    """Each rung standardised where the model needs it; trees do not."""
    return {
        "LogR": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, random_state=seed)),
        "NB": make_pipeline(StandardScaler(), GaussianNB()),
        "kNN": make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=15)),
        "DT": DecisionTreeClassifier(max_depth=4, random_state=seed),
        "RF": RandomForestClassifier(n_estimators=300, max_depth=8, n_jobs=-1, random_state=seed),
        "PCA+LogR": make_pipeline(StandardScaler(), PCA(n_components=8, random_state=seed),
                                  LogisticRegression(max_iter=2000, random_state=seed)),
    }


def run_supervised(X, y, groups, seed=SEED) -> list[dict]:
    from xgboost import XGBClassifier
    models = supervised_models(seed)
    models["XGBoost"] = XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.08,
                                      subsample=0.8, colsample_bytree=0.8, eval_metric="aucpr",
                                      tree_method="hist", n_jobs=-1, random_state=seed)
    rows = []
    gkf = GroupKFold(n_splits=5)
    for name, m in models.items():
        pr, roc = [], []
        for tr, te in gkf.split(X, y, groups):
            m.fit(X[tr], y[tr])
            p = m.predict_proba(X[te])[:, 1]
            pr.append(average_precision_score(y[te], p))
            roc.append(roc_auc_score(y[te], p))
        rows.append({"model": name, "prauc": float(np.mean(pr)), "prauc_sd": float(np.std(pr)),
                     "rocauc": float(np.mean(roc))})
    return rows


def run_unsupervised(df, feats, bcfg, label_col="y") -> pd.DataFrame:
    """Per-user novelty detection: fit on that user's NORMAL gestures only, score everything.

    This is PRECOG's real inference setting — no labels, one person's history as the only
    reference. Labels are used solely to evaluate, never to fit.
    """
    rows = []
    rng = np.random.default_rng(SEED)
    for uid, g in df.groupby("subject"):
        norm = g[g[label_col] == 0]
        if len(norm) < ENROL + 20 or g[label_col].nunique() < 2:
            continue
        enrol = norm.iloc[:ENROL]
        test = g.drop(enrol.index)
        if test[label_col].nunique() < 2:
            continue
        lab = test[label_col].to_numpy()

        Xe = np.nan_to_num(enrol[feats].to_numpy(float), nan=0.0, posinf=0.0, neginf=0.0)
        Xt = np.nan_to_num(test[feats].to_numpy(float), nan=0.0, posinf=0.0, neginf=0.0)
        sc = StandardScaler().fit(Xe)
        Xe_s, Xt_s = sc.transform(Xe), sc.transform(Xt)

        out = {"subject": uid, "n_test": len(test)}

        iso = IsolationForest(n_estimators=200, contamination="auto", random_state=SEED, n_jobs=-1)
        iso.fit(Xe_s)
        out["IsolationForest"] = fpr_at_sensitivity(-iso.score_samples(Xt_s), lab, SENS)

        sub = Xe_s if len(Xe_s) <= OCSVM_CAP else Xe_s[rng.choice(len(Xe_s), OCSVM_CAP, False)]
        oc = OneClassSVM(kernel="rbf", nu=0.1, gamma="scale").fit(sub)
        out["OneClassSVM"] = fpr_at_sensitivity(-oc.score_samples(Xt_s), lab, SENS)

        pb = PersonalBaseline(feats, bcfg).fit(enrol)
        out["Mahalanobis"] = fpr_at_sensitivity(
            dev_score(test[feats], pb)["deviation"].to_numpy(), lab, SENS)

        p = PCA(n_components=8, random_state=SEED).fit(Xe_s)
        rec = p.inverse_transform(p.transform(Xt_s))
        out["PCA_recon"] = fpr_at_sensitivity(((Xt_s - rec) ** 2).sum(axis=1), lab, SENS)

        rows.append(out)
    return pd.DataFrame(rows).dropna()


def main() -> int:
    OUT.mkdir(exist_ok=True)
    bcfg = yaml.safe_load((ROOT / "config/baseline.yaml").read_text())
    ecfg = yaml.safe_load((ROOT / "research/experiments/EXP-007_models/config.yaml").read_text())
    load_contrast, make_windows, summarise = _e7.load_contrast, _e7.make_windows, _e7.summarise

    results = {"supervised": {}, "unsupervised": {}}

    # ---------- 1. supervised ladder on the one valid real contrast ----------
    print("=" * 66)
    print("SUPERVISED LADDER — HMOG sit->walk (the only valid real contrast)")
    print("=" * 66)
    df, feats = load_contrast(ecfg["contrasts"]["hmog_posture"], ecfg)
    seqs, y, groups = make_windows(df, feats, ecfg["window"])
    flat, _ = summarise(seqs, feats)
    print(f"{len(seqs):,} windows · {len(set(groups))} subjects · {len(feats)} features · "
          f"prevalence {y.mean():.3f}\n")
    rows = run_supervised(flat, y, groups)
    rows.append({"model": "GRU (EXP-007)", "prauc": 0.597, "prauc_sd": 0.054, "rocauc": 0.641})
    rows.sort(key=lambda r: -r["prauc"])
    print(f"{'model':<14}{'PR-AUC':>9}{'± sd':>8}{'ROC-AUC':>10}")
    for r in rows:
        print(f"{r['model']:<14}{r['prauc']:>9.3f}{r['prauc_sd']:>8.3f}{r['rocauc']:>10.3f}")
    print(f"{'(prevalence)':<14}{y.mean():>9.3f}")
    results["supervised"]["hmog_posture"] = rows

    # ---------- 2. unsupervised arm ----------
    print("\n" + "=" * 66)
    print("UNSUPERVISED ARM — per-user novelty detection (PRECOG's real setting)")
    print("=" * 66)

    sess = pd.read_parquet(ROOT / "data/interim/hmog/sessions.parquet")
    hm = pd.read_parquet(ROOT / "data/processed/hmog_gesture-features_features-v0.1.parquet")
    hm = hm.merge(sess[["ActivityID", "posture"]].drop_duplicates("ActivityID"),
                  on="ActivityID", how="left")
    hm["y"] = (hm.posture == "walk").astype(int)
    hm = hm.sort_values(["subject", "t_start"]).reset_index(drop=True)
    ufeats = [c for c in feats if c in hm.columns]

    print("\nHMOG sit->walk · FPR at 80% sensitivity (lower is better)")
    r = run_unsupervised(hm, ufeats, bcfg)
    cols = ["IsolationForest", "OneClassSVM", "Mahalanobis", "PCA_recon"]
    print(f"  n = {len(r)} subjects")
    for c in cols:
        print(f"    {c:<18}{r[c].median():>8.3f}")
    results["unsupervised"]["hmog_posture"] = {c: float(r[c].median()) for c in cols}
    results["unsupervised"]["hmog_posture"]["n_subjects"] = int(len(r))

    # ---------- 3. unsupervised on synthetic, both anomaly types ----------
    scfg = yaml.safe_load((ROOT / "config/synthetic.yaml").read_text())
    rng = np.random.default_rng(scfg["seed"])
    real = pd.read_parquet(ROOT / scfg["fit_from"])
    sfeats = [c for c in real.columns if c not in {
        "subject", "session", "t_start", "t_end", "feature_version", "phone_orientation"}]
    pop = PopulationModel(real, sfeats)
    base = generate(pop, scfg, rng)
    for kind in scfg["anomaly"]["types"]:
        inj = enforce(inject(base, pop, scfg, kind, 1.5), scfg)
        inj = inj.sort_values(["subject", "t_start"]).reset_index(drop=True)
        r = run_unsupervised(inj, sfeats, bcfg)
        print(f"\nsynthetic · {kind} (magnitude 1.5) · n = {len(r)}")
        for c in cols:
            print(f"    {c:<18}{r[c].median():>8.3f}")
        results["unsupervised"][f"synthetic_{kind}"] = {c: float(r[c].median()) for c in cols}
        results["unsupervised"][f"synthetic_{kind}"]["n_subjects"] = int(len(r))

    (OUT / "summary.json").write_text(json.dumps(results, indent=2))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

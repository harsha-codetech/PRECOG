"""EXP-007 — XGBoost + SHAP (model C) and a GRU (model E).

Two questions, one experimental frame:

  1. WHICH features carry a behavioural deviation? Three contrasts have shown a single
     feature beating 29, but not which one or whether the answer differs by contrast.
     SHAP over XGBoost answers it directly.

  2. Does gesture ORDER matter? Both models see identical windows of consecutive gestures.
     XGBoost gets per-window summary statistics; the GRU gets the raw sequence. If the GRU
     does not win, order carries nothing the summaries already have — which is a result
     worth reporting, not a failure to hide.

Evaluation is subject-wise throughout (FETA pitfall P3). PR-AUC is primary because the
classes are unbalanced per subject; calibration is reported because a probability that gets
shown to a user must mean what it says.

    python research/experiments/EXP-007_models/run.py
    python research/experiments/EXP-007_models/run.py --contrast feta_task
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import GroupKFold

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / "outputs"


def load_contrast(spec: dict, cfg: dict) -> tuple[pd.DataFrame, list[str]]:
    """Concatenate the two sides of a contrast with a binary label."""
    frames = []
    for label, side in ((0, spec["normal"]), (1, spec["changed"])):
        df = pd.read_parquet(ROOT / side["path"])
        if "posture" in side:
            sess = pd.read_parquet(ROOT / "data/interim/hmog/sessions.parquet")
            df = df.merge(sess[["ActivityID", "posture"]].drop_duplicates("ActivityID"),
                          on="ActivityID", how="left")
            df = df[df.posture == side["posture"]]
        df = df.assign(y=label)
        frames.append(df)
    both = pd.concat(frames, ignore_index=True)
    feats = [c for c in both.columns if c not in set(cfg["exclude"]) | {"y"}]
    both = both.sort_values(["subject", "y", "t_start"]).reset_index(drop=True)
    return both, feats


def make_windows(df: pd.DataFrame, feats: list[str], w: dict):
    """Overlapping windows of consecutive gestures, never crossing subject/label/session."""
    seqs, labels, groups = [], [], []
    size, stride = w["size"], w["stride"]
    key = ["subject", "y"] + (["session"] if "session" in df.columns else [])
    for keys, g in df.groupby(key, sort=False):
        X = g[feats].to_numpy(np.float32)
        if len(X) < size:
            continue
        for s in range(0, len(X) - size + 1, stride):
            seqs.append(X[s:s + size])
            labels.append(keys[1])
            groups.append(keys[0])
    if not seqs:
        return None, None, None
    return np.stack(seqs), np.array(labels), np.array(groups)


def summarise(seqs: np.ndarray, feats: list[str]) -> tuple[np.ndarray, list[str]]:
    """Per-window mean and std — what XGBoost sees instead of the sequence."""
    m = np.nanmean(seqs, axis=1)
    s = np.nanstd(seqs, axis=1)
    names = [f"{f}_mean" for f in feats] + [f"{f}_std" for f in feats]
    return np.nan_to_num(np.hstack([m, s]), nan=0.0, posinf=0.0, neginf=0.0), names


def fit_xgb(Xtr, ytr, Xte, cfg):
    from xgboost import XGBClassifier
    p = cfg["xgboost"]
    m = XGBClassifier(
        n_estimators=p["n_estimators"], max_depth=p["max_depth"],
        learning_rate=p["learning_rate"], subsample=p["subsample"],
        colsample_bytree=p["colsample_bytree"], reg_lambda=p["reg_lambda"],
        eval_metric="aucpr", tree_method="hist", n_jobs=-1,
        random_state=cfg["seed"],
    )
    m.fit(Xtr, ytr, verbose=False)
    return m, m.predict_proba(Xte)[:, 1]


def fit_gru(seq_tr, ytr, seq_te, cfg):
    import torch
    import torch.nn as nn
    g = cfg["gru"]
    torch.manual_seed(cfg["seed"])

    mu = np.nanmean(seq_tr, axis=(0, 1), keepdims=True)
    sd = np.nanstd(seq_tr, axis=(0, 1), keepdims=True) + 1e-6
    tr = np.nan_to_num((seq_tr - mu) / sd, nan=0.0, posinf=0.0, neginf=0.0)
    te = np.nan_to_num((seq_te - mu) / sd, nan=0.0, posinf=0.0, neginf=0.0)

    class Net(nn.Module):
        def __init__(self, f):
            super().__init__()
            self.gru = nn.GRU(f, g["hidden"], g["layers"], batch_first=True,
                              dropout=g["dropout"] if g["layers"] > 1 else 0.0)
            self.head = nn.Sequential(nn.Dropout(g["dropout"]), nn.Linear(g["hidden"], 1))

        def forward(self, x):
            _, h = self.gru(x)
            return self.head(h[-1]).squeeze(-1)

    net = Net(tr.shape[2])
    opt = torch.optim.Adam(net.parameters(), lr=g["lr"])
    pos_w = torch.tensor([(ytr == 0).sum() / max((ytr == 1).sum(), 1)], dtype=torch.float32)
    lossf = nn.BCEWithLogitsLoss(pos_weight=pos_w)

    Xt = torch.tensor(tr); yt = torch.tensor(ytr, dtype=torch.float32)
    n = len(Xt); idx = np.arange(n)
    best, bad, best_state = np.inf, 0, None
    for _ in range(g["epochs"]):
        net.train(); np.random.shuffle(idx); tot = 0.0
        for i in range(0, n, g["batch_size"]):
            b = idx[i:i + g["batch_size"]]
            opt.zero_grad()
            l = lossf(net(Xt[b]), yt[b])
            l.backward(); opt.step(); tot += float(l) * len(b)
        ep = tot / n
        if ep < best - 1e-4:
            best, bad = ep, 0
            best_state = {k: v.clone() for k, v in net.state_dict().items()}
        else:
            bad += 1
            if bad >= g["patience"]:
                break
    if best_state:
        net.load_state_dict(best_state)
    net.eval()
    with torch.no_grad():
        return torch.sigmoid(net(torch.tensor(te))).numpy()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contrast", default=None)
    ap.add_argument("--skip-gru", action="store_true")
    args = ap.parse_args()

    cfg = yaml.safe_load((HERE / "config.yaml").read_text())
    OUT.mkdir(exist_ok=True)
    rng = np.random.default_rng(cfg["seed"])
    names = [args.contrast] if args.contrast else list(cfg["contrasts"])

    results, shap_tables = [], {}
    for cname in names:
        print(f"\n{'=' * 64}\n{cname}\n{'=' * 64}")
        df, feats = load_contrast(cfg["contrasts"][cname], cfg)
        seqs, y, groups = make_windows(df, feats, cfg["window"])
        if seqs is None:
            print("  no windows"); continue
        flat, flat_names = summarise(seqs, feats)
        print(f"windows {len(seqs):,} | subjects {len(set(groups))} | "
              f"features {len(feats)} | positives {y.mean():.1%}")

        gkf = GroupKFold(n_splits=cfg["cv"]["folds"])
        rows, shap_acc = [], []
        for k, (tr, te) in enumerate(gkf.split(flat, y, groups), 1):
            xgb_m, p_xgb = fit_xgb(flat[tr], y[tr], flat[te], cfg)
            fold = {"fold": k, "n_test": len(te), "test_subjects": len(set(groups[te]))}
            fold["xgb_prauc"] = average_precision_score(y[te], p_xgb)
            fold["xgb_rocauc"] = roc_auc_score(y[te], p_xgb)
            fold["xgb_brier"] = brier_score_loss(y[te], p_xgb)

            if not args.skip_gru:
                p_gru = fit_gru(seqs[tr], y[tr], seqs[te], cfg)
                fold["gru_prauc"] = average_precision_score(y[te], p_gru)
                fold["gru_rocauc"] = roc_auc_score(y[te], p_gru)
                fold["gru_brier"] = brier_score_loss(y[te], p_gru)

            rows.append(fold)
            print(f"  fold {k}: XGB PR-AUC {fold['xgb_prauc']:.3f}" +
                  (f" | GRU {fold['gru_prauc']:.3f}" if "gru_prauc" in fold else ""), flush=True)

            if k == 1:
                import shap
                sub = rng.choice(len(te), size=min(2000, len(te)), replace=False)
                sv = shap.TreeExplainer(xgb_m).shap_values(flat[te][sub])
                shap_acc.append(np.abs(sv).mean(axis=0))

        r = pd.DataFrame(rows)
        base = float(y.mean())
        line = {"contrast": cname, "windows": int(len(seqs)),
                "subjects": int(len(set(groups))), "baseline_prauc": base}
        for m in ("xgb", "gru"):
            if f"{m}_prauc" in r:
                line[f"{m}_prauc"] = float(r[f"{m}_prauc"].mean())
                line[f"{m}_prauc_sd"] = float(r[f"{m}_prauc"].std())
                line[f"{m}_rocauc"] = float(r[f"{m}_rocauc"].mean())
                line[f"{m}_brier"] = float(r[f"{m}_brier"].mean())
        results.append(line)

        print(f"\n  baseline PR-AUC (prevalence) : {base:.3f}")
        print(f"  XGBoost PR-AUC               : {line['xgb_prauc']:.3f} "
              f"± {line['xgb_prauc_sd']:.3f}   ROC {line['xgb_rocauc']:.3f}   "
              f"Brier {line['xgb_brier']:.3f}")
        if "gru_prauc" in line:
            print(f"  GRU     PR-AUC               : {line['gru_prauc']:.3f} "
                  f"± {line['gru_prauc_sd']:.3f}   ROC {line['gru_rocauc']:.3f}   "
                  f"Brier {line['gru_brier']:.3f}")
            d = line["gru_prauc"] - line["xgb_prauc"]
            print(f"  GRU - XGBoost                : {d:+.3f}  "
                  f"({'sequence order helps' if d > 0.01 else 'order adds nothing'})")

        if shap_acc:
            imp = pd.Series(shap_acc[0], index=flat_names).sort_values(ascending=False)
            shap_tables[cname] = imp
            imp.to_csv(OUT / f"shap_{cname}.csv")
            print("\n  top features by mean |SHAP| (fold 1):")
            for nm, v in imp.head(8).items():
                print(f"    {nm:<34} {v:.4f}")

    pd.DataFrame(results).to_csv(OUT / "model_comparison.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps({
        "experiment": "EXP-007", "seed": cfg["seed"],
        "window": cfg["window"], "cv": cfg["cv"], "results": results,
        "shap_top10": {k: v.head(10).round(5).to_dict() for k, v in shap_tables.items()},
    }, indent=2))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Generate all paper figures from experiment outputs.

Figures produced:
  fig-01  Pipeline architecture (text diagram — written separately)
  fig-02  ICC distribution by feature (EXP-001)
  fig-03  Baseline convergence curves HMOG vs FETA (EXP-002, EXP-005b)
  fig-04  FPR personalized vs global (not generated — null result, bar chart)
  fig-05  Per-subject identification accuracy distribution (EXP-001, EXP-005a)
  fig-06  Drift deviation by day bin (EXP-005b)
  fig-07  Model ladder comparison — PR-AUC (EXP-009)
  fig-08  SHAP feature importance (EXP-007)
  fig-09  PCA component sweep (EXP-011 — generated after that experiment)

    python scripts/generate_figures.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "results" / "figures"
TAB_DIR = ROOT / "results" / "tables"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TAB_DIR.mkdir(parents=True, exist_ok=True)

# Palette from design system
INK   = "#0E1320"
PAPER = "#F5F6F8"
ACCENT = "#1F3B73"
SAGE  = "#4A7C6F"
AMBER = "#B5893E"
RUST  = "#A3442E"
MID   = "#8A9BB5"

plt.rcParams.update({
    "figure.facecolor": PAPER, "axes.facecolor": PAPER,
    "axes.edgecolor": INK, "text.color": INK,
    "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
    "font.family": "sans-serif", "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "grid.alpha": 0.3, "grid.color": MID,
})


# ── fig-02: ICC distribution ─────────────────────────────────────────────────
def fig_icc():
    p1 = ROOT / "research/experiments/EXP-001_h1-individual-distinctiveness/outputs/icc_per_feature.csv"
    p5 = ROOT / "research/experiments/EXP-005_feta-replication/outputs/icc_per_feature.csv"
    if not p1.exists() or not p5.exists():
        print("fig-02: skipped (ICC CSVs missing)")
        return

    df1 = pd.read_csv(p1)
    df1.columns = ["feature", "ICC"]
    df1 = df1.sort_values("ICC", ascending=False)
    df5 = pd.read_csv(p5)
    df5.columns = ["feature", "ICC"]
    df5 = df5.sort_values("ICC", ascending=False)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=False)
    for ax, df, title, color in zip(axes, [df1, df5],
                                    ["HMOG (99 subjects)", "FETA (138 subjects)"],
                                    [ACCENT, SAGE]):
        # top 15
        top = df.head(15)
        labels = [f.replace("_", " ").replace(" mean", "").replace(" std", " σ")[:22]
                  for f in top.iloc[:, 0]]
        ax.barh(range(len(top)), top.ICC, color=color, alpha=0.85)
        ax.set_yticks(range(len(top)))
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlabel("ICC")
        ax.set_title(title, fontsize=10, fontweight="bold")
        ax.axvline(0.5, color=AMBER, lw=1, ls="--", label="ICC=0.5")
        ax.axvline(0.3, color=RUST, lw=1, ls=":", label="ICC=0.3")
        ax.invert_yaxis()
        ax.legend(fontsize=8)

    fig.suptitle("fig-02  Intraclass Correlation by Feature (top 15)", fontsize=11)
    fig.tight_layout()
    path = FIG_DIR / "fig-02_icc-by-feature.pdf"
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"fig-02 -> {path.name}")


# ── fig-03: convergence curves ───────────────────────────────────────────────
def fig_convergence():
    p2 = ROOT / "research/experiments/EXP-002_h2-baseline-convergence/outputs/summary.json"
    p5 = ROOT / "research/experiments/EXP-005_feta-replication/outputs/summary_drift.json"
    if not p2.exists() or not p5.exists():
        print("fig-03: skipped (summary JSONs missing)")
        return

    d2 = json.loads(p2.read_text())
    d5 = json.loads(p5.read_text())

    curve_hmog = {r["n"]: r["spearman_median"] for r in d2["curve"]}
    curve_feta_full = {int(k): v for k, v in d5["curve_full"].items()}
    curve_feta_win  = {int(k): v for k, v in d5["curve_matched"].items()}

    fig, ax = plt.subplots(figsize=(7, 4))
    ns = sorted(set(curve_hmog) & set(curve_feta_full))
    ax.plot(ns, [curve_hmog[n] for n in ns], "o-", color=ACCENT, label="HMOG (lab, short window)", lw=2)
    ax.plot(ns, [curve_feta_full.get(n, np.nan) for n in ns], "s--",
            color=RUST, label="FETA full span (30 days)", lw=2)
    ax.plot(ns, [curve_feta_win.get(n, np.nan) for n in ns], "^-",
            color=SAGE, label="FETA window-matched", lw=2)
    ax.axhline(0.95, color=INK, lw=1, ls=":", alpha=0.6, label="ρ = 0.95 target")
    ax.axvline(80, color=AMBER, lw=1, ls="--", alpha=0.7, label="n = 80 (HMOG n★)")
    ax.set_xlabel("Enrollment gestures (n)")
    ax.set_ylabel("Spearman ρ (feature-rank stability)")
    ax.set_ylim(0.5, 1.01)
    ax.set_title("fig-03  Baseline Convergence: HMOG vs FETA", fontweight="bold")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(axis="y")
    fig.tight_layout()
    path = FIG_DIR / "fig-03_convergence-curves.pdf"
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"fig-03 -> {path.name}")


# ── fig-05: per-subject accuracy distribution ────────────────────────────────
def fig_per_subject():
    p1 = ROOT / "research/experiments/EXP-001_h1-individual-distinctiveness/outputs/per_subject_accuracy.csv"
    p5 = ROOT / "research/experiments/EXP-005_feta-replication/outputs/per_subject_accuracy.csv"
    if not p1.exists() or not p5.exists():
        print("fig-05: skipped (CSVs missing)")
        return

    df1 = pd.read_csv(p1)
    df5 = pd.read_csv(p5)
    acc1 = df1.iloc[:, -1].dropna()
    acc5 = df5.iloc[:, -1].dropna()

    fig, ax = plt.subplots(figsize=(7, 4))
    bins = np.linspace(0, 1, 21)
    ax.hist(acc1, bins=bins, alpha=0.7, color=ACCENT, label=f"HMOG (n={len(acc1)})", density=True)
    ax.hist(acc5, bins=bins, alpha=0.6, color=SAGE, label=f"FETA (n={len(acc5)})", density=True)
    ax.set_xlabel("Top-1 identification accuracy (per subject)")
    ax.set_ylabel("Density")
    ax.set_title("fig-05  Per-Subject Identification Accuracy: Wide Spread Replicated", fontweight="bold")
    ax.legend()
    ax.grid(axis="y")
    # annotation
    ax.axvline(acc1.median(), color=ACCENT, lw=1.5, ls="--", alpha=0.9)
    ax.axvline(acc5.median(), color=SAGE, lw=1.5, ls="--", alpha=0.9)
    fig.tight_layout()
    path = FIG_DIR / "fig-05_per-subject-spread.pdf"
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"fig-05 -> {path.name}")


# ── fig-06: drift over days ──────────────────────────────────────────────────
def fig_drift():
    p = ROOT / "research/experiments/EXP-005_feta-replication/outputs/summary_drift.json"
    if not p.exists():
        print("fig-06: skipped")
        return
    d = json.loads(p.read_text())
    bins = list(d["deviation_by_day_bin"].keys())
    vals = list(d["deviation_by_day_bin"].values())
    labels = [b.replace("[", "").replace(")", "").replace(", ", "–") for b in bins]
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.bar(range(len(vals)), vals, color=AMBER, alpha=0.85)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels([f"day {l}" for l in labels], fontsize=8)
    ax.set_ylabel("Median deviation (robust z-score)")
    ax.set_title("fig-06  Temporal Drift: +12% Over 30 Days (FETA, n=138)", fontweight="bold")
    ax.grid(axis="y")
    fig.tight_layout()
    path = FIG_DIR / "fig-06_drift-over-days.pdf"
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"fig-06 -> {path.name}")


# ── fig-07: model ladder ─────────────────────────────────────────────────────
def fig_model_ladder():
    p = ROOT / "research/experiments/EXP-009_model-ladder/outputs/summary.json"
    if not p.exists():
        print("fig-07: skipped")
        return
    d = json.loads(p.read_text())
    sup = sorted(d["supervised"]["hmog_posture"], key=lambda r: r["prauc"], reverse=True)
    uns = sorted(d["unsupervised"]["hmog_posture"].items(), key=lambda kv: kv[1], reverse=True)
    uns = [(k, v) for k, v in uns if k != "n_subjects"]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))

    # supervised
    ax = axes[0]
    names = [r["model"] for r in sup]
    prauc = [r["prauc"] for r in sup]
    sd    = [r.get("prauc_sd", 0) for r in sup]
    bars = ax.barh(range(len(names)), prauc, xerr=sd, color=ACCENT, alpha=0.85, capsize=3)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names)
    ax.invert_yaxis()
    ax.set_xlabel("PR-AUC")
    ax.set_title("Supervised (HMOG sit->walk)", fontweight="bold")
    ax.axvline(d["supervised"]["hmog_posture"][-1]["prauc"], color=RUST,
               lw=1, ls="--", alpha=0.5, label="DT baseline")
    baseline = next(r for r in sup if r["model"] == "DT")
    ax.set_xlim(0.48, 0.72)

    # unsupervised
    ax = axes[1]
    names2 = [k for k, v in uns]
    vals2  = [v for k, v in uns]
    ax.barh(range(len(names2)), vals2, color=SAGE, alpha=0.85)
    ax.set_yticks(range(len(names2)))
    ax.set_yticklabels(names2)
    ax.invert_yaxis()
    ax.set_xlabel("PR-AUC")
    ax.set_title("Unsupervised (HMOG sit->walk)", fontweight="bold")
    ax.set_xlim(0.7, 0.9)

    fig.suptitle("fig-07  Model Ladder: Supervised and Unsupervised Arms", fontsize=11)
    fig.tight_layout()
    path = FIG_DIR / "fig-07_model-ladder.pdf"
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"fig-07 -> {path.name}")


# ── fig-08: SHAP importance ──────────────────────────────────────────────────
def fig_shap():
    p = ROOT / "research/experiments/EXP-007_models/outputs/shap_hmog_posture.csv"
    if not p.exists():
        print("fig-08: skipped")
        return
    df = pd.read_csv(p)
    df.columns = ["feature", "shap"]
    df = df.sort_values("shap", ascending=False).head(15)
    labels = [f.replace("_mean", " μ").replace("_std", " σ").replace("_", " ")[:28]
              for f in df.feature]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh(range(len(df)), df.shap, color=ACCENT, alpha=0.85)
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Mean |SHAP| value")
    ax.set_title("fig-08  SHAP Feature Importance (XGBoost, HMOG sit->walk, top 15)",
                 fontweight="bold")
    fig.tight_layout()
    path = FIG_DIR / "fig-08_shap-importance.pdf"
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"fig-08 -> {path.name}")


# ── tab-02: model comparison table ──────────────────────────────────────────
def table_model_comparison():
    p = ROOT / "research/experiments/EXP-009_model-ladder/outputs/summary.json"
    if not p.exists():
        return
    d = json.loads(p.read_text())
    rows = []
    for r in d["supervised"]["hmog_posture"]:
        rows.append({"Type": "Supervised", "Model": r["model"],
                     "PR-AUC": f"{r['prauc']:.3f}",
                     "SD": f"±{r.get('prauc_sd', 0):.3f}",
                     "ROC-AUC": f"{r.get('rocauc', 0):.3f}"})
    for model, val in d["unsupervised"]["hmog_posture"].items():
        if model == "n_subjects":
            continue
        rows.append({"Type": "Unsupervised", "Model": model,
                     "PR-AUC": f"{val:.3f}", "SD": "—", "ROC-AUC": "—"})
    df = pd.DataFrame(rows)
    path = TAB_DIR / "tab-02_model-comparison.csv"
    df.to_csv(path, index=False)
    print(f"tab-02 -> {path.name}")


if __name__ == "__main__":
    print("Generating figures...")
    fig_icc()
    fig_convergence()
    fig_per_subject()
    fig_drift()
    fig_model_ladder()
    fig_shap()
    table_model_comparison()
    print("\nDone. See results/figures/ and results/tables/")

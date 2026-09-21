"""Generate figures that depend on EXP-011/012/013/014 outputs.

    python scripts/generate_figures_part2.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "results" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

INK = "#0E1320"; PAPER = "#F5F6F8"; ACCENT = "#1F3B73"
SAGE = "#4A7C6F"; AMBER = "#B5893E"; RUST = "#A3442E"; MID = "#8A9BB5"

plt.rcParams.update({
    "figure.facecolor": PAPER, "axes.facecolor": PAPER,
    "axes.edgecolor": INK, "text.color": INK, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK, "font.family": "sans-serif",
    "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
    "grid.alpha": 0.3, "grid.color": MID,
})


def fig_pca_sweep():
    p = ROOT / "research/experiments/EXP-011_pca-component-sweep/outputs/pca_sweep.csv"
    if not p.exists():
        print("fig-09: skipped (EXP-011 not run)")
        return
    df = pd.read_csv(p)
    fig, ax1 = plt.subplots(figsize=(7, 4))
    ax2 = ax1.twinx()
    ax2.spines["right"].set_visible(True)
    ax1.plot(df.k, df.prauc_pooled, "o-", color=ACCENT, lw=2, label="PR-AUC (pooled/global)")
    ax1.plot(df.k, df.prauc_personal, "s--", color=SAGE, lw=2, label="PR-AUC (personal)")
    ax2.plot(df.k, df.explained_var, "^:", color=AMBER, lw=1.5, label="Variance explained")
    ax1.axvline(8, color=RUST, lw=1.5, ls="--", alpha=0.7, label="k=8 (current SPEC)")
    ax1.set_xlabel("PCA components (k)")
    ax1.set_ylabel("PR-AUC")
    ax2.set_ylabel("Cumulative variance explained")
    ax2.set_ylim(0, 1.05)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc="lower right")
    ax1.set_title("fig-09  PCA Component Sweep (HMOG sit->walk)", fontweight="bold")
    ax1.grid(axis="y")
    fig.tight_layout()
    path = FIG_DIR / "fig-09_pca-sweep.pdf"
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"fig-09 -> {path.name}")


def fig_session_aggregation():
    p = ROOT / "research/experiments/EXP-014_session-aggregation/outputs/summary.json"
    if not p.exists():
        print("fig-10: skipped")
        return
    d = json.loads(p.read_text())
    ws = [r["window"] for r in d["sweep"]]
    prauc = [r["prauc"] for r in d["sweep"]]
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.plot(ws, prauc, "o-", color=ACCENT, lw=2)
    ax.set_xlabel("Window size (gestures aggregated)")
    ax.set_ylabel("PR-AUC")
    ax.set_xticks(ws)
    ax.set_xticklabels([f"w={w}" for w in ws])
    ax.set_title("fig-10  Session Aggregation (PCA Reconstruction, HMOG sit->walk)", fontweight="bold")
    ax.grid(axis="y")
    fig.tight_layout()
    path = FIG_DIR / "fig-10_session-aggregation.pdf"
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"fig-10 -> {path.name}")


def fig_gmm_comparison():
    p = ROOT / "research/experiments/EXP-013_per-user-gmm/outputs/summary.json"
    if not p.exists():
        print("fig-11: skipped")
        return
    d = json.loads(p.read_text())["results"]
    datasets = list(d.keys())
    labels = ["HMOG\nsit->walk", "Synthetic\nperson-relative", "Synthetic\npop-consistent"]
    scorers = ["mah", "gmm2", "gmm3"]
    scorer_labels = ["Mahalanobis", "GMM-2", "GMM-3"]
    colors = [ACCENT, SAGE, AMBER]

    x = np.arange(len(datasets))
    width = 0.25
    fig, ax = plt.subplots(figsize=(8, 4))
    for i, (sc, lbl, col) in enumerate(zip(scorers, scorer_labels, colors)):
        vals = [d[ds][sc] for ds in datasets]
        ax.bar(x + i * width, vals, width, label=lbl, color=col, alpha=0.85)

    ax.set_xticks(x + width)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Median FPR at 80% sensitivity (lower = better)")
    ax.set_title("fig-11  Per-User GMM vs Single-Gaussian (Mahalanobis)", fontweight="bold")
    ax.legend()
    ax.grid(axis="y")
    fig.tight_layout()
    path = FIG_DIR / "fig-11_gmm-comparison.pdf"
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"fig-11 -> {path.name}")


def fig_feature_selection():
    p = ROOT / "research/experiments/EXP-012_feature-selection/outputs/summary.json"
    if not p.exists():
        print("fig-12: skipped")
        return
    d = json.loads(p.read_text())
    rows = d["sweep"]
    labels = [r["label"] for r in rows]
    prauc  = [r["prauc"] for r in rows]
    colors = [SAGE if r["k"] == "full" else ACCENT for r in rows]
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.bar(range(len(labels)), prauc, color=colors, alpha=0.85)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("PR-AUC (LogR, subject-wise 5-fold)")
    ax.set_ylim(0.5, 0.6)
    ax.set_title("fig-12  Feature Selection by SHAP Rank (HMOG sit->walk)", fontweight="bold")
    ax.axhline(d["full_prauc"], color=RUST, lw=1.5, ls="--", alpha=0.7, label=f"full set ({d['full_prauc']:.3f})")
    ax.legend(fontsize=8)
    ax.grid(axis="y")
    import matplotlib.patches as mpatches
    patch1 = mpatches.Patch(color=ACCENT, label="SHAP top-k")
    patch2 = mpatches.Patch(color=SAGE, label="Full set")
    ax.legend(handles=[patch1, patch2], fontsize=8)
    fig.tight_layout()
    path = FIG_DIR / "fig-12_feature-selection.pdf"
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"fig-12 -> {path.name}")


if __name__ == "__main__":
    print("Generating part-2 figures...")
    fig_pca_sweep()
    fig_session_aggregation()
    fig_gmm_comparison()
    fig_feature_selection()
    print("Done.")

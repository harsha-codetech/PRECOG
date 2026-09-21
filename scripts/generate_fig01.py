"""
fig-01 — PRECOG pipeline architecture diagram
Saves to results/figures/fig-01_pipeline-architecture.pdf and .png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
from pathlib import Path

OUT = Path(__file__).parent.parent / "results" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

# ── design tokens ─────────────────────────────────────────────────────────────
INK    = "#0E1320"
PAPER  = "#F5F6F8"
ACCENT = "#1F3B73"
SAGE   = "#4A7C6F"
AMBER  = "#B5893E"
RUST   = "#A3442E"
GREY   = "#8A95A8"
LIGHT  = "#D8DCE6"

fig, ax = plt.subplots(figsize=(14, 7))
fig.patch.set_facecolor(PAPER)
ax.set_facecolor(PAPER)
ax.set_xlim(0, 14)
ax.set_ylim(0, 7)
ax.axis("off")

# ── helpers ───────────────────────────────────────────────────────────────────
def box(ax, x, y, w, h, color, label, sublabel=None, fontsize=9, radius=0.18):
    rect = FancyBboxPatch((x, y), w, h,
                          boxstyle=f"round,pad=0,rounding_size={radius}",
                          linewidth=1.2, edgecolor=color,
                          facecolor=color + "22")
    ax.add_patch(rect)
    cy = y + h / 2 + (0.12 if sublabel else 0)
    ax.text(x + w/2, cy, label, ha="center", va="center",
            fontsize=fontsize, fontweight="bold", color=INK)
    if sublabel:
        ax.text(x + w/2, y + h/2 - 0.22, sublabel, ha="center", va="center",
                fontsize=7, color=GREY)

def arrow(ax, x1, y1, x2, y2, color=GREY):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color,
                                lw=1.3, mutation_scale=12))

def label(ax, x, y, text, color=GREY, fs=7.5, ha="center"):
    ax.text(x, y, text, ha=ha, va="center", fontsize=fs, color=color,
            style="italic")

# ── title ─────────────────────────────────────────────────────────────────────
ax.text(7, 6.72, "PRECOG — Detection Pipeline", ha="center", va="top",
        fontsize=13, fontweight="bold", color=INK)
ax.text(7, 6.42, "From raw scroll events to ordered behavioural state",
        ha="center", va="top", fontsize=8.5, color=GREY)

# ── row 1: data sources (y=4.9) ───────────────────────────────────────────────
box(ax, 0.3,  4.8, 2.1, 0.9, ACCENT, "HMOG Dataset",   "100 users · 40k gestures", 8)
box(ax, 2.6,  4.8, 2.1, 0.9, ACCENT, "FETA Dataset",   "470 users · scale repl.",  8)
box(ax, 4.9,  4.8, 2.1, 0.9, ACCENT, "Android Device", "AccessibilityService",     8)

# bracket label
ax.text(3.5, 5.85, "Data Sources", ha="center", fontsize=8, color=ACCENT, fontweight="bold")
ax.plot([0.3, 7.0], [5.78, 5.78], lw=0.8, color=ACCENT, alpha=0.4)

# ── row 2: feature extraction (y=3.3) ─────────────────────────────────────────
box(ax, 0.5,  3.2, 2.8, 0.9, SAGE, "Feature Extractor",
    "28 Touchalytics + 4 timing", 8.5)
box(ax, 3.6,  3.2, 2.8, 0.9, SAGE, "Context Segmenter",
    "app × time-of-day cells", 8.5)

# arrows: data → features
arrow(ax, 1.38, 4.8, 1.38, 4.12)
arrow(ax, 3.65, 4.8, 3.35, 4.12)
arrow(ax, 5.95, 4.8, 4.48, 4.12)

# ── row 3: baseline model (y=1.75) ────────────────────────────────────────────
box(ax, 0.5,  1.65, 2.1, 0.95, AMBER, "BaselineEngine",
    "Enrolment (n ≥ 80 gestures)", 8.5)
box(ax, 2.8,  1.65, 2.5, 0.95, AMBER, "GMM-2 / cell",
    "Tier 2: density (k=2 default)", 8.5)
box(ax, 5.5,  1.65, 2.4, 0.95, AMBER, "PCA Reconstruction",
    "Tier 3: k=8, 85% variance", 8.5)

# arrows: feature → baseline
arrow(ax, 1.9, 3.2, 1.9, 2.62)
arrow(ax, 4.52, 3.2, 3.9, 2.62)
arrow(ax, 4.52, 3.2, 6.7, 2.62)

# empirical-bayes note
ax.text(0.5, 1.56, "Empirical-Bayes shrinkage across context cells",
        ha="left", fontsize=6.8, color=AMBER, style="italic")

# ── row 4: deviation scoring (y=0.4) ──────────────────────────────────────────
box(ax, 0.5,  0.35, 2.1, 0.95, RUST, "DeviationEngine",
    "Robust z-score per feature", 8.5)
box(ax, 2.8,  0.35, 2.5, 0.95, RUST, "Mahalanobis (attrib.)",
    "Tier 1: per-feature evidence", 8.5)
box(ax, 5.5,  0.35, 2.4, 0.95, RUST, "Session Aggregation",
    "Window majority vote", 8.5)

arrow(ax, 1.55, 1.65, 1.55, 1.32)
arrow(ax, 3.75, 1.65, 3.75, 1.32)
arrow(ax, 6.7,  1.65, 6.7,  1.32)

# ── right panel: ordered states (x=8.5..13.5, y=0.4..5.5) ────────────────────
ax.add_patch(FancyBboxPatch((8.4, 0.25), 5.3, 5.6,
             boxstyle="round,pad=0,rounding_size=0.2",
             linewidth=1, edgecolor=LIGHT, facecolor="white", alpha=0.6))
ax.text(11.05, 5.62, "Ordered Behavioural States", ha="center",
        fontsize=9, fontweight="bold", color=INK)

states = [
    ("NORMAL",      "#4A7C6F", "Baseline zone · no action"),
    ("ENGAGED",     "#1F3B73", "Long session + low passive ratio\n→ deliberate use, no alert"),
    ("DISTRACTED",  "#B5893E", "Mild deviation · ambient signal"),
    ("COMPULSIVE",  "#C07840", "Sustained deviation · soft nudge"),
    ("HIGH-RISK",   "#A3442E", "Severe deviation · intervention"),
]
for i, (name, col, desc) in enumerate(states):
    yy = 4.6 - i * 0.95
    box(ax, 8.7, yy, 2.0, 0.75, col, name, fontsize=8.5, radius=0.12)
    ax.text(10.85, yy + 0.375, desc, ha="left", va="center",
            fontsize=7.2, color=INK)
    if i < len(states) - 1:
        arrow(ax, 9.7, yy, 9.7, yy - 0.21, color=col)

# arrow from deviation → states
arrow(ax, 7.9, 0.82, 8.68, 2.6, color=RUST)
ax.text(8.05, 1.85, "score\n→ state", ha="center", fontsize=7, color=RUST,
        style="italic")

# evidence-required note
ax.text(8.7, 0.1, "evidence-required constraint: every state carries ranked per-feature deviations (σ)",
        ha="left", fontsize=6.5, color=RUST, style="italic")

# ── legend ────────────────────────────────────────────────────────────────────
legend_items = [
    mpatches.Patch(facecolor=ACCENT+"33", edgecolor=ACCENT, label="Data layer"),
    mpatches.Patch(facecolor=SAGE  +"33", edgecolor=SAGE,   label="Feature layer"),
    mpatches.Patch(facecolor=AMBER +"33", edgecolor=AMBER,  label="Baseline layer"),
    mpatches.Patch(facecolor=RUST  +"33", edgecolor=RUST,   label="Deviation layer"),
]
ax.legend(handles=legend_items, loc="lower left", fontsize=7.5,
          framealpha=0.7, ncol=4, bbox_to_anchor=(0.0, -0.02))

plt.tight_layout(pad=0.3)
for ext in ("pdf", "png"):
    p = OUT / f"fig-01_pipeline-architecture.{ext}"
    plt.savefig(p, dpi=180, bbox_inches="tight", facecolor=PAPER)
    print(f"Saved {p}")
plt.close()

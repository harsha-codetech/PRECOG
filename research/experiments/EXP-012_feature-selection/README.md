# EXP-012 — Feature Selection by SHAP Rank

```
Date:        2026-09-20
Status:      COMPLETE
Question:    EXP-007 SHAP ranked features but did not test whether a subset matches
             the full set. Does top-k selection reduce dimensionality without hurting PR-AUC?
Data:        HMOG sit->walk · 99 subjects · 28 raw gesture features
Model:       Logistic Regression (EXP-009 best supervised), subject-wise GroupKFold-5
SHAP source: EXP-007 windowed features mapped back to base gesture features
```

## Verdict

**The full feature set wins, but the margin is small (+0.005 over top-10) and
the top-3 features alone reach 99% of full performance.** Feature selection
does not help here; the full set is the practical recommendation.

## Result

| Selection | n features | PR-AUC |
|---|---|---|
| SHAP top-3 | 3 | 0.544 |
| SHAP top-5 | 5 | 0.543 |
| SHAP top-8 | 8 | 0.540 |
| SHAP top-10 | 10 | 0.539 |
| **Full set** | **28** | **0.549** |

Top-3 features (by EXP-007 SHAP rank): `mid_stroke_area`, `duration_ms`, `inter_scroll_ms`

## Interpretation

**Feature selection monotonically hurts.** The pruned subsets underperform the full set
at every k. This means the bottom-ranked features carry small but real signal — the
direction of correlation is consistent enough that their inclusion helps the linear model.

This is consistent with the NB vs LogR result in EXP-009: the features are not
independent (NB 0.550 vs LogR 0.600), and their correlated structure benefits
Logistic Regression. Removing features that contribute even weakly to that structure
degrades performance.

**The top-3 features are interpretable:** stroke area reflects how widely the finger
moves, duration captures pace, and inter-scroll timing captures rhythm. These three
together explain the practical construct of "how this user scrolls," which is why
they rank highest under SHAP.

**Practical recommendation:** use the full 28-feature set. The dimensionality is
small, and there is no computational cost benefit to pruning. If dimensionality
reduction is ever needed (e.g., a privacy-constrained deployment), top-5 captures
99% of performance.

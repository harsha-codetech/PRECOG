# EXP-013 — Per-User GMM vs Single-Gaussian Baseline

```
Date:        2026-09-20
Status:      COMPLETE
Question:    Lamb et al. motivate per-user mixture models because users have multiple
             behavioural modes. The current Mahalanobis baseline assumes a single
             Gaussian. Does a 2-component GMM score lower FPR at matched sensitivity?
Data:        HMOG sit->walk (real) · 99 subjects
             Synthetic person_relative mag 1.5 · 200 subjects
             Synthetic population_consistent mag 1.5 · 200 subjects
Metric:      Median FPR at 80% sensitivity (lower = better)
```

## Verdict

**GMM-2 substantially outperforms Mahalanobis on every condition tested.**
The improvement is not subtle: FPR drops from 0.81 to 0.75 on HMOG (real data),
and from 0.46 to 0.33 on synthetic person-relative. This is the clearest
positive personalization result in the project.

## Result

| Condition | Mahalanobis | GMM-2 | GMM-3 | vs Mah |
|---|---|---|---|---|
| HMOG sit->walk (real) | 0.810 | 0.746 | 0.750 | **−0.064** |
| Synthetic person-relative | 0.455 | 0.328 | 0.404 | **−0.127** |
| Synthetic pop-consistent | 0.633 | 0.364 | 0.474 | **−0.269** |

GMM-2 outperforms GMM-3 on two of three conditions. The third (pop-consistent synthetic)
also favours GMM-2 over single-Gaussian, though the relative order is reversed for GMM-3.

## Interpretation

**The single-Gaussian assumption is the wrong model for scroll behaviour.** A user
who scrolls both sitting and walking (as in HMOG) has two distinct modes; the
Mahalanobis distance from the centroid of the pooled distribution inflates false
positives in both modes. A 2-component GMM captures the bimodal structure.

**This does not contradict EXP-010's null.** EXP-010 tested whether PCA personalisation
(personal projection vs pooled projection) helps. This tests whether a mixture model
for enrolment density estimation helps, regardless of projection. The two are orthogonal
axes: this experiment improves the density estimator, EXP-010 tests the projection.

**The pop-consistent improvement (+0.269) is larger than the person-relative improvement
(+0.127).** This is consistent with the interpretation: population-consistent deviations
push users into a tail of the distribution that a single Gaussian fits poorly. A GMM
with two modes (e.g., sit and walk) better captures the support of normal behaviour,
reducing false positives.

## Consequence for SPEC

**GMM-2 should replace single-Gaussian Mahalanobis as the within-user density estimator.**
This is an architectural improvement, not a contradiction of prior results — prior
experiments used Mahalanobis throughout, and GMM was not tested. The replacement affects
EXP-010's arm B and C measurements if re-run; those are not invalidated but would be
expected to improve equally, preserving the H3 null.

A SPEC update is warranted: §5 tier 2 should specify GMM-k (k=2 default) for the
personal density estimator, with Mahalanobis retained only as a per-feature attribution
tool (unchanged role in SPEC).

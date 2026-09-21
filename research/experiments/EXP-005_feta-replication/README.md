# EXP-005a — H5.3: do H1 and H2 replicate on FETA?

```
Date:        2026-09-20
Status:      CONFIRMATORY — pre-registered, no deviation (D1 and D2 do not apply here)
Dataset:     FETA · 288,124 gestures · 138 subjects · median 30 sessions each · 31 days
Comparison:  HMOG · 39,556 gestures · 99 subjects · 8 sessions each · short window
Versions:    features-v0.1 · baseline-v0.1
```

## Verdict

**H1 replicates almost exactly. H2 does not — and the failure is more informative than the success.**

---

## H1 — individual distinctiveness: replicated

| Measure | FETA (138 users) | HMOG (99 users) |
|---|---|---|
| Single-gesture top-1 | **14.9%** (20.5× chance) | 15.0% (14.8× chance) |
| Separability AUC | **0.802** | 0.787 |
| Closer to own centroid | **88.9%** | 88.5% |
| Median ICC | 0.105 | 0.161 |

Two independent datasets — different devices, different decade, different task, different
participants — land within **0.1 percentage points** on top-1 accuracy and 0.015 on AUC. That is not
a coincidence; it is a stable property of scroll behaviour.

**Top feature by ICC is `mid_stroke_area` (0.530)** — contact area. Touchalytics independently ranks
mid-stroke area **first** by mutual information (20.58%). A 2013 finding, reproduced here on 2020
data with a different method.

### The per-user spread replicates, and widens

```
FETA : median 7.0%   worst 0.0%   best 84.7%
HMOG : median 9.8%   worst 0.0%   best 65.9%
```

**This is the strongest finding in the project.** Some people have a highly distinctive scroll
signature; others have none at all. It now holds across two datasets, so it is a property of the
population rather than a quirk of one 2014 lab study.

It is also the empirical basis for the UX design: the *"not enough pattern"* state and
confidence-as-drawn-geometry exist because a meaningful fraction of users genuinely cannot be
served a confident deviation score.

---

## H2 — baseline convergence: did NOT replicate

| n gestures | FETA median ρ | HMOG median ρ |
|---|---|---|
| 20 | 0.747 | 0.890 |
| 80 | 0.787 | **0.944** |
| 150 | 0.879 | 0.985 |
| 200 | **0.919** | 0.984 |

**FETA never reaches ρ ≥ 0.95 within the grid.** HMOG reached it at n = 80.

### Why — and why this matters

The difference is the **collection window, not the number of gestures**. HMOG gives each subject
8 sessions over a short period; FETA gives ~30 sessions across **31 days**. A baseline fitted on a
user's first 80 gestures is being asked to predict their behaviour a month later, and it degrades.

**HMOG's fast convergence was an artifact of a short collection window.** EXP-002's headline —
*"baselines converge at n = 80 ≈ 2 sessions"* — is optimistic and must be corrected. The FETA curve
is still rising at n = 200 (0.919), so baselines converge **more slowly**, not never.

### Consequences

1. **EXP-002's convergence claim is superseded.** The paper must report the FETA figure, with HMOG's
   as the short-window comparison. Reporting only the flattering number would be indefensible.
2. **Baseline adaptation is now empirically necessary, not just prudent.** `SPEC.md` §5 already
   specifies EWMA adaptation at α = 0.05; this is the evidence for why a static baseline fails.
3. **The UX "learning mode" exit rule needs rethinking.** Gating on stability rather than elapsed
   days was the right instinct, but stability itself drifts — the baseline should keep updating
   after learning mode ends rather than freezing.
4. **Any future convergence claim must state its observation window.** A convergence number without
   the span it was measured over is meaningless.

---

## Pre-registration compliance

- H5.3 was run exactly as specified: enrolment fixed at n = 80 from EXP-002, contiguous splits,
  Mahalanobis-preferring scorer, no retuning on FETA.
- Deviation **D1** (orientation excluded — constant in FETA) applies to the feature set and was
  logged before the run.
- Deviation **D2** does not apply: H5.3 needs no behavioural contrast.
- **H5.1 and H5.2 remain UNTESTABLE on FETA**, as pre-specified. The scroll-vs-swipe analysis is
  exploratory only and is reported separately.

---

## EXP-005b — drift diagnostic (exploratory)

**A · window-matched.** Restricting FETA to each user's first 8 sessions (median span 7.0 days,
matching HMOG) improves convergence at every n:

| n | full 31d | matched 8 sessions | Δ |
|---|---|---|---|
| 80 | 0.787 | 0.889 | +0.102 |
| 150 | 0.879 | 0.937 | +0.058 |
| 200 | 0.919 | **0.969** | +0.050 |

ρ ≥ 0.95 is reached at **n = 200 window-matched**, never at full span. HMOG reached it at n = 80.

**So the window explains part of the gap, not all of it.** One honest caveat: the convergence target
is correlation with the *full-enrolment* baseline, which in FETA is built from ~2,000 gestures versus
HMOG's ~300. Converging to a better-estimated target is intrinsically harder, so the residual gap is
partly a measurement artifact rather than a property of the data.

**B · deviation vs elapsed time.** Enrol on the first 80 gestures, then score later gestures binned
by days since enrolment:

| days since enrolment | median deviation | vs first bin |
|---|---|---|
| 0–1 | 0.742 | 1.000 |
| 3–7 | 0.791 | 1.066 |
| 7–14 | 0.801 | 1.080 |
| 14–21 | 0.822 | 1.108 |
| 21–32 | **0.833** | **1.123** |

Monotonic across all six bins and 138 subjects. **Spearman(days, deviation) = +0.041, p = 1.3e-104.**

**Drift is real, and modest.** The p-value is driven by n = 277,000 — with that many gestures almost
anything is significant, and ρ = 0.041 is a small correlation. The number that matters is the
**+12% rise in median deviation over 30 days**. A static baseline degrades gradually rather than
catastrophically, which is exactly the regime slow EWMA adaptation (α = 0.05) is designed for.

---

## EXP-005c — scroll → swipe contrast (EXPLORATORY, per deviation D2)

> ## ⚠ WITHDRAWN — contrast invalid (EXP-007, 2026-09-20)
>
> SHAP revealed this contrast is confounded by **gesture type, not behaviour**. Reading is 98%
> vertical; map navigation 48%. Scroll feed is 99.2% vertical; swipe gallery 1.7%. A trained
> classifier reaches **PR-AUC 1.000** on both, and removing the direction features does not fix it —
> the leakage relocates to start position and straightness.
>
> **These are different gesture types, not behavioural deviations.** The comparisons below cannot
> test personalization and the conclusions are withdrawn. Retained for the record, not for citation.
> See `EXP-007_models/README.md`.

> **Not confirmatory.** H5.1 and H5.2 remain untestable as pre-specified. Nothing below supports a
> confirmatory claim about personalization.

FETA scroll (normal) vs swipe/image-gallery (behavioural change), 138 subjects, FPR at 80%
sensitivity:

| Model | FPR |
|---|---|
| **A — fixed univariate threshold** | **0.299** |
| B — global multivariate | 0.617 |
| C — personalized | 0.484 |

| Comparison | Δ | p | Cliff's δ | favouring first |
|---|---|---|---|---|
| **C − B** | **−0.104** | **6.5e-11** | **−0.411** | **79%** |
| C − A | +0.244 | 1.9e-19 | +0.627 | 12% |
| B − A | +0.343 | 2.5e-23 | +0.876 | 6% |

**The clearest personalization signal in the project** — personalized beats global for 79% of
subjects with a medium effect size, on 138 users. Had this been confirmatory it would have supported
H5.1.

**But the ordering replicates for a third time: A < C < B.** The single-feature threshold beats the
personalized model by a *larger* margin (δ = +0.63) than personalization beats the global model.
Across HMOG sit→walk, HMOG reading→map, and now FETA scroll→swipe, **feature selection has mattered
more than personalization every single time.**

## Next

1. **EXP-007 — feature selection.** Now the highest-value open question: which features carry the
   deviation, and can they be selected per-user? Three contrasts now point at it.
2. Pre-register EXP-005c properly and re-test on held-out users, since the exploratory result is
   strong enough to deserve a confirmatory test rather than a footnote.
3. Update `docs/PLAN.md`: the convergence claim now carries a window qualifier.

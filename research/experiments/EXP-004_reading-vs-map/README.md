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

# EXP-004 — does the EXP-003 null hold on a second behavioural contrast?

```
Date:        2026-09-20
Question:    EXP-003 found no personalization benefit on sit->walk. Posture changes scroll
             behaviour in a population-consistent way, which could explain the null. Does
             a different kind of real behavioural change give a different answer?
Contrast:    enrol on READING sessions, detect MAP NAVIGATION (both real, both labelled)
Dataset:     reading 39,556 gestures · map 145,000+ gestures · 98 subjects
Versions:    features-v0.1 · baseline-v0.1
```

## Verdict

**Personalization beats global here (p = 0.044) — but the finding that replicates across both
contrasts is that a single fixed threshold beats both multivariate models, decisively.**

## Result

**FPR at 80% sensitivity · n = 98 · lower is better**

| Model | reading→map | *(sit→walk, EXP-003)* |
|---|---|---|
| **A — one fixed threshold** | **0.394** | *0.712* |
| B — global multivariate | 0.631 | *0.825* |
| C — personalized | 0.597 | *0.821* |

| Comparison | Δ median | p | Cliff's δ | favouring first |
|---|---|---|---|---|
| **C − A** | **+0.150** | **1.7e-07** | +0.390 | 20% |
| **C − B** | **−0.045** | **0.044** | −0.123 | 58% |
| B − A | +0.207 | 4.3e-09 | +0.474 | 24% |

## Interpretation

**Personalization over global is inconsistent.** Absent on sit→walk (p = 0.33), small but nominally
significant on reading→map (p = 0.044, δ = −0.123). Two contrasts have now been tested, so a Holm
correction puts this at **p ≈ 0.089 — not significant**. The honest description is a weak,
contrast-dependent effect, not a reliable benefit.

**The replicated finding is different, and larger.** In both contrasts a **threshold on one feature
beat both multivariate models** by a wide margin (δ = +0.39 and +0.31 against personalized). This is
not a marginal effect and it does not depend on the contrast.

The likely mechanism is the same one that broke the first scorer in EXP-003: **signal dilution.**
`average_velocity` maps almost directly onto the reading/map distinction. Spreading the decision
across 29 features — most irrelevant to this particular change — buries it. Mean-z over 29 features
gave AUC 0.545 where Mahalanobis over 6 gave 0.868; reducing further to the single relevant feature
helps again.

**This points at feature selection, not personalization**, as the lever that matters. A parsimonious
model on the right features outperforms a rich model on everything, and PRECOG currently has no
feature-selection step at all.

## Consequences

1. **Keep the simple baseline in every comparison, permanently.** It has now won twice. Any claim
   that multivariate deviation helps carries a burden of proof this project has not met.
2. **The personalization claim stays unsupported.** One nominal p = 0.044 that does not survive
   correction is not evidence.
3. **New candidate direction: per-contrast feature selection.** The interesting question is no longer
   "does personalization help?" but "which features carry the deviation, and can they be chosen
   per-user?" That is testable and currently unexplored.
4. **The FETA pre-registration stands unchanged.** It was sealed before this run; EXP-004 does not
   license editing it.

## Data-quality findings

Map sessions are dirtier than reading sessions, in two ways not present in reading:
- rows with **non-finite `ActivityID`** — dropped and counted, never coerced
- **truncated lines** (e.g. 12 fields where 17 are expected), which left `Speed_X` mixed-type

Both are now handled in `precog/io/hmog.py` by unconditional numeric coercion on read, so the damage
is confined to NaNs in affected rows. Reading-only extractions are unaffected.

# EXP-008 — mechanism test: when does personalization help?

```
Date:        2026-09-20
Status:      SYNTHETIC — a mechanism test, NOT evidence that PRECOG works on people
Question:    EXP-003 found no personalization benefit and proposed a reason — walking changes
             behaviour in a population-consistent way, so a global model already captures it.
             That was inferred from a null. This tests it directly.
Generator:   synth-v0.1 · 200 users · 30 sessions each · 30 days · 472,842 gestures
             population means, between-user spread and within-user covariance FITTED FROM
             FETA (288,124 real gestures, 138 subjects) so correlations are realistic
Seed:        20260920
```

> ## ⚠ PARTIALLY SUPERSEDED — scorer-dependent (EXP-010, 2026-09-20)
>
> The sign flip below was measured with **Mahalanobis**, which EXP-009 showed is the weaker
> detector. Re-run with **PCA reconstruction** (EXP-010), the effect largely collapses: the sign
> reverses on population-consistent (−0.011, p=0.023) and becomes non-significant on person-relative
> (−0.005, p=0.24).
>
> **Cause:** a strong global detector leaves little for personalization to add. Global-PCA reaches
> 0.510 on person-relative where global-Mahalanobis reaches 0.651, so the gap Mahalanobis showed was
> partly compensating for its own weakness as a global model.
>
> **What survives:** the *direction* — every detector tested handles person-relative deviations
> better than population-consistent ones. **What does not:** the magnitude and reliability of the
> personalization gap, which is what the sign flip was taken to demonstrate.


## Verdict

**Confirmed. Personalization helps if and only if the deviation is person-relative.** The sign of
the effect flips cleanly between the two conditions, at every magnitude.

## Design

Two anomaly types, identical in every respect except what scales them:

| Type | Shift applied | Meaning |
|---|---|---|
| `population_consistent` | `magnitude × τ_f` | the same physical change for every user |
| `person_relative` | `magnitude × σ_uf` | scaled to each user's own spread |

Everything else is held constant — the same users, same baselines, same features, same affected
sessions. Only the scaling differs.

## Result

**FPR at 80% sensitivity · C−B negative means personalization wins**

| Anomaly type | mag | B global | C personal | **C−B** | p | Cliff's δ |
|---|---|---|---|---|---|---|
| population_consistent | 0.5 | 0.786 | 0.792 | **+0.009** | 7.1e-06 | +0.169 |
| population_consistent | 1.0 | 0.779 | 0.790 | **+0.014** | 1.3e-08 | +0.221 |
| population_consistent | 1.5 | 0.771 | 0.789 | **+0.021** | 2.3e-12 | +0.259 |
| population_consistent | 2.0 | 0.764 | 0.785 | **+0.026** | 4.9e-14 | +0.283 |
| person_relative | 0.5 | 0.749 | 0.735 | **−0.009** | 0.15 | −0.114 |
| person_relative | 1.0 | 0.694 | 0.651 | **−0.041** | 2.3e-04 | −0.234 |
| person_relative | 1.5 | 0.651 | 0.586 | **−0.071** | 3.1e-05 | −0.268 |
| person_relative | 2.0 | 0.600 | 0.547 | **−0.073** | 3.8e-04 | −0.220 |

**Every population-consistent row is positive. Every person-relative row is negative.** The
magnitude of the effect grows with anomaly severity in both directions.

**XGBoost, subject-wise 5-fold, magnitude 1.5:**

| Anomaly type | PR-AUC | prevalence |
|---|---|---|
| population_consistent | 0.611 ± 0.028 | 0.302 |
| **person_relative** | **0.889 ± 0.016** | 0.302 |

Person-relative deviations are far more learnable — consistent with the deviation arms.

## Interpretation

**EXP-003's explanation is no longer an inference.** Personalization is not weakly useful or
contrast-dependent by accident: it is *conditionally* useful, and the condition is now specified.

> A personal baseline adds information only when "normal" differs between people **and** the
> deviation is meaningful relative to that personal normal. When a change pushes everyone in the
> same direction by the same amount, a global model already accounts for it and a personal baseline
> is strictly worse — it spends its degrees of freedom modelling variation that is irrelevant to the
> decision.

This reframes every real-data result in the project:

- **sit → walk** (EXP-003, null) — walking degrades everyone's motor control similarly.
  **Population-consistent. Personalization correctly did not help.**
- **reading → map** (EXP-004, p=0.044) — partly task-driven, partly individual. **Mixed.**
- **scroll → swipe** (EXP-005c, 79% of subjects) — gesture repertoire differs strongly per person.
  **Closer to person-relative. Personalization helped most.**

The ordering of those three real results matches the synthetic prediction.

## Consequence for PRECOG

**The open empirical question is now sharp and answerable:** *is compulsive scrolling a
person-relative or a population-consistent deviation?*

If person-relative, personalization is the right architecture and this project's premise holds. If
population-consistent, a global model is better and PRECOG's central design choice is wrong.

No dataset can answer that yet — it needs compulsive-use labels, which do not exist publicly. But
the question is now precise enough to design a study around, which it was not before.

## Honest caveats

1. **Synthetic results are not evidence about people.** This tests whether the *detector* behaves as
   theory predicts, nothing more.
2. **The A arm (fixed threshold) is circular here**, exactly as in EXP-003 arm 1 — the shift is
   specified in feature space and A watches those features. Its numbers are reported for continuity
   but carry no information. **The C−B comparison is not circular**: both arms are multivariate
   models over identical features, and the manipulation changes only the *scaling* of the shift.
3. The generator assumes Gaussian within-user variation around a drifting mean. Real behaviour is
   heavier-tailed and likely multimodal (Lamb et al. motivate mixtures for exactly this reason).
4. `affected_fraction` is fixed at 30%; real compulsive episodes are likely rarer, which would make
   detection harder for every arm.

## Next

1. Sweep `kappa_sd` to find how much between-user variation is needed before personalization pays —
   gives a concrete design threshold rather than a binary answer.
2. Replace the Gaussian within-user model with a mixture and check the conclusion survives.
3. Use this generator for the power analysis the FETA pre-registration flagged as underpowered.

# EXP-005 — Pre-registration: FETA replication

```
Written:     2026-09-20
Status:      SEALED — written before the FETA raw data was available on this machine
Analyst:     analysis plan fixed prior to any inspection of FETA scroll trajectories
```

> This document exists to be checked against later. Every decision below is fixed **now**, while
> the outcome is unknown. Any departure from it in the final analysis must be reported as a
> deviation, with its reason, not quietly absorbed.

## Why pre-register this one

EXP-006 produced a non-significant trend suggesting personalization may help highly distinctive
users (top quartile: C−B = −0.019, 67% of subjects, p = 0.117, n = 21). That is a hypothesis, and it
is exactly the kind that becomes a false positive when tested flexibly on new data.

FETA has **470 users versus HMOG's 82** — roughly 5× the power. That makes it the right place to
test the hypothesis, and the wrong place to go looking for one.

## Hypotheses

**H5.1 (primary).** Among users in the top quartile of behavioural distinctiveness, a personalized
baseline yields a lower false-positive rate than a global baseline at matched sensitivity.

**H5.2 (secondary).** Distinctiveness correlates negatively with (FPR_personalized − FPR_global)
across all users — i.e. the advantage scales with how distinctive a person is.

**H5.3 (replication).** H1 and H2 replicate: scroll kinematics are individually distinctive, and
personal baselines converge within a bounded number of gestures.

## Data and preprocessing — fixed in advance

- **Source.** FETA `data_files.zip` touch CSVs, **scroll gametype only**. Swipe (image gallery) is
  excluded.
- **Cohort.** Users with ≥ 20 scroll sessions (the long arm). From `tables.zip` this is expected to
  be ~138 users; the actual number is whatever the data yields and will be reported.
- **Device.** FETA mixes iPhone models (FETA pitfall P2, 3.2–5.8 pp EER effect). Phone model will be
  included as a covariate and, if a single model has ≥ 50 users, a single-model sensitivity analysis
  will be reported.
- **Features.** The shared set computed by `precog/features/touch.py`. **Pressure is excluded** —
  it is constant in HMOG, so including it would confound any HMOG↔FETA comparison. This exclusion is
  fixed regardless of how informative pressure turns out to be in FETA.
- **Cleaning.** Identical thresholds to HMOG: `min_samples = 3`, `duration ∈ [1, 10000] ms`. These
  are not retuned for FETA.

## Protocol — fixed in advance

- **Split.** Contiguous, never random (FETA pitfall P3). Enrolment = each user's earliest sessions;
  evaluation = their later sessions.
- **Enrolment size.** **n = 80 gestures**, carried over from EXP-002. Not re-derived on FETA.
- **Scorer.** `deviation` — Mahalanobis tier where available, robust-z fallback. Mean-z across all
  features is **not** used; EXP-003 showed it produces spurious positives (AUC 0.545 vs 0.868).
- **Sensitivity.** FPR compared at **80%** sensitivity, matching EXP-003 and EXP-006.
- **Distinctiveness.** Measured on FETA independently, by the EXP-001 method: nearest-centroid
  identification accuracy on held-out gestures. Quartiles computed within FETA.

## Anomaly definition

**The deviation must be a real, un-injected behavioural contrast with ground-truth labels**, as in
EXP-003 arm 2. Semi-synthetic injection is prohibited — EXP-003 arm 1 demonstrated it is circular
when the shift is specified in feature space.

If FETA contains no usable natural contrast, **H5.1 and H5.2 are not testable on FETA and will be
reported as untestable.** They will not be replaced with an injected substitute.

H5.3 does not require a contrast and is testable regardless.

## Statistical analysis — fixed in advance

- **Primary test.** Wilcoxon signed-rank on paired per-subject (FPR_personal, FPR_global) within
  the top distinctiveness quartile. Two-sided. **α = 0.05.**
- **Effect size.** Cliff's δ, reported alongside every p-value.
- **Secondary.** Spearman correlation between distinctiveness and (FPR_personal − FPR_global).
- **Multiple comparisons.** Exactly **two** confirmatory tests (H5.1, H5.2). Holm correction applied
  across both.
- **Strata.** Four quartiles, reported for completeness. **Only Q4 is confirmatory.** Q1–Q3 are
  descriptive and no claim rests on them.

## Stopping and decision rules

- Analysis is run **once** on the full eligible cohort. No interim looks, no adding or removing users
  after seeing results.
- **H5.1 supported** iff Wilcoxon p < 0.05 after Holm correction **and** Cliff's δ favours
  personalization. Both conditions, not either.
- **H5.1 rejected** otherwise — including when the direction is right but p ≥ 0.05. A near-miss is a
  null result, not a trend worth narrating.
- No further stratification beyond the four pre-specified quartiles. No post-hoc subgroup search.

## What would falsify the personalization claim outright

If H5.1 fails on 470 users with adequate power, the personalization-benefit claim should be
**dropped from the paper**, not weakened into a suggestion. The contribution then rests on what is
already evidenced: baselines are learnable (EXP-001) and converge quickly (EXP-002).

## Expected power

At n ≈ 34 per quartile (138 long-arm users), a Wilcoxon signed-rank test has roughly 80% power to
detect a medium effect (Cliff's δ ≈ 0.35). It remains **underpowered for the small effect seen in
EXP-006** (δ ≈ 0.04). This is stated in advance so that a null is interpreted as "no medium effect
detected", not "no effect exists".

---

**Deviations log** — record any departure from the above, with date and reason.

**D1 · 2026-09-20 · `phone_orientation` excluded from the shared feature set.**
The plan specified "the shared set computed by `precog/features/touch.py`". FETA's touch CSVs
(`y, x, type, timestamp, pressure, area`) carry **no orientation field**, so the extractor passes a
constant 0. A constant column cannot contribute and would confound any HMOG↔FETA comparison in
exactly the way pressure would. It is therefore dropped from cross-dataset analysis.

*Impact: expected to be negligible.* EXP-001 found `phone_orientation` had the highest univariate
ICC (0.824) yet removing it slightly **improved** multivariate identification (top-1 15.0% → 15.2%),
i.e. it carries no independent information. Recorded because it is a departure, not because it is
consequential.

**Cohort confirmation · 2026-09-20.** The plan anticipated "~138 users" at the ≥20-scroll-session
threshold. The archive yields **exactly 138**. No adjustment to the inclusion rule was made.

**D2 · 2026-09-20 · scroll-vs-swipe contrast is EXPLORATORY, not confirmatory.**
FETA contains one candidate natural contrast: the scroll task (social-media feed search) versus the
swipe task (image gallery) — structurally the same design as EXP-004's reading-vs-map. But this plan
scoped the data source to "scroll gametype only, swipe excluded", so using swipe as the anomaly
class is a departure.

**Resolution.** The pre-specified rule stands: **H5.1 and H5.2 are reported as UNTESTABLE on FETA**,
because the contrast this plan authorised does not exist in the data. The scroll-vs-swipe analysis
will still be run, and reported **explicitly as exploratory** — it cannot support a confirmatory
claim, cannot be described as testing H5.1, and no conclusion about personalization rests on it.

Pre-registration does not forbid exploration; it forbids relabelling exploration as confirmation.
Recorded **before any FETA result was computed** — the extraction was still running when this was
written.

**H5.3 is unaffected** and remains fully confirmatory: it requires no contrast.

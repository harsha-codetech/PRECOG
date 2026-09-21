# EXP-003 — H3: personalized baseline vs global threshold

```
Date:        2026-09-20
Hypothesis:  H3 — at matched sensitivity a personalized baseline produces a lower
             false-positive rate than a global threshold. PRECOG's central claim.
Dataset:     hmog_gesture-features_features-v0.1 · 98 subjects (semi-synthetic arm),
             82 subjects (real-change arm)
Split:       enrol on first 80 gestures (from EXP-002), evaluate on the remainder
Versions:    features-v0.1 · baseline-v0.1 · seed 42
```

## Verdict

**H3 is NOT supported.** On a real behavioural change with real labels, personalization gave no
benefit over a global model, and both were significantly *worse* than a single fixed threshold.

---

## Arm 1 — semi-synthetic injection (design flawed, reported for transparency)

Injected a population-MAD-scaled shift on five kinematic features into held-out gestures.

| severity | A fixed threshold | B global multivariate | C personalized | C−A | C−B |
|---|---|---|---|---|---|
| 1.0 | **0.436** | 0.625 | 0.635 | +0.178 (p=4e-11) | −0.018 (p=0.25) |
| 1.5 | **0.325** | 0.507 | 0.536 | +0.189 (p=7e-09) | −0.012 (p=0.60) |
| 2.0 | **0.246** | 0.450 | 0.451 | +0.160 (p=7e-09) | +0.000 (p=0.88) |
| 3.0 | **0.175** | 0.337 | 0.293 | +0.112 (p=1e-08) | +0.006 (p=0.21) |

**This arm cannot test H3 and its numbers should not be used.** The anomaly was injected as an
additive shift along named features, and arm A is a threshold on one of those exact features — so A
wins by construction. This is the circularity that makes synthetic anomaly recovery invalid as
evidence, and it was designed in by mistake rather than caught in advance.

Kept in the record rather than deleted: the failure is instructive and deleting inconvenient runs is
how results stop being trustworthy.

## Arm 2 — real behavioural change (the valid test)

HMOG records posture per activity. **Sitting → walking is a genuine, un-injected behavioural change
with ground-truth labels.** Enrol on sitting, treat held-out sitting as normal and walking as the
deviation.

**82 subjects · FPR at 80% sensitivity · lower is better**

| Model | FPR |
|---|---|
| **A — fixed univariate threshold** | **0.712** |
| B — global multivariate | 0.825 |
| C — personalized baseline | 0.821 |

| Comparison | Δ median | p | Cliff's δ | subjects favouring the first |
|---|---|---|---|---|
| **C − A** | **+0.112** | **4.3e-07** | +0.379 | 28% |
| **C − B** | **+0.000** | **0.33** | +0.037 | 45% |
| B − A | +0.070 | 7.4e-06 | +0.313 | 28% |

## Interpretation

**Personalization added nothing over a global model** (C−B ≈ 0, p=0.33), and **both multivariate
models were significantly worse than one threshold on one feature** (C−A = +0.112, p=4e-07).

The likely reason is not a bug, and it matters:

> **Walking changes scroll behaviour in a population-consistent way.** Everyone gets shakier and
> slower in roughly the same direction. When a deviation affects everyone alike, a global model
> already captures it and a personal baseline has nothing left to add.

Personalization can only pay off when *normal itself differs between people* **and** the deviation
is meaningful only relative to that personal normal. Sit→walk satisfies the first condition but not
the second.

This does not falsify PRECOG's premise — it shows the premise is **untested**, because no available
dataset contains the kind of deviation the premise is about. EXP-001 already established that
personal normals genuinely differ (AUC 0.787). What remains unevidenced is that compulsive scrolling
presents as a *person-relative* deviation rather than a population-consistent one.

## Consequences for the paper

1. **The headline claim cannot be "personalization reduces false positives."** No supporting
   evidence exists, and one significant result points the other way.
2. **Reframe to what is actually evidenced:** personal scroll baselines are *learnable* (EXP-001)
   and *converge quickly* (EXP-002, n=80 ≈ 2 sessions). That is a real, modest, defensible
   contribution.
3. **Report the negative result prominently.** The blueprint anticipated exactly this
   ("if D−C ≈ 0, your personalization novelty is empirically unsupported"). Reporting it is what
   distinguishes a paper from a demo, and reviewers reward it.
4. **Simple baselines must stay in every future comparison.** A one-feature threshold beat two
   multivariate models here. Any claim that a complex model helps now carries a burden of proof.

## Also learned

**Scorer choice dominated the result.** An early version averaged robust-z across all 29 features
and reported personalization winning at every severity (p down to 4e-09). Switching to the
Mahalanobis tier that `SPEC.md` §5 actually specifies erased the effect entirely.

Diagnosis on one subject: **mean-z AUC 0.545 vs Mahalanobis AUC 0.868.** Averaging z over 29
features dilutes a 5-feature shift into noise. The apparent win was an artifact of a weak scorer, not
a property of personalization — a reminder to verify that a positive result survives a *better*
method before believing it.

## Next

1. **EXP-004** — repeat arm 2 with other real behavioural contrasts available in HMOG
   (reading vs map navigation), to test whether the null holds across change types.
2. **EXP-006** — stratify by per-user distinctiveness from EXP-001: does personalization help for
   the highly distinctive subjects even if it fails on average?
3. Update `docs/PLAN.md` H3 and the paper framing to match this result.
4. Do **not** pursue more synthetic-injection arms without an anomaly model that is not
   hand-specified in feature space.

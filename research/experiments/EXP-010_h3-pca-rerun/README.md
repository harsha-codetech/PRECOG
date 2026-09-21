# EXP-010 — H3 re-tested with the better detector

```
Date:        2026-09-20
Why:         EXP-003's null was measured with Mahalanobis, which EXP-009 then showed is the
             weaker detector (3rd of 4, beaten by PCA reconstruction on every condition).
             A null obtained with a weak instrument is not a settled null.
Data:        HMOG sit->walk (the only valid real contrast) · 94 subjects
             plus synthetic under both anomaly mechanisms · 200 subjects each
Arms:        B = global PCA fitted on all users' enrolment pooled
             C = personal PCA fitted on that user's enrolment alone
Versions:    features-v0.1 · 8 components · seed 42
```

## Verdict

**The H3 null survives the better detector — and EXP-008's mechanism turns out to be partly an
artifact of the weaker one.**

## Result

**FPR at 80% sensitivity · C−B negative means personalization wins**

### HMOG sit → walk (real)

| Scorer | B global | C personal | C−B | p | Cliff's δ |
|---|---|---|---|---|---|
| PCA reconstruction | 0.775 | 0.806 | +0.003 | **0.85** | +0.036 |
| Mahalanobis | 0.814 | 0.825 | +0.000 | 0.28 | +0.054 |
| *(A threshold)* | *0.750* | | | | |

**Null under both scorers.** EXP-003's conclusion holds: personalization gives no benefit on the one
valid real contrast, and that was not a weak-instrument artifact.

### Synthetic — and here the two scorers disagree

| Mechanism | Scorer | B global | C personal | C−B | p | Cliff's δ |
|---|---|---|---|---|---|---|
| population_consistent | PCA | 0.694 | 0.671 | **−0.011** | 0.023 | −0.152 |
| population_consistent | Mahalanobis | 0.771 | 0.789 | **+0.021** | 2.3e-12 | +0.259 |
| person_relative | PCA | 0.510 | 0.536 | **−0.005** | 0.24 | −0.037 |
| person_relative | Mahalanobis | 0.651 | 0.586 | **−0.071** | 3.1e-05 | −0.268 |

## The correction to EXP-008

EXP-008 reported a clean sign flip: personalization worse for population-consistent deviations,
better for person-relative ones, significant at every magnitude. **That pattern is substantially
scorer-dependent.**

Under PCA reconstruction the effect largely collapses — the sign actually *reverses* on
population-consistent (−0.011, p=0.023) and becomes non-significant on person-relative (−0.005,
p=0.24).

**Why: the global detector got much better.** Compare the B columns:

```
person_relative  ·  B global PCA 0.510   vs   B global Mahalanobis 0.651
```

A strong pooled model leaves little for personalization to add. **The apparent value of
personalization is partly a function of how weak your global baseline is.** Mahalanobis-global is a
poor detector, so personal-Mahalanobis looked valuable by comparison; PCA-global is strong, so
personal-PCA adds almost nothing.

This does not make EXP-008 wrong about the *mechanism* — every detector in EXP-009 still performed
markedly better on person-relative than population-consistent deviations. It makes EXP-008 wrong
about the **magnitude and reliability of the personalization gap**, which is what the sign flip was
taken to demonstrate.

**EXP-008's README is annotated accordingly.**

## The pattern worth naming

This is the third result in this project revised by a better method:

| | Original | After a better method |
|---|---|---|
| EXP-003 first pass | personalization wins at every severity, p→4e-09 | vanished under Mahalanobis (mean-z AUC 0.545 → 0.868) |
| EXP-004 / EXP-005c | personalization wins, 79% of subjects | withdrawn — contrast confounded by gesture direction (SHAP) |
| EXP-008 | clean mechanism sign flip, p<1e-5 throughout | largely collapses under PCA reconstruction |

**Every positive personalization result so far has failed to survive a stronger comparison.** Three
independent times, in three different ways. That consistency is itself evidence, and it points one
direction: **the personalization benefit this project set out to demonstrate has not been
demonstrated.**

## What stands

- **H1** — kinematics are individually distinctive, replicated across two datasets (14.9% vs 15.0%)
- **Per-user spread** — 0%–85%, replicated. Still the strongest finding
- **Drift** — +12% deviation over 30 days, monotonic
- **H3 — null**, now confirmed under the better detector
- **Mechanism direction** — all detectors handle person-relative deviations better than
  population-consistent ones, even though the personalization *gap* is small

## Next

1. Annotate EXP-008 with this correction *(done)*.
2. Update the paper framing: personalization is not the contribution. What survives is
   distinctiveness, its population spread, drift, and a well-characterised null.
3. If personalization is to be claimed at all, it needs a contrast that is valid, a detector that is
   strong, and an effect that survives both. None of the three attempts has cleared that bar.

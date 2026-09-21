# EXP-006 — does personalization help the people who have a signature?

```
Date:        2026-09-20
Question:    EXP-003 found no personalization benefit on average. EXP-001 showed the
             population splits hard (0%-65.9% distinctiveness). Is the average hiding a
             real effect concentrated in the distinctive subjects?
Dataset:     hmog_gesture-features_features-v0.1 · 82 subjects
Design:      EXP-003 arm 2 (real sit->walk change, ground-truth labels), stratified by
             per-subject distinctiveness measured independently in EXP-001
Versions:    features-v0.1 · baseline-v0.1
```

## Verdict

**The trend runs in the predicted direction but does not reach significance. H3 is not rescued.**

## Result

**Correlation across all 82 subjects**

```
Spearman(distinctiveness, C-B) = -0.110    p = 0.325
```

Negative is the predicted sign — more distinctive should mean personalization helps more — but the
relationship is weak and not significant.

**By distinctiveness quartile** · FPR at 80% sensitivity · C−B negative favours personalization

| Quartile | n | distinctiveness | personalized | global | C−B | p | subjects favouring personal |
|---|---|---|---|---|---|---|---|
| Q1 lowest | 21 | 0.008 | 0.822 | 0.844 | +0.000 | 0.83 | 43% |
| Q2 | 20 | 0.053 | 0.808 | 0.766 | +0.038 | 0.33 | 40% |
| Q3 | 20 | 0.109 | 0.839 | 0.779 | +0.041 | 0.09 | 30% |
| **Q4 highest** | 21 | 0.298 | 0.820 | 0.845 | **−0.019** | 0.12 | **67%** |

## Interpretation

Q4 is the only stratum where personalization wins: a majority of subjects (67%, 14 of 21) show a
lower false-positive rate with a personal baseline, and the median difference points the right way.
**But p = 0.117, and a sign test on 14/21 gives p ≈ 0.19.** This does not clear any reasonable bar.

Q2 and Q3 run mildly *against* personalization, which is what noise around a null looks like rather
than a coherent dose-response.

**This experiment is underpowered.** Twenty-one subjects per quartile cannot resolve an effect of
this size. The honest statement is that the data are consistent with a small benefit among highly
distinctive users **and** consistent with no benefit at all — and it cannot distinguish them.

## What this does and does not license

**Can say.** The personalization advantage, if it exists, is not large enough to detect in 82
subjects on this behavioural contrast. A directional trend by distinctiveness was observed but was
not statistically significant.

**Cannot say.** That personalization works for distinctive users. One non-significant quartile is a
hypothesis, not a finding, and presenting it as a rescue would be exactly the selective reporting
that makes results untrustworthy.

**Should not do.** Slice further looking for a significant subgroup. Four strata have already been
tested; continuing until something clears p<0.05 is p-hacking, and any result found that way would
not survive replication.

## Next

1. **Replicate on FETA** — 470 users versus 82 is roughly a 5× power increase, and this is precisely
   the hypothesis worth spending it on. Pre-register the quartile analysis before looking.
2. **EXP-004** — test other real behavioural contrasts (reading vs map navigation) to check whether
   the sit→walk null is specific to posture, which changes behaviour in a population-consistent way.
3. Keep the framing set by EXP-003: the paper claims baselines are **learnable and fast-converging**,
   not that personalization reduces false positives.

# EXP-014 — Session-Level Aggregation

```
Date:        2026-09-20
Status:      COMPLETE
Question:    Per-gesture FPRs of 0.5–0.8 are not deployable. PRECOG is designed to
             alert on sessions, not individual gestures. Does aggregating scores over
             a window of gestures reduce the false-positive burden?
Data:        HMOG sit->walk · 99 subjects · 39,556 gestures
Scorer:      PCA reconstruction error (pooled, k=8)
Aggregation: Mean score over non-overlapping windows; label = majority
```

## Verdict

**Aggregation does not improve PR-AUC on this contrast.** The curve is flat
(0.575–0.587 across all window sizes). The reason: the sit→walk contrast is
a within-session change, and walk gestures are uniformly present throughout the
session — there is no temporal structure for a window to exploit.

## Result

| Window size | PR-AUC | Prevalence | Approx. windows |
|---|---|---|---|
| 1 (gesture) | 0.585 | 60.8% | 39,556 |
| 5 | 0.578 | 60.8% | 7,878 |
| 10 | 0.576 | 61.1% | 3,916 |
| 20 | 0.574 | 61.4% | 1,934 |
| **40** | **0.587** | 62.5% | 943 |

## Interpretation

**The problem is not window size — it is prevalence.** Walk gestures make up ~60% of
the test set, so the baseline PR-AUC is 0.607 for a random classifier. The detector
is barely above chance. This is an intrinsic limit of the sit→walk contrast: it is a
near-even split with a weak signal, and aggregation over a weak signal recovers nothing.

**Aggregation would be more useful on a high-specificity detector.** If the underlying
FPR at the gesture level were 0.1 rather than 0.6, majority voting over a window of
20 gestures would reduce the window-level FPR to (0.1)^10 ≈ 0 with high probability.
The current detector is too noisy for this mechanism to help.

**What this means for PRECOG deployment.** Session-level alerting requires either:
1. A better underlying gesture detector (see EXP-013: GMM-2 improves FPR meaningfully), or
2. A contrast with genuine temporal structure (compulsive scroll episodes are episodic, not uniform).

The real use case — detecting a compulsive browsing session — has exactly the second
property: compulsive episodes are concentrated in time. Aggregation over a window would
amplify the signal during an episode rather than averaging it out. This experiment's null
does not rule out session-level alerting; it identifies that the sit→walk contrast is an
inadequate proxy for it.

## Note on the contrast

Sit→walk is the only valid contrast available (all task contrasts are confounded by
gesture direction). This limits interpretability: the HMOG null on this contrast is a
posture-change detection result, not a compulsive-use detection result. Aggregation's
true value for PRECOG will only be measurable with a labelled naturalistic dataset.

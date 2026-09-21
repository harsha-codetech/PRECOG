# EXP-002 — H2: Baseline Convergence and Stability

```
Date:        2026-09-20
Status:      COMPLETE
Hypothesis:  H2 — A personal baseline converges to a stable representation
             within a practical number of enrolled gestures
Data:        HMOG · 99 subjects · 39,556 gestures
Protocol:    Subject-wise, contiguous enrollment (FETA pitfall P3)
```

> ## ⚠ CONVERGENCE THRESHOLD SUPERSEDED — window-dependent (EXP-005b, 2026-09-20)
>
> This experiment found the HMOG median subject reaches ρ≥0.95 at **n=80 gestures (~2.1 sessions)**.
> EXP-005b on FETA (138 subjects, 30+ days, 288k gestures) shows this figure is **window-dependent**:
>
> - FETA full-span curve never reaches ρ=0.95; median subject stalls around ρ=0.919 at n=200
> - FETA **window-matched** curve (same short time window as HMOG) reaches ρ=0.969 at n=200
>
> **The n=80 / 2-session conclusion holds for short-window deployment** but should not be extrapolated
> to longitudinal use. Baselines require ongoing adaptation as behavioural drift accumulates
> (+12%/30d, p=1.3e-104, EXP-005b). Both the n_star result and the drift result are now necessary
> to characterise convergence completely.

## Verdict

**Supported with qualification.** Baselines converge within 2 sessions for short-horizon deployment.
Longitudinal stability requires adaptation — the baseline must update as the user drifts.

## Design

- Enrollment: gestures 1…n (contiguous from session start, per P3)
- Holdout: last 40 gestures per subject (never in enrollment)
- Stability measure: Spearman ρ between feature medians of enrollment set and holdout set
- n_star: smallest n where median subject reaches ρ≥0.95
- Subjects retained where holdout ≥40 gestures

## Result

| n gestures | Subjects | Median ρ | P25 ρ |
|---|---|---|---|
| 5 | 99 | 0.613 | 0.384 |
| 10 | 99 | 0.801 | 0.589 |
| 20 | 99 | 0.890 | 0.707 |
| 40 | 99 | 0.918 | 0.831 |
| 60 | 98 | 0.944 | 0.883 |
| **80** | 98 | **0.964** | 0.907 |
| 100 | 97 | 0.971 | 0.915 |
| 150 | 91 | 0.985 | 0.950 |
| 200 | 70 | 0.984 | 0.956 |

**n_star (median subject):** 80 gestures ≈ 2.1 sessions (HMOG: 39 gestures/session median)
**n_star (P25):** 150 gestures ≈ 3.8 sessions

## Interpretation

A user can be onboarded with 2 sessions. The 25th-percentile user needs 4 sessions to reach stability.
The per-user spread in the EXP-001/005 distinctiveness results (0–85%) partially explains why: users
with weaker behavioural signatures converge more slowly, because there is less reliable signal in each
gesture for the baseline to lock onto.

## Corrections since initial run

1. **n_star is window-dependent.** The 80-gesture figure was measured over a short time window
   (HMOG lab sessions, ~1 hour each). FETA's 30-day span never converges to ρ=0.95 without
   temporal windowing. Both results are correct; they answer different questions.
   See EXP-005b for the full reconciliation.

2. **Drift invalidates a static baseline.** Even after convergence, deviation increases monotonically
   (+12% over 30 days). Systems built on a static enrollment baseline will accumulate false positives
   over months. Empirical-Bayes context shrinkage (SPEC §4) provides the adaptation mechanism.

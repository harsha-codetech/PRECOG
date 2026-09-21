# EXP-009 — the complete model ladder

```
Date:        2026-09-20
Questions:   (1) do the interpretable rungs between "one threshold" and XGBoost change any
                 conclusion?
             (2) what should PRECOG actually use at inference, where no labels exist?
Data:        HMOG sit->walk (the only valid real contrast after EXP-007) · 3,816 windows ·
             99 subjects · 25 features · prevalence 0.488
             plus synthetic (synth-v0.1) under both anomaly types, magnitude 1.5
Protocol:    subject-wise GroupKFold ×5 (supervised) · per-user fit-on-normal (unsupervised)
Versions:    features-v0.1 · baseline-v0.1 · seed 42
```

## Verdict

**Two conclusions changed. Deep learning is not needed here — and neither is gradient boosting.
And the deviation scorer in `SPEC.md` is not the best available option.**

---

## 1. Supervised ladder

| Model | PR-AUC | ± sd | ROC-AUC | Justified by |
|---|---|---|---|---|
| **XGBoost** | **0.628** | 0.053 | 0.655 | carried from EXP-007 |
| RF | 0.608 | 0.052 | 0.625 | **Time2Stop's classifier** |
| **LogR** | **0.600** | **0.026** | 0.642 | blueprint's interpretable baseline |
| GRU | 0.597 | 0.054 | 0.641 | EXP-007 |
| NB | 0.550 | 0.031 | 0.574 | tests the independence assumption |
| PCA+LogR | 0.548 | 0.031 | 0.573 | tests dimensionality reduction |
| kNN | 0.542 | 0.034 | 0.569 | **Touchalytics' own classifier** |
| DT | 0.534 | 0.030 | 0.563 | blueprint's interpretable baseline |
| *(prevalence)* | *0.488* | | | |

### Logistic regression is competitive, and steadier

LogR reaches **0.600 against XGBoost's 0.628** — a gap of 0.028, well inside the fold variance —
with **half the standard deviation** (0.026 vs 0.053).

Without this rung the project would have concluded that gradient boosting was necessary. It is not.
A linear model over 25 features captures nearly all the available signal and generalises more
consistently across held-out subjects.

**This is what the ladder is for.** EXP-007 jumped from one threshold to XGBoost and had no way to
see that everything in between performs about the same.

### Naive Bayes measures the independence failure

NB (0.550) sits **0.050 below LogR** (0.600) on identical features. The models differ in essentially
one respect: NB assumes features are conditionally independent.

The project has blamed feature independence twice — the mean-z scorer collapsing to AUC 0.545 where
Mahalanobis reached 0.868 (EXP-003), and signal dilution recurring across contrasts. **That was an
explanation. This is a measurement.**

### PCA does not help supervised classification

PCA+LogR (0.548) falls **0.052 below plain LogR**. Compressing to 8 components discards
discriminative signal rather than concentrating it — so the hand-picked 6-feature Mahalanobis core
is not obviously improvable by a linear projection in the supervised setting.

*(It behaves completely differently unsupervised — see below.)*

### The Time2Stop-comparable number

RF reaches **0.608**. The blueprint calls benchmarking against Time2Stop mandatory; this is the
matched-classifier figure, though on PRECOG's features and contrast rather than a re-implementation
of their full pipeline.

---

## 2. Unsupervised arm — PRECOG's real inference setting

Each model is fitted on **one user's normal gestures only** and scores everything afterwards. Labels
are used to evaluate, never to fit. This is what the product does: no labels exist at inference.

**FPR at 80% sensitivity · lower is better**

| Model | HMOG sit→walk | synth population-consistent | synth **person-relative** |
|---|---|---|---|
| IsolationForest | 0.800 | 0.728 | 0.628 |
| OneClassSVM | 0.820 | 0.718 | 0.592 |
| Mahalanobis *(current SPEC)* | 0.823 | **0.789** | 0.586 |
| **PCA reconstruction** | **0.787** | **0.671** | **0.536** |
| *n subjects* | *88* | *200* | *200* |

### PCA reconstruction error wins everywhere

Best on all three conditions, and by the largest margin exactly where the current scorer is weakest:
**0.671 vs 0.789** on population-consistent deviations.

The reversal against its supervised showing is not a contradiction — it reflects a different
question. Supervised PCA asks *"which components separate two known classes?"* and throws away
whatever the label does not need. Reconstruction error asks *"does this gesture lie on the manifold
this person's normal behaviour occupies?"* — which is precisely the novelty-detection question, and
needs no labels at all.

### The EXP-008 mechanism is method-independent

**Every model does markedly better on person-relative than population-consistent deviations** —
Isolation Forest 0.628 vs 0.728, One-Class SVM 0.592 vs 0.718, PCA 0.536 vs 0.671.

That matters: EXP-008's finding is not an artifact of the Mahalanobis scorer. It is a property of
the problem, and it survives four independent detection methods.

---

## Consequences for the spec

1. **Add PCA reconstruction error as a deviation tier.** It beats Mahalanobis on every condition
   tested and requires no labels. `SPEC.md` §5 updated.
2. **Keep Mahalanobis.** It remains interpretable per-feature, which reconstruction error is not —
   and `evidence-required` is a non-negotiable product rule. The two are complementary: Mahalanobis
   explains, PCA detects.
3. **Logistic regression becomes the default supervised rung**, not XGBoost. Comparable accuracy,
   half the variance, readable coefficients.
4. **Retire the GRU.** It ranked 4th of 8 and lost to a linear model. Blueprint Principle 8 is
   satisfied and documented.

## Limitations

- One real contrast only. Sit→walk is all that survived EXP-007's leakage finding, so "wins
  everywhere" means two synthetic conditions and one real one.
- Absolute FPRs remain high (0.54–0.82). No model here is deployable as a per-gesture alarm; PRECOG
  aggregates over sessions, and that aggregation is not yet evaluated on a valid contrast.
- PCA components were fixed at 8 without tuning. A sweep might improve it further, or might not.

## Next

1. Sweep PCA components and add reconstruction error to `precog/deviation/score.py` as tier 3.
2. Re-run EXP-003's personalized-vs-global comparison with PCA reconstruction as the scorer — the
   H3 null was measured with Mahalanobis, which is now known to be the weaker detector.
3. The deployable-threshold question stands open and needs session-level aggregation on a contrast
   that is actually valid.

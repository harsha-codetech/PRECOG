# EXP-007 — XGBoost + SHAP and a GRU

```
Date:        2026-09-20
Questions:   (1) which features carry a behavioural deviation?
             (2) does gesture ORDER carry signal that window summaries discard?
Design:      both models see identical 16-gesture windows (stride 8, never crossing a
             session boundary). XGBoost gets per-window mean and std; the GRU gets the
             raw sequence. Subject-wise GroupKFold, 5 folds. PR-AUC primary.
Versions:    features-v0.1 · seed 42
```

## Verdict

**Two of the three contrasts are invalid, and SHAP is what exposed them.** The one clean contrast
gives a believable result, the GRU does not beat XGBoost, and `mid_stroke_area` is confirmed as the
dominant feature for a third time.

---

## The contrast validity failure

Both task contrasts returned **PR-AUC 1.000 ± 0.000**. Perfect separation is not a result; it is a
symptom.

SHAP identified the cause immediately — `direction_flag_mean` dominated with mean |SHAP| of **4.27**
(hmog_task) and **6.51** (feta_task), an order of magnitude above everything else. Checking the
underlying distributions:

| Contrast | normal: vertical | changed: vertical |
|---|---|---|
| reading → map | 98.0% | 47.6% |
| **scroll → swipe** | **99.2%** | **1.7%** |

Scrolling a feed is vertical. Swiping an image gallery is horizontal. The model was reading
**gesture direction**, not behaviour.

**Removing the three direction features did not fix it.** Accuracy stayed at 1.000 and the leakage
simply relocated — to `start_y_mean` (2.27) for reading→map, and `mean_resultant_length_mean` (5.98)
for scroll→swipe. Swipes start elsewhere on screen and are straighter than scrolls.

**Conclusion: these are not behavioural-deviation contrasts. They are different gesture types.** Any
model separates them trivially, so they cannot test anything PRECOG cares about.

### What this invalidates

| Result | Status |
|---|---|
| **EXP-004** reading→map, "personalization beats global p=0.044" | **Confounded — withdraw** |
| **EXP-005c** scroll→swipe, "79% of subjects, δ=−0.41" | **Confounded — withdraw.** This was the strongest personalization signal in the project |
| EXP-007 task contrasts | **Void** |

### What survives

| Result | Why unaffected |
|---|---|
| EXP-001 / EXP-005a distinctiveness | No contrast involved — identity, not deviation |
| EXP-002 / EXP-005b convergence and drift | No contrast involved |
| EXP-003 sit→walk null | **Valid** — same task, same gesture type, only physical condition differs |
| EXP-008 synthetic mechanism | Controlled generation; deviation defined by scaling, not gesture type |

**sit → walk is the only valid real behavioural contrast in this project.** And it returned a null.

---

## The valid contrast: sit → walk

```
3,816 windows · 99 subjects · 25 features · 48.8% positive
baseline PR-AUC (prevalence) : 0.488
XGBoost PR-AUC               : 0.628 ± 0.060   ROC 0.655   Brier 0.258
GRU     PR-AUC               : 0.597 ± 0.054   ROC 0.641   Brier 0.299
GRU − XGBoost                : −0.027
```

A modest but real lift over prevalence, with wide fold variance — which is what an honest result on
a hard problem looks like.

### Which features carry it

| Feature | mean \|SHAP\| |
|---|---|
| `mid_stroke_area_mean` | 0.680 |
| `duration_ms_mean` | 0.448 |
| **`inter_scroll_ms_mean`** | 0.430 |
| `median_acceleration_first_pts_mean` | 0.242 |

**`mid_stroke_area` leads for a third time.** It was FETA's highest-ICC feature (0.530) and
Touchalytics' top feature by mutual information in 2013. Three methods, three datasets, one answer —
contact area is the most individually informative touch feature available.

**`inter_scroll_ms` ranks third**, which retrospectively justifies choosing HMOG over FETA's
precomputed features: that table omits inter-stroke timing entirely.

### Does order matter?

**No.** The GRU lost by 0.027 on the only valid contrast, despite seeing the same windows with the
sequence intact. Gesture ordering carries nothing that per-window mean and std do not already hold.

This is the outcome the blueprint predicted (Principle 8: establish statistical baselines before
deep learning; reviewers punish gratuitous deep learning). It is reported as an ablation result, not
buried — a negative finding about sequence models is still a finding.

---

## What SHAP earned here

Feature attribution was added to answer "which features carry the deviation". It answered that — and
also caught a validity failure that four experiments and three summary statistics had missed. The
FPR numbers in EXP-004 and EXP-005c looked plausible (0.3–0.6) precisely because Mahalanobis spreads
its attention across 25 dimensions; only a model that *seeks* the separating feature revealed that
one existed.

**A model that performs perfectly should be investigated, not celebrated.**

## Next

1. Withdraw EXP-004 and EXP-005c conclusions; annotate both READMEs.
2. Add a **contrast-validity check** to the protocol: before using any contrast, verify no single
   feature separates the classes near-perfectly.
3. The personalization question now rests on one real null (sit→walk) plus the synthetic mechanism
   test (EXP-008). Both point the same way: **compulsive scrolling must be shown to be a
   person-relative deviation, and no existing dataset can show that.**

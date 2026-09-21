# PRECOG — Methods

Canonical statement of what data and what models. Supersedes scattered descriptions elsewhere.
Every figure below was measured from the files on disk, not quoted from a paper.

---

## 1. Datasets used for modelling

Two, both public, both with per-event timestamps **and** kinematics.

### HMOG — primary for timing

*Sitová et al., IEEE TIFS 2016 · 100 participants × 24 sessions · 2014 · Samsung · ToU, non-commercial*

| Slice | Gestures | Subjects | Sessions/subject |
|---|---|---|---|
| Reading | **39,556** | 99 | 7–8 |
| Map navigation | **~145,000** | 99 | 8 |

Supplies the sit/walk and reading/map labels. `ScrollEvent.csv` carries absolute epoch-ms
timestamps, so inter-scroll interval, burstiness and dwell are all derivable.

**Known limitation:** `Pressure` is constant `1.0` everywhere — the 2014 devices did not report it.
Touchalytics ranks mid-stroke pressure 3rd by mutual information, so this is a real loss and the
feature is excluded from every model.

### FETA — primary for scale and duration

*Georgiev et al., 2023 · 515 users, 31 days · 2020 · iOS · **ODC-PDDL (public domain)***

| Slice | Gestures | Subjects | Sessions/subject |
|---|---|---|---|
| Scroll (social-media feed) | **288,124** | 138 | median 30 |
| Swipe (image gallery) | **486,662** | 138 | median 30 |

Cohort = users with ≥ 20 scroll sessions (the 31-day arm). Median **2,012** gestures per subject
over a median **29.9-day** span — the only genuinely longitudinal source.

**Known limitation:** no orientation field, so `phone_orientation` is constant and excluded.

### Totals

```
237 subjects · 2 datasets · ~960,000 gestures
```

## 2. Datasets NOT used for modelling

| Dataset | Why |
|---|---|
| **Tappigraphy** (189 users) | Hourly aggregates only; no per-event data. Retained as naturalistic context and for the circadian discussion, never as model input |
| **AITouch** (45 users) | Four games on a Samsung Tab S4. Tablet gestures, no scrolling scene — wrong behaviour. **Dropped** |

---

## 3. Labels

**No public dataset pairs scroll telemetry with compulsive-use labels.** This is stated plainly in
the paper and bounds every claim.

Instead, three **real, un-injected behavioural contrasts with ground truth**:

| Contrast | Normal | Changed | Subjects |
|---|---|---|---|
| `hmog_posture` | sitting | walking | 82 |
| `hmog_task` | reading | map navigation | 98 |
| `feta_task` | scroll feed | swipe gallery | 138 |

**Semi-synthetic injection is prohibited.** EXP-003 arm 1 showed it circular: a shift specified in
feature space is trivially detected by a threshold on those features. Those numbers are void.

---

## 4. Features

**28 per gesture**, implementing Frank et al.'s Touchalytics set so HMOG and FETA stay comparable.

| Family | Features |
|---|---|
| Geometry | start/stop x,y · end-to-end distance · trajectory length · straightness ratio · largest deviation · deviation p20/50/80 |
| Kinematics | velocity p20/50/80 · average velocity · acceleration p20/50/80 · median velocity (last 3 pts) · median acceleration (first 5 pts) |
| Circular | average direction · direction end-to-end · mean resultant length · direction flag |
| Contact | mid-stroke area |
| Timing | duration · **inter-scroll interval** · n samples |

**Excluded, each with a reason:**

| Feature | Reason |
|---|---|
| `pressure` | Constant in HMOG — would confound cross-dataset comparison |
| `phone_orientation` | Constant in FETA; and EXP-001 showed removing it *improved* identification |
| `change_of_finger_orientation` | Zero mutual information in Touchalytics' own Table 1 |

---

## 5. Models

Five arms. A–C are statistical, D–E are trained.

| | Model | Input | Role |
|---|---|---|---|
| **A** | Fixed univariate threshold (`average_velocity`) | one feature | The strawman — which has beaten everything so far |
| **B** | Global multivariate baseline | population Mahalanobis | Does multivariate help? |
| **C** | **Personalized baseline** | per-user Mahalanobis + robust z, empirical-Bayes context shrinkage | Does personalization help? |
| **D** | **XGBoost + SHAP** | per-window mean & std of each feature | Which features carry the deviation? |
| **E** | **GRU** | raw window × feature sequence | Does gesture *order* matter? |

**D and E see identical windows** — 16 consecutive gestures, stride 8, never crossing a session
boundary. D gets summary statistics, E gets the sequence. The comparison therefore isolates exactly
one thing: whether ordering carries signal the summaries discard.

**Deviation scoring (arms B, C)** has two tiers, and which one ran is recorded with every score:
- Tier 1 — robust z: `0.6745 × (x − median) / MAD`
- Tier 2 — Mahalanobis over a 6-feature core with Ledoit–Wolf shrunk covariance, once n ≥ 30

Tier 2 is preferred wherever available. EXP-003 showed why: averaging z across 28 features gave
AUC 0.545 where Mahalanobis over 6 gave **0.868**. Signal dilution is the single most consistent
failure mode in this project.

**Planned, not yet run:** Isolation Forest and One-Class SVM per user — the unsupervised arm, which
is what PRECOG is at inference time when no labels exist.

---

## 6. Protocol

**Splits**
- **Subject-wise `GroupKFold`, 5 folds** for D and E. A subject never appears in both train and test.
- **Contiguous temporal splits** for baseline enrolment — earliest sessions enrol, later sessions
  evaluate. Never random (FETA pitfall P3, worth 3.8 pp EER).
- Enrolment fixed at **n = 80 gestures**, carried from EXP-002 and not retuned per dataset.

**Metrics**
- **PR-AUC primary** — classes are unbalanced per subject and ROC-AUC flatters that
- ROC-AUC and **Brier score** alongside, because a probability shown to a user must be calibrated
- **FPR at matched 80% sensitivity** for the deviation arms
- Per-subject distributions reported, never just the mean — EXP-001/005 showed a 0%–85% spread that
  any average hides

**Statistics**
- Wilcoxon signed-rank for paired per-subject comparisons (non-normal)
- **Cliff's δ reported with every p-value** — significance without effect size is not a result
- Holm correction across confirmatory tests
- Seed 42 throughout; `feature_version`, `baseline_version`, `model_version` stored with every output

**Reproducibility** — one directory per experiment run, never overwritten, each with `config.yaml`,
`run.py`, `README.md` and `outputs/`. Golden-vector tests lock feature parity for the eventual
Kotlin port.

---

## 7. What this design can and cannot support

**Can claim**
- Scroll kinematics are individually distinctive — replicated across two datasets (top-1 14.9% vs
  15.0%; AUC 0.802 vs 0.787)
- Distinctiveness varies enormously between people (0% – 84.7%) — replicated
- Personal baselines drift measurably: +12% deviation over 30 days, monotonic
- Feature selection has outperformed personalization in all three contrasts

**Cannot claim**
- That PRECOG detects compulsive scrolling. No dataset contains that label.
- That personalization reduces false positives. Contrast-dependent and not confirmatory.
- Anything about naturalistic free browsing. Every contrast is a task in a study.

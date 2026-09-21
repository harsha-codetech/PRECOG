# PRECOG — phased commit plan

Sixteen commits, ordered so the history reads as the project actually happened: specification,
then method, then experiments in the order they were run, then the failures that changed the claim,
then the app, then the paper. Anyone reading `git log --reverse` gets the story.

Drop the `Co-Authored-By` line from any message if you'd rather not have it.

---

## Before anything: two things that must not reach GitHub

Both are now handled, but verify rather than trust.

**1. The signing keystore.** `.gitignore` had `*.keystore`, which does **not** match `.jks`. Your
`android/precog-release.jks` would have been committed. Added `*.jks` and `android/keystore.properties`.

**2. Keystore passwords were hardcoded** in `android/app/build.gradle.kts`. Moved to
`android/keystore.properties` (gitignored), with `keystore.properties.example` committed in its
place. Release signing still works — verified, same certificate DN.

**3. Third-party research code.** `research/reference-code/codelab/` holds five repositories from
other researchers. Not yours to redistribute. Now gitignored.

**Run this after `git add -A` and before the first commit:**

```bash
git status --porcelain | grep -iE "\.jks|\.keystore|keystore\.properties$|local\.properties|\.apk|reference-code|/data/|references/papers" || echo "CLEAN"
```

If it prints anything other than `CLEAN`, stop and fix `.gitignore` before committing.

---

## Setup

```bash
cd C:/Users/Admin/Desktop/PRECOG
git init
git branch -M main
```

**Keep the repository private until you have decided you are happy for it to be public.** The patent
route is closed by your own decision of 2026-09-20, so publication no longer blocks you — but a
public repo is still a disclosure, and you may want the venue settled first.

---

## Phase 0 — Repository scaffold

```bash
git add .gitignore README.md LICENSE LICENSE-MIT LICENSE-APACHE
git commit -m "chore: repository scaffold, licensing and ignore rules

Dual-licensed Apache-2.0 or MIT, at the user's option.

Datasets, third-party PDFs, third-party research code and all signing
material are excluded. HMOG's terms of use forbid redistribution, so
data/ is reconstructed from the DOIs in docs/DATASETS.md rather than
committed, and LICENSE states plainly that a licence on this code
grants nothing with respect to that data.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Phase 1 — Specification and method

```bash
git add docs/
git commit -m "docs: specification, method, datasets and prior-art library

SPEC.md is the governing document: feature set, three-tier deviation
model, behavioural states, milestones and evaluation protocol.
RELATED_WORK.md catalogues 22 prior papers with access routes.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Phase 2 — Research library and pipeline

```bash
git add config/ research/precog/ research/tests/ research/pytest.ini scripts/
git commit -m "feat(research): feature extraction, baseline and deviation library

Touchalytics-compatible gesture features, per-user baselines with
empirical-Bayes context shrinkage, and the deviation tiers. Golden
vectors in tests/ lock feature parity so the Kotlin port can be
checked against this implementation.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Phase 3 — The three hypotheses

```bash
git add research/experiments/EXP-001_h1-individual-distinctiveness \
        research/experiments/EXP-002_h2-baseline-convergence \
        research/experiments/EXP-003_h3-personalized-vs-global
git commit -m "exp: H1 distinctiveness, H2 convergence, H3 personalisation null

H1 supported: AUC 0.787, 88.5% of gestures nearest their own centroid,
but per-subject accuracy ranges 0%-65.9%.
H2 supported: median subject stabilises at n=80 gestures.
H3 NOT supported: personalised 0.821 vs global 0.825 (p=0.33), and a
single fixed threshold beats both at 0.712 (p=4e-07).

H3 was the headline hypothesis. Its failure is why the paper's claim
changed.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Phase 4 — The validity failure

```bash
git add research/experiments/EXP-004_reading-vs-map \
        research/experiments/EXP-005_feta-replication \
        research/experiments/EXP-006_distinctiveness-stratification \
        research/experiments/EXP-007_models
git commit -m "exp: leakage audit withdraws two of three contrasts

EXP-007 reached PR-AUC 1.000 on two task contrasts. SHAP showed the
models were reading gesture direction, not behaviour: reading is 98%
vertical against map at 48%, FETA scroll 99.2% against swipe at 1.7%.
Removing direction features relocated the leakage to start position
and straightness rather than fixing it.

EXP-004 and EXP-005c withdrawn. EXP-005c had been the strongest
apparent personalisation signal at 79% of subjects, so this removes
evidence that favoured the original hypothesis.

Protocol rule added: verify no single feature separates the classes
near-perfectly before using a contrast.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Phase 5 — The mechanism

```bash
git add research/experiments/EXP-008_synthetic-mechanism \
        research/experiments/EXP-010_h3-pca-rerun
git commit -m "exp: personalisation is conditional on deviation type

Controlled generation produces a clean sign flip. Personalisation is
worse than a global model for population-consistent deviations
(C-B = +0.009 to +0.026, all p < 1e-5) and better for person-relative
ones (-0.009 to -0.073). This explains the H3 null directly: walking
changes everyone's scrolling in the same direction.

EXP-010 re-runs H3 under the stronger PCA detector. The null survives
(C-B = +0.003, p = 0.85), so it is not an artifact of the scorer.

This is the paper's contribution.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Phase 6 — Model selection

```bash
git add research/experiments/EXP-009_model-ladder \
        research/experiments/EXP-011_pca-component-sweep \
        research/experiments/EXP-012_feature-selection \
        research/experiments/EXP-013_per-user-gmm \
        research/experiments/EXP-014_session-aggregation
git commit -m "exp: detector and model selection measured, not assumed

PCA reconstruction beats Mahalanobis, one-class SVM and isolation
forest on all three conditions; k=8 sits in a plateau flat above k=5.
GMM-2 beats single-Gaussian Mahalanobis (0.746 vs 0.810 on HMOG).
Logistic regression matches XGBoost at half the variance, and a GRU
placed fourth of eight. Feature selection hurts monotonically.

EXP-014 is a null: session aggregation is flat across window sizes
1-40, because walk gestures are uniformly distributed through sessions
and offer no temporal concentration to exploit.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Phase 7 — Figures and tables

```bash
git add results/
git commit -m "results: 12 figures and 3 tables

tab-03 is the feature-comparison table and carries the deployability
claim: the Android feature set is a reduction plus one substitution,
not a strict subset of the offline 28.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Phase 8 — Course deliverable

```bash
git add reports/ml-course-report.html
git commit -m "docs: ML course report covering all 14 experiments

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Phase 9 — UX track

```bash
git add ux/ reports/ux-heuristic-evaluation.html public/
git commit -m "design: UX research, wireframes, design system and evaluation

Personas, journey map, competitive analysis, WF-01 to WF-08, the
interactive prototype and the heuristic evaluation. Findings F-01,
F-03, F-07, F-08, F-09 and F-16 are implemented in the Android UI,
which gives the evaluation-to-build trail the coursework needs.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Phase 10 — The feasibility spike

```bash
git add android/m0-spike-archive/
git commit -m "spike(M0): what an AccessibilityService can actually observe

Throwaway app used to answer the observability question before
building anything real. Establishes that scrollDeltaY is reported
inconsistently across apps and that YouTube emits no scroll events at
all under SurfaceView rendering.

Kept as the research record. Its findings became section 5A of the
paper.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Phase 11 — Android build scaffold

```bash
git add android/settings.gradle.kts android/build.gradle.kts \
        android/gradle.properties android/gradlew android/gradlew.bat \
        android/gradle/ android/app/build.gradle.kts \
        android/app/proguard-rules.pro android/keystore.properties.example \
        android/app/src/main/AndroidManifest.xml android/app/src/main/res/
git commit -m "build(android): Gradle scaffold, manifest and resources

AGP 8.7.0 / Gradle 9.3.0 / Kotlin 2.0.21, compileSdk 36, minSdk 26.

No INTERNET permission is declared, so the offline claim is structural
rather than a promise. canRetrieveWindowContent is false, so screen
text is unreadable at the capture boundary.

Signing credentials are read from keystore.properties, which is
gitignored; see keystore.properties.example. Release builds are
unsigned rather than failing when it is absent, so a fresh clone still
builds.

lint-vital is disabled for release: AGP 8.7's bundled lint crashes
against compileSdk 36 with a bare version string. Lint still runs via
:app:lintDebug.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Phase 12 — Storage layer

```bash
git add android/app/src/main/java/com/precog/PrecogApplication.kt \
        android/app/src/main/java/com/precog/data/
git commit -m "feat(android): encrypted local storage and settings

Room over SQLCipher. The passphrase is 32 random bytes sealed with
AES-GCM under an AndroidKeyStore key, so it never exists in plaintext
at rest. On unseal failure the app starts clean rather than crashing.

Raw scroll timings are purged after 48 hours; only derived feature
windows persist.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Phase 13 — Capture and features

```bash
git add android/app/src/main/java/com/precog/service/ \
        android/app/src/main/java/com/precog/features/
git commit -m "feat(android): scroll capture and the six observable features

Per-app delta resolution from M0: prefer a non-sentinel scrollDeltaY,
otherwise difference successive scrollY, otherwise return null. A
missing measurement stays missing rather than becoming a plausible
zero.

The unit is the scroll event, not the swipe. Measured 2026-09-21: ten
deliberate swipes produced 54 TYPE_VIEW_SCROLLED events, because
Android reports throughout a fling's deceleration. All user-facing
wording says 'scroll step' accordingly, and median_gap is documented
as intra-fling spacing rather than human pacing.

unbroken_ratio is deliberately not named passive_ratio: SPEC 4 defines
that as windows with scrolls and zero clicks, which is a different
quantity.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Phase 14 — The engine

```bash
git add android/app/src/main/java/com/precog/engine/
git commit -m "feat(android): baselines, deviation and state classification

Pure Kotlin, no ML dependency: cyclic Jacobi eigendecomposition,
diagonal-covariance GMM-2 by EM, PCA reconstruction error with k
chosen by 85% cumulative variance, and robust statistics throughout.

k is chosen by the criterion, not carried over: the offline k=8 was
fitted for 28 features and does not transfer to six. k is clamped to
[1, d-1] because retaining every axis zeroes the residual and blinds
the detector.

The enrolment gate is 25 windows per context cell, re-derived for the
window unit rather than reusing the offline n>=80 gestures.

ENGAGED is an explicit false-positive defence: an alerting score with
a low passive-ratio sigma and non-negative reversals reads as
deliberate use and does not alert.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Phase 15 — Interface

```bash
git add android/app/src/main/java/com/precog/ui/
git commit -m "feat(android): Compose interface implementing WF-01 to WF-08

Evidence is a type-level requirement: no score renders without the
per-feature evidence behind it. Confidence appears next to every
verdict, and below 0.35 the app reports NOT_ENOUGH_PATTERN rather than
guessing.

No detection-accuracy figure appears anywhere, deliberately. The
Android feature set has never been evaluated against labelled data and
the Settings screen says so to users.

Implements evaluation findings F-01, F-03, F-07, F-08, F-09 and F-16.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Phase 16 — The paper

```bash
git add paper/ research-workspace.md COMMIT_PLAN.md
git commit -m "paper: full draft and verified bibliography

Title: 'Not Every Deviation Is Personal: A Precondition for
Personalised Behavioural Baselines in Scroll-Based Deviation
Detection'. The previous working title promised false-positive
reduction, which is the result that did not hold.

24 bibliography entries, every one verified against the arXiv or
Crossref API. Four papers were being cited as preprints despite having
published versions.

Venue is not yet selected, so the draft is venue-neutral Markdown
rather than a template.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Push

```bash
git remote add origin https://github.com/<you>/precog.git
git push -u origin main
```

---

## After pushing

- LICENSE added 2026-09-21 (dual Apache-2.0 / MIT). Confirm "Sri Harsha" is the name you want on
  the copyright line — change it in LICENSE, LICENSE-MIT and LICENSE-APACHE if not.
- `paper/figures/`, `paper/manuscript/`, `paper/references/` and `paper/tables/` are empty, so git
  will not track them. They fill in once the venue is chosen.
- If you ever need to rotate the signing key: the current one is committed nowhere, but it is also
  backed up nowhere. Losing it means a new key, which means anyone with the app installed must
  uninstall before they can update.

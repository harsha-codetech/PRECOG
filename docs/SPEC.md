# PRECOG — Reconciled Specification v0.1

**Status:** proposal, awaiting approval. No code until approved.
**Date:** 2026-09-19
**Supersedes:** conflicting guidance in the PRECOG KT and `PRECOG_Blueprint.docx`, which are reconciled here.

> **Confidentiality.** No patent application has been filed. Any public disclosure of the
> mechanism — public repository, preprint, demo, artifact, README describing the method —
> may bar patentability in India, which has no general grace period. This repository stays
> **private** until a provisional is filed. See §10.

---

## 0. Governing decisions

Three decisions were taken on 2026-09-19 and everything below follows from them:

1. **Client is a native Android app (Kotlin).** Not an instrumented web feed.
2. **Nothing is filed.** Confidentiality constraint above is in force.
3. **Specification is reconciled before implementation.** This document.

---

## 1. What PRECOG is, in one sentence

A privacy-first Android application that learns an individual's scroll-interaction baseline
on-device, estimates compulsive-scrolling risk as a statistical deviation from that baseline,
explains every estimate from the deviations that produced it, and — in a later phase — selects
graded interventions through an online policy whose reward is the measured change in the same
interaction features.

**PRECOG is not** a diagnostic tool, a screen-time counter, a content monitor, or a surveillance
application. Language in code, UI, and writing says *behavioural deviation*, never *addiction*.

---

## 2. The observability question (resolved first, or not at all)

The blueprint calls cross-app scroll sensing "feasibility-fatal if ignored." It is the single
assumption on which every downstream claim rests, so it gets measured before anything is built.

**What Android can plausibly provide**, via `AccessibilityService`:

| Signal | Source | Confidence |
|---|---|---|
| Scroll event + timestamp | `TYPE_VIEW_SCROLLED` | High |
| Scroll delta (px) | `scrollDeltaX/Y` (API 28+) | **Unverified per-app** |
| Item indices scrolled past | `fromIndex`/`toIndex`/`itemCount` | **Unverified per-app** |
| Scroll direction | sign of delta or index change | Medium |
| Tap / like / interaction **count** | `TYPE_VIEW_CLICKED` | Medium |
| App foreground/background | `TYPE_WINDOW_STATE_CHANGED`, `UsageStatsManager` | High |
| Notification arrival | `NotificationListenerService` | High |

**What Android cannot provide** for a third-party app: touch coordinates, pressure, finger
trajectory, or true gesture velocity. Those require receiving the `MotionEvent`s, which only the
foreground app does. **Touchalytics-grade features are out of reach and must never be claimed.**

The honest position: PRECOG operates on **event-timing kinematics** (intervals, burstiness,
direction reversals, dwell, coarse displacement, active/passive ratio), a tier richer than the
coarse counts Time2Stop uses and poorer than touch biometrics. The paper must say exactly this.

### M0 — Feasibility spike (blocking, ~2–3 days)

A throwaway Android app that logs raw accessibility events to CSV while scrolling each target app
for a fixed period. Deliverable is a one-page findings table:

- For each of Instagram, YouTube Shorts, TikTok, Reddit, X, Chrome: does `TYPE_VIEW_SCROLLED`
  fire? At what rate? Are `scrollDeltaX/Y` non-zero? Are item indices populated?
- Event rate per minute of scrolling, and jitter in event timestamps.
- Do `TYPE_VIEW_CLICKED` events fire on likes/taps?
- Battery cost of an always-on service over one hour.

**Gate:** if scroll events are absent or delta-less across all target apps, the Android route
cannot support the kinematic claim. Fallback is the instrumented-feed route, decided then — not
assumed now.

---

## 3. Architecture

```
┌─────────────────────────── Android device ───────────────────────────┐
│                                                                       │
│  AccessibilityService ──► EventBuffer ──► Room (encrypted)            │
│  NotificationListener          │                                      │
│                                ▼                                      │
│                        FeatureExtractor  (windows + sessions)         │
│                                ▼                                      │
│                        BaselineEngine    (per-user, per-context)      │
│                                ▼                                      │
│                        DeviationEngine   (robust z / GMM / PCA-recon)  │
│                                ▼                                      │
│                        StateEngine       (5 ordered states)           │
│                                ▼                                      │
│                        RiskEngine        (score + confidence)         │
│                                ▼                                      │
│                        InsightEngine     (evidence → plain language)  │
│                                ▼                                      │
│         Compose UI  ◄──────────┴──────────►  InterventionEngine (M6)  │
│                                                                       │
└───────────────────────────────┬───────────────────────────────────────┘
                                │  optional, consent-gated, pseudonymized
                                ▼
                    FastAPI + PostgreSQL (research sync only)
                                │
                                ▼
                    Python experiments (ablation ladder, offline)
```

### Changes from the KT, and why

| KT prescribed | Reconciled | Reason |
|---|---|---|
| Next.js/React/Tailwind dashboard as primary UI | **Jetpack Compose, in-app** | With an Android client, the user-facing dashboard belongs in the app. The KT's design language (§24–28, §54–57) carries over unchanged — it is good and it survives the port. |
| Node API **and** separate Python ML service | **One Python FastAPI service** | The Node layer would only proxy. KT Principle 1: do not over-engineer. |
| Cloud-first pipeline | **On-device by default** | The privacy claim and the §3(k) technical-effect argument both require on-device processing. Cloud is opt-in, pseudonymized, research-only. |
| Per-feature z-scores | **Robust z → GMM-2 density → PCA reconstruction error** | §5. Independent z-scores double-count correlated features. GMM-2 outperforms single-Gaussian Mahalanobis (EXP-013). Mahalanobis retained for per-feature attribution only. |
| 4 threshold buckets | **5 ordered states incl. ENGAGED** | §6. ENGAGED is the false-positive defence. |

A **web dashboard is deferred**, and when it arrives it is a *researcher* tool (cohort views,
ablation results), not a user surface.

### Stack

- **Android:** Kotlin, Jetpack Compose, Room + SQLCipher, WorkManager, kotlinx.serialization
- **Backend (optional):** Python 3.11, FastAPI, PostgreSQL, Pydantic
- **Experiments:** NumPy, Pandas, SciPy, scikit-learn, XGBoost, SHAP, Matplotlib
- **Config:** YAML for every ML parameter (KT Principle 4)

---

## 4. Feature set

Three families. The **interaction-density** family is the addition the KT omitted and is what
separates ENGAGED from COMPULSIVE.

### Event-timing kinematics (core)
`inter_scroll_interval_mean`, `..._cv`, `burstiness`, `rapid_fire_rate`
(consecutive scrolls under a configurable interval), `direction_reversal_rate`,
`scroll_delta_mean`, `scroll_delta_cv`, `fling_ratio`
(bursts with a decaying inter-event profile ÷ all scroll bursts),
`dwell_mean`, `dwell_cv`, `dwell_entropy`

### Session structure
`session_duration`, `longest_continuous_scroll`, `pause_frequency`,
`sessions_today`, `inter_session_interval`, `reopen_within_60s_count`,
`session_acceleration` (trend in scroll rate across the session)

### Interaction density
`active_interactions_per_min`, **`passive_ratio`** (windows with scrolls and zero clicks ÷ all
windows), `passive_ratio_trend`

### Context (baseline conditioning — not features)
`app_id`, `hour_bucket`, `is_weekend`, `followed_notification`, `in_sleep_window`

**Windowing:** 45 s sliding windows, 15 s hop, plus session-level aggregates. A session ends after
120 s without a foreground scroll event. All configurable.

**Dropped from the KT:** `mean_scroll_velocity` and `velocity_variance` as named — true velocity is
not observable (§2). The honest substitutes are `scroll_delta` per event and inter-scroll interval
statistics. Do not relabel these as velocity anywhere in code or writing.

---

## 5. Baseline and deviation

### Context cells and the sparsity problem

Naive contextual baselines (app × 5 time buckets × weekday/weekend) create ~30 cells. Fourteen days
of data cannot populate them, and the KT does not address this.

**Resolution — empirical-Bayes shrinkage.** Every cell statistic is shrunk toward the user's global
statistic in proportion to its sample count:

```
θ_cell_shrunk = w · θ_cell + (1 − w) · θ_user_global
w = n_cell / (n_cell + k)        k configurable, default 10
```

A cell with 2 samples behaves almost like the global baseline; a cell with 50 stands on its own.
This degrades gracefully instead of producing confident nonsense during cold start.

### Baseline statistics

Per feature, per cell: `mean`, `std`, `median`, `MAD`, `IQR`, `n`, `updated_at`.
Robust statistics are primary — behavioural distributions are skewed.

### Deviation, in three tiers

**Tier 1 (always available).** Robust per-feature z:
```
z_robust = 0.6745 · (x − median) / MAD          MAD floored at ε to avoid division blowup
```

**Tier 2 (when n_cell ≥ 30).** Per-user **Gaussian Mixture Model** (GMM, k=2 components by default)
fitted on the user's enrolment gestures. Anomaly score is negative log-likelihood under the mixture.

*Why GMM, not single-Gaussian Mahalanobis.* EXP-013 (2026-09-20) compared Mahalanobis, GMM-2, and
GMM-3 on HMOG sit→walk (real data) and two synthetic conditions. Median FPR at 80% sensitivity:

| Detector | HMOG sit→walk | synth person-relative | synth pop-consistent |
|---|---|---|---|
| Mahalanobis (single Gaussian) | 0.810 | 0.455 | 0.633 |
| **GMM-2 (this tier)** | **0.746** | **0.328** | **0.364** |
| GMM-3 | 0.750 | 0.404 | 0.474 |

GMM-2 wins on all three conditions, reducing FPR by 0.064 (real) to 0.269 (synthetic).
The single-Gaussian assumption is wrong for users who scroll in multiple postures or contexts
(sit, walk, standing) — each mode occupies a different region of feature space, and a Mahalanobis
distance from the pooled centroid inflates false positives in both modes. A 2-component mixture
captures the bimodal structure with the smallest number of parameters.

*k=2 default.* EXP-013 shows GMM-3 degrades relative to GMM-2 on two of three conditions.
k=2 is the recommended default; k is config and can be raised for users whose enrolment data
indicates more than two distinct behavioural modes (detectable via BIC).

*Mahalanobis retained for attribution only.* The GMM score is a scalar. `evidence-required` (§7)
forbids displaying a score without the features that caused it. Mahalanobis per-feature distances
remain the attribution mechanism. **GMM detects; Mahalanobis explains.** Never report the
Mahalanobis distance as the anomaly score — it is an explanation tool only.

*Minimum enrolment for GMM.* n_cell ≥ 30 (same as the previous tier-2 threshold). With k=2 and
`full` covariance, the minimum safe sample size is ~5–10× the number of features; in practice 30
gestures × 28 features is borderline — use `diag` or `tied` covariance when n_cell < 60, full
covariance when n_cell ≥ 60.

**Tier 3 — PCA reconstruction error (primary detector, added after EXP-009).** Fit PCA on the user's
enrolment gestures; score a new gesture by its squared reconstruction error. This asks whether the
gesture lies on the manifold that person's normal behaviour occupies — the novelty-detection
question, and it needs no labels.

**Why tier 3 leads.** EXP-009 compared four unsupervised detectors per user, fitted on normal
gestures only (**FPR at 80% sensitivity — lower is better**; this matches EXP-013's table above,
so the two are directly comparable):

| Detector | HMOG sit→walk | synth population-consistent | synth person-relative |
|---|---|---|---|
| Isolation Forest | 0.800 | 0.728 | 0.628 |
| One-Class SVM | 0.820 | 0.718 | 0.592 |
| Mahalanobis | 0.823 | 0.789 | 0.586 |
| **PCA reconstruction** | **0.787** | **0.671** | **0.536** |

PCA wins on every condition, and by the widest margin exactly where Mahalanobis is weakest.

**PCA component count.** k=8 components (default). EXP-011 swept k=2…25: PR-AUC is flat above k=5
(range 0.579–0.610 across all k), and k=8 covers 85% of variance while sitting in the plateau.
The choice is insensitive to ±4 components in either direction. k is config; do not hard-code it.

**Mahalanobis is retained for attribution only** (same role as in tier 2 above). Reconstruction
error gives a single scalar; Mahalanobis per-feature distances explain which features deviated.
**PCA detects; Mahalanobis explains.** This is true for both tier 2 and tier 3 — the attribution
mechanism is the same regardless of which detector fires.

**Caveat.** "Wins everywhere" means one real contrast plus two synthetic conditions — sit→walk is the
only real contrast that survived EXP-007's leakage finding.

**Second caveat, and it is the important one.** Absolute FPRs stay between 0.54 and 0.82. No
detector in this table is deployable as a per-gesture alarm. This is why PRECOG scores **sessions**,
not gestures, and why the shipped Android app aggregates windows before it will say anything.
A metric label error here was corrected on 2026-09-20: this table was previously headed
"PR-AUC, higher is better", which inverted the reading and made the stated conclusion contradict
its own numbers. The source of truth is `research/experiments/EXP-009_model-ladder/README.md`.

Every stored prediction records which tier produced it. Tier is part of reproducibility (§9).

### Adaptation and contamination

EWMA update, `α` configurable (default 0.05). A window updates the baseline only if **both**:
- combined deviation is below `contamination_threshold`, **and**
- it is **not** within `post_intervention_exclusion` of a delivered intervention

The KT guards only the first; the blueprint guards only the second. Both are required — the first
stops anomalies redefining normal, the second stops PRECOG's own interventions doing it.

---

## 6. Behavioural states

Five ordered states, from the blueprint. **ENGAGED is non-negotiable** — it is what stops a
deliberate 90-minute session scoring like 90 minutes of compulsive scrolling.

| State | Operational definition |
|---|---|
| NORMAL | Combined deviation within baseline; bounded session |
| **ENGAGED** | Elevated duration **but** `passive_ratio` at or below baseline and interaction present — intentional use, **deliberately not flagged** |
| DISTRACTED | Moderate deviation; rising passivity; notification-driven entry |
| COMPULSIVE | Strong deviation: high rapid-fire rate, `passive_ratio` well above baseline, extended continuity |
| HIGH-RISK | Sustained COMPULSIVE in a vulnerable context (personal sleep window) with persistence |

**Integrity constraint (blueprint §10):** these are a *design abstraction*, not clinical
categories. v0 defines them by operational rules over deviations and reports them as such. An HSMM
treating them as latent states is a later option, only with enough data. They are never presented
to a user or a reviewer as validated psychological states.

Output is a probability distribution over the five, with hysteresis (minimum dwell time per state)
to stop flapping.

---

## 7. Risk and confidence

```
risk = squash( Σ wᵢ · deviationᵢ )        weights from config/risk.yaml, never inlined
```

**Confidence is separate from risk** and is a function of evidence quality, not severity:

```
confidence = f(n_cell_effective, baseline_age, feature_completeness, deviation_tier)
```

A high risk with low confidence must render differently in the UI than a high risk with high
confidence. Bands (`NORMAL` / `ELEVATED` / `UNUSUAL` / `HIGH_DEVIATION`) are config, not constants.

**Every risk output carries its evidence** — the ranked per-feature deviations that produced it.
A score without evidence is a bug, enforced by the type system (§8).

---

## 8. Data model

```
users(id, created_at, timezone, onboarding_completed, baseline_status)
sessions(id, user_id, app_id, started_at, ended_at, duration_s, event_count)
events(id, session_id, ts, type, delta, from_index, to_index, direction)
windows(id, session_id, start_ts, end_ts)
window_features(window_id, <feature columns>, feature_version)
baseline_cells(user_id, context_key, feature_name, mean, std, median, mad, iqr, n, updated_at)
deviations(window_id, feature_name, z_robust, tier)
risk_scores(id, window_id, score, confidence, state_dist, model_version, baseline_version, feature_version, created_at)
insights(id, user_id, session_id, type, severity, title, message, evidence_json, created_at, dismissed_at)
interventions(id, user_id, window_id, level, delivered_at, response, reward)   -- M6
```

`events` stores **no content** — no text, no media, no identifiers, no view labels. Only event
type, timing, and displacement. This is enforced at the capture boundary, not downstream.

**Shared types** live in a JSON Schema consumed by Kotlin (kotlinx.serialization) and Python
(Pydantic). A risk score is representable only with its evidence attached.

---

## 9. Reproducibility

Every stored prediction carries `feature_version`, `baseline_version`, `model_version`, and
deviation tier. Any prediction must be re-derivable from stored features plus those versions.

**Cross-language parity** is a real risk: the Kotlin on-device extractor and the Python offline
extractor must produce identical values or every offline result is invalid. Enforced by **shared
golden vectors** — a fixture of raw event sequences with expected feature outputs, run as a test
suite in both languages. This is the first test written in M2.

---

## 10. Milestones

Gates are real. M0 and M4 can each end the project as specified, and that is the point.

| | Milestone | Deliverable | Gate |
|---|---|---|---|
| **M0** | Feasibility spike | Per-app event availability table (§2) | **GO/NO-GO on the whole Android route** |
| M1 | Capture + storage | AccessibilityService, Room schema, encrypted local buffer, onboarding + consent | Dogfood on own device; content-free audit passes |
| M2 | Feature extractor | Kotlin + Python extractors, golden-vector parity suite | Parity tests green |
| M3 | Baseline + deviation | Baseline engine w/ shrinkage, both deviation tiers, contamination guards | Synthetic pipeline test recovers injected anomalies |
| **M4** | **Ablation harness** | Offline Python: subject-wise CV, ablation ladder A→E, PR-AUC + calibration | **Are the B−A and D−C gaps real?** |
| M5 | UI + insights | Compose dashboard, learning mode, session cards, explanations | No score renders without evidence |
| M6 | Intervention engine | Graded levels, LinUCB policy, kinematic-change reward | **Requires IRB** |
| M7 | Provisional filing | Filed before any disclosure | **Precedes M8** |
| M8 | Study + paper | MRT/A-B-n, benchmark vs. re-implemented Time2Stop | — |

**M4 — REMOVED FROM SCOPE, 2026-09-20.** It was the honest gate: per blueprint §19, if D−C ≈ 0 then
personalisation is empirically unsupported and the contribution must be repositioned.

**The gate fired, and it was answered without M4.** EXP-003 returned D−C ≈ 0 on the only valid real
contrast (0.821 vs 0.825, p = 0.33); EXP-010 confirmed it under the stronger PCA detector
(+0.003, p = 0.85); EXP-008 explained the mechanism. The contribution has been repositioned
accordingly — see `paper/DRAFT.md` §0. Running M4 now would answer a question already answered.

**Its remaining purpose would have been to score the six Android features offline, and that is
deliberately not being done.** No dataset pairs naturalistic scroll telemetry with the outcome of
interest, so the harness could only produce an accuracy figure for a proxy task. Such a figure would
be quoted as though it were the real one. **PRECOG ships with no detection-accuracy claim**, in the
app (`SettingsScreen` says so to users) and in the paper.

M7 is also inactive: the patent route was closed by the disclosure decision of 2026-09-20.

**Synthetic data** (KT §49–50) is an integration test for M3, not evidence. Injecting anomalies and
then detecting them is circular. Synthetic results are never reported as empirical findings.

**Real data:** M1–M3 validate on self-collected n=1 dogfooding. Anything involving other
participants needs ethics approval before collection begins, not before analysis.

---

## 11. Evaluation protocol

- **Splits: subject-wise (leave-users-out).** Never random. Random splits leak a user across train
  and test and inflate every metric — the first thing a reviewer checks.
- **Report both** within-user (personalized) and cross-user (cold-start) settings.
- **Primary metric: PR-AUC.** Compulsive sessions are the minority class; accuracy and ROC-AUC
  flatter it.
- **Calibration is mandatory** — reliability diagram, ECE, Brier. A percentage shown to a user must
  mean what it says.
- **False-positive rate is a first-class outcome**, plus alerts-per-user-per-week. Alert fatigue is
  a product failure, not a rounding error.
- **Ablation ladder:** A screen-time only → B +kinematics → C +temporal context → D +personalized
  deviation → E full. Report each increment with effect size and CI.

---

## 12. Open items

1. **M0 outcome** decides whether any of this survives contact with Instagram and TikTok.
2. **Session-level labels.** Person-level SAS-SV/BSMAS cannot label individual sessions. Plan is
   in-the-moment ESM prompts, triangulated with behavioural proxies — needs design before M4.
3. **Logo positioning.** `PRECOG_pfp.png` is neon-cyberpunk with a surveillance-eye motif, which
   contradicts KT §55 and works against the anti-surveillance differentiation the blueprint builds
   in §20. Recommend a redesign before any external use.
4. **Score naming.** Blueprint recommends `PSD-Risk` over `CSI` (overloaded). Not yet adopted.
5. **`PRECOG_Literature_Review.docx`** is superseded by `_1` and should be archived to avoid citing
   the stale copy.

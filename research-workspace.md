# Research Workspace — PRECOG

_Last updated: 2026-09-20 · Current phase: 11 (writing) · **Next action: select the venue — it blocks
Abstract trimming, section structure and length.** Draft at `paper/DRAFT.md`._

## Snapshot

- **Title (set 2026-09-21):** ***Not Every Deviation Is Personal: A Precondition for Personalised
  Behavioural Baselines in Scroll-Based Deviation Detection***
- **Retired:** the old working title promised *False-Positive Reduction versus Global Thresholds*,
  which is the result that did not hold. A reader could have falsified it by reaching §5.3.
- **Alternates:** *When Personalisation Helps: Person-Relative versus Population-Consistent
  Deviation in Behavioural Baselines* · *Personal Baselines Are Conditional*
- **Target venue:** — (TBD). Deadline fixed at **2026-10-25** (same date as ML and UI/UX course
  submissions). Venue not yet selected — see Risks.
- **Acceptance status:** drafting / experiments in progress
- **Patent track:** **closed 2026-09-20.** The review APK was shared without a provisional filing,
  knowingly accepting the loss of Indian novelty. Publishing and a public repository are unblocked.

## Problem & Gap

**Problem.** Digital-wellbeing tools operate on aggregate screen time and fixed thresholds. They
treat all minutes as equivalent, apply population thresholds that are wrong for individuals, and
cannot distinguish a deliberate long session from a compulsive one.

**Gap (narrow, defensible).** Scroll kinematics are a mature field — but used almost exclusively for
*authentication* ("who is this?"), never for *deviation from a person's own normal*. Time2Stop
(CHI 2024), the dominant prior art, is adaptive and explainable but runs on coarse features only:
unlock counts, app-visit frequency, notifications, lux. No kinematics, no inter-scroll timing.

**What this paper claims (restated 2026-09-21).** Learnability and stability of personal baselines;
a **precondition** on when personalisation helps; and what survives deployment. It no longer claims
false-positive reduction — EXP-003/010 returned a null and the claim was retired with the title.

**What it does NOT claim.** Not compulsive-use detection: no *public touch* dataset carries such an
outcome. Note the nuance uncovered on 2026-09-21 — Shin & Dey 2013 **did** have labels, from the
Mobile Phone Problem Usage Scale administered to 48 participants. So the honest statement is not
"nobody has labels"; it is that labels require recruiting participants and administering a validated
instrument, their dataset is unreleased, and we decline to manufacture a proxy. No accuracy figure
is claimed anywhere.

## Method & Data

**Methods.** Touchalytics-compatible gesture features → per-user baseline with empirical-Bayes
context shrinkage → three-tier deviation (robust-z; **GMM-2 density**; **PCA reconstruction error**,
which leads) → ordered behavioural states. Mahalanobis is retained for per-feature attribution only.
Interpretable and statistical before anything deep. *(Updated 2026-09-20 per EXP-009 and EXP-013;
the old two-tier Ledoit-Wolf description is superseded.)*

**Datasets** (all public; details in `docs/DATASETS.md`):

| Dataset | Role | Status |
|---|---|---|
| **HMOG** (100 users × 24 sessions) | **Primary** — event timing *and* kinematics | extracted: 39,556 gestures, 99 subjects |
| FETA (470 users, 31 d) | Replication, scale | user re-downloading raw |
| Tappigraphy (189 users, hourly) | Naturalistic context | hourly aggregates only |
| AITouch (45 users, tablet) | — | **dropped**: games on a tablet, wrong behaviour |

**Known data limitations.** HMOG pressure is constant 1.0 (2014 devices) — Touchalytics' 3rd-ranked
feature is unavailable, so cross-dataset comparison must exclude it. HMOG is a lab reading task, not
free browsing. Tappigraphy has no per-event data, so the sleep-displacement label route is closed.

## Experiments

**Completed**

| ID | Hypothesis | Result |
|---|---|---|
| **EXP-001** | H1 — scroll kinematics are individually distinctive | **Supported, moderate.** Median ICC 0.161; 88.5% of gestures closer to own centroid; AUC 0.787; single-gesture ID 15.0% vs 1.0% chance. Kinematics alone: 9.8%, AUC 0.741. **Per-subject accuracy ranges 0%–65.9%** |
| **EXP-002** | H2 — baselines converge and stabilise | **Supported.** Median subject reaches ρ≥0.95 at **n=80 gestures (~2.1 sessions)**; 75% by n=150 (~3.8 sessions) |
| **EXP-003** | H3 — personalized beats global on FPR | **NOT SUPPORTED.** On real sit→walk change (82 subjects): personalized 0.821 vs global 0.825 (p=0.33, no benefit) and both significantly *worse* than a single fixed threshold at 0.712 (p=4e-07) |

**EXP-003 consequences — the paper's claim has changed.**
The headline can no longer be "personalization reduces false positives." Likely cause: walking
changes scroll behaviour in a *population-consistent* way, so a global model already captures it.
Personalization can only pay when normal differs between people **and** the deviation is meaningful
only relative to that personal normal. The premise is **untested**, not falsified — no dataset
contains the person-relative deviation the premise is about.

Two methodological lessons recorded there: a semi-synthetic injection arm was **circular by
construction** (shift injected along named features, then detected by a threshold on those features)
and its numbers are void; and an earlier apparent win came entirely from a **weak scorer** —
mean-z across 29 features (AUC 0.545) vs the Mahalanobis tier the SPEC specifies (AUC 0.868).

| **EXP-006** | Does personalization help distinctive users? | **Trend only, not significant.** Spearman(distinctiveness, C−B) = −0.110 (p=0.33). Top quartile: C−B = −0.019, 67% of subjects favour personalization, **p=0.117**. Underpowered at n=21/quartile — data are consistent with a small benefit *and* with none |

| **EXP-004** | Does the null hold on a second contrast? (reading→map) | **Personalization beats global, p=0.044** — but does not survive Holm correction across two contrasts (p≈0.089). **Replicated finding: one fixed threshold beats both multivariate models** (A 0.394 vs C 0.597 vs B 0.631; δ=+0.39) |

| **EXP-007** | XGBoost + SHAP, GRU | **Caught a validity failure.** PR-AUC **1.000** on both task contrasts — SHAP showed the models were reading *gesture direction*, not behaviour. **GRU lost to XGBoost** (0.597 vs 0.628) on the one valid contrast |
| **EXP-008** | Synthetic mechanism test | **Confirmed EXP-003's explanation.** Clean sign flip: personalization is worse for population-consistent deviations (C−B = +0.009…+0.026, all p<1e-5) and better for person-relative ones (−0.009…−0.073) |

## ⚠ MAJOR CORRECTION — 2026-09-20

**Two of three real contrasts are invalid.** Reading is 98% vertical vs map 48%; FETA scroll is
**99.2% vertical vs swipe 1.7%**. Trained classifiers hit PR-AUC 1.000, and removing direction
features does not fix it — leakage relocates to start position and straightness. **These are
different gesture types, not behavioural deviations.**

**Withdrawn:** EXP-004 (reading→map) and EXP-005c (scroll→swipe, which had been the strongest
personalization signal at 79% of subjects). Both READMEs annotated.

**Survives:** EXP-001/005a distinctiveness, EXP-002/005b convergence and drift (no contrast
involved), EXP-003 sit→walk null (same task, same gesture type — **the only valid real contrast**),
EXP-008 (controlled generation).

**Net position.** The personalization question now rests on one real null plus one synthetic
mechanism test, and they agree: personalization pays only for person-relative deviations.
**Whether compulsive scrolling is person-relative is unknown and no public dataset can answer it.**

**New protocol rule.** Before using any contrast, verify no single feature separates the classes
near-perfectly. A model that performs perfectly is investigated, not celebrated.

| **EXP-009** | Full model ladder, supervised + unsupervised | **LogR 0.600 ≈ XGBoost 0.628 with half the variance** — gradient boosting is not needed either. NB 0.550 vs LogR 0.600 *measures* the independence failure. **PCA reconstruction wins the unsupervised arm on all three conditions** — FPR at 80% sensitivity, **lower is better**: 0.787 / 0.671 / 0.536 vs Mahalanobis 0.823 / 0.789 / 0.586 |

**Model decisions taken 2026-09-20.**
- **PCA reconstruction error added as `SPEC.md` §5 tier 3** — the primary detector. Mahalanobis
  retained for per-feature attribution, since `evidence-required` forbids an unexplained score.
  PCA detects, Mahalanobis explains.
- **Logistic regression is the default supervised rung**, not XGBoost.
- **GRU retired** — 4th of 8, beaten by a linear model. Blueprint Principle 8 satisfied and
  documented.
- The EXP-008 mechanism survives four independent detectors, so it is a property of the problem
  rather than an artifact of the scorer.

| **EXP-010** | H3 re-test with PCA reconstruction | **Null survives the better detector.** HMOG sit→walk: PCA C−B=+0.003 p=0.85, Mahalanobis C−B=0.000 p=0.28. The null is now settled under both scorers. EXP-008's sign flip largely collapses under PCA because the strong global baseline leaves little for personalization to add. |

| **EXP-011** | PCA component sweep (k=2…25) | **k=8 is justified — curve flat above k=5.** PR-AUC varies only 0.006 from k=5 to k=25 on the pooled arm. k=8 covers 85% of variance and sits in the flat plateau. Choice is robust to ±4 components. Best k=25 (0.610) gains only +0.025 over k=8 (0.585). |

| **EXP-012** | Feature selection by SHAP rank | **Full set wins, margin small (+0.005 over top-10).** Top-3 (mid_stroke_area, duration_ms, inter_scroll_ms) loses only 0.005. Selection monotonically hurts — the bottom-ranked features carry real correlated signal that LogR exploits. Full 28-feature set recommended; top-5 if dimensionality-constrained. |

| **EXP-013** | Per-user GMM vs single-Gaussian (Mahalanobis) | **Strongest positive result in the project.** GMM-2 FPR at 80% sensitivity: HMOG 0.746 vs Mah 0.810 (−0.064); synthetic person-relative 0.328 vs 0.455 (−0.127); synthetic pop-consistent 0.364 vs 0.633 (−0.269). Single-Gaussian assumption is wrong for multi-posture users. **SPEC update required: GMM-k (k=2 default) replaces Mahalanobis as tier-2 density estimator.** Mahalanobis retained for attribution only. |

| **EXP-014** | Session-level aggregation (windows 1–40) | **Null — aggregation does not help on sit→walk.** PR-AUC flat 0.574–0.587 across all window sizes. Reason: walk gestures are uniformly distributed throughout sessions (~60% prevalence), so there is no temporal concentration for aggregation to exploit. The real PRECOG use case (episodic compulsive sessions) would have temporal structure; this null reflects the proxy contrast, not the eventual deployment scenario. |

### M0 — Android observability spike (a paper result, not just engineering)

Run on a real device (Android 16, `000563491000004`) across Instagram, Reddit, X and YouTube.
This has been sitting in `android/m0-spike-archive/` as an engineering note; it belongs in the
paper, because it is a measured negative result about what the deployment platform permits.

**Finding 1 — the feature set does not transfer.** The offline experiments use a **28-feature
Touchalytics-compatible set** (`mid_stroke_area`, `duration_ms`, stroke geometry, velocity profile,
pressure). Every one of those requiring raw `MotionEvent` data is **unreachable from a third-party
Android app**: an accessibility service is delivered `TYPE_VIEW_SCROLLED` events, not touch points —
no pressure, no contact area, no per-sample coordinates, no stroke geometry. The shipped app
computes **six timing features**: median inter-event gap, burstiness, passive ratio, reversal rate,
delta magnitude, event rate. **This is a reduction in signal, not an equivalent substitution**, and
every offline result built on the 28-feature set is therefore an **upper bound** on deployed
performance, not a prediction of it.

*Exact counts are not asserted here.* The offline 28-feature set and the SPEC §4 PRECOG feature set
are different lists, and the mapping between them has not been tabulated. **Action: build that
mapping table before writing the Methods section** — a reviewer will ask which features survive and
"about six" is not an answer.

⚠ **Naming collision to fix before publication.** `passive_ratio` means two different things:
SPEC §4 defines it as *windows with scrolls and zero clicks ÷ all windows*; the Android app defines
it as *fraction of inter-event gaps below 400 ms*. Same name, different quantity. This is precisely
the silent substitution the project rules forbid. Rename one of them.

**Finding 2 — scroll displacement is reported inconsistently across apps.** No single field works:

| App | `scrollDeltaY` (API 28+) | `scrollY` | Usable strategy |
|---|---|---|---|
| Instagram | real values | constant | use `scrollDeltaY` |
| Reddit | constant `-1` sentinel | varies | difference successive `scrollY` |
| X | real values | varies | either |
| YouTube | **no events at all** | — | **excluded** — SurfaceView rendering emits zero `TYPE_VIEW_SCROLLED` |

The shipped app resolves in that order and returns *null* when neither field is usable, so an
unavailable measurement is never laundered into a plausible-looking zero. **YouTube is documented
absent, not silently dropped** — a wellbeing tool that cannot see the largest video feed on the
device should say so.

**Finding 2b — one swipe is not one event.** Measured 2026-09-21: ten deliberate swipes produced
54 `TYPE_VIEW_SCROLLED` events, ~5.4 per swipe, because the platform reports throughout a fling's
deceleration. Any paper reporting "scroll events" from an accessibility service is therefore
reporting a unit that is **not** the human gesture, and inter-event timing statistics computed over
them are dominated by fling mechanics rather than by user pacing. This is not documented in the
Android API reference and we have not seen it stated in the touch-behaviour literature, which works
exclusively from `MotionEvent` boundaries where the distinction does not arise.

**Finding 3 — the privacy claim is structural, not a promise.** `canRetrieveWindowContent="false"`
means screen text is unreadable at the capture boundary, and the manifest declares **no `INTERNET`
permission** — verified against the built APK on 2026-09-20. Exfiltration is not policy, it is
absent capability.

**Why this matters to the paper.** Every prior touch-behaviour paper in `RELATED_WORK.md` §B works
on datasets collected by instrumented research apps with full `MotionEvent` access. None of them
state what survives outside that setting. This is a short, checkable, negative systems result that
constrains the whole literature's deployability — and PRECOG is in a position to report it.

**Analysis discipline.** Four strata have already been tested in EXP-006. No further slicing to
find a significant subgroup — that is p-hacking and would not replicate.

**Applied 2026-09-20.** SPEC §5 tier 2 now specifies GMM-2; a metric-label error in the EXP-009
table (headed "PR-AUC, higher is better" when the source README says "FPR at 80% sensitivity, lower
is better") was corrected — as written, the SPEC's conclusion contradicted its own numbers.
Paper draft started at `paper/DRAFT.md`; contribution repositioned around the null.

**Historical note — the item this replaces.** EXP-013 required a SPEC §5 tier-2 revision: replace single-Gaussian
Mahalanobis with GMM-2 as the density estimator. EXP-010 arms B/C would improve equally under
GMM-2, preserving the H3 null — a re-run is not required to validate the null, but noting this
in SPEC is necessary for reproducibility.

## Assets

**Figures** (`results/figures/` — generated 2026-09-20)
- fig-02 ICC by feature (HMOG + FETA) · fig-03 convergence curves (HMOG vs FETA full vs matched)
- fig-05 per-subject accuracy spread (histogram, replicated) · fig-06 drift over days (+12%/30d)
- fig-07 model ladder (supervised + unsupervised) · fig-08 SHAP importance (sit→walk)
- fig-09 PCA sweep (k=2…25) · fig-10 session aggregation · fig-11 GMM comparison · fig-12 feature selection
- fig-01 pipeline architecture — **generated** (`fig-01_pipeline-architecture.pdf/png`)

**Tables** (`results/tables/`)
- tab-02 model comparison — **generated** (`tab-02_model-comparison.csv`)
- tab-01 dataset comparison — **generated** (`tab-01_dataset-comparison.csv`)
- tab-03 feature set vs Touchalytics — **generated** (`tab-03_feature-comparison.csv`)

**Reports** (`reports/`)
- `ml-course-report.html` — ML course deliverable, generated 2026-09-20, all 14 experiments covered

**References.** 22 papers in `references/papers/`, filenames are BibTeX keys. Annotated in
`docs/RELATED_WORK.md`. **The 10 arXiv-prefixed entries were verified against the arXiv API on
2026-09-20** and written to `paper/bib/precog-arxiv.bib` — author lines, titles and years are now
authoritative. Four were published elsewhere and are typed `@article` so the published version is
cited: Steil 2018 (DOI 10.1145/3229434.3229439), Lamb 2020 (IJCB, 10.1109/IJCB48548.2020.9304876),
Mahbub 2016 (BTAS, 10.1109/BTAS.2016.7791155), Lee 2026 (Tapia 2026). One placeholder remains:
GANTouch's arXiv comment claims IEEE TBIOM 2022 but the record carries no DOI — confirm on Xplore.
Nine further papers cited in the literature review are paywalled and not yet obtained.

**Two citation-hygiene issues surfaced by the verification.**
- Four of the ten (Dave, Pelto, Deridder, Vanamala) come from **one research group with overlapping
  authorship**. Citing them as four independent confirmations of touch-dynamics authentication would
  overstate the breadth of the evidence. Cite one or two as representative, or say they are a group.
- Ref #17 (gender bias in touch biometrics) is a **4-page Tapia 2026 conference paper**, not an
  archival study. It is too slight to carry the fairness argument in `SPEC.md` §20 on its own.

## On-device observation log (opened 2026-09-20)

The shipped app is now generating real data on one device (Android 16). This is **not** a study and
nothing here is a result — n = 1, the observer is the author, and there are no labels. It is
recorded because two numbers are worth watching and because deciding what they mean *after* seeing
them would be post-hoc.

**Stated in advance, 2026-09-20 23:50.** First readings: Reddit·Night baseline built from 48
windows at moderate confidence; median inter-event gap 104 ms; 5.1 events/sec; 89% unbroken.
Day totals: 21 sessions, 1159 events, **6 flagged (29%)**.

| Watch | Why | What would change the paper |
|---|---|---|
| **Flag rate** | 29% of sessions flagged on a 48-window baseline is high. EXP-009 measured per-gesture FPR at 0.54–0.82 and session aggregation was supposed to reduce it | If it stays near 30% as the baseline matures, session aggregation does **not** rescue the per-gesture false-positive rate in deployment, and §6 of the draft must say so. If it falls, that is evidence aggregation works outside the sit→walk proxy — which EXP-014 could not show |
| ~~Events vs swipes~~ | **RESOLVED 2026-09-21 — see below** | — |

**Do not tune thresholds during the observation window.** Adjusting `DISTRACTED_AT` now would be
fitting to a single user's first day.

### RESOLVED 2026-09-21 — the unit is the scroll event, not the swipe

**Measurement.** Ten deliberate swipes, each with a clear pause between them, produced **54
`TYPE_VIEW_SCROLLED` events**. Android reports repeatedly while a fling decelerates.

**Ratio: 5.4 events per swipe** (n = 1 session, one device, one app — quote it as approximate, and
as a single observation rather than a characterised distribution).

**Corrections that follow.**

| Was stated as | Actually |
|---|---|
| Enrolment ≈ 500 swipes per cell | 500 scroll **events** ≈ **93 swipes** — the gate is ~5× easier to reach than documented |
| "1159 scroll swipes today" | 1159 events ≈ **215 swipes** |
| Median gap 104 ms "between swipes" | 104 ms between **scroll steps** — this is intra-fling spacing |

**The consequential one: `MEDIAN_GAP` is not measuring human pacing.** Most of its gaps fall
*inside* a single fling, so it largely measures how the platform samples a decelerating scroll, not
how long a person pauses before swiping again. `UNBROKEN_RATIO` inherits the same problem from the
other direction — nearly every intra-fling gap is under its 400 ms threshold, which is why the
device reports 89% "unbroken". Both features are still *computable* and may still be
person-distinctive, but the **interpretation** attached to them was wrong.

**What was changed** (app rebuilt, release APK reissued):
- All user-facing wording now says "scroll step", not "swipe" — `Feature.kt`, Home, History,
  Session detail, Patterns, Settings, Onboarding.
- Patterns explains the relationship directly rather than hiding it: twenty steps per reading,
  several steps per swipe as a flick slows.
- `Feature.kt` carries the measurement in its doc comment so the next reader cannot re-acquire the
  misunderstanding.

**What was deliberately NOT changed.** The extractor still windows over raw events. Grouping events
into swipes by a gap threshold would give genuinely swipe-level features — and would invalidate the
48-window baseline already on the device, five weeks before the deadline. **Recorded as future
work, not done now.** See the draft's Limitations.

**Does this invalidate any published claim?** No. Every offline result (EXP-001 to EXP-014) was
computed on HMOG/FETA gesture-level data with real `MotionEvent` boundaries, where a gesture is a
gesture. This affects only the Android implementation and its description — which is exactly what
§5A of the draft is about, so it strengthens that section rather than undermining it.

**Review the flag rate on 2026-09-27.**

---

## Review & Revision

- Reviewer comments: — (none yet; run Phase 12 reviewer simulation once a draft exists)
- Revision history: — (n/a)

## Quality gates

- **Phase 8 (experiment design): PASS with one open item.** Subject-wise/contiguous splits are in
  place per FETA pitfall P3; versioning and seeds recorded; golden vectors lock feature parity.
  *Open:* venue not selected, so per-section alignment scoring cannot run.

## Standing risks

| Risk | Severity | Mitigation |
|---|---|---|
| **Venue unselected with a fixed 2026-10-25 deadline** | **High** | Select this week; a full CHI/IMWUT paper is likely unreachable — workshop/short track is the honest target |
| H3 null — confirmed | Resolved | Null confirmed under both Mahalanobis and PCA reconstruction (EXP-010). Reposition to distinctiveness + drift + well-characterised null as the contribution. |
| No true labels in any dataset | High | Already scoped out of the claim; state prominently in Limitations |
| Per-user distinctiveness varies 0–66% | Medium | Report the distribution, not the mean; feed into the confidence measure |
| 10 unverified reference author lines | Resolved 2026-09-20 | Verified against the arXiv API; `paper/bib/precog-arxiv.bib`. One open placeholder (GANTouch venue) |
| 9 paywalled papers not obtained | Medium | Routes: PMC, author preprints, INFLIBNET N-LIST, email authors. Shin & Dey 2013 and *Scrolling in the Deep* (CHI 2025) are the two that must actually be read |
| Three deliverables, one date | Medium | Courses take priority; paper may target a later cycle |
| M4 removed from scope 2026-09-20 | Accepted | The gate it existed to test was answered by EXP-003/008/010. Consequence: **no detection-accuracy figure is claimed anywhere**, deliberately. A reviewer may push; the answer is in SPEC §10 |
| Deployed flag rate may be ~29% | Open | Under observation, review 2026-09-27. Either direction is reportable |

# Not Every Deviation Is Personal
### A Precondition for Personalised Behavioural Baselines in Scroll-Based Deviation Detection

_Title set 2026-09-21, replacing "Personalized Behavioural Baselines over Scroll Kinematics:
Learnability, Stability, and False-Positive Reduction versus Global Thresholds" — which promised
false-positive reduction the work did not find. A title that a reader can falsify by reaching §5.3
costs more credibility than a modest one ever saves._

**Alternates, if the venue prefers a declarative title:**
- *When Personalisation Helps: Person-Relative versus Population-Consistent Deviation in Behavioural
  Baselines*
- *Personal Baselines Are Conditional: A Negative Result, a Mechanism, and What Survives Deployment*


_Started 2026-09-20. Markdown deliberately: the venue is not selected, so this holds **content**,
not formatting. Pour it into the template once the venue is fixed._

**Conventions in this file.** `[GAP]` marks something that does not exist yet and must be written or
measured. `[VERIFY]` marks a number or claim taken from a secondary source that has not been checked
against the primary. Nothing in this draft may be submitted while either marker remains.

---

## 0. The repositioning (read this first)

The paper that was planned cannot be written. The paper that can be written is better, and this
section says why.

**What was planned.** "Personalised behavioural baselines reduce false positives relative to global
thresholds." H3.

**What happened.** EXP-003 returned a null on the only valid real contrast: personalised 0.821 vs
global 0.825 (p=0.33). EXP-010 re-ran it under the stronger PCA detector and the null survived
(C−B = +0.003, p=0.85). Then the 2026-09-20 correction withdrew EXP-004 and EXP-005c after
discovering that their class labels were separable by gesture direction alone — reading is 98%
vertical against map at 48%, FETA scroll is 99.2% vertical against swipe at 1.7%. Those were
different gesture types, not behavioural deviations.

**Why the honest version is stronger.** The reason for the null is now understood, not merely
observed. EXP-008 generated deviations of two kinds under controlled conditions and found a clean
sign flip: personalisation is **worse** than a global model for population-consistent deviations
(C−B = +0.009 to +0.026, all p < 1e-5) and **better** for person-relative ones (−0.009 to −0.073).
Walking changes how everyone scrolls in the same direction, so a global model already captures it
and a personal baseline only adds variance.

This matters beyond PRECOG. Tolosa et al. (Electronics 2026) and Diaz et al. (U-BEHAVED, Sensors
2022) both build personalised rolling baselines and both *assume* personalisation helps. Neither
tests it. This paper can give that literature a conditional answer.

### Contribution statement (the claim, as it now stands)

1. **Scroll kinematics are individually distinctive, and unevenly so.** Median ICC 0.161, AUC 0.787,
   88.5% of gestures nearer their own subject's centroid. Per-subject identification accuracy ranges
   **0% to 65.9%** — the distribution, not the mean, is the result.
2. **Personal baselines converge quickly.** The median subject reaches ρ ≥ 0.95 at **n = 80
   gestures** (≈2.1 sessions); 75% by n = 150.
3. **Personalisation is conditional, and we characterise the condition.** It pays only when the
   deviation is person-relative. For population-consistent deviations a global model wins and a
   single fixed threshold beats both. Demonstrated on real data and explained on synthetic.
4. **A negative systems result about deployability.** Outside an instrumented research app, the
   Touchalytics feature family is unobtainable on Android. Six timing features survive. Every
   result in this literature, including ours, is an upper bound on what ships.
5. **An implemented, offline, on-device system** that carries its evidence and confidence with every
   score, and refuses to score when confidence is too low.

### What this paper explicitly does not claim

- **Not compulsive-use detection.** No public dataset pairs naturalistic scroll telemetry with
  compulsive-use labels. Nothing here is validated against that outcome.
- **No accuracy figure for the deployed system, permanently.** The Android six have never been
  evaluated against labelled data, and **the M4 ablation harness has been removed from scope**
  (decided 2026-09-20). This is not a gap to be filled later in this paper: no dataset pairs
  naturalistic scroll telemetry with the outcome of interest, so an offline ablation would produce
  an accuracy figure for a proxy task and invite exactly the misreading the paper is trying to
  avoid. **The system ships and is described without a detection-accuracy claim.** Say this in the
  abstract, not only in Limitations.
- **Nothing clinical.** Deviation, not diagnosis.

---

## 1. Abstract

_Drafted 2026-09-20, venue-neutral. ~210 words; trim to the venue's limit last, cutting from the
method sentence first and never from the null._

Digital wellbeing tools measure aggregate screen time and compare it against population thresholds.
This treats every minute as equivalent and fits no individual well. A natural correction is to model
each person against their own prior behaviour, and personalised baselines have become a common
design choice in behavioural sensing — but the assumption that personalisation reduces false alarms
is rarely tested. We test it on scroll kinematics, using 39,556 gestures from 99 subjects. We find
that scroll behaviour is individually distinctive but very unevenly so, with per-subject
identification accuracy ranging from 0% to 65.9%, and that a personal baseline stabilises after
roughly 80 gestures. We then find **no false-positive benefit** from personalisation on our one
valid behavioural contrast, and a single fixed threshold outperforms both personalised and global
multivariate models. Controlled experiments explain why: personalisation helps only when a deviation
is person-relative, and is actively harmful when the deviation is population-consistent. Separately,
we report what survives deployment: outside an instrumented research app, an Android application
cannot obtain the touch kinematics this literature is built on, and six timing features remain. We
describe an implemented on-device system that reports evidence and confidence with every score, and
we make no detection-accuracy claim.

**Keywords.** behavioural baselines; scroll kinematics; digital wellbeing; anomaly detection;
negative results; on-device sensing

---

## 2. Introduction

_Full prose drafted 2026-09-20, venue-neutral. Five beats. Compress beats 1–2 for a short track._

A person who has spent ninety minutes on a social feed has spent ninety minutes on a social feed.
Digital wellbeing tools can say that much, and for most of them it is all they say. Time is counted,
a threshold is applied, and a notification arrives. The threshold is set at population level, which
means it is wrong for almost everyone individually: ninety minutes of deliberate reading and ninety
minutes of compulsive scrolling are indistinguishable to a clock. A systematic review and
meta-analysis of digital self-control tools estimates their pooled effect on time spent at Hedges'
*g* = 0.47 (95% CI [0.27, 0.68]) — small to medium, and real — while finding that such tools are
overwhelmingly self-monitoring in nature and are evaluated over an average of just 22.6 days
[Roffarello & De Russis 2023]. The call is not to abandon them but to move past statistics and
timers toward interventions tailored to a user's current state.

If the problem is that population thresholds fit no individual, the obvious correction is to compare
a person against themselves. This idea is not new and it is increasingly common: recent work models
behavioural drift against rolling, per-user baselines over activity, sleep and communication
[Tolosa et al. 2026], and earlier work established personalised baselines with robust dispersion for
physical-activity change [Diaz et al. 2022]. What is striking about this literature is that the
central premise is assumed rather than measured. Personalisation is adopted because it is
intuitively right, and the question of whether it actually lowers false alarms is left open.

The signal we test it on is scroll kinematics. Touch and scroll dynamics are a mature measurement
field, but an almost exclusively single-purpose one: they are used to answer *"is this the right
person?"* for continuous authentication, and essentially never *"is this person behaving unlike
themselves?"* The dominant prior art on the intervention side, Time2Stop (CHI 2024), is adaptive and
explainable but operates on unlock counts, app-visit frequency, notifications and ambient light —
coarse features, no kinematics, no inter-scroll timing. The pieces for a personalised
deviation model exist in two separate literatures that have not been joined.

We join them, and the result is not the one we expected. Scroll behaviour is individually
distinctive, and personal baselines converge quickly enough to be practical. But on the one
behavioural contrast in our data that survives a leakage audit, personalisation gives **no
false-positive benefit** over a global model, and both are beaten by a single fixed threshold.
Rather than report this as a failed hypothesis, we characterise it: controlled experiments show a
clean sign flip in which personalisation helps for person-relative deviations and hurts for
population-consistent ones. That is a usable answer to the question the field has been assuming, and
it applies to any system built on personal baselines, not only to ours.

A second finding constrains all of this from a different direction. Every touch-behaviour result we
build on was collected by an instrumented research application with full access to raw touch events.
We implemented the system as an ordinary Android application and found that this access does not
exist outside the research setting: the platform delivers scroll notifications, not touch points, and
the feature family the field is built on largely disappears. Six timing features survive. This bounds
the deployability of the literature, and it is reported here as a measurement rather than an
engineering footnote.

We make no claim to detect compulsive use. No public dataset pairs naturalistic scroll telemetry with
that outcome, and we would rather state the boundary than gesture past it.

---

## 3. Related work

_Prose drafted 2026-09-21. Both previously-unobtained sources have now been read in full; the
characterisations below are from the papers, not from abstracts._

### 3.1 Touch and scroll kinematics: a mature measurement, a single question

Touch dynamics became a quantitative field with Touchalytics [Frank et al. 2013], which established
the feature family the area still uses: stroke geometry, velocity and acceleration profiles,
pressure, contact area, and the timing between strokes. HMOG [Sitova et al. 2016] and later FETA
[Georgiev et al. 2023] supplied the datasets, and a companion analysis of evaluation pitfalls
[Georgiev et al. 2022] established the methodological constraints — subject-wise splits above all —
that any credible result in this area must respect.

What is striking is how narrowly the measurement has been applied. Almost without exception the
question asked of these features is *"is this the right person?"*: continuous authentication
[Agrawal et al. 2022; Hu et al. 2022; Deridder et al. 2022], unsupervised per-user swipe modelling
for the same purpose [Lamb et al. 2020], benchmark datasets built for it [Mahbub et al. 2016]. The
underlying finding that makes authentication work — that people's touch behaviour is individually
distinctive — is precisely the finding a deviation detector would need. But the question *"is this
person behaving unlike themselves?"* is essentially unasked. The two framings are not equivalent:
authentication needs only that a person differ from **others**, whereas deviation detection needs
that a person's present behaviour differ from their own **past**, which is a strictly stronger
requirement and, as we show, one that does not follow automatically.

### 3.2 Personalised baselines: widely adopted, rarely tested

Outside touch sensing, modelling each person against their own history has become a common design
choice. U-BEHAVED [Diaz et al. 2022] detects physical-activity behaviour change by comparing
rolling windows of a participant's step counts against their own recent past with robust dispersion
estimates. More recently, Tolosa et al. [2026] detect behavioural drift for mental-health monitoring
across activity, sleep and communication, modelling deviations relative to rolling,
individual-specific baselines and grouping drift days into sustained streaks to separate persistent
change from transient noise.

Both are careful pieces of work, and both take the central premise as given. Personalisation is
adopted on the reasonable intuition that population norms fit no individual, and neither study
contrasts a personalised model against a global one to establish that the personalisation is what
produces the benefit. Tolosa et al. work at day scale over multimodal logs; U-BEHAVED at day scale
over step counts. Neither operates at gesture timescale and neither uses touch data, so our setting
is different — but the assumption we test is the one they share, and the answer applies to both.

### 3.3 Digital wellbeing: from detection to intervention

The automated detection line begins with Shin and Dey [2013], who instrumented 48 participants'
own Android phones for an average of 25.1 days and predicted problematic use from passive telemetry.
Their features are coarse and behavioural rather than kinematic — apps used per day, the ratio of
SMSs to calls, event-initiated session counts, apps per event-initiated session, non-event-initiated
session length — and with AdaBoost they reached 89.6% accuracy at an F-score of 0.707.

Two things about that paper matter for ours, and they pull in opposite directions. The first is that
**they had labels**: ground truth came from the Mobile Phone Problem Usage Scale, a validated
psychometric instrument, administered to participants. The second is that the labels were one-time
self-report used to split participants into groups, and the dataset is not public. This is the
precise reason we claim deviation rather than detection. The detection framing is available to
anyone willing to recruit participants and administer a validated scale; it is not available from
public touch datasets, none of which carry any such outcome, and we decline to manufacture a proxy
for it.

On the intervention side, Roffarello and De Russis [2023] provide the field's first systematic review
and meta-analysis of digital self-control tools. Their result is more nuanced than the common
shorthand that such tools do not work: across seven studies and 255 participants they estimate a
pooled effect of Hedges' *g* = 0.47 (95% CI [0.27, 0.68]) on reducing time spent — a small-to-medium
but statistically reliable effect. Their criticism is directed elsewhere: contemporary tools are
overwhelmingly self-monitoring in nature (statistics, self-imposed timers, lock-outs), evaluations
are short-term with an average duration of 22.6 days, and standardised measures are largely absent.
Their recommendation is to move past self-monitoring toward interventions that are tailored to a
user's current state and context.

That recommendation is the opening our work addresses, and Time2Stop [Orzikulova et al. 2024] is the
most direct response to it: an adaptive, explainable human-AI loop for overuse intervention. Its
sensing layer, however, remains coarse — unlock counts, app-visit frequency, notifications, ambient
light. No kinematics, no inter-event timing. The measurement literature of §3.1 and the intervention
literature of §3.3 have not been joined, and the personalisation assumption of §3.2 sits underneath
both without having been tested in either.

---

## 4. Method

**4.1 Features.** The offline work uses a 28-feature Touchalytics-compatible set. The mapping
between that set, SPEC §4 and the six Android-reachable features is
`results/tables/tab-03_feature-comparison.csv` — **this is Table 3 and it carries the paper's
sharpest systems claim.** Note the honest asymmetry recorded there: the Android set is *not* a
strict subset. Five of its six features have offline counterparts; `unbroken_ratio` (fraction of
inter-event gaps under 400 ms) has none. It is a reduction **plus one substitution**, and the paper
must say so rather than describing the app as running a subset of the offline pipeline.

**4.2 Context cells and shrinkage.** Cells are app × time-of-day. Cell estimates shrink toward
pooled global estimates with weight `w = n/(n+30)`, so a sparse cell borrows from the person's
overall pattern rather than asserting a baseline it cannot support.

**4.3 Detection.** Three tiers (SPEC §5): robust z per feature; GMM-2 density; PCA reconstruction
error. Selection is empirical, not assumed —

- GMM-2 over single-Gaussian Mahalanobis (EXP-013): FPR at 80% sensitivity 0.746 vs 0.810 on HMOG,
  0.328 vs 0.455 and 0.364 vs 0.633 on the two synthetic conditions. The single-Gaussian assumption
  is wrong for users who scroll in more than one posture.
- PCA reconstruction as primary detector (EXP-009), k = 8 at 85% cumulative variance, with EXP-011
  showing the curve is flat above k = 5 so the choice is robust to ±4 components.
- Mahalanobis **retained for attribution only.** A scalar score with no per-feature explanation
  violates the `evidence-required` rule. PCA detects; Mahalanobis explains.
- Logistic regression as the supervised rung, not gradient boosting: LogR 0.600 vs XGBoost 0.628
  PR-AUC, at half the variance. The GRU placed fourth of eight and was retired.

**4.4 Deployment.** On-device Android, accessibility-service capture, SQLCipher storage, no network
permission. Six features. Window = 20 events. Enrolment gate = 25 windows per cell, re-derived for
the window unit rather than carried over from the offline n ≥ 80 gestures.

---

## 5. Results

_Prose drafted 2026-09-21. Every number below is from `research/experiments/`; figure and table
references are to `results/figures/` and `results/tables/`._

### 5.1 Scroll behaviour is individually distinctive, and unevenly so

Across 39,556 gestures from 99 HMOG subjects, 88.5% of gestures lie closer to their own subject's
centroid than to any other, and same-subject versus different-subject separation reaches an AUC of
0.787. Single-gesture identification is correct 15.0% of the time against a 1.0% chance baseline.
Restricting to kinematic features alone drops this to 9.8% (AUC 0.741), which is the first
indication that inter-gesture timing carries a substantial part of the individual signal. Median ICC
across features is 0.161 (Figure 2).

These aggregate numbers conceal the result that matters. **Per-subject identification accuracy
ranges from 0% to 65.9%** (Figure 5). Some subjects are highly distinctive; others are not
distinguishable from the population at all. A mean would describe almost none of them. Any system
that assigns the same confidence to every user is therefore making a claim it cannot support for the
majority, and we return to this in §6.

### 5.2 Personal baselines converge within a few sessions

Baseline stability was measured by correlating a subject's running feature centroid against their
final centroid as gestures accumulate. The median subject reaches ρ ≥ 0.95 at **n = 80 gestures**,
approximately 2.1 sessions; 75% of subjects reach the same threshold by n = 150 (≈3.8 sessions)
(Figure 3). Enrolment is therefore practical: a deployed system does not need weeks of data before
it has a usable baseline.

Baselines are not static, however. Measured over the study period, feature centroids drift by
approximately +12% per 30 days (Figure 6), which any deployed system must accommodate through
adaptation rather than a one-time enrolment.

### 5.3 Personalisation gives no false-positive benefit on the one valid real contrast

We compare three arms at matched sensitivity (80%), reporting false-positive rate, where lower is
better: (A) a single fixed threshold, (B) a global multivariate model, and (C) a per-user
personalised model.

On the HMOG sit→walk contrast (82 subjects), personalisation gives **0.821 against the global
model's 0.825 — a difference of 0.004, p = 0.33**. There is no benefit. Re-running the comparison
under the stronger PCA reconstruction detector (§4.3) does not change the conclusion: C−B = +0.003,
p = 0.85 under PCA and C−B = 0.000, p = 0.28 under Mahalanobis. The null is stable across scorers.

The more uncomfortable result is that **a single fixed threshold beats both multivariate models, at
0.712 (p = 4×10⁻⁷)**. We report this prominently because it replicated across contrasts before two
of them were withdrawn (§5.6), and because it is the kind of finding a personalisation paper is
tempted to omit.

### 5.4 Why: personalisation is conditional on the deviation being person-relative

A null is only useful if its cause is understood. We generated deviations of two kinds under
controlled conditions: *population-consistent*, where a change moves all subjects in the same
direction in feature space, and *person-relative*, where each subject's change is defined relative
to their own baseline.

The result is a clean sign flip. For population-consistent deviations, personalisation is **worse**
than a global model (C−B = +0.009 to +0.026, all p < 10⁻⁵). For person-relative deviations it is
**better** (C−B = −0.009 to −0.073). The mechanism is straightforward in hindsight: when everyone
changes the same way, a global model already captures the change, and a personal baseline only adds
estimation variance. Walking is such a change — it alters how everyone scrolls, in the same
direction — which explains §5.3 directly.

This sign flip survives all four unsupervised detectors we tested, so it is a property of the
problem rather than an artifact of a particular scorer.

### 5.5 No evidence that personalisation rescues distinctive users

If personalisation fails on average, it might still help the subjects who are most distinctive.
It does not, at least not detectably. The correlation between a subject's distinctiveness and their
personalisation benefit is Spearman ρ = −0.110 (p = 0.33). In the most distinctive quartile, 67% of
subjects favour personalisation with a mean C−B of −0.019, but this does not reach significance
(p = 0.117) at n = 21 per quartile.

**This analysis is underpowered and we report it as such.** The data are consistent with a small
benefit and equally consistent with none. Four strata were pre-specified and tested; we performed no
further slicing, because searching subgroups until one reaches significance would not replicate.

### 5.6 Two contrasts withdrawn: a validity failure reported as a result

Supervised models reached **PR-AUC 1.000** on two of our three task contrasts. Perfect separation on
a behavioural task is not a success, and SHAP attribution showed why: the models were reading gesture
*direction*, not behaviour. The reading task is 98% vertical scrolling against the map task's 48%;
in FETA, scroll gestures are 99.2% vertical against swipe gestures' 1.7%. These were different
gesture **types**, not behavioural deviations of the same gesture type.

Removing direction features did not repair the contrasts — leakage relocated to gesture start
position and straightness. We therefore withdrew EXP-004 (reading→map) and EXP-005c (scroll→swipe),
the latter of which had been our strongest apparent personalisation signal at 79% of subjects
favouring the personalised model. The sit→walk contrast survives because it holds task and gesture
type constant and varies only posture.

We report this because the protocol rule it produced generalises beyond our study, and because
repurposed HCI datasets invite exactly this failure: **before using any contrast, verify that no
single feature separates the classes near-perfectly; a model that performs perfectly should be
investigated, not celebrated.**

Two further methodological corrections are recorded for the same reason. An early semi-synthetic
arm was circular by construction — a shift was injected along named features and then detected by a
threshold on those same features — and its numbers are void. And an earlier apparent personalisation
win came entirely from a weak scorer: mean-z across features (AUC 0.545) against the density tier
the design actually specifies (AUC 0.868).

### 5.7 Session-level aggregation does not rescue the per-gesture error rate here

Absolute false-positive rates across all detectors sit between 0.54 and 0.82, which is far too high
for a per-gesture alarm. Aggregating scores across windows is the obvious remedy, and we swept
window sizes from 1 to 40. Performance is flat throughout (PR-AUC 0.574–0.587).

The reason is a property of the contrast rather than of aggregation: walk gestures are distributed
approximately uniformly through sessions at roughly 60% prevalence, so there is no temporal
concentration for aggregation to exploit. An episodic deviation — which is what a compulsive
scrolling session would be — would have the temporal structure this contrast lacks. **We therefore
report this as a null about the proxy, not about aggregation**, and note that the deployed system
aggregates regardless because the per-gesture rates leave no alternative.

### 5.8 Model selection

For completeness, detector and model choices were made empirically rather than assumed. GMM-2
improves on single-Gaussian Mahalanobis at matched sensitivity (0.746 vs 0.810 on HMOG; 0.328 vs
0.455 and 0.364 vs 0.633 on the two synthetic conditions), consistent with users occupying more than
one behavioural mode. PCA reconstruction error outperforms Mahalanobis, one-class SVM and isolation
forest on all three conditions, and a component sweep (k = 2…25) shows performance flat above k = 5,
so k = 8 at 85% cumulative variance is robust to ±4 components (Figure 9). Feature selection by SHAP
rank does not help: the full set wins by 0.005 over the top ten, and selection degrades monotonically
(Figure 12). On the supervised side, logistic regression (PR-AUC 0.600) is statistically
indistinguishable from XGBoost (0.628) at half the variance, and a GRU placed fourth of eight,
losing to a linear model. We report the ladder because negative architecture results are as useful
as positive ones and are rarely published (Figure 7, Table 2).

---

## 5A. What survives deployment

**Promoted to its own section on 2026-09-20.** It was a Results subsection; it is the most
transferable finding in the paper and the only one that constrains work beyond PRECOG.

Every touch-behaviour result cited in §3A was collected by an instrumented research app holding
full `MotionEvent` access. Outside that setting an Android app is delivered `TYPE_VIEW_SCROLLED`
events, not touch points: no pressure, no contact area, no per-sample coordinates, no stroke
geometry. Table 3 gives the mapping. Six timing features survive.

**The reported unit is not the human gesture.** Measured on device: ten deliberate swipes, each
separated by a clear pause, produced 54 scroll events — roughly 5.4 per swipe, because the platform
continues reporting while a fling decelerates. Inter-event timing statistics computed from an
accessibility service are therefore dominated by fling mechanics rather than by how a person paces
their scrolling. We have not seen this stated in the touch-behaviour literature, which works from
`MotionEvent` boundaries where a gesture is unambiguous. Any future work reporting "scroll events"
from this API should either group events into gestures or say plainly which unit it is using.

Scroll displacement is also reported inconsistently, and no single field works across apps:
Instagram exposes real `scrollDeltaY` with a constant `scrollY`; Reddit the inverse, with
`scrollDeltaY` pinned to a `-1` sentinel; X exposes both; **YouTube emits no scroll events at all**
under SurfaceView rendering and is excluded rather than silently degraded. The implementation
resolves in that order and returns *null* when neither field is usable, so a missing measurement is
never laundered into a plausible zero.

The privacy position follows from the same boundary rather than from policy:
`canRetrieveWindowContent="false"` makes screen text unreadable at capture, and the shipped APK
declares **no `INTERNET` permission** (verified against the built artifact, 2026-09-20).
Exfiltration is not forbidden; it is absent.

**What follows from this.** The constraint is not a limitation of our implementation; it is a
property of the platform, and it applies to any deployment of this literature outside a research
instrument. Three consequences are worth stating plainly. First, results obtained with the full
kinematic feature set should be read as **upper bounds** on deployed performance, ours included.
Second, a paper reporting "scroll events" from an accessibility API is reporting a unit that is not
the human gesture, and inter-event timing statistics derived from it are not measurements of user
pacing unless events are first grouped into gestures. Third, the privacy properties that make such a
system acceptable to deploy come from the same boundary that removes the signal: the API is
restricted enough to be safe and, for this purpose, restricted enough to be limiting. That trade is
not resolvable by better engineering, and we think it is the most useful thing we can report to
anyone intending to build in this space.

---

## 6. Discussion

- Personalisation is a design choice with a precondition, not a default virtue. State the
  precondition: the deviation must be person-relative.
- Whether compulsive scrolling *is* person-relative is unknown. This is the honest centre of the
  paper. It is not rhetorical hedging — no public dataset can answer it, and saying so is the
  contribution's boundary.
- Absolute FPRs of 0.54–0.82 mean no detector here works per-gesture. Session-level aggregation is a
  necessity, not a refinement.
- The evidence-and-confidence requirement follows from 5.1, not from product taste: if per-subject
  accuracy ranges 0–66%, a system that reports the same confidence to every user is lying to most of
  them.

---

## 7. Limitations

Write these fully; do not compress. In order of severity:

1. **No ground-truth labels for compulsive use in any dataset.** The claim is scoped around this.
2. **One valid real contrast.** Sit→walk, after two withdrawals. A single contrast is thin and the
   paper should say so before a reviewer does.
3. **Sit→walk is a proxy, and a poor one** — it is population-consistent, which is precisely the
   regime where EXP-008 predicts personalisation fails. The null may be an artifact of the only
   contrast available rather than a general finding.
4. **HMOG is a lab reading task on 2014 devices.** Pressure is constant 1.0, so Touchalytics' third-
   ranked feature is unavailable and cross-dataset comparison must exclude it.
5. **EXP-006 is underpowered** at n = 21 per quartile.
6. **The deployed feature set has never been evaluated, and will not be in this paper.** M4 removed
   from scope 2026-09-20 — see §0. A reviewer may push on this; the answer is that a proxy-task
   accuracy number would be worse than no number, because it would be quoted as if it were the
   real one.
7. **No user study, and no substitute for one.** We report an implemented system and its offline
   evaluation. We make no usability, acceptability or behaviour-change claim, because we ran no
   study that could support one. The deployment observations in §5A come from a single device
   operated by an author: they establish what the platform does, which is a property of Android and
   not of a user population, and they are reported only for that purpose. Where a claim would
   require participants, we state the absence rather than estimate around it.
8. **The deployed features are computed over scroll events, not swipes.** At ~5.4 events per swipe,
   `median_gap` measures intra-fling sampling more than user pacing, and `unbroken_ratio` is
   inflated because nearly every intra-fling gap falls under its 400 ms threshold. Grouping events
   into gestures before feature extraction is the obvious correction and is left as future work;
   it was not applied here because it would invalidate the baselines already collected. **This
   affects the implementation and its description only** — every offline result is computed on
   gesture-level data where the distinction does not arise.

---

## 8. Conclusion

_Drafted 2026-09-20, venue-neutral._

We set out to show that personalised behavioural baselines reduce false positives relative to global
thresholds, and did not find it. What we found instead is more useful to anyone building such a
system: personalisation is a conditional technique, not a default virtue. It pays when a deviation
is meaningful only relative to a person's own normal, and it costs when the deviation moves everyone
in the same direction — a distinction that is invisible in aggregate performance and that explains
our null, our synthetic sign flip, and the awkward result that a single fixed threshold beat both
multivariate models.

Two things follow for practice. First, a system that reports a personalised deviation score should
report how much it trusts that score, because the per-subject spread in our data ran from 0% to
65.9%: some people have no usable behavioural signature at all, and returning the same confidence to
all of them is a misrepresentation. Second, a system intended to ship should be built against what
the deployment platform actually exposes. The touch-kinematic feature family that motivates this
literature is unavailable to an ordinary Android application; six timing features are what remain,
and results obtained with the full set should be read as upper bounds.

We leave open the question the work was originally about. Whether compulsive scrolling is a
person-relative deviation or a population-consistent one determines whether personalisation is the
right tool for it, and no dataset we are aware of can answer that. Answering it requires labelled
naturalistic data that does not yet exist. We have described the measurement, the mechanism, and the
platform constraints that any such study will have to work within.

---

## Open actions before this can be drafted into a template

| # | Action | Blocks |
|---|---|---|
| 1 | **Select the venue** | Template, length, section structure, tone |
| 2 | Build the feature-mapping table (28-set ↔ SPEC §4 ↔ Android 6) | §4.1 |
| 3 | Rename one of the two `passive_ratio` definitions | §4.1, and the app |
| ~~4~~ | ~~Obtain Shin & Dey 2013 and Roffarello & De Russis 2023~~ — **done 2026-09-21, both read in full; §3 written from the papers** | — |
| ~~5~~ | ~~M0 placement~~ — **done: promoted to §5A** | — |
| ~~6~~ | ~~M4 ablation~~ — **removed from scope; no accuracy claimed** | — |

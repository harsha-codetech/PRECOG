# PRECOG — Prior Work Library

**22 papers** in `prior-papers-datasets/` (19 PDF + 3 full-text XML), 39 MB.
Grouped by role. **★ = paper behind a dataset we hold.**

---

## A. Dataset papers — mandatory citations

These define the data PRECOG runs on. Every one must be cited and its limitations stated.

| # | Paper | Venue | Dataset | File |
|---|---|---|---|---|
| 1 ★ | Georgiev, Eberz, Turner, Lovisotto, Martinovic — **FETA: Fair Evaluation of Touch-based Authentication** | arXiv 2201.10606 / 2023 | **FETA** (515 users, 31 d, 1.19 M strokes) | `FETA.pdf` |
| 2 ★ | Sitová, Šeděnka et al. — **HMOG: New Behavioral Biometric Features for Continuous Authentication** | IEEE TIFS 11(5), 2016 | **HMOG** (100 users × 24 sessions) | `HMOG.pdf` |
| 3 ★ | Frank, Biedert, Ma, Martinovic, Song — **Touchalytics** | IEEE TIFS 8(1), 2013 | Touchalytics — the origin of the feature set FETA uses | `Touchalytics.pdf` |
| 4 ★ | Garabato, Casado Diez, Dafonte et al. — **Touch-based Interaction Dataset for User Behavioral Analysis** | Data in Brief 64, 2026 | **AITouch** (45 users, Samsung Tab S4) | `Touch-based interaction dataset...pdf` |
| 5 ★ | Borger, Ghosh et al. — **Capturing sleep–wake cycles by using day-to-day smartphone touchscreen interactions** | npj Digital Medicine, 2019 | Tappigraphy; source of `getresttimesphone.m` | `tappigraphy.pdf` |
| 6 ★ | Ceolini & Ghosh — **Common multi-day rhythms in smartphone behavior** | npj Digital Medicine 6, 2023 | Tappigraphy / CODELAB | `multiday_rhythms.pdf` |
| 7 ★ | Huber & Ghosh — **Large cognitive fluctuations surrounding sleep in daily living** | iScience, 2021 | **The `10.34894/6CIGDY` deposit we hold** | `PMC7918275.xml` |
| 8 ★ | Ceolini et al. — **Temporal clusters of age-related behavioral alterations captured in smartphone touchscreen interactions** | iScience 25, 2022 | Tappigraphy / JID | `PMC9418599.xml` |
| 9 ★ | Ceolini, Ridderinkhof & Ghosh — **Age-related behavioral resilience in smartphone touchscreen interaction dynamics** | PNAS 121(25), 2024 | Tappigraphy / CODELAB | `PMC11194488.xml` |

**Note on #7:** this is the paper whose deposit we actually downloaded. Read it first — it documents
what `CompiledData.mat` contains and why it is hourly-binned.

---

## B. Papers using these datasets — methodological precedent

How others have modelled the same data. Useful for feature choices, baselines, and for showing
PRECOG's framing is genuinely different from authentication.

| # | Paper | Relevance to PRECOG |
|---|---|---|
| 10 | **Relative Attention-based One-Class Adversarial Autoencoder for Continuous Authentication** (arXiv 2210.16819) | Uses **HMOG**. One-class modelling of a single user — structurally the same problem as a personal baseline, different goal. |
| 11 | **Your Identity is Your Behavior — Continuous User Authentication based on ML and Touch Dynamics** (arXiv 2305.09482) | Standard touch-dynamics ML pipeline; useful baseline feature set. |
| 12 | **GANTouch: Attack-Resilient Touch-based Continuous Authentication** (arXiv 2210.01594) | Synthetic touch-data generation — directly relevant to our synthetic generator. |
| 13 | **Hold On and Swipe: Touch-Movement Based Continuous Authentication** (arXiv 2201.08564) | Combines touch + motion, as HMOG supports. |
| 14 | **Continuous User Authentication Using ML and Multi-Finger Mobile Touch Dynamics** (arXiv 2207.13648) | Multi-touch feature engineering. |
| 15 | **Swipe Dynamics as a Means of Authentication: Bayesian Unsupervised Approach** (arXiv 2008.01013) | **Unsupervised** per-user modelling — closest methodological analogue to baseline-deviation without labels. |
| 16 | **Active User Authentication for Smartphones: A Challenge Data Set and Benchmark** (arXiv 1610.07930) | UMDAA-02 — a further dataset option if replication is needed. |
| 17 | **Investigating Gender Bias in Touch Biometrics** (arXiv 2606.11457) | Fairness analysis on touch features — supports the bias check in `SPEC.md` §20. |
| 18 | **Common Evaluation Pitfalls in Touch-Based Authentication Systems** (**ASIA CCS 2022**, pp. 1049–1063, DOI 10.1145/3488932.3517388 — *not* an Oxford ORA report; corrected 2026-09-21) | Companion to FETA. **Read before designing the evaluation** — it is the source of the subject-wise-CV requirement, and it reviews 30 touch-dynamics papers finding every one overlooks at least one pitfall. |
| 19 | **Georgiev — Techniques for Continuous Touch-Based Authentication** (Oxford thesis) | Full methodological background to FETA. |

---

## C. Digital wellbeing and behaviour change

| # | Paper | Relevance |
|---|---|---|
| 20 | **Time2Stop: Adaptive and Explainable Human-AI Loop for Smartphone Overuse Intervention** (CHI 2024, arXiv 2403.05584) | **The dominant prior art.** Must be cited, positioned against, and ideally benchmarked. See blueprint §21 [PA-1]. |
| 21 | **The Effects of Smartphones on Well-Being: Theoretical Integration and Research Agenda** (arXiv 2005.09100) | Framing for the wellbeing claim; keeps language non-diagnostic. |
| 22 | **Forecasting User Attention During Everyday Mobile Interactions** (arXiv 1801.06011) | Attention prediction from device sensors; adjacent problem, useful framing. |

---

## D. Previously "paywalled" — access resolved 2026-09-20

Seven of the nine are freely and legally available. **None of these were replaced with substitutes:**
they are cited because they are the source of the idea, not because they were convenient to reach.
Swapping Nahum-Shani for a different open paper would misattribute the JITAI framework.

| Paper | Venue | Free at | Why needed |
|---|---|---|---|
| Nahum-Shani et al. — JITAIs in Mobile Health | Ann. Behav. Med. 52(6), 2018 | **PubMed 27663578 → PMC** | Defines the JITAI framework |
| Liao, Greenewald, Klasnja, Murphy — Personalized HeartSteps | ACM IMWUT 4(1), 2020 | **arXiv 1909.03539**; PMC8439432 | Contextual-bandit JITAI precedent |
| Meinhardt et al. — **Scrolling in the Deep** | CHI 2025 | **arXiv 2501.11814**; Ulm PDF | Closest recent HCI work on scrolling interventions |
| Wellspent — Self-Regulated Social Media Use RCT | JMIR mHealth 14:e56824, 2026 | **mhealth.jmir.org/2026/1/e56824** (CC-BY); PMC13062480 | Recent intervention RCT |
| Microrandomized Trials for JITAIs | AJPH 113(1), 2023 | **PMC9755932** | Experimental design for Study B |
| Identifying Indicators of Smartphone Addiction | Comput. Hum. Behav., 2019 | PMC6686626 | Verify before citing |
| Reichenbacher et al. — Tappigraphy: in-situ map app use | J. Location Based Services 16(3), 2022 | author copy — request from authors | Further tappigraphy application |

**Both obtained and read in full, 2026-09-21.** PDFs in `references/papers/` as `2493432.2493443.pdf`
and `3571810.pdf`. §3 of the draft is written from the papers themselves, not from abstracts.

**What reading them changed:**
- **Shin & Dey 2013 had labels.** 48 participants, own phones, mean 25.1 days, ground truth from the
  Mobile Phone Problem Usage Scale; AdaBoost, 89.6% accuracy, F = 0.707 on app/session/call/SMS
  counts. So "nobody has labels" is **wrong** — the correct statement is that no *public touch
  dataset* carries such an outcome, and that theirs is one-time self-report and unreleased. The
  draft now says that precisely.
- **Roffarello & De Russis 2023 is more positive than the shorthand.** Pooled Hedges' *g* = 0.47,
  95% CI [0.27, 0.68], 7 studies, 255 participants — a real small-to-medium effect. Their criticism
  is that tools are overwhelmingly self-monitoring and evaluated over a mean of 22.6 days. **The
  draft's Introduction previously said the review "found the evidence thin" — that was a
  mischaracterisation and has been corrected.**

---

**Formerly paywalled — for the record.**

| Paper | Venue | Route |
|---|---|---|
| Shin & Dey — Automatically Detecting Problematic Use of Smartphones | UbiComp 2013, DOI 10.1145/2493432.2493443 | ACM DL via INFLIBNET N-LIST, or email Anind Dey |
| Roffarello & De Russis — Achieving Digital Wellbeing Through Digital Self-Control Tools | ACM TOCHI 30(4):53, 2023 | ACM DL; author copy likely at `elite.polito.it` (Polito e-Lite group) |

Note the TOCHI paper's correct year is **2023**, not 2022, and it is a systematic review *and
meta-analysis* — cite it accordingly.

---

## D2. Recent work to add (2025–2026, all open access)

Added 2026-09-20 to keep the related-work current. **These are additions, not replacements** for the
foundational citations in sections A–C.

| Paper | Venue | Relevance |
|---|---|---|
| Tolosa, Ihianle, Machado, Yahaya, Lotfi — **From Patterns to Deviations** | Electronics 15(4):885, 2026 | **Closest published method — read in full 2026-09-20, assessment below** |
| Diaz, Caillaud, Yacef — **U-BEHAVED** | Sensors 22(21):8255, 2022 | Rolling personalised baselines with **robust dispersion estimates** — the closest analogue to PRECOG's robust-z tier, on step counts |
| Meinhardt et al. — Scrolling in the Deep | CHI 2025 | Contextual moderators of scrolling-intervention effectiveness; 7-day study, 72 participants |
| Mertens et al. — Wellspent RCT | JMIR mHealth 14:e56824, 2026 | Current state of intervention efficacy |

### D3. Novelty assessment against Tolosa et al. 2026

Read in full on 2026-09-20 (MDPI, open access). **PRECOG's novelty survives, but narrowed.**

**What overlaps.** Per-user baselines rather than population norms; unsupervised detection under
label scarcity; explicit framing that the value lies in departures from an individual's own status
quo. Their contribution 1 — "a per-user modelling approach using sliding temporal windows to
construct stable, intra-individual behavioural baselines" — is, at the level of a one-line summary,
what PRECOG also does.

**What does not overlap.**

| | Tolosa et al. 2026 | PRECOG |
|---|---|---|
| Timescale | **Day-scale.** Sustained drift over days-to-weeks | **Within-session.** 20-event windows, seconds to minutes |
| Signal | Physical activity, sleep hygiene, communication diversity | Scroll timing and kinematics — no overlap at all |
| Target | Gradual precursors of depressive/anxious episodes | Episodic within-session behaviour |
| Context handling | Rolling windows over time | Context **cells** (app × time-of-day) with empirical-Bayes shrinkage |
| Data | NetHealth cohort, 500+ students, wearables + phone logs | HMOG/FETA touch data; on-device Android capture |

**Consequence for the claim.** PRECOG can no longer claim "we introduce personalised
baseline-deviation modelling for behavioural monitoring" — that framing is occupied by this paper
and by U-BEHAVED before it. It *can* claim the specific thing: personalised deviation at
**gesture timescale over scroll kinematics**, which neither paper touches.

**The unexpected upside.** Both Tolosa et al. and U-BEHAVED *assume* personalisation helps and do
not test the assumption. PRECOG's EXP-003 null plus EXP-008's mechanism give a direct answer to a
question this literature has left open: **personalisation pays only when the deviation is
person-relative, and is actively worse when the deviation is population-consistent.** That is a
contribution to their line of work, not a concession to it — and it is strengthened, not weakened,
by the fact that PRECOG's own headline hypothesis failed.

**On reference currency generally.** Do *not* purge older references. Frank et al. 2013
(Touchalytics) is the source of the feature set, Sitova et al. 2016 (HMOG) is the primary dataset,
and Shin & Dey 2013 originates the detection line. A paper that cites only recent work reads as
though it does not know its own field. The fix for currency is *adding* 2025–2026 work, which D2
does.

---

## E. Reading order

Before writing any code:

1. **#7** (Huber & Ghosh, iScience 2021) — documents the deposit we actually hold
2. **#18** (Oxford Evaluation Pitfalls) — why subject-wise CV is non-negotiable
3. **#2** (HMOG) — confirm `ScrollEvent.csv` column semantics, currently inferred from data

Before writing the paper:

4. **#20** (Time2Stop) — the prior art the contribution must be positioned against
5. **#15** (Swipe Dynamics, Bayesian) — nearest unsupervised-personalization analogue
6. **#6** (Multi-day rhythms) — temporal modelling on naturalistic data

---

## F. Positioning note

Papers 1–19 are almost entirely **authentication** work. That is exactly the gap the blueprint
identifies: scroll kinematics are a mature field, but only ever used to answer *"who is this?"* —
never *"is this person's behaviour unlike their own normal?"*

PRECOG must cite this literature generously and claim **no novelty in the features themselves**.
The contribution is the application and the deviation-as-risk framing. Overclaiming here is the
fastest route to rejection, since these reviewers know this literature well.

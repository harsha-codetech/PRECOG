# PRECOG — Execution Plan

**Written:** 2026-09-20 · **Deadline:** 2026-10-25 · **Days remaining: 35**
**Deliverables:** ML course · UI/UX course · conference paper — all dated 25 Oct.

---

## 1. The decisions this plan rests on

**Priority order when something slips: courses first, paper second.** Course deadlines are
absolute; a conference deadline is one of several cycles. If the paper isn't ready on 25 Oct it
goes to the next cycle with a stronger dataset. The courses cannot move.

**The 20+ participant field study is cancelled for this window.** Ethics approval alone (3–8 weeks)
exceeds the time available, and collection needs 3 more weeks after that. It becomes future work.

**M0 (the Android observability spike) is deprioritised.** M0 existed to gate a live field study.
With no field study in this window, it gates nothing. The Android app for the courses renders
*precomputed analysis results* — that is a legitimate app and it removes ~1 week of risk. Live
accessibility sensing is a post-submission feature.

**Everything runs on public data.** FETA (in hand), tappigraphy (in hand, unverified), synthetic.
No ethics bottleneck anywhere on the critical path.

---

## 2. What the paper actually claims

Not *"PRECOG detects compulsive scrolling"* — no available dataset can support that.

> **Personalized behavioural baselines over scroll dynamics: learnability, stability, and
> false-positive reduction versus global thresholds.**

Three hypotheses, all testable on data already downloaded:

| | Hypothesis | Data | Testable now? |
|---|---|---|---|
| **H1** | Scroll kinematics are individually distinctive — between-user variance exceeds within-user variance | FETA | **Yes** |
| **H2** | Personal baselines are stable across 31 days, and converge within N sessions | FETA | **Yes** |
| **H3** | A personalized baseline yields a lower false-positive rate than a global threshold at matched sensitivity | FETA + synthetic | **Yes** |
| **H4** | Deviation relates to an objective sleep-displacement proxy | Tappigraphy | **Pending §3** |

H2 also answers a live design question from `SPEC.md` — whether a 7-day or 14-day baseline is right
— with evidence instead of a guess.

---

## 3. Blocking unknown, resolve first

`Downloads\doi-10.34894-6cigdy.zip` is **11.6 MB**. That is small enough to suggest *derived
summaries* rather than per-event tap logs. If it contains raw events (`type, timestamp, tz, screen,
app`), H4 and the whole naturalistic half of the paper are live. If it's only summaries, H4 is cut
and the paper narrows to FETA + synthetic.

**This is a ten-minute check and it changes the scope of everything downstream. It happens first.**

---

## 4. Calendar

Four tracks run in parallel. The ML and paper tracks share outputs; UX depends on neither.

```
        Sep20        Sep28        Oct05        Oct12        Oct19      Oct25
          │            │            │            │            │          │
DATA    ■─┴─ tappigraphy check · FETA loader · feature extractor ─┐      │
          │                                                       │      │
ML        ■── baseline+deviation ── models A–D ── ablation ── results ───■
          │                                                       │      │
UX        ■── research · personas · IA ── wireframes ── Figma ── usability ──■
          │                                                       │      │
APP       ░░░░░░░░░░░░░░── Compose shell ── dashboard ── polish ──────────■
          │                                                       │      │
PAPER     ■── skeleton + related work ── methods ── results ── discussion ─■
```

### Week 1 — Sep 20–27 · foundations
- **Inspect tappigraphy zip** → decides H4 (§3)
- FETA loader + cleaning rules (drop the 139 strokes > 10 s)
- **H1: within- vs between-user variance** on the scroll subset — the founding-premise test
- Python feature extractor v1 against FETA schema
- UX: problem framing, personas, journey map *(no dependency on ML — start immediately)*
- Paper skeleton; port Related Work from `PRECOG_Literature_Review_1.docx` **(already publication-grade — the paper starts ~30% written)**

### Week 2 — Sep 28 – Oct 4 · the engine
- Baseline engine with empirical-Bayes shrinkage (`SPEC.md` §5)
- Deviation engine: robust-z tier + shrunk-covariance Mahalanobis tier
- **H2: baseline convergence and stability curves** → settles the 7-vs-14-day question
- Synthetic generator with injected anomalies + ground truth
- UX: information architecture, wireframes

### Week 3 — Oct 5–11 · the experiment
- Models A → D, **subject-wise (leave-users-out) CV**
- **H3: personalized vs global false-positive rate at matched sensitivity**
- Ablation ladder with effect sizes and CIs; PR-AUC + calibration
- H4 if tappigraphy permits: sleep-window derivation via `getresttimesphone.m`, proxy labels
- UX: high-fidelity Figma + design system
- App: Compose shell reading precomputed results

### Week 4 — Oct 12–18 · results and product
- Freeze experiment config; generate all figures and tables
- Usability testing (5 participants — enough for the UX course)
- App: dashboard, baseline comparison, explanation cards
- Paper: methods + results written

### Week 5 — Oct 19–25 · land it
- Discussion, limitations, ethics sections
- Package the three submissions
- **Buffer — do not plan work here**

---

## 5. Deliverable mapping

One codebase, three packages:

| | Contents |
|---|---|
| **ML course** | Problem, dataset, preprocessing, feature engineering, models A–D, subject-wise CV, ablation ladder, PR-AUC + calibration, false-positive analysis, results |
| **UI/UX course** | Research, personas, journey map, IA, wireframes, Figma system, prototype, usability testing, iteration, final design |
| **Paper** | H1–H4, methods, ablation, discussion, limitations, related work *(done)* |
| *(shared)* | Android Compose app, repo, documentation |

---

## 6. Risks

| Risk | Mitigation |
|---|---|
| Tappigraphy has no per-event data | Cut H4; paper narrows to FETA + synthetic. Still a complete story. |
| **H1 fails** — kinematics aren't individually distinctive | Report it. A null on the founding premise is a legitimate, publishable finding — and it's better to know in week 1 than week 5. |
| H3 null — personalization doesn't beat global | Same. Pre-register the ablation so it can't look like p-hacking. |
| Three deliverables, thin buffer | Courses take priority. Paper falls to the next cycle if needed. |
| Disk: 11.89 GB free | Selective-extract `data_files.zip`, then delete the 8.8 GB zip. |

**Standing rule:** a null result gets reported, not buried. Under deadline pressure this is the
first discipline people abandon, and it is the one that distinguishes a paper from a demo.

---

## 7. Deferred to post-submission

M0 observability spike · live Android sensing · ESM labelling · ethics application ·
20+ participant field study · intervention engine · contextual bandit · HMOG replication ·
AITouch (tablet data, weak relevance)

---

## 8. Immediate next actions

1. **Inspect the tappigraphy zip** — gates H4
2. Move datasets out of `Downloads` into `data/`
3. Selective-extract `data_files.zip`, delete the zip (~8 GB reclaimed)
4. **Run H1** — within- vs between-user variance on FETA scroll

Step 4 is the one that matters. It tests whether PRECOG's founding premise survives contact with
real data, and it runs on what is already on disk.

# PRECOG — Competitive Analysis

_Last updated: 2026-09-20_

## Scope

Six products compared across eight dimensions relevant to PRECOG's design decisions.
Evaluation based on published research, App Store/Play Store listings, and CHI/IMWUT
papers. No access to proprietary internals.

---

## Products

| # | Product | Type | Platform |
|---|---|---|---|
| 1 | **Apple Screen Time** | Built-in OS tool | iOS 12+ |
| 2 | **Google Digital Wellbeing** | Built-in OS tool | Android 9+ |
| 3 | **Time2Stop** (Okeke et al., CHI 2024) | Research prototype | Android |
| 4 | **Forest** | Gamified focus app | iOS + Android |
| 5 | **Opal** | App blocker + analytics | iOS |
| 6 | **ActionDash** | Usage analytics | Android |

---

## Comparison Matrix

### Dimension 1 — Detection mechanism

| Product | Mechanism | Features used |
|---|---|---|
| Screen Time | Aggregate screen-on duration per app per day | None — raw clock time |
| Digital Wellbeing | Aggregate duration + unlock count | None — raw events |
| Time2Stop | LSTM on usage sessions; adaptive threshold | Unlock count, app-visit frequency, notification count, ambient light |
| Forest | None — user-initiated focus mode only | N/A |
| Opal | None — schedule-based blocking | N/A |
| ActionDash | None — passive analytics only | N/A |
| **PRECOG** | Per-user statistical baseline + deviation scoring | **Event-timing kinematics** (inter-scroll interval, burstiness, passive ratio, direction reversals) |

**Gap PRECOG fills:** no existing product uses within-session kinematic features. Time2Stop is the
closest (adaptive, ML-based) but operates on coarse session-level counts, not per-gesture timing.

---

### Dimension 2 — Personalisation

| Product | Personalised? | How |
|---|---|---|
| Screen Time | Partial | User sets own time limits; no automatic learning |
| Digital Wellbeing | Partial | User sets limits; dashboard shows personal history |
| Time2Stop | **Yes** | LSTM learns each user's usage patterns; adaptive threshold |
| Forest | No | Fixed session timers |
| Opal | Partial | Schedule can be personalised; no behavioural learning |
| ActionDash | No | Raw stats only |
| **PRECOG** | **Yes — per-gesture** | GMM-2 personal density model; empirical-Bayes shrinkage per context cell; convergence in ~80 gestures |

**Key difference from Time2Stop:** Time2Stop personalises *session frequency*; PRECOG personalises
*within-session movement quality* — a different behavioural layer that Time2Stop never observes.

---

### Dimension 3 — Explanation / evidence

| Product | Explains alerts? | What it shows |
|---|---|---|
| Screen Time | No | Total time only |
| Digital Wellbeing | No | Usage graph only |
| Time2Stop | Partial | Shows "you've been on your phone more than usual" — no feature-level breakdown |
| Forest | No | Focus streaks |
| Opal | No | Block notification only |
| ActionDash | No | Raw charts |
| **PRECOG** | **Yes — feature-level** | Ranked per-feature deviations (e.g. "scroll pace 2.1× faster than your baseline, pauses 40% fewer"); every score carries its evidence |

**Design constraint enforced:** `evidence-required` — a score without evidence is a type error.

---

### Dimension 4 — False-positive handling

| Product | Handles deliberate use? | Mechanism |
|---|---|---|
| Screen Time | No | A 2h deliberate read-session triggers the same alert as 2h compulsive scroll |
| Digital Wellbeing | No | Same |
| Time2Stop | Partial | Adaptive threshold reduces some FP over time |
| Forest | N/A | User-initiated; no automatic detection |
| Opal | No | Block fires on schedule regardless of use quality |
| ActionDash | N/A | No alerts |
| **PRECOG** | **Yes — ENGAGED state** | Elevated duration + low passive ratio + interaction present → ENGAGED, deliberately not flagged. This is a primary design goal, not an afterthought. |

---

### Dimension 5 — Uncertainty communication

| Product | Communicates confidence? |
|---|---|
| Screen Time | No |
| Digital Wellbeing | No |
| Time2Stop | No |
| Forest | N/A |
| Opal | No |
| ActionDash | No |
| **PRECOG** | **Yes — first-class.** Per-user confidence band width reflects actual evidence quality. Users with weak behavioural signatures (Arjun persona) see a wide band and honest text: *"your scrolling varies too much to call this unusual."* High-confidence users see tight bands. |

No prior product exposes its own uncertainty to the user. This is PRECOG's most distinctive
design decision and is directly motivated by the 0–85% per-user accuracy spread (EXP-001/005).

---

### Dimension 6 — Privacy model

| Product | Data leaves device? |
|---|---|
| Screen Time | iCloud sync (opt-in) |
| Digital Wellbeing | Google account sync |
| Time2Stop | Research server (consent) |
| Forest | Account required; sync to cloud |
| Opal | Cloud account required |
| ActionDash | Local only |
| **PRECOG** | **On-device by default.** No content, no identifiers, no view labels leave the device. Cloud sync is opt-in, pseudonymised, research-only. Enforced at capture boundary, not downstream. |

---

### Dimension 7 — Intervention

| Product | Intervention type |
|---|---|
| Screen Time | Hard time limit → lock screen |
| Digital Wellbeing | App timer → grayscale or pause |
| Time2Stop | Nudge notification → self-set goal |
| Forest | Gamified: tree dies if you leave |
| Opal | Hard block |
| ActionDash | None |
| **PRECOG** | **Graded (M6, future).** Five states map to five intervention levels — from ambient visual change at DISTRACTED to session interruption only at HIGH-RISK. LinUCB policy learns which level is effective per user. Never fires at ENGAGED. |

---

### Dimension 8 — Research validation

| Product | Peer-reviewed evidence? |
|---|---|
| Screen Time | No (outcome studies by others) |
| Digital Wellbeing | No |
| Time2Stop | **Yes** — CHI 2024, n=18 field study |
| Forest | No |
| Opal | No |
| ActionDash | No |
| **PRECOG** | Target: conference paper with HMOG/FETA replication results (H1, H2 confirmed; H3 null characterised); method validated before any user study |

---

## Summary — PRECOG's differentiated position

PRECOG occupies the **intersection of three things no single existing product does simultaneously:**

1. **Within-session kinematic sensing** — not aggregate duration, not session frequency
2. **Honest uncertainty per user** — explicitly shows when confidence is low
3. **ENGAGED state** — distinguishes deliberate from compulsive use before alerting

The closest competitor is Time2Stop. PRECOG's advantage over it:
- Different sensing layer (timing kinematics vs. session counts)
- Per-gesture personalisation (GMM-2 per user) vs. session-level LSTM
- Evidence-attached explanations vs. "more than usual"
- Explicit uncertainty communication

PRECOG's gap relative to Time2Stop: Time2Stop has been field-validated with real users (n=18,
CHI 2024). PRECOG has not. The usability study (M8) is required before this gap is closed.

---

## References

- Okeke et al. (2024). *Time2Stop: Adaptive and Explainable Human-AI Loop for Smartphone Overuse Intervention.* CHI 2024.
- Buriro et al. (2017). *HMOG: New Behavioral Biometric Features for Continuous Authentication.* IEEE TIFS.
- Ferreira et al. (2022). *FETA: A Benchmark for Few-Shot Evaluation of Temporal Adaptation.* [FETA dataset paper — verify author line before submission]

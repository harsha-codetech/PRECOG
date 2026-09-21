# PRECOG — Usability Testing Plan

_Version: 1.0 · Date: 2026-09-20 · Phase: formative (pre-prototype)_

---

## 1. Objectives

1. Determine whether users understand what the tolerance band and confidence level communicate
   **without being told what they mean**.
2. Identify where the four screen states (Learning, Within Range, Unusual, Not Enough Pattern)
   cause confusion or misplaced alarm.
3. Measure whether PRECOG's explanation cards ("scroll pace 2.1× faster than your baseline")
   feel actionable, credible, and non-judgmental.
4. Expose false-positive anxiety — does an UNUSUAL alert feel like an accusation?

---

## 2. Scope

**In scope:** onboarding flow, home dashboard, session detail view, insight card, ENGAGED state,
UNUSUAL/PRONOUNCED alert, the "not enough pattern" honest-uncertainty state.

**Out of scope:** intervention engine (M6 not built), settings, account management.

---

## 3. Participants

**Target:** 5–8 participants for formative testing (Nielsen's heuristic for finding ~85% of
usability issues). Extend to 12–15 for summative/comparative testing.

**Recruitment criteria:**

| Criterion | Requirement |
|---|---|
| Age | 18–35 |
| Smartphone use | Self-reports ≥ 2 h/day on social apps |
| Prior wellbeing app use | Mix — at least 2 who have tried/abandoned a tool |
| Behavioural distinctiveness | Assessed post-study via HMOG proxy; report spread across personas |
| Language | English or Telugu (localisation TBD) |

**Personas targeted:**
- 2–3 Meera-type (consistent, high-distinctiveness)
- 2–3 Arjun-type (variable, low-distinctiveness — the hardest users to serve)
- 1–2 Priya-type (late-night, stress-correlated — high stakes)

---

## 4. Method

**Moderated think-aloud** with concurrent probing.

- Session length: 45–60 minutes
- Setting: participant's own phone (prototype loaded as an HTML file) or researcher's Android device
- Moderator: asks "what do you expect will happen next?" and "what does this tell you?" — never
  explains or corrects mid-task
- Note-taker logs confusion moments, hesitations, and emotional reactions separately

**Remote option:** screen share + voice; participant taps and speaks. Same protocol.

---

## 5. Tasks

Tasks are given as **scenario prompts**, not UI instructions, to avoid leading.

| # | Scenario | What we are measuring |
|---|---|---|
| T1 | "You just installed PRECOG. Walk through what you see and tell me what's happening." | Onboarding comprehension; tolerance band meaning |
| T2 | "It's been two weeks. Open the app after a normal evening scroll. What does this screen tell you?" | Within-range state comprehension; confidence band width |
| T3 | "You spent 90 minutes reading a long article. Open PRECOG. What do you see, and does it feel right?" | ENGAGED state — does it correctly not alarm? |
| T4 | "You had a bad night — scrolled Instagram for 2 hours in a loop. Open the app. What would you want to see? Now look at what PRECOG actually shows." | UNUSUAL/PRONOUNCED state; does it feel like accusation or information? |
| T5 | "PRECOG shows 'not enough pattern yet.' What does that mean to you? Is it reassuring or frustrating?" | Honest-uncertainty state — Arjun persona |
| T6 | "Tap on 'scroll pace faster than usual.' What does this tell you? Do you believe it? What would you do?" | Insight card; evidence credibility and actionability |

---

## 6. Metrics

### Task-level (per task)
- **Task completion** — did the participant correctly interpret the screen state? (Binary: yes/no)
- **Time on task** — seconds from scenario read to first confident statement
- **Error count** — number of misinterpretations requiring recovery

### Study-level
- **SUS (System Usability Scale)** — 10-item questionnaire after all tasks; score ≥ 70 is the
  target for a health-adjacent app (Bangor et al. 2008)
- **Comprehension rate** — % of participants who correctly interpret each state without prompting
- **False-alarm anxiety score** — 3-item Likert: "this feels like an accusation," "I would
  dismiss this immediately," "this makes me want to use the app less"

### Qualitative
- Open-ended: "Is there anything this app told you that felt wrong or unfair?"
- Sentence completion: "The most useful thing PRECOG showed me was ___."

---

## 7. Acceptance criteria

The prototype passes formative testing and is ready for Figma hi-fi if:

| Criterion | Threshold |
|---|---|
| T1 tolerance-band comprehension | ≥ 4/5 participants understand without prompting |
| T3 ENGAGED state — not alarmed | ≥ 4/5 participants correctly say "this looks fine" |
| T5 honest-uncertainty — not frustrated | ≥ 3/5 find it reassuring or neutral (not frustrating) |
| SUS score | ≥ 70 |
| False-alarm anxiety ("feels like accusation") | ≤ 2/5 agree |

If T3 fails (ENGAGED is confusing), revisit the label before hi-fi.
If T5 fails (honest uncertainty is frustrating), redesign that state with more forward-looking text.

---

## 8. Ethical requirements

- Written informed consent before any session recording
- Participants may stop at any time
- No real scrolling data collected — prototype only
- Debrief: explain PRECOG's actual sensing limitations (AccessibilityService timing only, no content)
- Data: session notes anonymised; recordings deleted after analysis; no participant identified in report
- IRB/ethics board approval required before any study involving real behavioural data (M8)

---

## 9. Timeline

| Step | When | Owner |
|---|---|---|
| Prototype ready (HTML clickable) | 2026-09-22 | Sri Harsha |
| Recruit 5 participants | 2026-09-25 | Sri Harsha |
| Pilot session (1 participant) | 2026-09-26 | Sri Harsha |
| Main sessions (4–7 participants) | 2026-09-27 to 2026-10-04 | Sri Harsha |
| Analysis + report | 2026-10-07 | Sri Harsha |
| Findings fed into hi-fi Figma | 2026-10-10 | Sri Harsha |
| Course submission | **2026-10-25** | Sri Harsha |

---

## 10. Analysis plan

1. Affinity diagram — cluster confusion moments by screen state
2. Task completion matrix — all tasks × all participants, mark pass/fail
3. SUS scoring — per participant, then aggregate
4. Theme extraction from think-aloud transcripts: comprehension, trust, emotional tone, actionability
5. Map failures to specific UI elements and propose remediation before hi-fi

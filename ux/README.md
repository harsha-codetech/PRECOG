# PRECOG — UX Track

UI/UX course deliverable. One design problem runs through everything here:

> **How do you report a measurement about someone's behaviour without either alarming them or
> pretending to more certainty than you have?**

## Design direction

**Subject vernacular.** PRECOG computes deviation from a personal distribution. Its natural visual
language is statistical process control — corridors, medians, σ — not dashboards or progress rings.

**Direction: technical drawing.** PRECOG measures deviation from a tolerance — which is engineering
drawing's native subject. Dimension lines, tick marks, tolerance bands and leader-line callouts are
borrowed as a system, not as decoration.

**Signature: the tolerance band.** A dimensioned corridor of *this person's* normal, with the
current session marked against it. It is literally what the engine computes, it scales from hero to
sparkline, and no wellbeing app looks like one.

**Confidence is drawn, not labelled.** EXP-001 found per-user distinctiveness ranging from 0% to
66% — roughly a quarter of people have no stable scroll signature. Drafting already has a convention
for this: **a solid edge is a defined limit, a dashed edge is approximate.** So an uncertain
baseline is drawn wider and dashed, exactly as an engineer would draw it. Uncertainty lives in the
same object as the measurement rather than in a percentage badge.

**Palette.** Cool drafting paper (`#F5F6F8`) rather than warm cream, with one confident ink blue
(`#1F3B73`) doing the work of an accent. Status colours are deep and desaturated so red stays
meaningful. Full dark counterpart for every token. Deliberately *not* the neon-cyberpunk treatment
of `docs/source/PRECOG_pfp.png`, which contradicts the anti-surveillance positioning.

**Type.** Two families split strictly by job: **Instrument Sans** carries every word, **Spline Sans
Mono** carries every number. Figures are tabular throughout, so a value that updates live never
nudges the layout beside it. No serif display anywhere.

**Themes.** Light and dark are both first-class, with a working toggle that persists. The pane also
follows the system preference when no choice has been made.

Full system: [`design-system/precog-design-system.html`](design-system/precog-design-system.html)

## Information architecture

```
Onboarding ──► Learning mode ──► Overview ──► Session detail
   │                                 │              │
   │                                 ├─► Trends     └─► Evidence
   │                                 ├─► Insights
   └─────────────────────────────────┴─► Settings & data
```

Five destinations, flat. Everything else is a detail view reached from Overview. The hierarchy
matches the pipeline — observe, learn, compare, explain — so the app's structure teaches its logic.

## Screen states

| State | When | What it must not do |
|---|---|---|
| **Learning** | First ~14 days, or after a long gap | Flag anything. Compare to other people. |
| **Within range** | Deviation inside the corridor | Congratulate. There is no target to hit. |
| **Unusual** | Deviation outside, evidence available | Diagnose, warn, or moralise |
| **Not enough pattern** | Per-user distinctiveness too low | Fake a score to look competent |

The fourth state is the one this project earned the hard way, and it is the most important screen in
the app.

## Voice

PRECOG reports a measurement. Every sentence must be something a number supports.

- *"This session is unlike your usual evenings"* — not *"You're addicted to scrolling"*
- *"Your scrolling varies too much to call this unusual"* — not *"Confidence: 41%"*
- *"Today sits inside your usual range"* — not *"Great job today!"*

## Non-negotiable rules

1. **evidence-required** — no deviation without the features that produced it
2. **confidence-is-geometry** — uncertainty widens the band, never a percentage
3. **silence-while-learning** — nothing flagged before the baseline holds
4. **red-is-rare** — rust for sustained pronounced deviation only
5. **own-units** — every comparison is to this person's history, never an average or a limit
6. **dismissible** — repeated dismissal reduces frequency

## Contents

| Path | Deliverable |
|---|---|
| `research/` | Competitive analysis, problem framing |
| `personas/personas.md` | Three personas, drawn from the data |
| `journeys/journey-map.md` | End-to-end journey with emotional states |
| `wireframes/` | Low-fidelity structure |
| `design-system/` | Tokens, type, components, voice — **built** |
| `usability/` | Test protocol and findings |

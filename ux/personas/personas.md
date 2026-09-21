# Personas

Three personas, each grounded in something the data actually showed rather than invented to fill a
template. The distinctiveness figures come from EXP-001, where per-subject identification accuracy
ranged from 0% to 65.9%.

---

## 1 — Meera · the consistent scroller

*22, final-year student. High behavioural distinctiveness (top quartile, ~50%+ identifiable).*

Scrolls in a recognisable way: similar pace, similar pauses, mostly the same two apps, mostly
evenings. Her baseline converges fast — **around 80 gestures, roughly two sessions** (EXP-002).

**Goal.** Notice when a late-night session is running away from her, before 1am rather than after.

**Frustration.** Screen Time tells her she used Instagram for 2h 14m. She already knew that. It
says nothing about whether that was a normal Tuesday or a bad one.

**What PRECOG owes her.** A tight, confident band and a specific sentence — *"longer than usual,
with fewer pauses."* She is the user the system works best for, and the one most likely to be
over-served with notifications if frequency isn't capped.

---

## 2 — Arjun · the variable scroller

*24, junior developer. Low behavioural distinctiveness (bottom quartile, near 0% identifiable).*

His scrolling has no stable signature. Commutes some days, works from home others; sits, walks,
scrolls one-handed on a train. His baseline stays wide no matter how much data accumulates.

**Goal.** The same as Meera's. He just cannot be served the same way.

**Frustration.** He has abandoned three wellbeing apps for crying wolf. One more false alarm and
PRECOG is uninstalled.

**What PRECOG owes him.** *Honesty.* A wide, hazy band and the plain sentence — *"your scrolling
varies too much to call this unusual."* He should see a system that declines to guess, not one that
produces a confident-looking number it cannot support.

> Arjun is the reason the **"not enough pattern"** state exists. EXP-001 showed users like him are
> not rare and not a defect — they are roughly a quarter of the population. An interface that
> reports a crisp deviation score for him is lying.

---

## 3 — Dr. Sowmya · the reviewer

*Faculty, evaluating this as a research artifact.*

**Goal.** Establish whether the claims are supported and the interface overstates them.

**What she checks.** Does a score ever appear without evidence? Does the language creep toward
diagnosis? Does the UI acknowledge uncertainty, or bury it? Is anything described as detected that
was only measured?

**What PRECOG owes her.** Every number traceable to a feature, every state defined operationally,
and no word anywhere that implies a clinical claim.

---

## Design consequences

| From | Consequence |
|---|---|
| Meera's fast convergence | Learning mode can end early for consistent users — gate on **baseline stability, not elapsed days** |
| Arjun's wide band | "Not enough pattern" is a first-class state, not an error |
| Both | Confidence must be per-user and visible, because the population genuinely splits |
| Sowmya | Evidence attached to every score; behavioural language only |

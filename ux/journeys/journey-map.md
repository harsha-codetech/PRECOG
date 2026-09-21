# Journey Map

Meera's path from install to sustained use. Arjun's divergence is marked where it matters.

```
INSTALL ──► CONSENT ──► LEARNING ──► FIRST READING ──► DEVIATION ──► RESPONSE ──► ADAPT
  d0          d0         d1-14          d~3             d~18          d~18        ongoing
```

---

### 1 · Install — *skeptical*

**Doing.** Downloading a fourth wellbeing app, expecting the same thing.
**Thinking.** *"This will just tell me a number I already know."*
**Risk.** Abandonment before consent.
**Design response.** The opening line is a claim, not a feature list: **"Measure the person, not
the minutes."** Say the one true differentiating thing immediately.

### 2 · Consent — *wary*

**Doing.** Reading what an accessibility service can see. This is the highest-anxiety moment in the
entire journey and the easiest to lose someone at.
**Thinking.** *"So it can read my screen?"*
**Design response.** State the limit before asking for the permission: *PRECOG records when and how
you scroll. Not what you read.* Show the actual fields collected. Offer delete-everything up front,
not buried in settings.
**Measure.** Consent-screen drop-off.

### 3 · Learning — *patient, then restless*

**Doing.** Using the phone normally. The app says almost nothing for two weeks.
**Thinking.** Day 3: *"is this working?"* Day 10: *"why hasn't it told me anything?"*
**Risk.** Silence reads as broken. This is the longest stretch with no payoff.
**Design response.** Progress is visible without being a reward — which features have firmed up, day
count, and an explicit reason for the silence: *"PRECOG will not flag anything yet. Comparing you to
other people would be the wrong measurement."* The restraint *is* the pitch.
**From EXP-002.** Baselines converge at ~80 gestures ≈ 2 sessions, far sooner than 14 days. **Gate on
stability, not the calendar** — end learning mode when the band tightens, and let fast users out in
days.

### 4 · First reading — *curious*

**Doing.** Seeing her own range for the first time: *usually 1h 20m – 2h 10m.*
**Thinking.** *"That's… actually about right."*
**Why it matters.** This is the moment the product earns trust. Recognition of her own pattern is
what makes a later deviation credible.
**Design response.** Lead with the range, not the score. Nothing is flagged.

> **Arjun diverges here.** His band arrives wide and hazy with *"your scrolling varies too much to
> call this unusual."* This must land as **candour, not failure** — the copy explains that people
> differ and his pattern is simply less regular. Handled badly, he churns.

### 5 · Deviation — *caught out*

**Doing.** 11:58pm, 48 minutes continuous, against a 19-minute usual.
**Thinking.** *"…yeah. I noticed."*
**Risk.** Defensiveness. Any hint of judgement converts reflection into dismissal.
**Design response.** Measurement plus evidence, no verdict: *"This session is unlike your usual
evenings"*, with length +2.4σ and pauses −1.9σ shown beneath. Never *"warning"*, never *"risk"*.
**Measure.** Dismissal rate, and whether the session ends within 10 minutes.

### 6 · Response — *in control*

**Doing.** Dismissing, or stopping.
**Design response.** Dismissal costs nothing and is never asked about twice in the same session.
Repeated dismissal *reduces* frequency — the system learns it is being unhelpful. An intervention
that nags has already failed.

### 7 · Adaptation — *settled*

**Doing.** Term ends, her routine changes, her baseline follows.
**Risk.** The opposite failure — the baseline quietly absorbs a genuine escalation and stops
flagging anything.
**Design response.** Slow EWMA adaptation (α = 0.05), and **anomalous sessions are excluded from
baseline updates** so a bad fortnight cannot redefine normal (`SPEC.md` §5). Sustained shifts are
surfaced as a change, not silently absorbed.

---

## Where this journey is won or lost

| Moment | Failure mode | Guard |
|---|---|---|
| **Consent** | Reads as surveillance | State the limit before requesting the permission |
| **Learning** | Silence reads as broken | Visible progress + stated reason; exit on stability, not days |
| **First reading** | Range feels wrong | Lead with range, flag nothing, let recognition build trust |
| **Low confidence** | Honesty reads as failure | Frame as a property of the person, never a defect |
| **Deviation** | Judgement triggers dismissal | Measurement + evidence, no verdict |
| **Adaptation** | Baseline absorbs escalation | Contamination guard; surface sustained shifts |

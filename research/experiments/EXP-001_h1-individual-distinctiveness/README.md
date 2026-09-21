# EXP-001 — H1: individual distinctiveness of scroll kinematics

```
Date:        2026-09-20
Hypothesis:  H1 — between-user variance in gesture features exceeds within-user variance;
             a gesture sits closer to its own user's behavioural centroid than to others'.
Dataset:     hmog_gesture-features_features-v0.1  (39,556 gestures · 99 subjects · 29 features)
Split:       contiguous — first 4 reading sessions enrol, later sessions test (FETA pitfall P3)
Versions:    features-v0.1
Seed:        42
```

## Verdict

**H1 is supported, but distinctiveness is moderate — not the strong personal signature the
authentication literature might lead you to expect.**

## Result

### 1. Variance decomposition (ICC — share of variance that is between-user)

| Feature | ICC |
|---|---|
| phone_orientation | 0.824 |
| start_x | 0.577 |
| stop_x | 0.546 |
| trajectory_length | 0.358 |
| end_to_end_distance | 0.336 |
| stop_y / start_y | 0.336 / 0.327 |
| mid_stroke_area | 0.302 |
| duration_ms | 0.299 |

**Median ICC 0.161.** Only 3 of 29 features exceed 0.50; 8 exceed 0.30; 19 exceed 0.10.

Most features carry *some* individual signal, but most of each feature's variance is
within-person. The strongest univariate signals are **positional** (`start_x`, `stop_x` — where on
the screen a person touches) rather than kinematic (how they move).

### 2. Centroid distance (evaluation sessions)

```
gestures closer to own centroid than to mean-other : 88.5%   (chance 50%)
separability AUC                                   : 0.787   (chance 0.500)
```

### 3. Single-gesture identification, 99 subjects

```
top-1 : 15.0%   (chance 1.0%  — 14.8x)
top-5 : 37.0%   (chance 5.1%)
median rank of true user : 10 of 99
```

### 4. Sensitivity — where does the signal actually live?

| Feature set | n | top-1 | AUC | closer-to-own |
|---|---|---|---|---|
| A — all | 27 | 15.0% | 0.787 | 88.5% |
| B — minus `phone_orientation` | 26 | **15.2%** | 0.788 | 87.5% |
| C — kinematics only (no position, no orientation) | 22 | **9.8%** | 0.741 | 82.6% |

## Observations

**`phone_orientation` is a red herring.** It has the highest univariate ICC (0.824) yet removing it
*improves* identification slightly — it is redundant with other features and contributes nothing in
combination. The confound worry was unfounded, but the lesson generalises: **rank features by
multivariate contribution, not by ICC.**

**Positional features carry real signal.** Dropping `start_x/y`, `stop_x/y` costs 5.4 points of
top-1 accuracy (15.2% → 9.8%). Where a person touches the screen is genuinely individual — grip,
hand size, thumb reach. This is legitimate behaviour, not an artifact, but it is *not* scroll
kinematics and should be reported separately.

**Kinematics alone still clear chance decisively** — 9.8% top-1 against 1.0% chance, AUC 0.741.
H1 survives on the kinematic substrate by itself, which is what PRECOG's claim requires.

**The most consequential finding is the spread between people:**

```
per-subject identification accuracy:  median 9.8%   worst 0.0%   best 65.9%
```

**Some people have a strongly distinctive scroll signature; others have none at all.** This is not
noise — it is a real property of the population, and it has direct product consequences:

- A personal baseline will be informative for some users and near-useless for others.
- `SPEC.md` §7's confidence measure must capture *per-user distinctiveness*, not only sample count.
  For a low-distinctiveness user, PRECOG should say so rather than emit a confident deviation score.
- Any aggregate performance number will hide this spread. **Report the per-user distribution, not
  just the mean.**

## Caveats

- Reading task in a lab, 2014 devices, ~11 minute sessions. Not free browsing.
- Pressure unavailable in HMOG (constant 1.0) — Touchalytics' 3rd-ranked feature is missing, so
  these numbers likely *understate* what is achievable on modern hardware.
- Nearest-centroid is a deliberately simple probe. A trained per-user model would score higher;
  the point here is distinctiveness, not building an authenticator.
- Sit vs walk posture is mixed within reading sessions and not yet controlled.

## Next

1. **EXP-002 (H2)** — baseline stability and convergence: how many gestures before a personal
   baseline stops moving? Settles the 7-vs-14-day question in `SPEC.md`.
2. Stratify by per-user distinctiveness — does the personalization benefit concentrate in the
   distinctive users?
3. Control for posture (sit/walk) as a covariate.
4. Replicate on FETA once the raw download lands, on the shared feature set (excluding pressure).

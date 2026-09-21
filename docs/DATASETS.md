# PRECOG — Dataset Inventory & Structural Analysis

**Verified:** 2026-09-20 (all figures below measured from the files on disk, not from papers)
**Location:** `C:\Users\Admin\Desktop\PRECOG\data` · **12.56 GB** total

---

## 1. What we have

| Dataset | Users | Granularity | Timestamps | Kinematics | Naturalistic | Licence | Status |
|---|---|---|---|---|---|---|---|
| **HMOG** | 100 × 24 sessions | per event | **✓ epoch ms** | **✓** | ✗ task | ToU, non-commercial | **Best source** |
| **FETA** | 470 (90 @ 31 d) | per stroke | ✗ | ✓ | ✗ task | ODC-PDDL | Good |
| **Tappigraphy** | 189 (147 ≥ 30 d) | hourly bins | ✓ coarse | ✗ | **✓ real life** | Open | Useful, limited |
| **AITouch** | 45 | per event | ✓ | ✓ | ✗ tablet game | CC BY-NC 4.0 | Low value |

---

## 2. HMOG — the strongest source

`data/public_dataset/` · 100 per-user zips · 5.73 GB

Each user has 24 sessions; each session directory contains:

```
Accelerometer.csv  Gyroscope.csv  Magnetometer.csv   ← inertial
ScrollEvent.csv    StrokeEvent.csv  TouchEvent.csv   ← interaction
Activity.csv       Reading1-3answer                  ← task/context
KeyPressEvent.csv  PinchEvent.csv
```

### 2.1 Official schema

**Verified against `public_dataset/data_description.pdf`, shipped with the dataset.** These are the
documented column names — not inferred.

**`ScrollEvent.csv`** (18 cols, no header):

| # | Column | Meaning |
|---|---|---|
| 1 | `Systime` | **absolute timestamp (epoch ms)** |
| 2 | `BeginTime` | relative scroll begin |
| 3 | `CurrentTime` | relative current |
| 4 | `ActivityID` | links to `Activity.csv` |
| 5 | `ScrollID` | **scroll gesture id, from 0** |
| 6 | `Start_action_type` | 0 = DOWN |
| 7–10 | `Start_X`, `Start_Y`, `Start_pressure`, `Start_size` | gesture start |
| 11 | `Current_action_type` | 2 = MOVE |
| 12–15 | `Current_X`, `Current_Y`, `Current_pressure`, `Current_size` | current sample |
| 16–17 | `Distance_X`, `Distance_Y` | **displacement since last `onScroll`** |
| 18 | `Phone_orientation` | 0 portrait · 1 / 3 rotated |

**Each row is a MOVE sample, not a scroll.** Rows group by `ScrollID` into gestures — in one
session, 5,134 rows → **189 scroll gestures**, median 24 samples each.

**`StrokeEvent.csv`** adds `Speed_X` / `Speed_Y` — **fling velocity in pixels per second**, measured
directly rather than derived.

**`Activity.csv`**: `ID, SubjectID, Session_number, Start_time, End_time, Relative_Start,
Relative_End, Gesture_scenario, TaskID, ContentID`.
`Gesture_scenario` 1 = Sit, 2 = Walk. `TaskID` encodes task × posture:

| TaskID | Task |
|---|---|
| **1, 7, 13, 19** | **Reading + Sitting** |
| **2, 8, 14, 20** | **Reading + Walking** |
| 3, 9, 15, 21 | Writing + Sitting |
| 4, 10, 16, 22 | Writing + Walking |
| 5, 11, 17, 23 | Map + Sitting |
| 6, 12, 18, 24 | Map + Walking |

### 2.2 Why this is the primary source

**Timing is confirmed working.** Derived from `Systime` grouped by `ScrollID` on one real session:

```
inter-scroll gap : median 1258 ms   (p25 852, p75 2582)
scroll duration  : median  401 ms
```

That gap distribution *is* PRECOG's dwell/pause/burstiness substrate. FETA cannot produce it (§3).

**Reading sessions are the usable slice** — 8 of each user's 24 sessions (TaskID 1, 2, 7, 8, 13, 14,
19, 20) are scrolling through articles, the closest available analogue to feed scrolling.
That is **100 users × 8 sessions**, with sitting-vs-walking as a controllable confound.

Collected 2014.

### 2.3 Known limitation: pressure is unusable

**`Pressure` is a constant `1.0` in every HMOG file, for every subject.** The 2014 Samsung devices
did not report touch pressure, and Android returns `1.0` when the sensor is unsupported.

This matters more than it looks. Touchalytics ranks **mid-stroke pressure as its 3rd most
discriminative feature (17.3% mutual information with user identity)** — and HMOG cannot supply it,
while FETA can (real values from iPhone). **Any cross-dataset comparison must exclude pressure**, or
FETA will appear to outperform HMOG for reasons that have nothing to do with the method.

`Contact_size` does vary (18 distinct values, quantised) and remains usable.

### 2.4 Extracted output

`scripts/extract_hmog.py` → `data/interim/hmog/` — **5.73 GB reduced to 81 MB**, 39 seconds.

| File | Rows |
|---|---|
| `sessions.parquet` | 13,410 activities (the manifest) |
| `hmog_scroll-events_v1.parquet` | 1,428,399 MOVE samples |
| **`hmog_scroll-gestures_v1.parquet`** | **40,659 scroll gestures** |
| `hmog_stroke-events_v1.parquet` | 23,235 strokes |
| `hmog_touch-events_v1.parquet` | 2,018,246 touch events |

Reading sessions only, 99 subjects (one has no scroll data in its reading sessions), 4,273
activities, 7–8 sessions each.

| Gestures per subject | Subjects |
|---|---|
| ≥ 100 | 98 |
| ≥ 200 | 91 |
| ≥ 300 | 60 |

Median 345 per subject (min 92, max 1,402). Verified characteristics:

```
inter-scroll gap : median 1580 ms  (p25 687, p75 5026)
gesture duration : median  483 ms
samples/gesture  : median   21
dy_sum           : median  175 px   ← strongly vertical, as reading should be
dx_sum           : median  -16 px
```

---

## 3. FETA

`data/feta/` · 0.73 GB · [ORA](https://ora.ox.ac.uk/objects/uuid:5f1abaa7-52a4-430b-9208-128d9f1832fd) · **ODC-PDDL (public domain)**

- `features.csv` — **1,166,092 strokes**, 33 columns; scroll subset **421,973 strokes / 470 users / 6,009 sessions**
- `tables/` — `userdata.csv` (486 users + demographics), `measurements.csv` (6,017 dated sessions), `gamedata.csv` (65,585 iterations)
- Cohort: **138 users ≥ 20 sessions, 90 users ≥ 30 sessions** across 31 days
- Quality: zero nulls; 139 strokes (0.03%) with `duration` > 10 s need cleaning

Has velocity/acceleration percentiles, pressure, trajectory, straightness.
**Has no timestamp column** → no inter-stroke timing. The 8.6 GB `data_files.zip` that would have
supplied it is **no longer on disk**. This matters much less now that HMOG covers timing.

Task: goal-directed search through a 20-item social-media-style feed. No stopping decision,
no labels; session duration and frequency are protocol artifacts and must not be used as features.

---

## 4. Tappigraphy (Leiden CODELAB)

`data/doi-10.34894-6cigdy/` · 12 MB · DOI `10.34894/6CIGDY` · Feb 2018 – Aug 2019

`DataScripts.7z` → `CompiledData.mat` + 3 MATLAB scripts + README.

**It is hourly-binned aggregates, not per-event tap logs.** Per respondent (235 cells,
**189 with usable series**):

| Field | Shape | Contents |
|---|---|---|
| `ID` | — | subject identifier |
| `Usage` | (N, 3) | UTC ms · **interactions per hour** · **unique apps per hour** |
| `speed` | (N, 2) | UTC ms · **25th-pct inter-touch interval (ms)** |
| `unlock` | (N, 2) | UTC ms · 25th-pct inter-touch interval at unlock |
| `findt` | (N, 2) | UTC ms · 25th-pct inter-touch interval at icon-finding |
| `watchraw*` | — | accelerometer / lux, only for participants who wore a watch |

Coverage: span **median 47 days**, p75 88, max 1,831. **147 users ≥ 30 days**, 45 ≥ 90 days,
16 ≥ 180. Median 1,136 hourly bins per user.

**Consequence for H4:** per-*session* sleep-displacement labels are **not** derivable — there are no
sessions and no per-event timestamps, so `getresttimesphone.m` cannot be run. But hourly interaction
counts still give a usable **per-user circadian profile and rest window** (long gaps = sleep), so a
*coarse, hourly* night-usage measure remains possible. H4 survives in weakened form only.

Its real value: the only **naturalistic, long-duration, per-user** behavioural series available —
the one place personalization can be tested on real life rather than a lab task.

---

## 5. AITouch

`data/AITouch - Data/` · 0.34 GB · CC BY-NC 4.0 · DOI `10.17632/9v7bxv3dcc.2`

`features/` holds four CSVs, one per game scene (`country`, `fruit`, `gearmatching`, `puzzle`);
`raw_data/data.json` is a single JSON of raw events. 45 users, **Samsung Tab S4 — a tablet.**

Tablet scroll kinematics do not transfer cleanly to phones. **Lowest priority; probably unused.**

---

## 6. Problems found

| Issue | Cost | Action |
|---|---|---|
| **HMOG duplicated** — `public_dataset/` and `hmog_dataset/public_dataset/` both 5.73 GB, identical file lists | **5.73 GB** | Verify byte-identical, then delete one |
| `data/hmog/`, `data/touch2025/` empty leftovers | 0 | Remove |
| `feta/features.zip` (201 MB) + `tables.zip` already extracted | ~206 MB | Delete archives |
| FETA `data_files.zip` gone | — | No longer needed; HMOG supplies timing |

Reclaimable: **~5.9 GB** without losing anything.

---

## 7. Feature coverage

| PRECOG feature family | HMOG | FETA | Tappigraphy |
|---|---|---|---|
| Scroll velocity / acceleration | **✓** | ✓ | ✗ |
| Pressure / contact area | **✓** | ✓ | ✗ |
| Inter-scroll interval | **✓** | ✗ | ~ hourly |
| Burstiness | **✓** | ✗ | ~ hourly |
| Dwell / pause frequency | **✓** | ✗ | ~ hourly |
| Direction reversals | **✓** | ✓ | ✗ |
| Session structure | **✓** | ✗ | ✗ |
| Sessions/day, inter-session | ✗ | ✗ | ~ |
| Time-of-day / circadian | ✗ | ✗ | **✓** |
| App context | ✗ | ✗ | **✓** (count only) |
| Active/passive ratio | **✓** | ✗ | ~ |
| Real stopping decision | ✗ | ✗ | **✓** |
| Wellbeing label | ✗ | ✗ | coarse proxy only |

**HMOG covers the most, FETA adds scale and a public-domain licence, tappigraphy is the only
naturalistic source. None has a true label.**

---

## 8. Pending

**Blocking:**
1. Confirm the two HMOG copies are byte-identical, delete one (**5.73 GB**)
2. Selective-extract HMOG: `ScrollEvent` / `TouchEvent` / `StrokeEvent` only, skipping the inertial
   CSVs that are ~93% of the volume. 100 users × 24 sessions ≈ **~3 GB** extracted.
3. Confirm `ScrollEvent.csv` column semantics against the HMOG paper — the schema in §2 is inferred
   from data, not documented.

**Then:**
4. HMOG loader + feature extractor
5. **H1** — within- vs between-user variance (now runnable on HMOG *and* FETA, i.e. replicated
   across two datasets, which is much stronger than one)
6. Tappigraphy loader (`scipy.io`, cell array of structs)
7. Revised H4 scope: hourly circadian deviation, not per-session sleep displacement

**Dropped:** FETA raw timing (gone, superseded by HMOG) · AITouch (tablet).

---

## 9. Net assessment

**The data is good — better than the plan assumed.** HMOG arriving with event-level timestamps
*and* kinematics removes the single biggest gap in the FETA-only plan and makes the full PRECOG
feature set computable from real human data.

Two datasets (HMOG + FETA) now support **cross-dataset replication** of the personalization result,
which materially strengthens the paper against the "single dataset, does it generalize?" objection.

The loss is H4: tappigraphy is hourly aggregates, so the objective sleep-displacement *session*
label is not available. Labels remain the project's unsolved problem, exactly as the blueprint
predicted.

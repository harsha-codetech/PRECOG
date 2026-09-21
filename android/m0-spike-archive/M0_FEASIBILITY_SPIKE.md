# M0 — AccessibilityService Feasibility Spike

**Status:** Code written — awaiting device test  
**Decision gate:** GO / NO-GO for the entire Android route

---

## What this spike answers

Can an Android `AccessibilityService` observe the timing kinematics needed to
replicate the PRECOG feature set on Instagram, YouTube, TikTok, Reddit, and X?

Specifically, are `TYPE_VIEW_SCROLLED` events fired with non-null/non-zero values
for `scrollDeltaX`, `scrollDeltaY`, and the index fields that let us compute
inter-scroll interval and burstiness?

---

## How to run

### 1. Build and install

```bash
cd android
./gradlew installDebug
```

Or open in Android Studio and run on a physical device (emulator may not fire
AccessibilityEvents from third-party apps reliably).

### 2. Enable the service

Open **PRECOG M0** on device → tap "Open Accessibility Settings" → enable
"PRECOG Event Logger".

### 3. Generate events

Open Instagram, YouTube, TikTok, Reddit, and X in turn. Scroll for 2–5 minutes
on each app. Do a mix of fast and slow scrolling.

### 4. Pull the log

```bash
adb pull /sdcard/Android/data/com.precog.m0spike/files/precog_m0_events.csv .
```

Or the internal path if external storage is unavailable:

```bash
adb shell run-as com.precog.m0spike cat files/precog_m0_events.csv > precog_m0_events.csv
```

---

## What to look for in the CSV

```
ts_ms,package,event_type,scroll_delta_x,scroll_delta_y,
from_index,to_index,item_count,max_scroll_x,max_scroll_y,scroll_x,scroll_y
```

| Column | GO criterion | NO-GO signal |
|---|---|---|
| `scroll_delta_y` | Non-zero for ≥3 of 5 apps | All zeros — events fired but no delta |
| `from_index` / `to_index` | Vary per event | Always −1 — app uses custom scroll view |
| `ts_ms` (inter-event gaps) | Varies 100ms–2000ms | All bunched at identical timestamps |
| Event rate | ≥1 per second when scrolling | Zero events for an app — not firing |

---

## GO / NO-GO decision matrix

| Condition | Decision | Consequence |
|---|---|---|
| `scrollDeltaY` non-zero in ≥3 apps, inter-event gaps vary | **GO** | Proceed to M1 (Room schema + onboarding) |
| `scrollDeltaY` zero but `from_index`/`to_index` vary | **GO — degraded** | Can compute inter-event interval but not scroll distance; PRECOG loses `scroll_delta` feature |
| Events fire but all timing fields are zero | **NO-GO** | AccessibilityService insufficient; evaluate MediaProjection or alternate path |
| Zero events for all apps | **NO-GO** | Likely Android 13+ restriction; evaluate alternate approach |

A degraded GO still supports the primary features:
- `inter_scroll_interval` (from `ts_ms` gaps)
- `burstiness` (coefficient of variation of gaps)
- `passive_ratio` (fraction of events without user-initiated trigger)
- `direction_reversals` (from `scroll_delta_y` sign flips, if available)

These four are sufficient for a meaningful M1 build.

---

## Files in this spike

```
android/
  app/
    src/main/
      java/com/precog/m0spike/
        EventLoggerService.kt   ← AccessibilityService, logs to CSV
        MainActivity.kt         ← Launcher, opens Accessibility Settings
      res/xml/
        accessibility_service_config.xml
      AndroidManifest.xml
    build.gradle.kts
  build.gradle.kts
  settings.gradle.kts
  M0_FEASIBILITY_SPIKE.md       ← this file
```

**This entire `android/` directory is throwaway M0 code.** M1 will be a clean
new module with Room, SQLCipher, proper architecture, and a Compose UI.

---

## Important constraints (do not weaken)

- `canRetrieveWindowContent="false"` in the service config — no content access
- No content, text, or view hierarchies are logged — timing/delta only
- No network calls from the spike
- Target packages are hardcoded — service does not activate on other apps
- HMOG Terms of Use: non-commercial research only, attribution required
- Repository stays private until provisional patent filed

---

## Next steps after GO

| Milestone | Description |
|---|---|
| M1 | Clean `AccessibilityService` + Room schema + SQLCipher local buffer + onboarding + consent |
| M2 | Kotlin feature extractor + Python parity test (inter_scroll_interval, burstiness, passive_ratio, direction_reversals) |
| M3 | BaselineEngine (GMM-2 density, empirical-Bayes shrinkage) + DeviationEngine |
| M4 | Offline ablation harness (subject-wise CV on extracted features) — honest GO/NO-GO for personalisation claim |
| M5 | Compose UI implementing WF-01 through WF-08 (see `ux/wireframes/`) |

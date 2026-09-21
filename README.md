# PRECOG

**Personalized Recognition and Estimation of Compulsive Online-scrolling Gestures**

*Digital wellbeing, before it becomes a problem.*

A privacy-first system that learns an individual's scroll-interaction baseline and estimates
behavioural deviation from that personal norm, rather than counting screen time against fixed
thresholds.

> **PRECOG is not** a diagnostic tool, a screen-time tracker, a content monitor, or a surveillance
> application. It estimates *behavioural deviation*. It does not diagnose anything.

---

## Status

Pre-implementation. Datasets acquired and audited; analysis not yet started.

**Private repository.** No patent application has been filed, and public disclosure of the
mechanism may bar patentability in India, which has no general grace period. Nothing gets published
— no public repo, preprint, or demo — without an explicit decision. See `docs/PLAN.md`.

---

## Documentation

| Document | What it covers |
|---|---|
| [`docs/SPEC.md`](docs/SPEC.md) | Technical specification — architecture, features, baseline and deviation maths, data model |
| [`docs/PLAN.md`](docs/PLAN.md) | Execution plan, hypotheses, calendar, risks |
| [`docs/DATASETS.md`](docs/DATASETS.md) | Dataset inventory, verified structure, coverage, limitations |
| [`docs/RELATED_WORK.md`](docs/RELATED_WORK.md) | 22-paper prior-work library, annotated |
| [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md) | Repository structure and naming rules |
| `docs/source/` | Original blueprint, literature review, brand assets |

---

## Layout

```
config/       tunable parameters — no hard-coded ML constants anywhere else
data/         raw (immutable) → interim → processed → synthetic
research/     Python package, experiments, tests, reference code
android/      Kotlin / Jetpack Compose client
ux/           UI/UX deliverable — research through usability testing
paper/        manuscript, figures, tables, references
results/      generated outputs; never hand-edited
references/   prior-work library
scripts/      one-off utilities
```

---

## Data

Four public datasets, none committed to the repository. Re-obtain from the DOIs in
`docs/DATASETS.md`.

| Dataset | Users | Provides | Licence |
|---|---|---|---|
| **HMOG** | 100 × 24 sessions | Event-level scroll timing **and** kinematics | ToU, non-commercial, **no redistribution** |
| **FETA** | 470 (90 @ 31 d) | Per-stroke kinematics at scale | ODC-PDDL (public domain) |
| **Tappigraphy** | 189 (147 ≥ 30 d) | Naturalistic hourly behaviour, circadian | Open |
| **AITouch** | 45 | Tablet gestures — low relevance | CC BY-NC 4.0 |

---

## Principles

1. Never invent telemetry. A feature that cannot be measured does not exist.
2. Never rename an unavailable measure after an available proxy.
3. Every risk estimate carries its evidence and a confidence value.
4. Never let anomalous behaviour silently redefine the baseline.
5. Subject-wise cross-validation always. Random splits leak users and inflate everything.
6. Synthetic results are never reported as empirical findings.
7. Null results get reported, not buried.
8. Behavioural language only — deviation, not diagnosis.

---

## Licence

Dual-licensed under either **[Apache-2.0](LICENSE-APACHE)** or **[MIT](LICENSE-MIT)**, at your
option. See [LICENSE](LICENSE) for what is and is not covered.

**The datasets are not.** None are distributed here; each is obtained from its own source using the
DOIs in [docs/DATASETS.md](docs/DATASETS.md) and carries its own terms. HMOG in particular permits
non-commercial research only, forbids redistribution, and requires attribution in publications.

PRECOG is a research prototype, not a medical or diagnostic tool. It reports how a person's
scrolling compares to their own earlier scrolling — nothing more. No detection-accuracy figure is
claimed, because none has been measured on the features the app actually observes.

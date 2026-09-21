# PRECOG — Repository Structure & Naming Conventions

**Applies to every file added to this repository.** When in doubt, match the nearest existing
example rather than inventing a variant.

---

## 1. Structure

```
PRECOG/
├── README.md
├── .gitignore
│
├── config/                     all tunable parameters — never hard-code these
│   ├── features.yaml
│   ├── baseline.yaml
│   ├── risk.yaml
│   └── experiment.yaml
│
├── data/
│   ├── raw/                    IMMUTABLE. Never write, never edit, never clean in place.
│   │   ├── feta/
│   │   ├── hmog/
│   │   ├── tappigraphy/
│   │   └── aitouch/
│   ├── interim/                extracted / normalised, reproducible from raw
│   ├── processed/              model-ready feature tables
│   └── synthetic/              generated, with ground truth
│
├── research/                   Python
│   ├── precog/                 importable package
│   │   ├── io/                 one loader per dataset
│   │   ├── features/
│   │   ├── baseline/
│   │   ├── deviation/
│   │   ├── state/
│   │   ├── risk/
│   │   └── synthetic/
│   ├── experiments/            EXP-NNN_* — one directory per run
│   ├── notebooks/              exploration only; nothing load-bearing
│   ├── reference-code/         third-party code read for reference, not imported
│   └── tests/
│       └── golden_vectors/     shared Kotlin/Python parity fixtures
│
├── android/                    Kotlin / Jetpack Compose
│
├── ux/                         UI/UX course deliverable
│   ├── research/
│   ├── personas/
│   ├── journeys/
│   ├── wireframes/
│   ├── design-system/
│   └── usability/
│
├── paper/
│   ├── manuscript/
│   ├── figures/
│   ├── tables/
│   └── references/             .bib
│
├── results/                    experiment outputs, never edited by hand
│   ├── figures/
│   ├── tables/
│   └── logs/
│
├── references/
│   └── papers/                 the prior-work library
│
├── docs/
│   ├── SPEC.md
│   ├── PLAN.md
│   ├── DATASETS.md
│   ├── RELATED_WORK.md
│   ├── CONVENTIONS.md
│   └── source/                 original blueprint, literature review, brand assets
│
└── scripts/                    one-off utilities
```

**The `data/raw` rule is absolute.** Anything under `raw/` is treated as read-only. Every cleaning,
filtering or reshaping step writes to `interim/` or `processed/` and is reproducible by re-running
code. This is what makes results defensible when a reviewer asks how a number was produced.

---

## 2. Naming by file type

| Kind | Convention | Example |
|---|---|---|
| Directory | `lowercase-kebab-case` | `design-system/` |
| Python package dir | `lowercase_snake_case` (import requirement) | `precog/features/` |
| Python module | `snake_case.py` | `feta_loader.py` |
| Python test | `test_<module>.py` | `test_baseline.py` |
| Kotlin class | `PascalCase.kt` | `ScrollEventCollector.kt` |
| Config | `kebab-case.yaml` | `baseline.yaml` |
| Doc (canonical) | `SCREAMING_SNAKE.md` | `SPEC.md` |
| Doc (ordered) | `NN-kebab-case.md` | `01-problem-statement.md` |
| Notebook | `NN_kebab-case.ipynb` | `01_feta-exploration.ipynb` |

---

## 3. Data files

```
{dataset}_{entity}_{version}.{ext}
```

`feta_strokes_v1.parquet` · `hmog_scroll-events_v1.parquet` · `tappigraphy_hourly_v1.parquet`
· `synthetic_sessions_v2.parquet`

**Under `raw/`, keep the publisher's original filenames.** Renaming raw files breaks traceability
back to the source deposit. Rename only on the way into `interim/`.

Prefer **Parquet** over CSV for anything over ~100 MB — typically 5–10× smaller and far faster to
load. Keep CSV only where a human needs to read it.

---

## 4. Papers

```
{FirstAuthorSurname}{Year}_{ShortSlug}.pdf
```

`Frank2013_Touchalytics.pdf` · `Sitova2016_HMOG.pdf` · `Orzikulova2024_Time2Stop.pdf`

This matches BibTeX citation keys, so the filename *is* the citation key — no lookup table needed.

**Never invent an author name.** Where the first author has not been verified, use the identifier
instead and rename once confirmed:

```
arXiv{ID}_{ShortSlug}.pdf     →  arXiv2210.01594_GANTouch.pdf
```

Files still carrying an `arXiv` prefix are a to-do list: open the PDF, read the author line,
rename. Do not guess.

---

## 5. Experiments

One directory per run, never overwritten:

```
research/experiments/EXP-007_personalized-vs-global/
├── config.yaml        exact parameters used
├── run.py
├── README.md          hypothesis · method · result · observation · next action
└── outputs/
```

`README.md` follows the research-log format:

```markdown
# EXP-007 — Personalized vs global baseline
Date:        2026-10-08
Hypothesis:  H3 — personalized baselines lower FPR at matched sensitivity
Dataset:     hmog_scroll-events_v1  (subject-wise CV, 5 folds)
Versions:    features-v0.2 · baseline-v0.1 · model-v0.1
Seed:        42
Result:      <numbers>
Observation: <what it means>
Next:        <what follows>
```

**Numbers are never edited after the fact.** A wrong run gets a new EXP number, not a correction.
This is the record that makes the paper reproducible, and it is also the thing that protects you if
a reviewer questions a result.

---

## 6. Figures and tables

```
fig-NN_short-name.{pdf,png}      tab-NN_short-name.{tex,csv}
```

`fig-03_baseline-convergence.pdf` · `tab-02_ablation-ladder.tex`

`NN` matches the number in the manuscript. Figures are **generated by code into `results/figures/`**
and copied to `paper/figures/` only when the manuscript freezes. Never hand-edit a generated figure
— if it needs changing, change the code.

---

## 7. Versioning

Every stored prediction carries `feature_version`, `baseline_version`, `model_version`
(`SPEC.md` §9). Bump on any change to the computation, never silently.

```
features-v0.2 · baseline-v0.1 · model-v0.1 · precog-v0.1
```

---

## 8. Things not to do

- Spaces in filenames — they break shell scripts and CI
- `final`, `final2`, `new`, `old`, `copy`, `backup` in any name — that is what versions and git are for
- Writing into `data/raw/`
- Hand-editing anything in `results/`
- Committing data files — `.gitignore` covers `data/`, and the raw sets are re-downloadable from their DOIs
- Inventing an author surname for a paper filename

# PRECOG — Prior Art Notes

Findings from reading the reference library that **change design decisions**. Not a summary of the
papers — only what alters what we build. Full bibliography in `RELATED_WORK.md`.

---

## 1. Touchalytics defines the canonical feature set — and FETA implements it exactly

Frank et al. (2013) propose **30 stroke features**, ranked by mutual information with user identity:

| Rank | Feature | MI |
|---|---|---|
| 1 | mid-stroke area covered | 20.6% |
| 2 | 20th-pct pairwise velocity | 19.6% |
| 3 | mid-stroke pressure | 17.3% |
| 4 | direction of end-to-end line | 11.1% |
| 5–8 | stop x · start x · average direction · start y | ~9–10% |
| … | stroke duration · end-to-end distance · trajectory length · 80th-pct velocity | ~8% |
| … | **inter-stroke time** | 5.3% |
| last | change of finger orientation | **0%** |

Every column in FETA's `features.csv` maps to this list. **FETA is Touchalytics, computed at scale.**

**Design consequences:**
- Compute the *same* features from HMOG so results are directly comparable across datasets. Do not
  invent a parallel feature set.
- **FETA dropped `inter-stroke time`, which Touchalytics had.** That single omission is why
  `features.csv` has no timestamps and why HMOG became the primary source.
- `change of finger orientation` carries **zero** mutual information — drop it, and say why.
- The three highest-MI features (area, velocity percentile, pressure) are all available in HMOG's
  `ScrollEvent.csv`.

---

## 2. FETA's six pitfalls are binding constraints on our evaluation

Georgiev et al. reviewed 30 touch-dynamics papers; **all of them fall into at least one pitfall.**
Measured effects on EER:

| | Pitfall | Effect | What PRECOG must do |
|---|---|---|---|
| **P1** | Small sample size (users *and* sessions) | reduces mean EER, smooths variance | Report a sample-size analysis, including **n = 40** for comparability |
| **P2** | Phone model mixing | **3.2–5.8 pp** | HMOG is single-model (fine). **FETA mixes iPhone models — must split or control** |
| **P3** | **Non-contiguous training data** | **3.8 pp** | **Build the baseline from contiguous *early* sessions and test on *later* ones.** Never sample randomly across time |
| **P4** | Attacker data in training | **2.55 pp** | Never include other users' data in a personal baseline |
| **P5** | Arbitrary aggregation windows | large | Report **single-scroll** performance alongside any aggregated figure |
| **P6** | Code/data unavailable | — | Release the extractor and feature code |

Cumulative effect of these choices: **8.9 pp EER**. These are not stylistic preferences — they are
the difference between a credible number and an inflated one.

**P3 is the one that bites PRECOG hardest.** It also happens to be the correct design for a
*temporal* baseline: learn from early sessions, detect on later ones. The methodological
requirement and the product logic agree.

---

## 3. Bayesian novelty detection validates the SPEC's approach

Lamb et al. (Callsign) state the problem PRECOG has, exactly:

> Supervised models are difficult to utilise in a real-world environment as **negatively labelled
> samples are not available in sufficient quantities per-user.**

Their answer is **novelty detection** — model the probability distribution of one user's features
and score deviation. They compare three:

1. **Shrunk covariance estimate** ← what `SPEC.md` §5 Tier 2 already specifies
2. Bayesian Gaussian with priors ← equivalent in spirit to our empirical-Bayes shrinkage
3. Bayesian non-parametric **infinite mixture of Gaussians** (Dirichlet Process)

**Design consequences:**
- The SPEC's shrunk-covariance Mahalanobis is an established choice, not an invention. Cite this.
- Priors are how they solve **few enrolment samples** — the same cold-start problem, same solution
  shape as our context-cell shrinkage.
- The mixture model exists because **a single user exhibits multiple behavioural modes.** A unimodal
  Gaussian baseline may be wrong for a person who scrolls differently in different contexts. Our
  context-conditioned cells are one answer; a per-user GMM is another worth testing.
- They report EER against **number of enrolment samples** — structurally identical to H2's baseline
  convergence curve. Use their framing.

---

## 4. Time2Stop's features confirm the differentiation story

The dominant prior art uses **only coarse signals**: unlock frequency and duration, screen on/off,
battery, app visit frequency and time spent, notification count and diversity, stationary/mobile
duration, ambient lux.

**No kinematics. No inter-scroll timing. No per-gesture anything.**

The blueprint's claimed differentiation survives contact with the actual paper. PRECOG operates a
full granularity tier below Time2Stop — that gap is the contribution, and it is real.

---

## 5. Net effect on the plan

| Decision | Status after reading |
|---|---|
| Compute Touchalytics-compatible features from HMOG | **New requirement** — enables cross-dataset comparison |
| Shrunk-covariance deviation (`SPEC` §5) | **Validated** by prior art; now citable |
| Empirical-Bayes context shrinkage (`SPEC` §5) | **Validated** in spirit; priors serve the same role |
| Baseline from contiguous early sessions | **Now mandatory** (P3), was unspecified |
| Per-user GMM as an alternative to unimodal baseline | **New candidate** worth an ablation arm |
| Drop `change of finger orientation` | **New** — zero MI, documented |
| Report single-scroll + n=40 results | **Now mandatory** (P1, P5) |
| Subject-wise CV | Already in `SPEC`; independently confirmed |

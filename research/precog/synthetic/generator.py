"""Synthetic behavioural data with ground truth.

Not evidence. This exists to test a mechanism EXP-003 could only infer — that personalization
should help for person-relative deviations and not for population-consistent ones — by
generating both on demand with known labels.

Population statistics are fitted from real data so that feature correlations match what the
real pipeline sees; only the generative structure on top is synthetic.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class PopulationModel:
    """Population means, between-user spread, and within-user covariance, fitted from real data."""

    def __init__(self, df: pd.DataFrame, features: list[str]):
        self.features = features
        X = df[features].astype(float)

        per_user = X.groupby(df["subject"]).mean()
        self.mu = per_user.mean().to_numpy()
        self.tau = per_user.std().to_numpy()                    # between-user spread

        centred = X.to_numpy() - per_user.reindex(df["subject"]).to_numpy()
        ok = np.isfinite(centred).all(axis=1)
        self.cov_within = np.cov(centred[ok], rowvar=False)     # within-user covariance
        self.sigma = np.sqrt(np.clip(np.diag(self.cov_within), 1e-12, None))

        # Correlation is kept and rescaled per user, so a user can be more or less variable
        # overall without losing the correlation structure between features.
        d = np.diag(1.0 / self.sigma)
        self.corr = d @ self.cov_within @ d
        self.corr = np.nan_to_num(self.corr, nan=0.0)
        np.fill_diagonal(self.corr, 1.0)
        self._chol = self._safe_chol(self.corr)

    @staticmethod
    def _safe_chol(c: np.ndarray) -> np.ndarray:
        for eps in (0, 1e-8, 1e-6, 1e-4, 1e-2):
            try:
                return np.linalg.cholesky(c + eps * np.eye(len(c)))
            except np.linalg.LinAlgError:
                continue
        return np.eye(len(c))

    def draw_correlated(self, rng, n: int) -> np.ndarray:
        return rng.standard_normal((n, len(self.features))) @ self._chol.T


def generate(pop: PopulationModel, cfg: dict, rng) -> pd.DataFrame:
    """Build the full synthetic cohort."""
    p, u, dr, ctx, an = (cfg["population"], cfg["users"], cfg["drift"],
                         cfg["context"], cfg["anomaly"])
    F = len(pop.features)
    n_users = p["n_users"]

    # --- RULE 1: user means and per-user variability ---------------------------------
    z_u = rng.standard_normal((n_users, F))
    user_mu = pop.mu[None, :] + pop.tau[None, :] * z_u
    kappa = rng.normal(u["kappa_mean"], u["kappa_sd"], n_users)
    n_dist = int(n_users * u["distinctive_fraction"])
    kappa[rng.permutation(n_users)[:n_dist]] -= 2 * u["kappa_sd"]   # a distinctive tail
    user_sigma = pop.sigma[None, :] * np.exp(kappa)[:, None]

    # --- RULE 2: per-user drift rate --------------------------------------------------
    drift_rate = (rng.normal(dr["scale_sigma_per_30d"], dr["per_user_sd"], n_users)
                  if dr["enabled"] else np.zeros(n_users))
    drift_dir = rng.choice([-1.0, 1.0], size=(n_users, F))

    # Anomaly direction vector over the feature space.
    dvec = np.zeros(F)
    for i, f in enumerate(pop.features):
        dvec[i] = an["direction"].get(f, 0.0)

    rows, meta = [], []
    day_ms = 86_400_000.0
    t_origin = 1_600_000_000_000.0

    for ui in range(n_users):
        n_sess = p["sessions_per_user"]
        sess_days = np.sort(rng.uniform(0, p["days_span"], n_sess))
        contexts = np.where(rng.random(n_sess) < ctx["secondary_fraction"], 1, 0)

        # Anomalous sessions arrive as one contiguous episode in the later half.
        n_anom = int(n_sess * an["affected_fraction"])
        start = rng.integers(n_sess // 2, max(n_sess // 2 + 1, n_sess - n_anom + 1))
        is_anom = np.zeros(n_sess, bool)
        is_anom[start:start + n_anom] = True

        for si in range(n_sess):
            n_g = rng.integers(*p["gestures_per_session"])
            base = user_mu[ui].copy()
            base += drift_dir[ui] * drift_rate[ui] * (sess_days[si] / 30.0) * user_sigma[ui]
            if contexts[si] == 1:
                base += ctx["shift_sigma"] * user_sigma[ui]

            noise = pop.draw_correlated(rng, n_g) * user_sigma[ui][None, :]
            X = base[None, :] + noise

            t0 = t_origin + sess_days[si] * day_ms
            rows.append((ui, si, contexts[si], is_anom[si], sess_days[si], t0, X))

        meta.append({"subject": ui, "kappa": kappa[ui], "drift_rate": drift_rate[ui]})

    # --- assemble ---------------------------------------------------------------------
    frames = []
    for ui, si, c, anom, day, t0, X in rows:
        n_g = len(X)
        df = pd.DataFrame(X, columns=pop.features)
        df["subject"] = ui
        df["session"] = si
        df["context"] = ctx["levels"][c]
        df["day"] = day
        df["is_anomalous_session"] = anom
        df["t_start"] = t0 + np.arange(n_g) * 3000.0
        df["t_end"] = df["t_start"] + df.get("duration_ms", pd.Series(400.0, index=df.index))
        frames.append(df)

    out = pd.concat(frames, ignore_index=True)
    out.attrs["user_sigma"] = user_sigma
    out.attrs["tau"] = pop.tau
    out.attrs["meta"] = pd.DataFrame(meta)
    return out


def inject(df: pd.DataFrame, pop: PopulationModel, cfg: dict, kind: str, magnitude: float):
    """Apply one anomaly type to the flagged sessions. Returns a copy plus a label column.

    population_consistent : scaled by tau   — the same physical change for every user
    person_relative       : scaled by sigma_u — scaled to each user's own spread

    These differ in exactly one way, which is the entire point of the experiment.
    """
    an = cfg["anomaly"]
    out = df.copy()
    user_sigma = df.attrs["user_sigma"]
    tau = df.attrs["tau"]
    mask = out["is_anomalous_session"].to_numpy()

    for i, f in enumerate(pop.features):
        d = an["direction"].get(f, 0.0)
        if d == 0.0:
            continue
        if kind == "population_consistent":
            delta = magnitude * d * tau[i]
            out.loc[mask, f] = out.loc[mask, f] + delta
        elif kind == "person_relative":
            s = user_sigma[out.loc[mask, "subject"].to_numpy(), i]
            out.loc[mask, f] = out.loc[mask, f] + magnitude * d * s
        else:
            raise ValueError(kind)

    out["y"] = mask.astype(int)
    out.attrs.update(df.attrs)
    return out


def enforce(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Apply RULE 5 fidelity guards so synthetic gestures obey the same invariants as real ones."""
    c = cfg["constraints"]
    for f in c["non_negative"]:
        if f in df:
            df[f] = df[f].clip(lower=0)
    for f in c["bounded_01"]:
        if f in df:
            df[f] = df[f].clip(0, 1)
    if c.get("enforce_trajectory_ge_endtoend") and {"trajectory_length",
                                                    "end_to_end_distance"} <= set(df.columns):
        df["trajectory_length"] = np.maximum(df["trajectory_length"], df["end_to_end_distance"])
    return df

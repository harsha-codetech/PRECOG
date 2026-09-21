"""Personal behavioural baselines.

A baseline is a per-user, per-context summary of what that person's gestures normally look
like. Context cells are sparse by construction — a user has few gestures in any one
(posture x time-of-day) combination — so every cell statistic is shrunk toward that user's
global statistic in proportion to how much evidence the cell actually has (SPEC.md §5).

Robust statistics (median, MAD) are primary: behavioural distributions are skewed and a
handful of extreme gestures should not define "normal".
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _mad(x: pd.Series) -> float:
    med = x.median()
    return float((x - med).abs().median())


def summarise(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    """mean/std/median/mad/n per feature over a set of gestures."""
    rows = {}
    for f in features:
        s = df[f].dropna()
        rows[f] = {
            "mean": float(s.mean()) if len(s) else np.nan,
            "std": float(s.std()) if len(s) > 1 else np.nan,
            "median": float(s.median()) if len(s) else np.nan,
            "mad": _mad(s) if len(s) else np.nan,
            "n": int(len(s)),
        }
    return pd.DataFrame(rows).T


class PersonalBaseline:
    """One user's baseline: a global summary plus shrunk per-context summaries."""

    def __init__(self, features: list[str], cfg: dict):
        self.features = features
        self.cfg = cfg
        self.k = cfg["shrinkage"]["k"]
        self.context_keys = cfg["context_keys"]
        self.global_: pd.DataFrame | None = None
        self.cells_: dict[tuple, pd.DataFrame] = {}
        self.cov_: np.ndarray | None = None
        self.cov_mean_: np.ndarray | None = None
        self.core_: list[str] = []

    def fit(self, df: pd.DataFrame) -> "PersonalBaseline":
        self.global_ = summarise(df, self.features)

        keys = [k for k in self.context_keys if k in df.columns]
        if keys:
            for name, part in df.groupby(keys, dropna=False):
                cell = summarise(part, self.features)
                self.cells_[name if isinstance(name, tuple) else (name,)] = self._shrink(cell)

        self._fit_covariance(df)
        return self

    def _shrink(self, cell: pd.DataFrame) -> pd.DataFrame:
        """Pull each cell statistic toward the user's global value by w = n/(n+k)."""
        out = cell.copy()
        w = cell["n"] / (cell["n"] + self.k)
        for stat in ("mean", "std", "median", "mad"):
            out[stat] = w * cell[stat].fillna(self.global_[stat]) + (1 - w) * self.global_[stat]
        out["shrinkage_w"] = w
        return out

    def _fit_covariance(self, df: pd.DataFrame) -> None:
        """Ledoit-Wolf shrunk covariance over a reduced core, for Mahalanobis distance."""
        m = self.cfg["mahalanobis"]
        core = [f for f in m["core_features"] if f in df.columns]
        sub = df[core].dropna()
        if len(sub) < m["min_samples"] or len(core) < 2:
            return
        try:
            from sklearn.covariance import LedoitWolf
        except ImportError:
            return
        lw = LedoitWolf().fit(sub.to_numpy())
        self.cov_ = lw.precision_
        self.cov_mean_ = lw.location_
        self.core_ = core

    def reference(self, context: tuple | None = None) -> pd.DataFrame:
        """The summary to compare against: the matching context cell, else global."""
        if context is not None and context in self.cells_:
            return self.cells_[context]
        return self.global_

    @property
    def has_covariance(self) -> bool:
        return self.cov_ is not None


def fit_all(
    df: pd.DataFrame, features: list[str], cfg: dict, by: str = "subject"
) -> dict[int, PersonalBaseline]:
    return {
        int(uid): PersonalBaseline(features, cfg).fit(part)
        for uid, part in df.groupby(by)
    }

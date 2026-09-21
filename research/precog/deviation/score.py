"""Deviation scoring against a personal baseline.

Two tiers (SPEC.md §5):

  Tier 1 — robust per-feature z, always available.
           z = 0.6745 * (x - median) / MAD

  Tier 2 — Mahalanobis distance over a reduced feature core with Ledoit-Wolf shrunk
           covariance, available once the user has enough gestures. Tier 1 treats features
           as independent, which double-counts correlated ones (velocity and inter-scroll
           interval are not independent); tier 2 does not.

Every score records which tier produced it — that is part of reproducibility, not a detail.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from precog.baseline.engine import PersonalBaseline


def robust_z(
    values: pd.DataFrame, baseline: PersonalBaseline, context: tuple | None = None
) -> pd.DataFrame:
    """Per-feature robust z-scores against the matching baseline cell."""
    ref = baseline.reference(context)
    c = baseline.cfg["robust"]
    floor = c["mad_floor"]
    const = c["consistency_constant"]

    out = {}
    for f in baseline.features:
        if f not in values.columns or f not in ref.index:
            continue
        mad = max(float(ref.loc[f, "mad"]), floor) if np.isfinite(ref.loc[f, "mad"]) else floor
        out[f] = const * (values[f] - ref.loc[f, "median"]) / mad
    return pd.DataFrame(out, index=values.index)


def aggregate_z(z: pd.DataFrame) -> pd.Series:
    """Collapse per-feature z into one magnitude, ignoring missing features."""
    return np.sqrt((z**2).mean(axis=1, skipna=True))


def mahalanobis(values: pd.DataFrame, baseline: PersonalBaseline) -> pd.Series:
    """Distance over the reduced core. NaN where the baseline has no covariance yet."""
    if not baseline.has_covariance:
        return pd.Series(np.nan, index=values.index)
    X = values[baseline.core_].to_numpy(float)
    d = X - baseline.cov_mean_
    ok = np.isfinite(d).all(axis=1)
    out = np.full(len(X), np.nan)
    if ok.any():
        dd = d[ok]
        out[ok] = np.sqrt(np.einsum("ij,jk,ik->i", dd, baseline.cov_, dd).clip(min=0))
    return pd.Series(out, index=values.index)


def score(
    values: pd.DataFrame, baseline: PersonalBaseline, context: tuple | None = None
) -> pd.DataFrame:
    """Both tiers plus the per-feature evidence that produced them.

    Evidence is returned alongside the score by construction: a deviation without the
    features that caused it is a bug (SPEC.md §7).
    """
    z = robust_z(values, baseline, context)
    out = pd.DataFrame(index=values.index)
    out["deviation_z"] = aggregate_z(z)
    out["deviation_mahalanobis"] = mahalanobis(values, baseline)
    out["tier"] = np.where(out["deviation_mahalanobis"].notna(), 2, 1)
    out["deviation"] = out["deviation_mahalanobis"].fillna(out["deviation_z"])

    # Top contributing feature and its z — the minimum viable explanation.
    if not z.empty:
        absz = z.abs()
        out["top_feature"] = absz.idxmax(axis=1)
        out["top_feature_z"] = z.to_numpy()[
            np.arange(len(z)), absz.to_numpy().argmax(axis=1)
        ]
    return out


def top_evidence(z_row: pd.Series, n: int = 3) -> list[tuple[str, float]]:
    """The n features that drove one deviation score, largest magnitude first."""
    s = z_row.dropna()
    return [(k, float(v)) for k, v in s.reindex(s.abs().sort_values(ascending=False).index)[:n].items()]

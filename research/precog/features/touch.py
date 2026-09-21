"""Gesture-level touch features.

Implements the Touchalytics feature set (Frank et al., IEEE TIFS 2013, Table 1) so that
features computed here are directly comparable with FETA's `features.csv`, which uses the
same definitions.

Three of the original features are deliberately absent — see `config/features.yaml`:
pressure (constant in HMOG), finger orientation (not recorded), and change of finger
orientation (zero mutual information with user identity).

A gesture is a run of MOVE samples sharing one ScrollID. Input is therefore the per-sample
table, not the gesture summary.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _circular_mean(angles: np.ndarray) -> float:
    return float(np.arctan2(np.sin(angles).mean(), np.cos(angles).mean()))


def _mean_resultant_length(angles: np.ndarray) -> float:
    """Circular concentration in [0, 1]. 1 = perfectly straight, 0 = uniformly scattered."""
    return float(np.hypot(np.sin(angles).mean(), np.cos(angles).mean()))


def _perpendicular_deviations(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Distance of each point from the straight line joining first and last point."""
    x0, y0, x1, y1 = x[0], y[0], x[-1], y[-1]
    dx, dy = x1 - x0, y1 - y0
    denom = np.hypot(dx, dy)
    if denom == 0:
        return np.hypot(x - x0, y - y0)
    return np.abs(dy * (x - x0) - dx * (y - y0)) / denom


def _direction_flag(dx: float, dy: float) -> int:
    """0 up, 1 down, 2 left, 3 right. Screen y grows downward."""
    if abs(dy) >= abs(dx):
        return 1 if dy > 0 else 0
    return 3 if dx > 0 else 2


def gesture_features(
    t: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    size: np.ndarray,
    orientation: int,
    cfg: dict,
) -> dict[str, float]:
    """Compute one gesture's features from its trajectory samples."""
    pct = cfg["percentiles"]
    n = len(t)

    duration = float(t[-1] - t[0])
    seg_dx, seg_dy = np.diff(x), np.diff(y)
    seg_len = np.hypot(seg_dx, seg_dy)
    seg_dt = np.diff(t).astype(float)
    seg_dt[seg_dt <= 0] = np.nan  # a zero gap makes velocity meaningless, not infinite

    trajectory_length = float(seg_len.sum())
    end_to_end = float(np.hypot(x[-1] - x[0], y[-1] - y[0]))

    velocity = seg_len / seg_dt
    acceleration = np.diff(velocity) / seg_dt[1:] if len(velocity) > 1 else np.array([np.nan])
    angles = np.arctan2(seg_dy, seg_dx)
    deviations = _perpendicular_deviations(x, y)

    mid = n // 2
    tail = cfg["velocity_tail_points"]
    head = cfg["acceleration_head_points"]

    f: dict[str, float] = {
        "n_samples": float(n),
        "duration_ms": duration,
        "start_x": float(x[0]),
        "start_y": float(y[0]),
        "stop_x": float(x[-1]),
        "stop_y": float(y[-1]),
        "end_to_end_distance": end_to_end,
        "trajectory_length": trajectory_length,
        "end_to_end_traj_ratio": end_to_end / trajectory_length if trajectory_length else np.nan,
        "direction_end_to_end": float(np.arctan2(y[-1] - y[0], x[-1] - x[0])),
        "average_direction": _circular_mean(angles),
        "mean_resultant_length": _mean_resultant_length(angles),
        "largest_deviation": float(np.nanmax(deviations)),
        "average_velocity": trajectory_length / duration if duration > 0 else np.nan,
        "median_velocity_last_pts": float(np.nanmedian(velocity[-tail:])) if len(velocity) else np.nan,
        "median_acceleration_first_pts": float(np.nanmedian(acceleration[:head]))
        if np.isfinite(acceleration).any()
        else np.nan,
        "mid_stroke_area": float(size[mid]),
        "phone_orientation": float(orientation),
        "direction_flag": float(_direction_flag(x[-1] - x[0], y[-1] - y[0])),
    }

    for p in pct:
        f[f"velocity_p{p}"] = float(np.nanpercentile(velocity, p)) if np.isfinite(velocity).any() else np.nan
        f[f"acceleration_p{p}"] = (
            float(np.nanpercentile(acceleration, p)) if np.isfinite(acceleration).any() else np.nan
        )
        f[f"deviation_p{p}"] = float(np.nanpercentile(deviations, p))

    return f


def extract(samples: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Compute features for every gesture in a per-sample ScrollEvent table.

    Gestures shorter than `quality.min_samples` or longer than `quality.max_duration_ms`
    are dropped and counted, never silently repaired.
    """
    q = cfg["quality"]
    need = ["ActivityID", "ScrollID", "Systime", "Current_X", "Current_Y",
            "Current_size", "Phone_orientation", "subject", "session"]
    df = samples[need].sort_values(["ActivityID", "ScrollID", "Systime"])

    keys = df[["ActivityID", "ScrollID"]].to_numpy()
    starts = np.flatnonzero(np.r_[True, (keys[1:] != keys[:-1]).any(axis=1)])
    bounds = np.r_[starts, len(df)]

    t = df["Systime"].to_numpy(np.int64)
    x = df["Current_X"].to_numpy(float)
    y = df["Current_Y"].to_numpy(float)
    sz = df["Current_size"].to_numpy(float)
    orient = df["Phone_orientation"].to_numpy()
    act = df["ActivityID"].to_numpy()
    sid = df["ScrollID"].to_numpy()
    subj = df["subject"].to_numpy()
    sess = df["session"].to_numpy()

    rows, dropped_short, dropped_long = [], 0, 0
    for a, b in zip(bounds[:-1], bounds[1:]):
        if b - a < q["min_samples"]:
            dropped_short += 1
            continue
        dur = t[b - 1] - t[a]
        if dur > q["max_duration_ms"] or dur < q["min_duration_ms"]:
            dropped_long += 1
            continue
        f = gesture_features(t[a:b], x[a:b], y[a:b], sz[a:b], orient[a], cfg)
        f.update(
            subject=int(subj[a]), session=int(sess[a]),
            ActivityID=int(act[a]), ScrollID=int(sid[a]),
            t_start=int(t[a]), t_end=int(t[b - 1]),
        )
        rows.append(f)

    out = pd.DataFrame(rows)
    if out.empty:
        return out

    # Gap from the previous gesture's lift to this one's touch-down — Touchalytics'
    # "inter-stroke time". FETA's feature table omits it; that omission is why HMOG is
    # the primary source. First gesture of an activity has no predecessor.
    out = out.sort_values(["ActivityID", "t_start"]).reset_index(drop=True)
    prev_end = out.groupby("ActivityID")["t_end"].shift(1)
    gap = out["t_start"] - prev_end
    # Negative means two gestures overlapped (multi-touch); not a pause, so drop it.
    out["inter_scroll_ms"] = gap.where(gap >= 0)

    out.attrs["dropped_short"] = dropped_short
    out.attrs["dropped_long"] = dropped_long
    return out

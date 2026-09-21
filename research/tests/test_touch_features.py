"""Golden-vector tests for gesture feature extraction.

`touch_features.json` holds real HMOG gesture trajectories with their expected feature
values. The Kotlin on-device extractor must reproduce these same numbers from the same
inputs — if the two implementations diverge, every offline result is invalid (SPEC.md §9).

Regenerate deliberately, never to make a failing test pass.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest
import yaml

from precog.features.touch import extract, gesture_features

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "research/tests/golden_vectors/touch_features.json"
CONFIG = ROOT / "config/features.yaml"

TOLERANCE = 1e-6


def _load():
    return json.loads(GOLDEN.read_text()), yaml.safe_load(CONFIG.read_text())


def _arrays(case):
    s = case["samples"]
    return (
        np.array([p["t"] for p in s], dtype=np.int64),
        np.array([p["x"] for p in s], dtype=float),
        np.array([p["y"] for p in s], dtype=float),
        np.array([p["size"] for p in s], dtype=float),
    )


def test_golden_config_matches_current():
    golden, cfg = _load()
    assert golden["feature_version"] == cfg["feature_version"], (
        "feature_version changed without regenerating golden vectors"
    )
    for key, value in golden["config"].items():
        assert cfg[key] == value, f"config drift on {key}"


@pytest.mark.parametrize("idx", range(3))
def test_golden_vectors(idx):
    golden, cfg = _load()
    case = golden["cases"][idx]
    t, x, y, size = _arrays(case)
    got = gesture_features(t, x, y, size, case["orientation"], cfg)

    assert set(got) == set(case["expected"]), "feature set changed"
    for name, want in case["expected"].items():
        have = got[name]
        if want is None:
            assert math.isnan(have), f"{name}: expected NaN, got {have}"
        else:
            assert have == pytest.approx(want, abs=TOLERANCE), f"{name}: {have} != {want}"


def test_invariants_hold_on_golden_cases():
    """Bounds that must hold for any gesture, not just these three."""
    golden, cfg = _load()
    for case in golden["cases"]:
        f = gesture_features(*_arrays(case), case["orientation"], cfg)
        assert 0.0 <= f["end_to_end_traj_ratio"] <= 1.0 + TOLERANCE
        assert 0.0 <= f["mean_resultant_length"] <= 1.0 + TOLERANCE
        assert f["trajectory_length"] >= f["end_to_end_distance"] - TOLERANCE
        assert f["duration_ms"] > 0
        assert f["direction_flag"] in (0.0, 1.0, 2.0, 3.0)
        assert not math.isinf(f["average_velocity"])


def test_short_gestures_dropped_not_repaired():
    """A gesture below min_samples must be excluded, never padded or interpolated."""
    import pandas as pd

    _, cfg = _load()
    two_samples = pd.DataFrame({
        "ActivityID": [1, 1], "ScrollID": [0, 0],
        "Systime": [1000, 1050], "Current_X": [10.0, 20.0], "Current_Y": [10.0, 40.0],
        "Current_size": [0.02, 0.02], "Phone_orientation": [0, 0],
        "subject": [1, 1], "session": [1, 1],
    })
    out = extract(two_samples, cfg)
    assert out.empty

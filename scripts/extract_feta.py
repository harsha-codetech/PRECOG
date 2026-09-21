"""Extract FETA scroll gestures into the same feature schema as HMOG.

Selective by design: the archive holds 196,716 CSVs across three sensors and two gametypes,
of which only scroll + touch_data for the long-arm cohort is needed (~20,600 files, 0.4 GB).
Accelerometer and gyroscope are skipped entirely.

Follows EXP-005_feta-replication/PREREGISTRATION.md:
  - scroll gametype only (swipe / image-gallery excluded)
  - users with >= 20 scroll sessions
  - features computed by precog.features.touch, identical to HMOG
  - pressure excluded (constant in HMOG, so including it would confound the comparison)

    python scripts/extract_feta.py
    python scripts/extract_feta.py --limit-users 5     # smoke test
"""

from __future__ import annotations

import argparse
import io
import sys
import time
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))

from precog.features.touch import gesture_features  # noqa: E402

ARCHIVE = ROOT / "data/raw/feta/data_files.zip"
MIN_SESSIONS = 20
DOWN, MOVE, UP = 0, 1, 2


def index_archive(z: zipfile.ZipFile, gametype: str = "scroll") -> dict[str, list[tuple[str, str]]]:
    """user -> [(measurement_id, member)] for one gametype's touch_data only."""
    out: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for m in z.namelist():
        if not m.endswith(".csv") or m.startswith("__MACOSX"):
            continue
        p = m.split("/")
        if len(p) != 7 or p[3] != gametype or p[5] != "touch_data":
            continue
        out[p[1]].append((p[2], m))
    return out


def strokes(df: pd.DataFrame):
    """Split one iteration's touch stream into DOWN..UP strokes.

    A stroke opens on type 0 and closes on type 2. Samples before the first DOWN are
    dropped rather than attached to a stroke that was never observed starting.
    """
    t = df["timestamp"].to_numpy(float)
    x = df["x"].to_numpy(float)
    y = df["y"].to_numpy(float)
    a = df["area"].to_numpy(float)
    ty = df["type"].to_numpy(int)

    start = None
    for i, k in enumerate(ty):
        if k == DOWN:
            start = i
        elif k == UP and start is not None:
            if i - start + 1 >= 3:
                yield t[start:i + 1], x[start:i + 1], y[start:i + 1], a[start:i + 1]
            start = None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-users", type=int, default=None)
    ap.add_argument("--out-dir", default=str(ROOT / "data/processed"))
    ap.add_argument("--gametype", default="scroll", choices=["scroll", "swipe"])
    ap.add_argument("--cohort-from", default=None, help="restrict to users in this parquet")
    args = ap.parse_args()

    cfg = yaml.safe_load((ROOT / "config/features.yaml").read_text())
    q = cfg["quality"]
    version = cfg["feature_version"]

    if not ARCHIVE.exists():
        print(f"missing {ARCHIVE}")
        return 1

    t0 = time.time()
    z = zipfile.ZipFile(ARCHIVE)
    idx = index_archive(z, args.gametype)
    if args.cohort_from:
        keep = set(pd.read_parquet(args.cohort_from)["subject"].unique())
        cohort = sorted(u for u in idx if u in keep)
    else:
        cohort = sorted(u for u, v in idx.items() if len({m for m, _ in v}) >= MIN_SESSIONS)
    if args.limit_users:
        cohort = cohort[: args.limit_users]
    print(f"archive indexed: {len(idx)} users total")
    print(f"cohort (>= {MIN_SESSIONS} scroll sessions): {len(cohort)} users\n")

    rows, short, bad_dur, files = [], 0, 0, 0
    for n, user in enumerate(cohort, 1):
        for meas, member in idx[user]:
            try:
                raw = z.read(member)
            except Exception:
                continue
            if not raw.strip():
                continue
            try:
                df = pd.read_csv(io.BytesIO(raw))
            except Exception:
                continue
            if df.empty or "type" not in df.columns:
                continue
            files += 1
            for t, x, y, a in strokes(df):
                if len(t) < q["min_samples"]:
                    short += 1
                    continue
                dur = t[-1] - t[0]
                if dur > q["max_duration_ms"] or dur < q["min_duration_ms"]:
                    bad_dur += 1
                    continue
                # FETA does not record phone orientation; passed as 0 and excluded from
                # any cross-dataset comparison (logged as a pre-registration deviation).
                f = gesture_features(t, x, y, a, 0, cfg)
                f.update(subject=user, session=int(meas),
                         t_start=float(t[0]), t_end=float(t[-1]))
                rows.append(f)
        if n % 20 == 0 or n == len(cohort):
            print(f"  [{n:>3}/{len(cohort)}] {len(rows):>8,} gestures", flush=True)

    if not rows:
        print("no gestures extracted")
        return 1

    out = pd.DataFrame(rows)
    # Gap to the previous gesture within the same session — Touchalytics' inter-stroke time.
    out = out.sort_values(["subject", "session", "t_start"]).reset_index(drop=True)
    prev = out.groupby(["subject", "session"])["t_end"].shift(1)
    gap = out["t_start"] - prev
    out["inter_scroll_ms"] = gap.where(gap >= 0)
    out["feature_version"] = version

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = "" if args.gametype == "scroll" else f"-{args.gametype}"
    path = out_dir / f"feta_gesture-features{tag}_{version}.parquet"
    out.to_parquet(path, index=False)

    print(f"\nfiles read: {files:,} | dropped: {short:,} short, {bad_dur:,} out of duration bounds")
    print(f"{path.name}: {len(out):,} gestures x {out.shape[1]} cols, "
          f"{path.stat().st_size / 2**20:.1f} MB")
    c = out.groupby("subject").size()
    print(f"subjects: {out.subject.nunique()} | gestures/subject: median {c.median():.0f} "
          f"min {c.min()} max {c.max()}")
    s = out.groupby("subject").session.nunique()
    print(f"sessions/subject: median {s.median():.0f} min {s.min()} max {s.max()}")
    print(f"\ndone in {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

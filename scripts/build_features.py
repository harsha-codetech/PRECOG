"""Compute gesture-level touch features from extracted HMOG scroll events.

    python scripts/build_features.py
    python scripts/build_features.py --limit-subjects 5    # smoke test

Reads  data/interim/hmog/hmog_scroll-events_v1.parquet
Writes data/processed/hmog_gesture-features_<version>.parquet
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))

from precog.features.touch import extract  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(ROOT / "config" / "features.yaml"))
    ap.add_argument("--input", default=str(ROOT / "data/interim/hmog/hmog_scroll-events_v1.parquet"))
    ap.add_argument("--out-dir", default=str(ROOT / "data/processed"))
    ap.add_argument("--limit-subjects", type=int, default=None)
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text())
    version = cfg["feature_version"]

    src = Path(args.input)
    if not src.exists():
        print(f"missing input: {src}\nrun scripts/extract_hmog.py first")
        return 1

    t0 = time.time()
    samples = pd.read_parquet(src)
    if args.limit_subjects:
        keep = sorted(samples["subject"].unique())[: args.limit_subjects]
        samples = samples[samples["subject"].isin(keep)]
    print(f"input: {len(samples):,} samples, {samples.subject.nunique()} subjects")

    feats = extract(samples, cfg)
    if feats.empty:
        print("no gestures survived quality filters")
        return 1

    feats["feature_version"] = version

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"hmog_gesture-features_{version}.parquet"
    feats.to_parquet(path, index=False)

    q = cfg["quality"]
    print(
        f"dropped: {feats.attrs['dropped_short']} below {q['min_samples']} samples, "
        f"{feats.attrs['dropped_long']} outside "
        f"[{q['min_duration_ms']}, {q['max_duration_ms']}] ms"
    )
    print(f"\n{path.name}: {len(feats):,} gestures x {feats.shape[1]} cols, "
          f"{path.stat().st_size / 2**20:.1f} MB")
    print(f"subjects: {feats.subject.nunique()}  activities: {feats.ActivityID.nunique()}")

    c = feats.groupby("subject").size()
    print(f"gestures/subject: median {c.median():.0f}  min {c.min()}  max {c.max()}")
    for k in (50, 100, 200, 300):
        print(f"  >={k:>3}: {(c >= k).sum()} subjects")

    nulls = feats.isna().mean().sort_values(ascending=False)
    hot = nulls[nulls > 0]
    print(f"\ncolumns with nulls: {len(hot)}")
    for name, frac in hot.head(8).items():
        print(f"  {name:<32} {frac:6.2%}")

    print(f"\ndone in {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Selectively extract HMOG interaction data into data/interim/hmog/.

Two passes. The first reads every Activity.csv straight out of the archives to learn which
session is which task; the second pulls interaction CSVs only for the sessions that matter.
This skips the three inertial streams, which are ~93% of the archive volume and unused here.

    python scripts/extract_hmog.py                 # reading sessions (per config)
    python scripts/extract_hmog.py --tasks all     # every task
    python scripts/extract_hmog.py --limit 3       # smoke test on 3 subjects
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

from precog.io.hmog import read_activity, read_member, scroll_gestures  # noqa: E402

INTERACTION_FILES = ["ScrollEvent.csv", "StrokeEvent.csv", "TouchEvent.csv"]


def build_manifest(zips: list[Path], task_map: dict) -> pd.DataFrame:
    rows = []
    for i, zp in enumerate(zips, 1):
        try:
            act = read_activity(zp)
        except Exception as exc:  # a corrupt archive should not kill the run
            print(f"  !! {zp.name}: {exc}")
            continue
        if act.empty:
            continue
        act["task"] = act["TaskID"].map(lambda t: task_map.get(int(t), ["unknown", "unknown"])[0])
        act["posture"] = act["TaskID"].map(lambda t: task_map.get(int(t), ["unknown", "unknown"])[1])
        act["zip"] = zp.name
        rows.append(act)
        print(f"  [{i:>3}/{len(zips)}] {zp.stem}  {len(act):>3} activities", flush=True)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(ROOT / "config" / "datasets.yaml"))
    ap.add_argument("--tasks", default=None, help="comma-separated, or 'all'")
    ap.add_argument("--limit", type=int, default=None, help="only N subjects (smoke test)")
    ap.add_argument("--out-dir", default=None, help="override config out_dir")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text())["hmog"]
    raw_dir = ROOT / cfg["raw_dir"]
    out_dir = ROOT / (args.out_dir or cfg["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    task_map = {int(k): v for k, v in cfg["task_map"].items()}

    if args.tasks == "all":
        wanted = None
    elif args.tasks:
        wanted = [t.strip() for t in args.tasks.split(",")]
    else:
        wanted = cfg.get("tasks")

    zips = sorted(raw_dir.glob("*.zip"))
    if args.limit:
        zips = zips[: args.limit]
    if not zips:
        print(f"No archives found in {raw_dir}")
        return 1

    t0 = time.time()
    print(f"== pass 1: indexing {len(zips)} subject archives ==")
    manifest = build_manifest(zips, task_map)
    if manifest.empty:
        print("No activities read — aborting.")
        return 1
    manifest.to_parquet(out_dir / "sessions.parquet", index=False)
    print(f"\nmanifest: {len(manifest)} activities, {manifest.SubjectID.nunique()} subjects")
    print(manifest.groupby(["task", "posture"]).size().to_string())

    keep = manifest if wanted is None else manifest[manifest["task"].isin(wanted)]
    keep_ids = set(keep["ActivityID"].astype("int64"))
    keep_sessions = {(r.zip, int(r.session)) for r in keep.itertuples()}
    print(f"\nselected: {len(keep)} activities across {len(keep_sessions)} sessions "
          f"(tasks={'all' if wanted is None else wanted})")

    print(f"\n== pass 2: extracting {INTERACTION_FILES} ==")
    buckets: dict[str, list[pd.DataFrame]] = {f: [] for f in INTERACTION_FILES}
    dropped_rows: dict[str, int] = {}
    for i, zp in enumerate(zips, 1):
        sessions = sorted({s for (z, s) in keep_sessions if z == zp.name})
        if not sessions:
            continue
        n = 0
        for sess in sessions:
            for fname in INTERACTION_FILES:
                member = f"{zp.stem}/{zp.stem}_session_{sess}/{fname}"
                try:
                    df = read_member(zp, member)
                except KeyError:
                    continue
                except Exception as exc:
                    print(f"  !! {member}: {exc}")
                    continue
                if df.empty:
                    continue
                # Some sessions (map navigation in particular) carry rows with a
                # non-finite ActivityID. They cannot be attributed to an activity, so
                # they are dropped and counted rather than coerced.
                aid = pd.to_numeric(df["ActivityID"], errors="coerce")
                bad = int(aid.isna().sum())
                if bad:
                    dropped_rows[fname] = dropped_rows.get(fname, 0) + bad
                df = df[aid.notna() & aid.fillna(-1).astype("int64").isin(keep_ids)]
                if df.empty:
                    continue
                df["subject"] = int(zp.stem)
                df["session"] = sess
                buckets[fname].append(df)
                n += len(df)
        print(f"  [{i:>3}/{len(zips)}] {zp.stem}  {len(sessions)} sessions  {n:>7} rows", flush=True)

    print("\n== writing ==")
    for fname, frames in buckets.items():
        if not frames:
            print(f"  {fname}: nothing extracted")
            continue
        df = pd.concat(frames, ignore_index=True)
        stem = fname.replace("Event.csv", "").lower()
        path = out_dir / f"hmog_{stem}-events_v1.parquet"
        df.to_parquet(path, index=False)
        print(f"  {path.name}: {len(df):,} rows, {path.stat().st_size / 2**20:.1f} MB")

        if fname == "ScrollEvent.csv":
            g = scroll_gestures(df)
            gp = out_dir / "hmog_scroll-gestures_v1.parquet"
            g.to_parquet(gp, index=False)
            print(f"  {gp.name}: {len(g):,} gestures, {gp.stat().st_size / 2**20:.1f} MB")

    print(f"\ndone in {time.time() - t0:.0f}s -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

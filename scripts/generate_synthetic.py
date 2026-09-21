"""Generate and persist the synthetic cohort to data/synthetic/.

Previously EXP-008/009/010 each regenerated this in memory. That was reproducible — the seed
is fixed — but wasteful, and it left data/synthetic/ empty in violation of CONVENTIONS.md.

Writes the base cohort plus both injected variants, and the per-user parameters needed to
re-inject at other magnitudes without regenerating.

    python scripts/generate_synthetic.py
    python scripts/generate_synthetic.py --magnitudes 0.5 1.0 1.5 2.0
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))

from precog.synthetic.generator import PopulationModel, enforce, generate, inject  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(ROOT / "config/synthetic.yaml"))
    ap.add_argument("--magnitudes", type=float, nargs="*", default=[1.5])
    ap.add_argument("--out-dir", default=str(ROOT / "data/synthetic"))
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text())
    rng = np.random.default_rng(cfg["seed"])
    version = cfg["synthetic_version"]
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    real = pd.read_parquet(ROOT / cfg["fit_from"])
    feats = [c for c in real.columns if c not in {
        "subject", "session", "t_start", "t_end", "feature_version", "phone_orientation"}]
    pop = PopulationModel(real, feats)
    print(f"population fitted from {cfg['fit_from']}")
    print(f"  {len(real):,} real gestures · {real.subject.nunique()} subjects · {len(feats)} features\n")

    base = generate(pop, cfg, rng)
    user_sigma, tau = base.attrs["user_sigma"], base.attrs["tau"]
    meta = base.attrs["meta"]

    def _clean(d: pd.DataFrame) -> pd.DataFrame:
        # pandas serialises df.attrs into parquet metadata as JSON; ours holds numpy
        # arrays, which are not JSON-serialisable. They are saved separately as .npz.
        d = d.copy()
        d.attrs = {}
        return d

    p = out / f"synthetic_gestures_{version}.parquet"
    _clean(enforce(base.copy(), cfg)).to_parquet(p, index=False)
    print(f"{p.name}: {len(base):,} gestures · {base.subject.nunique()} users · "
          f"{p.stat().st_size / 2**20:.1f} MB")

    # Per-user parameters, so other magnitudes can be injected without regenerating.
    np.savez_compressed(out / f"synthetic_params_{version}.npz",
                        user_sigma=user_sigma, tau=tau, features=np.array(feats, dtype=object))
    meta.to_csv(out / f"synthetic_users_{version}.csv", index=False)
    print(f"synthetic_params_{version}.npz · synthetic_users_{version}.csv")

    for kind in cfg["anomaly"]["types"]:
        for mag in args.magnitudes:
            inj = enforce(inject(base, pop, cfg, kind, mag), cfg)
            tag = kind.replace("_", "-")
            q = out / f"synthetic_{tag}-mag{mag}_{version}.parquet"
            _clean(inj).to_parquet(q, index=False)
            print(f"{q.name}: {len(inj):,} rows · positives {inj.y.mean():.1%} · "
                  f"{q.stat().st_size / 2**20:.1f} MB")

    (out / "MANIFEST.json").write_text(json.dumps({
        "synthetic_version": version,
        "seed": cfg["seed"],
        "fitted_from": cfg["fit_from"],
        "n_users": cfg["population"]["n_users"],
        "sessions_per_user": cfg["population"]["sessions_per_user"],
        "days_span": cfg["population"]["days_span"],
        "n_gestures": int(len(base)),
        "features": feats,
        "magnitudes": args.magnitudes,
        "anomaly_types": cfg["anomaly"]["types"],
        "note": "Synthetic. NOT evidence about people — a mechanism testbed with ground truth.",
    }, indent=2))
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

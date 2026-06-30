#!/usr/bin/env python3
"""Generate synthetic lunar water-ice benchmark instances."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.domain.scenario import SCALES
from lunar_ice_bpc.runners.generate_instances import generate_benchmark


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="data/instances")
    parser.add_argument("--manifest", default="data/manifests/lunar_ice_benchmark_manifest.json")
    parser.add_argument("--scales", default=",".join(str(item) for item in SCALES))
    parser.add_argument("--per-scale", type=int, default=20)
    parser.add_argument("--seed-base", type=int, default=629000)
    parser.add_argument("--max-attempts-per-instance", type=int, default=80)
    args = parser.parse_args()
    scales = [int(item.strip()) for item in args.scales.split(",") if item.strip()]
    manifest = generate_benchmark(
        output_root=ROOT / args.output_root,
        manifest_path=ROOT / args.manifest,
        project_root=ROOT,
        scales=scales,
        per_scale=args.per_scale,
        seed_base=args.seed_base,
        max_attempts_per_instance=args.max_attempts_per_instance,
    )
    print(
        f"wrote {manifest['accepted_total_count']}/{manifest['total_target_count']} accepted instances "
        f"status={manifest['status']} -> {ROOT / args.manifest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

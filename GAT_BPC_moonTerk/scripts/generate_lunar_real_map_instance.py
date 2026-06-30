#!/usr/bin/env python3
"""Generate one lunar-ice logical graph instance from local real-map rasters."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.domain.real_instance import generate_real_map_instance
from lunar_ice_bpc.io.instance_io import validate_instance, write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=int, default=5)
    parser.add_argument("--seed", type=int, default=629001)
    parser.add_argument("--index", type=int, default=1)
    parser.add_argument("--raw-map-dir", default="data/raw_maps")
    parser.add_argument("--output", default=None)
    parser.add_argument("--center-x-km", type=float, default=None)
    parser.add_argument("--center-y-km", type=float, default=None)
    parser.add_argument("--extent-km", type=float, default=None)
    parser.add_argument("--cells", type=int, default=None)
    parser.add_argument("--time-window-mode", choices=("outer_to_inner", "inner_to_outer", "easy_to_hard"), default=None)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    raw_map_dir = _project_path(args.raw_map_dir)
    output = _project_path(args.output) if args.output else _project_path(
        f"data/instances/lunar_ice_sp50_{args.scale:03d}/instance_{args.index:03d}_logical_graph.json"
    )
    instance = generate_real_map_instance(
        int(args.scale),
        raw_map_dir=raw_map_dir,
        seed=int(args.seed),
        index=int(args.index),
        center_x_km=args.center_x_km,
        center_y_km=args.center_y_km,
        extent_km=args.extent_km,
        output_cells=args.cells,
        time_window_mode=args.time_window_mode,
    )
    write_json(output, instance)
    issues = validate_instance(instance)
    print(f"wrote {output}")
    print(f"validation_reason: {(instance.get('validation') or {}).get('reason')}")
    print(f"schema_issues: {len(issues)}")
    if issues:
        for issue in issues[:10]:
            print(f"- {issue}")
    if args.strict and (issues or not (instance.get("validation") or {}).get("accepted")):
        return 2
    return 0


def _project_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path


if __name__ == "__main__":
    raise SystemExit(main())

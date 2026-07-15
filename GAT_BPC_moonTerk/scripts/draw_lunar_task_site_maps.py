#!/usr/bin/env python3
"""Draw comparable 20-task and 50-task lunar south-pole site maps."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.domain.scientific_visualization import draw_task_site_map


DEFAULT_INSTANCES = (
    "data/instances/lunar_ice_sp50_020/instance_001_logical_graph.json",
    "data/instances/lunar_ice_sp50_050/instance_001_logical_graph.json",
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Draw task sites and the depot without logical-edge or route overlays."
    )
    parser.add_argument("--instances", nargs="+", default=DEFAULT_INSTANCES)
    parser.add_argument(
        "--preview-json",
        default="data/processed/real_maps/south_pole_sp50_preview.json",
    )
    parser.add_argument("--output-dir", default="runs/figures/task_sites")
    parser.add_argument("--label-tasks", action="store_true")
    args = parser.parse_args()

    preview_path = _project_path(args.preview_json)
    output_dir = _project_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for value in args.instances:
        instance_path = _project_path(value)
        instance_number = instance_path.stem.removesuffix("_logical_graph")
        output = output_dir / f"{instance_path.parent.name}_{instance_number}_task_sites.png"
        draw_task_site_map(
            instance_path,
            output,
            preview_path=preview_path,
            label_tasks=args.label_tasks,
        )
        print(f"wrote {output}")
        print(f"wrote {output.with_suffix('.pdf')}")
    return 0


def _project_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())

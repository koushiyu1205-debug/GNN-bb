#!/usr/bin/env python3
"""Draw BPC_future-style PNG/PDF graph figures for one lunar-ice instance."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.domain.scientific_visualization import draw_logical_task_graph, draw_path_option_overlay


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--solution", default=None)
    parser.add_argument("--preview-json", default=None)
    parser.add_argument("--output-dir", default="runs/figures")
    args = parser.parse_args()

    instance_path = _project_path(args.instance)
    solution_path = _project_path(args.solution) if args.solution else None
    preview_path = _project_path(args.preview_json) if args.preview_json else None
    output_dir = _project_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = instance_path.stem
    logical = output_dir / f"{prefix}_logical_task_graph.png"
    overlay = output_dir / f"{prefix}_path_option_overlay.png"
    draw_logical_task_graph(instance_path, logical, preview_path=preview_path)
    draw_path_option_overlay(instance_path, overlay, solution_path=solution_path, preview_path=preview_path)
    print(f"wrote {logical}")
    print(f"wrote {logical.with_suffix('.pdf')}")
    print(f"wrote {overlay}")
    print(f"wrote {overlay.with_suffix('.pdf')}")
    return 0


def _project_path(value: str | None) -> Path:
    if value is None:
        raise ValueError("path value is required")
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build physical-grid and logical-task graph artifacts for a Moon Trek patch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from BPC_future.preprocess.terrain_graph import (  # noqa: E402
    TerrainGraphConfig,
    build_logical_graph_payload,
    draw_logical_task_graph,
    draw_path_option_overlay,
    draw_physical_grid_graph,
    write_logical_graph,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build physical and logical terrain graph artifacts.")
    parser.add_argument("--terrain-dir", required=True)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--output-dir", default="BPC_future/draw/graphs")
    parser.add_argument("--grid-size", type=int, default=256)
    parser.add_argument("--min-valid-fraction", type=float, default=0.60)
    parser.add_argument("--max-impassable-fraction", type=float, default=0.40)
    parser.add_argument("--risk-weight", type=float, default=2.0)
    parser.add_argument("--slope-weight", type=float, default=1.5)
    parser.add_argument("--uphill-weight", type=float, default=3.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    terrain_dir = Path(args.terrain_dir)
    prefix = terrain_dir.name
    out = Path(args.output_dir) / prefix
    out.mkdir(parents=True, exist_ok=True)
    config = TerrainGraphConfig(
        grid_size=int(args.grid_size),
        min_valid_fraction=float(args.min_valid_fraction),
        max_impassable_fraction=float(args.max_impassable_fraction),
        risk_weight=float(args.risk_weight),
        slope_weight=float(args.slope_weight),
        uphill_weight=float(args.uphill_weight),
    )
    payload = build_logical_graph_payload(terrain_dir, args.scenario, config=config)
    json_path = out / f"{prefix}_logical_graph.json"
    physical_png = out / f"{prefix}_physical_grid_graph.png"
    logical_png = out / f"{prefix}_logical_task_graph.png"
    overlay_png = out / f"{prefix}_path_option_overlay.png"
    write_logical_graph(json_path, payload)
    draw_physical_grid_graph(payload, physical_png)
    draw_logical_task_graph(payload, logical_png)
    draw_path_option_overlay(payload, overlay_png)
    summary = {
        "logical_graph": str(json_path),
        "physical_grid_graph_png": str(physical_png),
        "logical_task_graph_png": str(logical_png),
        "path_option_overlay_png": str(overlay_png),
        "physical_graph": payload["physical_graph"],
        "logical_summary": {
            key: payload["logical_graph"][key]
            for key in ("node_count", "directed_edge_count", "feasible_directed_edge_count")
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

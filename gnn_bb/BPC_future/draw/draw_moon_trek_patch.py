#!/usr/bin/env python3
"""Render Moon Trek terrain/risk figures and a sampled task scenario."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from BPC_future.draw.moon_trek_viz import (  # noqa: E402
    ScenarioConfig,
    draw_operational_scenario,
    draw_terrain_atlas,
    load_terrain_grid,
    sample_operational_scenario,
    write_scenario,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Draw scientific Moon Trek terrain/risk figures.")
    parser.add_argument("--terrain-dir", default="BPC_future/data/moon_trek/apollo15_20km")
    parser.add_argument("--output-dir", default="BPC_future/draw/figures")
    parser.add_argument("--scenario-dir", default="BPC_future/draw/scenarios")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--task-count", type=int, default=20)
    parser.add_argument("--operation-radius-km", type=float, default=10.0)
    parser.add_argument("--depot-x-km", type=float, default=10.0)
    parser.add_argument("--depot-y-km", type=float, default=10.0)
    parser.add_argument("--vehicle-max-roundtrip-km", type=float, default=30.0)
    parser.add_argument("--max-task-risk", type=float, default=0.90)
    parser.add_argument("--min-point-spacing-km", type=float, default=0.35)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    grid = load_terrain_grid(args.terrain_dir)
    output_dir = Path(args.output_dir)
    scenario_dir = Path(args.scenario_dir)
    if args.output_dir == "BPC_future/draw/figures":
        output_dir = output_dir / grid.source_dir.name
    if args.scenario_dir == "BPC_future/draw/scenarios":
        scenario_dir = scenario_dir / grid.source_dir.name
    figure_paths = draw_terrain_atlas(grid, output_dir)
    config = ScenarioConfig(
        seed=int(args.seed),
        task_count=int(args.task_count),
        operation_radius_km=float(args.operation_radius_km),
        depot_xy_km=(float(args.depot_x_km), float(args.depot_y_km)),
        vehicle_max_roundtrip_km=float(args.vehicle_max_roundtrip_km),
        max_task_risk=float(args.max_task_risk),
        min_point_spacing_km=float(args.min_point_spacing_km),
    )
    scenario = sample_operational_scenario(grid, config)
    scenario_path = scenario_dir / f"{grid.source_dir.name}_region_seed{args.seed}_tasks{args.task_count}.json"
    write_scenario(scenario_path, scenario)
    scenario_paths = draw_operational_scenario(grid, scenario, output_dir)
    payload = {
        "figures": {**figure_paths, **scenario_paths},
        "scenario": str(scenario_path),
        "vehicle": scenario["vehicle"],
        "operation_region": scenario["operation_region"],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

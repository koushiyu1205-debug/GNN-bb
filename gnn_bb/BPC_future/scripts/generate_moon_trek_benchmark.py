#!/usr/bin/env python3
"""Generate deterministic Moon Trek scenario and logical-graph batches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

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
from BPC_future.preprocess.terrain_graph import (  # noqa: E402
    TerrainGraphConfig,
    build_coarse_terrain_graph,
    build_logical_graph_payload_from_graph,
    draw_logical_task_graph,
    draw_path_option_overlay,
    draw_physical_grid_graph,
    write_logical_graph,
)
from BPC_future.preprocess.scheduling_augmentation import (  # noqa: E402
    SchedulingAugmentationConfig,
    augment_logical_graph_for_multisortie_cvrptw,
    augment_scenario_for_multisortie_cvrptw,
)


DEFAULT_TERRAINS = (
    "BPC_future/data/moon_trek/apollo15_20km",
    "BPC_future/data/moon_trek/tranquillitatis_balmer_like_20km",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Moon Trek BPC_future benchmark instances.")
    parser.add_argument("--terrain-dir", action="append", default=None, help="Terrain directory. Repeatable.")
    parser.add_argument("--task-counts", default="5,10,20", help="Comma-separated task counts.")
    parser.add_argument("--instances-per-size", type=int, default=10)
    parser.add_argument("--seed-start", type=int, default=1000)
    parser.add_argument("--output-root", default="BPC_future/data/generated/moon_trek_60")
    parser.add_argument("--figure-root", default="BPC_future/draw/moon_trek_60")
    parser.add_argument("--grid-size", type=int, default=256)
    parser.add_argument("--operation-radius-km", type=float, default=10.0)
    parser.add_argument("--depot-x-km", type=float, default=10.0)
    parser.add_argument("--depot-y-km", type=float, default=10.0)
    parser.add_argument("--vehicle-max-roundtrip-km", type=float, default=30.0)
    parser.add_argument(
        "--vehicle-max-roundtrip-energy-proxy",
        type=float,
        default=70.0,
        help="Maximum depot-task-depot energy proxy after physical shortest-path construction.",
    )
    parser.add_argument("--max-task-risk", type=float, default=0.90)
    parser.add_argument("--min-point-spacing-km", type=float, default=3.0)
    parser.add_argument("--max-seed-attempts", type=int, default=200)
    parser.add_argument("--draw-one-per-size", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--horizon-min", type=float, default=720.0)
    parser.add_argument("--usable-battery-capacity-proxy", type=float, default=80.0)
    parser.add_argument("--recharge-power-proxy-per-min", type=float, default=2.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    terrain_dirs = tuple(args.terrain_dir or DEFAULT_TERRAINS)
    task_counts = tuple(int(part.strip()) for part in args.task_counts.split(",") if part.strip())
    output_root = Path(args.output_root)
    figure_root = Path(args.figure_root)
    graph_config = TerrainGraphConfig(grid_size=int(args.grid_size))
    scheduling_config = SchedulingAugmentationConfig(
        horizon_min=float(args.horizon_min),
        usable_battery_capacity_proxy=float(args.usable_battery_capacity_proxy),
        recharge_power_proxy_per_min=float(args.recharge_power_proxy_per_min),
    )
    manifest: dict[str, Any] = {
        "output_root": str(output_root),
        "figure_root": str(figure_root),
        "terrain_dirs": list(terrain_dirs),
        "task_counts": list(task_counts),
        "instances_per_size": int(args.instances_per_size),
        "scenario_config": {
            "operation_radius_km": float(args.operation_radius_km),
            "depot_xy_km": [float(args.depot_x_km), float(args.depot_y_km)],
            "vehicle_max_roundtrip_km": float(args.vehicle_max_roundtrip_km),
            "vehicle_max_roundtrip_energy_proxy": float(args.vehicle_max_roundtrip_energy_proxy),
            "max_task_risk": float(args.max_task_risk),
            "min_point_spacing_km": float(args.min_point_spacing_km),
        },
        "graph_config": graph_config.__dict__,
        "scheduling_augmentation": scheduling_config.__dict__,
        "instances": [],
    }

    for terrain_dir in terrain_dirs:
        terrain_path = Path(terrain_dir)
        grid = load_terrain_grid(terrain_path)
        graph = build_coarse_terrain_graph(grid, graph_config)
        terrain_name = grid.source_dir.name
        terrain_figure_dir = figure_root / terrain_name / "terrain"
        draw_terrain_atlas(grid, terrain_figure_dir)
        for task_count in task_counts:
            accepted = 0
            attempt = 0
            while accepted < int(args.instances_per_size):
                if attempt >= int(args.max_seed_attempts):
                    raise RuntimeError(
                        f"failed to generate {args.instances_per_size} reachable instances for "
                        f"{terrain_name} tasks={task_count} after {attempt} attempts"
                    )
                seed = int(args.seed_start) + task_count * 1000 + accepted * 17 + attempt
                attempt += 1
                scenario_config = ScenarioConfig(
                    seed=seed,
                    task_count=int(task_count),
                    operation_radius_km=float(args.operation_radius_km),
                    depot_xy_km=(float(args.depot_x_km), float(args.depot_y_km)),
                    vehicle_max_roundtrip_km=float(args.vehicle_max_roundtrip_km),
                    max_task_risk=float(args.max_task_risk),
                    min_point_spacing_km=float(args.min_point_spacing_km),
                )
                try:
                    scenario = sample_operational_scenario(grid, scenario_config)
                except RuntimeError as exc:
                    _log_skip(terrain_name, task_count, seed, exc)
                    continue
                scenario["vehicle"]["max_roundtrip_energy_proxy"] = float(args.vehicle_max_roundtrip_energy_proxy)
                scenario["vehicle"][
                    "final_feasibility_note"
                ] = "Euclidean range only screens candidates; physical path distance and energy proxy are checked after logical graph construction."

                instance_id = f"{terrain_name}_tasks{task_count:02d}_{accepted + 1:02d}_seed{seed}"
                scenario_dir = output_root / "scenarios" / terrain_name / f"tasks_{task_count:02d}"
                graph_dir = output_root / "logical_graphs" / terrain_name / f"tasks_{task_count:02d}"
                scenario_path = scenario_dir / f"{instance_id}.json"
                write_scenario(scenario_path, scenario)
                payload = build_logical_graph_payload_from_graph(
                    graph,
                    scenario,
                    scenario_path=scenario_path,
                    source_shape=grid.shape,
                )
                if not _all_pairs_reachable(payload):
                    _log_skip(terrain_name, task_count, seed, RuntimeError("logical graph has unreachable pair"))
                    scenario_path.unlink(missing_ok=True)
                    continue
                roundtrip_report = _roundtrip_feasibility_report(
                    payload,
                    max_distance=float(args.vehicle_max_roundtrip_km),
                    max_energy=float(args.vehicle_max_roundtrip_energy_proxy),
                )
                if not roundtrip_report["all_tasks_roundtrip_feasible"]:
                    _log_skip(
                        terrain_name,
                        task_count,
                        seed,
                        RuntimeError(
                            "depot-task-depot physical roundtrip infeasible for "
                            f"{len(roundtrip_report['violations'])} tasks"
                        ),
                    )
                    scenario_path.unlink(missing_ok=True)
                    continue

                graph_path = graph_dir / f"{instance_id}_logical_graph.json"
                payload["scenario"]["vehicle"]["physical_roundtrip_check"] = roundtrip_report
                scenario["vehicle"]["physical_roundtrip_check"] = roundtrip_report
                scenario = augment_scenario_for_multisortie_cvrptw(scenario, config=scheduling_config)
                payload = augment_logical_graph_for_multisortie_cvrptw(payload, scenario, config=scheduling_config)
                write_scenario(scenario_path, scenario)
                write_logical_graph(graph_path, payload)
                figures: dict[str, str] = {}
                if args.draw_one_per_size and accepted == 0:
                    figure_dir = figure_root / terrain_name / f"tasks_{task_count:02d}" / instance_id
                    figures.update(draw_operational_scenario(grid, scenario, figure_dir))
                    physical_png = figure_dir / f"{instance_id}_physical_grid_graph.png"
                    logical_png = figure_dir / f"{instance_id}_logical_task_graph.png"
                    overlay_png = figure_dir / f"{instance_id}_path_option_overlay.png"
                    draw_physical_grid_graph(payload, physical_png)
                    draw_logical_task_graph(payload, logical_png)
                    draw_path_option_overlay(payload, overlay_png)
                    figures.update(
                        {
                            "physical_grid_graph_png": str(physical_png),
                            "logical_task_graph_png": str(logical_png),
                            "path_option_overlay_png": str(overlay_png),
                        }
                    )

                entry = {
                    "instance_id": instance_id,
                    "terrain": terrain_name,
                    "task_count": int(task_count),
                    "sample_index": accepted + 1,
                    "seed": seed,
                    "scenario": str(scenario_path),
                    "logical_graph": str(graph_path),
                    "figures": figures,
                    "logical_summary": {
                        key: payload["logical_graph"][key]
                        for key in ("node_count", "directed_edge_count", "feasible_directed_edge_count")
                    },
                    "physical_roundtrip_check": roundtrip_report,
                    "vehicle": scenario["vehicle"],
                    "scheduling": scenario["scheduling"],
                }
                manifest["instances"].append(entry)
                accepted += 1
                print(json.dumps({"event": "accepted", **entry}, sort_keys=True))

    manifest_path = output_root / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"event": "finish", "manifest": str(manifest_path), "instances": len(manifest["instances"])}, indent=2))


def _all_pairs_reachable(payload: dict[str, Any]) -> bool:
    logical = payload["logical_graph"]
    return logical["directed_edge_count"] == logical["feasible_directed_edge_count"]


def _roundtrip_feasibility_report(
    payload: dict[str, Any],
    *,
    max_distance: float,
    max_energy: float,
) -> dict[str, Any]:
    edges = {
        (edge["from"], edge["to"]): edge
        for edge in payload["logical_graph"]["edges"]
        if edge.get("feasible")
    }
    task_ids = [node["id"] for node in payload["logical_graph"]["nodes"] if node["id"] != "depot"]
    violations: list[dict[str, Any]] = []
    max_min_energy_distance = 0.0
    max_min_energy = 0.0
    max_feasible_distance = 0.0
    max_feasible_energy = 0.0
    for task_id in task_ids:
        out_edge = edges.get(("depot", task_id))
        return_edge = edges.get((task_id, "depot"))
        if out_edge is None or return_edge is None:
            violations.append({"task": task_id, "reason": "missing depot roundtrip edge"})
            continue
        best_pair: dict[str, Any] | None = None
        best_feasible_pair: dict[str, Any] | None = None
        for out_option in out_edge.get("path_options", []):
            for return_option in return_edge.get("path_options", []):
                distance = float(out_option["path_distance_km"]) + float(return_option["path_distance_km"])
                energy = float(out_option["energy_proxy"]) + float(return_option["energy_proxy"])
                pair = {
                    "out_path_type": out_option["path_type"],
                    "return_path_type": return_option["path_type"],
                    "roundtrip_path_distance_km": round(distance, 6),
                    "roundtrip_energy_proxy": round(energy, 6),
                }
                if best_pair is None or (energy, distance) < (
                    best_pair["roundtrip_energy_proxy"],
                    best_pair["roundtrip_path_distance_km"],
                ):
                    best_pair = pair
                if distance <= max_distance + 1.0e-9 and energy <= max_energy + 1.0e-9:
                    if best_feasible_pair is None or (energy, distance) < (
                        best_feasible_pair["roundtrip_energy_proxy"],
                        best_feasible_pair["roundtrip_path_distance_km"],
                    ):
                        best_feasible_pair = pair
        if best_pair is not None:
            max_min_energy_distance = max(max_min_energy_distance, float(best_pair["roundtrip_path_distance_km"]))
            max_min_energy = max(max_min_energy, float(best_pair["roundtrip_energy_proxy"]))
        if best_feasible_pair is None:
            violations.append(
                {
                    "task": task_id,
                    "reason": "no depot-task-depot option pair satisfies distance and energy budgets",
                    "best_energy_pair": best_pair,
                }
            )
        else:
            max_feasible_distance = max(max_feasible_distance, float(best_feasible_pair["roundtrip_path_distance_km"]))
            max_feasible_energy = max(max_feasible_energy, float(best_feasible_pair["roundtrip_energy_proxy"]))
    return {
        "max_roundtrip_path_distance_km": float(max_distance),
        "max_roundtrip_energy_proxy": float(max_energy),
        "task_count": len(task_ids),
        "all_tasks_roundtrip_feasible": not violations,
        "violation_count": len(violations),
        "violations": violations,
        "max_selected_feasible_pair_distance_km": round(max_feasible_distance, 6),
        "max_selected_feasible_pair_energy_proxy": round(max_feasible_energy, 6),
        "max_min_energy_pair_distance_km": round(max_min_energy_distance, 6),
        "max_min_energy_pair_energy_proxy": round(max_min_energy, 6),
    }


def _log_skip(terrain_name: str, task_count: int, seed: int, exc: Exception) -> None:
    print(
        json.dumps(
            {
                "event": "skip",
                "terrain": terrain_name,
                "task_count": int(task_count),
                "seed": int(seed),
                "reason": str(exc),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

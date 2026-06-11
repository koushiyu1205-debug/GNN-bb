#!/usr/bin/env python3
"""Generate Moon Trek instances with balanced time-window and energy tightness.

This generator is intentionally separate from generate_moon_trek_benchmark.py.
It writes a new dataset root and leaves the existing moon_trek_60 instances
untouched.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from itertools import combinations, permutations
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable

import numpy as np

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
from BPC_future.preprocess.scheduling_augmentation import (  # noqa: E402
    SchedulingAugmentationConfig,
    augment_logical_graph_for_multisortie_cvrptw,
    augment_scenario_for_multisortie_cvrptw,
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


DEFAULT_TERRAINS = (
    "BPC_future/data/moon_trek/apollo15_20km",
    "BPC_future/data/moon_trek/tranquillitatis_balmer_like_20km",
)


@dataclass(frozen=True)
class DensityBand:
    low: float
    high: float

    def contains(self, value: float) -> bool:
        return self.low <= float(value) <= self.high


@dataclass(frozen=True)
class TightnessProfile:
    window_base_min: float
    window_jitter_fraction: float
    ready_jitter_min: float
    energy_margin_candidates: tuple[float, ...]
    energy_pair: DensityBand
    energy_triple: DensityBand
    energy_quad: DensityBand
    energy_large: DensityBand
    time_pair: DensityBand
    time_triple: DensityBand


PROFILES: dict[int, TightnessProfile] = {
    5: TightnessProfile(
        window_base_min=220.0,
        window_jitter_fraction=0.20,
        ready_jitter_min=25.0,
        energy_margin_candidates=(1.10, 1.15, 1.20, 1.28, 1.36, 1.48, 1.60, 1.80),
        energy_pair=DensityBand(0.45, 0.95),
        energy_triple=DensityBand(0.15, 0.80),
        energy_quad=DensityBand(0.00, 0.65),
        energy_large=DensityBand(0.00, 0.45),
        time_pair=DensityBand(0.45, 1.00),
        time_triple=DensityBand(0.12, 0.85),
    ),
    10: TightnessProfile(
        window_base_min=165.0,
        window_jitter_fraction=0.18,
        ready_jitter_min=42.0,
        energy_margin_candidates=(1.08, 1.12, 1.16, 1.22, 1.30, 1.40, 1.55, 1.75),
        energy_pair=DensityBand(0.35, 0.90),
        energy_triple=DensityBand(0.08, 0.65),
        energy_quad=DensityBand(0.00, 0.40),
        energy_large=DensityBand(0.00, 0.25),
        time_pair=DensityBand(0.30, 0.90),
        time_triple=DensityBand(0.06, 0.55),
    ),
    20: TightnessProfile(
        window_base_min=130.0,
        window_jitter_fraction=0.22,
        ready_jitter_min=42.0,
        energy_margin_candidates=(1.05, 1.08, 1.12, 1.16, 1.22, 1.30, 1.42, 1.58),
        energy_pair=DensityBand(0.25, 0.85),
        energy_triple=DensityBand(0.04, 0.50),
        energy_quad=DensityBand(0.00, 0.28),
        energy_large=DensityBand(0.00, 0.14),
        time_pair=DensityBand(0.20, 0.80),
        time_triple=DensityBand(0.03, 0.40),
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate balanced Moon Trek BPC_future benchmark instances.")
    parser.add_argument("--terrain-dir", action="append", default=None, help="Terrain directory. Repeatable.")
    parser.add_argument("--task-counts", default="5,10,20", help="Comma-separated task counts.")
    parser.add_argument(
        "--instances-per-terrain-size",
        type=int,
        default=10,
        help="Instances per terrain and task count. With the two default terrains this gives 20 per size.",
    )
    parser.add_argument("--seed-start", type=int, default=31000)
    parser.add_argument("--output-root", default="BPC_future/data/generated/moon_trek_balanced_60")
    parser.add_argument("--figure-root", default="BPC_future/draw/moon_trek_balanced_60")
    parser.add_argument("--grid-size", type=int, default=256)
    parser.add_argument("--operation-radius-km", type=float, default=10.0)
    parser.add_argument("--depot-x-km", type=float, default=10.0)
    parser.add_argument("--depot-y-km", type=float, default=10.0)
    parser.add_argument("--vehicle-max-roundtrip-km", type=float, default=30.0)
    parser.add_argument("--vehicle-max-roundtrip-energy-proxy", type=float, default=70.0)
    parser.add_argument("--usable-battery-capacity-proxy", type=float, default=80.0)
    parser.add_argument("--survival-energy-reserve-proxy", type=float, default=10.0)
    parser.add_argument("--recharge-power-proxy-per-min", type=float, default=2.0)
    parser.add_argument("--max-task-risk", type=float, default=0.90)
    parser.add_argument("--min-point-spacing-km", type=float, default=3.0)
    parser.add_argument("--max-seed-attempts", type=int, default=500)
    parser.add_argument("--horizon-min", type=float, default=720.0)
    parser.add_argument("--draw-one-per-size", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--draw-terrain-atlas", action=argparse.BooleanOptionalAction, default=False)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    terrain_dirs = tuple(args.terrain_dir or DEFAULT_TERRAINS)
    task_counts = tuple(int(part.strip()) for part in str(args.task_counts).split(",") if part.strip())
    unsupported = sorted(set(task_counts) - set(PROFILES))
    if unsupported:
        raise ValueError(f"balanced profiles are defined only for task counts {sorted(PROFILES)}; got {unsupported}")

    output_root = Path(args.output_root)
    figure_root = Path(args.figure_root)
    graph_config = TerrainGraphConfig(grid_size=int(args.grid_size))
    base_scheduling_config = SchedulingAugmentationConfig(
        horizon_min=float(args.horizon_min),
        usable_battery_capacity_proxy=float(args.usable_battery_capacity_proxy),
        survival_energy_reserve_proxy=float(args.survival_energy_reserve_proxy),
        max_roundtrip_energy_proxy=float(args.vehicle_max_roundtrip_energy_proxy),
        recharge_power_proxy_per_min=float(args.recharge_power_proxy_per_min),
    )
    manifest: dict[str, Any] = {
        "output_root": str(output_root),
        "figure_root": str(figure_root),
        "terrain_dirs": list(terrain_dirs),
        "task_counts": list(task_counts),
        "instances_per_terrain_size": int(args.instances_per_terrain_size),
        "instances_per_size_total": int(args.instances_per_terrain_size) * len(terrain_dirs),
        "scenario_config": {
            "operation_radius_km": float(args.operation_radius_km),
            "depot_xy_km": [float(args.depot_x_km), float(args.depot_y_km)],
            "vehicle_max_roundtrip_km": float(args.vehicle_max_roundtrip_km),
            "vehicle_max_roundtrip_energy_proxy_upper": float(args.vehicle_max_roundtrip_energy_proxy),
            "max_task_risk": float(args.max_task_risk),
            "min_point_spacing_km": float(args.min_point_spacing_km),
        },
        "graph_config": graph_config.__dict__,
        "base_scheduling_augmentation": asdict(base_scheduling_config),
        "balanced_profiles": {str(key): _profile_payload(value) for key, value in PROFILES.items()},
        "instances": [],
    }

    for terrain_index, terrain_dir in enumerate(terrain_dirs):
        terrain_path = Path(terrain_dir)
        grid = load_terrain_grid(terrain_path)
        graph = build_coarse_terrain_graph(grid, graph_config)
        terrain_name = grid.source_dir.name
        if args.draw_terrain_atlas:
            draw_terrain_atlas(grid, figure_root / terrain_name / "terrain")

        for task_count in task_counts:
            accepted = 0
            attempt = 0
            while accepted < int(args.instances_per_terrain_size):
                if attempt >= int(args.max_seed_attempts):
                    raise RuntimeError(
                        f"failed to generate {args.instances_per_terrain_size} balanced instances for "
                        f"{terrain_name} tasks={task_count} after {attempt} attempts"
                    )
                seed = int(args.seed_start) + terrain_index * 100000 + task_count * 1000 + accepted * 101 + attempt
                attempt += 1
                instance_id = f"{terrain_name}_balanced_tasks{task_count:02d}_{accepted + 1:02d}_seed{seed}"
                scenario_dir = output_root / "scenarios" / terrain_name / f"tasks_{task_count:02d}"
                graph_dir = output_root / "logical_graphs" / terrain_name / f"tasks_{task_count:02d}"
                scenario_path = scenario_dir / f"{instance_id}.json"
                graph_path = graph_dir / f"{instance_id}_logical_graph.json"

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
                    scenario["id"] = instance_id
                    scenario["instance_id"] = instance_id
                    scenario["vehicle"]["max_roundtrip_energy_proxy"] = float(args.vehicle_max_roundtrip_energy_proxy)
                    scenario["vehicle"][
                        "final_feasibility_note"
                    ] = "Balanced generator screens final energy and time-window route-set density after physical paths."
                    payload = build_logical_graph_payload_from_graph(
                        graph,
                        scenario,
                        scenario_path=scenario_path,
                        source_shape=grid.shape,
                    )
                    if not _all_pairs_reachable(payload):
                        raise RuntimeError("logical graph has unreachable pair")
                    balanced = _build_balanced_instance(
                        scenario,
                        payload,
                        task_count=int(task_count),
                        seed=int(seed),
                        scenario_path=scenario_path,
                        base_config=base_scheduling_config,
                        energy_cap_upper=float(args.vehicle_max_roundtrip_energy_proxy),
                    )
                except RuntimeError as exc:
                    _log_skip(terrain_name, task_count, seed, exc)
                    continue

                final_scenario, final_payload, audit, roundtrip_report = balanced
                figures: dict[str, str] = {}
                if args.draw_one_per_size and accepted == 0:
                    figure_dir = figure_root / terrain_name / f"tasks_{task_count:02d}" / instance_id
                    figures.update(draw_operational_scenario(grid, final_scenario, figure_dir))
                    physical_png = figure_dir / f"{instance_id}_physical_grid_graph.png"
                    logical_png = figure_dir / f"{instance_id}_logical_task_graph.png"
                    overlay_png = figure_dir / f"{instance_id}_path_option_overlay.png"
                    draw_physical_grid_graph(final_payload, physical_png)
                    draw_logical_task_graph(final_payload, logical_png)
                    draw_path_option_overlay(final_payload, overlay_png)
                    figures.update(
                        {
                            "physical_grid_graph_png": str(physical_png),
                            "logical_task_graph_png": str(logical_png),
                            "path_option_overlay_png": str(overlay_png),
                        }
                    )

                write_scenario(scenario_path, final_scenario)
                write_logical_graph(graph_path, final_payload)
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
                        key: final_payload["logical_graph"][key]
                        for key in ("node_count", "directed_edge_count", "feasible_directed_edge_count")
                    },
                    "physical_roundtrip_check": roundtrip_report,
                    "vehicle": final_scenario["vehicle"],
                    "scheduling": final_scenario["scheduling"],
                    "balanced_audit": audit,
                }
                manifest["instances"].append(entry)
                accepted += 1
                print(json.dumps({"event": "accepted", **entry}, sort_keys=True))

    manifest_path = output_root / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"event": "finish", "manifest": str(manifest_path), "instances": len(manifest["instances"])}, indent=2))


def _profile_payload(profile: TightnessProfile) -> dict[str, Any]:
    return {
        "window_base_min": profile.window_base_min,
        "window_jitter_fraction": profile.window_jitter_fraction,
        "ready_jitter_min": profile.ready_jitter_min,
        "energy_margin_candidates": list(profile.energy_margin_candidates),
        "energy_pair": asdict(profile.energy_pair),
        "energy_triple": asdict(profile.energy_triple),
        "energy_quad": asdict(profile.energy_quad),
        "energy_large": asdict(profile.energy_large),
        "time_pair": asdict(profile.time_pair),
        "time_triple": asdict(profile.time_triple),
    }


def _build_balanced_instance(
    scenario: dict[str, Any],
    payload: dict[str, Any],
    *,
    task_count: int,
    seed: int,
    scenario_path: Path,
    base_config: SchedulingAugmentationConfig,
    energy_cap_upper: float,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    profile = PROFILES[int(task_count)]
    preliminary = augment_scenario_for_multisortie_cvrptw(scenario, config=base_config)
    matrices = _metric_matrices(payload, preliminary)
    energy_candidates = _subset_min_closed_energy(matrices, max_size=min(6, int(task_count)))
    energy_cap, energy_audit = _choose_energy_cap(
        matrices,
        energy_candidates,
        profile=profile,
        task_count=int(task_count),
        energy_cap_upper=float(energy_cap_upper),
    )
    if energy_cap is None:
        raise RuntimeError(f"no balanced energy cap found: {energy_audit}")

    config = SchedulingAugmentationConfig(
        **{
            **asdict(base_config),
            "max_roundtrip_energy_proxy": float(energy_cap),
        }
    )
    scheduled = augment_scenario_for_multisortie_cvrptw(scenario, config=config)
    _apply_balanced_time_windows(scheduled, matrices, profile=profile, seed=seed)
    time_audit = _time_window_audit(scheduled, matrices, task_count=int(task_count))
    if not profile.time_pair.contains(time_audit["time_pair_feasible_ratio"]):
        raise RuntimeError(f"time pair density out of band: {time_audit}")
    if task_count >= 3 and not profile.time_triple.contains(time_audit["time_triple_feasible_ratio"]):
        raise RuntimeError(f"time triple density out of band: {time_audit}")
    if not time_audit["single_task_timed_feasible"]:
        raise RuntimeError(f"single task timed feasibility failed: {time_audit}")

    scheduled["vehicle"]["max_roundtrip_energy_proxy"] = float(energy_cap)
    scheduled["vehicle"]["sortie_energy_capacity_proxy"] = float(energy_cap)
    scheduled["vehicle"]["B_use"] = float(energy_cap)
    scheduled["vehicle"]["balanced_energy_cap_policy"] = {
        "type": "instance_specific_cap_selected_by_route_set_density",
        "upper_cap": float(energy_cap_upper),
        "selected_cap": float(energy_cap),
    }
    scheduled["scheduling"]["balanced_time_window_policy"] = {
        "type": "canonical_task_index_template_shared_by_task_count",
        "profile": _profile_payload(profile),
        "template": {
            str(task_id): list(window)
            for task_id, window in _canonical_time_window_template(
                int(task_count),
                horizon=float(config.horizon_min),
                profile=profile,
            ).items()
        },
    }

    roundtrip_report = _roundtrip_feasibility_report(payload, max_distance=float(scheduled["vehicle"]["max_roundtrip_km"]), max_energy=float(energy_cap))
    if not roundtrip_report["all_tasks_roundtrip_feasible"]:
        raise RuntimeError(f"single task roundtrip infeasible after cap selection: {roundtrip_report}")
    scheduled["vehicle"]["physical_roundtrip_check"] = roundtrip_report

    final_payload = augment_logical_graph_for_multisortie_cvrptw(payload, scheduled, config=config)
    final_payload["terrain"]["scenario_path"] = str(scenario_path)
    final_payload["scenario"]["path"] = str(scenario_path)
    final_payload["scenario"]["scenario_path"] = str(scenario_path)
    final_payload["scenario"]["vehicle"] = scheduled["vehicle"]
    final_payload["scenario"]["scheduling"] = scheduled["scheduling"]
    seed_start_report = _single_task_seed_feasibility_report(final_payload, scheduled, start_step=10.0)
    if not seed_start_report["all_tasks_seed_feasible"]:
        raise RuntimeError(f"single task seed feasibility failed: {seed_start_report}")
    audit = {
        **energy_audit,
        **time_audit,
        **seed_start_report,
        "selected_energy_cap": round(float(energy_cap), 6),
        "energy_cap_upper": round(float(energy_cap_upper), 6),
        "window_width_median_ratio": round(float(time_audit["window_width_median"] / float(config.horizon_min)), 6),
        "singleton_only_solution": False,
        "audit_note": "Generated by balanced route-set density rejection sampling; no existing instances were modified.",
    }
    return scheduled, final_payload, audit, roundtrip_report


def _metric_matrices(payload: dict[str, Any], scheduled_scenario: dict[str, Any]) -> dict[str, Any]:
    task_names = [node["id"] for node in payload["logical_graph"]["nodes"] if node["id"] != "depot"]
    task_names.sort(key=lambda value: int(str(value).split("_", 1)[1]) if str(value).startswith("task_") else str(value))
    node_names = ["depot", *task_names]
    node_to_idx = {name: idx for idx, name in enumerate(node_names)}
    n = len(node_names)
    best_energy = np.full((n, n), np.inf, dtype=float)
    best_time = np.full((n, n), np.inf, dtype=float)
    best_distance = np.full((n, n), np.inf, dtype=float)
    for edge in payload["logical_graph"]["edges"]:
        if not edge.get("feasible", True):
            continue
        i = node_to_idx[str(edge["from"])]
        j = node_to_idx[str(edge["to"])]
        for option in edge.get("path_options", []) or [edge]:
            best_energy[i, j] = min(best_energy[i, j], float(option["energy_proxy"]))
            best_time[i, j] = min(best_time[i, j], float(option["travel_time_min"]))
            best_distance[i, j] = min(best_distance[i, j], float(option.get("path_distance_km", 0.0)))
    tasks_by_id = {int(str(task["id"]).split("_", 1)[1]): task for task in scheduled_scenario["tasks"]}
    service_energy = np.zeros(n, dtype=float)
    service_time = np.zeros(n, dtype=float)
    for idx, name in enumerate(task_names, start=1):
        task_id = int(str(name).split("_", 1)[1])
        task = tasks_by_id[task_id]
        service_energy[idx] = float(task["service_energy_proxy"])
        service_time[idx] = float(task["service_time_min"])
    return {
        "node_names": node_names,
        "task_names": task_names,
        "energy": best_energy,
        "time": best_time,
        "distance": best_distance,
        "service_energy": service_energy,
        "service_time": service_time,
    }


def _subset_min_closed_energy(matrices: dict[str, Any], *, max_size: int) -> dict[int, dict[tuple[int, ...], float]]:
    n_tasks = len(matrices["task_names"])
    energy = matrices["energy"]
    service_energy = matrices["service_energy"]
    by_size: dict[int, dict[tuple[int, ...], float]] = {size: {} for size in range(1, max_size + 1)}
    for size in range(1, max_size + 1):
        for subset in combinations(range(1, n_tasks + 1), size):
            route_energy = _closed_route_min_cost(energy, subset)
            if math.isfinite(route_energy):
                route_energy += float(sum(service_energy[node] for node in subset))
            by_size[size][subset] = route_energy
    return by_size


def _closed_route_min_cost(matrix: np.ndarray, subset: tuple[int, ...]) -> float:
    if not subset:
        return 0.0
    if len(subset) == 1:
        node = subset[0]
        return float(matrix[0, node] + matrix[node, 0])
    index = {node: bit for bit, node in enumerate(subset)}
    dp: dict[tuple[int, int], float] = {}
    for node in subset:
        dp[(1 << index[node], node)] = float(matrix[0, node])
    full = (1 << len(subset)) - 1
    for mask in range(1, full + 1):
        for last in subset:
            current = dp.get((mask, last))
            if current is None:
                continue
            for nxt in subset:
                bit = 1 << index[nxt]
                if mask & bit:
                    continue
                key = (mask | bit, nxt)
                candidate = current + float(matrix[last, nxt])
                if candidate < dp.get(key, math.inf):
                    dp[key] = candidate
    return min((cost + float(matrix[last, 0]) for (mask, last), cost in dp.items() if mask == full), default=math.inf)


def _choose_energy_cap(
    matrices: dict[str, Any],
    subset_energy: dict[int, dict[tuple[int, ...], float]],
    *,
    profile: TightnessProfile,
    task_count: int,
    energy_cap_upper: float,
) -> tuple[float | None, dict[str, Any]]:
    single_values = list(subset_energy.get(1, {}).values())
    if not single_values or not all(math.isfinite(value) for value in single_values):
        return None, {"energy_cap_failure": "missing_single_task_energy"}
    max_single = max(single_values)
    cap_candidates: list[float] = []
    for margin in profile.energy_margin_candidates:
        cap = min(float(energy_cap_upper), max_single * float(margin))
        if cap >= max_single - 1.0e-9 and cap not in cap_candidates:
            cap_candidates.append(cap)
    if float(energy_cap_upper) not in cap_candidates:
        cap_candidates.append(float(energy_cap_upper))

    best_audit: dict[str, Any] | None = None
    for cap in cap_candidates:
        audit = _energy_density_audit(subset_energy, cap=float(cap), task_count=int(task_count))
        if (
            profile.energy_pair.contains(audit["energy_pair_feasible_ratio"])
            and (task_count < 3 or profile.energy_triple.contains(audit["energy_triple_feasible_ratio"]))
            and (task_count < 4 or profile.energy_quad.contains(audit["energy_quad_feasible_ratio"]))
            and profile.energy_large.contains(audit["energy_large_feasible_ratio"])
        ):
            return float(cap), audit
        best_audit = audit
    assert best_audit is not None
    return None, {"energy_cap_failure": "no_candidate_in_density_band", "last_candidate_audit": best_audit}


def _energy_density_audit(subset_energy: dict[int, dict[tuple[int, ...], float]], *, cap: float, task_count: int) -> dict[str, Any]:
    ratios: dict[int, float] = {}
    feasible_counts: dict[int, int] = {}
    total_counts: dict[int, int] = {}
    for size, values in subset_energy.items():
        total = len(values)
        feasible = sum(1 for value in values.values() if float(value) <= float(cap) + 1.0e-9)
        total_counts[size] = total
        feasible_counts[size] = feasible
        ratios[size] = 0.0 if total == 0 else feasible / total
    large_total = sum(total_counts.get(size, 0) for size in (5, 6))
    large_feasible = sum(feasible_counts.get(size, 0) for size in (5, 6))
    return {
        "energy_cap_candidate": round(float(cap), 6),
        "energy_single_max_ratio": round(max(subset_energy[1].values()) / float(cap), 6),
        "energy_pair_feasible_ratio": round(ratios.get(2, 0.0), 6),
        "energy_triple_feasible_ratio": round(ratios.get(3, 0.0), 6),
        "energy_quad_feasible_ratio": round(ratios.get(4, 0.0), 6),
        "energy_large_feasible_ratio": round(0.0 if large_total == 0 else large_feasible / large_total, 6),
        "energy_feasible_counts_by_size": {str(size): feasible_counts[size] for size in sorted(feasible_counts)},
        "energy_total_counts_by_size": {str(size): total_counts[size] for size in sorted(total_counts)},
    }


def _apply_balanced_time_windows(
    scenario: dict[str, Any],
    matrices: dict[str, Any],
    *,
    profile: TightnessProfile,
    seed: int,
) -> None:
    horizon = float(scenario["scheduling"]["horizon_min"])
    task_count = len(scenario["tasks"])
    template = _canonical_time_window_template(task_count, horizon=horizon, profile=profile)

    for task in scenario["tasks"]:
        task_id = int(str(task["id"]).split("_", 1)[1])
        ready, due = template[task_id]
        task["ready_time_min"] = round(float(ready), 6)
        task["due_time_min"] = round(float(due), 6)
        task["time_window_min"] = [task["ready_time_min"], task["due_time_min"]]
        task["r"] = task["ready_time_min"]
        task["D"] = task["due_time_min"]


def _canonical_time_window_template(
    task_count: int,
    *,
    horizon: float,
    profile: TightnessProfile,
) -> dict[int, tuple[float, float]]:
    """Return the same task-index windows for every instance of one size."""

    if task_count <= 5:
        wave_count = 3
        tail_reserve = 115.0
        min_due = 160.0
    elif task_count <= 10:
        wave_count = 5
        tail_reserve = 105.0
        min_due = 175.0
    else:
        wave_count = 7
        tail_reserve = 95.0
        min_due = 215.0
    span = max(30.0, float(horizon) - float(profile.window_base_min) - tail_reserve)
    template: dict[int, tuple[float, float]] = {}
    for task_id in range(1, int(task_count) + 1):
        wave = int(round((task_id - 1) * (wave_count - 1) / max(1, task_count - 1)))
        position = 0.0 if wave_count <= 1 else float(wave) / float(wave_count - 1)
        deterministic_offset = math.sin(task_id * 1.61803398875) * float(profile.ready_jitter_min)
        ready = max(0.0, position * span + deterministic_offset)
        length_factor = 1.0 + float(profile.window_jitter_fraction) * math.sin(task_id * 2.41421356237)
        window_len = max(45.0, float(profile.window_base_min) * length_factor)
        due = min(float(horizon) - 10.0, max(float(min_due), ready + window_len))
        if due <= ready + 20.0:
            ready = max(0.0, due - 20.0)
        template[task_id] = (round(float(ready), 6), round(float(due), 6))
    return template


def _time_window_audit(scenario: dict[str, Any], matrices: dict[str, Any], *, task_count: int) -> dict[str, Any]:
    windows = _task_windows(scenario)
    n = int(task_count)
    single_ok = all(_sequence_time_feasible((task,), matrices, windows, scenario) for task in range(1, n + 1))
    pair_total = 0
    pair_feasible = 0
    for subset in combinations(range(1, n + 1), 2):
        pair_total += 1
        if any(_sequence_time_feasible(order, matrices, windows, scenario) for order in permutations(subset)):
            pair_feasible += 1
    triple_total = 0
    triple_feasible = 0
    if n >= 3:
        for subset in combinations(range(1, n + 1), 3):
            triple_total += 1
            if any(_sequence_time_feasible(order, matrices, windows, scenario) for order in permutations(subset)):
                triple_feasible += 1
    widths = [due - ready for ready, due in windows.values()]
    overlap_pairs = 0
    for i, j in combinations(range(1, n + 1), 2):
        ri, di = windows[i]
        rj, dj = windows[j]
        if min(di, dj) >= max(ri, rj) - 1.0e-9:
            overlap_pairs += 1
    return {
        "single_task_timed_feasible": bool(single_ok),
        "time_pair_feasible_ratio": round(0.0 if pair_total == 0 else pair_feasible / pair_total, 6),
        "time_triple_feasible_ratio": round(0.0 if triple_total == 0 else triple_feasible / triple_total, 6),
        "time_pair_feasible_count": pair_feasible,
        "time_pair_total_count": pair_total,
        "time_triple_feasible_count": triple_feasible,
        "time_triple_total_count": triple_total,
        "window_width_median": round(float(np.median(widths)), 6) if widths else 0.0,
        "window_overlap_density": round(0.0 if pair_total == 0 else overlap_pairs / pair_total, 6),
    }


def _task_windows(scenario: dict[str, Any]) -> dict[int, tuple[float, float]]:
    windows: dict[int, tuple[float, float]] = {}
    for task in scenario["tasks"]:
        task_id = int(str(task["id"]).split("_", 1)[1])
        windows[task_id] = (float(task["ready_time_min"]), float(task["due_time_min"]))
    return windows


def _single_task_seed_feasibility_report(
    payload: dict[str, Any],
    scenario: dict[str, Any],
    *,
    start_step: float,
) -> dict[str, Any]:
    edges = {
        (str(edge["from"]), str(edge["to"])): edge
        for edge in payload["logical_graph"]["edges"]
        if edge.get("feasible", True)
    }
    tasks_by_name = {str(task["id"]): task for task in scenario["tasks"]}
    vehicle = scenario["vehicle"]
    scheduling = scenario["scheduling"]
    horizon = float(scheduling["horizon_min"])
    energy_limit = float(vehicle["max_roundtrip_energy_proxy"])
    rho = float(vehicle["rho"])
    survival_rate = float(vehicle.get("survival_energy_proxy_per_min", 0.0))
    task_waiting_allowed = bool(scheduling.get("task_waiting_allowed", True))
    violations: list[dict[str, Any]] = []
    feasible_count = 0
    for task_name in sorted(tasks_by_name, key=lambda value: int(value.split("_", 1)[1])):
        out_edge = edges.get(("depot", task_name))
        back_edge = edges.get((task_name, "depot"))
        if out_edge is None or back_edge is None:
            violations.append({"task": task_name, "reason": "missing depot roundtrip edge"})
            continue
        task = tasks_by_name[task_name]
        ready = float(task["ready_time_min"])
        due = float(task["due_time_min"])
        service_time = float(task["service_time_min"])
        service_energy = float(task["service_energy_proxy"])
        feasible = False
        best_interval = -math.inf
        best_energy_margin = -math.inf
        for out_option in out_edge.get("path_options", []) or [out_edge]:
            for back_option in back_edge.get("path_options", []) or [back_edge]:
                interval, energy_margin = _single_task_start_interval_and_energy_margin(
                    ready=ready,
                    due=due,
                    service_time=service_time,
                    service_energy=service_energy,
                    out_option=out_option,
                    back_option=back_option,
                    horizon=horizon,
                    energy_limit=energy_limit,
                    rho=rho,
                    survival_rate=survival_rate,
                    task_waiting_allowed=task_waiting_allowed,
                )
                best_interval = max(best_interval, interval)
                best_energy_margin = max(best_energy_margin, energy_margin)
                if interval >= -1.0e-9 and energy_margin >= -1.0e-9:
                    feasible = True
                    break
            if feasible:
                break
        if feasible:
            feasible_count += 1
        else:
            violations.append(
                {
                    "task": task_name,
                    "reason": "no depot-task-depot path option pair has a feasible start interval and energy margin",
                    "best_start_interval_min": round(float(best_interval), 6) if math.isfinite(best_interval) else None,
                    "best_energy_margin": round(float(best_energy_margin), 6) if math.isfinite(best_energy_margin) else None,
                }
            )
    total = len(tasks_by_name)
    return {
        "single_task_seed_start_step": round(float(start_step), 6),
        "single_task_seed_feasible_count": feasible_count,
        "single_task_seed_total_count": total,
        "all_tasks_seed_feasible": feasible_count == total,
        "single_task_seed_violation_count": len(violations),
        "single_task_seed_violations": violations[:10],
    }


def _single_task_start_interval_and_energy_margin(
    *,
    ready: float,
    due: float,
    service_time: float,
    service_energy: float,
    out_option: dict[str, Any],
    back_option: dict[str, Any],
    horizon: float,
    energy_limit: float,
    rho: float,
    survival_rate: float,
    task_waiting_allowed: bool,
) -> tuple[float, float]:
    out_time = float(out_option["travel_time_min"])
    back_time = float(back_option["travel_time_min"])
    lower = 0.0
    if not task_waiting_allowed:
        lower = max(lower, float(ready) - out_time)
    upper = min(float(horizon), float(due) - float(service_time) - out_time)
    return_offset = out_time + float(service_time) + back_time
    out_energy = float(out_option["energy_proxy"])
    back_energy = float(back_option["energy_proxy"])
    total_energy = out_energy + back_energy + float(service_energy) + float(survival_rate) * return_offset
    energy_margin = float(energy_limit) - total_energy
    end_offset = return_offset + total_energy / float(rho)
    upper = min(upper, float(horizon) - end_offset)
    return upper - lower, energy_margin


def _sequence_time_feasible(
    sequence: tuple[int, ...],
    matrices: dict[str, Any],
    windows: dict[int, tuple[float, float]],
    scenario: dict[str, Any],
) -> bool:
    time_matrix = matrices["time"]
    service_time = matrices["service_time"]
    horizon = float(scenario["scheduling"]["horizon_min"])
    offset = 0.0
    delay_low = 0.0
    delay_high = math.inf
    previous = 0
    for task in sequence:
        offset += float(time_matrix[previous, task])
        ready, due = windows[int(task)]
        delay_low = max(delay_low, ready - offset)
        service = float(service_time[task])
        delay_high = min(delay_high, due - service - offset)
        offset += service
        previous = int(task)
    total_duration = offset + float(time_matrix[previous, 0])
    delay_high = min(delay_high, horizon - total_duration)
    return delay_low <= delay_high + 1.0e-9


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

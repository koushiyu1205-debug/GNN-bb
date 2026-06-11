#!/usr/bin/env python3
"""Generate multi-scale Moon Trek instances with randomized audited windows.

This generator intentionally writes a new dataset root. It keeps the existing
balanced benchmark generator and all existing instances untouched.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
from itertools import combinations, permutations
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable, Sequence

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
    _circle_mask,
    _connected_component,
    _distance_km,
    _point_payload,
    _row_col_to_xy,
    _sample_spaced_points,
    _xy_to_nearest_row_col,
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
    _edge_metrics,
    _nearest_passable_cell,
    _scipy_adjacency_by_objective,
    _xy_to_row_col as _coarse_xy_to_row_col,
)
from BPC_future.scripts.generate_moon_trek_balanced_benchmark import (  # noqa: E402
    DEFAULT_TERRAINS,
    DensityBand,
    TightnessProfile,
    _all_pairs_reachable,
    _closed_route_min_cost,
    _metric_matrices,
    _profile_payload,
    _roundtrip_feasibility_report,
    _sequence_time_feasible,
    _single_task_seed_feasibility_report,
)


DEFAULT_OUTPUT_ROOT = "BPC_future/data/generated/moon_trek_multiscale_random_tw_120_20260610"
DEFAULT_FIGURE_ROOT = "BPC_future/draw/moon_trek_multiscale_random_tw_120_20260610"
DEFAULT_TASK_COUNTS = "5,10,20,30,50,100"
NODE_FEATURE_SCHEMA: tuple[str, ...] = (
    "demand",
    "service_time",
    "time_window_start",
    "time_window_end",
    "x_coord",
    "y_coord",
    "is_depot",
    "service_energy",
    "local_risk",
)
OPTION_FEATURE_SCHEMA: tuple[str, ...] = (
    "distance",
    "travel_time",
    "energy",
    "risk",
    "generalized_cost",
    "is_low_time",
    "is_low_energy",
    "is_low_risk",
    "option_rank",
    "option_count_for_pair",
)
ANCHOR_PATH_CATEGORY_WEIGHTS: dict[str, float] = {
    "eco": 0.40,
    "time": 0.40,
    "balanced": 0.20,
}
TIME_WINDOW_MODES: tuple[str, ...] = ("greedy-anchor", "random-wave", "sector-wave")
WILSON_Z_95 = 1.959963984540054


PROFILES: dict[int, TightnessProfile] = {
    5: TightnessProfile(
        window_base_min=220.0,
        window_jitter_fraction=0.22,
        ready_jitter_min=30.0,
        energy_margin_candidates=(1.10, 1.15, 1.20, 1.28, 1.36, 1.48, 1.60, 1.80),
        energy_pair=DensityBand(0.42, 0.98),
        energy_triple=DensityBand(0.12, 0.85),
        energy_quad=DensityBand(0.00, 0.70),
        energy_large=DensityBand(0.00, 0.50),
        time_pair=DensityBand(0.40, 1.00),
        time_triple=DensityBand(0.10, 0.88),
    ),
    10: TightnessProfile(
        window_base_min=170.0,
        window_jitter_fraction=0.22,
        ready_jitter_min=48.0,
        energy_margin_candidates=(1.08, 1.12, 1.16, 1.22, 1.30, 1.42, 1.58, 1.80),
        energy_pair=DensityBand(0.30, 0.94),
        energy_triple=DensityBand(0.06, 0.70),
        energy_quad=DensityBand(0.00, 0.48),
        energy_large=DensityBand(0.00, 0.30),
        time_pair=DensityBand(0.24, 0.94),
        time_triple=DensityBand(0.04, 0.62),
    ),
    20: TightnessProfile(
        window_base_min=180.0,
        window_jitter_fraction=0.24,
        ready_jitter_min=58.0,
        energy_margin_candidates=(1.06, 1.10, 1.15, 1.22, 1.32, 1.45, 1.62, 1.85, 2.10),
        energy_pair=DensityBand(0.20, 0.99),
        energy_triple=DensityBand(0.03, 0.90),
        energy_quad=DensityBand(0.00, 0.80),
        energy_large=DensityBand(0.00, 0.62),
        time_pair=DensityBand(0.14, 0.90),
        time_triple=DensityBand(0.02, 0.50),
    ),
    30: TightnessProfile(
        window_base_min=200.0,
        window_jitter_fraction=0.24,
        ready_jitter_min=66.0,
        energy_margin_candidates=(1.06, 1.10, 1.16, 1.24, 1.36, 1.52, 1.72, 1.96, 2.25),
        energy_pair=DensityBand(0.14, 0.99),
        energy_triple=DensityBand(0.020, 0.88),
        energy_quad=DensityBand(0.00, 0.76),
        energy_large=DensityBand(0.00, 0.58),
        time_pair=DensityBand(0.10, 0.88),
        time_triple=DensityBand(0.015, 0.46),
    ),
    50: TightnessProfile(
        window_base_min=230.0,
        window_jitter_fraction=0.22,
        ready_jitter_min=76.0,
        energy_margin_candidates=(1.05, 1.10, 1.16, 1.25, 1.38, 1.56, 1.80, 2.10, 2.45),
        energy_pair=DensityBand(0.08, 0.98),
        energy_triple=DensityBand(0.010, 0.84),
        energy_quad=DensityBand(0.00, 0.70),
        energy_large=DensityBand(0.00, 0.52),
        time_pair=DensityBand(0.075, 0.86),
        time_triple=DensityBand(0.008, 0.40),
    ),
    100: TightnessProfile(
        window_base_min=270.0,
        window_jitter_fraction=0.20,
        ready_jitter_min=88.0,
        energy_margin_candidates=(1.05, 1.10, 1.18, 1.30, 1.48, 1.72, 2.05, 2.45, 2.90),
        energy_pair=DensityBand(0.04, 0.98),
        energy_triple=DensityBand(0.004, 0.80),
        energy_quad=DensityBand(0.00, 0.64),
        energy_large=DensityBand(0.00, 0.46),
        time_pair=DensityBand(0.04, 0.84),
        time_triple=DensityBand(0.003, 0.34),
    ),
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate multi-scale randomized Moon Trek benchmark instances.")
    parser.add_argument("--terrain-dir", action="append", default=None, help="Terrain directory. Repeatable.")
    parser.add_argument("--task-counts", default=DEFAULT_TASK_COUNTS, help="Comma-separated task counts.")
    parser.add_argument("--instances-per-terrain-size", type=int, default=10)
    parser.add_argument("--seed-start", type=int, default=41000)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--figure-root", default=DEFAULT_FIGURE_ROOT)
    parser.add_argument("--tensor-format", choices=("both", "pt", "npz", "none"), default="both")
    parser.add_argument(
        "--time-window-modes",
        default="greedy-anchor",
        help="Comma-separated modes from greedy-anchor,random-wave,sector-wave.",
    )
    parser.add_argument(
        "--smart-jitter-spread-quantile",
        type=float,
        default=0.90,
        help="Task-adjacent multi-path travel-time spread quantile used as the smart-jitter width floor.",
    )
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
    parser.add_argument("--min-point-spacing-km", type=float, default=1.0)
    parser.add_argument("--max-seed-attempts", type=int, default=800)
    parser.add_argument("--horizon-min", type=float, default=720.0)
    parser.add_argument("--exact-combination-task-limit", type=int, default=20)
    parser.add_argument("--density-subset-sample-count", type=int, default=6000)
    parser.add_argument("--time-triple-sample-count", type=int, default=12000)
    parser.add_argument("--draw-one-per-size", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--draw-terrain-atlas", action=argparse.BooleanOptionalAction, default=False)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    terrain_dirs = tuple(args.terrain_dir or DEFAULT_TERRAINS)
    task_counts = tuple(int(part.strip()) for part in str(args.task_counts).split(",") if part.strip())
    time_window_modes = tuple(part.strip() for part in str(args.time_window_modes).split(",") if part.strip())
    unknown_modes = sorted(set(time_window_modes) - set(TIME_WINDOW_MODES))
    if unknown_modes or not time_window_modes:
        raise ValueError(f"--time-window-modes must use {list(TIME_WINDOW_MODES)}; got {list(time_window_modes)}")
    unsupported = sorted(set(task_counts) - set(PROFILES))
    if unsupported:
        raise ValueError(f"multiscale profiles are defined only for task counts {sorted(PROFILES)}; got {unsupported}")
    if float(args.min_point_spacing_km) < 1.0 - 1.0e-9:
        raise ValueError("--min-point-spacing-km must be at least 1.0 for this dataset family")
    if not 0.0 < float(args.smart_jitter_spread_quantile) <= 1.0:
        raise ValueError("--smart-jitter-spread-quantile must be in (0, 1]")
    _validate_tensor_dependencies(str(args.tensor_format))

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
    skip_counter: Counter[str] = Counter()
    manifest: dict[str, Any] = {
        "version": "multiscale_random_tw_v1",
        "output_root": str(output_root),
        "figure_root": str(figure_root),
        "terrain_dirs": list(terrain_dirs),
        "task_counts": list(task_counts),
        "time_window_modes": list(time_window_modes),
        "time_window_mode_count": len(time_window_modes),
        "instances_per_terrain_size": int(args.instances_per_terrain_size),
        "instances_per_size_total": int(args.instances_per_terrain_size) * len(terrain_dirs) * len(time_window_modes),
        "tensor_format": str(args.tensor_format),
        "scenario_config": {
            "operation_radius_km": float(args.operation_radius_km),
            "depot_xy_km": [float(args.depot_x_km), float(args.depot_y_km)],
            "vehicle_max_roundtrip_km": float(args.vehicle_max_roundtrip_km),
            "vehicle_max_roundtrip_energy_proxy_upper": float(args.vehicle_max_roundtrip_energy_proxy),
            "max_task_risk": float(args.max_task_risk),
            "min_point_spacing_km": float(args.min_point_spacing_km),
        },
        "density_audit_config": {
            "exact_combination_task_limit": int(args.exact_combination_task_limit),
            "density_subset_sample_count": int(args.density_subset_sample_count),
            "time_triple_sample_count": int(args.time_triple_sample_count),
            "smart_jitter_spread_quantile": float(args.smart_jitter_spread_quantile),
            "monte_carlo_audit_note": (
                "Sample counts, variances, and Wilson intervals are generation-screening diagnostics only; "
                "they are not solver proof logic and are not used as branch-price-and-cut certificates."
            ),
        },
        "solver_load_recommendations": {
            "complete_logical_graph_retained_by_generator": True,
            "official_benchmark_pair_pruning_enabled": False,
            "pruned_graphs_emitted": False,
            "large_scale_pair_pruning_scope": "disabled for official generated benchmark; solver-load experiments must write separate pruned JSON/tensors",
            "suggested_for_task_count_ge": 50,
            "suggested_pair_prune_rule": (
                "optionally hide directed pair edges whose physical distance is greater than 15km "
                "and whose task time windows are mutually incompatible in both orders"
            ),
            "exactness_requirement": (
                "pair pruning must be emitted as an independent pruned graph/tensor version and every removed directed edge "
                "must be certified bidirectionally time-window infeasible before solver use"
            ),
        },
        "graph_config": asdict(graph_config),
        "base_scheduling_augmentation": asdict(base_scheduling_config),
        "balanced_profiles": {str(key): _profile_payload(value) for key, value in PROFILES.items()},
        "instances": [],
        "attempts": [],
        "skip_summary": {},
        "generation_summary": {},
    }

    for terrain_index, terrain_dir in enumerate(terrain_dirs):
        terrain_path = Path(terrain_dir)
        grid = load_terrain_grid(terrain_path)
        graph = build_coarse_terrain_graph(grid, graph_config)
        terrain_name = grid.source_dir.name
        if args.draw_terrain_atlas:
            draw_terrain_atlas(grid, figure_root / terrain_name / "terrain")

        for task_count in task_counts:
            for mode_index, time_window_mode in enumerate(time_window_modes):
                accepted = 0
                attempt = 0
                mode_slug = _mode_slug(time_window_mode)
                while accepted < int(args.instances_per_terrain_size):
                    if attempt >= int(args.max_seed_attempts):
                        raise RuntimeError(
                            f"failed to generate {args.instances_per_terrain_size} instances for "
                            f"{terrain_name} tasks={task_count} mode={time_window_mode} after {attempt} attempts; "
                            f"skips={dict(skip_counter)}"
                        )
                    seed = (
                        int(args.seed_start)
                        + int(mode_index) * 1000000
                        + terrain_index * 100000
                        + task_count * 1000
                        + accepted * 101
                        + attempt
                    )
                    attempt += 1
                    sample_index = accepted + 1
                    instance_id = (
                        f"{terrain_name}_{mode_slug}_randomtw_tasks{task_count:03d}_{sample_index:02d}_seed{seed}"
                    )
                    scenario_dir = output_root / "scenarios" / mode_slug / terrain_name / f"tasks_{task_count:03d}"
                    graph_dir = output_root / "logical_graphs" / mode_slug / terrain_name / f"tasks_{task_count:03d}"
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
                        scenario = _sample_path_screened_operational_scenario(
                            grid,
                            graph,
                            scenario_config,
                            energy_cap_upper=float(args.vehicle_max_roundtrip_energy_proxy),
                        )
                        scenario["id"] = instance_id
                        scenario["instance_id"] = instance_id
                        scenario["vehicle"]["max_roundtrip_energy_proxy"] = float(args.vehicle_max_roundtrip_energy_proxy)
                        scenario["vehicle"][
                            "final_feasibility_note"
                        ] = "Multiscale random-TW generator screens final energy and time-window route-set density."
                        payload = build_logical_graph_payload_from_graph(
                            graph,
                            scenario,
                            scenario_path=scenario_path,
                            source_shape=grid.shape,
                            use_scipy_dijkstra=True,
                        )
                        if not _all_pairs_reachable(payload):
                            raise RuntimeError("logical graph has unreachable pair")
                        balanced = _build_random_tw_instance(
                            scenario,
                            payload,
                            task_count=int(task_count),
                            seed=int(seed),
                            scenario_path=scenario_path,
                            base_config=base_scheduling_config,
                            energy_cap_upper=float(args.vehicle_max_roundtrip_energy_proxy),
                            exact_combination_task_limit=int(args.exact_combination_task_limit),
                            density_subset_sample_count=int(args.density_subset_sample_count),
                            time_triple_sample_count=int(args.time_triple_sample_count),
                            time_window_mode=str(time_window_mode),
                            smart_jitter_spread_quantile=float(args.smart_jitter_spread_quantile),
                        )
                    except RuntimeError as exc:
                        reason = _skip_reason_bucket(exc)
                        skip_counter[f"{terrain_name}|{task_count}|{time_window_mode}|{reason}"] += 1
                        attempt_entry = _attempt_record(
                            status="skipped",
                            terrain=terrain_name,
                            task_count=int(task_count),
                            time_window_mode=str(time_window_mode),
                            sample_index=int(sample_index),
                            attempt_index=int(attempt),
                            seed=int(seed),
                            reason_bucket=reason,
                            reason=str(exc),
                        )
                        manifest["attempts"].append(attempt_entry)
                        _log_skip(terrain_name, task_count, seed, exc, time_window_mode=time_window_mode)
                        continue

                    final_scenario, final_payload, audit, roundtrip_report = balanced
                    manifest["attempts"].append(
                        _attempt_record(
                            status="accepted",
                            terrain=terrain_name,
                            task_count=int(task_count),
                            time_window_mode=str(time_window_mode),
                            sample_index=int(sample_index),
                            attempt_index=int(attempt),
                            seed=int(seed),
                            instance_id=instance_id,
                        )
                    )
                    figures: dict[str, str] = {}
                    if args.draw_one_per_size and accepted == 0:
                        figure_dir = figure_root / mode_slug / terrain_name / f"tasks_{task_count:03d}" / instance_id
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
                    tensor_entry = _export_gnn_tensors(
                        graph_path=graph_path,
                        output_root=output_root,
                        instance_id=instance_id,
                        terrain=terrain_name,
                        task_count=int(task_count),
                        seed=int(seed),
                        scenario_path=scenario_path,
                        tensor_format=str(args.tensor_format),
                    )
                    entry = {
                        "instance_id": instance_id,
                        "terrain": terrain_name,
                        "task_count": int(task_count),
                        "time_window_mode": str(time_window_mode),
                        "sample_index": sample_index,
                        "seed": seed,
                        "scenario": str(scenario_path),
                        "logical_graph": str(graph_path),
                        "gnn_tensors": tensor_entry,
                        "figures": figures,
                        "logical_summary": {
                            key: final_payload["logical_graph"][key]
                            for key in ("node_count", "directed_edge_count", "feasible_directed_edge_count")
                        },
                        "physical_roundtrip_check": roundtrip_report,
                        "vehicle": final_scenario["vehicle"],
                        "scheduling": final_scenario["scheduling"],
                        "balanced_audit": audit,
                        "attempts_used_for_sample": int(attempt),
                    }
                    manifest["instances"].append(entry)
                    accepted += 1
                    print(json.dumps({"event": "accepted", **entry}, sort_keys=True))

    manifest["skip_summary"] = dict(sorted(skip_counter.items()))
    manifest["generation_summary"] = _manifest_generation_summary(manifest)
    manifest_path = output_root / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"event": "finish", "manifest": str(manifest_path), "instances": len(manifest["instances"])}, indent=2))


def _sample_path_screened_operational_scenario(
    grid: Any,
    graph: Any,
    config: ScenarioConfig,
    *,
    energy_cap_upper: float,
) -> dict[str, Any]:
    """Sample tasks only from cells with a feasible coarse depot round trip.

    The original scenario sampler filters by Euclidean one-way range.  For
    larger task counts, rejection probability becomes extreme because one
    physically awkward task can make the whole sample unusable.  This helper
    keeps the same task-spacing and risk rules, but intersects candidates with
    a coarse-graph singleton feasibility screen under the official distance
    limit and the configured energy upper cap.  Final exact route-set density
    audits still run later and remain authoritative for acceptance.
    """

    rng = np.random.default_rng(int(config.seed))
    center = tuple(float(value) for value in config.depot_xy_km)
    passable = grid.valid & (~grid.impassable) & np.isfinite(grid.risk)
    depot_row, depot_col = _xy_to_nearest_row_col(grid, center)
    if not passable[depot_row, depot_col]:
        return sample_operational_scenario(grid, config)
    depot_component = _connected_component(passable, depot_row, depot_col)
    depot_xy = _row_col_to_xy(grid, depot_row, depot_col)
    base_mask = passable & (grid.risk <= float(config.max_task_risk))
    base_mask &= depot_component
    base_mask &= _circle_mask(grid, center, float(config.operation_radius_km))
    base_mask &= _circle_mask(grid, depot_xy, float(config.vehicle_max_roundtrip_km) / 2.0)
    feasible_coarse = _coarse_singleton_feasible_mask(
        graph,
        depot_xy=depot_xy,
        max_roundtrip_km=float(config.vehicle_max_roundtrip_km),
        energy_cap_upper=float(energy_cap_upper),
    )
    row_factor = grid.shape[0] // graph.shape[0]
    col_factor = grid.shape[1] // graph.shape[1]
    feasible_highres = np.repeat(np.repeat(feasible_coarse, row_factor, axis=0), col_factor, axis=1)
    feasible_highres = feasible_highres[: grid.shape[0], : grid.shape[1]]
    task_mask = base_mask & feasible_highres
    candidates = np.argwhere(task_mask)
    if candidates.shape[0] < int(config.task_count):
        raise RuntimeError(
            f"only {candidates.shape[0]} path-screened candidate task cells, need {config.task_count}; "
            "relax vehicle limits or terrain risk thresholds"
        )
    tasks = _sample_spaced_points(
        grid,
        candidates,
        rng,
        int(config.task_count),
        float(config.min_point_spacing_km),
        depot_xy,
    )
    farthest = max(_distance_km(depot_xy, task["xy_km"]) for task in tasks) if tasks else 0.0
    return {
        "seed": int(config.seed),
        "terrain": {
            "source_dir": str(grid.source_dir),
            "width_km": grid.width_km,
            "height_km": grid.height_km,
            "shape": list(grid.shape),
        },
        "operation_region": {
            "center_xy_km": [round(center[0], 6), round(center[1], 6)],
            "radius_km": float(config.operation_radius_km),
            "note": "The depot and operation circle center are fixed; only task points are randomized.",
        },
        "vehicle": {
            "max_roundtrip_km": float(config.vehicle_max_roundtrip_km),
            "max_one_way_euclidean_km": float(config.vehicle_max_roundtrip_km) / 2.0,
            "farthest_depot_task_km": round(farthest, 6),
        },
        "connectivity": {
            "type": "4-connected passable grid component with coarse singleton physical feasibility screen",
            "depot_component_cells": int(depot_component.sum()),
            "task_candidate_cells": int(task_mask.sum()),
            "all_tasks_in_depot_component": True,
            "path_screened_candidate_cells": int(task_mask.sum()),
            "path_screened_coarse_cells": int(feasible_coarse.sum()),
            "path_screen_note": (
                "Candidates must have a coarse-graph depot round trip within max_roundtrip_km "
                "and energy_cap_upper before exact route-set density auditing."
            ),
        },
        "sampling": {
            **asdict(config),
            "path_screening_enabled": True,
            "path_screen_energy_cap_upper": float(energy_cap_upper),
        },
        "depot": {
            **_point_payload(grid, depot_row, depot_col, "depot"),
            "requested_xy_km": [round(center[0], 6), round(center[1], 6)],
        },
        "tasks": tasks,
    }


def _coarse_singleton_feasible_mask(
    graph: Any,
    *,
    depot_xy: tuple[float, float],
    max_roundtrip_km: float,
    energy_cap_upper: float,
) -> np.ndarray:
    cache_key = (
        id(graph),
        round(float(depot_xy[0]), 6),
        round(float(depot_xy[1]), 6),
        round(float(max_roundtrip_km), 6),
        round(float(energy_cap_upper), 6),
    )
    cached = _SINGLETON_FEASIBLE_MASK_CACHE.get(cache_key)
    if cached is not None:
        return cached.copy()
    row, col = _coarse_xy_to_row_col(graph, depot_xy)
    depot_row, depot_col = _nearest_passable_cell(graph.passable, row, col)
    depot_index = depot_row * graph.shape[1] + depot_col
    option_metrics = _depot_option_metric_maps(graph, depot_index)
    feasible = graph.passable.copy()
    option_feasible = np.zeros(graph.shape, dtype=bool)
    for out_metric in option_metrics["out"].values():
        for back_metric in option_metrics["back"].values():
            roundtrip_distance = out_metric[:, 0].reshape(graph.shape) + back_metric[:, 0].reshape(graph.shape)
            roundtrip_energy = out_metric[:, 2].reshape(graph.shape) + back_metric[:, 2].reshape(graph.shape)
            option_feasible |= (
                np.isfinite(roundtrip_distance)
                & np.isfinite(roundtrip_energy)
                & (roundtrip_distance <= float(max_roundtrip_km) + 1.0e-9)
                & (roundtrip_energy <= float(energy_cap_upper) + 1.0e-9)
            )
    feasible &= option_feasible
    _SINGLETON_FEASIBLE_MASK_CACHE[cache_key] = feasible.copy()
    return feasible


_SINGLETON_FEASIBLE_MASK_CACHE: dict[tuple[Any, ...], np.ndarray] = {}
_DEPOT_OPTION_METRIC_CACHE: dict[tuple[int, int], dict[str, dict[str, np.ndarray]]] = {}


def _depot_option_metric_maps(graph: Any, depot_index: int) -> dict[str, dict[str, np.ndarray]]:
    cache_key = (id(graph), int(depot_index))
    cached = _DEPOT_OPTION_METRIC_CACHE.get(cache_key)
    if cached is not None:
        return cached
    from scipy.sparse.csgraph import dijkstra as scipy_dijkstra

    adjacency = _scipy_adjacency_by_objective(graph)
    objective_by_path = {
        "low_time": "travel_time_h",
        "low_energy": "energy_proxy",
        "low_risk": "risk_integral",
    }
    out: dict[str, np.ndarray] = {}
    back: dict[str, np.ndarray] = {}
    for path_type, objective in objective_by_path.items():
        _dist, predecessors = scipy_dijkstra(
            adjacency[objective],
            directed=True,
            indices=int(depot_index),
            return_predecessors=True,
        )
        out[path_type] = _metric_tree_from_predecessors(
            graph,
            np.asarray(predecessors),
            source_index=int(depot_index),
            reverse_original_orientation=False,
        )
        _dist_back, predecessors_back = scipy_dijkstra(
            adjacency[objective].T,
            directed=True,
            indices=int(depot_index),
            return_predecessors=True,
        )
        back[path_type] = _metric_tree_from_predecessors(
            graph,
            np.asarray(predecessors_back),
            source_index=int(depot_index),
            reverse_original_orientation=True,
        )
    result = {"out": out, "back": back}
    _DEPOT_OPTION_METRIC_CACHE[cache_key] = result
    return result


def _metric_tree_from_predecessors(
    graph: Any,
    predecessors: np.ndarray,
    *,
    source_index: int,
    reverse_original_orientation: bool,
) -> np.ndarray:
    node_count = graph.shape[0] * graph.shape[1]
    metrics = np.full((node_count, 5), np.inf, dtype="float64")
    metrics[int(source_index)] = 0.0
    visiting = np.zeros(node_count, dtype=np.int8)

    def compute(index: int) -> np.ndarray:
        index = int(index)
        if np.isfinite(metrics[index, 0]):
            return metrics[index]
        if visiting[index]:
            return metrics[index]
        previous = int(predecessors[index])
        if previous < 0:
            return metrics[index]
        visiting[index] = 1
        parent_metric = compute(previous)
        if np.isfinite(parent_metric[0]):
            edge_metric = _coarse_edge_metric_between_indices(
                graph,
                index,
                previous,
                reverse_original_orientation=bool(reverse_original_orientation),
            )
            metrics[index] = parent_metric + edge_metric
        visiting[index] = 0
        return metrics[index]

    reachable = np.flatnonzero(np.asarray(predecessors) >= 0)
    for index in reachable:
        compute(int(index))
    metrics[int(source_index)] = 0.0
    return metrics


def _coarse_edge_metric_between_indices(
    graph: Any,
    child_index: int,
    parent_index: int,
    *,
    reverse_original_orientation: bool,
) -> np.ndarray:
    cols = graph.shape[1]
    child_row, child_col = divmod(int(child_index), cols)
    parent_row, parent_col = divmod(int(parent_index), cols)
    if reverse_original_orientation:
        row, col, n_row, n_col = child_row, child_col, parent_row, parent_col
    else:
        row, col, n_row, n_col = parent_row, parent_col, child_row, child_col
    step = math.hypot(float(n_col - col) * graph.dx_km, float(n_row - row) * graph.dy_km)
    edge = _edge_metrics(graph, row, col, n_row, n_col, step)
    return np.array(
        [
            edge["distance_km"],
            edge["risk_integral"],
            edge["energy_proxy"],
            edge["travel_time_h"],
            edge["generalized_cost"],
        ],
        dtype="float64",
    )


def _build_random_tw_instance(
    scenario: dict[str, Any],
    payload: dict[str, Any],
    *,
    task_count: int,
    seed: int,
    scenario_path: Path,
    base_config: SchedulingAugmentationConfig,
    energy_cap_upper: float,
    exact_combination_task_limit: int,
    density_subset_sample_count: int,
    time_triple_sample_count: int,
    time_window_mode: str,
    smart_jitter_spread_quantile: float,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    profile = PROFILES[int(task_count)]
    preliminary = augment_scenario_for_multisortie_cvrptw(scenario, config=base_config)
    matrices = _augment_matrices_with_path_options(
        _metric_matrices(payload, preliminary),
        payload,
        spread_quantile=float(smart_jitter_spread_quantile),
    )
    energy_candidates = _budgeted_subset_min_closed_energy(
        matrices,
        max_size=min(6, int(task_count)),
        seed=int(seed) + 17,
        exact_task_limit=int(exact_combination_task_limit),
        sample_count=int(density_subset_sample_count),
        survival_rate=float(preliminary["vehicle"].get("survival_energy_proxy_per_min", 0.0)),
    )
    energy_cap, energy_audit = _choose_energy_cap_budgeted(
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
    window_template = _apply_random_time_windows(
        scheduled,
        matrices,
        profile=profile,
        seed=seed,
        time_window_mode=str(time_window_mode),
    )
    time_audit = _time_window_audit_budgeted(
        scheduled,
        matrices,
        task_count=int(task_count),
        seed=int(seed) + 31,
        exact_task_limit=int(exact_combination_task_limit),
        triple_sample_count=int(time_triple_sample_count),
    )
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
        "type": "instance_specific_cap_selected_by_budgeted_route_set_density",
        "upper_cap": float(energy_cap_upper),
        "selected_cap": float(energy_cap),
    }
    scheduled["scheduling"]["balanced_time_window_policy"] = {
        "type": "random_instance_template_audited",
        "anchor_policy": _time_window_anchor_policy_payload(
            int(task_count),
            mode=str(time_window_mode),
            smart_jitter_spread_quantile=float(smart_jitter_spread_quantile),
        ),
        "seed": int(seed),
        "profile": _profile_payload(profile),
        "template": {str(task_id): list(window) for task_id, window in sorted(window_template.items())},
        "audit": time_audit,
    }

    roundtrip_report = _roundtrip_feasibility_report(
        payload,
        max_distance=float(scheduled["vehicle"]["max_roundtrip_km"]),
        max_energy=float(energy_cap),
    )
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
        "minimum_task_spacing_km": round(float(_minimum_task_spacing_km(scheduled)), 6),
        "window_width_median_ratio": round(float(time_audit["window_width_median"] / float(config.horizon_min)), 6),
        "time_window_mode": str(time_window_mode),
        "singleton_only_solution": False,
        "audit_note": "Generated by multiscale random-TW route-set density rejection sampling; no existing instances were modified.",
    }
    return scheduled, final_payload, audit, roundtrip_report


def _validate_tensor_dependencies(tensor_format: str) -> None:
    if tensor_format not in {"both", "pt"}:
        return
    try:
        import torch  # noqa: F401
    except Exception as exc:
        raise RuntimeError(
            f"tensor_format={tensor_format!r} requires torch to write .pt files; "
            "install torch or use --tensor-format npz in this environment"
        ) from exc


def _budgeted_subset_min_closed_energy(
    matrices: dict[str, Any],
    *,
    max_size: int,
    seed: int,
    exact_task_limit: int,
    sample_count: int,
    survival_rate: float = 0.0,
) -> dict[int, dict[tuple[int, ...], float]]:
    n_tasks = len(matrices["task_names"])
    energy = matrices["energy"]
    travel_time = matrices["time"]
    service_energy = matrices["service_energy"]
    service_time = matrices["service_time"]
    rng = np.random.default_rng(int(seed))
    by_size: dict[int, dict[tuple[int, ...], float]] = {size: {} for size in range(1, max_size + 1)}
    for size in range(1, max_size + 1):
        if size == 1:
            subsets: Iterable[tuple[int, ...]] = combinations(range(1, n_tasks + 1), 1)
        elif n_tasks <= int(exact_task_limit):
            subsets = combinations(range(1, n_tasks + 1), size)
        else:
            subsets = _sample_unique_subsets(n_tasks, size, sample_count=max(1, int(sample_count)), rng=rng)
        for subset in subsets:
            route_energy = _closed_route_min_cost(energy, subset)
            if math.isfinite(route_energy):
                route_energy += float(sum(service_energy[node] for node in subset))
                route_time = _closed_route_min_cost(travel_time, subset)
                if math.isfinite(route_time):
                    route_time += float(sum(service_time[node] for node in subset))
                    route_energy += float(survival_rate) * route_time
            by_size[size][tuple(subset)] = route_energy
    return by_size


def _sample_unique_subsets(
    n_tasks: int,
    size: int,
    *,
    sample_count: int,
    rng: np.random.Generator,
) -> list[tuple[int, ...]]:
    total = math.comb(int(n_tasks), int(size))
    target = min(int(sample_count), int(total))
    result: set[tuple[int, ...]] = set()
    max_attempts = max(target * 20, 100)
    attempts = 0
    while len(result) < target and attempts < max_attempts:
        attempts += 1
        subset = tuple(sorted(int(value) + 1 for value in rng.choice(int(n_tasks), size=int(size), replace=False)))
        result.add(subset)
    if len(result) < target:
        for subset in combinations(range(1, int(n_tasks) + 1), int(size)):
            result.add(subset)
            if len(result) >= target:
                break
    return sorted(result)


def _choose_energy_cap_budgeted(
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
        audit = _energy_density_audit_budgeted(subset_energy, cap=float(cap), task_count=int(task_count))
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


def _energy_density_audit_budgeted(
    subset_energy: dict[int, dict[tuple[int, ...], float]],
    *,
    cap: float,
    task_count: int,
) -> dict[str, Any]:
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
        "energy_density_estimates_by_size": {
            str(size): _ratio_estimate_payload(
                feasible_counts[size],
                total_counts[size],
                sampled=bool(int(task_count) > 20 and size > 1),
            )
            for size in sorted(feasible_counts)
        },
        "energy_density_audit_budgeted": bool(int(task_count) > 20),
    }


def _apply_random_time_windows(
    scenario: dict[str, Any],
    matrices: dict[str, Any],
    *,
    profile: TightnessProfile,
    seed: int,
    time_window_mode: str = "greedy-anchor",
) -> dict[int, tuple[float, float]]:
    horizon = float(scenario["scheduling"]["horizon_min"])
    task_count = len(scenario["tasks"])
    template = _random_time_window_template(
        scenario,
        task_count,
        horizon=horizon,
        profile=profile,
        seed=int(seed),
        matrices=matrices,
        mode=str(time_window_mode),
    )
    for task in scenario["tasks"]:
        task_id = int(str(task["id"]).split("_", 1)[1])
        ready, due = template[task_id]
        task["ready_time_min"] = round(float(ready), 6)
        task["due_time_min"] = round(float(due), 6)
        task["time_window_min"] = [task["ready_time_min"], task["due_time_min"]]
        task["r"] = task["ready_time_min"]
        task["D"] = task["due_time_min"]
    return template


def _random_time_window_template(
    scenario: dict[str, Any],
    task_count: int,
    *,
    horizon: float,
    profile: TightnessProfile,
    seed: int,
    matrices: dict[str, Any],
    mode: str = "greedy-anchor",
) -> dict[int, tuple[float, float]]:
    if mode not in TIME_WINDOW_MODES:
        raise ValueError(f"unknown time-window mode {mode!r}; expected one of {TIME_WINDOW_MODES}")
    rng = np.random.default_rng(int(seed) + 7001)
    span = max(30.0, float(horizon) - float(profile.window_base_min) - _tail_reserve(task_count))
    if mode == "greedy-anchor":
        anchors = _greedy_tour_arrival_anchors(
            int(task_count),
            matrices=matrices,
            horizon=float(horizon),
            profile=profile,
            seed=int(seed) + 9011,
            span=float(span),
        )
    elif mode == "random-wave":
        anchors = _random_wave_arrival_anchors(
            int(task_count),
            horizon=float(horizon),
            profile=profile,
            seed=int(seed) + 9011,
            span=float(span),
        )
    else:
        anchors = _sector_wave_arrival_anchors(
            scenario,
            int(task_count),
            horizon=float(horizon),
            profile=profile,
            seed=int(seed) + 9011,
            span=float(span),
        )
    task_ids = list(range(1, int(task_count) + 1))
    service_time = matrices["service_time"]
    time_matrix = matrices["time"]
    multi_path_spread = matrices.get("multi_path_time_spread")
    template: dict[int, tuple[float, float]] = {}
    mode_width_multiplier = _time_window_width_multiplier(str(mode), int(task_count))
    min_width = max(35.0, min(80.0, 0.28 * float(profile.window_base_min) * mode_width_multiplier))
    for task_id in task_ids:
        route_center = float(anchors[int(task_id)])
        ready_noise = rng.uniform(-float(profile.ready_jitter_min), float(profile.ready_jitter_min))
        local_noise = rng.normal(0.0, max(1.0, 0.08 * float(profile.ready_jitter_min)))
        width_factor = 1.0 + rng.uniform(-float(profile.window_jitter_fraction), float(profile.window_jitter_fraction))
        path_slack = 0.0 if multi_path_spread is None else float(multi_path_spread[int(task_id)])
        smart_width_floor = min_width + max(0.0, path_slack)
        base_width = float(profile.window_base_min) * mode_width_multiplier
        width = min(float(horizon) - 5.0, max(smart_width_floor, base_width * width_factor))
        out_time = float(time_matrix[0, task_id])
        back_time = float(time_matrix[task_id, 0])
        service = float(service_time[task_id])
        center = route_center + 0.35 * ready_noise + local_noise
        left_fraction = 0.45 + rng.uniform(-0.08, 0.08)
        ready = max(0.0, center - left_fraction * width)
        latest_ready = max(0.0, float(horizon) - back_time - service - min_width - 5.0)
        ready = min(ready, latest_ready)
        due = ready + width
        if due > float(horizon) - 5.0:
            due = float(horizon) - 5.0
            ready = max(0.0, due - width)
        due = max(due, out_time + service + 5.0)
        if due > float(horizon) - 5.0:
            due = float(horizon) - 5.0
            ready = max(0.0, due - width)
        if due <= ready + 20.0:
            ready = max(0.0, min(ready, due - 20.0))
        template[int(task_id)] = (round(float(ready), 6), round(float(due), 6))
    return template


def _greedy_tour_arrival_anchors(
    task_count: int,
    *,
    matrices: dict[str, Any],
    horizon: float,
    profile: TightnessProfile,
    seed: int,
    span: float,
) -> dict[int, float]:
    rng = np.random.default_rng(int(seed))
    order = _nearest_neighbor_order(int(task_count), matrices=matrices, rng=rng)
    max_tasks_per_sortie = _anchor_max_tasks_per_sortie()
    fleet_size = _fleet_size_for_task_count(int(task_count))
    chunks = [order[start : start + max_tasks_per_sortie] for start in range(0, len(order), max_tasks_per_sortie)]
    round_count = max(1, math.ceil(len(chunks) / max(1, fleet_size)))
    anchors: dict[int, float] = {}
    for chunk_index, chunk in enumerate(chunks):
        round_index = chunk_index // max(1, fleet_size)
        lane_index = chunk_index % max(1, fleet_size)
        round_position = 0.0 if round_count <= 1 else float(round_index) / float(round_count - 1)
        lane_center = (float(lane_index) - 0.5 * float(max(0, fleet_size - 1))) * 0.10 * float(profile.window_base_min)
        sortie_start = max(0.0, round_position * float(span) + lane_center)
        previous = 0
        elapsed = 0.0
        for task_id in chunk:
            elapsed += _sample_anchor_travel_time(matrices, previous, int(task_id), rng)
            anchors[int(task_id)] = min(float(horizon) - 30.0, max(0.0, sortie_start + elapsed))
            elapsed += float(matrices["service_time"][task_id])
            previous = int(task_id)
    return anchors


def _random_wave_arrival_anchors(
    task_count: int,
    *,
    horizon: float,
    profile: TightnessProfile,
    seed: int,
    span: float,
) -> dict[int, float]:
    rng = np.random.default_rng(int(seed))
    task_ids = list(range(1, int(task_count) + 1))
    rng.shuffle(task_ids)
    wave_count = _wave_count(int(task_count))
    wave_centers = _wave_centers(wave_count, span=float(span), horizon=float(horizon), profile=profile)
    anchors: dict[int, float] = {}
    for rank, task_id in enumerate(task_ids):
        wave = rank % wave_count
        jitter = rng.normal(0.0, max(2.0, 0.22 * float(profile.ready_jitter_min)))
        anchors[int(task_id)] = min(float(horizon) - 30.0, max(0.0, float(wave_centers[wave]) + float(jitter)))
    return anchors


def _sector_wave_arrival_anchors(
    scenario: dict[str, Any],
    task_count: int,
    *,
    horizon: float,
    profile: TightnessProfile,
    seed: int,
    span: float,
) -> dict[int, float]:
    rng = np.random.default_rng(int(seed))
    wave_count = _wave_count(int(task_count))
    wave_centers = _wave_centers(wave_count, span=float(span), horizon=float(horizon), profile=profile)
    depot_xy = np.asarray(scenario.get("depot", {}).get("xy_km", [0.0, 0.0]), dtype=float)
    anchors: dict[int, float] = {}
    for task in scenario["tasks"]:
        task_id = int(str(task["id"]).split("_", 1)[1])
        xy = np.asarray(task.get("xy_km", [0.0, 0.0]), dtype=float)
        dx, dy = xy - depot_xy
        angle = math.atan2(float(dy), float(dx))
        sector = int(math.floor(((angle + math.pi) / (2.0 * math.pi)) * wave_count)) % wave_count
        distance_bias = 0.015 * float(np.hypot(float(dx), float(dy))) * float(profile.window_base_min)
        jitter = rng.normal(0.0, max(2.0, 0.16 * float(profile.ready_jitter_min)))
        anchors[task_id] = min(
            float(horizon) - 30.0,
            max(0.0, float(wave_centers[sector]) + float(distance_bias) + float(jitter)),
        )
    return anchors


def _time_window_width_multiplier(mode: str, task_count: int) -> float:
    """Mode-specific width scaling for ablation distributions.

    Sector-wave anchors deliberately align spatial sectors with temporal waves.
    With the shared base widths, adjacent sectors overlap heavily at N>=20 and
    the generator rejects nearly every sample as too loose.  Narrowing only this
    ablation mode keeps singleton feasibility protected by the smart-jitter
    floor while restoring a useful pair/triple density range.
    """

    mode_name = str(mode)
    n_tasks = int(task_count)
    if mode_name == "greedy-anchor":
        if n_tasks <= 30:
            return 1.0
        if n_tasks <= 50:
            return 0.72
        return 0.50
    if mode_name == "random-wave":
        if n_tasks <= 20:
            return 1.0
        if n_tasks <= 30:
            return 0.82
        if n_tasks <= 50:
            return 0.70
        return 0.50
    if mode_name != "sector-wave":
        return 1.0
    if n_tasks <= 10:
        return 0.82
    if n_tasks <= 30:
        return 0.66
    if n_tasks <= 50:
        return 0.50
    return 0.38


def _wave_centers(
    wave_count: int,
    *,
    span: float,
    horizon: float,
    profile: TightnessProfile,
) -> list[float]:
    if int(wave_count) <= 1:
        return [0.5 * min(float(span), float(horizon))]
    margin = min(0.18 * float(profile.window_base_min), max(0.0, 0.08 * float(span)))
    return [
        min(float(horizon) - 30.0, max(0.0, margin + float(idx) * max(1.0, float(span) - 2.0 * margin) / float(wave_count - 1)))
        for idx in range(int(wave_count))
    ]


def _nearest_neighbor_order(
    task_count: int,
    *,
    matrices: dict[str, Any],
    rng: np.random.Generator,
) -> list[int]:
    distance_matrix = matrices["distance"]
    remaining: set[int] = set(range(1, int(task_count) + 1))
    order: list[int] = []
    current = 0
    while remaining:
        best_distance = min(float(distance_matrix[current, task_id]) for task_id in remaining)
        tied = [task_id for task_id in sorted(remaining) if float(distance_matrix[current, task_id]) <= best_distance + 1.0e-9]
        chosen = int(tied[int(rng.integers(0, len(tied)))])
        remaining.remove(chosen)
        order.append(chosen)
        current = chosen
    return order


def _augment_matrices_with_path_options(
    matrices: dict[str, Any],
    payload: dict[str, Any],
    *,
    spread_quantile: float = 0.90,
) -> dict[str, Any]:
    result = dict(matrices)
    node_to_idx = {str(name): idx for idx, name in enumerate(result["node_names"])}
    n = len(result["node_names"])
    option_times: dict[tuple[int, int], list[dict[str, Any]]] = {}
    spread_samples_by_task: list[list[float]] = [[] for _ in range(n)]
    for edge in payload["logical_graph"]["edges"]:
        if not edge.get("feasible", True):
            continue
        src = node_to_idx[str(edge["from"])]
        dst = node_to_idx[str(edge["to"])]
        options: list[dict[str, Any]] = []
        for option in edge.get("path_options", []) or [edge]:
            path_type = str(option.get("path_type", option.get("best_option_by_generalized_cost", "")))
            aliases = tuple(str(alias) for alias in option.get("aliases", ()))
            travel_time = float(option.get("travel_time_min", option.get("travel_time", option.get("tau", math.inf))))
            if math.isfinite(travel_time):
                options.append(
                    {
                        "path_type": path_type,
                        "aliases": aliases,
                        "travel_time": travel_time,
                    }
                )
        if not options:
            continue
        option_times[(src, dst)] = options
        times = [float(item["travel_time"]) for item in options]
        spread = max(times) - min(times)
        if src != 0:
            spread_samples_by_task[src].append(float(spread))
        if dst != 0:
            spread_samples_by_task[dst].append(float(spread))
    spread_by_task = np.zeros(n, dtype=float)
    quantile = min(1.0, max(0.0, float(spread_quantile)))
    for task_idx, values in enumerate(spread_samples_by_task):
        if values:
            spread_by_task[task_idx] = float(np.quantile(np.asarray(values, dtype=float), quantile))
    result["path_option_times"] = option_times
    result["multi_path_time_spread"] = spread_by_task
    result["multi_path_time_spread_quantile"] = float(quantile)
    result["multi_path_time_spread_source"] = "task-adjacent path-option travel-time spread quantile"
    return result


def _sample_anchor_travel_time(
    matrices: dict[str, Any],
    src: int,
    dst: int,
    rng: np.random.Generator,
) -> float:
    options = matrices.get("path_option_times", {}).get((int(src), int(dst)))
    if not options:
        return float(matrices["time"][int(src), int(dst)])
    categories = [_anchor_path_category(option) for option in options]
    counts = Counter(categories)
    weights = np.asarray(
        [
            float(ANCHOR_PATH_CATEGORY_WEIGHTS.get(category, ANCHOR_PATH_CATEGORY_WEIGHTS["balanced"]))
            / float(max(1, counts[category]))
            for category in categories
        ],
        dtype=float,
    )
    if not np.isfinite(weights).all() or float(weights.sum()) <= 0.0:
        weights = np.ones(len(options), dtype=float)
    weights /= float(weights.sum())
    selected = options[int(rng.choice(len(options), p=weights))]
    return float(selected["travel_time"])


def _anchor_path_category(option: dict[str, Any]) -> str:
    labels = {str(option.get("path_type", "")).lower()}
    labels.update(str(alias).lower() for alias in option.get("aliases", ()))
    if {"low_energy", "eco", "energy", "p_eco"} & labels:
        return "eco"
    if {"low_time", "time", "fast", "p_time"} & labels:
        return "time"
    return "balanced"


def _time_window_anchor_policy_payload(
    task_count: int,
    *,
    mode: str,
    smart_jitter_spread_quantile: float,
) -> dict[str, Any]:
    base = {
        "mode": str(mode),
        "wave_count": _wave_count(int(task_count)),
        "smart_jitter": (
            "window width floor includes the task-adjacent path-option travel-time spread "
            f"quantile={float(smart_jitter_spread_quantile):.3f}"
        ),
        "monte_carlo_audit_note": "Time/energy sample intervals are generation-screening diagnostics only, not solver proof logic.",
    }
    if mode == "greedy-anchor":
        base.update(
            {
                "type": "nearest_neighbor_random_path_sortie_arrival_anchor",
                "max_tasks_per_sortie": _anchor_max_tasks_per_sortie(),
                "fleet_size_estimate": _fleet_size_for_task_count(int(task_count)),
                "path_choice_weights": dict(ANCHOR_PATH_CATEGORY_WEIGHTS),
                "note": (
                    "Window centers follow greedy nearest-neighbor sortie arrivals; each anchor edge samples one "
                    "available path option before bounded random jitter."
                ),
            }
        )
    elif mode == "random-wave":
        base.update(
            {
                "type": "random_task_wave_anchor",
                "note": "Tasks are randomly assigned to temporal waves, then each center receives bounded jitter.",
            }
        )
    else:
        base.update(
            {
                "type": "depot_sector_wave_anchor",
                "note": "Tasks are assigned to waves by depot-relative angular sector, with distance-biased bounded jitter.",
            }
        )
    return base


def _anchor_max_tasks_per_sortie() -> int:
    return 6


def _fleet_size_for_task_count(task_count: int) -> int:
    return max(1, min(3, math.ceil(max(1, int(task_count)) / 6)))


def _wave_count(task_count: int) -> int:
    if task_count <= 5:
        return 3
    if task_count <= 10:
        return 5
    if task_count <= 20:
        return 7
    if task_count <= 30:
        return 8
    if task_count <= 50:
        return 10
    return 12


def _tail_reserve(task_count: int) -> float:
    if task_count <= 5:
        return 110.0
    if task_count <= 10:
        return 95.0
    if task_count <= 20:
        return 80.0
    return 65.0


def _time_window_audit_budgeted(
    scenario: dict[str, Any],
    matrices: dict[str, Any],
    *,
    task_count: int,
    seed: int,
    exact_task_limit: int,
    triple_sample_count: int,
) -> dict[str, Any]:
    windows = _task_windows(scenario)
    n = int(task_count)
    rng = np.random.default_rng(int(seed))
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
        if n <= int(exact_task_limit):
            triple_subsets: Iterable[tuple[int, ...]] = combinations(range(1, n + 1), 3)
            triple_sampled = False
        else:
            triple_subsets = _sample_unique_subsets(n, 3, sample_count=max(1, int(triple_sample_count)), rng=rng)
            triple_sampled = True
        for subset in triple_subsets:
            triple_total += 1
            if any(_sequence_time_feasible(order, matrices, windows, scenario) for order in permutations(subset)):
                triple_feasible += 1
    else:
        triple_sampled = False
    widths = [due - ready for ready, due in windows.values()]
    horizon = float(scenario.get("scheduling", {}).get("horizon_min", 720.0))
    window_width_ratios = [float(width) / float(horizon) for width in widths] if horizon > 0.0 else []
    spread = np.asarray(matrices.get("multi_path_time_spread", np.zeros(n + 1, dtype=float)), dtype=float)
    spread_ratios = []
    for task_id in range(1, n + 1):
        width = float(windows[task_id][1] - windows[task_id][0])
        if width > 1.0e-9:
            spread_ratios.append(float(spread[task_id]) / width)
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
        "time_pair_estimate": _ratio_estimate_payload(pair_feasible, pair_total, sampled=False),
        "time_triple_feasible_count": triple_feasible,
        "time_triple_total_count": triple_total,
        "time_triple_estimate": _ratio_estimate_payload(triple_feasible, triple_total, sampled=bool(triple_sampled)),
        "time_triple_audit_sampled": bool(triple_sampled),
        "window_width_median": round(float(np.median(widths)), 6) if widths else 0.0,
        "window_width_to_horizon_distribution": _distribution(window_width_ratios),
        "multi_path_spread_to_window_width_distribution": _distribution(spread_ratios),
        "multi_path_spread_quantile": round(float(matrices.get("multi_path_time_spread_quantile", 1.0)), 6),
        "window_overlap_density": round(0.0 if pair_total == 0 else overlap_pairs / pair_total, 6),
    }


def _task_windows(scenario: dict[str, Any]) -> dict[int, tuple[float, float]]:
    windows: dict[int, tuple[float, float]] = {}
    for task in scenario["tasks"]:
        task_id = int(str(task["id"]).split("_", 1)[1])
        windows[task_id] = (float(task["ready_time_min"]), float(task["due_time_min"]))
    return windows


def _export_gnn_tensors(
    *,
    graph_path: Path,
    output_root: Path,
    instance_id: str,
    terrain: str,
    task_count: int,
    seed: int,
    scenario_path: Path,
    tensor_format: str,
) -> dict[str, Any]:
    if tensor_format == "none":
        return {"format": "none"}
    try:
        from BPC_future.learning.graph_builder import FutureGraphBuilder

        graph = FutureGraphBuilder().build_from_json(graph_path)
        tensor_dict = _graph_tensor_dict(
            graph,
            instance_id=instance_id,
            terrain=terrain,
            task_count=int(task_count),
            seed=int(seed),
            scenario_path=scenario_path,
            logical_graph_path=graph_path,
        )
    except Exception as exc:
        tensor_dict = _raw_logical_graph_tensor_dict(
            graph_path=graph_path,
            instance_id=instance_id,
            terrain=terrain,
            task_count=int(task_count),
            seed=int(seed),
            scenario_path=scenario_path,
            build_error=exc,
            require_torch=tensor_format in {"both", "pt"},
        )
    tensor_root = output_root / "gnn_tensors"
    pt_path = tensor_root / "pt" / f"{instance_id}.pt"
    npz_path = tensor_root / "npz" / f"{instance_id}.npz"
    meta_path = tensor_root / "meta" / f"{instance_id}.json"
    result: dict[str, Any] = {
        "format": tensor_format,
        "shape": {
            "x": list(tensor_dict["x"].shape),
            "pair_edge_index": list(tensor_dict["pair_edge_index"].shape),
            "option_feat": list(tensor_dict["option_feat"].shape),
            "option_pair_id": list(tensor_dict["option_pair_id"].shape),
        },
        "node_feature_schema": list(tensor_dict["node_feature_schema"]),
        "option_feature_schema": list(tensor_dict["option_feature_schema"]),
        "tensor_builder": str(tensor_dict["tensor_builder"]),
    }
    if tensor_format in {"both", "pt"}:
        import torch

        pt_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(tensor_dict, pt_path)
        result["pt"] = str(pt_path)
    if tensor_format in {"both", "npz"}:
        npz_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            npz_path,
            x=_tensor_to_numpy(tensor_dict["x"]),
            pair_edge_index=_tensor_to_numpy(tensor_dict["pair_edge_index"]),
            option_feat=_tensor_to_numpy(tensor_dict["option_feat"]),
            option_pair_id=_tensor_to_numpy(tensor_dict["option_pair_id"]),
            task_ids=_tensor_to_numpy(tensor_dict["task_ids"]),
            task_mask=_tensor_to_numpy(tensor_dict["task_mask"]),
            node_ids=_tensor_to_numpy(tensor_dict["node_ids"]),
            node_feature_schema=np.asarray(tensor_dict["node_feature_schema"], dtype=str),
            option_feature_schema=np.asarray(tensor_dict["option_feature_schema"], dtype=str),
        )
        result["npz"] = str(npz_path)
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_payload = {
        key: value
        for key, value in tensor_dict.items()
        if key
        in {
            "instance_id",
            "terrain",
            "task_count",
            "seed",
            "scenario_path",
            "logical_graph_path",
            "node_feature_schema",
            "option_feature_schema",
            "tensor_builder",
        }
    }
    meta_payload["shape"] = result["shape"]
    meta_path.write_text(json.dumps(meta_payload, indent=2, sort_keys=True), encoding="utf-8")
    result["meta"] = str(meta_path)
    return result


def _graph_tensor_dict(
    graph: Any,
    *,
    instance_id: str,
    terrain: str,
    task_count: int,
    seed: int,
    scenario_path: Path,
    logical_graph_path: Path,
) -> dict[str, Any]:
    return {
        "x": graph.x.detach().cpu(),
        "pair_edge_index": graph.pair_edge_index.detach().cpu(),
        "option_feat": graph.option_feat.detach().cpu(),
        "option_pair_id": graph.option_pair_id.detach().cpu(),
        "task_ids": graph.task_ids.detach().cpu(),
        "task_mask": graph.task_mask.detach().cpu(),
        "node_ids": graph.node_ids.detach().cpu(),
        "node_feature_schema": list(graph.node_feature_schema),
        "option_feature_schema": list(graph.option_feature_schema),
        "instance_id": str(instance_id),
        "terrain": str(terrain),
        "task_count": int(task_count),
        "seed": int(seed),
        "scenario_path": str(scenario_path),
        "logical_graph_path": str(logical_graph_path),
        "tensor_builder": "FutureGraphBuilder",
    }


def _tensor_to_numpy(value: Any) -> np.ndarray:
    if hasattr(value, "detach"):
        return value.detach().cpu().numpy()
    return np.asarray(value)


def _raw_logical_graph_tensor_dict(
    *,
    graph_path: Path,
    instance_id: str,
    terrain: str,
    task_count: int,
    seed: int,
    scenario_path: Path,
    build_error: Exception,
    require_torch: bool,
) -> dict[str, Any]:
    torch_module: Any | None
    try:
        import torch as torch_module
    except Exception as exc:
        if require_torch:
            raise ImportError("tensor_format='both' or 'pt' requires torch when FutureGraphBuilder is unavailable") from exc
        torch_module = None

    payload = json.loads(Path(graph_path).read_text(encoding="utf-8"))
    scenario = _scenario_payload_for_raw_tensor(payload, scenario_path)
    logical = payload["logical_graph"]
    nodes = _ordered_logical_nodes(logical)
    node_positions = {str(node["id"]): index for index, node in enumerate(nodes)}
    task_payloads = {str(task["id"]): task for task in scenario["tasks"]}
    horizon = float(scenario.get("scheduling", {}).get("horizon_min", scenario.get("vehicle", {}).get("H", 720.0)))

    node_features: list[list[float]] = []
    task_ids: list[int] = []
    task_mask: list[bool] = []
    node_ids: list[int] = []
    for node in nodes:
        node_id = str(node["id"])
        if node_id == "depot":
            depot = scenario.get("depot", node)
            xy = _xy_from_payload(depot)
            node_features.append([0.0, 0.0, 0.0, horizon, xy[0], xy[1], 1.0, 0.0, 0.0])
            task_mask.append(False)
            node_ids.append(0)
            continue
        task = task_payloads[node_id]
        task_id = int(node_id.split("_", 1)[1]) if node_id.startswith("task_") else int("".join(ch for ch in node_id if ch.isdigit()))
        xy = _xy_from_payload(task)
        node_features.append(
            [
                _numeric(task, ("demand", "d", "quantity"), default=1.0),
                _numeric(task, ("service_time", "service_time_min", "sigma"), default=0.0),
                _numeric(task, ("time_window_start", "ready_time", "ready_time_min", "r"), default=0.0),
                _numeric(task, ("time_window_end", "due_time", "due_time_min", "D"), default=horizon),
                xy[0],
                xy[1],
                0.0,
                _numeric(task, ("service_energy", "service_energy_proxy", "g"), default=0.0),
                _numeric(task, ("local_risk", "risk"), default=_numeric(node, ("risk",), default=0.0)),
            ]
        )
        task_ids.append(task_id)
        task_mask.append(True)
        node_ids.append(task_id)

    pair_edges: list[tuple[int, int]] = []
    option_features: list[list[float]] = []
    option_pair_id: list[int] = []
    for edge in logical["edges"]:
        if not edge.get("feasible", True):
            continue
        src = str(edge["from"])
        dst = str(edge["to"])
        pair_id = len(pair_edges)
        pair_edges.append((node_positions[src], node_positions[dst]))
        options = edge.get("path_options") or [edge]
        option_count = len(options)
        for rank, option in enumerate(options):
            option_features.append(_raw_option_features(option, rank=rank, option_count=option_count))
            option_pair_id.append(pair_id)

    return {
        "x": _array_or_tensor(node_features, dtype="float32", torch_module=torch_module),
        "pair_edge_index": _pair_index_array_or_tensor(pair_edges, torch_module=torch_module),
        "option_feat": _array_or_tensor(option_features, dtype="float32", torch_module=torch_module),
        "option_pair_id": _array_or_tensor(option_pair_id, dtype="int64", torch_module=torch_module),
        "task_ids": _array_or_tensor(task_ids, dtype="int64", torch_module=torch_module),
        "task_mask": _array_or_tensor(task_mask, dtype="bool", torch_module=torch_module),
        "node_ids": _array_or_tensor(node_ids, dtype="int64", torch_module=torch_module),
        "node_feature_schema": list(NODE_FEATURE_SCHEMA),
        "option_feature_schema": list(OPTION_FEATURE_SCHEMA),
        "instance_id": str(instance_id),
        "terrain": str(terrain),
        "task_count": int(task_count),
        "seed": int(seed),
        "scenario_path": str(scenario_path),
        "logical_graph_path": str(graph_path),
        "tensor_builder": f"raw_logical_graph_fallback:{type(build_error).__name__}",
    }


def _array_or_tensor(values: Any, *, dtype: str, torch_module: Any | None) -> Any:
    if torch_module is not None:
        torch_dtype = {
            "float32": torch_module.float32,
            "int64": torch_module.long,
            "bool": torch_module.bool,
        }[dtype]
        return torch_module.tensor(values, dtype=torch_dtype)
    return np.asarray(values, dtype=dtype)


def _pair_index_array_or_tensor(pair_edges: list[tuple[int, int]], *, torch_module: Any | None) -> Any:
    if torch_module is not None:
        return torch_module.tensor(pair_edges, dtype=torch_module.long).t().contiguous()
    return np.asarray(pair_edges, dtype="int64").T.copy()


def _scenario_payload_for_raw_tensor(payload: dict[str, Any], scenario_path: Path) -> dict[str, Any]:
    scenario = payload.get("scenario")
    if isinstance(scenario, dict) and "tasks" in scenario and "depot" in scenario:
        return scenario
    return json.loads(Path(scenario_path).read_text(encoding="utf-8"))


def _ordered_logical_nodes(logical: dict[str, Any]) -> list[dict[str, Any]]:
    nodes = list(logical["nodes"])
    nodes.sort(key=lambda node: _logical_node_sort_key(str(node["id"])))
    if not nodes or str(nodes[0]["id"]) != "depot":
        nodes = [node for node in nodes if str(node["id"]) == "depot"] + [node for node in nodes if str(node["id"]) != "depot"]
    return nodes


def _logical_node_sort_key(node_id: str) -> tuple[int, int | str]:
    if node_id == "depot":
        return (0, 0)
    if node_id.startswith("task_"):
        return (1, int(node_id.split("_", 1)[1]))
    digits = "".join(ch for ch in node_id if ch.isdigit())
    return (1, int(digits) if digits else node_id)


def _xy_from_payload(payload: dict[str, Any]) -> tuple[float, float]:
    xy = payload.get("xy_km", payload.get("xy"))
    if xy is None:
        raise ValueError("payload missing xy_km")
    return float(xy[0]), float(xy[1])


def _numeric(payload: dict[str, Any], keys: tuple[str, ...], *, default: float) -> float:
    for key in keys:
        if key in payload:
            return float(payload[key])
    return float(default)


def _raw_option_features(option: dict[str, Any], *, rank: int, option_count: int) -> list[float]:
    path_type = str(option.get("path_type", option.get("best_option_by_generalized_cost", "")))
    aliases = {str(value) for value in option.get("aliases", ())}
    aliases.add(path_type)
    return [
        _numeric(option, ("distance", "distance_km", "path_distance_km"), default=0.0),
        _numeric(option, ("travel_time", "travel_time_min", "time_min", "tau"), default=0.0),
        _numeric(option, ("energy", "energy_proxy"), default=0.0),
        _numeric(option, ("risk", "risk_integral"), default=0.0),
        _numeric(option, ("generalized_cost", "option_cost", "cost"), default=0.0),
        1.0 if "low_time" in aliases else 0.0,
        1.0 if "low_energy" in aliases else 0.0,
        1.0 if "low_risk" in aliases else 0.0,
        float(rank),
        float(option_count),
    ]


def _ratio_estimate_payload(feasible: int, total: int, *, sampled: bool) -> dict[str, Any]:
    feasible = int(feasible)
    total = int(total)
    estimate = 0.0 if total <= 0 else float(feasible) / float(total)
    if total <= 0:
        variance = 0.0
        low = 0.0
        high = 0.0
    else:
        variance = estimate * (1.0 - estimate) / float(total)
        z = WILSON_Z_95
        denom = 1.0 + z * z / float(total)
        center = (estimate + z * z / (2.0 * float(total))) / denom
        half = (
            z
            * math.sqrt((estimate * (1.0 - estimate) / float(total)) + (z * z / (4.0 * float(total) * float(total))))
            / denom
        )
        low = max(0.0, center - half)
        high = min(1.0, center + half)
    return {
        "estimate": round(float(estimate), 6),
        "feasible_count": feasible,
        "sample_count": total,
        "estimated_variance": round(float(variance), 10),
        "wilson95_low": round(float(low), 6),
        "wilson95_high": round(float(high), 6),
        "audit_type": "monte_carlo_screen" if sampled else "exact_enumeration",
        "proof_scope": "generation_screening_only_not_solver_certificate",
    }


def _distribution(values: Sequence[float]) -> dict[str, Any]:
    array = np.asarray([float(value) for value in values if math.isfinite(float(value))], dtype=float)
    if array.size == 0:
        return {
            "count": 0,
            "mean": 0.0,
            "std": 0.0,
            "min": 0.0,
            "p25": 0.0,
            "median": 0.0,
            "p75": 0.0,
            "max": 0.0,
        }
    return {
        "count": int(array.size),
        "mean": round(float(np.mean(array)), 6),
        "std": round(float(np.std(array)), 6),
        "min": round(float(np.min(array)), 6),
        "p25": round(float(np.quantile(array, 0.25)), 6),
        "median": round(float(np.median(array)), 6),
        "p75": round(float(np.quantile(array, 0.75)), 6),
        "max": round(float(np.max(array)), 6),
    }


def _manifest_generation_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    attempts = list(manifest.get("attempts", []))
    instances = list(manifest.get("instances", []))
    groups: dict[str, dict[str, Any]] = {}
    for attempt in attempts:
        key = _summary_group_key(
            int(attempt.get("task_count", 0)),
            str(attempt.get("time_window_mode", "unknown")),
            str(attempt.get("terrain", "unknown")),
        )
        group = groups.setdefault(key, _empty_summary_group(attempt))
        group["attempt_count"] += 1
        if str(attempt.get("status")) == "accepted":
            group["accepted_count"] += 1
        else:
            group["skipped_count"] += 1
            reason = str(attempt.get("reason_bucket", "unknown"))
            group["skip_reason_counts"][reason] = group["skip_reason_counts"].get(reason, 0) + 1
    for instance in instances:
        key = _summary_group_key(
            int(instance.get("task_count", 0)),
            str(instance.get("time_window_mode", "unknown")),
            str(instance.get("terrain", "unknown")),
        )
        group = groups.setdefault(key, _empty_summary_group(instance))
        audit = dict(instance.get("balanced_audit", {}))
        for field in (
            "time_pair_feasible_ratio",
            "time_triple_feasible_ratio",
            "energy_pair_feasible_ratio",
            "energy_triple_feasible_ratio",
            "energy_quad_feasible_ratio",
            "energy_large_feasible_ratio",
            "window_width_median_ratio",
        ):
            if field in audit:
                group["_values"].setdefault(field, []).append(float(audit[field]))
        window_dist = audit.get("window_width_to_horizon_distribution", {})
        spread_dist = audit.get("multi_path_spread_to_window_width_distribution", {})
        for source, field in (
            (window_dist, "window_width_to_horizon_median"),
            (spread_dist, "multi_path_spread_to_window_width_median"),
        ):
            if isinstance(source, dict) and "median" in source:
                group["_values"].setdefault(field, []).append(float(source["median"]))
    for group in groups.values():
        attempt_count = int(group["attempt_count"])
        group["acceptance_rate"] = round(0.0 if attempt_count == 0 else group["accepted_count"] / attempt_count, 6)
        group["metric_distributions"] = {
            field: _distribution(values) for field, values in sorted(group.pop("_values").items())
        }
        group["skip_reason_counts"] = dict(sorted(group["skip_reason_counts"].items()))
    return {
        "group_by_task_mode_terrain": dict(sorted(groups.items())),
        "note": (
            "All accepted and skipped attempts are retained. Monte Carlo sample intervals are generation-screening "
            "diagnostics only and are not solver proof/certificate logic."
        ),
    }


def _summary_group_key(task_count: int, mode: str, terrain: str) -> str:
    return f"tasks={int(task_count):03d}|mode={mode}|terrain={terrain}"


def _empty_summary_group(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_count": int(source.get("task_count", 0)),
        "time_window_mode": str(source.get("time_window_mode", "unknown")),
        "terrain": str(source.get("terrain", "unknown")),
        "attempt_count": 0,
        "accepted_count": 0,
        "skipped_count": 0,
        "skip_reason_counts": {},
        "_values": {},
    }


def _attempt_record(
    *,
    status: str,
    terrain: str,
    task_count: int,
    time_window_mode: str,
    sample_index: int,
    attempt_index: int,
    seed: int,
    instance_id: str | None = None,
    reason_bucket: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "status": str(status),
        "terrain": str(terrain),
        "task_count": int(task_count),
        "time_window_mode": str(time_window_mode),
        "sample_index": int(sample_index),
        "attempt_index": int(attempt_index),
        "seed": int(seed),
    }
    if instance_id is not None:
        record["instance_id"] = str(instance_id)
    if reason_bucket is not None:
        record["reason_bucket"] = str(reason_bucket)
    if reason is not None:
        record["reason"] = str(reason)
    return record


def _mode_slug(mode: str) -> str:
    return str(mode).replace("_", "-").replace(" ", "-")


def _minimum_task_spacing_km(scenario: dict[str, Any]) -> float:
    tasks = scenario.get("tasks", [])
    if len(tasks) < 2:
        return math.inf
    best = math.inf
    for left, right in combinations(tasks, 2):
        xy_l = left["xy_km"]
        xy_r = right["xy_km"]
        best = min(best, float(np.hypot(float(xy_l[0]) - float(xy_r[0]), float(xy_l[1]) - float(xy_r[1]))))
    return best


def _skip_reason_bucket(exc: Exception) -> str:
    message = str(exc)
    if ":" in message:
        message = message.split(":", 1)[0]
    return message[:120]


def _log_skip(terrain_name: str, task_count: int, seed: int, exc: Exception, *, time_window_mode: str) -> None:
    print(
        json.dumps(
            {
                "event": "skip",
                "terrain": terrain_name,
                "task_count": int(task_count),
                "time_window_mode": str(time_window_mode),
                "seed": int(seed),
                "reason": str(exc),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

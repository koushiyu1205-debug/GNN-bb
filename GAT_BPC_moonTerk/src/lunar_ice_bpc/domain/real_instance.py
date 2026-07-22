"""Real-map lunar water-ice instance generation."""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
from collections import Counter
from pathlib import Path
import tempfile
from typing import Any

from lunar_ice_bpc.domain.real_maps import (
    DEFAULT_SP50_DEPOT_CENTER_KM,
    REAL_MAP_GENERATOR_ID,
    build_real_map_edge_options,
    build_real_map_preview,
    _real_map_edge_checkpoint_fingerprint,
)
from lunar_ice_bpc.domain.scenario import (
    ACTIVE_FOOTPRINT_BY_SCALE,
    FLEET_BY_SCALE,
    HORIZON_BY_SCALE,
    MEAN_WINDOW_WIDTH_CAP_BY_SCALE,
    OPERATION_MODE_SPECS,
    PATH_OPTION_POLICY_ID,
    RISK_SCHEMA_VERSION,
    SHADOW_CAP_BY_SCALE,
    TIME_WINDOW_POLICY_ID,
    WINDOW_WIDTH_CAP_BY_SCALE,
    LunarIceConfig,
    scale_label,
    snap_up,
)


REAL_MAP_INSTANCE_INPUT_CHECKPOINT_SCHEMA_VERSION = "lunar_ice_bpc.real_map_instance_input_checkpoint.v1"
from lunar_ice_bpc.domain.scheduling import (
    _apply_time_windows,
    _build_reference_solution,
    _edge_lookup,
    _objective,
)


def generate_real_map_instance(
    scale: int,
    *,
    raw_map_dir: str | Path,
    seed: int,
    index: int = 1,
    config: LunarIceConfig | None = None,
    center_x_km: float | None = None,
    center_y_km: float | None = None,
    extent_km: float | None = None,
    output_cells: int | None = None,
    time_window_mode: str | None = None,
    edge_checkpoint_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Generate one fixed three-path logical graph from real LOLA raster layers."""

    config = config or LunarIceConfig()
    scale = int(scale)
    label = scale_label(scale)
    rng = random.Random(int(seed))
    extent = float(extent_km if extent_km is not None else config.resource_map_extent_km)
    cells = int(output_cells if output_cells is not None else round(extent * 1000.0 / float(config.synthetic_grid_resolution_m)))
    time_mode = time_window_mode or _time_window_mode_for_index(index)
    active_footprint_km = ACTIVE_FOOTPRINT_BY_SCALE[scale]
    depot_selection = _resolve_depot_center(
        raw_map_dir=raw_map_dir,
        center_x_km=center_x_km,
        center_y_km=center_y_km,
    )
    center_x = float(depot_selection["center_x_km"])
    center_y = float(depot_selection["center_y_km"])
    candidate_pool_count = _candidate_pool_count(scale)
    preview = build_real_map_preview(
        raw_map_dir=raw_map_dir,
        center_x_km=center_x,
        center_y_km=center_y,
        extent_km=extent,
        output_cells=cells,
        target_count=candidate_pool_count,
        path_target_count=0,
        active_footprint_km=active_footprint_km,
    )
    if preview["status"] != "REAL_MAP_PREVIEW_READY":
        return {
            "schema_version": "lunar_ice_bpc.instance.v1",
            "instance_id": f"lunar_ice_sp50_{label}_{index:03d}_seed{int(seed)}",
            "scale": scale,
            "seed": int(seed),
            "validation": {
                "accepted": False,
                "reason": "real_map_preview_not_ready",
                "preview_status": preview["status"],
                "missing_required_lola_layers": preview.get("missing_required_lola_layers", []),
            },
        }
    if len(preview["targets"]) < scale:
        return {
            "schema_version": "lunar_ice_bpc.instance.v1",
            "instance_id": f"lunar_ice_sp50_{label}_{index:03d}_seed{int(seed)}",
            "scale": scale,
            "seed": int(seed),
            "validation": {
                "accepted": False,
                "reason": "not_enough_real_map_targets",
                "target_count": len(preview["targets"]),
                "required_target_count": scale,
            },
        }

    depot_xy = tuple(float(value) for value in preview["depot"]["xy_km"])
    checkpoint_root = Path(edge_checkpoint_dir) if edge_checkpoint_dir is not None else None
    input_checkpoint = checkpoint_root / "instance_input.json" if checkpoint_root is not None else None
    checkpoint_payload = _load_real_instance_input_checkpoint(
        input_checkpoint,
        scale=scale,
        seed=seed,
        index=index,
        time_window_mode=time_mode,
        preview_targets=preview["targets"],
        depot_xy=depot_xy,
    )
    checkpoint_status = "reused"
    if checkpoint_payload is None:
        sampled_targets = _recover_targets_from_edge_checkpoints(
            checkpoint_root,
            preview_targets=preview["targets"],
            scale=scale,
            raw_map_dir=raw_map_dir,
            depot_xy=depot_xy,
            center_x_km=center_x,
            center_y_km=center_y,
            extent_km=extent,
            output_cells=cells,
        )
        checkpoint_status = "recovered" if sampled_targets is not None else "generated"
        if sampled_targets is None:
            sampled_targets = _sample_targets_with_mission_screen(preview["targets"], scale, rng, depot_xy)
    else:
        sampled_by_id = {str(target["id"]): target for target in preview["targets"]}
        sampled_targets = [sampled_by_id[target_id] for target_id in checkpoint_payload["sampled_target_ids"]]
    missing_roles = _missing_required_candidate_roles(sampled_targets)
    if missing_roles:
        return {
            "schema_version": "lunar_ice_bpc.instance.v1",
            "instance_id": f"lunar_ice_sp50_{label}_{index:03d}_seed{int(seed)}",
            "scale": scale,
            "seed": int(seed),
            "validation": {
                "accepted": False,
                "reason": "sampled_candidate_roles_missing",
                "missing_candidate_roles": missing_roles,
                "sampled_candidate_role_counts": dict(
                    sorted(Counter(str(target.get("candidate_role", "")) for target in sampled_targets).items())
                ),
            },
        }
    if checkpoint_payload is None:
        tasks = _real_task_payloads(sampled_targets, scale, rng)
        _write_real_instance_input_checkpoint(
            input_checkpoint,
            scale=scale,
            seed=seed,
            index=index,
            time_window_mode=time_mode,
            preview_targets=preview["targets"],
            depot_xy=depot_xy,
            sampled_targets=sampled_targets,
            tasks=tasks,
        )
    else:
        tasks = checkpoint_payload["tasks"]
    if input_checkpoint is not None:
        print(
            f"[real-map instance checkpoint] status={checkpoint_status} path={input_checkpoint}",
            flush=True,
        )
    nodes = {"depot": depot_xy}
    nodes.update({task_id: tuple(task["xy_km"]) for task_id, task in tasks.items()})
    edges = build_real_map_edge_options(
        raw_map_dir=raw_map_dir,
        nodes=nodes,
        center_x_km=center_x,
        center_y_km=center_y,
        extent_km=extent,
        output_cells=cells,
        checkpoint_dir=edge_checkpoint_dir,
    )
    task_order = _task_order_for_time_window_mode(tasks, depot_xy, time_mode)
    reference = _build_reference_solution(tasks, _edge_lookup(edges), config, scale, task_order=task_order)
    instance = {
        "schema_version": "lunar_ice_bpc.instance.v1",
        "instance_id": f"lunar_ice_sp50_{label}_{index:03d}_seed{int(seed)}",
        "scale": scale,
        "seed": int(seed),
        "resource_map": {
            "type": "real_lunar_south_pole_raster",
            "benchmark_id": "lunar_ice_sp50_real_map_v1",
            "generator": REAL_MAP_GENERATOR_ID,
            "risk_schema_version": RISK_SCHEMA_VERSION,
            "extent_km": float(extent),
            "resolution_m": float(preview["roi"]["output_resolution_m"]),
            "grid_shape": [int(cells), int(cells)],
            "active_footprint_km": active_footprint_km,
            "center_x_km": float(center_x),
            "center_y_km": float(center_y),
            "depot_global_xy_km": [round(center_x, 6), round(center_y, 6)],
            "source_catalog_id": preview["source_catalog"]["catalog_id"],
            "ready_required_lola_layers": preview["ready_required_lola_layers"],
            "native_layer_status": preview["layer_status"],
            "depot_selection": depot_selection,
            "candidate_pool_policy": "water_ice_hotspot_directional_sampling_v1",
            "candidate_pool_count": len(preview["targets"]),
            "sampled_target_count": len(sampled_targets),
            "sampled_hotspot_count": len({str(target.get("hotspot_id", target["id"])) for target in sampled_targets}),
            "sampled_direction_sector_count": len({int(target.get("direction_sector", -1)) for target in sampled_targets}),
            "preview": _downsample_matrix(preview["preview_layers"]["resource_index"], cells=180),
            "risk_preview": _downsample_matrix(preview["preview_layers"]["risk_index"], cells=180),
            "dem_preview": _downsample_matrix(preview["preview_layers"].get("elevation_index", []), cells=180),
        },
        "depot": {
            **preview["depot"],
            "global_xy_km": [round(center_x, 6), round(center_y, 6)],
        },
        "vehicle": {
            "fleet_size": FLEET_BY_SCALE[scale],
            "Q_ice": config.q_ice,
            "B_use": config.b_use,
            "energy_unit": config.energy_unit,
            "max_tasks_per_trip": config.max_tasks_per_trip,
            "dock_overhead_min": config.dock_overhead_min,
            "recharge_power_proxy_per_min": config.recharge_power_proxy_per_min,
            "depot_chargers": config.depot_chargers,
            "max_shadow_exposure_per_sortie": SHADOW_CAP_BY_SCALE[scale],
        },
        "scheduling": {
            "horizon_min": HORIZON_BY_SCALE[scale],
            "time_bucket_size": config.time_bucket_size,
            "time_window_policy_id": TIME_WINDOW_POLICY_ID,
            "time_window_mode": time_mode,
            "time_window_mode_split": "outer_to_inner:7, inner_to_outer:7, easy_to_hard:6 per 20 seeds",
            "operation_modes": list(OPERATION_MODE_SPECS.keys()),
            "operation_mode_mix": {mode: spec.ratio for mode, spec in OPERATION_MODE_SPECS.items()},
            "objective": {
                "mode": "weighted_discovery_completion",
                "alpha_discovery_completion": config.objective_alpha_discovery_completion,
                "beta_journey_end_time": config.objective_beta_journey_end_time,
                "gamma_lunar_ice_risk": config.objective_gamma_lunar_ice_risk,
                "delta_energy": config.objective_delta_energy,
            },
        },
        "tasks": tasks,
        "logical_graph": {
            "path_option_policy_id": PATH_OPTION_POLICY_ID,
            "nodes": [{"id": node_id, "xy_km": [round(xy[0], 6), round(xy[1], 6)]} for node_id, xy in nodes.items()],
            "edges": edges,
        },
        "reference_solution": reference,
    }
    if reference["status"] != "FEASIBLE_REFERENCE":
        instance["validation"] = {
            "accepted": False,
            "reason": "reference_solution_infeasible",
            "time_window_policy_id": TIME_WINDOW_POLICY_ID,
            "time_window_mode": time_mode,
            "risk_schema_version": RISK_SCHEMA_VERSION,
        }
        return instance
    _apply_time_windows(instance, config)
    instance["reference_solution"]["objective"] = _objective(instance, config)
    instance["validation"] = _real_validation_payload(instance, config, scale)
    return instance


def _real_task_payloads(targets: list[dict[str, Any]], scale: int, rng: random.Random) -> dict[str, dict[str, Any]]:
    modes_by_candidate_id = _assign_operation_modes(targets, scale)
    raw_tasks: list[dict[str, Any]] = []
    for index, target in enumerate(targets):
        mode = modes_by_candidate_id[target["id"]]
        spec = OPERATION_MODE_SPECS[mode]
        resource_score = float(target["resource_score"])
        risk_score = float(target["risk_score"])
        shadow_score = float(target.get("local_shadow_score", risk_score))
        terrain_risk = float(target.get("local_terrain_risk", risk_score))
        interior_score = float(target.get("psr_interior_score", 0.0))
        boundary_score = float(target.get("psr_boundary_score", 0.0))
        service_time = rng.uniform(*spec.service_time_min)
        service_energy = rng.uniform(*spec.service_energy_proxy)
        expected_ice = 5.0 + 45.0 * (0.70 * resource_score + 0.30 * interior_score)
        task = {
            "id": f"ice_site_{index + 1:03d}",
            "kind": "psr_water_ice_target",
            "xy_km": [round(float(target["xy_km"][0]), 6), round(float(target["xy_km"][1]), 6)],
            "expected_ice_kg": round(expected_ice, 6),
            "ice_confidence": round(resource_score, 6),
            "science_weight": 1.0,
            "operation_mode": mode,
            "planned_depth_m": round(0.0 if mode == "detect" else rng.uniform(0.15, 1.0 if mode == "sample" else 2.0), 6),
            "planned_sample_mass_kg": round(0.0 if mode == "detect" else rng.uniform(0.25, 2.0 if mode == "sample" else 4.0), 6),
            "local_shadow_score": round(shadow_score, 6),
            "local_thermal_risk": round(shadow_score, 6),
            "local_slope_risk": round(terrain_risk, 6),
            "psr_boundary_score": round(boundary_score, 6),
            "psr_interior_score": round(interior_score, 6),
            "science_zone": target.get("science_zone", "unknown"),
            "d": float(spec.demand),
            "sigma": round(service_time, 6),
            "g": round(service_energy, 6),
            "c_srv": round(0.02 * service_time + 0.10 * service_energy, 6),
            "r": 0.0,
            "D": 0.0,
            "real_map_candidate_id": target["id"],
            "real_map_selection_score": target["selection_score"],
            "hotspot_id": target.get("hotspot_id"),
            "hotspot_rank": target.get("hotspot_rank"),
            "hotspot_xy_km": target.get("hotspot_xy_km"),
            "hotspot_distance_km": target.get("hotspot_distance_km"),
            "direction_sector": target.get("direction_sector"),
            "candidate_role": target.get("candidate_role", "hotspot"),
            "candidate_suggested_operation_mode": target.get("recommended_operation_mode", "detect"),
        }
        raw_tasks.append(task)
    max_ice = max(task["expected_ice_kg"] for task in raw_tasks) or 1.0
    for task in raw_tasks:
        norm_ice = float(task["expected_ice_kg"]) / max_ice
        task["science_weight"] = round(0.6 * float(task["ice_confidence"]) + 0.4 * norm_ice, 6)
    return {task["id"]: task for task in raw_tasks}


def _preview_target_signature(targets: list[dict[str, Any]]) -> str:
    payload = [
        [str(target["id"]), [round(float(target["xy_km"][0]), 6), round(float(target["xy_km"][1]), 6)]]
        for target in targets
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_real_instance_input_checkpoint(
    path: Path | None,
    *,
    scale: int,
    seed: int,
    index: int,
    time_window_mode: str,
    preview_targets: list[dict[str, Any]],
    depot_xy: tuple[float, float],
) -> dict[str, Any] | None:
    if path is None or not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    expected = {
        "schema_version": REAL_MAP_INSTANCE_INPUT_CHECKPOINT_SCHEMA_VERSION,
        "scale": int(scale),
        "seed": int(seed),
        "index": int(index),
        "time_window_mode": str(time_window_mode),
        "preview_target_signature": _preview_target_signature(preview_targets),
        "depot_xy": [round(float(depot_xy[0]), 6), round(float(depot_xy[1]), 6)],
    }
    if any(payload.get(key) != value for key, value in expected.items()):
        return None
    target_ids = payload.get("sampled_target_ids")
    tasks = payload.get("tasks")
    if not isinstance(target_ids, list) or len(target_ids) != int(scale) or len(set(target_ids)) != int(scale):
        return None
    available_ids = {str(target["id"]) for target in preview_targets}
    if any(not isinstance(target_id, str) or target_id not in available_ids for target_id in target_ids):
        return None
    if not isinstance(tasks, dict) or list(tasks) != [f"ice_site_{offset:03d}" for offset in range(1, int(scale) + 1)]:
        return None
    return payload


def _write_real_instance_input_checkpoint(
    path: Path | None,
    *,
    scale: int,
    seed: int,
    index: int,
    time_window_mode: str,
    preview_targets: list[dict[str, Any]],
    depot_xy: tuple[float, float],
    sampled_targets: list[dict[str, Any]],
    tasks: dict[str, dict[str, Any]],
) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": REAL_MAP_INSTANCE_INPUT_CHECKPOINT_SCHEMA_VERSION,
        "scale": int(scale),
        "seed": int(seed),
        "index": int(index),
        "time_window_mode": str(time_window_mode),
        "preview_target_signature": _preview_target_signature(preview_targets),
        "depot_xy": [round(float(depot_xy[0]), 6), round(float(depot_xy[1]), 6)],
        "sampled_target_ids": [str(target["id"]) for target in sampled_targets],
        "tasks": tasks,
    }
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def _recover_targets_from_edge_checkpoints(
    checkpoint_root: Path | None,
    *,
    preview_targets: list[dict[str, Any]],
    scale: int,
    raw_map_dir: str | Path,
    depot_xy: tuple[float, float],
    center_x_km: float,
    center_y_km: float,
    extent_km: float,
    output_cells: int,
) -> list[dict[str, Any]] | None:
    if checkpoint_root is None or not checkpoint_root.is_dir():
        return None
    groups: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(checkpoint_root.glob("source_*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        fingerprint = payload.get("fingerprint")
        if isinstance(fingerprint, str) and isinstance(payload.get("edges"), list):
            groups.setdefault(fingerprint, []).append(payload)
    if not groups:
        return None
    fingerprint, payloads = max(groups.items(), key=lambda item: (len(item[1]), item[0]))
    if len(payloads) < 2:
        return None
    payload = payloads[0]
    source_id = str(payload.get("source_id", ""))
    coordinates: dict[str, tuple[float, float]] = {}
    for edge in payload["edges"]:
        if not isinstance(edge, dict) or str(edge.get("from")) != source_id:
            return None
        options = edge.get("path_options")
        if not isinstance(options, list) or not options or not isinstance(options[0], dict):
            return None
        path_xy = options[0].get("path_xy")
        if not isinstance(path_xy, list) or len(path_xy) < 2:
            return None
        coordinates[source_id] = (round(float(path_xy[0][0]), 6), round(float(path_xy[0][1]), 6))
        coordinates[str(edge.get("to"))] = (round(float(path_xy[-1][0]), 6), round(float(path_xy[-1][1]), 6))
    expected_ids = {"depot", *(f"ice_site_{offset:03d}" for offset in range(1, int(scale) + 1))}
    if set(coordinates) != expected_ids:
        return None
    targets_by_xy: dict[tuple[float, float], list[dict[str, Any]]] = {}
    for target in preview_targets:
        xy = tuple(round(float(value), 6) for value in target["xy_km"])
        targets_by_xy.setdefault(xy, []).append(target)
    recovered: list[dict[str, Any]] = []
    for offset in range(1, int(scale) + 1):
        matches = targets_by_xy.get(coordinates[f"ice_site_{offset:03d}"], [])
        if len(matches) != 1:
            return None
        recovered.append(matches[0])
    # Path endpoints are raster-cell centres.  The logical depot may be a
    # continuous ROI coordinate (for SP50 it is [25.0, 25.0]), so retain the
    # preview coordinate rather than replacing it with the snapped path point.
    nodes = {"depot": depot_xy}
    nodes.update({f"ice_site_{offset:03d}": coordinates[f"ice_site_{offset:03d}"] for offset in range(1, int(scale) + 1)})
    recovered_fingerprint = _real_map_edge_checkpoint_fingerprint(
        raw_map_dir=raw_map_dir,
        nodes=nodes,
        center_x_km=center_x_km,
        center_y_km=center_y_km,
        extent_km=extent_km,
        output_cells=output_cells,
        allow_remote=False,
    )
    return recovered if recovered_fingerprint == fingerprint else None


def _real_validation_payload(instance: dict[str, Any], config: LunarIceConfig, scale: int) -> dict[str, Any]:
    widths = [float(task["D"]) - float(task["r"]) for task in instance["tasks"].values()]
    starts: dict[str, float] = {}
    for journey in instance["reference_solution"]["journeys"]:
        for sortie in journey["sorties"]:
            starts.update({task_id: float(value) for task_id, value in sortie["service_starts"].items()})
    cap = WINDOW_WIDTH_CAP_BY_SCALE[scale]
    effective_caps = {
        task_id: max(cap, snap_up(float(task["sigma"]) + 2.0 * config.time_bucket_size, config.time_bucket_size))
        for task_id, task in instance["tasks"].items()
    }
    forced_count = sum(1 for value in effective_caps.values() if value > cap + 1.0e-9)
    windows_contain_reference = all(
        float(task["r"]) <= starts[task_id] + 1.0e-9
        and starts[task_id] + float(task["sigma"]) <= float(task["D"]) + 1.0e-9
        for task_id, task in instance["tasks"].items()
    )
    windows_meet_min_width = all(
        float(task["D"]) - float(task["r"]) >= float(task["sigma"]) + 2.0 * config.time_bucket_size - 1.0e-9
        for task in instance["tasks"].values()
    )
    windows_within_effective_cap = all(
        float(task["D"]) - float(task["r"]) <= effective_caps[task_id] + 1.0e-9
        for task_id, task in instance["tasks"].items()
    )
    mean_width = sum(widths) / max(1, len(widths))
    accepted = (
        mean_width <= MEAN_WINDOW_WIDTH_CAP_BY_SCALE[scale] + 1.0e-9
        and windows_contain_reference
        and windows_meet_min_width
        and windows_within_effective_cap
    )
    if accepted:
        validation_reason = "accepted"
    elif not windows_contain_reference:
        validation_reason = "time_window_misses_reference_service"
    elif not windows_meet_min_width:
        validation_reason = "time_window_below_min_width"
    elif not windows_within_effective_cap:
        validation_reason = "time_window_exceeds_effective_cap"
    else:
        validation_reason = "mean_window_width_too_wide"
    return {
        "accepted": bool(accepted),
        "reason": validation_reason,
        "mean_window_width": round(mean_width, 6),
        "max_window_width": round(max(widths), 6),
        "configured_window_width_cap": cap,
        "max_effective_window_width_cap": round(max(effective_caps.values()), 6),
        "forced_min_width_count": forced_count,
        "windows_contain_reference": bool(windows_contain_reference),
        "windows_meet_min_width": bool(windows_meet_min_width),
        "windows_within_effective_cap": bool(windows_within_effective_cap),
        "time_window_policy_id": TIME_WINDOW_POLICY_ID,
        "time_window_mode": instance["scheduling"].get("time_window_mode"),
        "risk_schema_version": RISK_SCHEMA_VERSION,
    }


def _resolve_depot_center(
    *,
    raw_map_dir: str | Path,
    center_x_km: float | None,
    center_y_km: float | None,
) -> dict[str, Any]:
    if center_x_km is not None and center_y_km is not None:
        return {
            "status": "DEPOT_PROVIDED",
            "center_x_km": float(center_x_km),
            "center_y_km": float(center_y_km),
            "global_xy_km": [round(float(center_x_km), 6), round(float(center_y_km), 6)],
        }
    dense_x, dense_y = DEFAULT_SP50_DEPOT_CENTER_KM
    return {
        "status": "DEPOT_DEFAULT_DENSE_WATER_ICE_RIDGE",
        "center_x_km": float(dense_x),
        "center_y_km": float(dense_y),
        "global_xy_km": [round(float(dense_x), 6), round(float(dense_y), 6)],
        "selection_policy": "fixed_sp50_dense_water_ice_depot_v1",
        "selection_note": "Default benchmark depot chosen from the dense-depot visual comparison: high-illumination ridge near denser PSR/water-ice structure.",
    }


def _candidate_pool_count(scale: int) -> int:
    return max(int(scale), min(360, max(120, int(scale) * 4)))


def _sample_targets_with_mission_screen(
    targets: list[dict[str, Any]],
    scale: int,
    rng: random.Random,
    depot_xy: tuple[float, float],
) -> list[dict[str, Any]]:
    best: list[dict[str, Any]] | None = None
    best_score = math.inf
    for _ in range(80):
        sampled = _hotspot_directional_sample(targets, scale, rng, depot_xy)
        score = _distance_screen_score(sampled, scale, depot_xy)
        if score <= 0.0:
            return sampled
        if score < best_score:
            best = sampled
            best_score = score
    return best or _hotspot_directional_sample(targets, scale, rng, depot_xy)


def _hotspot_directional_sample(
    targets: list[dict[str, Any]],
    scale: int,
    rng: random.Random,
    depot_xy: tuple[float, float],
) -> list[dict[str, Any]]:
    groups = _targets_by_hotspot(targets)
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    science_quota = _science_focus_count(scale)
    exploration_quota = max(0, int(scale) - science_quota)
    hotspot_ids = _select_hotspot_ids_for_instance(groups, science_quota, rng)
    edge_science_quota = _edge_science_focus_count(science_quota)
    role_plan = ["hotspot_edge"] * edge_science_quota + ["hotspot_core"] * max(0, science_quota - edge_science_quota)
    rng.shuffle(role_plan)
    for offset, hotspot_id in enumerate(hotspot_ids):
        preferred_role = role_plan[offset] if offset < len(role_plan) else None
        choice = _choose_target_from_hotspot(groups[hotspot_id], selected, scale, rng, depot_xy, preferred_role=preferred_role)
        if choice is None:
            continue
        selected.append(choice)
        selected_ids.add(str(choice["id"]))
        if len(selected) >= int(scale):
            break
    # ``_is_exploration_candidate`` intentionally admits promising non-labelled
    # candidates.  Pick one literal exploration site first so the formal role
    # invariant cannot be lost to weighted selection from that broader pool.
    literal_exploration_pool = [
        target
        for target in targets
        if str(target["id"]) not in selected_ids and str(target.get("candidate_role", "")) == "exploration"
    ]
    selected_has_exploration = any(str(target.get("candidate_role", "")) == "exploration" for target in selected)
    if literal_exploration_pool and not selected_has_exploration and len(selected) < int(scale) and exploration_quota > 0:
        choice = _choose_exploration_target(literal_exploration_pool, selected, scale, rng, depot_xy)
        selected.append(choice)
        selected_ids.add(str(choice["id"]))
        exploration_quota -= 1
    exploration_pool = [
        target
        for target in targets
        if str(target["id"]) not in selected_ids and _is_exploration_candidate(target)
    ]
    while exploration_pool and len(selected) < int(scale) and exploration_quota > 0:
        choice = _choose_exploration_target(exploration_pool, selected, scale, rng, depot_xy)
        selected.append(choice)
        selected_ids.add(str(choice["id"]))
        exploration_quota -= 1
        exploration_pool = [target for target in exploration_pool if str(target["id"]) != str(choice["id"])]
    remaining = [target for target in targets if str(target["id"]) not in selected_ids]
    while remaining and len(selected) < int(scale):
        choice = _weighted_fill_target(remaining, selected, scale, rng, depot_xy)
        selected.append(choice)
        selected_ids.add(str(choice["id"]))
        remaining = [target for target in remaining if str(target["id"]) != str(choice["id"])]
    selected.sort(key=lambda item: (int(item.get("hotspot_rank", 9999)), str(item["id"])))
    return selected


def _missing_required_candidate_roles(targets: list[dict[str, Any]]) -> list[str]:
    roles = {str(target.get("candidate_role", "")) for target in targets}
    return [role for role in ("hotspot_edge", "exploration") if role not in roles]


def _targets_by_hotspot(targets: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for target in targets:
        hotspot_id = str(target.get("hotspot_id", target["id"]))
        groups.setdefault(hotspot_id, []).append(target)
    for group in groups.values():
        group.sort(key=_target_quality, reverse=True)
    return groups


def _select_hotspot_ids_for_instance(
    groups: dict[str, list[dict[str, Any]]],
    desired_count: int,
    rng: random.Random,
) -> list[str]:
    remaining = set(groups)
    selected: list[str] = []
    selected_sectors: list[int] = []
    selected_representatives: list[dict[str, Any]] = []
    desired = min(int(desired_count), len(groups))
    while len(selected) < desired and remaining:
        best: tuple[float, float, float, float, str] | None = None
        for hotspot_id in sorted(remaining):
            representative = groups[hotspot_id][0]
            sector = int(representative.get("direction_sector", -1))
            diversity = _sector_diversity_for_instance(sector, selected_sectors)
            spatial = _spatial_diversity_for_instance(representative, selected_representatives)
            quality = _target_quality(representative)
            jitter = 0.015 * rng.random()
            candidate = (quality + 0.18 * diversity + 0.18 * spatial + jitter, quality, diversity, spatial, hotspot_id)
            if best is None or candidate > best:
                best = candidate
        if best is None:
            break
        hotspot_id = best[4]
        selected.append(hotspot_id)
        representative = groups[hotspot_id][0]
        selected_sectors.append(int(representative.get("direction_sector", -1)))
        selected_representatives.append(representative)
        remaining.remove(hotspot_id)
    return selected


def _choose_target_from_hotspot(
    targets: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    scale: int,
    rng: random.Random,
    depot_xy: tuple[float, float],
    *,
    preferred_role: str | None = None,
) -> dict[str, Any] | None:
    min_spacing = _target_spacing_km(scale)
    choices = [
        target
        for target in targets
        if all(_target_distance(target, other) >= min_spacing for other in selected)
    ]
    if not choices:
        choices = list(targets)
    if preferred_role is not None:
        preferred_choices = [target for target in choices if str(target.get("candidate_role", "")) == preferred_role]
        if preferred_choices:
            return _weighted_choice(preferred_choices[: min(8, len(preferred_choices))], rng)
    return _weighted_choice(choices[: min(8, len(choices))], rng)


def _weighted_fill_target(
    targets: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    scale: int,
    rng: random.Random,
    depot_xy: tuple[float, float],
) -> dict[str, Any]:
    for spacing_factor in (1.0, 0.65, 0.35, 0.0):
        min_spacing = _target_spacing_km(scale) * spacing_factor
        choices = [
            target
            for target in targets
            if all(_target_distance(target, other) >= min_spacing for other in selected)
        ]
        if choices:
            return _weighted_choice(choices[: min(24, len(choices))], rng)
    return _weighted_choice(targets, rng)


def _choose_exploration_target(
    targets: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    scale: int,
    rng: random.Random,
    depot_xy: tuple[float, float],
) -> dict[str, Any]:
    for spacing_factor in (1.0, 0.75, 0.50, 0.0):
        min_spacing = _exploration_spacing_km(scale) * spacing_factor
        choices = [
            target
            for target in targets
            if all(_target_distance(target, other) >= min_spacing for other in selected)
        ]
        if choices:
            return _weighted_choice_by(choices[: min(32, len(choices))], rng, _exploration_quality)
    return _weighted_choice_by(targets, rng, _exploration_quality)


def _weighted_choice(targets: list[dict[str, Any]], rng: random.Random) -> dict[str, Any]:
    if not targets:
        raise ValueError("cannot choose from an empty target list")
    weights = [max(0.01, _target_quality(target) ** 1.25 + 0.02) for target in targets]
    total = sum(weights)
    draw = rng.random() * total
    cumulative = 0.0
    for target, weight in zip(targets, weights):
        cumulative += weight
        if cumulative >= draw:
            return target
    return targets[-1]


def _weighted_choice_by(
    targets: list[dict[str, Any]],
    rng: random.Random,
    scorer: Any,
) -> dict[str, Any]:
    if not targets:
        raise ValueError("cannot choose from an empty target list")
    weights = [max(0.01, float(scorer(target)) ** 1.15 + 0.02) for target in targets]
    total = sum(weights)
    draw = rng.random() * total
    cumulative = 0.0
    for target, weight in zip(targets, weights):
        cumulative += weight
        if cumulative >= draw:
            return target
    return targets[-1]


def _science_focus_count(scale: int) -> int:
    return max(1, min(int(scale), int(math.ceil(0.60 * float(scale)))))


def _edge_science_focus_count(science_quota: int) -> int:
    if science_quota <= 1:
        return 0
    return max(1, min(int(science_quota), int(round(0.35 * float(science_quota)))))


def _target_quality(target: dict[str, Any]) -> float:
    role = str(target.get("candidate_role", ""))
    edge_bonus = 0.035 if role == "hotspot_edge" else 0.0
    return (
        0.42 * float(target.get("selection_score", 0.0))
        + 0.28 * float(target.get("resource_score", 0.0))
        + 0.20 * float(target.get("psr_interior_score", 0.0))
        + 0.10 * float(target.get("psr_boundary_score", 0.0))
        + edge_bonus
    )


def _is_exploration_candidate(target: dict[str, Any]) -> bool:
    if str(target.get("candidate_role", "")) == "exploration":
        return True
    return _exploration_quality(target) >= 0.36


def _exploration_quality(target: dict[str, Any]) -> float:
    resource = float(target.get("resource_score", 0.0))
    interior = float(target.get("psr_interior_score", 0.0))
    boundary = float(target.get("psr_boundary_score", 0.0))
    terrain = float(target.get("local_terrain_risk", 0.0))
    shadow = float(target.get("local_shadow_score", 0.0))
    moderate_resource = max(0.0, 1.0 - abs(resource - 0.38) / 0.38)
    uncertainty = max(0.0, 1.0 - abs(interior - 0.25) / 0.75)
    return (
        0.30 * boundary
        + 0.24 * moderate_resource
        + 0.18 * uncertainty
        + 0.14 * max(0.0, 1.0 - terrain)
        + 0.08 * shadow
        + 0.06 * float(target.get("selection_score", 0.0))
    )


def _target_spacing_km(scale: int) -> float:
    return {5: 7.5, 10: 5.2, 20: 3.6, 30: 2.6, 50: 1.7, 100: 1.0}[int(scale)]


def _exploration_spacing_km(scale: int) -> float:
    return {5: 10.0, 10: 7.2, 20: 5.0, 30: 3.6, 50: 2.4, 100: 1.4}[int(scale)]


def _sector_diversity_for_instance(sector: int, selected_sectors: list[int]) -> float:
    if sector < 0 or not selected_sectors:
        return 1.0
    sector_count = 8
    half = float(sector_count) / 2.0
    min_distance = min(min(abs(sector - other), sector_count - abs(sector - other)) for other in selected_sectors)
    return min(1.0, float(min_distance) / half)


def _spatial_diversity_for_instance(target: dict[str, Any], selected: list[dict[str, Any]]) -> float:
    if not selected:
        return 1.0
    min_distance = min(_target_distance(target, other) for other in selected)
    return min(1.0, min_distance / 14.0)


def _target_distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    ax, ay = a["xy_km"]
    bx, by = b["xy_km"]
    return math.hypot(float(ax) - float(bx), float(ay) - float(by))


def _legacy_weighted_sample_targets(
    targets: list[dict[str, Any]],
    scale: int,
    rng: random.Random,
    depot_xy: tuple[float, float],
) -> list[dict[str, Any]]:
    remaining = list(targets)
    selected: list[dict[str, Any]] = []
    while remaining and len(selected) < int(scale):
        weights = [
            max(0.01, float(item.get("selection_score", 0.0)) ** 1.4 + 0.02)
            * _reach_weight(item, scale, depot_xy)
            for item in remaining
        ]
        total = sum(weights)
        draw = rng.random() * total
        cumulative = 0.0
        chosen_index = 0
        for index, weight in enumerate(weights):
            cumulative += weight
            if cumulative >= draw:
                chosen_index = index
                break
        selected.append(remaining.pop(chosen_index))
    selected.sort(key=lambda item: item["id"])
    return selected


def _reach_weight(target: dict[str, Any], scale: int, depot_xy: tuple[float, float]) -> float:
    reach_km = {5: 22.0, 10: 23.0, 20: 24.0, 30: 25.0, 50: 27.0, 100: 29.0}[int(scale)]
    distance = _target_distance_to_depot(target, depot_xy)
    excess = max(0.0, distance - reach_km)
    return max(0.20, 1.0 / (1.0 + (excess / 6.0) ** 2))


def _distance_screen_score(targets: list[dict[str, Any]], scale: int, depot_xy: tuple[float, float]) -> float:
    distances = sorted(_target_distance_to_depot(target, depot_xy) for target in targets)
    if not distances:
        return 0.0
    avg_caps = {5: 20.0, 10: 21.5, 20: 23.0, 30: 24.0, 50: 26.0, 100: 28.0}
    max_caps = {5: 31.0, 10: 32.5, 20: 34.0, 30: 35.0, 50: 36.0, 100: 37.0}
    avg = sum(distances) / len(distances)
    max_distance = max(distances)
    far_count = sum(1 for value in distances if value > avg_caps[int(scale)] + 6.0)
    allowed_far = {5: 2, 10: 4, 20: 8, 30: 12, 50: 20, 100: 40}[int(scale)]
    hotspot_count = len({str(target.get("hotspot_id", target["id"])) for target in targets})
    sector_count = len({int(target.get("direction_sector", -1)) for target in targets})
    required_hotspots = {5: 5, 10: 7, 20: 10, 30: 12, 50: 14, 100: 16}[int(scale)]
    required_sectors = {5: 4, 10: 5, 20: 6, 30: 6, 50: 7, 100: 8}[int(scale)]
    return (
        max(0.0, avg - avg_caps[int(scale)])
        + max(0.0, max_distance - max_caps[int(scale)])
        + 0.5 * max(0, far_count - allowed_far)
        + 0.8 * max(0, min(required_hotspots, int(scale)) - hotspot_count)
        + 0.5 * max(0, min(required_sectors, int(scale)) - sector_count)
    )


def _target_distance_to_depot(target: dict[str, Any], depot_xy: tuple[float, float]) -> float:
    xy = target["xy_km"]
    return math.hypot(float(xy[0]) - float(depot_xy[0]), float(xy[1]) - float(depot_xy[1]))


def _assign_operation_modes(targets: list[dict[str, Any]], scale: int) -> dict[str, str]:
    counts = _mode_counts(scale)
    detect_suitable_count = sum(1 for target in targets if _detect_suitability(target) >= 0.50)
    min_detect = max(1, int(math.floor(0.25 * float(scale))))
    detect_count = min(counts["detect"], max(min_detect, detect_suitable_count))
    drill_count = counts["drill"]
    sample_count = max(0, int(scale) - detect_count - drill_count)
    modes = {target["id"]: "sample" for target in targets}
    remaining = list(targets)
    drill_order = sorted(
        remaining,
        key=lambda item: (
            item.get("recommended_operation_mode") == "drill",
            0.60 * float(item.get("psr_interior_score", 0.0))
            + 0.35 * float(item.get("resource_score", 0.0))
            + 0.05 * float(item.get("selection_score", 0.0)),
            -float(item.get("hotspot_rank", 9999)),
            float(item.get("selection_score", 0.0)),
        ),
        reverse=True,
    )
    drill_targets = drill_order[:drill_count]
    for target in drill_targets:
        modes[target["id"]] = "drill"
    remaining = [target for target in remaining if modes[target["id"]] != "drill"]
    detect_order = sorted(
        remaining,
        key=lambda item: (
            _detect_suitability(item),
            item.get("recommended_operation_mode") == "detect",
            float(item.get("psr_boundary_score", 0.0)),
            -float(item.get("resource_score", 0.0)),
        ),
        reverse=True,
    )
    for target in detect_order[:detect_count]:
        modes[target["id"]] = "detect"
    if sample_count <= 0:
        sample_order = sorted(
            [target for target in targets if modes[target["id"]] == "sample"],
            key=lambda item: (float(item.get("resource_score", 0.0)), float(item.get("selection_score", 0.0))),
        )
        for target in sample_order:
            modes[target["id"]] = "detect"
    return modes


def _detect_suitability(target: dict[str, Any]) -> float:
    resource = float(target.get("resource_score", 0.0))
    interior = float(target.get("psr_interior_score", 0.0))
    boundary = float(target.get("psr_boundary_score", 0.0))
    shadow = float(target.get("local_shadow_score", 0.0))
    return (
        0.46 * (1.0 - resource)
        + 0.26 * (1.0 - interior)
        + 0.22 * boundary
        + 0.06 * max(0.0, 0.35 - shadow)
    )


def _mode_counts(scale: int) -> dict[str, int]:
    ratios = {"detect": 0.50, "sample": 0.30, "drill": 0.20}
    base = {mode: int(math.floor(float(scale) * ratio)) for mode, ratio in ratios.items()}
    remainder = int(scale) - sum(base.values())
    tie_priority = {"sample": 2, "detect": 1, "drill": 0}
    order = sorted(
        ratios,
        key=lambda mode: (float(scale) * ratios[mode] - base[mode], tie_priority[mode]),
        reverse=True,
    )
    for mode in order[:remainder]:
        base[mode] += 1
    return base


def _time_window_mode_for_index(index: int) -> str:
    slot = (int(index) - 1) % 20
    if slot < 7:
        return "outer_to_inner"
    if slot < 14:
        return "inner_to_outer"
    return "easy_to_hard"


def _task_order_for_time_window_mode(
    tasks: dict[str, dict[str, Any]],
    depot_xy: tuple[float, float],
    mode: str,
) -> list[str]:
    if mode == "outer_to_inner":
        return sorted(tasks, key=lambda task_id: (_task_depth_score(tasks[task_id]), _distance_to_depot(tasks[task_id], depot_xy)))
    if mode == "inner_to_outer":
        return sorted(tasks, key=lambda task_id: (_task_depth_score(tasks[task_id]), _distance_to_depot(tasks[task_id], depot_xy)), reverse=True)
    if mode == "easy_to_hard":
        complexity = {"detect": 0, "sample": 1, "drill": 2}
        return sorted(
            tasks,
            key=lambda task_id: (
                complexity.get(str(tasks[task_id].get("operation_mode")), 9),
                float(tasks[task_id].get("sigma", 0.0)),
                _task_depth_score(tasks[task_id]),
            ),
        )
    raise ValueError(f"unsupported real-map time_window_mode {mode!r}")


def _task_depth_score(task: dict[str, Any]) -> float:
    return (
        0.50 * float(task.get("psr_interior_score", 0.0))
        + 0.25 * float(task.get("ice_confidence", 0.0))
        + 0.20 * float(task.get("local_shadow_score", 0.0))
        - 0.10 * float(task.get("psr_boundary_score", 0.0))
    )


def _distance_to_depot(task: dict[str, Any], depot_xy: tuple[float, float]) -> float:
    xy = task["xy_km"]
    return math.hypot(float(xy[0]) - float(depot_xy[0]), float(xy[1]) - float(depot_xy[1]))


def _downsample_matrix(matrix: list[list[float]], *, cells: int) -> list[list[float]]:
    if not matrix:
        return []
    rows = len(matrix)
    cols = len(matrix[0])
    if rows <= cells and cols <= cells:
        return matrix
    result: list[list[float]] = []
    for row_idx in range(cells):
        src_row = min(rows - 1, int(row_idx * rows / cells))
        row: list[float] = []
        for col_idx in range(cells):
            src_col = min(cols - 1, int(col_idx * cols / cells))
            row.append(float(matrix[src_row][src_col]))
        result.append(row)
    return result

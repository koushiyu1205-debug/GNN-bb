"""Benchmark instance generation runner."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from lunar_ice_bpc.domain.scenario import (
    ACTIVE_FOOTPRINT_BY_SCALE,
    FLEET_BY_SCALE,
    HORIZON_BY_SCALE,
    LunarIceConfig,
    PATH_OPTION_POLICY_ID,
    RISK_SCHEMA_VERSION,
    SCALES,
    SHADOW_CAP_BY_SCALE,
    SYNTHETIC_GENERATOR_ID,
    TIME_WINDOW_POLICY_ID,
    scale_label,
)
from lunar_ice_bpc.domain.scheduling import generate_instance
from lunar_ice_bpc.io.instance_io import validate_instance, write_json


def generate_benchmark(
    *,
    output_root: str | Path,
    manifest_path: str | Path,
    project_root: str | Path | None = None,
    scales: Iterable[int] = SCALES,
    per_scale: int = 20,
    seed_base: int = 629000,
    max_attempts_per_instance: int = 80,
) -> dict:
    output_root = Path(output_root)
    manifest_path = Path(manifest_path)
    project_root_path = Path(project_root) if project_root is not None else _infer_project_root(output_root)
    scales = tuple(int(scale) for scale in scales)
    config = LunarIceConfig()
    manifest: dict = {
        "schema_version": "lunar_ice_bpc.manifest.v1",
        "generator": SYNTHETIC_GENERATOR_ID,
        "risk_schema_version": RISK_SCHEMA_VERSION,
        "time_window_policy_id": TIME_WINDOW_POLICY_ID,
        "path_option_policy_id": PATH_OPTION_POLICY_ID,
        "resource_map_extent_km": config.resource_map_extent_km,
        "synthetic_grid_resolution_m": config.synthetic_grid_resolution_m,
        "B_use": config.b_use,
        "Q_ice": config.q_ice,
        "max_tasks_per_trip": config.max_tasks_per_trip,
        "depot_chargers": config.depot_chargers,
        "per_scale_target": int(per_scale),
        "total_target_count": int(per_scale) * len(scales),
        "scales": {},
        "instances": [],
    }
    for scale in scales:
        label = scale_label(int(scale))
        accepted = 0
        attempts = 0
        skip_reason_counts: dict[str, int] = {}
        scale_dir = output_root / f"lunar_ice_{label}"
        if scale_dir.exists():
            for stale_path in scale_dir.glob("instance_*_logical_graph.json"):
                stale_path.unlink()
        while accepted < int(per_scale) and attempts < int(per_scale) * int(max_attempts_per_instance):
            attempts += 1
            seed = int(seed_base) + int(scale) * 10000 + attempts
            instance = generate_instance(int(scale), seed=seed, index=accepted + 1)
            if not instance.get("validation", {}).get("accepted", False):
                reason = str(instance.get("validation", {}).get("reason", "unknown_reject"))
                skip_reason_counts[reason] = skip_reason_counts.get(reason, 0) + 1
                continue
            issues = validate_instance(instance)
            if issues:
                skip_reason_counts["validation_error"] = skip_reason_counts.get("validation_error", 0) + 1
                continue
            accepted += 1
            path = scale_dir / f"instance_{accepted:03d}_logical_graph.json"
            write_json(path, instance)
            relative_path = _manifest_relative_path(path, project_root_path)
            manifest["instances"].append(
                {
                    "scale": int(scale),
                    "scale_label": label,
                    "instance_id": instance["instance_id"],
                    "path": str(relative_path),
                    "seed": seed,
                    "attempt_index": attempts,
                    "status": "accepted",
                    "risk_schema_version": RISK_SCHEMA_VERSION,
                    "time_window_policy_id": TIME_WINDOW_POLICY_ID,
                    "path_option_policy_id": PATH_OPTION_POLICY_ID,
                    "resource_map_extent_km": config.resource_map_extent_km,
                    "synthetic_grid_resolution_m": config.synthetic_grid_resolution_m,
                    "active_footprint_km": ACTIVE_FOOTPRINT_BY_SCALE[int(scale)],
                    "fleet_size": FLEET_BY_SCALE[int(scale)],
                    "horizon_min": HORIZON_BY_SCALE[int(scale)],
                    "B_use": config.b_use,
                    "max_shadow_exposure_per_sortie": SHADOW_CAP_BY_SCALE[int(scale)],
                    "mean_window_width": instance.get("validation", {}).get("mean_window_width"),
                    "max_window_width": instance.get("validation", {}).get("max_window_width"),
                    "configured_window_width_cap": instance.get("validation", {}).get("configured_window_width_cap"),
                    "max_effective_window_width_cap": instance.get("validation", {}).get("max_effective_window_width_cap"),
                    "forced_min_width_count": instance.get("validation", {}).get("forced_min_width_count"),
                }
            )
        manifest["scales"][label] = {
            "accepted_count": accepted,
            "attempt_count": attempts,
            "skip_reason_counts": dict(sorted(skip_reason_counts.items())),
            "target_count": int(per_scale),
            "status": "complete" if accepted == int(per_scale) else "incomplete",
            "risk_schema_version": RISK_SCHEMA_VERSION,
            "time_window_policy_id": TIME_WINDOW_POLICY_ID,
            "path_option_policy_id": PATH_OPTION_POLICY_ID,
            "resource_map_extent_km": config.resource_map_extent_km,
            "synthetic_grid_resolution_m": config.synthetic_grid_resolution_m,
            "active_footprint_km": ACTIVE_FOOTPRINT_BY_SCALE[int(scale)],
            "fleet_size": FLEET_BY_SCALE[int(scale)],
            "horizon_min": HORIZON_BY_SCALE[int(scale)],
            "B_use": config.b_use,
            "max_shadow_exposure_per_sortie": SHADOW_CAP_BY_SCALE[int(scale)],
        }
    manifest["accepted_total_count"] = len(manifest["instances"])
    manifest["status"] = "complete" if manifest["accepted_total_count"] == manifest["total_target_count"] else "incomplete"
    write_json(manifest_path, manifest)
    return manifest


def _infer_project_root(output_root: Path) -> Path:
    if output_root.name == "instances" and output_root.parent.name == "data":
        return output_root.parent.parent
    return output_root.parent


def _manifest_relative_path(path: Path, project_root: Path) -> Path:
    try:
        return path.relative_to(project_root)
    except ValueError:
        return path

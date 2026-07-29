#!/usr/bin/env python3
"""Generate the formal SP50 real-map lunar water-ice benchmark."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
import resource
import signal
import shutil
import subprocess
import sys
from time import perf_counter
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.domain.real_instance import generate_real_map_instance
from lunar_ice_bpc.domain.real_maps import (
    DEFAULT_SP50_DEPOT_CENTER_KM,
    REAL_MAP_GENERATOR_ID,
    REAL_MAP_SOURCE_CATALOG,
    build_real_map_preview,
    real_map_source_catalog,
)
from lunar_ice_bpc.domain.scenario import (
    ACTIVE_FOOTPRINT_BY_SCALE,
    FLEET_BY_SCALE,
    HORIZON_BY_SCALE,
    LunarIceConfig,
    PATH_OPTION_POLICY_ID,
    RISK_SCHEMA_VERSION,
    SCALES,
    SERVICE_TIMING_POLICY_ID,
    SHADOW_CAP_BY_SCALE,
    TIME_WINDOW_POLICY_ID,
    scale_label,
)
from lunar_ice_bpc.domain.visualization import write_svg
from lunar_ice_bpc.io.instance_io import read_json, validate_instance, write_json


BENCHMARK_GENERATOR_ID = "real_lunar_south_pole_sp50_benchmark_v1"
TIME_WINDOW_MODE_COUNTS_PER_20 = {"outer_to_inner": 7, "inner_to_outer": 7, "easy_to_hard": 6}
PREFERRED_REAL_MAP_LAYER_KEYS = {
    "lola_slope",
    "lola_roughness",
    "lola_psr",
    "lola_dem",
    "lola_avg_solar_visibility",
}


class GenerationTimeout(RuntimeError):
    """Raised when one instance exceeds the configured generation wall time."""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="data/instances")
    parser.add_argument("--manifest", default="data/manifests/lunar_ice_sp50_real_benchmark_manifest.json")
    parser.add_argument("--figures-dir", default="runs/figures")
    parser.add_argument("--scales", default=",".join(str(item) for item in SCALES))
    parser.add_argument("--per-scale", type=int, default=20)
    parser.add_argument("--seed-base", type=int, default=629000)
    parser.add_argument("--max-attempts-per-instance", type=int, default=80)
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--min-free-mem-gb", type=float, default=2.0)
    parser.add_argument("--worker-rss-budget-mb", type=float, default=900.0)
    parser.add_argument("--raw-map-dir", default="data/raw_maps")
    parser.add_argument("--path-preview", choices=("none", "sample", "all"), default="all")
    parser.add_argument("--max-instance-sec", type=float, default=None)
    parser.add_argument("--fresh", action="store_true", help="Remove only selected SP50 instance JSONs before generation.")
    parser.add_argument("--skip-preflight", action="store_true")
    parser.add_argument("--skip-bpc-future-check", action="store_true")
    parser.add_argument("--no-draw-figures", action="store_true")
    parser.add_argument("--continue-after-timeout", action="store_true")
    parser.add_argument("--refresh-only", action="store_true", help="Refresh manifest targets/summaries without generating instances.")
    parser.add_argument("--allow-incomplete", action="store_true", help="Return success after a partial/resumable generation run.")
    args = parser.parse_args()

    raw_map_dir = _project_path(args.raw_map_dir)
    output_root = _project_path(args.output_root)
    manifest_path = _project_path(args.manifest)
    figures_dir = _project_path(args.figures_dir)
    scales = _parse_scales(args.scales)

    if not args.skip_bpc_future_check:
        _assert_bpc_future_untouched()
    if not args.skip_preflight:
        preflight = _run_preflight(raw_map_dir)
        if preflight["status"] != "REAL_MAP_PREVIEW_READY":
            print(f"preflight failed: {preflight['status']}", file=sys.stderr, flush=True)
            return 2

    if args.fresh:
        _clear_selected_sp50_outputs(output_root, manifest_path, scales)

    manifest = _load_or_new_manifest(
        manifest_path=manifest_path,
        raw_map_dir=raw_map_dir,
        output_root=output_root,
        figures_dir=figures_dir,
        scales=scales,
        per_scale=int(args.per_scale),
        seed_base=int(args.seed_base),
        max_attempts_per_instance=int(args.max_attempts_per_instance),
    )
    _update_manifest_run_settings(
        manifest,
        raw_map_dir=raw_map_dir,
        output_root=output_root,
        figures_dir=figures_dir,
        scales=scales,
        per_scale=int(args.per_scale),
        seed_base=int(args.seed_base),
        max_attempts_per_instance=int(args.max_attempts_per_instance),
    )
    _refresh_manifest_summary(manifest, scales=scales, per_scale=int(args.per_scale))
    write_json(manifest_path, manifest)
    if args.refresh_only:
        print(
            "refreshed manifest {accepted}/{total} accepted status={status} -> {path}".format(
                accepted=manifest["accepted_total_count"],
                total=manifest["total_target_count"],
                status=manifest["status"],
                path=manifest_path,
            ),
            flush=True,
        )
        return 0 if args.allow_incomplete or manifest["status"] == "complete" else 2

    for scale in scales:
        _generate_scale(
            manifest,
            manifest_path=manifest_path,
            output_root=output_root,
            raw_map_dir=raw_map_dir,
            figures_dir=figures_dir,
            scale=int(scale),
            per_scale=int(args.per_scale),
            seed_base=int(args.seed_base),
            max_attempts_per_instance=int(args.max_attempts_per_instance),
            draw_figures=not args.no_draw_figures,
            path_preview=str(args.path_preview),
            max_instance_sec=args.max_instance_sec,
            continue_after_timeout=bool(args.continue_after_timeout),
            max_workers=int(args.max_workers),
            min_free_mem_gb=float(args.min_free_mem_gb),
            worker_rss_budget_mb=float(args.worker_rss_budget_mb),
        )
    _refresh_manifest_summary(manifest, scales=scales, per_scale=int(args.per_scale))
    write_json(manifest_path, manifest)
    print(
        "wrote {accepted}/{total} accepted real-map instances status={status} -> {path}".format(
            accepted=manifest["accepted_total_count"],
            total=manifest["total_target_count"],
            status=manifest["status"],
            path=manifest_path,
        ),
        flush=True,
    )
    return 0 if args.allow_incomplete or manifest["status"] == "complete" else 2


def _generate_scale(
    manifest: dict[str, Any],
    *,
    manifest_path: Path,
    output_root: Path,
    raw_map_dir: Path,
    figures_dir: Path,
    scale: int,
    per_scale: int,
    seed_base: int,
    max_attempts_per_instance: int,
    draw_figures: bool,
    path_preview: str,
    max_instance_sec: float | None,
    continue_after_timeout: bool,
    max_workers: int,
    min_free_mem_gb: float,
    worker_rss_budget_mb: float,
) -> None:
    label = scale_label(scale)
    scale_dir = output_root / f"lunar_ice_sp50_{label}"
    scale_dir.mkdir(parents=True, exist_ok=True)
    max_attempts = int(per_scale) * int(max_attempts_per_instance)
    accepted = _accepted_rows_for_scale(manifest, label)
    accepted_count = len(accepted)
    attempt_index = max([int(row.get("attempt_index", 0)) for row in accepted] + [_manifest_attempt_count(manifest, label)])
    print(f"[scale {label}] resume accepted={accepted_count}/{per_scale} attempts={attempt_index}", flush=True)
    if max_workers > 1:
        _generate_scale_parallel(
            manifest,
            manifest_path=manifest_path,
            output_root=output_root,
            raw_map_dir=raw_map_dir,
            figures_dir=figures_dir,
            scale=scale,
            per_scale=per_scale,
            seed_base=seed_base,
            max_attempts_per_instance=max_attempts_per_instance,
            draw_figures=draw_figures,
            path_preview=path_preview,
            max_instance_sec=max_instance_sec,
            continue_after_timeout=continue_after_timeout,
            requested_workers=max_workers,
            min_free_mem_gb=min_free_mem_gb,
            worker_rss_budget_mb=worker_rss_budget_mb,
        )
        return
    while accepted_count < int(per_scale) and attempt_index < max_attempts:
        attempt_index += 1
        index = accepted_count + 1
        seed = int(seed_base) + int(scale) * 10000 + attempt_index
        output_path = scale_dir / f"instance_{index:03d}_logical_graph.json"
        edge_checkpoint_dir = _edge_checkpoint_dir(scale_dir, index=index, seed=seed)
        start = perf_counter()
        start_rss_mb = _max_rss_mb()
        try:
            with _optional_time_limit(max_instance_sec):
                instance = generate_real_map_instance(
                    int(scale),
                    raw_map_dir=raw_map_dir,
                    seed=seed,
                    index=index,
                    time_window_mode=_time_window_mode_for_index(index),
                    edge_checkpoint_dir=edge_checkpoint_dir,
                )
            elapsed = perf_counter() - start
            issues = validate_instance(instance)
            acceptance_issues = _acceptance_issues(instance, issues, scale)
        except GenerationTimeout:
            elapsed = perf_counter() - start
            reason = "generation_timeout"
            _record_skip(manifest, label, reason, attempt_index=attempt_index, seed=seed, elapsed_sec=elapsed)
            _refresh_manifest_summary(manifest, scales=[scale], per_scale=per_scale)
            write_json(manifest_path, manifest)
            _remove_edge_checkpoint(edge_checkpoint_dir)
            print(f"[scale {label}] attempt={attempt_index} seed={seed} timeout after {elapsed:.1f}s", flush=True)
            if not continue_after_timeout:
                _mark_scale_stopped(manifest, label, reason)
                write_json(manifest_path, manifest)
                return
            continue
        except Exception as exc:
            elapsed = perf_counter() - start
            reason = f"generation_exception:{type(exc).__name__}"
            _record_skip(
                manifest,
                label,
                reason,
                attempt_index=attempt_index,
                seed=seed,
                elapsed_sec=elapsed,
                detail=str(exc),
            )
            _refresh_manifest_summary(manifest, scales=[scale], per_scale=per_scale)
            write_json(manifest_path, manifest)
            _remove_edge_checkpoint(edge_checkpoint_dir)
            print(f"[scale {label}] attempt={attempt_index} seed={seed} failed {reason}: {exc}", flush=True)
            continue
        if acceptance_issues:
            reason = _skip_reason_from_issues(instance, acceptance_issues)
            _record_skip(
                manifest,
                label,
                reason,
                attempt_index=attempt_index,
                seed=seed,
                elapsed_sec=elapsed,
                detail="; ".join(acceptance_issues[:8]),
            )
            _refresh_manifest_summary(manifest, scales=[scale], per_scale=per_scale)
            write_json(manifest_path, manifest)
            _remove_edge_checkpoint(edge_checkpoint_dir)
            print(f"[scale {label}] attempt={attempt_index} seed={seed} rejected {reason} in {elapsed:.1f}s", flush=True)
            continue
        write_json(output_path, instance)
        row = _manifest_row(
            instance,
            output_path,
            ROOT,
            scale=scale,
            seed=seed,
            attempt_index=attempt_index,
            elapsed_sec=elapsed,
            max_rss_mb=max(start_rss_mb, _max_rss_mb()),
        )
        _replace_or_append_instance_row(manifest, row)
        accepted_count += 1
        _refresh_manifest_summary(manifest, scales=[scale], per_scale=per_scale)
        write_json(manifest_path, manifest)
        _remove_edge_checkpoint(edge_checkpoint_dir)
        print(
            "[scale {label}] accepted {accepted}/{target} index={index:03d} seed={seed} "
            "elapsed={elapsed:.1f}s roles={roles} modes={modes}".format(
                label=label,
                accepted=accepted_count,
                target=per_scale,
                index=index,
                seed=seed,
                elapsed=elapsed,
                roles=row["candidate_role_counts"],
                modes=row["operation_mode_counts"],
            ),
            flush=True,
        )
        if draw_figures and index == 1:
            _draw_typical_figures(output_path, figures_dir=figures_dir, label=label, path_preview=path_preview)
    _refresh_manifest_summary(manifest, scales=[scale], per_scale=per_scale)
    write_json(manifest_path, manifest)


def _generate_scale_parallel(
    manifest: dict[str, Any],
    *,
    manifest_path: Path,
    output_root: Path,
    raw_map_dir: Path,
    figures_dir: Path,
    scale: int,
    per_scale: int,
    seed_base: int,
    max_attempts_per_instance: int,
    draw_figures: bool,
    path_preview: str,
    max_instance_sec: float | None,
    continue_after_timeout: bool,
    requested_workers: int,
    min_free_mem_gb: float,
    worker_rss_budget_mb: float,
) -> None:
    label = scale_label(scale)
    scale_dir = output_root / f"lunar_ice_sp50_{label}"
    scale_dir.mkdir(parents=True, exist_ok=True)
    existing_indices = _accepted_indices_for_scale(manifest, label)
    missing_indices = [index for index in range(1, int(per_scale) + 1) if index not in existing_indices]
    if not missing_indices:
        _refresh_manifest_summary(manifest, scales=[scale], per_scale=per_scale)
        write_json(manifest_path, manifest)
        return
    available_gb = _mem_available_gb()
    mem_capped_workers = max(1, int(max(0.0, available_gb - float(min_free_mem_gb)) * 1024.0 // max(1.0, float(worker_rss_budget_mb))))
    workers = max(1, min(int(requested_workers), int(mem_capped_workers), len(missing_indices)))
    max_existing_attempt = max(
        [int(row.get("attempt_index", 0)) for row in (manifest.get("instances") or []) if str(row.get("scale_label")) == label]
        + [int(row.get("attempt_index", 0)) for row in (manifest.get("skips") or []) if str(row.get("scale_label")) == label]
        + [0]
    )
    print(
        f"[scale {label}] parallel missing={len(missing_indices)} workers={workers} "
        f"mem_available_gb={available_gb:.2f}",
        flush=True,
    )
    payloads = []
    for index in missing_indices:
        output_path = scale_dir / f"instance_{index:03d}_logical_graph.json"
        payloads.append(
            {
                "scale": int(scale),
                "label": label,
                "index": int(index),
                "raw_map_dir": str(raw_map_dir),
                "output_path": str(output_path),
                "seed_base": int(seed_base),
                "start_attempt_index": int(max_existing_attempt) + int(index),
                "attempt_stride": max(1, int(per_scale)),
                "max_attempts_per_instance": int(max_attempts_per_instance),
                "max_instance_sec": max_instance_sec,
            }
        )
    stopped = False
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_generate_one_index_worker, payload): payload for payload in payloads}
        for future in as_completed(futures):
            payload = futures[future]
            index = int(payload["index"])
            try:
                result = future.result()
            except Exception as exc:
                result = {
                    "status": "exception",
                    "index": index,
                    "skips": [
                        {
                            "scale": int(label),
                            "scale_label": label,
                            "attempt_index": int(payload["start_attempt_index"]),
                            "seed": int(seed_base) + int(scale) * 10000 + int(payload["start_attempt_index"]),
                            "reason": f"worker_exception:{type(exc).__name__}",
                            "elapsed_sec": 0.0,
                            "detail": str(exc),
                        }
                    ],
                }
            for skip in result.get("skips", []):
                _append_unique_skip(manifest, skip)
            if result.get("status") == "accepted":
                row = result["row"]
                _replace_or_append_instance_row(manifest, row)
                print(
                    "[scale {label}] accepted index={index:03d} seed={seed} elapsed={elapsed:.1f}s roles={roles}".format(
                        label=label,
                        index=index,
                        seed=row["seed"],
                        elapsed=float(row.get("elapsed_sec") or 0.0),
                        roles=row.get("candidate_role_counts"),
                    ),
                    flush=True,
                )
                if draw_figures and index == 1:
                    _draw_typical_figures(ROOT / str(row["path"]), figures_dir=figures_dir, label=label, path_preview=path_preview)
            else:
                print(
                    f"[scale {label}] index={index:03d} status={result.get('status')} "
                    f"skips={len(result.get('skips', []))}",
                    flush=True,
                )
                if result.get("status") == "timeout" and not continue_after_timeout:
                    stopped = True
                    _mark_scale_stopped(manifest, label, "generation_timeout")
            _refresh_manifest_summary(manifest, scales=[scale], per_scale=per_scale)
            write_json(manifest_path, manifest)
    if stopped:
        _refresh_manifest_summary(manifest, scales=[scale], per_scale=per_scale)
        write_json(manifest_path, manifest)


def _generate_one_index_worker(payload: dict[str, Any]) -> dict[str, Any]:
    scale = int(payload["scale"])
    label = str(payload["label"])
    index = int(payload["index"])
    raw_map_dir = Path(str(payload["raw_map_dir"]))
    output_path = Path(str(payload["output_path"]))
    seed_base = int(payload["seed_base"])
    attempt_index = int(payload["start_attempt_index"])
    stride = int(payload["attempt_stride"])
    max_attempts = int(payload["max_attempts_per_instance"])
    max_instance_sec = payload.get("max_instance_sec")
    skips: list[dict[str, Any]] = []
    for attempt_round in range(max_attempts):
        current_attempt = attempt_index + attempt_round * stride
        seed = int(seed_base) + scale * 10000 + current_attempt
        edge_checkpoint_dir = _edge_checkpoint_dir(output_path.parent, index=index, seed=seed)
        start = perf_counter()
        start_rss_mb = _max_rss_mb()
        try:
            with _optional_time_limit(float(max_instance_sec) if max_instance_sec is not None else None):
                instance = generate_real_map_instance(
                    scale,
                    raw_map_dir=raw_map_dir,
                    seed=seed,
                    index=index,
                    time_window_mode=_time_window_mode_for_index(index),
                    edge_checkpoint_dir=edge_checkpoint_dir,
                )
            elapsed = perf_counter() - start
            issues = validate_instance(instance)
            acceptance_issues = _acceptance_issues(instance, issues, scale)
        except GenerationTimeout:
            elapsed = perf_counter() - start
            skips.append(
                _skip_payload(
                    label,
                    "generation_timeout",
                    attempt_index=current_attempt,
                    seed=seed,
                    elapsed_sec=elapsed,
                )
            )
            _remove_edge_checkpoint(edge_checkpoint_dir)
            return {"status": "timeout", "index": index, "skips": skips}
        except Exception as exc:
            elapsed = perf_counter() - start
            skips.append(
                _skip_payload(
                    label,
                    f"generation_exception:{type(exc).__name__}",
                    attempt_index=current_attempt,
                    seed=seed,
                    elapsed_sec=elapsed,
                    detail=str(exc),
                )
            )
            _remove_edge_checkpoint(edge_checkpoint_dir)
            continue
        if acceptance_issues:
            skips.append(
                _skip_payload(
                    label,
                    _skip_reason_from_issues(instance, acceptance_issues),
                    attempt_index=current_attempt,
                    seed=seed,
                    elapsed_sec=elapsed,
                    detail="; ".join(acceptance_issues[:8]),
                )
            )
            _remove_edge_checkpoint(edge_checkpoint_dir)
            continue
        write_json(output_path, instance)
        row = _manifest_row(
            instance,
            output_path,
            ROOT,
            scale=scale,
            seed=seed,
            attempt_index=current_attempt,
            elapsed_sec=elapsed,
            max_rss_mb=max(start_rss_mb, _max_rss_mb()),
        )
        _remove_edge_checkpoint(edge_checkpoint_dir)
        return {"status": "accepted", "index": index, "row": row, "skips": skips}
    return {"status": "exhausted", "index": index, "skips": skips}


def _run_preflight(raw_map_dir: Path) -> dict[str, Any]:
    catalog = real_map_source_catalog(raw_map_dir)
    layer_by_key = {item["key"]: item for item in catalog["layers"]}
    missing = sorted(
        key for key in PREFERRED_REAL_MAP_LAYER_KEYS if key not in layer_by_key or not bool(layer_by_key[key]["local_exists"])
    )
    if missing:
        return {"status": "MISSING_PREFERRED_REAL_MAP_LAYERS", "missing_layers": missing}
    preview = build_real_map_preview(
        raw_map_dir=raw_map_dir,
        center_x_km=DEFAULT_SP50_DEPOT_CENTER_KM[0],
        center_y_km=DEFAULT_SP50_DEPOT_CENTER_KM[1],
        extent_km=LunarIceConfig().resource_map_extent_km,
        output_cells=int(round(LunarIceConfig().resource_map_extent_km * 1000.0 / LunarIceConfig().synthetic_grid_resolution_m)),
        target_count=100,
        path_target_count=3,
        active_footprint_km=50.0,
    )
    print(f"preflight status: {preview.get('status')} center_xy_km={DEFAULT_SP50_DEPOT_CENTER_KM}", flush=True)
    return preview


def _edge_checkpoint_dir(scale_dir: Path, *, index: int, seed: int) -> Path:
    return scale_dir / ".generation_checkpoints" / f"index_{int(index):03d}_seed_{int(seed)}"


def _remove_edge_checkpoint(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)


def _acceptance_issues(instance: dict[str, Any], schema_issues: list[str], scale: int) -> list[str]:
    issues = list(schema_issues)
    validation = instance.get("validation") or {}
    if not validation.get("accepted", False):
        issues.append(f"validation_not_accepted:{validation.get('reason', 'unknown')}")
    tasks = instance.get("tasks") or {}
    if len(tasks) != int(scale):
        issues.append(f"task_count_mismatch:{len(tasks)}!={scale}")
    nodes = (instance.get("logical_graph") or {}).get("nodes") or []
    if len(nodes) != int(scale) + 1:
        issues.append(f"node_count_mismatch:{len(nodes)}!={int(scale) + 1}")
    edges = (instance.get("logical_graph") or {}).get("edges") or []
    expected_edges = int(scale) * (int(scale) + 1)
    if len(edges) != expected_edges:
        issues.append(f"edge_count_mismatch:{len(edges)}!={expected_edges}")
    bad_edge = next((edge for edge in edges if len(edge.get("path_options") or []) != 3), None)
    if bad_edge is not None:
        issues.append(f"edge_path_option_count_mismatch:{bad_edge.get('from')}->{bad_edge.get('to')}")
    role_counts = Counter(str(task.get("candidate_role", "")) for task in tasks.values())
    if role_counts.get("hotspot_edge", 0) < 1:
        issues.append("missing_candidate_role:hotspot_edge")
    if role_counts.get("exploration", 0) < 1:
        issues.append("missing_candidate_role:exploration")
    return issues


def _manifest_row(
    instance: dict[str, Any],
    path: Path,
    project_root: Path,
    *,
    scale: int,
    seed: int,
    attempt_index: int,
    elapsed_sec: float,
    max_rss_mb: float,
) -> dict[str, Any]:
    tasks = instance.get("tasks") or {}
    role_counts = dict(sorted(Counter(str(task.get("candidate_role", "")) for task in tasks.values()).items()))
    mode_counts = dict(sorted(Counter(str(task.get("operation_mode", "")) for task in tasks.values()).items()))
    hotspots = {str(task.get("hotspot_id", "")) for task in tasks.values()}
    sectors = {int(task.get("direction_sector", -1)) for task in tasks.values()}
    validation = instance.get("validation") or {}
    resource = instance.get("resource_map") or {}
    vehicle = instance.get("vehicle") or {}
    scheduling = instance.get("scheduling") or {}
    label = scale_label(scale)
    return {
        "scale": int(scale),
        "scale_label": label,
        "instance_id": instance.get("instance_id"),
        "path": str(_manifest_relative_path(path, project_root)),
        "seed": int(seed),
        "attempt_index": int(attempt_index),
        "status": "accepted",
        "elapsed_sec": round(float(elapsed_sec), 6),
        "max_rss_mb": round(float(max_rss_mb), 3),
        "risk_schema_version": resource.get("risk_schema_version", RISK_SCHEMA_VERSION),
        "time_window_policy_id": validation.get("time_window_policy_id", TIME_WINDOW_POLICY_ID),
        "service_timing_policy_id": validation.get(
            "service_timing_policy_id",
            SERVICE_TIMING_POLICY_ID,
        ),
        "path_option_policy_id": (instance.get("logical_graph") or {}).get("path_option_policy_id", PATH_OPTION_POLICY_ID),
        "time_window_mode": scheduling.get("time_window_mode"),
        "resource_map_extent_km": resource.get("extent_km"),
        "synthetic_grid_resolution_m": resource.get("resolution_m"),
        "active_footprint_km": resource.get("active_footprint_km", ACTIVE_FOOTPRINT_BY_SCALE[int(scale)]),
        "fleet_size": vehicle.get("fleet_size", FLEET_BY_SCALE[int(scale)]),
        "horizon_min": scheduling.get("horizon_min", HORIZON_BY_SCALE[int(scale)]),
        "B_use": vehicle.get("B_use", LunarIceConfig().b_use),
        "Q_ice": vehicle.get("Q_ice", LunarIceConfig().q_ice),
        "max_tasks_per_trip": vehicle.get("max_tasks_per_trip", LunarIceConfig().max_tasks_per_trip),
        "max_shadow_exposure_per_sortie": vehicle.get("max_shadow_exposure_per_sortie", SHADOW_CAP_BY_SCALE[int(scale)]),
        "mean_window_width": validation.get("mean_window_width"),
        "max_window_width": validation.get("max_window_width"),
        "configured_window_width_cap": validation.get("configured_window_width_cap"),
        "max_effective_window_width_cap": validation.get("max_effective_window_width_cap"),
        "forced_min_width_count": validation.get("forced_min_width_count"),
        "candidate_role_counts": role_counts,
        "operation_mode_counts": mode_counts,
        "sampled_hotspot_count": len({item for item in hotspots if item}),
        "sampled_direction_sector_count": len({item for item in sectors if item >= 0}),
    }


def _load_or_new_manifest(
    *,
    manifest_path: Path,
    raw_map_dir: Path,
    output_root: Path,
    figures_dir: Path,
    scales: list[int],
    per_scale: int,
    seed_base: int,
    max_attempts_per_instance: int,
) -> dict[str, Any]:
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        if manifest.get("generator") == BENCHMARK_GENERATOR_ID:
            return manifest
    config = LunarIceConfig()
    catalog = real_map_source_catalog(raw_map_dir)
    return {
        "schema_version": "lunar_ice_bpc.manifest.v1",
        "benchmark_id": "lunar_ice_sp50_real_map_v1",
        "generator": BENCHMARK_GENERATOR_ID,
        "real_map_generator": REAL_MAP_GENERATOR_ID,
        "risk_schema_version": RISK_SCHEMA_VERSION,
        "time_window_policy_id": TIME_WINDOW_POLICY_ID,
        "service_timing_policy_id": SERVICE_TIMING_POLICY_ID,
        "path_option_policy_id": PATH_OPTION_POLICY_ID,
        "candidate_pool_policy": "water_ice_hotspot_directional_sampling_v1",
        "time_window_mode_target_counts_per_20": dict(TIME_WINDOW_MODE_COUNTS_PER_20),
        "resource_map_extent_km": config.resource_map_extent_km,
        "synthetic_grid_resolution_m": config.synthetic_grid_resolution_m,
        "B_use": config.b_use,
        "Q_ice": config.q_ice,
        "max_tasks_per_trip": config.max_tasks_per_trip,
        "depot_chargers": config.depot_chargers,
        "default_depot_global_xy_km": [round(DEFAULT_SP50_DEPOT_CENTER_KM[0], 6), round(DEFAULT_SP50_DEPOT_CENTER_KM[1], 6)],
        "raw_map_dir": str(raw_map_dir),
        "output_root": str(output_root),
        "figures_dir": str(figures_dir),
        "source_catalog_id": catalog["catalog_id"],
        "ready_preferred_layer_keys": sorted(
            item["key"] for item in catalog["layers"] if item["key"] in PREFERRED_REAL_MAP_LAYER_KEYS and item["local_exists"]
        ),
        "formal_scales": [int(scale) for scale in SCALES],
        "scales_requested": [int(scale) for scale in scales],
        "per_scale_target": int(per_scale),
        "seed_base": int(seed_base),
        "max_attempts_per_instance": int(max_attempts_per_instance),
        "total_target_count": int(per_scale) * len(scales),
        "scales": {},
        "instances": [],
        "skips": [],
    }


def _update_manifest_run_settings(
    manifest: dict[str, Any],
    *,
    raw_map_dir: Path,
    output_root: Path,
    figures_dir: Path,
    scales: list[int],
    per_scale: int,
    seed_base: int,
    max_attempts_per_instance: int,
) -> None:
    manifest["raw_map_dir"] = str(raw_map_dir)
    manifest["output_root"] = str(output_root)
    manifest["figures_dir"] = str(figures_dir)
    manifest["scales_requested"] = [int(scale) for scale in scales]
    manifest["per_scale_target"] = int(per_scale)
    manifest["seed_base"] = int(seed_base)
    manifest["max_attempts_per_instance"] = int(max_attempts_per_instance)
    manifest["total_target_count"] = int(per_scale) * len(scales)


def _refresh_manifest_summary(manifest: dict[str, Any], *, scales: list[int], per_scale: int) -> None:
    instances = manifest.setdefault("instances", [])
    skips = manifest.setdefault("skips", [])
    scale_payload: dict[str, Any] = manifest.setdefault("scales", {})
    formal_scales = [int(scale) for scale in manifest.get("formal_scales", SCALES)]
    scale_set = sorted(set(formal_scales) | {int(scale) for scale in scales})
    for scale in scale_set:
        label = scale_label(int(scale))
        rows = [row for row in instances if str(row.get("scale_label")) == label]
        scale_skips = [row for row in skips if str(row.get("scale_label")) == label]
        role_counts: Counter[str] = Counter()
        mode_counts: Counter[str] = Counter()
        time_window_counts = Counter(str(row.get("time_window_mode", "")) for row in rows)
        mean_widths = [float(row["mean_window_width"]) for row in rows if row.get("mean_window_width") is not None]
        max_widths = [float(row["max_window_width"]) for row in rows if row.get("max_window_width") is not None]
        max_rss_values = [float(row["max_rss_mb"]) for row in rows if row.get("max_rss_mb") is not None]
        hotspot_counts = [int(row.get("sampled_hotspot_count") or 0) for row in rows]
        sector_counts = [int(row.get("sampled_direction_sector_count") or 0) for row in rows]
        for row in rows:
            role_counts.update({key: int(value) for key, value in (row.get("candidate_role_counts") or {}).items()})
            mode_counts.update({key: int(value) for key, value in (row.get("operation_mode_counts") or {}).items()})
        skip_counts = Counter(str(row.get("reason", "unknown")) for row in scale_skips)
        stopped_reason = scale_payload.get(label, {}).get("stopped_reason")
        accepted_count = len(rows)
        status = "complete" if accepted_count == int(per_scale) else "incomplete"
        if stopped_reason and status != "complete":
            status = "stopped"
        scale_payload[label] = {
            "accepted_count": accepted_count,
            "attempt_count": max([int(row.get("attempt_index", 0)) for row in rows + scale_skips] + [0]),
            "skip_reason_counts": dict(sorted(skip_counts.items())),
            "target_count": int(per_scale),
            "status": status,
            "stopped_reason": stopped_reason,
            "candidate_role_counts": dict(sorted(role_counts.items())),
            "operation_mode_counts": dict(sorted(mode_counts.items())),
            "time_window_mode_counts": dict(sorted(time_window_counts.items())),
            "mean_window_width_avg": _mean(mean_widths),
            "max_window_width_max": max(max_widths) if max_widths else None,
            "max_rss_mb_max": max(max_rss_values) if max_rss_values else None,
            "sampled_hotspot_count_avg": _mean(hotspot_counts),
            "sampled_direction_sector_count_avg": _mean(sector_counts),
            "risk_schema_version": RISK_SCHEMA_VERSION,
            "time_window_policy_id": TIME_WINDOW_POLICY_ID,
            "service_timing_policy_id": SERVICE_TIMING_POLICY_ID,
            "path_option_policy_id": PATH_OPTION_POLICY_ID,
            "resource_map_extent_km": LunarIceConfig().resource_map_extent_km,
            "synthetic_grid_resolution_m": LunarIceConfig().synthetic_grid_resolution_m,
            "active_footprint_km": ACTIVE_FOOTPRINT_BY_SCALE[int(scale)],
            "fleet_size": FLEET_BY_SCALE[int(scale)],
            "horizon_min": HORIZON_BY_SCALE[int(scale)],
            "B_use": LunarIceConfig().b_use,
            "Q_ice": LunarIceConfig().q_ice,
            "max_tasks_per_trip": LunarIceConfig().max_tasks_per_trip,
            "max_shadow_exposure_per_sortie": SHADOW_CAP_BY_SCALE[int(scale)],
        }
    manifest["accepted_total_count"] = len(instances)
    manifest["total_target_count"] = int(per_scale) * len(formal_scales)
    manifest["status"] = "complete" if manifest["accepted_total_count"] == manifest["total_target_count"] else "incomplete"


def _draw_typical_figures(instance_path: Path, *, figures_dir: Path, label: str, path_preview: str) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)
    base = figures_dir / f"lunar_ice_sp50_{label}_instance_001"
    views = {
        "logical_graph": (True, "none"),
        "path_options": (False, path_preview),
        "targets": (False, "none"),
    }
    written: list[Path] = []
    for suffix, (show_edges, view_path_preview) in views.items():
        resource_path = base.with_name(f"{base.name}_{suffix}.svg")
        dem_path = base.with_name(f"{base.name}_{suffix}_dem.svg")
        write_svg(instance_path, resource_path, show_logical_edges=show_edges, path_preview=view_path_preview, background_mode="resource")
        write_svg(instance_path, dem_path, show_logical_edges=show_edges, path_preview=view_path_preview, background_mode="dem")
        written.extend([resource_path, dem_path])
    # Keep the historic filename as the path-options view so open editor tabs do not show the old mixed overlay.
    write_svg(instance_path, base.with_suffix(".svg"), show_logical_edges=False, path_preview=path_preview, background_mode="resource")
    write_svg(instance_path, base.with_name(f"{base.name}_dem.svg"), show_logical_edges=False, path_preview=path_preview, background_mode="dem")
    print(f"[scale {label}] figures: " + " | ".join(str(path) for path in written), flush=True)


def _record_skip(
    manifest: dict[str, Any],
    label: str,
    reason: str,
    *,
    attempt_index: int,
    seed: int,
    elapsed_sec: float,
    detail: str | None = None,
) -> None:
    manifest.setdefault("skips", []).append(
        _skip_payload(
            label,
            reason,
            attempt_index=attempt_index,
            seed=seed,
            elapsed_sec=elapsed_sec,
            detail=detail,
        )
    )


def _skip_payload(
    label: str,
    reason: str,
    *,
    attempt_index: int,
    seed: int,
    elapsed_sec: float,
    detail: str | None = None,
) -> dict[str, Any]:
    return (
        {
            "scale": int(label),
            "scale_label": label,
            "attempt_index": int(attempt_index),
            "seed": int(seed),
            "reason": str(reason),
            "elapsed_sec": round(float(elapsed_sec), 6),
            "detail": detail,
        }
    )


def _append_unique_skip(manifest: dict[str, Any], skip: dict[str, Any]) -> None:
    skips = manifest.setdefault("skips", [])
    key = (str(skip.get("scale_label")), int(skip.get("attempt_index", -1)), int(skip.get("seed", -1)), str(skip.get("reason")))
    for old in skips:
        old_key = (
            str(old.get("scale_label")),
            int(old.get("attempt_index", -1)),
            int(old.get("seed", -1)),
            str(old.get("reason")),
        )
        if old_key == key:
            return
    skips.append(skip)


def _clear_selected_sp50_outputs(output_root: Path, manifest_path: Path, scales: list[int]) -> None:
    for scale in scales:
        scale_dir = output_root / f"lunar_ice_sp50_{scale_label(int(scale))}"
        if scale_dir.exists():
            for path in scale_dir.glob("instance_*_logical_graph.json"):
                path.unlink()
    if manifest_path.exists():
        manifest_path.unlink()


def _assert_bpc_future_untouched() -> None:
    repo = Path("/home/kai/work/gnn_bb")
    if not repo.exists():
        return
    result = subprocess.run(
        ["git", "-C", str(repo), "status", "--short", "--", "BPC_future"],
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "failed to check BPC_future status")
    if result.stdout.strip():
        raise RuntimeError("BPC_future has local changes; refusing to generate real-map benchmark")


def _replace_or_append_instance_row(manifest: dict[str, Any], row: dict[str, Any]) -> None:
    rows = manifest.setdefault("instances", [])
    for index, old in enumerate(rows):
        if str(old.get("path")) == str(row.get("path")):
            rows[index] = row
            return
    rows.append(row)


def _accepted_rows_for_scale(manifest: dict[str, Any], label: str) -> list[dict[str, Any]]:
    rows = [row for row in manifest.get("instances", []) if str(row.get("scale_label")) == label and row.get("status") == "accepted"]
    existing = []
    for row in rows:
        path = ROOT / str(row.get("path", ""))
        if path.exists():
            existing.append(row)
    return sorted(existing, key=lambda row: str(row.get("path", "")))


def _accepted_indices_for_scale(manifest: dict[str, Any], label: str) -> set[int]:
    indices: set[int] = set()
    for row in _accepted_rows_for_scale(manifest, label):
        path = Path(str(row.get("path", "")))
        stem = path.stem
        parts = stem.split("_")
        for part in parts:
            if part.isdigit():
                value = int(part)
                if value > 0:
                    indices.add(value)
                    break
    return indices


def _manifest_attempt_count(manifest: dict[str, Any], label: str) -> int:
    scale_info = (manifest.get("scales") or {}).get(label) or {}
    return int(scale_info.get("attempt_count") or 0)


def _mark_scale_stopped(manifest: dict[str, Any], label: str, reason: str) -> None:
    scale_info = manifest.setdefault("scales", {}).setdefault(label, {})
    scale_info["status"] = "stopped"
    scale_info["stopped_reason"] = reason


def _skip_reason_from_issues(instance: dict[str, Any], issues: list[str]) -> str:
    for prefix in (
        "validation_not_accepted:",
        "missing_candidate_role:",
        "task_count_mismatch:",
        "node_count_mismatch:",
        "edge_count_mismatch:",
        "edge_path_option_count_mismatch:",
    ):
        for issue in issues:
            if issue.startswith(prefix):
                return issue
    if issues:
        return "validation_error"
    return str((instance.get("validation") or {}).get("reason", "unknown_reject"))


def _time_window_mode_for_index(index: int) -> str:
    slot = (int(index) - 1) % 20
    if slot < 7:
        return "outer_to_inner"
    if slot < 14:
        return "inner_to_outer"
    return "easy_to_hard"


@contextmanager
def _optional_time_limit(seconds: float | None) -> Iterator[None]:
    if seconds is None or seconds <= 0:
        yield
        return
    previous_handler = signal.getsignal(signal.SIGALRM)
    def _raise_timeout(signum: int, frame: Any) -> None:
        raise GenerationTimeout(f"instance generation exceeded {seconds} seconds")

    signal.signal(signal.SIGALRM, _raise_timeout)
    signal.setitimer(signal.ITIMER_REAL, float(seconds))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, previous_handler)


def _parse_scales(value: str) -> list[int]:
    scales = [int(item.strip()) for item in str(value).split(",") if item.strip()]
    unsupported = sorted(set(scales) - set(SCALES))
    if unsupported:
        raise ValueError(f"unsupported scales {unsupported}; expected subset of {SCALES}")
    return scales


def _project_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def _manifest_relative_path(path: Path, project_root: Path) -> Path:
    try:
        return path.relative_to(project_root)
    except ValueError:
        return path


def _mean(values: list[float] | list[int]) -> float | None:
    if not values:
        return None
    return round(float(sum(values)) / float(len(values)), 6)


def _max_rss_mb() -> float:
    # Linux reports ru_maxrss in KiB.
    return float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) / 1024.0


def _mem_available_gb() -> float:
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemAvailable:"):
                parts = line.split()
                return float(parts[1]) / (1024.0 * 1024.0)
    except OSError:
        pass
    return 0.0


if __name__ == "__main__":
    raise SystemExit(main())

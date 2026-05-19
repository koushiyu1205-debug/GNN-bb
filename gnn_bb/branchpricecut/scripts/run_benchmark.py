#!/usr/bin/env python3
"""Run resumable branchpricecut benchmark suites with fixed generated instances."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
import math
import os
from pathlib import Path
import platform
import random
import subprocess
import sys
import time
import traceback
from typing import Any

SCRIPT = Path(__file__).resolve()
BRANCHPRICECUT_ROOT = SCRIPT.parents[1]
REPO_ROOT = SCRIPT.parents[2]
SRC = REPO_ROOT / "src"
for path in (REPO_ROOT, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from bpc.data import load_bpc_data
from bpc.solver import solve_bpc_clean
from branchpricecut.data import load_instance
from branchpricecut.solver import solve_vehicle_schedule_bpc
from gnn_bb.data.instances import scalable_task_parameters, scalable_vehicle_parameters, validate_instance_schema


VARIANT_CONFIGS: dict[str, dict[str, Any]] = {
    "bpc_clean_full": {"solver": "bpc_clean", "overrides": {}},
    "hybrid_full": {"solver": "branchpricecut", "overrides": {"master_type": "hybrid_route"}},
    "vehicle_schedule_ng_dssr": {
        "solver": "branchpricecut",
        "config_kind": "vehicle_schedule",
        "overrides": {"master_type": "vehicle_schedule"},
    },
    "hybrid_no_schedcap": {
        "solver": "branchpricecut",
        "overrides": {"master_type": "hybrid_route", "schedule_capacity_cuts_enabled": False},
    },
    "hybrid_no_crossing": {
        "solver": "branchpricecut",
        "overrides": {
            "master_type": "hybrid_route",
            "robust_capacity_cuts_enabled": False,
            "resource_lower_bound_cuts_enabled": False,
        },
    },
    "hybrid_no_task_vehicle_linking": {
        "solver": "branchpricecut",
        "overrides": {"master_type": "hybrid_route", "task_vehicle_linking_enabled": False},
    },
    "hybrid_simple_branching": {
        "solver": "branchpricecut",
        "overrides": {"master_type": "hybrid_route", "branching_strategy": "simple"},
    },
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _append_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()


def _run_capture(command: list[str]) -> str:
    try:
        completed = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    except Exception as exc:
        return f"ERROR: {exc}"
    return (completed.stdout + completed.stderr).strip()


def _distance(left: tuple[float, float], right: tuple[float, float]) -> float:
    return math.hypot(float(left[0]) - float(right[0]), float(left[1]) - float(right[1]))


def _edge(
    coords: dict[str, tuple[float, float]],
    u: str,
    v: str,
    rng: random.Random,
    order: int,
) -> dict[str, float | str]:
    distance = _distance(coords[u], coords[v])
    speed = 1.0 + 0.30 * rng.random()
    energy_rate = 0.50 + 0.14 * rng.random()
    cost_rate = 0.70 + 0.18 * rng.random()
    time_factor = 1.0 + 0.08 * ((order + 1) % 4)
    energy_factor = 1.0 + 0.06 * ((order + 2) % 5)
    cost_factor = 1.0 + 0.05 * ((order + 3) % 5)
    return {
        "u": u,
        "v": v,
        "distance": round(distance, 6),
        "time": round(distance / speed * time_factor, 6),
        "energy": round(distance * energy_rate * energy_factor, 6),
        "cost": round(distance * cost_rate * cost_factor, 6),
    }


def _generate_terrain(size: int, seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    node_count = max(80, size * 4)
    coords = {"p0": (0.0, 0.0)}
    for idx in range(1, node_count):
        angle = 0.59 * idx + 0.23 * (idx % 13) + 0.04 * rng.random()
        radius = 1.5 + 0.085 * idx + 0.75 * rng.random()
        coords[f"p{idx}"] = (
            round(radius * math.cos(angle) + 0.25 * rng.random(), 4),
            round(radius * math.sin(angle) + 0.25 * rng.random(), 4),
        )

    pairs: set[tuple[str, str]] = set()
    node_ids = list(coords)
    for idx in range(node_count - 1):
        pairs.add((f"p{idx}", f"p{idx + 1}"))
    for u in node_ids:
        ux, uy = coords[u]
        nearest = []
        for v in node_ids:
            if u == v:
                continue
            vx, vy = coords[v]
            nearest.append((math.hypot(ux - vx, uy - vy), v))
        nearest.sort()
        for _distance, v in nearest[:5]:
            pairs.add(tuple(sorted((u, v))))

    edge_specs = [_edge(coords, u, v, rng, order) for order, (u, v) in enumerate(sorted(pairs))]
    return {
        "positions": {node: [float(coord[0]), float(coord[1])] for node, coord in coords.items()},
        "edges": edge_specs,
    }


def _build_benchmark_instance(name: str, size: int, seed: int) -> dict[str, Any]:
    rng = random.Random(seed + 17)
    terrain = _generate_terrain(size, seed)
    candidates = [node for node in terrain["positions"] if node != "p0"]
    chosen = sorted(rng.sample(candidates, size), key=lambda item: int(item[1:]))
    tasks = {}
    for task_id, terrain_node in enumerate(chosen, start=1):
        tasks[str(task_id)] = {"terrain_node": terrain_node, **scalable_task_parameters(task_id)}

    instance = {
        "name": name,
        "seed": seed,
        "description": f"benchmark instance: size={size}, index seed={seed}",
        "terrain": terrain,
        "base": {"id": 0, "terrain_node": "p0"},
        "tasks": tasks,
        "vehicles": {},
        "parameter_profile": "benchmark_medium_like_scaled_v1",
        "benchmark_metadata": {"size": size, "seed": seed},
    }
    vehicles, scaling = scalable_vehicle_parameters(instance)
    instance["vehicles"] = vehicles
    instance["scaling_policy"] = scaling
    validate_instance_schema(instance)
    return instance


def _instance_specs(config: dict[str, Any]) -> list[dict[str, Any]]:
    specs = []
    seed_base = int(config.get("seed_base", 20260600))
    per_size = int(config.get("instances_per_size", 10))
    for size in [int(item) for item in config.get("sizes", [10, 20, 30])]:
        for index in range(1, per_size + 1):
            specs.append(
                {
                    "name": f"bench_{size}_{index:02d}",
                    "size": size,
                    "index": index,
                    "seed": seed_base + size * 100 + index,
                }
            )
    return specs


def _ensure_instances(config: dict[str, Any], run_id: str, run_root: Path) -> tuple[Path, list[dict[str, Any]]]:
    instance_dir_text = str(config.get("instance_dir", "branchpricecut/results/benchmark/{run_id}/instances")).format(run_id=run_id)
    instance_dir = Path(instance_dir_text)
    if not instance_dir.is_absolute():
        instance_dir = REPO_ROOT / instance_dir
    instance_dir.mkdir(parents=True, exist_ok=True)
    specs = _instance_specs(config)
    for spec in specs:
        path = instance_dir / f"instance_{spec['name']}.json"
        if not path.exists():
            payload = _build_benchmark_instance(str(spec["name"]), int(spec["size"]), int(spec["seed"]))
            _write_json_atomic(path, payload)
        spec["instance_path"] = str(path)
    _write_json_atomic(run_root / "instances_manifest.json", {"instance_dir": str(instance_dir), "instances": specs})
    return instance_dir, specs


def _load_base_config(config: dict[str, Any], kind: str) -> dict[str, Any]:
    key = "vehicle_schedule_config" if kind == "vehicle_schedule" else "base_solver_config"
    path = REPO_ROOT / str(config.get(key, "branchpricecut/config/medium_hybrid_route.json"))
    base = _read_json(path)
    return base


def _make_solver_config(config: dict[str, Any], run_id: str, instance_dir: Path, variant: str) -> dict[str, Any]:
    meta = VARIANT_CONFIGS[variant]
    kind = str(meta.get("config_kind", "hybrid"))
    solver_config = _load_base_config(config, kind)
    solver_config["instance_dir"] = str(instance_dir)
    solver_config["time_limit"] = float(config.get("time_limit", solver_config.get("time_limit", 3600)))
    solver_config["max_nodes"] = int(config.get("max_nodes", solver_config.get("max_nodes", 100000)))
    solver_config.update(dict(meta.get("overrides", {})))
    solver_config["benchmark_run_id"] = run_id
    solver_config["benchmark_variant"] = variant
    return solver_config


def _make_jobs(config: dict[str, Any], run_id: str, run_root: Path, instance_dir: Path, specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    variants = [str(item) for item in config.get("variants", list(VARIANT_CONFIGS))]
    unknown = sorted(set(variants) - set(VARIANT_CONFIGS))
    if unknown:
        raise ValueError(f"unknown benchmark variants: {unknown}")
    jobs = []
    for spec in specs:
        for variant in variants:
            solver_config = _make_solver_config(config, run_id, instance_dir, variant)
            job_id = f"{variant}__{spec['name']}"
            jobs.append(
                {
                    "run_id": run_id,
                    "job_id": job_id,
                    "variant": variant,
                    "solver": VARIANT_CONFIGS[variant]["solver"],
                    "instance": spec["name"],
                    "size": int(spec["size"]),
                    "instance_index": int(spec["index"]),
                    "seed": int(spec["seed"]),
                    "instance_dir": str(instance_dir),
                    "run_root": str(run_root),
                    "config": solver_config,
                    "log_path": str(run_root / "logs" / variant / f"{spec['name']}.jsonl"),
                    "solution_path": str(run_root / "solutions" / variant / f"solution_{spec['name']}.json"),
                    "result_path": str(run_root / "job_results" / f"{job_id}.json"),
                    "state_path": str(run_root / "job_state" / f"{job_id}.json"),
                    "terminal_log_path": str(run_root / "terminal" / f"{job_id}.log"),
                }
            )
    return jobs


def _save_manifest(config: dict[str, Any], run_id: str, run_root: Path, instance_dir: Path, jobs: list[dict[str, Any]]) -> None:
    manifest = {
        "run_id": run_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "config": config,
        "instance_dir": str(instance_dir),
        "job_count": len(jobs),
        "variants": sorted({job["variant"] for job in jobs}),
        "sizes": sorted({job["size"] for job in jobs}),
        "python": sys.executable,
        "platform": platform.platform(),
        "git_status": _run_capture(["git", "status", "--short"]),
        "git_diff_stat": _run_capture(["git", "diff", "--stat"]),
        "git_head": _run_capture(["git", "rev-parse", "HEAD"]),
    }
    _write_json_atomic(run_root / "manifest.json", manifest)
    _write_json_atomic(run_root / "jobs_manifest.json", {"jobs": jobs})
    (run_root / "git_status.txt").write_text(str(manifest["git_status"]) + "\n", encoding="utf-8")
    (run_root / "git_diff_stat.txt").write_text(str(manifest["git_diff_stat"]) + "\n", encoding="utf-8")


def _as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_log_metrics(path: str | Path) -> dict[str, Any]:
    log_path = Path(path)
    metrics: dict[str, Any] = {
        "time_to_first_incumbent": None,
        "time_to_best_incumbent": None,
        "best_incumbent_from_log": None,
        "root_pricing_events": 0,
        "root_last_pricing_time": None,
        "total_pricing_label_pops": 0,
        "total_pricing_generated_labels": 0,
        "schedule_nogood_cut_events": 0,
        "schedule_pair_conflict_cut_events": 0,
        "crossing_cut_events": 0,
        "schedule_capacity_cut_events": 0,
        "branch_rf_count": 0,
        "branch_task_vehicle_count": 0,
        "branch_arc_count": 0,
        "branch_vehicle_count": 0,
    }
    if not log_path.exists():
        return metrics
    best_obj = None
    with log_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            event = record.get("event")
            timestamp = _as_float(record.get("time"))
            if event == "incumbent":
                objective = _as_float(record.get("objective"))
                if metrics["time_to_first_incumbent"] is None:
                    metrics["time_to_first_incumbent"] = timestamp
                if objective is not None and (best_obj is None or objective < best_obj):
                    best_obj = objective
                    metrics["best_incumbent_from_log"] = objective
                    metrics["time_to_best_incumbent"] = timestamp
            if event in {"pricing", "exact_pricing"}:
                node = record.get("node_id", record.get("node"))
                if str(node) == "0":
                    metrics["root_pricing_events"] += 1
                    metrics["root_last_pricing_time"] = timestamp
                labels = record.get("label_pops", record.get("labels", 0))
                generated = record.get("generated_labels", 0)
                metrics["total_pricing_label_pops"] += int(_as_float(labels) or 0)
                metrics["total_pricing_generated_labels"] += int(_as_float(generated) or 0)
            if event == "cut_added":
                family = str(record.get("family", ""))
                if family == "schedule_pair_conflict":
                    metrics["schedule_pair_conflict_cut_events"] += int(_as_float(record.get("added")) or 1)
                elif family.startswith("schedule_nogood"):
                    metrics["schedule_nogood_cut_events"] += int(_as_float(record.get("added")) or 1)
                elif family == "crossing_cut":
                    metrics["crossing_cut_events"] += int(_as_float(record.get("added")) or 1)
                elif family.startswith("schedule_capacity"):
                    metrics["schedule_capacity_cut_events"] += int(_as_float(record.get("added")) or 1)
            if event == "branch":
                text = f"{record.get('left', '')} {record.get('right', '')}"
                if "RF(" in text or record.get("i") is not None:
                    metrics["branch_rf_count"] += 1
                elif "task_vehicle" in text:
                    metrics["branch_task_vehicle_count"] += 1
                elif "arc(" in text:
                    metrics["branch_arc_count"] += 1
                elif "vehicle(" in text:
                    metrics["branch_vehicle_count"] += 1
    return metrics


def _solve_bpc_clean_job(job: dict[str, Any]) -> dict[str, Any]:
    config = dict(job["config"])
    data = load_bpc_data(str(job["instance"]), instance_dir=job["instance_dir"])
    result = solve_bpc_clean(
        data,
        time_limit=float(config.get("time_limit", 3600)),
        max_nodes=int(config.get("max_nodes", 100000)),
        pricing_eps=float(config.get("pricing_eps", 1.0e-6)),
        integer_tol=float(config.get("integer_tol", 1.0e-6)),
        max_routes_per_pricing=int(config.get("max_routes_per_pricing", 200)),
        max_labels_per_pricing=int(config.get("hybrid_max_labels_per_pricing", config.get("max_labels_per_pricing", 0)) or 0),
        root_max_routes_per_pricing=int(config.get("root_max_routes_per_pricing", 0) or 0),
        heuristic_pricing_enabled=bool(config.get("heuristic_pricing_enabled", False)),
        heuristic_pricing_max_labels=int(config.get("heuristic_pricing_max_labels", 100000)),
        heuristic_pricing_routes_per_round=int(config.get("heuristic_pricing_routes_per_round", 500)),
        heuristic_pricing_selection_mode=str(config.get("heuristic_pricing_selection_mode", "diverse")),
        exact_pricing_selection_mode=str(config.get("exact_pricing_selection_mode", "reduced_cost")),
        branch_node_heuristic_boost_enabled=bool(config.get("branch_node_heuristic_boost_enabled", False)),
        branch_node_heuristic_boost_max_labels=int(config.get("branch_node_heuristic_boost_max_labels", 800000)),
        branch_node_heuristic_boost_routes_per_round=int(config.get("branch_node_heuristic_boost_routes_per_round", 1000)),
        branch_node_heuristic_boost_min_depth=int(config.get("branch_node_heuristic_boost_min_depth", 1)),
        exact_pricing_dominance_enabled=bool(
            config.get("exact_pricing_dominance_enabled", config.get("exact_pricing_enable_dominance", False))
        ),
        restricted_master_heuristic_enabled=bool(config.get("restricted_master_heuristic_enabled", False)),
        restricted_master_time_limit=float(config.get("restricted_master_time_limit", 20.0)),
        restricted_master_max_routes=int(config.get("restricted_master_max_routes", 4000)),
        restricted_master_max_calls=int(config.get("restricted_master_max_calls", 20)),
        restricted_master_max_depth=int(config.get("restricted_master_max_depth", 3)),
        restricted_master_schedule_aware=bool(config.get("restricted_master_schedule_aware", True)),
        restricted_master_max_no_good_rounds=int(config.get("restricted_master_max_no_good_rounds", 20)),
        rmp_params=dict(config.get("rmp_params", {})),
        log_path=job["log_path"],
        solution_path=job["solution_path"],
        seed=int(config["random_seed"]) if config.get("random_seed") is not None else None,
        quiet=True,
        branching_strategy=str(config.get("branching_strategy", "3pb")),
        three_pb_pseudocost_candidates=int(config.get("three_pb_pseudocost_candidates", 6)),
        three_pb_fractional_candidates=int(config.get("three_pb_fractional_candidates", 6)),
        three_pb_lp_candidates=int(config.get("three_pb_lp_candidates", 3)),
        three_pb_heuristic_cg_iterations=int(config.get("three_pb_heuristic_cg_iterations", 3)),
        three_pb_heuristic_routes_per_iter=int(config.get("three_pb_heuristic_routes_per_iter", 50)),
        three_pb_heuristic_max_labels=int(config.get("three_pb_heuristic_max_labels", 800)),
        task_vehicle_linking_enabled=bool(config.get("task_vehicle_linking_enabled", True)),
        robust_capacity_cuts_enabled=bool(config.get("robust_capacity_cuts_enabled", True)),
        robust_capacity_cut_max_depth=int(config.get("robust_capacity_cut_max_depth", 0)),
        robust_capacity_cut_max_subset_size=int(config.get("robust_capacity_cut_max_subset_size", 5)),
        robust_capacity_cut_max_per_round=int(config.get("robust_capacity_cut_max_per_round", 20)),
        robust_capacity_cut_min_violation=float(config.get("robust_capacity_cut_min_violation", 1.0e-5)),
        robust_capacity_cut_max_rounds_per_node=int(config.get("robust_capacity_cut_max_rounds_per_node", 3)),
        resource_lower_bound_cuts_enabled=bool(config.get("resource_lower_bound_cuts_enabled", True)),
        resource_cut_max_depth=int(config.get("resource_cut_max_depth", 0)),
        resource_cut_max_subset_size=int(config.get("resource_cut_max_subset_size", 6)),
        resource_cut_max_per_round=int(config.get("resource_cut_max_per_round", 20)),
        resource_cut_min_violation=float(config.get("resource_cut_min_violation", 1.0e-5)),
        resource_cut_max_rounds_per_node=int(config.get("resource_cut_max_rounds_per_node", 3)),
        schedule_capacity_cuts_enabled=bool(config.get("schedule_capacity_cuts_enabled", True)),
        schedule_capacity_cut_max_depth=int(config.get("schedule_capacity_cut_max_depth", 0)),
        schedule_capacity_cut_max_subset_size=int(config.get("schedule_capacity_cut_max_subset_size", 10)),
        schedule_capacity_cut_max_per_round=int(config.get("schedule_capacity_cut_max_per_round", 20)),
        schedule_capacity_cut_min_violation=float(config.get("schedule_capacity_cut_min_violation", 1.0e-5)),
        schedule_capacity_cut_max_rounds_per_node=int(config.get("schedule_capacity_cut_max_rounds_per_node", 3)),
        schedule_capacity_oracle_max_states=int(config.get("schedule_capacity_oracle_max_states", 200000)),
        schedule_capacity_candidate_top_tasks=int(config.get("schedule_capacity_candidate_top_tasks", 12)),
        schedule_capacity_candidate_max_combinations=int(config.get("schedule_capacity_candidate_max_combinations", 300)),
        schedule_capacity_route_union_top_routes=int(config.get("schedule_capacity_route_union_top_routes", 8)),
        schedule_capacity_route_union_max_routes=int(config.get("schedule_capacity_route_union_max_routes", 4)),
        cut_purge_age=int(config.get("cut_purge_age", 20)),
        cut_purge_slack=float(config.get("cut_purge_slack", 1.0e-5)),
        cut_purge_dual=float(config.get("cut_purge_dual", 1.0e-8)),
    )
    return result.to_row()


def _solve_branchpricecut_job(job: dict[str, Any]) -> dict[str, Any]:
    data = load_instance(str(job["instance"]), instance_dir=job["instance_dir"])
    result = solve_vehicle_schedule_bpc(
        data,
        config=dict(job["config"]),
        log_path=job["log_path"],
        solution_path=job["solution_path"],
        quiet=True,
    )
    return result.to_row()


def run_worker(job_path: Path) -> int:
    job = _read_json(job_path)
    started = time.perf_counter()
    _write_json_atomic(
        Path(job["state_path"]),
        {
            "job_id": job["job_id"],
            "state": "running",
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "pid": os.getpid(),
        },
    )
    try:
        if job["solver"] == "bpc_clean":
            result_row = _solve_bpc_clean_job(job)
        elif job["solver"] == "branchpricecut":
            result_row = _solve_branchpricecut_job(job)
        else:
            raise ValueError(f"unknown solver: {job['solver']}")
        metrics = _parse_log_metrics(job["log_path"])
        payload = {
            "completed": True,
            "error": None,
            "run_id": job["run_id"],
            "job_id": job["job_id"],
            "variant": job["variant"],
            "solver": job["solver"],
            "instance": job["instance"],
            "size": job["size"],
            "instance_index": job["instance_index"],
            "seed": job["seed"],
            "wall_time": round(time.perf_counter() - started, 6),
            "result": result_row,
            "metrics": metrics,
            "paths": {
                "log_path": job["log_path"],
                "solution_path": job["solution_path"],
                "terminal_log_path": job["terminal_log_path"],
            },
            "completed_at": datetime.now().isoformat(timespec="seconds"),
        }
        _write_json_atomic(Path(job["result_path"]), payload)
        _write_json_atomic(Path(job["state_path"]), {"job_id": job["job_id"], "state": "done", "completed_at": payload["completed_at"]})
        return 0
    except Exception:
        payload = {
            "completed": False,
            "error": traceback.format_exc(),
            "run_id": job["run_id"],
            "job_id": job["job_id"],
            "variant": job["variant"],
            "solver": job["solver"],
            "instance": job["instance"],
            "size": job["size"],
            "instance_index": job["instance_index"],
            "seed": job["seed"],
            "wall_time": round(time.perf_counter() - started, 6),
            "result": {"status": "ERROR"},
            "metrics": _parse_log_metrics(job["log_path"]),
            "paths": {
                "log_path": job["log_path"],
                "solution_path": job["solution_path"],
                "terminal_log_path": job["terminal_log_path"],
            },
            "completed_at": datetime.now().isoformat(timespec="seconds"),
        }
        _write_json_atomic(Path(job["result_path"]), payload)
        _write_json_atomic(Path(job["state_path"]), {"job_id": job["job_id"], "state": "error", "completed_at": payload["completed_at"]})
        return 0


def _flatten_result(payload: dict[str, Any]) -> dict[str, Any]:
    row = {
        "run_id": payload.get("run_id"),
        "job_id": payload.get("job_id"),
        "variant": payload.get("variant"),
        "solver": payload.get("solver"),
        "instance": payload.get("instance"),
        "size": payload.get("size"),
        "instance_index": payload.get("instance_index"),
        "seed": payload.get("seed"),
        "completed": payload.get("completed"),
        "error": "" if payload.get("error") is None else "ERROR",
        "worker_wall_time": payload.get("wall_time"),
    }
    for key, value in dict(payload.get("result") or {}).items():
        row[f"result_{key}"] = value
    for key, value in dict(payload.get("metrics") or {}).items():
        row[f"metric_{key}"] = value
    for key, value in dict(payload.get("paths") or {}).items():
        row[f"path_{key}"] = value
    return row


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    seen = set()
    preferred = [
        "run_id",
        "job_id",
        "variant",
        "solver",
        "instance",
        "size",
        "instance_index",
        "seed",
        "completed",
        "error",
        "result_status",
        "result_primal_bound",
        "result_dual_bound",
        "result_gap",
        "result_diagnostic_dual_bound",
        "result_diagnostic_gap",
        "result_solving_time",
        "result_node_count",
        "result_rmp_solves",
        "result_pricing_calls",
        "result_label_pops",
        "result_generated_labels",
        "result_cuts_added",
        "result_schedule_nogood_cuts_added",
        "result_schedule_pair_conflict_cuts_added",
        "result_schedule_capacity_cuts_added",
        "result_crossing_cuts_added",
        "metric_time_to_first_incumbent",
        "metric_time_to_best_incumbent",
        "metric_root_pricing_events",
    ]
    for key in preferred:
        if any(key in row for row in rows):
            fieldnames.append(key)
            seen.add(key)
    for row in rows:
        for key in row:
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _shifted_geomean(values: list[float], shift: float) -> float | None:
    cleaned = [max(0.0, float(value)) + shift for value in values if value is not None]
    if not cleaned:
        return None
    return round(math.exp(sum(math.log(value) for value in cleaned) / len(cleaned)) - shift, 6)


def _write_aggregate(path: Path, rows: list[dict[str, Any]], time_limit: float) -> None:
    groups: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault((str(row.get("variant")), int(row.get("size") or 0)), []).append(row)
    output = []
    for (variant, size), items in sorted(groups.items()):
        statuses = [str(item.get("result_status")) for item in items]
        solved = sum(1 for status in statuses if status == "OPTIMAL")
        time_limit_count = sum(1 for status in statuses if status == "TIME_LIMIT")
        pricing_failures = sum(1 for status in statuses if status in {"PRICING_INCOMPLETE", "PRICING_LIMIT"})
        errors = sum(1 for item in items if item.get("error"))
        times = [_as_float(item.get("result_solving_time")) or time_limit for item in items]
        gaps = [_as_float(item.get("result_gap")) for item in items if _as_float(item.get("result_gap")) is not None]
        labels = [_as_float(item.get("result_label_pops")) for item in items if _as_float(item.get("result_label_pops")) is not None]
        nodes = [_as_float(item.get("result_node_count")) for item in items if _as_float(item.get("result_node_count")) is not None]
        output.append(
            {
                "variant": variant,
                "size": size,
                "jobs": len(items),
                "solved": solved,
                "time_limit": time_limit_count,
                "pricing_failures": pricing_failures,
                "errors": errors,
                "valid_gap_count": len(gaps),
                "avg_gap": None if not gaps else round(sum(gaps) / len(gaps), 6),
                "shifted_geomean_time": _shifted_geomean(times, 10.0),
                "shifted_geomean_labels": _shifted_geomean(labels, 100.0),
                "shifted_geomean_nodes": _shifted_geomean(nodes, 1.0),
            }
        )
    _write_csv(path, output)


def rebuild_summaries(run_root: Path, time_limit: float) -> None:
    payloads = []
    for result_path in sorted((run_root / "job_results").glob("*.json")):
        payloads.append(_read_json(result_path))
    rows = [_flatten_result(payload) for payload in payloads]
    _write_csv(run_root / "summary.csv", rows)
    _write_aggregate(run_root / "aggregate.csv", rows, time_limit)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run 10/20/30 branchpricecut benchmark with resume.")
    parser.add_argument("--config", default=str(BRANCHPRICECUT_ROOT / "config" / "benchmark_10_20_30.json"))
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--time-limit", type=float)
    parser.add_argument("--max-nodes", type=int)
    parser.add_argument("--variants", nargs="*", choices=sorted(VARIANT_CONFIGS))
    parser.add_argument("--force", action="store_true", help="rerun completed jobs")
    parser.add_argument("--limit-jobs", type=int, default=0, help="debug only: run at most this many pending jobs")
    parser.add_argument("--list-jobs", action="store_true")
    parser.add_argument("--worker-job", help=argparse.SUPPRESS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.worker_job:
        raise SystemExit(run_worker(Path(args.worker_job)))

    config = _read_json(Path(args.config))
    if args.time_limit is not None:
        config["time_limit"] = float(args.time_limit)
    if args.max_nodes is not None:
        config["max_nodes"] = int(args.max_nodes)
    if args.variants:
        config["variants"] = list(args.variants)

    run_id = args.run_id or datetime.now().strftime("%Y%m%d_%H%M%S_branchpricecut_benchmark_10_20_30")
    run_root = BRANCHPRICECUT_ROOT / "results" / "benchmark" / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    instance_dir, specs = _ensure_instances(config, run_id, run_root)
    jobs = _make_jobs(config, run_id, run_root, instance_dir, specs)
    _save_manifest(config, run_id, run_root, instance_dir, jobs)

    if args.list_jobs:
        for job in jobs:
            print(job["job_id"])
        print(f"jobs={len(jobs)} run_root={run_root}")
        return

    pending = []
    for job in jobs:
        result_path = Path(job["result_path"])
        if result_path.exists() and not args.force:
            payload = _read_json(result_path)
            if payload.get("completed"):
                continue
        pending.append(job)

    if args.limit_jobs > 0:
        pending = pending[: args.limit_jobs]

    print(
        f"benchmark run_id={run_id} total_jobs={len(jobs)} pending={len(pending)} "
        f"run_root={run_root}",
        flush=True,
    )
    rebuild_summaries(run_root, float(config.get("time_limit", 3600)))

    for index, job in enumerate(pending, start=1):
        job_path = run_root / "jobs" / f"{job['job_id']}.json"
        _write_json_atomic(job_path, job)
        _write_json_atomic(
            Path(job["state_path"]),
            {
                "job_id": job["job_id"],
                "state": "queued",
                "queued_at": datetime.now().isoformat(timespec="seconds"),
            },
        )
        terminal_path = Path(job["terminal_log_path"])
        terminal_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"[{index}/{len(pending)}] {job['job_id']} -> {terminal_path}", flush=True)
        with terminal_path.open("a", encoding="utf-8") as terminal:
            terminal.write(f"\n=== start {datetime.now().isoformat(timespec='seconds')} {job['job_id']} ===\n")
            terminal.flush()
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--worker-job", str(job_path)],
                cwd=REPO_ROOT,
                stdout=terminal,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            terminal.write(f"=== end rc={completed.returncode} {datetime.now().isoformat(timespec='seconds')} ===\n")
            terminal.flush()
        if completed.returncode != 0:
            _write_json_atomic(
                Path(job["result_path"]),
                {
                    "completed": False,
                    "error": f"worker process exited with rc={completed.returncode}",
                    "run_id": job["run_id"],
                    "job_id": job["job_id"],
                    "variant": job["variant"],
                    "solver": job["solver"],
                    "instance": job["instance"],
                    "size": job["size"],
                    "instance_index": job["instance_index"],
                    "seed": job["seed"],
                    "wall_time": None,
                    "result": {"status": "ERROR"},
                    "metrics": _parse_log_metrics(job["log_path"]),
                    "paths": {
                        "log_path": job["log_path"],
                        "solution_path": job["solution_path"],
                        "terminal_log_path": job["terminal_log_path"],
                    },
                },
            )
        rebuild_summaries(run_root, float(config.get("time_limit", 3600)))

    rebuild_summaries(run_root, float(config.get("time_limit", 3600)))
    print(f"benchmark summary: {run_root / 'summary.csv'}", flush=True)
    print(f"benchmark aggregate: {run_root / 'aggregate.csv'}", flush=True)


if __name__ == "__main__":
    main()

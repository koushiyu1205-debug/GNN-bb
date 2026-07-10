#!/usr/bin/env python3
"""Run a resumable V4S/V4SZ 30-scale mature-pool experiment.

The experiment has two exact-safe phases per instance:

1. Build or resume a root-tail active-column pool from the instance JSON with
   the existing staged compact-pricing resume runner.
2. Run the B4.1 tree gate from that mature pool with each requested final-judge
   profile, typically V4S and V4SZ.

Pool building time and final proof/tree-closure time are reported separately.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
STAGED_RESUME = ROOT / "scripts" / "run_lunar_ice_compact_pricing_staged_resume.py"
B41_RUNNER = ROOT / "scripts" / "run_lunar_ice_b4_1_true_dual_proof_tail.py"

DEFAULT_PROOF_PROFILES = ("V4S", "V4SZ")
DEFAULT_POOL_PROFILE = "V4S"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default="runs/b4_1_v4s_v4sz_full30_20x_20260710",
    )
    parser.add_argument(
        "--instance-glob",
        default="data/instances/lunar_ice_sp50_030/instance_*_logical_graph.json",
    )
    parser.add_argument("--instance", action="append", default=[])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--proof-profile", action="append", default=[])
    parser.add_argument("--pool-profile", default=DEFAULT_POOL_PROFILE)
    parser.add_argument("--pool-stage-count", type=int, default=8)
    parser.add_argument("--pool-stage-time-limit-sec", type=float, default=600.0)
    parser.add_argument("--pool-max-rounds-per-stage", type=int, default=1)
    parser.add_argument("--pool-batch-target", type=int, default=1)
    parser.add_argument("--pool-negative-search-cap-sec", type=float, default=600.0)
    parser.add_argument("--pool-optimization-harvest-target", type=int, default=5)
    parser.add_argument(
        "--pool-optimization-harvest-no-good-scope",
        choices=("arc", "task_set", "arc_and_task_set"),
        default="task_set",
    )
    parser.add_argument("--pool-phase-mode", default="feasibility_proof_only")
    parser.add_argument("--tree-closure-time-limit-sec", type=float, default=600.0)
    parser.add_argument("--tree-closure-max-rounds", type=int, default=1)
    parser.add_argument("--tree-closure-max-columns-per-round", type=int, default=128)
    parser.add_argument("--tree-closure-max-nodes", type=int, default=31)
    parser.add_argument("--tree-closure-max-branch-depth", type=int, default=4)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--min-available-mem-gb", type=float, default=2.0)
    parser.add_argument("--min-free-disk-gb", type=float, default=20.0)
    parser.add_argument("--max-output-dir-gb", type=float, default=80.0)
    parser.add_argument(
        "--reuse-probe",
        action="append",
        default=[],
        help=(
            "Optional instance=probe mapping for proof-tail micro-benchmarks. "
            "Rows using this are marked strict_from_json=false and are excluded "
            "from strict end-to-end averages."
        ),
    )
    parser.add_argument(
        "--skip-pool-build",
        action="store_true",
        help="Only run tree closure for instances that already have a certified/latest pool.",
    )
    parser.add_argument("--no-resume", dest="resume", action="store_false", default=True)
    args = parser.parse_args()

    output_dir = _resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    state_path = output_dir / "full30_state.json"
    rows_csv = output_dir / "full30_rows.csv"
    summary_json = output_dir / "full30_summary.json"
    report_md = output_dir / "full30_report_zh.md"

    instances = _instance_paths(args)
    profiles = tuple(args.proof_profile or DEFAULT_PROOF_PROFILES)
    reuse_map = _reuse_probe_map(args.reuse_probe)
    state = _load_state(state_path) if args.resume else {}
    rows = _dedupe_rows(list(state.get("rows") or []))
    seen = {_row_key(row) for row in rows}

    for index, instance_path in enumerate(instances, start=1):
        if not _resource_ok(
            output_dir=output_dir,
            min_available_mem_gb=float(args.min_available_mem_gb),
            min_free_disk_gb=float(args.min_free_disk_gb),
            max_output_dir_gb=float(args.max_output_dir_gb),
        ):
            rows.append(
                _resource_stop_row(
                    instance_path=instance_path,
                    profile="",
                    phase="resource_precheck",
                    output_dir=output_dir,
                )
            )
            _write_artifacts(rows, state_path=state_path, rows_csv=rows_csv, summary_json=summary_json, report_md=report_md)
            return 2

        instance_key = _instance_key(instance_path)
        pool_dir = output_dir / "pools" / instance_key
        pool_dir.mkdir(parents=True, exist_ok=True)

        pool_row_key = (instance_key, "POOL", str(args.pool_profile), "pool_build")
        existing_pool_index = _row_index(rows, pool_row_key)
        existing_pool_row = rows[existing_pool_index] if existing_pool_index is not None else None
        should_refresh_pool = (
            existing_pool_row is None
            or (
                not bool(existing_pool_row.get("pool_certified"))
                and not bool(args.skip_pool_build)
            )
        )
        if should_refresh_pool:
            pool_row = _run_or_refresh_pool(
                args,
                instance_path=instance_path,
                pool_dir=pool_dir,
                reuse_map=reuse_map,
            )
            if existing_pool_index is None:
                rows.append(pool_row)
            else:
                rows[existing_pool_index] = pool_row
            seen.add(pool_row_key)
            _write_artifacts(
                rows,
                state_path=state_path,
                rows_csv=rows_csv,
                summary_json=summary_json,
                report_md=report_md,
            )
        else:
            pool_row = existing_pool_row or {}

        latest_probe = _latest_pool_probe(pool_dir) or _row_source_probe(pool_row)
        pool_certified = bool(pool_row.get("pool_certified")) and bool(latest_probe)
        for profile in profiles:
            key = (instance_key, str(profile), "proof_only", "tree_closure")
            existing_proof_index = _row_index(rows, key)
            existing_proof = rows[existing_proof_index] if existing_proof_index is not None else None
            if existing_proof is not None and (
                bool(existing_proof.get("exact_certificate"))
                or not pool_certified
            ):
                continue
            if not pool_certified:
                row = {
                    "phase": "tree_closure",
                    "instance_index": index,
                    "instance_key": instance_key,
                    "instance_path": str(instance_path),
                    "profile": str(profile),
                    "profile_phase_mode": "proof_only",
                    "source_probe_json": str(latest_probe or ""),
                    "algorithm_status": "POOL_NOT_CERTIFIED",
                    "certificate_scope": "",
                    "pricing_state": "",
                    "tree_optimal": False,
                    "bpc_tree_optimal": False,
                    "exact_certificate": False,
                    "strict_from_json": bool(pool_row.get("strict_from_json")),
                    "pool_build_wall_time_sec": pool_row.get("pool_build_wall_time_sec"),
                    "pool_elapsed_stage_sum_sec": pool_row.get("pool_elapsed_stage_sum_sec"),
                    "end_to_end_wall_time_sec": None,
                    "end_to_end_stage_sum_sec": None,
                    "wall_time_sec": None,
                    "final_judge_wall_time_sec": None,
                    "active_column_count": pool_row.get("pool_active_column_count"),
                    "note": "pool was not certified; proof-only tree closure skipped",
                }
            else:
                row = _run_tree_closure(
                    args,
                    instance_index=index,
                    instance_path=instance_path,
                    source_probe=latest_probe,
                    profile=str(profile),
                    output_dir=output_dir / "proofs" / instance_key / str(profile),
                )
                row["strict_from_json"] = bool(pool_row.get("strict_from_json"))
                row["pool_build_wall_time_sec"] = pool_row.get("pool_build_wall_time_sec")
                row["pool_elapsed_stage_sum_sec"] = pool_row.get("pool_elapsed_stage_sum_sec")
                row["end_to_end_wall_time_sec"] = _add_optional(
                    pool_row.get("pool_build_wall_time_sec"),
                    row.get("wall_time_sec"),
                )
                row["end_to_end_stage_sum_sec"] = _add_optional(
                    pool_row.get("pool_elapsed_stage_sum_sec"),
                    row.get("wall_time_sec"),
                )
            if existing_proof_index is None:
                rows.append(row)
            else:
                rows[existing_proof_index] = row
            seen.add(key)
            _write_artifacts(
                rows,
                state_path=state_path,
                rows_csv=rows_csv,
                summary_json=summary_json,
                report_md=report_md,
            )

    _write_artifacts(rows, state_path=state_path, rows_csv=rows_csv, summary_json=summary_json, report_md=report_md)
    print(json.dumps(_summary(rows), ensure_ascii=False, indent=2, sort_keys=True))
    print(f"report {report_md}")
    return 0


def _resolve(path: str | Path) -> Path:
    raw = Path(path)
    return raw if raw.is_absolute() else ROOT / raw


def _instance_paths(args: argparse.Namespace) -> list[Path]:
    if args.instance:
        paths = [_resolve(path) for path in args.instance]
    else:
        paths = sorted(ROOT.glob(str(args.instance_glob)))
    limit = max(0, int(args.limit))
    if limit:
        paths = paths[:limit]
    return paths


def _instance_key(path: Path) -> str:
    name = path.name
    if name.startswith("instance_") and "_logical_graph" in name:
        return name.split("_logical_graph", 1)[0]
    return path.stem


def _reuse_probe_map(values: list[str]) -> dict[str, Path]:
    mapped: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"--reuse-probe must be instance=probe, got {value!r}")
        key, raw_path = value.split("=", 1)
        probe = _resolve(raw_path)
        for alias in _instance_aliases(key):
            mapped[alias] = probe
    return mapped


def _instance_aliases(value: str | Path) -> set[str]:
    raw = str(value)
    path = Path(raw)
    key = _instance_key(path) if raw.endswith(".json") else raw
    aliases = {raw, key}
    if key.startswith("instance_"):
        suffix = key.split("instance_", 1)[1]
        aliases.add(suffix)
        aliases.add(f"030_{suffix}")
    return aliases


def _load_state(path: Path) -> dict:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"state must be a JSON object: {path}")
    return payload


def _row_key(row: dict) -> tuple[str, str, str, str]:
    if str(row.get("phase") or "") == "pool_build":
        return (
            str(row.get("instance_key") or ""),
            "POOL",
            str(row.get("pool_profile") or ""),
            "pool_build",
        )
    if str(row.get("phase") or "") == "tree_closure":
        return (
            str(row.get("instance_key") or ""),
            str(row.get("profile") or ""),
            "proof_only",
            "tree_closure",
        )
    return (
        str(row.get("instance_key") or ""),
        str(row.get("profile") or ""),
        str(row.get("profile_phase_mode") or row.get("pool_phase_mode") or ""),
        str(row.get("phase") or ""),
    )


def _row_index(rows: list[dict], key: tuple[str, str, str, str]) -> int | None:
    for index, row in enumerate(rows):
        if _row_key(row) == key:
            return index
    return None


def _dedupe_rows(rows: list[dict]) -> list[dict]:
    deduped: list[dict] = []
    index_by_key: dict[tuple[str, str, str, str], int] = {}
    for row in rows:
        key = _row_key(row)
        existing = index_by_key.get(key)
        if existing is None:
            index_by_key[key] = len(deduped)
            deduped.append(row)
            continue
        deduped[existing] = row
    return deduped


def _resource_ok(
    *,
    output_dir: Path,
    min_available_mem_gb: float,
    min_free_disk_gb: float,
    max_output_dir_gb: float,
) -> bool:
    available_gb = _available_mem_gb()
    free_disk_gb = shutil.disk_usage(output_dir).free / (1024**3)
    output_gb = _directory_size_bytes(output_dir) / (1024**3)
    return (
        available_gb >= float(min_available_mem_gb)
        and free_disk_gb >= float(min_free_disk_gb)
        and output_gb <= float(max_output_dir_gb)
    )


def _available_mem_gb() -> float:
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        return 999.0
    for line in meminfo.read_text(encoding="utf-8").splitlines():
        if line.startswith("MemAvailable:"):
            parts = line.split()
            if len(parts) >= 2:
                return float(parts[1]) / (1024**2)
    return 999.0


def _directory_size_bytes(path: Path) -> int:
    total = 0
    if not path.exists():
        return 0
    for child in path.rglob("*"):
        if child.is_file():
            try:
                total += child.stat().st_size
            except OSError:
                pass
    return total


def _resource_stop_row(*, instance_path: Path, profile: str, phase: str, output_dir: Path) -> dict:
    return {
        "phase": phase,
        "instance_key": _instance_key(instance_path),
        "instance_path": str(instance_path),
        "profile": profile,
        "algorithm_status": "RESOURCE_GUARD_STOPPED",
        "certificate_scope": "",
        "pricing_state": "",
        "tree_optimal": False,
        "bpc_tree_optimal": False,
        "exact_certificate": False,
        "note": f"resource guard stopped; output_dir={output_dir}",
    }


def _run_or_refresh_pool(
    args: argparse.Namespace,
    *,
    instance_path: Path,
    pool_dir: Path,
    reuse_map: dict[str, Path],
) -> dict:
    started = perf_counter()
    initial_probe = _initial_reuse_probe(instance_path, reuse_map)
    if bool(args.skip_pool_build) and initial_probe:
        probe = json.loads(initial_probe.read_text(encoding="utf-8"))
        return {
            "phase": "pool_build",
            "instance_key": _instance_key(instance_path),
            "instance_path": str(instance_path),
            "profile": "POOL",
            "pool_profile": "external_reuse",
            "pool_phase_mode": "external_reuse",
            "strict_from_json": False,
            "algorithm_status": probe.get("algorithm_status") or "",
            "certificate_scope": probe.get("certificate_scope") or "",
            "pricing_state": probe.get("pricing_state") or "",
            "pool_certified": probe.get("certificate_scope") == "BPC_NODE_LP_CERTIFIED",
            "pool_build_wall_time_sec": round(perf_counter() - started, 6),
            "pool_elapsed_stage_sum_sec": 0.0,
            "pool_stage_count": 0,
            "pool_active_column_count": len(probe.get("active_columns") or []),
            "pool_added_column_count_last_stage": probe.get("added_column_count"),
            "source_probe_json": str(initial_probe),
            "note": "external reuse probe; pool build skipped",
        }
    if not bool(args.skip_pool_build):
        command = [
            sys.executable,
            str(STAGED_RESUME),
            "--instance",
            str(instance_path),
            "--output-dir",
            str(pool_dir),
            "--stage-count",
            str(int(args.pool_stage_count)),
            "--stage-time-limit-sec",
            str(float(args.pool_stage_time_limit_sec)),
            "--max-rounds-per-stage",
            str(int(args.pool_max_rounds_per_stage)),
            "--max-direct-tasks",
            "30",
            "--seed-mode",
            "b0_incumbent_plus_singletons",
            "--batch-target",
            str(int(args.pool_batch_target)),
            "--negative-search-cap-sec",
            str(float(args.pool_negative_search_cap_sec)),
            "--compact-optimization-harvest-target",
            str(int(args.pool_optimization_harvest_target)),
            "--compact-optimization-harvest-no-good-scope",
            str(args.pool_optimization_harvest_no_good_scope),
            "--compact-final-judge-profile",
            str(args.pool_profile),
            "--compact-final-judge-phase-mode",
            str(args.pool_phase_mode),
            "--compact-service-start-depot-travel-lb",
            "--compact-task-to-depot-return-travel-lb",
            "--compact-pair-route-duration-lb",
            "--compact-sortie-slot-position-bounds",
            "--compact-pair-energy-infeasible-cut",
            "--compact-triple-time-window-infeasible-cut",
        ]
        if initial_probe and not _latest_pool_probe(pool_dir):
            command.extend(["--initial-resume-probe", str(initial_probe)])
        env = os.environ.copy()
        env["PYTHONPATH"] = _prepend_pythonpath(env.get("PYTHONPATH", ""), ROOT / "src")
        completed = subprocess.run(
            command,
            cwd=str(ROOT),
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        (pool_dir / "full30_pool_stdout.txt").write_text(completed.stdout, encoding="utf-8")
        (pool_dir / "full30_pool_stderr.txt").write_text(completed.stderr, encoding="utf-8")
        if completed.returncode != 0:
            return {
                "phase": "pool_build",
                "instance_key": _instance_key(instance_path),
                "instance_path": str(instance_path),
                "profile": "POOL",
                "pool_profile": str(args.pool_profile),
                "pool_phase_mode": str(args.pool_phase_mode),
                "algorithm_status": "POOL_BUILD_FAILED",
                "certificate_scope": "",
                "pricing_state": "",
                "pool_certified": False,
                "pool_build_wall_time_sec": round(perf_counter() - started, 6),
                "note": completed.stderr[-1000:] or completed.stdout[-1000:],
            }

    manifest_path = pool_dir / "staged_resume_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    stages = list(manifest.get("stages") or [])
    latest = stages[-1] if stages else {}
    return {
        "phase": "pool_build",
        "instance_key": _instance_key(instance_path),
        "instance_path": str(instance_path),
        "profile": "POOL",
        "pool_profile": str(args.pool_profile),
        "pool_phase_mode": str(args.pool_phase_mode),
        "strict_from_json": True,
        "algorithm_status": latest.get("algorithm_status") or "",
        "certificate_scope": latest.get("certificate_scope") or "",
        "pricing_state": latest.get("pricing_state") or "",
        "pool_certified": latest.get("certificate_scope") == "BPC_NODE_LP_CERTIFIED",
        "pool_build_wall_time_sec": round(perf_counter() - started, 6),
        "pool_elapsed_stage_sum_sec": _sum_float(stages, "elapsed_sec"),
        "pool_stage_count": len(stages),
        "pool_active_column_count": latest.get("active_column_count"),
        "pool_added_column_count_last_stage": latest.get("added_column_count"),
        "source_probe_json": str(_latest_pool_probe(pool_dir) or ""),
        "note": "" if stages else "no staged pool manifest found",
    }


def _initial_reuse_probe(instance_path: Path, reuse_map: dict[str, Path]) -> Path | None:
    for alias in _instance_aliases(instance_path):
        probe = reuse_map.get(alias)
        if probe:
            return probe
    return None


def _latest_pool_probe(pool_dir: Path) -> Path | None:
    manifest_path = pool_dir / "staged_resume_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        latest = manifest.get("latest_probe")
        if latest:
            path = _resolve(latest)
            if path.exists():
                return path
    probes = sorted(pool_dir.glob("stage_*/probe.json"))
    return probes[-1] if probes else None


def _row_source_probe(row: dict) -> Path | None:
    raw = str(row.get("source_probe_json") or "")
    if not raw:
        return None
    path = _resolve(raw)
    return path if path.exists() else None


def _run_tree_closure(
    args: argparse.Namespace,
    *,
    instance_index: int,
    instance_path: Path,
    source_probe: Path,
    profile: str,
    output_dir: Path,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(B41_RUNNER),
        "--output-dir",
        str(output_dir),
        "--source-probe-json",
        str(source_probe),
        "--tree-closure-from-probe",
        "--tree-closure-time-limit-sec",
        str(float(args.tree_closure_time_limit_sec)),
        "--tree-closure-max-rounds",
        str(int(args.tree_closure_max_rounds)),
        "--tree-closure-max-columns-per-round",
        str(int(args.tree_closure_max_columns_per_round)),
        "--tree-closure-max-nodes",
        str(int(args.tree_closure_max_nodes)),
        "--tree-closure-max-branch-depth",
        str(int(args.tree_closure_max_branch_depth)),
        "--threads",
        str(int(args.threads)),
        "--min-available-mem-gb",
        str(float(args.min_available_mem_gb)),
        "--min-free-disk-gb",
        str(float(args.min_free_disk_gb)),
        "--max-output-dir-gb",
        "8",
        "--resource-check-action",
        "stop",
    ]
    if not bool(args.resume):
        command.append("--no-resume")
    env = os.environ.copy()
    env["PYTHONPATH"] = _prepend_pythonpath(env.get("PYTHONPATH", ""), ROOT / "src")
    env["LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE"] = str(profile)
    env["LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE"] = "proof_only"
    started = perf_counter()
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    wall = perf_counter() - started
    (output_dir / "full30_tree_stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (output_dir / "full30_tree_stderr.txt").write_text(completed.stderr, encoding="utf-8")
    result_path = output_dir / "tree_closure_results" / "tree_closure_001.json"
    if not result_path.exists():
        return {
            "phase": "tree_closure",
            "instance_index": instance_index,
            "instance_key": _instance_key(instance_path),
            "instance_path": str(instance_path),
            "profile": str(profile),
            "profile_phase_mode": "proof_only",
            "source_probe_json": str(source_probe),
            "algorithm_status": "TREE_CLOSURE_FAILED",
            "certificate_scope": "",
            "pricing_state": "",
            "tree_optimal": False,
            "bpc_tree_optimal": False,
            "exact_certificate": False,
            "wall_time_sec": round(wall, 6),
            "note": completed.stderr[-1000:] or completed.stdout[-1000:],
        }
    raw = json.loads(result_path.read_text(encoding="utf-8"))
    root = (raw.get("nodes") or [{}])[0]
    final_judge = root.get("final_judge") if isinstance(root.get("final_judge"), dict) else {}
    certificate_scope = raw.get("certificate_scope") or root.get("certificate_scope") or ""
    algorithm_status = raw.get("algorithm_status") or root.get("algorithm_status") or ""
    pricing_state = root.get("pricing_state") or final_judge.get("pricing_state") or ""
    exact_certificate = (
        str(algorithm_status) == "BPC_OPTIMAL"
        and str(certificate_scope) == "BPC_TREE_OPTIMAL"
        and str(pricing_state) == "CERTIFIED_NO_NEGATIVE"
    )
    return {
        "phase": "tree_closure",
        "instance_index": instance_index,
        "instance_key": _instance_key(instance_path),
        "instance_path": str(instance_path),
        "profile": str(profile),
        "profile_phase_mode": "proof_only",
        "source_probe_json": str(source_probe),
        "result_json": str(result_path),
        "algorithm_status": algorithm_status,
        "certificate_scope": certificate_scope,
        "pricing_state": pricing_state,
        "tree_optimal": exact_certificate,
        "bpc_tree_optimal": certificate_scope == "BPC_TREE_OPTIMAL",
        "exact_certificate": exact_certificate,
        "wall_time_sec": round(wall, 6),
        "row_wall_time_sec": raw.get("wall_time") or raw.get("wall_time_sec"),
        "final_judge_wall_time_sec": final_judge.get("wall_time_sec") or final_judge.get("final_judge_wall_time"),
        "active_column_count": root.get("loaded_column_count"),
        "columns_added": root.get("added_column_count"),
        "round_count": root.get("round_count"),
        "final_judge_profile": final_judge.get("compact_final_judge_profile"),
        "final_judge_formulation_profile": final_judge.get("compact_final_judge_formulation_profile"),
        "pricing_proof_kind": final_judge.get("pricing_proof_kind"),
        "best_reduced_cost": final_judge.get("best_reduced_cost"),
        "global_remaining_rc_lb": final_judge.get("global_remaining_rc_lb"),
        "mip_node_count": final_judge.get("mip_node_count"),
        "simplex_iteration_count": final_judge.get("simplex_iteration_count"),
        "tight_sequence_count": final_judge.get("tight_conditional_sequence_big_m_count"),
        "tight_sequence_max_reduction": final_judge.get("tight_conditional_sequence_big_m_max_reduction"),
        "note": "",
    }


def _prepend_pythonpath(existing: str, path: Path) -> str:
    if not existing:
        return str(path)
    return f"{path}{os.pathsep}{existing}"


def _sum_float(rows: list[dict], key: str) -> float:
    total = 0.0
    for row in rows:
        try:
            total += float(row.get(key) or 0.0)
        except (TypeError, ValueError):
            pass
    return round(total, 6)


def _add_optional(left, right) -> float | None:
    try:
        return round(float(left) + float(right), 6)
    except (TypeError, ValueError):
        return None


def _write_artifacts(
    rows: list[dict],
    *,
    state_path: Path,
    rows_csv: Path,
    summary_json: Path,
    report_md: Path,
) -> None:
    state_path.write_text(json.dumps({"rows": rows}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    fieldnames = sorted({key for row in rows for key in row})
    with rows_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    summary = _summary(rows)
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_md.write_text(_render_report(rows, summary), encoding="utf-8")


def _summary(rows: list[dict]) -> dict:
    pool_rows = [row for row in rows if row.get("phase") == "pool_build"]
    proof_rows = [row for row in rows if row.get("phase") == "tree_closure"]
    strict_proof_rows = [row for row in proof_rows if bool(row.get("strict_from_json"))]
    by_profile: dict[str, dict] = {}
    for profile in sorted({str(row.get("profile") or "") for row in proof_rows if row.get("profile")}):
        profile_rows = [row for row in proof_rows if str(row.get("profile") or "") == profile]
        certified = [row for row in profile_rows if bool(row.get("exact_certificate"))]
        strict_profile_rows = [row for row in profile_rows if bool(row.get("strict_from_json"))]
        strict_certified = [row for row in strict_profile_rows if bool(row.get("exact_certificate"))]
        by_profile[profile] = {
            "rows": len(profile_rows),
            "exact_certificate_count": len(certified),
            "failed_or_skipped_count": len(profile_rows) - len(certified),
            "mean_wall_time_sec_certified": _mean(row.get("wall_time_sec") for row in certified),
            "mean_final_judge_wall_time_sec_certified": _mean(
                row.get("final_judge_wall_time_sec") for row in certified
            ),
            "mean_active_column_count_certified": _mean(row.get("active_column_count") for row in certified),
            "strict_from_json_rows": len(strict_profile_rows),
            "strict_from_json_exact_certificate_count": len(strict_certified),
            "strict_from_json_failed_or_skipped_count": len(strict_profile_rows) - len(strict_certified),
            "strict_from_json_mean_end_to_end_wall_time_sec_certified": _mean(
                row.get("end_to_end_wall_time_sec") for row in strict_certified
            ),
            "strict_from_json_mean_end_to_end_stage_sum_sec_certified": _mean(
                row.get("end_to_end_stage_sum_sec") for row in strict_certified
            ),
        }
    return {
        "row_count": len(rows),
        "pool_row_count": len(pool_rows),
        "pool_certified_count": sum(1 for row in pool_rows if bool(row.get("pool_certified"))),
        "strict_from_json_pool_row_count": sum(1 for row in pool_rows if bool(row.get("strict_from_json"))),
        "strict_from_json_pool_certified_count": sum(
            1 for row in pool_rows if bool(row.get("strict_from_json")) and bool(row.get("pool_certified"))
        ),
        "proof_row_count": len(proof_rows),
        "strict_from_json_proof_row_count": len(strict_proof_rows),
        "profiles": by_profile,
    }


def _mean(values) -> float | None:
    numbers = []
    for value in values:
        try:
            numbers.append(float(value))
        except (TypeError, ValueError):
            pass
    if not numbers:
        return None
    return round(sum(numbers) / len(numbers), 6)


def _render_report(rows: list[dict], summary: dict) -> str:
    lines = [
        "# B4.1 V4S/V4SZ Full 30-Scale Experiment",
        "",
        "## Boundary",
        "",
        "- Pool build uses staged true-dual pricing and does not certify by itself unless `BPC_NODE_LP_CERTIFIED` is recorded.",
        "- Final V4S/V4SZ rows are proof-only tree-closure checks from the mature active-column pool.",
        "- `BPC_TREE_OPTIMAL` here means exact optimality for the normalized additive objective, not makespan-in-objective.",
        "- Strict full-solve averages use only `strict_from_json=true`: instance JSON -> staged pool maturity -> final proof/tree gate.",
        "- Reused source-probe rows are proof-tail micro-benchmarks only and are excluded from strict end-to-end averages.",
        "",
        "## Summary",
        "",
        f"- pool rows: `{summary.get('pool_row_count')}`",
        f"- pool certified: `{summary.get('pool_certified_count')}`",
        f"- strict from-json pool certified: `{summary.get('strict_from_json_pool_certified_count')}` / `{summary.get('strict_from_json_pool_row_count')}`",
        f"- proof rows: `{summary.get('proof_row_count')}`",
        f"- strict from-json proof rows: `{summary.get('strict_from_json_proof_row_count')}`",
        "",
        "| profile | rows | exact cert | strict rows | strict exact | strict mean end-to-end wall | strict mean final proof wall | mean active cols |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for profile, item in (summary.get("profiles") or {}).items():
        lines.append(
            "| "
            f"{profile} | "
            f"{item.get('rows')} | "
            f"{item.get('exact_certificate_count')} | "
            f"{item.get('strict_from_json_rows')} | "
            f"{item.get('strict_from_json_exact_certificate_count')} | "
            f"{item.get('strict_from_json_mean_end_to_end_wall_time_sec_certified')} | "
            f"{item.get('mean_final_judge_wall_time_sec_certified')} | "
            f"{item.get('mean_active_column_count_certified')} |"
        )
    lines.extend(
        [
            "",
            "## Per-Instance Rows",
            "",
            "| instance | strict | phase | profile | status | scope | pricing | active cols | pool wall | proof wall | e2e wall | final judge | note |",
            "|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in rows:
        lines.append(
            "| "
            f"{row.get('instance_key')} | "
            f"{row.get('strict_from_json')} | "
            f"{row.get('phase')} | "
            f"{row.get('profile') or row.get('pool_profile')} | "
            f"{row.get('algorithm_status')} | "
            f"{row.get('certificate_scope')} | "
            f"{row.get('pricing_state')} | "
            f"{row.get('active_column_count') or row.get('pool_active_column_count')} | "
            f"{row.get('pool_build_wall_time_sec')} | "
            f"{row.get('wall_time_sec')} | "
            f"{row.get('end_to_end_wall_time_sec')} | "
            f"{row.get('final_judge_wall_time_sec')} | "
            f"{str(row.get('note') or '')[:120]} |"
        )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())

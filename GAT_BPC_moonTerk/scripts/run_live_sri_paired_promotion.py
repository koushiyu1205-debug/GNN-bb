#!/usr/bin/env python3
"""Fresh-process AB/BA paired promotion harness for Native Live SRI V1.

This harness is intentionally stricter than the generic acceptance runner.  A
policy can be promoted only when the complete 20-instance schedule is present,
every repeat is exact and bound to the frozen candidate, and every objective
matches the frozen no-cut reference.  Results and resource heartbeats are
persisted after every subprocess so a launcher restart never requires solver
resume or overwrites prior evidence.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from math import exp, log
import os
from pathlib import Path
import random
import shutil
import signal
import statistics
import subprocess
import sys
from time import monotonic, perf_counter
from typing import Iterable, Mapping

import yaml


ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE_RUNNER = ROOT / "scripts" / "run_lunar_ice_native_spprc_acceptance.py"
FORMAL_SCALES = (5, 10, 20, 30)
SMALL_SCALE_REPEATS = 10
LARGE_SCALE_REPEATS = 3
EXPECTED_INSTANCE_COUNT = 20
GIB = 1024**3


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-cut-config", type=Path, required=True)
    parser.add_argument("--live-config", type=Path, required=True)
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--frozen-baseline-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--scales", nargs="+", type=int, default=FORMAL_SCALES)
    parser.add_argument("--instance", action="append", default=[])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--repeats-small", type=int, default=SMALL_SCALE_REPEATS)
    parser.add_argument("--repeats-large", type=int, default=LARGE_SCALE_REPEATS)
    parser.add_argument("--bootstrap-samples", type=int, default=10_000)
    parser.add_argument("--heartbeat-interval-sec", type=float, default=60.0)
    parser.add_argument("--launcher-timeout-grace-sec", type=float, default=120.0)
    parser.add_argument("--min-available-memory-gb", type=float, default=1.0)
    parser.add_argument("--low-memory-consecutive-samples", type=int, default=2)
    parser.add_argument(
        "--recover-completed-harness-slots",
        action="store_true",
        help="Reuse only already-finished fresh subprocess slots; solver resume remains disabled.",
    )
    parser.add_argument("--keep-going-on-correctness-failure", action="store_true")
    parser.add_argument(
        "--benchmark-only",
        action="store_true",
        help=(
            "Run a paired diagnostic design without authorizing promotion. "
            "This permits custom repeat counts while retaining all correctness gates."
        ),
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    repeats_small = max(1, int(args.repeats_small))
    repeats_large = max(1, int(args.repeats_large))

    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    configs = {
        "no_cut": args.no_cut_config.resolve(),
        "live": args.live_config.resolve(),
    }
    candidate_manifest_path = args.candidate_manifest.resolve()
    baseline_manifest_path = args.frozen_baseline_manifest.resolve()
    candidate_manifest = _read_json(candidate_manifest_path)
    baseline_manifest = _read_json(baseline_manifest_path)
    selected = discover_instances(args.scales, args.instance, limit=args.limit)
    config_hashes = {mode: sha256_file(path) for mode, path in configs.items()}
    reference_objectives = frozen_reference_objectives(baseline_manifest)

    preflight_issues = validate_frozen_inputs(
        configs=configs,
        config_hashes=config_hashes,
        candidate_manifest=candidate_manifest,
        baseline_manifest=baseline_manifest,
        selected=selected,
    )
    preflight = {
        "schema_version": "lunar_ice_bpc.live_sri_promotion_preflight.v2",
        "checked_at_utc": utc_now(),
        "candidate_manifest": str(candidate_manifest_path),
        "frozen_baseline_manifest": str(baseline_manifest_path),
        "config_hashes": config_hashes,
        "candidate_id": candidate_manifest.get("candidate_id"),
        "expected_engine_hash": candidate_manifest.get("native_inprocess_engine_hash"),
        "expected_policy_hash": candidate_manifest.get("policy_hash"),
        "expected_no_cut_policy_hash": candidate_manifest.get("no_cut_policy_hash"),
        "source_bundle_hash": (candidate_manifest.get("source_bundle") or {}).get("sha256"),
        "issues": preflight_issues,
        "passed": not preflight_issues,
    }
    atomic_write_json(output / "promotion_preflight.json", preflight)
    if preflight_issues:
        print(json.dumps(preflight, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    schedule = build_schedule(
        selected,
        output=output,
        scales=tuple(int(scale) for scale in args.scales),
        repeats_small=repeats_small,
        repeats_large=repeats_large,
        configs=configs,
        config_hashes=config_hashes,
    )
    schedule_manifest = {
        "schema_version": "lunar_ice_bpc.live_sri_promotion_schedule.v2",
        "created_at_utc": utc_now(),
        "slot_count": len(schedule),
        "scales": [int(scale) for scale in args.scales],
        "strict_cold_start": True,
        "solver_resume": False,
        "fresh_python_native_runtime_per_slot": True,
        "ab_ba_alternation": True,
        "slots": schedule,
    }
    atomic_write_json(output / "promotion_schedule.json", schedule_manifest)

    rows_path = output / "promotion_rows.json"
    rows: list[dict] = []
    if rows_path.exists():
        if not args.recover_completed_harness_slots:
            raise SystemExit(
                "promotion_rows.json already exists; use a new output directory or "
                "--recover-completed-harness-slots"
            )
        rows = list(_read_json(rows_path))
    completed_by_slot = index_completed_rows(rows, schedule)
    recovered_slot_count = len(completed_by_slot)
    started = perf_counter()
    stopped_reason = ""

    for spec in schedule:
        slot_id = str(spec["slot_id"])
        if slot_id in completed_by_slot:
            continue
        binding_issues = validate_candidate_source_bundle(candidate_manifest)
        if binding_issues:
            stopped_reason = "CANDIDATE_BINDING_DRIFT:" + ",".join(binding_issues)
            break

        row = dict(spec)
        if args.dry_run:
            row.update(
                {
                    "status": "DRY_RUN",
                    "returncode": 0,
                    "exact": False,
                    "redlines_zero": False,
                    "completed_at_utc": utc_now(),
                }
            )
        else:
            slot_dir = Path(str(spec["slot_dir"]))
            run_dir, attempt_number = next_attempt_dir(slot_dir)
            run_dir.mkdir(parents=True, exist_ok=False)
            row["run_dir"] = str(run_dir)
            row["attempt_number"] = attempt_number
            command = [
                sys.executable,
                str(ACCEPTANCE_RUNNER),
                "--config",
                str(spec["config"]),
                "--scales",
                str(spec["scale"]),
                "--instance",
                str(spec["instance"]),
                "--output-dir",
                str(run_dir),
                "--no-resume",
            ]
            row["command"] = command
            profile = config_profile(Path(str(spec["config"])), int(spec["scale"]))
            row_limit_sec = float(profile["row_time_limit_sec"])
            memory_limit_gb = float(profile["memory_limit_gb"])
            run_started = perf_counter()
            monitor = run_monitored(
                command,
                cwd=ROOT,
                run_dir=run_dir,
                slot_id=slot_id,
                heartbeat_csv=output / "resource_heartbeat.csv",
                heartbeat_interval_sec=max(1.0, float(args.heartbeat_interval_sec)),
                timeout_sec=row_limit_sec + max(0.0, float(args.launcher_timeout_grace_sec)),
                effective_memory_limit_gb=effective_memory_limit_gb(memory_limit_gb),
                min_available_memory_gb=max(0.0, float(args.min_available_memory_gb)),
                low_memory_consecutive_samples=max(
                    1, int(args.low_memory_consecutive_samples)
                ),
            )
            row.update(
                read_run_result(
                    run_dir,
                    scale=int(spec["scale"]),
                    returncode=int(monitor["returncode"]),
                )
            )
            row.update(monitor)
            row["launcher_wall_time_sec"] = round(perf_counter() - run_started, 6)
            row["completed_at_utc"] = utc_now()

        rows.append(row)
        completed_by_slot[slot_id] = row
        write_rows(rows_path, output / "promotion_rows.csv", rows)
        atomic_write_json(
            output / "promotion_progress.json",
            {
                "schema_version": "lunar_ice_bpc.live_sri_promotion_progress.v2",
                "updated_at_utc": utc_now(),
                "expected_slot_count": len(schedule),
                "completed_slot_count": len(completed_by_slot),
                "recovered_slot_count": recovered_slot_count,
                "last_slot_id": slot_id,
                "last_status": row.get("status"),
                "last_exact": row.get("exact"),
                "solver_resume": False,
            },
        )
        if not args.dry_run and not row_correctness_basics(
            row,
            expected_engine_hash=str(candidate_manifest["native_inprocess_engine_hash"]),
            expected_policy_hash=str(candidate_manifest["policy_hash"]),
            expected_no_cut_policy_hash=str(candidate_manifest["no_cut_policy_hash"]),
            reference_objective=reference_objectives.get(
                (int(row["scale"]), str(row["instance_key"]))
            ),
        ):
            if not args.keep_going_on_correctness_failure:
                stopped_reason = f"CORRECTNESS_FAILURE:{slot_id}"
                break

    final_binding_issues = validate_candidate_source_bundle(candidate_manifest)
    if final_binding_issues and not stopped_reason:
        stopped_reason = "CANDIDATE_BINDING_DRIFT_AT_END:" + ",".join(
            final_binding_issues
        )
    summary = summarize_promotion(
        rows,
        schedule=schedule,
        reference_objectives=reference_objectives,
        expected_engine_hash=str(candidate_manifest["native_inprocess_engine_hash"]),
        expected_policy_hash=str(candidate_manifest["policy_hash"]),
        expected_no_cut_policy_hash=str(candidate_manifest["no_cut_policy_hash"]),
        bootstrap_samples=max(100, int(args.bootstrap_samples)),
        repeats_small=repeats_small,
        repeats_large=repeats_large,
        benchmark_only=bool(args.benchmark_only),
        dry_run=bool(args.dry_run),
    )
    summary.update(
        {
            "schema_version": "lunar_ice_bpc.live_sri_paired_promotion.v2",
            "no_cut_config": str(configs["no_cut"]),
            "live_config": str(configs["live"]),
            "candidate_manifest": str(candidate_manifest_path),
            "frozen_baseline_manifest": str(baseline_manifest_path),
            "config_hashes": config_hashes,
            "expected_engine_hash": candidate_manifest["native_inprocess_engine_hash"],
            "expected_policy_hash": candidate_manifest["policy_hash"],
            "expected_no_cut_policy_hash": candidate_manifest["no_cut_policy_hash"],
            "source_bundle_hash": (candidate_manifest.get("source_bundle") or {}).get(
                "sha256"
            ),
            "strict_cold_start": True,
            "solver_resume": False,
            "harness_recovery_enabled": bool(
                args.recover_completed_harness_slots
            ),
            "recovered_slot_count": recovered_slot_count,
            "ab_ba_alternation": True,
            "fresh_python_native_runtime_per_slot": True,
            "benchmark_only": bool(args.benchmark_only),
            "repeats_small": repeats_small,
            "repeats_large": repeats_large,
            "stopped_reason": stopped_reason,
            "final_binding_issues": final_binding_issues,
            "wall_time_sec": round(perf_counter() - started, 6),
        }
    )
    atomic_write_json(output / "promotion_summary.json", summary)
    atomic_write_text(output / "promotion_report_zh.md", render_report(summary))
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return (
        0
        if args.dry_run
        or summary.get("all_scales_promoted")
        or summary.get("benchmark_complete")
        else 3
    )


def build_schedule(
    selected: Mapping[int, tuple[Path, ...]],
    *,
    output: Path,
    scales: tuple[int, ...],
    repeats_small: int,
    repeats_large: int,
    configs: Mapping[str, Path],
    config_hashes: Mapping[str, str],
) -> list[dict]:
    schedule: list[dict] = []
    for scale in scales:
        repetitions = repeats_small if int(scale) in {5, 10} else repeats_large
        for instance_index, instance in enumerate(selected.get(int(scale), tuple())):
            instance_hash = sha256_file(instance)
            instance_key = instance_key_from_path(instance)
            for repetition in range(1, repetitions + 1):
                order = (
                    ("no_cut", "live")
                    if (instance_index + repetition) % 2 == 1
                    else ("live", "no_cut")
                )
                for order_index, mode in enumerate(order, start=1):
                    slot_id = (
                        f"s{scale:03d}:{instance_key}:r{repetition:02d}:"
                        f"o{order_index}:{mode}"
                    )
                    slot_dir = (
                        output
                        / "raw"
                        / f"scale_{scale:03d}"
                        / instance.stem
                        / f"repeat_{repetition:02d}"
                        / f"{order_index}_{mode}"
                    )
                    schedule.append(
                        {
                            "slot_id": slot_id,
                            "scale": int(scale),
                            "instance": str(instance),
                            "instance_key": instance_key,
                            "instance_sha256": instance_hash,
                            "repetition": repetition,
                            "order": "/".join(order),
                            "order_index": order_index,
                            "mode": mode,
                            "config": str(configs[mode]),
                            "config_sha256": config_hashes[mode],
                            "slot_dir": str(slot_dir),
                        }
                    )
    return schedule


def discover_instances(
    scales: Iterable[int], explicit: list[str], *, limit: int
) -> dict[int, tuple[Path, ...]]:
    scale_tuple = tuple(int(scale) for scale in scales)
    selected: dict[int, list[Path]] = {scale: [] for scale in scale_tuple}
    for raw in explicit:
        path = Path(raw).resolve()
        payload = json.loads(path.read_text(encoding="utf-8"))
        selected.setdefault(int(payload["scale"]), []).append(path)
    for scale in scale_tuple:
        if not selected[scale]:
            selected[scale] = sorted(
                (ROOT / "data" / "instances" / f"lunar_ice_sp50_{scale:03d}").glob(
                    "instance_*_logical_graph.json"
                )
            )
        if limit:
            selected[scale] = selected[scale][: int(limit)]
    return {scale: tuple(paths) for scale, paths in selected.items()}


def validate_frozen_inputs(
    *,
    configs: Mapping[str, Path],
    config_hashes: Mapping[str, str],
    candidate_manifest: Mapping,
    baseline_manifest: Mapping,
    selected: Mapping[int, tuple[Path, ...]],
) -> list[str]:
    issues = validate_candidate_source_bundle(candidate_manifest)
    if candidate_manifest.get("candidate_id") != "FROZEN_NATIVE_LIVE_SRI_P0_CANDIDATE_V1":
        issues.append("candidate_id_not_formal_p0_freeze")
    if str(candidate_manifest.get("policy_name")) != "P0":
        issues.append("candidate_policy_not_p0")
    if config_hashes["live"] != candidate_manifest.get("config_sha256"):
        issues.append("live_config_sha256_mismatch")
    if baseline_manifest.get("freeze_id") != "FROZEN_NATIVE_NO_CUT_BASELINE_V1":
        issues.append("baseline_freeze_id_mismatch")
    if config_hashes["no_cut"] != baseline_manifest.get("config_sha256"):
        issues.append("no_cut_config_sha256_mismatch")
    frozen_instances = {
        (int(scale), Path(row["path"]).stem): str(row["sha256"])
        for scale, rows in (baseline_manifest.get("instances") or {}).items()
        for row in rows
    }
    for scale, paths in selected.items():
        for path in paths:
            expected = frozen_instances.get((int(scale), path.stem))
            if expected is None:
                issues.append(f"instance_not_in_frozen_baseline:{scale}:{path.stem}")
            elif sha256_file(path) != expected:
                issues.append(f"instance_sha256_mismatch:{scale}:{path.stem}")
    live_config = yaml.safe_load(configs["live"].read_text(encoding="utf-8"))
    if str(live_config.get("live_sri_policy")) != "P0":
        issues.append("live_config_policy_not_p0")
    no_cut_config = yaml.safe_load(configs["no_cut"].read_text(encoding="utf-8"))
    if str(no_cut_config.get("live_sri_policy", "no_cut")) != "no_cut":
        issues.append("control_config_not_no_cut")
    return sorted(set(issues))


def validate_candidate_source_bundle(candidate_manifest: Mapping) -> list[str]:
    issues: list[str] = []
    bundle = candidate_manifest.get("source_bundle") or {}
    files = bundle.get("files") or []
    if not files:
        return ["candidate_source_bundle_missing"]
    actual_rows = []
    for row in files:
        relative = str(row.get("path") or "")
        path = ROOT / relative
        if not path.is_file():
            issues.append(f"candidate_file_missing:{relative}")
            continue
        actual_hash = sha256_file(path)
        actual_rows.append({"path": relative, "sha256": actual_hash})
        if actual_hash != row.get("sha256"):
            issues.append(f"candidate_file_hash_mismatch:{relative}")
    if not issues:
        actual_bundle_hash = stable_payload_hash(actual_rows)
        if actual_bundle_hash != bundle.get("sha256"):
            issues.append("candidate_source_bundle_hash_mismatch")
    module_path = ROOT / str(candidate_manifest.get("native_module_path") or "")
    if not module_path.is_file():
        issues.append("native_module_missing")
    elif sha256_file(module_path) != candidate_manifest.get("native_module_sha256"):
        issues.append("native_module_sha256_mismatch")
    return issues


def frozen_reference_objectives(baseline_manifest: Mapping) -> dict[tuple[int, str], float]:
    summary_path = Path(str(baseline_manifest.get("summary_path") or ""))
    if not summary_path.is_absolute():
        summary_path = ROOT / summary_path
    if not summary_path.is_file():
        summary_path = ROOT / "runs/native_spprc_no_cut_5_30_full3600_frozen_v1/baseline_summary.json"
    summary = _read_json(summary_path)
    return {
        (int(row["scale"]), str(row["instance_id"])): float(row["incumbent_objective"])
        for row in summary.get("rows", [])
        if row.get("incumbent_objective") is not None
    }


def read_run_result(run_dir: Path, *, scale: int, returncode: int) -> dict:
    summary_path = run_dir / "native_spprc_acceptance_summary.json"
    if not summary_path.exists():
        return {
            "status": "MISSING_SUMMARY",
            "returncode": returncode,
            "exact": False,
            "redlines_zero": False,
        }
    summary = _read_json(summary_path)
    acceptance_row = (summary.get("rows") or [{}])[0]
    state_path = run_dir / f"scale_{scale:03d}" / "b4_2_cold_exact_state.json"
    state = _read_json(state_path) if state_path.exists() else {}
    cold_row = (state.get("rows") or [{}])[0]
    tree_paths = sorted((run_dir / f"scale_{scale:03d}").glob("**/tree_closure_001.json"))
    tree = _read_json(tree_paths[-1]) if tree_paths else {}
    exact = bool(
        returncode == 0
        and acceptance_row.get("status") == "EXACT_CLOSED"
        and tree.get("exact_status") == "BPC_TREE_OPTIMAL"
    )
    policy_payload = tree.get("live_sri_policy")
    policy_name = (
        str(policy_payload.get("name"))
        if isinstance(policy_payload, dict)
        else "no_cut"
    )
    node_cut_counts = [int(node.get("cut_count") or 0) for node in tree.get("nodes", [])]
    return {
        "status": acceptance_row.get("status") or "UNKNOWN",
        "returncode": int(returncode),
        "cold_start_total_sec": cold_row.get("cold_start_total_sec"),
        "root_cg_sec": cold_row.get("root_cg_sec"),
        "tree_sec": cold_row.get("tree_sec"),
        "exact": exact,
        "redlines_zero": bool(acceptance_row.get("redlines_zero")),
        "engine_hash_valid": bool(
            (acceptance_row.get("engine_binding") or {}).get("valid")
        ),
        "engine_build_hash": acceptance_row.get("engine_build_hash_at_start"),
        "objective": tree.get("incumbent_objective"),
        "global_lower_bound": tree.get("global_lower_bound"),
        "certificate_scope": tree.get("certificate_scope"),
        "all_certificate_ledgers_valid": tree.get("all_certificate_ledgers_valid"),
        "all_node_lower_bounds_official": tree.get("all_node_lower_bounds_official"),
        "all_node_pricing_proofs_certifying": tree.get(
            "all_node_pricing_proofs_certifying"
        ),
        "tree_certificate_gate_issues": tree.get("tree_certificate_gate_issues") or [],
        "live_sri_policy_name": policy_name,
        "live_cut_policy_hash": tree.get("live_cut_policy_hash") or "",
        "max_active_cut_count": max(node_cut_counts, default=0),
        "certificate_leak": int(cold_row.get("certificate_leak") or 0),
        "pricing_rc_fail": int(cold_row.get("pricing_rc_fail") or 0),
        "manual_rc_fail": int(cold_row.get("manual_rc_fail") or 0),
        "no_cheat_pass": bool(cold_row.get("no_cheat_pass")),
        "same_run_checkpoint_resume_used": bool(
            cold_row.get("same_run_checkpoint_resume_used")
        ),
        "external_probe_used": bool(cold_row.get("external_probe_used")),
        "mature_pool_used": bool(cold_row.get("mature_pool_used")),
        "manual_columns_used": bool(cold_row.get("manual_columns_used")),
        "row_budget_exhausted": bool(cold_row.get("row_budget_exhausted")),
    }


def row_correctness_basics(
    row: Mapping,
    *,
    expected_engine_hash: str,
    expected_policy_hash: str,
    expected_no_cut_policy_hash: str,
    reference_objective: float | None,
) -> bool:
    objective = row.get("objective")
    mode = str(row.get("mode"))
    expected_policy_name = "P0" if mode == "live" else "no_cut"
    policy_hash_ok = row.get("live_cut_policy_hash") == (
        expected_policy_hash if mode == "live" else expected_no_cut_policy_hash
    )
    return bool(
        row.get("exact")
        and row.get("redlines_zero")
        and row.get("engine_hash_valid")
        and row.get("engine_build_hash") == expected_engine_hash
        and row.get("certificate_scope") == "BPC_TREE_OPTIMAL"
        and row.get("all_certificate_ledgers_valid") is True
        and row.get("all_node_lower_bounds_official") is True
        and row.get("all_node_pricing_proofs_certifying") is True
        and not row.get("tree_certificate_gate_issues")
        and row.get("live_sri_policy_name") == expected_policy_name
        and policy_hash_ok
        and int(row.get("certificate_leak") or 0) == 0
        and int(row.get("pricing_rc_fail") or 0) == 0
        and int(row.get("manual_rc_fail") or 0) == 0
        and row.get("no_cheat_pass")
        and not row.get("same_run_checkpoint_resume_used")
        and not row.get("external_probe_used")
        and not row.get("mature_pool_used")
        and not row.get("manual_columns_used")
        and not row.get("row_budget_exhausted")
        and not row.get("launcher_termination_reason")
        and objective is not None
        and reference_objective is not None
        and abs(float(objective) - float(reference_objective)) <= 1.0e-6
        and row.get("cold_start_total_sec") is not None
        and float(row["cold_start_total_sec"]) <= 3600.0
    )


def summarize_promotion(
    rows: list[dict],
    *,
    schedule: list[dict],
    reference_objectives: Mapping[tuple[int, str], float],
    expected_engine_hash: str,
    expected_policy_hash: str,
    expected_no_cut_policy_hash: str,
    bootstrap_samples: int,
    repeats_small: int = SMALL_SCALE_REPEATS,
    repeats_large: int = LARGE_SCALE_REPEATS,
    benchmark_only: bool = False,
    dry_run: bool,
) -> dict:
    expected_ids = {str(row["slot_id"]) for row in schedule}
    actual_ids = [str(row.get("slot_id")) for row in rows]
    schedule_complete = set(actual_ids) == expected_ids and len(actual_ids) == len(expected_ids)
    scales = sorted({int(row["scale"]) for row in schedule})
    by_scale: dict[str, dict] = {}
    for scale in scales:
        scale_schedule = [row for row in schedule if int(row["scale"]) == scale]
        scale_rows = [row for row in rows if int(row.get("scale", -1)) == scale]
        expected_scale_ids = {str(row["slot_id"]) for row in scale_schedule}
        actual_scale_ids = [str(row.get("slot_id")) for row in scale_rows]
        scale_schedule_complete = (
            set(actual_scale_ids) == expected_scale_ids
            and len(actual_scale_ids) == len(expected_scale_ids)
        )
        by_instance: dict[str, dict[str, list[dict]]] = {}
        for row in scale_rows:
            by_instance.setdefault(str(row["instance_key"]), {}).setdefault(
                str(row["mode"]), []
            ).append(row)
        pairs = []
        scale_correctness = scale_schedule_complete
        expected_instances = sorted(
            {str(row["instance_key"]) for row in scale_schedule}
        )
        for instance_key in expected_instances:
            modes = by_instance.get(instance_key, {})
            base_rows = modes.get("no_cut", [])
            live_rows = modes.get("live", [])
            expected_repeats = (
                repeats_small if scale in {5, 10} else repeats_large
            )
            reference = reference_objectives.get((scale, instance_key))
            row_correct = bool(
                len(base_rows) == expected_repeats
                and len(live_rows) == expected_repeats
                and {int(row["repetition"]) for row in base_rows}
                == set(range(1, expected_repeats + 1))
                and {int(row["repetition"]) for row in live_rows}
                == set(range(1, expected_repeats + 1))
                and all(
                    row_correctness_basics(
                        row,
                        expected_engine_hash=expected_engine_hash,
                        expected_policy_hash=expected_policy_hash,
                        expected_no_cut_policy_hash=expected_no_cut_policy_hash,
                        reference_objective=reference,
                    )
                    for row in (*base_rows, *live_rows)
                )
            )
            scale_correctness = scale_correctness and row_correct
            base_times = [
                float(row["cold_start_total_sec"])
                for row in base_rows
                if row.get("cold_start_total_sec") is not None
            ]
            live_times = [
                float(row["cold_start_total_sec"])
                for row in live_rows
                if row.get("cold_start_total_sec") is not None
            ]
            if len(base_times) != expected_repeats or len(live_times) != expected_repeats:
                continue
            base_median = statistics.median(base_times)
            live_median = statistics.median(live_times)
            pairs.append(
                {
                    "instance_key": instance_key,
                    "base_repeat_median_sec": base_median,
                    "live_repeat_median_sec": live_median,
                    "paired_ratio": live_median / base_median,
                    "correctness_pass": row_correct,
                }
            )
        base_values = [row["base_repeat_median_sec"] for row in pairs]
        live_values = [row["live_repeat_median_sec"] for row in pairs]
        ratios = [row["paired_ratio"] for row in pairs]
        ci = bootstrap_geometric_mean_ci(
            ratios,
            samples=bootstrap_samples,
            seed=72022026 + scale,
        )
        base_mean = statistics.mean(base_values) if base_values else None
        live_mean = statistics.mean(live_values) if live_values else None
        base_p50 = statistics.median(base_values) if base_values else None
        live_p50 = statistics.median(live_values) if live_values else None
        geometric = geometric_mean(ratios)
        full_instance_count = len(expected_instances) == EXPECTED_INSTANCE_COUNT
        paired_design_complete = bool(
            scale_schedule_complete
            and full_instance_count
            and len(pairs) == EXPECTED_INSTANCE_COUNT
        )
        formal_repeat_count = (
            repeats_small == SMALL_SCALE_REPEATS
            if scale in {5, 10}
            else repeats_large == LARGE_SCALE_REPEATS
        )
        formal_scale_design_complete = bool(
            paired_design_complete and formal_repeat_count
        )
        if scale in {20, 30}:
            performance_gate = bool(
                paired_design_complete
                and base_p50
                and base_mean
                and live_p50 <= 0.90 * base_p50
                and live_mean <= base_mean
                and geometric is not None
                and geometric <= 0.90
                and ci[1] is not None
                and ci[1] < 1.0
            )
        else:
            performance_gate = bool(
                paired_design_complete
                and base_p50
                and base_mean
                and live_p50 <= 1.05 * base_p50
                and live_mean <= 1.05 * base_mean
                and geometric is not None
                and geometric <= 1.05
                and ci[1] is not None
                and ci[1] < 1.10
            )
        by_scale[str(scale)] = {
            "expected_instance_count": len(expected_instances),
            "paired_instance_count": len(pairs),
            "expected_slot_count": len(scale_schedule),
            "completed_slot_count": len(scale_rows),
            "schedule_complete": scale_schedule_complete,
            "paired_design_complete": paired_design_complete,
            "formal_design_complete": formal_scale_design_complete,
            "base_mean_sec": base_mean,
            "live_mean_sec": live_mean,
            "live_base_mean_ratio": (
                None if not base_mean or live_mean is None else live_mean / base_mean
            ),
            "base_p50_sec": base_p50,
            "live_p50_sec": live_p50,
            "live_base_p50_ratio": (
                None if not base_p50 or live_p50 is None else live_p50 / base_p50
            ),
            "paired_ratio_point_estimate": geometric,
            "paired_ratio_median": statistics.median(ratios) if ratios else None,
            "paired_ratio_geometric_mean": geometric,
            "paired_bootstrap_95_ci_geometric_mean": list(ci),
            "improved_instance_count": sum(ratio < 1.0 for ratio in ratios),
            "degraded_instance_count": sum(ratio > 1.0 for ratio in ratios),
            "equal_instance_count": sum(ratio == 1.0 for ratio in ratios),
            "correctness_gate": bool(
                scale_correctness and paired_design_complete
            ),
            "performance_gate": performance_gate,
            "promotion_gate": bool(
                scale_correctness
                and paired_design_complete
                and performance_gate
            ),
            "pairs": pairs,
        }
    formal_design_complete = bool(
        tuple(scales) == FORMAL_SCALES
        and schedule_complete
        and all(row["formal_design_complete"] for row in by_scale.values())
        and all(
            (
                len([slot for slot in schedule if int(slot["scale"]) == scale])
                == EXPECTED_INSTANCE_COUNT
                * (
                    SMALL_SCALE_REPEATS
                    if scale in {5, 10}
                    else LARGE_SCALE_REPEATS
                )
                * 2
            )
            for scale in FORMAL_SCALES
        )
    )
    all_promoted = bool(
        not dry_run
        and not benchmark_only
        and formal_design_complete
        and by_scale
        and all(row["promotion_gate"] for row in by_scale.values())
    )
    paired_design_complete = bool(
        tuple(scales) == FORMAL_SCALES
        and schedule_complete
        and all(row["paired_design_complete"] for row in by_scale.values())
    )
    benchmark_complete = bool(
        benchmark_only
        and not dry_run
        and paired_design_complete
        and all(row["correctness_gate"] for row in by_scale.values())
    )
    status = (
        "DRY_RUN"
        if dry_run
        else "BENCHMARK_COMPLETE"
        if benchmark_complete
        else "BENCHMARK_INCOMPLETE"
        if benchmark_only
        else "PROMOTED"
        if all_promoted
        else "NOT_PROMOTED"
        if formal_design_complete
        else "FORMAL_INCOMPLETE"
    )
    return {
        "status": status,
        "expected_slot_count": len(schedule),
        "completed_slot_count": len(rows),
        "schedule_complete": schedule_complete,
        "paired_design_complete": paired_design_complete,
        "formal_design_complete": formal_design_complete,
        "scale_summary": by_scale,
        "all_scales_promoted": all_promoted,
        "benchmark_complete": benchmark_complete,
        "default_switch_allowed": all_promoted,
    }


def geometric_mean(values: list[float]) -> float | None:
    if not values or any(value <= 0.0 for value in values):
        return None
    return exp(statistics.mean(log(value) for value in values))


def bootstrap_geometric_mean_ci(
    values: list[float], *, samples: int, seed: int
) -> tuple[float | None, float | None]:
    if not values:
        return None, None
    generator = random.Random(seed)
    boot = sorted(
        geometric_mean([generator.choice(values) for _ in values])
        for _sample_index in range(samples)
    )
    lower_index = max(0, int(0.025 * (len(boot) - 1)))
    upper_index = min(len(boot) - 1, int(0.975 * (len(boot) - 1)))
    return boot[lower_index], boot[upper_index]


def run_monitored(
    command: list[str],
    *,
    cwd: Path,
    run_dir: Path,
    slot_id: str,
    heartbeat_csv: Path,
    heartbeat_interval_sec: float,
    timeout_sec: float,
    effective_memory_limit_gb: float,
    min_available_memory_gb: float,
    low_memory_consecutive_samples: int,
) -> dict:
    stdout_path = run_dir / "promotion_stdout.log"
    stderr_path = run_dir / "promotion_stderr.log"
    started = monotonic()
    peak_tree_rss_gb = 0.0
    minimum_available_gb: float | None = None
    low_memory_samples = 0
    termination_reason = ""
    with stdout_path.open("w", encoding="utf-8") as stdout_handle, stderr_path.open(
        "w", encoding="utf-8"
    ) as stderr_handle:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            text=True,
            stdout=stdout_handle,
            stderr=stderr_handle,
            start_new_session=True,
        )
        while True:
            sample = resource_sample(process.pid)
            elapsed = monotonic() - started
            sample.update(
                {
                    "timestamp_utc": utc_now(),
                    "slot_id": slot_id,
                    "root_pid": process.pid,
                    "elapsed_sec": round(elapsed, 6),
                    "effective_memory_limit_gb": effective_memory_limit_gb,
                }
            )
            append_heartbeat(heartbeat_csv, sample)
            peak_tree_rss_gb = max(peak_tree_rss_gb, float(sample["tree_rss_gb"]))
            available_gb = float(sample["available_memory_gb"])
            minimum_available_gb = (
                available_gb
                if minimum_available_gb is None
                else min(minimum_available_gb, available_gb)
            )
            low_memory_samples = (
                low_memory_samples + 1
                if available_gb < min_available_memory_gb
                else 0
            )
            if float(sample["tree_rss_gb"]) > effective_memory_limit_gb:
                termination_reason = "TREE_RSS_EXCEEDED_EFFECTIVE_LIMIT"
            elif low_memory_samples >= low_memory_consecutive_samples:
                termination_reason = "AVAILABLE_MEMORY_SUSTAINED_BELOW_LIMIT"
            elif elapsed > timeout_sec:
                termination_reason = "LAUNCHER_TIMEOUT"
            if termination_reason:
                terminate_process_group(process)
                break
            try:
                returncode = process.wait(timeout=heartbeat_interval_sec)
                break
            except subprocess.TimeoutExpired:
                continue
        if process.poll() is None:
            terminate_process_group(process)
        returncode = int(process.wait())
    return {
        "returncode": returncode,
        "launcher_termination_reason": termination_reason,
        "peak_process_tree_rss_gb": round(peak_tree_rss_gb, 6),
        "minimum_available_memory_gb": (
            None if minimum_available_gb is None else round(minimum_available_gb, 6)
        ),
        "resource_heartbeat_path": str(heartbeat_csv),
    }


def resource_sample(root_pid: int) -> dict:
    pids = process_tree_pids(root_pid)
    rss_kib = 0
    swap_kib = 0
    for pid in pids:
        status = proc_status(pid)
        rss_kib += int(status.get("VmRSS", 0))
        swap_kib += int(status.get("VmSwap", 0))
    memory = meminfo()
    disk = shutil.disk_usage(ROOT)
    return {
        "process_count": len(pids),
        "tree_rss_gb": rss_kib * 1024 / GIB,
        "tree_swap_gb": swap_kib * 1024 / GIB,
        "available_memory_gb": memory.get("MemAvailable", 0) * 1024 / GIB,
        "system_swap_used_gb": (
            memory.get("SwapTotal", 0) - memory.get("SwapFree", 0)
        )
        * 1024
        / GIB,
        "disk_free_gb": disk.free / GIB,
    }


def process_tree_pids(root_pid: int) -> tuple[int, ...]:
    parent_map: dict[int, list[int]] = {}
    for path in Path("/proc").glob("[0-9]*/status"):
        try:
            pid = int(path.parent.name)
            status = proc_status(pid)
            ppid = int(status.get("PPid", -1))
        except (OSError, ValueError):
            continue
        parent_map.setdefault(ppid, []).append(pid)
    result = []
    pending = [int(root_pid)]
    while pending:
        pid = pending.pop()
        if pid in result:
            continue
        result.append(pid)
        pending.extend(parent_map.get(pid, []))
    return tuple(result)


def proc_status(pid: int) -> dict[str, int | str]:
    result: dict[str, int | str] = {}
    try:
        text = Path(f"/proc/{pid}/status").read_text(encoding="utf-8")
    except OSError:
        return result
    for line in text.splitlines():
        key, separator, raw = line.partition(":")
        if not separator:
            continue
        value = raw.strip()
        if key in {"VmRSS", "VmSwap"}:
            try:
                result[key] = int(value.split()[0])
            except (IndexError, ValueError):
                result[key] = 0
        elif key == "PPid":
            try:
                result[key] = int(value)
            except ValueError:
                result[key] = -1
    return result


def meminfo() -> dict[str, int]:
    result = {}
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        key, separator, raw = line.partition(":")
        if separator:
            try:
                result[key] = int(raw.strip().split()[0])
            except (IndexError, ValueError):
                continue
    return result


def append_heartbeat(path: Path, row: Mapping) -> None:
    fieldnames = [
        "timestamp_utc",
        "slot_id",
        "root_pid",
        "elapsed_sec",
        "process_count",
        "tree_rss_gb",
        "tree_swap_gb",
        "effective_memory_limit_gb",
        "available_memory_gb",
        "system_swap_used_gb",
        "disk_free_gb",
    ]
    exists = path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow({key: row.get(key) for key in fieldnames})
        handle.flush()


def terminate_process_group(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=10.0)
        return
    except (ProcessLookupError, subprocess.TimeoutExpired):
        pass
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def effective_memory_limit_gb(config_limit_gb: float) -> float:
    available = meminfo().get("MemAvailable", 0) * 1024 / GIB
    cgroup_limit = cgroup_memory_limit_gb()
    candidates = [float(config_limit_gb), float(available)]
    if cgroup_limit is not None:
        candidates.append(cgroup_limit)
    return max(0.0, min(candidates))


def cgroup_memory_limit_gb() -> float | None:
    candidates = [
        Path("/sys/fs/cgroup/memory.max"),
        Path("/sys/fs/cgroup/memory/memory.limit_in_bytes"),
    ]
    for path in candidates:
        try:
            raw = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if raw == "max":
            continue
        try:
            value = int(raw)
        except ValueError:
            continue
        if value > 0 and value < 1 << 60:
            return value / GIB
    return None


def next_attempt_dir(slot_dir: Path) -> tuple[Path, int]:
    absolute = slot_dir if slot_dir.is_absolute() else ROOT / slot_dir
    for attempt in range(1, 10_000):
        candidate = absolute / f"attempt_{attempt:02d}"
        if not candidate.exists():
            return candidate, attempt
    raise RuntimeError(f"too many attempts under {absolute}")


def index_completed_rows(rows: list[dict], schedule: list[dict]) -> dict[str, dict]:
    expected = {str(row["slot_id"]): row for row in schedule}
    indexed: dict[str, dict] = {}
    for row in rows:
        slot_id = str(row.get("slot_id") or "")
        if slot_id not in expected:
            raise ValueError(f"unexpected recovered slot {slot_id!r}")
        if slot_id in indexed:
            raise ValueError(f"duplicate recovered slot {slot_id!r}")
        for key in (
            "scale",
            "instance_sha256",
            "repetition",
            "order",
            "order_index",
            "mode",
            "config_sha256",
        ):
            if row.get(key) != expected[slot_id].get(key):
                raise ValueError(f"recovered slot binding mismatch {slot_id}:{key}")
        indexed[slot_id] = row
    return indexed


def config_profile(config_path: Path, scale: int) -> dict:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    profiles = config.get("profiles") or {}
    profile = profiles.get(str(scale), profiles.get(scale))
    if not isinstance(profile, dict):
        raise KeyError(f"scale {scale} profile missing from {config_path}")
    return profile


def instance_key_from_path(path: Path) -> str:
    suffix = "_logical_graph"
    stem = path.stem
    return stem[: -len(suffix)] if stem.endswith(suffix) else stem


def write_rows(json_path: Path, csv_path: Path, rows: list[dict]) -> None:
    atomic_write_json(json_path, rows)
    fieldnames = [
        "slot_id",
        "scale",
        "instance_key",
        "repetition",
        "order",
        "order_index",
        "mode",
        "status",
        "returncode",
        "cold_start_total_sec",
        "exact",
        "redlines_zero",
        "engine_hash_valid",
        "engine_build_hash",
        "objective",
        "certificate_scope",
        "live_sri_policy_name",
        "live_cut_policy_hash",
        "max_active_cut_count",
        "launcher_termination_reason",
        "peak_process_tree_rss_gb",
        "minimum_available_memory_gb",
        "run_dir",
    ]
    temporary = csv_path.with_suffix(csv_path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})
    os.replace(temporary, csv_path)


def render_report(summary: Mapping) -> str:
    lines = [
        "# Native Live SRI V1 Frozen Paired Promotion",
        "",
        f"总状态：`{summary.get('status')}`；允许切换默认主线：`{summary.get('default_switch_allowed')}`。",
        "",
        f"正式设计完整：`{summary.get('formal_design_complete')}`；完成 slot：{summary.get('completed_slot_count')}/{summary.get('expected_slot_count')}。",
        "",
    ]
    if summary.get("stopped_reason"):
        lines.extend([f"停止原因：`{summary.get('stopped_reason')}`。", ""])
    for scale, row in summary.get("scale_summary", {}).items():
        lines.extend(
            [
                f"## {scale} 规模",
                "",
                f"- base/live p50：{row['base_p50_sec']} / {row['live_p50_sec']} 秒；比值={row['live_base_p50_ratio']}。",
                f"- base/live mean：{row['base_mean_sec']} / {row['live_mean_sec']} 秒；比值={row['live_base_mean_ratio']}。",
                f"- paired point/geometric mean：{row['paired_ratio_point_estimate']}，95% CI={row['paired_bootstrap_95_ci_geometric_mean']}。",
                f"- 改善/退化/相同实例：{row['improved_instance_count']} / {row['degraded_instance_count']} / {row['equal_instance_count']}。",
                f"- correctness/performance/promotion：{row['correctness_gate']} / {row['performance_gate']} / {row['promotion_gate']}。",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_payload_hash(payload: object) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def atomic_write_json(path: Path, payload: object) -> None:
    atomic_write_text(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())

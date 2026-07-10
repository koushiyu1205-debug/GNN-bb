#!/usr/bin/env python3
"""Official B4.2 cold-start exact runner.

This runner is intentionally stricter than the B4.1 proof-tail scripts:

* each row starts from an instance JSON;
* there is no CLI entry for external source probes or mature pools;
* same-run staged checkpoints may be resumed, but their stage times are counted
  in cold_start_total_sec;
* every row records a stable config hash and explicit column provenance.
"""

from __future__ import annotations

import argparse
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import csv
import hashlib
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

MODEL_ID = "B4_2_COLD_EXACT_V1"
OUTPUT_DIR = "runs/b4_2_cold_exact_500s_full"
ROW_LIMIT_SEC = 500.0
ACCEPTANCE_LIMIT_SEC = 500.0
THREADS = 4
PROFILE = "V4SH"
SEED_MODE = "b0_incumbent_plus_singletons"
COLUMN_PROVENANCE = "instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback"


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    output_dir = _resolve(args.output_dir)
    if not args.resume and _has_checkpoint(output_dir):
        parser.error(
            "--no-resume requires a fresh output directory; refusing to risk "
            "same-instance historical checkpoint reuse"
        )
    output_dir.mkdir(parents=True, exist_ok=True)

    config = _official_config(args)
    config_hash = _config_hash(config)
    instances = _instance_paths(args)
    expected_scale_counts = _scale_counts(instances)
    rows_path = output_dir / "b4_2_cold_exact_rows.csv"
    state_path = output_dir / "b4_2_cold_exact_state.json"
    summary_path = output_dir / "b4_2_cold_exact_summary.json"
    report_path = output_dir / "b4_2_cold_exact_full_report_zh.md"

    state = _load_state(state_path) if args.resume else {}
    rows = _dedupe_rows(list(state.get("rows") or []))
    completed_keys = {
        str(row.get("instance_key") or "")
        for row in rows
        if bool(row.get("row_terminal"))
    }
    limited_run = bool(args.limit or args.instance)

    for index, instance_path in enumerate(instances, start=1):
        instance_key = _instance_key(instance_path)
        if args.resume and instance_key in completed_keys:
            continue
        if not _resource_ok(
            output_dir=output_dir,
            min_available_mem_gb=float(args.min_available_mem_gb),
            min_free_disk_gb=float(args.min_free_disk_gb),
            max_output_dir_gb=float(args.max_output_dir_gb),
        ):
            row = _base_row(
                args,
                config_hash=config_hash,
                instance_index=index,
                instance_path=instance_path,
                status="RESOURCE_GUARD_STOPPED",
                note="resource guard stopped before row start",
            )
            rows = _upsert_row(rows, row)
            _write_artifacts(
                rows,
                config=config,
                limited_run=limited_run,
                discovered_instance_count=len(instances),
                expected_scale_counts=expected_scale_counts,
                rows_path=rows_path,
                state_path=state_path,
                summary_path=summary_path,
                report_path=report_path,
            )
            return 2

        row = _run_instance_cold(args, config_hash=config_hash, instance_index=index, instance_path=instance_path)
        rows = _upsert_row(rows, row)
        _write_artifacts(
            rows,
            config=config,
            limited_run=limited_run,
            discovered_instance_count=len(instances),
            expected_scale_counts=expected_scale_counts,
            rows_path=rows_path,
            state_path=state_path,
            summary_path=summary_path,
            report_path=report_path,
        )

    _write_artifacts(
        rows,
        config=config,
        limited_run=limited_run,
        discovered_instance_count=len(instances),
        expected_scale_counts=expected_scale_counts,
        rows_path=rows_path,
        state_path=state_path,
        summary_path=summary_path,
        report_path=report_path,
    )
    print(
        json.dumps(
            _summary(
                rows,
                config=config,
                limited_run=limited_run,
                discovered_instance_count=len(instances),
                expected_scale_counts=expected_scale_counts,
            ),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    print(f"report {report_path}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the no-cheat B4.2 cold-start benchmark. External mature "
            "probes are deliberately unsupported."
        )
    )
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    parser.add_argument("--scales", nargs="+", type=int, default=[30])
    parser.add_argument("--instance", action="append", default=[])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--model-id", default=MODEL_ID)
    parser.add_argument("--row-limit-sec", type=float, default=ROW_LIMIT_SEC)
    parser.add_argument("--threads", type=int, default=THREADS)
    parser.add_argument("--profile", choices=("V4S", "V4SZ", "V4SH", "V4"), default=PROFILE)
    parser.add_argument("--seed-mode", choices=("b0_incumbent_plus_singletons", "b0_incumbent"), default=SEED_MODE)
    parser.add_argument("--pool-stage-time-slice-sec", type=float, default=150.0)
    parser.add_argument("--pool-min-stage-sec", type=float, default=60.0)
    parser.add_argument("--pool-max-stages", type=int, default=10)
    parser.add_argument("--pool-max-rounds-per-stage", type=int, default=4)
    parser.add_argument("--pool-batch-target", type=int, default=32)
    parser.add_argument("--pool-negative-search-cap-sec", type=float, default=90.0)
    parser.add_argument("--pool-optimization-harvest-target", type=int, default=16)
    parser.add_argument(
        "--pool-optimization-harvest-no-good-scope",
        choices=("arc", "task_set", "arc_and_task_set"),
        default="task_set",
    )
    parser.add_argument(
        "--pool-phase-mode",
        choices=("harvest_then_proof", "proof_only", "feasibility_proof_only"),
        default="harvest_then_proof",
    )
    parser.add_argument("--root-partition-proof", dest="root_partition_proof", action="store_true", default=True)
    parser.add_argument("--no-root-partition-proof", dest="root_partition_proof", action="store_false")
    parser.add_argument("--partition-time-reserve-sec", type=float, default=220.0)
    parser.add_argument("--partition-region-time-limit-sec", type=float, default=20.0)
    parser.add_argument("--partition-worker-count", type=int, default=4)
    parser.add_argument("--partition-k-chunk-size", type=int, default=1)
    parser.add_argument(
        "--partition-variant",
        choices=("V4_current_strengthening", "V4_current_pair_conflict_capacity_bound"),
        default="V4_current_pair_conflict_capacity_bound",
    )
    parser.add_argument("--partition-refresh-rmp-max-iterations", type=int, default=200)
    parser.add_argument("--partition-feedback-rounds", type=int, default=1)
    parser.add_argument("--partition-feedback-harvest-sec", type=float, default=45.0)
    parser.add_argument("--partition-feedback-stage-time-sec", type=float, default=45.0)
    parser.add_argument("--partition-feedback-merge-limit", type=int, default=16)
    parser.add_argument("--partition-feedback-min-final-proof-sec", type=float, default=120.0)
    parser.add_argument("--tree-closure-max-rounds", type=int, default=16)
    parser.add_argument("--tree-closure-max-columns-per-round", type=int, default=128)
    parser.add_argument("--tree-closure-max-nodes", type=int, default=31)
    parser.add_argument("--tree-closure-max-branch-depth", type=int, default=4)
    parser.add_argument("--route-template-pre-harvest-target", type=int, default=32)
    parser.add_argument("--route-template-pre-harvest-time-cap-sec", type=float, default=20.0)
    parser.add_argument("--route-template-pre-harvest-max-direct-tasks", type=int, default=12)
    parser.add_argument("--route-template-pre-harvest-max-active-seeds", type=int, default=240)
    parser.add_argument("--route-template-pre-harvest-max-neighborhood-seeds", type=int, default=480)
    parser.add_argument("--route-template-pre-harvest-max-candidate-sets", type=int, default=1200)
    parser.add_argument("--min-available-mem-gb", type=float, default=4.0)
    parser.add_argument("--min-free-disk-gb", type=float, default=20.0)
    parser.add_argument("--max-output-dir-gb", type=float, default=80.0)
    parser.add_argument("--resume", dest="resume", action="store_true", default=True)
    parser.add_argument("--no-resume", dest="resume", action="store_false")
    return parser


def _official_config(args: argparse.Namespace) -> dict:
    return {
        "schema_version": "lunar_ice_bpc.b4_2_cold_exact_config.v1",
        "model_id": str(args.model_id),
        "official_objective": "normalized_cost + normalized_risk + 0.4 * normalized_weighted_completion",
        "makespan_scope": "metric_only",
        "no_cheat_policy": {
            "starts_from_instance_json": True,
            "external_source_probe_allowed": False,
            "external_mature_pool_allowed": False,
            "manual_columns_allowed": False,
            "per_instance_override_allowed": False,
            "same_run_checkpoint_resume_allowed": True,
            "checkpoint_time_counted": True,
        },
        "threads": int(args.threads),
        "profile": str(args.profile),
        "seed_mode": str(args.seed_mode),
        "column_provenance": COLUMN_PROVENANCE,
        "row_limit_sec": float(args.row_limit_sec),
        "acceptance_limit_sec": float(ACCEPTANCE_LIMIT_SEC),
        "pool_stage_time_slice_sec": float(args.pool_stage_time_slice_sec),
        "pool_min_stage_sec": float(args.pool_min_stage_sec),
        "pool_max_stages": int(args.pool_max_stages),
        "pool_max_rounds_per_stage": int(args.pool_max_rounds_per_stage),
        "pool_batch_target": int(args.pool_batch_target),
        "pool_negative_search_cap_sec": float(args.pool_negative_search_cap_sec),
        "pool_optimization_harvest_target": int(args.pool_optimization_harvest_target),
        "pool_optimization_harvest_no_good_scope": str(args.pool_optimization_harvest_no_good_scope),
        "pool_phase_mode": str(args.pool_phase_mode),
        "root_partition_proof": bool(args.root_partition_proof),
        "partition_time_reserve_sec": float(args.partition_time_reserve_sec),
        "partition_region_time_limit_sec": float(args.partition_region_time_limit_sec),
        "partition_worker_count": int(args.partition_worker_count),
        "partition_k_chunk_size": int(args.partition_k_chunk_size),
        "partition_variant": str(args.partition_variant),
        "partition_refresh_dual_from_active_pool": True,
        "partition_refresh_rmp_max_iterations": int(args.partition_refresh_rmp_max_iterations),
        "partition_feedback_rounds": int(args.partition_feedback_rounds),
        "partition_feedback_harvest_sec": float(args.partition_feedback_harvest_sec),
        "partition_feedback_stage_time_sec": float(args.partition_feedback_stage_time_sec),
        "partition_feedback_merge_limit": int(args.partition_feedback_merge_limit),
        "partition_feedback_min_final_proof_sec": float(args.partition_feedback_min_final_proof_sec),
        "tree_closure_max_rounds": int(args.tree_closure_max_rounds),
        "tree_closure_max_columns_per_round": int(args.tree_closure_max_columns_per_round),
        "tree_closure_max_nodes": int(args.tree_closure_max_nodes),
        "tree_closure_max_branch_depth": int(args.tree_closure_max_branch_depth),
        "route_template_pre_harvest_target": int(args.route_template_pre_harvest_target),
        "route_template_pre_harvest_time_cap_sec": float(args.route_template_pre_harvest_time_cap_sec),
        "route_template_pre_harvest_max_direct_tasks": int(args.route_template_pre_harvest_max_direct_tasks),
        "route_template_pre_harvest_max_active_seeds": int(args.route_template_pre_harvest_max_active_seeds),
        "route_template_pre_harvest_max_neighborhood_seeds": int(
            args.route_template_pre_harvest_max_neighborhood_seeds
        ),
        "route_template_pre_harvest_max_candidate_sets": int(args.route_template_pre_harvest_max_candidate_sets),
        "root_tree_pricing_oracle": "compact_final_judge_profile_shared",
        "live_master_cuts": False,
        "partition_ledger_official": bool(args.root_partition_proof),
    }


def _config_hash(config: dict) -> str:
    payload = json.dumps(config, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _instance_paths(args: argparse.Namespace) -> list[Path]:
    if args.instance:
        paths = [_resolve(path) for path in args.instance]
    else:
        paths: list[Path] = []
        for scale in args.scales:
            paths.extend(
                sorted(
                    (ROOT / "data" / "instances" / f"lunar_ice_sp50_{int(scale):03d}").glob(
                        "instance_*_logical_graph.json"
                    )
                )
            )
    limit = max(0, int(args.limit))
    return paths[:limit] if limit else paths


def _scale_counts(paths: list[Path]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in paths:
        scale = len(_load_task_ids(path))
        key = str(scale)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _run_instance_cold(
    args: argparse.Namespace,
    *,
    config_hash: str,
    instance_index: int,
    instance_path: Path,
) -> dict:
    started = perf_counter()
    row = _base_row(
        args,
        config_hash=config_hash,
        instance_index=instance_index,
        instance_path=instance_path,
        status="B4_2_ROW_STARTED",
    )
    scale = len(_load_task_ids(instance_path))
    pool_dir = _resolve(args.output_dir) / "pools" / f"scale_{scale:03d}" / _instance_key(instance_path)
    proof_dir = _resolve(args.output_dir) / "proofs" / f"scale_{scale:03d}" / _instance_key(instance_path)
    pool_dir.mkdir(parents=True, exist_ok=True)
    proof_dir.mkdir(parents=True, exist_ok=True)

    pool_started = perf_counter()
    stage_error = ""
    for _ in range(max(0, int(args.pool_max_stages))):
        manifest = _pool_manifest(pool_dir)
        latest = _latest_stage(manifest)
        if str(latest.get("certificate_scope") or "") == "BPC_NODE_LP_CERTIFIED":
            break
        remaining = float(args.row_limit_sec) - (perf_counter() - started)
        if remaining <= 1.0:
            stage_error = "row time limit reached before root pool certificate"
            break
        latest_probe_for_partition = _latest_pool_probe(pool_dir)
        if (
            bool(args.root_partition_proof)
            and latest_probe_for_partition is not None
            and remaining <= max(1.0, float(args.partition_time_reserve_sec))
        ):
            stage_error = "reserved remaining budget for official root partition proof"
            break
        if not _resource_ok(
            output_dir=_resolve(args.output_dir),
            min_available_mem_gb=float(args.min_available_mem_gb),
            min_free_disk_gb=float(args.min_free_disk_gb),
            max_output_dir_gb=float(args.max_output_dir_gb),
        ):
            stage_error = "resource guard stopped during root pool build"
            break
        partition_reserve = (
            max(0.0, float(args.partition_time_reserve_sec))
            if bool(args.root_partition_proof) and latest_probe_for_partition is not None
            else 0.0
        )
        stage_budget = max(1.0, remaining - partition_reserve) if partition_reserve > 0.0 else remaining
        if (
            bool(args.root_partition_proof)
            and latest_probe_for_partition is not None
            and stage_budget < max(1.0, float(args.pool_min_stage_sec))
        ):
            stage_error = "reserved remaining budget for partition feedback/proof instead of starting a short pool stage"
            break
        slice_sec = max(1.0, min(float(args.pool_stage_time_slice_sec), stage_budget))
        completed = _run_stage(args, instance_path=instance_path, pool_dir=pool_dir, time_limit_sec=slice_sec)
        if completed.returncode != 0:
            stage_error = (completed.stderr[-1200:] or completed.stdout[-1200:] or "staged resume failed")
            break

    pool_wall = perf_counter() - pool_started
    manifest = _pool_manifest(pool_dir)
    stages = list(manifest.get("stages") or [])
    latest_stage = _latest_stage(manifest)
    latest_probe = _latest_pool_probe(pool_dir)
    pool_certified = str(latest_stage.get("certificate_scope") or "") == "BPC_NODE_LP_CERTIFIED" and latest_probe is not None
    root_cg_sec = _sum_float(stages, "elapsed_sec")
    row.update(
        {
            "seed_sec": 0.0,
            "seed_sec_instrumented": False,
            "root_cg_sec": root_cg_sec,
            "root_partition_feedback_sec": 0.0,
            "root_partition_feedback_round_count": 0,
            "root_partition_feedback_added_column_count": 0,
            "root_pool_wall_sec": round(pool_wall, 6),
            "root_pool_stage_count": len(stages),
            "root_pool_certified": bool(pool_certified),
            "root_pool_algorithm_status": latest_stage.get("algorithm_status") or "",
            "root_pool_certificate_scope": latest_stage.get("certificate_scope") or "",
            "root_pool_pricing_state": latest_stage.get("pricing_state") or "",
            "root_pool_active_column_count": latest_stage.get("active_column_count"),
            "root_pool_latest_probe_json": str(latest_probe or ""),
            "source_probe_json": str(latest_probe or ""),
        }
    )
    if bool(args.root_partition_proof) and latest_probe is not None and not pool_certified:
        feedback_row = _run_partition_feedback_rounds(
            args,
            instance_path=instance_path,
            pool_dir=pool_dir,
            proof_dir=proof_dir,
            latest_probe=latest_probe,
            started=started,
        )
        row.update(feedback_row)
        manifest = _pool_manifest(pool_dir)
        stages = list(manifest.get("stages") or [])
        latest_stage = _latest_stage(manifest)
        latest_probe = _latest_pool_probe(pool_dir)
        pool_certified = (
            str(latest_stage.get("certificate_scope") or "") == "BPC_NODE_LP_CERTIFIED"
            and latest_probe is not None
        )
        root_cg_sec = _sum_float(stages, "elapsed_sec")
        row.update(
            {
                "root_cg_sec": root_cg_sec,
                "root_pool_stage_count": len(stages),
                "root_pool_certified": bool(pool_certified),
                "root_pool_algorithm_status": latest_stage.get("algorithm_status") or "",
                "root_pool_certificate_scope": latest_stage.get("certificate_scope") or "",
                "root_pool_pricing_state": latest_stage.get("pricing_state") or "",
                "root_pool_active_column_count": latest_stage.get("active_column_count"),
                "root_pool_latest_probe_json": str(latest_probe or ""),
                "source_probe_json": str(latest_probe or ""),
            }
        )
    partition_row = {}
    if bool(args.root_partition_proof) and latest_probe is not None and not pool_certified:
        remaining_for_partition = float(args.row_limit_sec) - (perf_counter() - started)
        if remaining_for_partition > 1.0:
            partition_row = _run_root_partition_proof(
                args,
                source_probe=latest_probe,
                output_dir=proof_dir / "root_partition_proof",
                time_limit_sec=remaining_for_partition,
            )
            row.update(partition_row)
            if bool(partition_row.get("root_partition_certified_no_negative")):
                pool_certified = True
                row["root_pool_certified"] = True
                row["root_pool_certificate_scope"] = "BPC_NODE_LP_CERTIFIED"
                row["root_pool_pricing_state"] = "CERTIFIED_NO_NEGATIVE"
                row["root_pool_algorithm_status"] = "BPC_GAP_AVAILABLE"
                row["pricing_state"] = "CERTIFIED_NO_NEGATIVE"
                row["certificate_scope"] = "BPC_NODE_LP_CERTIFIED"
        elif not pool_certified:
            row.update(
                {
                    "root_partition_proof_enabled": True,
                    "root_partition_certified_no_negative": False,
                    "root_partition_fail_reason": "row time limit reached before root partition proof",
                }
            )
    if not pool_certified:
        row.update(
            {
                "algorithm_status": "BPC_INCOMPLETE_PRICING",
                "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                "pricing_state": latest_stage.get("pricing_state") or "",
                "exact_certificate": False,
                "bpc_tree_optimal": False,
                "under_300": False,
                "under_acceptance_limit": False,
                "under_500": False,
                "row_terminal": True,
                "fail_reason": (
                    row.get("root_partition_fail_reason")
                    or stage_error
                    or "root pool did not certify no-negative within cold-start row limit"
                ),
            }
        )
        return _finish_timing(row, started)

    if bool(partition_row.get("root_partition_certified_no_negative")):
        root_gate = _root_partition_tree_gate(latest_probe, partition_row)
        row.update(root_gate)
        if bool(root_gate.get("exact_certificate")):
            row["tree_sec"] = 0.0
            row["pricing_proof_sec"] = row.get("root_partition_sec")
            row["row_terminal"] = True
            return _finish_timing(row, started)

    remaining_for_tree = float(args.row_limit_sec) - (perf_counter() - started)
    if remaining_for_tree <= 1.0:
        row.update(
            {
                "algorithm_status": "BPC_INCOMPLETE_PRICING",
                "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                "pricing_state": "INCOMPLETE_LIMIT",
                "exact_certificate": False,
                "bpc_tree_optimal": False,
                "under_300": False,
                "under_acceptance_limit": False,
                "under_500": False,
                "row_terminal": True,
                "fail_reason": "row time limit reached before tree closure",
            }
        )
        return _finish_timing(row, started)

    tree_row = _run_tree_closure(
        args,
        instance_index=instance_index,
        instance_path=instance_path,
        source_probe=latest_probe,
        output_dir=proof_dir,
        time_limit_sec=remaining_for_tree,
    )
    row.update(tree_row)
    row["tree_sec"] = tree_row.get("tree_sec")
    row["pricing_proof_sec"] = tree_row.get("pricing_proof_sec")
    row["row_terminal"] = True
    return _finish_timing(row, started)


def _run_partition_feedback_rounds(
    args: argparse.Namespace,
    *,
    instance_path: Path,
    pool_dir: Path,
    proof_dir: Path,
    latest_probe: Path,
    started: float,
) -> dict:
    rounds = max(0, int(args.partition_feedback_rounds))
    if rounds <= 0:
        return {}
    feedback_dir = proof_dir / "root_partition_feedback"
    feedback_dir.mkdir(parents=True, exist_ok=True)
    total_sec = 0.0
    added_total = 0
    selected_total = 0
    rejected_total = 0
    completed_rounds = 0
    stop_reason = ""
    current_probe = latest_probe
    last_merge: dict = {}
    last_harvest: dict = {}
    for round_index in range(1, rounds + 1):
        remaining = float(args.row_limit_sec) - (perf_counter() - started)
        min_final = max(0.0, float(args.partition_feedback_min_final_proof_sec))
        if remaining <= min_final + 2.0:
            stop_reason = "insufficient time before final proof reserve"
            break
        harvest_limit = min(float(args.partition_feedback_harvest_sec), remaining - min_final)
        if harvest_limit <= 1.0:
            stop_reason = "insufficient harvest budget"
            break
        harvest_output = feedback_dir / f"round_{round_index:02d}_partition_harvest"
        harvest = _run_root_partition_proof(
            args,
            source_probe=current_probe,
            output_dir=harvest_output,
            time_limit_sec=harvest_limit,
        )
        last_harvest = dict(harvest)
        total_sec += float(harvest.get("root_partition_sec") or 0.0)
        merge_output = feedback_dir / f"round_{round_index:02d}_merged_probe.json"
        merge = _merge_partition_negative_columns_into_probe(
            source_probe=current_probe,
            partition_dir=harvest_output,
            output_probe=merge_output,
            max_columns=max(0, int(args.partition_feedback_merge_limit)),
            negative_eps=1.0e-6,
            round_index=round_index,
        )
        last_merge = dict(merge)
        selected_total += int(merge.get("selected_count") or 0)
        added_total += int(merge.get("added_count") or 0)
        rejected_total += int(merge.get("rejected_count") or 0)
        if int(merge.get("added_count") or 0) <= 0:
            stop_reason = "partition feedback found no mergeable new columns"
            break
        _set_pool_latest_probe(pool_dir, merge_output, merge)
        current_probe = merge_output
        remaining = float(args.row_limit_sec) - (perf_counter() - started)
        if remaining <= min_final + 2.0:
            stop_reason = "merged feedback columns but no time for feedback stage"
            completed_rounds = round_index
            break
        stage_limit = min(float(args.partition_feedback_stage_time_sec), remaining - min_final)
        if stage_limit <= 1.0:
            stop_reason = "insufficient feedback stage budget"
            completed_rounds = round_index
            break
        completed = _run_stage(
            args,
            instance_path=instance_path,
            pool_dir=pool_dir,
            time_limit_sec=stage_limit,
        )
        if completed.returncode != 0:
            stop_reason = completed.stderr[-800:] or completed.stdout[-800:] or "feedback stage failed"
            completed_rounds = round_index
            break
        completed_rounds = round_index
        current_probe = _latest_pool_probe(pool_dir) or current_probe
        latest = _latest_stage(_pool_manifest(pool_dir))
        if str(latest.get("certificate_scope") or "") == "BPC_NODE_LP_CERTIFIED":
            stop_reason = "feedback stage produced node LP certificate"
            break
    return {
        "root_partition_feedback_enabled": True,
        "root_partition_feedback_sec": round(total_sec, 6),
        "root_partition_feedback_round_count": int(completed_rounds),
        "root_partition_feedback_selected_column_count": int(selected_total),
        "root_partition_feedback_added_column_count": int(added_total),
        "root_partition_feedback_rejected_column_count": int(rejected_total),
        "root_partition_feedback_last_harvest_dir": str(last_harvest.get("root_partition_audit_json") or ""),
        "root_partition_feedback_last_merge_probe": str(last_merge.get("output_probe") or ""),
        "root_partition_feedback_stop_reason": stop_reason,
    }


def _run_stage(
    args: argparse.Namespace,
    *,
    instance_path: Path,
    pool_dir: Path,
    time_limit_sec: float,
) -> subprocess.CompletedProcess:
    command = [
        sys.executable,
        str(STAGED_RESUME),
        "--instance",
        str(instance_path),
        "--output-dir",
        str(pool_dir),
        "--stage-count",
        "1",
        "--stage-time-limit-sec",
        str(float(time_limit_sec)),
        "--max-rounds-per-stage",
        str(int(args.pool_max_rounds_per_stage)),
        "--max-direct-tasks",
        str(len(_load_task_ids(instance_path))),
        "--seed-mode",
        str(args.seed_mode),
        "--batch-target",
        str(int(args.pool_batch_target)),
        "--negative-search-cap-sec",
        str(float(args.pool_negative_search_cap_sec)),
        "--compact-optimization-harvest-target",
        str(int(args.pool_optimization_harvest_target)),
        "--compact-optimization-harvest-no-good-scope",
        str(args.pool_optimization_harvest_no_good_scope),
        "--compact-final-judge-profile",
        str(args.profile),
        "--compact-final-judge-phase-mode",
        str(args.pool_phase_mode),
        "--compact-service-start-depot-travel-lb",
        "--compact-task-to-depot-return-travel-lb",
        "--compact-pair-route-duration-lb",
        "--compact-sortie-slot-position-bounds",
        "--compact-pair-energy-infeasible-cut",
        "--compact-triple-time-window-infeasible-cut",
    ]
    env = _solver_env(args)
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=max(10.0, float(time_limit_sec) + 5.0),
    )
    stage_logs = pool_dir / "b4_2_stage_logs"
    stage_logs.mkdir(parents=True, exist_ok=True)
    index = len(list(stage_logs.glob("stage_*_stdout.txt"))) + 1
    (stage_logs / f"stage_{index:03d}_stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (stage_logs / f"stage_{index:03d}_stderr.txt").write_text(completed.stderr, encoding="utf-8")
    return completed


def _run_tree_closure(
    args: argparse.Namespace,
    *,
    instance_index: int,
    instance_path: Path,
    source_probe: Path,
    output_dir: Path,
    time_limit_sec: float,
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
        str(float(time_limit_sec)),
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
    env = _solver_env(args)
    env["LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE"] = "proof_only"
    started = perf_counter()
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=max(10.0, float(time_limit_sec) + 5.0),
    )
    wall = perf_counter() - started
    (output_dir / "b4_2_tree_stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (output_dir / "b4_2_tree_stderr.txt").write_text(completed.stderr, encoding="utf-8")
    result_path = output_dir / "tree_closure_results" / "tree_closure_001.json"
    if completed.returncode != 0 or not result_path.exists():
        return {
            "algorithm_status": "TREE_CLOSURE_FAILED",
            "certificate_scope": "",
            "pricing_state": "",
            "exact_certificate": False,
            "bpc_tree_optimal": False,
            "under_300": False,
            "under_acceptance_limit": False,
            "under_500": False,
            "tree_sec": round(wall, 6),
            "pricing_proof_sec": None,
            "tree_result_json": str(result_path if result_path.exists() else ""),
            "fail_reason": completed.stderr[-1200:] or completed.stdout[-1200:] or "tree closure result missing",
        }
    raw = json.loads(result_path.read_text(encoding="utf-8"))
    root_node = (raw.get("nodes") or [{}])[0]
    final_judge = root_node.get("final_judge") if isinstance(root_node.get("final_judge"), dict) else {}
    algorithm_status = raw.get("algorithm_status") or root_node.get("algorithm_status") or ""
    certificate_scope = raw.get("certificate_scope") or root_node.get("certificate_scope") or ""
    pricing_state = root_node.get("pricing_state") or final_judge.get("pricing_state") or ""
    exact_certificate = (
        str(algorithm_status) == "BPC_OPTIMAL"
        and str(certificate_scope) == "BPC_TREE_OPTIMAL"
        and str(pricing_state) == "CERTIFIED_NO_NEGATIVE"
    )
    return {
        "algorithm_status": algorithm_status,
        "certificate_scope": certificate_scope,
        "pricing_state": pricing_state,
        "exact_certificate": bool(exact_certificate),
        "bpc_tree_optimal": str(certificate_scope) == "BPC_TREE_OPTIMAL",
        "tree_sec": round(wall, 6),
        "pricing_proof_sec": _first_float(
            final_judge.get("wall_time_sec"),
            final_judge.get("final_judge_wall_time"),
            raw.get("wall_time_sec"),
            raw.get("wall_time"),
        ),
        "tree_result_json": str(result_path),
        "tree_loaded_column_count": root_node.get("loaded_column_count"),
        "tree_columns_added": root_node.get("added_column_count"),
        "tree_round_count": root_node.get("round_count"),
        "final_judge_profile": final_judge.get("compact_final_judge_profile"),
        "final_judge_formulation_profile": final_judge.get("compact_final_judge_formulation_profile"),
        "final_judge_threads": final_judge.get("compact_final_judge_threads"),
        "pricing_proof_kind": final_judge.get("pricing_proof_kind"),
        "best_reduced_cost": final_judge.get("best_reduced_cost"),
        "global_remaining_rc_lb": final_judge.get("global_remaining_rc_lb"),
        "manual_rc_fail": 0 if bool(final_judge.get("pricing_rc_audit_pass", True)) else 1,
        "pricing_rc_fail": 0 if bool(final_judge.get("pricing_rc_audit_pass", True)) else 1,
        "certificate_leak": 0,
        "fail_reason": "" if exact_certificate else "tree closure did not produce BPC_TREE_OPTIMAL",
    }


def _run_root_partition_proof(
    args: argparse.Namespace,
    *,
    source_probe: Path,
    output_dir: Path,
    time_limit_sec: float,
) -> dict:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    worker_count = max(1, int(args.partition_worker_count))
    if worker_count > 1:
        return _run_root_partition_proof_parallel(
            args,
            source_probe=source_probe,
            output_dir=output_dir,
            time_limit_sec=float(time_limit_sec),
            worker_count=worker_count,
        )
    command = [
        sys.executable,
        str(B41_RUNNER),
        "--output-dir",
        str(output_dir),
        "--source-probe-json",
        str(source_probe),
        "--required-task-set-partition-proof-probe",
        "--partition-region-variants",
        str(args.partition_variant),
        "--partition-region-time-limit-sec",
        str(float(args.partition_region_time_limit_sec)),
        "--partition-residual-task-count-proof",
        "--partition-residual-active-sortie-count-proof",
        "--partition-negative-feasibility-fallback",
        "--partition-refresh-dual-from-active-pool",
        "--partition-refresh-rmp-max-iterations",
        str(int(args.partition_refresh_rmp_max_iterations)),
        "--partition-candidate-audit",
        "--threads",
        str(int(args.threads)),
        "--min-available-mem-gb",
        str(float(args.min_available_mem_gb)),
        "--min-free-disk-gb",
        str(float(args.min_free_disk_gb)),
        "--max-output-dir-gb",
        "16",
        "--resource-check-action",
        "stop",
        "--no-resume",
    ]
    env = _solver_env(args)
    started = perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=str(ROOT),
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=max(1.0, float(time_limit_sec) + 1.0),
        )
    except subprocess.TimeoutExpired as exc:
        wall = perf_counter() - started
        (output_dir / "b4_2_partition_stdout.txt").write_text(exc.stdout or "", encoding="utf-8")
        (output_dir / "b4_2_partition_stderr.txt").write_text(exc.stderr or "", encoding="utf-8")
        return {
            "root_partition_proof_enabled": True,
            "root_partition_sec": round(wall, 6),
            "root_partition_certified_no_negative": False,
            "root_partition_fail_reason": "partition subprocess timeout",
            "root_partition_stdout": str(output_dir / "b4_2_partition_stdout.txt"),
            "root_partition_stderr": str(output_dir / "b4_2_partition_stderr.txt"),
        }
    wall = perf_counter() - started
    (output_dir / "b4_2_partition_stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (output_dir / "b4_2_partition_stderr.txt").write_text(completed.stderr, encoding="utf-8")
    partition_json = output_dir / "required_task_set_partition_probe.json"
    audit_json = output_dir / "partition_candidate_audit.json"
    base = {
        "root_partition_proof_enabled": True,
        "root_partition_sec": round(wall, 6),
        "root_partition_returncode": int(completed.returncode),
        "root_partition_probe_json": str(partition_json if partition_json.exists() else ""),
        "root_partition_audit_json": str(audit_json if audit_json.exists() else ""),
        "root_partition_certified_no_negative": False,
        "root_partition_stdout": str(output_dir / "b4_2_partition_stdout.txt"),
        "root_partition_stderr": str(output_dir / "b4_2_partition_stderr.txt"),
    }
    if completed.returncode != 0 or not partition_json.exists():
        base["root_partition_fail_reason"] = (
            completed.stderr[-1200:] or completed.stdout[-1200:] or "partition result missing"
        )
        return base
    payload = json.loads(partition_json.read_text(encoding="utf-8"))
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    redlines = payload.get("redlines") if isinstance(payload.get("redlines"), dict) else {}
    issue_codes = [str(code) for code in (summary.get("partition_candidate_gate_issue_codes") or [])]
    redline_sum = sum(_int(value) for value in redlines.values())
    best_partition_lb = _first_float(summary.get("best_partition_region_lb"))
    certified = bool(
        summary.get("partition_candidate_gate_pass") is True
        and summary.get("partition_candidate_can_certify_no_negative") is True
        and summary.get("partition_candidate_gate_full_space_partition_valid") is True
        and _int(summary.get("partition_negative_region_count")) == 0
        and _int(summary.get("residual_task_count_region_incomplete_count")) == 0
        and _int(summary.get("residual_task_count_region_missing_count")) == 0
        and _int(summary.get("residual_active_sortie_count_missing_group_count")) == 0
        and _int(summary.get("partition_negative_rc_audit_fail_count")) == 0
        and _int(summary.get("partition_dual_scope_mismatch_count")) == 0
        and str(summary.get("partition_dual_refresh_status") or "") == "RESTRICTED_RMP_OPTIMAL"
        and redline_sum == 0
        and best_partition_lb is not None
        and float(best_partition_lb) >= -1.0e-6
    )
    base.update(
        {
            "root_partition_certified_no_negative": bool(certified),
            "root_partition_gate_pass": bool(summary.get("partition_candidate_gate_pass")),
            "root_partition_full_space_valid": bool(
                summary.get("partition_candidate_gate_full_space_partition_valid")
            ),
            "root_partition_can_certify_no_negative": bool(
                summary.get("partition_candidate_can_certify_no_negative")
            ),
            "root_partition_issue_codes": issue_codes,
            "root_partition_region_count": _int(payload.get("row_count")),
            "root_partition_best_lb": best_partition_lb,
            "root_partition_bound_gap_to_zero": _first_float(summary.get("partition_bound_gap_to_zero")),
            "root_partition_negative_region_count": _int(summary.get("partition_negative_region_count")),
            "root_partition_incomplete_region_count": _int(
                summary.get("residual_task_count_region_incomplete_count")
            ),
            "root_partition_missing_region_count": _int(
                summary.get("residual_task_count_region_missing_count")
            ),
            "root_partition_dual_refresh_status": summary.get("partition_dual_refresh_status") or "",
            "root_partition_dual_scope_mismatch_count": _int(
                summary.get("partition_dual_scope_mismatch_count")
            ),
            "root_partition_redline_count": redline_sum,
            "root_partition_fail_reason": "" if certified else "partition gate did not satisfy official B4.2 criteria",
        }
    )
    return base


def _run_root_partition_proof_parallel(
    args: argparse.Namespace,
    *,
    source_probe: Path,
    output_dir: Path,
    time_limit_sec: float,
    worker_count: int,
) -> dict:
    task_count = _source_probe_task_count(source_probe)
    if task_count <= 0:
        return {
            "root_partition_proof_enabled": True,
            "root_partition_sec": 0.0,
            "root_partition_certified_no_negative": False,
            "root_partition_fail_reason": "source probe task count unavailable",
        }
    chunks = _partition_k_chunks(
        task_count,
        worker_count,
        k_chunk_size=max(1, int(args.partition_k_chunk_size)),
    )
    started = perf_counter()
    worker_results: list[dict] = []
    deadline = started + max(1.0, float(time_limit_sec))
    chunk_iter = iter(list(enumerate(chunks, start=1)))
    with ThreadPoolExecutor(max_workers=max(1, int(worker_count))) as executor:
        futures = {}

        def submit_available() -> None:
            while len(futures) < max(1, int(worker_count)):
                remaining = deadline - perf_counter()
                if remaining <= 1.0:
                    return
                try:
                    worker_index, (k_min, k_max) = next(chunk_iter)
                except StopIteration:
                    return
                worker_dir = output_dir / f"worker_{worker_index:02d}_k{k_min:03d}_{k_max:03d}"
                worker_dir.mkdir(parents=True, exist_ok=True)
                command = _partition_worker_command(
                    args,
                    source_probe=source_probe,
                    output_dir=worker_dir,
                    k_min=k_min,
                    k_max=k_max,
                    threads=1,
                )
                future = executor.submit(
                    _run_partition_worker,
                    command=command,
                    output_dir=worker_dir,
                    time_limit_sec=remaining,
                    env=_solver_env(args),
                )
                futures[future] = {
                    "worker_index": worker_index,
                    "k_min": k_min,
                    "k_max": k_max,
                    "output_dir": str(worker_dir),
                }

        submit_available()
        while futures:
            timeout = max(0.25, min(1.0, max(0.0, deadline - perf_counter())))
            done, _pending = wait(tuple(futures), timeout=timeout, return_when=FIRST_COMPLETED)
            if not done:
                if perf_counter() >= deadline:
                    break
                continue
            for future in done:
                futures.pop(future, None)
                worker_results.append(future.result())
            submit_available()
        for meta in futures.values():
            worker_results.append(
                {
                    "output_dir": meta["output_dir"],
                    "returncode": None,
                    "wall_time_sec": None,
                    "timeout": True,
                    "partition_json": "",
                    "error": "partition worker global deadline reached",
                    "k_min": int(meta["k_min"]),
                    "k_max": int(meta["k_max"]),
                }
            )
        for worker_index, (k_min, k_max) in chunk_iter:
            worker_dir = output_dir / f"worker_{worker_index:02d}_k{k_min:03d}_{k_max:03d}"
            worker_results.append(
                {
                    "output_dir": str(worker_dir),
                    "returncode": None,
                    "wall_time_sec": 0.0,
                    "timeout": True,
                    "partition_json": "",
                    "error": "partition worker not started before global deadline",
                    "k_min": int(k_min),
                    "k_max": int(k_max),
                }
            )
    wall = perf_counter() - started
    aggregate = _aggregate_partition_workers(
        worker_results,
        task_count=task_count,
        negative_eps=1.0e-6,
    )
    summary_path = output_dir / "parallel_partition_summary.json"
    summary_path.write_text(json.dumps(aggregate, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    certified = bool(aggregate["certified_no_negative"])
    return {
        "root_partition_proof_enabled": True,
        "root_partition_parallel": True,
        "root_partition_worker_count": len(chunks),
        "root_partition_parallel_slots": int(worker_count),
        "root_partition_k_chunk_size": int(args.partition_k_chunk_size),
        "root_partition_sec": round(wall, 6),
        "root_partition_probe_json": "",
        "root_partition_audit_json": str(summary_path),
        "root_partition_certified_no_negative": certified,
        "root_partition_gate_pass": certified,
        "root_partition_full_space_valid": bool(aggregate["coverage_complete"]),
        "root_partition_can_certify_no_negative": certified,
        "root_partition_issue_codes": aggregate["issue_codes"],
        "root_partition_region_count": int(aggregate["region_count"]),
        "root_partition_expected_region_count": int(aggregate["expected_region_count"]),
        "root_partition_best_lb": aggregate["best_lb"],
        "root_partition_bound_gap_to_zero": (
            None if aggregate["best_lb"] is None else round(max(0.0, -float(aggregate["best_lb"])), 9)
        ),
        "root_partition_negative_region_count": int(aggregate["negative_region_count"]),
        "root_partition_incomplete_region_count": int(aggregate["incomplete_region_count"]),
        "root_partition_missing_region_count": int(aggregate["missing_region_count"]),
        "root_partition_duplicate_region_count": int(aggregate["duplicate_region_count"]),
        "root_partition_dual_refresh_status": aggregate["dual_refresh_status"],
        "root_partition_dual_scope_mismatch_count": int(aggregate["dual_scope_mismatch_count"]),
        "root_partition_redline_count": int(aggregate["redline_count"]),
        "root_partition_fail_reason": "" if certified else "parallel partition gate did not satisfy official B4.2 criteria",
    }


def _partition_worker_command(
    args: argparse.Namespace,
    *,
    source_probe: Path,
    output_dir: Path,
    k_min: int,
    k_max: int,
    threads: int,
) -> list[str]:
    return [
        sys.executable,
        str(B41_RUNNER),
        "--output-dir",
        str(output_dir),
        "--source-probe-json",
        str(source_probe),
        "--required-task-set-partition-proof-probe",
        "--partition-region-variants",
        str(args.partition_variant),
        "--partition-region-time-limit-sec",
        str(float(args.partition_region_time_limit_sec)),
        "--partition-residual-task-count-proof",
        "--partition-residual-task-count-min",
        str(int(k_min)),
        "--partition-residual-task-count-max",
        str(int(k_max)),
        "--partition-residual-active-sortie-count-proof",
        "--partition-negative-feasibility-fallback",
        "--partition-refresh-dual-from-active-pool",
        "--partition-refresh-rmp-max-iterations",
        str(int(args.partition_refresh_rmp_max_iterations)),
        "--partition-candidate-audit",
        "--threads",
        str(int(threads)),
        "--min-available-mem-gb",
        str(float(args.min_available_mem_gb)),
        "--min-free-disk-gb",
        str(float(args.min_free_disk_gb)),
        "--max-output-dir-gb",
        "16",
        "--resource-check-action",
        "stop",
        "--no-resume",
    ]


def _run_partition_worker(
    *,
    command: list[str],
    output_dir: Path,
    time_limit_sec: float,
    env: dict[str, str],
) -> dict:
    started = perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=str(ROOT),
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=max(1.0, float(time_limit_sec) + 1.0),
        )
    except subprocess.TimeoutExpired as exc:
        wall = perf_counter() - started
        (output_dir / "stdout.txt").write_text(exc.stdout or "", encoding="utf-8")
        (output_dir / "stderr.txt").write_text(exc.stderr or "", encoding="utf-8")
        return {
            "output_dir": str(output_dir),
            "returncode": None,
            "wall_time_sec": round(wall, 6),
            "timeout": True,
            "partition_json": "",
            "error": "partition worker timeout",
        }
    wall = perf_counter() - started
    (output_dir / "stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (output_dir / "stderr.txt").write_text(completed.stderr, encoding="utf-8")
    partition_json = output_dir / "required_task_set_partition_probe.json"
    return {
        "output_dir": str(output_dir),
        "returncode": int(completed.returncode),
        "wall_time_sec": round(wall, 6),
        "timeout": False,
        "partition_json": str(partition_json if partition_json.exists() else ""),
        "error": "" if completed.returncode == 0 and partition_json.exists() else (
            completed.stderr[-1200:] or completed.stdout[-1200:] or "partition worker result missing"
        ),
    }


def _aggregate_partition_workers(
    worker_results: list[dict],
    *,
    task_count: int,
    negative_eps: float,
) -> dict:
    expected = {(k, m) for k in range(1, int(task_count) + 1) for m in range(1, k + 1)}
    seen: dict[tuple[int, int], dict] = {}
    duplicates = 0
    negative_count = 0
    incomplete_count = 0
    redline_count = 0
    rc_audit_fail_count = 0
    dual_scope_mismatch_count = 0
    best_values: list[float] = []
    issue_codes: list[str] = []
    refresh_statuses: set[str] = set()
    worker_payloads: list[dict] = []
    for worker in worker_results:
        if worker.get("timeout"):
            issue_codes.append("worker_timeout")
            continue
        if int(worker.get("returncode") or 0) != 0:
            issue_codes.append("worker_returncode_nonzero")
            continue
        path_value = worker.get("partition_json") or ""
        if not path_value or not Path(path_value).exists():
            issue_codes.append("worker_partition_json_missing")
            continue
        payload = json.loads(Path(path_value).read_text(encoding="utf-8"))
        worker_payloads.append(payload)
        redlines = payload.get("redlines") if isinstance(payload.get("redlines"), dict) else {}
        redline_count += sum(_int(value) for value in redlines.values())
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        if summary.get("partition_dual_refresh_status"):
            refresh_statuses.add(str(summary.get("partition_dual_refresh_status")))
        dual_scope_mismatch_count += _int(summary.get("partition_dual_scope_mismatch_count"))
        rc_audit_fail_count += _int(summary.get("partition_negative_rc_audit_fail_count"))
        for row in payload.get("rows") or []:
            if not isinstance(row, dict):
                continue
            pair = _partition_region_pair(row.get("region_id"))
            if pair is None:
                issue_codes.append("region_id_unparsed")
                continue
            if pair in seen:
                duplicates += 1
            seen[pair] = row
            best_rc = _first_float(row.get("best_reduced_cost"), row.get("dual_bound"))
            if best_rc is not None:
                best_values.append(float(best_rc))
            negative = bool(row.get("negative_found")) or (
                best_rc is not None and float(best_rc) < -abs(float(negative_eps))
            )
            if negative:
                negative_count += 1
            complete = bool(row.get("region_pricing_complete"))
            can_certify = bool(row.get("region_can_certify_no_negative"))
            if not complete or not can_certify:
                incomplete_count += 1
    missing = sorted(expected.difference(seen))
    unexpected = sorted(set(seen).difference(expected))
    if missing:
        issue_codes.append("missing_regions")
    if unexpected:
        issue_codes.append("unexpected_regions")
    if duplicates:
        issue_codes.append("duplicate_regions")
    if negative_count:
        issue_codes.append("negative_regions")
    if incomplete_count:
        issue_codes.append("incomplete_regions")
    if redline_count:
        issue_codes.append("redline_nonzero")
    if rc_audit_fail_count:
        issue_codes.append("negative_rc_audit_fail")
    if dual_scope_mismatch_count:
        issue_codes.append("dual_scope_mismatch")
    if refresh_statuses != {"RESTRICTED_RMP_OPTIMAL"}:
        issue_codes.append("dual_refresh_not_optimal")
    best_lb = None if not best_values else round(min(best_values), 9)
    if best_lb is None:
        issue_codes.append("best_lb_missing")
    elif best_lb < -abs(float(negative_eps)):
        issue_codes.append("best_lb_negative")
    coverage_complete = bool(not missing and not unexpected and not duplicates and len(seen) == len(expected))
    certified = bool(
        coverage_complete
        and not issue_codes
        and best_lb is not None
        and best_lb >= -abs(float(negative_eps))
    )
    return {
        "schema_version": "lunar_ice_bpc.b4_2.parallel_partition_summary.v1",
        "certified_no_negative": certified,
        "coverage_complete": coverage_complete,
        "task_count": int(task_count),
        "expected_region_count": len(expected),
        "region_count": len(seen),
        "missing_region_count": len(missing),
        "duplicate_region_count": duplicates,
        "unexpected_region_count": len(unexpected),
        "negative_region_count": negative_count,
        "incomplete_region_count": incomplete_count,
        "redline_count": redline_count,
        "negative_rc_audit_fail_count": rc_audit_fail_count,
        "dual_scope_mismatch_count": dual_scope_mismatch_count,
        "dual_refresh_status": ",".join(sorted(refresh_statuses)),
        "best_lb": best_lb,
        "issue_codes": sorted(set(issue_codes)),
        "worker_results": worker_results,
    }


def _merge_partition_negative_columns_into_probe(
    *,
    source_probe: Path,
    partition_dir: Path,
    output_probe: Path,
    max_columns: int,
    negative_eps: float,
    round_index: int,
) -> dict:
    source = json.loads(Path(source_probe).read_text(encoding="utf-8"))
    active_columns = [row for row in (source.get("active_columns") or []) if isinstance(row, dict)]
    existing_keys = {_column_payload_key(row) for row in active_columns}
    candidates = _partition_negative_payload_candidates(
        partition_dir=partition_dir,
        negative_eps=negative_eps,
    )
    selected: list[dict] = []
    rejected = 0
    for candidate in candidates:
        payload = dict(candidate["payload"])
        key = _column_payload_key(payload)
        if key in existing_keys:
            rejected += 1
            continue
        existing_keys.add(key)
        payload["vehicle_id"] = f"b4_2_partition_feedback_r{round_index:02d}_{len(selected) + 1:03d}"
        selected.append({**candidate, "payload": payload})
        if len(selected) >= max(0, int(max_columns)):
            break
    merged = dict(source)
    before = len(active_columns)
    merged["active_columns_payload_version"] = "journey_solution_payload.v1"
    merged["active_columns"] = active_columns + [item["payload"] for item in selected]
    merged["b4_2_partition_feedback_merge"] = {
        "schema_version": "lunar_ice_bpc.b4_2.partition_feedback_merge.v1",
        "source_probe": str(source_probe),
        "partition_dir": str(partition_dir),
        "round_index": int(round_index),
        "candidate_count": len(candidates),
        "selected_count": len(selected),
        "rejected_duplicate_count": int(rejected),
        "before_active_column_count": before,
        "after_active_column_count": len(merged["active_columns"]),
        "selected": [
            {
                "source_json": item["source_json"],
                "row_index": item["row_index"],
                "region_id": item["region_id"],
                "task_set": item["task_set"],
                "true_rc": item["true_rc"],
                "replacement_or_new_task_set": item["replacement_or_new_task_set"],
            }
            for item in selected
        ],
    }
    output_probe.parent.mkdir(parents=True, exist_ok=True)
    output_probe.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "output_probe": str(output_probe),
        "candidate_count": len(candidates),
        "selected_count": len(selected),
        "added_count": len(merged["active_columns"]) - before,
        "rejected_count": int(rejected),
        "before_active_column_count": before,
        "after_active_column_count": len(merged["active_columns"]),
        "best_true_rc": None if not selected else min(float(item["true_rc"]) for item in selected),
    }


def _partition_negative_payload_candidates(*, partition_dir: Path, negative_eps: float) -> list[dict]:
    candidates: list[dict] = []
    for path in _partition_probe_json_paths(partition_dir):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            solution = row.get("partition_negative_solution_payload")
            if not isinstance(solution, dict):
                continue
            true_rc = _first_float(row.get("partition_negative_true_rc"), row.get("best_reduced_cost"))
            if true_rc is None or float(true_rc) >= -abs(float(negative_eps)):
                continue
            if row.get("partition_negative_rc_audit_pass") is not True:
                continue
            pricing_diff = _first_float(row.get("partition_negative_pricing_rc_diff"))
            if pricing_diff is not None and abs(float(pricing_diff)) > 1.0e-6:
                continue
            candidates.append(
                {
                    "source_json": str(path),
                    "row_index": int(index),
                    "region_id": str(row.get("region_id") or ""),
                    "task_set": list(row.get("partition_negative_task_set") or []),
                    "task_set_size": _int(row.get("partition_negative_task_set_size")),
                    "true_rc": float(true_rc),
                    "replacement_or_new_task_set": str(
                        row.get("partition_negative_replacement_or_new_task_set") or ""
                    ),
                    "already_active": bool(row.get("partition_negative_already_active")),
                    "active_task_set_seen": bool(row.get("partition_negative_active_task_set_seen")),
                    "payload": solution,
                }
            )
    return sorted(
        candidates,
        key=lambda item: (
            0 if item["replacement_or_new_task_set"] == "new_task_set" else 1,
            float(item["true_rc"]),
            int(item["task_set_size"] or 9999),
            str(item["region_id"]),
        ),
    )


def _partition_probe_json_paths(partition_dir: Path) -> list[Path]:
    candidates = []
    direct = Path(partition_dir) / "required_task_set_partition_probe.json"
    if direct.exists():
        candidates.append(direct)
    candidates.extend(sorted(Path(partition_dir).glob("worker_*/required_task_set_partition_probe.json")))
    return candidates


def _column_payload_key(column: dict) -> tuple:
    sortie_keys = []
    for sortie in column.get("sorties") or []:
        tasks = tuple(str(task_id) for task_id in sortie.get("tasks") or [])
        legs = tuple(
            (str(leg.get("from")), str(leg.get("to")), str(leg.get("path_type")))
            for leg in sortie.get("legs") or []
        )
        start_time = round(float(sortie.get("start_time", 0.0)), 6)
        service_starts = tuple(
            sorted(
                (str(task_id), round(float(value), 6))
                for task_id, value in (sortie.get("service_starts") or {}).items()
            )
        )
        sortie_keys.append((tasks, legs, start_time, service_starts))
    return tuple(sortie_keys)


def _set_pool_latest_probe(pool_dir: Path, probe_path: Path, merge: dict) -> None:
    manifest_path = Path(pool_dir) / "staged_resume_manifest.json"
    manifest = _load_state(manifest_path)
    merges = list(manifest.get("b4_2_partition_feedback_merges") or [])
    merges.append(dict(merge))
    manifest["latest_probe"] = str(probe_path)
    manifest["b4_2_partition_feedback_merges"] = merges
    _write_json(manifest_path, manifest)


def _partition_region_pair(region_id) -> tuple[int, int] | None:
    text = str(region_id or "")
    prefix = "residual_task_count_"
    marker = "_active_sorties_"
    if not text.startswith(prefix) or marker not in text:
        return None
    left, right = text[len(prefix):].split(marker, 1)
    try:
        return int(left), int(right)
    except ValueError:
        return None


def _partition_k_chunks(task_count: int, worker_count: int, *, k_chunk_size: int = 2) -> list[tuple[int, int]]:
    k_chunk_size = max(1, int(k_chunk_size))
    chunks: list[tuple[int, int]] = []
    start = 1
    while start <= int(task_count):
        end = min(int(task_count), start + k_chunk_size - 1)
        chunks.append((start, end))
        start = end + 1
    return chunks


def _source_probe_task_count(source_probe: Path) -> int:
    try:
        payload = json.loads(Path(source_probe).read_text(encoding="utf-8"))
        instance_path = payload.get("instance_path")
        if instance_path:
            return len(_load_task_ids(_resolve(instance_path)))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return 0
    return 0


def _root_partition_tree_gate(source_probe: Path | None, partition_row: dict) -> dict:
    if source_probe is None or not Path(source_probe).exists():
        return {
            "algorithm_status": "BPC_INCOMPLETE_PRICING",
            "certificate_scope": "BPC_NODE_LP_CERTIFIED",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "exact_certificate": False,
            "bpc_tree_optimal": False,
            "fail_reason": "root partition certified pricing but source probe is missing for tree gate",
        }
    payload = json.loads(Path(source_probe).read_text(encoding="utf-8"))
    integral_root = payload.get("integral_root")
    root_lp_bound = _first_float(payload.get("root_lp_bound"), payload.get("root_rmp_objective"))
    b0 = payload.get("b0_ablation") if isinstance(payload.get("b0_ablation"), dict) else {}
    direct_objective = _first_float(b0.get("direct_dp_objective"))
    root_gap = _first_float(payload.get("root_lp_vs_direct_dp_gap"))
    gate_pass = bool(integral_root is True)
    if gate_pass:
        return {
            "algorithm_status": "BPC_OPTIMAL",
            "certificate_scope": "BPC_TREE_OPTIMAL",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "exact_certificate": True,
            "bpc_tree_optimal": True,
            "tree_gate_source": "root_partition_no_negative_integral_root",
            "root_integral": True,
            "root_lp_bound": root_lp_bound,
            "direct_dp_objective": direct_objective,
            "root_lp_vs_direct_dp_gap": root_gap,
            "manual_rc_fail": 0,
            "pricing_rc_fail": 0,
            "certificate_leak": 0,
            "fail_reason": "",
        }
    return {
        "algorithm_status": "BPC_GAP_AVAILABLE",
        "certificate_scope": "BPC_NODE_LP_CERTIFIED",
        "pricing_state": "CERTIFIED_NO_NEGATIVE",
        "exact_certificate": False,
        "bpc_tree_optimal": False,
        "tree_gate_source": "root_partition_no_negative_nonintegral_or_unknown_root",
        "root_integral": integral_root,
        "root_lp_bound": root_lp_bound,
        "direct_dp_objective": direct_objective,
        "root_lp_vs_direct_dp_gap": root_gap,
        "fail_reason": "root partition certified node LP but root is not proven integral; branch tree closure still required",
    }


def _solver_env(args: argparse.Namespace) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = _prepend_pythonpath(env.get("PYTHONPATH", ""), ROOT / "src")
    env["LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE"] = str(args.profile)
    env["LUNAR_ICE_COMPACT_FINAL_JUDGE_THREADS"] = str(int(args.threads))
    env["LUNAR_ICE_COMPACT_HIGHS_THREADS"] = str(int(args.threads))
    env.setdefault("LUNAR_ICE_COMPACT_HIGHS_PARALLEL", "on")
    env["LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST"] = "1"
    env["LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_TARGET"] = str(
        int(args.route_template_pre_harvest_target)
    )
    env["LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_TIME_CAP_SEC"] = str(
        float(args.route_template_pre_harvest_time_cap_sec)
    )
    env["LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_MAX_DIRECT_TASKS"] = str(
        int(args.route_template_pre_harvest_max_direct_tasks)
    )
    env["LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_MAX_ACTIVE_SEEDS"] = str(
        int(args.route_template_pre_harvest_max_active_seeds)
    )
    env["LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_NEIGHBORHOOD"] = "1"
    env["LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_MAX_NEIGHBORHOOD_SEEDS"] = str(
        int(args.route_template_pre_harvest_max_neighborhood_seeds)
    )
    env["LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_MAX_CANDIDATE_SETS"] = str(
        int(args.route_template_pre_harvest_max_candidate_sets)
    )
    env["LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_FALLBACK"] = "1"
    return env


def _base_row(
    args: argparse.Namespace,
    *,
    config_hash: str,
    instance_index: int,
    instance_path: Path,
    status: str,
    note: str = "",
) -> dict:
    task_ids = _load_task_ids(instance_path)
    return {
        "schema_version": "lunar_ice_bpc.b4_2_cold_exact_row.v1",
        "model_id": str(args.model_id),
        "config_hash": str(config_hash),
        "scale": len(task_ids),
        "instance_index": int(instance_index),
        "instance_key": _instance_key(instance_path),
        "instance_path": str(instance_path),
        "row_limit_sec": float(args.row_limit_sec),
        "threads": int(args.threads),
        "profile": str(args.profile),
        "seed_mode": str(args.seed_mode),
        "column_provenance": COLUMN_PROVENANCE,
        "external_probe_used": False,
        "mature_pool_used": False,
        "manual_columns_used": False,
        "per_instance_override_used": False,
        "same_run_checkpoint_resume_allowed": True,
        "no_cheat_pass": True,
        "algorithm_status": str(status),
        "certificate_scope": "",
        "pricing_state": "",
        "exact_certificate": False,
        "bpc_tree_optimal": False,
        "under_300": False,
        "under_acceptance_limit": False,
        "under_500": False,
        "cold_start_total_sec": None,
        "cold_start_stage_sum_sec": None,
        "seed_sec": None,
        "root_cg_sec": None,
        "root_partition_sec": None,
        "root_partition_feedback_sec": 0.0,
        "root_partition_feedback_round_count": 0,
        "root_partition_feedback_added_column_count": 0,
        "root_partition_proof_enabled": False,
        "root_partition_certified_no_negative": False,
        "tree_sec": None,
        "pricing_proof_sec": None,
        "manual_rc_fail": 0,
        "pricing_rc_fail": 0,
        "certificate_leak": 0,
        "row_terminal": False,
        "fail_reason": "",
        "note": str(note),
    }


def _finish_timing(row: dict, started: float) -> dict:
    total = round(perf_counter() - started, 6)
    row["cold_start_total_sec"] = total
    row["cold_start_stage_sum_sec"] = _add_optional(
        _add_optional(
            _add_optional(row.get("root_cg_sec"), row.get("root_partition_feedback_sec")),
            row.get("root_partition_sec"),
        ),
        row.get("tree_sec"),
    )
    under_limit = bool(row.get("exact_certificate")) and total < ACCEPTANCE_LIMIT_SEC
    row["under_acceptance_limit"] = under_limit
    row["under_300"] = bool(row.get("exact_certificate")) and total < 300.0
    row["under_500"] = bool(row.get("exact_certificate")) and total < 500.0
    return row


def _pool_manifest(pool_dir: Path) -> dict:
    path = pool_dir / "staged_resume_manifest.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _latest_stage(manifest: dict) -> dict:
    stages = list(manifest.get("stages") or [])
    return stages[-1] if stages and isinstance(stages[-1], dict) else {}


def _latest_pool_probe(pool_dir: Path) -> Path | None:
    manifest = _pool_manifest(pool_dir)
    latest = manifest.get("latest_probe")
    if latest:
        path = _resolve(latest)
        if path.exists():
            return path
    probes = sorted(pool_dir.glob("stage_*/probe.json"))
    return probes[-1] if probes else None


def _write_artifacts(
    rows: list[dict],
    *,
    config: dict,
    limited_run: bool,
    discovered_instance_count: int,
    expected_scale_counts: dict[str, int],
    rows_path: Path,
    state_path: Path,
    summary_path: Path,
    report_path: Path,
) -> None:
    rows_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps({"rows": rows}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    fieldnames = sorted({key for row in rows for key in row})
    with rows_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    summary = _summary(
        rows,
        config=config,
        limited_run=limited_run,
        discovered_instance_count=discovered_instance_count,
        expected_scale_counts=expected_scale_counts,
    )
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(_render_report(rows, summary), encoding="utf-8")


def _summary(
    rows: list[dict],
    *,
    config: dict,
    limited_run: bool,
    discovered_instance_count: int,
    expected_scale_counts: dict[str, int] | None = None,
) -> dict:
    expected_scale_counts = dict(expected_scale_counts or {})
    by_scale: dict[str, dict] = {}
    for scale in sorted({int(row.get("scale") or 0) for row in rows}):
        scale_rows = [row for row in rows if int(row.get("scale") or 0) == scale]
        exact_rows = [row for row in scale_rows if bool(row.get("exact_certificate"))]
        under_rows = [row for row in exact_rows if _row_under_acceptance_limit(row)]
        under_300_rows = [row for row in exact_rows if bool(row.get("under_300"))]
        by_scale[str(scale)] = {
            "row_count": len(scale_rows),
            "exact_count": len(exact_rows),
            "under_acceptance_limit_exact_count": len(under_rows),
            "under_500_exact_count": len(under_rows),
            "under_300_exact_count": len(under_300_rows),
            "fail_closed_count": len(scale_rows) - len(exact_rows),
            "mean_cold_start_total_sec": _mean(row.get("cold_start_total_sec") for row in scale_rows),
            "max_cold_start_total_sec": _max(row.get("cold_start_total_sec") for row in scale_rows),
            "mean_exact_cold_start_total_sec": _mean(row.get("cold_start_total_sec") for row in exact_rows),
            "mean_root_cg_sec": _mean(row.get("root_cg_sec") for row in scale_rows),
            "mean_root_partition_sec": _mean(row.get("root_partition_sec") for row in scale_rows),
            "mean_tree_sec": _mean(row.get("tree_sec") for row in scale_rows),
        }
    config_hashes = sorted({str(row.get("config_hash") or "") for row in rows if row.get("config_hash")})
    no_cheat_fail = [
        row for row in rows
        if not bool(row.get("no_cheat_pass"))
        or bool(row.get("external_probe_used"))
        or bool(row.get("mature_pool_used"))
        or bool(row.get("manual_columns_used"))
        or bool(row.get("per_instance_override_used"))
    ]
    scale30_rows = [row for row in rows if int(row.get("scale") or 0) == 30]
    expected_scale30_count = int(expected_scale_counts.get("30") or discovered_instance_count)
    scale30_complete = not limited_run and scale30_rows and len(scale30_rows) == expected_scale30_count
    return {
        "schema_version": "lunar_ice_bpc.b4_2_cold_exact_summary.v1",
        "config": config,
        "config_hash": _config_hash(config),
        "unique_config_hash_count": len(config_hashes),
        "config_hashes": config_hashes,
        "row_count": len(rows),
        "limited_run": bool(limited_run),
        "discovered_instance_count": int(discovered_instance_count),
        "expected_scale_counts": expected_scale_counts,
        "by_scale": by_scale,
        "redlines": {
            "no_cheat_fail_count": len(no_cheat_fail),
            "manual_rc_fail_count": sum(_int(row.get("manual_rc_fail")) for row in rows),
            "pricing_rc_fail_count": sum(_int(row.get("pricing_rc_fail")) for row in rows),
            "certificate_leak_count": sum(_int(row.get("certificate_leak")) for row in rows),
        },
        "acceptance": {
            "same_model_config_hash": len(config_hashes) <= 1,
            "full_scale30_run_complete": bool(scale30_complete),
            "scale30_all_bpc_tree_optimal": bool(scale30_complete and all(row.get("certificate_scope") == "BPC_TREE_OPTIMAL" for row in scale30_rows)),
            "scale30_all_under_acceptance_limit": bool(
                scale30_complete and all(_row_under_acceptance_limit(row) for row in scale30_rows)
            ),
            "scale30_all_under_500": bool(
                scale30_complete and all(_row_under_acceptance_limit(row) for row in scale30_rows)
            ),
            "scale30_all_under_300": bool(
                scale30_complete and all(bool(row.get("under_300")) for row in scale30_rows)
            ),
            "b4_2_cold_exact_accepted": bool(
                scale30_complete
                and len(config_hashes) == 1
                and not no_cheat_fail
                and all(
                    bool(row.get("exact_certificate")) and _row_under_acceptance_limit(row)
                    for row in scale30_rows
                )
            ),
        },
    }


def _row_under_acceptance_limit(row: dict) -> bool:
    if "under_acceptance_limit" in row:
        return bool(row.get("under_acceptance_limit"))
    if "under_500" in row:
        return bool(row.get("under_500"))
    total = _first_float(row.get("cold_start_total_sec"))
    return bool(row.get("exact_certificate")) and total is not None and total < ACCEPTANCE_LIMIT_SEC


def _render_report(rows: list[dict], summary: dict) -> str:
    lines = [
        "# B4.2 Cold-Start Exact 500s Report",
        "",
        "## 边界",
        "",
        "- 正式行必须从 `instance_XXX_logical_graph.json` 冷启动。",
        "- 禁止外部 mature probe、同实例历史列池、手工补列、按实例调参。",
        "- 同一次 run 内 staged checkpoint 可以续跑，但所有 stage 时间计入 `cold_start_total_sec`。",
        "- `BPC_TREE_OPTIMAL` 只证明 normalized additive objective，不证明 makespan-in-objective。",
        "- B4.2 V1 固定 seed 为 B0 incumbent + singleton，并启用固定 route-template pre-harvest worker；worker 只找列，不给 no-negative 证书。",
        "",
        "## 汇总",
        "",
        f"- model: `{summary.get('config', {}).get('model_id')}`",
        f"- config hash: `{summary.get('config_hash')}`",
        f"- rows: `{summary.get('row_count')}`",
        f"- no-cheat fail: `{summary.get('redlines', {}).get('no_cheat_fail_count')}`",
        f"- accepted: `{summary.get('acceptance', {}).get('b4_2_cold_exact_accepted')}`",
        "",
        "| scale | rows | exact | under500 exact | fail-closed | mean total | max total | mean root | mean partition | mean tree |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for scale, item in (summary.get("by_scale") or {}).items():
        lines.append(
            f"| {scale} | {item.get('row_count')} | {item.get('exact_count')} | "
            f"{item.get('under_acceptance_limit_exact_count')} | {item.get('fail_closed_count')} | "
            f"{item.get('mean_cold_start_total_sec')} | {item.get('max_cold_start_total_sec')} | "
            f"{item.get('mean_root_cg_sec')} | {item.get('mean_root_partition_sec')} | {item.get('mean_tree_sec')} |"
        )
    lines.extend(
        [
            "",
            "## Per-Instance",
            "",
            "| scale | instance | status | scope | pricing | exact | under500 | total | root | partition | tree | active cols | provenance | fail reason |",
            "|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row.get('scale')} | {row.get('instance_key')} | {row.get('algorithm_status')} | "
            f"{row.get('certificate_scope')} | {row.get('pricing_state')} | "
            f"{row.get('exact_certificate')} | {_row_under_acceptance_limit(row)} | "
            f"{row.get('cold_start_total_sec')} | {row.get('root_cg_sec')} | "
            f"{row.get('root_partition_sec')} | {row.get('tree_sec')} | "
            f"{row.get('root_pool_active_column_count') or row.get('tree_loaded_column_count')} | "
            f"{row.get('column_provenance')} | {str(row.get('fail_reason') or '')[:140]} |"
        )
    return "\n".join(lines) + "\n"


def _resolve(path: str | Path) -> Path:
    raw = Path(path)
    return raw if raw.is_absolute() else ROOT / raw


def _instance_key(path: Path) -> str:
    name = path.name
    if name.startswith("instance_") and "_logical_graph" in name:
        return name.split("_logical_graph", 1)[0]
    return path.stem


def _load_task_ids(instance_path: Path) -> tuple[str, ...]:
    payload = json.loads(instance_path.read_text(encoding="utf-8"))
    tasks = payload.get("tasks") or []
    if isinstance(tasks, dict):
        return tuple(str(task_id) for task_id in sorted(tasks))
    if isinstance(tasks, list):
        ids = []
        for index, row in enumerate(tasks):
            if isinstance(row, dict):
                ids.append(str(row.get("id") or row.get("task_id") or index))
            else:
                ids.append(str(index))
        return tuple(ids)
    task_ids = payload.get("task_ids") or []
    return tuple(str(task_id) for task_id in task_ids)


def _load_state(path: Path) -> dict:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _dedupe_rows(rows: list[dict]) -> list[dict]:
    by_key: dict[str, dict] = {}
    for row in rows:
        by_key[str(row.get("instance_key") or "")] = row
    return list(by_key.values())


def _upsert_row(rows: list[dict], row: dict) -> list[dict]:
    key = str(row.get("instance_key") or "")
    replaced = False
    output = []
    for existing in rows:
        if str(existing.get("instance_key") or "") == key:
            output.append(row)
            replaced = True
        else:
            output.append(existing)
    if not replaced:
        output.append(row)
    return output


def _has_checkpoint(output_dir: Path) -> bool:
    if not output_dir.exists():
        return False
    markers = (
        output_dir / "b4_2_cold_exact_state.json",
        output_dir / "pools",
        output_dir / "proofs",
    )
    return any(path.exists() for path in markers)


def _resource_ok(
    *,
    output_dir: Path,
    min_available_mem_gb: float,
    min_free_disk_gb: float,
    max_output_dir_gb: float,
) -> bool:
    output_dir.mkdir(parents=True, exist_ok=True)
    return (
        _available_mem_gb() >= float(min_available_mem_gb)
        and shutil.disk_usage(output_dir).free / (1024**3) >= float(min_free_disk_gb)
        and _directory_size_bytes(output_dir) / (1024**3) <= float(max_output_dir_gb)
    )


def _available_mem_gb() -> float:
    path = Path("/proc/meminfo")
    if not path.exists():
        return 999.0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("MemAvailable:"):
            parts = line.split()
            if len(parts) >= 2:
                return float(parts[1]) / (1024**2)
    return 999.0


def _directory_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            try:
                total += child.stat().st_size
            except OSError:
                pass
    return total


def _prepend_pythonpath(existing: str, path: Path) -> str:
    return str(path) if not existing else f"{path}{os.pathsep}{existing}"


def _sum_float(rows: list[dict], key: str) -> float:
    total = 0.0
    for row in rows:
        value = _first_float(row.get(key))
        if value is not None:
            total += value
    return round(total, 6)


def _add_optional(left, right) -> float | None:
    left_value = _first_float(left)
    right_value = _first_float(right)
    if left_value is None and right_value is None:
        return None
    return round(float(left_value or 0.0) + float(right_value or 0.0), 6)


def _first_float(*values) -> float | None:
    for value in values:
        try:
            if value is not None and value != "":
                return float(value)
        except (TypeError, ValueError):
            pass
    return None


def _int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _mean(values) -> float | None:
    numbers = [float(value) for value in (_first_float(value) for value in values) if value is not None]
    if not numbers:
        return None
    return round(sum(numbers) / len(numbers), 6)


def _max(values) -> float | None:
    numbers = [float(value) for value in (_first_float(value) for value in values) if value is not None]
    return round(max(numbers), 6) if numbers else None


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Official B4.3 cold-start SPPRC labeling runner.

B4.3 keeps the no-cheat B4.2 benchmark shell but makes SPPRC labeling the
official pricing route: relaxed/ng labeling is candidate search only, and the
exact elementary labeler is the only no-negative certificate source.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_lunar_ice_b4_2_cold_exact as b42
from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (
    SPPRC_ENGINE_SOURCE,
    SPPRC_EXACT_MODE,
    SPPRC_MODEL_ID,
    SPPRC_WORKER_MODE,
    spprc_engine_build_hash,
)


MODEL_ID = SPPRC_MODEL_ID
OUTPUT_DIR = "runs/b4_3_spprc_labeling_1800s_full"
ROW_LIMIT_SEC = 1800.0
ACCEPTANCE_LIMIT_SEC = 1800.0
THREADS = 4
PROFILE = "V4SZ"
SPPRC_NG_SIZES = (6, 10, 14, 30)
LABELING_FINAL_JUDGE_EXACT_HARVEST_TARGET = 1024
LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_SCHEDULE: tuple[dict, ...] = tuple()
ACTIVE_TASK_SET_HARD_PREFERENCE_LIMIT = 4000
EXACT_FINAL_JUDGE_FIRST = True
WORKER_NEGATIVE_BATCH_EARLY_STOP = True
WORKER_NEGATIVE_BATCH_TARGET = 128
WORKER_RESOURCE_EXTENSION_SEED_ENABLED = False
WORKER_HARD_TIME_CAP_SEC = 30.0
ACTIVE_TASK_SET_AWARE_EXACT_HARVEST = True
COLUMN_PROVENANCE = "instance_json_fixed_seed_same_run_checkpoint_spprc_labeling"
POOL_EARLY_MAX_ROUNDS_PER_STAGE = 1
POOL_TAIL_ONE_ROUND_ACTIVE_THRESHOLD = 6000
POOL_TAIL_MAX_ROUNDS_PER_STAGE = 1
POOL_STAGE_BATCH_TIME_RESERVE_SEC = 30.0
RMP_SOLVER = "highs"
RMP_HIGHS_THREADS = 1
ROWS_NAME = "b4_3_spprc_labeling_rows.csv"
STATE_NAME = "b4_3_spprc_labeling_state.json"
SUMMARY_NAME = "b4_3_spprc_labeling_summary.json"
REPORT_NAME = "b4_3_spprc_labeling_1800s_report_zh.md"


def main() -> int:
    b42.ACCEPTANCE_LIMIT_SEC = ACCEPTANCE_LIMIT_SEC
    b42.COLUMN_PROVENANCE = COLUMN_PROVENANCE
    parser = _build_parser()
    args = parser.parse_args()
    _validate_args(parser, args)
    _install_b43_solver_env()

    output_dir = b42._resolve(args.output_dir)
    if not args.resume and b42._has_checkpoint(output_dir):
        parser.error(
            "--no-resume requires a fresh output directory; refusing to risk "
            "same-instance historical checkpoint reuse"
        )
    output_dir.mkdir(parents=True, exist_ok=True)

    config = _official_config(args)
    config_hash = b42._config_hash(config)
    instances = b42._instance_paths(args)
    expected_scale_counts = b42._scale_counts(instances)
    rows_path = output_dir / ROWS_NAME
    state_path = output_dir / STATE_NAME
    summary_path = output_dir / SUMMARY_NAME
    report_path = output_dir / REPORT_NAME

    state = b42._load_state(state_path) if args.resume else {}
    _enforce_resume_config(state, config_hash=config_hash, parser=parser)
    rows = b42._dedupe_rows(list(state.get("rows") or []))
    completed_keys = {
        str(row.get("instance_key") or "")
        for row in rows
        if bool(row.get("row_terminal"))
    }
    limited_run = bool(args.limit or args.instance)

    for index, instance_path in enumerate(instances, start=1):
        instance_key = b42._instance_key(instance_path)
        if args.resume and instance_key in completed_keys:
            continue
        if not b42._resource_ok(
            output_dir=output_dir,
            min_available_mem_gb=float(args.min_available_mem_gb),
            min_free_disk_gb=float(args.min_free_disk_gb),
            max_output_dir_gb=float(args.max_output_dir_gb),
        ):
            row = b42._base_row(
                args,
                config_hash=config_hash,
                instance_index=index,
                instance_path=instance_path,
                status="RESOURCE_GUARD_STOPPED",
                note="resource guard stopped before row start",
            )
            row = _apply_b43_row_overlay(row, args)
            rows = b42._upsert_row(rows, row)
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

        previous_row = b42._row_for_instance(rows, instance_key) if args.resume else None
        row = b42._run_instance_cold(
            args,
            config_hash=config_hash,
            instance_index=index,
            instance_path=instance_path,
            previous_row=previous_row,
        )
        row = _apply_b43_row_overlay(row, args)
        rows = b42._upsert_row(rows, row)
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
    parser = b42._build_parser()
    parser.description = (
        "Run the no-cheat B4.3 SPPRC labeling cold-start benchmark. "
        "External mature probes and manual source probes are deliberately unsupported."
    )
    parser.set_defaults(
        output_dir=OUTPUT_DIR,
        scales=[30],
        model_id=MODEL_ID,
        row_limit_sec=ROW_LIMIT_SEC,
        threads=THREADS,
        profile=PROFILE,
        root_engine="b2b_r3_worker",
        worker_pricer_kind="relaxed_labeling",
        labeling_worker_max_task_cap=30,
        tail_dual_stabilization_enabled=True,
        labeling_final_judge_mode="on",
        labeling_final_judge_max_exact_tasks=30,
        labeling_final_judge_exact_harvest_target=LABELING_FINAL_JUDGE_EXACT_HARVEST_TARGET,
        large_task_direct_worker_enabled=False,
        pool_stage_time_slice_sec=600.0,
        pool_stage_batch_time_reserve_sec=POOL_STAGE_BATCH_TIME_RESERVE_SEC,
        pool_min_stage_sec=30.0,
        pool_max_stages=64,
        pool_max_rounds_per_stage=POOL_EARLY_MAX_ROUNDS_PER_STAGE,
        pool_tail_one_round_active_threshold=POOL_TAIL_ONE_ROUND_ACTIVE_THRESHOLD,
        pool_tail_max_rounds_per_stage=POOL_TAIL_MAX_ROUNDS_PER_STAGE,
        pool_batch_target=LABELING_FINAL_JUDGE_EXACT_HARVEST_TARGET,
        pool_negative_search_cap_sec=120.0,
        pool_optimization_harvest_target=LABELING_FINAL_JUDGE_EXACT_HARVEST_TARGET,
        root_partition_proof=False,
        partition_feedback_rounds=0,
        tree_closure_max_rounds=32,
        tree_closure_max_columns_per_round=512,
    )
    parser.add_argument(
        "--spprc-ng-sizes",
        default=",".join(str(size) for size in SPPRC_NG_SIZES),
        help=(
            "Fixed comma-separated ng-neighborhood schedule for the relaxed "
            "worker labeler. This is part of the B4.3 config hash."
        ),
    )
    return parser


def _validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if int(args.threads) != THREADS:
        parser.error(f"B4.3 official runner requires fixed --threads {THREADS}")
    if str(args.model_id) != MODEL_ID:
        parser.error(f"B4.3 official runner requires --model-id {MODEL_ID}")
    if bool(args.root_partition_proof):
        parser.error("B4.3 official runner does not allow root partition proof as certificate path")
    if str(args.worker_pricer_kind) != "relaxed_labeling":
        parser.error("B4.3 official runner requires --worker-pricer-kind relaxed_labeling")
    if str(args.labeling_final_judge_mode) != "on":
        parser.error("B4.3 official runner requires --labeling-final-judge-mode on")
    if int(args.labeling_worker_max_task_cap) != 30:
        parser.error("B4.3 official runner requires --labeling-worker-max-task-cap 30")
    if int(args.labeling_final_judge_max_exact_tasks) != 30:
        parser.error("B4.3 official runner requires --labeling-final-judge-max-exact-tasks 30")
    if int(args.labeling_final_judge_exact_harvest_target) != LABELING_FINAL_JUDGE_EXACT_HARVEST_TARGET:
        parser.error(
            "B4.3 official runner requires fixed "
            f"--labeling-final-judge-exact-harvest-target {LABELING_FINAL_JUDGE_EXACT_HARVEST_TARGET}"
        )
    if int(args.pool_optimization_harvest_target) != LABELING_FINAL_JUDGE_EXACT_HARVEST_TARGET:
        parser.error(
            "B4.3 official runner requires fixed "
            f"--pool-optimization-harvest-target {LABELING_FINAL_JUDGE_EXACT_HARVEST_TARGET}"
        )
    if int(args.pool_max_rounds_per_stage) != POOL_EARLY_MAX_ROUNDS_PER_STAGE:
        parser.error(
            "B4.3 official runner requires fixed early "
            f"--pool-max-rounds-per-stage {POOL_EARLY_MAX_ROUNDS_PER_STAGE}"
        )
    if int(args.pool_tail_one_round_active_threshold) != POOL_TAIL_ONE_ROUND_ACTIVE_THRESHOLD:
        parser.error(
            "B4.3 official runner requires fixed "
            f"--pool-tail-one-round-active-threshold {POOL_TAIL_ONE_ROUND_ACTIVE_THRESHOLD}"
        )
    if int(args.pool_tail_max_rounds_per_stage) != POOL_TAIL_MAX_ROUNDS_PER_STAGE:
        parser.error(
            "B4.3 official runner requires fixed "
            f"--pool-tail-max-rounds-per-stage {POOL_TAIL_MAX_ROUNDS_PER_STAGE}"
        )
    if abs(float(args.pool_stage_batch_time_reserve_sec) - float(POOL_STAGE_BATCH_TIME_RESERVE_SEC)) > 1.0e-9:
        parser.error(
            "B4.3 official runner requires fixed "
            f"--pool-stage-batch-time-reserve-sec {POOL_STAGE_BATCH_TIME_RESERVE_SEC}"
        )
    _parse_ng_sizes(args.spprc_ng_sizes, max_size=30)


def _official_config(args: argparse.Namespace) -> dict:
    config = b42._official_config(args)
    ng_sizes = _parse_ng_sizes(args.spprc_ng_sizes, max_size=30)
    config.update(
        {
            "schema_version": "lunar_ice_bpc.b4_3_spprc_labeling_config.v1",
            "model_id": MODEL_ID,
            "acceptance_limit_sec": float(ACCEPTANCE_LIMIT_SEC),
            "column_provenance": COLUMN_PROVENANCE,
            "spprc_engine_source": SPPRC_ENGINE_SOURCE,
            "spprc_engine_build_hash": spprc_engine_build_hash(),
            "spprc_worker_mode": SPPRC_WORKER_MODE,
            "spprc_exact_mode": SPPRC_EXACT_MODE,
            "spprc_ng_sizes": list(ng_sizes),
            "spprc_exact_final_judge_first": bool(EXACT_FINAL_JUDGE_FIRST),
            "spprc_worker_negative_batch_early_stop": bool(WORKER_NEGATIVE_BATCH_EARLY_STOP),
            "spprc_worker_negative_batch_target": int(WORKER_NEGATIVE_BATCH_TARGET),
            "spprc_worker_resource_extension_seed_enabled": bool(
                WORKER_RESOURCE_EXTENSION_SEED_ENABLED
            ),
            "spprc_worker_hard_time_cap_sec": float(WORKER_HARD_TIME_CAP_SEC),
            "spprc_active_task_set_aware_exact_harvest": bool(ACTIVE_TASK_SET_AWARE_EXACT_HARVEST),
            "spprc_active_task_set_hard_preference_limit": int(
                ACTIVE_TASK_SET_HARD_PREFERENCE_LIMIT
            ),
            "spprc_pool_early_max_rounds_per_stage": int(POOL_EARLY_MAX_ROUNDS_PER_STAGE),
            "spprc_pool_stage_batch_time_reserve_sec": float(POOL_STAGE_BATCH_TIME_RESERVE_SEC),
            "spprc_pool_tail_one_round_active_threshold": int(
                POOL_TAIL_ONE_ROUND_ACTIVE_THRESHOLD
            ),
            "spprc_pool_tail_max_rounds_per_stage": int(POOL_TAIL_MAX_ROUNDS_PER_STAGE),
            "rmp_solver": RMP_SOLVER,
            "rmp_highs_threads": int(RMP_HIGHS_THREADS),
            "spprc_adaptive_exact_harvest_schedule": [
                dict(row) for row in LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_SCHEDULE
            ],
            "spprc_relaxed_worker_can_certify": False,
            "spprc_exact_proof_required_for_certificate": True,
            "compact_milp_final_judge_official": False,
            "root_partition_proof": False,
            "partition_ledger_official": False,
            "root_tree_pricing_oracle": "spprc_labeling_worker_with_exact_elementary_final_proof",
            "b4_2_partition_feedback_official": False,
            "minimum_acceptance_gate": "full_30_scale_cold_start_bpc_tree_optimal_under_1800s",
            "stretch_target_sec": 300.0,
        }
    )
    return config


def _install_b43_solver_env() -> None:
    original_solver_env = b42._solver_env

    def solver_env(args: argparse.Namespace) -> dict[str, str]:
        env = original_solver_env(args)
        env["LUNAR_ICE_LABELING_WORKER_NG_SIZES"] = ",".join(
            str(size) for size in _parse_ng_sizes(args.spprc_ng_sizes, max_size=30)
        )
        env["LUNAR_ICE_EXACT_FINAL_JUDGE_FIRST"] = "1" if EXACT_FINAL_JUDGE_FIRST else "0"
        env["LUNAR_ICE_LABELING_WORKER_NEGATIVE_BATCH_EARLY_STOP"] = (
            "1" if WORKER_NEGATIVE_BATCH_EARLY_STOP else "0"
        )
        env["LUNAR_ICE_LABELING_WORKER_NEGATIVE_BATCH_TARGET"] = str(
            int(WORKER_NEGATIVE_BATCH_TARGET)
        )
        env["LUNAR_ICE_LABELING_WORKER_RESOURCE_EXTENSION_SEED"] = (
            "1" if WORKER_RESOURCE_EXTENSION_SEED_ENABLED else "0"
        )
        env["LUNAR_ICE_LABELING_WORKER_HARD_TIME_CAP_SEC"] = str(
            float(WORKER_HARD_TIME_CAP_SEC)
        )
        if LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_SCHEDULE:
            env["LUNAR_ICE_LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_SCHEDULE"] = (
                _encode_adaptive_harvest_schedule(LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_SCHEDULE)
            )
        else:
            env["LUNAR_ICE_LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_SCHEDULE"] = "disabled"
        env["LUNAR_ICE_RMP_SOLVER"] = RMP_SOLVER
        env["LUNAR_ICE_RMP_HIGHS_THREADS"] = str(int(RMP_HIGHS_THREADS))
        return env

    b42._solver_env = solver_env


def _encode_adaptive_harvest_schedule(rows: tuple[dict, ...]) -> str:
    return ",".join(
        f"{int(row['active_task_set_count_gte'])}:{int(row['target_cap'])}"
        for row in rows
    )


def _apply_b43_row_overlay(row: dict, args: argparse.Namespace) -> dict:
    ng_sizes = _parse_ng_sizes(args.spprc_ng_sizes, max_size=30)
    row = dict(row)
    row.update(
        {
            "schema_version": "lunar_ice_bpc.b4_3_spprc_labeling_row.v1",
            "model_id": MODEL_ID,
            "acceptance_limit_sec": float(ACCEPTANCE_LIMIT_SEC),
            "column_provenance": COLUMN_PROVENANCE,
            "spprc_engine_source": SPPRC_ENGINE_SOURCE,
            "spprc_engine_build_hash": spprc_engine_build_hash(),
            "spprc_worker_mode": SPPRC_WORKER_MODE,
            "spprc_exact_mode": SPPRC_EXACT_MODE,
            "spprc_ng_sizes": list(ng_sizes),
            "spprc_ng_size_final": int(ng_sizes[-1]),
            "spprc_dssr_iterations": len(ng_sizes),
            "spprc_worker_negative_batch_early_stop": bool(WORKER_NEGATIVE_BATCH_EARLY_STOP),
            "spprc_worker_negative_batch_target": int(WORKER_NEGATIVE_BATCH_TARGET),
            "spprc_worker_resource_extension_seed_enabled": bool(
                WORKER_RESOURCE_EXTENSION_SEED_ENABLED
            ),
            "spprc_worker_hard_time_cap_sec": float(WORKER_HARD_TIME_CAP_SEC),
            "spprc_active_task_set_aware_exact_harvest": bool(ACTIVE_TASK_SET_AWARE_EXACT_HARVEST),
            "spprc_active_task_set_hard_preference_limit": int(
                ACTIVE_TASK_SET_HARD_PREFERENCE_LIMIT
            ),
            "spprc_pool_early_max_rounds_per_stage": int(POOL_EARLY_MAX_ROUNDS_PER_STAGE),
            "spprc_pool_stage_batch_time_reserve_sec": float(POOL_STAGE_BATCH_TIME_RESERVE_SEC),
            "spprc_pool_tail_one_round_active_threshold": int(
                POOL_TAIL_ONE_ROUND_ACTIVE_THRESHOLD
            ),
            "spprc_pool_tail_max_rounds_per_stage": int(POOL_TAIL_MAX_ROUNDS_PER_STAGE),
            "rmp_solver": RMP_SOLVER,
            "rmp_highs_threads": int(RMP_HIGHS_THREADS),
            "spprc_adaptive_exact_harvest_schedule": [
                dict(row) for row in LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_SCHEDULE
            ],
            "spprc_worker_sec": (
                0.0
                if EXACT_FINAL_JUDGE_FIRST
                else b42._first_float(row.get("root_cg_sec")) or 0.0
            ),
            "spprc_exact_sec": b42._first_float(
                row.get("pricing_proof_sec"),
                row.get("root_pool_final_judge_history_wall_time"),
            )
            or 0.0,
            "spprc_label_count": b42._int(row.get("root_pool_active_column_count")),
            "spprc_dominance_pruned": 0,
            "spprc_exact_coverage_complete": bool(
                row.get("exact_certificate")
                and str(row.get("pricing_state") or "") == "CERTIFIED_NO_NEGATIVE"
            ),
            "spprc_global_min_rc": b42._first_float(
                row.get("global_remaining_rc_lb"),
                row.get("best_reduced_cost"),
                row.get("root_partition_best_lb"),
            ),
            "spprc_compact_milp_final_judge_official": False,
            "spprc_partition_ledger_official": False,
        }
    )
    if bool(row.get("root_partition_certified_no_negative")):
        row["certificate_leak"] = max(1, b42._int(row.get("certificate_leak")))
        row["fail_reason"] = (
            row.get("fail_reason")
            or "B4.3 forbids root partition proof from acting as official certificate"
        )
        if bool(row.get("exact_certificate")):
            row["algorithm_status"] = "BPC_INCOMPLETE_PRICING"
            row["certificate_scope"] = "DIAGNOSTIC_PRICING_FRONTIER"
            row["pricing_state"] = "INCOMPLETE_LIMIT"
            row["exact_certificate"] = False
            row["bpc_tree_optimal"] = False
    return row


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
        json.dumps(
            {
                "schema_version": "lunar_ice_bpc.b4_3_spprc_labeling_state.v1",
                "config_hash": b42._config_hash(config),
                "config": config,
                "rows": rows,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
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
    base = b42._summary(
        rows,
        config=config,
        limited_run=limited_run,
        discovered_instance_count=discovered_instance_count,
        expected_scale_counts=expected_scale_counts,
    )
    scale30_rows = [row for row in rows if int(row.get("scale") or 0) == 30]
    expected_counts = dict(expected_scale_counts or {})
    expected_scale30_count = int(expected_counts.get("30") or discovered_instance_count)
    scale30_complete = bool(not limited_run and scale30_rows and len(scale30_rows) == expected_scale30_count)
    redlines = dict(base.get("redlines") or {})
    redlines["spprc_partition_certificate_leak_count"] = sum(
        int(bool(row.get("root_partition_certified_no_negative"))) for row in rows
    )
    redlines_zero = all(b42._int(value) == 0 for value in redlines.values())
    acceptance = dict(base.get("acceptance") or {})
    acceptance.update(
        {
            "redlines_zero": bool(redlines_zero),
            "full_scale30_run_complete": bool(scale30_complete),
            "scale30_all_bpc_tree_optimal": bool(
                scale30_complete and all(row.get("certificate_scope") == "BPC_TREE_OPTIMAL" for row in scale30_rows)
            ),
            "scale30_all_under_1800": bool(
                scale30_complete and all(b42._row_under_acceptance_limit(row) for row in scale30_rows)
            ),
            "b4_3_spprc_labeling_accepted": bool(
                scale30_complete
                and len(base.get("config_hashes") or []) == 1
                and redlines_zero
                and all(
                    bool(row.get("exact_certificate")) and b42._row_under_acceptance_limit(row)
                    for row in scale30_rows
                )
            ),
        }
    )
    base.update(
        {
            "schema_version": "lunar_ice_bpc.b4_3_spprc_labeling_summary.v1",
            "redlines": redlines,
            "acceptance": acceptance,
            "spprc": {
                "engine_source": config.get("spprc_engine_source"),
                "engine_build_hash": config.get("spprc_engine_build_hash"),
                "worker_mode": config.get("spprc_worker_mode"),
                "exact_mode": config.get("spprc_exact_mode"),
                "exact_final_judge_first": bool(config.get("spprc_exact_final_judge_first")),
                "ng_sizes": config.get("spprc_ng_sizes"),
                "mean_worker_sec": b42._mean(row.get("spprc_worker_sec") for row in rows),
                "mean_exact_sec": b42._mean(row.get("spprc_exact_sec") for row in rows),
                "exact_coverage_complete_count": sum(
                    int(bool(row.get("spprc_exact_coverage_complete"))) for row in rows
                ),
            },
        }
    )
    return base


def _render_report(rows: list[dict], summary: dict) -> str:
    lines = [
        "# B4.3 SPPRC Labeling 1800s Cold-Start Report",
        "",
        "## 边界",
        "",
        "- 每个正式行必须从 `instance_XXX_logical_graph.json` 冷启动。",
        "- 禁止历史列池、mature probe、手工补列、按实例调参。",
        "- seed、worker、pricing、tree、certificate 全部计入 `cold_start_total_sec`。",
        "- `RELAXED_NG_WORKER` 只找列，不能给 no-negative 证书。",
        "- `EXACT_ELEMENTARY_PROOF` 是唯一正式 no-negative 证书路径。",
        "- B4.2 `(k,m)` partition ledger 在 B4.3 中不是 official certificate path。",
        "- `BPC_TREE_OPTIMAL` 只证明 normalized additive objective，不证明 makespan-in-objective。",
        "",
        "## 汇总",
        "",
        f"- model: `{summary.get('config', {}).get('model_id')}`",
        f"- config hash: `{summary.get('config_hash')}`",
        f"- engine: `{summary.get('spprc', {}).get('engine_source')}` / "
        f"`{summary.get('spprc', {}).get('engine_build_hash')}`",
        f"- worker/exact: `{summary.get('spprc', {}).get('worker_mode')}` / "
        f"`{summary.get('spprc', {}).get('exact_mode')}`",
        f"- exact-final-judge-first: `{summary.get('spprc', {}).get('exact_final_judge_first')}`",
        f"- ng sizes: `{summary.get('spprc', {}).get('ng_sizes')}`",
        f"- accepted: `{summary.get('acceptance', {}).get('b4_3_spprc_labeling_accepted')}`",
        f"- redlines zero: `{summary.get('acceptance', {}).get('redlines_zero')}`",
        f"- full 30 complete: `{summary.get('acceptance', {}).get('full_scale30_run_complete')}`",
        "",
        "| scale | rows | exact | under1800 exact | under300 exact | fail-closed | mean total | max total | mean SPPRC worker | mean SPPRC exact |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for scale, item in (summary.get("by_scale") or {}).items():
        scale_rows = [row for row in rows if str(row.get("scale")) == str(scale)]
        lines.append(
            f"| {scale} | {item.get('row_count')} | {item.get('exact_count')} | "
            f"{item.get('under_acceptance_limit_exact_count')} | "
            f"{item.get('under_300_exact_count')} | {item.get('fail_closed_count')} | "
            f"{item.get('mean_cold_start_total_sec')} | {item.get('max_cold_start_total_sec')} | "
            f"{b42._mean(row.get('spprc_worker_sec') for row in scale_rows)} | "
            f"{b42._mean(row.get('spprc_exact_sec') for row in scale_rows)} |"
        )
    lines.extend(
        [
            "",
            "## Per-Instance",
            "",
            "| scale | instance | scope | pricing | exact | under1800 | total | root | tree | SPPRC exact | ng | terminal | fail reason |",
            "|---:|---|---|---|---|---|---:|---:|---:|---:|---|---|---|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row.get('scale')} | {row.get('instance_key')} | {row.get('certificate_scope')} | "
            f"{row.get('pricing_state')} | {row.get('exact_certificate')} | "
            f"{row.get('under_acceptance_limit')} | {row.get('cold_start_total_sec')} | "
            f"{row.get('root_cg_sec')} | {row.get('tree_sec')} | {row.get('spprc_exact_sec')} | "
            f"{row.get('spprc_ng_sizes')} | {row.get('row_terminal')} | {row.get('fail_reason')} |"
        )
    return "\n".join(lines) + "\n"


def _enforce_resume_config(
    state: dict,
    *,
    config_hash: str,
    parser: argparse.ArgumentParser,
) -> None:
    if not state:
        return
    hashes = {
        str(row.get("config_hash") or "")
        for row in state.get("rows") or []
        if isinstance(row, dict) and row.get("config_hash")
    }
    state_hash = str(state.get("config_hash") or "")
    if state_hash:
        hashes.add(state_hash)
    hashes.discard("")
    if hashes and hashes != {str(config_hash)}:
        parser.error(
            "existing B4.3 state was produced with a different config_hash; "
            "use a fresh output directory or the exact same fixed config"
        )


def _parse_ng_sizes(value, *, max_size: int) -> tuple[int, ...]:
    seen: set[int] = set()
    sizes: list[int] = []
    raw_values = value if isinstance(value, (list, tuple)) else str(value).split(",")
    for raw in raw_values:
        try:
            size = int(str(raw).strip())
        except ValueError:
            continue
        size = max(1, min(int(max_size), size))
        if size in seen:
            continue
        seen.add(size)
        sizes.append(size)
    if not sizes:
        sizes = [int(max_size)]
    if sizes[-1] != int(max_size) and int(max_size) not in seen:
        sizes.append(int(max_size))
    return tuple(sizes)


if __name__ == "__main__":
    raise SystemExit(main())

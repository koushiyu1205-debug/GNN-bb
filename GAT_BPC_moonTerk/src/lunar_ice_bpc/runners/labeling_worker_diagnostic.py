"""Cold-start diagnostic runner for BPC labeling worker pricing.

This runner compares the existing direct worker against the relaxed/ng-route
labeling worker under the same node-pricing engine.  It is deliberately a
diagnostic worker benchmark: worker-found columns are true-dual re-audited, but
worker no-column results are never certificates.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from statistics import mean
from time import perf_counter
from typing import Iterable

from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import (
    DIRECT_LABEL_WORKER,
    RELAXED_LABELING_WORKER,
    _price_singleton_seed_columns,
    solve_node_pricing_with_b2b_r3,
)
from lunar_ice_bpc.exact.bpc.core.column_signature import column_signature_from_journey
from lunar_ice_bpc.exact.bpc.pricing.labeling_pricer import (
    RELAXED_NG_ROUTE_MODE,
    LabelingPricingConfig,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.core.journey import JourneyColumn
from lunar_ice_bpc.exact.solver.journey_driver import _reference_solution_upper_bound
from lunar_ice_bpc.io.instance_io import read_json


LABELING_WORKER_DIAGNOSTIC_SCHEMA_VERSION = "lunar_ice_bpc.labeling_worker_diagnostic.v1"
DEFAULT_WORKERS = (DIRECT_LABEL_WORKER, RELAXED_LABELING_WORKER)

CSV_COLUMNS = (
    "schema_version",
    "config_hash",
    "scale",
    "instance_id",
    "instance_path",
    "worker_pricer_kind",
    "labeling_worker_enabled",
    "labeling_algorithm",
    "resource_label_algorithm",
    "resource_label_core_mode",
    "resource_dimensions",
    "dominance_policy",
    "elementarity_policy",
    "task_count",
    "max_tasks_per_trip",
    "worker_task_cap",
    "seed_builder",
    "seed_column_count",
    "seed_wall_time_sec",
    "column_provenance",
    "max_rounds",
    "max_columns_per_round",
    "row_time_limit_sec",
    "tail_dual_stabilization_enabled",
    "algorithm_status",
    "certificate_scope",
    "pricing_state",
    "node_status",
    "uses_true_dual_bpc_certificate",
    "node_lp_bound_official",
    "worker_can_certify_no_negative",
    "worker_uses_true_dual_bpc_certificate",
    "worker_root_lp_bound_official",
    "worker_certificate_leak",
    "pricing_proof_kind",
    "completion_bound_pruning_enabled",
    "completion_bound_evaluated_label_count",
    "completion_bound_pruned_label_count",
    "completion_bound_can_certify_no_negative",
    "bound_prune_count",
    "worker_generated_count",
    "worker_candidate_budget",
    "task_bound_pruned_count",
    "resource_bound_pruned_count",
    "dominance_filtered_count",
    "duplicate_filtered_count",
    "pricing_timeout",
    "refinement_seed_count",
    "active_refinement_seed_count",
    "refinement_expanded_seed_count",
    "active_refinement_expanded_seed_count",
    "refinement_seed_source",
    "refinement_seed_mutates_certificate",
    "global_remaining_rc_lb",
    "global_remaining_rc_lb_valid",
    "global_remaining_rc_lb_coverage_complete",
    "frontier_region_count",
    "frontier_unsupported_region_count",
    "frontier_unsupported_task_count_regions",
    "branch_context_audit_pass",
    "branch_invalid_column_count",
    "manual_rc_audit_pass",
    "pricing_rc_audit_pass",
    "rmp_iteration_count",
    "pricing_round_count",
    "final_judge_call_count",
    "candidate_negative_count",
    "addable_negative_count",
    "selected_count",
    "added_to_master_count",
    "worker_status",
    "worker_exit_reason",
    "worker_wall_time",
    "final_judge_wall_time",
    "time_to_first_negative",
    "time_to_first_addable_negative",
    "candidate_task_set_count",
    "labeling_seed_task_set_count",
    "ng_seed_task_set_count",
    "resource_extension_seed_enabled",
    "resource_extension_seed_task_set_count",
    "active_resource_extension_seed_task_set_count",
    "resource_extension_seed_task_set_count_by_size",
    "resource_extension_label_column_worker_enabled",
    "resource_extension_label_column_count",
    "resource_extension_label_column_task_set_count",
    "resource_extension_label_column_policy",
    "resource_extension_label_columns_can_certify_no_negative",
    "resource_extension_label_path_variant_candidate_count",
    "resource_extension_label_path_variant_duplicate_count",
    "resource_extension_label_path_variant_feasible_count",
    "resource_extension_label_path_variant_infeasible_count",
    "active_seed_selection_policy",
    "active_seed_task_set_source_counts",
    "active_seed_task_set_count_by_size",
    "priced_candidate_task_set_source_counts",
    "direct_candidate_task_set_count",
    "candidate_seed_source_precedence",
    "input_seed_task_set_count",
    "merged_seed_task_set_count",
    "active_seed_task_set_count",
    "active_ng_seed_task_set_count",
    "active_input_seed_task_set_count",
    "ng_neighborhood_size",
    "ng_neighborhood_sizes",
    "ng_neighborhood_stage_count",
    "ng_seed_task_set_count_by_size",
    "labels_generated_total",
    "labels_extended",
    "journey_labels",
    "true_dual_audited_column_count",
    "true_dual_selected_negative_count",
    "candidate_search_best_reduced_cost",
    "candidate_search_negative_column_count",
    "candidate_search_negative_true_negative_count",
    "candidate_search_negative_true_nonnegative_count",
    "true_negative_candidate_search_nonnegative_count",
    "candidate_search_dual_matches_true_dual",
    "candidate_search_rc_recomputed_under_true_dual",
    "worker_true_dual_candidate_audit_pass",
    "candidate_search_false_positive_rate",
    "true_negative_candidate_search_miss_rate",
    "candidate_search_false_positive_rows",
    "true_negative_candidate_search_miss_rows",
    "worker_candidate_universe_task_set_count",
    "worker_generated_column_task_set_count",
    "worker_candidate_universe_task_sets",
    "worker_generated_column_task_sets",
    "labeling_harvest_candidate_negative_count",
    "labeling_harvest_candidate_new_task_set_count",
    "labeling_harvest_candidate_replacement_task_set_count",
    "labeling_harvest_candidate_support_changing_count",
    "labeling_harvest_candidate_strong_replacement_count",
    "labeling_harvest_candidate_weak_replacement_count",
    "labeling_harvest_selected_count",
    "labeling_harvest_selected_new_task_set_count",
    "labeling_harvest_selected_replacement_task_set_count",
    "labeling_harvest_selected_support_changing_count",
    "labeling_harvest_selected_strong_replacement_count",
    "labeling_harvest_selected_weak_replacement_count",
    "labeling_harvest_selected_distinct_task_set_count",
    "labeling_harvest_selected_duplicate_task_set_count",
    "labeling_harvest_existing_master_task_set_count",
    "labeling_harvest_support_task_set_count",
    "labeling_harvest_support_aware_enabled",
    "labeling_harvest_weak_replacement_cap",
    "labeling_harvest_selection_policy",
    "labeling_harvest_avg_pairwise_jaccard",
    "labeling_harvest_max_pairwise_jaccard",
    "labeling_harvest_candidate_seed_source_counts",
    "labeling_harvest_selected_seed_source_counts",
    "labeling_no_column_uncertified",
    "diagnostic_dual_source",
    "worker_dual_source",
    "official_dual_source",
    "worker_dual_only",
    "true_dual_rc_recomputed",
    "tail_dual_no_column_can_certify",
    "tail_dual_certificate_leak",
    "true_dual_rc_recompute_missing",
    "wall_time_sec",
    "fail_closed_reason",
    "note",
)


def run_labeling_worker_diagnostic(
    instance_paths: Iterable[str | Path],
    *,
    project_root: str | Path,
    workers: Iterable[str] = DEFAULT_WORKERS,
    max_rounds: int = 1,
    max_columns_per_round: int = 16,
    row_time_limit_sec: float | None = 30.0,
    tail_dual_stabilization_enabled: bool = False,
    tail_dual_stabilization_alpha: float = 0.7,
    tail_dual_stabilization_window: int = 5,
) -> dict:
    project_root = Path(project_root)
    selected_workers = tuple(_normalize_worker(worker) for worker in workers)
    config = {
        "schema_version": LABELING_WORKER_DIAGNOSTIC_SCHEMA_VERSION,
        "runner": "labeling_worker_diagnostic",
        "model_id": "LABELING_WORKER_MULTI_NG_V1",
        "workers": selected_workers,
        "relaxed_ng_route_worker_config": _default_relaxed_worker_config_payload(),
        "max_rounds": int(max_rounds),
        "max_columns_per_round": int(max_columns_per_round),
        "row_time_limit_sec": row_time_limit_sec,
        "tail_dual_stabilization_enabled": bool(tail_dual_stabilization_enabled),
        "tail_dual_stabilization_alpha": float(tail_dual_stabilization_alpha),
        "tail_dual_stabilization_window": int(tail_dual_stabilization_window),
        "seed_builder": "instance_json_reference_repair_plus_singletons",
        "column_provenance": "instance_json_reference_repair_plus_singletons_no_history_no_b0_no_probe",
        "certificate_boundary": (
            "worker candidate search only; true-dual addability audit is required; "
            "worker no-column is not a no-negative certificate"
        ),
    }
    config_hash = _config_hash(config)
    rows: list[dict] = []
    for raw_path in instance_paths:
        instance_path = Path(raw_path)
        if not instance_path.is_absolute():
            instance_path = project_root / instance_path
        instance = read_json(instance_path)
        data = load_lunar_ice_data(instance)
        seed_started = perf_counter()
        seed_columns, seed_report = _build_instance_json_seed_columns(data)
        seed_wall_time = perf_counter() - seed_started
        for worker in selected_workers:
            started_at = perf_counter()
            result = solve_node_pricing_with_b2b_r3(
                data,
                node_id=f"labeling-worker-diagnostic-{worker}",
                initial_columns=seed_columns,
                b0_direct=None,
                max_direct_tasks=len(data.task_ids),
                max_rounds=max_rounds,
                wall_time_limit_sec=row_time_limit_sec,
                max_columns_per_round=max_columns_per_round,
                tail_dual_stabilization_enabled=tail_dual_stabilization_enabled,
                tail_dual_stabilization_alpha=tail_dual_stabilization_alpha,
                tail_dual_stabilization_window=tail_dual_stabilization_window,
                worker_pricer_kind=worker,
            )
            wall_time = perf_counter() - started_at
            row = _row_from_result(
                result,
                data=data,
                instance_path=instance_path,
                worker=worker,
                config_hash=config_hash,
                seed_column_count=len(seed_columns),
                seed_report=seed_report,
                seed_wall_time=seed_wall_time,
                max_rounds=max_rounds,
                max_columns_per_round=max_columns_per_round,
                row_time_limit_sec=row_time_limit_sec,
                tail_dual_stabilization_enabled=tail_dual_stabilization_enabled,
                wall_time=wall_time,
            )
            rows.append(row)
    return _report_from_rows(rows, config=config, config_hash=config_hash)


def write_labeling_worker_diagnostic_artifacts(
    report: dict,
    *,
    rows_csv: str | Path,
    summary_json: str | Path,
    report_md: str | Path,
) -> None:
    rows_csv = Path(rows_csv)
    summary_json = Path(summary_json)
    report_md = Path(report_md)
    rows_csv.parent.mkdir(parents=True, exist_ok=True)
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    report_md.parent.mkdir(parents=True, exist_ok=True)
    with rows_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in report["rows"]:
            writer.writerow({key: _csv_value(row.get(key)) for key in CSV_COLUMNS})
    summary_json.write_text(
        json.dumps(_json_safe(report), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_md.write_text(
        render_labeling_worker_diagnostic_markdown(report, rows_csv=rows_csv, summary_json=summary_json),
        encoding="utf-8",
    )


def render_labeling_worker_diagnostic_markdown(
    report: dict,
    *,
    rows_csv: str | Path,
    summary_json: str | Path,
) -> str:
    lines = [
        "# BPC Labeling Worker 诊断报告",
        "",
        "## 口径",
        "",
        "- 每个 row 从 instance JSON 自动生成 reference-repair + singleton seed。",
        "- 禁止历史列池、成熟 probe、手工补列；本报告只比较 worker 找列能力。",
        "- direct_label 与 relaxed_labeling 共用同一个 B2B_R3 node pricing engine。",
        "- worker 找到的列必须用 current true RMP dual 复算 reduced cost。",
        "- worker no-column 不能升级为 no-negative certificate。",
        "",
        "## Artifacts",
        "",
        f"- CSV rows: `{rows_csv}`",
        f"- JSON summary: `{summary_json}`",
        "",
        "## Summary",
        "",
        f"- row_count: {report['row_count']}",
        f"- config_hash: `{report['config_hash']}`",
        "",
        "| scale | worker | rows | found addable | mean added | mean label cols | mean path variants | mean selected | mean new task-set | mean support-changing | mean strong repl | mean weak repl | mean replacement | mean harvest Jaccard | worker cert leaks | tail-dual leaks | RC recompute missing | mean false+ | mean miss | false+ rows | miss rows | mean worker sec | mean wall sec | final judge calls |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["summary_rows"]:
        lines.append(
            "| {scale} | {worker_pricer_kind} | {row_count} | {found_addable_count} | {mean_added_to_master:.3f} | "
            "{mean_resource_extension_label_column_count:.3f} | "
            "{mean_resource_extension_label_path_variant_candidate_count:.3f} | "
            "{mean_labeling_harvest_selected_count:.3f} | {mean_labeling_harvest_selected_new_task_set_count:.3f} | "
            "{mean_labeling_harvest_selected_support_changing_count:.3f} | "
            "{mean_labeling_harvest_selected_strong_replacement_count:.3f} | "
            "{mean_labeling_harvest_selected_weak_replacement_count:.3f} | "
            "{mean_labeling_harvest_selected_replacement_task_set_count:.3f} | "
            "{mean_labeling_harvest_avg_pairwise_jaccard:.3f} | "
            "{worker_certificate_leak_count} | {tail_dual_certificate_leak_count} | {true_dual_rc_recompute_missing_count} | "
            "{mean_candidate_search_false_positive_rate:.3f} | {mean_true_negative_candidate_search_miss_rate:.3f} | "
            "{candidate_search_false_positive_row_count} | {true_negative_candidate_search_miss_row_count} | "
            "{mean_worker_wall_time:.3f} | {mean_wall_time_sec:.3f} | {final_judge_call_count} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## 证书边界",
            "",
            "- `uses_true_dual_bpc_certificate=true` 只允许来自 exact final proof；worker 行默认不应出现。",
            "- `labeling_no_column_uncertified=true` 表示 worker 没找到列，但不能证明无负列。",
            "- 这份报告用于判断 relaxed/ng-route worker 是否值得接入 B4.2，不是 30-scale exact closure 报告。",
            "",
            "## Rows",
            "",
            "| scale | instance | worker | status | scope | pricing | seed policy | harvest policy | label cols | path variants | added | selected | new task-set | support-changing | strong repl | weak repl | replacement | worker sec | wall sec | note |",
            "|---:|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in report["rows"]:
        lines.append(
            "| {scale} | {instance_id} | {worker_pricer_kind} | {algorithm_status} | {certificate_scope} | "
            "{pricing_state} | {active_seed_selection_policy} | {labeling_harvest_selection_policy} | "
            "{resource_extension_label_column_count} | {resource_extension_label_path_variant_candidate_count} | "
            "{added_to_master_count} | {labeling_harvest_selected_count} | "
            "{labeling_harvest_selected_new_task_set_count} | "
            "{labeling_harvest_selected_support_changing_count} | "
            "{labeling_harvest_selected_strong_replacement_count} | "
            "{labeling_harvest_selected_weak_replacement_count} | "
            "{labeling_harvest_selected_replacement_task_set_count} | "
            "{worker_wall_time} | {wall_time_sec} | {note} |".format(
                **{**row, "note": _markdown_cell(str(row.get("note") or ""))}
            )
        )
    return "\n".join(lines) + "\n"


def _row_from_result(
    result: dict,
    *,
    data,
    instance_path: Path,
    worker: str,
    config_hash: str,
    seed_column_count: int,
    seed_report: dict,
    seed_wall_time: float,
    max_rounds: int,
    max_columns_per_round: int,
    row_time_limit_sec: float | None,
    tail_dual_stabilization_enabled: bool,
    wall_time: float,
) -> dict:
    history = result.get("history") or []
    first_worker = next((row for row in history if row.get("worker_pricer_kind")), {})
    worker_can_certify = bool(first_worker.get("can_certify_no_negative"))
    worker_uses_true_dual = bool(first_worker.get("uses_true_dual_bpc_certificate"))
    worker_root_lp_bound_official = bool(first_worker.get("root_lp_bound_official"))
    completion_bound_certifies = bool(first_worker.get("completion_bound_can_certify_no_negative"))
    tail_dual_no_column_can_certify = bool(first_worker.get("tail_dual_no_column_can_certify"))
    worker_certificate_leak = bool(
        worker_can_certify
        or worker_uses_true_dual
        or worker_root_lp_bound_official
        or completion_bound_certifies
        or tail_dual_no_column_can_certify
    )
    true_dual_rc_recomputed = bool(first_worker.get("true_dual_rc_recomputed"))
    worker_dual_only = bool(first_worker.get("worker_dual_only"))
    official_dual_source = str(first_worker.get("official_dual_source") or "")
    tail_dual_active = bool(tail_dual_stabilization_enabled)
    true_dual_rc_recompute_missing = bool(
        tail_dual_active and first_worker and not true_dual_rc_recomputed
    )
    tail_dual_certificate_leak = bool(
        tail_dual_active
        and (
            worker_certificate_leak
            or tail_dual_no_column_can_certify
            or (first_worker and not worker_dual_only)
            or true_dual_rc_recompute_missing
            or (
                bool(first_worker)
                and official_dual_source not in {"", "current_true_rmp_dual"}
            )
        )
    )
    return {
        "schema_version": LABELING_WORKER_DIAGNOSTIC_SCHEMA_VERSION,
        "config_hash": config_hash,
        "scale": int(data.scale),
        "instance_id": str(data.instance_id),
        "instance_path": str(instance_path),
        "worker_pricer_kind": worker,
        "labeling_worker_enabled": bool(first_worker.get("labeling_worker_enabled")),
        "labeling_algorithm": first_worker.get("labeling_algorithm") or "",
        "resource_label_algorithm": first_worker.get("resource_label_algorithm") or "",
        "resource_label_core_mode": first_worker.get("resource_label_core_mode") or "",
        "resource_dimensions": first_worker.get("resource_dimensions") or [],
        "dominance_policy": first_worker.get("dominance_policy") or "",
        "elementarity_policy": first_worker.get("elementarity_policy") or "",
        "task_count": len(data.task_ids),
        "max_tasks_per_trip": int(data.max_tasks_per_trip),
        "worker_task_cap": first_worker.get("worker_task_cap"),
        "seed_builder": seed_report.get("seed_builder") or "instance_json_reference_repair_plus_singletons",
        "seed_column_count": int(seed_column_count),
        "seed_wall_time_sec": round(float(seed_wall_time), 6),
        "column_provenance": seed_report.get("column_provenance")
        or "instance_json_reference_repair_plus_singletons_no_history_no_b0_no_probe",
        "max_rounds": int(max_rounds),
        "max_columns_per_round": int(max_columns_per_round),
        "row_time_limit_sec": row_time_limit_sec,
        "tail_dual_stabilization_enabled": bool(tail_dual_stabilization_enabled),
        "algorithm_status": result.get("algorithm_status"),
        "certificate_scope": result.get("certificate_scope"),
        "pricing_state": result.get("pricing_state"),
        "node_status": result.get("node_status"),
        "uses_true_dual_bpc_certificate": bool(result.get("uses_true_dual_bpc_certificate")),
        "node_lp_bound_official": bool(result.get("node_lp_bound_official")),
        "worker_can_certify_no_negative": worker_can_certify,
        "worker_uses_true_dual_bpc_certificate": worker_uses_true_dual,
        "worker_root_lp_bound_official": worker_root_lp_bound_official,
        "worker_certificate_leak": worker_certificate_leak,
        "pricing_proof_kind": first_worker.get("pricing_proof_kind") or (result.get("final_judge") or {}).get("pricing_proof_kind") or "",
        "completion_bound_pruning_enabled": first_worker.get("completion_bound_pruning_enabled"),
        "completion_bound_evaluated_label_count": first_worker.get("completion_bound_evaluated_label_count"),
        "completion_bound_pruned_label_count": first_worker.get("completion_bound_pruned_label_count"),
        "completion_bound_can_certify_no_negative": first_worker.get(
            "completion_bound_can_certify_no_negative"
        ),
        "bound_prune_count": first_worker.get("bound_prune_count"),
        "worker_generated_count": first_worker.get("worker_generated_count"),
        "worker_candidate_budget": first_worker.get("worker_candidate_budget"),
        "task_bound_pruned_count": first_worker.get("task_bound_pruned_count"),
        "resource_bound_pruned_count": first_worker.get("resource_bound_pruned_count"),
        "dominance_filtered_count": first_worker.get("dominance_filtered_count"),
        "duplicate_filtered_count": first_worker.get("duplicate_filtered_count"),
        "pricing_timeout": first_worker.get("pricing_timeout"),
        "refinement_seed_count": first_worker.get("refinement_seed_count"),
        "active_refinement_seed_count": first_worker.get("active_refinement_seed_count"),
        "refinement_expanded_seed_count": first_worker.get("refinement_expanded_seed_count"),
        "active_refinement_expanded_seed_count": first_worker.get(
            "active_refinement_expanded_seed_count"
        ),
        "refinement_seed_source": first_worker.get("refinement_seed_source"),
        "refinement_seed_mutates_certificate": first_worker.get("refinement_seed_mutates_certificate"),
        "global_remaining_rc_lb": first_worker.get("global_remaining_rc_lb")
        or (result.get("final_judge") or {}).get("global_remaining_rc_lb"),
        "global_remaining_rc_lb_valid": first_worker.get("global_remaining_rc_lb_valid")
        if first_worker.get("global_remaining_rc_lb_valid") is not None
        else (result.get("final_judge") or {}).get("global_remaining_rc_lb_valid"),
        "global_remaining_rc_lb_coverage_complete": first_worker.get("global_remaining_rc_lb_coverage_complete")
        if first_worker.get("global_remaining_rc_lb_coverage_complete") is not None
        else (result.get("final_judge") or {}).get("global_remaining_rc_lb_coverage_complete"),
        "frontier_region_count": first_worker.get("frontier_region_count")
        if first_worker.get("frontier_region_count") is not None
        else (result.get("final_judge") or {}).get("frontier_region_count"),
        "frontier_unsupported_region_count": first_worker.get("frontier_unsupported_region_count")
        if first_worker.get("frontier_unsupported_region_count") is not None
        else (result.get("final_judge") or {}).get("frontier_unsupported_region_count"),
        "frontier_unsupported_task_count_regions": first_worker.get(
            "frontier_unsupported_task_count_regions"
        )
        or (result.get("final_judge") or {}).get("frontier_unsupported_task_count_regions")
        or [],
        "branch_context_audit_pass": first_worker.get("branch_context_audit_pass"),
        "branch_invalid_column_count": first_worker.get("branch_invalid_column_count"),
        "manual_rc_audit_pass": result.get("manual_rc_audit_pass"),
        "pricing_rc_audit_pass": result.get("pricing_rc_audit_pass"),
        "rmp_iteration_count": result.get("rmp_iteration_count"),
        "pricing_round_count": result.get("pricing_round_count"),
        "final_judge_call_count": result.get("final_judge_call_count"),
        "candidate_negative_count": result.get("candidate_negative_count"),
        "addable_negative_count": result.get("addable_negative_count"),
        "selected_count": result.get("selected_count"),
        "added_to_master_count": result.get("added_to_master_count"),
        "worker_status": first_worker.get("worker_status"),
        "worker_exit_reason": first_worker.get("worker_exit_reason"),
        "worker_wall_time": first_worker.get("worker_wall_time"),
        "final_judge_wall_time": result.get("final_judge_wall_time"),
        "time_to_first_negative": first_worker.get("time_to_first_negative"),
        "time_to_first_addable_negative": first_worker.get("time_to_first_addable_negative"),
        "candidate_task_set_count": first_worker.get("candidate_task_set_count"),
        "labeling_seed_task_set_count": first_worker.get("labeling_seed_task_set_count"),
        "ng_seed_task_set_count": first_worker.get("ng_seed_task_set_count"),
        "resource_extension_seed_enabled": first_worker.get("resource_extension_seed_enabled"),
        "resource_extension_seed_task_set_count": first_worker.get(
            "resource_extension_seed_task_set_count"
        ),
        "active_resource_extension_seed_task_set_count": first_worker.get(
            "active_resource_extension_seed_task_set_count"
        ),
        "resource_extension_seed_task_set_count_by_size": first_worker.get(
            "resource_extension_seed_task_set_count_by_size"
        ),
        "resource_extension_label_column_worker_enabled": first_worker.get(
            "resource_extension_label_column_worker_enabled"
        ),
        "resource_extension_label_column_count": first_worker.get(
            "resource_extension_label_column_count"
        ),
        "resource_extension_label_column_task_set_count": first_worker.get(
            "resource_extension_label_column_task_set_count"
        ),
        "resource_extension_label_column_policy": first_worker.get(
            "resource_extension_label_column_policy"
        )
        or "",
        "resource_extension_label_columns_can_certify_no_negative": first_worker.get(
            "resource_extension_label_columns_can_certify_no_negative"
        ),
        "resource_extension_label_path_variant_candidate_count": first_worker.get(
            "resource_extension_label_path_variant_candidate_count"
        ),
        "resource_extension_label_path_variant_duplicate_count": first_worker.get(
            "resource_extension_label_path_variant_duplicate_count"
        ),
        "resource_extension_label_path_variant_feasible_count": first_worker.get(
            "resource_extension_label_path_variant_feasible_count"
        ),
        "resource_extension_label_path_variant_infeasible_count": first_worker.get(
            "resource_extension_label_path_variant_infeasible_count"
        ),
        "active_seed_selection_policy": first_worker.get("active_seed_selection_policy") or "",
        "active_seed_task_set_source_counts": first_worker.get("active_seed_task_set_source_counts") or {},
        "active_seed_task_set_count_by_size": first_worker.get("active_seed_task_set_count_by_size") or {},
        "priced_candidate_task_set_source_counts": first_worker.get(
            "priced_candidate_task_set_source_counts"
        )
        or {},
        "direct_candidate_task_set_count": first_worker.get("direct_candidate_task_set_count"),
        "candidate_seed_source_precedence": first_worker.get("candidate_seed_source_precedence") or [],
        "input_seed_task_set_count": first_worker.get("input_seed_task_set_count"),
        "merged_seed_task_set_count": first_worker.get("merged_seed_task_set_count"),
        "active_seed_task_set_count": first_worker.get("active_seed_task_set_count"),
        "active_ng_seed_task_set_count": first_worker.get("active_ng_seed_task_set_count"),
        "active_input_seed_task_set_count": first_worker.get("active_input_seed_task_set_count"),
        "ng_neighborhood_size": first_worker.get("ng_neighborhood_size"),
        "ng_neighborhood_sizes": first_worker.get("ng_neighborhood_sizes") or [],
        "ng_neighborhood_stage_count": first_worker.get("ng_neighborhood_stage_count"),
        "ng_seed_task_set_count_by_size": first_worker.get("ng_seed_task_set_count_by_size") or {},
        "labels_generated_total": first_worker.get("labels_generated_total"),
        "labels_extended": first_worker.get("labels_extended"),
        "journey_labels": first_worker.get("journey_labels"),
        "true_dual_audited_column_count": first_worker.get("true_dual_audited_column_count"),
        "true_dual_selected_negative_count": first_worker.get("true_dual_selected_negative_count"),
        "candidate_search_best_reduced_cost": first_worker.get("candidate_search_best_reduced_cost"),
        "candidate_search_negative_column_count": first_worker.get("candidate_search_negative_column_count"),
        "candidate_search_negative_true_negative_count": first_worker.get(
            "candidate_search_negative_true_negative_count"
        ),
        "candidate_search_negative_true_nonnegative_count": first_worker.get(
            "candidate_search_negative_true_nonnegative_count"
        ),
        "true_negative_candidate_search_nonnegative_count": first_worker.get(
            "true_negative_candidate_search_nonnegative_count"
        ),
        "candidate_search_dual_matches_true_dual": first_worker.get(
            "candidate_search_dual_matches_true_dual"
        ),
        "candidate_search_rc_recomputed_under_true_dual": first_worker.get(
            "candidate_search_rc_recomputed_under_true_dual"
        ),
        "worker_true_dual_candidate_audit_pass": first_worker.get(
            "worker_true_dual_candidate_audit_pass"
        ),
        "candidate_search_false_positive_rate": first_worker.get("candidate_search_false_positive_rate"),
        "true_negative_candidate_search_miss_rate": first_worker.get(
            "true_negative_candidate_search_miss_rate"
        ),
        "candidate_search_false_positive_rows": first_worker.get("candidate_search_false_positive_rows") or [],
        "true_negative_candidate_search_miss_rows": first_worker.get(
            "true_negative_candidate_search_miss_rows"
        )
        or [],
        "worker_candidate_universe_task_set_count": len(
            first_worker.get("worker_candidate_universe_task_sets") or []
        ),
        "worker_generated_column_task_set_count": first_worker.get(
            "worker_generated_column_task_set_count"
        ),
        "worker_candidate_universe_task_sets": first_worker.get("worker_candidate_universe_task_sets") or [],
        "worker_generated_column_task_sets": first_worker.get("worker_generated_column_task_sets") or [],
        "labeling_harvest_candidate_negative_count": first_worker.get(
            "labeling_harvest_candidate_negative_count"
        ),
        "labeling_harvest_candidate_new_task_set_count": first_worker.get(
            "labeling_harvest_candidate_new_task_set_count"
        ),
        "labeling_harvest_candidate_replacement_task_set_count": first_worker.get(
            "labeling_harvest_candidate_replacement_task_set_count"
        ),
        "labeling_harvest_candidate_support_changing_count": first_worker.get(
            "labeling_harvest_candidate_support_changing_count"
        ),
        "labeling_harvest_candidate_strong_replacement_count": first_worker.get(
            "labeling_harvest_candidate_strong_replacement_count"
        ),
        "labeling_harvest_candidate_weak_replacement_count": first_worker.get(
            "labeling_harvest_candidate_weak_replacement_count"
        ),
        "labeling_harvest_selected_count": first_worker.get("labeling_harvest_selected_count"),
        "labeling_harvest_selected_new_task_set_count": first_worker.get(
            "labeling_harvest_selected_new_task_set_count"
        ),
        "labeling_harvest_selected_replacement_task_set_count": first_worker.get(
            "labeling_harvest_selected_replacement_task_set_count"
        ),
        "labeling_harvest_selected_support_changing_count": first_worker.get(
            "labeling_harvest_selected_support_changing_count"
        ),
        "labeling_harvest_selected_strong_replacement_count": first_worker.get(
            "labeling_harvest_selected_strong_replacement_count"
        ),
        "labeling_harvest_selected_weak_replacement_count": first_worker.get(
            "labeling_harvest_selected_weak_replacement_count"
        ),
        "labeling_harvest_selected_distinct_task_set_count": first_worker.get(
            "labeling_harvest_selected_distinct_task_set_count"
        ),
        "labeling_harvest_selected_duplicate_task_set_count": first_worker.get(
            "labeling_harvest_selected_duplicate_task_set_count"
        ),
        "labeling_harvest_existing_master_task_set_count": first_worker.get(
            "labeling_harvest_existing_master_task_set_count"
        ),
        "labeling_harvest_support_task_set_count": first_worker.get(
            "labeling_harvest_support_task_set_count"
        ),
        "labeling_harvest_support_aware_enabled": first_worker.get(
            "labeling_harvest_support_aware_enabled"
        ),
        "labeling_harvest_weak_replacement_cap": first_worker.get(
            "labeling_harvest_weak_replacement_cap"
        ),
        "labeling_harvest_selection_policy": first_worker.get("labeling_harvest_selection_policy") or "",
        "labeling_harvest_avg_pairwise_jaccard": first_worker.get("labeling_harvest_avg_pairwise_jaccard"),
        "labeling_harvest_max_pairwise_jaccard": first_worker.get("labeling_harvest_max_pairwise_jaccard"),
        "labeling_harvest_candidate_seed_source_counts": first_worker.get(
            "labeling_harvest_candidate_seed_source_counts"
        )
        or {},
        "labeling_harvest_selected_seed_source_counts": first_worker.get(
            "labeling_harvest_selected_seed_source_counts"
        )
        or {},
        "labeling_no_column_uncertified": first_worker.get("labeling_no_column_uncertified"),
        "diagnostic_dual_source": first_worker.get("diagnostic_dual_source"),
        "worker_dual_source": first_worker.get("worker_dual_source"),
        "official_dual_source": official_dual_source,
        "worker_dual_only": worker_dual_only,
        "true_dual_rc_recomputed": true_dual_rc_recomputed,
        "tail_dual_no_column_can_certify": tail_dual_no_column_can_certify,
        "tail_dual_certificate_leak": tail_dual_certificate_leak,
        "true_dual_rc_recompute_missing": true_dual_rc_recompute_missing,
        "wall_time_sec": round(float(wall_time), 6),
        "fail_closed_reason": result.get("fail_closed_reason") or "",
        "note": result.get("note") or "",
    }


def _build_instance_json_seed_columns(data) -> tuple[tuple[JourneyColumn, ...], dict]:
    columns: list[JourneyColumn] = []
    reference = _reference_solution_upper_bound(data)
    if reference is not None:
        columns.extend(reference.journeys)
    singleton_columns = _price_singleton_seed_columns(data)
    columns.extend(singleton_columns)
    deduped = _dedupe_journey_columns(columns)
    return deduped, {
        "seed_builder": "instance_json_reference_repair_plus_singletons",
        "column_provenance": "instance_json_reference_repair_plus_singletons_no_history_no_b0_no_probe",
        "reference_seed_column_count": 0 if reference is None else len(reference.journeys),
        "singleton_seed_column_count": len(singleton_columns),
        "seed_column_count": len(deduped),
        "reference_solution_source": "" if reference is None else reference.source,
    }


def _dedupe_journey_columns(columns: Iterable[JourneyColumn]) -> tuple[JourneyColumn, ...]:
    unique: list[JourneyColumn] = []
    seen = set()
    for column in columns:
        signature = column_signature_from_journey(column)
        if signature in seen:
            continue
        seen.add(signature)
        unique.append(column)
    return tuple(unique)


def _report_from_rows(rows: list[dict], *, config: dict, config_hash: str) -> dict:
    summary_rows = []
    keys = sorted({(int(row["scale"]), str(row["worker_pricer_kind"])) for row in rows})
    for scale, worker in keys:
        group = [row for row in rows if int(row["scale"]) == scale and str(row["worker_pricer_kind"]) == worker]
        summary_rows.append(
            {
                "scale": scale,
                "worker_pricer_kind": worker,
                "row_count": len(group),
                "found_addable_count": sum(1 for row in group if int(row.get("added_to_master_count") or 0) > 0),
                "mean_added_to_master": _mean(row.get("added_to_master_count") for row in group),
                "mean_resource_extension_label_column_count": _mean(
                    row.get("resource_extension_label_column_count") for row in group
                ),
                "mean_resource_extension_label_path_variant_candidate_count": _mean(
                    row.get("resource_extension_label_path_variant_candidate_count") for row in group
                ),
                "mean_labeling_harvest_selected_count": _mean(
                    row.get("labeling_harvest_selected_count") for row in group
                ),
                "mean_labeling_harvest_selected_new_task_set_count": _mean(
                    row.get("labeling_harvest_selected_new_task_set_count") for row in group
                ),
                "mean_labeling_harvest_selected_support_changing_count": _mean(
                    row.get("labeling_harvest_selected_support_changing_count") for row in group
                ),
                "mean_labeling_harvest_selected_strong_replacement_count": _mean(
                    row.get("labeling_harvest_selected_strong_replacement_count") for row in group
                ),
                "mean_labeling_harvest_selected_weak_replacement_count": _mean(
                    row.get("labeling_harvest_selected_weak_replacement_count") for row in group
                ),
                "mean_labeling_harvest_selected_replacement_task_set_count": _mean(
                    row.get("labeling_harvest_selected_replacement_task_set_count") for row in group
                ),
                "mean_labeling_harvest_avg_pairwise_jaccard": _mean(
                    row.get("labeling_harvest_avg_pairwise_jaccard") for row in group
                ),
                "mean_labeling_harvest_max_pairwise_jaccard": _mean(
                    row.get("labeling_harvest_max_pairwise_jaccard") for row in group
                ),
                "active_seed_selection_policies": sorted(
                    {
                        str(row.get("active_seed_selection_policy") or "")
                        for row in group
                        if row.get("active_seed_selection_policy")
                    }
                ),
                "labeling_harvest_selection_policies": sorted(
                    {
                        str(row.get("labeling_harvest_selection_policy") or "")
                        for row in group
                        if row.get("labeling_harvest_selection_policy")
                    }
                ),
                "worker_certificate_leak_count": sum(
                    1 for row in group if bool(row.get("worker_certificate_leak"))
                ),
                "tail_dual_certificate_leak_count": sum(
                    1 for row in group if bool(row.get("tail_dual_certificate_leak"))
                ),
                "true_dual_rc_recompute_missing_count": sum(
                    1 for row in group if bool(row.get("true_dual_rc_recompute_missing"))
                ),
                "mean_candidate_search_false_positive_rate": _mean(
                    row.get("candidate_search_false_positive_rate") for row in group
                ),
                "mean_true_negative_candidate_search_miss_rate": _mean(
                    row.get("true_negative_candidate_search_miss_rate") for row in group
                ),
                "candidate_search_false_positive_row_count": sum(
                    len(row.get("candidate_search_false_positive_rows") or []) for row in group
                ),
                "true_negative_candidate_search_miss_row_count": sum(
                    len(row.get("true_negative_candidate_search_miss_rows") or []) for row in group
                ),
                "mean_worker_wall_time": _mean(row.get("worker_wall_time") for row in group),
                "mean_wall_time_sec": _mean(row.get("wall_time_sec") for row in group),
                "final_judge_call_count": sum(int(row.get("final_judge_call_count") or 0) for row in group),
            }
        )
    return {
        "schema_version": LABELING_WORKER_DIAGNOSTIC_SCHEMA_VERSION,
        "config": config,
        "config_hash": config_hash,
        "row_count": len(rows),
        "rows": rows,
        "summary_rows": summary_rows,
        "certificate_boundary": config["certificate_boundary"],
    }


def _normalize_worker(value: str) -> str:
    normalized = str(value).strip().lower()
    if normalized in {"direct", "direct_label"}:
        return DIRECT_LABEL_WORKER
    if normalized in {"label", "labeling", "relaxed_labeling", "ng", "ng_route", "relaxed_ng_route"}:
        return RELAXED_LABELING_WORKER
    raise ValueError(f"unsupported worker {value!r}")


def _default_relaxed_worker_config_payload() -> dict:
    cfg = LabelingPricingConfig(mode=RELAXED_NG_ROUTE_MODE)
    return {
        "mode": cfg.mode,
        "max_label_task_count": cfg.max_label_task_count,
        "max_candidate_sets": cfg.max_candidate_sets,
        "harvest_target": cfg.harvest_target,
        "ng_neighborhood_size": cfg.ng_neighborhood_size,
        "ng_neighborhood_sizes": list(cfg.ng_neighborhood_sizes or ()),
        "dual_stabilization_enabled_default": cfg.dual_stabilization_enabled,
        "dual_stabilization_alpha": cfg.dual_stabilization_alpha,
        "dual_stabilization_window": cfg.dual_stabilization_window,
        "stop_at_first_negative": cfg.stop_at_first_negative,
        "support_aware_harvest_enabled": cfg.support_aware_harvest_enabled,
        "support_overlap_threshold": cfg.support_overlap_threshold,
        "max_selected_jaccard": cfg.max_selected_jaccard,
        "max_selected_containment": cfg.max_selected_containment,
        "weak_replacement_cap": cfg.weak_replacement_cap,
        "strong_replacement_threshold": cfg.strong_replacement_threshold,
        "certificate_boundary": "worker-only candidate search; no-column cannot certify",
    }


def _config_hash(config: dict) -> str:
    blob = json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _mean(values: Iterable[object]) -> float:
    parsed = [float(value) for value in values if value is not None and value != ""]
    return round(mean(parsed), 6) if parsed else 0.0


def _csv_value(value: object) -> object:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, bool):
        return int(value)
    return value


def _json_safe(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _json_safe(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(child) for child in value]
    if isinstance(value, Path):
        return str(value)
    return value


def _markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")[:180]

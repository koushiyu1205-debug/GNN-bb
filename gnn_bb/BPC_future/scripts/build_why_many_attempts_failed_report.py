"""Build a focused explanation of why recent optimization attempts failed.

This script is diagnostic-only.  It reads existing root-cause summaries and
produces a compact Chinese report for the recurring question: why did many
safe-looking Pulse/worker/selector attempts fail to give 5/10 no-regression and
20-task speedup?  It does not run BPC, pricing, RMP, or Pulse.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_LEDGER = Path("BPC_future/results/root_cause_evidence_ledger_20260613/summary.json")
DEFAULT_FAILURE_MATRIX = Path("BPC_future/results/root_cause_failure_matrix_20260613/summary.json")
DEFAULT_SELECTOR_BLOCKER = Path(
    "BPC_future/results/root_cause_production_selector_blocker_catalog_20260614/summary.json"
)
DEFAULT_FEATURE_AVAILABILITY = Path(
    "BPC_future/results/root_cause_selector_feature_availability_audit_20260614/summary.json"
)
DEFAULT_SCHEMA_FEASIBILITY = Path(
    "BPC_future/results/root_cause_capture_schema_feasibility_audit_20260614/summary.json"
)
DEFAULT_ENRICHED_SINGLE = Path(
    "BPC_future/results/root_cause_selector_enriched_rmp_feature_holdout_20260614/summary.json"
)
DEFAULT_ENRICHED_MODEL = Path(
    "BPC_future/results/root_cause_selector_enriched_multifeature_model_holdout_20260614/summary.json"
)
DEFAULT_ACTIVE_BASIS_COUNTEREXAMPLES = Path(
    "BPC_future/results/root_cause_active_basis_snapshot_counterexamples_20260614/"
    "summary.json"
)
DEFAULT_PRODUCTION_GATE = Path(
    "BPC_future/results/root_cause_production_ab_entry_gate_catalog_20260614/summary.json"
)
DEFAULT_COMPONENT_PAYLOAD_ROWS = Path(
    "BPC_future/results/root_cause_component_payload_addition_before_rows_20260614/"
    "summary.json"
)
DEFAULT_COMPONENT_PAYLOAD_HOLDOUT_EXTENSION = Path(
    "BPC_future/results/"
    "root_cause_component_payload_selector_holdout_extension_20260614/summary.json"
)
DEFAULT_SELECTOR_HOLDOUT_GAP_MATRIX = Path(
    "BPC_future/results/root_cause_selector_holdout_gap_matrix_20260614/"
    "summary.json"
)
DEFAULT_PRIORITY_CAPTURE_MISS = Path(
    "BPC_future/results/root_cause_selector_holdout_priority_capture_miss_20260614/"
    "summary.json"
)
DEFAULT_SELECTOR_CONTEXT_ACTION_PLAN = Path(
    "BPC_future/results/root_cause_selector_holdout_context_action_plan_20260614/"
    "summary.json"
)
DEFAULT_CONTEXT_TRAJECTORY_PROTOCOL = Path(
    "BPC_future/results/root_cause_selector_context_trajectory_capture_protocol_20260614/"
    "summary.json"
)
DEFAULT_SELECTOR_HOLDOUT_BLOCKER_STATUS = Path(
    "BPC_future/results/root_cause_selector_holdout_blocker_status_20260614/"
    "summary.json"
)
DEFAULT_WORKER_NEGATIVE_ROI_BLOCKER = Path(
    "BPC_future/results/root_cause_worker_negative_column_roi_blocker_20260614/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_why_many_attempts_failed_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_why_many_attempts_failed_zh.md"
)


EXPECTED_MISSING = [
    "five_ten_full_no_regression_ab",
    "production_validated_selector",
    "twenty_walltime_speedup",
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _route_by_id(failure_matrix: dict[str, Any], route_id: str) -> dict[str, Any]:
    for route in failure_matrix.get("routes", []):
        if route.get("route_id") == route_id:
            return route
    return {}


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def build_summary(
    *,
    ledger_path: Path,
    failure_matrix_path: Path,
    selector_blocker_path: Path,
    feature_availability_path: Path,
    schema_feasibility_path: Path,
    enriched_single_path: Path,
    enriched_model_path: Path,
    active_basis_counterexamples_path: Path,
    production_gate_path: Path,
    component_payload_rows_path: Path,
    component_payload_holdout_extension_path: Path,
    selector_holdout_gap_matrix_path: Path,
    priority_capture_miss_path: Path,
    selector_context_action_plan_path: Path,
    context_trajectory_protocol_path: Path,
    selector_holdout_blocker_status_path: Path,
    worker_negative_roi_blocker_path: Path,
) -> dict[str, Any]:
    ledger = _read_json(ledger_path)
    failure_matrix = _read_json(failure_matrix_path)
    selector_blocker = _read_json(selector_blocker_path)
    feature_availability = _read_json(feature_availability_path)
    schema_feasibility = _read_json(schema_feasibility_path)
    enriched_single = _read_json(enriched_single_path)
    enriched_model = _read_json(enriched_model_path)
    active_basis_counterexamples = _read_json(active_basis_counterexamples_path)
    production_gate = _read_json(production_gate_path)
    component_payload_rows = _read_json(component_payload_rows_path)
    component_payload_holdout_extension = _read_json(
        component_payload_holdout_extension_path
    )
    selector_holdout_gap_matrix = _read_json(selector_holdout_gap_matrix_path)
    priority_capture_miss = _read_json(priority_capture_miss_path)
    selector_context_action_plan = _read_json(selector_context_action_plan_path)
    context_trajectory_protocol = _read_json(context_trajectory_protocol_path)
    selector_holdout_blocker_status = _read_json(
        selector_holdout_blocker_status_path
    )
    worker_negative_roi_blocker = _read_json(worker_negative_roi_blocker_path)

    small = ledger.get("checks", {}).get("small_scale_overhead", {})
    goal_status = ledger.get("goal_status", {})
    completion_decision = ledger.get("completion_decision", {})
    missing = list(goal_status.get("missing_requirement_names", []))
    ledger_core_status_consistent = (
        goal_status.get("goal_complete") is False
        and completion_decision.get("status") == "keep_goal_active"
        and missing == EXPECTED_MISSING
    )

    pulse_route = _route_by_id(failure_matrix, "pulse_wiring_or_certificate_semantics")
    negative_route = _route_by_id(failure_matrix, "more_true_rc_negative_columns")
    worker_route = _route_by_id(failure_matrix, "expand_worker_budget_or_default_worker")
    local_selector_route = _route_by_id(
        failure_matrix, "true_rc_threshold_or_local_column_selector"
    )

    causes = [
        {
            "cause_id": "small_scale_fixed_overhead_sensitivity",
            "conclusion": "5/10 规模不是缺负列，而是触发 worker/audit/probe 的固定开销吃掉收益。",
            "evidence": {
                "triggered_rows": small.get("triggered_rows"),
                "triggered_worse_count": small.get("triggered_worse_count"),
                "triggered_better_count": small.get("triggered_better_count"),
                "nontriggered_official_changed": small.get("nontriggered_official_changed"),
                "missing_requirement": "five_ten_full_no_regression_ab",
            },
        },
        {
            "cause_id": "twenty_returned_batch_rmp_trajectory_coupling",
            "conclusion": (
                "20-task 不是完全找不到 true-RC negative columns；问题是 returned batch "
                "是否改变后续 RMP active-basis / dual / pricing tail。"
            ),
            "evidence": {
                "negative_columns_route_status": negative_route.get("status"),
                "negative_columns_route_evidence": negative_route.get("evidence", {}),
                "pulse_route_status": pulse_route.get("status"),
                "pulse_route_evidence": pulse_route.get("evidence", {}),
                "has_20_walltime_speedup_evidence": goal_status.get(
                    "has_20_walltime_speedup_evidence"
                ),
                "active_basis_counterexample_task20_rows": (
                    active_basis_counterexamples.get("task20_row_count")
                ),
                "active_basis_counterexample_task20_new_task_sets": (
                    active_basis_counterexamples.get("task20_new_task_set_row_count")
                ),
                "active_basis_counterexample_task20_label_counts": (
                    active_basis_counterexamples.get("task20_label_counts")
                ),
                "active_basis_counterexample_strongest_noop_true_rc": (
                    (active_basis_counterexamples.get("strongest_noop") or {}).get(
                        "true_reduced_cost"
                    )
                ),
                "weaker_improved_than_strongest_noop_count": (
                    active_basis_counterexamples.get(
                        "weaker_improved_than_strongest_noop_count"
                    )
                ),
                "worker_negative_roi_blocker_status": (
                    worker_negative_roi_blocker.get("status")
                ),
                "phase7o_worker_added_journeys": (
                    worker_negative_roi_blocker.get("phase7o_expanded", {}).get(
                        "worker_added_journeys"
                    )
                ),
                "phase7o_worker_added_new_task_sets": (
                    worker_negative_roi_blocker.get("phase7o_expanded", {}).get(
                        "worker_added_new_task_sets"
                    )
                ),
                "phase7o_nonbaseline_worsened_rows": (
                    worker_negative_roi_blocker.get("phase7o_expanded", {}).get(
                        "nonbaseline_worsened_rows"
                    )
                ),
                "phase7o_nonbaseline_rows": (
                    worker_negative_roi_blocker.get("phase7o_expanded", {}).get(
                        "nonbaseline_rows"
                    )
                ),
                "phase8q_worker_added_journeys": (
                    worker_negative_roi_blocker.get("phase8q_validation", {}).get(
                        "worker_added_journeys"
                    )
                ),
                "phase8q_worker_added_rows": (
                    worker_negative_roi_blocker.get("phase8q_validation", {}).get(
                        "worker_added_rows"
                    )
                ),
                "phase8q_improved_without_worker_added_count": (
                    worker_negative_roi_blocker.get(
                        "phase8q_improved_without_worker_added_count"
                    )
                ),
            },
        },
        {
            "cause_id": "addition_before_selector_not_production_validated",
            "conclusion": (
                "当前已有 calibration signal，但没有一个只用 addition-before 特征的 selector "
                "能通过 context / instance / dataset holdout。补回 event-history 可恢复字段并定义"
                "full-snapshot active-basis churn / RMP degeneracy pressure 后，旧 replay 证据包"
                "仍缺这些 snapshot 指标的实际值。最新 component payload 已能转成 "
                "addition-before rows；最小合并到 base selector rows 后仍没有 robust "
                "all-holdout feature/model。"
            ),
            "evidence": {
                "selector_status": selector_blocker.get("status"),
                "selector_blocker_count": len(selector_blocker.get("blockers", [])),
                "robust_single_features": enriched_single.get(
                    "robust_all_holdout_numeric_features", []
                ),
                "robust_enriched_features": enriched_single.get(
                    "robust_all_holdout_enriched_features", []
                ),
                "robust_models": enriched_model.get("robust_all_holdout_models", []),
                "best_context_model": enriched_model.get("best_context_model"),
                "candidate_row_count": feature_availability.get("row_count"),
                "present_rmp_fields": len(
                    feature_availability.get("desired_rmp_trajectory_present", [])
                ),
                "missing_rmp_fields": len(
                    feature_availability.get("desired_rmp_trajectory_missing", [])
                ),
                "requires_manifest_pass_through": schema_feasibility.get(
                    "requires_manifest_pass_through_count"
                ),
                "requires_event_history_join": schema_feasibility.get(
                    "requires_event_history_join_count"
                ),
                "requires_capture_schema_extension": schema_feasibility.get(
                    "requires_capture_schema_extension_count"
                ),
                "recovered_from_event_history": schema_feasibility.get(
                    "recovered_from_event_history_field_count"
                ),
                "requires_metric_definition": schema_feasibility.get(
                    "requires_metric_definition_count"
                ),
                "active_basis_snapshot_metric_fields": schema_feasibility.get(
                    "active_basis_snapshot_metric_field_count"
                ),
                "counterexample_false_positive_count": len(
                    active_basis_counterexamples.get("false_positive_rows", [])
                ),
                "counterexample_positive_churn_label_counts": (
                    active_basis_counterexamples.get("positive_churn_label_counts")
                ),
                "counterexample_degeneracy_one_label_counts": (
                    active_basis_counterexamples.get("degeneracy_one_label_counts")
                ),
                "counterexample_mixed_instance_group_count": len(
                    active_basis_counterexamples.get("mixed_instance_groups", [])
                ),
                "component_payload_rows_ready_case_count": (
                    component_payload_rows.get("ready_case_count")
                ),
                "component_payload_rows_candidate_row_count": (
                    component_payload_rows.get("candidate_row_count")
                ),
                "component_payload_rows_explicit_forbidden_true_count": (
                    component_payload_rows.get("explicit_forbidden_true_count")
                ),
                "component_payload_rows_runs_local_rmp_replay": (
                    component_payload_rows.get("runs_local_rmp_replay")
                ),
                "component_payload_extension_base_row_count": (
                    component_payload_holdout_extension.get("base", {}).get(
                        "row_count"
                    )
                ),
                "component_payload_extension_component_row_count": (
                    component_payload_holdout_extension.get(
                        "component_only", {}
                    ).get("row_count")
                ),
                "component_payload_extension_combined_row_count": (
                    component_payload_holdout_extension.get("combined", {}).get(
                        "row_count"
                    )
                ),
                "component_payload_extension_component_positive_only": (
                    component_payload_holdout_extension.get(
                        "component_positive_only"
                    )
                ),
                "component_payload_extension_combined_robust_features": (
                    component_payload_holdout_extension.get("combined", {}).get(
                        "robust_all_holdout_derived_feature_count"
                    )
                ),
                "component_payload_extension_combined_robust_models": (
                    component_payload_holdout_extension.get("combined", {}).get(
                        "robust_all_holdout_model_count"
                    )
                ),
                "selector_holdout_gap_total_candidate_rows": (
                    selector_holdout_gap_matrix.get("total_candidate_row_count")
                ),
                "selector_holdout_gap_complete_snapshot_rows": (
                    selector_holdout_gap_matrix.get(
                        "complete_snapshot_total", {}
                    ).get("row_count")
                ),
                "selector_holdout_gap_complete_snapshot_label_counts": (
                    selector_holdout_gap_matrix.get(
                        "complete_snapshot_total", {}
                    ).get("label_counts")
                ),
                "selector_holdout_gap_mixed_context_count": (
                    selector_holdout_gap_matrix.get(
                        "complete_snapshot_context_label_mix", {}
                    ).get("mixed_label_context_count")
                ),
                "selector_holdout_gap_complete_explicit_label_counts": (
                    selector_holdout_gap_matrix.get(
                        "complete_explicit_forbidden_total", {}
                    ).get("label_counts")
                ),
                "priority_capture_miss_expected_context_count": (
                    priority_capture_miss.get("expected_context_count")
                ),
                "priority_capture_miss_exact_hit_context_count": (
                    priority_capture_miss.get("exact_hit_context_count")
                ),
                "priority_capture_miss_source_active_hash_missing_context_count": (
                    priority_capture_miss.get(
                        "source_active_hash_missing_context_count"
                    )
                ),
                "priority_capture_miss_same_active_component_drift_context_count": (
                    priority_capture_miss.get(
                        "same_active_component_drift_context_count"
                    )
                ),
                "selector_context_action_plan_unresolved_action_count": (
                    selector_context_action_plan.get("unresolved_action_count")
                ),
                "selector_context_action_plan_unresolved_execution_category_counts": (
                    selector_context_action_plan.get(
                        "unresolved_execution_category_counts"
                    )
                ),
                "selector_context_action_plan_complete_snapshot_action_count": (
                    selector_context_action_plan.get(
                        "complete_snapshot_action_count"
                    )
                ),
                "context_trajectory_exact_component_count": len(
                    context_trajectory_protocol.get("exact_context_components", [])
                ),
                "context_trajectory_required_payload_count": len(
                    context_trajectory_protocol.get("required_capture_payload", [])
                ),
                "source_profile_rerun_is_not_sufficient": (
                    context_trajectory_protocol.get("checks", {}).get(
                        "source_profile_rerun_is_not_sufficient"
                    )
                ),
                "same_active_hash_is_not_sufficient": (
                    context_trajectory_protocol.get("checks", {}).get(
                        "same_active_hash_is_not_sufficient"
                    )
                ),
                "selector_holdout_blocker_status": (
                    selector_holdout_blocker_status.get("status")
                ),
                "selector_holdout_blocker_collection_hit_count": (
                    selector_holdout_blocker_status.get("capture_status", {})
                    .get("collection", {})
                    .get("expected_context_hit_count")
                ),
                "selector_holdout_blocker_collection_expected_count": (
                    selector_holdout_blocker_status.get("capture_status", {})
                    .get("collection", {})
                    .get("expected_context_hash_count")
                ),
                "selector_holdout_blocker_priority_hit_count": (
                    selector_holdout_blocker_status.get("capture_status", {})
                    .get("priority", {})
                    .get("expected_context_hit_count")
                ),
                "selector_holdout_blocker_priority_expected_count": (
                    selector_holdout_blocker_status.get("capture_status", {})
                    .get("priority", {})
                    .get("expected_context_hash_count")
                ),
                "selector_holdout_blocker_complete_snapshot_label_counts": (
                    selector_holdout_blocker_status.get("snapshot_label_mix", {})
                    .get("complete_snapshot", {})
                    .get("label_counts")
                ),
                "selector_holdout_blocker_complete_explicit_forbidden_label_counts": (
                    selector_holdout_blocker_status.get("snapshot_label_mix", {})
                    .get("complete_explicit_forbidden", {})
                    .get("label_counts")
                ),
            },
        },
    ]

    ruled_out = [
        {
            "hypothesis": "Pulse 接线、物化或证书语义是主因",
            "status": pulse_route.get("status"),
            "why": pulse_route.get("why_not_enough"),
            "evidence": pulse_route.get("evidence", {}),
        },
        {
            "hypothesis": "只要找更多或更负 true-RC negative columns 就会优化",
            "status": negative_route.get("status"),
            "why": negative_route.get("why_not_enough"),
            "evidence": {
                **negative_route.get("evidence", {}),
                "worker_negative_roi_blocker_status": (
                    worker_negative_roi_blocker.get("status")
                ),
                "phase7o_worker_added_journeys": (
                    worker_negative_roi_blocker.get("phase7o_expanded", {}).get(
                        "worker_added_journeys"
                    )
                ),
                "phase7o_worker_added_new_task_sets": (
                    worker_negative_roi_blocker.get("phase7o_expanded", {}).get(
                        "worker_added_new_task_sets"
                    )
                ),
                "phase7o_nonbaseline_worsened_rows": (
                    worker_negative_roi_blocker.get("phase7o_expanded", {}).get(
                        "nonbaseline_worsened_rows"
                    )
                ),
                "phase7o_nonbaseline_rows": (
                    worker_negative_roi_blocker.get("phase7o_expanded", {}).get(
                        "nonbaseline_rows"
                    )
                ),
                "phase8q_worker_added_journeys": (
                    worker_negative_roi_blocker.get("phase8q_validation", {}).get(
                        "worker_added_journeys"
                    )
                ),
                "phase8q_worker_added_rows": (
                    worker_negative_roi_blocker.get("phase8q_validation", {}).get(
                        "worker_added_rows"
                    )
                ),
                "phase8q_improved_without_worker_added_count": (
                    worker_negative_roi_blocker.get(
                        "phase8q_improved_without_worker_added_count"
                    )
                ),
            },
        },
        {
            "hypothesis": "扩大 worker 预算或默认启用 worker",
            "status": worker_route.get("status"),
            "why": worker_route.get("why_not_enough"),
            "evidence": worker_route.get("evidence", {}),
        },
        {
            "hypothesis": "用 true-RC 阈值或局部列形状做 selector 已足够",
            "status": local_selector_route.get("status"),
            "why": local_selector_route.get("why_not_enough"),
            "evidence": local_selector_route.get("evidence", {}),
        },
        {
            "hypothesis": "重跑 source profile 或只匹配 active hash 就足够补齐 selector holdout",
            "status": "ruled_out_as_sufficient_condition",
            "why": (
                "Priority capture produced safe no-certificate-effect events, but hit "
                "0/3 expected contexts. Two targets did not reach the source active "
                "hash, and one same-active case drifted in pool/forbidden/returned-batch "
                "components, so source-profile rerun and active-hash-only matching are "
                "not sufficient evidence for selector holdout."
            ),
            "evidence": {
                "priority_capture_miss_status": priority_capture_miss.get("status"),
                "expected_context_count": priority_capture_miss.get(
                    "expected_context_count"
                ),
                "exact_hit_context_count": priority_capture_miss.get(
                    "exact_hit_context_count"
                ),
                "source_active_hash_missing_context_count": (
                    priority_capture_miss.get(
                        "source_active_hash_missing_context_count"
                    )
                ),
                "same_active_component_drift_context_count": (
                    priority_capture_miss.get(
                        "same_active_component_drift_context_count"
                    )
                ),
                "observed_event_count": priority_capture_miss.get(
                    "observed_event_count"
                ),
                "selector_context_action_plan_status": (
                    selector_context_action_plan.get("status")
                ),
                "selector_context_action_plan_unresolved_action_count": (
                    selector_context_action_plan.get("unresolved_action_count")
                ),
                "selector_context_action_plan_unresolved_execution_category_counts": (
                    selector_context_action_plan.get(
                        "unresolved_execution_category_counts"
                    )
                ),
                "context_trajectory_protocol_status": (
                    context_trajectory_protocol.get("status")
                ),
                "source_profile_rerun_is_not_sufficient": (
                    context_trajectory_protocol.get("checks", {}).get(
                        "source_profile_rerun_is_not_sufficient"
                    )
                ),
                "same_active_hash_is_not_sufficient": (
                    context_trajectory_protocol.get("checks", {}).get(
                        "same_active_hash_is_not_sufficient"
                    )
                ),
            },
        },
    ]

    checks = {
        "ledger_core_status_consistent": ledger_core_status_consistent,
        "goal_still_active": goal_status.get("goal_complete") is False
        and completion_decision.get("status") == "keep_goal_active",
        "missing_requirements_match_expected": missing == EXPECTED_MISSING,
        "small_overhead_evidence_present": small.get("check_triggered_all_worse") is True
        and small.get("check_nontriggered_no_official_change") is True,
        "negative_columns_not_sufficient": negative_route.get("status")
        == "ruled_out_as_sufficient_condition",
        "selector_blocker_passed": selector_blocker.get("all_checks_pass") is True
        and selector_blocker.get("status") == "production_selector_not_validated",
        "single_feature_selector_not_robust": enriched_single.get("all_checks_pass") is True
        and not enriched_single.get("robust_all_holdout_numeric_features")
        and not enriched_single.get("robust_all_holdout_enriched_features"),
        "multifeature_selector_not_robust": enriched_model.get("all_checks_pass") is True
        and not enriched_model.get("robust_all_holdout_models"),
        "rmp_feature_gap_present": feature_availability.get("all_checks_pass") is True
        and len(feature_availability.get("desired_rmp_trajectory_present", [])) == 17
        and len(feature_availability.get("desired_rmp_trajectory_missing", [])) == 0
        and schema_feasibility.get("recovered_from_event_history_field_count") == 8
        and schema_feasibility.get("active_basis_snapshot_metric_field_count") == 2
        and schema_feasibility.get("requires_metric_definition_count") == 0,
        "active_basis_counterexamples_present": (
            active_basis_counterexamples.get("all_checks_pass") is True
            and active_basis_counterexamples.get("runs_bpc_or_pricing") is False
            and _as_int(active_basis_counterexamples.get("task20_row_count")) == 12
            and _as_int(
                active_basis_counterexamples.get("task20_new_task_set_row_count")
            )
            == 12
            and len(active_basis_counterexamples.get("false_positive_rows", [])) >= 2
            and _as_int(
                active_basis_counterexamples.get(
                    "weaker_improved_than_strongest_noop_count"
                )
            )
            > 0
        ),
        "production_ab_still_blocked": production_gate.get(
            "production_candidate_ab_entry_status"
        )
        == "blocked"
        and production_gate.get("must_not_enable_worker_default") is True
        and production_gate.get("must_not_open_certificate_gate") is True,
        "component_payload_rows_constructed_but_not_production": (
            component_payload_rows.get("all_checks_pass") is True
            and component_payload_rows.get("diagnostic_only") is True
            and component_payload_rows.get("runs_bpc_or_pricing") is False
            and component_payload_rows.get("runs_local_rmp_replay") is True
            and component_payload_rows.get("status")
            == "component_payload_addition_before_rows_audited"
            and _as_int(component_payload_rows.get("candidate_row_count")) == 48
            and _as_int(component_payload_rows.get("explicit_forbidden_true_count"))
            == 48
        ),
        "component_payload_extension_still_not_production": (
            component_payload_holdout_extension.get("all_checks_pass") is True
            and component_payload_holdout_extension.get("diagnostic_only") is True
            and component_payload_holdout_extension.get("runs_bpc_or_pricing")
            is False
            and component_payload_holdout_extension.get("status")
            == "component_payload_selector_holdout_extension_audited"
            and _as_int(
                component_payload_holdout_extension.get("base", {}).get("row_count")
            )
            == 280
            and _as_int(
                component_payload_holdout_extension.get("component_only", {}).get(
                    "row_count"
                )
            )
            == 48
            and _as_int(
                component_payload_holdout_extension.get("combined", {}).get(
                    "row_count"
                )
            )
            == 328
            and component_payload_holdout_extension.get("component_positive_only")
            is True
            and component_payload_holdout_extension.get(
                "combined_has_no_robust_selector"
            )
            is True
        ),
        "selector_holdout_gap_requires_negative_mixed_contexts": (
            selector_holdout_gap_matrix.get("all_checks_pass") is True
            and selector_holdout_gap_matrix.get("diagnostic_only") is True
            and selector_holdout_gap_matrix.get("runs_bpc_or_pricing") is False
            and selector_holdout_gap_matrix.get("status")
            == "selector_holdout_gap_matrix_audited"
            and _as_int(selector_holdout_gap_matrix.get("total_candidate_row_count"))
            == 630
            and _as_int(
                selector_holdout_gap_matrix.get("complete_snapshot_total", {}).get(
                    "row_count"
                )
            )
            == 62
            and selector_holdout_gap_matrix.get(
                "complete_snapshot_context_label_mix", {}
            ).get("mixed_label_context_count")
            == 0
            and selector_holdout_gap_matrix.get(
                "complete_explicit_forbidden_total", {}
            ).get("label_counts")
            == {"improved": 48}
        ),
        "priority_capture_miss_blocks_source_profile_rerun_shortcut": (
            priority_capture_miss.get("all_checks_pass") is True
            and priority_capture_miss.get("diagnostic_only") is True
            and priority_capture_miss.get("runs_bpc_or_pricing") is False
            and priority_capture_miss.get("status")
            == "selector_holdout_priority_capture_miss_diagnosed"
            and _as_int(priority_capture_miss.get("expected_context_count")) == 3
            and _as_int(priority_capture_miss.get("exact_hit_context_count")) == 0
            and _as_int(
                priority_capture_miss.get(
                    "source_active_hash_missing_context_count"
                )
            )
            == 2
            and _as_int(
                priority_capture_miss.get(
                    "same_active_component_drift_context_count"
                )
            )
            == 1
        ),
        "selector_context_action_plan_confirms_unresolved_context_actions": (
            selector_context_action_plan.get("all_checks_pass") is True
            and selector_context_action_plan.get("diagnostic_only") is True
            and selector_context_action_plan.get("runs_bpc_or_pricing") is False
            and selector_context_action_plan.get("status")
            == "selector_holdout_context_action_plan_ready"
            and _as_int(selector_context_action_plan.get("row_count")) == 12
            and _as_int(
                selector_context_action_plan.get("complete_snapshot_action_count")
            )
            == 7
            and _as_int(selector_context_action_plan.get("unresolved_action_count"))
            == 5
            and selector_context_action_plan.get(
                "unresolved_execution_category_counts", {}
            ).get("trajectory_variant_capture_required")
            == 2
            and selector_context_action_plan.get(
                "unresolved_execution_category_counts", {}
            ).get("full_component_match_required")
            == 1
            and selector_context_action_plan.get(
                "unresolved_execution_category_counts", {}
            ).get("run_or_reaudit_existing_manifest_command")
            == 1
            and selector_context_action_plan.get(
                "unresolved_execution_category_counts", {}
            ).get("source_mapping_recovery_required")
            == 1
        ),
        "context_trajectory_protocol_requires_exact_components": (
            context_trajectory_protocol.get("all_checks_pass") is True
            and context_trajectory_protocol.get("diagnostic_only") is True
            and context_trajectory_protocol.get("runs_bpc_or_pricing") is False
            and context_trajectory_protocol.get("status")
            == "selector_context_trajectory_capture_protocol_ready"
            and len(context_trajectory_protocol.get("exact_context_components", []))
            == 9
            and len(context_trajectory_protocol.get("required_capture_payload", []))
            == 9
            and context_trajectory_protocol.get("checks", {}).get(
                "source_profile_rerun_is_not_sufficient"
            )
            is True
            and context_trajectory_protocol.get("checks", {}).get(
                "same_active_hash_is_not_sufficient"
            )
            is True
        ),
        "selector_holdout_blocker_status_confirms_snapshot_label_mix_gap": (
            selector_holdout_blocker_status.get("all_checks_pass") is True
            and selector_holdout_blocker_status.get("diagnostic_only") is True
            and selector_holdout_blocker_status.get("runs_bpc_or_pricing") is False
            and selector_holdout_blocker_status.get("status")
            == "selector_holdout_blocked_by_snapshot_label_mix"
            and selector_holdout_blocker_status.get("capture_status", {})
            .get("collection", {})
            .get("expected_context_hit_count")
            == 9
            and selector_holdout_blocker_status.get("capture_status", {})
            .get("collection", {})
            .get("expected_context_hash_count")
            == 10
            and selector_holdout_blocker_status.get("capture_status", {})
            .get("priority", {})
            .get("expected_context_hit_count")
            == 0
            and selector_holdout_blocker_status.get("capture_status", {})
            .get("priority", {})
            .get("expected_context_hash_count")
            == 3
            and selector_holdout_blocker_status.get("snapshot_label_mix", {})
            .get("complete_snapshot", {})
            .get("label_counts")
            == {"improved": 59, "noop": 3}
            and selector_holdout_blocker_status.get("snapshot_label_mix", {})
            .get("complete_explicit_forbidden", {})
            .get("label_counts")
            == {"improved": 48}
        ),
        "worker_negative_column_roi_blocker_confirms_negative_columns_not_sufficient": (
            worker_negative_roi_blocker.get("all_checks_pass") is True
            and worker_negative_roi_blocker.get("diagnostic_only") is True
            and worker_negative_roi_blocker.get("runs_bpc_or_pricing") is False
            and worker_negative_roi_blocker.get("status")
            == "worker_negative_columns_not_sufficient_for_roi"
            and _as_int(
                worker_negative_roi_blocker.get("phase7o_expanded", {}).get(
                    "worker_added_journeys"
                )
            )
            == 63
            and _as_int(
                worker_negative_roi_blocker.get("phase7o_expanded", {}).get(
                    "worker_added_new_task_sets"
                )
            )
            == 30
            and _as_int(
                worker_negative_roi_blocker.get("phase7o_expanded", {}).get(
                    "nonbaseline_worsened_rows"
                )
            )
            == _as_int(
                worker_negative_roi_blocker.get("phase7o_expanded", {}).get(
                    "nonbaseline_rows"
                )
            )
            and _as_int(
                worker_negative_roi_blocker.get("phase8q_validation", {}).get(
                    "worker_added_journeys"
                )
            )
            == 10
            and _as_int(
                worker_negative_roi_blocker.get(
                    "phase8q_improved_without_worker_added_count"
                )
            )
            >= 1
        ),
    }

    return {
        "schema_version": "why_many_attempts_failed_report_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "sources": {
            "ledger": str(ledger_path),
            "failure_matrix": str(failure_matrix_path),
            "selector_blocker": str(selector_blocker_path),
            "feature_availability": str(feature_availability_path),
            "schema_feasibility": str(schema_feasibility_path),
            "enriched_single": str(enriched_single_path),
            "enriched_model": str(enriched_model_path),
            "active_basis_counterexamples": str(active_basis_counterexamples_path),
            "production_gate": str(production_gate_path),
            "component_payload_rows": str(component_payload_rows_path),
            "component_payload_holdout_extension": str(
                component_payload_holdout_extension_path
            ),
            "selector_holdout_gap_matrix": str(selector_holdout_gap_matrix_path),
            "priority_capture_miss": str(priority_capture_miss_path),
            "selector_context_action_plan": str(selector_context_action_plan_path),
            "context_trajectory_protocol": str(context_trajectory_protocol_path),
            "selector_holdout_blocker_status": str(
                selector_holdout_blocker_status_path
            ),
            "worker_negative_roi_blocker": str(worker_negative_roi_blocker_path),
        },
        "status": "supported_but_optimization_direction_unproven",
        "root_cause_short": (
            "5/10 卡在固定开销；20 卡在 returned-batch 与 RMP trajectory 的上下文耦合；"
            "当前缺少 production-validated addition-before selector。"
        ),
        "causes": causes,
        "ruled_out_hypotheses": ruled_out,
        "missing_requirements": missing,
        "next_required_evidence": [
            "继续扩展 component-payload / full-snapshot addition-before rows 的负例和 mixed context 分布",
            "按完整 context 组件捕获目标轨迹；不能用 source profile 重跑或 active hash 近似替代 exact context",
            "只用 addition-before 特征通过 context / instance / dataset selector holdout",
            "之后才做 full BPC A/B：先 5/10 no-regression，再 selected 20 hard-repeat speedup",
        ],
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def _fmt_bool(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def write_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# 为什么做了很多工作仍不行：根因机制报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告只回答一个问题：为什么已经实现了 Sharded Pulse、audit、worker、",
        "current-context probe、selector calibration 之后，仍然不能同时做到 5/10 不退化",
        "和 20-task 明显优化？",
        "",
        "它只读现有 summary artifacts，不运行 BPC / pricing / RMP / Pulse，",
        "也不改变 worker / certificate / solver 默认行为。",
        "",
        "## 机器字段",
        "",
        "```text",
        "why_many_attempts_failed = current",
        f"diagnostic_only = {_fmt_bool(summary['diagnostic_only'])}",
        f"runs_bpc_or_pricing = {_fmt_bool(summary['runs_bpc_or_pricing'])}",
        f"status = {summary['status']}",
        f"all_checks_pass = {_fmt_bool(summary['all_checks_pass'])}",
        "```",
        "",
        "## 一句话结论",
        "",
        summary["root_cause_short"],
        "",
        "## 因果链",
        "",
    ]
    for cause in summary["causes"]:
        lines.extend(
            [
                f"### {cause['cause_id']}",
                "",
                cause["conclusion"],
                "",
                "```json",
                json.dumps(cause["evidence"], ensure_ascii=False, indent=2, sort_keys=True),
                "```",
                "",
            ]
        )

    lines.extend(["## 已排除解释", ""])
    for item in summary["ruled_out_hypotheses"]:
        lines.extend(
            [
                f"### {item['hypothesis']}",
                "",
                f"状态：`{item['status']}`",
                "",
                item.get("why") or "",
                "",
                "```json",
                json.dumps(item["evidence"], ensure_ascii=False, indent=2, sort_keys=True),
                "```",
                "",
            ]
        )

    lines.extend(
        [
            "## 为什么这不是已完成目标",
            "",
            "当前仍缺三项硬证据：",
            "",
            "```text",
            "missing_requirements = " + ",".join(summary["missing_requirements"]),
            "```",
            "",
            "含义是：根因解释已经有证据，但生产优化方向仍未证明。不能把",
            "worker 找到负列、单 context replay 成功、或 calibration threshold 当成",
            "5/10 不退化且 20-task 大幅加速的证明。",
            "",
            "## 下一步只能补的证据",
            "",
        ]
    )
    for item in summary["next_required_evidence"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## 检查项",
            "",
            "```json",
            json.dumps(summary["checks"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    parser.add_argument("--failure-matrix", default=str(DEFAULT_FAILURE_MATRIX))
    parser.add_argument("--selector-blocker", default=str(DEFAULT_SELECTOR_BLOCKER))
    parser.add_argument("--feature-availability", default=str(DEFAULT_FEATURE_AVAILABILITY))
    parser.add_argument("--schema-feasibility", default=str(DEFAULT_SCHEMA_FEASIBILITY))
    parser.add_argument("--enriched-single", default=str(DEFAULT_ENRICHED_SINGLE))
    parser.add_argument("--enriched-model", default=str(DEFAULT_ENRICHED_MODEL))
    parser.add_argument(
        "--active-basis-counterexamples",
        default=str(DEFAULT_ACTIVE_BASIS_COUNTEREXAMPLES),
    )
    parser.add_argument("--production-gate", default=str(DEFAULT_PRODUCTION_GATE))
    parser.add_argument(
        "--component-payload-rows",
        default=str(DEFAULT_COMPONENT_PAYLOAD_ROWS),
    )
    parser.add_argument(
        "--component-payload-holdout-extension",
        default=str(DEFAULT_COMPONENT_PAYLOAD_HOLDOUT_EXTENSION),
    )
    parser.add_argument(
        "--selector-holdout-gap-matrix",
        default=str(DEFAULT_SELECTOR_HOLDOUT_GAP_MATRIX),
    )
    parser.add_argument(
        "--priority-capture-miss",
        default=str(DEFAULT_PRIORITY_CAPTURE_MISS),
    )
    parser.add_argument(
        "--selector-context-action-plan",
        default=str(DEFAULT_SELECTOR_CONTEXT_ACTION_PLAN),
    )
    parser.add_argument(
        "--context-trajectory-protocol",
        default=str(DEFAULT_CONTEXT_TRAJECTORY_PROTOCOL),
    )
    parser.add_argument(
        "--selector-holdout-blocker-status",
        default=str(DEFAULT_SELECTOR_HOLDOUT_BLOCKER_STATUS),
    )
    parser.add_argument(
        "--worker-negative-roi-blocker",
        default=str(DEFAULT_WORKER_NEGATIVE_ROI_BLOCKER),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    summary = build_summary(
        ledger_path=Path(args.ledger),
        failure_matrix_path=Path(args.failure_matrix),
        selector_blocker_path=Path(args.selector_blocker),
        feature_availability_path=Path(args.feature_availability),
        schema_feasibility_path=Path(args.schema_feasibility),
        enriched_single_path=Path(args.enriched_single),
        enriched_model_path=Path(args.enriched_model),
        active_basis_counterexamples_path=Path(args.active_basis_counterexamples),
        production_gate_path=Path(args.production_gate),
        component_payload_rows_path=Path(args.component_payload_rows),
        component_payload_holdout_extension_path=Path(
            args.component_payload_holdout_extension
        ),
        selector_holdout_gap_matrix_path=Path(args.selector_holdout_gap_matrix),
        priority_capture_miss_path=Path(args.priority_capture_miss),
        selector_context_action_plan_path=Path(args.selector_context_action_plan),
        context_trajectory_protocol_path=Path(args.context_trajectory_protocol),
        selector_holdout_blocker_status_path=Path(
            args.selector_holdout_blocker_status
        ),
        worker_negative_roi_blocker_path=Path(args.worker_negative_roi_blocker),
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(summary, Path(args.report))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

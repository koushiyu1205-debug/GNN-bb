"""Batch benchmark runner for lunar-ice instances."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
import json
from pathlib import Path
from time import perf_counter
from typing import Iterable

from lunar_ice_bpc.domain.scenario import SOLVE_TIME_LIMIT_SEC_BY_SCALE
from lunar_ice_bpc.exact.bpc.pricing.status import is_direct_dp_time_limit_status
from lunar_ice_bpc.io.instance_io import read_json, write_json
from lunar_ice_bpc.runners.solve import solve_reference


def _manifest_instance_paths(
    manifest_path: Path,
    project_root: Path,
    *,
    scales: Iterable[int | str] | None = None,
) -> list[Path]:
    manifest = read_json(manifest_path)
    allowed_scales = _normalize_scale_filter(scales)
    paths: list[Path] = []
    for row in manifest.get("instances", []):
        if allowed_scales is not None and _manifest_row_scale_label(row) not in allowed_scales:
            continue
        raw = Path(str(row["path"]))
        if raw.is_absolute():
            paths.append(raw)
            continue
        candidate = project_root / raw
        if candidate.exists():
            paths.append(candidate)
            continue
        paths.append(project_root / "data" / raw)
    return paths


def _normalize_scale_filter(scales: Iterable[int | str] | None) -> set[str] | None:
    if scales is None:
        return None
    labels: set[str] = set()
    for item in scales:
        if item is None:
            continue
        text = str(item).strip()
        if not text:
            continue
        labels.add(f"{int(text):03d}")
    return labels or None


def _manifest_row_scale_label(row: dict) -> str:
    if row.get("scale_label") is not None:
        return f"{int(str(row['scale_label']).strip()):03d}"
    if row.get("scale") is not None:
        return f"{int(row['scale']):03d}"
    path = str(row.get("path", ""))
    for scale in (5, 10, 20, 30, 50, 100):
        if f"lunar_ice_{scale:03d}" in path:
            return f"{scale:03d}"
    return ""


def _solve_one(
    instance_path: Path,
    solution_dir: Path,
    *,
    canonical_dp_max_tasks: int,
    direct_baseline_max_tasks: int,
    direct_baseline_time_limit_sec: float | None,
    restricted_rmp_enabled: bool,
    direct_pricing_enabled: bool,
    direct_pricing_max_tasks: int,
    direct_pricing_cg_rounds: int,
    time_limit_sec: float | None,
) -> dict:
    start = perf_counter()
    solution_path = solution_dir / instance_path.parent.name / f"{instance_path.stem}_solution.json"
    result = solve_reference(
        instance_path,
        solution_path,
        canonical_dp_max_tasks=canonical_dp_max_tasks,
        direct_baseline_max_tasks=direct_baseline_max_tasks,
        direct_baseline_time_limit_sec=direct_baseline_time_limit_sec,
        restricted_rmp_enabled=restricted_rmp_enabled,
        direct_pricing_enabled=direct_pricing_enabled,
        direct_pricing_max_tasks=direct_pricing_max_tasks,
        direct_pricing_cg_rounds=direct_pricing_cg_rounds,
    )
    elapsed = perf_counter() - start
    timings = result.get("timings") or {}
    rmp = result.get("restricted_rmp") or {}
    branch_context = rmp.get("branch_context") or {}
    branch_probe = rmp.get("branch_probe") or {}
    fractional_branch_probe = rmp.get("fractional_branch_probe") or {}
    branch_tree_probe = rmp.get("branch_tree_probe") or {}
    branch_node_queue = rmp.get("branch_node_queue") or {}
    cut_context = rmp.get("cut_context") or {}
    cut_duals = rmp.get("cut_duals") or {}
    primal_cut_activities = rmp.get("primal_cut_activities") or []
    cut_probe = rmp.get("cut_probe") or {}
    cut_separation = rmp.get("cut_separation_probe") or {}
    fixed_graph_pricing_proof = rmp.get("fixed_graph_pricing_proof") or {}
    fixed_graph_pricing_closure = rmp.get("fixed_graph_pricing_closure") or {}
    completion_bound_consistency = fixed_graph_pricing_closure.get("completion_bound_consistency") or {}
    direct = rmp.get("direct_pricing") or {}
    direct_cg = rmp.get("direct_column_generation") or {}
    direct_cg_incumbent = direct_cg.get("integer_incumbent") or {}
    direct_cache = direct.get("sortie_template_cache") or {}
    direct_completion_bound = direct.get("completion_bound") or {}
    direct_cg_cache = direct_cg.get("sortie_template_cache") or {}
    rmp_pool = rmp.get("pool") or {}
    seeded_selection = result.get("seeded_column_pool_selection") or {}
    direct_root_certificate = result.get("direct_root_certificate") or {}
    pricing_certificate = result.get("pricing_certificate") or {}
    true_dual_pricing_tail = result.get("true_dual_pricing_tail") or {}
    true_dual_tail_certificate = true_dual_pricing_tail.get("pricing_certificate") or {}
    pricing_frontier = pricing_certificate.get("frontier_ledger") or {}
    node_bound_certificate = result.get("node_bound_certificate") or {}
    true_dual_readiness = result.get("true_dual_certificate_readiness") or {}
    canonical_baseline = result.get("canonical_baseline") or {}
    direct_exact_baseline = result.get("direct_exact_baseline") or {}
    task_count = int(result.get("task_count") or 0)
    row_time_limit_sec = float(time_limit_sec) if time_limit_sec is not None else SOLVE_TIME_LIMIT_SEC_BY_SCALE.get(task_count)
    time_limit_exceeded = bool(row_time_limit_sec is not None and elapsed > float(row_time_limit_sec))
    row = {
        "instance_path": str(instance_path),
        "solution_path": str(solution_path),
        "instance_id": result.get("instance_id"),
        "status": result.get("status"),
        "algorithm_status": result.get("algorithm_status", result.get("status")),
        "exact_status": result.get("exact_status"),
        "exact_claim_scope": result.get("exact_claim_scope"),
        "certificate_scope": result.get("certificate_scope"),
        "bpc_certificate_status": result.get("bpc_certificate_status"),
        "uses_true_dual_bpc_certificate": result.get("uses_true_dual_bpc_certificate"),
        "pricing_certificate_status": pricing_certificate.get("status"),
        "pricing_certificate_selected_source": pricing_certificate.get("selected_certificate_source"),
        "pricing_certificate_true_dual_tail_status": pricing_certificate.get("true_dual_pricing_tail_status"),
        "pricing_certificate_exact_status": pricing_certificate.get("exact_status"),
        "pricing_certificate_scope": pricing_certificate.get("certificate_scope"),
        "pricing_certificate_can_certify_no_negative": pricing_certificate.get("can_certify_no_negative"),
        "pricing_certificate_pricing_complete": pricing_certificate.get("pricing_complete"),
        "pricing_certificate_coverage_complete": pricing_certificate.get("coverage_complete"),
        "pricing_certificate_min_reduced_cost": pricing_certificate.get("min_reduced_cost"),
        "true_dual_pricing_tail_status": true_dual_pricing_tail.get("status"),
        "true_dual_pricing_tail_source": true_dual_pricing_tail.get("source"),
        "true_dual_pricing_tail_uses_true_dual": true_dual_pricing_tail.get("uses_true_dual_bpc_certificate"),
        "true_dual_pricing_tail_pricing_complete": true_dual_pricing_tail.get("pricing_complete"),
        "true_dual_pricing_tail_coverage_complete": true_dual_pricing_tail.get("coverage_complete"),
        "true_dual_pricing_tail_rmp_optimal": true_dual_pricing_tail.get("rmp_optimal"),
        "true_dual_pricing_tail_min_reduced_cost": true_dual_pricing_tail.get("min_reduced_cost"),
        "true_dual_pricing_tail_dual_vector_bound_to_rmp": true_dual_pricing_tail.get(
            "dual_vector_bound_to_rmp"
        ),
        "true_dual_pricing_tail_dual_vector_fingerprint": true_dual_pricing_tail.get(
            "dual_vector_fingerprint"
        ),
        "true_dual_pricing_tail_can_certify_no_negative": true_dual_pricing_tail.get("can_certify_no_negative"),
        "true_dual_pricing_tail_lower_bound_official": true_dual_pricing_tail.get("lower_bound_official"),
        "true_dual_pricing_tail_missing_input_count": true_dual_pricing_tail.get("missing_input_count"),
        "true_dual_pricing_tail_certificate_status": true_dual_tail_certificate.get("status"),
        "pricing_frontier_status": pricing_frontier.get("status"),
        "pricing_frontier_global_remaining_rc_lower_bound": pricing_frontier.get("global_remaining_rc_lower_bound"),
        "pricing_frontier_lower_bound_official": pricing_frontier.get("lower_bound_official"),
        "pricing_frontier_can_certify_no_negative": pricing_frontier.get("can_certify_no_negative"),
        "pricing_frontier_issue_count": len(pricing_frontier.get("issues") or []),
        "node_bound_certificate_status": node_bound_certificate.get("status"),
        "node_bound_certificate_exact_status": node_bound_certificate.get("exact_status"),
        "node_bound_lower_bound_official": node_bound_certificate.get("lower_bound_official"),
        "node_bound_can_fathom_by_bound": node_bound_certificate.get("can_fathom_by_bound"),
        "node_bound_issue_count": len(node_bound_certificate.get("issues") or []),
        "true_dual_readiness_status": true_dual_readiness.get("status"),
        "true_dual_readiness_true_dual_pricing_used": true_dual_readiness.get("true_dual_pricing_used"),
        "true_dual_readiness_diagnostic_direct_pricing_complete": true_dual_readiness.get(
            "diagnostic_direct_pricing_complete"
        ),
        "true_dual_readiness_diagnostic_fixed_graph_closure_complete": true_dual_readiness.get(
            "diagnostic_fixed_graph_closure_complete"
        ),
        "true_dual_readiness_fixed_graph_closure_status": true_dual_readiness.get("fixed_graph_closure_status"),
        "true_dual_readiness_fixed_graph_closure_no_negative_proved": true_dual_readiness.get(
            "fixed_graph_closure_no_negative_proved"
        ),
        "true_dual_readiness_diagnostic_no_negative": true_dual_readiness.get("diagnostic_no_negative"),
        "true_dual_readiness_missing_input_count": true_dual_readiness.get("missing_input_count"),
        "true_dual_readiness_can_certify": true_dual_readiness.get("can_certify"),
        "objective": result.get("objective"),
        "lower_bound": result.get("lower_bound"),
        "lower_bound_source": result.get("lower_bound_source"),
        "lower_bound_scope": result.get("lower_bound_scope"),
        "relaxation_gap": result.get("relaxation_gap"),
        "gap_type": result.get("gap_type"),
        "best_diagnostic_bound": result.get("best_diagnostic_bound"),
        "best_diagnostic_bound_source": result.get("best_diagnostic_bound_source"),
        "best_diagnostic_bound_scope": result.get("best_diagnostic_bound_scope"),
        "canonical_baseline_status": canonical_baseline.get("status"),
        "canonical_baseline_exact_status": canonical_baseline.get("exact_status"),
        "canonical_baseline_certificate_scope": canonical_baseline.get("certificate_scope"),
        "direct_baseline_status": direct_exact_baseline.get("status"),
        "direct_baseline_exact_status": direct_exact_baseline.get("exact_status"),
        "direct_baseline_certificate_scope": direct_exact_baseline.get("certificate_scope"),
        "path_option_dominance_policy": result.get("path_option_dominance_policy"),
        "path_option_dominance_filtered_count": result.get("path_option_dominance_filtered_count"),
        "infeasibility_scope_if_any": result.get("infeasibility_scope_if_any"),
        "canonical_objective": result.get("canonical_objective"),
        "direct_exact_objective": result.get("direct_exact_objective"),
        "direct_root_certificate_status": direct_root_certificate.get("status"),
        "direct_root_certificate_exact_status": direct_root_certificate.get("exact_status"),
        "direct_root_lp_bound": direct_root_certificate.get("lp_bound"),
        "direct_root_gap": direct_root_certificate.get("root_gap"),
        "direct_root_min_reduced_cost": direct_root_certificate.get("min_reduced_cost"),
        "direct_root_universe_column_count": direct_root_certificate.get("universe_column_count"),
        "direct_root_integer_matches_lp": direct_root_certificate.get("integer_matches_root_lp"),
        "direct_root_uses_true_dual_bpc_certificate": direct_root_certificate.get("uses_true_dual_bpc_certificate"),
        "incumbent_source": result.get("incumbent_source"),
        "seeded_selection_status": seeded_selection.get("status"),
        "seeded_selection_objective": seeded_selection.get("objective"),
        "seeded_selection_state_count": seeded_selection.get("state_count"),
        "seeded_selection_max_states": seeded_selection.get("max_states"),
        "makespan_min": result.get("makespan_min"),
        "covered_task_count": result.get("covered_task_count"),
        "task_count": result.get("task_count"),
        "node_count": result.get("node_count", 0 if result.get("status") == "INVALID_INSTANCE" else 1),
        "time_limit_sec": row_time_limit_sec,
        "time_limit_exceeded": time_limit_exceeded,
        "timeout_reason": "wall_time_exceeded_configured_budget" if time_limit_exceeded else "",
        "generated_journey_count": result.get("generated_journey_count", 0),
        "generated_sortie_count": result.get("generated_sortie_count", 0),
        "route_template_count": result.get("route_template_count", 0),
        "pareto_label_count": result.get("pareto_label_count", 0),
        "set_partition_state_count": result.get("set_partition_state_count", 0),
        "canonical_dp_max_tasks": result.get("solver_options", {}).get("canonical_dp_max_tasks", canonical_dp_max_tasks),
        "direct_baseline_max_tasks": result.get("solver_options", {}).get("direct_baseline_max_tasks", direct_baseline_max_tasks),
        "direct_baseline_time_limit_sec": result.get("solver_options", {}).get(
            "direct_baseline_time_limit_sec",
            direct_baseline_time_limit_sec,
        ),
        "restricted_rmp_status": rmp.get("status"),
        "restricted_rmp_pool_type": rmp.get("pool_type"),
        "restricted_rmp_pool_column_count": rmp_pool.get("column_count"),
        "restricted_rmp_bound": rmp.get("objective_bound"),
        "restricted_rmp_min_reduced_cost": rmp.get("min_reduced_cost"),
        "restricted_rmp_active_column_count": rmp.get("active_column_count"),
        "restricted_rmp_primal_active_column_count": rmp.get("primal_active_column_count"),
        "restricted_rmp_primal_cover_residual_max": rmp.get("primal_cover_residual_max"),
        "restricted_rmp_primal_fleet_usage": rmp.get("primal_fleet_usage"),
        "restricted_rmp_branch_decision_count": branch_context.get("pair_decision_count"),
        "restricted_rmp_branch_filtered_column_count": rmp.get("branch_filtered_column_count"),
        "restricted_rmp_cut_count": cut_context.get("cut_count"),
        "restricted_rmp_cut_rows_active": rmp.get("cut_rows_active"),
        "restricted_rmp_cut_dual_count": len(cut_duals),
        "restricted_rmp_primal_cut_activity_count": len(primal_cut_activities),
        "restricted_rmp_primal_cut_violation_max": rmp.get("primal_cut_violation_max"),
        "cut_probe_status": cut_probe.get("status"),
        "cut_probe_subset_candidate_count": cut_probe.get("subset_candidate_count"),
        "cut_probe_violated_subset_candidate_count": cut_probe.get("violated_subset_candidate_count"),
        "cut_probe_rows_added_to_rmp": cut_probe.get("rows_added_to_rmp"),
        "cut_probe_cut_rows_active": cut_probe.get("cut_rows_active"),
        "cut_probe_mutates_solver": cut_probe.get("mutates_solver"),
        "cut_probe_can_certify": cut_probe.get("can_certify"),
        "cut_separation_status": cut_separation.get("status"),
        "cut_separation_candidate_cut_count": cut_separation.get("candidate_cut_count"),
        "cut_separation_selected_cut_count": cut_separation.get("selected_cut_count"),
        "cut_separation_rows_added_to_rmp": cut_separation.get("rows_added_to_rmp"),
        "cut_separation_cut_rows_active": cut_separation.get("cut_rows_active"),
        "cut_separation_cut_rmp_status": cut_separation.get("cut_rmp_status"),
        "cut_separation_cut_rmp_bound": cut_separation.get("cut_rmp_objective_bound"),
        "cut_separation_cut_rmp_bound_delta": cut_separation.get("cut_rmp_bound_delta"),
        "cut_separation_primal_cut_violation_max": cut_separation.get("primal_cut_violation_max"),
        "cut_separation_lower_bound_official": cut_separation.get("lower_bound_official"),
        "cut_separation_mutates_solver": cut_separation.get("mutates_solver"),
        "cut_separation_can_certify": cut_separation.get("can_certify"),
        "fixed_graph_pricing_proof_status": fixed_graph_pricing_proof.get("status"),
        "fixed_graph_pricing_proof_complete": fixed_graph_pricing_proof.get(
            "pricing_complete_for_all_task_subsets"
        ),
        "fixed_graph_pricing_proof_min_reduced_cost": fixed_graph_pricing_proof.get("min_reduced_cost"),
        "fixed_graph_pricing_proof_negative_found": fixed_graph_pricing_proof.get("negative_found"),
        "fixed_graph_pricing_proof_no_negative_proved": fixed_graph_pricing_proof.get(
            "fixed_graph_no_negative_proved"
        ),
        "fixed_graph_pricing_proof_uses_true_dual_bpc_certificate": fixed_graph_pricing_proof.get(
            "uses_true_dual_bpc_certificate"
        ),
        "fixed_graph_pricing_proof_lower_bound_official": fixed_graph_pricing_proof.get("lower_bound_official"),
        "fixed_graph_pricing_proof_can_certify_no_negative": fixed_graph_pricing_proof.get(
            "can_certify_no_negative"
        ),
        "fixed_graph_pricing_closure_status": fixed_graph_pricing_closure.get("status"),
        "fixed_graph_pricing_closure_round_count": fixed_graph_pricing_closure.get("round_count"),
        "fixed_graph_pricing_closure_added_column_count": fixed_graph_pricing_closure.get("added_column_count"),
        "fixed_graph_pricing_closure_final_bound": fixed_graph_pricing_closure.get("final_bound"),
        "fixed_graph_pricing_closure_last_best_reduced_cost": fixed_graph_pricing_closure.get(
            "last_best_reduced_cost"
        ),
        "fixed_graph_pricing_closure_no_negative_proved": fixed_graph_pricing_closure.get(
            "fixed_graph_no_negative_proved"
        ),
        "fixed_graph_pricing_closure_uses_true_dual_bpc_certificate": fixed_graph_pricing_closure.get(
            "uses_true_dual_bpc_certificate"
        ),
        "fixed_graph_pricing_closure_lower_bound_official": fixed_graph_pricing_closure.get("lower_bound_official"),
        "fixed_graph_pricing_closure_can_certify_no_negative": fixed_graph_pricing_closure.get(
            "can_certify_no_negative"
        ),
        "completion_bound_consistency_status": completion_bound_consistency.get("status"),
        "completion_bound_consistency_consistent": completion_bound_consistency.get("consistent"),
        "completion_bound_consistency_with_bound_best_reduced_cost": completion_bound_consistency.get(
            "with_bound_best_reduced_cost"
        ),
        "completion_bound_consistency_without_bound_best_reduced_cost": completion_bound_consistency.get(
            "without_bound_best_reduced_cost"
        ),
        "completion_bound_consistency_with_bound_pruned_label_count": completion_bound_consistency.get(
            "with_bound_pruned_label_count"
        ),
        "completion_bound_consistency_with_bound_evaluated_label_count": completion_bound_consistency.get(
            "with_bound_evaluated_label_count"
        ),
        "completion_bound_consistency_without_bound_evaluated_label_count": completion_bound_consistency.get(
            "without_bound_evaluated_label_count"
        ),
        "completion_bound_consistency_can_certify_no_negative": completion_bound_consistency.get(
            "can_certify_no_negative"
        ),
        "branch_probe_status": branch_probe.get("status"),
        "branch_probe_candidate_count": branch_probe.get("candidate_count"),
        "branch_probe_reported_candidate_count": branch_probe.get("reported_candidate_count"),
        "branch_probe_mutates_solver": branch_probe.get("mutates_solver"),
        "branch_probe_can_certify": branch_probe.get("can_certify"),
        "fractional_branch_probe_status": fractional_branch_probe.get("status"),
        "fractional_branch_probe_candidate_count": fractional_branch_probe.get("candidate_count"),
        "fractional_branch_probe_reported_candidate_count": fractional_branch_probe.get("reported_candidate_count"),
        "fractional_branch_probe_mutates_solver": fractional_branch_probe.get("mutates_solver"),
        "fractional_branch_probe_can_certify": fractional_branch_probe.get("can_certify"),
        "branch_tree_probe_status": branch_tree_probe.get("status"),
        "branch_tree_probe_node_count": branch_tree_probe.get("node_count"),
        "branch_tree_probe_child_count": branch_tree_probe.get("child_count"),
        "branch_tree_probe_reported_branch_pair_count": branch_tree_probe.get("reported_branch_pair_count"),
        "branch_tree_probe_restricted_rmp_evaluation_enabled": branch_tree_probe.get(
            "restricted_rmp_evaluation_enabled"
        ),
        "branch_tree_probe_evaluated_node_count": branch_tree_probe.get("evaluated_node_count"),
        "branch_tree_probe_child_evaluated_count": branch_tree_probe.get("child_evaluated_count"),
        "branch_tree_probe_child_restricted_rmp_value_count": branch_tree_probe.get("child_restricted_rmp_value_count"),
        "branch_tree_probe_best_child_restricted_rmp_value": branch_tree_probe.get("best_child_restricted_rmp_value"),
        "branch_tree_probe_mutates_solver": branch_tree_probe.get("mutates_solver"),
        "branch_tree_probe_can_certify": branch_tree_probe.get("can_certify"),
        "branch_node_queue_status": branch_node_queue.get("status"),
        "branch_node_queue_node_count": branch_node_queue.get("node_count"),
        "branch_node_queue_evaluated_node_count": branch_node_queue.get("evaluated_node_count"),
        "branch_node_queue_created_node_count": branch_node_queue.get("created_node_count"),
        "branch_node_queue_expanded_node_count": branch_node_queue.get("expanded_node_count"),
        "branch_node_queue_max_depth_reached": branch_node_queue.get("max_depth_reached"),
        "branch_node_queue_node_limit_hit": branch_node_queue.get("node_limit_hit"),
        "branch_node_queue_branch_candidate_total": branch_node_queue.get("branch_candidate_total"),
        "branch_node_queue_restricted_rmp_value_count": branch_node_queue.get("restricted_rmp_value_count"),
        "branch_node_queue_best_restricted_rmp_value": branch_node_queue.get("best_restricted_rmp_value"),
        "branch_node_queue_direct_pricing_probe_enabled": branch_node_queue.get("direct_pricing_probe_enabled"),
        "branch_node_queue_direct_pricing_probe_node_count": branch_node_queue.get("direct_pricing_probe_node_count"),
        "branch_node_queue_branch_feasible_negative_count": branch_node_queue.get("branch_feasible_negative_count"),
        "branch_node_queue_best_branch_feasible_reduced_cost": branch_node_queue.get(
            "best_branch_feasible_reduced_cost"
        ),
        "branch_node_queue_direct_pricing_probe_can_certify_no_negative": branch_node_queue.get(
            "direct_pricing_probe_can_certify_no_negative"
        ),
        "branch_node_queue_post_pricing_restricted_rmp_node_count": branch_node_queue.get(
            "post_pricing_restricted_rmp_node_count"
        ),
        "branch_node_queue_post_pricing_added_column_count": branch_node_queue.get("post_pricing_added_column_count"),
        "branch_node_queue_post_pricing_restricted_rmp_value_count": branch_node_queue.get(
            "post_pricing_restricted_rmp_value_count"
        ),
        "branch_node_queue_best_post_pricing_restricted_rmp_value": branch_node_queue.get(
            "best_post_pricing_restricted_rmp_value"
        ),
        "branch_node_queue_post_pricing_lower_bound_official": branch_node_queue.get(
            "post_pricing_lower_bound_official"
        ),
        "branch_node_queue_node_pricing_certificate_can_certify_count": branch_node_queue.get(
            "node_pricing_certificate_can_certify_count"
        ),
        "branch_node_queue_node_bound_incumbent_attached_count": branch_node_queue.get(
            "node_bound_incumbent_attached_count"
        ),
        "branch_node_queue_node_bound_incumbent_missing_count": branch_node_queue.get(
            "node_bound_incumbent_missing_count"
        ),
        "branch_node_queue_node_bound_fail_closed_count": branch_node_queue.get("node_bound_fail_closed_count"),
        "branch_node_queue_node_bound_can_fathom_count": branch_node_queue.get("node_bound_can_fathom_count"),
        "branch_node_queue_lower_bound_official": branch_node_queue.get("lower_bound_official"),
        "branch_node_queue_mutates_solver": branch_node_queue.get("mutates_solver"),
        "branch_node_queue_can_certify": branch_node_queue.get("can_certify"),
        "direct_pricing_status": direct.get("status"),
        "direct_pricing_best_reduced_cost": direct.get("best_reduced_cost"),
        "direct_pricing_negative_found": direct.get("negative_found"),
        "direct_pricing_complete_for_all_tasks": direct.get("pricing_complete_for_all_tasks"),
        "direct_pricing_branch_context_active": direct.get("branch_context_active"),
        "direct_pricing_branch_decision_count": direct.get("branch_decision_count"),
        "direct_pricing_branch_filtered_column_count": direct.get("branch_filtered_column_count"),
        "direct_pricing_candidate_round_count": direct.get("candidate_round_count"),
        "direct_pricing_candidate_round_limit": direct.get("candidate_round_limit"),
        "direct_pricing_candidate_task_count": direct.get("candidate_task_count"),
        "direct_pricing_feasible_sortie_template_count": direct.get("feasible_sortie_template_count"),
        "direct_pricing_completion_bound_enabled": direct_completion_bound.get("enabled"),
        "direct_pricing_completion_bound_pruned_label_count": direct_completion_bound.get("pruned_label_count"),
        "direct_pricing_completion_bound_evaluated_label_count": direct_completion_bound.get("evaluated_label_count"),
        "direct_pricing_completion_bound_can_certify": direct_completion_bound.get("can_certify_no_negative"),
        "direct_pricing_cache_hit_count": direct_cache.get("hit_count"),
        "direct_pricing_cache_miss_count": direct_cache.get("miss_count"),
        "direct_cg_status": direct_cg.get("status"),
        "direct_cg_added_column_count": direct_cg.get("added_column_count"),
        "direct_cg_final_bound": direct_cg.get("final_bound"),
        "direct_cg_integer_objective": direct_cg_incumbent.get("objective"),
        "direct_cg_round_count": direct_cg.get("round_count"),
        "direct_cg_cache_hit_count": direct_cg_cache.get("hit_count"),
        "direct_cg_cache_miss_count": direct_cg_cache.get("miss_count"),
        "direct_cg_reused_sortie_attempt_count": direct_cg_cache.get("reused_sortie_attempt_count"),
        "preprocess_wall_time_sec": timings.get("preprocess_wall_time_sec"),
        "exact_baseline_wall_time_sec": timings.get("exact_baseline_wall_time_sec"),
        "canonical_baseline_wall_time_sec": timings.get("canonical_baseline_wall_time_sec"),
        "direct_baseline_wall_time_sec": timings.get("direct_baseline_wall_time_sec"),
        "restricted_rmp_wall_time_sec": timings.get("restricted_rmp_wall_time_sec"),
        "seeded_selection_wall_time_sec": timings.get("seeded_selection_wall_time_sec"),
        "solver_total_wall_time_sec": timings.get("total_solve_wall_time_sec"),
        "wall_time_sec": round(elapsed, 6),
        "incomplete_reason": _incomplete_reason(result),
    }
    return row


def _incomplete_reason(result: dict) -> str:
    if result.get("status") == "DIRECT_DP_BASELINE_OPTIMAL":
        return "exact_direct_dp_baseline_not_true_dual_bpc_certificate"
    direct_baseline = result.get("direct_exact_baseline") or {}
    if is_direct_dp_time_limit_status(str(direct_baseline.get("status") or "")):
        return "direct_baseline_time_limit_reference_fallback"
    if result.get("status") == "CANONICAL_DP_BASELINE_OPTIMAL":
        direct = ((result.get("restricted_rmp") or {}).get("direct_pricing") or {})
        if direct.get("negative_found"):
            return "restricted_universe_has_direct_negative_column"
        if direct.get("status") == "PARTIAL_DIRECT_LABEL_PRICED":
            return "restricted_universe_direct_pricing_partial"
        return "restricted_universe_not_bpc_certified"
    if result.get("status") == "FEASIBLE_REFERENCE":
        return "reference_only_exact_not_solved"
    if result.get("status") == "INVALID_INSTANCE":
        return "invalid_instance"
    return str(result.get("status") or "unknown")


def run_benchmark(
    *,
    project_root: str | Path,
    instances: Iterable[str | Path] | None = None,
    manifest_path: str | Path | None = None,
    max_workers: int = 4,
    results_csv: str | Path = "runs/csv/lunar_ice_benchmark.csv",
    solution_dir: str | Path = "runs/solutions/benchmark",
    summary_json: str | Path = "runs/csv/lunar_ice_benchmark_summary.json",
    canonical_dp_max_tasks: int = 10,
    direct_baseline_max_tasks: int = 10,
    direct_baseline_time_limit_sec: float | None = None,
    restricted_rmp_enabled: bool = True,
    direct_pricing_enabled: bool = True,
    direct_pricing_max_tasks: int = 5,
    direct_pricing_cg_rounds: int = 1,
    time_limit_sec: float | None = None,
    scales: Iterable[int | str] | None = None,
) -> dict:
    project_root = Path(project_root)
    if instances is None:
        if manifest_path is None:
            raise ValueError("either instances or manifest_path is required")
        instance_paths = _manifest_instance_paths(Path(manifest_path), project_root, scales=scales)
    else:
        instance_paths = [Path(path) if Path(path).is_absolute() else project_root / Path(path) for path in instances]

    solution_dir = Path(solution_dir)
    if not solution_dir.is_absolute():
        solution_dir = project_root / solution_dir
    solution_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    with ProcessPoolExecutor(max_workers=max(1, int(max_workers))) as pool:
        futures = [
            pool.submit(
                _solve_one,
                path,
                solution_dir,
                canonical_dp_max_tasks=int(canonical_dp_max_tasks),
                direct_baseline_max_tasks=int(direct_baseline_max_tasks),
                direct_baseline_time_limit_sec=(
                    float(direct_baseline_time_limit_sec) if direct_baseline_time_limit_sec is not None else None
                ),
                restricted_rmp_enabled=bool(restricted_rmp_enabled),
                direct_pricing_enabled=bool(direct_pricing_enabled),
                direct_pricing_max_tasks=int(direct_pricing_max_tasks),
                direct_pricing_cg_rounds=int(direct_pricing_cg_rounds),
                time_limit_sec=float(time_limit_sec) if time_limit_sec is not None else None,
            )
            for path in instance_paths
        ]
        for future in as_completed(futures):
            rows.append(future.result())
    rows.sort(key=lambda row: str(row["instance_path"]))

    csv_path = Path(results_csv)
    if not csv_path.is_absolute():
        csv_path = project_root / csv_path
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "instance_path",
        "solution_path",
        "instance_id",
        "status",
        "algorithm_status",
        "exact_status",
        "exact_claim_scope",
        "certificate_scope",
        "bpc_certificate_status",
        "uses_true_dual_bpc_certificate",
        "pricing_certificate_status",
        "pricing_certificate_selected_source",
        "pricing_certificate_true_dual_tail_status",
        "pricing_certificate_exact_status",
        "pricing_certificate_scope",
        "pricing_certificate_can_certify_no_negative",
        "pricing_certificate_pricing_complete",
        "pricing_certificate_coverage_complete",
        "pricing_certificate_min_reduced_cost",
        "true_dual_pricing_tail_status",
        "true_dual_pricing_tail_source",
        "true_dual_pricing_tail_uses_true_dual",
        "true_dual_pricing_tail_pricing_complete",
        "true_dual_pricing_tail_coverage_complete",
        "true_dual_pricing_tail_rmp_optimal",
        "true_dual_pricing_tail_min_reduced_cost",
        "true_dual_pricing_tail_dual_vector_bound_to_rmp",
        "true_dual_pricing_tail_dual_vector_fingerprint",
        "true_dual_pricing_tail_can_certify_no_negative",
        "true_dual_pricing_tail_lower_bound_official",
        "true_dual_pricing_tail_missing_input_count",
        "true_dual_pricing_tail_certificate_status",
        "pricing_frontier_status",
        "pricing_frontier_global_remaining_rc_lower_bound",
        "pricing_frontier_lower_bound_official",
        "pricing_frontier_can_certify_no_negative",
        "pricing_frontier_issue_count",
        "node_bound_certificate_status",
        "node_bound_certificate_exact_status",
        "node_bound_lower_bound_official",
        "node_bound_can_fathom_by_bound",
        "node_bound_issue_count",
        "true_dual_readiness_status",
        "true_dual_readiness_true_dual_pricing_used",
        "true_dual_readiness_diagnostic_direct_pricing_complete",
        "true_dual_readiness_diagnostic_fixed_graph_closure_complete",
        "true_dual_readiness_fixed_graph_closure_status",
        "true_dual_readiness_fixed_graph_closure_no_negative_proved",
        "true_dual_readiness_diagnostic_no_negative",
        "true_dual_readiness_missing_input_count",
        "true_dual_readiness_can_certify",
        "objective",
        "lower_bound",
        "lower_bound_source",
        "lower_bound_scope",
        "relaxation_gap",
        "gap_type",
        "best_diagnostic_bound",
        "best_diagnostic_bound_source",
        "best_diagnostic_bound_scope",
        "canonical_baseline_status",
        "canonical_baseline_exact_status",
        "canonical_baseline_certificate_scope",
        "direct_baseline_status",
        "direct_baseline_exact_status",
        "direct_baseline_certificate_scope",
        "path_option_dominance_policy",
        "path_option_dominance_filtered_count",
        "infeasibility_scope_if_any",
        "canonical_objective",
        "direct_exact_objective",
        "direct_root_certificate_status",
        "direct_root_certificate_exact_status",
        "direct_root_lp_bound",
        "direct_root_gap",
        "direct_root_min_reduced_cost",
        "direct_root_universe_column_count",
        "direct_root_integer_matches_lp",
        "direct_root_uses_true_dual_bpc_certificate",
        "incumbent_source",
        "seeded_selection_status",
        "seeded_selection_objective",
        "seeded_selection_state_count",
        "seeded_selection_max_states",
        "makespan_min",
        "covered_task_count",
        "task_count",
        "node_count",
        "time_limit_sec",
        "time_limit_exceeded",
        "timeout_reason",
        "generated_journey_count",
        "generated_sortie_count",
        "route_template_count",
        "pareto_label_count",
        "set_partition_state_count",
        "canonical_dp_max_tasks",
        "direct_baseline_max_tasks",
        "direct_baseline_time_limit_sec",
        "restricted_rmp_status",
        "restricted_rmp_pool_type",
        "restricted_rmp_pool_column_count",
        "restricted_rmp_bound",
        "restricted_rmp_min_reduced_cost",
        "restricted_rmp_active_column_count",
        "restricted_rmp_primal_active_column_count",
        "restricted_rmp_primal_cover_residual_max",
        "restricted_rmp_primal_fleet_usage",
        "restricted_rmp_branch_decision_count",
        "restricted_rmp_branch_filtered_column_count",
        "restricted_rmp_cut_count",
        "restricted_rmp_cut_rows_active",
        "restricted_rmp_cut_dual_count",
        "restricted_rmp_primal_cut_activity_count",
        "restricted_rmp_primal_cut_violation_max",
        "cut_probe_status",
        "cut_probe_subset_candidate_count",
        "cut_probe_violated_subset_candidate_count",
        "cut_probe_rows_added_to_rmp",
        "cut_probe_cut_rows_active",
        "cut_probe_mutates_solver",
        "cut_probe_can_certify",
        "cut_separation_status",
        "cut_separation_candidate_cut_count",
        "cut_separation_selected_cut_count",
        "cut_separation_rows_added_to_rmp",
        "cut_separation_cut_rows_active",
        "cut_separation_cut_rmp_status",
        "cut_separation_cut_rmp_bound",
        "cut_separation_cut_rmp_bound_delta",
        "cut_separation_primal_cut_violation_max",
        "cut_separation_lower_bound_official",
        "cut_separation_mutates_solver",
        "cut_separation_can_certify",
        "fixed_graph_pricing_proof_status",
        "fixed_graph_pricing_proof_complete",
        "fixed_graph_pricing_proof_min_reduced_cost",
        "fixed_graph_pricing_proof_negative_found",
        "fixed_graph_pricing_proof_no_negative_proved",
        "fixed_graph_pricing_proof_uses_true_dual_bpc_certificate",
        "fixed_graph_pricing_proof_lower_bound_official",
        "fixed_graph_pricing_proof_can_certify_no_negative",
        "fixed_graph_pricing_closure_status",
        "fixed_graph_pricing_closure_round_count",
        "fixed_graph_pricing_closure_added_column_count",
        "fixed_graph_pricing_closure_final_bound",
        "fixed_graph_pricing_closure_last_best_reduced_cost",
        "fixed_graph_pricing_closure_no_negative_proved",
        "fixed_graph_pricing_closure_uses_true_dual_bpc_certificate",
        "fixed_graph_pricing_closure_lower_bound_official",
        "fixed_graph_pricing_closure_can_certify_no_negative",
        "completion_bound_consistency_status",
        "completion_bound_consistency_consistent",
        "completion_bound_consistency_with_bound_best_reduced_cost",
        "completion_bound_consistency_without_bound_best_reduced_cost",
        "completion_bound_consistency_with_bound_pruned_label_count",
        "completion_bound_consistency_with_bound_evaluated_label_count",
        "completion_bound_consistency_without_bound_evaluated_label_count",
        "completion_bound_consistency_can_certify_no_negative",
        "branch_probe_status",
        "branch_probe_candidate_count",
        "branch_probe_reported_candidate_count",
        "branch_probe_mutates_solver",
        "branch_probe_can_certify",
        "fractional_branch_probe_status",
        "fractional_branch_probe_candidate_count",
        "fractional_branch_probe_reported_candidate_count",
        "fractional_branch_probe_mutates_solver",
        "fractional_branch_probe_can_certify",
        "branch_tree_probe_status",
        "branch_tree_probe_node_count",
        "branch_tree_probe_child_count",
        "branch_tree_probe_reported_branch_pair_count",
        "branch_tree_probe_restricted_rmp_evaluation_enabled",
        "branch_tree_probe_evaluated_node_count",
        "branch_tree_probe_child_evaluated_count",
        "branch_tree_probe_child_restricted_rmp_value_count",
        "branch_tree_probe_best_child_restricted_rmp_value",
        "branch_tree_probe_mutates_solver",
        "branch_tree_probe_can_certify",
        "branch_node_queue_status",
        "branch_node_queue_node_count",
        "branch_node_queue_evaluated_node_count",
        "branch_node_queue_created_node_count",
        "branch_node_queue_expanded_node_count",
        "branch_node_queue_max_depth_reached",
        "branch_node_queue_node_limit_hit",
        "branch_node_queue_branch_candidate_total",
        "branch_node_queue_restricted_rmp_value_count",
        "branch_node_queue_best_restricted_rmp_value",
        "branch_node_queue_direct_pricing_probe_enabled",
        "branch_node_queue_direct_pricing_probe_node_count",
        "branch_node_queue_branch_feasible_negative_count",
        "branch_node_queue_best_branch_feasible_reduced_cost",
        "branch_node_queue_direct_pricing_probe_can_certify_no_negative",
        "branch_node_queue_post_pricing_restricted_rmp_node_count",
        "branch_node_queue_post_pricing_added_column_count",
        "branch_node_queue_post_pricing_restricted_rmp_value_count",
        "branch_node_queue_best_post_pricing_restricted_rmp_value",
        "branch_node_queue_post_pricing_lower_bound_official",
        "branch_node_queue_node_pricing_certificate_can_certify_count",
        "branch_node_queue_node_bound_incumbent_attached_count",
        "branch_node_queue_node_bound_incumbent_missing_count",
        "branch_node_queue_node_bound_fail_closed_count",
        "branch_node_queue_node_bound_can_fathom_count",
        "branch_node_queue_lower_bound_official",
        "branch_node_queue_mutates_solver",
        "branch_node_queue_can_certify",
        "direct_pricing_status",
        "direct_pricing_best_reduced_cost",
        "direct_pricing_negative_found",
        "direct_pricing_complete_for_all_tasks",
        "direct_pricing_branch_context_active",
        "direct_pricing_branch_decision_count",
        "direct_pricing_branch_filtered_column_count",
        "direct_pricing_candidate_round_count",
        "direct_pricing_candidate_round_limit",
        "direct_pricing_candidate_task_count",
        "direct_pricing_feasible_sortie_template_count",
        "direct_pricing_completion_bound_enabled",
        "direct_pricing_completion_bound_pruned_label_count",
        "direct_pricing_completion_bound_evaluated_label_count",
        "direct_pricing_completion_bound_can_certify",
        "direct_pricing_cache_hit_count",
        "direct_pricing_cache_miss_count",
        "direct_cg_status",
        "direct_cg_added_column_count",
        "direct_cg_final_bound",
        "direct_cg_integer_objective",
        "direct_cg_round_count",
        "direct_cg_cache_hit_count",
        "direct_cg_cache_miss_count",
        "direct_cg_reused_sortie_attempt_count",
        "preprocess_wall_time_sec",
        "exact_baseline_wall_time_sec",
        "canonical_baseline_wall_time_sec",
        "direct_baseline_wall_time_sec",
        "restricted_rmp_wall_time_sec",
        "seeded_selection_wall_time_sec",
        "solver_total_wall_time_sec",
        "wall_time_sec",
        "incomplete_reason",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    summary = _summary(rows)
    summary["results_csv"] = str(csv_path)
    summary["solution_dir"] = str(solution_dir)
    summary_path = Path(summary_json)
    if not summary_path.is_absolute():
        summary_path = project_root / summary_path
    write_json(summary_path, summary)
    return summary


def _summary(rows: list[dict]) -> dict:
    status_counts: dict[str, int] = {}
    exact_counts: dict[str, int] = {}
    exact_scope_counts: dict[str, int] = {}
    certificate_scope_counts: dict[str, int] = {}
    bpc_certificate_counts: dict[str, int] = {}
    pricing_frontier_counts: dict[str, int] = {}
    true_dual_tail_counts: dict[str, int] = {}
    completion_bound_consistency_counts: dict[str, int] = {}
    node_bound_counts: dict[str, int] = {}
    true_dual_readiness_counts: dict[str, int] = {}
    branch_tree_counts: dict[str, int] = {}
    branch_node_queue_counts: dict[str, int] = {}
    fractional_branch_counts: dict[str, int] = {}
    cut_probe_counts: dict[str, int] = {}
    direct_baseline_counts: dict[str, int] = {}
    for row in rows:
        status_counts[str(row["status"])] = status_counts.get(str(row["status"]), 0) + 1
        exact_counts[str(row["exact_status"])] = exact_counts.get(str(row["exact_status"]), 0) + 1
        exact_scope = str(row.get("exact_claim_scope") or "missing")
        certificate_scope = str(row.get("certificate_scope") or "missing")
        certificate_status = str(row.get("bpc_certificate_status") or "missing")
        frontier_status = str(row.get("pricing_frontier_status") or "missing")
        true_dual_tail_status = str(row.get("true_dual_pricing_tail_status") or "missing")
        completion_bound_consistency_status = str(row.get("completion_bound_consistency_status") or "missing")
        node_bound_status = str(row.get("node_bound_certificate_status") or "missing")
        readiness_status = str(row.get("true_dual_readiness_status") or "missing")
        branch_tree_status = str(row.get("branch_tree_probe_status") or "missing")
        branch_node_queue_status = str(row.get("branch_node_queue_status") or "missing")
        fractional_branch_status = str(row.get("fractional_branch_probe_status") or "missing")
        cut_probe_status = str(row.get("cut_probe_status") or "missing")
        direct_baseline_status = str(row.get("direct_baseline_status") or "missing")
        exact_scope_counts[exact_scope] = exact_scope_counts.get(exact_scope, 0) + 1
        certificate_scope_counts[certificate_scope] = certificate_scope_counts.get(certificate_scope, 0) + 1
        bpc_certificate_counts[certificate_status] = bpc_certificate_counts.get(certificate_status, 0) + 1
        pricing_frontier_counts[frontier_status] = pricing_frontier_counts.get(frontier_status, 0) + 1
        true_dual_tail_counts[true_dual_tail_status] = true_dual_tail_counts.get(true_dual_tail_status, 0) + 1
        completion_bound_consistency_counts[completion_bound_consistency_status] = (
            completion_bound_consistency_counts.get(completion_bound_consistency_status, 0) + 1
        )
        node_bound_counts[node_bound_status] = node_bound_counts.get(node_bound_status, 0) + 1
        true_dual_readiness_counts[readiness_status] = true_dual_readiness_counts.get(readiness_status, 0) + 1
        branch_tree_counts[branch_tree_status] = branch_tree_counts.get(branch_tree_status, 0) + 1
        branch_node_queue_counts[branch_node_queue_status] = (
            branch_node_queue_counts.get(branch_node_queue_status, 0) + 1
        )
        fractional_branch_counts[fractional_branch_status] = (
            fractional_branch_counts.get(fractional_branch_status, 0) + 1
        )
        cut_probe_counts[cut_probe_status] = cut_probe_counts.get(cut_probe_status, 0) + 1
        direct_baseline_counts[direct_baseline_status] = direct_baseline_counts.get(direct_baseline_status, 0) + 1
    times = [float(row["wall_time_sec"]) for row in rows]
    exact_times = [
        float(row["exact_baseline_wall_time_sec"])
        for row in rows
        if row.get("exact_baseline_wall_time_sec") not in {None, ""}
    ]
    gaps = [float(row["relaxation_gap"]) for row in rows if row.get("relaxation_gap") not in {None, ""}]
    timeout_reasons: dict[str, int] = {}
    for row in rows:
        reason = str(row.get("timeout_reason") or "")
        if reason:
            timeout_reasons[reason] = timeout_reasons.get(reason, 0) + 1
    return {
        "schema_version": "lunar_ice_bpc.benchmark_summary.v1",
        "run_count": len(rows),
        "status_counts": status_counts,
        "exact_status_counts": exact_counts,
        "exact_claim_scope_counts": exact_scope_counts,
        "certificate_scope_counts": certificate_scope_counts,
        "bpc_certificate_status_counts": bpc_certificate_counts,
        "pricing_frontier_status_counts": pricing_frontier_counts,
        "true_dual_pricing_tail_status_counts": true_dual_tail_counts,
        "completion_bound_consistency_status_counts": completion_bound_consistency_counts,
        "node_bound_certificate_status_counts": node_bound_counts,
        "true_dual_readiness_status_counts": true_dual_readiness_counts,
        "fractional_branch_probe_status_counts": fractional_branch_counts,
        "cut_probe_status_counts": cut_probe_counts,
        "branch_tree_probe_status_counts": branch_tree_counts,
        "branch_node_queue_status_counts": branch_node_queue_counts,
        "direct_baseline_status_counts": direct_baseline_counts,
        "mean_wall_time_sec": round(sum(times) / max(1, len(times)), 6),
        "max_wall_time_sec": round(max(times), 6) if times else 0.0,
        "mean_exact_baseline_wall_time_sec": round(sum(exact_times) / max(1, len(exact_times)), 6)
        if exact_times
        else None,
        "max_exact_baseline_wall_time_sec": round(max(exact_times), 6) if exact_times else None,
        "mean_relaxation_gap": round(sum(gaps) / max(1, len(gaps)), 9) if gaps else None,
        "total_node_count": sum(int(float(row.get("node_count") or 0)) for row in rows),
        "exact_baseline_optimal_count": sum(1 for row in rows if row["exact_status"] == "EXACT_BASELINE_OPTIMAL"),
        "fixed_graph_root_lp_diagnostic_audit_count": sum(
            1
            for row in rows
            if row.get("direct_root_certificate_exact_status")
            in {"FIXED_GRAPH_ROOT_LP_DIAGNOSTIC", "FIXED_GRAPH_ROOT_LP_INTEGRAL_DIAGNOSTIC"}
        ),
        "fixed_graph_integer_root_diagnostic_count": sum(
            1
            for row in rows
            if row.get("direct_root_certificate_exact_status") == "FIXED_GRAPH_ROOT_LP_INTEGRAL_DIAGNOSTIC"
        ),
        "direct_pricing_completion_bound_pruned_label_count": sum(
            int(float(row.get("direct_pricing_completion_bound_pruned_label_count") or 0))
            for row in rows
        ),
        "direct_pricing_completion_bound_evaluated_label_count": sum(
            int(float(row.get("direct_pricing_completion_bound_evaluated_label_count") or 0))
            for row in rows
        ),
        "cut_probe_violated_subset_candidate_count": sum(
            int(float(row.get("cut_probe_violated_subset_candidate_count") or 0)) for row in rows
        ),
        "true_dual_bpc_certificate_count": sum(
            1 for row in rows if str(row.get("uses_true_dual_bpc_certificate") or "") == "True"
        ),
        "official_pricing_frontier_count": sum(
            1 for row in rows if str(row.get("pricing_frontier_lower_bound_official") or "") == "True"
        ),
        "true_dual_pricing_tail_certified_count": sum(
            1 for row in rows if str(row.get("true_dual_pricing_tail_can_certify_no_negative") or "") == "True"
        ),
        "true_dual_pricing_tail_dual_vector_bound_count": sum(
            1 for row in rows if str(row.get("true_dual_pricing_tail_dual_vector_bound_to_rmp") or "") == "True"
        ),
        "completion_bound_consistency_pass_count": sum(
            1 for row in rows if str(row.get("completion_bound_consistency_consistent") or "") == "True"
        ),
        "node_bound_fathomed_count": sum(
            1 for row in rows if str(row.get("node_bound_can_fathom_by_bound") or "") == "True"
        ),
        "true_dual_readiness_waiting_count": sum(
            1 for row in rows if str(row.get("true_dual_readiness_status") or "") == "WAITING_TRUE_DUAL_PRICING_PROOF"
        ),
        "true_dual_readiness_missing_input_count": sum(
            int(float(row.get("true_dual_readiness_missing_input_count") or 0)) for row in rows
        ),
        "branch_tree_probe_evaluated_node_count": sum(
            int(float(row.get("branch_tree_probe_evaluated_node_count") or 0)) for row in rows
        ),
        "branch_tree_probe_child_evaluated_count": sum(
            int(float(row.get("branch_tree_probe_child_evaluated_count") or 0)) for row in rows
        ),
        "branch_node_queue_evaluated_node_count": sum(
            int(float(row.get("branch_node_queue_evaluated_node_count") or 0)) for row in rows
        ),
        "branch_node_queue_expanded_node_count": sum(
            int(float(row.get("branch_node_queue_expanded_node_count") or 0)) for row in rows
        ),
        "branch_node_queue_direct_pricing_probe_node_count": sum(
            int(float(row.get("branch_node_queue_direct_pricing_probe_node_count") or 0)) for row in rows
        ),
        "branch_node_queue_branch_feasible_negative_count": sum(
            int(float(row.get("branch_node_queue_branch_feasible_negative_count") or 0)) for row in rows
        ),
        "branch_node_queue_post_pricing_restricted_rmp_node_count": sum(
            int(float(row.get("branch_node_queue_post_pricing_restricted_rmp_node_count") or 0)) for row in rows
        ),
        "branch_node_queue_post_pricing_added_column_count": sum(
            int(float(row.get("branch_node_queue_post_pricing_added_column_count") or 0)) for row in rows
        ),
        "branch_node_queue_node_pricing_certificate_can_certify_count": sum(
            int(float(row.get("branch_node_queue_node_pricing_certificate_can_certify_count") or 0)) for row in rows
        ),
        "branch_node_queue_node_bound_incumbent_attached_count": sum(
            int(float(row.get("branch_node_queue_node_bound_incumbent_attached_count") or 0)) for row in rows
        ),
        "branch_node_queue_node_bound_incumbent_missing_count": sum(
            int(float(row.get("branch_node_queue_node_bound_incumbent_missing_count") or 0)) for row in rows
        ),
        "branch_node_queue_node_bound_fail_closed_count": sum(
            int(float(row.get("branch_node_queue_node_bound_fail_closed_count") or 0)) for row in rows
        ),
        "branch_node_queue_node_bound_can_fathom_count": sum(
            int(float(row.get("branch_node_queue_node_bound_can_fathom_count") or 0)) for row in rows
        ),
        "time_limit_exceeded_count": sum(1 for row in rows if str(row.get("time_limit_exceeded")) == "True"),
        "timeout_reason_counts": timeout_reasons,
        "certified_optimal_count": sum(
            1 for row in rows if str(row.get("node_bound_can_fathom_by_bound") or "") == "True"
        ),
        "note": (
            "exact_baseline_optimal_count counts exhaustive direct-DP fixed-graph optima; "
            "fixed_graph_root_lp_diagnostic_audit_count is scoped to the fixed three-path root LP and is not "
            "a BPC certificate; "
            "certified_optimal_count is positive only when the selected pricing certificate is true-dual "
            "and the node-bound artifact can fathom the node."
        ),
    }

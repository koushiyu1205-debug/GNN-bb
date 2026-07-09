"""B4.1 true-dual proof-tail strengthening experiment runner."""

from __future__ import annotations

import csv
import json
from collections import Counter
from itertools import combinations
from pathlib import Path
from statistics import mean
from time import perf_counter
from types import SimpleNamespace
from typing import Iterable

from lunar_ice_bpc.exact.bpc.pricing.hidden_negative_audit import HIDDEN_NEGATIVE_MISS_REASONS
from lunar_ice_bpc.exact.bpc.pricing.status import CertificateScope
from lunar_ice_bpc.exact.bpc.solver.branch_tree_solver import solve_b3_branch_price_tree_baseline
from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import (
    B2B_R2_MODE,
    B2B_R3_MODE,
    solve_b2_pricing_tail_baseline,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.core.journey import journey_column_from_solution_payload
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.exact.solver.gurobi_compact import solve_highs_compact_single_journey_pricing
from lunar_ice_bpc.exact.solver.journey_driver import solve_direct_journey_baseline
from lunar_ice_bpc.exact.solver.journey_driver import _reference_solution_upper_bound
from lunar_ice_bpc.io.instance_io import read_json
from lunar_ice_bpc.runners.b4_pricing_formulation_diagnostic import (
    B4D_VARIANT_CONFIGS,
    build_b4_pricing_formulation_report_from_rows,
    iter_b4_pricing_formulation_matrix_rows_from_probe,
)


B41_STAGE_A_B3B_BASELINE = "stageA_B3B_accepted_baseline"
B41_STAGE_A_B4V2_HARVEST = "stageA_B4V2_default_final_judge_harvesting"
B41_STAGE_A_TAIL_DUAL_OFF = "stageA_B2B_R2_worker_tail_dual_off"
B41_STAGE_A_TAIL_DUAL_ON = "stageA_B2B_R2_worker_tail_dual_on"

B41_STAGE_A_MODES = (
    B41_STAGE_A_B3B_BASELINE,
    B41_STAGE_A_B4V2_HARVEST,
    B41_STAGE_A_TAIL_DUAL_OFF,
    B41_STAGE_A_TAIL_DUAL_ON,
)

B41_STAGE_A_REQUIRED_REGRESSION_MODES = (
    B41_STAGE_A_B3B_BASELINE,
    B41_STAGE_A_B4V2_HARVEST,
)

B41_STAGE_B_VARIANTS = (
    "V2_latest_service_start_slot_bound",
    "V4_combined_endpoint_pair_latest_start_time_window",
)

B41_STAGE_B_REQUIRED_MATRIX_CELLS = (
    "B4V2_baseline",
    "B4V2_harvesting",
    "B4V2_hidden_negative_audit",
    "B4V2_frontier_ledger_diagnostic",
    "B4V2_harvesting_frontier_ledger_diagnostic",
    "B4V4_combined_formulation_diagnostic",
)

B41_TARGETED_RESTRICTED_REGION_VARIANT_CONFIGS = {
    "V2_latest_service_start_slot_bound": {
        **B4D_VARIANT_CONFIGS["V2_latest_service_start_slot_bound"],
        "service_start_depot_travel_lb": False,
        "task_to_depot_return_travel_lb": False,
        "pair_route_duration_lb": False,
        "pair_weighted_completion_lb": False,
        "sortie_slot_position_bounds": False,
        "demand_cover_cut": False,
        "single_task_energy_lb": False,
        "single_task_shadow_lb": False,
        "pair_energy_lb": False,
        "pair_shadow_lb": False,
        "pair_energy_infeasible_cut": False,
        "pair_time_window_infeasible_cut": False,
        "pair_time_window_precedence_cut": False,
        "triple_time_window_infeasible_cut": False,
        "quad_time_window_infeasible_cut": False,
        "pair_shadow_infeasible_cut": False,
        "triple_shadow_infeasible_cut": False,
        "triple_energy_infeasible_cut": False,
    },
    "V4_combined_endpoint_pair_latest_start_time_window": {
        **B4D_VARIANT_CONFIGS["V4_combined_endpoint_pair_latest_start_time_window"],
        "service_start_depot_travel_lb": False,
        "task_to_depot_return_travel_lb": False,
        "pair_route_duration_lb": False,
        "pair_weighted_completion_lb": False,
        "sortie_slot_position_bounds": False,
        "demand_cover_cut": False,
        "single_task_energy_lb": False,
        "single_task_shadow_lb": False,
        "pair_energy_lb": False,
        "pair_shadow_lb": False,
        "pair_energy_infeasible_cut": False,
        "pair_time_window_infeasible_cut": False,
        "pair_time_window_precedence_cut": False,
        "triple_time_window_infeasible_cut": False,
        "quad_time_window_infeasible_cut": False,
        "pair_shadow_infeasible_cut": False,
        "triple_shadow_infeasible_cut": False,
        "triple_energy_infeasible_cut": False,
    },
    "V4_current_strengthening": {
        **B4D_VARIANT_CONFIGS["V4_combined_endpoint_pair_latest_start_time_window"],
        "formulation_kind": "endpoint_pair_latest_timewindow+service_return_pair_duration+slot_position+pair_energy_infeasible+pair_timewindow_infeasible",
        "service_start_depot_travel_lb": True,
        "task_to_depot_return_travel_lb": True,
        "pair_route_duration_lb": True,
        "pair_weighted_completion_lb": False,
        "sortie_slot_position_bounds": True,
        "demand_cover_cut": False,
        "single_task_energy_lb": False,
        "single_task_shadow_lb": False,
        "pair_energy_lb": False,
        "pair_shadow_lb": False,
        "pair_energy_infeasible_cut": True,
        "pair_time_window_infeasible_cut": True,
        "pair_time_window_precedence_cut": False,
        "triple_time_window_infeasible_cut": False,
        "quad_time_window_infeasible_cut": False,
        "pair_shadow_infeasible_cut": False,
        "triple_shadow_infeasible_cut": False,
        "triple_energy_infeasible_cut": False,
    },
    "V4_current_pair_weighted_completion_lb": {
        **B4D_VARIANT_CONFIGS["V4_combined_endpoint_pair_latest_start_time_window"],
        "formulation_kind": "endpoint_pair_latest_timewindow+service_return_pair_duration+pair_weighted_completion+slot_position+pair_energy_infeasible+pair_timewindow_infeasible",
        "service_start_depot_travel_lb": True,
        "task_to_depot_return_travel_lb": True,
        "pair_route_duration_lb": True,
        "pair_weighted_completion_lb": True,
        "sortie_slot_position_bounds": True,
        "demand_cover_cut": False,
        "single_task_energy_lb": False,
        "single_task_shadow_lb": False,
        "pair_energy_lb": False,
        "pair_shadow_lb": False,
        "pair_energy_infeasible_cut": True,
        "pair_time_window_infeasible_cut": True,
        "pair_time_window_precedence_cut": False,
        "triple_time_window_infeasible_cut": False,
        "quad_time_window_infeasible_cut": False,
        "pair_shadow_infeasible_cut": False,
        "triple_shadow_infeasible_cut": False,
        "triple_energy_infeasible_cut": False,
    },
    "V4_current_triple_time_window_infeasible": {
        **B4D_VARIANT_CONFIGS["V4_combined_endpoint_pair_latest_start_time_window"],
        "formulation_kind": "endpoint_pair_latest_timewindow+service_return_pair_duration+slot_position+pair_energy_infeasible+pair_timewindow_infeasible+triple_timewindow_infeasible",
        "service_start_depot_travel_lb": True,
        "task_to_depot_return_travel_lb": True,
        "pair_route_duration_lb": True,
        "pair_weighted_completion_lb": False,
        "sortie_slot_position_bounds": True,
        "demand_cover_cut": False,
        "single_task_energy_lb": False,
        "single_task_shadow_lb": False,
        "pair_energy_lb": False,
        "pair_shadow_lb": False,
        "pair_energy_infeasible_cut": True,
        "pair_time_window_infeasible_cut": True,
        "pair_time_window_precedence_cut": False,
        "triple_time_window_infeasible_cut": True,
        "quad_time_window_infeasible_cut": False,
        "pair_shadow_infeasible_cut": False,
        "triple_shadow_infeasible_cut": False,
        "triple_energy_infeasible_cut": False,
    },
    "V4_current_quad_time_window_infeasible": {
        **B4D_VARIANT_CONFIGS["V4_combined_endpoint_pair_latest_start_time_window"],
        "formulation_kind": "endpoint_pair_latest_timewindow+service_return_pair_duration+slot_position+pair_energy_infeasible+pair_timewindow_infeasible+triple_timewindow_infeasible+quad_timewindow_infeasible",
        "service_start_depot_travel_lb": True,
        "task_to_depot_return_travel_lb": True,
        "pair_route_duration_lb": True,
        "pair_weighted_completion_lb": False,
        "sortie_slot_position_bounds": True,
        "demand_cover_cut": False,
        "single_task_energy_lb": False,
        "single_task_shadow_lb": False,
        "pair_energy_lb": False,
        "pair_shadow_lb": False,
        "pair_energy_infeasible_cut": True,
        "pair_time_window_infeasible_cut": True,
        "pair_time_window_precedence_cut": False,
        "triple_time_window_infeasible_cut": True,
        "quad_time_window_infeasible_cut": True,
        "pair_shadow_infeasible_cut": False,
        "triple_shadow_infeasible_cut": False,
        "triple_energy_infeasible_cut": False,
    },
}

CSV_COLUMNS = (
    "stage",
    "matrix_group",
    "instance_path",
    "source_probe_json",
    "scale",
    "instance_id",
    "mode",
    "variant",
    "b4_1_matrix_cell",
    "b4_1_proof_tail_component",
    "b4_1_formulation_profile",
    "b4_1_harvesting_enabled",
    "b4_1_hidden_negative_audit_enabled",
    "b4_1_frontier_ledger_enabled",
    "b4_1_official_certificate_allowed",
    "phase",
    "round",
    "max_rounds",
    "max_columns_per_round",
    "max_tree_nodes",
    "max_branch_depth",
    "node_count",
    "root_round_count",
    "root_added_column_count",
    "root_last_pricing_state",
    "root_last_negative_column_count",
    "tree_gate_issue_count",
    "algorithm_status",
    "certificate_scope",
    "underlying_certificate_scope",
    "pricing_state",
    "exact_status",
    "bpc_tree_optimal",
    "b3_objective_diff_vs_b0",
    "manual_rc_fail",
    "pricing_rc_fail",
    "certificate_leak",
    "hidden_negative_count",
    "hidden_negative_miss_reason_counts",
    "hidden_negative_top_miss_reason",
    "hidden_negative_worker_not_generated_count",
    "hidden_negative_pruned_by_dominance_count",
    "hidden_negative_pricing_timeout_only_count",
    "active_column_count",
    "pool_column_count",
    "columns_added",
    "active_columns_after_merge",
    "new_task_set_count",
    "replacement_task_set_count",
    "best_negative_rc",
    "targeted_negative_task_set",
    "targeted_negative_task_set_size",
    "targeted_negative_true_rc",
    "targeted_negative_source_phase",
    "targeted_negative_task_set_forbidden_seen",
    "last_best_reduced_cost",
    "final_judge_wall_time",
    "rmp_round_count",
    "harvest_selected_count",
    "harvest_candidate_negative_count",
    "harvest_selected_new_task_set_count",
    "harvest_selected_replacement_task_set_count",
    "harvest_rejected_duplicate_count",
    "harvest_rejected_not_addable_count",
    "harvest_source_phase",
    "harvest_best_true_rc",
    "harvest_worst_selected_true_rc",
    "harvest_avg_pairwise_jaccard",
    "compact_optimization_harvest_enabled",
    "compact_optimization_harvest_target",
    "compact_optimization_harvest_no_good_scope",
    "compact_optimization_harvest_found_count",
    "compact_optimization_harvest_search_call_count",
    "harvest_addability_audit_pass",
    "harvest_pricing_rc_audit_available",
    "harvest_pricing_rc_audit_pass",
    "harvest_pricing_rc_max_abs_diff",
    "tail_dual_stabilization_enabled",
    "worker_dual_only",
    "true_dual_rc_recomputed",
    "worker_dual_source",
    "official_dual_source",
    "tail_dual_stabilization_alpha",
    "tail_dual_stabilization_window",
    "tail_dual_center_task_count",
    "tail_dual_current_task_count",
    "tail_dual_no_column_can_certify",
    "global_remaining_rc_lb",
    "underlying_global_remaining_rc_lb",
    "frontier_lb_official",
    "frontier_coverage_complete",
    "underlying_frontier_coverage_complete",
    "frontier_unsupported_region_count",
    "underlying_frontier_unsupported_region_count",
    "pending_complete_min_rc",
    "underlying_pending_complete_min_rc",
    "pricing_proof_kind",
    "underlying_pricing_proof_kind",
    "compact_final_judge_profile",
    "compact_final_judge_formulation_profile",
    "compact_final_judge_phase_mode",
    "service_start_depot_travel_lb_enabled",
    "service_start_depot_travel_lb_count",
    "task_to_depot_return_travel_lb_enabled",
    "task_to_depot_return_travel_lb_count",
    "pair_route_duration_lb_enabled",
    "pair_route_duration_lb_count",
    "pair_weighted_completion_lb_enabled",
    "pair_weighted_completion_lb_count",
    "pair_weighted_completion_lb_min",
    "pair_weighted_completion_lb_max",
    "sortie_slot_position_bounds_enabled",
    "sortie_slot_position_bound_count",
    "demand_cover_cut_enabled",
    "demand_cover_cut_count",
    "demand_cover_subset_count",
    "single_task_energy_lb_enabled",
    "single_task_energy_lb_count",
    "single_task_shadow_lb_enabled",
    "single_task_shadow_lb_count",
    "pair_energy_lb_enabled",
    "pair_energy_lb_count",
    "pair_energy_lb_exceeds_limit_count",
    "pair_shadow_lb_enabled",
    "pair_shadow_lb_count",
    "pair_shadow_lb_exceeds_limit_count",
    "pair_energy_infeasible_cut_enabled",
    "pair_energy_infeasible_cut_count",
    "pair_energy_infeasible_pair_count",
    "pair_time_window_infeasible_cut_enabled",
    "pair_time_window_infeasible_cut_count",
    "pair_time_window_infeasible_pair_count",
    "pair_time_window_infeasible_margin_min",
    "pair_time_window_infeasible_margin_max",
    "pair_time_window_precedence_cut_enabled",
    "pair_time_window_precedence_cut_count",
    "pair_time_window_precedence_pair_count",
    "pair_time_window_precedence_margin_min",
    "pair_time_window_precedence_margin_max",
    "triple_time_window_infeasible_cut_enabled",
    "triple_time_window_infeasible_cut_count",
    "triple_time_window_infeasible_triple_count",
    "triple_time_window_infeasible_margin_min",
    "triple_time_window_infeasible_margin_max",
    "quad_time_window_infeasible_cut_enabled",
    "quad_time_window_infeasible_cut_count",
    "quad_time_window_infeasible_quad_count",
    "quad_time_window_infeasible_margin_min",
    "quad_time_window_infeasible_margin_max",
    "pair_shadow_infeasible_cut_enabled",
    "pair_shadow_infeasible_cut_count",
    "pair_shadow_infeasible_pair_count",
    "triple_shadow_infeasible_cut_enabled",
    "triple_shadow_infeasible_cut_count",
    "triple_shadow_infeasible_triple_count",
    "triple_energy_infeasible_cut_enabled",
    "triple_energy_infeasible_cut_count",
    "triple_energy_infeasible_triple_count",
    "negative_feasibility_skipped_for_proof_only",
    "negative_feasibility_full_space_proof_attempted",
    "negative_feasibility_full_space_proof_can_certify",
    "phase_budget_sec",
    "negative_feasibility_budget_sec",
    "optimization_proof_budget_sec",
    "negative_discovery_budget_exhausted",
    "feasibility_proof_budget_exhausted",
    "optimization_proof_missing",
    "compact_pricing_dual_bound",
    "new_negative_columns_found",
    "negative_column_count",
    "can_certify_no_negative",
    "underlying_can_certify_no_negative",
    "b4_1_certificate_suppressed",
    "diagnostic_claimed_certificate",
    "wall_time",
    "fail_closed_reason",
)


def run_b4_1_stage_a_regression(
    instances: Iterable[str | Path | dict],
    *,
    matrix_group: str = "B4.1 Stage A regression",
    modes: Iterable[str] = B41_STAGE_A_MODES,
    max_direct_tasks: int = 5,
    max_rounds: int = 16,
    wall_time_limit_sec: float | None = None,
    max_columns_per_round: int = 128,
    max_tree_nodes: int = 31,
    max_branch_depth: int = 4,
) -> dict:
    rows: list[dict] = []
    for item in instances:
        raw, instance_path = _load_instance(item)
        data = load_lunar_ice_data(raw)
        scale = len(data.task_ids)
        b0 = None
        if scale <= int(max_direct_tasks):
            b0 = solve_direct_journey_baseline(
                data,
                max_exact_tasks=int(max_direct_tasks),
                wall_time_limit_sec=wall_time_limit_sec,
            )
        for mode in tuple(modes):
            start = perf_counter()
            try:
                raw_result = _run_stage_a_mode(
                    data,
                    mode=mode,
                    b0_direct=b0,
                    max_direct_tasks=max_direct_tasks,
                    max_rounds=max_rounds,
                    wall_time_limit_sec=wall_time_limit_sec,
                    max_columns_per_round=max_columns_per_round,
                    max_tree_nodes=max_tree_nodes,
                    max_branch_depth=max_branch_depth,
                )
                row = _stage_a_row(
                    raw_result,
                    stage="A",
                    matrix_group=matrix_group,
                    instance_path=instance_path,
                    scale=scale,
                    mode=mode,
                    wall_time=perf_counter() - start,
                    max_rounds=max_rounds,
                    max_columns_per_round=max_columns_per_round,
                    max_tree_nodes=max_tree_nodes,
                    max_branch_depth=max_branch_depth,
                )
            except Exception as exc:  # pragma: no cover - fail-closed runner boundary
                row = _exception_row(
                    stage="A",
                    matrix_group=matrix_group,
                    instance_path=instance_path,
                    scale=scale,
                    instance_id=data.instance_id,
                    mode=mode,
                    exc=exc,
                    wall_time=perf_counter() - start,
                )
            rows.append(row)
    return build_b4_1_report(rows)


def run_b4_1_stage_b_from_probe(
    source_probe_json: str | Path,
    *,
    matrix_group: str = "B4.1 Stage B 30-scale staged frontier",
    variants: Iterable[str] = B41_STAGE_B_VARIANTS,
    history_round: int = -1,
    negative_feasibility_time_limit_sec: float = 600.0,
    optimization_proof_time_limit_sec: float = 900.0,
    threads: int = 1,
    skip_keys: Iterable[tuple[str, str, str, str]] = (),
) -> dict:
    skip_lookup = set(skip_keys)
    requested_variants = tuple(variants)
    rows = _stage_b_probe_evidence_rows(source_probe_json, matrix_group=matrix_group, skip_keys=skip_lookup)
    if requested_variants:
        rows.extend(
            _stage_probe_row(row, stage="B", mode="B4.1_compact_pricing_formulation", matrix_group=matrix_group)
            for row in iter_b4_pricing_formulation_matrix_rows_from_probe(
                source_probe_json,
                variants=requested_variants,
                history_round=history_round,
                negative_feasibility_time_limit_sec=negative_feasibility_time_limit_sec,
                optimization_proof_time_limit_sec=optimization_proof_time_limit_sec,
                threads=int(threads),
                matrix_group=matrix_group,
                skip_keys=skip_lookup,
            )
        )
    return build_b4_1_report(rows)


def run_b4_1_stage_c_selected_from_probe(
    source_probe_json: str | Path,
    *,
    matrix_group: str = "B4.1 Stage C 30-scale selected diagnostic",
    variants: Iterable[str] = B41_STAGE_B_VARIANTS,
    history_round: int = -1,
    negative_feasibility_time_limit_sec: float = 600.0,
    optimization_proof_time_limit_sec: float = 900.0,
    threads: int = 1,
    skip_keys: Iterable[tuple[str, str, str, str]] = (),
) -> dict:
    rows = [
        _stage_probe_row(row, stage="C", mode="B4.1_selected_30_diagnostic", matrix_group=matrix_group)
        for row in iter_b4_pricing_formulation_matrix_rows_from_probe(
            source_probe_json,
            variants=tuple(variants),
            history_round=history_round,
            negative_feasibility_time_limit_sec=negative_feasibility_time_limit_sec,
            optimization_proof_time_limit_sec=optimization_proof_time_limit_sec,
            threads=int(threads),
            matrix_group=matrix_group,
            skip_keys=skip_keys,
        )
    ]
    return build_b4_1_report(rows)


def run_b4_1_stage_b_worker_tail_hidden_probe(
    instance: str | Path | dict,
    *,
    output_probe_json: str | Path,
    matrix_group: str = "B4.1 Stage B 30-scale worker-tail hidden-negative diagnostic",
    max_direct_tasks: int = 30,
    max_rounds: int = 2,
    wall_time_limit_sec: float | None = 60.0,
    max_columns_per_round: int = 32,
    seed_mode: str = "b0_incumbent_plus_singletons",
    skip_b0_direct: bool = True,
    tail_dual_stabilization_enabled: bool = False,
    tail_dual_stabilization_alpha: float = 0.7,
    tail_dual_stabilization_window: int = 5,
    skip_keys: Iterable[tuple[str, str, str, str]] = (),
) -> dict:
    raw, instance_path = _load_instance(instance)
    data = load_lunar_ice_data(raw)
    output_path = Path(output_probe_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    b0_direct = _diagnostic_b0_placeholder(data) if skip_b0_direct else None
    started = perf_counter()
    result = solve_b2_pricing_tail_baseline(
        data,
        b0_direct=b0_direct,
        max_direct_tasks=int(max_direct_tasks),
        max_rounds=int(max_rounds),
        wall_time_limit_sec=wall_time_limit_sec,
        max_columns_per_round=int(max_columns_per_round),
        mode=B2B_R2_MODE,
        seed_mode=str(seed_mode),
        tail_dual_stabilization_enabled=bool(tail_dual_stabilization_enabled),
        tail_dual_stabilization_alpha=float(tail_dual_stabilization_alpha),
        tail_dual_stabilization_window=int(tail_dual_stabilization_window),
    )
    elapsed = perf_counter() - started
    payload = _worker_tail_probe_payload(
        data,
        result,
        instance_path=instance_path,
        elapsed=elapsed,
        max_direct_tasks=max_direct_tasks,
        max_rounds=max_rounds,
        wall_time_limit_sec=wall_time_limit_sec,
        max_columns_per_round=max_columns_per_round,
        seed_mode=seed_mode,
        skip_b0_direct=skip_b0_direct,
        tail_dual_stabilization_enabled=tail_dual_stabilization_enabled,
        tail_dual_stabilization_alpha=tail_dual_stabilization_alpha,
        tail_dual_stabilization_window=tail_dual_stabilization_window,
    )
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return run_b4_1_stage_b_from_probe(
        output_path,
        matrix_group=matrix_group,
        variants=(),
        skip_keys=skip_keys,
    )


def run_b4_1_tree_closure_from_probe(
    source_probe_json: str | Path,
    *,
    matrix_group: str = "B4.1 Stage D 30-scale tree closure from root-tail probe",
    max_rounds: int = 1,
    wall_time_limit_sec: float | None = None,
    max_columns_per_round: int = 128,
    max_tree_nodes: int = 31,
    max_branch_depth: int = 4,
) -> dict:
    """Rebuild a B3 tree certificate from a saved active-column root probe."""

    probe_path = Path(source_probe_json)
    probe = json.loads(probe_path.read_text(encoding="utf-8"))
    instance_path = Path(str(probe.get("instance_path") or ""))
    if not str(instance_path):
        raise ValueError("source probe does not contain instance_path")
    raw, normalized_instance_path = _load_instance(instance_path)
    data = load_lunar_ice_data(raw)
    if probe.get("instance_id") not in {None, "", data.instance_id}:
        raise ValueError(
            f"source probe instance_id={probe.get('instance_id')!r} "
            f"does not match loaded instance_id={data.instance_id!r}"
        )
    active_payloads = probe.get("active_columns") or []
    if not active_payloads:
        raise ValueError("source probe does not contain active_columns")
    initial_columns = tuple(journey_column_from_solution_payload(data, row) for row in active_payloads)
    start = perf_counter()
    raw_result = solve_b3_branch_price_tree_baseline(
        data,
        initial_columns=initial_columns,
        max_direct_tasks=len(data.task_ids),
        max_rounds_per_node=int(max_rounds),
        wall_time_limit_sec=wall_time_limit_sec,
        max_columns_per_round=int(max_columns_per_round),
        max_tree_nodes=int(max_tree_nodes),
        max_branch_depth=int(max_branch_depth),
        use_complete_universe_audit=False,
        run_b2_root_diagnostic=False,
        solve_b0_direct_first=False,
    )
    root_node = (raw_result.get("nodes") or [{}])[0]
    final_judge = probe.get("final_judge") if isinstance(probe.get("final_judge"), dict) else {}
    row = _stage_a_row(
        raw_result,
        stage="D",
        matrix_group=matrix_group,
        instance_path=normalized_instance_path,
        scale=len(data.task_ids),
        mode="B4.1_30_tree_closure_from_probe",
        wall_time=perf_counter() - start,
        max_rounds=max_rounds,
        max_columns_per_round=max_columns_per_round,
        max_tree_nodes=max_tree_nodes,
        max_branch_depth=max_branch_depth,
    )
    row.update(
        {
            "source_probe_json": str(probe_path),
            "variant": "V4_root_tail_probe_tree_gate",
            "b4_1_matrix_cell": "B4.1_30_tree_closure_from_probe",
            "b4_1_proof_tail_component": "root_tail_no_negative_to_tree_gate",
            "b4_1_formulation_profile": "B3B_warm_started_true_dual_tree_gate",
            "b4_1_official_certificate_allowed": True,
            "active_column_count": len(initial_columns),
            "active_columns_after_merge": len(initial_columns),
            "columns_added": root_node.get("added_column_count", raw_result.get("added_column_count", "")),
            "underlying_certificate_scope": probe.get("certificate_scope") or "",
            "underlying_can_certify_no_negative": bool(final_judge.get("can_certify_no_negative")),
            "underlying_pricing_proof_kind": final_judge.get("pricing_proof_kind") or "",
            "underlying_frontier_coverage_complete": bool(
                final_judge.get("global_remaining_rc_lb_coverage_complete")
                or final_judge.get("negative_feasibility_full_space_proof_can_certify")
            ),
            "underlying_frontier_unsupported_region_count": _first_int(
                final_judge.get("frontier_unsupported_region_count")
            ),
        }
    )
    report = build_b4_1_report([row])
    report["tree_closure_raw_results"] = [raw_result]
    return report


def build_b4_1_report(rows: Iterable[dict]) -> dict:
    materialized = [_normalize_b4_1_row(row) for row in rows]
    summary_rows = _summary_rows(materialized)
    latest_frontier_rows = _latest_stage_b_frontier_rows(materialized)
    stage_counts = _count_by(materialized, "stage")
    mode_counts = _count_by(materialized, "mode")
    variant_counts = _count_by(materialized, "variant")
    hidden_miss_reason_counts = _aggregate_hidden_negative_miss_reason_counts(materialized)
    tail_dual_rows = [row for row in materialized if _bool_value(row.get("tail_dual_stabilization_enabled"))]
    redlines = {
        "certificate_leak_count": sum(int(row.get("certificate_leak") or 0) for row in materialized),
        "manual_rc_fail_count": sum(int(row.get("manual_rc_fail") or 0) for row in materialized),
        "pricing_rc_fail_count": sum(int(row.get("pricing_rc_fail") or 0) for row in materialized),
        "diagnostic_claimed_certificate_count": sum(
            int(row.get("diagnostic_claimed_certificate") or 0) for row in materialized
        ),
        "resource_guard_stopped_count": sum(
            1 for row in materialized if str(row.get("algorithm_status") or "") == "RESOURCE_GUARD_STOPPED"
        ),
        "exception_fail_closed_count": sum(
            1 for row in materialized if str(row.get("algorithm_status") or "") == "EXCEPTION_FAIL_CLOSED"
        ),
        "stage_a_tree_closure_miss_count": sum(
            1
            for row in materialized
            if str(row.get("stage") or "") == "A"
            and str(row.get("mode") or "") in {B41_STAGE_A_B3B_BASELINE, B41_STAGE_A_B4V2_HARVEST}
            and str(row.get("certificate_scope") or "") != CertificateScope.BPC_TREE_OPTIMAL.value
        ),
        "tail_dual_certificate_leak_count": sum(
            1
            for row in tail_dual_rows
            if _bool_value(row.get("can_certify_no_negative"))
            or _bool_value(row.get("tail_dual_no_column_can_certify"))
            or not _bool_value(row.get("worker_dual_only"))
            or not _bool_value(row.get("true_dual_rc_recomputed"))
            or str(row.get("official_dual_source") or "") != "current_true_rmp_dual"
        ),
    }
    stage_a_rows = [row for row in materialized if row.get("stage") == "A"]
    stage_b_rows = [row for row in materialized if row.get("stage") == "B"]
    stage_c_rows = [row for row in materialized if row.get("stage") == "C"]
    stage_a_coverage = _stage_a_regression_coverage(stage_a_rows)
    stage_b_coverage = _stage_b_matrix_coverage(stage_b_rows)
    diagnostics = {
        "negative_discovery_budget_exhausted_count": sum(
            1 for row in materialized if row.get("negative_discovery_budget_exhausted") is True
        ),
        "feasibility_proof_budget_exhausted_count": sum(
            1 for row in materialized if row.get("feasibility_proof_budget_exhausted") is True
        ),
        "optimization_proof_missing_count": sum(
            1 for row in materialized if row.get("optimization_proof_missing") is True
        ),
        "positive_best_rc_negative_bound_count": sum(
            1
            for row in materialized
            if (_float_or_none(row.get("pending_complete_min_rc")) or 0.0) >= 0.0
            and (_float_or_none(row.get("global_remaining_rc_lb")) or 0.0) < 0.0
        ),
        "hidden_negative_miss_reason_counts": hidden_miss_reason_counts,
        "hidden_negative_top_miss_reason": _top_hidden_negative_miss_reason(hidden_miss_reason_counts),
        "hidden_negative_worker_not_generated_count": hidden_miss_reason_counts.get("worker_not_generated", 0),
        "hidden_negative_pruned_by_dominance_count": hidden_miss_reason_counts.get("pruned_by_dominance", 0),
        "hidden_negative_pricing_timeout_only_count": hidden_miss_reason_counts.get("pricing_timeout_only", 0),
        "tail_dual_enabled_count": len(tail_dual_rows),
        "tail_dual_worker_only_count": sum(1 for row in tail_dual_rows if _bool_value(row.get("worker_dual_only"))),
        "tail_dual_true_dual_recomputed_count": sum(
            1 for row in tail_dual_rows if _bool_value(row.get("true_dual_rc_recomputed"))
        ),
        "tail_dual_no_column_can_certify_count": sum(
            1 for row in tail_dual_rows if _bool_value(row.get("tail_dual_no_column_can_certify"))
        ),
        "tail_dual_official_true_dual_source_count": sum(
            1 for row in tail_dual_rows if str(row.get("official_dual_source") or "") == "current_true_rmp_dual"
        ),
        "stage_a_required_regression_modes": list(B41_STAGE_A_REQUIRED_REGRESSION_MODES),
        "stage_a_observed_regression_modes": stage_a_coverage["observed"],
        "stage_a_missing_regression_modes": stage_a_coverage["missing"],
        "stage_a_missing_regression_mode_count": len(stage_a_coverage["missing"]),
        "stage_b_required_matrix_cells": list(B41_STAGE_B_REQUIRED_MATRIX_CELLS),
        "stage_b_observed_matrix_cells": stage_b_coverage["observed"],
        "stage_b_missing_matrix_cells": stage_b_coverage["missing"],
        "stage_b_missing_matrix_cell_count": len(stage_b_coverage["missing"]),
        "thirty_scale_underlying_node_lp_certified_count": sum(
            1
            for row in materialized
            if _is_30_scale_row(row)
            and str(row.get("underlying_certificate_scope") or "") == CertificateScope.BPC_NODE_LP_CERTIFIED.value
        ),
        "thirty_scale_underlying_exhaustive_no_negative_count": sum(
            1
            for row in materialized
            if _is_30_scale_row(row)
            and _bool_value(row.get("underlying_can_certify_no_negative"))
            and str(row.get("underlying_pricing_proof_kind") or "") == "EXHAUSTIVE_NO_NEGATIVE"
        ),
    }
    acceptance = {
        "stage_a_regression_clean": bool(stage_a_rows)
        and not stage_a_coverage["missing"]
        and all(int(value or 0) == 0 for value in redlines.values()),
        "stage_b_diagnostic_clean": bool(stage_b_rows)
        and redlines["diagnostic_claimed_certificate_count"] == 0,
        "stage_b_matrix_complete": bool(stage_b_rows) and not stage_b_coverage["missing"],
        "stage_c_diagnostic_clean": bool(stage_c_rows)
        and redlines["diagnostic_claimed_certificate_count"] == 0,
        "b4_1_code_path_exercised": bool(materialized),
        "b4_1_full_experiment_complete": False,
        "requires_long_experiment_completion": True,
    }
    requirement_audit = _build_requirement_audit(
        rows=materialized,
        stage_a_rows=stage_a_rows,
        stage_b_rows=stage_b_rows,
        stage_c_rows=stage_c_rows,
        redlines=redlines,
        diagnostics=diagnostics,
        acceptance=acceptance,
    )
    return {
        "schema_version": "lunar_ice_bpc.b4_1_true_dual_proof_tail.v1",
        "rows": materialized,
        "row_count": len(materialized),
        "stage_counts": stage_counts,
        "mode_counts": mode_counts,
        "variant_counts": variant_counts,
        "summary_rows": summary_rows,
        "latest_frontier_rows": latest_frontier_rows,
        "redlines": redlines,
        "diagnostics": diagnostics,
        "requirement_audit": requirement_audit,
        "acceptance": acceptance,
    }


def write_b4_1_artifacts(
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
    with rows_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in report["rows"]:
            writer.writerow({key: _csv_value(row.get(key)) for key in CSV_COLUMNS})
    summary_json.write_text(
        json.dumps({key: value for key, value in report.items() if key != "rows"}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    report_md.write_text(render_b4_1_markdown(report, rows_csv=rows_csv, summary_json=summary_json), encoding="utf-8")


def build_b4_1_restricted_region_taskset_diagnostic(source_probe_json: str | Path) -> dict:
    """Summarize harvested true-dual task-set regions from an existing probe.

    This is a pure diagnostic parser. It never upgrades a frontier row to a
    certificate and never interprets restricted/no-good no-column results as a
    no-negative proof.
    """

    source = Path(source_probe_json)
    payload = json.loads(source.read_text(encoding="utf-8"))
    final_judge = payload.get("final_judge") if isinstance(payload.get("final_judge"), dict) else {}
    harvest_reports = final_judge.get("harvest_reports") if isinstance(final_judge.get("harvest_reports"), list) else []
    negatives = _restricted_region_harvested_negatives(harvest_reports)
    task_frequency = _restricted_region_task_frequency(negatives)
    pairwise_overlap = _restricted_region_pairwise_overlap(negatives)
    phase_rows = _restricted_region_phase_rows(final_judge)
    negative_time_limit_rows = [
        row
        for row in phase_rows
        if row.get("status") == "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED"
        and (_float_or_none(row.get("best_reduced_cost")) or 0.0) < -1.0e-9
    ]
    incomplete_time_limit_rows = [
        row
        for row in phase_rows
        if row.get("status") == "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED"
        and (_float_or_none(row.get("dual_bound")) or 0.0) < -1.0e-9
    ]
    max_frequency = max((row["count"] for row in task_frequency), default=0)
    repeated_tasks = [row for row in task_frequency if int(row["count"]) >= 2]
    hot_tasks = [row for row in task_frequency if max_frequency and int(row["count"]) == max_frequency]
    high_overlap_pairs = [
        row for row in pairwise_overlap if float(row.get("jaccard") or 0.0) >= 0.5
    ]
    recommended_next_actions = _restricted_region_next_actions(
        negatives=negatives,
        hot_tasks=hot_tasks,
        high_overlap_pairs=high_overlap_pairs,
        incomplete_time_limit_rows=incomplete_time_limit_rows,
    )
    return {
        "schema_version": "lunar_ice_bpc.b4_1_restricted_region_taskset_diagnostic.v1",
        "source_probe_json": str(source),
        "instance_id": payload.get("instance_id") or final_judge.get("instance_id") or "",
        "diagnostic_only": True,
        "official_certificate_allowed": False,
        "can_claim_certificate": False,
        "no_negative_certificate_claimed": False,
        "certificate_scope": payload.get("certificate_scope") or "",
        "pricing_proof_kind": final_judge.get("pricing_proof_kind") or "",
        "global_remaining_rc_lb": final_judge.get("global_remaining_rc_lb"),
        "frontier_coverage_complete": bool(final_judge.get("global_remaining_rc_lb_coverage_complete")),
        "frontier_unsupported_region_count": _first_int(final_judge.get("frontier_unsupported_region_count")),
        "compact_final_judge_profile": final_judge.get("compact_final_judge_profile") or "",
        "compact_final_judge_phase_mode": final_judge.get("compact_final_judge_phase_mode") or "",
        "compact_optimization_harvest_no_good_scope": final_judge.get("compact_optimization_harvest_no_good_scope") or "",
        "harvest_selected_count": _first_int(final_judge.get("harvest_selected_count")),
        "harvest_selected_new_task_set_count": _first_int(final_judge.get("harvest_selected_new_task_set_count")),
        "harvest_selected_replacement_task_set_count": _first_int(
            final_judge.get("harvest_selected_replacement_task_set_count")
        ),
        "harvest_pricing_rc_audit_pass": final_judge.get("harvest_pricing_rc_audit_pass"),
        "harvest_pricing_rc_max_abs_diff": final_judge.get("harvest_pricing_rc_max_abs_diff"),
        "harvested_negative_count": len(negatives),
        "harvested_negatives": negatives,
        "task_frequency": task_frequency,
        "pairwise_overlap": pairwise_overlap,
        "restricted_region_rows": phase_rows,
        "cluster_summary": {
            "max_task_frequency": max_frequency,
            "hot_tasks": hot_tasks,
            "repeated_tasks": repeated_tasks,
            "high_overlap_pairs": high_overlap_pairs,
            "negative_time_limit_region_count": len(negative_time_limit_rows),
            "incomplete_time_limit_region_count": len(incomplete_time_limit_rows),
        },
        "recommended_next_actions": recommended_next_actions,
    }


def write_b4_1_restricted_region_taskset_diagnostic(
    diagnostic: dict,
    *,
    summary_json: str | Path,
    report_md: str | Path,
) -> None:
    summary_path = Path(summary_json)
    report_path = Path(report_md)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(diagnostic, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    report_path.write_text(render_b4_1_restricted_region_taskset_markdown(diagnostic), encoding="utf-8")


def run_b4_1_targeted_restricted_region_probe(
    source_probe_json: str | Path,
    *,
    variants: Iterable[str] = (
        "V2_latest_service_start_slot_bound",
        "V4_combined_endpoint_pair_latest_start_time_window",
        "V4_current_strengthening",
    ),
    history_round: int = -1,
    time_limit_sec: float = 120.0,
    threads: int = 1,
    negative_eps: float = 1.0e-6,
    max_regions: int = 0,
    target_region_ids: Iterable[str] = (),
) -> dict:
    """Run true-dual restricted-region formulation diagnostics from a probe.

    Each row forbids a prefix of harvested task sets and re-solves compact
    pricing under the same true RMP dual.  Because every nonzero prefix is a
    restricted/no-good space, these rows are diagnostic only and can never close
    the official no-negative certificate.
    """

    source = Path(source_probe_json)
    payload = json.loads(source.read_text(encoding="utf-8"))
    diagnostic = build_b4_1_restricted_region_taskset_diagnostic(source)
    instance_path = payload.get("instance_path")
    if not instance_path:
        raise ValueError(f"source probe has no instance_path: {source}")
    data = load_lunar_ice_data(json.loads(Path(instance_path).read_text(encoding="utf-8")))
    history = payload.get("history") if isinstance(payload.get("history"), list) else []
    history_row = _select_history_row(history, int(history_round))
    dual_context = history_row.get("dual_context")
    if not isinstance(dual_context, dict):
        raise ValueError("selected history row has no dual_context")
    duals = JourneyDuals(
        cover={str(key): float(value) for key, value in (dual_context.get("task_duals") or {}).items()},
        fleet_limit=float(dual_context.get("fleet_dual") or 0.0),
        cuts={str(key): float(value) for key, value in (dual_context.get("cut_duals") or {}).items()},
    )
    negatives = list(diagnostic.get("harvested_negatives") or [])
    target_regions = _targeted_restricted_regions_from_diagnostic(diagnostic, max_regions=max_regions)
    target_regions = _filter_targeted_restricted_regions(
        target_regions,
        target_region_ids=target_region_ids,
    )
    rows: list[dict] = []
    for region in target_regions:
        prefix_count = int(region["forbidden_task_set_count"])
        forbidden_task_sets = tuple(tuple(row.get("task_set") or []) for row in negatives[:prefix_count])
        for variant in tuple(str(item) for item in variants):
            config = B41_TARGETED_RESTRICTED_REGION_VARIANT_CONFIGS.get(variant)
            if config is None:
                raise ValueError(f"unknown B4.1 targeted restricted-region variant: {variant}")
            start = perf_counter()
            result = solve_highs_compact_single_journey_pricing(
                data,
                duals,
                time_limit_sec=float(time_limit_sec),
                threads=int(threads),
                mip_gap=0.0,
                negative_eps=float(negative_eps),
                flow_connectivity=False,
                mtz_connectivity=bool(config["mtz_connectivity"]),
                mtz_endpoint_order_cuts=bool(config["mtz_endpoint_order_cuts"]),
                pair_adjacency_cuts=bool(config["pair_adjacency_cuts"]),
                latest_service_start_slot_bound=bool(config["latest_service_start_slot_bound"]),
                time_window_arc_pruning=bool(config["time_window_arc_pruning"]),
                service_start_depot_travel_lb=bool(config["service_start_depot_travel_lb"]),
                task_to_depot_return_travel_lb=bool(config["task_to_depot_return_travel_lb"]),
                pair_route_duration_lb=bool(config["pair_route_duration_lb"]),
                pair_weighted_completion_lb=bool(config["pair_weighted_completion_lb"]),
                sortie_slot_position_bounds=bool(config["sortie_slot_position_bounds"]),
                demand_cover_cut=bool(config["demand_cover_cut"]),
                single_task_energy_lb=bool(config["single_task_energy_lb"]),
                single_task_shadow_lb=bool(config["single_task_shadow_lb"]),
                pair_energy_lb=bool(config["pair_energy_lb"]),
                pair_shadow_lb=bool(config["pair_shadow_lb"]),
                pair_energy_infeasible_cut=bool(config["pair_energy_infeasible_cut"]),
                pair_time_window_infeasible_cut=bool(config["pair_time_window_infeasible_cut"]),
                pair_time_window_precedence_cut=bool(config["pair_time_window_precedence_cut"]),
                triple_time_window_infeasible_cut=bool(config["triple_time_window_infeasible_cut"]),
                quad_time_window_infeasible_cut=bool(config["quad_time_window_infeasible_cut"]),
                pair_shadow_infeasible_cut=bool(config["pair_shadow_infeasible_cut"]),
                triple_shadow_infeasible_cut=bool(config["triple_shadow_infeasible_cut"]),
                triple_energy_infeasible_cut=bool(config["triple_energy_infeasible_cut"]),
                negative_feasibility_search=False,
                forbidden_task_sets=forbidden_task_sets,
            )
            rows.append(
                _targeted_restricted_region_row(
                    result,
                    source_probe_json=source,
                    instance_id=str(payload.get("instance_id") or data.instance_id),
                    history_round=history_row.get("round"),
                    region=region,
                    variant=variant,
                    formulation_kind=str(config["formulation_kind"]),
                    wall_time=perf_counter() - start,
                )
            )
    return {
        "schema_version": "lunar_ice_bpc.b4_1_targeted_restricted_region_probe.v1",
        "source_probe_json": str(source),
        "instance_id": payload.get("instance_id") or data.instance_id,
        "diagnostic_only": True,
        "official_certificate_allowed": False,
        "can_claim_certificate": False,
        "target_region_ids": [str(item) for item in target_region_ids],
        "rows": rows,
        "row_count": len(rows),
        "taskset_diagnostic": diagnostic,
        "summary": _targeted_restricted_region_summary(rows),
        "redlines": {
            "certificate_claim_count": sum(1 for row in rows if row.get("can_claim_certificate") is True),
            "restricted_no_good_claimed_certificate_count": sum(
                1
                for row in rows
                if int(row.get("forbidden_task_set_count") or 0) > 0
                and row.get("can_certify_no_negative") is True
            ),
        },
    }


def write_b4_1_targeted_restricted_region_probe(
    report: dict,
    *,
    summary_json: str | Path,
    report_md: str | Path,
) -> None:
    summary_path = Path(summary_json)
    report_path = Path(report_md)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    report_path.write_text(render_b4_1_targeted_restricted_region_markdown(report), encoding="utf-8")


def build_b4_1_restricted_region_bound_ledger(
    source_probe_json: str | Path,
    *,
    targeted_probe_jsons: Iterable[str | Path] = (),
    max_regions: int = 0,
) -> dict:
    """Build a diagnostic ledger of the strongest known restricted-region bounds.

    The ledger deliberately reuses already-computed source phase bounds instead
    of re-solving compact pricing.  Targeted probe rows may be supplied as
    extra diagnostic candidates.  Restricted/no-good regions never certify the
    full pricing space, even when a row has a nonnegative incumbent RC.
    """

    source = Path(source_probe_json)
    diagnostic = build_b4_1_restricted_region_taskset_diagnostic(source)
    regions = _targeted_restricted_regions_from_diagnostic(diagnostic, max_regions=max_regions)
    targeted_rows = _restricted_region_bound_ledger_targeted_rows(
        source,
        targeted_probe_jsons=targeted_probe_jsons,
    )
    rows = [
        _restricted_region_bound_ledger_row(region, targeted_rows=targeted_rows)
        for region in regions
    ]
    selected_bounds = [
        _first_float(row.get("best_known_dual_bound"))
        for row in rows
        if _first_float(row.get("best_known_dual_bound")) is not None
    ]
    best_known_global_lb = (
        None
        if not selected_bounds
        else round(min(float(value) for value in selected_bounds), 9)
    )
    certificate_claim_count = sum(1 for row in rows if row.get("can_claim_certificate") is True)
    source_reuse_count = sum(1 for row in rows if row.get("source_bound_reused") is True)
    targeted_improvement_count = sum(
        1 for row in rows if row.get("targeted_bound_improved_over_source") is True
    )
    return {
        "schema_version": "lunar_ice_bpc.b4_1_restricted_region_bound_ledger.v1",
        "source_probe_json": str(source),
        "targeted_probe_jsons": [str(Path(path)) for path in targeted_probe_jsons],
        "instance_id": diagnostic.get("instance_id") or "",
        "diagnostic_only": True,
        "official_certificate_allowed": False,
        "can_claim_certificate": False,
        "no_negative_certificate_claimed": False,
        "certificate_allowed": False,
        "pricing_proof_kind": "FRONTIER_BOUND_INCOMPLETE",
        "frontier_coverage_complete": False,
        "frontier_unsupported_region_count": max(1, len(rows)) if rows else 0,
        "best_known_global_remaining_rc_lb": best_known_global_lb,
        "global_remaining_rc_lb": best_known_global_lb,
        "global_remaining_rc_lb_valid": bool(best_known_global_lb is not None),
        "global_remaining_rc_lb_coverage_complete": False,
        "region_count": len(rows),
        "source_bound_reuse_count": source_reuse_count,
        "targeted_bound_improvement_count": targeted_improvement_count,
        "rows": rows,
        "summary": {
            "certificate_claim_count": certificate_claim_count,
            "source_bound_reuse_count": source_reuse_count,
            "targeted_bound_improvement_count": targeted_improvement_count,
            "best_known_global_remaining_rc_lb": best_known_global_lb,
            "selected_bound_sources": dict(
                Counter(str(row.get("selected_bound_source") or "none") for row in rows)
            ),
        },
        "redlines": {
            "certificate_claim_count": certificate_claim_count,
            "official_bound_claim_count": sum(
                1 for row in rows if row.get("frontier_lb_official") is True
            ),
        },
        "note": (
            "Diagnostic-only restricted-region bound ledger. Source phase and targeted "
            "restricted/no-good bounds can guide proof-tail work but cannot close the "
            "full-space no-negative certificate."
        ),
    }


def write_b4_1_restricted_region_bound_ledger(
    ledger: dict,
    *,
    summary_json: str | Path,
    report_md: str | Path,
) -> None:
    summary_path = Path(summary_json)
    report_path = Path(report_md)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    report_path.write_text(render_b4_1_restricted_region_bound_ledger_markdown(ledger), encoding="utf-8")


def render_b4_1_restricted_region_bound_ledger_markdown(ledger: dict) -> str:
    lines = [
        "# B4.1 Restricted-Region Bound Ledger",
        "",
        "## Boundary",
        "",
        f"- Source probe: `{ledger.get('source_probe_json')}`",
        "- This ledger is diagnostic-only.",
        "- It may reuse source phase bounds and targeted restricted/no-good probe bounds.",
        "- It cannot claim an official full-space no-negative certificate.",
        "",
        "## Summary",
        "",
        f"- pricing_proof_kind: `{ledger.get('pricing_proof_kind')}`",
        f"- best_known_global_remaining_rc_lb: `{ledger.get('best_known_global_remaining_rc_lb')}`",
        f"- source_bound_reuse_count: `{ledger.get('source_bound_reuse_count')}`",
        f"- targeted_bound_improvement_count: `{ledger.get('targeted_bound_improvement_count')}`",
        "",
        "| region | forbidden sets | selected source | best known LB | source LB | targeted best LB | targeted variant | cert allowed |",
        "| --- | ---: | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in ledger.get("rows") or []:
        lines.append(
            "| {region} | {forbidden} | {source} | {best} | {src_lb} | {target_lb} | {variant} | {cert} |".format(
                region=row.get("region_id"),
                forbidden=row.get("forbidden_task_set_count"),
                source=row.get("selected_bound_source"),
                best=row.get("best_known_dual_bound"),
                src_lb=row.get("source_phase_dual_bound"),
                target_lb=row.get("targeted_best_dual_bound"),
                variant=row.get("targeted_best_variant"),
                cert=row.get("official_certificate_allowed"),
            )
        )
    lines.extend(["", "## Redlines", "", "| metric | value | required |", "| --- | ---: | ---: |"])
    for key, value in (ledger.get("redlines") or {}).items():
        lines.append(f"| {key} | {value} | 0 |")
    return "\n".join(lines) + "\n"


def render_b4_1_targeted_restricted_region_markdown(report: dict) -> str:
    lines = [
        "# B4.1 Targeted Restricted-Region Proof Probe",
        "",
        "## Boundary",
        "",
        f"- Source probe: `{report.get('source_probe_json')}`",
        "- This report re-solves restricted/no-good pricing regions under true RMP duals.",
        "- It is diagnostic-only and cannot claim an official no-negative certificate.",
        "",
        "## Summary",
        "",
        "| region | forbidden sets | rows | best bound | best RC | best variant | improved rows | time-limit rows |",
        "| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |",
    ]
    for row in report.get("summary") or []:
        lines.append(
            "| {region} | {forbidden} | {rows} | {bound} | {rc} | {variant} | {improved} | {tl} |".format(
                region=row.get("region_id"),
                forbidden=row.get("forbidden_task_set_count"),
                rows=row.get("row_count"),
                bound=row.get("best_dual_bound"),
                rc=row.get("best_reduced_cost"),
                variant=row.get("best_bound_variant"),
                improved=row.get("source_bound_improved_count"),
                tl=row.get("time_limit_row_count"),
            )
        )
    lines.extend(
        [
            "",
            "## Rows",
            "",
            "| region | variant | status | exact | best RC | dual bound | source bound | delta | pair TW cuts | triple TW cuts | quad TW cuts | wall s | cert allowed |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in report.get("rows") or []:
        lines.append(
            "| {region} | {variant} | {status} | {exact} | {rc} | {bound} | {src} | {delta} | {pair_tw} | {triple_tw} | {quad_tw} | {wall} | {cert} |".format(
                region=row.get("region_id"),
                variant=row.get("variant"),
                status=row.get("status"),
                exact=row.get("exact_status"),
                rc=row.get("best_reduced_cost"),
                bound=row.get("dual_bound"),
                src=row.get("source_phase_dual_bound"),
                delta=row.get("dual_bound_delta_vs_source"),
                pair_tw=row.get("pair_time_window_infeasible_cut_count"),
                triple_tw=row.get("triple_time_window_infeasible_cut_count"),
                quad_tw=row.get("quad_time_window_infeasible_cut_count"),
                wall=row.get("wall_time_sec"),
                cert=row.get("official_certificate_allowed"),
            )
        )
    negative_rows = [
        row for row in (report.get("rows") or [])
        if row.get("targeted_negative_task_set")
    ]
    if negative_rows:
        lines.extend(
            [
                "",
                "## Targeted Negative Columns",
                "",
                "| region | variant | true RC | task count | forbidden seen | task set |",
                "| --- | --- | ---: | ---: | --- | --- |",
            ]
        )
        for row in negative_rows:
            task_set = row.get("targeted_negative_task_set") or []
            lines.append(
                "| {region} | {variant} | {rc} | {size} | {seen} | {tasks} |".format(
                    region=row.get("region_id"),
                    variant=row.get("variant"),
                    rc=row.get("targeted_negative_true_rc"),
                    size=row.get("targeted_negative_task_set_size"),
                    seen=row.get("targeted_negative_task_set_forbidden_seen"),
                    tasks=", ".join(str(task) for task in task_set),
                )
            )
    lines.extend(["", "## Redlines", "", "| metric | value | required |", "| --- | ---: | ---: |"])
    for key, value in (report.get("redlines") or {}).items():
        lines.append(f"| {key} | {value} | 0 |")
    return "\n".join(lines) + "\n"


def render_b4_1_restricted_region_taskset_markdown(diagnostic: dict) -> str:
    lines = [
        "# B4.1 Restricted Region Task-Set Diagnostic",
        "",
        "## Boundary",
        "",
        f"- Source probe: `{diagnostic.get('source_probe_json')}`",
        f"- certificate_scope: `{diagnostic.get('certificate_scope')}`",
        f"- pricing_proof_kind: `{diagnostic.get('pricing_proof_kind')}`",
        f"- global_remaining_rc_lb: `{diagnostic.get('global_remaining_rc_lb')}`",
        f"- frontier_unsupported_region_count: `{diagnostic.get('frontier_unsupported_region_count')}`",
        "- This report is diagnostic-only. No no-negative certificate is claimed.",
        "",
        "## Harvested Negatives",
        "",
        "| id | true RC | pricing RC | size | would enter | task set |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in diagnostic.get("harvested_negatives") or []:
        lines.append(
            "| {id} | {true_rc} | {pricing_rc} | {size} | {enter} | {tasks} |".format(
                id=row.get("id"),
                true_rc=row.get("true_reduced_cost"),
                pricing_rc=row.get("pricing_reduced_cost"),
                size=row.get("task_set_size"),
                enter=row.get("would_enter_master"),
                tasks=", ".join(row.get("task_set") or []),
            )
        )
    lines.extend(["", "## Task Frequency", "", "| task | count |", "| --- | ---: |"])
    for row in diagnostic.get("task_frequency") or []:
        lines.append(f"| {row.get('task')} | {row.get('count')} |")
    lines.extend(["", "## Pairwise Overlap", "", "| pair | intersection | Jaccard | shared tasks |", "| --- | ---: | ---: | --- |"])
    for row in diagnostic.get("pairwise_overlap") or []:
        lines.append(
            "| {pair} | {size} | {jaccard} | {shared} |".format(
                pair=row.get("pair"),
                size=row.get("intersection_size"),
                jaccard=row.get("jaccard"),
                shared=", ".join(row.get("shared_tasks") or []),
            )
        )
    lines.extend(
        [
            "",
            "## Restricted Region Rows",
            "",
            "| phase | status | exact | best RC | dual bound | forbidden task sets | wall s |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in diagnostic.get("restricted_region_rows") or []:
        lines.append(
            "| {phase} | {status} | {exact} | {best} | {bound} | {forbidden} | {wall} |".format(
                phase=row.get("phase"),
                status=row.get("status"),
                exact=row.get("exact_status"),
                best=row.get("best_reduced_cost"),
                bound=row.get("dual_bound"),
                forbidden=row.get("forbidden_task_set_count"),
                wall=row.get("wall_time_sec"),
            )
        )
    summary = diagnostic.get("cluster_summary") or {}
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Hot tasks: `{', '.join(row.get('task') for row in summary.get('hot_tasks') or []) or 'none'}`.",
            f"- Repeated tasks: `{', '.join(row.get('task') for row in summary.get('repeated_tasks') or []) or 'none'}`.",
            f"- High-overlap pairs: `{', '.join(row.get('pair') for row in summary.get('high_overlap_pairs') or []) or 'none'}`.",
            f"- Negative time-limit regions: `{summary.get('negative_time_limit_region_count', 0)}`.",
            f"- Incomplete time-limit regions: `{summary.get('incomplete_time_limit_region_count', 0)}`.",
            "",
            "## Next Actions",
            "",
        ]
    )
    for action in diagnostic.get("recommended_next_actions") or []:
        lines.append(f"- {action}")
    return "\n".join(lines) + "\n"


def _restricted_region_harvested_negatives(harvest_reports: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for index, report in enumerate(harvest_reports, start=1):
        if not isinstance(report, dict):
            continue
        task_set = tuple(sorted(str(task) for task in (report.get("task_set") or []) if str(task)))
        if not task_set:
            continue
        rows.append(
            {
                "id": f"H{index}",
                "true_reduced_cost": _first_float(report.get("true_reduced_cost")),
                "pricing_reduced_cost": _first_float(report.get("pricing_reduced_cost")),
                "manual_pricing_rc_abs_diff": _first_float(report.get("manual_pricing_rc_abs_diff")),
                "task_set_size": len(task_set),
                "task_set": list(task_set),
                "would_enter_master": bool(report.get("would_enter_master")),
                "would_change_active_support": bool(report.get("would_change_active_support")),
                "selected_after_addability_audit": bool(report.get("selected_after_addability_audit")),
                "current_master_contains_signature": bool(report.get("current_master_contains_signature")),
                "pool_contains_signature": bool(report.get("pool_contains_signature")),
                "reject_reason": report.get("reject_reason") or "",
            }
        )
    return rows


def _restricted_region_task_frequency(negatives: list[dict]) -> list[dict]:
    counter: Counter[str] = Counter()
    for row in negatives:
        counter.update(str(task) for task in (row.get("task_set") or []))
    return [
        {"task": task, "count": int(count)}
        for task, count in sorted(counter.items(), key=lambda item: (-int(item[1]), str(item[0])))
    ]


def _restricted_region_pairwise_overlap(negatives: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for left, right in combinations(negatives, 2):
        left_tasks = set(str(task) for task in (left.get("task_set") or []))
        right_tasks = set(str(task) for task in (right.get("task_set") or []))
        union = left_tasks | right_tasks
        intersection = left_tasks & right_tasks
        jaccard = 0.0 if not union else len(intersection) / len(union)
        rows.append(
            {
                "pair": f"{left.get('id')}-{right.get('id')}",
                "left_id": left.get("id"),
                "right_id": right.get("id"),
                "intersection_size": len(intersection),
                "union_size": len(union),
                "jaccard": round(float(jaccard), 6),
                "shared_tasks": sorted(intersection),
            }
        )
    return rows


def _restricted_region_phase_rows(final_judge: dict) -> list[dict]:
    payloads = final_judge.get("compact_pricing_phase_payloads")
    if not isinstance(payloads, dict):
        return []
    rows: list[dict] = []
    for phase, payload in payloads.items():
        if not isinstance(payload, dict):
            continue
        rows.append(
            {
                "phase": str(phase),
                "status": payload.get("status") or payload.get("algorithm_status") or "",
                "exact_status": payload.get("exact_status") or "",
                "best_reduced_cost": _first_float(payload.get("best_reduced_cost")),
                "dual_bound": _first_float(payload.get("dual_bound"), payload.get("bound")),
                "wall_time_sec": _first_float(payload.get("wall_time_sec"), payload.get("wall_time")),
                "forbidden_task_set_count": _first_int(payload.get("forbidden_task_set_count")),
                "forbidden_task_sets_can_certify_full_space": bool(
                    payload.get("forbidden_task_sets_can_certify_full_space")
                ),
                "model_status_name": payload.get("model_status_name") or "",
            }
        )
    return rows


def _restricted_region_next_actions(
    *,
    negatives: list[dict],
    hot_tasks: list[dict],
    high_overlap_pairs: list[dict],
    incomplete_time_limit_rows: list[dict],
) -> list[str]:
    actions = [
        "Keep this diagnostic non-certifying until an unrestricted true-dual no-negative proof closes.",
    ]
    if incomplete_time_limit_rows:
        actions.append(
            "Target the time-limit restricted regions first; bound movement there is more important than finding more columns."
        )
    if high_overlap_pairs:
        actions.append(
            "Compare V2 and V4 proof rows on the high-overlap task-set cluster before adding more harvest stages."
        )
    if hot_tasks:
        actions.append(
            "Audit resource/time-window bounds around repeated hot tasks: "
            + ", ".join(str(row.get("task")) for row in hot_tasks)
            + "."
        )
    if negatives and not high_overlap_pairs:
        actions.append("Cluster harvested task sets by overlap and test formulation rows per cluster.")
    return actions


def _targeted_restricted_regions_from_diagnostic(diagnostic: dict, *, max_regions: int = 0) -> list[dict]:
    negatives = list(diagnostic.get("harvested_negatives") or [])
    by_prefix: dict[int, dict] = {}
    for row in diagnostic.get("restricted_region_rows") or []:
        prefix = _first_int(row.get("forbidden_task_set_count"))
        if prefix < 0 or prefix > len(negatives):
            continue
        status = str(row.get("status") or "")
        dual_bound = _first_float(row.get("dual_bound"))
        best_rc = _first_float(row.get("best_reduced_cost"))
        if status != "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED" and not (
            dual_bound is not None and dual_bound < -1.0e-9
        ):
            continue
        by_prefix[prefix] = {
            "region_id": f"prefix_{prefix}",
            "forbidden_task_set_count": prefix,
            "source_phase": row.get("phase") or "",
            "source_phase_status": status,
            "source_phase_exact_status": row.get("exact_status") or "",
            "source_phase_best_reduced_cost": best_rc,
            "source_phase_dual_bound": dual_bound,
            "source_phase_wall_time_sec": _first_float(row.get("wall_time_sec")),
            "forbidden_task_sets": [item.get("task_set") for item in negatives[:prefix]],
        }
    regions = [
        by_prefix[prefix]
        for prefix in sorted(
            by_prefix,
            key=lambda item: (
                0
                if str(by_prefix[item].get("source_phase_status") or "")
                == "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED"
                else 1,
                item,
            ),
        )
        if prefix > 0
    ]
    if not regions and negatives:
        regions = [
            {
                "region_id": f"prefix_{len(negatives)}",
                "forbidden_task_set_count": len(negatives),
                "source_phase": "",
                "source_phase_status": "",
                "source_phase_exact_status": "",
                "source_phase_best_reduced_cost": None,
                "source_phase_dual_bound": diagnostic.get("global_remaining_rc_lb"),
                "source_phase_wall_time_sec": None,
                "forbidden_task_sets": [item.get("task_set") for item in negatives],
            }
        ]
    if int(max_regions) > 0:
        return regions[: int(max_regions)]
    return regions


def _filter_targeted_restricted_regions(
    regions: list[dict],
    *,
    target_region_ids: Iterable[str],
) -> list[dict]:
    requested = tuple(str(item).strip() for item in target_region_ids if str(item).strip())
    if not requested:
        return regions
    requested_set = set(requested)
    filtered = [row for row in regions if str(row.get("region_id") or "") in requested_set]
    missing = sorted(requested_set - {str(row.get("region_id") or "") for row in filtered})
    if missing:
        available = ", ".join(str(row.get("region_id") or "") for row in regions) or "none"
        raise ValueError(
            "requested B4.1 targeted restricted-region id(s) not found: "
            + ", ".join(missing)
            + f"; available: {available}"
        )
    return filtered


def _targeted_restricted_region_row(
    result: dict,
    *,
    source_probe_json: Path,
    instance_id: str,
    history_round: object,
    region: dict,
    variant: str,
    formulation_kind: str,
    wall_time: float,
) -> dict:
    source_bound = _first_float(region.get("source_phase_dual_bound"))
    dual_bound = _first_float(result.get("dual_bound"), result.get("bound"))
    best_rc = _first_float(result.get("best_reduced_cost"), result.get("pricing_best_reduced_cost"))
    forbidden_count = _first_int(region.get("forbidden_task_set_count"))
    delta = None if source_bound is None or dual_bound is None else round(float(dual_bound) - float(source_bound), 9)
    best_column = result.get("best_column") if isinstance(result.get("best_column"), dict) else {}
    targeted_task_set = tuple(sorted(str(task) for task in (best_column.get("tasks") or []) if str(task)))
    forbidden_sets = tuple(
        tuple(sorted(str(task) for task in (task_set or []) if str(task)))
        for task_set in (region.get("forbidden_task_sets") or [])
    )
    targeted_negative_found = bool(result.get("negative_found") and targeted_task_set)
    targeted_solution_payload = (
        _targeted_negative_solution_payload(result)
        if targeted_negative_found
        else None
    )
    return {
        "source_probe_json": str(source_probe_json),
        "instance_id": instance_id,
        "history_round": history_round,
        "region_id": region.get("region_id"),
        "source_phase": region.get("source_phase"),
        "source_phase_status": region.get("source_phase_status"),
        "source_phase_exact_status": region.get("source_phase_exact_status"),
        "source_phase_best_reduced_cost": _first_float(region.get("source_phase_best_reduced_cost")),
        "source_phase_dual_bound": source_bound,
        "source_phase_wall_time_sec": _first_float(region.get("source_phase_wall_time_sec")),
        "forbidden_task_set_count": forbidden_count,
        "forbidden_task_sets": region.get("forbidden_task_sets") or [],
        "variant": variant,
        "formulation_kind": formulation_kind,
        "status": result.get("status") or result.get("algorithm_status") or "",
        "exact_status": result.get("exact_status") or "",
        "pricing_state": result.get("pricing_state") or "",
        "best_reduced_cost": best_rc,
        "dual_bound": dual_bound,
        "dual_bound_delta_vs_source": delta,
        "source_bound_improved": bool(delta is not None and float(delta) > 1.0e-9),
        "negative_found": bool(result.get("negative_found")),
        "negative_column_count": _first_int(result.get("negative_column_count")),
        "targeted_negative_task_set": list(targeted_task_set) if targeted_negative_found else [],
        "targeted_negative_task_set_size": len(targeted_task_set) if targeted_negative_found else "",
        "targeted_negative_true_rc": best_rc if targeted_negative_found else "",
        "targeted_negative_source_phase": region.get("source_phase") if targeted_negative_found else "",
        "targeted_negative_task_set_forbidden_seen": bool(
            targeted_negative_found and targeted_task_set in forbidden_sets
        ),
        "targeted_negative_solution_payload": targeted_solution_payload,
        "wall_time_sec": _first_float(result.get("wall_time_sec"), wall_time),
        "pricing_rc_audit_pass": result.get("pricing_rc_audit_pass"),
        "model_status_name": result.get("model_status_name") or "",
        "variable_count": _first_int(result.get("variable_count")),
        "constraint_count": _first_int(result.get("constraint_count")),
        "service_start_depot_travel_lb_enabled": bool(result.get("service_start_depot_travel_lb_enabled")),
        "task_to_depot_return_travel_lb_enabled": bool(result.get("task_to_depot_return_travel_lb_enabled")),
        "pair_route_duration_lb_enabled": bool(result.get("pair_route_duration_lb_enabled")),
        "pair_weighted_completion_lb_enabled": bool(result.get("pair_weighted_completion_lb_enabled")),
        "pair_weighted_completion_lb_count": _first_int(result.get("pair_weighted_completion_lb_count")),
        "pair_weighted_completion_lb_min": _first_float(result.get("pair_weighted_completion_lb_min")),
        "pair_weighted_completion_lb_max": _first_float(result.get("pair_weighted_completion_lb_max")),
        "sortie_slot_position_bounds_enabled": bool(result.get("sortie_slot_position_bounds_enabled")),
        "pair_energy_infeasible_cut_enabled": bool(result.get("pair_energy_infeasible_cut_enabled")),
        "pair_shadow_lb_enabled": bool(result.get("pair_shadow_lb_enabled")),
        "pair_shadow_lb_count": _first_int(result.get("pair_shadow_lb_count")),
        "pair_shadow_lb_exceeds_limit_count": _first_int(
            result.get("pair_shadow_lb_exceeds_limit_count")
        ),
        "pair_time_window_infeasible_cut_enabled": bool(
            result.get("pair_time_window_infeasible_cut_enabled")
        ),
        "pair_time_window_infeasible_cut_count": _first_int(
            result.get("pair_time_window_infeasible_cut_count")
        ),
        "pair_time_window_infeasible_pair_count": _first_int(
            result.get("pair_time_window_infeasible_pair_count")
        ),
        "pair_time_window_infeasible_margin_min": _first_float(
            result.get("pair_time_window_infeasible_margin_min")
        ),
        "pair_time_window_infeasible_margin_max": _first_float(
            result.get("pair_time_window_infeasible_margin_max")
        ),
        "pair_time_window_precedence_cut_enabled": bool(
            result.get("pair_time_window_precedence_cut_enabled")
        ),
        "pair_time_window_precedence_cut_count": _first_int(
            result.get("pair_time_window_precedence_cut_count")
        ),
        "pair_time_window_precedence_pair_count": _first_int(
            result.get("pair_time_window_precedence_pair_count")
        ),
        "pair_time_window_precedence_margin_min": _first_float(
            result.get("pair_time_window_precedence_margin_min")
        ),
        "pair_time_window_precedence_margin_max": _first_float(
            result.get("pair_time_window_precedence_margin_max")
        ),
        "triple_time_window_infeasible_cut_enabled": bool(
            result.get("triple_time_window_infeasible_cut_enabled")
        ),
        "triple_time_window_infeasible_cut_count": _first_int(
            result.get("triple_time_window_infeasible_cut_count")
        ),
        "triple_time_window_infeasible_triple_count": _first_int(
            result.get("triple_time_window_infeasible_triple_count")
        ),
        "triple_time_window_infeasible_margin_min": _first_float(
            result.get("triple_time_window_infeasible_margin_min")
        ),
        "triple_time_window_infeasible_margin_max": _first_float(
            result.get("triple_time_window_infeasible_margin_max")
        ),
        "quad_time_window_infeasible_cut_enabled": bool(
            result.get("quad_time_window_infeasible_cut_enabled")
        ),
        "quad_time_window_infeasible_cut_count": _first_int(
            result.get("quad_time_window_infeasible_cut_count")
        ),
        "quad_time_window_infeasible_quad_count": _first_int(
            result.get("quad_time_window_infeasible_quad_count")
        ),
        "quad_time_window_infeasible_margin_min": _first_float(
            result.get("quad_time_window_infeasible_margin_min")
        ),
        "quad_time_window_infeasible_margin_max": _first_float(
            result.get("quad_time_window_infeasible_margin_max")
        ),
        "frontier_unsupported_region_count": 1 if forbidden_count > 0 else 0,
        "official_certificate_allowed": False,
        "can_claim_certificate": False,
        "can_certify_no_negative": False,
        "diagnostic_only": True,
        "note": (
            "restricted/no-good targeted region; not a full-space no-negative certificate"
            if forbidden_count > 0
            else "unrestricted targeted diagnostic row"
        ),
    }


def _targeted_negative_solution_payload(result: dict) -> dict | None:
    journeys = result.get("journeys")
    if not journeys:
        return None
    try:
        journey = tuple(journeys)[0]
    except (TypeError, IndexError):
        return None
    to_payload = getattr(journey, "to_solution_payload", None)
    if not callable(to_payload):
        return None
    payload = to_payload(vehicle_id="targeted_restricted_region_negative")
    return payload if isinstance(payload, dict) else None


def _targeted_restricted_region_summary(rows: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("region_id") or ""), []).append(row)
    summary: list[dict] = []
    for region_id, group in sorted(grouped.items()):
        bounds = [
            (_first_float(row.get("dual_bound")), str(row.get("variant") or ""))
            for row in group
            if _first_float(row.get("dual_bound")) is not None
        ]
        rcs = [
            _first_float(row.get("best_reduced_cost"))
            for row in group
            if _first_float(row.get("best_reduced_cost")) is not None
        ]
        best_bound_pair = max(bounds, key=lambda item: float(item[0])) if bounds else (None, "")
        summary.append(
            {
                "region_id": region_id,
                "forbidden_task_set_count": _first_int(group[0].get("forbidden_task_set_count")),
                "row_count": len(group),
                "best_dual_bound": None if best_bound_pair[0] is None else round(float(best_bound_pair[0]), 9),
                "best_bound_variant": best_bound_pair[1],
                "best_reduced_cost": None if not rcs else round(min(float(value) for value in rcs), 9),
                "source_phase_dual_bound": _first_float(group[0].get("source_phase_dual_bound")),
                "source_bound_improved_count": sum(1 for row in group if row.get("source_bound_improved") is True),
                "time_limit_row_count": sum(
                    1 for row in group if str(row.get("status") or "") == "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED"
                ),
                "certificate_claim_count": sum(1 for row in group if row.get("can_claim_certificate") is True),
            }
        )
    return summary


def _restricted_region_bound_ledger_targeted_rows(
    source_probe_json: Path,
    *,
    targeted_probe_jsons: Iterable[str | Path],
) -> list[dict]:
    rows: list[dict] = []
    source_key = str(source_probe_json)
    source_resolved_key = str(source_probe_json.resolve()) if source_probe_json.exists() else source_key
    for path_like in targeted_probe_jsons:
        path = Path(path_like)
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            continue
        candidate_rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
        for row in candidate_rows:
            if not isinstance(row, dict):
                continue
            row_source = str(row.get("source_probe_json") or payload.get("source_probe_json") or "")
            if row_source:
                row_source_path = Path(row_source)
                row_source_resolved = (
                    str(row_source_path.resolve()) if row_source_path.exists() else row_source
                )
                if row_source not in {source_key, source_resolved_key} and row_source_resolved not in {
                    source_key,
                    source_resolved_key,
                }:
                    continue
            copied = dict(row)
            copied["targeted_probe_json"] = str(path)
            rows.append(copied)
    return rows


def _restricted_region_bound_ledger_row(region: dict, *, targeted_rows: list[dict]) -> dict:
    region_id = str(region.get("region_id") or "")
    forbidden_count = _first_int(region.get("forbidden_task_set_count"))
    source_bound = _first_float(region.get("source_phase_dual_bound"))
    source_candidate = {
        "candidate_source": "source_phase",
        "candidate_label": str(region.get("source_phase") or ""),
        "dual_bound": source_bound,
        "best_reduced_cost": _first_float(region.get("source_phase_best_reduced_cost")),
        "status": str(region.get("source_phase_status") or ""),
        "exact_status": str(region.get("source_phase_exact_status") or ""),
        "wall_time_sec": _first_float(region.get("source_phase_wall_time_sec")),
        "variant": "",
        "targeted_probe_json": "",
    }
    matching_targeted = [
        row
        for row in targeted_rows
        if str(row.get("region_id") or "") == region_id
        or (
            not region_id
            and _first_int(row.get("forbidden_task_set_count")) == forbidden_count
        )
    ]
    targeted_candidates = [
        {
            "candidate_source": "targeted_probe",
            "candidate_label": str(row.get("variant") or ""),
            "dual_bound": _first_float(row.get("dual_bound"), row.get("bound")),
            "best_reduced_cost": _first_float(row.get("best_reduced_cost")),
            "status": str(row.get("status") or row.get("algorithm_status") or ""),
            "exact_status": str(row.get("exact_status") or ""),
            "wall_time_sec": _first_float(row.get("wall_time_sec")),
            "variant": str(row.get("variant") or ""),
            "targeted_probe_json": str(row.get("targeted_probe_json") or ""),
        }
        for row in matching_targeted
    ]
    valid_targeted = [item for item in targeted_candidates if item["dual_bound"] is not None]
    targeted_best = (
        max(valid_targeted, key=lambda item: float(item["dual_bound"]))
        if valid_targeted
        else None
    )
    candidates = [
        item
        for item in (source_candidate, *(valid_targeted or []))
        if item.get("dual_bound") is not None
    ]
    selected = max(candidates, key=lambda item: float(item["dual_bound"])) if candidates else None
    selected_bound = None if selected is None else _first_float(selected.get("dual_bound"))
    source_bound_reused = bool(selected is not None and selected.get("candidate_source") == "source_phase")
    targeted_improved = bool(
        targeted_best is not None
        and source_bound is not None
        and float(targeted_best["dual_bound"]) > float(source_bound) + 1.0e-9
    )
    return {
        "region_id": region_id,
        "forbidden_task_set_count": forbidden_count,
        "forbidden_task_sets": region.get("forbidden_task_sets") or [],
        "source_phase": region.get("source_phase") or "",
        "source_phase_status": region.get("source_phase_status") or "",
        "source_phase_exact_status": region.get("source_phase_exact_status") or "",
        "source_phase_best_reduced_cost": _first_float(region.get("source_phase_best_reduced_cost")),
        "source_phase_dual_bound": source_bound,
        "source_phase_wall_time_sec": _first_float(region.get("source_phase_wall_time_sec")),
        "targeted_candidate_count": len(matching_targeted),
        "targeted_best_dual_bound": None if targeted_best is None else _first_float(targeted_best.get("dual_bound")),
        "targeted_best_reduced_cost": None
        if targeted_best is None
        else _first_float(targeted_best.get("best_reduced_cost")),
        "targeted_best_variant": "" if targeted_best is None else str(targeted_best.get("variant") or ""),
        "targeted_best_status": "" if targeted_best is None else str(targeted_best.get("status") or ""),
        "targeted_best_probe_json": "" if targeted_best is None else str(targeted_best.get("targeted_probe_json") or ""),
        "targeted_bound_improved_over_source": targeted_improved,
        "best_known_dual_bound": selected_bound,
        "best_known_best_reduced_cost": None
        if selected is None
        else _first_float(selected.get("best_reduced_cost")),
        "selected_bound_source": "none" if selected is None else str(selected.get("candidate_source") or "none"),
        "selected_bound_label": "" if selected is None else str(selected.get("candidate_label") or ""),
        "selected_bound_status": "" if selected is None else str(selected.get("status") or ""),
        "selected_bound_exact_status": "" if selected is None else str(selected.get("exact_status") or ""),
        "selected_bound_wall_time_sec": None if selected is None else _first_float(selected.get("wall_time_sec")),
        "source_bound_reused": source_bound_reused,
        "frontier_unsupported_region_count": 1,
        "pricing_proof_kind": "FRONTIER_BOUND_INCOMPLETE",
        "frontier_lb_official": False,
        "official_certificate_allowed": False,
        "can_claim_certificate": False,
        "can_certify_no_negative": False,
        "diagnostic_only": True,
        "note": "restricted/no-good bound ledger row; not a full-space no-negative certificate",
    }


def _select_history_row(history: list[dict], round_index: int) -> dict:
    if not history:
        raise ValueError("source probe has no history rows")
    if int(round_index) < 0:
        row = history[int(round_index)]
    else:
        matches = [item for item in history if int(item.get("round") or -1) == int(round_index)]
        row = matches[-1] if matches else history[int(round_index)]
    if not isinstance(row, dict):
        raise ValueError("selected history row is not an object")
    return row


def render_b4_1_markdown(report: dict, *, rows_csv: str | Path, summary_json: str | Path) -> str:
    lines = [
        "# B4.1 True-Dual Proof-Tail Strengthening 报告",
        "",
        "## Boundary",
        "",
        "- official objective 仍为 normalized cost + risk + 0.4 * weighted completion。",
        "- makespan 只作为 metric，不进入 pricing objective。",
        "- B4.1 diagnostic frontier 不自动升级 certificate。",
        "- worker dual smoothing 只用于 candidate search；official RC/bound/certificate 仍用 true RMP dual。",
        "",
        "## Artifacts",
        "",
        f"- CSV rows: `{rows_csv}`",
        f"- JSON summary: `{summary_json}`",
        "",
        "## Redlines",
        "",
        "| metric | value | required |",
        "| --- | ---: | ---: |",
    ]
    for key, value in report["redlines"].items():
        lines.append(f"| {key} | {value} | 0 |")
    if report.get("requirement_audit"):
        lines.extend(
            [
                "",
                "## Requirement Audit",
                "",
                "| id | status | evidence | next action |",
                "| --- | --- | --- | --- |",
            ]
        )
        for item in report["requirement_audit"]:
            lines.append(
                "| {id} | {status} | {evidence} | {next_action} |".format(
                    id=item["id"],
                    status=item["status"],
                    evidence=_compact_markdown_json(item.get("evidence") or {}),
                    next_action=str(item.get("next_action") or ""),
                )
            )
    lines.extend(["", "## Summary", ""])
    lines.append("| stage | mode | variant | rows | tree_opt | cert | diag_cert | negatives | best frontier LB | mean wall |")
    lines.append("| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for row in report["summary_rows"]:
        lines.append(
            "| {stage} | {mode} | {variant} | {rows} | {tree} | {cert} | {diag} | {neg} | {lb} | {wall} |".format(
                stage=row["stage"],
                mode=row["mode"],
                variant=row["variant"],
                rows=row["row_count"],
                tree=row["bpc_tree_optimal_count"],
                cert=row["can_certify_no_negative_count"],
                diag=row["diagnostic_claimed_certificate_count"],
                neg=row["negative_column_count"],
                lb=row["best_global_remaining_rc_lb"],
                wall=row["mean_wall_time"],
            )
        )
    if any(
        row.get("mean_active_column_count") is not None
        or row.get("best_negative_rc") is not None
        or row.get("mean_final_judge_wall_time") is not None
        for row in report["summary_rows"]
    ):
        lines.extend(
            [
                "",
                "## Stage B/C Telemetry",
                "",
                "| stage | mode | variant | active cols | active after merge | best neg RC | last best RC | final judge wall |",
                "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in report["summary_rows"]:
            lines.append(
                "| {stage} | {mode} | {variant} | {active} | {active_after} | {best_neg} | {last_best} | {fj_wall} |".format(
                    stage=row["stage"],
                    mode=row["mode"],
                    variant=row["variant"],
                    active=row.get("mean_active_column_count"),
                    active_after=row.get("mean_active_columns_after_merge"),
                    best_neg=row.get("best_negative_rc"),
                    last_best=row.get("best_last_best_reduced_cost"),
                    fj_wall=row.get("mean_final_judge_wall_time"),
                )
            )
    if report.get("latest_frontier_rows"):
        lines.extend(
            [
                "",
                "## Latest Stage B Frontier",
                "",
                "| mode | variant | active cols | added | negatives | latest neg RC | latest frontier LB | proof kind | scope | underlying scope | underlying proof | underlying cert | final judge wall | source |",
                "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | ---: | --- |",
            ]
        )
        for row in report["latest_frontier_rows"]:
            lines.append(
                "| {mode} | {variant} | {active} | {added} | {neg} | {best_neg} | {lb} | {proof} | {scope} | {underlying_scope} | {underlying_proof} | {underlying_cert} | {fj_wall} | {source} |".format(
                    mode=row.get("mode"),
                    variant=row.get("variant"),
                    active=row.get("active_columns_after_merge"),
                    added=row.get("columns_added"),
                    neg=row.get("negative_column_count"),
                    best_neg=row.get("best_negative_rc"),
                    lb=row.get("global_remaining_rc_lb"),
                    proof=row.get("pricing_proof_kind"),
                    scope=row.get("certificate_scope"),
                    underlying_scope=row.get("underlying_certificate_scope"),
                    underlying_proof=row.get("underlying_pricing_proof_kind"),
                    underlying_cert=row.get("underlying_can_certify_no_negative"),
                    fj_wall=row.get("final_judge_wall_time"),
                    source=row.get("source_probe_json"),
                )
            )
    acceptance = report["acceptance"]
    diagnostics = report.get("diagnostics") or {}
    lines.extend(
        [
            "",
            "## Acceptance State",
            "",
            f"- Stage A regression clean: `{acceptance['stage_a_regression_clean']}`。",
            f"- Stage B diagnostic clean: `{acceptance['stage_b_diagnostic_clean']}`。",
            f"- Stage B planned matrix complete: `{acceptance['stage_b_matrix_complete']}`。",
            f"- Stage C selected diagnostic clean: `{acceptance['stage_c_diagnostic_clean']}`。",
            f"- B4.1 code path exercised: `{acceptance['b4_1_code_path_exercised']}`。",
            f"- Full long experiment complete: `{acceptance['b4_1_full_experiment_complete']}`。",
            "- `b4_1_full_experiment_complete=False` 是刻意保守：需要另外完成 5/10/20 full regression 和 30-scale staged frontier/selected diagnostics。",
            "",
            "## Proof-Tail Diagnostics",
            "",
            f"- Negative-discovery budget exhausted rows: `{diagnostics.get('negative_discovery_budget_exhausted_count', 0)}`。",
            f"- Feasibility-proof budget exhausted rows: `{diagnostics.get('feasibility_proof_budget_exhausted_count', 0)}`。",
            f"- Missing optimization-proof rows: `{diagnostics.get('optimization_proof_missing_count', 0)}`。",
            f"- Positive incumbent RC but negative frontier bound rows: `{diagnostics.get('positive_best_rc_negative_bound_count', 0)}`。",
            f"- 30-scale underlying root LP certified rows: `{diagnostics.get('thirty_scale_underlying_node_lp_certified_count', 0)}`。",
            f"- 30-scale underlying exhaustive no-negative proofs: `{diagnostics.get('thirty_scale_underlying_exhaustive_no_negative_count', 0)}`。",
            f"- Hidden-negative miss reasons: `{_format_miss_reason_counts(diagnostics.get('hidden_negative_miss_reason_counts') or {})}`。",
            f"- Hidden-negative top miss reason: `{diagnostics.get('hidden_negative_top_miss_reason') or 'none'}`。",
            f"- Tail-dual worker rows: `{diagnostics.get('tail_dual_enabled_count', 0)}`；"
            f"worker-only `{diagnostics.get('tail_dual_worker_only_count', 0)}`；"
            f"true-dual RC recomputed `{diagnostics.get('tail_dual_true_dual_recomputed_count', 0)}`；"
            f"tail no-column certifies `{diagnostics.get('tail_dual_no_column_can_certify_count', 0)}`。",
            f"- Stage A observed regression modes: `{', '.join(diagnostics.get('stage_a_observed_regression_modes') or []) or 'none'}`。",
            f"- Stage A missing regression modes: `{', '.join(diagnostics.get('stage_a_missing_regression_modes') or []) or 'none'}`。",
            f"- Stage B observed matrix cells: `{', '.join(diagnostics.get('stage_b_observed_matrix_cells') or []) or 'none'}`。",
            f"- Stage B missing matrix cells: `{', '.join(diagnostics.get('stage_b_missing_matrix_cells') or []) or 'none'}`。",
        ]
    )
    return "\n".join(lines) + "\n"


def _run_stage_a_mode(
    data,
    *,
    mode: str,
    b0_direct,
    max_direct_tasks: int,
    max_rounds: int,
    wall_time_limit_sec: float | None,
    max_columns_per_round: int,
    max_tree_nodes: int,
    max_branch_depth: int,
) -> dict:
    if mode in {B41_STAGE_A_B3B_BASELINE, B41_STAGE_A_B4V2_HARVEST}:
        return solve_b3_branch_price_tree_baseline(
            data,
            b0_direct=b0_direct,
            max_direct_tasks=max_direct_tasks,
            max_rounds_per_node=max_rounds,
            wall_time_limit_sec=wall_time_limit_sec,
            max_columns_per_round=max_columns_per_round,
            max_tree_nodes=max_tree_nodes,
            max_branch_depth=max_branch_depth,
        )
    if mode in {B41_STAGE_A_TAIL_DUAL_OFF, B41_STAGE_A_TAIL_DUAL_ON}:
        return solve_b2_pricing_tail_baseline(
            data,
            b0_direct=b0_direct,
            max_direct_tasks=max_direct_tasks,
            max_rounds=max_rounds,
            wall_time_limit_sec=wall_time_limit_sec,
            max_columns_per_round=max_columns_per_round,
            mode=B2B_R2_MODE,
            tail_dual_stabilization_enabled=mode == B41_STAGE_A_TAIL_DUAL_ON,
        )
    raise ValueError(f"unknown B4.1 Stage A mode: {mode}")


def _stage_a_row(
    raw: dict,
    *,
    stage: str,
    matrix_group: str,
    instance_path: str,
    scale: int,
    mode: str,
    wall_time: float,
    max_rounds: int | None = None,
    max_columns_per_round: int | None = None,
    max_tree_nodes: int | None = None,
    max_branch_depth: int | None = None,
) -> dict:
    final_judge = raw.get("final_judge") if isinstance(raw.get("final_judge"), dict) else {}
    hidden_audit = raw.get("hidden_negative_audit") if isinstance(raw.get("hidden_negative_audit"), dict) else {}
    hidden_miss_reason_counts = _hidden_negative_miss_reason_counts(hidden_audit)
    b0_ablation = raw.get("b0_ablation") if isinstance(raw.get("b0_ablation"), dict) else {}
    b0_objective = _first_float(raw.get("B0_direct_objective"), b0_ablation.get("direct_dp_objective"))
    b3_objective = _first_float(raw.get("global_ub"), raw.get("incumbent_objective"), raw.get("root_lp_bound"))
    cert_scope = str(raw.get("certificate_scope") or "")
    pricing_state = str(raw.get("pricing_state") or "")
    history = raw.get("history") if isinstance(raw.get("history"), list) else []
    nodes = raw.get("nodes") if isinstance(raw.get("nodes"), list) else []
    root_node = nodes[0] if nodes and isinstance(nodes[0], dict) else {}
    root_history = root_node.get("history") if isinstance(root_node.get("history"), list) else []
    root_last = root_history[-1] if root_history and isinstance(root_history[-1], dict) else {}
    last_worker = _last_worker_payload(history)
    tail_payload = last_worker.get("tail_dual_stabilization") if isinstance(last_worker, dict) else {}
    if not isinstance(tail_payload, dict):
        tail_payload = {}
    tail_fields = _tail_dual_safety_fields(last_worker, tail_payload)
    return {
        "stage": stage,
        "matrix_group": matrix_group,
        "instance_path": instance_path,
        "source_probe_json": "",
        "scale": int(scale),
        "instance_id": raw.get("instance_id") or "",
        "mode": mode,
        "variant": "",
        "b4_1_matrix_cell": _stage_a_matrix_cell(mode),
        "b4_1_proof_tail_component": _stage_a_component(mode),
        "b4_1_formulation_profile": "B3B_representative_universe_branch_rc_audit",
        "b4_1_harvesting_enabled": mode == B41_STAGE_A_B4V2_HARVEST,
        "b4_1_hidden_negative_audit_enabled": mode in {B41_STAGE_A_B4V2_HARVEST, B41_STAGE_A_TAIL_DUAL_OFF, B41_STAGE_A_TAIL_DUAL_ON},
        "b4_1_frontier_ledger_enabled": False,
        "b4_1_official_certificate_allowed": mode in {B41_STAGE_A_B3B_BASELINE, B41_STAGE_A_B4V2_HARVEST},
        "phase": "stage_a_solver",
        "round": "",
        "max_rounds": _first_int(max_rounds, raw.get("max_rounds")),
        "max_columns_per_round": _first_int(max_columns_per_round, raw.get("max_columns_per_round")),
        "max_tree_nodes": _first_int(max_tree_nodes, raw.get("max_tree_nodes")),
        "max_branch_depth": _first_int(max_branch_depth, raw.get("max_branch_depth")),
        "node_count": _first_int(raw.get("node_count")),
        "root_round_count": _first_int(root_node.get("round_count")),
        "root_added_column_count": _first_int(root_node.get("added_column_count")),
        "root_last_pricing_state": root_last.get("pricing_state"),
        "root_last_negative_column_count": _first_int(root_last.get("negative_column_count")),
        "tree_gate_issue_count": len(raw.get("tree_certificate_gate_issues") or []),
        "algorithm_status": raw.get("algorithm_status") or "",
        "certificate_scope": cert_scope,
        "pricing_state": pricing_state,
        "exact_status": raw.get("exact_status") or "",
        "bpc_tree_optimal": cert_scope == CertificateScope.BPC_TREE_OPTIMAL.value,
        "b3_objective_diff_vs_b0": None
        if b0_objective is None or b3_objective is None
        else round(float(b3_objective) - float(b0_objective), 9),
        "manual_rc_fail": int(cert_scope in _CERTIFYING_SCOPES and raw.get("manual_rc_audit_pass") is False),
        "pricing_rc_fail": int(cert_scope in _CERTIFYING_SCOPES and raw.get("pricing_rc_audit_pass") is False),
        "certificate_leak": int(bool(raw.get("direct_dp_used_as_bpc_certificate"))),
        "hidden_negative_count": int(raw.get("hidden_negative_count") or 0),
        "hidden_negative_miss_reason_counts": hidden_miss_reason_counts,
        "hidden_negative_top_miss_reason": _top_hidden_negative_miss_reason(hidden_miss_reason_counts),
        "hidden_negative_worker_not_generated_count": hidden_miss_reason_counts.get("worker_not_generated", 0),
        "hidden_negative_pruned_by_dominance_count": hidden_miss_reason_counts.get("pruned_by_dominance", 0),
        "hidden_negative_pricing_timeout_only_count": hidden_miss_reason_counts.get("pricing_timeout_only", 0),
        "active_column_count": "",
        "pool_column_count": "",
        "columns_added": raw.get("added_column_count"),
        "active_columns_after_merge": "",
        "new_task_set_count": "",
        "replacement_task_set_count": "",
        "best_negative_rc": "",
        "last_best_reduced_cost": final_judge.get("best_reduced_cost", raw.get("last_best_reduced_cost", "")),
        "final_judge_wall_time": final_judge.get("final_judge_wall_time", ""),
        "rmp_round_count": _first_int(root_node.get("round_count")),
        "harvest_selected_count": _first_int(final_judge.get("harvest_selected_count"), raw.get("harvest_selected_count")),
        "harvest_candidate_negative_count": _first_int(
            final_judge.get("harvest_candidate_negative_count"),
            raw.get("candidate_negative_count"),
        ),
        "harvest_selected_new_task_set_count": final_judge.get("harvest_selected_new_task_set_count"),
        "harvest_selected_replacement_task_set_count": final_judge.get("harvest_selected_replacement_task_set_count"),
        "harvest_rejected_duplicate_count": _first_int(
            final_judge.get("harvest_rejected_duplicate_count"),
            raw.get("harvest_rejected_duplicate_count"),
        ),
        "harvest_rejected_not_addable_count": _first_int(
            final_judge.get("harvest_rejected_not_addable_count"),
            raw.get("harvest_rejected_not_addable_count"),
        ),
        "harvest_source_phase": final_judge.get("harvest_source_phase", raw.get("harvest_source_phase", "")),
        "harvest_best_true_rc": final_judge.get("harvest_best_true_rc"),
        "harvest_worst_selected_true_rc": final_judge.get("harvest_worst_selected_true_rc"),
        "harvest_avg_pairwise_jaccard": final_judge.get("harvest_avg_pairwise_jaccard", raw.get("harvest_avg_pairwise_jaccard")),
        "compact_optimization_harvest_enabled": bool(
            final_judge.get("compact_optimization_harvest_enabled")
        ),
        "compact_optimization_harvest_target": final_judge.get("compact_optimization_harvest_target"),
        "compact_optimization_harvest_no_good_scope": final_judge.get(
            "compact_optimization_harvest_no_good_scope"
        ),
        "compact_optimization_harvest_found_count": final_judge.get(
            "compact_optimization_harvest_found_count"
        ),
        "compact_optimization_harvest_search_call_count": final_judge.get(
            "compact_optimization_harvest_search_call_count"
        ),
        "harvest_addability_audit_pass": final_judge.get("harvest_addability_audit_pass"),
        "harvest_pricing_rc_audit_available": final_judge.get("harvest_pricing_rc_audit_available"),
        "harvest_pricing_rc_audit_pass": final_judge.get("harvest_pricing_rc_audit_pass"),
        "harvest_pricing_rc_max_abs_diff": final_judge.get("harvest_pricing_rc_max_abs_diff"),
        **tail_fields,
        "global_remaining_rc_lb": final_judge.get("global_remaining_rc_lb"),
        "frontier_coverage_complete": bool(final_judge.get("global_remaining_rc_lb_coverage_complete")),
        "frontier_unsupported_region_count": final_judge.get("frontier_unsupported_region_count"),
        "pending_complete_min_rc": final_judge.get("pending_complete_min_rc"),
        "pricing_proof_kind": final_judge.get("pricing_proof_kind"),
        "compact_final_judge_profile": final_judge.get("compact_final_judge_profile"),
        "compact_final_judge_formulation_profile": final_judge.get("compact_final_judge_formulation_profile"),
        "compact_final_judge_phase_mode": final_judge.get("compact_final_judge_phase_mode"),
        "service_start_depot_travel_lb_enabled": bool(
            final_judge.get("service_start_depot_travel_lb_enabled")
        ),
        "service_start_depot_travel_lb_count": final_judge.get("service_start_depot_travel_lb_count"),
        "task_to_depot_return_travel_lb_enabled": bool(
            final_judge.get("task_to_depot_return_travel_lb_enabled")
        ),
        "task_to_depot_return_travel_lb_count": final_judge.get("task_to_depot_return_travel_lb_count"),
        "pair_route_duration_lb_enabled": bool(final_judge.get("pair_route_duration_lb_enabled")),
        "pair_route_duration_lb_count": final_judge.get("pair_route_duration_lb_count"),
        "pair_weighted_completion_lb_enabled": bool(final_judge.get("pair_weighted_completion_lb_enabled")),
        "pair_weighted_completion_lb_count": final_judge.get("pair_weighted_completion_lb_count"),
        "pair_weighted_completion_lb_min": final_judge.get("pair_weighted_completion_lb_min"),
        "pair_weighted_completion_lb_max": final_judge.get("pair_weighted_completion_lb_max"),
        "sortie_slot_position_bounds_enabled": bool(
            final_judge.get("sortie_slot_position_bounds_enabled")
        ),
        "sortie_slot_position_bound_count": final_judge.get("sortie_slot_position_bound_count"),
        "demand_cover_cut_enabled": bool(final_judge.get("demand_cover_cut_enabled")),
        "demand_cover_cut_count": final_judge.get("demand_cover_cut_count"),
        "demand_cover_subset_count": final_judge.get("demand_cover_subset_count"),
        "single_task_energy_lb_enabled": bool(final_judge.get("single_task_energy_lb_enabled")),
        "single_task_energy_lb_count": final_judge.get("single_task_energy_lb_count"),
        "single_task_shadow_lb_enabled": bool(final_judge.get("single_task_shadow_lb_enabled")),
        "single_task_shadow_lb_count": final_judge.get("single_task_shadow_lb_count"),
        "pair_energy_lb_enabled": bool(final_judge.get("pair_energy_lb_enabled")),
        "pair_energy_lb_count": final_judge.get("pair_energy_lb_count"),
        "pair_energy_lb_exceeds_limit_count": final_judge.get("pair_energy_lb_exceeds_limit_count"),
        "pair_shadow_lb_enabled": bool(final_judge.get("pair_shadow_lb_enabled")),
        "pair_shadow_lb_count": final_judge.get("pair_shadow_lb_count"),
        "pair_shadow_lb_exceeds_limit_count": final_judge.get("pair_shadow_lb_exceeds_limit_count"),
        "pair_energy_infeasible_cut_enabled": bool(final_judge.get("pair_energy_infeasible_cut_enabled")),
        "pair_energy_infeasible_cut_count": final_judge.get("pair_energy_infeasible_cut_count"),
        "pair_energy_infeasible_pair_count": final_judge.get("pair_energy_infeasible_pair_count"),
        "pair_time_window_infeasible_cut_enabled": bool(
            final_judge.get("pair_time_window_infeasible_cut_enabled")
        ),
        "pair_time_window_infeasible_cut_count": final_judge.get(
            "pair_time_window_infeasible_cut_count"
        ),
        "pair_time_window_infeasible_pair_count": final_judge.get(
            "pair_time_window_infeasible_pair_count"
        ),
        "pair_time_window_infeasible_margin_min": final_judge.get(
            "pair_time_window_infeasible_margin_min"
        ),
        "pair_time_window_infeasible_margin_max": final_judge.get(
            "pair_time_window_infeasible_margin_max"
        ),
        "pair_time_window_precedence_cut_enabled": bool(
            final_judge.get("pair_time_window_precedence_cut_enabled")
        ),
        "pair_time_window_precedence_cut_count": final_judge.get(
            "pair_time_window_precedence_cut_count"
        ),
        "pair_time_window_precedence_pair_count": final_judge.get(
            "pair_time_window_precedence_pair_count"
        ),
        "pair_time_window_precedence_margin_min": final_judge.get(
            "pair_time_window_precedence_margin_min"
        ),
        "pair_time_window_precedence_margin_max": final_judge.get(
            "pair_time_window_precedence_margin_max"
        ),
        "triple_time_window_infeasible_cut_enabled": bool(
            final_judge.get("triple_time_window_infeasible_cut_enabled")
        ),
        "triple_time_window_infeasible_cut_count": final_judge.get(
            "triple_time_window_infeasible_cut_count"
        ),
        "triple_time_window_infeasible_triple_count": final_judge.get(
            "triple_time_window_infeasible_triple_count"
        ),
        "triple_time_window_infeasible_margin_min": final_judge.get(
            "triple_time_window_infeasible_margin_min"
        ),
        "triple_time_window_infeasible_margin_max": final_judge.get(
            "triple_time_window_infeasible_margin_max"
        ),
        "quad_time_window_infeasible_cut_enabled": bool(
            final_judge.get("quad_time_window_infeasible_cut_enabled")
        ),
        "quad_time_window_infeasible_cut_count": final_judge.get(
            "quad_time_window_infeasible_cut_count"
        ),
        "quad_time_window_infeasible_quad_count": final_judge.get(
            "quad_time_window_infeasible_quad_count"
        ),
        "quad_time_window_infeasible_margin_min": final_judge.get(
            "quad_time_window_infeasible_margin_min"
        ),
        "quad_time_window_infeasible_margin_max": final_judge.get(
            "quad_time_window_infeasible_margin_max"
        ),
        "pair_shadow_infeasible_cut_enabled": bool(final_judge.get("pair_shadow_infeasible_cut_enabled")),
        "pair_shadow_infeasible_cut_count": final_judge.get("pair_shadow_infeasible_cut_count"),
        "pair_shadow_infeasible_pair_count": final_judge.get("pair_shadow_infeasible_pair_count"),
        "triple_shadow_infeasible_cut_enabled": bool(final_judge.get("triple_shadow_infeasible_cut_enabled")),
        "triple_shadow_infeasible_cut_count": final_judge.get("triple_shadow_infeasible_cut_count"),
        "triple_shadow_infeasible_triple_count": final_judge.get("triple_shadow_infeasible_triple_count"),
        "triple_energy_infeasible_cut_enabled": bool(final_judge.get("triple_energy_infeasible_cut_enabled")),
        "triple_energy_infeasible_cut_count": final_judge.get("triple_energy_infeasible_cut_count"),
        "triple_energy_infeasible_triple_count": final_judge.get("triple_energy_infeasible_triple_count"),
        "negative_feasibility_skipped_for_proof_only": bool(
            final_judge.get("negative_feasibility_skipped_for_proof_only")
        ),
        "negative_feasibility_full_space_proof_attempted": bool(
            final_judge.get("negative_feasibility_full_space_proof_attempted")
        ),
        "negative_feasibility_full_space_proof_can_certify": bool(
            final_judge.get("negative_feasibility_full_space_proof_can_certify")
        ),
        "phase_budget_sec": "",
        "negative_feasibility_budget_sec": "",
        "optimization_proof_budget_sec": "",
        "negative_discovery_budget_exhausted": False,
        "feasibility_proof_budget_exhausted": False,
        "optimization_proof_missing": False,
        "compact_pricing_dual_bound": final_judge.get("dual_bound", final_judge.get("bound")),
        "new_negative_columns_found": raw.get("added_column_count"),
        "negative_column_count": final_judge.get("negative_column_count", raw.get("negative_column_count")),
        "can_certify_no_negative": bool(final_judge.get("can_certify_no_negative")),
        "diagnostic_claimed_certificate": _diagnostic_claimed_certificate(cert_scope, final_judge),
        "wall_time": round(float(wall_time), 6),
        "fail_closed_reason": raw.get("fail_closed_reason") or raw.get("note") or "",
    }


def _stage_probe_row(row: dict, *, stage: str, mode: str, matrix_group: str) -> dict:
    cert_scope = str(row.get("certificate_scope") or "")
    underlying_unsupported = _first_int(row.get("frontier_unsupported_region_count"))
    return {
        "stage": stage,
        "matrix_group": matrix_group,
        "instance_path": "",
        "source_probe_json": row.get("source_json") or "",
        "scale": "",
        "instance_id": row.get("instance_id") or "",
        "mode": mode,
        "variant": row.get("variant") or "",
        "b4_1_matrix_cell": _stage_probe_matrix_cell(str(row.get("variant") or "")),
        "b4_1_proof_tail_component": "compact_pricing_frontier_ledger_diagnostic",
        "b4_1_formulation_profile": _stage_probe_formulation_profile(str(row.get("variant") or "")),
        "b4_1_harvesting_enabled": False,
        "b4_1_hidden_negative_audit_enabled": False,
        "b4_1_frontier_ledger_enabled": True,
        "b4_1_official_certificate_allowed": False,
        "phase": row.get("phase") or "",
        "round": row.get("round") or "",
        "algorithm_status": row.get("compact_pricing_status") or "",
        "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
        "underlying_certificate_scope": cert_scope,
        "pricing_state": "",
        "exact_status": row.get("compact_pricing_exact_status") or "",
        "bpc_tree_optimal": False,
        "b3_objective_diff_vs_b0": None,
        "manual_rc_fail": 0,
        "pricing_rc_fail": 0,
        "certificate_leak": 0,
        "hidden_negative_count": "",
        "hidden_negative_miss_reason_counts": {},
        "hidden_negative_top_miss_reason": "",
        "hidden_negative_worker_not_generated_count": 0,
        "hidden_negative_pruned_by_dominance_count": 0,
        "hidden_negative_pricing_timeout_only_count": 0,
        "active_column_count": row.get("active_column_count", ""),
        "pool_column_count": row.get("pool_column_count", ""),
        "columns_added": row.get("columns_added", ""),
        "active_columns_after_merge": row.get("active_columns_after_merge", ""),
        "new_task_set_count": row.get("new_task_set_count", ""),
        "replacement_task_set_count": row.get("replacement_task_set_count", ""),
        "best_negative_rc": _first_float(row.get("negative_rc"), row.get("best_negative_rc")),
        "last_best_reduced_cost": _first_float(
            row.get("last_best_reduced_cost"),
            row.get("compact_pricing_best_rc"),
            row.get("pending_complete_min_rc"),
        ),
        "final_judge_wall_time": row.get("final_judge_wall_time", row.get("wall_time")),
        "rmp_round_count": row.get("rmp_round_count", row.get("round", "")),
        "harvest_selected_count": "",
        "harvest_candidate_negative_count": "",
        "harvest_selected_new_task_set_count": "",
        "harvest_selected_replacement_task_set_count": "",
        "harvest_rejected_duplicate_count": "",
        "harvest_rejected_not_addable_count": "",
        "harvest_source_phase": row.get("harvest_source_phase") or "",
        "harvest_best_true_rc": "",
        "harvest_worst_selected_true_rc": "",
        "harvest_avg_pairwise_jaccard": "",
        "compact_optimization_harvest_enabled": bool(row.get("compact_optimization_harvest_enabled")),
        "compact_optimization_harvest_target": row.get("compact_optimization_harvest_target", ""),
        "compact_optimization_harvest_no_good_scope": row.get(
            "compact_optimization_harvest_no_good_scope",
            "",
        ),
        "compact_optimization_harvest_found_count": row.get(
            "compact_optimization_harvest_found_count",
            "",
        ),
        "compact_optimization_harvest_search_call_count": row.get(
            "compact_optimization_harvest_search_call_count",
            "",
        ),
        "harvest_addability_audit_pass": "",
        "harvest_pricing_rc_audit_available": row.get("harvest_pricing_rc_audit_available", ""),
        "harvest_pricing_rc_audit_pass": row.get("harvest_pricing_rc_audit_pass", ""),
        "harvest_pricing_rc_max_abs_diff": row.get("harvest_pricing_rc_max_abs_diff", ""),
        "tail_dual_stabilization_enabled": False,
        "worker_dual_only": False,
        "true_dual_rc_recomputed": False,
        "worker_dual_source": "",
        "official_dual_source": "",
        "tail_dual_stabilization_alpha": "",
        "tail_dual_stabilization_window": "",
        "tail_dual_center_task_count": "",
        "tail_dual_current_task_count": "",
        "tail_dual_no_column_can_certify": False,
        "global_remaining_rc_lb": row.get("global_remaining_rc_lb"),
        "underlying_global_remaining_rc_lb": row.get("global_remaining_rc_lb"),
        "frontier_lb_official": False,
        "frontier_coverage_complete": False,
        "underlying_frontier_coverage_complete": bool(row.get("frontier_coverage_complete")),
        "frontier_unsupported_region_count": max(1, int(underlying_unsupported or 0)),
        "underlying_frontier_unsupported_region_count": row.get("frontier_unsupported_region_count"),
        "pending_complete_min_rc": row.get("pending_complete_min_rc"),
        "underlying_pending_complete_min_rc": row.get("pending_complete_min_rc"),
        "pricing_proof_kind": "FRONTIER_BOUND_INCOMPLETE",
        "underlying_pricing_proof_kind": row.get("pricing_proof_kind"),
        "compact_final_judge_profile": row.get("compact_final_judge_profile"),
        "compact_final_judge_formulation_profile": row.get("compact_final_judge_formulation_profile"),
        "compact_final_judge_phase_mode": row.get("compact_final_judge_phase_mode"),
        "service_start_depot_travel_lb_enabled": bool(row.get("service_start_depot_travel_lb_enabled")),
        "service_start_depot_travel_lb_count": row.get("service_start_depot_travel_lb_count"),
        "task_to_depot_return_travel_lb_enabled": bool(row.get("task_to_depot_return_travel_lb_enabled")),
        "task_to_depot_return_travel_lb_count": row.get("task_to_depot_return_travel_lb_count"),
        "pair_route_duration_lb_enabled": bool(row.get("pair_route_duration_lb_enabled")),
        "pair_route_duration_lb_count": row.get("pair_route_duration_lb_count"),
        "pair_weighted_completion_lb_enabled": bool(row.get("pair_weighted_completion_lb_enabled")),
        "pair_weighted_completion_lb_count": row.get("pair_weighted_completion_lb_count"),
        "pair_weighted_completion_lb_min": row.get("pair_weighted_completion_lb_min"),
        "pair_weighted_completion_lb_max": row.get("pair_weighted_completion_lb_max"),
        "sortie_slot_position_bounds_enabled": bool(row.get("sortie_slot_position_bounds_enabled")),
        "sortie_slot_position_bound_count": row.get("sortie_slot_position_bound_count"),
        "demand_cover_cut_enabled": bool(row.get("demand_cover_cut_enabled")),
        "demand_cover_cut_count": row.get("demand_cover_cut_count"),
        "demand_cover_subset_count": row.get("demand_cover_subset_count"),
        "single_task_energy_lb_enabled": bool(row.get("single_task_energy_lb_enabled")),
        "single_task_energy_lb_count": row.get("single_task_energy_lb_count"),
        "single_task_shadow_lb_enabled": bool(row.get("single_task_shadow_lb_enabled")),
        "single_task_shadow_lb_count": row.get("single_task_shadow_lb_count"),
        "pair_energy_lb_enabled": bool(row.get("pair_energy_lb_enabled")),
        "pair_energy_lb_count": row.get("pair_energy_lb_count"),
        "pair_energy_lb_exceeds_limit_count": row.get("pair_energy_lb_exceeds_limit_count"),
        "pair_shadow_lb_enabled": bool(row.get("pair_shadow_lb_enabled")),
        "pair_shadow_lb_count": row.get("pair_shadow_lb_count"),
        "pair_shadow_lb_exceeds_limit_count": row.get("pair_shadow_lb_exceeds_limit_count"),
        "pair_energy_infeasible_cut_enabled": bool(row.get("pair_energy_infeasible_cut_enabled")),
        "pair_energy_infeasible_cut_count": row.get("pair_energy_infeasible_cut_count"),
        "pair_energy_infeasible_pair_count": row.get("pair_energy_infeasible_pair_count"),
        "pair_time_window_infeasible_cut_enabled": bool(row.get("pair_time_window_infeasible_cut_enabled")),
        "pair_time_window_infeasible_cut_count": row.get("pair_time_window_infeasible_cut_count"),
        "pair_time_window_infeasible_pair_count": row.get("pair_time_window_infeasible_pair_count"),
        "pair_time_window_infeasible_margin_min": row.get("pair_time_window_infeasible_margin_min"),
        "pair_time_window_infeasible_margin_max": row.get("pair_time_window_infeasible_margin_max"),
        "pair_time_window_precedence_cut_enabled": bool(row.get("pair_time_window_precedence_cut_enabled")),
        "pair_time_window_precedence_cut_count": row.get("pair_time_window_precedence_cut_count"),
        "pair_time_window_precedence_pair_count": row.get("pair_time_window_precedence_pair_count"),
        "pair_time_window_precedence_margin_min": row.get("pair_time_window_precedence_margin_min"),
        "pair_time_window_precedence_margin_max": row.get("pair_time_window_precedence_margin_max"),
        "triple_time_window_infeasible_cut_enabled": bool(
            row.get("triple_time_window_infeasible_cut_enabled")
        ),
        "triple_time_window_infeasible_cut_count": row.get("triple_time_window_infeasible_cut_count"),
        "triple_time_window_infeasible_triple_count": row.get("triple_time_window_infeasible_triple_count"),
        "triple_time_window_infeasible_margin_min": row.get("triple_time_window_infeasible_margin_min"),
        "triple_time_window_infeasible_margin_max": row.get("triple_time_window_infeasible_margin_max"),
        "quad_time_window_infeasible_cut_enabled": bool(row.get("quad_time_window_infeasible_cut_enabled")),
        "quad_time_window_infeasible_cut_count": row.get("quad_time_window_infeasible_cut_count"),
        "quad_time_window_infeasible_quad_count": row.get("quad_time_window_infeasible_quad_count"),
        "quad_time_window_infeasible_margin_min": row.get("quad_time_window_infeasible_margin_min"),
        "quad_time_window_infeasible_margin_max": row.get("quad_time_window_infeasible_margin_max"),
        "pair_shadow_infeasible_cut_enabled": bool(row.get("pair_shadow_infeasible_cut_enabled")),
        "pair_shadow_infeasible_cut_count": row.get("pair_shadow_infeasible_cut_count"),
        "pair_shadow_infeasible_pair_count": row.get("pair_shadow_infeasible_pair_count"),
        "triple_shadow_infeasible_cut_enabled": bool(row.get("triple_shadow_infeasible_cut_enabled")),
        "triple_shadow_infeasible_cut_count": row.get("triple_shadow_infeasible_cut_count"),
        "triple_shadow_infeasible_triple_count": row.get("triple_shadow_infeasible_triple_count"),
        "triple_energy_infeasible_cut_enabled": bool(row.get("triple_energy_infeasible_cut_enabled")),
        "triple_energy_infeasible_cut_count": row.get("triple_energy_infeasible_cut_count"),
        "triple_energy_infeasible_triple_count": row.get("triple_energy_infeasible_triple_count"),
        "negative_feasibility_skipped_for_proof_only": bool(
            row.get("negative_feasibility_skipped_for_proof_only")
        ),
        "negative_feasibility_full_space_proof_attempted": bool(
            row.get("negative_feasibility_full_space_proof_attempted")
        ),
        "negative_feasibility_full_space_proof_can_certify": bool(
            row.get("negative_feasibility_full_space_proof_can_certify")
        ),
        "phase_budget_sec": row.get("phase_budget_sec"),
        "negative_feasibility_budget_sec": row.get("negative_feasibility_budget_sec"),
        "optimization_proof_budget_sec": row.get("optimization_proof_budget_sec"),
        "negative_discovery_budget_exhausted": bool(row.get("negative_discovery_budget_exhausted")),
        "feasibility_proof_budget_exhausted": bool(row.get("feasibility_proof_budget_exhausted")),
        "optimization_proof_missing": bool(row.get("optimization_proof_missing")),
        "compact_pricing_dual_bound": row.get("compact_pricing_dual_bound"),
        "new_negative_columns_found": row.get("new_negative_columns_found"),
        "negative_column_count": row.get("negative_column_count"),
        "can_certify_no_negative": False,
        "underlying_can_certify_no_negative": bool(row.get("can_certify_no_negative")),
        "b4_1_certificate_suppressed": bool(row.get("can_certify_no_negative") or cert_scope not in {"", "DIAGNOSTIC_PRICING_FRONTIER"}),
        "diagnostic_claimed_certificate": 0,
        "wall_time": row.get("wall_time"),
        "fail_closed_reason": "",
    }


def _stage_b_probe_evidence_rows(
    source_probe_json: str | Path,
    *,
    matrix_group: str,
    skip_keys: Iterable[tuple[str, str, str, str]] = (),
) -> list[dict]:
    source = Path(source_probe_json)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    if _payload_is_worker_tail_hidden_negative_evidence(payload):
        row = _stage_b_worker_tail_hidden_negative_evidence_row(
            source,
            payload,
            matrix_group=matrix_group,
        )
        key = _stage_b_evidence_key(row)
        return [] if key in set(skip_keys) else [row]
    final_judge = payload.get("final_judge") if isinstance(payload.get("final_judge"), dict) else {}
    if not final_judge:
        return []
    variant = _probe_final_judge_variant(final_judge)
    if variant not in {
        "V2_latest_service_start_slot_bound",
        "V4_combined_endpoint_pair_latest_start_time_window",
    }:
        return []
    base = _stage_probe_row(
        {
            "source_json": str(source),
            "instance_id": payload.get("instance_id") or final_judge.get("instance_id") or "",
            "variant": variant,
            "phase": "probe_final_judge_evidence",
            "round": payload.get("pricing_round_count") or final_judge.get("round") or "",
            "compact_pricing_status": final_judge.get("status") or final_judge.get("algorithm_status") or "",
            "compact_pricing_exact_status": final_judge.get("exact_status") or "",
            "certificate_scope": payload.get("certificate_scope") or "DIAGNOSTIC_PRICING_FRONTIER",
            "can_certify_no_negative": final_judge.get("can_certify_no_negative"),
            "pricing_proof_kind": final_judge.get("pricing_proof_kind"),
            "global_remaining_rc_lb": final_judge.get("global_remaining_rc_lb"),
            "frontier_coverage_complete": final_judge.get("global_remaining_rc_lb_coverage_complete"),
            "frontier_unsupported_region_count": final_judge.get("frontier_unsupported_region_count"),
            "pending_complete_min_rc": final_judge.get("pending_complete_min_rc"),
            "compact_final_judge_profile": final_judge.get("compact_final_judge_profile"),
            "compact_final_judge_formulation_profile": final_judge.get("compact_final_judge_formulation_profile"),
            "compact_final_judge_phase_mode": final_judge.get("compact_final_judge_phase_mode"),
            "negative_feasibility_skipped_for_proof_only": final_judge.get(
                "negative_feasibility_skipped_for_proof_only"
            ),
            "negative_feasibility_full_space_proof_attempted": final_judge.get(
                "negative_feasibility_full_space_proof_attempted"
            ),
            "negative_feasibility_full_space_proof_can_certify": final_judge.get(
                "negative_feasibility_full_space_proof_can_certify"
            ),
            "compact_pricing_dual_bound": final_judge.get("dual_bound", final_judge.get("bound")),
            "negative_column_count": final_judge.get("negative_column_count"),
            "active_column_count": _payload_active_column_count(payload, final_judge),
            "pool_column_count": _first_int(payload.get("pool_column_count"), final_judge.get("pool_column_count")),
            "columns_added": _first_int(payload.get("added_column_count"), final_judge.get("added_column_count")),
            "active_columns_after_merge": _first_int(
                payload.get("active_columns_after_merge"),
                final_judge.get("active_columns_after_merge"),
                _payload_active_column_count(payload, final_judge),
            ),
            "best_negative_rc": _first_float(
                final_judge.get("negative_rc"),
                final_judge.get("best_reduced_cost"),
                payload.get("harvest_best_true_rc"),
            ),
            "last_best_reduced_cost": _first_float(
                final_judge.get("best_reduced_cost"),
                final_judge.get("pending_complete_min_rc"),
                payload.get("last_best_reduced_cost"),
            ),
            "final_judge_wall_time": final_judge.get("final_judge_wall_time") or payload.get("elapsed_sec"),
            "rmp_round_count": payload.get("pricing_round_count") or final_judge.get("round") or "",
            "harvest_source_phase": final_judge.get("harvest_source_phase"),
            "harvest_pricing_rc_audit_available": final_judge.get("harvest_pricing_rc_audit_available"),
            "harvest_pricing_rc_audit_pass": final_judge.get("harvest_pricing_rc_audit_pass"),
            "harvest_pricing_rc_max_abs_diff": final_judge.get("harvest_pricing_rc_max_abs_diff"),
            "wall_time": final_judge.get("final_judge_wall_time") or payload.get("elapsed_sec"),
        },
        stage="B",
        mode="B4.1_probe_final_judge_evidence",
        matrix_group=matrix_group,
    )
    base["b4_1_proof_tail_component"] = "true_dual_final_judge_probe_evidence"
    base["b4_1_harvesting_enabled"] = _probe_has_final_judge_harvest_telemetry(final_judge)
    hidden_count = _probe_hidden_negative_count(payload)
    hidden_audit = payload.get("hidden_negative_audit") if isinstance(payload.get("hidden_negative_audit"), dict) else {}
    hidden_miss_reason_counts = _hidden_negative_miss_reason_counts(hidden_audit)
    base["b4_1_hidden_negative_audit_enabled"] = hidden_count is not None
    base["hidden_negative_count"] = "" if hidden_count is None else hidden_count
    base["hidden_negative_miss_reason_counts"] = hidden_miss_reason_counts
    base["hidden_negative_top_miss_reason"] = _top_hidden_negative_miss_reason(hidden_miss_reason_counts)
    base["hidden_negative_worker_not_generated_count"] = hidden_miss_reason_counts.get("worker_not_generated", 0)
    base["hidden_negative_pruned_by_dominance_count"] = hidden_miss_reason_counts.get("pruned_by_dominance", 0)
    base["hidden_negative_pricing_timeout_only_count"] = hidden_miss_reason_counts.get("pricing_timeout_only", 0)
    base["harvest_selected_count"] = final_judge.get("harvest_selected_count", "")
    base["harvest_candidate_negative_count"] = final_judge.get("harvest_candidate_negative_count", "")
    base["harvest_selected_new_task_set_count"] = final_judge.get("harvest_selected_new_task_set_count", "")
    base["harvest_selected_replacement_task_set_count"] = final_judge.get(
        "harvest_selected_replacement_task_set_count",
        "",
    )
    base["new_task_set_count"] = base["harvest_selected_new_task_set_count"]
    base["replacement_task_set_count"] = base["harvest_selected_replacement_task_set_count"]
    base["harvest_rejected_duplicate_count"] = final_judge.get("harvest_rejected_duplicate_count", "")
    base["harvest_rejected_not_addable_count"] = final_judge.get("harvest_rejected_not_addable_count", "")
    base["harvest_source_phase"] = final_judge.get("harvest_source_phase", "")
    base["harvest_best_true_rc"] = final_judge.get("harvest_best_true_rc", "")
    base["harvest_worst_selected_true_rc"] = final_judge.get("harvest_worst_selected_true_rc", "")
    base["harvest_avg_pairwise_jaccard"] = final_judge.get("harvest_avg_pairwise_jaccard", "")
    base["compact_optimization_harvest_enabled"] = bool(
        final_judge.get("compact_optimization_harvest_enabled")
    )
    base["compact_optimization_harvest_target"] = final_judge.get(
        "compact_optimization_harvest_target",
        "",
    )
    base["compact_optimization_harvest_no_good_scope"] = final_judge.get(
        "compact_optimization_harvest_no_good_scope",
        "",
    )
    base["compact_optimization_harvest_found_count"] = final_judge.get(
        "compact_optimization_harvest_found_count",
        "",
    )
    base["compact_optimization_harvest_search_call_count"] = final_judge.get(
        "compact_optimization_harvest_search_call_count",
        "",
    )
    base["harvest_addability_audit_pass"] = final_judge.get("harvest_addability_audit_pass", "")
    base["harvest_pricing_rc_audit_available"] = final_judge.get("harvest_pricing_rc_audit_available", "")
    base["harvest_pricing_rc_audit_pass"] = final_judge.get("harvest_pricing_rc_audit_pass", "")
    base["harvest_pricing_rc_max_abs_diff"] = final_judge.get("harvest_pricing_rc_max_abs_diff", "")
    key = _stage_b_evidence_key(base)
    return [] if key in set(skip_keys) else [base]


def _diagnostic_b0_placeholder(data) -> SimpleNamespace:
    reference = _reference_solution_upper_bound(data)
    return SimpleNamespace(
        status=(
            "REFERENCE_FEASIBLE_INCUMBENT_SEED_ONLY"
            if reference is not None
            else "SKIPPED_FOR_B4_1_WORKER_TAIL_DIAGNOSTIC"
        ),
        certificate_scope="NOT_SOLVED",
        objective=None if reference is None else float(reference.objective),
        journeys=tuple() if reference is None else tuple(reference.journeys),
        objective_breakdown=None,
        reference_solution_upper_bound=None if reference is None else float(reference.objective),
        reference_solution_upper_bound_source="" if reference is None else str(reference.source),
        direct_bound_pruning_root_bound=None,
        direct_bound_pruning_active=False,
        journey_label_bound_pruned_count=0,
    )


def _worker_tail_probe_payload(
    data,
    result: dict,
    *,
    instance_path: str,
    elapsed: float,
    max_direct_tasks: int,
    max_rounds: int,
    wall_time_limit_sec: float | None,
    max_columns_per_round: int,
    seed_mode: str,
    skip_b0_direct: bool,
    tail_dual_stabilization_enabled: bool,
    tail_dual_stabilization_alpha: float,
    tail_dual_stabilization_window: int,
) -> dict:
    final_judge = result.get("final_judge") if isinstance(result.get("final_judge"), dict) else {}
    final_judge_call_count = int(result.get("final_judge_call_count") or 0)
    hidden_audit = result.get("hidden_negative_audit") if isinstance(result.get("hidden_negative_audit"), dict) else {}
    if final_judge_call_count <= 0:
        hidden_audit = {}
    hidden_miss_reason_counts = _hidden_negative_miss_reason_counts(hidden_audit)
    history = result.get("history") if isinstance(result.get("history"), list) else []
    last_worker = _last_worker_payload(history)
    tail_payload = last_worker.get("tail_dual_stabilization") if isinstance(last_worker.get("tail_dual_stabilization"), dict) else {}
    tail_fields = _tail_dual_safety_fields(last_worker, tail_payload)
    return {
        "schema_version": "lunar_ice_bpc.b4_1_worker_tail_hidden_negative_probe.v1",
        "instance_path": str(instance_path),
        "instance_id": data.instance_id,
        "task_count": len(data.task_ids),
        "b2_mode": result.get("b2_mode") or B2B_R2_MODE,
        "config": {
            "max_direct_tasks": int(max_direct_tasks),
            "max_rounds": int(max_rounds),
            "wall_time_limit_sec": wall_time_limit_sec,
            "max_columns_per_round": int(max_columns_per_round),
            "seed_mode": str(seed_mode),
            "skip_b0_direct": bool(skip_b0_direct),
            "tail_dual_stabilization_enabled": bool(tail_dual_stabilization_enabled),
            "tail_dual_stabilization_alpha": float(tail_dual_stabilization_alpha),
            "tail_dual_stabilization_window": int(tail_dual_stabilization_window),
            "official_certificate_allowed": False,
        },
        "elapsed_sec": round(float(elapsed), 6),
        "algorithm_status": result.get("algorithm_status"),
        "certificate_scope": result.get("certificate_scope"),
        "exact_status": result.get("exact_status"),
        "pricing_state": result.get("pricing_state"),
        "pricing_round_count": result.get("pricing_round_count"),
        "added_column_count": result.get("added_column_count"),
        "final_judge_call_count": final_judge_call_count,
        "candidate_negative_count": result.get("candidate_negative_count"),
        "addable_negative_count": result.get("addable_negative_count"),
        "selected_count": result.get("selected_count"),
        "hidden_negative_count": result.get("hidden_negative_count") if hidden_audit else "",
        "hidden_negative_miss_reason_counts": hidden_miss_reason_counts,
        "hidden_negative_top_miss_reason": _top_hidden_negative_miss_reason(hidden_miss_reason_counts),
        "hidden_negative_audit": hidden_audit,
        "harvest_selected_count": result.get("harvest_selected_count"),
        "harvest_candidate_negative_count": result.get("harvest_candidate_negative_count"),
        "harvest_selected_new_task_set_count": result.get("harvest_selected_new_task_set_count"),
        "harvest_selected_replacement_task_set_count": result.get("harvest_selected_replacement_task_set_count"),
        "harvest_rejected_duplicate_count": result.get("harvest_rejected_duplicate_count"),
        "harvest_rejected_not_addable_count": result.get("harvest_rejected_not_addable_count"),
        "harvest_best_true_rc": result.get("harvest_best_true_rc"),
        "harvest_worst_selected_true_rc": result.get("harvest_worst_selected_true_rc"),
        "harvest_avg_pairwise_jaccard": result.get("harvest_avg_pairwise_jaccard"),
        "harvest_source_phase": result.get("harvest_source_phase"),
        "harvest_pricing_rc_audit_available": result.get("harvest_pricing_rc_audit_available"),
        "harvest_pricing_rc_audit_pass": result.get("harvest_pricing_rc_audit_pass"),
        "harvest_pricing_rc_max_abs_diff": result.get("harvest_pricing_rc_max_abs_diff"),
        **tail_fields,
        "tail_dual_stabilization": tail_payload,
        "final_judge": final_judge,
        "history": history,
        "profiling": result.get("profiling") if isinstance(result.get("profiling"), dict) else {},
        "worker_seed_catalog": result.get("worker_seed_catalog") if isinstance(result.get("worker_seed_catalog"), dict) else {},
        "b0_ablation": result.get("b0_ablation") if isinstance(result.get("b0_ablation"), dict) else {},
        "certificate_ledger": result.get("certificate_ledger") if isinstance(result.get("certificate_ledger"), dict) else {},
        "note": result.get("note") or result.get("fail_closed_reason") or "",
        "official_certificate_allowed": False,
        "can_certify_no_negative": False,
        "diagnostic_only": True,
    }


def _stage_b_worker_tail_hidden_negative_evidence_row(
    source: Path,
    payload: dict,
    *,
    matrix_group: str,
) -> dict:
    final_judge = payload.get("final_judge") if isinstance(payload.get("final_judge"), dict) else {}
    audit = payload.get("hidden_negative_audit") if isinstance(payload.get("hidden_negative_audit"), dict) else {}
    hidden_count = _probe_hidden_negative_count(payload)
    hidden_miss_reason_counts = _hidden_negative_miss_reason_counts(
        audit,
        payload.get("hidden_negative_miss_reason_counts"),
    )
    variant = _probe_final_judge_variant(final_judge) if final_judge else "V2_latest_service_start_slot_bound"
    base = _stage_probe_row(
        {
            "source_json": str(source),
            "instance_id": payload.get("instance_id") or final_judge.get("instance_id") or "",
            "variant": variant,
            "phase": "worker_tail_hidden_negative_evidence",
            "round": payload.get("pricing_round_count") or final_judge.get("round") or "",
            "compact_pricing_status": payload.get("algorithm_status")
            or final_judge.get("status")
            or final_judge.get("algorithm_status")
            or "",
            "compact_pricing_exact_status": payload.get("exact_status") or final_judge.get("exact_status") or "",
            "certificate_scope": payload.get("certificate_scope") or "DIAGNOSTIC_PRICING_FRONTIER",
            "can_certify_no_negative": final_judge.get("can_certify_no_negative"),
            "pricing_proof_kind": final_judge.get("pricing_proof_kind"),
            "global_remaining_rc_lb": final_judge.get("global_remaining_rc_lb"),
            "frontier_coverage_complete": final_judge.get("global_remaining_rc_lb_coverage_complete"),
            "frontier_unsupported_region_count": final_judge.get("frontier_unsupported_region_count"),
            "pending_complete_min_rc": final_judge.get("pending_complete_min_rc"),
            "compact_final_judge_profile": final_judge.get("compact_final_judge_profile"),
            "compact_final_judge_formulation_profile": final_judge.get("compact_final_judge_formulation_profile"),
            "compact_final_judge_phase_mode": final_judge.get("compact_final_judge_phase_mode"),
            "compact_pricing_dual_bound": final_judge.get("dual_bound", final_judge.get("bound")),
            "negative_column_count": _first_int(
                final_judge.get("negative_column_count"),
                payload.get("candidate_negative_count"),
                payload.get("hidden_negative_count"),
            ),
            "harvest_source_phase": _first_str(final_judge.get("harvest_source_phase"), payload.get("harvest_source_phase")),
            "harvest_pricing_rc_audit_available": final_judge.get(
                "harvest_pricing_rc_audit_available",
                payload.get("harvest_pricing_rc_audit_available", ""),
            ),
            "harvest_pricing_rc_audit_pass": final_judge.get(
                "harvest_pricing_rc_audit_pass",
                payload.get("harvest_pricing_rc_audit_pass", ""),
            ),
            "harvest_pricing_rc_max_abs_diff": final_judge.get(
                "harvest_pricing_rc_max_abs_diff",
                payload.get("harvest_pricing_rc_max_abs_diff", ""),
            ),
            "wall_time": final_judge.get("final_judge_wall_time") or payload.get("elapsed_sec"),
        },
        stage="B",
        mode="B4.1_worker_tail_hidden_negative_evidence",
        matrix_group=matrix_group,
    )
    base["b4_1_matrix_cell"] = "B4V2_hidden_negative_audit"
    base["b4_1_proof_tail_component"] = "worker_tail_hidden_negative_audit_diagnostic"
    base["b4_1_harvesting_enabled"] = _probe_has_final_judge_harvest_telemetry(
        final_judge
    ) or _payload_has_final_judge_harvest_telemetry(payload)
    base["b4_1_hidden_negative_audit_enabled"] = True
    base["b4_1_frontier_ledger_enabled"] = _probe_has_frontier_ledger(final_judge)
    base["hidden_negative_count"] = 0 if hidden_count is None else hidden_count
    base["hidden_negative_miss_reason_counts"] = hidden_miss_reason_counts
    base["hidden_negative_top_miss_reason"] = _first_str(
        payload.get("hidden_negative_top_miss_reason"),
        audit.get("hidden_negative_top_miss_reason"),
        audit.get("top_miss_reason"),
        _top_hidden_negative_miss_reason(hidden_miss_reason_counts),
    )
    base["hidden_negative_worker_not_generated_count"] = hidden_miss_reason_counts.get("worker_not_generated", 0)
    base["hidden_negative_pruned_by_dominance_count"] = hidden_miss_reason_counts.get("pruned_by_dominance", 0)
    base["hidden_negative_pricing_timeout_only_count"] = hidden_miss_reason_counts.get("pricing_timeout_only", 0)
    base["active_column_count"] = _payload_active_column_count(payload, final_judge)
    base["pool_column_count"] = _first_int(payload.get("pool_column_count"), final_judge.get("pool_column_count"))
    base["columns_added"] = _first_int(payload.get("added_column_count"), payload.get("columns_added"))
    base["active_columns_after_merge"] = _first_int(
        payload.get("active_columns_after_merge"),
        final_judge.get("active_columns_after_merge"),
    )
    base["harvest_selected_count"] = _first_int(final_judge.get("harvest_selected_count"), payload.get("harvest_selected_count"))
    base["harvest_candidate_negative_count"] = _first_int(
        final_judge.get("harvest_candidate_negative_count"),
        payload.get("harvest_candidate_negative_count"),
        payload.get("candidate_negative_count"),
    )
    base["harvest_selected_new_task_set_count"] = _first_int(
        final_judge.get("harvest_selected_new_task_set_count"),
        payload.get("harvest_selected_new_task_set_count"),
    )
    base["harvest_selected_replacement_task_set_count"] = _first_int(
        final_judge.get("harvest_selected_replacement_task_set_count"),
        payload.get("harvest_selected_replacement_task_set_count"),
    )
    base["new_task_set_count"] = base["harvest_selected_new_task_set_count"]
    base["replacement_task_set_count"] = base["harvest_selected_replacement_task_set_count"]
    base["best_negative_rc"] = _first_float(
        final_judge.get("negative_rc"),
        payload.get("best_negative_rc"),
        final_judge.get("best_reduced_cost"),
        payload.get("harvest_best_true_rc"),
    )
    base["last_best_reduced_cost"] = _first_float(
        final_judge.get("best_reduced_cost"),
        final_judge.get("pending_complete_min_rc"),
        payload.get("last_best_reduced_cost"),
    )
    base["final_judge_wall_time"] = _first_float(final_judge.get("final_judge_wall_time"), payload.get("elapsed_sec"))
    base["rmp_round_count"] = _first_int(payload.get("pricing_round_count"), final_judge.get("round"))
    base["harvest_rejected_duplicate_count"] = _first_int(
        final_judge.get("harvest_rejected_duplicate_count"),
        payload.get("harvest_rejected_duplicate_count"),
    )
    base["harvest_rejected_not_addable_count"] = _first_int(
        final_judge.get("harvest_rejected_not_addable_count"),
        payload.get("harvest_rejected_not_addable_count"),
    )
    base["harvest_source_phase"] = _first_str(
        final_judge.get("harvest_source_phase"),
        payload.get("harvest_source_phase"),
    )
    base["harvest_best_true_rc"] = _first_float(
        final_judge.get("harvest_best_true_rc"),
        payload.get("harvest_best_true_rc"),
    )
    base["harvest_worst_selected_true_rc"] = _first_float(
        final_judge.get("harvest_worst_selected_true_rc"),
        payload.get("harvest_worst_selected_true_rc"),
    )
    base["harvest_avg_pairwise_jaccard"] = _first_float(
        final_judge.get("harvest_avg_pairwise_jaccard"),
        payload.get("harvest_avg_pairwise_jaccard"),
    )
    base["compact_optimization_harvest_enabled"] = bool(
        final_judge.get(
            "compact_optimization_harvest_enabled",
            payload.get("compact_optimization_harvest_enabled", False),
        )
    )
    base["compact_optimization_harvest_target"] = _first_int(
        final_judge.get("compact_optimization_harvest_target"),
        payload.get("compact_optimization_harvest_target"),
    )
    base["compact_optimization_harvest_no_good_scope"] = final_judge.get(
        "compact_optimization_harvest_no_good_scope",
        payload.get("compact_optimization_harvest_no_good_scope", ""),
    )
    base["compact_optimization_harvest_found_count"] = _first_int(
        final_judge.get("compact_optimization_harvest_found_count"),
        payload.get("compact_optimization_harvest_found_count"),
    )
    base["compact_optimization_harvest_search_call_count"] = _first_int(
        final_judge.get("compact_optimization_harvest_search_call_count"),
        payload.get("compact_optimization_harvest_search_call_count"),
    )
    base["harvest_addability_audit_pass"] = final_judge.get(
        "harvest_addability_audit_pass",
        payload.get("harvest_addability_audit_pass", ""),
    )
    base["harvest_pricing_rc_audit_available"] = final_judge.get(
        "harvest_pricing_rc_audit_available",
        payload.get("harvest_pricing_rc_audit_available", ""),
    )
    base["harvest_pricing_rc_audit_pass"] = final_judge.get(
        "harvest_pricing_rc_audit_pass",
        payload.get("harvest_pricing_rc_audit_pass", ""),
    )
    base["harvest_pricing_rc_max_abs_diff"] = final_judge.get(
        "harvest_pricing_rc_max_abs_diff",
        payload.get("harvest_pricing_rc_max_abs_diff", ""),
    )
    history = payload.get("history") if isinstance(payload.get("history"), list) else []
    last_worker = _last_worker_payload(history)
    tail_payload = payload.get("tail_dual_stabilization") if isinstance(payload.get("tail_dual_stabilization"), dict) else {}
    if not tail_payload and isinstance(last_worker.get("tail_dual_stabilization"), dict):
        tail_payload = last_worker["tail_dual_stabilization"]
    base.update(_tail_dual_safety_fields(last_worker, tail_payload))
    base["fail_closed_reason"] = str(
        audit.get("status") or payload.get("fail_closed_reason") or payload.get("note") or ""
    )
    if not base["b4_1_frontier_ledger_enabled"]:
        base["global_remaining_rc_lb"] = ""
        base["underlying_global_remaining_rc_lb"] = ""
        base["frontier_coverage_complete"] = False
        base["underlying_frontier_coverage_complete"] = False
        base["frontier_unsupported_region_count"] = ""
        base["underlying_frontier_unsupported_region_count"] = ""
        base["pending_complete_min_rc"] = ""
        base["underlying_pending_complete_min_rc"] = ""
        base["pricing_proof_kind"] = ""
        base["underlying_pricing_proof_kind"] = ""
    return base


def _payload_is_worker_tail_hidden_negative_evidence(payload: dict) -> bool:
    audit = payload.get("hidden_negative_audit") if isinstance(payload.get("hidden_negative_audit"), dict) else {}
    if not audit:
        return False
    schema = str(payload.get("schema_version") or "")
    return bool(
        schema.startswith("lunar_ice_bpc.b2_")
        or schema.startswith("lunar_ice_bpc.b2b_")
        or payload.get("b2_mode")
        or payload.get("node_pricing_mode")
        or isinstance(payload.get("worker_seed_catalog"), dict)
    )


def _stage_b_evidence_key(row: dict) -> tuple[str, str, str, str]:
    return (
        str(Path(row.get("source_probe_json") or "")),
        str(row.get("round") or ""),
        str(row.get("variant") or ""),
        str(row.get("phase") or ""),
    )


def _probe_final_judge_variant(final_judge: dict) -> str:
    profile = str(final_judge.get("compact_final_judge_profile") or "").strip()
    formulation = str(final_judge.get("compact_final_judge_formulation_profile") or "").strip()
    if profile == "V4" or "B4V4" in formulation:
        return "V4_combined_endpoint_pair_latest_start_time_window"
    return "V2_latest_service_start_slot_bound"


def _probe_has_final_judge_harvest_telemetry(final_judge: dict) -> bool:
    if not any(
        key in final_judge
        for key in (
            "harvest_schema_version",
            "harvest_selected_count",
            "harvest_candidate_negative_count",
            "harvest_rejected_duplicate_count",
            "harvest_rejected_not_addable_count",
        )
    ):
        return False
    source_phase = str(final_judge.get("harvest_source_phase") or "")
    return not source_phase or _is_compact_final_judge_harvest_source(source_phase)


def _payload_has_final_judge_harvest_telemetry(payload: dict) -> bool:
    if not any(
        key in payload
        for key in (
            "harvest_schema_version",
            "harvest_selected_count",
            "harvest_candidate_negative_count",
            "harvest_rejected_duplicate_count",
            "harvest_rejected_not_addable_count",
        )
    ):
        return False
    return _is_compact_final_judge_harvest_source(str(payload.get("harvest_source_phase") or ""))


def _is_compact_final_judge_harvest_source(source_phase: str) -> bool:
    return str(source_phase or "").startswith("compact_final_judge")


def _probe_has_frontier_ledger(final_judge: dict) -> bool:
    return any(
        key in final_judge
        for key in (
            "global_remaining_rc_lb",
            "global_remaining_rc_lb_valid",
            "global_remaining_rc_lb_coverage_complete",
            "frontier_region_count",
            "frontier_unsupported_region_count",
            "pending_complete_min_rc",
            "pricing_proof_kind",
        )
    )


def _probe_hidden_negative_count(payload: dict) -> int | None:
    if "hidden_negative_count" in payload and payload.get("hidden_negative_count") not in {None, ""}:
        return int(payload.get("hidden_negative_count") or 0)
    audit = payload.get("hidden_negative_audit") if isinstance(payload.get("hidden_negative_audit"), dict) else {}
    if not audit:
        return None
    if "hidden_negative_count" in audit and audit.get("hidden_negative_count") not in {None, ""}:
        return int(audit.get("hidden_negative_count") or 0)
    return 0 if ("rows" in audit or "status" in audit) else None


def _payload_active_column_count(payload: dict, final_judge: dict | None = None) -> int:
    final_judge = final_judge or {}
    active_payloads = payload.get("active_columns")
    active_count = len(active_payloads) if isinstance(active_payloads, list) else ""
    return _first_int(
        payload.get("active_column_count"),
        final_judge.get("active_column_count"),
        payload.get("active_columns_after_merge"),
        final_judge.get("active_columns_after_merge"),
        active_count,
    )


def _last_worker_payload(history: object) -> dict:
    if not isinstance(history, list):
        return {}
    for row in reversed(history):
        if isinstance(row, dict) and row.get("final_judge_called") is False:
            return row
    return {}


def _tail_dual_safety_fields(worker_payload: dict | None = None, tail_payload: dict | None = None) -> dict:
    worker_payload = worker_payload if isinstance(worker_payload, dict) else {}
    tail_payload = tail_payload if isinstance(tail_payload, dict) else {}
    enabled = bool(tail_payload.get("tail_dual_stabilization_enabled"))
    return {
        "tail_dual_stabilization_enabled": enabled,
        "worker_dual_only": bool(worker_payload.get("worker_dual_only") or tail_payload.get("worker_dual_only")),
        "true_dual_rc_recomputed": bool(
            worker_payload.get("true_dual_rc_recomputed") or tail_payload.get("true_dual_rc_recomputed")
        ),
        "worker_dual_source": _first_str(
            worker_payload.get("worker_dual_source"),
            tail_payload.get("worker_dual_source"),
            worker_payload.get("diagnostic_dual_source") if enabled else "",
        ),
        "official_dual_source": _first_str(
            worker_payload.get("official_dual_source"),
            tail_payload.get("official_dual_source"),
            "current_true_rmp_dual" if enabled else "",
        ),
        "tail_dual_stabilization_alpha": tail_payload.get("tail_dual_stabilization_alpha", ""),
        "tail_dual_stabilization_window": tail_payload.get("tail_dual_stabilization_window", ""),
        "tail_dual_center_task_count": tail_payload.get("tail_dual_center_task_count", ""),
        "tail_dual_current_task_count": tail_payload.get("tail_dual_current_task_count", ""),
        "tail_dual_no_column_can_certify": bool(tail_payload.get("tail_dual_no_column_can_certify", False)),
    }


def _exception_row(
    *,
    stage: str,
    matrix_group: str,
    instance_path: str,
    scale: int,
    instance_id: str,
    mode: str,
    exc: Exception,
    wall_time: float,
) -> dict:
    return {
        "stage": stage,
        "matrix_group": matrix_group,
        "instance_path": instance_path,
        "source_probe_json": "",
        "scale": int(scale),
        "instance_id": instance_id,
        "mode": mode,
        "variant": "",
        "b4_1_matrix_cell": "exception_fail_closed",
        "b4_1_proof_tail_component": "",
        "b4_1_formulation_profile": "",
        "b4_1_harvesting_enabled": False,
        "b4_1_hidden_negative_audit_enabled": False,
        "b4_1_frontier_ledger_enabled": False,
        "b4_1_official_certificate_allowed": False,
        "phase": "exception",
        "round": "",
        "algorithm_status": "EXCEPTION_FAIL_CLOSED",
        "certificate_scope": "FEASIBLE_INCUMBENT_ONLY",
        "pricing_state": "INCOMPLETE_LIMIT",
        "exact_status": "NOT_SOLVED",
        "bpc_tree_optimal": False,
        "certificate_leak": 0,
        "manual_rc_fail": 0,
        "pricing_rc_fail": 0,
        "hidden_negative_count": "",
        "hidden_negative_miss_reason_counts": {},
        "hidden_negative_top_miss_reason": "",
        "hidden_negative_worker_not_generated_count": 0,
        "hidden_negative_pruned_by_dominance_count": 0,
        "hidden_negative_pricing_timeout_only_count": 0,
        "active_column_count": "",
        "pool_column_count": "",
        "columns_added": "",
        "active_columns_after_merge": "",
        "new_task_set_count": "",
        "replacement_task_set_count": "",
        "best_negative_rc": "",
        "last_best_reduced_cost": "",
        "final_judge_wall_time": "",
        "rmp_round_count": "",
        "diagnostic_claimed_certificate": 0,
        "wall_time": round(float(wall_time), 6),
        "fail_closed_reason": f"{type(exc).__name__}: {exc}",
    }


def _summary_rows(rows: list[dict]) -> list[dict]:
    groups: dict[tuple[str, str, str], list[dict]] = {}
    for row in rows:
        groups.setdefault((str(row.get("stage") or ""), str(row.get("mode") or ""), str(row.get("variant") or "")), []).append(row)
    summary = []
    for (stage, mode, variant), group in sorted(groups.items()):
        walls = [_float_or_none(row.get("wall_time")) for row in group]
        walls = [value for value in walls if value is not None]
        final_judge_walls = [_float_or_none(row.get("final_judge_wall_time")) for row in group]
        final_judge_walls = [value for value in final_judge_walls if value is not None]
        lbs = [_float_or_none(row.get("global_remaining_rc_lb")) for row in group]
        lbs = [value for value in lbs if value is not None]
        active_counts = [_float_or_none(row.get("active_column_count")) for row in group]
        active_counts = [value for value in active_counts if value is not None]
        active_after_counts = [_float_or_none(row.get("active_columns_after_merge")) for row in group]
        active_after_counts = [value for value in active_after_counts if value is not None]
        best_negative_rcs = [_float_or_none(row.get("best_negative_rc")) for row in group]
        best_negative_rcs = [value for value in best_negative_rcs if value is not None]
        last_best_rcs = [_float_or_none(row.get("last_best_reduced_cost")) for row in group]
        last_best_rcs = [value for value in last_best_rcs if value is not None]
        miss_reason_counts = _aggregate_hidden_negative_miss_reason_counts(group)
        summary.append(
            {
                "stage": stage,
                "mode": mode,
                "variant": variant,
                "row_count": len(group),
                "bpc_tree_optimal_count": sum(1 for row in group if row.get("bpc_tree_optimal") is True),
                "can_certify_no_negative_count": sum(1 for row in group if row.get("can_certify_no_negative") is True),
                "diagnostic_claimed_certificate_count": sum(
                    int(row.get("diagnostic_claimed_certificate") or 0) for row in group
                ),
                "hidden_negative_count": sum(int(row.get("hidden_negative_count") or 0) for row in group),
                "hidden_negative_miss_reason_counts": miss_reason_counts,
                "hidden_negative_top_miss_reason": _top_hidden_negative_miss_reason(miss_reason_counts),
                "negative_column_count": sum(int(row.get("negative_column_count") or 0) for row in group),
                "best_global_remaining_rc_lb": None if not lbs else round(max(lbs), 9),
                "mean_active_column_count": None if not active_counts else round(mean(active_counts), 6),
                "mean_active_columns_after_merge": None if not active_after_counts else round(mean(active_after_counts), 6),
                "best_negative_rc": None if not best_negative_rcs else round(min(best_negative_rcs), 9),
                "best_last_best_reduced_cost": None if not last_best_rcs else round(min(last_best_rcs), 9),
                "mean_final_judge_wall_time": None if not final_judge_walls else round(mean(final_judge_walls), 6),
                "mean_wall_time": None if not walls else round(mean(walls), 6),
            }
        )
    return summary


def _latest_stage_b_frontier_rows(rows: list[dict]) -> list[dict]:
    candidates = [
        row
        for row in rows
        if str(row.get("stage") or "") == "B"
        and str(row.get("mode") or "") == "B4.1_probe_final_judge_evidence"
        and _has_value(row.get("active_columns_after_merge") or row.get("active_column_count"))
    ]
    latest_by_variant: dict[tuple[str, str], dict] = {}
    for row in candidates:
        key = (str(row.get("mode") or ""), str(row.get("variant") or ""))
        current = latest_by_variant.get(key)
        if current is None or _frontier_sort_key(row) > _frontier_sort_key(current):
            latest_by_variant[key] = row
    latest = []
    for row in sorted(latest_by_variant.values(), key=lambda item: (str(item.get("mode") or ""), str(item.get("variant") or ""))):
        latest.append(
            {
                "stage": row.get("stage"),
                "mode": row.get("mode"),
                "variant": row.get("variant"),
                "source_probe_json": row.get("source_probe_json"),
                "active_column_count": _first_int(row.get("active_column_count")),
                "active_columns_after_merge": _first_int(
                    row.get("active_columns_after_merge"),
                    row.get("active_column_count"),
                ),
                "columns_added": _first_int(row.get("columns_added")),
                "negative_column_count": _first_int(row.get("negative_column_count")),
                "best_negative_rc": _first_float(row.get("best_negative_rc")),
                "last_best_reduced_cost": _first_float(row.get("last_best_reduced_cost")),
                "global_remaining_rc_lb": _first_float(row.get("global_remaining_rc_lb")),
                "frontier_unsupported_region_count": _first_int(row.get("frontier_unsupported_region_count")),
                "pricing_proof_kind": row.get("pricing_proof_kind"),
                "underlying_certificate_scope": row.get("underlying_certificate_scope"),
                "underlying_can_certify_no_negative": _bool_value(row.get("underlying_can_certify_no_negative")),
                "underlying_pricing_proof_kind": row.get("underlying_pricing_proof_kind"),
                "underlying_frontier_coverage_complete": _bool_value(
                    row.get("underlying_frontier_coverage_complete")
                ),
                "underlying_frontier_unsupported_region_count": _first_int(
                    row.get("underlying_frontier_unsupported_region_count")
                ),
                "certificate_scope": row.get("certificate_scope"),
                "final_judge_wall_time": _first_float(row.get("final_judge_wall_time")),
                "harvest_selected_count": _first_int(row.get("harvest_selected_count")),
                "harvest_selected_new_task_set_count": _first_int(row.get("harvest_selected_new_task_set_count")),
                "harvest_selected_replacement_task_set_count": _first_int(
                    row.get("harvest_selected_replacement_task_set_count")
                ),
            }
        )
    return latest


def _frontier_sort_key(row: dict) -> tuple[int, int, float, str]:
    return (
        _first_int(row.get("active_columns_after_merge"), row.get("active_column_count")),
        _first_int(row.get("columns_added")),
        _float_or_none(row.get("final_judge_wall_time")) or 0.0,
        str(row.get("source_probe_json") or ""),
    )


def _is_30_scale_row(row: dict) -> bool:
    if str(row.get("scale") or "") == "30":
        return True
    text = " ".join(
        str(row.get(key) or "")
        for key in ("instance_id", "instance_path", "source_probe_json", "matrix_group")
    )
    return "sp50_030" in text or "_030_" in text or "30-scale" in text


def _load_instance(item: str | Path | dict) -> tuple[dict, str]:
    if isinstance(item, dict):
        return item, str(item.get("source_path") or item.get("instance_path") or "")
    path = Path(item)
    return read_json(path), str(path)


def _count_by(rows: list[dict], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "")
        counts[value] = int(counts.get(value, 0)) + 1
    return dict(sorted(counts.items()))


def _normalize_b4_1_row(row: dict) -> dict:
    normalized = dict(row)
    hidden_audit = normalized.get("hidden_negative_audit")
    hidden_miss_counts = _normalize_hidden_negative_miss_reason_counts(
        normalized.get("hidden_negative_miss_reason_counts")
    )
    if not hidden_miss_counts and isinstance(hidden_audit, dict):
        hidden_miss_counts = _hidden_negative_miss_reason_counts(hidden_audit)
    if not _has_value(normalized.get("hidden_negative_miss_reason_counts")):
        normalized["hidden_negative_miss_reason_counts"] = hidden_miss_counts
    if not _has_value(normalized.get("hidden_negative_top_miss_reason")):
        normalized["hidden_negative_top_miss_reason"] = _top_hidden_negative_miss_reason(hidden_miss_counts)
    normalized.setdefault(
        "hidden_negative_worker_not_generated_count",
        hidden_miss_counts.get("worker_not_generated", 0),
    )
    normalized.setdefault(
        "hidden_negative_pruned_by_dominance_count",
        hidden_miss_counts.get("pruned_by_dominance", 0),
    )
    normalized.setdefault(
        "hidden_negative_pricing_timeout_only_count",
        hidden_miss_counts.get("pricing_timeout_only", 0),
    )
    if not _has_value(normalized.get("new_task_set_count")):
        normalized["new_task_set_count"] = normalized.get("harvest_selected_new_task_set_count", "")
    if not _has_value(normalized.get("replacement_task_set_count")):
        normalized["replacement_task_set_count"] = normalized.get("harvest_selected_replacement_task_set_count", "")
    if not _has_value(normalized.get("best_negative_rc")):
        best_candidate = _first_float(
            normalized.get("negative_rc"),
            normalized.get("best_negative_rc"),
            normalized.get("harvest_best_true_rc"),
            normalized.get("compact_pricing_best_rc"),
            normalized.get("pending_complete_min_rc"),
        )
        normalized["best_negative_rc"] = (
            best_candidate
            if best_candidate is not None and float(best_candidate) < -1.0e-9
            else ""
        )
    if not _has_value(normalized.get("last_best_reduced_cost")):
        normalized["last_best_reduced_cost"] = _first_float(
            normalized.get("last_best_reduced_cost"),
            normalized.get("compact_pricing_best_rc"),
            normalized.get("pending_complete_min_rc"),
            normalized.get("harvest_best_true_rc"),
        )
    if not _has_value(normalized.get("final_judge_wall_time")):
        normalized["final_judge_wall_time"] = _first_float(
            normalized.get("final_judge_wall_time"),
            normalized.get("wall_time"),
        )
    if not _has_value(normalized.get("rmp_round_count")):
        normalized["rmp_round_count"] = _first_int(
            normalized.get("rmp_round_count"),
            normalized.get("root_round_count"),
            normalized.get("round"),
        )
    tail_payload = normalized.get("tail_dual_stabilization") if isinstance(normalized.get("tail_dual_stabilization"), dict) else {}
    history = normalized.get("history") if isinstance(normalized.get("history"), list) else []
    last_worker = _last_worker_payload(history)
    if not tail_payload and isinstance(last_worker.get("tail_dual_stabilization"), dict):
        tail_payload = last_worker["tail_dual_stabilization"]
    tail_fields = _tail_dual_safety_fields(last_worker, tail_payload)
    for key, value in tail_fields.items():
        if tail_fields["tail_dual_stabilization_enabled"] or not _has_value(normalized.get(key)):
            normalized[key] = value
    for key in (
        "active_column_count",
        "pool_column_count",
        "columns_added",
        "active_columns_after_merge",
    ):
        normalized.setdefault(key, "")
    return normalized


def _hidden_negative_miss_reason_counts(audit: dict, fallback: object = None) -> dict[str, int]:
    for raw in (
        audit.get("hidden_negative_miss_reason_counts") if isinstance(audit, dict) else None,
        audit.get("miss_reason_counts") if isinstance(audit, dict) else None,
        fallback,
    ):
        counts = _normalize_hidden_negative_miss_reason_counts(raw)
        if counts:
            return counts
    rows = audit.get("rows") if isinstance(audit, dict) else None
    if not isinstance(rows, list):
        return {}
    counts = {reason: 0 for reason in HIDDEN_NEGATIVE_MISS_REASONS}
    for row in rows:
        if not isinstance(row, dict):
            continue
        reason = str(row.get("miss_reason") or "unknown")
        if reason not in counts:
            reason = "unknown"
        counts[reason] += 1
    return {reason: count for reason, count in counts.items() if count > 0}


def _normalize_hidden_negative_miss_reason_counts(raw: object) -> dict[str, int]:
    if raw is None or raw == "":
        return {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return {}
    if not isinstance(raw, dict):
        return {}
    counts = {reason: 0 for reason in HIDDEN_NEGATIVE_MISS_REASONS}
    for key, value in raw.items():
        reason = str(key or "unknown")
        if reason not in counts:
            reason = "unknown"
        try:
            count = int(value)
        except (TypeError, ValueError):
            continue
        if count > 0:
            counts[reason] += count
    return {reason: count for reason, count in counts.items() if count > 0}


def _aggregate_hidden_negative_miss_reason_counts(rows: Iterable[dict]) -> dict[str, int]:
    counts = {reason: 0 for reason in HIDDEN_NEGATIVE_MISS_REASONS}
    for row in rows:
        row_counts = _normalize_hidden_negative_miss_reason_counts(row.get("hidden_negative_miss_reason_counts"))
        if not row_counts and isinstance(row.get("hidden_negative_audit"), dict):
            row_counts = _hidden_negative_miss_reason_counts(row["hidden_negative_audit"])
        for reason, count in row_counts.items():
            counts[reason] += int(count)
    return {reason: count for reason, count in counts.items() if count > 0}


def _top_hidden_negative_miss_reason(counts: dict[str, int]) -> str:
    normalized = _normalize_hidden_negative_miss_reason_counts(counts)
    if not normalized:
        return ""
    return max(
        normalized,
        key=lambda reason: (
            int(normalized.get(reason, 0)),
            -HIDDEN_NEGATIVE_MISS_REASONS.index(reason)
            if reason in HIDDEN_NEGATIVE_MISS_REASONS
            else -len(HIDDEN_NEGATIVE_MISS_REASONS),
        ),
    )


def _format_miss_reason_counts(counts: dict[str, int]) -> str:
    normalized = _normalize_hidden_negative_miss_reason_counts(counts)
    if not normalized:
        return "none"
    return ", ".join(
        f"{reason}={normalized[reason]}"
        for reason in HIDDEN_NEGATIVE_MISS_REASONS
        if normalized.get(reason, 0) > 0
    )


def _diagnostic_claimed_certificate(certificate_scope: str, final_judge: dict) -> int:
    if certificate_scope not in {"DIAGNOSTIC_PRICING_FRONTIER", "DIAGNOSTIC_RMP_BOUND"}:
        return 0
    return int(bool(final_judge.get("can_certify_no_negative")))


def _stage_a_regression_coverage(rows: Iterable[dict]) -> dict[str, list[str]]:
    observed = {
        str(row.get("mode") or "")
        for row in rows
        if str(row.get("mode") or "") in B41_STAGE_A_REQUIRED_REGRESSION_MODES
    }
    missing = [mode for mode in B41_STAGE_A_REQUIRED_REGRESSION_MODES if mode not in observed]
    return {"observed": sorted(observed), "missing": missing}


def _stage_b_matrix_coverage(rows: Iterable[dict]) -> dict[str, list[str]]:
    observed: set[str] = set()
    for row in rows:
        observed.update(_stage_b_matrix_cells_for_row(row))
    missing = [cell for cell in B41_STAGE_B_REQUIRED_MATRIX_CELLS if cell not in observed]
    return {"observed": sorted(observed), "missing": missing}


def _build_requirement_audit(
    *,
    rows: list[dict],
    stage_a_rows: list[dict],
    stage_b_rows: list[dict],
    stage_c_rows: list[dict],
    redlines: dict,
    diagnostics: dict,
    acceptance: dict,
) -> list[dict]:
    redline_failures = {key: value for key, value in redlines.items() if int(value or 0) != 0}
    stage_bc_rows = [row for row in rows if str(row.get("stage") or "") in {"B", "C"}]
    stage_bc_certificate_claims = [
        row
        for row in stage_bc_rows
        if _bool_value(row.get("can_certify_no_negative"))
        or str(row.get("certificate_scope") or "") not in {"", "DIAGNOSTIC_PRICING_FRONTIER"}
    ]
    frontier_official_rows = [row for row in stage_bc_rows if _bool_value(row.get("frontier_lb_official"))]
    tail_enabled = int(diagnostics.get("tail_dual_enabled_count") or 0)
    tail_worker_only = int(diagnostics.get("tail_dual_worker_only_count") or 0)
    tail_recomputed = int(diagnostics.get("tail_dual_true_dual_recomputed_count") or 0)
    tail_official_true = int(diagnostics.get("tail_dual_official_true_dual_source_count") or 0)
    tail_no_column_certifies = int(diagnostics.get("tail_dual_no_column_can_certify_count") or 0)
    stage_c_selected_rows = [
        row
        for row in stage_c_rows
        if str(row.get("mode") or "") == "B4.1_selected_30_diagnostic"
        or str(row.get("matrix_group") or "").lower().find("selected") >= 0
    ]
    thirty_scale_certified_rows = [
        row
        for row in rows
        if str(row.get("scale") or "") == "30"
        and str(row.get("certificate_scope") or "") == CertificateScope.BPC_TREE_OPTIMAL.value
    ]
    audit = [
        _requirement_item(
            "R1_redlines_zero",
            "All certificate, RC, resource, exception, and tail-dual safety redlines are zero.",
            "pass" if not redline_failures else "fail",
            {
                "redline_failures": redline_failures,
                "redline_count": len(redlines),
            },
            "Fix failing redlines before interpreting any B4.1 diagnostic as evidence.",
        ),
        _requirement_item(
            "R2_stage_a_regression_clean",
            "Stage A regression rows are present and clean.",
            "pass"
            if acceptance.get("stage_a_regression_clean")
            else "missing"
            if (not stage_a_rows or diagnostics.get("stage_a_missing_regression_modes"))
            else "fail",
            {
                "stage_a_row_count": len(stage_a_rows),
                "stage_a_regression_clean": bool(acceptance.get("stage_a_regression_clean")),
                "observed_modes": diagnostics.get("stage_a_observed_regression_modes") or [],
                "missing_modes": diagnostics.get("stage_a_missing_regression_modes") or [],
            },
            "Run/import Stage A 5/10/20 regression rows and keep redlines at zero.",
        ),
        _requirement_item(
            "R3_stage_b_matrix_complete",
            "Stage B planned diagnostic matrix covers all required B4.1 cells.",
            "pass" if acceptance.get("stage_b_matrix_complete") else "missing" if not stage_b_rows else "incomplete",
            {
                "stage_b_row_count": len(stage_b_rows),
                "observed": diagnostics.get("stage_b_observed_matrix_cells") or [],
                "missing": diagnostics.get("stage_b_missing_matrix_cells") or [],
            },
            "Import or run evidence for every missing Stage B matrix cell.",
        ),
        _requirement_item(
            "R4_stage_c_selected_diagnostic",
            "Stage C selected 30-scale diagnostic rows are present and do not claim certificates.",
            "pass" if stage_c_selected_rows and acceptance.get("stage_c_diagnostic_clean") else "missing" if not stage_c_selected_rows else "fail",
            {
                "stage_c_row_count": len(stage_c_rows),
                "stage_c_selected_row_count": len(stage_c_selected_rows),
                "stage_c_diagnostic_clean": bool(acceptance.get("stage_c_diagnostic_clean")),
            },
            "Run/import the selected 30-scale Stage C diagnostic rows.",
        ),
        _requirement_item(
            "R5_stage_bc_diagnostic_only",
            "Stage B/C rows remain diagnostic-only unless a true-dual no-negative proof is actually certified.",
            "pass" if not stage_bc_certificate_claims and not frontier_official_rows else "fail",
            {
                "stage_bc_row_count": len(stage_bc_rows),
                "stage_bc_certificate_claim_count": len(stage_bc_certificate_claims),
                "frontier_lb_official_row_count": len(frontier_official_rows),
            },
            "Downgrade diagnostic rows or prove full true-dual no-negative certification before enabling certificate claims.",
        ),
        _requirement_item(
            "R6_tail_dual_worker_only",
            "Tail dual stabilization is worker-only and every tail-dual candidate path is true-dual RC recomputed.",
            "pass"
            if tail_enabled == 0
            or (
                int(redlines.get("tail_dual_certificate_leak_count") or 0) == 0
                and tail_worker_only == tail_enabled
                and tail_recomputed == tail_enabled
                and tail_official_true == tail_enabled
                and tail_no_column_certifies == 0
            )
            else "fail",
            {
                "tail_dual_enabled_count": tail_enabled,
                "tail_dual_worker_only_count": tail_worker_only,
                "tail_dual_true_dual_recomputed_count": tail_recomputed,
                "tail_dual_official_true_dual_source_count": tail_official_true,
                "tail_dual_no_column_can_certify_count": tail_no_column_certifies,
                "tail_dual_certificate_leak_count": int(redlines.get("tail_dual_certificate_leak_count") or 0),
            },
            "Keep tail dual as candidate-search telemetry only; recompute selected columns under the current true RMP dual.",
        ),
        _requirement_item(
            "R7_30_scale_exact_closure",
            "30-scale exact BPC_TREE_OPTIMAL closure is proven.",
            "pass" if thirty_scale_certified_rows else "incomplete",
            {
                "thirty_scale_bpc_tree_optimal_count": len(thirty_scale_certified_rows),
                "thirty_scale_underlying_node_lp_certified_count": int(
                    diagnostics.get("thirty_scale_underlying_node_lp_certified_count") or 0
                ),
                "thirty_scale_underlying_exhaustive_no_negative_count": int(
                    diagnostics.get("thirty_scale_underlying_exhaustive_no_negative_count") or 0
                ),
                "known_boundary": (
                    "A 30-scale root LP no-negative proof can be recorded as underlying evidence, "
                    "but R7 remains incomplete until BPC_TREE_OPTIMAL is proven."
                ),
            },
            "Use the root no-negative proof as B4.1 tail evidence, then continue tree-level closure work toward BPC_TREE_OPTIMAL.",
        ),
    ]
    return audit


def _requirement_item(
    requirement_id: str,
    requirement: str,
    status: str,
    evidence: dict,
    next_action: str,
) -> dict:
    return {
        "id": requirement_id,
        "requirement": requirement,
        "status": status,
        "evidence": evidence,
        "next_action": next_action if status != "pass" else "",
    }


def _stage_b_matrix_cells_for_row(row: dict) -> tuple[str, ...]:
    cells: list[str] = []
    variant = str(row.get("variant") or "")
    matrix_cell = str(row.get("b4_1_matrix_cell") or "")
    if variant == "V2_latest_service_start_slot_bound" or matrix_cell == "B4V2_frontier_ledger_diagnostic":
        cells.append("B4V2_baseline")
        if bool(row.get("b4_1_frontier_ledger_enabled")):
            cells.append("B4V2_frontier_ledger_diagnostic")
        if _row_has_b4_1_final_judge_harvesting(row):
            cells.append("B4V2_harvesting")
        if bool(row.get("b4_1_hidden_negative_audit_enabled")):
            cells.append("B4V2_hidden_negative_audit")
        if _row_has_b4_1_final_judge_harvesting(row) and bool(row.get("b4_1_frontier_ledger_enabled")):
            cells.append("B4V2_harvesting_frontier_ledger_diagnostic")
    if variant == "V4_combined_endpoint_pair_latest_start_time_window" or matrix_cell == "B4V4_combined_formulation_diagnostic":
        cells.append("B4V4_combined_formulation_diagnostic")
    return tuple(dict.fromkeys(cells))


def _row_has_b4_1_final_judge_harvesting(row: dict) -> bool:
    if not bool(row.get("b4_1_harvesting_enabled")):
        return False
    source_phase = str(row.get("harvest_source_phase") or "")
    if _is_compact_final_judge_harvest_source(source_phase):
        return True
    return bool(
        not source_phase
        and str(row.get("mode") or "") == "B4.1_probe_final_judge_evidence"
        and str(row.get("phase") or "") == "probe_final_judge_evidence"
    )


def _stage_a_matrix_cell(mode: str) -> str:
    if mode == B41_STAGE_A_B3B_BASELINE:
        return "B3B_accepted_tree_baseline"
    if mode == B41_STAGE_A_B4V2_HARVEST:
        return "B4V2_final_judge_harvesting"
    if mode == B41_STAGE_A_TAIL_DUAL_OFF:
        return "B2B_R2_worker_tail_dual_off"
    if mode == B41_STAGE_A_TAIL_DUAL_ON:
        return "B2B_R2_worker_tail_dual_on"
    return str(mode or "")


def _stage_a_component(mode: str) -> str:
    if mode in {B41_STAGE_A_B3B_BASELINE, B41_STAGE_A_B4V2_HARVEST}:
        return "true_dual_final_judge_tree_closure"
    if mode in {B41_STAGE_A_TAIL_DUAL_OFF, B41_STAGE_A_TAIL_DUAL_ON}:
        return "worker_candidate_search_tail_dual_diagnostic"
    return ""


def _stage_probe_matrix_cell(variant: str) -> str:
    if variant == "V2_latest_service_start_slot_bound":
        return "B4V2_frontier_ledger_diagnostic"
    if variant == "V4_combined_endpoint_pair_latest_start_time_window":
        return "B4V4_combined_formulation_diagnostic"
    return f"{variant}_frontier_ledger_diagnostic" if variant else "frontier_ledger_diagnostic"


def _stage_probe_formulation_profile(variant: str) -> str:
    if variant == "V2_latest_service_start_slot_bound":
        return "B4V2_latest_start_only"
    if variant == "V4_combined_endpoint_pair_latest_start_time_window":
        return "B4V4_endpoint_pair_latest_start_time_window"
    return str(variant or "")


def _csv_value(value):
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if value is None:
        return ""
    return value


def _compact_markdown_json(value: object) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return text.replace("|", "\\|")


def _first_float(*values: object) -> float | None:
    for value in values:
        if value is None or value == "":
            continue
        try:
            return round(float(value), 9)
        except (TypeError, ValueError):
            continue
    return None


def _float_or_none(value: object) -> float | None:
    return _first_float(value)


def _first_int(*values: object) -> int:
    for value in values:
        if value is None or value == "":
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return 0


def _first_str(*values: object) -> str:
    for value in values:
        if value is None or value == "":
            continue
        return str(value)
    return ""


def _has_value(value: object) -> bool:
    return value is not None and value != ""


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


_CERTIFYING_SCOPES = {
    CertificateScope.BPC_NODE_LP_CERTIFIED.value,
    CertificateScope.BPC_TREE_OPTIMAL.value,
}

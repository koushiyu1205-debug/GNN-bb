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
    DIRECT_LABEL_WORKER,
    solve_b2_pricing_tail_baseline,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.core.journey import journey_column_from_solution_payload
from lunar_ice_bpc.exact.master.journey_rmp import (
    JourneyDuals,
    manual_journey_reduced_cost,
    solve_restricted_journey_rmp,
)
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
    "V4_current_dual_task_slot_lb_gate": {
        **B4D_VARIANT_CONFIGS["V4_combined_endpoint_pair_latest_start_time_window"],
        "formulation_kind": "endpoint_pair_latest_timewindow+service_return_pair_duration+slot_position+pair_energy_infeasible+pair_timewindow_infeasible+dual_task_slot_lb_gate",
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
        "dual_task_slot_lower_bound": True,
    },
    "V4_current_pair_conflict_capacity_bound": {
        **B4D_VARIANT_CONFIGS["V4_combined_endpoint_pair_latest_start_time_window"],
        "formulation_kind": "endpoint_pair_latest_timewindow+service_return_pair_duration+slot_position+pair_energy_infeasible+pair_timewindow_infeasible+pair_conflict_capacity_bound",
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
        "task_slot_pair_conflict_capacity_bound": True,
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
    "negative_feasibility_search_enabled",
    "negative_feasibility_zero_objective_enabled",
    "objective_bound_no_negative_cutoff_enabled",
    "objective_bound_no_negative_cutoff_value",
    "objective_bound_no_negative_cutoff_can_certify",
    "zero_capacity_slot_truncation_enabled",
    "zero_capacity_slot_truncation_original_slot_count",
    "zero_capacity_slot_truncation_effective_slot_count",
    "zero_capacity_slot_truncation_trimmed_slot_count",
    "zero_capacity_slot_truncation_first_zero_slot",
    "slot_sequence_capacity_live_bound_enabled",
    "slot_sequence_capacity_live_bound_tightened_slot_count",
    "slot_sequence_capacity_live_bound_by_slot",
    "tight_service_start_bounds_enabled",
    "tight_service_start_bound_count",
    "tight_service_start_bound_min",
    "tight_service_start_bound_max",
    "tight_time_arc_big_m_enabled",
    "tight_time_arc_big_m_depot_arc_count",
    "tight_time_arc_big_m_active_time_bound_count",
    "tight_time_arc_big_m_max_reduction",
    "tight_conditional_sequence_big_m_enabled",
    "tight_conditional_sequence_big_m_count",
    "tight_conditional_sequence_big_m_max_reduction",
    "slot_service_start_y_lower_bound_enabled",
    "slot_service_start_y_lower_bound_count",
    "slot_service_start_y_lower_bound_max_lift",
    "slot_service_start_y_lower_bound_min",
    "slot_service_start_y_lower_bound_max",
    "sortie_start_upper_bound",
    "pricing_complete_by_dual_bound",
    "dual_bound_can_certify_no_negative",
    "variable_count",
    "constraint_count",
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
    "labeling_final_judge_exact_harvest_target",
    "labeling_final_judge_exact_harvest_target_source",
    "exact_negative_harvest_target",
    "exact_negative_harvest_candidate_count",
    "exact_negative_harvest_selected_count",
    "exact_negative_harvest_selected_new_task_set_count",
    "exact_negative_harvest_selected_replacement_task_set_count",
    "exact_negative_harvest_selection_policy",
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
    "compact_pricing_phase",
    "route_template_pre_harvest_enabled",
    "route_template_pre_harvest_status",
    "route_template_pre_harvest_target",
    "route_template_pre_harvest_time_cap_sec",
    "route_template_pre_harvest_max_direct_tasks",
    "route_template_pre_harvest_max_active_seeds",
    "route_template_pre_harvest_seed_strategy",
    "route_template_pre_harvest_neighborhood_enabled",
    "route_template_pre_harvest_max_neighborhood_seeds",
    "route_template_pre_harvest_max_candidate_sets",
    "route_template_pre_harvest_seed_count",
    "route_template_pre_harvest_candidate_round_count",
    "route_template_pre_harvest_candidate_round_limit",
    "route_template_pre_harvest_candidate_negative_count",
    "route_template_pre_harvest_selected_count",
    "route_template_pre_harvest_selected_new_task_set_count",
    "route_template_pre_harvest_selected_replacement_task_set_count",
    "route_template_pre_harvest_pricing_wall_time_sec",
    "route_template_pre_harvest_fallback_enabled",
    "compact_optimization_harvest_enabled",
    "compact_optimization_harvest_target",
    "compact_optimization_harvest_no_good_scope",
    "compact_optimization_harvest_found_count",
    "compact_optimization_harvest_search_call_count",
    "harvest_addability_audit_pass",
    "harvest_pricing_rc_audit_available",
    "harvest_pricing_rc_audit_pass",
    "harvest_pricing_rc_max_abs_diff",
    "worker_pricer_kind",
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
    "candidate_search_false_positive_rate",
    "true_negative_candidate_search_miss_rate",
    "candidate_search_false_positive_row_count",
    "true_negative_candidate_search_miss_row_count",
    "candidate_search_negative_true_nonnegative_count",
    "true_negative_candidate_search_nonnegative_count",
    "candidate_search_dual_matches_true_dual",
    "candidate_search_rc_recomputed_under_true_dual",
    "worker_true_dual_candidate_audit_pass",
    "worker_candidate_universe_task_set_count",
    "worker_generated_column_task_set_count",
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
    "sortie_slots_per_journey",
    "sortie_slot_bound_source",
    "sortie_slot_horizon_count_bound",
    "sortie_slot_latest_start_count_bound",
    "sortie_slot_min_duration_lower_bound",
    "sortie_slot_min_energy_recharge_duration_lower_bound",
    "slot_task_time_pruning_enabled",
    "slot_task_time_feasible_assignment_count",
    "slot_task_time_pruned_assignment_count",
    "slot_task_time_pruned_due_count",
    "slot_task_time_pruned_horizon_count",
    "slot_task_time_total_assignment_count",
    "slot_task_time_original_total_assignment_count",
    "slot_task_model_assignment_count",
    "slot_arc_support_pruning_enabled",
    "slot_arc_support_feasible_assignment_count",
    "slot_arc_support_pruned_assignment_count",
    "slot_arc_support_pruned_unreachable_count",
    "slot_arc_support_pruned_no_return_count",
    "slot_arc_support_pruned_option_count",
    "slot_arc_time_pruned_option_count",
    "slot_sequence_capacity_arc_pruning_enabled",
    "slot_sequence_capacity_arc_pruned_option_count",
    "slot_sequence_capacity_mtz_disabled_slot_count",
    "single_task_per_active_sortie_arc_pruning_enabled",
    "single_task_per_active_sortie_arc_pruned_option_count",
    "single_task_per_active_sortie_mtz_disabled",
    "mtz_connectivity_effective",
    "fixed_active_sortie_redundant_constraint_skipped_count",
    "single_task_per_active_sortie_slot_visit_eq_count",
    "single_task_per_active_sortie_y_z_link_skipped_count",
    "resource_arc_pruning_enabled",
    "resource_arc_pruned_option_count",
    "resource_arc_energy_pruned_option_count",
    "resource_arc_shadow_pruned_option_count",
    "resource_arc_demand_pruned_option_count",
    "slot_task_sequence_capacity_upper_bound",
    "slot_task_sequence_capacity_limited_slot_count",
    "slot_task_sequence_capacity_empty_slot_count",
    "slot_task_matching_capacity_upper_bound",
    "single_journey_mip_start_enabled",
    "single_journey_mip_start_status",
    "single_journey_mip_start_source",
    "single_journey_mip_start_entry_count",
    "single_journey_mip_start_zero_fill_integers",
    "single_journey_mip_start_zero_fill_integer_entry_count",
    "single_journey_mip_start_inactive_tail_time_entry_count",
    "single_journey_mip_start_inactive_tail_time_mode",
    "single_journey_mip_start_sort_indices",
    "single_journey_mip_start_sortie_count",
    "single_journey_mip_start_task_count",
    "single_journey_mip_start_objective",
    "single_journey_mip_start_reduced_cost",
    "required_task_set_enabled",
    "required_task_set_count",
    "pricing_model_task_count",
    "required_task_set_model_reduction_enabled",
    "required_task_set_model_task_count",
    "required_task_set_model_task_reduction_count",
    "required_task_set_region_can_certify_no_negative",
    "pricing_complete_for_required_task_set",
    "required_task_set_infeasible_by_feasible_task_count",
    "required_task_set_infeasible_by_slot_capacity",
    "required_task_set_infeasible_by_slot_sequence_capacity",
    "required_task_set_infeasible_by_slot_matching",
    "required_task_count_enabled",
    "required_task_count",
    "required_task_count_region_can_certify_no_negative",
    "pricing_complete_for_required_task_count",
    "required_task_count_feasible_task_count",
    "required_task_count_slot_capacity_task_upper_bound",
    "required_task_count_slot_sequence_capacity_upper_bound",
    "required_task_count_slot_matching_capacity_upper_bound",
    "required_task_count_pair_conflict_capacity_upper_bound",
    "required_task_count_min_active_sorties",
    "required_task_count_active_sortie_lb_count",
    "required_task_count_infeasible_by_feasible_task_count",
    "required_task_count_infeasible_by_slot_capacity",
    "required_task_count_infeasible_by_slot_sequence_capacity",
    "required_task_count_infeasible_by_slot_matching",
    "required_task_count_infeasible_by_pair_conflict_capacity",
    "required_task_count_certified_by_dual_task_slot_lower_bound",
    "required_task_count_infeasible_by_dual_task_slot_lower_bound",
    "dual_task_slot_lower_bound_enabled",
    "dual_task_slot_lower_bound_applicable",
    "dual_task_slot_lower_bound_optimal",
    "dual_task_slot_lower_bound_status",
    "dual_task_slot_lower_bound_value",
    "dual_task_slot_lower_bound_region_infeasible",
    "dual_task_slot_lower_bound_route_arc_mode",
    "dual_task_slot_lower_bound_route_arc_value",
    "dual_task_slot_lower_bound_route_arc_row_count",
    "dual_task_slot_lower_bound_route_arc_global_constant",
    "dual_task_slot_lower_bound_route_arc_slot_constant",
    "dual_task_slot_lower_bound_route_arc_constant",
    "dual_task_slot_lower_bound_route_arc_slot_outbound_sum",
    "dual_task_slot_lower_bound_route_arc_slot_return_sum",
    "dual_task_slot_lower_bound_single_task_route_arc_bound_row_count",
    "dual_task_slot_lower_bound_single_task_route_arc_bound_min",
    "dual_task_slot_lower_bound_single_task_route_arc_bound_max",
    "dual_task_slot_lower_bound_one_pair_rest_single_route_arc_var_count",
    "dual_task_slot_lower_bound_one_pair_rest_single_route_arc_row_count",
    "dual_task_slot_lower_bound_one_pair_rest_single_route_arc_pair_count",
    "dual_task_slot_lower_bound_one_pair_rest_single_route_arc_separation_row_count",
    "dual_task_slot_lower_bound_one_pair_rest_single_route_arc_separation_iteration_count",
    "dual_task_slot_lower_bound_pair_route_arc_bound_row_count",
    "dual_task_slot_lower_bound_pair_route_arc_bound_min",
    "dual_task_slot_lower_bound_pair_route_arc_bound_max",
    "dual_task_slot_lower_bound_triple_route_arc_bound_row_count",
    "dual_task_slot_lower_bound_triple_route_arc_bound_min",
    "dual_task_slot_lower_bound_triple_route_arc_bound_max",
    "dual_task_slot_lower_bound_pair_completion_lift_var_count",
    "dual_task_slot_lower_bound_pair_completion_lift_row_count",
    "dual_task_slot_lower_bound_pair_completion_lift_min",
    "dual_task_slot_lower_bound_pair_completion_lift_max",
    "dual_task_slot_lower_bound_cross_slot_completion_lift_var_count",
    "dual_task_slot_lower_bound_cross_slot_completion_lift_row_count",
    "dual_task_slot_lower_bound_cross_slot_pair_completion_separation_row_count",
    "dual_task_slot_lower_bound_cross_slot_completion_lift_min",
    "dual_task_slot_lower_bound_cross_slot_completion_lift_max",
    "dual_task_slot_lower_bound_wall_time_sec",
    "dual_task_slot_lower_bound_variable_count",
    "dual_task_slot_lower_bound_constraint_count",
    "dual_task_slot_lower_bound_pair_conflict_row_count",
    "dual_task_slot_lower_bound_hyperedge_conflict_row_count",
    "dual_task_slot_full_space_lower_bound_enabled",
    "dual_task_slot_full_space_lower_bound_applicable",
    "dual_task_slot_full_space_lower_bound_early_stop_on_negative",
    "dual_task_slot_full_space_lower_bound_early_stopped_on_negative",
    "dual_task_slot_full_space_lower_bound_coverage_complete",
    "dual_task_slot_full_space_lower_bound_can_certify",
    "dual_task_slot_full_space_lower_bound_region_count",
    "dual_task_slot_full_space_lower_bound_optimal_region_count",
    "dual_task_slot_full_space_lower_bound_infeasible_region_count",
    "dual_task_slot_full_space_lower_bound_unsupported_region_count",
    "dual_task_slot_full_space_lower_bound_negative_region_count",
    "dual_task_slot_full_space_lower_bound_value",
    "dual_task_slot_full_space_lower_bound_task_count",
    "dual_task_slot_full_space_lower_bound_active_sortie_count",
    "dual_task_slot_full_space_lower_bound_wall_time_sec",
    "dual_task_slot_full_space_lower_bound_status",
    "task_slot_pair_conflict_capacity_near_matching_cap",
    "task_slot_pair_conflict_capacity_bound_requested",
    "task_slot_pair_conflict_capacity_bound_enabled",
    "task_slot_pair_conflict_capacity_bound_optimal",
    "task_slot_pair_conflict_capacity_bound_status",
    "task_slot_pair_conflict_capacity_bound_wall_time_sec",
    "task_slot_pair_conflict_capacity_bound_variable_count",
    "task_slot_pair_conflict_capacity_bound_constraint_count",
    "task_slot_pair_conflict_capacity_pair_count",
    "task_slot_pair_conflict_capacity_row_count",
    "task_slot_pair_conflict_capacity_hyperedge_count",
    "task_slot_pair_conflict_capacity_hyperedge_row_count",
    "required_active_sortie_count_enabled",
    "required_active_sortie_count",
    "required_active_sortie_count_region_can_certify_no_negative",
    "pricing_complete_for_required_active_sortie_count",
    "required_active_sortie_count_min",
    "required_active_sortie_count_max",
    "required_active_sortie_count_capacity_min",
    "required_active_sortie_count_expected_counts",
    "required_active_sortie_count_infeasible",
    "required_active_sortie_count_infeasible_by_empty_slot",
    "required_active_sortie_count_infeasible_by_capacity_min",
    "required_active_sortie_count_slots_fixed",
    "required_active_sortie_count_fixed_slot_count",
    "forbidden_task_set_skipped_by_required_task_count",
    "residual_task_count_partition_enabled",
    "residual_task_count_region_expected_count",
    "residual_task_count_region_observed_count",
    "residual_task_count_region_proven_count",
    "residual_task_count_region_incomplete_count",
    "residual_task_count_region_negative_count",
    "residual_task_count_region_missing_count",
    "residual_task_count_region_missing_counts",
    "residual_active_sortie_count_partition_enabled",
    "residual_active_sortie_count_missing_group_count",
    "residual_active_sortie_count_duplicate_group_count",
    "partition_candidate_audit_json",
    "partition_probe_json",
    "partition_target_task_set_count",
    "partition_candidate_gate_pass",
    "partition_candidate_gate_issue_count",
    "partition_candidate_gate_issue_codes",
    "partition_candidate_gate_full_space_partition_valid",
    "partition_candidate_gate_exact_region_count",
    "partition_candidate_gate_exact_regions_proven",
    "partition_candidate_gate_residual_proven",
    "partition_candidate_can_certify_no_negative",
    "partition_candidate_redline_fail_count",
    "partition_candidate_row_certificate_claim_count",
    "partition_best_region_lb",
    "partition_bound_gap_to_zero",
    "partition_negative_region_count",
    "partition_negative_exact_region_count",
    "partition_negative_residual_region_count",
    "partition_negative_payload_available_count",
    "partition_best_negative_rc",
    "partition_negative_already_active_count",
    "partition_negative_replacement_task_set_count",
    "partition_negative_new_task_set_count",
    "partition_source_active_column_count",
    "partition_dual_active_column_count",
    "partition_dual_source",
    "partition_dual_refresh_status",
    "partition_dual_refresh_min_rc",
    "partition_dual_refresh_negative_count",
    "partition_dual_refresh_input_column_count",
    "partition_dual_refresh_rmp_active_column_count",
    "partition_active_pool_after_dual_delta",
    "partition_dual_scope_matches_active_pool",
    "partition_dual_scope_mismatch_count",
    "partition_negative_manual_rc",
    "partition_negative_pricing_rc_diff",
    "partition_negative_rc_audit_pass",
    "partition_negative_rc_audit_fail_count",
    "partition_negative_feasibility_fallback_enabled",
    "partition_negative_feasibility_fallback_run",
    "partition_negative_feasibility_fallback_used",
    "partition_negative_feasibility_fallback_status",
    "partition_negative_feasibility_fallback_exact_status",
    "partition_optimization_best_reduced_cost",
    "partition_optimization_dual_bound",
    "partition_optimization_exact_status",
    "partition_region_variable_count_max",
    "partition_region_constraint_count_max",
    "partition_region_variable_count_mean",
    "partition_region_constraint_count_mean",
    "partition_region_slot_task_time_feasible_assignment_count_max",
    "partition_region_slot_task_time_pruned_assignment_count_sum",
    "partition_region_slot_arc_time_pruned_option_count_sum",
    "partition_region_single_task_per_active_sortie_arc_pruned_option_count_sum",
    "partition_region_resource_arc_pruned_option_count_sum",
    "partition_region_resource_arc_energy_pruned_option_count_sum",
    "partition_region_resource_arc_shadow_pruned_option_count_sum",
    "partition_region_resource_arc_demand_pruned_option_count_sum",
    "partition_region_mip_start_enabled_count",
    "partition_region_mip_start_ok_count",
    "partition_exact_region_mip_start_ok_count",
    "partition_residual_region_mip_start_ok_count",
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
    labeling_final_judge_exact_harvest_target: int | None = None,
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
                    labeling_final_judge_exact_harvest_target=labeling_final_judge_exact_harvest_target,
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
    labeling_final_judge_exact_harvest_target: int | None = None,
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
        labeling_final_judge_exact_harvest_target=labeling_final_judge_exact_harvest_target,
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
        labeling_final_judge_exact_harvest_target=labeling_final_judge_exact_harvest_target,
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
    tail_dual_stabilization_enabled: bool = False,
    tail_dual_stabilization_alpha: float = 0.7,
    tail_dual_stabilization_window: int = 5,
    worker_pricer_kind: str = DIRECT_LABEL_WORKER,
    labeling_final_judge_enabled: bool | None = None,
    labeling_final_judge_max_exact_tasks: int | None = None,
    labeling_final_judge_exact_harvest_target: int | None = None,
    live_sri_policy: str = "no_cut",
    development_branch_rank_index: int = 0,
    development_branch_rank_by_path: dict[tuple[str, ...], int] | None = None,
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
        tail_dual_stabilization_enabled=bool(tail_dual_stabilization_enabled),
        tail_dual_stabilization_alpha=float(tail_dual_stabilization_alpha),
        tail_dual_stabilization_window=int(tail_dual_stabilization_window),
        worker_pricer_kind=str(worker_pricer_kind),
        labeling_final_judge_enabled=labeling_final_judge_enabled,
        labeling_final_judge_max_exact_tasks=labeling_final_judge_max_exact_tasks,
        labeling_final_judge_exact_harvest_target=labeling_final_judge_exact_harvest_target,
        live_sri_policy=str(live_sri_policy),
        development_branch_rank_index=int(
            development_branch_rank_index
        ),
        development_branch_rank_by_path=(
            development_branch_rank_by_path
        ),
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
            "worker_pricer_kind": str(worker_pricer_kind),
            "tail_dual_stabilization_enabled": bool(tail_dual_stabilization_enabled),
            "tail_dual_stabilization_alpha": float(tail_dual_stabilization_alpha),
            "tail_dual_stabilization_window": int(tail_dual_stabilization_window),
            "labeling_final_judge_enabled": labeling_final_judge_enabled,
            "labeling_final_judge_max_exact_tasks": labeling_final_judge_max_exact_tasks,
            "labeling_final_judge_exact_harvest_target": labeling_final_judge_exact_harvest_target,
            "live_sri_policy": str(live_sri_policy),
            "live_sri_enabled": str(live_sri_policy).lower() != "no_cut",
            "development_branch_rank_index": int(
                development_branch_rank_index
            ),
            "development_branch_rank_guidance_active": bool(
                int(development_branch_rank_index) != 0
                or development_branch_rank_by_path
            ),
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
    dual_search_rows = [
        row
        for row in materialized
        if _has_value(row.get("candidate_search_false_positive_rate"))
        or _has_value(row.get("true_negative_candidate_search_miss_rate"))
        or _has_value(row.get("candidate_search_false_positive_row_count"))
        or _has_value(row.get("true_negative_candidate_search_miss_row_count"))
    ]
    partition_rows = [
        row for row in materialized if str(row.get("mode") or "") == "B4.1_partition_candidate_audit"
    ]
    partition_issue_counts = _aggregate_partition_candidate_issue_counts(partition_rows)
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
            1 for row in tail_dual_rows if _tail_dual_certificate_leak(row)
        ),
        "partition_candidate_certificate_leak_count": sum(
            int(row.get("partition_candidate_redline_fail_count") or 0) for row in partition_rows
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
        "dual_search_diagnostic_row_count": len(dual_search_rows),
        "candidate_search_false_positive_row_count": sum(
            int(row.get("candidate_search_false_positive_row_count") or 0) for row in dual_search_rows
        ),
        "true_negative_candidate_search_miss_row_count": sum(
            int(row.get("true_negative_candidate_search_miss_row_count") or 0) for row in dual_search_rows
        ),
        "mean_candidate_search_false_positive_rate": _mean_present_float(
            row.get("candidate_search_false_positive_rate") for row in dual_search_rows
        ),
        "mean_true_negative_candidate_search_miss_rate": _mean_present_float(
            row.get("true_negative_candidate_search_miss_rate") for row in dual_search_rows
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
        "partition_candidate_audit_row_count": len(partition_rows),
        "partition_candidate_gate_pass_count": sum(
            1 for row in partition_rows if _bool_value(row.get("partition_candidate_gate_pass"))
        ),
        "partition_candidate_gate_fail_count": sum(
            1 for row in partition_rows if not _bool_value(row.get("partition_candidate_gate_pass"))
        ),
        "partition_candidate_can_certify_no_negative_count": sum(
            1 for row in partition_rows if _bool_value(row.get("partition_candidate_can_certify_no_negative"))
        ),
        "partition_candidate_full_space_valid_count": sum(
            1 for row in partition_rows if _bool_value(row.get("partition_candidate_gate_full_space_partition_valid"))
        ),
        "partition_candidate_redline_fail_count": sum(
            int(row.get("partition_candidate_redline_fail_count") or 0) for row in partition_rows
        ),
        "partition_negative_region_count": sum(
            int(row.get("partition_negative_region_count") or 0) for row in partition_rows
        ),
        "partition_negative_payload_available_count": sum(
            int(row.get("partition_negative_payload_available_count") or 0) for row in partition_rows
        ),
        "partition_best_negative_rc": _min_present_float(
            row.get("partition_best_negative_rc") for row in partition_rows
        ),
        "partition_negative_already_active_count": sum(
            int(row.get("partition_negative_already_active_count") or 0) for row in partition_rows
        ),
        "partition_negative_replacement_task_set_count": sum(
            int(row.get("partition_negative_replacement_task_set_count") or 0) for row in partition_rows
        ),
        "partition_negative_new_task_set_count": sum(
            int(row.get("partition_negative_new_task_set_count") or 0) for row in partition_rows
        ),
        "partition_region_variable_count_max": _max_present_int(
            row.get("partition_region_variable_count_max") for row in partition_rows
        ),
        "partition_region_constraint_count_max": _max_present_int(
            row.get("partition_region_constraint_count_max") for row in partition_rows
        ),
        "partition_region_variable_count_mean_max": _max_present_float(
            row.get("partition_region_variable_count_mean") for row in partition_rows
        ),
        "partition_region_constraint_count_mean_max": _max_present_float(
            row.get("partition_region_constraint_count_mean") for row in partition_rows
        ),
        "partition_region_slot_task_time_feasible_assignment_count_max": _max_present_int(
            row.get("partition_region_slot_task_time_feasible_assignment_count_max")
            for row in partition_rows
        ),
        "partition_region_slot_task_time_pruned_assignment_count_sum": sum(
            int(row.get("partition_region_slot_task_time_pruned_assignment_count_sum") or 0)
            for row in partition_rows
        ),
        "partition_region_slot_arc_time_pruned_option_count_sum": sum(
            int(row.get("partition_region_slot_arc_time_pruned_option_count_sum") or 0)
            for row in partition_rows
        ),
        "partition_region_single_task_per_active_sortie_arc_pruned_option_count_sum": sum(
            int(row.get("partition_region_single_task_per_active_sortie_arc_pruned_option_count_sum") or 0)
            for row in partition_rows
        ),
        "partition_region_resource_arc_pruned_option_count_sum": sum(
            int(row.get("partition_region_resource_arc_pruned_option_count_sum") or 0)
            for row in partition_rows
        ),
        "partition_region_resource_arc_energy_pruned_option_count_sum": sum(
            int(row.get("partition_region_resource_arc_energy_pruned_option_count_sum") or 0)
            for row in partition_rows
        ),
        "partition_region_resource_arc_shadow_pruned_option_count_sum": sum(
            int(row.get("partition_region_resource_arc_shadow_pruned_option_count_sum") or 0)
            for row in partition_rows
        ),
        "partition_region_resource_arc_demand_pruned_option_count_sum": sum(
            int(row.get("partition_region_resource_arc_demand_pruned_option_count_sum") or 0)
            for row in partition_rows
        ),
        "partition_dual_scope_mismatch_count": sum(
            int(row.get("partition_dual_scope_mismatch_count") or 0) for row in partition_rows
        ),
        "partition_negative_rc_audit_fail_count": sum(
            int(row.get("partition_negative_rc_audit_fail_count") or 0) for row in partition_rows
        ),
        "partition_region_mip_start_enabled_count": sum(
            int(row.get("partition_region_mip_start_enabled_count") or 0) for row in partition_rows
        ),
        "partition_region_mip_start_ok_count": sum(
            int(row.get("partition_region_mip_start_ok_count") or 0) for row in partition_rows
        ),
        "partition_exact_region_mip_start_ok_count": sum(
            int(row.get("partition_exact_region_mip_start_ok_count") or 0) for row in partition_rows
        ),
        "partition_residual_region_mip_start_ok_count": sum(
            int(row.get("partition_residual_region_mip_start_ok_count") or 0) for row in partition_rows
        ),
        "residual_task_count_partition_enabled_count": sum(
            1 for row in partition_rows if _bool_value(row.get("residual_task_count_partition_enabled"))
        ),
        "residual_task_count_region_expected_count": _max_present_int(
            row.get("residual_task_count_region_expected_count") for row in partition_rows
        ),
        "residual_task_count_region_observed_count": _max_present_int(
            row.get("residual_task_count_region_observed_count") for row in partition_rows
        ),
        "residual_task_count_region_proven_count": _max_present_int(
            row.get("residual_task_count_region_proven_count") for row in partition_rows
        ),
        "residual_task_count_region_incomplete_count": _max_present_int(
            row.get("residual_task_count_region_incomplete_count") for row in partition_rows
        ),
        "residual_task_count_region_negative_count": _max_present_int(
            row.get("residual_task_count_region_negative_count") for row in partition_rows
        ),
        "residual_task_count_region_missing_count": _max_present_int(
            row.get("residual_task_count_region_missing_count") for row in partition_rows
        ),
        "partition_active_pool_after_dual_delta_max": _max_present_int(
            row.get("partition_active_pool_after_dual_delta") for row in partition_rows
        ),
        "partition_refreshed_dual_row_count": sum(
            1
            for row in partition_rows
            if str(row.get("partition_dual_source") or "").startswith("refreshed_active_pool")
        ),
        "partition_dual_refresh_negative_count": sum(
            int(row.get("partition_dual_refresh_negative_count") or 0) for row in partition_rows
        ),
        "partition_dual_refresh_min_rc": _min_present_float(
            row.get("partition_dual_refresh_min_rc") for row in partition_rows
        ),
        "partition_candidate_issue_counts": partition_issue_counts,
        "partition_candidate_top_issue": _top_partition_candidate_issue(partition_issue_counts),
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
        dual_context = payload.get("dual_context")
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
                resource_arc_pruning=bool(config.get("resource_arc_pruning", False)),
                slot_task_time_pruning=bool(config.get("slot_task_time_pruning", False)),
                slot_arc_support_pruning=bool(config.get("slot_arc_support_pruning", False)),
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
                task_slot_pair_conflict_capacity_bound=bool(
                    config.get("task_slot_pair_conflict_capacity_bound", False)
                ),
                dual_task_slot_lower_bound=bool(config.get("dual_task_slot_lower_bound", False)),
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


def run_b4_1_required_task_set_partition_probe(
    source_probe_json: str | Path,
    *,
    variants: Iterable[str] = ("V4_current_strengthening",),
    history_round: int = -1,
    time_limit_sec: float = 120.0,
    threads: int = 1,
    negative_eps: float = 1.0e-6,
    max_task_sets: int = 0,
    refresh_dual_from_active_pool: bool = False,
    refresh_rmp_max_iterations: int = 100,
    residual_task_count_partition: bool = False,
    residual_task_count_min: int = 1,
    residual_task_count_max: int = 0,
    residual_task_count_max_regions: int = 0,
    residual_active_sortie_count_partition: bool = False,
    residual_active_sortie_count_min: int = 0,
    residual_active_sortie_count_max: int = 0,
    residual_active_sortie_adaptive_refinement: bool = False,
    negative_feasibility_fallback: bool = False,
) -> dict:
    """Probe an exact-task-set plus residual partition of harvested negatives.

    For harvested task sets H1..Hk this solves exact-task-set regions H_i and
    the final residual region that forbids all H_i.  These rows are a candidate
    partition proof under the same true dual, but remain diagnostic until a
    final judge/ledger path consumes the complete partition without redlines.
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
        dual_context = payload.get("dual_context")
    if not isinstance(dual_context, dict):
        raise ValueError("selected history row has no dual_context")
    history_duals = JourneyDuals(
        cover={str(key): float(value) for key, value in (dual_context.get("task_duals") or {}).items()},
        fleet_limit=float(dual_context.get("fleet_dual") or 0.0),
        cuts={str(key): float(value) for key, value in (dual_context.get("cut_duals") or {}).items()},
    )
    active_payloads = [
        row for row in (payload.get("active_columns") or []) if isinstance(row, dict)
    ]
    active_task_sets = {
        task_set for task_set in (_solution_payload_task_set(row) for row in active_payloads) if task_set
    }
    active_column_keys = {
        key for key in (_solution_payload_column_key(row) for row in active_payloads) if key
    }
    active_mip_start_columns = _partition_mip_start_columns_from_payloads(data, active_payloads)
    source_active_column_count = len(active_payloads)
    history_dual_active_column_count = _first_int(
        history_row.get("active_column_count"),
        history_row.get("active_columns_after_merge"),
    )
    duals = history_duals
    dual_source = "selected_history_dual"
    dual_refresh_payload = {
        "partition_dual_refresh_status": "",
        "partition_dual_refresh_min_rc": "",
        "partition_dual_refresh_negative_count": "",
        "partition_dual_refresh_input_column_count": "",
        "partition_dual_refresh_rmp_active_column_count": "",
    }
    dual_active_column_count = history_dual_active_column_count
    if refresh_dual_from_active_pool:
        refresh = _refresh_partition_duals_from_active_pool(
            data,
            active_payloads,
            negative_eps=float(negative_eps),
            max_iterations=int(refresh_rmp_max_iterations),
        )
        duals = refresh["duals"]
        dual_source = refresh["partition_dual_source"]
        dual_refresh_payload = refresh["payload"]
        dual_active_column_count = _first_int(
            dual_refresh_payload.get("partition_dual_refresh_input_column_count"),
            dual_refresh_payload.get("partition_dual_refresh_rmp_active_column_count"),
            history_dual_active_column_count,
        )
    task_sets = _unique_harvested_task_sets(diagnostic)
    if int(max_task_sets) > 0:
        task_sets = task_sets[: int(max_task_sets)]
    rows: list[dict] = []
    adaptive_refinement_attempt_count = 0
    adaptive_refinement_coarse_accepted_count = 0
    adaptive_refinement_refined_count = 0
    adaptive_refinement_discarded_coarse_wall_time_sec = 0.0
    for index, task_set in enumerate(task_sets, start=1):
        for variant in tuple(str(item) for item in variants):
            config = B41_TARGETED_RESTRICTED_REGION_VARIANT_CONFIGS.get(variant)
            if config is None:
                raise ValueError(f"unknown B4.1 partition variant: {variant}")
            mip_start_journey = _select_partition_region_mip_start(
                active_mip_start_columns,
                duals=duals,
                required_task_set=task_set,
            )
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
                resource_arc_pruning=bool(config.get("resource_arc_pruning", False)),
                slot_task_time_pruning=bool(config.get("slot_task_time_pruning", False)),
                slot_arc_support_pruning=bool(config.get("slot_arc_support_pruning", False)),
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
                task_slot_pair_conflict_capacity_bound=bool(
                    config.get("task_slot_pair_conflict_capacity_bound", False)
                ),
                dual_task_slot_lower_bound=bool(config.get("dual_task_slot_lower_bound", False)),
                negative_feasibility_search=False,
                required_task_set=task_set,
                mip_start_journey=mip_start_journey,
            )
            rows.append(
                _partition_probe_row(
                    result,
                    source_probe_json=source,
                    instance_id=str(payload.get("instance_id") or data.instance_id),
                    history_round=history_row.get("round"),
                    region_id=f"exact_{index:03d}",
                    region_kind="exact_task_set",
                    task_set=task_set,
                    forbidden_task_sets=tuple(),
                    variant=variant,
                    formulation_kind=str(config["formulation_kind"]),
                    wall_time=perf_counter() - start,
                    negative_eps=float(negative_eps),
                    active_task_sets=active_task_sets,
                    active_column_keys=active_column_keys,
                    source_active_column_count=source_active_column_count,
                    dual_active_column_count=dual_active_column_count,
                    dual_source=dual_source,
                    dual_refresh_payload=dual_refresh_payload,
                    data=data,
                    duals=duals,
                )
            )
    def _solve_residual_task_count_region(
        config: dict,
        *,
        required_count: int,
        active_sortie_count: int | None,
        mip_start_journey,
        negative_feasibility_search: bool,
    ) -> dict:
        return solve_highs_compact_single_journey_pricing(
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
            resource_arc_pruning=bool(config.get("resource_arc_pruning", False)),
            slot_task_time_pruning=bool(config.get("slot_task_time_pruning", False)),
            slot_arc_support_pruning=bool(config.get("slot_arc_support_pruning", False)),
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
            task_slot_pair_conflict_capacity_bound=bool(
                config.get("task_slot_pair_conflict_capacity_bound", False)
            ),
            dual_task_slot_lower_bound=bool(config.get("dual_task_slot_lower_bound", False)),
            negative_feasibility_search=bool(negative_feasibility_search),
            forbidden_task_sets=task_sets,
            required_task_count=int(required_count),
            required_active_sortie_count=active_sortie_count,
            mip_start_journey=mip_start_journey,
        )

    if residual_task_count_partition:
        max_count = int(residual_task_count_max) if int(residual_task_count_max or 0) > 0 else len(data.task_ids)
        min_count = max(1, int(residual_task_count_min))
        counts = list(range(min_count, min(max_count, len(data.task_ids)) + 1))
        if int(residual_task_count_max_regions) > 0:
            counts = counts[: int(residual_task_count_max_regions)]
        for required_count in counts:
            for variant in tuple(str(item) for item in variants):
                config = B41_TARGETED_RESTRICTED_REGION_VARIANT_CONFIGS.get(variant)
                if config is None:
                    raise ValueError(f"unknown B4.1 partition variant: {variant}")
                if residual_active_sortie_count_partition and residual_active_sortie_adaptive_refinement:
                    adaptive_refinement_attempt_count += 1
                    coarse_mip_start_journey = _select_partition_region_mip_start(
                        active_mip_start_columns,
                        duals=duals,
                        forbidden_task_sets=task_sets,
                        required_task_count=required_count,
                        required_active_sortie_count=None,
                    )
                    coarse_start = perf_counter()
                    coarse_result = _solve_residual_task_count_region(
                        config,
                        required_count=int(required_count),
                        active_sortie_count=None,
                        mip_start_journey=coarse_mip_start_journey,
                        negative_feasibility_search=False,
                    )
                    coarse_wall = perf_counter() - coarse_start
                    coarse_row = _partition_probe_row(
                        coarse_result,
                        source_probe_json=source,
                        instance_id=str(payload.get("instance_id") or data.instance_id),
                        history_round=history_row.get("round"),
                        region_id=f"residual_task_count_{required_count:03d}",
                        region_kind="residual_task_count",
                        task_set=tuple(),
                        forbidden_task_sets=tuple(task_sets),
                        variant=variant,
                        formulation_kind=str(config["formulation_kind"]),
                        wall_time=coarse_wall,
                        negative_eps=float(negative_eps),
                        active_task_sets=active_task_sets,
                        active_column_keys=active_column_keys,
                        source_active_column_count=source_active_column_count,
                        dual_active_column_count=dual_active_column_count,
                        dual_source=dual_source,
                        dual_refresh_payload=dual_refresh_payload,
                        data=data,
                        duals=duals,
                    )
                    coarse_row["partition_adaptive_active_sortie_refinement_enabled"] = True
                    coarse_row["partition_adaptive_active_sortie_refinement_role"] = "coarse_accepted"
                    if (
                        coarse_row.get("region_pricing_complete") is True
                        and coarse_row.get("region_can_certify_no_negative") is True
                        and coarse_row.get("negative_found") is not True
                    ):
                        adaptive_refinement_coarse_accepted_count += 1
                        rows.append(coarse_row)
                        continue
                    adaptive_refinement_refined_count += 1
                    adaptive_refinement_discarded_coarse_wall_time_sec += float(coarse_wall)
                active_sortie_counts: tuple[int | None, ...]
                if residual_active_sortie_count_partition:
                    active_min = max(1, int(residual_active_sortie_count_min or 0) or 1)
                    active_max = (
                        min(int(required_count), int(residual_active_sortie_count_max))
                        if int(residual_active_sortie_count_max or 0) > 0
                        else int(required_count)
                    )
                    active_sortie_counts = (
                        tuple(range(active_min, active_max + 1))
                        if active_min <= active_max
                        else tuple()
                    )
                else:
                    active_sortie_counts = (None,)
                for active_sortie_count in active_sortie_counts:
                    mip_start_journey = _select_partition_region_mip_start(
                        active_mip_start_columns,
                        duals=duals,
                        forbidden_task_sets=task_sets,
                        required_task_count=required_count,
                        required_active_sortie_count=active_sortie_count,
                    )
                    start = perf_counter()
                    result = _solve_residual_task_count_region(
                        config,
                        required_count=int(required_count),
                        active_sortie_count=active_sortie_count,
                        mip_start_journey=mip_start_journey,
                        negative_feasibility_search=False,
                    )
                    fallback_result = None
                    if bool(negative_feasibility_fallback) and _partition_region_needs_negative_feasibility_fallback(
                        result,
                        region_kind="residual_task_count",
                        negative_eps=float(negative_eps),
                    ):
                        fallback_result = _solve_residual_task_count_region(
                            config,
                            required_count=int(required_count),
                            active_sortie_count=active_sortie_count,
                            mip_start_journey=mip_start_journey,
                            negative_feasibility_search=True,
                        )
                    result = _partition_region_merge_negative_feasibility_fallback(
                        result,
                        fallback_result,
                        negative_eps=float(negative_eps),
                    )
                    result["partition_negative_feasibility_fallback_enabled"] = bool(
                        negative_feasibility_fallback
                    )
                    result["wall_time_sec"] = round(perf_counter() - start, 6)
                    active_suffix = (
                        ""
                        if active_sortie_count is None
                        else f"_active_sorties_{int(active_sortie_count):03d}"
                    )
                    split_row = _partition_probe_row(
                        result,
                        source_probe_json=source,
                        instance_id=str(payload.get("instance_id") or data.instance_id),
                        history_round=history_row.get("round"),
                        region_id=f"residual_task_count_{required_count:03d}{active_suffix}",
                        region_kind="residual_task_count",
                        task_set=tuple(),
                        forbidden_task_sets=tuple(task_sets),
                        variant=variant,
                        formulation_kind=str(config["formulation_kind"]),
                        wall_time=perf_counter() - start,
                        negative_eps=float(negative_eps),
                        active_task_sets=active_task_sets,
                        active_column_keys=active_column_keys,
                        source_active_column_count=source_active_column_count,
                        dual_active_column_count=dual_active_column_count,
                        dual_source=dual_source,
                        dual_refresh_payload=dual_refresh_payload,
                        data=data,
                        duals=duals,
                    )
                    if residual_active_sortie_count_partition and residual_active_sortie_adaptive_refinement:
                        split_row["partition_adaptive_active_sortie_refinement_enabled"] = True
                        split_row["partition_adaptive_active_sortie_refinement_role"] = "refined_active_sortie"
                    rows.append(split_row)
    elif task_sets:
        for variant in tuple(str(item) for item in variants):
            config = B41_TARGETED_RESTRICTED_REGION_VARIANT_CONFIGS.get(variant)
            if config is None:
                raise ValueError(f"unknown B4.1 partition variant: {variant}")
            mip_start_journey = _select_partition_region_mip_start(
                active_mip_start_columns,
                duals=duals,
                forbidden_task_sets=task_sets,
            )
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
                resource_arc_pruning=bool(config.get("resource_arc_pruning", False)),
                slot_task_time_pruning=bool(config.get("slot_task_time_pruning", False)),
                slot_arc_support_pruning=bool(config.get("slot_arc_support_pruning", False)),
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
                task_slot_pair_conflict_capacity_bound=bool(
                    config.get("task_slot_pair_conflict_capacity_bound", False)
                ),
                dual_task_slot_lower_bound=bool(config.get("dual_task_slot_lower_bound", False)),
                negative_feasibility_search=False,
                forbidden_task_sets=task_sets,
                mip_start_journey=mip_start_journey,
            )
            rows.append(
                _partition_probe_row(
                    result,
                    source_probe_json=source,
                    instance_id=str(payload.get("instance_id") or data.instance_id),
                    history_round=history_row.get("round"),
                    region_id="residual_after_exact_task_sets",
                    region_kind="residual_after_exact_task_sets",
                    task_set=tuple(),
                    forbidden_task_sets=tuple(task_sets),
                    variant=variant,
                    formulation_kind=str(config["formulation_kind"]),
                    wall_time=perf_counter() - start,
                    negative_eps=float(negative_eps),
                    active_task_sets=active_task_sets,
                    active_column_keys=active_column_keys,
                    source_active_column_count=source_active_column_count,
                    dual_active_column_count=dual_active_column_count,
                    dual_source=dual_source,
                    dual_refresh_payload=dual_refresh_payload,
                    data=data,
                    duals=duals,
                )
                )
    summary = _partition_probe_summary(
        rows,
        task_sets=task_sets,
        negative_eps=float(negative_eps),
        total_task_count=len(data.task_ids),
    )
    summary.update(
        {
            "partition_adaptive_active_sortie_refinement_enabled": bool(
                residual_active_sortie_adaptive_refinement
                and residual_task_count_partition
                and residual_active_sortie_count_partition
            ),
            "partition_adaptive_active_sortie_refinement_attempt_count": int(
                adaptive_refinement_attempt_count
            ),
            "partition_adaptive_active_sortie_refinement_coarse_accepted_count": int(
                adaptive_refinement_coarse_accepted_count
            ),
            "partition_adaptive_active_sortie_refinement_refined_count": int(
                adaptive_refinement_refined_count
            ),
            "partition_adaptive_active_sortie_refinement_discarded_coarse_wall_time_sec": round(
                float(adaptive_refinement_discarded_coarse_wall_time_sec),
                6,
            ),
            "partition_adaptive_active_sortie_refinement_reported_row_wall_time_sec": round(
                sum(float(row.get("wall_time_sec") or 0.0) for row in rows),
                6,
            ),
            "partition_adaptive_active_sortie_refinement_total_wall_time_sec": round(
                sum(float(row.get("wall_time_sec") or 0.0) for row in rows)
                + float(adaptive_refinement_discarded_coarse_wall_time_sec),
                6,
            ),
        }
    )
    return {
        "schema_version": "lunar_ice_bpc.b4_1_required_task_set_partition_probe.v1",
        "source_probe_json": str(source),
        "instance_id": payload.get("instance_id") or data.instance_id,
        "diagnostic_only": True,
        "official_certificate_allowed": False,
        "can_claim_certificate": False,
        "target_task_sets": [list(row) for row in task_sets],
        "target_task_set_count": len(task_sets),
        "rows": rows,
        "row_count": len(rows),
        "taskset_diagnostic": diagnostic,
        "summary": summary,
        "redlines": {
            "certificate_claim_count": sum(1 for row in rows if row.get("can_claim_certificate") is True),
            "official_certificate_claim_count": sum(
                1 for row in rows if row.get("official_certificate_allowed") is True
            ),
            "full_space_certificate_claim_count": int(summary.get("can_claim_certificate") is True),
        },
    }


def write_b4_1_required_task_set_partition_probe(
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
    report_path.write_text(render_b4_1_required_task_set_partition_markdown(report), encoding="utf-8")


def build_b4_1_partition_candidate_audit(
    partition_probe_jsons: Iterable[str | Path],
) -> dict:
    """Aggregate required-task-set partition probes into a candidate audit.

    This audit is intentionally separate from the Stage A/B/C/D row matrix.  A
    passing partition gate means the diagnostic regions are internally coherent
    enough for a future final-judge ledger integration; it still does not claim
    an official full-space no-negative certificate.
    """

    rows: list[dict] = []
    for path_like in partition_probe_jsons:
        path = Path(path_like)
        payload = json.loads(path.read_text(encoding="utf-8"))
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        redlines = payload.get("redlines") if isinstance(payload.get("redlines"), dict) else {}
        payload_rows = [item for item in (payload.get("rows") or []) if isinstance(item, dict)]
        negative_rows = [item for item in payload_rows if item.get("negative_found") is True]
        negative_rc_values = [
            rc
            for rc in (
                _first_float(item.get("partition_negative_true_rc"), item.get("best_reduced_cost"))
                for item in negative_rows
            )
            if rc is not None
        ]
        already_active_count = sum(
            1 for item in negative_rows if item.get("partition_negative_already_active") is True
        )
        replacement_task_set_count = sum(
            1
            for item in negative_rows
            if str(item.get("partition_negative_replacement_or_new_task_set") or "") == "replacement"
        )
        new_task_set_count = sum(
            1
            for item in negative_rows
            if str(item.get("partition_negative_replacement_or_new_task_set") or "") == "new_task_set"
        )
        scope_mismatch_count = sum(
            1 for item in payload_rows if item.get("partition_dual_scope_matches_active_pool") is False
        )
        rc_audit_fail_count = sum(
            1 for item in negative_rows if item.get("partition_negative_rc_audit_pass") is False
        )
        mip_start_enabled_count = sum(
            1 for item in payload_rows if item.get("single_journey_mip_start_enabled") is True
        )
        mip_start_ok_count = sum(
            1 for item in payload_rows if str(item.get("single_journey_mip_start_status") or "") == "OK"
        )
        exact_mip_start_ok_count = sum(
            1
            for item in payload_rows
            if str(item.get("region_kind") or "") == "exact_task_set"
            and str(item.get("single_journey_mip_start_status") or "") == "OK"
        )
        residual_mip_start_ok_count = sum(
            1
            for item in payload_rows
            if str(item.get("region_kind") or "")
            in {"residual_after_exact_task_sets", "residual_task_count"}
            and str(item.get("single_journey_mip_start_status") or "") == "OK"
        )
        model_size_metrics = _partition_probe_model_size_metrics(payload_rows)
        issue_codes = [
            str(code)
            for code in (summary.get("partition_candidate_gate_issue_codes") or [])
            if str(code)
        ]
        row_certificate_claim_count = sum(
            1
            for item in payload_rows
            if (
                item.get("official_certificate_allowed") is True
                or item.get("can_claim_certificate") is True
                or item.get("can_certify_no_negative") is True
                or item.get("region_can_certify_full_space") is True
            )
        )
        rows.append(
            {
                "partition_probe_json": str(path),
                "schema_version": payload.get("schema_version") or "",
                "instance_id": payload.get("instance_id") or "",
                "source_probe_json": payload.get("source_probe_json") or "",
                "target_task_set_count": _first_int(payload.get("target_task_set_count")),
                "row_count": _first_int(payload.get("row_count")),
                "partition_candidate_gate_schema_version": summary.get(
                    "partition_candidate_gate_schema_version"
                )
                or "",
                "partition_candidate_gate_pass": bool(summary.get("partition_candidate_gate_pass")),
                "partition_candidate_gate_issue_codes": issue_codes,
                "partition_candidate_gate_issue_count": len(issue_codes),
                "partition_candidate_gate_full_space_partition_valid": bool(
                    summary.get("partition_candidate_gate_full_space_partition_valid")
                ),
                "partition_candidate_gate_exact_region_count": _first_int(
                    summary.get("partition_candidate_gate_exact_region_count")
                ),
                "partition_candidate_gate_exact_regions_proven": _first_int(
                    summary.get("partition_candidate_gate_exact_regions_proven")
                ),
                "partition_candidate_gate_residual_proven": bool(
                    summary.get("partition_candidate_gate_residual_proven")
                ),
                "residual_task_count_partition_enabled": bool(
                    summary.get("residual_task_count_partition_enabled")
                ),
                "residual_task_count_region_expected_count": _first_int(
                    summary.get("residual_task_count_region_expected_count")
                ),
                "residual_task_count_region_observed_count": _first_int(
                    summary.get("residual_task_count_region_observed_count")
                ),
                "residual_task_count_region_proven_count": _first_int(
                    summary.get("residual_task_count_region_proven_count")
                ),
                "residual_task_count_region_incomplete_count": _first_int(
                    summary.get("residual_task_count_region_incomplete_count")
                ),
                "residual_task_count_region_negative_count": _first_int(
                    summary.get("residual_task_count_region_negative_count")
                ),
                "residual_task_count_region_missing_count": _first_int(
                    summary.get("residual_task_count_region_missing_count")
                ),
                "residual_task_count_region_missing_counts": summary.get(
                    "residual_task_count_region_missing_counts"
                )
                or [],
                "residual_active_sortie_count_partition_enabled": bool(
                    summary.get("residual_active_sortie_count_partition_enabled")
                ),
                "residual_active_sortie_count_missing_group_count": _first_int(
                    summary.get("residual_active_sortie_count_missing_group_count")
                ),
                "residual_active_sortie_count_duplicate_group_count": _first_int(
                    summary.get("residual_active_sortie_count_duplicate_group_count")
                ),
                "partition_candidate_gate_variant": summary.get("partition_candidate_gate_variant") or "",
                "partition_candidate_gate_source_probe_json": summary.get(
                    "partition_candidate_gate_source_probe_json"
                )
                or "",
                "partition_candidate_gate_history_round": summary.get(
                    "partition_candidate_gate_history_round"
                )
                or "",
                "partition_candidate_gate_official_certificate_allowed": bool(
                    summary.get("partition_candidate_gate_official_certificate_allowed")
                ),
                "partition_candidate_can_certify_no_negative": bool(
                    summary.get("partition_candidate_can_certify_no_negative")
                ),
                "best_partition_region_lb": _first_float(summary.get("best_partition_region_lb")),
                "partition_bound_gap_to_zero": _first_float(summary.get("partition_bound_gap_to_zero")),
                "partition_negative_region_count": len(negative_rows),
                "partition_negative_exact_region_count": sum(
                    1 for item in negative_rows if str(item.get("region_kind") or "") == "exact_task_set"
                ),
                "partition_negative_residual_region_count": sum(
                    1
                    for item in negative_rows
                    if str(item.get("region_kind") or "")
                    in {"residual_after_exact_task_sets", "residual_task_count"}
                ),
                "partition_negative_payload_available_count": sum(
                    1 for item in negative_rows if item.get("partition_negative_payload_available") is True
                ),
                "partition_best_negative_rc": None if not negative_rc_values else min(negative_rc_values),
                "partition_negative_already_active_count": already_active_count,
                "partition_negative_replacement_task_set_count": replacement_task_set_count,
                "partition_negative_new_task_set_count": new_task_set_count,
                "partition_region_variable_count_max": _first_int(
                    summary.get("partition_region_variable_count_max"),
                    model_size_metrics.get("partition_region_variable_count_max"),
                ),
                "partition_region_constraint_count_max": _first_int(
                    summary.get("partition_region_constraint_count_max"),
                    model_size_metrics.get("partition_region_constraint_count_max"),
                ),
                "partition_region_variable_count_mean": _first_float(
                    summary.get("partition_region_variable_count_mean"),
                    model_size_metrics.get("partition_region_variable_count_mean"),
                ),
                "partition_region_constraint_count_mean": _first_float(
                    summary.get("partition_region_constraint_count_mean"),
                    model_size_metrics.get("partition_region_constraint_count_mean"),
                ),
                "partition_region_slot_task_time_feasible_assignment_count_max": _first_int(
                    summary.get("partition_region_slot_task_time_feasible_assignment_count_max"),
                    model_size_metrics.get("partition_region_slot_task_time_feasible_assignment_count_max"),
                ),
                "partition_region_slot_task_time_pruned_assignment_count_sum": _first_int(
                    summary.get("partition_region_slot_task_time_pruned_assignment_count_sum"),
                    model_size_metrics.get("partition_region_slot_task_time_pruned_assignment_count_sum"),
                ),
                "partition_region_slot_arc_time_pruned_option_count_sum": _first_int(
                    summary.get("partition_region_slot_arc_time_pruned_option_count_sum"),
                    model_size_metrics.get("partition_region_slot_arc_time_pruned_option_count_sum"),
                ),
                "partition_region_single_task_per_active_sortie_arc_pruned_option_count_sum": _first_int(
                    summary.get(
                        "partition_region_single_task_per_active_sortie_arc_pruned_option_count_sum"
                    ),
                    model_size_metrics.get(
                        "partition_region_single_task_per_active_sortie_arc_pruned_option_count_sum"
                    ),
                ),
                "partition_region_resource_arc_pruned_option_count_sum": _first_int(
                    summary.get("partition_region_resource_arc_pruned_option_count_sum"),
                    model_size_metrics.get("partition_region_resource_arc_pruned_option_count_sum"),
                ),
                "partition_region_resource_arc_energy_pruned_option_count_sum": _first_int(
                    summary.get("partition_region_resource_arc_energy_pruned_option_count_sum"),
                    model_size_metrics.get("partition_region_resource_arc_energy_pruned_option_count_sum"),
                ),
                "partition_region_resource_arc_shadow_pruned_option_count_sum": _first_int(
                    summary.get("partition_region_resource_arc_shadow_pruned_option_count_sum"),
                    model_size_metrics.get("partition_region_resource_arc_shadow_pruned_option_count_sum"),
                ),
                "partition_region_resource_arc_demand_pruned_option_count_sum": _first_int(
                    summary.get("partition_region_resource_arc_demand_pruned_option_count_sum"),
                    model_size_metrics.get("partition_region_resource_arc_demand_pruned_option_count_sum"),
                ),
                "partition_source_active_column_count": _max_present_int(
                    item.get("partition_source_active_column_count") for item in payload_rows
                ),
                "partition_dual_active_column_count": _max_present_int(
                    item.get("partition_dual_active_column_count") for item in payload_rows
                ),
                "partition_dual_source": _first_present_str(
                    item.get("partition_dual_source") for item in payload_rows
                ),
                "partition_dual_refresh_status": _first_present_str(
                    item.get("partition_dual_refresh_status") for item in payload_rows
                ),
                "partition_dual_refresh_min_rc": _min_present_float(
                    item.get("partition_dual_refresh_min_rc") for item in payload_rows
                ),
                "partition_dual_refresh_negative_count": _max_present_int(
                    item.get("partition_dual_refresh_negative_count") for item in payload_rows
                ),
                "partition_dual_refresh_input_column_count": _max_present_int(
                    item.get("partition_dual_refresh_input_column_count") for item in payload_rows
                ),
                "partition_dual_refresh_rmp_active_column_count": _max_present_int(
                    item.get("partition_dual_refresh_rmp_active_column_count") for item in payload_rows
                ),
                "partition_active_pool_after_dual_delta": _max_present_int(
                    item.get("partition_active_pool_after_dual_delta") for item in payload_rows
                ),
                "partition_dual_scope_mismatch_count": scope_mismatch_count,
                "partition_negative_rc_audit_fail_count": rc_audit_fail_count,
                "partition_region_mip_start_enabled_count": mip_start_enabled_count,
                "partition_region_mip_start_ok_count": mip_start_ok_count,
                "partition_exact_region_mip_start_ok_count": exact_mip_start_ok_count,
                "partition_residual_region_mip_start_ok_count": residual_mip_start_ok_count,
                "official_certificate_allowed": bool(payload.get("official_certificate_allowed")),
                "can_claim_certificate": bool(payload.get("can_claim_certificate")),
                "redline_certificate_claim_count": _first_int(redlines.get("certificate_claim_count")) or 0,
                "redline_official_certificate_claim_count": _first_int(
                    redlines.get("official_certificate_claim_count")
                )
                or 0,
                "redline_full_space_certificate_claim_count": _first_int(
                    redlines.get("full_space_certificate_claim_count")
                )
                or 0,
                "row_certificate_claim_count": row_certificate_claim_count,
                "diagnostic_only": bool(payload.get("diagnostic_only")),
            }
        )
    redlines = {
        "partition_report_official_certificate_claim_count": sum(
            1 for row in rows if row.get("official_certificate_allowed") is True
        ),
        "partition_report_can_claim_certificate_count": sum(
            1 for row in rows if row.get("can_claim_certificate") is True
        ),
        "partition_row_certificate_claim_count": sum(
            int(row.get("row_certificate_claim_count") or 0) for row in rows
        ),
        "partition_gate_official_certificate_allowed_count": sum(
            1 for row in rows if row.get("partition_candidate_gate_official_certificate_allowed") is True
        ),
        "partition_gate_missing_count": sum(
            1 for row in rows if not row.get("partition_candidate_gate_schema_version")
        ),
    }
    return {
        "schema_version": "lunar_ice_bpc.b4_1_partition_candidate_audit.v1",
        "diagnostic_only": True,
        "official_certificate_allowed": False,
        "can_claim_certificate": False,
        "partition_probe_count": len(rows),
        "partition_gate_pass_count": sum(1 for row in rows if row.get("partition_candidate_gate_pass") is True),
        "partition_gate_fail_count": sum(1 for row in rows if row.get("partition_candidate_gate_pass") is not True),
        "partition_gate_full_space_valid_count": sum(
            1 for row in rows if row.get("partition_candidate_gate_full_space_partition_valid") is True
        ),
        "partition_candidate_can_certify_no_negative_count": sum(
            1 for row in rows if row.get("partition_candidate_can_certify_no_negative") is True
        ),
        "partition_negative_region_count": sum(
            int(row.get("partition_negative_region_count") or 0) for row in rows
        ),
        "partition_negative_payload_available_count": sum(
            int(row.get("partition_negative_payload_available_count") or 0) for row in rows
        ),
        "partition_best_negative_rc": _min_present_float(
            row.get("partition_best_negative_rc") for row in rows
        ),
        "partition_negative_already_active_count": sum(
            int(row.get("partition_negative_already_active_count") or 0) for row in rows
        ),
        "partition_negative_replacement_task_set_count": sum(
            int(row.get("partition_negative_replacement_task_set_count") or 0) for row in rows
        ),
        "partition_negative_new_task_set_count": sum(
            int(row.get("partition_negative_new_task_set_count") or 0) for row in rows
        ),
        "partition_region_variable_count_max": _max_present_int(
            row.get("partition_region_variable_count_max") for row in rows
        ),
        "partition_region_constraint_count_max": _max_present_int(
            row.get("partition_region_constraint_count_max") for row in rows
        ),
        "partition_region_variable_count_mean_max": _max_present_float(
            row.get("partition_region_variable_count_mean") for row in rows
        ),
        "partition_region_constraint_count_mean_max": _max_present_float(
            row.get("partition_region_constraint_count_mean") for row in rows
        ),
        "partition_region_slot_task_time_feasible_assignment_count_max": _max_present_int(
            row.get("partition_region_slot_task_time_feasible_assignment_count_max") for row in rows
        ),
        "partition_region_slot_task_time_pruned_assignment_count_sum": sum(
            int(row.get("partition_region_slot_task_time_pruned_assignment_count_sum") or 0)
            for row in rows
        ),
        "partition_region_slot_arc_time_pruned_option_count_sum": sum(
            int(row.get("partition_region_slot_arc_time_pruned_option_count_sum") or 0)
            for row in rows
        ),
        "partition_region_resource_arc_pruned_option_count_sum": sum(
            int(row.get("partition_region_resource_arc_pruned_option_count_sum") or 0)
            for row in rows
        ),
        "partition_region_resource_arc_energy_pruned_option_count_sum": sum(
            int(row.get("partition_region_resource_arc_energy_pruned_option_count_sum") or 0)
            for row in rows
        ),
        "partition_region_resource_arc_shadow_pruned_option_count_sum": sum(
            int(row.get("partition_region_resource_arc_shadow_pruned_option_count_sum") or 0)
            for row in rows
        ),
        "partition_region_resource_arc_demand_pruned_option_count_sum": sum(
            int(row.get("partition_region_resource_arc_demand_pruned_option_count_sum") or 0)
            for row in rows
        ),
        "partition_dual_scope_mismatch_count": sum(
            int(row.get("partition_dual_scope_mismatch_count") or 0) for row in rows
        ),
        "partition_negative_rc_audit_fail_count": sum(
            int(row.get("partition_negative_rc_audit_fail_count") or 0) for row in rows
        ),
        "partition_region_mip_start_enabled_count": sum(
            int(row.get("partition_region_mip_start_enabled_count") or 0) for row in rows
        ),
        "partition_region_mip_start_ok_count": sum(
            int(row.get("partition_region_mip_start_ok_count") or 0) for row in rows
        ),
        "partition_exact_region_mip_start_ok_count": sum(
            int(row.get("partition_exact_region_mip_start_ok_count") or 0) for row in rows
        ),
        "partition_residual_region_mip_start_ok_count": sum(
            int(row.get("partition_residual_region_mip_start_ok_count") or 0) for row in rows
        ),
        "residual_task_count_partition_enabled_count": sum(
            1 for row in rows if row.get("residual_task_count_partition_enabled") is True
        ),
        "residual_task_count_region_expected_count": _max_present_int(
            row.get("residual_task_count_region_expected_count") for row in rows
        ),
        "residual_task_count_region_observed_count": _max_present_int(
            row.get("residual_task_count_region_observed_count") for row in rows
        ),
        "residual_task_count_region_proven_count": _max_present_int(
            row.get("residual_task_count_region_proven_count") for row in rows
        ),
        "residual_task_count_region_incomplete_count": _max_present_int(
            row.get("residual_task_count_region_incomplete_count") for row in rows
        ),
        "residual_task_count_region_negative_count": _max_present_int(
            row.get("residual_task_count_region_negative_count") for row in rows
        ),
        "residual_task_count_region_missing_count": _max_present_int(
            row.get("residual_task_count_region_missing_count") for row in rows
        ),
        "partition_gate_issue_counts": dict(
            sorted(Counter(code for row in rows for code in row.get("partition_candidate_gate_issue_codes") or []).items())
        ),
        "redlines": redlines,
        "redline_fail_count": sum(int(value or 0) for value in redlines.values()),
        "rows": rows,
    }


def write_b4_1_partition_candidate_audit(
    audit: dict,
    *,
    summary_json: str | Path,
    report_md: str | Path,
) -> None:
    summary_path = Path(summary_json)
    report_path = Path(report_md)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    report_path.write_text(render_b4_1_partition_candidate_audit_markdown(audit), encoding="utf-8")


def rows_from_b4_1_partition_candidate_audit(
    audit_json: str | Path,
    *,
    matrix_group: str = "B4.1 Partition candidate audit",
) -> list[dict]:
    path = Path(audit_json)
    audit = json.loads(path.read_text(encoding="utf-8"))
    rows: list[dict] = []
    audit_redline_fail_count = int(audit.get("redline_fail_count") or 0)
    for row in audit.get("rows") or []:
        if not isinstance(row, dict):
            continue
        issue_codes = [
            str(code)
            for code in (row.get("partition_candidate_gate_issue_codes") or [])
            if str(code)
        ]
        candidate_can_certify = bool(row.get("partition_candidate_can_certify_no_negative"))
        gate_pass = bool(row.get("partition_candidate_gate_pass"))
        row_redline_fail_count = sum(
            int(row.get(key) or 0)
            for key in (
                "redline_certificate_claim_count",
                "redline_official_certificate_claim_count",
                "redline_full_space_certificate_claim_count",
                "row_certificate_claim_count",
            )
        )
        partition_best_region_lb = _first_float(row.get("best_partition_region_lb"))
        partition_bound_gap = _first_float(row.get("partition_bound_gap_to_zero"))
        rows.append(
            {
                "stage": "B",
                "matrix_group": str(matrix_group),
                "instance_path": "",
                "source_probe_json": row.get("source_probe_json") or "",
                "scale": "30" if _path_or_id_looks_30_scale(row.get("source_probe_json"), row.get("instance_id")) else "",
                "instance_id": row.get("instance_id") or "",
                "mode": "B4.1_partition_candidate_audit",
                "variant": row.get("partition_candidate_gate_variant") or "",
                "b4_1_matrix_cell": "B4.1_partition_candidate_audit",
                "b4_1_proof_tail_component": "required_task_set_partition_region_proof_candidate",
                "b4_1_formulation_profile": row.get("partition_candidate_gate_variant") or "",
                "b4_1_harvesting_enabled": False,
                "b4_1_hidden_negative_audit_enabled": False,
                "b4_1_frontier_ledger_enabled": True,
                "b4_1_official_certificate_allowed": False,
                "phase": "partition_candidate_audit",
                "round": row.get("partition_candidate_gate_history_round") or "",
                "algorithm_status": "PARTITION_CANDIDATE_GATE_PASS" if gate_pass else "PARTITION_CANDIDATE_GATE_FAIL",
                "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                "underlying_certificate_scope": "PARTITION_CANDIDATE_NO_NEGATIVE" if candidate_can_certify else "",
                "pricing_state": "INCOMPLETE_LIMIT",
                "exact_status": "PARTITION_CANDIDATE_GATE_PASS" if gate_pass else "PARTITION_CANDIDATE_GATE_FAIL",
                "bpc_tree_optimal": False,
                "manual_rc_fail": 0,
                "pricing_rc_fail": 0,
                "certificate_leak": row_redline_fail_count,
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
                "global_remaining_rc_lb": "",
                "underlying_global_remaining_rc_lb": partition_best_region_lb,
                "frontier_lb_official": False,
                "frontier_coverage_complete": False,
                "underlying_frontier_coverage_complete": gate_pass,
                "frontier_unsupported_region_count": 1,
                "underlying_frontier_unsupported_region_count": 0 if gate_pass else 1,
                "pending_complete_min_rc": "",
                "underlying_pending_complete_min_rc": partition_best_region_lb,
                "pricing_proof_kind": "FRONTIER_BOUND_INCOMPLETE",
                "underlying_pricing_proof_kind": "PARTITION_CANDIDATE_NO_NEGATIVE" if candidate_can_certify else "",
                "can_certify_no_negative": False,
                "underlying_can_certify_no_negative": candidate_can_certify,
                "b4_1_certificate_suppressed": candidate_can_certify,
                "diagnostic_claimed_certificate": row_redline_fail_count,
                "partition_candidate_audit_json": str(path),
                "partition_probe_json": row.get("partition_probe_json") or "",
                "partition_target_task_set_count": _first_int(row.get("target_task_set_count")),
                "partition_candidate_gate_pass": gate_pass,
                "partition_candidate_gate_issue_count": _first_int(row.get("partition_candidate_gate_issue_count")),
                "partition_candidate_gate_issue_codes": issue_codes,
                "partition_candidate_gate_full_space_partition_valid": bool(
                    row.get("partition_candidate_gate_full_space_partition_valid")
                ),
                "partition_candidate_gate_exact_region_count": _first_int(
                    row.get("partition_candidate_gate_exact_region_count")
                ),
                "partition_candidate_gate_exact_regions_proven": _first_int(
                    row.get("partition_candidate_gate_exact_regions_proven")
                ),
                "partition_candidate_gate_residual_proven": bool(
                    row.get("partition_candidate_gate_residual_proven")
                ),
                "residual_task_count_partition_enabled": bool(
                    row.get("residual_task_count_partition_enabled")
                ),
                "residual_task_count_region_expected_count": _first_int(
                    row.get("residual_task_count_region_expected_count")
                ),
                "residual_task_count_region_observed_count": _first_int(
                    row.get("residual_task_count_region_observed_count")
                ),
                "residual_task_count_region_proven_count": _first_int(
                    row.get("residual_task_count_region_proven_count")
                ),
                "residual_task_count_region_incomplete_count": _first_int(
                    row.get("residual_task_count_region_incomplete_count")
                ),
                "residual_task_count_region_negative_count": _first_int(
                    row.get("residual_task_count_region_negative_count")
                ),
                "residual_task_count_region_missing_count": _first_int(
                    row.get("residual_task_count_region_missing_count")
                ),
                "residual_task_count_region_missing_counts": row.get(
                    "residual_task_count_region_missing_counts"
                )
                or [],
                "residual_active_sortie_count_partition_enabled": bool(
                    row.get("residual_active_sortie_count_partition_enabled")
                ),
                "residual_active_sortie_count_missing_group_count": _first_int(
                    row.get("residual_active_sortie_count_missing_group_count")
                ),
                "residual_active_sortie_count_duplicate_group_count": _first_int(
                    row.get("residual_active_sortie_count_duplicate_group_count")
                ),
                "partition_candidate_can_certify_no_negative": candidate_can_certify,
                "partition_candidate_redline_fail_count": row_redline_fail_count,
                "partition_candidate_row_certificate_claim_count": _first_int(
                    row.get("row_certificate_claim_count")
                )
                or 0,
                "partition_best_region_lb": partition_best_region_lb,
                "partition_bound_gap_to_zero": partition_bound_gap,
                "partition_negative_region_count": _first_int(row.get("partition_negative_region_count")),
                "partition_negative_exact_region_count": _first_int(
                    row.get("partition_negative_exact_region_count")
                ),
                "partition_negative_residual_region_count": _first_int(
                    row.get("partition_negative_residual_region_count")
                ),
                "partition_negative_payload_available_count": _first_int(
                    row.get("partition_negative_payload_available_count")
                ),
                "partition_best_negative_rc": _first_float(row.get("partition_best_negative_rc")),
                "partition_negative_already_active_count": _first_int(
                    row.get("partition_negative_already_active_count")
                ),
                "partition_negative_replacement_task_set_count": _first_int(
                    row.get("partition_negative_replacement_task_set_count")
                ),
                "partition_negative_new_task_set_count": _first_int(
                    row.get("partition_negative_new_task_set_count")
                ),
                "partition_region_variable_count_max": _first_int(
                    row.get("partition_region_variable_count_max")
                ),
                "partition_region_constraint_count_max": _first_int(
                    row.get("partition_region_constraint_count_max")
                ),
                "partition_region_variable_count_mean": _first_float(
                    row.get("partition_region_variable_count_mean")
                ),
                "partition_region_constraint_count_mean": _first_float(
                    row.get("partition_region_constraint_count_mean")
                ),
                "partition_region_slot_task_time_feasible_assignment_count_max": _first_int(
                    row.get("partition_region_slot_task_time_feasible_assignment_count_max")
                ),
                "partition_region_slot_task_time_pruned_assignment_count_sum": _first_int(
                    row.get("partition_region_slot_task_time_pruned_assignment_count_sum")
                ),
                "partition_region_slot_arc_time_pruned_option_count_sum": _first_int(
                    row.get("partition_region_slot_arc_time_pruned_option_count_sum")
                ),
                "partition_region_single_task_per_active_sortie_arc_pruned_option_count_sum": _first_int(
                    row.get("partition_region_single_task_per_active_sortie_arc_pruned_option_count_sum")
                ),
                "partition_region_resource_arc_pruned_option_count_sum": _first_int(
                    row.get("partition_region_resource_arc_pruned_option_count_sum")
                ),
                "partition_region_resource_arc_energy_pruned_option_count_sum": _first_int(
                    row.get("partition_region_resource_arc_energy_pruned_option_count_sum")
                ),
                "partition_region_resource_arc_shadow_pruned_option_count_sum": _first_int(
                    row.get("partition_region_resource_arc_shadow_pruned_option_count_sum")
                ),
                "partition_region_resource_arc_demand_pruned_option_count_sum": _first_int(
                    row.get("partition_region_resource_arc_demand_pruned_option_count_sum")
                ),
                "partition_source_active_column_count": _first_int(
                    row.get("partition_source_active_column_count")
                ),
                "partition_dual_active_column_count": _first_int(row.get("partition_dual_active_column_count")),
                "partition_dual_source": row.get("partition_dual_source") or "",
                "partition_dual_refresh_status": row.get("partition_dual_refresh_status") or "",
                "partition_dual_refresh_min_rc": _first_float(row.get("partition_dual_refresh_min_rc")),
                "partition_dual_refresh_negative_count": _first_int(
                    row.get("partition_dual_refresh_negative_count")
                ),
                "partition_dual_refresh_input_column_count": _first_int(
                    row.get("partition_dual_refresh_input_column_count")
                ),
                "partition_dual_refresh_rmp_active_column_count": _first_int(
                    row.get("partition_dual_refresh_rmp_active_column_count")
                ),
                "partition_active_pool_after_dual_delta": _first_int(
                    row.get("partition_active_pool_after_dual_delta")
                ),
                "partition_dual_scope_mismatch_count": _first_int(
                    row.get("partition_dual_scope_mismatch_count")
                ),
                "partition_negative_rc_audit_fail_count": _first_int(
                    row.get("partition_negative_rc_audit_fail_count")
                ),
                "partition_region_mip_start_enabled_count": _first_int(
                    row.get("partition_region_mip_start_enabled_count")
                ),
                "partition_region_mip_start_ok_count": _first_int(
                    row.get("partition_region_mip_start_ok_count")
                ),
                "partition_exact_region_mip_start_ok_count": _first_int(
                    row.get("partition_exact_region_mip_start_ok_count")
                ),
                "partition_residual_region_mip_start_ok_count": _first_int(
                    row.get("partition_residual_region_mip_start_ok_count")
                ),
                "wall_time": "",
                "fail_closed_reason": ", ".join(issue_codes),
                "partition_candidate_audit_redline_fail_count": audit_redline_fail_count,
            }
        )
    return rows


def build_b4_1_restricted_region_bound_ledger(
    source_probe_json: str | Path,
    *,
    targeted_probe_jsons: Iterable[str | Path] = (),
    max_regions: int = 0,
    negative_eps: float = 1.0e-6,
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
    coverage = _restricted_region_bound_coverage_summary(
        rows,
        best_known_global_lb=best_known_global_lb,
        negative_eps=negative_eps,
    )
    partition_audit = _restricted_region_partition_audit(
        diagnostic,
        rows,
        negative_eps=negative_eps,
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
        "region_coverage_model": "prefix_no_good_regions_diagnostic_not_partition",
        "region_coverage_complete": False,
        **partition_audit,
        "region_bound_gap_to_zero": coverage["region_bound_gap_to_zero"],
        "region_bound_gap_source_region_id": coverage["region_bound_gap_source_region_id"],
        "region_bound_gap_source": coverage["region_bound_gap_source"],
        "frontier_coverage_complete": False,
        "frontier_unsupported_region_count": max(1, len(rows)) if rows else 0,
        "best_known_global_remaining_rc_lb": best_known_global_lb,
        "global_remaining_rc_lb": best_known_global_lb,
        "global_remaining_rc_lb_valid": bool(best_known_global_lb is not None),
        "global_remaining_rc_lb_coverage_complete": False,
        "region_count": len(rows),
        "supported_bound_region_count": coverage["supported_bound_region_count"],
        "unsupported_bound_region_count": coverage["unsupported_bound_region_count"],
        "nonnegative_bound_region_count": coverage["nonnegative_bound_region_count"],
        "negative_bound_region_count": coverage["negative_bound_region_count"],
        "time_limit_bound_region_count": coverage["time_limit_bound_region_count"],
        "exact_bound_region_count": coverage["exact_bound_region_count"],
        "source_bound_reuse_count": source_reuse_count,
        "targeted_bound_improvement_count": targeted_improvement_count,
        "rows": rows,
        "summary": {
            "certificate_claim_count": certificate_claim_count,
            "source_bound_reuse_count": source_reuse_count,
            "targeted_bound_improvement_count": targeted_improvement_count,
            "best_known_global_remaining_rc_lb": best_known_global_lb,
            **coverage,
            **partition_audit,
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
        f"- region_bound_gap_to_zero: `{ledger.get('region_bound_gap_to_zero')}`",
        f"- region_bound_gap_source: `{ledger.get('region_bound_gap_source_region_id')}` / `{ledger.get('region_bound_gap_source')}`",
        f"- supported / unsupported bound regions: `{ledger.get('supported_bound_region_count')}` / `{ledger.get('unsupported_bound_region_count')}`",
        f"- nonnegative / negative bound regions: `{ledger.get('nonnegative_bound_region_count')}` / `{ledger.get('negative_bound_region_count')}`",
        f"- region partition family: `{ledger.get('region_partition_family')}`",
        f"- observed prefixes: `{ledger.get('region_partition_observed_prefixes')}`",
        f"- required exact-task-set regions: `{ledger.get('region_partition_required_exact_task_set_region_count')}`",
        f"- missing exact-task-set regions: `{ledger.get('region_partition_missing_exact_task_set_region_count')}`",
        f"- residual region: `{ledger.get('region_partition_residual_region_id')}` / `{ledger.get('region_partition_residual_best_known_dual_bound')}`",
        f"- partition issue codes: `{', '.join(ledger.get('region_partition_issue_codes') or []) or 'none'}`",
        f"- source_bound_reuse_count: `{ledger.get('source_bound_reuse_count')}`",
        f"- targeted_bound_improvement_count: `{ledger.get('targeted_bound_improvement_count')}`",
        "",
        "| region | forbidden sets | selected source | best known LB | gap to 0 | source LB | targeted best LB | targeted variant | cert allowed |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in ledger.get("rows") or []:
        lines.append(
            "| {region} | {forbidden} | {source} | {best} | {gap} | {src_lb} | {target_lb} | {variant} | {cert} |".format(
                region=row.get("region_id"),
                forbidden=row.get("forbidden_task_set_count"),
                source=row.get("selected_bound_source"),
                best=row.get("best_known_dual_bound"),
                gap=row.get("best_known_dual_bound_gap_to_zero"),
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


def render_b4_1_required_task_set_partition_markdown(report: dict) -> str:
    summary = report.get("summary") or {}
    lines = [
        "# B4.1 Required Task-Set Partition Probe",
        "",
        "## Boundary",
        "",
        f"- Source probe: `{report.get('source_probe_json')}`",
        "- Exact task-set regions plus the residual region form a candidate partition.",
        "- This report is diagnostic-only; it does not claim an official no-negative certificate.",
        "",
        "## Summary",
        "",
        f"- target_task_set_count: `{report.get('target_task_set_count')}`",
        f"- partition_candidate_complete: `{summary.get('partition_candidate_complete')}`",
        f"- partition_candidate_can_certify_no_negative: `{summary.get('partition_candidate_can_certify_no_negative')}`",
        f"- partition_candidate_gate_pass: `{summary.get('partition_candidate_gate_pass')}`",
        f"- partition_candidate_gate_issue_codes: `{summary.get('partition_candidate_gate_issue_codes')}`",
        f"- official_certificate_allowed: `{report.get('official_certificate_allowed')}`",
        f"- exact regions proven / incomplete / negative: `{summary.get('exact_region_proven_count')}` / `{summary.get('exact_region_incomplete_count')}` / `{summary.get('exact_region_negative_count')}`",
        f"- residual observed / proven / negative: `{summary.get('residual_region_observed')}` / `{summary.get('residual_region_proven')}` / `{summary.get('residual_region_negative_found')}`",
        f"- negative relation counts: already_active `{summary.get('partition_negative_already_active_count')}`; "
        f"replacement `{summary.get('partition_negative_replacement_task_set_count')}`; "
        f"new_task_set `{summary.get('partition_negative_new_task_set_count')}`",
        f"- dual/active scope: source active `{summary.get('partition_source_active_column_count')}`; "
        f"dual active `{summary.get('partition_dual_active_column_count')}`; "
        f"delta `{summary.get('partition_active_pool_after_dual_delta')}`; "
        f"mismatch rows `{summary.get('partition_dual_scope_mismatch_count')}`",
        f"- dual source: `{summary.get('partition_dual_source')}`; "
        f"refresh status `{summary.get('partition_dual_refresh_status')}`; "
        f"refresh min RC `{summary.get('partition_dual_refresh_min_rc')}`; "
        f"refresh negatives `{summary.get('partition_dual_refresh_negative_count')}`",
        f"- region MIP-start: enabled `{summary.get('partition_region_mip_start_enabled_count')}`; "
        f"OK `{summary.get('partition_region_mip_start_ok_count')}`; "
        f"exact OK `{summary.get('partition_exact_region_mip_start_ok_count')}`; "
        f"residual OK `{summary.get('partition_residual_region_mip_start_ok_count')}`",
        f"- negative RC audit fail count: `{summary.get('partition_negative_rc_audit_fail_count')}`",
        f"- adaptive active-sortie refinement: enabled `{summary.get('partition_adaptive_active_sortie_refinement_enabled')}`; "
        f"attempts `{summary.get('partition_adaptive_active_sortie_refinement_attempt_count')}`; "
        f"coarse accepted `{summary.get('partition_adaptive_active_sortie_refinement_coarse_accepted_count')}`; "
        f"refined `{summary.get('partition_adaptive_active_sortie_refinement_refined_count')}`; "
        f"discarded coarse wall `{summary.get('partition_adaptive_active_sortie_refinement_discarded_coarse_wall_time_sec')}`; "
        f"total wall `{summary.get('partition_adaptive_active_sortie_refinement_total_wall_time_sec')}`",
        "",
        "| region | kind | variant | status | exact | best RC | manual RC | RC diff | dual cols | source cols | complete | region cert | negative | payload | active | relation |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report.get("rows") or []:
        lines.append(
            "| {region} | {kind} | {variant} | {status} | {exact} | {rc} | {manual_rc} | {rc_diff} | {dual_cols} | {source_cols} | {complete} | {cert} | {neg} | {payload} | {active} | {relation} |".format(
                region=row.get("region_id"),
                kind=row.get("region_kind"),
                variant=row.get("variant"),
                status=row.get("status"),
                exact=row.get("exact_status"),
                rc=row.get("best_reduced_cost"),
                manual_rc=row.get("partition_negative_manual_rc"),
                rc_diff=row.get("partition_negative_pricing_rc_diff"),
                dual_cols=row.get("partition_dual_active_column_count"),
                source_cols=row.get("partition_source_active_column_count"),
                complete=row.get("region_pricing_complete"),
                cert=row.get("region_can_certify_no_negative"),
                neg=row.get("negative_found"),
                payload=row.get("partition_negative_payload_available"),
                active=row.get("partition_negative_already_active"),
                relation=row.get("partition_negative_replacement_or_new_task_set"),
            )
        )
    lines.extend(["", "## Redlines", "", "| metric | value | required |", "| --- | ---: | ---: |"])
    for key, value in (report.get("redlines") or {}).items():
        lines.append(f"| {key} | {value} | 0 |")
    return "\n".join(lines) + "\n"


def render_b4_1_partition_candidate_audit_markdown(audit: dict) -> str:
    lines = [
        "# B4.1 Partition Candidate Audit",
        "",
        "## Boundary",
        "",
        "- This audit summarizes required-task-set partition probe artifacts.",
        "- A passing partition gate is still diagnostic-only until final judge ledger integration.",
        "- No official no-negative certificate or `BPC_TREE_OPTIMAL` claim is made here.",
        "",
        "## Summary",
        "",
        f"- partition_probe_count: `{audit.get('partition_probe_count')}`",
        f"- partition_gate_pass_count: `{audit.get('partition_gate_pass_count')}`",
        f"- partition_gate_fail_count: `{audit.get('partition_gate_fail_count')}`",
        f"- partition_candidate_can_certify_no_negative_count: `{audit.get('partition_candidate_can_certify_no_negative_count')}`",
        f"- partition_negative_region_count: `{audit.get('partition_negative_region_count')}`",
        f"- partition_negative_payload_available_count: `{audit.get('partition_negative_payload_available_count')}`",
        f"- partition_best_negative_rc: `{audit.get('partition_best_negative_rc')}`",
        f"- partition negative relation counts: already_active `{audit.get('partition_negative_already_active_count')}`; "
        f"replacement `{audit.get('partition_negative_replacement_task_set_count')}`; "
        f"new_task_set `{audit.get('partition_negative_new_task_set_count')}`",
        f"- partition dual/active scope mismatch count: `{audit.get('partition_dual_scope_mismatch_count')}`",
        f"- partition negative RC audit fail count: `{audit.get('partition_negative_rc_audit_fail_count')}`",
        f"- redline_fail_count: `{audit.get('redline_fail_count')}`",
        f"- gate issue counts: `{audit.get('partition_gate_issue_counts')}`",
        "",
        "| probe | instance | target sets | gate | issue count | issues | variant | dual source | refresh status | negatives | already active | new task-set | dual/source cols | scope mismatches | RC audit fail | best neg RC | full-space valid | candidate no-neg | official allowed |",
        "| --- | --- | ---: | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for row in audit.get("rows") or []:
        lines.append(
            "| {probe} | {instance} | {targets} | {gate} | {issue_count} | {issues} | {variant} | {dual_source} | {refresh_status} | {negatives} | {already} | {new_task_set} | {dual_cols}/{source_cols} | {scope_mismatch} | {rc_fail} | {best_neg} | {full_valid} | {candidate} | {official} |".format(
                probe=row.get("partition_probe_json"),
                instance=row.get("instance_id"),
                targets=row.get("target_task_set_count"),
                gate=row.get("partition_candidate_gate_pass"),
                issue_count=row.get("partition_candidate_gate_issue_count"),
                issues=", ".join(row.get("partition_candidate_gate_issue_codes") or []) or "none",
                variant=row.get("partition_candidate_gate_variant"),
                dual_source=row.get("partition_dual_source"),
                refresh_status=row.get("partition_dual_refresh_status"),
                negatives=row.get("partition_negative_region_count"),
                already=row.get("partition_negative_already_active_count"),
                new_task_set=row.get("partition_negative_new_task_set_count"),
                dual_cols=row.get("partition_dual_active_column_count"),
                source_cols=row.get("partition_source_active_column_count"),
                scope_mismatch=row.get("partition_dual_scope_mismatch_count"),
                rc_fail=row.get("partition_negative_rc_audit_fail_count"),
                best_neg=row.get("partition_best_negative_rc"),
                full_valid=row.get("partition_candidate_gate_full_space_partition_valid"),
                candidate=row.get("partition_candidate_can_certify_no_negative"),
                official=row.get("official_certificate_allowed"),
            )
        )
    lines.extend(["", "## Redlines", "", "| metric | value | required |", "| --- | ---: | ---: |"])
    for key, value in (audit.get("redlines") or {}).items():
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


def _unique_harvested_task_sets(diagnostic: dict) -> list[tuple[str, ...]]:
    seen: set[tuple[str, ...]] = set()
    ordered: list[tuple[str, ...]] = []
    for row in diagnostic.get("harvested_negatives") or []:
        task_set = tuple(sorted(str(task) for task in (row.get("task_set") or []) if str(task)))
        if not task_set or task_set in seen:
            continue
        seen.add(task_set)
        ordered.append(task_set)
    return ordered


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


def _partition_mip_start_columns_from_payloads(data, active_payloads: Iterable[dict]) -> tuple:
    columns = []
    for payload in active_payloads:
        if not isinstance(payload, dict):
            continue
        try:
            column = journey_column_from_solution_payload(data, payload)
        except Exception:
            continue
        if not getattr(column, "sorties", None):
            continue
        if not all(getattr(sortie, "feasible", False) for sortie in column.sorties):
            continue
        columns.append(column)
    return tuple(columns)


def _select_partition_region_mip_start(
    columns: Iterable,
    *,
    duals: JourneyDuals,
    required_task_set: Iterable[str] | None = None,
    required_task_count: int | None = None,
    required_active_sortie_count: int | None = None,
    forbidden_task_sets: Iterable[Iterable[str]] = tuple(),
):
    required = (
        None
        if required_task_set is None
        else tuple(sorted(str(task_id) for task_id in required_task_set))
    )
    forbidden = {
        tuple(sorted(str(task_id) for task_id in task_set))
        for task_set in forbidden_task_sets
    }
    candidates = []
    for column in columns:
        task_set = tuple(sorted(str(task_id) for task_id in getattr(column, "task_set", tuple())))
        if required is not None and task_set != required:
            continue
        if required_task_count is not None and len(task_set) != int(required_task_count):
            continue
        if required_active_sortie_count is not None and len(getattr(column, "sorties", tuple())) != int(
            required_active_sortie_count
        ):
            continue
        if task_set in forbidden:
            continue
        try:
            reduced_cost = manual_journey_reduced_cost(column, duals)
        except Exception:
            continue
        candidates.append((float(reduced_cost), len(task_set), column))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], -item[1]))
    return candidates[0][2]


def _partition_probe_row(
    result: dict,
    *,
    source_probe_json: Path,
    instance_id: str,
    history_round: object,
    region_id: str,
    region_kind: str,
    task_set: tuple[str, ...],
    forbidden_task_sets: tuple[tuple[str, ...], ...],
    variant: str,
    formulation_kind: str,
    wall_time: float,
    negative_eps: float,
    active_task_sets: set[tuple[str, ...]] | None = None,
    active_column_keys: set[tuple] | None = None,
    source_active_column_count: int | None = None,
    dual_active_column_count: int | None = None,
    dual_source: str = "selected_history_dual",
    dual_refresh_payload: dict | None = None,
    data=None,
    duals: JourneyDuals | None = None,
) -> dict:
    best_rc = _first_float(result.get("best_reduced_cost"), result.get("pricing_best_reduced_cost"))
    dual_bound = _first_float(result.get("dual_bound"), result.get("bound"))
    exact_status = str(result.get("exact_status") or "")
    negative_found = bool(
        result.get("negative_found")
        or (best_rc is not None and float(best_rc) < -abs(float(negative_eps)))
    )
    negative_task_set = _partition_negative_task_set(result, fallback_task_set=task_set)
    negative_solution_payload = _targeted_negative_solution_payload(result) if negative_found else None
    negative_payload_task_set = (
        _solution_payload_task_set(negative_solution_payload)
        if isinstance(negative_solution_payload, dict)
        else tuple()
    )
    if negative_payload_task_set:
        negative_task_set = negative_payload_task_set
    negative_column_key = (
        _solution_payload_column_key(negative_solution_payload)
        if isinstance(negative_solution_payload, dict)
        else tuple()
    )
    active_task_set_lookup = active_task_sets or set()
    active_column_key_lookup = active_column_keys or set()
    negative_already_active = bool(
        negative_found and negative_column_key and negative_column_key in active_column_key_lookup
    )
    negative_active_task_set_seen = bool(negative_found and negative_task_set in active_task_set_lookup)
    if not negative_found:
        negative_relation = ""
    elif negative_already_active:
        negative_relation = "already_active"
    elif negative_active_task_set_seen:
        negative_relation = "replacement"
    else:
        negative_relation = "new_task_set"
    source_active_count = int(source_active_column_count or 0)
    dual_active_count = int(dual_active_column_count or 0)
    active_pool_after_dual_delta = (
        source_active_count - dual_active_count
        if source_active_count > 0 and dual_active_count > 0
        else ""
    )
    dual_scope_matches_active_pool = (
        bool(source_active_count == dual_active_count)
        if source_active_count > 0 and dual_active_count > 0
        else ""
    )
    manual_rc_audit = _partition_negative_manual_rc_audit(
        negative_solution_payload,
        data=data,
        duals=duals,
        pricing_rc=best_rc,
        negative_eps=negative_eps,
    )
    if str(region_kind) == "exact_task_set":
        region_complete = bool(result.get("pricing_complete_for_required_task_set"))
        region_can_certify = bool(
            result.get("required_task_set_region_can_certify_no_negative")
            and not negative_found
        )
    elif str(region_kind) == "residual_task_count":
        region_complete = bool(result.get("pricing_complete_for_required_task_count"))
        region_can_certify = bool(
            result.get("required_task_count_region_can_certify_no_negative")
            and not negative_found
        )
    else:
        region_complete = exact_status in {
            "RESTRICTED_PRICING_OPTIMAL",
            "RESTRICTED_PRICING_INFEASIBLE",
        }
        region_can_certify = bool(
            region_complete
            and not negative_found
            and (best_rc is None or float(best_rc) >= -abs(float(negative_eps)))
        )
    return {
        "source_probe_json": str(source_probe_json),
        "instance_id": instance_id,
        "history_round": history_round,
        "region_id": str(region_id),
        "region_kind": str(region_kind),
        "required_task_set": list(task_set),
        "required_task_set_size": len(task_set),
        "forbidden_task_sets": [list(row) for row in forbidden_task_sets],
        "forbidden_task_set_count": len(forbidden_task_sets),
        "variant": variant,
        "formulation_kind": formulation_kind,
        "status": result.get("status") or result.get("algorithm_status") or "",
        "exact_status": exact_status,
        "pricing_state": result.get("pricing_state") or "",
        "negative_feasibility_search_enabled": bool(result.get("negative_feasibility_search_enabled")),
        "negative_feasibility_zero_objective_enabled": bool(
            result.get("negative_feasibility_zero_objective_enabled")
        ),
        "objective_bound_no_negative_cutoff_enabled": bool(
            result.get("objective_bound_no_negative_cutoff_enabled")
        ),
        "objective_bound_no_negative_cutoff_value": result.get(
            "objective_bound_no_negative_cutoff_value"
        ),
        "objective_bound_no_negative_cutoff_can_certify": bool(
            result.get("objective_bound_no_negative_cutoff_can_certify")
        ),
        "zero_capacity_slot_truncation_enabled": bool(
            result.get("zero_capacity_slot_truncation_enabled")
        ),
        "zero_capacity_slot_truncation_original_slot_count": _first_int(
            result.get("zero_capacity_slot_truncation_original_slot_count")
        ),
        "zero_capacity_slot_truncation_effective_slot_count": _first_int(
            result.get("zero_capacity_slot_truncation_effective_slot_count")
        ),
        "zero_capacity_slot_truncation_trimmed_slot_count": _first_int(
            result.get("zero_capacity_slot_truncation_trimmed_slot_count")
        ),
        "zero_capacity_slot_truncation_first_zero_slot": _first_int(
            result.get("zero_capacity_slot_truncation_first_zero_slot")
        ),
        "slot_sequence_capacity_live_bound_enabled": bool(
            result.get("slot_sequence_capacity_live_bound_enabled")
        ),
        "slot_sequence_capacity_live_bound_tightened_slot_count": _first_int(
            result.get("slot_sequence_capacity_live_bound_tightened_slot_count")
        ),
        "slot_sequence_capacity_live_bound_by_slot": result.get(
            "slot_sequence_capacity_live_bound_by_slot"
        ),
        "tight_service_start_bounds_enabled": bool(
            result.get("tight_service_start_bounds_enabled")
        ),
        "tight_service_start_bound_count": _first_int(
            result.get("tight_service_start_bound_count")
        ),
        "tight_service_start_bound_min": _first_float(
            result.get("tight_service_start_bound_min")
        ),
        "tight_service_start_bound_max": _first_float(
            result.get("tight_service_start_bound_max")
        ),
        "tight_time_arc_big_m_enabled": bool(result.get("tight_time_arc_big_m_enabled")),
        "tight_time_arc_big_m_depot_arc_count": _first_int(
            result.get("tight_time_arc_big_m_depot_arc_count")
        ),
        "tight_time_arc_big_m_active_time_bound_count": _first_int(
            result.get("tight_time_arc_big_m_active_time_bound_count")
        ),
        "tight_time_arc_big_m_max_reduction": _first_float(
            result.get("tight_time_arc_big_m_max_reduction")
        ),
        "tight_conditional_sequence_big_m_enabled": bool(
            result.get("tight_conditional_sequence_big_m_enabled")
        ),
        "tight_conditional_sequence_big_m_count": _first_int(
            result.get("tight_conditional_sequence_big_m_count")
        ),
        "tight_conditional_sequence_big_m_max_reduction": _first_float(
            result.get("tight_conditional_sequence_big_m_max_reduction")
        ),
        "slot_service_start_y_lower_bound_enabled": bool(
            result.get("slot_service_start_y_lower_bound_enabled")
        ),
        "slot_service_start_y_lower_bound_count": _first_int(
            result.get("slot_service_start_y_lower_bound_count")
        ),
        "slot_service_start_y_lower_bound_max_lift": _first_float(
            result.get("slot_service_start_y_lower_bound_max_lift")
        ),
        "slot_service_start_y_lower_bound_min": _first_float(
            result.get("slot_service_start_y_lower_bound_min")
        ),
        "slot_service_start_y_lower_bound_max": _first_float(
            result.get("slot_service_start_y_lower_bound_max")
        ),
        "sortie_start_upper_bound": _first_float(result.get("sortie_start_upper_bound")),
        "pricing_complete_by_dual_bound": bool(result.get("pricing_complete_by_dual_bound")),
        "dual_bound_can_certify_no_negative": bool(result.get("dual_bound_can_certify_no_negative")),
        "best_reduced_cost": best_rc,
        "dual_bound": dual_bound,
        "negative_found": negative_found,
        "negative_column_count": _first_int(result.get("negative_column_count")),
        "partition_negative_task_set": list(negative_task_set) if negative_found else [],
        "partition_negative_task_set_size": len(negative_task_set) if negative_found else "",
        "partition_negative_true_rc": best_rc if negative_found else "",
        "partition_negative_source_region_id": str(region_id) if negative_found else "",
        "partition_negative_source_region_kind": str(region_kind) if negative_found else "",
        "partition_negative_solution_payload": negative_solution_payload,
        "partition_negative_payload_available": bool(negative_solution_payload),
        "partition_negative_already_active": negative_already_active,
        "partition_negative_active_task_set_seen": negative_active_task_set_seen,
        "partition_negative_replacement_or_new_task_set": negative_relation,
        "partition_source_active_column_count": source_active_count,
        "partition_dual_active_column_count": dual_active_count,
        "partition_dual_source": str(dual_source or ""),
        **(dual_refresh_payload or {}),
        "partition_active_pool_after_dual_delta": active_pool_after_dual_delta,
        "partition_dual_scope_matches_active_pool": dual_scope_matches_active_pool,
        **manual_rc_audit,
        "partition_negative_feasibility_fallback_enabled": bool(
            result.get("partition_negative_feasibility_fallback_enabled")
        ),
        "partition_negative_feasibility_fallback_run": bool(
            result.get("partition_negative_feasibility_fallback_run")
        ),
        "partition_negative_feasibility_fallback_used": bool(
            result.get("partition_negative_feasibility_fallback_used")
        ),
        "partition_negative_feasibility_fallback_status": result.get(
            "partition_negative_feasibility_fallback_status"
        )
        or "",
        "partition_negative_feasibility_fallback_exact_status": result.get(
            "partition_negative_feasibility_fallback_exact_status"
        )
        or "",
        "partition_optimization_best_reduced_cost": _first_float(
            result.get("partition_optimization_best_reduced_cost")
        ),
        "partition_optimization_dual_bound": _first_float(
            result.get("partition_optimization_dual_bound")
        ),
        "partition_optimization_exact_status": result.get("partition_optimization_exact_status") or "",
        "region_pricing_complete": region_complete,
        "region_can_certify_no_negative": region_can_certify,
        "region_can_certify_full_space": False,
        "official_certificate_allowed": False,
        "can_claim_certificate": False,
        "can_certify_no_negative": False,
        "diagnostic_only": True,
        "wall_time_sec": _first_float(result.get("wall_time_sec"), wall_time),
        "pricing_rc_audit_pass": result.get("pricing_rc_audit_pass"),
        "model_status_name": result.get("model_status_name") or "",
        "variable_count": _first_int(result.get("variable_count")),
        "constraint_count": _first_int(result.get("constraint_count")),
        "zero_capacity_slot_truncation_enabled": bool(
            result.get("zero_capacity_slot_truncation_enabled")
        ),
        "zero_capacity_slot_truncation_original_slot_count": _first_int(
            result.get("zero_capacity_slot_truncation_original_slot_count")
        ),
        "zero_capacity_slot_truncation_effective_slot_count": _first_int(
            result.get("zero_capacity_slot_truncation_effective_slot_count")
        ),
        "zero_capacity_slot_truncation_trimmed_slot_count": _first_int(
            result.get("zero_capacity_slot_truncation_trimmed_slot_count")
        ),
        "zero_capacity_slot_truncation_first_zero_slot": _first_int(
            result.get("zero_capacity_slot_truncation_first_zero_slot")
        ),
        "slot_sequence_capacity_live_bound_enabled": bool(
            result.get("slot_sequence_capacity_live_bound_enabled")
        ),
        "slot_sequence_capacity_live_bound_tightened_slot_count": _first_int(
            result.get("slot_sequence_capacity_live_bound_tightened_slot_count")
        ),
        "slot_sequence_capacity_live_bound_by_slot": result.get(
            "slot_sequence_capacity_live_bound_by_slot"
        ),
        "tight_service_start_bounds_enabled": bool(
            result.get("tight_service_start_bounds_enabled")
        ),
        "tight_service_start_bound_count": _first_int(
            result.get("tight_service_start_bound_count")
        ),
        "tight_service_start_bound_min": _first_float(
            result.get("tight_service_start_bound_min")
        ),
        "tight_service_start_bound_max": _first_float(
            result.get("tight_service_start_bound_max")
        ),
        "tight_time_arc_big_m_enabled": bool(result.get("tight_time_arc_big_m_enabled")),
        "tight_time_arc_big_m_depot_arc_count": _first_int(
            result.get("tight_time_arc_big_m_depot_arc_count")
        ),
        "tight_time_arc_big_m_active_time_bound_count": _first_int(
            result.get("tight_time_arc_big_m_active_time_bound_count")
        ),
        "tight_time_arc_big_m_max_reduction": _first_float(
            result.get("tight_time_arc_big_m_max_reduction")
        ),
        "tight_conditional_sequence_big_m_enabled": bool(
            result.get("tight_conditional_sequence_big_m_enabled")
        ),
        "tight_conditional_sequence_big_m_count": _first_int(
            result.get("tight_conditional_sequence_big_m_count")
        ),
        "tight_conditional_sequence_big_m_max_reduction": _first_float(
            result.get("tight_conditional_sequence_big_m_max_reduction")
        ),
        "slot_service_start_y_lower_bound_enabled": bool(
            result.get("slot_service_start_y_lower_bound_enabled")
        ),
        "slot_service_start_y_lower_bound_count": _first_int(
            result.get("slot_service_start_y_lower_bound_count")
        ),
        "slot_service_start_y_lower_bound_max_lift": _first_float(
            result.get("slot_service_start_y_lower_bound_max_lift")
        ),
        "slot_service_start_y_lower_bound_min": _first_float(
            result.get("slot_service_start_y_lower_bound_min")
        ),
        "slot_service_start_y_lower_bound_max": _first_float(
            result.get("slot_service_start_y_lower_bound_max")
        ),
        "sortie_start_upper_bound": _first_float(result.get("sortie_start_upper_bound")),
        "sortie_slots_per_journey": _first_int(result.get("sortie_slots_per_journey")),
        "sortie_slot_bound_source": result.get("sortie_slot_bound_source") or "",
        "sortie_slot_horizon_count_bound": _first_int(result.get("sortie_slot_horizon_count_bound")),
        "sortie_slot_latest_start_count_bound": _first_int(result.get("sortie_slot_latest_start_count_bound")),
        "sortie_slot_min_duration_lower_bound": _first_float(result.get("sortie_slot_min_duration_lower_bound")),
        "sortie_slot_min_energy_recharge_duration_lower_bound": _first_float(
            result.get("sortie_slot_min_energy_recharge_duration_lower_bound")
        ),
        "slot_task_time_pruning_enabled": bool(result.get("slot_task_time_pruning_enabled")),
        "slot_task_time_feasible_assignment_count": _first_int(
            result.get("slot_task_time_feasible_assignment_count")
        ),
        "slot_task_time_pruned_assignment_count": _first_int(
            result.get("slot_task_time_pruned_assignment_count")
        ),
        "slot_task_time_pruned_due_count": _first_int(result.get("slot_task_time_pruned_due_count")),
        "slot_task_time_pruned_horizon_count": _first_int(
            result.get("slot_task_time_pruned_horizon_count")
        ),
        "slot_task_time_total_assignment_count": _first_int(
            result.get("slot_task_time_total_assignment_count")
        ),
        "slot_task_time_original_total_assignment_count": _first_int(
            result.get("slot_task_time_original_total_assignment_count")
        ),
        "slot_task_model_assignment_count": _first_int(
            result.get("slot_task_model_assignment_count")
        ),
        "slot_arc_support_pruning_enabled": bool(result.get("slot_arc_support_pruning_enabled")),
        "slot_arc_support_feasible_assignment_count": _first_int(
            result.get("slot_arc_support_feasible_assignment_count")
        ),
        "slot_arc_support_pruned_assignment_count": _first_int(
            result.get("slot_arc_support_pruned_assignment_count")
        ),
        "slot_arc_support_pruned_unreachable_count": _first_int(
            result.get("slot_arc_support_pruned_unreachable_count")
        ),
        "slot_arc_support_pruned_no_return_count": _first_int(
            result.get("slot_arc_support_pruned_no_return_count")
        ),
        "slot_arc_support_pruned_option_count": _first_int(
            result.get("slot_arc_support_pruned_option_count")
        ),
        "slot_arc_time_pruned_option_count": _first_int(result.get("slot_arc_time_pruned_option_count")),
        "slot_sequence_capacity_arc_pruning_enabled": bool(
            result.get("slot_sequence_capacity_arc_pruning_enabled")
        ),
        "slot_sequence_capacity_arc_pruned_option_count": _first_int(
            result.get("slot_sequence_capacity_arc_pruned_option_count")
        ),
        "slot_sequence_capacity_mtz_disabled_slot_count": _first_int(
            result.get("slot_sequence_capacity_mtz_disabled_slot_count")
        ),
        "single_task_per_active_sortie_arc_pruning_enabled": bool(
            result.get("single_task_per_active_sortie_arc_pruning_enabled")
        ),
        "single_task_per_active_sortie_arc_pruned_option_count": _first_int(
            result.get("single_task_per_active_sortie_arc_pruned_option_count")
        ),
        "single_task_per_active_sortie_mtz_disabled": bool(
            result.get("single_task_per_active_sortie_mtz_disabled")
        ),
        "mtz_connectivity_effective": bool(result.get("mtz_connectivity_effective")),
        "fixed_active_sortie_redundant_constraint_skipped_count": _first_int(
            result.get("fixed_active_sortie_redundant_constraint_skipped_count")
        ),
        "single_task_per_active_sortie_slot_visit_eq_count": _first_int(
            result.get("single_task_per_active_sortie_slot_visit_eq_count")
        ),
        "single_task_per_active_sortie_y_z_link_skipped_count": _first_int(
            result.get("single_task_per_active_sortie_y_z_link_skipped_count")
        ),
        "resource_arc_pruning_enabled": bool(result.get("resource_arc_pruning_enabled")),
        "resource_arc_pruned_option_count": _first_int(result.get("resource_arc_pruned_option_count")),
        "resource_arc_energy_pruned_option_count": _first_int(
            result.get("resource_arc_energy_pruned_option_count")
        ),
        "resource_arc_shadow_pruned_option_count": _first_int(
            result.get("resource_arc_shadow_pruned_option_count")
        ),
        "resource_arc_demand_pruned_option_count": _first_int(
            result.get("resource_arc_demand_pruned_option_count")
        ),
        "slot_task_sequence_capacity_upper_bound": _first_int(
            result.get("slot_task_sequence_capacity_upper_bound")
        ),
        "slot_task_sequence_capacity_limited_slot_count": _first_int(
            result.get("slot_task_sequence_capacity_limited_slot_count")
        ),
        "slot_task_sequence_capacity_empty_slot_count": _first_int(
            result.get("slot_task_sequence_capacity_empty_slot_count")
        ),
        "slot_task_matching_capacity_upper_bound": _first_int(
            result.get("slot_task_matching_capacity_upper_bound")
        ),
        "required_task_count_certified_by_dual_task_slot_lower_bound": bool(
            result.get("required_task_count_certified_by_dual_task_slot_lower_bound")
        ),
        "required_task_count_infeasible_by_dual_task_slot_lower_bound": bool(
            result.get("required_task_count_infeasible_by_dual_task_slot_lower_bound")
        ),
        "dual_task_slot_lower_bound_enabled": bool(result.get("dual_task_slot_lower_bound_enabled")),
        "dual_task_slot_lower_bound_applicable": bool(result.get("dual_task_slot_lower_bound_applicable")),
        "dual_task_slot_lower_bound_optimal": bool(result.get("dual_task_slot_lower_bound_optimal")),
        "dual_task_slot_lower_bound_status": result.get("dual_task_slot_lower_bound_status") or "",
        "dual_task_slot_lower_bound_value": _first_float(result.get("dual_task_slot_lower_bound_value")),
        "dual_task_slot_lower_bound_region_infeasible": bool(
            result.get("dual_task_slot_lower_bound_region_infeasible")
        ),
        "dual_task_slot_lower_bound_route_arc_mode": (
            result.get("dual_task_slot_lower_bound_route_arc_mode") or ""
        ),
        "dual_task_slot_lower_bound_route_arc_value": _first_float(
            result.get("dual_task_slot_lower_bound_route_arc_value")
        ),
        "dual_task_slot_lower_bound_route_arc_row_count": _first_int(
            result.get("dual_task_slot_lower_bound_route_arc_row_count")
        ),
        "dual_task_slot_lower_bound_route_arc_global_constant": _first_float(
            result.get("dual_task_slot_lower_bound_route_arc_global_constant")
        ),
        "dual_task_slot_lower_bound_route_arc_slot_constant": _first_float(
            result.get("dual_task_slot_lower_bound_route_arc_slot_constant")
        ),
        "dual_task_slot_lower_bound_route_arc_constant": _first_float(
            result.get("dual_task_slot_lower_bound_route_arc_constant")
        ),
        "dual_task_slot_lower_bound_route_arc_slot_outbound_sum": _first_float(
            result.get("dual_task_slot_lower_bound_route_arc_slot_outbound_sum")
        ),
        "dual_task_slot_lower_bound_route_arc_slot_return_sum": _first_float(
            result.get("dual_task_slot_lower_bound_route_arc_slot_return_sum")
        ),
        "dual_task_slot_lower_bound_single_task_route_arc_bound_row_count": _first_int(
            result.get("dual_task_slot_lower_bound_single_task_route_arc_bound_row_count")
        ),
        "dual_task_slot_lower_bound_single_task_route_arc_bound_min": _first_float(
            result.get("dual_task_slot_lower_bound_single_task_route_arc_bound_min")
        ),
        "dual_task_slot_lower_bound_single_task_route_arc_bound_max": _first_float(
            result.get("dual_task_slot_lower_bound_single_task_route_arc_bound_max")
        ),
        "dual_task_slot_lower_bound_one_pair_rest_single_route_arc_var_count": _first_int(
            result.get("dual_task_slot_lower_bound_one_pair_rest_single_route_arc_var_count")
        ),
        "dual_task_slot_lower_bound_one_pair_rest_single_route_arc_row_count": _first_int(
            result.get("dual_task_slot_lower_bound_one_pair_rest_single_route_arc_row_count")
        ),
        "dual_task_slot_lower_bound_one_pair_rest_single_route_arc_pair_count": _first_int(
            result.get("dual_task_slot_lower_bound_one_pair_rest_single_route_arc_pair_count")
        ),
        "dual_task_slot_lower_bound_one_pair_rest_single_route_arc_separation_row_count": _first_int(
            result.get("dual_task_slot_lower_bound_one_pair_rest_single_route_arc_separation_row_count")
        ),
        "dual_task_slot_lower_bound_one_pair_rest_single_route_arc_separation_iteration_count": _first_int(
            result.get("dual_task_slot_lower_bound_one_pair_rest_single_route_arc_separation_iteration_count")
        ),
        "dual_task_slot_lower_bound_pair_route_arc_bound_row_count": _first_int(
            result.get("dual_task_slot_lower_bound_pair_route_arc_bound_row_count")
        ),
        "dual_task_slot_lower_bound_pair_route_arc_bound_min": _first_float(
            result.get("dual_task_slot_lower_bound_pair_route_arc_bound_min")
        ),
        "dual_task_slot_lower_bound_pair_route_arc_bound_max": _first_float(
            result.get("dual_task_slot_lower_bound_pair_route_arc_bound_max")
        ),
        "dual_task_slot_lower_bound_triple_route_arc_bound_row_count": _first_int(
            result.get("dual_task_slot_lower_bound_triple_route_arc_bound_row_count")
        ),
        "dual_task_slot_lower_bound_triple_route_arc_bound_min": _first_float(
            result.get("dual_task_slot_lower_bound_triple_route_arc_bound_min")
        ),
        "dual_task_slot_lower_bound_triple_route_arc_bound_max": _first_float(
            result.get("dual_task_slot_lower_bound_triple_route_arc_bound_max")
        ),
        "dual_task_slot_lower_bound_pair_completion_lift_var_count": _first_int(
            result.get("dual_task_slot_lower_bound_pair_completion_lift_var_count")
        ),
        "dual_task_slot_lower_bound_pair_completion_lift_row_count": _first_int(
            result.get("dual_task_slot_lower_bound_pair_completion_lift_row_count")
        ),
        "dual_task_slot_lower_bound_pair_completion_lift_min": _first_float(
            result.get("dual_task_slot_lower_bound_pair_completion_lift_min")
        ),
        "dual_task_slot_lower_bound_pair_completion_lift_max": _first_float(
            result.get("dual_task_slot_lower_bound_pair_completion_lift_max")
        ),
        "dual_task_slot_lower_bound_cross_slot_completion_lift_var_count": _first_int(
            result.get("dual_task_slot_lower_bound_cross_slot_completion_lift_var_count")
        ),
        "dual_task_slot_lower_bound_cross_slot_completion_lift_row_count": _first_int(
            result.get("dual_task_slot_lower_bound_cross_slot_completion_lift_row_count")
        ),
        "dual_task_slot_lower_bound_cross_slot_pair_completion_separation_row_count": _first_int(
            result.get("dual_task_slot_lower_bound_cross_slot_pair_completion_separation_row_count")
        ),
        "dual_task_slot_lower_bound_cross_slot_completion_lift_min": _first_float(
            result.get("dual_task_slot_lower_bound_cross_slot_completion_lift_min")
        ),
        "dual_task_slot_lower_bound_cross_slot_completion_lift_max": _first_float(
            result.get("dual_task_slot_lower_bound_cross_slot_completion_lift_max")
        ),
        "dual_task_slot_lower_bound_wall_time_sec": _first_float(
            result.get("dual_task_slot_lower_bound_wall_time_sec")
        ),
        "dual_task_slot_lower_bound_variable_count": _first_int(
            result.get("dual_task_slot_lower_bound_variable_count")
        ),
        "dual_task_slot_lower_bound_constraint_count": _first_int(
            result.get("dual_task_slot_lower_bound_constraint_count")
        ),
        "dual_task_slot_lower_bound_pair_conflict_row_count": _first_int(
            result.get("dual_task_slot_lower_bound_pair_conflict_row_count")
        ),
        "dual_task_slot_lower_bound_hyperedge_conflict_row_count": _first_int(
            result.get("dual_task_slot_lower_bound_hyperedge_conflict_row_count")
        ),
        **_dual_task_slot_full_space_lower_bound_fields(result),
        **_single_journey_mip_start_fields(result),
        **_required_task_set_region_fields(result),
        "note": (
            "exact task-set region proof candidate; not a full-space certificate"
            if str(region_kind) == "exact_task_set"
            else "residual task-count region proof candidate after exact task-set regions; not a full-space certificate"
            if str(region_kind) == "residual_task_count"
            else "residual region proof candidate after exact task-set regions; not a full-space certificate"
        ),
    }


def _partition_negative_task_set(result: dict, *, fallback_task_set: tuple[str, ...]) -> tuple[str, ...]:
    best_column = result.get("best_column") if isinstance(result.get("best_column"), dict) else {}
    tasks = best_column.get("tasks")
    if tasks:
        return tuple(sorted(str(task) for task in tasks if str(task)))
    journeys = result.get("journeys")
    if journeys:
        try:
            journey = tuple(journeys)[0]
        except (TypeError, IndexError):
            journey = None
        if journey is not None:
            task_set = getattr(journey, "task_set", None)
            if task_set:
                return tuple(sorted(str(task) for task in task_set if str(task)))
    return tuple(sorted(str(task) for task in fallback_task_set if str(task)))


def _solution_payload_task_set(payload: dict | None) -> tuple[str, ...]:
    if not isinstance(payload, dict):
        return tuple()
    tasks: set[str] = set()
    for sortie in payload.get("sorties") or []:
        if not isinstance(sortie, dict):
            continue
        for task_id in sortie.get("tasks") or []:
            task = str(task_id)
            if task:
                tasks.add(task)
    return tuple(sorted(tasks))


def _solution_payload_column_key(payload: dict | None) -> tuple:
    if not isinstance(payload, dict):
        return tuple()
    sortie_keys = []
    for sortie in payload.get("sorties") or []:
        if not isinstance(sortie, dict):
            continue
        tasks = tuple(str(task_id) for task_id in sortie.get("tasks") or [])
        legs = tuple(
            (str(leg.get("from")), str(leg.get("to")), str(leg.get("path_type")))
            for leg in sortie.get("legs") or []
            if isinstance(leg, dict)
        )
        try:
            start_time = round(float(sortie.get("start_time", 0.0)), 6)
        except (TypeError, ValueError):
            start_time = 0.0
        sortie_keys.append((tasks, legs, start_time))
    return tuple(sortie_keys)


def _partition_negative_manual_rc_audit(
    payload: dict | None,
    *,
    data,
    duals: JourneyDuals | None,
    pricing_rc: float | None,
    negative_eps: float,
) -> dict:
    base = {
        "partition_negative_manual_rc": "",
        "partition_negative_pricing_rc_diff": "",
        "partition_negative_rc_audit_pass": "",
        "partition_negative_rc_audit_error": "",
    }
    if not isinstance(payload, dict) or data is None or duals is None or pricing_rc is None:
        return base
    try:
        column = journey_column_from_solution_payload(data, payload)
        manual_rc = manual_journey_reduced_cost(column, duals)
        diff = round(float(manual_rc) - float(pricing_rc), 9)
        base.update(
            {
                "partition_negative_manual_rc": manual_rc,
                "partition_negative_pricing_rc_diff": diff,
                "partition_negative_rc_audit_pass": abs(diff) <= max(1.0e-7, abs(float(negative_eps))),
            }
        )
    except Exception as exc:  # pragma: no cover - defensive diagnostic path
        base["partition_negative_rc_audit_pass"] = False
        base["partition_negative_rc_audit_error"] = str(exc)
    return base


def _refresh_partition_duals_from_active_pool(
    data,
    active_payloads: list[dict],
    *,
    negative_eps: float,
    max_iterations: int,
) -> dict:
    fallback = JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}, fleet_limit=0.0, cuts={})
    payload = {
        "partition_dual_refresh_status": "NOT_RUN",
        "partition_dual_refresh_min_rc": "",
        "partition_dual_refresh_negative_count": "",
        "partition_dual_refresh_input_column_count": len(active_payloads),
        "partition_dual_refresh_rmp_active_column_count": "",
        "partition_dual_refresh_error": "",
    }
    try:
        columns = tuple(journey_column_from_solution_payload(data, row) for row in active_payloads)
        if not columns:
            payload["partition_dual_refresh_status"] = "NO_ACTIVE_COLUMNS"
            return {
                "duals": fallback,
                "partition_dual_source": "refreshed_active_pool_failed_no_columns",
                "payload": payload,
            }
        rmp = solve_restricted_journey_rmp(
            data.task_ids,
            columns,
            fleet_size=data.fleet_size,
            negative_eps=float(negative_eps),
            max_iterations=int(max_iterations),
        )
        rc_values = [manual_journey_reduced_cost(column, rmp.duals) for column in columns]
        payload.update(
            {
                "partition_dual_refresh_status": rmp.status,
                "partition_dual_refresh_min_rc": rmp.min_reduced_cost,
                "partition_dual_refresh_negative_count": sum(
                    1 for value in rc_values if float(value) < -abs(float(negative_eps))
                ),
                "partition_dual_refresh_rmp_active_column_count": rmp.active_column_count,
            }
        )
        if rmp.status == "RESTRICTED_RMP_OPTIMAL":
            return {
                "duals": rmp.duals,
                "partition_dual_source": "refreshed_active_pool_restricted_rmp",
                "payload": payload,
            }
        payload["partition_dual_refresh_error"] = rmp.note
    except Exception as exc:  # pragma: no cover - defensive diagnostic path
        payload["partition_dual_refresh_status"] = "REFRESH_EXCEPTION"
        payload["partition_dual_refresh_error"] = str(exc)
    return {
        "duals": fallback,
        "partition_dual_source": "refreshed_active_pool_failed_zero_dual",
        "payload": payload,
    }


def _partition_region_needs_negative_feasibility_fallback(
    result: dict,
    *,
    region_kind: str,
    negative_eps: float,
) -> bool:
    best_rc = _first_float(result.get("best_reduced_cost"), result.get("pricing_best_reduced_cost"))
    negative_found = bool(
        result.get("negative_found")
        or (best_rc is not None and float(best_rc) < -abs(float(negative_eps)))
    )
    if negative_found:
        return False
    if str(region_kind) == "exact_task_set":
        region_complete = bool(result.get("pricing_complete_for_required_task_set"))
    elif str(region_kind) == "residual_task_count":
        region_complete = bool(result.get("pricing_complete_for_required_task_count"))
    else:
        exact_status = str(result.get("exact_status") or "")
        region_complete = exact_status in {
            "RESTRICTED_PRICING_OPTIMAL",
            "RESTRICTED_PRICING_INFEASIBLE",
        }
    if region_complete:
        return False
    return bool(best_rc is None or float(best_rc) >= -abs(float(negative_eps)))


def _partition_region_merge_negative_feasibility_fallback(
    optimization_result: dict,
    fallback_result: dict | None,
    *,
    negative_eps: float,
) -> dict:
    if not fallback_result:
        result = dict(optimization_result)
        result["partition_negative_feasibility_fallback_run"] = False
        result["partition_negative_feasibility_fallback_used"] = False
        return result
    fallback_best_rc = _first_float(
        fallback_result.get("best_reduced_cost"),
        fallback_result.get("pricing_best_reduced_cost"),
    )
    fallback_negative = bool(
        fallback_result.get("negative_found")
        or (fallback_best_rc is not None and float(fallback_best_rc) < -abs(float(negative_eps)))
    )
    fallback_region_certifies = bool(
        fallback_result.get("required_task_set_region_can_certify_no_negative")
        or fallback_result.get("required_task_count_region_can_certify_no_negative")
    )
    fallback_used = bool(fallback_negative or fallback_region_certifies)
    result = dict(fallback_result if fallback_used else optimization_result)
    result.update(
        {
            "partition_negative_feasibility_fallback_run": True,
            "partition_negative_feasibility_fallback_used": fallback_used,
            "partition_negative_feasibility_fallback_status": fallback_result.get("status")
            or fallback_result.get("algorithm_status")
            or "",
            "partition_negative_feasibility_fallback_exact_status": fallback_result.get("exact_status") or "",
            "partition_optimization_best_reduced_cost": _first_float(
                optimization_result.get("best_reduced_cost"),
                optimization_result.get("pricing_best_reduced_cost"),
            ),
            "partition_optimization_dual_bound": _first_float(
                optimization_result.get("dual_bound"),
                optimization_result.get("bound"),
            ),
            "partition_optimization_exact_status": optimization_result.get("exact_status") or "",
        }
    )
    return result


def _partition_probe_summary(
    rows: list[dict],
    *,
    task_sets: list[tuple[str, ...]],
    negative_eps: float,
    total_task_count: int = 0,
) -> dict:
    best_by_region = _partition_best_rows_by_region(rows)
    best_region_rows = list(best_by_region.values())
    exact_best = [
        row for row in best_region_rows if row.get("region_kind") == "exact_task_set"
    ]
    single_residual_best = [
        row for row in best_region_rows if row.get("region_kind") == "residual_after_exact_task_sets"
    ]
    task_count_residual_best = [
        row for row in best_region_rows if row.get("region_kind") == "residual_task_count"
    ]
    residual_best = task_count_residual_best or single_residual_best
    residual_row = single_residual_best[0] if single_residual_best else {}
    exact_region_proven = [
        row for row in exact_best if row.get("region_can_certify_no_negative") is True
    ]
    exact_region_negative = [
        row for row in exact_best if row.get("negative_found") is True
    ]
    exact_region_incomplete = [
        row for row in exact_best if row.get("region_pricing_complete") is not True
    ]
    task_count_group_summary = _residual_task_count_group_summary(
        task_count_residual_best,
        total_task_count=int(total_task_count or 0),
        negative_eps=float(negative_eps),
    )
    task_count_expected = task_count_group_summary["expected_counts"]
    task_count_observed = task_count_group_summary["observed_counts"]
    task_count_missing = task_count_group_summary["missing_counts"] if task_count_residual_best else []
    if task_count_residual_best:
        residual_proven = bool(
            task_count_expected
            and not task_count_missing
            and task_count_group_summary["proven_count"] == len(task_count_expected)
        )
        residual_negative = bool(task_count_group_summary["negative_count"] > 0)
        residual_complete = bool(
            task_count_expected
            and not task_count_missing
            and task_count_group_summary["incomplete_count"] == 0
        )
    else:
        residual_proven = bool(residual_row.get("region_can_certify_no_negative") is True)
        residual_negative = bool(residual_row.get("negative_found") is True)
        residual_complete = bool(residual_row.get("region_pricing_complete") is True)
    negative_rows = [row for row in best_region_rows if row.get("negative_found") is True]
    negative_rc_values = [
        value
        for value in (
            _first_float(
                row.get("partition_best_negative_rc"),
                row.get("partition_negative_true_rc"),
                row.get("best_reduced_cost"),
                row.get("dual_bound"),
            )
            for row in negative_rows
        )
        if value is not None
    ]
    gate = _partition_candidate_certificate_gate(
        rows,
        task_sets=task_sets,
        negative_eps=float(negative_eps),
        total_task_count=int(total_task_count or 0),
    )
    partition_candidate_complete = bool(gate.get("partition_candidate_gate_pass") is True)
    best_bounds = [
        _first_float(row.get("dual_bound"), row.get("best_reduced_cost"))
        for row in best_region_rows
        if _first_float(row.get("dual_bound"), row.get("best_reduced_cost")) is not None
    ]
    variable_counts = [
        value
        for value in (_first_int(row.get("variable_count")) for row in best_region_rows)
        if value is not None
    ]
    constraint_counts = [
        value
        for value in (_first_int(row.get("constraint_count")) for row in best_region_rows)
        if value is not None
    ]
    slot_feasible_assignments = [
        value
        for value in (
            _first_int(row.get("slot_task_time_feasible_assignment_count")) for row in best_region_rows
        )
        if value is not None
    ]
    slot_pruned_assignments = [
        value
        for value in (
            _first_int(row.get("slot_task_time_pruned_assignment_count")) for row in best_region_rows
        )
        if value is not None
    ]
    slot_pruned_arcs = [
        value
        for value in (_first_int(row.get("slot_arc_time_pruned_option_count")) for row in best_region_rows)
        if value is not None
    ]
    single_task_per_active_pruned_arcs = [
        value
        for value in (
            _first_int(row.get("single_task_per_active_sortie_arc_pruned_option_count"))
            for row in best_region_rows
        )
        if value is not None
    ]
    single_task_per_active_pruned_arcs = [
        value
        for value in (
            _first_int(row.get("single_task_per_active_sortie_arc_pruned_option_count"))
            for row in best_region_rows
        )
        if value is not None
    ]
    resource_pruned_arcs = [
        value
        for value in (_first_int(row.get("resource_arc_pruned_option_count")) for row in best_region_rows)
        if value is not None
    ]
    resource_energy_pruned_arcs = [
        value
        for value in (
            _first_int(row.get("resource_arc_energy_pruned_option_count")) for row in best_region_rows
        )
        if value is not None
    ]
    resource_shadow_pruned_arcs = [
        value
        for value in (
            _first_int(row.get("resource_arc_shadow_pruned_option_count")) for row in best_region_rows
        )
        if value is not None
    ]
    resource_demand_pruned_arcs = [
        value
        for value in (
            _first_int(row.get("resource_arc_demand_pruned_option_count")) for row in best_region_rows
        )
        if value is not None
    ]
    slot_sequence_caps = [
        value
        for value in (
            _first_int(row.get("slot_task_sequence_capacity_upper_bound")) for row in best_region_rows
        )
        if value is not None
    ]
    slot_matching_caps = [
        value
        for value in (
            _first_int(row.get("slot_task_matching_capacity_upper_bound")) for row in best_region_rows
        )
        if value is not None
    ]
    global_lb = None if not best_bounds else round(min(float(value) for value in best_bounds), 9)
    return {
        "partition_model": (
            "exact_task_set_regions_plus_residual_task_count_regions"
            if task_count_residual_best
            else "exact_task_set_regions_plus_final_residual"
        ),
        "partition_regions_disjoint": True,
        "partition_regions_cover_full_space": bool(
            (task_sets or task_count_residual_best)
            and (
                bool(single_residual_best)
                or bool(task_count_expected and not task_count_missing)
            )
        ),
        "partition_candidate_complete": partition_candidate_complete,
        "partition_candidate_can_certify_no_negative": partition_candidate_complete,
        "official_certificate_allowed": False,
        "can_claim_certificate": False,
        "target_task_set_count": len(task_sets),
        "exact_region_observed_count": len(exact_best),
        "exact_region_proven_count": len(exact_region_proven),
        "exact_region_negative_count": len(exact_region_negative),
        "exact_region_incomplete_count": len(exact_region_incomplete),
        "residual_region_observed": bool(residual_best),
        "residual_region_complete": residual_complete,
        "residual_region_proven": residual_proven,
        "residual_region_negative_found": residual_negative,
        "residual_task_count_partition_enabled": bool(task_count_residual_best),
        "residual_task_count_region_expected_count": len(task_count_expected),
        "residual_task_count_region_observed_count": len(task_count_observed),
        "residual_task_count_region_proven_count": task_count_group_summary["proven_count"],
        "residual_task_count_region_incomplete_count": task_count_group_summary["incomplete_count"],
        "residual_task_count_region_negative_count": task_count_group_summary["negative_count"],
        "residual_task_count_region_missing_count": len(task_count_missing),
        "residual_task_count_region_missing_counts": task_count_missing,
        "residual_active_sortie_count_partition_enabled": bool(
            task_count_group_summary["active_partition_enabled"]
        ),
        "residual_active_sortie_count_missing_group_count": int(
            task_count_group_summary["missing_active_group_count"]
        ),
        "residual_active_sortie_count_duplicate_group_count": int(
            task_count_group_summary["duplicate_active_group_count"]
        ),
        "best_partition_region_lb": global_lb,
        "partition_bound_gap_to_zero": None if global_lb is None else round(max(0.0, -float(global_lb)), 9),
        "partition_negative_already_active_count": sum(
            1 for row in negative_rows if row.get("partition_negative_already_active") is True
        ),
        "partition_negative_replacement_task_set_count": sum(
            1
            for row in negative_rows
            if str(row.get("partition_negative_replacement_or_new_task_set") or "") == "replacement"
        ),
        "partition_negative_new_task_set_count": sum(
            1
            for row in negative_rows
            if str(row.get("partition_negative_replacement_or_new_task_set") or "") == "new_task_set"
        ),
        "partition_best_negative_rc": (
            None if not negative_rc_values else round(min(float(value) for value in negative_rc_values), 9)
        ),
        "partition_region_variable_count_max": max(variable_counts) if variable_counts else 0,
        "partition_region_constraint_count_max": max(constraint_counts) if constraint_counts else 0,
        "partition_region_variable_count_mean": (
            None if not variable_counts else round(float(mean(variable_counts)), 6)
        ),
        "partition_region_constraint_count_mean": (
            None if not constraint_counts else round(float(mean(constraint_counts)), 6)
        ),
        "partition_region_slot_task_time_feasible_assignment_count_max": (
            max(slot_feasible_assignments) if slot_feasible_assignments else 0
        ),
        "partition_region_slot_task_time_pruned_assignment_count_sum": sum(slot_pruned_assignments),
        "partition_region_slot_arc_time_pruned_option_count_sum": sum(slot_pruned_arcs),
        "partition_region_single_task_per_active_sortie_arc_pruned_option_count_sum": sum(
            single_task_per_active_pruned_arcs
        ),
        "partition_region_resource_arc_pruned_option_count_sum": sum(resource_pruned_arcs),
        "partition_region_resource_arc_energy_pruned_option_count_sum": sum(resource_energy_pruned_arcs),
        "partition_region_resource_arc_shadow_pruned_option_count_sum": sum(resource_shadow_pruned_arcs),
        "partition_region_resource_arc_demand_pruned_option_count_sum": sum(resource_demand_pruned_arcs),
        "partition_region_slot_sequence_capacity_upper_bound_max": (
            max(slot_sequence_caps) if slot_sequence_caps else 0
        ),
        "partition_region_slot_matching_capacity_upper_bound_max": (
            max(slot_matching_caps) if slot_matching_caps else 0
        ),
        "partition_region_infeasible_by_slot_sequence_capacity_count": sum(
            1
            for row in best_region_rows
            if bool(row.get("required_task_count_infeasible_by_slot_sequence_capacity"))
        ),
        "partition_region_infeasible_by_slot_matching_count": sum(
            1 for row in best_region_rows if bool(row.get("required_task_count_infeasible_by_slot_matching"))
        ),
        "partition_region_infeasible_by_pair_conflict_capacity_count": sum(
            1
            for row in best_region_rows
            if bool(row.get("required_task_count_infeasible_by_pair_conflict_capacity"))
        ),
        "partition_region_certified_by_dual_task_slot_lower_bound_count": sum(
            1
            for row in best_region_rows
            if bool(row.get("required_task_count_certified_by_dual_task_slot_lower_bound"))
        ),
        "partition_region_infeasible_by_dual_task_slot_lower_bound_count": sum(
            1
            for row in best_region_rows
            if bool(row.get("required_task_count_infeasible_by_dual_task_slot_lower_bound"))
        ),
        "partition_region_dual_task_slot_lower_bound_enabled_count": sum(
            1 for row in best_region_rows if bool(row.get("dual_task_slot_lower_bound_enabled"))
        ),
        "partition_region_dual_task_slot_lower_bound_optimal_count": sum(
            1 for row in best_region_rows if bool(row.get("dual_task_slot_lower_bound_optimal"))
        ),
        "partition_region_pair_conflict_capacity_bound_enabled_count": sum(
            1 for row in best_region_rows if bool(row.get("task_slot_pair_conflict_capacity_bound_enabled"))
        ),
        "partition_region_infeasible_by_empty_active_slot_count": sum(
            1
            for row in best_region_rows
            if bool(row.get("required_active_sortie_count_infeasible_by_empty_slot"))
        ),
        "partition_region_infeasible_by_active_capacity_min_count": sum(
            1
            for row in best_region_rows
            if bool(row.get("required_active_sortie_count_infeasible_by_capacity_min"))
        ),
        "partition_source_active_column_count": _max_present_int(
            row.get("partition_source_active_column_count") for row in rows
        ),
        "partition_dual_active_column_count": _max_present_int(
            row.get("partition_dual_active_column_count") for row in rows
        ),
        "partition_dual_source": _first_present_str(row.get("partition_dual_source") for row in rows),
        "partition_dual_refresh_status": _first_present_str(
            row.get("partition_dual_refresh_status") for row in rows
        ),
        "partition_dual_refresh_min_rc": _min_present_float(
            row.get("partition_dual_refresh_min_rc") for row in rows
        ),
        "partition_dual_refresh_negative_count": _max_present_int(
            row.get("partition_dual_refresh_negative_count") for row in rows
        ),
        "partition_dual_refresh_input_column_count": _max_present_int(
            row.get("partition_dual_refresh_input_column_count") for row in rows
        ),
        "partition_dual_refresh_rmp_active_column_count": _max_present_int(
            row.get("partition_dual_refresh_rmp_active_column_count") for row in rows
        ),
        "partition_active_pool_after_dual_delta": _max_present_int(
            row.get("partition_active_pool_after_dual_delta") for row in rows
        ),
        "partition_dual_scope_mismatch_count": sum(
            1 for row in rows if row.get("partition_dual_scope_matches_active_pool") is False
        ),
        "partition_negative_rc_audit_fail_count": sum(
            1 for row in negative_rows if row.get("partition_negative_rc_audit_pass") is False
        ),
        "partition_region_mip_start_enabled_count": sum(
            1 for row in rows if row.get("single_journey_mip_start_enabled") is True
        ),
        "partition_region_mip_start_ok_count": sum(
            1 for row in rows if str(row.get("single_journey_mip_start_status") or "") == "OK"
        ),
        "partition_exact_region_mip_start_ok_count": sum(
            1
            for row in rows
            if str(row.get("region_kind") or "") == "exact_task_set"
            and str(row.get("single_journey_mip_start_status") or "") == "OK"
        ),
        "partition_residual_region_mip_start_ok_count": sum(
            1
            for row in rows
            if str(row.get("region_kind") or "")
            in {"residual_after_exact_task_sets", "residual_task_count"}
            and str(row.get("single_journey_mip_start_status") or "") == "OK"
        ),
        "negative_eps": float(negative_eps),
        **gate,
    }


def _partition_best_rows_by_region(rows: list[dict]) -> dict[str, dict]:
    grouped: dict[str, list[dict]] = {}
    context_keys = {
        (
            str(row.get("variant") or ""),
            str(row.get("formulation_kind") or ""),
            str(row.get("source_probe_json") or ""),
            str(row.get("history_round") or ""),
        )
        for row in rows
    }
    include_context = len(context_keys) > 1
    for row in rows:
        region_id = str(row.get("region_id") or "")
        if include_context:
            key = "|".join(
                (
                    region_id,
                    str(row.get("variant") or ""),
                    str(row.get("formulation_kind") or ""),
                    str(row.get("source_probe_json") or ""),
                    str(row.get("history_round") or ""),
                )
            )
        else:
            key = region_id
        grouped.setdefault(key, []).append(row)
    best: dict[str, dict] = {}
    for key, group in grouped.items():
        best[key] = max(
            group,
            key=lambda row: (
                1 if row.get("region_can_certify_no_negative") is True else 0,
                _first_float(row.get("dual_bound"), row.get("best_reduced_cost"), -1.0e100) or -1.0e100,
            ),
        )
    return best


def _partition_probe_model_size_metrics(rows: list[dict]) -> dict:
    best_region_rows = list(_partition_best_rows_by_region(rows).values())
    variable_counts = [
        value
        for value in (_first_int(row.get("variable_count")) for row in best_region_rows)
        if value is not None
    ]
    constraint_counts = [
        value
        for value in (_first_int(row.get("constraint_count")) for row in best_region_rows)
        if value is not None
    ]
    slot_feasible_assignments = [
        value
        for value in (
            _first_int(row.get("slot_task_time_feasible_assignment_count")) for row in best_region_rows
        )
        if value is not None
    ]
    slot_pruned_assignments = [
        value
        for value in (
            _first_int(row.get("slot_task_time_pruned_assignment_count")) for row in best_region_rows
        )
        if value is not None
    ]
    slot_pruned_arcs = [
        value
        for value in (_first_int(row.get("slot_arc_time_pruned_option_count")) for row in best_region_rows)
        if value is not None
    ]
    single_task_per_active_pruned_arcs = [
        value
        for value in (
            _first_int(row.get("single_task_per_active_sortie_arc_pruned_option_count"))
            for row in best_region_rows
        )
        if value is not None
    ]
    slot_sequence_caps = [
        value
        for value in (
            _first_int(row.get("slot_task_sequence_capacity_upper_bound")) for row in best_region_rows
        )
        if value is not None
    ]
    slot_matching_caps = [
        value
        for value in (
            _first_int(row.get("slot_task_matching_capacity_upper_bound")) for row in best_region_rows
        )
        if value is not None
    ]
    return {
        "partition_region_variable_count_max": max(variable_counts) if variable_counts else 0,
        "partition_region_constraint_count_max": max(constraint_counts) if constraint_counts else 0,
        "partition_region_variable_count_mean": (
            None if not variable_counts else round(float(mean(variable_counts)), 6)
        ),
        "partition_region_constraint_count_mean": (
            None if not constraint_counts else round(float(mean(constraint_counts)), 6)
        ),
        "partition_region_slot_task_time_feasible_assignment_count_max": (
            max(slot_feasible_assignments) if slot_feasible_assignments else 0
        ),
        "partition_region_slot_task_time_pruned_assignment_count_sum": sum(slot_pruned_assignments),
        "partition_region_slot_arc_time_pruned_option_count_sum": sum(slot_pruned_arcs),
        "partition_region_single_task_per_active_sortie_arc_pruned_option_count_sum": sum(
            single_task_per_active_pruned_arcs
        ),
        "partition_region_slot_sequence_capacity_upper_bound_max": (
            max(slot_sequence_caps) if slot_sequence_caps else 0
        ),
        "partition_region_slot_matching_capacity_upper_bound_max": (
            max(slot_matching_caps) if slot_matching_caps else 0
        ),
        "partition_region_infeasible_by_slot_sequence_capacity_count": sum(
            1
            for row in best_region_rows
            if bool(row.get("required_task_count_infeasible_by_slot_sequence_capacity"))
        ),
        "partition_region_infeasible_by_slot_matching_count": sum(
            1 for row in best_region_rows if bool(row.get("required_task_count_infeasible_by_slot_matching"))
        ),
        "partition_region_infeasible_by_pair_conflict_capacity_count": sum(
            1
            for row in best_region_rows
            if bool(row.get("required_task_count_infeasible_by_pair_conflict_capacity"))
        ),
        "partition_region_certified_by_dual_task_slot_lower_bound_count": sum(
            1
            for row in best_region_rows
            if bool(row.get("required_task_count_certified_by_dual_task_slot_lower_bound"))
        ),
        "partition_region_infeasible_by_dual_task_slot_lower_bound_count": sum(
            1
            for row in best_region_rows
            if bool(row.get("required_task_count_infeasible_by_dual_task_slot_lower_bound"))
        ),
        "partition_region_dual_task_slot_lower_bound_enabled_count": sum(
            1 for row in best_region_rows if bool(row.get("dual_task_slot_lower_bound_enabled"))
        ),
        "partition_region_dual_task_slot_lower_bound_optimal_count": sum(
            1 for row in best_region_rows if bool(row.get("dual_task_slot_lower_bound_optimal"))
        ),
        "partition_region_pair_conflict_capacity_bound_enabled_count": sum(
            1 for row in best_region_rows if bool(row.get("task_slot_pair_conflict_capacity_bound_enabled"))
        ),
        "partition_region_infeasible_by_empty_active_slot_count": sum(
            1
            for row in best_region_rows
            if bool(row.get("required_active_sortie_count_infeasible_by_empty_slot"))
        ),
        "partition_region_infeasible_by_active_capacity_min_count": sum(
            1
            for row in best_region_rows
            if bool(row.get("required_active_sortie_count_infeasible_by_capacity_min"))
        ),
    }


def _residual_task_count_group_summary(
    rows: list[dict],
    *,
    total_task_count: int,
    negative_eps: float,
) -> dict:
    expected_counts = set(range(1, int(total_task_count) + 1)) if int(total_task_count or 0) > 0 else set()
    groups: dict[int, list[dict]] = {}
    for row in rows:
        value = _optional_positive_int(row.get("required_task_count"))
        if value is not None:
            groups.setdefault(value, []).append(row)

    proven_count = 0
    incomplete_count = 0
    negative_count = 0
    negative_bound_count = 0
    missing_active_group_count = 0
    duplicate_active_group_count = 0
    duplicate_direct_group_count = 0
    active_partition_enabled = False
    group_details: dict[int, dict] = {}
    for required_count, group in groups.items():
        active_rows = [
            row for row in group if bool(row.get("required_active_sortie_count_enabled"))
        ]
        if active_rows:
            active_partition_enabled = True
            expected_active: set[int] = set()
            observed_active: list[int] = []
            for row in active_rows:
                for expected_value in row.get("required_active_sortie_count_expected_counts") or []:
                    parsed_expected = _optional_positive_int(expected_value)
                    if parsed_expected is not None:
                        expected_active.add(parsed_expected)
                value = _optional_positive_int(row.get("required_active_sortie_count"))
                if value is not None:
                    observed_active.append(value)
            if not expected_active:
                observed_set = set(observed_active)
                if observed_set:
                    expected_active = observed_set
            observed_set = set(observed_active)
            missing_active = sorted(expected_active - observed_set)
            duplicate_active = len(observed_set) != len(observed_active)
            if missing_active:
                missing_active_group_count += 1
            if duplicate_active:
                duplicate_active_group_count += 1
            group_rows = active_rows
            group_complete = bool(
                expected_active
                and not missing_active
                and all(row.get("region_pricing_complete") is True for row in group_rows)
            )
            group_proven = bool(
                group_complete
                and all(row.get("region_can_certify_no_negative") is True for row in group_rows)
            )
            group_details[required_count] = {
                "active_partition": True,
                "expected_active": sorted(expected_active),
                "observed_active": sorted(observed_set),
                "missing_active": missing_active,
                "duplicate_active": duplicate_active,
                "complete": group_complete,
                "proven": group_proven,
            }
        else:
            duplicate_direct = len(group) != 1
            if duplicate_direct:
                duplicate_direct_group_count += 1
            group_rows = group
            group_complete = bool(
                len(group_rows) == 1 and group_rows[0].get("region_pricing_complete") is True
            )
            group_proven = bool(
                group_complete and group_rows[0].get("region_can_certify_no_negative") is True
            )
            group_details[required_count] = {
                "active_partition": False,
                "complete": group_complete,
                "proven": group_proven,
                "duplicate_direct": duplicate_direct,
            }
        if group_proven:
            proven_count += 1
        if not group_complete:
            incomplete_count += 1
        if any(row.get("negative_found") is True for row in group_rows):
            negative_count += 1
        if any(_row_has_negative_bound(row, negative_eps) for row in group_rows):
            negative_bound_count += 1

    observed_counts = set(groups)
    missing_counts = sorted(expected_counts - observed_counts)
    return {
        "expected_counts": expected_counts,
        "observed_counts": observed_counts,
        "missing_counts": missing_counts,
        "proven_count": proven_count,
        "incomplete_count": incomplete_count,
        "negative_count": negative_count,
        "negative_bound_count": negative_bound_count,
        "missing_active_group_count": missing_active_group_count,
        "duplicate_active_group_count": duplicate_active_group_count,
        "duplicate_direct_group_count": duplicate_direct_group_count,
        "active_partition_enabled": active_partition_enabled,
        "group_details": group_details,
    }


def _partition_candidate_certificate_gate(
    rows: list[dict],
    *,
    task_sets: list[tuple[str, ...]],
    negative_eps: float,
    total_task_count: int = 0,
) -> dict:
    """Validate whether partition rows form a self-contained no-negative candidate.

    This is deliberately still not an official certificate gate.  It checks that
    exact task-set regions and the residual region are internally consistent
    enough to be passed to a future final-judge ledger integration.
    """

    issues: list[str] = []
    target_task_sets = [_canonical_task_set(row) for row in task_sets]
    target_task_set_set = set(target_task_sets)
    if len(target_task_set_set) != len(target_task_sets):
        issues.append("duplicate_target_task_sets")

    best_by_region = _partition_best_rows_by_region(rows)
    exact_best = [
        row for row in best_by_region.values() if row.get("region_kind") == "exact_task_set"
    ]
    single_residual_best = [
        row for row in best_by_region.values() if row.get("region_kind") == "residual_after_exact_task_sets"
    ]
    task_count_residual_best = [
        row for row in best_by_region.values() if row.get("region_kind") == "residual_task_count"
    ]
    if not target_task_sets and not task_count_residual_best:
        issues.append("no_target_task_sets")
    exact_best_task_sets = [_canonical_task_set(row.get("required_task_set") or []) for row in exact_best]
    exact_best_task_set_set = set(exact_best_task_sets)

    missing_exact = sorted(target_task_set_set - exact_best_task_set_set)
    unexpected_exact = sorted(exact_best_task_set_set - target_task_set_set)
    duplicate_exact = len(exact_best_task_set_set) != len(exact_best_task_sets)
    if missing_exact:
        issues.append("missing_exact_task_set_region")
    if unexpected_exact:
        issues.append("unexpected_exact_task_set_region")
    if duplicate_exact:
        issues.append("duplicate_exact_task_set_region")
    if len(exact_best) != len(target_task_sets):
        issues.append("exact_region_count_mismatch")

    residual_task_count_missing: list[int] = []
    residual_task_count_observed: set[int] = set()
    if single_residual_best and task_count_residual_best:
        issues.append("mixed_residual_partition_models")
    if task_count_residual_best:
        task_count_group_summary = _residual_task_count_group_summary(
            task_count_residual_best,
            total_task_count=int(total_task_count or 0),
            negative_eps=float(negative_eps),
        )
        expected_counts = task_count_group_summary["expected_counts"]
        residual_task_count_observed = task_count_group_summary["observed_counts"]
        residual_task_count_missing = task_count_group_summary["missing_counts"]
        unexpected_counts = sorted(residual_task_count_observed - expected_counts)
        if not expected_counts:
            issues.append("missing_residual_task_count_total")
        if residual_task_count_missing:
            issues.append("missing_residual_task_count_region")
        if unexpected_counts:
            issues.append("unexpected_residual_task_count_region")
        if task_count_group_summary["duplicate_direct_group_count"] > 0:
            issues.append("duplicate_residual_task_count_region")
        if task_count_group_summary["duplicate_active_group_count"] > 0:
            issues.append("duplicate_residual_active_sortie_count_region")
        if task_count_group_summary["missing_active_group_count"] > 0:
            issues.append("missing_residual_active_sortie_count_region")
        residual_row = {}
    elif not single_residual_best:
        issues.append("missing_residual_region")
        residual_row: dict = {}
    elif len(single_residual_best) > 1:
        issues.append("multiple_residual_regions")
        residual_row = single_residual_best[0]
    else:
        residual_row = single_residual_best[0]

    if residual_row:
        residual_forbidden_set = {
            _canonical_task_set(task_set) for task_set in (residual_row.get("forbidden_task_sets") or [])
        }
        if residual_forbidden_set != target_task_set_set:
            issues.append("residual_forbidden_task_sets_do_not_match_exact_regions")
    for row in task_count_residual_best:
        residual_forbidden_set = {
            _canonical_task_set(task_set) for task_set in (row.get("forbidden_task_sets") or [])
        }
        if residual_forbidden_set != target_task_set_set:
            issues.append("residual_task_count_forbidden_task_sets_do_not_match_exact_regions")

    exact_proven_count = 0
    for row in exact_best:
        if row.get("region_pricing_complete") is not True:
            issues.append("incomplete_exact_task_set_region")
        if row.get("negative_found") is True:
            issues.append("negative_exact_task_set_region")
        if row.get("region_can_certify_no_negative") is True:
            exact_proven_count += 1
        else:
            issues.append("unproven_exact_task_set_region")
        if _row_has_negative_bound(row, negative_eps):
            issues.append("negative_bound_exact_task_set_region")

    residual_proven = False
    if task_count_residual_best:
        if task_count_group_summary["incomplete_count"] > 0:
            issues.append("incomplete_residual_task_count_region")
        if task_count_group_summary["negative_count"] > 0:
            issues.append("negative_residual_task_count_region")
        if task_count_group_summary["proven_count"] != len(residual_task_count_observed):
            issues.append("unproven_residual_task_count_region")
        if task_count_group_summary["negative_bound_count"] > 0:
            issues.append("negative_bound_residual_task_count_region")
        residual_proven = bool(
            task_count_residual_best
            and task_count_group_summary["proven_count"] == len(expected_counts)
            and not residual_task_count_missing
            and "missing_residual_task_count_total" not in issues
            and "unexpected_residual_task_count_region" not in issues
            and "duplicate_residual_task_count_region" not in issues
            and "duplicate_residual_active_sortie_count_region" not in issues
            and "missing_residual_active_sortie_count_region" not in issues
        )
    elif residual_row:
        if residual_row.get("region_pricing_complete") is not True:
            issues.append("incomplete_residual_region")
        if residual_row.get("negative_found") is True:
            issues.append("negative_residual_region")
        residual_proven = bool(residual_row.get("region_can_certify_no_negative") is True)
        if not residual_proven:
            issues.append("unproven_residual_region")
        if _row_has_negative_bound(residual_row, negative_eps):
            issues.append("negative_bound_residual_region")

    candidate_rows = exact_best + task_count_residual_best + ([residual_row] if residual_row else [])
    variants = {str(row.get("variant") or "") for row in candidate_rows}
    formulation_kinds = {str(row.get("formulation_kind") or "") for row in candidate_rows}
    sources = {str(row.get("source_probe_json") or "") for row in candidate_rows}
    history_rounds = {str(row.get("history_round") or "") for row in candidate_rows}
    if len(variants) > 1:
        issues.append("mixed_variant_partition_rows")
    if len(formulation_kinds) > 1:
        issues.append("mixed_formulation_partition_rows")
    if len(sources) > 1:
        issues.append("mixed_source_probe_partition_rows")
    if len(history_rounds) > 1:
        issues.append("mixed_history_round_partition_rows")

    for row in candidate_rows:
        if row.get("diagnostic_only") is not True:
            issues.append("non_diagnostic_partition_row")
        if row.get("official_certificate_allowed") is True:
            issues.append("partition_row_allows_official_certificate")
        if row.get("can_claim_certificate") is True:
            issues.append("partition_row_claims_certificate")
        if row.get("region_can_certify_full_space") is True or row.get("can_certify_no_negative") is True:
            issues.append("partition_row_claims_full_space_certificate")
        if row.get("pricing_rc_audit_pass") is False:
            issues.append("pricing_rc_audit_failed")

    full_space_partition_valid = bool(
        (target_task_sets or task_count_residual_best)
        and not missing_exact
        and not unexpected_exact
        and not duplicate_exact
        and len(exact_best) == len(target_task_sets)
        and (bool(residual_row) or bool(task_count_residual_best and not residual_task_count_missing))
        and not any(
            issue
            in {
                "residual_forbidden_task_sets_do_not_match_exact_regions",
                "residual_task_count_forbidden_task_sets_do_not_match_exact_regions",
                "multiple_residual_regions",
                "missing_residual_region",
                "mixed_residual_partition_models",
                "missing_residual_task_count_total",
                "missing_residual_task_count_region",
                "unexpected_residual_task_count_region",
                "duplicate_residual_task_count_region",
                "duplicate_residual_active_sortie_count_region",
                "missing_residual_active_sortie_count_region",
            }
            for issue in issues
        )
    )
    gate_pass = bool(
        full_space_partition_valid
        and exact_proven_count == len(target_task_sets)
        and residual_proven
        and not issues
    )
    unique_issues = sorted(set(issues))
    return {
        "partition_candidate_gate_schema_version": "lunar_ice_bpc.b4_1.partition_candidate_gate.v1",
        "partition_candidate_gate_pass": gate_pass,
        "partition_candidate_gate_issue_codes": unique_issues,
        "partition_candidate_gate_issue_count": len(unique_issues),
        "partition_candidate_gate_exact_region_count": len(exact_best),
        "partition_candidate_gate_exact_regions_proven": exact_proven_count,
        "partition_candidate_gate_residual_proven": residual_proven,
        "partition_candidate_gate_residual_task_count_partition": bool(task_count_residual_best),
        "partition_candidate_gate_residual_task_count_observed": len(residual_task_count_observed),
        "partition_candidate_gate_full_space_partition_valid": full_space_partition_valid,
        "partition_candidate_gate_variant": next(iter(variants)) if len(variants) == 1 else "",
        "partition_candidate_gate_source_probe_json": next(iter(sources)) if len(sources) == 1 else "",
        "partition_candidate_gate_history_round": next(iter(history_rounds)) if len(history_rounds) == 1 else "",
        "partition_candidate_gate_official_certificate_allowed": False,
        "partition_candidate_gate_note": (
            "candidate partition is internally valid, but still diagnostic-only until final judge ledger integration"
            if gate_pass
            else "candidate partition is incomplete or unsafe; do not use as certificate"
        ),
    }


def _canonical_task_set(tasks: Iterable[object]) -> tuple[str, ...]:
    return tuple(sorted(str(task) for task in tasks if str(task)))


def _row_has_negative_bound(row: dict, negative_eps: float) -> bool:
    bound = _first_float(row.get("dual_bound"), row.get("best_reduced_cost"))
    return bool(bound is not None and float(bound) < -abs(float(negative_eps)))


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
        "zero_capacity_slot_truncation_enabled": bool(
            result.get("zero_capacity_slot_truncation_enabled")
        ),
        "zero_capacity_slot_truncation_original_slot_count": _first_int(
            result.get("zero_capacity_slot_truncation_original_slot_count")
        ),
        "zero_capacity_slot_truncation_effective_slot_count": _first_int(
            result.get("zero_capacity_slot_truncation_effective_slot_count")
        ),
        "zero_capacity_slot_truncation_trimmed_slot_count": _first_int(
            result.get("zero_capacity_slot_truncation_trimmed_slot_count")
        ),
        "zero_capacity_slot_truncation_first_zero_slot": _first_int(
            result.get("zero_capacity_slot_truncation_first_zero_slot")
        ),
        "slot_sequence_capacity_live_bound_enabled": bool(
            result.get("slot_sequence_capacity_live_bound_enabled")
        ),
        "slot_sequence_capacity_live_bound_tightened_slot_count": _first_int(
            result.get("slot_sequence_capacity_live_bound_tightened_slot_count")
        ),
        "slot_sequence_capacity_live_bound_by_slot": result.get(
            "slot_sequence_capacity_live_bound_by_slot"
        ),
        "tight_service_start_bounds_enabled": bool(
            result.get("tight_service_start_bounds_enabled")
        ),
        "tight_service_start_bound_count": _first_int(
            result.get("tight_service_start_bound_count")
        ),
        "tight_service_start_bound_min": _first_float(
            result.get("tight_service_start_bound_min")
        ),
        "tight_service_start_bound_max": _first_float(
            result.get("tight_service_start_bound_max")
        ),
        "tight_time_arc_big_m_enabled": bool(result.get("tight_time_arc_big_m_enabled")),
        "tight_time_arc_big_m_depot_arc_count": _first_int(
            result.get("tight_time_arc_big_m_depot_arc_count")
        ),
        "tight_time_arc_big_m_active_time_bound_count": _first_int(
            result.get("tight_time_arc_big_m_active_time_bound_count")
        ),
        "tight_time_arc_big_m_max_reduction": _first_float(
            result.get("tight_time_arc_big_m_max_reduction")
        ),
        "tight_conditional_sequence_big_m_enabled": bool(
            result.get("tight_conditional_sequence_big_m_enabled")
        ),
        "tight_conditional_sequence_big_m_count": _first_int(
            result.get("tight_conditional_sequence_big_m_count")
        ),
        "tight_conditional_sequence_big_m_max_reduction": _first_float(
            result.get("tight_conditional_sequence_big_m_max_reduction")
        ),
        "slot_service_start_y_lower_bound_enabled": bool(
            result.get("slot_service_start_y_lower_bound_enabled")
        ),
        "slot_service_start_y_lower_bound_count": _first_int(
            result.get("slot_service_start_y_lower_bound_count")
        ),
        "slot_service_start_y_lower_bound_max_lift": _first_float(
            result.get("slot_service_start_y_lower_bound_max_lift")
        ),
        "slot_service_start_y_lower_bound_min": _first_float(
            result.get("slot_service_start_y_lower_bound_min")
        ),
        "slot_service_start_y_lower_bound_max": _first_float(
            result.get("slot_service_start_y_lower_bound_max")
        ),
        "sortie_start_upper_bound": _first_float(result.get("sortie_start_upper_bound")),
        "sortie_slots_per_journey": _first_int(result.get("sortie_slots_per_journey")),
        "sortie_slot_bound_source": result.get("sortie_slot_bound_source") or "",
        "sortie_slot_horizon_count_bound": _first_int(result.get("sortie_slot_horizon_count_bound")),
        "sortie_slot_latest_start_count_bound": _first_int(result.get("sortie_slot_latest_start_count_bound")),
        "sortie_slot_min_duration_lower_bound": _first_float(result.get("sortie_slot_min_duration_lower_bound")),
        "sortie_slot_min_energy_recharge_duration_lower_bound": _first_float(
            result.get("sortie_slot_min_energy_recharge_duration_lower_bound")
        ),
        "slot_task_time_pruning_enabled": bool(result.get("slot_task_time_pruning_enabled")),
        "slot_task_time_feasible_assignment_count": _first_int(
            result.get("slot_task_time_feasible_assignment_count")
        ),
        "slot_task_time_pruned_assignment_count": _first_int(
            result.get("slot_task_time_pruned_assignment_count")
        ),
        "slot_task_time_pruned_due_count": _first_int(result.get("slot_task_time_pruned_due_count")),
        "slot_task_time_pruned_horizon_count": _first_int(
            result.get("slot_task_time_pruned_horizon_count")
        ),
        "slot_task_time_total_assignment_count": _first_int(
            result.get("slot_task_time_total_assignment_count")
        ),
        "slot_task_model_assignment_count": _first_int(
            result.get("slot_task_model_assignment_count")
        ),
        "slot_arc_support_pruning_enabled": bool(result.get("slot_arc_support_pruning_enabled")),
        "slot_arc_support_feasible_assignment_count": _first_int(
            result.get("slot_arc_support_feasible_assignment_count")
        ),
        "slot_arc_support_pruned_assignment_count": _first_int(
            result.get("slot_arc_support_pruned_assignment_count")
        ),
        "slot_arc_support_pruned_unreachable_count": _first_int(
            result.get("slot_arc_support_pruned_unreachable_count")
        ),
        "slot_arc_support_pruned_no_return_count": _first_int(
            result.get("slot_arc_support_pruned_no_return_count")
        ),
        "slot_arc_support_pruned_option_count": _first_int(
            result.get("slot_arc_support_pruned_option_count")
        ),
        "slot_arc_time_pruned_option_count": _first_int(result.get("slot_arc_time_pruned_option_count")),
        "slot_sequence_capacity_arc_pruning_enabled": bool(
            result.get("slot_sequence_capacity_arc_pruning_enabled")
        ),
        "slot_sequence_capacity_arc_pruned_option_count": _first_int(
            result.get("slot_sequence_capacity_arc_pruned_option_count")
        ),
        "slot_sequence_capacity_mtz_disabled_slot_count": _first_int(
            result.get("slot_sequence_capacity_mtz_disabled_slot_count")
        ),
        "single_task_per_active_sortie_arc_pruning_enabled": bool(
            result.get("single_task_per_active_sortie_arc_pruning_enabled")
        ),
        "single_task_per_active_sortie_arc_pruned_option_count": _first_int(
            result.get("single_task_per_active_sortie_arc_pruned_option_count")
        ),
        "single_task_per_active_sortie_mtz_disabled": bool(
            result.get("single_task_per_active_sortie_mtz_disabled")
        ),
        "mtz_connectivity_effective": bool(result.get("mtz_connectivity_effective")),
        "fixed_active_sortie_redundant_constraint_skipped_count": _first_int(
            result.get("fixed_active_sortie_redundant_constraint_skipped_count")
        ),
        "single_task_per_active_sortie_slot_visit_eq_count": _first_int(
            result.get("single_task_per_active_sortie_slot_visit_eq_count")
        ),
        "single_task_per_active_sortie_y_z_link_skipped_count": _first_int(
            result.get("single_task_per_active_sortie_y_z_link_skipped_count")
        ),
        "resource_arc_pruning_enabled": bool(result.get("resource_arc_pruning_enabled")),
        "resource_arc_pruned_option_count": _first_int(result.get("resource_arc_pruned_option_count")),
        "resource_arc_energy_pruned_option_count": _first_int(
            result.get("resource_arc_energy_pruned_option_count")
        ),
        "resource_arc_shadow_pruned_option_count": _first_int(
            result.get("resource_arc_shadow_pruned_option_count")
        ),
        "resource_arc_demand_pruned_option_count": _first_int(
            result.get("resource_arc_demand_pruned_option_count")
        ),
        "slot_task_sequence_capacity_upper_bound": _first_int(
            result.get("slot_task_sequence_capacity_upper_bound")
        ),
        "slot_task_sequence_capacity_limited_slot_count": _first_int(
            result.get("slot_task_sequence_capacity_limited_slot_count")
        ),
        "slot_task_sequence_capacity_empty_slot_count": _first_int(
            result.get("slot_task_sequence_capacity_empty_slot_count")
        ),
        "slot_task_matching_capacity_upper_bound": _first_int(
            result.get("slot_task_matching_capacity_upper_bound")
        ),
        **_single_journey_mip_start_fields(result),
        **_required_task_set_region_fields(result),
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
    selected_gap_to_zero = (
        None
        if selected_bound is None
        else round(max(0.0, -float(selected_bound)), 9)
    )
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
        "best_known_dual_bound_gap_to_zero": selected_gap_to_zero,
        "best_known_dual_bound_nonnegative": bool(
            selected_bound is not None and float(selected_bound) >= -1.0e-6
        ),
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


def _restricted_region_bound_coverage_summary(
    rows: list[dict],
    *,
    best_known_global_lb: float | None,
    negative_eps: float,
) -> dict:
    supported_rows = [
        row for row in rows if _first_float(row.get("best_known_dual_bound")) is not None
    ]
    unsupported_rows = [
        row for row in rows if _first_float(row.get("best_known_dual_bound")) is None
    ]
    nonnegative_rows = [
        row
        for row in supported_rows
        if float(_first_float(row.get("best_known_dual_bound"))) >= -abs(float(negative_eps))
    ]
    negative_rows = [
        row
        for row in supported_rows
        if float(_first_float(row.get("best_known_dual_bound"))) < -abs(float(negative_eps))
    ]
    time_limit_rows = [
        row
        for row in supported_rows
        if str(row.get("selected_bound_status") or "") == "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED"
    ]
    exact_rows = [
        row
        for row in supported_rows
        if str(row.get("selected_bound_exact_status") or "").startswith("RESTRICTED_PRICING_OPTIMAL")
        or str(row.get("selected_bound_exact_status") or "").startswith("EXACT_PRICING_OPTIMAL")
    ]
    gap = None if best_known_global_lb is None else round(max(0.0, -float(best_known_global_lb)), 9)
    source_region = ""
    source_kind = ""
    if best_known_global_lb is not None:
        worst = min(
            supported_rows,
            key=lambda row: float(_first_float(row.get("best_known_dual_bound"))),
            default=None,
        )
        if worst is not None:
            source_region = str(worst.get("region_id") or "")
            source_kind = str(worst.get("selected_bound_source") or "")
    return {
        "supported_bound_region_count": len(supported_rows),
        "unsupported_bound_region_count": len(unsupported_rows),
        "nonnegative_bound_region_count": len(nonnegative_rows),
        "negative_bound_region_count": len(negative_rows),
        "time_limit_bound_region_count": len(time_limit_rows),
        "exact_bound_region_count": len(exact_rows),
        "region_bound_gap_to_zero": gap,
        "region_bound_gap_source_region_id": source_region,
        "region_bound_gap_source": source_kind,
        "region_bound_diagnostic_complete_for_listed_regions": bool(
            rows and len(unsupported_rows) == 0
        ),
        "region_bound_can_certify_if_partition": bool(
            rows
            and len(unsupported_rows) == 0
            and len(negative_rows) == 0
            and best_known_global_lb is not None
            and float(best_known_global_lb) >= -abs(float(negative_eps))
        ),
        "region_bound_official_certificate_allowed": False,
    }


def _restricted_region_partition_audit(
    diagnostic: dict,
    rows: list[dict],
    *,
    negative_eps: float,
) -> dict:
    negatives = list(diagnostic.get("harvested_negatives") or [])
    observed_prefixes = sorted(
        {
            _first_int(row.get("forbidden_task_set_count"))
            for row in rows
            if _first_int(row.get("forbidden_task_set_count")) > 0
        }
    )
    deepest_prefix = max(observed_prefixes, default=0)
    residual_rows = [
        row
        for row in rows
        if _first_int(row.get("forbidden_task_set_count")) == deepest_prefix
    ]
    residual_row = residual_rows[0] if residual_rows else {}
    residual_bound = _first_float(residual_row.get("best_known_dual_bound"))
    required_exact_task_set_regions = max(0, deepest_prefix)
    observed_exact_task_set_regions = 0
    missing_exact_task_set_regions = max(
        0,
        required_exact_task_set_regions - observed_exact_task_set_regions,
    )
    residual_region_required = bool(required_exact_task_set_regions > 0)
    residual_region_observed = bool(residual_rows)
    missing_residual_region_count = 0 if (not residual_region_required or residual_region_observed) else 1
    prefix_regions_nested = bool(len(observed_prefixes) > 1)
    prefix_regions_disjoint = bool(len(observed_prefixes) <= 1)
    residual_nonnegative = bool(
        residual_bound is not None and float(residual_bound) >= -abs(float(negative_eps))
    )
    issues: list[str] = []
    if prefix_regions_nested:
        issues.append("prefix_no_good_regions_are_nested_not_disjoint")
    if missing_exact_task_set_regions:
        issues.append("missing_exact_task_set_region_proofs")
    if missing_residual_region_count:
        issues.append("missing_final_residual_region_proof")
    if residual_region_required and residual_region_observed and not residual_nonnegative:
        issues.append("final_residual_region_bound_negative_or_missing")
    if negatives and not rows:
        issues.append("no_restricted_region_rows")
    can_certify_if_partition = bool(
        required_exact_task_set_regions > 0
        and missing_exact_task_set_regions == 0
        and missing_residual_region_count == 0
        and residual_nonnegative
        and prefix_regions_disjoint
        and not issues
    )
    return {
        "region_partition_audit_schema_version": "lunar_ice_bpc.b4_1_region_partition_audit.v1",
        "region_partition_family": "prefix_no_good_residual_regions",
        "region_partition_required_model": "exact_task_set_regions_plus_final_residual",
        "region_partition_observed_prefix_count": len(observed_prefixes),
        "region_partition_observed_prefixes": observed_prefixes,
        "region_partition_prefix_regions_nested": prefix_regions_nested,
        "region_partition_regions_disjoint": prefix_regions_disjoint,
        "region_partition_covers_full_space": False,
        "region_partition_complete": False,
        "region_partition_can_certify": False,
        "region_partition_can_certify_if_all_missing_parts_proven": can_certify_if_partition,
        "region_partition_required_exact_task_set_region_count": required_exact_task_set_regions,
        "region_partition_observed_exact_task_set_region_count": observed_exact_task_set_regions,
        "region_partition_missing_exact_task_set_region_count": missing_exact_task_set_regions,
        "region_partition_residual_region_required": residual_region_required,
        "region_partition_residual_region_observed": residual_region_observed,
        "region_partition_missing_residual_region_count": missing_residual_region_count,
        "region_partition_residual_region_id": str(residual_row.get("region_id") or ""),
        "region_partition_residual_best_known_dual_bound": residual_bound,
        "region_partition_residual_bound_nonnegative": residual_nonnegative,
        "region_partition_issue_codes": issues,
        "region_partition_note": (
            "Prefix no-good rows are nested residual spaces. A full certificate would need "
            "separate exact-task-set region proofs for each excluded task set plus a final "
            "residual no-negative proof under the same true dual."
        ),
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
            f"- Dual-search audit rows: `{diagnostics.get('dual_search_diagnostic_row_count', 0)}`；"
            f"false-positive rows `{diagnostics.get('candidate_search_false_positive_row_count', 0)}`；"
            f"miss rows `{diagnostics.get('true_negative_candidate_search_miss_row_count', 0)}`；"
            f"mean false+ `{diagnostics.get('mean_candidate_search_false_positive_rate')}`；"
            f"mean miss `{diagnostics.get('mean_true_negative_candidate_search_miss_rate')}`。",
            f"- Partition candidate audit rows: `{diagnostics.get('partition_candidate_audit_row_count', 0)}`；"
            f"gate pass `{diagnostics.get('partition_candidate_gate_pass_count', 0)}`；"
            f"gate fail `{diagnostics.get('partition_candidate_gate_fail_count', 0)}`；"
            f"candidate no-negative `{diagnostics.get('partition_candidate_can_certify_no_negative_count', 0)}`；"
            f"redline fail `{diagnostics.get('partition_candidate_redline_fail_count', 0)}`。",
            f"- Partition candidate top issue: `{diagnostics.get('partition_candidate_top_issue') or 'none'}`；"
            f"issue counts `{_compact_markdown_json(diagnostics.get('partition_candidate_issue_counts') or {})}`。",
            f"- Partition negative regions: `{diagnostics.get('partition_negative_region_count', 0)}`；"
            f"payload available `{diagnostics.get('partition_negative_payload_available_count', 0)}`；"
            f"best negative RC `{diagnostics.get('partition_best_negative_rc')}`。",
        f"- Partition negative relation: already active `{diagnostics.get('partition_negative_already_active_count', 0)}`；"
        f"replacement `{diagnostics.get('partition_negative_replacement_task_set_count', 0)}`；"
        f"new task-set `{diagnostics.get('partition_negative_new_task_set_count', 0)}`。",
        f"- Partition model size: max variables `{diagnostics.get('partition_region_variable_count_max', 0)}`；"
        f"max constraints `{diagnostics.get('partition_region_constraint_count_max', 0)}`；"
        f"max mean variables `{diagnostics.get('partition_region_variable_count_mean_max')}`；"
        f"max mean constraints `{diagnostics.get('partition_region_constraint_count_mean_max')}`。",
        f"- Partition slot pruning: max feasible assignments "
        f"`{diagnostics.get('partition_region_slot_task_time_feasible_assignment_count_max', 0)}`；"
        f"pruned assignments sum "
        f"`{diagnostics.get('partition_region_slot_task_time_pruned_assignment_count_sum', 0)}`；"
        f"pruned arc options sum "
        f"`{diagnostics.get('partition_region_slot_arc_time_pruned_option_count_sum', 0)}`。",
        f"- Partition dual/active scope mismatch rows: `{diagnostics.get('partition_dual_scope_mismatch_count', 0)}`；"
        f"max active-pool-after-dual delta `{diagnostics.get('partition_active_pool_after_dual_delta_max', 0)}`；"
        f"negative RC audit fail `{diagnostics.get('partition_negative_rc_audit_fail_count', 0)}`。",
        f"- Partition region MIP-start: enabled `{diagnostics.get('partition_region_mip_start_enabled_count', 0)}`；"
        f"OK `{diagnostics.get('partition_region_mip_start_ok_count', 0)}`；"
        f"exact OK `{diagnostics.get('partition_exact_region_mip_start_ok_count', 0)}`；"
        f"residual OK `{diagnostics.get('partition_residual_region_mip_start_ok_count', 0)}`。",
        f"- Residual task-count partition: enabled rows `{diagnostics.get('residual_task_count_partition_enabled_count', 0)}`；"
        f"expected `{diagnostics.get('residual_task_count_region_expected_count')}`；"
        f"observed `{diagnostics.get('residual_task_count_region_observed_count')}`；"
        f"proven `{diagnostics.get('residual_task_count_region_proven_count')}`；"
        f"incomplete `{diagnostics.get('residual_task_count_region_incomplete_count')}`；"
        f"negative `{diagnostics.get('residual_task_count_region_negative_count')}`；"
        f"missing `{diagnostics.get('residual_task_count_region_missing_count')}`。",
        f"- Partition refreshed dual rows: `{diagnostics.get('partition_refreshed_dual_row_count', 0)}`；"
        f"refresh negative count `{diagnostics.get('partition_dual_refresh_negative_count', 0)}`；"
        f"refresh min RC `{diagnostics.get('partition_dual_refresh_min_rc')}`。",
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
    labeling_final_judge_exact_harvest_target: int | None,
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
            labeling_final_judge_exact_harvest_target=(
                labeling_final_judge_exact_harvest_target
                if mode == B41_STAGE_A_B4V2_HARVEST
                else None
            ),
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
            labeling_final_judge_exact_harvest_target=labeling_final_judge_exact_harvest_target,
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
    final_judge = raw.get("final_judge") if isinstance(raw.get("final_judge"), dict) else {}
    if not final_judge and isinstance(root_node.get("final_judge"), dict):
        final_judge = root_node["final_judge"]
    root_history = root_node.get("history") if isinstance(root_node.get("history"), list) else []
    root_last = root_history[-1] if root_history and isinstance(root_history[-1], dict) else {}
    last_worker = _last_worker_payload(history)
    if not last_worker and root_last:
        last_worker = root_last
    tail_payload = last_worker.get("tail_dual_stabilization") if isinstance(last_worker, dict) else {}
    if not isinstance(tail_payload, dict):
        tail_payload = {}
    if not tail_payload and _bool_value(raw.get("tail_dual_stabilization_enabled")):
        tail_payload = {
            "tail_dual_stabilization_enabled": True,
            "worker_dual_only": root_last.get("worker_dual_only"),
            "true_dual_rc_recomputed": root_last.get("true_dual_rc_recomputed"),
            "official_dual_source": _first_str(
                root_last.get("official_dual_source"),
                final_judge.get("official_pricing_dual_source"),
            ),
            "tail_dual_no_column_can_certify": root_last.get("tail_dual_no_column_can_certify"),
        }
    tail_fields = _tail_dual_safety_fields(last_worker, tail_payload)
    dual_search_fields = _dual_search_diagnostic_fields(last_worker)
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
        "b4_1_harvesting_enabled": bool(
            mode == B41_STAGE_A_B4V2_HARVEST
            or (stage != "A" and _probe_has_final_judge_harvest_telemetry(final_judge))
        ),
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
        "variable_count": _first_int(
            final_judge.get("variable_count"),
            root_last.get("variable_count"),
            raw.get("variable_count"),
        ),
        "constraint_count": _first_int(
            final_judge.get("constraint_count"),
            root_last.get("constraint_count"),
            raw.get("constraint_count"),
        ),
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
        "labeling_final_judge_exact_harvest_target": _first_int(
            final_judge.get("labeling_final_judge_exact_harvest_target"),
            raw.get("labeling_final_judge_exact_harvest_target"),
            root_last.get("labeling_final_judge_exact_harvest_target"),
        ),
        "labeling_final_judge_exact_harvest_target_source": _first_str(
            final_judge.get("labeling_final_judge_exact_harvest_target_source"),
            root_last.get("labeling_final_judge_exact_harvest_target_source"),
        ),
        "exact_negative_harvest_target": _first_int(
            final_judge.get("exact_negative_harvest_target"),
            root_last.get("exact_negative_harvest_target"),
        ),
        "exact_negative_harvest_candidate_count": _first_int(
            final_judge.get("exact_negative_harvest_candidate_count"),
            root_last.get("exact_negative_harvest_candidate_count"),
        ),
        "exact_negative_harvest_selected_count": _first_int(
            final_judge.get("exact_negative_harvest_selected_count"),
            root_last.get("exact_negative_harvest_selected_count"),
        ),
        "exact_negative_harvest_selected_new_task_set_count": _first_int(
            final_judge.get("exact_negative_harvest_selected_new_task_set_count"),
            root_last.get("exact_negative_harvest_selected_new_task_set_count"),
        ),
        "exact_negative_harvest_selected_replacement_task_set_count": _first_int(
            final_judge.get("exact_negative_harvest_selected_replacement_task_set_count"),
            root_last.get("exact_negative_harvest_selected_replacement_task_set_count"),
        ),
        "exact_negative_harvest_selection_policy": _first_str(
            final_judge.get("exact_negative_harvest_selection_policy"),
            root_last.get("exact_negative_harvest_selection_policy"),
        ),
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
        "compact_pricing_phase": final_judge.get("compact_pricing_phase"),
        "route_template_pre_harvest_enabled": bool(final_judge.get("route_template_pre_harvest_enabled")),
        "route_template_pre_harvest_status": final_judge.get("route_template_pre_harvest_status"),
        "route_template_pre_harvest_target": final_judge.get("route_template_pre_harvest_target"),
        "route_template_pre_harvest_time_cap_sec": final_judge.get(
            "route_template_pre_harvest_time_cap_sec"
        ),
        "route_template_pre_harvest_max_direct_tasks": final_judge.get(
            "route_template_pre_harvest_max_direct_tasks"
        ),
        "route_template_pre_harvest_max_active_seeds": final_judge.get(
            "route_template_pre_harvest_max_active_seeds"
        ),
        "route_template_pre_harvest_seed_strategy": final_judge.get(
            "route_template_pre_harvest_seed_strategy"
        ),
        "route_template_pre_harvest_neighborhood_enabled": final_judge.get(
            "route_template_pre_harvest_neighborhood_enabled"
        ),
        "route_template_pre_harvest_max_neighborhood_seeds": final_judge.get(
            "route_template_pre_harvest_max_neighborhood_seeds"
        ),
        "route_template_pre_harvest_max_candidate_sets": final_judge.get(
            "route_template_pre_harvest_max_candidate_sets"
        ),
        "route_template_pre_harvest_seed_count": final_judge.get("route_template_pre_harvest_seed_count"),
        "route_template_pre_harvest_candidate_round_count": final_judge.get(
            "route_template_pre_harvest_candidate_round_count"
        ),
        "route_template_pre_harvest_candidate_round_limit": final_judge.get(
            "route_template_pre_harvest_candidate_round_limit"
        ),
        "route_template_pre_harvest_candidate_negative_count": final_judge.get(
            "route_template_pre_harvest_candidate_negative_count"
        ),
        "route_template_pre_harvest_selected_count": final_judge.get(
            "route_template_pre_harvest_selected_count"
        ),
        "route_template_pre_harvest_selected_new_task_set_count": final_judge.get(
            "route_template_pre_harvest_selected_new_task_set_count"
        ),
        "route_template_pre_harvest_selected_replacement_task_set_count": final_judge.get(
            "route_template_pre_harvest_selected_replacement_task_set_count"
        ),
        "route_template_pre_harvest_pricing_wall_time_sec": final_judge.get(
            "route_template_pre_harvest_pricing_wall_time_sec"
        ),
        "route_template_pre_harvest_fallback_enabled": final_judge.get(
            "route_template_pre_harvest_fallback_enabled"
        ),
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
        **dual_search_fields,
        "global_remaining_rc_lb": final_judge.get("global_remaining_rc_lb"),
        "frontier_coverage_complete": bool(final_judge.get("global_remaining_rc_lb_coverage_complete")),
        "frontier_unsupported_region_count": final_judge.get("frontier_unsupported_region_count"),
        "pending_complete_min_rc": final_judge.get("pending_complete_min_rc"),
        "pricing_proof_kind": final_judge.get("pricing_proof_kind"),
        "compact_final_judge_profile": final_judge.get("compact_final_judge_profile"),
        "compact_final_judge_formulation_profile": final_judge.get("compact_final_judge_formulation_profile"),
        "compact_final_judge_phase_mode": final_judge.get("compact_final_judge_phase_mode"),
        "objective_bound_no_negative_cutoff_enabled": bool(
            final_judge.get("objective_bound_no_negative_cutoff_enabled")
        ),
        "objective_bound_no_negative_cutoff_value": final_judge.get(
            "objective_bound_no_negative_cutoff_value"
        ),
        "objective_bound_no_negative_cutoff_can_certify": bool(
            final_judge.get("objective_bound_no_negative_cutoff_can_certify")
        ),
        "zero_capacity_slot_truncation_enabled": bool(
            final_judge.get("zero_capacity_slot_truncation_enabled")
        ),
        "zero_capacity_slot_truncation_original_slot_count": _first_int(
            final_judge.get("zero_capacity_slot_truncation_original_slot_count")
        ),
        "zero_capacity_slot_truncation_effective_slot_count": _first_int(
            final_judge.get("zero_capacity_slot_truncation_effective_slot_count")
        ),
        "zero_capacity_slot_truncation_trimmed_slot_count": _first_int(
            final_judge.get("zero_capacity_slot_truncation_trimmed_slot_count")
        ),
        "zero_capacity_slot_truncation_first_zero_slot": _first_int(
            final_judge.get("zero_capacity_slot_truncation_first_zero_slot")
        ),
        "slot_sequence_capacity_live_bound_enabled": bool(
            final_judge.get("slot_sequence_capacity_live_bound_enabled")
        ),
        "slot_sequence_capacity_live_bound_tightened_slot_count": _first_int(
            final_judge.get("slot_sequence_capacity_live_bound_tightened_slot_count")
        ),
        "slot_sequence_capacity_live_bound_by_slot": final_judge.get(
            "slot_sequence_capacity_live_bound_by_slot"
        ),
        "tight_service_start_bounds_enabled": bool(
            final_judge.get("tight_service_start_bounds_enabled")
        ),
        "tight_service_start_bound_count": _first_int(
            final_judge.get("tight_service_start_bound_count")
        ),
        "tight_service_start_bound_min": _first_float(
            final_judge.get("tight_service_start_bound_min")
        ),
        "tight_service_start_bound_max": _first_float(
            final_judge.get("tight_service_start_bound_max")
        ),
        "tight_time_arc_big_m_enabled": bool(final_judge.get("tight_time_arc_big_m_enabled")),
        "tight_time_arc_big_m_depot_arc_count": _first_int(
            final_judge.get("tight_time_arc_big_m_depot_arc_count")
        ),
        "tight_time_arc_big_m_active_time_bound_count": _first_int(
            final_judge.get("tight_time_arc_big_m_active_time_bound_count")
        ),
        "tight_time_arc_big_m_max_reduction": _first_float(
            final_judge.get("tight_time_arc_big_m_max_reduction")
        ),
        "tight_conditional_sequence_big_m_enabled": bool(
            final_judge.get("tight_conditional_sequence_big_m_enabled")
        ),
        "tight_conditional_sequence_big_m_count": _first_int(
            final_judge.get("tight_conditional_sequence_big_m_count")
        ),
        "tight_conditional_sequence_big_m_max_reduction": _first_float(
            final_judge.get("tight_conditional_sequence_big_m_max_reduction")
        ),
        "slot_service_start_y_lower_bound_enabled": bool(
            final_judge.get("slot_service_start_y_lower_bound_enabled")
        ),
        "slot_service_start_y_lower_bound_count": _first_int(
            final_judge.get("slot_service_start_y_lower_bound_count")
        ),
        "slot_service_start_y_lower_bound_max_lift": _first_float(
            final_judge.get("slot_service_start_y_lower_bound_max_lift")
        ),
        "slot_service_start_y_lower_bound_min": _first_float(
            final_judge.get("slot_service_start_y_lower_bound_min")
        ),
        "slot_service_start_y_lower_bound_max": _first_float(
            final_judge.get("slot_service_start_y_lower_bound_max")
        ),
        "sortie_start_upper_bound": _first_float(final_judge.get("sortie_start_upper_bound")),
        "sortie_slots_per_journey": _first_int(final_judge.get("sortie_slots_per_journey")),
        "sortie_slot_bound_source": final_judge.get("sortie_slot_bound_source") or "",
        "sortie_slot_horizon_count_bound": _first_int(final_judge.get("sortie_slot_horizon_count_bound")),
        "sortie_slot_latest_start_count_bound": _first_int(
            final_judge.get("sortie_slot_latest_start_count_bound")
        ),
        "sortie_slot_min_duration_lower_bound": _first_float(
            final_judge.get("sortie_slot_min_duration_lower_bound")
        ),
        "sortie_slot_min_energy_recharge_duration_lower_bound": _first_float(
            final_judge.get("sortie_slot_min_energy_recharge_duration_lower_bound")
        ),
        "slot_task_time_pruning_enabled": bool(final_judge.get("slot_task_time_pruning_enabled")),
        "slot_task_time_feasible_assignment_count": final_judge.get(
            "slot_task_time_feasible_assignment_count"
        ),
        "slot_task_time_pruned_assignment_count": final_judge.get(
            "slot_task_time_pruned_assignment_count"
        ),
        "slot_task_time_pruned_due_count": final_judge.get("slot_task_time_pruned_due_count"),
        "slot_task_time_pruned_horizon_count": final_judge.get(
            "slot_task_time_pruned_horizon_count"
        ),
        "slot_task_time_total_assignment_count": final_judge.get("slot_task_time_total_assignment_count"),
        "slot_task_time_original_total_assignment_count": final_judge.get(
            "slot_task_time_original_total_assignment_count"
        ),
        "slot_task_model_assignment_count": final_judge.get("slot_task_model_assignment_count"),
        "slot_arc_support_pruning_enabled": bool(final_judge.get("slot_arc_support_pruning_enabled")),
        "slot_arc_support_feasible_assignment_count": final_judge.get(
            "slot_arc_support_feasible_assignment_count"
        ),
        "slot_arc_support_pruned_assignment_count": final_judge.get(
            "slot_arc_support_pruned_assignment_count"
        ),
        "slot_arc_support_pruned_unreachable_count": final_judge.get(
            "slot_arc_support_pruned_unreachable_count"
        ),
        "slot_arc_support_pruned_no_return_count": final_judge.get(
            "slot_arc_support_pruned_no_return_count"
        ),
        "slot_arc_support_pruned_option_count": final_judge.get(
            "slot_arc_support_pruned_option_count"
        ),
        "slot_arc_time_pruned_option_count": final_judge.get("slot_arc_time_pruned_option_count"),
        "slot_sequence_capacity_arc_pruning_enabled": bool(
            final_judge.get("slot_sequence_capacity_arc_pruning_enabled")
        ),
        "slot_sequence_capacity_arc_pruned_option_count": final_judge.get(
            "slot_sequence_capacity_arc_pruned_option_count"
        ),
        "slot_sequence_capacity_mtz_disabled_slot_count": final_judge.get(
            "slot_sequence_capacity_mtz_disabled_slot_count"
        ),
        "single_task_per_active_sortie_arc_pruning_enabled": bool(
            final_judge.get("single_task_per_active_sortie_arc_pruning_enabled")
        ),
        "single_task_per_active_sortie_arc_pruned_option_count": final_judge.get(
            "single_task_per_active_sortie_arc_pruned_option_count"
        ),
        "single_task_per_active_sortie_mtz_disabled": bool(
            final_judge.get("single_task_per_active_sortie_mtz_disabled")
        ),
        "mtz_connectivity_effective": bool(final_judge.get("mtz_connectivity_effective")),
        "fixed_active_sortie_redundant_constraint_skipped_count": final_judge.get(
            "fixed_active_sortie_redundant_constraint_skipped_count"
        ),
        "single_task_per_active_sortie_slot_visit_eq_count": final_judge.get(
            "single_task_per_active_sortie_slot_visit_eq_count"
        ),
        "single_task_per_active_sortie_y_z_link_skipped_count": final_judge.get(
            "single_task_per_active_sortie_y_z_link_skipped_count"
        ),
        "resource_arc_pruning_enabled": bool(final_judge.get("resource_arc_pruning_enabled")),
        "resource_arc_pruned_option_count": final_judge.get("resource_arc_pruned_option_count"),
        "resource_arc_energy_pruned_option_count": final_judge.get(
            "resource_arc_energy_pruned_option_count"
        ),
        "resource_arc_shadow_pruned_option_count": final_judge.get(
            "resource_arc_shadow_pruned_option_count"
        ),
        "resource_arc_demand_pruned_option_count": final_judge.get(
            "resource_arc_demand_pruned_option_count"
        ),
        **_dual_task_slot_full_space_lower_bound_fields(final_judge),
        **_single_journey_mip_start_fields(final_judge),
        **_required_task_set_region_fields(final_judge),
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
        "candidate_search_false_positive_rate": row.get("candidate_search_false_positive_rate", ""),
        "true_negative_candidate_search_miss_rate": row.get("true_negative_candidate_search_miss_rate", ""),
        "candidate_search_false_positive_row_count": _first_int(
            row.get("candidate_search_false_positive_row_count"),
            len(row.get("candidate_search_false_positive_rows") or [])
            if isinstance(row.get("candidate_search_false_positive_rows"), list)
            else None,
        ),
        "true_negative_candidate_search_miss_row_count": _first_int(
            row.get("true_negative_candidate_search_miss_row_count"),
            len(row.get("true_negative_candidate_search_miss_rows") or [])
            if isinstance(row.get("true_negative_candidate_search_miss_rows"), list)
            else None,
        ),
        "candidate_search_negative_true_nonnegative_count": row.get(
            "candidate_search_negative_true_nonnegative_count",
            "",
        ),
        "true_negative_candidate_search_nonnegative_count": row.get(
            "true_negative_candidate_search_nonnegative_count",
            "",
        ),
        "candidate_search_dual_matches_true_dual": row.get("candidate_search_dual_matches_true_dual", ""),
        "candidate_search_rc_recomputed_under_true_dual": row.get(
            "candidate_search_rc_recomputed_under_true_dual",
            "",
        ),
        "worker_true_dual_candidate_audit_pass": row.get("worker_true_dual_candidate_audit_pass", ""),
        "worker_candidate_universe_task_set_count": row.get("worker_candidate_universe_task_set_count", ""),
        "worker_generated_column_task_set_count": row.get("worker_generated_column_task_set_count", ""),
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
        "sortie_slots_per_journey": row.get("sortie_slots_per_journey"),
        "sortie_slot_bound_source": row.get("sortie_slot_bound_source"),
        "sortie_slot_horizon_count_bound": row.get("sortie_slot_horizon_count_bound"),
        "sortie_slot_latest_start_count_bound": row.get("sortie_slot_latest_start_count_bound"),
        "sortie_slot_min_duration_lower_bound": row.get("sortie_slot_min_duration_lower_bound"),
        "sortie_slot_min_energy_recharge_duration_lower_bound": row.get(
            "sortie_slot_min_energy_recharge_duration_lower_bound"
        ),
        "slot_task_time_pruning_enabled": bool(row.get("slot_task_time_pruning_enabled")),
        "slot_task_time_feasible_assignment_count": row.get("slot_task_time_feasible_assignment_count"),
        "slot_task_time_pruned_assignment_count": row.get("slot_task_time_pruned_assignment_count"),
        "slot_task_time_pruned_due_count": row.get("slot_task_time_pruned_due_count"),
        "slot_task_time_pruned_horizon_count": row.get("slot_task_time_pruned_horizon_count"),
        "slot_task_time_total_assignment_count": row.get("slot_task_time_total_assignment_count"),
        "slot_task_model_assignment_count": row.get("slot_task_model_assignment_count"),
        "slot_arc_support_pruning_enabled": bool(row.get("slot_arc_support_pruning_enabled")),
        "slot_arc_support_feasible_assignment_count": row.get(
            "slot_arc_support_feasible_assignment_count"
        ),
        "slot_arc_support_pruned_assignment_count": row.get(
            "slot_arc_support_pruned_assignment_count"
        ),
        "slot_arc_support_pruned_unreachable_count": row.get(
            "slot_arc_support_pruned_unreachable_count"
        ),
        "slot_arc_support_pruned_no_return_count": row.get(
            "slot_arc_support_pruned_no_return_count"
        ),
        "slot_arc_support_pruned_option_count": row.get("slot_arc_support_pruned_option_count"),
        "slot_arc_time_pruned_option_count": row.get("slot_arc_time_pruned_option_count"),
        "resource_arc_pruning_enabled": bool(row.get("resource_arc_pruning_enabled")),
        "resource_arc_pruned_option_count": row.get("resource_arc_pruned_option_count"),
        "resource_arc_energy_pruned_option_count": row.get("resource_arc_energy_pruned_option_count"),
        "resource_arc_shadow_pruned_option_count": row.get("resource_arc_shadow_pruned_option_count"),
        "resource_arc_demand_pruned_option_count": row.get("resource_arc_demand_pruned_option_count"),
        **_dual_task_slot_full_space_lower_bound_fields(row),
        **_single_journey_mip_start_fields(row),
        **_required_task_set_region_fields(row),
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
            "objective_bound_no_negative_cutoff_enabled": bool(
                final_judge.get("objective_bound_no_negative_cutoff_enabled")
            ),
            "objective_bound_no_negative_cutoff_value": final_judge.get(
                "objective_bound_no_negative_cutoff_value"
            ),
            "objective_bound_no_negative_cutoff_can_certify": bool(
                final_judge.get("objective_bound_no_negative_cutoff_can_certify")
            ),
            "zero_capacity_slot_truncation_enabled": bool(
                final_judge.get("zero_capacity_slot_truncation_enabled")
            ),
            "zero_capacity_slot_truncation_original_slot_count": final_judge.get(
                "zero_capacity_slot_truncation_original_slot_count"
            ),
            "zero_capacity_slot_truncation_effective_slot_count": final_judge.get(
                "zero_capacity_slot_truncation_effective_slot_count"
            ),
            "zero_capacity_slot_truncation_trimmed_slot_count": final_judge.get(
                "zero_capacity_slot_truncation_trimmed_slot_count"
            ),
            "zero_capacity_slot_truncation_first_zero_slot": final_judge.get(
                "zero_capacity_slot_truncation_first_zero_slot"
            ),
            "slot_sequence_capacity_live_bound_enabled": bool(
                final_judge.get("slot_sequence_capacity_live_bound_enabled")
            ),
            "slot_sequence_capacity_live_bound_tightened_slot_count": final_judge.get(
                "slot_sequence_capacity_live_bound_tightened_slot_count"
            ),
            "slot_sequence_capacity_live_bound_by_slot": final_judge.get(
                "slot_sequence_capacity_live_bound_by_slot"
            ),
            "tight_service_start_bounds_enabled": bool(
                final_judge.get("tight_service_start_bounds_enabled")
            ),
            "tight_service_start_bound_count": final_judge.get(
                "tight_service_start_bound_count"
            ),
            "tight_service_start_bound_min": final_judge.get(
                "tight_service_start_bound_min"
            ),
            "tight_service_start_bound_max": final_judge.get(
                "tight_service_start_bound_max"
            ),
            "tight_time_arc_big_m_enabled": bool(
                final_judge.get("tight_time_arc_big_m_enabled")
            ),
            "tight_time_arc_big_m_depot_arc_count": final_judge.get(
                "tight_time_arc_big_m_depot_arc_count"
            ),
            "tight_time_arc_big_m_active_time_bound_count": final_judge.get(
                "tight_time_arc_big_m_active_time_bound_count"
            ),
            "tight_time_arc_big_m_max_reduction": final_judge.get(
                "tight_time_arc_big_m_max_reduction"
            ),
            "tight_conditional_sequence_big_m_enabled": bool(
                final_judge.get("tight_conditional_sequence_big_m_enabled")
            ),
            "tight_conditional_sequence_big_m_count": final_judge.get(
                "tight_conditional_sequence_big_m_count"
            ),
            "tight_conditional_sequence_big_m_max_reduction": final_judge.get(
                "tight_conditional_sequence_big_m_max_reduction"
            ),
            "slot_service_start_y_lower_bound_enabled": bool(
                final_judge.get("slot_service_start_y_lower_bound_enabled")
            ),
            "slot_service_start_y_lower_bound_count": final_judge.get(
                "slot_service_start_y_lower_bound_count"
            ),
            "slot_service_start_y_lower_bound_max_lift": final_judge.get(
                "slot_service_start_y_lower_bound_max_lift"
            ),
            "slot_service_start_y_lower_bound_min": final_judge.get(
                "slot_service_start_y_lower_bound_min"
            ),
            "slot_service_start_y_lower_bound_max": final_judge.get(
                "slot_service_start_y_lower_bound_max"
            ),
            "sortie_start_upper_bound": final_judge.get("sortie_start_upper_bound"),
            "sortie_slots_per_journey": final_judge.get("sortie_slots_per_journey"),
            "sortie_slot_bound_source": final_judge.get("sortie_slot_bound_source"),
            "sortie_slot_horizon_count_bound": final_judge.get("sortie_slot_horizon_count_bound"),
            "sortie_slot_latest_start_count_bound": final_judge.get("sortie_slot_latest_start_count_bound"),
            "sortie_slot_min_duration_lower_bound": final_judge.get("sortie_slot_min_duration_lower_bound"),
            "sortie_slot_min_energy_recharge_duration_lower_bound": final_judge.get(
                "sortie_slot_min_energy_recharge_duration_lower_bound"
            ),
            "slot_task_time_pruning_enabled": bool(final_judge.get("slot_task_time_pruning_enabled")),
            "slot_task_time_feasible_assignment_count": final_judge.get(
                "slot_task_time_feasible_assignment_count"
            ),
            "slot_task_time_pruned_assignment_count": final_judge.get(
                "slot_task_time_pruned_assignment_count"
            ),
            "slot_task_time_pruned_due_count": final_judge.get("slot_task_time_pruned_due_count"),
            "slot_task_time_pruned_horizon_count": final_judge.get(
                "slot_task_time_pruned_horizon_count"
            ),
            "slot_task_time_total_assignment_count": final_judge.get(
                "slot_task_time_total_assignment_count"
            ),
            "slot_task_model_assignment_count": final_judge.get("slot_task_model_assignment_count"),
            "slot_arc_support_pruning_enabled": bool(
                final_judge.get("slot_arc_support_pruning_enabled")
            ),
            "slot_arc_support_feasible_assignment_count": final_judge.get(
                "slot_arc_support_feasible_assignment_count"
            ),
            "slot_arc_support_pruned_assignment_count": final_judge.get(
                "slot_arc_support_pruned_assignment_count"
            ),
            "slot_arc_support_pruned_unreachable_count": final_judge.get(
                "slot_arc_support_pruned_unreachable_count"
            ),
            "slot_arc_support_pruned_no_return_count": final_judge.get(
                "slot_arc_support_pruned_no_return_count"
            ),
            "slot_arc_support_pruned_option_count": final_judge.get(
                "slot_arc_support_pruned_option_count"
            ),
            "slot_arc_time_pruned_option_count": final_judge.get(
                "slot_arc_time_pruned_option_count"
            ),
            "single_task_per_active_sortie_arc_pruning_enabled": bool(
                final_judge.get("single_task_per_active_sortie_arc_pruning_enabled")
            ),
            "single_task_per_active_sortie_arc_pruned_option_count": final_judge.get(
                "single_task_per_active_sortie_arc_pruned_option_count"
            ),
            "single_task_per_active_sortie_mtz_disabled": bool(
                final_judge.get("single_task_per_active_sortie_mtz_disabled")
            ),
            "mtz_connectivity_effective": bool(final_judge.get("mtz_connectivity_effective")),
            "fixed_active_sortie_redundant_constraint_skipped_count": final_judge.get(
                "fixed_active_sortie_redundant_constraint_skipped_count"
            ),
            "single_task_per_active_sortie_slot_visit_eq_count": final_judge.get(
                "single_task_per_active_sortie_slot_visit_eq_count"
            ),
            "single_task_per_active_sortie_y_z_link_skipped_count": final_judge.get(
                "single_task_per_active_sortie_y_z_link_skipped_count"
            ),
            "resource_arc_pruning_enabled": bool(final_judge.get("resource_arc_pruning_enabled")),
            "resource_arc_pruned_option_count": final_judge.get("resource_arc_pruned_option_count"),
            "resource_arc_energy_pruned_option_count": final_judge.get(
                "resource_arc_energy_pruned_option_count"
            ),
            "resource_arc_shadow_pruned_option_count": final_judge.get(
                "resource_arc_shadow_pruned_option_count"
            ),
            "resource_arc_demand_pruned_option_count": final_judge.get(
                "resource_arc_demand_pruned_option_count"
            ),
            **_single_journey_mip_start_fields(final_judge),
            **_required_task_set_region_fields(final_judge),
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
            "labeling_final_judge_exact_harvest_target": _first_int(
                final_judge.get("labeling_final_judge_exact_harvest_target"),
                payload.get("labeling_final_judge_exact_harvest_target"),
                (payload.get("config") or {}).get("labeling_final_judge_exact_harvest_target")
                if isinstance(payload.get("config"), dict)
                else None,
            ),
            "labeling_final_judge_exact_harvest_target_source": _first_str(
                final_judge.get("labeling_final_judge_exact_harvest_target_source"),
            ),
            "exact_negative_harvest_target": _first_int(
                final_judge.get("exact_negative_harvest_target"),
                payload.get("exact_negative_harvest_target"),
            ),
            "exact_negative_harvest_candidate_count": _first_int(
                final_judge.get("exact_negative_harvest_candidate_count"),
                payload.get("exact_negative_harvest_candidate_count"),
            ),
            "exact_negative_harvest_selected_count": _first_int(
                final_judge.get("exact_negative_harvest_selected_count"),
                payload.get("exact_negative_harvest_selected_count"),
            ),
            "exact_negative_harvest_selected_new_task_set_count": _first_int(
                final_judge.get("exact_negative_harvest_selected_new_task_set_count"),
                payload.get("exact_negative_harvest_selected_new_task_set_count"),
            ),
            "exact_negative_harvest_selected_replacement_task_set_count": _first_int(
                final_judge.get("exact_negative_harvest_selected_replacement_task_set_count"),
                payload.get("exact_negative_harvest_selected_replacement_task_set_count"),
            ),
            "exact_negative_harvest_selection_policy": _first_str(
                final_judge.get("exact_negative_harvest_selection_policy"),
                payload.get("exact_negative_harvest_selection_policy"),
            ),
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
    labeling_final_judge_exact_harvest_target: int | None,
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
    dual_search_fields = _dual_search_diagnostic_fields(last_worker)
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
            "labeling_final_judge_exact_harvest_target": labeling_final_judge_exact_harvest_target,
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
        **dual_search_fields,
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
            "objective_bound_no_negative_cutoff_enabled": bool(
                final_judge.get("objective_bound_no_negative_cutoff_enabled")
            ),
            "objective_bound_no_negative_cutoff_value": final_judge.get(
                "objective_bound_no_negative_cutoff_value"
            ),
            "objective_bound_no_negative_cutoff_can_certify": bool(
                final_judge.get("objective_bound_no_negative_cutoff_can_certify")
            ),
            "zero_capacity_slot_truncation_enabled": bool(
                final_judge.get("zero_capacity_slot_truncation_enabled")
            ),
            "zero_capacity_slot_truncation_original_slot_count": final_judge.get(
                "zero_capacity_slot_truncation_original_slot_count"
            ),
            "zero_capacity_slot_truncation_effective_slot_count": final_judge.get(
                "zero_capacity_slot_truncation_effective_slot_count"
            ),
            "zero_capacity_slot_truncation_trimmed_slot_count": final_judge.get(
                "zero_capacity_slot_truncation_trimmed_slot_count"
            ),
            "zero_capacity_slot_truncation_first_zero_slot": final_judge.get(
                "zero_capacity_slot_truncation_first_zero_slot"
            ),
            "slot_sequence_capacity_live_bound_enabled": bool(
                final_judge.get("slot_sequence_capacity_live_bound_enabled")
            ),
            "slot_sequence_capacity_live_bound_tightened_slot_count": final_judge.get(
                "slot_sequence_capacity_live_bound_tightened_slot_count"
            ),
            "slot_sequence_capacity_live_bound_by_slot": final_judge.get(
                "slot_sequence_capacity_live_bound_by_slot"
            ),
            "tight_service_start_bounds_enabled": bool(
                final_judge.get("tight_service_start_bounds_enabled")
            ),
            "tight_service_start_bound_count": final_judge.get(
                "tight_service_start_bound_count"
            ),
            "tight_service_start_bound_min": final_judge.get(
                "tight_service_start_bound_min"
            ),
            "tight_service_start_bound_max": final_judge.get(
                "tight_service_start_bound_max"
            ),
            "tight_time_arc_big_m_enabled": bool(
                final_judge.get("tight_time_arc_big_m_enabled")
            ),
            "tight_time_arc_big_m_depot_arc_count": final_judge.get(
                "tight_time_arc_big_m_depot_arc_count"
            ),
            "tight_time_arc_big_m_active_time_bound_count": final_judge.get(
                "tight_time_arc_big_m_active_time_bound_count"
            ),
            "tight_time_arc_big_m_max_reduction": final_judge.get(
                "tight_time_arc_big_m_max_reduction"
            ),
            "slot_service_start_y_lower_bound_enabled": bool(
                final_judge.get("slot_service_start_y_lower_bound_enabled")
            ),
            "slot_service_start_y_lower_bound_count": final_judge.get(
                "slot_service_start_y_lower_bound_count"
            ),
            "slot_service_start_y_lower_bound_max_lift": final_judge.get(
                "slot_service_start_y_lower_bound_max_lift"
            ),
            "slot_service_start_y_lower_bound_min": final_judge.get(
                "slot_service_start_y_lower_bound_min"
            ),
            "slot_service_start_y_lower_bound_max": final_judge.get(
                "slot_service_start_y_lower_bound_max"
            ),
            "sortie_start_upper_bound": final_judge.get("sortie_start_upper_bound"),
            "sortie_slots_per_journey": final_judge.get("sortie_slots_per_journey"),
            "sortie_slot_bound_source": final_judge.get("sortie_slot_bound_source"),
            "sortie_slot_horizon_count_bound": final_judge.get("sortie_slot_horizon_count_bound"),
            "sortie_slot_latest_start_count_bound": final_judge.get("sortie_slot_latest_start_count_bound"),
            "sortie_slot_min_duration_lower_bound": final_judge.get("sortie_slot_min_duration_lower_bound"),
            "sortie_slot_min_energy_recharge_duration_lower_bound": final_judge.get(
                "sortie_slot_min_energy_recharge_duration_lower_bound"
            ),
            "slot_task_time_pruning_enabled": bool(final_judge.get("slot_task_time_pruning_enabled")),
            "slot_task_time_feasible_assignment_count": final_judge.get(
                "slot_task_time_feasible_assignment_count"
            ),
            "slot_task_time_pruned_assignment_count": final_judge.get(
                "slot_task_time_pruned_assignment_count"
            ),
            "slot_task_time_pruned_due_count": final_judge.get("slot_task_time_pruned_due_count"),
            "slot_task_time_pruned_horizon_count": final_judge.get(
                "slot_task_time_pruned_horizon_count"
            ),
            "slot_task_time_total_assignment_count": final_judge.get(
                "slot_task_time_total_assignment_count"
            ),
            "slot_task_model_assignment_count": final_judge.get("slot_task_model_assignment_count"),
            "slot_arc_support_pruning_enabled": bool(
                final_judge.get("slot_arc_support_pruning_enabled")
            ),
            "slot_arc_support_feasible_assignment_count": final_judge.get(
                "slot_arc_support_feasible_assignment_count"
            ),
            "slot_arc_support_pruned_assignment_count": final_judge.get(
                "slot_arc_support_pruned_assignment_count"
            ),
            "slot_arc_support_pruned_unreachable_count": final_judge.get(
                "slot_arc_support_pruned_unreachable_count"
            ),
            "slot_arc_support_pruned_no_return_count": final_judge.get(
                "slot_arc_support_pruned_no_return_count"
            ),
            "slot_arc_support_pruned_option_count": final_judge.get(
                "slot_arc_support_pruned_option_count"
            ),
            "slot_arc_time_pruned_option_count": final_judge.get(
                "slot_arc_time_pruned_option_count"
            ),
            "single_task_per_active_sortie_arc_pruning_enabled": bool(
                final_judge.get("single_task_per_active_sortie_arc_pruning_enabled")
            ),
            "single_task_per_active_sortie_arc_pruned_option_count": final_judge.get(
                "single_task_per_active_sortie_arc_pruned_option_count"
            ),
            "single_task_per_active_sortie_mtz_disabled": bool(
                final_judge.get("single_task_per_active_sortie_mtz_disabled")
            ),
            "mtz_connectivity_effective": bool(final_judge.get("mtz_connectivity_effective")),
            "fixed_active_sortie_redundant_constraint_skipped_count": final_judge.get(
                "fixed_active_sortie_redundant_constraint_skipped_count"
            ),
            "single_task_per_active_sortie_slot_visit_eq_count": final_judge.get(
                "single_task_per_active_sortie_slot_visit_eq_count"
            ),
            "single_task_per_active_sortie_y_z_link_skipped_count": final_judge.get(
                "single_task_per_active_sortie_y_z_link_skipped_count"
            ),
            "resource_arc_pruning_enabled": bool(final_judge.get("resource_arc_pruning_enabled")),
            "resource_arc_pruned_option_count": final_judge.get("resource_arc_pruned_option_count"),
            "resource_arc_energy_pruned_option_count": final_judge.get(
                "resource_arc_energy_pruned_option_count"
            ),
            "resource_arc_shadow_pruned_option_count": final_judge.get(
                "resource_arc_shadow_pruned_option_count"
            ),
            "resource_arc_demand_pruned_option_count": final_judge.get(
                "resource_arc_demand_pruned_option_count"
            ),
            **_single_journey_mip_start_fields(final_judge),
            **_required_task_set_region_fields(final_judge),
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
    payload_config = payload.get("config") if isinstance(payload.get("config"), dict) else {}
    base["labeling_final_judge_exact_harvest_target"] = _first_int(
        final_judge.get("labeling_final_judge_exact_harvest_target"),
        payload.get("labeling_final_judge_exact_harvest_target"),
        payload_config.get("labeling_final_judge_exact_harvest_target"),
    )
    base["labeling_final_judge_exact_harvest_target_source"] = _first_str(
        final_judge.get("labeling_final_judge_exact_harvest_target_source")
    )
    base["exact_negative_harvest_target"] = _first_int(
        final_judge.get("exact_negative_harvest_target"),
        payload.get("exact_negative_harvest_target"),
    )
    base["exact_negative_harvest_candidate_count"] = _first_int(
        final_judge.get("exact_negative_harvest_candidate_count"),
        payload.get("exact_negative_harvest_candidate_count"),
    )
    base["exact_negative_harvest_selected_count"] = _first_int(
        final_judge.get("exact_negative_harvest_selected_count"),
        payload.get("exact_negative_harvest_selected_count"),
    )
    base["exact_negative_harvest_selected_new_task_set_count"] = _first_int(
        final_judge.get("exact_negative_harvest_selected_new_task_set_count"),
        payload.get("exact_negative_harvest_selected_new_task_set_count"),
    )
    base["exact_negative_harvest_selected_replacement_task_set_count"] = _first_int(
        final_judge.get("exact_negative_harvest_selected_replacement_task_set_count"),
        payload.get("exact_negative_harvest_selected_replacement_task_set_count"),
    )
    base["exact_negative_harvest_selection_policy"] = _first_str(
        final_judge.get("exact_negative_harvest_selection_policy"),
        payload.get("exact_negative_harvest_selection_policy"),
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
    value = str(source_phase or "")
    return value.startswith("compact_final_judge") or value == "route_template_pre_harvest"


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


def _last_final_judge_history_payload(history: object) -> dict:
    if not isinstance(history, list):
        return {}
    for row in reversed(history):
        if isinstance(row, dict) and row.get("final_judge_called") is True:
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


def _dual_search_diagnostic_fields(worker_payload: dict | None = None) -> dict:
    worker_payload = worker_payload if isinstance(worker_payload, dict) else {}
    false_positive_rows = worker_payload.get("candidate_search_false_positive_rows") or []
    miss_rows = worker_payload.get("true_negative_candidate_search_miss_rows") or []
    candidate_universe_task_sets = worker_payload.get("worker_candidate_universe_task_sets") or []
    generated_column_task_sets = worker_payload.get("worker_generated_column_task_sets") or []
    return {
        "candidate_search_false_positive_rate": worker_payload.get("candidate_search_false_positive_rate", ""),
        "true_negative_candidate_search_miss_rate": worker_payload.get("true_negative_candidate_search_miss_rate", ""),
        "candidate_search_false_positive_row_count": len(false_positive_rows)
        if isinstance(false_positive_rows, list)
        else "",
        "true_negative_candidate_search_miss_row_count": len(miss_rows) if isinstance(miss_rows, list) else "",
        "candidate_search_negative_true_nonnegative_count": worker_payload.get(
            "candidate_search_negative_true_nonnegative_count",
            "",
        ),
        "true_negative_candidate_search_nonnegative_count": worker_payload.get(
            "true_negative_candidate_search_nonnegative_count",
            "",
        ),
        "candidate_search_dual_matches_true_dual": worker_payload.get(
            "candidate_search_dual_matches_true_dual",
            "",
        ),
        "candidate_search_rc_recomputed_under_true_dual": worker_payload.get(
            "candidate_search_rc_recomputed_under_true_dual",
            "",
        ),
        "worker_true_dual_candidate_audit_pass": worker_payload.get(
            "worker_true_dual_candidate_audit_pass",
            "",
        ),
        "worker_candidate_universe_task_set_count": len(candidate_universe_task_sets)
        if isinstance(candidate_universe_task_sets, list)
        else "",
        "worker_generated_column_task_set_count": worker_payload.get(
            "worker_generated_column_task_set_count",
            len(generated_column_task_sets) if isinstance(generated_column_task_sets, list) else "",
        ),
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
    text = " ".join(str(row.get(key) or "") for key in ("instance_id", "instance_path", "source_probe_json", "matrix_group"))
    return _text_looks_30_scale(text)


def _path_or_id_looks_30_scale(*values: object) -> bool:
    return _text_looks_30_scale(" ".join(str(value or "") for value in values))


def _text_looks_30_scale(text: str) -> bool:
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
    history = normalized.get("history") if isinstance(normalized.get("history"), list) else []
    final_judge_payload = normalized.get("final_judge") if isinstance(normalized.get("final_judge"), dict) else {}
    last_final_judge = _last_final_judge_history_payload(history)
    if not _has_value(normalized.get("compact_pricing_phase")):
        normalized["compact_pricing_phase"] = _first_str(
            final_judge_payload.get("compact_pricing_phase"),
            last_final_judge.get("compact_pricing_phase"),
        )
    for key in (
        "route_template_pre_harvest_status",
        "route_template_pre_harvest_target",
        "route_template_pre_harvest_time_cap_sec",
        "route_template_pre_harvest_max_direct_tasks",
        "route_template_pre_harvest_max_active_seeds",
        "route_template_pre_harvest_seed_strategy",
        "route_template_pre_harvest_neighborhood_enabled",
        "route_template_pre_harvest_max_neighborhood_seeds",
        "route_template_pre_harvest_max_candidate_sets",
        "route_template_pre_harvest_seed_count",
        "route_template_pre_harvest_candidate_round_count",
        "route_template_pre_harvest_candidate_round_limit",
        "route_template_pre_harvest_candidate_negative_count",
        "route_template_pre_harvest_selected_count",
        "route_template_pre_harvest_selected_new_task_set_count",
        "route_template_pre_harvest_selected_replacement_task_set_count",
        "route_template_pre_harvest_pricing_wall_time_sec",
        "route_template_pre_harvest_fallback_enabled",
        "labeling_final_judge_exact_harvest_target",
        "labeling_final_judge_exact_harvest_target_source",
        "exact_negative_harvest_target",
        "exact_negative_harvest_candidate_count",
        "exact_negative_harvest_selected_count",
        "exact_negative_harvest_selected_new_task_set_count",
        "exact_negative_harvest_selected_replacement_task_set_count",
        "exact_negative_harvest_selection_policy",
        "harvest_source_phase",
        "harvest_selected_count",
        "harvest_candidate_negative_count",
        "harvest_best_true_rc",
        "objective_bound_no_negative_cutoff_enabled",
        "objective_bound_no_negative_cutoff_value",
        "objective_bound_no_negative_cutoff_can_certify",
        "zero_capacity_slot_truncation_enabled",
        "zero_capacity_slot_truncation_original_slot_count",
        "zero_capacity_slot_truncation_effective_slot_count",
        "zero_capacity_slot_truncation_trimmed_slot_count",
        "zero_capacity_slot_truncation_first_zero_slot",
        "slot_sequence_capacity_live_bound_enabled",
        "slot_sequence_capacity_live_bound_tightened_slot_count",
        "slot_sequence_capacity_live_bound_by_slot",
        "tight_service_start_bounds_enabled",
        "tight_service_start_bound_count",
        "tight_service_start_bound_min",
        "tight_service_start_bound_max",
        "tight_time_arc_big_m_enabled",
        "tight_time_arc_big_m_depot_arc_count",
        "tight_time_arc_big_m_active_time_bound_count",
        "tight_time_arc_big_m_max_reduction",
        "slot_service_start_y_lower_bound_enabled",
        "slot_service_start_y_lower_bound_count",
        "slot_service_start_y_lower_bound_max_lift",
        "slot_service_start_y_lower_bound_min",
        "slot_service_start_y_lower_bound_max",
        "sortie_start_upper_bound",
    ):
        if not _has_value(normalized.get(key)):
            normalized[key] = _first_str(final_judge_payload.get(key), last_final_judge.get(key))
    if not _has_value(normalized.get("route_template_pre_harvest_enabled")):
        normalized["route_template_pre_harvest_enabled"] = bool(
            final_judge_payload.get("route_template_pre_harvest_enabled")
            or last_final_judge.get("route_template_pre_harvest_enabled")
        )
    tail_payload = normalized.get("tail_dual_stabilization") if isinstance(normalized.get("tail_dual_stabilization"), dict) else {}
    last_worker = _last_worker_payload(history)
    if not tail_payload and isinstance(last_worker.get("tail_dual_stabilization"), dict):
        tail_payload = last_worker["tail_dual_stabilization"]
    tail_fields = _tail_dual_safety_fields(last_worker, tail_payload)
    for key, value in tail_fields.items():
        if tail_fields["tail_dual_stabilization_enabled"] or not _has_value(normalized.get(key)):
            normalized[key] = value
    for key, value in _dual_search_diagnostic_fields(last_worker).items():
        if not _has_value(normalized.get(key)):
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


def _aggregate_partition_candidate_issue_counts(rows: Iterable[dict]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        raw = row.get("partition_candidate_gate_issue_codes")
        if isinstance(raw, str):
            codes = [item.strip() for item in raw.split(",") if item.strip()]
        elif isinstance(raw, (list, tuple)):
            codes = [str(item).strip() for item in raw if str(item).strip()]
        elif isinstance(raw, dict):
            codes = [str(key).strip() for key, value in raw.items() if int(value or 0) > 0 and str(key).strip()]
        else:
            codes = []
        counter.update(codes)
    return dict(counter)


def _top_partition_candidate_issue(counts: dict[str, int]) -> str:
    if not counts:
        return "none"
    issue, _count = max(sorted(counts.items()), key=lambda item: (int(item[1]), item[0]))
    return issue


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


def _tail_dual_certificate_leak(row: dict) -> bool:
    if _bool_value(row.get("tail_dual_no_column_can_certify")):
        return True
    worker_observed = any(
        (
            _has_value(row.get("worker_status")),
            _has_value(row.get("worker_dual_source")),
            int(row.get("worker_generated_column_task_set_count") or 0) > 0,
            _has_value(
                row.get(
                    "candidate_search_rc_recomputed_under_true_dual"
                )
            ),
            _has_value(row.get("worker_true_dual_candidate_audit_pass")),
            _has_value(row.get("tail_dual_center_task_count")),
            _has_value(row.get("tail_dual_current_task_count")),
        )
    )
    if not worker_observed:
        # A configured-but-unreached worker has no certificate role.  Missing
        # booleans on such a row are not evidence of a certificate leak.
        if not _bool_value(row.get("can_certify_no_negative")):
            return False
        proof_kind = str(
            row.get("pricing_proof_kind")
            or row.get("underlying_pricing_proof_kind")
            or ""
        )
        return proof_kind != "EXHAUSTIVE_NO_NEGATIVE"
    if not _bool_value(row.get("worker_dual_only")):
        return True
    if not _bool_value(row.get("true_dual_rc_recomputed")):
        return True
    if (
        _has_value(row.get("worker_true_dual_candidate_audit_pass"))
        and not _bool_value(row.get("worker_true_dual_candidate_audit_pass"))
    ):
        return True
    if str(row.get("official_dual_source") or "") != "current_true_rmp_dual":
        return True
    if not _bool_value(row.get("can_certify_no_negative")):
        return False
    proof_kind = str(
        row.get("pricing_proof_kind")
        or row.get("underlying_pricing_proof_kind")
        or ""
    )
    return proof_kind != "EXHAUSTIVE_NO_NEGATIVE"


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


def _min_present_float(values: Iterable[object]) -> float | None:
    parsed = [_first_float(value) for value in values]
    present = [float(value) for value in parsed if value is not None]
    return None if not present else round(min(present), 9)


def _max_present_float(values: Iterable[object]) -> float | None:
    parsed = [_first_float(value) for value in values]
    present = [float(value) for value in parsed if value is not None]
    return None if not present else round(max(present), 9)


def _mean_present_float(values: Iterable[object]) -> float | None:
    parsed = [_first_float(value) for value in values]
    present = [float(value) for value in parsed if value is not None]
    return None if not present else round(mean(present), 9)


def _max_present_int(values: Iterable[object]) -> int:
    present = [_first_int(value) for value in values if value not in (None, "")]
    return max(present) if present else 0


def _first_present_str(values: Iterable[object]) -> str:
    for value in values:
        if value not in (None, ""):
            return str(value)
    return ""


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


def _optional_positive_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _first_str(*values: object) -> str:
    for value in values:
        if value is None or value == "":
            continue
        return str(value)
    return ""


def _dual_task_slot_full_space_lower_bound_fields(payload: dict) -> dict:
    return {
        "dual_task_slot_full_space_lower_bound_enabled": bool(
            payload.get("dual_task_slot_full_space_lower_bound_enabled")
        ),
        "dual_task_slot_full_space_lower_bound_applicable": bool(
            payload.get("dual_task_slot_full_space_lower_bound_applicable")
        ),
        "dual_task_slot_full_space_lower_bound_early_stop_on_negative": bool(
            payload.get("dual_task_slot_full_space_lower_bound_early_stop_on_negative")
        ),
        "dual_task_slot_full_space_lower_bound_early_stopped_on_negative": bool(
            payload.get("dual_task_slot_full_space_lower_bound_early_stopped_on_negative")
        ),
        "dual_task_slot_full_space_lower_bound_coverage_complete": bool(
            payload.get("dual_task_slot_full_space_lower_bound_coverage_complete")
        ),
        "dual_task_slot_full_space_lower_bound_can_certify": bool(
            payload.get("dual_task_slot_full_space_lower_bound_can_certify")
        ),
        "dual_task_slot_full_space_lower_bound_region_count": _first_int(
            payload.get("dual_task_slot_full_space_lower_bound_region_count")
        ),
        "dual_task_slot_full_space_lower_bound_optimal_region_count": _first_int(
            payload.get("dual_task_slot_full_space_lower_bound_optimal_region_count")
        ),
        "dual_task_slot_full_space_lower_bound_infeasible_region_count": _first_int(
            payload.get("dual_task_slot_full_space_lower_bound_infeasible_region_count")
        ),
        "dual_task_slot_full_space_lower_bound_unsupported_region_count": _first_int(
            payload.get("dual_task_slot_full_space_lower_bound_unsupported_region_count")
        ),
        "dual_task_slot_full_space_lower_bound_negative_region_count": _first_int(
            payload.get("dual_task_slot_full_space_lower_bound_negative_region_count")
        ),
        "dual_task_slot_full_space_lower_bound_value": _first_float(
            payload.get("dual_task_slot_full_space_lower_bound_value")
        ),
        "dual_task_slot_full_space_lower_bound_task_count": _first_int(
            payload.get("dual_task_slot_full_space_lower_bound_task_count")
        ),
        "dual_task_slot_full_space_lower_bound_active_sortie_count": _first_int(
            payload.get("dual_task_slot_full_space_lower_bound_active_sortie_count")
        ),
        "dual_task_slot_full_space_lower_bound_wall_time_sec": _first_float(
            payload.get("dual_task_slot_full_space_lower_bound_wall_time_sec")
        ),
        "dual_task_slot_full_space_lower_bound_status": (
            payload.get("dual_task_slot_full_space_lower_bound_status") or ""
        ),
    }


def _single_journey_mip_start_fields(payload: dict) -> dict:
    return {
        "single_journey_mip_start_enabled": bool(payload.get("single_journey_mip_start_enabled")),
        "single_journey_mip_start_status": payload.get("single_journey_mip_start_status") or "",
        "single_journey_mip_start_source": payload.get("single_journey_mip_start_source") or "",
        "single_journey_mip_start_entry_count": _first_int(
            payload.get("single_journey_mip_start_entry_count")
        ),
        "single_journey_mip_start_zero_fill_integers": bool(
            payload.get("single_journey_mip_start_zero_fill_integers")
        ),
        "single_journey_mip_start_zero_fill_integer_entry_count": _first_int(
            payload.get("single_journey_mip_start_zero_fill_integer_entry_count")
        ),
        "single_journey_mip_start_inactive_tail_time_entry_count": _first_int(
            payload.get("single_journey_mip_start_inactive_tail_time_entry_count")
        ),
        "single_journey_mip_start_inactive_tail_time_mode": str(
            payload.get("single_journey_mip_start_inactive_tail_time_mode") or ""
        ),
        "single_journey_mip_start_sort_indices": bool(
            payload.get("single_journey_mip_start_sort_indices", True)
        ),
        "single_journey_mip_start_sortie_count": _first_int(
            payload.get("single_journey_mip_start_sortie_count")
        ),
        "single_journey_mip_start_task_count": _first_int(
            payload.get("single_journey_mip_start_task_count")
        ),
        "single_journey_mip_start_objective": _first_float(
            payload.get("single_journey_mip_start_objective")
        ),
        "single_journey_mip_start_reduced_cost": _first_float(
            payload.get("single_journey_mip_start_reduced_cost")
        ),
    }


def _required_task_set_region_fields(payload: dict) -> dict:
    required_task_count_enabled = bool(payload.get("required_task_count_enabled"))
    return {
        "required_task_set_enabled": bool(payload.get("required_task_set_enabled")),
        "required_task_set_count": _first_int(payload.get("required_task_set_count")),
        "pricing_model_task_count": _first_int(payload.get("pricing_model_task_count")),
        "required_task_set_model_reduction_enabled": bool(
            payload.get("required_task_set_model_reduction_enabled")
        ),
        "required_task_set_model_task_count": _first_int(
            payload.get("required_task_set_model_task_count")
        ),
        "required_task_set_model_task_reduction_count": _first_int(
            payload.get("required_task_set_model_task_reduction_count")
        ),
        "required_task_set_region_can_certify_no_negative": bool(
            payload.get("required_task_set_region_can_certify_no_negative")
        ),
        "pricing_complete_for_required_task_set": bool(
            payload.get("pricing_complete_for_required_task_set")
        ),
        "required_task_set_infeasible_by_feasible_task_count": bool(
            payload.get("required_task_set_infeasible_by_feasible_task_count")
        ),
        "required_task_set_infeasible_by_slot_capacity": bool(
            payload.get("required_task_set_infeasible_by_slot_capacity")
        ),
        "required_task_set_infeasible_by_slot_sequence_capacity": bool(
            payload.get("required_task_set_infeasible_by_slot_sequence_capacity")
        ),
        "required_task_set_infeasible_by_slot_matching": bool(
            payload.get("required_task_set_infeasible_by_slot_matching")
        ),
        "required_task_count_enabled": required_task_count_enabled,
        "required_task_count": (
            _first_int(payload.get("required_task_count"))
            if required_task_count_enabled
            else ""
        ),
        "required_task_count_region_can_certify_no_negative": bool(
            payload.get("required_task_count_region_can_certify_no_negative")
        ),
        "pricing_complete_for_required_task_count": bool(
            payload.get("pricing_complete_for_required_task_count")
        ),
        "required_task_count_feasible_task_count": _first_int(
            payload.get("required_task_count_feasible_task_count")
        ),
        "required_task_count_slot_capacity_task_upper_bound": _first_int(
            payload.get("required_task_count_slot_capacity_task_upper_bound")
        ),
        "required_task_count_slot_sequence_capacity_upper_bound": _first_int(
            payload.get("required_task_count_slot_sequence_capacity_upper_bound")
        ),
        "required_task_count_slot_matching_capacity_upper_bound": _first_int(
            payload.get("required_task_count_slot_matching_capacity_upper_bound")
        ),
        "required_task_count_pair_conflict_capacity_upper_bound": _first_int(
            payload.get("required_task_count_pair_conflict_capacity_upper_bound")
        ),
        "required_task_count_min_active_sorties": _first_int(
            payload.get("required_task_count_min_active_sorties")
        ),
        "required_task_count_active_sortie_lb_count": _first_int(
            payload.get("required_task_count_active_sortie_lb_count")
        ),
        "required_task_count_infeasible_by_feasible_task_count": bool(
            payload.get("required_task_count_infeasible_by_feasible_task_count")
        ),
        "required_task_count_infeasible_by_slot_capacity": bool(
            payload.get("required_task_count_infeasible_by_slot_capacity")
        ),
        "required_task_count_infeasible_by_slot_sequence_capacity": bool(
            payload.get("required_task_count_infeasible_by_slot_sequence_capacity")
        ),
        "required_task_count_infeasible_by_slot_matching": bool(
            payload.get("required_task_count_infeasible_by_slot_matching")
        ),
        "required_task_count_infeasible_by_pair_conflict_capacity": bool(
            payload.get("required_task_count_infeasible_by_pair_conflict_capacity")
        ),
        "task_slot_pair_conflict_capacity_bound_enabled": bool(
            payload.get("task_slot_pair_conflict_capacity_bound_enabled")
        ),
        "task_slot_pair_conflict_capacity_near_matching_cap": bool(
            payload.get("task_slot_pair_conflict_capacity_near_matching_cap")
        ),
        "task_slot_pair_conflict_capacity_bound_requested": bool(
            payload.get("task_slot_pair_conflict_capacity_bound_requested")
        ),
        "task_slot_pair_conflict_capacity_bound_optimal": bool(
            payload.get("task_slot_pair_conflict_capacity_bound_optimal")
        ),
        "task_slot_pair_conflict_capacity_bound_status": (
            payload.get("task_slot_pair_conflict_capacity_bound_status") or ""
        ),
        "task_slot_pair_conflict_capacity_bound_wall_time_sec": _first_float(
            payload.get("task_slot_pair_conflict_capacity_bound_wall_time_sec")
        ),
        "task_slot_pair_conflict_capacity_bound_variable_count": _first_int(
            payload.get("task_slot_pair_conflict_capacity_bound_variable_count")
        ),
        "task_slot_pair_conflict_capacity_bound_constraint_count": _first_int(
            payload.get("task_slot_pair_conflict_capacity_bound_constraint_count")
        ),
        "task_slot_pair_conflict_capacity_pair_count": _first_int(
            payload.get("task_slot_pair_conflict_capacity_pair_count")
        ),
        "task_slot_pair_conflict_capacity_row_count": _first_int(
            payload.get("task_slot_pair_conflict_capacity_row_count")
        ),
        "task_slot_pair_conflict_capacity_hyperedge_count": _first_int(
            payload.get("task_slot_pair_conflict_capacity_hyperedge_count")
        ),
        "task_slot_pair_conflict_capacity_hyperedge_row_count": _first_int(
            payload.get("task_slot_pair_conflict_capacity_hyperedge_row_count")
        ),
        "required_active_sortie_count_enabled": bool(
            payload.get("required_active_sortie_count_enabled")
        ),
        "required_active_sortie_count": (
            _first_int(payload.get("required_active_sortie_count"))
            if payload.get("required_active_sortie_count_enabled")
            else ""
        ),
        "required_active_sortie_count_region_can_certify_no_negative": bool(
            payload.get("required_active_sortie_count_region_can_certify_no_negative")
        ),
        "pricing_complete_for_required_active_sortie_count": bool(
            payload.get("pricing_complete_for_required_active_sortie_count")
        ),
        "required_active_sortie_count_min": _first_int(
            payload.get("required_active_sortie_count_min")
        ),
        "required_active_sortie_count_max": _first_int(
            payload.get("required_active_sortie_count_max")
        ),
        "required_active_sortie_count_capacity_min": _first_int(
            payload.get("required_active_sortie_count_capacity_min")
        ),
        "required_active_sortie_count_expected_counts": payload.get(
            "required_active_sortie_count_expected_counts"
        )
        or [],
        "required_active_sortie_count_infeasible": bool(
            payload.get("required_active_sortie_count_infeasible")
        ),
        "required_active_sortie_count_infeasible_by_empty_slot": bool(
            payload.get("required_active_sortie_count_infeasible_by_empty_slot")
        ),
        "required_active_sortie_count_infeasible_by_capacity_min": bool(
            payload.get("required_active_sortie_count_infeasible_by_capacity_min")
        ),
        "required_active_sortie_count_slots_fixed": bool(
            payload.get("required_active_sortie_count_slots_fixed")
        ),
        "required_active_sortie_count_fixed_slot_count": _first_int(
            payload.get("required_active_sortie_count_fixed_slot_count")
        ),
        "forbidden_task_set_skipped_by_required_task_count": _first_int(
            payload.get("forbidden_task_set_skipped_by_required_task_count")
        ),
    }


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

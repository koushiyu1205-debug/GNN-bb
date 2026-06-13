#!/usr/bin/env python3
"""Run audit-only Sharded Pulse ROI calibration on a small fixed matrix."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from BPC_future.core.data import load_future_data
from BPC_future.core.fleet_bound import apply_fleet_bound_override
from BPC_future.pricing.trip_pricing import _clear_sequence_resource_precheck_cache
from BPC_future.solver.journey_driver import solve_bpc_future_journey
from BPC_future.solver.logger import FutureLogger


BALANCED_ROOT = Path("BPC_future/data/generated/moon_trek_balanced_60_20260609/logical_graphs")

INSTANCE_PRESETS: dict[str, str] = {
    "very_small": "very_small",
    "apollo5": str(
        BALANCED_ROOT
        / "apollo15_20km/tasks_05/apollo15_20km_balanced_tasks05_01_seed36000_logical_graph.json"
    ),
    "tranq5": str(
        BALANCED_ROOT
        / "tranquillitatis_balmer_like_20km/tasks_05/"
        / "tranquillitatis_balmer_like_20km_balanced_tasks05_01_seed136000_logical_graph.json"
    ),
    "apollo10": str(
        BALANCED_ROOT
        / "apollo15_20km/tasks_10/apollo15_20km_balanced_tasks10_01_seed41002_logical_graph.json"
    ),
    "tranq10_09": str(
        BALANCED_ROOT
        / "tranquillitatis_balmer_like_20km/tasks_10/"
        / "tranquillitatis_balmer_like_20km_balanced_tasks10_09_seed141817_logical_graph.json"
    ),
    "tranq10_04": str(
        BALANCED_ROOT
        / "tranquillitatis_balmer_like_20km/tasks_10/"
        / "tranquillitatis_balmer_like_20km_balanced_tasks10_04_seed141307_logical_graph.json"
    ),
    "tranq10_01": str(
        BALANCED_ROOT
        / "tranquillitatis_balmer_like_20km/tasks_10/"
        / "tranquillitatis_balmer_like_20km_balanced_tasks10_01_seed141000_logical_graph.json"
    ),
    "tranq10_06": str(
        BALANCED_ROOT
        / "tranquillitatis_balmer_like_20km/tasks_10/"
        / "tranquillitatis_balmer_like_20km_balanced_tasks10_06_seed141511_logical_graph.json"
    ),
    "apollo10_04": str(
        BALANCED_ROOT
        / "apollo15_20km/tasks_10/apollo15_20km_balanced_tasks10_04_seed41316_logical_graph.json"
    ),
    "apollo10_09": str(
        BALANCED_ROOT
        / "apollo15_20km/tasks_10/apollo15_20km_balanced_tasks10_09_seed41847_logical_graph.json"
    ),
    "tranq20_01": str(
        Path("BPC_future/data/generated/moon_trek_60/logical_graphs")
        / "tranquillitatis_balmer_like_20km/tasks_20/"
        / "tranquillitatis_balmer_like_20km_tasks20_01_seed21000_logical_graph.json"
    ),
    "apollo20_01": str(
        Path("BPC_future/data/generated/moon_trek_60/logical_graphs")
        / "apollo15_20km/tasks_20/apollo15_20km_tasks20_01_seed21000_logical_graph.json"
    ),
    "mt20_greedy_apollo_01": str(
        Path("BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km")
        / "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json"
    ),
    "mt20_greedy_tranq_01": str(
        Path("BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km")
        / "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json"
    ),
}


def _balanced_task_paths(task_size: int) -> tuple[str, ...]:
    task_dir = f"tasks_{int(task_size):02d}"
    roots = (
        BALANCED_ROOT / "apollo15_20km" / task_dir,
        BALANCED_ROOT / "tranquillitatis_balmer_like_20km" / task_dir,
    )
    paths: list[str] = []
    for root in roots:
        paths.extend(str(path) for path in sorted(root.glob("*_logical_graph.json")))
    return tuple(paths)


INSTANCE_GROUPS: dict[str, tuple[str, ...]] = {
    "balanced5_all": _balanced_task_paths(5),
    "balanced10_all": _balanced_task_paths(10),
    "phase7o_5_gate": _balanced_task_paths(5),
    "phase7o_10_gate": (
        "apollo10",
        "tranq10_09",
        "tranq10_04",
        "tranq10_01",
        "tranq10_06",
        "apollo10_04",
        "apollo10_09",
    ),
    "phase7o_20_smoke": (
        "tranq20_01",
        "mt20_greedy_apollo_01",
        "mt20_greedy_tranq_01",
    ),
    "phase8p_20_source_seed_matrix": (
        "mt20_greedy_apollo_01",
        "mt20_greedy_tranq_01",
        "tranq20_01",
    ),
}

INSTANCE_GROUPS["phase7o_gate"] = (
    *INSTANCE_GROUPS["phase7o_5_gate"],
    *INSTANCE_GROUPS["phase7o_10_gate"],
    *INSTANCE_GROUPS["phase7o_20_smoke"],
)
INSTANCE_GROUPS["phase9k_dual_stabilization_gate"] = (
    "apollo5",
    "tranq5",
    "apollo10",
    "tranq10_09",
    "tranq10_04",
    "mt20_greedy_apollo_01",
    "tranq20_01",
    "mt20_greedy_tranq_01",
)
INSTANCE_GROUPS["phase9l_previous_dual_stabilization_gate"] = (
    *INSTANCE_GROUPS["balanced5_all"],
    *INSTANCE_GROUPS["balanced10_all"],
    *INSTANCE_GROUPS["phase7o_20_smoke"],
)
INSTANCE_GROUPS["phase10b_profile_dp_state_cap_gate"] = (
    "apollo5",
    "tranq5",
    "apollo10",
    "tranq10_09",
    "tranq10_04",
    "tranq20_01",
    "mt20_greedy_apollo_01",
    "mt20_greedy_tranq_01",
)
INSTANCE_GROUPS["phase10c_profile_dp_mask_hotspot_gate"] = (
    *INSTANCE_GROUPS["phase10b_profile_dp_state_cap_gate"],
)

ROI_PRESETS: dict[str, dict[str, float | int]] = {
    "low": {
        "prune_rate_floor": 0.001,
        "min_expanded": 10,
        "min_time": 0.0,
    },
    "mid": {
        "prune_rate_floor": 0.01,
        "min_expanded": 25,
        "min_time": 0.01,
    },
    "high": {
        "prune_rate_floor": 0.05,
        "min_expanded": 50,
        "min_time": 0.02,
    },
}

PROFILE_ORDER = (
    "baseline",
    "audit_no_refine",
    "audit_refine",
    "audit_refine_roi_low",
    "audit_refine_roi_mid",
    "audit_refine_roi_high",
)
VALID_PROFILES = (
    *PROFILE_ORDER,
    "audit_only",
    "audit_plus_strict_worker",
    "strict_worker_previous_signal_only",
    "strict_worker_current_probe",
    "strict_worker_current_probe_impact",
    "strict_worker_current_probe_support_aware",
    "strict_worker_current_probe_support_aware_low_budget",
    "strict_worker_current_probe_support_aware_mid_budget",
    "strict_worker_current_probe_support_aware_impact_filter",
    "strict_worker_current_probe_hard_tail_only",
    "strict_worker_delayed_hard_tail_only",
    "strict_worker_delayed_current_probe_impact",
    "strict_worker_delayed_current_probe_impact_low_budget",
    "strict_worker_delayed_current_probe_impact_ultra_low_budget",
    "strict_worker_delayed_current_probe_impact_low_budget_cooldown",
    "strict_worker_delayed_current_probe_impact_20_only_cooldown",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve_active_gate",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_deep_reserve_active_gate",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_active_gate",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_followup_reserve",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_early_cg",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_hard_tail_fingerprint",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown_ordered",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_transition_priority",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_path_diagnostic",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_arc_option_priority",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_residual_target_priority_roi_gate",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_diagnostic",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_roi_gate",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_diagnostic",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_roi_gate",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic",
    "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_roi_gate",
    "experimental_l1_previous_dual_stabilization_20_only",
    "experimental_l1_zero_dual_stabilization_20_only",
    "experimental_profile_dp_cap_2000_20_only",
    "experimental_profile_dp_cap_3000_20_only",
    "experimental_profile_dp_mask_label_cap_16_20_only",
    "experimental_profile_dp_mask_label_cap_32_20_only",
    "experimental_early_new_task_set_quota_3_20_only",
    "experimental_early_new_task_set_quota_3_return12_20_only",
    "experimental_pricing_time_0_6_20_only",
    "experimental_pricing_time_1_0_20_only",
    "experimental_profile_selection_integer_diverse_20_only",
    "experimental_profile_selection_orthogonal_20_only",
)
PROFILE_GROUPS: dict[str, tuple[str, ...]] = {
    "phase8o_active_source_search": (
        "baseline",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_diagnostic",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_roi_gate",
    ),
    "phase8p_active_source_seed_matrix": (
        "baseline",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown_ordered",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_diagnostic",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_roi_gate",
    ),
    "phase8q_passed_source_roi_validation": (
        "baseline",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_diagnostic",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_roi_gate",
    ),
    "phase9a_profile_dp_bridge_diagnostics": (
        "baseline",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic",
    ),
    "phase9b_returned_residual_tail_attribution": (
        "baseline",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic",
    ),
    "phase9c_rmp_residual_active_support_attribution": (
        "baseline",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic",
    ),
    "phase9d_residual_family_chain_attribution": (
        "baseline",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic",
    ),
    "phase9e_rmp_degeneracy_pool_pressure_attribution": (
        "baseline",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic",
    ),
    "phase9f_rmp_stabilization_pool_compression_diagnostics": (
        "baseline",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic",
    ),
    "phase9g_rmp_dual_stabilization_diagnostic_design": (
        "baseline",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic",
    ),
    "phase9h_rmp_dual_stabilization_probe_skeleton": (
        "baseline",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic",
    ),
    "phase9i_rmp_dual_stabilization_ab": (
        "baseline",
        "experimental_l1_previous_dual_stabilization_20_only",
        "experimental_l1_zero_dual_stabilization_20_only",
    ),
    "phase9j_rmp_dual_stabilization_repeat_ab": (
        "baseline",
        "experimental_l1_previous_dual_stabilization_20_only",
        "experimental_l1_zero_dual_stabilization_20_only",
    ),
    "phase9k_rmp_dual_stabilization_hardset_ab": (
        "baseline",
        "experimental_l1_previous_dual_stabilization_20_only",
        "experimental_l1_zero_dual_stabilization_20_only",
    ),
    "phase9l_previous_dual_stabilization_gate_ab": (
        "baseline",
        "experimental_l1_previous_dual_stabilization_20_only",
    ),
    "phase10a_profile_dp_tail_diagnostics": (
        "baseline",
    ),
    "phase10b_profile_dp_state_cap_sensitivity": (
        "baseline",
        "experimental_profile_dp_cap_2000_20_only",
        "experimental_profile_dp_cap_3000_20_only",
    ),
    "phase10c_profile_dp_mask_hotspot_sensitivity": (
        "baseline",
        "experimental_profile_dp_mask_label_cap_16_20_only",
        "experimental_profile_dp_mask_label_cap_32_20_only",
    ),
    "phase10h_early_new_task_set_quota": (
        "baseline",
        "experimental_early_new_task_set_quota_3_20_only",
        "experimental_early_new_task_set_quota_3_return12_20_only",
    ),
    "phase11a_profile_pricing_time_sensitivity": (
        "baseline",
        "experimental_pricing_time_0_6_20_only",
        "experimental_pricing_time_1_0_20_only",
    ),
    "phase11b_profile_selection_mode_sensitivity": (
        "baseline",
        "experimental_profile_selection_integer_diverse_20_only",
        "experimental_profile_selection_orthogonal_20_only",
    ),
}

SUMMARY_FIELDS = (
    "instance",
    "scale",
    "profile",
    "repeat_index",
    "tasks",
    "status",
    "wall_time",
    "primal",
    "dual_bound",
    "gap",
    "pricing_state",
    "best_rc",
    "official_status",
    "official_primal_bound",
    "official_dual_bound",
    "official_gap",
    "official_pricing_state",
    "official_best_rc",
    "official_negative_journey_task_set_count",
    "official_negative_journey_task_set_hash",
    "official_negative_journey_task_set_samples",
    "official_negative_journey_sequence_samples",
    "official_negative_journey_signature_samples",
    "official_negative_first_task_set",
    "official_negative_first_task_count",
    "official_negative_profile_dp_top_overlap",
    "official_negative_profile_dp_top_jaccard",
    "official_negative_profile_dp_top_relation",
    "official_negative_profile_dp_top_exact",
    "dual_stabilization_events",
    "dual_stabilization_accepted_count",
    "dual_stabilization_skipped_count",
    "dual_stabilization_status_sequence",
    "dual_stabilization_source_sequence",
    "dual_stabilization_mode_sequence",
    "dual_stabilization_reference_sequence",
    "dual_stabilization_first_accepted_cg_iter",
    "dual_stabilization_current_pool_negative_count_max",
    "dual_stabilization_objective_mismatch_count",
    "dual_stabilization_current_pool_infeasible_count",
    "dual_stabilization_time",
    "dual_stabilization_effect_class",
    "official_result_changed_vs_baseline",
    "objective_mismatch_vs_baseline",
    "official_unchanged_vs_baseline",
    "solving_time",
    "rmp_solves",
    "root_rmp_rounds",
    "pricing_calls",
    "exact_pricing_calls",
    "columns",
    "pool_diag_events",
    "pool_journeys_last",
    "pool_unique_task_sets_last",
    "pool_duplicate_task_sets_last",
    "pool_duplicate_task_set_ratio_last",
    "pool_duplicate_task_set_ratio_max",
    "pool_avg_journeys_per_task_set_last",
    "pool_max_journeys_per_task_set_last",
    "pool_active_journeys_last",
    "pool_active_task_sets_last",
    "pool_active_duplicate_task_sets_last",
    "pool_active_duplicate_task_set_ratio_last",
    "pool_active_duplicate_task_set_ratio_max",
    "pool_active_avg_journeys_per_task_set_last",
    "pool_active_fractional_journeys_last",
    "pool_active_fractional_ratio_last",
    "pool_active_fractional_ratio_max",
    "pool_active_fractional_value_sum_last",
    "pool_active_fractional_value_max_last",
    "pool_active_fractional_value_min_last",
    "pool_active_fractional_small_value_count_last",
    "pool_active_total_value_last",
    "pool_active_max_value_last",
    "pool_active_singleton_task_sets_last",
    "pool_active_multi_task_sets_last",
    "pool_active_task_count_union_last",
    "pool_active_task_set_hash_first",
    "pool_active_task_set_hash_last",
    "pool_active_task_set_hash_sequence",
    "pool_active_task_set_hash_unique_count",
    "pool_active_task_set_hash_churn_count",
    "pool_active_top_task_set_value_samples_first",
    "pool_active_top_task_set_value_samples_last",
    "pool_active_trajectory_class",
    "pool_active_trajectory_reason",
    "early_column_addition_events",
    "early_column_addition_kind_sequence",
    "early_column_primary_task_set_sequence",
    "early_column_changed_task_set_hash_sequence",
    "early_column_new_task_set_hash_sequence",
    "early_column_productivity_class_sequence",
    "early_column_active_hash_before_sequence",
    "early_column_active_hash_after_sequence",
    "early_column_active_hash_transition_count",
    "early_column_changed_active_relation_before_sequence",
    "early_column_changed_active_relation_after_sequence",
    "early_column_active_changed_task_set_count",
    "early_column_trajectory_class",
    "early_column_trajectory_reason",
    "generated_sequences",
    "evaluated_timed_trips",
    "legacy_final_judge_calls",
    "legacy_final_judge_after_worker_calls",
    "final_judge_max_single_call_time",
    "exact_completion_bound_retry_count",
    "exact_completion_bound_retry_time",
    "completion_bound_retry_count",
    "exact_retry_calls",
    "profile_dp_tail_records",
    "profile_dp_tail_incomplete_count",
    "profile_dp_tail_negative_count",
    "profile_dp_tail_no_negative_count",
    "profile_dp_tail_state_cap_hit_count",
    "profile_dp_tail_mask_cap_incomplete_count",
    "profile_dp_tail_time",
    "profile_dp_tail_state_count_max",
    "profile_dp_tail_processed_labels_max",
    "profile_dp_tail_extension_attempts",
    "profile_dp_tail_nonempty_mask_count_max",
    "profile_dp_tail_max_labels_per_mask_observed_max",
    "profile_dp_tail_top_mask_label_counts",
    "profile_dp_tail_min_best_rc",
    "profile_dp_tail_class",
    "profile_dp_tail_reason",
    "profile_dp_tail_label_cap_pruned",
    "profile_dp_tail_selected_candidate_input_count",
    "profile_dp_tail_selected_candidate_scanned_count",
    "profile_dp_tail_selected_candidate_materialized_count",
    "profile_dp_tail_selected_candidate_returned_count",
    "profile_dp_tail_selected_candidate_filtered_count",
    "profile_dp_tail_selected_unmaterialized_candidate_count",
    "profile_dp_tail_materialization_candidate_count",
    "profile_dp_tail_materialization_selected_candidate_count",
    "profile_dp_tail_materialization_infeasible_filtered_count",
    "profile_dp_tail_hotspot_class",
    "profile_dp_tail_hotspot_reason",
    "hidden_negative_audit_events",
    "hidden_negative_audit_count",
    "audit_events",
    "pulse_audit_skipped",
    "pulse_audit_skip_reason",
    "pulse_audit_trigger",
    "pulse_audit_status",
    "pulse_audit_comparison_type",
    "pulse_audit_disagreement_severity",
    "pulse_audit_time",
    "pulse_audit_recursions",
    "pulse_audit_shards_total",
    "pulse_audit_shards_certified",
    "pulse_audit_shards_incomplete",
    "pulse_audit_shards_negative",
    "pulse_audit_shards_refined",
    "pulse_audit_low_roi_shards",
    "pulse_audit_bound_pruned",
    "pulse_audit_archive_pruned",
    "pulse_audit_time_window_pruned",
    "pulse_audit_energy_pruned",
    "pulse_audit_return_pruned",
    "pulse_audit_capacity_pruned",
    "pulse_audit_pulse_energy_pruned",
    "pulse_audit_negative_pool_size",
    "pulse_audit_harvested_count",
    "worker_events",
    "pulse_worker_skipped",
    "pulse_worker_skip_reason",
    "pulse_worker_trigger",
    "pulse_worker_signal_source",
    "pulse_worker_previous_audit_signal",
    "pulse_worker_current_probe_signal",
    "pulse_worker_status",
    "worker_triggered",
    "worker_skip_reason",
    "worker_signal_source",
    "worker_context_hash",
    "worker_returned_journeys",
    "worker_added_journeys",
    "worker_added_new_task_sets",
    "worker_added_new_task_set_count",
    "worker_added_replacement_count",
    "worker_added_support_changing_count",
    "worker_addition_productivity_class",
    "worker_time",
    "worker_recursions",
    "worker_pruned_total",
    "worker_bound_pruned",
    "worker_archive_pruned",
    "worker_time_window_pruned",
    "worker_return_pruned",
    "worker_harvested_count",
    "worker_stop_after_first_negative",
    "worker_task_ordering",
    "worker_target_sequence",
    "worker_target_first_task_priority_enabled",
    "worker_target_first_task_priority_sequence",
    "worker_target_transition_priority_enabled",
    "worker_target_transition_priority_sequence",
    "worker_target_arc_option_priority_enabled",
    "worker_target_arc_option_priority_sequence",
    "worker_target_sequence_reached_prefix_len",
    "worker_target_sequence_completed",
    "worker_target_sequence_materialized",
    "worker_target_sequence_negative",
    "worker_target_sequence_blocked_reason",
    "worker_target_sequence_blocked_prefix",
    "worker_target_sequence_blocked_next_task",
    "worker_target_sequence_transition_attempts",
    "worker_target_sequence_transition_accepted",
    "worker_target_sequence_prune_reason_counts",
    "worker_target_path_diagnostics_enabled",
    "worker_target_path_prefix_samples",
    "worker_target_path_blocked_samples",
    "auto_residual_target_applied",
    "auto_residual_target_sequence",
    "auto_residual_target_source_profile",
    "auto_residual_target_source_context_hash",
    "auto_residual_target_context_match",
    "auto_residual_target_candidate_sequence",
    "auto_residual_target_source_gate",
    "auto_residual_target_source_gate_reason",
    "active_residual_source_candidate",
    "active_residual_source_candidate_sequence",
    "active_residual_source_context_hash",
    "active_residual_source_relation",
    "active_residual_source_active_signal_count",
    "active_residual_source_gate_reason",
    "active_residual_source_passed",
    "active_residual_source_search_candidate_count",
    "active_residual_source_search_passed_count",
    "active_residual_source_search_blocked_count",
    "active_residual_source_search_blocked_disjoint_count",
    "active_residual_source_search_blocked_no_active_count",
    "active_residual_source_search_blocked_relation_count",
    "active_residual_source_search_first_passed_profile",
    "active_residual_source_search_first_passed_sequence",
    "active_residual_source_search_first_passed_relation",
    "active_residual_source_search_first_passed_context_hash",
    "active_residual_source_search_first_blocked_profile",
    "active_residual_source_search_first_blocked_sequence",
    "active_residual_source_search_first_blocked_reason",
    "active_residual_source_search_outcome_class",
    "active_residual_source_search_recommendation",
    "worker_target_sequence_task_set",
    "worker_target_negative_pool_overlap",
    "worker_target_negative_pool_jaccard",
    "worker_target_negative_pool_relation",
    "worker_target_negative_pool_exact",
    "worker_target_harvested_overlap",
    "worker_target_harvested_jaccard",
    "worker_target_harvested_relation",
    "worker_target_harvested_exact",
    "worker_target_returned_candidate_overlap",
    "worker_target_returned_candidate_jaccard",
    "worker_target_returned_candidate_relation",
    "worker_target_returned_candidate_exact",
    "worker_shards_total",
    "worker_shards_certified",
    "worker_shards_incomplete",
    "worker_shards_negative",
    "worker_shards_refined",
    "worker_low_roi_shards",
    "worker_negative_journey_sequence_samples",
    "worker_negative_journey_signature_samples",
    "worker_negative_pool_task_set_samples",
    "worker_negative_pool_sequence_samples",
    "worker_negative_pool_signature_samples",
    "worker_harvested_task_set_samples",
    "worker_harvested_sequence_samples",
    "worker_harvested_signature_samples",
    "worker_returned_candidate_task_set_samples",
    "worker_returned_candidate_sequence_samples",
    "worker_returned_candidate_signature_samples",
    "worker_continue_same_iteration_events",
    "pulse_worker_returned_journeys",
    "pulse_worker_added_journeys",
    "pulse_worker_added_new_journeys",
    "pulse_worker_added_replacement_journeys",
    "pulse_worker_added_new_task_set_count",
    "pulse_worker_added_replacement_task_set_count",
    "pulse_worker_added_support_changing_count",
    "pulse_worker_addition_productivity_class",
    "pulse_worker_impact_filter_enabled",
    "pulse_worker_impact_filter_mode",
    "pulse_worker_impact_filter_candidate_count",
    "pulse_worker_impact_filter_selected_count",
    "pulse_worker_impact_filter_dropped_count",
    "pulse_worker_impact_filter_selected_new_task_set_count",
    "pulse_worker_impact_filter_selected_replacement_task_set_count",
    "pulse_worker_impact_filter_selected_active_support_changing_count",
    "pulse_worker_impact_filter_selected_weak_replacement_count",
    "pulse_worker_impact_filter_min_true_rc",
    "pulse_worker_impact_filter_selected_best_true_rc",
    "pulse_worker_impact_filter_rc_threshold_dropped_count",
    "pulse_worker_shards_total",
    "pulse_worker_shards_certified",
    "pulse_worker_shards_incomplete",
    "pulse_worker_shards_negative",
    "pulse_worker_shards_refined",
    "pulse_worker_low_roi_shards",
    "pulse_worker_followup_reserve_min_time",
    "pulse_worker_followup_reserve_remaining_time",
    "pulse_worker_followup_reserve_dropped_journeys",
    "followup_rmp_objective_delta",
    "followup_dual_l1_delta",
    "followup_worker_changed_task_set_count",
    "followup_worker_active_task_set_count",
    "followup_worker_inactive_task_set_count",
    "followup_worker_active_task_set_ratio",
    "followup_wall_after_worker",
    "followup_pricing_calls",
    "followup_heuristic_pricing_calls",
    "followup_exact_pricing_calls",
    "followup_exact_retry_pricing_calls",
    "followup_generated_sequences",
    "followup_evaluated_timed_trips",
    "followup_legacy_final_judge_calls",
    "followup_legacy_final_judge_time",
    "followup_completion_retry_count",
    "followup_completion_retry_time",
    "followup_hidden_negative_audit_count",
    "followup_worker_negative_after_worker_count",
    "followup_last_pricing_kind",
    "followup_last_pricing_state",
    "followup_last_pricing_reason",
    "followup_last_best_rc",
    "followup_tail_outcome",
    "followup_negative_pricing_calls",
    "followup_incomplete_pricing_calls",
    "followup_min_best_rc",
    "followup_pricing_state_sequence",
    "followup_first_negative_cg_iter",
    "followup_first_negative_pricing_kind",
    "followup_first_negative_best_rc",
    "followup_first_negative_task_set_hash",
    "followup_first_negative_task_set",
    "followup_first_negative_task_count",
    "followup_first_negative_sequence",
    "followup_first_negative_signature_sample",
    "followup_first_negative_overlap_to_worker",
    "followup_first_negative_jaccard_to_worker",
    "followup_first_negative_relation_to_worker",
    "worker_vs_ordinary_first_worker_task_set",
    "worker_vs_ordinary_first_followup_task_set",
    "worker_vs_ordinary_task_set_overlap",
    "worker_vs_ordinary_task_set_jaccard",
    "worker_vs_ordinary_task_set_relation",
    "worker_vs_ordinary_disjoint",
    "worker_vs_ordinary_worker_task_count",
    "worker_vs_ordinary_followup_task_count",
    "worker_vs_ordinary_task_count_delta",
    "worker_vs_ordinary_worker_added_before_followup",
    "worker_vs_ordinary_followup_returned_after_worker",
    "worker_vs_ordinary_contrast_class",
    "worker_vs_ordinary_negative_pool_overlap",
    "worker_vs_ordinary_negative_pool_jaccard",
    "worker_vs_ordinary_negative_pool_relation",
    "worker_vs_ordinary_negative_pool_exact",
    "worker_vs_ordinary_harvested_overlap",
    "worker_vs_ordinary_harvested_jaccard",
    "worker_vs_ordinary_harvested_relation",
    "worker_vs_ordinary_harvested_exact",
    "worker_vs_ordinary_returned_candidate_overlap",
    "worker_vs_ordinary_returned_candidate_jaccard",
    "worker_vs_ordinary_returned_candidate_relation",
    "worker_vs_ordinary_returned_candidate_exact",
    "followup_first_negative_profile_dp_top_overlap",
    "followup_first_negative_profile_dp_top_jaccard",
    "followup_first_negative_profile_dp_top_relation",
    "followup_first_negative_profile_dp_top_exact",
    "followup_first_negative_profile_reachable_overlap",
    "followup_first_negative_profile_reachable_jaccard",
    "followup_first_negative_profile_reachable_relation",
    "followup_first_negative_profile_reachable_exact",
    "followup_first_negative_profile_negative_overlap",
    "followup_first_negative_profile_negative_jaccard",
    "followup_first_negative_profile_negative_relation",
    "followup_first_negative_profile_negative_exact",
    "followup_first_negative_profile_selected_overlap",
    "followup_first_negative_profile_selected_jaccard",
    "followup_first_negative_profile_selected_relation",
    "followup_first_negative_profile_selected_exact",
    "followup_first_negative_profile_materialized_overlap",
    "followup_first_negative_profile_materialized_jaccard",
    "followup_first_negative_profile_materialized_relation",
    "followup_first_negative_profile_materialized_exact",
    "followup_first_negative_profile_returned_overlap",
    "followup_first_negative_profile_returned_jaccard",
    "followup_first_negative_profile_returned_relation",
    "followup_first_negative_profile_returned_exact",
    "followup_first_negative_profile_unmaterialized_overlap",
    "followup_first_negative_profile_unmaterialized_jaccard",
    "followup_first_negative_profile_unmaterialized_relation",
    "followup_first_negative_profile_unmaterialized_exact",
    "followup_first_negative_profile_weak_filtered_overlap",
    "followup_first_negative_profile_weak_filtered_jaccard",
    "followup_first_negative_profile_weak_filtered_relation",
    "followup_first_negative_profile_weak_filtered_exact",
    "followup_first_negative_profile_filtered_overlap",
    "followup_first_negative_profile_filtered_jaccard",
    "followup_first_negative_profile_filtered_relation",
    "followup_first_negative_profile_filtered_exact",
    "followup_proof_tail_bridge_class",
    "followup_proof_tail_bridge_reason",
    "followup_returned_residual_tail_class",
    "followup_returned_residual_tail_reason",
    "followup_negative_task_set_sequence",
    "followup_negative_task_set_unique_count",
    "followup_negative_task_set_repeat_count",
    "followup_first_negative_addition_productivity_class",
    "followup_first_negative_added_journeys",
    "followup_first_negative_added_new_task_set_count",
    "followup_first_negative_added_replacement_count",
    "followup_first_negative_added_support_changing_count",
    "followup_post_first_negative_rmp_objective_delta",
    "followup_post_first_negative_dual_l1_delta",
    "followup_first_negative_active_after_addition",
    "followup_first_negative_active_value_after_addition",
    "followup_first_negative_active_journey_count_after_addition",
    "followup_first_negative_active_relation_after_addition",
    "followup_active_fractional_ratio_after_first_negative",
    "followup_active_total_value_after_first_negative",
    "followup_active_task_set_hash_after_first_negative",
    "followup_rmp_residual_impact_class",
    "followup_rmp_residual_impact_reason",
    "followup_first_negative_active_persistence_count",
    "followup_first_negative_active_value_sequence",
    "followup_first_negative_active_last_value",
    "followup_active_basis_hash_sequence_after_first_negative",
    "followup_active_basis_unique_count_after_first_negative",
    "followup_active_basis_churn_count_after_first_negative",
    "followup_negative_family_after_first_count",
    "followup_negative_family_after_first_relation_sequence",
    "followup_negative_family_after_first_disjoint_count",
    "followup_negative_family_after_first_overlapping_count",
    "followup_negative_family_after_first_same_count",
    "followup_negative_family_after_first_max_overlap",
    "followup_negative_family_after_first_max_jaccard",
    "followup_residual_family_chain_class",
    "followup_residual_family_chain_reason",
    "followup_post_first_negative_pool_duplicate_task_sets",
    "followup_post_first_negative_pool_duplicate_task_set_ratio",
    "followup_post_first_negative_pool_active_duplicate_task_sets",
    "followup_post_first_negative_pool_active_duplicate_task_set_ratio",
    "followup_post_first_negative_pool_avg_journeys_per_task_set",
    "followup_post_first_negative_pool_max_journeys_per_task_set",
    "followup_post_first_negative_pool_active_avg_journeys_per_task_set",
    "followup_post_first_negative_pool_active_fractional_value_sum",
    "followup_post_first_negative_pool_active_fractional_value_max",
    "followup_post_first_negative_pool_active_fractional_value_min",
    "followup_post_first_negative_pool_active_fractional_small_value_count",
    "followup_rmp_degeneracy_pressure_class",
    "followup_rmp_degeneracy_pressure_reason",
    "followup_post_first_negative_dual_objective_abs_ratio",
    "followup_post_first_negative_dual_move_class",
    "followup_pool_compression_candidate_class",
    "followup_pool_compression_candidate_reason",
    "followup_rmp_stabilization_candidate_class",
    "followup_rmp_stabilization_candidate_reason",
    "followup_stabilization_diagnostic_design_class",
    "followup_stabilization_diagnostic_design_reason",
    "followup_stabilization_diagnostic_recommended_profile",
    "followup_stabilization_diagnostic_guarded_config_keys",
    "followup_stabilization_diagnostic_certificate_effect_allowed",
    "followup_stabilization_probe_enabled",
    "followup_stabilization_probe_status",
    "followup_stabilization_probe_reason",
    "followup_stabilization_probe_mode",
    "followup_stabilization_probe_candidate_source",
    "followup_stabilization_probe_anchor_weight",
    "followup_stabilization_probe_context_hash_required",
    "followup_stabilization_probe_context_hash",
    "followup_stabilization_probe_certificate_effect_allowed",
    "followup_stabilization_probe_official_effect_allowed",
    "followup_stabilization_probe_mutates_rmp",
    "followup_stabilization_probe_design_profile",
    "followup_profile_selected_candidate_input_count",
    "followup_profile_selected_candidate_scanned_count",
    "followup_profile_selected_candidate_materialized_count",
    "followup_profile_selected_candidate_returned_count",
    "followup_profile_selected_candidate_filtered_count",
    "followup_profile_selected_candidate_return_limit_truncated_count",
    "followup_terminal_after_negative_incomplete",
    "followup_last_pricing_time_limit",
    "followup_last_pricing_max_dp_states",
    "followup_last_pricing_profile_dp_time",
    "followup_last_pricing_dp_state_count",
    "followup_profile_dp_incomplete_count",
    "followup_profile_dp_incomplete_class",
    "followup_profile_dp_state_count_max",
    "followup_profile_dp_processed_labels_max",
    "followup_profile_dp_extension_attempts",
    "followup_profile_dp_time",
    "followup_profile_dp_state_cap_hit",
    "followup_profile_dp_min_best_rc",
    "followup_profile_dp_max_labels_per_mask_observed",
    "followup_profile_dp_nonempty_mask_count",
    "followup_profile_dp_labels_by_sortie_count",
    "followup_profile_dp_top_mask_label_counts",
    "followup_legacy_final_judge_called",
    "followup_completion_retry_called",
    "pulse_worker_next_rmp_objective_delta",
    "pulse_worker_next_dual_l1_delta",
    "pulse_worker_followup_changed_task_set_count",
    "pulse_worker_followup_active_task_set_count",
    "pulse_worker_followup_inactive_task_set_count",
    "pulse_worker_followup_active_task_set_ratio",
    "pulse_worker_followup_wall_after_worker",
    "pulse_worker_followup_pricing_calls",
    "pulse_worker_followup_generated_sequences",
    "pulse_worker_followup_evaluated_timed_trips",
    "pulse_worker_followup_legacy_final_judge_time",
    "pulse_worker_followup_completion_retry_count",
    "pulse_worker_followup_completion_retry_time",
    "pulse_worker_followup_legacy_final_judge_called",
    "pulse_worker_followup_completion_retry_called",
    "pulse_worker_followup_hidden_negative_found",
    "pulse_worker_followup_tail_outcome",
    "pulse_worker_followup_negative_pricing_calls",
    "pulse_worker_followup_incomplete_pricing_calls",
    "pulse_worker_followup_min_best_rc",
    "pulse_worker_followup_pricing_state_sequence",
    "pulse_worker_followup_first_negative_cg_iter",
    "pulse_worker_followup_first_negative_pricing_kind",
    "pulse_worker_followup_first_negative_best_rc",
    "pulse_worker_followup_first_negative_task_set_hash",
    "pulse_worker_followup_first_negative_task_set",
    "pulse_worker_followup_first_negative_task_count",
    "pulse_worker_followup_first_negative_sequence",
    "pulse_worker_followup_first_negative_signature_sample",
    "pulse_worker_followup_first_negative_overlap_to_worker",
    "pulse_worker_followup_first_negative_jaccard_to_worker",
    "pulse_worker_followup_first_negative_relation_to_worker",
    "pulse_worker_vs_ordinary_first_worker_task_set",
    "pulse_worker_vs_ordinary_first_followup_task_set",
    "pulse_worker_vs_ordinary_task_set_overlap",
    "pulse_worker_vs_ordinary_task_set_jaccard",
    "pulse_worker_vs_ordinary_task_set_relation",
    "pulse_worker_vs_ordinary_disjoint",
    "pulse_worker_vs_ordinary_worker_task_count",
    "pulse_worker_vs_ordinary_followup_task_count",
    "pulse_worker_vs_ordinary_task_count_delta",
    "pulse_worker_vs_ordinary_worker_added_before_followup",
    "pulse_worker_vs_ordinary_followup_returned_after_worker",
    "pulse_worker_vs_ordinary_contrast_class",
    "pulse_worker_vs_ordinary_negative_pool_overlap",
    "pulse_worker_vs_ordinary_negative_pool_jaccard",
    "pulse_worker_vs_ordinary_negative_pool_relation",
    "pulse_worker_vs_ordinary_negative_pool_exact",
    "pulse_worker_vs_ordinary_harvested_overlap",
    "pulse_worker_vs_ordinary_harvested_jaccard",
    "pulse_worker_vs_ordinary_harvested_relation",
    "pulse_worker_vs_ordinary_harvested_exact",
    "pulse_worker_vs_ordinary_returned_candidate_overlap",
    "pulse_worker_vs_ordinary_returned_candidate_jaccard",
    "pulse_worker_vs_ordinary_returned_candidate_relation",
    "pulse_worker_vs_ordinary_returned_candidate_exact",
    "pulse_worker_target_sequence_task_set",
    "pulse_worker_target_negative_pool_overlap",
    "pulse_worker_target_negative_pool_jaccard",
    "pulse_worker_target_negative_pool_relation",
    "pulse_worker_target_negative_pool_exact",
    "pulse_worker_target_harvested_overlap",
    "pulse_worker_target_harvested_jaccard",
    "pulse_worker_target_harvested_relation",
    "pulse_worker_target_harvested_exact",
    "pulse_worker_target_returned_candidate_overlap",
    "pulse_worker_target_returned_candidate_jaccard",
    "pulse_worker_target_returned_candidate_relation",
    "pulse_worker_target_returned_candidate_exact",
    "pulse_worker_followup_first_negative_profile_dp_top_overlap",
    "pulse_worker_followup_first_negative_profile_dp_top_jaccard",
    "pulse_worker_followup_first_negative_profile_dp_top_relation",
    "pulse_worker_followup_first_negative_profile_dp_top_exact",
    "pulse_worker_followup_first_negative_profile_reachable_overlap",
    "pulse_worker_followup_first_negative_profile_reachable_jaccard",
    "pulse_worker_followup_first_negative_profile_reachable_relation",
    "pulse_worker_followup_first_negative_profile_reachable_exact",
    "pulse_worker_followup_first_negative_profile_negative_overlap",
    "pulse_worker_followup_first_negative_profile_negative_jaccard",
    "pulse_worker_followup_first_negative_profile_negative_relation",
    "pulse_worker_followup_first_negative_profile_negative_exact",
    "pulse_worker_followup_first_negative_profile_selected_overlap",
    "pulse_worker_followup_first_negative_profile_selected_jaccard",
    "pulse_worker_followup_first_negative_profile_selected_relation",
    "pulse_worker_followup_first_negative_profile_selected_exact",
    "pulse_worker_followup_first_negative_profile_materialized_overlap",
    "pulse_worker_followup_first_negative_profile_materialized_jaccard",
    "pulse_worker_followup_first_negative_profile_materialized_relation",
    "pulse_worker_followup_first_negative_profile_materialized_exact",
    "pulse_worker_followup_first_negative_profile_returned_overlap",
    "pulse_worker_followup_first_negative_profile_returned_jaccard",
    "pulse_worker_followup_first_negative_profile_returned_relation",
    "pulse_worker_followup_first_negative_profile_returned_exact",
    "pulse_worker_followup_first_negative_profile_unmaterialized_overlap",
    "pulse_worker_followup_first_negative_profile_unmaterialized_jaccard",
    "pulse_worker_followup_first_negative_profile_unmaterialized_relation",
    "pulse_worker_followup_first_negative_profile_unmaterialized_exact",
    "pulse_worker_followup_first_negative_profile_weak_filtered_overlap",
    "pulse_worker_followup_first_negative_profile_weak_filtered_jaccard",
    "pulse_worker_followup_first_negative_profile_weak_filtered_relation",
    "pulse_worker_followup_first_negative_profile_weak_filtered_exact",
    "pulse_worker_followup_first_negative_profile_filtered_overlap",
    "pulse_worker_followup_first_negative_profile_filtered_jaccard",
    "pulse_worker_followup_first_negative_profile_filtered_relation",
    "pulse_worker_followup_first_negative_profile_filtered_exact",
    "pulse_worker_followup_proof_tail_bridge_class",
    "pulse_worker_followup_proof_tail_bridge_reason",
    "pulse_worker_followup_returned_residual_tail_class",
    "pulse_worker_followup_returned_residual_tail_reason",
    "pulse_worker_followup_negative_task_set_sequence",
    "pulse_worker_followup_negative_task_set_unique_count",
    "pulse_worker_followup_negative_task_set_repeat_count",
    "pulse_worker_followup_first_negative_addition_productivity_class",
    "pulse_worker_followup_first_negative_added_journeys",
    "pulse_worker_followup_first_negative_added_new_task_set_count",
    "pulse_worker_followup_first_negative_added_replacement_count",
    "pulse_worker_followup_first_negative_added_support_changing_count",
    "pulse_worker_followup_post_first_negative_rmp_objective_delta",
    "pulse_worker_followup_post_first_negative_dual_l1_delta",
    "pulse_worker_followup_first_negative_active_after_addition",
    "pulse_worker_followup_first_negative_active_value_after_addition",
    "pulse_worker_followup_first_negative_active_journey_count_after_addition",
    "pulse_worker_followup_first_negative_active_relation_after_addition",
    "pulse_worker_followup_active_fractional_ratio_after_first_negative",
    "pulse_worker_followup_active_total_value_after_first_negative",
    "pulse_worker_followup_active_task_set_hash_after_first_negative",
    "pulse_worker_followup_rmp_residual_impact_class",
    "pulse_worker_followup_rmp_residual_impact_reason",
    "pulse_worker_followup_first_negative_active_persistence_count",
    "pulse_worker_followup_first_negative_active_value_sequence",
    "pulse_worker_followup_first_negative_active_last_value",
    "pulse_worker_followup_active_basis_hash_sequence_after_first_negative",
    "pulse_worker_followup_active_basis_unique_count_after_first_negative",
    "pulse_worker_followup_active_basis_churn_count_after_first_negative",
    "pulse_worker_followup_negative_family_after_first_count",
    "pulse_worker_followup_negative_family_after_first_relation_sequence",
    "pulse_worker_followup_negative_family_after_first_disjoint_count",
    "pulse_worker_followup_negative_family_after_first_overlapping_count",
    "pulse_worker_followup_negative_family_after_first_same_count",
    "pulse_worker_followup_negative_family_after_first_max_overlap",
    "pulse_worker_followup_negative_family_after_first_max_jaccard",
    "pulse_worker_followup_residual_family_chain_class",
    "pulse_worker_followup_residual_family_chain_reason",
    "pulse_worker_followup_post_first_negative_pool_duplicate_task_sets",
    "pulse_worker_followup_post_first_negative_pool_duplicate_task_set_ratio",
    "pulse_worker_followup_post_first_negative_pool_active_duplicate_task_sets",
    "pulse_worker_followup_post_first_negative_pool_active_duplicate_task_set_ratio",
    "pulse_worker_followup_post_first_negative_pool_avg_journeys_per_task_set",
    "pulse_worker_followup_post_first_negative_pool_max_journeys_per_task_set",
    "pulse_worker_followup_post_first_negative_pool_active_avg_journeys_per_task_set",
    "pulse_worker_followup_post_first_negative_pool_active_fractional_value_sum",
    "pulse_worker_followup_post_first_negative_pool_active_fractional_value_max",
    "pulse_worker_followup_post_first_negative_pool_active_fractional_value_min",
    "pulse_worker_followup_post_first_negative_pool_active_fractional_small_value_count",
    "pulse_worker_followup_rmp_degeneracy_pressure_class",
    "pulse_worker_followup_rmp_degeneracy_pressure_reason",
    "pulse_worker_followup_post_first_negative_dual_objective_abs_ratio",
    "pulse_worker_followup_post_first_negative_dual_move_class",
    "pulse_worker_followup_pool_compression_candidate_class",
    "pulse_worker_followup_pool_compression_candidate_reason",
    "pulse_worker_followup_rmp_stabilization_candidate_class",
    "pulse_worker_followup_rmp_stabilization_candidate_reason",
    "pulse_worker_followup_stabilization_diagnostic_design_class",
    "pulse_worker_followup_stabilization_diagnostic_design_reason",
    "pulse_worker_followup_stabilization_diagnostic_recommended_profile",
    "pulse_worker_followup_stabilization_diagnostic_guarded_config_keys",
    "pulse_worker_followup_stabilization_diagnostic_certificate_effect_allowed",
    "pulse_worker_followup_stabilization_probe_enabled",
    "pulse_worker_followup_stabilization_probe_status",
    "pulse_worker_followup_stabilization_probe_reason",
    "pulse_worker_followup_stabilization_probe_mode",
    "pulse_worker_followup_stabilization_probe_candidate_source",
    "pulse_worker_followup_stabilization_probe_anchor_weight",
    "pulse_worker_followup_stabilization_probe_context_hash_required",
    "pulse_worker_followup_stabilization_probe_context_hash",
    "pulse_worker_followup_stabilization_probe_certificate_effect_allowed",
    "pulse_worker_followup_stabilization_probe_official_effect_allowed",
    "pulse_worker_followup_stabilization_probe_mutates_rmp",
    "pulse_worker_followup_stabilization_probe_design_profile",
    "pulse_worker_followup_profile_selected_candidate_input_count",
    "pulse_worker_followup_profile_selected_candidate_scanned_count",
    "pulse_worker_followup_profile_selected_candidate_materialized_count",
    "pulse_worker_followup_profile_selected_candidate_returned_count",
    "pulse_worker_followup_profile_selected_candidate_filtered_count",
    "pulse_worker_followup_profile_selected_candidate_return_limit_truncated_count",
    "pulse_residual_replay_events",
    "pulse_residual_replay_checked",
    "pulse_residual_replay_materialized",
    "pulse_residual_replay_negative",
    "pulse_residual_replay_rc_mismatch_count",
    "pulse_residual_replay_signature_mismatch_count",
    "pulse_residual_replay_first_status",
    "pulse_residual_replay_first_sequence",
    "pulse_residual_replay_first_original_true_rc",
    "pulse_residual_replay_first_replay_true_rc",
    "pulse_residual_replay_first_rc_delta",
    "pulse_worker_followup_terminal_after_negative_incomplete",
    "pulse_worker_followup_last_pricing_time_limit",
    "pulse_worker_followup_last_pricing_max_dp_states",
    "pulse_worker_followup_last_pricing_profile_dp_time",
    "pulse_worker_followup_last_pricing_dp_state_count",
    "pulse_worker_followup_profile_dp_incomplete_count",
    "pulse_worker_followup_profile_dp_incomplete_class",
    "pulse_worker_followup_profile_dp_state_count_max",
    "pulse_worker_followup_profile_dp_processed_labels_max",
    "pulse_worker_followup_profile_dp_extension_attempts",
    "pulse_worker_followup_profile_dp_time",
    "pulse_worker_followup_profile_dp_state_cap_hit",
    "pulse_worker_followup_profile_dp_min_best_rc",
    "pulse_worker_followup_profile_dp_max_labels_per_mask_observed",
    "pulse_worker_followup_profile_dp_nonempty_mask_count",
    "pulse_worker_followup_profile_dp_labels_by_sortie_count",
    "pulse_worker_followup_profile_dp_top_mask_label_counts",
    "pulse_worker_true_rc_filtered",
    "pulse_worker_task_ordering",
    "pulse_worker_continue_same_iteration_events",
    "pulse_worker_time",
    "pulse_worker_recursions",
    "pulse_worker_shards_negative",
    "pulse_worker_context_hash",
    "critical_disagreement",
    "critical_disagreement_count",
    "pivot_recommendation_class",
    "pivot_recommendation_reason",
    "improvement_class",
    "log_path",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit-only Sharded Pulse ROI calibration.")
    parser.add_argument("--output-dir", default="BPC_future/results/sharded_pulse_phase7l_roi_calibration_20260612")
    parser.add_argument("--instances", nargs="*", default=list(INSTANCE_PRESETS))
    parser.add_argument("--profiles", nargs="*", default=list(PROFILE_ORDER))
    parser.add_argument("--time-limit", type=float, default=8.0)
    parser.add_argument("--audit-time-limit", type=float, default=0.5)
    parser.add_argument("--worker-time-limit", type=float, default=0.5)
    parser.add_argument("--current-probe-time-limit", type=float, default=0.5)
    parser.add_argument("--pricing-time-limit", type=float, default=0.2)
    parser.add_argument("--pricing-max-dp-states", type=int, default=1)
    parser.add_argument("--max-cg-iterations", type=int, default=3)
    parser.add_argument("--audit-max-recursions", type=int, default=100000)
    parser.add_argument("--worker-max-recursions", type=int, default=100000)
    parser.add_argument("--current-probe-max-recursions", type=int, default=50000)
    parser.add_argument("--audit-negative-harvest-limit", type=int, default=16)
    parser.add_argument("--worker-negative-harvest-limit", type=int, default=16)
    parser.add_argument("--current-probe-negative-harvest-limit", type=int, default=16)
    parser.add_argument("--current-probe-min-tasks", type=int, default=10)
    parser.add_argument("--current-probe-min-remaining-time", type=float, default=0.0)
    parser.add_argument(
        "--repeat-count",
        type=int,
        default=1,
        help="Run each instance/profile pair this many times; baseline comparisons stay within each repeat.",
    )
    parser.add_argument("--profile-mask-diagnostics", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if int(args.repeat_count) < 1:
        raise ValueError("--repeat-count must be >= 1")
    args.profiles = _expand_profile_args([str(profile) for profile in args.profiles])
    output_dir = Path(args.output_dir)
    log_dir = output_dir / "logs"
    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    summaries: list[dict[str, Any]] = []
    baseline_by_instance: dict[str, dict[str, Any]] = {}
    previous_rows_by_instance: dict[str, list[dict[str, Any]]] = {}
    for instance_key in _expand_instance_args(args.instances):
        instance_name, locator = _resolve_instance(instance_key)
        for repeat_index in range(int(args.repeat_count)):
            repeat_key = f"{instance_name}__repeat_{repeat_index}"
            for profile in args.profiles:
                if profile not in VALID_PROFILES:
                    raise ValueError(
                        f"Unknown profile {profile!r}; expected one of {VALID_PROFILES}"
                    )
                auto_residual_target = _derive_auto_residual_target(
                    previous_rows_by_instance.get(repeat_key, []),
                    profile=profile,
                )
                row = _run_profile(
                    instance_name,
                    locator,
                    profile,
                    args,
                    log_dir=log_dir,
                    auto_residual_target=auto_residual_target,
                    repeat_index=repeat_index,
                )
                if profile == "baseline":
                    baseline_by_instance[repeat_key] = row
                    row["official_unchanged_vs_baseline"] = True
                    row["official_result_changed_vs_baseline"] = False
                    row["objective_mismatch_vs_baseline"] = False
                    row["improvement_class"] = "baseline"
                else:
                    _apply_baseline_comparison(baseline_by_instance.get(repeat_key), row)
                _apply_pivot_recommendation(row)
                summaries.append(row)
                previous_rows_by_instance.setdefault(repeat_key, []).append(row)
                if not bool(args.quiet):
                    print(
                        f"{instance_name}/r{repeat_index}/{profile}: "
                        f"status={row['official_status']} "
                        f"pricing={row['official_pricing_state']} "
                        f"audit={row['pulse_audit_status']} "
                        f"severity={row['pulse_audit_disagreement_severity']} "
                        f"unchanged={row['official_unchanged_vs_baseline']}",
                        flush=True,
                )

    summary_json = output_dir / "summary.json"
    summary_csv = output_dir / "summary.csv"
    summary_json.write_text(json.dumps(summaries, indent=2, ensure_ascii=False), encoding="utf-8")
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(SUMMARY_FIELDS))
        writer.writeheader()
        writer.writerows([{key: row.get(key) for key in SUMMARY_FIELDS} for row in summaries])
    print(f"Sharded Pulse calibration summary written: {summary_json}")
    print(f"Sharded Pulse calibration CSV written: {summary_csv}")


def _resolve_instance(instance: str) -> tuple[str, str]:
    if instance in INSTANCE_PRESETS:
        return instance, INSTANCE_PRESETS[instance]
    path = Path(instance)
    if path.exists():
        return path.stem.replace("_logical_graph", ""), str(path)
    raise ValueError(f"Unknown instance {instance!r}; expected preset or existing logical graph path")


def _expand_instance_args(instances: list[str]) -> list[str]:
    expanded: list[str] = []
    seen: set[str] = set()

    def add(item: str) -> None:
        if item in INSTANCE_GROUPS:
            for child in INSTANCE_GROUPS[item]:
                add(child)
            return
        key = item if item in INSTANCE_PRESETS else str(Path(item))
        if key in seen:
            return
        seen.add(key)
        expanded.append(item)

    for instance in instances:
        add(str(instance))
    return expanded


def _expand_profile_args(profiles: list[str]) -> list[str]:
    expanded: list[str] = []
    seen: set[str] = set()

    def add(item: str) -> None:
        if item in PROFILE_GROUPS:
            for child in PROFILE_GROUPS[item]:
                add(child)
            return
        if item in seen:
            return
        seen.add(item)
        expanded.append(item)

    for profile in profiles:
        add(str(profile))
    return expanded


def _run_profile(
    instance_name: str,
    locator: str,
    profile: str,
    args: argparse.Namespace,
    *,
    log_dir: Path,
    auto_residual_target: dict[str, Any] | None = None,
    repeat_index: int = 0,
) -> dict[str, Any]:
    data = load_future_data(locator)
    _clear_sequence_resource_precheck_cache()
    config = _base_config(args)
    _apply_profile(config, profile, args, task_count=len(tuple(data.tasks)))
    auto_residual_target = auto_residual_target or {}
    auto_residual_target_applied = _apply_auto_residual_target_to_config(
        config,
        auto_residual_target,
    )
    if (
        bool(config.get("journey_sharded_pulse_hidden_negative_worker_requires_auto_residual_target", False))
        and not bool(auto_residual_target_applied)
    ):
        config["journey_sharded_pulse_hidden_negative_worker_enabled"] = False
    data, _fleet_diag = apply_fleet_bound_override(data, config)
    log_path = _run_log_path(
        log_dir,
        instance_name,
        profile,
        repeat_count=int(getattr(args, "repeat_count", 1)),
        repeat_index=int(repeat_index),
    )
    logger = FutureLogger(log_path, console=False)
    try:
        result = solve_bpc_future_journey(data, config, logger=logger)
    finally:
        logger.close()
        _clear_sequence_resource_precheck_cache()
    records = _read_jsonl(log_path)
    official_pricing = _last_official_pricing(records)
    pool_structure = _pool_structure_metrics(records)
    early_column_trajectory = _early_column_trajectory_metrics(records)
    dual_stabilization = _dual_stabilization_metrics(records)
    profile_dp_tail = _profile_dp_tail_metrics(records)
    audits = [record for record in records if record.get("event") == "journey_sharded_pulse_audit"]
    audit = _last_real_audit(audits) or (audits[-1] if audits else {})
    worker_events = [
        record
        for record in records
        if record.get("event") == "journey_sharded_pulse_hidden_negative_worker"
    ]
    worker_pricing_records = [
        record
        for record in records
        if record.get("event") == "journey_pricing"
        and str(record.get("pricing_kind", "")) == "sharded_pulse_hidden_negative_worker"
    ]
    first_worker_pricing = worker_pricing_records[0] if worker_pricing_records else {}
    worker = _last_real_worker(worker_events) or (worker_events[-1] if worker_events else {})
    worker_additions = _worker_addition_records(records)
    worker_continue_same_iteration_events = [
        record
        for record in records
        if record.get("event") == "journey_sharded_pulse_worker_continue_same_iteration"
    ]
    worker_followup = _worker_followup_metrics(records)
    residual_replay_events = [
        record
        for record in records
        if record.get("event") == "journey_pulse_residual_replay_diagnostic"
    ]
    first_residual_replay = residual_replay_events[0] if residual_replay_events else {}
    legacy_records = _legacy_final_judge_records(records)
    generated_sequences = _sum_pricing_field(records, "generated_sequences")
    evaluated_timed_trips = _sum_pricing_field(records, "evaluated_timed_trips")
    worker_bound_pruned = sum(_as_int(event.get("pulse_worker_bound_pruned")) for event in worker_events)
    worker_archive_pruned = sum(_as_int(event.get("pulse_worker_archive_pruned")) for event in worker_events)
    worker_time_window_pruned = sum(
        _as_int(event.get("pulse_worker_time_window_pruned")) for event in worker_events
    )
    worker_return_pruned = sum(_as_int(event.get("pulse_worker_return_pruned")) for event in worker_events)
    worker_pruned_total = worker_bound_pruned + worker_archive_pruned + worker_time_window_pruned + worker_return_pruned
    worker_added_journeys = _worker_added_journeys(records)
    worker_returned_journeys = sum(
        _as_int(event.get("pulse_worker_returned_journeys"))
        for event in worker_events
    )
    worker_context_hash = _last_nonempty_record_field(
        worker_events,
        "pulse_worker_context_hash",
    ) or str(worker.get("pulse_worker_context_hash", ""))
    completion_retry_count = _completion_bound_retry_count(records)
    completion_retry_time = _completion_bound_retry_time(records)
    hidden_negative_audit_count = len(
        [record for record in records if record.get("event") == "hidden_negative_audit"]
    )
    official_negative_task_sets = _record_task_set_samples(
        official_pricing,
        "negative_journey_task_set_samples",
    )
    official_negative_first_task_set = (
        official_negative_task_sets[0] if official_negative_task_sets else tuple()
    )
    official_negative_top_overlap = _best_task_set_overlap(
        official_negative_first_task_set,
        _profile_dp_top_mask_task_sets(official_pricing),
    )
    inferred_skip_reason = ""
    if profile != "baseline" and not audits:
        inferred_skip_reason = "legacy_not_called"
    auto_target_sequence = tuple(int(task) for task in auto_residual_target.get("sequence", tuple()) or tuple())
    auto_candidate_sequence = _parse_int_sequence_value(
        auto_residual_target.get("candidate_sequence", tuple())
        or auto_residual_target.get("blocked_sequence", tuple())
        or auto_residual_target.get("sequence", tuple())
    )
    auto_target_source_context_hash = str(auto_residual_target.get("source_context_hash", ""))
    row = {
        "instance": instance_name,
        "scale": len(tuple(data.tasks)),
        "profile": profile,
        "repeat_index": int(repeat_index),
        "tasks": len(tuple(data.tasks)),
        "status": str(result.status),
        "wall_time": result.solving_time,
        "primal": result.primal_bound,
        "dual_bound": result.dual_bound,
        "gap": result.gap,
        "pricing_state": official_pricing.get("pricing_state", ""),
        "best_rc": official_pricing.get("best_reduced_cost"),
        "official_status": str(result.status),
        "official_primal_bound": result.primal_bound,
        "official_dual_bound": result.dual_bound,
        "official_gap": result.gap,
        "official_pricing_state": official_pricing.get("pricing_state", ""),
        "official_best_rc": official_pricing.get("best_reduced_cost"),
        "official_negative_journey_task_set_count": _as_int(
            official_pricing.get("negative_journey_task_set_count")
        ),
        "official_negative_journey_task_set_hash": str(
            official_pricing.get("negative_journey_task_set_hash", "")
        ),
        "official_negative_journey_task_set_samples": _compact_json_string(
            official_pricing.get("negative_journey_task_set_samples")
        ),
        "official_negative_journey_sequence_samples": _compact_json_string(
            official_pricing.get("negative_journey_sequence_samples")
        ),
        "official_negative_journey_signature_samples": _compact_json_string(
            official_pricing.get("negative_journey_signature_samples")
        ),
        "official_negative_first_task_set": _task_set_string(
            official_negative_first_task_set
        ),
        "official_negative_first_task_count": len(official_negative_first_task_set),
        "official_negative_profile_dp_top_overlap": official_negative_top_overlap["overlap"],
        "official_negative_profile_dp_top_jaccard": official_negative_top_overlap["jaccard"],
        "official_negative_profile_dp_top_relation": official_negative_top_overlap["relation"],
        "official_negative_profile_dp_top_exact": bool(
            official_negative_first_task_set
            and any(
                tuple(official_negative_first_task_set) == tuple(task_set)
                for task_set in _profile_dp_top_mask_task_sets(official_pricing)
            )
        ),
        **dual_stabilization,
        "official_result_changed_vs_baseline": False,
        "objective_mismatch_vs_baseline": False,
        "official_unchanged_vs_baseline": False,
        "solving_time": result.solving_time,
        "rmp_solves": result.rmp_solves,
        "root_rmp_rounds": result.rmp_solves,
        "pricing_calls": result.pricing_calls,
        "exact_pricing_calls": result.exact_pricing_calls,
        "columns": result.columns,
        **pool_structure,
        **early_column_trajectory,
        "generated_sequences": generated_sequences,
        "evaluated_timed_trips": evaluated_timed_trips,
        "legacy_final_judge_calls": len(legacy_records),
        "legacy_final_judge_after_worker_calls": worker_followup["legacy_after_worker_calls"],
        "final_judge_max_single_call_time": max(
            (float(record.get("time") or 0.0) for record in legacy_records),
            default=0.0,
        ),
        "exact_completion_bound_retry_count": completion_retry_count,
        "exact_completion_bound_retry_time": completion_retry_time,
        "completion_bound_retry_count": completion_retry_count,
        "exact_retry_calls": len(
            [
                record
                for record in records
                if record.get("event") == "journey_pricing"
                and "retry" in str(record.get("pricing_kind", ""))
            ]
        ),
        **profile_dp_tail,
        "hidden_negative_audit_events": hidden_negative_audit_count,
        "hidden_negative_audit_count": hidden_negative_audit_count,
        "audit_events": len(audits),
        "pulse_audit_skipped": bool(audit.get("pulse_audit_skipped", False)) or bool(inferred_skip_reason),
        "pulse_audit_skip_reason": str(audit.get("pulse_audit_skip_reason", inferred_skip_reason)),
        "pulse_audit_trigger": str(audit.get("pulse_audit_trigger", "")),
        "pulse_audit_status": str(audit.get("pulse_audit_status", "")),
        "pulse_audit_comparison_type": str(audit.get("pulse_audit_comparison_type", "")),
        "pulse_audit_disagreement_severity": str(audit.get("pulse_audit_disagreement_severity", "")),
        "pulse_audit_time": audit.get("pulse_audit_time"),
        "pulse_audit_recursions": _as_int(audit.get("pulse_audit_recursions")),
        "pulse_audit_shards_total": _as_int(audit.get("pulse_audit_shards_total")),
        "pulse_audit_shards_certified": _as_int(audit.get("pulse_audit_shards_certified")),
        "pulse_audit_shards_incomplete": _as_int(audit.get("pulse_audit_shards_incomplete")),
        "pulse_audit_shards_negative": _as_int(audit.get("pulse_audit_shards_negative")),
        "pulse_audit_shards_refined": _as_int(audit.get("pulse_audit_shards_refined")),
        "pulse_audit_low_roi_shards": _as_int(audit.get("pulse_audit_low_roi_shards")),
        "pulse_audit_bound_pruned": _as_int(audit.get("pulse_audit_bound_pruned")),
        "pulse_audit_archive_pruned": _as_int(audit.get("pulse_audit_archive_pruned")),
        "pulse_audit_time_window_pruned": _as_int(audit.get("pulse_audit_time_window_pruned")),
        "pulse_audit_energy_pruned": _as_int(audit.get("pulse_audit_energy_pruned")),
        "pulse_audit_return_pruned": _as_int(audit.get("pulse_audit_return_pruned")),
        "pulse_audit_capacity_pruned": _as_int(audit.get("pulse_audit_capacity_pruned")),
        "pulse_audit_pulse_energy_pruned": _as_int(audit.get("pulse_audit_pulse_energy_pruned")),
        "pulse_audit_negative_pool_size": _as_int(audit.get("pulse_audit_negative_pool_size")),
        "pulse_audit_harvested_count": _as_int(audit.get("pulse_audit_harvested_count")),
        "worker_events": len(worker_events),
        "pulse_worker_skipped": bool(worker.get("pulse_worker_skipped", False)),
        "pulse_worker_skip_reason": str(worker.get("pulse_worker_skip_reason", "")),
        "pulse_worker_trigger": str(worker.get("pulse_worker_trigger", "")),
        "pulse_worker_signal_source": str(worker.get("pulse_worker_signal_source", "")),
        "pulse_worker_previous_audit_signal": any(
            bool(event.get("pulse_worker_previous_audit_signal", False))
            for event in worker_events
        ),
        "pulse_worker_current_probe_signal": any(
            bool(event.get("pulse_worker_current_probe_signal", False))
            for event in worker_events
        ),
        "pulse_worker_status": str(worker.get("pulse_worker_status", "")),
        "worker_triggered": any(
            not bool(event.get("pulse_worker_skipped", False)) for event in worker_events
        ),
        "worker_skip_reason": str(worker.get("pulse_worker_skip_reason", "")),
        "worker_signal_source": str(worker.get("pulse_worker_signal_source", "")),
        "worker_context_hash": worker_context_hash,
        "worker_returned_journeys": worker_returned_journeys,
        "worker_added_journeys": worker_added_journeys,
        "worker_added_new_task_sets": sum(
            _as_int(record.get("new_task_set_count")) for record in worker_additions
        ),
        "worker_added_new_task_set_count": sum(
            _as_int(record.get("new_task_set_count")) for record in worker_additions
        ),
        "worker_added_replacement_count": sum(
            _as_int(record.get("replacement_journeys")) for record in worker_additions
        ),
        "worker_added_support_changing_count": sum(
            _as_int(record.get("active_changed_task_set_count")) for record in worker_additions
        ),
        "worker_addition_productivity_class": "|".join(
            str(record.get("addition_productivity_class", ""))
            for record in worker_additions
            if str(record.get("addition_productivity_class", ""))
        ),
        "worker_time": sum(
            float(event.get("pulse_worker_time") or 0.0)
            for event in worker_events
        ),
        "worker_recursions": sum(
            _as_int(event.get("pulse_worker_recursions"))
            for event in worker_events
        ),
        "worker_pruned_total": worker_pruned_total,
        "worker_bound_pruned": worker_bound_pruned,
        "worker_archive_pruned": worker_archive_pruned,
        "worker_time_window_pruned": worker_time_window_pruned,
        "worker_return_pruned": worker_return_pruned,
        "worker_harvested_count": sum(
            _as_int(event.get("pulse_worker_harvested_count"))
            for event in worker_events
        ),
        "worker_stop_after_first_negative": any(
            bool(event.get("pulse_worker_stop_after_first_negative", False))
            for event in worker_events
        ),
        "worker_task_ordering": "|".join(
            dict.fromkeys(
                str(event.get("pulse_worker_task_ordering", ""))
                for event in worker_events
                if str(event.get("pulse_worker_task_ordering", ""))
            )
        ),
        "worker_target_sequence": str(worker.get("pulse_worker_target_sequence", "")),
        "worker_target_first_task_priority_enabled": bool(
            worker.get("pulse_worker_target_first_task_priority_enabled", False)
        ),
        "worker_target_first_task_priority_sequence": str(
            worker.get("pulse_worker_target_first_task_priority_sequence", "")
        ),
        "worker_target_transition_priority_enabled": bool(
            worker.get("pulse_worker_target_transition_priority_enabled", False)
        ),
        "worker_target_transition_priority_sequence": str(
            worker.get("pulse_worker_target_transition_priority_sequence", "")
        ),
        "worker_target_arc_option_priority_enabled": bool(
            worker.get("pulse_worker_target_arc_option_priority_enabled", False)
        ),
        "worker_target_arc_option_priority_sequence": str(
            worker.get("pulse_worker_target_arc_option_priority_sequence", "")
        ),
        "worker_target_sequence_reached_prefix_len": _as_int(
            worker.get("pulse_worker_target_sequence_reached_prefix_len")
        ),
        "worker_target_sequence_completed": bool(
            worker.get("pulse_worker_target_sequence_completed", False)
        ),
        "worker_target_sequence_materialized": bool(
            worker.get("pulse_worker_target_sequence_materialized", False)
        ),
        "worker_target_sequence_negative": bool(
            worker.get("pulse_worker_target_sequence_negative", False)
        ),
        "worker_target_sequence_blocked_reason": str(
            worker.get("pulse_worker_target_sequence_blocked_reason", "")
        ),
        "worker_target_sequence_blocked_prefix": str(
            worker.get("pulse_worker_target_sequence_blocked_prefix", "")
        ),
        "worker_target_sequence_blocked_next_task": worker.get(
            "pulse_worker_target_sequence_blocked_next_task"
        ),
        "worker_target_sequence_transition_attempts": _as_int(
            worker.get("pulse_worker_target_sequence_transition_attempts")
        ),
        "worker_target_sequence_transition_accepted": _as_int(
            worker.get("pulse_worker_target_sequence_transition_accepted")
        ),
        "worker_target_sequence_prune_reason_counts": str(
            worker.get("pulse_worker_target_sequence_prune_reason_counts", "")
        ),
        "worker_target_path_diagnostics_enabled": bool(
            worker.get("pulse_worker_target_path_diagnostics_enabled", False)
        ),
        "worker_target_path_prefix_samples": str(
            worker.get("pulse_worker_target_path_prefix_samples", "")
        ),
        "worker_target_path_blocked_samples": str(
            worker.get("pulse_worker_target_path_blocked_samples", "")
        ),
        "auto_residual_target_applied": bool(auto_residual_target_applied),
        "auto_residual_target_sequence": _task_set_string(auto_target_sequence),
        "auto_residual_target_source_profile": str(
            auto_residual_target.get("source_profile", "")
        ),
        "auto_residual_target_source_context_hash": auto_target_source_context_hash,
        "auto_residual_target_context_match": False,
        "auto_residual_target_candidate_sequence": _task_set_string(auto_candidate_sequence),
        "auto_residual_target_source_gate": str(auto_residual_target.get("source_gate", "")),
        "auto_residual_target_source_gate_reason": str(
            auto_residual_target.get("source_gate_reason", "")
        ),
        "active_residual_source_search_candidate_count": _as_int(
            auto_residual_target.get("source_search_candidate_count")
        ),
        "active_residual_source_search_passed_count": _as_int(
            auto_residual_target.get("source_search_passed_count")
        ),
        "active_residual_source_search_blocked_count": _as_int(
            auto_residual_target.get("source_search_blocked_count")
        ),
        "active_residual_source_search_blocked_disjoint_count": _as_int(
            auto_residual_target.get("source_search_blocked_disjoint_count")
        ),
        "active_residual_source_search_blocked_no_active_count": _as_int(
            auto_residual_target.get("source_search_blocked_no_active_count")
        ),
        "active_residual_source_search_blocked_relation_count": _as_int(
            auto_residual_target.get("source_search_blocked_relation_count")
        ),
        "active_residual_source_search_first_passed_profile": str(
            auto_residual_target.get("source_search_first_passed_profile", "")
        ),
        "active_residual_source_search_first_passed_sequence": _task_set_string(
            _parse_int_sequence_value(
                auto_residual_target.get("source_search_first_passed_sequence", tuple())
            )
        ),
        "active_residual_source_search_first_passed_relation": str(
            auto_residual_target.get("source_search_first_passed_relation", "")
        ),
        "active_residual_source_search_first_passed_context_hash": str(
            auto_residual_target.get("source_search_first_passed_context_hash", "")
        ),
        "active_residual_source_search_first_blocked_profile": str(
            auto_residual_target.get("source_search_first_blocked_profile", "")
        ),
        "active_residual_source_search_first_blocked_sequence": _task_set_string(
            _parse_int_sequence_value(
                auto_residual_target.get("source_search_first_blocked_sequence", tuple())
            )
        ),
        "active_residual_source_search_first_blocked_reason": str(
            auto_residual_target.get("source_search_first_blocked_reason", "")
        ),
        "active_residual_source_search_outcome_class": str(
            auto_residual_target.get("source_search_outcome_class", "")
        ),
        "active_residual_source_search_recommendation": str(
            auto_residual_target.get("source_search_recommendation", "")
        ),
        "worker_shards_total": sum(
            _as_int(event.get("pulse_worker_shards_total"))
            for event in worker_events
        ),
        "worker_shards_certified": sum(
            _as_int(event.get("pulse_worker_shards_certified"))
            for event in worker_events
        ),
        "worker_shards_incomplete": sum(
            _as_int(event.get("pulse_worker_shards_incomplete"))
            for event in worker_events
        ),
        "worker_shards_negative": sum(
            _as_int(event.get("pulse_worker_shards_negative"))
            for event in worker_events
        ),
        "worker_shards_refined": sum(
            _as_int(event.get("pulse_worker_shards_refined"))
            for event in worker_events
        ),
        "worker_low_roi_shards": sum(
            _as_int(event.get("pulse_worker_low_roi_shards"))
            for event in worker_events
        ),
        "worker_negative_journey_sequence_samples": _record_sequence_samples_string(
            first_worker_pricing,
            "negative_journey_sequence_samples",
        ),
        "worker_negative_journey_signature_samples": _record_signature_samples_string(
            first_worker_pricing,
            "negative_journey_signature_samples",
        ),
        "worker_negative_pool_task_set_samples": worker_followup["worker_negative_pool_task_set_samples"],
        "worker_negative_pool_sequence_samples": worker_followup["worker_negative_pool_sequence_samples"],
        "worker_negative_pool_signature_samples": worker_followup["worker_negative_pool_signature_samples"],
        "worker_harvested_task_set_samples": worker_followup["worker_harvested_task_set_samples"],
        "worker_harvested_sequence_samples": worker_followup["worker_harvested_sequence_samples"],
        "worker_harvested_signature_samples": worker_followup["worker_harvested_signature_samples"],
        "worker_returned_candidate_task_set_samples": worker_followup[
            "worker_returned_candidate_task_set_samples"
        ],
        "worker_returned_candidate_sequence_samples": worker_followup[
            "worker_returned_candidate_sequence_samples"
        ],
        "worker_returned_candidate_signature_samples": worker_followup[
            "worker_returned_candidate_signature_samples"
        ],
        "worker_continue_same_iteration_events": len(worker_continue_same_iteration_events),
        "pulse_worker_returned_journeys": worker_returned_journeys,
        "pulse_worker_added_journeys": worker_added_journeys,
        "pulse_worker_added_new_journeys": sum(
            _as_int(record.get("new_journeys")) for record in worker_additions
        ),
        "pulse_worker_added_replacement_journeys": sum(
            _as_int(record.get("replacement_journeys")) for record in worker_additions
        ),
        "pulse_worker_added_new_task_set_count": sum(
            _as_int(record.get("new_task_set_count")) for record in worker_additions
        ),
        "pulse_worker_added_replacement_task_set_count": sum(
            _as_int(record.get("replacement_task_set_count")) for record in worker_additions
        ),
        "pulse_worker_added_support_changing_count": sum(
            _as_int(record.get("active_changed_task_set_count")) for record in worker_additions
        ),
        "pulse_worker_addition_productivity_class": "|".join(
            str(record.get("addition_productivity_class", ""))
            for record in worker_additions
            if str(record.get("addition_productivity_class", ""))
        ),
        "pulse_worker_impact_filter_enabled": any(
            bool(event.get("pulse_worker_impact_filter_enabled", False))
            for event in worker_events
        ),
        "pulse_worker_impact_filter_mode": "|".join(
            dict.fromkeys(
                str(event.get("pulse_worker_impact_filter_mode", ""))
                for event in worker_events
                if str(event.get("pulse_worker_impact_filter_mode", ""))
                and str(event.get("pulse_worker_impact_filter_mode", "")) != "off"
            )
        ),
        "pulse_worker_impact_filter_candidate_count": sum(
            _as_int(event.get("pulse_worker_impact_filter_candidate_count"))
            for event in worker_events
        ),
        "pulse_worker_impact_filter_selected_count": sum(
            _as_int(event.get("pulse_worker_impact_filter_selected_count"))
            for event in worker_events
        ),
        "pulse_worker_impact_filter_dropped_count": sum(
            _as_int(event.get("pulse_worker_impact_filter_dropped_count"))
            for event in worker_events
        ),
        "pulse_worker_impact_filter_selected_new_task_set_count": sum(
            _as_int(event.get("pulse_worker_impact_filter_selected_new_task_set_count"))
            for event in worker_events
        ),
        "pulse_worker_impact_filter_selected_replacement_task_set_count": sum(
            _as_int(event.get("pulse_worker_impact_filter_selected_replacement_task_set_count"))
            for event in worker_events
        ),
        "pulse_worker_impact_filter_selected_active_support_changing_count": sum(
            _as_int(event.get("pulse_worker_impact_filter_selected_active_support_changing_count"))
            for event in worker_events
        ),
        "pulse_worker_impact_filter_selected_weak_replacement_count": sum(
            _as_int(event.get("pulse_worker_impact_filter_selected_weak_replacement_count"))
            for event in worker_events
        ),
        "pulse_worker_impact_filter_min_true_rc": "|".join(
            dict.fromkeys(
                str(event.get("pulse_worker_impact_filter_min_true_rc"))
                for event in worker_events
                if event.get("pulse_worker_impact_filter_min_true_rc") is not None
            )
        ),
        "pulse_worker_impact_filter_selected_best_true_rc": min(
            (
                float(event.get("pulse_worker_impact_filter_selected_best_true_rc"))
                for event in worker_events
                if event.get("pulse_worker_impact_filter_selected_best_true_rc") is not None
            ),
            default=None,
        ),
        "pulse_worker_impact_filter_rc_threshold_dropped_count": sum(
            _as_int(event.get("pulse_worker_impact_filter_rc_threshold_dropped_count"))
            for event in worker_events
        ),
        "pulse_worker_shards_total": sum(
            _as_int(event.get("pulse_worker_shards_total"))
            for event in worker_events
        ),
        "pulse_worker_shards_certified": sum(
            _as_int(event.get("pulse_worker_shards_certified"))
            for event in worker_events
        ),
        "pulse_worker_shards_incomplete": sum(
            _as_int(event.get("pulse_worker_shards_incomplete"))
            for event in worker_events
        ),
        "pulse_worker_shards_negative": sum(
            _as_int(event.get("pulse_worker_shards_negative"))
            for event in worker_events
        ),
        "pulse_worker_shards_refined": sum(
            _as_int(event.get("pulse_worker_shards_refined"))
            for event in worker_events
        ),
        "pulse_worker_low_roi_shards": sum(
            _as_int(event.get("pulse_worker_low_roi_shards"))
            for event in worker_events
        ),
        "pulse_worker_followup_reserve_min_time": "|".join(
            dict.fromkeys(
                str(event.get("pulse_worker_followup_reserve_min_time"))
                for event in worker_events
                if event.get("pulse_worker_followup_reserve_min_time") is not None
            )
        ),
        "pulse_worker_followup_reserve_remaining_time": min(
            (
                float(event.get("pulse_worker_followup_reserve_remaining_time"))
                for event in worker_events
                if event.get("pulse_worker_followup_reserve_remaining_time") is not None
            ),
            default=None,
        ),
        "pulse_worker_followup_reserve_dropped_journeys": sum(
            _as_int(event.get("pulse_worker_followup_reserve_dropped_journeys"))
            for event in worker_events
        ),
        "followup_rmp_objective_delta": worker_followup["next_rmp_objective_delta"],
        "followup_dual_l1_delta": worker_followup["next_dual_l1_delta"],
        "followup_worker_changed_task_set_count": worker_followup["worker_changed_task_set_count"],
        "followup_worker_active_task_set_count": worker_followup["worker_active_task_set_count"],
        "followup_worker_inactive_task_set_count": worker_followup["worker_inactive_task_set_count"],
        "followup_worker_active_task_set_ratio": worker_followup["worker_active_task_set_ratio"],
        "followup_wall_after_worker": worker_followup["wall_after_worker"],
        "followup_pricing_calls": worker_followup["pricing_calls"],
        "followup_heuristic_pricing_calls": worker_followup["heuristic_pricing_calls"],
        "followup_exact_pricing_calls": worker_followup["exact_pricing_calls"],
        "followup_exact_retry_pricing_calls": worker_followup["exact_retry_pricing_calls"],
        "followup_generated_sequences": worker_followup["generated_sequences"],
        "followup_evaluated_timed_trips": worker_followup["evaluated_timed_trips"],
        "followup_legacy_final_judge_calls": worker_followup["legacy_after_worker_calls"],
        "followup_legacy_final_judge_time": worker_followup["legacy_after_worker_time"],
        "followup_completion_retry_count": worker_followup["completion_retry_after_worker_count"],
        "followup_completion_retry_time": worker_followup["completion_retry_after_worker_time"],
        "followup_hidden_negative_audit_count": worker_followup["hidden_negative_after_worker_count"],
        "followup_worker_negative_after_worker_count": worker_followup["worker_negative_after_worker_count"],
        "followup_last_pricing_kind": worker_followup["last_pricing_kind"],
        "followup_last_pricing_state": worker_followup["last_pricing_state"],
        "followup_last_pricing_reason": worker_followup["last_pricing_reason"],
        "followup_last_best_rc": worker_followup["last_best_rc"],
        "followup_tail_outcome": worker_followup["tail_outcome"],
        "followup_negative_pricing_calls": worker_followup["negative_pricing_calls"],
        "followup_incomplete_pricing_calls": worker_followup["incomplete_pricing_calls"],
        "followup_min_best_rc": worker_followup["min_best_rc"],
        "followup_pricing_state_sequence": worker_followup["pricing_state_sequence"],
        "followup_first_negative_cg_iter": worker_followup["first_negative_cg_iter"],
        "followup_first_negative_pricing_kind": worker_followup["first_negative_pricing_kind"],
        "followup_first_negative_best_rc": worker_followup["first_negative_best_rc"],
        "followup_first_negative_task_set_hash": worker_followup["first_negative_task_set_hash"],
        "followup_first_negative_task_set": worker_followup["first_negative_task_set"],
        "followup_first_negative_task_count": worker_followup["first_negative_task_count"],
        "followup_first_negative_sequence": worker_followup["first_negative_sequence"],
        "followup_first_negative_signature_sample": worker_followup["first_negative_signature_sample"],
        "followup_first_negative_overlap_to_worker": worker_followup[
            "first_negative_overlap_to_worker"
        ],
        "followup_first_negative_jaccard_to_worker": worker_followup[
            "first_negative_jaccard_to_worker"
        ],
        "followup_first_negative_relation_to_worker": worker_followup[
            "first_negative_relation_to_worker"
        ],
        "worker_vs_ordinary_first_worker_task_set": worker_followup[
            "worker_vs_ordinary_first_worker_task_set"
        ],
        "worker_vs_ordinary_first_followup_task_set": worker_followup[
            "worker_vs_ordinary_first_followup_task_set"
        ],
        "worker_vs_ordinary_task_set_overlap": worker_followup[
            "worker_vs_ordinary_task_set_overlap"
        ],
        "worker_vs_ordinary_task_set_jaccard": worker_followup[
            "worker_vs_ordinary_task_set_jaccard"
        ],
        "worker_vs_ordinary_task_set_relation": worker_followup[
            "worker_vs_ordinary_task_set_relation"
        ],
        "worker_vs_ordinary_disjoint": worker_followup["worker_vs_ordinary_disjoint"],
        "worker_vs_ordinary_worker_task_count": worker_followup[
            "worker_vs_ordinary_worker_task_count"
        ],
        "worker_vs_ordinary_followup_task_count": worker_followup[
            "worker_vs_ordinary_followup_task_count"
        ],
        "worker_vs_ordinary_task_count_delta": worker_followup[
            "worker_vs_ordinary_task_count_delta"
        ],
        "worker_vs_ordinary_worker_added_before_followup": worker_followup[
            "worker_vs_ordinary_worker_added_before_followup"
        ],
        "worker_vs_ordinary_followup_returned_after_worker": worker_followup[
            "worker_vs_ordinary_followup_returned_after_worker"
        ],
        "worker_vs_ordinary_contrast_class": worker_followup[
            "worker_vs_ordinary_contrast_class"
        ],
        "worker_vs_ordinary_negative_pool_overlap": worker_followup[
            "worker_vs_ordinary_negative_pool_overlap"
        ],
        "worker_vs_ordinary_negative_pool_jaccard": worker_followup[
            "worker_vs_ordinary_negative_pool_jaccard"
        ],
        "worker_vs_ordinary_negative_pool_relation": worker_followup[
            "worker_vs_ordinary_negative_pool_relation"
        ],
        "worker_vs_ordinary_negative_pool_exact": worker_followup[
            "worker_vs_ordinary_negative_pool_exact"
        ],
        "worker_vs_ordinary_harvested_overlap": worker_followup[
            "worker_vs_ordinary_harvested_overlap"
        ],
        "worker_vs_ordinary_harvested_jaccard": worker_followup[
            "worker_vs_ordinary_harvested_jaccard"
        ],
        "worker_vs_ordinary_harvested_relation": worker_followup[
            "worker_vs_ordinary_harvested_relation"
        ],
        "worker_vs_ordinary_harvested_exact": worker_followup[
            "worker_vs_ordinary_harvested_exact"
        ],
        "worker_vs_ordinary_returned_candidate_overlap": worker_followup[
            "worker_vs_ordinary_returned_candidate_overlap"
        ],
        "worker_vs_ordinary_returned_candidate_jaccard": worker_followup[
            "worker_vs_ordinary_returned_candidate_jaccard"
        ],
        "worker_vs_ordinary_returned_candidate_relation": worker_followup[
            "worker_vs_ordinary_returned_candidate_relation"
        ],
        "worker_vs_ordinary_returned_candidate_exact": worker_followup[
            "worker_vs_ordinary_returned_candidate_exact"
        ],
        "worker_target_sequence_task_set": worker_followup[
            "worker_target_sequence_task_set"
        ],
        "worker_target_negative_pool_overlap": worker_followup[
            "worker_target_negative_pool_overlap"
        ],
        "worker_target_negative_pool_jaccard": worker_followup[
            "worker_target_negative_pool_jaccard"
        ],
        "worker_target_negative_pool_relation": worker_followup[
            "worker_target_negative_pool_relation"
        ],
        "worker_target_negative_pool_exact": worker_followup[
            "worker_target_negative_pool_exact"
        ],
        "worker_target_harvested_overlap": worker_followup[
            "worker_target_harvested_overlap"
        ],
        "worker_target_harvested_jaccard": worker_followup[
            "worker_target_harvested_jaccard"
        ],
        "worker_target_harvested_relation": worker_followup[
            "worker_target_harvested_relation"
        ],
        "worker_target_harvested_exact": worker_followup[
            "worker_target_harvested_exact"
        ],
        "worker_target_returned_candidate_overlap": worker_followup[
            "worker_target_returned_candidate_overlap"
        ],
        "worker_target_returned_candidate_jaccard": worker_followup[
            "worker_target_returned_candidate_jaccard"
        ],
        "worker_target_returned_candidate_relation": worker_followup[
            "worker_target_returned_candidate_relation"
        ],
        "worker_target_returned_candidate_exact": worker_followup[
            "worker_target_returned_candidate_exact"
        ],
        "followup_first_negative_profile_dp_top_overlap": worker_followup[
            "first_negative_profile_dp_top_overlap"
        ],
        "followup_first_negative_profile_dp_top_jaccard": worker_followup[
            "first_negative_profile_dp_top_jaccard"
        ],
        "followup_first_negative_profile_dp_top_relation": worker_followup[
            "first_negative_profile_dp_top_relation"
        ],
        "followup_first_negative_profile_dp_top_exact": worker_followup[
            "first_negative_profile_dp_top_exact"
        ],
        "followup_first_negative_profile_reachable_overlap": worker_followup[
            "first_negative_profile_reachable_overlap"
        ],
        "followup_first_negative_profile_reachable_jaccard": worker_followup[
            "first_negative_profile_reachable_jaccard"
        ],
        "followup_first_negative_profile_reachable_relation": worker_followup[
            "first_negative_profile_reachable_relation"
        ],
        "followup_first_negative_profile_reachable_exact": worker_followup[
            "first_negative_profile_reachable_exact"
        ],
        "followup_first_negative_profile_negative_overlap": worker_followup[
            "first_negative_profile_negative_overlap"
        ],
        "followup_first_negative_profile_negative_jaccard": worker_followup[
            "first_negative_profile_negative_jaccard"
        ],
        "followup_first_negative_profile_negative_relation": worker_followup[
            "first_negative_profile_negative_relation"
        ],
        "followup_first_negative_profile_negative_exact": worker_followup[
            "first_negative_profile_negative_exact"
        ],
        "followup_first_negative_profile_selected_overlap": worker_followup[
            "first_negative_profile_selected_overlap"
        ],
        "followup_first_negative_profile_selected_jaccard": worker_followup[
            "first_negative_profile_selected_jaccard"
        ],
        "followup_first_negative_profile_selected_relation": worker_followup[
            "first_negative_profile_selected_relation"
        ],
        "followup_first_negative_profile_selected_exact": worker_followup[
            "first_negative_profile_selected_exact"
        ],
        "followup_first_negative_profile_materialized_overlap": worker_followup[
            "first_negative_profile_materialized_overlap"
        ],
        "followup_first_negative_profile_materialized_jaccard": worker_followup[
            "first_negative_profile_materialized_jaccard"
        ],
        "followup_first_negative_profile_materialized_relation": worker_followup[
            "first_negative_profile_materialized_relation"
        ],
        "followup_first_negative_profile_materialized_exact": worker_followup[
            "first_negative_profile_materialized_exact"
        ],
        "followup_first_negative_profile_returned_overlap": worker_followup[
            "first_negative_profile_returned_overlap"
        ],
        "followup_first_negative_profile_returned_jaccard": worker_followup[
            "first_negative_profile_returned_jaccard"
        ],
        "followup_first_negative_profile_returned_relation": worker_followup[
            "first_negative_profile_returned_relation"
        ],
        "followup_first_negative_profile_returned_exact": worker_followup[
            "first_negative_profile_returned_exact"
        ],
        "followup_first_negative_profile_unmaterialized_overlap": worker_followup[
            "first_negative_profile_unmaterialized_overlap"
        ],
        "followup_first_negative_profile_unmaterialized_jaccard": worker_followup[
            "first_negative_profile_unmaterialized_jaccard"
        ],
        "followup_first_negative_profile_unmaterialized_relation": worker_followup[
            "first_negative_profile_unmaterialized_relation"
        ],
        "followup_first_negative_profile_unmaterialized_exact": worker_followup[
            "first_negative_profile_unmaterialized_exact"
        ],
        "followup_first_negative_profile_weak_filtered_overlap": worker_followup[
            "first_negative_profile_weak_filtered_overlap"
        ],
        "followup_first_negative_profile_weak_filtered_jaccard": worker_followup[
            "first_negative_profile_weak_filtered_jaccard"
        ],
        "followup_first_negative_profile_weak_filtered_relation": worker_followup[
            "first_negative_profile_weak_filtered_relation"
        ],
        "followup_first_negative_profile_weak_filtered_exact": worker_followup[
            "first_negative_profile_weak_filtered_exact"
        ],
        "followup_first_negative_profile_filtered_overlap": worker_followup[
            "first_negative_profile_filtered_overlap"
        ],
        "followup_first_negative_profile_filtered_jaccard": worker_followup[
            "first_negative_profile_filtered_jaccard"
        ],
        "followup_first_negative_profile_filtered_relation": worker_followup[
            "first_negative_profile_filtered_relation"
        ],
        "followup_first_negative_profile_filtered_exact": worker_followup[
            "first_negative_profile_filtered_exact"
        ],
        "followup_proof_tail_bridge_class": worker_followup["proof_tail_bridge_class"],
        "followup_proof_tail_bridge_reason": worker_followup["proof_tail_bridge_reason"],
        "followup_returned_residual_tail_class": worker_followup["returned_residual_tail_class"],
        "followup_returned_residual_tail_reason": worker_followup["returned_residual_tail_reason"],
        "followup_negative_task_set_sequence": worker_followup["negative_task_set_sequence"],
        "followup_negative_task_set_unique_count": worker_followup["negative_task_set_unique_count"],
        "followup_negative_task_set_repeat_count": worker_followup["negative_task_set_repeat_count"],
        "followup_first_negative_addition_productivity_class": worker_followup[
            "first_negative_addition_productivity_class"
        ],
        "followup_first_negative_added_journeys": worker_followup["first_negative_added_journeys"],
        "followup_first_negative_added_new_task_set_count": worker_followup[
            "first_negative_added_new_task_set_count"
        ],
        "followup_first_negative_added_replacement_count": worker_followup[
            "first_negative_added_replacement_count"
        ],
        "followup_first_negative_added_support_changing_count": worker_followup[
            "first_negative_added_support_changing_count"
        ],
        "followup_post_first_negative_rmp_objective_delta": worker_followup[
            "post_first_negative_rmp_objective_delta"
        ],
        "followup_post_first_negative_dual_l1_delta": worker_followup[
            "post_first_negative_dual_l1_delta"
        ],
        "followup_first_negative_active_after_addition": worker_followup[
            "first_negative_active_after_addition"
        ],
        "followup_first_negative_active_value_after_addition": worker_followup[
            "first_negative_active_value_after_addition"
        ],
        "followup_first_negative_active_journey_count_after_addition": worker_followup[
            "first_negative_active_journey_count_after_addition"
        ],
        "followup_first_negative_active_relation_after_addition": worker_followup[
            "first_negative_active_relation_after_addition"
        ],
        "followup_active_fractional_ratio_after_first_negative": worker_followup[
            "active_fractional_ratio_after_first_negative"
        ],
        "followup_active_total_value_after_first_negative": worker_followup[
            "active_total_value_after_first_negative"
        ],
        "followup_active_task_set_hash_after_first_negative": worker_followup[
            "active_task_set_hash_after_first_negative"
        ],
        "followup_rmp_residual_impact_class": worker_followup["rmp_residual_impact_class"],
        "followup_rmp_residual_impact_reason": worker_followup["rmp_residual_impact_reason"],
        "followup_first_negative_active_persistence_count": worker_followup[
            "first_negative_active_persistence_count"
        ],
        "followup_first_negative_active_value_sequence": worker_followup[
            "first_negative_active_value_sequence"
        ],
        "followup_first_negative_active_last_value": worker_followup[
            "first_negative_active_last_value"
        ],
        "followup_active_basis_hash_sequence_after_first_negative": worker_followup[
            "active_basis_hash_sequence_after_first_negative"
        ],
        "followup_active_basis_unique_count_after_first_negative": worker_followup[
            "active_basis_unique_count_after_first_negative"
        ],
        "followup_active_basis_churn_count_after_first_negative": worker_followup[
            "active_basis_churn_count_after_first_negative"
        ],
        "followup_negative_family_after_first_count": worker_followup[
            "negative_family_after_first_count"
        ],
        "followup_negative_family_after_first_relation_sequence": worker_followup[
            "negative_family_after_first_relation_sequence"
        ],
        "followup_negative_family_after_first_disjoint_count": worker_followup[
            "negative_family_after_first_disjoint_count"
        ],
        "followup_negative_family_after_first_overlapping_count": worker_followup[
            "negative_family_after_first_overlapping_count"
        ],
        "followup_negative_family_after_first_same_count": worker_followup[
            "negative_family_after_first_same_count"
        ],
        "followup_negative_family_after_first_max_overlap": worker_followup[
            "negative_family_after_first_max_overlap"
        ],
        "followup_negative_family_after_first_max_jaccard": worker_followup[
            "negative_family_after_first_max_jaccard"
        ],
        "followup_residual_family_chain_class": worker_followup[
            "residual_family_chain_class"
        ],
        "followup_residual_family_chain_reason": worker_followup[
            "residual_family_chain_reason"
        ],
        "followup_post_first_negative_pool_duplicate_task_sets": worker_followup[
            "post_first_negative_pool_duplicate_task_sets"
        ],
        "followup_post_first_negative_pool_duplicate_task_set_ratio": worker_followup[
            "post_first_negative_pool_duplicate_task_set_ratio"
        ],
        "followup_post_first_negative_pool_active_duplicate_task_sets": worker_followup[
            "post_first_negative_pool_active_duplicate_task_sets"
        ],
        "followup_post_first_negative_pool_active_duplicate_task_set_ratio": worker_followup[
            "post_first_negative_pool_active_duplicate_task_set_ratio"
        ],
        "followup_post_first_negative_pool_avg_journeys_per_task_set": worker_followup[
            "post_first_negative_pool_avg_journeys_per_task_set"
        ],
        "followup_post_first_negative_pool_max_journeys_per_task_set": worker_followup[
            "post_first_negative_pool_max_journeys_per_task_set"
        ],
        "followup_post_first_negative_pool_active_avg_journeys_per_task_set": worker_followup[
            "post_first_negative_pool_active_avg_journeys_per_task_set"
        ],
        "followup_post_first_negative_pool_active_fractional_value_sum": worker_followup[
            "post_first_negative_pool_active_fractional_value_sum"
        ],
        "followup_post_first_negative_pool_active_fractional_value_max": worker_followup[
            "post_first_negative_pool_active_fractional_value_max"
        ],
        "followup_post_first_negative_pool_active_fractional_value_min": worker_followup[
            "post_first_negative_pool_active_fractional_value_min"
        ],
        "followup_post_first_negative_pool_active_fractional_small_value_count": worker_followup[
            "post_first_negative_pool_active_fractional_small_value_count"
        ],
        "followup_rmp_degeneracy_pressure_class": worker_followup[
            "rmp_degeneracy_pressure_class"
        ],
        "followup_rmp_degeneracy_pressure_reason": worker_followup[
            "rmp_degeneracy_pressure_reason"
        ],
        "followup_post_first_negative_dual_objective_abs_ratio": worker_followup[
            "post_first_negative_dual_objective_abs_ratio"
        ],
        "followup_post_first_negative_dual_move_class": worker_followup[
            "post_first_negative_dual_move_class"
        ],
        "followup_pool_compression_candidate_class": worker_followup[
            "pool_compression_candidate_class"
        ],
        "followup_pool_compression_candidate_reason": worker_followup[
            "pool_compression_candidate_reason"
        ],
        "followup_rmp_stabilization_candidate_class": worker_followup[
            "rmp_stabilization_candidate_class"
        ],
        "followup_rmp_stabilization_candidate_reason": worker_followup[
            "rmp_stabilization_candidate_reason"
        ],
        "followup_stabilization_diagnostic_design_class": worker_followup[
            "stabilization_diagnostic_design_class"
        ],
        "followup_stabilization_diagnostic_design_reason": worker_followup[
            "stabilization_diagnostic_design_reason"
        ],
        "followup_stabilization_diagnostic_recommended_profile": worker_followup[
            "stabilization_diagnostic_recommended_profile"
        ],
        "followup_stabilization_diagnostic_guarded_config_keys": worker_followup[
            "stabilization_diagnostic_guarded_config_keys"
        ],
        "followup_stabilization_diagnostic_certificate_effect_allowed": worker_followup[
            "stabilization_diagnostic_certificate_effect_allowed"
        ],
        "followup_stabilization_probe_enabled": worker_followup[
            "stabilization_probe_enabled"
        ],
        "followup_stabilization_probe_status": worker_followup[
            "stabilization_probe_status"
        ],
        "followup_stabilization_probe_reason": worker_followup[
            "stabilization_probe_reason"
        ],
        "followup_stabilization_probe_mode": worker_followup[
            "stabilization_probe_mode"
        ],
        "followup_stabilization_probe_candidate_source": worker_followup[
            "stabilization_probe_candidate_source"
        ],
        "followup_stabilization_probe_anchor_weight": worker_followup[
            "stabilization_probe_anchor_weight"
        ],
        "followup_stabilization_probe_context_hash_required": worker_followup[
            "stabilization_probe_context_hash_required"
        ],
        "followup_stabilization_probe_context_hash": worker_followup[
            "stabilization_probe_context_hash"
        ],
        "followup_stabilization_probe_certificate_effect_allowed": worker_followup[
            "stabilization_probe_certificate_effect_allowed"
        ],
        "followup_stabilization_probe_official_effect_allowed": worker_followup[
            "stabilization_probe_official_effect_allowed"
        ],
        "followup_stabilization_probe_mutates_rmp": worker_followup[
            "stabilization_probe_mutates_rmp"
        ],
        "followup_stabilization_probe_design_profile": worker_followup[
            "stabilization_probe_design_profile"
        ],
        "followup_profile_selected_candidate_input_count": worker_followup[
            "profile_selected_candidate_input_count"
        ],
        "followup_profile_selected_candidate_scanned_count": worker_followup[
            "profile_selected_candidate_scanned_count"
        ],
        "followup_profile_selected_candidate_materialized_count": worker_followup[
            "profile_selected_candidate_materialized_count"
        ],
        "followup_profile_selected_candidate_returned_count": worker_followup[
            "profile_selected_candidate_returned_count"
        ],
        "followup_profile_selected_candidate_filtered_count": worker_followup[
            "profile_selected_candidate_filtered_count"
        ],
        "followup_profile_selected_candidate_return_limit_truncated_count": worker_followup[
            "profile_selected_candidate_return_limit_truncated_count"
        ],
        "followup_terminal_after_negative_incomplete": worker_followup[
            "terminal_after_negative_incomplete"
        ],
        "followup_last_pricing_time_limit": worker_followup["last_pricing_time_limit"],
        "followup_last_pricing_max_dp_states": worker_followup["last_pricing_max_dp_states"],
        "followup_last_pricing_profile_dp_time": worker_followup["last_pricing_profile_dp_time"],
        "followup_last_pricing_dp_state_count": worker_followup["last_pricing_dp_state_count"],
        "followup_profile_dp_incomplete_count": worker_followup["profile_dp_incomplete_count"],
        "followup_profile_dp_incomplete_class": worker_followup["profile_dp_incomplete_class"],
        "followup_profile_dp_state_count_max": worker_followup["profile_dp_state_count_max"],
        "followup_profile_dp_processed_labels_max": worker_followup["profile_dp_processed_labels_max"],
        "followup_profile_dp_extension_attempts": worker_followup["profile_dp_extension_attempts"],
        "followup_profile_dp_time": worker_followup["profile_dp_time"],
        "followup_profile_dp_state_cap_hit": worker_followup["profile_dp_state_cap_hit"],
        "followup_profile_dp_min_best_rc": worker_followup["profile_dp_min_best_rc"],
        "followup_profile_dp_max_labels_per_mask_observed": worker_followup[
            "profile_dp_max_labels_per_mask_observed"
        ],
        "followup_profile_dp_nonempty_mask_count": worker_followup[
            "profile_dp_nonempty_mask_count"
        ],
        "followup_profile_dp_labels_by_sortie_count": worker_followup[
            "profile_dp_labels_by_sortie_count"
        ],
        "followup_profile_dp_top_mask_label_counts": worker_followup[
            "profile_dp_top_mask_label_counts"
        ],
        "followup_legacy_final_judge_called": bool(
            worker_followup["legacy_after_worker_calls"] > 0
        ),
        "followup_completion_retry_called": bool(
            worker_followup["completion_retry_after_worker_count"] > 0
        ),
        "pulse_worker_next_rmp_objective_delta": worker_followup["next_rmp_objective_delta"],
        "pulse_worker_next_dual_l1_delta": worker_followup["next_dual_l1_delta"],
        "pulse_worker_followup_changed_task_set_count": worker_followup["worker_changed_task_set_count"],
        "pulse_worker_followup_active_task_set_count": worker_followup["worker_active_task_set_count"],
        "pulse_worker_followup_inactive_task_set_count": worker_followup["worker_inactive_task_set_count"],
        "pulse_worker_followup_active_task_set_ratio": worker_followup["worker_active_task_set_ratio"],
        "pulse_worker_followup_wall_after_worker": worker_followup["wall_after_worker"],
        "pulse_worker_followup_pricing_calls": worker_followup["pricing_calls"],
        "pulse_worker_followup_generated_sequences": worker_followup["generated_sequences"],
        "pulse_worker_followup_evaluated_timed_trips": worker_followup["evaluated_timed_trips"],
        "pulse_worker_followup_legacy_final_judge_time": worker_followup["legacy_after_worker_time"],
        "pulse_worker_followup_completion_retry_count": worker_followup["completion_retry_after_worker_count"],
        "pulse_worker_followup_completion_retry_time": worker_followup["completion_retry_after_worker_time"],
        "pulse_worker_followup_legacy_final_judge_called": bool(
            worker_followup["legacy_after_worker_calls"] > 0
        ),
        "pulse_worker_followup_completion_retry_called": bool(
            worker_followup["completion_retry_after_worker_count"] > 0
        ),
        "pulse_worker_followup_hidden_negative_found": bool(
            worker_followup["worker_negative_after_worker_count"] > 0
        ),
        "pulse_worker_followup_tail_outcome": worker_followup["tail_outcome"],
        "pulse_worker_followup_negative_pricing_calls": worker_followup["negative_pricing_calls"],
        "pulse_worker_followup_incomplete_pricing_calls": worker_followup["incomplete_pricing_calls"],
        "pulse_worker_followup_min_best_rc": worker_followup["min_best_rc"],
        "pulse_worker_followup_pricing_state_sequence": worker_followup["pricing_state_sequence"],
        "pulse_worker_followup_first_negative_cg_iter": worker_followup["first_negative_cg_iter"],
        "pulse_worker_followup_first_negative_pricing_kind": worker_followup[
            "first_negative_pricing_kind"
        ],
        "pulse_worker_followup_first_negative_best_rc": worker_followup["first_negative_best_rc"],
        "pulse_worker_followup_first_negative_task_set_hash": worker_followup[
            "first_negative_task_set_hash"
        ],
        "pulse_worker_followup_first_negative_task_set": worker_followup[
            "first_negative_task_set"
        ],
        "pulse_worker_followup_first_negative_task_count": worker_followup[
            "first_negative_task_count"
        ],
        "pulse_worker_followup_first_negative_sequence": worker_followup[
            "first_negative_sequence"
        ],
        "pulse_worker_followup_first_negative_signature_sample": worker_followup[
            "first_negative_signature_sample"
        ],
        "pulse_worker_followup_first_negative_overlap_to_worker": worker_followup[
            "first_negative_overlap_to_worker"
        ],
        "pulse_worker_followup_first_negative_jaccard_to_worker": worker_followup[
            "first_negative_jaccard_to_worker"
        ],
        "pulse_worker_followup_first_negative_relation_to_worker": worker_followup[
            "first_negative_relation_to_worker"
        ],
        "pulse_worker_vs_ordinary_first_worker_task_set": worker_followup[
            "worker_vs_ordinary_first_worker_task_set"
        ],
        "pulse_worker_vs_ordinary_first_followup_task_set": worker_followup[
            "worker_vs_ordinary_first_followup_task_set"
        ],
        "pulse_worker_vs_ordinary_task_set_overlap": worker_followup[
            "worker_vs_ordinary_task_set_overlap"
        ],
        "pulse_worker_vs_ordinary_task_set_jaccard": worker_followup[
            "worker_vs_ordinary_task_set_jaccard"
        ],
        "pulse_worker_vs_ordinary_task_set_relation": worker_followup[
            "worker_vs_ordinary_task_set_relation"
        ],
        "pulse_worker_vs_ordinary_disjoint": worker_followup["worker_vs_ordinary_disjoint"],
        "pulse_worker_vs_ordinary_worker_task_count": worker_followup[
            "worker_vs_ordinary_worker_task_count"
        ],
        "pulse_worker_vs_ordinary_followup_task_count": worker_followup[
            "worker_vs_ordinary_followup_task_count"
        ],
        "pulse_worker_vs_ordinary_task_count_delta": worker_followup[
            "worker_vs_ordinary_task_count_delta"
        ],
        "pulse_worker_vs_ordinary_worker_added_before_followup": worker_followup[
            "worker_vs_ordinary_worker_added_before_followup"
        ],
        "pulse_worker_vs_ordinary_followup_returned_after_worker": worker_followup[
            "worker_vs_ordinary_followup_returned_after_worker"
        ],
        "pulse_worker_vs_ordinary_contrast_class": worker_followup[
            "worker_vs_ordinary_contrast_class"
        ],
        "pulse_worker_vs_ordinary_negative_pool_overlap": worker_followup[
            "worker_vs_ordinary_negative_pool_overlap"
        ],
        "pulse_worker_vs_ordinary_negative_pool_jaccard": worker_followup[
            "worker_vs_ordinary_negative_pool_jaccard"
        ],
        "pulse_worker_vs_ordinary_negative_pool_relation": worker_followup[
            "worker_vs_ordinary_negative_pool_relation"
        ],
        "pulse_worker_vs_ordinary_negative_pool_exact": worker_followup[
            "worker_vs_ordinary_negative_pool_exact"
        ],
        "pulse_worker_vs_ordinary_harvested_overlap": worker_followup[
            "worker_vs_ordinary_harvested_overlap"
        ],
        "pulse_worker_vs_ordinary_harvested_jaccard": worker_followup[
            "worker_vs_ordinary_harvested_jaccard"
        ],
        "pulse_worker_vs_ordinary_harvested_relation": worker_followup[
            "worker_vs_ordinary_harvested_relation"
        ],
        "pulse_worker_vs_ordinary_harvested_exact": worker_followup[
            "worker_vs_ordinary_harvested_exact"
        ],
        "pulse_worker_vs_ordinary_returned_candidate_overlap": worker_followup[
            "worker_vs_ordinary_returned_candidate_overlap"
        ],
        "pulse_worker_vs_ordinary_returned_candidate_jaccard": worker_followup[
            "worker_vs_ordinary_returned_candidate_jaccard"
        ],
        "pulse_worker_vs_ordinary_returned_candidate_relation": worker_followup[
            "worker_vs_ordinary_returned_candidate_relation"
        ],
        "pulse_worker_vs_ordinary_returned_candidate_exact": worker_followup[
            "worker_vs_ordinary_returned_candidate_exact"
        ],
        "pulse_worker_target_sequence_task_set": worker_followup[
            "worker_target_sequence_task_set"
        ],
        "pulse_worker_target_negative_pool_overlap": worker_followup[
            "worker_target_negative_pool_overlap"
        ],
        "pulse_worker_target_negative_pool_jaccard": worker_followup[
            "worker_target_negative_pool_jaccard"
        ],
        "pulse_worker_target_negative_pool_relation": worker_followup[
            "worker_target_negative_pool_relation"
        ],
        "pulse_worker_target_negative_pool_exact": worker_followup[
            "worker_target_negative_pool_exact"
        ],
        "pulse_worker_target_harvested_overlap": worker_followup[
            "worker_target_harvested_overlap"
        ],
        "pulse_worker_target_harvested_jaccard": worker_followup[
            "worker_target_harvested_jaccard"
        ],
        "pulse_worker_target_harvested_relation": worker_followup[
            "worker_target_harvested_relation"
        ],
        "pulse_worker_target_harvested_exact": worker_followup[
            "worker_target_harvested_exact"
        ],
        "pulse_worker_target_returned_candidate_overlap": worker_followup[
            "worker_target_returned_candidate_overlap"
        ],
        "pulse_worker_target_returned_candidate_jaccard": worker_followup[
            "worker_target_returned_candidate_jaccard"
        ],
        "pulse_worker_target_returned_candidate_relation": worker_followup[
            "worker_target_returned_candidate_relation"
        ],
        "pulse_worker_target_returned_candidate_exact": worker_followup[
            "worker_target_returned_candidate_exact"
        ],
        "pulse_worker_followup_first_negative_profile_dp_top_overlap": worker_followup[
            "first_negative_profile_dp_top_overlap"
        ],
        "pulse_worker_followup_first_negative_profile_dp_top_jaccard": worker_followup[
            "first_negative_profile_dp_top_jaccard"
        ],
        "pulse_worker_followup_first_negative_profile_dp_top_relation": worker_followup[
            "first_negative_profile_dp_top_relation"
        ],
        "pulse_worker_followup_first_negative_profile_dp_top_exact": worker_followup[
            "first_negative_profile_dp_top_exact"
        ],
        "pulse_worker_followup_first_negative_profile_reachable_overlap": worker_followup[
            "first_negative_profile_reachable_overlap"
        ],
        "pulse_worker_followup_first_negative_profile_reachable_jaccard": worker_followup[
            "first_negative_profile_reachable_jaccard"
        ],
        "pulse_worker_followup_first_negative_profile_reachable_relation": worker_followup[
            "first_negative_profile_reachable_relation"
        ],
        "pulse_worker_followup_first_negative_profile_reachable_exact": worker_followup[
            "first_negative_profile_reachable_exact"
        ],
        "pulse_worker_followup_first_negative_profile_negative_overlap": worker_followup[
            "first_negative_profile_negative_overlap"
        ],
        "pulse_worker_followup_first_negative_profile_negative_jaccard": worker_followup[
            "first_negative_profile_negative_jaccard"
        ],
        "pulse_worker_followup_first_negative_profile_negative_relation": worker_followup[
            "first_negative_profile_negative_relation"
        ],
        "pulse_worker_followup_first_negative_profile_negative_exact": worker_followup[
            "first_negative_profile_negative_exact"
        ],
        "pulse_worker_followup_first_negative_profile_selected_overlap": worker_followup[
            "first_negative_profile_selected_overlap"
        ],
        "pulse_worker_followup_first_negative_profile_selected_jaccard": worker_followup[
            "first_negative_profile_selected_jaccard"
        ],
        "pulse_worker_followup_first_negative_profile_selected_relation": worker_followup[
            "first_negative_profile_selected_relation"
        ],
        "pulse_worker_followup_first_negative_profile_selected_exact": worker_followup[
            "first_negative_profile_selected_exact"
        ],
        "pulse_worker_followup_first_negative_profile_materialized_overlap": worker_followup[
            "first_negative_profile_materialized_overlap"
        ],
        "pulse_worker_followup_first_negative_profile_materialized_jaccard": worker_followup[
            "first_negative_profile_materialized_jaccard"
        ],
        "pulse_worker_followup_first_negative_profile_materialized_relation": worker_followup[
            "first_negative_profile_materialized_relation"
        ],
        "pulse_worker_followup_first_negative_profile_materialized_exact": worker_followup[
            "first_negative_profile_materialized_exact"
        ],
        "pulse_worker_followup_first_negative_profile_returned_overlap": worker_followup[
            "first_negative_profile_returned_overlap"
        ],
        "pulse_worker_followup_first_negative_profile_returned_jaccard": worker_followup[
            "first_negative_profile_returned_jaccard"
        ],
        "pulse_worker_followup_first_negative_profile_returned_relation": worker_followup[
            "first_negative_profile_returned_relation"
        ],
        "pulse_worker_followup_first_negative_profile_returned_exact": worker_followup[
            "first_negative_profile_returned_exact"
        ],
        "pulse_worker_followup_first_negative_profile_unmaterialized_overlap": worker_followup[
            "first_negative_profile_unmaterialized_overlap"
        ],
        "pulse_worker_followup_first_negative_profile_unmaterialized_jaccard": worker_followup[
            "first_negative_profile_unmaterialized_jaccard"
        ],
        "pulse_worker_followup_first_negative_profile_unmaterialized_relation": worker_followup[
            "first_negative_profile_unmaterialized_relation"
        ],
        "pulse_worker_followup_first_negative_profile_unmaterialized_exact": worker_followup[
            "first_negative_profile_unmaterialized_exact"
        ],
        "pulse_worker_followup_first_negative_profile_weak_filtered_overlap": worker_followup[
            "first_negative_profile_weak_filtered_overlap"
        ],
        "pulse_worker_followup_first_negative_profile_weak_filtered_jaccard": worker_followup[
            "first_negative_profile_weak_filtered_jaccard"
        ],
        "pulse_worker_followup_first_negative_profile_weak_filtered_relation": worker_followup[
            "first_negative_profile_weak_filtered_relation"
        ],
        "pulse_worker_followup_first_negative_profile_weak_filtered_exact": worker_followup[
            "first_negative_profile_weak_filtered_exact"
        ],
        "pulse_worker_followup_first_negative_profile_filtered_overlap": worker_followup[
            "first_negative_profile_filtered_overlap"
        ],
        "pulse_worker_followup_first_negative_profile_filtered_jaccard": worker_followup[
            "first_negative_profile_filtered_jaccard"
        ],
        "pulse_worker_followup_first_negative_profile_filtered_relation": worker_followup[
            "first_negative_profile_filtered_relation"
        ],
        "pulse_worker_followup_first_negative_profile_filtered_exact": worker_followup[
            "first_negative_profile_filtered_exact"
        ],
        "pulse_worker_followup_proof_tail_bridge_class": worker_followup["proof_tail_bridge_class"],
        "pulse_worker_followup_proof_tail_bridge_reason": worker_followup["proof_tail_bridge_reason"],
        "pulse_worker_followup_returned_residual_tail_class": worker_followup[
            "returned_residual_tail_class"
        ],
        "pulse_worker_followup_returned_residual_tail_reason": worker_followup[
            "returned_residual_tail_reason"
        ],
        "pulse_worker_followup_negative_task_set_sequence": worker_followup["negative_task_set_sequence"],
        "pulse_worker_followup_negative_task_set_unique_count": worker_followup[
            "negative_task_set_unique_count"
        ],
        "pulse_worker_followup_negative_task_set_repeat_count": worker_followup[
            "negative_task_set_repeat_count"
        ],
        "pulse_worker_followup_first_negative_addition_productivity_class": worker_followup[
            "first_negative_addition_productivity_class"
        ],
        "pulse_worker_followup_first_negative_added_journeys": worker_followup[
            "first_negative_added_journeys"
        ],
        "pulse_worker_followup_first_negative_added_new_task_set_count": worker_followup[
            "first_negative_added_new_task_set_count"
        ],
        "pulse_worker_followup_first_negative_added_replacement_count": worker_followup[
            "first_negative_added_replacement_count"
        ],
        "pulse_worker_followup_first_negative_added_support_changing_count": worker_followup[
            "first_negative_added_support_changing_count"
        ],
        "pulse_worker_followup_post_first_negative_rmp_objective_delta": worker_followup[
            "post_first_negative_rmp_objective_delta"
        ],
        "pulse_worker_followup_post_first_negative_dual_l1_delta": worker_followup[
            "post_first_negative_dual_l1_delta"
        ],
        "pulse_worker_followup_first_negative_active_after_addition": worker_followup[
            "first_negative_active_after_addition"
        ],
        "pulse_worker_followup_first_negative_active_value_after_addition": worker_followup[
            "first_negative_active_value_after_addition"
        ],
        "pulse_worker_followup_first_negative_active_journey_count_after_addition": worker_followup[
            "first_negative_active_journey_count_after_addition"
        ],
        "pulse_worker_followup_first_negative_active_relation_after_addition": worker_followup[
            "first_negative_active_relation_after_addition"
        ],
        "pulse_worker_followup_active_fractional_ratio_after_first_negative": worker_followup[
            "active_fractional_ratio_after_first_negative"
        ],
        "pulse_worker_followup_active_total_value_after_first_negative": worker_followup[
            "active_total_value_after_first_negative"
        ],
        "pulse_worker_followup_active_task_set_hash_after_first_negative": worker_followup[
            "active_task_set_hash_after_first_negative"
        ],
        "pulse_worker_followup_rmp_residual_impact_class": worker_followup[
            "rmp_residual_impact_class"
        ],
        "pulse_worker_followup_rmp_residual_impact_reason": worker_followup[
            "rmp_residual_impact_reason"
        ],
        "pulse_worker_followup_first_negative_active_persistence_count": worker_followup[
            "first_negative_active_persistence_count"
        ],
        "pulse_worker_followup_first_negative_active_value_sequence": worker_followup[
            "first_negative_active_value_sequence"
        ],
        "pulse_worker_followup_first_negative_active_last_value": worker_followup[
            "first_negative_active_last_value"
        ],
        "pulse_worker_followup_active_basis_hash_sequence_after_first_negative": worker_followup[
            "active_basis_hash_sequence_after_first_negative"
        ],
        "pulse_worker_followup_active_basis_unique_count_after_first_negative": worker_followup[
            "active_basis_unique_count_after_first_negative"
        ],
        "pulse_worker_followup_active_basis_churn_count_after_first_negative": worker_followup[
            "active_basis_churn_count_after_first_negative"
        ],
        "pulse_worker_followup_negative_family_after_first_count": worker_followup[
            "negative_family_after_first_count"
        ],
        "pulse_worker_followup_negative_family_after_first_relation_sequence": worker_followup[
            "negative_family_after_first_relation_sequence"
        ],
        "pulse_worker_followup_negative_family_after_first_disjoint_count": worker_followup[
            "negative_family_after_first_disjoint_count"
        ],
        "pulse_worker_followup_negative_family_after_first_overlapping_count": worker_followup[
            "negative_family_after_first_overlapping_count"
        ],
        "pulse_worker_followup_negative_family_after_first_same_count": worker_followup[
            "negative_family_after_first_same_count"
        ],
        "pulse_worker_followup_negative_family_after_first_max_overlap": worker_followup[
            "negative_family_after_first_max_overlap"
        ],
        "pulse_worker_followup_negative_family_after_first_max_jaccard": worker_followup[
            "negative_family_after_first_max_jaccard"
        ],
        "pulse_worker_followup_residual_family_chain_class": worker_followup[
            "residual_family_chain_class"
        ],
        "pulse_worker_followup_residual_family_chain_reason": worker_followup[
            "residual_family_chain_reason"
        ],
        "pulse_worker_followup_post_first_negative_pool_duplicate_task_sets": worker_followup[
            "post_first_negative_pool_duplicate_task_sets"
        ],
        "pulse_worker_followup_post_first_negative_pool_duplicate_task_set_ratio": worker_followup[
            "post_first_negative_pool_duplicate_task_set_ratio"
        ],
        "pulse_worker_followup_post_first_negative_pool_active_duplicate_task_sets": worker_followup[
            "post_first_negative_pool_active_duplicate_task_sets"
        ],
        "pulse_worker_followup_post_first_negative_pool_active_duplicate_task_set_ratio": worker_followup[
            "post_first_negative_pool_active_duplicate_task_set_ratio"
        ],
        "pulse_worker_followup_post_first_negative_pool_avg_journeys_per_task_set": worker_followup[
            "post_first_negative_pool_avg_journeys_per_task_set"
        ],
        "pulse_worker_followup_post_first_negative_pool_max_journeys_per_task_set": worker_followup[
            "post_first_negative_pool_max_journeys_per_task_set"
        ],
        "pulse_worker_followup_post_first_negative_pool_active_avg_journeys_per_task_set": worker_followup[
            "post_first_negative_pool_active_avg_journeys_per_task_set"
        ],
        "pulse_worker_followup_post_first_negative_pool_active_fractional_value_sum": worker_followup[
            "post_first_negative_pool_active_fractional_value_sum"
        ],
        "pulse_worker_followup_post_first_negative_pool_active_fractional_value_max": worker_followup[
            "post_first_negative_pool_active_fractional_value_max"
        ],
        "pulse_worker_followup_post_first_negative_pool_active_fractional_value_min": worker_followup[
            "post_first_negative_pool_active_fractional_value_min"
        ],
        "pulse_worker_followup_post_first_negative_pool_active_fractional_small_value_count": worker_followup[
            "post_first_negative_pool_active_fractional_small_value_count"
        ],
        "pulse_worker_followup_rmp_degeneracy_pressure_class": worker_followup[
            "rmp_degeneracy_pressure_class"
        ],
        "pulse_worker_followup_rmp_degeneracy_pressure_reason": worker_followup[
            "rmp_degeneracy_pressure_reason"
        ],
        "pulse_worker_followup_post_first_negative_dual_objective_abs_ratio": worker_followup[
            "post_first_negative_dual_objective_abs_ratio"
        ],
        "pulse_worker_followup_post_first_negative_dual_move_class": worker_followup[
            "post_first_negative_dual_move_class"
        ],
        "pulse_worker_followup_pool_compression_candidate_class": worker_followup[
            "pool_compression_candidate_class"
        ],
        "pulse_worker_followup_pool_compression_candidate_reason": worker_followup[
            "pool_compression_candidate_reason"
        ],
        "pulse_worker_followup_rmp_stabilization_candidate_class": worker_followup[
            "rmp_stabilization_candidate_class"
        ],
        "pulse_worker_followup_rmp_stabilization_candidate_reason": worker_followup[
            "rmp_stabilization_candidate_reason"
        ],
        "pulse_worker_followup_stabilization_diagnostic_design_class": worker_followup[
            "stabilization_diagnostic_design_class"
        ],
        "pulse_worker_followup_stabilization_diagnostic_design_reason": worker_followup[
            "stabilization_diagnostic_design_reason"
        ],
        "pulse_worker_followup_stabilization_diagnostic_recommended_profile": worker_followup[
            "stabilization_diagnostic_recommended_profile"
        ],
        "pulse_worker_followup_stabilization_diagnostic_guarded_config_keys": worker_followup[
            "stabilization_diagnostic_guarded_config_keys"
        ],
        "pulse_worker_followup_stabilization_diagnostic_certificate_effect_allowed": worker_followup[
            "stabilization_diagnostic_certificate_effect_allowed"
        ],
        "pulse_worker_followup_stabilization_probe_enabled": worker_followup[
            "stabilization_probe_enabled"
        ],
        "pulse_worker_followup_stabilization_probe_status": worker_followup[
            "stabilization_probe_status"
        ],
        "pulse_worker_followup_stabilization_probe_reason": worker_followup[
            "stabilization_probe_reason"
        ],
        "pulse_worker_followup_stabilization_probe_mode": worker_followup[
            "stabilization_probe_mode"
        ],
        "pulse_worker_followup_stabilization_probe_candidate_source": worker_followup[
            "stabilization_probe_candidate_source"
        ],
        "pulse_worker_followup_stabilization_probe_anchor_weight": worker_followup[
            "stabilization_probe_anchor_weight"
        ],
        "pulse_worker_followup_stabilization_probe_context_hash_required": worker_followup[
            "stabilization_probe_context_hash_required"
        ],
        "pulse_worker_followup_stabilization_probe_context_hash": worker_followup[
            "stabilization_probe_context_hash"
        ],
        "pulse_worker_followup_stabilization_probe_certificate_effect_allowed": worker_followup[
            "stabilization_probe_certificate_effect_allowed"
        ],
        "pulse_worker_followup_stabilization_probe_official_effect_allowed": worker_followup[
            "stabilization_probe_official_effect_allowed"
        ],
        "pulse_worker_followup_stabilization_probe_mutates_rmp": worker_followup[
            "stabilization_probe_mutates_rmp"
        ],
        "pulse_worker_followup_stabilization_probe_design_profile": worker_followup[
            "stabilization_probe_design_profile"
        ],
        "pulse_worker_followup_profile_selected_candidate_input_count": worker_followup[
            "profile_selected_candidate_input_count"
        ],
        "pulse_worker_followup_profile_selected_candidate_scanned_count": worker_followup[
            "profile_selected_candidate_scanned_count"
        ],
        "pulse_worker_followup_profile_selected_candidate_materialized_count": worker_followup[
            "profile_selected_candidate_materialized_count"
        ],
        "pulse_worker_followup_profile_selected_candidate_returned_count": worker_followup[
            "profile_selected_candidate_returned_count"
        ],
        "pulse_worker_followup_profile_selected_candidate_filtered_count": worker_followup[
            "profile_selected_candidate_filtered_count"
        ],
        "pulse_worker_followup_profile_selected_candidate_return_limit_truncated_count": worker_followup[
            "profile_selected_candidate_return_limit_truncated_count"
        ],
        "pulse_residual_replay_events": len(residual_replay_events),
        "pulse_residual_replay_checked": sum(
            _as_int(event.get("checked_journeys"))
            for event in residual_replay_events
        ),
        "pulse_residual_replay_materialized": sum(
            _as_int(event.get("materialized_journeys"))
            for event in residual_replay_events
        ),
        "pulse_residual_replay_negative": sum(
            _as_int(event.get("negative_journeys"))
            for event in residual_replay_events
        ),
        "pulse_residual_replay_rc_mismatch_count": sum(
            _as_int(event.get("rc_mismatch_count"))
            for event in residual_replay_events
        ),
        "pulse_residual_replay_signature_mismatch_count": sum(
            _as_int(event.get("signature_mismatch_count"))
            for event in residual_replay_events
        ),
        "pulse_residual_replay_first_status": str(first_residual_replay.get("first_status", "")),
        "pulse_residual_replay_first_sequence": str(first_residual_replay.get("first_sequence", "")),
        "pulse_residual_replay_first_original_true_rc": first_residual_replay.get(
            "first_original_true_rc"
        ),
        "pulse_residual_replay_first_replay_true_rc": first_residual_replay.get(
            "first_replay_true_rc"
        ),
        "pulse_residual_replay_first_rc_delta": first_residual_replay.get("first_rc_delta"),
        "pulse_worker_followup_terminal_after_negative_incomplete": worker_followup[
            "terminal_after_negative_incomplete"
        ],
        "pulse_worker_followup_last_pricing_time_limit": worker_followup["last_pricing_time_limit"],
        "pulse_worker_followup_last_pricing_max_dp_states": worker_followup[
            "last_pricing_max_dp_states"
        ],
        "pulse_worker_followup_last_pricing_profile_dp_time": worker_followup[
            "last_pricing_profile_dp_time"
        ],
        "pulse_worker_followup_last_pricing_dp_state_count": worker_followup[
            "last_pricing_dp_state_count"
        ],
        "pulse_worker_followup_profile_dp_incomplete_count": worker_followup["profile_dp_incomplete_count"],
        "pulse_worker_followup_profile_dp_incomplete_class": worker_followup["profile_dp_incomplete_class"],
        "pulse_worker_followup_profile_dp_state_count_max": worker_followup["profile_dp_state_count_max"],
        "pulse_worker_followup_profile_dp_processed_labels_max": worker_followup[
            "profile_dp_processed_labels_max"
        ],
        "pulse_worker_followup_profile_dp_extension_attempts": worker_followup[
            "profile_dp_extension_attempts"
        ],
        "pulse_worker_followup_profile_dp_time": worker_followup["profile_dp_time"],
        "pulse_worker_followup_profile_dp_state_cap_hit": worker_followup["profile_dp_state_cap_hit"],
        "pulse_worker_followup_profile_dp_min_best_rc": worker_followup["profile_dp_min_best_rc"],
        "pulse_worker_followup_profile_dp_max_labels_per_mask_observed": worker_followup[
            "profile_dp_max_labels_per_mask_observed"
        ],
        "pulse_worker_followup_profile_dp_nonempty_mask_count": worker_followup[
            "profile_dp_nonempty_mask_count"
        ],
        "pulse_worker_followup_profile_dp_labels_by_sortie_count": worker_followup[
            "profile_dp_labels_by_sortie_count"
        ],
        "pulse_worker_followup_profile_dp_top_mask_label_counts": worker_followup[
            "profile_dp_top_mask_label_counts"
        ],
        "pulse_worker_true_rc_filtered": sum(
            _as_int(event.get("pulse_worker_true_rc_filtered"))
            for event in worker_events
        ),
        "pulse_worker_task_ordering": "|".join(
            dict.fromkeys(
                str(event.get("pulse_worker_task_ordering", ""))
                for event in worker_events
                if str(event.get("pulse_worker_task_ordering", ""))
            )
        ),
        "pulse_worker_continue_same_iteration_events": len(worker_continue_same_iteration_events),
        "pulse_worker_time": sum(
            float(event.get("pulse_worker_time") or 0.0)
            for event in worker_events
        ),
        "pulse_worker_recursions": sum(
            _as_int(event.get("pulse_worker_recursions"))
            for event in worker_events
        ),
        "pulse_worker_context_hash": worker_context_hash,
        "critical_disagreement": str(audit.get("pulse_audit_disagreement_severity", "")) == "critical",
        "critical_disagreement_count": sum(
            1
            for event in audits
            if str(event.get("pulse_audit_disagreement_severity", "")) == "critical"
        ),
        "pivot_recommendation_class": "unclassified",
        "pivot_recommendation_reason": "",
        "improvement_class": "inconclusive",
        "log_path": str(log_path),
    }
    row["auto_residual_target_context_match"] = bool(
        auto_target_source_context_hash
        and str(row.get("worker_context_hash", ""))
        and auto_target_source_context_hash == str(row.get("worker_context_hash", ""))
    )
    row.update(_active_residual_source_row_summary(row))
    return row


def _run_log_path(
    log_dir: Path,
    instance_name: str,
    profile: str,
    *,
    repeat_count: int,
    repeat_index: int,
) -> Path:
    repeat_suffix = f"__r{int(repeat_index)}" if int(repeat_count) > 1 else ""
    return log_dir / f"{instance_name}__{profile}{repeat_suffix}.jsonl"


def _base_config(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "time_limit": float(args.time_limit),
        "journey_max_cg_iterations": int(args.max_cg_iterations),
        "journey_initial_pool_integer_enabled": False,
        "journey_pool_integer_heuristic_enabled": False,
        "journey_pool_time_limit": 0.2,
        "initial_single_task_starts_per_task": 3,
        "journey_initial_source_trip_limit": 500,
        "journey_initial_max_columns": 250,
        "journey_pool_max_columns": 250,
        "journey_pool_max_extensions_per_prefix": 80,
        "journey_pricing_time_limit": float(args.pricing_time_limit),
        "journey_min_pricing_time": 0.0,
        "journey_post_pricing_time_reserve": 0.0,
        "journey_certificate_no_reserve_enabled": True,
        "journey_certificate_no_reserve_min_cg_iter": 1,
        "journey_pricing_profile_pricing_enabled": False,
        "journey_pricing_direct_journey_label_pricing_enabled": False,
        "journey_pricing_max_sequences": 1,
        "journey_pricing_max_timed_evaluations": 1,
        "journey_pricing_max_candidate_trips": 1,
        "journey_pricing_max_dp_states": max(1, int(args.pricing_max_dp_states)),
        "journey_pulse_residual_replay_diagnostics_enabled": False,
        "journey_pricing_profile_mask_diagnostics_enabled": bool(
            getattr(args, "profile_mask_diagnostics", False)
        ),
        "journey_pulse_target_sequence_diagnostics_enabled": False,
        "journey_pulse_target_sequence_diagnostics_sequence": "",
        "journey_pulse_target_first_task_priority_enabled": False,
        "journey_pulse_target_first_task_priority_sequence": "",
        "journey_pulse_target_transition_priority_enabled": False,
        "journey_pulse_target_transition_priority_sequence": "",
        "journey_pulse_target_arc_option_priority_enabled": False,
        "journey_pulse_target_arc_option_priority_sequence": "",
        "journey_pulse_target_path_diagnostics_enabled": False,
        "journey_pulse_target_path_diagnostics_max_samples": 8,
        "journey_static_fleet_lb_cut_enabled": False,
        "fleet_bound_mode": "computed",
        "fleet_bound_slack": 1,
        "fleet_bound_cost_safe": True,
        "fleet_bound_max": None,
        "pricing_eps": 1.0e-6,
        "integer_tol": 1.0e-6,
    }


def _apply_profile(
    config: dict[str, Any],
    profile: str,
    args: argparse.Namespace,
    *,
    task_count: int | None = None,
) -> None:
    if profile == "baseline":
        return
    stabilization_experiment_profiles = {
        "experimental_l1_previous_dual_stabilization_20_only",
        "experimental_l1_zero_dual_stabilization_20_only",
    }
    if profile in stabilization_experiment_profiles:
        if task_count is not None and int(task_count) < 20:
            return
        _apply_dual_stabilization_experiment_profile(config, profile, args)
        return
    profile_dp_cap_experiment_profiles = {
        "experimental_profile_dp_cap_2000_20_only",
        "experimental_profile_dp_cap_3000_20_only",
    }
    if profile in profile_dp_cap_experiment_profiles:
        if task_count is not None and int(task_count) < 20:
            return
        _apply_profile_dp_cap_experiment_profile(config, profile)
        return
    profile_dp_mask_hotspot_profiles = {
        "experimental_profile_dp_mask_label_cap_16_20_only",
        "experimental_profile_dp_mask_label_cap_32_20_only",
    }
    if profile in profile_dp_mask_hotspot_profiles:
        if task_count is not None and int(task_count) < 20:
            return
        _apply_profile_dp_mask_hotspot_experiment_profile(config, profile)
        return
    early_new_task_set_profiles = {
        "experimental_early_new_task_set_quota_3_20_only",
        "experimental_early_new_task_set_quota_3_return12_20_only",
    }
    if profile in early_new_task_set_profiles:
        if task_count is not None and int(task_count) < 20:
            return
        _apply_early_new_task_set_quota_experiment_profile(config, profile)
        return
    pricing_time_experiment_profiles = {
        "experimental_pricing_time_0_6_20_only",
        "experimental_pricing_time_1_0_20_only",
    }
    if profile in pricing_time_experiment_profiles:
        if task_count is not None and int(task_count) < 20:
            return
        _apply_pricing_time_experiment_profile(config, profile)
        return
    profile_selection_experiment_profiles = {
        "experimental_profile_selection_integer_diverse_20_only",
        "experimental_profile_selection_orthogonal_20_only",
    }
    if profile in profile_selection_experiment_profiles:
        if task_count is not None and int(task_count) < 20:
            return
        _apply_profile_selection_experiment_profile(config, profile)
        return
    delayed_profiles = {
        "strict_worker_delayed_hard_tail_only",
        "strict_worker_delayed_current_probe_impact",
        "strict_worker_delayed_current_probe_impact_low_budget",
        "strict_worker_delayed_current_probe_impact_ultra_low_budget",
        "strict_worker_delayed_current_probe_impact_low_budget_cooldown",
        "strict_worker_delayed_current_probe_impact_20_only_cooldown",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve_active_gate",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_deep_reserve_active_gate",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_active_gate",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_followup_reserve",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_early_cg",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_hard_tail_fingerprint",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown_ordered",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_transition_priority",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_path_diagnostic",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_arc_option_priority",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_residual_target_priority_roi_gate",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_diagnostic",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_roi_gate",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_diagnostic",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_roi_gate",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_roi_gate",
    }
    if profile in delayed_profiles:
        min_tasks = (
            max(20, int(args.current_probe_min_tasks))
            if profile in {
                "strict_worker_delayed_current_probe_impact_20_only_cooldown",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve_active_gate",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_deep_reserve_active_gate",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_active_gate",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_followup_reserve",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_early_cg",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_hard_tail_fingerprint",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown_ordered",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_transition_priority",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_path_diagnostic",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_arc_option_priority",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_residual_target_priority_roi_gate",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_diagnostic",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_roi_gate",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_diagnostic",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_roi_gate",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic",
                "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_roi_gate",
            }
            else int(args.current_probe_min_tasks)
        )
        if task_count is not None and int(task_count) < min_tasks:
            return
        _apply_delayed_worker_profile(config, profile, args)
        return
    config.update(
        {
            "journey_sharded_pulse_audit_enabled": True,
            "journey_sharded_pulse_audit_after_legacy_final_judge": True,
            "journey_sharded_pulse_audit_trigger": "after_each_final_pricing",
            "journey_sharded_pulse_audit_force_on_root": True,
            "journey_sharded_pulse_audit_log_skips": True,
            "journey_sharded_pulse_audit_time_limit": float(args.audit_time_limit),
            "journey_sharded_pulse_audit_max_recursions": int(args.audit_max_recursions),
            "journey_sharded_pulse_audit_log_disagreements": True,
            "journey_sharded_pulse_audit_allow_certificate_effect": False,
            "journey_sharded_pulse_audit_archive_enabled": True,
            "journey_sharded_pulse_audit_bound_pruning_enabled": True,
            "journey_sharded_pulse_audit_support_aware_harvesting_enabled": True,
            "journey_sharded_pulse_audit_negative_harvest_limit": int(
                args.audit_negative_harvest_limit
            ),
            "journey_sharded_pulse_audit_shard_scheduling_enabled": True,
            "journey_sharded_pulse_hidden_negative_worker_enabled": False,
        }
    )
    if profile in {"audit_no_refine", "audit_only"}:
        return
    config.update(
        {
            "journey_sharded_pulse_audit_adaptive_sharding_enabled": True,
            "journey_sharded_pulse_audit_refine_incomplete_first_task_shards": True,
            "journey_sharded_pulse_audit_refinement_min_recursions": 1,
            "journey_sharded_pulse_audit_refinement_min_expanded": 1,
            "journey_sharded_pulse_audit_refinement_max_children": 64,
        }
    )
    if profile == "audit_refine":
        return
    if profile in {"audit_plus_strict_worker", "strict_worker_previous_signal_only"}:
        config.update(
            {
                "journey_sharded_pulse_audit_shard_roi_gate_enabled": True,
                "journey_sharded_pulse_audit_shard_roi_prune_rate_floor": float(
                    ROI_PRESETS["mid"]["prune_rate_floor"]
                ),
                "journey_sharded_pulse_audit_shard_roi_min_expanded": int(
                    ROI_PRESETS["mid"]["min_expanded"]
                ),
                "journey_sharded_pulse_audit_shard_roi_min_time": float(
                    ROI_PRESETS["mid"]["min_time"]
                ),
                "journey_sharded_pulse_hidden_negative_worker_enabled": True,
                "journey_sharded_pulse_hidden_negative_worker_trigger": "hard_tail_only",
                "journey_sharded_pulse_hidden_negative_worker_log_skips": True,
                "journey_sharded_pulse_hidden_negative_worker_min_tasks": 5,
                "journey_sharded_pulse_hidden_negative_worker_min_remaining_time": 0.0,
                "journey_sharded_pulse_hidden_negative_worker_audit_signal_max_age": 3,
                "journey_sharded_pulse_hidden_negative_worker_time_limit": float(
                    args.worker_time_limit
                ),
                "journey_sharded_pulse_hidden_negative_worker_max_recursions": int(
                    args.worker_max_recursions
                ),
                "journey_sharded_pulse_hidden_negative_worker_archive_enabled": True,
                "journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled": True,
                "journey_sharded_pulse_hidden_negative_worker_harvesting_enabled": True,
                "journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit": int(
                    args.worker_negative_harvest_limit
                ),
                "journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled": True,
                "journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled": True,
                "journey_sharded_pulse_hidden_negative_worker_shard_roi_prune_rate_floor": float(
                    ROI_PRESETS["mid"]["prune_rate_floor"]
                ),
                "journey_sharded_pulse_hidden_negative_worker_shard_roi_min_expanded": int(
                    ROI_PRESETS["mid"]["min_expanded"]
                ),
                "journey_sharded_pulse_hidden_negative_worker_shard_roi_min_time": float(
                    ROI_PRESETS["mid"]["min_time"]
                ),
            }
        )
        return
    current_probe_profiles = {
        "strict_worker_current_probe",
        "strict_worker_current_probe_impact",
        "strict_worker_current_probe_support_aware",
        "strict_worker_current_probe_support_aware_low_budget",
        "strict_worker_current_probe_support_aware_mid_budget",
        "strict_worker_current_probe_support_aware_impact_filter",
    }
    if profile in current_probe_profiles:
        probe_time_factor = 1.0
        probe_recursion_factor = 1.0
        probe_max_columns = 16
        if profile == "strict_worker_current_probe_support_aware_low_budget":
            probe_time_factor = 0.5
            probe_recursion_factor = 0.5
            probe_max_columns = 8
        elif profile == "strict_worker_current_probe_support_aware_mid_budget":
            probe_time_factor = 2.0
            probe_recursion_factor = 2.0
            probe_max_columns = 24
        config.update(
            {
                "journey_sharded_pulse_audit_shard_roi_gate_enabled": True,
                "journey_sharded_pulse_audit_shard_roi_prune_rate_floor": float(
                    ROI_PRESETS["mid"]["prune_rate_floor"]
                ),
                "journey_sharded_pulse_audit_shard_roi_min_expanded": int(
                    ROI_PRESETS["mid"]["min_expanded"]
                ),
                "journey_sharded_pulse_audit_shard_roi_min_time": float(
                    ROI_PRESETS["mid"]["min_time"]
                ),
                "journey_sharded_pulse_hidden_negative_worker_enabled": True,
                "journey_sharded_pulse_hidden_negative_worker_trigger": "audit_signal_or_current_probe",
                "journey_sharded_pulse_hidden_negative_worker_log_skips": True,
                "journey_sharded_pulse_hidden_negative_worker_min_tasks": 5,
                "journey_sharded_pulse_hidden_negative_worker_min_remaining_time": 0.0,
                "journey_sharded_pulse_hidden_negative_worker_audit_signal_max_age": 3,
                "journey_sharded_pulse_hidden_negative_worker_time_limit": float(
                    args.worker_time_limit
                ),
                "journey_sharded_pulse_hidden_negative_worker_max_recursions": int(
                    args.worker_max_recursions
                ),
                "journey_sharded_pulse_hidden_negative_worker_archive_enabled": True,
                "journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled": True,
                "journey_sharded_pulse_hidden_negative_worker_harvesting_enabled": True,
                "journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit": int(
                    args.worker_negative_harvest_limit
                ),
                "journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled": True,
                "journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled": True,
                "journey_sharded_pulse_hidden_negative_worker_shard_roi_prune_rate_floor": float(
                    ROI_PRESETS["mid"]["prune_rate_floor"]
                ),
                "journey_sharded_pulse_hidden_negative_worker_shard_roi_min_expanded": int(
                    ROI_PRESETS["mid"]["min_expanded"]
                ),
                "journey_sharded_pulse_hidden_negative_worker_shard_roi_min_time": float(
                    ROI_PRESETS["mid"]["min_time"]
                ),
                "journey_sharded_pulse_worker_current_probe_enabled": True,
                "journey_sharded_pulse_worker_current_probe_time_limit": float(
                    args.current_probe_time_limit
                )
                * probe_time_factor,
                "journey_sharded_pulse_worker_current_probe_max_recursions": max(
                    1,
                    int(
                        round(
                            int(args.current_probe_max_recursions)
                            * probe_recursion_factor
                        )
                    ),
                ),
                "journey_sharded_pulse_worker_current_probe_min_tasks": int(
                    args.current_probe_min_tasks
                ),
                "journey_sharded_pulse_worker_current_probe_min_remaining_time": float(
                    args.current_probe_min_remaining_time
                ),
                "journey_sharded_pulse_worker_current_probe_harvesting_enabled": True,
                "journey_sharded_pulse_worker_current_probe_max_columns": int(
                    probe_max_columns
                ),
                "journey_sharded_pulse_worker_current_probe_negative_harvest_limit": int(
                    args.current_probe_negative_harvest_limit
                ),
            }
        )
        if profile in {
            "strict_worker_current_probe_impact",
            "strict_worker_current_probe_support_aware_impact_filter",
        }:
            config.update(
                {
                    "journey_sharded_pulse_hidden_negative_worker_impact_filter_mode": "require_new_or_active_support",
                    "journey_sharded_pulse_hidden_negative_worker_impact_filter_max_columns": 0,
                }
            )
        return
    if profile == "strict_worker_current_probe_hard_tail_only":
        config.update(
            {
                "journey_sharded_pulse_audit_shard_roi_gate_enabled": True,
                "journey_sharded_pulse_audit_shard_roi_prune_rate_floor": float(
                    ROI_PRESETS["high"]["prune_rate_floor"]
                ),
                "journey_sharded_pulse_audit_shard_roi_min_expanded": int(
                    ROI_PRESETS["high"]["min_expanded"]
                ),
                "journey_sharded_pulse_audit_shard_roi_min_time": float(
                    ROI_PRESETS["high"]["min_time"]
                ),
                "journey_sharded_pulse_hidden_negative_worker_enabled": True,
                "journey_sharded_pulse_hidden_negative_worker_trigger": "hard_tail_only",
                "journey_sharded_pulse_hidden_negative_worker_log_skips": True,
                "journey_sharded_pulse_hidden_negative_worker_min_tasks": max(
                    10, int(args.current_probe_min_tasks)
                ),
                "journey_sharded_pulse_hidden_negative_worker_min_remaining_time": float(
                    args.current_probe_min_remaining_time
                ),
                "journey_sharded_pulse_hidden_negative_worker_audit_signal_max_age": 3,
                "journey_sharded_pulse_hidden_negative_worker_time_limit": float(
                    args.worker_time_limit
                ),
                "journey_sharded_pulse_hidden_negative_worker_max_recursions": int(
                    args.worker_max_recursions
                ),
                "journey_sharded_pulse_hidden_negative_worker_archive_enabled": True,
                "journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled": True,
                "journey_sharded_pulse_hidden_negative_worker_harvesting_enabled": True,
                "journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit": int(
                    args.worker_negative_harvest_limit
                ),
                "journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled": True,
                "journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled": True,
                "journey_sharded_pulse_hidden_negative_worker_shard_roi_prune_rate_floor": float(
                    ROI_PRESETS["high"]["prune_rate_floor"]
                ),
                "journey_sharded_pulse_hidden_negative_worker_shard_roi_min_expanded": int(
                    ROI_PRESETS["high"]["min_expanded"]
                ),
                "journey_sharded_pulse_hidden_negative_worker_shard_roi_min_time": float(
                    ROI_PRESETS["high"]["min_time"]
                ),
            }
        )
        return
    suffix = profile.removeprefix("audit_refine_roi_")
    preset = ROI_PRESETS[suffix]
    config.update(
        {
            "journey_sharded_pulse_audit_shard_roi_gate_enabled": True,
            "journey_sharded_pulse_audit_shard_roi_prune_rate_floor": float(
                preset["prune_rate_floor"]
            ),
            "journey_sharded_pulse_audit_shard_roi_min_expanded": int(preset["min_expanded"]),
            "journey_sharded_pulse_audit_shard_roi_min_time": float(preset["min_time"]),
        }
    )


def _apply_dual_stabilization_experiment_profile(
    config: dict[str, Any],
    profile: str,
    args: argparse.Namespace,
) -> None:
    reference_mode = (
        "zero"
        if profile == "experimental_l1_zero_dual_stabilization_20_only"
        else "previous"
    )
    config.update(
        {
            "journey_dual_stabilization_enabled": True,
            "journey_dual_stabilization_min_cg_iter": 1,
            "journey_dual_stabilization_tail_only_enabled": False,
            "journey_dual_stabilization_certificate_candidate_enabled": False,
            "journey_dual_stabilization_disable_on_certificate_candidate": True,
            "journey_dual_stabilization_mode": "l1_reference",
            "journey_dual_stabilization_reference_mode": reference_mode,
            "journey_dual_stabilization_time_limit": max(
                0.01,
                min(0.15, float(args.pricing_time_limit)),
            ),
            "journey_sharded_pulse_audit_enabled": False,
            "journey_sharded_pulse_hidden_negative_worker_enabled": False,
        }
    )


def _apply_profile_dp_cap_experiment_profile(
    config: dict[str, Any],
    profile: str,
) -> None:
    if profile == "experimental_profile_dp_cap_2000_20_only":
        max_dp_states = 2000
    elif profile == "experimental_profile_dp_cap_3000_20_only":
        max_dp_states = 3000
    else:
        raise ValueError(f"Unsupported profile-DP cap experiment profile: {profile!r}")
    config.update(
        {
            "journey_pricing_max_dp_states": max_dp_states,
            "journey_sharded_pulse_audit_enabled": False,
            "journey_sharded_pulse_hidden_negative_worker_enabled": False,
            "journey_dual_stabilization_enabled": False,
        }
    )


def _apply_profile_dp_mask_hotspot_experiment_profile(
    config: dict[str, Any],
    profile: str,
) -> None:
    if profile == "experimental_profile_dp_mask_label_cap_16_20_only":
        max_labels_per_mask = 16
    elif profile == "experimental_profile_dp_mask_label_cap_32_20_only":
        max_labels_per_mask = 32
    else:
        raise ValueError(f"Unsupported profile-DP mask-hotspot experiment profile: {profile!r}")
    config.update(
        {
            "journey_pricing_profile_dp_max_labels_per_mask": max_labels_per_mask,
            "journey_sharded_pulse_audit_enabled": False,
            "journey_sharded_pulse_hidden_negative_worker_enabled": False,
            "journey_dual_stabilization_enabled": False,
        }
    )


def _apply_early_new_task_set_quota_experiment_profile(
    config: dict[str, Any],
    profile: str,
) -> None:
    if profile == "experimental_early_new_task_set_quota_3_20_only":
        max_returned = 8
    elif profile == "experimental_early_new_task_set_quota_3_return12_20_only":
        max_returned = 12
    else:
        raise ValueError(f"Unsupported early new-task-set quota experiment profile: {profile!r}")
    config.update(
        {
            "journey_pricing_early_return_new_task_set_min_count": 3,
            "journey_heuristic_early_return_new_task_set_min_count": 3,
            "journey_pricing_max_returned_journeys": int(max_returned),
            "journey_heuristic_max_returned_journeys": int(max_returned),
            "journey_pricing_selection_mode": "diverse",
            "journey_heuristic_selection_mode": "diverse",
            "journey_sharded_pulse_audit_enabled": False,
            "journey_sharded_pulse_hidden_negative_worker_enabled": False,
            "journey_dual_stabilization_enabled": False,
        }
    )


def _apply_pricing_time_experiment_profile(
    config: dict[str, Any],
    profile: str,
) -> None:
    if profile == "experimental_pricing_time_0_6_20_only":
        pricing_time_limit = 0.6
    elif profile == "experimental_pricing_time_1_0_20_only":
        pricing_time_limit = 1.0
    else:
        raise ValueError(f"Unsupported pricing-time experiment profile: {profile!r}")
    config.update(
        {
            "journey_pricing_time_limit": float(pricing_time_limit),
            "journey_sharded_pulse_audit_enabled": False,
            "journey_sharded_pulse_hidden_negative_worker_enabled": False,
            "journey_dual_stabilization_enabled": False,
        }
    )


def _apply_profile_selection_experiment_profile(
    config: dict[str, Any],
    profile: str,
) -> None:
    if profile == "experimental_profile_selection_integer_diverse_20_only":
        selection_mode = "integer_diverse"
    elif profile == "experimental_profile_selection_orthogonal_20_only":
        selection_mode = "orthogonal"
    else:
        raise ValueError(f"Unsupported profile-selection experiment profile: {profile!r}")
    config.update(
        {
            "journey_pricing_selection_mode": selection_mode,
            "journey_heuristic_selection_mode": selection_mode,
            "journey_sharded_pulse_audit_enabled": False,
            "journey_sharded_pulse_hidden_negative_worker_enabled": False,
            "journey_dual_stabilization_enabled": False,
        }
    )


def _apply_delayed_worker_profile(
    config: dict[str, Any],
    profile: str,
    args: argparse.Namespace,
) -> None:
    config.update(
        {
            "journey_sharded_pulse_audit_enabled": True,
            "journey_sharded_pulse_audit_after_legacy_final_judge": True,
            "journey_sharded_pulse_audit_trigger": "on_certificate_candidate",
            "journey_sharded_pulse_audit_force_on_root": False,
            "journey_sharded_pulse_audit_log_skips": False,
            "journey_sharded_pulse_audit_time_limit": float(args.audit_time_limit),
            "journey_sharded_pulse_audit_max_recursions": int(args.audit_max_recursions),
            "journey_sharded_pulse_audit_log_disagreements": True,
            "journey_sharded_pulse_audit_allow_certificate_effect": False,
            "journey_sharded_pulse_audit_archive_enabled": True,
            "journey_sharded_pulse_audit_bound_pruning_enabled": True,
            "journey_sharded_pulse_audit_support_aware_harvesting_enabled": True,
            "journey_sharded_pulse_audit_negative_harvest_limit": int(
                args.audit_negative_harvest_limit
            ),
            "journey_sharded_pulse_audit_adaptive_sharding_enabled": True,
            "journey_sharded_pulse_audit_refine_incomplete_first_task_shards": True,
            "journey_sharded_pulse_audit_refinement_min_recursions": 1,
            "journey_sharded_pulse_audit_refinement_min_expanded": 1,
            "journey_sharded_pulse_audit_refinement_max_children": 64,
            "journey_sharded_pulse_audit_shard_scheduling_enabled": True,
            "journey_sharded_pulse_audit_shard_roi_gate_enabled": True,
            "journey_sharded_pulse_audit_shard_roi_prune_rate_floor": float(
                ROI_PRESETS["high"]["prune_rate_floor"]
            ),
            "journey_sharded_pulse_audit_shard_roi_min_expanded": int(
                ROI_PRESETS["high"]["min_expanded"]
            ),
            "journey_sharded_pulse_audit_shard_roi_min_time": float(
                ROI_PRESETS["high"]["min_time"]
            ),
            "journey_sharded_pulse_hidden_negative_worker_enabled": True,
            "journey_sharded_pulse_hidden_negative_worker_trigger": "hard_tail_only",
            "journey_sharded_pulse_hidden_negative_worker_log_skips": False,
            "journey_sharded_pulse_hidden_negative_worker_min_tasks": int(
                args.current_probe_min_tasks
            ),
            "journey_sharded_pulse_hidden_negative_worker_min_remaining_time": float(
                args.current_probe_min_remaining_time
            ),
            "journey_sharded_pulse_hidden_negative_worker_audit_signal_max_age": 3,
            "journey_sharded_pulse_hidden_negative_worker_time_limit": float(
                args.worker_time_limit
            ),
            "journey_sharded_pulse_hidden_negative_worker_max_recursions": int(
                args.worker_max_recursions
            ),
            "journey_sharded_pulse_hidden_negative_worker_archive_enabled": True,
            "journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled": True,
            "journey_sharded_pulse_hidden_negative_worker_harvesting_enabled": True,
            "journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit": int(
                args.worker_negative_harvest_limit
            ),
            "journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled": True,
            "journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled": True,
            "journey_sharded_pulse_hidden_negative_worker_shard_roi_prune_rate_floor": float(
                ROI_PRESETS["high"]["prune_rate_floor"]
            ),
            "journey_sharded_pulse_hidden_negative_worker_shard_roi_min_expanded": int(
                ROI_PRESETS["high"]["min_expanded"]
            ),
            "journey_sharded_pulse_hidden_negative_worker_shard_roi_min_time": float(
                ROI_PRESETS["high"]["min_time"]
            ),
        }
    )
    if profile in {
        "strict_worker_delayed_current_probe_impact",
        "strict_worker_delayed_current_probe_impact_low_budget",
        "strict_worker_delayed_current_probe_impact_ultra_low_budget",
        "strict_worker_delayed_current_probe_impact_low_budget_cooldown",
        "strict_worker_delayed_current_probe_impact_20_only_cooldown",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve_active_gate",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_deep_reserve_active_gate",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_active_gate",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_followup_reserve",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_early_cg",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_hard_tail_fingerprint",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown_ordered",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_transition_priority",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_path_diagnostic",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_arc_option_priority",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_residual_target_priority_roi_gate",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_diagnostic",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_roi_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_diagnostic",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_roi_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_roi_gate",
    }:
        probe_time_factor = 1.0
        probe_recursion_factor = 1.0
        probe_max_columns = 16
        if profile in {
            "strict_worker_delayed_current_probe_impact_low_budget",
            "strict_worker_delayed_current_probe_impact_low_budget_cooldown",
            "strict_worker_delayed_current_probe_impact_20_only_cooldown",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve_active_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_deep_reserve_active_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_active_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_followup_reserve",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_early_cg",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_hard_tail_fingerprint",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown_ordered",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_transition_priority",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_path_diagnostic",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_arc_option_priority",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_residual_target_priority_roi_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_diagnostic",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_roi_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_diagnostic",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_roi_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_roi_gate",
        }:
            probe_time_factor = 1.0 / 3.0
            probe_recursion_factor = 1.0 / 3.0
            probe_max_columns = 8
        elif profile == "strict_worker_delayed_current_probe_impact_ultra_low_budget":
            probe_time_factor = 2.0 / 15.0
            probe_recursion_factor = 2.0 / 15.0
            probe_max_columns = 4
        config.update(
            {
                "journey_sharded_pulse_hidden_negative_worker_trigger": "audit_signal_or_current_probe",
                "journey_sharded_pulse_worker_current_probe_enabled": True,
                "journey_sharded_pulse_worker_current_probe_time_limit": float(
                    args.current_probe_time_limit
                )
                * probe_time_factor,
                "journey_sharded_pulse_worker_current_probe_max_recursions": max(
                    1,
                    int(
                        round(
                            int(args.current_probe_max_recursions)
                            * probe_recursion_factor
                        )
                    ),
                ),
                "journey_sharded_pulse_worker_current_probe_min_tasks": int(
                    args.current_probe_min_tasks
                ),
                "journey_sharded_pulse_worker_current_probe_min_remaining_time": float(
                    args.current_probe_min_remaining_time
                ),
                "journey_sharded_pulse_worker_current_probe_harvesting_enabled": True,
                "journey_sharded_pulse_worker_current_probe_max_columns": int(
                    probe_max_columns
                ),
                "journey_sharded_pulse_worker_current_probe_negative_harvest_limit": int(
                    args.current_probe_negative_harvest_limit
                ),
                "journey_sharded_pulse_hidden_negative_worker_impact_filter_mode": "require_new_or_active_support",
                "journey_sharded_pulse_hidden_negative_worker_impact_filter_max_columns": 0,
            }
        )
        if profile in {
            "strict_worker_delayed_current_probe_impact_low_budget_cooldown",
            "strict_worker_delayed_current_probe_impact_20_only_cooldown",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown_ordered",
        }:
            config["journey_sharded_pulse_hidden_negative_worker_success_cooldown_rounds"] = 2
        if profile in {
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve_active_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_deep_reserve_active_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_active_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_followup_reserve",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_early_cg",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_hard_tail_fingerprint",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown_ordered",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_transition_priority",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_path_diagnostic",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_arc_option_priority",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_residual_target_priority_roi_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_diagnostic",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_roi_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_diagnostic",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_roi_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_roi_gate",
        }:
            config["journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled"] = True
            config["journey_sharded_pulse_hidden_negative_worker_stop_after_first_negative"] = True
        if profile in {
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_transition_priority",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_path_diagnostic",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_arc_option_priority",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_residual_target_priority_roi_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_diagnostic",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_roi_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_diagnostic",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_roi_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_roi_gate",
        }:
            config["journey_sharded_pulse_hidden_negative_worker_stop_after_first_negative"] = False
            config["journey_sharded_pulse_hidden_negative_worker_max_cg_iter"] = 1
            config["journey_pulse_residual_replay_diagnostics_enabled"] = True
            config["journey_pulse_residual_replay_diagnostics_max_journeys"] = 1
        if profile in {
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_transition_priority",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_path_diagnostic",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_arc_option_priority",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_residual_target_priority_roi_gate",
        }:
            config["journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled"] = True
            config[
                "journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence"
            ] = "8,15,5"
        if profile == "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority":
            config[
                "journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled"
            ] = True
            config[
                "journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence"
            ] = "8,15,5"
        if profile == "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_residual_target_priority_roi_gate":
            config[
                "journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled"
            ] = True
            config[
                "journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence"
            ] = "8,15,5"
            config["journey_sharded_pulse_hidden_negative_worker_continue_same_iteration_after_add"] = True
            config["journey_sharded_pulse_hidden_negative_worker_continue_only_on_active_support"] = True
            config["journey_sharded_pulse_hidden_negative_worker_inactive_success_cooldown_rounds"] = 2
            config["journey_sharded_pulse_hidden_negative_worker_impact_filter_min_true_rc"] = -30.0
            config["journey_sharded_pulse_hidden_negative_worker_min_followup_time_after_add"] = 0.4
            config["journey_sharded_pulse_hidden_negative_worker_failure_cooldown_rounds"] = 2
            config["journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled"] = True
            config["journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds"] = 1
            config["journey_sharded_pulse_worker_current_probe_min_no_column_rounds"] = 1
        if profile in {
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_diagnostic",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_roi_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_diagnostic",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_roi_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_roi_gate",
        }:
            config["journey_sharded_pulse_hidden_negative_worker_log_skips"] = True
        if profile in {
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_diagnostic",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_roi_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_roi_gate",
        }:
            config[
                "journey_sharded_pulse_hidden_negative_worker_requires_auto_residual_target"
            ] = True
            config[
                "journey_sharded_pulse_hidden_negative_worker_auto_residual_target_active_gate_enabled"
            ] = True
        if profile in {
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_roi_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_roi_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_roi_gate",
        }:
            config["journey_sharded_pulse_hidden_negative_worker_continue_same_iteration_after_add"] = True
            config["journey_sharded_pulse_hidden_negative_worker_continue_only_on_active_support"] = True
            config["journey_sharded_pulse_hidden_negative_worker_inactive_success_cooldown_rounds"] = 2
            config["journey_sharded_pulse_hidden_negative_worker_impact_filter_min_true_rc"] = -30.0
            config["journey_sharded_pulse_hidden_negative_worker_min_followup_time_after_add"] = 0.4
            config["journey_sharded_pulse_hidden_negative_worker_failure_cooldown_rounds"] = 2
            config["journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled"] = True
            config["journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds"] = 1
            config["journey_sharded_pulse_worker_current_probe_min_no_column_rounds"] = 1
        if profile == "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_transition_priority":
            config[
                "journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled"
            ] = True
            config[
                "journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence"
            ] = "8,15,5"
            config[
                "journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled"
            ] = True
            config[
                "journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence"
            ] = "8,15,5"
        if profile == "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_path_diagnostic":
            config[
                "journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled"
            ] = True
            config[
                "journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence"
            ] = "8,15,5"
            config[
                "journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled"
            ] = True
            config[
                "journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence"
            ] = "8,15,5"
            config[
                "journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled"
            ] = True
            config[
                "journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_max_samples"
            ] = 12
        if profile == "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_arc_option_priority":
            config[
                "journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled"
            ] = True
            config[
                "journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence"
            ] = "8,15,5"
            config[
                "journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled"
            ] = True
            config[
                "journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence"
            ] = "8,15,5"
            config[
                "journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled"
            ] = True
            config[
                "journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence"
            ] = "0->8:low_time:0,8->15:low_risk:2,15->5:low_risk:2,5->0:low_time:0"
            config[
                "journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled"
            ] = True
            config[
                "journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_max_samples"
            ] = 12
        if profile == "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate":
            config["journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled"] = False
        if profile in {
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve_active_gate",
            "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_deep_reserve_active_gate",
        }:
            config["journey_sharded_pulse_hidden_negative_worker_post_call_time_reserve"] = 0.08
        if profile == "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_deep_reserve_active_gate":
            config["journey_sharded_pulse_hidden_negative_worker_post_call_time_reserve"] = 0.16
        if profile == "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve_active_gate":
            config["journey_sharded_pulse_hidden_negative_worker_continue_only_on_active_support"] = True
            config["journey_sharded_pulse_hidden_negative_worker_inactive_success_cooldown_rounds"] = 2
        if profile == "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_deep_reserve_active_gate":
            config["journey_sharded_pulse_hidden_negative_worker_continue_only_on_active_support"] = True
            config["journey_sharded_pulse_hidden_negative_worker_inactive_success_cooldown_rounds"] = 2
        if profile == "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_active_gate":
            config["journey_sharded_pulse_hidden_negative_worker_continue_only_on_active_support"] = True
            config["journey_sharded_pulse_hidden_negative_worker_inactive_success_cooldown_rounds"] = 2
            config["journey_sharded_pulse_hidden_negative_worker_continue_same_iteration_after_add"] = True
        if profile == "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate":
            config["journey_sharded_pulse_hidden_negative_worker_continue_only_on_active_support"] = True
            config["journey_sharded_pulse_hidden_negative_worker_inactive_success_cooldown_rounds"] = 2
            config["journey_sharded_pulse_hidden_negative_worker_continue_same_iteration_after_add"] = True
            config["journey_sharded_pulse_hidden_negative_worker_impact_filter_min_true_rc"] = -30.0
        if profile == "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_followup_reserve":
            config["journey_sharded_pulse_hidden_negative_worker_continue_only_on_active_support"] = True
            config["journey_sharded_pulse_hidden_negative_worker_inactive_success_cooldown_rounds"] = 2
            config["journey_sharded_pulse_hidden_negative_worker_continue_same_iteration_after_add"] = True
            config["journey_sharded_pulse_hidden_negative_worker_impact_filter_min_true_rc"] = -30.0
            config["journey_sharded_pulse_hidden_negative_worker_min_followup_time_after_add"] = 0.4
        if profile == "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_early_cg":
            config["journey_sharded_pulse_hidden_negative_worker_continue_only_on_active_support"] = True
            config["journey_sharded_pulse_hidden_negative_worker_inactive_success_cooldown_rounds"] = 2
            config["journey_sharded_pulse_hidden_negative_worker_continue_same_iteration_after_add"] = True
            config["journey_sharded_pulse_hidden_negative_worker_impact_filter_min_true_rc"] = -30.0
            config["journey_sharded_pulse_hidden_negative_worker_min_followup_time_after_add"] = 0.4
            config["journey_sharded_pulse_hidden_negative_worker_max_cg_iter"] = 1
        if profile == "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown":
            config["journey_sharded_pulse_hidden_negative_worker_continue_only_on_active_support"] = True
            config["journey_sharded_pulse_hidden_negative_worker_inactive_success_cooldown_rounds"] = 2
            config["journey_sharded_pulse_hidden_negative_worker_continue_same_iteration_after_add"] = True
            config["journey_sharded_pulse_hidden_negative_worker_impact_filter_min_true_rc"] = -30.0
            config["journey_sharded_pulse_hidden_negative_worker_min_followup_time_after_add"] = 0.4
            config["journey_sharded_pulse_hidden_negative_worker_failure_cooldown_rounds"] = 2
        if profile == "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_hard_tail_fingerprint":
            config["journey_sharded_pulse_hidden_negative_worker_continue_only_on_active_support"] = True
            config["journey_sharded_pulse_hidden_negative_worker_inactive_success_cooldown_rounds"] = 2
            config["journey_sharded_pulse_hidden_negative_worker_continue_same_iteration_after_add"] = True
            config["journey_sharded_pulse_hidden_negative_worker_impact_filter_min_true_rc"] = -30.0
            config["journey_sharded_pulse_hidden_negative_worker_min_followup_time_after_add"] = 0.4
            config["journey_sharded_pulse_hidden_negative_worker_failure_cooldown_rounds"] = 2
            config["journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled"] = True
            config["journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds"] = 1
            config["journey_sharded_pulse_worker_current_probe_min_no_column_rounds"] = 1
        if profile == "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown_ordered":
            config["journey_sharded_pulse_hidden_negative_worker_task_ordering"] = "reduced_cost_proxy"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip():
            records.append(json.loads(raw))
    return records


def _last_official_pricing(records: list[dict[str, Any]]) -> dict[str, Any]:
    for record in reversed(records):
        if record.get("event") != "journey_pricing":
            continue
        if record.get("pricing_kind") == "sharded_pulse_hidden_negative_worker":
            continue
        if record.get("final_judge_engine") in {"sharded_pulse", "sharded_pulse_dummy"}:
            continue
        return record
    return {}


def _last_real_audit(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    for record in reversed(records):
        if not bool(record.get("pulse_audit_skipped", False)):
            return record
    return None


def _last_real_worker(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    for record in reversed(records):
        if not bool(record.get("pulse_worker_skipped", False)):
            return record
    return None


def _worker_added_journeys(records: list[dict[str, Any]]) -> int:
    total = 0
    for record in _worker_addition_records(records):
        total += _as_int(record.get("added_journeys"))
    return total


def _worker_addition_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        record
        for record in records
        if record.get("event") == "journey_column_addition"
        and record.get("pricing_kind") == "sharded_pulse_hidden_negative_worker"
    ]


def _first_record_index(records: list[dict[str, Any]], target: dict[str, Any]) -> int | None:
    for index, record in enumerate(records):
        if record is target:
            return index
    for index, record in enumerate(records):
        if record == target:
            return index
    return None


def _legacy_final_judge_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    legacy = []
    for record in records:
        if record.get("event") != "journey_pricing":
            continue
        kind = str(record.get("pricing_kind", ""))
        if kind == "sharded_pulse_hidden_negative_worker":
            continue
        if kind == "heuristic":
            continue
        if kind.startswith("exact"):
            legacy.append(record)
    return legacy


def _completion_bound_retry_count(records: list[dict[str, Any]]) -> int:
    count = 0
    for record in records:
        if record.get("event") == "journey_exact_pricing_completion_bound_retry":
            count += 1
            continue
        if record.get("event") != "journey_pricing":
            continue
        kind = str(record.get("pricing_kind", ""))
        if "completion_bound" in kind and "retry" in kind:
            count += 1
    return count


def _completion_bound_retry_time(records: list[dict[str, Any]]) -> float:
    total = 0.0
    for record in records:
        retry_event = record.get("event") == "journey_exact_pricing_completion_bound_retry"
        retry_pricing = (
            record.get("event") == "journey_pricing"
            and "completion_bound" in str(record.get("pricing_kind", ""))
            and "retry" in str(record.get("pricing_kind", ""))
        )
        if retry_event or retry_pricing:
            total += float(record.get("time") or 0.0)
    return total


def _official_pricing_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    official: list[dict[str, Any]] = []
    for record in records:
        if record.get("event") != "journey_pricing":
            continue
        if record.get("pricing_kind") == "sharded_pulse_hidden_negative_worker":
            continue
        if record.get("final_judge_engine") in {"sharded_pulse", "sharded_pulse_dummy"}:
            continue
        official.append(record)
    return official


def _profile_dp_tail_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    pricing_records = _official_pricing_records(records)
    profile_records = [
        record
        for record in pricing_records
        if (
            "profile_dp" in str(record.get("reason", ""))
            or float(record.get("profile_dp_time") or 0.0) > 0.0
            or _as_int(record.get("dp_state_count")) > 0
            or _as_int(record.get("dp_processed_labels")) > 0
            or _as_int(record.get("dp_nonempty_mask_count")) > 0
            or _as_int(record.get("dp_max_labels_per_mask_observed")) > 0
            or bool(record.get("dp_top_mask_label_counts"))
        )
    ]
    if not profile_records:
        return {
            "profile_dp_tail_records": 0,
            "profile_dp_tail_incomplete_count": 0,
            "profile_dp_tail_negative_count": 0,
            "profile_dp_tail_no_negative_count": 0,
            "profile_dp_tail_state_cap_hit_count": 0,
            "profile_dp_tail_mask_cap_incomplete_count": 0,
            "profile_dp_tail_time": 0.0,
            "profile_dp_tail_state_count_max": 0,
            "profile_dp_tail_processed_labels_max": 0,
            "profile_dp_tail_extension_attempts": 0,
            "profile_dp_tail_nonempty_mask_count_max": 0,
            "profile_dp_tail_max_labels_per_mask_observed_max": 0,
            "profile_dp_tail_top_mask_label_counts": "",
            "profile_dp_tail_min_best_rc": None,
            "profile_dp_tail_class": "no_profile_dp_tail",
            "profile_dp_tail_reason": "no official pricing record reported profile-DP work",
            "profile_dp_tail_label_cap_pruned": 0,
            "profile_dp_tail_selected_candidate_input_count": 0,
            "profile_dp_tail_selected_candidate_scanned_count": 0,
            "profile_dp_tail_selected_candidate_materialized_count": 0,
            "profile_dp_tail_selected_candidate_returned_count": 0,
            "profile_dp_tail_selected_candidate_filtered_count": 0,
            "profile_dp_tail_selected_unmaterialized_candidate_count": 0,
            "profile_dp_tail_materialization_candidate_count": 0,
            "profile_dp_tail_materialization_selected_candidate_count": 0,
            "profile_dp_tail_materialization_infeasible_filtered_count": 0,
            "profile_dp_tail_hotspot_class": "no_profile_dp_tail",
            "profile_dp_tail_hotspot_reason": "no official pricing record reported profile-DP work",
        }
    incomplete_records = [
        record
        for record in profile_records
        if "profile_dp_incomplete" in str(record.get("reason", ""))
        or "profile_mask_cap_incomplete" in str(record.get("reason", ""))
    ]
    negative_records = [
        record
        for record in profile_records
        if str(record.get("pricing_state", "")) == "FOUND_NEGATIVE"
        or _as_float_or_none(record.get("best_reduced_cost")) is not None
        and float(record.get("best_reduced_cost")) < -1.0e-6
    ]
    no_negative_records = [
        record
        for record in profile_records
        if str(record.get("pricing_state", "")) in {
            "CERTIFIED_NO_NEGATIVE",
            "HEURISTIC_NO_NEGATIVE",
            "DUPLICATE_ONLY",
        }
    ]
    state_cap_records = [
        record
        for record in profile_records
        if (
            _as_int(record.get("pricing_max_dp_states")) > 0
            and _as_int(record.get("dp_state_count")) >= _as_int(record.get("pricing_max_dp_states"))
        )
        or "state_cap" in str(record.get("reason", ""))
    ]
    incomplete_state_cap_records = [
        record for record in incomplete_records if record in state_cap_records
    ]
    mask_cap_records = [
        record
        for record in incomplete_records
        if "profile_mask_cap_incomplete" in str(record.get("reason", ""))
        or _as_int(record.get("profile_mask_cap_pruned")) > 0
    ]
    structural_record = max(
        profile_records,
        key=lambda record: (
            _as_int(record.get("dp_max_labels_per_mask_observed")),
            _as_int(record.get("dp_state_count")),
            _as_int(record.get("dp_processed_labels")),
        ),
        default={},
    )
    best_rc_values = [
        value
        for value in (
            _as_float_or_none(record.get("best_reduced_cost"))
            for record in profile_records
        )
        if value is not None
    ]
    profile_dp_class, profile_dp_reason = _classify_profile_dp_tail(
        profile_records=profile_records,
        incomplete_records=incomplete_records,
        negative_records=negative_records,
        no_negative_records=no_negative_records,
        state_cap_records=incomplete_state_cap_records,
        mask_cap_records=mask_cap_records,
    )
    selected_candidate_filtered_count = sum(
        _as_int(record.get("profile_selected_candidate_branch_filtered_count"))
        + _as_int(record.get("profile_selected_candidate_duplicate_signature_filtered_count"))
        + _as_int(record.get("profile_selected_candidate_duplicate_task_set_filtered_count"))
        + _as_int(record.get("profile_selected_candidate_forbidden_signature_filtered_count"))
        + _as_int(record.get("profile_selected_candidate_dominated_task_set_filtered_count"))
        for record in profile_records
    )
    label_cap_pruned = sum(_as_int(record.get("dp_label_cap_pruned")) for record in profile_records)
    selected_input_count = sum(
        _as_int(record.get("profile_selected_candidate_input_count"))
        for record in profile_records
    )
    selected_scanned_count = sum(
        _as_int(record.get("profile_selected_candidate_scanned_count"))
        for record in profile_records
    )
    selected_materialized_count = sum(
        _as_int(record.get("profile_selected_candidate_materialized_count"))
        for record in profile_records
    )
    selected_returned_count = sum(
        _as_int(record.get("profile_selected_candidate_returned_count"))
        for record in profile_records
    )
    selected_unmaterialized_count = sum(
        _as_int(record.get("profile_selected_unmaterialized_candidate_count"))
        for record in profile_records
    )
    materialization_candidate_count = sum(
        _as_int(record.get("profile_materialization_candidate_count"))
        for record in profile_records
    )
    materialization_selected_candidate_count = sum(
        _as_int(record.get("profile_materialization_selected_candidate_count"))
        for record in profile_records
    )
    materialization_infeasible_filtered_count = sum(
        _as_int(record.get("profile_materialization_infeasible_candidates_filtered"))
        for record in profile_records
    )
    max_labels_observed = max(
        (
            _as_int(record.get("dp_max_labels_per_mask_observed"))
            for record in profile_records
        ),
        default=0,
    )
    hotspot_class, hotspot_reason = _classify_profile_dp_hotspot(
        profile_records=profile_records,
        label_cap_pruned=label_cap_pruned,
        max_labels_per_mask_observed=max_labels_observed,
        selected_input_count=selected_input_count,
        selected_materialized_count=selected_materialized_count,
        selected_returned_count=selected_returned_count,
        selected_candidate_filtered_count=selected_candidate_filtered_count,
        selected_unmaterialized_count=selected_unmaterialized_count,
        materialization_candidate_count=materialization_candidate_count,
        materialization_infeasible_filtered_count=materialization_infeasible_filtered_count,
    )
    return {
        "profile_dp_tail_records": len(profile_records),
        "profile_dp_tail_incomplete_count": len(incomplete_records),
        "profile_dp_tail_negative_count": len(negative_records),
        "profile_dp_tail_no_negative_count": len(no_negative_records),
        "profile_dp_tail_state_cap_hit_count": len(state_cap_records),
        "profile_dp_tail_mask_cap_incomplete_count": len(mask_cap_records),
        "profile_dp_tail_time": sum(
            float(record.get("profile_dp_time") or 0.0) for record in profile_records
        ),
        "profile_dp_tail_state_count_max": max(
            (_as_int(record.get("dp_state_count")) for record in profile_records),
            default=0,
        ),
        "profile_dp_tail_processed_labels_max": max(
            (_as_int(record.get("dp_processed_labels")) for record in profile_records),
            default=0,
        ),
        "profile_dp_tail_extension_attempts": sum(
            _as_int(record.get("dp_extension_attempts")) for record in profile_records
        ),
        "profile_dp_tail_nonempty_mask_count_max": max(
            (_as_int(record.get("dp_nonempty_mask_count")) for record in profile_records),
            default=0,
        ),
        "profile_dp_tail_max_labels_per_mask_observed_max": max(
            (
                _as_int(record.get("dp_max_labels_per_mask_observed"))
                for record in profile_records
            ),
            default=0,
        ),
        "profile_dp_tail_top_mask_label_counts": _compact_json_string(
            structural_record.get("dp_top_mask_label_counts")
        ),
        "profile_dp_tail_min_best_rc": min(best_rc_values) if best_rc_values else None,
        "profile_dp_tail_class": profile_dp_class,
        "profile_dp_tail_reason": profile_dp_reason,
        "profile_dp_tail_label_cap_pruned": int(label_cap_pruned),
        "profile_dp_tail_selected_candidate_input_count": int(selected_input_count),
        "profile_dp_tail_selected_candidate_scanned_count": int(selected_scanned_count),
        "profile_dp_tail_selected_candidate_materialized_count": int(selected_materialized_count),
        "profile_dp_tail_selected_candidate_returned_count": int(selected_returned_count),
        "profile_dp_tail_selected_candidate_filtered_count": int(selected_candidate_filtered_count),
        "profile_dp_tail_selected_unmaterialized_candidate_count": int(selected_unmaterialized_count),
        "profile_dp_tail_materialization_candidate_count": int(materialization_candidate_count),
        "profile_dp_tail_materialization_selected_candidate_count": int(materialization_selected_candidate_count),
        "profile_dp_tail_materialization_infeasible_filtered_count": int(materialization_infeasible_filtered_count),
        "profile_dp_tail_hotspot_class": hotspot_class,
        "profile_dp_tail_hotspot_reason": hotspot_reason,
    }


def _classify_profile_dp_tail(
    *,
    profile_records: list[dict[str, Any]],
    incomplete_records: list[dict[str, Any]],
    negative_records: list[dict[str, Any]],
    no_negative_records: list[dict[str, Any]],
    state_cap_records: list[dict[str, Any]],
    mask_cap_records: list[dict[str, Any]],
) -> tuple[str, str]:
    if not profile_records:
        return ("no_profile_dp_tail", "no profile-DP pricing records")
    if state_cap_records:
        return (
            "profile_dp_state_cap_tail",
            f"{len(state_cap_records)} profile-DP records reached max state cap",
        )
    if mask_cap_records:
        return (
            "profile_dp_mask_cap_tail",
            f"{len(mask_cap_records)} profile-DP records hit profile mask cap",
        )
    if incomplete_records:
        return (
            "profile_dp_incomplete_tail",
            f"{len(incomplete_records)} profile-DP records ended incomplete",
        )
    if negative_records and no_negative_records:
        return (
            "profile_dp_mixed_negative_no_negative_tail",
            f"{len(negative_records)} negative and {len(no_negative_records)} no-negative records",
        )
    if negative_records:
        return ("profile_dp_negative_tail", f"{len(negative_records)} profile-DP negative records")
    if no_negative_records:
        return (
            "profile_dp_no_negative_tail",
            f"{len(no_negative_records)} profile-DP no-negative records",
        )
    return ("profile_dp_other_tail", "profile-DP records present without classified terminal state")


def _classify_profile_dp_hotspot(
    *,
    profile_records: list[dict[str, Any]],
    label_cap_pruned: int,
    max_labels_per_mask_observed: int,
    selected_input_count: int,
    selected_materialized_count: int,
    selected_returned_count: int,
    selected_candidate_filtered_count: int,
    selected_unmaterialized_count: int,
    materialization_candidate_count: int,
    materialization_infeasible_filtered_count: int,
) -> tuple[str, str]:
    if not profile_records:
        return ("no_profile_dp_tail", "no profile-DP pricing records")
    if int(label_cap_pruned) > 0:
        return (
            "profile_dp_label_cap_active",
            f"profile-DP label cap pruned {int(label_cap_pruned)} labels",
        )
    if int(materialization_candidate_count) > 0 and int(selected_returned_count) <= 0:
        return (
            "profile_dp_materialization_gap",
            f"{int(materialization_candidate_count)} materialization candidates produced no returned journey",
        )
    if int(selected_input_count) > 0 and int(selected_returned_count) <= 0:
        blocked = (
            int(selected_candidate_filtered_count)
            + int(selected_unmaterialized_count)
            + int(materialization_infeasible_filtered_count)
        )
        return (
            "profile_dp_selected_candidate_gap",
            f"{int(selected_input_count)} selected candidates produced no returned journey; blocked={blocked}",
        )
    if int(max_labels_per_mask_observed) >= 48:
        return (
            "profile_dp_severe_mask_hotspot",
            f"max labels per mask observed={int(max_labels_per_mask_observed)}",
        )
    if int(max_labels_per_mask_observed) >= 24:
        return (
            "profile_dp_mask_hotspot",
            f"max labels per mask observed={int(max_labels_per_mask_observed)}",
        )
    return (
        "profile_dp_no_mask_hotspot",
        f"max labels per mask observed={int(max_labels_per_mask_observed)}",
    )


def _sum_pricing_field(records: list[dict[str, Any]], field: str) -> int:
    total = 0
    for record in records:
        if record.get("event") != "journey_pricing":
            continue
        if record.get("pricing_kind") == "sharded_pulse_hidden_negative_worker":
            continue
        total += _as_int(record.get(field))
    return total


def _pool_structure_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    events = [
        record
        for record in records
        if record.get("event") == "journey_pool_structure_diagnostics"
    ]
    if not events:
        return {
            "pool_diag_events": 0,
            "pool_journeys_last": 0,
            "pool_unique_task_sets_last": 0,
            "pool_duplicate_task_sets_last": 0,
            "pool_duplicate_task_set_ratio_last": None,
            "pool_duplicate_task_set_ratio_max": None,
            "pool_avg_journeys_per_task_set_last": None,
            "pool_max_journeys_per_task_set_last": 0,
            "pool_active_journeys_last": 0,
            "pool_active_task_sets_last": 0,
            "pool_active_duplicate_task_sets_last": 0,
            "pool_active_duplicate_task_set_ratio_last": None,
            "pool_active_duplicate_task_set_ratio_max": None,
            "pool_active_avg_journeys_per_task_set_last": None,
            "pool_active_fractional_journeys_last": 0,
            "pool_active_fractional_ratio_last": None,
            "pool_active_fractional_ratio_max": None,
            "pool_active_fractional_value_sum_last": None,
            "pool_active_fractional_value_max_last": None,
            "pool_active_fractional_value_min_last": None,
            "pool_active_fractional_small_value_count_last": 0,
            "pool_active_total_value_last": None,
            "pool_active_max_value_last": None,
            "pool_active_singleton_task_sets_last": 0,
            "pool_active_multi_task_sets_last": 0,
            "pool_active_task_count_union_last": 0,
            "pool_active_task_set_hash_first": "",
            "pool_active_task_set_hash_last": "",
            "pool_active_task_set_hash_sequence": "",
            "pool_active_task_set_hash_unique_count": 0,
            "pool_active_task_set_hash_churn_count": 0,
            "pool_active_top_task_set_value_samples_first": "",
            "pool_active_top_task_set_value_samples_last": "",
            "pool_active_trajectory_class": "no_pool_diagnostics",
            "pool_active_trajectory_reason": "no pool structure diagnostics events",
        }
    last = events[-1]
    first = events[0]
    active_hashes = [
        str(event.get("pool_active_task_set_hash", ""))
        for event in events
        if str(event.get("pool_active_task_set_hash", ""))
    ]
    active_hash_churn_count = 0
    previous_active_hash = None
    for active_hash in active_hashes:
        if previous_active_hash is not None and active_hash != previous_active_hash:
            active_hash_churn_count += 1
        previous_active_hash = active_hash
    active_trajectory_class, active_trajectory_reason = _classify_active_pool_trajectory(
        active_hashes=active_hashes,
        churn_count=active_hash_churn_count,
    )
    duplicate_ratios = [
        float(event.get("pool_duplicate_task_set_ratio"))
        for event in events
        if event.get("pool_duplicate_task_set_ratio") is not None
    ]
    fractional_ratios = [
        float(event.get("pool_active_fractional_ratio"))
        for event in events
        if event.get("pool_active_fractional_ratio") is not None
    ]
    active_duplicate_ratios = [
        float(event.get("pool_active_duplicate_task_set_ratio"))
        for event in events
        if event.get("pool_active_duplicate_task_set_ratio") is not None
    ]
    return {
        "pool_diag_events": len(events),
        "pool_journeys_last": _as_int(last.get("pool_journey_count")),
        "pool_unique_task_sets_last": _as_int(last.get("pool_unique_task_set_count")),
        "pool_duplicate_task_sets_last": _as_int(last.get("pool_duplicate_task_set_count")),
        "pool_duplicate_task_set_ratio_last": last.get("pool_duplicate_task_set_ratio"),
        "pool_duplicate_task_set_ratio_max": max(duplicate_ratios, default=None),
        "pool_avg_journeys_per_task_set_last": last.get("pool_avg_journeys_per_task_set"),
        "pool_max_journeys_per_task_set_last": _as_int(last.get("pool_max_journeys_per_task_set")),
        "pool_active_journeys_last": _as_int(last.get("pool_active_journey_count")),
        "pool_active_task_sets_last": _as_int(last.get("pool_active_task_set_count")),
        "pool_active_duplicate_task_sets_last": _as_int(last.get("pool_active_duplicate_task_set_count")),
        "pool_active_duplicate_task_set_ratio_last": last.get("pool_active_duplicate_task_set_ratio"),
        "pool_active_duplicate_task_set_ratio_max": max(active_duplicate_ratios, default=None),
        "pool_active_avg_journeys_per_task_set_last": last.get("pool_active_avg_journeys_per_task_set"),
        "pool_active_fractional_journeys_last": _as_int(last.get("pool_active_fractional_journey_count")),
        "pool_active_fractional_ratio_last": last.get("pool_active_fractional_ratio"),
        "pool_active_fractional_ratio_max": max(fractional_ratios, default=None),
        "pool_active_fractional_value_sum_last": last.get("pool_active_fractional_value_sum"),
        "pool_active_fractional_value_max_last": last.get("pool_active_fractional_value_max"),
        "pool_active_fractional_value_min_last": last.get("pool_active_fractional_value_min"),
        "pool_active_fractional_small_value_count_last": _as_int(
            last.get("pool_active_fractional_small_value_count")
        ),
        "pool_active_total_value_last": last.get("pool_active_total_value"),
        "pool_active_max_value_last": last.get("pool_active_max_value"),
        "pool_active_singleton_task_sets_last": _as_int(last.get("pool_active_singleton_task_set_count")),
        "pool_active_multi_task_sets_last": _as_int(last.get("pool_active_multi_task_set_count")),
        "pool_active_task_count_union_last": _as_int(last.get("pool_active_task_count_union")),
        "pool_active_task_set_hash_first": str(first.get("pool_active_task_set_hash", "")),
        "pool_active_task_set_hash_last": str(last.get("pool_active_task_set_hash", "")),
        "pool_active_task_set_hash_sequence": _compact_json_string(active_hashes[:12]),
        "pool_active_task_set_hash_unique_count": len(set(active_hashes)),
        "pool_active_task_set_hash_churn_count": active_hash_churn_count,
        "pool_active_top_task_set_value_samples_first": _compact_json_string(
            first.get("pool_active_top_task_set_value_samples")
        ),
        "pool_active_top_task_set_value_samples_last": _compact_json_string(
            last.get("pool_active_top_task_set_value_samples")
        ),
        "pool_active_trajectory_class": active_trajectory_class,
        "pool_active_trajectory_reason": active_trajectory_reason,
    }


def _classify_active_pool_trajectory(
    *,
    active_hashes: list[str],
    churn_count: int,
) -> tuple[str, str]:
    if not active_hashes:
        return ("no_active_basis", "pool diagnostics contained no active task-set hash")
    unique_count = len(set(active_hashes))
    if unique_count <= 1:
        return ("stable_active_basis", "active task-set hash did not change")
    if int(churn_count) >= 3:
        return (
            "high_churn_active_basis",
            f"active task-set hash changed {int(churn_count)} times across {len(active_hashes)} diagnostics",
        )
    return (
        "churn_active_basis",
        f"active task-set hash changed {int(churn_count)} times across {len(active_hashes)} diagnostics",
    )


def _early_column_trajectory_metrics(records: list[dict[str, Any]], *, limit: int = 8) -> dict[str, Any]:
    additions = [
        (index, record)
        for index, record in enumerate(records)
        if record.get("event") == "journey_column_addition"
    ]
    if not additions:
        return {
            "early_column_addition_events": 0,
            "early_column_addition_kind_sequence": "",
            "early_column_primary_task_set_sequence": "",
            "early_column_changed_task_set_hash_sequence": "",
            "early_column_new_task_set_hash_sequence": "",
            "early_column_productivity_class_sequence": "",
            "early_column_active_hash_before_sequence": "",
            "early_column_active_hash_after_sequence": "",
            "early_column_active_hash_transition_count": 0,
            "early_column_changed_active_relation_before_sequence": "",
            "early_column_changed_active_relation_after_sequence": "",
            "early_column_active_changed_task_set_count": 0,
            "early_column_trajectory_class": "no_early_additions",
            "early_column_trajectory_reason": "no journey_column_addition events",
        }

    limited = additions[: max(0, int(limit))]
    pricing_kinds: list[str] = []
    primary_task_sets: list[list[int]] = []
    changed_hashes: list[str] = []
    new_hashes: list[str] = []
    productivity_classes: list[str] = []
    active_hashes_before: list[str] = []
    active_hashes_after: list[str] = []
    relation_before: list[str] = []
    relation_after: list[str] = []
    active_changed_task_set_count = 0
    active_hash_transition_count = 0

    for index, addition in limited:
        pricing_kind = str(addition.get("pricing_kind", ""))
        if pricing_kind:
            pricing_kinds.append(pricing_kind)
        changed_hash = str(addition.get("changed_task_set_hash", ""))
        if changed_hash:
            changed_hashes.append(changed_hash)
        new_hash = str(addition.get("new_task_set_hash", ""))
        if new_hash:
            new_hashes.append(new_hash)
        productivity_class = str(addition.get("addition_productivity_class", ""))
        if productivity_class:
            productivity_classes.append(productivity_class)
        active_changed_task_set_count += _as_int(addition.get("active_changed_task_set_count"))

        primary_task_set = _primary_addition_task_set(addition)
        if primary_task_set:
            primary_task_sets.append(list(primary_task_set))

        pool_before = _last_pool_before_index(records, index)
        pool_after = _first_pool_after_index(records, index)
        active_hash_before = str(pool_before.get("pool_active_task_set_hash", ""))
        active_hash_after = str(pool_after.get("pool_active_task_set_hash", ""))
        if active_hash_before:
            active_hashes_before.append(active_hash_before)
        if active_hash_after:
            active_hashes_after.append(active_hash_after)
        if active_hash_before and active_hash_after and active_hash_before != active_hash_after:
            active_hash_transition_count += 1
        if primary_task_set:
            relation_before.append(
                str(_active_task_set_value_from_pool_record(pool_before, primary_task_set)["relation"])
            )
            relation_after.append(
                str(_active_task_set_value_from_pool_record(pool_after, primary_task_set)["relation"])
            )

    trajectory_class, trajectory_reason = _classify_early_column_trajectory(
        addition_count=len(additions),
        active_changed_task_set_count=active_changed_task_set_count,
        active_hash_transition_count=active_hash_transition_count,
        relation_after=relation_after,
    )
    return {
        "early_column_addition_events": len(additions),
        "early_column_addition_kind_sequence": _compact_json_string(pricing_kinds),
        "early_column_primary_task_set_sequence": _compact_json_string(primary_task_sets),
        "early_column_changed_task_set_hash_sequence": _compact_json_string(changed_hashes),
        "early_column_new_task_set_hash_sequence": _compact_json_string(new_hashes),
        "early_column_productivity_class_sequence": _compact_json_string(productivity_classes),
        "early_column_active_hash_before_sequence": _compact_json_string(active_hashes_before),
        "early_column_active_hash_after_sequence": _compact_json_string(active_hashes_after),
        "early_column_active_hash_transition_count": active_hash_transition_count,
        "early_column_changed_active_relation_before_sequence": _compact_json_string(relation_before),
        "early_column_changed_active_relation_after_sequence": _compact_json_string(relation_after),
        "early_column_active_changed_task_set_count": active_changed_task_set_count,
        "early_column_trajectory_class": trajectory_class,
        "early_column_trajectory_reason": trajectory_reason,
    }


def _primary_addition_task_set(record: dict[str, Any]) -> tuple[int, ...]:
    for field in (
        "changed_task_set_samples",
        "new_task_set_samples",
        "requested_task_set_samples",
        "replacement_task_set_samples",
    ):
        sample = _first_record_task_set_sample(record, field)
        if sample:
            return sample
    return tuple()


def _last_pool_before_index(records: list[dict[str, Any]], index: int | None) -> dict[str, Any]:
    if index is None:
        return {}
    for record in reversed(records[: int(index)]):
        if record.get("event") == "journey_pool_structure_diagnostics":
            return record
    return {}


def _classify_early_column_trajectory(
    *,
    addition_count: int,
    active_changed_task_set_count: int,
    active_hash_transition_count: int,
    relation_after: list[str],
) -> tuple[str, str]:
    if int(addition_count) <= 0:
        return ("no_early_additions", "no journey_column_addition events")
    if int(active_changed_task_set_count) > 0:
        return (
            "active_support_changing_additions",
            f"active_changed_task_set_count={int(active_changed_task_set_count)}",
        )
    if any(str(relation) == "same_task_set" for relation in relation_after):
        return (
            "inactive_addition_enters_active_basis",
            "an inactive added task set appears in a later active basis sample",
        )
    if int(active_hash_transition_count) > 0:
        return (
            "inactive_additions_with_active_basis_transition",
            f"active basis hash changed after {int(active_hash_transition_count)} early additions",
        )
    return (
        "inactive_additions_no_active_basis_transition",
        "early additions did not change sampled active basis hash",
    )


def _dual_stabilization_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    events = [
        record
        for record in records
        if record.get("event") == "journey_dual_stabilization"
    ]
    if not events:
        return {
            "dual_stabilization_events": 0,
            "dual_stabilization_accepted_count": 0,
            "dual_stabilization_skipped_count": 0,
            "dual_stabilization_status_sequence": "",
            "dual_stabilization_source_sequence": "",
            "dual_stabilization_mode_sequence": "",
            "dual_stabilization_reference_sequence": "",
            "dual_stabilization_first_accepted_cg_iter": None,
            "dual_stabilization_current_pool_negative_count_max": 0,
            "dual_stabilization_objective_mismatch_count": 0,
            "dual_stabilization_current_pool_infeasible_count": 0,
            "dual_stabilization_time": 0.0,
            "dual_stabilization_effect_class": "not_run",
        }
    accepted_events = [event for event in events if bool(event.get("accepted", False))]
    skipped_events = [event for event in events if str(event.get("status", "")) == "SKIPPED"]
    non_skipped_events = [
        event for event in events if str(event.get("status", "")) != "SKIPPED"
    ]
    objective_mismatch_count = sum(
        int(not bool(event.get("objective_matches", True)))
        for event in non_skipped_events
    )
    current_pool_infeasible_count = sum(
        int(not bool(event.get("current_pool_dual_feasible", True)))
        for event in non_skipped_events
    )
    first_accepted_cg_iter = None
    if accepted_events:
        first_accepted_cg_iter = min(
            _as_int(event.get("cg_iter")) for event in accepted_events
        )
    if accepted_events:
        effect_class = "accepted_stabilized_dual"
    elif len(skipped_events) == len(events):
        effect_class = "all_skipped"
    elif objective_mismatch_count or current_pool_infeasible_count:
        effect_class = "rejected_inexact_or_infeasible"
    else:
        effect_class = "no_accepted_stabilized_dual"
    return {
        "dual_stabilization_events": len(events),
        "dual_stabilization_accepted_count": len(accepted_events),
        "dual_stabilization_skipped_count": len(skipped_events),
        "dual_stabilization_status_sequence": "|".join(
            str(event.get("status", "")) for event in events
        ),
        "dual_stabilization_source_sequence": "|".join(
            str(event.get("pricing_dual_source", "")) for event in events
        ),
        "dual_stabilization_mode_sequence": "|".join(
            str(event.get("mode", "")) for event in events if str(event.get("mode", ""))
        ),
        "dual_stabilization_reference_sequence": "|".join(
            str(event.get("reference", ""))
            for event in events
            if str(event.get("reference", ""))
        ),
        "dual_stabilization_first_accepted_cg_iter": first_accepted_cg_iter,
        "dual_stabilization_current_pool_negative_count_max": max(
            (
                _as_int(event.get("current_pool_negative_reduced_cost_count"))
                for event in events
            ),
            default=0,
        ),
        "dual_stabilization_objective_mismatch_count": objective_mismatch_count,
        "dual_stabilization_current_pool_infeasible_count": current_pool_infeasible_count,
        "dual_stabilization_time": sum(
            float(event.get("time") or 0.0) for event in events
        ),
        "dual_stabilization_effect_class": effect_class,
    }


def _record_task_set_samples(record: dict[str, Any], field: str) -> list[tuple[int, ...]]:
    raw_samples = record.get(field, [])
    if not isinstance(raw_samples, list):
        return []
    samples: list[tuple[int, ...]] = []
    for raw_sample in raw_samples:
        if not isinstance(raw_sample, (list, tuple, set)):
            continue
        sample = tuple(sorted(int(task) for task in raw_sample))
        if sample:
            samples.append(sample)
    return samples


def _first_record_task_set_sample(record: dict[str, Any], field: str) -> tuple[int, ...]:
    samples = _record_task_set_samples(record, field)
    return samples[0] if samples else tuple()


def _records_task_set_samples(records: list[dict[str, Any]], field: str) -> list[tuple[int, ...]]:
    samples: list[tuple[int, ...]] = []
    seen: set[tuple[int, ...]] = set()
    for record in records:
        for sample in _record_task_set_samples(record, field):
            if sample in seen:
                continue
            seen.add(sample)
            samples.append(sample)
    return samples


def _records_task_set_samples_any(records: list[dict[str, Any]], *fields: str) -> list[tuple[int, ...]]:
    samples: list[tuple[int, ...]] = []
    seen: set[tuple[int, ...]] = set()
    for field in fields:
        for sample in _records_task_set_samples(records, field):
            if sample in seen:
                continue
            seen.add(sample)
            samples.append(sample)
    return samples


def _first_nonempty_compact_field(records: list[dict[str, Any]], *fields: str) -> str:
    for field in fields:
        for record in records:
            value = record.get(field)
            if value:
                return _compact_json_string(value)
    return ""


def _last_nonempty_record_field(records: list[dict[str, Any]], field: str) -> str:
    for record in reversed(records):
        value = record.get(field)
        if value:
            return str(value)
    return ""


def _first_record_int_sequence_any(records: list[dict[str, Any]], *fields: str) -> tuple[int, ...]:
    for field in fields:
        for record in records:
            value = record.get(field)
            if isinstance(value, (list, tuple)):
                sequence: list[int] = []
                for item in value:
                    try:
                        sequence.append(int(item))
                    except (TypeError, ValueError):
                        sequence = []
                        break
                if sequence:
                    return tuple(sequence)
            if isinstance(value, str) and value.strip():
                sequence = []
                for raw_item in value.replace("[", "").replace("]", "").split(","):
                    raw_item = raw_item.strip()
                    if not raw_item:
                        continue
                    try:
                        sequence.append(int(raw_item))
                    except ValueError:
                        sequence = []
                        break
                if sequence:
                    return tuple(sequence)
    return tuple()


def _task_set_string(task_set: tuple[int, ...]) -> str:
    return ",".join(str(task) for task in task_set)


def _record_sequence_samples(record: dict[str, Any], field: str) -> list[tuple[tuple[int, ...], ...]]:
    raw_samples = record.get(field, [])
    if not isinstance(raw_samples, list):
        return []
    samples: list[tuple[tuple[int, ...], ...]] = []
    for raw_sample in raw_samples:
        if not isinstance(raw_sample, list):
            continue
        sorties: list[tuple[int, ...]] = []
        for raw_sortie in raw_sample:
            if not isinstance(raw_sortie, (list, tuple)):
                continue
            sortie = tuple(int(task) for task in raw_sortie)
            if sortie:
                sorties.append(sortie)
        if sorties:
            samples.append(tuple(sorties))
    return samples


def _first_record_sequence_sample(record: dict[str, Any], field: str) -> tuple[tuple[int, ...], ...]:
    samples = _record_sequence_samples(record, field)
    return samples[0] if samples else tuple()


def _sequence_sample_string(sample: tuple[tuple[int, ...], ...]) -> str:
    return "|".join(",".join(str(task) for task in sortie) for sortie in sample)


def _record_sequence_samples_string(record: dict[str, Any], field: str) -> str:
    return ";".join(_sequence_sample_string(sample) for sample in _record_sequence_samples(record, field))


def _record_signature_samples_string(record: dict[str, Any], field: str) -> str:
    raw_samples = record.get(field, [])
    if not isinstance(raw_samples, list):
        return ""
    return ";".join(str(sample) for sample in raw_samples if str(sample))


def _compact_json_string(value: Any) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _profile_dp_top_mask_task_sets(record: dict[str, Any]) -> list[tuple[int, ...]]:
    raw_items = record.get("dp_top_mask_label_counts", [])
    if isinstance(raw_items, str):
        try:
            raw_items = json.loads(raw_items)
        except json.JSONDecodeError:
            return []
    if not isinstance(raw_items, (list, tuple)):
        return []
    task_sets: list[tuple[int, ...]] = []
    for item in raw_items:
        if not isinstance(item, (list, tuple)) or len(item) < 3:
            continue
        raw_tasks = item[2]
        if not isinstance(raw_tasks, (list, tuple, set)):
            continue
        tasks = tuple(sorted(int(task) for task in raw_tasks))
        if tasks:
            task_sets.append(tasks)
    return task_sets


def _best_task_set_overlap(
    task_set: tuple[int, ...],
    worker_task_sets: list[tuple[int, ...]],
) -> dict[str, Any]:
    if not task_set or not worker_task_sets:
        return {"overlap": 0, "jaccard": None, "relation": "unknown"}
    left = set(task_set)
    best_overlap = 0
    best_jaccard = 0.0
    for worker_task_set in worker_task_sets:
        right = set(worker_task_set)
        if not right:
            continue
        overlap = len(left.intersection(right))
        union = len(left.union(right))
        jaccard = 0.0 if union <= 0 else float(overlap) / float(union)
        if jaccard > best_jaccard or (math.isclose(jaccard, best_jaccard) and overlap > best_overlap):
            best_jaccard = jaccard
            best_overlap = overlap
    if best_overlap == 0:
        relation = "disjoint_task_set"
    elif math.isclose(best_jaccard, 1.0):
        relation = "same_task_set"
    else:
        relation = "overlapping_task_set"
    return {
        "overlap": best_overlap,
        "jaccard": round(best_jaccard, 9),
        "relation": relation,
    }


def _worker_vs_ordinary_contrast_class(
    *,
    worker_added: bool,
    worker_task_set: tuple[int, ...],
    followup_task_set: tuple[int, ...],
    relation: str,
) -> str:
    if not worker_added:
        return "no_worker_add"
    if not followup_task_set:
        return "no_followup_negative"
    if not worker_task_set:
        return "unknown_worker_task_set"
    if relation == "same_task_set":
        return "same_task_set"
    if relation == "overlapping_task_set":
        return "overlapping_task_set"
    if relation == "disjoint_task_set":
        return "disjoint_residual_after_worker"
    return "unknown"


def _worker_followup_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    additions = _worker_addition_records(records)
    if not additions:
        return {
            "next_rmp_objective_delta": None,
            "next_dual_l1_delta": None,
            "worker_changed_task_set_count": 0,
            "worker_active_task_set_count": 0,
            "worker_inactive_task_set_count": 0,
            "worker_active_task_set_ratio": None,
            "wall_after_worker": None,
            "pricing_calls": 0,
            "heuristic_pricing_calls": 0,
            "exact_pricing_calls": 0,
            "exact_retry_pricing_calls": 0,
            "generated_sequences": 0,
            "evaluated_timed_trips": 0,
            "legacy_after_worker_calls": 0,
            "legacy_after_worker_time": 0.0,
            "completion_retry_after_worker_count": 0,
            "completion_retry_after_worker_time": 0.0,
            "hidden_negative_after_worker_count": 0,
            "worker_negative_after_worker_count": 0,
            "last_pricing_kind": "",
            "last_pricing_state": "",
            "last_pricing_reason": "",
            "last_best_rc": None,
            "tail_outcome": "no_worker_add",
            "negative_pricing_calls": 0,
            "incomplete_pricing_calls": 0,
            "min_best_rc": None,
            "pricing_state_sequence": "",
            "first_negative_cg_iter": None,
            "first_negative_pricing_kind": "",
            "first_negative_best_rc": None,
            "first_negative_task_set_hash": "",
            "first_negative_task_set": "",
            "first_negative_task_count": 0,
            "first_negative_sequence": "",
            "first_negative_signature_sample": "",
            "first_negative_overlap_to_worker": 0,
            "first_negative_jaccard_to_worker": None,
            "first_negative_relation_to_worker": "no_worker_add",
            "worker_vs_ordinary_first_worker_task_set": "",
            "worker_vs_ordinary_first_followup_task_set": "",
            "worker_vs_ordinary_task_set_overlap": 0,
            "worker_vs_ordinary_task_set_jaccard": None,
            "worker_vs_ordinary_task_set_relation": "no_worker_add",
            "worker_vs_ordinary_disjoint": False,
            "worker_vs_ordinary_worker_task_count": 0,
            "worker_vs_ordinary_followup_task_count": 0,
            "worker_vs_ordinary_task_count_delta": None,
            "worker_vs_ordinary_worker_added_before_followup": False,
            "worker_vs_ordinary_followup_returned_after_worker": False,
            "worker_vs_ordinary_contrast_class": "no_worker_add",
            "worker_negative_pool_task_set_samples": "",
            "worker_negative_pool_sequence_samples": "",
            "worker_negative_pool_signature_samples": "",
            "worker_harvested_task_set_samples": "",
            "worker_harvested_sequence_samples": "",
            "worker_harvested_signature_samples": "",
            "worker_returned_candidate_task_set_samples": "",
            "worker_returned_candidate_sequence_samples": "",
            "worker_returned_candidate_signature_samples": "",
            "worker_vs_ordinary_negative_pool_overlap": 0,
            "worker_vs_ordinary_negative_pool_jaccard": None,
            "worker_vs_ordinary_negative_pool_relation": "no_worker_add",
            "worker_vs_ordinary_negative_pool_exact": False,
            "worker_vs_ordinary_harvested_overlap": 0,
            "worker_vs_ordinary_harvested_jaccard": None,
            "worker_vs_ordinary_harvested_relation": "no_worker_add",
            "worker_vs_ordinary_harvested_exact": False,
            "worker_vs_ordinary_returned_candidate_overlap": 0,
            "worker_vs_ordinary_returned_candidate_jaccard": None,
            "worker_vs_ordinary_returned_candidate_relation": "no_worker_add",
            "worker_vs_ordinary_returned_candidate_exact": False,
            "worker_target_sequence_task_set": "",
            "worker_target_negative_pool_overlap": 0,
            "worker_target_negative_pool_jaccard": None,
            "worker_target_negative_pool_relation": "no_worker_add",
            "worker_target_negative_pool_exact": False,
            "worker_target_harvested_overlap": 0,
            "worker_target_harvested_jaccard": None,
            "worker_target_harvested_relation": "no_worker_add",
            "worker_target_harvested_exact": False,
            "worker_target_returned_candidate_overlap": 0,
            "worker_target_returned_candidate_jaccard": None,
            "worker_target_returned_candidate_relation": "no_worker_add",
            "worker_target_returned_candidate_exact": False,
            "first_negative_profile_dp_top_overlap": 0,
            "first_negative_profile_dp_top_jaccard": None,
            "first_negative_profile_dp_top_relation": "no_worker_add",
            "first_negative_profile_dp_top_exact": False,
            "first_negative_profile_reachable_overlap": 0,
            "first_negative_profile_reachable_jaccard": None,
            "first_negative_profile_reachable_relation": "no_worker_add",
            "first_negative_profile_reachable_exact": False,
            "first_negative_profile_negative_overlap": 0,
            "first_negative_profile_negative_jaccard": None,
            "first_negative_profile_negative_relation": "no_worker_add",
            "first_negative_profile_negative_exact": False,
            "first_negative_profile_selected_overlap": 0,
            "first_negative_profile_selected_jaccard": None,
            "first_negative_profile_selected_relation": "no_worker_add",
            "first_negative_profile_selected_exact": False,
            "first_negative_profile_materialized_overlap": 0,
            "first_negative_profile_materialized_jaccard": None,
            "first_negative_profile_materialized_relation": "no_worker_add",
            "first_negative_profile_materialized_exact": False,
            "first_negative_profile_returned_overlap": 0,
            "first_negative_profile_returned_jaccard": None,
            "first_negative_profile_returned_relation": "no_worker_add",
            "first_negative_profile_returned_exact": False,
            "first_negative_profile_unmaterialized_overlap": 0,
            "first_negative_profile_unmaterialized_jaccard": None,
            "first_negative_profile_unmaterialized_relation": "no_worker_add",
            "first_negative_profile_unmaterialized_exact": False,
            "first_negative_profile_weak_filtered_overlap": 0,
            "first_negative_profile_weak_filtered_jaccard": None,
            "first_negative_profile_weak_filtered_relation": "no_worker_add",
            "first_negative_profile_weak_filtered_exact": False,
            "first_negative_profile_filtered_overlap": 0,
            "first_negative_profile_filtered_jaccard": None,
            "first_negative_profile_filtered_relation": "no_worker_add",
            "first_negative_profile_filtered_exact": False,
            "proof_tail_bridge_class": "no_worker_add",
            "proof_tail_bridge_reason": "no worker-added column before follow-up pricing",
            "returned_residual_tail_class": "no_worker_add",
            "returned_residual_tail_reason": "no worker-added column before follow-up pricing",
            "negative_task_set_sequence": "",
            "negative_task_set_unique_count": 0,
            "negative_task_set_repeat_count": 0,
            "first_negative_addition_productivity_class": "",
            "first_negative_added_journeys": 0,
            "first_negative_added_new_task_set_count": 0,
            "first_negative_added_replacement_count": 0,
            "first_negative_added_support_changing_count": 0,
            "post_first_negative_rmp_objective_delta": None,
            "post_first_negative_dual_l1_delta": None,
            "first_negative_active_after_addition": False,
            "first_negative_active_value_after_addition": None,
            "first_negative_active_journey_count_after_addition": 0,
            "first_negative_active_relation_after_addition": "no_worker_add",
            "active_fractional_ratio_after_first_negative": None,
            "active_total_value_after_first_negative": None,
            "active_task_set_hash_after_first_negative": "",
            "rmp_residual_impact_class": "no_worker_add",
            "rmp_residual_impact_reason": "no worker-added column before follow-up pricing",
            "first_negative_active_persistence_count": 0,
            "first_negative_active_value_sequence": "",
            "first_negative_active_last_value": None,
            "active_basis_hash_sequence_after_first_negative": "",
            "active_basis_unique_count_after_first_negative": 0,
            "active_basis_churn_count_after_first_negative": 0,
            "negative_family_after_first_count": 0,
            "negative_family_after_first_relation_sequence": "",
            "negative_family_after_first_disjoint_count": 0,
            "negative_family_after_first_overlapping_count": 0,
            "negative_family_after_first_same_count": 0,
            "negative_family_after_first_max_overlap": 0,
            "negative_family_after_first_max_jaccard": None,
            "residual_family_chain_class": "no_worker_add",
            "residual_family_chain_reason": "no worker-added column before follow-up pricing",
            "post_first_negative_pool_duplicate_task_sets": 0,
            "post_first_negative_pool_duplicate_task_set_ratio": None,
            "post_first_negative_pool_active_duplicate_task_sets": 0,
            "post_first_negative_pool_active_duplicate_task_set_ratio": None,
            "post_first_negative_pool_avg_journeys_per_task_set": None,
            "post_first_negative_pool_max_journeys_per_task_set": 0,
            "post_first_negative_pool_active_avg_journeys_per_task_set": None,
            "post_first_negative_pool_active_fractional_value_sum": None,
            "post_first_negative_pool_active_fractional_value_max": None,
            "post_first_negative_pool_active_fractional_value_min": None,
            "post_first_negative_pool_active_fractional_small_value_count": 0,
            "rmp_degeneracy_pressure_class": "no_worker_add",
            "rmp_degeneracy_pressure_reason": "no worker-added column before follow-up pricing",
            "post_first_negative_dual_objective_abs_ratio": None,
            "post_first_negative_dual_move_class": "no_worker_add",
            "pool_compression_candidate_class": "no_worker_add",
            "pool_compression_candidate_reason": "no worker-added column before follow-up pricing",
            "rmp_stabilization_candidate_class": "no_worker_add",
            "rmp_stabilization_candidate_reason": "no worker-added column before follow-up pricing",
            "stabilization_diagnostic_design_class": "no_worker_add",
            "stabilization_diagnostic_design_reason": "no worker-added column before follow-up pricing",
            "stabilization_diagnostic_recommended_profile": "",
            "stabilization_diagnostic_guarded_config_keys": "",
            "stabilization_diagnostic_certificate_effect_allowed": False,
            "stabilization_probe_enabled": False,
            "stabilization_probe_status": "no_worker_add",
            "stabilization_probe_reason": "no worker-added column before follow-up pricing",
            "stabilization_probe_mode": "",
            "stabilization_probe_candidate_source": "no_worker_add",
            "stabilization_probe_anchor_weight": 0.0,
            "stabilization_probe_context_hash_required": False,
            "stabilization_probe_context_hash": "",
            "stabilization_probe_certificate_effect_allowed": False,
            "stabilization_probe_official_effect_allowed": False,
            "stabilization_probe_mutates_rmp": False,
            "stabilization_probe_design_profile": "",
            "profile_selected_candidate_input_count": 0,
            "profile_selected_candidate_scanned_count": 0,
            "profile_selected_candidate_materialized_count": 0,
            "profile_selected_candidate_returned_count": 0,
            "profile_selected_candidate_filtered_count": 0,
            "profile_selected_candidate_return_limit_truncated_count": 0,
            "terminal_after_negative_incomplete": False,
            "last_pricing_time_limit": None,
            "last_pricing_max_dp_states": 0,
            "last_pricing_profile_dp_time": 0.0,
            "last_pricing_dp_state_count": 0,
            "profile_dp_incomplete_count": 0,
            "profile_dp_incomplete_class": "no_worker_add",
            "profile_dp_state_count_max": 0,
            "profile_dp_processed_labels_max": 0,
            "profile_dp_extension_attempts": 0,
            "profile_dp_time": 0.0,
            "profile_dp_state_cap_hit": False,
            "profile_dp_min_best_rc": None,
            "profile_dp_max_labels_per_mask_observed": 0,
            "profile_dp_nonempty_mask_count": 0,
            "profile_dp_labels_by_sortie_count": "",
            "profile_dp_top_mask_label_counts": "",
        }
    first_add = min(
        additions,
        key=lambda record: (
            _as_int(record.get("cg_iter")),
            float(record.get("time") or 0.0),
        ),
    )
    first_add_index = _first_record_index(records, first_add)
    before_add_records = records[:first_add_index] if first_add_index is not None else []
    after_add_records = records[first_add_index + 1 :] if first_add_index is not None else []
    worker_diagnostic_records = [
        record
        for record in before_add_records
        if (
            record.get("event") == "journey_pricing"
            and str(record.get("pricing_kind", "")) == "sharded_pulse_hidden_negative_worker"
        )
        or record.get("event") == "journey_sharded_pulse_hidden_negative_worker"
    ]
    worker_context_hash = _first_nonempty_compact_field(
        worker_diagnostic_records,
        "pulse_worker_context_hash",
        "worker_context_hash",
        "context_hash",
    )
    first_add_time = _as_float_or_none(first_add.get("time"))
    next_rmp = None
    for record in after_add_records:
        if record.get("event") != "journey_rmp_dual_diagnostics":
            continue
        next_rmp = record
        break
    followup_pricing = [
        record
        for record in after_add_records
        if record.get("event") == "journey_pricing"
        and record.get("pricing_kind") != "sharded_pulse_hidden_negative_worker"
    ]
    legacy_after = [
        record
        for record in _legacy_final_judge_records(after_add_records)
    ]
    completion_after = [
        record
        for record in after_add_records
        if (
            record.get("event") == "journey_exact_pricing_completion_bound_retry"
            or (
                record.get("event") == "journey_pricing"
                and "completion_bound" in str(record.get("pricing_kind", ""))
                and "retry" in str(record.get("pricing_kind", ""))
            )
        )
    ]
    hidden_negative_after = [
        record
        for record in after_add_records
        if record.get("event") in {"hidden_negative_audit", "journey_hidden_negative_audit"}
    ]
    worker_negative_after = [
        record
        for record in after_add_records
        if record.get("event") == "journey_sharded_pulse_hidden_negative_worker"
        and str(record.get("pulse_worker_status", "")) == "FOUND_NEGATIVE"
    ]
    last_pricing = followup_pricing[-1] if followup_pricing else {}
    finish_time = None
    for record in reversed(records):
        if record.get("event") == "finish":
            finish_time = _as_float_or_none(record.get("time"))
            break
    wall_after_worker = None
    if first_add_time is not None and finish_time is not None:
        wall_after_worker = max(0.0, finish_time - first_add_time)
    worker_changed_task_set_count = 0 if not next_rmp else _as_int(
        next_rmp.get("worker_followup_changed_task_set_count")
    )
    worker_active_task_set_count = 0 if not next_rmp else _as_int(
        next_rmp.get("worker_followup_active_changed_task_set_count")
    )
    worker_inactive_task_set_count = 0 if not next_rmp else _as_int(
        next_rmp.get("worker_followup_inactive_changed_task_set_count")
    )
    worker_active_task_set_ratio = None
    if worker_changed_task_set_count > 0:
        worker_active_task_set_ratio = round(
            float(worker_active_task_set_count) / float(worker_changed_task_set_count),
            9,
        )
    exact_pricing = [
        record
        for record in followup_pricing
        if str(record.get("pricing_kind", "")).startswith("exact")
    ]
    exact_retry_pricing = [
        record
        for record in followup_pricing
        if "retry" in str(record.get("pricing_kind", ""))
    ]
    negative_pricing_calls = sum(
        int(str(record.get("pricing_state", "")) == "FOUND_NEGATIVE")
        for record in followup_pricing
    )
    incomplete_pricing_calls = sum(
        int(str(record.get("pricing_state", "")).startswith("INCOMPLETE"))
        for record in followup_pricing
    )
    best_rc_values = [
        value
        for value in (_as_float_or_none(record.get("best_reduced_cost")) for record in followup_pricing)
        if value is not None
    ]
    min_best_rc = min(best_rc_values) if best_rc_values else None
    tail_outcome = _classify_worker_followup_tail(
        followup_pricing,
        min_best_rc=min_best_rc,
        incomplete_pricing_calls=incomplete_pricing_calls,
        negative_pricing_calls=negative_pricing_calls,
    )
    pricing_state_sequence = _pricing_state_sequence(followup_pricing)
    negative_followup_pricing = [
        record
        for record in followup_pricing
        if str(record.get("pricing_state", "")) == "FOUND_NEGATIVE"
    ]
    first_negative = negative_followup_pricing[0] if negative_followup_pricing else {}
    negative_followup_task_sets = [
        task_set
        for task_set in (
            _first_record_task_set_sample(record, "negative_journey_task_set_samples")
            for record in negative_followup_pricing
        )
        if task_set
    ]
    unique_negative_followup_task_sets = tuple(dict.fromkeys(negative_followup_task_sets))
    worker_changed_task_set_samples = _record_task_set_samples(first_add, "changed_task_set_samples")
    first_negative_task_set = _first_record_task_set_sample(
        first_negative,
        "negative_journey_task_set_samples",
    )
    first_negative_sequence = _first_record_sequence_sample(
        first_negative,
        "negative_journey_sequence_samples",
    )
    first_negative_signature_samples = first_negative.get(
        "negative_journey_signature_samples",
        [],
    )
    first_negative_signature_sample = (
        str(first_negative_signature_samples[0])
        if isinstance(first_negative_signature_samples, list) and first_negative_signature_samples
        else ""
    )
    first_negative_overlap = _best_task_set_overlap(
        first_negative_task_set,
        worker_changed_task_set_samples,
    )
    first_worker_task_set = (
        worker_changed_task_set_samples[0]
        if worker_changed_task_set_samples
        else tuple()
    )
    worker_vs_ordinary_task_count_delta = (
        len(first_negative_task_set) - len(first_worker_task_set)
        if first_worker_task_set and first_negative_task_set
        else None
    )
    worker_vs_ordinary_contrast_class = _worker_vs_ordinary_contrast_class(
        worker_added=True,
        worker_task_set=first_worker_task_set,
        followup_task_set=first_negative_task_set,
        relation=str(first_negative_overlap["relation"]),
    )
    worker_negative_pool_task_sets = _records_task_set_samples_any(
        worker_diagnostic_records,
        "pulse_negative_pool_task_set_samples",
        "pulse_worker_negative_pool_task_set_samples",
    )
    worker_harvested_task_sets = _records_task_set_samples_any(
        worker_diagnostic_records,
        "pulse_harvested_task_set_samples",
        "pulse_worker_harvested_task_set_samples",
    )
    worker_returned_candidate_task_sets = _records_task_set_samples_any(
        worker_diagnostic_records,
        "pulse_returned_candidate_task_set_samples",
        "pulse_worker_returned_candidate_task_set_samples",
    )
    worker_negative_pool_overlap = _best_task_set_overlap(
        first_negative_task_set,
        worker_negative_pool_task_sets,
    )
    worker_harvested_overlap = _best_task_set_overlap(
        first_negative_task_set,
        worker_harvested_task_sets,
    )
    worker_returned_candidate_overlap = _best_task_set_overlap(
        first_negative_task_set,
        worker_returned_candidate_task_sets,
    )
    worker_negative_pool_exact = bool(
        first_negative_task_set
        and any(tuple(first_negative_task_set) == tuple(task_set) for task_set in worker_negative_pool_task_sets)
    )
    worker_harvested_exact = bool(
        first_negative_task_set
        and any(tuple(first_negative_task_set) == tuple(task_set) for task_set in worker_harvested_task_sets)
    )
    worker_returned_candidate_exact = bool(
        first_negative_task_set
        and any(
            tuple(first_negative_task_set) == tuple(task_set)
            for task_set in worker_returned_candidate_task_sets
        )
    )
    worker_target_sequence = _first_record_int_sequence_any(
        worker_diagnostic_records,
        "pulse_target_sequence",
        "pulse_worker_target_sequence",
    )
    worker_target_task_set = tuple(sorted(set(int(task) for task in worker_target_sequence)))
    worker_target_negative_pool_overlap = _best_task_set_overlap(
        worker_target_task_set,
        worker_negative_pool_task_sets,
    )
    worker_target_harvested_overlap = _best_task_set_overlap(
        worker_target_task_set,
        worker_harvested_task_sets,
    )
    worker_target_returned_candidate_overlap = _best_task_set_overlap(
        worker_target_task_set,
        worker_returned_candidate_task_sets,
    )
    worker_target_negative_pool_exact = bool(
        worker_target_task_set
        and any(tuple(worker_target_task_set) == tuple(task_set) for task_set in worker_negative_pool_task_sets)
    )
    worker_target_harvested_exact = bool(
        worker_target_task_set
        and any(tuple(worker_target_task_set) == tuple(task_set) for task_set in worker_harvested_task_sets)
    )
    worker_target_returned_candidate_exact = bool(
        worker_target_task_set
        and any(
            tuple(worker_target_task_set) == tuple(task_set)
            for task_set in worker_returned_candidate_task_sets
        )
    )
    terminal_after_negative_incomplete = bool(
        negative_followup_pricing
        and str(last_pricing.get("pricing_state", "")).startswith("INCOMPLETE")
    )
    first_negative_index = _first_record_index(after_add_records, first_negative) if first_negative else None
    first_negative_addition = _first_matching_column_addition_after(
        after_add_records,
        start_index=first_negative_index,
        cg_iter=_as_int(first_negative.get("cg_iter")) if first_negative else 0,
        pricing_kind=str(first_negative.get("pricing_kind", "")) if first_negative else "",
    )
    first_negative_addition_index = (
        _first_record_index(after_add_records, first_negative_addition) if first_negative_addition else None
    )
    post_first_negative_rmp = _first_rmp_after_index(after_add_records, first_negative_addition_index)
    post_first_negative_pool = _first_pool_after_index(after_add_records, first_negative_addition_index)
    post_first_negative_pools = _pool_records_after_index(
        after_add_records,
        first_negative_addition_index,
    )
    post_first_negative_active_match = _active_task_set_value_from_pool_record(
        post_first_negative_pool,
        first_negative_task_set,
    )
    active_residual_persistence = _active_residual_persistence_summary(
        post_first_negative_pools,
        first_negative_task_set,
    )
    negative_family_after_first = _negative_family_after_first_summary(
        negative_followup_task_sets,
        first_negative_task_set,
    )
    profile_dp_incomplete = [
        record
        for record in followup_pricing
        if "profile_dp_incomplete" in str(record.get("reason", ""))
    ]
    profile_dp_records = [
        record
        for record in followup_pricing
        if (
            _as_int(record.get("dp_state_count")) > 0
            or _as_int(record.get("dp_max_labels_per_mask_observed")) > 0
            or _as_int(record.get("dp_nonempty_mask_count")) > 0
            or bool(record.get("dp_top_mask_label_counts"))
        )
    ]
    profile_dp_structural_record = max(
        profile_dp_records,
        key=lambda record: (
            _as_int(record.get("dp_max_labels_per_mask_observed")),
            _as_int(record.get("dp_state_count")),
            _as_int(record.get("dp_processed_labels")),
        ),
        default={},
    )
    profile_dp_top_mask_task_sets = _profile_dp_top_mask_task_sets(profile_dp_structural_record)
    first_negative_profile_dp_top_overlap = _best_task_set_overlap(
        first_negative_task_set,
        profile_dp_top_mask_task_sets,
    )
    first_negative_profile_dp_top_exact = bool(
        first_negative_task_set
        and any(tuple(first_negative_task_set) == tuple(task_set) for task_set in profile_dp_top_mask_task_sets)
    )
    profile_reachable_task_sets = _records_task_set_samples(
        followup_pricing,
        "diagnostic_reachable_task_set_samples",
    )
    profile_negative_task_sets = _records_task_set_samples(
        followup_pricing,
        "diagnostic_negative_task_set_samples",
    )
    profile_selected_task_sets = _records_task_set_samples(
        followup_pricing,
        "diagnostic_selected_task_set_samples",
    )
    first_negative_profile_reachable_overlap = _best_task_set_overlap(
        first_negative_task_set,
        profile_reachable_task_sets,
    )
    first_negative_profile_negative_overlap = _best_task_set_overlap(
        first_negative_task_set,
        profile_negative_task_sets,
    )
    first_negative_profile_selected_overlap = _best_task_set_overlap(
        first_negative_task_set,
        profile_selected_task_sets,
    )
    profile_materialized_task_sets = _records_task_set_samples(
        followup_pricing,
        "diagnostic_selected_materialized_task_set_samples",
    )
    profile_returned_task_sets = _records_task_set_samples(
        followup_pricing,
        "diagnostic_selected_returned_task_set_samples",
    )
    profile_unmaterialized_task_sets = _records_task_set_samples(
        followup_pricing,
        "diagnostic_selected_unmaterialized_task_set_samples",
    )
    profile_weak_filtered_task_sets = _records_task_set_samples(
        followup_pricing,
        "diagnostic_selected_weak_filtered_task_set_samples",
    )
    profile_filtered_task_sets = _records_task_set_samples(
        followup_pricing,
        "diagnostic_selected_filtered_task_set_samples",
    )
    first_negative_profile_materialized_overlap = _best_task_set_overlap(
        first_negative_task_set,
        profile_materialized_task_sets,
    )
    first_negative_profile_returned_overlap = _best_task_set_overlap(
        first_negative_task_set,
        profile_returned_task_sets,
    )
    first_negative_profile_unmaterialized_overlap = _best_task_set_overlap(
        first_negative_task_set,
        profile_unmaterialized_task_sets,
    )
    first_negative_profile_weak_filtered_overlap = _best_task_set_overlap(
        first_negative_task_set,
        profile_weak_filtered_task_sets,
    )
    first_negative_profile_filtered_overlap = _best_task_set_overlap(
        first_negative_task_set,
        profile_filtered_task_sets,
    )
    first_negative_profile_reachable_exact = bool(
        first_negative_task_set
        and any(tuple(first_negative_task_set) == tuple(task_set) for task_set in profile_reachable_task_sets)
    )
    first_negative_profile_negative_exact = bool(
        first_negative_task_set
        and any(tuple(first_negative_task_set) == tuple(task_set) for task_set in profile_negative_task_sets)
    )
    first_negative_profile_selected_exact = bool(
        first_negative_task_set
        and any(tuple(first_negative_task_set) == tuple(task_set) for task_set in profile_selected_task_sets)
    )
    first_negative_profile_materialized_exact = bool(
        first_negative_task_set
        and any(tuple(first_negative_task_set) == tuple(task_set) for task_set in profile_materialized_task_sets)
    )
    first_negative_profile_returned_exact = bool(
        first_negative_task_set
        and any(tuple(first_negative_task_set) == tuple(task_set) for task_set in profile_returned_task_sets)
    )
    first_negative_profile_unmaterialized_exact = bool(
        first_negative_task_set
        and any(tuple(first_negative_task_set) == tuple(task_set) for task_set in profile_unmaterialized_task_sets)
    )
    first_negative_profile_weak_filtered_exact = bool(
        first_negative_task_set
        and any(tuple(first_negative_task_set) == tuple(task_set) for task_set in profile_weak_filtered_task_sets)
    )
    first_negative_profile_filtered_exact = bool(
        first_negative_task_set
        and any(tuple(first_negative_task_set) == tuple(task_set) for task_set in profile_filtered_task_sets)
    )
    selected_candidate_filtered_count = sum(
        _as_int(record.get(field))
        for record in followup_pricing
        for field in (
            "profile_selected_candidate_branch_filtered_count",
            "profile_selected_candidate_duplicate_signature_filtered_count",
            "profile_selected_candidate_duplicate_task_set_filtered_count",
            "profile_selected_candidate_forbidden_signature_filtered_count",
            "profile_selected_candidate_dominated_task_set_filtered_count",
        )
    )
    profile_dp_state_count_max = (
        max(_as_int(record.get("dp_state_count")) for record in profile_dp_incomplete)
        if profile_dp_incomplete
        else 0
    )
    profile_dp_processed_labels_max = (
        max(_as_int(record.get("dp_processed_labels")) for record in profile_dp_incomplete)
        if profile_dp_incomplete
        else 0
    )
    profile_dp_extension_attempts = sum(
        _as_int(record.get("dp_extension_attempts")) for record in profile_dp_incomplete
    )
    profile_dp_time = sum(
        float(record.get("profile_dp_time") or 0.0) for record in profile_dp_incomplete
    )
    profile_dp_state_cap_hit = any(
        _as_int(record.get("pricing_max_dp_states")) > 0
        and _as_int(record.get("dp_state_count")) >= _as_int(record.get("pricing_max_dp_states"))
        for record in profile_dp_incomplete
    )
    profile_dp_best_rc_values = [
        value
        for value in (
            _as_float_or_none(record.get("best_reduced_cost")) for record in profile_dp_incomplete
        )
        if value is not None
    ]
    profile_dp_min_best_rc = min(profile_dp_best_rc_values) if profile_dp_best_rc_values else None
    profile_dp_max_labels_per_mask_observed = (
        max(_as_int(record.get("dp_max_labels_per_mask_observed")) for record in profile_dp_records)
        if profile_dp_records
        else 0
    )
    profile_dp_nonempty_mask_count = (
        max(_as_int(record.get("dp_nonempty_mask_count")) for record in profile_dp_records)
        if profile_dp_records
        else 0
    )
    profile_dp_incomplete_class = _classify_followup_profile_dp_incomplete(
        profile_dp_incomplete,
        min_best_rc=profile_dp_min_best_rc,
        state_cap_hit=profile_dp_state_cap_hit,
    )
    proof_tail_bridge_class, proof_tail_bridge_reason = _classify_followup_proof_tail_bridge(
        first_negative_task_set=first_negative_task_set,
        profile_returned_exact=first_negative_profile_returned_exact,
        profile_materialized_exact=first_negative_profile_materialized_exact,
        profile_unmaterialized_exact=first_negative_profile_unmaterialized_exact,
        profile_weak_filtered_exact=first_negative_profile_weak_filtered_exact,
        profile_filtered_exact=first_negative_profile_filtered_exact,
        profile_selected_exact=first_negative_profile_selected_exact,
        profile_negative_exact=first_negative_profile_negative_exact,
        profile_reachable_exact=first_negative_profile_reachable_exact,
        profile_dp_top_exact=first_negative_profile_dp_top_exact,
        profile_dp_state_cap_hit=profile_dp_state_cap_hit,
        profile_dp_incomplete_class=profile_dp_incomplete_class,
        best_overlap=max(
            int(first_negative_profile_dp_top_overlap["overlap"] or 0),
            int(first_negative_profile_reachable_overlap["overlap"] or 0),
            int(first_negative_profile_negative_overlap["overlap"] or 0),
            int(first_negative_profile_selected_overlap["overlap"] or 0),
            int(first_negative_profile_materialized_overlap["overlap"] or 0),
            int(first_negative_profile_returned_overlap["overlap"] or 0),
            int(first_negative_profile_unmaterialized_overlap["overlap"] or 0),
            int(first_negative_profile_weak_filtered_overlap["overlap"] or 0),
            int(first_negative_profile_filtered_overlap["overlap"] or 0),
        ),
        selected_candidate_filtered_count=selected_candidate_filtered_count,
        selected_candidate_return_limit_truncated_count=sum(
            _as_int(record.get("profile_selected_candidate_return_limit_truncated_count"))
            for record in followup_pricing
        ),
    )
    returned_residual_tail_class, returned_residual_tail_reason = _classify_returned_residual_tail(
        proof_tail_bridge_class=proof_tail_bridge_class,
        first_negative_task_set=first_negative_task_set,
        negative_pricing_calls=negative_pricing_calls,
        negative_task_set_unique_count=len(unique_negative_followup_task_sets),
        negative_task_set_repeat_count=max(
            0,
            len(negative_followup_task_sets) - len(unique_negative_followup_task_sets),
        ),
        terminal_after_negative_incomplete=terminal_after_negative_incomplete,
        first_negative_added_journeys=_as_int(first_negative_addition.get("added_journeys"))
        if first_negative_addition
        else 0,
        first_negative_added_new_task_set_count=_as_int(
            first_negative_addition.get("new_task_set_count")
        )
        if first_negative_addition
        else 0,
        first_negative_added_replacement_count=_as_int(
            first_negative_addition.get("replacement_journeys")
        )
        if first_negative_addition
        else 0,
        first_negative_added_support_changing_count=_as_int(
            first_negative_addition.get("active_changed_task_set_count")
        )
        if first_negative_addition
        else 0,
        post_first_negative_objective_delta=None
        if not post_first_negative_rmp
        else _as_float_or_none(post_first_negative_rmp.get("objective_delta")),
        post_first_negative_dual_l1_delta=None
        if not post_first_negative_rmp
        else _as_float_or_none(post_first_negative_rmp.get("dual_l1_delta")),
    )
    rmp_residual_impact_class, rmp_residual_impact_reason = _classify_rmp_residual_impact(
        first_negative_task_set=first_negative_task_set,
        active_relation=str(post_first_negative_active_match["relation"]),
        active_value=post_first_negative_active_match["value"],
        active_journey_count=int(post_first_negative_active_match["journey_count"] or 0),
        first_negative_added_journeys=_as_int(first_negative_addition.get("added_journeys"))
        if first_negative_addition
        else 0,
        first_negative_added_new_task_set_count=_as_int(
            first_negative_addition.get("new_task_set_count")
        )
        if first_negative_addition
        else 0,
        first_negative_added_support_changing_count=_as_int(
            first_negative_addition.get("active_changed_task_set_count")
        )
        if first_negative_addition
        else 0,
        negative_task_set_unique_count=len(unique_negative_followup_task_sets),
        post_first_negative_objective_delta=None
        if not post_first_negative_rmp
        else _as_float_or_none(post_first_negative_rmp.get("objective_delta")),
        post_first_negative_dual_l1_delta=None
        if not post_first_negative_rmp
        else _as_float_or_none(post_first_negative_rmp.get("dual_l1_delta")),
        active_fractional_ratio=_as_float_or_none(
            post_first_negative_pool.get("pool_active_fractional_ratio")
        )
        if post_first_negative_pool
        else None,
    )
    residual_family_chain_class, residual_family_chain_reason = _classify_residual_family_chain(
        first_negative_task_set=first_negative_task_set,
        active_persistence_count=int(active_residual_persistence["active_count"] or 0),
        active_last_value=active_residual_persistence["last_value"],
        active_basis_unique_count=int(active_residual_persistence["basis_unique_count"] or 0),
        active_basis_churn_count=int(active_residual_persistence["basis_churn_count"] or 0),
        negative_family_after_first_count=int(negative_family_after_first["count"] or 0),
        negative_family_same_count=int(negative_family_after_first["same_count"] or 0),
        negative_family_overlapping_count=int(negative_family_after_first["overlapping_count"] or 0),
        negative_family_disjoint_count=int(negative_family_after_first["disjoint_count"] or 0),
    )
    post_first_negative_pool_duplicate_ratio = (
        _as_float_or_none(post_first_negative_pool.get("pool_duplicate_task_set_ratio"))
        if post_first_negative_pool
        else None
    )
    post_first_negative_pool_active_duplicate_ratio = (
        _as_float_or_none(post_first_negative_pool.get("pool_active_duplicate_task_set_ratio"))
        if post_first_negative_pool
        else None
    )
    post_first_negative_pool_active_fractional_ratio = (
        _as_float_or_none(post_first_negative_pool.get("pool_active_fractional_ratio"))
        if post_first_negative_pool
        else None
    )
    post_first_negative_pool_active_fractional_value_sum = (
        _as_float_or_none(post_first_negative_pool.get("pool_active_fractional_value_sum"))
        if post_first_negative_pool
        else None
    )
    rmp_degeneracy_pressure_class, rmp_degeneracy_pressure_reason = _classify_rmp_degeneracy_pressure(
        first_negative_task_set=first_negative_task_set,
        active_basis_unique_count=int(active_residual_persistence["basis_unique_count"] or 0),
        active_basis_churn_count=int(active_residual_persistence["basis_churn_count"] or 0),
        negative_family_after_first_count=int(negative_family_after_first["count"] or 0),
        negative_family_overlapping_count=int(negative_family_after_first["overlapping_count"] or 0),
        negative_family_disjoint_count=int(negative_family_after_first["disjoint_count"] or 0),
        pool_duplicate_task_set_ratio=post_first_negative_pool_duplicate_ratio,
        pool_active_duplicate_task_set_ratio=post_first_negative_pool_active_duplicate_ratio,
        active_fractional_ratio=post_first_negative_pool_active_fractional_ratio,
        active_fractional_value_sum=post_first_negative_pool_active_fractional_value_sum,
        post_first_negative_objective_delta=None
        if not post_first_negative_rmp
        else _as_float_or_none(post_first_negative_rmp.get("objective_delta")),
        post_first_negative_dual_l1_delta=None
        if not post_first_negative_rmp
        else _as_float_or_none(post_first_negative_rmp.get("dual_l1_delta")),
    )
    post_first_negative_objective_delta = (
        None if not post_first_negative_rmp else _as_float_or_none(post_first_negative_rmp.get("objective_delta"))
    )
    post_first_negative_dual_l1_delta = (
        None if not post_first_negative_rmp else _as_float_or_none(post_first_negative_rmp.get("dual_l1_delta"))
    )
    post_first_negative_dual_move_class, post_first_negative_dual_objective_ratio = _classify_dual_move(
        post_first_negative_objective_delta,
        post_first_negative_dual_l1_delta,
    )
    pool_compression_candidate_class, pool_compression_candidate_reason = _classify_pool_compression_candidate(
        pool_duplicate_task_set_ratio=post_first_negative_pool_duplicate_ratio,
        pool_active_duplicate_task_set_ratio=post_first_negative_pool_active_duplicate_ratio,
        pool_max_journeys_per_task_set=_as_int(
            post_first_negative_pool.get("pool_max_journeys_per_task_set")
        )
        if post_first_negative_pool
        else 0,
        pool_avg_journeys_per_task_set=_as_float_or_none(
            post_first_negative_pool.get("pool_avg_journeys_per_task_set")
        )
        if post_first_negative_pool
        else None,
        pool_active_avg_journeys_per_task_set=_as_float_or_none(
            post_first_negative_pool.get("pool_active_avg_journeys_per_task_set")
        )
        if post_first_negative_pool
        else None,
    )
    rmp_stabilization_candidate_class, rmp_stabilization_candidate_reason = (
        _classify_rmp_stabilization_candidate(
            rmp_degeneracy_pressure_class=rmp_degeneracy_pressure_class,
            dual_move_class=post_first_negative_dual_move_class,
            pool_compression_candidate_class=pool_compression_candidate_class,
            active_fractional_ratio=post_first_negative_pool_active_fractional_ratio,
            active_fractional_value_sum=post_first_negative_pool_active_fractional_value_sum,
        )
    )
    stabilization_diagnostic_design = _stabilization_diagnostic_design(
        rmp_stabilization_candidate_class=rmp_stabilization_candidate_class,
        rmp_stabilization_candidate_reason=rmp_stabilization_candidate_reason,
        rmp_degeneracy_pressure_class=rmp_degeneracy_pressure_class,
        dual_move_class=post_first_negative_dual_move_class,
        pool_compression_candidate_class=pool_compression_candidate_class,
    )
    stabilization_probe = _stabilization_probe_skeleton(
        stabilization_diagnostic_design=stabilization_diagnostic_design,
        rmp_stabilization_candidate_class=rmp_stabilization_candidate_class,
        rmp_stabilization_candidate_reason=rmp_stabilization_candidate_reason,
        context_hash=worker_context_hash,
    )
    return {
        "next_rmp_objective_delta": None
        if not next_rmp
        else next_rmp.get("objective_delta"),
        "next_dual_l1_delta": None if not next_rmp else next_rmp.get("dual_l1_delta"),
        "worker_changed_task_set_count": worker_changed_task_set_count,
        "worker_active_task_set_count": worker_active_task_set_count,
        "worker_inactive_task_set_count": worker_inactive_task_set_count,
        "worker_active_task_set_ratio": worker_active_task_set_ratio,
        "wall_after_worker": wall_after_worker,
        "pricing_calls": len(followup_pricing),
        "heuristic_pricing_calls": len(
            [
                record
                for record in followup_pricing
                if str(record.get("pricing_kind", "")) == "heuristic"
            ]
        ),
        "exact_pricing_calls": len(exact_pricing),
        "exact_retry_pricing_calls": len(exact_retry_pricing),
        "generated_sequences": sum(_as_int(record.get("generated_sequences")) for record in followup_pricing),
        "evaluated_timed_trips": sum(_as_int(record.get("evaluated_timed_trips")) for record in followup_pricing),
        "legacy_after_worker_calls": len(legacy_after),
        "legacy_after_worker_time": sum(float(record.get("time") or 0.0) for record in legacy_after),
        "completion_retry_after_worker_count": len(completion_after),
        "completion_retry_after_worker_time": sum(float(record.get("time") or 0.0) for record in completion_after),
        "hidden_negative_after_worker_count": len(hidden_negative_after),
        "worker_negative_after_worker_count": len(worker_negative_after),
        "last_pricing_kind": str(last_pricing.get("pricing_kind", "")),
        "last_pricing_state": str(last_pricing.get("pricing_state", "")),
        "last_pricing_reason": str(last_pricing.get("reason", "")),
        "last_best_rc": last_pricing.get("best_reduced_cost"),
        "tail_outcome": tail_outcome,
        "negative_pricing_calls": negative_pricing_calls,
        "incomplete_pricing_calls": incomplete_pricing_calls,
        "min_best_rc": min_best_rc,
        "pricing_state_sequence": pricing_state_sequence,
        "first_negative_cg_iter": None if not first_negative else _as_int(first_negative.get("cg_iter")),
        "first_negative_pricing_kind": str(first_negative.get("pricing_kind", "")),
        "first_negative_best_rc": None if not first_negative else first_negative.get("best_reduced_cost"),
        "first_negative_task_set_hash": str(first_negative.get("negative_journey_task_set_hash", "")),
        "first_negative_task_set": _task_set_string(first_negative_task_set),
        "first_negative_task_count": len(first_negative_task_set),
        "first_negative_sequence": _sequence_sample_string(first_negative_sequence),
        "first_negative_signature_sample": first_negative_signature_sample,
        "first_negative_overlap_to_worker": first_negative_overlap["overlap"],
        "first_negative_jaccard_to_worker": first_negative_overlap["jaccard"],
        "first_negative_relation_to_worker": first_negative_overlap["relation"],
        "worker_vs_ordinary_first_worker_task_set": _task_set_string(first_worker_task_set),
        "worker_vs_ordinary_first_followup_task_set": _task_set_string(first_negative_task_set),
        "worker_vs_ordinary_task_set_overlap": first_negative_overlap["overlap"],
        "worker_vs_ordinary_task_set_jaccard": first_negative_overlap["jaccard"],
        "worker_vs_ordinary_task_set_relation": first_negative_overlap["relation"],
        "worker_vs_ordinary_disjoint": (
            bool(first_worker_task_set)
            and bool(first_negative_task_set)
            and first_negative_overlap["relation"] == "disjoint_task_set"
        ),
        "worker_vs_ordinary_worker_task_count": len(first_worker_task_set),
        "worker_vs_ordinary_followup_task_count": len(first_negative_task_set),
        "worker_vs_ordinary_task_count_delta": worker_vs_ordinary_task_count_delta,
        "worker_vs_ordinary_worker_added_before_followup": True,
        "worker_vs_ordinary_followup_returned_after_worker": bool(first_negative_task_set),
        "worker_vs_ordinary_contrast_class": worker_vs_ordinary_contrast_class,
        "worker_negative_pool_task_set_samples": _first_nonempty_compact_field(
            worker_diagnostic_records,
            "pulse_negative_pool_task_set_samples",
            "pulse_worker_negative_pool_task_set_samples",
        ),
        "worker_negative_pool_sequence_samples": _first_nonempty_compact_field(
            worker_diagnostic_records,
            "pulse_negative_pool_sequence_samples",
            "pulse_worker_negative_pool_sequence_samples",
        ),
        "worker_negative_pool_signature_samples": _first_nonempty_compact_field(
            worker_diagnostic_records,
            "pulse_negative_pool_signature_samples",
            "pulse_worker_negative_pool_signature_samples",
        ),
        "worker_harvested_task_set_samples": _first_nonempty_compact_field(
            worker_diagnostic_records,
            "pulse_harvested_task_set_samples",
            "pulse_worker_harvested_task_set_samples",
        ),
        "worker_harvested_sequence_samples": _first_nonempty_compact_field(
            worker_diagnostic_records,
            "pulse_harvested_sequence_samples",
            "pulse_worker_harvested_sequence_samples",
        ),
        "worker_harvested_signature_samples": _first_nonempty_compact_field(
            worker_diagnostic_records,
            "pulse_harvested_signature_samples",
            "pulse_worker_harvested_signature_samples",
        ),
        "worker_returned_candidate_task_set_samples": _first_nonempty_compact_field(
            worker_diagnostic_records,
            "pulse_returned_candidate_task_set_samples",
            "pulse_worker_returned_candidate_task_set_samples",
        ),
        "worker_returned_candidate_sequence_samples": _first_nonempty_compact_field(
            worker_diagnostic_records,
            "pulse_returned_candidate_sequence_samples",
            "pulse_worker_returned_candidate_sequence_samples",
        ),
        "worker_returned_candidate_signature_samples": _first_nonempty_compact_field(
            worker_diagnostic_records,
            "pulse_returned_candidate_signature_samples",
            "pulse_worker_returned_candidate_signature_samples",
        ),
        "worker_vs_ordinary_negative_pool_overlap": worker_negative_pool_overlap["overlap"],
        "worker_vs_ordinary_negative_pool_jaccard": worker_negative_pool_overlap["jaccard"],
        "worker_vs_ordinary_negative_pool_relation": worker_negative_pool_overlap["relation"],
        "worker_vs_ordinary_negative_pool_exact": worker_negative_pool_exact,
        "worker_vs_ordinary_harvested_overlap": worker_harvested_overlap["overlap"],
        "worker_vs_ordinary_harvested_jaccard": worker_harvested_overlap["jaccard"],
        "worker_vs_ordinary_harvested_relation": worker_harvested_overlap["relation"],
        "worker_vs_ordinary_harvested_exact": worker_harvested_exact,
        "worker_vs_ordinary_returned_candidate_overlap": worker_returned_candidate_overlap["overlap"],
        "worker_vs_ordinary_returned_candidate_jaccard": worker_returned_candidate_overlap["jaccard"],
        "worker_vs_ordinary_returned_candidate_relation": worker_returned_candidate_overlap["relation"],
        "worker_vs_ordinary_returned_candidate_exact": worker_returned_candidate_exact,
        "worker_target_sequence_task_set": _task_set_string(worker_target_task_set),
        "worker_target_negative_pool_overlap": worker_target_negative_pool_overlap["overlap"],
        "worker_target_negative_pool_jaccard": worker_target_negative_pool_overlap["jaccard"],
        "worker_target_negative_pool_relation": worker_target_negative_pool_overlap["relation"],
        "worker_target_negative_pool_exact": worker_target_negative_pool_exact,
        "worker_target_harvested_overlap": worker_target_harvested_overlap["overlap"],
        "worker_target_harvested_jaccard": worker_target_harvested_overlap["jaccard"],
        "worker_target_harvested_relation": worker_target_harvested_overlap["relation"],
        "worker_target_harvested_exact": worker_target_harvested_exact,
        "worker_target_returned_candidate_overlap": worker_target_returned_candidate_overlap["overlap"],
        "worker_target_returned_candidate_jaccard": worker_target_returned_candidate_overlap["jaccard"],
        "worker_target_returned_candidate_relation": worker_target_returned_candidate_overlap["relation"],
        "worker_target_returned_candidate_exact": worker_target_returned_candidate_exact,
        "first_negative_profile_dp_top_overlap": first_negative_profile_dp_top_overlap["overlap"],
        "first_negative_profile_dp_top_jaccard": first_negative_profile_dp_top_overlap["jaccard"],
        "first_negative_profile_dp_top_relation": first_negative_profile_dp_top_overlap["relation"],
        "first_negative_profile_dp_top_exact": first_negative_profile_dp_top_exact,
        "first_negative_profile_reachable_overlap": first_negative_profile_reachable_overlap["overlap"],
        "first_negative_profile_reachable_jaccard": first_negative_profile_reachable_overlap["jaccard"],
        "first_negative_profile_reachable_relation": first_negative_profile_reachable_overlap["relation"],
        "first_negative_profile_reachable_exact": first_negative_profile_reachable_exact,
        "first_negative_profile_negative_overlap": first_negative_profile_negative_overlap["overlap"],
        "first_negative_profile_negative_jaccard": first_negative_profile_negative_overlap["jaccard"],
        "first_negative_profile_negative_relation": first_negative_profile_negative_overlap["relation"],
        "first_negative_profile_negative_exact": first_negative_profile_negative_exact,
        "first_negative_profile_selected_overlap": first_negative_profile_selected_overlap["overlap"],
        "first_negative_profile_selected_jaccard": first_negative_profile_selected_overlap["jaccard"],
        "first_negative_profile_selected_relation": first_negative_profile_selected_overlap["relation"],
        "first_negative_profile_selected_exact": first_negative_profile_selected_exact,
        "first_negative_profile_materialized_overlap": first_negative_profile_materialized_overlap["overlap"],
        "first_negative_profile_materialized_jaccard": first_negative_profile_materialized_overlap["jaccard"],
        "first_negative_profile_materialized_relation": first_negative_profile_materialized_overlap["relation"],
        "first_negative_profile_materialized_exact": first_negative_profile_materialized_exact,
        "first_negative_profile_returned_overlap": first_negative_profile_returned_overlap["overlap"],
        "first_negative_profile_returned_jaccard": first_negative_profile_returned_overlap["jaccard"],
        "first_negative_profile_returned_relation": first_negative_profile_returned_overlap["relation"],
        "first_negative_profile_returned_exact": first_negative_profile_returned_exact,
        "first_negative_profile_unmaterialized_overlap": first_negative_profile_unmaterialized_overlap["overlap"],
        "first_negative_profile_unmaterialized_jaccard": first_negative_profile_unmaterialized_overlap["jaccard"],
        "first_negative_profile_unmaterialized_relation": first_negative_profile_unmaterialized_overlap["relation"],
        "first_negative_profile_unmaterialized_exact": first_negative_profile_unmaterialized_exact,
        "first_negative_profile_weak_filtered_overlap": first_negative_profile_weak_filtered_overlap["overlap"],
        "first_negative_profile_weak_filtered_jaccard": first_negative_profile_weak_filtered_overlap["jaccard"],
        "first_negative_profile_weak_filtered_relation": first_negative_profile_weak_filtered_overlap["relation"],
        "first_negative_profile_weak_filtered_exact": first_negative_profile_weak_filtered_exact,
        "first_negative_profile_filtered_overlap": first_negative_profile_filtered_overlap["overlap"],
        "first_negative_profile_filtered_jaccard": first_negative_profile_filtered_overlap["jaccard"],
        "first_negative_profile_filtered_relation": first_negative_profile_filtered_overlap["relation"],
        "first_negative_profile_filtered_exact": first_negative_profile_filtered_exact,
        "proof_tail_bridge_class": proof_tail_bridge_class,
        "proof_tail_bridge_reason": proof_tail_bridge_reason,
        "returned_residual_tail_class": returned_residual_tail_class,
        "returned_residual_tail_reason": returned_residual_tail_reason,
        "negative_task_set_sequence": "|".join(
            _task_set_string(task_set) for task_set in negative_followup_task_sets[:8]
        ),
        "negative_task_set_unique_count": len(unique_negative_followup_task_sets),
        "negative_task_set_repeat_count": max(
            0,
            len(negative_followup_task_sets) - len(unique_negative_followup_task_sets),
        ),
        "first_negative_addition_productivity_class": str(
            first_negative_addition.get("addition_productivity_class", "")
        )
        if first_negative_addition
        else "",
        "first_negative_added_journeys": _as_int(first_negative_addition.get("added_journeys"))
        if first_negative_addition
        else 0,
        "first_negative_added_new_task_set_count": _as_int(
            first_negative_addition.get("new_task_set_count")
        )
        if first_negative_addition
        else 0,
        "first_negative_added_replacement_count": _as_int(
            first_negative_addition.get("replacement_journeys")
        )
        if first_negative_addition
        else 0,
        "first_negative_added_support_changing_count": _as_int(
            first_negative_addition.get("active_changed_task_set_count")
        )
        if first_negative_addition
        else 0,
        "post_first_negative_rmp_objective_delta": None
        if not post_first_negative_rmp
        else post_first_negative_rmp.get("objective_delta"),
        "post_first_negative_dual_l1_delta": None
        if not post_first_negative_rmp
        else post_first_negative_rmp.get("dual_l1_delta"),
        "first_negative_active_after_addition": bool(
            post_first_negative_active_match["relation"] == "same_task_set"
        ),
        "first_negative_active_value_after_addition": post_first_negative_active_match["value"],
        "first_negative_active_journey_count_after_addition": post_first_negative_active_match[
            "journey_count"
        ],
        "first_negative_active_relation_after_addition": post_first_negative_active_match["relation"],
        "active_fractional_ratio_after_first_negative": None
        if not post_first_negative_pool
        else post_first_negative_pool.get("pool_active_fractional_ratio"),
        "active_total_value_after_first_negative": None
        if not post_first_negative_pool
        else post_first_negative_pool.get("pool_active_total_value"),
        "active_task_set_hash_after_first_negative": ""
        if not post_first_negative_pool
        else str(post_first_negative_pool.get("pool_active_task_set_hash", "")),
        "rmp_residual_impact_class": rmp_residual_impact_class,
        "rmp_residual_impact_reason": rmp_residual_impact_reason,
        "first_negative_active_persistence_count": active_residual_persistence["active_count"],
        "first_negative_active_value_sequence": active_residual_persistence["value_sequence"],
        "first_negative_active_last_value": active_residual_persistence["last_value"],
        "active_basis_hash_sequence_after_first_negative": active_residual_persistence[
            "basis_hash_sequence"
        ],
        "active_basis_unique_count_after_first_negative": active_residual_persistence[
            "basis_unique_count"
        ],
        "active_basis_churn_count_after_first_negative": active_residual_persistence[
            "basis_churn_count"
        ],
        "negative_family_after_first_count": negative_family_after_first["count"],
        "negative_family_after_first_relation_sequence": negative_family_after_first[
            "relation_sequence"
        ],
        "negative_family_after_first_disjoint_count": negative_family_after_first[
            "disjoint_count"
        ],
        "negative_family_after_first_overlapping_count": negative_family_after_first[
            "overlapping_count"
        ],
        "negative_family_after_first_same_count": negative_family_after_first["same_count"],
        "negative_family_after_first_max_overlap": negative_family_after_first["max_overlap"],
        "negative_family_after_first_max_jaccard": negative_family_after_first["max_jaccard"],
        "residual_family_chain_class": residual_family_chain_class,
        "residual_family_chain_reason": residual_family_chain_reason,
        "post_first_negative_pool_duplicate_task_sets": _as_int(
            post_first_negative_pool.get("pool_duplicate_task_set_count")
        )
        if post_first_negative_pool
        else 0,
        "post_first_negative_pool_duplicate_task_set_ratio": post_first_negative_pool_duplicate_ratio,
        "post_first_negative_pool_active_duplicate_task_sets": _as_int(
            post_first_negative_pool.get("pool_active_duplicate_task_set_count")
        )
        if post_first_negative_pool
        else 0,
        "post_first_negative_pool_active_duplicate_task_set_ratio": (
            post_first_negative_pool_active_duplicate_ratio
        ),
        "post_first_negative_pool_avg_journeys_per_task_set": None
        if not post_first_negative_pool
        else post_first_negative_pool.get("pool_avg_journeys_per_task_set"),
        "post_first_negative_pool_max_journeys_per_task_set": _as_int(
            post_first_negative_pool.get("pool_max_journeys_per_task_set")
        )
        if post_first_negative_pool
        else 0,
        "post_first_negative_pool_active_avg_journeys_per_task_set": None
        if not post_first_negative_pool
        else post_first_negative_pool.get("pool_active_avg_journeys_per_task_set"),
        "post_first_negative_pool_active_fractional_value_sum": (
            post_first_negative_pool_active_fractional_value_sum
        ),
        "post_first_negative_pool_active_fractional_value_max": None
        if not post_first_negative_pool
        else post_first_negative_pool.get("pool_active_fractional_value_max"),
        "post_first_negative_pool_active_fractional_value_min": None
        if not post_first_negative_pool
        else post_first_negative_pool.get("pool_active_fractional_value_min"),
        "post_first_negative_pool_active_fractional_small_value_count": _as_int(
            post_first_negative_pool.get("pool_active_fractional_small_value_count")
        )
        if post_first_negative_pool
        else 0,
        "rmp_degeneracy_pressure_class": rmp_degeneracy_pressure_class,
        "rmp_degeneracy_pressure_reason": rmp_degeneracy_pressure_reason,
        "post_first_negative_dual_objective_abs_ratio": post_first_negative_dual_objective_ratio,
        "post_first_negative_dual_move_class": post_first_negative_dual_move_class,
        "pool_compression_candidate_class": pool_compression_candidate_class,
        "pool_compression_candidate_reason": pool_compression_candidate_reason,
        "rmp_stabilization_candidate_class": rmp_stabilization_candidate_class,
        "rmp_stabilization_candidate_reason": rmp_stabilization_candidate_reason,
        "stabilization_diagnostic_design_class": stabilization_diagnostic_design[
            "design_class"
        ],
        "stabilization_diagnostic_design_reason": stabilization_diagnostic_design[
            "design_reason"
        ],
        "stabilization_diagnostic_recommended_profile": stabilization_diagnostic_design[
            "recommended_profile"
        ],
        "stabilization_diagnostic_guarded_config_keys": stabilization_diagnostic_design[
            "guarded_config_keys"
        ],
        "stabilization_diagnostic_certificate_effect_allowed": bool(
            stabilization_diagnostic_design["certificate_effect_allowed"]
        ),
        "stabilization_probe_enabled": bool(stabilization_probe["enabled"]),
        "stabilization_probe_status": stabilization_probe["status"],
        "stabilization_probe_reason": stabilization_probe["reason"],
        "stabilization_probe_mode": stabilization_probe["mode"],
        "stabilization_probe_candidate_source": stabilization_probe["candidate_source"],
        "stabilization_probe_anchor_weight": stabilization_probe["anchor_weight"],
        "stabilization_probe_context_hash_required": bool(
            stabilization_probe["context_hash_required"]
        ),
        "stabilization_probe_context_hash": stabilization_probe["context_hash"],
        "stabilization_probe_certificate_effect_allowed": bool(
            stabilization_probe["certificate_effect_allowed"]
        ),
        "stabilization_probe_official_effect_allowed": bool(
            stabilization_probe["official_effect_allowed"]
        ),
        "stabilization_probe_mutates_rmp": bool(stabilization_probe["mutates_rmp"]),
        "stabilization_probe_design_profile": stabilization_probe["design_profile"],
        "profile_selected_candidate_input_count": sum(
            _as_int(record.get("profile_selected_candidate_input_count")) for record in followup_pricing
        ),
        "profile_selected_candidate_scanned_count": sum(
            _as_int(record.get("profile_selected_candidate_scanned_count")) for record in followup_pricing
        ),
        "profile_selected_candidate_materialized_count": sum(
            _as_int(record.get("profile_selected_candidate_materialized_count")) for record in followup_pricing
        ),
        "profile_selected_candidate_returned_count": sum(
            _as_int(record.get("profile_selected_candidate_returned_count")) for record in followup_pricing
        ),
        "profile_selected_candidate_filtered_count": selected_candidate_filtered_count,
        "profile_selected_candidate_return_limit_truncated_count": sum(
            _as_int(record.get("profile_selected_candidate_return_limit_truncated_count"))
            for record in followup_pricing
        ),
        "terminal_after_negative_incomplete": terminal_after_negative_incomplete,
        "last_pricing_time_limit": last_pricing.get("pricing_time_limit"),
        "last_pricing_max_dp_states": _as_int(last_pricing.get("pricing_max_dp_states")),
        "last_pricing_profile_dp_time": float(last_pricing.get("profile_dp_time") or 0.0),
        "last_pricing_dp_state_count": _as_int(last_pricing.get("dp_state_count")),
        "profile_dp_incomplete_count": len(profile_dp_incomplete),
        "profile_dp_incomplete_class": profile_dp_incomplete_class,
        "profile_dp_state_count_max": profile_dp_state_count_max,
        "profile_dp_processed_labels_max": profile_dp_processed_labels_max,
        "profile_dp_extension_attempts": profile_dp_extension_attempts,
        "profile_dp_time": profile_dp_time,
        "profile_dp_state_cap_hit": profile_dp_state_cap_hit,
        "profile_dp_min_best_rc": profile_dp_min_best_rc,
        "profile_dp_max_labels_per_mask_observed": profile_dp_max_labels_per_mask_observed,
        "profile_dp_nonempty_mask_count": profile_dp_nonempty_mask_count,
        "profile_dp_labels_by_sortie_count": _compact_json_string(
            profile_dp_structural_record.get("dp_labels_by_sortie_count")
        ),
        "profile_dp_top_mask_label_counts": _compact_json_string(
            profile_dp_structural_record.get("dp_top_mask_label_counts")
        ),
    }


def _classify_worker_followup_tail(
    followup_pricing: list[dict[str, Any]],
    *,
    min_best_rc: float | None,
    incomplete_pricing_calls: int,
    negative_pricing_calls: int,
    eps: float = 1.0e-6,
    near_zero: float = 1.0e-3,
) -> str:
    if not followup_pricing:
        return "no_followup_pricing"
    if int(negative_pricing_calls) > 0:
        return "followup_found_negative"
    states = {str(record.get("pricing_state", "")) for record in followup_pricing}
    if "CERTIFIED_NO_NEGATIVE" in states:
        return "followup_certified_no_negative"
    if int(incomplete_pricing_calls) > 0:
        if min_best_rc is None:
            return "followup_incomplete_unknown_best_rc"
        if float(min_best_rc) < -float(eps):
            return "followup_incomplete_negative_best_rc"
        if abs(float(min_best_rc)) <= float(near_zero):
            return "followup_incomplete_near_zero_best_rc"
        return "followup_incomplete_positive_best_rc"
    if min_best_rc is not None and float(min_best_rc) < -float(eps):
        return "followup_nonnegative_state_negative_best_rc"
    return "followup_no_negative_observed"


def _pricing_state_sequence(records: list[dict[str, Any]], *, limit: int = 8) -> str:
    parts: list[str] = []
    for record in records[: max(0, int(limit))]:
        kind = str(record.get("pricing_kind", ""))
        state = str(record.get("pricing_state", ""))
        reason = str(record.get("reason", ""))
        parts.append(f"{kind}:{state}:{reason}")
    if len(records) > int(limit):
        parts.append(f"...(+{len(records) - int(limit)})")
    return "|".join(parts)


def _classify_followup_profile_dp_incomplete(
    profile_dp_incomplete: list[dict[str, Any]],
    *,
    min_best_rc: float | None,
    state_cap_hit: bool,
    eps: float = 1.0e-6,
    near_zero: float = 1.0e-3,
) -> str:
    if not profile_dp_incomplete:
        return "no_profile_dp_incomplete"
    if bool(state_cap_hit):
        return "profile_dp_state_cap_hit"
    if min_best_rc is None:
        return "profile_dp_unknown_best_rc_incomplete"
    if float(min_best_rc) < -float(eps):
        return "profile_dp_negative_best_rc_incomplete"
    if abs(float(min_best_rc)) <= float(near_zero):
        return "profile_dp_near_zero_best_rc_incomplete"
    return "profile_dp_positive_best_rc_incomplete"


def _classify_followup_proof_tail_bridge(
    *,
    first_negative_task_set: tuple[int, ...],
    profile_returned_exact: bool,
    profile_materialized_exact: bool,
    profile_unmaterialized_exact: bool,
    profile_weak_filtered_exact: bool,
    profile_filtered_exact: bool,
    profile_selected_exact: bool,
    profile_negative_exact: bool,
    profile_reachable_exact: bool,
    profile_dp_top_exact: bool,
    profile_dp_state_cap_hit: bool,
    profile_dp_incomplete_class: str,
    best_overlap: int,
    selected_candidate_filtered_count: int,
    selected_candidate_return_limit_truncated_count: int,
) -> tuple[str, str]:
    if not first_negative_task_set:
        return ("no_followup_negative", "no ordinary follow-up negative to bridge")
    if profile_returned_exact:
        return ("profile_returned_residual_exact", "profile-DP returned the same residual task set")
    if profile_materialized_exact:
        return (
            "profile_materialized_residual_not_returned",
            "profile-DP materialized the residual task set but did not return it",
        )
    if profile_unmaterialized_exact:
        return (
            "profile_selected_unmaterialized_residual",
            "profile-DP selected the residual task set but materialization did not produce a journey",
        )
    if profile_weak_filtered_exact:
        return (
            "profile_weak_filtered_residual",
            "profile-DP selected the residual task set but true-RC filtering rejected it",
        )
    if profile_filtered_exact:
        return (
            "profile_filtered_residual",
            "profile-DP selected the residual task set but branch/duplicate/forbidden/dominance filters rejected it",
        )
    if profile_selected_exact:
        suffix = ""
        if int(selected_candidate_filtered_count) > 0:
            suffix = f"; selected_filtered={int(selected_candidate_filtered_count)}"
        if int(selected_candidate_return_limit_truncated_count) > 0:
            suffix += f"; return_limit_truncated={int(selected_candidate_return_limit_truncated_count)}"
        return (
            "profile_selected_residual_not_materialized",
            "profile-DP selected the residual task set but it did not reach materialized/returned samples" + suffix,
        )
    if profile_negative_exact:
        return (
            "profile_negative_residual_not_selected",
            "profile-DP generated a negative candidate for the residual task set but selection skipped it",
        )
    if profile_reachable_exact:
        return (
            "profile_reachable_residual_not_negative",
            "profile-DP reached the residual task set but did not classify it as a negative candidate",
        )
    if profile_dp_top_exact:
        return (
            "profile_topmask_residual_not_reached",
            "profile-DP top mask matched residual task set but reachable/negative samples did not return it",
        )
    if bool(profile_dp_state_cap_hit):
        return ("profile_dp_state_cap_missing_residual", "profile-DP hit state cap before residual task set was observed")
    if str(profile_dp_incomplete_class or "").startswith("profile_dp_") and str(
        profile_dp_incomplete_class
    ) != "no_profile_dp_incomplete":
        return ("profile_dp_incomplete_missing_residual", str(profile_dp_incomplete_class))
    if int(best_overlap) > 0:
        return (
            "profile_overlap_without_exact_residual",
            f"profile-DP samples overlap residual task set but no exact residual match; best_overlap={int(best_overlap)}",
        )
    return ("profile_no_residual_signal", "profile-DP samples contain no residual task-set signal")


def _first_matching_column_addition_after(
    records: list[dict[str, Any]],
    *,
    start_index: int | None,
    cg_iter: int,
    pricing_kind: str,
) -> dict[str, Any]:
    if start_index is None:
        return {}
    for record in records[int(start_index) + 1 :]:
        if record.get("event") != "journey_column_addition":
            continue
        if int(cg_iter) > 0 and _as_int(record.get("cg_iter")) != int(cg_iter):
            continue
        record_kind = str(record.get("pricing_kind", ""))
        if pricing_kind and record_kind and record_kind != pricing_kind:
            continue
        return record
    return {}


def _first_rmp_after_index(records: list[dict[str, Any]], index: int | None) -> dict[str, Any]:
    if index is None:
        return {}
    for record in records[int(index) + 1 :]:
        if record.get("event") == "journey_rmp_dual_diagnostics":
            return record
    return {}


def _first_pool_after_index(records: list[dict[str, Any]], index: int | None) -> dict[str, Any]:
    if index is None:
        return {}
    for record in records[int(index) + 1 :]:
        if record.get("event") == "journey_pool_structure_diagnostics":
            return record
    return {}


def _active_task_set_value_from_pool_record(
    record: dict[str, Any],
    task_set: tuple[int, ...],
) -> dict[str, Any]:
    raw_samples = record.get("pool_active_top_task_set_value_samples", [])
    if isinstance(raw_samples, str):
        try:
            raw_samples = json.loads(raw_samples)
        except json.JSONDecodeError:
            raw_samples = []
    if not task_set or not isinstance(raw_samples, (list, tuple)):
        return {"relation": "unknown", "value": None, "journey_count": 0, "overlap": 0, "jaccard": None}
    active_task_sets: list[tuple[int, ...]] = []
    active_values: dict[tuple[int, ...], tuple[float | None, int]] = {}
    for item in raw_samples:
        if not isinstance(item, (list, tuple)) or len(item) < 3:
            continue
        raw_tasks = item[2]
        if not isinstance(raw_tasks, (list, tuple, set)):
            continue
        tasks = tuple(sorted(int(task) for task in raw_tasks))
        if not tasks:
            continue
        active_task_sets.append(tasks)
        active_values[tasks] = (_as_float_or_none(item[0]), _as_int(item[1]))
    overlap = _best_task_set_overlap(task_set, active_task_sets)
    exact_key = tuple(task_set)
    if exact_key in active_values:
        value, journey_count = active_values[exact_key]
        return {
            "relation": "same_task_set",
            "value": value,
            "journey_count": journey_count,
            "overlap": len(exact_key),
            "jaccard": 1.0,
        }
    return {
        "relation": overlap["relation"],
        "value": None,
        "journey_count": 0,
        "overlap": overlap["overlap"],
        "jaccard": overlap["jaccard"],
    }


def _pool_records_after_index(records: list[dict[str, Any]], index: int | None) -> list[dict[str, Any]]:
    if index is None:
        return []
    return [
        record
        for record in records[int(index) + 1 :]
        if record.get("event") == "journey_pool_structure_diagnostics"
    ]


def _active_residual_persistence_summary(
    pool_records: list[dict[str, Any]],
    task_set: tuple[int, ...],
    *,
    limit: int = 8,
) -> dict[str, Any]:
    if not task_set:
        return {
            "active_count": 0,
            "value_sequence": "",
            "last_value": None,
            "basis_hash_sequence": "",
            "basis_unique_count": 0,
            "basis_churn_count": 0,
        }
    values: list[float | None] = []
    basis_hashes: list[str] = []
    for record in pool_records:
        basis_hash = str(record.get("pool_active_task_set_hash", ""))
        if basis_hash:
            basis_hashes.append(basis_hash)
        active_match = _active_task_set_value_from_pool_record(record, task_set)
        if str(active_match["relation"]) == "same_task_set":
            values.append(active_match["value"])
    limited_values = values[: max(0, int(limit))]
    limited_hashes = basis_hashes[: max(0, int(limit))]
    basis_churn_count = 0
    previous_hash = None
    for basis_hash in basis_hashes:
        if previous_hash is not None and basis_hash != previous_hash:
            basis_churn_count += 1
        previous_hash = basis_hash
    return {
        "active_count": len(values),
        "value_sequence": _compact_json_string(limited_values),
        "last_value": values[-1] if values else None,
        "basis_hash_sequence": _compact_json_string(limited_hashes),
        "basis_unique_count": len(set(basis_hashes)),
        "basis_churn_count": basis_churn_count,
    }


def _negative_family_after_first_summary(
    negative_task_sets: list[tuple[int, ...]],
    first_task_set: tuple[int, ...],
    *,
    limit: int = 8,
) -> dict[str, Any]:
    later_task_sets = list(negative_task_sets[1:])
    relations: list[str] = []
    disjoint_count = 0
    overlapping_count = 0
    same_count = 0
    max_overlap = 0
    max_jaccard: float | None = None
    for task_set in later_task_sets:
        overlap = _best_task_set_overlap(first_task_set, [task_set])
        relation = str(overlap["relation"])
        relations.append(relation)
        if relation == "same_task_set":
            same_count += 1
        elif relation == "overlapping_task_set":
            overlapping_count += 1
        elif relation == "disjoint_task_set":
            disjoint_count += 1
        max_overlap = max(max_overlap, int(overlap["overlap"] or 0))
        jaccard = overlap["jaccard"]
        if jaccard is not None:
            max_jaccard = float(jaccard) if max_jaccard is None else max(max_jaccard, float(jaccard))
    return {
        "count": len(later_task_sets),
        "relation_sequence": "|".join(relations[: max(0, int(limit))]),
        "disjoint_count": disjoint_count,
        "overlapping_count": overlapping_count,
        "same_count": same_count,
        "max_overlap": max_overlap,
        "max_jaccard": max_jaccard,
    }


def _classify_returned_residual_tail(
    *,
    proof_tail_bridge_class: str,
    first_negative_task_set: tuple[int, ...],
    negative_pricing_calls: int,
    negative_task_set_unique_count: int,
    negative_task_set_repeat_count: int,
    terminal_after_negative_incomplete: bool,
    first_negative_added_journeys: int,
    first_negative_added_new_task_set_count: int,
    first_negative_added_replacement_count: int,
    first_negative_added_support_changing_count: int,
    post_first_negative_objective_delta: float | None,
    post_first_negative_dual_l1_delta: float | None,
    eps: float = 1.0e-6,
    dual_move_eps: float = 1.0e-6,
) -> tuple[str, str]:
    if not first_negative_task_set:
        return ("no_followup_negative", "no ordinary follow-up negative after worker addition")
    if str(proof_tail_bridge_class) != "profile_returned_residual_exact":
        return (
            "not_profile_returned_residual",
            f"proof_tail_bridge_class={str(proof_tail_bridge_class)}",
        )
    if int(first_negative_added_journeys) <= 0:
        return (
            "returned_residual_no_addition_record",
            "profile-DP returned residual but no matching column-addition event was observed",
        )
    if int(negative_task_set_unique_count) > 1:
        return (
            "returned_residual_then_new_negative_family",
            f"profile-DP returned residual, then {int(negative_task_set_unique_count)} unique follow-up negative task sets appeared",
        )
    if int(negative_task_set_repeat_count) > 0:
        return (
            "returned_residual_repeated_same_task_set",
            f"profile-DP returned residual and the same task set repeated {int(negative_task_set_repeat_count)} times",
        )
    if bool(terminal_after_negative_incomplete):
        return (
            "returned_residual_then_incomplete_tail",
            "profile-DP returned residual, then pricing ended incomplete",
        )
    objective_delta = post_first_negative_objective_delta
    dual_l1_delta = post_first_negative_dual_l1_delta
    if objective_delta is not None:
        if abs(float(objective_delta)) <= float(eps) and (
            dual_l1_delta is not None and float(dual_l1_delta) > float(dual_move_eps)
        ):
            return (
                "returned_residual_degenerate_dual_move",
                f"objective_delta={float(objective_delta):.9f}, dual_l1_delta={float(dual_l1_delta):.9f}",
            )
        if float(objective_delta) < -float(eps) and int(negative_pricing_calls) <= 1:
            return (
                "returned_residual_single_improving_column",
                f"objective_delta={float(objective_delta):.9f}",
            )
    if int(first_negative_added_support_changing_count) > 0:
        return (
            "returned_residual_active_support_changing",
            "profile-DP returned residual and the added column changed active support",
        )
    if int(first_negative_added_new_task_set_count) > 0:
        return (
            "returned_residual_new_task_set_no_tail_signal",
            "profile-DP returned residual as a new task set without further tail signal",
        )
    if int(first_negative_added_replacement_count) > 0:
        return (
            "returned_residual_replacement_no_tail_signal",
            "profile-DP returned residual as a replacement column without further tail signal",
        )
    return ("returned_residual_unclassified_tail", "profile-DP returned residual but no tail class matched")


def _classify_rmp_residual_impact(
    *,
    first_negative_task_set: tuple[int, ...],
    active_relation: str,
    active_value: float | None,
    active_journey_count: int,
    first_negative_added_journeys: int,
    first_negative_added_new_task_set_count: int,
    first_negative_added_support_changing_count: int,
    negative_task_set_unique_count: int,
    post_first_negative_objective_delta: float | None,
    post_first_negative_dual_l1_delta: float | None,
    active_fractional_ratio: float | None,
    eps: float = 1.0e-6,
    dual_move_eps: float = 1.0e-6,
) -> tuple[str, str]:
    if not first_negative_task_set:
        return ("no_followup_negative", "no ordinary follow-up negative after worker addition")
    if int(first_negative_added_journeys) <= 0:
        return ("no_followup_addition", "no column-addition event for the first follow-up residual")
    active_exact = str(active_relation) == "same_task_set"
    objective_delta = post_first_negative_objective_delta
    dual_delta = post_first_negative_dual_l1_delta
    if active_exact and int(negative_task_set_unique_count) > 1:
        return (
            "active_residual_then_new_negative_family",
            f"residual active value={active_value}; unique_followup_negatives={int(negative_task_set_unique_count)}",
        )
    if not active_exact and int(negative_task_set_unique_count) > 1:
        return (
            "inactive_residual_then_new_negative_family",
            f"active_relation={str(active_relation)}; unique_followup_negatives={int(negative_task_set_unique_count)}",
        )
    if active_exact and objective_delta is not None and abs(float(objective_delta)) <= float(eps):
        if dual_delta is not None and float(dual_delta) > float(dual_move_eps):
            return (
                "active_residual_degenerate_dual_move",
                f"objective_delta={float(objective_delta):.9f}, dual_l1_delta={float(dual_delta):.9f}",
            )
        return ("active_residual_zero_objective_move", "residual active but objective did not move")
    if active_exact and int(first_negative_added_support_changing_count) <= 0:
        return (
            "became_active_after_rmp_without_addition_active_signal",
            f"active value={active_value}, active journey count={int(active_journey_count)}",
        )
    if active_exact:
        return (
            "active_residual_after_rmp",
            f"active value={active_value}, active journey count={int(active_journey_count)}",
        )
    if active_fractional_ratio is not None and float(active_fractional_ratio) > 0.0:
        return (
            "inactive_residual_with_fractional_active_pressure",
            f"active_fractional_ratio={float(active_fractional_ratio):.9f}",
        )
    if int(first_negative_added_new_task_set_count) > 0:
        return (
            "inactive_new_residual_after_rmp",
            f"active_relation={str(active_relation)}",
        )
    return ("inactive_residual_after_rmp", f"active_relation={str(active_relation)}")


def _classify_residual_family_chain(
    *,
    first_negative_task_set: tuple[int, ...],
    active_persistence_count: int,
    active_last_value: float | None,
    active_basis_unique_count: int,
    active_basis_churn_count: int,
    negative_family_after_first_count: int,
    negative_family_same_count: int,
    negative_family_overlapping_count: int,
    negative_family_disjoint_count: int,
    eps: float = 1.0e-6,
) -> tuple[str, str]:
    if not first_negative_task_set:
        return ("no_followup_negative", "no ordinary follow-up negative after worker addition")
    if int(negative_family_after_first_count) <= 0:
        if int(active_persistence_count) > 0:
            return (
                "active_residual_no_observed_new_family",
                f"active_persistence_count={int(active_persistence_count)}",
            )
        return ("single_residual_no_active_persistence", "one residual negative and no later family")
    active_persistent = int(active_persistence_count) > 0 and (
        active_last_value is None or float(active_last_value) > float(eps)
    )
    churn = int(active_basis_churn_count) > 0 or int(active_basis_unique_count) > 1
    if active_persistent and int(negative_family_disjoint_count) == int(negative_family_after_first_count):
        return (
            "persistent_active_residual_with_disjoint_new_family",
            f"active_last_value={active_last_value}; disjoint_later={int(negative_family_disjoint_count)}",
        )
    if active_persistent and int(negative_family_overlapping_count) > 0:
        return (
            "persistent_active_residual_with_overlapping_new_family",
            f"active_last_value={active_last_value}; overlapping_later={int(negative_family_overlapping_count)}",
        )
    if active_persistent and int(negative_family_same_count) > 0:
        return (
            "persistent_active_residual_with_repeated_same_family",
            f"active_last_value={active_last_value}; repeated_same={int(negative_family_same_count)}",
        )
    if churn and int(negative_family_after_first_count) > 0:
        return (
            "active_basis_churn_with_new_family",
            f"basis_unique={int(active_basis_unique_count)}; basis_churn={int(active_basis_churn_count)}",
        )
    if int(active_persistence_count) <= 0 and int(negative_family_after_first_count) > 0:
        return (
            "inactive_residual_with_new_family_chain",
            f"later_negative_families={int(negative_family_after_first_count)}",
        )
    return (
        "residual_family_chain_unclassified",
        f"later={int(negative_family_after_first_count)}; active_count={int(active_persistence_count)}",
    )


def _classify_rmp_degeneracy_pressure(
    *,
    first_negative_task_set: tuple[int, ...],
    active_basis_unique_count: int,
    active_basis_churn_count: int,
    negative_family_after_first_count: int,
    negative_family_overlapping_count: int,
    negative_family_disjoint_count: int,
    pool_duplicate_task_set_ratio: float | None,
    pool_active_duplicate_task_set_ratio: float | None,
    active_fractional_ratio: float | None,
    active_fractional_value_sum: float | None,
    post_first_negative_objective_delta: float | None,
    post_first_negative_dual_l1_delta: float | None,
    duplicate_ratio_threshold: float = 0.2,
    fractional_ratio_threshold: float = 0.5,
    dual_move_eps: float = 1.0e-6,
) -> tuple[str, str]:
    if not first_negative_task_set:
        return ("no_followup_negative", "no ordinary follow-up negative after worker addition")
    duplicate_ratio = pool_duplicate_task_set_ratio
    active_duplicate_ratio = pool_active_duplicate_task_set_ratio
    fractional_ratio = active_fractional_ratio
    fractional_sum = active_fractional_value_sum
    if active_duplicate_ratio is not None and float(active_duplicate_ratio) >= float(duplicate_ratio_threshold):
        return (
            "active_pool_duplicate_pressure",
            f"active_duplicate_ratio={float(active_duplicate_ratio):.6f}",
        )
    if duplicate_ratio is not None and float(duplicate_ratio) >= float(duplicate_ratio_threshold):
        return ("pool_duplicate_pressure", f"duplicate_ratio={float(duplicate_ratio):.6f}")
    if fractional_ratio is not None and float(fractional_ratio) >= float(fractional_ratio_threshold):
        return (
            "active_fractional_pressure",
            f"active_fractional_ratio={float(fractional_ratio):.6f}",
        )
    if fractional_sum is not None and float(fractional_sum) > 0.0:
        return (
            "active_fractional_value_pressure",
            f"active_fractional_value_sum={float(fractional_sum):.6f}",
        )
    stable_basis = int(active_basis_unique_count) <= 1 and int(active_basis_churn_count) <= 0
    dual_delta = post_first_negative_dual_l1_delta
    objective_delta = post_first_negative_objective_delta
    if stable_basis and int(negative_family_overlapping_count) > 0:
        if dual_delta is not None and float(dual_delta) > float(dual_move_eps):
            return (
                "stable_basis_overlapping_family_with_dual_move",
                f"overlapping={int(negative_family_overlapping_count)}; dual_l1_delta={float(dual_delta):.6f}",
            )
        return (
            "stable_basis_overlapping_family",
            f"overlapping={int(negative_family_overlapping_count)}",
        )
    if stable_basis and int(negative_family_disjoint_count) > 0:
        return (
            "stable_basis_disjoint_family",
            f"disjoint={int(negative_family_disjoint_count)}",
        )
    if int(active_basis_churn_count) > 0 or int(active_basis_unique_count) > 1:
        return (
            "active_basis_churn_pressure",
            f"basis_unique={int(active_basis_unique_count)}; basis_churn={int(active_basis_churn_count)}",
        )
    if (
        int(negative_family_after_first_count) <= 0
        and objective_delta is not None
        and dual_delta is not None
        and abs(float(objective_delta)) <= 1.0e-6
        and float(dual_delta) > float(dual_move_eps)
    ):
        return (
            "dual_move_without_objective_progress",
            f"objective_delta={float(objective_delta):.9f}; dual_l1_delta={float(dual_delta):.9f}",
        )
    if int(negative_family_after_first_count) > 0:
        return (
            "new_family_without_pool_pressure",
            f"later_negative_families={int(negative_family_after_first_count)}",
        )
    return ("no_clear_degeneracy_pressure", "no pool/fractional/basis pressure signal")


def _dual_objective_abs_ratio(
    objective_delta: float | None,
    dual_l1_delta: float | None,
    *,
    eps: float = 1.0e-9,
) -> float | None:
    if objective_delta is None or dual_l1_delta is None:
        return None
    denominator = max(abs(float(objective_delta)), float(eps))
    return round(abs(float(dual_l1_delta)) / denominator, 9)


def _classify_dual_move(
    objective_delta: float | None,
    dual_l1_delta: float | None,
    *,
    eps: float = 1.0e-6,
    large_ratio: float = 3.0,
) -> tuple[str, float | None]:
    ratio = _dual_objective_abs_ratio(objective_delta, dual_l1_delta)
    if objective_delta is None or dual_l1_delta is None:
        return ("no_post_first_negative_rmp", ratio)
    if abs(float(dual_l1_delta)) <= float(eps):
        return ("no_dual_move", ratio)
    if abs(float(objective_delta)) <= float(eps):
        return ("dual_move_without_objective_progress", ratio)
    if ratio is not None and float(ratio) >= float(large_ratio):
        return ("large_dual_move_relative_to_objective", ratio)
    return ("proportional_dual_objective_move", ratio)


def _classify_pool_compression_candidate(
    *,
    pool_duplicate_task_set_ratio: float | None,
    pool_active_duplicate_task_set_ratio: float | None,
    pool_max_journeys_per_task_set: int,
    pool_avg_journeys_per_task_set: float | None,
    pool_active_avg_journeys_per_task_set: float | None,
    duplicate_ratio_threshold: float = 0.2,
    max_journeys_threshold: int = 2,
    avg_journeys_threshold: float = 1.5,
) -> tuple[str, str]:
    if pool_active_duplicate_task_set_ratio is not None and float(pool_active_duplicate_task_set_ratio) >= float(
        duplicate_ratio_threshold
    ):
        return (
            "active_pool_compression_candidate",
            f"active_duplicate_ratio={float(pool_active_duplicate_task_set_ratio):.6f}",
        )
    if pool_duplicate_task_set_ratio is not None and float(pool_duplicate_task_set_ratio) >= float(
        duplicate_ratio_threshold
    ):
        return (
            "pool_compression_candidate",
            f"duplicate_ratio={float(pool_duplicate_task_set_ratio):.6f}",
        )
    if int(pool_max_journeys_per_task_set) > int(max_journeys_threshold):
        return (
            "pool_compression_candidate",
            f"max_journeys_per_task_set={int(pool_max_journeys_per_task_set)}",
        )
    if pool_active_avg_journeys_per_task_set is not None and float(
        pool_active_avg_journeys_per_task_set
    ) > float(avg_journeys_threshold):
        return (
            "active_pool_compression_candidate",
            f"active_avg_journeys_per_task_set={float(pool_active_avg_journeys_per_task_set):.6f}",
        )
    if pool_avg_journeys_per_task_set is not None and float(pool_avg_journeys_per_task_set) > float(
        avg_journeys_threshold
    ):
        return (
            "pool_compression_candidate",
            f"avg_journeys_per_task_set={float(pool_avg_journeys_per_task_set):.6f}",
        )
    return ("no_pool_compression_signal", "no duplicate or multi-journey task-set pressure")


def _classify_rmp_stabilization_candidate(
    *,
    rmp_degeneracy_pressure_class: str,
    dual_move_class: str,
    pool_compression_candidate_class: str,
    active_fractional_ratio: float | None,
    active_fractional_value_sum: float | None,
) -> tuple[str, str]:
    if str(pool_compression_candidate_class) in {
        "pool_compression_candidate",
        "active_pool_compression_candidate",
    }:
        return (
            "pool_compression_precheck_candidate",
            f"pool_class={str(pool_compression_candidate_class)}",
        )
    pressure_class = str(rmp_degeneracy_pressure_class)
    if pressure_class == "active_fractional_pressure":
        return (
            "active_family_stabilization_candidate",
            f"active_fractional_ratio={active_fractional_ratio}; active_fractional_value_sum={active_fractional_value_sum}",
        )
    if pressure_class == "active_fractional_value_pressure":
        return (
            "active_family_stabilization_candidate",
            f"active_fractional_value_sum={active_fractional_value_sum}",
        )
    if pressure_class == "stable_basis_overlapping_family_with_dual_move":
        return (
            "stable_basis_dual_stabilization_candidate",
            f"dual_move_class={str(dual_move_class)}",
        )
    if pressure_class == "active_basis_churn_pressure":
        return ("basis_churn_stabilization_candidate", "active basis hash changed after residual")
    if str(dual_move_class) == "dual_move_without_objective_progress":
        return ("dual_stabilization_candidate", str(dual_move_class))
    return ("no_stabilization_candidate", f"pressure_class={pressure_class}")


def _stabilization_diagnostic_design(
    *,
    rmp_stabilization_candidate_class: str,
    rmp_stabilization_candidate_reason: str,
    rmp_degeneracy_pressure_class: str,
    dual_move_class: str,
    pool_compression_candidate_class: str,
) -> dict[str, Any]:
    config_keys_common = [
        "journey_rmp_stabilization_diagnostic_enabled",
        "journey_rmp_stabilization_diagnostic_mode",
        "journey_rmp_stabilization_diagnostic_allow_certificate_effect",
        "journey_rmp_stabilization_diagnostic_context_hash_required",
    ]
    candidate = str(rmp_stabilization_candidate_class)
    if candidate == "active_family_stabilization_candidate":
        keys = [
            *config_keys_common,
            "journey_rmp_stabilization_active_family_fractional_threshold",
            "journey_rmp_stabilization_active_family_dual_anchor_weight",
        ]
        return {
            "design_class": "active_family_stabilization_diagnostic",
            "design_reason": str(rmp_stabilization_candidate_reason),
            "recommended_profile": "diagnostic_active_family_dual_anchor_audit_only",
            "guarded_config_keys": _compact_json_string(keys),
            "certificate_effect_allowed": False,
        }
    if candidate == "stable_basis_dual_stabilization_candidate":
        keys = [
            *config_keys_common,
            "journey_rmp_stabilization_stable_basis_dual_anchor_weight",
            "journey_rmp_stabilization_stable_basis_required_hash_repeats",
        ]
        reason = str(rmp_stabilization_candidate_reason)
        if str(dual_move_class) and f"dual_move_class={str(dual_move_class)}" not in reason:
            reason = f"{reason}; dual_move_class={str(dual_move_class)}"
        return {
            "design_class": "stable_basis_dual_stabilization_diagnostic",
            "design_reason": reason,
            "recommended_profile": "diagnostic_stable_basis_dual_anchor_audit_only",
            "guarded_config_keys": _compact_json_string(keys),
            "certificate_effect_allowed": False,
        }
    if candidate == "pool_compression_precheck_candidate":
        keys = [
            "journey_pool_compression_diagnostic_enabled",
            "journey_pool_compression_diagnostic_mode",
            "journey_pool_compression_diagnostic_allow_certificate_effect",
            "journey_pool_compression_diagnostic_context_hash_required",
        ]
        return {
            "design_class": "pool_compression_precheck_diagnostic",
            "design_reason": str(rmp_stabilization_candidate_reason),
            "recommended_profile": "diagnostic_pool_compression_audit_only",
            "guarded_config_keys": _compact_json_string(keys),
            "certificate_effect_allowed": False,
        }
    if candidate in {"basis_churn_stabilization_candidate", "dual_stabilization_candidate"}:
        keys = [
            *config_keys_common,
            "journey_rmp_stabilization_dual_move_ratio_threshold",
            "journey_rmp_stabilization_objective_delta_floor",
        ]
        return {
            "design_class": "generic_dual_stabilization_diagnostic",
            "design_reason": str(rmp_stabilization_candidate_reason),
            "recommended_profile": "diagnostic_dual_move_anchor_audit_only",
            "guarded_config_keys": _compact_json_string(keys),
            "certificate_effect_allowed": False,
        }
    return {
        "design_class": "no_stabilization_diagnostic",
        "design_reason": (
            f"candidate={candidate}; pressure={str(rmp_degeneracy_pressure_class)}; "
            f"pool={str(pool_compression_candidate_class)}"
        ),
        "recommended_profile": "",
        "guarded_config_keys": "",
        "certificate_effect_allowed": False,
    }


def _stabilization_probe_skeleton(
    *,
    stabilization_diagnostic_design: dict[str, Any],
    rmp_stabilization_candidate_class: str,
    rmp_stabilization_candidate_reason: str,
    context_hash: str | None,
) -> dict[str, Any]:
    design_class = str(stabilization_diagnostic_design.get("design_class", ""))
    recommended_profile = str(stabilization_diagnostic_design.get("recommended_profile", ""))
    design_reason = str(
        stabilization_diagnostic_design.get("design_reason")
        or rmp_stabilization_candidate_reason
        or ""
    )
    candidate_source = str(rmp_stabilization_candidate_class or "")
    context = str(context_hash or "")
    mode_by_design = {
        "active_family_stabilization_diagnostic": "active_family_dual_anchor",
        "stable_basis_dual_stabilization_diagnostic": "stable_basis_dual_anchor",
        "generic_dual_stabilization_diagnostic": "generic_dual_anchor",
        "pool_compression_precheck_diagnostic": "pool_compression_precheck",
    }
    anchor_weight_by_mode = {
        "active_family_dual_anchor": 0.10,
        "stable_basis_dual_anchor": 0.05,
        "generic_dual_anchor": 0.05,
        "pool_compression_precheck": 0.0,
    }
    mode = mode_by_design.get(design_class, "")
    has_design = bool(mode)
    if not has_design:
        return {
            "enabled": False,
            "status": "no_stabilization_design",
            "reason": design_reason,
            "mode": "",
            "candidate_source": candidate_source or "no_stabilization_candidate",
            "anchor_weight": 0.0,
            "context_hash_required": False,
            "context_hash": "",
            "certificate_effect_allowed": False,
            "official_effect_allowed": False,
            "mutates_rmp": False,
            "design_profile": recommended_profile,
        }
    if not context:
        return {
            "enabled": False,
            "status": "blocked_missing_context_hash",
            "reason": design_reason,
            "mode": mode,
            "candidate_source": candidate_source,
            "anchor_weight": anchor_weight_by_mode[mode],
            "context_hash_required": True,
            "context_hash": "",
            "certificate_effect_allowed": False,
            "official_effect_allowed": False,
            "mutates_rmp": False,
            "design_profile": recommended_profile,
        }
    return {
        "enabled": True,
        "status": "audit_only_probe_planned",
        "reason": design_reason,
        "mode": mode,
        "candidate_source": candidate_source,
        "anchor_weight": anchor_weight_by_mode[mode],
        "context_hash_required": True,
        "context_hash": context,
        "certificate_effect_allowed": False,
        "official_effect_allowed": False,
        "mutates_rmp": False,
        "design_profile": recommended_profile,
    }


def _apply_pivot_recommendation(row: dict[str, Any]) -> None:
    pivot_class, reason = _classify_pivot_recommendation(row)
    row["pivot_recommendation_class"] = pivot_class
    row["pivot_recommendation_reason"] = reason


def _classify_pivot_recommendation(row: dict[str, Any]) -> tuple[str, str]:
    if bool(row.get("critical_disagreement", False)) or int(row.get("critical_disagreement_count") or 0) > 0:
        return ("correctness_blocker", "critical disagreement present")
    if int(row.get("pulse_residual_replay_rc_mismatch_count") or 0) > 0:
        return ("correctness_blocker", "residual replay RC mismatch")
    if int(row.get("pulse_residual_replay_signature_mismatch_count") or 0) > 0:
        return ("correctness_blocker", "residual replay signature mismatch")

    profile_dp_class = str(row.get("followup_profile_dp_incomplete_class", "") or "")
    if bool(row.get("followup_profile_dp_state_cap_hit", False)) or profile_dp_class == "profile_dp_state_cap_hit":
        return ("profile_dp_state_cap", "follow-up profile-DP hit state cap")
    if profile_dp_class.startswith("profile_dp_") and profile_dp_class != "no_profile_dp_incomplete":
        return ("profile_dp_incomplete", profile_dp_class)

    relation = str(row.get("followup_first_negative_relation_to_worker", "") or "")
    if relation == "disjoint_task_set":
        return ("residual_disjoint_negative", "follow-up negative is disjoint from worker task set")
    if relation in {"overlapping_task_set", "same_task_set"}:
        return ("residual_overlapping_negative", f"follow-up negative relation={relation}")

    duplicate_ratio = _as_float_or_none(row.get("pool_duplicate_task_set_ratio_last"))
    duplicate_count = int(row.get("pool_duplicate_task_sets_last") or 0)
    if duplicate_ratio is not None and duplicate_ratio >= 0.2:
        return ("pool_duplicate_pressure", f"duplicate task-set ratio={duplicate_ratio:.6f}")
    if duplicate_count > 0:
        return ("pool_duplicate_pressure", f"duplicate task sets={duplicate_count}")

    fractional_ratio = _as_float_or_none(row.get("pool_active_fractional_ratio_last"))
    if fractional_ratio is not None and fractional_ratio >= 0.5:
        return ("rmp_fractional_active_pressure", f"active fractional ratio={fractional_ratio:.6f}")

    if int(row.get("worker_added_journeys") or 0) > 0:
        return ("worker_column_impact_unclear", "worker added columns without classified follow-up bottleneck")
    return ("no_clear_pivot_signal", "no worker/pool/follow-up bottleneck signal")


def _official_unchanged(baseline: dict[str, Any] | None, row: dict[str, Any]) -> bool:
    if not baseline:
        return False
    keys = (
        "official_status",
        "official_dual_bound",
        "official_primal_bound",
        "official_gap",
    )
    return all(_same_value(baseline.get(key), row.get(key)) for key in keys)


def _apply_baseline_comparison(baseline: dict[str, Any] | None, row: dict[str, Any]) -> None:
    if not baseline:
        row["official_unchanged_vs_baseline"] = False
        row["official_result_changed_vs_baseline"] = True
        row["objective_mismatch_vs_baseline"] = True
        row["improvement_class"] = "inconclusive"
        return
    official_unchanged = _official_unchanged(baseline, row)
    row["official_unchanged_vs_baseline"] = official_unchanged
    row["official_result_changed_vs_baseline"] = not official_unchanged
    objective_mismatch = (
        str(baseline.get("official_status", "")) == "OPTIMAL"
        and str(row.get("official_status", "")) == "OPTIMAL"
        and not (
            _same_value(baseline.get("official_primal_bound"), row.get("official_primal_bound"))
            and _same_value(baseline.get("official_dual_bound"), row.get("official_dual_bound"))
        )
    )
    row["objective_mismatch_vs_baseline"] = objective_mismatch
    row["improvement_class"] = _classify_improvement(baseline, row)


def _classify_improvement(baseline: dict[str, Any], row: dict[str, Any]) -> str:
    if bool(row.get("critical_disagreement", False)) or int(
        row.get("critical_disagreement_count") or 0
    ) > 0:
        return "unsafe"
    if bool(row.get("objective_mismatch_vs_baseline", False)):
        return "unsafe"
    baseline_status = str(baseline.get("official_status", ""))
    row_status = str(row.get("official_status", ""))
    if baseline_status == "OPTIMAL" and row_status != "OPTIMAL":
        return "worsened"
    if baseline_status != "OPTIMAL" and row_status == "OPTIMAL":
        return "improved"
    scale = _as_int(row.get("scale"))
    if scale >= 20 and baseline_status == row_status and row_status != "OPTIMAL":
        baseline_primal = _as_float_or_none(
            baseline.get("primal", baseline.get("official_primal_bound"))
        )
        row_primal = _as_float_or_none(row.get("primal", row.get("official_primal_bound")))
        if (
            baseline_primal is not None
            and row_primal is not None
            and row_primal > baseline_primal + 1.0e-6
        ):
            return "worsened"
        if (
            baseline_primal is not None
            and row_primal is not None
            and row_primal < baseline_primal - 1.0e-6
        ):
            return "improved"
    baseline_time = _as_float_or_none(baseline.get("wall_time"))
    row_time = _as_float_or_none(row.get("wall_time"))
    baseline_gap = _as_float_or_none(baseline.get("gap"))
    row_gap = _as_float_or_none(row.get("gap"))
    baseline_retry = _as_int(baseline.get("exact_completion_bound_retry_count"))
    row_retry = _as_int(row.get("exact_completion_bound_retry_count"))
    if baseline_time is not None and row_time is not None:
        allowed_increase = max(0.2, 0.05 * max(baseline_time, 0.0))
        if row_time > baseline_time + allowed_increase:
            return "worsened"
        if baseline_time > 0.0 and row_time <= 0.85 * baseline_time:
            return "improved"
    if baseline_gap is not None and row_gap is not None and baseline_gap > 0.0:
        if row_gap <= 0.9 * baseline_gap:
            return "improved"
    if baseline_retry > 0 and row_retry <= max(0, int(math.floor(0.75 * baseline_retry))):
        return "improved"
    if bool(row.get("pulse_worker_added_journeys", 0)):
        objective_delta = _as_float_or_none(row.get("pulse_worker_next_rmp_objective_delta"))
        if objective_delta is not None and abs(objective_delta) > 1.0e-7:
            return "no_regression"
    return "no_regression"


def _same_value(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return left is None and right is None
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1.0e-6)
    return left == right


def _as_float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _as_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(value)


def _parse_int_sequence_value(value: Any) -> tuple[int, ...]:
    if value is None:
        return tuple()
    if isinstance(value, (list, tuple)):
        sequence: list[int] = []
        for item in value:
            try:
                sequence.append(int(item))
            except (TypeError, ValueError):
                return tuple()
        return tuple(sequence)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return tuple()
        if "|" in text:
            text = text.split("|", 1)[0]
        sequence = []
        for raw_item in text.replace("[", "").replace("]", "").split(","):
            raw_item = raw_item.strip()
            if not raw_item:
                continue
            try:
                sequence.append(int(raw_item))
            except ValueError:
                return tuple()
        return tuple(sequence)
    return tuple()


def _derive_auto_residual_target(
    previous_rows: list[dict[str, Any]],
    *,
    profile: str,
) -> dict[str, Any]:
    auto_profiles = {
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_diagnostic",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_roi_gate",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_diagnostic",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_roi_gate",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_roi_gate",
    }
    active_gate_profiles = {
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_diagnostic",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_roi_gate",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic",
        "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_roi_gate",
    }
    if profile not in auto_profiles:
        return {}
    source_search = (
        _summarize_active_residual_source_search(previous_rows)
        if profile in active_gate_profiles
        else {}
    )
    first_blocked: dict[str, Any] = {}
    for row in reversed(previous_rows):
        if _as_int(row.get("scale", row.get("tasks"))) < 20:
            continue
        source_context_hash = str(
            row.get("worker_context_hash")
            or row.get("pulse_worker_context_hash")
            or ""
        )
        if not source_context_hash:
            continue
        sequence = _parse_int_sequence_value(row.get("followup_first_negative_sequence"))
        if not sequence:
            sequence = _parse_int_sequence_value(row.get("followup_first_negative_task_set"))
        if len(sequence) < 2:
            continue
        candidate = {
            "candidate_sequence": tuple(sequence),
            "source_profile": str(row.get("profile", "")),
            "source_context_hash": source_context_hash,
            "source_relation": str(
                row.get("worker_vs_ordinary_task_set_relation")
                or row.get("followup_first_negative_relation_to_worker")
                or ""
            ),
        }
        if profile in active_gate_profiles:
            gate_reason = _auto_residual_target_active_source_gate_reason(row)
            candidate["source_gate"] = "active_support"
            if gate_reason:
                candidate["blocked_sequence"] = tuple(sequence)
                candidate["source_gate_reason"] = gate_reason
                if not first_blocked:
                    first_blocked = {**source_search, **candidate}
                continue
            candidate["source_gate_reason"] = "passed"
        return {
            "sequence": tuple(sequence),
            **source_search,
            **candidate,
        }
    return first_blocked or source_search


def _active_residual_source_signal_count(row: dict[str, Any]) -> int:
    return max(
        _as_int(row.get("worker_added_support_changing_count")),
        _as_int(row.get("pulse_worker_impact_filter_selected_active_support_changing_count")),
        _as_int(row.get("followup_worker_active_task_set_count")),
    )


def _active_residual_source_candidate_sequence(row: dict[str, Any]) -> tuple[int, ...]:
    sequence = _parse_int_sequence_value(row.get("followup_first_negative_sequence"))
    if not sequence:
        sequence = _parse_int_sequence_value(row.get("followup_first_negative_task_set"))
    return sequence


def _active_residual_source_row_summary(row: dict[str, Any]) -> dict[str, Any]:
    sequence = _active_residual_source_candidate_sequence(row)
    context_hash = str(
        row.get("worker_context_hash")
        or row.get("pulse_worker_context_hash")
        or ""
    )
    relation = str(
        row.get("worker_vs_ordinary_task_set_relation")
        or row.get("followup_first_negative_relation_to_worker")
        or ""
    )
    active_signal_count = _active_residual_source_signal_count(row)
    candidate = (
        _as_int(row.get("scale", row.get("tasks"))) >= 20
        and bool(context_hash)
        and len(sequence) >= 2
    )
    if candidate:
        gate_reason = _auto_residual_target_active_source_gate_reason(row)
    elif _as_int(row.get("scale", row.get("tasks"))) < 20:
        gate_reason = "scale_below_20"
    elif not context_hash:
        gate_reason = "missing_context_hash"
    elif len(sequence) < 2:
        gate_reason = "missing_followup_negative"
    else:
        gate_reason = "not_candidate"
    return {
        "active_residual_source_candidate": bool(candidate),
        "active_residual_source_candidate_sequence": _task_set_string(sequence),
        "active_residual_source_context_hash": context_hash,
        "active_residual_source_relation": relation,
        "active_residual_source_active_signal_count": int(active_signal_count),
        "active_residual_source_gate_reason": str(gate_reason),
        "active_residual_source_passed": bool(candidate and not gate_reason),
    }


def _summarize_active_residual_source_search(
    previous_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_count = 0
    passed_count = 0
    blocked_count = 0
    blocked_disjoint_count = 0
    blocked_no_active_count = 0
    blocked_relation_count = 0
    first_passed: dict[str, Any] = {}
    first_blocked: dict[str, Any] = {}
    for row in reversed(previous_rows):
        summary = _active_residual_source_row_summary(row)
        if not bool(summary["active_residual_source_candidate"]):
            continue
        candidate_count += 1
        reason = str(summary["active_residual_source_gate_reason"])
        if reason:
            blocked_count += 1
            if reason == "residual_disjoint_from_worker":
                blocked_disjoint_count += 1
            elif reason == "no_active_support_changing_source":
                blocked_no_active_count += 1
            else:
                blocked_relation_count += 1
            if not first_blocked:
                first_blocked = {
                    "profile": str(row.get("profile", "")),
                    "sequence": _parse_int_sequence_value(
                        summary["active_residual_source_candidate_sequence"]
                    ),
                    "reason": reason,
                }
            continue
        passed_count += 1
        if not first_passed:
            first_passed = {
                "profile": str(row.get("profile", "")),
                "sequence": _parse_int_sequence_value(
                    summary["active_residual_source_candidate_sequence"]
                ),
                "relation": str(summary["active_residual_source_relation"]),
                "context_hash": str(summary["active_residual_source_context_hash"]),
            }
    return {
        "source_search_candidate_count": int(candidate_count),
        "source_search_passed_count": int(passed_count),
        "source_search_blocked_count": int(blocked_count),
        "source_search_blocked_disjoint_count": int(blocked_disjoint_count),
        "source_search_blocked_no_active_count": int(blocked_no_active_count),
        "source_search_blocked_relation_count": int(blocked_relation_count),
        "source_search_first_passed_profile": str(first_passed.get("profile", "")),
        "source_search_first_passed_sequence": tuple(first_passed.get("sequence", tuple())),
        "source_search_first_passed_relation": str(first_passed.get("relation", "")),
        "source_search_first_passed_context_hash": str(first_passed.get("context_hash", "")),
        "source_search_first_blocked_profile": str(first_blocked.get("profile", "")),
        "source_search_first_blocked_sequence": tuple(first_blocked.get("sequence", tuple())),
        "source_search_first_blocked_reason": str(first_blocked.get("reason", "")),
        **_classify_active_residual_source_search(
            candidate_count=candidate_count,
            passed_count=passed_count,
            blocked_count=blocked_count,
            blocked_disjoint_count=blocked_disjoint_count,
            blocked_no_active_count=blocked_no_active_count,
            blocked_relation_count=blocked_relation_count,
        ),
    }


def _classify_active_residual_source_search(
    *,
    candidate_count: int,
    passed_count: int,
    blocked_count: int,
    blocked_disjoint_count: int,
    blocked_no_active_count: int,
    blocked_relation_count: int,
) -> dict[str, str]:
    if int(passed_count) > 0:
        return {
            "source_search_outcome_class": "passed_source_available",
            "source_search_recommendation": "test_active_auto_target_on_passed_source",
        }
    if int(candidate_count) <= 0:
        return {
            "source_search_outcome_class": "no_source_candidate",
            "source_search_recommendation": "broaden_seed_matrix_or_pivot",
        }
    if int(blocked_count) == int(candidate_count) and int(blocked_disjoint_count) == int(candidate_count):
        return {
            "source_search_outcome_class": "disjoint_only_no_passed_source",
            "source_search_recommendation": "do_not_chase_disjoint_residual_target",
        }
    if int(blocked_count) == int(candidate_count) and int(blocked_no_active_count) == int(candidate_count):
        return {
            "source_search_outcome_class": "no_active_signal_only",
            "source_search_recommendation": "seek_active_support_changing_seed_or_pivot",
        }
    if int(blocked_count) == int(candidate_count):
        return {
            "source_search_outcome_class": "blocked_mixed_no_passed_source",
            "source_search_recommendation": "broaden_seed_matrix_before_worker_expansion",
        }
    return {
        "source_search_outcome_class": "mixed_unclassified",
        "source_search_recommendation": "inspect_source_search_rows",
    }


def _auto_residual_target_active_source_gate_reason(row: dict[str, Any]) -> str:
    support_changing_count = _active_residual_source_signal_count(row)
    if support_changing_count <= 0:
        return "no_active_support_changing_source"
    relation = str(
        row.get("worker_vs_ordinary_task_set_relation")
        or row.get("followup_first_negative_relation_to_worker")
        or ""
    )
    if relation in {"same_task_set", "overlapping_task_set"}:
        return ""
    if relation == "disjoint_task_set":
        return "residual_disjoint_from_worker"
    return "residual_relation_not_active_support"


def _apply_auto_residual_target_to_config(
    config: dict[str, Any],
    auto_residual_target: dict[str, Any] | None,
) -> bool:
    target = auto_residual_target or {}
    sequence = _parse_int_sequence_value(target.get("sequence", tuple()))
    source_context_hash = str(target.get("source_context_hash", ""))
    if not sequence or not source_context_hash:
        return False
    sequence_text = _task_set_string(sequence)
    config["journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled"] = True
    config["journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence"] = sequence_text
    config["journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled"] = True
    config["journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence"] = sequence_text
    config["journey_sharded_pulse_hidden_negative_worker_expected_context_hash"] = source_context_hash
    config["journey_sharded_pulse_hidden_negative_worker_auto_residual_target_enabled"] = True
    config["journey_sharded_pulse_hidden_negative_worker_auto_residual_target_source_profile"] = str(
        target.get("source_profile", "")
    )
    return True


if __name__ == "__main__":
    main()

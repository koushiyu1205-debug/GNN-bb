"""Exact-safe journey pricing for the BPC_future journey master."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import bisect
import heapq
import itertools
import math
import os
import time
from typing import Any, Callable

from BPC_future.core.branching import BranchConstraint, partial_sequence_allowed
from BPC_future.core.columns import TimedTrip, evaluate_timed_trip, rounded
from BPC_future.core.cuts import FutureCut
from BPC_future.core.data import ArcOption, FutureData
from BPC_future.core.journey import JourneyColumn, make_journey
from BPC_future.master.journey_rmp import JourneyDuals, manual_journey_reduced_cost
from BPC_future.master.rmp import FutureDuals, manual_reduced_cost
from BPC_future.pricing.journey_harvesting import (
    _select_diverse_journey_candidates as _harvesting_select_diverse_journey_candidates,
)
from BPC_future.pricing.available_mask_completion_bound import AvailableMaskCompletionBound
from BPC_future.pricing.resource_pareto_completion import ResourceParetoCompletionEnvelope
from BPC_future.pricing.sharded_pulse_final_judge import build_dummy_shard_ledger
from BPC_future.pricing.pulse_toy_exhaustive import transition_root_only_pulse
from BPC_future.pricing.trip_pricing import (
    _PartialNoWaitingPathProfile,
    PricingConfig,
    _PricingTimeout,
    _OptimizedArcProfile,
    _complete_no_waiting_partial,
    _extend_no_waiting_partial,
    _max_tasks_per_trip,
    _optimized_arc_profiles_for_sequence,
    _sequence_reduced_cost_lower_bound,
    _sequence_resource_precheck,
    _task_order,
    price_timed_trips,
)


PRICING_STATE_FOUND_NEGATIVE = "FOUND_NEGATIVE"
PRICING_STATE_LOCAL_NO_COLUMN_UNCERTIFIED = "LOCAL_NO_COLUMN_UNCERTIFIED"
PRICING_STATE_CERTIFIED_NO_NEGATIVE = "CERTIFIED_NO_NEGATIVE"
PRICING_STATE_INCOMPLETE_LIMIT = "INCOMPLETE_LIMIT"
PRICING_STATE_DUPLICATE_ONLY = "DUPLICATE_ONLY"


@dataclass(frozen=True)
class JourneyPricingConfig:
    time_bucket_size: float = 10.0
    max_tasks_per_trip: int = 6
    max_sequences: int = 0
    max_timed_evaluations: int = 0
    time_limit: float = 0.0
    absolute_deadline: float | None = None
    final_judge_engine: str = ""
    sharded_final_judge_enabled: bool = False
    sharded_final_judge_dummy_engine_enabled: bool = False
    sharded_final_judge_dummy_mode: str = ""
    sharded_final_judge_allow_test_dummy_certificate: bool = False
    sharded_final_judge_dummy_statuses: tuple[str, ...] = tuple()
    sharded_final_judge_toy_certificate_enabled: bool = False
    pulse_max_recursions: int = 50000
    pulse_exact_safe_pruning_enabled: bool = False
    pulse_archive_dominance_enabled: bool = False
    pulse_archive_max_records_per_key: int = 32
    pulse_support_aware_harvesting_enabled: bool = False
    pulse_negative_harvest_limit: int = 0
    pulse_resume_enabled: bool = False
    pulse_cache_max_states: int = 0
    pulse_parallel_enabled: bool = False
    pulse_parallel_workers: int = 1
    start_time_step: float = 10.0
    path_dominance_enabled: bool = True
    start_optimization_enabled: bool = True
    max_path_combinations_per_sequence: int = 0
    max_candidate_trips: int = 0
    max_dp_states: int = 200000
    allow_partial_negative: bool = False
    profile_pricing_enabled: bool = True
    direct_journey_label_pricing_enabled: bool = False
    direct_journey_label_global_certificate_enabled: bool = False
    direct_journey_label_early_return_negative: bool = True
    direct_journey_label_early_return_negative_min_count: int = 0
    direct_journey_label_early_return_negative_grace_time: float = 0.0
    direct_journey_label_diverse_harvest_enabled: bool = False
    direct_journey_label_diverse_harvest_overlap_threshold: float = 0.4
    direct_journey_label_diverse_harvest_top_k_strongest: int = 5
    direct_journey_label_diverse_harvest_min_fill: int = 20
    direct_journey_label_diverse_harvest_min_new_task_sets: int = 0
    direct_journey_label_diverse_harvest_min_priority_task_sets: int = 0
    direct_journey_label_diverse_harvest_priority_overlap_threshold: float = 1.0
    direct_journey_label_diverse_harvest_support_aware_enabled: bool = False
    direct_journey_label_diverse_harvest_support_overlap_threshold: float = 0.6
    direct_journey_label_diverse_harvest_replacement_cap: int = 8
    direct_journey_label_diverse_harvest_strong_replacement_threshold: float = -1.0e-4
    direct_journey_label_mask_closure_enabled: bool = False
    direct_journey_label_mask_closure_max_masks: int = 8
    direct_journey_label_mask_closure_max_columns_per_mask: int = 6
    direct_journey_label_diverse_harvest_max_containment: float = 0.8
    direct_journey_label_diverse_harvest_allow_duplicate_task_sets: bool = False
    direct_journey_label_diverse_harvest_soft_return_min_count: int = 0
    direct_journey_label_diverse_harvest_soft_return_min_new_task_sets: int = 0
    direct_journey_label_diverse_harvest_soft_return_after_time: float = 0.0
    direct_journey_label_diverse_harvest_soft_return_remaining_time: float = 0.0
    direct_journey_label_diverse_harvest_duplicate_saturation_after_time: float = 0.0
    direct_journey_label_next_sortie_cache_enabled: bool = True
    direct_journey_label_next_sortie_trip_return_limit: int = 0
    direct_journey_label_max_labels_per_node: int = 0
    direct_journey_label_cross_count_dominance_enabled: bool = False
    direct_journey_label_resource_coarsening_time_bucket_size: float = 0.0
    direct_journey_label_resource_coarsening_energy_bucket_size: float = 0.0
    direct_journey_label_existing_task_set_repair_only: bool = False
    direct_journey_label_repair_task_sets: tuple[frozenset[int], ...] = tuple()
    direct_journey_label_new_task_set_only: bool = False
    direct_journey_label_task_set_bound_pruning_enabled: bool = True
    direct_journey_label_completion_bound_enabled: bool = False
    direct_journey_label_completion_bound_mode: str = "bucket"
    direct_journey_label_completion_bound_time_buckets: int = 10
    direct_journey_label_completion_bound_energy_buckets: int = 0
    direct_journey_label_completion_bound_partial_pruning_enabled: bool = True
    direct_journey_label_completion_bound_audit_enabled: bool = False
    direct_journey_label_resource_pareto_completion_enabled: bool = False
    direct_journey_label_resource_pareto_completion_max_front_size: int = 5000
    direct_journey_label_resource_pareto_completion_time_eps: float = 1.0e-3
    direct_journey_label_resource_pareto_completion_energy_eps: float = 1.0e-3
    direct_journey_label_resource_pareto_completion_load_eps: float = 1.0e-6
    direct_journey_label_resource_pareto_completion_rc_eps: float = 1.0e-9
    direct_journey_label_resource_pareto_completion_lazy_enabled: bool = True
    direct_journey_label_available_mask_completion_bound_enabled: bool = False
    direct_journey_label_available_mask_completion_bound_max_subset_size: int = 6
    direct_journey_label_available_mask_completion_bound_max_states: int = 200000
    direct_journey_label_completion_bound_unique_task_helper_enabled: bool = False
    direct_journey_label_completion_bound_unique_route_helper_enabled: bool = False
    direct_journey_label_completion_bound_unique_route_exact_first_step_enabled: bool = False
    direct_journey_label_completion_bound_unique_route_max_tasks: int = 16
    direct_journey_label_completion_bound_unique_route_cache_max_states: int = 0
    direct_journey_label_completion_bound_two_cycle_enabled: bool = False
    direct_journey_label_completion_bound_two_cycle_max_states: int = 0
    direct_journey_label_completion_bound_elapsed_soft_return_enabled: bool = True
    direct_journey_label_profile_timing_enabled: bool = False
    direct_journey_label_partial_max_states: int = 0
    direct_journey_label_ng_dssr_enabled: bool = False
    direct_journey_label_ng_memory_size: int = 8
    direct_journey_label_dssr_initial_memory_size: int = 0
    direct_journey_label_dssr_max_iterations: int = 4
    direct_journey_label_dssr_memory_growth: int = 4
    direct_journey_label_ng_max_labels: int = 200000
    direct_journey_label_ng_min_negative_journeys: int = 1
    direct_journey_label_ng_probe_time_limit: float = 0.0
    direct_journey_label_ng_probe_min_journeys_for_early_return: int = 1
    direct_journey_label_ng_probe_certificate_enabled: bool = False
    direct_journey_label_ng_completion_bound_preprobe_enabled: bool = False
    direct_journey_label_ng_dominance_enabled: bool = True
    direct_journey_label_ng_sequence_key_enabled: bool = True
    direct_journey_label_ng_visit_mask_dominance_enabled: bool = False
    direct_journey_label_ng_reset_memory_between_sorties_enabled: bool = False
    direct_journey_label_ng_certificate_enabled: bool = False
    direct_journey_label_ng_exact_probe_enabled: bool = False
    profile_generation_time_fraction: float = 0.75
    profile_labeling_enabled: bool = False
    profile_labeling_best_first_enabled: bool = True
    profile_labeling_resume_enabled: bool = False
    profile_labeling_physical_catalog_resume_enabled: bool = False
    profile_labeling_existing_catalog_pre_scan_enabled: bool = False
    profile_labeling_physical_catalog_share_across_branches_enabled: bool = False
    profile_labeling_task_set_superset_pruning_enabled: bool = False
    profile_labeling_priority_future_dual_weight: float = 0.0
    profile_labeling_priority_cut_dual_weight: float = 0.0
    profile_cross_dominance_enabled: bool = True
    max_returned_journeys: int = 1
    duplicate_retry_factor: int = 4
    profile_true_rc_candidate_scan_factor: int = 1
    profile_true_rc_candidate_scan_max_candidates: int = 0
    early_return_negative: bool = False
    early_return_negative_min_count: int = 1
    early_return_new_task_set_min_count: int = 0
    early_return_unique_masks_enabled: bool = False
    streaming_pricing_enabled: bool = False
    streaming_profile_batch_size: int = 5000
    streaming_min_negative_batch: int = 1
    streaming_min_returned_journeys: int = 1
    streaming_partial_return_after_time: float = 0.0
    streaming_partial_return_min_journeys: int = 0
    streaming_final_dp_time_reserve: float = 0.0
    streaming_profile_cap_per_mask: int = 0
    streaming_callback_backoff_enabled: bool = False
    streaming_callback_backoff_max_batches: int = 4
    streaming_callback_exhaust_after_profile_count: int = 0
    min_add_reduced_cost: float = 0.0
    dp_bound_pruning_enabled: bool = True
    dp_disjoint_bound_pruning_enabled: bool = True
    dp_disjoint_bound_max_tasks: int = 12
    dp_cross_count_dominance_enabled: bool = True
    profile_dp_max_labels_per_mask: int = 0
    profile_true_rc_materialization_slack: float = 0.0
    profile_true_rc_materialization_max_candidates: int = 0
    profile_no_negative_true_rc_materialization_slack: float = 0.0
    profile_no_negative_true_rc_materialization_max_candidates: int = 0
    profile_replacement_true_rc_materialization_slack: float = 0.0
    profile_replacement_true_rc_materialization_max_candidates: int = 0
    profile_cross_count_true_rc_materialization_slack: float = 0.0
    profile_cross_count_true_rc_materialization_max_candidates: int = 0
    profile_materialization_feasibility_filter_enabled: bool = False
    dp_same_completion_pruning_enabled: bool = False
    profile_catalog_enabled: bool = False
    profile_catalog_resume_enabled: bool = False
    profile_catalog_max_tasks: int = 10
    profile_catalog_max_profiles: int = 200000
    generalized_partial_dominance_enabled: bool = False
    task_set_bound_pruning_enabled: bool = False
    task_set_resource_pruning_enabled: bool = False
    partial_profile_bound_pruning_enabled: bool = False
    profile_online_dominance_enabled: bool = False
    profile_mask_diagnostics_enabled: bool = False
    profile_best_contribution_diagnostics_enabled: bool = False
    profile_best_contribution_diagnostics_max_masks: int = 256
    journey_selection_mode: str = "reduced_cost"
    duplicate_scan_limit: int = 10000
    eps: float = 1.0e-6


def _pricing_absolute_deadline(started: float, config: JourneyPricingConfig) -> float | None:
    deadlines: list[float] = []
    if float(config.time_limit) > 0.0:
        deadlines.append(float(started) + float(config.time_limit))
    absolute_deadline = getattr(config, "absolute_deadline", None)
    if absolute_deadline is not None:
        try:
            value = float(absolute_deadline)
        except (TypeError, ValueError):
            value = 0.0
        if math.isfinite(value) and value > 0.0:
            deadlines.append(value)
    return min(deadlines) if deadlines else None


@dataclass
class JourneyPricingResult:
    journeys: list[JourneyColumn]
    exhausted: bool
    best_reduced_cost: float | None
    generated_sequences: int
    evaluated_timed_trips: int
    candidate_trips: int
    selected_trips: int
    status: str
    reason: str = ""
    profile_dominance_pruned: int = 0
    existing_journeys_filtered: int = 0
    profile_cut_penalty_pruned: int = 0
    weak_negative_journeys_filtered: int = 0
    dp_bound_pruned_labels: int = 0
    dp_cross_count_pruned_labels: int = 0
    profile_catalog_hit: bool = False
    profile_catalog_size: int = 0
    profile_generation_time: float = 0.0
    profile_filter_time: float = 0.0
    profile_dp_time: float = 0.0
    profile_negative_candidate_count: int = 0
    profile_negative_unique_mask_count: int = 0
    profile_negative_new_mask_count: int = 0
    profile_negative_selected_candidate_count: int = 0
    profile_negative_selected_new_mask_count: int = 0
    profile_negative_selected_replacement_mask_count: int = 0
    profile_materialization_candidate_count: int = 0
    profile_materialization_candidate_selected_for_scan_count: int = 0
    profile_materialization_candidate_cap_filtered: int = 0
    profile_materialization_selected_candidate_count: int = 0
    profile_no_negative_materialization_candidate_count: int = 0
    profile_no_negative_materialization_selected_for_scan_count: int = 0
    profile_no_negative_materialization_candidate_cap_filtered: int = 0
    profile_no_negative_materialization_selected_candidate_count: int = 0
    profile_replacement_materialization_candidate_count: int = 0
    profile_replacement_materialization_selected_for_scan_count: int = 0
    profile_replacement_materialization_candidate_cap_filtered: int = 0
    profile_replacement_materialization_selected_candidate_count: int = 0
    profile_cross_count_materialization_candidate_count: int = 0
    profile_cross_count_materialization_selected_for_scan_count: int = 0
    profile_cross_count_materialization_candidate_cap_filtered: int = 0
    profile_cross_count_materialization_selected_candidate_count: int = 0
    profile_materialization_infeasible_candidates_filtered: int = 0
    duplicate_candidate_scan_count: int = 0
    duplicate_candidates_filtered: int = 0
    duplicate_scan_limited: bool = False
    direct_next_sortie_cache_hits: int = 0
    direct_next_sortie_cache_misses: int = 0
    direct_label_max_labels_per_node: int = 0
    direct_label_cross_count_pruned_labels: int = 0
    direct_label_existing_task_set_repair_only: bool = False
    direct_label_new_task_set_only: bool = False
    direct_label_diverse_harvest_enabled: bool = False
    direct_label_diverse_harvest_allow_duplicate_task_sets: bool = False
    direct_label_harvest_candidate_count: int = 0
    direct_label_harvest_selected_count: int = 0
    direct_label_harvest_overlap_deferred: int = 0
    direct_label_harvest_duplicate_task_set_rejected_count: int = 0
    direct_label_harvest_fallback_fill_count: int = 0
    direct_label_harvest_fallback_fill_new_mask_count: int = 0
    direct_label_harvest_fallback_fill_replacement_count: int = 0
    direct_label_harvest_fallback_fill_support_changing_count: int = 0
    direct_label_harvest_fallback_fill_weak_replacement_count: int = 0
    direct_label_harvest_candidate_new_task_set_count: int = 0
    direct_label_harvest_selected_new_task_set_count: int = 0
    direct_label_harvest_selected_replacement_task_set_count: int = 0
    direct_label_harvest_candidate_priority_task_set_count: int = 0
    direct_label_harvest_selected_priority_task_set_count: int = 0
    direct_label_harvest_support_aware_enabled: bool = False
    direct_label_harvest_candidate_support_changing_count: int = 0
    direct_label_harvest_selected_support_changing_count: int = 0
    direct_label_harvest_selected_strong_replacement_count: int = 0
    direct_label_harvest_selected_weak_replacement_count: int = 0
    direct_label_harvest_task_set_dominance_enabled: bool = False
    direct_label_harvest_task_set_dominance_collapsed_count: int = 0
    direct_label_mask_closure_enabled: bool = False
    direct_label_mask_closure_candidate_task_set_count: int = 0
    direct_label_mask_closure_selected_count: int = 0
    direct_label_mask_closure_selected_task_set_count: int = 0
    direct_label_harvest_best_true_rc: float | None = None
    direct_label_harvest_worst_selected_true_rc: float | None = None
    direct_label_harvest_avg_pairwise_jaccard: float | None = None
    direct_label_harvest_soft_return_triggered: bool = False
    harvest_candidate_negative_count: int = 0
    harvest_selected_count: int = 0
    harvest_rejected_overlap_count: int = 0
    harvest_rejected_duplicate_task_set_count: int = 0
    harvest_fallback_fill_count: int = 0
    harvest_fallback_fill_new_mask_count: int = 0
    harvest_fallback_fill_replacement_count: int = 0
    harvest_fallback_fill_support_changing_count: int = 0
    harvest_fallback_fill_weak_replacement_count: int = 0
    harvest_candidate_new_task_set_count: int = 0
    harvest_selected_new_task_set_count: int = 0
    harvest_selected_replacement_task_set_count: int = 0
    harvest_candidate_priority_task_set_count: int = 0
    harvest_selected_priority_task_set_count: int = 0
    harvest_support_aware_enabled: bool = False
    harvest_candidate_support_changing_count: int = 0
    harvest_selected_support_changing_count: int = 0
    harvest_selected_strong_replacement_count: int = 0
    harvest_selected_weak_replacement_count: int = 0
    harvest_task_set_dominance_enabled: bool = False
    harvest_task_set_dominance_collapsed_count: int = 0
    harvest_mask_closure_enabled: bool = False
    harvest_mask_closure_candidate_task_set_count: int = 0
    harvest_mask_closure_selected_count: int = 0
    harvest_mask_closure_selected_task_set_count: int = 0
    harvest_best_true_rc: float | None = None
    harvest_worst_selected_true_rc: float | None = None
    harvest_avg_pairwise_jaccard: float | None = None
    direct_label_resource_coarsening_time_bucket_size: float = 0.0
    direct_label_resource_coarsening_energy_bucket_size: float = 0.0
    direct_label_completion_bound_unique_route_exact_first_step_enabled: bool = False
    direct_label_completion_bound_unique_route_max_tasks: int = 16
    direct_label_completion_bound_unique_route_cache_max_states: int = 0
    direct_label_completion_bound_unique_route_enabled: bool = False
    direct_label_unique_route_cache_budget_exceeded_count: int = 0
    direct_label_unique_route_future_cache_hits: int = 0
    direct_label_unique_route_future_cache_misses: int = 0
    direct_label_unique_route_future_cache_size: int = 0
    direct_label_unique_route_partial_cache_hits: int = 0
    direct_label_unique_route_partial_cache_misses: int = 0
    direct_label_unique_route_partial_cache_size: int = 0
    direct_label_unique_route_exact_first_step_cache_hits: int = 0
    direct_label_unique_route_exact_first_step_cache_misses: int = 0
    direct_label_unique_route_exact_first_step_cache_size: int = 0
    direct_label_unique_route_exact_first_step_resource_bucket_count: int = 0
    direct_label_unique_route_exact_first_step_resource_bucket_revisits: int = 0
    direct_label_profile_timing_enabled: bool = False
    direct_label_profile_next_sortie_calls: int = 0
    direct_label_profile_next_sortie_total_time: float = 0.0
    direct_label_profile_partial_heap_pops: int = 0
    direct_label_profile_extension_attempts: int = 0
    direct_label_profile_option_attempts: int = 0
    direct_label_profile_bound_checks: int = 0
    direct_label_profile_dominance_checks: int = 0
    direct_label_profile_completion_calls: int = 0
    direct_label_profile_resource_precheck_time: float = 0.0
    direct_label_profile_extend_time: float = 0.0
    direct_label_profile_bound_check_time: float = 0.0
    direct_label_profile_pre_dominance_checks: int = 0
    direct_label_profile_pre_dominance_pruned: int = 0
    direct_label_profile_pre_dominance_time: float = 0.0
    direct_label_profile_dominance_time: float = 0.0
    direct_label_profile_completion_time: float = 0.0
    direct_label_profile_partial_bound_dual_sum_time: float = 0.0
    direct_label_profile_partial_bound_unique_task_time: float = 0.0
    direct_label_profile_partial_bound_unique_route_time: float = 0.0
    direct_label_profile_partial_bound_completion_route_time: float = 0.0
    direct_label_profile_partial_bound_resource_pareto_time: float = 0.0
    direct_label_profile_partial_bound_cut_time: float = 0.0
    direct_label_profile_partial_bucket_count: int = 0
    direct_label_profile_partial_bucket_label_count: int = 0
    direct_label_profile_partial_bucket_max_size: int = 0
    direct_label_profile_partial_bucket_mean_size: float = 0.0
    dp_disjoint_bound_pruned_labels: int = 0
    dominated_task_set_journeys_filtered: int = 0
    task_set_resource_pruned_sequences: int = 0
    partial_profile_bound_pruned_labels: int = 0
    label_physical_catalog: bool = False
    label_physical_catalog_exhausted: bool = False
    label_resume_heap: int = 0
    label_resume_profiles: int = 0
    label_resume_exhausted: bool = False
    streaming_callback_exhaust_triggered: bool = False
    streaming_callback_exhaust_threshold: int = 0
    profile_mask_cap_pruned: int = 0
    profile_completion_time_pruned: int = 0
    branch_mask_pruned_sequences: int = 0
    dp_processed_labels: int = 0
    dp_state_count: int = 0
    dp_profile_record_scans: int = 0
    dp_profile_time_filtered: int = 0
    dp_extension_attempts: int = 0
    dp_label_cap_pruned: int = 0
    dp_same_completion_pruned_labels: int = 0
    completion_bound_enabled: bool = False
    completion_bound_cache_hit: bool = False
    completion_bound_cache_stored: bool = False
    bound_build_time: float = 0.0
    lb_state_count: int = 0
    lb_min_value: float | None = None
    lb_mean_value: float | None = None
    lb_negative_state_count: int = 0
    expanded_labels_before_bound: int = 0
    expanded_labels_after_bound: int = 0
    lb_pruned_labels: int = 0
    lb_partial_pruned_labels: int = 0
    lb_suffix_pruned_labels: int = 0
    lb_partial_pruned_no_outgoing: int = 0
    lb_partial_pruned_unique_route_infeasible: int = 0
    lb_partial_pruned_completion_route_infeasible: int = 0
    lb_partial_pruned_unique_task_winner: int = 0
    lb_partial_pruned_unique_route_winner: int = 0
    lb_partial_pruned_completion_route_winner: int = 0
    lb_partial_pruned_resource_pareto_winner: int = 0
    lb_partial_pruned_resource_pareto_infeasible: int = 0
    lb_partial_pruned_available_mask_winner: int = 0
    lb_partial_pruned_route_finish_winner: int = 0
    lb_suffix_pruned_unique_task_winner: int = 0
    lb_suffix_pruned_unique_route_winner: int = 0
    lb_suffix_pruned_completion_route_winner: int = 0
    lb_suffix_pruned_resource_pareto_winner: int = 0
    lb_suffix_pruned_available_mask_winner: int = 0
    lb_partial_cut_reward_positive_checks: int = 0
    lb_suffix_cut_reward_positive_checks: int = 0
    amcb_enabled: bool = False
    amcb_build_time: float = 0.0
    amcb_query_count: int = 0
    amcb_pruned_labels: int = 0
    amcb_partial_winner_count: int = 0
    amcb_suffix_winner_count: int = 0
    amcb_state_count: int = 0
    amcb_closed_subset_count: int = 0
    amcb_tail_state_count: int = 0
    amcb_disabled: bool = False
    amcb_disable_reason: str | None = None
    amcb_skipped_by_unique_route: bool = False
    amcb_resource_filtered_subsets: int = 0
    rpce_enabled: bool = False
    rpce_build_time: float = 0.0
    rpce_arc_front_count: int = 0
    rpce_sortie_front_count: int = 0
    rpce_tail_front_count: int = 0
    rpce_overflow_state_count: int = 0
    rpce_disabled_state_count: int = 0
    rpce_runtime_disabled: bool = False
    rpce_disable_reason: str | None = None
    rpce_query_count: int = 0
    rpce_query_feasible_count: int = 0
    rpce_query_disabled_count: int = 0
    rpce_pruned_labels: int = 0
    rpce_resource_infeasible_labels: int = 0
    rpce_min_lb: float | None = None
    rpce_mean_lb: float | None = None
    generated_next_sorties_before_bound: int = 0
    generated_next_sorties_after_bound: int = 0
    two_cycle_enabled: bool = False
    two_cycle_table_complete: bool = False
    two_cycle_fallback_to_memoryless: bool = False
    two_cycle_state_count: int = 0
    two_cycle_blocked_extensions: int = 0
    two_cycle_second_best_queries: int = 0
    two_cycle_incompatible_queries: int = 0
    two_cycle_top2_replacements: int = 0
    two_cycle_build_time: float = 0.0
    ng_relaxation_enabled: bool = False
    ng_dssr_iterations: int = 0
    ng_memory_size: int = 0
    ng_non_elementary_negative: int = 0
    ng_label_pops: int = 0
    ng_generated_labels: int = 0
    ng_dominance_pruned_labels: int = 0
    ng_fallback_to_elementary: bool = False
    ng_certificate_from_relaxation: bool = False
    ng_certificate_limit_hit: bool = False
    ng_probe_limit_hit: bool = False
    ng_relaxation_superset: bool | None = None
    ng_best_relaxed_reduced_cost: float | None = None
    global_certificate_capable: bool = False
    final_judge_engine: str = ""
    final_judge_certificate_capable: bool = False
    final_judge_sharded_enabled: bool = False
    final_judge_dummy_engine_enabled: bool = False
    final_judge_dummy_mode: str = ""
    final_judge_allow_test_dummy_certificate: bool = False
    final_judge_dummy_certificate: bool = False
    final_judge_test_only: bool = False
    final_judge_shards_total: int = 0
    final_judge_shards_certified: int = 0
    final_judge_shards_incomplete: int = 0
    final_judge_shards_negative_found: int = 0
    final_judge_shards_refined: int = 0
    final_judge_incomplete_reason: str = ""
    pulse_recursions: int = 0
    pulse_expanded_states: int = 0
    pulse_resource_pruned: int = 0
    pulse_return_pruned: int = 0
    pulse_time_window_pruned: int = 0
    pulse_capacity_pruned: int = 0
    pulse_energy_pruned: int = 0
    transition_time_window_pruned: int = 0
    transition_energy_pruned: int = 0
    transition_return_pruned: int = 0
    pulse_bound_pruned: int = 0
    pulse_archive_pruned: int = 0
    pulse_depot_ready_pruned: int = 0
    pulse_negative_found: bool = False
    pulse_harvested_count: int = 0
    pulse_best_true_rc: float | None = None
    pricing_state: str = ""
    diagnostic_profile_task_masks: frozenset[int] = frozenset()
    diagnostic_profile_trip_masks: frozenset[int] = frozenset()
    diagnostic_reachable_task_masks: frozenset[int] = frozenset()
    diagnostic_negative_task_masks: frozenset[int] = frozenset()
    diagnostic_selected_task_masks: frozenset[int] = frozenset()
    diagnostic_best_objective_by_mask: dict[int, float] = field(default_factory=dict)
    diagnostic_best_profile_contribution_by_mask: dict[int, float] = field(default_factory=dict)
    profile_selected_unmaterialized_candidate_count: int = 0
    profile_weak_filtered_materialized_count: int = 0
    profile_weak_filtered_best_rough_rc: float | None = None
    profile_weak_filtered_best_true_rc: float | None = None
    profile_weak_filtered_max_true_minus_rough: float | None = None
    profile_weak_filtered_max_true_minus_rough_mask: int | None = None

    def __post_init__(self) -> None:
        if not str(self.pricing_state or ""):
            self.pricing_state = _infer_journey_pricing_state(self)
        elif str(self.pricing_state) == PRICING_STATE_CERTIFIED_NO_NEGATIVE and not (
            bool(self.global_certificate_capable)
            and str(self.status) == "OPTIMAL"
            and not bool(self.journeys)
            and _pricing_certificate_reason_allowed(self)
        ):
            if bool(self.exhausted) and str(self.status) == "OPTIMAL":
                self.pricing_state = PRICING_STATE_LOCAL_NO_COLUMN_UNCERTIFIED
            else:
                self.pricing_state = PRICING_STATE_INCOMPLETE_LIMIT


def _pricing_certificate_reason_allowed(result: JourneyPricingResult) -> bool:
    reason = str(result.reason or "")
    if bool(result.completion_bound_enabled) and reason == "direct_label_no_negative_journey":
        return True
    if (
        str(getattr(result, "final_judge_engine", "")) in {"sharded_pulse", "sharded_pulse_dummy"}
        and bool(getattr(result, "final_judge_certificate_capable", False))
        and reason == "sharded_pulse_no_negative_journey"
    ):
        return True
    if bool(getattr(result, "ng_certificate_from_relaxation", False)) and reason == "ng_dssr_relaxed_no_negative_journey":
        if bool(getattr(result, "ng_certificate_limit_hit", False)):
            return False
        if bool(getattr(result, "ng_probe_limit_hit", False)):
            return False
        if getattr(result, "ng_relaxation_superset", None) is not True:
            return False
        return True
    return False


def _infer_journey_pricing_state(result: JourneyPricingResult) -> str:
    if result.journeys:
        return PRICING_STATE_FOUND_NEGATIVE
    reason = str(result.reason or "")
    if (
        bool(result.exhausted)
        and bool(result.global_certificate_capable)
        and str(result.status) == "OPTIMAL"
        and _pricing_certificate_reason_allowed(result)
    ):
        return PRICING_STATE_CERTIFIED_NO_NEGATIVE
    if not bool(result.exhausted) or str(result.status) != "OPTIMAL":
        return PRICING_STATE_INCOMPLETE_LIMIT
    if (
        int(result.duplicate_candidates_filtered) > 0
        or int(result.existing_journeys_filtered) > 0
        or int(result.dominated_task_set_journeys_filtered) > 0
        or bool(result.duplicate_scan_limited)
        or reason == "negative_journeys_already_in_pool"
    ):
        return PRICING_STATE_DUPLICATE_ONLY
    if bool(result.exhausted) and str(result.status) == "OPTIMAL":
        return PRICING_STATE_LOCAL_NO_COLUMN_UNCERTIFIED
    return PRICING_STATE_INCOMPLETE_LIMIT


def _journey_column_task_set(journey: JourneyColumn) -> frozenset[int]:
    return frozenset(int(task) for task in getattr(journey, "task_set", tuple()))


def _task_set_mask_from_tasks(task_to_bit: dict[int, int], tasks: Any) -> int:
    mask = 0
    for task in tasks or ():
        bit = task_to_bit.get(int(task))
        if bit is None:
            continue
        mask |= 1 << int(bit)
    return int(mask)


def _direct_repair_target_masks(
    data: FutureData,
    task_to_bit: dict[int, int],
    dominant_task_set_costs: dict[frozenset[int], float] | None,
    repair_task_sets: tuple[frozenset[int], ...] | None = None,
) -> frozenset[int]:
    repair_target_costs_by_mask = _dominant_task_set_costs_by_mask(data, dominant_task_set_costs)
    if repair_task_sets:
        explicit_repair_masks = frozenset(
            int(_task_set_mask_from_tasks(task_to_bit, task_set))
            for task_set in repair_task_sets
        )
        return frozenset(
            int(mask)
            for mask in repair_target_costs_by_mask.keys()
            if int(mask) > 0 and int(mask) in explicit_repair_masks
        )
    return frozenset(
        int(mask)
        for mask in repair_target_costs_by_mask.keys()
        if int(mask) > 0
    )


def _journey_task_jaccard(left: JourneyColumn, right: JourneyColumn) -> float:
    left_tasks = _journey_column_task_set(left)
    right_tasks = _journey_column_task_set(right)
    union = left_tasks | right_tasks
    if not union:
        return 0.0
    return float(len(left_tasks & right_tasks)) / float(len(union))


def _journey_task_containment(left: JourneyColumn, right: JourneyColumn) -> float:
    left_tasks = _journey_column_task_set(left)
    right_tasks = _journey_column_task_set(right)
    if not left_tasks or not right_tasks:
        return 0.0
    return float(len(left_tasks & right_tasks)) / float(min(len(left_tasks), len(right_tasks)))


def _task_set_jaccard(left: frozenset[int], right: frozenset[int]) -> float:
    union = left | right
    if not union:
        return 0.0
    return float(len(left & right)) / float(len(union))


def _avg_pairwise_journey_task_jaccard(journeys: list[JourneyColumn]) -> float | None:
    if len(journeys) < 2:
        return None
    total = 0.0
    pairs = 0
    for left_index, left in enumerate(journeys):
        for right in journeys[left_index + 1 :]:
            total += _journey_task_jaccard(left, right)
            pairs += 1
    return None if pairs <= 0 else float(total) / float(pairs)


@dataclass(frozen=True)
class _DiverseJourneySelection:
    journeys: list[JourneyColumn]
    candidate_negative_count: int
    selected_count: int
    task_set_dominance_enabled: bool
    task_set_dominance_collapsed_count: int
    rejected_overlap_count: int
    rejected_duplicate_task_set_count: int
    fallback_fill_count: int
    fallback_fill_new_mask_count: int
    fallback_fill_replacement_count: int
    fallback_fill_support_changing_count: int
    fallback_fill_weak_replacement_count: int
    candidate_new_task_set_count: int
    selected_new_task_set_count: int
    selected_replacement_task_set_count: int
    candidate_priority_task_set_count: int
    selected_priority_task_set_count: int
    candidate_support_changing_count: int
    selected_support_changing_count: int
    selected_strong_replacement_count: int
    selected_weak_replacement_count: int
    mask_closure_candidate_task_set_count: int
    mask_closure_selected_count: int
    mask_closure_selected_task_set_count: int
    best_true_rc: float | None
    worst_selected_true_rc: float | None
    avg_pairwise_jaccard: float | None


def _select_diverse_journey_candidates(
    candidates: list[tuple[float, JourneyColumn]],
    *,
    max_returned: int,
    top_k_strongest: int = 5,
    min_fill: int = 20,
    min_new_task_sets: int = 0,
    min_priority_task_sets: int = 0,
    max_jaccard: float = 0.5,
    max_containment: float = 0.8,
    overlap_threshold: float | None = None,
    dominant_task_set_costs: dict[frozenset[int], float] | None = None,
    existing_task_sets: set[frozenset[int]] | None = None,
    priority_task_sets: set[frozenset[int]] | None = None,
    priority_overlap_threshold: float = 1.0,
    support_aware_enabled: bool = False,
    support_task_sets: set[frozenset[int]] | None = None,
    support_overlap_threshold: float = 0.6,
    replacement_cap: int = 8,
    strong_replacement_threshold: float = -1.0e-4,
    mask_closure_enabled: bool = False,
    mask_closure_max_masks: int = 8,
    mask_closure_max_columns_per_mask: int = 6,
    prefer_new_task_sets: bool = True,
    allow_duplicate_task_sets: bool = False,
) -> _DiverseJourneySelection:
    """Harvest exact true-RC negative journeys by strength and orthogonality.

    The input candidates have already passed the exact reduced-cost filter.
    This selector only ranks and batches useful directions for the RMP after an
    expensive exact-pricing probe; it never changes certificate validity.
    """

    limit = max(1, int(max_returned))
    if overlap_threshold is not None:
        max_jaccard = float(overlap_threshold)
    jaccard_limit = min(1.0, max(0.0, float(max_jaccard)))
    containment_limit = min(1.0, max(0.0, float(max_containment)))
    strongest_limit = max(0, min(limit, int(top_k_strongest)))
    fill_limit = max(0, min(limit, int(min_fill)))
    new_task_set_quota = max(0, min(limit, int(min_new_task_sets)))
    priority_task_set_quota = max(0, min(limit, int(min_priority_task_sets)))

    best_by_signature: dict[tuple, tuple[float, JourneyColumn]] = {}
    for objective, journey in candidates:
        signature = tuple(getattr(journey, "signature", tuple()))
        old = best_by_signature.get(signature)
        if old is None or (float(objective), signature) < (float(old[0]), signature):
            best_by_signature[signature] = (float(objective), journey)

    dominant_costs = {
        frozenset(int(task) for task in task_set): float(cost)
        for task_set, cost in (dominant_task_set_costs or {}).items()
    }
    task_set_dominance_active = bool(dominant_costs)
    existing_keys = set(dominant_costs.keys()) if task_set_dominance_active else set(existing_task_sets or set())
    priority_keys = {frozenset(int(task) for task in task_set) for task_set in (priority_task_sets or set())}
    priority_overlap = min(1.0, max(0.0, float(priority_overlap_threshold)))
    support_aware = bool(support_aware_enabled)
    support_keys = {frozenset(int(task) for task in task_set) for task_set in (support_task_sets or set())}
    support_overlap = min(1.0, max(0.0, float(support_overlap_threshold)))
    weak_replacement_limit = max(0, min(limit, int(replacement_cap)))
    strong_replacement_cutoff = float(strong_replacement_threshold)
    closure_enabled = bool(mask_closure_enabled) and not task_set_dominance_active
    closure_max_masks = max(0, int(mask_closure_max_masks))
    closure_max_columns_per_mask = max(0, int(mask_closure_max_columns_per_mask))

    scored_source = list(best_by_signature.values())
    raw_candidate_negative_count = len(scored_source)
    if task_set_dominance_active:
        best_by_task_set: dict[frozenset[int], tuple[float, JourneyColumn]] = {}
        for objective, journey in scored_source:
            task_set = _journey_column_task_set(journey)
            incumbent_cost = dominant_costs.get(task_set)
            if incumbent_cost is not None and float(journey.cost) >= float(incumbent_cost) - 1.0e-9:
                continue
            old = best_by_task_set.get(task_set)
            candidate_key = (
                round(float(journey.cost), 9),
                round(float(objective), 9),
                tuple(getattr(journey, "signature", tuple())),
            )
            if old is None:
                best_by_task_set[task_set] = (float(objective), journey)
                continue
            old_objective, old_journey = old
            old_key = (
                round(float(old_journey.cost), 9),
                round(float(old_objective), 9),
                tuple(getattr(old_journey, "signature", tuple())),
            )
            if candidate_key < old_key:
                best_by_task_set[task_set] = (float(objective), journey)
        scored_source = list(best_by_task_set.values())

    def is_priority_task_set(task_set: frozenset[int]) -> bool:
        normalized = frozenset(int(task) for task in task_set)
        if normalized in priority_keys:
            return True
        return any(_task_set_jaccard(normalized, priority) >= priority_overlap for priority in priority_keys)

    def max_support_jaccard(task_set: frozenset[int]) -> float:
        normalized = frozenset(int(task) for task in task_set)
        if not support_keys:
            return 0.0
        return max(_task_set_jaccard(normalized, support) for support in support_keys)

    def support_bucket(objective: float, journey: JourneyColumn) -> str:
        task_set = _journey_column_task_set(journey)
        if task_set not in existing_keys:
            return "new"
        if support_keys and max_support_jaccard(task_set) <= support_overlap:
            return "support"
        if float(objective) <= strong_replacement_cutoff:
            return "strong_replacement"
        return "weak_replacement"

    scored = sorted(
        scored_source,
        key=lambda item: (round(float(item[0]), 9), item[1].signature),
    )
    task_set_dominance_collapsed_count = max(0, len(best_by_signature) - len(scored))
    candidate_new_task_set_count = sum(
        1 for _objective, journey in scored if _journey_column_task_set(journey) not in existing_keys
    )
    candidate_priority_task_set_count = sum(
        1 for _objective, journey in scored if is_priority_task_set(_journey_column_task_set(journey))
    )
    candidate_support_changing_count = sum(
        1
        for objective, journey in scored
        if support_bucket(float(objective), journey) in {"new", "support"}
    )
    # The strongest phase is intentionally based on exact true reduced cost.
    # New task-set preference is only applied afterwards; otherwise a weak new
    # direction could displace the globally strongest negative column when the
    # harvest budget is small.
    diverse_selection_order = scored
    if prefer_new_task_sets and existing_keys and candidate_new_task_set_count > 0:
        diverse_selection_order = sorted(
            scored,
            key=lambda item: (
                0 if _journey_column_task_set(item[1]) not in existing_keys else 1,
                round(float(item[0]), 9),
                item[1].signature,
            ),
        )
    if support_aware:
        bucket_rank = {
            "new": 0,
            "support": 1,
            "strong_replacement": 2,
            "weak_replacement": 3,
        }
        diverse_selection_order = sorted(
            scored,
            key=lambda item: (
                bucket_rank.get(support_bucket(float(item[0]), item[1]), 4),
                round(float(item[0]), 9),
                item[1].signature,
            ),
        )

    selected: list[tuple[float, JourneyColumn]] = []
    selected_signatures: set[tuple] = set()
    selected_task_sets: set[frozenset[int]] = set()
    rejected_duplicate_signatures: set[tuple] = set()
    rejected_overlap = 0
    rejected_duplicate_task_set = 0
    selected_bucket_counts = {
        "new": 0,
        "support": 0,
        "strong_replacement": 0,
        "weak_replacement": 0,
    }
    selected_closure_signatures: set[tuple] = set()

    def selected_weak_replacements() -> int:
        return int(selected_bucket_counts.get("weak_replacement", 0))

    def add_selected(objective: float, journey: JourneyColumn, *, from_closure: bool = False) -> None:
        signature = tuple(getattr(journey, "signature", tuple()))
        selected.append((float(objective), journey))
        selected_signatures.add(signature)
        selected_task_sets.add(_journey_column_task_set(journey))
        if from_closure:
            selected_closure_signatures.add(signature)
        if support_aware:
            bucket = support_bucket(float(objective), journey)
            selected_bucket_counts[bucket] = int(selected_bucket_counts.get(bucket, 0)) + 1

    def weak_replacement_cap_reached(objective: float, journey: JourneyColumn) -> bool:
        if not support_aware:
            return False
        if support_bucket(float(objective), journey) != "weak_replacement":
            return False
        return selected_weak_replacements() >= weak_replacement_limit

    def weak_replacement_cap_reached_for_fill(objective: float, journey: JourneyColumn) -> bool:
        if not weak_replacement_cap_reached(float(objective), journey):
            return False
        # In the final proof tail, all candidates reaching this selector are
        # already exact true-RC negative.  The replacement cap should bias the
        # diverse phase away from weak same-face repairs, but it should not
        # prevent the expensive judge from returning the configured minimum
        # batch when no stronger/new/support directions exist.
        return not (fill_limit > weak_replacement_limit and len(selected) < fill_limit)

    if priority_task_set_quota > 0 and priority_keys:
        for objective, journey in scored:
            selected_priority_so_far = sum(
                1 for _selected_objective, selected_journey in selected
                if is_priority_task_set(_journey_column_task_set(selected_journey))
            )
            if selected_priority_so_far >= min(priority_task_set_quota, candidate_priority_task_set_count):
                break
            signature = tuple(getattr(journey, "signature", tuple()))
            if signature in selected_signatures:
                continue
            task_set = _journey_column_task_set(journey)
            if not is_priority_task_set(task_set):
                continue
            if weak_replacement_cap_reached(float(objective), journey):
                continue
            if not allow_duplicate_task_sets and task_set in selected_task_sets:
                if signature not in rejected_duplicate_signatures:
                    rejected_duplicate_signatures.add(signature)
                    rejected_duplicate_task_set += 1
                continue
            add_selected(float(objective), journey)

    if prefer_new_task_sets and existing_keys and new_task_set_quota > 0:
        for objective, journey in diverse_selection_order:
            selected_new_so_far = sum(
                1 for _selected_objective, selected_journey in selected
                if _journey_column_task_set(selected_journey) not in existing_keys
            )
            if selected_new_so_far >= min(new_task_set_quota, candidate_new_task_set_count):
                break
            signature = tuple(getattr(journey, "signature", tuple()))
            if signature in selected_signatures:
                continue
            task_set = _journey_column_task_set(journey)
            if task_set in existing_keys:
                continue
            if weak_replacement_cap_reached(float(objective), journey):
                continue
            if not allow_duplicate_task_sets and task_set in selected_task_sets:
                if signature not in rejected_duplicate_signatures:
                    rejected_duplicate_signatures.add(signature)
                    rejected_duplicate_task_set += 1
                continue
            add_selected(float(objective), journey)

    for objective, journey in scored:
        if len(selected) >= strongest_limit:
            break
        signature = tuple(getattr(journey, "signature", tuple()))
        if signature in selected_signatures:
            continue
        task_set = _journey_column_task_set(journey)
        if weak_replacement_cap_reached(float(objective), journey):
            continue
        if not allow_duplicate_task_sets and task_set in selected_task_sets:
            if signature not in rejected_duplicate_signatures:
                rejected_duplicate_signatures.add(signature)
                rejected_duplicate_task_set += 1
            continue
        add_selected(float(objective), journey)

    for objective, journey in diverse_selection_order:
        if len(selected) >= limit:
            break
        signature = tuple(getattr(journey, "signature", tuple()))
        if signature in selected_signatures:
            continue
        task_set = _journey_column_task_set(journey)
        if weak_replacement_cap_reached(float(objective), journey):
            continue
        if not allow_duplicate_task_sets and task_set in selected_task_sets:
            if signature not in rejected_duplicate_signatures:
                rejected_duplicate_signatures.add(signature)
                rejected_duplicate_task_set += 1
            continue
        diverse = True
        for _selected_objective, selected_journey in selected:
            if (
                _journey_task_jaccard(journey, selected_journey) > jaccard_limit
                or _journey_task_containment(journey, selected_journey) > containment_limit
            ):
                diverse = False
                break
        if diverse:
            add_selected(float(objective), journey)
        else:
            rejected_overlap += 1

    closure_candidate_task_sets: set[frozenset[int]] = set()
    if closure_enabled and closure_max_masks > 0 and closure_max_columns_per_mask > 0 and len(selected) < limit:
        by_task_set: dict[frozenset[int], list[tuple[float, JourneyColumn]]] = {}
        for objective, journey in scored:
            task_set = _journey_column_task_set(journey)
            by_task_set.setdefault(task_set, []).append((float(objective), journey))

        def closure_task_set_allowed(task_set: frozenset[int], grouped: list[tuple[float, JourneyColumn]]) -> bool:
            if task_set not in existing_keys:
                return False
            if support_keys and task_set in support_keys:
                return True
            # Repeated hidden-negative replacement masks are worth closing even
            # when they are not active; otherwise the same physical alternatives
            # tend to reappear one by one in later final-judge calls.
            return len(grouped) > 1

        closure_groups = [
            (task_set, grouped)
            for task_set, grouped in by_task_set.items()
            if closure_task_set_allowed(task_set, grouped)
        ]
        closure_candidate_task_sets = {task_set for task_set, _grouped in closure_groups}
        closure_groups.sort(
            key=lambda item: (
                0 if item[0] in support_keys else 1,
                round(float(item[1][0][0]), 9),
                tuple(sorted(item[0])),
            )
        )
        closed_masks = 0
        for task_set, grouped in closure_groups:
            if len(selected) >= limit or closed_masks >= closure_max_masks:
                break
            grouped = sorted(grouped, key=lambda item: (round(float(item[0]), 9), item[1].signature))
            added_for_mask = sum(
                1
                for _objective, selected_journey in selected
                if _journey_column_task_set(selected_journey) == task_set
            )
            added_any_for_mask = False
            for objective, journey in grouped:
                if len(selected) >= limit or added_for_mask >= closure_max_columns_per_mask:
                    break
                signature = tuple(getattr(journey, "signature", tuple()))
                if signature in selected_signatures:
                    continue
                # Mask closure intentionally bypasses the one-column-per-task-set
                # rule, but only for bounded active/repeated replacement masks.
                add_selected(float(objective), journey, from_closure=True)
                added_for_mask += 1
                added_any_for_mask = True
            if added_any_for_mask:
                closed_masks += 1

    fallback_fill = 0
    if len(selected) < fill_limit:
        for objective, journey in diverse_selection_order:
            if len(selected) >= fill_limit:
                break
            signature = tuple(getattr(journey, "signature", tuple()))
            if signature in selected_signatures:
                continue
            task_set = _journey_column_task_set(journey)
            if weak_replacement_cap_reached_for_fill(float(objective), journey):
                continue
            if not allow_duplicate_task_sets and task_set in selected_task_sets:
                if signature not in rejected_duplicate_signatures:
                    rejected_duplicate_signatures.add(signature)
                    rejected_duplicate_task_set += 1
                continue
            add_selected(float(objective), journey)
            fallback_fill += 1

    selected.sort(key=lambda item: (round(float(item[0]), 9), item[1].signature))
    selected = selected[:limit]
    selected_journeys = [journey for _objective, journey in selected]
    selected_rcs = [float(objective) for objective, _journey in selected]
    selected_bucket_counts = {
        "new": 0,
        "support": 0,
        "strong_replacement": 0,
        "weak_replacement": 0,
    }
    if support_aware:
        for objective, journey in selected:
            bucket = support_bucket(float(objective), journey)
            selected_bucket_counts[bucket] = int(selected_bucket_counts.get(bucket, 0)) + 1
    selected_closure_signatures = {
        signature
        for signature in selected_closure_signatures
        if any(tuple(getattr(journey, "signature", tuple())) == signature for _objective, journey in selected)
    }
    selected_closure_task_sets = {
        _journey_column_task_set(journey)
        for _objective, journey in selected
        if tuple(getattr(journey, "signature", tuple())) in selected_closure_signatures
    }
    selected_new_task_set_count = sum(
        1 for journey in selected_journeys if _journey_column_task_set(journey) not in existing_keys
    )
    selected_priority_task_set_count = sum(
        1 for journey in selected_journeys if is_priority_task_set(_journey_column_task_set(journey))
    )
    selected_support_changing_count = sum(
        1
        for objective, journey in selected
        if support_bucket(float(objective), journey) in {"new", "support"}
    )
    return _DiverseJourneySelection(
        journeys=selected_journeys,
        candidate_negative_count=int(raw_candidate_negative_count),
        selected_count=len(selected_journeys),
        task_set_dominance_enabled=bool(task_set_dominance_active),
        task_set_dominance_collapsed_count=int(task_set_dominance_collapsed_count),
        rejected_overlap_count=int(rejected_overlap),
        rejected_duplicate_task_set_count=int(rejected_duplicate_task_set),
        fallback_fill_count=int(fallback_fill),
        fallback_fill_new_mask_count=0,
        fallback_fill_replacement_count=0,
        fallback_fill_support_changing_count=0,
        fallback_fill_weak_replacement_count=0,
        candidate_new_task_set_count=int(candidate_new_task_set_count),
        selected_new_task_set_count=int(selected_new_task_set_count),
        selected_replacement_task_set_count=int(len(selected_journeys) - selected_new_task_set_count),
        candidate_priority_task_set_count=int(candidate_priority_task_set_count),
        selected_priority_task_set_count=int(selected_priority_task_set_count),
        candidate_support_changing_count=int(candidate_support_changing_count),
        selected_support_changing_count=int(selected_support_changing_count),
        selected_strong_replacement_count=int(selected_bucket_counts.get("strong_replacement", 0)),
        selected_weak_replacement_count=int(selected_bucket_counts.get("weak_replacement", 0)),
        mask_closure_candidate_task_set_count=int(len(closure_candidate_task_sets)),
        mask_closure_selected_count=int(len(selected_closure_signatures)),
        mask_closure_selected_task_set_count=int(len(selected_closure_task_sets)),
        best_true_rc=None if not scored else float(scored[0][0]),
        worst_selected_true_rc=None if not selected_rcs else max(selected_rcs),
        avg_pairwise_jaccard=_avg_pairwise_journey_task_jaccard(selected_journeys),
    )


# Keep the historical private name as a compatibility shim for existing tests
# and call sites; the selector implementation now lives in journey_harvesting.
_select_diverse_journey_candidates = _harvesting_select_diverse_journey_candidates


@dataclass(frozen=True, slots=True)
class _SortieProfile:
    sequence: tuple[int, ...]
    arc_options: tuple[ArcOption, ...]
    lower_start: float
    upper_start: float
    end_offset: float
    cost: float
    mask: int
    contribution: float


@dataclass
class _SortieProfileCatalogState:
    profiles: list[_SortieProfile]
    keys: set[tuple]
    generated: int = 0
    evaluated: int = 0
    next_size: int = 1
    next_permutation_index: int = 0
    exhausted: bool = False
    reason: str = ""


@dataclass
class _SortieLabelResumeState:
    labels_by_key: dict[tuple[int, int], list["_SortiePartialLabel"]]
    profiles_by_key: dict[tuple, _SortieProfile]
    heap: list[tuple[float, int, float, tuple[int, ...], int, "_SortiePartialLabel"]]
    active_label_ids: set[int]
    profiles_by_mask: dict[int, list[_SortieProfile]] | None = None
    serial: int = 0
    generated: int = 0
    evaluated: int = 0
    best_profile_rc: float | None = None
    exhausted: bool = False
    reason: str = ""
    online_dominance_pruned: int = 0
    profile_mask_cap_pruned: int = 0


@dataclass(frozen=True)
class SortieProfileCatalogSeedStats:
    enabled: bool
    skipped_no_cache: bool = False
    catalog_hit: bool = False
    journeys_seen: int = 0
    trips_seen: int = 0
    seeded_profiles: int = 0
    forced_seed_profiles: int = 0
    duplicate_or_dominated_profiles: int = 0
    skipped_missing_arc_option: int = 0
    skipped_invalid_trip: int = 0
    catalog_size_before: int = 0
    catalog_size_after: int = 0


@dataclass(frozen=True)
class _JourneyLabel:
    end_time: float
    value: float
    selected: tuple[tuple[int, float], ...]


@dataclass(frozen=True, slots=True)
class _SortiePartialLabel:
    sequence: tuple[int, ...]
    mask: int
    last: int
    partial: _PartialNoWaitingPathProfile


class _SortiePartialDominanceIndex:
    """Exact dominance scan accelerator for one ``(mask, last)`` bucket.

    The index never decides dominance by itself.  It only selects a necessary
    superset of labels that could dominate, or be dominated by, a candidate;
    every selected label is still checked by ``_dominates_sortie_partial_label``.
    """

    __slots__ = ("labels", "_travel_cost_entries", "_offset_entries")

    def __init__(self, labels: list["_SortiePartialLabel"]) -> None:
        self.labels = labels
        self._travel_cost_entries: list[tuple[float, int, "_SortiePartialLabel"]] = []
        self._offset_entries: list[tuple[float, int, "_SortiePartialLabel"]] = []
        self.rebuild()

    def rebuild(self) -> None:
        self._travel_cost_entries = sorted(
            (float(label.partial.travel_cost), id(label), label) for label in self.labels
        )
        self._offset_entries = sorted((float(label.partial.offset), id(label), label) for label in self.labels)

    def add(self, label: "_SortiePartialLabel") -> None:
        bisect.insort(self._travel_cost_entries, (float(label.partial.travel_cost), id(label), label))
        bisect.insort(self._offset_entries, (float(label.partial.offset), id(label), label))

    def labels_that_may_dominate(self, candidate: "_SortiePartialLabel") -> list["_SortiePartialLabel"]:
        eps = 1.0e-9
        cost_stop = bisect.bisect_right(
            self._travel_cost_entries,
            (float(candidate.partial.travel_cost) + eps, math.inf),
        )
        offset_stop = bisect.bisect_right(
            self._offset_entries,
            (float(candidate.partial.offset) + eps, math.inf),
        )
        if cost_stop <= offset_stop:
            return [entry[2] for entry in self._travel_cost_entries[:cost_stop]]
        return [entry[2] for entry in self._offset_entries[:offset_stop]]

    def labels_that_may_be_dominated_by(self, candidate: "_SortiePartialLabel") -> list["_SortiePartialLabel"]:
        eps = 1.0e-9
        cost_start = bisect.bisect_left(
            self._travel_cost_entries,
            (float(candidate.partial.travel_cost) - eps, -1),
        )
        offset_start = bisect.bisect_left(
            self._offset_entries,
            (float(candidate.partial.offset) - eps, -1),
        )
        cost_count = len(self._travel_cost_entries) - int(cost_start)
        offset_count = len(self._offset_entries) - int(offset_start)
        if cost_count <= offset_count:
            return [entry[2] for entry in self._travel_cost_entries[cost_start:]]
        return [entry[2] for entry in self._offset_entries[offset_start:]]


@dataclass(frozen=True, slots=True)
class _DirectJourneyLabel:
    end_time: float
    value: float
    mask: int
    trips: tuple[Any, ...]


@dataclass(frozen=True, slots=True)
class _DirectSortieSegment:
    sequence: tuple[int, ...]
    arc_options: tuple[ArcOption, ...]
    start_time: float
    end_time: float
    contribution: float
    mask: int

    @property
    def signature(self) -> tuple[tuple[int, ...], tuple[str, ...], float]:
        return (
            tuple(int(task) for task in self.sequence),
            tuple(option.option_id for option in self.arc_options),
            float(self.start_time),
        )


@dataclass(frozen=True, slots=True)
class _DirectNGJourneyLabel:
    ready_time: float
    value: float
    dssr_seen: frozenset[int]
    ng_memory: frozenset[int]
    visits: tuple[int, ...]
    completed: tuple[TimedTrip, ...]
    current: _SortiePartialLabel


@dataclass
class _DirectNGStats:
    iterations: int = 0
    memory_size: int = 0
    non_elementary_negative: int = 0
    label_pops: int = 0
    generated_labels: int = 0
    state_count: int = 0
    evaluated_timed_trips: int = 0
    dominance_pruned_labels: int = 0
    best_relaxed_reduced_cost: float | None = None


@dataclass
class _DirectNGIterationResult:
    journeys: list[JourneyColumn]
    exhausted: bool
    best_candidate_reduced_cost: float | None
    best_relaxed_reduced_cost: float | None
    stop_reason: str
    label_pops: int
    generated_labels: int
    state_count: int
    evaluated_timed_trips: int
    dominance_pruned_labels: int
    repeated_negative_tasks: set[int]


class _StreamingPricingStop(Exception):
    def __init__(self, result: JourneyPricingResult) -> None:
        super().__init__(result.reason)
        self.result = result


def _streaming_next_profile_count(
    current_profile_count: int,
    batch_size: int,
    no_result_streak: int,
    config: JourneyPricingConfig,
) -> int:
    """Return the next profile-count checkpoint for streaming journey DP.

    A streaming callback can be expensive because it solves the journey-level
    profile DP over the whole current catalog.  If several consecutive
    callbacks produce no returnable true-RC column batch, back off the next
    checkpoint.  This is worker-only scheduling: it never changes reduced costs
    and never turns a local no-column result into a certificate.
    """

    batch = max(1, int(batch_size))
    multiplier = 1
    if bool(config.streaming_callback_backoff_enabled):
        max_batches = max(1, int(config.streaming_callback_backoff_max_batches))
        shift = min(max(0, int(no_result_streak)), 20)
        multiplier = min(max_batches, 1 << shift)
    return int(current_profile_count) + batch * int(multiplier)


class _ProfileTimeFilterIndex:
    """Range index for `upper_start >= threshold` in original profile order."""

    def __init__(self, records: tuple[tuple[int, int, _SortieProfile], ...]) -> None:
        self.records = records
        self.count = len(records)
        size = 1
        while size < max(1, self.count):
            size <<= 1
        self.size = size
        self.max_upper_start = [-float("inf")] * (2 * size)
        for index, record in enumerate(records):
            self.max_upper_start[size + index] = float(record[2].upper_start)
        for index in range(size - 1, 0, -1):
            self.max_upper_start[index] = max(self.max_upper_start[index << 1], self.max_upper_start[(index << 1) | 1])

    def records_at_or_after(self, threshold: float) -> tuple[tuple[int, int, _SortieProfile], ...]:
        if self.count <= 0 or self.max_upper_start[1] < float(threshold):
            return tuple()
        selected: list[tuple[int, int, _SortieProfile]] = []
        stack: list[tuple[int, int, int]] = [(1, 0, self.size)]
        while stack:
            node, left, right = stack.pop()
            if self.max_upper_start[node] < float(threshold):
                continue
            if right - left == 1:
                if left < self.count:
                    selected.append(self.records[left])
                continue
            mid = (left + right) // 2
            # Push right first so the left child is consumed first and the
            # returned tuple preserves the existing profile-DP scan order.
            stack.append(((node << 1) | 1, mid, right))
            stack.append((node << 1, left, mid))
        return tuple(selected)


class _CompatibleProfileCache:
    def __init__(self, ordered_records: tuple[tuple[int, int, _SortieProfile], ...], *, task_count: int) -> None:
        self.ordered_records = ordered_records
        self.upper_start_records = tuple(
            sorted(
                ordered_records,
                key=lambda record: (
                    round(float(record[2].upper_start), 9),
                    record[0],
                    record[1],
                    record[2].sequence,
                ),
            )
        )
        self.upper_start_values = tuple(float(record[2].upper_start) for record in self.upper_start_records)
        self.enabled = int(task_count) <= 10
        self.requires_overlap_check = not self.enabled
        self.full_mask = (1 << int(task_count)) - 1 if self.enabled else 0
        self.by_profile_mask: dict[int, list[tuple[int, int, _SortieProfile]]] = {}
        self.by_used_mask: dict[int, tuple[tuple[int, int, _SortieProfile], ...]] = {}
        self.by_used_mask_time: dict[tuple[int, float], tuple[tuple[int, int, _SortieProfile], ...]] = {}
        self.by_used_mask_time_index: dict[int, _ProfileTimeFilterIndex] = {}
        self.full_time_index: _ProfileTimeFilterIndex | None = None
        if self.enabled:
            for record in ordered_records:
                self.by_profile_mask.setdefault(int(record[2].mask), []).append(record)

    def records(
        self,
        used_mask: int,
        *,
        min_upper_start: float | None = None,
    ) -> tuple[tuple[int, int, _SortieProfile], ...]:
        time_threshold = None if min_upper_start is None else float(min_upper_start) - 1.0e-9
        if not self.enabled:
            if time_threshold is None:
                return self.ordered_records
            if self.full_time_index is None:
                self.full_time_index = _ProfileTimeFilterIndex(self.ordered_records)
            return self.full_time_index.records_at_or_after(float(time_threshold))
        used_mask = int(used_mask)
        cached = self.by_used_mask.get(used_mask)
        if cached is not None:
            if time_threshold is None:
                return cached
            time_key = (used_mask, float(min_upper_start))
            timed = self.by_used_mask_time.get(time_key)
            if timed is None:
                index = self.by_used_mask_time_index.get(used_mask)
                if index is None:
                    index = _ProfileTimeFilterIndex(cached)
                    self.by_used_mask_time_index[used_mask] = index
                timed = index.records_at_or_after(float(time_threshold))
                self.by_used_mask_time[time_key] = timed
            return timed
        available = self.full_mask ^ used_mask
        records: list[tuple[int, int, _SortieProfile]] = []
        submask = available
        while submask:
            records.extend(self.by_profile_mask.get(submask, ()))
            submask = (submask - 1) & available
        records.sort(key=lambda record: record[0])
        cached = tuple(records)
        self.by_used_mask[used_mask] = cached
        if time_threshold is not None:
            time_key = (used_mask, float(min_upper_start))
            index = _ProfileTimeFilterIndex(cached)
            self.by_used_mask_time_index[used_mask] = index
            timed = index.records_at_or_after(float(time_threshold))
            self.by_used_mask_time[time_key] = timed
            return timed
        return cached


class _TaskSetReducedCostLowerBoundCache:
    """Safe task-set lower bound before order/path expansion.

    The bound minimizes travel cost over the task set using the cheapest logical
    option on each arc and ignores time and energy feasibility.  It is therefore
    optimistic for every feasible sortie over the same task set.  If this lower
    bound is already above the profile threshold, all permutations and path
    combinations for that task set can be skipped without losing a negative
    reduced-cost column.
    """

    def __init__(self, data: FutureData, duals: FutureDuals, vehicle: int, task_to_bit: dict[int, int]) -> None:
        self.data = data
        self.duals = duals
        self.vehicle = int(vehicle)
        self.task_by_bit = {int(bit): int(task) for task, bit in task_to_bit.items()}
        self.arc_cache: dict[tuple[int, int], float] = {}
        self.travel_cache: dict[tuple[int, int], float] = {}
        self.value_cache: dict[int, float] = {}

    def value(self, mask: int) -> float:
        mask = int(mask)
        cached = self.value_cache.get(mask)
        if cached is not None:
            return cached
        travel = self._travel(mask, 0)
        if travel == float("inf"):
            self.value_cache[mask] = float("inf")
            return float("inf")
        service = 0.0
        dual_sum = 0.0
        remaining = mask
        while remaining:
            bit = remaining & -remaining
            task = self.task_by_bit[bit.bit_length() - 1]
            service += float(self.data.task_value(task, "c_srv"))
            dual_sum += float(self.duals.cover.get(int(task), 0.0))
            dual_sum += float(self.duals.task_vehicle.get((int(task), int(self.vehicle)), 0.0))
            remaining ^= bit
        value = float(travel) + float(service) - float(dual_sum) - float(self.duals.sortie_count.get(int(self.vehicle), 0.0))
        self.value_cache[mask] = value
        return value

    def _travel(self, mask: int, current: int) -> float:
        key = (int(mask), int(current))
        cached = self.travel_cache.get(key)
        if cached is not None:
            return cached
        if int(mask) == 0:
            value = self._arc_cost_lb(int(current), 0)
            self.travel_cache[key] = value
            return value
        best = float("inf")
        remaining = int(mask)
        while remaining:
            bit = remaining & -remaining
            task = self.task_by_bit[bit.bit_length() - 1]
            arc = self._arc_cost_lb(int(current), int(task))
            if arc != float("inf"):
                tail = self._travel(int(mask) ^ bit, int(task))
                if tail != float("inf"):
                    best = min(best, float(arc) + float(tail))
            remaining ^= bit
        self.travel_cache[key] = best
        return best

    def _arc_cost_lb(self, origin: int, destination: int) -> float:
        key = (int(origin), int(destination))
        cached = self.arc_cache.get(key)
        if cached is not None:
            return cached
        options = self.data.options(int(origin), int(destination))
        if not options:
            value = float("inf")
        else:
            value = min(float(option.cost) for option in options)
        self.arc_cache[key] = value
        return value


class _TaskSetResourceLowerBoundCache:
    """Optimistic resource feasibility test for a task set.

    The cache uses the cheapest energy and time arcs independently, so the
    resulting closed-tour energy/time values are optimistic lower bounds for
    any concrete sortie over the same task set.  If even this optimistic
    closed tour violates capacity, battery, or horizon, no ordered path-option
    expansion for that task set can be feasible.
    """

    def __init__(self, data: FutureData, task_to_bit: dict[int, int], *, enabled: bool) -> None:
        self.data = data
        self.enabled = bool(enabled)
        self.task_by_bit = {int(bit): int(task) for task, bit in task_to_bit.items()}
        self.load_by_bit = {
            int(bit): float(data.task_value(int(task), "d"))
            for task, bit in task_to_bit.items()
        }
        self.service_time_by_bit = {
            int(bit): float(data.task_value(int(task), "sigma"))
            for task, bit in task_to_bit.items()
        }
        self.service_energy_by_bit = {
            int(bit): float(data.task_value(int(task), "g"))
            for task, bit in task_to_bit.items()
        }
        self.arc_energy_cache: dict[tuple[int, int], float] = {}
        self.arc_time_cache: dict[tuple[int, int], float] = {}
        self.travel_energy_cache: dict[tuple[int, int], float] = {}
        self.travel_time_cache: dict[tuple[int, int], float] = {}
        self.feasible_cache: dict[int, bool] = {}

    def maybe_feasible(self, mask: int) -> bool:
        if not self.enabled:
            return True
        mask = int(mask)
        if mask == 0:
            return True
        cached = self.feasible_cache.get(mask)
        if cached is not None:
            return bool(cached)
        load = 0.0
        service_energy = 0.0
        remaining = mask
        while remaining:
            bit = remaining & -remaining
            bit_index = bit.bit_length() - 1
            load += float(self.load_by_bit.get(bit_index, 0.0))
            service_energy += float(self.service_energy_by_bit.get(bit_index, 0.0))
            remaining ^= bit
        if load > float(self.data.capacity) + 1.0e-9:
            self.feasible_cache[mask] = False
            return False
        energy_lb = self._travel_energy(mask, 0)
        time_lb = self._travel_time(mask, 0)
        if energy_lb == float("inf") or time_lb == float("inf"):
            self.feasible_cache[mask] = False
            return False
        total_energy_lb = float(energy_lb) + float(service_energy) + float(self.data.survival_energy_rate) * float(time_lb)
        if total_energy_lb > float(self.data.energy_limit) + 1.0e-9:
            self.feasible_cache[mask] = False
            return False
        recharge_lb = float(total_energy_lb) / max(1.0e-9, float(self.data.rho))
        feasible = float(time_lb) + float(recharge_lb) <= float(self.data.horizon) + 1.0e-9
        self.feasible_cache[mask] = bool(feasible)
        return bool(feasible)

    def _travel_energy(self, mask: int, current: int) -> float:
        key = (int(mask), int(current))
        cached = self.travel_energy_cache.get(key)
        if cached is not None:
            return cached
        if int(mask) == 0:
            value = self._arc_energy_lb(int(current), 0)
            self.travel_energy_cache[key] = value
            return value
        best = float("inf")
        remaining = int(mask)
        while remaining:
            bit = remaining & -remaining
            task = self.task_by_bit[bit.bit_length() - 1]
            arc = self._arc_energy_lb(int(current), int(task))
            if arc != float("inf"):
                tail = self._travel_energy(int(mask) ^ bit, int(task))
                if tail != float("inf"):
                    best = min(best, float(arc) + float(tail))
            remaining ^= bit
        self.travel_energy_cache[key] = best
        return best

    def _travel_time(self, mask: int, current: int) -> float:
        key = (int(mask), int(current))
        cached = self.travel_time_cache.get(key)
        if cached is not None:
            return cached
        if int(mask) == 0:
            value = self._arc_time_lb(int(current), 0)
            self.travel_time_cache[key] = value
            return value
        best = float("inf")
        remaining = int(mask)
        while remaining:
            bit = remaining & -remaining
            bit_index = bit.bit_length() - 1
            task = self.task_by_bit[bit_index]
            arc = self._arc_time_lb(int(current), int(task))
            if arc != float("inf"):
                tail = self._travel_time(int(mask) ^ bit, int(task))
                if tail != float("inf"):
                    best = min(best, float(arc) + float(self.service_time_by_bit.get(bit_index, 0.0)) + float(tail))
            remaining ^= bit
        self.travel_time_cache[key] = best
        return best

    def _arc_energy_lb(self, origin: int, destination: int) -> float:
        key = (int(origin), int(destination))
        cached = self.arc_energy_cache.get(key)
        if cached is not None:
            return cached
        options = self.data.options(int(origin), int(destination))
        value = float("inf") if not options else min(float(option.energy) for option in options)
        self.arc_energy_cache[key] = value
        return value

    def _arc_time_lb(self, origin: int, destination: int) -> float:
        key = (int(origin), int(destination))
        cached = self.arc_time_cache.get(key)
        if cached is not None:
            return cached
        options = self.data.options(int(origin), int(destination))
        value = float("inf") if not options else min(float(option.tau) for option in options)
        self.arc_time_cache[key] = value
        return value


def _task_set_resource_cache_key(data: FutureData, task_to_bit: dict[int, int]) -> tuple:
    return (
        "task_set_resource_lower_bound_v1",
        str(data.instance_path),
        tuple(sorted((int(task), int(bit)) for task, bit in task_to_bit.items())),
        round(float(data.capacity), 9),
        round(float(data.energy_limit), 9),
        round(float(data.horizon), 9),
        round(float(data.rho), 9),
        round(float(data.survival_energy_rate), 9),
    )


def _get_task_set_resource_lower_bound_cache(
    data: FutureData,
    task_to_bit: dict[int, int],
    *,
    enabled: bool,
    resource_cache: dict[tuple, Any] | None,
) -> _TaskSetResourceLowerBoundCache:
    if not bool(enabled):
        return _TaskSetResourceLowerBoundCache(data, task_to_bit, enabled=False)
    if resource_cache is None:
        return _TaskSetResourceLowerBoundCache(data, task_to_bit, enabled=True)
    key = _task_set_resource_cache_key(data, task_to_bit)
    cached = resource_cache.get(key)
    if isinstance(cached, _TaskSetResourceLowerBoundCache):
        return cached
    cache = _TaskSetResourceLowerBoundCache(data, task_to_bit, enabled=True)
    resource_cache[key] = cache
    return cache


class _PartialSortieProfileLowerBoundCache:
    """Optimistic continuation bound for a partial sortie label.

    The bound uses cheapest arc costs and ignores time/energy feasibility for
    future tasks.  It is therefore no larger than the best feasible completion
    contribution.  If it is already above the profile threshold, no descendant
    of the partial label can produce a useful sortie profile.
    """

    def __init__(self, data: FutureData, duals: FutureDuals, vehicle: int, task_to_bit: dict[int, int], *, enabled: bool) -> None:
        self.data = data
        self.duals = duals
        self.vehicle = int(vehicle)
        self.enabled = bool(enabled)
        self.task_by_bit = {int(bit): int(task) for task, bit in task_to_bit.items()}
        self.full_mask = 0
        for bit in self.task_by_bit:
            self.full_mask |= 1 << int(bit)
        self.arc_cache: dict[tuple[int, int], float] = {}
        self.tail_cache: dict[tuple[int, int, int], float] = {}

    def value(self, label: _SortiePartialLabel, remaining_slots: int) -> float:
        if not self.enabled:
            return -float("inf")
        current = self._partial_contribution(label)
        if current == float("inf"):
            return float("inf")
        available_mask = self.full_mask & ~int(label.mask)
        tail = self._tail(int(label.last), int(available_mask), max(0, int(remaining_slots)))
        if tail == float("inf"):
            return float("inf")
        return float(current) + float(tail)

    def _partial_contribution(self, label: _SortiePartialLabel) -> float:
        dual_sum = 0.0
        for task in set(label.sequence):
            task = int(task)
            dual_sum += float(self.duals.cover.get(task, 0.0))
            dual_sum += float(self.duals.task_vehicle.get((task, int(self.vehicle)), 0.0))
        return float(label.partial.travel_cost) + float(label.partial.service_cost) - float(dual_sum)

    def _tail(self, current: int, available_mask: int, remaining_slots: int) -> float:
        key = (int(current), int(available_mask), int(remaining_slots))
        cached = self.tail_cache.get(key)
        if cached is not None:
            return cached
        best = self._arc_cost_lb(int(current), 0)
        if int(remaining_slots) > 0:
            remaining = int(available_mask)
            while remaining:
                bit = remaining & -remaining
                bit_index = bit.bit_length() - 1
                task = self.task_by_bit[bit_index]
                arc = self._arc_cost_lb(int(current), int(task))
                if arc != float("inf"):
                    dual = float(self.duals.cover.get(int(task), 0.0))
                    dual += float(self.duals.task_vehicle.get((int(task), int(self.vehicle)), 0.0))
                    service = float(self.data.task_value(int(task), "c_srv"))
                    tail = self._tail(int(task), int(available_mask) ^ bit, int(remaining_slots) - 1)
                    if tail != float("inf"):
                        best = min(best, float(arc) + float(service) - float(dual) + float(tail))
                remaining ^= bit
        self.tail_cache[key] = best
        return best

    def _arc_cost_lb(self, origin: int, destination: int) -> float:
        key = (int(origin), int(destination))
        cached = self.arc_cache.get(key)
        if cached is not None:
            return cached
        options = self.data.options(int(origin), int(destination))
        value = float("inf") if not options else min(float(option.cost) for option in options)
        self.arc_cache[key] = value
        return value


class _OptimisticProfileBoundCache:
    """Safe lower bound on extra profile contribution for DP label pruning.

    It ignores time compatibility and mutual overlap among future profiles, so
    the value can only be more optimistic than a real continuation.  That makes
    it safe for proving that a label cannot lead to a negative journey.
    """

    def __init__(self, compatible_profile_cache: _CompatibleProfileCache) -> None:
        self.compatible_profile_cache = compatible_profile_cache
        self.cache: dict[tuple[int, int], float] = {}

    def value(self, used_mask: int, remaining_count: int) -> float:
        remaining_count = int(remaining_count)
        if remaining_count <= 0:
            return 0.0
        key = (int(used_mask), remaining_count)
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        values = [
            float(profile.contribution)
            for _position, _profile_index, profile in self.compatible_profile_cache.records(int(used_mask))
            if float(profile.contribution) < 0.0
        ]
        if not values:
            self.cache[key] = 0.0
            return 0.0
        values.sort()
        bound = float(sum(values[:remaining_count]))
        self.cache[key] = bound
        return bound


class _DisjointProfileBoundCache:
    """Safe lower bound using only task-disjoint future profile masks.

    The bound ignores timing and ordering, so it is still optimistic for the
    true continuation.  Unlike ``_OptimisticProfileBoundCache``, it respects
    task-mask disjointness among the remaining profiles, which makes the lower
    bound much tighter on degenerate pools with many profiles over the same
    tasks.
    """

    def __init__(self, ordered_records: tuple[tuple[int, int, _SortieProfile], ...], *, task_count: int, enabled: bool) -> None:
        self.enabled = bool(enabled) and int(task_count) <= 20
        self.task_count = int(task_count)
        self.full_mask = (1 << int(task_count)) - 1 if self.enabled else 0
        self.dp_by_count: list[list[float]] = []
        if not self.enabled:
            return
        size = self.full_mask + 1
        best_by_mask = [float("inf")] * size
        for _position, _profile_index, profile in ordered_records:
            mask = int(profile.mask)
            if mask <= 0 or mask > self.full_mask:
                continue
            contribution = float(profile.contribution)
            if contribution < best_by_mask[mask]:
                best_by_mask[mask] = contribution
        active_masks = [mask for mask, value in enumerate(best_by_mask) if mask > 0 and value < 0.0]
        previous = [0.0] * size
        self.dp_by_count = [previous]
        max_count = int(task_count)
        for _count in range(1, max_count + 1):
            current = previous[:]
            for mask in range(size):
                best = current[mask]
                for profile_mask in active_masks:
                    if profile_mask & mask != profile_mask:
                        continue
                    candidate = best_by_mask[profile_mask] + previous[mask ^ profile_mask]
                    if candidate < best:
                        best = candidate
                current[mask] = best
            self.dp_by_count.append(current)
            previous = current

    def value(self, used_mask: int, remaining_count: int) -> float | None:
        if not self.enabled or not self.dp_by_count:
            return None
        count = max(0, min(int(remaining_count), len(self.dp_by_count) - 1))
        available = self.full_mask ^ int(used_mask)
        if available < 0 or available > self.full_mask:
            return None
        return float(self.dp_by_count[count][available])


class _TaskSetContinuationLowerBoundCache:
    """Optimistic lower bound for future direct-journey labels.

    It combines task-set sortie lower bounds over disjoint remaining task
    subsets and ignores timing/order compatibility.  The result is therefore a
    lower bound on the best possible continuation; if even this optimistic
    value cannot make the label negative, the label is safe to prune.
    """

    def __init__(
        self,
        task_set_cache: _TaskSetReducedCostLowerBoundCache,
        *,
        task_count: int,
        max_tasks_per_sortie: int,
        enabled: bool,
    ) -> None:
        self.task_set_cache = task_set_cache
        self.task_count = int(task_count)
        self.max_tasks_per_sortie = max(1, int(max_tasks_per_sortie))
        self.enabled = bool(enabled)
        self.full_mask = (1 << int(task_count)) - 1 if self.enabled else 0
        self.cache: dict[tuple[int, int], float] = {}

    def value(self, used_mask: int, remaining_count: int) -> float | None:
        if not self.enabled:
            return None
        available = self.full_mask ^ int(used_mask)
        if available < 0 or available > self.full_mask:
            return None
        return self._value(int(available), int(remaining_count))

    def _value(self, available: int, remaining_count: int) -> float:
        if int(available) == 0 or int(remaining_count) <= 0:
            return 0.0
        key = (int(available), int(remaining_count))
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        best = 0.0
        submask = int(available)
        while submask:
            if int(submask).bit_count() <= self.max_tasks_per_sortie:
                sortie_lb = self.task_set_cache.value(int(submask))
                if sortie_lb < 0.0:
                    tail = self._value(int(available) ^ int(submask), int(remaining_count) - 1)
                    best = min(best, float(sortie_lb) + float(tail))
            submask = (submask - 1) & int(available)
        self.cache[key] = best
        return best


@dataclass(frozen=True)
class _TwoCycleCompletionLabel:
    cost: float
    prev_in_dp: int


@dataclass(frozen=True)
class _ArcCompletionOption:
    cost: float
    time: float
    energy: float


class _DirectJourneyCompletionBound:
    """Coarse optimistic suffix lower bound for direct journey labeling.

    The table is rebuilt for the current true-dual pricing call.  It only uses
    task-cover duals and directed physical arc options.  Task uniqueness is
    relaxed, and time/energy are represented by coarse optimistic buckets, so
    every table value is intentionally optimistic: if this lower bound still
    cannot make a partial journey negative, pruning that label is exact-safe.
    """

    def __init__(
        self,
        data: FutureData,
        duals: JourneyDuals,
        *,
        time_buckets: int,
        energy_buckets: int,
        max_tasks_per_sortie: int,
        sortie_limit: int,
        two_cycle_enabled: bool = False,
        two_cycle_max_states: int = 0,
        deadline: float | None = None,
    ) -> None:
        started = time.perf_counter()
        self.deadline = None if deadline is None else float(deadline)
        self.enabled = True
        self.horizon = max(0.0, float(data.horizon))
        self.bucket_count = max(1, int(time_buckets))
        self.bucket_width = self.horizon / float(self.bucket_count) if self.horizon > 0.0 else 1.0
        self.energy_limit = max(0.0, float(data.energy_limit))
        self.energy_bucket_count = max(0, int(energy_buckets))
        self.energy_bucket_width = (
            self.energy_limit / float(self.energy_bucket_count)
            if self.energy_bucket_count > 0 and self.energy_limit > 0.0
            else 1.0
        )
        self.rho = max(1.0e-9, float(data.rho))
        self.survival_energy_rate = max(0.0, float(data.survival_energy_rate))
        self.sortie_limit = max(0, int(sortie_limit))
        self.max_tasks_per_sortie = max(1, int(max_tasks_per_sortie))
        self.node_values: dict[int, list[list[float]]] = {}
        self.two_cycle_enabled = bool(two_cycle_enabled)
        self.two_cycle_max_states = max(0, int(two_cycle_max_states))
        self.two_cycle_values: dict[tuple[int, int, int, int, int], tuple[_TwoCycleCompletionLabel, ...]] = {}
        self.two_cycle_table_complete = False
        self.two_cycle_fallback_to_memoryless = False
        self.two_cycle_state_count = 0
        self.two_cycle_blocked_extensions = 0
        self.two_cycle_second_best_queries = 0
        self.two_cycle_incompatible_queries = 0
        self.two_cycle_top2_replacements = 0
        self.two_cycle_build_time = 0.0
        self.table_complete = True
        self.future_sortie_floor = 0.0
        self.build_time = 0.0
        self.state_count = 0
        self.lb_min_value: float | None = None
        self.lb_mean_value: float | None = None
        self.lb_negative_state_count = 0

        self.arc_options = self._directed_arc_lower_bounds(data)
        # Completion-bound 构表会在 memoryless 表与 two-cycle 表中反复查询
        # 同一个粗资源状态下的物理弧候选。缓存仅绑定当前 bound 实例，
        # 因此不会跨 dual / branch / config 泄漏，只消除本次构表内的重复枚举。
        self._return_completion_cache: dict[tuple[int, float, float], tuple[tuple[float, float], ...]] = {}
        self._task_transition_cache: dict[tuple[int, int, int, float, float], tuple[tuple[int, int, float], ...]] = {}
        self.service_time = {int(task): float(data.task_value(int(task), "sigma")) for task in data.tasks}
        self.service_cost = {int(task): float(data.task_value(int(task), "c_srv")) for task in data.tasks}
        self.service_energy = {int(task): float(data.task_value(int(task), "g")) for task in data.tasks}
        self.ready_time = {int(task): float(data.task_value(int(task), "r")) for task in data.tasks}
        self.due_arrival = {
            int(task): float(data.task_value(int(task), "D")) - float(data.task_value(int(task), "sigma"))
            for task in data.tasks
        }
        self.task_reward = {int(task): float(duals.cover.get(int(task), 0.0)) for task in data.tasks}
        self.tasks = tuple(int(task) for task in data.tasks)
        self.nodes = (0, *self.tasks)
        self.node_values = self._build_node_time_energy_values()
        depot_values = self.node_values.get(0, [])
        finite_depot_values = [
            float(value)
            for row in depot_values
            for value in row
            if math.isfinite(float(value))
        ]
        self.future_sortie_floor = min(0.0, min(finite_depot_values)) if finite_depot_values else 0.0

        flat_values = [
            float(value)
            for table in self.node_values.values()
            for row in table
            for value in row
            if math.isfinite(float(value))
        ]
        self.lb_min_value = min(flat_values) if flat_values else None
        self.lb_mean_value = (sum(flat_values) / float(len(flat_values))) if flat_values else None
        self.lb_negative_state_count = sum(1 for value in flat_values if value < 0.0)
        if self.enabled and self.two_cycle_enabled:
            self._build_two_cycle_values()
        self.build_time = time.perf_counter() - started

    def _deadline_exceeded(self) -> bool:
        return self.deadline is not None and time.perf_counter() > float(self.deadline)

    def value(self, remaining_sorties: int, end_time: float) -> float:
        remaining = max(0, int(remaining_sorties))
        if remaining <= 0:
            return 0.0
        # Future sorties are optional: a journey can stop after the current
        # completed sortie.  The suffix bound is therefore at most 0.  The first
        # remaining sortie, however, cannot start before the current journey
        # end time.  Using the depot bucket for that first sortie is still an
        # optimistic relaxation, but is much tighter than multiplying the
        # globally best depot floor by the number of remaining sorties.
        if float(end_time) > float(self.horizon) + 1.0e-9:
            return 0.0
        if self.two_cycle_table_complete:
            first_suffix = self._two_cycle_partial_value(
                0,
                0,
                self.max_tasks_per_sortie,
                remaining - 1,
                float(end_time),
                0.0,
            )
        else:
            table = self.node_values.get(0)
            if table is None:
                return 0.0
            first_suffix = float(table[self._bucket_of_time(float(end_time))][0])
            if math.isfinite(first_suffix):
                first_suffix += float(remaining - 1) * float(self.future_sortie_floor)
        if not math.isfinite(float(first_suffix)):
            return 0.0
        return min(0.0, float(first_suffix))

    def _bucket_delta(self, duration: float) -> int:
        if float(duration) <= 1.0e-12:
            return 0
        return max(1, int(math.ceil(float(duration) / float(self.bucket_width) - 1.0e-12)))

    def _bucket_of_time(self, value: float) -> int:
        if self.horizon <= 0.0:
            return 0
        bounded = max(0.0, min(float(value), self.horizon))
        return max(0, min(self.bucket_count, int(math.floor(bounded / float(self.bucket_width)))))

    def _bucket_time(self, bucket: int) -> float:
        return max(0.0, min(float(self.horizon), float(bucket) * float(self.bucket_width)))

    def _bucket_of_energy(self, value: float) -> int:
        if self.energy_bucket_count <= 0 or self.energy_limit <= 0.0:
            return 0
        bounded = max(0.0, min(float(value), self.energy_limit))
        return max(0, min(self.energy_bucket_count, int(math.floor(bounded / float(self.energy_bucket_width)))))

    def _bucket_energy(self, bucket: int) -> float:
        if self.energy_bucket_count <= 0:
            return 0.0
        return max(0.0, min(float(self.energy_limit), float(bucket) * float(self.energy_bucket_width)))

    def _time_after_return(self, depart_time: float, return_time: float, energy_used: float, return_energy: float) -> float:
        # 这里使用能量桶下界、定向返仓弧的最小能耗和返仓行驶期间
        # 必然产生的 survival 能耗来估计最小充电时间。
        # 该值不超过任何真实完成路径的返仓+充电时间，因此仍是乐观下界。
        survival_lb = float(self.survival_energy_rate) * max(0.0, float(return_time))
        total_energy_lb = max(0.0, float(energy_used) + float(return_energy) + float(survival_lb))
        recharge_lb = total_energy_lb / float(self.rho)
        return float(depart_time) + float(return_time) + float(recharge_lb)

    @staticmethod
    def _directed_arc_lower_bounds(
        data: FutureData,
    ) -> dict[tuple[int, int], tuple[_ArcCompletionOption, ...]]:
        arcs: dict[tuple[int, int], tuple[_ArcCompletionOption, ...]] = {}
        nodes = (0, *tuple(int(task) for task in data.tasks))
        for i in nodes:
            for j in nodes:
                if int(i) == int(j):
                    continue
                options = data.options(int(i), int(j))
                if not options:
                    continue
                candidates = tuple(
                    _ArcCompletionOption(
                        cost=float(option.cost),
                        time=float(option.tau),
                        energy=float(option.energy),
                    )
                    for option in options
                )
                kept: list[_ArcCompletionOption] = []
                for candidate in sorted(candidates, key=lambda item: (item.cost, item.time, item.energy)):
                    dominated = any(
                        other.cost <= candidate.cost + 1.0e-12
                        and other.time <= candidate.time + 1.0e-12
                        and other.energy <= candidate.energy + 1.0e-12
                        for other in kept
                    )
                    if dominated:
                        continue
                    kept = [
                        other
                        for other in kept
                        if not (
                            candidate.cost <= other.cost + 1.0e-12
                            and candidate.time <= other.time + 1.0e-12
                            and candidate.energy <= other.energy + 1.0e-12
                        )
                    ]
                    kept.append(candidate)
                arcs[(int(i), int(j))] = tuple(kept)
        return arcs

    def _build_node_time_energy_values(self) -> dict[int, list[list[float]]]:
        energy_states = self.energy_bucket_count + 1 if self.energy_bucket_count > 0 else 1
        values: dict[int, list[list[float]]] = {
            int(node): [[float("inf")] * energy_states for _ in range(self.bucket_count + 1)]
            for node in self.nodes
        }
        for time_bucket in range(self.bucket_count, -1, -1):
            for energy_bucket in range(energy_states - 1, -1, -1):
                depart_time = self._bucket_time(int(time_bucket))
                energy_used = self._bucket_energy(int(energy_bucket))
                for node in self.nodes:
                    if self._deadline_exceeded():
                        self.table_complete = False
                        self.enabled = False
                        return {}
                    self.state_count += 1
                    best = self._return_arc_completion_value(
                        int(node),
                        depart_time=depart_time,
                        energy_used=energy_used,
                    )
                    for task in self.tasks:
                        if int(task) == int(node):
                            continue
                        for transition in self._task_transitions(
                            int(node),
                            int(task),
                            time_bucket=int(time_bucket),
                            depart_time=depart_time,
                            energy_used=energy_used,
                        ):
                            next_time_bucket, next_energy_bucket, transition_value = transition
                            tail = values[int(task)][int(next_time_bucket)][int(next_energy_bucket)]
                            if not math.isfinite(float(tail)):
                                continue
                            candidate = float(transition_value) + float(tail)
                            if candidate < best:
                                best = candidate
                    values[int(node)][int(time_bucket)][int(energy_bucket)] = float(best)
        return values

    def _build_two_cycle_values(self) -> None:
        started = time.perf_counter()
        energy_states = self.energy_bucket_count + 1 if self.energy_bucket_count > 0 else 1
        values: dict[tuple[int, int, int, int, int], tuple[_TwoCycleCompletionLabel, ...]] = {}
        complete = True
        for slots in range(0, self.max_tasks_per_sortie + 1):
            for future_sorties in range(0, self.sortie_limit + 1):
                for time_bucket in range(self.bucket_count, -1, -1):
                    depart_time = self._bucket_time(int(time_bucket))
                    for energy_bucket in range(energy_states - 1, -1, -1):
                        energy_used = self._bucket_energy(int(energy_bucket))
                        for node in self.nodes:
                            if self._deadline_exceeded():
                                complete = False
                                break
                            self.two_cycle_state_count += 1
                            if (
                                self.two_cycle_max_states > 0
                                and self.two_cycle_state_count > self.two_cycle_max_states
                            ):
                                complete = False
                                break
                            labels: tuple[_TwoCycleCompletionLabel, ...] = tuple()
                            for return_cost, return_ready_time in self._return_arc_completion_candidates(
                                int(node),
                                depart_time=depart_time,
                                energy_used=energy_used,
                            ):
                                labels = self._insert_two_cycle_label(
                                    labels,
                                    _TwoCycleCompletionLabel(
                                        cost=float(return_cost)
                                        + self._future_sortie_suffix_value(
                                            int(future_sorties),
                                            float(return_ready_time),
                                        ),
                                        prev_in_dp=0,
                                    ),
                                )
                            if int(slots) > 0:
                                for task in self.tasks:
                                    if int(task) == int(node):
                                        continue
                                    for transition in self._task_transitions(
                                        int(node),
                                        int(task),
                                        time_bucket=int(time_bucket),
                                        depart_time=depart_time,
                                        energy_used=energy_used,
                                    ):
                                        next_time_bucket, next_energy_bucket, transition_value = transition
                                        suffix_key = (
                                            int(task),
                                            int(next_time_bucket),
                                            int(next_energy_bucket),
                                            int(future_sorties),
                                            int(slots) - 1,
                                        )
                                        suffix_labels = values.get(suffix_key, tuple())
                                        for suffix in suffix_labels:
                                            if (
                                                int(node) != 0
                                                and int(task) != 0
                                                and int(node) == int(suffix.prev_in_dp)
                                            ):
                                                self.two_cycle_blocked_extensions += 1
                                                continue
                                            labels = self._insert_two_cycle_label(
                                                labels,
                                                _TwoCycleCompletionLabel(
                                                    cost=float(transition_value) + float(suffix.cost),
                                                    prev_in_dp=int(task),
                                                ),
                                            )
                            values[(int(node), int(time_bucket), int(energy_bucket), int(future_sorties), int(slots))] = labels
                        if not complete:
                            break
                    if not complete:
                        break
                if not complete:
                    break
            if not complete:
                break
        self.two_cycle_build_time = time.perf_counter() - started
        if complete:
            self.two_cycle_values = values
            self.two_cycle_table_complete = True
            self.two_cycle_fallback_to_memoryless = False
        else:
            self.two_cycle_values = {}
            self.two_cycle_table_complete = False
            self.two_cycle_fallback_to_memoryless = True

    def _insert_two_cycle_label(
        self,
        labels: tuple[_TwoCycleCompletionLabel, ...],
        new_label: _TwoCycleCompletionLabel,
    ) -> tuple[_TwoCycleCompletionLabel, ...]:
        current = list(labels)
        for index, label in enumerate(current):
            if int(label.prev_in_dp) != int(new_label.prev_in_dp):
                continue
            if float(new_label.cost) < float(label.cost):
                current[index] = new_label
                self.two_cycle_top2_replacements += 1
            current.sort(key=lambda item: (float(item.cost), int(item.prev_in_dp)))
            return tuple(current[:2])
        if len(current) < 2:
            current.append(new_label)
            current.sort(key=lambda item: (float(item.cost), int(item.prev_in_dp)))
            return tuple(current)
        worst_index = max(range(len(current)), key=lambda idx: (float(current[idx].cost), int(current[idx].prev_in_dp)))
        if float(new_label.cost) < float(current[worst_index].cost):
            current[worst_index] = new_label
            self.two_cycle_top2_replacements += 1
            current.sort(key=lambda item: (float(item.cost), int(item.prev_in_dp)))
            return tuple(current[:2])
        return tuple(current)

    def _future_sortie_suffix_value(self, future_sorties: int, ready_time: float) -> float:
        future = max(0, int(future_sorties))
        if future <= 0:
            return 0.0
        table = self.node_values.get(0)
        if table is None:
            return 0.0
        first_suffix = float(table[self._bucket_of_time(float(ready_time))][0])
        if not math.isfinite(float(first_suffix)):
            return 0.0
        if future > 1:
            first_suffix += float(future - 1) * float(self.future_sortie_floor)
        return min(0.0, float(first_suffix))

    def _return_arc_completion_candidates(
        self,
        node: int,
        *,
        depart_time: float,
        energy_used: float,
    ) -> tuple[tuple[float, float], ...]:
        key = (int(node), float(depart_time), float(energy_used))
        cached = self._return_completion_cache.get(key)
        if cached is not None:
            return cached
        if int(node) == 0:
            result = ((0.0, float(depart_time)),)
            self._return_completion_cache[key] = result
            return result
        candidates: list[tuple[float, float]] = []
        for option in self.arc_options.get((int(node), 0), tuple()):
            survival_lb = float(self.survival_energy_rate) * max(0.0, float(option.time))
            total_energy = float(energy_used) + float(option.energy) + float(survival_lb)
            if self.energy_bucket_count > 0 and total_energy > self.energy_limit + 1.0e-9:
                continue
            end_time = self._time_after_return(
                float(depart_time),
                float(option.time),
                float(energy_used),
                float(option.energy),
            )
            if end_time > self.horizon + 1.0e-9:
                continue
            candidates.append((float(option.cost), float(end_time)))
        result = tuple(candidates)
        self._return_completion_cache[key] = result
        return result

    def _return_arc_completion_value(self, node: int, *, depart_time: float, energy_used: float) -> float:
        candidates = self._return_arc_completion_candidates(
            int(node),
            depart_time=float(depart_time),
            energy_used=float(energy_used),
        )
        if not candidates:
            return float("inf")
        return min(float(cost) for cost, _end_time in candidates)

    def _task_transitions(
        self,
        node: int,
        task: int,
        *,
        time_bucket: int,
        depart_time: float,
        energy_used: float,
    ) -> tuple[tuple[int, int, float], ...]:
        key = (int(node), int(task), int(time_bucket), float(depart_time), float(energy_used))
        cached = self._task_transition_cache.get(key)
        if cached is not None:
            return cached
        transitions: list[tuple[int, int, float]] = []
        for option in self.arc_options.get((int(node), int(task)), tuple()):
            arrival_time = float(depart_time) + float(option.time)
            # 反向 completion bound 允许 no-wait 实例在界里“等待”，这是一个
            # 合法松弛；但服务不可能早于 ready time 开始。把 ready time 纳入
            # 粗时间桶能显著收紧强时间窗场景的 suffix 下界。
            service_start = max(float(arrival_time), float(self.ready_time[int(task)]))
            if service_start > self.due_arrival[int(task)] + 1.0e-9:
                continue
            # Survival energy is charged over physical travel/service duration.
            # Waiting induced by the coarse ready-time relaxation is not counted,
            # keeping the resource state optimistic and proof-safe.
            survival_lb = float(self.survival_energy_rate) * (
                max(0.0, float(option.time)) + max(0.0, float(self.service_time[int(task)]))
            )
            next_energy = (
                float(energy_used)
                + float(option.energy)
                + self.service_energy[int(task)]
                + float(survival_lb)
            )
            if self.energy_bucket_count > 0 and next_energy > self.energy_limit + 1.0e-9:
                continue
            next_time_bucket = self._bucket_of_time(float(service_start) + self.service_time[int(task)])
            if next_time_bucket > self.bucket_count:
                continue
            next_energy_bucket = self._bucket_of_energy(float(next_energy))
            transition_value = float(option.cost) + self.service_cost[int(task)] - self.task_reward[int(task)]
            transitions.append((int(next_time_bucket), int(next_energy_bucket), float(transition_value)))
        result = tuple(transitions)
        self._task_transition_cache[key] = result
        return result

    def partial_value(
        self,
        last: int,
        previous: int,
        remaining_slots_in_sortie: int,
        future_sorties: int,
        current_time: float,
        current_energy: float,
    ) -> float:
        if self.two_cycle_table_complete:
            return self._two_cycle_partial_value(
                int(last),
                int(previous),
                int(remaining_slots_in_sortie),
                int(future_sorties),
                float(current_time),
                float(current_energy),
            )
        bucket = self._bucket_of_time(float(current_time))
        energy_bucket = self._bucket_of_energy(float(current_energy))
        table = self.node_values.get(int(last))
        if table is None:
            return float("inf")
        current_sortie_lb = float(table[int(bucket)][int(energy_bucket)])
        if not math.isfinite(current_sortie_lb):
            return float("inf")
        return float(current_sortie_lb) + float(max(0, int(future_sorties))) * float(self.future_sortie_floor)

    def _two_cycle_partial_value(
        self,
        last: int,
        previous: int,
        remaining_slots_in_sortie: int,
        future_sorties: int,
        current_time: float,
        current_energy: float,
    ) -> float:
        key = (
            int(last),
            self._bucket_of_time(float(current_time)),
            self._bucket_of_energy(float(current_energy)),
            max(0, min(int(future_sorties), self.sortie_limit)),
            max(0, min(int(remaining_slots_in_sortie), self.max_tasks_per_sortie)),
        )
        labels = self.two_cycle_values.get(key, tuple())
        if not labels:
            return float("inf")
        for index, label in enumerate(labels):
            if int(previous) != 0 and int(last) != 0 and int(label.prev_in_dp) == int(previous):
                self.two_cycle_incompatible_queries += 1
                continue
            if index > 0:
                self.two_cycle_second_best_queries += 1
            return float(label.cost)
        return float("inf")


def _direct_completion_bound_cache_key(
    data: FutureData,
    duals: JourneyDuals,
    config: JourneyPricingConfig,
) -> tuple:
    max_tasks_per_sortie = _max_tasks_per_trip(data, int(config.max_tasks_per_trip))
    return (
        "direct_journey_completion_bound_v2",
        id(data),
        str(getattr(data, "instance_path", "")),
        tuple(int(task) for task in data.tasks),
        int(data.sortie_limit),
        round(float(data.horizon), 9),
        round(float(data.energy_limit), 9),
        round(float(data.rho), 9),
        round(float(data.survival_energy_rate), 9),
        int(max_tasks_per_sortie),
        int(config.direct_journey_label_completion_bound_time_buckets),
        int(config.direct_journey_label_completion_bound_energy_buckets),
        bool(config.direct_journey_label_completion_bound_two_cycle_enabled),
        int(config.direct_journey_label_completion_bound_two_cycle_max_states),
        # The completion-bound table uses task-cover rewards and physical
        # resources only. Fleet duals are applied outside the suffix table in
        # the journey objective, so including them here creates needless cache
        # misses without changing the bound.
        tuple(sorted((int(task), round(float(value), 12)) for task, value in duals.cover.items())),
    )


def _direct_completion_bound_cacheable(bound: _DirectJourneyCompletionBound) -> bool:
    if not bool(getattr(bound, "enabled", True)) or not bool(getattr(bound, "table_complete", True)):
        return False
    if not bool(bound.two_cycle_enabled):
        return True
    # Two-cycle tables are only reusable when fully built.  A fallback table is
    # safe but deliberately not cached, because a later final probe may have a
    # larger budget and should get the chance to build the stronger table.
    return bool(bound.two_cycle_table_complete) and not bool(bound.two_cycle_fallback_to_memoryless)


def _reset_direct_completion_bound_query_stats(bound: _DirectJourneyCompletionBound) -> None:
    # Query counters are diagnostics for one pricing call.  The bound table is
    # immutable after construction, but these counters mutate during lookup, so
    # reset them when a cached table is reused by the next caller.
    bound.two_cycle_second_best_queries = 0
    bound.two_cycle_incompatible_queries = 0


class _UniqueTaskVisitLowerBound:
    """O(N) lower bound that collects each remaining task dual at most once."""

    def __init__(self, data: FutureData, duals: FutureDuals, task_to_bit: dict[int, int]) -> None:
        self.full_mask = (1 << len(task_to_bit)) - 1
        self.incoming_entries: tuple[tuple[int, float], ...] = tuple(
            (1 << int(task_to_bit[int(task)]), self._task_visit_lower_bound(data, duals, int(task), direction="incoming"))
            for task in data.tasks
            if int(task) in task_to_bit
        )
        self.outgoing_entries: tuple[tuple[int, float], ...] = tuple(
            (1 << int(task_to_bit[int(task)]), self._task_visit_lower_bound(data, duals, int(task), direction="outgoing"))
            for task in data.tasks
            if int(task) in task_to_bit
        )
        self._incoming_cache: dict[tuple[int, int], float] = {}
        self._outgoing_cache: dict[tuple[int, int], float] = {}
        self._value_cache: dict[tuple[int, int], float] = {}

    def value(self, available_mask: int, max_visits: int) -> float:
        if int(max_visits) <= 0 or int(available_mask) <= 0:
            return 0.0
        key = (int(available_mask), int(max_visits))
        cached = self._value_cache.get(key)
        if cached is not None:
            return cached
        result = max(
            self.incoming_value(int(available_mask), int(max_visits)),
            self.outgoing_value(int(available_mask), int(max_visits)),
        )
        self._value_cache[key] = float(result)
        return float(result)

    def incoming_value(self, available_mask: int, max_visits: int) -> float:
        if int(max_visits) <= 0 or int(available_mask) <= 0:
            return 0.0
        key = (int(available_mask), int(max_visits))
        cached = self._incoming_cache.get(key)
        if cached is not None:
            return cached
        result = self._value_from_entries(self.incoming_entries, int(available_mask), int(max_visits))
        self._incoming_cache[key] = float(result)
        return float(result)

    def outgoing_value(self, available_mask: int, max_visits: int) -> float:
        if int(max_visits) <= 0 or int(available_mask) <= 0:
            return 0.0
        key = (int(available_mask), int(max_visits))
        cached = self._outgoing_cache.get(key)
        if cached is not None:
            return cached
        result = self._value_from_entries(self.outgoing_entries, int(available_mask), int(max_visits))
        self._outgoing_cache[key] = float(result)
        return float(result)

    @staticmethod
    def _value_from_entries(entries: tuple[tuple[int, float], ...], available_mask: int, max_visits: int) -> float:
        values = [
            float(value)
            for bit, value in entries
            if int(available_mask) & int(bit) and float(value) < 0.0
        ]
        if not values:
            return 0.0
        values.sort()
        return float(sum(values[: int(max_visits)]))

    @staticmethod
    def _task_visit_lower_bound(data: FutureData, duals: FutureDuals, task: int, *, direction: str) -> float:
        arc_costs: list[float] = []
        other_tasks = tuple(int(item) for item in data.tasks if int(item) != int(task))
        if direction == "incoming":
            pairs = ((int(source), int(task)) for source in (0, *other_tasks))
        elif direction == "outgoing":
            pairs = ((int(task), int(target)) for target in (*other_tasks, 0))
        else:
            raise ValueError(f"unsupported unique task lower-bound direction {direction!r}")
        for source, target in pairs:
            try:
                options = data.options(int(source), int(target))
            except KeyError:
                continue
            arc_costs.extend(float(option.cost) for option in options)
        arc_lb = min(arc_costs) if arc_costs else 0.0
        return (
            float(arc_lb)
            + float(data.task_value(int(task), "c_srv"))
            - float(duals.cover.get(int(task), 0.0))
        )


class _PositiveSubsetCutRewardBound:
    """Upper bound on future positive subset-row cut reward.

    For small task sets this precomputes an exact mask DP:
    `best[slots][mask]` is the largest positive SRC reward among supersets of
    `mask` that add at most `slots` tasks.  For larger task sets it falls back
    to a row-wise upper bound to avoid a Python `2^N` table in 20-task runs.
    """

    EXACT_MASK_LIMIT = 16

    def __init__(
        self,
        *,
        task_count: int,
        cut_duals: dict[int, float],
        cuts: tuple[FutureCut, ...],
        cut_masks: tuple[int, ...],
    ) -> None:
        self.task_count = max(0, int(task_count))
        self.cut_duals = cut_duals
        self.cuts = cuts
        self.cut_masks = cut_masks
        self.has_positive_subset_reward = any(
            float(cut_duals.get(int(cut_index), 0.0)) > 1.0e-12
            and getattr(cut, "kind", "") == "subset_row"
            and int(cut_index) < len(cut_masks)
            and int(cut_masks[cut_index]) > 0
            for cut_index, cut in enumerate(cuts)
        )
        self.exact_enabled = bool(self.has_positive_subset_reward) and self.task_count <= self.EXACT_MASK_LIMIT
        self.total_reward: list[float] = []
        self.best_by_slots: list[list[float]] = []
        self.value_cache: dict[tuple[int, int], float] = {}
        if self.exact_enabled:
            self._build_exact_tables()

    def value(self, mask: int, remaining_visit_capacity: int) -> float:
        slots = max(0, min(int(remaining_visit_capacity), self.task_count))
        current_mask = int(mask)
        if slots <= 0 or not self.has_positive_subset_reward:
            return 0.0
        key = (int(current_mask), int(slots))
        cached = self.value_cache.get(key)
        if cached is not None:
            return cached
        if self.exact_enabled and self.best_by_slots:
            bounded_mask = int(current_mask) & ((1 << self.task_count) - 1)
            result = max(
                0.0,
                float(self.best_by_slots[slots][bounded_mask]) - float(self.total_reward[bounded_mask]),
            )
            self.value_cache[key] = float(result)
            return float(result)
        result = _direct_completion_positive_subset_future_reward_bound_rowwise(
            current_mask,
            slots,
            self.cut_duals,
            self.cuts,
            self.cut_masks,
        )
        self.value_cache[key] = float(result)
        return float(result)

    def _build_exact_tables(self) -> None:
        size = 1 << self.task_count
        total = [0.0] * size
        positive_cuts: list[tuple[int, int, float]] = []
        for cut_index, cut in enumerate(self.cuts):
            dual = float(self.cut_duals.get(int(cut_index), 0.0))
            if dual <= 1.0e-12 or getattr(cut, "kind", "") != "subset_row" or int(cut_index) >= len(self.cut_masks):
                continue
            cut_mask = int(self.cut_masks[cut_index]) & (size - 1)
            if cut_mask <= 0:
                continue
            positive_cuts.append((cut_mask, max(1, int(getattr(cut, "k", 2))), dual))
        if not positive_cuts:
            self.exact_enabled = False
            return
        for mask in range(size):
            reward = 0.0
            for cut_mask, k, dual in positive_cuts:
                reward += float(dual) * float((int(mask) & int(cut_mask)).bit_count() // int(k))
            total[mask] = reward
        self.total_reward = total
        best_by_slots: list[list[float]] = [total]
        full_mask = size - 1
        for slots in range(1, self.task_count + 1):
            previous = best_by_slots[slots - 1]
            current = previous.copy()
            for mask in range(size - 1, -1, -1):
                missing = full_mask ^ int(mask)
                best = float(current[mask])
                bitset = int(missing)
                while bitset:
                    bit = bitset & -bitset
                    candidate = float(previous[int(mask) | int(bit)])
                    if candidate > best:
                        best = candidate
                    bitset ^= bit
                current[mask] = best
            best_by_slots.append(current)
        self.best_by_slots = best_by_slots


class _UniqueRouteBoundBudgetExceeded(Exception):
    """Internal signal that unique-route helper should skip this query."""


class _UniqueRouteCompletionLowerBound:
    """Task-unique route suffix bound for small direct-journey pricing calls.

    This DP keeps the current node, available task mask, remaining slots in the
    active sortie, and remaining future sorties.  It ignores time windows,
    energy, and physical option coupling, so it remains an optimistic lower
    bound, while being much tighter than node-independent task rewards.
    """

    EXACT_MASK_LIMIT = 16
    EXACT_FIRST_STEP_CACHE_MAX_SIZE = 100_000

    def __init__(
        self,
        data: FutureData,
        duals: FutureDuals,
        task_to_bit: dict[int, int],
        *,
        max_tasks_per_sortie: int,
        sortie_limit: int,
        time_buckets: int,
        energy_buckets: int,
        exact_first_step_enabled: bool = False,
        exact_first_step_bucket_diagnostics_enabled: bool = False,
        exact_mask_limit: int | None = None,
        cache_state_limit: int = 0,
        deadline: float | None = None,
    ) -> None:
        self.exact_mask_limit = self.EXACT_MASK_LIMIT if exact_mask_limit is None else max(0, int(exact_mask_limit))
        self.enabled = len(task_to_bit) <= int(self.exact_mask_limit)
        self.exact_first_step_enabled = bool(exact_first_step_enabled)
        self.exact_first_step_bucket_diagnostics_enabled = bool(exact_first_step_bucket_diagnostics_enabled)
        self.cache_state_limit = max(0, int(cache_state_limit))
        self.deadline = None if deadline is None else float(deadline)
        self.horizon = max(0.0, float(data.horizon))
        self.bucket_count = max(1, int(time_buckets))
        self.bucket_width = self.horizon / float(self.bucket_count) if self.horizon > 0.0 else 1.0
        self.energy_limit = max(0.0, float(data.energy_limit))
        self.energy_bucket_count = max(0, int(energy_buckets))
        self.energy_bucket_width = (
            self.energy_limit / float(self.energy_bucket_count)
            if self.energy_bucket_count > 0 and self.energy_limit > 0.0
            else 1.0
        )
        self.rho = max(1.0e-9, float(data.rho))
        self.survival_energy_rate = max(0.0, float(data.survival_energy_rate))
        self.tasks = tuple(int(task) for task in data.tasks if int(task) in task_to_bit)
        self.task_to_bit = {int(task): int(bit) for task, bit in task_to_bit.items()}
        self.task_bits = tuple((int(task), 1 << int(self.task_to_bit[int(task)])) for task in self.tasks)
        self.full_mask = (1 << len(task_to_bit)) - 1 if self.enabled else 0
        self.max_tasks_per_sortie = max(1, int(max_tasks_per_sortie))
        self.sortie_limit = max(0, int(sortie_limit))
        self.service_cost = {int(task): float(data.task_value(int(task), "c_srv")) for task in self.tasks}
        self.service_energy = {int(task): float(data.task_value(int(task), "g")) for task in self.tasks}
        self.service_time = {int(task): float(data.task_value(int(task), "sigma")) for task in self.tasks}
        self.ready_time = {int(task): float(data.task_value(int(task), "r")) for task in self.tasks}
        self.due_arrival = {
            int(task): float(data.task_value(int(task), "D")) - float(data.task_value(int(task), "sigma"))
            for task in self.tasks
        }
        self.task_reward = {int(task): float(duals.cover.get(int(task), 0.0)) for task in self.tasks}
        self.arc_options = _DirectJourneyCompletionBound._directed_arc_lower_bounds(data)
        self._future_cache: dict[tuple[int, int, int], float] = {}
        self._partial_cache: dict[tuple[int, int, int, int, int, int], float] = {}
        self._exact_first_step_cache: dict[tuple[int, int, int, int, float, float], float] = {}
        self._exact_first_step_resource_bucket_keys: set[tuple[int, int, int, int, int, int]] = set()
        self.future_cache_hits = 0
        self.future_cache_misses = 0
        self.partial_cache_hits = 0
        self.partial_cache_misses = 0
        self.exact_first_step_cache_hits = 0
        self.exact_first_step_cache_misses = 0
        self.exact_first_step_resource_bucket_revisits = 0
        self.cache_budget_exceeded_count = 0

    def future_value(self, available_mask: int, remaining_sorties: int, current_time: float = 0.0) -> float | None:
        if not self.enabled:
            return None
        try:
            return self._future_value(
                int(available_mask) & int(self.full_mask),
                max(0, int(remaining_sorties)),
                self._bucket_of_time(float(current_time)),
            )
        except _UniqueRouteBoundBudgetExceeded:
            return None

    def partial_value(
        self,
        last: int,
        available_mask: int,
        remaining_slots_in_sortie: int,
        future_sorties: int,
        current_time: float = 0.0,
        current_energy: float = 0.0,
    ) -> float | None:
        if not self.enabled:
            return None
        bounded_mask = int(available_mask) & int(self.full_mask)
        slots = max(0, int(remaining_slots_in_sortie))
        future = max(0, int(future_sorties))
        try:
            bucketed = self._partial_value(
                int(last),
                int(bounded_mask),
                int(slots),
                int(future),
                self._bucket_of_time(float(current_time)),
                self._bucket_of_energy(float(current_energy)),
            )
        except _UniqueRouteBoundBudgetExceeded:
            return None
        if not self.exact_first_step_enabled:
            return float(bucketed)
        if float(bucketed) == math.inf:
            return float(bucketed)
        try:
            exact_first = self._partial_value_exact_first_step(
                int(last),
                int(bounded_mask),
                int(slots),
                int(future),
                float(current_time),
                float(current_energy),
            )
        except _UniqueRouteBoundBudgetExceeded:
            return float(bucketed)
        # Both values are optimistic lower bounds.  Taking the larger one keeps
        # the proof safe while recovering precision lost by flooring the
        # current prefix resources into a coarse bucket.
        return max(float(bucketed), float(exact_first))

    def _cache_state_count(self) -> int:
        return (
            len(self._future_cache)
            + len(self._partial_cache)
            + len(self._exact_first_step_cache)
        )

    def _ensure_cache_budget(self) -> None:
        if self.deadline is not None and time.perf_counter() > float(self.deadline):
            self.cache_budget_exceeded_count += 1
            raise _UniqueRouteBoundBudgetExceeded
        if self.cache_state_limit <= 0:
            return
        if self._cache_state_count() >= int(self.cache_state_limit):
            self.cache_budget_exceeded_count += 1
            raise _UniqueRouteBoundBudgetExceeded

    def _bucket_of_time(self, value: float) -> int:
        if self.horizon <= 0.0:
            return 0
        bounded = max(0.0, min(float(value), self.horizon))
        return max(0, min(self.bucket_count, int(math.floor(bounded / float(self.bucket_width)))))

    def _bucket_time(self, bucket: int) -> float:
        return max(0.0, min(float(self.horizon), float(bucket) * float(self.bucket_width)))

    def _bucket_of_energy(self, value: float) -> int:
        if self.energy_bucket_count <= 0 or self.energy_limit <= 0.0:
            return 0
        bounded = max(0.0, min(float(value), self.energy_limit))
        return max(0, min(self.energy_bucket_count, int(math.floor(bounded / float(self.energy_bucket_width)))))

    def _bucket_energy(self, bucket: int) -> float:
        if self.energy_bucket_count <= 0:
            return 0.0
        return max(0.0, min(float(self.energy_limit), float(bucket) * float(self.energy_bucket_width)))

    def _time_after_return(self, depart_time: float, return_time: float, energy_used: float, return_energy: float) -> float:
        survival_lb = float(self.survival_energy_rate) * max(0.0, float(return_time))
        total_energy_lb = max(0.0, float(energy_used) + float(return_energy) + float(survival_lb))
        recharge_lb = total_energy_lb / float(self.rho)
        return float(depart_time) + float(return_time) + float(recharge_lb)

    def _future_value(self, available_mask: int, remaining_sorties: int, bucket: int) -> float:
        key = (int(available_mask), int(remaining_sorties), int(bucket))
        cached = self._future_cache.get(key)
        if cached is not None:
            self.future_cache_hits += 1
            return cached
        self._ensure_cache_budget()
        self.future_cache_misses += 1
        best = 0.0
        if int(remaining_sorties) > 0 and int(available_mask) > 0:
            for task, bit in self.task_bits:
                self._ensure_cache_budget()
                if not (int(available_mask) & int(bit)):
                    continue
                depart_time = self._bucket_time(int(bucket))
                for option in self.arc_options.get((0, int(task)), tuple()):
                    self._ensure_cache_budget()
                    arrival_time = float(depart_time) + float(option.time)
                    service_start = max(float(arrival_time), float(self.ready_time[int(task)]))
                    if service_start > self.due_arrival[int(task)] + 1.0e-9:
                        continue
                    survival_lb = float(self.survival_energy_rate) * (
                        max(0.0, float(option.time)) + max(0.0, float(self.service_time[int(task)]))
                    )
                    next_energy = float(option.energy) + self.service_energy[int(task)] + float(survival_lb)
                    if self.energy_bucket_count > 0 and next_energy > self.energy_limit + 1.0e-9:
                        continue
                    next_bucket = self._bucket_of_time(float(service_start) + self.service_time[int(task)])
                    candidate = (
                        float(option.cost)
                        + float(self.service_cost[int(task)])
                        - float(self.task_reward[int(task)])
                        + self._partial_value(
                            int(task),
                            int(available_mask) ^ int(bit),
                            self.max_tasks_per_sortie - 1,
                            int(remaining_sorties) - 1,
                            int(next_bucket),
                            self._bucket_of_energy(float(next_energy)),
                        )
                    )
                    if candidate < best:
                        best = candidate
        self._ensure_cache_budget()
        self._future_cache[key] = float(best)
        return float(best)

    def _partial_value(
        self,
        last: int,
        available_mask: int,
        remaining_slots_in_sortie: int,
        future_sorties: int,
        bucket: int,
        energy_bucket: int,
    ) -> float:
        key = (
            int(last),
            int(available_mask),
            int(remaining_slots_in_sortie),
            int(future_sorties),
            int(bucket),
            int(energy_bucket),
        )
        cached = self._partial_cache.get(key)
        if cached is not None:
            self.partial_cache_hits += 1
            return cached
        self._ensure_cache_budget()
        self.partial_cache_misses += 1
        best = float("inf")
        depart_time = self._bucket_time(int(bucket))
        energy_used = self._bucket_energy(int(energy_bucket))
        for option in self.arc_options.get((int(last), 0), tuple()):
            self._ensure_cache_budget()
            return_time = self._time_after_return(
                float(depart_time),
                float(option.time),
                float(energy_used),
                float(option.energy),
            )
            if return_time > self.horizon + 1.0e-9:
                continue
            survival_lb = float(self.survival_energy_rate) * max(0.0, float(option.time))
            if (
                self.energy_bucket_count > 0
                and float(energy_used) + float(option.energy) + float(survival_lb) > self.energy_limit + 1.0e-9
            ):
                continue
            return_bucket = self._bucket_of_time(float(return_time))
            candidate = float(option.cost) + self._future_value(int(available_mask), int(future_sorties), int(return_bucket))
            if candidate < best:
                best = candidate
        if int(remaining_slots_in_sortie) > 0 and int(available_mask) > 0:
            for task, bit in self.task_bits:
                self._ensure_cache_budget()
                if not (int(available_mask) & int(bit)):
                    continue
                for option in self.arc_options.get((int(last), int(task)), tuple()):
                    self._ensure_cache_budget()
                    arrival_time = float(depart_time) + float(option.time)
                    service_start = max(float(arrival_time), float(self.ready_time[int(task)]))
                    if service_start > self.due_arrival[int(task)] + 1.0e-9:
                        continue
                    survival_lb = float(self.survival_energy_rate) * (
                        max(0.0, float(option.time)) + max(0.0, float(self.service_time[int(task)]))
                    )
                    next_energy = (
                        float(energy_used)
                        + float(option.energy)
                        + self.service_energy[int(task)]
                        + float(survival_lb)
                    )
                    if self.energy_bucket_count > 0 and next_energy > self.energy_limit + 1.0e-9:
                        continue
                    next_bucket = self._bucket_of_time(float(service_start) + self.service_time[int(task)])
                    candidate = (
                        float(option.cost)
                        + float(self.service_cost[int(task)])
                        - float(self.task_reward[int(task)])
                        + self._partial_value(
                            int(task),
                            int(available_mask) ^ int(bit),
                            int(remaining_slots_in_sortie) - 1,
                            int(future_sorties),
                            int(next_bucket),
                            self._bucket_of_energy(float(next_energy)),
                        )
                    )
                    if candidate < best:
                        best = candidate
        if math.isinf(best):
            # No relaxed completion exists from this partial route.  The exact
            # label cannot produce a feasible journey either.
            best = float("inf")
        self._ensure_cache_budget()
        self._partial_cache[key] = float(best)
        return float(best)

    def _partial_value_exact_first_step(
        self,
        last: int,
        available_mask: int,
        remaining_slots_in_sortie: int,
        future_sorties: int,
        current_time: float,
        current_energy: float,
    ) -> float:
        bounded_time = max(0.0, min(float(self.horizon), float(current_time)))
        bounded_energy = max(0.0, min(float(self.energy_limit), float(current_energy)))
        key = (
            int(last),
            int(available_mask),
            int(remaining_slots_in_sortie),
            int(future_sorties),
            float(bounded_time),
            float(bounded_energy),
        )
        cached = self._exact_first_step_cache.get(key)
        if cached is not None:
            self.exact_first_step_cache_hits += 1
            return cached
        self._ensure_cache_budget()
        self.exact_first_step_cache_misses += 1
        if self.exact_first_step_bucket_diagnostics_enabled:
            bucket_key = (
                int(last),
                int(available_mask),
                int(remaining_slots_in_sortie),
                int(future_sorties),
                self._bucket_of_time(float(bounded_time)),
                self._bucket_of_energy(float(bounded_energy)),
            )
            if bucket_key in self._exact_first_step_resource_bucket_keys:
                self.exact_first_step_resource_bucket_revisits += 1
            else:
                self._exact_first_step_resource_bucket_keys.add(bucket_key)
        best = float("inf")
        depart_time = float(bounded_time)
        energy_used = float(bounded_energy)
        for option in self.arc_options.get((int(last), 0), tuple()):
            self._ensure_cache_budget()
            return_time = self._time_after_return(
                float(depart_time),
                float(option.time),
                float(energy_used),
                float(option.energy),
            )
            if return_time > self.horizon + 1.0e-9:
                continue
            survival_lb = float(self.survival_energy_rate) * max(0.0, float(option.time))
            if (
                self.energy_bucket_count > 0
                and float(energy_used) + float(option.energy) + float(survival_lb) > self.energy_limit + 1.0e-9
            ):
                continue
            future_lb = self.future_value(
                int(available_mask),
                int(future_sorties),
                float(return_time),
            )
            if future_lb is None:
                raise _UniqueRouteBoundBudgetExceeded
            candidate = float(option.cost) + float(future_lb)
            if float(candidate) < float(best):
                best = float(candidate)
        if int(remaining_slots_in_sortie) > 0 and int(available_mask) > 0:
            for task, bit in self.task_bits:
                self._ensure_cache_budget()
                if not (int(available_mask) & int(bit)):
                    continue
                for option in self.arc_options.get((int(last), int(task)), tuple()):
                    self._ensure_cache_budget()
                    arrival_time = float(depart_time) + float(option.time)
                    service_start = max(float(arrival_time), float(self.ready_time[int(task)]))
                    if service_start > self.due_arrival[int(task)] + 1.0e-9:
                        continue
                    survival_lb = float(self.survival_energy_rate) * (
                        max(0.0, float(option.time)) + max(0.0, float(self.service_time[int(task)]))
                    )
                    next_energy = (
                        float(energy_used)
                        + float(option.energy)
                        + self.service_energy[int(task)]
                        + float(survival_lb)
                    )
                    if self.energy_bucket_count > 0 and next_energy > self.energy_limit + 1.0e-9:
                        continue
                    candidate = (
                        float(option.cost)
                        + float(self.service_cost[int(task)])
                        - float(self.task_reward[int(task)])
                        + self._partial_value(
                            int(task),
                            int(available_mask) ^ int(bit),
                            int(remaining_slots_in_sortie) - 1,
                            int(future_sorties),
                            self._bucket_of_time(float(service_start) + self.service_time[int(task)]),
                            self._bucket_of_energy(float(next_energy)),
                        )
                    )
                    if float(candidate) < float(best):
                        best = float(candidate)
        if len(self._exact_first_step_cache) < int(self.EXACT_FIRST_STEP_CACHE_MAX_SIZE):
            self._ensure_cache_budget()
            self._exact_first_step_cache[key] = float(best)
        return float(best)


class _TaskSetSupersetLowerBoundCache:
    """Best optimistic sortie lower bound among supersets of a partial task set."""

    def __init__(
        self,
        task_set_cache: _TaskSetReducedCostLowerBoundCache,
        *,
        task_count: int,
        max_tasks_per_sortie: int,
        enabled: bool,
    ) -> None:
        self.task_set_cache = task_set_cache
        self.enabled = bool(enabled) and int(task_count) <= 20
        self.full_mask = (1 << int(task_count)) - 1 if self.enabled else 0
        self.max_tasks_per_sortie = max(1, int(max_tasks_per_sortie))
        self.cache: dict[tuple[int, int], float] = {}

    def value(self, required_mask: int, available_mask: int | None = None) -> float | None:
        if not self.enabled:
            return None
        required = int(required_mask)
        available = self.full_mask if available_mask is None else int(available_mask)
        if required & ~available:
            return float("inf")
        key = (required, available)
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        if required.bit_count() > self.max_tasks_per_sortie:
            self.cache[key] = float("inf")
            return float("inf")
        optional = int(available) ^ int(required)
        remaining_slots = self.max_tasks_per_sortie - int(required).bit_count()
        best = self.task_set_cache.value(required)
        submask = optional
        while submask:
            if int(submask).bit_count() <= remaining_slots:
                best = min(best, self.task_set_cache.value(required | int(submask)))
            submask = (submask - 1) & optional
        self.cache[key] = best
        return best


def _price_journeys_by_sharded_pulse_dummy(
    data: FutureData,
    *,
    config: JourneyPricingConfig,
) -> JourneyPricingResult:
    ledger = build_dummy_shard_ledger(
        data,
        getattr(config, "sharded_final_judge_dummy_statuses", tuple()),
    )
    fields = ledger.result_fields()
    pricing_state = str(fields.get("pricing_state", ""))
    fields["final_judge_engine"] = "sharded_pulse_dummy"
    exhausted = bool(fields.pop("exhausted"))
    best_reduced_cost = fields.pop("best_reduced_cost")
    status = str(fields.pop("status"))
    reason = str(fields.pop("reason"))
    return JourneyPricingResult(
        [],
        exhausted,
        None if best_reduced_cost is None else float(best_reduced_cost),
        0,
        0,
        0,
        0,
        status,
        reason,
        final_judge_dummy_engine_enabled=True,
        final_judge_dummy_mode=str(config.sharded_final_judge_dummy_mode or ""),
        final_judge_allow_test_dummy_certificate=bool(
            config.sharded_final_judge_allow_test_dummy_certificate
        ),
        final_judge_dummy_certificate=pricing_state == PRICING_STATE_CERTIFIED_NO_NEGATIVE,
        final_judge_test_only=True,
        **fields,
    )


def _sharded_pulse_incomplete_result(
    *,
    reason: str,
    incomplete_reason: str,
    dummy_engine_enabled: bool = False,
    dummy_mode: str = "",
    allow_test_dummy_certificate: bool = False,
) -> JourneyPricingResult:
    return JourneyPricingResult(
        [],
        False,
        None,
        0,
        0,
        0,
        0,
        "INCOMPLETE",
        reason,
        global_certificate_capable=False,
        final_judge_engine="sharded_pulse_dummy" if bool(dummy_engine_enabled) else "sharded_pulse",
        final_judge_certificate_capable=False,
        final_judge_sharded_enabled=True,
        final_judge_dummy_engine_enabled=bool(dummy_engine_enabled),
        final_judge_dummy_mode=str(dummy_mode or ""),
        final_judge_allow_test_dummy_certificate=bool(allow_test_dummy_certificate),
        final_judge_dummy_certificate=False,
        final_judge_test_only=bool(dummy_engine_enabled),
        final_judge_incomplete_reason=str(incomplete_reason),
        pricing_state=PRICING_STATE_INCOMPLETE_LIMIT,
    )


def _sharded_pulse_dummy_engine_allowed(data: FutureData, config: JourneyPricingConfig) -> bool:
    if not bool(config.sharded_final_judge_allow_test_dummy_certificate):
        return False
    env_value = str(os.environ.get("BPC_FUTURE_ALLOW_DUMMY_CERTIFICATE", "")).strip().lower()
    if env_value not in {"1", "true", "yes", "on"}:
        return False
    name = str(getattr(data, "name", "") or "")
    return name == "very_small" or name.startswith("test")


def _price_journeys_by_sharded_pulse_guarded(
    data: FutureData,
    duals: JourneyDuals,
    branch_constraints: tuple[BranchConstraint, ...],
    *,
    config: JourneyPricingConfig,
    cuts: tuple[FutureCut, ...],
    forbidden_journey_signatures: set[tuple] | frozenset[tuple] | None,
    active_support_task_sets: set[frozenset[int]] | frozenset[frozenset[int]] | None,
    pool_task_sets: set[frozenset[int]] | frozenset[frozenset[int]] | None,
) -> JourneyPricingResult:
    forbidden = {tuple(signature) for signature in (forbidden_journey_signatures or set())}
    all_candidates: dict[tuple, tuple[float, JourneyColumn]] = {}
    duplicate_negative_seen = False
    incomplete_reason = ""
    shards_total = len(tuple(data.tasks))
    shards_certified = 0
    shards_incomplete = 0
    shards_negative = 0
    generated_traces = 0
    materialized_sorties = 0
    materialized_journeys = 0
    pulse_recursions = 0
    pulse_expanded_states = 0
    pulse_resource_pruned = 0
    pulse_return_pruned = 0
    pulse_time_window_pruned = 0
    pulse_capacity_pruned = 0
    pulse_energy_pruned = 0
    transition_time_window_pruned = 0
    transition_energy_pruned = 0
    transition_return_pruned = 0
    pulse_bound_pruned = 0
    pulse_archive_pruned = 0
    pulse_depot_ready_pruned = 0
    pulse_harvested_count = 0
    best_true_rc: float | None = None

    deadline = config.absolute_deadline
    if deadline is None and float(config.time_limit) > 0.0:
        deadline = time.perf_counter() + float(config.time_limit)

    for task in data.tasks:
        shard = transition_root_only_pulse(
            data,
            duals,
            cuts=cuts,
            time_bucket_size=float(config.time_bucket_size),
            eps=1.0e-6,
            max_tasks_per_sortie=int(config.max_tasks_per_trip),
            max_sorties=int(data.sortie_limit),
            first_task_shard=int(task),
            branch_constraints=branch_constraints,
            deadline=deadline,
            max_recursions=int(config.pulse_max_recursions),
        )
        generated_traces += int(shard.generated_sortie_traces)
        materialized_sorties += int(shard.materialized_sorties)
        materialized_journeys += int(shard.materialized_journeys)
        pulse_recursions += int(shard.recursions)
        pulse_expanded_states += int(shard.expanded_states)
        pulse_resource_pruned += int(shard.pulse_resource_pruned)
        pulse_return_pruned += int(shard.pulse_return_pruned)
        pulse_time_window_pruned += int(shard.pulse_time_window_pruned)
        pulse_capacity_pruned += int(shard.pulse_capacity_pruned)
        pulse_energy_pruned += int(shard.pulse_energy_pruned)
        transition_time_window_pruned += int(shard.transition_time_window_pruned)
        transition_energy_pruned += int(shard.transition_energy_pruned)
        transition_return_pruned += int(shard.transition_return_pruned)
        pulse_bound_pruned += int(shard.pulse_bound_pruned)
        pulse_archive_pruned += int(shard.pulse_archive_pruned)
        pulse_depot_ready_pruned += int(shard.pulse_depot_ready_pruned)
        pulse_harvested_count += int(shard.pulse_harvested_count)
        if shard.best_true_reduced_cost is not None:
            best_true_rc = (
                float(shard.best_true_reduced_cost)
                if best_true_rc is None
                else min(float(best_true_rc), float(shard.best_true_reduced_cost))
            )
        if not bool(shard.exhausted) and str(shard.status) not in {"FOUND_NEGATIVE", "FOUND_NEGATIVE_HARVESTED"}:
            shards_incomplete += 1
            incomplete_reason = str(shard.reason or shard.status)
            continue

        shard_new_negative = False
        negative_candidates = (
            tuple(shard.harvested_journeys)
            if shard.harvested_journeys
            else tuple(candidate.journey for candidate in shard.negative_leaves)
        )
        for journey in negative_candidates:
            signature = tuple(journey.signature)
            if signature in forbidden:
                duplicate_negative_seen = True
                continue
            if not _journey_task_set_branch_allowed(journey.task_set, branch_constraints):
                continue
            true_rc = float(manual_journey_reduced_cost(journey, duals, cuts=cuts))
            if true_rc >= -1.0e-6:
                continue
            old = all_candidates.get(signature)
            if old is None or true_rc < float(old[0]):
                all_candidates[signature] = (true_rc, journey)
            shard_new_negative = True
        if shard_new_negative:
            shards_negative += 1
        elif bool(shard.exhausted):
            shards_certified += 1

    common = {
        "final_judge_engine": "sharded_pulse",
        "final_judge_sharded_enabled": True,
        "final_judge_shards_total": int(shards_total),
        "final_judge_shards_certified": int(shards_certified),
        "final_judge_shards_incomplete": int(shards_incomplete),
        "final_judge_shards_negative_found": int(shards_negative),
        "pulse_recursions": int(pulse_recursions),
        "pulse_expanded_states": int(pulse_expanded_states),
        "pulse_resource_pruned": int(pulse_resource_pruned),
        "pulse_return_pruned": int(pulse_return_pruned),
        "pulse_time_window_pruned": int(pulse_time_window_pruned),
        "pulse_capacity_pruned": int(pulse_capacity_pruned),
        "pulse_energy_pruned": int(pulse_energy_pruned),
        "transition_time_window_pruned": int(transition_time_window_pruned),
        "transition_energy_pruned": int(transition_energy_pruned),
        "transition_return_pruned": int(transition_return_pruned),
        "pulse_bound_pruned": int(pulse_bound_pruned),
        "pulse_archive_pruned": int(pulse_archive_pruned),
        "pulse_depot_ready_pruned": int(pulse_depot_ready_pruned),
        "pulse_harvested_count": int(pulse_harvested_count),
        "pulse_best_true_rc": best_true_rc,
    }
    if all_candidates:
        selected = [
            journey
            for _rc, journey in sorted(
                all_candidates.values(),
                key=lambda item: (round(float(item[0]), 9), item[1].signature),
            )[: max(1, int(config.max_returned_journeys))]
        ]
        return JourneyPricingResult(
            selected,
            False,
            min(float(rc) for rc, _journey in all_candidates.values()),
            int(generated_traces),
            int(materialized_sorties),
            int(materialized_journeys),
            len(selected),
            "FOUND_NEGATIVE",
            "sharded_pulse_found_negative",
            global_certificate_capable=False,
            final_judge_certificate_capable=False,
            final_judge_incomplete_reason="",
            pricing_state=PRICING_STATE_FOUND_NEGATIVE,
            pulse_negative_found=True,
            **common,
        )

    if duplicate_negative_seen:
        return JourneyPricingResult(
            [],
            False,
            best_true_rc,
            int(generated_traces),
            int(materialized_sorties),
            int(materialized_journeys),
            0,
            "INCOMPLETE",
            "sharded_pulse_duplicate_only_no_certificate",
            global_certificate_capable=False,
            final_judge_certificate_capable=False,
            final_judge_incomplete_reason="duplicate_only",
            pricing_state=PRICING_STATE_DUPLICATE_ONLY,
            pulse_negative_found=True,
            **common,
        )

    if shards_incomplete > 0:
        return JourneyPricingResult(
            [],
            False,
            best_true_rc,
            int(generated_traces),
            int(materialized_sorties),
            int(materialized_journeys),
            0,
            "INCOMPLETE",
            "sharded_pulse_incomplete",
            global_certificate_capable=False,
            final_judge_certificate_capable=False,
            final_judge_incomplete_reason=incomplete_reason or "incomplete",
            pricing_state=PRICING_STATE_INCOMPLETE_LIMIT,
            pulse_negative_found=False,
            **common,
        )

    if not _sharded_pulse_toy_certificate_allowed(data, branch_constraints, config):
        return JourneyPricingResult(
            [],
            False,
            best_true_rc,
            int(generated_traces),
            int(materialized_sorties),
            int(materialized_journeys),
            0,
            "INCOMPLETE",
            "sharded_pulse_toy_certificate_guard_failed",
            global_certificate_capable=False,
            final_judge_certificate_capable=False,
            final_judge_incomplete_reason="toy_certificate_guard_failed",
            pricing_state=PRICING_STATE_INCOMPLETE_LIMIT,
            pulse_negative_found=False,
            **common,
        )

    return JourneyPricingResult(
        [],
        True,
        0.0 if best_true_rc is None else max(0.0, float(best_true_rc)),
        int(generated_traces),
        int(materialized_sorties),
        int(materialized_journeys),
        0,
        "OPTIMAL",
        "sharded_pulse_no_negative_journey",
        global_certificate_capable=True,
        final_judge_certificate_capable=True,
        final_judge_incomplete_reason="",
        pricing_state=PRICING_STATE_CERTIFIED_NO_NEGATIVE,
        pulse_negative_found=False,
        **common,
    )


def _sharded_pulse_toy_certificate_allowed(
    data: FutureData,
    branch_constraints: tuple[BranchConstraint, ...],
    config: JourneyPricingConfig,
) -> bool:
    if not bool(config.sharded_final_judge_toy_certificate_enabled):
        return False
    name = str(getattr(data, "name", "") or "")
    if not (name == "very_small" or name.startswith("test")):
        return False
    if not bool(data.instance.get("scheduling", {}).get("task_waiting_allowed", True)):
        return False
    return all(constraint.kind in {"same_vehicle", "separate_vehicle"} for constraint in branch_constraints)


def price_journeys(
    data: FutureData,
    duals: JourneyDuals,
    branch_constraints: tuple[BranchConstraint, ...],
    *,
    config: JourneyPricingConfig,
    cuts: tuple[FutureCut, ...] = tuple(),
    trip_cache: dict[tuple, tuple[tuple[TimedTrip, ...], int, int]] | None = None,
    resource_cache: dict[tuple, Any] | None = None,
    forbidden_journey_signatures: set[tuple] | frozenset[tuple] | None = None,
    dominant_task_set_costs: dict[frozenset[int], float] | None = None,
    priority_task_sets: set[frozenset[int]] | frozenset[frozenset[int]] | None = None,
    active_support_task_sets: set[frozenset[int]] | frozenset[frozenset[int]] | None = None,
    priority_duals: JourneyDuals | None = None,
) -> JourneyPricingResult:
    """Return at most one most-negative journey or an exact no-negative certificate."""

    if any(constraint.kind not in {"same_vehicle", "separate_vehicle"} for constraint in branch_constraints):
        return JourneyPricingResult([], False, None, 0, 0, 0, 0, "UNSUPPORTED", "branch_or_cut_not_supported")
    if any(not _journey_pricing_cut_supported(cut) for cut in cuts):
        return JourneyPricingResult([], False, None, 0, 0, 0, 0, "UNSUPPORTED", "branch_or_cut_not_supported")
    if bool(config.sharded_final_judge_enabled) or str(config.final_judge_engine) == "sharded_pulse":
        if bool(config.sharded_final_judge_dummy_engine_enabled):
            if not _sharded_pulse_dummy_engine_allowed(data, config):
                return _sharded_pulse_incomplete_result(
                    reason="sharded_pulse_dummy_engine_not_allowed",
                    incomplete_reason="dummy_engine_not_allowed",
                    dummy_engine_enabled=True,
                    dummy_mode=str(config.sharded_final_judge_dummy_mode or ""),
                    allow_test_dummy_certificate=bool(
                        config.sharded_final_judge_allow_test_dummy_certificate
                    ),
                )
            return _price_journeys_by_sharded_pulse_dummy(data, config=config)
        return _price_journeys_by_sharded_pulse_guarded(
            data,
            duals,
            branch_constraints,
            config=config,
            cuts=cuts,
            forbidden_journey_signatures=forbidden_journey_signatures,
            active_support_task_sets=active_support_task_sets,
            pool_task_sets=set(dominant_task_set_costs or {}),
        )
    if bool(config.profile_pricing_enabled):
        return _price_journeys_by_profiles(
            data,
            duals,
            branch_constraints=branch_constraints,
            config=config,
            cuts=cuts,
            trip_cache=trip_cache,
            resource_cache=resource_cache,
            forbidden_journey_signatures=forbidden_journey_signatures,
            dominant_task_set_costs=dominant_task_set_costs,
        )
    direct_branch_safe = (not branch_constraints) or (
        bool(config.direct_journey_label_completion_bound_enabled)
        and _direct_ng_branch_certificate_safe(branch_constraints)
    ) or (
        int(config.direct_journey_label_max_labels_per_node) > 0
        and not bool(config.direct_journey_label_completion_bound_enabled)
    )
    if (
        bool(config.direct_journey_label_pricing_enabled)
        and bool(direct_branch_safe)
        and not bool(data.instance.get("scheduling", {}).get("task_waiting_allowed", True))
    ):
        return _price_journeys_by_direct_labels_with_ng_preprobe(
            data,
            duals,
            config=config,
            cuts=cuts,
            branch_constraints=branch_constraints,
            forbidden_journey_signatures=forbidden_journey_signatures,
            dominant_task_set_costs=dominant_task_set_costs,
            priority_task_sets=priority_task_sets,
            active_support_task_sets=active_support_task_sets,
            priority_duals=priority_duals,
            resource_cache=resource_cache,
        )
    started = time.perf_counter()
    vehicle = int(data.vehicles[0])
    trip_duals = FutureDuals(
        cover={int(task): float(value) for task, value in duals.cover.items()},
        task_vehicle={},
        sortie_count={int(vehicle): 0.0},
        time_occupation={},
        ordering={},
        branches={},
        cuts={},
    )
    trip_result = price_timed_trips(
        data,
        trip_duals,
        tuple(),
        vehicle=vehicle,
        config=PricingConfig(
            time_bucket_size=float(config.time_bucket_size),
            max_tasks_per_trip=int(config.max_tasks_per_trip),
            max_sequences=int(config.max_sequences),
            max_timed_evaluations=int(config.max_timed_evaluations),
            max_returned_trips=int(config.max_candidate_trips)
            if bool(config.allow_partial_negative) and int(config.max_candidate_trips) > 0
            else 0,
            eps=float(config.eps),
            heuristic=False,
            time_limit=float(config.time_limit),
            start_time_step=float(config.start_time_step),
            selection_mode="reduced_cost",
            max_path_combinations_per_sequence=int(config.max_path_combinations_per_sequence),
            path_dominance_enabled=bool(config.path_dominance_enabled),
            start_optimization_enabled=bool(config.start_optimization_enabled),
            max_negative_trips_per_sequence=0,
            max_negative_starts_per_profile=0,
            generalized_partial_dominance_enabled=bool(config.generalized_partial_dominance_enabled),
        ),
        cuts=tuple(),
        phase="phase2",
        trip_cache=trip_cache,
    )
    partial_trip_scan = not bool(trip_result.exhausted)
    if partial_trip_scan and (not bool(config.allow_partial_negative) or not trip_result.trips):
        return JourneyPricingResult(
            [],
            False,
            trip_result.best_reduced_cost,
            trip_result.generated_sequences,
            trip_result.evaluated_timed_trips,
            len(trip_result.trips),
            0,
            "INCOMPLETE",
            "timed_trip_pricing_incomplete",
        )
    base = float(data.fixed_vehicle_cost) - float(duals.fleet_limit)
    if not trip_result.trips:
        if base < -float(config.eps):
            return JourneyPricingResult(
                [],
                False,
                base if trip_result.best_reduced_cost is None else base + float(trip_result.best_reduced_cost),
                trip_result.generated_sequences,
                trip_result.evaluated_timed_trips,
                0,
                0,
                "INCOMPLETE",
                "negative_fleet_base_requires_nonnegative_trip_scan",
            )
        return JourneyPricingResult(
            [],
            True,
            None if trip_result.best_reduced_cost is None else base + float(trip_result.best_reduced_cost),
            trip_result.generated_sequences,
            trip_result.evaluated_timed_trips,
            0,
            0,
            "OPTIMAL",
            "no_negative_trip_contribution",
        )
    max_candidates = int(config.max_candidate_trips)
    if max_candidates > 0 and len(trip_result.trips) > max_candidates:
        return JourneyPricingResult(
            [],
            False,
            trip_result.best_reduced_cost,
            trip_result.generated_sequences,
            trip_result.evaluated_timed_trips,
            len(trip_result.trips),
            0,
            "INCOMPLETE",
            "candidate_trip_budget",
        )
    remaining_time = 0.0
    if float(config.time_limit) > 0.0:
        remaining_time = max(0.0, float(config.time_limit) - (time.perf_counter() - started))
        if remaining_time <= 0.0:
            return JourneyPricingResult(
                [],
                False,
                trip_result.best_reduced_cost,
                trip_result.generated_sequences,
                trip_result.evaluated_timed_trips,
                len(trip_result.trips),
                0,
                "INCOMPLETE",
                "time_limit_before_selection_mip",
            )
    selected, objective, status = _solve_best_journey_selection_dp(
        data,
        trip_result.trips,
        trip_duals,
        base_reduced_cost=base,
        max_states=int(config.max_dp_states),
    )
    if status != "OPTIMAL":
        return JourneyPricingResult(
            [],
            False,
            objective,
            trip_result.generated_sequences,
            trip_result.evaluated_timed_trips,
            len(trip_result.trips),
            len(selected),
            status,
            "selection_mip_not_optimal",
        )
    if objective is None or objective >= -float(config.eps):
        return JourneyPricingResult(
            [],
            not partial_trip_scan,
            objective,
            trip_result.generated_sequences,
            trip_result.evaluated_timed_trips,
            len(trip_result.trips),
            len(selected),
            "OPTIMAL" if not partial_trip_scan else "INCOMPLETE",
            "no_negative_journey" if not partial_trip_scan else "partial_scan_no_negative_journey",
        )
    journey = make_journey(data, selected)
    if journey is None:
        return JourneyPricingResult(
            [],
            False,
            objective,
            trip_result.generated_sequences,
            trip_result.evaluated_timed_trips,
            len(trip_result.trips),
            len(selected),
            "INCOMPLETE",
            "selected_trips_not_a_valid_journey",
        )
    add_threshold = max(float(config.eps), float(config.min_add_reduced_cost))
    if objective >= -add_threshold:
        return JourneyPricingResult(
            [],
            False,
            objective,
            trip_result.generated_sequences,
            trip_result.evaluated_timed_trips,
            len(trip_result.trips),
            len(selected),
            "INCOMPLETE",
            "weak_negative_journeys_filtered",
            weak_negative_journeys_filtered=1,
        )
    if journey.signature in (forbidden_journey_signatures or set()):
        return JourneyPricingResult(
            [],
            False,
            objective,
            trip_result.generated_sequences,
            trip_result.evaluated_timed_trips,
            len(trip_result.trips),
            len(selected),
            "INCOMPLETE",
            "negative_journey_already_in_pool",
            existing_journeys_filtered=1,
        )
    return JourneyPricingResult(
        [journey],
        not partial_trip_scan,
        objective,
        trip_result.generated_sequences,
        trip_result.evaluated_timed_trips,
        len(trip_result.trips),
        len(selected),
        "OPTIMAL" if not partial_trip_scan else "INCOMPLETE",
        "negative_journey" if not partial_trip_scan else "partial_negative_journey",
    )


def _attach_ng_probe_stats(result: JourneyPricingResult, ng_probe: JourneyPricingResult) -> JourneyPricingResult:
    return replace(
        result,
        ng_relaxation_enabled=bool(ng_probe.ng_relaxation_enabled),
        ng_dssr_iterations=int(ng_probe.ng_dssr_iterations),
        ng_memory_size=int(ng_probe.ng_memory_size),
        ng_non_elementary_negative=int(ng_probe.ng_non_elementary_negative),
        ng_label_pops=int(ng_probe.ng_label_pops),
        ng_generated_labels=int(ng_probe.ng_generated_labels),
        ng_dominance_pruned_labels=int(ng_probe.ng_dominance_pruned_labels),
        ng_fallback_to_elementary=bool(ng_probe.ng_fallback_to_elementary),
        ng_certificate_from_relaxation=bool(ng_probe.ng_certificate_from_relaxation),
        ng_best_relaxed_reduced_cost=ng_probe.ng_best_relaxed_reduced_cost,
    )


def _merge_ng_probe_pricing_result(
    result: JourneyPricingResult,
    ng_probe: JourneyPricingResult,
    *,
    duals: JourneyDuals,
    cuts: tuple[FutureCut, ...],
    max_returned: int,
    eps: float,
) -> JourneyPricingResult:
    if not ng_probe.journeys:
        return _attach_ng_probe_stats(result, ng_probe)

    by_signature: dict[tuple, tuple[float, JourneyColumn]] = {}
    for journey in [*result.journeys, *ng_probe.journeys]:
        true_rc = float(manual_journey_reduced_cost(journey, duals, cuts))
        if true_rc >= -float(eps):
            continue
        old = by_signature.get(journey.signature)
        if old is None or true_rc < old[0] - 1.0e-9:
            by_signature[journey.signature] = (true_rc, journey)

    selected_with_rc = sorted(by_signature.values(), key=lambda item: (round(item[0], 9), item[1].signature))
    selected = [journey for _rc, journey in selected_with_rc[: max(1, int(max_returned))]]
    if not selected:
        return _attach_ng_probe_stats(result, ng_probe)

    best_values = [
        value
        for value in (
            result.best_reduced_cost,
            ng_probe.best_reduced_cost,
            selected_with_rc[0][0] if selected_with_rc else None,
        )
        if value is not None
    ]
    merged = replace(
        result,
        journeys=selected,
        exhausted=False,
        best_reduced_cost=None if not best_values else min(float(value) for value in best_values),
        candidate_trips=max(int(result.candidate_trips), int(ng_probe.candidate_trips)),
        selected_trips=max((len(journey.trips) for journey in selected), default=0),
        status="INCOMPLETE",
        reason=(
            result.reason
            if result.journeys
            else "ng_probe_profile_merged_negative_journey"
        ),
        pricing_state=PRICING_STATE_FOUND_NEGATIVE,
    )
    return _attach_ng_probe_stats(merged, ng_probe)


def _price_journeys_by_direct_labels_with_ng_preprobe(
    data: FutureData,
    duals: JourneyDuals,
    *,
    config: JourneyPricingConfig,
    cuts: tuple[FutureCut, ...],
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
    forbidden_journey_signatures: set[tuple] | frozenset[tuple] | None = None,
    dominant_task_set_costs: dict[frozenset[int], float] | None = None,
    priority_task_sets: set[frozenset[int]] | frozenset[frozenset[int]] | None = None,
    active_support_task_sets: set[frozenset[int]] | frozenset[frozenset[int]] | None = None,
    priority_duals: JourneyDuals | None = None,
    resource_cache: dict[tuple, Any] | None = None,
) -> JourneyPricingResult:
    """Run optional NG/DSSR proof before the elementary direct-label judge.

    The NG relaxation is a true-dual direct-label front-end.  It may return
    materialized elementary negative journeys.  When certificate mode is
    enabled, a relaxed no-negative result is a valid certificate for the
    elementary problem because the relaxed state space contains every elementary
    journey.  If the preprobe cannot certify or find enough negative journeys,
    the existing elementary completion-bound judge remains the authoritative
    fallback.
    """

    if bool(config.direct_journey_label_ng_dssr_enabled):
        if not bool(config.direct_journey_label_completion_bound_enabled):
            return _price_journeys_by_direct_ng_dssr(
                data,
                duals,
                config=config,
                cuts=cuts,
                branch_constraints=branch_constraints,
                forbidden_journey_signatures=forbidden_journey_signatures,
                dominant_task_set_costs=dominant_task_set_costs,
            )
        if not bool(config.direct_journey_label_ng_completion_bound_preprobe_enabled):
            return _price_journeys_by_direct_labels(
                data,
                duals,
                config=config,
                cuts=cuts,
                branch_constraints=branch_constraints,
                forbidden_journey_signatures=forbidden_journey_signatures,
                dominant_task_set_costs=dominant_task_set_costs,
                priority_task_sets=priority_task_sets,
                active_support_task_sets=active_support_task_sets,
                priority_duals=priority_duals,
                resource_cache=resource_cache,
            )
        probe_allowed = (
            bool(config.direct_journey_label_ng_exact_probe_enabled)
            or bool(config.direct_journey_label_ng_certificate_enabled)
            or bool(config.direct_journey_label_ng_probe_certificate_enabled)
        )
        if probe_allowed:
            probe_config = replace(
                config,
                direct_journey_label_ng_certificate_enabled=bool(
                    config.direct_journey_label_ng_certificate_enabled
                    or (
                        config.direct_journey_label_ng_probe_certificate_enabled
                        and _direct_ng_branch_certificate_safe(branch_constraints)
                    )
                ),
            )
            probe_time_limit = float(config.direct_journey_label_ng_probe_time_limit)
            if probe_time_limit > 0.0 and float(config.time_limit) > 0.0:
                probe_config = replace(probe_config, time_limit=min(float(config.time_limit), probe_time_limit))
            ng_probe = _price_journeys_by_direct_ng_dssr(
                data,
                duals,
                config=probe_config,
                cuts=cuts,
                branch_constraints=branch_constraints,
                forbidden_journey_signatures=forbidden_journey_signatures,
                dominant_task_set_costs=dominant_task_set_costs,
                fallback_to_elementary=False,
            )
            min_early_return = max(1, int(config.direct_journey_label_ng_probe_min_journeys_for_early_return))
            if ng_probe.journeys and len(ng_probe.journeys) >= min_early_return:
                return ng_probe
            if (
                bool(probe_config.direct_journey_label_ng_certificate_enabled)
                and bool(ng_probe.exhausted)
                and str(ng_probe.status) == "OPTIMAL"
                and bool(ng_probe.ng_certificate_from_relaxation)
            ):
                return ng_probe
            if float(config.time_limit) > 0.0:
                remaining = max(0.0, float(config.time_limit) - float(ng_probe.profile_generation_time))
                if remaining <= 0.0:
                    return ng_probe
                config = replace(config, time_limit=remaining)
            fallback = _price_journeys_by_direct_labels(
                data,
                duals,
                config=config,
                cuts=cuts,
                branch_constraints=branch_constraints,
                forbidden_journey_signatures=forbidden_journey_signatures,
                dominant_task_set_costs=dominant_task_set_costs,
                priority_task_sets=priority_task_sets,
                active_support_task_sets=active_support_task_sets,
                priority_duals=priority_duals,
                resource_cache=resource_cache,
            )
            return _merge_ng_probe_pricing_result(
                fallback,
                ng_probe,
                duals=duals,
                cuts=cuts,
                max_returned=max(1, int(config.max_returned_journeys)),
                eps=float(config.eps),
            )

    return _price_journeys_by_direct_labels(
        data,
        duals,
        config=config,
        cuts=cuts,
        branch_constraints=branch_constraints,
        forbidden_journey_signatures=forbidden_journey_signatures,
        dominant_task_set_costs=dominant_task_set_costs,
        priority_task_sets=priority_task_sets,
        active_support_task_sets=active_support_task_sets,
        priority_duals=priority_duals,
        resource_cache=resource_cache,
    )


def _price_journeys_by_profiles(
    data: FutureData,
    duals: JourneyDuals,
    *,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
    config: JourneyPricingConfig,
    cuts: tuple[FutureCut, ...],
    trip_cache: dict[tuple, tuple[tuple[TimedTrip, ...], int, int]] | None,
    resource_cache: dict[tuple, Any] | None = None,
    forbidden_journey_signatures: set[tuple] | frozenset[tuple] | None = None,
    dominant_task_set_costs: dict[frozenset[int], float] | None = None,
) -> JourneyPricingResult:
    profile_call_started = time.perf_counter()
    ng_probe_stats: JourneyPricingResult | None = None
    if (
        bool(config.direct_journey_label_ng_dssr_enabled)
        and not bool(config.direct_journey_label_pricing_enabled)
        and not bool(data.instance.get("scheduling", {}).get("task_waiting_allowed", True))
        and (
            bool(config.allow_partial_negative)
            or bool(config.direct_journey_label_ng_exact_probe_enabled)
            or bool(config.direct_journey_label_ng_certificate_enabled)
            or bool(config.direct_journey_label_ng_probe_certificate_enabled)
        )
        ):
        probe_config = replace(
            config,
            direct_journey_label_ng_certificate_enabled=bool(
                config.direct_journey_label_ng_probe_certificate_enabled
                and _direct_ng_branch_certificate_safe(branch_constraints)
            ),
        )
        probe_time_limit = float(config.direct_journey_label_ng_probe_time_limit)
        if probe_time_limit > 0.0 and float(config.time_limit) > 0.0:
            probe_config = replace(probe_config, time_limit=min(float(config.time_limit), probe_time_limit))
        ng_probe = _price_journeys_by_direct_ng_dssr(
            data,
            duals,
            config=probe_config,
            cuts=cuts,
            branch_constraints=branch_constraints,
            forbidden_journey_signatures=forbidden_journey_signatures,
            dominant_task_set_costs=dominant_task_set_costs,
            fallback_to_elementary=False,
        )
        min_early_return = max(1, int(config.direct_journey_label_ng_probe_min_journeys_for_early_return))
        if ng_probe.journeys and len(ng_probe.journeys) >= min_early_return:
            return ng_probe
        if (
            bool(probe_config.direct_journey_label_ng_certificate_enabled)
            and bool(ng_probe.exhausted)
            and str(ng_probe.status) == "OPTIMAL"
            and bool(ng_probe.ng_certificate_from_relaxation)
        ):
            return ng_probe
        ng_probe_stats = ng_probe
        if float(config.time_limit) > 0.0:
            remaining = max(0.0, float(config.time_limit) - (time.perf_counter() - profile_call_started))
            if remaining <= 0.0:
                return ng_probe
            config = replace(config, time_limit=remaining)
    direct_branch_safe = (not branch_constraints) or (
        bool(config.direct_journey_label_completion_bound_enabled)
        and _direct_ng_branch_certificate_safe(branch_constraints)
    ) or (
        int(config.direct_journey_label_max_labels_per_node) > 0
        and not bool(config.direct_journey_label_completion_bound_enabled)
    )
    if (
        bool(config.direct_journey_label_pricing_enabled)
        and bool(direct_branch_safe)
        and not bool(data.instance.get("scheduling", {}).get("task_waiting_allowed", True))
    ):
        return _price_journeys_by_direct_labels_with_ng_preprobe(
            data,
            duals,
            config=config,
            cuts=cuts,
            branch_constraints=branch_constraints,
            forbidden_journey_signatures=forbidden_journey_signatures,
            dominant_task_set_costs=dominant_task_set_costs,
            resource_cache=resource_cache,
        )
    if bool(config.streaming_pricing_enabled):
        result = _price_journeys_by_streaming_profiles(
            data,
            duals,
            branch_constraints=branch_constraints,
            config=config,
            cuts=cuts,
            trip_cache=trip_cache,
            resource_cache=resource_cache,
            forbidden_journey_signatures=forbidden_journey_signatures,
            dominant_task_set_costs=dominant_task_set_costs,
        )
        if ng_probe_stats is not None:
            return _merge_ng_probe_pricing_result(
                result,
                ng_probe_stats,
                duals=duals,
                cuts=cuts,
                max_returned=max(1, int(config.max_returned_journeys)),
                eps=float(config.eps),
            )
        return result
    started = time.perf_counter()
    deadline = _pricing_absolute_deadline(started, config)
    generation_deadline = deadline
    if deadline is not None:
        fraction = min(1.0, max(0.05, float(config.profile_generation_time_fraction)))
        if float(config.time_limit) > 0.0:
            generation_deadline = min(float(deadline), started + float(config.time_limit) * fraction)
    vehicle = int(data.vehicles[0])
    trip_duals = FutureDuals(
        cover={int(task): float(value) for task, value in duals.cover.items()},
        task_vehicle={},
        sortie_count={int(vehicle): 0.0},
        time_occupation={},
        ordering={},
        branches={},
        cuts={},
    )
    base = float(data.fixed_vehicle_cost) - float(duals.fleet_limit)
    catalog_stats: dict[str, int] = {}
    dominant_task_set_cost_by_mask = _dominant_task_set_costs_by_mask(data, dominant_task_set_costs)
    generation_started = time.perf_counter()
    profiles, generated, evaluated, best_profile_rc, exhausted, reason, cut_penalty_pruned = _generate_negative_sortie_profiles(
        data,
        trip_duals,
        base_reduced_cost=base,
        config=config,
        trip_cache=trip_cache,
        resource_cache=resource_cache,
        started=started,
        deadline=generation_deadline,
        journey_cut_duals=duals.cuts or {},
        journey_cuts=cuts,
        catalog_stats=catalog_stats,
        branch_constraints=branch_constraints,
    )
    profile_generation_time = time.perf_counter() - generation_started
    if not exhausted and not profiles:
        return JourneyPricingResult(
            [],
            False,
            best_profile_rc,
            generated,
            evaluated,
            len(profiles),
            0,
            "INCOMPLETE",
            reason or "profile_generation_incomplete",
            profile_cut_penalty_pruned=cut_penalty_pruned,
            profile_catalog_hit=bool(catalog_stats.get("hit", 0)),
            profile_catalog_size=int(catalog_stats.get("size", 0)),
            profile_generation_time=profile_generation_time,
            **_resource_stats_kwargs(catalog_stats),
        )
    if not profiles:
        if base < -float(config.eps):
            return JourneyPricingResult(
                [],
                False,
                best_profile_rc,
                generated,
                evaluated,
                0,
                0,
                "INCOMPLETE",
                "negative_fleet_base_requires_profiles",
                profile_cut_penalty_pruned=cut_penalty_pruned,
                profile_catalog_hit=bool(catalog_stats.get("hit", 0)),
                profile_catalog_size=int(catalog_stats.get("size", 0)),
                profile_generation_time=profile_generation_time,
                **_resource_stats_kwargs(catalog_stats),
            )
        return JourneyPricingResult(
            [],
            exhausted,
            None if best_profile_rc is None else base + float(best_profile_rc),
            generated,
            evaluated,
            0,
            0,
            "OPTIMAL" if exhausted else "INCOMPLETE",
            "no_negative_sortie_profile" if exhausted else reason,
            profile_cut_penalty_pruned=cut_penalty_pruned,
            profile_catalog_hit=bool(catalog_stats.get("hit", 0)),
            profile_catalog_size=int(catalog_stats.get("size", 0)),
            profile_generation_time=profile_generation_time,
            **_resource_stats_kwargs(catalog_stats),
            )
    profile_dominance_pruned = 0
    filter_started = time.perf_counter()
    profiles, profile_dominance_pruned = _filter_sortie_profiles_after_generation(profiles, config, catalog_stats)
    profile_filter_time = time.perf_counter() - filter_started
    max_returned = max(1, int(config.max_returned_journeys))
    candidate_return_limit = _profile_candidate_return_limit(config, max_returned)
    dp_stats: dict[str, int] = {}
    dp_started = time.perf_counter()
    selected_candidates, objective, status = _solve_best_journey_profile_dp(
        data,
        profiles,
        base_reduced_cost=base,
        cut_duals=duals.cuts or {},
        cuts=cuts,
        cut_masks=_cut_masks(data, cuts),
        max_states=int(config.max_dp_states),
        deadline=deadline,
        max_returned=candidate_return_limit,
        early_return_negative=bool(config.early_return_negative),
        early_return_min_count=max(1, int(config.early_return_negative_min_count)),
        optimistic_bound_pruning=bool(config.dp_bound_pruning_enabled),
        cross_count_dominance=bool(config.dp_cross_count_dominance_enabled),
        selection_mode=str(config.journey_selection_mode),
        dp_stats=dp_stats,
        forbidden_journey_signatures=forbidden_journey_signatures,
        duplicate_scan_limit=int(config.duplicate_scan_limit),
        dominant_task_set_cost_by_mask=dominant_task_set_cost_by_mask,
        pricing_config=config,
        branch_constraints=branch_constraints,
        eps=float(config.eps),
    )
    profile_dp_time = time.perf_counter() - dp_started
    if status != "OPTIMAL":
        journeys, existing_filtered, weak_filtered = _instantiate_profile_journey_candidates(
            data,
            profiles,
            selected_candidates,
            config,
            eps=float(config.eps),
            forbidden_journey_signatures=forbidden_journey_signatures,
            dominant_task_set_costs=dominant_task_set_costs,
            max_journeys=max_returned,
            branch_constraints=branch_constraints,
            duals=duals,
            cuts=cuts,
            dp_stats=dp_stats,
        )
        if journeys:
            min_returned = max(1, int(config.streaming_min_returned_journeys))
            if len(journeys) < min_returned:
                return None
            return JourneyPricingResult(
                journeys,
                False,
                objective,
                generated,
                evaluated,
                len(profiles),
                max((len(selected) for selected, _obj in selected_candidates), default=0),
                "INCOMPLETE",
                "partial_dp_negative_journey",
                profile_dominance_pruned,
                existing_filtered,
                cut_penalty_pruned,
                weak_filtered,
                dp_stats.get("bound_pruned_labels", 0),
                dp_stats.get("cross_count_pruned_labels", 0),
                bool(catalog_stats.get("hit", 0)),
                int(catalog_stats.get("size", 0)),
                profile_generation_time,
                profile_filter_time,
                profile_dp_time,
                **_resource_stats_kwargs(catalog_stats),
                **_duplicate_stats_kwargs(dp_stats),
                **_profile_mask_diagnostic_kwargs(profiles, dp_stats, config),
            )
        if weak_filtered > 0:
            return JourneyPricingResult(
                [],
                False,
                objective,
                generated,
                evaluated,
                len(profiles),
                max((len(selected) for selected, _obj in selected_candidates), default=0),
                "INCOMPLETE",
                "weak_negative_journeys_filtered",
                profile_dominance_pruned,
                existing_filtered,
                cut_penalty_pruned,
                weak_filtered,
                dp_stats.get("bound_pruned_labels", 0),
                dp_stats.get("cross_count_pruned_labels", 0),
                bool(catalog_stats.get("hit", 0)),
                int(catalog_stats.get("size", 0)),
                profile_generation_time,
                profile_filter_time,
                profile_dp_time,
                **_resource_stats_kwargs(catalog_stats),
                **_duplicate_stats_kwargs(dp_stats),
                **_profile_mask_diagnostic_kwargs(profiles, dp_stats, config),
            )
        return JourneyPricingResult(
            [],
            False,
            objective,
            generated,
            evaluated,
            len(profiles),
            0,
            status,
            _profile_dp_incomplete_reason(status, dp_stats),
            profile_dominance_pruned,
            existing_filtered,
            cut_penalty_pruned,
            weak_filtered,
            dp_stats.get("bound_pruned_labels", 0),
            dp_stats.get("cross_count_pruned_labels", 0),
            bool(catalog_stats.get("hit", 0)),
            int(catalog_stats.get("size", 0)),
            profile_generation_time,
            profile_filter_time,
            profile_dp_time,
            **_resource_stats_kwargs(catalog_stats),
            **_duplicate_stats_kwargs(dp_stats),
            **_profile_mask_diagnostic_kwargs(profiles, dp_stats, config),
        )
    if (objective is None or objective >= -float(config.eps)) and not selected_candidates:
        return JourneyPricingResult(
            [],
            bool(exhausted),
            objective,
            generated,
            evaluated,
            len(profiles),
            0,
            "OPTIMAL" if exhausted else "INCOMPLETE",
            "no_negative_journey" if exhausted else "partial_profile_scan_no_negative_journey",
            profile_dominance_pruned,
            dp_bound_pruned_labels=dp_stats.get("bound_pruned_labels", 0),
            dp_cross_count_pruned_labels=dp_stats.get("cross_count_pruned_labels", 0),
            profile_cut_penalty_pruned=cut_penalty_pruned,
            profile_catalog_hit=bool(catalog_stats.get("hit", 0)),
            profile_catalog_size=int(catalog_stats.get("size", 0)),
            profile_generation_time=profile_generation_time,
            profile_filter_time=profile_filter_time,
            profile_dp_time=profile_dp_time,
            **_resource_stats_kwargs(catalog_stats),
            **_duplicate_stats_kwargs(dp_stats),
            **_profile_mask_diagnostic_kwargs(profiles, dp_stats, config),
        )
    journeys, existing_filtered, weak_filtered = _instantiate_profile_journey_candidates(
        data,
        profiles,
        selected_candidates,
        config,
        eps=float(config.eps),
        forbidden_journey_signatures=forbidden_journey_signatures,
        dominant_task_set_costs=dominant_task_set_costs,
        max_journeys=max_returned,
        branch_constraints=branch_constraints,
        duals=duals,
        cuts=cuts,
        dp_stats=dp_stats,
    )
    if not journeys:
        reason = "selected_profiles_not_a_valid_journey"
        exhausted_for_result = False
        status_for_result = "INCOMPLETE"
        if weak_filtered > 0:
            reason = "weak_negative_journeys_filtered"
        if (
            existing_filtered > 0
            or int(dp_stats.get("duplicate_candidates_filtered", 0)) > 0
            or int(dp_stats.get("dominated_task_set_candidates_filtered", 0)) > 0
        ):
            reason = "negative_journeys_already_in_pool"
        elif weak_filtered <= 0:
            exhausted_for_result = False
        return JourneyPricingResult(
            [],
            exhausted_for_result,
            objective,
            generated,
            evaluated,
            len(profiles),
            0,
            status_for_result,
            reason,
            profile_dominance_pruned,
            existing_filtered,
            cut_penalty_pruned,
            weak_filtered,
            dp_stats.get("bound_pruned_labels", 0),
            dp_stats.get("cross_count_pruned_labels", 0),
            bool(catalog_stats.get("hit", 0)),
            int(catalog_stats.get("size", 0)),
            profile_generation_time,
            profile_filter_time,
            profile_dp_time,
            **_resource_stats_kwargs(catalog_stats),
            **_duplicate_stats_kwargs(dp_stats),
            **_profile_mask_diagnostic_kwargs(profiles, dp_stats, config),
        )
    return JourneyPricingResult(
        journeys,
        bool(exhausted),
        objective,
        generated,
        evaluated,
        len(profiles),
        max((len(selected) for selected, _obj in selected_candidates), default=0),
        "OPTIMAL" if exhausted else "INCOMPLETE",
        "negative_journey" if exhausted else "partial_negative_journey",
        profile_dominance_pruned,
        existing_filtered,
        cut_penalty_pruned,
        weak_filtered,
        dp_stats.get("bound_pruned_labels", 0),
        dp_stats.get("cross_count_pruned_labels", 0),
        bool(catalog_stats.get("hit", 0)),
        int(catalog_stats.get("size", 0)),
        profile_generation_time,
        profile_filter_time,
        profile_dp_time,
        **_resource_stats_kwargs(catalog_stats),
        **_duplicate_stats_kwargs(dp_stats),
        **_profile_mask_diagnostic_kwargs(profiles, dp_stats, config),
    )


def _price_journeys_by_direct_ng_dssr(
    data: FutureData,
    duals: JourneyDuals,
    *,
    config: JourneyPricingConfig,
    cuts: tuple[FutureCut, ...],
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
    forbidden_journey_signatures: set[tuple] | frozenset[tuple] | None = None,
    dominant_task_set_costs: dict[frozenset[int], float] | None = None,
    fallback_to_elementary: bool = True,
) -> JourneyPricingResult:
    """Run ng-route/DSSR as an exact-safe direct-label front-end.

    V1 uses the relaxation to find valid elementary negative journeys and to
    identify repeated-task conflicts for DSSR memory growth.  Unless
    ``direct_journey_label_ng_certificate_enabled`` is explicitly enabled, a
    no-negative relaxed result falls through to the existing elementary labeler
    so the official certificate path remains unchanged.
    """

    fallback_to_elementary = bool(fallback_to_elementary) and not branch_constraints
    if fallback_to_elementary and not (
        bool(config.allow_partial_negative)
        or bool(config.direct_journey_label_ng_certificate_enabled)
        or bool(config.direct_journey_label_ng_exact_probe_enabled)
    ):
        return _price_journeys_by_direct_labels(
            data,
            duals,
            config=replace(config, direct_journey_label_ng_dssr_enabled=False),
            cuts=cuts,
            branch_constraints=branch_constraints,
            forbidden_journey_signatures=forbidden_journey_signatures,
            dominant_task_set_costs=dominant_task_set_costs,
        )

    started = time.perf_counter()
    deadline = _pricing_absolute_deadline(started, config)
    task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
    trip_duals = FutureDuals(
        cover={int(task): float(value) for task, value in duals.cover.items()},
        task_vehicle={},
        sortie_count={int(data.vehicles[0]): 0.0},
        time_occupation={},
        ordering={},
        branches={},
        cuts={},
    )
    task_order = _task_order(data, trip_duals, int(data.vehicles[0]), PricingConfig(heuristic=False, heuristic_top_tasks=0))
    neighborhoods = _direct_ng_neighborhoods(data, ng_size=int(config.direct_journey_label_ng_memory_size))
    memory = frozenset(
        int(task) for task in data.tasks[: max(0, int(config.direct_journey_label_dssr_initial_memory_size))]
    )
    all_tasks = frozenset(int(task) for task in data.tasks)
    stats = _DirectNGStats()
    selected: list[JourneyColumn] = []
    best_candidate_rc: float | None = None
    stop_reason = ""
    exhausted = True

    max_iterations = max(1, int(config.direct_journey_label_dssr_max_iterations))
    for iteration in range(1, max_iterations + 1):
        stats.iterations = iteration
        remaining = 0.0 if deadline is None else max(0.0, deadline - time.perf_counter())
        if deadline is not None and remaining <= 0.0:
            exhausted = False
            stop_reason = "ng_dssr_time_limit"
            break
        iteration_result = _direct_ng_relaxed_iteration(
            data,
            duals,
            task_order,
            task_to_bit,
            neighborhoods,
            memory=memory,
            config=config,
            cuts=cuts,
            branch_constraints=branch_constraints,
            forbidden_journey_signatures=forbidden_journey_signatures,
            dominant_task_set_costs=dominant_task_set_costs,
            deadline=None if deadline is None else time.perf_counter() + remaining,
        )
        stats.label_pops += int(iteration_result.label_pops)
        stats.generated_labels += int(iteration_result.generated_labels)
        stats.state_count += int(iteration_result.state_count)
        stats.evaluated_timed_trips += int(iteration_result.evaluated_timed_trips)
        stats.dominance_pruned_labels += int(iteration_result.dominance_pruned_labels)
        stats.non_elementary_negative += len(iteration_result.repeated_negative_tasks)
        stats.memory_size = len(memory)
        if iteration_result.best_relaxed_reduced_cost is not None:
            stats.best_relaxed_reduced_cost = (
                float(iteration_result.best_relaxed_reduced_cost)
                if stats.best_relaxed_reduced_cost is None
                else min(float(stats.best_relaxed_reduced_cost), float(iteration_result.best_relaxed_reduced_cost))
            )
        if iteration_result.journeys:
            selected = iteration_result.journeys
            best_candidate_rc = iteration_result.best_candidate_reduced_cost
            exhausted = False
            stop_reason = "ng_dssr_elementary_negative_journey"
            break
        if not iteration_result.exhausted:
            exhausted = False
            stop_reason = iteration_result.stop_reason or "ng_dssr_incomplete"
            break
        if (
            iteration_result.best_relaxed_reduced_cost is None
            or float(iteration_result.best_relaxed_reduced_cost) >= -float(config.eps)
        ):
            if bool(config.direct_journey_label_ng_certificate_enabled):
                return JourneyPricingResult(
                    [],
                    True,
                    iteration_result.best_relaxed_reduced_cost,
                    iteration_result.generated_labels,
                    iteration_result.evaluated_timed_trips,
                    iteration_result.state_count,
                    0,
                    "OPTIMAL",
                    "ng_dssr_relaxed_no_negative_journey",
                    profile_generation_time=time.perf_counter() - started,
                    global_certificate_capable=True,
                    pricing_state=PRICING_STATE_CERTIFIED_NO_NEGATIVE,
                    **_direct_ng_stats_kwargs(stats, fallback=False, certificate=True),
                )
            stop_reason = "ng_dssr_relaxed_no_negative_fallback"
            break

        grow = set(int(task) for task in iteration_result.repeated_negative_tasks)
        growth = max(1, int(config.direct_journey_label_dssr_memory_growth))
        if len(grow) < growth:
            scored = sorted(
                (abs(float(duals.cover.get(int(task), 0.0))), int(task))
                for task in data.tasks
                if int(task) not in memory
            )
            for _score, task in reversed(scored):
                grow.add(int(task))
                if len(grow) >= growth:
                    break
        new_memory = frozenset(set(memory) | grow)
        if new_memory == memory:
            exhausted = False
            stop_reason = "ng_dssr_negative_no_memory_growth"
            break
        memory = new_memory
        stats.memory_size = len(memory)
        if memory == all_tasks:
            continue
    else:
        exhausted = False
        stop_reason = "ng_dssr_iteration_limit"

    if selected:
        selected = selected[: max(1, int(config.max_returned_journeys))]
        return JourneyPricingResult(
            selected,
            False,
            best_candidate_rc,
            stats.generated_labels,
            stats.evaluated_timed_trips,
            stats.state_count,
            max((len(journey.trips) for journey in selected), default=0),
            "INCOMPLETE",
            stop_reason or "ng_dssr_elementary_negative_journey",
            profile_generation_time=time.perf_counter() - started,
            **_direct_ng_stats_kwargs(stats, fallback=False, certificate=False),
        )

    if not fallback_to_elementary:
        return JourneyPricingResult(
            [],
            False,
            stats.best_relaxed_reduced_cost,
            stats.generated_labels,
            stats.evaluated_timed_trips,
            stats.state_count,
            0,
            "INCOMPLETE",
            stop_reason or ("ng_dssr_exhausted_no_candidate" if exhausted else "ng_dssr_no_candidate"),
            profile_generation_time=time.perf_counter() - started,
            **_direct_ng_stats_kwargs(stats, fallback=False, certificate=False),
        )

    fallback_config = replace(config, direct_journey_label_ng_dssr_enabled=False)
    fallback = _price_journeys_by_direct_labels(
        data,
        duals,
        config=fallback_config,
        cuts=cuts,
        branch_constraints=branch_constraints,
        forbidden_journey_signatures=forbidden_journey_signatures,
        dominant_task_set_costs=dominant_task_set_costs,
    )
    return replace(fallback, **_direct_ng_stats_kwargs(stats, fallback=True, certificate=False))


def _direct_ng_stats_kwargs(
    stats: _DirectNGStats,
    *,
    fallback: bool,
    certificate: bool,
) -> dict[str, Any]:
    return {
        "ng_relaxation_enabled": True,
        "ng_dssr_iterations": int(stats.iterations),
        "ng_memory_size": int(stats.memory_size),
        "ng_non_elementary_negative": int(stats.non_elementary_negative),
        "ng_label_pops": int(stats.label_pops),
        "ng_generated_labels": int(stats.generated_labels),
        "ng_dominance_pruned_labels": int(stats.dominance_pruned_labels),
        "ng_fallback_to_elementary": bool(fallback),
        "ng_certificate_from_relaxation": bool(certificate),
        "ng_relaxation_superset": True if bool(certificate) else None,
        "ng_best_relaxed_reduced_cost": stats.best_relaxed_reduced_cost,
    }


def _direct_ng_neighborhoods(data: FutureData, *, ng_size: int) -> dict[int, frozenset[int]]:
    size = max(1, int(ng_size))
    neighborhoods: dict[int, frozenset[int]] = {}
    for task in data.tasks:
        task = int(task)
        candidates: list[tuple[float, int]] = []
        for other in data.tasks:
            other = int(other)
            if other == task:
                continue
            options = data.options(task, other)
            best = min(options, key=lambda option: (float(option.cost), float(option.tau), float(option.energy)))
            score = float(best.cost) + 0.01 * float(best.tau)
            candidates.append((score, other))
        selected = {task}
        for _score, other in sorted(candidates)[: max(0, size - 1)]:
            selected.add(int(other))
        neighborhoods[task] = frozenset(selected)
    return neighborhoods


def _direct_ng_initial_partial(data: FutureData) -> _SortiePartialLabel:
    return _SortiePartialLabel(
        sequence=tuple(),
        mask=0,
        last=0,
        partial=_PartialNoWaitingPathProfile(
            arc_options=tuple(),
            lower_start=0.0,
            upper_start=float(data.horizon),
            offset=0.0,
            travel_cost=0.0,
            travel_energy=0.0,
            service_cost=0.0,
            service_energy=0.0,
        ),
    )


def _direct_ng_boundary_memory(label: _DirectNGJourneyLabel) -> frozenset[int]:
    """Return NG memory after a depot/recharge boundary between sorties."""

    return frozenset(int(task) for task in label.dssr_seen)


def _direct_ng_label_key(
    label: _DirectNGJourneyLabel,
    *,
    task_to_bit: dict[int, int] | None = None,
    include_visit_mask: bool = False,
    include_current_sequence: bool = True,
) -> tuple[Any, ...]:
    current_component: Any
    if bool(include_current_sequence):
        current_component = tuple(int(task) for task in label.current.sequence)
    else:
        current_component = int(label.current.mask)
    key: tuple[Any, ...] = (
        label.dssr_seen,
        label.ng_memory,
        current_component,
        int(label.current.last),
        len(label.completed),
    )
    if bool(include_visit_mask):
        if task_to_bit is None:
            raise ValueError("task_to_bit is required when include_visit_mask=True")
        key = (*key, _direct_ng_unique_mask(label.visits, task_to_bit))
    return key


def _direct_ng_label_dominates(left: _DirectNGJourneyLabel, right: _DirectNGJourneyLabel) -> bool:
    return bool(
        float(left.ready_time) <= float(right.ready_time) + 1.0e-9
        and float(left.value) <= float(right.value) + 1.0e-9
        and float(left.current.partial.offset) <= float(right.current.partial.offset) + 1.0e-9
        and float(left.current.partial.travel_cost) <= float(right.current.partial.travel_cost) + 1.0e-9
        and float(left.current.partial.travel_energy) <= float(right.current.partial.travel_energy) + 1.0e-9
        and float(left.current.partial.service_cost) <= float(right.current.partial.service_cost) + 1.0e-9
        and float(left.current.partial.service_energy) <= float(right.current.partial.service_energy) + 1.0e-9
    )


def _direct_ng_repeated_tasks(visits: tuple[int, ...]) -> set[int]:
    seen: set[int] = set()
    repeated: set[int] = set()
    for task in visits:
        task = int(task)
        if task in seen:
            repeated.add(task)
        seen.add(task)
    return repeated


def _direct_ng_visits_elementary(visits: tuple[int, ...]) -> bool:
    return len(visits) == len(set(int(task) for task in visits))


def _direct_ng_unique_mask(visits: tuple[int, ...], task_to_bit: dict[int, int]) -> int:
    mask = 0
    for task in set(int(task) for task in visits):
        mask |= 1 << int(task_to_bit[int(task)])
    return mask


def _direct_ng_partial_branch_pruning_safe(constraints: tuple[BranchConstraint, ...]) -> bool:
    """Return whether branch rows can be checked one-sided on a partial mask."""

    return all(
        constraint.kind in {"same_vehicle", "separate_vehicle"} and constraint.task_j is not None
        for constraint in constraints
    )


def _direct_ng_branch_certificate_safe(constraints: tuple[BranchConstraint, ...]) -> bool:
    """Return whether NG relaxed no-negative can certify a branch-pricing call."""

    return _direct_ng_partial_branch_pruning_safe(constraints)


def _direct_ng_label_priority(
    base_reduced_cost: float,
    label: _DirectNGJourneyLabel,
    duals: JourneyDuals,
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
    task_to_bit: dict[int, int],
) -> float:
    current_dual = sum(float(duals.cover.get(int(task), 0.0)) for task in label.current.sequence)
    optimistic = (
        float(base_reduced_cost)
        + float(label.value)
        + float(label.current.partial.travel_cost)
        + float(label.current.partial.service_cost)
        - float(current_dual)
    )
    if label.visits:
        mask = _direct_ng_unique_mask(label.visits, task_to_bit)
        optimistic -= _journey_cut_dual_value_cached(int(mask), duals.cuts or {}, cuts, cut_masks, {})
    return optimistic


def _direct_ng_relaxed_iteration(
    data: FutureData,
    duals: JourneyDuals,
    task_order: tuple[int, ...],
    task_to_bit: dict[int, int],
    neighborhoods: dict[int, frozenset[int]],
    *,
    memory: frozenset[int],
    config: JourneyPricingConfig,
    cuts: tuple[FutureCut, ...],
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
    forbidden_journey_signatures: set[tuple] | frozenset[tuple] | None = None,
    dominant_task_set_costs: dict[frozenset[int], float] | None = None,
    deadline: float | None = None,
) -> _DirectNGIterationResult:
    base = float(data.fixed_vehicle_cost) - float(duals.fleet_limit)
    cut_masks = _cut_masks(data, cuts)
    cut_duals = duals.cuts or {}
    candidates: dict[tuple, tuple[float, JourneyColumn]] = {}
    repeated_negative: set[int] = set()
    best_relaxed_rc: float | None = None
    label_pops = 0
    generated_labels = 0
    dominance_pruned = 0
    evaluated = 0
    state_count = 1
    exhausted = True
    stop_reason = ""
    max_labels = int(config.direct_journey_label_ng_max_labels)
    if max_labels <= 0:
        max_labels = int(config.max_dp_states)
    target_negative_journeys = max(
        1,
        min(
            max(1, int(config.max_returned_journeys)),
            max(1, int(config.direct_journey_label_ng_min_negative_journeys)),
        ),
    )
    max_sortie_tasks = _max_tasks_per_trip(data, int(config.max_tasks_per_trip))
    forbidden = forbidden_journey_signatures or set()
    start = _DirectNGJourneyLabel(
        ready_time=0.0,
        value=0.0,
        dssr_seen=frozenset(),
        ng_memory=frozenset(),
        visits=tuple(),
        completed=tuple(),
        current=_direct_ng_initial_partial(data),
    )
    heap: list[tuple[float, int, float, int, _DirectNGJourneyLabel]] = [(0.0, 0, 0.0, 0, start)]
    serial = 0
    include_visit_mask_in_dominance = bool(
        config.direct_journey_label_ng_visit_mask_dominance_enabled
        or config.direct_journey_label_ng_certificate_enabled
    )
    include_current_sequence_in_dominance = bool(config.direct_journey_label_ng_sequence_key_enabled)
    partial_branch_pruning_safe = _direct_ng_partial_branch_pruning_safe(branch_constraints)
    dominance_buckets: dict[tuple[Any, ...], list[_DirectNGJourneyLabel]] = {
        _direct_ng_label_key(
            start,
            task_to_bit=task_to_bit,
            include_visit_mask=include_visit_mask_in_dominance,
            include_current_sequence=include_current_sequence_in_dominance,
        ): [start]
    }

    def active(label: _DirectNGJourneyLabel) -> bool:
        if not bool(config.direct_journey_label_ng_dominance_enabled):
            return True
        return any(
            old is label
            for old in dominance_buckets.get(
                _direct_ng_label_key(
                    label,
                    task_to_bit=task_to_bit,
                    include_visit_mask=include_visit_mask_in_dominance,
                    include_current_sequence=include_current_sequence_in_dominance,
                ),
                [],
            )
        )

    def dominated(label: _DirectNGJourneyLabel) -> bool:
        nonlocal dominance_pruned
        if not bool(config.direct_journey_label_ng_dominance_enabled):
            return False
        key = _direct_ng_label_key(
            label,
            task_to_bit=task_to_bit,
            include_visit_mask=include_visit_mask_in_dominance,
            include_current_sequence=include_current_sequence_in_dominance,
        )
        bucket = dominance_buckets.setdefault(key, [])
        if any(_direct_ng_label_dominates(old, label) for old in bucket):
            dominance_pruned += 1
            return True
        survivors: list[_DirectNGJourneyLabel] = []
        for old in bucket:
            if _direct_ng_label_dominates(label, old):
                dominance_pruned += 1
                continue
            survivors.append(old)
        survivors.append(label)
        dominance_buckets[key] = survivors
        return False

    def push(label: _DirectNGJourneyLabel) -> bool:
        nonlocal generated_labels, serial, state_count, exhausted, stop_reason
        if deadline is not None and time.perf_counter() > deadline:
            exhausted = False
            stop_reason = "ng_dssr_time_limit"
            return False
        if max_labels > 0 and generated_labels >= max_labels:
            exhausted = False
            stop_reason = "ng_dssr_label_limit"
            return False
        if dominated(label):
            return True
        generated_labels += 1
        state_count += 1
        serial += 1
        heapq.heappush(
            heap,
            (
                round(_direct_ng_label_priority(base, label, duals, cuts, cut_masks, task_to_bit), 9),
                len(label.completed),
                round(float(label.ready_time) + float(label.current.partial.offset), 9),
                serial,
                label,
            ),
        )
        return True

    def record_completed_sortie(label: _DirectNGJourneyLabel) -> bool:
        nonlocal best_relaxed_rc, evaluated
        if not label.current.sequence:
            return True
        options = data.options(int(label.current.last), 0)
        if not options:
            return True
        dual_sum = sum(float(duals.cover.get(int(task), 0.0)) for task in label.current.sequence)
        for option in options:
            if deadline is not None and time.perf_counter() > deadline:
                return False
            completed_partial = _complete_no_waiting_partial(data, label.current.partial, option)
            if completed_partial is None:
                continue
            profile = completed_partial.profile
            start_time = max(float(label.ready_time), float(profile.lower_start))
            if start_time > float(profile.upper_start) + 1.0e-9:
                continue
            trip = evaluate_timed_trip(
                data,
                label.current.sequence,
                start_time,
                time_bucket_size=float(config.time_bucket_size),
                arc_options=completed_partial.arc_options,
                include_physical_paths=False,
            )
            evaluated += 1
            if trip is None:
                continue
            contribution = float(profile.cost) - float(dual_sum)
            new_value = round(float(label.value) + float(contribution), 9)
            new_visits = tuple(int(task) for task in label.visits)
            new_mask = _direct_ng_unique_mask(new_visits, task_to_bit)
            relaxed_rc = float(base) + float(new_value) - _journey_cut_dual_value_cached(
                int(new_mask),
                cut_duals,
                cuts,
                cut_masks,
                {},
            )
            best_relaxed_rc = relaxed_rc if best_relaxed_rc is None else min(float(best_relaxed_rc), float(relaxed_rc))
            new_completed = (*label.completed, trip)
            if relaxed_rc < -float(config.eps):
                if _direct_ng_visits_elementary(new_visits):
                    journey = make_journey(data, new_completed)
                    if (
                        journey is not None
                        and journey.signature not in forbidden
                        and _journey_task_set_branch_allowed(journey.task_set, branch_constraints)
                        and not _journey_task_set_cost_dominated(journey, dominant_task_set_costs)
                    ):
                        add_threshold = max(float(config.eps), float(config.min_add_reduced_cost))
                        if relaxed_rc < -add_threshold:
                            old = candidates.get(journey.signature)
                            if old is None or relaxed_rc < old[0] - 1.0e-9:
                                candidates[journey.signature] = (relaxed_rc, journey)
                else:
                    repeated_negative.update(_direct_ng_repeated_tasks(new_visits))
            if len(new_completed) < int(data.sortie_limit):
                next_label = _DirectNGJourneyLabel(
                    ready_time=float(trip.end_time),
                    value=new_value,
                    dssr_seen=label.dssr_seen,
                    ng_memory=(
                        _direct_ng_boundary_memory(label)
                        if bool(config.direct_journey_label_ng_reset_memory_between_sorties_enabled)
                        or bool(config.direct_journey_label_ng_certificate_enabled)
                        else label.ng_memory
                    ),
                    visits=new_visits,
                    completed=new_completed,
                    current=_direct_ng_initial_partial(data),
                )
                if not push(next_label):
                    return False
        return True

    def unique_candidate_task_sets() -> int:
        return len({frozenset(int(task) for task in journey.task_set) for _rc, journey in candidates.values()})

    while heap:
        if deadline is not None and time.perf_counter() > deadline:
            exhausted = False
            stop_reason = "ng_dssr_time_limit"
            break
        _priority, _count, _time_key, _serial, label = heapq.heappop(heap)
        if not active(label):
            continue
        label_pops += 1
        if max_labels > 0 and label_pops > max_labels:
            exhausted = False
            stop_reason = "ng_dssr_label_limit"
            break
        if not record_completed_sortie(label):
            exhausted = False
            stop_reason = "ng_dssr_time_limit"
            break
        if unique_candidate_task_sets() >= target_negative_journeys:
            break
        if len(label.current.sequence) >= max_sortie_tasks:
            continue
        for task in task_order:
            task = int(task)
            if task in label.current.sequence:
                continue
            if task in label.dssr_seen or task in label.ng_memory:
                continue
            sequence = (*label.current.sequence, task)
            if not _sequence_resource_precheck(data, sequence):
                continue
            options = data.options(int(label.current.last), task)
            if not options:
                continue
            global_bit = 1 << int(task_to_bit[task])
            local_mask = int(label.current.mask) | int(global_bit)
            for option in options:
                if deadline is not None and time.perf_counter() > deadline:
                    exhausted = False
                    stop_reason = "ng_dssr_time_limit"
                    break
                extended = _extend_no_waiting_partial(
                    data,
                    sequence,
                    len(label.current.sequence),
                    label.current.partial,
                    option,
                )
                if extended is None:
                    continue
                next_dssr_seen = label.dssr_seen | ({task} if task in memory else set())
                next_ng_memory = frozenset((label.ng_memory & neighborhoods[task]) | {task} | next_dssr_seen)
                next_visits = (*label.visits, task)
                if partial_branch_pruning_safe and not _journey_mask_branch_allowed(
                    _direct_ng_unique_mask(next_visits, task_to_bit),
                    branch_constraints,
                    task_to_bit,
                    final=False,
                ):
                    continue
                next_label = _DirectNGJourneyLabel(
                    ready_time=label.ready_time,
                    value=label.value,
                    dssr_seen=frozenset(next_dssr_seen),
                    ng_memory=next_ng_memory,
                    visits=next_visits,
                    completed=label.completed,
                    current=_SortiePartialLabel(
                        sequence=sequence,
                        mask=local_mask,
                        last=task,
                        partial=extended,
                    ),
                )
                if not push(next_label):
                    break
            if not exhausted:
                break
        if not exhausted:
            break

    selected = []
    seen_task_sets: set[frozenset[int]] = set()
    for item in sorted(candidates.values(), key=lambda item: (round(item[0], 9), item[1].signature)):
        task_key = frozenset(int(task) for task in item[1].task_set)
        if task_key in seen_task_sets:
            continue
        selected.append(item)
        seen_task_sets.add(task_key)
    if int(config.max_returned_journeys) > 0:
        selected = selected[: max(1, int(config.max_returned_journeys))]
    return _DirectNGIterationResult(
        journeys=[journey for _rc, journey in selected],
        exhausted=bool(exhausted),
        best_candidate_reduced_cost=None if not selected else float(selected[0][0]),
        best_relaxed_reduced_cost=best_relaxed_rc,
        stop_reason=stop_reason,
        label_pops=label_pops,
        generated_labels=generated_labels,
        state_count=state_count,
        evaluated_timed_trips=evaluated,
        dominance_pruned_labels=dominance_pruned,
        repeated_negative_tasks=repeated_negative,
    )


def _price_journeys_by_direct_labels(
    data: FutureData,
    duals: JourneyDuals,
    *,
    config: JourneyPricingConfig,
    cuts: tuple[FutureCut, ...],
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
    forbidden_journey_signatures: set[tuple] | frozenset[tuple] | None = None,
    dominant_task_set_costs: dict[frozenset[int], float] | None = None,
    priority_task_sets: set[frozenset[int]] | frozenset[frozenset[int]] | None = None,
    active_support_task_sets: set[frozenset[int]] | frozenset[frozenset[int]] | None = None,
    priority_duals: JourneyDuals | None = None,
    resource_cache: dict[tuple, Any] | None = None,
) -> JourneyPricingResult:
    started = time.perf_counter()
    deadline = _pricing_absolute_deadline(started, config)
    vehicle = int(data.vehicles[0])
    trip_duals = FutureDuals(
        cover={int(task): float(value) for task, value in duals.cover.items()},
        task_vehicle={},
        sortie_count={int(vehicle): 0.0},
        time_occupation={},
        ordering={},
        branches={},
        cuts={},
    )
    task_order_duals = trip_duals
    if priority_duals is not None:
        task_order_duals = FutureDuals(
            cover={int(task): float(value) for task, value in priority_duals.cover.items()},
            task_vehicle={},
            sortie_count={int(vehicle): 0.0},
            time_occupation={},
            ordering={},
            branches={},
            cuts={},
        )
    base = float(data.fixed_vehicle_cost) - float(duals.fleet_limit)
    task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
    task_order = _task_order(data, task_order_duals, vehicle, PricingConfig(heuristic=False, heuristic_top_tasks=0))
    cut_masks = _cut_masks(data, cuts)
    cut_duals = duals.cuts or {}
    cut_value_cache: dict[int, float] = {}
    optimistic_cut_value_cache: dict[int, float] = {}
    profile_cut_penalty_cache: dict[int, float] = {}
    has_nonzero_cut_dual = any(abs(float(value)) > 1.0e-9 for value in cut_duals.values())
    cut_pruning_safe = _profile_cut_penalty_pruning_safe(cut_duals, cuts)
    labels_by_count: list[dict[int, list[_DirectJourneyLabel]]] = [dict() for _ in range(int(data.sortie_limit) + 1)]
    initial = _DirectJourneyLabel(end_time=0.0, value=0.0, mask=0, trips=tuple())
    labels_by_count[0][0] = [initial]
    heap: list[tuple[float, int, float, int, _DirectJourneyLabel]] = [(0.0, 0, 0.0, 0, initial)]
    serial = 0
    generated = 0
    evaluated = 0
    state_count = 1
    best_objective: float | None = None
    candidates: list[tuple[float, JourneyColumn]] = []
    candidate_signatures: set[tuple] = set()
    duplicate_filtered = 0
    weak_filtered = 0
    dominated_task_set_filtered = 0
    forbidden = forbidden_journey_signatures or set()
    exhausted = True
    reason = ""
    next_sortie_cache: dict[int, tuple[list[_SortieProfile], int, int, str]] = {}
    next_sortie_cache_hits = 0
    next_sortie_cache_misses = 0
    use_next_sortie_cache = bool(config.direct_journey_label_next_sortie_cache_enabled)
    direct_label_max_labels_per_node = max(0, int(config.direct_journey_label_max_labels_per_node))
    direct_label_beam_mode = direct_label_max_labels_per_node > 0
    direct_label_cross_count_pruned = 0
    repair_existing_only = bool(config.direct_journey_label_existing_task_set_repair_only)
    new_task_set_only = bool(config.direct_journey_label_new_task_set_only)
    repair_target_masks = _direct_repair_target_masks(
        data,
        task_to_bit,
        dominant_task_set_costs,
        tuple(getattr(config, "direct_journey_label_repair_task_sets", tuple()) or tuple()),
    )
    repair_prefix_cache: dict[int, bool] = {}
    direct_bound_pruned = 0
    completion_lb_pruned = 0
    expanded_before_completion_bound = 0
    expanded_after_completion_bound = 0
    generated_next_sorties_before_bound = 0
    generated_next_sorties_after_bound = 0
    completion_bound_stats: dict[str, int] = {}
    direct_label_harvest_candidate_count = 0
    direct_label_harvest_selected_count = 0
    direct_label_harvest_overlap_deferred = 0
    direct_label_harvest_duplicate_task_set_rejected_count = 0
    direct_label_harvest_fallback_fill_count = 0
    direct_label_harvest_fallback_fill_new_mask_count = 0
    direct_label_harvest_fallback_fill_replacement_count = 0
    direct_label_harvest_fallback_fill_support_changing_count = 0
    direct_label_harvest_fallback_fill_weak_replacement_count = 0
    direct_label_harvest_candidate_new_task_set_count = 0
    direct_label_harvest_selected_new_task_set_count = 0
    direct_label_harvest_selected_replacement_task_set_count = 0
    direct_label_harvest_candidate_priority_task_set_count = 0
    direct_label_harvest_selected_priority_task_set_count = 0
    direct_label_harvest_candidate_support_changing_count = 0
    direct_label_harvest_selected_support_changing_count = 0
    direct_label_harvest_selected_strong_replacement_count = 0
    direct_label_harvest_selected_weak_replacement_count = 0
    direct_label_harvest_task_set_dominance_enabled = False
    direct_label_harvest_task_set_dominance_collapsed_count = 0
    direct_label_mask_closure_candidate_task_set_count = 0
    direct_label_mask_closure_selected_count = 0
    direct_label_mask_closure_selected_task_set_count = 0
    direct_label_harvest_best_true_rc: float | None = None
    direct_label_harvest_worst_selected_true_rc: float | None = None
    direct_label_harvest_avg_pairwise_jaccard: float | None = None
    direct_label_harvest_soft_return_triggered = False
    direct_label_profile_stats: dict[str, int] = {
        "next_sortie_calls": 0,
        "next_sortie_total_ns": 0,
        "partial_heap_pops": 0,
        "extension_attempts": 0,
        "option_attempts": 0,
        "bound_checks": 0,
        "dominance_checks": 0,
        "completion_calls": 0,
        "resource_precheck_ns": 0,
        "extend_ns": 0,
        "bound_check_ns": 0,
        "pre_dominance_checks": 0,
        "pre_dominance_pruned": 0,
        "pre_dominance_ns": 0,
        "dominance_ns": 0,
        "completion_ns": 0,
        "partial_bound_dual_sum_ns": 0,
        "partial_bound_unique_task_ns": 0,
        "partial_bound_unique_route_ns": 0,
        "partial_bound_completion_route_ns": 0,
        "partial_bound_resource_pareto_ns": 0,
        "partial_bound_cut_ns": 0,
        "partial_bucket_count": 0,
        "partial_bucket_label_count": 0,
        "partial_bucket_max_size": 0,
    }
    selected_candidate_cache_len = -1
    selected_candidate_cache: tuple[JourneyColumn, ...] | None = None
    task_set_continuation_bound = None
    completion_bound = None
    rpce_bound: ResourceParetoCompletionEnvelope | None = None
    amcb_bound: AvailableMaskCompletionBound | None = None
    completion_bound_cache_hit = False
    completion_bound_cache_stored = False
    completion_bound_reported_build_time = 0.0
    unique_task_bound = None
    positive_cut_reward_bound = None
    unique_route_bound = None
    if (
        bool(config.direct_journey_label_task_set_bound_pruning_enabled)
        and not has_nonzero_cut_dual
        and len(data.tasks) <= int(config.dp_disjoint_bound_max_tasks)
    ):
        task_set_continuation_bound = _TaskSetContinuationLowerBoundCache(
            _TaskSetReducedCostLowerBoundCache(data, trip_duals, vehicle, task_to_bit),
            task_count=len(data.tasks),
            max_tasks_per_sortie=_max_tasks_per_trip(data, int(config.max_tasks_per_trip)),
            enabled=True,
        )
    completion_bound_cut_safe = _direct_completion_bound_cut_safe(cut_duals, cuts)
    if bool(config.direct_journey_label_completion_bound_enabled) and completion_bound_cut_safe:
        completion_bound_mode = str(config.direct_journey_label_completion_bound_mode or "bucket").strip().lower()
        if completion_bound_mode not in {"bucket", "hybrid", "resource_pareto"}:
            completion_bound_mode = "bucket"
        bucket_completion_enabled = completion_bound_mode in {"bucket", "hybrid"}
        rpce_completion_enabled = bool(
            config.direct_journey_label_resource_pareto_completion_enabled
            or completion_bound_mode == "resource_pareto"
        )
        amcb_completion_enabled = bool(
            config.direct_journey_label_available_mask_completion_bound_enabled
        )
        if bucket_completion_enabled:
            cache_key = None if resource_cache is None else _direct_completion_bound_cache_key(data, duals, config)
            cached = None if cache_key is None else resource_cache.get(cache_key)
            if isinstance(cached, _DirectJourneyCompletionBound):
                completion_bound = cached
                completion_bound_cache_hit = True
                _reset_direct_completion_bound_query_stats(completion_bound)
                completion_bound_reported_build_time = 0.0
            else:
                completion_bound = _DirectJourneyCompletionBound(
                    data,
                    duals,
                    time_buckets=int(config.direct_journey_label_completion_bound_time_buckets),
                    energy_buckets=int(config.direct_journey_label_completion_bound_energy_buckets),
                    max_tasks_per_sortie=_max_tasks_per_trip(data, int(config.max_tasks_per_trip)),
                    sortie_limit=int(data.sortie_limit),
                    two_cycle_enabled=bool(config.direct_journey_label_completion_bound_two_cycle_enabled),
                    two_cycle_max_states=int(config.direct_journey_label_completion_bound_two_cycle_max_states),
                    deadline=deadline,
                )
                completion_bound_reported_build_time = float(completion_bound.build_time)
                if not bool(getattr(completion_bound, "enabled", True)):
                    completion_bound = None
                if (
                    cache_key is not None
                    and resource_cache is not None
                    and completion_bound is not None
                    and _direct_completion_bound_cacheable(completion_bound)
                ):
                    resource_cache[cache_key] = completion_bound
                    completion_bound_cache_stored = True
        if rpce_completion_enabled and (deadline is None or time.perf_counter() <= float(deadline)):
            rpce_bound = ResourceParetoCompletionEnvelope(
                data,
                duals,
                max_tasks_per_sortie=_max_tasks_per_trip(data, int(config.max_tasks_per_trip)),
                sortie_limit=int(data.sortie_limit),
                max_front_size=int(config.direct_journey_label_resource_pareto_completion_max_front_size),
                time_eps=float(config.direct_journey_label_resource_pareto_completion_time_eps),
                energy_eps=float(config.direct_journey_label_resource_pareto_completion_energy_eps),
                load_eps=float(config.direct_journey_label_resource_pareto_completion_load_eps),
                rc_eps=float(config.direct_journey_label_resource_pareto_completion_rc_eps),
                lazy_enabled=bool(config.direct_journey_label_resource_pareto_completion_lazy_enabled),
                deadline=deadline,
            )
        if amcb_completion_enabled and (deadline is None or time.perf_counter() <= float(deadline)):
            amcb_bound = AvailableMaskCompletionBound(
                data,
                duals,
                task_to_bit,
                max_tasks_per_sortie=_max_tasks_per_trip(data, int(config.max_tasks_per_trip)),
                sortie_limit=int(data.sortie_limit),
                max_subset_size=int(config.direct_journey_label_available_mask_completion_bound_max_subset_size),
                max_states=int(config.direct_journey_label_available_mask_completion_bound_max_states),
                deadline=deadline,
            )
        if deadline is None or time.perf_counter() <= float(deadline):
            if bool(config.direct_journey_label_completion_bound_unique_task_helper_enabled):
                unique_task_bound = _UniqueTaskVisitLowerBound(data, trip_duals, task_to_bit)
            positive_cut_reward_bound = _PositiveSubsetCutRewardBound(
                task_count=len(data.tasks),
                cut_duals=cut_duals,
                cuts=cuts,
                cut_masks=cut_masks,
            )
            if bool(config.direct_journey_label_completion_bound_unique_route_helper_enabled):
                unique_route_bound = _UniqueRouteCompletionLowerBound(
                    data,
                    trip_duals,
                    task_to_bit,
                    max_tasks_per_sortie=_max_tasks_per_trip(data, int(config.max_tasks_per_trip)),
                    sortie_limit=int(data.sortie_limit),
                    time_buckets=int(config.direct_journey_label_completion_bound_time_buckets),
                    energy_buckets=int(config.direct_journey_label_completion_bound_energy_buckets),
                    exact_first_step_enabled=bool(
                        config.direct_journey_label_completion_bound_unique_route_exact_first_step_enabled
                    ),
                    exact_first_step_bucket_diagnostics_enabled=bool(
                        config.direct_journey_label_profile_timing_enabled
                    ),
                    exact_mask_limit=int(config.direct_journey_label_completion_bound_unique_route_max_tasks),
                    cache_state_limit=int(
                        config.direct_journey_label_completion_bound_unique_route_cache_max_states
                    ),
                    deadline=deadline,
                )
            # Sortie-level completion pruning depends on the current journey label
            # value, sortie count, and end time.  A profile cache keyed only by
            # used_mask would mix bounds from different parents.  Journey-level
            # suffix pruning is parent-specific but runs after cached profiles are
            # instantiated, so it can still safely use the cache when partial
            # pruning is disabled.
            if bool(config.direct_journey_label_completion_bound_partial_pruning_enabled):
                use_next_sortie_cache = False
    if (
        completion_bound is None
        and rpce_bound is None
        and amcb_bound is None
        and completion_bound_cut_safe
        and (deadline is None or time.perf_counter() <= float(deadline))
        and (
            bool(config.direct_journey_label_completion_bound_unique_task_helper_enabled)
            or bool(config.direct_journey_label_completion_bound_unique_route_helper_enabled)
        )
    ):
        if bool(config.direct_journey_label_completion_bound_unique_task_helper_enabled):
            unique_task_bound = _UniqueTaskVisitLowerBound(data, trip_duals, task_to_bit)
        positive_cut_reward_bound = _PositiveSubsetCutRewardBound(
            task_count=len(data.tasks),
            cut_duals=cut_duals,
            cuts=cuts,
            cut_masks=cut_masks,
        )
        if bool(config.direct_journey_label_completion_bound_unique_route_helper_enabled):
            unique_route_bound = _UniqueRouteCompletionLowerBound(
                data,
                trip_duals,
                task_to_bit,
                max_tasks_per_sortie=_max_tasks_per_trip(data, int(config.max_tasks_per_trip)),
                sortie_limit=int(data.sortie_limit),
                time_buckets=int(config.direct_journey_label_completion_bound_time_buckets),
                energy_buckets=int(config.direct_journey_label_completion_bound_energy_buckets),
                exact_first_step_enabled=bool(
                    config.direct_journey_label_completion_bound_unique_route_exact_first_step_enabled
                ),
                exact_first_step_bucket_diagnostics_enabled=bool(config.direct_journey_label_profile_timing_enabled),
                exact_mask_limit=int(config.direct_journey_label_completion_bound_unique_route_max_tasks),
                cache_state_limit=int(config.direct_journey_label_completion_bound_unique_route_cache_max_states),
                deadline=deadline,
            )
        if bool(config.direct_journey_label_completion_bound_partial_pruning_enabled):
            use_next_sortie_cache = False

    def _repair_prefix_allowed(mask: int) -> bool:
        """Worker-only filter for existing task-set physical repairs.

        In repair mode the direct-label worker is not trying to discover a
        global no-column certificate.  It searches only prefixes that can still
        end at a task set already represented in the journey pool, so any
        negative column it returns is a lower-cost physical replacement for an
        existing RMP direction.  A miss from this restricted universe is always
        uncertified.
        """

        if not repair_existing_only:
            return True
        mask = int(mask)
        if mask <= 0:
            return True
        cached = repair_prefix_cache.get(mask)
        if cached is not None:
            return bool(cached)
        allowed = any((mask & ~int(target_mask)) == 0 for target_mask in repair_target_masks)
        repair_prefix_cache[mask] = bool(allowed)
        return bool(allowed)

    def _repair_final_mask_allowed(mask: int) -> bool:
        if not repair_existing_only:
            return True
        return int(mask) in repair_target_masks

    def _new_task_set_final_mask_allowed(mask: int) -> bool:
        if not new_task_set_only:
            return True
        if int(mask) <= 0:
            return False
        if not repair_target_masks:
            return True
        return int(mask) not in repair_target_masks

    def _selected_unique_task_set_candidates() -> list[JourneyColumn]:
        nonlocal direct_label_harvest_candidate_count
        nonlocal direct_label_harvest_selected_count
        nonlocal direct_label_harvest_overlap_deferred
        nonlocal direct_label_harvest_duplicate_task_set_rejected_count
        nonlocal direct_label_harvest_fallback_fill_count
        nonlocal direct_label_harvest_fallback_fill_new_mask_count
        nonlocal direct_label_harvest_fallback_fill_replacement_count
        nonlocal direct_label_harvest_fallback_fill_support_changing_count
        nonlocal direct_label_harvest_fallback_fill_weak_replacement_count
        nonlocal direct_label_harvest_candidate_new_task_set_count
        nonlocal direct_label_harvest_selected_new_task_set_count
        nonlocal direct_label_harvest_selected_replacement_task_set_count
        nonlocal direct_label_harvest_candidate_priority_task_set_count
        nonlocal direct_label_harvest_selected_priority_task_set_count
        nonlocal direct_label_harvest_candidate_support_changing_count
        nonlocal direct_label_harvest_selected_support_changing_count
        nonlocal direct_label_harvest_selected_strong_replacement_count
        nonlocal direct_label_harvest_selected_weak_replacement_count
        nonlocal direct_label_harvest_task_set_dominance_enabled
        nonlocal direct_label_harvest_task_set_dominance_collapsed_count
        nonlocal direct_label_mask_closure_candidate_task_set_count
        nonlocal direct_label_mask_closure_selected_count
        nonlocal direct_label_mask_closure_selected_task_set_count
        nonlocal direct_label_harvest_best_true_rc
        nonlocal direct_label_harvest_worst_selected_true_rc
        nonlocal direct_label_harvest_avg_pairwise_jaccard
        nonlocal selected_candidate_cache_len
        nonlocal selected_candidate_cache
        # This helper is polled repeatedly by early-return checks while the
        # exact direct-label search is running.  The selected batch is a pure
        # function of the current candidate list and static config, so reuse the
        # last selection until a new true-RC candidate is appended.
        if selected_candidate_cache_len == len(candidates) and selected_candidate_cache is not None:
            return list(selected_candidate_cache)
        if bool(config.direct_journey_label_diverse_harvest_enabled):
            selection = _select_diverse_journey_candidates(
                candidates,
                max_returned=max(1, int(config.max_returned_journeys)),
                top_k_strongest=int(config.direct_journey_label_diverse_harvest_top_k_strongest),
                min_fill=int(config.direct_journey_label_diverse_harvest_min_fill),
                min_new_task_sets=int(config.direct_journey_label_diverse_harvest_min_new_task_sets),
                min_priority_task_sets=int(config.direct_journey_label_diverse_harvest_min_priority_task_sets),
                max_jaccard=float(config.direct_journey_label_diverse_harvest_overlap_threshold),
                max_containment=float(config.direct_journey_label_diverse_harvest_max_containment),
                dominant_task_set_costs=dominant_task_set_costs,
                existing_task_sets=set(dominant_task_set_costs or {}),
                priority_task_sets=set(priority_task_sets or set()),
                priority_overlap_threshold=float(
                    config.direct_journey_label_diverse_harvest_priority_overlap_threshold
                ),
                support_aware_enabled=bool(
                    config.direct_journey_label_diverse_harvest_support_aware_enabled
                ),
                support_task_sets=set(active_support_task_sets or set()),
                support_overlap_threshold=float(
                    config.direct_journey_label_diverse_harvest_support_overlap_threshold
                ),
                replacement_cap=int(config.direct_journey_label_diverse_harvest_replacement_cap),
                strong_replacement_threshold=float(
                    config.direct_journey_label_diverse_harvest_strong_replacement_threshold
                ),
                mask_closure_enabled=bool(config.direct_journey_label_mask_closure_enabled),
                mask_closure_max_masks=int(config.direct_journey_label_mask_closure_max_masks),
                mask_closure_max_columns_per_mask=int(
                    config.direct_journey_label_mask_closure_max_columns_per_mask
                ),
                prefer_new_task_sets=True,
                allow_duplicate_task_sets=bool(
                    config.direct_journey_label_diverse_harvest_allow_duplicate_task_sets
                ),
            )
            direct_label_harvest_candidate_count = int(selection.candidate_negative_count)
            direct_label_harvest_selected_count = int(selection.selected_count)
            direct_label_harvest_overlap_deferred = int(selection.rejected_overlap_count)
            direct_label_harvest_duplicate_task_set_rejected_count = int(
                selection.rejected_duplicate_task_set_count
            )
            direct_label_harvest_fallback_fill_count = int(selection.fallback_fill_count)
            direct_label_harvest_fallback_fill_new_mask_count = int(selection.fallback_fill_new_mask_count)
            direct_label_harvest_fallback_fill_replacement_count = int(selection.fallback_fill_replacement_count)
            direct_label_harvest_fallback_fill_support_changing_count = int(
                selection.fallback_fill_support_changing_count
            )
            direct_label_harvest_fallback_fill_weak_replacement_count = int(
                selection.fallback_fill_weak_replacement_count
            )
            direct_label_harvest_candidate_new_task_set_count = int(selection.candidate_new_task_set_count)
            direct_label_harvest_selected_new_task_set_count = int(selection.selected_new_task_set_count)
            direct_label_harvest_selected_replacement_task_set_count = int(
                selection.selected_replacement_task_set_count
            )
            direct_label_harvest_candidate_priority_task_set_count = int(
                selection.candidate_priority_task_set_count
            )
            direct_label_harvest_selected_priority_task_set_count = int(
                selection.selected_priority_task_set_count
            )
            direct_label_harvest_candidate_support_changing_count = int(
                selection.candidate_support_changing_count
            )
            direct_label_harvest_selected_support_changing_count = int(
                selection.selected_support_changing_count
            )
            direct_label_harvest_selected_strong_replacement_count = int(
                selection.selected_strong_replacement_count
            )
            direct_label_harvest_selected_weak_replacement_count = int(
                selection.selected_weak_replacement_count
            )
            direct_label_harvest_task_set_dominance_enabled = bool(selection.task_set_dominance_enabled)
            direct_label_harvest_task_set_dominance_collapsed_count = int(
                selection.task_set_dominance_collapsed_count
            )
            direct_label_mask_closure_candidate_task_set_count = int(
                selection.mask_closure_candidate_task_set_count
            )
            direct_label_mask_closure_selected_count = int(selection.mask_closure_selected_count)
            direct_label_mask_closure_selected_task_set_count = int(
                selection.mask_closure_selected_task_set_count
            )
            direct_label_harvest_best_true_rc = selection.best_true_rc
            direct_label_harvest_worst_selected_true_rc = selection.worst_selected_true_rc
            direct_label_harvest_avg_pairwise_jaccard = selection.avg_pairwise_jaccard
            selected_candidate_cache_len = len(candidates)
            selected_candidate_cache = tuple(selection.journeys)
            return list(selected_candidate_cache)
        best_by_task_set: dict[frozenset[int], tuple[float, JourneyColumn]] = {}
        for objective, journey in candidates:
            key = frozenset(int(task) for task in getattr(journey, "task_set", tuple()))
            old = best_by_task_set.get(key)
            if old is None or (float(objective), journey.signature) < (float(old[0]), old[1].signature):
                best_by_task_set[key] = (float(objective), journey)
        selected_with_objective = sorted(
            best_by_task_set.values(),
            key=lambda item: (round(float(item[0]), 9), item[1].signature),
        )
        selected = [journey for _objective, journey in selected_with_objective[: max(1, int(config.max_returned_journeys))]]
        direct_label_harvest_candidate_count = len(selected_with_objective)
        direct_label_harvest_selected_count = len(selected)
        direct_label_harvest_overlap_deferred = 0
        direct_label_harvest_duplicate_task_set_rejected_count = 0
        direct_label_harvest_fallback_fill_count = 0
        direct_label_harvest_fallback_fill_new_mask_count = 0
        direct_label_harvest_fallback_fill_replacement_count = 0
        direct_label_harvest_fallback_fill_support_changing_count = 0
        direct_label_harvest_fallback_fill_weak_replacement_count = 0
        existing_keys = set(dominant_task_set_costs or {})
        direct_label_harvest_candidate_new_task_set_count = sum(
            1 for _objective, journey in selected_with_objective if _journey_column_task_set(journey) not in existing_keys
        )
        direct_label_harvest_selected_new_task_set_count = sum(
            1 for journey in selected if _journey_column_task_set(journey) not in existing_keys
        )
        direct_label_harvest_selected_replacement_task_set_count = (
            len(selected) - direct_label_harvest_selected_new_task_set_count
        )
        priority_keys = {frozenset(int(task) for task in task_set) for task_set in (priority_task_sets or set())}
        priority_overlap = min(
            1.0,
            max(0.0, float(config.direct_journey_label_diverse_harvest_priority_overlap_threshold)),
        )

        def is_priority_task_set(task_set: frozenset[int]) -> bool:
            normalized = frozenset(int(task) for task in task_set)
            if normalized in priority_keys:
                return True
            return any(_task_set_jaccard(normalized, priority) >= priority_overlap for priority in priority_keys)

        direct_label_harvest_candidate_priority_task_set_count = sum(
            1 for _objective, journey in selected_with_objective
            if is_priority_task_set(_journey_column_task_set(journey))
        )
        direct_label_harvest_selected_priority_task_set_count = sum(
            1 for journey in selected if is_priority_task_set(_journey_column_task_set(journey))
        )
        direct_label_harvest_candidate_support_changing_count = 0
        direct_label_harvest_selected_support_changing_count = 0
        direct_label_harvest_selected_strong_replacement_count = 0
        direct_label_harvest_selected_weak_replacement_count = 0
        direct_label_harvest_task_set_dominance_enabled = bool(dominant_task_set_costs)
        direct_label_harvest_task_set_dominance_collapsed_count = 0
        direct_label_mask_closure_candidate_task_set_count = 0
        direct_label_mask_closure_selected_count = 0
        direct_label_mask_closure_selected_task_set_count = 0
        objectives = [float(objective) for objective, _journey in selected_with_objective]
        selected_objectives = [float(objective) for objective, _journey in selected_with_objective[: len(selected)]]
        direct_label_harvest_best_true_rc = None if not objectives else min(objectives)
        direct_label_harvest_worst_selected_true_rc = None if not selected_objectives else max(selected_objectives)
        direct_label_harvest_avg_pairwise_jaccard = _avg_pairwise_journey_task_jaccard(selected)
        selected_candidate_cache_len = len(candidates)
        selected_candidate_cache = tuple(selected)
        return list(selected_candidate_cache)

    def _unique_candidate_task_set_count() -> int:
        return len(
            {
                frozenset(int(task) for task in getattr(journey, "task_set", tuple()))
                for _objective, journey in candidates
            }
        )

    def _selected_new_task_set_target_met() -> bool:
        target = max(0, int(config.direct_journey_label_diverse_harvest_soft_return_min_new_task_sets))
        if target <= 0:
            return True
        return int(direct_label_harvest_selected_new_task_set_count) >= int(target)

    direct_early_return_grace_deadline: float | None = None

    def _direct_negative_early_return_ready() -> bool:
        nonlocal direct_early_return_grace_deadline
        nonlocal direct_label_harvest_soft_return_triggered
        if not bool(config.direct_journey_label_early_return_negative):
            return False
        max_returned = max(1, int(config.max_returned_journeys))
        configured_early_return_count = int(config.direct_journey_label_early_return_negative_min_count)
        early_return_count = (
            max_returned
            if configured_early_return_count <= 0
            else max(1, min(max_returned, configured_early_return_count))
        )
        if bool(config.direct_journey_label_diverse_harvest_enabled):
            unique_count = len(_selected_unique_task_set_candidates())
        else:
            unique_count = _unique_candidate_task_set_count()
        if not _selected_new_task_set_target_met():
            return False
        if unique_count < early_return_count:
            if bool(config.direct_journey_label_diverse_harvest_enabled):
                soft_min = int(config.direct_journey_label_diverse_harvest_soft_return_min_count)
                soft_after = float(config.direct_journey_label_diverse_harvest_soft_return_after_time)
                soft_remaining = float(config.direct_journey_label_diverse_harvest_soft_return_remaining_time)
                now = time.perf_counter()
                remaining = None if deadline is None else float(deadline) - float(now)
                if _direct_label_diverse_harvest_soft_return_ready(
                    completion_bound_enabled=completion_bound is not None or rpce_bound is not None or amcb_bound is not None,
                    completion_bound_elapsed_soft_return_enabled=bool(
                        config.direct_journey_label_completion_bound_elapsed_soft_return_enabled
                    ),
                    unique_count=int(unique_count),
                    candidate_count=int(direct_label_harvest_candidate_count),
                    new_task_set_count=int(direct_label_harvest_selected_new_task_set_count),
                    max_returned=int(max_returned),
                    soft_min=int(soft_min),
                    soft_min_new_task_sets=int(
                        config.direct_journey_label_diverse_harvest_soft_return_min_new_task_sets
                    ),
                    soft_after=float(soft_after),
                    soft_remaining=float(soft_remaining),
                    duplicate_saturation_after_time=float(
                        config.direct_journey_label_diverse_harvest_duplicate_saturation_after_time
                    ),
                    elapsed=float(now) - float(started),
                    remaining=remaining,
                ):
                    direct_label_harvest_soft_return_triggered = True
                    return True
            return False
        if unique_count >= max_returned:
            return True
        grace_time = max(0.0, float(config.direct_journey_label_early_return_negative_grace_time))
        if grace_time <= 0.0:
            return True
        now = time.perf_counter()
        if direct_early_return_grace_deadline is None:
            direct_early_return_grace_deadline = now + grace_time
            return False
        return now >= float(direct_early_return_grace_deadline)

    def _record_negative_label(label: _DirectJourneyLabel, objective: float) -> bool:
        nonlocal duplicate_filtered, weak_filtered, dominated_task_set_filtered
        if not label.trips:
            return False
        if not _repair_final_mask_allowed(int(label.mask)):
            return False
        if not _new_task_set_final_mask_allowed(int(label.mask)):
            dominated_task_set_filtered += 1
            return False
        # Direct-label completion may use lightweight profile contributions
        # before a segment is materialized.  Close-to-zero rough objectives can
        # therefore hide a true-RC negative journey.  Only skip labels that are
        # clearly non-negative; otherwise materialize and apply the exact
        # reduced-cost formula below.
        if float(objective) >= max(1.0e-1, float(config.eps)):
            return False
        timed_trips = _materialize_direct_sortie_segments(data, label.trips, config)
        if not timed_trips:
            return False
        journey = make_journey(data, timed_trips)
        if journey is None:
            return False
        exact_objective = manual_journey_reduced_cost(journey, duals, cuts)
        if float(exact_objective) >= -float(config.eps):
            return False
        if journey.signature in forbidden:
            duplicate_filtered += 1
            return False
        if not _journey_task_set_branch_allowed(journey.task_set, branch_constraints):
            duplicate_filtered += 1
            return False
        if _journey_task_set_cost_dominated(journey, dominant_task_set_costs):
            dominated_task_set_filtered += 1
            return False
        add_threshold = max(float(config.eps), float(config.min_add_reduced_cost))
        if float(exact_objective) >= -add_threshold:
            weak_filtered += 1
            return False
        if journey.signature not in candidate_signatures:
            candidates.append((float(exact_objective), journey))
            candidate_signatures.add(journey.signature)
        return _direct_negative_early_return_ready()

    def _direct_label_mask_diagnostic_kwargs(selected: list[JourneyColumn] | None = None) -> dict[str, Any]:
        selected = selected or []
        return {
            "diagnostic_reachable_task_masks": frozenset(
                int(mask)
                for labels_by_mask in labels_by_count[1:]
                for mask in labels_by_mask.keys()
                if int(mask) > 0
            ),
            "diagnostic_negative_task_masks": frozenset(
                _task_set_mask_from_tasks(task_to_bit, getattr(journey, "task_set", ()))
                for _objective, journey in candidates
            ),
            "diagnostic_selected_task_masks": frozenset(
                _task_set_mask_from_tasks(task_to_bit, getattr(journey, "task_set", ())) for journey in selected
            ),
        }

    def _completion_bound_kwargs() -> dict[str, Any]:
        rpce_stats = {} if rpce_bound is None else rpce_bound.stats()
        amcb_stats = {} if amcb_bound is None else amcb_bound.stats()
        amcb_partial_winners = int(completion_bound_stats.get("partial_pruned_available_mask_winner", 0))
        amcb_suffix_winners = int(completion_bound_stats.get("suffix_pruned_available_mask_winner", 0))
        amcb_skipped_by_unique_route = (
            amcb_bound is not None
            and unique_route_bound is not None
            and bool(getattr(unique_route_bound, "enabled", True))
        )
        return {
            "completion_bound_enabled": completion_bound is not None or rpce_bound is not None or amcb_bound is not None,
            "global_certificate_capable": bool(config.direct_journey_label_global_certificate_enabled),
            "completion_bound_cache_hit": bool(completion_bound_cache_hit),
            "completion_bound_cache_stored": bool(completion_bound_cache_stored),
            "bound_build_time": float(completion_bound_reported_build_time),
            "lb_state_count": 0 if completion_bound is None else int(completion_bound.state_count),
            "lb_min_value": None if completion_bound is None else completion_bound.lb_min_value,
            "lb_mean_value": None if completion_bound is None else completion_bound.lb_mean_value,
            "lb_negative_state_count": 0 if completion_bound is None else int(completion_bound.lb_negative_state_count),
            "expanded_labels_before_bound": int(expanded_before_completion_bound),
            "expanded_labels_after_bound": int(expanded_after_completion_bound),
            "lb_pruned_labels": int(completion_lb_pruned),
            "lb_partial_pruned_labels": int(completion_bound_stats.get("partial_pruned_labels", 0)),
            "lb_suffix_pruned_labels": int(completion_bound_stats.get("suffix_pruned_labels", 0)),
            "lb_partial_pruned_no_outgoing": int(completion_bound_stats.get("partial_pruned_no_outgoing", 0)),
            "lb_partial_pruned_unique_route_infeasible": int(
                completion_bound_stats.get("partial_pruned_unique_route_infeasible", 0)
            ),
            "lb_partial_pruned_completion_route_infeasible": int(
                completion_bound_stats.get("partial_pruned_completion_route_infeasible", 0)
            ),
            "lb_partial_pruned_unique_task_winner": int(
                completion_bound_stats.get("partial_pruned_unique_task_winner", 0)
            ),
            "lb_partial_pruned_unique_route_winner": int(
                completion_bound_stats.get("partial_pruned_unique_route_winner", 0)
            ),
            "lb_partial_pruned_completion_route_winner": int(
                completion_bound_stats.get("partial_pruned_completion_route_winner", 0)
            ),
            "lb_partial_pruned_resource_pareto_winner": int(
                completion_bound_stats.get("partial_pruned_resource_pareto_winner", 0)
            ),
            "lb_partial_pruned_resource_pareto_infeasible": int(
                completion_bound_stats.get("partial_pruned_resource_pareto_infeasible", 0)
            ),
            "lb_partial_pruned_available_mask_winner": int(amcb_partial_winners),
            "lb_partial_pruned_route_finish_winner": int(
                completion_bound_stats.get("partial_pruned_route_finish_winner", 0)
            ),
            "lb_suffix_pruned_unique_task_winner": int(
                completion_bound_stats.get("suffix_pruned_unique_task_winner", 0)
            ),
            "lb_suffix_pruned_unique_route_winner": int(
                completion_bound_stats.get("suffix_pruned_unique_route_winner", 0)
            ),
            "lb_suffix_pruned_completion_route_winner": int(
                completion_bound_stats.get("suffix_pruned_completion_route_winner", 0)
            ),
            "lb_suffix_pruned_resource_pareto_winner": int(
                completion_bound_stats.get("suffix_pruned_resource_pareto_winner", 0)
            ),
            "lb_suffix_pruned_available_mask_winner": int(amcb_suffix_winners),
            "lb_partial_cut_reward_positive_checks": int(
                completion_bound_stats.get("partial_cut_reward_positive_checks", 0)
            ),
            "lb_suffix_cut_reward_positive_checks": int(
                completion_bound_stats.get("suffix_cut_reward_positive_checks", 0)
            ),
            "amcb_enabled": amcb_bound is not None,
            "amcb_build_time": round(float(amcb_stats.get("build_time", 0.0)), 9),
            "amcb_query_count": int(amcb_stats.get("query_count", 0)),
            "amcb_pruned_labels": int(amcb_partial_winners) + int(amcb_suffix_winners),
            "amcb_partial_winner_count": int(amcb_partial_winners),
            "amcb_suffix_winner_count": int(amcb_suffix_winners),
            "amcb_state_count": int(amcb_stats.get("state_count", 0)),
            "amcb_closed_subset_count": int(amcb_stats.get("closed_subset_count", 0)),
            "amcb_tail_state_count": int(amcb_stats.get("tail_state_count", 0)),
            "amcb_disabled": bool(amcb_stats.get("disabled", False)),
            "amcb_disable_reason": amcb_stats.get("disable_reason", None),
            "amcb_skipped_by_unique_route": bool(amcb_skipped_by_unique_route),
            "amcb_resource_filtered_subsets": int(amcb_stats.get("resource_filtered_subsets", 0)),
            "rpce_enabled": rpce_bound is not None,
            "rpce_build_time": round(float(rpce_stats.get("build_time", 0.0)), 9),
            "rpce_arc_front_count": int(rpce_stats.get("arc_front_count", 0)),
            "rpce_sortie_front_count": int(rpce_stats.get("sortie_front_count", 0)),
            "rpce_tail_front_count": int(rpce_stats.get("tail_front_count", 0)),
            "rpce_overflow_state_count": int(rpce_stats.get("overflow_state_count", 0)),
            "rpce_disabled_state_count": int(rpce_stats.get("disabled_state_count", 0)),
            "rpce_runtime_disabled": bool(rpce_stats.get("runtime_disabled", False)),
            "rpce_disable_reason": rpce_stats.get("disable_reason", None),
            "rpce_query_count": int(rpce_stats.get("query_count", 0)),
            "rpce_query_feasible_count": int(rpce_stats.get("query_feasible_count", 0)),
            "rpce_query_disabled_count": int(rpce_stats.get("query_disabled_count", 0)),
            "rpce_pruned_labels": int(
                completion_bound_stats.get("partial_pruned_resource_pareto_winner", 0)
            )
            + int(completion_bound_stats.get("suffix_pruned_resource_pareto_winner", 0))
            + int(completion_bound_stats.get("partial_pruned_resource_pareto_infeasible", 0)),
            "rpce_resource_infeasible_labels": int(
                completion_bound_stats.get("partial_pruned_resource_pareto_infeasible", 0)
            ),
            "rpce_min_lb": rpce_stats.get("min_lb", None),
            "rpce_mean_lb": rpce_stats.get("mean_lb", None),
            "generated_next_sorties_before_bound": int(generated_next_sorties_before_bound),
            "generated_next_sorties_after_bound": int(generated_next_sorties_after_bound),
            "direct_label_max_labels_per_node": int(direct_label_max_labels_per_node),
            "direct_label_cross_count_pruned_labels": int(direct_label_cross_count_pruned),
            "direct_label_existing_task_set_repair_only": bool(repair_existing_only),
            "direct_label_new_task_set_only": bool(new_task_set_only),
            "direct_label_completion_bound_unique_route_exact_first_step_enabled": bool(
                config.direct_journey_label_completion_bound_unique_route_exact_first_step_enabled
            ),
            "direct_label_completion_bound_unique_route_max_tasks": int(
                config.direct_journey_label_completion_bound_unique_route_max_tasks
            ),
            "direct_label_completion_bound_unique_route_cache_max_states": int(
                config.direct_journey_label_completion_bound_unique_route_cache_max_states
            ),
            "direct_label_completion_bound_unique_route_enabled": bool(
                unique_route_bound is not None and unique_route_bound.enabled
            ),
            "direct_label_unique_route_cache_budget_exceeded_count": 0
            if unique_route_bound is None
            else int(unique_route_bound.cache_budget_exceeded_count),
            "direct_label_unique_route_future_cache_hits": 0
            if unique_route_bound is None
            else int(unique_route_bound.future_cache_hits),
            "direct_label_unique_route_future_cache_misses": 0
            if unique_route_bound is None
            else int(unique_route_bound.future_cache_misses),
            "direct_label_unique_route_future_cache_size": 0
            if unique_route_bound is None
            else len(unique_route_bound._future_cache),
            "direct_label_unique_route_partial_cache_hits": 0
            if unique_route_bound is None
            else int(unique_route_bound.partial_cache_hits),
            "direct_label_unique_route_partial_cache_misses": 0
            if unique_route_bound is None
            else int(unique_route_bound.partial_cache_misses),
            "direct_label_unique_route_partial_cache_size": 0
            if unique_route_bound is None
            else len(unique_route_bound._partial_cache),
            "direct_label_unique_route_exact_first_step_cache_hits": 0
            if unique_route_bound is None
            else int(unique_route_bound.exact_first_step_cache_hits),
            "direct_label_unique_route_exact_first_step_cache_misses": 0
            if unique_route_bound is None
            else int(unique_route_bound.exact_first_step_cache_misses),
            "direct_label_unique_route_exact_first_step_cache_size": 0
            if unique_route_bound is None
            else len(unique_route_bound._exact_first_step_cache),
            "direct_label_unique_route_exact_first_step_resource_bucket_count": 0
            if unique_route_bound is None
            else len(unique_route_bound._exact_first_step_resource_bucket_keys),
            "direct_label_unique_route_exact_first_step_resource_bucket_revisits": 0
            if unique_route_bound is None
            else int(unique_route_bound.exact_first_step_resource_bucket_revisits),
            "direct_label_profile_timing_enabled": bool(config.direct_journey_label_profile_timing_enabled),
            "direct_label_profile_next_sortie_calls": int(
                direct_label_profile_stats.get("next_sortie_calls", 0)
            ),
            "direct_label_profile_next_sortie_total_time": round(
                float(direct_label_profile_stats.get("next_sortie_total_ns", 0)) / 1.0e9,
                9,
            ),
            "direct_label_profile_partial_heap_pops": int(
                direct_label_profile_stats.get("partial_heap_pops", 0)
            ),
            "direct_label_profile_extension_attempts": int(
                direct_label_profile_stats.get("extension_attempts", 0)
            ),
            "direct_label_profile_option_attempts": int(
                direct_label_profile_stats.get("option_attempts", 0)
            ),
            "direct_label_profile_bound_checks": int(direct_label_profile_stats.get("bound_checks", 0)),
            "direct_label_profile_dominance_checks": int(
                direct_label_profile_stats.get("dominance_checks", 0)
            ),
            "direct_label_profile_completion_calls": int(
                direct_label_profile_stats.get("completion_calls", 0)
            ),
            "direct_label_profile_pre_dominance_checks": int(
                direct_label_profile_stats.get("pre_dominance_checks", 0)
            ),
            "direct_label_profile_pre_dominance_pruned": int(
                direct_label_profile_stats.get("pre_dominance_pruned", 0)
            ),
            "direct_label_profile_resource_precheck_time": round(
                float(direct_label_profile_stats.get("resource_precheck_ns", 0)) / 1.0e9,
                9,
            ),
            "direct_label_profile_extend_time": round(
                float(direct_label_profile_stats.get("extend_ns", 0)) / 1.0e9,
                9,
            ),
            "direct_label_profile_bound_check_time": round(
                float(direct_label_profile_stats.get("bound_check_ns", 0)) / 1.0e9,
                9,
            ),
            "direct_label_profile_pre_dominance_time": round(
                float(direct_label_profile_stats.get("pre_dominance_ns", 0)) / 1.0e9,
                9,
            ),
            "direct_label_profile_dominance_time": round(
                float(direct_label_profile_stats.get("dominance_ns", 0)) / 1.0e9,
                9,
            ),
            "direct_label_profile_completion_time": round(
                float(direct_label_profile_stats.get("completion_ns", 0)) / 1.0e9,
                9,
            ),
            "direct_label_profile_partial_bound_dual_sum_time": round(
                float(direct_label_profile_stats.get("partial_bound_dual_sum_ns", 0)) / 1.0e9,
                9,
            ),
            "direct_label_profile_partial_bound_unique_task_time": round(
                float(direct_label_profile_stats.get("partial_bound_unique_task_ns", 0)) / 1.0e9,
                9,
            ),
            "direct_label_profile_partial_bound_unique_route_time": round(
                float(direct_label_profile_stats.get("partial_bound_unique_route_ns", 0)) / 1.0e9,
                9,
            ),
            "direct_label_profile_partial_bound_completion_route_time": round(
                float(direct_label_profile_stats.get("partial_bound_completion_route_ns", 0)) / 1.0e9,
                9,
            ),
            "direct_label_profile_partial_bound_resource_pareto_time": round(
                float(direct_label_profile_stats.get("partial_bound_resource_pareto_ns", 0)) / 1.0e9,
                9,
            ),
            "direct_label_profile_partial_bound_cut_time": round(
                float(direct_label_profile_stats.get("partial_bound_cut_ns", 0)) / 1.0e9,
                9,
            ),
            "direct_label_profile_partial_bucket_count": int(
                direct_label_profile_stats.get("partial_bucket_count", 0)
            ),
            "direct_label_profile_partial_bucket_label_count": int(
                direct_label_profile_stats.get("partial_bucket_label_count", 0)
            ),
            "direct_label_profile_partial_bucket_max_size": int(
                direct_label_profile_stats.get("partial_bucket_max_size", 0)
            ),
            "direct_label_profile_partial_bucket_mean_size": (
                0.0
                if int(direct_label_profile_stats.get("partial_bucket_count", 0)) <= 0
                else round(
                    float(direct_label_profile_stats.get("partial_bucket_label_count", 0))
                    / float(direct_label_profile_stats.get("partial_bucket_count", 1)),
                    9,
                )
            ),
            "direct_label_diverse_harvest_enabled": bool(config.direct_journey_label_diverse_harvest_enabled),
            "direct_label_harvest_support_aware_enabled": bool(
                config.direct_journey_label_diverse_harvest_support_aware_enabled
            ),
            "direct_label_diverse_harvest_allow_duplicate_task_sets": bool(
                config.direct_journey_label_diverse_harvest_allow_duplicate_task_sets
            ),
            "direct_label_harvest_candidate_count": int(direct_label_harvest_candidate_count),
            "direct_label_harvest_selected_count": int(direct_label_harvest_selected_count),
            "direct_label_harvest_overlap_deferred": int(direct_label_harvest_overlap_deferred),
            "direct_label_harvest_duplicate_task_set_rejected_count": int(
                direct_label_harvest_duplicate_task_set_rejected_count
            ),
            "direct_label_harvest_fallback_fill_count": int(direct_label_harvest_fallback_fill_count),
            "direct_label_harvest_fallback_fill_new_mask_count": int(
                direct_label_harvest_fallback_fill_new_mask_count
            ),
            "direct_label_harvest_fallback_fill_replacement_count": int(
                direct_label_harvest_fallback_fill_replacement_count
            ),
            "direct_label_harvest_fallback_fill_support_changing_count": int(
                direct_label_harvest_fallback_fill_support_changing_count
            ),
            "direct_label_harvest_fallback_fill_weak_replacement_count": int(
                direct_label_harvest_fallback_fill_weak_replacement_count
            ),
            "direct_label_harvest_candidate_new_task_set_count": int(
                direct_label_harvest_candidate_new_task_set_count
            ),
            "direct_label_harvest_selected_new_task_set_count": int(
                direct_label_harvest_selected_new_task_set_count
            ),
            "direct_label_harvest_selected_replacement_task_set_count": int(
                direct_label_harvest_selected_replacement_task_set_count
            ),
            "direct_label_harvest_candidate_priority_task_set_count": int(
                direct_label_harvest_candidate_priority_task_set_count
            ),
            "direct_label_harvest_selected_priority_task_set_count": int(
                direct_label_harvest_selected_priority_task_set_count
            ),
            "direct_label_harvest_candidate_support_changing_count": int(
                direct_label_harvest_candidate_support_changing_count
            ),
            "direct_label_harvest_selected_support_changing_count": int(
                direct_label_harvest_selected_support_changing_count
            ),
            "direct_label_harvest_selected_strong_replacement_count": int(
                direct_label_harvest_selected_strong_replacement_count
            ),
            "direct_label_harvest_selected_weak_replacement_count": int(
                direct_label_harvest_selected_weak_replacement_count
            ),
            "direct_label_harvest_task_set_dominance_enabled": bool(
                direct_label_harvest_task_set_dominance_enabled
            ),
            "direct_label_harvest_task_set_dominance_collapsed_count": int(
                direct_label_harvest_task_set_dominance_collapsed_count
            ),
            "direct_label_mask_closure_enabled": bool(config.direct_journey_label_mask_closure_enabled)
            and not bool(direct_label_harvest_task_set_dominance_enabled),
            "direct_label_mask_closure_candidate_task_set_count": int(
                direct_label_mask_closure_candidate_task_set_count
            ),
            "direct_label_mask_closure_selected_count": int(direct_label_mask_closure_selected_count),
            "direct_label_mask_closure_selected_task_set_count": int(
                direct_label_mask_closure_selected_task_set_count
            ),
            "direct_label_harvest_best_true_rc": direct_label_harvest_best_true_rc,
            "direct_label_harvest_worst_selected_true_rc": direct_label_harvest_worst_selected_true_rc,
            "direct_label_harvest_avg_pairwise_jaccard": direct_label_harvest_avg_pairwise_jaccard,
            "direct_label_harvest_soft_return_triggered": bool(direct_label_harvest_soft_return_triggered),
            "harvest_candidate_negative_count": int(direct_label_harvest_candidate_count),
            "harvest_selected_count": int(direct_label_harvest_selected_count),
            "harvest_rejected_overlap_count": int(direct_label_harvest_overlap_deferred),
            "harvest_rejected_duplicate_task_set_count": int(
                direct_label_harvest_duplicate_task_set_rejected_count
            ),
            "harvest_fallback_fill_count": int(direct_label_harvest_fallback_fill_count),
            "harvest_fallback_fill_new_mask_count": int(direct_label_harvest_fallback_fill_new_mask_count),
            "harvest_fallback_fill_replacement_count": int(
                direct_label_harvest_fallback_fill_replacement_count
            ),
            "harvest_fallback_fill_support_changing_count": int(
                direct_label_harvest_fallback_fill_support_changing_count
            ),
            "harvest_fallback_fill_weak_replacement_count": int(
                direct_label_harvest_fallback_fill_weak_replacement_count
            ),
            "harvest_candidate_new_task_set_count": int(direct_label_harvest_candidate_new_task_set_count),
            "harvest_selected_new_task_set_count": int(direct_label_harvest_selected_new_task_set_count),
            "harvest_selected_replacement_task_set_count": int(
                direct_label_harvest_selected_replacement_task_set_count
            ),
            "harvest_candidate_priority_task_set_count": int(
                direct_label_harvest_candidate_priority_task_set_count
            ),
            "harvest_selected_priority_task_set_count": int(
                direct_label_harvest_selected_priority_task_set_count
            ),
            "harvest_support_aware_enabled": bool(
                config.direct_journey_label_diverse_harvest_support_aware_enabled
            ),
            "harvest_candidate_support_changing_count": int(
                direct_label_harvest_candidate_support_changing_count
            ),
            "harvest_selected_support_changing_count": int(
                direct_label_harvest_selected_support_changing_count
            ),
            "harvest_selected_strong_replacement_count": int(
                direct_label_harvest_selected_strong_replacement_count
            ),
            "harvest_selected_weak_replacement_count": int(
                direct_label_harvest_selected_weak_replacement_count
            ),
            "harvest_task_set_dominance_enabled": bool(direct_label_harvest_task_set_dominance_enabled),
            "harvest_task_set_dominance_collapsed_count": int(
                direct_label_harvest_task_set_dominance_collapsed_count
            ),
            "harvest_mask_closure_enabled": bool(config.direct_journey_label_mask_closure_enabled)
            and not bool(direct_label_harvest_task_set_dominance_enabled),
            "harvest_mask_closure_candidate_task_set_count": int(
                direct_label_mask_closure_candidate_task_set_count
            ),
            "harvest_mask_closure_selected_count": int(direct_label_mask_closure_selected_count),
            "harvest_mask_closure_selected_task_set_count": int(
                direct_label_mask_closure_selected_task_set_count
            ),
            "harvest_best_true_rc": direct_label_harvest_best_true_rc,
            "harvest_worst_selected_true_rc": direct_label_harvest_worst_selected_true_rc,
            "harvest_avg_pairwise_jaccard": direct_label_harvest_avg_pairwise_jaccard,
            "direct_label_resource_coarsening_time_bucket_size": float(
                config.direct_journey_label_resource_coarsening_time_bucket_size
            ),
            "direct_label_resource_coarsening_energy_bucket_size": float(
                config.direct_journey_label_resource_coarsening_energy_bucket_size
            ),
            "two_cycle_enabled": False if completion_bound is None else bool(completion_bound.two_cycle_enabled),
            "two_cycle_table_complete": False if completion_bound is None else bool(completion_bound.two_cycle_table_complete),
            "two_cycle_fallback_to_memoryless": False
            if completion_bound is None
            else bool(completion_bound.two_cycle_fallback_to_memoryless),
            "two_cycle_state_count": 0 if completion_bound is None else int(completion_bound.two_cycle_state_count),
            "two_cycle_blocked_extensions": 0
            if completion_bound is None
            else int(completion_bound.two_cycle_blocked_extensions),
            "two_cycle_second_best_queries": 0
            if completion_bound is None
            else int(completion_bound.two_cycle_second_best_queries),
            "two_cycle_incompatible_queries": 0
            if completion_bound is None
            else int(completion_bound.two_cycle_incompatible_queries),
            "two_cycle_top2_replacements": 0
            if completion_bound is None
            else int(completion_bound.two_cycle_top2_replacements),
            "two_cycle_build_time": 0.0 if completion_bound is None else float(completion_bound.two_cycle_build_time),
        }

    def _record_streamed_next_sortie(
        parent_label: _DirectJourneyLabel,
        trip: _DirectSortieSegment,
        contribution: float,
        trip_mask: int,
    ) -> bool:
        nonlocal best_objective
        if int(parent_label.mask) & int(trip_mask):
            return False
        new_label = _DirectJourneyLabel(
            end_time=float(trip.end_time),
            value=round(float(parent_label.value) + float(contribution), 9),
            mask=int(parent_label.mask) | int(trip_mask),
            trips=(*parent_label.trips, trip),
        )
        if not _journey_mask_branch_allowed(int(new_label.mask), branch_constraints, task_to_bit, final=False):
            return False
        new_label_objective = _direct_journey_objective(
            float(base),
            new_label,
            cut_duals,
            cuts,
            cut_masks,
            cut_value_cache,
        )
        best_objective = (
            float(new_label_objective)
            if best_objective is None
            else min(float(best_objective), float(new_label_objective))
        )
        # This streaming hook is only a negative-column shortcut.  It never
        # certifies no-column status, and it still materializes the candidate
        # journey through `_record_negative_label`, which applies true RC.
        return _record_negative_label(new_label, float(new_label_objective))

    while heap:
        if deadline is not None and time.perf_counter() > deadline:
            exhausted = False
            reason = "time_limit"
            break
        if _direct_negative_early_return_ready():
            selected = _selected_unique_task_set_candidates()
            return JourneyPricingResult(
                selected,
                False,
                best_objective,
                generated,
                evaluated,
                state_count,
                max((len(journey.trips) for journey in selected), default=0),
                "INCOMPLETE",
                "direct_label_partial_negative_journey",
                existing_journeys_filtered=duplicate_filtered,
                weak_negative_journeys_filtered=weak_filtered,
                dp_bound_pruned_labels=direct_bound_pruned + completion_lb_pruned,
                profile_generation_time=time.perf_counter() - started,
                direct_next_sortie_cache_hits=next_sortie_cache_hits,
                direct_next_sortie_cache_misses=next_sortie_cache_misses,
                dominated_task_set_journeys_filtered=dominated_task_set_filtered,
                **_completion_bound_kwargs(),
                **_direct_label_mask_diagnostic_kwargs(selected),
            )
        _priority, count, _end, _serial, label = heapq.heappop(heap)
        if label not in labels_by_count[int(count)].get(int(label.mask), []):
            continue
        objective = _direct_journey_objective(float(base), label, cut_duals, cuts, cut_masks, cut_value_cache)
        best_objective = objective if best_objective is None else min(best_objective, objective)
        if _record_negative_label(label, float(objective)):
            selected = _selected_unique_task_set_candidates()
            return JourneyPricingResult(
                selected,
                False,
                best_objective,
                generated,
                evaluated,
                state_count,
                max((len(journey.trips) for journey in selected), default=0),
                "INCOMPLETE",
                "direct_label_partial_negative_journey",
                existing_journeys_filtered=duplicate_filtered,
                weak_negative_journeys_filtered=weak_filtered,
                dp_bound_pruned_labels=direct_bound_pruned + completion_lb_pruned,
                profile_generation_time=time.perf_counter() - started,
                direct_next_sortie_cache_hits=next_sortie_cache_hits,
                direct_next_sortie_cache_misses=next_sortie_cache_misses,
                dominated_task_set_journeys_filtered=dominated_task_set_filtered,
                **_completion_bound_kwargs(),
                **_direct_label_mask_diagnostic_kwargs(selected),
            )
        if int(count) >= int(data.sortie_limit):
            continue
        if task_set_continuation_bound is not None:
            remaining = int(data.sortie_limit) - int(count)
            continuation = task_set_continuation_bound.value(int(label.mask), remaining)
            if continuation is not None and float(base) + float(label.value) + float(continuation) >= -float(config.eps):
                direct_bound_pruned += 1
                continue
        remaining_threshold = max(0.0, -float(base) - float(label.value)) + float(config.eps)
        if cut_duals and not cut_pruning_safe:
            # Journey-level cut coefficients depend on the final task mask.
            # A sortie that is not attractive by its own contribution can still
            # be part of a negative journey after cut duals are applied.
            if completion_bound is not None and positive_cut_reward_bound is not None:
                remaining_visit_capacity = (
                    (int(data.sortie_limit) - int(count))
                    * _max_tasks_per_trip(data, int(config.max_tasks_per_trip))
                )
                future_cut_reward = positive_cut_reward_bound.value(int(label.mask), int(remaining_visit_capacity))
                suffix_floor = min(0.0, 0.0 if completion_bound.lb_min_value is None else float(completion_bound.lb_min_value))
                remaining_threshold = (
                    max(
                        0.0,
                        -float(base)
                        - float(label.value)
                        - float(suffix_floor)
                        + float(future_cut_reward),
                    )
                    + float(config.eps)
                )
            else:
                remaining_threshold = float("inf")
        if use_next_sortie_cache:
            cached = next_sortie_cache.get(int(label.mask))
            if cached is None:
                next_sortie_cache_misses += 1
                profiles, gen_inc, profile_eval_inc, incomplete_reason = _direct_next_sortie_profiles(
                    data,
                    trip_duals,
                    task_order,
                    task_to_bit,
                    used_mask=int(label.mask),
                    branch_constraints=branch_constraints,
                    config=config,
                    deadline=deadline,
                )
                next_sortie_cache[int(label.mask)] = (profiles, gen_inc, profile_eval_inc, incomplete_reason)
            else:
                next_sortie_cache_hits += 1
                profiles, _cached_gen, _cached_eval, incomplete_reason = cached
                gen_inc = 0
                profile_eval_inc = 0
            next_trips, instantiate_eval_inc, conversion_reason = _direct_sortie_profiles_to_trips(
                data,
                profiles,
                earliest_start=float(label.end_time),
                threshold=remaining_threshold,
                cut_duals=cut_duals,
                cuts=cuts,
                cut_masks=cut_masks,
                cut_pruning_safe=cut_pruning_safe,
                config=config,
                deadline=deadline,
            )
            eval_inc = int(profile_eval_inc) + int(instantiate_eval_inc)
            incomplete_reason = incomplete_reason or conversion_reason
        else:
            active_rpce_bound = (
                rpce_bound
                if rpce_bound is not None and bool(getattr(rpce_bound, "is_available", True))
                else None
            )
            active_amcb_bound = (
                amcb_bound
                if amcb_bound is not None and not bool(getattr(amcb_bound, "disabled", False))
                else None
            )
            next_trips, gen_inc, eval_inc, incomplete_reason, bound_checked_inc, bound_pruned_inc = _direct_next_sortie_trips(
                data,
                trip_duals,
                task_order,
                task_to_bit,
                used_mask=int(label.mask),
                earliest_start=float(label.end_time),
                threshold=remaining_threshold,
                base_reduced_cost=float(base),
                journey_label_value=float(label.value),
                journey_label_mask=int(label.mask),
                journey_label_count=int(count),
                completion_bound=completion_bound,
                rpce_bound=active_rpce_bound,
                amcb_bound=active_amcb_bound,
                unique_task_bound=unique_task_bound,
                unique_route_bound=unique_route_bound,
                positive_cut_reward_bound=positive_cut_reward_bound,
                cut_duals=cut_duals,
                cuts=cuts,
                cut_masks=cut_masks,
                cut_pruning_safe=cut_pruning_safe,
                branch_constraints=branch_constraints,
                config=config,
                deadline=deadline,
                completion_bound_stats=completion_bound_stats,
                cut_value_cache=cut_value_cache,
                optimistic_cut_value_cache=optimistic_cut_value_cache,
                profile_cut_penalty_cache=profile_cut_penalty_cache,
                profile_stats=direct_label_profile_stats,
                completed_trip_callback=(
                    (
                        lambda trip, contribution, trip_mask, parent_label=label: _record_streamed_next_sortie(
                            parent_label,
                            trip,
                            float(contribution),
                            int(trip_mask),
                        )
                    )
                        if (completion_bound is not None or active_rpce_bound is not None or active_amcb_bound is not None)
                        and bool(config.direct_journey_label_early_return_negative)
                        else None
                    ),
            )
            expanded_before_completion_bound += int(bound_checked_inc)
            expanded_after_completion_bound += max(0, int(bound_checked_inc) - int(bound_pruned_inc))
            completion_lb_pruned += int(bound_pruned_inc)
        generated += gen_inc
        evaluated += eval_inc
        generated_next_sorties_before_bound += int(gen_inc)
        generated_next_sorties_after_bound += max(0, int(gen_inc) - int(bound_pruned_inc if not use_next_sortie_cache else 0))
        if incomplete_reason == "direct_label_next_sortie_streaming_negative_journey":
            selected = _selected_unique_task_set_candidates()
            return JourneyPricingResult(
                selected,
                False,
                best_objective,
                generated,
                evaluated,
                state_count,
                max((len(journey.trips) for journey in selected), default=0),
                "INCOMPLETE",
                "direct_label_partial_negative_journey",
                existing_journeys_filtered=duplicate_filtered,
                weak_negative_journeys_filtered=weak_filtered,
                dp_bound_pruned_labels=direct_bound_pruned + completion_lb_pruned,
                profile_generation_time=time.perf_counter() - started,
                direct_next_sortie_cache_hits=next_sortie_cache_hits,
                direct_next_sortie_cache_misses=next_sortie_cache_misses,
                dominated_task_set_journeys_filtered=dominated_task_set_filtered,
                **_completion_bound_kwargs(),
                **_direct_label_mask_diagnostic_kwargs(selected),
            )
        # `_direct_next_sortie_trips` can hit a soft budget after already
        # producing valid completed sortie segments.  Consume those segments
        # before marking the pricing call incomplete; otherwise we throw away
        # columns that were already paid for by the final-probe search.
        drain_limit = len(next_trips)
        if incomplete_reason and next_trips:
            drain_limit = min(
                len(next_trips),
                max(
                    1,
                    max(1, int(config.max_returned_journeys))
                    * max(1, int(config.direct_journey_label_early_return_negative_min_count or 1))
                    * 4,
                ),
            )
            next_trips = sorted(next_trips, key=lambda item: (round(float(item[1]), 9), item[0].signature))[
                :drain_limit
            ]
        for trip, contribution, trip_mask in next_trips:
            if deadline is not None and time.perf_counter() > float(deadline) and not incomplete_reason:
                exhausted = False
                reason = "time_limit"
                break
            if int(label.mask) & int(trip_mask):
                continue
            expanded_before_completion_bound += 1
            new_label = _DirectJourneyLabel(
                end_time=float(trip.end_time),
                value=round(float(label.value) + float(contribution), 9),
                mask=int(label.mask) | int(trip_mask),
                trips=(*label.trips, trip),
            )
            if not _journey_mask_branch_allowed(int(new_label.mask), branch_constraints, task_to_bit, final=False):
                continue
            if not _repair_prefix_allowed(int(new_label.mask)):
                continue
            new_label_objective = _direct_journey_objective(
                float(base),
                new_label,
                cut_duals,
                cuts,
                cut_masks,
                cut_value_cache,
            )
            best_objective = (
                float(new_label_objective)
                if best_objective is None
                else min(float(best_objective), float(new_label_objective))
            )
            active_rpce_bound = (
                rpce_bound
                if rpce_bound is not None and bool(getattr(rpce_bound, "is_available", True))
                else None
            )
            active_amcb_bound = (
                amcb_bound
                if amcb_bound is not None and not bool(getattr(amcb_bound, "disabled", False))
                else None
            )
            if (
                completion_bound is not None
                or active_rpce_bound is not None
                or active_amcb_bound is not None
                or unique_task_bound is not None
                or unique_route_bound is not None
                or positive_cut_reward_bound is not None
            ):
                remaining_sorties = int(data.sortie_limit) - (int(count) + 1)
                if _direct_completed_journey_suffix_bound_prunes(
                    data,
                    new_mask=int(new_label.mask),
                    new_end_time=float(new_label.end_time),
                    new_objective=float(new_label_objective),
                    remaining_sorties=int(remaining_sorties),
                    completion_bound=completion_bound,
                    rpce_bound=active_rpce_bound,
                    amcb_bound=active_amcb_bound,
                    unique_task_bound=unique_task_bound,
                    unique_route_bound=unique_route_bound,
                    positive_cut_reward_bound=positive_cut_reward_bound,
                    max_tasks_per_sortie=_max_tasks_per_trip(data, int(config.max_tasks_per_trip)),
                    cut_duals=cut_duals,
                    cuts=cuts,
                    cut_masks=cut_masks,
                    eps=float(config.eps),
                    completion_bound_stats=completion_bound_stats,
                ):
                    completion_lb_pruned += 1
                    continue
            if _record_negative_label(new_label, float(new_label_objective)):
                selected = _selected_unique_task_set_candidates()
                return JourneyPricingResult(
                    selected,
                    False,
                    best_objective,
                    generated,
                    evaluated,
                    state_count,
                    max((len(journey.trips) for journey in selected), default=0),
                    "INCOMPLETE",
                    "direct_label_partial_negative_journey",
                    existing_journeys_filtered=duplicate_filtered,
                    weak_negative_journeys_filtered=weak_filtered,
                    dp_bound_pruned_labels=direct_bound_pruned + completion_lb_pruned,
                    profile_generation_time=time.perf_counter() - started,
                    direct_next_sortie_cache_hits=next_sortie_cache_hits,
                    direct_next_sortie_cache_misses=next_sortie_cache_misses,
                    dominated_task_set_journeys_filtered=dominated_task_set_filtered,
                    **_completion_bound_kwargs(),
                    **_direct_label_mask_diagnostic_kwargs(selected),
                )
            expanded_after_completion_bound += 1
            added, cross_count_pruned = _add_direct_journey_label_with_cross_count_dominance(
                labels_by_count,
                int(count) + 1,
                int(new_label.mask),
                new_label,
                enabled=bool(config.direct_journey_label_cross_count_dominance_enabled),
                max_labels_per_node=int(direct_label_max_labels_per_node),
                time_bucket_size=float(config.direct_journey_label_resource_coarsening_time_bucket_size),
            )
            direct_label_cross_count_pruned += int(cross_count_pruned)
            state_count += int(added)
            if not added:
                continue
            if int(config.max_dp_states) > 0 and state_count > int(config.max_dp_states):
                exhausted = False
                reason = "direct_label_state_budget"
                break
            priority = _direct_journey_label_priority(
                float(base),
                new_label,
                cut_duals,
                cuts,
                cut_masks,
                cut_value_cache,
            )
            active_rpce_bound = (
                rpce_bound
                if rpce_bound is not None and bool(getattr(rpce_bound, "is_available", True))
                else None
            )
            active_amcb_bound = (
                amcb_bound
                if amcb_bound is not None and not bool(getattr(amcb_bound, "disabled", False))
                else None
            )
            if (
                completion_bound is not None
                or active_rpce_bound is not None
                or active_amcb_bound is not None
                or unique_task_bound is not None
                or unique_route_bound is not None
                or positive_cut_reward_bound is not None
            ):
                remaining_sorties = int(data.sortie_limit) - (int(count) + 1)
                priority, _priority_winner, _priority_cut_reward = _direct_completed_journey_suffix_optimistic_objective(
                    data,
                    new_mask=int(new_label.mask),
                    new_end_time=float(new_label.end_time),
                    new_objective=float(new_label_objective),
                    remaining_sorties=int(remaining_sorties),
                    completion_bound=completion_bound,
                    rpce_bound=active_rpce_bound,
                    amcb_bound=active_amcb_bound,
                    unique_task_bound=unique_task_bound,
                    unique_route_bound=unique_route_bound,
                    positive_cut_reward_bound=positive_cut_reward_bound,
                    max_tasks_per_sortie=_max_tasks_per_trip(data, int(config.max_tasks_per_trip)),
                    cut_duals=cut_duals,
                    cuts=cuts,
                    cut_masks=cut_masks,
                )
            serial += 1
            heapq.heappush(
                heap,
                (
                    round(float(priority), 9),
                    int(count) + 1,
                    round(float(new_label.end_time), 9),
                    serial,
                    new_label,
                ),
            )
        if incomplete_reason:
            exhausted = False
            reason = incomplete_reason
            break
        if not exhausted:
            break
        if not exhausted:
            break

    candidates.sort(key=lambda item: (round(item[0], 9), item[1].signature))
    selected = _selected_unique_task_set_candidates()
    if selected:
        selected_exhausted = (
            bool(exhausted)
            and not bool(direct_label_beam_mode)
            and not bool(repair_existing_only)
            and not bool(new_task_set_only)
        )
        return JourneyPricingResult(
            selected,
            selected_exhausted,
            best_objective,
            generated,
            evaluated,
            state_count,
            max((len(journey.trips) for journey in selected), default=0),
            "OPTIMAL" if selected_exhausted else "INCOMPLETE",
            "direct_label_negative_journey"
            if selected_exhausted
            else reason
            or (
                "direct_label_existing_task_set_repair_negative_journey"
                if repair_existing_only
                else (
                    "direct_label_new_task_set_negative_journey"
                    if new_task_set_only
                    else (
                        "direct_label_beam_negative_journey"
                        if direct_label_beam_mode
                        else "direct_label_partial_negative_journey"
                    )
                )
            ),
            existing_journeys_filtered=duplicate_filtered,
            weak_negative_journeys_filtered=weak_filtered,
            dp_bound_pruned_labels=direct_bound_pruned + completion_lb_pruned,
            profile_generation_time=time.perf_counter() - started,
            direct_next_sortie_cache_hits=next_sortie_cache_hits,
            direct_next_sortie_cache_misses=next_sortie_cache_misses,
            dominated_task_set_journeys_filtered=dominated_task_set_filtered,
            **_completion_bound_kwargs(),
            **_direct_label_mask_diagnostic_kwargs(selected),
        )
    status = (
        "OPTIMAL"
        if exhausted and not direct_label_beam_mode and not repair_existing_only and not new_task_set_only
        else "INCOMPLETE"
    )
    final_reason = (
        "direct_label_no_negative_journey"
        if exhausted and not direct_label_beam_mode and not repair_existing_only and not new_task_set_only
        else (
            "direct_label_existing_task_set_repair_no_negative_journey"
            if exhausted and repair_existing_only
            else (
                "direct_label_new_task_set_no_negative_journey"
                if exhausted and new_task_set_only
                else (
                    "direct_label_beam_no_negative_journey"
                    if exhausted and direct_label_beam_mode
                    else reason or "direct_label_incomplete"
                )
            )
        )
    )
    if weak_filtered > 0:
        status = "INCOMPLETE"
        final_reason = "weak_negative_journeys_filtered"
    if duplicate_filtered > 0 and exhausted:
        final_reason = "negative_journeys_already_in_pool"
    if dominated_task_set_filtered > 0 and not exhausted:
        final_reason = "dominated_task_set_journeys_filtered"
    reported_best_objective = best_objective
    if status == "OPTIMAL" and final_reason == "direct_label_no_negative_journey":
        # `best_objective` tracks optimistic partial/rough label objectives as
        # well as exact materialized journey RCs.  Under completion-bound pruning
        # the optimistic value can be negative even when no valid negative
        # journey exists, so a proven no-column certificate must report a
        # nonnegative best RC to downstream diagnostics.
        reported_best_objective = 0.0
    result = JourneyPricingResult(
        [],
        bool(exhausted)
        and weak_filtered <= 0
        and not bool(direct_label_beam_mode)
        and not bool(repair_existing_only)
        and not bool(new_task_set_only),
        reported_best_objective,
        generated,
        evaluated,
        state_count,
        0,
        status,
        final_reason,
        existing_journeys_filtered=duplicate_filtered,
        weak_negative_journeys_filtered=weak_filtered,
        dp_bound_pruned_labels=direct_bound_pruned + completion_lb_pruned,
        profile_generation_time=time.perf_counter() - started,
        direct_next_sortie_cache_hits=next_sortie_cache_hits,
        direct_next_sortie_cache_misses=next_sortie_cache_misses,
        dominated_task_set_journeys_filtered=dominated_task_set_filtered,
        **_completion_bound_kwargs(),
        **_direct_label_mask_diagnostic_kwargs(),
    )
    if (
        bool(config.direct_journey_label_completion_bound_audit_enabled)
        and bool(config.direct_journey_label_completion_bound_enabled)
        and bool(result.exhausted)
        and result.status == "OPTIMAL"
        and result.reason == "direct_label_no_negative_journey"
    ):
        _audit_direct_completion_bound_certificate(
            data,
            duals,
            config=config,
            cuts=cuts,
            forbidden_journey_signatures=forbidden_journey_signatures,
            dominant_task_set_costs=dominant_task_set_costs,
            eps=float(config.eps),
        )
    return result


def _audit_direct_completion_bound_certificate(
    data: FutureData,
    duals: JourneyDuals,
    *,
    config: JourneyPricingConfig,
    cuts: tuple[FutureCut, ...],
    forbidden_journey_signatures: set[tuple] | frozenset[tuple] | None,
    dominant_task_set_costs: dict[frozenset[int], float] | None,
    eps: float,
) -> None:
    audit_config = replace(
        config,
        direct_journey_label_global_certificate_enabled=False,
        direct_journey_label_completion_bound_enabled=False,
        direct_journey_label_completion_bound_audit_enabled=False,
    )
    audit = _price_journeys_by_direct_labels(
        data,
        duals,
        config=audit_config,
        cuts=cuts,
        forbidden_journey_signatures=forbidden_journey_signatures,
        dominant_task_set_costs=dominant_task_set_costs,
    )
    if not bool(audit.exhausted):
        raise RuntimeError(
            "completion-bound audit failed: bound-off direct pricing did not exhaust "
            f"(status={audit.status}, reason={audit.reason}, best_rc={audit.best_reduced_cost})"
        )
    if audit.journeys or (audit.best_reduced_cost is not None and float(audit.best_reduced_cost) < -float(eps)):
        raise RuntimeError(
            "completion-bound audit failed: bound-off direct pricing found a negative journey "
            f"(status={audit.status}, reason={audit.reason}, best_rc={audit.best_reduced_cost})"
        )


def _increment_completion_bound_stat(stats: dict[str, int] | None, key: str, amount: int = 1) -> None:
    if stats is None:
        return
    stats[key] = int(stats.get(key, 0)) + int(amount)


def _cover_dual_sum_for_mask(
    mask: int,
    duals: FutureDuals,
    task_to_bit: dict[int, int],
    cache: dict[int, float] | None = None,
) -> float:
    mask = int(mask)
    if cache is not None:
        cached = cache.get(mask)
        if cached is not None:
            return float(cached)
    value = 0.0
    for task, bit_index in task_to_bit.items():
        if mask & (1 << int(bit_index)):
            value += float(duals.cover.get(int(task), 0.0))
    if cache is not None:
        cache[mask] = float(value)
    return float(value)


def _direct_next_sortie_trips(
    data: FutureData,
    duals: FutureDuals,
    task_order: tuple[int, ...],
    task_to_bit: dict[int, int],
    *,
    used_mask: int,
    earliest_start: float,
    threshold: float,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
    cut_pruning_safe: bool,
    config: JourneyPricingConfig,
    deadline: float | None,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
    base_reduced_cost: float = 0.0,
    journey_label_value: float = 0.0,
    journey_label_mask: int = 0,
    journey_label_count: int = 0,
    completion_bound: _DirectJourneyCompletionBound | None = None,
    rpce_bound: ResourceParetoCompletionEnvelope | None = None,
    amcb_bound: AvailableMaskCompletionBound | None = None,
    unique_task_bound: _UniqueTaskVisitLowerBound | None = None,
    unique_route_bound: "_UniqueRouteCompletionLowerBound | None" = None,
    positive_cut_reward_bound: "_PositiveSubsetCutRewardBound | None" = None,
    completion_bound_stats: dict[str, int] | None = None,
    cut_value_cache: dict[int, float] | None = None,
    optimistic_cut_value_cache: dict[int, float] | None = None,
    profile_cut_penalty_cache: dict[int, float] | None = None,
    profile_stats: dict[str, int] | None = None,
    completed_trip_callback: Callable[[_DirectSortieSegment, float, int], bool] | None = None,
) -> tuple[list[tuple[_DirectSortieSegment, float, int]], int, int, str, int, int]:
    profile_enabled = profile_stats is not None and bool(config.direct_journey_label_profile_timing_enabled)
    profile_started_ns = time.perf_counter_ns() if profile_enabled else 0
    if profile_enabled:
        profile_stats["next_sortie_calls"] = int(profile_stats.get("next_sortie_calls", 0)) + 1

    def _profile_add(name: str, start_ns: int) -> None:
        if profile_enabled:
            profile_stats[name] = int(profile_stats.get(name, 0)) + (time.perf_counter_ns() - int(start_ns))

    def _profile_inc(name: str, value: int = 1) -> None:
        if profile_enabled:
            profile_stats[name] = int(profile_stats.get(name, 0)) + int(value)

    def _return(
        trips: list[tuple[_DirectSortieSegment, float, int]],
        generated_count: int,
        evaluated_count: int,
        reason: str,
        checked_count: int,
        pruned_count: int,
    ) -> tuple[list[tuple[_DirectSortieSegment, float, int]], int, int, str, int, int]:
        if profile_enabled:
            bucket_sizes = [len(bucket) for bucket in labels_by_key.values()]
            profile_stats["partial_bucket_count"] = int(profile_stats.get("partial_bucket_count", 0)) + len(
                bucket_sizes
            )
            profile_stats["partial_bucket_label_count"] = int(
                profile_stats.get("partial_bucket_label_count", 0)
            ) + sum(bucket_sizes)
            profile_stats["partial_bucket_max_size"] = max(
                int(profile_stats.get("partial_bucket_max_size", 0)),
                max(bucket_sizes, default=0),
            )
            profile_stats["next_sortie_total_ns"] = int(profile_stats.get("next_sortie_total_ns", 0)) + (
                time.perf_counter_ns() - int(profile_started_ns)
            )
        return trips, generated_count, evaluated_count, reason, checked_count, pruned_count

    max_tasks = _max_tasks_per_trip(data, int(config.max_tasks_per_trip))
    initial = _SortiePartialLabel(
        sequence=tuple(),
        mask=0,
        last=0,
        partial=_PartialNoWaitingPathProfile(
            arc_options=tuple(),
            lower_start=0.0,
            upper_start=float(data.horizon),
            offset=0.0,
            travel_cost=0.0,
            travel_energy=0.0,
            service_cost=0.0,
            service_energy=0.0,
        ),
    )
    labels_by_key: dict[tuple[int, int], list[_SortiePartialLabel]] = {(0, 0): [initial]}
    use_dominance_index = len(data.tasks) <= 10
    dominance_index_by_key: dict[tuple[int, int], _SortiePartialDominanceIndex] = (
        {(0, 0): _SortiePartialDominanceIndex(labels_by_key[(0, 0)])}
        if bool(use_dominance_index)
        else {}
    )
    active_label_ids: set[int] = {id(initial)}
    heap: list[tuple[float, int, float, tuple[int, ...], int, _SortiePartialLabel]] = [
        (_sortie_partial_label_priority(initial, duals), 0, 0.0, tuple(), 0, initial)
    ]
    partial_state_count = 1
    partial_max_states = max(0, int(config.direct_journey_label_partial_max_states))
    serial = 0
    generated = 0
    evaluated = 0
    bound_checked = 0
    bound_pruned = 0
    trips_by_signature: dict[tuple, tuple[_DirectSortieSegment, float, int]] = {}
    partial_cover_dual_sum_cache: dict[int, float] = {}
    min_outgoing_completion_arc_cache: dict[tuple[int, int], float | None] = {}
    soft_return_limit = max(0, int(config.direct_journey_label_next_sortie_trip_return_limit))
    available_mask = ((1 << len(data.tasks)) - 1) ^ int(used_mask)
    superset_bound_cache = (
        _TaskSetSupersetLowerBoundCache(
            _TaskSetReducedCostLowerBoundCache(data, duals, int(data.vehicles[0]), task_to_bit),
            task_count=len(data.tasks),
            max_tasks_per_sortie=max_tasks,
            enabled=True,
        )
        if bool(config.profile_labeling_task_set_superset_pruning_enabled) and threshold < float("inf")
        else None
    )
    while heap:
        if deadline is not None and time.perf_counter() > deadline:
            return _return(list(trips_by_signature.values()), generated, evaluated, "time_limit", bound_checked, bound_pruned)
        _priority, _depth, _offset, _seq_key, _serial, label = heapq.heappop(heap)
        _profile_inc("partial_heap_pops")
        if id(label) not in active_label_ids:
            continue
        if len(label.sequence) >= max_tasks:
            continue
        for task in task_order:
            _profile_inc("extension_attempts")
            task = int(task)
            global_bit = 1 << task_to_bit[task]
            if int(used_mask) & global_bit or label.mask & global_bit:
                continue
            sequence = (*label.sequence, task)
            local_mask = label.mask | global_bit
            if not _journey_mask_branch_allowed(
                int(used_mask) | int(local_mask),
                branch_constraints,
                task_to_bit,
                final=False,
            ):
                continue
            if superset_bound_cache is not None:
                superset_lb = superset_bound_cache.value(local_mask, available_mask)
                if superset_lb is not None and superset_lb >= threshold:
                    continue
            _resource_precheck_started_ns = time.perf_counter_ns() if profile_enabled else 0
            if not _sequence_resource_precheck(data, sequence):
                _profile_add("resource_precheck_ns", _resource_precheck_started_ns)
                continue
            _profile_add("resource_precheck_ns", _resource_precheck_started_ns)
            options = data.options(int(label.last), task)
            if not options:
                continue
            for option in options:
                _profile_inc("option_attempts")
                if deadline is not None and time.perf_counter() > deadline:
                    return _return(
                        list(trips_by_signature.values()),
                        generated,
                        evaluated,
                        "time_limit",
                        bound_checked,
                        bound_pruned,
                    )
                _extend_started_ns = time.perf_counter_ns() if profile_enabled else 0
                extended = _extend_no_waiting_partial(data, sequence, len(label.sequence), label.partial, option)
                if extended is None:
                    _profile_add("extend_ns", _extend_started_ns)
                    continue
                _profile_add("extend_ns", _extend_started_ns)
                generated += 1
                if int(config.max_sequences) > 0 and generated > int(config.max_sequences):
                    return _return(
                        list(trips_by_signature.values()),
                        generated,
                        evaluated,
                        "direct_label_sequence_budget",
                        bound_checked,
                        bound_pruned,
                    )
                new_label = _SortiePartialLabel(sequence=sequence, mask=local_mask, last=task, partial=extended)
                label_key = (local_mask, task)
                labels_for_key = labels_by_key.get(label_key)
                if labels_for_key is None:
                    labels_for_key = []
                    labels_by_key[label_key] = labels_for_key
                    if bool(use_dominance_index):
                        dominance_index_by_key[label_key] = _SortiePartialDominanceIndex(labels_for_key)
                dominance_index = dominance_index_by_key.get(label_key)
                if labels_for_key:
                    _profile_inc("pre_dominance_checks")
                    _pre_dominance_started_ns = time.perf_counter_ns() if profile_enabled else 0
                    if _sortie_partial_label_dominated_by_existing(
                        labels_for_key,
                        new_label,
                        generalized=bool(config.generalized_partial_dominance_enabled),
                        time_bucket_size=float(config.direct_journey_label_resource_coarsening_time_bucket_size),
                        energy_bucket_size=float(config.direct_journey_label_resource_coarsening_energy_bucket_size),
                        dominance_index=dominance_index,
                    ):
                        _profile_add("pre_dominance_ns", _pre_dominance_started_ns)
                        _profile_inc("pre_dominance_pruned")
                        continue
                    _profile_add("pre_dominance_ns", _pre_dominance_started_ns)
                active_rpce_bound = (
                    rpce_bound
                    if rpce_bound is not None and bool(getattr(rpce_bound, "is_available", True))
                    else None
                )
                active_amcb_bound = (
                    amcb_bound
                    if amcb_bound is not None and not bool(getattr(amcb_bound, "disabled", False))
                    else None
                )
                if (
                    completion_bound is not None
                    or active_rpce_bound is not None
                    or active_amcb_bound is not None
                    or unique_task_bound is not None
                    or unique_route_bound is not None
                    or positive_cut_reward_bound is not None
                ):
                    bound_checked += 1
                    _profile_inc("bound_checks")
                    _bound_started_ns = time.perf_counter_ns() if profile_enabled else 0
                    pruned_by_completion_bound, completion_bound_priority = _direct_sortie_partial_completion_bound_check(
                        data,
                        duals,
                        new_label,
                        task_to_bit,
                        base_reduced_cost=float(base_reduced_cost),
                        journey_label_value=float(journey_label_value),
                        journey_label_mask=int(journey_label_mask),
                        journey_label_count=int(journey_label_count),
                        earliest_start=float(earliest_start),
                        completion_bound=completion_bound,
                        rpce_bound=active_rpce_bound,
                        amcb_bound=active_amcb_bound,
                        unique_task_bound=unique_task_bound,
                        unique_route_bound=unique_route_bound,
                        positive_cut_reward_bound=positive_cut_reward_bound,
                        max_tasks_per_sortie=max_tasks,
                        cut_duals=cut_duals,
                        cuts=cuts,
                        cut_masks=cut_masks,
                        eps=float(config.eps),
                        completion_bound_stats=completion_bound_stats,
                        optimistic_cut_value_cache=optimistic_cut_value_cache,
                        partial_cover_dual_sum_cache=partial_cover_dual_sum_cache,
                        min_outgoing_completion_arc_cache=min_outgoing_completion_arc_cache,
                        profile_stats=profile_stats if profile_enabled else None,
                    )
                    _profile_add("bound_check_ns", _bound_started_ns)
                    if pruned_by_completion_bound:
                        bound_pruned += 1
                        continue
                else:
                    completion_bound_priority = None
                _profile_inc("dominance_checks")
                _dominance_started_ns = time.perf_counter_ns() if profile_enabled else 0
                if not _add_sortie_partial_label(
                    labels_for_key,
                    new_label,
                    generalized=bool(config.generalized_partial_dominance_enabled),
                    candidate_not_dominated=True,
                    max_labels_per_node=int(config.direct_journey_label_max_labels_per_node),
                    rank_key=lambda item: _sortie_partial_label_priority(item, duals),
                    active_label_ids=active_label_ids,
                    time_bucket_size=float(config.direct_journey_label_resource_coarsening_time_bucket_size),
                    energy_bucket_size=float(config.direct_journey_label_resource_coarsening_energy_bucket_size),
                    dominance_index=dominance_index,
                ):
                    _profile_add("dominance_ns", _dominance_started_ns)
                    continue
                _profile_add("dominance_ns", _dominance_started_ns)
                partial_state_count += 1
                if partial_max_states > 0 and partial_state_count > partial_max_states:
                    return _return(
                        list(trips_by_signature.values()),
                        generated,
                        evaluated,
                        "direct_label_partial_state_budget",
                        bound_checked,
                        bound_pruned,
                    )
                priority = (
                    _sortie_partial_label_priority(new_label, duals)
                    if completion_bound_priority is None
                    else round(float(completion_bound_priority), 9)
                )
                serial += 1
                heapq.heappush(
                    heap,
                    (
                        priority,
                        len(new_label.sequence),
                        round(float(new_label.partial.offset), 9),
                        tuple(int(item) for item in new_label.sequence),
                        serial,
                        new_label,
                    ),
                )
                _profile_inc("completion_calls")
                _completion_started_ns = time.perf_counter_ns() if profile_enabled else 0
                (
                    completed,
                    eval_inc,
                    completion_reason,
                    completion_bound_checked_inc,
                    completion_bound_pruned_inc,
                ) = _complete_direct_sortie_label_trips(
                    data,
                    duals,
                    new_label,
                    config,
                    earliest_start=earliest_start,
                    threshold=threshold,
                    cut_duals=cut_duals,
                    cuts=cuts,
                    cut_masks=cut_masks,
                    cut_pruning_safe=cut_pruning_safe,
                    task_to_bit=task_to_bit,
                    deadline=deadline,
                    base_reduced_cost=float(base_reduced_cost),
                    journey_label_value=float(journey_label_value),
                    journey_label_mask=int(journey_label_mask),
                    journey_label_count=int(journey_label_count),
                    completion_bound=completion_bound,
                    rpce_bound=rpce_bound,
                    amcb_bound=amcb_bound,
                    unique_task_bound=unique_task_bound,
                    unique_route_bound=unique_route_bound,
                    positive_cut_reward_bound=positive_cut_reward_bound,
                    completion_bound_stats=completion_bound_stats,
                    cut_value_cache=cut_value_cache,
                    optimistic_cut_value_cache=optimistic_cut_value_cache,
                    profile_cut_penalty_cache=profile_cut_penalty_cache,
                    partial_cover_dual_sum_cache=partial_cover_dual_sum_cache,
                )
                _profile_add("completion_ns", _completion_started_ns)
                bound_checked += int(completion_bound_checked_inc)
                bound_pruned += int(completion_bound_pruned_inc)
                evaluated += eval_inc
                if completion_reason:
                    return _return(
                        list(trips_by_signature.values()),
                        generated,
                        evaluated,
                        completion_reason,
                        bound_checked,
                        bound_pruned,
                    )
                for trip, contribution, trip_mask in completed:
                    old = trips_by_signature.get(trip.signature)
                    if old is None or contribution < old[1] - 1.0e-9:
                        trips_by_signature[trip.signature] = (trip, contribution, trip_mask)
                        if completed_trip_callback is not None and completed_trip_callback(
                            trip,
                            float(contribution),
                            int(trip_mask),
                        ):
                            return _return(
                                list(trips_by_signature.values()),
                                generated,
                                evaluated,
                                "direct_label_next_sortie_streaming_negative_journey",
                                bound_checked,
                                bound_pruned,
                        )
                if soft_return_limit > 0 and len(trips_by_signature) >= soft_return_limit:
                    return _return(
                        list(trips_by_signature.values()),
                        generated,
                        evaluated,
                        "direct_label_next_sortie_trip_return_limit",
                        bound_checked,
                        bound_pruned,
                    )
                if int(config.max_timed_evaluations) > 0 and evaluated > int(config.max_timed_evaluations):
                    return _return(
                        list(trips_by_signature.values()),
                        generated,
                        evaluated,
                        "direct_label_profile_evaluation_budget",
                        bound_checked,
                        bound_pruned,
                    )
    return _return(list(trips_by_signature.values()), generated, evaluated, "", bound_checked, bound_pruned)


def _direct_min_outgoing_completion_arc_cost(
    data: FutureData,
    last: int,
    available_mask: int,
    task_to_bit: dict[int, int],
) -> float | None:
    targets = [0]
    for task, bit_index in task_to_bit.items():
        if int(available_mask) & (1 << int(bit_index)):
            targets.append(int(task))
    costs: list[float] = []
    for target in targets:
        try:
            options = data.options(int(last), int(target))
        except KeyError:
            continue
        costs.extend(float(option.cost) for option in options)
    if not costs:
        return None
    return min(costs)


def _direct_sortie_partial_completion_bound_check(
    data: FutureData,
    duals: FutureDuals,
    label: _SortiePartialLabel,
    task_to_bit: dict[int, int],
    *,
    base_reduced_cost: float,
    journey_label_value: float,
    journey_label_mask: int,
    journey_label_count: int,
    earliest_start: float,
    completion_bound: _DirectJourneyCompletionBound | None,
    rpce_bound: ResourceParetoCompletionEnvelope | None = None,
    amcb_bound: AvailableMaskCompletionBound | None = None,
    unique_task_bound: _UniqueTaskVisitLowerBound | None,
    unique_route_bound: "_UniqueRouteCompletionLowerBound | None",
    positive_cut_reward_bound: "_PositiveSubsetCutRewardBound | None",
    max_tasks_per_sortie: int,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
    eps: float,
    completion_bound_stats: dict[str, int] | None = None,
    optimistic_cut_value_cache: dict[int, float] | None = None,
    partial_cover_dual_sum_cache: dict[int, float] | None = None,
    min_outgoing_completion_arc_cache: dict[tuple[int, int], float | None] | None = None,
    profile_stats: dict[str, int] | None = None,
) -> tuple[bool, float | None]:
    profile_enabled = profile_stats is not None

    def _profile_add(name: str, start_ns: int) -> None:
        if profile_enabled:
            profile_stats[name] = int(profile_stats.get(name, 0)) + (time.perf_counter_ns() - int(start_ns))

    if not label.sequence:
        return False, None
    start_lb = max(float(earliest_start), float(label.partial.lower_start))
    if start_lb > float(label.partial.upper_start) + 1.0e-9:
        return True, float("inf")
    _dual_sum_started_ns = time.perf_counter_ns() if profile_enabled else 0
    dual_sum = _cover_dual_sum_for_mask(int(label.mask), duals, task_to_bit, partial_cover_dual_sum_cache)
    _profile_add("partial_bound_dual_sum_ns", _dual_sum_started_ns)
    # 当前 partial 已经真实支付的前缀代价。后续完成部分用 unique-task
    # bound 处理，不在这里强制当前节点立即返仓；否则会排除继续加任务的
    # 可行完成方式，剪枝将不再安全。
    sortie_prefix_contribution = (
        float(label.partial.travel_cost)
        + float(label.partial.service_cost)
        - float(dual_sum)
    )
    remaining_sorties = int(data.sortie_limit) - int(journey_label_count) - 1
    remaining_visit_capacity = (
        max(0, int(max_tasks_per_sortie) - len(label.sequence))
        + max(0, int(remaining_sorties)) * max(1, int(max_tasks_per_sortie))
    )
    remaining_lb: float | None = None
    remaining_lb_winner = ""
    available_mask = 0
    if unique_task_bound is not None:
        available_mask = int(unique_task_bound.full_mask) ^ (int(journey_label_mask) | int(label.mask))
    elif unique_route_bound is not None:
        available_mask = int(unique_route_bound.full_mask) ^ (int(journey_label_mask) | int(label.mask))
    elif amcb_bound is not None:
        available_mask = int(amcb_bound.full_mask) ^ (int(journey_label_mask) | int(label.mask))
    if unique_task_bound is not None and remaining_visit_capacity > 0:
        _unique_task_started_ns = time.perf_counter_ns() if profile_enabled else 0
        remaining_lb = unique_task_bound.value(int(available_mask), int(remaining_visit_capacity))
        remaining_lb_winner = "unique_task"
        outgoing_cache_key = (int(label.last), int(available_mask))
        if min_outgoing_completion_arc_cache is not None and outgoing_cache_key in min_outgoing_completion_arc_cache:
            outgoing_arc_lb = min_outgoing_completion_arc_cache[outgoing_cache_key]
        else:
            outgoing_arc_lb = _direct_min_outgoing_completion_arc_cost(
                data,
                int(label.last),
                int(available_mask),
                task_to_bit,
            )
            if min_outgoing_completion_arc_cache is not None:
                min_outgoing_completion_arc_cache[outgoing_cache_key] = outgoing_arc_lb
        if outgoing_arc_lb is None:
            _profile_add("partial_bound_unique_task_ns", _unique_task_started_ns)
            _increment_completion_bound_stat(completion_bound_stats, "partial_pruned_labels")
            _increment_completion_bound_stat(completion_bound_stats, "partial_pruned_no_outgoing")
            return True, float("inf")
        outgoing_suffix_lb = float(outgoing_arc_lb) + unique_task_bound.outgoing_value(
            int(available_mask),
            int(remaining_visit_capacity),
        )
        if float(outgoing_suffix_lb) > float(remaining_lb):
            remaining_lb = float(outgoing_suffix_lb)
            remaining_lb_winner = "unique_task"
        _profile_add("partial_bound_unique_task_ns", _unique_task_started_ns)
    if unique_route_bound is not None:
        _unique_route_started_ns = time.perf_counter_ns() if profile_enabled else 0
        route_lb = unique_route_bound.partial_value(
            int(label.last),
            int(available_mask),
            max(0, int(max_tasks_per_sortie) - len(label.sequence)),
            max(0, int(remaining_sorties)),
            float(start_lb) + float(label.partial.offset),
            float(label.partial.travel_energy) + float(label.partial.service_energy),
        )
        if route_lb is not None:
            if math.isinf(float(route_lb)):
                _profile_add("partial_bound_unique_route_ns", _unique_route_started_ns)
                _increment_completion_bound_stat(completion_bound_stats, "partial_pruned_labels")
                _increment_completion_bound_stat(completion_bound_stats, "partial_pruned_unique_route_infeasible")
                return True, float("inf")
            if remaining_lb is None or float(route_lb) > float(remaining_lb):
                remaining_lb = float(route_lb)
                remaining_lb_winner = "unique_route"
        _profile_add("partial_bound_unique_route_ns", _unique_route_started_ns)
    previous = 0 if len(label.sequence) <= 1 else int(label.sequence[-2])
    if completion_bound is not None:
        _completion_route_started_ns = time.perf_counter_ns() if profile_enabled else 0
        relaxed_route_lb = completion_bound.partial_value(
            int(label.last),
            int(previous),
            max(0, int(max_tasks_per_sortie) - len(label.sequence)),
            max(0, int(remaining_sorties)),
            float(start_lb) + float(label.partial.offset),
            float(label.partial.travel_energy) + float(label.partial.service_energy),
        )
        if math.isinf(float(relaxed_route_lb)):
            _profile_add("partial_bound_completion_route_ns", _completion_route_started_ns)
            _increment_completion_bound_stat(completion_bound_stats, "partial_pruned_labels")
            _increment_completion_bound_stat(completion_bound_stats, "partial_pruned_completion_route_infeasible")
            return True, float("inf")
        if remaining_lb is None or float(relaxed_route_lb) > float(remaining_lb):
            remaining_lb = float(relaxed_route_lb)
            remaining_lb_winner = "completion_route"
        _profile_add("partial_bound_completion_route_ns", _completion_route_started_ns)
    if rpce_bound is not None and bool(getattr(rpce_bound, "is_available", True)):
        _rpce_started_ns = time.perf_counter_ns() if profile_enabled else 0
        current_load = sum(float(data.task_value(int(task), "d")) for task in label.sequence)
        rpce_result = rpce_bound.partial_value(
            int(label.last),
            max(0, int(max_tasks_per_sortie) - len(label.sequence)),
            max(0, int(remaining_sorties)),
            float(start_lb) + float(label.partial.offset),
            float(label.partial.travel_energy) + float(label.partial.service_energy),
            float(current_load),
            current_mask=int(label.mask),
        )
        if bool(rpce_result.infeasible):
            _profile_add("partial_bound_resource_pareto_ns", _rpce_started_ns)
            _increment_completion_bound_stat(completion_bound_stats, "partial_pruned_labels")
            _increment_completion_bound_stat(completion_bound_stats, "partial_pruned_resource_pareto_infeasible")
            return True, float("inf")
        if rpce_result.value is not None and math.isfinite(float(rpce_result.value)):
            if remaining_lb is None or float(rpce_result.value) > float(remaining_lb):
                remaining_lb = float(rpce_result.value)
                remaining_lb_winner = "resource_pareto"
        _profile_add("partial_bound_resource_pareto_ns", _rpce_started_ns)
    unique_route_amcb_skip = (
        unique_route_bound is not None
        and bool(getattr(unique_route_bound, "enabled", True))
    )
    if (
        amcb_bound is not None
        and not bool(getattr(amcb_bound, "disabled", False))
        and not bool(unique_route_amcb_skip)
    ):
        amcb_result = amcb_bound.lower_bound_for_partial(
            last=int(label.last),
            available_mask=int(available_mask),
            remaining_slots_current_sortie=max(0, int(max_tasks_per_sortie) - len(label.sequence)),
            remaining_sorties_after_current=max(0, int(remaining_sorties)),
        )
        if amcb_result.value is not None and math.isfinite(float(amcb_result.value)):
            if remaining_lb is None or float(amcb_result.value) > float(remaining_lb):
                remaining_lb = float(amcb_result.value)
                remaining_lb_winner = "available_mask"
    if completion_bound is not None and len(label.sequence) >= int(max_tasks_per_sortie):
        _completion_route_started_ns = time.perf_counter_ns() if profile_enabled else 0
        try:
            return_options = data.options(int(label.last), 0)
        except KeyError:
            return_options = tuple()
        if return_options:
            route_finish_lb = min(
                (
                    float(option.cost)
                    + completion_bound.value(
                        int(remaining_sorties),
                        float(start_lb) + float(label.partial.offset) + float(option.tau),
                    )
                )
                for option in return_options
            )
            if remaining_lb is None or float(route_finish_lb) > float(remaining_lb):
                remaining_lb = float(route_finish_lb)
                remaining_lb_winner = "route_finish"
        _profile_add("partial_bound_completion_route_ns", _completion_route_started_ns)
    if remaining_lb is None:
        return False, None
    _cut_started_ns = time.perf_counter_ns() if profile_enabled else 0
    optimistic_cut_value = _direct_completion_optimistic_cut_dual_value(
        int(journey_label_mask) | int(label.mask),
        cut_duals,
        cuts,
        cut_masks,
        optimistic_cut_value_cache,
    )
    optimistic_cut_value += _direct_completion_positive_subset_future_reward_bound(
        int(journey_label_mask) | int(label.mask),
        int(remaining_visit_capacity),
        cut_duals,
        cuts,
        cut_masks,
        positive_cut_reward_bound=positive_cut_reward_bound,
    )
    if float(optimistic_cut_value) > 0.0:
        _increment_completion_bound_stat(completion_bound_stats, "partial_cut_reward_positive_checks")
    _profile_add("partial_bound_cut_ns", _cut_started_ns)
    optimistic_objective = (
        float(base_reduced_cost)
        + float(journey_label_value)
        + float(sortie_prefix_contribution)
        - float(optimistic_cut_value)
        + float(remaining_lb)
    )
    if optimistic_objective >= -float(eps):
        _increment_completion_bound_stat(completion_bound_stats, "partial_pruned_labels")
        if remaining_lb_winner:
            _increment_completion_bound_stat(
                completion_bound_stats,
                f"partial_pruned_{remaining_lb_winner}_winner",
            )
        return True, float(optimistic_objective)
    return False, float(optimistic_objective)


def _direct_completed_journey_suffix_optimistic_objective(
    data: FutureData,
    *,
    new_mask: int,
    new_end_time: float,
    new_objective: float,
    remaining_sorties: int,
    completion_bound: _DirectJourneyCompletionBound | None,
    rpce_bound: ResourceParetoCompletionEnvelope | None = None,
    amcb_bound: AvailableMaskCompletionBound | None = None,
    unique_task_bound: _UniqueTaskVisitLowerBound | None,
    unique_route_bound: "_UniqueRouteCompletionLowerBound | None",
    positive_cut_reward_bound: "_PositiveSubsetCutRewardBound | None",
    max_tasks_per_sortie: int,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
) -> tuple[float, str, float]:
    suffix_lb = 0.0
    suffix_lb_winner = "none"
    if completion_bound is not None:
        suffix_lb = completion_bound.value(int(remaining_sorties), float(new_end_time))
        suffix_lb_winner = "completion_route"
    if rpce_bound is not None and bool(getattr(rpce_bound, "is_available", True)):
        rpce_result = rpce_bound.suffix_value(int(remaining_sorties), float(new_end_time))
        if rpce_result.value is not None and math.isfinite(float(rpce_result.value)):
            if float(rpce_result.value) > float(suffix_lb):
                suffix_lb = float(rpce_result.value)
                suffix_lb_winner = "resource_pareto"
    available_mask = 0
    if unique_task_bound is not None:
        available_mask = int(unique_task_bound.full_mask) ^ int(new_mask)
    elif unique_route_bound is not None:
        available_mask = int(unique_route_bound.full_mask) ^ int(new_mask)
    elif amcb_bound is not None:
        available_mask = int(amcb_bound.full_mask) ^ int(new_mask)
    unique_route_amcb_skip = (
        unique_route_bound is not None
        and bool(getattr(unique_route_bound, "enabled", True))
    )
    if (
        amcb_bound is not None
        and not bool(getattr(amcb_bound, "disabled", False))
        and not bool(unique_route_amcb_skip)
    ):
        amcb_result = amcb_bound.lower_bound_for_suffix(
            available_mask=int(available_mask),
            remaining_sorties=int(remaining_sorties),
        )
        if amcb_result.value is not None and math.isfinite(float(amcb_result.value)):
            if float(amcb_result.value) > float(suffix_lb):
                suffix_lb = float(amcb_result.value)
                suffix_lb_winner = "available_mask"
    if unique_task_bound is not None:
        unique_suffix_lb = unique_task_bound.value(
            int(available_mask),
            int(remaining_sorties) * int(max_tasks_per_sortie),
        )
        if float(unique_suffix_lb) > float(suffix_lb):
            suffix_lb = float(unique_suffix_lb)
            suffix_lb_winner = "unique_task"
    if unique_route_bound is not None:
        route_suffix_lb = unique_route_bound.future_value(
            int(available_mask),
            int(remaining_sorties),
            float(new_end_time),
        )
        if route_suffix_lb is not None and float(route_suffix_lb) > float(suffix_lb):
            suffix_lb = float(route_suffix_lb)
            suffix_lb_winner = "unique_route"
    future_cut_reward = _direct_completion_positive_subset_future_reward_bound(
        int(new_mask),
        int(remaining_sorties) * int(max_tasks_per_sortie),
        cut_duals,
        cuts,
        cut_masks,
        positive_cut_reward_bound=positive_cut_reward_bound,
    )
    optimistic_objective = float(new_objective) + float(suffix_lb) - float(future_cut_reward)
    return float(optimistic_objective), str(suffix_lb_winner), float(future_cut_reward)


def _direct_completed_journey_suffix_bound_prunes(
    data: FutureData,
    *,
    new_mask: int,
    new_end_time: float,
    new_objective: float,
    remaining_sorties: int,
    completion_bound: _DirectJourneyCompletionBound | None,
    rpce_bound: ResourceParetoCompletionEnvelope | None = None,
    amcb_bound: AvailableMaskCompletionBound | None = None,
    unique_task_bound: _UniqueTaskVisitLowerBound | None,
    unique_route_bound: "_UniqueRouteCompletionLowerBound | None",
    positive_cut_reward_bound: "_PositiveSubsetCutRewardBound | None",
    max_tasks_per_sortie: int,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
    eps: float,
    completion_bound_stats: dict[str, int] | None = None,
) -> bool:
    optimistic_objective, suffix_lb_winner, future_cut_reward = _direct_completed_journey_suffix_optimistic_objective(
        data,
        new_mask=int(new_mask),
        new_end_time=float(new_end_time),
        new_objective=float(new_objective),
        remaining_sorties=int(remaining_sorties),
        completion_bound=completion_bound,
        rpce_bound=rpce_bound,
        amcb_bound=amcb_bound,
        unique_task_bound=unique_task_bound,
        unique_route_bound=unique_route_bound,
        positive_cut_reward_bound=positive_cut_reward_bound,
        max_tasks_per_sortie=int(max_tasks_per_sortie),
        cut_duals=cut_duals,
        cuts=cuts,
        cut_masks=cut_masks,
    )
    if float(future_cut_reward) > 0.0:
        _increment_completion_bound_stat(completion_bound_stats, "suffix_cut_reward_positive_checks")
    if optimistic_objective >= -float(eps):
        _increment_completion_bound_stat(completion_bound_stats, "suffix_pruned_labels")
        _increment_completion_bound_stat(
            completion_bound_stats,
            f"suffix_pruned_{suffix_lb_winner}_winner",
        )
        return True
    return False


def _direct_next_sortie_profiles(
    data: FutureData,
    duals: FutureDuals,
    task_order: tuple[int, ...],
    task_to_bit: dict[int, int],
    *,
    used_mask: int,
    config: JourneyPricingConfig,
    deadline: float | None,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
) -> tuple[list[_SortieProfile], int, int, str]:
    max_tasks = _max_tasks_per_trip(data, int(config.max_tasks_per_trip))
    initial = _SortiePartialLabel(
        sequence=tuple(),
        mask=0,
        last=0,
        partial=_PartialNoWaitingPathProfile(
            arc_options=tuple(),
            lower_start=0.0,
            upper_start=float(data.horizon),
            offset=0.0,
            travel_cost=0.0,
            travel_energy=0.0,
            service_cost=0.0,
            service_energy=0.0,
        ),
    )
    labels_by_key: dict[tuple[int, int], list[_SortiePartialLabel]] = {(0, 0): [initial]}
    heap: list[tuple[float, int, float, tuple[int, ...], int, _SortiePartialLabel]] = [
        (_sortie_partial_label_priority(initial, duals), 0, 0.0, tuple(), 0, initial)
    ]
    serial = 0
    generated = 0
    evaluated = 0
    profiles_by_key: dict[tuple, _SortieProfile] = {}
    profiles_by_mask: dict[int, list[_SortieProfile]] = {}
    while heap:
        if deadline is not None and time.perf_counter() > deadline:
            return list(profiles_by_key.values()), generated, evaluated, "time_limit"
        _priority, _depth, _offset, _seq_key, _serial, label = heapq.heappop(heap)
        if label not in labels_by_key.get((int(label.mask), int(label.last)), []):
            continue
        if len(label.sequence) >= max_tasks:
            continue
        for task in task_order:
            task = int(task)
            global_bit = 1 << task_to_bit[task]
            if int(used_mask) & global_bit or label.mask & global_bit:
                continue
            sequence = (*label.sequence, task)
            local_mask = label.mask | global_bit
            if not _journey_mask_branch_allowed(
                int(used_mask) | int(local_mask),
                branch_constraints,
                task_to_bit,
                final=False,
            ):
                continue
            if not _sequence_resource_precheck(data, sequence):
                continue
            options = data.options(int(label.last), task)
            if not options:
                continue
            for option in options:
                if deadline is not None and time.perf_counter() > deadline:
                    return list(profiles_by_key.values()), generated, evaluated, "time_limit"
                extended = _extend_no_waiting_partial(data, sequence, len(label.sequence), label.partial, option)
                if extended is None:
                    continue
                generated += 1
                if int(config.max_sequences) > 0 and generated > int(config.max_sequences):
                    return list(profiles_by_key.values()), generated, evaluated, "direct_label_sequence_budget"
                new_label = _SortiePartialLabel(sequence=sequence, mask=local_mask, last=task, partial=extended)
                if not _add_sortie_partial_label(
                    labels_by_key.setdefault((local_mask, task), []),
                    new_label,
                    generalized=bool(config.generalized_partial_dominance_enabled),
                    max_labels_per_node=int(config.direct_journey_label_max_labels_per_node),
                    rank_key=lambda item: _sortie_partial_label_priority(item, duals),
                    time_bucket_size=float(config.direct_journey_label_resource_coarsening_time_bucket_size),
                    energy_bucket_size=float(config.direct_journey_label_resource_coarsening_energy_bucket_size),
                ):
                    continue
                serial += 1
                heapq.heappush(
                    heap,
                    (
                        _sortie_partial_label_priority(new_label, duals),
                        len(new_label.sequence),
                        round(float(new_label.partial.offset), 9),
                        tuple(int(item) for item in new_label.sequence),
                        serial,
                        new_label,
                    ),
                )
                completed, eval_inc = _complete_direct_sortie_label_profiles(
                    data,
                    duals,
                    new_label,
                    task_to_bit,
                )
                evaluated += eval_inc
                for profile in completed:
                    key = (
                        tuple(int(task) for task in profile.sequence),
                        tuple(option.option_id for option in profile.arc_options),
                        round(float(profile.lower_start), 6),
                        round(float(profile.upper_start), 6),
                        round(float(profile.end_offset), 6),
                    )
                    old = profiles_by_key.get(key)
                    if old is None or profile.contribution < old.contribution - 1.0e-9:
                        profiles_by_key[key] = profile
                if int(config.max_timed_evaluations) > 0 and evaluated > int(config.max_timed_evaluations):
                    return list(profiles_by_key.values()), generated, evaluated, "direct_label_profile_evaluation_budget"
    return list(profiles_by_key.values()), generated, evaluated, ""


def _complete_direct_sortie_label_profiles(
    data: FutureData,
    duals: FutureDuals,
    label: _SortiePartialLabel,
    task_to_bit: dict[int, int],
) -> tuple[list[_SortieProfile], int]:
    options = data.options(int(label.last), 0)
    if not options:
        return [], 0
    dual_sum = sum(float(duals.cover.get(int(task), 0.0)) for task in set(label.sequence))
    completed: list[_SortieProfile] = []
    evaluated = 0
    mask = 0
    for task in set(label.sequence):
        mask |= 1 << task_to_bit[int(task)]
    for option in options:
        base = _complete_no_waiting_partial(data, label.partial, option)
        if base is None:
            continue
        evaluated += 1
        profile = base.profile
        contribution = float(profile.cost) - dual_sum
        completed.append(
            _SortieProfile(
                sequence=tuple(int(task) for task in label.sequence),
                arc_options=base.arc_options,
                lower_start=float(profile.lower_start),
                upper_start=float(profile.upper_start),
                end_offset=float(profile.end_offset),
                cost=float(profile.cost),
                mask=mask,
                contribution=contribution,
            )
        )
    return completed, evaluated


def _direct_sortie_profiles_to_trips(
    data: FutureData,
    profiles: list[_SortieProfile],
    *,
    earliest_start: float,
    threshold: float,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
    cut_pruning_safe: bool,
    config: JourneyPricingConfig,
    deadline: float | None = None,
) -> tuple[list[tuple[TimedTrip, float, int]], int, str]:
    trips_by_signature: dict[tuple, tuple[TimedTrip, float, int]] = {}
    evaluated = 0
    for profile in profiles:
        if deadline is not None and time.perf_counter() > deadline:
            return list(trips_by_signature.values()), evaluated, "time_limit"
        profile_cut_penalty = _profile_cut_penalty(
            int(profile.mask),
            cut_duals,
            cuts,
            cut_masks,
            enabled=bool(cut_pruning_safe),
        )
        if float(profile.contribution) + profile_cut_penalty >= float(threshold):
            continue
        start = max(float(earliest_start), float(profile.lower_start))
        if start > float(profile.upper_start) + 1.0e-9:
            continue
        trip = evaluate_timed_trip(
            data,
            profile.sequence,
            start,
            time_bucket_size=float(config.time_bucket_size),
            arc_options=profile.arc_options,
        )
        evaluated += 1
        if trip is None:
            continue
        old = trips_by_signature.get(trip.signature)
        contribution = float(profile.contribution)
        if old is None or contribution < old[1] - 1.0e-9:
            trips_by_signature[trip.signature] = (trip, contribution, int(profile.mask))
    return list(trips_by_signature.values()), evaluated, ""


def _complete_direct_sortie_label_trips(
    data: FutureData,
    duals: FutureDuals,
    label: _SortiePartialLabel,
    config: JourneyPricingConfig,
    *,
    earliest_start: float,
    threshold: float,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
    cut_pruning_safe: bool,
    task_to_bit: dict[int, int],
    deadline: float | None = None,
    base_reduced_cost: float = 0.0,
    journey_label_value: float = 0.0,
    journey_label_mask: int = 0,
    journey_label_count: int = 0,
    completion_bound: _DirectJourneyCompletionBound | None = None,
    rpce_bound: ResourceParetoCompletionEnvelope | None = None,
    amcb_bound: AvailableMaskCompletionBound | None = None,
    unique_task_bound: _UniqueTaskVisitLowerBound | None = None,
    unique_route_bound: "_UniqueRouteCompletionLowerBound | None" = None,
    positive_cut_reward_bound: "_PositiveSubsetCutRewardBound | None" = None,
    completion_bound_stats: dict[str, int] | None = None,
    cut_value_cache: dict[int, float] | None = None,
    optimistic_cut_value_cache: dict[int, float] | None = None,
    profile_cut_penalty_cache: dict[int, float] | None = None,
    partial_cover_dual_sum_cache: dict[int, float] | None = None,
) -> tuple[list[tuple[TimedTrip, float, int]], int, str, int, int]:
    options = data.options(int(label.last), 0)
    if not options:
        return [], 0, "", 0, 0
    mask = int(label.mask)
    dual_sum = _cover_dual_sum_for_mask(int(mask), duals, task_to_bit, partial_cover_dual_sum_cache)
    completed: list[tuple[TimedTrip, float, int]] = []
    evaluated = 0
    bound_checked = 0
    bound_pruned = 0
    profile_cut_penalty = _profile_cut_penalty_cached(
        mask,
        cut_duals,
        cuts,
        cut_masks,
        enabled=bool(cut_pruning_safe),
        cache=profile_cut_penalty_cache,
    )
    completion_cost_lb = float(label.partial.travel_cost) + float(label.partial.service_cost) + min(
        float(option.cost) for option in options
    )
    if completion_cost_lb - dual_sum + profile_cut_penalty >= float(threshold):
        return [], 0, "", 0, 0
    for option in options:
        if deadline is not None and time.perf_counter() > float(deadline):
            return completed, evaluated, "time_limit", bound_checked, bound_pruned
        base = _complete_no_waiting_partial(data, label.partial, option)
        if base is None:
            continue
        profile = base.profile
        start = max(float(earliest_start), float(profile.lower_start))
        if start > float(profile.upper_start) + 1.0e-9:
            continue
        contribution = float(profile.cost) - dual_sum
        if contribution + profile_cut_penalty >= float(threshold):
            continue
        provisional_mask = int(journey_label_mask) | int(mask)
        provisional_end_time = float(start) + float(profile.end_offset)
        provisional_objective = (
            float(base_reduced_cost)
            + float(journey_label_value)
            + float(contribution)
            - _journey_cut_dual_value_cached(
                int(provisional_mask),
                cut_duals,
                cuts,
                cut_masks,
                cut_value_cache if cut_value_cache is not None else {},
            )
        )
        active_rpce_bound = (
            rpce_bound
            if rpce_bound is not None and bool(getattr(rpce_bound, "is_available", True))
            else None
        )
        active_amcb_bound = (
            amcb_bound
            if amcb_bound is not None and not bool(getattr(amcb_bound, "disabled", False))
            else None
        )
        if (
            completion_bound is not None
            or active_rpce_bound is not None
            or active_amcb_bound is not None
            or unique_task_bound is not None
            or unique_route_bound is not None
            or positive_cut_reward_bound is not None
        ):
            bound_checked += 1
            remaining_sorties = int(data.sortie_limit) - int(journey_label_count) - 1
            if _direct_completed_journey_suffix_bound_prunes(
                data,
                new_mask=int(provisional_mask),
                new_end_time=float(provisional_end_time),
                new_objective=float(provisional_objective),
                remaining_sorties=int(remaining_sorties),
                completion_bound=completion_bound,
                rpce_bound=active_rpce_bound,
                amcb_bound=active_amcb_bound,
                unique_task_bound=unique_task_bound,
                unique_route_bound=unique_route_bound,
                positive_cut_reward_bound=positive_cut_reward_bound,
                max_tasks_per_sortie=_max_tasks_per_trip(data, int(config.max_tasks_per_trip)),
                cut_duals=cut_duals,
                cuts=cuts,
                cut_masks=cut_masks,
                eps=float(config.eps),
                completion_bound_stats=completion_bound_stats,
            ):
                bound_pruned += 1
                continue
        segment = _DirectSortieSegment(
            sequence=tuple(int(task) for task in label.sequence),
            arc_options=tuple(base.arc_options),
            start_time=rounded(float(start)),
            end_time=rounded(float(start) + float(profile.end_offset)),
            contribution=round(float(contribution), 9),
            mask=int(mask),
        )
        evaluated += 1
        completed.append((segment, contribution, mask))
    return completed, evaluated, "", bound_checked, bound_pruned


def _materialize_direct_sortie_segments(
    data: FutureData,
    segments: tuple[Any, ...],
    config: JourneyPricingConfig,
) -> tuple[TimedTrip, ...]:
    timed_trips: list[TimedTrip] = []
    for segment in segments:
        if isinstance(segment, TimedTrip):
            timed_trips.append(segment)
            continue
        if not isinstance(segment, _DirectSortieSegment):
            return tuple()
        trip = evaluate_timed_trip(
            data,
            segment.sequence,
            float(segment.start_time),
            time_bucket_size=float(config.time_bucket_size),
            arc_options=segment.arc_options,
            include_physical_paths=False,
        )
        if trip is None:
            return tuple()
        timed_trips.append(trip)
    return tuple(timed_trips)


def _direct_journey_objective(
    base_reduced_cost: float,
    label: _DirectJourneyLabel,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
    cut_value_cache: dict[int, float] | None = None,
) -> float:
    return (
        float(base_reduced_cost)
        + float(label.value)
        - _journey_cut_dual_value_cached(
            int(label.mask),
            cut_duals,
            cuts,
            cut_masks,
            cut_value_cache if cut_value_cache is not None else {},
        )
    )


def _direct_journey_label_priority(
    base_reduced_cost: float,
    label: _DirectJourneyLabel,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
    cut_value_cache: dict[int, float] | None = None,
) -> float:
    return round(_direct_journey_objective(base_reduced_cost, label, cut_duals, cuts, cut_masks, cut_value_cache), 9)


def _add_direct_journey_label_with_cross_count_dominance(
    stores_by_count: list[dict[int, list[_DirectJourneyLabel]]],
    count: int,
    mask: int,
    label: _DirectJourneyLabel,
    *,
    enabled: bool = True,
    max_labels_per_node: int = 0,
    time_bucket_size: float = 0.0,
) -> tuple[bool, int]:
    """Add a journey label and prune same-mask labels using sortie-count slack.

    For a fixed visited-task mask, using fewer sorties is never worse: it leaves
    at least as much remaining sortie capacity for future extensions.  Therefore
    a label at count ``c1`` exact-safely dominates another label at count ``c2``
    when ``c1 <= c2`` and its end time and reduced-cost value are no worse.
    The ordinary same-count dominance is still delegated to
    ``_add_direct_journey_label``.
    """

    count = int(count)
    if not bool(enabled):
        added = _add_direct_journey_label(
            stores_by_count[count],
            int(mask),
            label,
            max_labels_per_node=int(max_labels_per_node),
            time_bucket_size=float(time_bucket_size),
        )
        return bool(added), 0

    # A label that reaches the same task set with fewer sorties and no worse
    # time/cost makes the candidate redundant.  Same-count dominance is handled
    # by the normal insertion routine below.
    for old_count in range(0, max(0, count)):
        for old in stores_by_count[int(old_count)].get(int(mask), []):
            if _dominates_direct_journey_label(old, label, time_bucket_size=float(time_bucket_size)):
                return False, 1

    added = _add_direct_journey_label(
        stores_by_count[count],
        int(mask),
        label,
        max_labels_per_node=int(max_labels_per_node),
        time_bucket_size=float(time_bucket_size),
    )
    if not added:
        return False, 0

    pruned = 0
    for future_count in range(count + 1, len(stores_by_count)):
        labels = stores_by_count[int(future_count)].get(int(mask))
        if not labels:
            continue
        survivors = [
            old
            for old in labels
            if not _dominates_direct_journey_label(label, old, time_bucket_size=float(time_bucket_size))
        ]
        pruned += len(labels) - len(survivors)
        if survivors:
            labels[:] = survivors
        else:
            del stores_by_count[int(future_count)][int(mask)]
    return True, int(pruned)


def _add_direct_journey_label(
    store: dict[int, list[_DirectJourneyLabel]],
    mask: int,
    label: _DirectJourneyLabel,
    *,
    max_labels_per_node: int = 0,
    time_bucket_size: float = 0.0,
) -> bool:
    labels = store.setdefault(int(mask), [])
    for old in labels:
        if _dominates_direct_journey_label(old, label, time_bucket_size=float(time_bucket_size)):
            return False
    labels[:] = [
        old
        for old in labels
        if not _dominates_direct_journey_label(label, old, time_bucket_size=float(time_bucket_size))
    ]
    labels.append(label)
    max_labels = max(0, int(max_labels_per_node))
    if max_labels > 0 and len(labels) > max_labels:
        # Beam 模式只用于 true-dual 负列巡逻，不能证明 no-column。
        # 同一 task-mask 下保留 value/end_time 最有希望的标签，防止
        # direct-label 在 profile 和 final judge 之间膨胀成完整证明搜索。
        labels.sort(
            key=lambda item: (
                round(float(item.value), 9),
                round(float(item.end_time), 9),
                len(item.trips),
            )
        )
        survivors = labels[:max_labels]
        kept = any(item is label for item in survivors)
        labels[:] = survivors
        if not kept:
            return False
    return True


def _resource_bucket_floor(value: float, bucket_size: float) -> float:
    if float(bucket_size) <= 0.0:
        return float(value)
    return float(math.floor(float(value) / float(bucket_size) + 1.0e-12))


def _resource_bucket_ceil(value: float, bucket_size: float) -> float:
    if float(bucket_size) <= 0.0:
        return float(value)
    return float(math.ceil(float(value) / float(bucket_size) - 1.0e-12))


def _dominates_direct_journey_label(
    left: _DirectJourneyLabel,
    right: _DirectJourneyLabel,
    *,
    time_bucket_size: float = 0.0,
) -> bool:
    left_end = _resource_bucket_floor(float(left.end_time), float(time_bucket_size))
    right_end = _resource_bucket_floor(float(right.end_time), float(time_bucket_size))
    return bool(
        float(left_end) <= float(right_end) + 1.0e-9
        and float(left.value) <= float(right.value) + 1.0e-9
    )


def _price_journeys_by_streaming_profiles(
    data: FutureData,
    duals: JourneyDuals,
    *,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
    config: JourneyPricingConfig,
    cuts: tuple[FutureCut, ...],
    trip_cache: dict[tuple, tuple[tuple[TimedTrip, ...], int, int]] | None,
    resource_cache: dict[tuple, Any] | None = None,
    forbidden_journey_signatures: set[tuple] | frozenset[tuple] | None = None,
    dominant_task_set_costs: dict[frozenset[int], float] | None = None,
) -> JourneyPricingResult:
    """Interleave sortie-profile generation with journey DP.

    A partial streaming hit is a valid negative-column search result, but not an
    exact no-negative certificate.  If profile generation exhausts, the final DP
    result is handled exactly like the materialized profile oracle.
    """

    started = time.perf_counter()
    deadline = _pricing_absolute_deadline(started, config)
    vehicle = int(data.vehicles[0])
    trip_duals = FutureDuals(
        cover={int(task): float(value) for task, value in duals.cover.items()},
        task_vehicle={},
        sortie_count={int(vehicle): 0.0},
        time_occupation={},
        ordering={},
        branches={},
        cuts={},
    )
    base = float(data.fixed_vehicle_cost) - float(duals.fleet_limit)
    max_returned = max(1, int(config.max_returned_journeys))
    candidate_return_limit = _profile_candidate_return_limit(config, max_returned)
    cut_masks = _cut_masks(data, cuts)
    dominant_task_set_cost_by_mask = _dominant_task_set_costs_by_mask(data, dominant_task_set_costs)
    stream_batch = max(1, int(config.streaming_profile_batch_size))
    stream_min_negative = max(1, int(config.streaming_min_negative_batch))
    catalog_stats: dict[str, int] = {}
    best_partial_result: JourneyPricingResult | None = None

    def remember_partial(result: JourneyPricingResult) -> None:
        nonlocal best_partial_result
        if not result.journeys:
            return
        if best_partial_result is None:
            best_partial_result = result
            return
        current_count = len(result.journeys)
        best_count = len(best_partial_result.journeys)
        current_rc = math.inf if result.best_reduced_cost is None else float(result.best_reduced_cost)
        best_rc = math.inf if best_partial_result.best_reduced_cost is None else float(best_partial_result.best_reduced_cost)
        if current_count > best_count or (current_count == best_count and current_rc < best_rc - 1.0e-9):
            best_partial_result = result

    def stream_callback(
        profiles: list[_SortieProfile],
        generated: int,
        evaluated: int,
        best_profile_rc: float | None,
        cut_penalty_pruned: int,
    ) -> JourneyPricingResult | None:
        callback_elapsed = time.perf_counter() - started
        callback_dp_started = time.perf_counter()
        adaptive_min = int(config.streaming_partial_return_min_journeys)
        adaptive_after = float(config.streaming_partial_return_after_time)
        early_return_min = stream_min_negative
        if adaptive_min > 0 and adaptive_after > 0.0 and callback_elapsed >= adaptive_after:
            early_return_min = min(stream_min_negative, max(1, adaptive_min))
        candidate_profiles = profiles
        profile_dominance_pruned = 0
        candidate_profiles, profile_dominance_pruned = _filter_sortie_profiles_after_generation(
            candidate_profiles,
            config,
            catalog_stats,
        )
        dp_stats: dict[str, int] = {}
        selected_candidates, objective, status = _solve_best_journey_profile_dp(
            data,
            candidate_profiles,
            base_reduced_cost=base,
            cut_duals=duals.cuts or {},
            cuts=cuts,
            cut_masks=cut_masks,
            max_states=int(config.max_dp_states),
            deadline=deadline,
            max_returned=candidate_return_limit,
            early_return_negative=bool(config.early_return_negative),
            early_return_min_count=early_return_min,
            optimistic_bound_pruning=bool(config.dp_bound_pruning_enabled),
            cross_count_dominance=bool(config.dp_cross_count_dominance_enabled),
            selection_mode=str(config.journey_selection_mode),
            dp_stats=dp_stats,
            forbidden_journey_signatures=forbidden_journey_signatures,
            duplicate_scan_limit=int(config.duplicate_scan_limit),
            dominant_task_set_cost_by_mask=dominant_task_set_cost_by_mask,
            pricing_config=config,
            branch_constraints=branch_constraints,
            eps=float(config.eps),
        )
        callback_dp_time = time.perf_counter() - callback_dp_started
        if not selected_candidates:
            return None
        journeys, existing_filtered, weak_filtered = _instantiate_profile_journey_candidates(
            data,
            candidate_profiles,
            selected_candidates,
            config,
            eps=float(config.eps),
            forbidden_journey_signatures=forbidden_journey_signatures,
            dominant_task_set_costs=dominant_task_set_costs,
            max_journeys=max_returned,
            branch_constraints=branch_constraints,
            duals=duals,
            cuts=cuts,
            dp_stats=dp_stats,
        )
        if journeys:
            min_returned = max(1, int(config.streaming_min_returned_journeys))
            result = JourneyPricingResult(
                journeys,
                False,
                objective,
                generated,
                evaluated,
                len(candidate_profiles),
                max((len(selected) for selected, _obj in selected_candidates), default=0),
                "INCOMPLETE",
                "streaming_partial_negative_journey",
                profile_dominance_pruned,
                existing_filtered,
                cut_penalty_pruned,
                weak_filtered,
                dp_stats.get("bound_pruned_labels", 0),
                dp_stats.get("cross_count_pruned_labels", 0),
                profile_catalog_hit=bool(catalog_stats.get("hit", 0)),
                profile_catalog_size=int(catalog_stats.get("size", 0)),
                duplicate_candidate_scan_count=dp_stats.get("duplicate_candidate_scan_count", 0),
                duplicate_candidates_filtered=dp_stats.get("duplicate_candidates_filtered", 0),
                duplicate_scan_limited=bool(dp_stats.get("duplicate_scan_limited", 0)),
                profile_generation_time=callback_elapsed,
                profile_dp_time=callback_dp_time,
                **_dp_profile_stats_kwargs(dp_stats),
                **_resource_stats_kwargs(catalog_stats),
                **_profile_mask_diagnostic_kwargs(candidate_profiles, dp_stats, config),
            )
            remember_partial(result)
            if len(journeys) < min_returned:
                if (
                    adaptive_min > 0
                    and adaptive_after > 0.0
                    and len(journeys) >= adaptive_min
                    and callback_elapsed >= adaptive_after
                ):
                    return result
                return None
            return result
        if weak_filtered > 0:
            return JourneyPricingResult(
                [],
                False,
                objective,
                generated,
                evaluated,
                len(candidate_profiles),
                max((len(selected) for selected, _obj in selected_candidates), default=0),
                "INCOMPLETE",
                "weak_negative_journeys_filtered",
                profile_dominance_pruned,
                existing_filtered,
                cut_penalty_pruned,
                weak_filtered,
                dp_stats.get("bound_pruned_labels", 0),
                dp_stats.get("cross_count_pruned_labels", 0),
                profile_catalog_hit=bool(catalog_stats.get("hit", 0)),
                profile_catalog_size=int(catalog_stats.get("size", 0)),
                duplicate_candidate_scan_count=dp_stats.get("duplicate_candidate_scan_count", 0),
                duplicate_candidates_filtered=dp_stats.get("duplicate_candidates_filtered", 0),
                duplicate_scan_limited=bool(dp_stats.get("duplicate_scan_limited", 0)),
                profile_generation_time=callback_elapsed,
                profile_dp_time=callback_dp_time,
                **_dp_profile_stats_kwargs(dp_stats),
                **_resource_stats_kwargs(catalog_stats),
                **_profile_mask_diagnostic_kwargs(candidate_profiles, dp_stats, config),
            )
        if (
            status != "OPTIMAL"
            and existing_filtered <= 0
            and int(dp_stats.get("dominated_task_set_candidates_filtered", 0)) <= 0
        ):
            if deadline is None or time.perf_counter() <= float(deadline):
                return None
            return JourneyPricingResult(
                [],
                False,
                objective,
                generated,
                evaluated,
                len(candidate_profiles),
                0,
                "INCOMPLETE",
                "streaming_profile_dp_incomplete",
                profile_dominance_pruned,
                existing_filtered,
                cut_penalty_pruned,
                weak_filtered,
                dp_stats.get("bound_pruned_labels", 0),
                dp_stats.get("cross_count_pruned_labels", 0),
                profile_catalog_hit=bool(catalog_stats.get("hit", 0)),
                profile_catalog_size=int(catalog_stats.get("size", 0)),
                profile_generation_time=callback_elapsed,
                profile_dp_time=callback_dp_time,
                **_dp_profile_stats_kwargs(dp_stats),
                **_resource_stats_kwargs(catalog_stats),
                **_profile_mask_diagnostic_kwargs(candidate_profiles, dp_stats, config),
            )
        return None

    generation_deadline = deadline
    if deadline is not None:
        fraction = min(1.0, max(0.05, float(config.profile_generation_time_fraction)))
        if float(config.time_limit) > 0.0:
            generation_deadline = min(float(deadline), started + float(config.time_limit) * fraction)
    if deadline is not None and float(config.streaming_final_dp_time_reserve) > 0.0:
        reserve = max(0.0, float(config.streaming_final_dp_time_reserve))
        reserved_deadline = max(started, float(deadline) - reserve)
        generation_deadline = min(float(generation_deadline), float(reserved_deadline))

    try:
        profiles, generated, evaluated, best_profile_rc, exhausted, reason, cut_penalty_pruned = _generate_negative_sortie_profiles(
            data,
            trip_duals,
            base_reduced_cost=base,
            config=config,
            trip_cache=trip_cache,
            resource_cache=resource_cache,
            started=started,
            deadline=generation_deadline,
            journey_cut_duals=duals.cuts or {},
            journey_cuts=cuts,
            stream_callback=stream_callback,
            stream_profile_batch_size=stream_batch,
            catalog_stats=catalog_stats,
            branch_constraints=branch_constraints,
        )
    except _StreamingPricingStop as stop:
        return stop.result
    generation_elapsed = time.perf_counter() - started
    if best_partial_result is not None and not exhausted and deadline is not None and time.perf_counter() >= deadline:
        return best_partial_result
    if not exhausted and not profiles:
        if best_partial_result is not None:
            return best_partial_result
        return JourneyPricingResult(
            [],
            False,
            best_profile_rc,
            generated,
            evaluated,
            0,
            0,
            "INCOMPLETE",
            reason or "streaming_profile_generation_incomplete",
            profile_cut_penalty_pruned=cut_penalty_pruned,
            profile_catalog_hit=bool(catalog_stats.get("hit", 0)),
            profile_catalog_size=int(catalog_stats.get("size", 0)),
            profile_generation_time=generation_elapsed,
            **_resource_stats_kwargs(catalog_stats),
        )
    if not profiles:
        if base < -float(config.eps):
            return JourneyPricingResult(
                [],
                False,
                best_profile_rc,
                generated,
                evaluated,
                0,
                0,
                "INCOMPLETE",
                "negative_fleet_base_requires_profiles",
                profile_cut_penalty_pruned=cut_penalty_pruned,
                profile_catalog_hit=bool(catalog_stats.get("hit", 0)),
                profile_catalog_size=int(catalog_stats.get("size", 0)),
                profile_generation_time=generation_elapsed,
                **_resource_stats_kwargs(catalog_stats),
            )
        return JourneyPricingResult(
            [],
            exhausted,
            None if best_profile_rc is None else base + float(best_profile_rc),
            generated,
            evaluated,
            0,
            0,
            "OPTIMAL" if exhausted else "INCOMPLETE",
            "no_negative_sortie_profile" if exhausted else reason,
            profile_cut_penalty_pruned=cut_penalty_pruned,
            profile_catalog_hit=bool(catalog_stats.get("hit", 0)),
            profile_catalog_size=int(catalog_stats.get("size", 0)),
            profile_generation_time=generation_elapsed,
            **_resource_stats_kwargs(catalog_stats),
        )
    profile_dominance_pruned = 0
    filter_started = time.perf_counter()
    profiles, profile_dominance_pruned = _filter_sortie_profiles_after_generation(profiles, config, catalog_stats)
    profile_filter_time = time.perf_counter() - filter_started
    dp_stats: dict[str, int] = {}
    final_dp_started = time.perf_counter()
    selected_candidates, objective, status = _solve_best_journey_profile_dp(
        data,
        profiles,
        base_reduced_cost=base,
        cut_duals=duals.cuts or {},
        cuts=cuts,
        cut_masks=cut_masks,
        max_states=int(config.max_dp_states),
        deadline=deadline,
        max_returned=candidate_return_limit,
        early_return_negative=bool(config.early_return_negative),
        early_return_min_count=stream_min_negative,
        optimistic_bound_pruning=bool(config.dp_bound_pruning_enabled),
        cross_count_dominance=bool(config.dp_cross_count_dominance_enabled),
        selection_mode=str(config.journey_selection_mode),
        dp_stats=dp_stats,
        forbidden_journey_signatures=forbidden_journey_signatures,
        duplicate_scan_limit=int(config.duplicate_scan_limit),
        dominant_task_set_cost_by_mask=dominant_task_set_cost_by_mask,
        pricing_config=config,
        branch_constraints=branch_constraints,
        eps=float(config.eps),
    )
    final_dp_time = time.perf_counter() - final_dp_started
    if status != "OPTIMAL":
        journeys, existing_filtered, weak_filtered = _instantiate_profile_journey_candidates(
            data,
            profiles,
            selected_candidates,
            config,
            eps=float(config.eps),
            forbidden_journey_signatures=forbidden_journey_signatures,
            dominant_task_set_costs=dominant_task_set_costs,
            max_journeys=max_returned,
            branch_constraints=branch_constraints,
            duals=duals,
            cuts=cuts,
            dp_stats=dp_stats,
        )
        if journeys:
            return JourneyPricingResult(
                journeys,
                False,
                objective,
                generated,
                evaluated,
                len(profiles),
                max((len(selected) for selected, _obj in selected_candidates), default=0),
                "INCOMPLETE",
                "streaming_partial_dp_negative_journey",
                profile_dominance_pruned,
                existing_filtered,
                cut_penalty_pruned,
                weak_filtered,
                dp_stats.get("bound_pruned_labels", 0),
                dp_stats.get("cross_count_pruned_labels", 0),
                profile_catalog_hit=bool(catalog_stats.get("hit", 0)),
                profile_catalog_size=int(catalog_stats.get("size", 0)),
                duplicate_candidate_scan_count=dp_stats.get("duplicate_candidate_scan_count", 0),
                duplicate_candidates_filtered=dp_stats.get("duplicate_candidates_filtered", 0),
                duplicate_scan_limited=bool(dp_stats.get("duplicate_scan_limited", 0)),
                profile_generation_time=generation_elapsed,
                profile_filter_time=profile_filter_time,
                profile_dp_time=final_dp_time,
                **_dp_profile_stats_kwargs(dp_stats),
                **_resource_stats_kwargs(catalog_stats),
                **_profile_mask_diagnostic_kwargs(profiles, dp_stats, config),
            )
        reason_text = _profile_dp_incomplete_reason("profile_dp_incomplete", dp_stats)
        if weak_filtered > 0:
            reason_text = "weak_negative_journeys_filtered"
        if (
            existing_filtered > 0
            or int(dp_stats.get("duplicate_candidates_filtered", 0)) > 0
            or int(dp_stats.get("dominated_task_set_candidates_filtered", 0)) > 0
        ):
            reason_text = "negative_journeys_already_in_pool"
        if best_partial_result is not None:
            return best_partial_result
        return JourneyPricingResult(
            [],
            False,
            objective,
            generated,
            evaluated,
            len(profiles),
            0,
            "INCOMPLETE",
            reason_text,
            profile_dominance_pruned,
            existing_filtered,
            cut_penalty_pruned,
            weak_filtered,
            dp_stats.get("bound_pruned_labels", 0),
            dp_stats.get("cross_count_pruned_labels", 0),
            profile_catalog_hit=bool(catalog_stats.get("hit", 0)),
            profile_catalog_size=int(catalog_stats.get("size", 0)),
            duplicate_candidate_scan_count=dp_stats.get("duplicate_candidate_scan_count", 0),
            duplicate_candidates_filtered=dp_stats.get("duplicate_candidates_filtered", 0),
            duplicate_scan_limited=bool(dp_stats.get("duplicate_scan_limited", 0)),
            profile_generation_time=generation_elapsed,
            profile_filter_time=profile_filter_time,
            profile_dp_time=final_dp_time,
            **_dp_profile_stats_kwargs(dp_stats),
            **_resource_stats_kwargs(catalog_stats),
            **_profile_mask_diagnostic_kwargs(profiles, dp_stats, config),
        )
    if (objective is None or objective >= -float(config.eps)) and not selected_candidates:
        return JourneyPricingResult(
            [],
            bool(exhausted),
            objective,
            generated,
            evaluated,
            len(profiles),
            0,
            "OPTIMAL" if exhausted else "INCOMPLETE",
            "no_negative_journey" if exhausted else "partial_profile_scan_no_negative_journey",
            profile_dominance_pruned,
            dp_bound_pruned_labels=dp_stats.get("bound_pruned_labels", 0),
            dp_cross_count_pruned_labels=dp_stats.get("cross_count_pruned_labels", 0),
            profile_cut_penalty_pruned=cut_penalty_pruned,
            profile_catalog_hit=bool(catalog_stats.get("hit", 0)),
            profile_catalog_size=int(catalog_stats.get("size", 0)),
            duplicate_candidate_scan_count=dp_stats.get("duplicate_candidate_scan_count", 0),
            duplicate_candidates_filtered=dp_stats.get("duplicate_candidates_filtered", 0),
            duplicate_scan_limited=bool(dp_stats.get("duplicate_scan_limited", 0)),
            profile_generation_time=generation_elapsed,
            profile_filter_time=profile_filter_time,
            profile_dp_time=final_dp_time,
            **_dp_profile_stats_kwargs(dp_stats),
            **_resource_stats_kwargs(catalog_stats),
            **_profile_mask_diagnostic_kwargs(profiles, dp_stats, config),
        )
    journeys, existing_filtered, weak_filtered = _instantiate_profile_journey_candidates(
        data,
        profiles,
        selected_candidates,
        config,
        eps=float(config.eps),
        forbidden_journey_signatures=forbidden_journey_signatures,
        dominant_task_set_costs=dominant_task_set_costs,
        max_journeys=max_returned,
        branch_constraints=branch_constraints,
        duals=duals,
        cuts=cuts,
        dp_stats=dp_stats,
    )
    if not journeys:
        reason_text = "selected_profiles_not_a_valid_journey"
        if weak_filtered > 0:
            reason_text = "weak_negative_journeys_filtered"
        if (
            existing_filtered > 0
            or int(dp_stats.get("duplicate_candidates_filtered", 0)) > 0
            or int(dp_stats.get("dominated_task_set_candidates_filtered", 0)) > 0
        ):
            reason_text = "negative_journeys_already_in_pool"
        if best_partial_result is not None:
            return best_partial_result
        return JourneyPricingResult(
            [],
            False,
            objective,
            generated,
            evaluated,
            len(profiles),
            0,
            "INCOMPLETE",
            reason_text,
            profile_dominance_pruned,
            existing_filtered,
            cut_penalty_pruned,
            weak_filtered,
            dp_stats.get("bound_pruned_labels", 0),
            dp_stats.get("cross_count_pruned_labels", 0),
            profile_catalog_hit=bool(catalog_stats.get("hit", 0)),
            profile_catalog_size=int(catalog_stats.get("size", 0)),
            duplicate_candidate_scan_count=dp_stats.get("duplicate_candidate_scan_count", 0),
            duplicate_candidates_filtered=dp_stats.get("duplicate_candidates_filtered", 0),
            duplicate_scan_limited=bool(dp_stats.get("duplicate_scan_limited", 0)),
            profile_generation_time=generation_elapsed,
            profile_filter_time=profile_filter_time,
            profile_dp_time=final_dp_time,
            **_dp_profile_stats_kwargs(dp_stats),
            **_resource_stats_kwargs(catalog_stats),
            **_profile_mask_diagnostic_kwargs(profiles, dp_stats, config),
        )
    return JourneyPricingResult(
        journeys,
        bool(exhausted),
        objective,
        generated,
        evaluated,
        len(profiles),
        max((len(selected) for selected, _obj in selected_candidates), default=0),
        "OPTIMAL" if exhausted else "INCOMPLETE",
        "negative_journey" if exhausted else "partial_negative_journey",
        profile_dominance_pruned,
        existing_filtered,
        cut_penalty_pruned,
        weak_filtered,
        dp_stats.get("bound_pruned_labels", 0),
        dp_stats.get("cross_count_pruned_labels", 0),
        profile_catalog_hit=bool(catalog_stats.get("hit", 0)),
        profile_catalog_size=int(catalog_stats.get("size", 0)),
        duplicate_candidate_scan_count=dp_stats.get("duplicate_candidate_scan_count", 0),
        duplicate_candidates_filtered=dp_stats.get("duplicate_candidates_filtered", 0),
        duplicate_scan_limited=bool(dp_stats.get("duplicate_scan_limited", 0)),
        profile_generation_time=generation_elapsed,
        profile_filter_time=profile_filter_time,
        profile_dp_time=final_dp_time,
        **_dp_profile_stats_kwargs(dp_stats),
        **_resource_stats_kwargs(catalog_stats),
        **_profile_mask_diagnostic_kwargs(profiles, dp_stats, config),
    )


def _duplicate_stats_kwargs(dp_stats: dict[str, int]) -> dict[str, Any]:
    return {
        "duplicate_candidate_scan_count": int(dp_stats.get("duplicate_candidate_scan_count", 0)),
        "duplicate_candidates_filtered": int(dp_stats.get("duplicate_candidates_filtered", 0)),
        "duplicate_scan_limited": bool(dp_stats.get("duplicate_scan_limited", 0)),
        "dp_disjoint_bound_pruned_labels": int(dp_stats.get("disjoint_bound_pruned_labels", 0)),
        "dp_processed_labels": int(dp_stats.get("processed_labels", 0)),
        "dp_state_count": int(dp_stats.get("state_count", 0)),
        "dp_profile_record_scans": int(dp_stats.get("profile_record_scans", 0)),
        "dp_profile_time_filtered": int(dp_stats.get("profile_time_filtered", 0)),
        "dp_extension_attempts": int(dp_stats.get("extension_attempts", 0)),
        "dp_label_cap_pruned": int(dp_stats.get("label_cap_pruned", 0)),
        "dp_same_completion_pruned_labels": int(dp_stats.get("same_completion_pruned_labels", 0)),
    }


def _profile_candidate_return_limit(config: JourneyPricingConfig, max_returned: int) -> int:
    """Bound how many rough profile-DP candidates are rescored by true RC.

    ``max_returned_journeys`` is the number of columns that may be added to the
    RMP.  Hard cases need a wider rough-candidate scan before true-RC filtering,
    otherwise weak/dominated rough candidates can hide later valid columns.  This
    helper deliberately keeps the final add-column limit separate from the
    candidate scan width.
    """

    final_limit = max(1, int(max_returned))
    duplicate_limit = final_limit * max(1, int(config.duplicate_retry_factor))
    scan_factor = max(1, int(config.profile_true_rc_candidate_scan_factor))
    scan_limit = max(duplicate_limit, final_limit * scan_factor)
    cap = max(0, int(config.profile_true_rc_candidate_scan_max_candidates))
    if cap > 0:
        # 不能让 cap 小于最终加列上限，否则会把“扫描宽度”反过来变成
        # 新的列数截断，破坏 max_returned_journeys 的原有语义。
        scan_limit = max(final_limit, min(scan_limit, cap))
    return int(scan_limit)


def _dp_profile_stats_kwargs(dp_stats: dict[str, int]) -> dict[str, Any]:
    return {
        "dp_processed_labels": int(dp_stats.get("processed_labels", 0)),
        "dp_state_count": int(dp_stats.get("state_count", 0)),
        "dp_profile_record_scans": int(dp_stats.get("profile_record_scans", 0)),
        "dp_profile_time_filtered": int(dp_stats.get("profile_time_filtered", 0)),
        "dp_extension_attempts": int(dp_stats.get("extension_attempts", 0)),
        "dp_label_cap_pruned": int(dp_stats.get("label_cap_pruned", 0)),
        "dp_same_completion_pruned_labels": int(dp_stats.get("same_completion_pruned_labels", 0)),
        "profile_negative_candidate_count": int(dp_stats.get("negative_candidate_count", 0)),
        "profile_negative_unique_mask_count": int(dp_stats.get("negative_unique_mask_count", 0)),
        "profile_negative_new_mask_count": int(dp_stats.get("negative_new_mask_count", 0)),
        "profile_negative_selected_candidate_count": int(dp_stats.get("negative_selected_candidate_count", 0)),
        "profile_negative_selected_new_mask_count": int(dp_stats.get("negative_selected_new_mask_count", 0)),
        "profile_negative_selected_replacement_mask_count": int(
            dp_stats.get("negative_selected_replacement_mask_count", 0)
        ),
        "profile_materialization_candidate_count": int(dp_stats.get("materialization_candidate_count", 0)),
        "profile_materialization_candidate_selected_for_scan_count": int(
            dp_stats.get("materialization_candidate_selected_for_scan_count", 0)
        ),
        "profile_materialization_candidate_cap_filtered": int(
            dp_stats.get("materialization_candidate_cap_filtered", 0)
        ),
        "profile_materialization_selected_candidate_count": int(
            dp_stats.get("materialization_selected_candidate_count", 0)
        ),
        "profile_no_negative_materialization_candidate_count": int(
            dp_stats.get("no_negative_materialization_candidate_count", 0)
        ),
        "profile_no_negative_materialization_selected_for_scan_count": int(
            dp_stats.get("no_negative_materialization_selected_for_scan_count", 0)
        ),
        "profile_no_negative_materialization_candidate_cap_filtered": int(
            dp_stats.get("no_negative_materialization_candidate_cap_filtered", 0)
        ),
        "profile_no_negative_materialization_selected_candidate_count": int(
            dp_stats.get("no_negative_materialization_selected_candidate_count", 0)
        ),
        "profile_replacement_materialization_candidate_count": int(
            dp_stats.get("replacement_materialization_candidate_count", 0)
        ),
        "profile_replacement_materialization_selected_for_scan_count": int(
            dp_stats.get("replacement_materialization_selected_for_scan_count", 0)
        ),
        "profile_replacement_materialization_candidate_cap_filtered": int(
            dp_stats.get("replacement_materialization_candidate_cap_filtered", 0)
        ),
        "profile_replacement_materialization_selected_candidate_count": int(
            dp_stats.get("replacement_materialization_selected_candidate_count", 0)
        ),
        "profile_cross_count_materialization_candidate_count": int(
            dp_stats.get("cross_count_materialization_candidate_count", 0)
        ),
        "profile_cross_count_materialization_selected_for_scan_count": int(
            dp_stats.get("cross_count_materialization_selected_for_scan_count", 0)
        ),
        "profile_cross_count_materialization_candidate_cap_filtered": int(
            dp_stats.get("cross_count_materialization_candidate_cap_filtered", 0)
        ),
        "profile_cross_count_materialization_selected_candidate_count": int(
            dp_stats.get("cross_count_materialization_selected_candidate_count", 0)
        ),
        "profile_materialization_infeasible_candidates_filtered": int(
            dp_stats.get("profile_materialization_infeasible_candidates_filtered", 0)
        ),
        "profile_selected_unmaterialized_candidate_count": int(
            dp_stats.get("profile_selected_unmaterialized_candidate_count", 0)
        ),
        "profile_weak_filtered_materialized_count": int(
            dp_stats.get("profile_weak_filtered_materialized_count", 0)
        ),
        "profile_weak_filtered_best_rough_rc": dp_stats.get("profile_weak_filtered_best_rough_rc"),
        "profile_weak_filtered_best_true_rc": dp_stats.get("profile_weak_filtered_best_true_rc"),
        "profile_weak_filtered_max_true_minus_rough": dp_stats.get(
            "profile_weak_filtered_max_true_minus_rough"
        ),
        "profile_weak_filtered_max_true_minus_rough_mask": dp_stats.get(
            "profile_weak_filtered_max_true_minus_rough_mask"
        ),
        "dominated_task_set_journeys_filtered": int(
            dp_stats.get("dominated_task_set_candidates_filtered", 0)
        ),
    }


def _profile_mask_diagnostic_kwargs(
    profiles: list[_SortieProfile],
    dp_stats: dict[str, Any] | None,
    pricing_config: JourneyPricingConfig | None = None,
) -> dict[str, Any]:
    if pricing_config is None or not bool(pricing_config.profile_mask_diagnostics_enabled):
        return {
            "diagnostic_profile_task_masks": frozenset(),
            "diagnostic_profile_trip_masks": frozenset(),
            "diagnostic_reachable_task_masks": frozenset(),
            "diagnostic_negative_task_masks": frozenset(),
            "diagnostic_selected_task_masks": frozenset(),
            "diagnostic_best_objective_by_mask": {},
            "diagnostic_best_profile_contribution_by_mask": {},
        }
    stats = dp_stats or {}
    best_by_mask = stats.get("best_objective_by_mask", {})
    if not isinstance(best_by_mask, dict):
        best_by_mask = {}
    best_profile_by_mask: dict[int, float] = {}
    if pricing_config is not None and bool(pricing_config.profile_best_contribution_diagnostics_enabled):
        for profile in profiles:
            mask = int(profile.mask)
            if mask <= 0:
                continue
            contribution = float(profile.contribution)
            old = best_profile_by_mask.get(mask)
            if old is None or contribution < float(old) - 1.0e-9:
                best_profile_by_mask[mask] = contribution
        cap = max(1, int(pricing_config.profile_best_contribution_diagnostics_max_masks))
        best_profile_by_mask = dict(
            sorted(
                best_profile_by_mask.items(),
                key=lambda item: (round(float(item[1]), 9), int(item[0])),
            )[:cap]
        )
    return {
        "diagnostic_profile_task_masks": frozenset(int(profile.mask) for profile in profiles if int(profile.mask) > 0),
        "diagnostic_profile_trip_masks": frozenset(int(profile.mask) for profile in profiles if int(profile.mask) > 0),
        "diagnostic_reachable_task_masks": frozenset(int(mask) for mask in stats.get("reachable_task_masks", ())),
        "diagnostic_negative_task_masks": frozenset(int(mask) for mask in stats.get("negative_task_masks", ())),
        "diagnostic_selected_task_masks": frozenset(int(mask) for mask in stats.get("selected_task_masks", ())),
        "diagnostic_best_objective_by_mask": {
            int(mask): float(value)
            for mask, value in best_by_mask.items()
        },
        "diagnostic_best_profile_contribution_by_mask": {
            int(mask): round(float(value), 9)
            for mask, value in best_profile_by_mask.items()
        },
    }


def _resource_stats_kwargs(catalog_stats: dict[str, int] | None) -> dict[str, Any]:
    return {
        "task_set_resource_pruned_sequences": int(
            (catalog_stats or {}).get("task_set_resource_pruned_sequences", 0)
        ),
        "partial_profile_bound_pruned_labels": int(
            (catalog_stats or {}).get("partial_profile_bound_pruned_labels", 0)
        ),
        "profile_mask_cap_pruned": int((catalog_stats or {}).get("profile_mask_cap_pruned", 0)),
        "profile_completion_time_pruned": int((catalog_stats or {}).get("profile_completion_time_pruned", 0)),
        "branch_mask_pruned_sequences": int((catalog_stats or {}).get("branch_mask_pruned_sequences", 0)),
        "label_physical_catalog": bool((catalog_stats or {}).get("label_physical_catalog", 0)),
        "label_physical_catalog_exhausted": bool(
            (catalog_stats or {}).get("label_physical_catalog_exhausted", 0)
        ),
        "label_resume_heap": int((catalog_stats or {}).get("label_resume_heap", 0)),
        "label_resume_profiles": int((catalog_stats or {}).get("label_resume_profiles", 0)),
        "label_resume_exhausted": bool((catalog_stats or {}).get("label_resume_exhausted", 0)),
        "streaming_callback_exhaust_triggered": bool(
            (catalog_stats or {}).get("streaming_callback_exhaust_triggered", 0)
        ),
        "streaming_callback_exhaust_threshold": int(
            (catalog_stats or {}).get("streaming_callback_exhaust_threshold", 0)
        ),
    }


def _profile_dp_incomplete_reason(status: str, dp_stats: dict[str, int]) -> str:
    if int(dp_stats.get("duplicate_scan_limited", 0)) > 0:
        return "duplicate_scan_incomplete"
    if (
        int(dp_stats.get("duplicate_candidates_filtered", 0)) > 0
        or int(dp_stats.get("dominated_task_set_candidates_filtered", 0)) > 0
    ):
        return "negative_journeys_already_in_pool"
    return str(status) if str(status) != "INCOMPLETE" else "profile_dp_incomplete"


def _generate_negative_sortie_profiles(
    data: FutureData,
    duals: FutureDuals,
    *,
    base_reduced_cost: float,
    config: JourneyPricingConfig,
    trip_cache: dict[tuple, tuple[tuple[TimedTrip, ...], int, int]] | None,
    started: float,
    resource_cache: dict[tuple, Any] | None = None,
    deadline: float | None = None,
    journey_cut_duals: dict[int, float] | None = None,
    journey_cuts: tuple[FutureCut, ...] = tuple(),
    stream_callback: Any | None = None,
    stream_profile_batch_size: int = 0,
    catalog_stats: dict[str, int] | None = None,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
) -> tuple[list[_SortieProfile], int, int, float | None, bool, str, int]:
    vehicle = int(data.vehicles[0])
    max_tasks = _max_tasks_per_trip(data, int(config.max_tasks_per_trip))
    task_order = _task_order(
        data,
        duals,
        vehicle,
        PricingConfig(heuristic=False, heuristic_top_tasks=0),
    )
    pricing_config = PricingConfig(
        time_bucket_size=float(config.time_bucket_size),
        max_tasks_per_trip=int(config.max_tasks_per_trip),
        max_sequences=int(config.max_sequences),
        max_timed_evaluations=int(config.max_timed_evaluations),
        eps=float(config.eps),
        heuristic=False,
        time_limit=float(config.time_limit),
        start_time_step=float(config.start_time_step),
        max_path_combinations_per_sequence=int(config.max_path_combinations_per_sequence),
        path_dominance_enabled=bool(config.path_dominance_enabled),
        start_optimization_enabled=bool(config.start_optimization_enabled),
        generalized_partial_dominance_enabled=bool(config.generalized_partial_dominance_enabled),
    )
    generated = 0
    evaluated = 0
    best_profile_rc: float | None = None
    exhausted = True
    reason = ""
    profiles_by_key: dict[tuple, _SortieProfile] = {}
    profiles_by_mask: dict[int, list[_SortieProfile]] = {}
    task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
    catalog_key = _sortie_profile_catalog_key(data, config, max_tasks, branch_constraints=branch_constraints)
    if catalog_key is not None and trip_cache is not None and catalog_key in trip_cache:
        cached_catalog, cached_generated, cached_evaluated = trip_cache[catalog_key]  # type: ignore[assignment]
        profiles, best_profile_rc, cut_penalty_pruned = _filter_sortie_profile_catalog(
            cached_catalog,  # type: ignore[arg-type]
            duals,
            base_reduced_cost=base_reduced_cost,
            config=config,
            journey_cut_duals=journey_cut_duals or {},
            journey_cuts=journey_cuts,
            task_to_bit=task_to_bit,
            branch_constraints=branch_constraints,
        )
        if catalog_stats is not None:
            catalog_stats["hit"] = 1
            catalog_stats["size"] = len(cached_catalog)  # type: ignore[arg-type]
        return profiles, int(cached_generated), int(cached_evaluated), best_profile_rc, True, "", cut_penalty_pruned
    threshold = max(0.0, -float(base_reduced_cost)) + float(config.eps)
    cut_penalty_enabled = _profile_cut_penalty_pruning_safe(journey_cut_duals or {}, journey_cuts)
    if (duals.cuts or {}) or ((journey_cut_duals or {}) and not cut_penalty_enabled):
        # Cut contributions are evaluated on the final journey mask.  Keep all
        # potentially feasible sortie profiles to preserve exactness.
        threshold = float("inf")
    cut_masks = _cut_masks(data, journey_cuts)
    cut_penalty_pruned = 0
    next_stream_profile_count = max(1, int(stream_profile_batch_size)) if stream_callback is not None else 0
    stream_callback_no_result_streak = 0
    online_dominance = bool(config.profile_online_dominance_enabled) and bool(config.profile_cross_dominance_enabled)
    online_dominance_pruned = 0

    def current_profiles() -> list[_SortieProfile]:
        if not online_dominance:
            return list(profiles_by_key.values())
        return [profile for group in profiles_by_mask.values() for profile in group]

    def record_online_stats() -> None:
        if catalog_stats is not None and online_dominance:
            catalog_stats["online_dominance_pruned"] = int(online_dominance_pruned)

    task_set_bound_cache = (
        _TaskSetReducedCostLowerBoundCache(data, duals, vehicle, task_to_bit)
        if bool(config.task_set_bound_pruning_enabled)
        else None
    )
    if (
        bool(config.profile_labeling_enabled)
        and not bool(data.instance.get("scheduling", {}).get("task_waiting_allowed", True))
    ):
        if bool(config.profile_labeling_physical_catalog_resume_enabled) and trip_cache is not None:
            return _generate_negative_sortie_profiles_by_label_physical_catalog(
                data,
                duals,
                base_reduced_cost=base_reduced_cost,
                config=config,
                deadline=deadline,
                task_order=task_order,
                task_to_bit=task_to_bit,
                trip_cache=trip_cache,
                resource_cache=resource_cache,
                catalog_stats=catalog_stats,
                journey_cut_duals=journey_cut_duals or {},
                journey_cuts=journey_cuts,
                stream_callback=stream_callback,
                stream_profile_batch_size=stream_profile_batch_size,
                branch_constraints=branch_constraints,
            )
        labeled = _generate_negative_sortie_profiles_by_labels(
            data,
            duals,
            base_reduced_cost=base_reduced_cost,
            config=config,
            deadline=deadline,
            task_order=task_order,
            threshold=threshold,
            task_to_bit=task_to_bit,
            trip_cache=trip_cache,
            resource_cache=resource_cache,
            catalog_stats=catalog_stats,
            stream_callback=stream_callback,
            stream_profile_batch_size=stream_profile_batch_size,
            branch_constraints=branch_constraints,
        )
        return (*labeled, 0)
    if (
        catalog_key is not None
        and trip_cache is not None
        and stream_callback is None
        and bool(config.profile_catalog_resume_enabled)
    ):
        resume_key = (*catalog_key, "resume_v1")
        state = trip_cache.get(resume_key)
        if not isinstance(state, _SortieProfileCatalogState):
            state = _SortieProfileCatalogState(profiles=[], keys=set())
            trip_cache[resume_key] = state  # type: ignore[assignment]
        before_generated = int(state.generated)
        before_evaluated = int(state.evaluated)
        _resume_sortie_profile_catalog(
            data,
            config,
            trip_cache,
            state,
            deadline=deadline,
            max_tasks=max_tasks,
            task_order=tuple(int(task) for task in data.tasks),
            branch_constraints=branch_constraints,
        )
        if catalog_stats is not None:
            catalog_stats["hit"] = int(before_evaluated > 0)
            catalog_stats["size"] = len(state.profiles)
            catalog_stats["resume"] = 1
            catalog_stats["resume_exhausted"] = int(state.exhausted)
        profiles, best_profile_rc, cut_penalty_pruned = _filter_sortie_profile_catalog(
            state.profiles,
            duals,
            base_reduced_cost=base_reduced_cost,
            config=config,
            journey_cut_duals=journey_cut_duals or {},
            journey_cuts=journey_cuts,
            task_to_bit=task_to_bit,
            branch_constraints=branch_constraints,
        )
        return (
            profiles,
            int(state.generated) - before_generated,
            int(state.evaluated) - before_evaluated,
            best_profile_rc,
            bool(state.exhausted),
            str(state.reason),
            cut_penalty_pruned,
        )
    if catalog_key is not None and trip_cache is not None and stream_callback is None:
        catalog, generated, evaluated, catalog_exhausted, catalog_reason = _build_sortie_profile_catalog(
            data,
            config,
            trip_cache,
            deadline=deadline,
            max_tasks=max_tasks,
            task_order=tuple(int(task) for task in data.tasks),
            branch_constraints=branch_constraints,
        )
        if catalog_exhausted and len(catalog) <= int(config.profile_catalog_max_profiles):
            trip_cache[catalog_key] = (tuple(catalog), int(generated), int(evaluated))  # type: ignore[assignment]
        if catalog_stats is not None:
            catalog_stats["hit"] = 0
            catalog_stats["size"] = len(catalog)
        profiles, best_profile_rc, cut_penalty_pruned = _filter_sortie_profile_catalog(
            catalog,
            duals,
            base_reduced_cost=base_reduced_cost,
            config=config,
            journey_cut_duals=journey_cut_duals or {},
            journey_cuts=journey_cuts,
            task_to_bit=task_to_bit,
            branch_constraints=branch_constraints,
        )
        return profiles, generated, evaluated, best_profile_rc, catalog_exhausted, catalog_reason, cut_penalty_pruned
    try:
        task_set_lb_pruned_masks: set[int] = set()
        for size in range(1, max_tasks + 1):
            for sequence in itertools.permutations(task_order, size):
                if deadline is not None and time.perf_counter() > deadline:
                    record_online_stats()
                    return current_profiles(), generated, evaluated, best_profile_rc, False, "time_limit", cut_penalty_pruned
                mask = 0
                for task in set(sequence):
                    mask |= 1 << task_to_bit[int(task)]
                if task_set_bound_cache is not None and mask in task_set_lb_pruned_masks:
                    if catalog_stats is not None:
                        catalog_stats["task_set_bound_pruned_sequences"] = int(
                            catalog_stats.get("task_set_bound_pruned_sequences", 0)
                        ) + 1
                    continue
                if not _sortie_profile_mask_allowed_by_branch(mask, branch_constraints, task_to_bit):
                    if catalog_stats is not None:
                        catalog_stats["branch_mask_pruned_sequences"] = int(
                            catalog_stats.get("branch_mask_pruned_sequences", 0)
                        ) + 1
                    continue
                profile_cut_penalty = _profile_cut_penalty(
                    mask,
                    journey_cut_duals or {},
                    journey_cuts,
                    cut_masks,
                    enabled=cut_penalty_enabled,
                )
                task_set_lb = (
                    float("-inf")
                    if task_set_bound_cache is None
                    else task_set_bound_cache.value(mask) + profile_cut_penalty
                )
                if task_set_bound_cache is not None and task_set_lb >= threshold:
                    task_set_lb_pruned_masks.add(mask)
                    if catalog_stats is not None:
                        catalog_stats["task_set_bound_pruned_sequences"] = int(
                            catalog_stats.get("task_set_bound_pruned_sequences", 0)
                        ) + 1
                    cut_penalty_pruned += int(profile_cut_penalty > 0.0)
                    continue
                if not partial_sequence_allowed(tuple(sequence), vehicle, tuple()):
                    continue
                if not _sequence_resource_precheck(data, tuple(sequence)):
                    continue
                generated += 1
                if int(config.max_sequences) > 0 and generated > int(config.max_sequences):
                    record_online_stats()
                    return current_profiles(), generated, evaluated, best_profile_rc, False, "sequence_budget", cut_penalty_pruned
                sequence_lb = _sequence_reduced_cost_lower_bound(
                    data,
                    tuple(sequence),
                    vehicle,
                    duals,
                    tuple(),
                    tuple(),
                    "phase2",
                )
                sequence_lb += profile_cut_penalty
                if sequence_lb >= threshold:
                    cut_penalty_pruned += int(profile_cut_penalty > 0.0)
                    continue
                arc_profiles, pruned, _cache_hit = _optimized_arc_profiles_for_sequence(
                    data,
                    tuple(sequence),
                    pricing_config,
                    trip_cache,
                    True,
                    tuple(),
                    vehicle,
                    True,
                    deadline=deadline,
                )
                if pruned > 0 and not bool(config.path_dominance_enabled):
                    exhausted = False
                    reason = "unsafe_profile_pruning"
                dual_sum = sum(float(duals.cover.get(int(task), 0.0)) for task in set(sequence))
                for arc_profile in arc_profiles:
                    if deadline is not None and time.perf_counter() > deadline:
                        record_online_stats()
                        return current_profiles(), generated, evaluated, best_profile_rc, False, "time_limit", cut_penalty_pruned
                    evaluated += 1
                    profile = arc_profile.profile
                    contribution = float(profile.cost) - dual_sum
                    best_profile_rc = contribution if best_profile_rc is None else min(best_profile_rc, contribution)
                    if contribution + profile_cut_penalty >= threshold:
                        cut_penalty_pruned += int(profile_cut_penalty > 0.0)
                        continue
                    key = (
                        tuple(int(task) for task in sequence),
                        tuple(option.option_id for option in arc_profile.arc_options),
                        round(float(profile.lower_start), 6),
                        round(float(profile.upper_start), 6),
                        round(float(profile.end_offset), 6),
                    )
                    candidate = _SortieProfile(
                        sequence=tuple(int(task) for task in sequence),
                        arc_options=arc_profile.arc_options,
                        lower_start=float(profile.lower_start),
                        upper_start=float(profile.upper_start),
                        end_offset=float(profile.end_offset),
                        cost=float(profile.cost),
                        mask=mask,
                        contribution=contribution,
                    )
                    old = profiles_by_key.get(key)
                    if old is None or candidate.contribution < old.contribution - 1.0e-9:
                        profiles_by_key[key] = candidate
                        if online_dominance:
                            added, pruned = _add_sortie_profile_skyline(profiles_by_mask, candidate)
                            online_dominance_pruned += int(pruned)
                            if not added:
                                online_dominance_pruned += 1
                    if stream_callback is not None and len(profiles_by_key) >= next_stream_profile_count:
                        result = stream_callback(
                            list(profiles_by_key.values()),
                            generated,
                            evaluated,
                            best_profile_rc,
                            cut_penalty_pruned,
                        )
                        if result is not None:
                            raise _StreamingPricingStop(result)
                        stream_callback_no_result_streak += 1
                        next_stream_profile_count = _streaming_next_profile_count(
                            len(profiles_by_key),
                            int(stream_profile_batch_size),
                            int(stream_callback_no_result_streak),
                            config,
                        )
                        if int(config.max_candidate_trips) > 0 and len(profiles_by_key) > int(config.max_candidate_trips):
                            record_online_stats()
                            return current_profiles(), generated, evaluated, best_profile_rc, False, "candidate_profile_budget", cut_penalty_pruned
                        if int(config.max_timed_evaluations) > 0 and evaluated > int(config.max_timed_evaluations):
                            record_online_stats()
                            return current_profiles(), generated, evaluated, best_profile_rc, False, "profile_evaluation_budget", cut_penalty_pruned
    except _PricingTimeout:
        record_online_stats()
        return current_profiles(), generated, evaluated, best_profile_rc, False, "time_limit", cut_penalty_pruned
    record_online_stats()
    return current_profiles(), generated, evaluated, best_profile_rc, exhausted, reason, cut_penalty_pruned


def _sortie_profile_catalog_key(
    data: FutureData,
    config: JourneyPricingConfig,
    max_tasks: int,
    *,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
) -> tuple | None:
    if not bool(config.profile_catalog_enabled):
        return None
    if len(data.tasks) > int(config.profile_catalog_max_tasks):
        return None
    if int(config.max_candidate_trips) > 0:
        return None
    if bool(config.profile_labeling_enabled):
        return None
    return (
        "journey_sortie_profile_catalog_v2",
        str(data.instance_path),
        _branch_constraints_cache_key(branch_constraints),
        int(max_tasks),
        int(config.max_sequences),
        int(config.max_timed_evaluations),
        round(float(config.time_bucket_size), 9),
        round(float(config.start_time_step), 9),
        int(config.max_path_combinations_per_sequence),
        bool(config.path_dominance_enabled),
        bool(config.start_optimization_enabled),
    )


def _resume_sortie_profile_catalog(
    data: FutureData,
    config: JourneyPricingConfig,
    trip_cache: dict[tuple, tuple[tuple[TimedTrip, ...], int, int]] | None,
    state: _SortieProfileCatalogState,
    *,
    deadline: float | None,
    max_tasks: int,
    task_order: tuple[int, ...],
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
) -> None:
    if bool(state.exhausted):
        return
    vehicle = int(data.vehicles[0])
    pricing_config = PricingConfig(
        time_bucket_size=float(config.time_bucket_size),
        max_tasks_per_trip=int(config.max_tasks_per_trip),
        max_sequences=int(config.max_sequences),
        max_timed_evaluations=int(config.max_timed_evaluations),
        eps=float(config.eps),
        heuristic=False,
        time_limit=float(config.time_limit),
        start_time_step=float(config.start_time_step),
        max_path_combinations_per_sequence=int(config.max_path_combinations_per_sequence),
        path_dominance_enabled=bool(config.path_dominance_enabled),
        start_optimization_enabled=bool(config.start_optimization_enabled),
        generalized_partial_dominance_enabled=bool(config.generalized_partial_dominance_enabled),
    )
    task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
    try:
        for size in range(max(1, int(state.next_size)), int(max_tasks) + 1):
            start_index = int(state.next_permutation_index) if size == int(state.next_size) else 0
            for permutation_index, sequence in enumerate(itertools.permutations(task_order, size)):
                if permutation_index < start_index:
                    continue
                if deadline is not None and time.perf_counter() > deadline:
                    state.reason = "time_limit"
                    return
                sequence = tuple(int(task) for task in sequence)
                mask = 0
                for task in set(sequence):
                    mask |= 1 << task_to_bit[int(task)]
                if not _sortie_profile_mask_allowed_by_branch(mask, branch_constraints, task_to_bit):
                    state.next_size = size
                    state.next_permutation_index = permutation_index + 1
                    continue
                if not partial_sequence_allowed(sequence, vehicle, tuple()):
                    state.next_size = size
                    state.next_permutation_index = permutation_index + 1
                    continue
                if not _sequence_resource_precheck(data, sequence):
                    state.next_size = size
                    state.next_permutation_index = permutation_index + 1
                    continue
                if int(config.max_sequences) > 0 and int(state.generated) + 1 > int(config.max_sequences):
                    state.reason = "sequence_budget"
                    return
                arc_profiles, _pruned, _cache_hit = _optimized_arc_profiles_for_sequence(
                    data,
                    sequence,
                    pricing_config,
                    trip_cache,
                    True,
                    tuple(),
                    vehicle,
                    True,
                    deadline=deadline,
                )
                for arc_profile in arc_profiles:
                    if deadline is not None and time.perf_counter() > deadline:
                        state.reason = "time_limit"
                        return
                    profile = arc_profile.profile
                    key = (
                        sequence,
                        tuple(option.option_id for option in arc_profile.arc_options),
                        round(float(profile.lower_start), 6),
                        round(float(profile.upper_start), 6),
                        round(float(profile.end_offset), 6),
                    )
                    if key not in state.keys:
                        state.keys.add(key)
                        state.profiles.append(
                            _SortieProfile(
                                sequence=sequence,
                                arc_options=arc_profile.arc_options,
                                lower_start=float(profile.lower_start),
                                upper_start=float(profile.upper_start),
                                end_offset=float(profile.end_offset),
                                cost=float(profile.cost),
                                mask=mask,
                                contribution=float(profile.cost),
                            )
                        )
                    state.evaluated += 1
                    if len(state.profiles) > int(config.profile_catalog_max_profiles):
                        state.reason = "profile_catalog_budget"
                        return
                    if int(config.max_timed_evaluations) > 0 and int(state.evaluated) > int(config.max_timed_evaluations):
                        state.reason = "profile_evaluation_budget"
                        return
                state.generated += 1
                state.next_size = size
                state.next_permutation_index = permutation_index + 1
            state.next_size = size + 1
            state.next_permutation_index = 0
        state.exhausted = True
        state.reason = ""
    except _PricingTimeout:
        state.reason = "time_limit"


def _build_sortie_profile_catalog(
    data: FutureData,
    config: JourneyPricingConfig,
    trip_cache: dict[tuple, tuple[tuple[TimedTrip, ...], int, int]] | None,
    *,
    deadline: float | None,
    max_tasks: int,
    task_order: tuple[int, ...],
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
) -> tuple[list[_SortieProfile], int, int, bool, str]:
    vehicle = int(data.vehicles[0])
    pricing_config = PricingConfig(
        time_bucket_size=float(config.time_bucket_size),
        max_tasks_per_trip=int(config.max_tasks_per_trip),
        max_sequences=int(config.max_sequences),
        max_timed_evaluations=int(config.max_timed_evaluations),
        eps=float(config.eps),
        heuristic=False,
        time_limit=float(config.time_limit),
        start_time_step=float(config.start_time_step),
        max_path_combinations_per_sequence=int(config.max_path_combinations_per_sequence),
        path_dominance_enabled=bool(config.path_dominance_enabled),
        start_optimization_enabled=bool(config.start_optimization_enabled),
        generalized_partial_dominance_enabled=bool(config.generalized_partial_dominance_enabled),
    )
    task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
    generated = 0
    evaluated = 0
    exhausted = True
    reason = ""
    catalog: list[_SortieProfile] = []
    try:
        for size in range(1, int(max_tasks) + 1):
            for sequence in itertools.permutations(task_order, size):
                if deadline is not None and time.perf_counter() > deadline:
                    return catalog, generated, evaluated, False, "time_limit"
                mask = 0
                for task in set(sequence):
                    mask |= 1 << task_to_bit[int(task)]
                if not _sortie_profile_mask_allowed_by_branch(mask, branch_constraints, task_to_bit):
                    continue
                if not partial_sequence_allowed(tuple(sequence), vehicle, tuple()):
                    continue
                if not _sequence_resource_precheck(data, tuple(sequence)):
                    continue
                generated += 1
                if int(config.max_sequences) > 0 and generated > int(config.max_sequences):
                    return catalog, generated, evaluated, False, "sequence_budget"
                arc_profiles, _pruned, _cache_hit = _optimized_arc_profiles_for_sequence(
                    data,
                    tuple(sequence),
                    pricing_config,
                    trip_cache,
                    True,
                    tuple(),
                    vehicle,
                    True,
                    deadline=deadline,
                )
                for arc_profile in arc_profiles:
                    if deadline is not None and time.perf_counter() > deadline:
                        return catalog, generated, evaluated, False, "time_limit"
                    evaluated += 1
                    profile = arc_profile.profile
                    catalog.append(
                        _SortieProfile(
                            sequence=tuple(int(task) for task in sequence),
                            arc_options=arc_profile.arc_options,
                            lower_start=float(profile.lower_start),
                            upper_start=float(profile.upper_start),
                            end_offset=float(profile.end_offset),
                            cost=float(profile.cost),
                            mask=mask,
                            contribution=float(profile.cost),
                        )
                    )
                    if len(catalog) > int(config.profile_catalog_max_profiles):
                        return catalog, generated, evaluated, False, "profile_catalog_budget"
                    if int(config.max_timed_evaluations) > 0 and evaluated > int(config.max_timed_evaluations):
                        return catalog, generated, evaluated, False, "profile_evaluation_budget"
    except _PricingTimeout:
        return catalog, generated, evaluated, False, "time_limit"
    return catalog, generated, evaluated, exhausted, reason


def _filter_sortie_profile_catalog(
    catalog: tuple[_SortieProfile, ...] | list[_SortieProfile],
    duals: FutureDuals,
    *,
    base_reduced_cost: float,
    config: JourneyPricingConfig,
    journey_cut_duals: dict[int, float],
    journey_cuts: tuple[FutureCut, ...],
    task_to_bit: dict[int, int],
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
) -> tuple[list[_SortieProfile], float | None, int]:
    threshold = max(0.0, -float(base_reduced_cost)) + float(config.eps)
    cut_penalty_enabled = _profile_cut_penalty_pruning_safe(journey_cut_duals or {}, journey_cuts)
    if (duals.cuts or {}) or ((journey_cut_duals or {}) and not cut_penalty_enabled):
        threshold = float("inf")
    cut_masks = _cut_masks_from_task_bits(journey_cuts, task_to_bit)
    cut_penalty_pruned = 0
    best_profile_rc: float | None = None
    profiles: list[_SortieProfile] = []
    bit_duals = [0.0] * max(1, (max(task_to_bit.values()) + 1 if task_to_bit else 0))
    for task, bit in task_to_bit.items():
        if int(bit) >= len(bit_duals):
            bit_duals.extend([0.0] * (int(bit) + 1 - len(bit_duals)))
        bit_duals[int(bit)] = float(duals.cover.get(int(task), 0.0))
    dual_sum_by_mask: dict[int, float] = {}
    cut_penalty_by_mask: dict[int, float] = {}

    def dual_sum_for_mask(mask: int) -> float:
        mask = int(mask)
        cached = dual_sum_by_mask.get(mask)
        if cached is not None:
            return float(cached)
        total = 0.0
        remaining = int(mask)
        while remaining:
            bit_value = remaining & -remaining
            bit_index = int(bit_value.bit_length() - 1)
            if bit_index < len(bit_duals):
                total += float(bit_duals[bit_index])
            remaining ^= bit_value
        dual_sum_by_mask[mask] = float(total)
        return float(total)

    def cut_penalty_for_mask(mask: int) -> float:
        mask = int(mask)
        cached = cut_penalty_by_mask.get(mask)
        if cached is not None:
            return float(cached)
        value = _profile_cut_penalty(
            mask,
            journey_cut_duals or {},
            journey_cuts,
            cut_masks,
            enabled=cut_penalty_enabled,
        )
        cut_penalty_by_mask[mask] = float(value)
        return float(value)

    for base_profile in catalog:
        mask = int(base_profile.mask)
        if not _sortie_profile_mask_allowed_by_branch(mask, branch_constraints, task_to_bit):
            continue
        dual_sum = dual_sum_for_mask(mask)
        contribution = float(base_profile.cost) - dual_sum
        best_profile_rc = contribution if best_profile_rc is None else min(best_profile_rc, contribution)
        profile_cut_penalty = cut_penalty_for_mask(mask)
        if contribution + profile_cut_penalty >= threshold:
            cut_penalty_pruned += int(profile_cut_penalty > 0.0)
            continue
        profiles.append(
            _SortieProfile(
                sequence=base_profile.sequence,
                arc_options=base_profile.arc_options,
                lower_start=base_profile.lower_start,
                upper_start=base_profile.upper_start,
                end_offset=base_profile.end_offset,
                cost=base_profile.cost,
                mask=base_profile.mask,
                contribution=contribution,
            )
        )
    return profiles, best_profile_rc, cut_penalty_pruned


def _generate_negative_sortie_profiles_by_label_physical_catalog(
    data: FutureData,
    duals: FutureDuals,
    *,
    base_reduced_cost: float,
    config: JourneyPricingConfig,
    deadline: float | None,
    task_order: tuple[int, ...],
    task_to_bit: dict[int, int],
    trip_cache: dict[tuple, Any],
    resource_cache: dict[tuple, Any] | None,
    catalog_stats: dict[str, int] | None,
    journey_cut_duals: dict[int, float],
    journey_cuts: tuple[FutureCut, ...],
    stream_callback: Any | None = None,
    stream_profile_batch_size: int = 0,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
) -> tuple[list[_SortieProfile], int, int, float | None, bool, str, int]:
    max_tasks = _max_tasks_per_trip(data, int(config.max_tasks_per_trip))
    shared_branchless_catalog = bool(config.profile_labeling_physical_catalog_share_across_branches_enabled)
    catalog_branch_constraints = tuple() if shared_branchless_catalog else branch_constraints
    catalog_key = _sortie_label_physical_catalog_key(data, config, task_order, max_tasks, catalog_branch_constraints)
    state = trip_cache.get(catalog_key)
    hit = isinstance(state, _SortieLabelResumeState)
    if not hit:
        state = _initial_sortie_label_resume_state(data, duals)
        trip_cache[catalog_key] = state
    assert isinstance(state, _SortieLabelResumeState)
    if hit:
        _reprioritize_sortie_label_state(
            state,
            duals,
            config=config,
            task_order=task_order,
            max_tasks=max_tasks,
            cut_duals=journey_cut_duals,
            cuts=journey_cuts,
            cut_masks=_cut_masks(data, journey_cuts),
        )
    before_generated = int(state.generated)
    before_evaluated = int(state.evaluated)
    local_stream_callback = stream_callback
    local_stream_profile_batch_size = stream_profile_batch_size
    exhaust_after_profile_count = max(0, int(config.streaming_callback_exhaust_after_profile_count))
    if (
        local_stream_callback is not None
        and exhaust_after_profile_count > 0
        and len(state.profiles_by_key) >= exhaust_after_profile_count
        and not bool(state.exhausted)
    ):
        # Worker-only cadence control: once the dual-independent physical
        # catalog is already large, avoid repeatedly solving profile DP at
        # intermediate checkpoints.  The caller still runs one final DP over
        # the returned catalog and this result remains uncertified unless a
        # later true-dual final judge proves no negative column.
        local_stream_callback = None
        local_stream_profile_batch_size = 0
        if catalog_stats is not None:
            catalog_stats["streaming_callback_exhaust_triggered"] = 1
            catalog_stats["streaming_callback_exhaust_threshold"] = int(exhaust_after_profile_count)
    resource_bound_cache = _get_task_set_resource_lower_bound_cache(
        data,
        task_to_bit,
        enabled=bool(config.task_set_resource_pruning_enabled),
        resource_cache=resource_cache,
    )
    if catalog_stats is not None:
        catalog_stats["hit"] = int(hit)
        catalog_stats["label_physical_catalog"] = 1
        catalog_stats["label_resume_heap"] = len(state.heap)
        catalog_stats["label_resume_profiles"] = len(state.profiles_by_key)
        catalog_stats["label_resume_exhausted"] = int(state.exhausted)
        if bool(config.profile_online_dominance_enabled) and bool(config.profile_cross_dominance_enabled):
            catalog_stats["online_dominance_applied"] = 1
            catalog_stats["online_dominance_pruned"] = int(getattr(state, "online_dominance_pruned", 0))
    if (
        bool(config.profile_labeling_existing_catalog_pre_scan_enabled)
        and hit
        and local_stream_callback is not None
        and state.profiles_by_key
    ):
        # Worker-only fast path: the physical catalog is dual-independent and
        # often already contains enough profiles for the current true dual.
        # Scan it before spending this round extending the catalog again.  A
        # no-column result from this scan is ignored; only an actual negative
        # worker batch may short-circuit catalog growth.
        catalog_profiles = _sortie_label_state_profiles(state, config)
        if catalog_stats is not None:
            catalog_stats["streaming_existing_catalog_scan"] = 1
            catalog_stats["size"] = len(state.profiles_by_key)
            catalog_stats["label_resume_heap"] = len(state.heap)
            catalog_stats["label_resume_profiles"] = len(catalog_profiles)
            catalog_stats["label_resume_exhausted"] = int(state.exhausted)
            if bool(config.profile_online_dominance_enabled) and bool(config.profile_cross_dominance_enabled):
                catalog_stats["online_dominance_applied"] = 1
                catalog_stats["online_dominance_pruned"] = int(getattr(state, "online_dominance_pruned", 0))
        result = local_stream_callback(
            catalog_profiles,
            int(state.generated),
            int(state.evaluated),
            state.best_profile_rc,
            0,
        )
        if result is not None and result.journeys:
            raise _StreamingPricingStop(result)
    try:
        _advance_sortie_label_resume_state(
            data,
            duals,
            state,
            config=config,
            deadline=deadline,
            task_order=task_order,
            threshold=float("inf"),
            task_to_bit=task_to_bit,
            max_tasks=max_tasks,
            resource_bound_cache=resource_bound_cache,
            catalog_stats=catalog_stats,
            stream_callback=local_stream_callback,
            stream_profile_batch_size=local_stream_profile_batch_size,
            branch_constraints=catalog_branch_constraints,
            cut_duals=journey_cut_duals,
            cuts=journey_cuts,
            cut_masks=_cut_masks(data, journey_cuts),
        )
    finally:
        catalog_profiles = _sortie_label_state_profiles(state, config)
        if catalog_stats is not None:
            catalog_stats["hit"] = int(hit)
            catalog_stats["size"] = len(state.profiles_by_key)
            catalog_stats["label_physical_catalog"] = 1
            catalog_stats["label_physical_catalog_exhausted"] = int(state.exhausted)
            catalog_stats["label_resume_heap"] = len(state.heap)
            catalog_stats["label_resume_profiles"] = len(catalog_profiles)
            catalog_stats["label_resume_exhausted"] = int(state.exhausted)
            if bool(config.profile_online_dominance_enabled) and bool(config.profile_cross_dominance_enabled):
                catalog_stats["online_dominance_applied"] = 1
                catalog_stats["online_dominance_pruned"] = int(getattr(state, "online_dominance_pruned", 0))
    profiles, best_profile_rc, cut_penalty_pruned = _filter_sortie_profile_catalog(
        catalog_profiles,
        duals,
        base_reduced_cost=base_reduced_cost,
        config=config,
        journey_cut_duals=journey_cut_duals,
        journey_cuts=journey_cuts,
        task_to_bit=task_to_bit,
        branch_constraints=branch_constraints,
    )
    return (
        profiles,
        int(state.generated) - before_generated,
        int(state.evaluated) - before_evaluated,
        best_profile_rc,
        bool(state.exhausted),
        str(state.reason),
        int(cut_penalty_pruned),
    )


def _sortie_label_physical_catalog_key(
    data: FutureData,
    config: JourneyPricingConfig,
    task_order: tuple[int, ...],
    max_tasks: int,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
) -> tuple:
    del task_order
    return (
        "journey_sortie_label_physical_catalog_v2",
        str(data.instance_path),
        tuple(int(task) for task in data.tasks),
        _branch_constraints_cache_key(branch_constraints),
        int(max_tasks),
        int(config.max_sequences),
        int(config.max_timed_evaluations),
        int(config.max_candidate_trips),
        bool(config.generalized_partial_dominance_enabled),
    )


def _arc_options_for_timed_trip(data: FutureData, trip: TimedTrip) -> tuple[ArcOption, ...] | None:
    sequence = tuple(int(task) for task in trip.tasks)
    option_ids = tuple(str(option_id) for option_id in trip.arc_option_ids)
    if len(option_ids) != len(sequence) + 1:
        return None
    arc_options: list[ArcOption] = []
    current = 0
    for destination, option_id in zip((*sequence, 0), option_ids):
        matches = [option for option in data.options(int(current), int(destination)) if option.option_id == option_id]
        if not matches:
            return None
        arc_options.append(matches[0])
        current = int(destination)
    return tuple(arc_options)


def _force_insert_sortie_profile_seed(
    state: _SortieLabelResumeState,
    key: tuple,
    profile: _SortieProfile,
    *,
    online_dominance: bool,
) -> bool:
    old_same_key = state.profiles_by_key.get(key)
    if old_same_key is not None and _sortie_profile_sort_key(old_same_key) <= _sortie_profile_sort_key(profile):
        return False
    if online_dominance:
        if state.profiles_by_mask is None:
            state.profiles_by_mask = {}
        group = state.profiles_by_mask.setdefault(int(profile.mask), [])
        group = [old for old in group if _sortie_profile_key(old) != key]
        group.append(profile)
        state.profiles_by_mask[int(profile.mask)] = group
    state.profiles_by_key[key] = profile
    return True


def seed_sortie_profile_catalog_from_journeys(
    data: FutureData,
    duals: FutureDuals,
    journeys: list[JourneyColumn] | tuple[JourneyColumn, ...],
    *,
    config: JourneyPricingConfig,
    trip_cache: dict[tuple, Any] | None,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
) -> SortieProfileCatalogSeedStats:
    """Seed the physical sortie-profile worker catalog with known feasible trips.

    This is a worker repair mechanism, not a certificate shortcut.  Every
    inserted profile comes from an already constructed feasible JourneyColumn
    and will still be re-filtered under the current duals when profile pricing
    runs.  A profile no-column result remains uncertified.
    """

    if trip_cache is None or not bool(config.profile_labeling_physical_catalog_resume_enabled):
        return SortieProfileCatalogSeedStats(
            enabled=False,
            skipped_no_cache=trip_cache is None,
            journeys_seen=len(journeys),
        )
    task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
    max_tasks = _max_tasks_per_trip(data, int(config.max_tasks_per_trip))
    task_order = tuple(
        sorted(
            (int(task) for task in data.tasks),
            key=lambda task: (-float(getattr(duals, "cover", {}).get(int(task), 0.0)), int(task)),
        )
    )
    shared_branchless_catalog = bool(config.profile_labeling_physical_catalog_share_across_branches_enabled)
    catalog_branch_constraints = tuple() if shared_branchless_catalog else branch_constraints
    catalog_key = _sortie_label_physical_catalog_key(data, config, task_order, max_tasks, catalog_branch_constraints)
    state = trip_cache.get(catalog_key)
    catalog_hit = isinstance(state, _SortieLabelResumeState)
    if not catalog_hit:
        state = _initial_sortie_label_resume_state(data, duals)
        trip_cache[catalog_key] = state
    assert isinstance(state, _SortieLabelResumeState)
    online_dominance = bool(config.profile_online_dominance_enabled) and bool(config.profile_cross_dominance_enabled)
    if online_dominance and getattr(state, "profiles_by_mask", None) is None:
        state.profiles_by_mask = {}
    before = len(state.profiles_by_key)
    trips_seen = 0
    seeded = 0
    forced_seeded = 0
    duplicate_or_dominated = 0
    skipped_missing_arc_option = 0
    skipped_invalid_trip = 0
    for journey in journeys:
        for trip in tuple(getattr(journey, "trips", tuple())):
            trips_seen += 1
            sequence = tuple(int(task) for task in getattr(trip, "tasks", tuple()))
            if not sequence or len(sequence) > max_tasks or any(task not in task_to_bit for task in sequence):
                skipped_invalid_trip += 1
                continue
            arc_options = _arc_options_for_timed_trip(data, trip)
            if arc_options is None:
                skipped_missing_arc_option += 1
                continue
            valid_trip = evaluate_timed_trip(
                data,
                sequence,
                float(trip.start_time),
                time_bucket_size=float(config.time_bucket_size),
                arc_options=arc_options,
                include_physical_paths=False,
            )
            if valid_trip is None:
                skipped_invalid_trip += 1
                continue
            mask = 0
            for task in set(sequence):
                mask |= 1 << task_to_bit[int(task)]
            if not _sortie_profile_mask_allowed_by_branch(mask, catalog_branch_constraints, task_to_bit):
                skipped_invalid_trip += 1
                continue
            dual_sum = sum(float(duals.cover.get(int(task), 0.0)) for task in set(sequence))
            profile = _SortieProfile(
                sequence=sequence,
                arc_options=arc_options,
                lower_start=float(valid_trip.start_time),
                upper_start=float(valid_trip.start_time),
                end_offset=max(0.0, float(valid_trip.end_time) - float(valid_trip.start_time)),
                cost=float(valid_trip.cost),
                mask=mask,
                contribution=float(valid_trip.cost) - dual_sum,
            )
            key = _sortie_profile_key(profile)
            if online_dominance and state.profiles_by_mask is not None:
                added, _cap_pruned = _add_sortie_profile_online_skyline(
                    state.profiles_by_key,
                    state.profiles_by_mask,
                    key,
                    profile,
                )
            else:
                old = state.profiles_by_key.get(key)
                added = old is None or profile.contribution < old.contribution - 1.0e-9
                if added:
                    state.profiles_by_key[key] = profile
            if added:
                seeded += 1
            else:
                forced = _force_insert_sortie_profile_seed(
                    state,
                    key,
                    profile,
                    online_dominance=online_dominance,
                )
                if forced:
                    seeded += 1
                    forced_seeded += 1
                else:
                    duplicate_or_dominated += 1
    after = len(state.profiles_by_key)
    return SortieProfileCatalogSeedStats(
        enabled=True,
        skipped_no_cache=False,
        catalog_hit=catalog_hit,
        journeys_seen=len(journeys),
        trips_seen=trips_seen,
        seeded_profiles=seeded,
        forced_seed_profiles=forced_seeded,
        duplicate_or_dominated_profiles=duplicate_or_dominated,
        skipped_missing_arc_option=skipped_missing_arc_option,
        skipped_invalid_trip=skipped_invalid_trip,
        catalog_size_before=before,
        catalog_size_after=after,
    )


def _zero_sortie_profile_duals(data: FutureData) -> FutureDuals:
    return FutureDuals(
        cover={int(task): 0.0 for task in data.tasks},
        task_vehicle={},
        sortie_count={int(data.vehicles[0]): 0.0},
        time_occupation={},
        ordering={},
        branches={},
        cuts={},
    )


def _generate_negative_sortie_profiles_by_labels(
    data: FutureData,
    duals: FutureDuals,
    *,
    base_reduced_cost: float,
    config: JourneyPricingConfig,
    deadline: float | None,
    task_order: tuple[int, ...],
    threshold: float,
    task_to_bit: dict[int, int],
    trip_cache: dict[tuple, Any] | None = None,
    resource_cache: dict[tuple, Any] | None = None,
    catalog_stats: dict[str, int] | None = None,
    stream_callback: Any | None = None,
    stream_profile_batch_size: int = 0,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
) -> tuple[list[_SortieProfile], int, int, float | None, bool, str]:
    if bool(config.profile_labeling_best_first_enabled):
        return _generate_negative_sortie_profiles_by_best_first_labels(
            data,
            duals,
            config=config,
            deadline=deadline,
            task_order=task_order,
            threshold=threshold,
            task_to_bit=task_to_bit,
            trip_cache=trip_cache,
            resource_cache=resource_cache,
            catalog_stats=catalog_stats,
            stream_callback=stream_callback,
            stream_profile_batch_size=stream_profile_batch_size,
            branch_constraints=branch_constraints,
        )
    max_tasks = _max_tasks_per_trip(data, int(config.max_tasks_per_trip))
    initial = _SortiePartialLabel(
        sequence=tuple(),
        mask=0,
        last=0,
        partial=_PartialNoWaitingPathProfile(
            arc_options=tuple(),
            lower_start=0.0,
            upper_start=float(data.horizon),
            offset=0.0,
            travel_cost=0.0,
            travel_energy=0.0,
            service_cost=0.0,
            service_energy=0.0,
        ),
    )
    labels_by_key: dict[tuple[int, int], list[_SortiePartialLabel]] = {(0, 0): [initial]}
    profiles_by_key: dict[tuple, _SortieProfile] = {}
    generated = 0
    evaluated = 0
    best_profile_rc: float | None = None
    exhausted = True
    reason = ""
    superset_bound_cache = (
        _TaskSetSupersetLowerBoundCache(
            _TaskSetReducedCostLowerBoundCache(data, duals, int(data.vehicles[0]), task_to_bit),
            task_count=len(data.tasks),
            max_tasks_per_sortie=max_tasks,
            enabled=True,
        )
        if bool(config.profile_labeling_task_set_superset_pruning_enabled) and threshold < float("inf")
        else None
    )
    resource_bound_cache = _get_task_set_resource_lower_bound_cache(
        data,
        task_to_bit,
        enabled=bool(config.task_set_resource_pruning_enabled),
        resource_cache=resource_cache,
    )
    partial_bound_cache = _PartialSortieProfileLowerBoundCache(
        data,
        duals,
        int(data.vehicles[0]),
        task_to_bit,
        enabled=bool(config.partial_profile_bound_pruning_enabled) and threshold < float("inf"),
    )
    for depth in range(max_tasks):
        if deadline is not None and time.perf_counter() > deadline:
            return list(profiles_by_key.values()), generated, evaluated, best_profile_rc, False, "time_limit"
        snapshot = [label for labels in labels_by_key.values() for label in labels if len(label.sequence) == depth]
        if not snapshot:
            break
        for label in snapshot:
            if deadline is not None and time.perf_counter() > deadline:
                return list(profiles_by_key.values()), generated, evaluated, best_profile_rc, False, "time_limit"
            for task in task_order:
                task = int(task)
                bit = 1 << task_to_bit[task]
                if label.mask & bit:
                    continue
                sequence = (*label.sequence, task)
                new_mask = label.mask | bit
                if not _sortie_profile_mask_allowed_by_branch(new_mask, branch_constraints, task_to_bit):
                    if catalog_stats is not None:
                        catalog_stats["branch_mask_pruned_sequences"] = int(
                            catalog_stats.get("branch_mask_pruned_sequences", 0)
                        ) + 1
                    continue
                if superset_bound_cache is not None:
                    superset_lb = superset_bound_cache.value(new_mask)
                    if superset_lb is not None and superset_lb >= threshold:
                        if catalog_stats is not None:
                            catalog_stats["task_set_bound_pruned_sequences"] = int(
                                catalog_stats.get("task_set_bound_pruned_sequences", 0)
                            ) + 1
                        continue
                if not resource_bound_cache.maybe_feasible(new_mask):
                    if catalog_stats is not None:
                        catalog_stats["task_set_resource_pruned_sequences"] = int(
                            catalog_stats.get("task_set_resource_pruned_sequences", 0)
                        ) + 1
                    continue
                if not _sequence_resource_precheck(data, sequence):
                    continue
                options = data.options(int(label.last), task)
                if not options:
                    continue
                for option in options:
                    if deadline is not None and time.perf_counter() > deadline:
                        return list(profiles_by_key.values()), generated, evaluated, best_profile_rc, False, "time_limit"
                    extended = _extend_no_waiting_partial(data, sequence, len(label.sequence), label.partial, option)
                    if extended is None:
                        continue
                    generated += 1
                    if int(config.max_sequences) > 0 and generated > int(config.max_sequences):
                        return list(profiles_by_key.values()), generated, evaluated, best_profile_rc, False, "label_budget"
                    new_label = _SortiePartialLabel(sequence=sequence, mask=new_mask, last=task, partial=extended)
                    if partial_bound_cache.value(new_label, max_tasks - len(new_label.sequence)) >= threshold:
                        if catalog_stats is not None:
                            catalog_stats["partial_profile_bound_pruned_labels"] = int(
                                catalog_stats.get("partial_profile_bound_pruned_labels", 0)
                            ) + 1
                        continue
                    _add_sortie_partial_label(
                        labels_by_key.setdefault((new_mask, task), []),
                        new_label,
                        generalized=bool(config.generalized_partial_dominance_enabled),
                    )
                    eval_inc, best_added_rc = _complete_sortie_label_profiles(
                        data,
                        duals,
                        new_label,
                        config,
                        profiles_by_key,
                        threshold,
                        task_to_bit,
                        deadline=deadline,
                    )
                    evaluated += eval_inc
                    if deadline is not None and time.perf_counter() > deadline:
                        return list(profiles_by_key.values()), generated, evaluated, best_profile_rc, False, "time_limit"
                    if best_added_rc is not None:
                        best_profile_rc = best_added_rc if best_profile_rc is None else min(best_profile_rc, best_added_rc)
                    if int(config.max_candidate_trips) > 0 and len(profiles_by_key) > int(config.max_candidate_trips):
                        return list(profiles_by_key.values()), generated, evaluated, best_profile_rc, False, "candidate_profile_budget"
                    if int(config.max_timed_evaluations) > 0 and evaluated > int(config.max_timed_evaluations):
                        return list(profiles_by_key.values()), generated, evaluated, best_profile_rc, False, "profile_evaluation_budget"
    return list(profiles_by_key.values()), generated, evaluated, best_profile_rc, exhausted, reason


def _generate_negative_sortie_profiles_by_best_first_labels(
    data: FutureData,
    duals: FutureDuals,
    *,
    config: JourneyPricingConfig,
    deadline: float | None,
    task_order: tuple[int, ...],
    threshold: float,
    task_to_bit: dict[int, int],
    trip_cache: dict[tuple, Any] | None = None,
    resource_cache: dict[tuple, Any] | None = None,
    catalog_stats: dict[str, int] | None = None,
    stream_callback: Any | None = None,
    stream_profile_batch_size: int = 0,
    resource_bound_cache: _TaskSetResourceLowerBoundCache | None = None,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
) -> tuple[list[_SortieProfile], int, int, float | None, bool, str]:
    max_tasks = _max_tasks_per_trip(data, int(config.max_tasks_per_trip))
    superset_bound_cache = (
        _TaskSetSupersetLowerBoundCache(
            _TaskSetReducedCostLowerBoundCache(data, duals, int(data.vehicles[0]), task_to_bit),
            task_count=len(data.tasks),
            max_tasks_per_sortie=max_tasks,
            enabled=True,
        )
        if bool(config.profile_labeling_task_set_superset_pruning_enabled) and threshold < float("inf")
        else None
    )
    if resource_bound_cache is None:
        resource_bound_cache = _get_task_set_resource_lower_bound_cache(
            data,
            task_to_bit,
            enabled=bool(config.task_set_resource_pruning_enabled),
            resource_cache=resource_cache,
        )
    partial_bound_cache = _PartialSortieProfileLowerBoundCache(
        data,
        duals,
        int(data.vehicles[0]),
        task_to_bit,
        enabled=bool(config.partial_profile_bound_pruning_enabled) and threshold < float("inf"),
    )
    resume_key = _sortie_label_resume_key(data, duals, config, task_order, threshold, max_tasks, branch_constraints)
    if resume_key is not None and trip_cache is not None:
        state = trip_cache.get(resume_key)
        hit = isinstance(state, _SortieLabelResumeState)
        if not hit:
            state = _initial_sortie_label_resume_state(data, duals)
            trip_cache[resume_key] = state
        assert isinstance(state, _SortieLabelResumeState)
        before_generated = int(state.generated)
        before_evaluated = int(state.evaluated)
        _advance_sortie_label_resume_state(
            data,
            duals,
            state,
            config=config,
            deadline=deadline,
            task_order=task_order,
            threshold=threshold,
            task_to_bit=task_to_bit,
            max_tasks=max_tasks,
            superset_bound_cache=superset_bound_cache,
            resource_bound_cache=resource_bound_cache,
            partial_bound_cache=partial_bound_cache,
            catalog_stats=catalog_stats,
            stream_callback=stream_callback,
            stream_profile_batch_size=stream_profile_batch_size,
            branch_constraints=branch_constraints,
        )
        if catalog_stats is not None:
            catalog_stats["hit"] = int(hit)
            catalog_stats["size"] = len(_sortie_label_state_profiles(state, config))
            catalog_stats["label_resume"] = 1
            catalog_stats["label_resume_hit"] = int(hit)
            catalog_stats["label_resume_heap"] = len(state.heap)
            catalog_stats["label_resume_profiles"] = len(_sortie_label_state_profiles(state, config))
            catalog_stats["label_resume_exhausted"] = int(state.exhausted)
            if bool(config.profile_online_dominance_enabled) and bool(config.profile_cross_dominance_enabled):
                catalog_stats["online_dominance_applied"] = 1
            catalog_stats["online_dominance_pruned"] = int(getattr(state, "online_dominance_pruned", 0))
        return (
            _sortie_label_state_profiles(state, config),
            int(state.generated) - before_generated,
            int(state.evaluated) - before_evaluated,
            state.best_profile_rc,
            bool(state.exhausted),
            str(state.reason),
        )
    state = _initial_sortie_label_resume_state(data, duals)
    _advance_sortie_label_resume_state(
        data,
        duals,
        state,
        config=config,
        deadline=deadline,
        task_order=task_order,
        threshold=threshold,
        task_to_bit=task_to_bit,
        max_tasks=max_tasks,
        superset_bound_cache=superset_bound_cache,
        resource_bound_cache=resource_bound_cache,
        partial_bound_cache=partial_bound_cache,
        catalog_stats=catalog_stats,
        stream_callback=stream_callback,
        stream_profile_batch_size=stream_profile_batch_size,
        branch_constraints=branch_constraints,
    )
    return (
        _sortie_label_state_profiles(state, config),
        int(state.generated),
        int(state.evaluated),
        state.best_profile_rc,
        bool(state.exhausted),
        str(state.reason),
    )


def _sortie_label_resume_key(
    data: FutureData,
    duals: FutureDuals,
    config: JourneyPricingConfig,
    task_order: tuple[int, ...],
    threshold: float,
    max_tasks: int,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
) -> tuple | None:
    if not bool(config.profile_labeling_resume_enabled):
        return None
    return (
        "journey_sortie_label_resume_v2",
        str(data.instance_path),
        tuple(int(task) for task in task_order),
        _branch_constraints_cache_key(branch_constraints),
        tuple((int(task), round(float(duals.cover.get(int(task), 0.0)), 9)) for task in data.tasks),
        round(float(threshold), 9),
        int(max_tasks),
        int(config.max_sequences),
        int(config.max_timed_evaluations),
        int(config.max_candidate_trips),
        bool(config.generalized_partial_dominance_enabled),
        bool(config.profile_online_dominance_enabled) and bool(config.profile_cross_dominance_enabled),
        bool(config.task_set_resource_pruning_enabled),
        bool(config.partial_profile_bound_pruning_enabled),
    )


def _initial_sortie_label_resume_state(data: FutureData, duals: FutureDuals) -> _SortieLabelResumeState:
    initial = _SortiePartialLabel(
        sequence=tuple(),
        mask=0,
        last=0,
        partial=_PartialNoWaitingPathProfile(
            arc_options=tuple(),
            lower_start=0.0,
            upper_start=float(data.horizon),
            offset=0.0,
            travel_cost=0.0,
            travel_energy=0.0,
            service_cost=0.0,
            service_energy=0.0,
        ),
    )
    labels_by_key: dict[tuple[int, int], list[_SortiePartialLabel]] = {(0, 0): [initial]}
    profiles_by_key: dict[tuple, _SortieProfile] = {}
    heap: list[tuple[float, int, float, tuple[int, ...], int, _SortiePartialLabel]] = []
    heapq.heappush(heap, (_sortie_partial_label_priority(initial, duals), 0, 0.0, tuple(), 0, initial))
    return _SortieLabelResumeState(
        labels_by_key=labels_by_key,
        profiles_by_key=profiles_by_key,
        profiles_by_mask={},
        heap=heap,
        active_label_ids={id(initial)},
    )


def _sortie_label_state_profiles(state: _SortieLabelResumeState, config: JourneyPricingConfig) -> list[_SortieProfile]:
    online = bool(config.profile_online_dominance_enabled) and bool(config.profile_cross_dominance_enabled)
    profiles_by_mask = getattr(state, "profiles_by_mask", None)
    if not online or profiles_by_mask is None:
        return list(state.profiles_by_key.values())
    return [profile for group in profiles_by_mask.values() for profile in group]


def _advance_sortie_label_resume_state(
    data: FutureData,
    duals: FutureDuals,
    state: _SortieLabelResumeState,
    *,
    config: JourneyPricingConfig,
    deadline: float | None,
    task_order: tuple[int, ...],
    threshold: float,
    task_to_bit: dict[int, int],
    max_tasks: int,
    superset_bound_cache: _TaskSetSupersetLowerBoundCache | None = None,
    resource_bound_cache: _TaskSetResourceLowerBoundCache | None = None,
    partial_bound_cache: _PartialSortieProfileLowerBoundCache | None = None,
    catalog_stats: dict[str, int] | None = None,
    stream_callback: Any | None = None,
    stream_profile_batch_size: int = 0,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
    cut_duals: dict[int, float] | None = None,
    cuts: tuple[FutureCut, ...] = tuple(),
    cut_masks: tuple[int, ...] = tuple(),
) -> None:
    if bool(state.exhausted):
        return
    state.reason = ""
    next_stream_profile_count = (
        len(state.profiles_by_key) + max(1, int(stream_profile_batch_size))
        if stream_callback is not None
        else 0
    )
    stream_callback_no_result_streak = 0
    online_dominance = bool(config.profile_online_dominance_enabled) and bool(config.profile_cross_dominance_enabled)
    if online_dominance and getattr(state, "profiles_by_mask", None) is None:
        state.profiles_by_mask = {}
    while state.heap:
        if deadline is not None and time.perf_counter() > deadline:
            state.reason = "time_limit"
            return
        _priority, _depth_key, _offset_key, _seq_key, _serial, label = heapq.heappop(state.heap)
        if id(label) not in state.active_label_ids:
            continue
        if len(label.sequence) >= max_tasks:
            continue
        for task in task_order:
            task = int(task)
            bit = 1 << task_to_bit[task]
            if label.mask & bit:
                continue
            sequence = (*label.sequence, task)
            new_mask = label.mask | bit
            if not _sortie_profile_mask_allowed_by_branch(new_mask, branch_constraints, task_to_bit):
                if catalog_stats is not None:
                    catalog_stats["branch_mask_pruned_sequences"] = int(
                        catalog_stats.get("branch_mask_pruned_sequences", 0)
                    ) + 1
                continue
            if superset_bound_cache is not None:
                superset_lb = superset_bound_cache.value(new_mask)
                if superset_lb is not None and superset_lb >= threshold:
                    if catalog_stats is not None:
                        catalog_stats["task_set_bound_pruned_sequences"] = int(
                            catalog_stats.get("task_set_bound_pruned_sequences", 0)
                        ) + 1
                    continue
            if resource_bound_cache is not None and not resource_bound_cache.maybe_feasible(new_mask):
                if catalog_stats is not None:
                    catalog_stats["task_set_resource_pruned_sequences"] = int(
                        catalog_stats.get("task_set_resource_pruned_sequences", 0)
                    ) + 1
                continue
            if not _sequence_resource_precheck(data, sequence):
                continue
            options = data.options(int(label.last), task)
            if not options:
                continue
            for option in options:
                if deadline is not None and time.perf_counter() > deadline:
                    _requeue_sortie_label_state(
                        state,
                        duals,
                        label,
                        config=config,
                        task_order=task_order,
                        max_tasks=max_tasks,
                        cut_duals=cut_duals or {},
                        cuts=cuts,
                        cut_masks=cut_masks,
                    )
                    state.reason = "time_limit"
                    return
                extended = _extend_no_waiting_partial(data, sequence, len(label.sequence), label.partial, option)
                if extended is None:
                    continue
                state.generated += 1
                if int(config.max_sequences) > 0 and int(state.generated) > int(config.max_sequences):
                    _requeue_sortie_label_state(
                        state,
                        duals,
                        label,
                        config=config,
                        task_order=task_order,
                        max_tasks=max_tasks,
                        cut_duals=cut_duals or {},
                        cuts=cuts,
                        cut_masks=cut_masks,
                    )
                    state.reason = "label_budget"
                    return
                new_label = _SortiePartialLabel(sequence=sequence, mask=new_mask, last=task, partial=extended)
                if partial_bound_cache is not None and partial_bound_cache.value(
                    new_label,
                    max_tasks - len(new_label.sequence),
                ) >= threshold:
                    if catalog_stats is not None:
                        catalog_stats["partial_profile_bound_pruned_labels"] = int(
                            catalog_stats.get("partial_profile_bound_pruned_labels", 0)
                        ) + 1
                    continue
                if not _add_sortie_partial_label(
                    state.labels_by_key.setdefault((new_mask, task), []),
                    new_label,
                    generalized=bool(config.generalized_partial_dominance_enabled),
                    active_label_ids=state.active_label_ids,
                ):
                    continue
                state.serial += 1
                heapq.heappush(
                    state.heap,
                    (
                        _sortie_partial_label_priority(
                            new_label,
                            duals,
                            config=config,
                            task_order=task_order,
                            max_tasks=max_tasks,
                            cut_duals=cut_duals or {},
                            cuts=cuts,
                            cut_masks=cut_masks,
                        ),
                        len(new_label.sequence),
                        round(float(new_label.partial.offset), 9),
                        tuple(int(item) for item in new_label.sequence),
                        int(state.serial),
                        new_label,
                    ),
                )
                cap_pruned_before = int((catalog_stats or {}).get("profile_mask_cap_pruned", 0))
                eval_inc, best_added_rc = _complete_sortie_label_profiles(
                    data,
                    duals,
                    new_label,
                    config,
                    state.profiles_by_key,
                    threshold,
                    task_to_bit,
                    deadline=deadline,
                    profiles_by_mask=state.profiles_by_mask if online_dominance else None,
                    catalog_stats=catalog_stats,
                    profile_cap_per_mask=(
                        int(config.streaming_profile_cap_per_mask)
                        if stream_callback is not None and int(config.streaming_profile_cap_per_mask) > 0
                        else 0
                    ),
                )
                cap_pruned_after = int((catalog_stats or {}).get("profile_mask_cap_pruned", 0))
                if cap_pruned_after > cap_pruned_before:
                    state.profile_mask_cap_pruned += cap_pruned_after - cap_pruned_before
                state.evaluated += eval_inc
                if deadline is not None and time.perf_counter() > deadline:
                    _requeue_sortie_label_state(
                        state,
                        duals,
                        label,
                        config=config,
                        task_order=task_order,
                        max_tasks=max_tasks,
                        cut_duals=cut_duals or {},
                        cuts=cuts,
                        cut_masks=cut_masks,
                    )
                    state.reason = "time_limit"
                    return
                if best_added_rc is not None:
                    state.best_profile_rc = (
                        best_added_rc if state.best_profile_rc is None else min(state.best_profile_rc, best_added_rc)
                    )
                current_profile_count = len(state.profiles_by_key)
                if stream_callback is not None and current_profile_count >= next_stream_profile_count:
                    stream_profiles = _sortie_label_state_profiles(state, config)
                    if catalog_stats is not None:
                        if online_dominance:
                            catalog_stats["online_dominance_applied"] = 1
                            catalog_stats["online_dominance_pruned"] = int(getattr(state, "online_dominance_pruned", 0))
                        catalog_stats["size"] = int(current_profile_count)
                        catalog_stats["label_resume_heap"] = len(state.heap)
                        catalog_stats["label_resume_profiles"] = len(stream_profiles)
                        catalog_stats["label_resume_exhausted"] = int(state.exhausted)
                    result = stream_callback(
                        stream_profiles,
                        int(state.generated),
                        int(state.evaluated),
                        state.best_profile_rc,
                        0,
                    )
                    if result is not None:
                        raise _StreamingPricingStop(result)
                    stream_callback_no_result_streak += 1
                    next_stream_profile_count = _streaming_next_profile_count(
                        int(current_profile_count),
                        int(stream_profile_batch_size),
                        int(stream_callback_no_result_streak),
                        config,
                    )
                if int(config.max_candidate_trips) > 0 and current_profile_count > int(config.max_candidate_trips):
                    _requeue_sortie_label_state(
                        state,
                        duals,
                        label,
                        config=config,
                        task_order=task_order,
                        max_tasks=max_tasks,
                        cut_duals=cut_duals or {},
                        cuts=cuts,
                        cut_masks=cut_masks,
                    )
                    state.reason = "candidate_profile_budget"
                    return
                if int(config.profile_catalog_max_profiles) > 0 and current_profile_count > int(config.profile_catalog_max_profiles):
                    _requeue_sortie_label_state(
                        state,
                        duals,
                        label,
                        config=config,
                        task_order=task_order,
                        max_tasks=max_tasks,
                        cut_duals=cut_duals or {},
                        cuts=cuts,
                        cut_masks=cut_masks,
                    )
                    state.reason = "profile_catalog_budget"
                    return
                if int(config.max_timed_evaluations) > 0 and int(state.evaluated) > int(config.max_timed_evaluations):
                    _requeue_sortie_label_state(
                        state,
                        duals,
                        label,
                        config=config,
                        task_order=task_order,
                        max_tasks=max_tasks,
                        cut_duals=cut_duals or {},
                        cuts=cuts,
                        cut_masks=cut_masks,
                    )
                    state.reason = "profile_evaluation_budget"
                    return
    if int(state.profile_mask_cap_pruned) > 0:
        state.exhausted = False
        state.reason = "profile_mask_cap_incomplete"
    else:
        state.exhausted = True
        state.reason = ""


def _requeue_sortie_label_state(
    state: _SortieLabelResumeState,
    duals: FutureDuals,
    label: _SortiePartialLabel,
    *,
    config: JourneyPricingConfig | None = None,
    task_order: tuple[int, ...] = tuple(),
    max_tasks: int = 0,
    cut_duals: dict[int, float] | None = None,
    cuts: tuple[FutureCut, ...] = tuple(),
    cut_masks: tuple[int, ...] = tuple(),
) -> None:
    state.serial += 1
    heapq.heappush(
        state.heap,
        (
            _sortie_partial_label_priority(
                label,
                duals,
                config=config,
                task_order=task_order,
                max_tasks=max_tasks,
                cut_duals=cut_duals or {},
                cuts=cuts,
                cut_masks=cut_masks,
            ),
            len(label.sequence),
            round(float(label.partial.offset), 9),
            tuple(int(item) for item in label.sequence),
            int(state.serial),
            label,
        ),
    )


def _reprioritize_sortie_label_state(
    state: _SortieLabelResumeState,
    duals: FutureDuals,
    *,
    config: JourneyPricingConfig | None = None,
    task_order: tuple[int, ...] = tuple(),
    max_tasks: int = 0,
    cut_duals: dict[int, float] | None = None,
    cuts: tuple[FutureCut, ...] = tuple(),
    cut_masks: tuple[int, ...] = tuple(),
) -> None:
    if not state.heap:
        return
    rebuilt: list[tuple[float, int, float, tuple[int, ...], int, _SortiePartialLabel]] = []
    for _priority, _depth, _offset, _seq_key, _serial, label in state.heap:
        if id(label) not in state.active_label_ids:
            continue
        state.serial += 1
        rebuilt.append(
            (
                _sortie_partial_label_priority(
                    label,
                    duals,
                    config=config,
                    task_order=task_order,
                    max_tasks=max_tasks,
                    cut_duals=cut_duals or {},
                    cuts=cuts,
                    cut_masks=cut_masks,
                ),
                len(label.sequence),
                round(float(label.partial.offset), 9),
                tuple(int(item) for item in label.sequence),
                int(state.serial),
                label,
            )
        )
    heapq.heapify(rebuilt)
    state.heap = rebuilt


def _sortie_partial_label_priority(
    label: _SortiePartialLabel,
    duals: FutureDuals,
    *,
    config: JourneyPricingConfig | None = None,
    task_order: tuple[int, ...] = tuple(),
    max_tasks: int = 0,
    cut_duals: dict[int, float] | None = None,
    cuts: tuple[FutureCut, ...] = tuple(),
    cut_masks: tuple[int, ...] = tuple(),
) -> float:
    dual_sum = sum(float(duals.cover.get(int(task), 0.0)) for task in set(label.sequence))
    partial_cost = float(label.partial.travel_cost) + float(label.partial.service_cost)
    priority = partial_cost - dual_sum
    future_weight = 0.0 if config is None else max(0.0, float(config.profile_labeling_priority_future_dual_weight))
    remaining_slots = max(0, int(max_tasks) - len(label.sequence))
    if future_weight > 0.0 and remaining_slots > 0 and task_order:
        visited = set(int(task) for task in label.sequence)
        future_rewards = sorted(
            (
                float(duals.cover.get(int(task), 0.0))
                for task in task_order
                if int(task) not in visited and float(duals.cover.get(int(task), 0.0)) > 0.0
            ),
            reverse=True,
        )
        priority -= future_weight * sum(future_rewards[:remaining_slots])
    cut_weight = 0.0 if config is None else max(0.0, float(config.profile_labeling_priority_cut_dual_weight))
    if cut_weight > 0.0 and cut_duals and cuts and cut_masks:
        priority += cut_weight * _journey_cut_dual_value(int(label.mask), cut_duals, cuts, cut_masks)
    return round(priority, 9)


def _filter_dominated_sortie_profiles(profiles: list[_SortieProfile]) -> tuple[list[_SortieProfile], int]:
    profiles, duplicate_pruned = _deduplicate_sortie_profiles_for_dominance(profiles)
    by_mask: dict[int, list[_SortieProfile]] = {}
    for profile in profiles:
        by_mask.setdefault(int(profile.mask), []).append(profile)
    kept: list[_SortieProfile] = []
    pruned = int(duplicate_pruned)
    for group in by_mask.values():
        skyline: list[_SortieProfile] = []
        for profile in sorted(group, key=_sortie_profile_sort_key):
            if any(_dominates_sortie_profile(old, profile) for old in skyline):
                pruned += 1
                continue
            survivors: list[_SortieProfile] = []
            for old in skyline:
                if _dominates_sortie_profile(profile, old):
                    pruned += 1
                    continue
                survivors.append(old)
            survivors.append(profile)
            skyline = survivors
        kept.extend(skyline)
    kept.sort(key=_sortie_profile_sort_key)
    return kept, pruned


def _filter_sortie_profiles_after_generation(
    profiles: list[_SortieProfile],
    config: JourneyPricingConfig,
    catalog_stats: dict[str, int],
) -> tuple[list[_SortieProfile], int]:
    if not bool(config.profile_cross_dominance_enabled):
        return profiles, 0
    if bool(config.profile_online_dominance_enabled) and bool(catalog_stats.get("online_dominance_applied", 0)):
        return profiles, int(catalog_stats.get("online_dominance_pruned", 0))
    return _filter_dominated_sortie_profiles(profiles)


def _add_sortie_profile_skyline(store: dict[int, list[_SortieProfile]], profile: _SortieProfile) -> tuple[bool, int]:
    group = store.setdefault(int(profile.mask), [])
    for old in group:
        if _dominates_sortie_profile(old, profile):
            return False, 0
    survivors: list[_SortieProfile] = []
    removed = 0
    for old in group:
        if _dominates_sortie_profile(profile, old):
            removed += 1
            continue
        survivors.append(old)
    survivors.append(profile)
    store[int(profile.mask)] = survivors
    return True, removed


def _deduplicate_sortie_profiles_for_dominance(profiles: list[_SortieProfile]) -> tuple[list[_SortieProfile], int]:
    best_by_resource: dict[tuple, _SortieProfile] = {}
    for profile in profiles:
        key = _sortie_profile_resource_key(profile)
        old = best_by_resource.get(key)
        if old is None or _sortie_profile_sort_key(profile) < _sortie_profile_sort_key(old):
            best_by_resource[key] = profile
    return list(best_by_resource.values()), max(0, len(profiles) - len(best_by_resource))


def _sortie_profile_resource_key(profile: _SortieProfile) -> tuple:
    return (
        profile.mask,
        round(profile.lower_start, 6),
        round(profile.upper_start, 6),
        round(profile.end_offset, 6),
    )


def _sortie_profile_sort_key(profile: _SortieProfile) -> tuple:
    return (
        profile.mask,
        round(profile.contribution, 9),
        round(profile.lower_start, 9),
        round(profile.end_offset, 9),
        round(-profile.upper_start, 9),
        profile.sequence,
        tuple(option.option_id for option in profile.arc_options),
    )


def _dominates_sortie_profile(left: _SortieProfile, right: _SortieProfile) -> bool:
    if left.mask != right.mask:
        return False
    left_contribution = left.contribution
    left_lower_start = left.lower_start
    left_upper_start = left.upper_start
    left_end_offset = left.end_offset
    right_contribution = right.contribution
    right_lower_start = right.lower_start
    right_upper_start = right.upper_start
    right_end_offset = right.end_offset
    no_worse = (
        left_contribution <= right_contribution + 1.0e-9
        and left_lower_start <= right_lower_start + 1.0e-9
        and left_upper_start >= right_upper_start - 1.0e-9
        and left_end_offset <= right_end_offset + 1.0e-9
    )
    strict = (
        left_contribution < right_contribution - 1.0e-9
        or left_lower_start < right_lower_start - 1.0e-9
        or left_upper_start > right_upper_start + 1.0e-9
        or left_end_offset < right_end_offset - 1.0e-9
    )
    return bool(no_worse and strict)


def _complete_sortie_label_profiles(
    data: FutureData,
    duals: FutureDuals,
    label: _SortiePartialLabel,
    config: JourneyPricingConfig,
    profiles_by_key: dict[tuple, _SortieProfile],
    threshold: float,
    task_to_bit: dict[int, int],
    deadline: float | None = None,
    profiles_by_mask: dict[int, list[_SortieProfile]] | None = None,
    catalog_stats: dict[str, int] | None = None,
    profile_cap_per_mask: int = 0,
) -> tuple[int, float | None]:
    evaluated = 0
    best_added_rc: float | None = None
    options = data.options(int(label.last), 0)
    if not options:
        return 0, None
    dual_sum = sum(float(duals.cover.get(int(task), 0.0)) for task in set(label.sequence))
    completion_cost_lb = float(label.partial.travel_cost) + float(label.partial.service_cost) + min(
        float(option.cost) for option in options
    )
    if completion_cost_lb - dual_sum >= float(threshold):
        return 0, None
    for option in options:
        if deadline is not None and time.perf_counter() > deadline:
            if catalog_stats is not None:
                catalog_stats["profile_completion_time_pruned"] = int(
                    catalog_stats.get("profile_completion_time_pruned", 0)
                ) + 1
            return evaluated, best_added_rc
        base = _complete_no_waiting_partial(data, label.partial, option)
        if base is None:
            continue
        evaluated += 1
        profile = base.profile
        contribution = float(profile.cost) - dual_sum
        if contribution >= threshold:
            continue
        mask = 0
        for task in set(label.sequence):
            mask |= 1 << task_to_bit[int(task)]
        key = (
            tuple(int(task) for task in label.sequence),
            tuple(option.option_id for option in base.arc_options),
            round(float(profile.lower_start), 6),
            round(float(profile.upper_start), 6),
            round(float(profile.end_offset), 6),
        )
        candidate = _SortieProfile(
            sequence=tuple(int(task) for task in label.sequence),
            arc_options=base.arc_options,
            lower_start=float(profile.lower_start),
            upper_start=float(profile.upper_start),
            end_offset=float(profile.end_offset),
            cost=float(profile.cost),
            mask=mask,
            contribution=contribution,
        )
        if profiles_by_mask is not None:
            added, cap_pruned = _add_sortie_profile_online_skyline(
                profiles_by_key,
                profiles_by_mask,
                key,
                candidate,
                profile_cap_per_mask=profile_cap_per_mask,
            )
            if cap_pruned:
                if catalog_stats is not None:
                    catalog_stats["profile_mask_cap_pruned"] = int(
                        catalog_stats.get("profile_mask_cap_pruned", 0)
                    ) + 1
            if added:
                best_added_rc = candidate.contribution if best_added_rc is None else min(best_added_rc, candidate.contribution)
            continue
        old = profiles_by_key.get(key)
        if old is None or candidate.contribution < old.contribution - 1.0e-9:
            profiles_by_key[key] = candidate
            best_added_rc = candidate.contribution if best_added_rc is None else min(best_added_rc, candidate.contribution)
    return evaluated, best_added_rc


def _sortie_profile_key(profile: _SortieProfile) -> tuple:
    return (
        tuple(int(task) for task in profile.sequence),
        tuple(option.option_id for option in profile.arc_options),
        round(float(profile.lower_start), 6),
        round(float(profile.upper_start), 6),
        round(float(profile.end_offset), 6),
    )


def _add_sortie_profile_online_skyline(
    profiles_by_key: dict[tuple, _SortieProfile],
    profiles_by_mask: dict[int, list[_SortieProfile]],
    key: tuple,
    candidate: _SortieProfile,
    *,
    profile_cap_per_mask: int = 0,
) -> tuple[bool, bool]:
    group = profiles_by_mask.setdefault(int(candidate.mask), [])
    candidate_resource_key = _sortie_profile_resource_key(candidate)
    old_same_key = profiles_by_key.get(key)
    if old_same_key is not None:
        if _sortie_profile_sort_key(old_same_key) <= _sortie_profile_sort_key(candidate):
            return False, False
        profiles_by_key.pop(key, None)
    for old in group:
        if _sortie_profile_resource_key(old) == candidate_resource_key:
            if _sortie_profile_sort_key(old) <= _sortie_profile_sort_key(candidate):
                return False, False
            continue
        if _dominates_sortie_profile(old, candidate):
            return False, False
    survivors: list[_SortieProfile] = []
    for old in group:
        same_resource = _sortie_profile_resource_key(old) == candidate_resource_key
        if same_resource or _dominates_sortie_profile(candidate, old):
            profiles_by_key.pop(_sortie_profile_key(old), None)
            continue
        survivors.append(old)
    cap = int(profile_cap_per_mask)
    if cap > 0 and len(survivors) >= cap:
        if old_same_key is not None:
            profiles_by_key[key] = old_same_key
        return False, True
    survivors.append(candidate)
    profiles_by_mask[int(candidate.mask)] = survivors
    profiles_by_key[key] = candidate
    return True, False


def _add_sortie_partial_label(
    labels: list[_SortiePartialLabel],
    candidate: _SortiePartialLabel,
    *,
    generalized: bool = False,
    candidate_not_dominated: bool = False,
    active_label_ids: set[int] | None = None,
    max_labels_per_node: int = 0,
    rank_key: Callable[[_SortiePartialLabel], float] | None = None,
    time_bucket_size: float = 0.0,
    energy_bucket_size: float = 0.0,
    dominance_index: _SortiePartialDominanceIndex | None = None,
) -> bool:
    if not bool(candidate_not_dominated):
        if _sortie_partial_label_dominated_by_existing(
            labels,
            candidate,
            generalized=generalized,
            time_bucket_size=float(time_bucket_size),
            energy_bucket_size=float(energy_bucket_size),
            dominance_index=dominance_index,
        ):
            return False
    candidate_scan = (
        dominance_index.labels_that_may_be_dominated_by(candidate)
        if dominance_index is not None
        and not bool(generalized)
        and float(time_bucket_size) <= 0.0
        and float(energy_bucket_size) <= 0.0
        else labels
    )
    dominated_ids: set[int] = set()
    for old in candidate_scan:
        if _dominates_sortie_partial_label(
            candidate,
            old,
            generalized=generalized,
            time_bucket_size=float(time_bucket_size),
            energy_bucket_size=float(energy_bucket_size),
        ):
            dominated_ids.add(id(old))
    if dominated_ids:
        if active_label_ids is not None:
            active_label_ids.difference_update(dominated_ids)
        labels[:] = [old for old in labels if id(old) not in dominated_ids]
        if dominance_index is not None:
            dominance_index.rebuild()
    labels.append(candidate)
    if active_label_ids is not None:
        active_label_ids.add(id(candidate))
    if dominance_index is not None:
        dominance_index.add(candidate)
    max_labels = max(0, int(max_labels_per_node))
    if max_labels > 0 and len(labels) > max_labels:
        if rank_key is None:
            def _default_rank(label: _SortiePartialLabel) -> float:
                partial = label.partial
                return (
                    float(partial.travel_cost)
                    + float(partial.service_cost)
                    + 1.0e-6 * float(partial.offset)
                )

            rank_key = _default_rank
        labels.sort(
            key=lambda item: (
                round(float(rank_key(item)), 9),
                round(float(item.partial.offset), 9),
                tuple(int(task) for task in item.sequence),
            )
        )
        survivors = labels[:max_labels]
        removed = labels[max_labels:]
        if active_label_ids is not None:
            for old in removed:
                active_label_ids.discard(id(old))
        kept = any(item is candidate for item in survivors)
        labels[:] = survivors
        if dominance_index is not None:
            dominance_index.rebuild()
        if not kept:
            if active_label_ids is not None:
                active_label_ids.discard(id(candidate))
            return False
    return True


def _sortie_partial_label_dominated_by_existing(
    labels: list[_SortiePartialLabel],
    candidate: _SortiePartialLabel,
    *,
    generalized: bool = False,
    time_bucket_size: float = 0.0,
    energy_bucket_size: float = 0.0,
    dominance_index: _SortiePartialDominanceIndex | None = None,
) -> bool:
    scan = (
        dominance_index.labels_that_may_dominate(candidate)
        if dominance_index is not None
        and not bool(generalized)
        and float(time_bucket_size) <= 0.0
        and float(energy_bucket_size) <= 0.0
        else labels
    )
    for old in scan:
        if _dominates_sortie_partial_label(
            old,
            candidate,
            generalized=generalized,
            time_bucket_size=float(time_bucket_size),
            energy_bucket_size=float(energy_bucket_size),
        ):
            return True
    return False


def _dominates_sortie_partial_label(
    left: _SortiePartialLabel,
    right: _SortiePartialLabel,
    *,
    generalized: bool = False,
    time_bucket_size: float = 0.0,
    energy_bucket_size: float = 0.0,
) -> bool:
    a = left.partial
    b = right.partial
    if not bool(generalized) and float(time_bucket_size) <= 0.0 and float(energy_bucket_size) <= 0.0:
        eps = 1.0e-9
        if a.lower_start > b.lower_start + eps:
            return False
        if a.upper_start < b.upper_start - eps:
            return False
        if a.offset > b.offset + eps:
            return False
        if a.travel_cost > b.travel_cost + eps:
            return False
        if a.travel_energy > b.travel_energy + eps:
            return False
        if a.service_cost > b.service_cost + eps:
            return False
        if a.service_energy > b.service_energy + eps:
            return False
        return bool(
            a.lower_start < b.lower_start - eps
            or a.upper_start > b.upper_start + eps
            or a.offset < b.offset - eps
            or a.travel_cost < b.travel_cost - eps
            or a.travel_energy < b.travel_energy - eps
            or a.service_cost < b.service_cost - eps
            or a.service_energy < b.service_energy - eps
        )
    a_lower_start = a.lower_start
    a_upper_start = a.upper_start
    a_offset = a.offset
    a_travel_cost = a.travel_cost
    a_travel_energy_raw = a.travel_energy
    a_service_cost = a.service_cost
    a_service_energy_raw = a.service_energy
    b_lower_start = b.lower_start
    b_upper_start = b.upper_start
    b_offset = b.offset
    b_travel_cost = b.travel_cost
    b_travel_energy_raw = b.travel_energy
    b_service_cost = b.service_cost
    b_service_energy_raw = b.service_energy
    if bool(generalized):
        a_current_low = a_lower_start + a_offset
        a_current_high = a_upper_start + a_offset
        b_current_low = b_lower_start + b_offset
        b_current_high = b_upper_start + b_offset
        interval_no_worse = (
            a_current_low <= b_current_low + 1.0e-9
            and a_current_high >= b_current_high - 1.0e-9
            and a_offset <= b_offset + 1.0e-9
        )
        interval_strict = (
            a_current_low < b_current_low - 1.0e-9
            or a_current_high > b_current_high + 1.0e-9
            or a_offset < b_offset - 1.0e-9
        )
    else:
        interval_no_worse = (
            a_lower_start <= b_lower_start + 1.0e-9
            and a_upper_start >= b_upper_start - 1.0e-9
            and a_offset <= b_offset + 1.0e-9
        )
        interval_strict = (
            a_lower_start < b_lower_start - 1.0e-9
            or a_upper_start > b_upper_start + 1.0e-9
            or a_offset < b_offset - 1.0e-9
        )
    if float(time_bucket_size) > 0.0:
        if bool(generalized):
            a_current_low = _resource_bucket_floor(a_current_low, float(time_bucket_size))
            b_current_low = _resource_bucket_floor(b_current_low, float(time_bucket_size))
            a_current_high = _resource_bucket_ceil(a_current_high, float(time_bucket_size))
            b_current_high = _resource_bucket_ceil(b_current_high, float(time_bucket_size))
        else:
            a_lower = _resource_bucket_floor(a_lower_start, float(time_bucket_size))
            b_lower = _resource_bucket_floor(b_lower_start, float(time_bucket_size))
            a_upper = _resource_bucket_ceil(a_upper_start, float(time_bucket_size))
            b_upper = _resource_bucket_ceil(b_upper_start, float(time_bucket_size))
            a_offset_bucket = _resource_bucket_floor(a_offset, float(time_bucket_size))
            b_offset_bucket = _resource_bucket_floor(b_offset, float(time_bucket_size))
            interval_no_worse = (
                a_lower <= b_lower + 1.0e-9
                and a_upper >= b_upper - 1.0e-9
                and a_offset_bucket <= b_offset_bucket + 1.0e-9
            )
            interval_strict = (
                a_lower < b_lower - 1.0e-9
                or a_upper > b_upper + 1.0e-9
                or a_offset_bucket < b_offset_bucket - 1.0e-9
            )
        if bool(generalized):
            a_offset_bucket = _resource_bucket_floor(a_offset, float(time_bucket_size))
            b_offset_bucket = _resource_bucket_floor(b_offset, float(time_bucket_size))
            interval_no_worse = (
                a_current_low <= b_current_low + 1.0e-9
                and a_current_high >= b_current_high - 1.0e-9
                and a_offset_bucket <= b_offset_bucket + 1.0e-9
            )
            interval_strict = (
                a_current_low < b_current_low - 1.0e-9
                or a_current_high > b_current_high + 1.0e-9
                or a_offset_bucket < b_offset_bucket - 1.0e-9
            )
    if float(energy_bucket_size) > 0.0:
        a_travel_energy = _resource_bucket_floor(a_travel_energy_raw, float(energy_bucket_size))
        b_travel_energy = _resource_bucket_floor(b_travel_energy_raw, float(energy_bucket_size))
        a_service_energy = _resource_bucket_floor(a_service_energy_raw, float(energy_bucket_size))
        b_service_energy = _resource_bucket_floor(b_service_energy_raw, float(energy_bucket_size))
    else:
        a_travel_energy = a_travel_energy_raw
        b_travel_energy = b_travel_energy_raw
        a_service_energy = a_service_energy_raw
        b_service_energy = b_service_energy_raw
    no_worse = (
        interval_no_worse
        and a_travel_cost <= b_travel_cost + 1.0e-9
        and float(a_travel_energy) <= float(b_travel_energy) + 1.0e-9
        and a_service_cost <= b_service_cost + 1.0e-9
        and float(a_service_energy) <= float(b_service_energy) + 1.0e-9
    )
    strict = (
        interval_strict
        or a_travel_cost < b_travel_cost - 1.0e-9
        or float(a_travel_energy) < float(b_travel_energy) - 1.0e-9
        or a_service_cost < b_service_cost - 1.0e-9
        or float(a_service_energy) < float(b_service_energy) - 1.0e-9
    )
    return bool(no_worse and strict)


def _solve_best_journey_profile_dp(
    data: FutureData,
    profiles: list[_SortieProfile],
    *,
    base_reduced_cost: float,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
    max_states: int,
    deadline: float | None = None,
    max_returned: int = 1,
    early_return_negative: bool = False,
    early_return_min_count: int = 1,
    optimistic_bound_pruning: bool = True,
    cross_count_dominance: bool = True,
    selection_mode: str = "reduced_cost",
    dp_stats: dict[str, int] | None = None,
    forbidden_journey_signatures: set[tuple] | frozenset[tuple] | None = None,
    duplicate_scan_limit: int = 10000,
    dominant_task_set_cost_by_mask: dict[int, float] | None = None,
    pricing_config: JourneyPricingConfig | None = None,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
    eps: float = 1.0e-6,
) -> tuple[list[tuple[tuple[tuple[int, float], ...], float]], float | None, str]:
    cut_value_cache: dict[int, float] = {}
    early_candidates: list[tuple[float, tuple[tuple[int, float], ...], int]] = []
    task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
    ordered = sorted(
        enumerate(profiles),
        key=lambda item: (item[1].upper_start + item[1].end_offset, item[1].lower_start, item[1].contribution, item[1].sequence),
    )
    ordered_records = tuple((position, profile_index, profile) for position, (profile_index, profile) in enumerate(ordered))
    compatible_profile_cache = _CompatibleProfileCache(ordered_records, task_count=len(data.tasks))
    optimistic_cache = _OptimisticProfileBoundCache(compatible_profile_cache)
    disjoint_cache = _DisjointProfileBoundCache(
        ordered_records,
        task_count=len(data.tasks),
        enabled=bool(optimistic_bound_pruning)
        and pricing_config is not None
        and bool(getattr(pricing_config, "dp_disjoint_bound_pruning_enabled", True))
        and len(data.tasks) <= int(getattr(pricing_config, "dp_disjoint_bound_max_tasks", 12)),
    )
    bound_pruning_safe = bool(optimistic_bound_pruning) and _profile_bound_pruning_cut_safe(cut_duals, cuts)
    max_future_tasks_per_profile = (
        _max_tasks_per_trip(data, int(pricing_config.max_tasks_per_trip))
        if pricing_config is not None
        else max(1, len(data.tasks))
    )
    positive_cut_reward_bound = (
        _PositiveSubsetCutRewardBound(
            task_count=len(data.tasks),
            cut_duals=cut_duals,
            cuts=cuts,
            cut_masks=cut_masks,
        )
        if bound_pruning_safe and cut_duals
        else None
    )
    labels_by_count: list[dict[int, list[_JourneyLabel]]] = [dict() for _ in range(int(data.sortie_limit) + 1)]
    labels_by_count[0][0] = [_JourneyLabel(0.0, 0.0, tuple())]
    cross_count_materialization_by_mask: dict[int, tuple[float, tuple[tuple[int, float], ...], int]] = {}
    state_count = 1
    processed_labels = 0
    profile_record_scans = 0
    profile_time_filtered = 0
    extension_attempts = 0
    max_labels_per_mask = (
        max(0, int(getattr(pricing_config, "profile_dp_max_labels_per_mask", 0)))
        if pricing_config is not None
        else 0
    )
    cross_count_materialization_slack = (
        max(0.0, float(getattr(pricing_config, "profile_cross_count_true_rc_materialization_slack", 0.0)))
        if pricing_config is not None
        else 0.0
    )
    cross_count_materialization_cap = (
        max(0, int(getattr(pricing_config, "profile_cross_count_true_rc_materialization_max_candidates", 0)))
        if pricing_config is not None
        else 0
    )
    cross_count_materialization_enabled = bool(
        cross_count_materialization_slack > 0.0 and cross_count_materialization_cap > 0
    )
    def trim_cross_count_materialization_candidates(force: bool = False) -> None:
        if not cross_count_materialization_enabled:
            return
        cap = max(1, int(cross_count_materialization_cap))
        if not force and len(cross_count_materialization_by_mask) <= cap * 4:
            return
        ordered_candidates = sorted(
            cross_count_materialization_by_mask.values(),
            key=lambda item: (round(float(item[0]), 9), len(item[1]), int(item[2]), item[1]),
        )[:cap]
        cross_count_materialization_by_mask.clear()
        for candidate in ordered_candidates:
            cross_count_materialization_by_mask[int(candidate[2])] = candidate

    def record_cross_count_materialization_candidate(
        new_mask: int,
        new_value: float,
        selected_profiles: tuple[tuple[int, float], ...],
    ) -> None:
        if not cross_count_materialization_enabled:
            return
        mask_key = int(new_mask)
        if not _journey_mask_branch_allowed(mask_key, branch_constraints, task_to_bit, final=True):
            return
        objective = (
            float(base_reduced_cost)
            + float(new_value)
            - _journey_cut_dual_value_cached(mask_key, cut_duals, cuts, cut_masks, cut_value_cache)
        )
        if objective >= float(cross_count_materialization_slack):
            return
        # 如果这个 task-set 已经在 RMP 中存在，只有物理成本更低的代表才值得
        # 复算 true RC。这样避免把 cross-count 备选池变成同 mask 重复列工厂。
        if dominant_task_set_cost_by_mask and mask_key in dominant_task_set_cost_by_mask:
            if not _profile_candidate_task_set_cost_improves(
                data,
                profiles,
                selected_profiles,
                mask_key,
                dominant_task_set_cost_by_mask,
                eps=float(eps),
            ):
                return
        old_candidate = cross_count_materialization_by_mask.get(mask_key)
        old_key = (
            math.inf if old_candidate is None else round(float(old_candidate[0]), 9),
            math.inf if old_candidate is None else len(old_candidate[1]),
            math.inf if old_candidate is None else int(old_candidate[2]),
            tuple() if old_candidate is None else old_candidate[1],
        )
        new_key = (round(float(objective), 9), len(selected_profiles), mask_key, selected_profiles)
        if old_candidate is None or new_key < old_key:
            cross_count_materialization_by_mask[mask_key] = (objective, selected_profiles, mask_key)
            trim_cross_count_materialization_candidates(force=False)

    def record_dp_stats() -> None:
        if dp_stats is None:
            return
        dp_stats["processed_labels"] = int(processed_labels)
        dp_stats["state_count"] = int(state_count)
        dp_stats["profile_record_scans"] = int(profile_record_scans)
        dp_stats["profile_time_filtered"] = int(profile_time_filtered)
        dp_stats["extension_attempts"] = int(extension_attempts)
        dp_stats["reachable_task_masks"] = frozenset(
            int(mask)
            for labels_by_mask in labels_by_count[1:]
            for mask in labels_by_mask.keys()
            if int(mask) > 0
        )

    for count in range(int(data.sortie_limit)):
        if deadline is not None and time.perf_counter() > deadline:
            record_dp_stats()
            return _collect_negative_journey_profile_labels(
                labels_by_count,
                data,
                profiles,
                base_reduced_cost,
                cut_duals,
                cuts,
                cut_masks,
                cut_value_cache,
                max_returned,
                selection_mode,
                forbidden_journey_signatures=forbidden_journey_signatures,
                duplicate_scan_limit=duplicate_scan_limit,
                dominant_task_set_cost_by_mask=dominant_task_set_cost_by_mask,
                pricing_config=pricing_config,
                branch_constraints=branch_constraints,
                dp_stats=dp_stats,
                cross_count_materialization_candidates=tuple(cross_count_materialization_by_mask.values()),
            )
        for mask, labels in list(labels_by_count[count].items()):
            if deadline is not None and time.perf_counter() > deadline:
                record_dp_stats()
                return _collect_negative_journey_profile_labels(
                    labels_by_count,
                    data,
                    profiles,
                    base_reduced_cost,
                    cut_duals,
                    cuts,
                    cut_masks,
                    cut_value_cache,
                    max_returned,
                    selection_mode,
                    forbidden_journey_signatures=forbidden_journey_signatures,
                    duplicate_scan_limit=duplicate_scan_limit,
                    dominant_task_set_cost_by_mask=dominant_task_set_cost_by_mask,
                    pricing_config=pricing_config,
                    branch_constraints=branch_constraints,
                    dp_stats=dp_stats,
                    status="INCOMPLETE",
                    cross_count_materialization_candidates=tuple(cross_count_materialization_by_mask.values()),
                )
            for label in list(labels):
                processed_labels += 1
                if deadline is not None and time.perf_counter() > deadline:
                    record_dp_stats()
                    return _collect_negative_journey_profile_labels(
                        labels_by_count,
                        data,
                        profiles,
                        base_reduced_cost,
                        cut_duals,
                        cuts,
                        cut_masks,
                        cut_value_cache,
                        max_returned,
                        selection_mode,
                        forbidden_journey_signatures=forbidden_journey_signatures,
                        duplicate_scan_limit=duplicate_scan_limit,
                        dominant_task_set_cost_by_mask=dominant_task_set_cost_by_mask,
                        pricing_config=pricing_config,
                        branch_constraints=branch_constraints,
                        dp_stats=dp_stats,
                        status="INCOMPLETE",
                        cross_count_materialization_candidates=tuple(cross_count_materialization_by_mask.values()),
                    )
                if bound_pruning_safe:
                    remaining = int(data.sortie_limit) - int(count)
                    disjoint_extra = disjoint_cache.value(int(mask), remaining)
                    if disjoint_extra is None:
                        optimistic_extra = optimistic_cache.value(int(mask), remaining)
                    else:
                        optimistic_extra = float(disjoint_extra)
                    future_cut_reward = _direct_completion_positive_subset_future_reward_bound(
                        int(mask),
                        int(remaining) * int(max_future_tasks_per_profile),
                        cut_duals,
                        cuts,
                        cut_masks,
                        positive_cut_reward_bound=positive_cut_reward_bound,
                    )
                    future_cut_reward += _profile_future_positive_fleet_cut_reward(int(mask), int(remaining), cut_duals, cuts)
                    lower_bound_objective = (
                        float(base_reduced_cost)
                        + float(label.value)
                        + float(optimistic_extra)
                        - _journey_cut_dual_value_cached(int(mask), cut_duals, cuts, cut_masks, cut_value_cache)
                        - float(future_cut_reward)
                    )
                    if lower_bound_objective >= -float(eps):
                        if dp_stats is not None:
                            dp_stats["bound_pruned_labels"] = int(dp_stats.get("bound_pruned_labels", 0)) + 1
                            if disjoint_extra is None:
                                pass
                            else:
                                dp_stats["disjoint_bound_pruned_labels"] = int(dp_stats.get("disjoint_bound_pruned_labels", 0)) + 1
                        continue
                candidate_records = compatible_profile_cache.records(mask, min_upper_start=float(label.end_time))
                profile_record_scans += len(candidate_records)
                if dp_stats is not None:
                    # This is diagnostic-only.  Avoid a second full compatible
                    # profile lookup for every DP label; in 10/20-task tails
                    # that extra count can dominate worker time.  When the
                    # cache has a full mask entry, use it.  Otherwise keep the
                    # conservative filtered count at zero rather than paying
                    # for a diagnostic-only reconstruction.
                    cached_records = compatible_profile_cache.by_used_mask.get(int(mask))
                    if cached_records is not None:
                        profile_time_filtered += max(0, int(len(cached_records)) - len(candidate_records))
                for _position, profile_index, profile in candidate_records:
                    extension_attempts += 1
                    if deadline is not None and time.perf_counter() > deadline:
                        record_dp_stats()
                        return _collect_negative_journey_profile_labels(
                            labels_by_count,
                            data,
                            profiles,
                            base_reduced_cost,
                            cut_duals,
                            cuts,
                            cut_masks,
                            cut_value_cache,
                            max_returned,
                            selection_mode,
                            forbidden_journey_signatures=forbidden_journey_signatures,
                            duplicate_scan_limit=duplicate_scan_limit,
                            dominant_task_set_cost_by_mask=dominant_task_set_cost_by_mask,
                            pricing_config=pricing_config,
                            branch_constraints=branch_constraints,
                            dp_stats=dp_stats,
                            status="INCOMPLETE",
                            cross_count_materialization_candidates=tuple(cross_count_materialization_by_mask.values()),
                        )
                    if compatible_profile_cache.requires_overlap_check and (mask & profile.mask):
                        continue
                    start = max(float(profile.lower_start), float(label.end_time))
                    if start > float(profile.upper_start) + 1.0e-9:
                        continue
                    new_end = start + float(profile.end_offset)
                    new_value = float(label.value) + float(profile.contribution)
                    new_mask = mask | profile.mask
                    if not _journey_mask_branch_allowed(new_mask, branch_constraints, task_to_bit, final=False):
                        continue
                    remaining_slots = int(data.sortie_limit) - int(count) - 1
                    if bool(getattr(pricing_config, "dp_same_completion_pruning_enabled", False)) and not (
                        _journey_same_completion_possible(
                            new_mask,
                            new_end,
                            remaining_slots,
                            branch_constraints,
                            task_to_bit,
                            compatible_profile_cache,
                        )
                    ):
                        if dp_stats is not None:
                            dp_stats["same_completion_pruned_labels"] = int(
                                dp_stats.get("same_completion_pruned_labels", 0)
                            ) + 1
                        continue
                    if bool(cross_count_dominance):
                        new_selected = (*label.selected, (int(profile_index), round(start, 6)))
                        if _profile_label_cross_count_dominated_by_values(
                            labels_by_count,
                            count + 1,
                            int(new_mask),
                            float(new_end),
                            float(new_value),
                            dp_stats,
                        ):
                            record_cross_count_materialization_candidate(
                                int(new_mask),
                                float(new_value),
                                new_selected,
                            )
                            continue
                        candidate = _JourneyLabel(new_end, new_value, new_selected)
                        added = _add_profile_label_cross_count(
                            labels_by_count,
                            count + 1,
                            new_mask,
                            candidate,
                            dp_stats,
                            max_labels_per_mask=max_labels_per_mask,
                            skip_precheck=True,
                        )
                    else:
                        if _profile_label_bucket_dominated_by_values(
                            labels_by_count[count + 1],
                            int(new_mask),
                            float(new_end),
                            float(new_value),
                        ):
                            continue
                        new_selected = (*label.selected, (int(profile_index), round(start, 6)))
                        candidate = _JourneyLabel(new_end, new_value, new_selected)
                        added = _add_profile_label(
                            labels_by_count[count + 1],
                            new_mask,
                            candidate,
                            dp_stats=dp_stats,
                            max_labels_per_mask=max_labels_per_mask,
                            skip_precheck=True,
                        )
                    state_count += int(added)
                    if bool(early_return_negative) and added:
                        objective = (
                            float(base_reduced_cost)
                            + float(new_value)
                            - _journey_cut_dual_value_cached(int(new_mask), cut_duals, cuts, cut_masks, cut_value_cache)
                        )
                        if objective < -float(eps):
                            if not _journey_mask_branch_allowed(new_mask, branch_constraints, task_to_bit, final=True):
                                continue
                            if _profile_candidate_task_set_cost_dominated(
                                data,
                                profiles,
                                new_selected,
                                int(new_mask),
                                dominant_task_set_cost_by_mask,
                            ):
                                if dp_stats is not None:
                                    dp_stats["dominated_task_set_candidates_filtered"] = int(
                                        dp_stats.get("dominated_task_set_candidates_filtered", 0)
                                    ) + 1
                                continue
                            early_candidates.append((objective, new_selected, int(new_mask)))
                            if _early_return_negative_candidates_ready(
                                early_candidates,
                                pricing_config,
                                dominant_task_set_cost_by_mask,
                                min_count=max(1, int(early_return_min_count)),
                            ):
                                early_candidates.sort(key=lambda item: (round(item[0], 9), len(item[1]), item[2], item[1]))
                                limited = _select_negative_journey_candidates(early_candidates, max_returned, selection_mode)
                                if dp_stats is not None:
                                    dp_stats["negative_candidate_count"] = len(early_candidates)
                                    negative_masks = frozenset(
                                        int(mask) for _objective, _selected, mask in early_candidates
                                    )
                                    dp_stats["negative_unique_mask_count"] = len(negative_masks)
                                    dp_stats["negative_new_mask_count"] = _negative_candidate_new_task_mask_count(
                                        early_candidates,
                                        dominant_task_set_cost_by_mask,
                                    )
                                    dp_stats["negative_task_masks"] = negative_masks
                                    dp_stats["negative_selected_candidate_count"] = len(limited)
                                    dp_stats["negative_selected_new_mask_count"] = _negative_candidate_new_task_mask_count(
                                        limited,
                                        dominant_task_set_cost_by_mask,
                                    )
                                    dp_stats["negative_selected_replacement_mask_count"] = max(
                                        0,
                                        len({int(mask) for _objective, _selected, mask in limited})
                                        - int(dp_stats["negative_selected_new_mask_count"]),
                                    )
                                    dp_stats["selected_task_masks"] = frozenset(
                                        int(mask) for _objective, _selected, mask in limited
                                    )
                                record_dp_stats()
                                return [(selected, objective) for objective, selected, _mask in limited], early_candidates[0][0], "INCOMPLETE"
                    if max_states > 0 and state_count > int(max_states):
                        record_dp_stats()
                        return _collect_negative_journey_profile_labels(
                            labels_by_count,
                            data,
                            profiles,
                            base_reduced_cost,
                            cut_duals,
                            cuts,
                            cut_masks,
                            cut_value_cache,
                            max_returned,
                            selection_mode,
                            forbidden_journey_signatures=forbidden_journey_signatures,
                            duplicate_scan_limit=duplicate_scan_limit,
                            dominant_task_set_cost_by_mask=dominant_task_set_cost_by_mask,
                            pricing_config=pricing_config,
                            branch_constraints=branch_constraints,
                            dp_stats=dp_stats,
                            status="INCOMPLETE",
                            cross_count_materialization_candidates=tuple(cross_count_materialization_by_mask.values()),
                        )
    trim_cross_count_materialization_candidates(force=True)
    record_dp_stats()
    return _collect_negative_journey_profile_labels(
        labels_by_count,
        data,
        profiles,
        base_reduced_cost,
        cut_duals,
        cuts,
        cut_masks,
        cut_value_cache,
        max_returned,
        selection_mode,
        forbidden_journey_signatures=forbidden_journey_signatures,
        duplicate_scan_limit=duplicate_scan_limit,
        dominant_task_set_cost_by_mask=dominant_task_set_cost_by_mask,
        pricing_config=pricing_config,
        branch_constraints=branch_constraints,
        dp_stats=dp_stats,
        status="OPTIMAL",
        cross_count_materialization_candidates=tuple(cross_count_materialization_by_mask.values()),
    )


def _collect_negative_journey_profile_labels(
    labels_by_count: list[dict[int, list[_JourneyLabel]]],
    data: FutureData,
    profiles: list[_SortieProfile],
    base_reduced_cost: float,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
    cut_value_cache: dict[int, float],
    max_returned: int,
    selection_mode: str,
    *,
    forbidden_journey_signatures: set[tuple] | frozenset[tuple] | None = None,
    duplicate_scan_limit: int = 10000,
    dominant_task_set_cost_by_mask: dict[int, float] | None = None,
    pricing_config: JourneyPricingConfig | None = None,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
    dp_stats: dict[str, int] | None = None,
    status: str = "INCOMPLETE",
    cross_count_materialization_candidates: tuple[tuple[float, tuple[tuple[int, float], ...], int], ...] = tuple(),
) -> tuple[list[tuple[tuple[tuple[int, float], ...], float]], float | None, str]:
    candidates: list[tuple[float, tuple[tuple[int, float], ...], int]] = []
    materialization_by_mask: dict[int, tuple[float, tuple[tuple[int, float], ...], int]] = {}
    no_negative_materialization_by_mask: dict[int, tuple[float, tuple[tuple[int, float], ...], int]] = {}
    replacement_materialization_by_mask: dict[int, tuple[float, tuple[tuple[int, float], ...], int]] = {}
    best_value: float | None = None
    best_objective_by_mask: dict[int, float] = {}
    task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
    materialization_slack = (
        max(0.0, float(getattr(pricing_config, "profile_true_rc_materialization_slack", 0.0)))
        if pricing_config is not None
        else 0.0
    )
    no_negative_materialization_slack = (
        max(0.0, float(getattr(pricing_config, "profile_no_negative_true_rc_materialization_slack", 0.0)))
        if pricing_config is not None
        else 0.0
    )
    replacement_materialization_slack = (
        max(0.0, float(getattr(pricing_config, "profile_replacement_true_rc_materialization_slack", 0.0)))
        if pricing_config is not None
        else 0.0
    )
    for labels_by_mask in labels_by_count[1:]:
        for mask, labels in labels_by_mask.items():
            if not _journey_mask_branch_allowed(int(mask), branch_constraints, task_to_bit, final=True):
                continue
            for label in labels:
                if not label.selected:
                    continue
                objective = (
                    float(base_reduced_cost)
                    + float(label.value)
                    - _journey_cut_dual_value_cached(int(mask), cut_duals, cuts, cut_masks, cut_value_cache)
                )
                if best_value is None or objective < best_value - 1.0e-9:
                    best_value = objective
                mask_key = int(mask)
                old_mask_best = best_objective_by_mask.get(mask_key)
                if old_mask_best is None or objective < float(old_mask_best) - 1.0e-9:
                    best_objective_by_mask[mask_key] = float(objective)
                if objective < -1.0e-9:
                    candidates.append((objective, label.selected, int(mask)))
                elif materialization_slack > 0.0 and objective < float(materialization_slack):
                    old_candidate = materialization_by_mask.get(mask_key)
                    if old_candidate is None or objective < float(old_candidate[0]) - 1.0e-9:
                        materialization_by_mask[mask_key] = (objective, label.selected, int(mask))
                elif no_negative_materialization_slack > 0.0 and objective < float(no_negative_materialization_slack):
                    old_candidate = no_negative_materialization_by_mask.get(mask_key)
                    if old_candidate is None or objective < float(old_candidate[0]) - 1.0e-9:
                        no_negative_materialization_by_mask[mask_key] = (
                            objective,
                            label.selected,
                            int(mask),
                        )
                if (
                    replacement_materialization_slack > 0.0
                    and objective < float(replacement_materialization_slack)
                    and _profile_candidate_task_set_cost_improves(
                        data,
                        profiles,
                        label.selected,
                        int(mask),
                        dominant_task_set_cost_by_mask,
                        eps=float(getattr(pricing_config, "eps", 1.0e-6)) if pricing_config is not None else 1.0e-6,
                    )
                ):
                    old_candidate = replacement_materialization_by_mask.get(mask_key)
                    old_key = (
                        math.inf if old_candidate is None else round(float(old_candidate[0]), 9),
                        math.inf if old_candidate is None else len(old_candidate[1]),
                    )
                    new_key = (round(float(objective), 9), len(label.selected))
                    if old_candidate is None or new_key < old_key:
                        replacement_materialization_by_mask[mask_key] = (
                            objective,
                            label.selected,
                            int(mask),
                        )
    if dp_stats is not None:
        cap = 0
        if pricing_config is not None:
            cap = int(getattr(pricing_config, "profile_best_objective_diagnostics_max_masks", 0))
        if cap <= 0:
            cap = 256
        ordered_best = sorted(
            best_objective_by_mask.items(),
            key=lambda item: (round(float(item[1]), 9), int(item[0])),
        )[: max(1, int(cap))]
        dp_stats["best_objective_by_mask"] = {
            int(mask): round(float(value), 9)
            for mask, value in ordered_best
        }
    materialization_candidates = list(materialization_by_mask.values())
    materialization_candidate_count = len(materialization_candidates)
    materialization_cap = (
        max(0, int(getattr(pricing_config, "profile_true_rc_materialization_max_candidates", 0)))
        if pricing_config is not None
        else 0
    )
    if materialization_cap > 0 and len(materialization_candidates) > materialization_cap:
        materialization_candidates = sorted(
            materialization_candidates,
            key=lambda item: (round(float(item[0]), 9), len(item[1]), int(item[2]), item[1]),
        )[:materialization_cap]
    no_negative_materialization_candidates = list(no_negative_materialization_by_mask.values())
    no_negative_materialization_candidate_count = len(no_negative_materialization_candidates)
    no_negative_materialization_cap = (
        max(0, int(getattr(pricing_config, "profile_no_negative_true_rc_materialization_max_candidates", 0)))
        if pricing_config is not None
        else 0
    )
    if (
        no_negative_materialization_cap > 0
        and len(no_negative_materialization_candidates) > no_negative_materialization_cap
    ):
        no_negative_materialization_candidates = sorted(
            no_negative_materialization_candidates,
            key=lambda item: (round(float(item[0]), 9), len(item[1]), int(item[2]), item[1]),
        )[:no_negative_materialization_cap]
    replacement_materialization_candidates = list(replacement_materialization_by_mask.values())
    replacement_materialization_candidate_count = len(replacement_materialization_candidates)
    replacement_materialization_cap = (
        max(0, int(getattr(pricing_config, "profile_replacement_true_rc_materialization_max_candidates", 0)))
        if pricing_config is not None
        else 0
    )
    if replacement_materialization_cap > 0 and len(replacement_materialization_candidates) > replacement_materialization_cap:
        replacement_materialization_candidates = sorted(
            replacement_materialization_candidates,
            key=lambda item: (round(float(item[0]), 9), len(item[1]), int(item[2]), item[1]),
        )[:replacement_materialization_cap]
    cross_count_materialization_candidates_list = list(cross_count_materialization_candidates)
    cross_count_materialization_candidate_count = len(cross_count_materialization_candidates_list)
    cross_count_materialization_cap = (
        max(0, int(getattr(pricing_config, "profile_cross_count_true_rc_materialization_max_candidates", 0)))
        if pricing_config is not None
        else 0
    )
    if (
        cross_count_materialization_cap > 0
        and len(cross_count_materialization_candidates_list) > cross_count_materialization_cap
    ):
        cross_count_materialization_candidates_list = sorted(
            cross_count_materialization_candidates_list,
            key=lambda item: (round(float(item[0]), 9), len(item[1]), int(item[2]), item[1]),
        )[:cross_count_materialization_cap]
    # The no-negative materialization pool is a narrow worker repair for the
    # hard tail where profile DP finds no rough-negative labels but the same
    # mask can still instantiate to a true-RC negative journey.  Do not mix it
    # into ordinary negative rounds; doing so previously inflated duplicate and
    # replacement churn without improving the certificate tail.
    no_negative_materialization_active = not candidates and bool(no_negative_materialization_candidates)
    selection_candidates = (
        [*no_negative_materialization_candidates, *cross_count_materialization_candidates_list]
        if no_negative_materialization_active
        else [
            *candidates,
            *materialization_candidates,
            *replacement_materialization_candidates,
            *cross_count_materialization_candidates_list,
        ]
    )
    if dp_stats is not None:
        dp_stats["materialization_candidate_count"] = materialization_candidate_count
        dp_stats["materialization_candidate_selected_for_scan_count"] = len(materialization_candidates)
        dp_stats["materialization_candidate_cap_filtered"] = max(
            0,
            int(materialization_candidate_count) - int(len(materialization_candidates)),
        )
        dp_stats["no_negative_materialization_candidate_count"] = no_negative_materialization_candidate_count
        dp_stats["no_negative_materialization_selected_for_scan_count"] = (
            len(no_negative_materialization_candidates)
            if bool(no_negative_materialization_active)
            else 0
        )
        dp_stats["no_negative_materialization_candidate_cap_filtered"] = max(
            0,
            int(no_negative_materialization_candidate_count) - int(len(no_negative_materialization_candidates)),
        )
        dp_stats["replacement_materialization_candidate_count"] = replacement_materialization_candidate_count
        dp_stats["replacement_materialization_selected_for_scan_count"] = (
            0 if bool(no_negative_materialization_active) else len(replacement_materialization_candidates)
        )
        dp_stats["replacement_materialization_candidate_cap_filtered"] = max(
            0,
            int(replacement_materialization_candidate_count) - int(len(replacement_materialization_candidates)),
        )
        dp_stats["cross_count_materialization_candidate_count"] = cross_count_materialization_candidate_count
        dp_stats["cross_count_materialization_selected_for_scan_count"] = len(
            cross_count_materialization_candidates_list
        )
        dp_stats["cross_count_materialization_candidate_cap_filtered"] = max(
            0,
            int(cross_count_materialization_candidate_count)
            - int(len(cross_count_materialization_candidates_list)),
        )
    limited, status = _select_nonduplicate_negative_journey_candidates(
        data,
        profiles,
        selection_candidates,
        max_returned,
        selection_mode,
        forbidden_journey_signatures=forbidden_journey_signatures,
        duplicate_scan_limit=duplicate_scan_limit,
        dominant_task_set_cost_by_mask=dominant_task_set_cost_by_mask,
        pricing_config=pricing_config,
        dp_stats=dp_stats,
        status=status,
    )
    if dp_stats is not None:
        dp_stats["materialization_selected_candidate_count"] = (
            0
            if bool(no_negative_materialization_active)
            else sum(1 for objective, _selected, _mask in limited if float(objective) >= -1.0e-9)
        )
        no_negative_selected = set(no_negative_materialization_candidates)
        dp_stats["no_negative_materialization_selected_candidate_count"] = (
            sum(1 for candidate in limited if candidate in no_negative_selected)
            if bool(no_negative_materialization_active)
            else 0
        )
        replacement_selected = set(replacement_materialization_candidates)
        dp_stats["replacement_materialization_selected_candidate_count"] = (
            0
            if bool(no_negative_materialization_active)
            else sum(1 for candidate in limited if candidate in replacement_selected)
        )
        cross_count_selected = set(cross_count_materialization_candidates_list)
        dp_stats["cross_count_materialization_selected_candidate_count"] = sum(
            1 for candidate in limited if candidate in cross_count_selected
        )
    return [(selected, objective) for objective, selected, _mask in limited], best_value, status


def _journey_mask_branch_allowed(
    mask: int,
    constraints: tuple[BranchConstraint, ...],
    task_to_bit: dict[int, int],
    *,
    final: bool,
) -> bool:
    mask = int(mask)
    for constraint in constraints:
        if constraint.task_j is None:
            return False
        left_bit = task_to_bit.get(int(constraint.task_i))
        right_bit = task_to_bit.get(int(constraint.task_j))
        if left_bit is None or right_bit is None:
            continue
        left = bool(mask & (1 << int(left_bit)))
        right = bool(mask & (1 << int(right_bit)))
        if constraint.kind == "separate_vehicle":
            if left and right:
                return False
        elif constraint.kind == "same_vehicle":
            if bool(final) and left != right:
                return False
        else:
            return False
    return True


def _journey_same_completion_possible(
    mask: int,
    end_time: float,
    remaining_slots: int,
    constraints: tuple[BranchConstraint, ...],
    task_to_bit: dict[int, int],
    compatible_profile_cache: _CompatibleProfileCache,
) -> bool:
    """Return whether a partial journey can still satisfy same-vehicle rows.

    This is a one-sided exact-safe pruning test.  If a same-vehicle pair is
    currently split across the partial journey mask, the missing task must be
    present in at least one future sortie profile that can still be appended in
    time and without reusing already covered tasks.  If not, no completion of
    the partial label can satisfy the branch row.
    """

    mask = int(mask)
    if int(remaining_slots) <= 0:
        for constraint in constraints:
            if constraint.kind != "same_vehicle" or constraint.task_j is None:
                continue
            left_bit = task_to_bit.get(int(constraint.task_i))
            right_bit = task_to_bit.get(int(constraint.task_j))
            if left_bit is None or right_bit is None:
                continue
            if bool(mask & (1 << int(left_bit))) != bool(mask & (1 << int(right_bit))):
                return False
        return True

    missing_bits: set[int] = set()
    for constraint in constraints:
        if constraint.kind != "same_vehicle" or constraint.task_j is None:
            continue
        left_bit = task_to_bit.get(int(constraint.task_i))
        right_bit = task_to_bit.get(int(constraint.task_j))
        if left_bit is None or right_bit is None:
            continue
        left_mask = 1 << int(left_bit)
        right_mask = 1 << int(right_bit)
        left = bool(mask & left_mask)
        right = bool(mask & right_mask)
        if left and not right:
            missing_bits.add(right_mask)
        elif right and not left:
            missing_bits.add(left_mask)
    if not missing_bits:
        return True

    remaining = set(missing_bits)
    for _position, _profile_index, profile in compatible_profile_cache.records(mask, min_upper_start=float(end_time)):
        profile_mask = int(profile.mask)
        if profile_mask & mask:
            continue
        covered = {bit for bit in remaining if profile_mask & bit}
        if covered:
            remaining.difference_update(covered)
            if not remaining:
                return True
    return False


def _sortie_profile_mask_allowed_by_branch(
    mask: int,
    constraints: tuple[BranchConstraint, ...],
    task_to_bit: dict[int, int],
) -> bool:
    """Safe profile-level branch pruning.

    A separate-vehicle Ryan-Foster constraint forbids any final journey from
    containing both tasks, so a single sortie profile containing both can be
    discarded immediately.  Same-vehicle constraints are not applied here:
    a profile containing only one side may still be completed by another
    sortie in the same journey.
    """

    mask = int(mask)
    for constraint in constraints:
        if constraint.kind != "separate_vehicle" or constraint.task_j is None:
            continue
        left_bit = task_to_bit.get(int(constraint.task_i))
        right_bit = task_to_bit.get(int(constraint.task_j))
        if left_bit is None or right_bit is None:
            continue
        if (mask & (1 << int(left_bit))) and (mask & (1 << int(right_bit))):
            return False
    return True


def _branch_constraints_cache_key(constraints: tuple[BranchConstraint, ...]) -> tuple:
    return tuple(
        (
            str(constraint.kind),
            int(constraint.task_i),
            None if constraint.task_j is None else int(constraint.task_j),
            None if constraint.vehicle is None else int(constraint.vehicle),
        )
        for constraint in constraints
    )


def _early_return_candidate_count(
    candidates: list[tuple[float, tuple[tuple[int, float], ...], int]],
    pricing_config: JourneyPricingConfig | None,
) -> int:
    if pricing_config is not None and bool(getattr(pricing_config, "early_return_unique_masks_enabled", False)):
        return len({int(mask) for _objective, _selected, mask in candidates})
    return len(candidates)


def _negative_candidate_new_task_mask_count(
    candidates: list[tuple[float, tuple[tuple[int, float], ...], int]],
    dominant_task_set_cost_by_mask: dict[int, float] | None,
) -> int:
    masks = {int(mask) for _objective, _selected, mask in candidates}
    if not masks:
        return 0
    if not dominant_task_set_cost_by_mask:
        return len(masks)
    existing_masks = {int(mask) for mask in dominant_task_set_cost_by_mask.keys()}
    return sum(1 for mask in masks if int(mask) not in existing_masks)


def _early_return_negative_candidates_ready(
    candidates: list[tuple[float, tuple[tuple[int, float], ...], int]],
    pricing_config: JourneyPricingConfig | None,
    dominant_task_set_cost_by_mask: dict[int, float] | None,
    *,
    min_count: int,
) -> bool:
    if _early_return_candidate_count(candidates, pricing_config) < max(1, int(min_count)):
        return False
    new_min = 0
    if pricing_config is not None:
        new_min = max(0, int(getattr(pricing_config, "early_return_new_task_set_min_count", 0)))
    if new_min <= 0:
        return True
    return _negative_candidate_new_task_mask_count(candidates, dominant_task_set_cost_by_mask) >= int(new_min)


def _select_negative_journey_candidates(
    candidates: list[tuple[float, tuple[tuple[int, float], ...], int]],
    max_returned: int,
    selection_mode: str,
) -> list[tuple[float, tuple[tuple[int, float], ...], int]]:
    if not candidates:
        return []
    limit = max(1, int(max_returned))
    ordered = sorted(candidates, key=lambda item: (round(item[0], 9), len(item[1]), item[2], item[1]))
    ordered = _best_negative_candidate_per_task_mask(ordered)
    mode = str(selection_mode)
    if mode not in {"diverse", "integer_diverse", "orthogonal"} or len(ordered) <= limit:
        return ordered[:limit]
    if mode == "integer_diverse":
        return _select_integer_diverse_negative_journey_candidates(ordered, limit)
    if mode == "orthogonal":
        return _select_orthogonal_negative_journey_candidates(ordered, limit)

    selected: list[tuple[float, tuple[tuple[int, float], ...], int]] = []
    seen_masks: set[int] = set()

    def add(candidate: tuple[float, tuple[tuple[int, float], ...], int]) -> None:
        if len(selected) >= limit or candidate in selected:
            return
        selected.append(candidate)
        seen_masks.add(int(candidate[2]))

    for candidate in ordered[: max(1, limit // 2)]:
        add(candidate)
    for candidate in ordered:
        if int(candidate[2]) not in seen_masks:
            add(candidate)
        if len(selected) >= limit:
            break
    by_task_count_seen = {int(candidate[2]).bit_count() for candidate in selected}
    for candidate in ordered:
        task_count = int(candidate[2]).bit_count()
        if task_count not in by_task_count_seen:
            add(candidate)
            by_task_count_seen.add(task_count)
        if len(selected) >= limit:
            break
    for candidate in ordered:
        add(candidate)
        if len(selected) >= limit:
            break
    return selected


def _mask_jaccard(left: int, right: int) -> float:
    union = int(left | right).bit_count()
    if union <= 0:
        return 0.0
    return float(int(left & right).bit_count()) / float(union)


def _mask_containment(left: int, right: int) -> float:
    left_count = int(left).bit_count()
    right_count = int(right).bit_count()
    base = min(left_count, right_count)
    if base <= 0:
        return 0.0
    return float(int(left & right).bit_count()) / float(base)


def _select_orthogonal_negative_journey_candidates(
    ordered: list[tuple[float, tuple[tuple[int, float], ...], int]],
    limit: int,
    *,
    top_k_strongest: int = 5,
    max_jaccard: float = 0.5,
    max_containment: float = 0.8,
) -> list[tuple[float, tuple[tuple[int, float], ...], int]]:
    """Lightweight worker harvesting on final task-set masks.

    Profile/streaming pricing is still only a worker, not a certificate.  This
    selector broadens the batch of true-RC negative directions returned to the
    RMP without changing any reduced-cost value or no-column proof semantics.
    """

    selected: list[tuple[float, tuple[tuple[int, float], ...], int]] = []
    selected_masks: set[int] = set()
    limit = max(1, int(limit))
    strongest = max(1, min(limit, int(top_k_strongest), max(1, limit // 4)))

    def add(candidate: tuple[float, tuple[tuple[int, float], ...], int]) -> None:
        if len(selected) >= limit or candidate in selected:
            return
        selected.append(candidate)
        selected_masks.add(int(candidate[2]))

    for candidate in ordered[:strongest]:
        add(candidate)

    for candidate in ordered[strongest:]:
        if len(selected) >= limit:
            break
        mask = int(candidate[2])
        if mask in selected_masks:
            continue
        if any(
            _mask_jaccard(mask, selected_mask) > float(max_jaccard)
            or _mask_containment(mask, selected_mask) > float(max_containment)
            for selected_mask in selected_masks
        ):
            continue
        add(candidate)

    # Fallback fill keeps the worker productive when the instance naturally has
    # many overlapping profitable task sets.
    for candidate in ordered:
        if len(selected) >= limit:
            break
        add(candidate)
    return selected


def _best_negative_candidate_per_task_mask(
    ordered: list[tuple[float, tuple[tuple[int, float], ...], int]]
) -> list[tuple[float, tuple[tuple[int, float], ...], int]]:
    """Keep only the best candidate for each final task set.

    Journey-master coefficients currently depend on the final task set, fleet
    count, and subset-row cuts.  For two candidates with the same final mask,
    the lower reduced-cost candidate has no larger journey cost and dominates
    the other for the current master.  Returning only this representative
    avoids feeding the RMP many equivalent schedule variants during degenerate
    tailing rounds.
    """

    best_by_mask: dict[int, tuple[float, tuple[tuple[int, float], ...], int]] = {}
    for candidate in ordered:
        mask = int(candidate[2])
        if mask not in best_by_mask:
            best_by_mask[mask] = candidate
    return sorted(best_by_mask.values(), key=lambda item: (round(item[0], 9), len(item[1]), item[2], item[1]))


def _select_integer_diverse_negative_journey_candidates(
    ordered: list[tuple[float, tuple[tuple[int, float], ...], int]],
    limit: int,
) -> list[tuple[float, tuple[tuple[int, float], ...], int]]:
    selected: list[tuple[float, tuple[tuple[int, float], ...], int]] = []
    seed_count = max(1, int(limit) // 3)
    seen_signatures: set[tuple] = set()

    def feature(candidate: tuple[float, tuple[tuple[int, float], ...], int]) -> tuple:
        _objective, selected_profiles, mask = candidate
        starts = tuple(round(float(start), 1) for _profile_index, start in selected_profiles)
        start_bucket = None if not starts else int(min(starts) // 60)
        return (
            int(mask),
            int(mask).bit_count(),
            len(selected_profiles),
            start_bucket,
        )

    def add(candidate: tuple[float, tuple[tuple[int, float], ...], int]) -> None:
        if len(selected) >= int(limit) or candidate in selected:
            return
        selected.append(candidate)
        seen_signatures.add(feature(candidate))

    for candidate in ordered[:seed_count]:
        add(candidate)
    for candidate in ordered:
        if feature(candidate) not in seen_signatures:
            add(candidate)
        if len(selected) >= int(limit):
            break

    seen_masks = {int(candidate[2]) for candidate in selected}
    for candidate in ordered:
        mask = int(candidate[2])
        if mask in seen_masks:
            continue
        add(candidate)
        seen_masks.add(mask)
        if len(selected) >= int(limit):
            break

    seen_sortie_counts = {len(candidate[1]) for candidate in selected}
    for candidate in ordered:
        count = len(candidate[1])
        if count in seen_sortie_counts:
            continue
        add(candidate)
        seen_sortie_counts.add(count)
        if len(selected) >= int(limit):
            break

    for candidate in ordered:
        add(candidate)
        if len(selected) >= int(limit):
            break
    return selected


def _select_nonduplicate_negative_journey_candidates(
    data: FutureData,
    profiles: list[_SortieProfile],
    candidates: list[tuple[float, tuple[tuple[int, float], ...], int]],
    max_returned: int,
    selection_mode: str,
    *,
    forbidden_journey_signatures: set[tuple] | frozenset[tuple] | None,
    duplicate_scan_limit: int,
    dominant_task_set_cost_by_mask: dict[int, float] | None,
    pricing_config: JourneyPricingConfig | None,
    dp_stats: dict[str, int] | None,
    status: str,
) -> tuple[list[tuple[float, tuple[tuple[int, float], ...], int]], str]:
    if not candidates:
        if dp_stats is not None:
            dp_stats["negative_task_masks"] = frozenset()
            dp_stats["selected_task_masks"] = frozenset()
            dp_stats["negative_new_mask_count"] = 0
            dp_stats["negative_selected_new_mask_count"] = 0
            dp_stats["negative_selected_replacement_mask_count"] = 0
        return [], status
    rough_negative_candidates = [
        candidate for candidate in candidates if float(candidate[0]) < -1.0e-9
    ]
    if dp_stats is not None:
        dp_stats["negative_candidate_count"] = len(rough_negative_candidates)
        negative_masks = frozenset(int(mask) for _objective, _selected, mask in rough_negative_candidates)
        dp_stats["negative_unique_mask_count"] = len(negative_masks)
        dp_stats["negative_new_mask_count"] = _negative_candidate_new_task_mask_count(
            rough_negative_candidates,
            dominant_task_set_cost_by_mask,
        )
        dp_stats["negative_task_masks"] = negative_masks
    forbidden = forbidden_journey_signatures or set()
    if not forbidden and not dominant_task_set_cost_by_mask:
        selected_without_forbidden = []
        materialization_filtered = 0
        for candidate in _select_negative_journey_candidates(candidates, len(candidates), selection_mode):
            _objective, selected_profiles, _mask = candidate
            if _profile_materialization_filter_enabled(pricing_config) and not _selected_profiles_materializable(
                data,
                profiles,
                selected_profiles,
                pricing_config,
            ):
                materialization_filtered += 1
                continue
            selected_without_forbidden.append(candidate)
            if len(selected_without_forbidden) >= max(1, int(max_returned)):
                break
        if dp_stats is not None:
            rough_selected = [
                candidate for candidate in selected_without_forbidden if float(candidate[0]) < -1.0e-9
            ]
            dp_stats["profile_materialization_infeasible_candidates_filtered"] = int(
                dp_stats.get("profile_materialization_infeasible_candidates_filtered", 0)
            ) + int(materialization_filtered)
            dp_stats["negative_selected_candidate_count"] = len(rough_selected)
            dp_stats["negative_selected_new_mask_count"] = _negative_candidate_new_task_mask_count(
                rough_selected,
                dominant_task_set_cost_by_mask,
            )
            dp_stats["negative_selected_replacement_mask_count"] = max(
                0,
                len({int(mask) for _objective, _selected, mask in rough_selected})
                - int(dp_stats["negative_selected_new_mask_count"]),
            )
            dp_stats["selected_task_masks"] = frozenset(
                int(mask) for _objective, _selected, mask in selected_without_forbidden
            )
        return selected_without_forbidden, status

    ordered = _select_negative_journey_candidates(candidates, len(candidates), selection_mode)
    scan_limit = int(duplicate_scan_limit)
    if scan_limit <= 0:
        scan_limit = len(ordered)
    selected: list[tuple[float, tuple[tuple[int, float], ...], int]] = []
    scanned = 0
    filtered = 0
    limited = False
    for candidate in ordered:
        if scanned >= scan_limit:
            limited = True
            break
        scanned += 1
        _objective, selected_profiles, _mask = candidate
        if _profile_candidate_task_set_cost_dominated(
            data,
            profiles,
            selected_profiles,
            int(_mask),
            dominant_task_set_cost_by_mask,
        ):
            filtered += 1
            if dp_stats is not None:
                dp_stats["dominated_task_set_candidates_filtered"] = int(
                    dp_stats.get("dominated_task_set_candidates_filtered", 0)
                ) + 1
            continue
        if forbidden:
            signature = _selected_profile_journey_signature(data, profiles, selected_profiles, pricing_config)
            if signature in forbidden:
                filtered += 1
                continue
        if _profile_materialization_filter_enabled(pricing_config) and not _selected_profiles_materializable(
            data,
            profiles,
            selected_profiles,
            pricing_config,
        ):
            filtered += 1
            if dp_stats is not None:
                dp_stats["profile_materialization_infeasible_candidates_filtered"] = int(
                    dp_stats.get("profile_materialization_infeasible_candidates_filtered", 0)
                ) + 1
            continue
        selected.append(candidate)
        if len(selected) >= max(1, int(max_returned)):
            break
    if dp_stats is not None:
        rough_selected = [candidate for candidate in selected if float(candidate[0]) < -1.0e-9]
        dp_stats["duplicate_candidate_scan_count"] = int(dp_stats.get("duplicate_candidate_scan_count", 0)) + int(scanned)
        dp_stats["duplicate_candidates_filtered"] = int(dp_stats.get("duplicate_candidates_filtered", 0)) + int(filtered)
        dp_stats["negative_selected_candidate_count"] = len(rough_selected)
        dp_stats["negative_selected_new_mask_count"] = _negative_candidate_new_task_mask_count(
            rough_selected,
            dominant_task_set_cost_by_mask,
        )
        dp_stats["negative_selected_replacement_mask_count"] = max(
            0,
            len({int(mask) for _objective, _selected, mask in rough_selected})
            - int(dp_stats["negative_selected_new_mask_count"]),
        )
        dp_stats["selected_task_masks"] = frozenset(int(mask) for _objective, _selected, mask in selected)
        if limited:
            dp_stats["duplicate_scan_limited"] = 1
    if limited and not selected:
        return [], "INCOMPLETE"
    return selected, status


def _profile_materialization_filter_enabled(pricing_config: JourneyPricingConfig | None) -> bool:
    if pricing_config is None:
        return False
    return bool(getattr(pricing_config, "profile_materialization_feasibility_filter_enabled", False))


def _selected_profiles_materializable(
    data: FutureData,
    profiles: list[_SortieProfile],
    selected_profiles: tuple[tuple[int, float], ...],
    pricing_config: JourneyPricingConfig | None,
) -> bool:
    config = pricing_config if pricing_config is not None else JourneyPricingConfig()
    trips = _instantiate_profile_journey(data, profiles, selected_profiles, config)
    if not trips:
        return False
    return make_journey(data, trips) is not None


def _dominant_task_set_costs_by_mask(
    data: FutureData,
    dominant_task_set_costs: dict[frozenset[int], float] | None,
) -> dict[int, float]:
    if not dominant_task_set_costs:
        return {}
    task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
    result: dict[int, float] = {}
    for task_set, cost in dominant_task_set_costs.items():
        mask = 0
        valid = True
        for task in task_set:
            task = int(task)
            if task not in task_to_bit:
                valid = False
                break
            mask |= 1 << task_to_bit[task]
        if not valid or mask == 0:
            continue
        result[mask] = min(float(result.get(mask, float("inf"))), float(cost))
    return result


def _profile_selected_candidate_cost(
    data: FutureData,
    profiles: list[_SortieProfile],
    selected: tuple[tuple[int, float], ...],
) -> float:
    candidate_cost = float(data.fixed_vehicle_cost)
    for profile_index, _start in selected:
        candidate_cost += float(profiles[int(profile_index)].cost)
    return float(candidate_cost)


def _profile_candidate_task_set_cost_dominated(
    data: FutureData,
    profiles: list[_SortieProfile],
    selected: tuple[tuple[int, float], ...],
    mask: int,
    dominant_task_set_cost_by_mask: dict[int, float] | None,
) -> bool:
    if not dominant_task_set_cost_by_mask:
        return False
    incumbent_cost = dominant_task_set_cost_by_mask.get(int(mask))
    if incumbent_cost is None:
        return False
    candidate_cost = _profile_selected_candidate_cost(data, profiles, selected)
    return bool(float(incumbent_cost) <= candidate_cost + 1.0e-9)


def _profile_candidate_task_set_cost_improves(
    data: FutureData,
    profiles: list[_SortieProfile],
    selected: tuple[tuple[int, float], ...],
    mask: int,
    dominant_task_set_cost_by_mask: dict[int, float] | None,
    *,
    eps: float,
) -> bool:
    if not dominant_task_set_cost_by_mask:
        return False
    incumbent_cost = dominant_task_set_cost_by_mask.get(int(mask))
    if incumbent_cost is None:
        return False
    candidate_cost = _profile_selected_candidate_cost(data, profiles, selected)
    return bool(candidate_cost < float(incumbent_cost) - max(1.0e-9, float(eps)))


def _journey_task_set_cost_dominated(
    journey: JourneyColumn,
    dominant_task_set_costs: dict[frozenset[int], float] | None,
) -> bool:
    if not dominant_task_set_costs:
        return False
    key = frozenset(int(task) for task in journey.task_set)
    incumbent_cost = dominant_task_set_costs.get(key)
    return bool(incumbent_cost is not None and float(incumbent_cost) <= float(journey.cost) + 1.0e-9)


def _selected_profile_journey_signature(
    data: FutureData,
    profiles: list[_SortieProfile],
    selected: tuple[tuple[int, float], ...],
    pricing_config: JourneyPricingConfig | None,
) -> tuple[tuple[tuple[int, ...], tuple[str, ...], float], ...]:
    # This mirrors JourneyColumn.signature without building full TimedTrip
    # objects.  It keeps duplicate filtering inside the pricing oracle cheap.
    trip_keys: list[tuple[float, float, tuple[int, ...], tuple[str, ...], tuple[tuple[int, ...], tuple[str, ...], float]]] = []
    for profile_index, start in selected:
        profile = profiles[int(profile_index)]
        start_time = rounded(float(start))
        end_time = rounded(float(start) + float(profile.end_offset))
        arc_option_ids = tuple(option.option_id for option in profile.arc_options)
        trip_signature = (tuple(int(task) for task in profile.sequence), arc_option_ids, start_time)
        trip_keys.append((start_time, end_time, tuple(int(task) for task in profile.sequence), arc_option_ids, trip_signature))
    trip_keys.sort(key=lambda item: (item[0], item[1], item[2], item[3]))
    return tuple(item[-1] for item in trip_keys)


def _journey_cut_dual_value_cached(
    mask: int,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
    cache: dict[int, float],
) -> float:
    if int(mask) not in cache:
        cache[int(mask)] = _journey_cut_dual_value(int(mask), cut_duals, cuts, cut_masks)
    return cache[int(mask)]


def _profile_cut_penalty_pruning_safe(cut_duals: dict[int, float], cuts: tuple[FutureCut, ...]) -> bool:
    for cut_index, cut in enumerate(cuts):
        dual = float(cut_duals.get(int(cut_index), 0.0))
        if abs(dual) <= 1.0e-9:
            continue
        if getattr(cut, "kind", "") != "subset_row":
            return False
        if dual > 1.0e-9:
            return False
    return True


def _profile_bound_pruning_cut_safe(cut_duals: dict[int, float], cuts: tuple[FutureCut, ...]) -> bool:
    """Return whether profile-DP suffix pruning can account for cut duals safely.

    The profile suffix bound can handle subset-row cuts by subtracting the exact
    reward or penalty already implied by the current task mask and an upper
    bound on future positive SRC reward.  Fleet cuts are also safe: once the
    partial journey is non-empty their coefficient is already fully realized,
    while the empty start label subtracts an upper bound on future positive
    fleet reward.  Other dynamic cut families stay disabled.
    """

    if not cut_duals or not cuts:
        return True
    for cut_index, cut in enumerate(cuts):
        dual = float(cut_duals.get(int(cut_index), 0.0))
        if abs(dual) <= 1.0e-9:
            continue
        if getattr(cut, "kind", "") not in {"subset_row", "fleet_lower_bound", "fleet_upper_bound"}:
            return False
    return True


def _profile_future_positive_fleet_cut_reward(
    mask: int,
    remaining_profile_capacity: int,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
) -> float:
    if int(mask) != 0 or int(remaining_profile_capacity) <= 0 or not cut_duals or not cuts:
        return 0.0
    reward = 0.0
    for cut_index, cut in enumerate(cuts):
        if getattr(cut, "kind", "") not in {"fleet_lower_bound", "fleet_upper_bound"}:
            continue
        dual = float(cut_duals.get(int(cut_index), 0.0))
        if dual > 1.0e-12:
            reward += dual
    return float(reward)


def _direct_completion_bound_cut_safe(cut_duals: dict[int, float], cuts: tuple[FutureCut, ...]) -> bool:
    """Return whether direct-label suffix bounds may ignore future cut changes.

    The completion suffix table only contains task-cover duals.  Subset-row cuts
    stay safe because pruning sites add an explicit optimistic upper bound on
    any future positive SRC reward; negative SRC duals only create penalties, so
    ignoring their future increase is conservative.  Fleet cuts are safe here:
    direct-label pruning is applied only after a non-empty new label is created,
    and the non-empty fleet-cut coefficient is already included in that label's
    true objective; adding more sorties does not change it.
    """

    if not cut_duals or not cuts:
        return True
    for cut_index, cut in enumerate(cuts):
        dual = float(cut_duals.get(int(cut_index), 0.0))
        if abs(dual) <= 1.0e-9:
            continue
        kind = getattr(cut, "kind", "")
        if kind == "subset_row":
            continue
        if kind in {"fleet_lower_bound", "fleet_upper_bound"}:
            continue
        return False
    return True


def _direct_label_diverse_harvest_soft_return_ready(
    *,
    completion_bound_enabled: bool,
    completion_bound_elapsed_soft_return_enabled: bool = True,
    unique_count: int,
    candidate_count: int | None = None,
    new_task_set_count: int = 0,
    max_returned: int,
    soft_min: int,
    soft_min_new_task_sets: int = 0,
    soft_after: float,
    soft_remaining: float,
    duplicate_saturation_after_time: float = 0.0,
    elapsed: float,
    remaining: float | None,
) -> bool:
    if int(soft_min) <= 0:
        return False
    unique_total = max(0, int(unique_count))
    candidate_total = max(unique_total, int(candidate_count) if candidate_count is not None else unique_total)
    soft_target = max(1, min(max(1, int(max_returned)), int(soft_min)))
    new_task_set_target = max(0, int(soft_min_new_task_sets))
    new_task_set_total = max(0, int(new_task_set_count))
    # If the final judge is only rediscovering physical variants of the same
    # few true-negative task sets, return those columns instead of burning the
    # remaining pricing budget chasing a diversity target it is unlikely to hit.
    duplicate_saturated = (
        bool(completion_bound_enabled)
        and unique_total >= min(4, soft_target)
        and candidate_total >= max(4 * soft_target, 8 * unique_total)
    )
    if unique_total < soft_target and not duplicate_saturated:
        return False
    new_task_set_gate_ready = new_task_set_target <= 0 or new_task_set_total >= new_task_set_target
    remaining_soft_ready = (
        float(soft_remaining) > 0.0
        and remaining is not None
        and float(remaining) <= float(soft_remaining)
    )
    # A positive new-task-set target is an explicit request to keep the final
    # judge from returning replacement-only batches.  Apply that gate to every
    # soft-return path, including the remaining-time escape hatch; otherwise
    # completion-bound pricing quietly becomes a replacement worker in the tail.
    remaining_soft_ready = bool(remaining_soft_ready and new_task_set_gate_ready)
    if bool(completion_bound_enabled) and not bool(completion_bound_elapsed_soft_return_enabled):
        # Completion-bound final probes have already paid the expensive bound
        # build/search setup cost.  Returning merely because elapsed time passed
        # a threshold recreates the long-tail loop with tiny column batches; only
        # use soft return here when the local pricing budget is nearly exhausted.
        return bool(remaining_soft_ready)
    duplicate_saturation_ready = (
        bool(new_task_set_gate_ready)
        and bool(duplicate_saturated)
        and float(duplicate_saturation_after_time) > 0.0
        and float(elapsed) >= float(duplicate_saturation_after_time)
    )
    elapsed_soft_ready = (
        bool(new_task_set_gate_ready)
        and float(soft_after) > 0.0
        and float(elapsed) >= float(soft_after)
    )
    return bool(duplicate_saturation_ready or elapsed_soft_ready or remaining_soft_ready)


def _direct_completion_positive_subset_future_reward_bound(
    mask: int,
    remaining_visit_capacity: int,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
    *,
    positive_cut_reward_bound: _PositiveSubsetCutRewardBound | None = None,
) -> float:
    """Upper-bound extra positive SRC reward reachable by future task visits.

    Subtracting this reward from a suffix lower bound can only make the bound
    smaller and therefore safer.  Small task sets use an exact mask DP cache;
    larger instances fall back to a row-wise upper bound to protect memory.
    """

    if int(remaining_visit_capacity) <= 0 or not cut_duals or not cuts:
        return 0.0
    if positive_cut_reward_bound is not None:
        return positive_cut_reward_bound.value(int(mask), int(remaining_visit_capacity))
    return _direct_completion_positive_subset_future_reward_bound_rowwise(
        int(mask),
        int(remaining_visit_capacity),
        cut_duals,
        cuts,
        cut_masks,
    )


def _direct_completion_positive_subset_future_reward_bound_rowwise(
    mask: int,
    remaining_visit_capacity: int,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
) -> float:
    current_mask = int(mask)
    capacity = max(0, int(remaining_visit_capacity))
    reward = 0.0
    for cut_index, cut in enumerate(cuts):
        dual = float(cut_duals.get(int(cut_index), 0.0))
        if dual <= 1.0e-12 or getattr(cut, "kind", "") != "subset_row" or int(cut_index) >= len(cut_masks):
            continue
        cut_mask = int(cut_masks[cut_index])
        if cut_mask <= 0:
            continue
        k = max(1, int(getattr(cut, "k", 2)))
        current_overlap = (current_mask & cut_mask).bit_count()
        additional_available = (cut_mask & ~current_mask).bit_count()
        additional_overlap = min(capacity, int(additional_available))
        current_coeff = int(current_overlap) // int(k)
        best_coeff = (int(current_overlap) + int(additional_overlap)) // int(k)
        if best_coeff > current_coeff:
            reward += float(dual) * float(best_coeff - current_coeff)
    return float(reward)


def _direct_completion_optimistic_cut_dual_value(
    mask: int,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
    cache: dict[int, float] | None = None,
) -> float:
    if int(mask) == 0 or not cut_duals or not cuts:
        return 0.0
    if cache is not None and int(mask) in cache:
        return float(cache[int(mask)])
    value = 0.0
    for cut_index, cut in enumerate(cuts):
        dual = float(cut_duals.get(int(cut_index), 0.0))
        if dual <= 1.0e-12:
            continue
        kind = getattr(cut, "kind", "")
        if kind in {"fleet_lower_bound", "fleet_upper_bound"}:
            value += dual
        elif kind == "subset_row" and int(cut_index) < len(cut_masks):
            # Realized positive SRC reward on the current mask.  Future reward
            # is handled separately by
            # _direct_completion_positive_subset_future_reward_bound().
            k = int(getattr(cut, "k", 2))
            overlap = (int(mask) & int(cut_masks[cut_index])).bit_count()
            value += dual * float(overlap // k)
    if cache is not None:
        cache[int(mask)] = float(value)
    return value


def _profile_cut_penalty_cached(
    mask: int,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
    *,
    enabled: bool,
    cache: dict[int, float] | None = None,
) -> float:
    if not enabled or not cut_duals or not cuts:
        return 0.0
    if cache is not None and int(mask) in cache:
        return float(cache[int(mask)])
    value = _profile_cut_penalty(int(mask), cut_duals, cuts, cut_masks, enabled=True)
    if cache is not None:
        cache[int(mask)] = float(value)
    return float(value)


def _profile_cut_penalty(
    mask: int,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
    *,
    enabled: bool,
) -> float:
    if not enabled or not cut_duals or not cuts:
        return 0.0
    value = 0.0
    for cut_index, cut in enumerate(cuts):
        if getattr(cut, "kind", "") != "subset_row":
            continue
        dual = float(cut_duals.get(int(cut_index), 0.0))
        if dual >= -1.0e-12 or cut_index >= len(cut_masks):
            continue
        k = int(getattr(cut, "k", 2))
        overlap = (int(mask) & int(cut_masks[cut_index])).bit_count()
        value += -dual * float(overlap // k)
    return value


def _journey_cut_dual_value(mask: int, cut_duals: dict[int, float], cuts: tuple[FutureCut, ...], cut_masks: tuple[int, ...]) -> float:
    if not cut_duals or not cuts:
        return 0.0
    value = 0.0
    for cut_index, cut in enumerate(cuts):
        kind = getattr(cut, "kind", "")
        if kind in {"fleet_lower_bound", "fleet_upper_bound"}:
            if int(mask) != 0:
                value += float(cut_duals.get(int(cut_index), 0.0))
            continue
        if kind != "subset_row":
            continue
        k = int(getattr(cut, "k", 2))
        if cut_index >= len(cut_masks):
            continue
        overlap = (int(mask) & int(cut_masks[cut_index])).bit_count()
        value += float(cut_duals.get(int(cut_index), 0.0)) * float(overlap // k)
    return value


def _journey_pricing_cut_supported(cut: FutureCut) -> bool:
    return getattr(cut, "kind", "") in {"subset_row", "fleet_lower_bound", "fleet_upper_bound"}


def _cut_masks(data: FutureData, cuts: tuple[FutureCut, ...]) -> tuple[int, ...]:
    task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
    return _cut_masks_from_task_bits(cuts, task_to_bit)


def _cut_masks_from_task_bits(cuts: tuple[FutureCut, ...], task_to_bit: dict[int, int]) -> tuple[int, ...]:
    masks: list[int] = []
    for cut in cuts:
        mask = 0
        if getattr(cut, "kind", "") == "subset_row":
            for task in getattr(cut, "tasks", tuple()):
                if int(task) in task_to_bit:
                    mask |= 1 << task_to_bit[int(task)]
        masks.append(mask)
    return tuple(masks)


def _add_profile_label(
    store: dict[int, list[_JourneyLabel]],
    mask: int,
    label: _JourneyLabel,
    *,
    dp_stats: dict[str, int] | None = None,
    max_labels_per_mask: int = 0,
    skip_precheck: bool = False,
) -> bool:
    labels = store.setdefault(int(mask), [])
    if not bool(skip_precheck):
        for old in labels:
            if _dominates_journey_label(old, label):
                return False
    labels[:] = [
        old
        for old in labels
        if not _dominates_journey_label(label, old)
    ]
    labels.append(label)
    return _cap_profile_label_bucket(labels, label, max_labels_per_mask, dp_stats)


def _add_profile_label_cross_count(
    labels_by_count: list[dict[int, list[_JourneyLabel]]],
    count: int,
    mask: int,
    label: _JourneyLabel,
    dp_stats: dict[str, int] | None,
    *,
    max_labels_per_mask: int = 0,
    skip_precheck: bool = False,
) -> bool:
    mask = int(mask)
    count = int(count)
    if not bool(skip_precheck):
        for old_count in range(0, count + 1):
            for old in labels_by_count[old_count].get(mask, []):
                if _dominates_journey_label(old, label):
                    if dp_stats is not None:
                        dp_stats["cross_count_pruned_labels"] = int(dp_stats.get("cross_count_pruned_labels", 0)) + 1
                    return False

    removed = 0
    for old_count in range(count, len(labels_by_count)):
        labels = labels_by_count[old_count].get(mask)
        if not labels:
            continue
        survivors: list[_JourneyLabel] = []
        for old in labels:
            if _dominates_journey_label(label, old):
                removed += 1
                continue
            survivors.append(old)
        if survivors:
            labels_by_count[old_count][mask] = survivors
        else:
            labels_by_count[old_count].pop(mask, None)
    labels_by_count[count].setdefault(mask, []).append(label)
    if removed and dp_stats is not None:
        dp_stats["cross_count_pruned_labels"] = int(dp_stats.get("cross_count_pruned_labels", 0)) + int(removed)
    return _cap_profile_label_bucket(
        labels_by_count[count].setdefault(mask, []),
        label,
        max_labels_per_mask,
        dp_stats,
    )


def _profile_label_bucket_dominated_by_values(
    store: dict[int, list[_JourneyLabel]],
    mask: int,
    end_time: float,
    value: float,
) -> bool:
    for old in store.get(int(mask), []):
        if (
            float(old.end_time) <= float(end_time) + 1.0e-9
            and float(old.value) <= float(value) + 1.0e-9
        ):
            return True
    return False


def _profile_label_cross_count_dominated_by_values(
    labels_by_count: list[dict[int, list[_JourneyLabel]]],
    count: int,
    mask: int,
    end_time: float,
    value: float,
    dp_stats: dict[str, int] | None,
) -> bool:
    mask = int(mask)
    for old_count in range(0, int(count) + 1):
        for old in labels_by_count[old_count].get(mask, []):
            if (
                float(old.end_time) <= float(end_time) + 1.0e-9
                and float(old.value) <= float(value) + 1.0e-9
            ):
                if dp_stats is not None:
                    dp_stats["cross_count_pruned_labels"] = int(dp_stats.get("cross_count_pruned_labels", 0)) + 1
                return True
    return False


def _cap_profile_label_bucket(
    labels: list[_JourneyLabel],
    added_label: _JourneyLabel,
    max_labels_per_mask: int,
    dp_stats: dict[str, int] | None,
) -> bool:
    """Keep a bounded worker frontier for one profile-DP mask bucket.

    This is deliberately a worker-only truncation.  It reduces repeated
    profile-DP scans in degenerate tails, but it is not used as a certificate:
    a no-column result from profile DP remains `LOCAL_NO_COLUMN_UNCERTIFIED`
    and must still be checked by the true-dual direct-label final judge.
    """

    cap = max(0, int(max_labels_per_mask))
    if cap <= 0 or len(labels) <= cap:
        return True
    ranked = sorted(
        labels,
        key=lambda old: (
            round(float(old.value), 9),
            round(float(old.end_time), 9),
            len(old.selected),
            old.selected,
        ),
    )
    survivors = ranked[:cap]
    removed = len(labels) - len(survivors)
    labels[:] = survivors
    if removed > 0 and dp_stats is not None:
        dp_stats["label_cap_pruned"] = int(dp_stats.get("label_cap_pruned", 0)) + int(removed)
    return any(old is added_label for old in labels)


def _dominates_journey_label(left: _JourneyLabel, right: _JourneyLabel) -> bool:
    return bool(
        float(left.end_time) <= float(right.end_time) + 1.0e-9
        and float(left.value) <= float(right.value) + 1.0e-9
    )


def _instantiate_profile_journey(
    data: FutureData,
    profiles: list[_SortieProfile],
    selected: tuple[tuple[int, float], ...],
    config: JourneyPricingConfig,
) -> list[TimedTrip]:
    trips: list[TimedTrip] = []
    for profile_index, start in selected:
        profile = profiles[int(profile_index)]
        trip = evaluate_timed_trip(
            data,
            profile.sequence,
            float(start),
            time_bucket_size=float(config.time_bucket_size),
            arc_options=profile.arc_options,
            include_physical_paths=False,
        )
        if trip is None:
            return []
        trips.append(trip)
    trips.sort(key=lambda trip: (trip.start_time, trip.end_time, trip.tasks, trip.arc_option_ids))
    return trips


def _instantiate_profile_journey_candidates(
    data: FutureData,
    profiles: list[_SortieProfile],
    selected_candidates: list[tuple[tuple[tuple[int, float], ...], float]],
    config: JourneyPricingConfig,
    *,
    eps: float,
    forbidden_journey_signatures: set[tuple] | frozenset[tuple] | None = None,
    dominant_task_set_costs: dict[frozenset[int], float] | None = None,
    max_journeys: int | None = None,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
    duals: JourneyDuals | None = None,
    cuts: tuple[FutureCut, ...] = tuple(),
    dp_stats: dict[str, Any] | None = None,
) -> tuple[list[JourneyColumn], int, int]:
    journeys: list[JourneyColumn] = []
    seen: set[tuple] = set()
    seen_task_sets: set[frozenset[int]] = set()
    forbidden = forbidden_journey_signatures or set()
    existing_filtered = 0
    weak_negative_filtered = 0
    unmaterialized_candidates = 0
    weak_materialized_count = 0
    weak_best_rough: float | None = None
    weak_best_true: float | None = None
    weak_max_gap: float | None = None
    weak_max_gap_mask: int | None = None
    add_threshold = max(float(eps), float(config.min_add_reduced_cost))

    def selected_mask(selected: tuple[tuple[int, float], ...]) -> int:
        mask = 0
        for profile_index, _start in selected:
            index = int(profile_index)
            if 0 <= index < len(profiles):
                mask |= int(getattr(profiles[index], "mask", 0))
        return int(mask)

    def record_weak_materialized(
        selected: tuple[tuple[int, float], ...],
        rough_objective: float,
        true_objective: float,
    ) -> None:
        nonlocal weak_materialized_count
        nonlocal weak_best_rough
        nonlocal weak_best_true
        nonlocal weak_max_gap
        nonlocal weak_max_gap_mask
        weak_materialized_count += 1
        rough = float(rough_objective)
        true_rc = float(true_objective)
        if weak_best_rough is None or rough < float(weak_best_rough):
            weak_best_rough = rough
        if weak_best_true is None or true_rc < float(weak_best_true):
            weak_best_true = true_rc
        gap = true_rc - rough
        if weak_max_gap is None or gap > float(weak_max_gap):
            weak_max_gap = gap
            weak_max_gap_mask = selected_mask(selected)

    def flush_stats() -> None:
        if dp_stats is None:
            return
        if unmaterialized_candidates > 0:
            dp_stats["profile_selected_unmaterialized_candidate_count"] = int(
                dp_stats.get("profile_selected_unmaterialized_candidate_count", 0)
            ) + int(unmaterialized_candidates)
        if weak_materialized_count > 0:
            dp_stats["profile_weak_filtered_materialized_count"] = int(
                dp_stats.get("profile_weak_filtered_materialized_count", 0)
            ) + int(weak_materialized_count)
            old_rough = dp_stats.get("profile_weak_filtered_best_rough_rc")
            if old_rough is None or (weak_best_rough is not None and float(weak_best_rough) < float(old_rough)):
                dp_stats["profile_weak_filtered_best_rough_rc"] = weak_best_rough
            old_true = dp_stats.get("profile_weak_filtered_best_true_rc")
            if old_true is None or (weak_best_true is not None and float(weak_best_true) < float(old_true)):
                dp_stats["profile_weak_filtered_best_true_rc"] = weak_best_true
            old_gap = dp_stats.get("profile_weak_filtered_max_true_minus_rough")
            if old_gap is None or (weak_max_gap is not None and float(weak_max_gap) > float(old_gap)):
                dp_stats["profile_weak_filtered_max_true_minus_rough"] = weak_max_gap
                dp_stats["profile_weak_filtered_max_true_minus_rough_mask"] = weak_max_gap_mask

    for selected, objective in selected_candidates:
        if objective >= -float(eps) and duals is None:
            continue
        if objective >= -add_threshold and duals is None:
            weak_negative_filtered += 1
            continue
        trips = _instantiate_profile_journey(data, profiles, selected, config)
        journey = make_journey(data, trips)
        if journey is None:
            unmaterialized_candidates += 1
            continue
        if journey.signature in seen:
            continue
        true_objective = float(objective)
        if duals is not None:
            true_objective = float(manual_journey_reduced_cost(journey, duals, cuts))
        if true_objective >= -float(eps):
            weak_negative_filtered += 1
            record_weak_materialized(selected, float(objective), true_objective)
            continue
        if true_objective >= -add_threshold:
            weak_negative_filtered += 1
            record_weak_materialized(selected, float(objective), true_objective)
            continue
        if not _journey_task_set_branch_allowed(journey.task_set, branch_constraints):
            existing_filtered += 1
            continue
        task_set_key = frozenset(int(task) for task in journey.task_set)
        if task_set_key in seen_task_sets:
            existing_filtered += 1
            continue
        if journey.signature in forbidden:
            existing_filtered += 1
            continue
        if _journey_task_set_cost_dominated(journey, dominant_task_set_costs):
            existing_filtered += 1
            continue
        seen.add(journey.signature)
        seen_task_sets.add(task_set_key)
        journeys.append(journey)
        if max_journeys is not None and len(journeys) >= int(max_journeys):
            break
    flush_stats()
    return journeys, existing_filtered, weak_negative_filtered


def _journey_task_set_branch_allowed(task_set: frozenset[int] | set[int], constraints: tuple[BranchConstraint, ...]) -> bool:
    tasks = {int(task) for task in task_set}
    for constraint in constraints:
        if constraint.task_j is None:
            return False
        left = int(constraint.task_i) in tasks
        right = int(constraint.task_j) in tasks
        if constraint.kind == "separate_vehicle" and left and right:
            return False
        if constraint.kind == "same_vehicle" and left != right:
            return False
        if constraint.kind not in {"same_vehicle", "separate_vehicle"}:
            return False
    return True


def _solve_best_journey_selection_dp(
    data: FutureData,
    trips: list[TimedTrip],
    duals: FutureDuals,
    *,
    base_reduced_cost: float,
    max_states: int,
) -> tuple[list[TimedTrip], float | None, str]:
    task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
    if len(task_to_bit) > 62:
        return [], None, "INCOMPLETE"
    prepared: list[tuple[float, TimedTrip, int, float]] = []
    vehicle = int(data.vehicles[0])
    for trip in trips:
        mask = 0
        for task in trip.task_set:
            mask |= 1 << task_to_bit[int(task)]
        contribution = manual_reduced_cost(trip, vehicle, duals, tuple(), phase="phase2")
        prepared.append((float(trip.end_time), trip, mask, float(contribution)))
    prepared.sort(key=lambda item: (item[0], item[1].start_time, item[3], item[1].signature))

    states: dict[tuple[int, int], tuple[float, tuple[int, ...]]] = {(0, 0): (0.0, tuple())}
    snapshot_ends = [float("-inf")]
    snapshots: list[dict[tuple[int, int], tuple[float, tuple[int, ...]]]] = [dict(states)]
    index_by_signature = {trip.signature: index for index, (_end, trip, _mask, _contribution) in enumerate(prepared)}

    position = 0
    while position < len(prepared):
        end_time = prepared[position][0]
        group: list[tuple[TimedTrip, int, float]] = []
        while position < len(prepared) and abs(prepared[position][0] - end_time) <= 1.0e-9:
            _end, trip, mask, contribution = prepared[position]
            group.append((trip, mask, contribution))
            position += 1
        updates: dict[tuple[int, int], tuple[float, tuple[int, ...]]] = {}
        for trip, trip_mask, contribution in group:
            pred = bisect.bisect_right(snapshot_ends, float(trip.start_time) + 1.0e-9) - 1
            base_states = snapshots[max(0, pred)]
            trip_index = index_by_signature[trip.signature]
            for (mask, count), (value, selected) in base_states.items():
                if count >= int(data.sortie_limit):
                    continue
                if mask & trip_mask:
                    continue
                new_key = (mask | trip_mask, count + 1)
                new_value = value + contribution
                old = updates.get(new_key)
                if old is None or new_value < old[0] - 1.0e-9:
                    updates[new_key] = (new_value, (*selected, trip_index))
        for key, candidate in updates.items():
            old = states.get(key)
            if old is None or candidate[0] < old[0] - 1.0e-9:
                states[key] = candidate
        if max_states > 0 and len(states) > int(max_states):
            return [], None, "INCOMPLETE"
        snapshot_ends.append(float(end_time))
        snapshots.append(dict(states))

    best_value: float | None = None
    best_selected: tuple[int, ...] = tuple()
    for (mask, count), (value, selected) in states.items():
        if mask == 0 or count == 0:
            continue
        objective = float(base_reduced_cost) + float(value)
        if best_value is None or objective < best_value - 1.0e-9:
            best_value = objective
            best_selected = selected
    if best_value is None:
        return [], None, "OPTIMAL"
    selected_trips = [prepared[index][1] for index in best_selected]
    selected_trips.sort(key=lambda trip: (trip.start_time, trip.end_time, trip.tasks, trip.arc_option_ids))
    return selected_trips, best_value, "OPTIMAL"


def _solve_best_journey_selection(
    data: FutureData,
    trips: list[TimedTrip],
    duals: FutureDuals,
    *,
    base_reduced_cost: float,
    time_limit: float,
) -> tuple[list[TimedTrip], float | None, str]:
    from pyscipopt import Model, quicksum

    model = Model(f"bpc_future_journey_pricing_{data.name}")
    _try_set_param(model, "display/verblevel", 0)
    _try_set_param(model, "parallel/maxnthreads", 1)
    if time_limit > 0.0:
        _try_set_param(model, "limits/time", float(time_limit))
    z = {
        index: model.addVar(
            vtype="B",
            obj=float(manual_reduced_cost(trip, int(data.vehicles[0]), duals, tuple(), phase="phase2")),
            name=f"z_trip[{index}]",
        )
        for index, trip in enumerate(trips)
    }
    for task in data.tasks:
        terms = [var for index, var in z.items() if int(task) in trips[index].task_set]
        if terms:
            model.addCons(quicksum(terms) <= 1.0, name=f"task_once[{task}]")
    model.addCons(quicksum(z.values()) >= 1.0, name="nonempty_journey")
    model.addCons(quicksum(z.values()) <= float(data.sortie_limit), name="sortie_limit")
    for point_index, point in enumerate(_interval_clique_points(trips)):
        terms = [
            var
            for index, var in z.items()
            if trips[index].start_time <= point + 1.0e-9 and point < trips[index].end_time - 1.0e-9
        ]
        if len(terms) > 1:
            model.addCons(quicksum(terms) <= 1.0, name=f"time_clique[{point_index}]")
    model.addVar(vtype="C", lb=1.0, ub=1.0, obj=float(base_reduced_cost), name="journey_base")
    model.optimize()
    status = _status_name(model.getStatus())
    if model.getNSols() <= 0:
        return [], None, status
    sol = model.getBestSol()
    selected = [
        trips[index]
        for index, var in z.items()
        if float(model.getSolVal(sol, var)) > 0.5
    ]
    selected.sort(key=lambda trip: (trip.start_time, trip.end_time, trip.tasks, trip.arc_option_ids))
    return selected, float(model.getSolObjVal(sol)), status


def _interval_clique_points(trips: list[TimedTrip]) -> tuple[float, ...]:
    endpoints = sorted(
        {
            round(float(trip.start_time), 6)
            for trip in trips
        }
        | {
            round(float(trip.end_time), 6)
            for trip in trips
        }
    )
    points: set[float] = set()
    for left, right in zip(endpoints[:-1], endpoints[1:]):
        if right > left + 1.0e-9:
            points.add(round((left + right) / 2.0, 6))
    return tuple(sorted(points))


def _try_set_param(model: Any, name: str, value: Any) -> None:
    try:
        model.setParam(name, value)
    except Exception:
        pass


def _status_name(status: Any) -> str:
    text = str(status).lower()
    mapping = {
        "optimal": "OPTIMAL",
        "infeasible": "INFEASIBLE",
        "unbounded": "UNBOUNDED",
        "inforunbd": "INF_OR_UNBD",
        "timelimit": "TIME_LIMIT",
    }
    return mapping.get(text, text.upper())

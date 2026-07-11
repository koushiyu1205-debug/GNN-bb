"""B1 true-dual fixed-graph pricing final judge."""

from __future__ import annotations

from dataclasses import dataclass
import os
from time import perf_counter

from lunar_ice_bpc.exact.bpc.core.column_pool import BpcColumn, ColumnPool
from lunar_ice_bpc.exact.bpc.core.column_signature import column_signature_from_journey
from lunar_ice_bpc.exact.bpc.core.master_column_view import MasterColumnView
from lunar_ice_bpc.exact.bpc.master.reduced_cost import ReducedCostContext
from lunar_ice_bpc.exact.bpc.pricing.labeling_pricer import (
    CERTIFYING_PROOF_KINDS,
    EXACT_ELEMENTARY_MODE,
    LabelingPricingConfig,
    PROOF_KIND_EXHAUSTIVE_FOUND_NEGATIVE,
    PROOF_KIND_EXHAUSTIVE_INCOMPLETE,
    PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE,
    run_bpc_labeling_pricer,
)
from lunar_ice_bpc.exact.bpc.pricing.status import PricingState
from lunar_ice_bpc.exact.core.branching import BranchContext, branch_context_from_payload, journey_satisfies_branch_context
from lunar_ice_bpc.exact.core.cuts import CutContext, cut_coefficients_for_journey, cut_context_from_payload
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import JourneyColumn
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals, manual_journey_reduced_cost
from lunar_ice_bpc.exact.pricing.journey_pricing import (
    DirectPricingCache,
    price_direct_journey_columns_incremental,
    price_exhaustive_direct_journey_columns,
)
from lunar_ice_bpc.exact.solver.journey_driver import (
    DirectBaselineTimeLimitExceeded,
    enumerate_direct_journey_columns,
)
from lunar_ice_bpc.exact.solver.gurobi_compact import solve_highs_compact_single_journey_pricing


TASK_SUBSET_REPRESENTATIVE_UNIVERSE_SEMANTICS = "best_task_subset_representative_fixed_graph_columns"
COMPACT_SINGLE_JOURNEY_PRICING_MIN_TASKS = 25
LABELING_FINAL_JUDGE_ENV = "LUNAR_ICE_LABELING_FINAL_JUDGE"
LABELING_FINAL_JUDGE_MAX_TASKS_ENV = "LUNAR_ICE_LABELING_FINAL_JUDGE_MAX_TASKS"
LABELING_FINAL_JUDGE_EXACT_HARVEST_TARGET_ENV = (
    "LUNAR_ICE_LABELING_FINAL_JUDGE_EXACT_HARVEST_TARGET"
)
LABELING_FINAL_JUDGE_AUTO_VALUES = {"auto", "adaptive"}
COMPACT_SINGLE_JOURNEY_NEGATIVE_SEARCH_CAP_SEC = 60.0
COMPACT_SINGLE_JOURNEY_NEGATIVE_BATCH_TARGET = 5
COMPACT_SINGLE_JOURNEY_OPTIMIZATION_HARVEST_TARGET = 5
COMPACT_SINGLE_JOURNEY_NEGATIVE_SEARCH_CAP_ENV = "LUNAR_ICE_COMPACT_NEGATIVE_SEARCH_CAP_SEC"
COMPACT_SINGLE_JOURNEY_NEGATIVE_BATCH_TARGET_ENV = "LUNAR_ICE_COMPACT_NEGATIVE_BATCH_TARGET"
COMPACT_SINGLE_JOURNEY_NEGATIVE_NO_GOOD_SCOPE_ENV = "LUNAR_ICE_COMPACT_NEGATIVE_NO_GOOD_SCOPE"
COMPACT_SINGLE_JOURNEY_OPTIMIZATION_HARVEST_TARGET_ENV = (
    "LUNAR_ICE_COMPACT_OPTIMIZATION_HARVEST_TARGET"
)
COMPACT_SINGLE_JOURNEY_OPTIMIZATION_HARVEST_NO_GOOD_SCOPE_ENV = (
    "LUNAR_ICE_COMPACT_OPTIMIZATION_HARVEST_NO_GOOD_SCOPE"
)
COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PROFILE_ENV = "LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE"
COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_ENV = "LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE"
COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_THREADS_ENV = "LUNAR_ICE_COMPACT_FINAL_JUDGE_THREADS"
COMPACT_SINGLE_JOURNEY_PROOF_MTZ_CONNECTIVITY_ENV = (
    "LUNAR_ICE_COMPACT_PROOF_MTZ_CONNECTIVITY"
)
COMPACT_SINGLE_JOURNEY_NEGATIVE_SEARCH_MIP_START_ENV = (
    "LUNAR_ICE_COMPACT_NEGATIVE_SEARCH_MIP_START"
)
COMPACT_SINGLE_JOURNEY_MIP_START_ZERO_FILL_INTEGERS_ENV = (
    "LUNAR_ICE_COMPACT_MIP_START_ZERO_FILL_INTEGERS"
)
COMPACT_SINGLE_JOURNEY_MIP_START_INACTIVE_TAIL_TIME_ENV = (
    "LUNAR_ICE_COMPACT_MIP_START_INACTIVE_TAIL_TIME"
)
COMPACT_SINGLE_JOURNEY_MIP_START_INACTIVE_TAIL_TIME_MODE_ENV = (
    "LUNAR_ICE_COMPACT_MIP_START_INACTIVE_TAIL_TIME_MODE"
)
COMPACT_SINGLE_JOURNEY_MTZ_ENDPOINT_ORDER_CUTS_ENV = (
    "LUNAR_ICE_COMPACT_MTZ_ENDPOINT_ORDER_CUTS"
)
COMPACT_SINGLE_JOURNEY_PAIR_ADJACENCY_CUTS_ENV = (
    "LUNAR_ICE_COMPACT_PAIR_ADJACENCY_CUTS"
)
COMPACT_SINGLE_JOURNEY_RESOURCE_ARC_PRUNING_ENV = "LUNAR_ICE_COMPACT_RESOURCE_ARC_PRUNING"
COMPACT_SINGLE_JOURNEY_SLOT_ARC_SUPPORT_PRUNING_ENV = (
    "LUNAR_ICE_COMPACT_SLOT_ARC_SUPPORT_PRUNING"
)
COMPACT_SINGLE_JOURNEY_SLOT_SEQUENCE_CAPACITY_ARC_PRUNING_ENV = (
    "LUNAR_ICE_COMPACT_SLOT_SEQUENCE_CAPACITY_ARC_PRUNING"
)
COMPACT_SINGLE_JOURNEY_DUAL_TASK_SLOT_FULL_SPACE_LB_ENV = (
    "LUNAR_ICE_COMPACT_DUAL_TASK_SLOT_FULL_SPACE_LB"
)
COMPACT_SINGLE_JOURNEY_DUAL_TASK_SLOT_FULL_SPACE_LB_TIME_LIMIT_ENV = (
    "LUNAR_ICE_COMPACT_DUAL_TASK_SLOT_FULL_SPACE_LB_TIME_LIMIT_SEC"
)
COMPACT_SINGLE_JOURNEY_DUAL_TASK_SLOT_FULL_SPACE_LB_EARLY_STOP_ENV = (
    "LUNAR_ICE_COMPACT_DUAL_TASK_SLOT_FULL_SPACE_LB_EARLY_STOP"
)
COMPACT_SINGLE_JOURNEY_RECHARGE_AWARE_SLOT_BOUND_ENV = (
    "LUNAR_ICE_COMPACT_RECHARGE_AWARE_SLOT_BOUND"
)
COMPACT_SINGLE_JOURNEY_OBJECTIVE_BOUND_CUTOFF_ENV = (
    "LUNAR_ICE_COMPACT_OBJECTIVE_BOUND_NO_NEGATIVE_CUTOFF"
)
COMPACT_SINGLE_JOURNEY_ZERO_CAPACITY_SLOT_TRUNCATION_ENV = (
    "LUNAR_ICE_COMPACT_ZERO_CAPACITY_SLOT_TRUNCATION"
)
COMPACT_SINGLE_JOURNEY_SLOT_SEQUENCE_CAPACITY_LIVE_BOUND_ENV = (
    "LUNAR_ICE_COMPACT_SLOT_SEQUENCE_CAPACITY_LIVE_BOUND"
)
COMPACT_SINGLE_JOURNEY_TIGHT_SERVICE_START_BOUNDS_ENV = (
    "LUNAR_ICE_COMPACT_TIGHT_SERVICE_START_BOUNDS"
)
COMPACT_SINGLE_JOURNEY_TIGHT_TIME_ARC_BIG_M_ENV = (
    "LUNAR_ICE_COMPACT_TIGHT_TIME_ARC_BIG_M"
)
COMPACT_SINGLE_JOURNEY_SLOT_SERVICE_START_Y_LB_ENV = (
    "LUNAR_ICE_COMPACT_SLOT_SERVICE_START_Y_LB"
)
COMPACT_SINGLE_JOURNEY_SERVICE_START_DEPOT_TRAVEL_LB_ENV = "LUNAR_ICE_COMPACT_SERVICE_START_DEPOT_TRAVEL_LB"
COMPACT_SINGLE_JOURNEY_TASK_TO_DEPOT_RETURN_TRAVEL_LB_ENV = (
    "LUNAR_ICE_COMPACT_TASK_TO_DEPOT_RETURN_TRAVEL_LB"
)
COMPACT_SINGLE_JOURNEY_PAIR_ROUTE_DURATION_LB_ENV = "LUNAR_ICE_COMPACT_PAIR_ROUTE_DURATION_LB"
COMPACT_SINGLE_JOURNEY_PAIR_WEIGHTED_COMPLETION_LB_ENV = (
    "LUNAR_ICE_COMPACT_PAIR_WEIGHTED_COMPLETION_LB"
)
COMPACT_SINGLE_JOURNEY_SORTIE_SLOT_POSITION_BOUNDS_ENV = (
    "LUNAR_ICE_COMPACT_SORTIE_SLOT_POSITION_BOUNDS"
)
COMPACT_SINGLE_JOURNEY_DEMAND_COVER_CUT_ENV = "LUNAR_ICE_COMPACT_DEMAND_COVER_CUT"
COMPACT_SINGLE_JOURNEY_SINGLE_TASK_ENERGY_LB_ENV = "LUNAR_ICE_COMPACT_SINGLE_TASK_ENERGY_LB"
COMPACT_SINGLE_JOURNEY_SINGLE_TASK_SHADOW_LB_ENV = "LUNAR_ICE_COMPACT_SINGLE_TASK_SHADOW_LB"
COMPACT_SINGLE_JOURNEY_PAIR_ENERGY_LB_ENV = "LUNAR_ICE_COMPACT_PAIR_ENERGY_LB"
COMPACT_SINGLE_JOURNEY_PAIR_SHADOW_LB_ENV = "LUNAR_ICE_COMPACT_PAIR_SHADOW_LB"
COMPACT_SINGLE_JOURNEY_PAIR_ENERGY_INFEASIBLE_CUT_ENV = (
    "LUNAR_ICE_COMPACT_PAIR_ENERGY_INFEASIBLE_CUT"
)
COMPACT_SINGLE_JOURNEY_PAIR_TIME_WINDOW_INFEASIBLE_CUT_ENV = (
    "LUNAR_ICE_COMPACT_PAIR_TIME_WINDOW_INFEASIBLE_CUT"
)
COMPACT_SINGLE_JOURNEY_PAIR_TIME_WINDOW_PRECEDENCE_CUT_ENV = (
    "LUNAR_ICE_COMPACT_PAIR_TIME_WINDOW_PRECEDENCE_CUT"
)
COMPACT_SINGLE_JOURNEY_TRIPLE_TIME_WINDOW_INFEASIBLE_CUT_ENV = (
    "LUNAR_ICE_COMPACT_TRIPLE_TIME_WINDOW_INFEASIBLE_CUT"
)
COMPACT_SINGLE_JOURNEY_QUAD_TIME_WINDOW_INFEASIBLE_CUT_ENV = (
    "LUNAR_ICE_COMPACT_QUAD_TIME_WINDOW_INFEASIBLE_CUT"
)
COMPACT_SINGLE_JOURNEY_PAIR_SHADOW_INFEASIBLE_CUT_ENV = (
    "LUNAR_ICE_COMPACT_PAIR_SHADOW_INFEASIBLE_CUT"
)
COMPACT_SINGLE_JOURNEY_TRIPLE_SHADOW_INFEASIBLE_CUT_ENV = (
    "LUNAR_ICE_COMPACT_TRIPLE_SHADOW_INFEASIBLE_CUT"
)
COMPACT_SINGLE_JOURNEY_TRIPLE_ENERGY_INFEASIBLE_CUT_ENV = (
    "LUNAR_ICE_COMPACT_TRIPLE_ENERGY_INFEASIBLE_CUT"
)
COMPACT_SINGLE_JOURNEY_TASK_SLOT_PAIR_CONFLICT_CAPACITY_BOUND_ENV = (
    "LUNAR_ICE_COMPACT_TASK_SLOT_PAIR_CONFLICT_CAPACITY_BOUND"
)
COMPACT_SINGLE_JOURNEY_ROUTE_TEMPLATE_PRE_HARVEST_ENV = (
    "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST"
)
COMPACT_SINGLE_JOURNEY_ROUTE_TEMPLATE_PRE_HARVEST_TIME_CAP_ENV = (
    "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_TIME_CAP_SEC"
)
COMPACT_SINGLE_JOURNEY_ROUTE_TEMPLATE_PRE_HARVEST_MAX_DIRECT_TASKS_ENV = (
    "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_MAX_DIRECT_TASKS"
)
COMPACT_SINGLE_JOURNEY_ROUTE_TEMPLATE_PRE_HARVEST_MAX_ACTIVE_SEEDS_ENV = (
    "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_MAX_ACTIVE_SEEDS"
)
COMPACT_SINGLE_JOURNEY_ROUTE_TEMPLATE_PRE_HARVEST_NEIGHBORHOOD_ENV = (
    "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_NEIGHBORHOOD"
)
COMPACT_SINGLE_JOURNEY_ROUTE_TEMPLATE_PRE_HARVEST_MAX_NEIGHBORHOOD_SEEDS_ENV = (
    "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_MAX_NEIGHBORHOOD_SEEDS"
)
COMPACT_SINGLE_JOURNEY_ROUTE_TEMPLATE_PRE_HARVEST_MAX_CANDIDATE_SETS_ENV = (
    "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_MAX_CANDIDATE_SETS"
)
COMPACT_SINGLE_JOURNEY_ROUTE_TEMPLATE_PRE_HARVEST_TARGET = 5
COMPACT_SINGLE_JOURNEY_ROUTE_TEMPLATE_PRE_HARVEST_TARGET_ENV = (
    "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_TARGET"
)
COMPACT_SINGLE_JOURNEY_ROUTE_TEMPLATE_PRE_HARVEST_FALLBACK_ENV = (
    "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_FALLBACK"
)
COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_DEFAULT = "harvest_then_proof"
COMPACT_SINGLE_JOURNEY_NEGATIVE_SEARCH_MTZ_CONNECTIVITY = False
COMPACT_SINGLE_JOURNEY_PROOF_MTZ_CONNECTIVITY = True
COMPACT_SINGLE_JOURNEY_B4V2_MTZ_ENDPOINT_ORDER_CUTS = False
COMPACT_SINGLE_JOURNEY_B4V2_PAIR_ADJACENCY_CUTS = False
COMPACT_SINGLE_JOURNEY_B4V2_LATEST_SERVICE_START_SLOT_BOUND = True
COMPACT_SINGLE_JOURNEY_B4V2_TIME_WINDOW_ARC_PRUNING = False
COMPACT_SINGLE_JOURNEY_B4V2_SLOT_TASK_TIME_PRUNING = False
COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PROFILES = {
    "B4V2": {
        "name": "B4V2",
        "formulation_profile": "B4V2_latest_start_only",
        "negative_mtz_connectivity": COMPACT_SINGLE_JOURNEY_NEGATIVE_SEARCH_MTZ_CONNECTIVITY,
        "proof_mtz_connectivity": COMPACT_SINGLE_JOURNEY_PROOF_MTZ_CONNECTIVITY,
        "mtz_endpoint_order_cuts": COMPACT_SINGLE_JOURNEY_B4V2_MTZ_ENDPOINT_ORDER_CUTS,
        "pair_adjacency_cuts": COMPACT_SINGLE_JOURNEY_B4V2_PAIR_ADJACENCY_CUTS,
        "latest_service_start_slot_bound": COMPACT_SINGLE_JOURNEY_B4V2_LATEST_SERVICE_START_SLOT_BOUND,
        "time_window_arc_pruning": COMPACT_SINGLE_JOURNEY_B4V2_TIME_WINDOW_ARC_PRUNING,
        "resource_arc_pruning": False,
        "slot_task_time_pruning": COMPACT_SINGLE_JOURNEY_B4V2_SLOT_TASK_TIME_PRUNING,
        "slot_arc_support_pruning": False,
        "mip_start_from_column_pool": False,
        "official_default": True,
    },
    "V4": {
        "name": "V4",
        "formulation_profile": "B4V4_endpoint_pair_latest_start_time_window",
        "negative_mtz_connectivity": True,
        "proof_mtz_connectivity": True,
        "mtz_endpoint_order_cuts": True,
        "pair_adjacency_cuts": True,
        "latest_service_start_slot_bound": True,
        "time_window_arc_pruning": True,
        "resource_arc_pruning": True,
        "slot_task_time_pruning": True,
        "slot_arc_support_pruning": False,
        "mip_start_from_column_pool": True,
        "official_default": False,
    },
    "V4S": {
        "name": "V4S",
        "formulation_profile": "B4V4_strengthened_pair_weighted_final_tail",
        "negative_mtz_connectivity": True,
        "proof_mtz_connectivity": True,
        "mtz_endpoint_order_cuts": False,
        "pair_adjacency_cuts": False,
        "latest_service_start_slot_bound": True,
        "time_window_arc_pruning": True,
        "resource_arc_pruning": True,
        "slot_task_time_pruning": True,
        "slot_arc_support_pruning": False,
        "mip_start_from_column_pool": True,
        "sortie_slot_position_bounds": True,
        "pair_weighted_completion_lb": True,
        "pair_energy_infeasible_cut": True,
        "pair_time_window_infeasible_cut": True,
        "pair_shadow_infeasible_cut": True,
        "recharge_aware_slot_bound": False,
        "official_default": False,
    },
    "V4SR": {
        "name": "V4SR",
        "formulation_profile": "B4V4_strengthened_pair_weighted_recharge_slot_bound",
        "negative_mtz_connectivity": True,
        "proof_mtz_connectivity": True,
        "mtz_endpoint_order_cuts": False,
        "pair_adjacency_cuts": False,
        "latest_service_start_slot_bound": True,
        "time_window_arc_pruning": True,
        "resource_arc_pruning": True,
        "slot_task_time_pruning": True,
        "slot_arc_support_pruning": False,
        "mip_start_from_column_pool": True,
        "sortie_slot_position_bounds": True,
        "pair_weighted_completion_lb": True,
        "pair_energy_infeasible_cut": True,
        "pair_time_window_infeasible_cut": True,
        "pair_shadow_infeasible_cut": True,
        "recharge_aware_slot_bound": True,
        "official_default": False,
    },
    "V4SC": {
        "name": "V4SC",
        "formulation_profile": "B4V4_strengthened_pair_weighted_objective_bound_cutoff",
        "negative_mtz_connectivity": True,
        "proof_mtz_connectivity": True,
        "mtz_endpoint_order_cuts": False,
        "pair_adjacency_cuts": False,
        "latest_service_start_slot_bound": True,
        "time_window_arc_pruning": True,
        "resource_arc_pruning": True,
        "slot_task_time_pruning": True,
        "slot_arc_support_pruning": False,
        "mip_start_from_column_pool": True,
        "sortie_slot_position_bounds": True,
        "pair_weighted_completion_lb": True,
        "pair_energy_infeasible_cut": True,
        "pair_time_window_infeasible_cut": True,
        "pair_shadow_infeasible_cut": True,
        "recharge_aware_slot_bound": False,
        "objective_bound_no_negative_cutoff": True,
        "official_default": False,
    },
    "V4SZ": {
        "name": "V4SZ",
        "formulation_profile": "B4V4_strengthened_pair_weighted_zero_capacity_slot_truncation",
        "negative_mtz_connectivity": True,
        "proof_mtz_connectivity": True,
        "mtz_endpoint_order_cuts": False,
        "pair_adjacency_cuts": False,
        "latest_service_start_slot_bound": True,
        "time_window_arc_pruning": True,
        "resource_arc_pruning": True,
        "slot_task_time_pruning": True,
        "slot_arc_support_pruning": False,
        "mip_start_from_column_pool": True,
        "sortie_slot_position_bounds": True,
        "pair_weighted_completion_lb": True,
        "pair_energy_infeasible_cut": True,
        "pair_time_window_infeasible_cut": True,
        "pair_shadow_infeasible_cut": True,
        "recharge_aware_slot_bound": False,
        "zero_capacity_slot_truncation": True,
        "official_default": False,
    },
    "V4SZW": {
        "name": "V4SZW",
        "formulation_profile": "B4V4_strengthened_pair_weighted_zero_capacity_slot_warm_integer_start",
        "negative_mtz_connectivity": True,
        "proof_mtz_connectivity": True,
        "mtz_endpoint_order_cuts": False,
        "pair_adjacency_cuts": False,
        "latest_service_start_slot_bound": True,
        "time_window_arc_pruning": True,
        "resource_arc_pruning": True,
        "slot_task_time_pruning": True,
        "slot_arc_support_pruning": False,
        "mip_start_from_column_pool": True,
        "mip_start_zero_fill_integers": True,
        "sortie_slot_position_bounds": True,
        "pair_weighted_completion_lb": True,
        "pair_energy_infeasible_cut": True,
        "pair_time_window_infeasible_cut": True,
        "pair_shadow_infeasible_cut": True,
        "recharge_aware_slot_bound": False,
        "zero_capacity_slot_truncation": True,
        "official_default": False,
    },
    "V4SZCAP": {
        "name": "V4SZCAP",
        "formulation_profile": "B4V4_strengthened_pair_weighted_zero_capacity_slot_sequence_capacity_arc_pruning",
        "negative_mtz_connectivity": True,
        "proof_mtz_connectivity": True,
        "mtz_endpoint_order_cuts": False,
        "pair_adjacency_cuts": False,
        "latest_service_start_slot_bound": True,
        "time_window_arc_pruning": True,
        "resource_arc_pruning": True,
        "slot_task_time_pruning": True,
        "slot_arc_support_pruning": False,
        "slot_sequence_capacity_arc_pruning": True,
        "mip_start_from_column_pool": True,
        "sortie_slot_position_bounds": True,
        "pair_weighted_completion_lb": True,
        "pair_energy_infeasible_cut": True,
        "pair_time_window_infeasible_cut": True,
        "pair_shadow_infeasible_cut": True,
        "recharge_aware_slot_bound": False,
        "zero_capacity_slot_truncation": True,
        "official_default": False,
    },
    "V4SZPC": {
        "name": "V4SZPC",
        "formulation_profile": "B4V4_strengthened_zero_slot_pair_conflict_capacity_bound",
        "negative_mtz_connectivity": True,
        "proof_mtz_connectivity": True,
        "mtz_endpoint_order_cuts": False,
        "pair_adjacency_cuts": False,
        "latest_service_start_slot_bound": True,
        "time_window_arc_pruning": True,
        "resource_arc_pruning": True,
        "slot_task_time_pruning": True,
        "slot_arc_support_pruning": False,
        "mip_start_from_column_pool": True,
        "sortie_slot_position_bounds": True,
        "pair_weighted_completion_lb": True,
        "pair_energy_infeasible_cut": True,
        "pair_time_window_infeasible_cut": True,
        "pair_shadow_infeasible_cut": True,
        "task_slot_pair_conflict_capacity_bound": True,
        "recharge_aware_slot_bound": False,
        "zero_capacity_slot_truncation": True,
        "official_default": False,
    },
    "V4SL": {
        "name": "V4SL",
        "formulation_profile": "B4V4_strengthened_pair_weighted_slot_sequence_live_bound",
        "negative_mtz_connectivity": True,
        "proof_mtz_connectivity": True,
        "mtz_endpoint_order_cuts": False,
        "pair_adjacency_cuts": False,
        "latest_service_start_slot_bound": True,
        "time_window_arc_pruning": True,
        "resource_arc_pruning": True,
        "slot_task_time_pruning": True,
        "slot_arc_support_pruning": False,
        "mip_start_from_column_pool": True,
        "sortie_slot_position_bounds": True,
        "pair_weighted_completion_lb": True,
        "pair_energy_infeasible_cut": True,
        "pair_time_window_infeasible_cut": True,
        "pair_shadow_infeasible_cut": True,
        "recharge_aware_slot_bound": False,
        "zero_capacity_slot_truncation": True,
        "slot_sequence_capacity_live_bound": True,
        "official_default": False,
    },
    "V4ST": {
        "name": "V4ST",
        "formulation_profile": "B4V4_strengthened_pair_weighted_tight_service_start_bounds",
        "negative_mtz_connectivity": True,
        "proof_mtz_connectivity": True,
        "mtz_endpoint_order_cuts": False,
        "pair_adjacency_cuts": False,
        "latest_service_start_slot_bound": True,
        "time_window_arc_pruning": True,
        "resource_arc_pruning": True,
        "slot_task_time_pruning": True,
        "slot_arc_support_pruning": False,
        "mip_start_from_column_pool": True,
        "sortie_slot_position_bounds": True,
        "pair_weighted_completion_lb": True,
        "pair_energy_infeasible_cut": True,
        "pair_time_window_infeasible_cut": True,
        "pair_shadow_infeasible_cut": True,
        "recharge_aware_slot_bound": False,
        "zero_capacity_slot_truncation": True,
        "tight_service_start_bounds": True,
        "official_default": False,
    },
    "V4SZT": {
        "name": "V4SZT",
        "formulation_profile": "B4V4_strengthened_pair_weighted_zero_slot_tight_time_big_m",
        "negative_mtz_connectivity": True,
        "proof_mtz_connectivity": True,
        "mtz_endpoint_order_cuts": False,
        "pair_adjacency_cuts": False,
        "latest_service_start_slot_bound": True,
        "time_window_arc_pruning": True,
        "resource_arc_pruning": True,
        "slot_task_time_pruning": True,
        "slot_arc_support_pruning": False,
        "mip_start_from_column_pool": True,
        "sortie_slot_position_bounds": True,
        "pair_weighted_completion_lb": True,
        "pair_energy_infeasible_cut": True,
        "pair_time_window_infeasible_cut": True,
        "pair_shadow_infeasible_cut": True,
        "recharge_aware_slot_bound": False,
        "zero_capacity_slot_truncation": True,
        "tight_service_start_bounds": True,
        "tight_time_arc_big_m": True,
        "official_default": False,
    },
    "V4SZTP": {
        "name": "V4SZTP",
        "formulation_profile": "B4V4_strengthened_pair_weighted_zero_slot_tight_time_big_m_proof_only",
        "negative_mtz_connectivity": True,
        "proof_mtz_connectivity": True,
        "mtz_endpoint_order_cuts": False,
        "pair_adjacency_cuts": False,
        "latest_service_start_slot_bound": True,
        "time_window_arc_pruning": True,
        "resource_arc_pruning": True,
        "slot_task_time_pruning": True,
        "slot_arc_support_pruning": False,
        "mip_start_from_column_pool": True,
        "sortie_slot_position_bounds": True,
        "pair_weighted_completion_lb": True,
        "pair_energy_infeasible_cut": True,
        "pair_time_window_infeasible_cut": True,
        "pair_shadow_infeasible_cut": True,
        "recharge_aware_slot_bound": False,
        "zero_capacity_slot_truncation": True,
        "tight_service_start_bounds": True,
        "tight_time_arc_big_m": True,
        "phase_mode_default": "proof_only",
        "official_default": False,
    },
    "V4SH": {
        "name": "V4SH",
        "formulation_profile": "B4V4_strengthened_pair_weighted_seed_harvest",
        "negative_mtz_connectivity": True,
        "proof_mtz_connectivity": True,
        "mtz_endpoint_order_cuts": False,
        "pair_adjacency_cuts": False,
        "latest_service_start_slot_bound": True,
        "time_window_arc_pruning": True,
        "resource_arc_pruning": True,
        "slot_task_time_pruning": True,
        "slot_arc_support_pruning": False,
        "mip_start_from_column_pool": True,
        "sortie_slot_position_bounds": True,
        "pair_weighted_completion_lb": True,
        "pair_energy_infeasible_cut": True,
        "pair_time_window_infeasible_cut": True,
        "pair_shadow_infeasible_cut": True,
        "recharge_aware_slot_bound": False,
        "route_template_pre_harvest_enabled": True,
        "route_template_pre_harvest_time_cap_sec": 15.0,
        "route_template_pre_harvest_max_direct_tasks": 8,
        "route_template_pre_harvest_max_active_seeds": 120,
        "route_template_pre_harvest_neighborhood_enabled": True,
        "route_template_pre_harvest_max_neighborhood_seeds": 120,
        "route_template_pre_harvest_max_candidate_sets": 180,
        "route_template_pre_harvest_target": 1,
        "route_template_pre_harvest_fallback_enabled": True,
        "official_default": False,
    },
}


@dataclass(frozen=True)
class FinalJudgeResult:
    pricing_state: PricingState
    pricing_payload: dict
    negative_columns: tuple[JourneyColumn, ...]
    all_priced_columns: tuple[JourneyColumn, ...]


def run_true_dual_root_final_judge(
    data: LunarIceData,
    context: ReducedCostContext,
    *,
    max_direct_tasks: int = 5,
    negative_eps: float = 1.0e-6,
    cache: DirectPricingCache | None = None,
    branch_context: BranchContext | None = None,
    cut_context: CutContext | None = None,
    wall_time_limit_sec: float | None = None,
    complete_universe_columns: tuple[JourneyColumn, ...] | None = None,
    complete_universe_counts: dict | None = None,
    column_pool: ColumnPool | None = None,
    master_view: MasterColumnView | None = None,
    node_id: str = "root",
    active_task_sets: set[frozenset[str]] | None = None,
    labeling_final_judge_enabled: bool | None = None,
    labeling_final_judge_max_exact_tasks: int | None = None,
    labeling_final_judge_exact_harvest_target: int | None = None,
) -> FinalJudgeResult:
    """Run exhaustive fixed-graph pricing with fail-closed proof semantics.

    ``complete_universe_columns`` is a legacy name for the compressed fixed-graph
    universe: one objective-best representative journey per nonempty task subset.
    It is not the set of all route variants.
    """

    active_branch_context = branch_context or _branch_context_from_reduced_cost_context(context)
    active_cut_context = cut_context or _cut_context_from_reduced_cost_context(context)
    duals = JourneyDuals(
        cover=context.task_duals,
        fleet_limit=context.fleet_dual,
        cuts=context.cut_duals,
    )
    labeling_mode, labeling_source = _labeling_final_judge_mode(labeling_final_judge_enabled)
    auto_max_exact_tasks = _labeling_final_judge_max_exact_tasks(
        max_direct_tasks=max_direct_tasks,
        max_exact_tasks_override=labeling_final_judge_max_exact_tasks,
    )
    use_labeling_final_judge = bool(
        labeling_mode == "enabled"
        or (labeling_mode == "auto" and len(data.task_ids) <= auto_max_exact_tasks)
    )
    labeling_selection_reason = ""
    if labeling_mode == "enabled":
        labeling_selection_reason = (
            "explicit_enabled" if labeling_source == "explicit_parameter" else "environment_enabled"
        )
    elif labeling_mode == "auto" and use_labeling_final_judge:
        labeling_selection_reason = "auto_task_count_within_max_exact_tasks"
    if use_labeling_final_judge:
        result = _run_labeling_pricer_final_judge(
            data,
            duals,
            context=context,
            branch_context=active_branch_context,
            cut_context=active_cut_context,
            max_direct_tasks=max_direct_tasks,
            negative_eps=negative_eps,
            cache=cache,
            wall_time_limit_sec=wall_time_limit_sec,
            max_exact_tasks_override=labeling_final_judge_max_exact_tasks,
            exact_harvest_target_override=labeling_final_judge_exact_harvest_target,
            explicit_opt_in=labeling_final_judge_enabled is not None,
            selection_reason=labeling_selection_reason,
        )
        if labeling_mode == "auto":
            result.pricing_payload.update(
                {
                    "labeling_final_judge_auto_mode": True,
                    "labeling_final_judge_auto_selected": True,
                    "labeling_final_judge_auto_skip_reason": "",
                    "labeling_final_judge_opt_in_source": labeling_source,
                }
            )
        return result

    labeling_auto_payload = {}
    if labeling_mode == "auto":
        labeling_auto_payload = {
            "labeling_final_judge_enabled": False,
            "labeling_final_judge_auto_mode": True,
            "labeling_final_judge_auto_selected": False,
            "labeling_final_judge_auto_skip_reason": "task_count_exceeds_max_exact_tasks",
            "labeling_final_judge_opt_in_source": labeling_source,
            "labeling_final_judge_env": LABELING_FINAL_JUDGE_ENV,
            "labeling_final_judge_max_tasks_env": LABELING_FINAL_JUDGE_MAX_TASKS_ENV,
            "labeling_final_judge_exact_harvest_target_env": LABELING_FINAL_JUDGE_EXACT_HARVEST_TARGET_ENV,
            "labeling_final_judge_max_exact_tasks": int(auto_max_exact_tasks),
            "labeling_final_judge_max_exact_tasks_source": (
                "explicit_parameter"
                if labeling_final_judge_max_exact_tasks is not None
                else "environment_or_default"
            ),
            "labeling_final_judge_task_count": len(data.task_ids),
            "labeling_final_judge_exact_harvest_target": _labeling_final_judge_exact_harvest_target(
                exact_harvest_target_override=labeling_final_judge_exact_harvest_target
            ),
            "labeling_final_judge_selection_reason": "task_count_exceeds_max_exact_tasks",
            "labeling_final_judge_certificate_role": "not_selected",
            "labeling_final_judge_can_certify": False,
            "labeling_final_judge_downgrade_reason": "",
        }
    if active_cut_context.empty and (active_branch_context.empty or complete_universe_columns is not None):
        if (
            active_branch_context.empty
            and complete_universe_columns is None
            and len(data.task_ids) >= COMPACT_SINGLE_JOURNEY_PRICING_MIN_TASKS
        ):
            result = _run_compact_single_journey_pricing_final_judge(
                data,
                duals,
                context=context,
                branch_context=active_branch_context,
                cut_context=active_cut_context,
                negative_eps=negative_eps,
                wall_time_limit_sec=wall_time_limit_sec,
                column_pool=column_pool,
                master_view=master_view,
                node_id=node_id,
                active_task_sets=active_task_sets,
            )
            result.pricing_payload.update(labeling_auto_payload)
            return result
        result = _run_complete_universe_rc_final_judge(
            data,
            duals,
            context=context,
            branch_context=active_branch_context,
            cut_context=active_cut_context,
            max_direct_tasks=max_direct_tasks,
            negative_eps=negative_eps,
            cache=cache,
            wall_time_limit_sec=wall_time_limit_sec,
            complete_universe_columns=complete_universe_columns,
            complete_universe_counts=complete_universe_counts,
        )
        result.pricing_payload.update(labeling_auto_payload)
        return result

    pricing, columns = price_exhaustive_direct_journey_columns(
        data,
        duals,
        negative_eps=negative_eps,
        max_direct_tasks=int(max_direct_tasks),
        cache=cache,
        completion_bound_enabled=False,
        wall_time_limit_sec=wall_time_limit_sec,
        branch_context=active_branch_context,
        cut_context=active_cut_context,
    )
    negative_columns = tuple(
        column
        for column in columns
        if _manual_reduced_cost(column, duals, active_cut_context) < -abs(float(negative_eps))
    )
    manual_rc_values = tuple(_manual_reduced_cost(column, duals, active_cut_context) for column in columns)
    manual_best_reduced_cost = min(manual_rc_values) if manual_rc_values else None
    complete = bool(pricing.get("pricing_complete_for_all_task_subsets"))
    min_reduced_cost = pricing.get("best_reduced_cost")
    pricing_rc_audit_pass = bool(
        min_reduced_cost is None
        and manual_best_reduced_cost is None
        or (
            min_reduced_cost is not None
            and manual_best_reduced_cost is not None
            and abs(float(min_reduced_cost) - float(manual_best_reduced_cost)) <= 1.0e-6
        )
    )
    certified = bool(
        complete
        and min_reduced_cost is not None
        and float(min_reduced_cost) >= -abs(float(negative_eps))
        and not negative_columns
        and pricing_rc_audit_pass
    )
    if negative_columns:
        state = PricingState.FOUND_NEGATIVE
    elif certified:
        state = PricingState.CERTIFIED_NO_NEGATIVE
    else:
        state = PricingState.INCOMPLETE_LIMIT
    payload = dict(pricing)
    payload["pricing_state"] = state.value
    payload["completion_bound_pruning_enabled"] = False
    payload["can_certify_no_negative"] = bool(certified)
    payload["uses_true_dual_bpc_certificate"] = bool(certified)
    payload["dual_fingerprint"] = context.dual_fingerprint
    payload["branch_context"] = active_branch_context.to_payload()
    payload["cut_context"] = active_cut_context.to_payload()
    payload["manual_best_reduced_cost"] = manual_best_reduced_cost
    payload["pricing_best_reduced_cost"] = min_reduced_cost
    payload["pricing_rc_audit_pass"] = pricing_rc_audit_pass
    payload["manual_priced_column_count"] = len(manual_rc_values)
    payload["all_priced_columns_satisfy_branch_context"] = all(
        journey_satisfies_branch_context(column, active_branch_context)
        for column in columns
    )
    payload.update(labeling_auto_payload)
    return FinalJudgeResult(
        pricing_state=state,
        pricing_payload=payload,
        negative_columns=negative_columns,
        all_priced_columns=tuple(columns),
    )


def _run_labeling_pricer_final_judge(
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    context: ReducedCostContext,
    branch_context: BranchContext,
    cut_context: CutContext,
    max_direct_tasks: int,
    negative_eps: float,
    cache: DirectPricingCache | None,
    wall_time_limit_sec: float | None,
    max_exact_tasks_override: int | None = None,
    exact_harvest_target_override: int | None = None,
    explicit_opt_in: bool = False,
    selection_reason: str = "",
) -> FinalJudgeResult:
    start = perf_counter()
    max_exact_tasks = (
        max(1, min(64, int(max_exact_tasks_override)))
        if max_exact_tasks_override is not None
        else _env_int(
            LABELING_FINAL_JUDGE_MAX_TASKS_ENV,
            default=int(max_direct_tasks),
            minimum=1,
            maximum=64,
        )
    )
    exact_harvest_target = _labeling_final_judge_exact_harvest_target(
        exact_harvest_target_override=exact_harvest_target_override
    )
    payload, columns = run_bpc_labeling_pricer(
        data,
        duals,
        config=LabelingPricingConfig(
            mode=EXACT_ELEMENTARY_MODE,
            max_exact_tasks=max_exact_tasks,
            negative_eps=negative_eps,
            wall_time_limit_sec=wall_time_limit_sec,
            exact_negative_harvest_target=exact_harvest_target,
            stop_at_first_negative=True,
        ),
        branch_context=branch_context,
        cut_context=cut_context,
        cache=cache,
    )
    manual_rc_rows = tuple(
        (
            manual_journey_reduced_cost(
                column,
                duals,
                cut_coefficients=cut_context.coefficients_for(column),
            ),
            column,
        )
        for column in columns
    )
    manual_negative_rows = tuple(
        (rc, column)
        for rc, column in manual_rc_rows
        if rc < -abs(float(negative_eps))
    )
    branch_feasible_negative_rows = tuple(
        (rc, column)
        for rc, column in manual_negative_rows
        if journey_satisfies_branch_context(column, branch_context)
    )
    branch_filtered_negative_count = len(manual_negative_rows) - len(branch_feasible_negative_rows)
    negative_columns = tuple(column for _rc, column in branch_feasible_negative_rows)
    branch_feasible_rc_values = tuple(
        rc
        for rc, column in manual_rc_rows
        if journey_satisfies_branch_context(column, branch_context)
    )
    manual_branch_feasible_best = min(branch_feasible_rc_values) if branch_feasible_rc_values else None
    payload_true_best = _first_float(payload.get("true_best_reduced_cost"))
    manual_consistency_pass = bool(
        (payload_true_best is None and manual_branch_feasible_best is None)
        or (
            payload_true_best is not None
            and manual_branch_feasible_best is not None
            and abs(float(payload_true_best) - float(manual_branch_feasible_best)) <= 1.0e-6
        )
    )
    underlying_proof_kind = str(payload.get("pricing_proof_kind") or "")
    underlying_proof_kind_certifying = underlying_proof_kind in CERTIFYING_PROOF_KINDS
    state = _pricing_state_from_payload(payload.get("pricing_state"))
    if negative_columns:
        state = PricingState.FOUND_NEGATIVE
    elif branch_filtered_negative_count and state == PricingState.FOUND_NEGATIVE:
        state = PricingState.INCOMPLETE_LIMIT
    elif state == PricingState.CERTIFIED_NO_NEGATIVE and not manual_consistency_pass:
        state = PricingState.INCOMPLETE_LIMIT
    elif state == PricingState.CERTIFIED_NO_NEGATIVE and not underlying_proof_kind_certifying:
        state = PricingState.INCOMPLETE_LIMIT
    can_certify = bool(
        payload.get("can_certify_no_negative") is True
        and state == PricingState.CERTIFIED_NO_NEGATIVE
        and manual_consistency_pass
        and underlying_proof_kind_certifying
    )
    final_proof_kind = (
        PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE
        if can_certify
        else PROOF_KIND_EXHAUSTIVE_FOUND_NEGATIVE
        if negative_columns
        else PROOF_KIND_EXHAUSTIVE_INCOMPLETE
    )
    downgrade_reason = _labeling_final_judge_downgrade_reason(
        can_certify=can_certify,
        negative_columns=negative_columns,
        branch_filtered_negative_count=branch_filtered_negative_count,
        manual_consistency_pass=manual_consistency_pass,
        underlying_proof_kind_certifying=underlying_proof_kind_certifying,
        underlying_proof_kind=underlying_proof_kind,
    )
    payload = dict(payload)
    payload.update(
        {
            "status": "LABELING_FINAL_JUDGE_PRICED",
            "exact_status": (
                "BPC_NO_NEGATIVE_CERTIFIED"
                if can_certify
                else "NOT_SOLVED"
            ),
            "pricing_state": state.value,
            "can_certify_no_negative": can_certify,
            "uses_true_dual_bpc_certificate": can_certify,
            "pricing_proof_kind": final_proof_kind,
            "underlying_pricing_proof_kind": underlying_proof_kind,
            "underlying_pricing_proof_kind_certifying": underlying_proof_kind_certifying,
            "pricing_proof_kind_source": "labeling_final_judge_true_dual_reaudit",
            "labeling_final_judge_enabled": True,
            "labeling_final_judge_opt_in_source": "explicit_parameter" if explicit_opt_in else "environment",
            "labeling_final_judge_selection_reason": selection_reason,
            "labeling_final_judge_task_count": len(data.task_ids),
            "labeling_final_judge_certificate_role": "true_dual_exact_elementary_final_proof",
            "labeling_final_judge_can_certify": can_certify,
            "labeling_final_judge_downgrade_reason": downgrade_reason,
            "labeling_final_judge_env": LABELING_FINAL_JUDGE_ENV,
            "labeling_final_judge_max_tasks_env": LABELING_FINAL_JUDGE_MAX_TASKS_ENV,
            "labeling_final_judge_exact_harvest_target_env": LABELING_FINAL_JUDGE_EXACT_HARVEST_TARGET_ENV,
            "labeling_final_judge_max_exact_tasks": int(max_exact_tasks),
            "labeling_final_judge_max_exact_tasks_source": (
                "explicit_parameter" if max_exact_tasks_override is not None else "environment_or_default"
            ),
            "labeling_final_judge_exact_harvest_target": int(exact_harvest_target),
            "labeling_final_judge_exact_harvest_target_source": (
                "explicit_parameter" if exact_harvest_target_override is not None else "environment_or_default"
            ),
            "labeling_final_judge_early_negative_stop_enabled": True,
            "labeling_final_judge_early_negative_stop_can_certify_no_negative": False,
            "dual_fingerprint": context.dual_fingerprint,
            "branch_context": branch_context.to_payload(),
            "cut_context": cut_context.to_payload(),
            "manual_best_reduced_cost": payload.get("true_best_reduced_cost"),
            "manual_branch_feasible_best_reduced_cost": manual_branch_feasible_best,
            "labeling_final_judge_manual_rc_consistency_pass": manual_consistency_pass,
            "labeling_final_judge_payload_true_best_reduced_cost": payload_true_best,
            "manual_branch_feasible_negative_count": len(branch_feasible_negative_rows),
            "manual_branch_filtered_negative_count": int(branch_filtered_negative_count),
            "labeling_final_judge_branch_filtered_negative_count": int(
                branch_filtered_negative_count
            ),
            "pricing_best_reduced_cost": payload.get("pricing_best_reduced_cost"),
            "manual_priced_column_count": int(payload.get("true_audited_column_count") or 0),
            "completion_bound": payload.get("completion_bound") or {},
            "all_priced_columns_satisfy_branch_context": all(
                journey_satisfies_branch_context(column, branch_context)
                for column in columns
            ),
            "completion_bound_pruning_enabled": bool(
                (payload.get("completion_bound") or {}).get("enabled")
            ),
            "final_judge_wall_time": round(perf_counter() - start, 6),
            "note": (
                "Opt-in final judge used exact-safe resource-labeling pricing. "
                "Certificates are allowed only for exact elementary full-subset coverage "
                "with true-dual reduced-cost audit."
            ),
        }
    )
    return FinalJudgeResult(
        pricing_state=state,
        pricing_payload=payload,
        negative_columns=negative_columns,
        all_priced_columns=tuple(columns),
    )


def _labeling_final_judge_downgrade_reason(
    *,
    can_certify: bool,
    negative_columns: tuple[JourneyColumn, ...],
    branch_filtered_negative_count: int,
    manual_consistency_pass: bool,
    underlying_proof_kind_certifying: bool,
    underlying_proof_kind: str,
) -> str:
    if can_certify:
        return ""
    if negative_columns:
        return "found_negative"
    if int(branch_filtered_negative_count) > 0:
        return "branch_filtered_negative"
    if not bool(manual_consistency_pass):
        return "manual_rc_mismatch"
    if not bool(underlying_proof_kind_certifying):
        if str(underlying_proof_kind or "") in {"", PROOF_KIND_EXHAUSTIVE_INCOMPLETE}:
            return "coverage_incomplete_or_timeout"
        return "noncertifying_underlying_proof_kind"
    return "coverage_incomplete_or_timeout"


def _run_compact_single_journey_pricing_final_judge(
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    context: ReducedCostContext,
    branch_context: BranchContext,
    cut_context: CutContext,
    negative_eps: float,
    wall_time_limit_sec: float | None,
    column_pool: ColumnPool | None = None,
    master_view: MasterColumnView | None = None,
    node_id: str = "root",
    active_task_sets: set[frozenset[str]] | None = None,
) -> FinalJudgeResult:
    start = perf_counter()
    phase_payloads: dict[str, dict] = {}
    forbidden_patterns: list[tuple[tuple[int, str, str, str], ...]] = []
    forbidden_task_sets: list[tuple[str, ...]] = []
    seen_patterns: set[tuple[tuple[int, str, str, str], ...]] = set()
    seen_task_sets: set[tuple[str, ...]] = set()
    batch_negative_columns: list[JourneyColumn] = []
    batch_pricing_rc_by_signature: dict[object, float] = {}
    last_negative_result: dict | None = None
    profile = _compact_final_judge_profile_from_env()
    phase_mode = _compact_final_judge_phase_mode_from_env(
        default=str(
            profile.get(
                "phase_mode_default",
                COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_DEFAULT,
            )
        )
    )
    compact_pricing_threads = _env_int(
        COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_THREADS_ENV,
        default=1,
        minimum=1,
        maximum=64,
    )
    profile = dict(profile)
    profile["compact_final_judge_threads"] = int(compact_pricing_threads)
    proof_mip_start_journey = _compact_mip_start_journey_from_pool(
        column_pool,
        duals,
        cut_context,
        branch_context,
    ) if bool(profile.get("mip_start_from_column_pool")) else None
    service_start_depot_travel_lb = _env_bool(
        COMPACT_SINGLE_JOURNEY_SERVICE_START_DEPOT_TRAVEL_LB_ENV,
        default=bool(profile.get("service_start_depot_travel_lb")),
    )
    mtz_endpoint_order_cuts = _env_bool(
        COMPACT_SINGLE_JOURNEY_MTZ_ENDPOINT_ORDER_CUTS_ENV,
        default=bool(profile["mtz_endpoint_order_cuts"]),
    )
    pair_adjacency_cuts = _env_bool(
        COMPACT_SINGLE_JOURNEY_PAIR_ADJACENCY_CUTS_ENV,
        default=bool(profile["pair_adjacency_cuts"]),
    )
    profile["proof_mtz_connectivity"] = _env_bool(
        COMPACT_SINGLE_JOURNEY_PROOF_MTZ_CONNECTIVITY_ENV,
        default=bool(profile["proof_mtz_connectivity"]),
    )
    task_to_depot_return_travel_lb = _env_bool(
        COMPACT_SINGLE_JOURNEY_TASK_TO_DEPOT_RETURN_TRAVEL_LB_ENV,
        default=bool(profile.get("task_to_depot_return_travel_lb")),
    )
    pair_route_duration_lb = _env_bool(
        COMPACT_SINGLE_JOURNEY_PAIR_ROUTE_DURATION_LB_ENV,
        default=bool(profile.get("pair_route_duration_lb")),
    )
    pair_weighted_completion_lb = _env_bool(
        COMPACT_SINGLE_JOURNEY_PAIR_WEIGHTED_COMPLETION_LB_ENV,
        default=bool(profile.get("pair_weighted_completion_lb")),
    )
    sortie_slot_position_bounds = _env_bool(
        COMPACT_SINGLE_JOURNEY_SORTIE_SLOT_POSITION_BOUNDS_ENV,
        default=bool(profile.get("sortie_slot_position_bounds")),
    )
    demand_cover_cut = _env_bool(
        COMPACT_SINGLE_JOURNEY_DEMAND_COVER_CUT_ENV,
        default=bool(profile.get("demand_cover_cut")),
    )
    single_task_energy_lb = _env_bool(
        COMPACT_SINGLE_JOURNEY_SINGLE_TASK_ENERGY_LB_ENV,
        default=bool(profile.get("single_task_energy_lb")),
    )
    single_task_shadow_lb = _env_bool(
        COMPACT_SINGLE_JOURNEY_SINGLE_TASK_SHADOW_LB_ENV,
        default=bool(profile.get("single_task_shadow_lb")),
    )
    pair_energy_lb = _env_bool(
        COMPACT_SINGLE_JOURNEY_PAIR_ENERGY_LB_ENV,
        default=bool(profile.get("pair_energy_lb")),
    )
    pair_shadow_lb = _env_bool(
        COMPACT_SINGLE_JOURNEY_PAIR_SHADOW_LB_ENV,
        default=bool(profile.get("pair_shadow_lb")),
    )
    pair_energy_infeasible_cut = _env_bool(
        COMPACT_SINGLE_JOURNEY_PAIR_ENERGY_INFEASIBLE_CUT_ENV,
        default=bool(profile.get("pair_energy_infeasible_cut")),
    )
    pair_time_window_infeasible_cut = _env_bool(
        COMPACT_SINGLE_JOURNEY_PAIR_TIME_WINDOW_INFEASIBLE_CUT_ENV,
        default=bool(profile.get("pair_time_window_infeasible_cut")),
    )
    pair_time_window_precedence_cut = _env_bool(
        COMPACT_SINGLE_JOURNEY_PAIR_TIME_WINDOW_PRECEDENCE_CUT_ENV,
        default=bool(profile.get("pair_time_window_precedence_cut")),
    )
    triple_time_window_infeasible_cut = _env_bool(
        COMPACT_SINGLE_JOURNEY_TRIPLE_TIME_WINDOW_INFEASIBLE_CUT_ENV,
        default=bool(profile.get("triple_time_window_infeasible_cut")),
    )
    quad_time_window_infeasible_cut = _env_bool(
        COMPACT_SINGLE_JOURNEY_QUAD_TIME_WINDOW_INFEASIBLE_CUT_ENV,
        default=bool(profile.get("quad_time_window_infeasible_cut")),
    )
    pair_shadow_infeasible_cut = _env_bool(
        COMPACT_SINGLE_JOURNEY_PAIR_SHADOW_INFEASIBLE_CUT_ENV,
        default=bool(profile.get("pair_shadow_infeasible_cut")),
    )
    triple_shadow_infeasible_cut = _env_bool(
        COMPACT_SINGLE_JOURNEY_TRIPLE_SHADOW_INFEASIBLE_CUT_ENV,
        default=bool(profile.get("triple_shadow_infeasible_cut")),
    )
    triple_energy_infeasible_cut = _env_bool(
        COMPACT_SINGLE_JOURNEY_TRIPLE_ENERGY_INFEASIBLE_CUT_ENV,
        default=bool(profile.get("triple_energy_infeasible_cut")),
    )
    resource_arc_pruning = _env_bool(
        COMPACT_SINGLE_JOURNEY_RESOURCE_ARC_PRUNING_ENV,
        default=bool(profile.get("resource_arc_pruning")),
    )
    slot_arc_support_pruning = _env_bool(
        COMPACT_SINGLE_JOURNEY_SLOT_ARC_SUPPORT_PRUNING_ENV,
        default=bool(profile.get("slot_arc_support_pruning")),
    )
    slot_sequence_capacity_arc_pruning = _env_bool(
        COMPACT_SINGLE_JOURNEY_SLOT_SEQUENCE_CAPACITY_ARC_PRUNING_ENV,
        default=bool(profile.get("slot_sequence_capacity_arc_pruning")),
    )
    task_slot_pair_conflict_capacity_bound = _env_bool(
        COMPACT_SINGLE_JOURNEY_TASK_SLOT_PAIR_CONFLICT_CAPACITY_BOUND_ENV,
        default=bool(profile.get("task_slot_pair_conflict_capacity_bound")),
    )
    recharge_aware_slot_bound = _env_bool(
        COMPACT_SINGLE_JOURNEY_RECHARGE_AWARE_SLOT_BOUND_ENV,
        default=bool(profile.get("recharge_aware_slot_bound")),
    )
    objective_bound_no_negative_cutoff = _env_bool(
        COMPACT_SINGLE_JOURNEY_OBJECTIVE_BOUND_CUTOFF_ENV,
        default=bool(profile.get("objective_bound_no_negative_cutoff")),
    )
    zero_capacity_slot_truncation = _env_bool(
        COMPACT_SINGLE_JOURNEY_ZERO_CAPACITY_SLOT_TRUNCATION_ENV,
        default=bool(profile.get("zero_capacity_slot_truncation")),
    )
    slot_sequence_capacity_live_bound = _env_bool(
        COMPACT_SINGLE_JOURNEY_SLOT_SEQUENCE_CAPACITY_LIVE_BOUND_ENV,
        default=bool(profile.get("slot_sequence_capacity_live_bound")),
    )
    tight_service_start_bounds = _env_bool(
        COMPACT_SINGLE_JOURNEY_TIGHT_SERVICE_START_BOUNDS_ENV,
        default=bool(profile.get("tight_service_start_bounds")),
    )
    tight_time_arc_big_m = _env_bool(
        COMPACT_SINGLE_JOURNEY_TIGHT_TIME_ARC_BIG_M_ENV,
        default=bool(profile.get("tight_time_arc_big_m")),
    )
    slot_service_start_y_lower_bound = _env_bool(
        COMPACT_SINGLE_JOURNEY_SLOT_SERVICE_START_Y_LB_ENV,
        default=bool(profile.get("slot_service_start_y_lower_bound")),
    )
    dual_task_slot_full_space_lower_bound = _env_bool(
        COMPACT_SINGLE_JOURNEY_DUAL_TASK_SLOT_FULL_SPACE_LB_ENV,
        default=False,
    )
    dual_task_slot_full_space_lb_time_limit_sec = _env_float(
        COMPACT_SINGLE_JOURNEY_DUAL_TASK_SLOT_FULL_SPACE_LB_TIME_LIMIT_ENV,
        default=0.25,
        minimum=0.001,
        maximum=10.0,
    )
    dual_task_slot_full_space_lb_early_stop_on_negative = _env_bool(
        COMPACT_SINGLE_JOURNEY_DUAL_TASK_SLOT_FULL_SPACE_LB_EARLY_STOP_ENV,
        default=True,
    )
    batch_target = _env_int(
        COMPACT_SINGLE_JOURNEY_NEGATIVE_BATCH_TARGET_ENV,
        default=COMPACT_SINGLE_JOURNEY_NEGATIVE_BATCH_TARGET,
        minimum=1,
        maximum=32,
    )
    optimization_harvest_target = _env_int(
        COMPACT_SINGLE_JOURNEY_OPTIMIZATION_HARVEST_TARGET_ENV,
        default=COMPACT_SINGLE_JOURNEY_OPTIMIZATION_HARVEST_TARGET,
        minimum=1,
        maximum=16,
    )
    negative_search_cap = _env_float(
        COMPACT_SINGLE_JOURNEY_NEGATIVE_SEARCH_CAP_ENV,
        default=COMPACT_SINGLE_JOURNEY_NEGATIVE_SEARCH_CAP_SEC,
        minimum=0.001,
        maximum=3600.0,
    )
    no_good_scope = _env_choice(
        COMPACT_SINGLE_JOURNEY_NEGATIVE_NO_GOOD_SCOPE_ENV,
        default="arc",
        choices={"arc", "task_set", "arc_and_task_set"},
    )
    optimization_harvest_no_good_scope = _env_choice(
        COMPACT_SINGLE_JOURNEY_OPTIMIZATION_HARVEST_NO_GOOD_SCOPE_ENV,
        default="task_set",
        choices={"arc", "task_set", "arc_and_task_set"},
    )
    route_template_pre_harvest_enabled = _env_bool(
        COMPACT_SINGLE_JOURNEY_ROUTE_TEMPLATE_PRE_HARVEST_ENV,
        default=bool(profile.get("route_template_pre_harvest_enabled", False)),
    )
    route_template_pre_harvest_time_cap = _env_float(
        COMPACT_SINGLE_JOURNEY_ROUTE_TEMPLATE_PRE_HARVEST_TIME_CAP_ENV,
        default=float(profile.get("route_template_pre_harvest_time_cap_sec", 5.0)),
        minimum=0.001,
        maximum=3600.0,
    )
    route_template_pre_harvest_max_direct_tasks = _env_int(
        COMPACT_SINGLE_JOURNEY_ROUTE_TEMPLATE_PRE_HARVEST_MAX_DIRECT_TASKS_ENV,
        default=int(profile.get("route_template_pre_harvest_max_direct_tasks", 8)),
        minimum=1,
        maximum=max(1, len(data.task_ids)),
    )
    route_template_pre_harvest_max_active_seeds = _env_int(
        COMPACT_SINGLE_JOURNEY_ROUTE_TEMPLATE_PRE_HARVEST_MAX_ACTIVE_SEEDS_ENV,
        default=int(profile.get("route_template_pre_harvest_max_active_seeds", 120)),
        minimum=0,
        maximum=10000,
    )
    route_template_pre_harvest_neighborhood_enabled = _env_bool(
        COMPACT_SINGLE_JOURNEY_ROUTE_TEMPLATE_PRE_HARVEST_NEIGHBORHOOD_ENV,
        default=bool(profile.get("route_template_pre_harvest_neighborhood_enabled", True)),
    )
    route_template_pre_harvest_max_neighborhood_seeds = _env_int(
        COMPACT_SINGLE_JOURNEY_ROUTE_TEMPLATE_PRE_HARVEST_MAX_NEIGHBORHOOD_SEEDS_ENV,
        default=int(profile.get("route_template_pre_harvest_max_neighborhood_seeds", 120)),
        minimum=0,
        maximum=100000,
    )
    route_template_pre_harvest_max_candidate_sets = _env_int(
        COMPACT_SINGLE_JOURNEY_ROUTE_TEMPLATE_PRE_HARVEST_MAX_CANDIDATE_SETS_ENV,
        default=int(profile.get("route_template_pre_harvest_max_candidate_sets", 160)),
        minimum=1,
        maximum=100000,
    )
    route_template_pre_harvest_target = _env_int(
        COMPACT_SINGLE_JOURNEY_ROUTE_TEMPLATE_PRE_HARVEST_TARGET_ENV,
        default=int(
            profile.get(
                "route_template_pre_harvest_target",
                COMPACT_SINGLE_JOURNEY_ROUTE_TEMPLATE_PRE_HARVEST_TARGET,
            )
        ),
        minimum=1,
        maximum=32,
    )
    route_template_pre_harvest_fallback_enabled = _env_bool(
        COMPACT_SINGLE_JOURNEY_ROUTE_TEMPLATE_PRE_HARVEST_FALLBACK_ENV,
        default=bool(profile.get("route_template_pre_harvest_fallback_enabled", True)),
    )
    mip_start_zero_fill_integers = _env_bool(
        COMPACT_SINGLE_JOURNEY_MIP_START_ZERO_FILL_INTEGERS_ENV,
        default=bool(profile.get("mip_start_zero_fill_integers", False)),
    )
    mip_start_inactive_tail_time = _env_bool(
        COMPACT_SINGLE_JOURNEY_MIP_START_INACTIVE_TAIL_TIME_ENV,
        default=bool(profile.get("mip_start_inactive_tail_time", False)),
    )
    mip_start_inactive_tail_time_mode = _env_choice(
        COMPACT_SINGLE_JOURNEY_MIP_START_INACTIVE_TAIL_TIME_MODE_ENV,
        default=str(profile.get("mip_start_inactive_tail_time_mode", "zero")),
        choices={"zero", "previous_end", "previous_end_all"},
    )
    negative_search_mip_start_enabled = _env_bool(
        COMPACT_SINGLE_JOURNEY_NEGATIVE_SEARCH_MIP_START_ENV,
        default=False,
    )
    negative_search_mip_start_journey = (
        proof_mip_start_journey if negative_search_mip_start_enabled else None
    )
    if (
        route_template_pre_harvest_enabled
        and phase_mode == COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_DEFAULT
    ):
        route_template_result = _run_route_template_pre_harvest(
            data,
            duals,
            cut_context,
            branch_context=branch_context,
            negative_eps=negative_eps,
            started_at=start,
            wall_time_limit_sec=wall_time_limit_sec,
            time_cap_sec=route_template_pre_harvest_time_cap,
            max_direct_tasks=route_template_pre_harvest_max_direct_tasks,
            max_active_seeds=route_template_pre_harvest_max_active_seeds,
            neighborhood_enabled=route_template_pre_harvest_neighborhood_enabled,
            max_neighborhood_seeds=route_template_pre_harvest_max_neighborhood_seeds,
            max_candidate_sets=route_template_pre_harvest_max_candidate_sets,
            harvest_target=route_template_pre_harvest_target,
            column_pool=column_pool,
            master_view=master_view,
            node_id=node_id,
            active_task_sets=active_task_sets,
        )
        phase_payloads["route_template_pre_harvest"] = _compact_phase_summary(route_template_result)
        selected_columns = tuple(route_template_result.get("journeys") or tuple())
        if selected_columns:
            return _compact_final_judge_result(
                data,
                context=context,
                branch_context=branch_context,
                cut_context=cut_context,
                result=route_template_result,
                state=PricingState.FOUND_NEGATIVE,
                negative_columns=selected_columns,
                can_certify=False,
                started_at=start,
                phase="route_template_pre_harvest",
                phase_payloads=phase_payloads,
                profile=profile,
                phase_mode=phase_mode,
            )
        if not route_template_pre_harvest_fallback_enabled:
            route_template_result = dict(route_template_result)
            route_template_result["route_template_pre_harvest_fallback_enabled"] = False
            route_template_result["status"] = "ROUTE_TEMPLATE_PRE_HARVEST_NO_NEGATIVE_FALLBACK_DISABLED"
            route_template_result["algorithm_status"] = "ROUTE_TEMPLATE_PRE_HARVEST_NO_NEGATIVE_FALLBACK_DISABLED"
            route_template_result["pricing_state"] = PricingState.INCOMPLETE_LIMIT.value
            route_template_result["note"] = (
                "Route-template pre-harvest did not return an addable negative column and "
                "compact fallback is disabled for this diagnostic frontier run. This is not "
                "a no-negative certificate."
            )
            phase_payloads["route_template_pre_harvest"] = _compact_phase_summary(route_template_result)
            return _compact_final_judge_result(
                data,
                context=context,
                branch_context=branch_context,
                cut_context=cut_context,
                result=route_template_result,
                state=PricingState.INCOMPLETE_LIMIT,
                negative_columns=tuple(),
                can_certify=False,
                started_at=start,
                phase="route_template_pre_harvest",
                phase_payloads=phase_payloads,
                profile=profile,
                phase_mode=phase_mode,
            )
    if phase_mode == "feasibility_proof_only":
        remaining = _remaining_compact_time(wall_time_limit_sec, started_at=start)
        result = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=remaining,
            threads=compact_pricing_threads,
            mip_gap=0.0,
            negative_eps=negative_eps,
            mtz_connectivity=bool(profile["proof_mtz_connectivity"]),
            mtz_endpoint_order_cuts=bool(mtz_endpoint_order_cuts),
            pair_adjacency_cuts=bool(pair_adjacency_cuts),
            latest_service_start_slot_bound=bool(profile["latest_service_start_slot_bound"]),
            time_window_arc_pruning=bool(profile["time_window_arc_pruning"]),
            resource_arc_pruning=bool(resource_arc_pruning),
            slot_task_time_pruning=bool(profile["slot_task_time_pruning"]),
            slot_arc_support_pruning=bool(slot_arc_support_pruning),
            slot_sequence_capacity_arc_pruning=bool(slot_sequence_capacity_arc_pruning),
            recharge_aware_slot_bound=bool(recharge_aware_slot_bound),
            objective_bound_no_negative_cutoff=bool(objective_bound_no_negative_cutoff),
            zero_capacity_slot_truncation=bool(zero_capacity_slot_truncation),
            slot_sequence_capacity_live_bound=bool(slot_sequence_capacity_live_bound),
            tight_service_start_bounds=bool(tight_service_start_bounds),
            tight_time_arc_big_m=bool(tight_time_arc_big_m),
            slot_service_start_y_lower_bound=bool(slot_service_start_y_lower_bound),
            dual_task_slot_full_space_lower_bound=bool(dual_task_slot_full_space_lower_bound),
            dual_task_slot_full_space_lb_time_limit_sec=float(
                dual_task_slot_full_space_lb_time_limit_sec
            ),
            dual_task_slot_full_space_lb_early_stop_on_negative=bool(
                dual_task_slot_full_space_lb_early_stop_on_negative
            ),
            sortie_slot_position_bounds=sortie_slot_position_bounds,
            service_start_depot_travel_lb=service_start_depot_travel_lb,
            task_to_depot_return_travel_lb=task_to_depot_return_travel_lb,
            pair_route_duration_lb=pair_route_duration_lb,
            pair_weighted_completion_lb=pair_weighted_completion_lb,
            demand_cover_cut=demand_cover_cut,
            single_task_energy_lb=single_task_energy_lb,
            single_task_shadow_lb=single_task_shadow_lb,
            pair_energy_lb=pair_energy_lb,
            pair_shadow_lb=pair_shadow_lb,
            pair_energy_infeasible_cut=pair_energy_infeasible_cut,
            pair_time_window_infeasible_cut=pair_time_window_infeasible_cut,
            pair_time_window_precedence_cut=pair_time_window_precedence_cut,
            triple_time_window_infeasible_cut=triple_time_window_infeasible_cut,
            quad_time_window_infeasible_cut=quad_time_window_infeasible_cut,
            pair_shadow_infeasible_cut=pair_shadow_infeasible_cut,
            triple_shadow_infeasible_cut=triple_shadow_infeasible_cut,
            triple_energy_infeasible_cut=triple_energy_infeasible_cut,
            task_slot_pair_conflict_capacity_bound=bool(
                task_slot_pair_conflict_capacity_bound
            ),
            negative_feasibility_search=True,
            mip_start_journey=negative_search_mip_start_journey,
            mip_start_zero_fill_integers=bool(mip_start_zero_fill_integers),
            mip_start_inactive_tail_time=bool(mip_start_inactive_tail_time),
            mip_start_inactive_tail_time_mode=str(mip_start_inactive_tail_time_mode),
        )
        result = _with_compact_profile_payload(result, profile)
        result["negative_feasibility_full_space_proof_attempted"] = True
        result["negative_feasibility_full_space_proof_can_certify"] = bool(
            result.get("can_certify_no_negative")
            and not result.get("forbidden_arc_pattern_count")
            and not result.get("forbidden_task_set_count")
        )
        state, negative_columns, can_certify = _compact_result_state(
            result,
            duals,
            cut_context,
            negative_eps=negative_eps,
        )
        return _compact_final_judge_result(
            data,
            context=context,
            branch_context=branch_context,
            cut_context=cut_context,
            result=result,
            state=state,
            negative_columns=negative_columns,
            can_certify=can_certify,
            started_at=start,
            phase="negative_feasibility_proof",
            phase_payloads={"negative_feasibility_proof": _compact_phase_summary(result)},
            profile=profile,
            phase_mode=phase_mode,
        )

    negative_batch_range = range(1, batch_target + 1) if phase_mode != "proof_only" else ()
    for batch_index in negative_batch_range:
        remaining_for_search = _remaining_compact_time(wall_time_limit_sec, started_at=start)
        if remaining_for_search is not None and remaining_for_search <= 0.25:
            break
        negative_budget = (
            negative_search_cap
            if remaining_for_search is None
            else min(
                max(0.001, float(remaining_for_search)),
                negative_search_cap,
            )
        )
        negative_result = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=negative_budget,
            threads=compact_pricing_threads,
            mip_gap=0.0,
            negative_eps=negative_eps,
            mtz_connectivity=bool(profile["negative_mtz_connectivity"]),
            mtz_endpoint_order_cuts=bool(mtz_endpoint_order_cuts),
            pair_adjacency_cuts=bool(pair_adjacency_cuts),
            latest_service_start_slot_bound=bool(profile["latest_service_start_slot_bound"]),
            time_window_arc_pruning=bool(profile["time_window_arc_pruning"]),
            resource_arc_pruning=bool(resource_arc_pruning),
            slot_task_time_pruning=bool(profile["slot_task_time_pruning"]),
            slot_arc_support_pruning=bool(slot_arc_support_pruning),
            slot_sequence_capacity_arc_pruning=bool(slot_sequence_capacity_arc_pruning),
            recharge_aware_slot_bound=bool(recharge_aware_slot_bound),
            objective_bound_no_negative_cutoff=bool(objective_bound_no_negative_cutoff),
            zero_capacity_slot_truncation=bool(zero_capacity_slot_truncation),
            slot_sequence_capacity_live_bound=bool(slot_sequence_capacity_live_bound),
            tight_service_start_bounds=bool(tight_service_start_bounds),
            tight_time_arc_big_m=bool(tight_time_arc_big_m),
            slot_service_start_y_lower_bound=bool(slot_service_start_y_lower_bound),
            dual_task_slot_full_space_lower_bound=bool(dual_task_slot_full_space_lower_bound),
            dual_task_slot_full_space_lb_time_limit_sec=float(
                dual_task_slot_full_space_lb_time_limit_sec
            ),
            dual_task_slot_full_space_lb_early_stop_on_negative=bool(
                dual_task_slot_full_space_lb_early_stop_on_negative
            ),
            sortie_slot_position_bounds=sortie_slot_position_bounds,
            service_start_depot_travel_lb=service_start_depot_travel_lb,
            task_to_depot_return_travel_lb=task_to_depot_return_travel_lb,
            pair_route_duration_lb=pair_route_duration_lb,
            pair_weighted_completion_lb=pair_weighted_completion_lb,
            demand_cover_cut=demand_cover_cut,
            single_task_energy_lb=single_task_energy_lb,
            single_task_shadow_lb=single_task_shadow_lb,
            pair_energy_lb=pair_energy_lb,
            pair_shadow_lb=pair_shadow_lb,
            pair_energy_infeasible_cut=pair_energy_infeasible_cut,
            pair_time_window_infeasible_cut=pair_time_window_infeasible_cut,
            pair_time_window_precedence_cut=pair_time_window_precedence_cut,
            triple_time_window_infeasible_cut=triple_time_window_infeasible_cut,
            quad_time_window_infeasible_cut=quad_time_window_infeasible_cut,
            pair_shadow_infeasible_cut=pair_shadow_infeasible_cut,
            triple_shadow_infeasible_cut=triple_shadow_infeasible_cut,
            triple_energy_infeasible_cut=triple_energy_infeasible_cut,
            task_slot_pair_conflict_capacity_bound=bool(
                task_slot_pair_conflict_capacity_bound
            ),
            negative_feasibility_search=True,
            forbidden_arc_patterns=tuple(forbidden_patterns),
            forbidden_task_sets=tuple(forbidden_task_sets),
            mip_start_journey=negative_search_mip_start_journey,
            mip_start_zero_fill_integers=bool(mip_start_zero_fill_integers),
            mip_start_inactive_tail_time=bool(mip_start_inactive_tail_time),
            mip_start_inactive_tail_time_mode=str(mip_start_inactive_tail_time_mode),
        )
        negative_result = _with_compact_profile_payload(negative_result, profile)
        last_negative_result = negative_result
        phase_payloads[f"negative_feasibility_search_{batch_index}"] = _compact_phase_summary(negative_result)
        negative_state, negative_columns, negative_can_certify = _compact_result_state(
            negative_result,
            duals,
            cut_context,
            negative_eps=negative_eps,
        )
        if negative_state == PricingState.FOUND_NEGATIVE:
            added_new = False
            for column in negative_columns:
                signature = column_signature_from_journey(column)
                pattern = _journey_forbidden_arc_pattern(column)
                task_set = _journey_forbidden_task_set(column)
                pattern_added = False
                task_set_added = False
                if no_good_scope in {"arc", "arc_and_task_set"} and pattern and pattern not in seen_patterns:
                    seen_patterns.add(pattern)
                    forbidden_patterns.append(pattern)
                    pattern_added = True
                if no_good_scope in {"task_set", "arc_and_task_set"} and task_set and task_set not in seen_task_sets:
                    seen_task_sets.add(task_set)
                    forbidden_task_sets.append(task_set)
                    task_set_added = True
                if not (pattern_added or task_set_added):
                    continue
                batch_negative_columns.append(column)
                pricing_rc = _compact_result_pricing_rc_for_column(negative_result, column_count=len(negative_columns))
                if pricing_rc is not None:
                    batch_pricing_rc_by_signature[signature] = pricing_rc
                added_new = True
            if added_new:
                continue
            break
        if negative_state == PricingState.CERTIFIED_NO_NEGATIVE and not batch_negative_columns:
            return _compact_final_judge_result(
                data,
                context=context,
                branch_context=branch_context,
                cut_context=cut_context,
                result=negative_result,
                state=negative_state,
                negative_columns=tuple(),
                can_certify=negative_can_certify,
                started_at=start,
                phase="negative_feasibility_search",
                phase_payloads=phase_payloads,
                profile=profile,
                phase_mode=phase_mode,
            )
        break

    if batch_negative_columns:
        harvest_payload = _compact_negative_harvest_payload(
            batch_negative_columns,
            duals,
            cut_context,
            negative_eps=negative_eps,
            candidate_negative_count=len(batch_negative_columns),
            max_selected=batch_target,
            pricing_rc_by_signature=batch_pricing_rc_by_signature,
            column_pool=column_pool,
            master_view=master_view,
            node_id=node_id,
            active_task_sets=active_task_sets,
            branch_context=branch_context,
        )
        selected_columns = tuple(harvest_payload.pop("_selected_columns"))
        manual_rc_values = tuple(_manual_reduced_cost(column, duals, cut_context) for column in selected_columns)
        manual_best = min(manual_rc_values) if manual_rc_values else None
        result = dict(last_negative_result or {})
        if not selected_columns:
            result.update(
                {
                    "status": "COMPACT_HIGHS_PRICING_BATCH_NO_ADDABLE_NEGATIVE",
                    "algorithm_status": "COMPACT_HIGHS_PRICING_BATCH_NO_ADDABLE_NEGATIVE",
                    "exact_status": "NOT_SOLVED",
                    "pricing_state": PricingState.INCOMPLETE_LIMIT.value,
                    "negative_found": True,
                    "negative_column_count": 0,
                    "can_certify_no_negative": False,
                    "uses_true_dual_bpc_certificate": False,
                    "pricing_rc_audit_pass": True,
                    "journeys": tuple(),
                    "journey_count": 0,
                    "compact_negative_batch_enabled": True,
                    "compact_negative_batch_target": batch_target,
                    "compact_negative_no_good_scope": no_good_scope,
                    "compact_negative_search_cap_sec": negative_search_cap,
                    "compact_negative_batch_found_count": 0,
                    "compact_negative_batch_search_call_count": len(phase_payloads),
                    "forbidden_arc_pattern_count": len(forbidden_patterns),
                    "forbidden_arc_patterns_can_certify_full_space": False,
                    "forbidden_task_set_count": len(forbidden_task_sets),
                    "forbidden_task_sets_can_certify_full_space": False,
                    "wall_time_sec": round(perf_counter() - start, 6),
                    "note": (
                        "Compact final judge found true negative candidates, but harvesting "
                        "rejected all of them as non-addable. This cannot advance the master "
                        "and cannot certify no-negative, so the runner falls through to the "
                        "unrestricted proof phase when time remains."
                    ),
                    **harvest_payload,
                }
            )
            last_negative_result = result
        else:
            result.update(
                {
                    "status": "COMPACT_HIGHS_PRICING_BATCH_FOUND_NEGATIVE",
                    "algorithm_status": "COMPACT_HIGHS_PRICING_BATCH_FOUND_NEGATIVE",
                    "exact_status": "NOT_SOLVED",
                    "pricing_state": PricingState.FOUND_NEGATIVE.value,
                    "best_reduced_cost": None if manual_best is None else round(float(manual_best), 9),
                    "manual_best_reduced_cost": None if manual_best is None else round(float(manual_best), 9),
                    "pricing_best_reduced_cost": None if manual_best is None else round(float(manual_best), 9),
                    "negative_found": True,
                    "negative_column_count": len(selected_columns),
                    "can_certify_no_negative": False,
                    "uses_true_dual_bpc_certificate": False,
                    "pricing_rc_audit_pass": True,
                    "journeys": selected_columns,
                    "journey_count": len(selected_columns),
                    "has_feasible_incumbent": True,
                    "compact_negative_batch_enabled": True,
                    "compact_negative_batch_target": batch_target,
                    "compact_negative_no_good_scope": no_good_scope,
                    "compact_negative_search_cap_sec": negative_search_cap,
                    "compact_negative_batch_found_count": len(selected_columns),
                    "compact_negative_batch_search_call_count": len(phase_payloads),
                    "forbidden_arc_pattern_count": len(forbidden_patterns),
                    "forbidden_arc_patterns_can_certify_full_space": False,
                    "forbidden_task_set_count": len(forbidden_task_sets),
                    "forbidden_task_sets_can_certify_full_space": False,
                    "wall_time_sec": round(perf_counter() - start, 6),
                    "note": (
                        "Compact final judge used restricted negative-feasibility discovery to return "
                        "multiple audited negative columns. Restricted discovery is not a no-negative "
                        "certificate; a later unrestricted proof phase is still required for closure."
                    ),
                    **harvest_payload,
                }
            )
            return _compact_final_judge_result(
                data,
                context=context,
                branch_context=branch_context,
                cut_context=cut_context,
                result=result,
                state=PricingState.FOUND_NEGATIVE,
                negative_columns=selected_columns,
                can_certify=False,
                started_at=start,
                phase="negative_feasibility_batch",
                phase_payloads=phase_payloads,
                profile=profile,
                phase_mode=phase_mode,
            )

    remaining = _remaining_compact_time(wall_time_limit_sec, started_at=start)
    if remaining is None or remaining > 0.25:
        result = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=remaining,
            threads=compact_pricing_threads,
            mip_gap=0.0,
            negative_eps=negative_eps,
            mtz_connectivity=bool(profile["proof_mtz_connectivity"]),
            mtz_endpoint_order_cuts=bool(mtz_endpoint_order_cuts),
            pair_adjacency_cuts=bool(pair_adjacency_cuts),
            latest_service_start_slot_bound=bool(profile["latest_service_start_slot_bound"]),
            time_window_arc_pruning=bool(profile["time_window_arc_pruning"]),
            resource_arc_pruning=bool(resource_arc_pruning),
            slot_task_time_pruning=bool(profile["slot_task_time_pruning"]),
            slot_arc_support_pruning=bool(slot_arc_support_pruning),
            slot_sequence_capacity_arc_pruning=bool(slot_sequence_capacity_arc_pruning),
            recharge_aware_slot_bound=bool(recharge_aware_slot_bound),
            objective_bound_no_negative_cutoff=bool(objective_bound_no_negative_cutoff),
            zero_capacity_slot_truncation=bool(zero_capacity_slot_truncation),
            slot_sequence_capacity_live_bound=bool(slot_sequence_capacity_live_bound),
            tight_service_start_bounds=bool(tight_service_start_bounds),
            tight_time_arc_big_m=bool(tight_time_arc_big_m),
            slot_service_start_y_lower_bound=bool(slot_service_start_y_lower_bound),
            dual_task_slot_full_space_lower_bound=bool(dual_task_slot_full_space_lower_bound),
            dual_task_slot_full_space_lb_time_limit_sec=float(
                dual_task_slot_full_space_lb_time_limit_sec
            ),
            dual_task_slot_full_space_lb_early_stop_on_negative=bool(
                dual_task_slot_full_space_lb_early_stop_on_negative
            ),
            sortie_slot_position_bounds=sortie_slot_position_bounds,
            service_start_depot_travel_lb=service_start_depot_travel_lb,
            task_to_depot_return_travel_lb=task_to_depot_return_travel_lb,
            pair_route_duration_lb=pair_route_duration_lb,
            pair_weighted_completion_lb=pair_weighted_completion_lb,
            demand_cover_cut=demand_cover_cut,
            single_task_energy_lb=single_task_energy_lb,
            single_task_shadow_lb=single_task_shadow_lb,
            pair_energy_lb=pair_energy_lb,
            pair_shadow_lb=pair_shadow_lb,
            pair_energy_infeasible_cut=pair_energy_infeasible_cut,
            pair_time_window_infeasible_cut=pair_time_window_infeasible_cut,
            pair_time_window_precedence_cut=pair_time_window_precedence_cut,
            triple_time_window_infeasible_cut=triple_time_window_infeasible_cut,
            quad_time_window_infeasible_cut=quad_time_window_infeasible_cut,
            pair_shadow_infeasible_cut=pair_shadow_infeasible_cut,
            triple_shadow_infeasible_cut=triple_shadow_infeasible_cut,
            triple_energy_infeasible_cut=triple_energy_infeasible_cut,
            task_slot_pair_conflict_capacity_bound=bool(
                task_slot_pair_conflict_capacity_bound
            ),
            mip_start_journey=proof_mip_start_journey,
            mip_start_zero_fill_integers=bool(mip_start_zero_fill_integers),
            mip_start_inactive_tail_time=bool(mip_start_inactive_tail_time),
            mip_start_inactive_tail_time_mode=str(mip_start_inactive_tail_time_mode),
        )
        result = _with_compact_profile_payload(result, profile)
        state, negative_columns, can_certify = _compact_result_state(
            result,
            duals,
            cut_context,
            negative_eps=negative_eps,
        )
        if state == PricingState.FOUND_NEGATIVE and optimization_harvest_target > 1:
            optimization_columns: list[JourneyColumn] = list(negative_columns)
            optimization_pricing_rc_by_signature: dict[object, float] = {}
            for column in negative_columns:
                signature = column_signature_from_journey(column)
                pricing_rc = _compact_result_pricing_rc_for_column(result, column_count=len(negative_columns))
                if pricing_rc is not None:
                    optimization_pricing_rc_by_signature[signature] = pricing_rc
                pattern = _journey_forbidden_arc_pattern(column)
                task_set = _journey_forbidden_task_set(column)
                if (
                    optimization_harvest_no_good_scope in {"arc", "arc_and_task_set"}
                    and pattern
                    and pattern not in seen_patterns
                ):
                    seen_patterns.add(pattern)
                    forbidden_patterns.append(pattern)
                if (
                    optimization_harvest_no_good_scope in {"task_set", "arc_and_task_set"}
                    and task_set
                    and task_set not in seen_task_sets
                ):
                    seen_task_sets.add(task_set)
                    forbidden_task_sets.append(task_set)
            optimization_phase_payloads = {
                **phase_payloads,
                "optimization_proof": _compact_phase_summary(result),
            }
            for harvest_index in range(2, optimization_harvest_target + 1):
                remaining_for_harvest = _remaining_compact_time(wall_time_limit_sec, started_at=start)
                if remaining_for_harvest is not None and remaining_for_harvest <= 0.25:
                    break
                restricted_result = solve_highs_compact_single_journey_pricing(
                    data,
                    duals,
                    time_limit_sec=remaining_for_harvest,
                    threads=compact_pricing_threads,
                    mip_gap=0.0,
                    negative_eps=negative_eps,
                    mtz_connectivity=bool(profile["proof_mtz_connectivity"]),
                    mtz_endpoint_order_cuts=bool(mtz_endpoint_order_cuts),
                    pair_adjacency_cuts=bool(pair_adjacency_cuts),
                    latest_service_start_slot_bound=bool(profile["latest_service_start_slot_bound"]),
                    time_window_arc_pruning=bool(profile["time_window_arc_pruning"]),
                    resource_arc_pruning=bool(resource_arc_pruning),
                    slot_task_time_pruning=bool(profile["slot_task_time_pruning"]),
                    slot_arc_support_pruning=bool(slot_arc_support_pruning),
                    slot_sequence_capacity_arc_pruning=bool(slot_sequence_capacity_arc_pruning),
                    recharge_aware_slot_bound=bool(recharge_aware_slot_bound),
                    objective_bound_no_negative_cutoff=bool(objective_bound_no_negative_cutoff),
                    zero_capacity_slot_truncation=bool(zero_capacity_slot_truncation),
                    slot_sequence_capacity_live_bound=bool(slot_sequence_capacity_live_bound),
                    tight_service_start_bounds=bool(tight_service_start_bounds),
                    tight_time_arc_big_m=bool(tight_time_arc_big_m),
                    slot_service_start_y_lower_bound=bool(slot_service_start_y_lower_bound),
                    dual_task_slot_full_space_lower_bound=bool(dual_task_slot_full_space_lower_bound),
                    dual_task_slot_full_space_lb_time_limit_sec=float(
                        dual_task_slot_full_space_lb_time_limit_sec
                    ),
                    dual_task_slot_full_space_lb_early_stop_on_negative=bool(
                        dual_task_slot_full_space_lb_early_stop_on_negative
                    ),
                    sortie_slot_position_bounds=sortie_slot_position_bounds,
                    service_start_depot_travel_lb=service_start_depot_travel_lb,
                    task_to_depot_return_travel_lb=task_to_depot_return_travel_lb,
                    pair_route_duration_lb=pair_route_duration_lb,
                    pair_weighted_completion_lb=pair_weighted_completion_lb,
                    demand_cover_cut=demand_cover_cut,
                    single_task_energy_lb=single_task_energy_lb,
                    single_task_shadow_lb=single_task_shadow_lb,
                    pair_energy_lb=pair_energy_lb,
                    pair_shadow_lb=pair_shadow_lb,
                    pair_energy_infeasible_cut=pair_energy_infeasible_cut,
                    pair_time_window_infeasible_cut=pair_time_window_infeasible_cut,
                    pair_time_window_precedence_cut=pair_time_window_precedence_cut,
                    triple_time_window_infeasible_cut=triple_time_window_infeasible_cut,
                    quad_time_window_infeasible_cut=quad_time_window_infeasible_cut,
                    pair_shadow_infeasible_cut=pair_shadow_infeasible_cut,
                    triple_shadow_infeasible_cut=triple_shadow_infeasible_cut,
                    triple_energy_infeasible_cut=triple_energy_infeasible_cut,
                    task_slot_pair_conflict_capacity_bound=bool(
                        task_slot_pair_conflict_capacity_bound
                    ),
                    forbidden_arc_patterns=tuple(forbidden_patterns),
                    forbidden_task_sets=tuple(forbidden_task_sets),
                    mip_start_journey=proof_mip_start_journey,
                    mip_start_zero_fill_integers=bool(mip_start_zero_fill_integers),
                    mip_start_inactive_tail_time=bool(mip_start_inactive_tail_time),
                    mip_start_inactive_tail_time_mode=str(mip_start_inactive_tail_time_mode),
                )
                restricted_result = _with_compact_profile_payload(restricted_result, profile)
                optimization_phase_payloads[f"optimization_harvest_{harvest_index}"] = _compact_phase_summary(
                    restricted_result
                )
                restricted_state, restricted_negative_columns, _restricted_can_certify = _compact_result_state(
                    restricted_result,
                    duals,
                    cut_context,
                    negative_eps=negative_eps,
                )
                if restricted_state != PricingState.FOUND_NEGATIVE:
                    break
                added_new = False
                for column in restricted_negative_columns:
                    signature = column_signature_from_journey(column)
                    pattern = _journey_forbidden_arc_pattern(column)
                    task_set = _journey_forbidden_task_set(column)
                    pattern_added = False
                    task_set_added = False
                    if (
                        optimization_harvest_no_good_scope in {"arc", "arc_and_task_set"}
                        and pattern
                        and pattern not in seen_patterns
                    ):
                        seen_patterns.add(pattern)
                        forbidden_patterns.append(pattern)
                        pattern_added = True
                    if (
                        optimization_harvest_no_good_scope in {"task_set", "arc_and_task_set"}
                        and task_set
                        and task_set not in seen_task_sets
                    ):
                        seen_task_sets.add(task_set)
                        forbidden_task_sets.append(task_set)
                        task_set_added = True
                    if not (pattern_added or task_set_added):
                        continue
                    optimization_columns.append(column)
                    pricing_rc = _compact_result_pricing_rc_for_column(
                        restricted_result,
                        column_count=len(restricted_negative_columns),
                    )
                    if pricing_rc is not None:
                        optimization_pricing_rc_by_signature[signature] = pricing_rc
                    added_new = True
                if not added_new:
                    break
            harvest_payload = _compact_negative_harvest_payload(
                optimization_columns,
                duals,
                cut_context,
                negative_eps=negative_eps,
                candidate_negative_count=len(optimization_columns),
                max_selected=optimization_harvest_target,
                source_phase="compact_final_judge_optimization_harvest",
                pricing_rc_by_signature=optimization_pricing_rc_by_signature,
                column_pool=column_pool,
                master_view=master_view,
                node_id=node_id,
                active_task_sets=active_task_sets,
                branch_context=branch_context,
            )
            selected_columns = tuple(harvest_payload.pop("_selected_columns"))
            if selected_columns:
                manual_rc_values = tuple(_manual_reduced_cost(column, duals, cut_context) for column in selected_columns)
                manual_best = min(manual_rc_values)
                result = dict(result)
                result.update(
                    {
                        "status": "COMPACT_HIGHS_PRICING_OPTIMIZATION_HARVEST_FOUND_NEGATIVE",
                        "algorithm_status": "COMPACT_HIGHS_PRICING_OPTIMIZATION_HARVEST_FOUND_NEGATIVE",
                        "exact_status": "NOT_SOLVED",
                        "pricing_state": PricingState.FOUND_NEGATIVE.value,
                        "best_reduced_cost": round(float(manual_best), 9),
                        "manual_best_reduced_cost": round(float(manual_best), 9),
                        "pricing_best_reduced_cost": round(float(manual_best), 9),
                        "negative_found": True,
                        "negative_column_count": len(selected_columns),
                        "can_certify_no_negative": False,
                        "uses_true_dual_bpc_certificate": False,
                        "pricing_rc_audit_pass": bool(harvest_payload.get("harvest_pricing_rc_audit_pass")),
                        "journeys": selected_columns,
                        "journey_count": len(selected_columns),
                        "has_feasible_incumbent": True,
                        "compact_optimization_harvest_enabled": True,
                        "compact_optimization_harvest_target": int(optimization_harvest_target),
                        "compact_optimization_harvest_no_good_scope": optimization_harvest_no_good_scope,
                        "compact_optimization_harvest_found_count": len(selected_columns),
                        "compact_optimization_harvest_search_call_count": len(
                            [key for key in optimization_phase_payloads if str(key).startswith("optimization")]
                        ),
                        "compact_negative_no_good_scope": no_good_scope,
                        "restricted_harvest_can_certify_no_negative": False,
                        "forbidden_arc_pattern_count": len(forbidden_patterns),
                        "forbidden_arc_patterns_can_certify_full_space": False,
                        "forbidden_task_set_count": len(forbidden_task_sets),
                        "forbidden_task_sets_can_certify_full_space": False,
                        "wall_time_sec": round(perf_counter() - start, 6),
                        "note": (
                            "Compact final judge used unrestricted optimization proof followed by "
                            "restricted no-good optimization harvest. Restricted harvest rows are "
                            "candidate discovery only and cannot certify no-negative."
                        ),
                        **harvest_payload,
                    }
                )
                return _compact_final_judge_result(
                    data,
                    context=context,
                    branch_context=branch_context,
                    cut_context=cut_context,
                    result=result,
                    state=PricingState.FOUND_NEGATIVE,
                    negative_columns=selected_columns,
                    can_certify=False,
                    started_at=start,
                    phase="optimization_harvest",
                    phase_payloads=optimization_phase_payloads,
                    profile=profile,
                    phase_mode=phase_mode,
                )
        return _compact_final_judge_result(
            data,
            context=context,
            branch_context=branch_context,
            cut_context=cut_context,
            result=result,
            state=state,
            negative_columns=negative_columns,
            can_certify=can_certify,
            started_at=start,
            phase="optimization_proof",
            phase_payloads={
                **phase_payloads,
                "optimization_proof": _compact_phase_summary(result),
            },
            profile=profile,
            phase_mode=phase_mode,
        )

    return _compact_final_judge_result(
        data,
        context=context,
        branch_context=branch_context,
        cut_context=cut_context,
        result=last_negative_result or {},
        state=PricingState.INCOMPLETE_LIMIT,
        negative_columns=tuple(),
        can_certify=False,
        started_at=start,
        phase="negative_feasibility_search",
        phase_payloads=phase_payloads,
        profile=profile,
        phase_mode=phase_mode,
    )


def _remaining_compact_time(wall_time_limit_sec: float | None, *, started_at: float) -> float | None:
    if wall_time_limit_sec is None:
        return None
    return max(0.001, float(wall_time_limit_sec) - (perf_counter() - float(started_at)))


def _pricing_state_from_payload(value: object) -> PricingState:
    try:
        return PricingState(str(value))
    except ValueError:
        return PricingState.INCOMPLETE_LIMIT


def _labeling_final_judge_mode(value: bool | None) -> tuple[str, str]:
    """Return enabled/disabled/auto for the labeling final-judge switch."""

    if value is not None:
        return ("enabled" if bool(value) else "disabled", "explicit_parameter")
    raw = os.environ.get(LABELING_FINAL_JUDGE_ENV)
    if raw in {None, ""}:
        return ("disabled", "environment_or_default")
    normalized = str(raw).strip().lower()
    if normalized in LABELING_FINAL_JUDGE_AUTO_VALUES:
        return ("auto", "environment_auto")
    return ("enabled" if _env_bool(LABELING_FINAL_JUDGE_ENV, default=False) else "disabled", "environment")


def _labeling_final_judge_max_exact_tasks(
    *,
    max_direct_tasks: int,
    max_exact_tasks_override: int | None,
) -> int:
    if max_exact_tasks_override is not None:
        return max(1, min(64, int(max_exact_tasks_override)))
    return _env_int(
        LABELING_FINAL_JUDGE_MAX_TASKS_ENV,
        default=int(max_direct_tasks),
        minimum=1,
        maximum=64,
    )


def _labeling_final_judge_exact_harvest_target(
    *,
    exact_harvest_target_override: int | None,
) -> int:
    if exact_harvest_target_override is not None:
        return max(1, min(32, int(exact_harvest_target_override)))
    return _env_int(
        LABELING_FINAL_JUDGE_EXACT_HARVEST_TARGET_ENV,
        default=1,
        minimum=1,
        maximum=32,
    )


def _env_int(name: str, *, default: int, minimum: int, maximum: int) -> int:
    raw = os.environ.get(str(name))
    try:
        value = int(raw) if raw not in {None, ""} else int(default)
    except (TypeError, ValueError):
        value = int(default)
    return max(int(minimum), min(int(maximum), int(value)))


def _env_float(name: str, *, default: float, minimum: float, maximum: float) -> float:
    raw = os.environ.get(str(name))
    try:
        value = float(raw) if raw not in {None, ""} else float(default)
    except (TypeError, ValueError):
        value = float(default)
    return max(float(minimum), min(float(maximum), float(value)))


def _env_choice(name: str, *, default: str, choices: set[str]) -> str:
    raw = os.environ.get(str(name))
    value = str(raw).strip().lower() if raw not in {None, ""} else str(default)
    return value if value in choices else str(default)


def _env_bool(name: str, *, default: bool) -> bool:
    raw = os.environ.get(str(name))
    if raw in {None, ""}:
        return bool(default)
    value = str(raw).strip().lower()
    if value in {"1", "true", "yes", "on", "enabled", "enable"}:
        return True
    if value in {"0", "false", "no", "off", "disabled", "disable"}:
        return False
    return bool(default)


def _compact_final_judge_profile_from_env() -> dict:
    raw = os.environ.get(COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PROFILE_ENV)
    value = str(raw or "B4V2").strip().upper()
    aliases = {
        "": "B4V2",
        "DEFAULT": "B4V2",
        "V2": "B4V2",
        "B4V2": "B4V2",
        "LATEST_START": "B4V2",
        "LATEST_START_ONLY": "B4V2",
        "V4": "V4",
        "B4V4": "V4",
        "COMBINED": "V4",
        "B4V4_COMBINED": "V4",
        "V4S": "V4S",
        "B4V4S": "V4S",
        "V4_STRONG": "V4S",
        "V4_STRONG_TAIL": "V4S",
        "V4_STRENGTHENED": "V4S",
        "B4V4_STRENGTHENED": "V4S",
        "PAIR_WEIGHTED": "V4S",
        "PAIR_WEIGHTED_FINAL_TAIL": "V4S",
        "STRENGTHENED_FINAL_TAIL": "V4S",
        "V4SR": "V4SR",
        "B4V4SR": "V4SR",
        "V4S_RECHARGE": "V4SR",
        "V4S_RECHARGE_SLOT": "V4SR",
        "RECHARGE_SLOT": "V4SR",
        "STRENGTHENED_RECHARGE_SLOT": "V4SR",
        "V4SC": "V4SC",
        "B4V4SC": "V4SC",
        "V4S_CUTOFF": "V4SC",
        "V4S_OBJECTIVE_BOUND": "V4SC",
        "OBJECTIVE_BOUND_CUTOFF": "V4SC",
        "STRENGTHENED_OBJECTIVE_BOUND": "V4SC",
        "V4SZ": "V4SZ",
        "B4V4SZ": "V4SZ",
        "V4S_ZERO_SLOT": "V4SZ",
        "V4S_ZERO_CAPACITY_SLOT": "V4SZ",
        "ZERO_CAPACITY_SLOT": "V4SZ",
        "STRENGTHENED_ZERO_CAPACITY_SLOT": "V4SZ",
        "V4SZW": "V4SZW",
        "B4V4SZW": "V4SZW",
        "V4S_ZERO_SLOT_WARM": "V4SZW",
        "V4S_ZERO_CAPACITY_SLOT_WARM": "V4SZW",
        "ZERO_CAPACITY_SLOT_WARM_INTEGER_START": "V4SZW",
        "WARM_INTEGER_START": "V4SZW",
        "V4SZCAP": "V4SZCAP",
        "B4V4SZCAP": "V4SZCAP",
        "V4S_ZERO_SLOT_CAPACITY_ARC": "V4SZCAP",
        "ZERO_CAPACITY_SLOT_SEQUENCE_CAPACITY_ARC": "V4SZCAP",
        "SLOT_SEQUENCE_CAPACITY_ARC_PRUNING": "V4SZCAP",
        "V4SZPC": "V4SZPC",
        "B4V4SZPC": "V4SZPC",
        "V4S_ZERO_SLOT_PAIR_CONFLICT_CAPACITY": "V4SZPC",
        "PAIR_CONFLICT_CAPACITY_BOUND": "V4SZPC",
        "TASK_SLOT_PAIR_CONFLICT_CAPACITY_BOUND": "V4SZPC",
        "V4SL": "V4SL",
        "B4V4SL": "V4SL",
        "V4S_LIVE_SLOT_CAPACITY": "V4SL",
        "V4S_SLOT_SEQUENCE_LIVE_BOUND": "V4SL",
        "SLOT_SEQUENCE_LIVE_BOUND": "V4SL",
        "STRENGTHENED_SLOT_SEQUENCE_LIVE_BOUND": "V4SL",
        "V4ST": "V4ST",
        "B4V4ST": "V4ST",
        "V4S_TIGHT_SERVICE_START": "V4ST",
        "V4S_TIGHT_SERVICE_START_BOUNDS": "V4ST",
        "TIGHT_SERVICE_START": "V4ST",
        "TIGHT_SERVICE_START_BOUNDS": "V4ST",
        "STRENGTHENED_TIGHT_SERVICE_START_BOUNDS": "V4ST",
        "V4SZT": "V4SZT",
        "B4V4SZT": "V4SZT",
        "V4S_ZERO_SLOT_TIGHT_TIME": "V4SZT",
        "ZERO_CAPACITY_SLOT_TIGHT_TIME": "V4SZT",
        "TIGHT_TIME_BIG_M": "V4SZT",
        "ZERO_SLOT_TIGHT_TIME_BIG_M": "V4SZT",
        "V4SZTP": "V4SZTP",
        "B4V4SZTP": "V4SZTP",
        "V4SZT_PROOF": "V4SZTP",
        "V4SZT_PROOF_ONLY": "V4SZTP",
        "ZERO_SLOT_TIGHT_TIME_PROOF": "V4SZTP",
        "ZERO_SLOT_TIGHT_TIME_PROOF_ONLY": "V4SZTP",
        "V4SH": "V4SH",
        "B4V4SH": "V4SH",
        "V4S_HARVEST": "V4SH",
        "V4S_SEED_HARVEST": "V4SH",
        "SEED_HARVEST": "V4SH",
        "ROUTE_TEMPLATE_HARVEST": "V4SH",
        "STRENGTHENED_SEED_HARVEST": "V4SH",
    }
    key = aliases.get(value, "B4V2")
    return dict(COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PROFILES[key])


def _compact_final_judge_phase_mode_from_env(
    *,
    default: str = COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_DEFAULT,
) -> str:
    raw = os.environ.get(COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_ENV)
    value = str(raw if raw is not None else default).strip().lower()
    aliases = {
        "": COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_DEFAULT,
        "default": COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_DEFAULT,
        "harvest": COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_DEFAULT,
        "harvest_then_proof": COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_DEFAULT,
        "negative_then_proof": COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_DEFAULT,
        "proof": "proof_only",
        "proof_only": "proof_only",
        "optimization_proof": "proof_only",
        "feasibility_proof": "feasibility_proof_only",
        "feasibility_proof_only": "feasibility_proof_only",
        "negative_feasibility_proof": "feasibility_proof_only",
        "negative_feasibility_proof_only": "feasibility_proof_only",
    }
    return aliases.get(value, COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_DEFAULT)


def _compact_profile_payload(profile: dict) -> dict:
    return {
        "compact_final_judge_profile": str(profile["name"]),
        "compact_final_judge_formulation_profile": str(profile["formulation_profile"]),
        "compact_final_judge_profile_env": COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PROFILE_ENV,
        "compact_final_judge_threads_env": COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_THREADS_ENV,
        "compact_final_judge_threads": int(profile.get("compact_final_judge_threads") or 1),
        "compact_final_judge_profile_official_default": bool(profile["official_default"]),
        "compact_final_judge_profile_phase_mode_default": str(
            profile.get(
                "phase_mode_default",
                COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_DEFAULT,
            )
        ),
        "compact_final_judge_profile_resource_arc_pruning": bool(profile.get("resource_arc_pruning")),
        "compact_final_judge_profile_slot_arc_support_pruning": bool(
            profile.get("slot_arc_support_pruning")
        ),
        "compact_final_judge_profile_proof_mtz_connectivity": bool(
            profile.get("proof_mtz_connectivity")
        ),
        "compact_final_judge_profile_sortie_slot_position_bounds": bool(
            profile.get("sortie_slot_position_bounds")
        ),
        "compact_final_judge_profile_pair_weighted_completion_lb": bool(
            profile.get("pair_weighted_completion_lb")
        ),
        "compact_final_judge_profile_pair_energy_infeasible_cut": bool(
            profile.get("pair_energy_infeasible_cut")
        ),
        "compact_final_judge_profile_pair_time_window_infeasible_cut": bool(
            profile.get("pair_time_window_infeasible_cut")
        ),
        "compact_final_judge_profile_pair_shadow_infeasible_cut": bool(
            profile.get("pair_shadow_infeasible_cut")
        ),
        "compact_final_judge_profile_recharge_aware_slot_bound": bool(
            profile.get("recharge_aware_slot_bound")
        ),
        "compact_final_judge_profile_objective_bound_no_negative_cutoff": bool(
            profile.get("objective_bound_no_negative_cutoff")
        ),
        "compact_final_judge_profile_zero_capacity_slot_truncation": bool(
            profile.get("zero_capacity_slot_truncation")
        ),
        "compact_final_judge_profile_slot_sequence_capacity_arc_pruning": bool(
            profile.get("slot_sequence_capacity_arc_pruning")
        ),
        "compact_final_judge_profile_task_slot_pair_conflict_capacity_bound": bool(
            profile.get("task_slot_pair_conflict_capacity_bound")
        ),
        "compact_final_judge_profile_mip_start_zero_fill_integers": bool(
            profile.get("mip_start_zero_fill_integers")
        ),
        "compact_final_judge_profile_mip_start_inactive_tail_time": bool(
            profile.get("mip_start_inactive_tail_time")
        ),
        "compact_final_judge_profile_mip_start_inactive_tail_time_mode": str(
            profile.get("mip_start_inactive_tail_time_mode", "")
        ),
        "compact_final_judge_profile_slot_sequence_capacity_live_bound": bool(
            profile.get("slot_sequence_capacity_live_bound")
        ),
        "compact_final_judge_profile_tight_service_start_bounds": bool(
            profile.get("tight_service_start_bounds")
        ),
        "compact_final_judge_profile_tight_time_arc_big_m": bool(
            profile.get("tight_time_arc_big_m")
        ),
        "compact_final_judge_profile_slot_service_start_y_lower_bound": bool(
            profile.get("slot_service_start_y_lower_bound")
        ),
        "compact_final_judge_profile_route_template_pre_harvest": bool(
            profile.get("route_template_pre_harvest_enabled")
        ),
        "compact_final_judge_profile_route_template_pre_harvest_target": int(
            profile.get("route_template_pre_harvest_target") or 0
        ),
        "compact_final_judge_profile_route_template_pre_harvest_time_cap_sec": float(
            profile.get("route_template_pre_harvest_time_cap_sec") or 0.0
        ),
        "compact_final_judge_mip_start_from_column_pool": bool(profile.get("mip_start_from_column_pool")),
    }


def _with_compact_profile_payload(result: dict, profile: dict) -> dict:
    merged = dict(result)
    merged.update(_compact_profile_payload(profile))
    return merged


def _compact_mip_start_journey_from_pool(
    column_pool: ColumnPool | None,
    duals: JourneyDuals,
    cut_context: CutContext,
    branch_context: BranchContext,
) -> JourneyColumn | None:
    if column_pool is None:
        return None
    if not cut_context.empty:
        # Compact single-journey pricing currently has no live cut-dual terms.
        # A warm start is only a hint, but keeping it off under active cuts makes
        # the telemetry unambiguous while live cut pricing remains diagnostic.
        return None
    candidates: list[tuple[float, tuple[str, ...], float, JourneyColumn]] = []
    for bpc_column in column_pool.columns_by_signature.values():
        column = bpc_column.payload
        if not isinstance(column, JourneyColumn):
            continue
        if not journey_satisfies_branch_context(column, branch_context):
            continue
        true_rc = _manual_reduced_cost(column, duals, cut_context)
        candidates.append(
            (
                float(true_rc),
                tuple(sorted(str(task_id) for task_id in column.task_set)),
                float(column.objective),
                column,
            )
        )
    if not candidates:
        return None
    candidates.sort(key=lambda row: (row[0], row[1], row[2]))
    return candidates[0][3]


def _run_route_template_pre_harvest(
    data: LunarIceData,
    duals: JourneyDuals,
    cut_context: CutContext,
    *,
    branch_context: BranchContext,
    negative_eps: float,
    started_at: float,
    wall_time_limit_sec: float | None,
    time_cap_sec: float,
    max_direct_tasks: int,
    max_active_seeds: int,
    neighborhood_enabled: bool,
    max_neighborhood_seeds: int,
    max_candidate_sets: int,
    harvest_target: int,
    column_pool: ColumnPool | None,
    master_view: MasterColumnView | None,
    node_id: str,
    active_task_sets: set[frozenset[str]] | None,
) -> dict:
    phase_start = perf_counter()
    remaining = _remaining_compact_time(wall_time_limit_sec, started_at=started_at)
    if remaining is not None and remaining <= 0.05:
        return _route_template_pre_harvest_payload(
            status="ROUTE_TEMPLATE_PRE_HARVEST_SKIPPED_NO_TIME",
            phase_start=phase_start,
            max_direct_tasks=max_direct_tasks,
            max_active_seeds=max_active_seeds,
            neighborhood_enabled=neighborhood_enabled,
            max_neighborhood_seeds=max_neighborhood_seeds,
            max_candidate_sets=max_candidate_sets,
            harvest_target=harvest_target,
            time_cap_sec=0.0,
            seed_task_sets=tuple(),
            pricing_payload={},
            selected_columns=tuple(),
            harvest_payload={},
            note="No time remained before compact proof; route-template pre-harvest skipped.",
        )
    budget = float(time_cap_sec) if remaining is None else min(float(time_cap_sec), max(0.001, float(remaining)))
    seed_task_sets = _route_template_pre_harvest_seed_task_sets(
        data,
        duals,
        cut_context,
        branch_context=branch_context,
        column_pool=column_pool,
        max_direct_tasks=max_direct_tasks,
        max_active_seeds=max_active_seeds,
        neighborhood_enabled=neighborhood_enabled,
        max_neighborhood_seeds=max_neighborhood_seeds,
    )
    if not seed_task_sets:
        return _route_template_pre_harvest_payload(
            status="ROUTE_TEMPLATE_PRE_HARVEST_SKIPPED_NO_ACTIVE_SEEDS",
            phase_start=phase_start,
            max_direct_tasks=max_direct_tasks,
            max_active_seeds=max_active_seeds,
            neighborhood_enabled=neighborhood_enabled,
            max_neighborhood_seeds=max_neighborhood_seeds,
            max_candidate_sets=max_candidate_sets,
            harvest_target=harvest_target,
            time_cap_sec=budget,
            seed_task_sets=seed_task_sets,
            pricing_payload={},
            selected_columns=tuple(),
            harvest_payload={},
            note="No eligible active column-pool task sets were available for route-template pre-harvest.",
        )
    pricing_payload, priced_columns = price_direct_journey_columns_incremental(
        data,
        duals,
        negative_eps=negative_eps,
        max_direct_tasks=max_direct_tasks,
        seed_task_sets=seed_task_sets,
        max_candidate_sets=max_candidate_sets,
        wall_time_limit_sec=budget,
        stop_at_first_negative=bool(int(harvest_target) <= 1),
        cut_context=cut_context,
        branch_context=branch_context,
    )
    pricing_rc_by_signature = {
        column_signature_from_journey(column): _manual_reduced_cost(column, duals, cut_context)
        for column in priced_columns
    }
    negative_columns = [
        column
        for column in priced_columns
        if _manual_reduced_cost(column, duals, cut_context) < -abs(float(negative_eps))
    ]
    harvest_payload = _compact_negative_harvest_payload(
        list(priced_columns),
        duals,
        cut_context,
        negative_eps=negative_eps,
        candidate_negative_count=len(negative_columns),
        max_selected=harvest_target,
        source_phase="route_template_pre_harvest",
        pricing_rc_by_signature=pricing_rc_by_signature,
        column_pool=column_pool,
        master_view=master_view,
        node_id=node_id,
        active_task_sets=active_task_sets,
        branch_context=branch_context,
    )
    selected_columns = tuple(harvest_payload.pop("_selected_columns"))
    status = (
        "ROUTE_TEMPLATE_PRE_HARVEST_FOUND_NEGATIVE"
        if selected_columns
        else "ROUTE_TEMPLATE_PRE_HARVEST_NO_ADDABLE_NEGATIVE"
        if negative_columns
        else "ROUTE_TEMPLATE_PRE_HARVEST_NO_NEGATIVE_IN_SELECTED_SETS"
    )
    return _route_template_pre_harvest_payload(
        status=status,
        phase_start=phase_start,
        max_direct_tasks=max_direct_tasks,
        max_active_seeds=max_active_seeds,
        neighborhood_enabled=neighborhood_enabled,
        max_neighborhood_seeds=max_neighborhood_seeds,
        max_candidate_sets=max_candidate_sets,
        harvest_target=harvest_target,
        time_cap_sec=budget,
        seed_task_sets=seed_task_sets,
        pricing_payload=pricing_payload,
        selected_columns=selected_columns,
        harvest_payload=harvest_payload,
        note=(
            "Route-template pre-harvest found true-dual audited negative columns from active "
            "column-pool task sets. This is candidate discovery only and cannot certify "
            "no-negative."
            if selected_columns
            else "Route-template pre-harvest did not return an addable negative column; compact "
            "pricing proof must continue for any certificate."
        ),
    )


def _route_template_pre_harvest_payload(
    *,
    status: str,
    phase_start: float,
    max_direct_tasks: int,
    max_active_seeds: int,
    neighborhood_enabled: bool,
    max_neighborhood_seeds: int,
    max_candidate_sets: int,
    harvest_target: int,
    time_cap_sec: float,
    seed_task_sets: tuple[tuple[str, ...], ...],
    pricing_payload: dict,
    selected_columns: tuple[JourneyColumn, ...],
    harvest_payload: dict,
    note: str,
) -> dict:
    manual_best = _optional_float(
        harvest_payload.get("harvest_best_true_rc"),
        pricing_payload.get("best_reduced_cost"),
    )
    return {
        **{key: value for key, value in pricing_payload.items() if key != "journeys"},
        "status": str(status),
        "algorithm_status": str(status),
        "exact_status": "NOT_SOLVED",
        "pricing_state": (
            PricingState.FOUND_NEGATIVE.value
            if selected_columns
            else PricingState.INCOMPLETE_LIMIT.value
        ),
        "best_reduced_cost": None if manual_best is None else round(float(manual_best), 9),
        "manual_best_reduced_cost": None if manual_best is None else round(float(manual_best), 9),
        "pricing_best_reduced_cost": None if manual_best is None else round(float(manual_best), 9),
        "negative_found": bool(selected_columns),
        "negative_column_count": len(selected_columns),
        "can_certify_no_negative": False,
        "uses_true_dual_bpc_certificate": False,
        "pricing_rc_audit_pass": bool(
            harvest_payload.get("harvest_pricing_rc_audit_pass") is True
            if selected_columns
            else True
        ),
        "journeys": selected_columns,
        "journey_count": len(selected_columns),
        "has_feasible_incumbent": bool(selected_columns),
        "route_template_pre_harvest_enabled": True,
        "route_template_pre_harvest_status": str(status),
        "route_template_pre_harvest_time_cap_sec": round(float(time_cap_sec), 6),
        "route_template_pre_harvest_pricing_wall_time_sec": pricing_payload.get("wall_time_sec"),
        "route_template_pre_harvest_max_direct_tasks": int(max_direct_tasks),
        "route_template_pre_harvest_max_active_seeds": int(max_active_seeds),
        "route_template_pre_harvest_neighborhood_enabled": bool(neighborhood_enabled),
        "route_template_pre_harvest_max_neighborhood_seeds": int(max_neighborhood_seeds),
        "route_template_pre_harvest_seed_strategy": (
            "seed_first_active_pool_plus_dual_neighborhood"
            if neighborhood_enabled
            else "seed_first_active_pool_only"
        ),
        "route_template_pre_harvest_max_candidate_sets": int(max_candidate_sets),
        "route_template_pre_harvest_target": int(harvest_target),
        "route_template_pre_harvest_seed_count": len(seed_task_sets),
        "route_template_pre_harvest_candidate_round_count": int(
            pricing_payload.get("candidate_round_count") or 0
        ),
        "route_template_pre_harvest_candidate_round_limit": int(max_candidate_sets),
        "route_template_pre_harvest_candidate_negative_count": int(
            pricing_payload.get("negative_column_count") or harvest_payload.get("harvest_candidate_negative_count") or 0
        ),
        "route_template_pre_harvest_selected_count": len(selected_columns),
        "route_template_pre_harvest_selected_new_task_set_count": int(
            harvest_payload.get("harvest_selected_new_task_set_count") or 0
        ),
        "route_template_pre_harvest_selected_replacement_task_set_count": int(
            harvest_payload.get("harvest_selected_replacement_task_set_count") or 0
        ),
        "route_template_pre_harvest_seed_task_sets": [list(row) for row in seed_task_sets],
        "route_template_pre_harvest_can_certify_no_negative": False,
        "route_template_pre_harvest_fallback_enabled": True,
        "pricing_complete_for_all_tasks": False,
        "pricing_complete_for_all_task_subsets": False,
        "pricing_complete_by_compact_milp": False,
        "pricing_proof_kind": "FRONTIER_BOUND_INCOMPLETE",
        "frontier_unsupported_region_count": 1,
        "global_remaining_rc_lb": None,
        "global_remaining_rc_lb_valid": False,
        "global_remaining_rc_lb_coverage_complete": False,
        "variable_count": 0,
        "constraint_count": 0,
        "solver_backend": "incremental_route_template_direct_label_pricing",
        "wall_time_sec": round(perf_counter() - phase_start, 6),
        "note": str(note),
        **harvest_payload,
    }


def _route_template_pre_harvest_seed_task_sets(
    data: LunarIceData,
    duals: JourneyDuals,
    cut_context: CutContext,
    *,
    branch_context: BranchContext,
    column_pool: ColumnPool | None,
    max_direct_tasks: int,
    max_active_seeds: int,
    neighborhood_enabled: bool,
    max_neighborhood_seeds: int,
) -> tuple[tuple[str, ...], ...]:
    if column_pool is None or int(max_active_seeds) <= 0:
        return tuple()
    task_lookup = {str(task_id) for task_id in data.task_ids}
    rows: list[tuple[float, int, tuple[str, ...], float]] = []
    seen: set[tuple[str, ...]] = set()
    for bpc_column in column_pool.columns_by_signature.values():
        column = bpc_column.payload
        if not isinstance(column, JourneyColumn):
            continue
        if not journey_satisfies_branch_context(column, branch_context):
            continue
        task_set = tuple(sorted(str(task_id) for task_id in column.task_set))
        if (
            not task_set
            or len(task_set) > int(max_direct_tasks)
            or any(task_id not in task_lookup for task_id in task_set)
            or task_set in seen
        ):
            continue
        seen.add(task_set)
        true_rc = _manual_reduced_cost(column, duals, cut_context)
        rows.append((float(true_rc), -len(task_set), task_set, float(column.objective)))
    rows.sort(key=lambda row: (row[0], row[1], row[3], row[2]))
    active_seed_sets = tuple(row[2] for row in rows[: max(0, int(max_active_seeds))])
    if not neighborhood_enabled or int(max_neighborhood_seeds) <= 0:
        return active_seed_sets

    neighborhood_rows: list[tuple[float, int, tuple[str, ...]]] = []
    neighborhood_seen: set[tuple[str, ...]] = set(active_seed_sets)
    ranked_tasks = tuple(
        task_id
        for _score, task_id in sorted(
            (
                (
                    -float(duals.cover.get(str(task_id), 0.0)),
                    str(task_id),
                )
                for task_id in data.task_ids
            ),
            key=lambda row: (row[0], row[1]),
        )
    )
    add_swap_pool = ranked_tasks[: max(1, min(len(ranked_tasks), int(max_direct_tasks) * 2))]

    def add_neighbor(row: tuple[str, ...]) -> None:
        normalized = tuple(sorted(str(task_id) for task_id in row if str(task_id) in task_lookup))
        if (
            not normalized
            or len(normalized) > int(max_direct_tasks)
            or normalized in neighborhood_seen
            or not _task_set_satisfies_branch_context(normalized, branch_context)
        ):
            return
        neighborhood_seen.add(normalized)
        attractiveness = sum(float(duals.cover.get(task_id, 0.0)) for task_id in normalized)
        neighborhood_rows.append((-attractiveness, -len(normalized), normalized))

    for task_set in active_seed_sets:
        current = set(task_set)
        for task_id in task_set:
            if len(task_set) > 1:
                add_neighbor(tuple(sorted(current - {task_id})))
        if len(task_set) < int(max_direct_tasks):
            for task_id in add_swap_pool:
                if task_id not in current:
                    add_neighbor(tuple(sorted((*task_set, task_id))))
        for removed in task_set:
            base = current - {removed}
            for added in add_swap_pool:
                if added not in current:
                    add_neighbor(tuple(sorted((*base, added))))

    neighborhood_rows.sort(key=lambda row: (row[0], row[1], row[2]))
    neighborhood_seed_sets = tuple(row[2] for row in neighborhood_rows[: max(0, int(max_neighborhood_seeds))])
    return (*active_seed_sets, *neighborhood_seed_sets)


def _task_set_satisfies_branch_context(
    task_set: tuple[str, ...],
    branch_context: BranchContext | None,
) -> bool:
    if branch_context is None or branch_context.empty:
        return True
    lookup = set(task_set)
    for decision in branch_context.pair_decisions:
        has_a = str(decision.task_a) in lookup
        has_b = str(decision.task_b) in lookup
        if decision.sense == "same_journey" and has_a != has_b:
            return False
        if decision.sense == "different_journey" and has_a and has_b:
            return False
    return True


def _compact_result_state(
    result: dict,
    duals: JourneyDuals,
    cut_context: CutContext,
    *,
    negative_eps: float,
) -> tuple[PricingState, tuple[JourneyColumn, ...], bool]:
    state = PricingState(str(result.get("pricing_state") or PricingState.INCOMPLETE_LIMIT.value))
    columns = tuple(result.get("journeys") or tuple())
    negative_columns = tuple(
        column
        for column in columns
        if _manual_reduced_cost(column, duals, cut_context) < -abs(float(negative_eps))
    )
    if negative_columns:
        state = PricingState.FOUND_NEGATIVE
    can_certify = bool(
        state == PricingState.CERTIFIED_NO_NEGATIVE
        and result.get("can_certify_no_negative") is True
        and result.get("pricing_rc_audit_pass") is True
    )
    if can_certify:
        state = PricingState.CERTIFIED_NO_NEGATIVE
    elif state == PricingState.CERTIFIED_NO_NEGATIVE:
        state = PricingState.INCOMPLETE_LIMIT
    return state, negative_columns, bool(can_certify)


def _compact_final_judge_result(
    data: LunarIceData,
    *,
    context: ReducedCostContext,
    branch_context: BranchContext,
    cut_context: CutContext,
    result: dict,
    state: PricingState,
    negative_columns: tuple[JourneyColumn, ...],
    can_certify: bool,
    started_at: float,
    phase: str,
    phase_payloads: dict,
    profile: dict | None = None,
    phase_mode: str = COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_DEFAULT,
) -> FinalJudgeResult:
    columns = tuple(result.get("journeys") or tuple())
    pricing_proof_kind = _compact_pricing_proof_kind(result, can_certify=can_certify)
    profile_payload = _compact_profile_payload(profile or _compact_final_judge_profile_from_env())
    global_remaining_rc_lb = _first_float(
        result.get("global_remaining_rc_lb"),
        result.get("global_remaining_rc_lower_bound"),
        result.get("dual_bound"),
        result.get("bound"),
    )
    unsupported_region_count = _compact_frontier_unsupported_region_count(result, pricing_proof_kind=pricing_proof_kind)
    payload = {
        **{key: value for key, value in result.items() if key != "journeys"},
        **profile_payload,
        "status": str(result.get("status") or "COMPACT_HIGHS_SINGLE_JOURNEY_PRICING"),
        "exact_status": str(result.get("exact_status") or "NOT_SOLVED"),
        "compact_pricing_phase": str(phase),
        "compact_pricing_phase_payloads": dict(phase_payloads),
        "compact_final_judge_phase_mode": str(phase_mode),
        "compact_final_judge_phase_mode_env": COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_ENV,
        "negative_feasibility_skipped_for_proof_only": bool(str(phase_mode) == "proof_only"),
        "negative_feasibility_full_space_proof_attempted": bool(
            result.get("negative_feasibility_full_space_proof_attempted")
        ),
        "negative_feasibility_full_space_proof_can_certify": bool(
            result.get("negative_feasibility_full_space_proof_can_certify")
        ),
        "task_count": len(data.task_ids),
        "max_direct_tasks": len(data.task_ids),
        "candidate_round_count": int(result.get("candidate_round_count") or result.get("compact_negative_batch_search_call_count") or 1),
        "candidate_round_limit": int(result.get("candidate_round_limit") or result.get("compact_negative_batch_target") or 1),
        "candidate_task_count": len(data.task_ids),
        "candidate_task_ids": list(data.task_ids),
        "pricing_state": state.value,
        "can_certify_no_negative": bool(can_certify),
        "uses_true_dual_bpc_certificate": bool(can_certify),
        "negative_found": bool(negative_columns) or bool(result.get("negative_found")) or state == PricingState.FOUND_NEGATIVE,
        "negative_column_count": len(negative_columns),
        "cut_context_active": not cut_context.empty,
        "cut_count": len(cut_context.cuts),
        "branch_context_active": not branch_context.empty,
        "branch_decision_count": len(branch_context.pair_decisions),
        "branch_filtered_column_count": 0,
        "completion_bound": _disabled_completion_bound_payload(),
        "completion_bound_pruning_enabled": False,
        "sortie_template_cache": {"enabled": False, "entry_count": 0, "hit_count": 0, "miss_count": 0},
        "dual_fingerprint": context.dual_fingerprint,
        "branch_context": branch_context.to_payload(),
        "cut_context": cut_context.to_payload(),
        "manual_best_reduced_cost": result.get("manual_best_reduced_cost"),
        "pricing_best_reduced_cost": result.get("pricing_best_reduced_cost", result.get("best_reduced_cost")),
        "pricing_rc_audit_pass": bool(result.get("pricing_rc_audit_pass") is True),
        "manual_priced_column_count": len(columns),
        "all_priced_columns_satisfy_branch_context": True,
        "global_remaining_rc_lb": global_remaining_rc_lb,
        "global_remaining_rc_lb_valid": bool(global_remaining_rc_lb is not None),
        "global_remaining_rc_lb_coverage_complete": bool(can_certify),
        "frontier_region_count": int(result.get("frontier_region_count") or (1 if global_remaining_rc_lb is not None else 0)),
        "frontier_unsupported_region_count": int(unsupported_region_count),
        "pending_complete_min_rc": _first_float(
            result.get("pending_complete_min_rc"),
            result.get("best_reduced_cost"),
            result.get("manual_best_reduced_cost"),
        ),
        "pricing_proof_kind": pricing_proof_kind,
        "final_judge_wall_time": round(perf_counter() - started_at, 6),
        "column_universe_semantics": "compact_single_journey_pricing_fixed_graph_all_task_subsets",
        "compact_pricing_contains_all_route_variants": True,
        "complete_universe_contains_all_route_variants": False,
        "representative_universe_total_count": _representative_universe_total_count(data),
        "representative_universe_audited_count": 0,
        "representative_universe_completion_ratio": 0.0,
        "representative_universe_remaining_count": _representative_universe_total_count(data),
        "note": (
            "Final judge used compact HiGHS single-journey reduced-cost pricing instead of "
            "enumerating every task-subset representative. It can certify no-negative only "
            "when the compact pricing MILP is exact and nonnegative; negative-feasibility "
            "phase may still return audited negative columns before exact closure."
        ),
    }
    return FinalJudgeResult(
        pricing_state=state,
        pricing_payload=payload,
        negative_columns=negative_columns,
        all_priced_columns=columns,
    )


def _compact_negative_harvest_payload(
    columns: list[JourneyColumn],
    duals: JourneyDuals,
    cut_context: CutContext,
    *,
    negative_eps: float,
    candidate_negative_count: int,
    max_selected: int | None = None,
    source_phase: str = "compact_final_judge_negative_feasibility_batch",
    pricing_rc_by_signature: dict[object, float] | None = None,
    column_pool: ColumnPool | None = None,
    master_view: MasterColumnView | None = None,
    node_id: str = "root",
    active_task_sets: set[frozenset[str]] | None = None,
    branch_context: BranchContext | None = None,
) -> dict:
    audited: list[tuple[float, tuple[str, ...], JourneyColumn]] = []
    not_addable_count = 0
    for column in columns:
        true_rc = _manual_reduced_cost(column, duals, cut_context)
        if true_rc < -abs(float(negative_eps)):
            audited.append((float(true_rc), _journey_forbidden_task_set(column), column))
        else:
            not_addable_count += 1
    audited.sort(key=lambda row: (row[0], row[1]))
    active_task_set_lookup = {
        tuple(sorted(str(task_id) for task_id in row))
        for row in (active_task_sets or set())
    }
    new_rows: list[tuple[float, tuple[str, ...], JourneyColumn]] = []
    replacement_rows: list[tuple[float, tuple[str, ...], JourneyColumn]] = []
    selected_new_task_sets: set[tuple[str, ...]] = set()
    seen_task_sets: set[tuple[str, ...]] = set()
    for row in audited:
        _true_rc, task_set, _column = row
        seen_before = task_set in seen_task_sets
        seen_task_sets.add(task_set)
        if (
            task_set not in active_task_set_lookup
            and not seen_before
            and task_set not in selected_new_task_sets
        ):
            new_rows.append(row)
            selected_new_task_sets.add(task_set)
        else:
            replacement_rows.append(row)
    limit = len(audited) if max_selected is None else max(0, int(max_selected))
    selected: list[JourneyColumn] = []
    selected_task_set_rows: list[tuple[tuple[str, ...], bool]] = []
    addability_reports: list[dict] = []
    addability_audit_available = bool(column_pool is not None and master_view is not None)
    addability_rejected_count = 0
    addability_reject_reasons: dict[str, int] = {}
    pricing_lookup = pricing_rc_by_signature or {}
    for true_rc, task_set, column in new_rows + replacement_rows:
        pricing_rc = _optional_float(pricing_lookup.get(column_signature_from_journey(column)))
        addability_report = _compact_harvest_addability_report(
            column,
            true_rc=true_rc,
            pricing_rc=pricing_rc,
            column_pool=column_pool,
            master_view=master_view,
            node_id=node_id,
            active_task_sets=active_task_sets,
            branch_context=branch_context,
            cut_context=cut_context,
        )
        addability_reports.append(addability_report)
        if not addability_report["would_enter_master"]:
            addability_rejected_count += 1
            reason = str(addability_report.get("reject_reason") or addability_report.get("addability_reason") or "not_addable")
            addability_reject_reasons[reason] = int(addability_reject_reasons.get(reason, 0)) + 1
            continue
        selected.append(column)
        selected_task_set_rows.append((task_set, task_set not in active_task_set_lookup))
        if len(selected) >= limit:
            break
    selected_new_task_sets_count, replacement_task_set_count = _compact_selected_task_set_counts(
        selected_task_set_rows,
        active_task_set_lookup=active_task_set_lookup,
    )
    duplicate_count = max(0, len(audited) - len(seen_task_sets))
    selected_rc_values = tuple(_manual_reduced_cost(column, duals, cut_context) for column in selected)
    selected_pricing_rc_values = tuple(
        _optional_float(pricing_lookup.get(column_signature_from_journey(column)))
        for column in selected
    )
    selected_pricing_rc_available = bool(selected) and all(value is not None for value in selected_pricing_rc_values)
    selected_pricing_diffs = tuple(
        abs(float(manual_rc) - float(pricing_rc))
        for manual_rc, pricing_rc in zip(selected_rc_values, selected_pricing_rc_values)
        if pricing_rc is not None
    )
    pricing_rc_audit_pass = bool(
        selected_pricing_rc_available
        and len(selected_pricing_diffs) == len(selected_rc_values)
        and all(diff <= 1.0e-6 for diff in selected_pricing_diffs)
    )
    selected_task_set_tuples = tuple(_journey_forbidden_task_set(column) for column in selected)
    selected_addability_reports = tuple(
        row for row in addability_reports if row.get("selected_after_addability_audit")
    )
    return {
        "_selected_columns": tuple(selected),
        "harvest_schema_version": "lunar_ice_bpc.b4_1_final_judge_harvest.v1",
        "harvest_source_phase": str(source_phase),
        "harvest_target": None if max_selected is None else int(max_selected),
        "harvest_candidate_negative_count": int(candidate_negative_count),
        "harvest_selected_count": len(selected),
        "harvest_selected_new_task_set_count": int(selected_new_task_sets_count),
        "harvest_selected_replacement_task_set_count": int(replacement_task_set_count),
        "harvest_rejected_duplicate_count": int(duplicate_count),
        "harvest_rejected_not_addable_count": int(not_addable_count + addability_rejected_count),
        "harvest_addability_audit_available": addability_audit_available,
        "harvest_selected_all_addability_audited": addability_audit_available,
        "harvest_selected_all_would_enter_master": all(
            bool(row.get("would_enter_master")) for row in addability_reports if row.get("selected_after_addability_audit")
        ),
        "harvest_addability_reject_reasons": dict(sorted(addability_reject_reasons.items())),
        "harvest_manual_rc_audit_pass": all(value < -abs(float(negative_eps)) for value in selected_rc_values),
        "harvest_pricing_rc_audit_available": selected_pricing_rc_available,
        "harvest_pricing_rc_audit_pass": pricing_rc_audit_pass,
        "harvest_pricing_rc_max_abs_diff": (
            None if not selected_pricing_diffs else round(float(max(selected_pricing_diffs)), 9)
        ),
        "harvest_branch_context_audit_pass": all(
            bool(row.get("is_allowed_by_branch")) for row in selected_addability_reports
        ),
        "harvest_cut_context_audit_pass": all(
            bool(row.get("is_allowed_by_cut_context")) for row in selected_addability_reports
        ),
        "harvest_addability_audit_pass": (
            all(bool(row.get("would_enter_master")) for row in selected_addability_reports)
            if addability_audit_available
            else None
        ),
        "harvest_best_true_rc": None if not selected_rc_values else round(float(min(selected_rc_values)), 9),
        "harvest_worst_selected_true_rc": None if not selected_rc_values else round(float(max(selected_rc_values)), 9),
        "harvest_avg_pairwise_jaccard": _avg_pairwise_jaccard(selected_task_set_tuples),
        "harvest_priority": "prefer_new_task_set_then_true_rc_then_replacements",
        "restricted_harvest_can_certify_no_negative": False,
        "harvest_reports": addability_reports,
    }


def _compact_harvest_addability_report(
    column: JourneyColumn,
    *,
    true_rc: float,
    pricing_rc: float | None = None,
    column_pool: ColumnPool | None,
    master_view: MasterColumnView | None,
    node_id: str,
    active_task_sets: set[frozenset[str]] | None,
    branch_context: BranchContext | None,
    cut_context: CutContext,
) -> dict:
    signature = column_signature_from_journey(column)
    branch_allowed = journey_satisfies_branch_context(column, branch_context)
    cut_coefficients = cut_coefficients_for_journey(column, cut_context)
    cut_allowed = True
    if column_pool is None or master_view is None:
        return {
            "task_set": list(signature.task_set),
            "true_reduced_cost": round(float(true_rc), 9),
            "pricing_reduced_cost": None if pricing_rc is None else round(float(pricing_rc), 9),
            "manual_pricing_rc_abs_diff": None
            if pricing_rc is None
            else round(abs(float(true_rc) - float(pricing_rc)), 9),
            "would_enter_master": True,
            "selected_after_addability_audit": True,
            "addability_audit_available": False,
            "addability_reason": "addability_audit_not_available",
            "reject_reason": "",
            "pool_contains_signature": False,
            "current_master_contains_signature": False,
            "is_allowed_by_branch": bool(branch_allowed),
            "is_allowed_by_cut_context": bool(cut_allowed),
            "would_change_active_support": True,
        }
    bpc_column = BpcColumn(signature=signature, objective=column.objective, payload=column)
    report = column_pool.addability_check(
        bpc_column,
        {
            "master_view": master_view,
            "node_id": str(node_id),
            "active_task_sets": active_task_sets or set(),
            "is_allowed_by_branch": branch_allowed,
            "is_allowed_by_cut_context": cut_allowed,
            "cut_coefficients": cut_coefficients,
        },
    )
    return {
        "task_set": list(signature.task_set),
        "true_reduced_cost": round(float(true_rc), 9),
        "pricing_reduced_cost": None if pricing_rc is None else round(float(pricing_rc), 9),
        "manual_pricing_rc_abs_diff": None
        if pricing_rc is None
        else round(abs(float(true_rc) - float(pricing_rc)), 9),
        "would_enter_master": bool(report.would_enter_master),
        "selected_after_addability_audit": bool(report.would_enter_master),
        "addability_audit_available": True,
        "addability_reason": report.reason,
        "reject_reason": report.reject_reason,
        "pool_contains_signature": report.pool_contains_signature,
        "current_master_contains_signature": report.current_master_contains_signature,
        "is_allowed_by_branch": report.is_allowed_by_branch,
        "is_allowed_by_cut_context": report.is_allowed_by_cut_context,
        "would_change_active_support": report.would_change_active_support,
    }


def _compact_selected_task_set_counts(
    rows: list[tuple[tuple[str, ...], bool]],
    *,
    active_task_set_lookup: set[tuple[str, ...]],
) -> tuple[int, int]:
    selected_new_task_sets: set[tuple[str, ...]] = set()
    new_count = 0
    replacement_count = 0
    for task_set, candidate_is_new in rows:
        if candidate_is_new and task_set not in active_task_set_lookup and task_set not in selected_new_task_sets:
            new_count += 1
            selected_new_task_sets.add(task_set)
        else:
            replacement_count += 1
    return new_count, replacement_count


def _compact_result_pricing_rc_for_column(result: dict, *, column_count: int) -> float | None:
    if int(column_count) != 1:
        return None
    return _optional_float(
        result.get("pricing_model_reduced_cost"),
        result.get("model_objective"),
        result.get("pricing_best_reduced_cost"),
        result.get("best_reduced_cost"),
    )


def _optional_float(*values: object) -> float | None:
    for value in values:
        if value is None or value == "":
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _avg_pairwise_jaccard(task_sets: tuple[tuple[str, ...], ...]) -> float | None:
    if len(task_sets) < 2:
        return None
    total = 0.0
    count = 0
    for left_index, left in enumerate(task_sets):
        left_set = set(left)
        for right in task_sets[left_index + 1 :]:
            right_set = set(right)
            union = left_set | right_set
            total += 1.0 if not union else len(left_set & right_set) / len(union)
            count += 1
    return None if count == 0 else round(float(total / count), 9)


def _compact_pricing_proof_kind(result: dict, *, can_certify: bool) -> str:
    if can_certify:
        return "EXHAUSTIVE_NO_NEGATIVE"
    explicit = result.get("pricing_proof_kind")
    if explicit in {
        "NONE",
        "EXHAUSTIVE_NO_NEGATIVE",
        "FRONTIER_BOUND_INCOMPLETE",
        "FRONTIER_BOUND_NO_NEGATIVE",
    }:
        if explicit in {"EXHAUSTIVE_NO_NEGATIVE", "FRONTIER_BOUND_NO_NEGATIVE"}:
            return "FRONTIER_BOUND_INCOMPLETE"
        return str(explicit)
    if result.get("negative_feasibility_search_enabled") or result.get("compact_negative_batch_enabled"):
        return "FRONTIER_BOUND_INCOMPLETE"
    if result.get("pricing_complete_by_compact_milp") and result.get("can_certify_no_negative") is True:
        return "EXHAUSTIVE_NO_NEGATIVE"
    return "FRONTIER_BOUND_INCOMPLETE"


def _compact_frontier_unsupported_region_count(result: dict, *, pricing_proof_kind: str) -> int:
    if pricing_proof_kind in {"EXHAUSTIVE_NO_NEGATIVE", "FRONTIER_BOUND_NO_NEGATIVE"}:
        return 0
    explicit = result.get("frontier_unsupported_region_count")
    if explicit is not None:
        try:
            explicit_count = max(0, int(explicit))
            if pricing_proof_kind == "FRONTIER_BOUND_INCOMPLETE":
                return max(1, explicit_count)
            return explicit_count
        except (TypeError, ValueError):
            pass
    forbidden_count = int(result.get("forbidden_arc_pattern_count") or 0) + int(result.get("forbidden_task_set_count") or 0)
    return max(1, forbidden_count)


def _first_float(*values: object) -> float | None:
    for value in values:
        if value is None:
            continue
        try:
            return round(float(value), 9)
        except (TypeError, ValueError):
            continue
    return None


def _compact_phase_summary(result: dict) -> dict:
    return {
        "status": result.get("status"),
        "exact_status": result.get("exact_status"),
        "pricing_state": result.get("pricing_state"),
        "best_reduced_cost": result.get("best_reduced_cost"),
        "manual_best_reduced_cost": result.get("manual_best_reduced_cost"),
        "dual_bound": result.get("dual_bound", result.get("bound")),
        "gap": result.get("gap"),
        "wall_time_sec": result.get("wall_time_sec"),
        "negative_found": result.get("negative_found"),
        "negative_feasibility_search_enabled": result.get("negative_feasibility_search_enabled"),
        "negative_feasibility_zero_objective_enabled": result.get(
            "negative_feasibility_zero_objective_enabled"
        ),
        "compact_final_judge_profile": result.get("compact_final_judge_profile"),
        "compact_final_judge_formulation_profile": result.get("compact_final_judge_formulation_profile"),
        "compact_final_judge_profile_official_default": result.get("compact_final_judge_profile_official_default"),
        "compact_final_judge_phase_mode": result.get("compact_final_judge_phase_mode"),
        "compact_optimization_harvest_enabled": result.get("compact_optimization_harvest_enabled"),
        "compact_optimization_harvest_target": result.get("compact_optimization_harvest_target"),
        "compact_optimization_harvest_no_good_scope": result.get(
            "compact_optimization_harvest_no_good_scope"
        ),
        "compact_optimization_harvest_found_count": result.get("compact_optimization_harvest_found_count"),
        "compact_optimization_harvest_search_call_count": result.get(
            "compact_optimization_harvest_search_call_count"
        ),
        "route_template_pre_harvest_enabled": result.get("route_template_pre_harvest_enabled"),
        "route_template_pre_harvest_status": result.get("route_template_pre_harvest_status"),
        "route_template_pre_harvest_time_cap_sec": result.get("route_template_pre_harvest_time_cap_sec"),
        "route_template_pre_harvest_pricing_wall_time_sec": result.get(
            "route_template_pre_harvest_pricing_wall_time_sec"
        ),
        "route_template_pre_harvest_max_direct_tasks": result.get(
            "route_template_pre_harvest_max_direct_tasks"
        ),
        "route_template_pre_harvest_max_active_seeds": result.get(
            "route_template_pre_harvest_max_active_seeds"
        ),
        "route_template_pre_harvest_max_candidate_sets": result.get(
            "route_template_pre_harvest_max_candidate_sets"
        ),
        "route_template_pre_harvest_target": result.get("route_template_pre_harvest_target"),
        "route_template_pre_harvest_seed_count": result.get("route_template_pre_harvest_seed_count"),
        "route_template_pre_harvest_candidate_round_count": result.get(
            "route_template_pre_harvest_candidate_round_count"
        ),
        "route_template_pre_harvest_candidate_negative_count": result.get(
            "route_template_pre_harvest_candidate_negative_count"
        ),
        "route_template_pre_harvest_selected_count": result.get(
            "route_template_pre_harvest_selected_count"
        ),
        "route_template_pre_harvest_selected_new_task_set_count": result.get(
            "route_template_pre_harvest_selected_new_task_set_count"
        ),
        "route_template_pre_harvest_selected_replacement_task_set_count": result.get(
            "route_template_pre_harvest_selected_replacement_task_set_count"
        ),
        "route_template_pre_harvest_can_certify_no_negative": result.get(
            "route_template_pre_harvest_can_certify_no_negative"
        ),
        "route_template_pre_harvest_fallback_enabled": result.get(
            "route_template_pre_harvest_fallback_enabled"
        ),
        "negative_feasibility_skipped_for_proof_only": result.get("negative_feasibility_skipped_for_proof_only"),
        "negative_feasibility_full_space_proof_attempted": result.get(
            "negative_feasibility_full_space_proof_attempted"
        ),
        "negative_feasibility_full_space_proof_can_certify": result.get(
            "negative_feasibility_full_space_proof_can_certify"
        ),
        "mtz_connectivity_enabled": result.get("mtz_connectivity_enabled"),
        "mtz_endpoint_order_cuts_enabled": result.get("mtz_endpoint_order_cuts_enabled"),
        "mtz_endpoint_order_cut_count": result.get("mtz_endpoint_order_cut_count"),
        "pair_adjacency_cuts_enabled": result.get("pair_adjacency_cuts_enabled"),
        "pair_adjacency_cut_count": result.get("pair_adjacency_cut_count"),
        "sortie_slots_per_journey": result.get("sortie_slots_per_journey"),
        "sortie_slot_bound_source": result.get("sortie_slot_bound_source"),
        "sortie_slot_horizon_count_bound": result.get("sortie_slot_horizon_count_bound"),
        "latest_service_start_slot_bound_enabled": result.get("latest_service_start_slot_bound_enabled"),
        "sortie_slot_latest_start_count_bound": result.get("sortie_slot_latest_start_count_bound"),
        "sortie_slot_latest_service_start_upper_bound": result.get("sortie_slot_latest_service_start_upper_bound"),
        "sortie_slot_min_depot_outbound_travel_lower_bound": result.get(
            "sortie_slot_min_depot_outbound_travel_lower_bound"
        ),
        "sortie_slot_min_duration_lower_bound": result.get("sortie_slot_min_duration_lower_bound"),
        "sortie_slot_min_return_duration_lower_bound": result.get("sortie_slot_min_return_duration_lower_bound"),
        "sortie_slot_min_out_return_travel_lower_bound": result.get(
            "sortie_slot_min_out_return_travel_lower_bound"
        ),
        "sortie_slot_min_sortie_energy_lower_bound": result.get(
            "sortie_slot_min_sortie_energy_lower_bound"
        ),
        "sortie_slot_min_energy_recharge_duration_lower_bound": result.get(
            "sortie_slot_min_energy_recharge_duration_lower_bound"
        ),
        "time_window_arc_pruning_enabled": result.get("time_window_arc_pruning_enabled"),
        "time_window_arc_option_count": result.get("time_window_arc_option_count"),
        "time_window_impossible_arc_option_count": result.get("time_window_impossible_arc_option_count"),
        "slot_task_time_pruning_enabled": result.get("slot_task_time_pruning_enabled"),
        "slot_task_time_feasible_assignment_count": result.get("slot_task_time_feasible_assignment_count"),
        "slot_task_time_pruned_assignment_count": result.get("slot_task_time_pruned_assignment_count"),
        "slot_task_time_pruned_due_count": result.get("slot_task_time_pruned_due_count"),
        "slot_task_time_pruned_horizon_count": result.get("slot_task_time_pruned_horizon_count"),
        "slot_task_time_total_assignment_count": result.get("slot_task_time_total_assignment_count"),
        "slot_task_time_original_total_assignment_count": result.get(
            "slot_task_time_original_total_assignment_count"
        ),
        "slot_task_model_assignment_count": result.get("slot_task_model_assignment_count"),
        "slot_arc_support_pruning_enabled": result.get("slot_arc_support_pruning_enabled"),
        "slot_arc_support_feasible_assignment_count": result.get(
            "slot_arc_support_feasible_assignment_count"
        ),
        "slot_arc_support_pruned_assignment_count": result.get(
            "slot_arc_support_pruned_assignment_count"
        ),
        "slot_arc_support_pruned_unreachable_count": result.get(
            "slot_arc_support_pruned_unreachable_count"
        ),
        "slot_arc_support_pruned_no_return_count": result.get(
            "slot_arc_support_pruned_no_return_count"
        ),
        "slot_arc_support_pruned_option_count": result.get("slot_arc_support_pruned_option_count"),
        "slot_arc_time_pruned_option_count": result.get("slot_arc_time_pruned_option_count"),
        "slot_sequence_capacity_arc_pruning_enabled": result.get(
            "slot_sequence_capacity_arc_pruning_enabled"
        ),
        "slot_sequence_capacity_arc_pruned_option_count": result.get(
            "slot_sequence_capacity_arc_pruned_option_count"
        ),
        "slot_sequence_capacity_mtz_disabled_slot_count": result.get(
            "slot_sequence_capacity_mtz_disabled_slot_count"
        ),
        "resource_arc_pruning_enabled": result.get("resource_arc_pruning_enabled"),
        "resource_arc_pruned_option_count": result.get("resource_arc_pruned_option_count"),
        "resource_arc_energy_pruned_option_count": result.get("resource_arc_energy_pruned_option_count"),
        "resource_arc_shadow_pruned_option_count": result.get("resource_arc_shadow_pruned_option_count"),
        "resource_arc_demand_pruned_option_count": result.get("resource_arc_demand_pruned_option_count"),
        "dual_task_slot_full_space_lower_bound_enabled": result.get(
            "dual_task_slot_full_space_lower_bound_enabled"
        ),
        "dual_task_slot_full_space_lower_bound_applicable": result.get(
            "dual_task_slot_full_space_lower_bound_applicable"
        ),
        "dual_task_slot_full_space_lower_bound_early_stop_on_negative": result.get(
            "dual_task_slot_full_space_lower_bound_early_stop_on_negative"
        ),
        "dual_task_slot_full_space_lower_bound_early_stopped_on_negative": result.get(
            "dual_task_slot_full_space_lower_bound_early_stopped_on_negative"
        ),
        "dual_task_slot_full_space_lower_bound_coverage_complete": result.get(
            "dual_task_slot_full_space_lower_bound_coverage_complete"
        ),
        "dual_task_slot_full_space_lower_bound_can_certify": result.get(
            "dual_task_slot_full_space_lower_bound_can_certify"
        ),
        "dual_task_slot_full_space_lower_bound_region_count": result.get(
            "dual_task_slot_full_space_lower_bound_region_count"
        ),
        "dual_task_slot_full_space_lower_bound_optimal_region_count": result.get(
            "dual_task_slot_full_space_lower_bound_optimal_region_count"
        ),
        "dual_task_slot_full_space_lower_bound_infeasible_region_count": result.get(
            "dual_task_slot_full_space_lower_bound_infeasible_region_count"
        ),
        "dual_task_slot_full_space_lower_bound_unsupported_region_count": result.get(
            "dual_task_slot_full_space_lower_bound_unsupported_region_count"
        ),
        "dual_task_slot_full_space_lower_bound_negative_region_count": result.get(
            "dual_task_slot_full_space_lower_bound_negative_region_count"
        ),
        "dual_task_slot_full_space_lower_bound_value": result.get(
            "dual_task_slot_full_space_lower_bound_value"
        ),
        "dual_task_slot_full_space_lower_bound_task_count": result.get(
            "dual_task_slot_full_space_lower_bound_task_count"
        ),
        "dual_task_slot_full_space_lower_bound_active_sortie_count": result.get(
            "dual_task_slot_full_space_lower_bound_active_sortie_count"
        ),
        "dual_task_slot_full_space_lower_bound_wall_time_sec": result.get(
            "dual_task_slot_full_space_lower_bound_wall_time_sec"
        ),
        "dual_task_slot_full_space_lower_bound_status": result.get(
            "dual_task_slot_full_space_lower_bound_status"
        ),
        "single_journey_mip_start_enabled": result.get("single_journey_mip_start_enabled"),
        "single_journey_mip_start_status": result.get("single_journey_mip_start_status"),
        "single_journey_mip_start_source": result.get("single_journey_mip_start_source"),
        "single_journey_mip_start_entry_count": result.get("single_journey_mip_start_entry_count"),
        "single_journey_mip_start_zero_fill_integers": result.get(
            "single_journey_mip_start_zero_fill_integers"
        ),
        "single_journey_mip_start_zero_fill_integer_entry_count": result.get(
            "single_journey_mip_start_zero_fill_integer_entry_count"
        ),
        "single_journey_mip_start_inactive_tail_time_entry_count": result.get(
            "single_journey_mip_start_inactive_tail_time_entry_count"
        ),
        "single_journey_mip_start_inactive_tail_time_mode": result.get(
            "single_journey_mip_start_inactive_tail_time_mode"
        ),
        "single_journey_mip_start_sort_indices": result.get(
            "single_journey_mip_start_sort_indices"
        ),
        "single_journey_mip_start_sortie_count": result.get("single_journey_mip_start_sortie_count"),
        "single_journey_mip_start_task_count": result.get("single_journey_mip_start_task_count"),
        "single_journey_mip_start_objective": result.get("single_journey_mip_start_objective"),
        "single_journey_mip_start_reduced_cost": result.get("single_journey_mip_start_reduced_cost"),
        "zero_capacity_slot_truncation_enabled": result.get(
            "zero_capacity_slot_truncation_enabled"
        ),
        "zero_capacity_slot_truncation_original_slot_count": result.get(
            "zero_capacity_slot_truncation_original_slot_count"
        ),
        "zero_capacity_slot_truncation_effective_slot_count": result.get(
            "zero_capacity_slot_truncation_effective_slot_count"
        ),
        "zero_capacity_slot_truncation_trimmed_slot_count": result.get(
            "zero_capacity_slot_truncation_trimmed_slot_count"
        ),
        "zero_capacity_slot_truncation_first_zero_slot": result.get(
            "zero_capacity_slot_truncation_first_zero_slot"
        ),
        "slot_sequence_capacity_live_bound_enabled": result.get(
            "slot_sequence_capacity_live_bound_enabled"
        ),
        "slot_sequence_capacity_live_bound_by_slot": result.get(
            "slot_sequence_capacity_live_bound_by_slot"
        ),
        "slot_sequence_capacity_live_bound_tightened_slot_count": result.get(
            "slot_sequence_capacity_live_bound_tightened_slot_count"
        ),
        "tight_service_start_bounds_enabled": result.get(
            "tight_service_start_bounds_enabled"
        ),
        "tight_service_start_bound_count": result.get("tight_service_start_bound_count"),
        "tight_service_start_bound_min": result.get("tight_service_start_bound_min"),
        "tight_service_start_bound_max": result.get("tight_service_start_bound_max"),
        "tight_time_arc_big_m_enabled": result.get("tight_time_arc_big_m_enabled"),
        "tight_time_arc_big_m_depot_arc_count": result.get(
            "tight_time_arc_big_m_depot_arc_count"
        ),
        "tight_time_arc_big_m_active_time_bound_count": result.get(
            "tight_time_arc_big_m_active_time_bound_count"
        ),
        "tight_time_arc_big_m_max_reduction": result.get(
            "tight_time_arc_big_m_max_reduction"
        ),
        "tight_conditional_sequence_big_m_enabled": result.get(
            "tight_conditional_sequence_big_m_enabled"
        ),
        "tight_conditional_sequence_big_m_count": result.get(
            "tight_conditional_sequence_big_m_count"
        ),
        "tight_conditional_sequence_big_m_max_reduction": result.get(
            "tight_conditional_sequence_big_m_max_reduction"
        ),
        "slot_service_start_y_lower_bound_enabled": result.get(
            "slot_service_start_y_lower_bound_enabled"
        ),
        "slot_service_start_y_lower_bound_count": result.get(
            "slot_service_start_y_lower_bound_count"
        ),
        "slot_service_start_y_lower_bound_max_lift": result.get(
            "slot_service_start_y_lower_bound_max_lift"
        ),
        "slot_service_start_y_lower_bound_min": result.get(
            "slot_service_start_y_lower_bound_min"
        ),
        "slot_service_start_y_lower_bound_max": result.get(
            "slot_service_start_y_lower_bound_max"
        ),
        "required_task_set_enabled": result.get("required_task_set_enabled"),
        "required_task_set_count": result.get("required_task_set_count"),
        "pricing_model_task_count": result.get("pricing_model_task_count"),
        "required_task_set_model_reduction_enabled": result.get(
            "required_task_set_model_reduction_enabled"
        ),
        "required_task_set_model_task_count": result.get("required_task_set_model_task_count"),
        "required_task_set_model_task_reduction_count": result.get(
            "required_task_set_model_task_reduction_count"
        ),
        "required_task_set_region_can_certify_no_negative": result.get(
            "required_task_set_region_can_certify_no_negative"
        ),
        "pricing_complete_for_required_task_set": result.get("pricing_complete_for_required_task_set"),
        "sortie_slot_position_bounds_enabled": result.get("sortie_slot_position_bounds_enabled"),
        "sortie_slot_position_bound_count": result.get("sortie_slot_position_bound_count"),
        "sortie_slot_latest_start_upper_bound": result.get("sortie_slot_latest_start_upper_bound"),
        "service_start_depot_travel_lb_enabled": result.get("service_start_depot_travel_lb_enabled"),
        "service_start_depot_travel_lb_count": result.get("service_start_depot_travel_lb_count"),
        "service_start_depot_travel_lb_min": result.get("service_start_depot_travel_lb_min"),
        "service_start_depot_travel_lb_max": result.get("service_start_depot_travel_lb_max"),
        "task_to_depot_return_travel_lb_enabled": result.get("task_to_depot_return_travel_lb_enabled"),
        "task_to_depot_return_travel_lb_count": result.get("task_to_depot_return_travel_lb_count"),
        "task_to_depot_return_travel_lb_min": result.get("task_to_depot_return_travel_lb_min"),
        "task_to_depot_return_travel_lb_max": result.get("task_to_depot_return_travel_lb_max"),
        "pair_route_duration_lb_enabled": result.get("pair_route_duration_lb_enabled"),
        "pair_route_duration_lb_count": result.get("pair_route_duration_lb_count"),
        "pair_route_duration_lb_min": result.get("pair_route_duration_lb_min"),
        "pair_route_duration_lb_max": result.get("pair_route_duration_lb_max"),
        "pair_weighted_completion_lb_enabled": result.get("pair_weighted_completion_lb_enabled"),
        "pair_weighted_completion_lb_count": result.get("pair_weighted_completion_lb_count"),
        "pair_weighted_completion_lb_min": result.get("pair_weighted_completion_lb_min"),
        "pair_weighted_completion_lb_max": result.get("pair_weighted_completion_lb_max"),
        "demand_cover_cut_enabled": result.get("demand_cover_cut_enabled"),
        "demand_cover_cut_count": result.get("demand_cover_cut_count"),
        "demand_cover_subset_count": result.get("demand_cover_subset_count"),
        "demand_cover_max_size": result.get("demand_cover_max_size"),
        "demand_cover_min_demand": result.get("demand_cover_min_demand"),
        "demand_cover_max_demand": result.get("demand_cover_max_demand"),
        "single_task_energy_lb_enabled": result.get("single_task_energy_lb_enabled"),
        "single_task_energy_lb_count": result.get("single_task_energy_lb_count"),
        "single_task_energy_lb_min": result.get("single_task_energy_lb_min"),
        "single_task_energy_lb_max": result.get("single_task_energy_lb_max"),
        "single_task_shadow_lb_enabled": result.get("single_task_shadow_lb_enabled"),
        "single_task_shadow_lb_count": result.get("single_task_shadow_lb_count"),
        "single_task_shadow_lb_min": result.get("single_task_shadow_lb_min"),
        "single_task_shadow_lb_max": result.get("single_task_shadow_lb_max"),
        "pair_energy_lb_enabled": result.get("pair_energy_lb_enabled"),
        "pair_energy_lb_count": result.get("pair_energy_lb_count"),
        "pair_energy_lb_min": result.get("pair_energy_lb_min"),
        "pair_energy_lb_max": result.get("pair_energy_lb_max"),
        "pair_energy_lb_exceeds_limit_count": result.get("pair_energy_lb_exceeds_limit_count"),
        "pair_shadow_lb_enabled": result.get("pair_shadow_lb_enabled"),
        "pair_shadow_lb_count": result.get("pair_shadow_lb_count"),
        "pair_shadow_lb_min": result.get("pair_shadow_lb_min"),
        "pair_shadow_lb_max": result.get("pair_shadow_lb_max"),
        "pair_shadow_lb_exceeds_limit_count": result.get("pair_shadow_lb_exceeds_limit_count"),
        "pair_energy_infeasible_cut_enabled": result.get("pair_energy_infeasible_cut_enabled"),
        "pair_energy_infeasible_cut_count": result.get("pair_energy_infeasible_cut_count"),
        "pair_energy_infeasible_pair_count": result.get("pair_energy_infeasible_pair_count"),
        "pair_time_window_infeasible_cut_enabled": result.get("pair_time_window_infeasible_cut_enabled"),
        "pair_time_window_infeasible_cut_count": result.get("pair_time_window_infeasible_cut_count"),
        "pair_time_window_infeasible_pair_count": result.get("pair_time_window_infeasible_pair_count"),
        "pair_time_window_infeasible_margin_min": result.get("pair_time_window_infeasible_margin_min"),
        "pair_time_window_infeasible_margin_max": result.get("pair_time_window_infeasible_margin_max"),
        "pair_time_window_precedence_cut_enabled": result.get("pair_time_window_precedence_cut_enabled"),
        "pair_time_window_precedence_cut_count": result.get("pair_time_window_precedence_cut_count"),
        "pair_time_window_precedence_pair_count": result.get("pair_time_window_precedence_pair_count"),
        "pair_time_window_precedence_margin_min": result.get("pair_time_window_precedence_margin_min"),
        "pair_time_window_precedence_margin_max": result.get("pair_time_window_precedence_margin_max"),
        "triple_time_window_infeasible_cut_enabled": result.get("triple_time_window_infeasible_cut_enabled"),
        "triple_time_window_infeasible_cut_count": result.get("triple_time_window_infeasible_cut_count"),
        "triple_time_window_infeasible_triple_count": result.get("triple_time_window_infeasible_triple_count"),
        "triple_time_window_infeasible_margin_min": result.get("triple_time_window_infeasible_margin_min"),
        "triple_time_window_infeasible_margin_max": result.get("triple_time_window_infeasible_margin_max"),
        "quad_time_window_infeasible_cut_enabled": result.get("quad_time_window_infeasible_cut_enabled"),
        "quad_time_window_infeasible_cut_count": result.get("quad_time_window_infeasible_cut_count"),
        "quad_time_window_infeasible_quad_count": result.get("quad_time_window_infeasible_quad_count"),
        "quad_time_window_infeasible_margin_min": result.get("quad_time_window_infeasible_margin_min"),
        "quad_time_window_infeasible_margin_max": result.get("quad_time_window_infeasible_margin_max"),
        "pair_shadow_infeasible_cut_enabled": result.get("pair_shadow_infeasible_cut_enabled"),
        "pair_shadow_infeasible_cut_count": result.get("pair_shadow_infeasible_cut_count"),
        "pair_shadow_infeasible_pair_count": result.get("pair_shadow_infeasible_pair_count"),
        "pair_shadow_infeasible_lb_min": result.get("pair_shadow_infeasible_lb_min"),
        "pair_shadow_infeasible_lb_max": result.get("pair_shadow_infeasible_lb_max"),
        "triple_shadow_infeasible_cut_enabled": result.get("triple_shadow_infeasible_cut_enabled"),
        "triple_shadow_infeasible_cut_count": result.get("triple_shadow_infeasible_cut_count"),
        "triple_shadow_infeasible_triple_count": result.get("triple_shadow_infeasible_triple_count"),
        "triple_shadow_infeasible_lb_min": result.get("triple_shadow_infeasible_lb_min"),
        "triple_shadow_infeasible_lb_max": result.get("triple_shadow_infeasible_lb_max"),
        "triple_energy_infeasible_cut_enabled": result.get("triple_energy_infeasible_cut_enabled"),
        "triple_energy_infeasible_cut_count": result.get("triple_energy_infeasible_cut_count"),
        "triple_energy_infeasible_triple_count": result.get("triple_energy_infeasible_triple_count"),
        "triple_energy_infeasible_lb_min": result.get("triple_energy_infeasible_lb_min"),
        "triple_energy_infeasible_lb_max": result.get("triple_energy_infeasible_lb_max"),
        "compact_negative_no_good_scope": result.get("compact_negative_no_good_scope"),
        "forbidden_arc_pattern_count": result.get("forbidden_arc_pattern_count"),
        "forbidden_arc_patterns_can_certify_full_space": result.get("forbidden_arc_patterns_can_certify_full_space"),
        "forbidden_task_set_count": result.get("forbidden_task_set_count"),
        "forbidden_task_sets_can_certify_full_space": result.get("forbidden_task_sets_can_certify_full_space"),
        "variable_count": result.get("variable_count"),
        "constraint_count": result.get("constraint_count"),
        "model_status_name": result.get("model_status_name"),
    }


def _journey_forbidden_arc_pattern(column: JourneyColumn) -> tuple[tuple[int, str, str, str], ...]:
    pattern: list[tuple[int, str, str, str]] = []
    for slot, sortie in enumerate(column.sorties):
        for leg in sortie.legs:
            pattern.append((int(slot), str(leg.source), str(leg.target), str(leg.path_type)))
    return tuple(pattern)


def _journey_forbidden_task_set(column: JourneyColumn) -> tuple[str, ...]:
    return tuple(sorted(str(task_id) for task_id in column.task_set))


def _run_complete_universe_rc_final_judge(
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    context: ReducedCostContext,
    branch_context: BranchContext,
    cut_context: CutContext,
    max_direct_tasks: int,
    negative_eps: float,
    cache: DirectPricingCache | None,
    wall_time_limit_sec: float | None,
    complete_universe_columns: tuple[JourneyColumn, ...] | None,
    complete_universe_counts: dict | None,
) -> FinalJudgeResult:
    """Price columns by task-subset representative enumeration plus manual RC audit.

    At the root without branch/cut context, reduced cost differs across columns
    only by the fixed journey objective for a given task set. The direct journey
    universe enumerator already returns the objective-best fixed-graph column
    for every nonempty task subset. Under Ryan-Foster task-set branching and no
    cuts, a manual RC audit over these representatives is an exact no-negative
    proof path without re-pricing every route variant.
    """

    if len(data.task_ids) > int(max_direct_tasks):
        payload = _incomplete_universe_payload(
            data,
            max_direct_tasks=max_direct_tasks,
            status="SKIPPED_TOO_LARGE_FOR_COMPLETE_UNIVERSE_RC_AUDIT",
            note=f"task_count={len(data.task_ids)} exceeds max_direct_tasks={max_direct_tasks}",
            cache=cache,
        )
        payload["dual_fingerprint"] = context.dual_fingerprint
        payload["branch_context"] = branch_context.to_payload()
        payload["cut_context"] = cut_context.to_payload()
        return FinalJudgeResult(
            pricing_state=PricingState.INCOMPLETE_LIMIT,
            pricing_payload=payload,
            negative_columns=tuple(),
            all_priced_columns=tuple(),
        )

    start = perf_counter()
    complete_universe_counts = complete_universe_counts or {}
    if complete_universe_columns is None:
        deadline = None
        if wall_time_limit_sec is not None:
            deadline = start + max(0.001, float(wall_time_limit_sec))
        try:
            universe = enumerate_direct_journey_columns(
                data,
                max_exact_tasks=int(max_direct_tasks),
                deadline=deadline,
            )
        except DirectBaselineTimeLimitExceeded as exc:
            payload = _incomplete_universe_payload(
                data,
                max_direct_tasks=max_direct_tasks,
                status="COMPLETE_UNIVERSE_RC_AUDIT_TIME_LIMIT",
                note=(
                    f"Complete fixed-universe RC audit exceeded wall_time_limit_sec={wall_time_limit_sec} "
                    f"during {exc.stage}; partial counts are diagnostic only."
                ),
                cache=cache,
                generated_journey_count=exc.generated_journey_count,
                generated_sortie_count=exc.generated_sortie_count,
                route_template_count=exc.route_template_count,
                pareto_label_count=exc.pareto_label_count,
            )
            payload["final_judge_wall_time"] = round(perf_counter() - start, 6)
            payload["dual_fingerprint"] = context.dual_fingerprint
            payload["branch_context"] = branch_context.to_payload()
            payload["cut_context"] = cut_context.to_payload()
            return FinalJudgeResult(
                pricing_state=PricingState.INCOMPLETE_LIMIT,
                pricing_payload=payload,
                negative_columns=tuple(),
                all_priced_columns=tuple(),
            )
        raw_columns = tuple(universe.columns)
        generated_sortie_count = int(universe.generated_sortie_count)
        route_template_count = int(universe.route_template_count)
        pareto_label_count = int(universe.pareto_label_count)
        universe_source = "enumerated"
    else:
        raw_columns = tuple(complete_universe_columns)
        generated_sortie_count = int(complete_universe_counts.get("generated_sortie_count") or 0)
        route_template_count = int(complete_universe_counts.get("route_template_count") or 0)
        pareto_label_count = int(complete_universe_counts.get("pareto_label_count") or 0)
        universe_source = "provided_complete_universe_cache"
    columns = tuple(column for column in raw_columns if journey_satisfies_branch_context(column, branch_context))
    branch_filtered_column_count = len(raw_columns) - len(columns)
    rc_values = tuple(_manual_reduced_cost(column, duals, cut_context) for column in columns)
    min_reduced_cost = min(rc_values) if rc_values else None
    negative_pairs = tuple(
        sorted(
            (
                (rc, column)
                for rc, column in zip(rc_values, columns)
                if rc < -abs(float(negative_eps))
            ),
            key=lambda item: (item[0], tuple(sorted(item[1].task_set)), item[1].objective),
        )
    )
    negative_columns = tuple(column for _, column in negative_pairs)
    pricing_rc_audit_pass = bool(
        (min_reduced_cost is None and not columns)
        or (min_reduced_cost is not None and min_reduced_cost == min(rc_values))
    )
    certified = bool(
        columns
        and min_reduced_cost is not None
        and float(min_reduced_cost) >= -abs(float(negative_eps))
        and not negative_columns
        and pricing_rc_audit_pass
    )
    state = (
        PricingState.FOUND_NEGATIVE
        if negative_columns
        else PricingState.CERTIFIED_NO_NEGATIVE
        if certified
        else PricingState.INCOMPLETE_LIMIT
    )
    pricing_proof_kind = (
        PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE
        if certified
        else PROOF_KIND_EXHAUSTIVE_FOUND_NEGATIVE
        if negative_columns
        else PROOF_KIND_EXHAUSTIVE_INCOMPLETE
    )
    payload = {
        "status": "COMPLETE_DIRECT_UNIVERSE_RC_AUDITED",
        "exact_status": "NOT_BPC_CERTIFIED",
        "task_count": len(data.task_ids),
        "max_direct_tasks": int(max_direct_tasks),
        "candidate_round_count": len(columns),
        "candidate_round_limit": None,
        "candidate_task_count": len(data.task_ids),
        "candidate_task_ids": list(data.task_ids),
        "pricing_complete_for_all_tasks": True,
        "pricing_complete_for_all_task_subsets": True,
        "exhaustive_candidate_set_count": len(columns),
        "representative_universe_total_count": _representative_universe_total_count(data),
        "representative_universe_audited_count": len(columns),
        "representative_universe_completion_ratio": _completion_ratio(
            len(columns),
            _representative_universe_total_count(data),
        ),
        "representative_universe_remaining_count": max(
            0,
            _representative_universe_total_count(data) - len(columns),
        ),
        "generated_journey_count": len(columns),
        "complete_universe_raw_column_count": len(raw_columns),
        "column_universe_semantics": TASK_SUBSET_REPRESENTATIVE_UNIVERSE_SEMANTICS,
        "complete_universe_contains_all_route_variants": False,
        "sortie_attempt_count": int(route_template_count),
        "feasible_sortie_template_count": int(generated_sortie_count),
        "route_template_count": int(route_template_count),
        "pareto_label_count": int(pareto_label_count),
        "best_reduced_cost": min_reduced_cost,
        "negative_found": bool(negative_columns),
        "negative_column_count": len(negative_columns),
        "cut_context_active": not cut_context.empty,
        "cut_count": len(cut_context.cuts),
        "branch_context_active": not branch_context.empty,
        "branch_decision_count": len(branch_context.pair_decisions),
        "branch_filtered_column_count": branch_filtered_column_count,
        "completion_bound": _disabled_completion_bound_payload(),
        "completion_bound_pruning_enabled": False,
        "sortie_template_cache": _cache_payload(cache),
        "pricing_state": state.value,
        "can_certify_no_negative": bool(certified),
        "uses_true_dual_bpc_certificate": bool(certified),
        "pricing_proof_kind": pricing_proof_kind,
        "pricing_proof_kind_source": "complete_universe_representative_rc_audit",
        "dual_fingerprint": context.dual_fingerprint,
        "branch_context": branch_context.to_payload(),
        "cut_context": cut_context.to_payload(),
        "manual_best_reduced_cost": min_reduced_cost,
        "pricing_best_reduced_cost": min_reduced_cost,
        "pricing_rc_audit_pass": pricing_rc_audit_pass,
        "manual_priced_column_count": len(rc_values),
        "all_priced_columns_satisfy_branch_context": all(
            journey_satisfies_branch_context(column, branch_context)
            for column in columns
        ),
        "final_judge_wall_time": round(perf_counter() - start, 6),
        "complete_universe_source": universe_source,
        "note": (
            "Final judge used the objective-best fixed-graph representative for each task subset "
            "plus manual reduced-cost audit; certificate authority is granted only when all audited "
            "RC values are nonnegative. This is not an all-route-variant universe."
        ),
    }
    return FinalJudgeResult(
        pricing_state=state,
        pricing_payload=payload,
        negative_columns=negative_columns,
        all_priced_columns=columns,
    )


def _incomplete_universe_payload(
    data: LunarIceData,
    *,
    max_direct_tasks: int,
    status: str,
    note: str,
    cache: DirectPricingCache | None,
    generated_journey_count: int = 0,
    generated_sortie_count: int = 0,
    route_template_count: int = 0,
    pareto_label_count: int = 0,
) -> dict:
    representative_total = _representative_universe_total_count(data)
    return {
        "status": status,
        "exact_status": "NOT_SOLVED",
        "task_count": len(data.task_ids),
        "max_direct_tasks": int(max_direct_tasks),
        "candidate_round_count": int(generated_journey_count),
        "candidate_round_limit": None,
        "candidate_task_count": 0,
        "candidate_task_ids": [],
        "pricing_complete_for_all_tasks": False,
        "pricing_complete_for_all_task_subsets": False,
        "exhaustive_candidate_set_count": int(generated_journey_count),
        "representative_universe_total_count": representative_total,
        "representative_universe_audited_count": int(generated_journey_count),
        "representative_universe_completion_ratio": _completion_ratio(
            int(generated_journey_count),
            representative_total,
        ),
        "representative_universe_remaining_count": max(
            0,
            representative_total - int(generated_journey_count),
        ),
        "generated_journey_count": int(generated_journey_count),
        "sortie_attempt_count": int(route_template_count),
        "feasible_sortie_template_count": int(generated_sortie_count),
        "route_template_count": int(route_template_count),
        "pareto_label_count": int(pareto_label_count),
        "best_reduced_cost": None,
        "negative_found": False,
        "negative_column_count": 0,
        "cut_context_active": False,
        "cut_count": 0,
        "branch_context_active": False,
        "branch_decision_count": 0,
        "branch_filtered_column_count": 0,
        "completion_bound": _disabled_completion_bound_payload(),
        "completion_bound_pruning_enabled": False,
        "sortie_template_cache": _cache_payload(cache),
        "pricing_state": PricingState.INCOMPLETE_LIMIT.value,
        "can_certify_no_negative": False,
        "uses_true_dual_bpc_certificate": False,
        "manual_best_reduced_cost": None,
        "pricing_best_reduced_cost": None,
        "pricing_rc_audit_pass": False,
        "manual_priced_column_count": 0,
        "all_priced_columns_satisfy_branch_context": True,
        "note": note,
    }


def _representative_universe_total_count(data: LunarIceData) -> int:
    return (1 << len(data.task_ids)) - 1


def _completion_ratio(count: int, total: int) -> float:
    if int(total) <= 0:
        return 0.0
    return round(float(count) / float(total), 12)


def _disabled_completion_bound_payload() -> dict:
    return {
        "enabled": False,
        "pruning_enabled": False,
        "evaluated_label_count": 0,
        "pruned_label_count": 0,
    }


def _cache_payload(cache: DirectPricingCache | None) -> dict:
    if cache is None:
        return {"enabled": False, "entry_count": 0, "hit_count": 0, "miss_count": 0}
    return cache.stats()


def _branch_context_from_reduced_cost_context(context: ReducedCostContext) -> BranchContext:
    if isinstance(context.branch_context, BranchContext):
        return context.branch_context
    if isinstance(context.branch_context, dict):
        return branch_context_from_payload(context.branch_context)
    return BranchContext()


def _cut_context_from_reduced_cost_context(context: ReducedCostContext) -> CutContext:
    if isinstance(context.cut_context, CutContext):
        return context.cut_context
    if isinstance(context.cut_context, dict):
        return cut_context_from_payload(context.cut_context)
    return CutContext()


def _manual_reduced_cost(column: JourneyColumn, duals: JourneyDuals, cut_context: CutContext) -> float:
    return manual_journey_reduced_cost(
        column,
        duals,
        cut_coefficients=cut_context.coefficients_for(column),
    )

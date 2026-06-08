from __future__ import annotations

import hashlib
import math
import json
import tempfile
import time
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import numpy as np

try:
    import pyscipopt  # noqa: F401

    HAS_SCIP = True
except Exception:
    HAS_SCIP = False

from BPC_future.core.branching import BranchConstraint, trip_allowed_by_branch
from BPC_future.core.columns import TripPool, evaluate_timed_trip
from BPC_future.core.cuts import FleetLowerBoundCut, SortieLowerBoundCut, SubsetRowCut, TimePointCapacityCut, add_cut_unique
from BPC_future.core.data import ArcOption, _pareto_filter_arc_options, load_future_data
from BPC_future.core.fleet_bound import (
    _hungarian_min_cost,
    _sortie_path_assignment_nonvehicle_lb,
    apply_fleet_bound_override,
    unavoidable_nonvehicle_cost_lb,
)
from BPC_future.core.journey import JourneyColumn, JourneyPool, build_journey_pool, make_journey, trips_compatible
from BPC_future.master.journey_rmp import (
    JourneyDuals,
    manual_journey_reduced_cost,
    solve_journey_gurobi_barrier_dual,
    solve_journey_pool_master,
    solve_journey_rmp,
    solve_journey_stabilized_dual,
)
from BPC_future.master.rmp import FutureDuals, FutureRMPSolution, manual_reduced_cost, solve_trip_time_rmp
from BPC_future.pricing.journey_pricing import (
    JourneyPricingConfig,
    _CompatibleProfileCache,
    _DirectJourneyCompletionBound,
    _DirectJourneyLabel,
    _DirectNGJourneyLabel,
    _SortiePartialLabel,
    _SortieProfile,
    _SortieProfileCatalogState,
    _StreamingPricingStop,
    _JourneyLabel,
    _TaskSetReducedCostLowerBoundCache,
    _TaskSetResourceLowerBoundCache,
    _UniqueRouteCompletionLowerBound,
    _branch_constraints_cache_key,
    _add_direct_journey_label,
    _add_direct_journey_label_with_cross_count_dominance,
    _add_sortie_profile_skyline,
    _add_sortie_profile_online_skyline,
    _advance_sortie_label_resume_state,
    _complete_sortie_label_profiles,
    _filter_dominated_sortie_profiles,
    _filter_sortie_profile_catalog,
    _filter_sortie_profiles_after_generation,
    _direct_next_sortie_profiles,
    _direct_next_sortie_trips,
    _direct_ng_boundary_memory,
    _direct_ng_branch_certificate_safe,
    _direct_ng_initial_partial,
    _direct_ng_label_key,
    _direct_ng_partial_branch_pruning_safe,
    _direct_ng_neighborhoods,
    _direct_label_diverse_harvest_soft_return_ready,
    _direct_completed_journey_suffix_optimistic_objective,
    _direct_completion_bound_cache_key,
    _direct_repair_target_masks,
    _direct_ng_relaxed_iteration,
    _direct_sortie_partial_completion_bound_check,
    _direct_sortie_profiles_to_trips,
    _cover_dual_sum_for_mask,
    _generate_negative_sortie_profiles,
    _generate_negative_sortie_profiles_by_label_physical_catalog,
    _generate_negative_sortie_profiles_by_best_first_labels,
    _initial_sortie_label_resume_state,
    _instantiate_profile_journey_candidates,
    _cut_masks,
    _add_profile_label,
    _add_sortie_partial_label,
    _dominates_sortie_partial_label,
    _early_return_candidate_count,
    _early_return_negative_candidates_ready,
    _profile_cut_penalty,
    _profile_cut_penalty_pruning_safe,
    _profile_mask_diagnostic_kwargs,
    _journey_task_set_branch_allowed,
    _profile_candidate_return_limit,
    _journey_same_completion_possible,
    _price_journeys_by_profiles,
    _price_journeys_by_streaming_profiles,
    _resume_sortie_profile_catalog,
    _select_negative_journey_candidates,
    _select_nonduplicate_negative_journey_candidates,
    _select_diverse_journey_candidates,
    _solve_best_journey_profile_dp,
    _sortie_label_physical_catalog_key,
    _sortie_partial_label_priority,
    _sortie_profile_mask_allowed_by_branch,
    price_journeys,
    seed_sortie_profile_catalog_from_journeys,
)
from BPC_future.pricing.journey_pricing import (
    PRICING_STATE_CERTIFIED_NO_NEGATIVE,
    PRICING_STATE_DUPLICATE_ONLY,
    PRICING_STATE_FOUND_NEGATIVE,
    PRICING_STATE_INCOMPLETE_LIMIT,
    PRICING_STATE_LOCAL_NO_COLUMN_UNCERTIFIED,
    JourneyPricingResult,
)
from BPC_future.draw.moon_trek_viz import ScenarioConfig, TerrainGrid, sample_operational_scenario
from BPC_future.preprocess.risk_model import RiskModelConfig, build_risk_layer, derive_slope_from_dem
from BPC_future.preprocess.scheduling_augmentation import (
    SchedulingAugmentationConfig,
    augment_scenario_for_multisortie_cvrptw,
)
from BPC_future.preprocess.terrain_graph import TerrainGraphConfig, build_coarse_terrain_graph, build_logical_graph_payload
from BPC_future.pricing.trip_pricing import (
    PricingConfig,
    _PartialNoWaitingPathProfile,
    _clear_sequence_resource_precheck_cache,
    _occupancy_profile,
    _pareto_filter_arc_combinations,
    _pareto_filter_partial_profiles,
    _reduced_cost_at_start,
    _sequence_resource_precheck,
    _sequence_resource_precheck_cache_stats,
    price_timed_trips,
)
from BPC_future.scripts.run_bpc_future import load_config
from BPC_future.solver.driver import _separate_time_occupation_rows, _should_use_bulk_exact_pricing, solve_bpc_future
from BPC_future.solver.driver import _seed_initial_savings_trips
from BPC_future.solver.journey_driver import (
    JourneyBranchStats,
    JourneyNode,
    _choose_journey_branch,
    _filter_journeys_by_branch,
    _journey_certificate_pricing_config,
    _journey_completion_bound_escalation_config,
    _journey_completion_bound_escalation_needed,
    _journey_completion_bound_final_probe_needed,
    _journey_completion_bound_probe_budget,
    _journey_fixed_task_set_repair_enabled,
    _journey_fixed_task_set_repair_pool_targets,
    _journey_fixed_task_set_repair_target_task_sets,
    _journey_new_task_set_sweep_candidate_task_sets,
    _journey_new_task_set_sweep_enabled,
    _journey_hidden_negative_patrol_config,
    _journey_hidden_negative_patrol_after_small_batch_needed,
    _journey_same_dual_supplement_config,
    _journey_same_dual_supplement_needed,
    _journey_pre_exact_completion_bound_handoff_needed,
    _journey_post_seed_profile_reharvest_config,
    _journey_profile_repair_config,
    _journey_replacement_repair_config,
    _JourneyAdditionCount,
    _journey_active_task_sets,
    _journey_allowed_by_branch,
    _journey_branch_same_mass,
    _journey_child_constraint_order,
    _journey_cut_hash,
    _journey_exact_pricing_budget,
    _journey_flat_weak_column_pressure_addition,
    _journey_continue_exact_after_flat_weak_heuristic,
    _journey_analytic_center_priority_task_sets,
    _journey_dual_current_pool_validation,
    _journey_dual_optimal_inequality_bounds,
    _journey_dual_hash,
    _journey_dual_vector,
    _journey_immediate_certificate_no_reserve_config,
    _journey_pre_retry_completion_reserve_time,
    _journey_retry_budget_with_completion_reserve,
    _journey_retry_force_ng_config,
    _journey_replacement_repair_target_task_sets,
    _price_fixed_task_set_representatives,
    _price_new_task_set_sweep,
    _journey_static_cuts,
    _journey_static_subset_row_compactness_score,
    _journey_skip_ordinary_retry_after_profile_materialization_failure,
    _journey_skip_ordinary_retry_after_weak_negative_filtered,
    _journey_learning_certificate_gate_disabled,
    _journey_learning_filter_true_rc_enabled,
    _journey_learning_pricing_max_rounds,
    _journey_learning_pricing_config,
    _journey_learning_pricing_duals,
    _journey_learning_runtime_for_pricing,
    _journey_learning_true_rc_filter,
    _journey_learning_certificate_true_rc_fallback_keep_threshold,
    _journey_learning_certificate_true_rc_fallback_max_kept_per_round,
    _journey_learning_certificate_true_rc_keep_threshold,
    _journey_learning_certificate_true_rc_max_kept_per_round,
    _journey_learning_true_rc_keep_threshold,
    _journey_learning_true_rc_max_kept_per_round,
    _journey_learning_true_rc_filter_parameters,
    _JourneyLearningRuntime,
    _JourneyDualAveragingRuntime,
    _journey_dual_average_direct_patrol_config,
    _journey_dual_averaging_pricing_duals,
    _journey_pricing_caches_for_learning_pass,
    _journey_exact_pricing_duals,
    _journey_pricing_certificate_rejection_reason,
    _journey_pricing_is_global_certificate,
    _journey_pricing_state,
    _journey_promote_duplicate_only_final_judge_certificate,
    _journey_reduced_cost_components,
    _hidden_negative_miss_diagnostics,
    _log_hidden_negative_audit,
    _log_journey_addition,
    _journey_task_set_dominance_safe,
    _journey_forbidden_signatures_for_node,
    _add_priced_journeys,
    _maybe_restart_journey_pool,
    _journey_pool_restart_triggered,
    _journey_progress_classification,
    _journey_node_depth_pricing_config,
    _journey_pricing_config,
    _journey_should_early_branch,
    _journey_should_skip_short_exact_pricing,
    _ordered_journey_child_constraints,
    _process_journey_branch_node,
    _select_journey_pricing_duals,
    _should_run_journey_pool_probe,
    _update_journey_fleet_limit,
    _validate_journey_required_components,
    solve_bpc_future_journey,
)
from BPC_future.solver.logger import FutureLogger

try:
    import rasterio
    from rasterio.transform import from_origin

    HAS_RASTERIO = True
except Exception:
    HAS_RASTERIO = False


class BPCFutureTests(unittest.TestCase):
    def test_future_python_modules_do_not_import_legacy_solver(self):
        root = Path(__file__).resolve().parents[1]
        forbidden = (
            "from " + "bpc",
            "import " + "bpc",
            "from " + "branchpricecut",
            "import " + "branchpricecut",
        )
        offenders = []
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if any(token in text for token in forbidden):
                offenders.append(str(path.relative_to(root)))
        self.assertEqual(offenders, [])

    def test_load_future_data_builds_closure(self):
        data = replace(load_future_data("very_small"), vehicles=(1, 2, 3, 4))
        self.assertEqual(data.name, "very_small")
        self.assertEqual(len(data.tasks), 4)
        self.assertIn((0, data.tasks[0]), data.closure)
        self.assertGreater(data.arc(0, data.tasks[0]).cost, 0.0)

    def test_timed_trip_feasibility_and_occupation(self):
        data = load_future_data("very_small")
        trip = evaluate_timed_trip(data, (1, 2), 0.0, time_bucket_size=5.0)
        self.assertIsNotNone(trip)
        assert trip is not None
        self.assertLessEqual(trip.load, data.capacity)
        self.assertGreater(trip.end_time, trip.start_time)
        self.assertTrue(trip.occupancy)
        self.assertLessEqual(max(trip.occupancy.values()), 1.0)

    def test_branch_separate_filters_trip(self):
        data = load_future_data("very_small")
        trip = evaluate_timed_trip(data, (1, 2), 0.0, time_bucket_size=5.0)
        self.assertIsNotNone(trip)
        assert trip is not None
        constraint = BranchConstraint("separate_vehicle", 1, 2)
        self.assertFalse(trip_allowed_by_branch(trip, data.vehicles[0], (constraint,)))

    def test_journey_task_set_branch_allowed(self):
        same = BranchConstraint("same_vehicle", 1, 2)
        separate = BranchConstraint("separate_vehicle", 1, 2)
        self.assertTrue(_journey_task_set_branch_allowed(frozenset({1, 2}), (same,)))
        self.assertTrue(_journey_task_set_branch_allowed(frozenset({3}), (same,)))
        self.assertFalse(_journey_task_set_branch_allowed(frozenset({1}), (same,)))
        self.assertFalse(_journey_task_set_branch_allowed(frozenset({1, 2}), (separate,)))
        self.assertTrue(_journey_task_set_branch_allowed(frozenset({1, 3}), (separate,)))

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_pricing_respects_ryan_foster_branch_constraints(self):
        data = load_future_data("very_small")
        config = JourneyPricingConfig(
            time_bucket_size=5.0,
            start_time_step=10.0,
            max_tasks_per_trip=2,
            time_limit=5.0,
            max_dp_states=2000,
            max_returned_journeys=10,
            early_return_negative=True,
            early_return_negative_min_count=1,
            profile_labeling_enabled=True,
        )
        duals = JourneyDuals(cover={int(task): 200.0 for task in data.tasks}, fleet_limit=0.0)
        result = price_journeys(
            data,
            duals=duals,
            branch_constraints=(BranchConstraint("separate_vehicle", 1, 2),),
            config=config,
        )
        self.assertNotEqual(result.status, "UNSUPPORTED")
        for journey in result.journeys:
            self.assertTrue(
                _journey_task_set_branch_allowed(journey.task_set, (BranchConstraint("separate_vehicle", 1, 2),))
            )

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_rmp_reduced_cost_matches_manual_formula(self):
        data = load_future_data("very_small")
        trips = _single_task_grid_trips(data, bucket=10.0)
        self.assertGreaterEqual(len(trips), len(data.tasks))
        solution = solve_trip_time_rmp(
            data,
            trips,
            tuple(),
            time_bucket_size=10.0,
            capture_reduced_costs=True,
        )
        self.assertTrue(solution.optimal)
        assert solution.duals is not None
        for (trip_id, vehicle), solver_rc in solution.theta_reduced_costs.items():
            manual = manual_reduced_cost(trips[trip_id], vehicle, solution.duals, tuple())
            self.assertAlmostEqual(solver_rc, manual, places=5)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_rmp_phase1_uses_artificial_without_big_m_costs(self):
        data = load_future_data("very_small")
        solution = solve_trip_time_rmp(
            data,
            [],
            tuple(),
            time_bucket_size=10.0,
            phase="phase1",
        )
        self.assertTrue(solution.optimal)
        self.assertAlmostEqual(solution.objective, len(data.tasks), places=6)
        self.assertAlmostEqual(solution.artificial_mass, len(data.tasks), places=6)

    def test_phase1_reduced_cost_ignores_trip_objective_cost(self):
        data = load_future_data("very_small")
        trip = evaluate_timed_trip(data, (1,), 0.0, time_bucket_size=10.0)
        self.assertIsNotNone(trip)
        assert trip is not None
        vehicle = data.vehicles[0]
        duals = FutureDuals(
            cover={1: 5.0},
            task_vehicle={},
            sortie_count={vehicle: 0.0},
            time_occupation={},
            ordering={},
            branches={},
        )
        phase1_rc = manual_reduced_cost(trip, vehicle, duals, tuple(), phase="phase1")
        phase2_rc = manual_reduced_cost(trip, vehicle, duals, tuple(), phase="phase2")
        self.assertAlmostEqual(phase2_rc - phase1_rc, trip.cost, places=6)

    def test_pricing_filters_false_stabilized_candidate_by_true_dual(self):
        data = load_future_data("very_small")
        vehicle = data.vehicles[0]
        fake_duals = FutureDuals(
            cover={task: 100.0 for task in data.tasks},
            task_vehicle={},
            sortie_count={vehicle: 0.0},
            time_occupation={},
            ordering={},
            branches={},
        )
        true_duals = FutureDuals(
            cover={task: 0.0 for task in data.tasks},
            task_vehicle={},
            sortie_count={vehicle: 0.0},
            time_occupation={},
            ordering={},
            branches={},
        )
        result = price_timed_trips(
            data,
            fake_duals,
            tuple(),
            vehicle=vehicle,
            config=PricingConfig(time_bucket_size=20.0, max_tasks_per_trip=1, heuristic=True, max_returned_trips=10),
            true_duals=true_duals,
        )
        self.assertEqual(result.negative_trips, 0)
        self.assertGreater(result.false_candidate_trips, 0)

    def test_sequence_resource_precheck_cache_reuses_exact_result(self):
        data = load_future_data("very_small")
        sequence = tuple(int(task) for task in data.tasks[:2])
        _clear_sequence_resource_precheck_cache()
        first = _sequence_resource_precheck(data, sequence)
        stats_after_first = _sequence_resource_precheck_cache_stats(data)
        second = _sequence_resource_precheck(data, sequence)
        stats_after_second = _sequence_resource_precheck_cache_stats(data)
        self.assertEqual(first, second)
        self.assertEqual(stats_after_first["misses"], 1)
        self.assertEqual(stats_after_second["hits"], 1)
        self.assertEqual(stats_after_second["entries"], 1)

    def test_task_set_resource_lower_bound_cache_prunes_impossible_set(self):
        data = load_future_data("very_small")
        limited = replace(data, energy_limit=8.0, capacity=999.0)
        task_to_bit = {int(task): index for index, task in enumerate(limited.tasks)}
        first, second = int(limited.tasks[0]), int(limited.tasks[1])
        singleton_mask = 1 << task_to_bit[first]
        pair_mask = singleton_mask | (1 << task_to_bit[second])

        cache = _TaskSetResourceLowerBoundCache(limited, task_to_bit, enabled=True)
        self.assertTrue(cache.maybe_feasible(singleton_mask))
        self.assertFalse(cache.maybe_feasible(pair_mask))
        self.assertFalse(cache.maybe_feasible(pair_mask))
        self.assertIn(pair_mask, cache.feasible_cache)

        disabled = _TaskSetResourceLowerBoundCache(limited, task_to_bit, enabled=False)
        self.assertTrue(disabled.maybe_feasible(pair_mask))

    def test_label_online_profile_dominance_matches_batch_filter(self):
        data = load_future_data("very_small")
        vehicle = data.vehicles[0]
        duals = FutureDuals(
            cover={int(task): 0.0 for task in data.tasks},
            task_vehicle={},
            sortie_count={int(vehicle): 0.0},
            time_occupation={},
            ordering={},
            branches={},
            cuts={},
        )
        task_order = tuple(int(task) for task in data.tasks)
        task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
        base_config = JourneyPricingConfig(
            max_tasks_per_trip=3,
            profile_cross_dominance_enabled=True,
            profile_online_dominance_enabled=False,
        )
        offline_state = _initial_sortie_label_resume_state(data, duals)
        _advance_sortie_label_resume_state(
            data,
            duals,
            offline_state,
            config=base_config,
            deadline=None,
            task_order=task_order,
            threshold=float("inf"),
            task_to_bit=task_to_bit,
            max_tasks=3,
        )
        batch_filtered, _pruned = _filter_dominated_sortie_profiles(list(offline_state.profiles_by_key.values()))

        online_config = JourneyPricingConfig(
            max_tasks_per_trip=3,
            profile_cross_dominance_enabled=True,
            profile_online_dominance_enabled=True,
        )
        online_state = _initial_sortie_label_resume_state(data, duals)
        _advance_sortie_label_resume_state(
            data,
            duals,
            online_state,
            config=online_config,
            deadline=None,
            task_order=task_order,
            threshold=float("inf"),
            task_to_bit=task_to_bit,
            max_tasks=3,
        )
        online_profiles = [profile for group in (online_state.profiles_by_mask or {}).values() for profile in group]

        def key(profile: _SortieProfile) -> tuple:
            return (
                int(profile.mask),
                round(float(profile.contribution), 6),
                round(float(profile.lower_start), 6),
                round(float(profile.upper_start), 6),
                round(float(profile.end_offset), 6),
            )

        self.assertEqual(sorted(key(profile) for profile in online_profiles), sorted(key(profile) for profile in batch_filtered))

    def test_seed_sortie_profile_catalog_from_hidden_journey_is_bounded(self):
        data = load_future_data("very_small")
        vehicle = data.vehicles[0]
        task = int(data.tasks[0])
        trip = evaluate_timed_trip(data, (task,), 0.0, time_bucket_size=10.0)
        self.assertIsNotNone(trip)
        assert trip is not None
        journey = make_journey(data, [trip])
        self.assertIsNotNone(journey)
        assert journey is not None
        duals = JourneyDuals(
            cover={int(item): 10.0 for item in data.tasks},
            fleet_limit=0.0,
            cuts={},
        )
        config = JourneyPricingConfig(
            time_bucket_size=10.0,
            max_tasks_per_trip=2,
            profile_labeling_physical_catalog_resume_enabled=True,
            profile_cross_dominance_enabled=True,
            profile_online_dominance_enabled=True,
        )
        trip_cache: dict[tuple, object] = {}
        stats = seed_sortie_profile_catalog_from_journeys(
            data,
            duals,
            [journey],
            config=config,
            trip_cache=trip_cache,
        )
        self.assertTrue(stats.enabled)
        self.assertFalse(stats.catalog_hit)
        self.assertEqual(stats.seeded_profiles, 1)
        self.assertEqual(stats.forced_seed_profiles, 0)
        self.assertEqual(stats.catalog_size_before, 0)
        self.assertEqual(stats.catalog_size_after, 1)
        state = next(iter(trip_cache.values()))
        profiles = list(getattr(state, "profiles_by_key").values())
        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles[0].sequence, (task,))
        self.assertAlmostEqual(profiles[0].lower_start, trip.start_time, places=6)
        self.assertAlmostEqual(profiles[0].upper_start, trip.start_time, places=6)
        self.assertAlmostEqual(profiles[0].end_offset, trip.end_time - trip.start_time, places=6)

        repeat = seed_sortie_profile_catalog_from_journeys(
            data,
            duals,
            [journey],
            config=config,
            trip_cache=trip_cache,
        )
        self.assertTrue(repeat.catalog_hit)
        self.assertEqual(repeat.seeded_profiles, 0)
        self.assertEqual(repeat.forced_seed_profiles, 0)
        self.assertEqual(repeat.duplicate_or_dominated_profiles, 1)
        self.assertEqual(repeat.catalog_size_after, 1)

    def test_incomplete_pricing_does_not_certificate(self):
        data = load_future_data("very_small")
        vehicle = data.vehicles[0]
        duals = FutureDuals(
            cover={task: 0.0 for task in data.tasks},
            task_vehicle={},
            sortie_count={vehicle: 0.0},
            time_occupation={},
            ordering={},
            branches={},
        )
        result = price_timed_trips(
            data,
            duals,
            tuple(),
            vehicle=vehicle,
            config=PricingConfig(time_bucket_size=1.0, max_tasks_per_trip=2, max_sequences=1),
        )
        self.assertFalse(result.exhausted)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_time_occupation_blocks_overlapping_integral_trips(self):
        data = load_future_data("very_small")
        trip1 = evaluate_timed_trip(data, (1,), 0.0, time_bucket_size=20.0)
        trip2 = evaluate_timed_trip(data, (2,), 0.0, time_bucket_size=20.0)
        self.assertIsNotNone(trip1)
        self.assertIsNotNone(trip2)
        trips = [trip1, trip2]
        trips.extend(trip for trip in _single_task_grid_trips(data, bucket=20.0) if trip.tasks not in {(1,), (2,)})
        solution = solve_trip_time_rmp(data, trips, tuple(), time_bucket_size=20.0)
        self.assertTrue(solution.optimal)
        # Two overlapping trips cannot both be assigned integrally to the same vehicle
        # in the same occupation bucket.
        for vehicle in data.vehicles:
            overlap_mass = sum(
                value
                for trip, r, value in solution.trip_values
                if r == vehicle and trip.tasks in {(1,), (2,)} and trip.start_time == 0.0
            )
            self.assertLessEqual(overlap_mass, 1.0 + 1.0e-6)

    def test_pricing_keeps_one_best_time_per_structure(self):
        data = load_future_data("very_small")
        vehicle = data.vehicles[0]
        duals = FutureDuals(
            cover={task: 100.0 if task == 1 else 0.0 for task in data.tasks},
            task_vehicle={},
            sortie_count={vehicle: 0.0},
            time_occupation={},
            ordering={},
            branches={},
        )
        result = price_timed_trips(
            data,
            duals,
            tuple(),
            vehicle=vehicle,
            config=PricingConfig(time_bucket_size=1.0, max_tasks_per_trip=1, max_returned_trips=100),
        )
        signatures = [trip.tasks for trip in result.trips]
        self.assertEqual(len(signatures), len(set(signatures)))

    def test_no_task_waiting_policy_rejects_early_arrival(self):
        data = load_future_data("very_small")
        task = data.tasks[0]
        data.instance.setdefault("scheduling", {})["task_waiting_allowed"] = False
        data.instance["tasks"][str(task)]["r"] = 100.0
        data.instance["tasks"][str(task)]["D"] = 200.0
        self.assertIsNone(evaluate_timed_trip(data, (task,), 0.0, time_bucket_size=10.0))

        data.instance["scheduling"]["task_waiting_allowed"] = True
        trip = evaluate_timed_trip(data, (task,), 0.0, time_bucket_size=10.0)
        self.assertIsNotNone(trip)
        assert trip is not None
        self.assertAlmostEqual(trip.service_start[str(task)], 100.0)

    @unittest.skipUnless(HAS_RASTERIO, "rasterio unavailable")
    def test_derive_slope_from_dem_plane(self):
        rows = cols = 8
        dem = np.tile(np.arange(cols, dtype="float32"), (rows, 1))
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            dem_path = tmp_path / "dem.tif"
            slope_path = tmp_path / "slope.tif"
            profile = {
                "driver": "GTiff",
                "height": rows,
                "width": cols,
                "count": 1,
                "dtype": "float32",
                "crs": "EPSG:4326",
                "transform": from_origin(0, rows, 1, 1),
            }
            with rasterio.open(dem_path, "w", **profile) as dst:
                dst.write(dem, 1)
            metadata = derive_slope_from_dem(dem_path, slope_path, width_km=0.008, height_km=0.008)
            self.assertEqual(metadata["valid_cells"], rows * cols)
            with rasterio.open(slope_path) as src:
                slope = src.read(1)
            self.assertTrue(np.all(np.isfinite(slope)))
            self.assertAlmostEqual(float(np.median(slope)), 45.0, delta=1.0e-4)

    @unittest.skipUnless(HAS_RASTERIO, "rasterio unavailable")
    def test_risk_model_builds_deterministic_layer(self):
        dem = np.array(
            [
                [0, 0, 0, 0, 0],
                [0, 1, 2, 3, 4],
                [0, 2, 4, 6, 8],
                [0, 3, 6, 9, 12],
                [0, 4, 8, 12, 16],
            ],
            dtype="float32",
        )
        slope = np.array(
            [
                [1, 5, 10, 20, 31],
                [1, 5, 10, 20, 31],
                [1, 5, 10, 20, 31],
                [1, 5, 10, 20, 31],
                [1, 5, 10, 20, 31],
            ],
            dtype="float32",
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            dem_path = tmp_path / "dem.tif"
            slope_path = tmp_path / "slope.tif"
            profile = {
                "driver": "GTiff",
                "height": dem.shape[0],
                "width": dem.shape[1],
                "count": 1,
                "dtype": "float32",
                "crs": "EPSG:4326",
                "transform": from_origin(0, 5, 1, 1),
            }
            with rasterio.open(dem_path, "w", **profile) as dst:
                dst.write(dem, 1)
            with rasterio.open(slope_path, "w", **profile) as dst:
                dst.write(slope, 1)
            metadata = build_risk_layer(
                dem_path,
                slope_path,
                tmp_path / "processed",
                config=RiskModelConfig(impassable_slope_deg=30.0, roughness_reference_m=4.0),
            )
            self.assertEqual(metadata["statistics"]["valid_cells"], 25)
            self.assertEqual(metadata["statistics"]["impassable_cells"], 5)
            risk_npz = np.load(tmp_path / "processed" / "risk_grid.npz")
            risk = risk_npz["risk"]
            self.assertGreaterEqual(float(np.nanmin(risk)), 0.0)
            self.assertLessEqual(float(np.nanmax(risk)), 1.0)

    def test_scenario_sampler_respects_roundtrip_screen(self):
        rows = cols = 50
        grid = TerrainGrid(
            dem=np.zeros((rows, cols), dtype="float32"),
            slope=np.ones((rows, cols), dtype="float32"),
            roughness=np.zeros((rows, cols), dtype="float32"),
            risk=np.full((rows, cols), 0.2, dtype="float32"),
            impassable=np.zeros((rows, cols), dtype=bool),
            valid=np.ones((rows, cols), dtype=bool),
            width_km=20.0,
            height_km=20.0,
            source_dir=Path("synthetic"),
        )
        scenario = sample_operational_scenario(
            grid,
            ScenarioConfig(
                seed=3,
                task_count=8,
                operation_radius_km=10.0,
                vehicle_max_roundtrip_km=14.0,
                min_point_spacing_km=0.2,
            ),
        )
        depot = scenario["depot"]["xy_km"]
        self.assertEqual(scenario["depot"]["requested_xy_km"], [10.0, 10.0])
        self.assertTrue(scenario["connectivity"]["all_tasks_in_depot_component"])
        self.assertGreaterEqual(scenario["connectivity"]["depot_component_cells"], len(scenario["tasks"]) + 1)
        for task in scenario["tasks"]:
            self.assertFalse(task["impassable"])
            dist = math.hypot(task["xy_km"][0] - depot[0], task["xy_km"][1] - depot[1])
            self.assertLessEqual(2.0 * dist, 14.0 + 1.0e-6)

    def test_coarse_terrain_graph_downsamples_passability(self):
        rows = cols = 8
        impassable = np.zeros((rows, cols), dtype=bool)
        impassable[0:2, 0:2] = True
        grid = TerrainGrid(
            dem=np.zeros((rows, cols), dtype="float32"),
            slope=np.ones((rows, cols), dtype="float32"),
            roughness=np.zeros((rows, cols), dtype="float32"),
            risk=np.full((rows, cols), 0.2, dtype="float32"),
            impassable=impassable,
            valid=np.ones((rows, cols), dtype=bool),
            width_km=8.0,
            height_km=8.0,
            source_dir=Path("synthetic"),
        )
        graph = build_coarse_terrain_graph(
            grid,
            TerrainGraphConfig(grid_size=4, min_valid_fraction=1.0, max_impassable_fraction=0.0),
        )
        self.assertEqual(graph.shape, (4, 4))
        self.assertFalse(graph.passable[0, 0])
        self.assertEqual(int(graph.passable.sum()), 15)

    def test_logical_graph_keeps_bounded_complete_path_options(self):
        rows = cols = 8
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "terrain"
            (root / "processed").mkdir(parents=True)
            (root / "metadata").mkdir(parents=True)
            np.savez(
                root / "processed" / "risk_grid.npz",
                dem=np.zeros((rows, cols), dtype="float32"),
                slope=np.ones((rows, cols), dtype="float32"),
                roughness=np.zeros((rows, cols), dtype="float32"),
                risk=np.full((rows, cols), 0.2, dtype="float32"),
                impassable=np.zeros((rows, cols), dtype=bool),
                valid=np.ones((rows, cols), dtype=bool),
            )
            (root / "metadata" / "bbox.json").write_text(
                json.dumps({"patch": {"width_km": 8.0, "height_km": 8.0}}),
                encoding="utf-8",
            )
            scenario = {
                "seed": 11,
                "operation_region": {"center_xy_km": [4.0, 4.0], "radius_km": 4.0},
                "vehicle": {"max_roundtrip_km": 30.0},
                "depot": {"id": "depot", "xy_km": [1.0, 7.0]},
                "tasks": [
                    {"id": "task_1", "xy_km": [7.0, 7.0]},
                    {"id": "task_2", "xy_km": [7.0, 1.0]},
                ],
            }
            scenario_path = Path(tmp) / "scenario.json"
            scenario_path.write_text(json.dumps(scenario), encoding="utf-8")

            payload = build_logical_graph_payload(
                root,
                scenario_path,
                config=TerrainGraphConfig(grid_size=4, min_valid_fraction=1.0, max_impassable_fraction=0.0),
            )

        logical = payload["logical_graph"]
        self.assertEqual(logical["node_count"], 3)
        self.assertEqual(logical["directed_edge_count"], 6)
        self.assertEqual(logical["feasible_directed_edge_count"], 6)
        for edge in logical["edges"]:
            self.assertTrue(edge["feasible"])
            self.assertIn(edge["best_option_by_generalized_cost"], {"low_time", "low_energy", "low_risk"})
            self.assertGreaterEqual(edge["option_count"], 1)
            self.assertLessEqual(edge["option_count"], 3)
            self.assertEqual(edge["option_count"], len(edge["path_options"]))
            for option in edge["path_options"]:
                self.assertIn(option["path_type"], {"low_time", "low_energy", "low_risk"})
                self.assertTrue(option["aliases"])
                self.assertEqual(option["path_cell_count"], len(option["path_cells"]))
                self.assertEqual(option["path_cell_count"], len(option["path_xy"]))
                self.assertGreater(option["path_cell_count"], 1)
                for key in ("generalized_cost", "path_distance_km", "travel_time_min", "energy_proxy", "risk_integral"):
                    self.assertIn(key, option)
                    self.assertGreaterEqual(option[key], 0.0)

    def test_scheduling_augmentation_adds_multisortie_fields(self):
        scenario = {
            "seed": 1,
            "depot": {"id": "depot", "xy_km": [10.0, 10.0]},
            "vehicle": {"max_roundtrip_km": 30.0, "max_roundtrip_energy_proxy": 70.0},
            "tasks": [
                {
                    "id": "task_1",
                    "xy_km": [12.0, 10.0],
                    "risk": 0.25,
                    "slope_deg": 8.0,
                    "roughness_m": 1.0,
                }
            ],
        }
        augmented = augment_scenario_for_multisortie_cvrptw(
            scenario,
            config=SchedulingAugmentationConfig(horizon_min=720.0, recharge_power_proxy_per_min=2.0),
        )

        self.assertEqual(augmented["problem_type"], "multi_sortie_cvrptw")
        self.assertFalse(augmented["scheduling"]["task_waiting_allowed"])
        self.assertTrue(augmented["scheduling"]["sortie_policy"]["full_recharge_after_each_sortie"])
        self.assertEqual(
            augmented["scheduling"]["sortie_policy"]["recharge_time_formula"],
            "recharge_time_min = energy_used_proxy / recharge_power_proxy_per_min",
        )
        vehicle = augmented["vehicle"]
        self.assertEqual(vehicle["recharge_policy"], "full_after_each_sortie")
        self.assertEqual(vehicle["rho"], 2.0)
        self.assertEqual(vehicle["usable_battery_capacity_proxy"], 80.0)
        self.assertEqual(vehicle["survival_energy_reserve_proxy"], 10.0)
        self.assertEqual(vehicle["max_roundtrip_energy_proxy"], 70.0)
        self.assertEqual(vehicle["sortie_energy_capacity_proxy"], 70.0)
        self.assertEqual(vehicle["B_use"], 70.0)
        task = augmented["tasks"][0]
        for key in ("demand", "service_time_min", "service_energy_proxy", "ready_time_min", "due_time_min"):
            self.assertIn(key, task)
        for alias in ("d", "sigma", "g", "c_srv", "r", "D"):
            self.assertIn(alias, task)
        self.assertEqual(task["service_start_rule"], "arrival_time_must_be_inside_time_window; no waiting at task")

    def test_logical_graph_loader_keeps_path_options_and_energy_reserve(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=30.0, inbound_energy=20.0)
            data = load_future_data(str(graph_path))

        self.assertEqual(data.energy_limit, 70.0)
        self.assertEqual(data.usable_battery_capacity, 80.0)
        self.assertEqual(data.reserve_energy_proxy, 10.0)
        self.assertEqual(len(data.options(0, 1)), 3)
        self.assertEqual({option.path_type for option in data.options(0, 1)}, {"low_time", "low_energy", "low_risk"})
        trip = evaluate_timed_trip(data, (1,), 0.0, time_bucket_size=5.0)
        self.assertIsNotNone(trip)
        assert trip is not None
        self.assertLessEqual(trip.energy, 70.0)
        self.assertGreater(trip.survival_energy, 0.0)

    def test_logical_graph_trip_rejects_energy_that_consumes_survival_reserve(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=40.0, inbound_energy=30.0)
            data = load_future_data(str(graph_path))

        self.assertIsNone(evaluate_timed_trip(data, (1,), 0.0, time_bucket_size=5.0))

    def test_path_option_signature_distinguishes_same_task_and_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))

        pool = TripPool()
        low_time = (data.options(0, 1)[0], data.options(1, 0)[0])
        low_risk = (data.options(0, 1)[-1], data.options(1, 0)[-1])
        trip_a = evaluate_timed_trip(data, (1,), 0.0, time_bucket_size=5.0, arc_options=low_time)
        trip_b = evaluate_timed_trip(data, (1,), 0.0, time_bucket_size=5.0, arc_options=low_risk)
        self.assertIsNotNone(trip_a)
        self.assertIsNotNone(trip_b)
        assert trip_a is not None and trip_b is not None
        self.assertNotEqual(trip_a.signature, trip_b.signature)
        pool.add(trip_a)
        pool.add(trip_b)
        self.assertEqual(len(pool.trips), 2)

    def test_journey_pool_keeps_cheapest_column_per_task_set(self):
        pool = JourneyPool()
        expensive = JourneyColumn(
            id=-1,
            trips=tuple(),
            task_set=frozenset({1, 2}),
            start_time=0.0,
            end_time=10.0,
            travel_cost=100.0,
            fixed_vehicle_cost=50.0,
            cost=150.0,
            signature=(((1, 2), ("expensive",), 0.0),),
        )
        dominated = JourneyColumn(
            id=-1,
            trips=tuple(),
            task_set=frozenset({1, 2}),
            start_time=0.0,
            end_time=9.0,
            travel_cost=110.0,
            fixed_vehicle_cost=50.0,
            cost=160.0,
            signature=(((1, 2), ("dominated",), 0.0),),
        )
        pool.add(expensive)
        stored = pool.add(dominated)
        self.assertEqual(len(pool.journeys), 1)
        self.assertEqual(stored.signature, expensive.signature)
        self.assertEqual(pool.by_task_set[frozenset({1, 2})].cost, 150.0)
        self.assertIs(pool.by_signature[expensive.signature], pool.journeys[0])
        self.assertNotIn(dominated.signature, pool.by_signature)

    def test_journey_pool_replaces_same_task_set_with_cheaper_column(self):
        pool = JourneyPool()
        expensive = JourneyColumn(
            id=-1,
            trips=tuple(),
            task_set=frozenset({1, 2}),
            start_time=0.0,
            end_time=10.0,
            travel_cost=100.0,
            fixed_vehicle_cost=50.0,
            cost=150.0,
            signature=(((1, 2), ("expensive",), 0.0),),
        )
        cheaper = JourneyColumn(
            id=-1,
            trips=tuple(),
            task_set=frozenset({1, 2}),
            start_time=0.0,
            end_time=9.0,
            travel_cost=90.0,
            fixed_vehicle_cost=50.0,
            cost=140.0,
            signature=(((1, 2), ("cheaper",), 0.0),),
        )
        pool.add(expensive)
        stored = pool.add(cheaper)
        self.assertEqual(len(pool.journeys), 1)
        self.assertEqual(stored.id, 0)
        self.assertEqual(stored.signature, cheaper.signature)
        self.assertEqual(pool.journeys[0].cost, 140.0)
        self.assertNotIn(expensive.signature, pool.by_signature)
        self.assertIs(pool.by_signature[cheaper.signature], pool.journeys[0])

    def test_journey_pool_can_disable_task_set_dominance(self):
        pool = JourneyPool(task_set_dominance_enabled=False)
        first = JourneyColumn(
            id=-1,
            trips=tuple(),
            task_set=frozenset({1, 2}),
            start_time=0.0,
            end_time=10.0,
            travel_cost=100.0,
            fixed_vehicle_cost=50.0,
            cost=150.0,
            signature=(((1, 2), ("first",), 0.0),),
        )
        second = JourneyColumn(
            id=-1,
            trips=tuple(),
            task_set=frozenset({1, 2}),
            start_time=0.0,
            end_time=9.0,
            travel_cost=90.0,
            fixed_vehicle_cost=50.0,
            cost=140.0,
            signature=(((1, 2), ("second",), 0.0),),
        )
        pool.add(first)
        pool.add(second)
        self.assertEqual(len(pool.journeys), 2)
        self.assertEqual(pool.by_task_set[frozenset({1, 2})].signature, second.signature)
        self.assertIs(pool.by_signature[first.signature], pool.journeys[0])
        self.assertIs(pool.by_signature[second.signature], pool.journeys[1])

    def test_add_priced_journeys_reports_changed_task_sets(self):
        pool = JourneyPool()
        first = JourneyColumn(
            id=-1,
            trips=tuple(),
            task_set=frozenset({1, 2}),
            start_time=0.0,
            end_time=10.0,
            travel_cost=100.0,
            fixed_vehicle_cost=50.0,
            cost=150.0,
            signature=(((1, 2), ("first",), 0.0),),
        )
        replacement = JourneyColumn(
            id=-1,
            trips=tuple(),
            task_set=frozenset({1, 2}),
            start_time=0.0,
            end_time=9.0,
            travel_cost=90.0,
            fixed_vehicle_cost=50.0,
            cost=140.0,
            signature=(((1, 2), ("replacement",), 0.0),),
        )
        dominated = JourneyColumn(
            id=-1,
            trips=tuple(),
            task_set=frozenset({1, 2}),
            start_time=0.0,
            end_time=11.0,
            travel_cost=110.0,
            fixed_vehicle_cost=50.0,
            cost=160.0,
            signature=(((1, 2), ("dominated",), 0.0),),
        )
        other = JourneyColumn(
            id=-1,
            trips=tuple(),
            task_set=frozenset({3}),
            start_time=0.0,
            end_time=5.0,
            travel_cost=40.0,
            fixed_vehicle_cost=50.0,
            cost=90.0,
            signature=(((3,), ("other",), 0.0),),
        )

        added = _add_priced_journeys(pool, [first, replacement, dominated, other])

        self.assertEqual(int(added), 3)
        self.assertEqual(added.new_journeys, 2)
        self.assertEqual(added.replacement_journeys, 1)
        self.assertEqual(added.unchanged_journeys, 1)
        self.assertEqual(added.new_task_sets, (frozenset({1, 2}), frozenset({3})))
        self.assertEqual(added.replacement_task_sets, (frozenset({1, 2}),))
        self.assertEqual(added.changed_task_sets, (frozenset({1, 2}), frozenset({3})))

    def test_journey_addition_log_reports_active_support_overlap(self):
        active_values = [
            (SimpleNamespace(task_set=frozenset({1, 2}), signature="active"), 0.75),
            (SimpleNamespace(task_set=frozenset({4}), signature="inactive_zero"), 0.0),
        ]
        active_task_sets = _journey_active_task_sets(active_values)
        added = _JourneyAdditionCount(
            2,
            new_journeys=1,
            replacement_journeys=1,
            unchanged_journeys=0,
            new_task_sets=(frozenset({3}),),
            replacement_task_sets=(frozenset({1, 2}),),
            changed_task_sets=(frozenset({1, 2}), frozenset({3})),
        )
        pricing = SimpleNamespace(
            journeys=(
                SimpleNamespace(signature="replacement", task_set=frozenset({1, 2})),
                SimpleNamespace(signature="new", task_set=frozenset({3})),
            )
        )
        events: list[tuple[str, dict[str, Any]]] = []
        logger = SimpleNamespace(log=lambda name, **payload: events.append((name, payload)))

        _log_journey_addition(
            logger,
            pricing,
            added,
            7,
            pricing_kind="exact",
            active_task_sets=active_task_sets,
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][0], "journey_column_addition")
        payload = events[0][1]
        self.assertEqual(payload["active_changed_task_set_count"], 1)
        self.assertEqual(payload["active_new_task_set_count"], 0)
        self.assertEqual(payload["active_replacement_task_set_count"], 1)
        self.assertEqual(payload["inactive_changed_task_set_count"], 1)
        self.assertEqual(payload["addition_productivity_class"], "active_replacement_task_set")
        self.assertEqual(payload["requested_task_set_count"], 2)
        self.assertEqual(payload["changed_task_set_count"], 2)
        self.assertEqual(payload["new_task_set_count"], 1)
        self.assertEqual(payload["replacement_task_set_count"], 1)
        self.assertEqual(payload["changed_journey_ratio"], 1.0)
        self.assertEqual(payload["new_journey_ratio"], 0.5)
        self.assertEqual(payload["replacement_journey_ratio"], 0.5)
        self.assertEqual(payload["unchanged_journey_ratio"], 0.0)

    def test_pre_exact_completion_bound_handoff_is_tail_only(self):
        config = {
            "journey_certificate_completion_bound_pre_exact_handoff_enabled": True,
            "journey_certificate_completion_bound_pre_exact_handoff_min_flat_rounds": 3,
            "journey_certificate_completion_bound_pre_exact_handoff_disable_on_branch_depth_gt": 0,
            "journey_certificate_completion_bound_pre_exact_handoff_slack_time": 2.0,
            "journey_certificate_completion_bound_after_retry_reserve_time": 2.0,
        }

        self.assertTrue(
            _journey_pre_exact_completion_bound_handoff_needed(
                config,
                remaining=7.5,
                final_min_time=6.0,
                min_pricing_time=1.0,
                certificate_candidate=True,
                certificate_flat_rounds=4,
                depth=0,
                final_completion_bound_eligible=True,
                exact_completion_bound_enabled=False,
            )
        )
        self.assertFalse(
            _journey_pre_exact_completion_bound_handoff_needed(
                config,
                remaining=30.0,
                final_min_time=6.0,
                min_pricing_time=1.0,
                certificate_candidate=True,
                certificate_flat_rounds=4,
                depth=0,
                final_completion_bound_eligible=True,
                exact_completion_bound_enabled=False,
            )
        )
        self.assertFalse(
            _journey_pre_exact_completion_bound_handoff_needed(
                config,
                remaining=7.5,
                final_min_time=6.0,
                min_pricing_time=1.0,
                certificate_candidate=False,
                certificate_flat_rounds=4,
                depth=0,
                final_completion_bound_eligible=True,
                exact_completion_bound_enabled=False,
            )
        )
        self.assertFalse(
            _journey_pre_exact_completion_bound_handoff_needed(
                config,
                remaining=7.5,
                final_min_time=6.0,
                min_pricing_time=1.0,
                certificate_candidate=True,
                certificate_flat_rounds=4,
                depth=1,
                final_completion_bound_eligible=True,
                exact_completion_bound_enabled=False,
            )
        )

    def test_flat_weak_column_pressure_treats_inactive_support_batch_as_weak(self):
        config = {
            "journey_certificate_flat_weak_column_pressure_enabled": True,
            "journey_certificate_flat_weak_column_min_flat_rounds": 1,
            "journey_certificate_flat_weak_column_max_added_journeys": 2,
            "journey_certificate_flat_weak_column_active_support_miss_enabled": True,
        }
        added = _JourneyAdditionCount(
            8,
            new_journeys=8,
            replacement_journeys=0,
            unchanged_journeys=0,
            changed_task_sets=(frozenset({3}), frozenset({4}), frozenset({5})),
        )

        self.assertTrue(
            _journey_flat_weak_column_pressure_addition(
                config,
                added,
                certificate_candidate=True,
                certificate_flat_rounds=2,
                objective_delta=0.0,
                eps=1.0e-6,
                active_task_sets={frozenset({1, 2})},
            )
        )
        self.assertFalse(
            _journey_flat_weak_column_pressure_addition(
                config,
                added,
                certificate_candidate=True,
                certificate_flat_rounds=2,
                objective_delta=0.0,
                eps=1.0e-6,
                active_task_sets={frozenset({3})},
            )
        )

    def test_pricing_uses_path_options_without_one_minute_full_grid(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))

        vehicle = data.vehicles[0]
        duals = FutureDuals(
            cover={1: 100.0},
            task_vehicle={},
            sortie_count={vehicle: 0.0},
            time_occupation={},
            ordering={},
            branches={},
        )
        result = price_timed_trips(
            data,
            duals,
            tuple(),
            vehicle=vehicle,
            config=PricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=1,
                max_returned_trips=10,
                max_negative_trips_per_sequence=0,
            ),
        )
        self.assertTrue(result.exhausted)
        self.assertGreater(result.negative_trips, 0)
        self.assertLess(result.evaluated_timed_trips, data.horizon)

    def test_exact_start_optimization_preserves_best_reduced_cost_without_time_duals(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))

        vehicle = data.vehicles[0]
        duals = FutureDuals(
            cover={1: 100.0},
            task_vehicle={},
            sortie_count={vehicle: 0.0},
            time_occupation={},
            ordering={},
            branches={},
        )
        common = dict(
            time_bucket_size=5.0,
            start_time_step=10.0,
            max_tasks_per_trip=1,
            max_returned_trips=10,
            max_negative_trips_per_sequence=0,
        )
        enumerated = price_timed_trips(
            data,
            duals,
            tuple(),
            vehicle=vehicle,
            config=PricingConfig(**common, start_optimization_enabled=False),
        )
        optimized = price_timed_trips(
            data,
            duals,
            tuple(),
            vehicle=vehicle,
            config=PricingConfig(**common, start_optimization_enabled=True),
        )
        self.assertTrue(enumerated.exhausted)
        self.assertTrue(optimized.exhausted)
        self.assertGreater(optimized.negative_trips, 0)
        self.assertAlmostEqual(enumerated.best_reduced_cost, optimized.best_reduced_cost, places=6)

    def test_exact_path_profile_dominance_preserves_best_reduced_cost(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_dominated_time_logical_graph_case(Path(tmp))
            data = load_future_data(str(graph_path))

        vehicle = data.vehicles[0]
        duals = FutureDuals(
            cover={1: 100.0},
            task_vehicle={},
            sortie_count={vehicle: 0.0},
            time_occupation={},
            ordering={},
            branches={},
        )
        common = dict(
            time_bucket_size=5.0,
            start_time_step=10.0,
            max_tasks_per_trip=1,
            max_returned_trips=100,
            max_negative_trips_per_sequence=0,
            start_optimization_enabled=True,
        )
        full = price_timed_trips(
            data,
            duals,
            tuple(),
            vehicle=vehicle,
            config=PricingConfig(**common, path_dominance_enabled=False),
        )
        filtered = price_timed_trips(
            data,
            duals,
            tuple(),
            vehicle=vehicle,
            config=PricingConfig(**common, path_dominance_enabled=True),
        )
        self.assertTrue(full.exhausted)
        self.assertTrue(filtered.exhausted)
        self.assertEqual({key: len(options) for key, options in data.arc_options.items()}, {(0, 1): 1, (1, 0): 1})
        self.assertEqual(filtered.evaluated_timed_trips, full.evaluated_timed_trips)
        self.assertAlmostEqual(full.best_reduced_cost, filtered.best_reduced_cost, places=6)

    def test_partial_profile_dominance_uses_current_time_interval_not_exact_offset(self):
        dominant = _PartialNoWaitingPathProfile(
            arc_options=tuple(),
            lower_start=0.0,
            upper_start=100.0,
            offset=10.0,
            travel_cost=5.0,
            travel_energy=5.0,
            service_cost=0.0,
            service_energy=0.0,
        )
        dominated = _PartialNoWaitingPathProfile(
            arc_options=tuple(),
            lower_start=5.0,
            upper_start=80.0,
            offset=12.0,
            travel_cost=6.0,
            travel_energy=6.0,
            service_cost=0.0,
            service_energy=0.0,
        )
        self.assertEqual(len(_pareto_filter_partial_profiles([dominated, dominant])), 2)
        self.assertEqual(
            _pareto_filter_partial_profiles([dominated, dominant], generalized=True),
            [dominant],
        )

    def test_arc_combination_dominance_does_not_double_count_risk_resource(self):
        dominant = (
            ArcOption("a", "low_cost", tuple(), tau=5.0, energy=5.0, risk=10.0, distance=1.0, cost=1.0),
        )
        dominated = (
            ArcOption("b", "low_risk", tuple(), tau=6.0, energy=6.0, risk=1.0, distance=1.0, cost=2.0),
        )
        self.assertEqual(_pareto_filter_arc_combinations([dominated, dominant]), [dominant])

    def test_loader_arc_option_dominance_preserves_faster_path(self):
        slow_low_cost = ArcOption(
            "slow",
            "low_cost",
            tuple(),
            tau=10.0,
            energy=4.0,
            risk=1.0,
            distance=1.0,
            cost=1.0,
        )
        fast_higher_cost = ArcOption(
            "fast",
            "low_time",
            tuple(),
            tau=5.0,
            energy=4.0,
            risk=1.0,
            distance=1.5,
            cost=1.1,
        )
        self.assertEqual(
            _pareto_filter_arc_options([slow_low_cost, fast_higher_cost]),
            [slow_low_cost, fast_higher_cost],
        )

    def test_loader_arc_option_dominance_removes_cost_time_energy_dominated_path(self):
        dominant = ArcOption("dominant", "a", tuple(), tau=5.0, energy=4.0, risk=10.0, distance=2.0, cost=1.0)
        dominated = ArcOption("dominated", "b", tuple(), tau=6.0, energy=5.0, risk=0.0, distance=1.0, cost=1.5)
        self.assertEqual(_pareto_filter_arc_options([dominated, dominant]), [dominant])

    def test_direct_time_dual_overlap_matches_occupancy_reduced_cost(self):
        bucket = 10.0
        horizon = 120.0
        start = 7.5
        end_offset = 31.25
        time_duals = {0: -1.0, 1: 2.5, 2: -0.5, 3: 3.0}
        occupancy = _occupancy_profile(start, end_offset, bucket, horizon)
        tuple_rc = _reduced_cost_at_start(
            10.0,
            occupancy,
            start,
            end_offset,
            time_duals,
            tuple(),
        )
        direct_rc = _reduced_cost_at_start(
            10.0,
            tuple(),
            start,
            end_offset,
            time_duals,
            tuple(),
            bucket,
            horizon,
        )
        self.assertAlmostEqual(tuple_rc, direct_rc, places=9)

    def test_negative_column_truncation_is_not_certificate(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        vehicle = data.vehicles[0]
        duals = FutureDuals(
            cover={1: 100.0},
            task_vehicle={},
            sortie_count={vehicle: 0.0},
            time_occupation={},
            ordering={},
            branches={},
        )
        result = price_timed_trips(
            data,
            duals,
            tuple(),
            vehicle=vehicle,
            config=PricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=1,
                max_returned_trips=10,
                max_negative_trips_per_sequence=1,
                start_optimization_enabled=True,
            ),
        )
        self.assertFalse(result.exhausted)
        self.assertGreater(result.negative_trips, 0)

    def test_journey_column_requires_nonoverlap_and_counts_fixed_cost_once(self):
        data = load_future_data("very_small")
        trip1 = evaluate_timed_trip(data, (1,), 0.0, time_bucket_size=20.0)
        overlapping = evaluate_timed_trip(data, (2,), 0.0, time_bucket_size=20.0)
        self.assertIsNotNone(trip1)
        self.assertIsNotNone(overlapping)
        assert trip1 is not None and overlapping is not None
        nonoverlap = evaluate_timed_trip(data, (2,), trip1.end_time, time_bucket_size=20.0)
        self.assertIsNotNone(nonoverlap)
        assert nonoverlap is not None
        self.assertFalse(trips_compatible(trip1, overlapping))
        self.assertTrue(trips_compatible(trip1, nonoverlap))
        self.assertIsNone(make_journey(data, (trip1, overlapping)))
        journey = make_journey(data, (trip1, nonoverlap))
        self.assertIsNotNone(journey)
        assert journey is not None
        self.assertEqual(journey.task_set, frozenset({1, 2}))
        self.assertAlmostEqual(journey.cost, data.fixed_vehicle_cost + trip1.cost + nonoverlap.cost, places=6)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_pool_master_uses_combined_nonoverlap_schedule(self):
        data = replace(load_future_data("very_small"), vehicles=(1, 2, 3, 4))
        trips = []
        for task in data.tasks:
            trip = evaluate_timed_trip(data, (task,), 0.0, time_bucket_size=20.0)
            self.assertIsNotNone(trip)
            assert trip is not None
            trips.append(trip)
        first = trips[0]
        second_late = evaluate_timed_trip(data, (data.tasks[1],), first.end_time, time_bucket_size=20.0)
        self.assertIsNotNone(second_late)
        assert second_late is not None
        trips.append(second_late)
        journey_pool = build_journey_pool(data, trips, max_trips_per_journey=2, max_columns=50)
        self.assertTrue(any(journey.task_set == frozenset({data.tasks[0], data.tasks[1]}) for journey in journey_pool.journeys))
        result = solve_journey_pool_master(data, journey_pool.journeys, time_limit=2.0)
        self.assertIsNotNone(result.lp_objective)
        self.assertIsNotNone(result.mip_objective)
        self.assertTrue(any(journey.task_set == frozenset({data.tasks[0], data.tasks[1]}) and value > 0.5 for journey, value in result.selected_journeys))

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_rmp_reduced_cost_matches_manual_formula(self):
        data = replace(load_future_data("very_small"), vehicles=(1, 2, 3, 4))
        trips = _single_task_grid_trips(data, bucket=20.0)
        journey_pool = build_journey_pool(data, trips, max_trips_per_journey=1, max_columns=200)
        solution = solve_journey_rmp(data, journey_pool.journeys, capture_reduced_costs=True)
        self.assertTrue(solution.optimal)
        assert solution.duals is not None
        for journey_id, solver_rc in solution.reduced_costs.items():
            manual = manual_journey_reduced_cost(journey_pool.journeys[journey_id], solution.duals)
            self.assertAlmostEqual(solver_rc, manual, places=5)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_rmp_reduced_cost_matches_manual_formula_with_cuts(self):
        data = replace(load_future_data("very_small"), vehicles=(1, 2, 3, 4))
        trips = _single_task_grid_trips(data, bucket=20.0)
        journey_pool = build_journey_pool(data, trips, max_trips_per_journey=2, max_columns=300)
        cuts = (FleetLowerBoundCut(1), SubsetRowCut(tuple(int(task) for task in data.tasks[:3]), 2))
        solution = solve_journey_rmp(
            data,
            journey_pool.journeys,
            cuts=cuts,
            capture_reduced_costs=True,
        )
        self.assertTrue(solution.optimal)
        assert solution.duals is not None
        self.assertIsNotNone(solution.duals.cuts)
        for journey_id, solver_rc in solution.reduced_costs.items():
            manual = manual_journey_reduced_cost(journey_pool.journeys[journey_id], solution.duals, cuts=cuts)
            self.assertAlmostEqual(solver_rc, manual, places=5)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_gurobi_barrier_dual_matches_current_rmp_face_when_available(self):
        try:
            import gurobipy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"gurobipy unavailable: {exc}")
        data = replace(load_future_data("very_small"), vehicles=(1, 2, 3, 4))
        trips = _single_task_grid_trips(data, bucket=20.0)
        journey_pool = build_journey_pool(data, trips, max_trips_per_journey=1, max_columns=200)
        solution = solve_journey_rmp(data, journey_pool.journeys)
        self.assertTrue(solution.optimal)
        assert solution.objective is not None
        result = solve_journey_gurobi_barrier_dual(
            data,
            journey_pool.journeys,
            time_limit=2.0,
        )
        if result.status == "UNAVAILABLE":
            self.skipTest("gurobi sidecar unavailable")
        self.assertEqual(result.status, "OPTIMAL")
        self.assertIsNotNone(result.duals)
        self.assertIsNotNone(result.objective_value)
        assert result.duals is not None and result.objective_value is not None
        self.assertAlmostEqual(result.objective_value, solution.objective, places=5)
        min_rc, negative_count = _journey_dual_current_pool_validation(
            journey_pool.journeys,
            result.duals,
            tuple(),
            tolerance=1.0e-5,
        )
        self.assertIsNotNone(min_rc)
        self.assertEqual(negative_count, 0)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_stabilized_dual_supports_fleet_lower_cut(self):
        data = replace(load_future_data("very_small"), vehicles=(1, 2, 3, 4))
        trips = _single_task_grid_trips(data, bucket=20.0)
        journey_pool = build_journey_pool(data, trips, max_trips_per_journey=1, max_columns=200)
        cuts = (FleetLowerBoundCut(1),)
        solution = solve_journey_rmp(data, journey_pool.journeys, cuts=cuts)
        self.assertTrue(solution.optimal)
        assert solution.duals is not None and solution.objective is not None
        stabilized = solve_journey_stabilized_dual(
            data,
            journey_pool.journeys,
            cuts=cuts,
            objective_value=solution.objective,
            reference=solution.duals,
            time_limit=2.0,
        )
        self.assertEqual(stabilized.status, "OPTIMAL")
        self.assertIsNotNone(stabilized.duals)
        assert stabilized.duals is not None
        for journey in journey_pool.journeys:
            self.assertGreaterEqual(manual_journey_reduced_cost(journey, stabilized.duals, cuts=cuts), -1.0e-5)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_stabilized_dual_is_rmp_dual_feasible(self):
        data = replace(load_future_data("very_small"), vehicles=(1, 2, 3, 4))
        trips = _single_task_grid_trips(data, bucket=20.0)
        journey_pool = build_journey_pool(data, trips, max_trips_per_journey=1, max_columns=200)
        solution = solve_journey_rmp(data, journey_pool.journeys)
        self.assertTrue(solution.optimal)
        assert solution.duals is not None and solution.objective is not None
        stabilized = solve_journey_stabilized_dual(
            data,
            journey_pool.journeys,
            objective_value=solution.objective,
            reference=solution.duals,
            time_limit=2.0,
        )
        self.assertEqual(stabilized.status, "OPTIMAL")
        self.assertIsNotNone(stabilized.duals)
        self.assertIsNotNone(stabilized.objective_value)
        assert stabilized.duals is not None and stabilized.objective_value is not None
        self.assertAlmostEqual(stabilized.objective_value, solution.objective, places=5)
        for journey in journey_pool.journeys:
            self.assertGreaterEqual(manual_journey_reduced_cost(journey, stabilized.duals), -1.0e-5)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_slack_center_dual_is_rmp_dual_feasible(self):
        data = replace(load_future_data("very_small"), vehicles=(1, 2, 3, 4))
        trips = _single_task_grid_trips(data, bucket=20.0)
        journey_pool = build_journey_pool(data, trips, max_trips_per_journey=1, max_columns=200)
        solution = solve_journey_rmp(data, journey_pool.journeys)
        self.assertTrue(solution.optimal)
        assert solution.objective is not None
        centered = solve_journey_stabilized_dual(
            data,
            journey_pool.journeys,
            objective_value=solution.objective,
            mode="slack_center",
            slack_cap=100.0,
            time_limit=2.0,
        )
        self.assertEqual(centered.status, "OPTIMAL")
        self.assertIsNotNone(centered.duals)
        self.assertIsNotNone(centered.objective_value)
        assert centered.duals is not None and centered.objective_value is not None
        self.assertAlmostEqual(centered.objective_value, solution.objective, places=5)
        for journey in journey_pool.journeys:
            self.assertGreaterEqual(manual_journey_reduced_cost(journey, centered.duals), -1.0e-5)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_interior_dual_with_doi_bounds_is_rmp_dual_feasible(self):
        data = replace(load_future_data("very_small"), vehicles=(1, 2, 3, 4))
        trips = _single_task_grid_trips(data, bucket=20.0)
        journey_pool = build_journey_pool(data, trips, max_trips_per_journey=2, max_columns=400)
        solution = solve_journey_rmp(data, journey_pool.journeys)
        self.assertTrue(solution.optimal)
        assert solution.objective is not None
        cover_bounds, pair_bounds = _journey_dual_optimal_inequality_bounds(
            data,
            journey_pool.journeys,
            include_pairs=True,
        )
        self.assertTrue(cover_bounds)
        interior = solve_journey_stabilized_dual(
            data,
            journey_pool.journeys,
            objective_value=solution.objective,
            mode="interior_slack",
            slack_cap=100.0,
            cover_upper_bounds=cover_bounds,
            pair_upper_bounds=pair_bounds,
            time_limit=2.0,
        )
        self.assertEqual(interior.status, "OPTIMAL")
        self.assertIsNotNone(interior.duals)
        self.assertIsNotNone(interior.objective_value)
        assert interior.duals is not None and interior.objective_value is not None
        self.assertAlmostEqual(interior.objective_value, solution.objective, places=5)
        for journey in journey_pool.journeys:
            self.assertGreaterEqual(manual_journey_reduced_cost(journey, interior.duals), -1.0e-5)

    def test_journey_dual_current_pool_validation_detects_bad_dual(self):
        data = load_future_data("very_small")
        trips = _single_task_grid_trips(data, bucket=20.0)
        journey_pool = build_journey_pool(data, trips, max_trips_per_journey=1, max_columns=100)
        bad_dual = JourneyDuals(
            cover={int(task): 1.0e6 for task in data.tasks},
            fleet_limit=0.0,
        )
        min_rc, negative_count = _journey_dual_current_pool_validation(
            journey_pool.journeys,
            bad_dual,
            tuple(),
            tolerance=1.0e-6,
        )
        self.assertIsNotNone(min_rc)
        assert min_rc is not None
        self.assertLess(min_rc, 0.0)
        self.assertGreater(negative_count, 0)

    def test_journey_analytic_center_priority_sets_are_ranking_hints(self):
        data = load_future_data("very_small")
        center = JourneyDuals(
            cover={int(task): float(index + 1) for index, task in enumerate(data.tasks)},
            fleet_limit=0.0,
        )
        scip = JourneyDuals(cover={int(task): 0.0 for task in data.tasks}, fleet_limit=0.0)
        priority_sets = _journey_analytic_center_priority_task_sets(
            data,
            {
                "journey_analytic_center_priority_top_tasks": 3,
                "journey_analytic_center_priority_max_task_set_size": 2,
                "journey_analytic_center_priority_max_task_sets": 10,
            },
            center,
            scip,
        )
        self.assertTrue(priority_sets)
        strongest = max(data.tasks, key=lambda task: center.cover[int(task)])
        self.assertIn(frozenset({int(strongest)}), priority_sets)
        self.assertTrue(all(isinstance(task_set, frozenset) for task_set in priority_sets))

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_pricing_dual_selector_returns_valid_stabilized_source(self):
        data = replace(load_future_data("very_small"), vehicles=(1, 2, 3, 4))
        trips = _single_task_grid_trips(data, bucket=20.0)
        journey_pool = build_journey_pool(data, trips, max_trips_per_journey=2, max_columns=400)
        solution = solve_journey_rmp(data, journey_pool.journeys)
        self.assertTrue(solution.optimal)
        assert solution.duals is not None and solution.objective is not None
        selected, source = _select_journey_pricing_duals(
            data,
            {
                "journey_dual_stabilization_enabled": True,
                "journey_dual_stabilization_mode": "interior_slack",
                "journey_dual_optimal_inequalities_enabled": True,
                "journey_deep_dual_optimal_inequalities_enabled": True,
                "journey_dual_stabilization_time_limit": 2.0,
            },
            journey_pool,
            tuple(),
            len(data.vehicles),
            float(solution.objective),
            solution.duals,
            None,
            FutureLogger(None, console=False),
            1,
            progress_classification="initial_rmp",
        )
        self.assertEqual(source, "stabilized")
        min_rc, negative_count = _journey_dual_current_pool_validation(
            journey_pool.journeys,
            selected,
            tuple(),
            tolerance=1.0e-6,
        )
        self.assertIsNotNone(min_rc)
        self.assertEqual(negative_count, 0)

    def test_journey_pricing_dual_selector_reference_mode_is_opt_in(self):
        data = replace(load_future_data("very_small"), vehicles=(1, 2, 3, 4))
        trips = _single_task_grid_trips(data, bucket=20.0)
        journey_pool = build_journey_pool(data, trips, max_trips_per_journey=2, max_columns=400)
        scip = JourneyDuals(cover={int(task): 0.0 for task in data.tasks}, fleet_limit=0.0, cuts={})
        previous = JourneyDuals(
            cover={int(task): float(index + 1) for index, task in enumerate(data.tasks)},
            fleet_limit=0.0,
            cuts={},
        )

        def _run_selector(config: dict[str, Any], **selector_kwargs: Any) -> Any:
            with patch("BPC_future.solver.journey_driver.solve_journey_stabilized_dual") as stabilized:
                stabilized.return_value = SimpleNamespace(
                    status="OPTIMAL",
                    duals=scip,
                    objective_value=0.0,
                    variable_count=1,
                    constraint_count=1,
                )
                selected, source = _select_journey_pricing_duals(
                    data,
                    {
                        "journey_dual_stabilization_enabled": True,
                        "journey_dual_stabilization_mode": "l1_reference",
                        "journey_dual_stabilization_time_limit": 0.1,
                        **config,
                    },
                    journey_pool,
                    tuple(),
                    len(data.vehicles),
                    0.0,
                    scip,
                    previous,
                    FutureLogger(None, console=False),
                    1,
                    progress_classification="dual_changed_degenerate",
                    **selector_kwargs,
                )
                self.assertIs(selected, scip)
                self.assertEqual(source, "stabilized")
                return stabilized.call_args.kwargs

        default_kwargs = _run_selector({})
        self.assertIs(default_kwargs["reference"], previous)

        zero_kwargs = _run_selector({"journey_dual_stabilization_reference_mode": "zero"})
        self.assertIsNone(zero_kwargs["reference"])

        scip_kwargs = _run_selector({"journey_dual_stabilization_reference_mode": "scip"})
        self.assertIs(scip_kwargs["reference"], scip)

        root_tail_kwargs = _run_selector(
            {"journey_dual_stabilization_reference_mode": "root_tail_zero"},
            incumbent=0.0,
            certificate_flat_rounds=1,
            node_id=0,
            depth=0,
        )
        self.assertIsNone(root_tail_kwargs["reference"])

    def test_journey_pricing_dual_selector_root_tail_zero_gate_preserves_branch_path(self):
        data = replace(load_future_data("very_small"), vehicles=(1, 2, 3, 4))
        trips = _single_task_grid_trips(data, bucket=20.0)
        journey_pool = build_journey_pool(data, trips, max_trips_per_journey=2, max_columns=400)
        scip = JourneyDuals(cover={int(task): 0.0 for task in data.tasks}, fleet_limit=0.0, cuts={})
        config = {
            "journey_dual_stabilization_enabled": True,
            "journey_dual_stabilization_mode": "l1_reference",
            "journey_dual_stabilization_reference_mode": "root_tail_zero",
            "journey_dual_stabilization_time_limit": 0.1,
        }

        def _select(**selector_kwargs: Any) -> tuple[JourneyDuals, str, int]:
            with patch("BPC_future.solver.journey_driver.solve_journey_stabilized_dual") as stabilized:
                selected, source = _select_journey_pricing_duals(
                    data,
                    config,
                    journey_pool,
                    tuple(),
                    len(data.vehicles),
                    0.0,
                    scip,
                    scip,
                    FutureLogger(None, console=False),
                    1,
                    progress_classification="dual_changed_degenerate",
                    **selector_kwargs,
                )
                return selected, source, int(stabilized.call_count)

        selected, source, calls = _select(incumbent=0.0, certificate_flat_rounds=1, node_id=0, depth=1)
        self.assertIs(selected, scip)
        self.assertEqual(source, "scip")
        self.assertEqual(calls, 0)

        selected, source, calls = _select(incumbent=math.inf, certificate_flat_rounds=1, node_id=0, depth=0)
        self.assertIs(selected, scip)
        self.assertEqual(source, "scip")
        self.assertEqual(calls, 0)

    def test_journey_exact_pricing_duals_force_scip_for_certificate_modes(self):
        scip = JourneyDuals(cover={1: 1.0}, fleet_limit=0.0)
        stabilized = JourneyDuals(cover={1: 2.0}, fleet_limit=0.0)
        selected, source = _journey_exact_pricing_duals(
            scip,
            stabilized,
            "stabilized",
            learning_runtime=None,
            certificate_candidate=False,
            completion_bound_enabled=False,
        )
        self.assertIs(selected, stabilized)
        self.assertEqual(source, "stabilized")

        selected, source = _journey_exact_pricing_duals(
            scip,
            stabilized,
            "stabilized",
            learning_runtime=None,
            certificate_candidate=True,
            completion_bound_enabled=False,
        )
        self.assertIs(selected, stabilized)
        self.assertEqual(source, "stabilized_certificate")

        selected, source = _journey_exact_pricing_duals(
            scip,
            stabilized,
            "stabilized",
            learning_runtime=None,
            certificate_candidate=False,
            completion_bound_enabled=True,
        )
        self.assertIs(selected, stabilized)
        self.assertEqual(source, "stabilized_certificate")

        selected, source = _journey_exact_pricing_duals(
            scip,
            stabilized,
            "stabilized",
            learning_runtime=object(),
            certificate_candidate=True,
            completion_bound_enabled=True,
        )
        self.assertIs(selected, stabilized)
        self.assertEqual(source, "stabilized_certificate")

        selected, source = _journey_exact_pricing_duals(
            scip,
            stabilized,
            "learning_smoothed",
            learning_runtime=object(),
            certificate_candidate=False,
            completion_bound_enabled=False,
        )
        self.assertIs(selected, scip)
        self.assertEqual(source, "scip_learning_certificate")

        averaged = JourneyDuals(cover={1: 1.5}, fleet_limit=0.0)
        selected, source = _journey_exact_pricing_duals(
            scip,
            averaged,
            "dual_average",
            learning_runtime=None,
            certificate_candidate=True,
            completion_bound_enabled=False,
        )
        self.assertIs(selected, averaged)
        self.assertEqual(source, "dual_average")

        selected, source = _journey_exact_pricing_duals(
            scip,
            averaged,
            "dual_average",
            learning_runtime=None,
            certificate_candidate=True,
            completion_bound_enabled=True,
        )
        self.assertIs(selected, scip)
        self.assertEqual(source, "scip_certificate")

    def test_journey_dual_averaging_activates_after_flat_history(self):
        runtime = _JourneyDualAveragingRuntime()
        data = SimpleNamespace(tasks=(1, 2))
        config = {
            "journey_dual_averaging_enabled": True,
            "journey_dual_averaging_window": 3,
            "journey_dual_averaging_patience": 3,
            "journey_dual_averaging_objective_tol": 1.0e-4,
        }
        logger = FutureLogger(None, console=False)
        duals = [
            JourneyDuals(cover={1: 1.0, 2: 10.0}, fleet_limit=-1.0, cuts={0: 2.0}),
            JourneyDuals(cover={1: 3.0, 2: 12.0}, fleet_limit=-2.0, cuts={0: 4.0}),
            JourneyDuals(cover={1: 5.0, 2: 14.0}, fleet_limit=-3.0, cuts={0: 6.0}),
        ]
        for index, dual in enumerate(duals[:2], start=1):
            averaged, source = _journey_dual_averaging_pricing_duals(
                data,
                config,
                runtime,
                dual,
                objective_delta=0.0,
                progress_classification="dual_changed_degenerate",
                logger=logger,
                cg_iter=index,
                node_id=0,
                depth=0,
            )
            self.assertIsNone(averaged)
            self.assertIsNone(source)

        averaged, source = _journey_dual_averaging_pricing_duals(
            data,
            config,
            runtime,
            duals[2],
            objective_delta=0.0,
            progress_classification="dual_changed_degenerate",
            logger=logger,
            cg_iter=3,
            node_id=0,
            depth=0,
        )
        self.assertEqual(source, "dual_average")
        assert averaged is not None
        self.assertAlmostEqual(averaged.cover[1], 3.0)
        self.assertAlmostEqual(averaged.cover[2], 12.0)
        self.assertAlmostEqual(averaged.fleet_limit, -3.0)
        self.assertEqual(averaged.cuts, {0: 6.0})

    def test_dual_average_direct_patrol_is_worker_only(self):
        base = JourneyPricingConfig(
            time_limit=20.0,
            direct_journey_label_pricing_enabled=False,
            direct_journey_label_global_certificate_enabled=True,
            direct_journey_label_completion_bound_enabled=False,
        )
        updated, mode = _journey_dual_average_direct_patrol_config(
            {
                "journey_dual_averaging_direct_patrol_enabled": True,
                "journey_hidden_negative_patrol_enabled": True,
                "journey_hidden_negative_patrol_time_limit": 0.5,
                "journey_hidden_negative_patrol_final_reserve_time": 1.0,
                "journey_hidden_negative_patrol_min_journeys": 4,
                "journey_hidden_negative_patrol_max_returned_journeys": 8,
                "journey_hidden_negative_patrol_resource_coarsening_enabled": True,
                "journey_hidden_negative_patrol_resource_coarsening_time_bucket_size": 50.0,
                "journey_hidden_negative_patrol_resource_coarsening_energy_bucket_size": 50.0,
            },
            base,
            remaining=5.0,
            min_pricing_time=0.1,
        )
        self.assertTrue(mode["dual_average_direct_patrol"])
        self.assertFalse(mode["certificate_capable"])
        self.assertTrue(updated.direct_journey_label_pricing_enabled)
        self.assertFalse(updated.direct_journey_label_global_certificate_enabled)
        self.assertFalse(updated.direct_journey_label_completion_bound_enabled)
        self.assertAlmostEqual(updated.time_limit, 0.5)
        self.assertEqual(updated.direct_journey_label_early_return_negative_min_count, 4)
        self.assertEqual(updated.max_returned_journeys, 8)
        self.assertAlmostEqual(updated.direct_journey_label_resource_coarsening_time_bucket_size, 50.0)
        self.assertAlmostEqual(updated.direct_journey_label_resource_coarsening_energy_bucket_size, 50.0)

    def test_completion_bound_diverse_harvest_soft_return_ignores_elapsed_time(self):
        self.assertTrue(
            _direct_label_diverse_harvest_soft_return_ready(
                completion_bound_enabled=False,
                unique_count=5,
                max_returned=30,
                soft_min=5,
                soft_after=10.0,
                soft_remaining=8.0,
                elapsed=12.0,
                remaining=40.0,
            )
        )
        self.assertFalse(
            _direct_label_diverse_harvest_soft_return_ready(
                completion_bound_enabled=True,
                completion_bound_elapsed_soft_return_enabled=False,
                unique_count=5,
                max_returned=30,
                soft_min=5,
                soft_after=10.0,
                soft_remaining=8.0,
                elapsed=12.0,
                remaining=40.0,
            )
        )
        self.assertTrue(
            _direct_label_diverse_harvest_soft_return_ready(
                completion_bound_enabled=True,
                completion_bound_elapsed_soft_return_enabled=False,
                unique_count=5,
                max_returned=30,
                soft_min=5,
                soft_after=10.0,
                soft_remaining=8.0,
                elapsed=12.0,
                remaining=7.5,
            )
        )
        self.assertTrue(
            _direct_label_diverse_harvest_soft_return_ready(
                completion_bound_enabled=True,
                completion_bound_elapsed_soft_return_enabled=True,
                unique_count=5,
                max_returned=30,
                soft_min=5,
                soft_after=10.0,
                soft_remaining=8.0,
                elapsed=12.0,
                remaining=40.0,
            )
        )
        self.assertTrue(
            _direct_label_diverse_harvest_soft_return_ready(
                completion_bound_enabled=True,
                completion_bound_elapsed_soft_return_enabled=True,
                unique_count=4,
                candidate_count=362,
                max_returned=30,
                soft_min=15,
                soft_after=10.0,
                soft_remaining=8.0,
                elapsed=12.0,
                remaining=40.0,
            )
        )
        self.assertTrue(
            _direct_label_diverse_harvest_soft_return_ready(
                completion_bound_enabled=True,
                completion_bound_elapsed_soft_return_enabled=True,
                unique_count=7,
                candidate_count=60,
                max_returned=30,
                soft_min=15,
                soft_after=15.0,
                soft_remaining=8.0,
                duplicate_saturation_after_time=5.0,
                elapsed=5.1,
                remaining=40.0,
            )
        )
        self.assertFalse(
            _direct_label_diverse_harvest_soft_return_ready(
                completion_bound_enabled=True,
                completion_bound_elapsed_soft_return_enabled=True,
                unique_count=7,
                candidate_count=60,
                max_returned=30,
                soft_min=15,
                soft_after=15.0,
                soft_remaining=8.0,
                duplicate_saturation_after_time=5.0,
                elapsed=4.9,
                remaining=40.0,
            )
        )
        self.assertFalse(
            _direct_label_diverse_harvest_soft_return_ready(
                completion_bound_enabled=True,
                completion_bound_elapsed_soft_return_enabled=False,
                unique_count=4,
                candidate_count=362,
                max_returned=30,
                soft_min=15,
                soft_after=10.0,
                soft_remaining=8.0,
                elapsed=12.0,
                remaining=40.0,
            )
        )
        self.assertFalse(
            _direct_label_diverse_harvest_soft_return_ready(
                completion_bound_enabled=True,
                completion_bound_elapsed_soft_return_enabled=True,
                unique_count=4,
                candidate_count=20,
                max_returned=30,
                soft_min=15,
                soft_after=10.0,
                soft_remaining=8.0,
                elapsed=12.0,
                remaining=40.0,
            )
        )
        self.assertFalse(
            _direct_label_diverse_harvest_soft_return_ready(
                completion_bound_enabled=True,
                completion_bound_elapsed_soft_return_enabled=True,
                unique_count=7,
                candidate_count=80,
                new_task_set_count=0,
                max_returned=30,
                soft_min=15,
                soft_min_new_task_sets=1,
                soft_after=10.0,
                soft_remaining=8.0,
                elapsed=12.0,
                remaining=40.0,
            )
        )
        self.assertFalse(
            _direct_label_diverse_harvest_soft_return_ready(
                completion_bound_enabled=True,
                completion_bound_elapsed_soft_return_enabled=True,
                unique_count=7,
                candidate_count=80,
                new_task_set_count=0,
                max_returned=30,
                soft_min=15,
                soft_min_new_task_sets=1,
                soft_after=10.0,
                soft_remaining=8.0,
                elapsed=12.0,
                remaining=7.5,
            )
        )
        self.assertTrue(
            _direct_label_diverse_harvest_soft_return_ready(
                completion_bound_enabled=True,
                completion_bound_elapsed_soft_return_enabled=True,
                unique_count=7,
                candidate_count=80,
                new_task_set_count=1,
                max_returned=30,
                soft_min=15,
                soft_min_new_task_sets=1,
                soft_after=10.0,
                soft_remaining=8.0,
                elapsed=12.0,
                remaining=7.5,
            )
        )

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_pricing_dual_selector_tail_only_gate(self):
        data = replace(load_future_data("very_small"), vehicles=(1, 2, 3, 4))
        trips = _single_task_grid_trips(data, bucket=20.0)
        journey_pool = build_journey_pool(data, trips, max_trips_per_journey=2, max_columns=400)
        solution = solve_journey_rmp(data, journey_pool.journeys)
        self.assertTrue(solution.optimal)
        assert solution.duals is not None and solution.objective is not None
        config = {
            "journey_dual_stabilization_enabled": True,
            "journey_dual_stabilization_tail_only_enabled": True,
            "journey_dual_stabilization_mode": "interior_slack",
            "journey_dual_stabilization_time_limit": 2.0,
        }
        early_duals, early_source = _select_journey_pricing_duals(
            data,
            config,
            journey_pool,
            tuple(),
            len(data.vehicles),
            float(solution.objective),
            solution.duals,
            None,
            FutureLogger(None, console=False),
            1,
            progress_classification="objective_improved",
        )
        self.assertEqual(early_source, "scip")
        self.assertEqual(_journey_dual_vector(data, early_duals, 0), _journey_dual_vector(data, solution.duals, 0))
        tail_duals, tail_source = _select_journey_pricing_duals(
            data,
            config,
            journey_pool,
            tuple(),
            len(data.vehicles),
            float(solution.objective),
            solution.duals,
            None,
            FutureLogger(None, console=False),
            2,
            progress_classification="dual_changed_degenerate",
        )
        self.assertEqual(tail_source, "stabilized")
        min_rc, negative_count = _journey_dual_current_pool_validation(
            journey_pool.journeys,
            tail_duals,
            tuple(),
            tolerance=1.0e-6,
        )
        self.assertIsNotNone(min_rc)
        self.assertEqual(negative_count, 0)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_pricing_dual_selector_certificate_gate(self):
        data = replace(load_future_data("very_small"), vehicles=(1, 2, 3, 4))
        trips = _single_task_grid_trips(data, bucket=20.0)
        journey_pool = build_journey_pool(data, trips, max_trips_per_journey=2, max_columns=400)
        solution = solve_journey_rmp(data, journey_pool.journeys)
        self.assertTrue(solution.optimal)
        assert solution.duals is not None and solution.objective is not None
        config = {
            "journey_dual_stabilization_enabled": True,
            "journey_dual_stabilization_tail_only_enabled": True,
            "journey_dual_stabilization_certificate_candidate_enabled": True,
            "journey_dual_stabilization_mode": "interior_slack",
            "journey_dual_stabilization_time_limit": 2.0,
        }
        selected, source = _select_journey_pricing_duals(
            data,
            config,
            journey_pool,
            tuple(),
            len(data.vehicles),
            float(solution.objective),
            solution.duals,
            None,
            FutureLogger(None, console=False),
            1,
            progress_classification="initial_rmp",
            incumbent=float(solution.objective),
            integer_tol=1.0e-6,
        )
        self.assertEqual(source, "stabilized")
        min_rc, negative_count = _journey_dual_current_pool_validation(
            journey_pool.journeys,
            selected,
            tuple(),
            tolerance=1.0e-6,
        )
        self.assertIsNotNone(min_rc)
        self.assertEqual(negative_count, 0)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_pricing_dual_selector_can_force_scip_for_certificate_candidate(self):
        data = replace(load_future_data("very_small"), vehicles=(1, 2, 3, 4))
        trips = _single_task_grid_trips(data, bucket=20.0)
        journey_pool = build_journey_pool(data, trips, max_trips_per_journey=2, max_columns=400)
        solution = solve_journey_rmp(data, journey_pool.journeys)
        self.assertTrue(solution.optimal)
        assert solution.duals is not None and solution.objective is not None
        selected, source = _select_journey_pricing_duals(
            data,
            {
                "journey_dual_stabilization_enabled": True,
                "journey_dual_stabilization_tail_only_enabled": True,
                "journey_dual_stabilization_certificate_candidate_enabled": True,
                "journey_dual_stabilization_disable_on_certificate_candidate": True,
                "journey_dual_stabilization_mode": "interior_slack",
                "journey_dual_stabilization_time_limit": 2.0,
            },
            journey_pool,
            tuple(),
            len(data.vehicles),
            float(solution.objective),
            solution.duals,
            None,
            FutureLogger(None, console=False),
            1,
            progress_classification="initial_rmp",
            incumbent=float(solution.objective),
            integer_tol=1.0e-6,
        )
        self.assertEqual(source, "scip")
        self.assertEqual(_journey_dual_vector(data, selected, 0), _journey_dual_vector(data, solution.duals, 0))

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_pricing_dual_selector_uses_scip_when_certificate_time_is_low(self):
        data = replace(load_future_data("very_small"), vehicles=(1, 2, 3, 4))
        trips = _single_task_grid_trips(data, bucket=20.0)
        journey_pool = build_journey_pool(data, trips, max_trips_per_journey=2, max_columns=400)
        solution = solve_journey_rmp(data, journey_pool.journeys)
        self.assertTrue(solution.optimal)
        assert solution.duals is not None and solution.objective is not None
        config = {
            "journey_dual_stabilization_enabled": True,
            "journey_dual_stabilization_tail_only_enabled": True,
            "journey_dual_stabilization_certificate_candidate_enabled": True,
            "journey_dual_stabilization_disable_below_remaining": 8.0,
            "journey_dual_stabilization_disable_below_remaining_max_flat_rounds": 1,
            "journey_dual_stabilization_mode": "interior_slack",
            "journey_dual_stabilization_time_limit": 2.0,
        }
        low_remaining_duals, low_remaining_source = _select_journey_pricing_duals(
            data,
            config,
            journey_pool,
            tuple(),
            len(data.vehicles),
            float(solution.objective),
            solution.duals,
            None,
            FutureLogger(None, console=False),
            2,
            progress_classification="dual_changed_degenerate",
            incumbent=float(solution.objective),
            integer_tol=1.0e-6,
            remaining_time=7.5,
            certificate_flat_rounds=1,
        )
        self.assertEqual(low_remaining_source, "scip")
        self.assertEqual(_journey_dual_vector(data, low_remaining_duals, 0), _journey_dual_vector(data, solution.duals, 0))

        enough_remaining_duals, enough_remaining_source = _select_journey_pricing_duals(
            data,
            config,
            journey_pool,
            tuple(),
            len(data.vehicles),
            float(solution.objective),
            solution.duals,
            None,
            FutureLogger(None, console=False),
            2,
            progress_classification="dual_changed_degenerate",
            incumbent=float(solution.objective),
            integer_tol=1.0e-6,
            remaining_time=8.5,
            certificate_flat_rounds=1,
        )
        self.assertEqual(enough_remaining_source, "stabilized")
        min_rc, negative_count = _journey_dual_current_pool_validation(
            journey_pool.journeys,
            enough_remaining_duals,
            tuple(),
            tolerance=1.0e-6,
        )
        self.assertIsNotNone(min_rc)
        self.assertEqual(negative_count, 0)

        flat_tail_duals, flat_tail_source = _select_journey_pricing_duals(
            data,
            config,
            journey_pool,
            tuple(),
            len(data.vehicles),
            float(solution.objective),
            solution.duals,
            None,
            FutureLogger(None, console=False),
            2,
            progress_classification="dual_changed_degenerate",
            incumbent=float(solution.objective),
            integer_tol=1.0e-6,
            remaining_time=7.5,
            certificate_flat_rounds=3,
        )
        self.assertEqual(flat_tail_source, "stabilized")
        min_rc, negative_count = _journey_dual_current_pool_validation(
            journey_pool.journeys,
            flat_tail_duals,
            tuple(),
            tolerance=1.0e-6,
        )
        self.assertIsNotNone(min_rc)
        self.assertEqual(negative_count, 0)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_pricing_returns_true_negative_journey(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        result = price_journeys(
            data,
            duals=JourneyDuals(cover={1: 200.0}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=JourneyPricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=1,
                time_limit=5.0,
                max_candidate_trips=0,
                max_dp_states=1000,
            ),
        )
        self.assertTrue(result.exhausted)
        self.assertEqual(len(result.journeys), 1)
        self.assertLess(result.best_reduced_cost, 0.0)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_pricing_filters_same_task_set_dominated_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        result = price_journeys(
            data,
            duals=JourneyDuals(cover={1: 200.0}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=JourneyPricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=1,
                time_limit=5.0,
                max_candidate_trips=0,
                max_dp_states=1000,
            ),
            dominant_task_set_costs={frozenset({1}): 0.0},
        )
        self.assertEqual(result.journeys, [])
        self.assertGreater(
            result.existing_journeys_filtered
            + result.dominated_task_set_journeys_filtered
            + result.duplicate_candidates_filtered,
            0,
        )
        self.assertEqual(result.reason, "negative_journeys_already_in_pool")

    def test_direct_journey_label_beam_cap_keeps_best_labels(self):
        store: dict[int, list[_DirectJourneyLabel]] = {}
        labels = [
            _DirectJourneyLabel(end_time=1.0, value=5.0, mask=1, trips=tuple()),
            _DirectJourneyLabel(end_time=5.0, value=1.0, mask=1, trips=tuple()),
            _DirectJourneyLabel(end_time=2.0, value=2.0, mask=1, trips=tuple()),
        ]

        for label in labels:
            self.assertTrue(
                _add_direct_journey_label(
                    store,
                    1,
                    label,
                    max_labels_per_node=2,
                    time_bucket_size=0.0,
                )
            )

        kept = store[1]
        self.assertEqual(len(kept), 2)
        self.assertEqual([(round(item.value, 1), round(item.end_time, 1)) for item in kept], [(1.0, 5.0), (2.0, 2.0)])
        self.assertNotIn(labels[0], kept)

    def test_direct_journey_label_cross_count_dominance_uses_fewer_sorties(self):
        stores: list[dict[int, list[_DirectJourneyLabel]]] = [dict() for _ in range(4)]
        one_sortie = _DirectJourneyLabel(end_time=10.0, value=5.0, mask=3, trips=tuple())
        two_sortie_worse = _DirectJourneyLabel(end_time=12.0, value=7.0, mask=3, trips=tuple())
        zero_sortie_not_dominated = _DirectJourneyLabel(end_time=9.0, value=4.0, mask=3, trips=tuple())

        added, pruned = _add_direct_journey_label_with_cross_count_dominance(stores, 1, 3, one_sortie)
        self.assertTrue(added)
        self.assertEqual(pruned, 0)

        added, pruned = _add_direct_journey_label_with_cross_count_dominance(stores, 2, 3, two_sortie_worse)
        self.assertFalse(added)
        self.assertEqual(pruned, 1)
        self.assertEqual(stores[2].get(3, []), [])

        added, pruned = _add_direct_journey_label_with_cross_count_dominance(stores, 0, 3, zero_sortie_not_dominated)
        self.assertTrue(added)
        self.assertEqual(pruned, 1)
        self.assertEqual(stores[1].get(3, []), [])
        self.assertEqual(stores[0][3], [zero_sortie_not_dominated])

    def test_negative_journey_candidate_selection_keeps_best_per_task_mask(self):
        selected = _select_negative_journey_candidates(
            [
                (-5.0, ((2, 0.0),), 3),
                (-4.0, ((3, 0.0),), 3),
                (-3.0, ((4, 0.0),), 5),
            ],
            max_returned=10,
            selection_mode="reduced_cost",
        )
        self.assertEqual([(round(obj, 1), mask) for obj, _sel, mask in selected], [(-5.0, 3), (-3.0, 5)])

    def test_early_return_candidate_count_can_require_unique_masks(self):
        candidates = [
            (-5.0, ((1, 0.0),), 3),
            (-4.0, ((2, 0.0),), 3),
            (-3.0, ((3, 0.0),), 5),
        ]
        self.assertEqual(_early_return_candidate_count(candidates, JourneyPricingConfig()), 3)
        self.assertEqual(
            _early_return_candidate_count(
                candidates,
                JourneyPricingConfig(early_return_unique_masks_enabled=True),
            ),
            2,
        )

    def test_early_return_can_require_new_task_set_masks(self):
        candidates = [
            (-5.0, ((1, 0.0),), 3),
            (-4.0, ((2, 0.0),), 5),
            (-3.0, ((3, 0.0),), 7),
        ]
        config = JourneyPricingConfig(
            early_return_unique_masks_enabled=True,
            early_return_new_task_set_min_count=2,
        )
        self.assertFalse(
            _early_return_negative_candidates_ready(
                candidates[:2],
                config,
                {3: 10.0, 5: 11.0},
                min_count=2,
            )
        )
        self.assertTrue(
            _early_return_negative_candidates_ready(
                candidates,
                config,
                {3: 10.0},
                min_count=2,
            )
        )

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_streaming_journey_pricing_returns_true_negative_journey(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        result = price_journeys(
            data,
            duals=JourneyDuals(cover={1: 200.0}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=JourneyPricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=1,
                time_limit=5.0,
                max_candidate_trips=0,
                max_dp_states=1000,
                streaming_pricing_enabled=True,
                streaming_profile_batch_size=1,
            ),
        )
        self.assertEqual(len(result.journeys), 1)
        self.assertLess(result.best_reduced_cost, 0.0)
        self.assertFalse(result.exhausted)
        self.assertEqual(result.reason, "streaming_partial_negative_journey")

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_streaming_profile_labeling_returns_before_full_certificate(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        result = price_journeys(
            data,
            duals=JourneyDuals(cover={1: 200.0}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=JourneyPricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=1,
                time_limit=5.0,
                max_candidate_trips=0,
                max_dp_states=1000,
                streaming_pricing_enabled=True,
                streaming_profile_batch_size=1,
                profile_labeling_enabled=True,
                profile_labeling_best_first_enabled=True,
            ),
        )
        self.assertEqual(len(result.journeys), 1)
        self.assertLess(result.best_reduced_cost, 0.0)
        self.assertFalse(result.exhausted)
        self.assertEqual(result.reason, "streaming_partial_negative_journey")

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_streaming_pricing_continues_after_batch_dp_incomplete_without_column(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        calls = {"count": 0}

        def fake_dp(*args, **kwargs):
            calls["count"] += 1
            if calls["count"] == 1:
                return [], None, "INCOMPLETE"
            return [(((0, 0.0),), -1.0)], -1.0, "INCOMPLETE"

        with patch("BPC_future.pricing.journey_pricing._solve_best_journey_profile_dp", side_effect=fake_dp):
            result = price_journeys(
                data,
                duals=JourneyDuals(cover={1: 200.0}, fleet_limit=0.0),
                branch_constraints=tuple(),
                config=JourneyPricingConfig(
                    time_bucket_size=5.0,
                    start_time_step=10.0,
                    max_tasks_per_trip=1,
                    time_limit=5.0,
                    max_candidate_trips=0,
                    max_dp_states=1,
                    streaming_pricing_enabled=True,
                    streaming_profile_batch_size=1,
                    profile_labeling_enabled=True,
                    profile_labeling_best_first_enabled=True,
                ),
            )
        self.assertGreaterEqual(calls["count"], 2)
        self.assertEqual(len(result.journeys), 1)
        self.assertFalse(result.exhausted)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_streaming_pricing_waits_for_min_returned_and_keeps_partial_fallback(self):
        data = replace(load_future_data("very_small"), tasks=(1,), vehicles=(1,))
        fake_journey = JourneyColumn(
            id=0,
            trips=tuple(),
            task_set=frozenset({1}),
            start_time=0.0,
            end_time=1.0,
            travel_cost=1.0,
            fixed_vehicle_cost=0.0,
            cost=1.0,
            signature=("streaming-partial",),
        )
        callback_returned = {"value": "not-called"}

        def fake_generate(*args, **kwargs):
            callback = kwargs["stream_callback"]
            callback_returned["value"] = callback([], 10, 20, -1.0, 0)
            return [], 10, 20, -1.0, False, "time_limit", 0

        def fake_dp(*args, **kwargs):
            return [(((0, 0.0),), -2.0)], -2.0, "INCOMPLETE"

        def fake_instantiate(*args, **kwargs):
            return [fake_journey], 0, 0

        with patch("BPC_future.pricing.journey_pricing._generate_negative_sortie_profiles", side_effect=fake_generate), patch(
            "BPC_future.pricing.journey_pricing._solve_best_journey_profile_dp", side_effect=fake_dp
        ), patch("BPC_future.pricing.journey_pricing._instantiate_profile_journey_candidates", side_effect=fake_instantiate):
            result = _price_journeys_by_streaming_profiles(
                data,
                JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
                config=JourneyPricingConfig(
                    streaming_pricing_enabled=True,
                    streaming_min_negative_batch=2,
                    streaming_min_returned_journeys=2,
                    max_returned_journeys=4,
                ),
                cuts=tuple(),
                trip_cache={},
            )
        self.assertIsNone(callback_returned["value"])
        self.assertEqual(result.journeys, [fake_journey])
        self.assertFalse(result.exhausted)
        self.assertEqual(result.reason, "streaming_partial_negative_journey")

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_streaming_pricing_adaptive_partial_return_is_opt_in(self):
        data = replace(load_future_data("very_small"), tasks=(1,), vehicles=(1,))
        fake_journey = JourneyColumn(
            id=0,
            trips=tuple(),
            task_set=frozenset({1}),
            start_time=0.0,
            end_time=1.0,
            travel_cost=1.0,
            fixed_vehicle_cost=0.0,
            cost=1.0,
            signature=("streaming-adaptive-partial",),
        )
        callback_returned = {"value": None}

        def fake_generate(*args, **kwargs):
            callback = kwargs["stream_callback"]
            callback_returned["value"] = callback([], 10, 20, -1.0, 0)
            if callback_returned["value"] is not None:
                raise _StreamingPricingStop(callback_returned["value"])
            return [], 10, 20, -1.0, False, "time_limit", 0

        def fake_dp(*args, **kwargs):
            return [(((0, 0.0),), -2.0)], -2.0, "INCOMPLETE"

        def fake_instantiate(*args, **kwargs):
            return [fake_journey], 0, 0

        with patch("BPC_future.pricing.journey_pricing._generate_negative_sortie_profiles", side_effect=fake_generate), patch(
            "BPC_future.pricing.journey_pricing._solve_best_journey_profile_dp", side_effect=fake_dp
        ), patch("BPC_future.pricing.journey_pricing._instantiate_profile_journey_candidates", side_effect=fake_instantiate):
            result = _price_journeys_by_streaming_profiles(
                data,
                JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
                config=JourneyPricingConfig(
                    streaming_pricing_enabled=True,
                    streaming_min_negative_batch=2,
                    streaming_min_returned_journeys=2,
                    streaming_partial_return_after_time=1.0e-12,
                    streaming_partial_return_min_journeys=1,
                    max_returned_journeys=4,
                ),
                cuts=tuple(),
                trip_cache={},
            )
        self.assertIsNotNone(callback_returned["value"])
        self.assertEqual(result.journeys, [fake_journey])
        self.assertFalse(result.exhausted)
        self.assertEqual(result.reason, "streaming_partial_negative_journey")

    def test_streaming_partial_result_records_callback_times(self):
        data = replace(load_future_data("very_small"), tasks=(1,), vehicles=(1,))
        fake_journey = JourneyColumn(
            id=0,
            trips=tuple(),
            task_set=frozenset({1}),
            start_time=0.0,
            end_time=1.0,
            travel_cost=1.0,
            fixed_vehicle_cost=0.0,
            cost=1.0,
            signature=("streaming-callback-times",),
        )

        def fake_generate(*args, **kwargs):
            callback = kwargs["stream_callback"]
            time.sleep(0.001)
            result = callback([], 10, 20, -1.0, 0)
            if result is not None:
                raise _StreamingPricingStop(result)
            return [], 10, 20, -1.0, False, "time_limit", 0

        def fake_dp(*args, **kwargs):
            time.sleep(0.001)
            return [(((0, 0.0),), -2.0)], -2.0, "INCOMPLETE"

        def fake_instantiate(*args, **kwargs):
            return [fake_journey], 0, 0

        with patch("BPC_future.pricing.journey_pricing._generate_negative_sortie_profiles", side_effect=fake_generate), patch(
            "BPC_future.pricing.journey_pricing._solve_best_journey_profile_dp", side_effect=fake_dp
        ), patch("BPC_future.pricing.journey_pricing._instantiate_profile_journey_candidates", side_effect=fake_instantiate):
            result = _price_journeys_by_streaming_profiles(
                data,
                JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
                config=JourneyPricingConfig(
                    streaming_pricing_enabled=True,
                    streaming_min_negative_batch=1,
                    streaming_min_returned_journeys=1,
                    max_returned_journeys=4,
                ),
                cuts=tuple(),
                trip_cache={},
            )

        self.assertEqual(result.journeys, [fake_journey])
        self.assertEqual(result.reason, "streaming_partial_negative_journey")
        self.assertGreater(result.profile_generation_time, 0.0)
        self.assertGreater(result.profile_dp_time, 0.0)

    def test_streaming_final_dp_time_reserve_shortens_generation_deadline_only(self):
        data = replace(load_future_data("very_small"), tasks=(1,), vehicles=(1,))
        captured = {}

        def fake_generate(*args, **kwargs):
            captured["generation_budget"] = float(kwargs["deadline"]) - float(kwargs["started"])
            return [], 0, 0, None, False, "generation_reserved_for_dp", 0

        with patch(
            "BPC_future.pricing.journey_pricing._generate_negative_sortie_profiles",
            side_effect=fake_generate,
        ):
            result = _price_journeys_by_streaming_profiles(
                data,
                JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
                config=JourneyPricingConfig(
                    streaming_pricing_enabled=True,
                    time_limit=10.0,
                    profile_generation_time_fraction=1.0,
                    streaming_final_dp_time_reserve=2.0,
                ),
                cuts=tuple(),
                trip_cache={},
            )

        self.assertAlmostEqual(captured["generation_budget"], 8.0, delta=0.1)
        self.assertFalse(result.exhausted)
        self.assertEqual(result.reason, "generation_reserved_for_dp")

    def test_streaming_profile_generation_fraction_shortens_generation_deadline(self):
        data = replace(load_future_data("very_small"), tasks=(1,), vehicles=(1,))
        captured = {}

        def fake_generate(*args, **kwargs):
            captured["generation_budget"] = float(kwargs["deadline"]) - float(kwargs["started"])
            return [], 0, 0, None, False, "generation_reserved_for_dp", 0

        with patch(
            "BPC_future.pricing.journey_pricing._generate_negative_sortie_profiles",
            side_effect=fake_generate,
        ):
            result = _price_journeys_by_streaming_profiles(
                data,
                JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
                config=JourneyPricingConfig(
                    streaming_pricing_enabled=True,
                    time_limit=10.0,
                    profile_generation_time_fraction=0.6,
                ),
                cuts=tuple(),
                trip_cache={},
            )

        self.assertAlmostEqual(captured["generation_budget"], 6.0, delta=0.1)
        self.assertFalse(result.exhausted)
        self.assertEqual(result.reason, "generation_reserved_for_dp")

    def test_streaming_final_dp_reserve_can_shorten_fraction_deadline(self):
        data = replace(load_future_data("very_small"), tasks=(1,), vehicles=(1,))
        captured = {}

        def fake_generate(*args, **kwargs):
            captured["generation_budget"] = float(kwargs["deadline"]) - float(kwargs["started"])
            return [], 0, 0, None, False, "generation_reserved_for_dp", 0

        with patch(
            "BPC_future.pricing.journey_pricing._generate_negative_sortie_profiles",
            side_effect=fake_generate,
        ):
            result = _price_journeys_by_streaming_profiles(
                data,
                JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
                config=JourneyPricingConfig(
                    streaming_pricing_enabled=True,
                    time_limit=10.0,
                    profile_generation_time_fraction=0.9,
                    streaming_final_dp_time_reserve=3.0,
                ),
                cuts=tuple(),
                trip_cache={},
            )

        self.assertAlmostEqual(captured["generation_budget"], 7.0, delta=0.1)
        self.assertFalse(result.exhausted)
        self.assertEqual(result.reason, "generation_reserved_for_dp")

    def test_compatible_profile_cache_filters_by_upper_start_safely(self):
        def profile(mask: int, upper_start: float) -> _SortieProfile:
            return _SortieProfile(
                sequence=(mask,),
                arc_options=tuple(),
                lower_start=0.0,
                upper_start=float(upper_start),
                end_offset=1.0,
                cost=float(mask),
                mask=int(mask),
                contribution=-float(mask),
            )

        records = tuple((idx, idx, prof) for idx, prof in enumerate((profile(4, 15.0), profile(1, 5.0), profile(2, 10.0))))
        cache = _CompatibleProfileCache(records, task_count=20)
        self.assertEqual(len(cache.records(0)), 3)
        filtered = cache.records(0, min_upper_start=10.0)
        self.assertEqual([record[0] for record in filtered], [0, 2])
        self.assertEqual([record[2].upper_start for record in filtered], [15.0, 10.0])
        self.assertTrue(all(record[2].upper_start + 1.0e-9 >= 10.0 for record in filtered))

    def test_compatible_profile_cache_reuses_time_filtered_records(self):
        def profile(mask: int, upper_start: float) -> _SortieProfile:
            return _SortieProfile(
                sequence=(mask,),
                arc_options=tuple(),
                lower_start=0.0,
                upper_start=float(upper_start),
                end_offset=1.0,
                cost=float(mask),
                mask=int(mask),
                contribution=-float(mask),
            )

        records = tuple((idx, idx, prof) for idx, prof in enumerate((profile(4, 15.0), profile(1, 5.0), profile(2, 10.0))))
        cache = _CompatibleProfileCache(records, task_count=3)
        filtered = cache.records(0, min_upper_start=10.0)
        self.assertEqual([record[0] for record in filtered], [0, 2])
        self.assertIs(cache.records(0, min_upper_start=10.0), filtered)
        self.assertIn(0, cache.by_used_mask_time_index)

    def test_compatible_profile_cache_time_index_preserves_scan_order(self):
        def profile(mask: int, upper_start: float) -> _SortieProfile:
            return _SortieProfile(
                sequence=(mask,),
                arc_options=tuple(),
                lower_start=0.0,
                upper_start=float(upper_start),
                end_offset=1.0,
                cost=float(mask),
                mask=int(mask),
                contribution=-float(mask),
            )

        records = tuple(
            (idx, idx, prof)
            for idx, prof in enumerate(
                (
                    profile(1, 9.0),
                    profile(2, 3.0),
                    profile(4, 11.0),
                    profile(3, 12.0),
                    profile(5, 2.0),
                    profile(6, 10.0),
                )
            )
        )
        cache = _CompatibleProfileCache(records, task_count=3)
        filtered = cache.records(0, min_upper_start=10.0)
        expected = [record for record in cache.records(0) if float(record[2].upper_start) + 1.0e-9 >= 10.0]

        self.assertEqual(filtered, tuple(expected))
        self.assertEqual([record[0] for record in filtered], [2, 3, 5])

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_streaming_label_physical_catalog_returns_true_negative_journey(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        result = price_journeys(
            data,
            duals=JourneyDuals(cover={1: 200.0}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=JourneyPricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=1,
                time_limit=5.0,
                max_candidate_trips=0,
                max_dp_states=1000,
                streaming_pricing_enabled=True,
                streaming_profile_batch_size=1,
                profile_labeling_enabled=True,
                profile_labeling_best_first_enabled=True,
                profile_labeling_physical_catalog_resume_enabled=True,
            ),
            trip_cache={},
        )
        self.assertEqual(len(result.journeys), 1)
        self.assertTrue(result.label_physical_catalog)
        self.assertLess(result.best_reduced_cost, 0.0)
        self.assertFalse(result.exhausted)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_streaming_label_physical_catalog_reports_cache_hit_on_reuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        trip_cache: dict[tuple, object] = {}
        config = JourneyPricingConfig(
            time_bucket_size=5.0,
            start_time_step=10.0,
            max_tasks_per_trip=1,
            time_limit=5.0,
            max_candidate_trips=0,
            max_dp_states=1000,
            streaming_pricing_enabled=True,
            streaming_profile_batch_size=1,
            profile_labeling_enabled=True,
            profile_labeling_best_first_enabled=True,
            profile_labeling_physical_catalog_resume_enabled=True,
        )

        first = price_journeys(
            data,
            duals=JourneyDuals(cover={1: 200.0}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=config,
            trip_cache=trip_cache,
        )
        second = price_journeys(
            data,
            duals=JourneyDuals(cover={1: 201.0}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=config,
            trip_cache=trip_cache,
        )

        self.assertTrue(first.label_physical_catalog)
        self.assertFalse(first.profile_catalog_hit)
        self.assertTrue(second.label_physical_catalog)
        self.assertTrue(second.profile_catalog_hit)
        self.assertGreaterEqual(second.profile_catalog_size, first.profile_catalog_size)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_streaming_journey_pricing_can_still_certificate_no_negative(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        result = price_journeys(
            data,
            duals=JourneyDuals(cover={1: 10.0}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=JourneyPricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=1,
                time_limit=5.0,
                max_candidate_trips=0,
                max_dp_states=1000,
                streaming_pricing_enabled=True,
                streaming_profile_batch_size=1,
            ),
        )
        self.assertTrue(result.exhausted)
        self.assertEqual(result.journeys, [])
        self.assertEqual(result.status, "OPTIMAL")

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_direct_journey_label_pricing_returns_true_negative_journey(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        result = price_journeys(
            data,
            duals=JourneyDuals(cover={1: 200.0}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=JourneyPricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=1,
                time_limit=5.0,
                max_candidate_trips=0,
                max_dp_states=1000,
                direct_journey_label_pricing_enabled=True,
            ),
        )
        self.assertEqual(len(result.journeys), 1)
        self.assertLess(result.best_reduced_cost, 0.0)
        self.assertEqual(result.reason, "direct_label_partial_negative_journey")
        self.assertFalse(result.exhausted)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_direct_journey_label_pricing_runs_when_profile_frontend_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        result = price_journeys(
            data,
            duals=JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=JourneyPricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=1,
                time_limit=5.0,
                max_candidate_trips=0,
                max_dp_states=1000,
                profile_pricing_enabled=False,
                direct_journey_label_pricing_enabled=True,
                direct_journey_label_early_return_negative=False,
                direct_journey_label_completion_bound_enabled=True,
                direct_journey_label_completion_bound_time_buckets=5,
                direct_journey_label_completion_bound_energy_buckets=5,
            ),
        )
        self.assertTrue(result.exhausted)
        self.assertEqual(result.journeys, [])
        self.assertEqual(result.status, "OPTIMAL")
        self.assertEqual(result.reason, "direct_label_no_negative_journey")
        self.assertTrue(result.completion_bound_enabled)

    def test_select_diverse_journey_candidates_filters_high_task_overlap(self):
        first = SimpleNamespace(task_set=(1, 2, 3), signature=("first",))
        duplicate_task_set = SimpleNamespace(task_set=(1, 2, 3), signature=("duplicate",))
        high_overlap = SimpleNamespace(task_set=(1, 2, 3, 4), signature=("high_overlap",))
        disjoint = SimpleNamespace(task_set=(5,), signature=("disjoint",))
        low_overlap = SimpleNamespace(task_set=(2, 6), signature=("low_overlap",))

        selection = _select_diverse_journey_candidates(
            [
                (-10.0, first),
                (-11.0, duplicate_task_set),
                (-9.0, high_overlap),
                (-8.0, disjoint),
                (-7.0, low_overlap),
            ],
            max_returned=3,
            top_k_strongest=1,
            max_jaccard=0.4,
        )

        self.assertEqual(selection.candidate_negative_count, 5)
        self.assertEqual([journey.signature[0] for journey in selection.journeys], ["duplicate", "disjoint", "low_overlap"])
        self.assertEqual(selection.rejected_overlap_count, 1)
        self.assertEqual(selection.rejected_duplicate_task_set_count, 1)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_direct_journey_label_pricing_can_certificate_no_negative(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        result = price_journeys(
            data,
            duals=JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=JourneyPricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=1,
                time_limit=5.0,
                max_candidate_trips=0,
                max_dp_states=1000,
                direct_journey_label_pricing_enabled=True,
                direct_journey_label_early_return_negative=False,
            ),
        )
        self.assertTrue(result.exhausted)
        self.assertEqual(result.journeys, [])
        self.assertEqual(result.status, "OPTIMAL")
        self.assertEqual(result.reason, "direct_label_no_negative_journey")

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_direct_journey_label_beam_no_column_is_not_certificate(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        result = price_journeys(
            data,
            duals=JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=JourneyPricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=1,
                time_limit=5.0,
                max_candidate_trips=0,
                max_dp_states=1000,
                direct_journey_label_pricing_enabled=True,
                direct_journey_label_early_return_negative=False,
                direct_journey_label_max_labels_per_node=10,
            ),
        )
        self.assertFalse(result.exhausted)
        self.assertEqual(result.journeys, [])
        self.assertEqual(result.status, "INCOMPLETE")
        self.assertEqual(result.reason, "direct_label_beam_no_negative_journey")

    def test_direct_journey_label_ng_dssr_returns_elementary_negative_journey(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        result = price_journeys(
            data,
            duals=JourneyDuals(cover={1: 200.0}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=JourneyPricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=1,
                time_limit=5.0,
                max_candidate_trips=0,
                max_dp_states=1000,
                allow_partial_negative=True,
                direct_journey_label_pricing_enabled=True,
                direct_journey_label_ng_dssr_enabled=True,
                direct_journey_label_ng_memory_size=1,
            ),
        )
        self.assertEqual(len(result.journeys), 1)
        self.assertLess(result.best_reduced_cost, 0.0)
        self.assertTrue(result.ng_relaxation_enabled)
        self.assertFalse(result.ng_fallback_to_elementary)
        self.assertEqual(result.reason, "ng_dssr_elementary_negative_journey")
        self.assertEqual(len(result.journeys[0].task_set), sum(len(trip.tasks) for trip in result.journeys[0].trips))

    def test_direct_ng_boundary_memory_resets_noncritical_ng_state(self):
        data = load_future_data("very_small")
        label = _DirectNGJourneyLabel(
            ready_time=0.0,
            value=0.0,
            dssr_seen=frozenset({2}),
            ng_memory=frozenset({1, 2, 3}),
            visits=(1, 2, 3),
            completed=tuple(),
            current=_direct_ng_initial_partial(data),
        )
        self.assertEqual(_direct_ng_boundary_memory(label), frozenset({2}))

    def test_direct_journey_label_ng_dssr_no_negative_falls_back_to_elementary_certificate(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        result = price_journeys(
            data,
            duals=JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=JourneyPricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=1,
                time_limit=5.0,
                max_candidate_trips=0,
                max_dp_states=1000,
                direct_journey_label_pricing_enabled=True,
                direct_journey_label_early_return_negative=False,
                direct_journey_label_ng_dssr_enabled=True,
                direct_journey_label_ng_certificate_enabled=False,
                direct_journey_label_ng_exact_probe_enabled=True,
            ),
        )
        self.assertTrue(result.exhausted)
        self.assertEqual(result.journeys, [])
        self.assertEqual(result.status, "OPTIMAL")
        self.assertEqual(result.reason, "direct_label_no_negative_journey")
        self.assertTrue(result.ng_relaxation_enabled)
        self.assertTrue(result.ng_fallback_to_elementary)
        self.assertFalse(result.ng_certificate_from_relaxation)

    def test_direct_ng_certificate_dominance_key_can_include_visit_mask(self):
        data = load_future_data("very_small")
        task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
        first = int(data.tasks[0])
        second = int(data.tasks[1])
        base = _DirectNGJourneyLabel(
            ready_time=0.0,
            value=0.0,
            dssr_seen=frozenset(),
            ng_memory=frozenset(),
            visits=(first,),
            completed=tuple(),
            current=_direct_ng_initial_partial(data),
        )
        same_relaxed_state_other_cut_mask = _DirectNGJourneyLabel(
            ready_time=0.0,
            value=0.0,
            dssr_seen=frozenset(),
            ng_memory=frozenset(),
            visits=(second,),
            completed=tuple(),
            current=_direct_ng_initial_partial(data),
        )

        self.assertEqual(_direct_ng_label_key(base), _direct_ng_label_key(same_relaxed_state_other_cut_mask))
        self.assertNotEqual(
            _direct_ng_label_key(base, task_to_bit=task_to_bit, include_visit_mask=True),
            _direct_ng_label_key(
                same_relaxed_state_other_cut_mask,
                task_to_bit=task_to_bit,
                include_visit_mask=True,
            ),
        )

    def test_direct_ng_dominance_key_can_use_current_mask(self):
        data = load_future_data("very_small")
        first = int(data.tasks[0])
        second = int(data.tasks[1])
        task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
        left = _DirectNGJourneyLabel(
            ready_time=0.0,
            value=0.0,
            dssr_seen=frozenset(),
            ng_memory=frozenset(),
            visits=(first, second),
            completed=tuple(),
            current=_direct_ng_initial_partial(data),
        )
        right = _DirectNGJourneyLabel(
            ready_time=0.0,
            value=0.0,
            dssr_seen=frozenset(),
            ng_memory=frozenset(),
            visits=(second, first),
            completed=tuple(),
            current=_direct_ng_initial_partial(data),
        )
        left = replace(
            left,
            current=replace(
                left.current,
                sequence=(first, second),
                mask=(1 << task_to_bit[first]) | (1 << task_to_bit[second]),
                last=second,
            ),
        )
        right = replace(
            right,
            current=replace(
                right.current,
                sequence=(second, first),
                mask=(1 << task_to_bit[first]) | (1 << task_to_bit[second]),
                last=second,
            ),
        )

        self.assertNotEqual(_direct_ng_label_key(left), _direct_ng_label_key(right))
        self.assertEqual(
            _direct_ng_label_key(left, include_current_sequence=False),
            _direct_ng_label_key(right, include_current_sequence=False),
        )

    def test_direct_ng_relaxed_iteration_prunes_separate_branch_partial_mask(self):
        data = replace(load_future_data("very_small"), tasks=(1, 2), sortie_limit=1)
        data.instance.setdefault("scheduling", {})["task_waiting_allowed"] = False
        task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
        task_order = tuple(int(task) for task in data.tasks)
        neighborhoods = _direct_ng_neighborhoods(data, ng_size=1)
        duals = JourneyDuals(cover={1: 60.0, 2: 60.0}, fleet_limit=0.0)
        config = JourneyPricingConfig(
            time_bucket_size=5.0,
            max_tasks_per_trip=2,
            max_returned_journeys=4,
            max_dp_states=1000,
            direct_journey_label_ng_max_labels=10000,
            direct_journey_label_ng_min_negative_journeys=1,
        )

        unbranched = _direct_ng_relaxed_iteration(
            data,
            duals,
            task_order,
            task_to_bit,
            neighborhoods,
            memory=frozenset(),
            config=config,
            cuts=tuple(),
        )
        branched = _direct_ng_relaxed_iteration(
            data,
            duals,
            task_order,
            task_to_bit,
            neighborhoods,
            memory=frozenset(),
            config=config,
            cuts=tuple(),
            branch_constraints=(BranchConstraint("separate_vehicle", 1, 2),),
        )

        self.assertTrue(_direct_ng_partial_branch_pruning_safe((BranchConstraint("separate_vehicle", 1, 2),)))
        self.assertEqual(len(unbranched.journeys), 1)
        self.assertEqual(frozenset(unbranched.journeys[0].task_set), frozenset({1, 2}))
        self.assertEqual(branched.journeys, [])
        self.assertTrue(branched.exhausted)
        self.assertIsNotNone(branched.best_relaxed_reduced_cost)
        self.assertGreaterEqual(float(branched.best_relaxed_reduced_cost), -float(config.eps))

    def test_direct_journey_label_ng_dssr_can_preprobe_profile_pricing(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        result = price_journeys(
            data,
            duals=JourneyDuals(cover={1: 200.0}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=JourneyPricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=1,
                time_limit=5.0,
                max_candidate_trips=0,
                max_dp_states=1000,
                allow_partial_negative=True,
                profile_pricing_enabled=True,
                direct_journey_label_pricing_enabled=False,
                direct_journey_label_ng_dssr_enabled=True,
                direct_journey_label_ng_memory_size=1,
            ),
        )
        self.assertEqual(len(result.journeys), 1)
        self.assertLess(result.best_reduced_cost, 0.0)
        self.assertTrue(result.ng_relaxation_enabled)
        self.assertEqual(result.reason, "ng_dssr_elementary_negative_journey")

    def test_ng_preprobe_profile_pricing_filters_branch_infeasible_journeys(self):
        data = replace(load_future_data("very_small"), vehicles=(1,))
        data.instance.setdefault("scheduling", {})["task_waiting_allowed"] = False
        first = int(data.tasks[0])
        second = int(data.tasks[1])

        def fake_generate(*args, **kwargs):
            return [], 0, 0, None, False, "profile_skipped_after_ng_probe", 0

        with patch(
            "BPC_future.pricing.journey_pricing._generate_negative_sortie_profiles",
            side_effect=fake_generate,
        ):
            unbranched = _price_journeys_by_profiles(
                data,
                JourneyDuals(cover={first: 500.0}, fleet_limit=0.0),
                config=JourneyPricingConfig(
                    profile_pricing_enabled=True,
                    allow_partial_negative=True,
                    direct_journey_label_ng_dssr_enabled=True,
                    direct_journey_label_ng_memory_size=1,
                    max_tasks_per_trip=1,
                    max_returned_journeys=4,
                    time_limit=1.0,
                ),
                cuts=tuple(),
                trip_cache={},
            )
            branched = _price_journeys_by_profiles(
                data,
                JourneyDuals(cover={first: 500.0}, fleet_limit=0.0),
                branch_constraints=(BranchConstraint("same_vehicle", first, second),),
                config=JourneyPricingConfig(
                    profile_pricing_enabled=True,
                    allow_partial_negative=True,
                    direct_journey_label_ng_dssr_enabled=True,
                    direct_journey_label_ng_memory_size=1,
                    max_tasks_per_trip=1,
                    max_returned_journeys=4,
                    time_limit=1.0,
                ),
                cuts=tuple(),
                trip_cache={},
            )

        self.assertTrue(unbranched.ng_relaxation_enabled)
        self.assertTrue(unbranched.journeys)
        self.assertTrue(any(frozenset(journey.task_set) == frozenset({first}) for journey in unbranched.journeys))
        self.assertTrue(branched.ng_relaxation_enabled)
        self.assertTrue(branched.journeys)
        self.assertTrue(
            all(
                _journey_task_set_branch_allowed(
                    journey.task_set,
                    (BranchConstraint("same_vehicle", first, second),),
                )
                for journey in branched.journeys
            )
        )
        self.assertFalse(any(frozenset(journey.task_set) == frozenset({first}) for journey in branched.journeys))
        self.assertFalse(branched.exhausted)
        self.assertFalse(branched.ng_certificate_from_relaxation)

    def test_ng_preprobe_certificate_can_close_profile_pricing(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))

        certificate = JourneyPricingResult(
            [],
            True,
            0.25,
            12,
            0,
            4,
            0,
            "OPTIMAL",
            "ng_dssr_relaxed_no_negative_journey",
            ng_relaxation_enabled=True,
            ng_certificate_from_relaxation=True,
            ng_best_relaxed_reduced_cost=0.25,
        )

        def fake_ng_probe(*_args, **kwargs):
            self.assertFalse(kwargs["fallback_to_elementary"])
            self.assertTrue(kwargs["config"].direct_journey_label_ng_certificate_enabled)
            return certificate

        with patch(
            "BPC_future.pricing.journey_pricing._price_journeys_by_direct_ng_dssr",
            side_effect=fake_ng_probe,
        ), patch(
            "BPC_future.pricing.journey_pricing._generate_negative_sortie_profiles",
            side_effect=AssertionError("profile pricing should not run after an NG certificate"),
        ):
            result = _price_journeys_by_profiles(
                data,
                JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
                config=JourneyPricingConfig(
                    profile_pricing_enabled=True,
                    direct_journey_label_pricing_enabled=False,
                    direct_journey_label_ng_dssr_enabled=True,
                    direct_journey_label_ng_exact_probe_enabled=True,
                    direct_journey_label_ng_probe_certificate_enabled=True,
                ),
                cuts=tuple(),
                trip_cache=None,
            )

        self.assertTrue(result.exhausted)
        self.assertEqual(result.status, "OPTIMAL")
        self.assertTrue(result.ng_certificate_from_relaxation)
        self.assertEqual(result.reason, "ng_dssr_relaxed_no_negative_journey")

    def test_ng_preprobe_certificate_flag_alone_starts_profile_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))

        certificate = JourneyPricingResult(
            [],
            True,
            0.25,
            12,
            0,
            4,
            0,
            "OPTIMAL",
            "ng_dssr_relaxed_no_negative_journey",
            ng_relaxation_enabled=True,
            ng_certificate_from_relaxation=True,
            ng_best_relaxed_reduced_cost=0.25,
        )

        def fake_ng_probe(*_args, **kwargs):
            self.assertFalse(kwargs["fallback_to_elementary"])
            self.assertTrue(kwargs["config"].direct_journey_label_ng_certificate_enabled)
            return certificate

        with patch(
            "BPC_future.pricing.journey_pricing._price_journeys_by_direct_ng_dssr",
            side_effect=fake_ng_probe,
        ), patch(
            "BPC_future.pricing.journey_pricing._generate_negative_sortie_profiles",
            side_effect=AssertionError("profile pricing should not run after an NG certificate"),
        ):
            result = _price_journeys_by_profiles(
                data,
                JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
                config=JourneyPricingConfig(
                    profile_pricing_enabled=True,
                    direct_journey_label_pricing_enabled=False,
                    direct_journey_label_ng_dssr_enabled=True,
                    direct_journey_label_ng_exact_probe_enabled=False,
                    direct_journey_label_ng_certificate_enabled=False,
                    direct_journey_label_ng_probe_certificate_enabled=True,
                ),
                cuts=tuple(),
                trip_cache=None,
            )

        self.assertTrue(result.exhausted)
        self.assertEqual(result.status, "OPTIMAL")
        self.assertTrue(result.ng_certificate_from_relaxation)

    def test_ng_preprobe_certificate_can_close_ryan_foster_branch_pricing(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))

        certificate = JourneyPricingResult(
            [],
            True,
            0.25,
            12,
            0,
            4,
            0,
            "OPTIMAL",
            "ng_dssr_relaxed_no_negative_journey",
            ng_relaxation_enabled=True,
            ng_certificate_from_relaxation=True,
            ng_best_relaxed_reduced_cost=0.25,
        )

        def fake_ng_probe(*_args, **kwargs):
            self.assertFalse(kwargs["fallback_to_elementary"])
            self.assertTrue(kwargs["config"].direct_journey_label_ng_certificate_enabled)
            self.assertEqual(kwargs["branch_constraints"], (BranchConstraint("same_vehicle", 1, 2),))
            return certificate

        self.assertTrue(_direct_ng_branch_certificate_safe((BranchConstraint("same_vehicle", 1, 2),)))
        with patch(
            "BPC_future.pricing.journey_pricing._price_journeys_by_direct_ng_dssr",
            side_effect=fake_ng_probe,
        ), patch(
            "BPC_future.pricing.journey_pricing._generate_negative_sortie_profiles",
            side_effect=AssertionError("profile pricing should not run after a branch NG certificate"),
        ):
            result = _price_journeys_by_profiles(
                data,
                JourneyDuals(cover={1: 0.0, 2: 0.0}, fleet_limit=0.0),
                branch_constraints=(BranchConstraint("same_vehicle", 1, 2),),
                config=JourneyPricingConfig(
                    profile_pricing_enabled=True,
                    direct_journey_label_pricing_enabled=False,
                    direct_journey_label_ng_dssr_enabled=True,
                    direct_journey_label_ng_exact_probe_enabled=True,
                    direct_journey_label_ng_probe_certificate_enabled=True,
                ),
                cuts=tuple(),
                trip_cache=None,
            )

        self.assertTrue(result.exhausted)
        self.assertEqual(result.status, "OPTIMAL")
        self.assertTrue(result.ng_certificate_from_relaxation)

    def test_ng_preprobe_certificate_rejects_non_ryan_foster_branch_pricing(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))

        def fake_ng_probe(*_args, **kwargs):
            self.assertFalse(kwargs["fallback_to_elementary"])
            self.assertFalse(kwargs["config"].direct_journey_label_ng_certificate_enabled)
            return JourneyPricingResult(
                [],
                True,
                0.25,
                12,
                0,
                4,
                0,
                "OPTIMAL",
                "ng_dssr_relaxed_no_negative_journey",
                ng_relaxation_enabled=True,
                ng_certificate_from_relaxation=True,
                ng_best_relaxed_reduced_cost=0.25,
            )

        self.assertFalse(_direct_ng_branch_certificate_safe((BranchConstraint("task_vehicle_on", 1, vehicle=1),)))
        with patch(
            "BPC_future.pricing.journey_pricing._price_journeys_by_direct_ng_dssr",
            side_effect=fake_ng_probe,
        ), patch(
            "BPC_future.pricing.journey_pricing._generate_negative_sortie_profiles",
            return_value=([], 0, 0, None, True, "", 0),
        ) as profile_pricing:
            result = _price_journeys_by_profiles(
                data,
                JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
                branch_constraints=(BranchConstraint("task_vehicle_on", 1, vehicle=1),),
                config=JourneyPricingConfig(
                    profile_pricing_enabled=True,
                    direct_journey_label_pricing_enabled=False,
                    direct_journey_label_ng_dssr_enabled=True,
                    direct_journey_label_ng_exact_probe_enabled=True,
                    direct_journey_label_ng_probe_certificate_enabled=True,
                ),
                cuts=tuple(),
                trip_cache=None,
            )

        profile_pricing.assert_called_once()
        self.assertTrue(result.exhausted)
        self.assertFalse(result.ng_certificate_from_relaxation)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_direct_journey_label_task_set_bound_prunes_initial_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        result = price_journeys(
            data,
            duals=JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=JourneyPricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=1,
                time_limit=5.0,
                max_candidate_trips=0,
                max_dp_states=1000,
                direct_journey_label_pricing_enabled=True,
                direct_journey_label_early_return_negative=False,
                direct_journey_label_task_set_bound_pruning_enabled=True,
            ),
        )
        self.assertTrue(result.exhausted)
        self.assertEqual(result.journeys, [])
        self.assertEqual(result.status, "OPTIMAL")
        self.assertEqual(result.generated_sequences, 0)
        self.assertGreater(result.dp_bound_pruned_labels, 0)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_direct_journey_label_completion_bound_prunes_expanded_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        result = price_journeys(
            data,
            duals=JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=JourneyPricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=1,
                time_limit=5.0,
                max_candidate_trips=0,
                max_dp_states=1000,
                direct_journey_label_pricing_enabled=True,
                direct_journey_label_early_return_negative=False,
                direct_journey_label_task_set_bound_pruning_enabled=False,
                direct_journey_label_completion_bound_enabled=True,
                direct_journey_label_completion_bound_time_buckets=8,
            ),
        )
        self.assertTrue(result.exhausted)
        self.assertEqual(result.journeys, [])
        self.assertEqual(result.status, "OPTIMAL")
        self.assertEqual(result.reason, "direct_label_no_negative_journey")
        self.assertEqual(result.best_reduced_cost, 0.0)
        self.assertTrue(result.completion_bound_enabled)
        self.assertGreater(result.bound_build_time, 0.0)
        self.assertGreater(result.lb_state_count, 0)
        self.assertGreater(result.expanded_labels_before_bound, 0)
        self.assertGreater(result.lb_pruned_labels, 0)
        self.assertEqual(result.dp_bound_pruned_labels, result.lb_pruned_labels)
        self.assertEqual(
            result.lb_pruned_labels,
            result.lb_partial_pruned_labels + result.lb_suffix_pruned_labels,
        )

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_direct_journey_completion_bound_reuses_resource_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        config = JourneyPricingConfig(
            time_bucket_size=5.0,
            start_time_step=10.0,
            max_tasks_per_trip=1,
            time_limit=5.0,
            max_candidate_trips=0,
            max_dp_states=1000,
            direct_journey_label_pricing_enabled=True,
            direct_journey_label_early_return_negative=False,
            direct_journey_label_task_set_bound_pruning_enabled=False,
            direct_journey_label_completion_bound_enabled=True,
            direct_journey_label_completion_bound_time_buckets=5,
            direct_journey_label_completion_bound_energy_buckets=4,
            direct_journey_label_completion_bound_two_cycle_enabled=True,
        )
        cache: dict[tuple, object] = {}
        duals = JourneyDuals(cover={1: 0.0}, fleet_limit=0.0)
        first = price_journeys(
            data,
            duals=duals,
            branch_constraints=tuple(),
            config=config,
            resource_cache=cache,
        )
        second = price_journeys(
            data,
            duals=duals,
            branch_constraints=tuple(),
            config=config,
            resource_cache=cache,
        )
        self.assertTrue(first.completion_bound_enabled)
        self.assertTrue(first.completion_bound_cache_stored)
        self.assertFalse(first.completion_bound_cache_hit)
        self.assertGreater(first.bound_build_time, 0.0)
        self.assertTrue(second.completion_bound_enabled)
        self.assertTrue(second.completion_bound_cache_hit)
        self.assertFalse(second.completion_bound_cache_stored)
        self.assertEqual(second.bound_build_time, 0.0)
        self.assertEqual(first.status, second.status)
        self.assertEqual(first.reason, second.reason)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_direct_journey_completion_bound_cache_key_ignores_fleet_dual(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        config = JourneyPricingConfig(
            time_bucket_size=5.0,
            start_time_step=10.0,
            max_tasks_per_trip=1,
            time_limit=5.0,
            max_candidate_trips=0,
            max_dp_states=1000,
            direct_journey_label_pricing_enabled=True,
            direct_journey_label_early_return_negative=False,
            direct_journey_label_task_set_bound_pruning_enabled=False,
            direct_journey_label_completion_bound_enabled=True,
            direct_journey_label_completion_bound_time_buckets=5,
            direct_journey_label_completion_bound_energy_buckets=4,
            direct_journey_label_completion_bound_two_cycle_enabled=True,
        )
        low_fleet_dual = JourneyDuals(cover={1: 3.0}, fleet_limit=-10.0)
        high_fleet_dual = JourneyDuals(cover={1: 3.0}, fleet_limit=25.0)
        self.assertEqual(
            _direct_completion_bound_cache_key(data, low_fleet_dual, config),
            _direct_completion_bound_cache_key(data, high_fleet_dual, config),
        )

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_direct_journey_label_two_cycle_completion_bound_audit_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        result = price_journeys(
            data,
            duals=JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=JourneyPricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=1,
                time_limit=5.0,
                max_candidate_trips=0,
                max_dp_states=1000,
                direct_journey_label_pricing_enabled=True,
                direct_journey_label_early_return_negative=False,
                direct_journey_label_task_set_bound_pruning_enabled=False,
                direct_journey_label_completion_bound_enabled=True,
                direct_journey_label_completion_bound_time_buckets=5,
                direct_journey_label_completion_bound_energy_buckets=4,
                direct_journey_label_completion_bound_two_cycle_enabled=True,
                direct_journey_label_completion_bound_audit_enabled=True,
            ),
        )
        self.assertTrue(result.exhausted)
        self.assertEqual(result.status, "OPTIMAL")
        self.assertEqual(result.reason, "direct_label_no_negative_journey")
        self.assertEqual(result.best_reduced_cost, 0.0)
        self.assertTrue(result.completion_bound_enabled)
        self.assertTrue(result.two_cycle_enabled)
        self.assertTrue(result.two_cycle_table_complete)
        self.assertFalse(result.two_cycle_fallback_to_memoryless)
        self.assertGreater(result.two_cycle_state_count, 0)
        self.assertGreater(result.lb_pruned_labels, 0)
        self.assertEqual(
            result.lb_pruned_labels,
            result.lb_partial_pruned_labels + result.lb_suffix_pruned_labels,
        )

    def test_direct_journey_completion_bound_state_is_node_time_energy_only(self):
        data = load_future_data("very_small")
        bound = _DirectJourneyCompletionBound(
            data,
            JourneyDuals(cover={int(task): 0.0 for task in data.tasks}, fleet_limit=0.0),
            time_buckets=5,
            energy_buckets=4,
            max_tasks_per_sortie=6,
            sortie_limit=int(data.sortie_limit),
        )
        expected_states = (len(data.tasks) + 1) * (5 + 1) * (4 + 1)
        self.assertEqual(bound.state_count, expected_states)
        self.assertIn(0, bound.node_values)
        self.assertEqual(len(bound.node_values[0]), 6)
        self.assertEqual(len(bound.node_values[0][0]), 5)
        self.assertTrue(math.isfinite(bound.partial_value(0, -1, 6, 0, 0.0, 0.0)))

    def test_direct_journey_completion_bound_caches_arc_enumeration(self):
        data = replace(load_future_data("very_small"), tasks=(1, 2), sortie_limit=2)
        duals = JourneyDuals(cover={1: 10.0, 2: 5.0}, fleet_limit=0.0)
        bound = _DirectJourneyCompletionBound(
            data,
            duals,
            time_buckets=5,
            energy_buckets=4,
            max_tasks_per_sortie=2,
            sortie_limit=2,
            two_cycle_enabled=True,
        )
        fresh = _DirectJourneyCompletionBound(
            data,
            duals,
            time_buckets=5,
            energy_buckets=4,
            max_tasks_per_sortie=2,
            sortie_limit=2,
            two_cycle_enabled=True,
        )

        self.assertGreater(len(bound._task_transition_cache), 0)
        self.assertGreater(len(bound._return_completion_cache), 0)
        transition_cache_size = len(bound._task_transition_cache)
        return_cache_size = len(bound._return_completion_cache)

        transitions = bound._task_transitions(
            0,
            1,
            time_bucket=0,
            depart_time=bound._bucket_time(0),
            energy_used=bound._bucket_energy(0),
        )
        self.assertIs(
            transitions,
            bound._task_transitions(
                0,
                1,
                time_bucket=0,
                depart_time=bound._bucket_time(0),
                energy_used=bound._bucket_energy(0),
            ),
        )
        self.assertEqual(len(bound._task_transition_cache), transition_cache_size)

        return_candidates = bound._return_arc_completion_candidates(
            1,
            depart_time=bound._bucket_time(0),
            energy_used=bound._bucket_energy(0),
        )
        self.assertIs(
            return_candidates,
            bound._return_arc_completion_candidates(
                1,
                depart_time=bound._bucket_time(0),
                energy_used=bound._bucket_energy(0),
            ),
        )
        self.assertEqual(len(bound._return_completion_cache), return_cache_size)

        self.assertAlmostEqual(
            bound.partial_value(1, 0, 1, 1, 0.0, 0.0),
            fresh.partial_value(1, 0, 1, 1, 0.0, 0.0),
            places=9,
        )

    def test_direct_journey_completion_bound_keeps_arc_option_triplets(self):
        data = replace(load_future_data("very_small"), tasks=(1,))
        slow_cheap = ArcOption(
            option_id="slow-cheap",
            path_type="test",
            aliases=tuple(),
            tau=30.0,
            energy=10.0,
            risk=0.0,
            distance=1.0,
            cost=1.0,
        )
        fast_expensive = ArcOption(
            option_id="fast-expensive",
            path_type="test",
            aliases=tuple(),
            tau=5.0,
            energy=1.0,
            risk=0.0,
            distance=1.0,
            cost=10.0,
        )
        data = replace(
            data,
            arc_options={
                **data.arc_options,
                (0, 1): (slow_cheap, fast_expensive),
            },
        )
        bound = _DirectJourneyCompletionBound(
            data,
            JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
            time_buckets=10,
            energy_buckets=10,
            max_tasks_per_sortie=1,
            sortie_limit=1,
        )
        transitions = bound._task_transitions(0, 1, time_bucket=0, depart_time=0.0, energy_used=0.0)
        service_cost = float(data.task_value(1, "c_srv"))
        service_time = float(data.task_value(1, "sigma"))
        ready_time = float(data.task_value(1, "r"))
        fast_bucket = bound._bucket_of_time(max(float(fast_expensive.tau), ready_time) + service_time)
        slow_bucket = bound._bucket_of_time(max(float(slow_cheap.tau), ready_time) + service_time)

        self.assertTrue(
            any(
                bucket == fast_bucket and math.isclose(value, float(fast_expensive.cost) + service_cost)
                for bucket, _energy_bucket, value in transitions
            )
        )
        self.assertTrue(
            any(
                bucket == slow_bucket and math.isclose(value, float(slow_cheap.cost) + service_cost)
                for bucket, _energy_bucket, value in transitions
            )
        )
        self.assertFalse(
            any(
                bucket == fast_bucket and math.isclose(value, float(slow_cheap.cost) + service_cost)
                for bucket, _energy_bucket, value in transitions
            )
        )

    def test_direct_journey_completion_bound_accounts_for_ready_time(self):
        data = replace(load_future_data("very_small"), tasks=(1,), horizon=100.0)
        instance = dict(data.instance)
        tasks = {str(task): dict(payload) for task, payload in data.instance["tasks"].items()}
        tasks["1"] = {**tasks["1"], "r": 80.0, "D": 95.0, "sigma": 5.0}
        data = replace(data, instance={**instance, "tasks": tasks})
        option = ArcOption(
            option_id="early-arrival",
            path_type="test",
            aliases=tuple(),
            tau=1.0,
            energy=1.0,
            risk=0.0,
            distance=1.0,
            cost=1.0,
        )
        data = replace(
            data,
            arc_options={
                **data.arc_options,
                (0, 1): (option,),
            },
        )
        bound = _DirectJourneyCompletionBound(
            data,
            JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
            time_buckets=10,
            energy_buckets=10,
            max_tasks_per_sortie=1,
            sortie_limit=1,
        )
        transitions = bound._task_transitions(0, 1, time_bucket=0, depart_time=0.0, energy_used=0.0)
        expected_bucket = bound._bucket_of_time(85.0)

        self.assertTrue(transitions)
        self.assertTrue(any(bucket == expected_bucket for bucket, _energy_bucket, _value in transitions))
        self.assertFalse(any(bucket == bound._bucket_of_time(6.0) for bucket, _energy_bucket, _value in transitions))

    def test_direct_journey_completion_bound_future_suffix_respects_current_time(self):
        data = replace(load_future_data("very_small"), tasks=(1,), sortie_limit=2, horizon=100.0)
        instance = dict(data.instance)
        tasks = {str(task): dict(payload) for task, payload in data.instance["tasks"].items()}
        tasks["1"] = {**tasks["1"], "r": 0.0, "D": 60.0, "sigma": 5.0, "c_srv": 0.0, "g": 0.0}
        outbound = ArcOption(
            option_id="outbound",
            path_type="test",
            aliases=tuple(),
            tau=15.0,
            energy=1.0,
            risk=0.0,
            distance=1.0,
            cost=1.0,
        )
        inbound = ArcOption(
            option_id="return",
            path_type="test",
            aliases=tuple(),
            tau=5.0,
            energy=1.0,
            risk=0.0,
            distance=1.0,
            cost=1.0,
        )
        data = replace(
            data,
            instance={**instance, "tasks": tasks},
            arc_options={(0, 1): (outbound,), (1, 0): (inbound,)},
        )
        duals = JourneyDuals(cover={1: 50.0}, fleet_limit=0.0)
        memoryless = _DirectJourneyCompletionBound(
            data,
            duals,
            time_buckets=10,
            energy_buckets=5,
            max_tasks_per_sortie=1,
            sortie_limit=2,
        )
        two_cycle = _DirectJourneyCompletionBound(
            data,
            duals,
            time_buckets=10,
            energy_buckets=5,
            max_tasks_per_sortie=1,
            sortie_limit=2,
            two_cycle_enabled=True,
        )

        self.assertLess(memoryless.value(1, 0.0), 0.0)
        self.assertEqual(memoryless.value(1, 95.0), 0.0)
        self.assertGreater(memoryless.value(1, 95.0), memoryless.value(1, 0.0))
        self.assertLess(two_cycle.value(1, 0.0), 0.0)
        self.assertEqual(two_cycle.value(1, 95.0), 0.0)
        self.assertGreater(two_cycle.value(1, 95.0), two_cycle.value(1, 0.0))

    def test_two_cycle_return_suffix_uses_return_ready_time(self):
        data = replace(load_future_data("very_small"), tasks=(1,), sortie_limit=2, horizon=100.0, rho=1.0)
        instance = dict(data.instance)
        tasks = {str(task): dict(payload) for task, payload in data.instance["tasks"].items()}
        tasks["1"] = {**tasks["1"], "r": 0.0, "D": 60.0, "sigma": 0.0, "c_srv": 0.0, "g": 0.0}
        outbound = ArcOption(
            option_id="outbound",
            path_type="test",
            aliases=tuple(),
            tau=15.0,
            energy=0.0,
            risk=0.0,
            distance=1.0,
            cost=1.0,
        )
        inbound = ArcOption(
            option_id="return",
            path_type="test",
            aliases=tuple(),
            tau=5.0,
            energy=0.0,
            risk=0.0,
            distance=1.0,
            cost=1.0,
        )
        data = replace(
            data,
            instance={**instance, "tasks": tasks},
            arc_options={(0, 1): (outbound,), (1, 0): (inbound,)},
        )
        bound = _DirectJourneyCompletionBound(
            data,
            JourneyDuals(cover={1: 50.0}, fleet_limit=0.0),
            time_buckets=20,
            energy_buckets=0,
            max_tasks_per_sortie=1,
            sortie_limit=2,
            two_cycle_enabled=True,
        )

        early_return_then_future = bound.partial_value(1, 0, 0, 1, 0.0, 0.0)
        late_return_then_future = bound.partial_value(1, 0, 0, 1, 60.0, 0.0)

        self.assertLess(early_return_then_future, 0.0)
        self.assertAlmostEqual(late_return_then_future, float(inbound.cost), places=6)
        self.assertGreater(late_return_then_future, early_return_then_future)

    def test_completion_bounds_account_for_survival_energy_lower_bound(self):
        return_option = ArcOption(
            option_id="return",
            path_type="test",
            aliases=tuple(),
            tau=10.0,
            energy=9.0,
            risk=0.0,
            distance=1.0,
            cost=2.0,
        )
        outbound_option = ArcOption(
            option_id="outbound",
            path_type="test",
            aliases=tuple(),
            tau=1.0,
            energy=1.0,
            risk=0.0,
            distance=1.0,
            cost=1.0,
        )
        base = replace(
            load_future_data("very_small"),
            tasks=(1,),
            sortie_limit=1,
            horizon=100.0,
            energy_limit=10.0,
            rho=1.0,
            arc_options={(0, 1): (outbound_option,), (1, 0): (return_option,)},
        )
        no_survival = replace(base, survival_energy_rate=0.0)
        with_survival = replace(base, survival_energy_rate=0.2)

        direct_no_survival = _DirectJourneyCompletionBound(
            no_survival,
            JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
            time_buckets=10,
            energy_buckets=10,
            max_tasks_per_sortie=1,
            sortie_limit=1,
        )
        direct_with_survival = _DirectJourneyCompletionBound(
            with_survival,
            JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
            time_buckets=10,
            energy_buckets=10,
            max_tasks_per_sortie=1,
            sortie_limit=1,
        )
        self.assertTrue(math.isfinite(direct_no_survival.partial_value(1, 0, 0, 0, 0.0, 0.0)))
        self.assertTrue(math.isinf(direct_with_survival.partial_value(1, 0, 0, 0, 0.0, 0.0)))

        unique_no_survival = _UniqueRouteCompletionLowerBound(
            no_survival,
            FutureDuals(
                cover={1: 0.0},
                task_vehicle={},
                sortie_count={},
                time_occupation={},
                ordering={},
                branches={},
            ),
            {1: 0},
            max_tasks_per_sortie=1,
            sortie_limit=1,
            time_buckets=10,
            energy_buckets=10,
        )
        unique_with_survival = _UniqueRouteCompletionLowerBound(
            with_survival,
            FutureDuals(
                cover={1: 0.0},
                task_vehicle={},
                sortie_count={},
                time_occupation={},
                ordering={},
                branches={},
            ),
            {1: 0},
            max_tasks_per_sortie=1,
            sortie_limit=1,
            time_buckets=10,
            energy_buckets=10,
        )
        self.assertTrue(math.isfinite(unique_no_survival.partial_value(1, 0, 0, 0, 0.0, 0.0)))
        self.assertTrue(math.isinf(unique_with_survival.partial_value(1, 0, 0, 0, 0.0, 0.0)))

    def test_unique_route_completion_bound_keeps_arc_option_triplets(self):
        data = replace(load_future_data("very_small"), tasks=(1,), sortie_limit=1)
        slow_cheap = ArcOption(
            option_id="slow-cheap",
            path_type="test",
            aliases=tuple(),
            tau=float(data.horizon) + 1000.0,
            energy=1.0,
            risk=0.0,
            distance=1.0,
            cost=1.0,
        )
        fast_expensive = ArcOption(
            option_id="fast-expensive",
            path_type="test",
            aliases=tuple(),
            tau=1.0,
            energy=1.0,
            risk=0.0,
            distance=1.0,
            cost=10.0,
        )
        return_option = ArcOption(
            option_id="return",
            path_type="test",
            aliases=tuple(),
            tau=1.0,
            energy=1.0,
            risk=0.0,
            distance=1.0,
            cost=2.0,
        )
        data = replace(
            data,
            arc_options={
                **data.arc_options,
                (0, 1): (slow_cheap, fast_expensive),
                (1, 0): (return_option,),
            },
        )
        bound = _UniqueRouteCompletionLowerBound(
            data,
            FutureDuals(
                cover={1: 100.0},
                task_vehicle={},
                sortie_count={},
                time_occupation={},
                ordering={},
                branches={},
            ),
            {1: 0},
            max_tasks_per_sortie=1,
            sortie_limit=1,
            time_buckets=10,
            energy_buckets=10,
        )
        value = bound.future_value(available_mask=1, remaining_sorties=1, current_time=0.0)
        expected = float(fast_expensive.cost) + float(data.task_value(1, "c_srv")) - 100.0 + float(return_option.cost)
        self.assertIsNotNone(value)
        self.assertAlmostEqual(float(value), expected)

    def test_unique_route_completion_bound_accounts_for_return_recharge_time(self):
        data = replace(
            load_future_data("very_small"),
            tasks=(1, 2),
            sortie_limit=1,
            horizon=20.0,
            energy_limit=100.0,
            rho=1.0,
        )

        def option(name: str, tau: float, energy: float, cost: float) -> ArcOption:
            return ArcOption(
                option_id=name,
                path_type="test",
                aliases=tuple(),
                tau=float(tau),
                energy=float(energy),
                risk=0.0,
                distance=1.0,
                cost=float(cost),
            )

        data = replace(
            data,
            arc_options={
                (0, 1): (option("0-1", 1.0, 9.0, 0.0),),
                (1, 0): (option("1-0", 1.0, 9.0, 0.0),),
                (0, 2): (option("0-2", 1.0, 0.0, 0.0),),
                (2, 0): (option("2-0", 1.0, 0.0, 0.0),),
                (1, 2): (option("1-2", 1.0, 1000.0, 1000.0),),
                (2, 1): (option("2-1", 1.0, 1000.0, 1000.0),),
            },
        )
        bound = _UniqueRouteCompletionLowerBound(
            data,
            FutureDuals(
                cover={1: 100.0, 2: 20.0},
                task_vehicle={},
                sortie_count={},
                time_occupation={},
                ordering={},
                branches={},
            ),
            {1: 0, 2: 1},
            max_tasks_per_sortie=1,
            sortie_limit=1,
            time_buckets=20,
            energy_buckets=20,
        )

        value = bound.future_value(available_mask=3, remaining_sorties=1, current_time=0.0)
        expected_task2 = float(data.task_value(2, "c_srv")) - 20.0
        self.assertIsNotNone(value)
        self.assertAlmostEqual(float(value), expected_task2)
        self.assertGreater(float(value), -50.0)

    def test_unique_route_completion_bound_exact_first_step_tightens_current_time(self):
        data = replace(
            load_future_data("very_small"),
            tasks=(1,),
            sortie_limit=1,
            horizon=10.0,
            energy_limit=100.0,
            arc_options={
                (0, 1): (
                    ArcOption(
                        option_id="outbound",
                        path_type="test",
                        aliases=tuple(),
                        tau=1.0,
                        energy=0.0,
                        risk=0.0,
                        distance=1.0,
                        cost=0.0,
                    ),
                ),
                (1, 0): (
                    ArcOption(
                        option_id="late-return",
                        path_type="test",
                        aliases=tuple(),
                        tau=1.0,
                        energy=0.0,
                        risk=0.0,
                        distance=1.0,
                        cost=0.0,
                    ),
                ),
            },
        )
        duals = FutureDuals(
            cover={1: 0.0},
            task_vehicle={},
            sortie_count={},
            time_occupation={},
            ordering={},
            branches={},
        )
        bucketed = _UniqueRouteCompletionLowerBound(
            data,
            duals,
            {1: 0},
            max_tasks_per_sortie=1,
            sortie_limit=1,
            time_buckets=1,
            energy_buckets=1,
        )
        exact_first = _UniqueRouteCompletionLowerBound(
            data,
            duals,
            {1: 0},
            max_tasks_per_sortie=1,
            sortie_limit=1,
            time_buckets=1,
            energy_buckets=1,
            exact_first_step_enabled=True,
        )

        bucketed_value = bucketed.partial_value(
            last=1,
            available_mask=0,
            remaining_slots_in_sortie=0,
            future_sorties=0,
            current_time=9.5,
            current_energy=0.0,
        )
        exact_first_value = exact_first.partial_value(
            last=1,
            available_mask=0,
            remaining_slots_in_sortie=0,
            future_sorties=0,
            current_time=9.5,
            current_energy=0.0,
        )

        self.assertTrue(math.isfinite(float(bucketed_value)))
        self.assertTrue(math.isinf(float(exact_first_value)))

    def test_unique_route_completion_bound_reports_cache_hits(self):
        data = replace(load_future_data("very_small"), tasks=(1,), sortie_limit=1)
        duals = FutureDuals(
            cover={1: 50.0},
            task_vehicle={},
            sortie_count={},
            time_occupation={},
            ordering={},
            branches={},
        )
        bound = _UniqueRouteCompletionLowerBound(
            data,
            duals,
            {1: 0},
            max_tasks_per_sortie=1,
            sortie_limit=1,
            time_buckets=5,
            energy_buckets=5,
            exact_first_step_enabled=True,
        )

        first = bound.partial_value(
            last=0,
            available_mask=1,
            remaining_slots_in_sortie=1,
            future_sorties=0,
            current_time=0.0,
            current_energy=0.0,
        )
        second = bound.partial_value(
            last=0,
            available_mask=1,
            remaining_slots_in_sortie=1,
            future_sorties=0,
            current_time=0.0,
            current_energy=0.0,
        )

        self.assertEqual(first, second)
        self.assertGreaterEqual(bound.partial_cache_misses, 1)
        self.assertGreaterEqual(bound.partial_cache_hits, 1)
        self.assertEqual(bound.exact_first_step_cache_misses, 1)
        self.assertEqual(bound.exact_first_step_cache_hits, 1)
        self.assertEqual(len(bound._exact_first_step_cache), 1)

    def test_unique_route_exact_first_step_cache_cap_keeps_computing(self):
        data = replace(load_future_data("very_small"), tasks=(1,), sortie_limit=1)
        bound = _UniqueRouteCompletionLowerBound(
            data,
            FutureDuals(
                cover={1: 50.0},
                task_vehicle={},
                sortie_count={},
                time_occupation={},
                ordering={},
                branches={},
            ),
            {1: 0},
            max_tasks_per_sortie=1,
            sortie_limit=1,
            time_buckets=5,
            energy_buckets=5,
            exact_first_step_enabled=True,
        )
        bound.EXACT_FIRST_STEP_CACHE_MAX_SIZE = 1

        first = bound.partial_value(0, 1, 1, 0, current_time=0.0, current_energy=0.0)
        second = bound.partial_value(0, 1, 1, 0, current_time=0.1, current_energy=0.0)
        first_again = bound.partial_value(0, 1, 1, 0, current_time=0.0, current_energy=0.0)

        self.assertTrue(math.isfinite(float(first)))
        self.assertTrue(math.isfinite(float(second)))
        self.assertEqual(first, first_again)
        self.assertEqual(len(bound._exact_first_step_cache), 1)
        self.assertEqual(bound.exact_first_step_cache_hits, 1)
        self.assertEqual(bound.exact_first_step_cache_misses, 2)

    def test_unique_route_exact_first_step_skips_when_bucketed_bound_infeasible(self):
        data = replace(
            load_future_data("very_small"),
            tasks=(1,),
            sortie_limit=1,
            arc_options={(0, 1): tuple(), (1, 0): tuple()},
        )
        bound = _UniqueRouteCompletionLowerBound(
            data,
            FutureDuals(
                cover={1: 0.0},
                task_vehicle={},
                sortie_count={},
                time_occupation={},
                ordering={},
                branches={},
            ),
            {1: 0},
            max_tasks_per_sortie=1,
            sortie_limit=1,
            time_buckets=5,
            energy_buckets=5,
            exact_first_step_enabled=True,
        )

        value = bound.partial_value(
            last=1,
            available_mask=0,
            remaining_slots_in_sortie=0,
            future_sorties=0,
            current_time=0.0,
            current_energy=0.0,
        )

        self.assertTrue(math.isinf(float(value)))
        self.assertEqual(bound.exact_first_step_cache_hits, 0)
        self.assertEqual(bound.exact_first_step_cache_misses, 0)
        self.assertEqual(len(bound._exact_first_step_cache), 0)

    def test_direct_journey_completion_bound_two_cycle_depot_immune_and_budget_fallback(self):
        data = replace(load_future_data("very_small"), tasks=(1,), sortie_limit=1)
        duals = JourneyDuals(cover={1: 0.0}, fleet_limit=0.0)
        memoryless = _DirectJourneyCompletionBound(
            data,
            duals,
            time_buckets=5,
            energy_buckets=4,
            max_tasks_per_sortie=1,
            sortie_limit=1,
        )
        two_cycle = _DirectJourneyCompletionBound(
            data,
            duals,
            time_buckets=5,
            energy_buckets=4,
            max_tasks_per_sortie=1,
            sortie_limit=1,
            two_cycle_enabled=True,
        )
        self.assertTrue(two_cycle.two_cycle_table_complete)
        self.assertFalse(two_cycle.two_cycle_fallback_to_memoryless)
        # Depot is immune: the legal one-task sortie Depot -> 1 -> Depot must
        # remain compatible even though the reverse label's predecessor is depot.
        depot_immune_lb = two_cycle.partial_value(1, 0, 0, 0, 0.0, 0.0)
        self.assertTrue(math.isfinite(depot_immune_lb))

        fallback = _DirectJourneyCompletionBound(
            data,
            duals,
            time_buckets=5,
            energy_buckets=4,
            max_tasks_per_sortie=1,
            sortie_limit=1,
            two_cycle_enabled=True,
            two_cycle_max_states=1,
        )
        self.assertFalse(fallback.two_cycle_table_complete)
        self.assertTrue(fallback.two_cycle_fallback_to_memoryless)
        self.assertAlmostEqual(
            fallback.partial_value(1, 1, 0, 0, 0.0, 0.0),
            memoryless.partial_value(1, 1, 0, 0, 0.0, 0.0),
        )

        deadline_fallback = _DirectJourneyCompletionBound(
            data,
            duals,
            time_buckets=5,
            energy_buckets=4,
            max_tasks_per_sortie=1,
            sortie_limit=1,
            two_cycle_enabled=True,
            deadline=time.perf_counter() - 1.0,
        )
        self.assertFalse(deadline_fallback.two_cycle_table_complete)
        self.assertTrue(deadline_fallback.two_cycle_fallback_to_memoryless)
        self.assertAlmostEqual(
            deadline_fallback.partial_value(1, 1, 0, 0, 0.0, 0.0),
            memoryless.partial_value(1, 1, 0, 0, 0.0, 0.0),
        )

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_direct_journey_label_completion_bound_can_keep_next_sortie_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        result = price_journeys(
            data,
            duals=JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=JourneyPricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=1,
                time_limit=5.0,
                max_candidate_trips=0,
                max_dp_states=1000,
                direct_journey_label_pricing_enabled=True,
                direct_journey_label_early_return_negative=False,
                direct_journey_label_task_set_bound_pruning_enabled=False,
                direct_journey_label_completion_bound_enabled=True,
                direct_journey_label_completion_bound_time_buckets=8,
                direct_journey_label_completion_bound_partial_pruning_enabled=False,
            ),
        )
        self.assertTrue(result.completion_bound_enabled)
        self.assertGreater(result.direct_next_sortie_cache_misses, 0)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_direct_journey_label_pricing_keeps_cut_dual_reward_candidate(self):
        data = load_future_data("very_small")
        instance = dict(data.instance)
        instance["scheduling"] = {"task_waiting_allowed": False}
        data = replace(data, instance=instance)
        first, second = int(data.tasks[0]), int(data.tasks[1])
        cut = SubsetRowCut((first, second), 2)
        result = price_journeys(
            data,
            duals=JourneyDuals(
                cover={int(task): 0.0 for task in data.tasks},
                fleet_limit=0.0,
                cuts={0: 500.0},
            ),
            branch_constraints=tuple(),
            cuts=(cut,),
            config=JourneyPricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=2,
                time_limit=5.0,
                max_candidate_trips=0,
                max_dp_states=10000,
                direct_journey_label_pricing_enabled=True,
                direct_journey_label_completion_bound_enabled=True,
                direct_journey_label_completion_bound_time_buckets=8,
            ),
        )
        self.assertTrue(result.completion_bound_enabled)
        self.assertEqual(len(result.journeys), 1)
        self.assertLess(result.best_reduced_cost, 0.0)
        self.assertIn(first, result.journeys[0].task_set)
        self.assertIn(second, result.journeys[0].task_set)

    def test_direct_journey_completion_bound_respects_branch_constraints(self):
        data = load_future_data("very_small")
        instance = dict(data.instance)
        instance["scheduling"] = {"task_waiting_allowed": False}
        data = replace(data, instance=instance)
        first, second = int(data.tasks[0]), int(data.tasks[1])
        constraint = BranchConstraint("separate_vehicle", first, second)
        result = price_journeys(
            data,
            duals=JourneyDuals(cover={int(task): 1000.0 for task in data.tasks}, fleet_limit=0.0),
            branch_constraints=(constraint,),
            config=JourneyPricingConfig(
                profile_pricing_enabled=True,
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=2,
                time_limit=5.0,
                max_candidate_trips=0,
                max_dp_states=10000,
                direct_journey_label_pricing_enabled=True,
                direct_journey_label_completion_bound_enabled=True,
                direct_journey_label_completion_bound_time_buckets=6,
                direct_journey_label_completion_bound_energy_buckets=6,
            ),
        )
        self.assertTrue(result.completion_bound_enabled)
        self.assertTrue(result.journeys)
        for journey in result.journeys:
            self.assertTrue(_journey_task_set_branch_allowed(journey.task_set, (constraint,)))

    def test_direct_next_sortie_profile_cache_matches_uncached_generation(self):
        data = load_future_data("very_small")
        vehicle = int(data.vehicles[0])
        duals = FutureDuals(
            cover={int(task): 100.0 for task in data.tasks},
            task_vehicle={},
            sortie_count={vehicle: 0.0},
            time_occupation={},
            ordering={},
            branches={},
        )
        task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
        task_order = tuple(int(task) for task in data.tasks)
        config = JourneyPricingConfig(
            time_bucket_size=5.0,
            start_time_step=10.0,
            max_tasks_per_trip=2,
            max_dp_states=10000,
            direct_journey_label_pricing_enabled=True,
        )
        uncached, _gen, _eval, reason, _bound_checked, _bound_pruned = _direct_next_sortie_trips(
            data,
            duals,
            task_order,
            task_to_bit,
            used_mask=0,
            earliest_start=0.0,
            threshold=float("inf"),
            cut_duals={},
            cuts=tuple(),
            cut_masks=tuple(),
            cut_pruning_safe=True,
            config=config,
            deadline=None,
        )
        self.assertEqual(reason, "")
        profiles, _profile_gen, _profile_eval, profile_reason = _direct_next_sortie_profiles(
            data,
            duals,
            task_order,
            task_to_bit,
            used_mask=0,
            config=config,
            deadline=None,
        )
        self.assertEqual(profile_reason, "")
        cached, _inst_eval, conversion_reason = _direct_sortie_profiles_to_trips(
            data,
            profiles,
            earliest_start=0.0,
            threshold=float("inf"),
            cut_duals={},
            cuts=tuple(),
            cut_masks=tuple(),
            cut_pruning_safe=True,
            config=config,
        )
        self.assertEqual(conversion_reason, "")
        self.assertEqual({trip.signature for trip, _contribution, _mask in uncached}, {trip.signature for trip, _contribution, _mask in cached})

    def test_direct_next_sortie_trip_return_limit_is_incomplete_soft_stop(self):
        data = load_future_data("very_small")
        vehicle = int(data.vehicles[0])
        duals = FutureDuals(
            cover={int(task): 100.0 for task in data.tasks},
            task_vehicle={},
            sortie_count={vehicle: 0.0},
            time_occupation={},
            ordering={},
            branches={},
        )
        task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
        task_order = tuple(int(task) for task in data.tasks)
        limited, _gen, _eval, reason, _bound_checked, _bound_pruned = _direct_next_sortie_trips(
            data,
            duals,
            task_order,
            task_to_bit,
            used_mask=0,
            earliest_start=0.0,
            threshold=float("inf"),
            cut_duals={},
            cuts=tuple(),
            cut_masks=tuple(),
            cut_pruning_safe=True,
            config=JourneyPricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=2,
                max_dp_states=10000,
                direct_journey_label_pricing_enabled=True,
                direct_journey_label_next_sortie_trip_return_limit=1,
            ),
            deadline=None,
        )
        self.assertEqual(reason, "direct_label_next_sortie_trip_return_limit")
        self.assertGreaterEqual(len(limited), 1)

    def test_direct_next_sortie_streaming_callback_returns_immediately(self):
        data = load_future_data("very_small")
        vehicle = int(data.vehicles[0])
        duals = FutureDuals(
            cover={int(task): 100.0 for task in data.tasks},
            task_vehicle={},
            sortie_count={vehicle: 0.0},
            time_occupation={},
            ordering={},
            branches={},
        )
        task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
        task_order = tuple(int(task) for task in data.tasks)
        streamed_signatures: list[tuple] = []

        def _stop_after_first(trip, _contribution, _trip_mask):
            streamed_signatures.append(trip.signature)
            return True

        streamed, _gen, _eval, reason, _bound_checked, _bound_pruned = _direct_next_sortie_trips(
            data,
            duals,
            task_order,
            task_to_bit,
            used_mask=0,
            earliest_start=0.0,
            threshold=float("inf"),
            cut_duals={},
            cuts=tuple(),
            cut_masks=tuple(),
            cut_pruning_safe=True,
            config=JourneyPricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=2,
                max_dp_states=10000,
                direct_journey_label_pricing_enabled=True,
            ),
            deadline=None,
            completed_trip_callback=_stop_after_first,
        )
        self.assertEqual(reason, "direct_label_next_sortie_streaming_negative_journey")
        self.assertEqual(len(streamed_signatures), 1)
        self.assertIn(streamed_signatures[0], {trip.signature for trip, _contribution, _mask in streamed})

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_nonprofile_weak_negative_threshold_is_not_certificate(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        trip = evaluate_timed_trip(data, (1,), 0.0, time_bucket_size=5.0)
        self.assertIsNotNone(trip)
        assert trip is not None
        weak_cover = float(data.fixed_vehicle_cost) + float(trip.cost) + 2.0e-6
        result = price_journeys(
            data,
            duals=JourneyDuals(cover={1: weak_cover}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=JourneyPricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=1,
                time_limit=5.0,
                max_candidate_trips=0,
                max_dp_states=1000,
                profile_pricing_enabled=False,
                min_add_reduced_cost=1.0e-4,
            ),
        )
        self.assertFalse(result.exhausted)
        self.assertEqual(result.status, "INCOMPLETE")
        self.assertEqual(result.reason, "weak_negative_journeys_filtered")
        self.assertEqual(result.weak_negative_journeys_filtered, 1)

    def test_label_sortie_profile_generator_matches_permutation_generator_small_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        vehicle = int(data.vehicles[0])
        duals = FutureDuals(
            cover={1: 200.0},
            task_vehicle={},
            sortie_count={vehicle: 0.0},
            time_occupation={},
            ordering={},
            branches={},
            cuts={},
        )

        def profile_keys(profiles):
            return {
                (
                    profile.sequence,
                    tuple(option.option_id for option in profile.arc_options),
                    round(profile.lower_start, 6),
                    round(profile.upper_start, 6),
                    round(profile.end_offset, 6),
                    round(profile.contribution, 6),
                )
                for profile in profiles
            }

        common = dict(time_bucket_size=5.0, start_time_step=10.0, max_tasks_per_trip=1, time_limit=5.0)
        permutation_profiles, *_ = _generate_negative_sortie_profiles(
            data,
            duals,
            base_reduced_cost=0.0,
            config=JourneyPricingConfig(**common, profile_labeling_enabled=False),
            trip_cache={},
            started=0.0,
            deadline=None,
        )
        label_profiles, *_ = _generate_negative_sortie_profiles(
            data,
            duals,
            base_reduced_cost=0.0,
            config=JourneyPricingConfig(**common, profile_labeling_enabled=True),
            trip_cache={},
            started=0.0,
            deadline=None,
        )
        self.assertEqual(profile_keys(label_profiles), profile_keys(permutation_profiles))

    def test_journey_profile_catalog_reuses_feasibility_with_changed_duals(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))
        cache: dict[tuple, tuple] = {}
        first = price_journeys(
            data,
            duals=JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=JourneyPricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=1,
                time_limit=5.0,
                max_candidate_trips=0,
                max_dp_states=1000,
                profile_catalog_enabled=True,
            ),
            trip_cache=cache,
        )
        self.assertTrue(first.exhausted)
        self.assertFalse(first.profile_catalog_hit)
        self.assertGreater(first.profile_catalog_size, 0)

        second = price_journeys(
            data,
            duals=JourneyDuals(cover={1: 200.0}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=JourneyPricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=1,
                time_limit=5.0,
                max_candidate_trips=0,
                max_dp_states=1000,
                profile_catalog_enabled=True,
            ),
            trip_cache=cache,
        )
        self.assertTrue(second.profile_catalog_hit)
        self.assertEqual(second.profile_catalog_size, first.profile_catalog_size)
        self.assertEqual(len(second.journeys), 1)
        self.assertLess(second.best_reduced_cost, 0.0)

    def test_resumable_sortie_profile_catalog_continues_without_duplicates(self):
        data = load_future_data("very_small")
        cache: dict[tuple, tuple] = {}
        state = _SortieProfileCatalogState(profiles=[], keys=set())
        first_config = JourneyPricingConfig(
            time_bucket_size=20.0,
            start_time_step=20.0,
            max_tasks_per_trip=2,
            max_sequences=1,
            profile_catalog_max_profiles=10000,
        )
        _resume_sortie_profile_catalog(
            data,
            first_config,
            cache,
            state,
            deadline=None,
            max_tasks=2,
            task_order=tuple(int(task) for task in data.tasks),
        )
        self.assertFalse(state.exhausted)
        self.assertEqual(state.reason, "sequence_budget")
        self.assertGreater(len(state.profiles), 0)
        first_size = len(state.profiles)
        second_config = JourneyPricingConfig(
            time_bucket_size=20.0,
            start_time_step=20.0,
            max_tasks_per_trip=2,
            max_sequences=100,
            profile_catalog_max_profiles=10000,
        )
        _resume_sortie_profile_catalog(
            data,
            second_config,
            cache,
            state,
            deadline=None,
            max_tasks=2,
            task_order=tuple(int(task) for task in data.tasks),
        )
        self.assertTrue(state.exhausted)
        self.assertGreater(len(state.profiles), first_size)
        self.assertEqual(len(state.profiles), len(state.keys))

    def test_resumable_sortie_label_state_requeues_partial_expansion(self):
        data = load_future_data("very_small")
        duals = FutureDuals(
            cover={int(task): 0.0 for task in data.tasks},
            task_vehicle={},
            sortie_count={int(data.vehicles[0]): 0.0},
            time_occupation={},
            ordering={},
            branches={},
            cuts={},
        )
        task_order = tuple(int(task) for task in data.tasks)
        task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
        partial_config = JourneyPricingConfig(
            time_bucket_size=20.0,
            start_time_step=20.0,
            max_tasks_per_trip=2,
            max_sequences=1,
            max_candidate_trips=0,
            max_timed_evaluations=0,
        )
        state = _initial_sortie_label_resume_state(data, duals)
        _advance_sortie_label_resume_state(
            data,
            duals,
            state,
            config=partial_config,
            deadline=None,
            task_order=task_order,
            threshold=1.0e9,
            task_to_bit=task_to_bit,
            max_tasks=2,
        )
        self.assertFalse(state.exhausted)
        self.assertEqual(state.reason, "label_budget")
        self.assertGreater(len(state.heap), 0)

        complete_config = replace(partial_config, max_sequences=10000)
        _advance_sortie_label_resume_state(
            data,
            duals,
            state,
            config=complete_config,
            deadline=None,
            task_order=task_order,
            threshold=1.0e9,
            task_to_bit=task_to_bit,
            max_tasks=2,
        )
        self.assertTrue(state.exhausted)
        self.assertEqual(state.reason, "")

        reference = _initial_sortie_label_resume_state(data, duals)
        _advance_sortie_label_resume_state(
            data,
            duals,
            reference,
            config=complete_config,
            deadline=None,
            task_order=task_order,
            threshold=1.0e9,
            task_to_bit=task_to_bit,
            max_tasks=2,
        )
        self.assertTrue(reference.exhausted)
        self.assertEqual(set(state.profiles_by_key), set(reference.profiles_by_key))

    def test_label_generator_keeps_superset_expansion_when_singleton_not_negative(self):
        data = load_future_data(
            "BPC_future/data/generated/moon_trek_60/logical_graphs/"
            "tranquillitatis_balmer_like_20km/tasks_05/"
            "tranquillitatis_balmer_like_20km_tasks05_01_seed6000_logical_graph.json"
        )
        first, second = int(data.tasks[0]), int(data.tasks[1])
        duals = FutureDuals(
            cover={int(task): 0.0 for task in data.tasks},
            task_vehicle={},
            sortie_count={int(data.vehicles[0]): 0.0},
            time_occupation={},
            ordering={},
            branches={},
            cuts={},
        )
        # The first task alone has no dual reward, but the two-task superset
        # does.  A singleton-level lower-bound prune would incorrectly stop
        # expansion before the negative superset can be reached.
        duals.cover[first] = 0.0
        duals.cover[second] = 500.0
        task_order = (first, second)
        task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
        config = JourneyPricingConfig(
            time_bucket_size=20.0,
            start_time_step=20.0,
            max_tasks_per_trip=2,
            profile_labeling_best_first_enabled=True,
            profile_labeling_task_set_superset_pruning_enabled=True,
            partial_profile_bound_pruning_enabled=True,
            max_sequences=1000,
            max_candidate_trips=0,
            max_timed_evaluations=0,
        )
        profiles, generated, evaluated, best_rc, exhausted, reason = _generate_negative_sortie_profiles_by_best_first_labels(
            data,
            duals,
            config=config,
            deadline=None,
            task_order=task_order,
            threshold=0.0,
            task_to_bit=task_to_bit,
        )
        self.assertTrue(exhausted, reason)
        self.assertGreater(generated, 0)
        self.assertGreater(evaluated, 0)
        self.assertIsNotNone(best_rc)
        self.assertTrue(any(len(profile.sequence) == 2 for profile in profiles))

    def test_partial_profile_bound_prunes_when_no_completion_can_be_negative(self):
        data = load_future_data(
            "BPC_future/data/generated/moon_trek_60/logical_graphs/"
            "tranquillitatis_balmer_like_20km/tasks_05/"
            "tranquillitatis_balmer_like_20km_tasks05_01_seed6000_logical_graph.json"
        )
        duals = FutureDuals(
            cover={int(task): 0.0 for task in data.tasks},
            task_vehicle={},
            sortie_count={int(data.vehicles[0]): 0.0},
            time_occupation={},
            ordering={},
            branches={},
            cuts={},
        )
        task_order = tuple(int(task) for task in data.tasks[:2])
        task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
        stats: dict[str, int] = {}
        profiles, generated, evaluated, best_rc, exhausted, reason = _generate_negative_sortie_profiles_by_best_first_labels(
            data,
            duals,
            config=JourneyPricingConfig(
                time_bucket_size=20.0,
                start_time_step=20.0,
                max_tasks_per_trip=2,
                profile_labeling_best_first_enabled=True,
                partial_profile_bound_pruning_enabled=True,
                max_sequences=1000,
                max_candidate_trips=0,
                max_timed_evaluations=0,
            ),
            deadline=None,
            task_order=task_order,
            threshold=0.0,
            task_to_bit=task_to_bit,
            catalog_stats=stats,
        )
        self.assertTrue(exhausted, reason)
        self.assertGreater(generated, 0)
        self.assertEqual(evaluated, 0)
        self.assertEqual(profiles, [])
        self.assertIsNone(best_rc)
        self.assertGreater(stats.get("partial_profile_bound_pruned_labels", 0), 0)

    def test_label_superset_bound_prunes_when_no_superset_can_be_negative(self):
        data = load_future_data(
            "BPC_future/data/generated/moon_trek_60/logical_graphs/"
            "tranquillitatis_balmer_like_20km/tasks_05/"
            "tranquillitatis_balmer_like_20km_tasks05_01_seed6000_logical_graph.json"
        )
        duals = FutureDuals(
            cover={int(task): 0.0 for task in data.tasks},
            task_vehicle={},
            sortie_count={int(data.vehicles[0]): 0.0},
            time_occupation={},
            ordering={},
            branches={},
            cuts={},
        )
        task_order = tuple(int(task) for task in data.tasks[:2])
        task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
        stats: dict[str, int] = {}
        profiles, generated, evaluated, best_rc, exhausted, reason = _generate_negative_sortie_profiles_by_best_first_labels(
            data,
            duals,
            config=JourneyPricingConfig(
                time_bucket_size=20.0,
                start_time_step=20.0,
                max_tasks_per_trip=2,
                profile_labeling_best_first_enabled=True,
                profile_labeling_task_set_superset_pruning_enabled=True,
                max_sequences=1000,
                max_candidate_trips=0,
                max_timed_evaluations=0,
            ),
            deadline=None,
            task_order=task_order,
            threshold=0.0,
            task_to_bit=task_to_bit,
            catalog_stats=stats,
        )
        self.assertTrue(exhausted, reason)
        self.assertEqual(profiles, [])
        self.assertEqual(generated, 0)
        self.assertEqual(evaluated, 0)
        self.assertIsNone(best_rc)
        self.assertGreater(stats.get("task_set_bound_pruned_sequences", 0), 0)

    def test_label_physical_catalog_reuses_across_duals(self):
        data = load_future_data(
            "BPC_future/data/generated/moon_trek_60/logical_graphs/"
            "tranquillitatis_balmer_like_20km/tasks_05/"
            "tranquillitatis_balmer_like_20km_tasks05_01_seed6000_logical_graph.json"
        )
        cache: dict[tuple, object] = {}
        config = JourneyPricingConfig(
            time_limit=5.0,
            max_tasks_per_trip=3,
            start_time_step=10.0,
            profile_labeling_enabled=True,
            profile_labeling_best_first_enabled=True,
            profile_labeling_physical_catalog_resume_enabled=True,
            early_return_negative=False,
            max_returned_journeys=10,
            max_sequences=0,
            max_candidate_trips=0,
            max_timed_evaluations=0,
        )
        first = price_journeys(
            data,
            duals=JourneyDuals(cover={int(task): 100.0 for task in data.tasks}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=config,
            trip_cache=cache,
        )
        self.assertFalse(first.profile_catalog_hit)
        self.assertTrue(first.exhausted)
        self.assertGreater(first.profile_catalog_size, 0)
        self.assertGreater(first.generated_sequences, 0)

        second = price_journeys(
            data,
            duals=JourneyDuals(cover={int(task): 90.0 for task in data.tasks}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=config,
            trip_cache=cache,
        )
        self.assertTrue(second.profile_catalog_hit)
        self.assertTrue(second.exhausted)
        self.assertEqual(second.profile_catalog_size, first.profile_catalog_size)
        self.assertEqual(second.generated_sequences, 0)
        self.assertEqual(second.evaluated_timed_trips, 0)
        self.assertNotEqual(first.best_reduced_cost, second.best_reduced_cost)

    def test_label_physical_catalog_respects_profile_budget(self):
        data = load_future_data(
            "BPC_future/data/generated/moon_trek_60/logical_graphs/"
            "tranquillitatis_balmer_like_20km/tasks_05/"
            "tranquillitatis_balmer_like_20km_tasks05_01_seed6000_logical_graph.json"
        )
        config = JourneyPricingConfig(
            time_limit=5.0,
            max_tasks_per_trip=3,
            start_time_step=10.0,
            profile_labeling_enabled=True,
            profile_labeling_best_first_enabled=True,
            profile_labeling_physical_catalog_resume_enabled=True,
            profile_catalog_max_profiles=1,
            max_sequences=0,
            max_candidate_trips=0,
            max_timed_evaluations=0,
        )
        result = price_journeys(
            data,
            duals=JourneyDuals(cover={int(task): 0.0 for task in data.tasks}, fleet_limit=0.0),
            branch_constraints=tuple(),
            config=config,
            trip_cache={},
        )
        self.assertFalse(result.exhausted)
        self.assertEqual(result.reason, "profile_catalog_budget")
        self.assertGreater(result.profile_catalog_size, 1)

    def test_task_set_profile_lower_bound_skips_arc_expansion(self):
        data = load_future_data("very_small")
        vehicle = int(data.vehicles[0])
        duals = FutureDuals(
            cover={int(task): 0.0 for task in data.tasks},
            task_vehicle={},
            sortie_count={vehicle: 0.0},
            time_occupation={},
            ordering={},
            branches={},
        )
        task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
        first_mask = 1 << task_to_bit[int(data.tasks[0])]
        bound_cache = _TaskSetReducedCostLowerBoundCache(data, duals, vehicle, task_to_bit)
        self.assertGreater(bound_cache.value(first_mask), 0.0)

        stats: dict[str, int] = {}
        with patch(
            "BPC_future.pricing.journey_pricing._optimized_arc_profiles_for_sequence",
            side_effect=AssertionError("task-set bound should prune before arc-profile expansion"),
        ):
            profiles, generated, evaluated, best_rc, exhausted, reason, _cut_pruned = _generate_negative_sortie_profiles(
                data,
                duals,
                base_reduced_cost=0.0,
                config=JourneyPricingConfig(
                    time_bucket_size=5.0,
                    max_tasks_per_trip=2,
                    task_set_bound_pruning_enabled=True,
                    eps=1.0e-6,
                ),
                trip_cache={},
                started=0.0,
                deadline=None,
                catalog_stats=stats,
            )
        self.assertTrue(exhausted)
        self.assertEqual(reason, "")
        self.assertEqual(profiles, [])
        self.assertEqual(generated, 0)
        self.assertEqual(evaluated, 0)
        self.assertIsNone(best_rc)
        self.assertGreater(stats.get("task_set_bound_pruned_sequences", 0), 0)

    def test_initial_savings_seed_adds_feasible_multi_task_trip(self):
        data = load_future_data("very_small")
        pool = TripPool()
        added = _seed_initial_savings_trips(
            data,
            {
                "initial_savings_seed_enabled": True,
                "initial_savings_seed_max_tasks": 2,
                "initial_savings_seed_max_evaluations": 100,
                "initial_savings_seed_max_trips": 20,
                "initial_savings_seed_path_combinations": 0,
                "initial_savings_seed_path_dominance_enabled": True,
                "pricing_eps": 1.0e-6,
            },
            pool,
            5.0,
        )
        self.assertGreater(added, 0)
        self.assertTrue(any(len(trip.task_set) >= 2 for trip in pool.trips))
        self.assertTrue(all(trip.cost > 0.0 and trip.end_time >= trip.start_time for trip in pool.trips))

    def test_journey_dual_diagnostic_hash_changes_with_duals(self):
        data = load_future_data("very_small")
        left = JourneyDuals(cover={int(task): float(task) for task in data.tasks}, fleet_limit=1.0, cuts={0: 0.5})
        right = JourneyDuals(cover={int(task): float(task) for task in data.tasks}, fleet_limit=2.0, cuts={0: 0.5})
        self.assertNotEqual(
            _journey_dual_hash(_journey_dual_vector(data, left, 1)),
            _journey_dual_hash(_journey_dual_vector(data, right, 1)),
        )

    def test_hidden_negative_audit_reduced_cost_components_match_manual_rc(self):
        journey = JourneyColumn(
            id=0,
            trips=tuple(),
            task_set=frozenset({1, 2, 3}),
            start_time=0.0,
            end_time=1.0,
            travel_cost=100.0,
            fixed_vehicle_cost=0.0,
            cost=100.0,
            signature=("audit-components",),
        )
        cuts = (SubsetRowCut(tasks=(1, 2, 4), k=2), FleetLowerBoundCut(lb=1))
        duals = JourneyDuals(cover={1: 5.0, 2: 7.0, 3: -2.0}, fleet_limit=4.0, cuts={0: 3.0, 1: 2.0})
        components = _journey_reduced_cost_components(journey, duals, cuts)
        self.assertAlmostEqual(components["journey_cost"], 100.0)
        self.assertAlmostEqual(components["cover_dual_sum"], 10.0)
        self.assertAlmostEqual(components["fleet_dual"], 4.0)
        self.assertAlmostEqual(components["cut_dual_sum"], 5.0)
        self.assertAlmostEqual(components["manual_true_reduced_cost"], manual_journey_reduced_cost(journey, duals, cuts))
        self.assertAlmostEqual(components["decomposed_true_reduced_cost"], 81.0)
        self.assertAlmostEqual(components["decomposition_abs_error"], 0.0)
        self.assertNotEqual(_journey_cut_hash(cuts), _journey_cut_hash((SubsetRowCut(tasks=(1, 3, 4), k=2), cuts[1])))

    def test_hidden_negative_audit_limits_detailed_journey_logs(self):
        data = load_future_data("very_small")
        journeys = [
            JourneyColumn(
                id=index,
                trips=tuple(),
                task_set=frozenset({int(data.tasks[index % len(data.tasks)])}),
                start_time=0.0,
                end_time=1.0,
                travel_cost=float(index),
                fixed_vehicle_cost=0.0,
                cost=float(index),
                signature=("audit-limit", index),
            )
            for index in range(10)
        ]
        ordinary = JourneyPricingResult(
            journeys=[],
            exhausted=True,
            best_reduced_cost=0.0,
            generated_sequences=0,
            evaluated_timed_trips=0,
            candidate_trips=0,
            selected_trips=0,
            status="OPTIMAL",
            reason="no_negative_journey",
        )
        hidden = JourneyPricingResult(
            journeys=journeys,
            exhausted=False,
            best_reduced_cost=-1.0,
            generated_sequences=0,
            evaluated_timed_trips=0,
            candidate_trips=0,
            selected_trips=0,
            status="INCOMPLETE",
            reason="time_limit",
        )
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "audit.jsonl"
            logger = FutureLogger(log_path, console=False)
            try:
                _log_hidden_negative_audit(
                    logger,
                    data,
                    JourneyPool(),
                    ordinary,
                    hidden,
                    JourneyDuals(cover={int(task): 0.0 for task in data.tasks}, fleet_limit=0.0, cuts={}),
                    tuple(),
                    tuple(),
                    cg_iter=7,
                    hidden_pricing_kind="test_hidden",
                    hidden_dual_source="true_dual",
                    max_logged_journeys=3,
                )
            finally:
                logger.close()

            records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]

        detailed = [record for record in records if record["event"] == "journey_hidden_negative_audit"]
        summaries = [record for record in records if record["event"] == "journey_hidden_negative_audit_summary"]
        reason_summaries = [
            record for record in records if record["event"] == "journey_hidden_negative_audit_reason_summary"
        ]
        self.assertEqual(len(detailed), 3)
        self.assertEqual([record["CB_journey_rank"] for record in detailed], [0, 1, 2])
        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0]["hidden_negative_audit_candidate_count"], 10)
        self.assertEqual(summaries[0]["hidden_negative_audit_logged_count"], 3)
        self.assertEqual(summaries[0]["hidden_negative_audit_skipped_count"], 7)
        self.assertEqual(len(reason_summaries), 1)
        self.assertEqual(reason_summaries[0]["hidden_negative_audit_candidate_count"], 10)
        self.assertEqual(reason_summaries[0]["hidden_negative_primary_reason_counts"]["not_generated"], 10)
        self.assertEqual(
            reason_summaries[0]["hidden_negative_candidate_reason_counts"][
                "worker_profile_universe_missing_hidden_task_set"
            ],
            10,
        )

        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "audit_disabled.jsonl"
            logger = FutureLogger(log_path, console=False)
            try:
                _log_hidden_negative_audit(
                    logger,
                    data,
                    JourneyPool(),
                    ordinary,
                    hidden,
                    JourneyDuals(cover={int(task): 0.0 for task in data.tasks}, fleet_limit=0.0, cuts={}),
                    tuple(),
                    tuple(),
                    cg_iter=7,
                    hidden_pricing_kind="test_hidden",
                    hidden_dual_source="true_dual",
                    max_logged_journeys=0,
                )
            finally:
                logger.close()
            self.assertEqual(log_path.read_text(encoding="utf-8"), "")

    def test_profile_mask_diagnostics_default_to_empty(self):
        profile = _SortieProfile(
            sequence=(1,),
            arc_options=tuple(),
            lower_start=0.0,
            upper_start=10.0,
            end_offset=1.0,
            cost=1.0,
            mask=1,
            contribution=-1.0,
        )
        disabled = _profile_mask_diagnostic_kwargs(
            [profile],
            {"reachable_task_masks": frozenset({1})},
            JourneyPricingConfig(),
        )
        self.assertEqual(disabled["diagnostic_profile_task_masks"], frozenset())
        self.assertEqual(disabled["diagnostic_reachable_task_masks"], frozenset())

        enabled = _profile_mask_diagnostic_kwargs(
            [profile],
            {"reachable_task_masks": frozenset({1})},
            JourneyPricingConfig(profile_mask_diagnostics_enabled=True),
        )
        self.assertEqual(enabled["diagnostic_profile_task_masks"], frozenset({1}))
        self.assertEqual(enabled["diagnostic_reachable_task_masks"], frozenset({1}))

    def test_hidden_negative_miss_diagnostics_summarizes_worker_pruning_signals(self):
        ordinary = JourneyPricingResult(
            journeys=[],
            exhausted=True,
            best_reduced_cost=0.0,
            generated_sequences=12,
            evaluated_timed_trips=0,
            candidate_trips=0,
            selected_trips=0,
            status="OPTIMAL",
            reason="no_negative_journey",
            profile_dominance_pruned=3,
            existing_journeys_filtered=1,
            task_set_resource_pruned_sequences=5,
            dp_bound_pruned_labels=7,
            dp_cross_count_pruned_labels=11,
            profile_catalog_hit=True,
            profile_negative_candidate_count=2,
        )
        diagnostics = _hidden_negative_miss_diagnostics(
            ordinary,
            signature_duplicate=True,
            forbidden_signature_hit=False,
            task_set_dominated=True,
            reduced_cost_components={"decomposition_abs_error": 0.0},
        )
        candidates = diagnostics["hidden_negative_miss_reason_candidates"]
        self.assertEqual(diagnostics["hidden_negative_miss_reason_primary"], "duplicate_signature_filter")
        self.assertIn("dominant_task_set_filter", candidates)
        self.assertIn("worker_existing_journey_filter", candidates)
        self.assertIn("task_set_resource_pruning", candidates)
        self.assertIn("dp_bound_pruning", candidates)
        self.assertIn("profile_dominance_pruning", candidates)
        self.assertIn("profile_cross_count_dominance", candidates)
        self.assertIn("profile_catalog_reuse", candidates)
        self.assertIn("generated_negative_candidate_but_not_returned", candidates)
        self.assertIn("worker_local_no_column_universe_gap", candidates)

    def test_hidden_negative_miss_diagnostics_flags_not_generated_and_rc_mismatch(self):
        ordinary = JourneyPricingResult(
            journeys=[],
            exhausted=False,
            best_reduced_cost=None,
            generated_sequences=0,
            evaluated_timed_trips=0,
            candidate_trips=0,
            selected_trips=0,
            status="INCOMPLETE",
            reason="profile_dp_incomplete",
        )
        diagnostics = _hidden_negative_miss_diagnostics(
            ordinary,
            signature_duplicate=False,
            forbidden_signature_hit=False,
            task_set_dominated=False,
            reduced_cost_components={"decomposition_abs_error": 1.0e-4},
        )
        candidates = diagnostics["hidden_negative_miss_reason_candidates"]
        self.assertEqual(diagnostics["hidden_negative_miss_reason_primary"], "worker_incomplete_limit")
        self.assertIn("not_generated", candidates)
        self.assertIn("reduced_cost_decomposition_mismatch", candidates)

    def test_hidden_negative_miss_diagnostics_flags_worker_time_limit_gap(self):
        ordinary = JourneyPricingResult(
            journeys=[],
            exhausted=False,
            best_reduced_cost=None,
            generated_sequences=120,
            evaluated_timed_trips=80,
            candidate_trips=15,
            selected_trips=0,
            status="INCOMPLETE",
            reason="time_limit",
        )
        diagnostics = _hidden_negative_miss_diagnostics(
            ordinary,
            signature_duplicate=False,
            forbidden_signature_hit=False,
            task_set_dominated=False,
            reduced_cost_components={"decomposition_abs_error": 0.0},
        )
        candidates = diagnostics["hidden_negative_miss_reason_candidates"]
        self.assertEqual(diagnostics["hidden_negative_miss_reason_primary"], "worker_incomplete_time_limit")
        self.assertIn("worker_universe_no_true_rc_negative_candidate", candidates)
        self.assertNotIn("unknown_worker_gap", candidates)

    def test_hidden_negative_miss_diagnostics_prefers_hidden_mask_specific_reason(self):
        ordinary = JourneyPricingResult(
            journeys=[],
            exhausted=True,
            best_reduced_cost=0.0,
            generated_sequences=25,
            evaluated_timed_trips=20,
            candidate_trips=10,
            selected_trips=0,
            status="OPTIMAL",
            reason="no_negative_journey",
            weak_negative_journeys_filtered=4,
            dp_cross_count_pruned_labels=9,
            diagnostic_profile_task_masks=frozenset({1, 2, 3}),
            diagnostic_profile_trip_masks=frozenset({1, 2}),
            diagnostic_reachable_task_masks=frozenset({3}),
            diagnostic_negative_task_masks=frozenset(),
            diagnostic_selected_task_masks=frozenset(),
        )
        diagnostics = _hidden_negative_miss_diagnostics(
            ordinary,
            signature_duplicate=False,
            forbidden_signature_hit=False,
            task_set_dominated=False,
            reduced_cost_components={"decomposition_abs_error": 0.0},
            hidden_task_mask=3,
            hidden_trip_masks=(1, 2),
        )
        candidates = diagnostics["hidden_negative_miss_reason_candidates"]
        self.assertEqual(
            diagnostics["hidden_negative_miss_reason_primary"],
            "worker_reached_hidden_task_set_without_negative_candidate",
        )
        self.assertIn("worker_true_rc_threshold_filter", candidates)
        self.assertIn("profile_cross_count_dominance", candidates)
        self.assertIn("worker_profile_universe_has_hidden_sortie_masks", candidates)

    def test_journey_exact_pricing_budget_uses_reserve_until_certificate_candidate(self):
        budget, reserve, reason = _journey_exact_pricing_budget(
            remaining=10.0,
            post_pricing_reserve=2.0,
            min_pricing_time=0.1,
            incumbent=200.0,
            rmp_objective=180.0,
            integer_tol=1.0e-6,
        )
        self.assertAlmostEqual(budget, 8.0)
        self.assertAlmostEqual(reserve, 2.0)
        self.assertEqual(reason, "post_pricing_reserve")
        budget, reserve, reason = _journey_exact_pricing_budget(
            remaining=10.0,
            post_pricing_reserve=2.0,
            min_pricing_time=0.1,
            incumbent=200.0,
            rmp_objective=200.0,
            integer_tol=1.0e-6,
            cg_iter=2,
            certificate_no_reserve_enabled=True,
            certificate_no_reserve_min_cg_iter=3,
        )
        self.assertAlmostEqual(budget, 8.0)
        self.assertAlmostEqual(reserve, 2.0)
        self.assertEqual(reason, "post_pricing_reserve")
        budget, reserve, reason = _journey_exact_pricing_budget(
            remaining=10.0,
            post_pricing_reserve=2.0,
            min_pricing_time=0.1,
            incumbent=200.0,
            rmp_objective=200.0,
            integer_tol=1.0e-6,
            cg_iter=3,
            certificate_no_reserve_enabled=True,
            certificate_no_reserve_min_cg_iter=3,
        )
        self.assertAlmostEqual(budget, 10.0)
        self.assertAlmostEqual(reserve, 0.0)
        self.assertEqual(reason, "certificate_candidate_no_reserve")
        budget, reserve, reason = _journey_exact_pricing_budget(
            remaining=10.0,
            post_pricing_reserve=2.0,
            min_pricing_time=0.1,
            incumbent=200.0,
            rmp_objective=200.0,
            integer_tol=1.0e-6,
            cg_iter=3,
            certificate_no_reserve_enabled=True,
            certificate_no_reserve_min_cg_iter=3,
            deadline_safety_margin=1.0,
        )
        self.assertAlmostEqual(budget, 9.0)
        self.assertAlmostEqual(reserve, 0.0)
        self.assertEqual(reason, "certificate_candidate_no_reserve")

    def test_profile_materialization_failure_skip_is_opt_in(self):
        pricing = SimpleNamespace(reason="selected_profiles_not_a_valid_journey")
        self.assertFalse(
            _journey_skip_ordinary_retry_after_profile_materialization_failure(
                {},
                pricing,
            )
        )
        self.assertTrue(
            _journey_skip_ordinary_retry_after_profile_materialization_failure(
                {"journey_skip_ordinary_retry_after_profile_materialization_failure": True},
                pricing,
            )
        )
        self.assertFalse(
            _journey_skip_ordinary_retry_after_profile_materialization_failure(
                {},
                SimpleNamespace(reason="time_limit"),
            )
        )
        duplicate_only = SimpleNamespace(
            reason="negative_journeys_already_in_pool",
            existing_journeys_filtered=1,
            duplicate_candidates_filtered=0,
            dominated_task_set_journeys_filtered=0,
            duplicate_scan_limited=False,
        )
        self.assertFalse(
            _journey_skip_ordinary_retry_after_profile_materialization_failure(
                {},
                duplicate_only,
            )
        )
        self.assertFalse(
            _journey_skip_ordinary_retry_after_profile_materialization_failure(
                {"journey_skip_ordinary_retry_after_profile_materialization_failure": True},
                duplicate_only,
            )
        )
        self.assertTrue(
            _journey_skip_ordinary_retry_after_profile_materialization_failure(
                {"journey_skip_ordinary_retry_after_duplicate_only": True},
                duplicate_only,
            )
        )
        self.assertFalse(
            _journey_skip_ordinary_retry_after_profile_materialization_failure(
                {"journey_skip_ordinary_retry_after_duplicate_only": True},
                SimpleNamespace(
                    reason="negative_journeys_already_in_pool",
                    existing_journeys_filtered=1,
                    duplicate_candidates_filtered=0,
                    dominated_task_set_journeys_filtered=0,
                    duplicate_scan_limited=True,
                ),
            )
        )

    def test_weak_negative_filtered_retry_skip_is_opt_in_and_column_free(self):
        weak_filtered = SimpleNamespace(weak_negative_journeys_filtered=2, journeys=[])
        self.assertFalse(_journey_skip_ordinary_retry_after_weak_negative_filtered({}, weak_filtered))
        self.assertTrue(
            _journey_skip_ordinary_retry_after_weak_negative_filtered(
                {"journey_skip_ordinary_retry_after_weak_negative_filtered": True},
                weak_filtered,
            )
        )
        self.assertFalse(
            _journey_skip_ordinary_retry_after_weak_negative_filtered(
                {"journey_skip_ordinary_retry_after_weak_negative_filtered": True},
                SimpleNamespace(weak_negative_journeys_filtered=0, journeys=[]),
            )
        )
        self.assertFalse(
            _journey_skip_ordinary_retry_after_weak_negative_filtered(
                {"journey_skip_ordinary_retry_after_weak_negative_filtered": True},
                SimpleNamespace(weak_negative_journeys_filtered=2, journeys=[object()]),
            )
        )

    def test_journey_skip_short_exact_pricing_gate_is_conservative(self):
        config = {
            "journey_skip_short_exact_after_retry_negative_enabled": True,
            "journey_skip_short_exact_min_retry_negative_rounds": 2,
            "journey_skip_short_exact_min_cg_iter": 4,
        }
        self.assertFalse(
            _journey_should_skip_short_exact_pricing(
                {},
                depth=0,
                cg_iter=4,
                certificate_candidate=True,
                retry_negative_after_no_column_rounds=2,
            )
        )
        self.assertFalse(
            _journey_should_skip_short_exact_pricing(
                config,
                depth=1,
                cg_iter=4,
                certificate_candidate=True,
                retry_negative_after_no_column_rounds=2,
            )
        )
        self.assertFalse(
            _journey_should_skip_short_exact_pricing(
                config,
                depth=0,
                cg_iter=4,
                certificate_candidate=False,
                retry_negative_after_no_column_rounds=2,
            )
        )
        self.assertFalse(
            _journey_should_skip_short_exact_pricing(
                config,
                depth=0,
                cg_iter=3,
                certificate_candidate=True,
                retry_negative_after_no_column_rounds=2,
            )
        )
        self.assertFalse(
            _journey_should_skip_short_exact_pricing(
                config,
                depth=0,
                cg_iter=4,
                certificate_candidate=True,
                retry_negative_after_no_column_rounds=1,
            )
        )
        self.assertTrue(
            _journey_should_skip_short_exact_pricing(
                config,
                depth=0,
                cg_iter=4,
                certificate_candidate=True,
                retry_negative_after_no_column_rounds=2,
            )
        )

    def test_journey_flat_weak_column_pressure_is_conservative(self):
        enabled = {
            "journey_certificate_flat_weak_column_pressure_enabled": True,
            "journey_certificate_flat_weak_column_min_flat_rounds": 1,
            "journey_certificate_flat_weak_column_max_added_journeys": 4,
        }
        self.assertFalse(
            _journey_flat_weak_column_pressure_addition(
                {},
                1,
                certificate_candidate=True,
                certificate_flat_rounds=1,
                objective_delta=0.0,
                eps=1.0e-6,
            )
        )
        self.assertFalse(
            _journey_flat_weak_column_pressure_addition(
                enabled,
                1,
                certificate_candidate=False,
                certificate_flat_rounds=1,
                objective_delta=0.0,
                eps=1.0e-6,
            )
        )
        self.assertFalse(
            _journey_flat_weak_column_pressure_addition(
                enabled,
                1,
                certificate_candidate=True,
                certificate_flat_rounds=0,
                objective_delta=0.0,
                eps=1.0e-6,
            )
        )
        self.assertFalse(
            _journey_flat_weak_column_pressure_addition(
                enabled,
                1,
                certificate_candidate=True,
                certificate_flat_rounds=1,
                objective_delta=-0.01,
                eps=1.0e-6,
            )
        )
        self.assertFalse(
            _journey_flat_weak_column_pressure_addition(
                enabled,
                5,
                certificate_candidate=True,
                certificate_flat_rounds=1,
                objective_delta=0.0,
                eps=1.0e-6,
            )
        )
        self.assertTrue(
            _journey_flat_weak_column_pressure_addition(
                enabled,
                2,
                certificate_candidate=True,
                certificate_flat_rounds=1,
                objective_delta=0.0,
                eps=1.0e-6,
            )
        )

    def test_journey_flat_weak_heuristic_fallthrough_gate(self):
        config = {
            "journey_certificate_flat_weak_column_continue_exact_after_heuristic": True,
            "journey_certificate_flat_weak_column_continue_exact_after_heuristic_rounds": 2,
        }
        self.assertFalse(
            _journey_continue_exact_after_flat_weak_heuristic(
                {},
                flat_weak_column_rounds=10,
            )
        )
        self.assertFalse(
            _journey_continue_exact_after_flat_weak_heuristic(
                config,
                flat_weak_column_rounds=1,
            )
        )
        self.assertTrue(
            _journey_continue_exact_after_flat_weak_heuristic(
                config,
                flat_weak_column_rounds=2,
            )
        )

    def test_journey_immediate_certificate_no_reserve_config_is_opt_in(self):
        pricing_config = JourneyPricingConfig(time_limit=4.0, profile_generation_time_fraction=0.9)
        unchanged, enabled = _journey_immediate_certificate_no_reserve_config(
            {},
            pricing_config,
            certificate_candidate=True,
            budget_reason="certificate_candidate_no_reserve",
            exact_budget=20.0,
        )
        self.assertFalse(enabled)
        self.assertEqual(unchanged.time_limit, 4.0)

        updated, enabled = _journey_immediate_certificate_no_reserve_config(
            {
                "journey_certificate_immediate_no_reserve_enabled": True,
                "journey_retry_incomplete_no_column_generation_fraction": 0.95,
            },
            pricing_config,
            certificate_candidate=True,
            budget_reason="certificate_candidate_no_reserve",
            exact_budget=20.0,
        )
        self.assertTrue(enabled)
        self.assertEqual(updated.time_limit, 20.0)
        self.assertAlmostEqual(updated.profile_generation_time_fraction, 0.95)

    def test_journey_learning_defaults_are_conservative_but_overridable(self):
        self.assertEqual(_journey_learning_pricing_max_rounds({}), 1)
        self.assertEqual(_journey_learning_true_rc_max_kept_per_round({}), 4)
        self.assertAlmostEqual(_journey_learning_true_rc_keep_threshold({}), 0.0)
        self.assertTrue(_journey_learning_filter_true_rc_enabled({}))
        self.assertFalse(_journey_learning_filter_true_rc_enabled({"journey_learning_filter_true_rc": False}))
        self.assertTrue(_journey_learning_certificate_gate_disabled({}, certificate_candidate=True))
        self.assertFalse(_journey_learning_certificate_gate_disabled({}, certificate_candidate=False))
        self.assertFalse(
            _journey_learning_certificate_gate_disabled(
                {"journey_learning_disable_on_certificate_candidate": False},
                certificate_candidate=True,
            )
        )
        self.assertEqual(_journey_learning_pricing_max_rounds({"journey_learning_pricing_max_rounds": 0}), 0)
        self.assertEqual(
            _journey_learning_true_rc_max_kept_per_round({"journey_learning_true_rc_max_kept_per_round": 0}),
            0,
        )
        self.assertEqual(_journey_learning_pricing_max_rounds({"journey_learning_pricing_max_rounds": 3}), 3)
        self.assertEqual(
            _journey_learning_true_rc_max_kept_per_round({"journey_learning_true_rc_max_kept_per_round": 9}),
            9,
        )
        self.assertAlmostEqual(
            _journey_learning_true_rc_keep_threshold({"journey_learning_true_rc_keep_threshold": 1.5}),
            1.5,
        )
        self.assertAlmostEqual(
            _journey_learning_certificate_true_rc_keep_threshold(
                {
                    "journey_learning_true_rc_keep_threshold": 0.25,
                    "journey_learning_certificate_true_rc_keep_threshold": 1.5,
                }
            ),
            1.5,
        )
        self.assertEqual(
            _journey_learning_certificate_true_rc_max_kept_per_round(
                {
                    "journey_learning_true_rc_max_kept_per_round": 4,
                    "journey_learning_certificate_true_rc_max_kept_per_round": 2,
                }
            ),
            2,
        )
        self.assertAlmostEqual(
            _journey_learning_certificate_true_rc_fallback_keep_threshold(
                {
                    "journey_learning_true_rc_fallback_keep_threshold": 0.0,
                    "journey_learning_certificate_true_rc_fallback_keep_threshold": 1.5,
                }
            ),
            1.5,
        )
        self.assertEqual(
            _journey_learning_certificate_true_rc_fallback_max_kept_per_round(
                {
                    "journey_learning_true_rc_fallback_max_kept_per_round": 1,
                    "journey_learning_certificate_true_rc_fallback_max_kept_per_round": 0,
                }
            ),
            0,
        )

    def test_journey_learning_filter_parameters_tighten_certificate_candidate_only(self):
        runtime = SimpleNamespace(
            true_rc_keep_threshold=0.0,
            true_rc_max_kept_per_round=4,
            true_rc_fallback_keep_threshold=0.0,
            true_rc_fallback_max_kept_per_round=1,
        )
        config = {
            "journey_learning_certificate_true_rc_keep_threshold": 1.0,
            "journey_learning_certificate_true_rc_max_kept_per_round": 2,
            "journey_learning_certificate_true_rc_fallback_keep_threshold": 1.0,
            "journey_learning_certificate_true_rc_fallback_max_kept_per_round": 0,
        }
        self.assertEqual(
            _journey_learning_true_rc_filter_parameters(config, runtime, certificate_candidate=False),
            (0.0, 4, 0.0, 1, "regular"),
        )
        self.assertEqual(
            _journey_learning_true_rc_filter_parameters(config, runtime, certificate_candidate=True),
            (1.0, 2, 1.0, 0, "certificate_candidate"),
        )

    def test_journey_learning_true_rc_filter_fills_strong_cap_with_weak_true_negatives(self):
        class CaptureLogger:
            def __init__(self):
                self.events = []

            def log(self, event, **payload):
                self.events.append({"event": event, **payload})

        journeys = [
            SimpleNamespace(signature=("strong",), task_set=(1,), cost=0.0),
            SimpleNamespace(signature=("weak-a",), task_set=(2,), cost=0.0),
            SimpleNamespace(signature=("weak-b",), task_set=(3,), cost=0.0),
            SimpleNamespace(signature=("positive",), task_set=(4,), cost=10.0),
        ]
        logger = CaptureLogger()
        kept = _journey_learning_true_rc_filter(
            logger,
            journeys,
            true_duals=JourneyDuals(cover={1: 20.0, 2: 5.0, 3: 4.0, 4: 1.0}, fleet_limit=0.0, cuts={}),
            cuts=tuple(),
            tol=1.0e-6,
            keep_threshold=10.0,
            max_kept=3,
            fallback_keep_threshold=0.0,
            fallback_max_kept=1,
            cg_iter=1,
            node_id=0,
            depth=0,
            pricing_kind="heuristic",
        )

        self.assertEqual([journey.signature for journey in kept], [("strong",), ("weak-a",), ("weak-b",)])
        event = logger.events[-1]
        self.assertEqual(event["strong_true_negative_journeys"], 1)
        self.assertEqual(event["fallback_fill_journeys"], 2)
        self.assertEqual(event["kept_journeys"], 3)

    def test_journey_learning_true_rc_filter_certificate_context_rejects_weak_fill(self):
        class CaptureLogger:
            def __init__(self):
                self.events = []

            def log(self, event, **payload):
                self.events.append({"event": event, **payload})

        journeys = [
            SimpleNamespace(signature=("strong",), task_set=(1,), cost=0.0),
            SimpleNamespace(signature=("weak-a",), task_set=(2,), cost=0.0),
            SimpleNamespace(signature=("weak-b",), task_set=(3,), cost=0.0),
        ]
        logger = CaptureLogger()
        kept = _journey_learning_true_rc_filter(
            logger,
            journeys,
            true_duals=JourneyDuals(cover={1: 20.0, 2: 0.5, 3: 0.25}, fleet_limit=0.0, cuts={}),
            cuts=tuple(),
            tol=1.0e-6,
            keep_threshold=1.0,
            max_kept=2,
            fallback_keep_threshold=1.0,
            fallback_max_kept=0,
            cg_iter=1,
            node_id=0,
            depth=0,
            pricing_kind="heuristic",
            filter_context="certificate_candidate",
        )

        self.assertEqual([journey.signature for journey in kept], [("strong",)])
        event = logger.events[-1]
        self.assertEqual(event["filter_context"], "certificate_candidate")
        self.assertEqual(event["strong_true_negative_journeys"], 1)
        self.assertEqual(event["true_negative_journeys"], 3)
        self.assertEqual(event["fallback_fill_journeys"], 0)
        self.assertEqual(event["kept_journeys"], 1)

    def test_journey_learning_runtime_for_pricing_honors_round_gate(self):
        runtime = SimpleNamespace(pricing_rounds_used=0)
        self.assertIs(
            _journey_learning_runtime_for_pricing(runtime, {"journey_learning_pricing_max_rounds": 1}, cg_iter=1, certificate_disabled=False),
            runtime,
        )
        self.assertIs(
            _journey_learning_runtime_for_pricing(runtime, {"journey_learning_pricing_max_rounds": 1}, cg_iter=20, certificate_disabled=False),
            runtime,
        )
        runtime.pricing_rounds_used = 1
        self.assertIsNone(
            _journey_learning_runtime_for_pricing(runtime, {"journey_learning_pricing_max_rounds": 1}, cg_iter=2, certificate_disabled=False)
        )
        runtime.pricing_rounds_used = 0
        self.assertIs(
            _journey_learning_runtime_for_pricing(runtime, {"journey_learning_pricing_max_rounds": 0}, cg_iter=10, certificate_disabled=False),
            runtime,
        )
        self.assertIsNone(
            _journey_learning_runtime_for_pricing(runtime, {"journey_learning_pricing_enabled": False}, cg_iter=1, certificate_disabled=False)
        )
        self.assertIsNone(
            _journey_learning_runtime_for_pricing(runtime, {"journey_learning_pricing_max_rounds": 0}, cg_iter=1, certificate_disabled=True)
        )

    def test_journey_learning_dual_center_blends_gnn_anchor_only_for_smoothed_pricing(self):
        class StubStabilizer:
            alpha = 0.5

            def update_alpha(self, _history, pricing_stats=None, branch_depth=0):
                return self.alpha

            def should_disable(self, branch_depth, certificate_mode=False):
                return False

            def smooth_task_duals(self, true_task_duals, predicted_anchor, alpha=None):
                active_alpha = self.alpha if alpha is None else float(alpha)
                return {
                    int(task): active_alpha * float(predicted_anchor[int(task)])
                    + (1.0 - active_alpha) * float(true_value)
                    for task, true_value in true_task_duals.items()
                }

        class CaptureLogger:
            def __init__(self):
                self.events = []

            def log(self, event, **payload):
                self.events.append({"event": event, **payload})

        runtime = _JourneyLearningRuntime(
            stabilizer=StubStabilizer(),
            anchor={1: 100.0, 2: 0.0},
            objective_history=[],
            filter_true_rc=True,
            true_rc_tol=1.0e-5,
            true_rc_keep_threshold=0.0,
            true_rc_fallback_keep_threshold=0.0,
            true_rc_fallback_max_kept_per_round=1,
            true_rc_max_kept_per_round=4,
            stop_after_no_strong_round=False,
            min_kept_to_continue=1,
            dual_center_enabled=True,
            dual_center_weight=0.5,
            dual_center_momentum=0.5,
            dual_center_min_rounds=2,
        )
        logger = CaptureLogger()
        true_duals_1 = JourneyDuals(cover={1: 10.0, 2: 20.0}, fleet_limit=0.0, cuts={})
        smoothed_1, source_1, active_1 = _journey_learning_pricing_duals(
            runtime,
            true_duals_1,
            rmp_objective=100.0,
            branch_depth=0,
            logger=logger,
            cg_iter=1,
            node_id=0,
            depth=0,
        )
        self.assertTrue(active_1)
        self.assertEqual(source_1, "learning_smoothed")
        self.assertEqual(smoothed_1.cover, {1: 55.0, 2: 10.0})
        self.assertEqual(logger.events[-1]["anchor_source"], "gnn_anchor_warming")

        true_duals_2 = JourneyDuals(cover={1: 20.0, 2: 40.0}, fleet_limit=0.0, cuts={})
        smoothed_2, _source_2, active_2 = _journey_learning_pricing_duals(
            runtime,
            true_duals_2,
            rmp_objective=100.0,
            branch_depth=0,
            logger=logger,
            cg_iter=2,
            node_id=0,
            depth=0,
        )
        self.assertTrue(active_2)
        self.assertEqual(logger.events[-1]["anchor_source"], "gnn_dual_center_anchor")
        self.assertTrue(logger.events[-1]["dual_center_active"])
        # EMA center is {1: 15, 2: 30}; effective anchor is {1: 57.5, 2: 15}.
        self.assertAlmostEqual(smoothed_2.cover[1], 38.75)
        self.assertAlmostEqual(smoothed_2.cover[2], 27.5)

    def test_journey_learning_pricing_config_has_separate_budget_overrides(self):
        base = JourneyPricingConfig(
            time_limit=5.0,
            max_returned_journeys=96,
            streaming_profile_batch_size=5000,
            streaming_min_negative_batch=64,
            streaming_min_returned_journeys=1,
            streaming_partial_return_after_time=0.0,
            streaming_partial_return_min_journeys=0,
            early_return_negative_min_count=64,
            profile_generation_time_fraction=1.0,
        )

        self.assertIs(_journey_learning_pricing_config({}, base), base)

        updated = _journey_learning_pricing_config(
            {
                "journey_learning_pricing_time_limit": 0.75,
                "journey_learning_profile_generation_time_fraction": 0.6,
                "journey_learning_max_returned_journeys": 8,
                "journey_learning_streaming_profile_batch_size": 1000,
                "journey_learning_streaming_min_negative_batch": 8,
                "journey_learning_streaming_min_returned_journeys": 2,
                "journey_learning_streaming_partial_return_after_time": 0.4,
                "journey_learning_streaming_partial_return_min_journeys": 3,
                "journey_learning_early_return_negative_min_count": 4,
            },
            base,
        )

        self.assertAlmostEqual(updated.time_limit, 0.75)
        self.assertAlmostEqual(updated.profile_generation_time_fraction, 0.6)
        self.assertEqual(updated.max_returned_journeys, 8)
        self.assertEqual(updated.streaming_profile_batch_size, 1000)
        self.assertEqual(updated.streaming_min_negative_batch, 8)
        self.assertEqual(updated.streaming_min_returned_journeys, 2)
        self.assertAlmostEqual(updated.streaming_partial_return_after_time, 0.4)
        self.assertEqual(updated.streaming_partial_return_min_journeys, 3)
        self.assertEqual(updated.early_return_negative_min_count, 4)
        self.assertEqual(base.time_limit, 5.0)

    def test_journey_learning_pricing_config_keeps_learning_layer_light(self):
        base = JourneyPricingConfig(
            time_limit=5.0,
            direct_journey_label_pricing_enabled=True,
            direct_journey_label_global_certificate_enabled=True,
            direct_journey_label_completion_bound_enabled=True,
            direct_journey_label_ng_dssr_enabled=True,
            direct_journey_label_ng_exact_probe_enabled=True,
            direct_journey_label_ng_certificate_enabled=True,
            direct_journey_label_ng_probe_certificate_enabled=True,
        )

        updated = _journey_learning_pricing_config({}, base)

        self.assertIsNot(updated, base)
        self.assertFalse(updated.direct_journey_label_pricing_enabled)
        self.assertFalse(updated.direct_journey_label_global_certificate_enabled)
        self.assertFalse(updated.direct_journey_label_completion_bound_enabled)
        self.assertFalse(updated.direct_journey_label_ng_dssr_enabled)
        self.assertFalse(updated.direct_journey_label_ng_exact_probe_enabled)
        self.assertFalse(updated.direct_journey_label_ng_certificate_enabled)
        self.assertFalse(updated.direct_journey_label_ng_probe_certificate_enabled)
        self.assertTrue(base.direct_journey_label_pricing_enabled)
        self.assertTrue(base.direct_journey_label_ng_dssr_enabled)

        experimental = _journey_learning_pricing_config(
            {"journey_learning_force_light_profile_pricing": False},
            base,
        )
        self.assertIs(experimental, base)

    def test_learning_smoothed_pricing_uses_isolated_caches(self):
        trip_cache: dict[tuple, object] = {("resume",): object()}
        resource_cache: dict[tuple, object] = {("resource",): object()}

        normal_trip_cache, normal_resource_cache = _journey_pricing_caches_for_learning_pass(
            learning_smoothed=False,
            trip_cache=trip_cache,
            resource_cache=resource_cache,
        )
        self.assertIs(normal_trip_cache, trip_cache)
        self.assertIs(normal_resource_cache, resource_cache)

        learning_trip_cache, learning_resource_cache = _journey_pricing_caches_for_learning_pass(
            learning_smoothed=True,
            trip_cache=trip_cache,
            resource_cache=resource_cache,
        )
        self.assertIsNot(learning_trip_cache, trip_cache)
        self.assertIsNot(learning_resource_cache, resource_cache)
        self.assertEqual(learning_trip_cache, {})
        self.assertEqual(learning_resource_cache, {})
        self.assertEqual(trip_cache, {("resume",): trip_cache[("resume",)]})
        self.assertEqual(resource_cache, {("resource",): resource_cache[("resource",)]})

    def test_mainline_learning_anchor_configs_are_exact_safe(self):
        config_paths = [
            Path("BPC_future/configs/moon_trek_5_journey.yaml"),
            Path("BPC_future/configs/moon_trek_10_journey.yaml"),
            Path("BPC_future/configs/moon_trek_20_smoke.yaml"),
        ]
        for path in config_paths:
            with self.subTest(path=str(path)):
                config = load_config(path)
                _validate_journey_required_components(config)
                self.assertEqual(config.get("master_mode"), "journey")
                self.assertTrue(config.get("journey_learning_enabled"))
                self.assertTrue(config.get("journey_learning_required"))
                self.assertTrue(config.get("journey_learning_fail_hard"))
                self.assertTrue(config.get("journey_learning_prewarm_enabled"))
                checkpoint = Path(str(config.get("journey_learning_checkpoint_path")))
                self.assertTrue(checkpoint.exists(), checkpoint)
                self.assertTrue(config.get("journey_learning_filter_true_rc"))
                self.assertFalse(config.get("journey_learning_disable_on_certificate_candidate"))
                self.assertFalse(config.get("journey_learning_stagnation_forces_exact"))
                self.assertGreaterEqual(int(config.get("journey_learning_disable_on_branch_depth_gt")), 999)
                self.assertTrue(config.get("journey_learning_pricing_enabled"))
                self.assertGreaterEqual(float(config.get("journey_learning_true_rc_keep_threshold", 0.0)), 0.0)
                self.assertGreater(int(config.get("journey_learning_true_rc_max_kept_per_round")), 0)
                self.assertGreater(float(config.get("journey_learning_pricing_time_limit")), 0.0)
                self.assertEqual(int(config.get("journey_learning_pricing_max_rounds")), 0)
                self.assertTrue(config.get("journey_completion_bound_required"))
                self.assertTrue(config.get("journey_certificate_completion_bound_enabled"))
                self.assertTrue(config.get("journey_certificate_completion_bound_final_probe_only"))
                self.assertTrue(config.get("journey_certificate_completion_bound_after_retry_enabled"))
                self.assertFalse(config.get("journey_certificate_fast_negative_return_enabled"))
                self.assertGreaterEqual(int(config.get("journey_certificate_completion_bound_time_buckets")), 5)
                self.assertLessEqual(int(config.get("journey_certificate_completion_bound_time_buckets")), 15)
                self.assertGreaterEqual(int(config.get("journey_certificate_completion_bound_energy_buckets")), 5)
                self.assertLessEqual(int(config.get("journey_certificate_completion_bound_energy_buckets")), 15)
                self.assertGreater(
                    float(config.get("journey_certificate_completion_bound_after_retry_reserve_time", 0.0)),
                    0.0,
                )
                self.assertGreater(int(config.get("journey_certificate_completion_bound_max_sequences", 0)), 0)
                self.assertGreater(int(config.get("journey_certificate_completion_bound_max_dp_states", 0)), 0)
                self.assertGreater(int(config.get("journey_certificate_completion_bound_partial_max_states", 0)), 0)
                self.assertTrue(config.get("journey_certificate_completion_bound_two_cycle_enabled"))
                self.assertGreater(
                    int(config.get("journey_certificate_completion_bound_two_cycle_max_states", 0)),
                    0,
                )
                self.assertTrue(config.get("journey_certificate_completion_bound_hidden_negative_enabled"))
                self.assertGreater(
                    int(config.get("journey_certificate_completion_bound_hidden_negative_min_journeys", 0)),
                    0,
                )
                self.assertGreaterEqual(
                    int(config.get("journey_certificate_completion_bound_hidden_negative_max_returned_journeys", 0)),
                    int(config.get("journey_certificate_completion_bound_hidden_negative_min_journeys", 0)),
                )
                self.assertGreaterEqual(
                    float(config.get("journey_certificate_completion_bound_hidden_negative_grace_time", 0.0)),
                    0.0,
                )
                self.assertTrue(config.get("journey_certificate_completion_bound_diverse_harvest_enabled"))
                self.assertGreater(
                    int(config.get("journey_certificate_completion_bound_diverse_harvest_min_journeys", 0)),
                    0,
                )
                self.assertGreaterEqual(
                    int(config.get("journey_certificate_completion_bound_diverse_harvest_max_returned_journeys", 0)),
                    int(config.get("journey_certificate_completion_bound_diverse_harvest_min_journeys", 0)),
                )
                self.assertGreaterEqual(
                    int(config.get("journey_certificate_completion_bound_diverse_harvest_top_k_strongest", 0)),
                    0,
                )
                self.assertGreaterEqual(
                    float(config.get("journey_certificate_completion_bound_diverse_harvest_grace_time", 0.0)),
                    0.0,
                )
                self.assertTrue(config.get("journey_pricing_direct_journey_label_cross_count_dominance_enabled"))
                self.assertTrue(config.get("journey_hidden_negative_patrol_enabled"))
                self.assertTrue(config.get("journey_pricing_profile_labeling_physical_catalog_resume_enabled"))
                self.assertFalse(config.get("journey_hidden_negative_profile_catalog_seed_enabled"))
                self.assertFalse(config.get("journey_post_seed_profile_reharvest_enabled"))
                self.assertTrue(config.get("journey_post_seed_profile_reharvest_after_replacement_only"))
                self.assertGreater(float(config.get("journey_post_seed_profile_reharvest_time_limit", 0.0)), 0.0)
                self.assertGreaterEqual(
                    int(config.get("journey_post_seed_profile_reharvest_max_returned_journeys", 0)),
                    int(config.get("journey_post_seed_profile_reharvest_min_journeys", 0)),
                )
                self.assertGreater(
                    int(config.get("journey_post_seed_profile_reharvest_streaming_profile_batch_size", 0)),
                    0,
                )
                patrol_has_beam = int(config.get("journey_hidden_negative_patrol_max_labels_per_node", 0)) > 0
                patrol_has_completion_bound = bool(config.get("journey_hidden_negative_patrol_completion_bound_enabled", False))
                patrol_has_coarsening = bool(config.get("journey_hidden_negative_patrol_resource_coarsening_enabled", False))
                self.assertTrue(patrol_has_beam or patrol_has_completion_bound or patrol_has_coarsening)
                if patrol_has_coarsening:
                    self.assertTrue(
                        float(config.get("journey_hidden_negative_patrol_resource_coarsening_time_bucket_size", 0.0))
                        > 0.0
                        or float(
                            config.get("journey_hidden_negative_patrol_resource_coarsening_energy_bucket_size", 0.0)
                        )
                        > 0.0
                    )
                self.assertGreater(float(config.get("journey_hidden_negative_patrol_time_limit", 0.0)), 0.0)
                self.assertGreater(int(config.get("journey_hidden_negative_patrol_min_journeys", 0)), 0)
                self.assertGreaterEqual(
                    int(config.get("journey_hidden_negative_patrol_max_returned_journeys", 0)),
                    int(config.get("journey_hidden_negative_patrol_min_journeys", 0)),
                )
                self.assertGreaterEqual(int(config.get("journey_hidden_negative_audit_max_logged_journeys", -1)), 0)

    def test_frozen_5_10_mainline_artifacts_are_unchanged(self):
        locked_hashes = {
            Path("BPC_future/configs/moon_trek_5_journey.yaml"):
                "a2e351c7b89b4d37caff49474e5d9d281396de2edcd4c2a9e64444e0bf4435ce",
            Path("BPC_future/configs/moon_trek_10_journey.yaml"):
                "f8f896ad9502b36480d46d5b0484171ff6ca64c75ac2057d8750eee5a95b7313",
            Path("BPC_future/data/learning_dual/hardtail_20260604/hierarchical_option_gat_hardtail.pt"):
                "ef7e8a4acdb9d2d6f60a6bd6038ed75d3e89ac72408acd237e5c1054fefcf88d",
        }
        for path, expected_hash in locked_hashes.items():
            with self.subTest(path=str(path)):
                self.assertTrue(path.exists(), path)
                actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(actual_hash, expected_hash)

    def test_20_task_completion_bound_budget_is_not_smoke_capped(self):
        config = load_config(Path("BPC_future/configs/moon_trek_20_smoke.yaml"))
        self.assertGreaterEqual(int(config.get("journey_certificate_completion_bound_max_sequences", 0)), 1500000)
        self.assertGreaterEqual(int(config.get("journey_certificate_completion_bound_max_dp_states", 0)), 500000)
        self.assertGreaterEqual(int(config.get("journey_certificate_completion_bound_partial_max_states", 0)), 1500000)
        self.assertTrue(config.get("journey_certificate_completion_bound_escalation_enabled"))
        self.assertGreater(
            int(config.get("journey_certificate_completion_bound_escalation_partial_max_states", 0)),
            int(config.get("journey_certificate_completion_bound_partial_max_states", 0)),
        )

    def test_20_task_completion_bound_prioritizes_active_support_repairs(self):
        config = load_config(Path("BPC_future/configs/moon_trek_20_smoke.yaml"))
        self.assertGreater(
            int(config.get("journey_certificate_completion_bound_diverse_harvest_min_priority_task_sets", 0)),
            0,
        )
        self.assertEqual(
            float(config.get("journey_certificate_completion_bound_diverse_harvest_priority_overlap_threshold", 0.0)),
            1.0,
        )

    def test_20_task_flat_weak_replacement_repair_stays_experimental(self):
        config = load_config(Path("BPC_future/configs/moon_trek_20_smoke.yaml"))
        self.assertFalse(config.get("journey_certificate_flat_weak_column_pressure_enabled"))
        self.assertFalse(config.get("journey_replacement_repair_enabled"))
        self.assertFalse(config.get("journey_replacement_repair_after_flat_weak_enabled"))
        self.assertTrue(config.get("journey_replacement_repair_root_only"))
        self.assertGreater(float(config.get("journey_replacement_repair_time_limit", 0.0)), 0.0)
        self.assertGreater(int(config.get("journey_replacement_repair_min_journeys", 0)), 0)
        self.assertGreaterEqual(
            int(config.get("journey_replacement_repair_max_returned_journeys", 0)),
            int(config.get("journey_replacement_repair_min_journeys", 0)),
        )

    def test_journey_required_components_fail_closed(self):
        config = load_config(Path("BPC_future/configs/moon_trek_5_journey.yaml"))
        _validate_journey_required_components(config)

        missing_learning = dict(config)
        missing_learning["journey_learning_enabled"] = False
        with self.assertRaisesRegex(ValueError, "journey_learning_enabled"):
            _validate_journey_required_components(missing_learning)

        missing_checkpoint = dict(config)
        missing_checkpoint["journey_learning_checkpoint_path"] = ""
        with self.assertRaisesRegex(ValueError, "journey_learning_checkpoint_path"):
            _validate_journey_required_components(missing_checkpoint)

        hidden_learning = dict(config)
        hidden_learning["journey_learning_disable_on_certificate_candidate"] = True
        with self.assertRaisesRegex(ValueError, "disable_on_certificate_candidate"):
            _validate_journey_required_components(hidden_learning)

        stagnation_closes_learning = dict(config)
        stagnation_closes_learning["journey_learning_stagnation_forces_exact"] = True
        with self.assertRaisesRegex(ValueError, "stagnation_forces_exact"):
            _validate_journey_required_components(stagnation_closes_learning)

        cold_start_learning = dict(config)
        cold_start_learning["journey_learning_prewarm_enabled"] = False
        with self.assertRaisesRegex(ValueError, "prewarm"):
            _validate_journey_required_components(cold_start_learning)

        disabled_bound = dict(config)
        disabled_bound["journey_certificate_completion_bound_enabled"] = False
        with self.assertRaisesRegex(ValueError, "completion_bound_enabled"):
            _validate_journey_required_components(disabled_bound)

        worker_bound = dict(config)
        worker_bound["journey_certificate_completion_bound_final_probe_only"] = False
        with self.assertRaisesRegex(ValueError, "final_probe_only"):
            _validate_journey_required_components(worker_bound)

        oversized_bound = dict(config)
        oversized_bound["journey_certificate_completion_bound_time_buckets"] = 16
        with self.assertRaisesRegex(ValueError, "time_buckets"):
            _validate_journey_required_components(oversized_bound)

        no_bound_reserve = dict(config)
        no_bound_reserve["journey_certificate_completion_bound_after_retry_reserve_time"] = 0.0
        with self.assertRaisesRegex(ValueError, "after_retry_reserve_time"):
            _validate_journey_required_components(no_bound_reserve)

        unbounded_probe = dict(config)
        unbounded_probe["journey_certificate_completion_bound_partial_max_states"] = 0
        with self.assertRaisesRegex(ValueError, "partial_max_states"):
            _validate_journey_required_components(unbounded_probe)

        invalid_priority_lookahead = dict(config)
        invalid_priority_lookahead["journey_pricing_profile_labeling_priority_future_dual_weight"] = -0.1
        with self.assertRaisesRegex(ValueError, "priority_future_dual_weight"):
            _validate_journey_required_components(invalid_priority_lookahead)

        invalid_cut_priority = dict(config)
        invalid_cut_priority["journey_pricing_profile_labeling_priority_cut_dual_weight"] = -0.1
        with self.assertRaisesRegex(ValueError, "priority_cut_dual_weight"):
            _validate_journey_required_components(invalid_cut_priority)

        invalid_profile_dp_cap = dict(config)
        invalid_profile_dp_cap["journey_pricing_profile_dp_max_labels_per_mask"] = -1
        with self.assertRaisesRegex(ValueError, "profile_dp_max_labels_per_mask"):
            _validate_journey_required_components(invalid_profile_dp_cap)

        invalid_hidden_probe = dict(config)
        invalid_hidden_probe["journey_certificate_completion_bound_hidden_negative_min_journeys"] = 3
        invalid_hidden_probe["journey_certificate_completion_bound_hidden_negative_max_returned_journeys"] = 2
        with self.assertRaisesRegex(ValueError, "hidden_negative_max_returned_journeys"):
            _validate_journey_required_components(invalid_hidden_probe)

        invalid_hidden_grace = dict(config)
        invalid_hidden_grace["journey_certificate_completion_bound_hidden_negative_grace_time"] = -0.1
        with self.assertRaisesRegex(ValueError, "hidden_negative_grace_time"):
            _validate_journey_required_components(invalid_hidden_grace)

        invalid_patrol_labels = dict(config)
        invalid_patrol_labels["journey_hidden_negative_patrol_max_labels_per_node"] = 0
        invalid_patrol_labels["journey_hidden_negative_patrol_completion_bound_enabled"] = False
        with self.assertRaisesRegex(ValueError, "patrol_max_labels_per_node"):
            _validate_journey_required_components(invalid_patrol_labels)

        invalid_patrol_time = dict(config)
        invalid_patrol_time["journey_hidden_negative_patrol_time_limit"] = 0.0
        with self.assertRaisesRegex(ValueError, "patrol_time_limit"):
            _validate_journey_required_components(invalid_patrol_time)

        invalid_patrol_return = dict(config)
        invalid_patrol_return["journey_hidden_negative_patrol_min_journeys"] = 3
        invalid_patrol_return["journey_hidden_negative_patrol_max_returned_journeys"] = 2
        with self.assertRaisesRegex(ValueError, "patrol_max_returned_journeys"):
            _validate_journey_required_components(invalid_patrol_return)

        invalid_deadline_safety = dict(config)
        invalid_deadline_safety["journey_pricing_deadline_safety_margin"] = -0.1
        with self.assertRaisesRegex(ValueError, "deadline_safety_margin"):
            _validate_journey_required_components(invalid_deadline_safety)

        invalid_hidden_audit_limit = dict(config)
        invalid_hidden_audit_limit["journey_hidden_negative_audit_max_logged_journeys"] = -1
        with self.assertRaisesRegex(ValueError, "hidden_negative_audit_max_logged_journeys"):
            _validate_journey_required_components(invalid_hidden_audit_limit)

        invalid_hidden_seed = dict(config)
        invalid_hidden_seed["journey_hidden_negative_profile_catalog_seed_enabled"] = True
        invalid_hidden_seed["journey_pricing_profile_labeling_physical_catalog_resume_enabled"] = False
        with self.assertRaisesRegex(ValueError, "profile_catalog_seed_enabled"):
            _validate_journey_required_components(invalid_hidden_seed)

        invalid_reharvest = dict(config)
        invalid_reharvest["journey_post_seed_profile_reharvest_enabled"] = True
        invalid_reharvest["journey_post_seed_profile_reharvest_time_limit"] = 0.0
        with self.assertRaisesRegex(ValueError, "post_seed_profile_reharvest_time_limit"):
            _validate_journey_required_components(invalid_reharvest)

        invalid_static_src_selection = dict(config)
        invalid_static_src_selection["static_subset_row_selection"] = "unknown"
        with self.assertRaisesRegex(ValueError, "static_subset_row_selection"):
            _validate_journey_required_components(invalid_static_src_selection)

        invalid_pre_exact_patrol = dict(config)
        invalid_pre_exact_patrol["journey_hidden_negative_patrol_before_exact_flat_enabled"] = True
        invalid_pre_exact_patrol["journey_hidden_negative_patrol_before_exact_min_retry_negative_rounds"] = -1
        with self.assertRaisesRegex(ValueError, "before_exact_min_retry_negative_rounds"):
            _validate_journey_required_components(invalid_pre_exact_patrol)

    def test_learning_enabled_configs_do_not_silently_gate_learning(self):
        config_paths = sorted(Path("BPC_future/configs").glob("*.yaml"))
        checked = 0
        for path in config_paths:
            config = load_config(path)
            if not bool(config.get("journey_learning_enabled", False)):
                continue
            checked += 1
            with self.subTest(path=str(path)):
                _validate_journey_required_components(config)
                self.assertTrue(config.get("journey_learning_required"))
                self.assertTrue(config.get("journey_learning_fail_hard"))
                self.assertTrue(config.get("journey_learning_prewarm_enabled"))
                self.assertTrue(config.get("journey_learning_pricing_enabled"))
                self.assertEqual(int(config.get("journey_learning_pricing_max_rounds", -1)), 0)
                self.assertFalse(config.get("journey_learning_stop_after_no_strong_round"))
                self.assertFalse(config.get("journey_learning_disable_on_certificate_candidate"))
                self.assertFalse(config.get("journey_learning_stagnation_forces_exact"))
                self.assertGreaterEqual(int(config.get("journey_learning_disable_on_branch_depth_gt", -1)), 999)
        self.assertGreater(checked, 0)

    def test_journey_pricing_config_maps_ng_probe_controls(self):
        data = load_future_data("very_small")
        pricing_config = _journey_pricing_config(
            data,
            {
                "journey_pricing_direct_journey_label_ng_probe_time_limit": 1.5,
                "journey_pricing_direct_journey_label_ng_probe_min_journeys_for_early_return": 9,
                "journey_pricing_direct_journey_label_ng_probe_certificate_enabled": True,
                "journey_pricing_direct_journey_label_ng_reset_memory_between_sorties_enabled": True,
                "journey_pricing_direct_journey_label_ng_visit_mask_dominance_enabled": True,
                "journey_pricing_streaming_final_dp_time_reserve": 2.25,
            },
            10.0,
            10.0,
            1.0e-6,
            5.0,
            heuristic=False,
            cg_iter=1,
        )
        self.assertAlmostEqual(pricing_config.direct_journey_label_ng_probe_time_limit, 1.5)
        self.assertEqual(pricing_config.direct_journey_label_ng_probe_min_journeys_for_early_return, 9)
        self.assertTrue(pricing_config.direct_journey_label_ng_probe_certificate_enabled)
        self.assertTrue(pricing_config.direct_journey_label_ng_reset_memory_between_sorties_enabled)
        self.assertTrue(pricing_config.direct_journey_label_ng_visit_mask_dominance_enabled)
        self.assertAlmostEqual(pricing_config.streaming_final_dp_time_reserve, 2.25)

    def test_journey_retry_force_ng_config_is_opt_in_and_root_only_by_default(self):
        base = JourneyPricingConfig(
            direct_journey_label_ng_dssr_enabled=False,
            direct_journey_label_ng_exact_probe_enabled=False,
            direct_journey_label_ng_max_labels=50,
            direct_journey_label_ng_min_negative_journeys=2,
            direct_journey_label_ng_probe_time_limit=0.2,
            direct_journey_label_ng_probe_min_journeys_for_early_return=1,
        )

        unchanged, enabled = _journey_retry_force_ng_config({}, base, depth=0)
        self.assertIs(unchanged, base)
        self.assertFalse(enabled)

        updated, enabled = _journey_retry_force_ng_config(
            {
                "journey_retry_incomplete_no_column_force_ng_enabled": True,
                "journey_retry_incomplete_no_column_force_ng_max_labels": 123,
                "journey_retry_incomplete_no_column_force_ng_min_negative_journeys": 7,
                "journey_retry_incomplete_no_column_force_ng_probe_time_limit": 0.6,
                "journey_retry_incomplete_no_column_force_ng_probe_min_journeys_for_early_return": 3,
            },
            base,
            depth=0,
        )
        self.assertTrue(enabled)
        self.assertTrue(updated.direct_journey_label_ng_dssr_enabled)
        self.assertTrue(updated.direct_journey_label_ng_exact_probe_enabled)
        self.assertEqual(updated.direct_journey_label_ng_max_labels, 123)
        self.assertEqual(updated.direct_journey_label_ng_min_negative_journeys, 7)
        self.assertAlmostEqual(updated.direct_journey_label_ng_probe_time_limit, 0.6)
        self.assertEqual(updated.direct_journey_label_ng_probe_min_journeys_for_early_return, 3)

        branch_updated, branch_enabled = _journey_retry_force_ng_config(
            {"journey_retry_incomplete_no_column_force_ng_enabled": True},
            base,
            depth=1,
        )
        self.assertIs(branch_updated, base)
        self.assertFalse(branch_enabled)

    def test_sortie_profile_cross_dominance_is_exact_safe(self):
        data = load_future_data("very_small")
        option = data.options(0, int(data.tasks[0]))[0]
        dominant = _SortieProfile(
            sequence=(1, 2),
            arc_options=(option,),
            lower_start=0.0,
            upper_start=100.0,
            end_offset=20.0,
            cost=10.0,
            mask=0b11,
            contribution=-5.0,
        )
        dominated = _SortieProfile(
            sequence=(2, 1),
            arc_options=(option,),
            lower_start=5.0,
            upper_start=90.0,
            end_offset=25.0,
            cost=12.0,
            mask=0b11,
            contribution=-4.0,
        )
        not_dominated = _SortieProfile(
            sequence=(1, 2),
            arc_options=(option,),
            lower_start=0.0,
            upper_start=120.0,
            end_offset=30.0,
            cost=13.0,
            mask=0b11,
            contribution=-3.0,
        )
        filtered, pruned = _filter_dominated_sortie_profiles([dominated, dominant, not_dominated])
        self.assertEqual(pruned, 1)
        self.assertIn(dominant, filtered)
        self.assertIn(not_dominated, filtered)
        self.assertNotIn(dominated, filtered)

    def test_sortie_profile_filter_deduplicates_identical_resources(self):
        data = load_future_data("very_small")
        option = data.options(0, int(data.tasks[0]))[0]
        weak = _SortieProfile(
            sequence=(1,),
            arc_options=(option,),
            lower_start=0.0,
            upper_start=100.0,
            end_offset=20.0,
            cost=12.0,
            mask=0b1,
            contribution=-4.0,
        )
        strong = _SortieProfile(
            sequence=(1,),
            arc_options=(option,),
            lower_start=0.0,
            upper_start=100.0,
            end_offset=20.0,
            cost=10.0,
            mask=0b1,
            contribution=-6.0,
        )
        filtered, pruned = _filter_dominated_sortie_profiles([weak, strong])
        self.assertEqual(filtered, [strong])
        self.assertEqual(pruned, 1)

    def test_sortie_profile_catalog_filter_counts_cover_dual_once_per_task_mask(self):
        data = load_future_data("very_small")
        task = int(data.tasks[0])
        option = data.options(0, task)[0]
        profile = _SortieProfile(
            sequence=(task, task),
            arc_options=(option,),
            lower_start=0.0,
            upper_start=100.0,
            end_offset=20.0,
            cost=5.0,
            mask=0b1,
            contribution=0.0,
        )
        duals = FutureDuals(
            cover={task: 6.0},
            task_vehicle={},
            sortie_count={int(data.vehicles[0]): 0.0},
            time_occupation={},
            ordering={},
            branches={},
            cuts={},
        )

        filtered, best_profile_rc, cut_pruned = _filter_sortie_profile_catalog(
            [profile],
            duals,
            base_reduced_cost=0.0,
            config=JourneyPricingConfig(),
            journey_cut_duals={},
            journey_cuts=tuple(),
            task_to_bit={task: 0},
        )

        self.assertEqual(cut_pruned, 0)
        self.assertEqual(len(filtered), 1)
        self.assertAlmostEqual(filtered[0].contribution, -1.0)
        self.assertAlmostEqual(best_profile_rc, -1.0)

    def test_sortie_profile_filter_skips_batch_when_online_dominance_applied(self):
        data = load_future_data("very_small")
        option = data.options(0, int(data.tasks[0]))[0]
        profile = _SortieProfile(
            sequence=(1,),
            arc_options=(option,),
            lower_start=0.0,
            upper_start=100.0,
            end_offset=20.0,
            cost=10.0,
            mask=0b1,
            contribution=-5.0,
        )
        config = JourneyPricingConfig(
            profile_cross_dominance_enabled=True,
            profile_online_dominance_enabled=True,
        )
        with patch(
            "BPC_future.pricing.journey_pricing._filter_dominated_sortie_profiles",
            side_effect=AssertionError("batch filter should not run after online dominance"),
        ):
            filtered, pruned = _filter_sortie_profiles_after_generation(
                [profile],
                config,
                {"online_dominance_applied": 1, "online_dominance_pruned": 7},
            )
        self.assertEqual(filtered, [profile])
        self.assertEqual(pruned, 7)

    def test_label_physical_catalog_marks_online_dominance_applied(self):
        data = load_future_data("very_small")
        vehicle = data.vehicles[0]
        duals = FutureDuals(
            cover={int(task): 0.0 for task in data.tasks},
            task_vehicle={},
            sortie_count={int(vehicle): 0.0},
            time_occupation={},
            ordering={},
            branches={},
            cuts={},
        )
        task_order = tuple(int(task) for task in data.tasks)
        task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
        config = JourneyPricingConfig(
            max_tasks_per_trip=3,
            profile_cross_dominance_enabled=True,
            profile_online_dominance_enabled=True,
            profile_labeling_physical_catalog_resume_enabled=True,
            task_set_resource_pruning_enabled=True,
        )
        catalog_stats: dict[str, int] = {}
        profiles, _generated, _evaluated, _best_rc, _exhausted, _reason, _cut_pruned = (
            _generate_negative_sortie_profiles_by_label_physical_catalog(
                data,
                duals,
                base_reduced_cost=-1.0e6,
                config=config,
                deadline=None,
                task_order=task_order,
                task_to_bit=task_to_bit,
                trip_cache={},
                resource_cache={},
                catalog_stats=catalog_stats,
                journey_cut_duals={},
                journey_cuts=tuple(),
            )
        )
        refiltered, pruned = _filter_dominated_sortie_profiles(list(profiles))
        self.assertEqual(catalog_stats.get("online_dominance_applied"), 1)
        self.assertEqual(pruned, 0)
        self.assertEqual(set(refiltered), set(profiles))

    def test_label_physical_catalog_can_exhaust_instead_of_stream_callbacks_after_threshold(self):
        data = load_future_data("very_small")
        vehicle = data.vehicles[0]
        task = int(data.tasks[0])
        duals = FutureDuals(
            cover={int(candidate): 0.0 for candidate in data.tasks},
            task_vehicle={},
            sortie_count={int(vehicle): 0.0},
            time_occupation={},
            ordering={},
            branches={},
            cuts={},
        )
        task_order = tuple(int(candidate) for candidate in data.tasks)
        task_to_bit = {int(candidate): index for index, candidate in enumerate(data.tasks)}
        config = JourneyPricingConfig(
            max_tasks_per_trip=1,
            profile_labeling_physical_catalog_resume_enabled=True,
            streaming_pricing_enabled=True,
            streaming_profile_batch_size=1,
            streaming_callback_exhaust_after_profile_count=1,
        )
        state = _initial_sortie_label_resume_state(data, duals)
        profile = _SortieProfile(
            sequence=(task,),
            arc_options=tuple(),
            lower_start=0.0,
            upper_start=10.0,
            end_offset=1.0,
            cost=-10.0,
            mask=1 << task_to_bit[task],
            contribution=0.0,
        )
        state.profiles_by_key[(profile.sequence, profile.arc_options)] = profile
        key = _sortie_label_physical_catalog_key(
            data,
            config,
            task_order,
            1,
            tuple(),
        )
        captured: dict[str, Any] = {}

        def fake_advance(*args, **kwargs):
            captured["stream_callback"] = kwargs.get("stream_callback")
            captured["stream_profile_batch_size"] = kwargs.get("stream_profile_batch_size")
            resume_state = args[2]
            resume_state.exhausted = True
            resume_state.reason = "exhausted"

        def forbidden_callback(*args, **kwargs):  # pragma: no cover - defensive guard
            raise AssertionError("stream callback should be disabled after threshold")

        catalog_stats: dict[str, int] = {}
        with patch(
            "BPC_future.pricing.journey_pricing._advance_sortie_label_resume_state",
            side_effect=fake_advance,
        ):
            profiles, _generated, _evaluated, _best_rc, exhausted, reason, _cut_pruned = (
                _generate_negative_sortie_profiles_by_label_physical_catalog(
                    data,
                    duals,
                    base_reduced_cost=0.0,
                    config=config,
                    deadline=None,
                    task_order=task_order,
                    task_to_bit=task_to_bit,
                    trip_cache={key: state},
                    resource_cache={},
                    catalog_stats=catalog_stats,
                    journey_cut_duals={},
                    journey_cuts=tuple(),
                    stream_callback=forbidden_callback,
                    stream_profile_batch_size=1,
                )
            )

        self.assertIsNone(captured["stream_callback"])
        self.assertEqual(captured["stream_profile_batch_size"], 0)
        self.assertEqual(catalog_stats.get("streaming_callback_exhaust_triggered"), 1)
        self.assertEqual(catalog_stats.get("streaming_callback_exhaust_threshold"), 1)
        self.assertTrue(exhausted)
        self.assertEqual(reason, "exhausted")
        self.assertEqual([item.sequence for item in profiles], [(task,)])

    def test_sortie_profile_online_skyline_matches_filter(self):
        data = load_future_data("very_small")
        option = data.options(0, int(data.tasks[0]))[0]
        profiles = [
            _SortieProfile(
                sequence=(1, 2),
                arc_options=(option,),
                lower_start=5.0,
                upper_start=80.0,
                end_offset=25.0,
                cost=12.0,
                mask=0b11,
                contribution=-4.0,
            ),
            _SortieProfile(
                sequence=(2, 1),
                arc_options=(option,),
                lower_start=0.0,
                upper_start=100.0,
                end_offset=20.0,
                cost=10.0,
                mask=0b11,
                contribution=-5.0,
            ),
            _SortieProfile(
                sequence=(1,),
                arc_options=(option,),
                lower_start=0.0,
                upper_start=100.0,
                end_offset=12.0,
                cost=7.0,
                mask=0b01,
                contribution=-2.0,
            ),
        ]
        offline, _pruned = _filter_dominated_sortie_profiles(profiles)
        store: dict[int, list[_SortieProfile]] = {}
        for profile in profiles:
            _add_sortie_profile_skyline(store, profile)
        online = [profile for group in store.values() for profile in group]
        self.assertEqual(set(online), set(offline))

    def test_sortie_profile_online_skyline_cap_is_incomplete_search_only(self):
        data = load_future_data("very_small")
        option = data.options(0, int(data.tasks[0]))[0]

        def profile(index: int, *, lower: float, upper: float, end: float, cost: float, contribution: float) -> _SortieProfile:
            return _SortieProfile(
                sequence=(1, 2),
                arc_options=(option,),
                lower_start=lower,
                upper_start=upper,
                end_offset=end,
                cost=cost,
                mask=0b11,
                contribution=contribution,
            )

        first = profile(1, lower=0.0, upper=100.0, end=20.0, cost=10.0, contribution=-5.0)
        second = profile(2, lower=0.0, upper=150.0, end=30.0, cost=9.0, contribution=-6.0)
        dominant = profile(3, lower=0.0, upper=200.0, end=10.0, cost=5.0, contribution=-10.0)
        profiles_by_key: dict[tuple, _SortieProfile] = {}
        profiles_by_mask: dict[int, list[_SortieProfile]] = {}

        added, cap_pruned = _add_sortie_profile_online_skyline(
            profiles_by_key,
            profiles_by_mask,
            ("first",),
            first,
            profile_cap_per_mask=1,
        )
        self.assertTrue(added)
        self.assertFalse(cap_pruned)
        added, cap_pruned = _add_sortie_profile_online_skyline(
            profiles_by_key,
            profiles_by_mask,
            ("second",),
            second,
            profile_cap_per_mask=1,
        )
        self.assertFalse(added)
        self.assertTrue(cap_pruned)
        added, cap_pruned = _add_sortie_profile_online_skyline(
            profiles_by_key,
            profiles_by_mask,
            ("dominant",),
            dominant,
            profile_cap_per_mask=1,
        )
        self.assertTrue(added)
        self.assertFalse(cap_pruned)
        self.assertEqual(profiles_by_mask[0b11], [dominant])

    def test_profile_mask_cap_prevents_exhausted_certificate(self):
        data = load_future_data("very_small")
        duals = FutureDuals(
            cover={int(task): 0.0 for task in data.tasks},
            task_vehicle={},
            sortie_count={int(data.vehicles[0]): 0.0},
            time_occupation={},
            ordering={},
            branches={},
            cuts={},
        )
        state = _initial_sortie_label_resume_state(data, duals)
        state.heap.clear()
        state.profile_mask_cap_pruned = 1
        _advance_sortie_label_resume_state(
            data,
            duals,
            state,
            config=JourneyPricingConfig(streaming_profile_cap_per_mask=1),
            deadline=None,
            task_order=tuple(int(task) for task in data.tasks),
            threshold=float("inf"),
            task_to_bit={int(task): index for index, task in enumerate(data.tasks)},
            max_tasks=2,
        )
        self.assertFalse(state.exhausted)
        self.assertEqual(state.reason, "profile_mask_cap_incomplete")

    def test_journey_profile_instantiation_filters_existing_signature(self):
        data = load_future_data("very_small")
        task = int(data.tasks[0])
        trip = evaluate_timed_trip(data, (task,), 0.0, time_bucket_size=5.0)
        self.assertIsNotNone(trip)
        assert trip is not None
        journey = make_journey(data, (trip,))
        self.assertIsNotNone(journey)
        assert journey is not None
        profile = _SortieProfile(
            sequence=trip.tasks,
            arc_options=tuple(data.options(0, task)[0:1] + data.options(task, 0)[0:1]),
            lower_start=trip.start_time,
            upper_start=trip.start_time,
            end_offset=trip.end_time - trip.start_time,
            cost=trip.cost,
            mask=1,
            contribution=-10.0,
        )
        journeys, filtered, weak_filtered = _instantiate_profile_journey_candidates(
            data,
            [profile],
            [(((0, trip.start_time),), -10.0)],
            JourneyPricingConfig(time_bucket_size=5.0),
            eps=1.0e-6,
            forbidden_journey_signatures={journey.signature},
            max_journeys=1,
        )
        self.assertEqual(journeys, [])
        self.assertEqual(filtered, 1)
        self.assertEqual(weak_filtered, 0)

    def test_journey_profile_dp_skips_forbidden_duplicate_candidate(self):
        data = load_future_data("very_small")
        first_task = int(data.tasks[0])
        second_task = int(data.tasks[1])
        first_trip = evaluate_timed_trip(data, (first_task,), 0.0, time_bucket_size=5.0)
        second_trip = evaluate_timed_trip(data, (second_task,), 0.0, time_bucket_size=5.0)
        self.assertIsNotNone(first_trip)
        self.assertIsNotNone(second_trip)
        assert first_trip is not None and second_trip is not None
        first_journey = make_journey(data, (first_trip,))
        self.assertIsNotNone(first_journey)
        assert first_journey is not None

        profiles = [
            _SortieProfile(
                sequence=first_trip.tasks,
                arc_options=tuple(data.options(0, first_task)[0:1] + data.options(first_task, 0)[0:1]),
                lower_start=0.0,
                upper_start=0.0,
                end_offset=first_trip.end_time - first_trip.start_time,
                cost=first_trip.cost,
                mask=1,
                contribution=-10.0,
            ),
            _SortieProfile(
                sequence=second_trip.tasks,
                arc_options=tuple(data.options(0, second_task)[0:1] + data.options(second_task, 0)[0:1]),
                lower_start=0.0,
                upper_start=0.0,
                end_offset=second_trip.end_time - second_trip.start_time,
                cost=second_trip.cost,
                mask=2,
                contribution=-5.0,
            ),
        ]
        stats: dict[str, int] = {}
        selected, objective, status = _solve_best_journey_profile_dp(
            data,
            profiles,
            base_reduced_cost=0.0,
            cut_duals={},
            cuts=tuple(),
            cut_masks=tuple(),
            max_states=1000,
            max_returned=1,
            forbidden_journey_signatures={first_journey.signature},
            duplicate_scan_limit=10,
            pricing_config=JourneyPricingConfig(time_bucket_size=5.0),
            dp_stats=stats,
        )
        self.assertEqual(status, "OPTIMAL")
        self.assertAlmostEqual(objective or 0.0, -10.0, places=6)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0][0][0][0], 1)
        self.assertEqual(stats.get("duplicate_candidates_filtered"), 1)

    def test_journey_profile_dp_duplicate_scan_limit_is_incomplete(self):
        data = load_future_data("very_small")
        first_task = int(data.tasks[0])
        second_task = int(data.tasks[1])
        first_trip = evaluate_timed_trip(data, (first_task,), 0.0, time_bucket_size=5.0)
        second_trip = evaluate_timed_trip(data, (second_task,), 0.0, time_bucket_size=5.0)
        self.assertIsNotNone(first_trip)
        self.assertIsNotNone(second_trip)
        assert first_trip is not None and second_trip is not None
        journey = make_journey(data, (first_trip,))
        self.assertIsNotNone(journey)
        assert journey is not None
        profiles = [
            _SortieProfile(
                sequence=first_trip.tasks,
                arc_options=tuple(data.options(0, first_task)[0:1] + data.options(first_task, 0)[0:1]),
                lower_start=0.0,
                upper_start=0.0,
                end_offset=first_trip.end_time - first_trip.start_time,
                cost=first_trip.cost,
                mask=1,
                contribution=-10.0,
            ),
            _SortieProfile(
                sequence=second_trip.tasks,
                arc_options=tuple(data.options(0, second_task)[0:1] + data.options(second_task, 0)[0:1]),
                lower_start=0.0,
                upper_start=0.0,
                end_offset=second_trip.end_time - second_trip.start_time,
                cost=second_trip.cost,
                mask=2,
                contribution=-5.0,
            ),
        ]
        stats: dict[str, int] = {}
        selected, objective, status = _solve_best_journey_profile_dp(
            data,
            profiles,
            base_reduced_cost=0.0,
            cut_duals={},
            cuts=tuple(),
            cut_masks=tuple(),
            max_states=1000,
            max_returned=1,
            forbidden_journey_signatures={journey.signature},
            duplicate_scan_limit=1,
            pricing_config=JourneyPricingConfig(time_bucket_size=5.0),
            dp_stats=stats,
        )
        self.assertEqual(selected, [])
        self.assertAlmostEqual(objective or 0.0, -10.0, places=6)
        self.assertEqual(status, "INCOMPLETE")
        self.assertEqual(stats.get("duplicate_candidates_filtered"), 1)
        self.assertEqual(stats.get("duplicate_scan_limited"), 1)

    def test_journey_profile_instantiation_can_filter_weak_negative_without_certificate(self):
        data = load_future_data("very_small")
        task = int(data.tasks[0])
        trip = evaluate_timed_trip(data, (task,), 0.0, time_bucket_size=5.0)
        self.assertIsNotNone(trip)
        assert trip is not None
        profile = _SortieProfile(
            sequence=trip.tasks,
            arc_options=tuple(data.options(0, task)[0:1] + data.options(task, 0)[0:1]),
            lower_start=trip.start_time,
            upper_start=trip.start_time,
            end_offset=trip.end_time - trip.start_time,
            cost=trip.cost,
            mask=1,
            contribution=-10.0,
        )
        journeys, existing_filtered, weak_filtered = _instantiate_profile_journey_candidates(
            data,
            [profile],
            [(((0, trip.start_time),), -2.0e-6)],
            JourneyPricingConfig(time_bucket_size=5.0, min_add_reduced_cost=1.0e-4),
            eps=1.0e-6,
            max_journeys=1,
        )
        self.assertEqual(journeys, [])
        self.assertEqual(existing_filtered, 0)
        self.assertEqual(weak_filtered, 1)

    def test_journey_profile_instantiation_uses_true_rc_when_duals_are_available(self):
        data = load_future_data("very_small")
        task = int(data.tasks[0])
        trip = evaluate_timed_trip(data, (task,), 0.0, time_bucket_size=5.0)
        self.assertIsNotNone(trip)
        assert trip is not None
        journey = make_journey(data, (trip,))
        self.assertIsNotNone(journey)
        assert journey is not None
        profile = _SortieProfile(
            sequence=trip.tasks,
            arc_options=tuple(data.options(0, task)[0:1] + data.options(task, 0)[0:1]),
            lower_start=trip.start_time,
            upper_start=trip.start_time,
            end_offset=trip.end_time - trip.start_time,
            cost=trip.cost,
            mask=1,
            contribution=-2.0e-6,
        )
        duals = JourneyDuals(
            cover={task: float(journey.cost) + 1.0},
            fleet_limit=0.0,
            cuts={},
        )
        journeys, existing_filtered, weak_filtered = _instantiate_profile_journey_candidates(
            data,
            [profile],
            [(((0, trip.start_time),), -2.0e-6)],
            JourneyPricingConfig(time_bucket_size=5.0, min_add_reduced_cost=1.0e-4),
            eps=1.0e-6,
            max_journeys=1,
            duals=duals,
            cuts=tuple(),
        )
        self.assertEqual(len(journeys), 1)
        self.assertAlmostEqual(manual_journey_reduced_cost(journeys[0], duals), -1.0, places=6)
        self.assertEqual(existing_filtered, 0)
        self.assertEqual(weak_filtered, 0)

    def test_profile_candidate_return_limit_decouples_true_rc_scan_from_add_limit(self):
        base = JourneyPricingConfig(max_returned_journeys=8, duplicate_retry_factor=4)
        self.assertEqual(_profile_candidate_return_limit(base, 8), 32)

        wider_scan = JourneyPricingConfig(
            max_returned_journeys=8,
            duplicate_retry_factor=4,
            profile_true_rc_candidate_scan_factor=12,
        )
        self.assertEqual(_profile_candidate_return_limit(wider_scan, 8), 96)

        capped_scan = JourneyPricingConfig(
            max_returned_journeys=8,
            duplicate_retry_factor=4,
            profile_true_rc_candidate_scan_factor=12,
            profile_true_rc_candidate_scan_max_candidates=40,
        )
        self.assertEqual(_profile_candidate_return_limit(capped_scan, 8), 40)

        tiny_cap = JourneyPricingConfig(
            max_returned_journeys=8,
            duplicate_retry_factor=4,
            profile_true_rc_candidate_scan_factor=12,
            profile_true_rc_candidate_scan_max_candidates=3,
        )
        self.assertEqual(_profile_candidate_return_limit(tiny_cap, 8), 8)

    def test_journey_profile_dp_returns_materialization_window_candidate(self):
        data = load_future_data("very_small")
        task = int(data.tasks[0])
        trip = evaluate_timed_trip(data, (task,), 0.0, time_bucket_size=5.0)
        self.assertIsNotNone(trip)
        assert trip is not None
        profile = _SortieProfile(
            sequence=trip.tasks,
            arc_options=tuple(data.options(0, task)[0:1] + data.options(task, 0)[0:1]),
            lower_start=trip.start_time,
            upper_start=trip.start_time,
            end_offset=trip.end_time - trip.start_time,
            cost=trip.cost,
            mask=1,
            contribution=0.5,
        )
        stats: dict[str, int] = {}
        selected, objective, status = _solve_best_journey_profile_dp(
            data,
            [profile],
            base_reduced_cost=0.0,
            cut_duals={},
            cuts=tuple(),
            cut_masks=tuple(),
            max_states=1000,
            max_returned=1,
            optimistic_bound_pruning=False,
            pricing_config=JourneyPricingConfig(
                time_bucket_size=5.0,
                profile_true_rc_materialization_slack=1.0,
            ),
            dp_stats=stats,
        )
        self.assertEqual(status, "OPTIMAL")
        _ = objective
        self.assertEqual(len(selected), 1)
        self.assertEqual(stats.get("negative_candidate_count"), 0)
        self.assertEqual(stats.get("materialization_candidate_count"), 1)
        self.assertEqual(stats.get("materialization_selected_candidate_count"), 1)

    def test_journey_profile_dp_returns_no_negative_only_materialization_candidate(self):
        data = load_future_data("very_small")
        task = int(data.tasks[0])
        trip = evaluate_timed_trip(data, (task,), 0.0, time_bucket_size=5.0)
        self.assertIsNotNone(trip)
        assert trip is not None
        profile = _SortieProfile(
            sequence=trip.tasks,
            arc_options=tuple(data.options(0, task)[0:1] + data.options(task, 0)[0:1]),
            lower_start=trip.start_time,
            upper_start=trip.start_time,
            end_offset=trip.end_time - trip.start_time,
            cost=trip.cost,
            mask=1,
            contribution=0.0,
        )
        stats: dict[str, int] = {}
        selected, objective, status = _solve_best_journey_profile_dp(
            data,
            [profile],
            base_reduced_cost=0.0,
            cut_duals={},
            cuts=tuple(),
            cut_masks=tuple(),
            max_states=1000,
            max_returned=1,
            optimistic_bound_pruning=False,
            pricing_config=JourneyPricingConfig(
                time_bucket_size=5.0,
                profile_no_negative_true_rc_materialization_slack=1.0,
                profile_no_negative_true_rc_materialization_max_candidates=4,
            ),
            dp_stats=stats,
        )
        self.assertEqual(status, "OPTIMAL")
        self.assertEqual(objective, 0.0)
        self.assertEqual(len(selected), 1)
        self.assertEqual(stats.get("negative_candidate_count"), 0)
        self.assertEqual(stats.get("materialization_selected_candidate_count"), 0)
        self.assertEqual(stats.get("no_negative_materialization_candidate_count"), 1)
        self.assertEqual(stats.get("no_negative_materialization_selected_for_scan_count"), 1)
        self.assertEqual(stats.get("no_negative_materialization_selected_candidate_count"), 1)

    def test_journey_profile_dp_returns_replacement_materialization_candidate(self):
        data = load_future_data("very_small")
        task = int(data.tasks[0])
        trip = evaluate_timed_trip(data, (task,), 0.0, time_bucket_size=5.0)
        self.assertIsNotNone(trip)
        assert trip is not None
        profile = _SortieProfile(
            sequence=trip.tasks,
            arc_options=tuple(data.options(0, task)[0:1] + data.options(task, 0)[0:1]),
            lower_start=trip.start_time,
            upper_start=trip.start_time,
            end_offset=trip.end_time - trip.start_time,
            cost=trip.cost,
            mask=1,
            contribution=0.5,
        )
        stats: dict[str, int] = {}
        selected, objective, status = _solve_best_journey_profile_dp(
            data,
            [profile],
            base_reduced_cost=0.0,
            cut_duals={},
            cuts=tuple(),
            cut_masks=tuple(),
            max_states=100,
            max_returned=1,
            optimistic_bound_pruning=False,
            selection_mode="reduced_cost",
            dp_stats=stats,
            dominant_task_set_cost_by_mask={1: float(data.fixed_vehicle_cost) + float(profile.cost) + 1.0},
            pricing_config=JourneyPricingConfig(
                profile_replacement_true_rc_materialization_slack=1.0,
                profile_replacement_true_rc_materialization_max_candidates=4,
            ),
        )
        self.assertEqual(status, "OPTIMAL")
        self.assertEqual(len(selected), 1)
        self.assertAlmostEqual(objective or 0.0, 0.5)
        self.assertEqual(stats.get("replacement_materialization_candidate_count"), 1)
        self.assertEqual(stats.get("replacement_materialization_selected_for_scan_count"), 1)
        self.assertEqual(stats.get("replacement_materialization_selected_candidate_count"), 1)

    def test_journey_profile_dp_caps_materialization_window_candidates(self):
        data = load_future_data("very_small")
        tasks = [int(task) for task in data.tasks[:2]]
        profiles: list[_SortieProfile] = []
        for index, task in enumerate(tasks):
            trip = evaluate_timed_trip(data, (task,), 0.0, time_bucket_size=5.0)
            self.assertIsNotNone(trip)
            assert trip is not None
            profiles.append(
                _SortieProfile(
                    sequence=trip.tasks,
                    arc_options=tuple(data.options(0, task)[0:1] + data.options(task, 0)[0:1]),
                    lower_start=trip.start_time,
                    upper_start=trip.start_time,
                    end_offset=trip.end_time - trip.start_time,
                    cost=trip.cost,
                    mask=1 << index,
                    contribution=0.25 + float(index),
                )
            )
        stats: dict[str, int] = {}
        selected, _objective, status = _solve_best_journey_profile_dp(
            data,
            profiles,
            base_reduced_cost=0.0,
            cut_duals={},
            cuts=tuple(),
            cut_masks=tuple(),
            max_states=1000,
            max_returned=4,
            optimistic_bound_pruning=False,
            pricing_config=JourneyPricingConfig(
                time_bucket_size=5.0,
                profile_true_rc_materialization_slack=2.0,
                profile_true_rc_materialization_max_candidates=1,
            ),
            dp_stats=stats,
        )
        self.assertEqual(status, "OPTIMAL")
        self.assertEqual(len(selected), 1)
        self.assertEqual(stats.get("materialization_candidate_count"), 2)
        self.assertEqual(stats.get("materialization_candidate_selected_for_scan_count"), 1)
        self.assertEqual(stats.get("materialization_candidate_cap_filtered"), 1)

    def test_profile_journey_instantiation_counts_true_rc_filtered_candidate_as_weak(self):
        data = load_future_data("very_small")
        task = int(data.tasks[0])
        trip = evaluate_timed_trip(data, (task,), 0.0, time_bucket_size=5.0)
        self.assertIsNotNone(trip)
        assert trip is not None
        profile = _SortieProfile(
            sequence=trip.tasks,
            arc_options=tuple(data.options(0, task)[0:1] + data.options(task, 0)[0:1]),
            lower_start=trip.start_time,
            upper_start=trip.start_time,
            end_offset=trip.end_time - trip.start_time,
            cost=trip.cost,
            mask=1,
            contribution=-10.0,
        )
        stats: dict[str, object] = {}

        journeys, existing_filtered, weak_filtered = _instantiate_profile_journey_candidates(
            data,
            [profile],
            [(((0, trip.start_time),), -10.0)],
            JourneyPricingConfig(time_bucket_size=5.0),
            eps=1.0e-6,
            max_journeys=1,
            duals=JourneyDuals(cover={task: -100.0}, fleet_limit=0.0, cuts={}),
            cuts=tuple(),
            dp_stats=stats,
        )

        self.assertEqual(journeys, [])
        self.assertEqual(existing_filtered, 0)
        self.assertEqual(weak_filtered, 1)
        self.assertEqual(stats.get("profile_weak_filtered_materialized_count"), 1)
        self.assertEqual(stats.get("profile_weak_filtered_best_rough_rc"), -10.0)
        self.assertGreater(float(stats.get("profile_weak_filtered_best_true_rc", 0.0)), 0.0)
        self.assertGreater(float(stats.get("profile_weak_filtered_max_true_minus_rough", 0.0)), 10.0)
        self.assertEqual(stats.get("profile_weak_filtered_max_true_minus_rough_mask"), 1)

    def test_profile_candidate_selection_skips_nonmaterializable_profile_combo(self):
        data = load_future_data("very_small")
        first_task = int(data.tasks[0])
        second_task = int(data.tasks[1])
        first_trip = evaluate_timed_trip(data, (first_task,), 0.0, time_bucket_size=5.0)
        self.assertIsNotNone(first_trip)
        assert first_trip is not None
        second_trip = None
        for start in (0.0, 1.0, 2.0, 5.0, 10.0):
            candidate = evaluate_timed_trip(data, (second_task,), start, time_bucket_size=5.0)
            if candidate is not None and float(candidate.start_time) < float(first_trip.end_time) - 1.0e-6:
                second_trip = candidate
                break
        self.assertIsNotNone(second_trip)
        assert second_trip is not None
        first_options = tuple(data.options(0, first_task)[0:1] + data.options(first_task, 0)[0:1])
        second_options = tuple(data.options(0, second_task)[0:1] + data.options(second_task, 0)[0:1])
        profiles = [
            _SortieProfile(
                sequence=first_trip.tasks,
                arc_options=first_options,
                lower_start=first_trip.start_time,
                upper_start=first_trip.start_time,
                # Deliberately optimistic: profile DP can believe the next
                # sortie fits, but true trip evaluation shows overlap.
                end_offset=0.1,
                cost=first_trip.cost,
                mask=0b001,
                contribution=-10.0,
            ),
            _SortieProfile(
                sequence=second_trip.tasks,
                arc_options=second_options,
                lower_start=second_trip.start_time,
                upper_start=second_trip.start_time,
                end_offset=second_trip.end_time - second_trip.start_time,
                cost=second_trip.cost,
                mask=0b010,
                contribution=-9.0,
            ),
        ]
        invalid_combo = (-10.0, ((0, first_trip.start_time), (1, second_trip.start_time)), 0b011)
        valid_combo = (-9.0, ((1, second_trip.start_time),), 0b010)
        stats: dict[str, int] = {}

        selected, status = _select_nonduplicate_negative_journey_candidates(
            data,
            profiles,
            [invalid_combo, valid_combo],
            max_returned=1,
            selection_mode="reduced_cost",
            forbidden_journey_signatures=frozenset(),
            duplicate_scan_limit=10,
            dominant_task_set_cost_by_mask=None,
            pricing_config=JourneyPricingConfig(
                time_bucket_size=5.0,
                profile_materialization_feasibility_filter_enabled=True,
            ),
            dp_stats=stats,
            status="OPTIMAL",
        )

        self.assertEqual(status, "OPTIMAL")
        self.assertEqual(selected, [valid_combo])
        self.assertEqual(stats.get("profile_materialization_infeasible_candidates_filtered"), 1)

    def test_sortie_partial_generalized_dominance_prunes_current_time_interval(self):
        left = SimpleNamespace(
            sequence=(1,),
            mask=1,
            last=1,
            partial=_PartialNoWaitingPathProfile(
                arc_options=tuple(),
                lower_start=10.0,
                upper_start=20.0,
                offset=0.0,
                travel_cost=5.0,
                travel_energy=5.0,
                service_cost=0.0,
                service_energy=0.0,
            ),
        )
        right = SimpleNamespace(
            sequence=(1,),
            mask=1,
            last=1,
            partial=_PartialNoWaitingPathProfile(
                arc_options=tuple(),
                lower_start=0.0,
                upper_start=5.0,
                offset=10.0,
                travel_cost=5.0,
                travel_energy=5.0,
                service_cost=0.0,
                service_energy=0.0,
            ),
        )
        self.assertFalse(_dominates_sortie_partial_label(left, right))
        self.assertTrue(_dominates_sortie_partial_label(left, right, generalized=True))
        labels = [left]
        self.assertFalse(_add_sortie_partial_label(labels, right, generalized=True))
        self.assertEqual(labels, [left])

    def test_sortie_partial_active_label_ids_track_dominance(self):
        old = _SortiePartialLabel(
            sequence=(1,),
            mask=1,
            last=1,
            partial=_PartialNoWaitingPathProfile(
                arc_options=tuple(),
                lower_start=0.0,
                upper_start=20.0,
                offset=0.0,
                travel_cost=5.0,
                travel_energy=5.0,
                service_cost=0.0,
                service_energy=0.0,
            ),
        )
        better = _SortiePartialLabel(
            sequence=(1,),
            mask=1,
            last=1,
            partial=_PartialNoWaitingPathProfile(
                arc_options=tuple(),
                lower_start=0.0,
                upper_start=20.0,
                offset=0.0,
                travel_cost=4.0,
                travel_energy=5.0,
                service_cost=0.0,
                service_energy=0.0,
            ),
        )
        worse = _SortiePartialLabel(
            sequence=(1,),
            mask=1,
            last=1,
            partial=_PartialNoWaitingPathProfile(
                arc_options=tuple(),
                lower_start=0.0,
                upper_start=20.0,
                offset=0.0,
                travel_cost=6.0,
                travel_energy=5.0,
                service_cost=0.0,
                service_energy=0.0,
            ),
        )
        labels = [old]
        active_ids = {id(old)}

        self.assertTrue(_add_sortie_partial_label(labels, better, active_label_ids=active_ids))
        self.assertEqual(labels, [better])
        self.assertNotIn(id(old), active_ids)
        self.assertIn(id(better), active_ids)

        self.assertFalse(_add_sortie_partial_label(labels, worse, active_label_ids=active_ids))
        self.assertEqual(labels, [better])
        self.assertNotIn(id(worse), active_ids)

    def test_cover_dual_sum_for_mask_uses_cache(self):
        duals = FutureDuals(
            cover={1: 2.5, 2: -1.0, 3: 4.0},
            task_vehicle={},
            sortie_count={},
            time_occupation={},
            ordering={},
            branches={},
        )
        task_to_bit = {1: 0, 2: 1, 3: 2}
        cache = {}

        self.assertAlmostEqual(_cover_dual_sum_for_mask(0b101, duals, task_to_bit, cache), 6.5)
        self.assertEqual(cache, {0b101: 6.5})
        duals.cover[1] = 100.0
        self.assertAlmostEqual(_cover_dual_sum_for_mask(0b101, duals, task_to_bit, cache), 6.5)

    def test_journey_profile_dp_early_return_waits_for_min_count(self):
        data = load_future_data("very_small")
        task = int(data.tasks[0])
        trip = evaluate_timed_trip(data, (task,), 0.0, time_bucket_size=5.0)
        self.assertIsNotNone(trip)
        assert trip is not None
        profile = _SortieProfile(
            sequence=trip.tasks,
            arc_options=tuple(data.options(0, task)[0:1] + data.options(task, 0)[0:1]),
            lower_start=trip.start_time,
            upper_start=trip.start_time,
            end_offset=trip.end_time - trip.start_time,
            cost=trip.cost,
            mask=1,
            contribution=-10.0,
        )
        selected, objective, status = _solve_best_journey_profile_dp(
            data,
            [profile],
            base_reduced_cost=0.0,
            cut_duals={},
            cuts=tuple(),
            cut_masks=tuple(),
            max_states=1000,
            max_returned=1,
            early_return_negative=True,
            early_return_min_count=2,
            pricing_config=JourneyPricingConfig(time_bucket_size=5.0),
        )
        self.assertEqual(status, "OPTIMAL")
        self.assertEqual(len(selected), 1)
        self.assertLess(objective, 0.0)

    def test_journey_profile_dp_early_return_records_stats(self):
        data = load_future_data("very_small")
        task = int(data.tasks[0])
        trip = evaluate_timed_trip(data, (task,), 0.0, time_bucket_size=5.0)
        self.assertIsNotNone(trip)
        assert trip is not None
        profile = _SortieProfile(
            sequence=trip.tasks,
            arc_options=tuple(data.options(0, task)[0:1] + data.options(task, 0)[0:1]),
            lower_start=trip.start_time,
            upper_start=trip.start_time,
            end_offset=trip.end_time - trip.start_time,
            cost=trip.cost,
            mask=1,
            contribution=-10.0,
        )
        stats: dict[str, int] = {}
        selected, objective, status = _solve_best_journey_profile_dp(
            data,
            [profile],
            base_reduced_cost=0.0,
            cut_duals={},
            cuts=tuple(),
            cut_masks=tuple(),
            max_states=1000,
            max_returned=1,
            early_return_negative=True,
            early_return_min_count=1,
            pricing_config=JourneyPricingConfig(time_bucket_size=5.0),
            dp_stats=stats,
        )
        self.assertEqual(status, "INCOMPLETE")
        self.assertEqual(len(selected), 1)
        self.assertLess(objective, 0.0)
        self.assertGreater(stats.get("processed_labels", 0), 0)
        self.assertGreater(stats.get("state_count", 0), 0)
        self.assertGreater(stats.get("profile_record_scans", 0), 0)

    def test_profile_cut_penalty_pruning_is_sign_guarded(self):
        data = load_future_data("very_small")
        cut = SubsetRowCut((1, 2, 3), 2)
        masks = _cut_masks(data, (cut,))
        task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
        mask = (1 << task_to_bit[1]) | (1 << task_to_bit[2])

        self.assertTrue(_profile_cut_penalty_pruning_safe({0: -3.5}, (cut,)))
        self.assertAlmostEqual(
            _profile_cut_penalty(mask, {0: -3.5}, (cut,), masks, enabled=True),
            3.5,
            places=6,
        )
        self.assertFalse(_profile_cut_penalty_pruning_safe({0: 0.1}, (cut,)))
        self.assertAlmostEqual(
            _profile_cut_penalty(mask, {0: 0.1}, (cut,), masks, enabled=False),
            0.0,
            places=6,
        )

    def test_journey_profile_dp_bound_pruning_can_certificate_no_negative(self):
        data = load_future_data("very_small")
        profile = _SortieProfile(
            sequence=(int(data.tasks[0]),),
            arc_options=tuple(),
            lower_start=0.0,
            upper_start=100.0,
            end_offset=10.0,
            cost=10.0,
            mask=1,
            contribution=5.0,
        )
        stats: dict[str, int] = {}
        candidates, objective, status = _solve_best_journey_profile_dp(
            data,
            [profile],
            base_reduced_cost=100.0,
            cut_duals={},
            cuts=tuple(),
            cut_masks=tuple(),
            max_states=1000,
            optimistic_bound_pruning=True,
            dp_stats=stats,
        )
        self.assertEqual(status, "OPTIMAL")
        self.assertEqual(candidates, [])
        self.assertIsNone(objective)
        self.assertGreater(stats.get("bound_pruned_labels", 0), 0)

    def test_journey_profile_dp_bound_pruning_keeps_possible_negative(self):
        data = load_future_data("very_small")
        profile = _SortieProfile(
            sequence=(int(data.tasks[0]),),
            arc_options=tuple(),
            lower_start=0.0,
            upper_start=100.0,
            end_offset=10.0,
            cost=10.0,
            mask=1,
            contribution=-20.0,
        )
        stats: dict[str, int] = {}
        candidates, objective, status = _solve_best_journey_profile_dp(
            data,
            [profile],
            base_reduced_cost=10.0,
            cut_duals={},
            cuts=tuple(),
            cut_masks=tuple(),
            max_states=1000,
            optimistic_bound_pruning=True,
            dp_stats=stats,
        )
        self.assertEqual(status, "OPTIMAL")
        self.assertLess(objective, 0.0)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(stats.get("bound_pruned_labels", 0), 0)

    def test_journey_profile_dp_bound_pruning_keeps_positive_src_reward_negative(self):
        data = load_future_data("very_small")
        first = int(data.tasks[0])
        second = int(data.tasks[1])
        task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
        profiles = [
            _SortieProfile(
                sequence=(first,),
                arc_options=tuple(),
                lower_start=0.0,
                upper_start=100.0,
                end_offset=10.0,
                cost=0.0,
                mask=1 << task_to_bit[first],
                contribution=0.0,
            ),
            _SortieProfile(
                sequence=(second,),
                arc_options=tuple(),
                lower_start=0.0,
                upper_start=100.0,
                end_offset=10.0,
                cost=0.0,
                mask=1 << task_to_bit[second],
                contribution=0.0,
            ),
        ]
        cut = SubsetRowCut((first, second), 2)
        stats: dict[str, int] = {}

        candidates, objective, status = _solve_best_journey_profile_dp(
            data,
            profiles,
            base_reduced_cost=0.0,
            cut_duals={0: 10.0},
            cuts=(cut,),
            cut_masks=_cut_masks(data, (cut,)),
            max_states=1000,
            optimistic_bound_pruning=True,
            pricing_config=JourneyPricingConfig(max_tasks_per_trip=1),
            dp_stats=stats,
        )

        self.assertEqual(status, "OPTIMAL")
        self.assertLess(objective, 0.0)
        self.assertEqual(len(candidates), 1)
        self.assertAlmostEqual(objective, -10.0, places=6)

    def test_journey_profile_dp_bound_pruning_uses_positive_src_reward_bound(self):
        data = load_future_data("very_small")
        first = int(data.tasks[0])
        second = int(data.tasks[1])
        task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
        profiles = [
            _SortieProfile(
                sequence=(first,),
                arc_options=tuple(),
                lower_start=0.0,
                upper_start=100.0,
                end_offset=10.0,
                cost=0.0,
                mask=1 << task_to_bit[first],
                contribution=0.0,
            ),
            _SortieProfile(
                sequence=(second,),
                arc_options=tuple(),
                lower_start=0.0,
                upper_start=100.0,
                end_offset=10.0,
                cost=0.0,
                mask=1 << task_to_bit[second],
                contribution=0.0,
            ),
        ]
        cut = SubsetRowCut((first, second), 2)
        stats: dict[str, int] = {}

        candidates, objective, status = _solve_best_journey_profile_dp(
            data,
            profiles,
            base_reduced_cost=20.0,
            cut_duals={0: 10.0},
            cuts=(cut,),
            cut_masks=_cut_masks(data, (cut,)),
            max_states=1000,
            optimistic_bound_pruning=True,
            pricing_config=JourneyPricingConfig(max_tasks_per_trip=1),
            dp_stats=stats,
        )

        self.assertEqual(status, "OPTIMAL")
        self.assertEqual(candidates, [])
        self.assertIsNone(objective)
        self.assertGreater(stats.get("bound_pruned_labels", 0), 0)

    def test_journey_profile_dp_bound_pruning_keeps_positive_fleet_reward_negative(self):
        data = load_future_data("very_small")
        first = int(data.tasks[0])
        task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
        profile = _SortieProfile(
            sequence=(first,),
            arc_options=tuple(),
            lower_start=0.0,
            upper_start=100.0,
            end_offset=10.0,
            cost=0.0,
            mask=1 << task_to_bit[first],
            contribution=0.0,
        )
        cut = FleetLowerBoundCut(1)
        stats: dict[str, int] = {}

        candidates, objective, status = _solve_best_journey_profile_dp(
            data,
            [profile],
            base_reduced_cost=0.0,
            cut_duals={0: 5.0},
            cuts=(cut,),
            cut_masks=_cut_masks(data, (cut,)),
            max_states=1000,
            optimistic_bound_pruning=True,
            pricing_config=JourneyPricingConfig(max_tasks_per_trip=1),
            dp_stats=stats,
        )

        self.assertEqual(status, "OPTIMAL")
        self.assertLess(objective, 0.0)
        self.assertEqual(len(candidates), 1)
        self.assertAlmostEqual(objective, -5.0, places=6)

    def test_sortie_label_completion_obeys_expired_deadline(self):
        data = load_future_data("very_small")
        first = int(data.tasks[0])
        task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
        label = _SortiePartialLabel(
            sequence=(first,),
            mask=1 << task_to_bit[first],
            last=first,
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
        stats: dict[str, int] = {}
        profiles_by_key: dict[tuple, _SortieProfile] = {}

        evaluated, best_rc = _complete_sortie_label_profiles(
            data,
            FutureDuals(
                cover={int(task): 0.0 for task in data.tasks},
                task_vehicle={},
                sortie_count={},
                time_occupation={},
                ordering={},
                branches={},
            ),
            label,
            JourneyPricingConfig(),
            profiles_by_key,
            float("inf"),
            task_to_bit,
            deadline=0.0,
            catalog_stats=stats,
        )

        self.assertEqual(evaluated, 0)
        self.assertIsNone(best_rc)
        self.assertEqual(profiles_by_key, {})
        self.assertEqual(stats.get("profile_completion_time_pruned"), 1)

    def test_journey_profile_dp_disjoint_bound_prunes_overlapping_profiles(self):
        data = load_future_data("very_small")
        profiles = [
            _SortieProfile(
                sequence=(int(data.tasks[0]),),
                arc_options=tuple(),
                lower_start=0.0,
                upper_start=100.0,
                end_offset=10.0,
                cost=10.0,
                mask=1,
                contribution=-10.0,
            ),
            _SortieProfile(
                sequence=(int(data.tasks[0]),),
                arc_options=tuple(),
                lower_start=0.0,
                upper_start=100.0,
                end_offset=10.0,
                cost=9.0,
                mask=1,
                contribution=-10.0,
            ),
        ]
        stats: dict[str, int] = {}
        candidates, objective, status = _solve_best_journey_profile_dp(
            data,
            profiles,
            base_reduced_cost=15.0,
            cut_duals={},
            cuts=tuple(),
            cut_masks=tuple(),
            max_states=1000,
            optimistic_bound_pruning=True,
            pricing_config=JourneyPricingConfig(time_bucket_size=5.0, dp_disjoint_bound_pruning_enabled=True),
            dp_stats=stats,
        )
        self.assertEqual(status, "OPTIMAL")
        self.assertEqual(candidates, [])
        self.assertIsNone(objective)
        self.assertGreater(stats.get("disjoint_bound_pruned_labels", 0), 0)

    def test_journey_profile_dp_disjoint_bound_keeps_disjoint_negative(self):
        data = load_future_data("very_small")
        profiles = [
            _SortieProfile(
                sequence=(int(data.tasks[0]),),
                arc_options=tuple(),
                lower_start=0.0,
                upper_start=100.0,
                end_offset=10.0,
                cost=10.0,
                mask=1,
                contribution=-10.0,
            ),
            _SortieProfile(
                sequence=(int(data.tasks[1]),),
                arc_options=tuple(),
                lower_start=0.0,
                upper_start=100.0,
                end_offset=10.0,
                cost=10.0,
                mask=2,
                contribution=-10.0,
            ),
        ]
        stats: dict[str, int] = {}
        candidates, objective, status = _solve_best_journey_profile_dp(
            data,
            profiles,
            base_reduced_cost=15.0,
            cut_duals={},
            cuts=tuple(),
            cut_masks=tuple(),
            max_states=1000,
            optimistic_bound_pruning=True,
            pricing_config=JourneyPricingConfig(time_bucket_size=5.0, dp_disjoint_bound_pruning_enabled=True),
            dp_stats=stats,
        )
        self.assertEqual(status, "OPTIMAL")
        self.assertLess(objective, 0.0)
        self.assertEqual(len(candidates), 1)

    def test_journey_profile_dp_same_vehicle_completion_prunes_dead_partial(self):
        data = load_future_data("very_small")
        left_task = int(data.tasks[0])
        right_task = int(data.tasks[1])
        left = _SortieProfile(
            sequence=(left_task,),
            arc_options=tuple(),
            lower_start=0.0,
            upper_start=0.0,
            end_offset=10.0,
            cost=10.0,
            mask=0b01,
            contribution=-10.0,
        )
        right_too_early = _SortieProfile(
            sequence=(right_task,),
            arc_options=tuple(),
            lower_start=0.0,
            upper_start=5.0,
            end_offset=10.0,
            cost=10.0,
            mask=0b10,
            contribution=-10.0,
        )
        stats: dict[str, int] = {}
        candidates, objective, status = _solve_best_journey_profile_dp(
            data,
            [left, right_too_early],
            base_reduced_cost=0.0,
            cut_duals={},
            cuts=tuple(),
            cut_masks=tuple(),
            max_states=1000,
            optimistic_bound_pruning=False,
            branch_constraints=(BranchConstraint("same_vehicle", left_task, right_task),),
            pricing_config=JourneyPricingConfig(dp_same_completion_pruning_enabled=True),
            dp_stats=stats,
        )
        self.assertEqual(status, "OPTIMAL")
        self.assertEqual(candidates, [])
        self.assertIsNone(objective)
        self.assertGreater(stats.get("same_completion_pruned_labels", 0), 0)

    def test_journey_profile_dp_same_vehicle_completion_keeps_feasible_partial(self):
        data = load_future_data("very_small")
        left_task = int(data.tasks[0])
        right_task = int(data.tasks[1])
        left = _SortieProfile(
            sequence=(left_task,),
            arc_options=tuple(),
            lower_start=0.0,
            upper_start=0.0,
            end_offset=10.0,
            cost=10.0,
            mask=0b01,
            contribution=-10.0,
        )
        right_late = _SortieProfile(
            sequence=(right_task,),
            arc_options=tuple(),
            lower_start=10.0,
            upper_start=100.0,
            end_offset=10.0,
            cost=10.0,
            mask=0b10,
            contribution=-10.0,
        )
        stats: dict[str, int] = {}
        candidates, objective, status = _solve_best_journey_profile_dp(
            data,
            [left, right_late],
            base_reduced_cost=0.0,
            cut_duals={},
            cuts=tuple(),
            cut_masks=tuple(),
            max_states=1000,
            optimistic_bound_pruning=False,
            branch_constraints=(BranchConstraint("same_vehicle", left_task, right_task),),
            pricing_config=JourneyPricingConfig(dp_same_completion_pruning_enabled=True),
            dp_stats=stats,
        )
        self.assertEqual(status, "OPTIMAL")
        self.assertLess(objective, 0.0)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(len(candidates[0][0]), 2)

    def test_journey_profile_dp_cross_count_dominates_same_mask_with_more_sorties(self):
        data = load_future_data("very_small")
        one_sortie = _SortieProfile(
            sequence=(1, 2),
            arc_options=tuple(),
            lower_start=0.0,
            upper_start=100.0,
            end_offset=20.0,
            cost=10.0,
            mask=0b11,
            contribution=-5.0,
        )
        first = _SortieProfile(
            sequence=(1,),
            arc_options=tuple(),
            lower_start=0.0,
            upper_start=100.0,
            end_offset=10.0,
            cost=10.0,
            mask=0b01,
            contribution=-2.0,
        )
        second = _SortieProfile(
            sequence=(2,),
            arc_options=tuple(),
            lower_start=0.0,
            upper_start=100.0,
            end_offset=10.0,
            cost=10.0,
            mask=0b10,
            contribution=-2.0,
        )
        stats: dict[str, int] = {}
        candidates, objective, status = _solve_best_journey_profile_dp(
            data,
            [first, second, one_sortie],
            base_reduced_cost=0.0,
            cut_duals={},
            cuts=tuple(),
            cut_masks=tuple(),
            max_states=1000,
            optimistic_bound_pruning=False,
            cross_count_dominance=True,
            dp_stats=stats,
        )
        self.assertEqual(status, "OPTIMAL")
        self.assertLess(objective, 0.0)
        self.assertEqual(len(candidates[0][0]), 1)
        self.assertGreater(stats.get("cross_count_pruned_labels", 0), 0)

    def test_journey_profile_dp_cross_count_pruned_label_can_enter_materialization_pool(self):
        data = load_future_data("very_small")
        first = _SortieProfile(
            sequence=(1,),
            arc_options=tuple(),
            lower_start=0.0,
            upper_start=100.0,
            end_offset=10.0,
            cost=10.0,
            mask=0b01,
            contribution=0.2,
        )
        second = _SortieProfile(
            sequence=(2,),
            arc_options=tuple(),
            lower_start=10.0,
            upper_start=100.0,
            end_offset=10.0,
            cost=10.0,
            mask=0b10,
            contribution=0.2,
        )
        dominant_same_mask = _SortieProfile(
            sequence=(1, 2),
            arc_options=tuple(),
            lower_start=0.0,
            upper_start=100.0,
            end_offset=5.0,
            cost=10.0,
            mask=0b11,
            contribution=0.0,
        )
        stats: dict[str, int] = {}

        candidates, objective, status = _solve_best_journey_profile_dp(
            data,
            [first, second, dominant_same_mask],
            base_reduced_cost=0.0,
            cut_duals={},
            cuts=tuple(),
            cut_masks=tuple(),
            max_states=1000,
            optimistic_bound_pruning=False,
            cross_count_dominance=True,
            pricing_config=JourneyPricingConfig(
                profile_cross_count_true_rc_materialization_slack=1.0,
                profile_cross_count_true_rc_materialization_max_candidates=4,
            ),
            dp_stats=stats,
        )

        self.assertEqual(status, "OPTIMAL")
        self.assertAlmostEqual(objective or 0.0, 0.0)
        self.assertGreater(stats.get("cross_count_pruned_labels", 0), 0)
        self.assertEqual(stats.get("cross_count_materialization_candidate_count"), 1)
        self.assertEqual(stats.get("cross_count_materialization_selected_for_scan_count"), 1)
        self.assertEqual(stats.get("cross_count_materialization_selected_candidate_count"), 1)
        self.assertTrue(any(len(selected) == 2 for selected, _objective in candidates))

    def test_profile_worker_label_cap_prunes_bucket_without_certificate_semantics(self):
        labels: dict[int, list[_JourneyLabel]] = {}
        stats: dict[str, int] = {}
        first = _JourneyLabel(end_time=10.0, value=1.0, selected=((0, 0.0),))
        second = _JourneyLabel(end_time=20.0, value=0.0, selected=((1, 0.0),))
        third = _JourneyLabel(end_time=5.0, value=2.0, selected=((2, 0.0),))

        self.assertTrue(_add_profile_label(labels, 0b11, first, dp_stats=stats, max_labels_per_mask=2))
        self.assertTrue(_add_profile_label(labels, 0b11, second, dp_stats=stats, max_labels_per_mask=2))
        self.assertFalse(_add_profile_label(labels, 0b11, third, dp_stats=stats, max_labels_per_mask=2))

        self.assertEqual(len(labels[0b11]), 2)
        self.assertIn(first, labels[0b11])
        self.assertIn(second, labels[0b11])
        self.assertNotIn(third, labels[0b11])
        self.assertEqual(stats.get("label_cap_pruned"), 1)

    def test_negative_journey_diverse_selection_keeps_true_negative_candidates(self):
        candidates = [
            (-10.0, ((0, 0.0),), 0b001),
            (-9.0, ((1, 0.0),), 0b001),
            (-8.0, ((2, 0.0),), 0b001),
            (-7.0, ((3, 0.0),), 0b010),
            (-6.0, ((4, 0.0),), 0b100),
        ]
        selected = _select_negative_journey_candidates(candidates, 3, "diverse")
        self.assertEqual(selected[0], candidates[0])
        self.assertTrue(all(objective < 0.0 for objective, _selected, _mask in selected))
        self.assertGreater(len({mask for _objective, _selected, mask in selected}), 1)

    def test_negative_journey_integer_diverse_selection_keeps_structural_variety(self):
        candidates = [
            (-10.0, ((0, 0.0),), 0b001),
            (-9.0, ((1, 10.0),), 0b001),
            (-8.0, ((2, 20.0),), 0b001),
            (-7.0, ((3, 0.0),), 0b010),
            (-6.0, ((4, 0.0), (5, 120.0)), 0b100),
        ]
        reduced_cost = _select_negative_journey_candidates(candidates, 3, "reduced_cost")
        integer_diverse = _select_negative_journey_candidates(candidates, 3, "integer_diverse")
        self.assertEqual(reduced_cost, [candidates[0], candidates[3], candidates[4]])
        self.assertTrue(all(objective < 0.0 for objective, _selected, _mask in integer_diverse))
        self.assertGreater(len({mask for _objective, _selected, mask in integer_diverse}), 1)
        self.assertIn(candidates[0], integer_diverse)

    def test_negative_journey_orthogonal_selection_prefers_low_overlap_masks(self):
        candidates = [
            (-10.0, ((0, 0.0),), 0b00111),
            (-9.0, ((1, 0.0),), 0b00110),
            (-8.0, ((2, 0.0),), 0b11000),
            (-7.0, ((3, 0.0),), 0b100000),
            (-6.0, ((4, 0.0),), 0b00101),
        ]

        selected = _select_negative_journey_candidates(candidates, 3, "orthogonal")

        self.assertEqual(selected[0], candidates[0])
        self.assertIn(candidates[2], selected)
        self.assertIn(candidates[3], selected)
        self.assertNotIn(candidates[1], selected)

    def test_profile_candidate_selection_skips_dominated_task_sets_without_forbidden_signatures(self):
        profiles = [
            _SortieProfile(
                sequence=(1,),
                arc_options=tuple(),
                lower_start=0.0,
                upper_start=100.0,
                end_offset=10.0,
                cost=10.0,
                mask=0b001,
                contribution=-10.0,
            ),
            _SortieProfile(
                sequence=(2,),
                arc_options=tuple(),
                lower_start=0.0,
                upper_start=100.0,
                end_offset=10.0,
                cost=20.0,
                mask=0b010,
                contribution=-9.0,
            ),
        ]
        candidates = [
            (-10.0, ((0, 0.0),), 0b001),
            (-9.0, ((1, 0.0),), 0b010),
        ]
        stats: dict[str, int] = {}

        selected, status = _select_nonduplicate_negative_journey_candidates(
            SimpleNamespace(fixed_vehicle_cost=100.0),
            profiles,
            candidates,
            max_returned=1,
            selection_mode="reduced_cost",
            forbidden_journey_signatures=frozenset(),
            duplicate_scan_limit=10,
            dominant_task_set_cost_by_mask={0b001: 105.0},
            pricing_config=None,
            dp_stats=stats,
            status="OPTIMAL",
        )

        self.assertEqual(status, "OPTIMAL")
        self.assertEqual(selected, [candidates[1]])
        self.assertEqual(stats.get("dominated_task_set_candidates_filtered"), 1)
        self.assertEqual(stats.get("duplicate_candidates_filtered"), 1)

    def test_journey_progress_classifies_flat_objective_changing_dual_as_degenerate(self):
        self.assertEqual(
            _journey_progress_classification(0.0, 0.5, "support-a", "support-a", 1.0e-6),
            "dual_changed_degenerate",
        )
        self.assertEqual(
            _journey_progress_classification(0.0, 0.0, "support-a", "support-a", 1.0e-6),
            "stalled_same_dual_support",
        )

    def test_journey_pool_restart_triggers_are_opt_in(self):
        triggered, reason = _journey_pool_restart_triggered(
            {},
            cg_iter=8,
            certificate_flat_rounds=0,
            restart_count=0,
            progress_classification="dual_changed_degenerate",
            degenerate_rounds=5,
        )
        self.assertFalse(triggered)
        self.assertEqual(reason, "not_triggered")

        triggered, reason = _journey_pool_restart_triggered(
            {"journey_pool_restart_trigger": "certificate_flat", "journey_pool_restart_after_flat_rounds": 2},
            cg_iter=8,
            certificate_flat_rounds=2,
            restart_count=0,
            progress_classification="objective_improved",
            degenerate_rounds=0,
        )
        self.assertTrue(triggered)
        self.assertEqual(reason, "certificate_flat")

        triggered, reason = _journey_pool_restart_triggered(
            {
                "journey_pool_restart_trigger": "degenerate_flat",
                "journey_pool_restart_after_degenerate_rounds": 3,
            },
            cg_iter=8,
            certificate_flat_rounds=0,
            restart_count=0,
            progress_classification="dual_changed_degenerate",
            degenerate_rounds=3,
        )
        self.assertTrue(triggered)
        self.assertEqual(reason, "degenerate_flat")

        triggered, reason = _journey_pool_restart_triggered(
            {"journey_pool_restart_trigger": "fixed_interval", "journey_pool_restart_interval": 4},
            cg_iter=8,
            certificate_flat_rounds=0,
            restart_count=0,
            progress_classification="objective_improved",
            degenerate_rounds=0,
        )
        self.assertTrue(triggered)
        self.assertEqual(reason, "fixed_interval")

    def test_journey_pool_probe_respects_frequency(self):
        self.assertFalse(_should_run_journey_pool_probe(False, 2, 1))
        self.assertFalse(_should_run_journey_pool_probe(True, 0, 1))
        self.assertFalse(_should_run_journey_pool_probe(True, 3, 2))
        self.assertTrue(_should_run_journey_pool_probe(True, 4, 2))
        self.assertTrue(_should_run_journey_pool_probe(True, 3, 0))

    def test_journey_branch_helpers_filter_and_choose_pair(self):
        data = load_future_data("very_small")

        def journey(jid: int, tasks: tuple[int, ...]) -> JourneyColumn:
            return JourneyColumn(
                id=jid,
                trips=tuple(),
                task_set=frozenset(tasks),
                start_time=0.0,
                end_time=0.0,
                travel_cost=0.0,
                fixed_vehicle_cost=0.0,
                cost=0.0,
                signature=("j", jid, tasks),
            )

        only_1 = journey(1, (1,))
        both = journey(2, (1, 2))
        neither = journey(3, (3,))
        self.assertTrue(_journey_allowed_by_branch(both, (BranchConstraint("same_vehicle", 1, 2),)))
        self.assertFalse(_journey_allowed_by_branch(only_1, (BranchConstraint("same_vehicle", 1, 2),)))
        self.assertFalse(_journey_allowed_by_branch(both, (BranchConstraint("separate_vehicle", 1, 2),)))
        self.assertEqual(
            _filter_journeys_by_branch([only_1, both, neither], (BranchConstraint("same_vehicle", 1, 2),)),
            [both, neither],
        )
        branch = _choose_journey_branch(
            data,
            [(both, 0.5), (only_1, 0.5)],
            tuple(),
            1.0e-6,
        )
        self.assertIsNotNone(branch)
        assert branch is not None
        self.assertEqual((branch[0].kind, branch[1].kind), ("same_vehicle", "separate_vehicle"))
        self.assertEqual((branch[0].task_i, branch[0].task_j), (1, 2))

    def test_forbidden_signatures_are_scoped_to_branch_node_pool(self):
        def journey(jid: int, tasks: tuple[int, ...]) -> JourneyColumn:
            return JourneyColumn(
                id=jid,
                trips=tuple(),
                task_set=frozenset(tasks),
                start_time=0.0,
                end_time=0.0,
                travel_cost=0.0,
                fixed_vehicle_cost=0.0,
                cost=0.0,
                signature=("j", jid, tasks),
            )

        pool = JourneyPool(task_set_dominance_enabled=False)
        only_1 = pool.add(journey(1, (1,)))
        both = pool.add(journey(2, (1, 2)))

        root_forbidden = _journey_forbidden_signatures_for_node(pool, tuple())
        self.assertIn(only_1.signature, root_forbidden)
        self.assertIn(both.signature, root_forbidden)

        node_forbidden = _journey_forbidden_signatures_for_node(
            pool,
            (BranchConstraint("separate_vehicle", 1, 2),),
        )
        self.assertIn(only_1.signature, node_forbidden)
        self.assertNotIn(both.signature, node_forbidden)

    def test_journey_branch_tie_tolerance_can_stabilize_pair_choice(self):
        data = replace(load_future_data("very_small"), tasks=(1, 2, 3))

        def journey(jid: int, tasks: tuple[int, ...]) -> JourneyColumn:
            return JourneyColumn(
                id=jid,
                trips=tuple(),
                task_set=frozenset(tasks),
                start_time=0.0,
                end_time=0.0,
                travel_cost=0.0,
                fixed_vehicle_cost=0.0,
                cost=0.0,
                signature=("branch-tie", jid, tasks),
            )

        values = [(journey(1, (1, 2)), 0.49), (journey(2, (2, 3)), 0.5)]
        default_branch = _choose_journey_branch(data, values, tuple(), 1.0e-6)
        self.assertIsNotNone(default_branch)
        assert default_branch is not None
        self.assertEqual((default_branch[0].task_i, default_branch[0].task_j), (2, 3))

        stable_branch = _choose_journey_branch(
            data,
            values,
            tuple(),
            1.0e-6,
            tie_tolerance=0.02,
            priority_mode="low_task_index",
        )
        self.assertIsNotNone(stable_branch)
        assert stable_branch is not None
        self.assertEqual((stable_branch[0].task_i, stable_branch[0].task_j), (1, 2))

    def test_journey_branch_can_prioritize_incumbent_disagreement(self):
        data = replace(load_future_data("very_small"), tasks=(1, 2, 3))

        def journey(jid: int, tasks: tuple[int, ...]) -> JourneyColumn:
            return JourneyColumn(
                id=jid,
                trips=tuple(),
                task_set=frozenset(tasks),
                start_time=0.0,
                end_time=0.0,
                travel_cost=0.0,
                fixed_vehicle_cost=0.0,
                cost=0.0,
                signature=("branch-incumbent", jid, tasks),
            )

        values = [(journey(1, (1, 2)), 0.5), (journey(2, (2, 3)), 0.49)]
        incumbent_solution = {
            1: [SimpleNamespace(tasks=(2, 3))],
            2: [SimpleNamespace(tasks=(1,))],
        }
        default_branch = _choose_journey_branch(data, values, tuple(), 1.0e-6)
        self.assertIsNotNone(default_branch)
        assert default_branch is not None
        self.assertEqual((default_branch[0].task_i, default_branch[0].task_j), (1, 2))

        guided_branch = _choose_journey_branch(
            data,
            values,
            tuple(),
            1.0e-6,
            tie_tolerance=0.02,
            priority_mode="incumbent_disagreement",
            incumbent_solution=incumbent_solution,
        )
        self.assertIsNotNone(guided_branch)
        assert guided_branch is not None
        self.assertEqual((guided_branch[0].task_i, guided_branch[0].task_j), (2, 3))

        same, separate = guided_branch
        ordered = _journey_child_constraint_order(
            JourneyPool(),
            tuple(),
            (same, separate),
            by_width=False,
            priority_mode="incumbent_relation",
            incumbent_solution=incumbent_solution,
        )
        self.assertEqual(ordered[0][0].kind, "same_vehicle")

    def test_journey_branch_can_prioritize_pool_split_width(self):
        data = replace(load_future_data("very_small"), tasks=(1, 2, 3))

        def journey(jid: int, tasks: tuple[int, ...]) -> JourneyColumn:
            return JourneyColumn(
                id=jid,
                trips=tuple(),
                task_set=frozenset(tasks),
                start_time=0.0,
                end_time=0.0,
                travel_cost=0.0,
                fixed_vehicle_cost=0.0,
                cost=float(jid),
                signature=("branch-pool-split", jid, tasks),
            )

        values = [(journey(1, (1, 2)), 0.49), (journey(2, (2, 3)), 0.5)]
        pool = JourneyPool()
        for col in (journey(10, (1, 2)), journey(11, (3,)), journey(12, (1,))):
            pool.add(col)

        default_branch = _choose_journey_branch(data, values, tuple(), 1.0e-6)
        self.assertIsNotNone(default_branch)
        assert default_branch is not None
        self.assertEqual((default_branch[0].task_i, default_branch[0].task_j), (2, 3))

        split_branch = _choose_journey_branch(
            data,
            values,
            tuple(),
            1.0e-6,
            tie_tolerance=0.02,
            priority_mode="pool_split",
            journey_pool=pool,
        )
        self.assertIsNotNone(split_branch)
        assert split_branch is not None
        self.assertEqual((split_branch[0].task_i, split_branch[0].task_j), (1, 2))

    def test_sortie_profile_branch_mask_pruning_only_applies_separate(self):
        task_to_bit = {1: 0, 2: 1, 3: 2}
        both_12 = (1 << task_to_bit[1]) | (1 << task_to_bit[2])
        only_1 = 1 << task_to_bit[1]
        separate = (BranchConstraint("separate_vehicle", 1, 2),)
        same = (BranchConstraint("same_vehicle", 1, 2),)
        self.assertFalse(_sortie_profile_mask_allowed_by_branch(both_12, separate, task_to_bit))
        self.assertTrue(_sortie_profile_mask_allowed_by_branch(only_1, separate, task_to_bit))
        self.assertTrue(_sortie_profile_mask_allowed_by_branch(both_12, same, task_to_bit))
        self.assertNotEqual(_branch_constraints_cache_key(separate), _branch_constraints_cache_key(same))

    def test_shared_physical_catalog_key_and_branch_filter_are_opt_in(self):
        data = replace(load_future_data("very_small"), tasks=(1, 2), vehicles=(1,))
        task_order = (1, 2)
        separate = (BranchConstraint("separate_vehicle", 1, 2),)
        same = (BranchConstraint("same_vehicle", 1, 2),)
        config = JourneyPricingConfig(profile_labeling_physical_catalog_resume_enabled=True)

        default_separate_key = _sortie_label_physical_catalog_key(data, config, task_order, 2, separate)
        default_same_key = _sortie_label_physical_catalog_key(data, config, task_order, 2, same)
        self.assertNotEqual(default_separate_key, default_same_key)
        self.assertEqual(
            _sortie_label_physical_catalog_key(data, config, (1, 2), 2, tuple()),
            _sortie_label_physical_catalog_key(data, config, (2, 1), 2, tuple()),
        )

        shared_config = replace(config, profile_labeling_physical_catalog_share_across_branches_enabled=True)
        shared_key = _sortie_label_physical_catalog_key(data, shared_config, task_order, 2, tuple())
        self.assertEqual(
            shared_key,
            _sortie_label_physical_catalog_key(data, shared_config, task_order, 2, tuple()),
        )
        option = ArcOption("toy", "toy", tuple(), tau=1.0, energy=1.0, risk=0.0, distance=1.0, cost=1.0)
        both_profile = _SortieProfile(
            sequence=(1, 2),
            arc_options=(option,),
            lower_start=0.0,
            upper_start=10.0,
            end_offset=2.0,
            cost=2.0,
            mask=0b11,
            contribution=2.0,
        )
        one_profile = _SortieProfile(
            sequence=(1,),
            arc_options=(option,),
            lower_start=0.0,
            upper_start=10.0,
            end_offset=1.0,
            cost=1.0,
            mask=0b01,
            contribution=1.0,
        )
        filtered, _best, _cut_pruned = _filter_sortie_profile_catalog(
            [both_profile, one_profile],
            FutureDuals(
                cover={1: 10.0, 2: 10.0},
                task_vehicle={},
                sortie_count={},
                time_occupation={},
                ordering={},
                branches={},
            ),
            base_reduced_cost=-50.0,
            config=shared_config,
            journey_cut_duals={},
            journey_cuts=tuple(),
            task_to_bit={1: 0, 2: 1},
            branch_constraints=separate,
        )
        self.assertEqual([profile.sequence for profile in filtered], [(1,)])

    def test_journey_pricing_config_maps_shared_physical_catalog_option(self):
        config = {
            "journey_pricing_profile_labeling_enabled": True,
            "journey_pricing_profile_labeling_physical_catalog_resume_enabled": True,
            "journey_pricing_profile_labeling_physical_catalog_share_across_branches_enabled": True,
            "journey_pricing_profile_labeling_priority_future_dual_weight": 0.75,
            "journey_pricing_profile_labeling_priority_cut_dual_weight": 0.5,
            "journey_pricing_profile_dp_max_labels_per_mask": 8,
        }
        data = replace(load_future_data("very_small"), vehicles=(1,))
        pricing_config = _journey_pricing_config(data, config, 10.0, 10.0, 1.0e-6, 10.0, heuristic=False, cg_iter=1)
        self.assertTrue(pricing_config.profile_labeling_physical_catalog_resume_enabled)
        self.assertTrue(pricing_config.profile_labeling_physical_catalog_share_across_branches_enabled)
        self.assertAlmostEqual(pricing_config.profile_labeling_priority_future_dual_weight, 0.75)
        self.assertAlmostEqual(pricing_config.profile_labeling_priority_cut_dual_weight, 0.5)
        self.assertEqual(pricing_config.profile_dp_max_labels_per_mask, 8)

        branch_override = _journey_node_depth_pricing_config(
            {
                "journey_branch_pricing_profile_labeling_physical_catalog_share_across_branches_enabled": False,
            },
            pricing_config,
            depth=1,
        )
        self.assertFalse(branch_override.profile_labeling_physical_catalog_share_across_branches_enabled)

    def test_sortie_partial_label_priority_can_include_future_dual_lookahead(self):
        label = _SortiePartialLabel(
            sequence=(1,),
            mask=1,
            last=1,
            partial=_PartialNoWaitingPathProfile(
                arc_options=tuple(),
                lower_start=0.0,
                upper_start=100.0,
                offset=0.0,
                travel_cost=100.0,
                travel_energy=0.0,
                service_cost=0.0,
                service_energy=0.0,
            ),
        )
        duals = FutureDuals(
            cover={1: 0.0, 2: 60.0, 3: 40.0, 4: -100.0},
            task_vehicle={},
            sortie_count={1: 0.0},
            time_occupation={},
            ordering={},
            branches={},
        )

        self.assertAlmostEqual(_sortie_partial_label_priority(label, duals), 100.0)
        lookahead_priority = _sortie_partial_label_priority(
            label,
            duals,
            config=JourneyPricingConfig(profile_labeling_priority_future_dual_weight=0.5),
            task_order=(1, 2, 3, 4),
            max_tasks=3,
        )
        self.assertAlmostEqual(lookahead_priority, 50.0)
        cut_label = _SortiePartialLabel(
            sequence=(1, 2),
            mask=3,
            last=2,
            partial=_PartialNoWaitingPathProfile(
                arc_options=tuple(),
                lower_start=0.0,
                upper_start=100.0,
                offset=0.0,
                travel_cost=100.0,
                travel_energy=0.0,
                service_cost=0.0,
                service_energy=0.0,
            ),
        )
        cut_priority = _sortie_partial_label_priority(
            cut_label,
            duals,
            config=JourneyPricingConfig(profile_labeling_priority_cut_dual_weight=1.0),
            cut_duals={0: -30.0},
            cuts=(SubsetRowCut((1, 2), 2),),
            cut_masks=(3,),
        )
        self.assertAlmostEqual(cut_priority, 10.0)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_branch_node_requires_exact_pricing_before_branching(self):
        data = replace(load_future_data("very_small"), tasks=(1, 2), vehicles=(1, 2))

        def journey(jid: int, tasks: tuple[int, ...], cost: float) -> JourneyColumn:
            return JourneyColumn(
                id=jid,
                trips=tuple(),
                task_set=frozenset(tasks),
                start_time=0.0,
                end_time=1.0,
                travel_cost=cost,
                fixed_vehicle_cost=0.0,
                cost=cost,
                signature=("branch-node", jid, tasks),
            )

        j12 = journey(0, (1, 2), 10.0)
        j1 = journey(1, (1,), 9.0)
        j2 = journey(2, (2,), 9.0)
        pool = JourneyPool()
        for col in (j12, j1, j2):
            pool.add(col)
        fake_solution = SimpleNamespace(
            optimal=True,
            objective=10.0,
            duals=JourneyDuals(cover={1: 0.0, 2: 0.0}, fleet_limit=0.0),
            journey_values=[(j12, 0.5), (j1, 0.5), (j2, 0.5)],
            status="OPTIMAL",
            variable_count=3,
        )
        fake_pricing = JourneyPricingResult(
            journeys=[],
            exhausted=True,
            best_reduced_cost=0.0,
            generated_sequences=3,
            evaluated_timed_trips=3,
            candidate_trips=0,
            selected_trips=0,
            status="OPTIMAL",
            reason="direct_label_no_negative_journey",
            completion_bound_enabled=True,
            global_certificate_capable=True,
        )
        fake_pool_mip = SimpleNamespace(
            status="OPTIMAL",
            lp_objective=10.0,
            mip_objective=None,
            selected_journeys=[],
        )
        with tempfile.TemporaryDirectory() as tmp:
            logger = FutureLogger(Path(tmp) / "branch_node.jsonl", console=False)
            try:
                with patch("BPC_future.solver.journey_driver.solve_journey_rmp", return_value=fake_solution), patch(
                    "BPC_future.solver.journey_driver.price_journeys", return_value=fake_pricing
                ), patch("BPC_future.solver.journey_driver.solve_journey_pool_master", return_value=fake_pool_mip):
                    result = _process_journey_branch_node(
                        data,
                        {
                            "journey_heuristic_pricing_enabled": False,
                            "journey_dynamic_subset_row_cuts_enabled": False,
                            "journey_max_cg_iterations": 1,
                            "journey_pool_time_limit": 0.01,
                        },
                        pool,
                        [],
                        set(),
                        JourneyNode(0.0, 0, 0, tuple()),
                        math.inf,
                        {},
                        len(data.vehicles),
                        logger,
                        JourneyBranchStats(),
                        deadline=time.perf_counter() + 10.0,
                        bucket=1.0,
                        start_step=1.0,
                        eps=1.0e-6,
                    )
            finally:
                logger.close()
        self.assertEqual(result["status"], "COMPLETE")
        self.assertFalse(result["integral"])
        self.assertEqual(result["bound"], 10.0)
        branch = _choose_journey_branch(data, result["solution"].journey_values, tuple(), 1.0e-6)
        self.assertIsNotNone(branch)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_branch_node_reuses_pricing_trip_cache_across_cg_rounds(self):
        data = replace(load_future_data("very_small"), tasks=(1,), vehicles=(1,))
        base_journey = JourneyColumn(
            id=0,
            trips=tuple(),
            task_set=frozenset({1}),
            start_time=0.0,
            end_time=1.0,
            travel_cost=2.0,
            fixed_vehicle_cost=0.0,
            cost=2.0,
            signature=("base-cache",),
        )
        priced_journey = JourneyColumn(
            id=1,
            trips=tuple(),
            task_set=frozenset({1}),
            start_time=0.0,
            end_time=1.0,
            travel_cost=1.0,
            fixed_vehicle_cost=0.0,
            cost=1.0,
            signature=("priced-cache",),
        )
        pool = JourneyPool()
        pool.add(base_journey)
        fake_solution = SimpleNamespace(
            optimal=True,
            objective=2.0,
            duals=JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
            journey_values=[(base_journey, 1.0)],
            status="OPTIMAL",
            variable_count=1,
        )
        fake_pool_mip = SimpleNamespace(
            status="OPTIMAL",
            lp_objective=2.0,
            mip_objective=2.0,
            selected_journeys=[(base_journey, 1.0)],
        )
        cache_ids: list[int] = []

        def fake_price(*args, **kwargs):
            cache = kwargs["trip_cache"]
            cache_ids.append(id(cache))
            if len(cache_ids) == 1:
                self.assertNotIn("marker", cache)
                cache["marker"] = "kept"
                return JourneyPricingResult(
                    journeys=[priced_journey],
                    exhausted=False,
                    best_reduced_cost=-1.0,
                    generated_sequences=1,
                    evaluated_timed_trips=1,
                    candidate_trips=1,
                    selected_trips=1,
                    status="INCOMPLETE",
                    reason="negative",
                )
            self.assertEqual(cache.get("marker"), "kept")
            return JourneyPricingResult(
                journeys=[],
                exhausted=True,
                best_reduced_cost=0.0,
                generated_sequences=1,
                evaluated_timed_trips=1,
                candidate_trips=1,
                selected_trips=0,
                status="OPTIMAL",
                reason="direct_label_no_negative_journey",
                completion_bound_enabled=True,
                global_certificate_capable=True,
            )

        with tempfile.TemporaryDirectory() as tmp:
            logger = FutureLogger(Path(tmp) / "cache_node.jsonl", console=False)
            try:
                with patch("BPC_future.solver.journey_driver.solve_journey_rmp", return_value=fake_solution), patch(
                    "BPC_future.solver.journey_driver.price_journeys", side_effect=fake_price
                ), patch("BPC_future.solver.journey_driver.solve_journey_pool_master", return_value=fake_pool_mip):
                    result = _process_journey_branch_node(
                        data,
                        {
                            "journey_heuristic_pricing_enabled": False,
                            "journey_dynamic_subset_row_cuts_enabled": False,
                            "journey_max_cg_iterations": 2,
                            "journey_pool_time_limit": 0.01,
                        },
                        pool,
                        [],
                        set(),
                        JourneyNode(0.0, 0, 0, tuple()),
                        math.inf,
                        {},
                        len(data.vehicles),
                        logger,
                        JourneyBranchStats(),
                        deadline=time.perf_counter() + 10.0,
                        bucket=1.0,
                        start_step=1.0,
                        eps=1.0e-6,
                    )
            finally:
                logger.close()
        self.assertEqual(result["status"], "COMPLETE")
        self.assertGreaterEqual(len(cache_ids), 2)
        self.assertEqual(len(set(cache_ids)), 1)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_branch_node_trip_cache_override_is_branch_only(self):
        data = replace(load_future_data("very_small"), tasks=(1,), vehicles=(1,))
        base_journey = JourneyColumn(
            id=0,
            trips=tuple(),
            task_set=frozenset({1}),
            start_time=0.0,
            end_time=1.0,
            travel_cost=2.0,
            fixed_vehicle_cost=0.0,
            cost=2.0,
            signature=("base-cache-override",),
        )
        priced_journey = JourneyColumn(
            id=1,
            trips=tuple(),
            task_set=frozenset({1}),
            start_time=0.0,
            end_time=1.0,
            travel_cost=1.0,
            fixed_vehicle_cost=0.0,
            cost=1.0,
            signature=("priced-cache-override",),
        )
        fake_solution = SimpleNamespace(
            optimal=True,
            objective=2.0,
            duals=JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
            journey_values=[(base_journey, 1.0)],
            status="OPTIMAL",
            variable_count=1,
        )
        fake_pool_mip = SimpleNamespace(
            status="OPTIMAL",
            lp_objective=2.0,
            mip_objective=2.0,
            selected_journeys=[(base_journey, 1.0)],
        )

        def run_node(depth: int) -> tuple[list[int], list[bool]]:
            pool = JourneyPool()
            pool.add(base_journey)
            cache_ids: list[int] = []
            marker_seen: list[bool] = []
            cache_refs: list[dict] = []

            def fake_price(*args, **kwargs):
                cache = kwargs["trip_cache"]
                cache_refs.append(cache)
                cache_ids.append(id(cache))
                if len(cache_ids) == 1:
                    cache["marker"] = "kept"
                    return JourneyPricingResult(
                        journeys=[priced_journey],
                        exhausted=False,
                        best_reduced_cost=-1.0,
                        generated_sequences=1,
                        evaluated_timed_trips=1,
                        candidate_trips=1,
                        selected_trips=1,
                        status="INCOMPLETE",
                        reason="negative",
                    )
                marker_seen.append(cache.get("marker") == "kept")
                return JourneyPricingResult(
                    journeys=[],
                    exhausted=True,
                    best_reduced_cost=0.0,
                    generated_sequences=1,
                    evaluated_timed_trips=1,
                    candidate_trips=1,
                    selected_trips=0,
                    status="OPTIMAL",
                    reason="direct_label_no_negative_journey",
                    completion_bound_enabled=True,
                    global_certificate_capable=True,
                )

            with tempfile.TemporaryDirectory() as tmp:
                logger = FutureLogger(Path(tmp) / "cache_override_node.jsonl", console=False)
                try:
                    with patch("BPC_future.solver.journey_driver.solve_journey_rmp", return_value=fake_solution), patch(
                        "BPC_future.solver.journey_driver.price_journeys", side_effect=fake_price
                    ), patch("BPC_future.solver.journey_driver.solve_journey_pool_master", return_value=fake_pool_mip):
                        result = _process_journey_branch_node(
                            data,
                            {
                                "journey_heuristic_pricing_enabled": False,
                                "journey_dynamic_subset_row_cuts_enabled": False,
                                "journey_max_cg_iterations": 2,
                                "journey_pool_time_limit": 0.01,
                                "journey_pricing_trip_cache_enabled": False,
                                "journey_branch_pricing_trip_cache_enabled": True,
                            },
                            pool,
                            [],
                            set(),
                            JourneyNode(0.0, 0, depth, tuple()),
                            math.inf,
                            {},
                            len(data.vehicles),
                            logger,
                            JourneyBranchStats(),
                            deadline=time.perf_counter() + 10.0,
                            bucket=1.0,
                            start_step=1.0,
                            eps=1.0e-6,
                        )
                finally:
                    logger.close()
            self.assertEqual(result["status"], "COMPLETE")
            self.assertGreaterEqual(len(cache_ids), 2)
            return cache_ids, marker_seen

        root_cache_ids, root_marker_seen = run_node(depth=0)
        self.assertEqual(len(set(root_cache_ids)), len(root_cache_ids))
        self.assertEqual(root_marker_seen, [False])

        branch_cache_ids, branch_marker_seen = run_node(depth=1)
        self.assertEqual(len(set(branch_cache_ids)), 1)
        self.assertEqual(branch_marker_seen, [True])

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_branch_nodes_share_pricing_cache_when_enabled(self):
        data = replace(load_future_data("very_small"), tasks=(1,), vehicles=(1,))
        base_journey = JourneyColumn(
            id=0,
            trips=tuple(),
            task_set=frozenset({1}),
            start_time=0.0,
            end_time=1.0,
            travel_cost=2.0,
            fixed_vehicle_cost=0.0,
            cost=2.0,
            signature=("cross-node-cache-base",),
        )
        fake_solution = SimpleNamespace(
            optimal=True,
            objective=2.0,
            duals=JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
            journey_values=[(base_journey, 1.0)],
            status="OPTIMAL",
            variable_count=1,
        )
        fake_pool_mip = SimpleNamespace(
            status="OPTIMAL",
            lp_objective=2.0,
            mip_objective=2.0,
            selected_journeys=[(base_journey, 1.0)],
        )
        shared_cache: dict[tuple, object] = {}
        marker_seen: list[bool] = []

        def fake_price(*args, **kwargs):
            cache = kwargs["trip_cache"]
            marker_seen.append(cache.get("marker") == "kept")
            cache["marker"] = "kept"
            return JourneyPricingResult(
                journeys=[],
                exhausted=True,
                best_reduced_cost=0.0,
                generated_sequences=1,
                evaluated_timed_trips=1,
                candidate_trips=1,
                selected_trips=0,
                status="OPTIMAL",
                reason="direct_label_no_negative_journey",
                completion_bound_enabled=True,
                global_certificate_capable=True,
            )

        with tempfile.TemporaryDirectory() as tmp:
            logger = FutureLogger(Path(tmp) / "cross_node_cache.jsonl", console=False)
            try:
                with patch("BPC_future.solver.journey_driver.solve_journey_rmp", return_value=fake_solution), patch(
                    "BPC_future.solver.journey_driver.price_journeys", side_effect=fake_price
                ), patch("BPC_future.solver.journey_driver.solve_journey_pool_master", return_value=fake_pool_mip):
                    for node_id in (1, 2):
                        pool = JourneyPool()
                        pool.add(base_journey)
                        result = _process_journey_branch_node(
                            data,
                            {
                                "journey_heuristic_pricing_enabled": False,
                                "journey_dynamic_subset_row_cuts_enabled": False,
                                "journey_max_cg_iterations": 1,
                                "journey_pool_time_limit": 0.01,
                                "journey_branch_pricing_cross_node_cache_enabled": True,
                            },
                            pool,
                            [],
                            set(),
                            JourneyNode(0.0, node_id, 1, tuple()),
                            math.inf,
                            {},
                            len(data.vehicles),
                            logger,
                            JourneyBranchStats(),
                            deadline=time.perf_counter() + 10.0,
                            bucket=1.0,
                            start_step=1.0,
                            eps=1.0e-6,
                            shared_pricing_trip_cache=shared_cache,
                            shared_pricing_resource_cache={},
                        )
                        self.assertEqual(result["status"], "COMPLETE")
            finally:
                logger.close()
        self.assertEqual(marker_seen, [False, True])

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_root_node_ignores_cross_node_pricing_cache(self):
        data = replace(load_future_data("very_small"), tasks=(1,), vehicles=(1,))
        base_journey = JourneyColumn(
            id=0,
            trips=tuple(),
            task_set=frozenset({1}),
            start_time=0.0,
            end_time=1.0,
            travel_cost=2.0,
            fixed_vehicle_cost=0.0,
            cost=2.0,
            signature=("root-cross-node-cache-base",),
        )
        pool = JourneyPool()
        pool.add(base_journey)
        fake_solution = SimpleNamespace(
            optimal=True,
            objective=2.0,
            duals=JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
            journey_values=[(base_journey, 1.0)],
            status="OPTIMAL",
            variable_count=1,
        )
        fake_pool_mip = SimpleNamespace(
            status="OPTIMAL",
            lp_objective=2.0,
            mip_objective=2.0,
            selected_journeys=[(base_journey, 1.0)],
        )
        shared_cache: dict[tuple, object] = {"marker": "shared"}
        marker_seen: list[bool] = []

        def fake_price(*args, **kwargs):
            marker_seen.append(kwargs["trip_cache"].get("marker") == "shared")
            return JourneyPricingResult(
                journeys=[],
                exhausted=True,
                best_reduced_cost=0.0,
                generated_sequences=1,
                evaluated_timed_trips=1,
                candidate_trips=1,
                selected_trips=0,
                status="OPTIMAL",
                reason="direct_label_no_negative_journey",
                completion_bound_enabled=True,
                global_certificate_capable=True,
            )

        with tempfile.TemporaryDirectory() as tmp:
            logger = FutureLogger(Path(tmp) / "root_cross_node_cache.jsonl", console=False)
            try:
                with patch("BPC_future.solver.journey_driver.solve_journey_rmp", return_value=fake_solution), patch(
                    "BPC_future.solver.journey_driver.price_journeys", side_effect=fake_price
                ), patch("BPC_future.solver.journey_driver.solve_journey_pool_master", return_value=fake_pool_mip):
                    result = _process_journey_branch_node(
                        data,
                        {
                            "journey_heuristic_pricing_enabled": False,
                            "journey_dynamic_subset_row_cuts_enabled": False,
                            "journey_max_cg_iterations": 1,
                            "journey_pool_time_limit": 0.01,
                            "journey_branch_pricing_cross_node_cache_enabled": True,
                        },
                        pool,
                        [],
                        set(),
                        JourneyNode(0.0, 0, 0, tuple()),
                        math.inf,
                        {},
                        len(data.vehicles),
                        logger,
                        JourneyBranchStats(),
                        deadline=time.perf_counter() + 10.0,
                        bucket=1.0,
                        start_step=1.0,
                        eps=1.0e-6,
                        shared_pricing_trip_cache=shared_cache,
                        shared_pricing_resource_cache={},
                    )
            finally:
                logger.close()
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(marker_seen, [False])

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_branch_node_skips_pool_integer_when_bound_fathoms(self):
        data = replace(load_future_data("very_small"), tasks=(1,), vehicles=(1,))
        base_journey = JourneyColumn(
            id=0,
            trips=tuple(),
            task_set=frozenset({1}),
            start_time=0.0,
            end_time=1.0,
            travel_cost=10.0,
            fixed_vehicle_cost=0.0,
            cost=10.0,
            signature=("bound-fathom-skip",),
        )
        pool = JourneyPool()
        pool.add(base_journey)
        fake_solution = SimpleNamespace(
            optimal=True,
            objective=10.0,
            duals=JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
            journey_values=[(base_journey, 1.0)],
            status="OPTIMAL",
            variable_count=1,
        )
        exhausted_pricing = JourneyPricingResult(
            journeys=[],
            exhausted=True,
            best_reduced_cost=0.0,
            generated_sequences=1,
            evaluated_timed_trips=1,
            candidate_trips=1,
            selected_trips=0,
            status="OPTIMAL",
            reason="direct_label_no_negative_journey",
            completion_bound_enabled=True,
            global_certificate_capable=True,
        )

        with tempfile.TemporaryDirectory() as tmp:
            logger = FutureLogger(Path(tmp) / "bound_fathom_skip.jsonl", console=False)
            try:
                with patch("BPC_future.solver.journey_driver.solve_journey_rmp", return_value=fake_solution), patch(
                    "BPC_future.solver.journey_driver.price_journeys", return_value=exhausted_pricing
                ), patch("BPC_future.solver.journey_driver.solve_journey_pool_master") as pool_master:
                    result = _process_journey_branch_node(
                        data,
                        {
                            "journey_heuristic_pricing_enabled": False,
                            "journey_dynamic_subset_row_cuts_enabled": False,
                            "journey_max_cg_iterations": 1,
                            "journey_pool_integer_heuristic_enabled": False,
                            "journey_skip_pool_integer_when_bound_fathoms_enabled": True,
                        },
                        pool,
                        [],
                        set(),
                        JourneyNode(0.0, 0, 0, tuple()),
                        9.0,
                        {1: [SimpleNamespace(tasks=(1,))]},
                        len(data.vehicles),
                        logger,
                        JourneyBranchStats(),
                        deadline=time.perf_counter() + 10.0,
                        bucket=1.0,
                        start_step=1.0,
                        eps=1.0e-6,
                    )
            finally:
                logger.close()
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(result["bound"], 10.0)
        self.assertEqual(pool_master.call_count, 0)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_early_branch_uses_inherited_bound_not_unpriced_rmp_objective(self):
        data = replace(load_future_data("very_small"), tasks=(1, 2), vehicles=(1, 2))
        j12 = JourneyColumn(
            id=0,
            trips=tuple(),
            task_set=frozenset({1, 2}),
            start_time=0.0,
            end_time=1.0,
            travel_cost=10.0,
            fixed_vehicle_cost=0.0,
            cost=10.0,
            signature=("early-j12",),
        )
        j1 = JourneyColumn(
            id=1,
            trips=tuple(),
            task_set=frozenset({1}),
            start_time=0.0,
            end_time=1.0,
            travel_cost=9.0,
            fixed_vehicle_cost=0.0,
            cost=9.0,
            signature=("early-j1",),
        )
        priced = JourneyColumn(
            id=2,
            trips=tuple(),
            task_set=frozenset({2}),
            start_time=0.0,
            end_time=1.0,
            travel_cost=1.0,
            fixed_vehicle_cost=0.0,
            cost=1.0,
            signature=("early-priced",),
        )
        pool = JourneyPool()
        for col in (j12, j1):
            pool.add(col)
        fake_solution = SimpleNamespace(
            optimal=True,
            objective=10.0,
            duals=JourneyDuals(cover={1: 0.0, 2: 0.0}, fleet_limit=0.0),
            journey_values=[(j12, 0.5), (j1, 0.5)],
            status="OPTIMAL",
            variable_count=2,
        )
        fake_pricing = JourneyPricingResult(
            journeys=[priced],
            exhausted=False,
            best_reduced_cost=-1.0,
            generated_sequences=1,
            evaluated_timed_trips=1,
            candidate_trips=1,
            selected_trips=1,
            status="INCOMPLETE",
            reason="negative",
        )
        with tempfile.TemporaryDirectory() as tmp:
            logger = FutureLogger(Path(tmp) / "early_branch.jsonl", console=False)
            try:
                with patch("BPC_future.solver.journey_driver.solve_journey_rmp", return_value=fake_solution), patch(
                    "BPC_future.solver.journey_driver.price_journeys", return_value=fake_pricing
                ):
                    result = _process_journey_branch_node(
                        data,
                        {
                            "journey_heuristic_pricing_enabled": False,
                            "journey_dynamic_subset_row_cuts_enabled": False,
                            "journey_max_cg_iterations": 5,
                            "journey_early_branching_enabled": True,
                            "journey_early_branching_min_cg_iter": 1,
                            "journey_early_branching_max_depth": 0,
                        },
                        pool,
                        [],
                        set(),
                        JourneyNode(7.0, 0, 0, tuple()),
                        math.inf,
                        {},
                        len(data.vehicles),
                        logger,
                        JourneyBranchStats(),
                        deadline=time.perf_counter() + 10.0,
                        bucket=1.0,
                        start_step=1.0,
                        eps=1.0e-6,
                    )
            finally:
                logger.close()
        self.assertEqual(result["status"], "BRANCH")
        self.assertEqual(result["bound"], 7.0)
        self.assertFalse(result["exact_bound"])

    def test_journey_early_branch_child_min_iter_and_child_order(self):
        data = replace(load_future_data("very_small"), tasks=(1, 2, 3), vehicles=(1, 2))

        def journey(jid: int, tasks: tuple[int, ...]) -> JourneyColumn:
            return JourneyColumn(
                id=jid,
                trips=tuple(),
                task_set=frozenset(tasks),
                start_time=0.0,
                end_time=1.0,
                travel_cost=1.0,
                fixed_vehicle_cost=0.0,
                cost=1.0,
                signature=("order", jid, tasks),
            )

        pool = JourneyPool()
        for col in (journey(0, (1,)), journey(1, (2,)), journey(2, (1, 2)), journey(3, (1, 3))):
            pool.add(col)
        same = BranchConstraint("same_vehicle", 1, 2)
        separate = BranchConstraint("separate_vehicle", 1, 2)
        ordered = _ordered_journey_child_constraints(pool, tuple(), (same, separate))
        self.assertEqual(ordered[0][0].kind, "same_vehicle")
        self.assertLessEqual(ordered[0][1], ordered[1][1])

        low_same_values = [(journey(4, (1, 2)), 0.4), (journey(5, (1,)), 0.6)]
        self.assertAlmostEqual(_journey_branch_same_mass(low_same_values, (same, separate)), 0.4)
        lp_order = _journey_child_constraint_order(
            pool,
            tuple(),
            (same, separate),
            by_width=False,
            priority_mode="lp_rounding",
            journey_values=low_same_values,
        )
        self.assertEqual(lp_order[0][0].kind, "separate_vehicle")
        high_same_values = [(journey(6, (1, 2)), 0.6), (journey(7, (1,)), 0.4)]
        lp_order = _journey_child_constraint_order(
            pool,
            tuple(),
            (same, separate),
            by_width=False,
            priority_mode="lp_rounding",
            journey_values=high_same_values,
        )
        self.assertEqual(lp_order[0][0].kind, "same_vehicle")
        tie_order = _journey_child_constraint_order(
            pool,
            tuple(),
            (same, separate),
            by_width=False,
            priority_mode="lp_rounding_wide_tie",
            journey_values=[(journey(8, (1, 2)), 0.5), (journey(9, (1,)), 0.5)],
        )
        self.assertGreaterEqual(tie_order[0][1], tie_order[1][1])

        fractional_solution = SimpleNamespace(
            journey_values=[(journey(4, (1, 2)), 0.5), (journey(5, (1,)), 0.5)]
        )
        node = JourneyNode(0.0, 1, 1, tuple())
        config = {
            "journey_early_branching_enabled": True,
            "journey_early_branching_min_cg_iter": 12,
            "journey_early_branching_child_min_cg_iter": 4,
            "journey_early_branching_max_depth": 1,
        }
        self.assertFalse(_journey_should_early_branch(config, node, 3, fractional_solution, 1.0e-6))
        self.assertTrue(_journey_should_early_branch(config, node, 4, fractional_solution, 1.0e-6))

    def test_certificate_pricing_fast_return_is_certificate_only(self):
        base = JourneyPricingConfig(
            early_return_negative=False,
            early_return_negative_min_count=8,
            streaming_min_negative_batch=8,
            streaming_min_returned_journeys=4,
        )
        updated, mode = _journey_certificate_pricing_config(
            {"journey_certificate_fast_negative_return_enabled": True},
            base,
            certificate_candidate=False,
            certificate_flat_rounds=0,
        )
        self.assertEqual(updated, base)
        self.assertEqual(mode, {})

        updated, mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_fast_negative_return_enabled": True,
                "journey_certificate_fast_negative_return_min_count": 1,
            },
            base,
            certificate_candidate=True,
            certificate_flat_rounds=0,
        )
        self.assertTrue(mode["fast_negative_return"])
        self.assertTrue(updated.early_return_negative)
        self.assertEqual(updated.early_return_negative_min_count, 1)
        self.assertEqual(updated.streaming_min_negative_batch, 1)
        self.assertEqual(updated.streaming_min_returned_journeys, 4)

        updated, mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_fast_negative_return_enabled": True,
                "journey_certificate_fast_negative_return_min_count": 1,
                "journey_certificate_fast_negative_return_min_proof_rounds": 2,
            },
            base,
            certificate_candidate=True,
            certificate_flat_rounds=1,
        )
        self.assertEqual(updated, base)
        self.assertEqual(mode, {})

        updated, mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_fast_negative_return_enabled": True,
                "journey_certificate_fast_negative_return_min_count": 1,
                "journey_certificate_fast_negative_return_min_proof_rounds": 2,
            },
            base,
            certificate_candidate=True,
            certificate_flat_rounds=2,
        )
        self.assertTrue(mode["fast_negative_return"])

    def test_certificate_full_scan_overrides_fast_return_after_flat_rounds(self):
        base = JourneyPricingConfig(
            streaming_pricing_enabled=True,
            early_return_negative=True,
            profile_generation_time_fraction=0.5,
            max_sequences=10,
            max_timed_evaluations=20,
        )
        updated, mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_fast_negative_return_enabled": True,
                "journey_certificate_fast_negative_return_min_count": 1,
                "journey_certificate_full_scan_after_flat_rounds": 1,
                "journey_certificate_full_scan_max_sequences": 0,
                "journey_certificate_full_scan_max_timed_evaluations": 0,
            },
            base,
            certificate_candidate=True,
            certificate_flat_rounds=1,
        )
        self.assertTrue(mode["fast_negative_return"])
        self.assertTrue(mode["full_scan"])
        self.assertFalse(updated.streaming_pricing_enabled)
        self.assertFalse(updated.early_return_negative)
        self.assertEqual(updated.profile_generation_time_fraction, 1.0)
        self.assertEqual(updated.max_sequences, 0)
        self.assertEqual(updated.max_timed_evaluations, 0)

    def test_certificate_completion_bound_is_tail_and_root_only(self):
        base = JourneyPricingConfig(direct_journey_label_completion_bound_enabled=False)
        updated, mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_time_buckets": 12,
            },
            base,
            certificate_candidate=False,
            certificate_flat_rounds=0,
        )
        self.assertEqual(updated, base)
        self.assertEqual(mode, {})

        updated, mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_exact_proof_enabled": True,
                "journey_certificate_completion_bound_root_only": False,
                "journey_certificate_completion_bound_time_buckets": 12,
            },
            base,
            certificate_candidate=False,
            certificate_flat_rounds=0,
            depth=0,
        )
        self.assertEqual(updated, base)
        self.assertEqual(mode, {})

        updated, mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_exact_proof_enabled": True,
                "journey_certificate_completion_bound_root_only": False,
                "journey_certificate_completion_bound_time_buckets": 12,
                "journey_certificate_fast_negative_return_enabled": True,
            },
            base,
            certificate_candidate=False,
            certificate_flat_rounds=0,
            depth=1,
        )
        self.assertEqual(updated, base)
        self.assertEqual(mode, {})

        updated, mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_exact_proof_enabled": True,
                "journey_certificate_completion_bound_root_only": False,
                "journey_certificate_completion_bound_time_buckets": 12,
                "journey_certificate_fast_negative_return_enabled": True,
            },
            base,
            certificate_candidate=False,
            certificate_flat_rounds=0,
            certificate_no_column_rounds=1,
            depth=1,
        )
        self.assertEqual(updated, base)
        self.assertEqual(mode, {})

        updated, mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_exact_proof_enabled": True,
                "journey_certificate_completion_bound_root_only": False,
                "journey_certificate_completion_bound_time_buckets": 12,
                "journey_certificate_fast_negative_return_enabled": True,
            },
            base,
            certificate_candidate=False,
            certificate_flat_rounds=0,
            certificate_no_column_rounds=1,
            depth=1,
            completion_bound_phase="after_retry",
        )
        self.assertTrue(updated.direct_journey_label_completion_bound_enabled)
        self.assertTrue(mode["completion_bound"])
        self.assertNotIn("fast_negative_return", mode)

        updated, mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_after_retry_enabled": True,
                "journey_certificate_completion_bound_final_probe_only": True,
                "journey_certificate_completion_bound_time_buckets": 6,
                "journey_certificate_completion_bound_energy_buckets": 6,
                "journey_certificate_completion_bound_max_sequences": 1234,
                "journey_certificate_completion_bound_max_dp_states": 5678,
                "journey_certificate_completion_bound_partial_max_states": 910,
                "journey_certificate_completion_bound_two_cycle_enabled": True,
                "journey_certificate_completion_bound_two_cycle_max_states": 1112,
                "journey_certificate_completion_bound_next_sortie_trip_return_limit": 222,
            },
            base,
            certificate_candidate=False,
            certificate_flat_rounds=0,
            certificate_no_column_rounds=1,
            depth=0,
            completion_bound_phase="after_retry",
        )
        self.assertTrue(updated.direct_journey_label_completion_bound_enabled)
        self.assertTrue(mode["completion_bound"])
        self.assertEqual(updated.max_sequences, 1234)
        self.assertEqual(updated.max_dp_states, 5678)
        self.assertEqual(updated.direct_journey_label_partial_max_states, 910)
        self.assertEqual(mode["completion_bound_max_sequences"], 1234)
        self.assertEqual(mode["completion_bound_max_dp_states"], 5678)
        self.assertEqual(mode["completion_bound_partial_max_states"], 910)
        self.assertTrue(updated.direct_journey_label_completion_bound_two_cycle_enabled)
        self.assertEqual(updated.direct_journey_label_completion_bound_two_cycle_max_states, 1112)
        self.assertTrue(mode["completion_bound_two_cycle"])
        self.assertEqual(mode["completion_bound_two_cycle_max_states"], 1112)
        self.assertEqual(updated.direct_journey_label_next_sortie_trip_return_limit, 222)
        self.assertEqual(mode["completion_bound_next_sortie_trip_return_limit"], 222)
        self.assertEqual(updated.direct_journey_label_early_return_negative_min_count, 0)
        self.assertFalse(updated.direct_journey_label_next_sortie_cache_enabled)
        self.assertFalse(mode["completion_bound_next_sortie_cache"])

        hidden_updated, hidden_mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_after_retry_enabled": True,
                "journey_certificate_completion_bound_final_probe_only": True,
                "journey_certificate_completion_bound_time_buckets": 6,
                "journey_certificate_completion_bound_energy_buckets": 6,
                "journey_certificate_completion_bound_hidden_negative_enabled": True,
                "journey_certificate_completion_bound_hidden_negative_min_journeys": 1,
                "journey_certificate_completion_bound_hidden_negative_max_returned_journeys": 4,
                "journey_certificate_completion_bound_hidden_negative_grace_time": 0.25,
            },
            base,
            certificate_candidate=False,
            certificate_flat_rounds=0,
            certificate_no_column_rounds=1,
            depth=0,
            completion_bound_phase="after_retry",
        )
        self.assertTrue(hidden_mode["completion_bound"])
        self.assertTrue(hidden_updated.direct_journey_label_global_certificate_enabled)
        self.assertTrue(hidden_mode["completion_bound_hidden_negative"])
        self.assertTrue(hidden_updated.direct_journey_label_early_return_negative)
        self.assertEqual(hidden_updated.direct_journey_label_early_return_negative_min_count, 1)
        self.assertEqual(hidden_updated.direct_journey_label_early_return_negative_grace_time, 0.25)
        self.assertEqual(hidden_updated.max_returned_journeys, 4)
        self.assertEqual(hidden_mode["completion_bound_hidden_negative_grace_time"], 0.25)

        harvest_updated, harvest_mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_after_retry_enabled": True,
                "journey_certificate_completion_bound_final_probe_only": True,
                "journey_certificate_completion_bound_time_buckets": 6,
                "journey_certificate_completion_bound_energy_buckets": 6,
                "journey_certificate_completion_bound_hidden_negative_enabled": True,
                "journey_certificate_completion_bound_hidden_negative_min_journeys": 2,
                "journey_certificate_completion_bound_hidden_negative_max_returned_journeys": 4,
                "journey_certificate_completion_bound_diverse_harvest_enabled": True,
                "journey_certificate_completion_bound_diverse_harvest_min_journeys": 12,
                "journey_certificate_completion_bound_diverse_harvest_max_returned_journeys": 30,
                "journey_certificate_completion_bound_diverse_harvest_overlap_threshold": 0.35,
                "journey_certificate_completion_bound_diverse_harvest_top_k_strongest": 6,
                "journey_certificate_completion_bound_diverse_harvest_min_fill": 18,
                "journey_certificate_completion_bound_diverse_harvest_min_priority_task_sets": 3,
                "journey_certificate_completion_bound_diverse_harvest_priority_overlap_threshold": 0.55,
                "journey_certificate_completion_bound_diverse_harvest_support_aware_enabled": True,
                "journey_certificate_completion_bound_diverse_harvest_support_overlap_threshold": 0.45,
                "journey_certificate_completion_bound_diverse_harvest_replacement_cap": 7,
                "journey_certificate_completion_bound_diverse_harvest_strong_replacement_threshold": -0.0002,
                "journey_certificate_completion_bound_mask_closure_enabled": True,
                "journey_certificate_completion_bound_mask_closure_max_masks": 4,
                "journey_certificate_completion_bound_mask_closure_max_columns_per_mask": 3,
                "journey_certificate_completion_bound_diverse_harvest_max_containment": 0.75,
                "journey_certificate_completion_bound_diverse_harvest_allow_duplicate_task_sets": True,
                "journey_certificate_completion_bound_diverse_harvest_grace_time": 0.75,
                "journey_certificate_completion_bound_diverse_harvest_soft_return_min_journeys": 5,
                "journey_certificate_completion_bound_diverse_harvest_soft_return_min_new_task_sets": 2,
                "journey_certificate_completion_bound_diverse_harvest_soft_return_after_time": 10.0,
                "journey_certificate_completion_bound_diverse_harvest_soft_return_remaining_time": 8.0,
                "journey_certificate_completion_bound_diverse_harvest_duplicate_saturation_after_time": 4.0,
            },
            base,
            certificate_candidate=False,
            certificate_flat_rounds=0,
            certificate_no_column_rounds=1,
            depth=0,
            completion_bound_phase="after_retry",
        )
        self.assertTrue(harvest_updated.direct_journey_label_diverse_harvest_enabled)
        self.assertEqual(harvest_updated.direct_journey_label_early_return_negative_min_count, 12)
        self.assertEqual(harvest_updated.max_returned_journeys, 30)
        self.assertAlmostEqual(harvest_updated.direct_journey_label_diverse_harvest_overlap_threshold, 0.35)
        self.assertEqual(harvest_updated.direct_journey_label_diverse_harvest_top_k_strongest, 6)
        self.assertEqual(harvest_updated.direct_journey_label_diverse_harvest_min_fill, 18)
        self.assertEqual(harvest_updated.direct_journey_label_diverse_harvest_min_priority_task_sets, 3)
        self.assertAlmostEqual(
            harvest_updated.direct_journey_label_diverse_harvest_priority_overlap_threshold,
            0.55,
        )
        self.assertTrue(harvest_updated.direct_journey_label_diverse_harvest_support_aware_enabled)
        self.assertAlmostEqual(harvest_updated.direct_journey_label_diverse_harvest_support_overlap_threshold, 0.45)
        self.assertEqual(harvest_updated.direct_journey_label_diverse_harvest_replacement_cap, 7)
        self.assertAlmostEqual(
            harvest_updated.direct_journey_label_diverse_harvest_strong_replacement_threshold,
            -0.0002,
        )
        self.assertTrue(harvest_updated.direct_journey_label_mask_closure_enabled)
        self.assertEqual(harvest_updated.direct_journey_label_mask_closure_max_masks, 4)
        self.assertEqual(harvest_updated.direct_journey_label_mask_closure_max_columns_per_mask, 3)
        self.assertAlmostEqual(harvest_updated.direct_journey_label_diverse_harvest_max_containment, 0.75)
        self.assertTrue(harvest_updated.direct_journey_label_diverse_harvest_allow_duplicate_task_sets)
        self.assertAlmostEqual(harvest_updated.direct_journey_label_early_return_negative_grace_time, 0.75)
        self.assertEqual(harvest_updated.direct_journey_label_diverse_harvest_soft_return_min_count, 5)
        self.assertEqual(harvest_updated.direct_journey_label_diverse_harvest_soft_return_min_new_task_sets, 2)
        self.assertAlmostEqual(harvest_updated.direct_journey_label_diverse_harvest_soft_return_after_time, 10.0)
        self.assertAlmostEqual(harvest_updated.direct_journey_label_diverse_harvest_soft_return_remaining_time, 8.0)
        self.assertAlmostEqual(
            harvest_updated.direct_journey_label_diverse_harvest_duplicate_saturation_after_time,
            4.0,
        )
        self.assertTrue(harvest_mode["completion_bound_diverse_harvest"])
        self.assertEqual(harvest_mode["completion_bound_diverse_harvest_max_returned_journeys"], 30)
        self.assertEqual(harvest_mode["completion_bound_diverse_harvest_top_k_strongest"], 6)
        self.assertEqual(harvest_mode["completion_bound_diverse_harvest_min_fill"], 18)
        self.assertEqual(harvest_mode["completion_bound_diverse_harvest_min_priority_task_sets"], 3)
        self.assertEqual(harvest_mode["completion_bound_diverse_harvest_priority_overlap_threshold"], 0.55)
        self.assertTrue(harvest_mode["completion_bound_diverse_harvest_support_aware"])
        self.assertEqual(harvest_mode["completion_bound_diverse_harvest_support_overlap_threshold"], 0.45)
        self.assertEqual(harvest_mode["completion_bound_diverse_harvest_replacement_cap"], 7)
        self.assertEqual(harvest_mode["completion_bound_diverse_harvest_strong_replacement_threshold"], -0.0002)
        self.assertTrue(harvest_mode["completion_bound_mask_closure"])
        self.assertEqual(harvest_mode["completion_bound_mask_closure_max_masks"], 4)
        self.assertEqual(harvest_mode["completion_bound_mask_closure_max_columns_per_mask"], 3)
        self.assertAlmostEqual(harvest_mode["completion_bound_diverse_harvest_max_containment"], 0.75)
        self.assertTrue(harvest_mode["completion_bound_diverse_harvest_allow_duplicate_task_sets"])
        self.assertEqual(harvest_mode["completion_bound_diverse_harvest_soft_return_min_journeys"], 5)
        self.assertEqual(harvest_mode["completion_bound_diverse_harvest_soft_return_min_new_task_sets"], 2)
        self.assertEqual(harvest_mode["completion_bound_diverse_harvest_soft_return_after_time"], 10.0)
        self.assertEqual(harvest_mode["completion_bound_diverse_harvest_duplicate_saturation_after_time"], 4.0)

        branch_updated, branch_mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_after_retry_enabled": True,
                "journey_certificate_completion_bound_final_probe_only": True,
                "journey_certificate_completion_bound_root_only": False,
                "journey_certificate_completion_bound_time_buckets": 6,
                "journey_certificate_completion_bound_energy_buckets": 6,
                "journey_certificate_completion_bound_two_cycle_enabled": True,
            },
            base,
            certificate_candidate=False,
            certificate_flat_rounds=0,
            certificate_no_column_rounds=1,
            depth=1,
            completion_bound_phase="after_retry",
        )
        self.assertTrue(branch_updated.direct_journey_label_completion_bound_enabled)
        self.assertFalse(branch_updated.direct_journey_label_completion_bound_two_cycle_enabled)
        self.assertFalse(branch_mode["completion_bound_two_cycle"])

        branch_two_cycle_updated, branch_two_cycle_mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_after_retry_enabled": True,
                "journey_certificate_completion_bound_final_probe_only": True,
                "journey_certificate_completion_bound_root_only": False,
                "journey_certificate_completion_bound_time_buckets": 6,
                "journey_certificate_completion_bound_energy_buckets": 6,
                "journey_certificate_completion_bound_two_cycle_enabled": True,
                "journey_certificate_completion_bound_two_cycle_branch_enabled": True,
            },
            base,
            certificate_candidate=False,
            certificate_flat_rounds=0,
            certificate_no_column_rounds=1,
            depth=1,
            completion_bound_phase="after_retry",
        )
        self.assertTrue(branch_two_cycle_updated.direct_journey_label_completion_bound_enabled)
        self.assertTrue(branch_two_cycle_updated.direct_journey_label_completion_bound_two_cycle_enabled)
        self.assertTrue(branch_two_cycle_mode["completion_bound_two_cycle"])

        updated, mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_time_buckets": 12,
            },
            base,
            certificate_candidate=True,
            certificate_flat_rounds=0,
            depth=0,
        )
        self.assertEqual(updated, base)
        self.assertEqual(mode, {})

        updated, mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_time_buckets": 12,
                "journey_certificate_completion_bound_min_flat_rounds": 2,
            },
            base,
            certificate_candidate=True,
            certificate_flat_rounds=1,
            depth=0,
            completion_bound_phase="after_retry",
        )
        self.assertFalse(updated.direct_journey_label_completion_bound_enabled)
        self.assertNotIn("completion_bound", mode)

        updated, mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_time_buckets": 12,
                "journey_certificate_completion_bound_audit_enabled": True,
            },
            base,
            certificate_candidate=True,
            certificate_flat_rounds=2,
            depth=0,
            completion_bound_phase="after_retry",
        )
        self.assertTrue(mode["completion_bound"])
        self.assertTrue(updated.direct_journey_label_pricing_enabled)
        self.assertTrue(updated.direct_journey_label_global_certificate_enabled)
        self.assertTrue(updated.direct_journey_label_completion_bound_enabled)
        self.assertEqual(updated.direct_journey_label_completion_bound_time_buckets, 12)
        self.assertEqual(updated.direct_journey_label_completion_bound_energy_buckets, 10)
        self.assertTrue(updated.direct_journey_label_completion_bound_partial_pruning_enabled)
        self.assertTrue(updated.direct_journey_label_completion_bound_audit_enabled)
        self.assertFalse(updated.direct_journey_label_completion_bound_unique_task_helper_enabled)
        self.assertFalse(updated.direct_journey_label_completion_bound_unique_route_helper_enabled)
        self.assertEqual(mode["completion_bound_energy_buckets"], 10)
        self.assertTrue(mode["completion_bound_audit"])
        self.assertFalse(mode["completion_bound_unique_task_helper"])
        self.assertFalse(mode["completion_bound_unique_route_helper"])

        updated, mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_time_buckets": 12,
                "journey_certificate_completion_bound_energy_buckets": 6,
                "journey_certificate_completion_bound_partial_pruning_enabled": False,
                "journey_certificate_completion_bound_unique_task_helper_enabled": True,
                "journey_certificate_completion_bound_unique_route_helper_enabled": True,
                "journey_certificate_completion_bound_unique_route_exact_first_step_enabled": True,
            },
            base,
            certificate_candidate=True,
            certificate_flat_rounds=2,
            depth=0,
            completion_bound_phase="after_retry",
        )
        self.assertTrue(mode["completion_bound"])
        self.assertTrue(updated.direct_journey_label_completion_bound_enabled)
        self.assertEqual(updated.direct_journey_label_completion_bound_energy_buckets, 6)
        self.assertFalse(updated.direct_journey_label_completion_bound_partial_pruning_enabled)
        self.assertTrue(updated.direct_journey_label_completion_bound_unique_task_helper_enabled)
        self.assertTrue(updated.direct_journey_label_completion_bound_unique_route_helper_enabled)
        self.assertTrue(updated.direct_journey_label_completion_bound_unique_route_exact_first_step_enabled)
        self.assertTrue(mode["completion_bound_unique_route_exact_first_step"])

        updated, mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_time_buckets": 12,
                "journey_certificate_completion_bound_after_retry_enabled": True,
            },
            base,
            certificate_candidate=True,
            certificate_flat_rounds=2,
            depth=0,
        )
        self.assertFalse(updated.direct_journey_label_completion_bound_enabled)
        self.assertNotIn("completion_bound", mode)

        updated, mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_time_buckets": 12,
                "journey_certificate_completion_bound_after_retry_enabled": True,
            },
            base,
            certificate_candidate=True,
            certificate_flat_rounds=2,
            depth=0,
            completion_bound_phase="after_retry",
        )
        self.assertTrue(mode["completion_bound"])
        self.assertTrue(updated.direct_journey_label_completion_bound_enabled)

        updated, mode = _journey_certificate_pricing_config(
            {"journey_certificate_completion_bound_enabled": True},
            base,
            certificate_candidate=True,
            certificate_flat_rounds=0,
            depth=1,
        )
        self.assertFalse(updated.direct_journey_label_completion_bound_enabled)
        self.assertNotIn("completion_bound", mode)

        updated, mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_root_only": False,
            },
            base,
            certificate_candidate=True,
            certificate_flat_rounds=0,
            depth=1,
        )
        self.assertFalse(updated.direct_journey_label_completion_bound_enabled)
        self.assertNotIn("completion_bound", mode)

        updated, mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_root_only": False,
            },
            base,
            certificate_candidate=True,
            certificate_flat_rounds=0,
            depth=1,
            completion_bound_phase="after_retry",
        )
        self.assertTrue(updated.direct_journey_label_completion_bound_enabled)
        self.assertTrue(mode["completion_bound"])

    def test_retry_budget_completion_reserve_is_opt_in_and_bounded(self):
        budget, reserve = _journey_retry_budget_with_completion_reserve(
            {},
            retry_remaining=20.0,
            min_pricing_time=1.0,
            retry_min_time=2.0,
            final_completion_bound_eligible=True,
        )
        self.assertEqual(budget, 20.0)
        self.assertEqual(reserve, 0.0)

        budget, reserve = _journey_retry_budget_with_completion_reserve(
            {"journey_certificate_completion_bound_after_retry_reserve_time": 6.0},
            retry_remaining=20.0,
            min_pricing_time=1.0,
            retry_min_time=2.0,
            final_completion_bound_eligible=False,
        )
        self.assertEqual(budget, 20.0)
        self.assertEqual(reserve, 0.0)

        budget, reserve = _journey_retry_budget_with_completion_reserve(
            {"journey_certificate_completion_bound_after_retry_reserve_time": 6.0},
            retry_remaining=20.0,
            min_pricing_time=1.0,
            retry_min_time=2.0,
            final_completion_bound_eligible=True,
        )
        self.assertEqual(budget, 14.0)
        self.assertEqual(reserve, 6.0)

        budget, reserve = _journey_retry_budget_with_completion_reserve(
            {"journey_certificate_completion_bound_after_retry_reserve_time": 6.0},
            retry_remaining=7.0,
            min_pricing_time=1.0,
            retry_min_time=2.0,
            final_completion_bound_eligible=True,
        )
        self.assertEqual(budget, 7.0)
        self.assertEqual(reserve, 0.0)

        self.assertEqual(
            _journey_completion_bound_probe_budget(
                {"journey_certificate_completion_bound_after_retry_reserve_time": 6.0},
                remaining=20.0,
            ),
            14.0,
        )
        self.assertEqual(
            _journey_completion_bound_probe_budget(
                {"journey_certificate_completion_bound_after_retry_reserve_time": 6.0},
                remaining=5.0,
            ),
            5.0,
        )
        self.assertEqual(
            _journey_completion_bound_probe_budget(
                {
                    "journey_certificate_completion_bound_after_retry_reserve_time": 2.0,
                    "journey_certificate_completion_bound_after_retry_min_time": 1.0,
                },
                remaining=2.25,
            ),
            1.0,
        )

    def test_hidden_negative_patrol_config_is_beam_limited_not_certificate(self):
        base = JourneyPricingConfig(
            direct_journey_label_completion_bound_enabled=True,
            direct_journey_label_completion_bound_two_cycle_enabled=True,
            direct_journey_label_completion_bound_unique_task_helper_enabled=True,
            direct_journey_label_completion_bound_unique_route_helper_enabled=True,
            max_returned_journeys=8,
        )
        updated, mode = _journey_hidden_negative_patrol_config(
            {
                "journey_hidden_negative_patrol_enabled": True,
                "journey_hidden_negative_patrol_max_labels_per_node": 10,
                "journey_hidden_negative_patrol_time_limit": 0.25,
                "journey_hidden_negative_patrol_min_journeys": 2,
                "journey_hidden_negative_patrol_max_returned_journeys": 4,
                "journey_hidden_negative_patrol_max_dp_states": 5000,
                "journey_hidden_negative_patrol_partial_max_states": 2000,
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_unique_task_helper_enabled": True,
                "journey_certificate_completion_bound_unique_route_helper_enabled": True,
                "journey_certificate_completion_bound_two_cycle_enabled": True,
            },
            base,
            remaining=10.0,
            min_pricing_time=1.0,
        )
        self.assertTrue(mode["hidden_negative_patrol"])
        self.assertTrue(updated.direct_journey_label_pricing_enabled)
        self.assertTrue(updated.direct_journey_label_completion_bound_enabled)
        self.assertFalse(updated.direct_journey_label_global_certificate_enabled)
        self.assertTrue(updated.direct_journey_label_completion_bound_two_cycle_enabled)
        self.assertTrue(updated.direct_journey_label_completion_bound_unique_task_helper_enabled)
        self.assertTrue(updated.direct_journey_label_completion_bound_unique_route_helper_enabled)
        self.assertFalse(updated.direct_journey_label_completion_bound_audit_enabled)
        self.assertEqual(updated.direct_journey_label_max_labels_per_node, 10)
        self.assertFalse(updated.direct_journey_label_new_task_set_only)
        self.assertFalse(mode["new_task_set_only"])
        self.assertEqual(updated.direct_journey_label_early_return_negative_min_count, 2)
        self.assertEqual(updated.max_returned_journeys, 4)
        self.assertEqual(updated.max_dp_states, 5000)
        self.assertEqual(updated.direct_journey_label_partial_max_states, 2000)
        self.assertAlmostEqual(updated.time_limit, 0.25)

    def test_hidden_negative_patrol_config_can_filter_to_new_task_sets(self):
        base = JourneyPricingConfig(
            direct_journey_label_existing_task_set_repair_only=True,
            direct_journey_label_completion_bound_enabled=False,
            max_returned_journeys=8,
        )
        updated, mode = _journey_hidden_negative_patrol_config(
            {
                "journey_hidden_negative_patrol_enabled": True,
                "journey_hidden_negative_patrol_new_task_set_only": True,
                "journey_hidden_negative_patrol_max_labels_per_node": 10,
                "journey_hidden_negative_patrol_time_limit": 0.25,
            },
            base,
            remaining=10.0,
            min_pricing_time=1.0,
        )
        self.assertTrue(mode["hidden_negative_patrol"])
        self.assertTrue(mode["new_task_set_only"])
        self.assertTrue(updated.direct_journey_label_new_task_set_only)
        self.assertFalse(updated.direct_journey_label_existing_task_set_repair_only)
        self.assertTrue(updated.direct_journey_label_pricing_enabled)
        self.assertFalse(updated.direct_journey_label_global_certificate_enabled)

    def test_hidden_negative_patrol_config_allows_full_direct_only_with_completion_bound(self):
        base = JourneyPricingConfig(
            direct_journey_label_completion_bound_enabled=False,
            direct_journey_label_completion_bound_two_cycle_enabled=False,
            max_returned_journeys=8,
        )
        disabled, disabled_mode = _journey_hidden_negative_patrol_config(
            {
                "journey_hidden_negative_patrol_enabled": True,
                "journey_hidden_negative_patrol_max_labels_per_node": 0,
                "journey_hidden_negative_patrol_completion_bound_enabled": False,
                "journey_hidden_negative_patrol_time_limit": 0.25,
            },
            base,
            remaining=10.0,
            min_pricing_time=1.0,
        )
        self.assertIs(disabled, base)
        self.assertEqual(disabled_mode, {})

        updated, mode = _journey_hidden_negative_patrol_config(
            {
                "journey_hidden_negative_patrol_enabled": True,
                "journey_hidden_negative_patrol_max_labels_per_node": 0,
                "journey_hidden_negative_patrol_completion_bound_enabled": True,
                "journey_hidden_negative_patrol_completion_bound_two_cycle_enabled": True,
                "journey_hidden_negative_patrol_time_limit": 0.25,
                "journey_hidden_negative_patrol_min_journeys": 4,
                "journey_hidden_negative_patrol_max_returned_journeys": 4,
                "journey_certificate_completion_bound_time_buckets": 6,
                "journey_certificate_completion_bound_energy_buckets": 6,
            },
            base,
            remaining=10.0,
            min_pricing_time=1.0,
        )
        self.assertTrue(mode["hidden_negative_patrol"])
        self.assertTrue(mode["full_direct"])
        self.assertEqual(mode["max_labels_per_node"], 0)
        self.assertTrue(updated.direct_journey_label_completion_bound_enabled)
        self.assertTrue(updated.direct_journey_label_completion_bound_two_cycle_enabled)
        self.assertEqual(updated.direct_journey_label_max_labels_per_node, 0)
        self.assertEqual(updated.direct_journey_label_early_return_negative_min_count, 4)
        self.assertEqual(updated.max_returned_journeys, 4)

        coarsened, coarsened_mode = _journey_hidden_negative_patrol_config(
            {
                "journey_hidden_negative_patrol_enabled": True,
                "journey_hidden_negative_patrol_max_labels_per_node": 0,
                "journey_hidden_negative_patrol_completion_bound_enabled": False,
                "journey_hidden_negative_patrol_resource_coarsening_enabled": True,
                "journey_hidden_negative_patrol_resource_coarsening_time_bucket_size": 50.0,
                "journey_hidden_negative_patrol_resource_coarsening_energy_bucket_size": 50.0,
                "journey_hidden_negative_patrol_time_limit": 0.25,
                "journey_hidden_negative_patrol_min_journeys": 3,
                "journey_hidden_negative_patrol_max_returned_journeys": 8,
            },
            base,
            remaining=10.0,
            min_pricing_time=1.0,
        )
        self.assertTrue(coarsened_mode["hidden_negative_patrol"])
        self.assertTrue(coarsened_mode["resource_coarsening"])
        self.assertFalse(coarsened.direct_journey_label_completion_bound_enabled)
        self.assertFalse(coarsened.direct_journey_label_global_certificate_enabled)
        self.assertEqual(coarsened.direct_journey_label_max_labels_per_node, 0)
        self.assertAlmostEqual(coarsened.direct_journey_label_resource_coarsening_time_bucket_size, 50.0)
        self.assertAlmostEqual(coarsened.direct_journey_label_resource_coarsening_energy_bucket_size, 50.0)
        self.assertEqual(coarsened.direct_journey_label_early_return_negative_min_count, 3)
        self.assertEqual(coarsened.max_returned_journeys, 8)

    def test_replacement_repair_config_is_restricted_direct_worker_not_certificate(self):
        base = JourneyPricingConfig(
            profile_pricing_enabled=True,
            streaming_pricing_enabled=True,
            direct_journey_label_pricing_enabled=False,
            direct_journey_label_completion_bound_enabled=True,
            direct_journey_label_ng_dssr_enabled=True,
            max_returned_journeys=8,
            max_dp_states=12345,
        )
        updated, mode = _journey_replacement_repair_config(
            {
                "journey_replacement_repair_enabled": True,
                "journey_replacement_repair_time_limit": 2.0,
                "journey_replacement_repair_final_reserve_time": 1.0,
                "journey_replacement_repair_min_journeys": 3,
                "journey_replacement_repair_max_returned_journeys": 9,
                "journey_replacement_repair_resource_coarsening_enabled": True,
                "journey_replacement_repair_resource_coarsening_time_bucket_size": 50.0,
                "journey_replacement_repair_resource_coarsening_energy_bucket_size": 25.0,
                "journey_replacement_repair_next_sortie_cache_enabled": False,
                "journey_replacement_repair_max_dp_states": 999,
                "journey_replacement_repair_partial_max_states": 777,
            },
            base,
            remaining=10.0,
            min_pricing_time=0.5,
            depth=0,
            target_task_sets=(frozenset({1, 2}), frozenset({3})),
        )
        self.assertTrue(mode["replacement_repair"])
        self.assertFalse(mode["certificate_capable"])
        self.assertEqual(mode["target_task_sets"], 2)
        self.assertFalse(updated.profile_pricing_enabled)
        self.assertFalse(updated.streaming_pricing_enabled)
        self.assertTrue(updated.direct_journey_label_pricing_enabled)
        self.assertFalse(updated.direct_journey_label_completion_bound_enabled)
        self.assertFalse(updated.direct_journey_label_ng_dssr_enabled)
        self.assertTrue(updated.direct_journey_label_existing_task_set_repair_only)
        self.assertEqual(updated.direct_journey_label_repair_task_sets, (frozenset({1, 2}), frozenset({3})))
        self.assertFalse(updated.direct_journey_label_next_sortie_cache_enabled)
        self.assertTrue(updated.direct_journey_label_early_return_negative)
        self.assertEqual(updated.direct_journey_label_early_return_negative_min_count, 3)
        self.assertEqual(updated.max_returned_journeys, 9)
        self.assertEqual(updated.max_dp_states, 999)
        self.assertEqual(updated.direct_journey_label_partial_max_states, 777)
        self.assertAlmostEqual(updated.time_limit, 2.0)
        self.assertAlmostEqual(updated.direct_journey_label_resource_coarsening_time_bucket_size, 50.0)
        self.assertAlmostEqual(updated.direct_journey_label_resource_coarsening_energy_bucket_size, 25.0)

        guided, guided_mode = _journey_replacement_repair_config(
            {
                "journey_replacement_repair_enabled": True,
                "journey_replacement_repair_time_limit": 2.0,
                "journey_replacement_repair_final_reserve_time": 1.0,
                "journey_replacement_repair_completion_bound_enabled": True,
                "journey_replacement_repair_completion_bound_time_buckets": 7,
                "journey_replacement_repair_completion_bound_energy_buckets": 9,
                "journey_replacement_repair_completion_bound_two_cycle_enabled": True,
                "journey_replacement_repair_completion_bound_two_cycle_max_states": 321,
            },
            base,
            remaining=10.0,
            min_pricing_time=0.5,
            depth=0,
            target_task_sets=(frozenset({4}),),
        )
        self.assertTrue(guided.direct_journey_label_completion_bound_enabled)
        self.assertTrue(guided.direct_journey_label_completion_bound_two_cycle_enabled)
        self.assertEqual(guided.direct_journey_label_completion_bound_time_buckets, 7)
        self.assertEqual(guided.direct_journey_label_completion_bound_energy_buckets, 9)
        self.assertEqual(guided.direct_journey_label_completion_bound_two_cycle_max_states, 321)
        self.assertFalse(guided.direct_journey_label_global_certificate_enabled)
        self.assertFalse(guided.direct_journey_label_completion_bound_audit_enabled)
        self.assertTrue(guided.direct_journey_label_existing_task_set_repair_only)
        self.assertEqual(guided.direct_journey_label_repair_task_sets, (frozenset({4}),))
        self.assertEqual(guided_mode["target_task_sets"], 1)
        self.assertFalse(guided_mode["certificate_capable"])
        self.assertTrue(guided_mode["completion_bound"])
        self.assertTrue(guided_mode["completion_bound_two_cycle"])

        untargeted, untargeted_mode = _journey_replacement_repair_config(
            {
                "journey_replacement_repair_enabled": True,
                "journey_replacement_repair_time_limit": 2.0,
            },
            base,
            remaining=10.0,
            min_pricing_time=0.5,
            depth=0,
        )
        self.assertIs(untargeted, base)
        self.assertEqual(untargeted_mode, {})

        branch_skipped, branch_mode = _journey_replacement_repair_config(
            {
                "journey_replacement_repair_enabled": True,
                "journey_replacement_repair_time_limit": 2.0,
                "journey_replacement_repair_root_only": True,
            },
            base,
            remaining=10.0,
            min_pricing_time=0.5,
            depth=1,
        )
        self.assertIs(branch_skipped, base)
        self.assertEqual(branch_mode, {})

    def test_direct_repair_target_masks_can_be_limited_to_recent_task_sets(self):
        data = SimpleNamespace(tasks=(1, 2, 3, 4))
        task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
        dominant_costs = {
            frozenset({1, 2}): 10.0,
            frozenset({2, 3}): 9.0,
            frozenset({4}): 8.0,
        }

        all_masks = _direct_repair_target_masks(data, task_to_bit, dominant_costs)
        mask_12 = (1 << task_to_bit[1]) | (1 << task_to_bit[2])
        mask_23 = (1 << task_to_bit[2]) | (1 << task_to_bit[3])
        mask_4 = 1 << task_to_bit[4]
        self.assertEqual(all_masks, frozenset({mask_12, mask_23, mask_4}))

        targeted = _direct_repair_target_masks(
            data,
            task_to_bit,
            dominant_costs,
            (frozenset({2, 3}), frozenset({1, 4})),
        )
        self.assertEqual(targeted, frozenset({mask_23}))

    def test_replacement_repair_targets_can_include_active_support(self):
        recent = (frozenset({1, 2}), frozenset({3}))
        active = {frozenset({3}), frozenset({4, 5})}

        default_targets = _journey_replacement_repair_target_task_sets(
            {},
            recent_changed_task_sets=recent,
            active_task_sets=active,
        )
        self.assertEqual(default_targets, recent)

        combined = _journey_replacement_repair_target_task_sets(
            {"journey_replacement_repair_target_active_task_sets_enabled": True},
            recent_changed_task_sets=recent,
            active_task_sets=active,
        )
        self.assertEqual(set(combined), {frozenset({1, 2}), frozenset({3}), frozenset({4, 5})})

        active_only = _journey_replacement_repair_target_task_sets(
            {
                "journey_replacement_repair_target_recent_changed_task_sets_enabled": False,
                "journey_replacement_repair_target_active_task_sets_enabled": True,
            },
            recent_changed_task_sets=recent,
            active_task_sets=active,
        )
        self.assertEqual(set(active_only), active)

    def test_replacement_repair_no_column_is_not_global_certificate(self):
        pricing = SimpleNamespace(
            journeys=[],
            exhausted=False,
            status="INCOMPLETE",
            reason="direct_label_existing_task_set_repair_no_negative_journey",
            completion_bound_enabled=False,
        )
        self.assertEqual(_journey_pricing_state(pricing), PRICING_STATE_INCOMPLETE_LIMIT)
        self.assertFalse(_journey_pricing_is_global_certificate(pricing))

    def test_fixed_task_set_repair_targets_and_gate_are_worker_only(self):
        recent = (frozenset({1, 2}),)
        active = {frozenset({2, 3}), frozenset({4})}
        targets = _journey_fixed_task_set_repair_target_task_sets(
            {},
            recent_changed_task_sets=recent,
            active_task_sets=active,
        )
        self.assertEqual(set(targets), {frozenset({1, 2}), frozenset({2, 3}), frozenset({4})})

        disabled, disabled_mode = _journey_fixed_task_set_repair_enabled(
            {"journey_fixed_task_set_repair_enabled": True, "journey_fixed_task_set_repair_time_limit": 2.0},
            remaining=2.5,
            min_pricing_time=1.0,
            depth=0,
            target_task_sets=targets,
        )
        self.assertFalse(disabled)
        self.assertEqual(disabled_mode, {})

        enabled, mode = _journey_fixed_task_set_repair_enabled(
            {
                "journey_fixed_task_set_repair_enabled": True,
                "journey_fixed_task_set_repair_time_limit": 2.0,
                "journey_fixed_task_set_repair_final_reserve_time": 1.0,
                "journey_fixed_task_set_repair_max_task_set_size": 5,
            },
            remaining=5.0,
            min_pricing_time=0.5,
            depth=0,
            target_task_sets=targets,
        )
        self.assertTrue(enabled)
        self.assertTrue(mode["fixed_task_set_repair"])
        self.assertFalse(mode["certificate_capable"])
        self.assertAlmostEqual(mode["time_limit"], 2.0)
        self.assertEqual(mode["max_task_set_size"], 5)

    def test_fixed_task_set_repair_finds_same_task_set_cheaper_true_negative(self):
        data = load_future_data("very_small")
        task = int(data.tasks[0])
        trip = evaluate_timed_trip(data, (task,), 0.0, time_bucket_size=5.0)
        self.assertIsNotNone(trip)
        assert trip is not None
        journey = make_journey(data, (trip,))
        self.assertIsNotNone(journey)
        assert journey is not None
        inflated = replace(journey, cost=round(float(journey.cost) + 10.0, 6))
        pool = JourneyPool()
        pool.add(inflated)
        duals = JourneyDuals(
            cover={task: float(inflated.cost) - 0.5},
            fleet_limit=0.0,
            cuts={},
        )
        pool_targets = _journey_fixed_task_set_repair_pool_targets(
            {"journey_fixed_task_set_repair_max_target_task_sets": 4},
            pool,
            duals,
            tuple(),
        )
        self.assertEqual(pool_targets, (frozenset({task}),))

        result = _price_fixed_task_set_representatives(
            data,
            duals,
            tuple(),
            pool,
            (frozenset({task}),),
            {
                "time_bucket_size": 5.0,
                "max_tasks_per_trip": 3,
                "journey_fixed_task_set_repair_time_limit": 1.0,
                "journey_fixed_task_set_repair_max_task_set_size": 3,
                "journey_fixed_task_set_repair_max_returned_journeys": 2,
            },
            time_limit=1.0,
            forbidden_journey_signatures=set(),
        )
        self.assertEqual(result.status, "INCOMPLETE")
        self.assertEqual(result.pricing_state, PRICING_STATE_FOUND_NEGATIVE)
        self.assertEqual(result.reason, "fixed_task_set_repair_negative_journey")
        self.assertEqual(len(result.journeys), 1)
        self.assertEqual(result.journeys[0].task_set, frozenset({task}))
        self.assertLess(float(result.journeys[0].cost), float(inflated.cost))
        self.assertLess(manual_journey_reduced_cost(result.journeys[0], duals, tuple()), -1.0e-6)
        self.assertFalse(_journey_pricing_is_global_certificate(result))

    def test_new_task_set_sweep_gate_and_candidates_are_worker_only(self):
        data = load_future_data("very_small")
        tasks = [int(task) for task in data.tasks[:3]]
        pool = JourneyPool()
        first_trip = evaluate_timed_trip(data, (tasks[0],), 0.0, time_bucket_size=5.0)
        self.assertIsNotNone(first_trip)
        assert first_trip is not None
        first_journey = make_journey(data, (first_trip,))
        self.assertIsNotNone(first_journey)
        assert first_journey is not None
        pool.add(first_journey)
        duals = JourneyDuals(
            cover={tasks[0]: 100.0, tasks[1]: 300.0, tasks[2]: 200.0},
            fleet_limit=0.0,
            cuts={},
        )
        candidates = _journey_new_task_set_sweep_candidate_task_sets(
            data,
            duals,
            pool,
            {
                "journey_new_task_set_sweep_min_task_count": 1,
                "journey_new_task_set_sweep_max_task_count": 1,
                "journey_new_task_set_sweep_top_tasks": 3,
                "journey_new_task_set_sweep_max_combinations": 4,
            },
        )
        self.assertNotIn(frozenset({tasks[0]}), candidates)
        self.assertEqual(candidates[0], frozenset({tasks[1]}))

        disabled, disabled_mode = _journey_new_task_set_sweep_enabled(
            {"journey_new_task_set_sweep_enabled": True, "journey_new_task_set_sweep_time_limit": 2.0},
            remaining=2.5,
            min_pricing_time=1.0,
            depth=0,
        )
        self.assertFalse(disabled)
        self.assertEqual(disabled_mode, {})

        enabled, mode = _journey_new_task_set_sweep_enabled(
            {
                "journey_new_task_set_sweep_enabled": True,
                "journey_new_task_set_sweep_time_limit": 1.0,
                "journey_new_task_set_sweep_final_reserve_time": 1.0,
                "journey_new_task_set_sweep_top_tasks": 3,
                "journey_new_task_set_sweep_max_task_count": 1,
            },
            remaining=5.0,
            min_pricing_time=0.5,
            depth=0,
        )
        self.assertTrue(enabled)
        self.assertTrue(mode["new_task_set_sweep"])
        self.assertFalse(mode["certificate_capable"])
        self.assertAlmostEqual(mode["time_limit"], 1.0)

    def test_new_task_set_sweep_finds_true_negative_new_task_set(self):
        data = load_future_data("very_small")
        task = int(data.tasks[0])
        trip = evaluate_timed_trip(data, (task,), 0.0, time_bucket_size=5.0)
        self.assertIsNotNone(trip)
        assert trip is not None
        journey = make_journey(data, (trip,))
        self.assertIsNotNone(journey)
        assert journey is not None
        pool = JourneyPool()
        duals = JourneyDuals(
            cover={task: float(journey.cost) + 1.0},
            fleet_limit=0.0,
            cuts={},
        )
        result = _price_new_task_set_sweep(
            data,
            duals,
            tuple(),
            pool,
            {
                "time_bucket_size": 5.0,
                "max_tasks_per_trip": 3,
                "journey_new_task_set_sweep_min_task_count": 1,
                "journey_new_task_set_sweep_max_task_count": 1,
                "journey_new_task_set_sweep_top_tasks": 1,
                "journey_new_task_set_sweep_max_combinations": 1,
                "journey_new_task_set_sweep_max_returned_journeys": 2,
            },
            time_limit=1.0,
            forbidden_journey_signatures=set(),
        )
        self.assertEqual(result.status, "INCOMPLETE")
        self.assertEqual(result.pricing_state, PRICING_STATE_FOUND_NEGATIVE)
        self.assertEqual(result.reason, "new_task_set_sweep_negative_journey")
        self.assertTrue(result.direct_label_new_task_set_only)
        self.assertEqual(result.harvest_selected_new_task_set_count, 1)
        self.assertEqual(len(result.journeys), 1)
        self.assertEqual(result.journeys[0].task_set, frozenset({task}))
        self.assertLess(manual_journey_reduced_cost(result.journeys[0], duals, tuple()), -1.0e-6)
        self.assertFalse(_journey_pricing_is_global_certificate(result))

    def test_profile_repair_config_is_local_profile_worker_not_certificate(self):
        base = JourneyPricingConfig(
            direct_journey_label_pricing_enabled=True,
            direct_journey_label_completion_bound_enabled=True,
            direct_journey_label_ng_dssr_enabled=True,
            profile_labeling_enabled=False,
            profile_labeling_physical_catalog_resume_enabled=True,
            profile_labeling_physical_catalog_share_across_branches_enabled=True,
            profile_best_contribution_diagnostics_enabled=True,
            streaming_pricing_enabled=False,
            max_returned_journeys=8,
            max_dp_states=12345,
            streaming_profile_batch_size=50,
        )
        skipped, skipped_mode = _journey_profile_repair_config(
            {
                "journey_profile_repair_enabled": True,
                "journey_profile_repair_time_limit": 2.0,
            },
            base,
            remaining=10.0,
            min_pricing_time=0.5,
            depth=0,
        )
        self.assertIs(skipped, base)
        self.assertEqual(skipped_mode, {})

        updated, mode = _journey_profile_repair_config(
            {
                "journey_profile_repair_enabled": True,
                "journey_profile_repair_time_limit": 2.0,
                "journey_profile_repair_final_reserve_time": 1.0,
                "journey_profile_repair_min_journeys": 6,
                "journey_profile_repair_max_returned_journeys": 12,
                "journey_profile_repair_streaming_min_negative_batch": 7,
                "journey_profile_repair_streaming_profile_batch_size": 200,
                "journey_profile_repair_selection_mode": "orthogonal",
            },
            base,
            remaining=10.0,
            min_pricing_time=0.5,
            depth=0,
            after_patrol=True,
        )
        self.assertTrue(mode["profile_repair"])
        self.assertTrue(mode["after_patrol"])
        self.assertFalse(updated.direct_journey_label_pricing_enabled)
        self.assertFalse(updated.direct_journey_label_completion_bound_enabled)
        self.assertFalse(updated.direct_journey_label_ng_dssr_enabled)
        self.assertTrue(updated.profile_pricing_enabled)
        self.assertTrue(updated.profile_labeling_enabled)
        self.assertTrue(updated.profile_labeling_resume_enabled)
        self.assertFalse(updated.profile_labeling_physical_catalog_resume_enabled)
        self.assertFalse(updated.profile_labeling_physical_catalog_share_across_branches_enabled)
        self.assertFalse(updated.profile_best_contribution_diagnostics_enabled)
        self.assertTrue(updated.streaming_pricing_enabled)
        self.assertTrue(updated.early_return_negative)
        self.assertTrue(updated.early_return_unique_masks_enabled)
        self.assertEqual(updated.early_return_negative_min_count, 7)
        self.assertEqual(updated.streaming_min_negative_batch, 7)
        self.assertEqual(updated.streaming_profile_batch_size, 200)
        self.assertEqual(updated.max_returned_journeys, 12)
        self.assertEqual(updated.max_dp_states, 12345)
        self.assertEqual(updated.journey_selection_mode, "orthogonal")
        self.assertAlmostEqual(updated.time_limit, 2.0)
        self.assertFalse(mode["certificate_capable"])
        self.assertFalse(mode["physical_catalog_resume"])
        self.assertTrue(updated.dp_cross_count_dominance_enabled)
        self.assertTrue(mode["dp_cross_count_dominance"])

        cross_count_relaxed, cross_count_relaxed_mode = _journey_profile_repair_config(
            {
                "journey_profile_repair_enabled": True,
                "journey_profile_repair_time_limit": 1.0,
                "journey_profile_repair_final_reserve_time": 0.0,
                "journey_profile_repair_dp_cross_count_dominance_enabled": False,
            },
            replace(base, dp_cross_count_dominance_enabled=True),
            remaining=5.0,
            min_pricing_time=0.0,
            depth=0,
            after_patrol=True,
        )
        self.assertFalse(cross_count_relaxed.dp_cross_count_dominance_enabled)
        self.assertFalse(cross_count_relaxed_mode["dp_cross_count_dominance"])
        self.assertFalse(cross_count_relaxed_mode["certificate_capable"])

        disabled, disabled_mode = _journey_profile_repair_config(
            {
                "journey_profile_repair_enabled": True,
                "journey_profile_repair_time_limit": 2.0,
                "journey_profile_repair_root_only": True,
            },
            base,
            remaining=10.0,
            min_pricing_time=0.5,
            depth=1,
            after_patrol=True,
        )
        self.assertIs(disabled, base)
        self.assertEqual(disabled_mode, {})

        no_budget, no_budget_mode = _journey_profile_repair_config(
            {
                "journey_profile_repair_enabled": True,
                "journey_profile_repair_time_limit": 2.0,
                "journey_profile_repair_final_reserve_time": 1.0,
            },
            base,
            remaining=2.5,
            min_pricing_time=0.5,
            depth=0,
            after_patrol=True,
        )
        self.assertIs(no_budget, base)
        self.assertEqual(no_budget_mode, {})

    def test_post_seed_profile_reharvest_config_uses_seeded_catalog_only_after_replacement(self):
        base = JourneyPricingConfig(
            profile_pricing_enabled=False,
            direct_journey_label_pricing_enabled=True,
            direct_journey_label_global_certificate_enabled=True,
            direct_journey_label_completion_bound_enabled=True,
            direct_journey_label_ng_dssr_enabled=True,
            profile_labeling_physical_catalog_resume_enabled=False,
            streaming_pricing_enabled=False,
            max_returned_journeys=6,
            streaming_profile_batch_size=50,
        )
        replacement_added = _JourneyAdditionCount(
            3,
            new_journeys=0,
            replacement_journeys=3,
            unchanged_journeys=0,
            replacement_task_sets=(frozenset({1, 2}),),
            changed_task_sets=(frozenset({1, 2}),),
        )
        new_added = _JourneyAdditionCount(
            1,
            new_journeys=1,
            replacement_journeys=0,
            unchanged_journeys=0,
            new_task_sets=(frozenset({3}),),
            changed_task_sets=(frozenset({3}),),
        )

        skipped, skipped_mode = _journey_post_seed_profile_reharvest_config(
            {},
            base,
            replacement_added,
            remaining=10.0,
            min_pricing_time=0.5,
            depth=0,
        )
        self.assertIs(skipped, base)
        self.assertEqual(skipped_mode, {})

        new_skip, new_skip_mode = _journey_post_seed_profile_reharvest_config(
            {
                "journey_post_seed_profile_reharvest_enabled": True,
                "journey_post_seed_profile_reharvest_time_limit": 1.0,
                "journey_post_seed_profile_reharvest_final_reserve_time": 0.5,
            },
            base,
            new_added,
            remaining=10.0,
            min_pricing_time=0.5,
            depth=0,
        )
        self.assertIs(new_skip, base)
        self.assertEqual(new_skip_mode, {})

        updated, mode = _journey_post_seed_profile_reharvest_config(
            {
                "journey_post_seed_profile_reharvest_enabled": True,
                "journey_post_seed_profile_reharvest_time_limit": 1.5,
                "journey_post_seed_profile_reharvest_final_reserve_time": 0.5,
                "journey_post_seed_profile_reharvest_min_journeys": 8,
                "journey_post_seed_profile_reharvest_max_returned_journeys": 24,
                "journey_post_seed_profile_reharvest_streaming_min_negative_batch": 9,
                "journey_post_seed_profile_reharvest_streaming_profile_batch_size": 200,
                "journey_post_seed_profile_reharvest_selection_mode": "orthogonal",
            },
            base,
            replacement_added,
            remaining=10.0,
            min_pricing_time=0.5,
            depth=0,
        )
        self.assertTrue(mode["post_seed_profile_reharvest"])
        self.assertFalse(updated.direct_journey_label_pricing_enabled)
        self.assertFalse(updated.direct_journey_label_global_certificate_enabled)
        self.assertFalse(updated.direct_journey_label_completion_bound_enabled)
        self.assertFalse(updated.direct_journey_label_ng_dssr_enabled)
        self.assertTrue(updated.profile_pricing_enabled)
        self.assertTrue(updated.profile_labeling_enabled)
        self.assertTrue(updated.profile_labeling_resume_enabled)
        self.assertTrue(updated.profile_labeling_physical_catalog_resume_enabled)
        self.assertFalse(updated.profile_labeling_physical_catalog_share_across_branches_enabled)
        self.assertTrue(updated.streaming_pricing_enabled)
        self.assertTrue(updated.early_return_negative)
        self.assertTrue(updated.early_return_unique_masks_enabled)
        self.assertEqual(updated.early_return_negative_min_count, 9)
        self.assertEqual(updated.streaming_min_negative_batch, 9)
        self.assertEqual(updated.streaming_profile_batch_size, 200)
        self.assertEqual(updated.max_returned_journeys, 24)
        self.assertEqual(updated.journey_selection_mode, "orthogonal")
        self.assertAlmostEqual(updated.time_limit, 1.5)
        self.assertFalse(mode["certificate_capable"])
        self.assertTrue(mode["physical_catalog_resume"])

    def test_hidden_negative_patrol_after_small_batch_gate(self):
        config = {
            "journey_hidden_negative_patrol_enabled": True,
            "journey_hidden_negative_patrol_after_small_batch_enabled": True,
            "journey_hidden_negative_patrol_after_small_batch_max_added_journeys": 3,
            "journey_hidden_negative_patrol_after_small_batch_min_flat_rounds": 2,
        }
        pricing = SimpleNamespace(journeys=[object()], status="OPTIMAL", reason="negative_journey")
        self.assertTrue(
            _journey_hidden_negative_patrol_after_small_batch_needed(
                config,
                pricing,
                added_columns=2,
                certificate_candidate=True,
                certificate_flat_rounds=2,
                depth=0,
            )
        )
        self.assertFalse(
            _journey_hidden_negative_patrol_after_small_batch_needed(
                config,
                pricing,
                added_columns=4,
                certificate_candidate=True,
                certificate_flat_rounds=2,
                depth=0,
            )
        )
        self.assertFalse(
            _journey_hidden_negative_patrol_after_small_batch_needed(
                config,
                pricing,
                added_columns=2,
                certificate_candidate=False,
                certificate_flat_rounds=2,
                depth=0,
            )
        )
        self.assertFalse(
            _journey_hidden_negative_patrol_after_small_batch_needed(
                config,
                pricing,
                added_columns=2,
                certificate_candidate=True,
                certificate_flat_rounds=1,
                depth=0,
            )
        )
        no_column = SimpleNamespace(journeys=[], status="OPTIMAL", reason="no_negative_journey", exhausted=True)
        self.assertFalse(
            _journey_hidden_negative_patrol_after_small_batch_needed(
                config,
                no_column,
                added_columns=1,
                certificate_candidate=True,
                certificate_flat_rounds=2,
                depth=0,
            )
        )

    def test_same_dual_supplement_gate_requires_small_true_dual_tail_batch(self):
        config = {
            "journey_same_dual_supplement_enabled": True,
            "journey_same_dual_supplement_max_initial_added_journeys": 3,
            "journey_same_dual_supplement_min_flat_rounds": 2,
        }
        self.assertTrue(
            _journey_same_dual_supplement_needed(
                config,
                added_columns=2,
                certificate_candidate=True,
                certificate_flat_rounds=2,
                depth=0,
                pricing_dual_source="scip_certificate",
            )
        )
        self.assertFalse(
            _journey_same_dual_supplement_needed(
                config,
                added_columns=4,
                certificate_candidate=True,
                certificate_flat_rounds=2,
                depth=0,
                pricing_dual_source="scip_certificate",
            )
        )
        self.assertFalse(
            _journey_same_dual_supplement_needed(
                config,
                added_columns=2,
                certificate_candidate=False,
                certificate_flat_rounds=2,
                depth=0,
                pricing_dual_source="scip_certificate",
            )
        )
        self.assertFalse(
            _journey_same_dual_supplement_needed(
                config,
                added_columns=2,
                certificate_candidate=True,
                certificate_flat_rounds=1,
                depth=0,
                pricing_dual_source="scip_certificate",
            )
        )
        self.assertFalse(
            _journey_same_dual_supplement_needed(
                config,
                added_columns=2,
                certificate_candidate=True,
                certificate_flat_rounds=2,
                depth=0,
                pricing_dual_source="dual_average",
            )
        )

    def test_same_dual_supplement_config_is_worker_only_direct_label(self):
        config = {
            "journey_same_dual_supplement_enabled": True,
            "journey_same_dual_supplement_time_limit": 0.75,
            "journey_same_dual_supplement_final_reserve_time": 1.0,
            "journey_same_dual_supplement_min_journeys": 3,
            "journey_same_dual_supplement_max_returned_journeys": 12,
            "journey_same_dual_supplement_resource_coarsening_enabled": True,
            "journey_same_dual_supplement_resource_coarsening_time_bucket_size": 50.0,
            "journey_same_dual_supplement_resource_coarsening_energy_bucket_size": 25.0,
            "journey_same_dual_supplement_max_dp_states": 1234,
        }
        base = JourneyPricingConfig(
            profile_pricing_enabled=True,
            streaming_pricing_enabled=True,
            direct_journey_label_completion_bound_enabled=True,
            direct_journey_label_global_certificate_enabled=True,
            max_returned_journeys=4,
        )
        updated, mode = _journey_same_dual_supplement_config(
            config,
            base,
            remaining=5.0,
            min_pricing_time=0.2,
        )
        self.assertTrue(mode["same_dual_supplement"])
        self.assertFalse(updated.profile_pricing_enabled)
        self.assertFalse(updated.streaming_pricing_enabled)
        self.assertTrue(updated.direct_journey_label_pricing_enabled)
        self.assertFalse(updated.direct_journey_label_global_certificate_enabled)
        self.assertFalse(updated.direct_journey_label_completion_bound_enabled)
        self.assertFalse(updated.direct_journey_label_completion_bound_two_cycle_enabled)
        self.assertTrue(updated.direct_journey_label_early_return_negative)
        self.assertEqual(updated.direct_journey_label_early_return_negative_min_count, 3)
        self.assertEqual(updated.max_returned_journeys, 12)
        self.assertEqual(updated.max_dp_states, 1234)
        self.assertAlmostEqual(updated.time_limit, 0.75)
        self.assertAlmostEqual(updated.direct_journey_label_resource_coarsening_time_bucket_size, 50.0)
        self.assertAlmostEqual(updated.direct_journey_label_resource_coarsening_energy_bucket_size, 25.0)

    def test_pre_retry_completion_reserve_requires_low_remaining_threshold(self):
        config = {
            "journey_certificate_completion_bound_pre_retry_reserve_time": 1.5,
        }
        reserve = _journey_pre_retry_completion_reserve_time(
            config,
            remaining=100.0,
            exact_time_limit=4.0,
            min_pricing_time=0.2,
            final_completion_bound_eligible=True,
            exact_completion_bound_enabled=False,
        )
        self.assertEqual(reserve, 0.0)

        config["journey_certificate_completion_bound_pre_retry_reserve_remaining_threshold"] = 10.0
        reserve = _journey_pre_retry_completion_reserve_time(
            config,
            remaining=100.0,
            exact_time_limit=4.0,
            min_pricing_time=0.2,
            final_completion_bound_eligible=True,
            exact_completion_bound_enabled=False,
        )
        self.assertEqual(reserve, 0.0)

        reserve = _journey_pre_retry_completion_reserve_time(
            config,
            remaining=8.0,
            exact_time_limit=4.0,
            min_pricing_time=0.2,
            final_completion_bound_eligible=True,
            exact_completion_bound_enabled=False,
        )
        self.assertEqual(reserve, 1.5)

        reserve = _journey_pre_retry_completion_reserve_time(
            config,
            remaining=8.0,
            exact_time_limit=4.0,
            min_pricing_time=0.2,
            final_completion_bound_eligible=False,
            exact_completion_bound_enabled=False,
        )
        self.assertEqual(reserve, 0.0)

        reserve = _journey_pre_retry_completion_reserve_time(
            config,
            remaining=8.0,
            exact_time_limit=1.6,
            min_pricing_time=0.2,
            final_completion_bound_eligible=True,
            exact_completion_bound_enabled=False,
        )
        self.assertEqual(reserve, 0.0)

        reserve = _journey_pre_retry_completion_reserve_time(
            config,
            remaining=8.0,
            exact_time_limit=4.0,
            min_pricing_time=0.2,
            certificate_candidate=False,
            final_completion_bound_eligible=True,
            exact_completion_bound_enabled=False,
        )
        self.assertEqual(reserve, 0.0)

        config["journey_retry_incomplete_no_column_min_time"] = 1.0
        reserve = _journey_pre_retry_completion_reserve_time(
            config,
            remaining=8.0,
            exact_time_limit=2.0,
            min_pricing_time=0.2,
            final_completion_bound_eligible=True,
            exact_completion_bound_enabled=False,
        )
        self.assertEqual(reserve, 0.0)

        reserve = _journey_pre_retry_completion_reserve_time(
            config,
            remaining=8.0,
            exact_time_limit=3.0,
            min_pricing_time=0.2,
            final_completion_bound_eligible=True,
            exact_completion_bound_enabled=False,
        )
        self.assertEqual(reserve, 1.5)

    def test_completion_bound_final_probe_verifies_profile_no_column_certificates(self):
        config = {"journey_certificate_completion_bound_after_retry_enabled": True}
        exhausted_no_column = SimpleNamespace(exhausted=True, journeys=[])
        exhausted_completion_bound_no_column = SimpleNamespace(
            exhausted=True,
            journeys=[],
            completion_bound_enabled=True,
            status="OPTIMAL",
            reason="direct_label_no_negative_journey",
            global_certificate_capable=False,
        )
        incomplete_no_column = SimpleNamespace(exhausted=False, journeys=[])
        incomplete_candidate = SimpleNamespace(exhausted=False, journeys=[object()])
        duplicate_only = SimpleNamespace(
            exhausted=False,
            journeys=[],
            pricing_state=PRICING_STATE_DUPLICATE_ONLY,
        )
        certified_no_negative = SimpleNamespace(
            exhausted=True,
            journeys=[],
            pricing_state=PRICING_STATE_CERTIFIED_NO_NEGATIVE,
            global_certificate_capable=True,
        )

        self.assertTrue(_journey_completion_bound_final_probe_needed(config, exhausted_no_column))
        self.assertTrue(_journey_completion_bound_final_probe_needed(config, exhausted_completion_bound_no_column))
        self.assertTrue(_journey_completion_bound_final_probe_needed(config, incomplete_no_column))
        self.assertFalse(_journey_completion_bound_final_probe_needed(config, incomplete_candidate))
        self.assertTrue(_journey_completion_bound_final_probe_needed(config, duplicate_only))
        self.assertFalse(_journey_completion_bound_final_probe_needed(config, certified_no_negative))
        self.assertTrue(
            _journey_completion_bound_final_probe_needed(
                config,
                incomplete_candidate,
                added_columns=0,
            )
        )
        self.assertFalse(
            _journey_completion_bound_final_probe_needed(
                config,
                incomplete_candidate,
                added_columns=1,
            )
        )
        self.assertFalse(_journey_completion_bound_final_probe_needed({}, incomplete_no_column))

    def test_only_completion_bound_direct_label_no_column_is_global_certificate(self):
        profile_no_column = SimpleNamespace(
            exhausted=True,
            journeys=[],
            status="OPTIMAL",
            reason="no_negative_journey",
            completion_bound_enabled=False,
        )
        completion_bound_no_column = SimpleNamespace(
            exhausted=True,
            journeys=[],
            status="OPTIMAL",
            reason="direct_label_no_negative_journey",
            completion_bound_enabled=True,
            global_certificate_capable=True,
        )
        completion_bound_worker_no_column = SimpleNamespace(
            exhausted=True,
            journeys=[],
            status="OPTIMAL",
            reason="direct_label_no_negative_journey",
            completion_bound_enabled=True,
            global_certificate_capable=False,
        )
        completion_bound_negative = SimpleNamespace(
            exhausted=True,
            journeys=[object()],
            status="OPTIMAL",
            reason="direct_label_negative_journey",
            completion_bound_enabled=True,
        )
        completion_bound_local_reason = SimpleNamespace(
            exhausted=True,
            journeys=[],
            status="OPTIMAL",
            reason="no_negative_journey",
            completion_bound_enabled=True,
            global_certificate_capable=True,
        )

        self.assertFalse(_journey_pricing_is_global_certificate(profile_no_column))
        self.assertEqual(
            _journey_pricing_certificate_rejection_reason(profile_no_column),
            "profile_exhausted_requires_direct_label_final_judge",
        )
        self.assertTrue(_journey_pricing_is_global_certificate(completion_bound_no_column))
        self.assertFalse(_journey_pricing_is_global_certificate(completion_bound_worker_no_column))
        self.assertEqual(
            _journey_pricing_certificate_rejection_reason(completion_bound_worker_no_column),
            "completion_bound_worker_requires_direct_label_final_judge",
        )
        self.assertFalse(_journey_pricing_is_global_certificate(completion_bound_negative))
        self.assertEqual(
            _journey_pricing_certificate_rejection_reason(completion_bound_negative),
            "negative_journey_requires_column_addition",
        )
        self.assertFalse(_journey_pricing_is_global_certificate(completion_bound_local_reason))
        self.assertEqual(
            _journey_pricing_certificate_rejection_reason(completion_bound_local_reason),
            "direct_label_final_judge_not_no_column_certificate",
        )

    def test_journey_pricing_state_uses_explicit_certificate_semantics(self):
        found_negative = JourneyPricingResult(
            journeys=[SimpleNamespace(signature=("j",), task_set=(1,))],
            exhausted=False,
            best_reduced_cost=-1.0,
            generated_sequences=0,
            evaluated_timed_trips=0,
            candidate_trips=0,
            selected_trips=0,
            status="INCOMPLETE",
            reason="partial_negative_journey",
        )
        local_no_column = JourneyPricingResult(
            journeys=[],
            exhausted=True,
            best_reduced_cost=0.0,
            generated_sequences=0,
            evaluated_timed_trips=0,
            candidate_trips=0,
            selected_trips=0,
            status="OPTIMAL",
            reason="no_negative_journey",
            completion_bound_enabled=False,
        )
        certified_no_negative = JourneyPricingResult(
            journeys=[],
            exhausted=True,
            best_reduced_cost=0.0,
            generated_sequences=0,
            evaluated_timed_trips=0,
            candidate_trips=0,
            selected_trips=0,
            status="OPTIMAL",
            reason="direct_label_no_negative_journey",
            completion_bound_enabled=True,
            global_certificate_capable=True,
        )
        completion_bound_worker_no_negative = JourneyPricingResult(
            journeys=[],
            exhausted=True,
            best_reduced_cost=0.0,
            generated_sequences=0,
            evaluated_timed_trips=0,
            candidate_trips=0,
            selected_trips=0,
            status="OPTIMAL",
            reason="direct_label_no_negative_journey",
            completion_bound_enabled=True,
            global_certificate_capable=False,
        )
        incomplete = JourneyPricingResult(
            journeys=[],
            exhausted=False,
            best_reduced_cost=None,
            generated_sequences=0,
            evaluated_timed_trips=0,
            candidate_trips=0,
            selected_trips=0,
            status="INCOMPLETE",
            reason="time_limit",
        )
        incomplete_duplicate = JourneyPricingResult(
            journeys=[],
            exhausted=False,
            best_reduced_cost=-1.0,
            generated_sequences=0,
            evaluated_timed_trips=0,
            candidate_trips=0,
            selected_trips=0,
            status="INCOMPLETE",
            reason="negative_journeys_already_in_pool",
            existing_journeys_filtered=1,
        )
        duplicate_only = JourneyPricingResult(
            journeys=[],
            exhausted=True,
            best_reduced_cost=-1.0,
            generated_sequences=0,
            evaluated_timed_trips=0,
            candidate_trips=0,
            selected_trips=0,
            status="OPTIMAL",
            reason="negative_journeys_already_in_pool",
            existing_journeys_filtered=1,
        )
        dominated_only = JourneyPricingResult(
            journeys=[],
            exhausted=True,
            best_reduced_cost=-1.0,
            generated_sequences=0,
            evaluated_timed_trips=0,
            candidate_trips=0,
            selected_trips=0,
            status="OPTIMAL",
            reason="dominated_task_set_journeys_filtered",
            dominated_task_set_journeys_filtered=1,
        )

        self.assertEqual(found_negative.pricing_state, PRICING_STATE_FOUND_NEGATIVE)
        self.assertEqual(local_no_column.pricing_state, PRICING_STATE_LOCAL_NO_COLUMN_UNCERTIFIED)
        self.assertEqual(certified_no_negative.pricing_state, PRICING_STATE_CERTIFIED_NO_NEGATIVE)
        self.assertEqual(
            completion_bound_worker_no_negative.pricing_state,
            PRICING_STATE_LOCAL_NO_COLUMN_UNCERTIFIED,
        )
        self.assertEqual(incomplete.pricing_state, PRICING_STATE_INCOMPLETE_LIMIT)
        self.assertEqual(incomplete_duplicate.pricing_state, PRICING_STATE_INCOMPLETE_LIMIT)
        self.assertEqual(duplicate_only.pricing_state, PRICING_STATE_DUPLICATE_ONLY)
        self.assertEqual(dominated_only.pricing_state, PRICING_STATE_DUPLICATE_ONLY)
        self.assertEqual(_journey_pricing_state(incomplete_duplicate), PRICING_STATE_INCOMPLETE_LIMIT)
        self.assertEqual(_journey_pricing_state(duplicate_only), PRICING_STATE_DUPLICATE_ONLY)
        self.assertEqual(_journey_pricing_state(dominated_only), PRICING_STATE_DUPLICATE_ONLY)
        self.assertEqual(_journey_pricing_state(certified_no_negative), PRICING_STATE_CERTIFIED_NO_NEGATIVE)
        self.assertTrue(_journey_pricing_is_global_certificate(certified_no_negative))
        self.assertFalse(_journey_pricing_is_global_certificate(completion_bound_worker_no_negative))
        self.assertFalse(_journey_pricing_is_global_certificate(local_no_column))

    def test_duplicate_only_final_judge_certifies_when_negative_rmp_columns_are_at_upper_bound(self):
        pricing = JourneyPricingResult(
            journeys=[],
            exhausted=True,
            best_reduced_cost=-2.0,
            generated_sequences=0,
            evaluated_timed_trips=0,
            candidate_trips=0,
            selected_trips=0,
            status="OPTIMAL",
            reason="negative_journeys_already_in_pool",
            completion_bound_enabled=True,
            global_certificate_capable=True,
            existing_journeys_filtered=3,
        )
        pool = SimpleNamespace(
            journeys=[
                SimpleNamespace(signature=("upper",), task_set=frozenset({1}), cost=1.0),
                SimpleNamespace(signature=("free",), task_set=frozenset({2}), cost=1.0),
            ]
        )
        audit_solution = SimpleNamespace(
            optimal=True,
            status="OPTIMAL",
            objective=10.0,
            reduced_costs={0: -2.0, 1: 0.25},
            variable_values={0: 1.0, 1: 0.0},
        )

        with patch("BPC_future.solver.journey_driver.solve_journey_rmp", return_value=audit_solution):
            promoted = _journey_promote_duplicate_only_final_judge_certificate(
                SimpleNamespace(),
                {},
                pool,
                tuple(),
                tuple(),
                None,
                pricing,
                FutureLogger(None, console=False),
                4,
                node_id=2,
                depth=1,
            )

        self.assertEqual(_journey_pricing_state(promoted), PRICING_STATE_CERTIFIED_NO_NEGATIVE)
        self.assertTrue(_journey_pricing_is_global_certificate(promoted))
        self.assertEqual(promoted.reason, "direct_label_duplicate_only_no_new_column_certificate")
        self.assertEqual(promoted.best_reduced_cost, 0.0)

    def test_duplicate_only_final_judge_does_not_certify_negative_rmp_column_below_upper_bound(self):
        pricing = JourneyPricingResult(
            journeys=[],
            exhausted=True,
            best_reduced_cost=-2.0,
            generated_sequences=0,
            evaluated_timed_trips=0,
            candidate_trips=0,
            selected_trips=0,
            status="OPTIMAL",
            reason="negative_journeys_already_in_pool",
            completion_bound_enabled=True,
            global_certificate_capable=True,
            existing_journeys_filtered=3,
        )
        pool = SimpleNamespace(
            journeys=[
                SimpleNamespace(signature=("not_upper",), task_set=frozenset({1}), cost=1.0),
            ]
        )
        audit_solution = SimpleNamespace(
            optimal=True,
            status="OPTIMAL",
            objective=10.0,
            reduced_costs={0: -2.0},
            variable_values={0: 0.5},
        )

        with patch("BPC_future.solver.journey_driver.solve_journey_rmp", return_value=audit_solution):
            promoted = _journey_promote_duplicate_only_final_judge_certificate(
                SimpleNamespace(),
                {},
                pool,
                tuple(),
                tuple(),
                None,
                pricing,
                FutureLogger(None, console=False),
                4,
                node_id=2,
                depth=1,
            )

        self.assertEqual(_journey_pricing_state(promoted), PRICING_STATE_DUPLICATE_ONLY)
        self.assertFalse(_journey_pricing_is_global_certificate(promoted))

    def test_diverse_journey_harvest_keeps_strongest_and_fills_when_overlap_blocks(self):
        candidates = [
            (-10.0, SimpleNamespace(signature=("a",), task_set=(1, 2))),
            (-9.0, SimpleNamespace(signature=("b",), task_set=(2, 3))),
            (-8.0, SimpleNamespace(signature=("c",), task_set=(1, 3))),
            (-7.0, SimpleNamespace(signature=("d",), task_set=(4,))),
        ]

        selection = _select_diverse_journey_candidates(
            candidates,
            max_returned=4,
            top_k_strongest=1,
            min_fill=3,
            max_jaccard=0.0,
            max_containment=0.0,
        )

        self.assertEqual(selection.candidate_negative_count, 4)
        self.assertEqual(selection.selected_count, 3)
        self.assertEqual(selection.rejected_overlap_count, 2)
        self.assertEqual(selection.rejected_duplicate_task_set_count, 0)
        self.assertEqual(selection.fallback_fill_count, 1)
        self.assertEqual(selection.best_true_rc, -10.0)
        self.assertEqual(selection.worst_selected_true_rc, -7.0)
        self.assertEqual([journey.signature for journey in selection.journeys], [("a",), ("b",), ("d",)])
        self.assertIsNotNone(selection.avg_pairwise_jaccard)

    def test_diverse_journey_harvest_does_not_fallback_fill_duplicate_task_sets_by_default(self):
        candidates = [
            (-10.0, SimpleNamespace(signature=("a",), task_set=(1, 2))),
            (-9.0, SimpleNamespace(signature=("a2",), task_set=(1, 2))),
            (-8.0, SimpleNamespace(signature=("b",), task_set=(3,))),
            (-7.0, SimpleNamespace(signature=("c",), task_set=(4,))),
        ]

        selection = _select_diverse_journey_candidates(
            candidates,
            max_returned=4,
            top_k_strongest=2,
            min_fill=4,
            max_jaccard=0.0,
            max_containment=0.0,
        )

        self.assertEqual(selection.candidate_negative_count, 4)
        self.assertEqual(selection.selected_count, 3)
        self.assertEqual(selection.rejected_duplicate_task_set_count, 1)
        self.assertEqual(selection.fallback_fill_count, 0)
        self.assertEqual([journey.signature for journey in selection.journeys], [("a",), ("b",), ("c",)])

    def test_diverse_journey_harvest_can_opt_in_duplicate_task_set_fill(self):
        candidates = [
            (-10.0, SimpleNamespace(signature=("a",), task_set=(1, 2))),
            (-9.0, SimpleNamespace(signature=("a2",), task_set=(1, 2))),
            (-8.0, SimpleNamespace(signature=("b",), task_set=(3,))),
            (-7.0, SimpleNamespace(signature=("c",), task_set=(4,))),
        ]

        selection = _select_diverse_journey_candidates(
            candidates,
            max_returned=4,
            top_k_strongest=2,
            min_fill=4,
            max_jaccard=0.0,
            max_containment=0.0,
            allow_duplicate_task_sets=True,
        )

        self.assertEqual(selection.candidate_negative_count, 4)
        self.assertEqual(selection.selected_count, 4)
        self.assertEqual(selection.rejected_duplicate_task_set_count, 0)
        self.assertEqual([journey.signature for journey in selection.journeys], [("a",), ("a2",), ("b",), ("c",)])

    def test_diverse_journey_harvest_prefers_new_task_sets_before_replacements(self):
        candidates = [
            (-20.0, SimpleNamespace(signature=("replacement_strong",), task_set=(1, 2))),
            (-5.0, SimpleNamespace(signature=("new_a",), task_set=(3,))),
            (-4.0, SimpleNamespace(signature=("new_b",), task_set=(4,))),
            (-3.0, SimpleNamespace(signature=("replacement_fill",), task_set=(2, 5))),
        ]

        selection = _select_diverse_journey_candidates(
            candidates,
            max_returned=3,
            top_k_strongest=1,
            min_fill=3,
            max_jaccard=0.0,
            max_containment=0.0,
            existing_task_sets={frozenset((1, 2)), frozenset((2, 5))},
        )

        self.assertEqual(selection.candidate_negative_count, 4)
        self.assertEqual(selection.candidate_new_task_set_count, 2)
        self.assertEqual(selection.selected_new_task_set_count, 2)
        self.assertEqual(selection.selected_replacement_task_set_count, 1)
        self.assertEqual(
            [journey.signature for journey in selection.journeys],
            [("replacement_strong",), ("new_a",), ("new_b",)],
        )

    def test_diverse_journey_harvest_strongest_phase_uses_global_true_rc(self):
        candidates = [
            (-20.0, SimpleNamespace(signature=("replacement_strong",), task_set=(1, 2))),
            (-5.0, SimpleNamespace(signature=("new_a",), task_set=(3,))),
            (-4.0, SimpleNamespace(signature=("new_b",), task_set=(4,))),
        ]

        selection = _select_diverse_journey_candidates(
            candidates,
            max_returned=1,
            top_k_strongest=1,
            min_fill=1,
            existing_task_sets={frozenset((1, 2))},
            prefer_new_task_sets=True,
        )

        self.assertEqual(selection.selected_count, 1)
        self.assertEqual(selection.selected_replacement_task_set_count, 1)
        self.assertEqual([journey.signature for journey in selection.journeys], [("replacement_strong",)])

    def test_diverse_journey_harvest_new_task_set_quota_overrides_strong_replacements(self):
        candidates = [
            (-30.0, SimpleNamespace(signature=("replacement_a",), task_set=(1, 2))),
            (-29.0, SimpleNamespace(signature=("replacement_b",), task_set=(2, 5))),
            (-4.0, SimpleNamespace(signature=("new_a",), task_set=(3,))),
            (-3.0, SimpleNamespace(signature=("new_b",), task_set=(4,))),
            (-2.0, SimpleNamespace(signature=("new_c",), task_set=(6,))),
        ]

        selection = _select_diverse_journey_candidates(
            candidates,
            max_returned=4,
            top_k_strongest=2,
            min_fill=4,
            min_new_task_sets=2,
            existing_task_sets={frozenset((1, 2)), frozenset((2, 5))},
            prefer_new_task_sets=True,
        )

        self.assertEqual(selection.candidate_new_task_set_count, 3)
        self.assertGreaterEqual(selection.selected_new_task_set_count, 2)
        self.assertIn(("new_a",), [journey.signature for journey in selection.journeys])
        self.assertIn(("new_b",), [journey.signature for journey in selection.journeys])

    def test_diverse_journey_harvest_priority_task_set_quota_keeps_active_support(self):
        candidates = [
            (-50.0, SimpleNamespace(signature=("inactive_replacement",), task_set=(1, 2))),
            (-40.0, SimpleNamespace(signature=("inactive_replacement_2",), task_set=(2, 5))),
            (-3.0, SimpleNamespace(signature=("active_repair",), task_set=(7, 8))),
            (-2.0, SimpleNamespace(signature=("new_direction",), task_set=(9,))),
        ]

        selection = _select_diverse_journey_candidates(
            candidates,
            max_returned=3,
            top_k_strongest=2,
            min_fill=3,
            min_priority_task_sets=1,
            existing_task_sets={frozenset((1, 2)), frozenset((2, 5)), frozenset((7, 8))},
            priority_task_sets={frozenset((7, 8))},
            prefer_new_task_sets=True,
        )

        self.assertEqual(selection.candidate_priority_task_set_count, 1)
        self.assertEqual(selection.selected_priority_task_set_count, 1)
        self.assertIn(("active_repair",), [journey.signature for journey in selection.journeys])

    def test_diverse_journey_harvest_priority_overlap_keeps_near_active_support(self):
        candidates = [
            (-50.0, SimpleNamespace(signature=("far_strong",), task_set=(8, 9))),
            (-3.0, SimpleNamespace(signature=("near_active",), task_set=(1, 2, 4))),
            (-2.0, SimpleNamespace(signature=("weak_new",), task_set=(6,))),
        ]

        selection = _select_diverse_journey_candidates(
            candidates,
            max_returned=2,
            top_k_strongest=1,
            min_fill=2,
            min_priority_task_sets=1,
            existing_task_sets={frozenset((8, 9))},
            priority_task_sets={frozenset((1, 2, 3))},
            priority_overlap_threshold=0.5,
            prefer_new_task_sets=True,
        )

        self.assertEqual(selection.candidate_priority_task_set_count, 1)
        self.assertEqual(selection.selected_priority_task_set_count, 1)
        self.assertIn(("near_active",), [journey.signature for journey in selection.journeys])

    def test_support_aware_harvest_prioritizes_active_support_changes(self):
        candidates = [
            (-100.0, SimpleNamespace(signature=("weak_replacement_a",), task_set=(1, 2))),
            (-90.0, SimpleNamespace(signature=("weak_replacement_b",), task_set=(3, 4))),
            (-80.0, SimpleNamespace(signature=("weak_replacement_c",), task_set=(5, 6))),
            (-10.0, SimpleNamespace(signature=("support_change",), task_set=(9, 10))),
            (-8.0, SimpleNamespace(signature=("new_mask",), task_set=(11,))),
        ]

        selection = _select_diverse_journey_candidates(
            candidates,
            max_returned=4,
            top_k_strongest=0,
            min_fill=4,
            existing_task_sets={
                frozenset((1, 2)),
                frozenset((3, 4)),
                frozenset((5, 6)),
                frozenset((9, 10)),
            },
            priority_task_sets={frozenset((1, 2)), frozenset((3, 4))},
            support_aware_enabled=True,
            support_task_sets={frozenset((1, 2)), frozenset((3, 4))},
            support_overlap_threshold=0.1,
            replacement_cap=1,
            strong_replacement_threshold=-200.0,
            prefer_new_task_sets=True,
        )

        signatures = [journey.signature for journey in selection.journeys]
        self.assertIn(("new_mask",), signatures)
        self.assertIn(("support_change",), signatures)
        self.assertEqual(selection.candidate_support_changing_count, 3)
        self.assertGreaterEqual(selection.selected_support_changing_count, 2)
        self.assertEqual(selection.selected_weak_replacement_count, 1)

    def test_support_aware_harvest_replacement_cap_is_soft_for_min_fill(self):
        candidates = [
            (-10.0, SimpleNamespace(signature=("weak_a",), task_set=(1, 2))),
            (-9.0, SimpleNamespace(signature=("weak_b",), task_set=(3, 4))),
            (-8.0, SimpleNamespace(signature=("weak_c",), task_set=(5, 6))),
        ]

        selection = _select_diverse_journey_candidates(
            candidates,
            max_returned=3,
            top_k_strongest=0,
            min_fill=3,
            existing_task_sets={frozenset((1, 2)), frozenset((3, 4)), frozenset((5, 6))},
            support_aware_enabled=True,
            replacement_cap=1,
            strong_replacement_threshold=-100.0,
        )

        self.assertEqual(selection.selected_count, 3)
        self.assertEqual(selection.selected_weak_replacement_count, 3)
        self.assertEqual(selection.fallback_fill_count, 2)

    def test_unique_route_partial_bound_gets_available_mask_without_unique_task(self):
        class FakeUniqueRoute:
            full_mask = 0b111

            def __init__(self):
                self.calls = []

            def partial_value(
                self,
                last,
                available_mask,
                remaining_slots_in_sortie,
                future_sorties,
                current_time,
                current_energy,
            ):
                self.calls.append(int(available_mask))
                return 0.0

        unique_route = FakeUniqueRoute()
        label = _SortiePartialLabel(
            sequence=(2,),
            mask=0b010,
            last=2,
            partial=SimpleNamespace(
                lower_start=0.0,
                upper_start=100.0,
                offset=0.0,
                travel_cost=0.0,
                service_cost=0.0,
                travel_energy=0.0,
                service_energy=0.0,
            ),
        )

        _direct_sortie_partial_completion_bound_check(
            SimpleNamespace(sortie_limit=2),
            FutureDuals({}, {}, {}, {}, {}, {}),
            label,
            {1: 0, 2: 1, 3: 2},
            base_reduced_cost=-10.0,
            journey_label_value=0.0,
            journey_label_mask=0b001,
            journey_label_count=0,
            earliest_start=0.0,
            completion_bound=None,
            unique_task_bound=None,
            unique_route_bound=unique_route,
            positive_cut_reward_bound=None,
            max_tasks_per_sortie=3,
            cut_duals={},
            cuts=tuple(),
            cut_masks=tuple(),
            eps=1.0e-6,
        )

        self.assertEqual(unique_route.calls, [0b100])

    def test_unique_route_suffix_bound_gets_available_mask_without_unique_task(self):
        class FakeUniqueRoute:
            full_mask = 0b111

            def __init__(self):
                self.calls = []

            def future_value(self, available_mask, remaining_sorties, current_time=0.0):
                self.calls.append(int(available_mask))
                return 0.0

        unique_route = FakeUniqueRoute()

        _direct_completed_journey_suffix_optimistic_objective(
            SimpleNamespace(),
            new_mask=0b011,
            new_end_time=0.0,
            new_objective=-10.0,
            remaining_sorties=1,
            completion_bound=None,
            unique_task_bound=None,
            unique_route_bound=unique_route,
            positive_cut_reward_bound=None,
            max_tasks_per_sortie=3,
            cut_duals={},
            cuts=tuple(),
            cut_masks=tuple(),
        )

        self.assertEqual(unique_route.calls, [0b100])

    def test_mask_closure_harvest_keeps_multiple_active_replacements(self):
        candidates = [
            (-10.0, SimpleNamespace(signature=("active_a",), task_set=(1, 2))),
            (-9.0, SimpleNamespace(signature=("active_b",), task_set=(1, 2))),
            (-8.0, SimpleNamespace(signature=("active_c",), task_set=(1, 2))),
            (-7.0, SimpleNamespace(signature=("other_a",), task_set=(3, 4))),
            (-6.0, SimpleNamespace(signature=("other_b",), task_set=(3, 4))),
            (-5.0, SimpleNamespace(signature=("new_mask",), task_set=(5,))),
        ]

        selection = _select_diverse_journey_candidates(
            candidates,
            max_returned=5,
            top_k_strongest=1,
            min_fill=5,
            existing_task_sets={frozenset((1, 2)), frozenset((3, 4))},
            priority_task_sets={frozenset((1, 2))},
            support_aware_enabled=True,
            support_task_sets={frozenset((1, 2))},
            mask_closure_enabled=True,
            mask_closure_max_masks=1,
            mask_closure_max_columns_per_mask=3,
            prefer_new_task_sets=True,
        )

        signatures = [journey.signature for journey in selection.journeys]
        self.assertIn(("active_a",), signatures)
        self.assertIn(("active_b",), signatures)
        self.assertIn(("active_c",), signatures)
        self.assertEqual(selection.mask_closure_candidate_task_set_count, 2)
        self.assertEqual(selection.mask_closure_selected_task_set_count, 1)
        self.assertEqual(selection.mask_closure_selected_count, 2)

    def test_harvest_respects_task_set_dominance_before_mask_closure(self):
        candidates = [
            (-20.0, SimpleNamespace(signature=("same_strong_rc",), task_set=(1, 2), cost=90.0)),
            (-8.0, SimpleNamespace(signature=("same_lowest_cost",), task_set=(1, 2), cost=80.0)),
            (-7.0, SimpleNamespace(signature=("same_dominated",), task_set=(1, 2), cost=110.0)),
            (-6.0, SimpleNamespace(signature=("new_higher_cost",), task_set=(3,), cost=70.0)),
            (-5.0, SimpleNamespace(signature=("new_lowest_cost",), task_set=(3,), cost=60.0)),
        ]

        selection = _select_diverse_journey_candidates(
            candidates,
            max_returned=5,
            top_k_strongest=5,
            min_fill=5,
            dominant_task_set_costs={frozenset((1, 2)): 100.0},
            existing_task_sets={frozenset((1, 2))},
            mask_closure_enabled=True,
            mask_closure_max_masks=2,
            mask_closure_max_columns_per_mask=3,
            allow_duplicate_task_sets=True,
        )

        self.assertTrue(selection.task_set_dominance_enabled)
        self.assertEqual(selection.candidate_negative_count, 5)
        self.assertEqual(selection.task_set_dominance_collapsed_count, 3)
        self.assertEqual(selection.mask_closure_selected_count, 0)
        self.assertEqual(selection.selected_count, 2)
        self.assertEqual(
            [journey.signature for journey in selection.journeys],
            [("same_lowest_cost",), ("new_lowest_cost",)],
        )

    def test_completion_bound_escalation_only_after_budget_hit_with_time(self):
        config = {
            "journey_certificate_completion_bound_escalation_enabled": True,
            "journey_certificate_completion_bound_escalation_min_remaining_time": 90.0,
            "journey_certificate_completion_bound_escalation_max_sequences": 1500000,
            "journey_certificate_completion_bound_escalation_max_dp_states": 500000,
            "journey_certificate_completion_bound_escalation_partial_max_states": 1500000,
        }
        budget_hit = SimpleNamespace(
            exhausted=False,
            journeys=[],
            reason="direct_label_sequence_budget",
        )
        self.assertTrue(_journey_completion_bound_escalation_needed(config, budget_hit, remaining=100.0))
        self.assertFalse(_journey_completion_bound_escalation_needed(config, budget_hit, remaining=60.0))
        time_limit = SimpleNamespace(exhausted=False, journeys=[], reason="time_limit")
        self.assertFalse(_journey_completion_bound_escalation_needed(config, time_limit, remaining=100.0))
        has_column = SimpleNamespace(
            exhausted=False,
            journeys=[object()],
            reason="direct_label_sequence_budget",
        )
        self.assertFalse(_journey_completion_bound_escalation_needed(config, has_column, remaining=100.0))

        base = JourneyPricingConfig(
            max_sequences=100000,
            max_dp_states=150000,
            direct_journey_label_partial_max_states=40000,
            direct_journey_label_completion_bound_two_cycle_enabled=True,
            direct_journey_label_completion_bound_two_cycle_max_states=100000,
        )
        updated, mode = _journey_completion_bound_escalation_config(config, base)
        self.assertEqual(updated.max_sequences, 1500000)
        self.assertEqual(updated.max_dp_states, 500000)
        self.assertEqual(updated.direct_journey_label_partial_max_states, 1500000)
        self.assertTrue(updated.direct_journey_label_completion_bound_two_cycle_enabled)
        self.assertTrue(mode["completion_bound_escalation"])
        self.assertTrue(mode["completion_bound_two_cycle"])

    def test_forbidden_journey_signatures_ignore_task_set_aliases(self):
        pool = JourneyPool()
        stored = SimpleNamespace(signature=(("stored",),))
        pool.journeys = [stored]
        pool.by_signature = {
            (("stored",),): stored,
            (("dominated_alias",),): stored,
        }
        self.assertEqual(_journey_forbidden_signatures_for_node(pool, tuple()), {(("stored",),)})

    def test_journey_node_depth_pricing_config_only_changes_branch_nodes(self):
        base = JourneyPricingConfig(
            time_limit=60.0,
            max_returned_journeys=96,
            streaming_min_negative_batch=24,
            streaming_min_returned_journeys=24,
            early_return_negative_min_count=24,
            journey_selection_mode="reduced_cost",
            direct_journey_label_completion_bound_two_cycle_enabled=True,
            direct_journey_label_ng_dssr_enabled=True,
            direct_journey_label_ng_probe_time_limit=1.5,
            direct_journey_label_ng_probe_min_journeys_for_early_return=9,
        )
        config = {
            "journey_branch_pricing_time_limit": 20.0,
            "journey_branch_pricing_max_returned_journeys": 48,
            "journey_branch_pricing_streaming_min_negative_batch": 8,
            "journey_branch_pricing_streaming_min_returned_journeys": 8,
            "journey_branch_pricing_streaming_partial_return_after_time": 15.0,
            "journey_branch_pricing_streaming_partial_return_min_journeys": 8,
            "journey_branch_pricing_early_return_negative_min_count": 8,
            "journey_branch_pricing_selection_mode": "integer_diverse",
            "journey_branch_pricing_direct_journey_label_ng_dssr_enabled": False,
            "journey_branch_pricing_direct_journey_label_ng_probe_time_limit": 0.25,
            "journey_branch_pricing_direct_journey_label_ng_probe_min_journeys_for_early_return": 2,
        }
        self.assertEqual(_journey_node_depth_pricing_config(config, base, 0), base)
        branch = _journey_node_depth_pricing_config(config, base, 1)
        self.assertEqual(branch.time_limit, 20.0)
        self.assertEqual(branch.max_returned_journeys, 48)
        self.assertEqual(branch.streaming_min_negative_batch, 8)
        self.assertEqual(branch.streaming_min_returned_journeys, 8)
        self.assertEqual(branch.streaming_partial_return_after_time, 15.0)
        self.assertEqual(branch.streaming_partial_return_min_journeys, 8)
        self.assertEqual(branch.early_return_negative_min_count, 8)
        self.assertEqual(branch.journey_selection_mode, "integer_diverse")
        self.assertFalse(branch.direct_journey_label_completion_bound_two_cycle_enabled)
        self.assertFalse(branch.direct_journey_label_ng_dssr_enabled)
        self.assertAlmostEqual(branch.direct_journey_label_ng_probe_time_limit, 0.25)
        self.assertEqual(branch.direct_journey_label_ng_probe_min_journeys_for_early_return, 2)

        branch_keep_two_cycle = _journey_node_depth_pricing_config(
            {**config, "journey_certificate_completion_bound_two_cycle_branch_enabled": True},
            base,
            1,
        )
        self.assertTrue(branch_keep_two_cycle.direct_journey_label_completion_bound_two_cycle_enabled)

    def test_journey_fleet_limit_slack_tightens_only_when_cost_safe(self):
        data = replace(load_future_data("very_small"), vehicles=tuple(range(1, 9)))
        self.assertGreater(data.fixed_vehicle_cost, 0.0)
        used_solution = {1: [object()], 2: [object()]}
        unavoidable = unavoidable_nonvehicle_cost_lb(data)
        incumbent = float(unavoidable) + 3.5 * float(data.fixed_vehicle_cost)
        with tempfile.TemporaryDirectory() as tmp:
            logger = FutureLogger(Path(tmp) / "fleet_limit.jsonl", console=False)
            try:
                unchanged = _update_journey_fleet_limit(
                    data,
                    logger,
                    8,
                    incumbent,
                    used_solution,
                    1,
                    slack=0,
                )
                tightened = _update_journey_fleet_limit(
                    data,
                    logger,
                    8,
                    incumbent,
                    used_solution,
                    2,
                    slack=1,
                )
            finally:
                logger.close()
        self.assertEqual(unchanged, 8)
        self.assertEqual(tightened, 3)

    def test_journey_pool_restart_is_opt_in_and_keeps_core_columns(self):
        data = load_future_data("very_small")

        def journey(jid: int, tasks: tuple[int, ...], cost: float) -> JourneyColumn:
            return JourneyColumn(
                id=jid,
                trips=tuple(),
                task_set=frozenset(tasks),
                start_time=0.0,
                end_time=0.0,
                travel_cost=float(cost),
                fixed_vehicle_cost=0.0,
                cost=float(cost),
                signature=((tuple(tasks), (f"p{jid}",), float(jid)),),
            )

        columns = [
            journey(0, (1,), 10.0),
            journey(1, (2,), 11.0),
            journey(2, (3,), 12.0),
            journey(3, (1, 2), 13.0),
            journey(4, (2, 3), 14.0),
            journey(5, (1, 3), 15.0),
        ]
        pool = JourneyPool()
        for col in columns:
            pool.add(col)
        solution = SimpleNamespace(journey_values=[(columns[3], 1.0)])
        logger = FutureLogger(None, console=False)

        same, restarted = _maybe_restart_journey_pool(
            data,
            {"journey_pool_restart_enabled": False},
            pool,
            solution,
            {},
            [columns[4]],
            logger,
            3,
            3,
            0,
        )
        self.assertFalse(restarted)
        self.assertIs(same, pool)

        root_same, root_restarted = _maybe_restart_journey_pool(
            data,
            {
                "journey_pool_restart_enabled": True,
                "journey_pool_restart_min_depth": 1,
                "journey_pool_restart_after_flat_rounds": 2,
                "journey_pool_restart_min_columns": 3,
            },
            pool,
            solution,
            {},
            [columns[4]],
            logger,
            3,
            3,
            0,
            depth=0,
        )
        self.assertFalse(root_restarted)
        self.assertIs(root_same, pool)

        shrunk, restarted = _maybe_restart_journey_pool(
            data,
            {
                "journey_pool_restart_enabled": True,
                "journey_pool_restart_after_flat_rounds": 2,
                "journey_pool_restart_min_columns": 3,
                "journey_pool_restart_keep_task_sets": 1,
                "journey_pool_restart_keep_recent": 1,
                "journey_pool_restart_max_times": 1,
            },
            pool,
            solution,
            {},
            [columns[4]],
            logger,
            3,
            3,
            0,
            depth=1,
        )
        self.assertTrue(restarted)
        self.assertLess(len(shrunk.journeys), len(pool.journeys))
        signatures = {col.signature for col in shrunk.journeys}
        self.assertIn(columns[0].signature, signatures)
        self.assertIn(columns[3].signature, signatures)
        self.assertIn(columns[4].signature, signatures)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_incomplete_pricing_does_not_report_dual_bound(self):
        data = replace(load_future_data("very_small"), vehicles=(1, 2))
        fake_rmp = SimpleNamespace(
            optimal=True,
            objective=42.0,
            duals=JourneyDuals(cover={int(task): 0.0 for task in data.tasks}, fleet_limit=0.0),
            journey_values=[],
            status="OPTIMAL",
            variable_count=0,
        )
        fake_pricing = JourneyPricingResult(
            journeys=[],
            exhausted=False,
            best_reduced_cost=-1.0,
            generated_sequences=1,
            evaluated_timed_trips=1,
            candidate_trips=1,
            selected_trips=0,
            status="INCOMPLETE",
            reason="test_incomplete",
        )
        with tempfile.TemporaryDirectory() as tmp:
            logger = FutureLogger(Path(tmp) / "journey.jsonl", console=False)
            try:
                with patch("BPC_future.solver.journey_driver.solve_journey_rmp", return_value=fake_rmp), patch(
                    "BPC_future.solver.journey_driver.price_journeys",
                    return_value=fake_pricing,
                ):
                    result = solve_bpc_future_journey(
                        data,
                        {
                            "time_limit": 10.0,
                            "journey_heuristic_pricing_enabled": False,
                            "initial_composite_seed_enabled": False,
                            "initial_single_task_starts_per_task": 1,
                            "journey_pool_time_limit": 0.1,
                        },
                        logger=logger,
                    )
            finally:
                logger.close()
        self.assertEqual(result.status, "TIME_LIMIT")
        self.assertIsNone(result.dual_bound)
        self.assertIsNone(result.gap)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_journey_duplicate_exact_negative_does_not_certificate(self):
        data = replace(load_future_data("very_small"), vehicles=(1, 2))
        fake_rmp = SimpleNamespace(
            optimal=True,
            objective=42.0,
            duals=JourneyDuals(cover={int(task): 0.0 for task in data.tasks}, fleet_limit=0.0),
            journey_values=[],
            status="OPTIMAL",
            variable_count=0,
        )
        fake_pricing = JourneyPricingResult(
            journeys=[SimpleNamespace(signature=("duplicate",))],
            exhausted=True,
            best_reduced_cost=-1.0,
            generated_sequences=1,
            evaluated_timed_trips=1,
            candidate_trips=1,
            selected_trips=1,
            status="OPTIMAL",
            reason="negative_journey",
        )
        with tempfile.TemporaryDirectory() as tmp:
            logger = FutureLogger(Path(tmp) / "journey.jsonl", console=False)
            try:
                with patch("BPC_future.solver.journey_driver.solve_journey_rmp", return_value=fake_rmp), patch(
                    "BPC_future.solver.journey_driver.price_journeys",
                    return_value=fake_pricing,
                ), patch("BPC_future.solver.journey_driver._add_priced_journeys", return_value=0):
                    result = solve_bpc_future_journey(
                        data,
                        {
                            "time_limit": 10.0,
                            "journey_heuristic_pricing_enabled": False,
                            "initial_composite_seed_enabled": False,
                            "initial_single_task_starts_per_task": 1,
                            "journey_pool_time_limit": 0.1,
                        },
                        logger=logger,
                    )
            finally:
                logger.close()
        self.assertEqual(result.status, "TIME_LIMIT")
        self.assertIsNone(result.dual_bound)
        self.assertIsNone(result.gap)

    def test_heuristic_pricing_path_cap_and_diverse_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = load_future_data(str(graph_path))

        vehicle = data.vehicles[0]
        duals = FutureDuals(
            cover={1: 100.0},
            task_vehicle={},
            sortie_count={vehicle: 0.0},
            time_occupation={},
            ordering={},
            branches={},
        )
        full = price_timed_trips(
            data,
            duals,
            tuple(),
            vehicle=vehicle,
            config=PricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=1,
                max_returned_trips=10,
                heuristic=True,
                selection_mode="reduced_cost",
            ),
        )
        capped = price_timed_trips(
            data,
            duals,
            tuple(),
            vehicle=vehicle,
            config=PricingConfig(
                time_bucket_size=5.0,
                start_time_step=10.0,
                max_tasks_per_trip=1,
                max_returned_trips=1,
                heuristic=True,
                selection_mode="diverse",
                max_path_combinations_per_sequence=1,
                path_dominance_enabled=True,
            ),
        )
        self.assertGreater(full.evaluated_timed_trips, capped.evaluated_timed_trips)
        self.assertEqual(capped.diverse_selected, capped.negative_trips)
        self.assertLessEqual(capped.negative_trips, 1)

    def test_journey_profile_labeling_can_be_gated_by_cg_iter(self):
        data = load_future_data("very_small")
        config = {
            "journey_pricing_profile_labeling_enabled": True,
            "journey_pricing_profile_labeling_min_cg_iter": 3,
            "journey_pricing_direct_journey_label_pricing_enabled": True,
            "journey_pricing_direct_journey_label_min_cg_iter": 4,
            "journey_pricing_direct_journey_label_ng_dssr_enabled": True,
            "journey_pricing_direct_journey_label_ng_min_cg_iter": 3,
            "journey_pricing_direct_journey_label_ng_memory_size": 5,
            "journey_pricing_direct_journey_label_dssr_max_iterations": 3,
            "journey_pricing_direct_journey_label_ng_max_labels": 1234,
                "journey_pricing_direct_journey_label_ng_min_negative_journeys": 7,
                "journey_pricing_direct_journey_label_ng_exact_probe_enabled": True,
                "journey_pricing_direct_journey_label_ng_probe_certificate_enabled": True,
                "journey_pricing_direct_journey_label_ng_sequence_key_enabled": False,
                "journey_pricing_direct_journey_label_ng_reset_memory_between_sorties_enabled": True,
                "journey_pricing_direct_journey_label_ng_visit_mask_dominance_enabled": True,
                "journey_pricing_direct_journey_label_ng_disable_below_remaining": 4.5,
            "journey_pricing_max_returned_journeys": 64,
            "journey_pricing_late_max_returned_journeys": 256,
            "journey_pricing_late_max_returned_min_cg_iter": 3,
            "journey_pricing_late_early_return_negative_min_count": 32,
            "journey_pricing_late_early_return_new_task_set_min_count": 6,
            "journey_pricing_late_streaming_min_negative_batch": 48,
            "journey_pricing_late_streaming_min_returned_journeys": 7,
            "journey_pricing_late_selection_mode": "integer_diverse",
            "journey_pricing_late_profile_true_rc_materialization_slack": 2.5,
            "journey_pricing_late_profile_true_rc_materialization_max_candidates": 17,
            "journey_pricing_late_profile_no_negative_true_rc_materialization_slack": 0.75,
            "journey_pricing_late_profile_no_negative_true_rc_materialization_max_candidates": 11,
            "journey_pricing_late_profile_replacement_true_rc_materialization_slack": 1.25,
            "journey_pricing_late_profile_replacement_true_rc_materialization_max_candidates": 19,
            "journey_pricing_late_profile_cross_count_true_rc_materialization_slack": 1.75,
            "journey_pricing_late_profile_cross_count_true_rc_materialization_max_candidates": 23,
            "journey_pricing_late_profile_true_rc_candidate_scan_factor": 9,
            "journey_pricing_late_profile_true_rc_candidate_scan_max_candidates": 211,
            "journey_pricing_dp_cross_count_dominance_enabled": True,
            "journey_pricing_late_dp_cross_count_dominance_enabled": False,
            "journey_pricing_streaming_enabled": True,
            "journey_pricing_streaming_min_cg_iter": 3,
            "journey_pricing_streaming_min_negative_batch": 12,
            "journey_pricing_early_return_negative_min_count": 10,
            "journey_pricing_time_limit": 5.0,
        }
        early = _journey_pricing_config(
            data,
            config,
            5.0,
            5.0,
            1.0e-6,
            5.0,
            heuristic=False,
            cg_iter=1,
        )
        late = _journey_pricing_config(
            data,
            config,
            5.0,
            5.0,
            1.0e-6,
            5.0,
            heuristic=False,
            cg_iter=3,
        )
        late_low_remaining = _journey_pricing_config(
            data,
            config,
            5.0,
            5.0,
            1.0e-6,
            4.0,
            heuristic=False,
            cg_iter=3,
        )
        heuristic_low_remaining = _journey_pricing_config(
            data,
            config,
            5.0,
            5.0,
            1.0e-6,
            4.0,
            heuristic=True,
            cg_iter=3,
        )
        exact_low_remaining_legacy_gate = _journey_pricing_config(
            data,
            {
                **config,
                "journey_pricing_direct_journey_label_ng_disable_below_remaining_exact_enabled": True,
            },
            5.0,
            5.0,
            1.0e-6,
            4.0,
            heuristic=False,
            cg_iter=3,
        )
        self.assertFalse(early.profile_labeling_enabled)
        self.assertFalse(early.streaming_pricing_enabled)
        self.assertTrue(late.profile_labeling_enabled)
        self.assertTrue(late.streaming_pricing_enabled)
        self.assertFalse(late.direct_journey_label_pricing_enabled)
        self.assertFalse(early.direct_journey_label_ng_dssr_enabled)
        self.assertEqual(early.max_returned_journeys, 64)
        self.assertEqual(late.max_returned_journeys, 256)
        self.assertEqual(early.early_return_negative_min_count, 10)
        self.assertEqual(early.early_return_new_task_set_min_count, 0)
        self.assertEqual(early.streaming_min_negative_batch, 12)
        self.assertEqual(early.streaming_min_returned_journeys, 1)
        self.assertEqual(early.journey_selection_mode, "reduced_cost")
        self.assertEqual(early.direct_journey_label_early_return_negative_min_count, 10)
        self.assertEqual(late.early_return_negative_min_count, 32)
        self.assertEqual(late.early_return_new_task_set_min_count, 6)
        self.assertEqual(late.streaming_min_negative_batch, 48)
        self.assertEqual(late.streaming_min_returned_journeys, 7)
        self.assertEqual(late.journey_selection_mode, "integer_diverse")
        self.assertAlmostEqual(late.profile_true_rc_materialization_slack, 2.5)
        self.assertEqual(late.profile_true_rc_materialization_max_candidates, 17)
        self.assertAlmostEqual(late.profile_no_negative_true_rc_materialization_slack, 0.75)
        self.assertEqual(late.profile_no_negative_true_rc_materialization_max_candidates, 11)
        self.assertAlmostEqual(late.profile_replacement_true_rc_materialization_slack, 1.25)
        self.assertEqual(late.profile_replacement_true_rc_materialization_max_candidates, 19)
        self.assertAlmostEqual(late.profile_cross_count_true_rc_materialization_slack, 1.75)
        self.assertEqual(late.profile_cross_count_true_rc_materialization_max_candidates, 23)
        self.assertEqual(late.profile_true_rc_candidate_scan_factor, 9)
        self.assertEqual(late.profile_true_rc_candidate_scan_max_candidates, 211)
        self.assertAlmostEqual(early.profile_true_rc_materialization_slack, 0.0)
        self.assertEqual(early.profile_true_rc_materialization_max_candidates, 0)
        self.assertAlmostEqual(early.profile_no_negative_true_rc_materialization_slack, 0.0)
        self.assertEqual(early.profile_no_negative_true_rc_materialization_max_candidates, 0)
        self.assertAlmostEqual(early.profile_replacement_true_rc_materialization_slack, 0.0)
        self.assertEqual(early.profile_replacement_true_rc_materialization_max_candidates, 0)
        self.assertAlmostEqual(early.profile_cross_count_true_rc_materialization_slack, 0.0)
        self.assertEqual(early.profile_cross_count_true_rc_materialization_max_candidates, 0)
        self.assertEqual(early.profile_true_rc_candidate_scan_factor, 1)
        self.assertEqual(early.profile_true_rc_candidate_scan_max_candidates, 0)
        self.assertTrue(early.dp_cross_count_dominance_enabled)
        self.assertFalse(late.dp_cross_count_dominance_enabled)
        self.assertEqual(late.direct_journey_label_early_return_negative_min_count, 32)
        self.assertTrue(late.direct_journey_label_ng_dssr_enabled)
        self.assertEqual(late.direct_journey_label_ng_memory_size, 5)
        self.assertEqual(late.direct_journey_label_dssr_max_iterations, 3)
        self.assertEqual(late.direct_journey_label_ng_max_labels, 1234)
        self.assertEqual(late.direct_journey_label_ng_min_negative_journeys, 7)
        self.assertTrue(late.direct_journey_label_ng_exact_probe_enabled)
        self.assertTrue(late.direct_journey_label_ng_probe_certificate_enabled)
        self.assertFalse(late.direct_journey_label_ng_sequence_key_enabled)
        self.assertTrue(late.direct_journey_label_ng_reset_memory_between_sorties_enabled)
        self.assertTrue(late.direct_journey_label_ng_visit_mask_dominance_enabled)
        self.assertTrue(late_low_remaining.direct_journey_label_ng_dssr_enabled)
        self.assertFalse(heuristic_low_remaining.direct_journey_label_ng_dssr_enabled)
        self.assertFalse(exact_low_remaining_legacy_gate.direct_journey_label_ng_dssr_enabled)
        direct = _journey_pricing_config(
            data,
            config,
            5.0,
            5.0,
            1.0e-6,
            5.0,
            heuristic=False,
            cg_iter=4,
        )
        self.assertTrue(direct.direct_journey_label_pricing_enabled)
        self.assertEqual(direct.direct_journey_label_early_return_negative_min_count, 32)

        alias_config = {
            "journey_pricing_direct_label_enabled": True,
            "journey_pricing_direct_journey_label_min_cg_iter": 1,
            "journey_pricing_time_limit": 5.0,
        }
        alias_direct = _journey_pricing_config(
            data,
            alias_config,
            5.0,
            5.0,
            1.0e-6,
            5.0,
            heuristic=False,
            cg_iter=1,
        )
        self.assertTrue(alias_direct.direct_journey_label_pricing_enabled)

    def test_hungarian_min_cost_basic(self):
        value = _hungarian_min_cost(
            [
                [4.0, 1.0, 3.0],
                [2.0, 0.0, 5.0],
                [3.0, 2.0, 2.0],
            ]
        )
        self.assertAlmostEqual(value, 5.0, places=6)

    def test_sortie_assignment_unavoidable_lb_is_below_singleton_cover(self):
        data = load_future_data("very_small")
        service = sum(data.task_value(task, "c_srv") for task in data.tasks)
        singleton_travel = sum(
            min(option.cost for option in data.options(0, task))
            + min(option.cost for option in data.options(task, 0))
            for task in data.tasks
        )
        lb = _sortie_path_assignment_nonvehicle_lb(data)
        self.assertGreaterEqual(lb, service - 1.0e-6)
        self.assertLessEqual(lb, service + singleton_travel + 1.0e-6)

    def test_unavoidable_cost_lb_dominates_degree_lb(self):
        data = load_future_data("very_small")
        service = sum(data.task_value(task, "c_srv") for task in data.tasks)
        inbound_sum = 0.0
        outbound_sum = 0.0
        for task in data.tasks:
            inbound_sum += min(
                min(option.cost for option in data.options(source, task))
                for source in (0, *data.tasks)
                if int(source) != int(task) and (int(source), int(task)) in data.arc_options
            )
            outbound_sum += min(
                min(option.cost for option in data.options(task, target))
                for target in (0, *data.tasks)
                if int(target) != int(task) and (int(task), int(target)) in data.arc_options
            )
        self.assertGreaterEqual(unavoidable_nonvehicle_cost_lb(data), service + max(inbound_sum, outbound_sum) - 1.0e-6)

    def test_computed_fleet_bound_uses_slack_when_cost_safe(self):
        data = replace(load_future_data("very_small"), fixed_vehicle_cost=1000.0)
        updated, diag = apply_fleet_bound_override(
            data,
            {
                "fleet_bound_mode": "computed",
                "fleet_bound_slack": 1,
                "fleet_bound_cost_safe": True,
                "time_bucket_size": 5.0,
                "pricing_start_time_step": 5.0,
            },
        )
        self.assertIsNotNone(diag.heuristic_R)
        assert diag.heuristic_R is not None
        self.assertEqual(diag.new_R_bar, min(len(data.tasks), diag.heuristic_R + 1))
        self.assertEqual(len(updated.vehicles), diag.new_R_bar)
        self.assertIn("dominates", diag.reason)

    def test_computed_fleet_bound_falls_back_to_objective_safe_cap(self):
        data = replace(load_future_data("very_small"), fixed_vehicle_cost=1.0)
        with patch("BPC_future.core.fleet_bound.unavoidable_nonvehicle_cost_lb", return_value=0.0):
            updated, diag = apply_fleet_bound_override(
                data,
                {
                    "fleet_bound_mode": "computed",
                    "fleet_bound_slack": 1,
                    "fleet_bound_cost_safe": True,
                    "time_bucket_size": 5.0,
                    "pricing_start_time_step": 5.0,
                },
            )
        self.assertIsNotNone(diag.heuristic_R)
        self.assertEqual(diag.new_R_bar, len(data.tasks))
        self.assertEqual(len(updated.vehicles), len(data.tasks))
        self.assertIn("objective_safe", diag.reason)

    def test_computed_fleet_bound_uses_unavoidable_cost_lb(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = _write_logical_graph_case(Path(tmp), outbound_energy=10.0, inbound_energy=10.0)
            data = replace(load_future_data(str(graph_path)), fixed_vehicle_cost=20.0)
        lb = unavoidable_nonvehicle_cost_lb(data)
        self.assertGreater(lb, 0.0)
        updated, diag = apply_fleet_bound_override(
            data,
            {
                "fleet_bound_mode": "computed",
                "fleet_bound_slack": 1,
                "fleet_bound_cost_safe": True,
                "time_bucket_size": 5.0,
                "pricing_start_time_step": 5.0,
            },
        )
        self.assertEqual(diag.unavoidable_cost_lb, lb)
        self.assertIn("unavoidable", diag.reason)
        self.assertEqual(len(updated.vehicles), diag.new_R_bar)

    def test_computed_fleet_bound_fallback_task_count_when_heuristic_fails(self):
        data = replace(load_future_data("very_small"), arc_options={})
        updated, diag = apply_fleet_bound_override(data, {"fleet_bound_mode": "computed"})
        self.assertIsNone(diag.heuristic_R)
        self.assertEqual(diag.new_R_bar, len(data.tasks))
        self.assertEqual(len(updated.vehicles), len(data.tasks))

    def test_degenerate_bulk_pricing_trigger_is_gap_guarded(self):
        solution = FutureRMPSolution(
            status="OPTIMAL",
            objective=100.0,
            duals=None,
            trip_values=[],
            y_values={},
            artificial_cover_values={},
            variable_count=0,
            constraint_count=0,
            theta_reduced_costs={},
        )
        config = {
            "exact_certificate_mode_enabled": True,
            "exact_certificate_min_cg_iter": 10,
            "exact_degenerate_bulk_pricing_enabled": True,
            "exact_degenerate_bulk_min_cg_iter": 3,
            "exact_degenerate_bulk_gap_threshold": 1.0e-6,
        }
        self.assertTrue(_should_use_bulk_exact_pricing(config, 3, "phase2", solution, 100.0, 1.0e-6))
        self.assertFalse(_should_use_bulk_exact_pricing(config, 3, "phase2", solution, 101.0, 1.0e-6))
        self.assertFalse(_should_use_bulk_exact_pricing(config, 2, "phase2", solution, 100.0, 1.0e-6))

    def test_time_occupation_row_separator_adds_only_violated_rows(self):
        data = load_future_data("very_small")
        vehicle = data.vehicles[0]
        trip1 = evaluate_timed_trip(data, (1,), 0.0, time_bucket_size=20.0)
        trip2 = evaluate_timed_trip(data, (2,), 0.0, time_bucket_size=20.0)
        self.assertIsNotNone(trip1)
        self.assertIsNotNone(trip2)
        assert trip1 is not None and trip2 is not None
        solution = FutureRMPSolution(
            status="OPTIMAL",
            objective=0.0,
            duals=None,
            trip_values=[(trip1, vehicle, 1.0), (trip2, vehicle, 1.0)],
            y_values={vehicle: 1.0},
            artificial_cover_values={},
            variable_count=0,
            constraint_count=0,
            theta_reduced_costs={},
        )
        active: set[tuple[int, int]] = set()
        added = _separate_time_occupation_rows(data, solution, active, 20.0, 1.0e-7, (vehicle,))
        self.assertTrue(added)
        self.assertEqual(active, {(vehicle, bucket) for vehicle, bucket, _violation in added})
        self.assertFalse(_separate_time_occupation_rows(data, solution, active, 20.0, 1.0e-7, (vehicle,)))

    def test_pricing_compatible_cut_coefficients_and_duplicates(self):
        data = load_future_data("very_small")
        trip = evaluate_timed_trip(data, (1, 2), 0.0, time_bucket_size=5.0)
        self.assertIsNotNone(trip)
        assert trip is not None
        fleet_cut = FleetLowerBoundCut(1)
        sortie_cut = SortieLowerBoundCut(2)
        subset_cut = SubsetRowCut((1, 2, 3), 2)
        time_cut = TimePointCapacityCut(1, trip.start_time + 0.1)
        self.assertEqual(fleet_cut.coefficient(trip, 1), 0.0)
        self.assertEqual(fleet_cut.y_coefficient(1), 1.0)
        self.assertEqual(sortie_cut.coefficient(trip, 1), -1.0)
        self.assertEqual(sortie_cut.rhs, -2.0)
        self.assertEqual(subset_cut.coefficient(trip, 1), 1.0)
        self.assertEqual(time_cut.coefficient(trip, 1), 1.0)
        self.assertEqual(time_cut.coefficient(trip, 2), 0.0)
        self.assertEqual(time_cut.y_coefficient(1), -1.0)
        cuts = []
        keys = set()
        self.assertTrue(add_cut_unique(cuts, keys, subset_cut))
        self.assertFalse(add_cut_unique(cuts, keys, SubsetRowCut((3, 2, 1), 2)))
        self.assertEqual(len(cuts), 1)

    def test_journey_static_cuts_exclude_sortie_lower_bound(self):
        data = load_future_data("very_small")
        cuts = _journey_static_cuts(
            data,
            {
                "cuts_enabled": True,
                "fleet_lower_bound_cut_enabled": True,
                "sortie_lower_bound_cut_enabled": True,
                "static_subset_row_cuts_enabled": True,
                "static_subset_row_cut_budget": 3,
            },
        )
        kinds = [cut.kind for cut in cuts]
        self.assertIn("fleet_lower_bound", kinds)
        self.assertIn("subset_row", kinds)
        self.assertNotIn("sortie_lower_bound", kinds)
        self.assertTrue(_journey_task_set_dominance_safe(tuple(cuts), tuple()))

    def test_journey_static_cuts_compact_selection_keeps_valid_budgeted_src(self):
        data = load_future_data("very_small")
        cuts = _journey_static_cuts(
            data,
            {
                "cuts_enabled": True,
                "fleet_lower_bound_cut_enabled": True,
                "static_subset_row_cuts_enabled": True,
                "static_subset_row_cut_budget": 3,
                "static_subset_row_selection": "compact",
            },
        )
        subset_cuts = [cut for cut in cuts if isinstance(cut, SubsetRowCut)]
        self.assertEqual(len(subset_cuts), 3)
        self.assertTrue(all(cut.kind == "subset_row" and len(cut.tasks) >= 3 for cut in subset_cuts))
        self.assertTrue(_journey_task_set_dominance_safe(tuple(cuts), tuple()))
        score = _journey_static_subset_row_compactness_score(data, tuple(int(task) for task in data.tasks[:3]))
        self.assertTrue(math.isfinite(score))

    def test_journey_profile_pruning_is_not_safe_for_nonzero_fleet_cut_dual(self):
        cuts = (FleetLowerBoundCut(1),)
        self.assertTrue(_profile_cut_penalty_pruning_safe({}, cuts))
        self.assertFalse(_profile_cut_penalty_pruning_safe({0: 2.0}, cuts))
        self.assertFalse(_journey_task_set_dominance_safe((SortieLowerBoundCut(1),), tuple()))

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_heuristic_pricing_vehicle_limit_keeps_very_small_optimal(self):
        data = load_future_data("very_small")
        config = {
            "time_limit": 30,
            "max_nodes": 20,
            "max_cg_iterations": 30,
            "time_bucket_size": 2.0,
            "max_tasks_per_trip": 2,
            "heuristic_top_tasks": 4,
            "heuristic_max_sequences": 20,
            "heuristic_max_timed_evaluations": 2000,
            "heuristic_pricing_stop_after_first_add": True,
            "heuristic_pricing_vehicle_limit": 1,
            "exact_max_sequences": 0,
            "exact_max_timed_evaluations": 0,
            "max_trips_per_pricing": 50,
        }
        with tempfile.TemporaryDirectory() as tmp:
            logger = FutureLogger(Path(tmp) / "future.jsonl", console=False)
            try:
                result = solve_bpc_future(data, config, logger=logger)
            finally:
                logger.close()
        self.assertEqual(result.status, "OPTIMAL")
        self.assertAlmostEqual(result.primal_bound, 132.270984, places=5)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_rmp_reduced_cost_matches_manual_formula_with_cuts(self):
        data = load_future_data("very_small")
        trips = _single_task_grid_trips(data, bucket=10.0)
        cuts = (
            FleetLowerBoundCut(1),
            SortieLowerBoundCut(1),
            SubsetRowCut((1, 2, 3), 2),
            TimePointCapacityCut(data.vehicles[0], 0.1),
        )
        solution = solve_trip_time_rmp(
            data,
            trips,
            tuple(),
            time_bucket_size=10.0,
            cuts=cuts,
            capture_reduced_costs=True,
        )
        self.assertTrue(solution.optimal)
        assert solution.duals is not None
        self.assertTrue(solution.duals.cuts)
        for (trip_id, vehicle), solver_rc in solution.theta_reduced_costs.items():
            manual = manual_reduced_cost(trips[trip_id], vehicle, solution.duals, tuple(), cuts)
            self.assertAlmostEqual(solver_rc, manual, places=5)

    @unittest.skipUnless(HAS_SCIP, "PySCIPOpt unavailable")
    def test_very_small_future_solver_runs(self):
        data = load_future_data("very_small")
        config = {
            "time_limit": 30,
            "max_nodes": 20,
            "max_cg_iterations": 30,
            "time_bucket_size": 2.0,
            "max_tasks_per_trip": 2,
            "heuristic_top_tasks": 4,
            "heuristic_max_sequences": 20,
            "heuristic_max_timed_evaluations": 2000,
            "exact_max_sequences": 0,
            "exact_max_timed_evaluations": 0,
            "max_trips_per_pricing": 50,
        }
        with tempfile.TemporaryDirectory() as tmp:
            logger = FutureLogger(Path(tmp) / "future.jsonl", console=False)
            try:
                result = solve_bpc_future(data, config, logger=logger)
            finally:
                logger.close()
        self.assertIn(result.status, {"OPTIMAL", "TIME_LIMIT"})
        self.assertIsNotNone(result.primal_bound)
        self.assertGreater(result.columns, len(data.tasks))


def _single_task_grid_trips(data, *, bucket: float):
    trips = []
    seen = set()
    for task in data.tasks:
        start = 0.0
        while start <= data.horizon + 1.0e-9:
            trip = evaluate_timed_trip(data, (task,), start, time_bucket_size=bucket)
            if trip is not None and trip.signature not in seen:
                trips.append(trip)
                seen.add(trip.signature)
            start += bucket
    return trips


def _write_logical_graph_case(root: Path, *, outbound_energy: float, inbound_energy: float) -> Path:
    scenario = {
        "id": "logical_case",
        "depot": {"id": "depot", "xy_km": [10.0, 10.0]},
        "vehicle": {
            "R_bar": 1,
            "S_bar": 4,
            "Q": 6.0,
            "B_use": 80.0,
            "usable_battery_capacity_proxy": 80.0,
            "max_roundtrip_energy_proxy": 70.0,
            "survival_energy_reserve_proxy": 10.0,
            "rho": 2.0,
            "F": 50.0,
            "H": 720.0,
            "survival_energy_proxy_per_min": 0.01,
        },
        "scheduling": {
            "task_waiting_allowed": False,
            "depot_waiting_allowed": True,
            "horizon_min": 720.0,
            "objective": {
                "travel_cost_weight": 1.0,
                "energy_cost_weight": 0.25,
                "risk_cost_weight": 8.0,
            },
        },
        "tasks": [
            {
                "id": "task_1",
                "xy_km": [12.0, 10.0],
                "d": 1.0,
                "sigma": 0.0,
                "g": 0.0,
                "c_srv": 0.0,
                "r": 0.0,
                "D": 720.0,
            }
        ],
    }

    def options(energy: float) -> list[dict[str, object]]:
        return [
            _option("low_time", 10.0, energy, 1.4, 2.0),
            _option("low_energy", 12.0, energy * 0.95, 1.2, 2.2),
            _option("low_risk", 14.0, energy * 1.05, 0.4, 2.4),
        ]

    graph = {
        "scenario": scenario,
        "logical_graph": {
            "node_count": 2,
            "directed_edge_count": 2,
            "feasible_directed_edge_count": 2,
            "nodes": [
                {"id": "depot", "kind": "depot", "xy_km": [10.0, 10.0]},
                {"id": "task_1", "kind": "task", "xy_km": [12.0, 10.0]},
            ],
            "edges": [
                {
                    "from": "depot",
                    "to": "task_1",
                    "feasible": True,
                    "path_options": options(outbound_energy),
                },
                {
                    "from": "task_1",
                    "to": "depot",
                    "feasible": True,
                    "path_options": options(inbound_energy),
                },
            ],
        },
    }
    graph_path = root / "logical_case_logical_graph.json"
    graph_path.write_text(json.dumps(graph), encoding="utf-8")
    return graph_path


def _write_dominated_time_logical_graph_case(root: Path) -> Path:
    scenario = {
        "id": "dominated_time_case",
        "depot": {"id": "depot", "xy_km": [10.0, 10.0]},
        "vehicle": {
            "R_bar": 1,
            "S_bar": 4,
            "Q": 6.0,
            "B_use": 80.0,
            "usable_battery_capacity_proxy": 80.0,
            "max_roundtrip_energy_proxy": 70.0,
            "survival_energy_reserve_proxy": 10.0,
            "rho": 2.0,
            "F": 50.0,
            "H": 720.0,
            "survival_energy_proxy_per_min": 0.0,
        },
        "scheduling": {
            "task_waiting_allowed": False,
            "depot_waiting_allowed": True,
            "horizon_min": 720.0,
            "objective": {
                "travel_cost_weight": 1.0,
                "energy_cost_weight": 0.25,
                "risk_cost_weight": 8.0,
            },
        },
        "tasks": [
            {
                "id": "task_1",
                "xy_km": [12.0, 10.0],
                "d": 1.0,
                "sigma": 0.0,
                "g": 0.0,
                "c_srv": 0.0,
                "r": 0.0,
                "D": 720.0,
            }
        ],
    }

    def options(prefix: str) -> list[dict[str, object]]:
        return [
            _option(f"{prefix}_fast", 5.0, 10.0, 1.0, 2.0),
            _option(f"{prefix}_slow", 15.0, 10.0, 1.0, 2.0),
        ]

    graph = {
        "scenario": scenario,
        "logical_graph": {
            "node_count": 2,
            "directed_edge_count": 2,
            "feasible_directed_edge_count": 2,
            "nodes": [
                {"id": "depot", "kind": "depot", "xy_km": [10.0, 10.0]},
                {"id": "task_1", "kind": "task", "xy_km": [12.0, 10.0]},
            ],
            "edges": [
                {
                    "from": "depot",
                    "to": "task_1",
                    "feasible": True,
                    "path_options": options("out"),
                },
                {
                    "from": "task_1",
                    "to": "depot",
                    "feasible": True,
                    "path_options": options("back"),
                },
            ],
        },
    }
    graph_path = root / "dominated_time_case_logical_graph.json"
    graph_path.write_text(json.dumps(graph), encoding="utf-8")
    return graph_path


def _option(path_type: str, time_min: float, energy: float, risk: float, distance: float) -> dict[str, object]:
    return {
        "path_type": path_type,
        "aliases": [path_type],
        "travel_time_min": time_min,
        "energy_proxy": energy,
        "risk_integral": risk,
        "path_distance_km": distance,
        "path_cells": [[0, 0], [1, 1]],
        "path_xy": [[10.0, 10.0], [12.0, 10.0]],
    }


if __name__ == "__main__":
    unittest.main()

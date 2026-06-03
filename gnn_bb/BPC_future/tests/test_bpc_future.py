from __future__ import annotations

import math
import json
import tempfile
import time
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
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
    solve_journey_pool_master,
    solve_journey_rmp,
    solve_journey_stabilized_dual,
)
from BPC_future.master.rmp import FutureDuals, FutureRMPSolution, manual_reduced_cost, solve_trip_time_rmp
from BPC_future.pricing.journey_pricing import (
    JourneyPricingConfig,
    _CompatibleProfileCache,
    _SortieProfile,
    _SortieProfileCatalogState,
    _StreamingPricingStop,
    _TaskSetReducedCostLowerBoundCache,
    _TaskSetResourceLowerBoundCache,
    _branch_constraints_cache_key,
    _add_sortie_profile_skyline,
    _add_sortie_profile_online_skyline,
    _advance_sortie_label_resume_state,
    _filter_dominated_sortie_profiles,
    _direct_next_sortie_profiles,
    _direct_next_sortie_trips,
    _direct_sortie_profiles_to_trips,
    _generate_negative_sortie_profiles,
    _generate_negative_sortie_profiles_by_best_first_labels,
    _initial_sortie_label_resume_state,
    _instantiate_profile_journey_candidates,
    _cut_masks,
    _add_sortie_partial_label,
    _dominates_sortie_partial_label,
    _early_return_candidate_count,
    _profile_cut_penalty,
    _profile_cut_penalty_pruning_safe,
    _journey_task_set_branch_allowed,
    _journey_same_completion_possible,
    _price_journeys_by_streaming_profiles,
    _resume_sortie_profile_catalog,
    _select_negative_journey_candidates,
    _solve_best_journey_profile_dp,
    _sortie_profile_mask_allowed_by_branch,
    price_journeys,
)
from BPC_future.pricing.journey_pricing import JourneyPricingResult
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
from BPC_future.solver.driver import _separate_time_occupation_rows, _should_use_bulk_exact_pricing, solve_bpc_future
from BPC_future.solver.driver import _seed_initial_savings_trips
from BPC_future.solver.journey_driver import (
    JourneyBranchStats,
    JourneyNode,
    _choose_journey_branch,
    _filter_journeys_by_branch,
    _journey_certificate_pricing_config,
    _journey_allowed_by_branch,
    _journey_branch_same_mass,
    _journey_child_constraint_order,
    _journey_exact_pricing_budget,
    _journey_dual_current_pool_validation,
    _journey_dual_optimal_inequality_bounds,
    _journey_dual_hash,
    _journey_dual_vector,
    _journey_static_cuts,
    _journey_task_set_dominance_safe,
    _maybe_restart_journey_pool,
    _journey_pool_restart_triggered,
    _journey_progress_classification,
    _journey_node_depth_pricing_config,
    _journey_pricing_config,
    _journey_should_early_branch,
    _ordered_journey_child_constraints,
    _process_journey_branch_node,
    _select_journey_pricing_duals,
    _should_run_journey_pool_probe,
    _update_journey_fleet_limit,
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
        self.assertIs(pool.by_signature[dominated.signature], pool.journeys[0])

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
        self.assertIs(pool.by_signature[expensive.signature], pool.journeys[0])

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
        self.assertGreater(result.existing_journeys_filtered + result.dominated_task_set_journeys_filtered, 0)
        self.assertEqual(result.reason, "negative_journeys_already_in_pool")

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
    def test_streaming_journey_pricing_can_still_certificate_no_negative(self):
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
            ),
        )
        self.assertEqual(len(result.journeys), 1)
        self.assertLess(result.best_reduced_cost, 0.0)
        self.assertIn(first, result.journeys[0].task_set)
        self.assertIn(second, result.journeys[0].task_set)

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
        uncached, _gen, _eval, reason = _direct_next_sortie_trips(
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
            reason="exhausted",
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
                reason="exhausted",
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
                    reason="exhausted",
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
        self.assertEqual(updated.streaming_min_returned_journeys, 1)

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

    def test_journey_node_depth_pricing_config_only_changes_branch_nodes(self):
        base = JourneyPricingConfig(
            time_limit=60.0,
            max_returned_journeys=96,
            streaming_min_negative_batch=24,
            streaming_min_returned_journeys=24,
            early_return_negative_min_count=24,
            journey_selection_mode="reduced_cost",
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
            "journey_pricing_max_returned_journeys": 64,
            "journey_pricing_late_max_returned_journeys": 256,
            "journey_pricing_late_max_returned_min_cg_iter": 3,
            "journey_pricing_streaming_enabled": True,
            "journey_pricing_streaming_min_cg_iter": 3,
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
        self.assertFalse(early.profile_labeling_enabled)
        self.assertFalse(early.streaming_pricing_enabled)
        self.assertTrue(late.profile_labeling_enabled)
        self.assertTrue(late.streaming_pricing_enabled)
        self.assertFalse(late.direct_journey_label_pricing_enabled)
        self.assertEqual(early.max_returned_journeys, 64)
        self.assertEqual(late.max_returned_journeys, 256)
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

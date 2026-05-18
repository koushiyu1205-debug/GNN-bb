"""Tests for the branchpricecut vehicle-schedule BPC implementation."""

from __future__ import annotations

from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from branchpricecut.branching import BranchConstraint, schedule_allowed_by_branch
from branchpricecut.data import load_instance
from branchpricecut.logger import BPCLogger
from branchpricecut.ng_dssr import NGLabel, label_key, ng_dssr_schedule_pricing
from branchpricecut.pricing import DSSRSchedulePricing, exact_schedule_pricing
from branchpricecut.rmp import (
    RMPDuals,
    check_schedule_reduced_cost_consistency,
    manual_reduced_cost,
    solve_restricted_master_integer,
    solve_rmp_lp,
)
from branchpricecut.route_pool import (
    SortieRoute,
    build_portfolio_routes,
    route_allowed_by_branch,
    sortie_from_zero,
)
from branchpricecut.schedule_dp import DPLabel, compose_schedules_heuristic, label_dominates
from branchpricecut.solver import solve_vehicle_schedule_bpc
from branchpricecut.tree import SearchNode, VehicleScheduleBPCTree
from bpc.branching import BranchConstraint as RouteBranchConstraint
from bpc.columns import evaluate_route as evaluate_hybrid_route
from bpc.data import load_bpc_data
from bpc.logger import BPCLogger as HybridBPCLogger
from bpc.node import BPCNode
from bpc.pricing import exact_pricing as hybrid_exact_pricing
from bpc.rmp import RMPDuals as HybridRMPDuals
from bpc.schedule_capacity import exact_schedule_task_capacity
from bpc.tree import CleanBPCTree
from bpc.validation import check_route_set_schedule_feasible


def _has_pyscipopt() -> bool:
    try:
        import pyscipopt  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


def _config(**overrides):
    config = {
        "max_routes_in_pricing_pool": 2000,
        "max_new_routes_per_pricing_round": 1000,
        "low_cbar_route_quota": 500,
        "per_task_route_quota": 20,
        "route_size_bucket_quota": 100,
        "time_flexible_route_quota": 200,
        "micro_route_quota": 200,
        "branch_relevant_route_quota": 300,
        "historical_route_quota": 300,
        "diverse_route_quota": 300,
        "schedule_dp_max_labels": 200000,
        "schedule_dp_beam_width": 5000,
        "schedule_dp_max_labels_per_bucket": 5,
        "schedule_dp_time_bucket_size": 10,
        "schedule_dp_enable_subset_dominance": True,
        "schedule_dp_enable_beam_pruning": True,
        "schedule_dp_early_stop_on_full_batch": True,
        "schedule_dp_max_seconds": 10,
        "max_negative_schedules_per_pricing": 50,
        "max_labels_per_exact_pricing": 0,
        "manual_rc_tolerance": 1.0e-6,
        "historical_route_quota": 300,
    }
    config.update(overrides)
    return config


def _tree(data, **overrides) -> VehicleScheduleBPCTree:
    config = _config(**overrides.pop("config_overrides", {}))
    return VehicleScheduleBPCTree(
        data,
        time_limit=float(overrides.pop("time_limit", 30)),
        max_nodes=int(overrides.pop("max_nodes", 100)),
        eps=1.0e-6,
        integer_tol=1.0e-6,
        max_columns_per_pricing=int(overrides.pop("max_columns_per_pricing", 100)),
        max_labels_per_pricing=0,
        max_generated_labels_per_pricing=0,
        max_queue_size_per_pricing=0,
        max_candidate_pool_per_pricing=0,
        max_pricing_seconds=float(overrides.pop("max_pricing_seconds", 10)),
        master_cover_mode=str(overrides.pop("master_cover_mode", "partitioning")),
        vehicle_lower_bound_cut_enabled=bool(overrides.pop("vehicle_lower_bound_cut_enabled", False)),
        schedule_column_pool_enabled=True,
        max_schedule_pool_size=100000,
        route_pool_pricing_enabled=bool(overrides.pop("route_pool_pricing_enabled", True)),
        exact_pricing_fallback_enabled=True,
        exact_pricing_required_for_certificate=True,
        config=config,
        rmp_params={},
        logger=BPCLogger(None, console=False),
    )


def _enumerate_columns(data):
    duals = RMPDuals({task: 1.0e6 for task in data.tasks}, fleet=0.0, vehicle_lb=0.0)
    result = exact_schedule_pricing(
        data,
        [],
        duals,
        tuple(),
        phase="phase2",
        eps=1.0e-6,
        max_columns_to_return=10000,
        max_labels=0,
        max_generated_labels=0,
        max_queue_size=0,
        max_candidate_pool=0,
        max_seconds=0.0,
        enable_dominance=False,
    )
    if not result.exhausted:
        raise AssertionError("tiny enumeration exact pricing did not exhaust")
    return result.columns


class BranchPriceCutVehicleScheduleTests(unittest.TestCase):
    def setUp(self):
        self.data = load_instance("very_small")

    @unittest.skipUnless(_has_pyscipopt(), "当前 Python 环境没有 PySCIPOpt")
    def test_01_reduced_cost_consistency_existing_columns(self):
        tree = _tree(self.data, vehicle_lower_bound_cut_enabled=True)
        tree.initialize()
        columns = tree._current_columns()
        for phase in ("phase1", "phase2"):
            for mode in ("partitioning", "covering"):
                with self.subTest(phase=phase, mode=mode):
                    solution = solve_rmp_lp(
                        self.data,
                        columns,
                        tuple(),
                        phase=phase,
                        master_cover_mode=mode,
                        vehicle_lower_bound_cut_enabled=True,
                        rmp_params={},
                    )
                    self.assertTrue(solution.optimal)
                    self.assertLessEqual(check_schedule_reduced_cost_consistency(solution), 1.0e-6)

    @unittest.skipUnless(_has_pyscipopt(), "当前 Python 环境没有 PySCIPOpt")
    def test_02_phase_i_to_phase_ii_dual_transition(self):
        tree = _tree(self.data, route_pool_pricing_enabled=False, vehicle_lower_bound_cut_enabled=True)
        tree.initialize()
        solution, certified = tree._solve_node_lp(SearchNode(0.0, 0, 0))
        self.assertTrue(certified)
        self.assertIsNotNone(solution)
        self.assertEqual(tree.stats.phase_switch_count, 1)
        self.assertGreaterEqual(tree.stats.rmp_solves, 2)
        self.assertGreater(float(solution.objective or 0.0), 0.0)

    @unittest.skipUnless(_has_pyscipopt(), "当前 Python 环境没有 PySCIPOpt")
    def test_03_vehicle_lower_bound_dual_sign_matches_solver_reduced_cost(self):
        tree = _tree(self.data, vehicle_lower_bound_cut_enabled=True)
        tree.initialize()
        solution = solve_rmp_lp(
            self.data,
            tree._current_columns(),
            tuple(),
            phase="phase2",
            master_cover_mode="partitioning",
            vehicle_lower_bound_cut_enabled=True,
            rmp_params={},
        )
        self.assertTrue(solution.optimal)
        self.assertGreaterEqual(solution.vehicle_lower_bound_value, 1)
        self.assertLessEqual(check_schedule_reduced_cost_consistency(solution), 1.0e-6)
        for index, manual_rc in solution.manual_reduced_costs.items():
            self.assertAlmostEqual(manual_rc, solution.reduced_costs[index], places=6)

    def test_04_layer1_separate_filtering_rejects_joint_route(self):
        constraints = (BranchConstraint("separate", 1, 2),)
        bad_route = SortieRoute((1, 2), frozenset({1, 2}), 0.0, 0.0, 0.0, 0.0, {})
        self.assertFalse(route_allowed_by_branch(bad_route, constraints))

        duals = RMPDuals({task: 10.0 for task in self.data.tasks}, fleet=0.0, vehicle_lb=0.0)
        result = build_portfolio_routes(self.data, duals, constraints, [], _config(), phase="phase2")
        self.assertTrue(all(not ({1, 2}.issubset(route.task_set)) for route in result.routes))

    def test_05_layer1_portfolio_includes_required_route_buckets(self):
        constraints = (BranchConstraint("same", 1, 2), BranchConstraint("separate", 1, 3))
        duals = RMPDuals({task: 10.0 for task in self.data.tasks}, fleet=0.0, vehicle_lb=0.0)
        historical = [sortie_from_zero(self.data, (int(self.data.tasks[0]),))]
        result = build_portfolio_routes(
            self.data,
            duals,
            constraints,
            [route for route in historical if route is not None],
            _config(),
            phase="phase2",
        )
        self.assertGreater(result.stats.route_pool_size, 0)
        self.assertGreater(result.stats.low_cbar_routes_kept, 0)
        self.assertGreater(result.stats.per_task_routes_kept, 0)
        self.assertGreater(result.stats.route_size_bucket_routes_kept, 0)
        self.assertGreater(result.stats.time_flexible_routes_kept, 0)
        self.assertGreater(result.stats.micro_routes_kept, 0)
        self.assertGreater(result.stats.branch_relevant_routes_kept, 0)
        self.assertGreater(result.stats.historical_routes_kept, 0)
        self.assertTrue(any(route.same_component_hits for route in result.routes if route.task_set & {1, 2}))

    def test_06_layer2_subset_dominance_uses_branch_state(self):
        state = ((0, (1, 2), (1,)),)
        left = DPLabel(0.0, frozenset({1}), 1, 10.0, -5.0, tuple(), state)
        right = DPLabel(0.0, frozenset({1, 2}), 2, 20.0, -4.0, tuple(), state)
        empty = DPLabel(0.0, frozenset(), 0, 0.0, -10.0, tuple(), tuple())
        self.assertTrue(label_dominates(left, right))
        self.assertFalse(label_dominates(empty, right))

    def test_07_layer2_beam_pruning_failure_triggers_layer3(self):
        routes = [sortie_from_zero(self.data, (task,)) for task in self.data.tasks]
        routes = [route for route in routes if route is not None]
        early_duals = RMPDuals({task: 1000.0 for task in self.data.tasks}, fleet=0.0, vehicle_lb=0.0)
        early = compose_schedules_heuristic(
            self.data,
            routes,
            early_duals,
            tuple(),
            _config(
                schedule_dp_enable_subset_dominance=False,
                schedule_dp_enable_beam_pruning=False,
                max_negative_schedules_per_pricing=2,
            ),
            phase="phase2",
            eps=1.0e-6,
        )
        self.assertEqual(len(early.columns), 2)
        self.assertTrue(early.stats.early_stopped)
        self.assertFalse(early.stats.exhausted)

        duals = RMPDuals({task: 20.0 for task in self.data.tasks}, fleet=0.0, vehicle_lb=0.0)
        result = compose_schedules_heuristic(
            self.data,
            routes,
            duals,
            tuple(),
            _config(
                schedule_dp_enable_subset_dominance=False,
                schedule_dp_enable_beam_pruning=True,
                schedule_dp_beam_width=1,
                schedule_dp_max_labels_per_bucket=1,
                schedule_dp_max_labels=100,
            ),
            phase="phase2",
            eps=1.0e-6,
        )
        self.assertFalse(result.stats.exhausted)
        self.assertGreater(result.stats.labels_pruned_by_beam, 0)

        tree = _tree(
            self.data,
            vehicle_lower_bound_cut_enabled=False,
            config_overrides={
                "schedule_dp_enable_subset_dominance": False,
                "schedule_dp_enable_beam_pruning": True,
                "schedule_dp_beam_width": 1,
                "schedule_dp_max_labels_per_bucket": 1,
                "max_negative_schedules_per_pricing": 0,
            },
        )
        tree.initialize()
        solution, certified = tree._solve_node_lp(SearchNode(0.0, 0, 0))
        self.assertTrue(certified)
        self.assertIsNotNone(solution)
        self.assertGreater(tree.stats.exact_pricing_calls, 0)

    @unittest.skipUnless(_has_pyscipopt(), "当前 Python 环境没有 PySCIPOpt")
    def test_08_partitioning_default_and_covering_postprocess(self):
        tree = _tree(self.data, master_cover_mode="partitioning")
        self.assertEqual(tree.master_cover_mode, "partitioning")
        tree.initialize()
        partitioning = solve_rmp_lp(
            self.data,
            tree._current_columns(),
            tuple(),
            phase="phase2",
            master_cover_mode="partitioning",
            vehicle_lower_bound_cut_enabled=False,
            rmp_params={},
        )
        covering = solve_rmp_lp(
            self.data,
            tree._current_columns(),
            tuple(),
            phase="phase2",
            master_cover_mode="covering",
            vehicle_lower_bound_cut_enabled=False,
            rmp_params={},
        )
        self.assertTrue(partitioning.optimal)
        self.assertTrue(covering.optimal)
        integer = solve_restricted_master_integer(
            self.data,
            tree._current_columns(),
            tuple(),
            master_cover_mode="partitioning",
            vehicle_lower_bound_cut_enabled=False,
            time_limit=5.0,
            rmp_params={},
        )
        self.assertTrue(integer.feasible)
        self.assertLessEqual(len(integer.selected_columns), self.data.vehicle_count)

        covering_tree = _tree(self.data, master_cover_mode="covering")
        covering_tree.initialize()
        greedy = covering_tree._greedy_schedule_columns()
        self.assertIsNotNone(greedy)
        duplicate = covering_tree._single_task_schedule(int(self.data.tasks[0]))
        self.assertIsNotNone(duplicate)
        incumbent = covering_tree._postprocess_covering_incumbent([*greedy, duplicate], SearchNode(0.0, 0, 0))
        self.assertIsNotNone(incumbent)
        assert incumbent is not None
        counts = {task: 0 for task in self.data.tasks}
        for column in incumbent.columns:
            for task in column.task_set:
                counts[task] += 1
        self.assertTrue(all(value == 1 for value in counts.values()))

    @unittest.skipUnless(_has_pyscipopt(), "当前 Python 环境没有 PySCIPOpt")
    def test_09_tiny_full_enumeration_master_matches_cg_lp(self):
        columns = _enumerate_columns(self.data)
        self.assertGreater(len(columns), 0)
        full_master = solve_rmp_lp(
            self.data,
            columns,
            tuple(),
            phase="phase2",
            master_cover_mode="partitioning",
            vehicle_lower_bound_cut_enabled=False,
            rmp_params={},
        )
        self.assertTrue(full_master.optimal)

        duals = RMPDuals({task: 1.0e6 for task in self.data.tasks}, fleet=0.0, vehicle_lb=0.0)
        dominance_result = exact_schedule_pricing(
            self.data,
            [],
            duals,
            tuple(),
            phase="phase2",
            eps=1.0e-6,
            max_columns_to_return=10000,
            max_labels=0,
            max_generated_labels=0,
            max_queue_size=0,
            max_candidate_pool=0,
            max_seconds=0.0,
            enable_dominance=True,
        )
        self.assertTrue(dominance_result.exhausted)
        self.assertGreater(dominance_result.labels_pruned_by_dominance, 0)
        dominance_master = solve_rmp_lp(
            self.data,
            dominance_result.columns,
            tuple(),
            phase="phase2",
            master_cover_mode="partitioning",
            vehicle_lower_bound_cut_enabled=False,
            rmp_params={},
        )
        self.assertTrue(dominance_master.optimal)
        self.assertAlmostEqual(float(full_master.objective or 0.0), float(dominance_master.objective or 0.0), places=5)

        dssr = DSSRSchedulePricing(
            self.data,
            [],
            eps=1.0e-6,
            max_columns_to_return=10000,
            max_labels=0,
            max_generated_labels=0,
            max_queue_size=0,
            max_candidate_pool=0,
            max_seconds=0.0,
            relaxed_memory_enabled=True,
            relaxed_initial_memory_size=0,
            relaxed_max_iterations=2,
            relaxed_memory_growth=2,
            relaxed_iteration_seconds=0.0,
            relaxed_max_labels=0,
        )
        dssr_result = dssr.run(duals, tuple(), phase="phase2")
        self.assertTrue(dssr_result.exhausted)
        self.assertIn(dssr_result.algorithm, {"ng_dssr", "dssr_relaxed_memory", "dssr_full_memory_exact"})
        self.assertGreaterEqual(dssr_result.dssr_iterations, 1)

        tree = _tree(self.data, route_pool_pricing_enabled=False, vehicle_lower_bound_cut_enabled=False)
        tree.initialize()
        cg_solution, certified = tree._solve_node_lp(SearchNode(0.0, 0, 0))
        self.assertTrue(certified)
        self.assertIsNotNone(cg_solution)
        assert cg_solution is not None
        self.assertAlmostEqual(float(full_master.objective or 0.0), float(cg_solution.objective or 0.0), places=5)

    @unittest.skipUnless(_has_pyscipopt(), "当前 Python 环境没有 PySCIPOpt")
    def test_10_branching_coverage_classifies_child_columns(self):
        columns = _enumerate_columns(self.data)
        same = (BranchConstraint("same", 1, 2),)
        separate = (BranchConstraint("separate", 1, 2),)
        for column in columns:
            in_same = schedule_allowed_by_branch(column, same)
            in_separate = schedule_allowed_by_branch(column, separate)
            self.assertTrue(in_same or in_separate)
            if {1, 2}.issubset(column.task_set):
                self.assertTrue(in_same)
                self.assertFalse(in_separate)
            elif column.task_set & {1, 2}:
                self.assertFalse(in_same)
                self.assertTrue(in_separate)
            else:
                self.assertTrue(in_same)
                self.assertTrue(in_separate)

    @unittest.skipUnless(_has_pyscipopt(), "当前 Python 环境没有 PySCIPOpt")
    def test_11_ng_dssr_tree_matches_full_master_on_tiny_instance(self):
        columns = _enumerate_columns(self.data)
        full_master = solve_rmp_lp(
            self.data,
            columns,
            tuple(),
            phase="phase2",
            master_cover_mode="partitioning",
            vehicle_lower_bound_cut_enabled=False,
            rmp_params={},
        )
        self.assertTrue(full_master.optimal)
        tree = _tree(
            self.data,
            route_pool_pricing_enabled=False,
            vehicle_lower_bound_cut_enabled=False,
            config_overrides={
                "exact_pricing_algorithm": "ng_dssr",
                "full_memory_fallback_enabled": False,
                "ng_neighborhood_size": 2,
                "dssr_certificate_without_full_memory": True,
            },
        )
        tree.initialize()
        solution, certified = tree._solve_node_lp(SearchNode(0.0, 0, 0))
        self.assertTrue(certified)
        self.assertIsNotNone(solution)
        assert solution is not None
        self.assertEqual(tree.stats.full_memory_fallback_called, 0)
        self.assertGreater(tree.stats.dssr_certificate_from_relaxation, 0)
        self.assertAlmostEqual(float(full_master.objective or 0.0), float(solution.objective or 0.0), places=5)

    def test_12_ng_dssr_memory_growth_on_negative_non_elementary_schedule(self):
        existing = _enumerate_columns(self.data)
        duals = RMPDuals({task: 1000.0 for task in self.data.tasks}, fleet=0.0, vehicle_lb=0.0)
        result = ng_dssr_schedule_pricing(
            self.data,
            existing,
            duals,
            tuple(),
            phase="phase2",
            eps=1.0e-6,
            max_columns_to_return=20,
            max_labels=0,
            max_generated_labels=0,
            max_queue_size=0,
            max_candidate_pool=0,
            max_seconds=0.0,
            enable_dominance=True,
            ng_size=1,
            initial_memory_size=0,
            max_iterations=3,
            memory_growth=2,
            certificate_without_full_memory=True,
        )
        self.assertGreaterEqual(result.dssr_iterations, 2)
        self.assertGreater(result.dssr_non_elementary_negative, 0)
        self.assertEqual(result.algorithm, "ng_dssr")

    def test_13_ng_dssr_returns_elementary_negative_schedule(self):
        duals = RMPDuals({task: 1000.0 for task in self.data.tasks}, fleet=0.0, vehicle_lb=0.0)
        result = ng_dssr_schedule_pricing(
            self.data,
            [],
            duals,
            tuple(),
            phase="phase2",
            eps=1.0e-6,
            max_columns_to_return=5,
            max_labels=0,
            max_generated_labels=0,
            max_queue_size=0,
            max_candidate_pool=0,
            max_seconds=0.0,
            enable_dominance=True,
            ng_size=2,
            initial_memory_size=0,
            max_iterations=2,
            memory_growth=2,
        )
        self.assertGreater(len(result.columns), 0)
        self.assertFalse(result.certificate)
        for column in result.columns:
            self.assertLess(manual_reduced_cost(column, duals, "phase2"), 0.0)

    def test_14_ng_dssr_relaxed_certificate_without_full_memory(self):
        duals = RMPDuals({task: 0.0 for task in self.data.tasks}, fleet=0.0, vehicle_lb=0.0)
        dssr = DSSRSchedulePricing(
            self.data,
            [],
            eps=1.0e-6,
            max_columns_to_return=20,
            max_labels=0,
            max_generated_labels=0,
            max_queue_size=0,
            max_candidate_pool=0,
            max_seconds=0.0,
            relaxed_memory_enabled=True,
            exact_pricing_algorithm="ng_dssr",
            full_memory_fallback_enabled=False,
            ng_neighborhood_size=2,
            dssr_certificate_without_full_memory=True,
        )
        result = dssr.run(duals, tuple(), phase="phase2")
        self.assertTrue(result.exhausted)
        self.assertTrue(result.certificate)
        self.assertTrue(result.certificate_from_relaxation)
        self.assertFalse(result.full_memory_fallback_called)

    def test_15_ng_dssr_limits_do_not_certificate(self):
        duals = RMPDuals({task: 1000.0 for task in self.data.tasks}, fleet=0.0, vehicle_lb=0.0)
        result = ng_dssr_schedule_pricing(
            self.data,
            [],
            duals,
            tuple(),
            phase="phase2",
            eps=1.0e-6,
            max_columns_to_return=20,
            max_labels=1,
            max_generated_labels=0,
            max_queue_size=0,
            max_candidate_pool=0,
            max_seconds=0.0,
            enable_dominance=True,
            ng_size=2,
            initial_memory_size=0,
            max_iterations=2,
            memory_growth=2,
        )
        self.assertFalse(result.exhausted)
        self.assertFalse(result.certificate)
        self.assertEqual(result.stop_reason, "label_pop_limit")

    def test_16_ng_dssr_dominance_key_keeps_sortie_and_branch_state(self):
        base = dict(
            priority=0.0,
            ready_time=0.0,
            dssr_seen=frozenset(),
            ng_memory=frozenset({1}),
            visits=(1,),
            completed=tuple(),
            current_node=1,
            current_time=1.0,
            current_load=1.0,
            current_energy=1.0,
            current_cost=1.0,
            total_cost=1.0,
            current_service_start={},
        )
        left = NGLabel(current_tasks=(1,), **base)
        right = NGLabel(current_tasks=(2,), **{**base, "visits": (2,), "current_node": 2})
        self.assertNotEqual(label_key(left, tuple()), label_key(right, tuple()))
        constraints = (BranchConstraint("same", 1, 2),)
        partial = NGLabel(current_tasks=(1,), **base)
        full = NGLabel(current_tasks=(1, 2), **{**base, "visits": (1, 2)})
        self.assertNotEqual(label_key(partial, constraints), label_key(full, constraints))

    def test_17_ng_dssr_respects_same_and_separate_branching(self):
        duals = RMPDuals({task: 1000.0 for task in self.data.tasks}, fleet=0.0, vehicle_lb=0.0)
        for constraints in ((BranchConstraint("separate", 1, 2),), (BranchConstraint("same", 1, 2),)):
            with self.subTest(constraints=constraints):
                result = ng_dssr_schedule_pricing(
                    self.data,
                    [],
                    duals,
                    constraints,
                    phase="phase2",
                    eps=1.0e-6,
                    max_columns_to_return=20,
                    max_labels=0,
                    max_generated_labels=0,
                    max_queue_size=0,
                    max_candidate_pool=0,
                    max_seconds=0.0,
                    enable_dominance=True,
                    ng_size=2,
                    initial_memory_size=0,
                    max_iterations=2,
                    memory_growth=2,
                )
                self.assertTrue(all(schedule_allowed_by_branch(column, constraints) for column in result.columns))

        zero_duals = RMPDuals({task: 0.0 for task in self.data.tasks}, fleet=0.0, vehicle_lb=0.0)
        certificate = ng_dssr_schedule_pricing(
            self.data,
            [],
            zero_duals,
            (BranchConstraint("same", 1, 2), BranchConstraint("separate", 3, 4)),
            phase="phase2",
            eps=1.0e-6,
            max_columns_to_return=20,
            max_labels=0,
            max_generated_labels=0,
            max_queue_size=0,
            max_candidate_pool=0,
            max_seconds=0.0,
            enable_dominance=True,
            ng_size=2,
            initial_memory_size=0,
            max_iterations=2,
            memory_growth=2,
        )
        self.assertTrue(certificate.certificate)

    @unittest.skipUnless(_has_pyscipopt(), "当前 Python 环境没有 PySCIPOpt")
    def test_18_hybrid_route_master_dispatch_solves_very_small(self):
        config = {
            "master_type": "hybrid_route",
            "time_limit": 20,
            "max_nodes": 200,
            "pricing_eps": 1.0e-6,
            "integer_tol": 1.0e-6,
            "max_routes_per_pricing": 200,
            "hybrid_max_labels_per_pricing": 0,
            "random_seed": 20260511,
            "rmp_params": {"display/verblevel": 0, "presolving/maxrounds": 0, "separating/maxrounds": 0},
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = solve_vehicle_schedule_bpc(
                self.data,
                config=config,
                log_path=root / "hybrid.jsonl",
                solution_path=root / "solution.json",
                quiet=True,
            )
            solution = json.loads((root / "solution.json").read_text(encoding="utf-8"))

        self.assertEqual(result.master_type, "hybrid_route")
        self.assertEqual(result.master_cover_mode, "route_vehicle")
        self.assertEqual(result.status, "OPTIMAL")
        self.assertAlmostEqual(result.primal_bound or 0.0, 132.270984, places=5)
        self.assertGreater(result.generated_routes, 0)
        self.assertIn("schedule_checks", solution["solution"])
        self.assertTrue(all(check["feasible"] for check in solution["solution"]["schedule_checks"].values()))

    def test_19_hybrid_route_pricing_exhaustion_and_limits_are_explicit(self):
        data = load_bpc_data("very_small")
        duals = HybridRMPDuals(
            cover={task: 0.0 for task in data.tasks},
            task_vehicle={},
            sortie_count={vehicle: 0.0 for vehicle in data.vehicles},
            vehicle_time={vehicle: 0.0 for vehicle in data.vehicles},
            cuts={},
            branches={},
        )
        exhaustive = hybrid_exact_pricing(
            data,
            [],
            duals,
            cuts=[],
            branch_constraints=tuple(),
            phase="phase2",
            eps=1.0e-6,
            max_routes_to_return=20,
            max_labels=0,
        )
        self.assertTrue(exhaustive.exhausted)
        self.assertEqual(exhaustive.routes, [])
        self.assertIsNotNone(exhaustive.best_reduced_cost)
        self.assertGreaterEqual(exhaustive.best_reduced_cost or 0.0, -1.0e-6)

        attractive = HybridRMPDuals(
            cover={task: 1000.0 for task in data.tasks},
            task_vehicle={},
            sortie_count={vehicle: 0.0 for vehicle in data.vehicles},
            vehicle_time={vehicle: 0.0 for vehicle in data.vehicles},
            cuts={},
            branches={},
        )
        limited = hybrid_exact_pricing(
            data,
            [],
            attractive,
            cuts=[],
            branch_constraints=tuple(),
            phase="phase2",
            eps=1.0e-6,
            max_routes_to_return=20,
            max_labels=1,
        )
        self.assertFalse(limited.exhausted)

    def test_20_hybrid_no_good_cut_rejects_infeasible_route_set(self):
        data = load_bpc_data("medium")
        first = evaluate_hybrid_route(data, (1,))
        second = evaluate_hybrid_route(data, (11, 2))
        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        assert first is not None and second is not None
        self.assertFalse(check_route_set_schedule_feasible(data, [first, second]).feasible)

        logger = HybridBPCLogger(None, console=False)
        tree = CleanBPCTree(
            data,
            time_limit=30,
            max_nodes=10,
            eps=1.0e-6,
            integer_tol=1.0e-6,
            max_routes_per_pricing=20,
            max_labels_per_pricing=0,
            rmp_params={},
            logger=logger,
        )
        added = tree._add_schedule_conflict_cuts(
            BPCNode(0.0, 0, 0),
            source_vehicle=int(data.vehicles[0]),
            routes=[first, second],
            kind="schedule_nogood_core",
        )
        self.assertEqual(added, len(data.vehicles))
        for cut in tree.cuts:
            coeff = sum(cut.coefficient(route, int(cut.vehicle)) for route in (first, second))
            self.assertGreater(coeff, cut.rhs)

    def test_21_hybrid_schedule_capacity_oracle_bounds_cut_strength(self):
        data = load_bpc_data("very_small")
        result = exact_schedule_task_capacity(data, tuple(data.tasks[:3]), max_states=100000)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertTrue(result.exact)
        self.assertGreaterEqual(result.upper_bound, 1)
        self.assertLessEqual(result.upper_bound, 3)

    def test_22_hybrid_branching_filters_route_space(self):
        data = load_bpc_data("very_small")
        route = evaluate_hybrid_route(data, tuple(data.tasks[:2]))
        if route is None:
            route = evaluate_hybrid_route(data, tuple(reversed(data.tasks[:2])))
        self.assertIsNotNone(route)
        assert route is not None
        vehicle = data.vehicles[0]
        rf_left = RouteBranchConstraint("ryan_separate", route.tasks[0], route.tasks[1])
        rf_right = RouteBranchConstraint("ryan_together", route.tasks[0], route.tasks[1])
        from bpc.branching import route_allowed_by_branch as hybrid_route_allowed_by_branch

        self.assertFalse(hybrid_route_allowed_by_branch(route, vehicle, (rf_left,)))
        self.assertTrue(hybrid_route_allowed_by_branch(route, vehicle, (rf_right,)))
        self.assertFalse(hybrid_route_allowed_by_branch(route, vehicle, (RouteBranchConstraint("vehicle_use_off", 0, vehicle=vehicle),)))
        self.assertTrue(hybrid_route_allowed_by_branch(route, vehicle, (RouteBranchConstraint("vehicle_use_on", 0, vehicle=vehicle),)))


if __name__ == "__main__":
    unittest.main()

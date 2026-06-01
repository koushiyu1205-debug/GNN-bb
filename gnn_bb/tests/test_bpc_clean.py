"""中文摘要：本测试文件覆盖根目录 bpc/ clean BPC 的基础闭环。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from itertools import permutations
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
_gnn_bb_pkg = sys.modules.get("gnn_bb")
if _gnn_bb_pkg is not None and hasattr(_gnn_bb_pkg, "__path__"):
    _src_pkg = str(SRC / "gnn_bb")
    if _src_pkg not in list(_gnn_bb_pkg.__path__):
        _gnn_bb_pkg.__path__.append(_src_pkg)

from bpc.columns import RoutePool, evaluate_route
from bpc.branching import BranchCandidate, BranchConstraint, route_allowed_by_branch, route_branch_coefficient
from bpc.cuts import (
    CrossingCut,
    LimitedMemoryRank1Cut,
    ScheduleCapacityCut,
    ScheduleNoGoodCut,
    ScheduleSubsetCostLowerBoundCut,
    SubsetRowCut,
    WeightedScheduleRouteSetPackingCut,
    capacity_route_lower_bound,
)
from bpc.data import BPCData, load_bpc_data
from bpc.logger import BPCLogger
from bpc.node import BPCNode
from bpc.perf_stats import analyze_jsonl
from bpc.persistent_rmp import PersistentRMP
from bpc.pricing import PricingResult, exact_pricing, reduced_cost
from bpc.rmp import RMPDuals, RMPSolution, RestrictedIntegerResult, solve_restricted_integer_master, solve_rmp_lp
from bpc.schedule_capacity import exact_schedule_task_capacity, find_schedule_capacity_conflict
from bpc.schedule_cost import exact_schedule_subset_cost
from bpc.schedule_pack import solve_schedule_pack_node_relaxation, solve_schedule_pack_restricted_lp
from bpc.solver import solve_bpc_clean
from bpc.task_schedule_capacity import generate_task_schedule_capacity_candidates, witness_from_routes
from bpc.tree import CleanBPCTree, Incumbent
from bpc.validation import diagnose_route_set_schedule, exact_route_set_schedule_capacity, exact_weighted_route_set_schedule_capacity


class CleanBPCTests(unittest.TestCase):
    def _require_pyscipopt(self):
        try:
            import pyscipopt  # noqa: F401
        except Exception:
            self.skipTest("当前 Python 环境没有 PySCIPOpt")

    def test_single_task_route_evaluates(self):
        data = load_bpc_data("very_small")
        route = evaluate_route(data, (1,))
        self.assertIsNotNone(route)
        self.assertEqual(route.tasks, (1,))
        self.assertGreater(route.cost, 0.0)

    def test_arc_branching_filters_and_coefficients(self):
        data = load_bpc_data("very_small")
        route = None
        for left in data.tasks:
            for right in data.tasks:
                if left == right:
                    continue
                route = evaluate_route(data, (left, right))
                if route is not None:
                    break
            if route is not None:
                break
        self.assertIsNotNone(route)
        assert route is not None
        tail, head = route.tasks[0], route.tasks[1]
        off = BranchConstraint("arc_off", tail, head)
        on = BranchConstraint("arc_on", tail, head)
        self.assertFalse(route_allowed_by_branch(route, data.vehicles[0], (off,)))
        self.assertEqual(route_branch_coefficient(route, data.vehicles[0], on), 1.0)

    def test_crossing_cut_capacity_coefficient(self):
        data = load_bpc_data("very_small")
        route = None
        for left in data.tasks:
            for right in data.tasks:
                if left == right:
                    continue
                route = evaluate_route(data, (left, right))
                if route is not None:
                    break
            if route is not None:
                break
        self.assertIsNotNone(route)
        assert route is not None
        capacity_bound = capacity_route_lower_bound(data, tuple(sorted(route.tasks)))
        cut = CrossingCut(
            id=0,
            tasks=tuple(sorted(route.tasks)),
            rhs=float(2 * capacity_bound),
            k_bound=capacity_bound,
            capacity_bound=capacity_bound,
            resource_bound=1,
            demand=sum(data.task_value(task, "d") for task in route.tasks),
            capacity=data.capacity,
        )
        self.assertEqual(cut.sense, ">=")
        self.assertEqual(cut.key, ("crossing_cut", frozenset(route.tasks)))
        self.assertEqual(cut.coefficient(route, data.vehicles[0]), 2.0)

    def test_crossing_cut_resource_coefficient(self):
        data = load_bpc_data("very_small")
        route = None
        for left in data.tasks:
            for right in data.tasks:
                if left == right:
                    continue
                route = evaluate_route(data, (left, right))
                if route is not None:
                    break
            if route is not None:
                break
        self.assertIsNotNone(route)
        assert route is not None
        cut = CrossingCut(
            id=0,
            tasks=tuple(sorted(route.tasks)),
            rhs=4.0,
            k_bound=2,
            capacity_bound=1,
            resource_bound=2,
            demand=sum(data.task_value(task, "d") for task in route.tasks),
            capacity=data.capacity,
        )
        self.assertEqual(cut.sense, ">=")
        self.assertEqual(cut.coefficient(route, data.vehicles[0]), 2.0)

    def test_schedule_capacity_cut_coefficients(self):
        data = load_bpc_data("very_small")
        route = evaluate_route(data, tuple(data.tasks[:2]))
        if route is None:
            route = evaluate_route(data, tuple(reversed(data.tasks[:2])))
        self.assertIsNotNone(route)
        assert route is not None
        vehicle = data.vehicles[0]
        cut = ScheduleCapacityCut(
            id=0,
            vehicle=vehicle,
            tasks=tuple(sorted(route.tasks)),
            upper_bound=1,
            oracle_states=10,
        )
        self.assertEqual(cut.sense, "<=")
        self.assertEqual(cut.rhs, 0.0)
        self.assertEqual(cut.coefficient(route, vehicle), 2.0)
        self.assertEqual(cut.y_coefficient(vehicle), -1.0)
        self.assertEqual(cut.coefficient(route, data.vehicles[-1] + 1), 0.0)

    def test_subset_row_and_schedule_cost_cut_coefficients(self):
        data = load_bpc_data("very_small")
        route = evaluate_route(data, tuple(data.tasks[:2]))
        if route is None:
            route = evaluate_route(data, tuple(reversed(data.tasks[:2])))
        self.assertIsNotNone(route)
        assert route is not None

        subset_row = SubsetRowCut(id=0, tasks=tuple(sorted(route.tasks)), divisor=2)
        self.assertEqual(subset_row.sense, "<=")
        self.assertEqual(subset_row.rhs, 1.0)
        self.assertEqual(subset_row.coefficient(route, data.vehicles[0]), 1.0)

        lm_rank1 = LimitedMemoryRank1Cut(
            id=2,
            tasks=tuple(sorted(route.tasks)),
            multipliers=(2, 1),
            denominator=3,
            memory_tasks=(route.tasks[0],),
        )
        self.assertEqual(lm_rank1.sense, "<=")
        self.assertEqual(lm_rank1.rhs, 1.0)
        self.assertEqual(lm_rank1.coefficient(route, data.vehicles[0]), 1.0)

        schedule_cost = ScheduleSubsetCostLowerBoundCut(
            id=1,
            vehicle=data.vehicles[0],
            tasks=tuple(sorted(route.tasks)),
            lower_bound=10.0,
            oracle_states=5,
        )
        self.assertEqual(schedule_cost.sense, ">=")
        self.assertEqual(schedule_cost.rhs, 0.0)
        self.assertAlmostEqual(schedule_cost.coefficient(route, data.vehicles[0]), route.cost - 20.0)
        self.assertAlmostEqual(schedule_cost.y_coefficient(data.vehicles[0]), 10.0)
        self.assertEqual(schedule_cost.coefficient(route, data.vehicles[-1] + 1), 0.0)

    def test_greedy_insertion_accounts_for_fixed_vehicle_cost(self):
        instance = {
            "name": "fixed_cost_greedy_smoke",
            "tasks": {
                "1": {"r": 0, "D": 200, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "2": {"r": 0, "D": 200, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
            },
        }
        pairwise = {
            "0->0": {"tau": 0, "energy": 0, "cost": 0, "path": []},
            "1->1": {"tau": 0, "energy": 0, "cost": 0, "path": []},
            "2->2": {"tau": 0, "energy": 0, "cost": 0, "path": []},
            "0->1": {"tau": 5, "energy": 0, "cost": 5, "path": []},
            "1->0": {"tau": 5, "energy": 0, "cost": 5, "path": []},
            "0->2": {"tau": 5, "energy": 0, "cost": 5, "path": []},
            "2->0": {"tau": 5, "energy": 0, "cost": 5, "path": []},
            "1->2": {"tau": 70, "energy": 0, "cost": 70, "path": []},
            "2->1": {"tau": 70, "energy": 0, "cost": 70, "path": []},
        }
        data = BPCData(
            instance=instance,
            pairwise=pairwise,
            instance_path=Path("synthetic"),
            name="fixed_cost_greedy_smoke",
            tasks=(1, 2),
            vehicles=(1, 2),
            sortie_limit=1,
            capacity=2,
            energy_limit=10,
            rho=1,
            fixed_vehicle_cost=100,
            horizon=200,
        )
        tree = CleanBPCTree(
            data,
            time_limit=10,
            max_nodes=10,
            eps=1.0e-6,
            integer_tol=1.0e-6,
            max_routes_per_pricing=10,
            max_labels_per_pricing=0,
            rmp_params={},
            logger=BPCLogger(None, console=False),
        )
        assigned = tree._construct_assignment((1, 2))
        self.assertIsNotNone(assigned)
        assert assigned is not None
        self.assertEqual([vehicle for vehicle, routes in assigned.items() if routes], [1])
        self.assertEqual(assigned[1][0].tasks, (1, 2))
        self.assertAlmostEqual(tree._assignment_objective(assigned), 180.0)

    def test_schedule_clique_conflict_cut_has_rhs_one(self):
        data = load_bpc_data("very_small")
        routes = [evaluate_route(data, (task,)) for task in data.tasks[:3]]
        self.assertTrue(all(route is not None for route in routes))
        routes = [route for route in routes if route is not None]
        cut = ScheduleNoGoodCut(
            id=0,
            vehicle=data.vehicles[0],
            signatures=tuple(route.signature for route in routes),
            kind="schedule_clique_conflict",
            rhs_value=1.0,
        )
        self.assertEqual(cut.sense, "<=")
        self.assertEqual(cut.rhs, 0.0)
        self.assertEqual(cut.upper_bound, 1.0)
        self.assertEqual(cut.y_coefficient(data.vehicles[0]), -1.0)
        self.assertEqual(sum(cut.coefficient(route, data.vehicles[0]) for route in routes), 3.0)
        self.assertEqual(cut.coefficient(routes[0], data.vehicles[-1] + 1), 0.0)

    def test_route_set_schedule_capacity_exact_for_horizon_packing(self):
        instance = {
            "name": "route_set_packing_smoke",
            "tasks": {
                "1": {"r": 0, "D": 10, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "2": {"r": 0, "D": 10, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "3": {"r": 0, "D": 10, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
            },
        }
        pairwise = {}
        for i in (0, 1, 2, 3):
            for j in (0, 1, 2, 3):
                tau = 0 if i == j else (1 if i == 0 or j == 0 else 10)
                pairwise[f"{i}->{j}"] = {"tau": tau, "energy": 0, "cost": tau, "path": []}
        data = BPCData(
            instance=instance,
            pairwise=pairwise,
            instance_path=Path("synthetic"),
            name="route_set_packing_smoke",
            tasks=(1, 2, 3),
            vehicles=(1,),
            sortie_limit=3,
            capacity=10,
            energy_limit=10,
            rho=1,
            fixed_vehicle_cost=100,
            horizon=5,
        )
        routes = [evaluate_route(data, (task,)) for task in data.tasks]
        self.assertTrue(all(route is not None for route in routes))
        routes = [route for route in routes if route is not None]
        result = exact_route_set_schedule_capacity(data, routes, max_states=100000)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertTrue(result.exact)
        self.assertEqual(result.upper_bound, 2)

    def test_weighted_route_set_schedule_capacity_exact_for_horizon_packing(self):
        data, routes, _solution, _tree = self._weighted_route_set_packing_fixture()
        result = exact_weighted_route_set_schedule_capacity(data, routes, (1.0, 0.5, 0.25), max_states=100000)
        self.assertTrue(result.exact)
        self.assertAlmostEqual(result.upper_bound, 1.5)

    def test_weighted_route_set_packing_cut_coefficients(self):
        data, routes, _solution, _tree = self._weighted_route_set_packing_fixture()
        signatures = tuple(route.signature for route in routes)
        cut = WeightedScheduleRouteSetPackingCut(
            id=7,
            vehicle=1,
            signatures=signatures,
            weights=(1.0, 0.5, 0.25),
            upper_bound=1.5,
            oracle_states=12,
        )
        self.assertEqual(cut.sense, "<=")
        self.assertEqual(cut.rhs, 0.0)
        self.assertAlmostEqual(cut.y_coefficient(1), -1.5)
        self.assertAlmostEqual(cut.coefficient(routes[0], 1), 1.0)
        self.assertAlmostEqual(cut.coefficient(routes[1], 1), 0.5)
        self.assertEqual(cut.coefficient(routes[0], data.vehicles[-1] + 1), 0.0)

    def _weighted_route_set_packing_fixture(
        self,
        *,
        route_values: tuple[float, float, float] = (0.6, 0.3, 0.3),
        y_value: float = 0.5,
        max_states: int = 200000,
    ):
        instance = {
            "name": "weighted_route_set_packing_smoke",
            "tasks": {
                "1": {"r": 0, "D": 10, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "2": {"r": 0, "D": 10, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "3": {"r": 0, "D": 10, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
            },
        }
        pairwise = {}
        for i in (0, 1, 2, 3):
            for j in (0, 1, 2, 3):
                tau = 0 if i == j else (1 if i == 0 or j == 0 else 10)
                pairwise[f"{i}->{j}"] = {"tau": tau, "energy": 0, "cost": tau, "path": []}
        data = BPCData(
            instance=instance,
            pairwise=pairwise,
            instance_path=Path("synthetic"),
            name="weighted_route_set_packing_smoke",
            tasks=(1, 2, 3),
            vehicles=(1,),
            sortie_limit=3,
            capacity=10,
            energy_limit=10,
            rho=1,
            fixed_vehicle_cost=100,
            horizon=5,
        )
        routes = [evaluate_route(data, (task,)) for task in data.tasks]
        self.assertTrue(all(route is not None for route in routes))
        routes = [route for route in routes if route is not None]
        solution = RMPSolution(
            status="optimal",
            objective=0.0,
            duals=None,
            artificial_sum=0.0,
            route_values=[(route, 1, value) for route, value in zip(routes, route_values)],
            y_values={1: y_value},
            variable_count=0,
            constraint_count=0,
        )
        tree = CleanBPCTree(
            data,
            time_limit=10,
            max_nodes=10,
            eps=1.0e-6,
            integer_tol=1.0e-6,
            max_routes_per_pricing=10,
            max_labels_per_pricing=0,
            rmp_params={},
            logger=BPCLogger(None, console=False),
            weighted_route_schedule_packing_cuts_enabled=True,
            weighted_route_schedule_packing_max_depth=1,
            weighted_route_schedule_packing_max_rounds_per_node=2,
            weighted_route_schedule_packing_max_candidates=20,
            weighted_route_schedule_packing_max_cuts_per_round=2,
            weighted_route_schedule_packing_max_routes=3,
            weighted_route_schedule_packing_oracle_max_states=max_states,
            weighted_route_schedule_packing_min_violation=0.05,
        )
        for route in routes:
            tree.pool.add(route)
        return data, routes, solution, tree

    def test_weighted_route_set_schedule_packing_separator_adds_cut(self):
        _data, _routes, solution, tree = self._weighted_route_set_packing_fixture()
        added = tree._separate_weighted_route_schedule_packing_cuts(BPCNode(0.0, 0, 0), solution)
        self.assertEqual(added, 1)
        self.assertIsInstance(tree.cuts[0], WeightedScheduleRouteSetPackingCut)
        self.assertEqual(tree.cuts[0].kind, "weighted_schedule_route_set_packing")
        self.assertGreater(tree.stats.weighted_route_schedule_packing_best_violation, 0.0)
        self.assertEqual(tree.stats.weighted_route_schedule_packing_cuts_added, 1)

    def test_weighted_route_set_schedule_packing_incomplete_cached_without_cut(self):
        _data, routes, solution, tree = self._weighted_route_set_packing_fixture(max_states=1)
        added = tree._separate_weighted_route_schedule_packing_cuts(BPCNode(0.0, 0, 0), solution)
        self.assertEqual(added, 0)
        self.assertEqual(tree.cuts, [])
        self.assertGreater(tree.stats.weighted_route_schedule_packing_oracle_incomplete, 0)
        signatures, _ordered = tree._weighted_route_signature_routes(routes)
        weights = tuple(1.0 for _signature in signatures)
        self.assertIn((signatures, weights), tree.weighted_route_schedule_packing_cache)
        self.assertIsNone(tree.weighted_route_schedule_packing_cache[(signatures, weights)])

    def test_weighted_route_set_schedule_packing_exact_not_violated(self):
        _data, _routes, solution, tree = self._weighted_route_set_packing_fixture(
            route_values=(0.55, 0.55, 0.55),
            y_value=1.0,
        )
        added = tree._separate_weighted_route_schedule_packing_cuts(BPCNode(0.0, 0, 0), solution)
        self.assertEqual(added, 0)
        self.assertEqual(tree.cuts, [])
        self.assertGreater(tree.stats.weighted_route_schedule_packing_exact_not_violated, 0)

    def test_weighted_route_set_schedule_packing_duplicate_skips_second_cut(self):
        _data, _routes, solution, tree = self._weighted_route_set_packing_fixture()
        node = BPCNode(0.0, 0, 0)
        self.assertEqual(tree._separate_weighted_route_schedule_packing_cuts(node, solution), 1)
        self.assertEqual(tree._separate_weighted_route_schedule_packing_cuts(node, solution), 0)
        self.assertGreater(tree.stats.weighted_route_schedule_packing_duplicate_skips, 0)

    def test_weighted_route_set_schedule_packing_cache_normalizes_scaled_weights(self):
        _data, routes, _solution, tree = self._weighted_route_set_packing_fixture()
        first = tree._weighted_route_schedule_packing_bound_with_cache_status(routes, (1.0, 0.5, 0.25))
        second = tree._weighted_route_schedule_packing_bound_with_cache_status(routes, (2.0, 1.0, 0.5))
        self.assertFalse(first[2])
        self.assertTrue(second[2])
        self.assertAlmostEqual(first[0], second[0])

    def test_weighted_route_set_schedule_packing_separator_uses_normalized_alpha_scale(self):
        _data, routes, solution, tree = self._weighted_route_set_packing_fixture(
            route_values=(0.6, 0.45, 0.3),
            y_value=0.5,
        )
        signatures, _ordered = tree._weighted_route_signature_routes(routes)
        normalized_weights = tree._normalized_weighted_route_weights(
            signatures,
            {signature: weight for signature, weight in zip(signatures, (3.0, 2.0, 1.0))},
        )
        expected_beta = exact_weighted_route_set_schedule_capacity(
            _data,
            routes,
            normalized_weights,
            max_states=100000,
        ).upper_bound
        with patch.object(tree, "_route_set_schedule_packing_candidates", return_value=[routes]):
            with patch.object(
                tree,
                "_weighted_route_schedule_packing_candidate_patterns",
                return_value=[("conflict_score_discrete", (3.0, 2.0, 1.0))],
            ):
                added = tree._separate_weighted_route_schedule_packing_cuts(BPCNode(0.0, 0, 0), solution)

        self.assertEqual(added, 1)
        self.assertEqual(tree.stats.weighted_route_schedule_packing_violated_candidates, 1)
        cut = tree.cuts[0]
        self.assertIsInstance(cut, WeightedScheduleRouteSetPackingCut)
        self.assertEqual(cut.signatures, signatures)
        self.assertEqual(cut.weights, normalized_weights)
        self.assertAlmostEqual(cut.upper_bound, expected_beta)
        lhs = sum(cut.coefficient(route, 1) * value for route, _vehicle, value in solution.route_values)
        rhs = -cut.y_coefficient(1) * solution.y_values[1]
        self.assertGreater(lhs, rhs + tree.weighted_route_schedule_packing_min_violation)

    def test_weighted_route_set_schedule_packing_does_not_emit_lp_value_by_default(self):
        _data, routes, solution, tree = self._weighted_route_set_packing_fixture()
        signatures = tuple(route.signature for route in routes)
        value_by_signature = {route.signature: value for route, _vehicle, value in solution.route_values}
        patterns = tree._weighted_route_schedule_packing_candidate_patterns(
            routes,
            value_by_signature,
            {signatures[0]: 3, signatures[1]: 1, signatures[2]: 0},
            source="route_pack_witness",
        )
        names = {name for name, _weights in patterns}
        self.assertNotIn("lp_value", names)
        self.assertIn("conflict_core", names)
        self.assertIn("conflict_score_discrete", names)
        for _name, weights in patterns:
            self.assertTrue(set(weights).issubset({1.0, 2.0, 3.0}))

    def test_route_pack_roi_classifies_same_pool_degeneracy(self):
        _data, _routes, solution, tree = self._weighted_route_set_packing_fixture()
        context = {
            "vehicles": (1,),
            "cut_core_signatures": ((1,), (2,)),
            "cut_core_task_union": (1, 2),
            "pre_support_signatures": ((1,), (2,)),
            "pre_pool_signatures": ((1,), (2,), (1, 3)),
            "pre_pool_size": 3,
            "alpha_patterns": ("uniform",),
        }
        payload = tree._route_pack_roi_diagnostics_payload(
            context,
            stage="post_rmp",
            post_rmp_support_signatures=((1, 3),),
            new_pricing_signatures=tuple(),
            before_objective=10.0,
            after_objective=10.0,
            objective_improvement=0.0,
            low_improvement=True,
        )
        self.assertEqual(payload["classification"], "same_pool_degeneracy")
        self.assertEqual(payload["same_pool_replacement_count"], 1)
        self.assertEqual(payload["pricing_replacement_count"], 0)

    def test_route_pack_roi_classifies_pricing_mousehole(self):
        _data, _routes, solution, tree = self._weighted_route_set_packing_fixture()
        context = {
            "vehicles": (1,),
            "cut_core_signatures": ((1,), (2,)),
            "cut_core_task_union": (1, 2),
            "pre_support_signatures": ((1,), (2,)),
            "pre_pool_signatures": ((1,), (2,)),
            "pre_pool_size": 2,
            "alpha_patterns": ("uniform",),
        }
        payload = tree._route_pack_roi_diagnostics_payload(
            context,
            stage="post_pricing",
            post_rmp_support_signatures=((3,),),
            new_pricing_signatures=((1, 3),),
            before_objective=10.0,
            after_objective=10.5,
            objective_improvement=0.5,
            low_improvement=False,
        )
        self.assertEqual(payload["classification"], "pricing_mousehole")
        self.assertEqual(payload["pricing_replacement_count"], 1)

    def test_route_pack_roi_classifies_objective_degeneracy_without_support_change(self):
        _data, _routes, solution, tree = self._weighted_route_set_packing_fixture()
        context = {
            "vehicles": (1,),
            "cut_core_signatures": ((1,), (2,)),
            "cut_core_task_union": (1, 2),
            "pre_support_signatures": ((1,), (2,)),
            "pre_pool_signatures": ((1,), (2,)),
            "pre_pool_size": 2,
            "alpha_patterns": ("uniform",),
        }
        payload = tree._route_pack_roi_diagnostics_payload(
            context,
            stage="post_rmp",
            post_rmp_support_signatures=((1,), (2,)),
            new_pricing_signatures=tuple(),
            before_objective=10.0,
            after_objective=10.0,
            objective_improvement=0.0,
            low_improvement=True,
        )
        self.assertEqual(payload["classification"], "objective_degeneracy_no_support_change")

    def _route_pool_hygiene_fixture(self):
        instance = {
            "name": "route_pool_hygiene_smoke",
            "tasks": {
                "1": {"r": 0, "D": 100, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "2": {"r": 0, "D": 100, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "3": {"r": 0, "D": 100, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
            },
        }
        pairwise = {}
        for i in (0, 1, 2, 3):
            for j in (0, 1, 2, 3):
                tau = 0 if i == j else 1
                pairwise[f"{i}->{j}"] = {"tau": tau, "energy": 0, "cost": tau, "path": []}
        data = BPCData(
            instance=instance,
            pairwise=pairwise,
            instance_path=Path("synthetic"),
            name="route_pool_hygiene_smoke",
            tasks=(1, 2, 3),
            vehicles=(1,),
            sortie_limit=3,
            capacity=10,
            energy_limit=10,
            rho=1,
            fixed_vehicle_cost=100,
            horizon=100,
        )
        routes = [evaluate_route(data, sequence) for sequence in ((1, 2), (2, 1), (1, 3))]
        self.assertTrue(all(route is not None for route in routes))
        routes = [route for route in routes if route is not None]
        tree = CleanBPCTree(
            data,
            time_limit=10,
            max_nodes=10,
            eps=1.0e-6,
            integer_tol=1.0e-6,
            max_routes_per_pricing=10,
            max_labels_per_pricing=0,
            rmp_params={},
            logger=BPCLogger(None, console=False),
            route_pool_hygiene_diagnostics_enabled=True,
            route_pool_hygiene_admission_enabled=True,
            route_pool_hygiene_admission_max_per_task_set=1,
        )
        return data, routes, tree

    def test_route_pool_hygiene_profile_detects_same_task_set_degeneracy(self):
        _data, routes, tree = self._route_pool_hygiene_fixture()
        payload = tree._route_pool_hygiene_profile(routes)
        self.assertEqual(payload["route_count"], 3)
        self.assertEqual(payload["task_set_groups"], 2)
        self.assertEqual(payload["multi_route_groups"], 1)
        self.assertEqual(payload["near_duplicate_groups"], 1)
        self.assertEqual(payload["near_duplicate_routes"], 1)
        self.assertEqual(payload["max_group_size"], 2)

    def test_route_pool_hygiene_admission_filters_only_heuristic_and_forces_exact(self):
        _data, routes, tree = self._route_pool_hygiene_fixture()
        pricing = PricingResult(
            routes=routes,
            exhausted=True,
            best_reduced_cost=-1.0,
            label_pops=10,
            generated_labels=20,
            negative_routes=len(routes),
        )
        filtered, payload = tree._apply_route_pool_hygiene_admission(pricing, pricing_kind="heuristic")
        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload["filtered_routes"], 1)
        self.assertEqual(len(filtered.routes), 2)
        self.assertFalse(filtered.exhausted)
        self.assertEqual(tree.stats.route_pool_hygiene_admission_filtered, 1)
        self.assertEqual(tree.stats.route_pool_hygiene_admission_forced_exact, 1)

        exact_pricing_result, exact_payload = tree._apply_route_pool_hygiene_admission(pricing, pricing_kind="exact")
        self.assertIsNone(exact_payload)
        self.assertIs(exact_pricing_result, pricing)
        self.assertTrue(exact_pricing_result.exhausted)
        self.assertEqual(len(exact_pricing_result.routes), 3)

    def test_route_pool_hygiene_admission_respects_min_depth(self):
        _data, routes, tree = self._route_pool_hygiene_fixture()
        tree.route_pool_hygiene_admission_min_depth = 1
        pricing = PricingResult(
            routes=routes,
            exhausted=True,
            best_reduced_cost=-1.0,
            label_pops=10,
            generated_labels=20,
            negative_routes=len(routes),
        )

        root_filtered, root_payload = tree._apply_route_pool_hygiene_admission(
            pricing,
            pricing_kind="heuristic",
            node=BPCNode(0.0, 0, 0),
        )
        self.assertIs(root_filtered, pricing)
        self.assertIsNone(root_payload)

        child_filtered, child_payload = tree._apply_route_pool_hygiene_admission(
            pricing,
            pricing_kind="heuristic",
            node=BPCNode(0.0, 1, 1),
        )
        self.assertIsNotNone(child_payload)
        assert child_payload is not None
        self.assertEqual(child_payload["filtered_routes"], 1)
        self.assertEqual(len(child_filtered.routes), 2)
        self.assertFalse(child_filtered.exhausted)

    def test_route_pool_hygiene_admission_protects_active_task_sets(self):
        data, routes, tree = self._route_pool_hygiene_fixture()
        extra = evaluate_route(data, (3, 1))
        self.assertIsNotNone(extra)
        assert extra is not None
        pricing = PricingResult(
            routes=[routes[0], routes[1], routes[2], extra],
            exhausted=True,
            best_reduced_cost=-1.0,
            label_pops=10,
            generated_labels=20,
            negative_routes=4,
        )
        solution = RMPSolution(
            status="optimal",
            objective=0.0,
            duals=None,
            artificial_sum=0.0,
            route_values=[(routes[0], 1, 0.5)],
            y_values={1: 1.0},
            variable_count=0,
            constraint_count=0,
        )
        filtered, payload = tree._apply_route_pool_hygiene_admission(
            pricing,
            pricing_kind="heuristic",
            node=BPCNode(0.0, 1, 1),
            solution=solution,
        )
        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload["protected_routes"], 2)
        self.assertEqual(payload["protected_task_set_count"], 1)
        self.assertEqual(payload["filtered_routes"], 1)
        self.assertEqual(len(filtered.routes), 3)
        self.assertIn(routes[0], filtered.routes)
        self.assertIn(routes[1], filtered.routes)
        self.assertEqual(tree.stats.route_pool_hygiene_admission_protected, 2)

    def test_route_pool_restart_can_create_mid_node_local_pool_from_solution(self):
        _data, routes, tree = self._route_pool_hygiene_fixture()
        for route in routes:
            tree.pool.add(route)
        tree.route_pool_restart_enabled = True
        tree.route_pool_restart_cleanup_enabled = True
        tree.route_pool_restart_max_routes = 2
        tree.route_pool_restart_min_global_routes = 2
        tree.route_pool_restart_max_routes_per_task_set = 1
        solution = RMPSolution(
            status="optimal",
            objective=0.0,
            duals=None,
            artificial_sum=0.0,
            route_values=[(tree.pool.by_signature[routes[0].signature], 1, 0.5)],
            y_values={1: 1.0},
            variable_count=0,
            constraint_count=0,
        )

        created = tree._create_node_route_pool_from_solution(
            BPCNode(0.0, 3, 0),
            solution,
            {route.signature: 0 for route in tree.pool.routes},
            cg_iter=4,
        )

        self.assertIsNotNone(created)
        assert created is not None
        local_pool, local_birth_iter = created
        self.assertEqual(len(local_pool.routes), 2)
        self.assertIn(routes[0].signature, local_pool.by_signature)
        same_task_set_routes = [
            route
            for route in local_pool.routes
            if tuple(sorted(route.task_set)) == tuple(sorted(routes[0].task_set))
        ]
        self.assertEqual(len(same_task_set_routes), 1)
        self.assertEqual(set(local_birth_iter), set(local_pool.by_signature))
        self.assertEqual(tree.stats.route_pool_restart_nodes, 1)
        self.assertEqual(tree.stats.route_pool_restart_rounds, 1)
        self.assertEqual(tree.stats.route_pool_restart_routes_omitted_total, 1)

        tree.route_pool_restart_max_depth = 0
        blocked = tree._create_node_route_pool_from_solution(
            BPCNode(0.0, 4, 1),
            solution,
            {route.signature: 0 for route in tree.pool.routes},
            cg_iter=4,
        )
        self.assertIsNone(blocked)

    def test_restricted_master_adaptive_reduces_budget_and_then_skips(self):
        _data, routes, tree = self._route_pool_hygiene_fixture()
        for route in routes:
            tree.pool.add(route)
        tree.restricted_master_heuristic_enabled = True
        tree.time_limit = 100.0
        tree.restricted_master_time_limit = 20.0
        tree.restricted_master_max_depth = 10
        tree.restricted_master_max_calls = 10
        tree.restricted_master_adaptive_enabled = True
        tree.restricted_master_adaptive_min_depth = 1
        tree.restricted_master_adaptive_after_failures = 1
        tree.restricted_master_adaptive_reduced_time_limit = 3.0
        tree.restricted_master_adaptive_skip_after_failures = 2
        solution = RMPSolution(
            status="optimal",
            objective=100.0,
            duals=None,
            artificial_sum=0.0,
            route_values=[],
            y_values={1: 0.0},
            variable_count=0,
            constraint_count=0,
        )
        time_limits: list[float] = []

        def fake_rim(*args, **kwargs):
            time_limits.append(float(kwargs["time_limit"]))
            return RestrictedIntegerResult(
                status="TIME_LIMIT",
                objective=None,
                assigned_routes={},
                solving_time=float(kwargs["time_limit"]),
                variable_count=0,
                constraint_count=0,
                selected_routes=0,
            )

        node = BPCNode(0.0, 1, 1)
        with patch("bpc.tree.solve_restricted_integer_master", side_effect=fake_rim):
            self.assertEqual(tree._try_restricted_master_heuristic(node, solution), 0)
            self.assertEqual(tree._try_restricted_master_heuristic(node, solution), 0)
            self.assertEqual(tree._try_restricted_master_heuristic(node, solution), 0)

        self.assertEqual(time_limits, [20.0, 3.0])
        self.assertEqual(tree.stats.restricted_master_integer_calls, 2)
        self.assertEqual(tree.stats.restricted_master_adaptive_time_limit_reductions, 1)
        self.assertEqual(tree.stats.restricted_master_adaptive_skips, 1)
        self.assertEqual(tree.stats.restricted_master_adaptive_failure_streak_max, 2)

    def test_restricted_master_productivity_guard_forces_probe_after_bounded_skips(self):
        _data, routes, tree = self._route_pool_hygiene_fixture()
        for route in routes:
            tree.pool.add(route)
        tree.restricted_master_heuristic_enabled = True
        tree.time_limit = 100.0
        tree.restricted_master_time_limit = 20.0
        tree.restricted_master_max_depth = 10
        tree.restricted_master_max_calls = 10
        tree.restricted_master_adaptive_enabled = True
        tree.restricted_master_adaptive_min_depth = 1
        tree.restricted_master_adaptive_after_failures = 1
        tree.restricted_master_adaptive_reduced_time_limit = 3.0
        tree.restricted_master_adaptive_skip_after_failures = 0
        tree.restricted_master_adaptive_productivity_guard_enabled = True
        tree.restricted_master_adaptive_productive_after_failures = 2
        tree.restricted_master_adaptive_productive_max_consecutive_skips = 2
        solution = RMPSolution(
            status="optimal",
            objective=100.0,
            duals=None,
            artificial_sum=0.0,
            route_values=[],
            y_values={1: 0.0},
            variable_count=0,
            constraint_count=0,
        )
        time_limits: list[float] = []

        def fake_rim(*args, **kwargs):
            time_limits.append(float(kwargs["time_limit"]))
            return RestrictedIntegerResult(
                status="TIME_LIMIT",
                objective=None,
                assigned_routes={},
                solving_time=float(kwargs["time_limit"]),
                variable_count=0,
                constraint_count=0,
                selected_routes=0,
            )

        node = BPCNode(0.0, 1, 1)
        with patch("bpc.tree.solve_restricted_integer_master", side_effect=fake_rim):
            for _ in range(5):
                self.assertEqual(tree._try_restricted_master_heuristic(node, solution), 0)

        self.assertEqual(time_limits, [20.0, 3.0, 3.0])
        self.assertEqual(tree.stats.restricted_master_integer_calls, 3)
        self.assertEqual(tree.stats.restricted_master_adaptive_time_limit_reductions, 2)
        self.assertEqual(tree.stats.restricted_master_adaptive_skips, 2)
        self.assertEqual(tree.stats.restricted_master_adaptive_probe_forced, 1)
        self.assertEqual(tree.stats.restricted_master_adaptive_unproductive_streak_max, 3)

    def test_restricted_master_productivity_guard_resets_on_raw_improvement(self):
        _data, routes, tree = self._route_pool_hygiene_fixture()
        for route in routes:
            tree.pool.add(route)
        tree.restricted_master_heuristic_enabled = True
        tree.time_limit = 100.0
        tree.restricted_master_time_limit = 20.0
        tree.restricted_master_max_depth = 10
        tree.restricted_master_max_calls = 10
        tree.restricted_master_adaptive_enabled = True
        tree.restricted_master_adaptive_min_depth = 1
        tree.restricted_master_adaptive_after_failures = 1
        tree.restricted_master_adaptive_reduced_time_limit = 3.0
        tree.restricted_master_adaptive_skip_after_failures = 0
        tree.restricted_master_adaptive_productivity_guard_enabled = True
        tree.restricted_master_adaptive_productive_after_failures = 99
        tree.restricted_master_adaptive_productive_max_consecutive_skips = 2
        solution = RMPSolution(
            status="optimal",
            objective=100.0,
            duals=None,
            artificial_sum=0.0,
            route_values=[],
            y_values={1: 0.0},
            variable_count=0,
            constraint_count=0,
        )
        responses = iter(
            [
                RestrictedIntegerResult(
                    status="TIME_LIMIT",
                    objective=None,
                    assigned_routes={},
                    solving_time=1.0,
                    variable_count=0,
                    constraint_count=0,
                    selected_routes=0,
                ),
                RestrictedIntegerResult(
                    status="TIME_LIMIT",
                    objective=None,
                    assigned_routes={},
                    solving_time=1.0,
                    variable_count=0,
                    constraint_count=0,
                    selected_routes=0,
                    raw_objective=90.0,
                ),
            ]
        )

        node = BPCNode(0.0, 1, 1)
        with patch("bpc.tree.solve_restricted_integer_master", side_effect=lambda *args, **kwargs: next(responses)):
            self.assertEqual(tree._try_restricted_master_heuristic(node, solution), 0)
            self.assertEqual(tree._restricted_master_adaptive_unproductive_streak, 1)
            self.assertEqual(tree._try_restricted_master_heuristic(node, solution), 0)

        self.assertEqual(tree._restricted_master_adaptive_unproductive_streak, 0)
        self.assertEqual(tree.stats.restricted_master_integer_raw_best_objective, 90.0)
        self.assertEqual(tree.stats.restricted_master_adaptive_skips, 0)

    def _pricing_stabilization_fixture(self, *, true_negative: bool = False):
        data = load_bpc_data("very_small")
        route = evaluate_route(data, (data.tasks[0],))
        self.assertIsNotNone(route)
        assert route is not None
        vehicle = data.vehicles[0]
        cover = {int(task): 0.0 for task in data.tasks}
        if true_negative:
            cover[int(data.tasks[0])] = float(route.cost) + 1.0
        duals = RMPDuals(
            cover=cover,
            task_vehicle={},
            sortie_count={int(v): 0.0 for v in data.vehicles},
            vehicle_time={int(v): 0.0 for v in data.vehicles},
            cuts={},
            branches={},
        )
        solution = RMPSolution(
            status="optimal",
            objective=0.0,
            duals=duals,
            artificial_sum=0.0,
            route_values=[],
            y_values={int(vehicle): 1.0},
            variable_count=0,
            constraint_count=0,
        )
        tree = CleanBPCTree(
            data,
            time_limit=10,
            max_nodes=10,
            eps=1.0e-6,
            integer_tol=1.0e-6,
            max_routes_per_pricing=10,
            max_labels_per_pricing=0,
            rmp_params={},
            logger=BPCLogger(None, console=False),
            pricing_dual_stabilization_enabled=True,
            pricing_tailing_diagnostics_enabled=True,
        )
        return data, route, tree, solution

    def test_stabilized_pricing_filters_by_true_reduced_cost_and_never_certifies(self):
        _data, route, tree, solution = self._pricing_stabilization_fixture(true_negative=False)
        fake = PricingResult(
            routes=[route],
            exhausted=True,
            best_reduced_cost=-1.0,
            label_pops=7,
            generated_labels=9,
            negative_routes=1,
        )
        with patch("bpc.tree.exact_pricing", return_value=fake):
            pricing, added = tree._run_pricing(
                BPCNode(0.0, 0, 0),
                solution,
                cg_iter=1,
                phase="phase2",
                pricing_kind="heuristic",
                max_routes_to_return=10,
                max_labels=100,
                selection_mode="diverse",
                pricing_duals=solution.duals,
                true_duals=solution.duals,
                dual_source="stabilized",
            )

        self.assertEqual(added, 0)
        self.assertEqual(pricing.routes, [])
        self.assertFalse(pricing.exhausted)
        self.assertEqual(pricing.false_candidate_routes, 1)
        self.assertEqual(tree.stats.pricing_stabilization_false_candidate_routes, 1)
        self.assertEqual(len(tree.pool.routes), 0)

    def test_stabilized_pricing_accepts_only_true_negative_columns(self):
        _data, route, tree, solution = self._pricing_stabilization_fixture(true_negative=True)
        fake = PricingResult(
            routes=[route],
            exhausted=True,
            best_reduced_cost=-1.0,
            label_pops=7,
            generated_labels=9,
            negative_routes=1,
        )
        with patch("bpc.tree.exact_pricing", return_value=fake):
            pricing, added = tree._run_pricing(
                BPCNode(0.0, 0, 0),
                solution,
                cg_iter=1,
                phase="phase2",
                pricing_kind="heuristic",
                max_routes_to_return=10,
                max_labels=100,
                selection_mode="diverse",
                pricing_duals=solution.duals,
                true_duals=solution.duals,
                dual_source="stabilized",
            )

        self.assertEqual(added, 1)
        self.assertEqual(pricing.routes, [route])
        self.assertFalse(pricing.exhausted)
        self.assertEqual(pricing.false_candidate_routes, 0)
        self.assertEqual(tree.stats.pricing_stabilization_true_negative_routes, 1)
        self.assertEqual(len(tree.pool.routes), 1)

    def test_selective_pricing_controller_requires_slow_exact_history(self):
        _data, _route, tree, _solution = self._pricing_stabilization_fixture()
        tree.selective_pricing_controller_enabled = True
        tree.selective_pricing_min_depth = 1
        tree.selective_pricing_slow_exact_streak = 1
        self.assertFalse(tree._selective_pricing_should_try_extra(BPCNode(0.0, 0, 0)))
        self.assertFalse(tree._selective_pricing_should_try_extra(BPCNode(0.0, 1, 1)))
        tree._selective_pricing_slow_exact_streak = 1
        self.assertTrue(tree._selective_pricing_should_try_extra(BPCNode(0.0, 1, 1)))

    def test_branch_heuristic_boost_empty_certificate_skip_is_configured(self):
        _data, _route, tree, _solution = self._pricing_stabilization_fixture()
        self.assertFalse(tree._branch_heuristic_boost_should_skip(100))
        tree.branch_node_heuristic_boost_skip_after_empty_certificates = 2
        self.assertFalse(tree._branch_heuristic_boost_should_skip(1))
        self.assertTrue(tree._branch_heuristic_boost_should_skip(2))

    def test_pricing_tailing_classifies_slow_certificate(self):
        _data, _route, tree, _solution = self._pricing_stabilization_fixture()
        tree.pricing_tailing_label_threshold = 100
        pricing = PricingResult(
            routes=[],
            exhausted=True,
            best_reduced_cost=None,
            label_pops=101,
            generated_labels=101,
            negative_routes=0,
        )
        classification = tree._record_pricing_tailing_diagnostic(
            node=BPCNode(0.0, 0, 0),
            cg_iter=1,
            phase="phase2",
            pricing_kind="exact",
            pricing=pricing,
            added=0,
            duplicate_task_sets=0,
            repeated_task_sets=0,
            rmp_objective_delta=0.0,
        )
        self.assertEqual(classification, "certificate_slow")
        self.assertEqual(tree.stats.pricing_tailing_certificate_slow, 1)
        self.assertEqual(tree.stats.pricing_tailing_exact_label_pops, 101)

    def test_restricted_master_gap_guard_skips_near_proof(self):
        _data, routes, tree = self._route_pool_hygiene_fixture()
        for route in routes:
            tree.pool.add(route)
        tree.restricted_master_heuristic_enabled = True
        tree.restricted_master_max_depth = 10
        tree.restricted_master_max_calls = 10
        tree.restricted_master_adaptive_enabled = True
        tree.restricted_master_adaptive_min_depth = 1
        tree.restricted_master_adaptive_productivity_guard_enabled = True
        tree.restricted_master_adaptive_productive_after_failures = 1
        tree.restricted_master_adaptive_productive_max_consecutive_skips = 1
        tree.restricted_master_adaptive_gap_guard_enabled = True
        tree.restricted_master_adaptive_near_proof_gap = 0.005
        tree._restricted_master_adaptive_unproductive_streak = 1
        tree.incumbent = Incumbent(objective=100.0, route_values=[], y_values={}, node_id=0)
        tree.stats.time_to_best_incumbent = 0.0
        solution = RMPSolution(
            status="optimal",
            objective=99.8,
            duals=None,
            artificial_sum=0.0,
            route_values=[],
            y_values={1: 1.0},
            variable_count=0,
            constraint_count=0,
        )

        with patch("bpc.tree.solve_restricted_integer_master") as mocked_rim:
            self.assertEqual(tree._try_restricted_master_heuristic(BPCNode(0.0, 1, 1), solution), 0)

        mocked_rim.assert_not_called()
        self.assertEqual(tree.stats.restricted_master_adaptive_gap_skips, 1)
        self.assertEqual(tree.stats.restricted_master_adaptive_skips, 1)

    def test_weighted_route_set_schedule_packing_default_off(self):
        _data, _routes, solution, tree = self._weighted_route_set_packing_fixture()
        tree.weighted_route_schedule_packing_cuts_enabled = False
        added = tree._separate_weighted_route_schedule_packing_cuts(BPCNode(0.0, 0, 0), solution)
        self.assertEqual(added, 0)
        self.assertEqual(tree.cuts, [])

    def test_schedule_pack_diagnostic_solves_restricted_lp(self):
        self._require_pyscipopt()
        data = load_bpc_data("very_small")
        routes = [evaluate_route(data, (task,)) for task in data.tasks]
        self.assertTrue(all(route is not None for route in routes))
        routes = [route for route in routes if route is not None]
        result = solve_schedule_pack_restricted_lp(
            data,
            routes,
            max_candidate_routes=20,
            max_columns=100,
            beam_width=20,
            time_limit=5.0,
        )
        self.assertEqual(result.status, "OPTIMAL")
        self.assertIsNotNone(result.objective)
        self.assertGreater(result.column_count, 0)

    def test_schedule_pack_full_route_space_pricing_marks_exact_on_small_instance(self):
        self._require_pyscipopt()
        data = load_bpc_data("very_small")
        routes = [evaluate_route(data, (task,)) for task in data.tasks]
        self.assertTrue(all(route is not None for route in routes))
        routes = [route for route in routes if route is not None]
        result = solve_schedule_pack_node_relaxation(
            data,
            routes,
            [],
            (),
            max_candidate_routes=20,
            max_columns=200,
            beam_width=50,
            time_limit=10.0,
            pricing_batch_size=4,
            full_route_space_pricing=True,
        )
        self.assertEqual(result.status, "OPTIMAL")
        self.assertTrue(result.exact_over_full_route_space)
        self.assertGreaterEqual(result.full_pricing_route_count, len(routes))

    def test_schedule_pack_skips_vacuous_cut_without_dual_error(self):
        self._require_pyscipopt()
        data = load_bpc_data("very_small")
        routes = [evaluate_route(data, (task,)) for task in data.tasks]
        self.assertTrue(all(route is not None for route in routes))
        routes = [route for route in routes if route is not None]
        cut = SubsetRowCut(id=99, tasks=tuple(data.tasks[:2]), divisor=3)
        result = solve_schedule_pack_node_relaxation(
            data,
            routes,
            [cut],
            (),
            max_candidate_routes=20,
            max_columns=100,
            beam_width=20,
            time_limit=5.0,
        )
        self.assertEqual(result.status, "OPTIMAL")
        self.assertIsNotNone(result.objective)

    def test_route_set_schedule_packing_separator_adds_high_order_cut(self):
        instance = {
            "name": "route_set_packing_separator_smoke",
            "tasks": {
                "1": {"r": 0, "D": 10, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "2": {"r": 0, "D": 10, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "3": {"r": 0, "D": 10, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
            },
        }
        pairwise = {}
        for i in (0, 1, 2, 3):
            for j in (0, 1, 2, 3):
                tau = 0 if i == j else (1 if i == 0 or j == 0 else 10)
                pairwise[f"{i}->{j}"] = {"tau": tau, "energy": 0, "cost": tau, "path": []}
        data = BPCData(
            instance=instance,
            pairwise=pairwise,
            instance_path=Path("synthetic"),
            name="route_set_packing_separator_smoke",
            tasks=(1, 2, 3),
            vehicles=(1,),
            sortie_limit=3,
            capacity=10,
            energy_limit=10,
            rho=1,
            fixed_vehicle_cost=100,
            horizon=5,
        )
        routes = [evaluate_route(data, (task,)) for task in data.tasks]
        self.assertTrue(all(route is not None for route in routes))
        routes = [route for route in routes if route is not None]
        solution = RMPSolution(
            status="optimal",
            objective=0.0,
            duals=None,
            artificial_sum=0.0,
            route_values=[(route, 1, 0.45) for route in routes],
            y_values={1: 0.5},
            variable_count=0,
            constraint_count=0,
        )
        tree = CleanBPCTree(
            data,
            time_limit=10,
            max_nodes=10,
            eps=1.0e-6,
            integer_tol=1.0e-6,
            max_routes_per_pricing=10,
            max_labels_per_pricing=0,
            rmp_params={},
            logger=BPCLogger(None, console=False),
            route_set_schedule_packing_cuts_enabled=True,
            route_set_schedule_packing_cut_max_support_routes=10,
            route_set_schedule_packing_cut_max_routes=3,
            route_set_schedule_packing_cut_min_violation=0.05,
        )
        added = tree._separate_route_set_schedule_packing_cuts(BPCNode(0.0, 0, 0), solution)
        self.assertEqual(added, 1)
        self.assertEqual(tree.cuts[0].kind, "schedule_route_set_packing")
        self.assertEqual(tree.cuts[0].rhs, 0.0)
        self.assertEqual(tree.cuts[0].upper_bound, 2.0)
        self.assertEqual(tree.cuts[0].y_coefficient(1), -2.0)
        self.assertEqual(tree.stats.schedule_route_set_packing_cuts_added, 1)

    def _root_schedule_capacity_fixture(
        self,
        *,
        max_states: int = 200000,
        y_value: float = 1.0,
        lambda_value: float = 0.6,
        vehicles: tuple[int, ...] = (1,),
    ):
        instance = {
            "name": "root_schedule_capacity_smoke",
            "tasks": {
                "1": {"r": 0, "D": 1, "sigma": 1, "d": 1, "g": 0, "c_srv": 0},
                "2": {"r": 0, "D": 1, "sigma": 1, "d": 1, "g": 0, "c_srv": 0},
                "3": {"r": 0, "D": 1, "sigma": 1, "d": 1, "g": 0, "c_srv": 0},
            },
        }
        pairwise = {
            f"{i}->{j}": {"tau": 0, "energy": 0, "cost": 1 if i != j else 0, "path": []}
            for i in (0, 1, 2, 3)
            for j in (0, 1, 2, 3)
        }
        data = BPCData(
            instance=instance,
            pairwise=pairwise,
            instance_path=Path("synthetic"),
            name="root_schedule_capacity_smoke",
            tasks=(1, 2, 3),
            vehicles=vehicles,
            sortie_limit=3,
            capacity=10,
            energy_limit=10,
            rho=1,
            fixed_vehicle_cost=100,
            horizon=3,
        )
        routes = [evaluate_route(data, (task,)) for task in data.tasks]
        self.assertTrue(all(route is not None for route in routes))
        routes = [route for route in routes if route is not None]
        solution = RMPSolution(
            status="optimal",
            objective=0.0,
            duals=None,
            artificial_sum=0.0,
            route_values=[(route, vehicle, lambda_value) for vehicle in vehicles for route in routes],
            y_values={vehicle: y_value for vehicle in vehicles},
            variable_count=0,
            constraint_count=0,
        )
        tree = CleanBPCTree(
            data,
            time_limit=10,
            max_nodes=10,
            eps=1.0e-6,
            integer_tol=1.0e-6,
            max_routes_per_pricing=10,
            max_labels_per_pricing=0,
            rmp_params={},
            logger=BPCLogger(None, console=False),
            root_schedule_capacity_cuts_enabled=True,
            root_schedule_capacity_max_depth=0,
            root_schedule_capacity_pair_budget=10,
            root_schedule_capacity_triple_budget=10,
            root_schedule_capacity_oracle_max_states=max_states,
            root_schedule_capacity_time_budget=5.0,
            root_schedule_capacity_min_violation=1.0e-5,
        )
        return tree, solution

    def test_root_schedule_capacity_separator_adds_exact_violated_cut(self):
        tree, solution = self._root_schedule_capacity_fixture()
        tree.root_schedule_capacity_triple_budget = 0
        added = tree._separate_root_schedule_capacity_cuts(BPCNode(0.0, 0, 0), solution)
        self.assertGreaterEqual(added, 1)
        self.assertIsInstance(tree.cuts[0], ScheduleCapacityCut)
        self.assertEqual(len(tree.cuts[0].tasks), 2)
        self.assertEqual(tree.cuts[0].upper_bound, 1)
        self.assertEqual(tree.cuts[0].source, "root_schedule_capacity")
        self.assertEqual(tree.stats.root_schedule_capacity_cuts_added, added)

    def test_root_schedule_capacity_triple_u1_not_filtered_by_old_precheck(self):
        tree, solution = self._root_schedule_capacity_fixture(y_value=1.0, lambda_value=0.4)
        tree.root_schedule_capacity_pair_budget = 0
        added = tree._separate_root_schedule_capacity_cuts(BPCNode(0.0, 0, 0), solution)
        self.assertGreaterEqual(added, 1)
        triple_cuts = [cut for cut in tree.cuts if isinstance(cut, ScheduleCapacityCut) and len(cut.tasks) == 3]
        self.assertEqual(len(triple_cuts), 1)
        self.assertEqual(triple_cuts[0].upper_bound, 1)
        self.assertGreater(tree.stats.root_schedule_capacity_oracle_queries, 0)
        self.assertGreater(tree.stats.root_schedule_capacity_candidates_after_precheck, 0)

    def test_root_schedule_capacity_incomplete_oracle_does_not_add_cut(self):
        tree, solution = self._root_schedule_capacity_fixture(max_states=0)
        tree.root_schedule_capacity_stop_after_no_add_rounds = 10
        added = tree._separate_root_schedule_capacity_cuts(BPCNode(0.0, 0, 0), solution)
        self.assertEqual(added, 0)
        self.assertEqual(len(tree.cuts), 0)
        self.assertGreater(tree.stats.root_schedule_capacity_oracle_incomplete, 0)
        self.assertIn((1, 2), tree.root_schedule_capacity_cache)
        self.assertIsNone(tree.root_schedule_capacity_cache[(1, 2)])
        cache_hits_before = tree.stats.root_schedule_capacity_cache_hits
        queries_before = tree.stats.root_schedule_capacity_oracle_queries
        added_again = tree._separate_root_schedule_capacity_cuts(BPCNode(0.0, 0, 0), solution)
        self.assertEqual(added_again, 0)
        self.assertGreater(tree.stats.root_schedule_capacity_cache_hits, cache_hits_before)
        self.assertEqual(tree.stats.root_schedule_capacity_oracle_queries, queries_before)

    def test_root_schedule_capacity_precheck_skips_oracle(self):
        tree, solution = self._root_schedule_capacity_fixture(y_value=1.0, lambda_value=0.2)
        added = tree._separate_root_schedule_capacity_cuts(BPCNode(0.0, 0, 0), solution)
        self.assertEqual(added, 0)
        self.assertEqual(tree.stats.root_schedule_capacity_oracle_queries, 0)
        self.assertEqual(tree.root_schedule_capacity_cache, {})

    def test_root_schedule_capacity_duplicate_skips_second_oracle(self):
        tree, solution = self._root_schedule_capacity_fixture()
        node = BPCNode(0.0, 0, 0)
        first = tree._separate_root_schedule_capacity_cuts(node, solution)
        queries_after_first = tree.stats.root_schedule_capacity_oracle_queries
        cache_size_after_first = len(tree.root_schedule_capacity_cache)
        second = tree._separate_root_schedule_capacity_cuts(node, solution)
        self.assertGreaterEqual(first, 1)
        self.assertEqual(second, 0)
        self.assertEqual(tree.stats.root_schedule_capacity_oracle_queries, queries_after_first)
        self.assertEqual(len(tree.root_schedule_capacity_cache), cache_size_after_first)

    def test_task_schedule_capacity_exact_not_tight_cached_without_cut(self):
        instance = {
            "name": "task_schedcap_not_tight",
            "tasks": {
                "1": {"r": 0, "D": 10, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "2": {"r": 0, "D": 10, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
            },
        }
        pairwise = {
            f"{i}->{j}": {"tau": 0 if i == j else 1, "energy": 0, "cost": 0 if i == j else 1, "path": []}
            for i in (0, 1, 2)
            for j in (0, 1, 2)
        }
        data = BPCData(instance, pairwise, Path("synthetic"), "task_schedcap_not_tight", (1, 2), (1,), 2, 10, 10, 1, 100, 20)
        routes = [evaluate_route(data, (task,)) for task in data.tasks]
        self.assertTrue(all(route is not None for route in routes))
        routes = [route for route in routes if route is not None]
        solution = RMPSolution("optimal", 0.0, None, 0.0, [(route, 1, 0.6) for route in routes], {1: 1.0}, 0, 0)
        tree = CleanBPCTree(
            data,
            time_limit=10,
            max_nodes=10,
            eps=1.0e-6,
            integer_tol=1.0e-6,
            max_routes_per_pricing=10,
            max_labels_per_pricing=0,
            rmp_params={},
            logger=BPCLogger(None, console=False),
            task_schedule_capacity_cuts_enabled=True,
            task_schedule_capacity_pair_budget=10,
            task_schedule_capacity_triple_budget=0,
        )
        added = tree._separate_root_schedule_capacity_cuts(BPCNode(0.0, 0, 0), solution)
        self.assertEqual(added, 0)
        self.assertEqual(tree.stats.task_schedule_capacity_exact_not_tight, 1)
        self.assertIn((1, 2), tree.task_schedule_capacity_cache)

    def test_task_schedule_capacity_exact_tight_not_violated(self):
        instance = {
            "name": "task_schedcap_tight_not_violated",
            "tasks": {
                "1": {"r": 0, "D": 20, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "2": {"r": 0, "D": 20, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "3": {"r": 0, "D": 20, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
            },
        }
        pairwise = {}
        for i in (0, 1, 2, 3):
            for j in (0, 1, 2, 3):
                tau = 0 if i == j else (1 if i == 0 or j == 0 else 10)
                pairwise[f"{i}->{j}"] = {"tau": tau, "energy": 0, "cost": tau, "path": []}
        data = BPCData(instance, pairwise, Path("synthetic"), "task_schedcap_tight_not_violated", (1, 2, 3), (1,), 2, 10, 10, 1, 100, 4)
        routes = [evaluate_route(data, (task,)) for task in data.tasks]
        self.assertTrue(all(route is not None for route in routes))
        routes = [route for route in routes if route is not None]
        solution = RMPSolution("optimal", 0.0, None, 0.0, [(route, 1, 0.4) for route in routes], {1: 1.0}, 0, 0)
        tree = CleanBPCTree(
            data,
            time_limit=10,
            max_nodes=10,
            eps=1.0e-6,
            integer_tol=1.0e-6,
            max_routes_per_pricing=10,
            max_labels_per_pricing=0,
            rmp_params={},
            logger=BPCLogger(None, console=False),
            task_schedule_capacity_cuts_enabled=True,
            task_schedule_capacity_pair_budget=0,
            task_schedule_capacity_triple_budget=10,
        )
        added = tree._separate_root_schedule_capacity_cuts(BPCNode(0.0, 0, 0), solution)
        self.assertEqual(added, 0)
        self.assertEqual(tree.stats.task_schedule_capacity_exact_tight_not_violated, 1)
        self.assertEqual(tree.task_schedule_capacity_cache[(1, 2, 3)].upper_bound, 2)

    def test_task_schedule_capacity_reuses_exact_cache_across_vehicles(self):
        tree, solution = self._root_schedule_capacity_fixture(vehicles=(1, 2))
        solution = RMPSolution(
            solution.status,
            solution.objective,
            solution.duals,
            solution.artificial_sum,
            [(route, vehicle, value) for route, vehicle, value in solution.route_values if 3 not in route.task_set],
            solution.y_values,
            solution.variable_count,
            solution.constraint_count,
        )
        tree.task_schedule_capacity_cuts_enabled = True
        tree.task_schedule_capacity_pair_budget = 2
        tree.task_schedule_capacity_triple_budget = 0
        tree.task_schedule_capacity_max_cuts_per_round = 2
        added = tree._separate_root_schedule_capacity_cuts(BPCNode(0.0, 0, 0), solution)
        self.assertEqual(added, 2)
        self.assertEqual(tree.stats.task_schedule_capacity_oracle_computations, 1)
        self.assertGreaterEqual(tree.stats.task_schedule_capacity_cache_hits, 1)

    def test_task_schedule_capacity_copy_to_all_vehicles(self):
        tree, solution = self._root_schedule_capacity_fixture(vehicles=(1, 2))
        solution = RMPSolution(
            solution.status,
            solution.objective,
            solution.duals,
            solution.artificial_sum,
            [(route, vehicle, value) for route, vehicle, value in solution.route_values if vehicle == 1],
            {1: 1.0, 2: 1.0},
            solution.variable_count,
            solution.constraint_count,
        )
        tree.task_schedule_capacity_cuts_enabled = True
        tree.task_schedule_capacity_copy_to_all_vehicles = True
        tree.task_schedule_capacity_pair_budget = 1
        tree.task_schedule_capacity_triple_budget = 0
        tree.task_schedule_capacity_max_cuts_per_round = 2
        added = tree._separate_root_schedule_capacity_cuts(BPCNode(0.0, 0, 0), solution)
        self.assertEqual(added, 2)
        self.assertEqual({cut.vehicle for cut in tree.cuts}, {1, 2})
        self.assertEqual(tree.stats.task_schedule_capacity_cuts_copied_to_all_vehicles, 1)

    def test_task_schedule_capacity_no_copy_only_violated_vehicle(self):
        tree, solution = self._root_schedule_capacity_fixture(vehicles=(1, 2))
        solution = RMPSolution(
            solution.status,
            solution.objective,
            solution.duals,
            solution.artificial_sum,
            [(route, vehicle, value) for route, vehicle, value in solution.route_values if vehicle == 1],
            {1: 1.0, 2: 1.0},
            solution.variable_count,
            solution.constraint_count,
        )
        tree.task_schedule_capacity_cuts_enabled = True
        tree.task_schedule_capacity_copy_to_all_vehicles = False
        tree.task_schedule_capacity_pair_budget = 1
        tree.task_schedule_capacity_triple_budget = 0
        tree.task_schedule_capacity_max_cuts_per_round = 1
        added = tree._separate_root_schedule_capacity_cuts(BPCNode(0.0, 0, 0), solution)
        self.assertEqual(added, 1)
        self.assertEqual({cut.vehicle for cut in tree.cuts}, {1})

    def test_task_schedule_capacity_witness_candidate_priority(self):
        tree, solution = self._root_schedule_capacity_fixture(lambda_value=0.6)
        routes = [route for route, _vehicle, _value in solution.route_values]
        witness = witness_from_routes(routes[:3], source="rim_witness", vehicle=1, node_id=0)
        self.assertIsNotNone(witness)
        assert witness is not None
        generation = generate_task_schedule_capacity_candidates(
            tree.data,
            vehicles=(1,),
            y_values={1: 1.0},
            task_values_by_vehicle={1: tree._vehicle_task_values(solution, 1)},
            support_routes_by_vehicle={1: []},
            witness_memory={witness.tasks: witness},
            min_violation=1.0e-6,
            pair_budget=10,
            triple_budget=10,
            small_set_budget=1,
            max_subset_size=3,
            use_rim_witness=True,
            use_route_pack_witness=True,
            use_incompatibility_witness=True,
            use_time_window_clusters=False,
        )
        self.assertTrue(generation.candidates)
        self.assertTrue(generation.candidates[0].from_rim_conflict)

    def test_task_schedule_capacity_default_off(self):
        tree, solution = self._root_schedule_capacity_fixture()
        tree.task_schedule_capacity_cuts_enabled = False
        tree.root_schedule_capacity_cuts_enabled = False
        added = tree._separate_root_schedule_capacity_cuts(BPCNode(0.0, 0, 0), solution)
        self.assertEqual(added, 0)
        self.assertEqual(tree.cuts, [])

    def test_task_schedule_capacity_branch_signal_recorded(self):
        tree, solution = self._root_schedule_capacity_fixture()
        tree.task_schedule_capacity_cuts_enabled = True
        tree.task_schedule_capacity_branch_signal_enabled = True
        tree.task_schedule_capacity_pair_budget = 10
        tree.task_schedule_capacity_triple_budget = 0
        added = tree._separate_root_schedule_capacity_cuts(BPCNode(0.0, 0, 0), solution)
        self.assertGreaterEqual(added, 1)
        summary = tree._task_schedule_capacity_branch_summary()
        self.assertTrue(summary["enabled"])
        self.assertGreater(summary["candidates"], 0)

    def test_route_pack_branch_signal_respects_apply_min_depth(self):
        data = load_bpc_data("very_small")
        tree = CleanBPCTree(
            data,
            time_limit=10,
            max_nodes=10,
            eps=1.0e-6,
            integer_tol=1.0e-6,
            max_routes_per_pricing=10,
            max_labels_per_pricing=0,
            rmp_params={},
            logger=BPCLogger(None, console=False),
            route_pack_branch_signal_enabled=True,
            route_pack_branch_signal_apply_enabled=True,
            route_pack_branch_signal_apply_min_depth=1,
            route_pack_branch_signal_boost=0.02,
        )
        tree.route_pack_branch_arc_scores[(1, 2)] = 10.0
        candidate = BranchCandidate(
            kind="arc",
            left=BranchConstraint("arc_off", 1, 2),
            right=BranchConstraint("arc_on", 1, 2),
            value=0.5,
            fractionality=0.5,
        )
        self.assertEqual(tree._route_pack_branch_boost(candidate, BPCNode(0.0, 0, 0)), 0.0)
        self.assertAlmostEqual(tree._route_pack_branch_boost(candidate, BPCNode(0.0, 1, 1)), 0.2)
        self.assertEqual(tree._route_pack_branch_summary()["apply_min_depth"], 1)

    def test_subset_row_separator_adds_violated_cut(self):
        instance = {
            "name": "subset_row_separator_smoke",
            "tasks": {
                "1": {"r": 0, "D": 100, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "2": {"r": 0, "D": 100, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "3": {"r": 0, "D": 100, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
            },
        }
        pairwise = {
            f"{i}->{j}": {"tau": 0 if i == j else 1, "energy": 0, "cost": 0 if i == j else 1, "path": []}
            for i in (0, 1, 2, 3)
            for j in (0, 1, 2, 3)
        }
        data = BPCData(
            instance=instance,
            pairwise=pairwise,
            instance_path=Path("synthetic"),
            name="subset_row_separator_smoke",
            tasks=(1, 2, 3),
            vehicles=(1,),
            sortie_limit=3,
            capacity=10,
            energy_limit=10,
            rho=1,
            fixed_vehicle_cost=100,
            horizon=100,
        )
        routes = [evaluate_route(data, tasks) for tasks in ((1, 2), (2, 3), (1, 3))]
        self.assertTrue(all(route is not None for route in routes))
        routes = [route for route in routes if route is not None]
        solution = RMPSolution(
            status="optimal",
            objective=0.0,
            duals=None,
            artificial_sum=0.0,
            route_values=[(route, 1, 0.5) for route in routes],
            y_values={1: 1.0},
            variable_count=0,
            constraint_count=0,
        )
        tree = CleanBPCTree(
            data,
            time_limit=10,
            max_nodes=10,
            eps=1.0e-6,
            integer_tol=1.0e-6,
            max_routes_per_pricing=10,
            max_labels_per_pricing=0,
            rmp_params={},
            logger=BPCLogger(None, console=False),
            subset_row_cuts_enabled=True,
            subset_row_cut_max_subset_size=3,
            subset_row_cut_min_violation=0.05,
            subset_row_k_values=(2,),
        )
        added = tree._separate_subset_row_cuts(BPCNode(0.0, 0, 0), solution)
        self.assertEqual(added, 1)
        self.assertIsInstance(tree.cuts[0], SubsetRowCut)
        self.assertEqual(tree.cuts[0].tasks, (1, 2, 3))
        self.assertEqual(tree.stats.subset_row_cuts_added, 1)

    def test_witness_rank1_default_disabled_adds_no_cut(self):
        data = load_bpc_data("very_small")
        routes = [evaluate_route(data, (1, 2)), evaluate_route(data, (2, 3)), evaluate_route(data, (1, 3))]
        routes = [route for route in routes if route is not None]
        solution = RMPSolution(
            status="optimal",
            objective=0.0,
            duals=None,
            artificial_sum=0.0,
            route_values=[(route, data.vehicles[0], 0.5) for route in routes],
            y_values={data.vehicles[0]: 1.0},
            variable_count=0,
            constraint_count=0,
        )
        tree = CleanBPCTree(
            data,
            time_limit=10,
            max_nodes=10,
            eps=1.0e-6,
            integer_tol=1.0e-6,
            max_routes_per_pricing=10,
            max_labels_per_pricing=0,
            rmp_params={},
            logger=BPCLogger(None, console=False),
        )
        tree._record_witness_rank1_tasks((1, 2, 3), source="route_pack_roi_same_pool_degeneracy", node_id=0)
        added = tree._separate_witness_rank1_cuts(BPCNode(0.0, 0, 0), solution)
        self.assertEqual(added, 0)
        self.assertEqual(tree.cuts, [])

    def test_witness_rank1_roi_is_not_recorded_when_separator_disabled(self):
        data = load_bpc_data("very_small")
        tree = CleanBPCTree(
            data,
            time_limit=10,
            max_nodes=10,
            eps=1.0e-6,
            integer_tol=1.0e-6,
            max_routes_per_pricing=10,
            max_labels_per_pricing=0,
            rmp_params={},
            logger=BPCLogger(None, console=False),
        )
        tree._record_witness_rank1_route_pack_roi(
            0,
            {
                "low_improvement": True,
                "classification": "same_pool_degeneracy",
                "cut_core_task_union": [1, 2, 3],
                "cut_core_signatures": [[1, 2, 3]],
                "same_pool_replacement_count": 1,
                "same_pool_replacement_signatures": [[1, 2, 4]],
                "pricing_replacement_count": 0,
                "pricing_replacement_signatures": [],
                "max_task_overlap_old_pool": 0.667,
            },
        )
        self.assertEqual(tree.witness_rank1_memory, {})

    def test_witness_rank1_roi_records_replacement_candidates(self):
        data = load_bpc_data("very_small")
        solution = RMPSolution(
            status="optimal",
            objective=0.0,
            duals=None,
            artificial_sum=0.0,
            route_values=[],
            y_values={data.vehicles[0]: 1.0},
            variable_count=0,
            constraint_count=0,
        )
        tree = CleanBPCTree(
            data,
            time_limit=10,
            max_nodes=10,
            eps=1.0e-6,
            integer_tol=1.0e-6,
            max_routes_per_pricing=10,
            max_labels_per_pricing=0,
            rmp_params={},
            logger=BPCLogger(None, console=False),
            witness_rank1_cuts_enabled=True,
            witness_rank1_max_subset_size=4,
        )
        tree._record_witness_rank1_route_pack_roi(
            0,
            {
                "low_improvement": True,
                "classification": "same_pool_degeneracy",
                "cut_core_task_union": [1, 2, 3],
                "cut_core_signatures": [[1, 2, 3]],
                "same_pool_replacement_count": 1,
                "same_pool_replacement_signatures": [[1, 2, 4]],
                "pricing_replacement_count": 0,
                "pricing_replacement_signatures": [],
                "max_task_overlap_old_pool": 0.667,
            },
        )
        self.assertIn((1, 2, 3), tree.witness_rank1_memory)
        self.assertIn((1, 2, 4), tree.witness_rank1_memory)
        self.assertIn((1, 2, 3, 4), tree.witness_rank1_memory)
        subsets = tree._witness_rank1_candidate_subsets(solution)
        self.assertGreaterEqual(len(subsets), 3)
        self.assertIn(subsets[0][0], {(1, 2, 4), (1, 2, 3, 4)})
        self.assertTrue(subsets[0][1].startswith("route_pack_roi_same_pool_replacement"))

    def test_witness_rank1_separator_adds_pricing_aware_subset_row_cut(self):
        instance = {
            "name": "witness_rank1_separator_smoke",
            "tasks": {
                "1": {"r": 0, "D": 100, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "2": {"r": 0, "D": 100, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "3": {"r": 0, "D": 100, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
            },
        }
        pairwise = {
            f"{i}->{j}": {"tau": 0 if i == j else 1, "energy": 0, "cost": 0 if i == j else 1, "path": []}
            for i in (0, 1, 2, 3)
            for j in (0, 1, 2, 3)
        }
        data = BPCData(
            instance=instance,
            pairwise=pairwise,
            instance_path=Path("synthetic"),
            name="witness_rank1_separator_smoke",
            tasks=(1, 2, 3),
            vehicles=(1,),
            sortie_limit=3,
            capacity=10,
            energy_limit=10,
            rho=1,
            fixed_vehicle_cost=100,
            horizon=100,
        )
        routes = [evaluate_route(data, tasks) for tasks in ((1, 2), (2, 3), (1, 3))]
        self.assertTrue(all(route is not None for route in routes))
        routes = [route for route in routes if route is not None]
        solution = RMPSolution(
            status="optimal",
            objective=0.0,
            duals=None,
            artificial_sum=0.0,
            route_values=[(route, 1, 0.5) for route in routes],
            y_values={1: 1.0},
            variable_count=0,
            constraint_count=0,
        )
        tree = CleanBPCTree(
            data,
            time_limit=10,
            max_nodes=10,
            eps=1.0e-6,
            integer_tol=1.0e-6,
            max_routes_per_pricing=10,
            max_labels_per_pricing=0,
            rmp_params={},
            logger=BPCLogger(None, console=False),
            witness_rank1_cuts_enabled=True,
            witness_rank1_use_subset_row=True,
            witness_rank1_use_lm_rank1=False,
            witness_rank1_max_subset_size=3,
            witness_rank1_min_violation=0.05,
            subset_row_k_values=(2,),
        )
        tree._record_witness_rank1_tasks((1, 2, 3), source="route_pack_roi_same_pool_degeneracy", node_id=0, score=10.0)
        added = tree._separate_witness_rank1_cuts(BPCNode(0.0, 0, 0), solution)
        self.assertEqual(added, 1)
        self.assertIsInstance(tree.cuts[0], SubsetRowCut)
        self.assertEqual(tree.cuts[0].tasks, (1, 2, 3))
        self.assertEqual(tree.stats.witness_rank1_cuts_added, 1)
        self.assertEqual(tree.stats.witness_rank1_subset_row_cuts_added, 1)
        self.assertEqual(tree.stats.subset_row_cuts_added, 1)

    def test_lm_rank1_separator_adds_violated_cut(self):
        instance = {
            "name": "lm_rank1_separator_smoke",
            "tasks": {
                "1": {"r": 0, "D": 100, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "2": {"r": 0, "D": 100, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "3": {"r": 0, "D": 100, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
            },
        }
        pairwise = {
            f"{i}->{j}": {"tau": 0 if i == j else 1, "energy": 0, "cost": 0 if i == j else 1, "path": []}
            for i in (0, 1, 2, 3)
            for j in (0, 1, 2, 3)
        }
        data = BPCData(
            instance=instance,
            pairwise=pairwise,
            instance_path=Path("synthetic"),
            name="lm_rank1_separator_smoke",
            tasks=(1, 2, 3),
            vehicles=(1,),
            sortie_limit=3,
            capacity=10,
            energy_limit=10,
            rho=1,
            fixed_vehicle_cost=100,
            horizon=100,
        )
        routes = [evaluate_route(data, tasks) for tasks in ((1, 2), (2, 3), (1, 3))]
        self.assertTrue(all(route is not None for route in routes))
        routes = [route for route in routes if route is not None]
        solution = RMPSolution(
            status="optimal",
            objective=0.0,
            duals=None,
            artificial_sum=0.0,
            route_values=[(route, 1, 0.5) for route in routes],
            y_values={1: 1.0},
            variable_count=0,
            constraint_count=0,
        )
        tree = CleanBPCTree(
            data,
            time_limit=10,
            max_nodes=10,
            eps=1.0e-6,
            integer_tol=1.0e-6,
            max_routes_per_pricing=10,
            max_labels_per_pricing=0,
            rmp_params={},
            logger=BPCLogger(None, console=False),
            lm_rank1_cuts_enabled=True,
            lm_rank1_cut_max_subset_size=3,
            lm_rank1_cut_min_violation=0.05,
            lm_rank1_denominators=(3,),
            lm_rank1_memory_size=2,
        )
        added = tree._separate_lm_rank1_cuts(BPCNode(0.0, 0, 0), solution)
        self.assertGreaterEqual(added, 1)
        self.assertIsInstance(tree.cuts[0], LimitedMemoryRank1Cut)
        self.assertEqual(tree.cuts[0].tasks, (1, 2, 3))
        self.assertEqual(tree.stats.lm_rank1_cuts_added, added)

    def test_route_set_schedule_packing_conflict_cut_from_infeasible_routes(self):
        instance = {
            "name": "route_set_packing_conflict_smoke",
            "tasks": {
                "1": {"r": 3, "D": 4, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "2": {"r": 3, "D": 4, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "3": {"r": 3, "D": 4, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "4": {"r": 3, "D": 4, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
            },
        }
        pairwise = {
            f"{i}->{j}": {"tau": 0 if i == j else 0.5, "energy": 0, "cost": 0 if i == j else 0.5, "path": []}
            for i in (0, 1, 2, 3, 4)
            for j in (0, 1, 2, 3, 4)
        }
        data = BPCData(
            instance=instance,
            pairwise=pairwise,
            instance_path=Path("synthetic"),
            name="route_set_packing_conflict_smoke",
            tasks=(1, 2, 3, 4),
            vehicles=(1, 2),
            sortie_limit=4,
            capacity=10,
            energy_limit=10,
            rho=1,
            fixed_vehicle_cost=100,
            horizon=5,
        )
        routes = [evaluate_route(data, (task,)) for task in data.tasks]
        self.assertTrue(all(route is not None for route in routes))
        routes = [route for route in routes if route is not None]
        witness = diagnose_route_set_schedule(data, routes)
        self.assertIsNotNone(witness)
        assert witness is not None
        self.assertEqual(witness.pair_conflicts, tuple())

        tree = CleanBPCTree(
            data,
            time_limit=10,
            max_nodes=10,
            eps=1.0e-6,
            integer_tol=1.0e-6,
            max_routes_per_pricing=10,
            max_labels_per_pricing=0,
            rmp_params={},
            logger=BPCLogger(None, console=False),
            route_set_schedule_packing_cuts_enabled=True,
        )
        added, cache_hit, states = tree._add_schedule_route_set_packing_conflict_cuts(
            BPCNode(0.0, 0, 0),
            source_vehicle=1,
            routes=list(routes),
        )
        self.assertEqual(added, len(data.vehicles))
        self.assertFalse(cache_hit)
        self.assertIsNotNone(states)
        self.assertTrue(all(cut.kind == "schedule_route_set_packing" for cut in tree.cuts))
        self.assertTrue(all(cut.upper_bound == 2.0 for cut in tree.cuts))

        added_again, cache_hit_again, _states_again = tree._add_schedule_route_set_packing_conflict_cuts(
            BPCNode(0.0, 0, 0),
            source_vehicle=1,
            routes=list(routes),
        )
        self.assertEqual(added_again, 0)
        self.assertTrue(cache_hit_again)

    def test_route_set_schedule_packing_conflict_skips_nogood_equivalent_cut(self):
        instance = {
            "name": "route_set_packing_conflict_equivalent_smoke",
            "tasks": {
                "1": {"r": 0, "D": 10, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "2": {"r": 0, "D": 10, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "3": {"r": 0, "D": 10, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
            },
        }
        pairwise = {
            f"{i}->{j}": {"tau": 0 if i == j else 1, "energy": 0, "cost": 0 if i == j else 1, "path": []}
            for i in (0, 1, 2, 3)
            for j in (0, 1, 2, 3)
        }
        data = BPCData(
            instance=instance,
            pairwise=pairwise,
            instance_path=Path("synthetic"),
            name="route_set_packing_conflict_equivalent_smoke",
            tasks=(1, 2, 3),
            vehicles=(1, 2),
            sortie_limit=3,
            capacity=10,
            energy_limit=10,
            rho=1,
            fixed_vehicle_cost=100,
            horizon=5,
        )
        routes = [evaluate_route(data, (task,)) for task in data.tasks]
        self.assertTrue(all(route is not None for route in routes))
        routes = [route for route in routes if route is not None]
        witness = diagnose_route_set_schedule(data, routes)
        self.assertIsNotNone(witness)
        assert witness is not None

        tree = CleanBPCTree(
            data,
            time_limit=10,
            max_nodes=10,
            eps=1.0e-6,
            integer_tol=1.0e-6,
            max_routes_per_pricing=10,
            max_labels_per_pricing=0,
            rmp_params={},
            logger=BPCLogger(None, console=False),
            route_set_schedule_packing_cuts_enabled=True,
        )
        added, cache_hit, states = tree._add_schedule_route_set_packing_conflict_cuts(
            BPCNode(0.0, 0, 0),
            source_vehicle=1,
            routes=list(witness.routes),
        )
        self.assertEqual(added, 0)
        self.assertFalse(cache_hit)
        self.assertIsNotNone(states)
        self.assertEqual(tree.cuts, [])

    def _variant_route_pack_fixture(self, *, max_states: int = 200000, enabled: bool = True):
        instance = {
            "name": "variant_route_pack_smoke",
            "tasks": {
                "1": {"r": 0, "D": 20, "sigma": 1, "d": 1, "g": 0, "c_srv": 0},
                "2": {"r": 0, "D": 20, "sigma": 1, "d": 1, "g": 0, "c_srv": 0},
                "3": {"r": 0, "D": 20, "sigma": 1, "d": 1, "g": 0, "c_srv": 0},
                "4": {"r": 0, "D": 20, "sigma": 1, "d": 1, "g": 0, "c_srv": 0},
            },
        }
        pairwise = {
            f"{i}->{j}": {"tau": 0 if i == j else 1, "energy": 0, "cost": 0 if i == j else 1, "path": []}
            for i in (0, 1, 2, 3, 4)
            for j in (0, 1, 2, 3, 4)
        }
        data = BPCData(
            instance=instance,
            pairwise=pairwise,
            instance_path=Path("synthetic"),
            name="variant_route_pack_smoke",
            tasks=(1, 2, 3, 4),
            vehicles=(1, 2),
            sortie_limit=4,
            capacity=10,
            energy_limit=10,
            rho=1,
            fixed_vehicle_cost=100,
            horizon=5,
        )
        tree = CleanBPCTree(
            data,
            time_limit=10,
            max_nodes=10,
            eps=1.0e-6,
            integer_tol=1.0e-6,
            max_routes_per_pricing=10,
            max_labels_per_pricing=0,
            rmp_params={},
            logger=BPCLogger(None, console=False),
            route_set_schedule_packing_cuts_enabled=True,
            route_set_schedule_packing_oracle_max_states=max_states,
            schedule_variant_route_pack_cuts_enabled=enabled,
            schedule_variant_route_pack_max_variants_per_task_set=2,
            schedule_variant_route_pack_min_violation=1.0e-6,
        )
        routes = {}
        for sequence in ((1, 2), (2, 1), (3, 4), (4, 3)):
            route = evaluate_route(data, sequence)
            self.assertIsNotNone(route)
            assert route is not None
            routes[sequence] = tree.pool.add(route)
        solution = RMPSolution(
            status="optimal",
            objective=0.0,
            duals=None,
            artificial_sum=0.0,
            route_values=[(routes[(1, 2)], 1, 1.0), (routes[(3, 4)], 1, 1.0)],
            y_values={1: 1.0, 2: 1.0},
            variable_count=0,
            constraint_count=0,
        )
        return tree, routes, solution

    def test_variant_route_pack_adds_exact_finite_support_closure_cut(self):
        tree, routes, solution = self._variant_route_pack_fixture()
        added = tree._add_schedule_variant_route_pack_conflict_cuts(
            BPCNode(0.0, 0, 0),
            source_vehicle=1,
            routes=[routes[(1, 2)], routes[(3, 4)]],
            solution=solution,
            source="test",
        )
        self.assertEqual(added, 1)
        self.assertEqual(tree.stats.schedule_variant_route_pack_cuts_added, 1)
        self.assertEqual(tree.stats.schedule_route_set_packing_cuts_added, 1)
        cut = tree.cuts[0]
        self.assertEqual(cut.kind, "schedule_route_set_packing")
        self.assertEqual(cut.vehicle, 1)
        self.assertEqual(cut.upper_bound, 1.0)
        self.assertEqual(len(cut.signatures), 4)
        self.assertEqual(cut.coefficient(routes[(2, 1)], 1), 1.0)
        self.assertEqual(cut.coefficient(routes[(4, 3)], 1), 1.0)

    def test_variant_route_pack_default_off_does_not_add_cut(self):
        tree, routes, solution = self._variant_route_pack_fixture(enabled=False)
        added = tree._add_schedule_variant_route_pack_conflict_cuts(
            BPCNode(0.0, 0, 0),
            source_vehicle=1,
            routes=[routes[(1, 2)], routes[(3, 4)]],
            solution=solution,
            source="test",
        )
        self.assertEqual(added, 0)
        self.assertEqual(tree.cuts, [])
        self.assertEqual(tree.stats.schedule_variant_route_pack_candidates, 0)

    def test_variant_route_pack_incomplete_oracle_is_cached_without_cut(self):
        tree, routes, solution = self._variant_route_pack_fixture(max_states=1)
        added = tree._add_schedule_variant_route_pack_conflict_cuts(
            BPCNode(0.0, 0, 0),
            source_vehicle=1,
            routes=[routes[(1, 2)], routes[(3, 4)]],
            solution=solution,
            source="test",
        )
        self.assertEqual(added, 0)
        self.assertEqual(tree.cuts, [])
        self.assertEqual(tree.stats.schedule_variant_route_pack_oracle_incomplete, 1)
        added_again = tree._add_schedule_variant_route_pack_conflict_cuts(
            BPCNode(0.0, 0, 0),
            source_vehicle=1,
            routes=[routes[(1, 2)], routes[(3, 4)]],
            solution=solution,
            source="test",
        )
        self.assertEqual(added_again, 0)
        self.assertEqual(tree.stats.schedule_variant_route_pack_cache_hits, 1)

    def test_variant_route_pack_duplicate_cut_is_skipped(self):
        tree, routes, solution = self._variant_route_pack_fixture()
        node = BPCNode(0.0, 0, 0)
        added = tree._add_schedule_variant_route_pack_conflict_cuts(
            node,
            source_vehicle=1,
            routes=[routes[(1, 2)], routes[(3, 4)]],
            solution=solution,
            source="test",
        )
        self.assertEqual(added, 1)
        added_again = tree._add_schedule_variant_route_pack_conflict_cuts(
            node,
            source_vehicle=1,
            routes=[routes[(1, 2)], routes[(3, 4)]],
            solution=solution,
            source="test",
        )
        self.assertEqual(added_again, 0)
        self.assertEqual(tree.stats.schedule_variant_route_pack_duplicate_skips, 1)

    def test_variant_route_pack_roi_same_pool_replacement_adds_cut(self):
        tree, routes, _solution = self._variant_route_pack_fixture()
        solution = RMPSolution(
            status="optimal",
            objective=0.0,
            duals=None,
            artificial_sum=0.0,
            route_values=[(routes[(2, 1)], 1, 1.0), (routes[(4, 3)], 1, 1.0)],
            y_values={1: 1.0, 2: 1.0},
            variable_count=0,
            constraint_count=0,
        )
        diagnostics = {
            "classification": "same_pool_degeneracy",
            "low_improvement": True,
            "vehicles": [1],
            "cut_core_signatures": [[1, 2], [3, 4]],
            "same_pool_replacement_signatures": [[2, 1], [4, 3]],
        }
        added = tree._add_schedule_variant_route_pack_roi_cuts(
            BPCNode(0.0, 0, 0),
            solution,
            diagnostics,
            source="test_roi",
        )
        self.assertEqual(added, 1)
        self.assertEqual(tree.stats.schedule_variant_route_pack_cuts_added, 1)
        self.assertEqual(tree.cuts[0].vehicle, 1)
        self.assertEqual(set(tree.cuts[0].signatures), {(1, 2), (2, 1), (3, 4), (4, 3)})

    def test_schedule_capacity_oracle_exact_for_small_subset(self):
        data = load_bpc_data("very_small")
        result = exact_schedule_task_capacity(data, tuple(data.tasks[:3]), max_states=100000)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertTrue(result.exact)
        self.assertGreaterEqual(result.upper_bound, 1)
        self.assertLessEqual(result.upper_bound, 3)

    def test_schedule_subset_cost_oracle_exact_for_small_subset(self):
        instance = {
            "name": "schedule_subset_cost_smoke",
            "tasks": {
                "1": {"r": 0, "D": 100, "sigma": 0, "d": 1, "g": 0, "c_srv": 1},
                "2": {"r": 0, "D": 100, "sigma": 0, "d": 1, "g": 0, "c_srv": 1},
            },
        }
        pairwise = {
            "0->0": {"tau": 0, "energy": 0, "cost": 0, "path": []},
            "1->1": {"tau": 0, "energy": 0, "cost": 0, "path": []},
            "2->2": {"tau": 0, "energy": 0, "cost": 0, "path": []},
            "0->1": {"tau": 2, "energy": 0, "cost": 2, "path": []},
            "1->2": {"tau": 3, "energy": 0, "cost": 3, "path": []},
            "2->0": {"tau": 4, "energy": 0, "cost": 4, "path": []},
            "0->2": {"tau": 5, "energy": 0, "cost": 5, "path": []},
            "2->1": {"tau": 3, "energy": 0, "cost": 3, "path": []},
            "1->0": {"tau": 2, "energy": 0, "cost": 2, "path": []},
        }
        data = BPCData(
            instance=instance,
            pairwise=pairwise,
            instance_path=Path("synthetic"),
            name="schedule_subset_cost_smoke",
            tasks=(1, 2),
            vehicles=(1,),
            sortie_limit=2,
            capacity=10,
            energy_limit=10,
            rho=1,
            fixed_vehicle_cost=100,
            horizon=100,
        )
        result = exact_schedule_subset_cost(data, (1, 2), max_states=100000)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertTrue(result.exact)
        self.assertTrue(result.feasible)
        self.assertEqual(result.lower_bound, 11.0)

    def test_schedule_subset_cost_separator_adds_violated_cut(self):
        instance = {
            "name": "schedule_subset_cost_separator_smoke",
            "tasks": {
                "1": {"r": 0, "D": 100, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "2": {"r": 0, "D": 100, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
            },
        }
        pairwise = {
            "0->0": {"tau": 0, "energy": 0, "cost": 0, "path": []},
            "1->1": {"tau": 0, "energy": 0, "cost": 0, "path": []},
            "2->2": {"tau": 0, "energy": 0, "cost": 0, "path": []},
            "0->1": {"tau": 1, "energy": 0, "cost": 1, "path": []},
            "1->0": {"tau": 1, "energy": 0, "cost": 1, "path": []},
            "0->2": {"tau": 1, "energy": 0, "cost": 1, "path": []},
            "2->0": {"tau": 1, "energy": 0, "cost": 1, "path": []},
            "1->2": {"tau": 10, "energy": 0, "cost": 10, "path": []},
            "2->1": {"tau": 10, "energy": 0, "cost": 10, "path": []},
        }
        data = BPCData(
            instance=instance,
            pairwise=pairwise,
            instance_path=Path("synthetic"),
            name="schedule_subset_cost_separator_smoke",
            tasks=(1, 2),
            vehicles=(1,),
            sortie_limit=1,
            capacity=10,
            energy_limit=100,
            rho=1,
            fixed_vehicle_cost=100,
            horizon=100,
        )
        routes = [evaluate_route(data, (1,)), evaluate_route(data, (2,))]
        self.assertTrue(all(route is not None for route in routes))
        routes = [route for route in routes if route is not None]
        solution = RMPSolution(
            status="optimal",
            objective=0.0,
            duals=None,
            artificial_sum=0.0,
            route_values=[(route, 1, 1.0) for route in routes],
            y_values={1: 1.0},
            variable_count=0,
            constraint_count=0,
        )
        tree = CleanBPCTree(
            data,
            time_limit=10,
            max_nodes=10,
            eps=1.0e-6,
            integer_tol=1.0e-6,
            max_routes_per_pricing=10,
            max_labels_per_pricing=0,
            rmp_params={},
            logger=BPCLogger(None, console=False),
            schedule_subset_cost_cuts_enabled=True,
            schedule_subset_cost_cut_max_subset_size=2,
            schedule_subset_cost_cut_min_violation=0.05,
        )
        added = tree._separate_schedule_subset_cost_cuts(BPCNode(0.0, 0, 0), solution)
        self.assertEqual(added, 1)
        self.assertIsInstance(tree.cuts[0], ScheduleSubsetCostLowerBoundCut)
        self.assertEqual(tree.cuts[0].tasks, (1, 2))
        self.assertEqual(tree.stats.schedule_subset_cost_cuts_added, 1)

    def test_schedule_capacity_conflict_cut_from_infeasible_routes(self):
        instance = {
            "name": "schedule_capacity_conflict_smoke",
            "tasks": {
                "1": {"r": 0, "D": 2, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "2": {"r": 0, "D": 2, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "3": {"r": 0, "D": 2, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
            },
        }
        pairwise = {}
        for i in (0, 1, 2, 3):
            for j in (0, 1, 2, 3):
                if i == j:
                    tau = 0
                elif i == 0 or j == 0:
                    tau = 1
                else:
                    tau = 3
                pairwise[f"{i}->{j}"] = {"tau": tau, "energy": 0, "cost": tau, "path": []}
        data = BPCData(
            instance=instance,
            pairwise=pairwise,
            instance_path=Path("synthetic"),
            name="schedule_capacity_conflict_smoke",
            tasks=(1, 2, 3),
            vehicles=(1, 2),
            sortie_limit=3,
            capacity=10,
            energy_limit=10,
            rho=1,
            fixed_vehicle_cost=100,
            horizon=10,
        )
        routes = [evaluate_route(data, (task,)) for task in data.tasks]
        self.assertTrue(all(route is not None for route in routes))
        routes = [route for route in routes if route is not None]

        conflict = find_schedule_capacity_conflict(data, routes, max_subset_size=3, max_states=100000)
        self.assertIsNotNone(conflict)
        assert conflict is not None
        self.assertEqual(conflict.tasks, (1, 2, 3))
        self.assertEqual(conflict.upper_bound, 1)

        tree = CleanBPCTree(
            data,
            time_limit=10,
            max_nodes=10,
            eps=1.0e-6,
            integer_tol=1.0e-6,
            max_routes_per_pricing=10,
            max_labels_per_pricing=0,
            rmp_params={},
            logger=BPCLogger(None, console=False),
            schedule_capacity_cuts_enabled=True,
            schedule_capacity_cut_max_subset_size=3,
        )
        added = tree._add_schedule_capacity_conflict_cuts(
            BPCNode(0.0, 0, 0),
            source_vehicle=1,
            routes=routes,
        )
        self.assertEqual(added, len(data.vehicles))
        self.assertTrue(all(isinstance(cut, ScheduleCapacityCut) for cut in tree.cuts))
        self.assertTrue(all(getattr(cut, "source", "") == "schedule_conflict" for cut in tree.cuts))

    def test_schedule_pair_conflict_witness_and_cut(self):
        instance = {
            "name": "schedule_pair_conflict_smoke",
            "tasks": {
                "1": {"r": 0, "D": 2, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "2": {"r": 0, "D": 2, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
            },
        }
        pairwise = {
            f"{i}->{j}": {"tau": 0 if i == j else 1, "energy": 0, "cost": 0 if i == j else 1, "path": []}
            for i in (0, 1, 2)
            for j in (0, 1, 2)
        }
        data = BPCData(
            instance=instance,
            pairwise=pairwise,
            instance_path=Path("synthetic"),
            name="schedule_pair_conflict_smoke",
            tasks=(1, 2),
            vehicles=(1, 2),
            sortie_limit=2,
            capacity=10,
            energy_limit=10,
            rho=1,
            fixed_vehicle_cost=100,
            horizon=5,
        )
        routes = [evaluate_route(data, (1,)), evaluate_route(data, (2,))]
        self.assertTrue(all(route is not None for route in routes))
        routes = [route for route in routes if route is not None]

        witness = diagnose_route_set_schedule(data, routes)
        self.assertIsNotNone(witness)
        assert witness is not None
        self.assertEqual(witness.reason, "pair_transition")
        self.assertEqual(len(witness.pair_conflicts), 1)

        tree = CleanBPCTree(
            data,
            time_limit=10,
            max_nodes=10,
            eps=1.0e-6,
            integer_tol=1.0e-6,
            max_routes_per_pricing=10,
            max_labels_per_pricing=0,
            rmp_params={},
            logger=BPCLogger(None, console=False),
        )
        added = tree._add_schedule_pair_conflict_cuts(
            BPCNode(0.0, 0, 0),
            source_vehicle=1,
            pair_conflicts=witness.pair_conflicts,
        )
        self.assertEqual(added, len(data.vehicles))
        self.assertTrue(all(isinstance(cut, ScheduleNoGoodCut) for cut in tree.cuts))
        self.assertTrue(all(cut.kind == "schedule_pair_conflict" for cut in tree.cuts))

    def test_schedule_incompatibility_separator_adds_clique_cut(self):
        instance = {
            "name": "schedule_incompatibility_clique_smoke",
            "tasks": {
                "1": {"r": 0, "D": 2, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "2": {"r": 0, "D": 2, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "3": {"r": 0, "D": 2, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
            },
        }
        pairwise = {}
        for i in (0, 1, 2, 3):
            for j in (0, 1, 2, 3):
                if i == j:
                    tau = 0
                elif i == 0 or j == 0:
                    tau = 1
                else:
                    tau = 3
                pairwise[f"{i}->{j}"] = {"tau": tau, "energy": 0, "cost": tau, "path": []}
        data = BPCData(
            instance=instance,
            pairwise=pairwise,
            instance_path=Path("synthetic"),
            name="schedule_incompatibility_clique_smoke",
            tasks=(1, 2, 3),
            vehicles=(1,),
            sortie_limit=3,
            capacity=10,
            energy_limit=10,
            rho=1,
            fixed_vehicle_cost=100,
            horizon=10,
        )
        routes = [evaluate_route(data, (task,)) for task in data.tasks]
        self.assertTrue(all(route is not None for route in routes))
        routes = [route for route in routes if route is not None]
        solution = RMPSolution(
            status="optimal",
            objective=0.0,
            duals=None,
            artificial_sum=0.0,
            route_values=[(route, 1, 0.25) for route in routes],
            y_values={1: 0.6},
            variable_count=0,
            constraint_count=0,
        )
        tree = CleanBPCTree(
            data,
            time_limit=10,
            max_nodes=10,
            eps=1.0e-6,
            integer_tol=1.0e-6,
            max_routes_per_pricing=10,
            max_labels_per_pricing=0,
            rmp_params={},
            logger=BPCLogger(None, console=False),
            schedule_incompatibility_cuts_enabled=True,
            schedule_incompatibility_cut_max_support_routes=10,
            schedule_incompatibility_cut_min_violation=0.05,
        )
        added = tree._separate_schedule_incompatibility_cuts(BPCNode(0.0, 0, 0), solution)
        self.assertEqual(added, 1)
        self.assertEqual(tree.cuts[0].kind, "schedule_clique_conflict")
        self.assertEqual(tree.cuts[0].rhs, 0.0)
        self.assertEqual(tree.cuts[0].upper_bound, 1.0)
        self.assertEqual(tree.cuts[0].y_coefficient(1), -1.0)

    def test_rmp_has_task_vehicle_linking_duals(self):
        try:
            import pyscipopt  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("当前 Python 环境没有 PySCIPOpt")

        data = load_bpc_data("very_small")
        routes = [evaluate_route(data, (task,)) for task in data.tasks]
        self.assertTrue(all(route is not None for route in routes))
        solution = solve_rmp_lp(
            data,
            [route for route in routes if route is not None],
            cuts=[],
            branch_constraints=tuple(),
            phase="phase1",
            rmp_params={"display/verblevel": 0, "presolving/maxrounds": 0, "separating/maxrounds": 0},
            verbose=False,
        )
        self.assertTrue(solution.optimal)
        self.assertIsNotNone(solution.duals)
        assert solution.duals is not None
        self.assertEqual(len(solution.duals.task_vehicle), len(data.tasks) * len(data.vehicles))

    def test_rmp_can_disable_task_vehicle_linking_for_ablation(self):
        try:
            import pyscipopt  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("当前 Python 环境没有 PySCIPOpt")

        data = load_bpc_data("very_small")
        routes = [evaluate_route(data, (task,)) for task in data.tasks]
        solution = solve_rmp_lp(
            data,
            [route for route in routes if route is not None],
            cuts=[],
            branch_constraints=tuple(),
            phase="phase1",
            rmp_params={"display/verblevel": 0, "presolving/maxrounds": 0, "separating/maxrounds": 0},
            verbose=False,
            task_vehicle_linking_enabled=False,
        )
        self.assertTrue(solution.optimal)
        self.assertIsNotNone(solution.duals)
        assert solution.duals is not None
        self.assertEqual(solution.duals.task_vehicle, {})

    def _very_small_singleton_routes(self):
        data = load_bpc_data("very_small")
        routes = [evaluate_route(data, (task,)) for task in data.tasks]
        self.assertTrue(all(route is not None for route in routes))
        return data, [route for route in routes if route is not None]

    def _first_pair_route(self, data):
        for left in data.tasks:
            for right in data.tasks:
                if left == right:
                    continue
                route = evaluate_route(data, (left, right))
                if route is not None:
                    return route
        self.fail("expected at least one feasible pair route")

    def _assert_lambda_reduced_cost_formula(
        self,
        data: BPCData,
        routes,
        cuts,
        branch_constraints,
        phase: str,
        solution: RMPSolution,
    ) -> None:
        self.assertIsNotNone(solution.duals)
        self.assertIsNotNone(solution.lambda_reduced_costs)
        assert solution.duals is not None
        assert solution.lambda_reduced_costs is not None
        for (route_index, route_vehicle), solver_reduced_cost in solution.lambda_reduced_costs.items():
            formula_reduced_cost = reduced_cost(
                data,
                routes[route_index],
                route_vehicle,
                solution.duals,
                list(cuts),
                tuple(branch_constraints),
                phase=phase,
            )
            self.assertAlmostEqual(solver_reduced_cost, formula_reduced_cost, delta=1.0e-6)

    def _assert_rmp_close(
        self,
        persistent_solution: RMPSolution,
        rebuild_solution: RMPSolution,
        *,
        data: BPCData,
        routes,
        cuts,
        branch_constraints,
        phase: str,
    ) -> None:
        self.assertEqual(persistent_solution.status, rebuild_solution.status)
        self.assertEqual(persistent_solution.optimal, rebuild_solution.optimal)
        self.assertAlmostEqual(persistent_solution.objective or 0.0, rebuild_solution.objective or 0.0, delta=1.0e-6)
        self.assertAlmostEqual(persistent_solution.artificial_sum, rebuild_solution.artificial_sum, delta=1.0e-6)
        self.assertEqual(set(persistent_solution.y_values), set(rebuild_solution.y_values))
        for vehicle, value in persistent_solution.y_values.items():
            self.assertAlmostEqual(value, rebuild_solution.y_values[vehicle], delta=1.0e-6)
        self._assert_lambda_reduced_cost_formula(
            data,
            routes,
            cuts,
            branch_constraints,
            phase,
            persistent_solution,
        )

    def test_persistent_rmp_phase1_matches_rebuild(self):
        try:
            import pyscipopt  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("当前 Python 环境没有 PySCIPOpt")

        data, routes = self._very_small_singleton_routes()
        params = {"display/verblevel": 0, "presolving/maxrounds": 0, "separating/maxrounds": 0}
        persistent = PersistentRMP(data, routes, [], tuple(), phase="phase1", rmp_params=params)
        persistent_solution = persistent.solve(capture_lambda_reduced_costs=True)
        rebuild_solution = solve_rmp_lp(data, routes, [], tuple(), phase="phase1", rmp_params=params)
        self._assert_rmp_close(
            persistent_solution,
            rebuild_solution,
            data=data,
            routes=routes,
            cuts=[],
            branch_constraints=tuple(),
            phase="phase1",
        )

    def test_persistent_rmp_phase2_matches_rebuild(self):
        try:
            import pyscipopt  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("当前 Python 环境没有 PySCIPOpt")

        data, routes = self._very_small_singleton_routes()
        params = {"display/verblevel": 0, "presolving/maxrounds": 0, "separating/maxrounds": 0}
        persistent = PersistentRMP(data, routes, [], tuple(), phase="phase2", rmp_params=params)
        persistent_solution = persistent.solve(capture_lambda_reduced_costs=True)
        rebuild_solution = solve_rmp_lp(data, routes, [], tuple(), phase="phase2", rmp_params=params)
        self._assert_rmp_close(
            persistent_solution,
            rebuild_solution,
            data=data,
            routes=routes,
            cuts=[],
            branch_constraints=tuple(),
            phase="phase2",
        )

    def test_persistent_rmp_incremental_route_matches_rebuild(self):
        try:
            import pyscipopt  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("当前 Python 环境没有 PySCIPOpt")

        data, routes = self._very_small_singleton_routes()
        pair_route = self._first_pair_route(data)
        params = {"display/verblevel": 0, "presolving/maxrounds": 0, "separating/maxrounds": 0}
        persistent = PersistentRMP(data, routes, [], tuple(), phase="phase2", rmp_params=params)
        persistent.solve()
        extended_routes = [*routes, pair_route]
        persistent.sync(extended_routes, [])
        persistent_solution = persistent.solve(capture_lambda_reduced_costs=True)
        rebuild_solution = solve_rmp_lp(data, extended_routes, [], tuple(), phase="phase2", rmp_params=params)
        self._assert_rmp_close(
            persistent_solution,
            rebuild_solution,
            data=data,
            routes=extended_routes,
            cuts=[],
            branch_constraints=tuple(),
            phase="phase2",
        )

    def test_persistent_rmp_incremental_cut_matches_rebuild(self):
        try:
            import pyscipopt  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("当前 Python 环境没有 PySCIPOpt")

        data, routes = self._very_small_singleton_routes()
        pair_route = self._first_pair_route(data)
        routes = [*routes, pair_route]
        vehicle = data.vehicles[0]
        cut = ScheduleCapacityCut(
            id=777,
            vehicle=vehicle,
            tasks=tuple(sorted(pair_route.tasks)),
            upper_bound=len(pair_route.tasks),
            oracle_states=1,
        )
        params = {"display/verblevel": 0, "presolving/maxrounds": 0, "separating/maxrounds": 0}
        persistent = PersistentRMP(data, routes, [], tuple(), phase="phase2", rmp_params=params)
        persistent.solve()
        persistent.sync(routes, [cut])
        persistent_solution = persistent.solve(capture_lambda_reduced_costs=True)
        rebuild_solution = solve_rmp_lp(data, routes, [cut], tuple(), phase="phase2", rmp_params=params)
        self._assert_rmp_close(
            persistent_solution,
            rebuild_solution,
            data=data,
            routes=routes,
            cuts=[cut],
            branch_constraints=tuple(),
            phase="phase2",
        )

    def test_persistent_rmp_lambda_reduced_cost_matches_formula(self):
        try:
            import pyscipopt  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("当前 Python 环境没有 PySCIPOpt")

        data, singleton_routes = self._very_small_singleton_routes()
        pair_route = self._first_pair_route(data)
        pool = RoutePool()
        for route in singleton_routes:
            pool.add(route)
        pool.add(pair_route)
        routes = pool.routes
        vehicle = data.vehicles[0]
        cuts = [
            ScheduleCapacityCut(
                id=0,
                vehicle=vehicle,
                tasks=tuple(sorted(pair_route.tasks)),
                upper_bound=len(pair_route.tasks),
                oracle_states=1,
            ),
            SubsetRowCut(id=1, tasks=tuple(sorted(pair_route.tasks)), divisor=2),
        ]
        branch_constraints = (BranchConstraint("arc_on", pair_route.tasks[0], pair_route.tasks[1]),)
        params = {"display/verblevel": 0, "presolving/maxrounds": 0, "separating/maxrounds": 0}
        persistent = PersistentRMP(data, routes, cuts, branch_constraints, phase="phase2", rmp_params=params)
        solution = persistent.solve(capture_lambda_reduced_costs=True)
        self.assertTrue(solution.optimal)
        self._assert_lambda_reduced_cost_formula(data, routes, cuts, branch_constraints, "phase2", solution)

    def test_very_small_persistent_rmp_enabled_optimal(self):
        try:
            import pyscipopt  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("当前 Python 环境没有 PySCIPOpt")

        data = load_bpc_data("very_small")
        result = solve_bpc_clean(
            data,
            time_limit=30,
            max_nodes=200,
            pricing_eps=1.0e-6,
            integer_tol=1.0e-6,
            max_routes_per_pricing=200,
            max_labels_per_pricing=0,
            rmp_params={"display/verblevel": 0, "presolving/maxrounds": 0, "separating/maxrounds": 0},
            log_path=None,
            solution_path=None,
            seed=None,
            quiet=True,
            persistent_rmp_enabled=True,
        )
        self.assertEqual(result.status, "OPTIMAL")
        self.assertAlmostEqual(result.primal_bound or 0.0, 132.270984, delta=1.0e-6)
        self.assertAlmostEqual(result.gap or 0.0, 0.0, delta=1.0e-9)

    def test_restricted_integer_master_rejects_schedule_infeasible_assignment(self):
        try:
            import pyscipopt  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("当前 Python 环境没有 PySCIPOpt")

        instance = {
            "name": "rim_conflict_smoke",
            "tasks": {
                "1": {"r": 0, "D": 2, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "2": {"r": 0, "D": 2, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
            },
        }
        pairwise = {
            f"{i}->{j}": {"tau": 0 if i == j else 1, "energy": 0, "cost": 0 if i == j else 1, "path": []}
            for i in (0, 1, 2)
            for j in (0, 1, 2)
        }
        data = BPCData(
            instance=instance,
            pairwise=pairwise,
            instance_path=Path("synthetic"),
            name="rim_conflict_smoke",
            tasks=(1, 2),
            vehicles=(1,),
            sortie_limit=2,
            capacity=10,
            energy_limit=10,
            rho=1,
            fixed_vehicle_cost=100,
            horizon=5,
        )
        routes = [evaluate_route(data, (1,)), evaluate_route(data, (2,))]
        self.assertTrue(all(route is not None for route in routes))
        result = solve_restricted_integer_master(
            data,
            [route for route in routes if route is not None],
            cuts=[],
            branch_constraints=tuple(),
            time_limit=5,
            schedule_aware=True,
            max_no_good_rounds=3,
        )
        self.assertIsNone(result.objective)
        self.assertEqual(result.raw_objective, 104.0)
        self.assertEqual(result.rejected_solutions, 1)
        self.assertEqual(result.pair_conflict_cuts, 1)
        self.assertEqual(result.no_good_cuts, 0)
        self.assertEqual(len(result.rejected_conflicts), 1)

    def test_restricted_integer_master_applies_temporary_nogood_to_all_vehicles(self):
        try:
            import pyscipopt  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("当前 Python 环境没有 PySCIPOpt")

        instance = {
            "name": "rim_two_vehicle_conflict_smoke",
            "tasks": {
                "1": {"r": 0, "D": 2, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "2": {"r": 0, "D": 2, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
            },
        }
        pairwise = {
            f"{i}->{j}": {"tau": 0 if i == j else 1, "energy": 0, "cost": 0 if i == j else 1, "path": []}
            for i in (0, 1, 2)
            for j in (0, 1, 2)
        }
        data = BPCData(
            instance=instance,
            pairwise=pairwise,
            instance_path=Path("synthetic"),
            name="rim_two_vehicle_conflict_smoke",
            tasks=(1, 2),
            vehicles=(1, 2),
            sortie_limit=2,
            capacity=10,
            energy_limit=10,
            rho=1,
            fixed_vehicle_cost=100,
            horizon=5,
        )
        routes = [evaluate_route(data, (1,)), evaluate_route(data, (2,))]
        self.assertTrue(all(route is not None for route in routes))
        result = solve_restricted_integer_master(
            data,
            [route for route in routes if route is not None],
            cuts=[],
            branch_constraints=tuple(),
            time_limit=5,
            schedule_aware=True,
            max_no_good_rounds=3,
        )
        self.assertEqual(result.status, "REPAIRED")
        self.assertEqual(result.objective, 204.0)
        self.assertEqual(result.raw_objective, 104.0)
        self.assertEqual(result.rejected_solutions, 1)
        self.assertEqual(result.repair_attempts, 1)
        self.assertEqual(result.repair_successes, 1)
        self.assertEqual(result.pair_conflict_cuts, 0)
        self.assertEqual(result.no_good_cuts, 0)
        self.assertEqual(len(result.rejected_conflicts), 0)

        pair_cut_result = solve_restricted_integer_master(
            data,
            [route for route in routes if route is not None],
            cuts=[],
            branch_constraints=tuple(),
            time_limit=5,
            schedule_aware=True,
            max_no_good_rounds=3,
            repair_enabled=False,
        )
        self.assertEqual(pair_cut_result.objective, 204.0)
        self.assertEqual(pair_cut_result.raw_objective, 104.0)
        self.assertEqual(pair_cut_result.rejected_solutions, 1)
        self.assertEqual(pair_cut_result.pair_conflict_cuts, 2)
        self.assertEqual(pair_cut_result.no_good_cuts, 0)
        self.assertEqual(len(pair_cut_result.rejected_conflicts), 1)

    def test_restricted_integer_master_prefers_route_pack_before_nogood(self):
        try:
            import pyscipopt  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("当前 Python 环境没有 PySCIPOpt")

        instance = {
            "name": "rim_route_pack_conflict_smoke",
            "tasks": {
                "1": {"r": 3, "D": 4, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "2": {"r": 3, "D": 4, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "3": {"r": 3, "D": 4, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
                "4": {"r": 3, "D": 4, "sigma": 0, "d": 1, "g": 0, "c_srv": 0},
            },
        }
        pairwise = {
            f"{i}->{j}": {"tau": 0 if i == j else 0.5, "energy": 0, "cost": 0 if i == j else 0.5, "path": []}
            for i in (0, 1, 2, 3, 4)
            for j in (0, 1, 2, 3, 4)
        }
        data = BPCData(
            instance=instance,
            pairwise=pairwise,
            instance_path=Path("synthetic"),
            name="rim_route_pack_conflict_smoke",
            tasks=(1, 2, 3, 4),
            vehicles=(1,),
            sortie_limit=4,
            capacity=10,
            energy_limit=10,
            rho=1,
            fixed_vehicle_cost=100,
            horizon=5,
        )
        routes = [evaluate_route(data, (task,)) for task in data.tasks]
        self.assertTrue(all(route is not None for route in routes))
        result = solve_restricted_integer_master(
            data,
            [route for route in routes if route is not None],
            cuts=[],
            branch_constraints=tuple(),
            time_limit=5,
            schedule_aware=True,
            max_no_good_rounds=3,
        )
        self.assertIsNone(result.objective)
        self.assertEqual(result.rejected_solutions, 1)
        self.assertEqual(result.pair_conflict_cuts, 0)
        self.assertEqual(result.route_set_packing_cuts, 1)
        self.assertEqual(result.no_good_cuts, 0)
        self.assertEqual(len(result.rejected_conflicts), 1)

    def test_analyze_bpc_logs_reports_timeout_certificate_and_hardness(self):
        records = [
            {"time": 0.0, "event": "start", "instance": "sample_hard", "initial_incumbent": 200.0},
            {"time": 1.0, "event": "incumbent", "node_id": 0, "objective": 180.0},
            {
                "time": 2.0,
                "event": "rmp",
                "node_id": 0,
                "depth": 0,
                "phase": "phase2",
                "objective": 120.0,
            },
            {
                "time": 3.0,
                "event": "pricing",
                "node_id": 0,
                "pricing_kind": "exact",
                "label_pops": 12000000,
                "generated_labels": 13000000,
                "best_reduced_cost": -1.0,
                "added_routes": 0,
                "certificate": True,
            },
            {
                "time": 4.0,
                "event": "restricted_integer_master",
                "node_id": 0,
                "rejected_solutions": 2,
                "pair_conflict_cuts": 1,
                "route_set_packing_cuts": 0,
                "schedule_capacity_cuts": 0,
                "no_good_cuts": 0,
            },
            {"time": 5.0, "event": "fathom", "node_id": 0, "reason": "time_limit_after_node_certificate"},
            {
                "time": 5.0,
                "event": "timeout_diagnostics",
                "timeout_pending_node_certified": True,
                "official_bound_available": False,
                "diagnostic_bound": 120.0,
            },
            {
                "time": 5.0,
                "event": "finish",
                "status": "TIME_LIMIT",
                "primal_bound": 180.0,
                "dual_bound": None,
                "diagnostic_dual_bound": 120.0,
                "diagnostic_gap": 0.333333,
                "root_relaxation": 120.0,
                "time_to_first_incumbent": 1.0,
                "time_to_best_incumbent": 1.0,
                "open_nodes_remaining": 1,
                "timeout_pending_node_certified": True,
                "official_bound_available": False,
            },
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.jsonl"
            path.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")
            summary = analyze_jsonl(path)
        self.assertTrue(summary["timeout_pending_node_certified"])
        self.assertFalse(summary["official_bound_available"])
        self.assertIn("proof-hard", summary["hardness_tags"])
        self.assertIn("schedule-conflict-hard", summary["hardness_tags"])

    def test_existing_lambda_reduced_cost_matches_solver(self):
        try:
            import pyscipopt  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("当前 Python 环境没有 PySCIPOpt")

        data = load_bpc_data("very_small")
        routes = [evaluate_route(data, (task,)) for task in data.tasks]
        self.assertTrue(all(route is not None for route in routes))
        pair_route = None
        for left in data.tasks:
            for right in data.tasks:
                if left == right:
                    continue
                pair_route = evaluate_route(data, (left, right))
                if pair_route is not None:
                    break
            if pair_route is not None:
                break
        self.assertIsNotNone(pair_route)
        assert pair_route is not None
        pool = RoutePool()
        for route in routes:
            if route is not None:
                pool.add(route)
        pool.add(pair_route)
        routes = pool.routes

        vehicle = data.vehicles[0]
        cuts = [
            ScheduleCapacityCut(
                id=0,
                vehicle=vehicle,
                tasks=tuple(sorted(pair_route.tasks)),
                upper_bound=len(pair_route.tasks),
                oracle_states=1,
            ),
            SubsetRowCut(id=1, tasks=tuple(sorted(pair_route.tasks)), divisor=2),
            LimitedMemoryRank1Cut(
                id=3,
                tasks=tuple(sorted(pair_route.tasks)),
                multipliers=tuple(2 if index == 0 else 1 for index, _task in enumerate(sorted(pair_route.tasks))),
                denominator=3,
                memory_tasks=(min(pair_route.tasks),),
            ),
            ScheduleSubsetCostLowerBoundCut(
                id=2,
                vehicle=vehicle,
                tasks=tuple(sorted(pair_route.tasks)),
                lower_bound=0.1,
                oracle_states=1,
            ),
        ]
        branch_constraints = (BranchConstraint("arc_on", pair_route.tasks[0], pair_route.tasks[1]),)
        solution = solve_rmp_lp(
            data,
            routes,
            cuts=cuts,
            branch_constraints=branch_constraints,
            phase="phase2",
            rmp_params={"display/verblevel": 0, "presolving/maxrounds": 0, "separating/maxrounds": 0},
            verbose=False,
            capture_lambda_reduced_costs=True,
        )
        self.assertTrue(solution.optimal)
        self.assertIsNotNone(solution.duals)
        self.assertIsNotNone(solution.lambda_reduced_costs)
        assert solution.duals is not None
        assert solution.lambda_reduced_costs is not None

        for (route_index, route_vehicle), solver_reduced_cost in solution.lambda_reduced_costs.items():
            formula_reduced_cost = reduced_cost(
                data,
                routes[route_index],
                route_vehicle,
                solution.duals,
                cuts,
                branch_constraints,
                phase="phase2",
            )
            self.assertAlmostEqual(
                solver_reduced_cost,
                formula_reduced_cost,
                delta=1.0e-6,
                msg=(
                    f"route_index={route_index}, vehicle={route_vehicle}, "
                    f"solver_rc={solver_reduced_cost}, formula_rc={formula_reduced_cost}"
                ),
            )

    def test_exact_pricing_matches_bruteforce_negative_routes(self):
        data = load_bpc_data("very_small")
        vehicle = data.vehicles[0]
        cuts = [
            CrossingCut(
                id=0,
                tasks=tuple(sorted(data.tasks[:2])),
                rhs=2.0,
                k_bound=1,
                capacity_bound=1,
                resource_bound=1,
                demand=sum(data.task_value(task, "d") for task in data.tasks[:2]),
                capacity=data.capacity,
            )
        ]
        branch_constraints = (
            BranchConstraint("ryan_together", data.tasks[0], data.tasks[1]),
            BranchConstraint("arc_on", data.tasks[0], data.tasks[1]),
        )
        duals = RMPDuals(
            cover={task: 15.0 + task for task in data.tasks},
            task_vehicle={(task, route_vehicle): 0.1 * task for task in data.tasks for route_vehicle in data.vehicles},
            sortie_count={route_vehicle: 0.0 for route_vehicle in data.vehicles},
            vehicle_time={route_vehicle: 0.0 for route_vehicle in data.vehicles},
            cuts={0: 0.75},
            branches={0: 0.0, 1: 0.5},
        )

        expected_best = None
        expected_negative: set[tuple[int, ...]] = set()
        for length in range(1, len(data.tasks) + 1):
            for sequence in permutations(data.tasks, length):
                route = evaluate_route(data, sequence)
                if route is None:
                    continue
                for route_vehicle in data.vehicles:
                    if not route_allowed_by_branch(route, route_vehicle, branch_constraints):
                        continue
                    rc = reduced_cost(data, route, route_vehicle, duals, cuts, branch_constraints, phase="phase2")
                    expected_best = rc if expected_best is None else min(expected_best, rc)
                    if rc < -1.0e-6:
                        expected_negative.add(route.signature)

        result = exact_pricing(
            data,
            routes=[],
            duals=duals,
            cuts=cuts,
            branch_constraints=branch_constraints,
            phase="phase2",
            eps=1.0e-6,
            max_routes_to_return=1000,
            max_labels=0,
            dominance_enabled=True,
        )
        self.assertTrue(result.exhausted)
        self.assertTrue(result.dominance_enabled)
        self.assertAlmostEqual(result.best_reduced_cost, expected_best, delta=1.0e-6)
        self.assertEqual({route.signature for route in result.routes}, expected_negative)

    def test_exact_pricing_matches_bruteforce_with_subset_and_cost_cuts(self):
        data = load_bpc_data("very_small")
        vehicle = data.vehicles[0]
        tasks = tuple(sorted(data.tasks[:3]))
        cuts = [
            SubsetRowCut(id=11, tasks=tasks, divisor=2),
            LimitedMemoryRank1Cut(
                id=13,
                tasks=tasks,
                multipliers=(2, 1, 1),
                denominator=3,
                memory_tasks=(tasks[0],),
            ),
            ScheduleSubsetCostLowerBoundCut(
                id=12,
                vehicle=vehicle,
                tasks=tasks,
                lower_bound=5.0,
                oracle_states=10,
            ),
        ]
        duals = RMPDuals(
            cover={task: 18.0 + 0.2 * task for task in data.tasks},
            task_vehicle={(task, route_vehicle): 0.05 * task for task in data.tasks for route_vehicle in data.vehicles},
            sortie_count={route_vehicle: 0.0 for route_vehicle in data.vehicles},
            vehicle_time={route_vehicle: 0.0 for route_vehicle in data.vehicles},
            cuts={11: 0.8, 12: 0.2, 13: 0.4},
            branches={},
        )

        expected_best = None
        expected_negative: set[tuple[int, ...]] = set()
        for length in range(1, len(data.tasks) + 1):
            for sequence in permutations(data.tasks, length):
                route = evaluate_route(data, sequence)
                if route is None:
                    continue
                for route_vehicle in data.vehicles:
                    rc = reduced_cost(data, route, route_vehicle, duals, cuts, tuple(), phase="phase2")
                    expected_best = rc if expected_best is None else min(expected_best, rc)
                    if rc < -1.0e-6:
                        expected_negative.add(route.signature)

        result = exact_pricing(
            data,
            routes=[],
            duals=duals,
            cuts=cuts,
            branch_constraints=tuple(),
            phase="phase2",
            eps=1.0e-6,
            max_routes_to_return=1000,
            max_labels=0,
            dominance_enabled=True,
        )
        self.assertTrue(result.exhausted)
        self.assertFalse(result.dominance_enabled)
        self.assertAlmostEqual(result.best_reduced_cost, expected_best, delta=1.0e-6)
        self.assertEqual({route.signature for route in result.routes}, expected_negative)

    def test_signature_cut_dominance_matches_bruteforce_negative_routes(self):
        data = load_bpc_data("very_small")
        vehicle = data.vehicles[0]
        signature = tuple(data.tasks[:2])
        route = evaluate_route(data, signature)
        if route is None:
            signature = tuple(reversed(signature))
            route = evaluate_route(data, signature)
        self.assertIsNotNone(route)
        assert route is not None
        cuts = [
            ScheduleNoGoodCut(
                id=7,
                vehicle=vehicle,
                signatures=(route.signature,),
                kind="schedule_pair_conflict",
            )
        ]
        duals = RMPDuals(
            cover={task: 12.0 + 0.25 * task for task in data.tasks},
            task_vehicle={(task, route_vehicle): 0.1 for task in data.tasks for route_vehicle in data.vehicles},
            sortie_count={route_vehicle: 0.0 for route_vehicle in data.vehicles},
            vehicle_time={route_vehicle: 0.0 for route_vehicle in data.vehicles},
            cuts={7: 4.0},
            branches={},
        )

        expected_best = None
        expected_negative: set[tuple[int, ...]] = set()
        for length in range(1, len(data.tasks) + 1):
            for sequence in permutations(data.tasks, length):
                candidate = evaluate_route(data, sequence)
                if candidate is None:
                    continue
                for route_vehicle in data.vehicles:
                    rc = reduced_cost(data, candidate, route_vehicle, duals, cuts, tuple(), phase="phase2")
                    expected_best = rc if expected_best is None else min(expected_best, rc)
                    if rc < -1.0e-6:
                        expected_negative.add(candidate.signature)

        result = exact_pricing(
            data,
            routes=[],
            duals=duals,
            cuts=cuts,
            branch_constraints=tuple(),
            phase="phase2",
            eps=1.0e-6,
            max_routes_to_return=1000,
            max_labels=0,
            dominance_enabled=True,
        )
        self.assertTrue(result.exhausted)
        self.assertTrue(result.dominance_enabled)
        self.assertAlmostEqual(result.best_reduced_cost, expected_best, delta=1.0e-6)
        self.assertEqual({route.signature for route in result.routes}, expected_negative)

    def test_ng_pricing_is_not_used_as_certificate(self):
        data = load_bpc_data("very_small")
        duals = RMPDuals(
            cover={task: 0.0 for task in data.tasks},
            task_vehicle={},
            sortie_count={vehicle: 0.0 for vehicle in data.vehicles},
            vehicle_time={vehicle: 0.0 for vehicle in data.vehicles},
            cuts={},
            branches={},
        )

        result = exact_pricing(
            data,
            routes=[],
            duals=duals,
            cuts=[],
            branch_constraints=tuple(),
            phase="phase2",
            eps=1.0e-6,
            max_routes_to_return=1000,
            max_labels=100000,
            dominance_enabled=True,
            ng_relaxation_enabled=True,
            ng_memory_size=2,
        )

        self.assertFalse(result.exhausted)
        self.assertTrue(result.ng_relaxation_enabled)
        self.assertEqual(result.ng_memory_size, 2)

    def test_route_enumeration_returns_near_zero_nonnegative_routes(self):
        data = load_bpc_data("very_small")
        duals = RMPDuals(
            cover={task: 0.0 for task in data.tasks},
            task_vehicle={},
            sortie_count={vehicle: 0.0 for vehicle in data.vehicles},
            vehicle_time={vehicle: 0.0 for vehicle in data.vehicles},
            cuts={},
            branches={},
        )

        result = exact_pricing(
            data,
            routes=[],
            duals=duals,
            cuts=[],
            branch_constraints=tuple(),
            phase="phase2",
            eps=1.0e-6,
            max_routes_to_return=1000,
            max_labels=0,
            dominance_enabled=True,
            route_enumeration_rc_threshold=10_000.0,
            route_enumeration_max_routes=5,
        )

        self.assertTrue(result.exhausted)
        self.assertEqual(result.negative_routes, 0)
        self.assertGreater(result.enumerated_routes, 0)
        self.assertGreater(len(result.routes), 0)

    def test_very_small_solves_to_known_optimum(self):
        try:
            import pyscipopt  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("当前 Python 环境没有 PySCIPOpt")

        data = load_bpc_data("very_small")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = solve_bpc_clean(
                data,
                time_limit=20,
                max_nodes=200,
                pricing_eps=1.0e-6,
                integer_tol=1.0e-6,
                max_routes_per_pricing=200,
                max_labels_per_pricing=0,
                rmp_params={"display/verblevel": 0, "presolving/maxrounds": 0, "separating/maxrounds": 0},
                log_path=root / "clean.jsonl",
                solution_path=root / "solution.json",
                seed=20260511,
                quiet=True,
            )
        self.assertEqual(result.status, "OPTIMAL")
        self.assertAlmostEqual(result.primal_bound, 132.270984, places=5)
        self.assertEqual(result.gap, 0.0)

    def test_very_small_task_schedule_capacity_small_budget_same_optimum(self):
        try:
            import pyscipopt  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("当前 Python 环境没有 PySCIPOpt")

        data = load_bpc_data("very_small")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = solve_bpc_clean(
                data,
                time_limit=20,
                max_nodes=200,
                pricing_eps=1.0e-6,
                integer_tol=1.0e-6,
                max_routes_per_pricing=200,
                max_labels_per_pricing=0,
                rmp_params={"display/verblevel": 0, "presolving/maxrounds": 0, "separating/maxrounds": 0},
                log_path=root / "clean_task_schedcap.jsonl",
                solution_path=root / "solution_task_schedcap.json",
                seed=20260511,
                quiet=True,
                task_schedule_capacity_cuts_enabled=True,
                task_schedule_capacity_pair_budget=4,
                task_schedule_capacity_triple_budget=2,
                task_schedule_capacity_small_set_budget=0,
                task_schedule_capacity_max_depth=0,
                task_schedule_capacity_node_time_budget=1.0,
                task_schedule_capacity_oracle_max_states=10000,
            )
        self.assertEqual(result.status, "OPTIMAL")
        self.assertAlmostEqual(result.primal_bound, 132.270984, places=5)
        self.assertEqual(result.gap, 0.0)

    def test_very_small_route_pool_restart_same_optimum(self):
        try:
            import pyscipopt  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("当前 Python 环境没有 PySCIPOpt")

        data = load_bpc_data("very_small")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = solve_bpc_clean(
                data,
                time_limit=20,
                max_nodes=200,
                pricing_eps=1.0e-6,
                integer_tol=1.0e-6,
                max_routes_per_pricing=200,
                max_labels_per_pricing=0,
                rmp_params={"display/verblevel": 0, "presolving/maxrounds": 0, "separating/maxrounds": 0},
                log_path=root / "clean_route_pool_restart.jsonl",
                solution_path=root / "solution_route_pool_restart.json",
                seed=20260511,
                quiet=True,
                route_pool_restart_enabled=True,
                route_pool_restart_max_routes=8,
                route_pool_restart_min_global_routes=8,
                route_pool_restart_max_routes_per_task_set=2,
                route_pool_restart_keep_recent_rounds=1,
            )
        self.assertEqual(result.status, "OPTIMAL")
        self.assertAlmostEqual(result.primal_bound, 132.270984, places=5)
        self.assertEqual(result.gap, 0.0)


if __name__ == "__main__":
    unittest.main()

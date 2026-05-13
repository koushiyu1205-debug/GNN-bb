"""中文摘要：本测试文件覆盖根目录 bpc/ clean BPC 的基础闭环。"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bpc.columns import RoutePool, evaluate_route
from bpc.branching import BranchConstraint, route_allowed_by_branch, route_branch_coefficient
from bpc.cuts import CrossingCut, ScheduleCapacityCut, capacity_route_lower_bound
from bpc.data import load_bpc_data
from bpc.pricing import reduced_cost
from bpc.rmp import solve_rmp_lp
from bpc.schedule_capacity import exact_schedule_task_capacity
from bpc.solver import solve_bpc_clean


class CleanBPCTests(unittest.TestCase):
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

    def test_schedule_capacity_oracle_exact_for_small_subset(self):
        data = load_bpc_data("very_small")
        result = exact_schedule_task_capacity(data, tuple(data.tasks[:3]), max_states=100000)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertTrue(result.exact)
        self.assertGreaterEqual(result.upper_bound, 1)
        self.assertLessEqual(result.upper_bound, 3)

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
            )
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


if __name__ == "__main__":
    unittest.main()

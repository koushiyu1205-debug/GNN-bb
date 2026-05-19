"""中文摘要：本测试文件覆盖根目录 bpc/ clean BPC 的基础闭环。"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from itertools import permutations

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bpc.columns import RoutePool, evaluate_route
from bpc.branching import BranchConstraint, route_allowed_by_branch, route_branch_coefficient
from bpc.cuts import CrossingCut, ScheduleCapacityCut, ScheduleNoGoodCut, capacity_route_lower_bound
from bpc.data import BPCData, load_bpc_data
from bpc.logger import BPCLogger
from bpc.node import BPCNode
from bpc.pricing import exact_pricing, reduced_cost
from bpc.rmp import RMPDuals, solve_restricted_integer_master, solve_rmp_lp
from bpc.schedule_capacity import exact_schedule_task_capacity, find_schedule_capacity_conflict
from bpc.solver import solve_bpc_clean
from bpc.tree import CleanBPCTree
from bpc.validation import diagnose_route_set_schedule


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
        self.assertEqual(result.objective, 204.0)
        self.assertEqual(result.raw_objective, 104.0)
        self.assertEqual(result.rejected_solutions, 1)
        self.assertEqual(result.pair_conflict_cuts, 2)
        self.assertEqual(result.no_good_cuts, 0)
        self.assertEqual(len(result.rejected_conflicts), 1)

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

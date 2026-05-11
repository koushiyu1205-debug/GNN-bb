"""中文摘要：本测试文件覆盖 no-ML 分支定价的路径评价、RMP/pricing 基本接口和小实例求解。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gnn_bb.bp.route_slot_branch_price import build_branch_price_model, evaluate_route
from gnn_bb.bp.schedule_branch_price import BranchConstraint, BranchPriceSolver, IntegratedPricingLabel, _branch_coefficient_for_route, evaluate_sequence
from gnn_bb.bp.vehicle_schedule_branch_price import build_branch_price_model as build_schedule_model
from gnn_bb.bp.vehicle_schedule_branch_price import evaluate_schedule
from gnn_bb.data.instances import build_instance_from_legacy
from gnn_bb.data.terrain import build_task_closure


class BPNoMLTests(unittest.TestCase):
    def test_evaluate_single_task_route(self):
        instance = build_instance_from_legacy("very_small")
        pairwise = build_task_closure(instance)
        route = evaluate_sequence(instance, pairwise, (1,))
        self.assertIsNotNone(route)
        self.assertEqual(route["tasks"], (1,))
        self.assertGreater(route["cycle_time"], 0.0)

    def test_route_slot_evaluate_single_task_route(self):
        instance = build_instance_from_legacy("very_small")
        pairwise = build_task_closure(instance)
        route = evaluate_route(instance, pairwise, [1])
        self.assertIsNotNone(route)
        self.assertEqual(route["tasks"], [1])
        self.assertGreater(route["cycle_time"], 0.0)

    def test_route_slot_pricer_model_builds(self):
        try:
            import pyscipopt  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("当前 Python 环境没有 PySCIPOpt")
        instance = build_instance_from_legacy("very_small")
        pairwise = build_task_closure(instance)
        model, pricer, data = build_branch_price_model(instance, pairwise, warm_start=True)
        self.assertGreater(model.getNVars(), 0)
        self.assertGreater(model.getNConss(), 0)
        self.assertGreater(len(pricer.columns), 0)
        self.assertEqual(len(data["tasks"]), 4)

    def test_vehicle_schedule_evaluates_true_sequence(self):
        instance = build_instance_from_legacy("very_small")
        pairwise = build_task_closure(instance)
        schedule = evaluate_schedule(instance, pairwise, ((1, 2), (3, 4)))
        self.assertIsNotNone(schedule)
        self.assertEqual(schedule["task_set"], [1, 2, 3, 4])
        self.assertGreater(schedule["ready_time"], 0.0)

    def test_vehicle_schedule_model_builds(self):
        try:
            import pyscipopt  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("当前 Python 环境没有 PySCIPOpt")
        instance = build_instance_from_legacy("very_small")
        pairwise = build_task_closure(instance)
        model, pricer, data = build_schedule_model(instance, pairwise, warm_start=True)
        self.assertGreater(model.getNVars(), 0)
        self.assertGreater(model.getNConss(), 0)
        self.assertGreater(len(pricer.schedules), 0)
        self.assertEqual(len(data["tasks"]), 4)

    def test_initial_rmp_builds(self):
        try:
            import pyscipopt  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("当前 Python 环境没有 PySCIPOpt")
        instance = build_instance_from_legacy("very_small")
        pairwise = build_task_closure(instance)
        solver = BranchPriceSolver(instance, pairwise, time_limit=5, max_nodes=1, log_level="quiet")
        solver.initialize_columns()
        model, _ = solver._build_rmp(tuple())
        self.assertGreater(model.getNVars(), 0)
        self.assertGreater(model.getNConss(), 0)

    def test_ryan_foster_branch_coefficient(self):
        route = {"tasks": (1, 3), "task_set": frozenset({1, 3}), "arcs": ((0, 1), (1, 3), (3, 0))}
        together = BranchConstraint(kind="ryan_foster", sense=">=", rhs=1.0, pair=(1, 3))
        separate = BranchConstraint(kind="ryan_foster", sense="<=", rhs=0.0, pair=(1, 2))
        self.assertEqual(_branch_coefficient_for_route(route, together), 1.0)
        self.assertEqual(_branch_coefficient_for_route(route, separate), 0.0)

    def test_choose_branch_prefers_ryan_foster_pair(self):
        instance = build_instance_from_legacy("very_small")
        pairwise = build_task_closure(instance)
        solver = BranchPriceSolver(instance, pairwise, time_limit=5, max_nodes=1, log_level="quiet")
        route_data_a = {
            "tasks": (1, 2),
            "task_set": frozenset({1, 2}),
            "arcs": ((0, 1), (1, 2), (2, 0)),
            "cost": 1.0,
            "load": 1.0,
            "energy": 1.0,
            "return_time": 1.0,
            "travel_time": 1.0,
            "cycle_time": 1.0,
            "service_start": {},
        }
        route_data_b = {
            "tasks": (1, 3),
            "task_set": frozenset({1, 3}),
            "arcs": ((0, 1), (1, 3), (3, 0)),
            "cost": 1.0,
            "load": 1.0,
            "energy": 1.0,
            "return_time": 1.0,
            "travel_time": 1.0,
            "cycle_time": 1.0,
            "service_start": {},
        }
        route_a = solver.pool.add_route(route_data_a)
        route_b = solver.pool.add_route(route_data_b)
        solver.pool.add_schedule((route_a,), source="test")
        solver.pool.add_schedule((route_b,), source="test")
        values = {((1, 2),): 0.5, ((1, 3),): 0.5}

        left, right = solver._choose_branch(values)

        self.assertEqual(left.kind, "ryan_foster")
        self.assertEqual(right.kind, "ryan_foster")
        self.assertEqual(left.sense, "<=")
        self.assertEqual(right.sense, ">=")

    def test_route_total_branch_coefficient(self):
        route = {"tasks": (1, 2), "task_set": frozenset({1, 2}), "arcs": ((0, 1), (1, 2), (2, 0))}
        branch = BranchConstraint(kind="route_total", sense=">=", rhs=1.0, route_signature=(1, 2))
        self.assertEqual(_branch_coefficient_for_route(route, branch), 1.0)

    def test_schedule_label_dominance(self):
        instance = build_instance_from_legacy("very_small")
        pairwise = build_task_closure(instance)
        solver = BranchPriceSolver(instance, pairwise, time_limit=5, max_nodes=1, log_level="quiet")
        nondominated = {}
        better = IntegratedPricingLabel(
            priority=0.0,
            route_ids=(1,),
            task_set=frozenset({1, 2}),
            used_sorties=1,
            cycle_time=5.0,
            closed_reduced_cost=-3.0,
            current_node=0,
            route_tasks=tuple(),
            route_time=0.0,
            route_load=0.0,
            route_energy=0.0,
            route_cost=0.0,
            route_travel_time=0.0,
            route_reduced_cost=0.0,
        )
        worse = IntegratedPricingLabel(
            priority=0.0,
            route_ids=(2,),
            task_set=frozenset({1, 2}),
            used_sorties=2,
            cycle_time=7.0,
            closed_reduced_cost=-2.0,
            current_node=0,
            route_tasks=tuple(),
            route_time=0.0,
            route_load=0.0,
            route_energy=0.0,
            route_cost=0.0,
            route_travel_time=0.0,
            route_reduced_cost=0.0,
        )

        self.assertTrue(solver._record_integrated_label(better, nondominated, exact_route_order=False))
        self.assertFalse(solver._record_integrated_label(worse, nondominated, exact_route_order=False))

    def test_very_small_solves(self):
        try:
            import pyscipopt  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("当前 Python 环境没有 PySCIPOpt")
        instance = build_instance_from_legacy("very_small")
        pairwise = build_task_closure(instance)
        solver = BranchPriceSolver(instance, pairwise, time_limit=20, max_nodes=200, max_columns_per_pricing=100, log_level="quiet")
        result = solver.solve()
        self.assertEqual(result.status, "OPTIMAL")
        self.assertAlmostEqual(result.primal_bound, 132.270984, places=5)


if __name__ == "__main__":
    unittest.main()

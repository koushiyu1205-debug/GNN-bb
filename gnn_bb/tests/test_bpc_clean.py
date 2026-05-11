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

from bpc.columns import evaluate_route
from bpc.branching import BranchConstraint, route_allowed_by_branch, route_branch_coefficient
from bpc.data import load_bpc_data
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

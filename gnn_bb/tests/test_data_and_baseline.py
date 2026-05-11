"""中文摘要：本测试文件覆盖新实例读取、任务层闭包、compact MILP 构建和 baseline CSV 字段。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gnn_bb.baseline.scip_milp import BaselineResult, build_compact_milp
from gnn_bb.data.instances import (
    SCALABLE_VEHICLE_PHYSICAL_PARAMETERS,
    build_instance_from_legacy,
    load_or_build_instance,
    scalable_task_parameters,
    scalable_vehicle_parameters,
    task_ids,
    validate_instance_schema,
)
from gnn_bb.data.terrain import arc_key, build_task_closure


class DataAndBaselineTests(unittest.TestCase):
    def test_instance_schema(self):
        instance = build_instance_from_legacy("very_small")
        validate_instance_schema(instance)
        self.assertEqual(instance["name"], "very_small")
        self.assertEqual(len(task_ids(instance)), 4)

    def test_task_closure_dimension(self):
        instance = build_instance_from_legacy("very_small")
        pairwise = build_task_closure(instance)
        node_count = len(task_ids(instance)) + 1
        self.assertEqual(len(pairwise), node_count * (node_count - 1))
        self.assertIn(arc_key(0, 1), pairwise)
        self.assertIn("tau", pairwise[arc_key(0, 1)])

    def test_compact_milp_builds(self):
        try:
            import pyscipopt  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("当前 Python 环境没有 PySCIPOpt")
        instance = build_instance_from_legacy("very_small")
        pairwise = build_task_closure(instance)
        model, data = build_compact_milp(instance, pairwise, time_limit=1, verbose=False)
        self.assertGreater(model.getNVars(), 0)
        self.assertGreater(model.getNConss(), 0)
        self.assertEqual(len(data["tasks"]), 4)

    def test_baseline_csv_fields(self):
        fields = set(BaselineResult.__dataclass_fields__)
        for required in ("instance", "status", "primal_bound", "dual_bound", "gap", "solving_time", "node_count"):
            self.assertIn(required, fields)

    def test_medium_and_30_use_scaling_policy(self):
        medium, _ = load_or_build_instance("medium", write_if_missing=False)
        instance_30, _ = load_or_build_instance("30", write_if_missing=False)
        medium_vehicles, medium_metadata = scalable_vehicle_parameters(medium)
        vehicles_30, metadata_30 = scalable_vehicle_parameters(instance_30)
        self.assertEqual(medium["vehicles"], medium_vehicles)
        self.assertEqual(instance_30["vehicles"], vehicles_30)
        self.assertGreaterEqual(medium["vehicles"]["S_bar"], 1)
        self.assertGreaterEqual(instance_30["vehicles"]["S_bar"], 1)
        self.assertGreaterEqual(medium["vehicles"]["R_bar"], 1)
        self.assertGreaterEqual(instance_30["vehicles"]["R_bar"], 1)
        self.assertEqual(medium["scaling_policy"]["s_bar_formula"], medium_metadata["s_bar_formula"])
        self.assertEqual(instance_30["scaling_policy"]["s_bar_formula"], metadata_30["s_bar_formula"])
        for key, value in SCALABLE_VEHICLE_PHYSICAL_PARAMETERS.items():
            self.assertEqual(medium["vehicles"][key], value)
            self.assertEqual(instance_30["vehicles"][key], value)
        for task_id in (1, 2, 3, 10, 20):
            expected = scalable_task_parameters(task_id)
            self.assertEqual({key: medium["tasks"][str(task_id)][key] for key in expected}, expected)
            self.assertEqual({key: instance_30["tasks"][str(task_id)][key] for key in expected}, expected)


if __name__ == "__main__":
    unittest.main()

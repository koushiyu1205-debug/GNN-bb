from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_seed61635_formulation_contract_gate import (
    build_seed61635_formulation_contract_gate,
)


class Seed61635FormulationContractGateTests(unittest.TestCase):
    def test_builds_contract_gate_and_selects_route_order_design_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readiness = root / "readiness"
            readiness.mkdir()
            (readiness / "summary.json").write_text(
                json.dumps({"decision": "do_not_enter_live_cut"}, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            rows = [
                {
                    "family": "route_order_partition_formulation",
                    "observed_signal": True,
                    "partition_row_count": 2,
                    "partition_contract_holding_row_count": 2,
                    "max_child_rmp_objective_gain": 48.0,
                    "child_pricing_found_negative_row_count": 3,
                    "min_child_pricing_best_reduced_cost": -67.0,
                    "exact_pricing_supported": False,
                    "completion_bound_fail_closed": True,
                },
                {
                    "family": "route_resource_cut_audit",
                    "observed_signal": True,
                    "max_global_valid_candidate_count": 0,
                    "max_pricing_supported_candidate_count": 0,
                    "completion_bound_fail_closed": True,
                },
                {
                    "family": "weighted_rank1_task_subset",
                    "observed_signal": True,
                    "dual_moved_from_seed61635_plateau": False,
                },
            ]
            (readiness / "readiness_rows.jsonl").write_text(
                "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
                encoding="utf-8",
            )

            summary = build_seed61635_formulation_contract_gate(
                readiness,
                root / "out",
                root / "report.md",
            )

            self.assertEqual(summary["candidate_count"], 3)
            self.assertEqual(summary["live_ready_candidate_count"], 0)
            self.assertEqual(summary["selected_next_candidate"], "state_scoped_route_order_partition_branch")
            gate_rows = [
                json.loads(line)
                for line in (root / "out" / "contract_gate_rows.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            by_candidate = {row["candidate"]: row for row in gate_rows}
            self.assertTrue(
                by_candidate["state_scoped_route_order_partition_branch"]["selected_for_next_design"]
            )
            route_gates = {
                gate["name"]: gate["status"]
                for gate in by_candidate["state_scoped_route_order_partition_branch"]["gates"]
            }
            self.assertEqual(route_gates["state_scoped_partition_contract"], "pass")
            self.assertEqual(route_gates["child_pricing_pressure_cleared"], "fail")
            self.assertEqual(route_gates["direct_certificate_support"], "fail_closed")
            resource_gates = {
                gate["name"]: gate["status"]
                for gate in by_candidate["pricing_compatible_route_resource_row"]["gates"]
            }
            self.assertEqual(resource_gates["global_valid_row_family"], "fail")
            self.assertEqual(resource_gates["rmp_coefficient_defined"], "fail")
            self.assertIn("selected_next_candidate", (root / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.summarize_seed61635_formulation_cut_readiness import (
    summarize_seed61635_formulation_cut_readiness,
)


class Seed61635FormulationCutReadinessTests(unittest.TestCase):
    def test_summarizes_gate_matrix_without_live_ready_family(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            weighted = root / "weighted"
            route_resource = root / "route_resource"
            route_order = root / "route_order"
            _write_result(weighted)
            _write_result(route_resource)
            _write_result(route_order)
            _write_log(
                weighted,
                [
                    {"event": "journey_weighted_rank1_cut_separation", "best_violation": 0.25},
                    {"event": "journey_weighted_rank1_cut_added"},
                    {
                        "event": "journey_cut_dual_diagnostics",
                        "top_cuts": [{"kind": "weighted_subset_row", "dual": -3.0}],
                    },
                ],
            )
            _write_log(
                route_resource,
                [
                    {
                        "event": "journey_route_resource_cut_audit",
                        "order_direction_candidate_count": 2,
                        "adjacent_direction_candidate_count": 1,
                        "same_task_set_multi_route_candidate_count": 0,
                        "route_resource_global_valid_candidate_count": 0,
                        "route_resource_pricing_supported_candidate_count": 0,
                        "completion_bound_fail_closed": True,
                    }
                ],
            )
            _write_log(
                route_order,
                [
                    {
                        "event": "journey_route_order_partition_audit",
                        "exact_pricing_supported": False,
                        "completion_bound_fail_closed": True,
                        "top_partition_rows": [
                            {
                                "tasks": [12, 20],
                                "exact_safe_partition_contract_holds": True,
                                "child_rmp_probe_rows": [
                                    {"kind": "same_route_order_before_strict", "objective_gain": 48.0}
                                ],
                                "child_pricing_probe_rows": [
                                    {
                                        "kind": "same_route_order_before_strict",
                                        "best_reduced_cost": -67.0,
                                        "negative_journey_count": 1,
                                    }
                                ],
                            }
                        ],
                    }
                ],
            )

            summary = summarize_seed61635_formulation_cut_readiness(
                weighted_run=weighted,
                route_resource_run=route_resource,
                route_order_run=route_order,
                output_dir=root / "out",
                report=root / "report.md",
            )

            self.assertEqual(summary["row_count"], 3)
            self.assertEqual(summary["live_ready_family_count"], 0)
            self.assertTrue(summary["dual_plateau_holds_for_inputs"])
            rows = [
                json.loads(line)
                for line in (root / "out" / "readiness_rows.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            by_family = {row["family"]: row for row in rows}
            self.assertEqual(
                by_family["route_resource_cut_audit"]["primary_blocker"],
                "no_global_valid_or_pricing_supported_route_resource_row",
            )
            self.assertEqual(
                by_family["route_order_partition_formulation"]["child_pricing_found_negative_row_count"],
                1,
            )
            self.assertIn("Hard Gates Before Live Cut", (root / "report.md").read_text(encoding="utf-8"))


def _write_result(run_dir: Path) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "results.csv").write_text(
        "instance,status,primal_bound,dual_bound,gap,node_count,pricing_calls,exact_pricing_calls,columns,cuts_added,subset_row_cuts_added\n"
        "seed61635,TIME_LIMIT,561.030445,526.651393,0.061278,2,32,9,350,1,0\n",
        encoding="utf-8",
    )


def _write_log(run_dir: Path, rows: list[dict[str, object]]) -> None:
    log_path = run_dir / "logs" / "seed61635.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()

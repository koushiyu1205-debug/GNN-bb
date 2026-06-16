from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.build_gat_active_replacement_target_candidates import (
    build_active_replacement_target_candidates,
)


def _journey(tasks: list[int], *, rc: float) -> dict[str, object]:
    arcs = [f"0->{tasks[0]}:low_time:0", f"{tasks[-1]}->0:low_time:0"]
    return {
        "task_set": sorted(tasks),
        "signature": [[tasks, arcs, 10.0]],
        "true_reduced_cost": rc,
        "trips": [
            {
                "tasks": tasks,
                "start_time": 10.0,
                "arc_option_ids": arcs,
            }
        ],
    }


class GATActiveReplacementTargetCandidatesTests(unittest.TestCase):
    def test_extracts_active_replacement_and_replacement_controls(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            log_dir = tmp / "logs"
            output_dir = tmp / "out"
            report = tmp / "report.md"
            log_dir.mkdir()
            events = [
                {
                    "event": "journey_counterfactual_replay_capture",
                    "context_hash": "ctx",
                    "instance_path": "BPC_future/logical_graph/tasks_020/sector-wave/demo.json",
                    "task_count": 20,
                    "pricing_state": "FOUND_NEGATIVE",
                    "pricing_kind": "exact",
                    "cg_iter": 7,
                    "true_dual_hash": "dual",
                    "cut_hash": "cuts",
                    "branch_hash": "branch",
                    "forbidden_signature_hash": "forbidden",
                    "active_hash_before": "active",
                    "pool_signature_hash": "pool-signature",
                    "pool_task_set_hash": "pool-task-set",
                    "returned_journeys": [
                        _journey([4, 6], rc=-9.0),
                        _journey([9, 17], rc=-8.0),
                        _journey([1, 5], rc=-7.0),
                    ],
                },
                {
                    "event": "journey_column_addition",
                    "cg_iter": 7,
                    "pricing_kind": "exact",
                    "addition_productivity_class": "active_replacement_task_set",
                    "active_changed_task_set_count": 1,
                    "replacement_task_set_count": 2,
                    "active_changed_task_set_samples": [[4, 6]],
                    "replacement_task_set_samples": [[4, 6], [9, 17]],
                    "active_changed_task_set_samples_truncated": False,
                    "replacement_task_set_samples_truncated": False,
                },
            ]
            (log_dir / "run.jsonl").write_text(
                "\n".join(json.dumps(event) for event in events) + "\n",
                encoding="utf-8",
            )

            summary = build_active_replacement_target_candidates(
                log_dir=log_dir,
                output_dir=output_dir,
                report=report,
                max_active=4,
                max_replacement_controls=2,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["selector_can_certificate"])
            self.assertEqual(summary["capture_candidate_count"], 2)
            self.assertEqual(
                summary["selected_category_counts"],
                {"active_replacement": 1, "replacement_control": 1},
            )
            payload = json.loads((output_dir / "candidates.json").read_text(encoding="utf-8"))
            selected = payload["candidates"]
            self.assertEqual(selected[0]["selection_category"], "active_replacement")
            self.assertEqual(selected[0]["target_task_set"], [4, 6])
            self.assertEqual(selected[0]["target_sequence"], [4, 6])
            self.assertEqual(selected[1]["selection_category"], "replacement_control")
            self.assertEqual(selected[1]["target_task_set"], [9, 17])
            self.assertTrue(report.exists())


if __name__ == "__main__":
    unittest.main()

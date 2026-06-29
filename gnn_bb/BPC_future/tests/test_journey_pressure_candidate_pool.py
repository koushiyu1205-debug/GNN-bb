from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_journey_pressure_candidate_pool import (
    build_pressure_candidate_pool,
)


class JourneyPressureCandidatePoolTests(unittest.TestCase):
    def test_builds_uncovered_pressure_replay_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_dir = tmp_path / "logs" / "BPC_future" / "logical_graph" / "tasks_020" / "case"
            log_dir.mkdir(parents=True)
            log_path = log_dir / "case_randomtw_tasks020_03_seed3_logical_graph.json.jsonl"
            records = [
                {
                    "event": "journey_branch_candidates",
                    "node_id": 0,
                    "depth": 0,
                    "time": 12.5,
                    "priority_mode": "fractionality",
                    "candidate_count": 4,
                    "eligible_count": 4,
                    "selected": {"task_i": 1, "task_j": 2, "fractionality": 0.5},
                    "priority_top": [
                        {"task_i": 1, "task_j": 2, "fractionality": 0.5},
                        {
                            "task_i": 1,
                            "task_j": 3,
                            "fractionality": 0.49,
                            "phase2_negative_severity_sum": 3.0,
                            "phase2_negative_severity_gap": 3.0,
                            "phase2_negative_child_presence_balance_gap": 1,
                        },
                        {
                            "task_i": 1,
                            "task_j": 5,
                            "fractionality": 0.48,
                            "phase2_negative_severity_sum": 2.0,
                            "phase2_negative_severity_gap": 2.0,
                            "phase2_negative_child_presence_balance_gap": 1,
                        },
                        {
                            "task_i": 1,
                            "task_j": 6,
                            "fractionality": 0.47,
                            "phase2_negative_severity_sum": 0.0,
                        },
                    ],
                }
            ]
            log_path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )
            instance = (
                "BPC_future/logical_graph/tasks_020/case/"
                "case_randomtw_tasks020_03_seed3_logical_graph.json"
            )
            covered_dir = tmp_path / "covered"
            covered_dir.mkdir()
            (covered_dir / "branch_counterfactual_delta_rows.jsonl").write_text(
                json.dumps(
                    {
                        "instance": instance,
                        "node_id": 0,
                        "depth": 0,
                        "alternative_pair": [1, 3],
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = build_pressure_candidate_pool(
                [log_path],
                tmp_path / "pool",
                tmp_path / "report.md",
                covered_inputs=[covered_dir],
                candidate_source="both",
                max_queue=4,
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertEqual(summary["source_event_count"], 1)
            self.assertEqual(summary["candidate_row_count"], 2)
            self.assertEqual(summary["queue_row_count"], 1)
            self.assertEqual(summary["coverage_status_counts"]["delta_observed"], 1)
            self.assertEqual(summary["coverage_status_counts"]["uncovered"], 1)
            self.assertIn("--focus-candidate-input", summary["recommended_runbook_command"])

            pool_rows = [
                json.loads(line)
                for line in (tmp_path / "pool" / "candidate_pool.jsonl").read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
            queue_rows = [
                json.loads(line)
                for line in (tmp_path / "pool" / "replay_queue.jsonl").read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
            self.assertEqual([row["candidate_pair"] for row in pool_rows], [[1, 3], [1, 5]])
            self.assertEqual(queue_rows[0]["candidate_pair"], [1, 5])
            self.assertEqual(queue_rows[0]["coverage_status"], "uncovered")
            report = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("queue_row_count = 1", report)
            self.assertIn("candidate_pair = [1, 5]", report)


if __name__ == "__main__":
    unittest.main()

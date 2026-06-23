from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_journey_branch_tail_positive_runbook import build_runbook


class JourneyBranchTailPositiveRunbookTests(unittest.TestCase):
    def test_build_runbook_uses_root_near_positive_force_pair(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            positive_gap = tmp_path / "positive_gap.json"
            positive_gap.write_text(
                json.dumps(
                    {
                        "near_positive_rows": [
                            {
                                "source_type": "branch_impact",
                                "depth": 0,
                                "task_i": 2,
                                "task_j": 13,
                                "tail_class": "early_branch_continues",
                                "tail_badness_score": 58.0,
                                "y_child_negative_pricing_events": 5.0,
                                "log_file": (
                                    "BPC_future/results/probe/logs/"
                                    "BPC_future/logical_graph/tasks_020/greedy-anchor/"
                                    "demo_instance.json.jsonl"
                                ),
                            },
                            {
                                "source_type": "branch_impact",
                                "depth": 1,
                                "task_i": 2,
                                "task_j": 3,
                                "tail_class": "early_branch_continues",
                                "log_file": (
                                    "BPC_future/results/probe/logs/"
                                    "BPC_future/logical_graph/tasks_020/greedy-anchor/"
                                    "demo_instance.json.jsonl"
                                ),
                            },
                        ]
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            runbook = build_runbook(
                positive_gap,
                tmp_path / "out",
                tmp_path / "report.md",
                time_limit=123,
            )

            self.assertTrue(runbook["diagnostic_only"])
            self.assertFalse(runbook["runs_bpc_or_pricing"])
            self.assertEqual(
                runbook["base_sample_strategy"],
                "extend_existing_5000_with_branch_tail_interventions",
            )
            self.assertEqual(runbook["entry_count"], 1)
            entry = runbook["entries"][0]
            self.assertEqual(entry["forced_pair"], [2, 13])
            self.assertEqual(
                entry["instance"],
                "BPC_future/logical_graph/tasks_020/greedy-anchor/demo_instance.json",
            )
            self.assertIn("journey_branch_candidate_priority=force_pair:2,13", entry["command"])
            self.assertIn("--time-limit", entry["command"])
            self.assertIn("123", entry["command"])
            self.assertTrue((tmp_path / "out" / "runbook.json").exists())
            self.assertTrue((tmp_path / "out" / "commands.sh").exists())
            self.assertIn("certificate_effect = false", (tmp_path / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

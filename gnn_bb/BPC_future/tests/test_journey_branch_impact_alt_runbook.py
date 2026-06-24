from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_journey_branch_impact_alt_runbook import build_runbook


class JourneyBranchImpactAltRunbookTests(unittest.TestCase):
    def test_build_runbook_emits_root_priority_top_alternative(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            audit_dir = tmp_path / "audit"
            audit_dir.mkdir()
            log_path = (
                tmp_path
                / "logs"
                / "BPC_future"
                / "logical_graph"
                / "tasks_020"
                / "demo_instance.json.jsonl"
            )
            log_path.parent.mkdir(parents=True)
            log_path.write_text(
                json.dumps({"event": "journey_node_start", "node_id": 0, "depth": 0}) + "\n",
                encoding="utf-8",
            )
            row = {
                "branch_feature_source": "candidate_log",
                "branch_labels": {"y_completion_bound_tail": 1.0},
                "branch_node_id": 0,
                "depth": 0,
                "label_observation_complete": True,
                "log_file": str(log_path),
                "observed_branch_candidate": {"task_i": 1, "task_j": 2},
                "priority_top": [
                    {"task_i": 1, "task_j": 2, "pool_max_child_width": 30, "pool_total_child_width": 50},
                    {"task_i": 1, "task_j": 3, "pool_max_child_width": 20, "pool_total_child_width": 40},
                    {"task_i": 2, "task_j": 3, "pool_max_child_width": 25, "pool_total_child_width": 35},
                ],
                "task_i": 1,
                "task_j": 2,
                "tail_class": "completion_bound_tail",
                "usable_for_branch_impact_training": True,
            }
            (audit_dir / "branch_impact_rows.jsonl").write_text(
                json.dumps(row, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            runbook = build_runbook(
                [audit_dir],
                tmp_path / "out",
                tmp_path / "report.md",
                time_limit=321,
                alt_pairs_per_node=1,
            )

            self.assertTrue(runbook["diagnostic_only"])
            self.assertFalse(runbook["runs_bpc_or_pricing"])
            self.assertEqual(runbook["entry_count"], 1)
            entry = runbook["entries"][0]
            self.assertEqual(entry["source_selected_pair"], [1, 2])
            self.assertEqual(entry["forced_pair"], [1, 3])
            self.assertEqual(entry["forced_pair_path_rule"], "force_pair_path:0:1,3")
            self.assertIn("journey_branch_candidate_log_top_n=12", entry["command"])
            self.assertIn("journey_branch_candidate_priority=force_pair_path:0:1,3", entry["command"])
            self.assertIn("--time-limit", entry["command"])
            self.assertIn("321", entry["command"])
            self.assertTrue((tmp_path / "out" / "runbook.json").exists())
            self.assertTrue((tmp_path / "out" / "commands.sh").exists())
            self.assertIn("official_bound_effect = false", (tmp_path / "report.md").read_text(encoding="utf-8"))

    def test_build_runbook_preserves_depth_path_for_alternative(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            audit_dir = tmp_path / "audit"
            audit_dir.mkdir()
            log_path = (
                tmp_path
                / "logs"
                / "BPC_future"
                / "logical_graph"
                / "tasks_020"
                / "demo_instance.json.jsonl"
            )
            log_path.parent.mkdir(parents=True)
            log_rows = [
                {"event": "journey_node_start", "node_id": 0, "depth": 0},
                {
                    "event": "journey_child_queued",
                    "parent_node_id": 0,
                    "child_node_id": 1,
                    "depth": 1,
                    "constraint": "RF(2,5)=same_vehicle",
                },
                {"event": "journey_node_start", "node_id": 1, "depth": 1},
            ]
            log_path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in log_rows),
                encoding="utf-8",
            )
            row = {
                "branch_feature_source": "candidate_log",
                "branch_labels": {"y_completion_bound_tail": 1.0},
                "branch_node_id": 1,
                "depth": 1,
                "label_observation_complete": True,
                "log_file": str(log_path),
                "observed_branch_candidate": {"task_i": 2, "task_j": 17},
                "priority_top": [
                    {"task_i": 2, "task_j": 17, "pool_max_child_width": 50, "pool_total_child_width": 90},
                    {"task_i": 3, "task_j": 17, "pool_max_child_width": 40, "pool_total_child_width": 80},
                ],
                "task_i": 2,
                "task_j": 17,
                "tail_class": "completion_bound_tail",
                "usable_for_branch_impact_training": True,
            }
            (audit_dir / "branch_impact_rows.jsonl").write_text(
                json.dumps(row, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            runbook = build_runbook(
                [audit_dir],
                tmp_path / "out",
                tmp_path / "report.md",
                alt_pairs_per_node=2,
            )

            self.assertEqual(runbook["entry_count"], 1)
            entry = runbook["entries"][0]
            self.assertEqual(entry["forced_pair"], [3, 17])
            self.assertEqual(
                entry["forced_pair_path_rule"],
                "force_pair_path:0:2,5=same_vehicle;1:3,17",
            )
            self.assertEqual(
                entry["source_path_edges"],
                [
                    {
                        "child_node_id": 1,
                        "kind": "same_vehicle",
                        "parent_depth": 0,
                        "parent_node_id": 0,
                        "task_i": 2,
                        "task_j": 5,
                    }
                ],
            )


if __name__ == "__main__":
    unittest.main()

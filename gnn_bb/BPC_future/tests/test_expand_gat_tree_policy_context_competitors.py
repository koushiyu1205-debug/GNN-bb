from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.expand_gat_tree_policy_context_competitors import expand_context_competitors


class ExpandGATTreePolicyContextCompetitorsTests(unittest.TestCase):
    def test_expands_top_candidates_as_low_weight_competitors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows = [
                {
                    "instance": "inst.json",
                    "node_id": 0,
                    "depth": 0,
                    "baseline_pair": [1, 3],
                    "selected_pair": [1, 2],
                    "top": [
                        {"task_i": 1, "task_j": 2, "same_mass": 0.5},
                        {"task_i": 1, "task_j": 3, "same_mass": 0.25},
                        {"task_i": 2, "task_j": 3, "same_mass": 0.75},
                    ],
                    "tree_policy_label_type": "strong_positive",
                    "y_tree_policy_positive": 1.0,
                    "y_tree_policy_hard_negative": 0.0,
                    "event_loss_weight": 0.5,
                },
                {
                    "instance": "inst.json",
                    "node_id": 0,
                    "depth": 0,
                    "baseline_pair": [1, 3],
                    "selected_pair": [1, 3],
                    "tree_policy_label_type": "context_competitor_negative",
                    "y_tree_policy_positive": 0.0,
                    "y_tree_policy_hard_negative": 1.0,
                },
                {
                    "instance": "inst.json",
                    "node_id": 1,
                    "depth": 1,
                    "baseline_pair": [1, 2],
                    "selected_pair": [2, 3],
                    "tree_policy_label_type": "hard_negative",
                    "y_tree_policy_positive": 0.0,
                    "y_tree_policy_hard_negative": 1.0,
                },
            ]
            input_path = root / "tree_policy_event_rows.jsonl"
            input_path.write_text(
                "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
                encoding="utf-8",
            )

            summary = expand_context_competitors(
                input_path,
                root / "out",
                root / "report.md",
                max_competitors_per_positive=200,
                competitor_weight=0.05,
            )

            self.assertEqual(summary["input_row_count"], 3)
            self.assertEqual(summary["added_context_competitor_count"], 2)
            self.assertEqual(summary["skipped_counts"]["dropped_existing_context_competitor"], 1)
            output_rows = [
                json.loads(line)
                for line in (root / "out" / "tree_policy_event_rows.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            competitor_rows = [
                row for row in output_rows if row.get("tree_policy_label_type") == "context_competitor_negative"
            ]
            self.assertEqual(len(competitor_rows), 2)
            self.assertEqual({tuple(row["selected_pair"]) for row in competitor_rows}, {(1, 3), (2, 3)})
            self.assertTrue(all(row["event_loss_weight"] == 0.05 for row in competitor_rows))
            self.assertTrue(all(row["candidate_counterfactual_observed"] is False for row in competitor_rows))
            self.assertTrue(any(row.get("tree_policy_label_type") == "hard_negative" for row in output_rows))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.audit_journey_tail_positive_gap import audit_positive_gap


class JourneyTailPositiveGapTests(unittest.TestCase):
    def test_audit_positive_gap_flags_missing_useful_positive(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            rows_dir = tmp_path / "rows"
            rows_dir.mkdir()
            rows = [
                {
                    "source_type": "branch_impact",
                    "log_file": "branch.jsonl",
                    "node_id": 2,
                    "depth": 1,
                    "task_i": 4,
                    "task_j": 8,
                    "tail_class": "completion_bound_tail",
                    "labels": {
                        "y_useful_tail_reduction": 0.0,
                        "y_tail_risk": 1.0,
                        "y_completion_bound_tail": 1.0,
                        "y_early_branch_continues": 0.0,
                        "y_negative_chain_continues": 0.0,
                        "y_active_touch": 1.0,
                        "y_inactive_only": 0.0,
                        "y_child_negative_pricing_events": 2.0,
                        "y_child_completion_bound_retries": 1.0,
                        "y_child_early_branch_triggers": 0.0,
                    },
                },
                {
                    "source_type": "weak_negative_tail",
                    "log_file": "weak.jsonl",
                    "node_id": 3,
                    "depth": 2,
                    "tail_class": "weak_negative_filtered",
                    "labels": {
                        "y_useful_tail_reduction": 0.0,
                        "y_tail_risk": 1.0,
                        "y_weak_negative_filtered": 1.0,
                    },
                },
            ]
            (rows_dir / "tail_impact_training_rows.jsonl").write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

            summary = audit_positive_gap(
                [rows_dir],
                tmp_path / "out",
                tmp_path / "report.md",
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["certificate_effect"])
            self.assertFalse(summary["contrastive_tail_training_ready"])
            self.assertEqual(summary["positive_gap_reason"], "no_useful_tail_reduction_positive")
            self.assertEqual(summary["row_count"], 2)
            self.assertEqual(summary["useful_tail_reduction_positive_count"], 0)
            self.assertEqual(summary["tail_risk_count"], 2)
            self.assertEqual(summary["active_touch_count"], 1)
            self.assertEqual(summary["active_touch_still_tail_risk_count"], 1)
            self.assertEqual(summary["active_touch_completion_bound_tail_count"], 1)
            self.assertEqual(summary["weak_negative_filtered_count"], 1)
            self.assertEqual(len(summary["near_positive_rows"]), 1)
            self.assertTrue((tmp_path / "out" / "summary.json").exists())
            self.assertTrue((tmp_path / "out" / "near_positive_rows.jsonl").exists())
            self.assertIn("certificate_effect = false", (tmp_path / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

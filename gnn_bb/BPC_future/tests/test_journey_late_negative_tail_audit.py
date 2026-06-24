from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.audit_journey_late_negative_tail import summarize, write_outputs


class JourneyLateNegativeTailAuditTests(unittest.TestCase):
    def test_summarize_joins_pricing_and_column_addition_classes(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_path = tmp_path / "tail.jsonl"
            records = [
                {
                    "event": "journey_pricing",
                    "node_id": 1,
                    "depth": 1,
                    "cg_iter": 3,
                    "time": 10.0,
                    "pricing_kind": "exact_completion_bound",
                    "pricing_state": "FOUND_NEGATIVE",
                    "reason": "negative_journey_requires_column_addition",
                    "negative_journeys": 2,
                    "selected_trips": 1,
                    "generated_sequences": 100,
                    "evaluated_timed_trips": 200,
                },
                {
                    "event": "journey_column_addition",
                    "node_id": 1,
                    "depth": 1,
                    "cg_iter": 3,
                    "pricing_kind": "exact_completion_bound",
                    "added_journeys": 2,
                    "active_changed_task_set_count": 1,
                    "inactive_changed_task_set_count": 1,
                    "changed_task_set_count": 2,
                    "addition_productivity_class": "active_support_changed",
                    "changed_task_set_samples": [[1, 2], [3, 4]],
                    "active_changed_task_set_samples": [[1, 2]],
                    "inactive_changed_task_set_samples": [[3, 4]],
                },
                {
                    "event": "journey_pricing",
                    "node_id": 2,
                    "depth": 2,
                    "cg_iter": 4,
                    "time": 11.0,
                    "pricing_kind": "heuristic",
                    "pricing_state": "FOUND_NEGATIVE",
                    "reason": "streaming_partial_negative_journey",
                    "negative_journeys": 1,
                    "selected_trips": 1,
                },
                {
                    "event": "journey_column_addition",
                    "node_id": 2,
                    "depth": 2,
                    "cg_iter": 4,
                    "pricing_kind": "heuristic",
                    "added_journeys": 1,
                    "active_changed_task_set_count": 0,
                    "inactive_changed_task_set_count": 1,
                    "changed_task_set_count": 1,
                    "addition_productivity_class": "changed_inactive_only",
                    "changed_task_set_samples": [[5, 6]],
                    "inactive_changed_task_set_samples": [[5, 6]],
                },
                {
                    "event": "journey_pricing",
                    "node_id": 3,
                    "depth": 2,
                    "cg_iter": 5,
                    "time": 12.0,
                    "pricing_kind": "exact_completion_bound",
                    "pricing_state": "INCOMPLETE_LIMIT",
                    "reason": "weak_negative_journeys_filtered",
                    "negative_journeys": 0,
                    "selected_trips": 0,
                    "weak_negative_journeys_filtered": 1,
                    "profile_weak_filtered_materialized_count": 1,
                    "profile_weak_filtered_best_rough_rc": -0.3,
                    "profile_weak_filtered_best_true_rc": 4.0,
                    "diagnostic_selected_weak_filtered_task_set_samples": [[7, 8]],
                },
            ]
            log_path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )

            summary = summarize([log_path], min_cg_iter=3)

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertEqual(summary["tail_event_count"], 3)
            self.assertEqual(summary["true_negative_event_count"], 2)
            self.assertEqual(summary["weak_filtered_event_count"], 1)
            self.assertEqual(summary["weak_false_negative_event_count"], 1)
            self.assertEqual(summary["total_active_changed_task_sets"], 1)
            self.assertEqual(summary["total_inactive_changed_task_sets"], 2)
            self.assertEqual(summary["total_added_journeys"], 3)
            self.assertEqual(
                summary["tail_class_counts"],
                {
                    "true_negative_active_support_changing": 1,
                    "true_negative_inactive_only": 1,
                    "weak_false_negative_filtered": 1,
                },
            )
            self.assertEqual(summary["changed_task_set_sample_counts"]["1,2"], 1)
            self.assertEqual(summary["weak_task_set_sample_counts"]["7,8"], 1)
            rows = summary["rows"]
            self.assertEqual(rows[0]["tail_class"], "true_negative_active_support_changing")
            self.assertTrue(rows[0]["has_true_negative"])
            self.assertFalse(rows[0]["has_weak_filtered"])
            self.assertEqual(rows[1]["tail_class"], "true_negative_inactive_only")
            self.assertEqual(rows[2]["tail_class"], "weak_false_negative_filtered")
            self.assertFalse(rows[2]["has_true_negative"])
            self.assertTrue(rows[2]["has_weak_filtered"])

            write_outputs(summary, tmp_path / "out", tmp_path / "report.md")
            self.assertTrue((tmp_path / "out" / "summary.json").exists())
            self.assertTrue((tmp_path / "out" / "late_negative_tail_rows.jsonl").exists())
            self.assertIn("official_bound_effect = false", (tmp_path / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.audit_journey_weak_negative_tail import summarize, write_outputs


class JourneyWeakNegativeTailAuditTests(unittest.TestCase):
    def test_summarize_extracts_true_rc_filtered_weak_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_path = tmp_path / "weak.jsonl"
            records = [
                {
                    "event": "journey_pricing",
                    "node_id": 3,
                    "depth": 2,
                    "cg_iter": 4,
                    "time": 12.0,
                    "pricing_kind": "exact_retry",
                    "pricing_state": "INCOMPLETE_LIMIT",
                    "reason": "weak_negative_journeys_filtered",
                    "oracle_classification": "weak_negative_filtered_incomplete",
                    "pricing_dual_source": "scip_learning_certificate",
                    "pricing_time_limit": 20.0,
                    "profile_generation_time": 1.5,
                    "profile_dp_time": 10.0,
                    "dp_state_count": 100,
                    "dp_profile_record_scans": 200,
                    "negative_journeys": 0,
                    "selected_trips": 2,
                    "profile_negative_candidate_count": 8,
                    "profile_negative_unique_mask_count": 4,
                    "profile_negative_selected_candidate_count": 1,
                    "profile_selected_candidate_input_count": 1,
                    "profile_selected_candidate_scanned_count": 1,
                    "profile_selected_candidate_materialized_count": 1,
                    "weak_negative_journeys_filtered": 1,
                    "profile_weak_filtered_materialized_count": 1,
                    "profile_weak_filtered_best_rough_rc": -0.2,
                    "profile_weak_filtered_best_true_rc": 8.0,
                    "profile_weak_filtered_max_true_minus_rough": 8.2,
                    "profile_weak_filtered_max_true_minus_rough_mask": 42,
                    "diagnostic_selected_weak_filtered_task_set_samples": [[2, 4, 7]],
                },
                {
                    "event": "journey_pricing",
                    "node_id": 4,
                    "depth": 2,
                    "cg_iter": 1,
                    "pricing_kind": "heuristic",
                    "pricing_state": "FOUND_NEGATIVE",
                    "negative_journeys": 3,
                    "weak_negative_journeys_filtered": 0,
                },
            ]
            log_path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )

            summary = summarize([log_path])
            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["certificate_effect"])
            self.assertEqual(summary["weak_event_count"], 1)
            self.assertEqual(summary["weak_training_row_count"], 1)
            self.assertEqual(summary["total_weak_negative_journeys_filtered"], 1)
            self.assertEqual(summary["total_profile_weak_filtered_materialized_count"], 1)
            self.assertEqual(summary["max_true_minus_rough"], 8.2)
            self.assertEqual(summary["best_rough_rc"], -0.2)
            self.assertEqual(summary["best_true_rc_after_materialization"], 8.0)
            self.assertEqual(summary["weak_mask_counts"], {"42": 1})
            self.assertEqual(summary["weak_task_set_sample_counts"], {"2,4,7": 1})
            row = summary["rows"][0]
            self.assertEqual(row["node_id"], 3)
            self.assertEqual(row["weak_task_set_samples"], [(2, 4, 7)])

            write_outputs(summary, tmp_path / "out", tmp_path / "report.md")
            self.assertTrue((tmp_path / "out" / "summary.json").exists())
            self.assertTrue((tmp_path / "out" / "weak_negative_tail_rows.jsonl").exists())
            self.assertIn("certificate_effect = false", (tmp_path / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

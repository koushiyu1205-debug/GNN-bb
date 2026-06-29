import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_journey_completion_tail_profile import build_profile


class JourneyCompletionTailProfileTests(unittest.TestCase):
    def test_profile_summarizes_tail_min_fill_audit_only_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_dir = tmp_path / "logs"
            log_dir.mkdir()
            rows = [
                {
                    "event": "journey_exact_pricing_completion_bound_retry",
                    "time": 10.0,
                    "node_id": 0,
                    "depth": 0,
                    "cg_iter": 4,
                    "retry_mode": {
                        "completion_bound_diverse_harvest_tail_min_fill_enabled": False,
                        "completion_bound_diverse_harvest_tail_min_fill_audit_enabled": True,
                        "completion_bound_diverse_harvest_tail_min_fill_candidate": True,
                        "completion_bound_diverse_harvest_tail_min_fill_applied": False,
                        "completion_bound_diverse_harvest_tail_min_fill_base": 10,
                        "completion_bound_diverse_harvest_tail_min_fill_target": 4,
                        "completion_bound_diverse_harvest_tail_min_fill_reason": "optin_disabled",
                    },
                },
                {
                    "event": "journey_pricing",
                    "time": 11.0,
                    "node_id": 0,
                    "depth": 0,
                    "cg_iter": 4,
                    "pricing_kind": "exact_completion_bound_retry",
                    "pricing_state": "FOUND_NEGATIVE",
                    "reason": "negative_journey_requires_column_addition",
                    "negative_journeys": 3,
                    "selected_trips": 2,
                    "profile_generation_time": 1.25,
                    "direct_label_harvest_min_fill": 10,
                    "harvest_candidate_negative_count": 4,
                    "harvest_selected_count": 2,
                    "harvest_candidate_new_task_set_count": 3,
                    "harvest_selected_new_task_set_count": 2,
                    "harvest_selected_support_changing_count": 2,
                },
                {
                    "event": "finish",
                    "status": "TIME_LIMIT",
                    "solving_time": 200.0,
                    "instance": "fake_tasks020.json",
                },
            ]
            (log_dir / "run.jsonl").write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

            summary = build_profile([log_dir], tmp_path / "out", tmp_path / "report.md")

            aggregate = summary["aggregate"]
            self.assertEqual(aggregate["completion_retry_tail_min_fill_mode_count"], 1)
            self.assertEqual(aggregate["completion_retry_tail_min_fill_candidate_count"], 1)
            self.assertEqual(aggregate["completion_retry_tail_min_fill_applied_count"], 0)
            self.assertEqual(aggregate["completion_retry_tail_min_fill_optin_disabled_count"], 1)
            self.assertEqual(
                aggregate["completion_retry_tail_min_fill_reason_counts"],
                {"optin_disabled": 1},
            )
            record = summary["records"][0]
            self.assertEqual(record["completion_retry_last"]["direct_label_harvest_min_fill"], 10)
            self.assertEqual(
                record["completion_retry_tail_min_fill_last"][
                    "completion_bound_diverse_harvest_tail_min_fill_reason"
                ],
                "optin_disabled",
            )
            self.assertEqual(
                record["completion_retry_harvest_tail_class"],
                "harvest_returned_new_task_set",
            )
            self.assertEqual(
                aggregate["completion_retry_harvest_tail_class_counts"],
                {"harvest_returned_new_task_set": 1},
            )
            self.assertEqual(
                aggregate["completion_retry_harvest_count_totals"]["harvest_candidate_new_task_set_count"],
                3,
            )
            self.assertTrue((tmp_path / "out" / "summary.json").exists())
            self.assertTrue((tmp_path / "report.md").exists())

    def test_profile_classifies_expensive_retry_without_harvest_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_dir = tmp_path / "logs"
            log_dir.mkdir()
            rows = [
                {
                    "event": "journey_pricing",
                    "time": 11.0,
                    "node_id": 0,
                    "depth": 0,
                    "cg_iter": 8,
                    "pricing_kind": "exact_completion_bound_retry",
                    "pricing_state": "INCOMPLETE",
                    "reason": "time_limit",
                    "negative_journeys": 0,
                    "selected_trips": 0,
                    "profile_generation_time": 45.0,
                    "harvest_candidate_negative_count": 0,
                    "harvest_selected_count": 0,
                },
                {
                    "event": "finish",
                    "status": "EXTERNAL_TIME_LIMIT",
                    "solving_time": None,
                    "instance": "hard_tasks020.json",
                },
            ]
            (log_dir / "run.jsonl").write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

            summary = build_profile([log_dir], tmp_path / "out", tmp_path / "report.md")

            aggregate = summary["aggregate"]
            self.assertEqual(
                aggregate["completion_retry_harvest_tail_class_counts"],
                {"expensive_no_harvest_candidate": 1},
            )
            self.assertIn("direct-label proof loop", aggregate["interpretation"])
            self.assertEqual(
                aggregate["completion_retry_harvest_top_profile_records"][0]["harvest_tail_class"],
                "expensive_no_harvest_candidate",
            )
            self.assertEqual(
                summary["records"][0]["completion_retry_harvest_count_totals"]["harvest_selected_count"],
                0,
            )


if __name__ == "__main__":
    unittest.main()

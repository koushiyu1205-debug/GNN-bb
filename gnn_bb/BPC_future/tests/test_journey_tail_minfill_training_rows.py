from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_journey_tail_minfill_training_rows import (
    build_tail_minfill_training_rows,
)


class JourneyTailMinfillTrainingRowsTests(unittest.TestCase):
    def test_build_training_rows_preserves_strict_and_shadow_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            summary_path = tmp_path / "ab" / "summary.json"
            summary_path.parent.mkdir()
            summary_path.write_text(
                json.dumps(
                    {
                        "rows": [
                            self._row(
                                "positive.json",
                                "strong_positive",
                                "nonoptimal_to_target_optimal",
                                baseline_status="TIME_LIMIT",
                                optin_status="OPTIMAL",
                                baseline_wall=151.0,
                                optin_wall=131.0,
                                exact_delta=-5,
                                retry_delta=-2,
                            ),
                            self._row(
                                "speedup.json",
                                "positive_speedup",
                                "both_optimal_wall_reduced",
                                baseline_status="OPTIMAL",
                                optin_status="OPTIMAL",
                                baseline_wall=251.0,
                                optin_wall=250.0,
                                exact_delta=0,
                                retry_delta=0,
                            ),
                            self._row(
                                "negative.json",
                                "hard_negative",
                                "both_nonoptimal_no_target_resolution",
                                baseline_status="EXTERNAL_TIME_LIMIT",
                                optin_status="EXTERNAL_TIME_LIMIT",
                                baseline_wall=260.0,
                                optin_wall=260.1,
                                exact_delta=0,
                                retry_delta=-1,
                            ),
                            self._row(
                                "missing.json",
                                "missing_result",
                                "baseline_or_optin_result_missing",
                                baseline_status="",
                                optin_status="",
                                baseline_wall=0.0,
                                optin_wall=0.0,
                                exact_delta=0,
                                retry_delta=0,
                            ),
                        ]
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            result = build_tail_minfill_training_rows(
                [summary_path],
                output_dir=tmp_path / "out",
                report=tmp_path / "report.md",
            )

            self.assertFalse(result["runs_bpc_or_pricing"])
            self.assertFalse(result["production_ready"])
            self.assertEqual(result["training_row_count"], 3)
            self.assertEqual(result["skipped_missing_result_count"], 1)
            self.assertEqual(result["strict_positive_count"], 1)
            self.assertEqual(result["hard_negative_count"], 1)
            self.assertEqual(result["shadow_only_count"], 1)
            self.assertTrue(result["minimal_contrastive_ready"])
            self.assertFalse(result["shadow_training_ready"])
            self.assertFalse(result["optin_training_ready"])

            rows = result["training_rows"]
            positive = next(row for row in rows if row["instance"] == "positive.json")
            speedup = next(row for row in rows if row["instance"] == "speedup.json")
            negative = next(row for row in rows if row["instance"] == "negative.json")
            self.assertEqual(positive["labels"]["y_strict_positive"], 1.0)
            self.assertEqual(positive["labels"]["y_target200_success"], 1.0)
            self.assertEqual(positive["labels"]["y_timeout_resolved"], 1.0)
            self.assertEqual(positive["labels"]["y_exact_pricing_reduced"], 1.0)
            self.assertEqual(speedup["labels"]["y_positive_speedup"], 1.0)
            self.assertEqual(speedup["labels"]["y_shadow_only"], 1.0)
            self.assertEqual(speedup["labels"]["y_trainable_positive"], 0.0)
            self.assertEqual(speedup["labels"]["y_target200_success"], 0.0)
            self.assertEqual(negative["labels"]["y_hard_negative"], 1.0)
            self.assertEqual(negative["labels"]["y_trainable_negative"], 1.0)
            self.assertTrue((tmp_path / "out" / "tail_minfill_training_rows.jsonl").exists())
            self.assertIn("strict_positive_count = 1", (tmp_path / "report.md").read_text())

    @staticmethod
    def _row(
        instance: str,
        classification: str,
        reason: str,
        *,
        baseline_status: str,
        optin_status: str,
        baseline_wall: float,
        optin_wall: float,
        exact_delta: int,
        retry_delta: int,
    ) -> dict:
        return {
            "schema_version": "journey_tail_minfill_ab_result_row_v1",
            "instance": instance,
            "entry_id": 1,
            "classification": classification,
            "classification_reason": reason,
            "source_completion_retry_class": "completion_bound_time_limit_no_column_uncertified",
            "source_tail_min_fill_candidate_count": 4,
            "baseline": {
                "status": baseline_status,
                "wall_time": baseline_wall,
                "solving_time": baseline_wall - 2.0,
                "external_timeout": baseline_status == "EXTERNAL_TIME_LIMIT",
                "tail_minfill_candidate_count": 4,
                "tail_minfill_applied_count": 0,
                "direct_label_harvest_min_fill_values": [10],
            },
            "optin": {
                "status": optin_status,
                "wall_time": optin_wall,
                "solving_time": optin_wall - 2.0,
                "external_timeout": optin_status == "EXTERNAL_TIME_LIMIT",
                "tail_minfill_candidate_count": 2,
                "tail_minfill_applied_count": 2,
                "direct_label_harvest_min_fill_values": [4],
            },
            "deltas": {
                "wall_time": optin_wall - baseline_wall,
                "solving_time": optin_wall - baseline_wall,
                "pricing_calls": exact_delta,
                "exact_pricing_calls": exact_delta,
                "completion_retry_count": retry_delta,
                "completion_retry_negative_journeys": -1,
                "completion_retry_selected_trips": -1,
            },
        }


if __name__ == "__main__":
    unittest.main()

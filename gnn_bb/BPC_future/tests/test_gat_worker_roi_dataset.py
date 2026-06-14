from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.build_gat_worker_roi_dataset import build_roi_dataset


class GATWorkerROIDatasetTests(unittest.TestCase):
    def test_builds_positive_and_noop_roi_labels_with_candidate_features(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            audit = tmp / "audit_summary.json"
            candidate_summary = tmp / "candidate_summary.json"
            instance = "toy_instance.json"
            audit.write_text(
                json.dumps(
                    {
                        "certificate_ready": False,
                        "official_bound_effect": False,
                        "records": [
                            {
                                "name": "positive",
                                "instance": instance,
                                "expected_context_hash": "ctx-pos",
                                "target_sequence": [1, 2],
                                "target_arc_option_sequence": ["0->1:a", "1->2:a", "2->0:a"],
                                "baseline_csv_exists": True,
                                "worker_csv_exists": True,
                                "official_bound_effect": False,
                                "certificate_effect": False,
                                "baseline_status": "TIME_LIMIT",
                                "worker_status": "TIME_LIMIT",
                                "baseline_primal": 10.0,
                                "worker_primal": 9.0,
                                "primal_improvement": 1.0,
                                "baseline_columns": 10,
                                "worker_columns": 12,
                                "columns_delta": 2,
                                "exact_pricing_calls_delta": 1,
                                "generated_sequences_delta": 7,
                                "roi_class": "positive_primal_roi",
                            },
                            {
                                "name": "noop",
                                "instance": instance,
                                "expected_context_hash": "ctx-flat",
                                "target_sequence": [3],
                                "target_arc_option_sequence": ["0->3:a", "3->0:a"],
                                "baseline_csv_exists": True,
                                "worker_csv_exists": True,
                                "official_bound_effect": False,
                                "certificate_effect": False,
                                "baseline_status": "TIME_LIMIT",
                                "worker_status": "TIME_LIMIT",
                                "baseline_primal": 10.0,
                                "worker_primal": 10.0,
                                "primal_improvement": 0.0,
                                "baseline_columns": 10,
                                "worker_columns": 10,
                                "columns_delta": 0,
                                "exact_pricing_calls_delta": 0,
                                "generated_sequences_delta": 0,
                                "roi_class": "no_observed_roi",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            candidate_summary.write_text(
                json.dumps(
                    {
                        "candidates": [
                            {
                                "name": "positive",
                                "instance": instance,
                                "expected_context_hash": "ctx-pos",
                                "target_sequence": [1, 2],
                                "target_arc_option_sequence": ["0->1:a", "1->2:a", "2->0:a"],
                                "decision_name": "HIGH_PRIORITY",
                                "decision_probability": 0.91,
                                "decision_reason": "high_priority",
                                "best_true_reduced_cost": -8.5,
                                "capture_cg_iter": 4,
                                "capture_returned_journey_count": 3,
                                "source_file": "capture.jsonl",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            summary = build_roi_dataset(
                audit_summary_path=audit,
                candidate_summary_paths=[candidate_summary],
                output_dir=tmp / "out",
                report=tmp / "report.md",
                min_positive_for_training=1,
                min_negative_for_training=1,
            )

            rows = [
                json.loads(line)
                for line in (tmp / "out" / "gat_worker_roi_rows.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            by_name = {row["name"]: row for row in rows}
            self.assertTrue(summary["all_checks_pass"])
            self.assertTrue(summary["training_ready"])
            self.assertEqual(summary["label_counts"], {"0": 1, "1": 1})
            self.assertEqual(by_name["positive"]["label_worker_roi_positive"], 1)
            self.assertEqual(by_name["positive"]["label_worker_adds_columns"], 1)
            self.assertEqual(by_name["positive"]["decision_probability"], 0.91)
            self.assertEqual(by_name["positive"]["best_true_reduced_cost"], -8.5)
            self.assertTrue(by_name["positive"]["candidate_feature_joined"])
            self.assertEqual(by_name["noop"]["label_worker_roi_positive"], 0)
            self.assertEqual(by_name["noop"]["label_worker_adds_columns"], 0)
            self.assertFalse(by_name["noop"]["candidate_feature_joined"])
            self.assertTrue((tmp / "out" / "gat_worker_roi_rows.csv").exists())
            self.assertTrue((tmp / "report.md").exists())

    def test_missing_result_is_not_training_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            audit = tmp / "audit_summary.json"
            audit.write_text(
                json.dumps(
                    {
                        "certificate_ready": False,
                        "official_bound_effect": False,
                        "records": [
                            {
                                "name": "missing",
                                "instance": "toy_instance.json",
                                "expected_context_hash": "ctx",
                                "target_sequence": [1],
                                "target_arc_option_sequence": ["0->1:a", "1->0:a"],
                                "baseline_csv_exists": True,
                                "worker_csv_exists": False,
                                "official_bound_effect": False,
                                "certificate_effect": False,
                                "primal_improvement": None,
                                "columns_delta": None,
                                "roi_class": "missing_result",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            summary = build_roi_dataset(
                audit_summary_path=audit,
                candidate_summary_paths=[],
                output_dir=tmp / "out",
                report=tmp / "report.md",
                min_positive_for_training=1,
                min_negative_for_training=1,
            )

            rows = [
                json.loads(line)
                for line in (tmp / "out" / "gat_worker_roi_rows.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertFalse(summary["all_checks_pass"])
            self.assertFalse(summary["training_ready"])
            self.assertEqual(summary["training_row_count"], 0)
            self.assertFalse(rows[0]["training_eligible"])
            self.assertEqual(rows[0]["training_exclusion_reason"], "missing_ab_result")
            self.assertIsNone(rows[0]["label_worker_roi_positive"])
            self.assertFalse(summary["certificate_ready"])
            self.assertFalse(summary["official_bound_effect"])


if __name__ == "__main__":
    unittest.main()

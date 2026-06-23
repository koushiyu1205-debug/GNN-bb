from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_journey_tail_impact_training_rows import build_tail_impact


class JourneyTailImpactTrainingRowsTests(unittest.TestCase):
    def test_build_tail_impact_fuses_weak_and_branch_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            weak_dir = tmp_path / "weak"
            weak_dir.mkdir()
            branch_dir = tmp_path / "branch"
            branch_dir.mkdir()
            weak_row = {
                "schema_version": "journey_weak_negative_tail_row_v1",
                "log_file": "weak.jsonl",
                "node_id": 3,
                "depth": 2,
                "cg_iter": 4,
                "time": 12.5,
                "pricing_time_limit": 20.0,
                "profile_generation_time": 1.25,
                "profile_dp_time": 8.0,
                "dp_state_count": 100,
                "negative_journeys": 0,
                "selected_trips": 2,
                "weak_negative_journeys_filtered": 1,
                "profile_weak_filtered_materialized_count": 1,
                "profile_weak_filtered_best_rough_rc": -0.3,
                "profile_weak_filtered_best_true_rc": 5.0,
                "profile_weak_filtered_max_true_minus_rough": 5.3,
            }
            branch_row = {
                "schema_version": "journey_branch_impact_training_row_v1",
                "log_file": "branch.jsonl",
                "branch_node_id": 0,
                "depth": 0,
                "task_i": 1,
                "task_j": 2,
                "tail_class": "completion_bound_tail",
                "branch_feature_source": "candidate_log",
                "branch_feature_schema": [
                    "depth",
                    "candidate_count",
                    "eligible_count",
                    "branch_rank_in_priority_top",
                    "pool_max_child_width",
                    "pool_total_child_width",
                    "pool_balance_gap",
                ],
                "branch_features": [0, 3, 2, 0, 5, 9, 1],
                "branch_labels": {
                    "y_tail_improved": 0.0,
                    "y_completion_bound_tail": 1.0,
                    "y_early_branch_continues": 0.0,
                    "y_negative_chain_continues": 0.0,
                    "y_active_touch": 0.0,
                    "y_inactive_only": 1.0,
                    "y_child_negative_pricing_events": 2.0,
                    "y_child_completion_bound_retries": 1.0,
                    "y_child_early_branch_triggers": 0.0,
                },
            }
            (weak_dir / "weak_negative_tail_rows.jsonl").write_text(
                json.dumps(weak_row, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (branch_dir / "branch_training_rows.jsonl").write_text(
                json.dumps(branch_row, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            summary = build_tail_impact(
                [weak_dir],
                [branch_dir],
                tmp_path / "out",
                tmp_path / "report.md",
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["certificate_effect"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertTrue(summary["hard_negative_catalog_ready"])
            self.assertFalse(summary["contrastive_tail_training_ready"])
            self.assertFalse(summary["tail_label_training_ready"])
            self.assertEqual(summary["training_row_count"], 2)
            self.assertEqual(summary["weak_row_count"], 1)
            self.assertEqual(summary["branch_row_count"], 1)
            self.assertEqual(summary["source_counts"], {"branch_impact": 1, "weak_negative_tail": 1})
            self.assertEqual(summary["label_positive_counts"]["y_tail_risk"], 2)
            self.assertEqual(summary["label_positive_counts"]["y_weak_negative_filtered"], 1)
            self.assertEqual(summary["label_positive_counts"]["y_completion_bound_tail"], 1)
            self.assertEqual(summary["regression_label_totals"]["child_negative_pricing_events"], 2)
            rows = summary["rows"]
            weak_fused = next(row for row in rows if row["source_type"] == "weak_negative_tail")
            branch_fused = next(row for row in rows if row["source_type"] == "branch_impact")
            self.assertEqual(weak_fused["labels"]["y_useful_tail_reduction"], 0.0)
            self.assertEqual(weak_fused["labels"]["y_weak_negative_filtered"], 1.0)
            self.assertEqual(branch_fused["labels"]["y_completion_bound_tail"], 1.0)
            self.assertEqual(branch_fused["labels"]["y_inactive_only"], 1.0)
            self.assertEqual(len(branch_fused["features"]), len(summary["feature_schema"]))
            self.assertTrue((tmp_path / "out" / "summary.json").exists())
            self.assertTrue((tmp_path / "out" / "tail_impact_training_rows.jsonl").exists())
            self.assertIn("certificate_effect = false", (tmp_path / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

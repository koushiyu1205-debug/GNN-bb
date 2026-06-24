from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.audit_journey_branch_impact import build_branch_impact


class JourneyBranchImpactAuditTests(unittest.TestCase):
    def test_build_branch_impact_summarizes_selected_branch_and_child_tail(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_path = tmp_path / "branch.jsonl"
            records = [
                {"event": "journey_node_start", "node_id": 0, "depth": 0, "time": 0.0},
                {
                    "event": "journey_branch_candidates",
                    "node_id": 0,
                    "depth": 0,
                    "time": 1.0,
                    "candidate_count": 2,
                    "eligible_count": 2,
                    "priority_mode": "pool_split",
                    "forced_pair": [1, 2],
                    "forced_pair_matched": True,
                    "selected": {
                        "task_i": 1,
                        "task_j": 2,
                        "fractionality": 0.49,
                        "pool_max_child_width": 3,
                    },
                    "top": [
                        {"task_i": 2, "task_j": 3, "fractionality": 0.5},
                        {"task_i": 1, "task_j": 2, "fractionality": 0.49},
                    ],
                    "priority_top": [
                        {"task_i": 1, "task_j": 2, "fractionality": 0.49},
                        {"task_i": 2, "task_j": 3, "fractionality": 0.5},
                    ],
                },
                {
                    "event": "journey_branch",
                    "node_id": 0,
                    "depth": 0,
                    "time": 1.1,
                    "left": "RF(1,2)=same_vehicle",
                    "right": "RF(1,2)=separate_vehicle",
                },
                {
                    "event": "journey_child_queued",
                    "parent_node_id": 0,
                    "child_node_id": 1,
                    "depth": 1,
                    "time": 1.2,
                    "constraint": "RF(1,2)=same_vehicle",
                    "allowed_current_journeys": 3,
                    "lower_bound_exact": False,
                },
                {
                    "event": "journey_child_queued",
                    "parent_node_id": 0,
                    "child_node_id": 2,
                    "depth": 1,
                    "time": 1.3,
                    "constraint": "RF(1,2)=separate_vehicle",
                    "allowed_current_journeys": 5,
                    "lower_bound_exact": False,
                },
                {"event": "journey_node_start", "node_id": 1, "depth": 1, "time": 2.0},
                {
                    "event": "journey_pricing",
                    "node_id": 1,
                    "depth": 1,
                    "time": 3.0,
                    "pricing_kind": "heuristic",
                    "pricing_state": "FOUND_NEGATIVE",
                    "best_reduced_cost": -2.0,
                    "negative_journeys": 1,
                    "selected_trips": 1,
                },
                {
                    "event": "journey_column_addition",
                    "node_id": 1,
                    "depth": 1,
                    "time": 3.1,
                    "addition_productivity_class": "active_replacement_task_set",
                    "added_journeys": 2,
                    "new_journeys": 1,
                    "replacement_journeys": 1,
                    "active_replacement_task_set_count": 1,
                    "inactive_changed_task_set_count": 0,
                },
                {
                    "event": "journey_early_branch_trigger",
                    "node_id": 1,
                    "depth": 1,
                    "time": 4.0,
                    "reason": "incomplete_no_column_tailing",
                },
            ]
            log_path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )

            summary = build_branch_impact(
                [log_path],
                tmp_path / "out",
                tmp_path / "report.md",
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertEqual(summary["aggregate"]["branch_count"], 1)
            self.assertEqual(summary["aggregate"]["tail_class_counts"], {"early_branch_continues": 1})
            self.assertEqual(summary["aggregate"]["unprocessed_child_count"], 1)
            row = summary["records"][0]
            self.assertTrue(row["selected_matches_branch"])
            self.assertEqual(row["priority_mode"], "pool_split")
            self.assertEqual(row["forced_pair"], [1, 2])
            self.assertTrue(row["forced_pair_matched"])
            self.assertEqual(row["branch_rank_in_top"], 1)
            self.assertEqual(row["branch_rank_in_priority_top"], 0)
            self.assertEqual(row["unprocessed_child_count"], 1)
            self.assertEqual(row["first_started_child_node_id"], 1)
            self.assertEqual(row["first_child_negative_pricing_event_count"], 1)
            self.assertEqual(row["first_child_column_additions"], 1)
            self.assertEqual(row["first_child_early_branch_trigger_count"], 1)
            self.assertEqual(row["sum_child_added_journeys"], 2)
            self.assertEqual(row["sum_child_active_replacement_task_set_count"], 1)
            self.assertEqual(row["branch_feature_source"], "candidate_log")
            self.assertTrue(row["right_censored"])
            self.assertFalse(row["label_observation_complete"])
            self.assertFalse(row["usable_for_branch_impact_training"])
            self.assertEqual(summary["aggregate"]["right_censored_branch_count"], 1)
            self.assertEqual(summary["aggregate"]["forced_pair_branch_count"], 1)
            self.assertEqual(summary["aggregate"]["forced_pair_matched_branch_count"], 1)
            self.assertEqual(summary["aggregate"]["complete_label_branch_count"], 0)
            self.assertEqual(summary["aggregate"]["usable_branch_impact_training_count"], 0)
            self.assertEqual(
                len(row["branch_feature_vector"]),
                len(summary["branch_feature_schema"]),
            )
            self.assertEqual(row["branch_labels"]["y_early_branch_continues"], 1.0)
            self.assertEqual(row["branch_labels"]["y_active_touch"], 1.0)
            training_rows = summary["branch_training_rows"]
            self.assertEqual(len(training_rows), 1)
            self.assertEqual(training_rows[0]["branch_feature_schema"], summary["branch_feature_schema"])
            self.assertEqual(training_rows[0]["branch_label_schema"], summary["branch_label_schema"])
            self.assertTrue(training_rows[0]["right_censored"])
            self.assertEqual(training_rows[0]["forced_pair"], [1, 2])
            self.assertTrue(training_rows[0]["forced_pair_matched"])
            self.assertFalse(training_rows[0]["usable_for_branch_impact_training"])
            self.assertTrue((tmp_path / "out" / "summary.json").exists())
            self.assertTrue((tmp_path / "out" / "branch_impact_rows.jsonl").exists())
            self.assertTrue((tmp_path / "out" / "branch_training_rows.jsonl").exists())
            self.assertIn("production_ready = false", (tmp_path / "report.md").read_text(encoding="utf-8"))

    def test_build_branch_impact_marks_complete_candidate_rows_usable(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_path = tmp_path / "branch_complete.jsonl"
            records = [
                {"event": "journey_node_start", "node_id": 0, "depth": 0, "time": 0.0},
                {
                    "event": "journey_branch_candidates",
                    "node_id": 0,
                    "depth": 0,
                    "time": 1.0,
                    "candidate_count": 1,
                    "eligible_count": 1,
                    "priority_mode": "fractionality",
                    "selected": {"task_i": 1, "task_j": 2, "fractionality": 0.5},
                    "top": [{"task_i": 1, "task_j": 2, "fractionality": 0.5}],
                    "priority_top": [{"task_i": 1, "task_j": 2, "fractionality": 0.5}],
                },
                {
                    "event": "journey_branch",
                    "node_id": 0,
                    "depth": 0,
                    "time": 1.1,
                    "left": "RF(1,2)=same_vehicle",
                    "right": "RF(1,2)=separate_vehicle",
                },
                {
                    "event": "journey_child_queued",
                    "parent_node_id": 0,
                    "child_node_id": 1,
                    "depth": 1,
                    "time": 1.2,
                    "constraint": "RF(1,2)=same_vehicle",
                    "allowed_current_journeys": 3,
                    "lower_bound_exact": True,
                },
                {
                    "event": "journey_child_queued",
                    "parent_node_id": 0,
                    "child_node_id": 2,
                    "depth": 1,
                    "time": 1.3,
                    "constraint": "RF(1,2)=separate_vehicle",
                    "allowed_current_journeys": 5,
                    "lower_bound_exact": True,
                },
                {"event": "journey_node_start", "node_id": 1, "depth": 1, "time": 2.0},
                {"event": "journey_node_start", "node_id": 2, "depth": 1, "time": 3.0},
                {"event": "finish", "status": "OPTIMAL", "time": 4.0},
            ]
            log_path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )

            summary = build_branch_impact(
                [log_path],
                tmp_path / "out",
                tmp_path / "report.md",
            )

            row = summary["records"][0]
            self.assertFalse(row["right_censored"])
            self.assertTrue(row["label_observation_complete"])
            self.assertTrue(row["usable_for_branch_impact_training"])
            self.assertEqual(row["run_status"], "OPTIMAL")
            self.assertEqual(summary["aggregate"]["right_censored_branch_count"], 0)
            self.assertEqual(summary["aggregate"]["complete_label_branch_count"], 1)
            self.assertEqual(summary["aggregate"]["usable_branch_impact_training_count"], 1)
            self.assertEqual(summary["branch_training_rows"][0]["usable_for_branch_impact_training"], True)


if __name__ == "__main__":
    unittest.main()

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
                {
                    "event": "journey_node_start",
                    "node_id": 0,
                    "depth": 0,
                    "time": 0.0,
                    "lower_bound": 5.0,
                },
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
                    "phased_testing_controller_active": True,
                    "phased_testing_controller_input_count": 2,
                    "phased_testing_stage_counts": {"phase2_heuristic": 1, "phase1_lp": 1},
                    "phased_testing_decision_counts": {"probed_complete": 1, "skipped_by_dynamic_k": 1},
                    "phased_testing_phase0_fail_reason_counts": {},
                    "phased_testing_phase1_candidate_count": 2,
                    "phased_testing_phase1_probe_count": 2,
                    "phased_testing_phase1_complete_count": 2,
                    "phased_testing_phase1_dynamic_k_excluded_count": 0,
                    "phased_testing_phase1_reason_counts": {"ok": 2},
                    "phased_testing_phase1_total_wall_time": 0.25,
                    "phased_testing_phase1_best_min_child_lp_gain": 2.25,
                    "phased_testing_phase1_best_child_lp_gain_product": 5.0,
                    "phased_testing_phase1_official_bound_effect_any": False,
                    "phased_testing_phase1_certificate_effect_any": False,
                    "phased_testing_phase2_candidate_count": 2,
                    "phased_testing_phase2_probe_count": 1,
                    "phased_testing_phase2_complete_count": 1,
                    "phased_testing_phase2_dynamic_k_excluded_count": 1,
                    "phased_testing_phase2_reason_counts": {"dynamic_k_excluded": 1, "ok": 1},
                    "phased_testing_phase2_total_wall_time": 0.05,
                    "phased_testing_phase2_negative_child_count_total": 1,
                    "phased_testing_phase2_negative_journey_count_total": 3,
                    "phased_testing_phase2_generated_sequences_total": 40,
                    "phased_testing_phase2_evaluated_timed_trips_total": 12,
                    "phased_testing_phase2_worst_negative_severity_max": 1.5,
                    "phased_testing_phase2_negative_severity_sum_total": 2.0,
                    "phased_testing_phase2_negative_severity_gap_max": 1.0,
                    "phased_testing_phase2_negative_severity_balance_ratio_min": 0.5,
                    "phased_testing_phase2_official_bound_effect_any": False,
                    "phased_testing_phase2_certificate_effect_any": False,
                    "phased_testing_official_bound_effect_any": False,
                    "phased_testing_certificate_effect_any": False,
                    "selected": {
                        "task_i": 1,
                        "task_j": 2,
                        "fractionality": 0.49,
                        "pool_max_child_width": 3,
                        "phased_testing_stage": "phase2_heuristic",
                        "phased_testing_decision": "probed_complete",
                        "phased_testing_phase0_passed": True,
                        "phased_testing_phase1_lp_complete": True,
                        "phased_testing_phase2_heuristic_complete": True,
                        "phase1_min_child_lp_gain": 2.25,
                        "phase1_child_lp_gain_product": 5.0,
                        "phase1_child_width_balance": 2,
                        "phase2_negative_child_count": 1,
                        "phase2_negative_journey_count": 3,
                        "phase2_negative_journey_balance_gap": 2,
                        "phase2_best_reduced_cost": -1.5,
                        "phase2_worst_negative_severity": 1.5,
                        "phase2_same_child_negative_severity": 1.5,
                        "phase2_separate_child_negative_severity": 0.5,
                        "phase2_negative_severity_sum": 2.0,
                        "phase2_negative_severity_gap": 1.0,
                        "phase2_negative_severity_balance_ratio": 0.5,
                        "phase2_negative_child_presence_balance_gap": 0,
                        "phase2_child_wall_time_balance_gap": 0.015,
                        "phase2_child_status_mismatch": True,
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
                    "lower_bound": 7.0,
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
                    "lower_bound": 7.0,
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
                    "event": "journey_pricing",
                    "node_id": 1,
                    "depth": 1,
                    "time": 3.5,
                    "pricing_kind": "exact",
                    "pricing_state": "CERTIFIED_NO_NEGATIVE",
                    "global_certificate": True,
                    "best_reduced_cost": 0.0,
                    "negative_journeys": 0,
                    "selected_trips": 0,
                },
                {
                    "event": "journey_corrected_node_bound_audit",
                    "node_id": 1,
                    "depth": 1,
                    "time": 3.6,
                    "corrected_node_lb": 11.0,
                },
                {
                    "event": "journey_early_branch_trigger",
                    "node_id": 1,
                    "depth": 1,
                    "time": 4.0,
                    "reason": "incomplete_no_column_tailing",
                },
                {"event": "journey_fathom", "node_id": 1, "depth": 1, "time": 5.0, "reason": "bound"},
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
            self.assertEqual(summary["schema_version"], "journey_branch_impact_audit_v2")
            row = summary["records"][0]
            self.assertEqual(row["schema_version"], "journey_branch_impact_row_v2")
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
            self.assertEqual(row["sum_child_exact_pricing_event_count"], 1)
            self.assertEqual(row["sum_child_certificate_pricing_event_count"], 1)
            self.assertEqual(row["sum_child_fathom_event_count"], 1)
            self.assertEqual(row["max_child_lower_bound_gain"], 2.0)
            self.assertEqual(row["max_child_corrected_bound_gain"], 4.0)
            self.assertEqual(row["branch_feature_source"], "candidate_log")
            self.assertEqual(row["phased_testing_stage"], "phase2_heuristic")
            self.assertEqual(row["phased_testing_decision"], "probed_complete")
            self.assertTrue(row["phased_testing_phase0_passed"])
            self.assertTrue(row["phased_testing_phase1_lp_complete"])
            self.assertTrue(row["phased_testing_phase2_heuristic_complete"])
            self.assertEqual(row["phase1_min_child_lp_gain"], 2.25)
            self.assertEqual(row["phase1_child_lp_gain_product"], 5.0)
            self.assertEqual(row["phase1_child_width_balance"], 2)
            self.assertEqual(row["phase2_negative_child_count"], 1)
            self.assertEqual(row["phase2_negative_journey_count"], 3)
            self.assertEqual(row["phase2_negative_journey_balance_gap"], 2)
            self.assertEqual(row["phase2_best_reduced_cost"], -1.5)
            self.assertEqual(row["phase2_same_child_negative_severity"], 1.5)
            self.assertEqual(row["phase2_separate_child_negative_severity"], 0.5)
            self.assertEqual(row["phase2_negative_severity_sum"], 2.0)
            self.assertEqual(row["phase2_negative_severity_gap"], 1.0)
            self.assertEqual(row["phase2_negative_severity_balance_ratio"], 0.5)
            self.assertEqual(row["phase2_negative_child_presence_balance_gap"], 0)
            self.assertEqual(row["phase2_child_wall_time_balance_gap"], 0.015)
            self.assertTrue(row["phase2_child_status_mismatch"])
            self.assertTrue(row["phased_testing_controller_active"])
            self.assertEqual(row["phased_testing_controller_input_count"], 2)
            self.assertEqual(row["phased_testing_phase1_probe_count"], 2)
            self.assertEqual(row["phased_testing_phase2_probe_count"], 1)
            self.assertEqual(row["phased_testing_phase2_dynamic_k_excluded_count"], 1)
            self.assertEqual(row["phased_testing_phase2_negative_journey_count_total"], 3)
            self.assertEqual(row["phased_testing_phase2_negative_severity_sum_total"], 2.0)
            self.assertEqual(row["phased_testing_phase2_negative_severity_gap_max"], 1.0)
            self.assertEqual(row["phased_testing_phase2_negative_severity_balance_ratio_min"], 0.5)
            self.assertEqual(row["phased_testing_decision_counts"], {"probed_complete": 1, "skipped_by_dynamic_k": 1})
            self.assertFalse(row["phased_testing_official_bound_effect_any"])
            self.assertFalse(row["phased_testing_certificate_effect_any"])
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
            self.assertEqual(row["branch_labels"]["y_child_exact_pricing_events"], 1.0)
            self.assertEqual(row["branch_labels"]["y_child_fathom_events"], 1.0)
            self.assertEqual(row["branch_labels"]["y_child_max_safe_bound_gain"], 2.0)
            self.assertEqual(row["branch_labels"]["y_child_max_corrected_bound_gain"], 4.0)
            self.assertEqual(summary["child_probe_row_count"], 2)
            child_rows = summary["child_probe_rows"]
            self.assertEqual(child_rows[0]["schema_version"], "journey_branch_child_probe_row_v2")
            self.assertEqual(child_rows[0]["instance_id"], "branch")
            self.assertEqual(child_rows[0]["source_log_file"], str(log_path))
            self.assertEqual(child_rows[0]["child_node_id"], 1)
            self.assertEqual(child_rows[0]["child_bound_reference"], 5.0)
            self.assertEqual(child_rows[0]["child_lower_bound_gain"], 2.0)
            self.assertEqual(child_rows[0]["child_max_corrected_bound_gain"], 4.0)
            self.assertEqual(child_rows[0]["child_exact_pricing_event_count"], 1.0)
            self.assertEqual(child_rows[0]["child_labels"]["child_lower_bound_gain"], 2.0)
            self.assertEqual(child_rows[0]["child_labels"]["child_max_corrected_node_lb"], 11.0)
            self.assertEqual(child_rows[0]["child_labels"]["child_max_corrected_bound_gain"], 4.0)
            self.assertEqual(child_rows[0]["child_labels"]["child_exact_pricing_event_count"], 1.0)
            self.assertEqual(child_rows[0]["child_labels"]["child_time_to_first_certificate"], 1.5)
            self.assertEqual(child_rows[0]["child_labels"]["child_time_to_fathom"], 3.0)
            self.assertEqual(child_rows[0]["child_labels"]["child_fathomed"], 1.0)
            self.assertEqual(
                child_rows[0]["observed_branch_candidate"]["phased_testing_stage"],
                "phase2_heuristic",
            )
            self.assertEqual(
                child_rows[0]["observed_branch_candidate"]["phase2_negative_journey_count"],
                3,
            )
            self.assertEqual(
                child_rows[0]["observed_branch_candidate"]["phase2_negative_severity_sum"],
                2.0,
            )
            training_rows = summary["branch_training_rows"]
            self.assertEqual(len(training_rows), 1)
            self.assertEqual(training_rows[0]["schema_version"], "journey_branch_impact_training_row_v2")
            self.assertEqual(training_rows[0]["branch_feature_schema"], summary["branch_feature_schema"])
            self.assertEqual(training_rows[0]["branch_label_schema"], summary["branch_label_schema"])
            self.assertTrue(training_rows[0]["right_censored"])
            self.assertEqual(training_rows[0]["forced_pair"], [1, 2])
            self.assertTrue(training_rows[0]["forced_pair_matched"])
            self.assertFalse(training_rows[0]["usable_for_branch_impact_training"])
            self.assertEqual(training_rows[0]["phased_testing_stage"], "phase2_heuristic")
            self.assertEqual(training_rows[0]["phase1_min_child_lp_gain"], 2.25)
            self.assertEqual(training_rows[0]["phase2_negative_child_count"], 1)
            self.assertEqual(training_rows[0]["phase2_negative_severity_sum"], 2.0)
            self.assertEqual(training_rows[0]["phased_testing_phase1_probe_count"], 2)
            self.assertEqual(training_rows[0]["phased_testing_phase2_probe_count"], 1)
            self.assertEqual(training_rows[0]["phased_testing_phase2_negative_severity_gap_max"], 1.0)
            self.assertEqual(training_rows[0]["phased_testing_phase2_reason_counts"], {"dynamic_k_excluded": 1, "ok": 1})
            self.assertFalse(training_rows[0]["phased_testing_official_bound_effect_any"])
            self.assertFalse(training_rows[0]["phased_testing_certificate_effect_any"])
            self.assertTrue((tmp_path / "out" / "summary.json").exists())
            self.assertTrue((tmp_path / "out" / "branch_impact_rows.jsonl").exists())
            self.assertTrue((tmp_path / "out" / "branch_training_rows.jsonl").exists())
            self.assertTrue((tmp_path / "out" / "child_probe_rows.jsonl").exists())
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
            self.assertEqual(summary["child_probe_row_count"], 2)
            first_child = summary["child_probe_rows"][0]
            self.assertTrue(first_child["child_started"])
            self.assertGreaterEqual(first_child["child_labels"]["child_proof_cpu"], 0.0)

    def test_completion_bound_retry_count_excludes_ordinary_no_column_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_path = tmp_path / "retry_kinds.jsonl"
            records = [
                {"event": "journey_node_start", "node_id": 0, "depth": 0, "time": 0.0},
                {
                    "event": "journey_branch_candidates",
                    "node_id": 0,
                    "depth": 0,
                    "time": 0.1,
                    "candidate_count": 1,
                    "eligible_count": 1,
                    "selected": {"task_i": 1, "task_j": 2, "fractionality": 0.5},
                    "top": [{"task_i": 1, "task_j": 2, "fractionality": 0.5}],
                    "priority_top": [{"task_i": 1, "task_j": 2, "fractionality": 0.5}],
                },
                {
                    "event": "journey_branch",
                    "node_id": 0,
                    "depth": 0,
                    "time": 0.2,
                    "left": "RF(1,2)=same_vehicle",
                    "right": "RF(1,2)=separate_vehicle",
                },
                {
                    "event": "journey_child_queued",
                    "parent_node_id": 0,
                    "child_node_id": 1,
                    "depth": 1,
                    "time": 0.3,
                    "constraint": "RF(1,2)=same_vehicle",
                    "lower_bound": 0.0,
                    "lower_bound_exact": True,
                },
                {
                    "event": "journey_child_queued",
                    "parent_node_id": 0,
                    "child_node_id": 2,
                    "depth": 1,
                    "time": 0.4,
                    "constraint": "RF(1,2)=separate_vehicle",
                    "lower_bound": 0.0,
                    "lower_bound_exact": True,
                },
                {"event": "journey_node_start", "node_id": 1, "depth": 1, "time": 1.0},
                {
                    "event": "journey_exact_pricing_retry",
                    "node_id": 1,
                    "depth": 1,
                    "time": 1.1,
                    "previous_status": "INCOMPLETE",
                    "previous_reason": "profile_exhausted_no_column",
                },
                {
                    "event": "journey_exact_pricing_completion_bound_retry",
                    "node_id": 1,
                    "depth": 1,
                    "time": 1.2,
                    "pricing_kind": "exact_completion_bound_retry",
                    "previous_status": "INCOMPLETE",
                    "previous_reason": "profile_exhausted_no_column",
                },
                {"event": "journey_finish", "status": "TIME_LIMIT", "time": 2.0},
            ]
            log_path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )

            summary = build_branch_impact([log_path], tmp_path / "out", tmp_path / "report.md")

            row = summary["records"][0]
            self.assertEqual(row["sum_child_completion_bound_retry_count"], 1)
            self.assertEqual(row["children"][0]["completion_bound_retry_count"], 1)
            self.assertEqual(row["children"][1]["completion_bound_retry_count"], 0)
            self.assertEqual(summary["aggregate"]["total_child_completion_bound_retries"], 1)
            self.assertEqual(
                summary["child_probe_rows"][0]["child_completion_bound_retry_count"],
                1.0,
            )


if __name__ == "__main__":
    unittest.main()

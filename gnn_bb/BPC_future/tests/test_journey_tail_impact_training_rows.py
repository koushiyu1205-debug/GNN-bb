from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_journey_tail_impact_training_rows import build_tail_impact


class JourneyTailImpactTrainingRowsTests(unittest.TestCase):
    def test_tail_action_rows_backfill_class_metadata_without_feature_leakage(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            tail_action_dir = tmp_path / "tail_action"
            tail_action_dir.mkdir()
            row = {
                "schema_version": "journey_tail_action_controller_audit_v2",
                "log_file": "legacy_tail_action.jsonl",
                "node_id": 7,
                "depth": 2,
                "cg_iter": 4,
                "tail_action": "EARLY_BRANCH",
                "tail_action_reason": "rmp_below_incumbent_pricing_unproductive_for_fathom",
                "tail_action_no_column": True,
                "no_column_branch_task_i": 4,
                "no_column_branch_task_j": 12,
            }
            (tail_action_dir / "early_branch_trigger_rows.jsonl").write_text(
                json.dumps(row, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            summary = build_tail_impact(
                [],
                [],
                tmp_path / "out",
                tmp_path / "report.md",
                tail_action_inputs=[tail_action_dir],
            )

            self.assertEqual(summary["tail_action_class_counts"], {"D_EARLY_BRANCH": 1})
            self.assertEqual(summary["tail_action_productivity_class_counts"], {"unknown": 1})
            fused = summary["rows"][0]
            self.assertEqual(fused["tail_action_class"], "D_EARLY_BRANCH")
            self.assertEqual(fused["tail_action_productivity_class"], "unknown")
            self.assertNotIn("tail_action_class", summary["feature_schema"])
            self.assertNotIn("tail_action_productivity_class", summary["feature_schema"])

    def test_build_tail_impact_fuses_weak_and_branch_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            weak_dir = tmp_path / "weak"
            weak_dir.mkdir()
            branch_dir = tmp_path / "branch"
            branch_dir.mkdir()
            tail_action_dir = tmp_path / "tail_action"
            tail_action_dir.mkdir()
            tail_counterfactual_dir = tmp_path / "tail_counterfactual"
            tail_counterfactual_dir.mkdir()
            late_negative_dir = tmp_path / "late_negative"
            late_negative_dir.mkdir()
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
            tail_action_row = {
                "schema_version": "journey_tail_action_controller_audit_v2",
                "log_file": "tail_action.jsonl",
                "time": 30.0,
                "node_id": 7,
                "depth": 2,
                "cg_iter": 4,
                "tail_action": "EARLY_BRANCH",
                "tail_action_class": "D_EARLY_BRANCH",
                "tail_action_reason": "rmp_below_incumbent_pricing_unproductive_for_fathom",
                "tail_action_productivity_class": "pricing_unproductive_no_negative_columns",
                "tail_action_no_column": True,
                "no_column_branch_task_i": 4,
                "no_column_branch_task_j": 12,
                "no_column_branch_pool_max_child_width": 111,
                "no_column_branch_pool_total_child_width": 202,
                "no_column_branch_pool_balance_gap": 20,
                "child_direct_started_count": 1,
                "child_direct_unstarted_count": 1,
                "child_subtree_node_count": 2,
                "child_subtree_pricing_event_count": 3,
                "child_subtree_negative_pricing_event_count": 1,
                "child_subtree_completion_retry_count": 1,
                "child_subtree_completion_retry_pricing_event_count": 1,
                "child_subtree_completion_retry_low_min_fill_count": 1,
                "child_subtree_completion_retry_min_harvest_min_fill": 4,
                "child_subtree_completion_retry_max_harvest_min_fill": 4,
                "child_subtree_completion_retry_harvest_min_fill_values": "4:1",
                "child_subtree_completion_retry_found_negative_count": 0,
                "child_subtree_completion_retry_certified_no_negative_count": 1,
                "child_subtree_completion_retry_incomplete_count": 0,
                "child_subtree_early_branch_trigger_count": 2,
                "child_subtree_no_column_early_branch_trigger_count": 1,
                "child_subtree_observed_wall_span": 36.14,
            }
            tail_counterfactual_row = {
                "schema_version": "journey_tail_action_counterfactual_delta_v1",
                "diagnostic_only": True,
                "runs_bpc_or_pricing": False,
                "production_ready": False,
                "certificate_effect": False,
                "official_bound_effect": False,
                "instance": "BPC_future/logical_graph/tasks_020/sector-wave/demo.json",
                "node_id": 7,
                "depth": 2,
                "baseline_pair": [4, 12],
                "alternative_pair": [4, 11],
                "baseline_status": "EXTERNAL_TIME_LIMIT",
                "alternative_status": "EXTERNAL_TIME_LIMIT",
                "baseline_tail": {
                    "tail_cost": 59.2,
                    "negative_pricing_events": 31,
                    "completion_retries": 14,
                    "no_column_chain": 9,
                },
                "alternative_tail": {
                    "tail_cost": 26.25,
                    "pricing_events": 25,
                    "negative_pricing_events": 10,
                    "completion_retries": 6,
                    "no_column_chain": 0,
                    "observed_wall_span": 199.5,
                },
                "deltas": {
                    "local_tail_cost_delta": -32.95,
                    "local_negative_pricing_events_delta": -21,
                    "local_completion_retries_delta": -8,
                    "local_no_column_chain_delta": -9,
                    "wall_time_delta": -0.002,
                    "pricing_calls_delta": -12,
                    "exact_pricing_calls_delta": -9,
                    "node_count_delta": -1,
                    "solving_time_delta": -3.4,
                    "primal_bound_delta": 0.0,
                    "dual_bound_delta": 0.0,
                    "gap_delta": -0.01,
                    "completion_retry_trigger_count_delta": -2,
                    "completion_retry_pricing_count_delta": -2,
                    "completion_retry_work_time_proxy_delta": -3.5,
                    "completion_retry_generated_sequences_delta": -100,
                    "completion_retry_evaluated_timed_trips_delta": -50,
                },
                "labels": {
                    "y_local_tail_improved": 1.0,
                    "y_whole_run_improved": 0.0,
                    "y_budget_dominant_improvement": 0.0,
                    "y_local_improved_but_whole_run_not": 1.0,
                    "y_timeout_resolved": 0.0,
                    "y_timeout_regression": 0.0,
                    "y_right_censored_counterfactual": 1.0,
                },
            }
            late_negative_row = {
                "schema_version": "journey_late_negative_tail_row_v1",
                "log_file": "late.jsonl",
                "tail_class": "true_negative_active_support_changing",
                "has_true_negative": True,
                "has_weak_filtered": False,
                "node_id": 8,
                "depth": 2,
                "cg_iter": 5,
                "time": 42.0,
                "pricing_kind": "exact",
                "pricing_state": "FOUND_NEGATIVE",
                "reason": "negative_journey",
                "negative_journeys": 3,
                "selected_trips": 2,
                "added_journeys": 2,
                "active_changed_task_set_count": 1,
                "inactive_changed_task_set_count": 1,
                "new_task_set_count": 2,
                "replacement_task_set_count": 0,
            }
            (weak_dir / "weak_negative_tail_rows.jsonl").write_text(
                json.dumps(weak_row, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (branch_dir / "branch_training_rows.jsonl").write_text(
                json.dumps(branch_row, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (tail_action_dir / "early_branch_trigger_rows.jsonl").write_text(
                json.dumps(tail_action_row, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (tail_counterfactual_dir / "tail_action_counterfactual_delta_rows.jsonl").write_text(
                json.dumps(tail_counterfactual_row, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (late_negative_dir / "late_negative_tail_rows.jsonl").write_text(
                json.dumps(late_negative_row, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            summary = build_tail_impact(
                [weak_dir],
                [branch_dir],
                tmp_path / "out",
                tmp_path / "report.md",
                tail_action_inputs=[tail_action_dir],
                tail_action_counterfactual_inputs=[tail_counterfactual_dir],
                late_negative_inputs=[late_negative_dir],
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["certificate_effect"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertTrue(summary["hard_negative_catalog_ready"])
            self.assertFalse(summary["minimal_tail_signal_ready"])
            self.assertFalse(summary["strict_tail_training_ready"])
            self.assertFalse(summary["contrastive_tail_training_ready"])
            self.assertFalse(summary["tail_label_training_ready"])
            self.assertIn("tail_counterfactual_wall_time_delta", summary["outcome_schema"])
            self.assertIn("tail_counterfactual_exact_pricing_calls_delta", summary["outcome_schema"])
            self.assertIn("tail_counterfactual_gap_delta", summary["outcome_schema"])
            self.assertIn(
                "tail_counterfactual_completion_retry_work_time_proxy_delta",
                summary["outcome_schema"],
            )
            self.assertNotIn("tail_counterfactual_wall_time_delta", summary["feature_schema"])
            self.assertNotIn("tail_counterfactual_exact_pricing_calls_delta", summary["feature_schema"])
            self.assertNotIn("tail_counterfactual_gap_delta", summary["feature_schema"])
            self.assertNotIn(
                "tail_counterfactual_completion_retry_work_time_proxy_delta",
                summary["feature_schema"],
            )
            self.assertIn("branch_child_completion_bound_retries", summary["outcome_schema"])
            self.assertNotIn("branch_child_completion_bound_retries", summary["feature_schema"])
            self.assertEqual(summary["training_row_count"], 5)
            self.assertEqual(summary["deduplicated_row_count"], 0)
            self.assertEqual(summary["duplicate_context_action_count"], 0)
            self.assertEqual(summary["weak_row_count"], 1)
            self.assertEqual(summary["branch_row_count"], 1)
            self.assertEqual(summary["tail_action_row_count"], 1)
            self.assertEqual(summary["tail_action_counterfactual_row_count"], 1)
            self.assertEqual(summary["late_negative_row_count"], 1)
            self.assertEqual(
                summary["source_counts"],
                {
                    "branch_impact": 1,
                    "late_negative_tail": 1,
                    "tail_action_counterfactual_delta": 1,
                    "tail_action_proof_cost": 1,
                    "weak_negative_tail": 1,
                },
            )
            self.assertEqual(summary["tail_action_class_counts"], {"D_EARLY_BRANCH": 1})
            self.assertEqual(
                summary["tail_action_productivity_class_counts"],
                {"pricing_unproductive_no_negative_columns": 1},
            )
            self.assertEqual(summary["label_positive_counts"]["y_tail_risk"], 5)
            self.assertEqual(summary["label_positive_counts"]["y_weak_negative_filtered"], 1)
            self.assertEqual(summary["label_positive_counts"]["y_completion_bound_tail"], 2)
            self.assertEqual(summary["label_positive_counts"]["y_tail_action_no_column"], 1)
            self.assertEqual(summary["label_positive_counts"]["y_tail_action_counterfactual"], 1)
            self.assertEqual(summary["label_positive_counts"]["y_tail_min_fill_completion_retry"], 1)
            self.assertEqual(summary["label_positive_counts"]["y_tail_min_fill_found_negative"], 0)
            self.assertEqual(summary["label_positive_counts"]["y_tail_min_fill_certified_no_negative"], 1)
            self.assertEqual(summary["label_positive_counts"]["y_local_tail_improved"], 1)
            self.assertEqual(summary["label_positive_counts"]["y_whole_run_improved"], 0)
            self.assertEqual(summary["label_positive_counts"]["y_budget_dominant_improvement"], 0)
            self.assertEqual(
                summary["label_positive_counts"]["y_local_improved_but_whole_run_not"],
                1,
            )
            self.assertEqual(summary["label_positive_counts"]["y_right_censored_counterfactual"], 1)
            self.assertEqual(summary["label_positive_counts"]["y_late_true_negative"], 1)
            self.assertEqual(summary["label_positive_counts"]["y_late_active_support_changing"], 1)
            self.assertEqual(summary["regression_label_totals"]["child_negative_pricing_events"], 13)
            self.assertEqual(summary["regression_label_totals"]["child_unstarted"], 1)
            self.assertEqual(summary["regression_label_totals"]["subtree_no_column_chain"], 1)
            self.assertEqual(summary["regression_label_totals"]["local_tail_improved"], 1)
            self.assertEqual(summary["regression_label_totals"]["whole_run_improved"], 0)
            self.assertEqual(summary["regression_label_totals"]["budget_dominant_improvement"], 0)
            self.assertEqual(
                summary["regression_label_totals"]["local_improved_but_whole_run_not"],
                1,
            )
            self.assertEqual(summary["regression_label_totals"]["late_true_negative"], 1)
            self.assertEqual(summary["regression_label_totals"]["late_active_support_changing"], 1)
            self.assertEqual(summary["regression_label_totals"]["tail_min_fill_completion_retry"], 1)
            self.assertEqual(summary["regression_label_totals"]["tail_min_fill_certified_no_negative"], 1)
            rows = summary["rows"]
            weak_fused = next(row for row in rows if row["source_type"] == "weak_negative_tail")
            branch_fused = next(row for row in rows if row["source_type"] == "branch_impact")
            tail_action_fused = next(row for row in rows if row["source_type"] == "tail_action_proof_cost")
            tail_counterfactual_fused = next(
                row for row in rows if row["source_type"] == "tail_action_counterfactual_delta"
            )
            late_fused = next(row for row in rows if row["source_type"] == "late_negative_tail")
            self.assertEqual(weak_fused["labels"]["y_useful_tail_reduction"], 0.0)
            self.assertEqual(weak_fused["labels"]["y_weak_negative_filtered"], 1.0)
            self.assertEqual(branch_fused["labels"]["y_completion_bound_tail"], 1.0)
            self.assertEqual(branch_fused["labels"]["y_inactive_only"], 1.0)
            self.assertEqual(tail_action_fused["labels"]["y_tail_action_no_column"], 1.0)
            self.assertEqual(tail_action_fused["labels"]["y_child_unstarted"], 1.0)
            self.assertEqual(tail_action_fused["labels"]["y_subtree_no_column_chain"], 1.0)
            self.assertEqual(tail_action_fused["labels"]["y_tail_min_fill_completion_retry"], 1.0)
            self.assertEqual(tail_action_fused["labels"]["y_tail_min_fill_found_negative"], 0.0)
            self.assertEqual(tail_action_fused["labels"]["y_tail_min_fill_certified_no_negative"], 1.0)
            self.assertEqual(tail_action_fused["tail_action_class"], "D_EARLY_BRANCH")
            self.assertEqual(
                tail_action_fused["tail_action_productivity_class"],
                "pricing_unproductive_no_negative_columns",
            )
            self.assertNotIn("tail_action_class", tail_action_fused["decision_feature_schema"])
            self.assertNotIn(
                "tail_action_productivity_class",
                tail_action_fused["decision_feature_schema"],
            )
            self.assertEqual(tail_counterfactual_fused["labels"]["y_useful_tail_reduction"], 0.0)
            self.assertEqual(tail_counterfactual_fused["labels"]["y_tail_action_counterfactual"], 1.0)
            self.assertEqual(tail_counterfactual_fused["labels"]["y_local_tail_improved"], 1.0)
            self.assertEqual(tail_counterfactual_fused["labels"]["y_whole_run_improved"], 0.0)
            self.assertEqual(tail_counterfactual_fused["labels"]["y_budget_dominant_improvement"], 0.0)
            self.assertEqual(
                tail_counterfactual_fused["labels"]["y_local_improved_but_whole_run_not"],
                1.0,
            )
            self.assertEqual(
                tail_counterfactual_fused["tail_class"],
                "tail_action_local_only_hard_negative",
            )
            self.assertEqual(
                tail_counterfactual_fused["decision_feature_schema"],
                summary["feature_schema"],
            )
            self.assertEqual(tail_counterfactual_fused["decision_features"], tail_counterfactual_fused["features"])
            self.assertNotIn(
                "tail_action_subtree_completion_retry_low_min_fill",
                tail_action_fused["decision_feature_schema"],
            )
            tail_action_outcomes = dict(
                zip(tail_action_fused["outcome_schema"], tail_action_fused["outcomes"], strict=False)
            )
            self.assertEqual(tail_action_outcomes["tail_action_subtree_completion_retry_low_min_fill"], 1.0)
            self.assertEqual(
                tail_action_outcomes["tail_action_subtree_completion_retry_min_harvest_min_fill"],
                4.0,
            )
            self.assertEqual(
                tail_action_outcomes["tail_action_subtree_completion_retry_certified_no_negative"],
                1.0,
            )
            counterfactual_outcomes = dict(
                zip(
                    tail_counterfactual_fused["outcome_schema"],
                    tail_counterfactual_fused["outcomes"],
                    strict=False,
                )
            )
            self.assertEqual(counterfactual_outcomes["tail_counterfactual_local_tail_cost_delta"], -32.95)
            self.assertEqual(counterfactual_outcomes["tail_counterfactual_completion_retry_delta"], -8.0)
            self.assertEqual(counterfactual_outcomes["tail_counterfactual_exact_pricing_calls_delta"], -9.0)
            self.assertEqual(counterfactual_outcomes["tail_counterfactual_gap_delta"], -0.01)
            self.assertEqual(
                counterfactual_outcomes[
                    "tail_counterfactual_completion_retry_work_time_proxy_delta"
                ],
                -3.5,
            )
            self.assertEqual(
                counterfactual_outcomes[
                    "tail_counterfactual_completion_retry_pricing_count_delta"
                ],
                -2.0,
            )
            self.assertEqual(counterfactual_outcomes["branch_child_completion_bound_retries"], 6.0)
            self.assertEqual(late_fused["labels"]["y_late_true_negative"], 1.0)
            self.assertEqual(late_fused["labels"]["y_late_active_support_changing"], 1.0)
            self.assertEqual(len(branch_fused["features"]), len(summary["feature_schema"]))
            self.assertEqual(len(tail_action_fused["features"]), len(summary["feature_schema"]))
            self.assertEqual(len(tail_counterfactual_fused["features"]), len(summary["feature_schema"]))
            self.assertEqual(len(late_fused["features"]), len(summary["feature_schema"]))
            self.assertTrue((tmp_path / "out" / "summary.json").exists())
            self.assertTrue((tmp_path / "out" / "tail_impact_training_rows.jsonl").exists())
            self.assertIn("certificate_effect = false", (tmp_path / "report.md").read_text(encoding="utf-8"))

    def test_tail_training_ready_requires_strict_context_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            tail_counterfactual_dir = tmp_path / "tail_counterfactual"
            tail_counterfactual_dir.mkdir()
            rows = [
                {
                    "schema_version": "journey_tail_action_counterfactual_delta_v1",
                    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/a.json",
                    "node_id": 0,
                    "depth": 0,
                    "baseline_pair": [1, 2],
                    "alternative_pair": [2, 3],
                    "baseline_status": "OPTIMAL",
                    "alternative_status": "OPTIMAL",
                    "baseline_tail": {"tail_cost": 10.0},
                    "alternative_tail": {"tail_cost": 5.0},
                    "deltas": {"local_tail_cost_delta": -5.0, "wall_time_delta": -30.0},
                    "labels": {
                        "y_local_tail_improved": 1.0,
                        "y_whole_run_improved": 1.0,
                        "y_local_improved_but_whole_run_not": 0.0,
                        "y_timeout_resolved": 0.0,
                        "y_timeout_regression": 0.0,
                        "y_right_censored_counterfactual": 0.0,
                    },
                },
                {
                    "schema_version": "journey_tail_action_counterfactual_delta_v1",
                    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/a.json",
                    "node_id": 1,
                    "depth": 1,
                    "baseline_pair": [3, 4],
                    "alternative_pair": [4, 5],
                    "baseline_status": "EXTERNAL_TIME_LIMIT",
                    "alternative_status": "EXTERNAL_TIME_LIMIT",
                    "baseline_tail": {"tail_cost": 30.0},
                    "alternative_tail": {"tail_cost": 20.0},
                    "deltas": {"local_tail_cost_delta": -10.0, "wall_time_delta": 0.0},
                    "labels": {
                        "y_local_tail_improved": 1.0,
                        "y_whole_run_improved": 0.0,
                        "y_local_improved_but_whole_run_not": 1.0,
                        "y_timeout_resolved": 0.0,
                        "y_timeout_regression": 0.0,
                        "y_right_censored_counterfactual": 1.0,
                    },
                },
            ]
            (tail_counterfactual_dir / "tail_action_counterfactual_delta_rows.jsonl").write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

            summary = build_tail_impact(
                [],
                [],
                tmp_path / "out",
                tmp_path / "report.md",
                tail_action_counterfactual_inputs=[tail_counterfactual_dir],
            )

            self.assertTrue(summary["minimal_tail_signal_ready"])
            self.assertFalse(summary["strict_tail_training_ready"])
            self.assertFalse(summary["contrastive_tail_training_ready"])
            self.assertFalse(summary["tail_label_training_ready"])
            self.assertEqual(summary["whole_run_positive_context_count"], 1)
            self.assertEqual(summary["whole_run_positive_instance_count"], 1)
            self.assertEqual(summary["whole_run_positive_time_window_family_count"], 1)
            self.assertEqual(summary["local_only_hard_negative_count"], 1)
            self.assertEqual(summary["positive_holdout_context_count"], 0)

    def test_budget_dominant_improvement_is_not_promoted_to_useful_tail_reduction(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            tail_counterfactual_dir = tmp_path / "tail_counterfactual"
            tail_counterfactual_dir.mkdir()
            row = {
                "schema_version": "journey_tail_action_counterfactual_delta_v2",
                "instance": "BPC_future/logical_graph/tasks_020/random-wave/a.json",
                "node_id": 0,
                "depth": 0,
                "baseline_pair": [1, 2],
                "alternative_pair": [2, 3],
                "baseline_status": "EXTERNAL_TIME_LIMIT",
                "alternative_status": "EXTERNAL_TIME_LIMIT",
                "baseline_tail": {"tail_cost": 20.0},
                "alternative_tail": {"tail_cost": 12.0},
                "deltas": {
                    "local_tail_cost_delta": -8.0,
                    "wall_time_delta": 0.0,
                    "pricing_calls_delta": -20.0,
                    "exact_pricing_calls_delta": -10.0,
                    "node_count_delta": 0.0,
                    "gap_delta": -0.02,
                },
                "labels": {
                    "y_local_tail_improved": 1.0,
                    "y_whole_run_improved": 0.0,
                    "y_budget_dominant_improvement": 1.0,
                    "y_local_improved_but_whole_run_not": 0.0,
                    "y_timeout_resolved": 0.0,
                    "y_timeout_regression": 0.0,
                    "y_right_censored_counterfactual": 1.0,
                },
            }
            (tail_counterfactual_dir / "tail_action_counterfactual_delta_rows.jsonl").write_text(
                json.dumps(row, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            summary = build_tail_impact(
                [],
                [],
                tmp_path / "out",
                tmp_path / "report.md",
                tail_action_counterfactual_inputs=[tail_counterfactual_dir],
            )

            self.assertEqual(summary["label_positive_counts"]["y_budget_dominant_improvement"], 1)
            self.assertEqual(
                summary["counterfactual_label_type_counts"],
                {"budget_dominant_improvement": 1},
            )
            self.assertEqual(summary["label_positive_counts"]["y_whole_run_improved"], 0)
            self.assertEqual(summary["label_positive_counts"]["y_useful_tail_reduction"], 0)
            self.assertFalse(summary["minimal_tail_signal_ready"])
            self.assertFalse(summary["strict_tail_training_ready"])
            fused = summary["rows"][0]
            self.assertEqual(fused["tail_class"], "tail_action_budget_dominant_improvement")
            self.assertEqual(fused["counterfactual_label_type"], "budget_dominant_improvement")
            self.assertEqual(fused["outcome_label_type"], "budget_dominant_improvement")
            self.assertEqual(fused["labels"]["y_useful_tail_reduction"], 0.0)
            self.assertEqual(fused["labels"]["y_budget_dominant_improvement"], 1.0)
            self.assertEqual(fused["labels"]["y_tail_risk"], 0.0)
            outcomes = dict(zip(fused["outcome_schema"], fused["outcomes"], strict=False))
            self.assertEqual(outcomes["tail_counterfactual_exact_pricing_calls_delta"], -10.0)
            self.assertEqual(outcomes["tail_counterfactual_gap_delta"], -0.02)
            self.assertNotIn("tail_counterfactual_gap_delta", fused["decision_feature_schema"])


if __name__ == "__main__":
    unittest.main()

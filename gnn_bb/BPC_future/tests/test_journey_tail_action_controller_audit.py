from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.audit_journey_tail_action_controller import audit_tail_actions


class JourneyTailActionControllerAuditTests(unittest.TestCase):
    def test_audit_tail_actions_summarizes_controller_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_dir = tmp_path / "logs"
            log_dir.mkdir()
            rows = [
                {
                    "event": "journey_corrected_node_bound_audit",
                    "time": 10.0,
                    "node_id": 0,
                    "depth": 0,
                    "cg_iter": 5,
                    "pricing_kind": "exact_completion_bound_retry",
                    "tail_action": "FRONTIER_REFINEMENT",
                    "tail_action_reason": "fathom_possible_sparse_low_waterline",
                    "fathom_possible_if_rc_zero": True,
                    "recent_active_support_additions": 1,
                    "recent_rmp_objective_progress": 0.25,
                    "recent_true_rc_productivity": 0,
                    "frontier_micro_expansion_attempted": 2,
                    "frontier_micro_expansion_expanded": 1,
                },
                {
                    "event": "journey_corrected_node_bound_audit",
                    "time": 20.0,
                    "node_id": 1,
                    "depth": 1,
                    "cg_iter": 3,
                    "pricing_kind": "exact_completion_bound_retry",
                    "tail_action": "BROAD_PLATEAU_FALLBACK",
                    "tail_action_reason": "fathom_possible_broad_low_waterline",
                    "fathom_possible_if_rc_zero": True,
                    "recent_active_support_additions": 0,
                    "recent_rmp_objective_progress": 0.0,
                    "recent_true_rc_productivity": 0,
                    "frontier_micro_expansion_attempted": 0,
                    "frontier_floor_band_count_10": 2704,
                },
                {
                    "event": "journey_corrected_node_bound_audit",
                    "time": 30.0,
                    "node_id": 2,
                    "depth": 1,
                    "cg_iter": 1,
                    "pricing_kind": "exact_completion_bound_retry",
                    "tail_action": "EARLY_BRANCH",
                    "tail_action_reason": "rmp_below_incumbent_pricing_unproductive_for_fathom",
                    "fathom_possible_if_rc_zero": False,
                    "recent_true_rc_productivity": 0,
                },
                {
                    "event": "journey_early_branch_trigger",
                    "time": 31.0,
                    "node_id": 2,
                    "depth": 1,
                    "cg_iter": 2,
                    "trigger": "tail_action_controller",
                    "tail_action": "EARLY_BRANCH",
                    "tail_action_no_column": True,
                    "reason": "rmp_below_incumbent_weak_columns_no_active_or_objective_progress",
                    "exact_bound_available": False,
                    "child_lower_bound_exact": False,
                    "recent_active_support_additions": 0,
                    "recent_rmp_objective_progress": 0.0,
                    "recent_true_rc_productivity": 1,
                    "previous_status": "OPTIMAL",
                    "previous_reason": "no_negative_journey",
                    "previous_pricing_state": "LOCAL_NO_COLUMN_UNCERTIFIED",
                    "no_column_branch_task_i": 1,
                    "no_column_branch_task_j": 2,
                    "no_column_branch_pool_max_child_width": 3,
                    "no_column_branch_pool_total_child_width": 5,
                    "no_column_branch_width_guard_reason": "ok",
                },
                {
                    "event": "journey_tail_action_no_column_early_branch_gate",
                    "time": 31.5,
                    "node_id": 3,
                    "depth": 1,
                    "cg_iter": 2,
                    "gate_passed": False,
                    "gate_reason": "before_final_probe_disabled",
                    "tail_action": "EARLY_BRANCH",
                    "tail_action_reason": "rmp_below_incumbent_pricing_unproductive_for_fathom",
                    "tail_action_before_final_probe": True,
                    "rmp_to_incumbent_gap": 2.0,
                    "recent_true_rc_productivity": 0,
                    "previous_status": "OPTIMAL",
                    "previous_reason": "no_negative_journey",
                    "previous_pricing_state": "LOCAL_NO_COLUMN_UNCERTIFIED",
                    "exact_bound_available": False,
                    "child_lower_bound_exact": False,
                },
                {
                    "event": "journey_child_queued",
                    "time": 32.0,
                    "parent_node_id": 2,
                    "child_node_id": 4,
                    "depth": 2,
                    "allowed_current_journeys": 10,
                    "queue_priority_width": -1,
                    "lower_bound_exact": False,
                },
                {
                    "event": "journey_child_queued",
                    "time": 33.0,
                    "parent_node_id": 2,
                    "child_node_id": 5,
                    "depth": 2,
                    "allowed_current_journeys": 15,
                    "queue_priority_width": -1,
                    "lower_bound_exact": False,
                },
                {
                    "event": "journey_node_start",
                    "time": 34.0,
                    "node_id": 4,
                    "depth": 2,
                    "lower_bound_exact": False,
                },
                {
                    "event": "journey_pricing",
                    "time": 35.0,
                    "node_id": 4,
                    "depth": 2,
                    "cg_iter": 1,
                    "pricing_kind": "exact",
                    "pricing_state": "FOUND_NEGATIVE",
                    "reason": "negative_journey_requires_column_addition",
                    "best_reduced_cost": -0.5,
                },
                {
                    "event": "journey_exact_pricing_completion_bound_retry",
                    "time": 36.0,
                    "node_id": 4,
                    "depth": 2,
                    "cg_iter": 1,
                    "trigger": "profile_exhausted_no_column",
                },
                {
                    "event": "journey_corrected_node_bound_audit",
                    "time": 40.0,
                    "node_id": 4,
                    "depth": 2,
                    "cg_iter": 1,
                    "pricing_kind": "exact",
                    "tail_action": "CONTINUE_COLUMN_GENERATION",
                    "tail_action_reason": "rmp_below_incumbent_pricing_active_support_productive",
                    "fathom_possible_if_rc_zero": False,
                    "recent_active_support_additions": 1,
                    "recent_rmp_objective_progress": 0.5,
                    "recent_true_rc_productivity": 3,
                },
                {
                    "event": "journey_pricing",
                    "tail_action": "SHOULD_NOT_COUNT",
                },
            ]
            (log_dir / "run.jsonl").write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

            summary = audit_tail_actions(
                [log_dir],
                tmp_path / "out",
                tmp_path / "report.md",
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["certificate_effect"])
            self.assertEqual(summary["log_file_count"], 1)
            self.assertEqual(summary["row_count"], 4)
            self.assertEqual(summary["a_frontier_refinement_count"], 1)
            self.assertEqual(summary["b_broad_plateau_count"], 1)
            self.assertEqual(summary["d_early_branch_count"], 1)
            self.assertEqual(summary["c_continue_cg_count"], 1)
            self.assertEqual(summary["unknown_action_count"], 0)
            self.assertEqual(summary["fathom_possible_if_rc_zero_count"], 2)
            self.assertEqual(summary["micro_expansion_attempt_row_count"], 1)
            self.assertEqual(summary["recent_active_support_addition_row_count"], 2)
            self.assertEqual(summary["recent_rmp_objective_progress_row_count"], 2)
            self.assertEqual(summary["early_branch_trigger_count"], 1)
            self.assertEqual(summary["tail_action_early_branch_trigger_count"], 1)
            self.assertEqual(summary["tail_action_no_column_early_branch_trigger_count"], 1)
            self.assertEqual(summary["nonexact_early_branch_trigger_count"], 1)
            self.assertEqual(summary["no_column_gate_row_count"], 1)
            self.assertEqual(summary["no_column_gate_before_final_probe_count"], 1)
            self.assertEqual(summary["no_column_gate_before_final_probe_disabled_count"], 1)
            self.assertEqual(summary["no_column_gate_d_early_branch_count"], 1)
            self.assertEqual(summary["no_column_gate_before_final_probe_disabled_d_count"], 1)
            self.assertEqual(
                summary["no_column_gate_reason_counts"]["before_final_probe_disabled"],
                1,
            )
            self.assertEqual(summary["tail_action_queued_child_count"], 2)
            self.assertEqual(summary["tail_action_nonexact_queued_child_count"], 2)
            self.assertEqual(summary["tail_action_observed_child_audit_count"], 1)
            self.assertEqual(summary["tail_action_child_min_queue_priority_width"], -1)
            self.assertEqual(summary["tail_action_child_max_queue_priority_width"], -1)
            self.assertTrue((tmp_path / "out" / "summary.json").exists())
            self.assertTrue((tmp_path / "out" / "tail_action_rows.jsonl").exists())
            self.assertTrue((tmp_path / "out" / "tail_action_rows.csv").exists())
            self.assertTrue((tmp_path / "out" / "early_branch_trigger_rows.jsonl").exists())
            self.assertTrue((tmp_path / "out" / "no_column_gate_rows.jsonl").exists())
            self.assertTrue((tmp_path / "out" / "no_column_gate_rows.csv").exists())
            gate_rows = [
                json.loads(line)
                for line in (tmp_path / "out" / "no_column_gate_rows.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            self.assertEqual(gate_rows[0]["gate_reason"], "before_final_probe_disabled")
            self.assertEqual(gate_rows[0]["tail_action"], "EARLY_BRANCH")
            trigger_rows = [
                json.loads(line)
                for line in (tmp_path / "out" / "early_branch_trigger_rows.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            self.assertTrue(trigger_rows[0]["tail_action_no_column"])
            self.assertEqual(trigger_rows[0]["previous_pricing_state"], "LOCAL_NO_COLUMN_UNCERTIFIED")
            self.assertEqual(trigger_rows[0]["no_column_branch_task_i"], 1)
            self.assertEqual(trigger_rows[0]["no_column_branch_pool_max_child_width"], 3)
            self.assertEqual(trigger_rows[0]["no_column_branch_width_guard_reason"], "ok")
            self.assertEqual(trigger_rows[0]["queued_child_count"], 2)
            self.assertEqual(trigger_rows[0]["queued_child_nonexact_count"], 2)
            self.assertEqual(trigger_rows[0]["queued_child_min_queue_priority_width"], -1)
            self.assertEqual(trigger_rows[0]["queued_child_max_queue_priority_width"], -1)
            self.assertEqual(trigger_rows[0]["observed_child_audit_count"], 1)
            self.assertEqual(trigger_rows[0]["child_direct_started_count"], 1)
            self.assertEqual(trigger_rows[0]["child_direct_unstarted_count"], 1)
            self.assertEqual(trigger_rows[0]["child_subtree_node_count"], 2)
            self.assertEqual(trigger_rows[0]["child_subtree_node_start_count"], 1)
            self.assertEqual(trigger_rows[0]["child_subtree_pricing_event_count"], 1)
            self.assertEqual(trigger_rows[0]["child_subtree_negative_pricing_event_count"], 1)
            self.assertEqual(trigger_rows[0]["child_subtree_completion_retry_count"], 1)
            self.assertEqual(trigger_rows[0]["child_subtree_tail_action_audit_count"], 1)
            self.assertIn("D/early branch: 1", (tmp_path / "report.md").read_text(encoding="utf-8"))
            self.assertIn("tail-action early branch triggers: 1", (tmp_path / "report.md").read_text(encoding="utf-8"))
            self.assertIn(
                "tail-action no-column early branch triggers: 1",
                (tmp_path / "report.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "negative_pricing=1 cb_retry=1",
                (tmp_path / "report.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "no-column before-final-probe disabled D rows: 1",
                (tmp_path / "report.md").read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()

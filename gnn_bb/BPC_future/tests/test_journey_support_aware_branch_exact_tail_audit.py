from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.audit_journey_support_aware_branch_exact_tail import (
    summarize,
    write_outputs,
)


class JourneySupportAwareBranchExactTailAuditTests(unittest.TestCase):
    def test_summarize_branch_exact_support_categories(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_path = tmp_path / "support_tail.jsonl"
            records = [
                {
                    "event": "journey_gat_target_mode_admission",
                    "node_id": 0,
                    "depth": 0,
                    "cg_iter": 30,
                    "time": 50.0,
                    "pricing_kind": "exact",
                    "status": "bypassed",
                    "reason": "pricing_kind_not_mutated",
                    "candidate_journeys": 10,
                    "support_aware_admission_enabled": True,
                    "support_candidate_active_support_changing_journeys": 10,
                },
                {
                    "event": "journey_gat_target_mode_admission",
                    "node_id": 1,
                    "depth": 1,
                    "cg_iter": 1,
                    "time": 100.0,
                    "pricing_kind": "exact",
                    "status": "bypassed",
                    "reason": "pricing_kind_not_mutated",
                    "candidate_journeys": 3,
                    "admitted_journeys": 3,
                    "true_negative_journeys": 3,
                    "support_aware_admission_enabled": True,
                    "support_candidate_active_support_changing_journeys": 2,
                    "support_candidate_new_task_set_journeys": 1,
                    "support_candidate_inactive_only_journeys": 0,
                    "support_online_high_priority_journeys": 3,
                    "exact_path_preserved": True,
                },
                {
                    "event": "journey_gat_target_mode_admission",
                    "node_id": 2,
                    "depth": 2,
                    "cg_iter": 4,
                    "time": 120.0,
                    "pricing_kind": "exact_completion_bound_retry",
                    "status": "scheduled",
                    "reason": "opt_in_admission_scheduler",
                    "candidate_journeys": 2,
                    "admitted_journeys": 1,
                    "true_negative_journeys": 2,
                    "support_aware_admission_enabled": True,
                    "support_candidate_active_support_changing_journeys": 0,
                    "support_candidate_new_task_set_journeys": 0,
                    "support_candidate_inactive_only_journeys": 2,
                    "support_delayed_inactive_only_journeys": 1,
                },
                {
                    "event": "journey_gat_target_mode_admission",
                    "node_id": 3,
                    "depth": 1,
                    "cg_iter": 2,
                    "time": 125.0,
                    "pricing_kind": "heuristic",
                    "status": "scheduled",
                    "candidate_journeys": 99,
                    "support_candidate_inactive_only_journeys": 99,
                },
                {
                    "event": "journey_gat_target_mode_admission",
                    "node_id": 4,
                    "depth": 1,
                    "cg_iter": 2,
                    "time": 130.0,
                    "pricing_kind": "exact",
                    "status": "bypassed",
                    "reason": "pricing_kind_not_mutated",
                    "candidate_journeys": 1,
                    "support_aware_admission_enabled": False,
                },
            ]
            log_path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )

            summary = summarize([log_path], min_depth=1)

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertEqual(summary["admission_event_count"], 3)
            self.assertEqual(summary["support_enabled_event_count"], 2)
            self.assertEqual(summary["total_candidate_journeys"], 6)
            self.assertEqual(summary["total_true_negative_journeys"], 5)
            self.assertEqual(summary["total_support_active_journeys"], 2)
            self.assertEqual(summary["total_support_new_journeys"], 1)
            self.assertEqual(summary["total_support_inactive_journeys"], 2)
            self.assertEqual(summary["total_support_delayed_inactive_journeys"], 1)
            self.assertEqual(summary["support_inactive_share"], 0.4)
            self.assertEqual(
                summary["support_tail_class_counts"],
                {
                    "active_support_changing": 1,
                    "inactive_only": 1,
                    "support_context_missing_or_disabled": 1,
                },
            )
            rows = summary["rows"]
            self.assertEqual(rows[0]["support_tail_class"], "active_support_changing")
            self.assertEqual(rows[1]["support_tail_class"], "inactive_only")
            self.assertEqual(rows[2]["support_tail_class"], "support_context_missing_or_disabled")

            write_outputs(summary, tmp_path / "out", tmp_path / "report.md")
            self.assertTrue((tmp_path / "out" / "summary.json").exists())
            self.assertTrue((tmp_path / "out" / "support_aware_branch_exact_tail_rows.jsonl").exists())
            self.assertTrue((tmp_path / "out" / "support_aware_branch_exact_tail_rows.csv").exists())
            self.assertIn("official_bound_effect = false", (tmp_path / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

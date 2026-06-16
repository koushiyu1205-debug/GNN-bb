from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_gat_model_scored_online_safe_source import (
    audit_model_scored_online_safe_source,
)


class GATModelScoredOnlineSafeSourceAuditTests(unittest.TestCase):
    def test_reports_diagnostic_hint_without_admission_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            safe_source = root / "safe_source.json"
            decision_records = root / "decision_records.jsonl"
            log_dir = root / "logs"
            output_dir = root / "out"
            report = root / "report.md"
            log_dir.mkdir()

            safe_source.write_text(
                json.dumps({"safe_source_ready": True, "safe_candidate_ids": []}) + "\n",
                encoding="utf-8",
            )
            records = [
                {
                    "candidate_signature_ids": ["offline-high"],
                    "candidate_task_sets": [[1, 5]],
                    "high_priority_candidate_signature_ids": ["offline-high"],
                    "label_high_priority": 1,
                    "decision": 1,
                    "decision_name": "HIGH_PRIORITY",
                    "accepted_batch_roi_label": 2.0,
                    "batch_score": 0.9,
                    "instance_family": "sector-wave",
                    "instance_task_count": "20",
                    "context_hash": "ctx-high",
                },
                {
                    "candidate_signature_ids": ["offline-conflict-high"],
                    "candidate_task_sets": [[2, 6]],
                    "high_priority_candidate_signature_ids": ["offline-conflict-high"],
                    "label_high_priority": 1,
                    "decision": 1,
                    "decision_name": "HIGH_PRIORITY",
                    "accepted_batch_roi_label": 2.0,
                    "batch_score": 0.8,
                    "instance_family": "sector-wave",
                    "instance_task_count": "20",
                    "context_hash": "ctx-conflict-high",
                },
                {
                    "candidate_signature_ids": ["offline-conflict-delay"],
                    "candidate_task_sets": [[2, 6]],
                    "high_priority_candidate_signature_ids": [],
                    "label_high_priority": 0,
                    "decision": 0,
                    "decision_name": "DELAY_QUEUE",
                    "accepted_batch_roi_label": -1.0,
                    "batch_score": 0.2,
                    "instance_family": "sector-wave",
                    "instance_task_count": "20",
                    "context_hash": "ctx-conflict-delay",
                },
            ]
            decision_records.write_text(
                "\n".join(json.dumps(record) for record in records) + "\n",
                encoding="utf-8",
            )
            (log_dir / "shadow.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "event": "journey_gat_target_mode_shadow",
                                "status": "logged",
                                "pricing_kind": "exact",
                                "cg_iter": 7,
                                "candidate_journeys": 2,
                                "decision_samples": [
                                    {
                                        "candidate_id": "online-hint",
                                        "decision": "DELAY_QUEUE",
                                        "reason": "true_rc_negative_delayed_not_rejected",
                                        "task_set": [1, 5],
                                        "signature": [[[1, 5], ["0->1:a", "1->5:b", "5->0:c"], 0.0]],
                                        "true_reduced_cost": -3.0,
                                    },
                                    {
                                        "candidate_id": "online-conflict",
                                        "decision": "DELAY_QUEUE",
                                        "reason": "true_rc_negative_delayed_not_rejected",
                                        "task_set": [2, 6],
                                        "signature": [[[2, 6], ["0->2:a", "2->6:b", "6->0:c"], 0.0]],
                                        "true_reduced_cost": -4.0,
                                    },
                                ],
                            }
                        )
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            summary = audit_model_scored_online_safe_source(
                safe_source=safe_source,
                decision_records=decision_records,
                shadow_log_dir=log_dir,
                output_dir=output_dir,
                report=report,
                min_roi=0.65,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["online_sampled_candidate_journeys"], 2)
            self.assertEqual(summary["exact_safe_id_hit_count"], 0)
            self.assertEqual(summary["diagnostic_priority_hint_count"], 1)
            self.assertEqual(summary["admission_ready_count"], 0)
            self.assertFalse(summary["stage4_model_scored_online_safe_source_ready"])
            self.assertFalse(summary["stage4_mutating_admission_ready"])
            top = summary["top_diagnostic_candidates"][0]
            self.assertEqual(top["candidate_id"], "online-hint")
            self.assertEqual(top["best_key_level"], "task_set")
            self.assertEqual(top["offline_delay_conflict_count"], 0)
            self.assertTrue((output_dir / "summary.json").exists())
            self.assertTrue((output_dir / "online_candidate_evidence.jsonl").exists())
            self.assertTrue(report.exists())

    def test_exact_hit_blocker_requires_online_trajectory_roi(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            safe_source = root / "safe_source.json"
            decision_records = root / "decision_records.jsonl"
            log_dir = root / "logs"
            output_dir = root / "out"
            report = root / "report.md"
            log_dir.mkdir()

            safe_source.write_text(
                json.dumps({"safe_source_ready": True, "safe_candidate_ids": ["exact-hit"]}) + "\n",
                encoding="utf-8",
            )
            decision_records.write_text("", encoding="utf-8")
            (log_dir / "shadow.jsonl").write_text(
                json.dumps(
                    {
                        "event": "journey_gat_target_mode_shadow",
                        "status": "logged",
                        "pricing_kind": "exact",
                        "cg_iter": 7,
                        "candidate_journeys": 1,
                        "decision_samples": [
                            {
                                "candidate_id": "exact-hit",
                                "decision": "DELAY_QUEUE",
                                "reason": "true_rc_negative_delayed_not_rejected",
                                "task_set": [1, 5],
                                "signature": [[[1, 5], ["0->1:a", "1->5:b", "5->0:c"], 0.0]],
                                "true_reduced_cost": -3.0,
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            summary = audit_model_scored_online_safe_source(
                safe_source=safe_source,
                decision_records=decision_records,
                shadow_log_dir=log_dir,
                output_dir=output_dir,
                report=report,
                min_roi=0.65,
            )

            self.assertEqual(summary["exact_safe_id_hit_count"], 1)
            self.assertEqual(summary["admission_ready_count"], 0)
            self.assertIn(
                "exact_safe_id_overlap_is_not_trajectory_roi_proof",
                summary["blocked_reasons"],
            )
            self.assertNotIn("exact_safe_id_overlap_missing", summary["blocked_reasons"])
            evidence = json.loads((output_dir / "online_candidate_evidence.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(
                evidence["admission_blocker"],
                "exact_safe_id_hit_but_online_trajectory_roi_unverified",
            )


if __name__ == "__main__":
    unittest.main()

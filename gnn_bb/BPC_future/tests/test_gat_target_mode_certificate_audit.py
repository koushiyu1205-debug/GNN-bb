from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_gat_target_mode_certificate_closure import (
    audit_gat_target_mode_certificate_closure,
)


class GATTargetModeCertificateAuditTests(unittest.TestCase):
    def test_clean_shadow_log_passes_certificate_boundary_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            log_file = tmp / "clean.jsonl"
            _write_jsonl(
                log_file,
                [
                    {
                        "event": "journey_gat_target_mode_shadow",
                        "pricing_kind": "exact",
                        "certificate_candidate": True,
                        "candidate_journeys": 1,
                        "true_negative_journeys": 1,
                        "high_priority_journeys": 0,
                        "delay_queue_journeys": 1,
                        "reject_nonnegative_only_journeys": 0,
                        "delayed_negative_journeys": 1,
                        "selector_is_pricing_oracle": False,
                        "selector_can_certificate": False,
                        "official_bound_effect": False,
                        "hard_filter_enabled": False,
                        "decision_samples": [
                            {
                                "candidate_id": "neg",
                                "decision": "DELAY_QUEUE",
                                "true_reduced_cost": -0.5,
                            }
                        ],
                    },
                    {
                        "event": "journey_gat_target_mode_admission",
                        "pricing_kind": "exact",
                        "certificate_candidate": True,
                        "status": "bypassed",
                        "reason": "certificate_candidate_release",
                        "candidate_journeys": 0,
                        "admitted_journeys": 1,
                        "released_journeys": 1,
                        "true_negative_journeys": 0,
                        "high_priority_journeys": 0,
                        "delay_queue_journeys": 0,
                        "reject_nonnegative_only_journeys": 0,
                        "online_safe_hit_journeys": 0,
                        "delayed_negative_journeys": 0,
                        "selector_is_pricing_oracle": False,
                        "selector_can_certificate": False,
                        "official_bound_effect": False,
                        "hard_filter_enabled": False,
                    },
                    {
                        "event": "journey_pricing",
                        "pricing_kind": "exact_completion_bound_retry",
                        "global_certificate": True,
                    },
                    {
                        "event": "finish",
                        "status": "OPTIMAL",
                        "dual_bound": 1.0,
                    },
                ],
            )

            summary = audit_gat_target_mode_certificate_closure(
                log_paths=[log_file],
                output_dir=tmp / "audit",
                report=tmp / "audit.md",
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["violation_count"], 0)
            self.assertEqual(summary["gat_events"], 2)
            self.assertEqual(summary["shadow_events"], 1)
            self.assertEqual(summary["admission_events"], 1)
            self.assertEqual(summary["true_negative_journeys"], 1)
            self.assertEqual(summary["shadow_true_negative_journeys"], 1)
            self.assertEqual(summary["shadow_delay_queue_journeys"], 1)
            self.assertEqual(summary["admission_true_negative_journeys"], 0)
            self.assertEqual(summary["admission_delay_queue_journeys"], 0)
            self.assertEqual(summary["admission_online_safe_hit_journeys"], 0)
            self.assertEqual(summary["certificate_candidate_delayed_negative_events"], 1)

    def test_gat_certificate_claim_and_negative_reject_are_violations(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            log_file = tmp / "bad.jsonl"
            _write_jsonl(
                log_file,
                [
                    {
                        "event": "journey_gat_target_mode_shadow",
                        "pricing_kind": "exact",
                        "candidate_journeys": 1,
                        "true_negative_journeys": 1,
                        "reject_nonnegative_only_journeys": 1,
                        "selector_is_pricing_oracle": True,
                        "selector_can_certificate": True,
                        "official_bound_effect": True,
                        "hard_filter_enabled": True,
                        "decision_samples": [
                            {
                                "candidate_id": "neg",
                                "decision": "REJECT_NONNEGATIVE_ONLY",
                                "true_reduced_cost": -0.25,
                            }
                        ],
                    },
                    {
                        "event": "finish",
                        "status": "TIME_LIMIT",
                        "dual_bound": 10.0,
                    },
                ],
            )

            summary = audit_gat_target_mode_certificate_closure(
                log_paths=[log_file],
                output_dir=tmp / "audit",
                report=tmp / "audit.md",
            )

            reasons = {item["reason"] for item in summary["violations"]}
            self.assertFalse(summary["all_checks_pass"])
            self.assertIn("selector_can_certificate_true", reasons)
            self.assertIn("selector_is_pricing_oracle_true", reasons)
            self.assertIn("official_bound_effect_true", reasons)
            self.assertIn("hard_filter_enabled_true", reasons)
            self.assertIn("true_rc_negative_rejected", reasons)
            self.assertIn("non_optimal_finish_has_official_dual_bound", reasons)


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()

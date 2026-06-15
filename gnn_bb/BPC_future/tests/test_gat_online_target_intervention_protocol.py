from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.build_gat_online_target_intervention_protocol import build_protocol


class GATOnlineTargetInterventionProtocolTests(unittest.TestCase):
    def test_protocol_requires_same_context_target_causal_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            roi = tmp / "roi_summary.json"
            context = tmp / "context_summary.json"
            roi.write_text(
                json.dumps(
                    {
                        "row_count": 13,
                        "training_row_count": 0,
                        "unique_training_row_count": 0,
                        "target_diag_available_count": 3,
                        "worker_context_match_count": 0,
                        "target_causal_match_count": 0,
                        "target_intervention_observed_count": 2,
                        "positive_roi_without_target_causal_match_count": 2,
                        "worker_context_mismatch_count": 1,
                        "roi_without_target_causal_match_count": 1,
                        "no_worker_target_intervention_count": 10,
                        "training_ready": False,
                    }
                ),
                encoding="utf-8",
            )
            context.write_text(
                json.dumps(
                    {"status": "selector_context_trajectory_capture_protocol_ready"}
                ),
                encoding="utf-8",
            )

            summary = build_protocol(
                roi_dataset_path=roi,
                context_protocol_path=context,
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["default_enabled"])
            self.assertFalse(summary["certificate_ready"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertIn("true_dual_hash", summary["required_exact_context_components"])
            self.assertIn("cuts_hash", summary["required_exact_context_components"])
            self.assertIn("branch_hash", summary["required_exact_context_components"])
            self.assertIn("context_mismatch", summary["invalid_sample_classes"])
            self.assertIn("worker_context_mismatch", summary["invalid_sample_classes"])
            self.assertIn(
                "target causal match is observed in worker diagnostics",
                summary["label_acceptance_rules"]["positive_roi"],
            )
            self.assertIn(
                "target causal match is observed in worker diagnostics",
                summary["label_acceptance_rules"]["no_observed_or_negative_roi"],
            )
            self.assertEqual(
                summary["current_roi_dataset_machine_fields"][
                    "positive_roi_without_target_causal_match_count"
                ],
                2,
            )
            self.assertTrue((tmp / "out" / "summary.json").exists())
            self.assertTrue((tmp / "report.md").exists())

    def test_protocol_exposes_required_worker_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            roi = tmp / "roi_summary.json"
            context = tmp / "context_summary.json"
            roi.write_text(
                json.dumps(
                    {
                        "target_causal_match_count": 1,
                        "worker_context_match_count": 1,
                        "target_intervention_observed_count": 1,
                        "positive_roi_without_target_causal_match_count": 0,
                        "worker_context_mismatch_count": 0,
                        "no_worker_target_intervention_count": 0,
                    }
                ),
                encoding="utf-8",
            )
            context.write_text("{}", encoding="utf-8")

            summary = build_protocol(
                roi_dataset_path=roi,
                context_protocol_path=context,
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

            required = summary["required_worker_diagnostics"]
            self.assertIn(
                "journey_sharded_pulse_hidden_negative_worker_log_skips",
                required,
            )
            self.assertIn(
                "journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled",
                required,
            )
            self.assertIn("pulse_worker_context_hash", required)
            self.assertTrue(
                summary["checks"][
                    "requires_worker_log_skips_and_target_diagnostics"
                ]
            )
            self.assertTrue(summary["checks"]["context_mismatch_is_not_a_negative_label"])
            self.assertTrue(summary["checks"]["delay_queue_preserves_completeness"])


if __name__ == "__main__":
    unittest.main()

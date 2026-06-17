from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.audit_gat_batch_impact_epoch_selector import (
    _min_confidence_all_success_count,
    audit_epoch_selector,
)


class GATBatchImpactEpochSelectorTests(unittest.TestCase):
    def test_min_confidence_all_success_count_matches_stage3_ci_gate(self) -> None:
        self.assertEqual(
            _min_confidence_all_success_count(
                {
                    "min_safe_precision_ci_low": 0.9,
                    "confidence_z": 1.96,
                }
            ),
            35,
        )

    def test_epoch_audit_detects_tradeoff_not_checkpoint_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            summary_path = tmp / "metrics.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema_version": "gat_batch_impact_training_summary_v1",
                        "history": [
                            {
                                "epoch": 1,
                                "accepted_batch_count": 9,
                                "accepted_batch_roi": 1.0,
                                "false_high_priority_on_delay": 0.0,
                                "high_priority_precision": 1.0,
                                "safe_precision": 1.0,
                                "validation_loss": 4.0,
                            },
                            {
                                "epoch": 2,
                                "accepted_batch_count": 35,
                                "accepted_batch_roi": 8.0,
                                "false_high_priority_on_delay": 0.4,
                                "high_priority_precision": 0.95,
                                "safe_precision": 1.0,
                                "validation_loss": 5.0,
                            },
                        ],
                        "threshold_search": {
                            "gate_config": {
                                "min_safe_precision_ci_low": 0.9,
                                "confidence_z": 1.96,
                                "max_false_high_priority_on_delay": 0.01,
                                "max_false_safe_union_rate": 0.02,
                                "min_accepted_batch_roi": 0.65,
                                "min_high_priority_precision": 0.9,
                                "min_safe_precision": 0.9,
                            }
                        },
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = audit_epoch_selector(
                checkpoint=None,
                training_summary=summary_path,
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

        self.assertEqual(summary["history_source"], "training_summary")
        self.assertEqual(summary["false_delay_safe_epoch_count"], 1)
        self.assertEqual(summary["coverage_confidence_ready_epoch_count"], 1)
        self.assertEqual(summary["coverage_and_false_delay_safe_epoch_count"], 0)
        self.assertEqual(
            summary["diagnosis"]["primary"],
            "no_epoch_satisfies_coverage_and_false_delay_constraints",
        )
        self.assertFalse(summary["diagnosis"]["checkpoint_selection_is_primary_blocker"])
        self.assertEqual(
            summary["diagnosis"]["recommended_next_step"],
            "not_a_checkpoint_selection_problem_collect_context_local_hard_negatives",
        )

    def test_epoch_audit_marks_candidate_epoch_when_coverage_and_false_delay_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            summary_path = tmp / "metrics.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "history": [
                            {
                                "epoch": 3,
                                "accepted_batch_count": 40,
                                "accepted_batch_rate": 0.2,
                                "accepted_batch_roi": 2.0,
                                "accepted_batch_roi_ci_low": 1.0,
                                "false_high_priority_on_delay": 0.0,
                                "false_safe_rate_union": 0.0,
                                "high_priority_precision": 0.95,
                                "high_priority_precision_ci_low": 0.91,
                                "safe_precision": 1.0,
                                "safe_precision_ci_low": 0.91,
                                "validation_loss": 3.0,
                            }
                        ],
                        "threshold_search": {
                            "gate_config": {
                                "min_safe_precision_ci_low": 0.9,
                                "confidence_z": 1.96,
                                "max_false_high_priority_on_delay": 0.01,
                                "max_false_safe_union_rate": 0.02,
                                "min_accepted_batch_roi": 0.65,
                                "min_high_priority_precision": 0.9,
                                "min_safe_precision": 0.9,
                            }
                        },
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = audit_epoch_selector(
                checkpoint=None,
                training_summary=summary_path,
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

        self.assertEqual(summary["coverage_and_false_delay_safe_epoch_count"], 1)
        self.assertTrue(summary["diagnosis"]["checkpoint_selection_is_primary_blocker"])
        self.assertEqual(
            summary["epoch_rows"][0]["epoch_signal_class"],
            "coverage_ready_and_false_delay_safe",
        )


if __name__ == "__main__":
    unittest.main()

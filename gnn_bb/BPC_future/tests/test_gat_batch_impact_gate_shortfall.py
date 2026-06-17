from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.audit_gat_batch_impact_gate_shortfall import (
    additional_all_successes_for_wilson,
    audit_gate_shortfall,
    enrich_shortfall_row,
)


class GATBatchImpactGateShortfallTests(unittest.TestCase):
    def test_additional_successes_for_wilson_reports_precision_sample_shortfall(self) -> None:
        self.assertEqual(
            additional_all_successes_for_wilson(
                15,
                15,
                0.85,
                z=1.96,
            ),
            7,
        )

    def test_enrich_shortfall_row_keeps_roi_ci_as_hard_blocker(self) -> None:
        row = {
            "threshold_local_reject_reasons": [
                "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable",
            ],
            "accepted_batch_count": 15,
            "safe_precision": 1.0,
            "safe_precision_ci_low": 0.7961107336956521,
            "high_priority_prediction_count": 917,
            "high_priority_true_positive_count": 917,
            "high_priority_precision_ci_low": 0.9958281641489696,
            "accepted_batch_roi": 0.6835797051588695,
            "accepted_batch_roi_ci_low": 0.378967479841408,
        }
        gate = {
            "confidence_z": 1.96,
            "min_safe_precision_ci_low": 0.85,
            "min_high_priority_precision_ci_low": 0.85,
            "min_accepted_batch_roi": 0.65,
            "min_accepted_batch_roi_ci_low": 0.65,
        }

        enriched = enrich_shortfall_row(row, gate_config=gate)

        self.assertEqual(enriched["safe_precision_additional_all_success_needed"], 7)
        self.assertEqual(enriched["high_priority_precision_additional_all_success_needed"], 0)
        self.assertEqual(enriched["accepted_batch_roi_point_gap"], 0.0)
        self.assertGreater(enriched["accepted_batch_roi_ci_low_gap"], 0.27)

    def test_audit_includes_family_delay_fallback_and_delay_safe_shell(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            global_path = tmp / "global.jsonl"
            fallback_path = tmp / "fallback.jsonl"
            summary_path = tmp / "summary.json"
            _write_jsonl(
                global_path,
                [
                    {
                        "threshold_scope": "global",
                        "threshold_mode": "separate_batch_candidate",
                        "accepted_batch_count": 10,
                        "accepted_batch_roi": 3.0,
                        "accepted_batch_roi_ci_low": 1.0,
                        "candidate_threshold": 0.2,
                        "false_high_priority_on_delay": 0.4,
                        "false_safe_rate_union": 0.4,
                        "high_priority_prediction_count": 100,
                        "high_priority_true_positive_count": 95,
                        "high_priority_precision_ci_low": 0.90,
                        "safe_precision": 1.0,
                        "safe_precision_ci_low": 0.85,
                        "threshold_local_reject_reasons": [
                            "false_high_priority_on_delay_too_high",
                            "false_safe_rate_union_too_high",
                        ],
                    }
                ],
            )
            _write_jsonl(
                fallback_path,
                [
                    {
                        "threshold_scope": "family_delay_fallback",
                        "threshold_mode": "family_delay_fallback",
                        "accepted_batch_count": 2,
                        "accepted_batch_roi": 20.0,
                        "accepted_batch_roi_ci_low": -10.0,
                        "candidate_threshold": 0.49,
                        "false_high_priority_on_delay": 0.0,
                        "false_safe_rate_union": 0.0,
                        "high_priority_prediction_count": 10,
                        "high_priority_true_positive_count": 10,
                        "high_priority_precision_ci_low": 0.70,
                        "safe_precision": 1.0,
                        "safe_precision_ci_low": 0.40,
                        "threshold_local_reject_reasons": [
                            "safe_precision_ci_low_below_threshold_or_not_measurable",
                            "accepted_batch_rate_too_low",
                        ],
                    }
                ],
            )
            summary_path.write_text(
                json.dumps(
                    {
                        "schema_version": "gat_batch_impact_threshold_frontier_v1",
                        "diagnostic_only": True,
                        "runs_bpc_or_pricing": False,
                        "production_ready": False,
                        "selector_can_certificate": False,
                        "frontier_global_path": str(global_path),
                        "frontier_family_delay_fallback_path": str(fallback_path),
                        "feasible_threshold_count": 0,
                        "checkpoint_feasible_threshold_count": 0,
                        "validation_record_count": 2,
                        "train_record_count": 2,
                        "gate_config": {
                            "confidence_z": 1.96,
                            "max_false_high_priority_on_delay": 0.01,
                            "max_false_safe_union_rate": 0.02,
                            "min_safe_precision_ci_low": 0.90,
                            "min_high_priority_precision_ci_low": 0.90,
                            "min_accepted_batch_roi": 0.65,
                            "min_accepted_batch_roi_ci_low": 0.65,
                        },
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = audit_gate_shortfall(
                threshold_summary=summary_path,
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

        delay_safe = summary["delay_safe_frontier_summary"]
        self.assertEqual(summary["total_frontier_rows"], 2)
        self.assertEqual(delay_safe["delay_safe_with_accepted_batch_count"], 1)
        self.assertEqual(delay_safe["delay_safe_accepted_batch_count_max"], 2)
        self.assertEqual(
            summary["recommended_next_step"]["primary"],
            "delay_safe_shell_exists_but_coverage_too_small",
        )


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()

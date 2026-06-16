from __future__ import annotations

import unittest

from BPC_future.scripts.audit_gat_batch_impact_gate_shortfall import (
    additional_all_successes_for_wilson,
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


if __name__ == "__main__":
    unittest.main()

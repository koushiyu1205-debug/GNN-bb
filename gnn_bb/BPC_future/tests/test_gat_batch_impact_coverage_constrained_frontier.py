from __future__ import annotations

import unittest

from BPC_future.scripts.audit_gat_batch_impact_coverage_constrained_frontier import (
    CoverageConstraints,
    coverage_constraint_summary,
    coverage_reject_reasons,
)


class GATBatchImpactCoverageConstrainedFrontierTests(unittest.TestCase):
    def test_passes_when_all_oracle_families_capture_high_roi(self) -> None:
        row = _row(
            random_accepted_high_roi=1,
            sector_accepted_high_roi=2,
            safe_precision_ci_low=0.90,
        )

        summary = coverage_constraint_summary(row)

        self.assertTrue(summary["coverage_constraint_pass"])
        self.assertTrue(summary["coverage_constrained_gate_pass"])
        self.assertEqual(summary["accepted_high_roi_family_count"], 2)
        self.assertEqual(summary["sector_wave_accepted_high_roi_count"], 2)

    def test_rejects_zero_sector_wave_capture(self) -> None:
        row = _row(
            random_accepted_high_roi=1,
            sector_accepted_high_roi=0,
            safe_precision_ci_low=0.90,
        )

        reasons = coverage_reject_reasons(row)

        self.assertIn("family_high_roi_capture_count_below_limit:sector-wave", reasons)
        self.assertIn("required_high_roi_family_zero_capture:sector-wave", reasons)

    def test_rejects_safe_shell_with_insufficient_confidence(self) -> None:
        row = _row(
            random_accepted_high_roi=1,
            sector_accepted_high_roi=1,
            safe_precision_ci_low=0.60,
        )

        reasons = coverage_reject_reasons(row)

        self.assertIn("safe_precision_ci_low_below_coverage_limit", reasons)

    def test_can_require_nonzero_family_capture_rate(self) -> None:
        row = _row(
            random_accepted_high_roi=0,
            sector_accepted_high_roi=1,
            safe_precision_ci_low=0.90,
        )
        constraints = CoverageConstraints(min_family_high_roi_capture_rate=0.20)

        reasons = coverage_reject_reasons(row, constraints=constraints)

        self.assertIn("family_high_roi_capture_count_below_limit:random-wave", reasons)
        self.assertIn("family_high_roi_capture_rate_below_limit:random-wave", reasons)


def _row(
    *,
    random_accepted_high_roi: int,
    sector_accepted_high_roi: int,
    safe_precision_ci_low: float,
) -> dict[str, object]:
    return {
        "threshold_local_gate_pass": True,
        "accepted_batch_count": 10,
        "accepted_bad_mode_count": 0,
        "safe_precision_ci_low": safe_precision_ci_low,
        "false_safe_rate_union": 0.0,
        "false_high_priority_on_delay": 0.0,
        "family_holdout_per_family": {
            "random-wave": {
                "oracle_high_roi_count": 2,
                "accepted_high_roi_count": random_accepted_high_roi,
                "high_roi_capture_rate": float(random_accepted_high_roi) / 2.0,
            },
            "sector-wave": {
                "oracle_high_roi_count": 3,
                "accepted_high_roi_count": sector_accepted_high_roi,
                "high_roi_capture_rate": float(sector_accepted_high_roi) / 3.0,
            },
            "greedy-anchor": {
                "oracle_high_roi_count": 0,
                "accepted_high_roi_count": 0,
                "high_roi_capture_rate": None,
            },
        },
    }


if __name__ == "__main__":
    unittest.main()


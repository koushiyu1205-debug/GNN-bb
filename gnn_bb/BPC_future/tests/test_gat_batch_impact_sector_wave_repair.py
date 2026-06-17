from __future__ import annotations

import unittest

from BPC_future.scripts.audit_gat_batch_impact_sector_wave_repair import (
    build_context_repair_rows,
    primary_repair_action,
)


class GATBatchImpactSectorWaveRepairTests(unittest.TestCase):
    def test_context_repair_prefers_same_context_contrast_when_low_roi_accepts_exist(self) -> None:
        rows = build_context_repair_rows(
            [
                _decision(
                    context="ctx-a",
                    roi=2.0,
                    accepted=False,
                    high_roi=True,
                    reasons=["no_candidate_above_threshold"],
                ),
                _decision(
                    context="ctx-a",
                    roi=0.1,
                    accepted=True,
                    high_roi=False,
                    reasons=[],
                ),
            ]
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["missed_high_roi_count"], 1)
        self.assertEqual(rows[0]["accepted_low_roi_or_bad_count"], 1)
        self.assertEqual(
            rows[0]["primary_repair_action"],
            "same_context_high_roi_vs_low_roi_contrast",
        )

    def test_primary_action_detects_delay_risk_repair(self) -> None:
        action = primary_repair_action(
            missed_high_roi=[
                _decision(
                    context="ctx-a",
                    roi=2.0,
                    accepted=False,
                    high_roi=True,
                    reasons=["candidate_risk_adjusted_below_threshold"],
                )
            ],
            accepted_low_roi_or_bad=[],
        )

        self.assertEqual(action, "delay_risk_or_risk_adjusted_score_repair")

    def test_ignores_other_families(self) -> None:
        rows = build_context_repair_rows(
            [
                _decision(
                    context="ctx-a",
                    family="random-wave",
                    roi=2.0,
                    accepted=False,
                    high_roi=True,
                    reasons=["no_candidate_above_threshold"],
                )
            ]
        )

        self.assertEqual(rows, [])


def _decision(
    *,
    context: str,
    roi: float,
    accepted: bool,
    high_roi: bool,
    reasons: list[str],
    family: str = "sector-wave",
) -> dict[str, object]:
    return {
        "family": family,
        "context_hash": context,
        "instance_path": "instance.json",
        "task_count": 20,
        "accepted": accepted,
        "is_high_roi_opportunity": high_roi,
        "is_accepted_high_roi_opportunity": bool(accepted and high_roi),
        "is_missed_high_roi_opportunity": bool((not accepted) and high_roi),
        "is_accepted_low_roi_or_bad": bool(accepted and not high_roi),
        "missed_reasons": reasons,
        "accepted_batch_roi_label": roi,
        "max_safe_candidate_score_margin": -0.1,
        "batch_score_margin": 0.0,
    }


if __name__ == "__main__":
    unittest.main()


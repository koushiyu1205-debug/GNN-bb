from __future__ import annotations

import unittest

from BPC_future.scripts.audit_gat_batch_impact_opportunity_mining import (
    classify_opportunity_record,
)


class GATBatchImpactOpportunityMiningTests(unittest.TestCase):
    def test_classifies_high_roi_missed_by_batch_threshold(self) -> None:
        decision = classify_opportunity_record(
            _record(batch_score=0.4, candidate_scores=[0.9], delay_labels=[0], roi=1.1),
            batch_threshold=0.8,
            candidate_threshold=0.7,
            batch_thresholds_by_family={"random-wave": 0.8},
            min_accepted_batch_roi=0.65,
        )

        self.assertFalse(decision["accepted"])
        self.assertTrue(decision["is_missed_high_roi_opportunity"])
        self.assertEqual(decision["missed_reasons"], ["batch_score_below_family_threshold"])
        self.assertLess(decision["batch_score_margin"], 0.0)

    def test_classifies_high_roi_missed_by_delay_conflict(self) -> None:
        decision = classify_opportunity_record(
            _record(batch_score=0.9, candidate_scores=[0.9, 0.6], delay_labels=[1, 0], roi=1.1),
            batch_threshold=0.8,
            candidate_threshold=0.7,
            min_accepted_batch_roi=0.65,
        )

        self.assertFalse(decision["accepted"])
        self.assertTrue(decision["is_missed_high_roi_opportunity"])
        self.assertEqual(decision["missed_reasons"], ["candidate_delay_conflict"])
        self.assertEqual(decision["predicted_delay_candidate_count"], 1)

    def test_accepts_high_roi_when_batch_and_safe_candidate_pass(self) -> None:
        decision = classify_opportunity_record(
            _record(batch_score=0.9, candidate_scores=[0.9, 0.6], delay_labels=[0, 1], roi=1.1),
            batch_threshold=0.8,
            candidate_threshold=0.7,
            min_accepted_batch_roi=0.65,
        )

        self.assertTrue(decision["accepted"])
        self.assertTrue(decision["is_accepted_high_roi_opportunity"])
        self.assertEqual(decision["missed_reasons"], [])

    def test_classifies_high_roi_missed_by_candidate_delay_risk_gate(self) -> None:
        decision = classify_opportunity_record(
            _record(
                batch_score=0.9,
                candidate_scores=[0.9],
                candidate_delay_scores=[0.8],
                delay_labels=[0],
                roi=1.1,
            ),
            batch_threshold=0.8,
            candidate_threshold=0.7,
            candidate_delay_gate_enabled=True,
            candidate_delay_risk_threshold=0.5,
            min_accepted_batch_roi=0.65,
        )

        self.assertFalse(decision["accepted"])
        self.assertTrue(decision["is_missed_high_roi_opportunity"])
        self.assertEqual(
            decision["missed_reasons"],
            ["no_candidate_above_threshold", "candidate_delay_risk_above_threshold"],
        )
        self.assertEqual(decision["candidate_delay_gate_blocked_count"], 1)


def _record(
    *,
    batch_score: float,
    candidate_scores: list[float],
    candidate_delay_scores: list[float] | None = None,
    delay_labels: list[int],
    roi: float,
) -> dict[str, object]:
    return {
        "family": "random-wave",
        "context_hash": "ctx",
        "instance": "inst",
        "instance_path": "path",
        "region": "region",
        "task_count": 20,
        "batch_score": batch_score,
        "candidate_scores": candidate_scores,
        "candidate_delay_scores": candidate_delay_scores or [0.0 for _ in candidate_scores],
        "candidate_delay_labels": delay_labels,
        "candidate_high_priority_labels": [1 for _ in candidate_scores],
        "batch_roi_positive": 1,
        "bad_mode_switch": 0,
        "tail_improved": 0,
        "support_changed_good": 0,
        "accepted_batch_roi_label": roi,
        "candidate_signature_ids": [f"sig-{idx}" for idx, _ in enumerate(candidate_scores)],
    }


if __name__ == "__main__":
    unittest.main()

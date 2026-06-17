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

    def test_classifies_high_roi_missed_by_risk_adjusted_candidate_score(self) -> None:
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
            candidate_admission_score_mode="risk_adjusted_product",
            candidate_delay_score_penalty=1.0,
            min_accepted_batch_roi=0.65,
        )

        self.assertFalse(decision["accepted"])
        self.assertTrue(decision["is_missed_high_roi_opportunity"])
        self.assertEqual(
            decision["missed_reasons"],
            ["no_candidate_above_threshold", "candidate_risk_adjusted_below_threshold"],
        )
        self.assertEqual(decision["candidate_risk_adjusted_suppressed_count"], 1)
        self.assertGreater(decision["max_raw_candidate_score_margin"], 0.0)
        self.assertLess(decision["max_candidate_score_margin"], 0.0)

    def test_rescue_window_accepts_raw_safe_candidate_inside_delay_window(self) -> None:
        decision = classify_opportunity_record(
            _record(
                batch_score=0.9,
                candidate_scores=[0.95],
                candidate_delay_scores=[0.60],
                delay_labels=[0],
                roi=1.1,
            ),
            batch_threshold=0.8,
            candidate_threshold=0.5,
            candidate_delay_gate_enabled=True,
            candidate_delay_risk_threshold=0.5,
            candidate_admission_score_mode="risk_adjusted_rescue_window",
            candidate_delay_score_penalty=2.0,
            candidate_rescue_raw_score_threshold=0.9,
            candidate_rescue_delay_risk_threshold=0.75,
            candidate_rescue_delay_score_penalty=0.25,
            min_accepted_batch_roi=0.65,
        )

        self.assertTrue(decision["accepted"])
        self.assertTrue(decision["is_accepted_high_roi_opportunity"])
        self.assertEqual(decision["candidate_risk_adjusted_suppressed_count"], 1)
        self.assertEqual(decision["candidate_rescue_window_eligible_count"], 1)
        self.assertEqual(decision["candidate_rescue_window_promoted_count"], 1)
        self.assertGreater(decision["max_candidate_score_margin"], 0.0)

    def test_rescue_window_rejects_candidate_outside_delay_window(self) -> None:
        decision = classify_opportunity_record(
            _record(
                batch_score=0.9,
                candidate_scores=[0.95],
                candidate_delay_scores=[0.90],
                delay_labels=[0],
                roi=1.1,
            ),
            batch_threshold=0.8,
            candidate_threshold=0.5,
            candidate_delay_gate_enabled=True,
            candidate_delay_risk_threshold=0.5,
            candidate_admission_score_mode="risk_adjusted_rescue_window",
            candidate_delay_score_penalty=2.0,
            candidate_rescue_raw_score_threshold=0.9,
            candidate_rescue_delay_risk_threshold=0.75,
            candidate_rescue_delay_score_penalty=0.25,
            min_accepted_batch_roi=0.65,
        )

        self.assertFalse(decision["accepted"])
        self.assertTrue(decision["is_missed_high_roi_opportunity"])
        self.assertEqual(decision["candidate_rescue_window_eligible_count"], 0)
        self.assertEqual(decision["candidate_rescue_window_promoted_count"], 0)
        self.assertEqual(decision["candidate_risk_adjusted_suppressed_count"], 1)

    def test_context_delay_fallback_overrides_candidate_acceptance(self) -> None:
        decision = classify_opportunity_record(
            _record(batch_score=0.9, candidate_scores=[0.95], delay_labels=[0], roi=1.1),
            batch_threshold=0.8,
            candidate_threshold=0.5,
            context_delay_fallback_contexts=["ctx"],
            min_accepted_batch_roi=0.65,
        )

        self.assertFalse(decision["accepted"])
        self.assertTrue(decision["context_delay_fallback"])
        self.assertTrue(decision["is_missed_high_roi_opportunity"])
        self.assertEqual(decision["predicted_candidate_count"], 0)
        self.assertEqual(decision["missed_reasons"], ["context_delay_fallback"])


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

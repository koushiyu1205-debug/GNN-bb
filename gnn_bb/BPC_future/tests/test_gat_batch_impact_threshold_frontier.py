from __future__ import annotations

import unittest

from BPC_future.scripts.audit_gat_batch_impact_threshold_frontier import (
    evaluate_threshold_frontier_records,
    records_for_split,
)


class GATBatchImpactThresholdFrontierTests(unittest.TestCase):
    def test_frontier_finds_feasible_threshold_when_confidence_has_support(self) -> None:
        records = [_record(idx, score=0.9, roi=1.0) for idx in range(30)]
        frontier = evaluate_threshold_frontier_records(
            records,
            gate_config=_gate_config(actual_sample_count=len(records)),
            max_dynamic_thresholds=16,
        )

        self.assertGreater(frontier["feasible_threshold_count"], 0)
        self.assertTrue(frontier["best_candidate"]["threshold_local_gate_pass"])
        self.assertGreaterEqual(frontier["best_candidate"]["safe_precision_ci_low"], 0.85)
        self.assertGreaterEqual(frontier["best_candidate"]["accepted_batch_roi_ci_low"], 0.65)

    def test_frontier_reports_confidence_blocker_for_tiny_safe_shell(self) -> None:
        records = [_record(idx, score=0.9, roi=1.0) for idx in range(2)]
        frontier = evaluate_threshold_frontier_records(
            records,
            gate_config=_gate_config(actual_sample_count=len(records)),
            max_dynamic_thresholds=16,
        )

        self.assertEqual(frontier["feasible_threshold_count"], 0)
        best = frontier["best_candidate"]
        self.assertEqual(best["safe_precision"], 1.0)
        self.assertLess(best["safe_precision_ci_low"], 0.85)
        self.assertIn(
            "safe_precision_ci_low_below_threshold_or_not_measurable",
            best["threshold_local_reject_reasons"],
        )

    def test_frontier_includes_context_delay_fallback_candidates(self) -> None:
        records = [
            _record(0, family="greedy-anchor", score=0.9, roi=0.05),
            _record(1, family="random-wave", score=0.9, roi=1.0),
            _record(2, family="sector-wave", score=0.9, roi=1.0),
            _record(3, family="greedy-anchor", score=0.9, roi=1.0),
        ]
        frontier = evaluate_threshold_frontier_records(
            records,
            gate_config=_gate_config_without_confidence_bounds(
                actual_sample_count=len(records),
                observed_family_count=3,
                min_major_families=3,
                min_accepted_batch_count=2,
                min_family_holdout_accepted_roi=0.65,
            ),
            max_dynamic_thresholds=16,
        )

        self.assertGreater(frontier["family_delay_fallback_frontier_count"], 0)
        self.assertEqual(
            frontier["best_candidate"]["family_delay_fallback_families"],
            [],
        )
        self.assertEqual(
            frontier["best_candidate"]["context_delay_fallback_contexts"],
            ["ctx-0"],
        )
        self.assertTrue(frontier["best_candidate"]["threshold_local_gate_pass"])
        self.assertNotIn(
            "family_holdout_accepted_roi_below_threshold",
            frontier["best_candidate"]["threshold_local_reject_reasons"],
        )

    def test_records_for_split_preserves_multiple_contexts_per_instance(self) -> None:
        record_items = [
            ("inst-a", {"id": 1}),
            ("inst-a", {"id": 2}),
            ("inst-b", {"id": 3}),
        ]

        train_records, validation_records = records_for_split(
            record_items,
            train_instances={"inst-b"},
            validation_instances={"inst-a"},
        )

        self.assertEqual([record["id"] for record in train_records], [3])
        self.assertEqual([record["id"] for record in validation_records], [1, 2])


def _record(idx: int, *, score: float, roi: float, family: str = "random-wave") -> dict[str, object]:
    return {
        "family": family,
        "context_hash": f"ctx-{idx}",
        "batch_score": score,
        "candidate_scores": [score],
        "candidate_high_priority_labels": [1],
        "candidate_delay_labels": [0],
        "batch_roi_positive": 1,
        "bad_mode_switch": 0,
        "tail_improved": 0,
        "support_changed_good": 0,
        "accepted_batch_roi_label": roi,
    }


def _gate_config(*, actual_sample_count: int) -> dict[str, object]:
    return {
        "min_high_priority_precision": 0.85,
        "min_high_priority_precision_ci_low": 0.85,
        "min_safe_precision": 0.85,
        "min_safe_precision_ci_low": 0.85,
        "confidence_z": 1.96,
        "max_false_high_priority_on_delay": 0.0,
        "max_false_safe_union_rate": 0.02,
        "min_accepted_batch_count": 1,
        "min_accepted_batch_rate": 0.0,
        "min_accepted_batch_roi": 0.65,
        "min_accepted_batch_roi_ci_low": 0.65,
        "baseline_accepted_batch_roi": 0.0,
        "min_roi_margin_over_baseline": 0.20,
        "min_family_holdout_precision": 0.0,
        "min_family_holdout_accepted_roi": 0.0,
        "min_major_families": 1,
        "observed_family_count": 1,
        "stage3_min_samples": 1,
        "actual_sample_count": actual_sample_count,
        "knn_ood_audit_completed": True,
    }


def _gate_config_without_confidence_bounds(
    *,
    actual_sample_count: int,
    observed_family_count: int,
    min_major_families: int,
    min_accepted_batch_count: int,
    min_family_holdout_accepted_roi: float,
) -> dict[str, object]:
    gate = _gate_config(actual_sample_count=actual_sample_count)
    gate.update(
        {
            "min_high_priority_precision_ci_low": None,
            "min_safe_precision_ci_low": None,
            "min_accepted_batch_roi_ci_low": None,
            "min_accepted_batch_count": min_accepted_batch_count,
            "min_accepted_batch_rate": 0.0,
            "min_family_holdout_precision": 0.85,
            "min_family_holdout_accepted_roi": min_family_holdout_accepted_roi,
            "min_major_families": min_major_families,
            "observed_family_count": observed_family_count,
        }
    )
    return gate


if __name__ == "__main__":
    unittest.main()

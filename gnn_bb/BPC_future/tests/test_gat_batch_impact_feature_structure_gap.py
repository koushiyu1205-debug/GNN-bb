from __future__ import annotations

import unittest

from BPC_future.scripts.audit_gat_batch_impact_feature_structure_gap import (
    build_feature_category_coverage,
    compare_feature_structure_pair,
    recommended_next_step,
    summarize_candidate_feature_values,
    summarize_feature_structure_gap,
)


class GATBatchImpactFeatureStructureGapTests(unittest.TestCase):
    def test_signature_metadata_is_not_model_input(self) -> None:
        coverage = build_feature_category_coverage(
            candidate_schema=[
                "true_reduced_cost",
                "cost",
                "sequence_length",
                "sortie_count",
            ],
            context_schema=["branch_constraint_count", "cut_dual_l1_norm"],
            batch_schema=["returned_journey_count", "best_true_reduced_cost"],
            signature_metadata_present=True,
        )

        by_category = {row["category"]: row for row in coverage}

        self.assertEqual(by_category["signature_identity"]["status"], "metadata_only")
        self.assertFalse(by_category["signature_identity"]["model_input"])
        self.assertEqual(by_category["selected_arc_option_sequence"]["status"], "missing")

    def test_visible_coarse_diff_plus_raw_failure_recommends_feature_repair(self) -> None:
        positive = _row(
            row_index=10,
            label_class="positive_trajectory",
            roi=1.0,
            rc=-14.0,
            cost=100.0,
            sequence=[1, 2, 4],
            signature="pos",
        )
        negative = _row(
            row_index=11,
            label_class="delay_or_hard_negative",
            roi=-2.0,
            rc=-30.0,
            cost=90.0,
            sequence=[1, 3, 4],
            signature="neg",
        )
        ranking_pair = {
            "raw_positive_above_negative": False,
            "admission_positive_above_negative": False,
            "positive_lower_delay_risk": False,
            "raw_margin": -0.1,
            "admission_margin": -0.2,
            "delay_risk_margin": -0.3,
        }

        pair = compare_feature_structure_pair(
            positive=positive,
            negative=negative,
            ranking_pair=ranking_pair,
        )
        feature_summary = summarize_candidate_feature_values(
            [positive, negative],
            ["true_reduced_cost", "cost", "strict_replacement_by_cost"],
        )
        coverage = build_feature_category_coverage(
            candidate_schema=list(feature_summary),
            context_schema=["branch_constraint_count", "cut_dual_l1_norm"],
            batch_schema=["returned_journey_count"],
            signature_metadata_present=True,
        )
        summary = summarize_feature_structure_gap(
            row_records=[positive, negative],
            pair_rows=[pair],
            feature_summary=feature_summary,
            category_coverage=coverage,
        )

        self.assertTrue(pair["model_visible_difference"])
        self.assertEqual(pair["gap_class"], "coarse_input_visible_but_candidate_head_misranks")
        self.assertEqual(
            summary["primary"],
            "candidate_input_under_specified_for_action_consequence",
        )
        self.assertEqual(
            recommended_next_step(summary)["primary"],
            "add_trace_timing_slack_and_candidate_interaction_features_then_retrain",
        )

    def test_constant_candidate_feature_summary(self) -> None:
        rows = [
            _row(row_index=1, label_class="positive_trajectory", roi=1.0, rc=-1.0, cost=10.0),
            _row(row_index=2, label_class="delay_or_hard_negative", roi=-1.0, rc=-2.0, cost=20.0),
        ]

        summary = summarize_candidate_feature_values(
            rows,
            ["true_reduced_cost", "cost", "strict_replacement_by_cost"],
        )

        self.assertFalse(summary["true_reduced_cost"]["constant"])
        self.assertFalse(summary["cost"]["constant"])
        self.assertTrue(summary["strict_replacement_by_cost"]["constant"])


def _row(
    *,
    row_index: int,
    label_class: str,
    roi: float,
    rc: float,
    cost: float,
    sequence: list[int] | None = None,
    signature: str = "sig",
) -> dict[str, object]:
    sequence = sequence or [1, 2]
    positions = [0.0, 0.0, 0.0, 0.0]
    membership = [0.0, 0.0, 0.0, 0.0]
    for order, task_id in enumerate(sequence, start=1):
        positions[task_id - 1] = float(order)
        membership[task_id - 1] = 1.0
    return {
        "row_index": row_index,
        "context_key": "instance|ctx",
        "context_hash": "ctx",
        "family": "sector-wave",
        "label_class": label_class,
        "accepted_batch_roi": roi,
        "primary_candidate_signature_id": signature,
        "candidate_feature_values": {
            "true_reduced_cost": rc,
            "cost": cost,
            "strict_replacement_by_cost": 0.0,
        },
        "candidate_sequence_positions": positions,
        "candidate_task_set": sorted(sequence),
        "candidate_task_sequence": sequence,
    }


if __name__ == "__main__":
    unittest.main()

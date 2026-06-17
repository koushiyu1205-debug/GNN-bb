from __future__ import annotations

import unittest

from BPC_future.scripts.audit_gat_batch_impact_individual_context_ranking import (
    build_context_ranking_rows,
    compare_positive_negative_pair,
    focused_pair_gate,
    recommended_next_step,
    summarize_context_ranking,
)


class GATBatchImpactIndividualContextRankingTests(unittest.TestCase):
    def test_candidate_head_ranking_failure_is_primary(self) -> None:
        rows = [
            _row("positive_high_priority", raw=0.2, admission=0.1, delay=0.4, roi=1.0),
            _row("delay_or_hard_negative", raw=0.3, admission=0.05, delay=0.8, roi=-1.0),
        ]
        context_rows, pair_rows = build_context_ranking_rows(rows)
        summary = summarize_context_ranking(rows, context_rows, pair_rows)

        self.assertEqual(len(pair_rows), 1)
        self.assertFalse(pair_rows[0]["raw_positive_above_negative"])
        self.assertEqual(summary["primary"], "candidate_head_context_ranking_failure")
        self.assertEqual(
            recommended_next_step(summary)["primary"],
            "repair_candidate_head_context_local_representation",
        )

    def test_risk_adjusted_admission_failure_is_distinct_from_raw_ranking(self) -> None:
        positive = _row("positive_high_priority", raw=0.4, admission=0.1, delay=0.7, roi=1.0)
        negative = _row("delay_or_hard_negative", raw=0.2, admission=0.15, delay=0.5, roi=-1.0)

        pair = compare_positive_negative_pair(positive, negative)

        self.assertTrue(pair["raw_positive_above_negative"])
        self.assertFalse(pair["admission_positive_above_negative"])
        self.assertFalse(pair["positive_lower_delay_risk"])

    def test_focused_pair_gate_rejects_context_local_misranking(self) -> None:
        rows = [
            _row("positive_high_priority", raw=0.2, admission=0.1, delay=0.4, roi=1.0),
            _row("delay_or_hard_negative", raw=0.3, admission=0.05, delay=0.8, roi=-1.0),
        ]
        context_rows, pair_rows = build_context_ranking_rows(rows)
        summary = summarize_context_ranking(rows, context_rows, pair_rows)

        gate = focused_pair_gate(summary)

        self.assertFalse(gate["gate_pass"])
        self.assertIn("raw_pair_pass_rate_below_threshold", gate["reject_reasons"])
        self.assertIn("strict_pair_pass_rate_below_threshold", gate["reject_reasons"])
        self.assertEqual(gate["blocking_primary"], "candidate_head_context_ranking_failure")

    def test_focused_pair_gate_rejects_missing_pair_contrast(self) -> None:
        rows = [
            _row("positive_high_priority", raw=0.4, admission=0.3, delay=0.1, roi=1.0),
        ]
        context_rows, pair_rows = build_context_ranking_rows(rows)
        summary = summarize_context_ranking(rows, context_rows, pair_rows)

        gate = focused_pair_gate(summary)

        self.assertFalse(gate["gate_pass"])
        self.assertIn(
            "not_enough_focused_positive_negative_pairs",
            gate["reject_reasons"],
        )
        self.assertIn("raw_pair_pass_rate_below_threshold", gate["reject_reasons"])

    def test_focused_pair_gate_passes_when_all_pair_heads_pass(self) -> None:
        rows = [
            _row("positive_high_priority", raw=0.4, admission=0.3, delay=0.1, roi=1.0),
            _row("delay_or_hard_negative", raw=0.2, admission=0.1, delay=0.6, roi=-1.0),
        ]
        context_rows, pair_rows = build_context_ranking_rows(rows)
        summary = summarize_context_ranking(rows, context_rows, pair_rows)

        gate = focused_pair_gate(summary)

        self.assertTrue(gate["gate_pass"])
        self.assertEqual(gate["reject_reasons"], [])
        self.assertEqual(gate["blocking_primary"], "focused_context_pair_gate_passed")


def _row(
    label_class: str,
    *,
    raw: float,
    admission: float,
    delay: float,
    roi: float,
) -> dict[str, object]:
    return {
        "row_index": 1 if roi > 0 else 2,
        "context_key": "instance|ctx",
        "context_hash": "ctx",
        "instance": "instance",
        "family": "sector-wave",
        "task_count": 20,
        "candidate_signature_ids": ["sig"],
        "label_class": label_class,
        "accepted_batch_roi_label": roi,
        "batch_score": raw,
        "max_raw_candidate_score": raw,
        "max_admission_score": admission,
        "max_delay_risk_score": delay,
    }


if __name__ == "__main__":
    unittest.main()

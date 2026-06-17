from __future__ import annotations

import unittest

from BPC_future.scripts.audit_gat_batch_impact_context_contrast_priority import (
    build_context_priority_rows,
    summarize_context_priority,
)


class GATBatchImpactContextContrastPriorityTests(unittest.TestCase):
    def test_structural_negative_neighbor_context_ranks_above_near_threshold(self) -> None:
        rows = build_context_priority_rows(
            score_records=[
                _score_record(
                    "ctx-structural",
                    family="random-wave",
                    task_count=50,
                    roi=5.0,
                    margin=-0.4,
                    bucket="deep_candidate_score_gap",
                    has_contrast=False,
                ),
                _score_record(
                    "ctx-near",
                    family="sector-wave",
                    task_count=20,
                    roi=10.0,
                    margin=-0.02,
                    bucket="near_candidate_threshold",
                    has_contrast=True,
                ),
            ],
            embedding_records=[
                _embedding_record(
                    "ctx-structural",
                    family="random-wave",
                    task_count=50,
                    roi=5.0,
                    margin=-0.4,
                    nearest_negative_closer=True,
                    knn_positive_fraction=0.0,
                ),
                _embedding_record(
                    "ctx-near",
                    family="sector-wave",
                    task_count=20,
                    roi=10.0,
                    margin=-0.02,
                    nearest_negative_closer=False,
                    knn_positive_fraction=0.8,
                ),
            ],
        )

        self.assertEqual(rows[0]["context_hash"], "ctx-structural")
        self.assertEqual(
            rows[0]["primary_action"],
            "collect_same_context_positive_negative_contrast",
        )
        self.assertGreater(rows[0]["priority_score"], rows[1]["priority_score"])

    def test_summary_keeps_exact_safe_diagnostic_contract(self) -> None:
        rows = build_context_priority_rows(
            score_records=[
                _score_record(
                    "ctx",
                    family="sector-wave",
                    task_count=20,
                    roi=2.0,
                    margin=-0.3,
                    bucket="deep_candidate_score_gap",
                    has_contrast=True,
                )
            ],
            embedding_records=[],
        )
        summary = summarize_context_priority(rows)

        self.assertEqual(summary["context_count"], 1)
        self.assertEqual(summary["contexts_with_deep_candidate_gap"], 1)
        self.assertEqual(summary["primary_blocker"], "candidate_head_deep_score_gap")
        self.assertFalse(rows[0]["training_label_allowed_before_worker_reachability"])
        self.assertEqual(rows[0]["exact_safe_scope"], "diagnostic_only_no_certificate_effect")


def _score_record(
    context_hash: str,
    *,
    family: str,
    task_count: int,
    roi: float,
    margin: float,
    bucket: str,
    has_contrast: bool,
) -> dict[str, object]:
    return {
        "context_hash": context_hash,
        "family": family,
        "task_count": task_count,
        "accepted_batch_roi_label": roi,
        "max_safe_candidate_score_margin": margin,
        "candidate_margin_bucket": bucket,
        "has_same_context_low_roi_or_delay_contrast": has_contrast,
        "needs_same_context_contrast": not has_contrast,
        "same_context_low_roi_or_delay_count": int(has_contrast),
        "region": "test-region",
    }


def _embedding_record(
    context_hash: str,
    *,
    family: str,
    task_count: int,
    roi: float,
    margin: float,
    nearest_negative_closer: bool,
    knn_positive_fraction: float,
) -> dict[str, object]:
    return {
        "context_hash": context_hash,
        "family": family,
        "task_count": task_count,
        "accepted_batch_roi_label": roi,
        "max_candidate_score_margin": margin,
        "nearest_negative_closer": nearest_negative_closer,
        "knn_positive_fraction": knn_positive_fraction,
    }


if __name__ == "__main__":
    unittest.main()

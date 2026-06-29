from __future__ import annotations

import unittest

from BPC_future.scripts.audit_gat_branch_action_checkpoint_ranking import (
    _average_precision,
    _binary_roc_auc,
    _group_ranking_metrics,
)


class GATBranchActionCheckpointRankingTests(unittest.TestCase):
    def test_binary_roc_auc_counts_ties(self) -> None:
        self.assertAlmostEqual(
            _binary_roc_auc([1, 1, 0, 0], [0.8, 0.5, 0.5, 0.2]),
            0.875,
        )

    def test_average_precision_rewards_early_positives(self) -> None:
        self.assertAlmostEqual(
            _average_precision([0, 1, 1], [0.9, 0.8, 0.7]),
            (1.0 / 2.0 + 2.0 / 3.0) / 2.0,
        )

    def test_group_ranking_metrics_are_context_local(self) -> None:
        rows = [
            {
                "context_key": "a",
                "branch_priority_loss_weight": 1.0,
                "label": 1,
                "score": 0.8,
            },
            {
                "context_key": "a",
                "branch_priority_loss_weight": 1.0,
                "label": 0,
                "score": 0.2,
            },
            {
                "context_key": "b",
                "branch_priority_loss_weight": 1.0,
                "label": 1,
                "score": 0.3,
            },
            {
                "context_key": "b",
                "branch_priority_loss_weight": 1.0,
                "label": 0,
                "score": 0.7,
            },
            {
                "context_key": "single",
                "branch_priority_loss_weight": 1.0,
                "label": 1,
                "score": 0.9,
            },
        ]

        metrics = _group_ranking_metrics(rows, "score")

        self.assertEqual(metrics["context_count"], 3)
        self.assertEqual(metrics["comparable_context_count"], 2)
        self.assertEqual(metrics["pair_count"], 2)
        self.assertAlmostEqual(metrics["pairwise_accuracy"], 0.5)
        self.assertAlmostEqual(metrics["top1_positive_context_rate"], 0.5)
        self.assertAlmostEqual(metrics["top2_positive_context_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()

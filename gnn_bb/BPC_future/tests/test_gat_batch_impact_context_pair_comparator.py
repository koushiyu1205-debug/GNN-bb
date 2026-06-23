from __future__ import annotations

import unittest

try:
    import torch

    from BPC_future.scripts.audit_gat_batch_impact_context_pair_comparator import (
        _recommend_next_step,
        _score_pair_with_comparator,
        _summary_stats,
    )

    HAS_LEARNING_STACK = True
except Exception:
    HAS_LEARNING_STACK = False


@unittest.skipUnless(HAS_LEARNING_STACK, "learning stack is not installed")
class GATBatchImpactContextPairComparatorAuditTests(unittest.TestCase):
    def test_score_pair_marks_comparator_repair(self):
        class FakeModel:
            def context_pair_preference_logit(self, left_output, right_output):
                if left_output["name"] == "positive" and right_output["name"] == "negative":
                    return torch.tensor([2.0])
                return torch.tensor([-2.0])

        row = _score_pair_with_comparator(
            {
                "context_key": "inst|ctx",
                "context_hash": "ctx",
                "family": "random-wave",
                "positive_row_index": 1,
                "negative_row_index": 2,
                "pair_pass": False,
            },
            outputs={
                1: {"name": "positive"},
                2: {"name": "negative"},
            },
            model=FakeModel(),
        )

        self.assertTrue(row["comparator_pair_pass"])
        self.assertTrue(row["comparator_repairs_existing_failure"])
        self.assertFalse(row["comparator_unresolved_existing_failure"])

    def test_summary_recommends_fused_audit_when_comparator_repairs_all(self):
        rows = [
            {
                "context_key": "inst|ctx",
                "context_hash": "ctx",
                "family": "random-wave",
                "existing_pair_pass": False,
                "comparator_pair_pass": True,
                "comparator_forward_pass": True,
                "comparator_reverse_pass": True,
                "comparator_repairs_existing_failure": True,
                "comparator_unresolved_existing_failure": False,
                "comparator_conflicts_existing_pass": False,
            },
            {
                "context_key": "inst|ctx",
                "context_hash": "ctx",
                "family": "random-wave",
                "existing_pair_pass": True,
                "comparator_pair_pass": True,
                "comparator_forward_pass": True,
                "comparator_reverse_pass": True,
                "comparator_repairs_existing_failure": False,
                "comparator_unresolved_existing_failure": False,
                "comparator_conflicts_existing_pass": False,
            },
        ]

        stats = _summary_stats(rows, context_rows=[])

        self.assertEqual(
            stats["primary"],
            "comparator_separates_all_pairs_but_heads_do_not_use_it",
        )
        self.assertEqual(
            _recommend_next_step(stats),
            "prototype_default_off_fused_context_pair_score_audit_before_training_more",
        )


if __name__ == "__main__":
    unittest.main()

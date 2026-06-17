from __future__ import annotations

import unittest

from BPC_future.scripts.audit_gat_batch_impact_embedding_separation import (
    audit_embedding_separation_records,
    summarize_embedding_separation,
)


class GATBatchImpactEmbeddingSeparationTests(unittest.TestCase):
    def test_missed_high_roi_near_positive_neighbor_is_not_negative_closer(self) -> None:
        rows = audit_embedding_separation_records(
            train_records=[
                _record("train-pos", [0.0, 0.0], roi=1.0, score=0.95),
                _record("train-neg", [10.0, 10.0], roi=0.0, score=0.10),
            ],
            validation_records=[
                _record("missed", [0.1, 0.1], roi=1.0, score=0.40),
            ],
            thresholds={"batch_threshold": 0.0, "candidate_threshold": 0.9},
            min_accepted_batch_roi=0.65,
            knn_k=1,
        )

        self.assertTrue(rows[0]["is_missed_high_roi_opportunity"])
        self.assertFalse(rows[0]["nearest_negative_closer"])
        self.assertEqual(rows[0]["knn_positive_fraction"], 1.0)

    def test_missed_high_roi_near_negative_neighbor_is_structurally_mixed(self) -> None:
        rows = audit_embedding_separation_records(
            train_records=[
                _record("train-pos", [0.0, 0.0], roi=1.0, score=0.95),
                _record("train-neg", [10.0, 10.0], roi=0.0, score=0.10),
            ],
            validation_records=[
                _record("missed", [9.9, 9.9], roi=1.0, score=0.40),
            ],
            thresholds={"batch_threshold": 0.0, "candidate_threshold": 0.9},
            min_accepted_batch_roi=0.65,
            knn_k=1,
        )
        summary = summarize_embedding_separation(rows)

        self.assertTrue(rows[0]["is_missed_high_roi_opportunity"])
        self.assertTrue(rows[0]["nearest_negative_closer"])
        self.assertEqual(rows[0]["knn_positive_fraction"], 0.0)
        self.assertEqual(summary["missed_nearest_negative_closer_count"], 1)


def _record(name: str, embedding: list[float], *, roi: float, score: float) -> dict[str, object]:
    return {
        "instance": name,
        "sample_path": f"{name}.pt",
        "context_hash": "ctx",
        "instance_family": "sector-wave",
        "instance_task_count": "20",
        "embedding": embedding,
        "batch_score": 0.9,
        "candidate_scores": [score],
        "candidate_delay_scores": [0.0],
        "candidate_delay_labels": [0],
        "accepted_batch_roi_label": roi,
        "bad_mode_switch": 0,
    }


if __name__ == "__main__":
    unittest.main()

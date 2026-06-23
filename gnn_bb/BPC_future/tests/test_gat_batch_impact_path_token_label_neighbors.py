import unittest

from BPC_future.scripts.audit_gat_batch_impact_path_token_label_neighbors import (
    _neighbor_record,
    _neighbor_stats,
    _pair_diagnosis,
    _query_diagnosis,
)


class PathTokenLabelNeighborsTest(unittest.TestCase):
    def test_neighbor_record_scores_token_overlap(self) -> None:
        query = {
            "token_ids": [1, 2, 3],
            "pair_ids": [10, 20, 30],
            "type_ids": [1, 2, 3],
            "signature_id": "sig-a",
        }
        candidate = {
            "row_index": 7,
            "candidate_index": 0,
            "split": "train",
            "family": "greedy-anchor",
            "task_count": 20,
            "context_hash": "ctx",
            "accepted_batch_roi": 0.0,
            "batch_roi_positive": 0,
            "signature_id": "sig-a",
            "safe_label": 0,
            "delay_label": 1,
            "true_rc_negative_label": 1,
            "token_ids": [2, 3, 4],
            "pair_ids": [20, 30, 40],
            "type_ids": [2, 3, 1],
        }

        neighbor = _neighbor_record(query, candidate)

        self.assertTrue(neighbor["same_signature"])
        self.assertAlmostEqual(neighbor["token_jaccard"], 0.5)
        self.assertAlmostEqual(neighbor["pair_jaccard"], 0.5)
        self.assertAlmostEqual(neighbor["token_lcs_ratio"], 2 / 3)

    def test_query_diagnosis_marks_positive_delay_biased(self) -> None:
        query = {"role": "positive"}
        neighbors = [
            {
                "token_jaccard": 0.4,
                "split": "train",
                "same_signature": False,
                "exact_token_sequence_match": False,
                "safe_label": 0,
                "delay_label": 1,
                "batch_roi_positive": 0,
                "accepted_batch_roi": 0.0,
            },
            {
                "token_jaccard": 0.3,
                "split": "train",
                "same_signature": False,
                "exact_token_sequence_match": False,
                "safe_label": 0,
                "delay_label": 1,
                "batch_roi_positive": 0,
                "accepted_batch_roi": 0.0,
            },
        ]

        self.assertEqual(
            _query_diagnosis(query, neighbors),
            "positive_path_neighborhood_train_delay_biased",
        )

    def test_pair_diagnosis_prefers_supported_labels_case(self) -> None:
        positive = {"diagnosis": "positive_path_neighborhood_train_supports_safe_label"}
        negative = {"diagnosis": "negative_path_neighborhood_train_supports_delay_label"}

        self.assertEqual(
            _pair_diagnosis(positive, negative),
            "path_neighbors_support_labels_model_head_learned_wrong_direction",
        )

    def test_neighbor_stats_rates(self) -> None:
        stats = _neighbor_stats(
            [
                {
                    "token_jaccard": 1.0,
                    "split": "train",
                    "same_signature": True,
                    "exact_token_sequence_match": True,
                    "safe_label": 1,
                    "delay_label": 0,
                    "batch_roi_positive": 1,
                    "accepted_batch_roi": 2.0,
                },
                {
                    "token_jaccard": 0.5,
                    "split": "validation",
                    "same_signature": False,
                    "exact_token_sequence_match": False,
                    "safe_label": 0,
                    "delay_label": 1,
                    "batch_roi_positive": 0,
                    "accepted_batch_roi": 0.0,
                },
            ]
        )

        self.assertAlmostEqual(stats["safe_label_rate"], 0.5)
        self.assertAlmostEqual(stats["delay_label_rate"], 0.5)
        self.assertEqual(stats["split_counts"], {"train": 1, "validation": 1})


if __name__ == "__main__":
    unittest.main()

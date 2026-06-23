import unittest

import torch

from BPC_future.scripts.audit_gat_batch_impact_path_token_failure_attribution import (
    _candidate_admission_scores,
    _candidate_path_overlap,
    _candidate_token_values,
    _lcs_ratio,
    _pair_margin_summary,
    _row_score_summary,
)


class _Sample:
    pass


class PathTokenFailureAttributionTest(unittest.TestCase):
    def _sample(self) -> _Sample:
        sample = _Sample()
        sample.candidate_path_token_ids = torch.tensor(
            [
                [11, 22, 0],
                [22, 33, 44],
            ],
            dtype=torch.long,
        )
        sample.candidate_path_pair_ids = torch.tensor(
            [
                [101, 102, 0],
                [102, 103, 104],
            ],
            dtype=torch.long,
        )
        sample.candidate_path_type_ids = torch.tensor(
            [
                [1, 3, 0],
                [1, 2, 3],
            ],
            dtype=torch.long,
        )
        sample.candidate_path_token_mask = torch.tensor(
            [
                [True, True, False],
                [True, True, True],
            ],
            dtype=torch.bool,
        )
        sample.batch_impact_candidate_signature_ids = ["sig-a", "sig-b"]
        sample.batch_impact_candidate_ids = ["cand-a", "cand-b"]
        sample.y_candidate_high_priority = torch.tensor([1.0, 0.0])
        sample.y_candidate_delay_risk = torch.tensor([0.0, 1.0])
        return sample

    def test_candidate_token_values_honor_mask(self) -> None:
        sample = self._sample()

        self.assertEqual(
            _candidate_token_values(sample, 0, "candidate_path_token_ids"),
            [11, 22],
        )
        self.assertEqual(
            _candidate_token_values(sample, 1, "candidate_path_type_ids"),
            [1, 2, 3],
        )

    def test_risk_adjusted_admission_scores(self) -> None:
        scores = _candidate_admission_scores(
            [0.8, 0.9],
            [0.5, 0.1],
            gate_config={
                "candidate_admission_score_mode": "risk_adjusted_product",
                "candidate_delay_score_penalty": 1.0,
            },
        )

        self.assertAlmostEqual(scores[0], 0.4)
        self.assertAlmostEqual(scores[1], 0.81)

    def test_row_score_summary_and_pair_margin(self) -> None:
        sample = self._sample()
        output = {
            "high_priority_probability": torch.tensor([0.8, 0.3]),
            "delay_risk_probability": torch.tensor([0.1, 0.7]),
            "candidate_action_priority_probability": torch.tensor([0.6, 0.2]),
            "candidate_path_embedding": torch.ones((2, 3)),
            "candidate_embedding": torch.ones((2, 4)),
        }
        positive_scores = _row_score_summary(
            sample,
            output,
            gate_config={
                "candidate_admission_score_mode": "risk_adjusted_product",
                "candidate_delay_score_penalty": 1.0,
            },
        )
        negative_scores = {
            **positive_scores,
            "raw": {**positive_scores["raw"], "max_score": 0.7},
            "admission": {**positive_scores["admission"], "max_score": 0.5},
            "delay_risk": {**positive_scores["delay_risk"], "max_score": 0.2},
        }

        margins = _pair_margin_summary(positive_scores, negative_scores)

        self.assertEqual(positive_scores["raw"]["max_index"], 0)
        self.assertAlmostEqual(margins["raw_margin"], 0.1)
        self.assertAlmostEqual(margins["admission_margin"], 0.22)
        self.assertAlmostEqual(margins["delay_risk_margin"], -0.5)
        self.assertFalse(margins["pair_pass"])

    def test_path_overlap_sequence_metrics(self) -> None:
        left = {
            "index": 0,
            "signature_id": "left",
            "path_token_ids": [1, 2, 3],
            "path_pair_ids": [10, 20, 30],
            "path_type_ids": [1, 2, 3],
        }
        right = {
            "index": 1,
            "signature_id": "right",
            "path_token_ids": [2, 3, 4],
            "path_pair_ids": [20, 30, 40],
            "path_type_ids": [2, 3, 1],
        }

        overlap = _candidate_path_overlap(left, right)

        self.assertAlmostEqual(overlap["token_jaccard"], 0.5)
        self.assertAlmostEqual(overlap["pair_jaccard"], 0.5)
        self.assertAlmostEqual(_lcs_ratio([1, 2, 3], [2, 3, 4]), 2 / 3)
        self.assertFalse(overlap["exact_token_sequence_match"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.audit_gat_batch_impact_missed_high_roi_diagnosis import (
    audit_missed_high_roi_diagnosis,
)


class GATBatchImpactMissedHighROIDiagnosisTests(unittest.TestCase):
    def test_diagnosis_classifies_candidate_and_embedding_structural_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            score_path = tmp / "score.json"
            embedding_path = tmp / "embedding.json"
            worker_path = tmp / "worker.json"
            training_path = tmp / "training.json"
            _write_json(
                score_path,
                _score_summary(
                    missed=4,
                    bucket_counts={"deep_candidate_score_gap": 3, "moderate_candidate_score_gap": 1},
                    max_margin=-0.07,
                ),
            )
            _write_json(
                embedding_path,
                _embedding_summary(
                    missed=4,
                    nearest_negative_closer=3,
                    missed_knn_fraction=0.10,
                    accepted_knn_fraction=0.60,
                ),
            )
            _write_json(worker_path, _worker_summary(positive=1, nonpositive=3))
            _write_json(training_path, _training_summary(checkpoint_gate_pass=False))

            summary = audit_missed_high_roi_diagnosis(
                score_margin_summary=score_path,
                embedding_summary=embedding_path,
                worker_rows_summary=worker_path,
                next_training_summary=training_path,
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

        decision = summary["decision_summary"]
        self.assertEqual(
            decision["primary"],
            "candidate_head_score_gap_plus_embedding_structural_gap",
        )
        self.assertEqual(decision["near_threshold_miss_count"], 0)
        self.assertEqual(decision["missed_nearest_negative_closer_count"], 3)
        self.assertEqual(
            decision["family_classification_counts"],
            {"mixed_candidate_head_embedding_gap": 1},
        )
        self.assertTrue(decision["worker_feedback"]["hard_negative_dominant"])
        self.assertEqual(
            decision["recommended_next_step"],
            "collect_train_split_same_context_positive_negative_pairs_and_delay_hard_negatives",
        )
        self.assertFalse(summary["runs_bpc_or_pricing"])
        self.assertFalse(summary["selector_can_certificate"])

    def test_diagnosis_classifies_threshold_borderline_when_near_bucket_dominates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            score_path = tmp / "score.json"
            embedding_path = tmp / "embedding.json"
            _write_json(
                score_path,
                _score_summary(
                    missed=3,
                    bucket_counts={"near_candidate_threshold": 3},
                    max_margin=-0.01,
                ),
            )
            _write_json(
                embedding_path,
                _embedding_summary(
                    missed=3,
                    nearest_negative_closer=0,
                    missed_knn_fraction=0.70,
                    accepted_knn_fraction=0.60,
                ),
            )

            summary = audit_missed_high_roi_diagnosis(
                score_margin_summary=score_path,
                embedding_summary=embedding_path,
                worker_rows_summary=None,
                next_training_summary=None,
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

        decision = summary["decision_summary"]
        self.assertEqual(decision["primary"], "threshold_borderline_missed_high_roi")
        self.assertEqual(decision["near_threshold_miss_count"], 3)
        self.assertEqual(
            decision["recommended_next_step"],
            "audit_precision_safe_threshold_frontier_before_lowering_candidate_threshold",
        )


def _score_summary(
    *,
    missed: int,
    bucket_counts: dict[str, int],
    max_margin: float,
) -> dict[str, object]:
    return {
        "schema_version": "gat_batch_impact_score_margin_audit_v1",
        "all_checks_pass": True,
        "margin_summary": {
            "accepted_high_roi_opportunities": 2,
            "candidate_threshold": 0.9,
            "candidate_margin_bucket_counts": bucket_counts,
            "family": {
                "sector-wave": {
                    "candidate_margin_bucket_counts": bucket_counts,
                    "missed_high_roi_opportunities": missed,
                    "missed_without_same_context_contrast_count": 1,
                    "task_count_counts": {"20": missed},
                }
            },
            "missed_candidate_score_margin_mean": -0.2,
            "missed_candidate_score_margin_min": -0.5,
            "missed_candidate_score_margin_max": max_margin,
            "missed_high_roi_opportunities": missed,
            "missed_without_same_context_contrast_count": 1,
        },
    }


def _embedding_summary(
    *,
    missed: int,
    nearest_negative_closer: int,
    missed_knn_fraction: float,
    accepted_knn_fraction: float,
) -> dict[str, object]:
    return {
        "schema_version": "gat_batch_impact_embedding_separation_audit_v1",
        "all_checks_pass": True,
        "embedding_summary": {
            "accepted_high_roi_knn_positive_fraction_mean": accepted_knn_fraction,
            "family": {
                "sector-wave": {
                    "missed_high_roi_opportunities": missed,
                    "missed_nearest_negative_closer_count": nearest_negative_closer,
                }
            },
            "missed_high_roi_opportunities": missed,
            "missed_knn_positive_fraction_mean": missed_knn_fraction,
            "missed_nearest_negative_closer_count": nearest_negative_closer,
        },
    }


def _worker_summary(*, positive: int, nonpositive: int) -> dict[str, object]:
    return {
        "schema_version": "gat_multibatch_worker_batch_impact_rows_summary_v1",
        "row_count": positive + nonpositive,
        "positive_trajectory_roi_count": positive,
        "nonpositive_trajectory_roi_count": nonpositive,
        "roi_class_counts": {
            "positive_retry_roi": positive,
            "negative_retry_roi": nonpositive,
        },
    }


def _training_summary(*, checkpoint_gate_pass: bool) -> dict[str, object]:
    return {
        "schema_version": "gat_batch_impact_training_summary_v1",
        "checkpoint_gate_pass": checkpoint_gate_pass,
        "stage4_candidate_ready": False,
        "validation_deployment_metrics": {
            "accepted_batch_count": 4,
            "false_high_priority_on_delay": 0.01,
            "false_safe_rate_union": 0.01,
            "safe_precision_ci_low": 0.75,
            "threshold_local_reject_reasons": [
                "safe_precision_ci_low_below_threshold_or_not_measurable"
            ],
        },
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()

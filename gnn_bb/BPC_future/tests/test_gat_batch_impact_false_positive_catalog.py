from __future__ import annotations

import unittest

from BPC_future.scripts.audit_gat_batch_impact_false_positive_catalog import (
    catalog_candidate_decisions_for_record,
    summarize_false_positive_catalog,
)


class GATBatchImpactFalsePositiveCatalogTests(unittest.TestCase):
    def test_catalog_counts_false_high_priority_on_delay_candidates(self) -> None:
        record = {
            "family": "sector-wave",
            "context_hash": "ctx",
            "batch_score": 0.9,
            "candidate_scores": [0.8, 0.2, 0.9],
            "candidate_delay_scores": [0.1, 0.2, 0.7],
            "candidate_high_priority_labels": [1, 0, 0],
            "candidate_delay_labels": [0, 1, 1],
            "batch_roi_positive": 0,
            "bad_mode_switch": 1,
            "tail_improved": 0,
            "support_changed_good": 0,
            "accepted_batch_roi_label": -1.0,
        }
        metadata = {
            "sample_index": 3,
            "sample_path": "samples/sample_000003.pt",
            "source_file": "capture.jsonl",
            "row_index": 7,
            "instance": "inst",
            "instance_path": "inst.json",
            "family": "sector-wave",
            "region": "apollo15_20km",
            "task_count": 20,
            "context_hash": "ctx",
            "batch_type": "new_task_set",
            "accepted_batch_roi_label": -1.0,
            "label_batch_roi_positive": 0,
            "objective_improvement": 2.0,
            "candidate_ids": ["a", "b", "c"],
            "candidate_signature_ids": ["sig-a", "sig-b", "sig-c"],
        }
        gate_config = {
            "candidate_admission_score_mode": "risk_adjusted_product",
            "candidate_delay_score_penalty": 1.0,
            "candidate_delay_gate_enabled": True,
            "candidate_delay_risk_threshold": 0.5,
        }
        rows, false_rows, stats, record_row = catalog_candidate_decisions_for_record(
            record=record,
            metadata=metadata,
            raw_candidate_features=[
                [-0.1, 10.0, 2.0],
                [-0.2, 11.0, 3.0],
                [-0.3, 12.0, 4.0],
            ],
            candidate_feature_schema=["true_reduced_cost", "cost", "task_count"],
            batch_threshold=0.0,
            candidate_threshold=0.0,
            gate_config=gate_config,
            batch_thresholds_by_family={},
            fallback_families=set(),
            fallback_contexts=set(),
        )

        self.assertEqual(len(rows), 3)
        self.assertEqual(len(false_rows), 1)
        self.assertEqual(false_rows[0]["candidate_signature_id"], "sig-b")
        self.assertTrue(false_rows[0]["false_high_priority_on_delay"])
        self.assertEqual(stats["predicted_candidate_count"], 2)
        self.assertEqual(stats["candidate_delay_gate_blocked_count"], 1)
        self.assertEqual(stats["delay_label_count"], 2)
        self.assertEqual(stats["false_high_priority_on_delay_count"], 1)
        self.assertEqual(record_row["false_high_priority_on_delay_count"], 1)
        self.assertEqual(
            false_rows[0]["candidate_feature_values"]["true_reduced_cost"],
            -0.2,
        )

    def test_summary_marks_threshold_zero_and_keeps_exact_safe_contract(self) -> None:
        false_row = {
            "family": "sector-wave",
            "context_hash": "ctx",
            "task_count": 20,
            "accepted_batch_roi_label": -1.0,
            "predicted_delay_risk_score": 0.2,
            "raw_high_priority_score": 0.2,
            "candidate_admission_score": 0.16,
            "delay_gate_margin": 0.3,
            "candidate_score_margin": 0.16,
            "candidate_feature_values": {
                "true_reduced_cost": -0.2,
                "cost": 11.0,
            },
        }
        summary = summarize_false_positive_catalog(
            false_positive_rows=[false_row],
            all_candidate_rows=[false_row],
            record_rows=[],
            context_rows=[
                {
                    "family": "sector-wave",
                    "context_hash": "ctx",
                    "false_high_priority_on_delay_count": 1,
                }
            ],
            stats={
                "batch_record_count": 1,
                "fallback_batch_record_count": 0,
                "evaluated_batch_record_count": 1,
                "candidate_count": 3,
                "evaluated_candidate_count": 3,
                "predicted_candidate_count": 2,
                "high_priority_true_positive_count": 1,
                "false_high_priority_on_delay_count": 1,
                "delay_label_count": 2,
                "candidate_delay_gate_blocked_count": 1,
                "candidate_risk_adjusted_suppressed_count": 0,
                "candidate_rescue_window_eligible_count": 0,
                "candidate_rescue_window_promoted_count": 0,
            },
            selected_metrics={
                "threshold_mode": "family_delay_fallback",
                "batch_threshold": 0.0,
                "candidate_threshold": 0.0,
                "high_priority_prediction_count": 2,
                "high_priority_true_positive_count": 1,
                "false_high_priority_on_delay_count": 1,
                "delay_label_count": 2,
                "candidate_delay_gate_blocked_count": 1,
                "candidate_risk_adjusted_suppressed_count": 0,
                "candidate_rescue_window_eligible_count": 0,
                "candidate_rescue_window_promoted_count": 0,
                "family_delay_fallback_families": ["greedy-anchor"],
            },
            gate_config={
                "candidate_admission_score_mode": "risk_adjusted_product",
                "candidate_delay_score_penalty": 1.0,
                "candidate_delay_gate_enabled": True,
                "candidate_delay_risk_threshold": 0.5,
            },
            candidate_feature_schema=["true_reduced_cost", "cost"],
            split="validation",
            top_k=5,
            training_summary={"stage4_candidate_ready": False, "production_ready": False},
        )

        self.assertTrue(summary["candidate_threshold_zero"])
        self.assertEqual(summary["false_high_priority_on_delay_count"], 1)
        self.assertEqual(summary["delay_label_count"], 2)
        self.assertTrue(summary["all_metric_counts_match"])
        self.assertEqual(
            summary["candidate_threshold_zero_effect"],
            "candidate_head_threshold_disabled_delay_gate_is_only_filter",
        )
        self.assertIn(
            "candidate_threshold_zero_disables_candidate_head_as_a_filter",
            summary["diagnosis"]["findings"],
        )
        self.assertFalse(summary["diagnosis"]["stage4_candidate_ready"])


if __name__ == "__main__":
    unittest.main()

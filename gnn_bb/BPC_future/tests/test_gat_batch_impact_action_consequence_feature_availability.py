from __future__ import annotations

import unittest

from BPC_future.scripts.audit_gat_batch_impact_action_consequence_feature_availability import (
    primary_diagnosis,
    summarize_availability,
    summarize_candidate_payload,
)


class GATBatchImpactActionConsequenceFeatureAvailabilityTests(unittest.TestCase):
    def test_candidate_payload_marks_arc_tokens_slack_and_interactions(self) -> None:
        signature = [[[1, 2], ["0->1:low_time:0", "1->2:low_energy:1", "2->0:low_risk:2"], 5.0]]
        sample = _sample(signature_id="sig-a")
        event = {
            "pool_task_sets": [[1, 2], [3]],
            "pool_signatures": [signature],
            "branch_constraints": [{"type": "same_vehicle"}],
            "cut_duals": {"cut-a": -0.5},
        }
        journey = {
            "task_set": [1, 2],
            "sequence": [1, 2],
            "signature": signature,
            "cut_coefficients": {"cut-a": 1.0},
            "true_reduced_cost": -3.0,
            "trips": [
                {
                    "arc_option_ids": [
                        "0->1:low_time:0",
                        "1->2:low_energy:1",
                        "2->0:low_risk:2",
                    ],
                    "service_start": {"1": 10.0, "2": 25.0},
                    "survival_energy": 4.0,
                    "occupancy": {"1": 1.0},
                    "tasks": [1, 2],
                }
            ],
        }

        row = summarize_candidate_payload(
            sample=sample,
            row={"source_file": "capture.jsonl"},
            event=event,
            journey=journey,
            candidate_index=0,
            task_time_windows={1: (0.0, 50.0), 2: (20.0, 60.0)},
        )

        self.assertTrue(row["has_arc_option_token_sequence"])
        self.assertTrue(row["has_parseable_arc_option_tokens"])
        self.assertTrue(row["has_time_window_slack"])
        self.assertEqual(row["min_time_window_late_slack"], 35.0)
        self.assertTrue(row["has_resource_slack"])
        self.assertTrue(row["has_pool_overlap_proxy"])
        self.assertTrue(row["task_set_in_pool"])
        self.assertTrue(row["signature_in_pool"])
        self.assertTrue(row["has_branch_payload"])
        self.assertTrue(row["has_cut_payload"])

    def test_summary_marks_missing_arc_tokens_as_primary_gap(self) -> None:
        sample = _sample(signature_id="sig-b")
        row = summarize_candidate_payload(
            sample=sample,
            row={},
            event={"pool_task_sets": [[1]]},
            journey={
                "task_set": [1],
                "sequence": [1],
                "trips": [{"service_start": {"1": 10.0}, "tasks": [1]}],
            },
            candidate_index=0,
            task_time_windows={1: (0.0, 50.0)},
        )

        summary = summarize_availability([row], [{"candidate_count": 1}])

        self.assertEqual(summary["arc_token_sequence_coverage"], 0.0)
        self.assertEqual(primary_diagnosis(summary), "arc_option_token_payload_incomplete")


def _sample(*, signature_id: str) -> dict[str, object]:
    return {
        "row_index": 7,
        "context_hash": "ctx",
        "instance": "instance",
        "instance_family": "sector-wave",
        "task_count": 20,
        "candidate_signature_ids": [signature_id],
        "label_batch_roi_positive": 1,
    }


if __name__ == "__main__":
    unittest.main()

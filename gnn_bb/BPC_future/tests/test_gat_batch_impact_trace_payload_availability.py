from __future__ import annotations

import unittest

from BPC_future.scripts.audit_gat_batch_impact_trace_payload_availability import (
    extract_journey_trace_payload_features,
    payload_availability_flags,
    primary_diagnosis,
    proposed_candidate_trace_feature_schema,
    recommended_next_step,
    summarize_payload_availability,
)


class GATBatchImpactTracePayloadAvailabilityTests(unittest.TestCase):
    def test_extracts_trace_timing_resource_features(self) -> None:
        journey = _journey()

        flags = payload_availability_flags(journey=journey, event={"cuts": [{"id": "c"}]})
        features = extract_journey_trace_payload_features(journey)

        self.assertTrue(flags["trip_arc_option_ids"])
        self.assertTrue(flags["trip_service_start"])
        self.assertTrue(flags["event_cuts"])
        self.assertFalse(flags["per_candidate_branch_cut_coefficients"])
        self.assertEqual(features["trace_arc_option_count"], 3.0)
        self.assertEqual(features["trace_low_time_arc_count"], 2.0)
        self.assertEqual(features["trace_low_energy_arc_count"], 1.0)
        self.assertAlmostEqual(features["trace_total_energy"], 7.0)
        self.assertAlmostEqual(features["trace_service_start_span"], 8.0)

    def test_summary_recommends_schema_extension_when_payload_available(self) -> None:
        rows = [
            {
                "target_journey_found": True,
                "source_event_found": True,
                "family": "sector-wave",
                "event_has_cuts": True,
                "event_has_branch_constraints": False,
                "availability": payload_availability_flags(journey=_journey(), event={}),
                "trace_feature_values": extract_journey_trace_payload_features(_journey()),
            }
        ]

        summary = summarize_payload_availability(rows)
        summary["primary"] = primary_diagnosis(summary)
        proposal = proposed_candidate_trace_feature_schema(summary)

        self.assertEqual(
            summary["primary"],
            "trace_timing_resource_payload_available_but_not_in_model_schema",
        )
        self.assertEqual(
            recommended_next_step(summary)["primary"],
            "extend_batch_impact_candidate_schema_with_trace_payload_features",
        )
        self.assertIn("trace_total_energy", proposal["recommended_scalar_features"])
        self.assertIn(
            "per_candidate_branch_cut_coefficients",
            proposal["requires_additional_extraction_or_instrumentation"],
        )


def _journey() -> dict[str, object]:
    return {
        "signature": [["sig"]],
        "sequence": [[1, 2]],
        "task_set": [1, 2],
        "start_time": 5.0,
        "end_time": 25.0,
        "trips": [
            {
                "arc_option_ids": [
                    "0->1:low_time:0",
                    "1->2:low_energy:0",
                    "2->0:low_time:0",
                ],
                "start_time": 5.0,
                "end_time": 25.0,
                "distance": 3.0,
                "energy": 7.0,
                "risk": 0.5,
                "travel_time": 12.0,
                "load": 2.0,
                "survival_energy": 4.0,
                "recharge_time": 1.5,
                "service_start": {"1": 10.0, "2": 18.0},
                "occupancy": {"5": 1.0},
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()

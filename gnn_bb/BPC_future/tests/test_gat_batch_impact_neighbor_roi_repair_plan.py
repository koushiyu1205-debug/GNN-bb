from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_gat_batch_impact_neighbor_roi_repair_plan import (
    build_neighbor_roi_repair_plan,
    build_repair_candidate_rows,
)


class GATBatchImpactNeighborROIRepairPlanTests(unittest.TestCase):
    def test_repair_rows_select_delayed_high_roi_and_accepted_high_roi(self) -> None:
        records = [
            _record(
                "ctx-delayed",
                roi=1.2,
                decision_name="DELAY_QUEUE",
                decision_reason="knn_roi_mean_delay_queue",
            ),
            _record(
                "ctx-low",
                roi=0.2,
                decision_name="DELAY_QUEUE",
                decision_reason="knn_roi_mean_delay_queue",
            ),
            _record(
                "ctx-accepted",
                roi=3.4,
                decision_name="HIGH_PRIORITY",
                decision_reason="high_priority",
            ),
        ]

        rows = build_repair_candidate_rows(records, min_high_roi=0.65)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["repair_type"], "roi_neighbor_delayed_high_roi")
        self.assertEqual(rows[0]["context_hash"], "ctx-delayed")
        self.assertEqual(rows[1]["repair_type"], "accepted_high_point_roi_unstable")
        self.assertFalse(rows[0]["training_label_allowed_before_worker_reachability"])
        self.assertEqual(rows[0]["exact_safe_scope"], "diagnostic_only_no_certificate_effect")

    def test_cli_builder_writes_summary_and_context_priority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records_path = root / "decision_records.jsonl"
            _write_jsonl(
                records_path,
                [
                    _record(
                        "ctx-a",
                        family="random-wave",
                        task_count=50,
                        roi=1.1,
                        decision_name="DELAY_QUEUE",
                        decision_reason="knn_roi_mean_delay_queue",
                    ),
                    _record(
                        "ctx-a",
                        family="random-wave",
                        task_count=50,
                        roi=2.2,
                        decision_name="HIGH_PRIORITY",
                        decision_reason="high_priority",
                    ),
                    _record(
                        "ctx-b",
                        family="sector-wave",
                        task_count=20,
                        roi=0.1,
                        decision_name="DELAY_QUEUE",
                        decision_reason="knn_roi_mean_delay_queue",
                    ),
                ],
            )

            summary = build_neighbor_roi_repair_plan(
                decision_records_jsonl=[records_path],
                output_dir=root / "out",
                report=root / "report.md",
                min_high_roi=0.65,
                top_k=5,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["selector_can_certificate"])
            self.assertFalse(summary["gate_can_permanently_discard_negative_columns"])
            self.assertFalse(summary["stage4_candidate_ready"])
            self.assertEqual(summary["source_record_count"], 3)
            self.assertEqual(summary["repair_candidate_count"], 2)
            self.assertEqual(summary["roi_neighbor_delayed_high_roi_count"], 1)
            self.assertEqual(summary["accepted_high_point_roi_unstable_count"], 1)
            self.assertEqual(summary["top_contexts"][0]["context_hash"], "ctx-a")
            self.assertEqual(
                summary["top_contexts"][0]["primary_action"],
                "collect_same_context_contrast_and_audit_accepted_outliers",
            )
            self.assertTrue((root / "out" / "summary.json").exists())
            self.assertTrue((root / "out" / "repair_candidates.jsonl").exists())
            self.assertTrue((root / "out" / "context_repair_priority.jsonl").exists())
            self.assertTrue((root / "report.md").exists())


def _record(
    context_hash: str,
    *,
    roi: float,
    decision_name: str,
    decision_reason: str,
    family: str = "sector-wave",
    task_count: int = 20,
) -> dict[str, object]:
    return {
        "context_hash": context_hash,
        "instance": f"instances/{context_hash}.json",
        "instance_family": family,
        "instance_task_count": str(task_count),
        "accepted_batch_roi_label": roi,
        "decision_name": decision_name,
        "decision_reason": decision_reason,
        "is_label_unsafe": False,
        "label_high_priority": 1,
        "batch_score": 0.8,
        "candidate_threshold": 0.7,
        "neighbor_accepted_batch_roi_mean": 0.3,
        "neighbor_accepted_batch_roi_ci_low": -0.1,
        "neighbor_accepted_batch_roi_count": 2,
        "neighbor_delay_fraction": 0.0,
        "candidate_predicted_high_priority_count": 4,
        "candidate_rescue_window_promoted_count": 2,
        "candidate_risk_adjusted_suppressed_count": 1,
        "candidate_signature_id_count": 1,
        "candidate_signature_ids": ["sig-a"],
        "high_priority_candidate_signature_ids": ["sig-a"],
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    unittest.main()

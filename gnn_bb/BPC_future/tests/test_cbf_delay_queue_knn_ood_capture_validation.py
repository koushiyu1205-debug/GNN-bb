from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_cbf_delay_queue_knn_ood_capture_validation import (
    audit_capture_validation,
)
from BPC_future.tests.test_cbf_mode_transition_audit import _capture, _journey
from BPC_future.tests.test_cbf_delay_queue_knn_ood_external_validation import _row


class CBFDelayQueueKNNOODCaptureValidationTests(unittest.TestCase):
    def test_capture_validation_builds_dataset_and_preserves_guards(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            train = tmp / "train.jsonl"
            train_rows = [
                _row(instance="a_sector-wave", task_count=20, horizon_feasible=1, state_dual=0.1, action_count=3),
                _row(instance="a_sector-wave", task_count=20, horizon_feasible=0, state_dual=5.0),
                _row(instance="b_sector-wave", task_count=20, horizon_feasible=1, state_dual=0.2, action_count=3),
                _row(instance="b_sector-wave", task_count=20, horizon_feasible=0, state_dual=6.0),
            ]
            train.write_text(
                "\n".join(json.dumps(row, sort_keys=True) for row in train_rows) + "\n",
                encoding="utf-8",
            )

            log_path = tmp / "events.jsonl"
            records = [
                _capture(
                    1,
                    active_hash="active-a",
                    context_hash="ctx-a",
                    objective=100.0,
                    returned=[_journey([2], rc=-2.0, signature="r1")],
                    pool=[_journey([1], rc=0.0, signature="p1")],
                    active_task_sets=[[1]],
                ),
                _capture(
                    2,
                    active_hash="active-b",
                    context_hash="ctx-b",
                    objective=99.0,
                    returned=[_journey([3], rc=-1.0, signature="r2")],
                    pool=[_journey([2], rc=-0.5, signature="p2")],
                    active_task_sets=[[2]],
                ),
                _capture(
                    3,
                    active_hash="active-c",
                    context_hash="ctx-c",
                    objective=98.0,
                    returned=[],
                    pool=[_journey([3], rc=0.2, signature="p3")],
                    active_task_sets=[[3]],
                ),
            ]
            log_path.write_text(
                "\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n",
                encoding="utf-8",
            )

            summary = audit_capture_validation(
                train,
                [log_path],
                output_dir=tmp / "audit",
                report=tmp / "report.md",
                min_validation_rows=1,
                min_validation_high_priority=0,
                min_high_priority_threshold=0.5,
                knn_k=1,
                max_neighbor_unsafe_fraction=0.0,
                safe_radius_quantile=1.0,
                safe_radius_multiplier=10.0,
                epochs=20,
                lr=0.05,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["validation_row_count"], 1)
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertTrue(summary["checks"]["trajectory_dataset_checks_pass"])
            self.assertTrue(summary["checks"]["external_validation_checks_pass"])
            self.assertTrue(summary["checks"]["delay_queue_proof_budget_guard_present"])
            external = summary["external_validation_summary"]
            self.assertIn("decision_reason_counts", external)
            self.assertTrue(
                (tmp / "audit" / "external_validation" / "decision_records.jsonl").exists()
            )
            self.assertTrue((tmp / "audit" / "summary.json").exists())


if __name__ == "__main__":
    unittest.main()

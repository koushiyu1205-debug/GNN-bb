from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.build_cbf_gate_dataset import build_dataset
from BPC_future.tests.test_cbf_mode_transition_audit import _capture, _journey


class CBFBarrierGateDatasetTests(unittest.TestCase):
    def test_build_dataset_flattens_transitions_and_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            log_path = tmp / "events.jsonl"
            records = [
                {
                    "event": "journey_rmp_dual_diagnostics",
                    "cg_iter": 1,
                    "dual_l1_delta": 0.1,
                },
                _capture(
                    1,
                    active_hash="active-a",
                    context_hash="ctx-a",
                    objective=100.0,
                    returned=[_journey([2], rc=-2.0, signature="r1")],
                    pool=[_journey([1], rc=0.0, signature="p1")],
                    active_task_sets=[[1]],
                ),
                {
                    "event": "journey_rmp_dual_diagnostics",
                    "cg_iter": 2,
                    "dual_l1_delta": 10.0,
                },
                _capture(
                    2,
                    active_hash="active-b",
                    context_hash="ctx-b",
                    objective=99.0,
                    returned=[_journey([3, 4], rc=-1.0, sequence=[[3, 4]], signature="r2")],
                    pool=[_journey([2], rc=-0.5, signature="p2")],
                    active_task_sets=[[2]],
                ),
            ]
            log_path.write_text(
                "\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n",
                encoding="utf-8",
            )

            summary = build_dataset(
                [log_path],
                output_dir=tmp / "dataset",
                report=tmp / "report.md",
                min_rows_for_training=2,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["row_count"], 1)
            self.assertFalse(summary["training_ready"])
            row_path = Path(summary["jsonl_path"])
            rows = [
                json.loads(line)
                for line in row_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row["schema_version"], "cbf_gate_dataset_row_v1")
            self.assertTrue(row["diagnostic_only"])
            self.assertFalse(row["certificate_capable"])
            self.assertFalse(row["official_bound_effect"])
            self.assertEqual(row["context_hash"], "ctx-a")
            self.assertEqual(row["next_context_hash"], "ctx-b")
            self.assertEqual(row["action_returned_count"], 1)
            self.assertEqual(row["action_negative_count"], 1)
            self.assertIn("barrier_slack", row)
            self.assertIn("label_cbf_feasible", row)
            self.assertIn("state_t_dual_l1_delta", row)
            self.assertIn("delta_dual_l1_delta", row)

    def test_build_dataset_fails_closed_on_bad_capture(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            log_path = tmp / "events.jsonl"
            records = [
                _capture(
                    1,
                    active_hash="active-a",
                    context_hash="ctx-a",
                    objective=100.0,
                    returned=[_journey([2], rc=-2.0)],
                    pool=[],
                    active_task_sets=[],
                    no_effect=False,
                ),
                _capture(
                    2,
                    active_hash="active-b",
                    context_hash="ctx-b",
                    objective=99.0,
                    returned=[],
                    pool=[],
                    active_task_sets=[],
                ),
            ]
            log_path.write_text(
                "\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n",
                encoding="utf-8",
            )

            summary = build_dataset(
                [log_path],
                output_dir=tmp / "dataset",
                report=tmp / "report.md",
            )

            self.assertFalse(summary["all_checks_pass"])
            self.assertFalse(summary["checks"]["audit_checks_pass"])
            self.assertEqual(summary["row_count"], 0)


if __name__ == "__main__":
    unittest.main()

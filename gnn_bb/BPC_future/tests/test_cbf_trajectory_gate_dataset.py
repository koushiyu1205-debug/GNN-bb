from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.build_cbf_trajectory_gate_dataset import build_trajectory_dataset
from BPC_future.tests.test_cbf_mode_transition_audit import _capture, _journey


class CBFTrajectoryGateDatasetTests(unittest.TestCase):
    def test_build_trajectory_dataset_labels_full_horizon(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            log_path = tmp / "events.jsonl"
            records = [
                {"event": "journey_rmp_dual_diagnostics", "cg_iter": 1, "dual_l1_delta": 5.0},
                _capture(
                    1,
                    active_hash="active-a",
                    context_hash="ctx-a",
                    objective=100.0,
                    returned=[_journey([2], rc=-2.0, signature="r1")],
                    pool=[_journey([1], rc=0.0, signature="p1")],
                    active_task_sets=[[1]],
                ),
                {"event": "journey_rmp_dual_diagnostics", "cg_iter": 2, "dual_l1_delta": 2.0},
                _capture(
                    2,
                    active_hash="active-b",
                    context_hash="ctx-b",
                    objective=98.0,
                    returned=[_journey([3, 4], rc=-1.0, sequence=[[3, 4]], signature="r2")],
                    pool=[_journey([2], rc=-0.5, signature="p2")],
                    active_task_sets=[[2]],
                ),
                {"event": "journey_rmp_dual_diagnostics", "cg_iter": 3, "dual_l1_delta": 1.0},
                _capture(
                    3,
                    active_hash="active-c",
                    context_hash="ctx-c",
                    objective=97.5,
                    returned=[],
                    pool=[_journey([3], rc=0.2, signature="p3")],
                    active_task_sets=[[3]],
                ),
            ]
            log_path.write_text(
                "\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n",
                encoding="utf-8",
            )

            summary = build_trajectory_dataset(
                [log_path],
                output_dir=tmp / "trajectory",
                report=tmp / "report.md",
                horizon_steps=2,
                min_rows_for_training=1,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["one_step_transition_count"], 2)
            self.assertEqual(summary["row_count"], 1)
            row_path = Path(summary["jsonl_path"])
            rows = [
                json.loads(line)
                for line in row_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row["schema_version"], "cbf_trajectory_gate_dataset_row_v1")
            self.assertEqual(row["context_hash"], "ctx-a")
            self.assertEqual(row["next_context_hash"], "ctx-b")
            self.assertEqual(row["horizon_next_context_hash"], "ctx-c")
            self.assertEqual(row["horizon_steps"], 2)
            self.assertIn("horizon_delta_v", row)
            self.assertIn("horizon_barrier_slack", row)
            self.assertIn("label_horizon_cbf_feasible", row)
            self.assertTrue(row["diagnostic_only"])
            self.assertFalse(row["certificate_capable"])
            self.assertFalse(row["official_bound_effect"])

    def test_build_trajectory_dataset_fails_closed_on_bad_capture(self) -> None:
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
                _capture(
                    3,
                    active_hash="active-c",
                    context_hash="ctx-c",
                    objective=98.0,
                    returned=[],
                    pool=[],
                    active_task_sets=[],
                ),
            ]
            log_path.write_text(
                "\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n",
                encoding="utf-8",
            )

            summary = build_trajectory_dataset(
                [log_path],
                output_dir=tmp / "trajectory",
                report=tmp / "report.md",
                horizon_steps=2,
            )

            self.assertFalse(summary["all_checks_pass"])
            self.assertFalse(summary["checks"]["audit_checks_pass"])
            self.assertEqual(summary["row_count"], 0)


if __name__ == "__main__":
    unittest.main()

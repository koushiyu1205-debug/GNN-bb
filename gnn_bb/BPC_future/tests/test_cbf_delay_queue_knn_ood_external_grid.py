from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_cbf_delay_queue_knn_ood_external_grid import (
    audit_external_grid,
)
from BPC_future.tests.test_cbf_delay_queue_knn_ood_external_validation import _row


class CBFDelayQueueKNNOODExternalGridTests(unittest.TestCase):
    def test_external_grid_preserves_guards(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            train = tmp / "train.jsonl"
            validation = tmp / "validation.jsonl"
            train_rows = [
                _row(instance="a_sector-wave", task_count=20, horizon_feasible=1, state_dual=0.1, action_count=3),
                _row(instance="a_sector-wave", task_count=20, horizon_feasible=0, state_dual=5.0),
                _row(instance="b_sector-wave", task_count=20, horizon_feasible=1, state_dual=0.2, action_count=3),
                _row(instance="b_sector-wave", task_count=20, horizon_feasible=0, state_dual=6.0),
            ]
            validation_rows = [
                _row(instance="c_sector-wave", task_count=20, horizon_feasible=1, state_dual=0.15, action_count=3),
                _row(instance="d_sector-wave", task_count=20, horizon_feasible=0, state_dual=5.5),
            ]
            train.write_text(
                "\n".join(json.dumps(row, sort_keys=True) for row in train_rows) + "\n",
                encoding="utf-8",
            )
            validation.write_text(
                "\n".join(json.dumps(row, sort_keys=True) for row in validation_rows) + "\n",
                encoding="utf-8",
            )

            summary = audit_external_grid(
                train,
                validation,
                output_dir=tmp / "grid",
                report=tmp / "report.md",
                k_values=[1],
                max_neighbor_unsafe_fractions=[0.0],
                min_high_priority_thresholds=[0.5],
                safe_radius_quantiles=[1.0],
                safe_radius_multipliers=[1.0, 10.0],
                min_validation_rows=1,
                min_validation_high_priority=0,
                min_train_high_priority=1,
                min_external_candidate_count=1,
                epochs=20,
                lr=0.05,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["trial_count"], 2)
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertTrue(summary["checks"]["delay_queue_exactness_guard_present"])
            self.assertTrue(summary["checks"]["delay_queue_proof_budget_guard_present"])
            self.assertIn("external_candidate_count", summary)
            self.assertTrue((tmp / "grid" / "summary.json").exists())


if __name__ == "__main__":
    unittest.main()

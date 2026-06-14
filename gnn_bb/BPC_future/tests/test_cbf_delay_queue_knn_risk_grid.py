from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_cbf_delay_queue_knn_risk_grid import audit_knn_risk_grid


def _row(
    *,
    instance: str,
    task_count: int,
    horizon_feasible: int,
    state_dual: float,
    action_count: int = 1,
) -> dict[str, object]:
    return {
        "schema_version": "cbf_trajectory_gate_dataset_row_v1",
        "diagnostic_only": True,
        "certificate_capable": False,
        "official_bound_effect": False,
        "source_file": f"/tmp/{instance}.jsonl",
        "instance": instance,
        "task_count": task_count,
        "depth": 0,
        "cg_iter": 1,
        "horizon_steps": 2,
        "v_t": state_dual,
        "h_t": 1.0 - state_dual,
        "action_returned_count": action_count,
        "action_negative_count": action_count,
        "action_unique_task_set_count": action_count,
        "action_avg_task_set_size": float(action_count),
        "state_t_dual_l1_delta": state_dual,
        "state_t_hidden_negative_count": 0.1 * action_count,
        "state_t_mode_negative_count": float(action_count),
        "state_t_z_hash": f"z-{instance}",
        "horizon_v_next": state_dual - 1.0 if horizon_feasible else state_dual + 1.0,
        "horizon_delta_v": -1.0 if horizon_feasible else 1.0,
        "horizon_barrier_slack": 1.0 if horizon_feasible else -1.0,
        "label_cbf_feasible": 1,
        "label_horizon_cbf_feasible": horizon_feasible,
        "label_horizon_bad_mode_transition": 0 if horizon_feasible else 1,
        "label_horizon_delta_v_nonpositive": horizon_feasible,
    }


class CBFDelayQueueKNNRiskGridTests(unittest.TestCase):
    def test_knn_risk_grid_preserves_diagnostic_only_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            dataset = tmp / "cbf_trajectory_gate_transitions.jsonl"
            rows = [
                _row(instance="a_sector-wave", task_count=20, horizon_feasible=1, state_dual=0.1, action_count=3),
                _row(instance="a_sector-wave", task_count=20, horizon_feasible=0, state_dual=5.0),
                _row(instance="b_sector-wave", task_count=20, horizon_feasible=1, state_dual=0.2, action_count=3),
                _row(instance="b_sector-wave", task_count=20, horizon_feasible=0, state_dual=6.0),
            ]
            dataset.write_text(
                "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
                encoding="utf-8",
            )

            summary = audit_knn_risk_grid(
                dataset,
                output_dir=tmp / "grid",
                report=tmp / "report.md",
                k_values=[1, 2],
                max_neighbor_unsafe_fractions=[0.0],
                min_high_priority_thresholds=[0.5, 0.8],
                min_enabled_task_count=20,
                min_scale_rows=2,
                min_family_rows=2,
                min_holdout_rows=1,
                min_train_rows=2,
                min_evaluated_folds=1,
                min_train_high_priority=1,
                epochs=20,
                lr=0.05,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["trial_count"], 4)
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertIn("best_production_candidate_ready", summary)
            self.assertTrue((tmp / "grid" / "summary.json").exists())


if __name__ == "__main__":
    unittest.main()

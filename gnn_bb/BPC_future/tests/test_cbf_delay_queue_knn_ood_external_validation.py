from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_cbf_delay_queue_knn_ood_external_validation import (
    audit_external_validation,
)


def _row(
    *,
    instance: str,
    task_count: int,
    horizon_feasible: int,
    state_dual: float,
    source_file: str | None = None,
    action_count: int = 1,
) -> dict[str, object]:
    return {
        "schema_version": "cbf_trajectory_gate_dataset_row_v1",
        "diagnostic_only": True,
        "certificate_capable": False,
        "official_bound_effect": False,
        "source_file": source_file or f"/tmp/{instance}.jsonl",
        "instance": instance,
        "context_hash": f"ctx-{instance}-{state_dual}",
        "horizon_next_context_hash": f"hctx-{instance}-{state_dual}",
        "task_count": task_count,
        "depth": 0,
        "cg_iter": int(state_dual * 10) + 1,
        "horizon_next_cg_iter": int(state_dual * 10) + 3,
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


class CBFDelayQueueKNNOODExternalValidationTests(unittest.TestCase):
    def test_external_validation_keeps_diagnostic_only_contract(self) -> None:
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

            summary = audit_external_validation(
                train,
                validation,
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
            self.assertEqual(summary["validation_row_count"], 2)
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertFalse(summary["gate_can_permanently_discard_negative_columns"])
            self.assertTrue(summary["negative_columns_must_remain_eventually_reachable"])
            self.assertFalse(summary["delay_queue_can_extend_proof_budget"])
            self.assertFalse(summary["delay_queue_runs_proof_sweep"])
            self.assertIn("overall", summary["validation_metrics"])
            self.assertIn("decision_reason_counts", summary)
            self.assertIn("positive_delay_reason_counts", summary)
            self.assertIn("decision_samples", summary)
            self.assertTrue((tmp / "audit" / "decision_records.jsonl").exists())
            self.assertTrue((tmp / "audit" / "summary.json").exists())


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.train_cbf_gate import cbf_gate_feature_names, train_cbf_gate


def _row(
    *,
    instance: str,
    feasible: int,
    task_count: int = 20,
    state_dual: float = 1.0,
    action_count: int = 1,
    future_delta: float = 0.0,
) -> dict[str, object]:
    return {
        "schema_version": "cbf_gate_dataset_row_v1",
        "diagnostic_only": True,
        "certificate_capable": False,
        "official_bound_effect": False,
        "instance": instance,
        "task_count": task_count,
        "depth": 0,
        "cg_iter": 1,
        "v_t": state_dual,
        "h_t": 1.0 - state_dual,
        "action_returned_count": action_count,
        "action_negative_count": action_count,
        "action_unique_task_set_count": action_count,
        "action_avg_task_set_size": 2.0,
        "state_t_dual_l1_delta": state_dual,
        "state_t_hidden_negative_count": 0.1 * action_count,
        "state_t_mode_negative_count": float(action_count),
        "state_t_z_hash": f"z-{instance}",
        "state_next_dual_l1_delta": state_dual + future_delta,
        "delta_dual_l1_delta": future_delta,
        "delta_v": future_delta,
        "barrier_slack": 1.0 if feasible else -1.0,
        "mode_switched": 1,
        "active_hash_switched": 1,
        "label_cbf_feasible": feasible,
        "label_bad_mode_transition": 0 if feasible else 1,
        "label_delta_v_nonpositive": feasible,
    }


class CBFBarrierGateTrainingTests(unittest.TestCase):
    def test_feature_names_exclude_future_and_label_leakage(self) -> None:
        rows = [
            _row(instance="a", feasible=1, state_dual=1.0, future_delta=-5.0),
            _row(instance="b", feasible=0, state_dual=2.0, future_delta=5.0),
        ]

        names = cbf_gate_feature_names(rows)

        self.assertIn("state_t_dual_l1_delta", names)
        self.assertIn("action_returned_count", names)
        self.assertIn("v_t", names)
        self.assertNotIn("state_next_dual_l1_delta", names)
        self.assertNotIn("delta_dual_l1_delta", names)
        self.assertNotIn("delta_v", names)
        self.assertNotIn("barrier_slack", names)
        self.assertNotIn("label_cbf_feasible", names)
        self.assertNotIn("mode_switched", names)
        self.assertNotIn("active_hash_switched", names)

    def test_training_writes_diagnostic_only_non_certificate_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            dataset = tmp / "cbf_gate_transitions.jsonl"
            rows = [
                _row(instance="train-a", feasible=1, state_dual=0.5, action_count=3, future_delta=-1.0),
                _row(instance="train-a", feasible=1, state_dual=0.4, action_count=2, future_delta=-0.5),
                _row(instance="train-b", feasible=0, state_dual=5.0, action_count=1, future_delta=2.0),
                _row(instance="train-b", feasible=0, state_dual=4.0, action_count=1, future_delta=3.0),
                _row(instance="valid-c", feasible=1, state_dual=0.6, action_count=3, future_delta=-1.0),
                _row(instance="valid-c", feasible=0, state_dual=4.5, action_count=1, future_delta=2.0),
            ]
            dataset.write_text(
                "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
                encoding="utf-8",
            )

            summary = train_cbf_gate(
                dataset,
                output_dir=tmp / "training",
                report=tmp / "report.md",
                epochs=20,
                lr=0.05,
                validation_fraction=0.34,
                seed=3,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["selector_is_pricing_oracle"])
            self.assertFalse(summary["selector_can_certificate"])
            model = json.loads(Path(summary["model_path"]).read_text(encoding="utf-8"))
            self.assertEqual(model["schema_version"], "cbf_linear_gate_model_v1")
            self.assertIn("Never a pricing oracle", model["exactness_contract"])
            self.assertNotIn("state_next_dual_l1_delta", model["feature_names"])


if __name__ == "__main__":
    unittest.main()

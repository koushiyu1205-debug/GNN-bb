from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_cbf_gate_holdout import audit_cbf_gate_holdout


def _row(
    *,
    instance: str,
    feasible: int,
    task_count: int = 20,
    no_effect: bool = True,
    state_dual: float = 1.0,
    action_count: int = 1,
) -> dict[str, object]:
    return {
        "schema_version": "cbf_gate_dataset_row_v1",
        "diagnostic_only": no_effect,
        "certificate_capable": False,
        "official_bound_effect": False if no_effect else True,
        "instance": instance,
        "task_count": task_count,
        "depth": 0,
        "cg_iter": 1,
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
        "state_next_dual_l1_delta": 100.0 if feasible else -100.0,
        "delta_dual_l1_delta": -100.0 if feasible else 100.0,
        "delta_v": -1.0 if feasible else 1.0,
        "barrier_slack": 1.0 if feasible else -1.0,
        "mode_switched": 1,
        "active_hash_switched": 1,
        "label_cbf_feasible": feasible,
        "label_bad_mode_transition": 0 if feasible else 1,
        "label_delta_v_nonpositive": feasible,
    }


class CBFBarrierGateHoldoutAuditTests(unittest.TestCase):
    def test_holdout_audit_is_diagnostic_and_excludes_future_features(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            dataset = tmp / "cbf_gate_transitions.jsonl"
            rows = [
                _row(instance="a", feasible=1, state_dual=0.2, action_count=3),
                _row(instance="a", feasible=0, state_dual=4.0, action_count=1),
                _row(instance="b", feasible=1, state_dual=0.3, action_count=3),
                _row(instance="b", feasible=0, state_dual=5.0, action_count=1),
                _row(instance="c", feasible=1, task_count=10, state_dual=0.4, action_count=3),
                _row(instance="c", feasible=0, task_count=10, state_dual=6.0, action_count=1),
            ]
            dataset.write_text(
                "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
                encoding="utf-8",
            )

            summary = audit_cbf_gate_holdout(
                dataset,
                output_dir=tmp / "audit",
                report=tmp / "report.md",
                min_holdout_rows=2,
                epochs=20,
                lr=0.05,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["selector_is_pricing_oracle"])
            self.assertFalse(summary["selector_can_certificate"])
            self.assertIn("state_t_dual_l1_delta", summary["base_feature_names"])
            self.assertIn("action_returned_count", summary["base_feature_names"])
            self.assertNotIn("state_next_dual_l1_delta", summary["base_feature_names"])
            self.assertNotIn("delta_v", summary["base_feature_names"])
            self.assertNotIn("barrier_slack", summary["base_feature_names"])
            self.assertGreater(summary["instance_holdout_summary"]["evaluated_count"], 0)

    def test_holdout_audit_fails_closed_on_certificate_effect_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            dataset = tmp / "cbf_gate_transitions.jsonl"
            rows = [
                _row(instance="a", feasible=1),
                _row(instance="b", feasible=0, no_effect=False),
            ]
            dataset.write_text(
                "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
                encoding="utf-8",
            )

            summary = audit_cbf_gate_holdout(
                dataset,
                output_dir=tmp / "audit",
                report=tmp / "report.md",
                min_holdout_rows=1,
                epochs=5,
            )

            self.assertFalse(summary["all_checks_pass"])
            self.assertFalse(summary["checks"]["all_rows_no_certificate_effect"])
            self.assertFalse(summary["production_ready"])


if __name__ == "__main__":
    unittest.main()

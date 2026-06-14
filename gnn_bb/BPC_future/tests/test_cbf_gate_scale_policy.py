from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_cbf_gate_scale_policy import audit_scale_policy


def _row(
    *,
    instance: str,
    task_count: int,
    feasible: int,
    state_dual: float,
    action_count: int = 1,
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
        "action_avg_task_set_size": float(action_count),
        "state_t_dual_l1_delta": state_dual,
        "state_t_hidden_negative_count": 0.1 * action_count,
        "state_t_mode_negative_count": float(action_count),
        "state_t_z_hash": f"z-{instance}",
        "delta_v": -1.0 if feasible else 1.0,
        "barrier_slack": 1.0 if feasible else -1.0,
        "label_cbf_feasible": feasible,
        "label_bad_mode_transition": 0 if feasible else 1,
        "label_delta_v_nonpositive": feasible,
    }


class CBFBarrierGateScalePolicyTests(unittest.TestCase):
    def test_scale_policy_forces_small_task_counts_to_abstain(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            dataset = tmp / "cbf_gate_transitions.jsonl"
            rows = [
                _row(instance="small-a", task_count=5, feasible=1, state_dual=0.1),
                _row(instance="small-b", task_count=10, feasible=0, state_dual=10.0),
                _row(instance="big-a", task_count=20, feasible=1, state_dual=0.2, action_count=3),
                _row(instance="big-a", task_count=20, feasible=0, state_dual=4.0),
                _row(instance="big-b", task_count=20, feasible=1, state_dual=0.3, action_count=3),
                _row(instance="big-b", task_count=20, feasible=0, state_dual=5.0),
            ]
            dataset.write_text(
                "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
                encoding="utf-8",
            )

            summary = audit_scale_policy(
                dataset,
                output_dir=tmp / "audit",
                report=tmp / "report.md",
                min_enabled_task_count=20,
                min_scale_rows=2,
                min_holdout_rows=1,
                min_train_rows=2,
                min_evaluated_folds=1,
                epochs=20,
            )

            self.assertTrue(summary["all_checks_pass"])
            by_task = {item["task_count"]: item for item in summary["scale_results"]}
            self.assertTrue(by_task[5]["must_abstain"])
            self.assertEqual(by_task[5]["status"], "guarded_abstain_below_min_task_count")
            self.assertTrue(by_task[10]["must_abstain"])
            self.assertEqual(by_task[10]["reason"], "protect_5_10_no_regression")
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["selector_is_pricing_oracle"])
            self.assertFalse(summary["selector_can_certificate"])

    def test_scale_policy_blocks_scale_with_holdout_false_positive(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            dataset = tmp / "cbf_gate_transitions.jsonl"
            rows = [
                _row(instance="train-a", task_count=20, feasible=1, state_dual=0.1, action_count=3),
                _row(instance="train-a", task_count=20, feasible=0, state_dual=5.0),
                _row(instance="train-b", task_count=20, feasible=1, state_dual=0.2, action_count=3),
                _row(instance="train-b", task_count=20, feasible=0, state_dual=6.0),
                # Held-out instance has an unsafe row that looks like the positive
                # pattern by current-state features.
                _row(instance="bad-c", task_count=20, feasible=0, state_dual=0.15, action_count=3),
                _row(instance="bad-c", task_count=20, feasible=1, state_dual=0.25, action_count=3),
            ]
            dataset.write_text(
                "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
                encoding="utf-8",
            )

            summary = audit_scale_policy(
                dataset,
                output_dir=tmp / "audit",
                report=tmp / "report.md",
                min_enabled_task_count=20,
                min_scale_rows=2,
                min_holdout_rows=1,
                min_train_rows=2,
                min_evaluated_folds=1,
                epochs=80,
                lr=0.05,
            )

            scale20 = next(item for item in summary["scale_results"] if item["task_count"] == 20)
            self.assertFalse(scale20["scale_gate_candidate_ready"])
            self.assertTrue(scale20["must_abstain"])
            self.assertGreaterEqual(scale20["fold_summary"]["false_positive_fold_count"], 1)
            self.assertFalse(summary["scale_policy_ready"])


if __name__ == "__main__":
    unittest.main()

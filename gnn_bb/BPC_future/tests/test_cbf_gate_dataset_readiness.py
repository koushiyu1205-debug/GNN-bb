from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_cbf_gate_dataset_readiness import audit_readiness


def _row(
    *,
    instance: str = "inst",
    task_count: int = 10,
    feasible: int = 1,
    bad_mode: int = 0,
    no_effect: bool = True,
) -> dict[str, object]:
    return {
        "schema_version": "cbf_gate_dataset_row_v1",
        "diagnostic_only": no_effect,
        "certificate_capable": False,
        "official_bound_effect": False if no_effect else True,
        "instance": instance,
        "task_count": task_count,
        "label_cbf_feasible": feasible,
        "label_bad_mode_transition": bad_mode,
        "label_delta_v_nonpositive": feasible,
        "delta_v": -1.0 if feasible else 1.0,
        "barrier_slack": 1.0 if feasible else -1.0,
    }


class CBFBarrierGateDatasetReadinessTests(unittest.TestCase):
    def test_readiness_accepts_balanced_no_effect_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "cbf_gate_transitions.jsonl"
            rows = [
                _row(instance="a", task_count=10, feasible=1),
                _row(instance="b", task_count=20, feasible=0, bad_mode=1),
            ]
            path.write_text(
                "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
                encoding="utf-8",
            )

            summary = audit_readiness(
                [path],
                min_rows=2,
                min_instances=2,
                require_both_labels=True,
                require_task20=True,
            )

        self.assertTrue(summary["all_checks_pass"])
        self.assertTrue(summary["training_ready"])
        self.assertEqual(summary["row_count"], 2)
        self.assertEqual(summary["cbf_feasible_count"], 1)
        self.assertEqual(summary["cbf_infeasible_count"], 1)
        self.assertEqual(summary["task_count_histogram"], {"10": 1, "20": 1})

    def test_readiness_fails_closed_on_certificate_effect_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "cbf_gate_transitions.jsonl"
            rows = [
                _row(instance="a", task_count=10, feasible=1),
                _row(instance="b", task_count=20, feasible=0, bad_mode=1, no_effect=False),
            ]
            path.write_text(
                "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
                encoding="utf-8",
            )

            summary = audit_readiness(
                [path],
                min_rows=2,
                min_instances=2,
                require_both_labels=True,
                require_task20=True,
            )

        self.assertFalse(summary["all_checks_pass"])
        self.assertFalse(summary["training_ready"])
        self.assertFalse(summary["checks"]["all_rows_no_certificate_effect"])


if __name__ == "__main__":
    unittest.main()

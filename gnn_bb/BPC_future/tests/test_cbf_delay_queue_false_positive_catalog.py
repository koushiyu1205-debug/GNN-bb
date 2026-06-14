from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_cbf_delay_queue_false_positive_catalog import (
    build_false_positive_catalog,
)


def _row(
    *,
    instance: str,
    task_count: int,
    horizon_feasible: int,
    state_dual: float,
    source_file: str = "",
    action_count: int = 1,
    no_effect: bool = True,
) -> dict[str, object]:
    return {
        "schema_version": "cbf_trajectory_gate_dataset_row_v1",
        "diagnostic_only": no_effect,
        "certificate_capable": False,
        "official_bound_effect": False if no_effect else True,
        "source_file": source_file,
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


class CBFDelayQueueFalsePositiveCatalogTests(unittest.TestCase):
    def test_catalog_marks_unsafe_high_priority_as_force_delay(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            dataset = tmp / "cbf_trajectory_gate_transitions.jsonl"
            rows = [
                _row(instance="train_a_sector-wave", task_count=20, horizon_feasible=1, state_dual=0.1, action_count=3),
                _row(instance="train_a_sector-wave", task_count=20, horizon_feasible=0, state_dual=5.0),
                _row(instance="train_b_sector-wave", task_count=20, horizon_feasible=1, state_dual=0.2, action_count=3),
                _row(instance="train_b_sector-wave", task_count=20, horizon_feasible=0, state_dual=6.0),
                # This holdout row looks like the safe positives in online
                # features but has an unsafe H=2 label, so it should appear in
                # the false-positive catalog.
                _row(instance="holdout_sector-wave", task_count=20, horizon_feasible=0, state_dual=0.1, action_count=3),
                _row(instance="holdout_sector-wave", task_count=20, horizon_feasible=1, state_dual=0.3, action_count=3),
            ]
            dataset.write_text(
                "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
                encoding="utf-8",
            )

            summary = build_false_positive_catalog(
                dataset,
                output_dir=tmp / "catalog",
                report=tmp / "report.md",
                min_enabled_task_count=20,
                min_scale_rows=2,
                min_family_rows=2,
                min_holdout_rows=1,
                min_train_rows=2,
                min_train_high_priority=1,
                min_high_priority_threshold=0.5,
                epochs=80,
                lr=0.1,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertGreater(summary["false_positive_record_count"], 0)
            self.assertTrue(summary["catalog_requires_force_delay"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["gate_can_permanently_discard_negative_columns"])
            self.assertTrue(summary["negative_columns_must_remain_eventually_reachable"])
            self.assertTrue(summary["finite_delay_required"])
            self.assertFalse(summary["delay_queue_is_proof_blocking"])
            record = summary["false_positive_records"][0]
            self.assertEqual(record["predicted_decision"], "HIGH_PRIORITY")
            self.assertEqual(record["required_safe_decision"], "DELAY_QUEUE")
            self.assertEqual(record["exactness_action"], "force_delay_not_discard")

            records_path = tmp / "catalog" / "false_positive_records.jsonl"
            self.assertTrue(records_path.exists())
            self.assertTrue(records_path.read_text(encoding="utf-8").strip())

    def test_catalog_fails_closed_on_official_effect_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            dataset = tmp / "cbf_trajectory_gate_transitions.jsonl"
            rows = [
                _row(instance="a", task_count=20, horizon_feasible=1, state_dual=0.1),
                _row(instance="b", task_count=20, horizon_feasible=0, state_dual=3.0, no_effect=False),
            ]
            dataset.write_text(
                "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
                encoding="utf-8",
            )

            summary = build_false_positive_catalog(
                dataset,
                output_dir=tmp / "catalog",
                report=tmp / "report.md",
                min_holdout_rows=1,
                min_train_rows=1,
                epochs=5,
            )

            self.assertFalse(summary["all_checks_pass"])
            self.assertFalse(summary["checks"]["all_rows_no_certificate_effect"])
            self.assertFalse(summary["production_ready"])


if __name__ == "__main__":
    unittest.main()

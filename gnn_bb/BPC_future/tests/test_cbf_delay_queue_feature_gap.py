from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_cbf_delay_queue_feature_gap import audit_feature_gap


def _row(
    *,
    instance: str,
    task_count: int,
    horizon_feasible: int,
    state_dual: float,
    action_count: int = 1,
    no_effect: bool = True,
) -> dict[str, object]:
    return {
        "schema_version": "cbf_trajectory_gate_dataset_row_v1",
        "diagnostic_only": no_effect,
        "certificate_capable": False,
        "official_bound_effect": False if no_effect else True,
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
        "state_next_dual_l1_delta": 999.0,
        "delta_v": 999.0,
        "horizon_v_next": state_dual - 1.0 if horizon_feasible else state_dual + 1.0,
        "horizon_delta_v": -1.0 if horizon_feasible else 1.0,
        "horizon_barrier_slack": 1.0 if horizon_feasible else -1.0,
        "label_cbf_feasible": 1,
        "label_horizon_cbf_feasible": horizon_feasible,
        "label_horizon_bad_mode_transition": 0 if horizon_feasible else 1,
        "label_horizon_delta_v_nonpositive": horizon_feasible,
    }


class CBFDelayQueueFeatureGapAuditTests(unittest.TestCase):
    def test_feature_gap_uses_online_features_and_keeps_audit_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            dataset = tmp / "cbf_trajectory_gate_transitions.jsonl"
            rows = [
                _row(instance="safe_a_sector-wave", task_count=20, horizon_feasible=1, state_dual=0.1, action_count=3),
                _row(instance="safe_b_sector-wave", task_count=20, horizon_feasible=1, state_dual=0.2, action_count=3),
                _row(instance="unsafe_a_sector-wave", task_count=20, horizon_feasible=0, state_dual=5.0, action_count=1),
                _row(instance="fp_sector-wave", task_count=20, horizon_feasible=0, state_dual=0.11, action_count=3),
            ]
            dataset.write_text(
                "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
                encoding="utf-8",
            )
            fp_path = tmp / "false_positive_records.jsonl"
            fp_record = {
                "schema_version": "cbf_delay_queue_false_positive_record_v1",
                "diagnostic_only": True,
                "official_bound_effect": False,
                "task_count": 20,
                "family": "sector-wave",
                "row_index": 3,
                "instance": "fp_sector-wave",
                "required_safe_decision": "DELAY_QUEUE",
                "exactness_action": "force_delay_not_discard",
            }
            fp_path.write_text(json.dumps(fp_record, sort_keys=True) + "\n", encoding="utf-8")

            summary = audit_feature_gap(
                dataset,
                fp_path,
                output_dir=tmp / "gap",
                report=tmp / "report.md",
                min_safe_retention=0.0,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["production_ready"])
            self.assertEqual(summary["unique_false_positive_row_count"], 1)
            self.assertEqual(summary["false_positive_by_family"], {"20|sector-wave": 1})
            self.assertIn("state_t_dual_l1_delta", summary["feature_names"])
            self.assertNotIn("state_next_dual_l1_delta", summary["feature_names"])
            self.assertNotIn("delta_v", summary["feature_names"])
            self.assertNotIn("horizon_delta_v", summary["feature_names"])
            self.assertTrue(summary["false_positive_neighbor_profiles"])
            self.assertEqual(
                summary["recommended_action"],
                "force_delay_affected_buckets_and_collect_fp_neighborhood",
            )

    def test_feature_gap_fails_closed_on_official_effect_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            dataset = tmp / "cbf_trajectory_gate_transitions.jsonl"
            rows = [
                _row(instance="safe", task_count=20, horizon_feasible=1, state_dual=0.1),
                _row(instance="fp", task_count=20, horizon_feasible=0, state_dual=0.2, no_effect=False),
            ]
            dataset.write_text(
                "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
                encoding="utf-8",
            )
            fp_path = tmp / "false_positive_records.jsonl"
            fp_path.write_text(
                json.dumps(
                    {
                        "row_index": 1,
                        "task_count": 20,
                        "family": "sector-wave",
                        "official_bound_effect": False,
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = audit_feature_gap(
                dataset,
                fp_path,
                output_dir=tmp / "gap",
                report=tmp / "report.md",
            )

            self.assertFalse(summary["all_checks_pass"])
            self.assertFalse(summary["checks"]["all_rows_no_certificate_effect"])
            self.assertFalse(summary["production_ready"])


if __name__ == "__main__":
    unittest.main()

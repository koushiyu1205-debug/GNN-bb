from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_cbf_trajectory_gate_policy import trajectory_gate_feature_names
from BPC_future.scripts.build_cbf_trajectory_history_dataset import build_history_dataset


def _row(
    *,
    cg_iter: int,
    context_hash: str,
    horizon_feasible: int,
    delta_v: float,
    barrier_slack: float,
) -> dict[str, object]:
    return {
        "schema_version": "cbf_trajectory_gate_dataset_row_v1",
        "diagnostic_only": True,
        "certificate_capable": False,
        "official_bound_effect": False,
        "source_file": "/tmp/source.jsonl",
        "instance": "toy_sector-wave",
        "task_count": 20,
        "node_id": 0,
        "depth": 0,
        "cg_iter": cg_iter,
        "next_cg_iter": cg_iter + 1,
        "context_hash": context_hash,
        "horizon_steps": 2,
        "v_t": 10.0 + cg_iter,
        "h_t": -9.0 - cg_iter,
        "action_returned_count": 4 + cg_iter,
        "action_negative_count": 4 + cg_iter,
        "action_unique_task_set_count": 3 + cg_iter,
        "action_avg_task_set_size": 2.0,
        "state_t_dual_l1_delta": 5.0 + cg_iter,
        "state_t_hidden_negative_count": 0.1,
        "state_t_mode_negative_count": 4.0,
        "state_t_z_hash": f"z-{cg_iter}",
        "state_next_dual_l1_delta": 99.0,
        "delta_v": delta_v,
        "barrier_slack": barrier_slack,
        "mode_switched": 1,
        "active_hash_switched": 1,
        "label_cbf_feasible": int(barrier_slack >= 0.0),
        "label_bad_mode_transition": 0 if delta_v <= 0.0 else 1,
        "label_delta_v_nonpositive": int(delta_v <= 0.0),
        "horizon_v_next": 11.0,
        "horizon_delta_v": -1.0 if horizon_feasible else 1.0,
        "horizon_barrier_slack": 1.0 if horizon_feasible else -1.0,
        "label_horizon_cbf_feasible": horizon_feasible,
        "label_horizon_bad_mode_transition": 0 if horizon_feasible else 1,
        "label_horizon_delta_v_nonpositive": horizon_feasible,
    }


class CBFTrajectoryHistoryDatasetTests(unittest.TestCase):
    def test_history_dataset_uses_only_previous_transition_features(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            source = tmp / "h2.jsonl"
            rows = [
                _row(cg_iter=1, context_hash="ctx-1", horizon_feasible=1, delta_v=-2.0, barrier_slack=3.0),
                _row(cg_iter=2, context_hash="ctx-2", horizon_feasible=0, delta_v=5.0, barrier_slack=-1.0),
            ]
            source.write_text(
                "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
                encoding="utf-8",
            )

            summary = build_history_dataset(
                source,
                output_dir=tmp / "history",
                report=tmp / "report.md",
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["row_count"], 2)
            self.assertGreater(summary["history_feature_count"], 0)
            enriched = [
                json.loads(line)
                for line in Path(summary["jsonl_path"]).read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            first, second = enriched
            self.assertEqual(first["history_prev_available"], 0)
            self.assertEqual(first["history_prev_delta_v"], 0.0)
            self.assertEqual(second["history_prev_available"], 1)
            self.assertEqual(second["history_prev_delta_v"], -2.0)
            self.assertEqual(second["history_prev_barrier_slack"], 3.0)
            self.assertEqual(second["history_prev_action_returned_count"], 5.0)
            feature_names = trajectory_gate_feature_names(enriched)
            self.assertIn("history_prev_delta_v", feature_names)
            self.assertIn("history_prev_label_cbf_feasible", feature_names)
            self.assertNotIn("state_next_dual_l1_delta", feature_names)
            self.assertNotIn("delta_v", feature_names)
            self.assertNotIn("horizon_delta_v", feature_names)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_cbf_mode_transition import audit


def _journey(
    task_set: list[int],
    *,
    rc: float,
    sequence: list[list[int]] | None = None,
    signature: str = "sig",
) -> dict[str, object]:
    seq = sequence if sequence is not None else [task_set]
    return {
        "signature": [signature, task_set],
        "task_set": task_set,
        "sequence": seq,
        "true_reduced_cost": rc,
        "trips": [
            {
                "tasks": sortie,
                "start_time": 0.0,
                "end_time": 10.0,
                "arc_option_ids": ["out", "back"] if len(sortie) == 1 else ["out", "mid", "back"],
                "occupancy": [],
            }
            for sortie in seq
        ],
    }


def _capture(
    cg_iter: int,
    *,
    active_hash: str,
    context_hash: str,
    objective: float,
    returned: list[dict[str, object]],
    pool: list[dict[str, object]],
    active_task_sets: list[list[int]],
    no_effect: bool = True,
) -> dict[str, object]:
    return {
        "event": "journey_counterfactual_replay_capture",
        "schema_version": "journey_counterfactual_replay_capture_v1",
        "time": float(cg_iter),
        "node_id": 0,
        "depth": 0,
        "cg_iter": cg_iter,
        "instance": "unit",
        "task_count": 20,
        "diagnostic_only": no_effect,
        "replay_no_certificate_effect": no_effect,
        "certificate_capable": False,
        "official_bound_effect": False,
        "context_hash": context_hash,
        "true_dual_hash": f"dual-{cg_iter}",
        "cut_hash": "cuts",
        "branch_hash": "branch",
        "forbidden_signature_hash": "forbidden",
        "rmp_objective_before": objective,
        "pricing_state": "FOUND_NEGATIVE" if returned else "INCOMPLETE_LIMIT",
        "active_hash_before": active_hash,
        "active_task_sets": active_task_sets,
        "returned_journey_count": len(returned),
        "captured_journey_count": len(returned),
        "returned_batch_complete": True,
        "returned_batch_truncated": False,
        "returned_journeys": returned,
        "pool_journey_count": len(pool),
        "pool_journey_payload_count": len(pool),
        "pool_snapshot_truncated": False,
        "pool_signature_hash": f"pool-sig-{cg_iter}",
        "pool_task_set_hash": f"pool-task-{cg_iter}",
        "pool_signatures": [journey["signature"] for journey in pool],
        "pool_task_sets": [journey["task_set"] for journey in pool],
        "pool_journeys": pool,
    }


class CBFModeTransitionAuditTests(unittest.TestCase):
    def test_audit_builds_state_action_next_and_barrier_slack(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "events.jsonl"
            records = [
                {
                    "event": "journey_rmp_dual_diagnostics",
                    "cg_iter": 1,
                    "dual_l1_delta": 0.1,
                },
                _capture(
                    1,
                    active_hash="active-a",
                    context_hash="ctx-a",
                    objective=100.0,
                    returned=[_journey([2], rc=-2.0, signature="r1")],
                    pool=[_journey([1], rc=0.0, signature="p1")],
                    active_task_sets=[[1]],
                ),
                {
                    "event": "journey_rmp_dual_diagnostics",
                    "cg_iter": 2,
                    "dual_l1_delta": 1.5,
                },
                _capture(
                    2,
                    active_hash="active-b",
                    context_hash="ctx-b",
                    objective=99.0,
                    returned=[_journey([3, 4], rc=-1.0, sequence=[[3, 4]], signature="r2")],
                    pool=[_journey([2], rc=-0.5, signature="p2")],
                    active_task_sets=[[2]],
                ),
            ]
            log_path.write_text(
                "\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n",
                encoding="utf-8",
            )

            summary = audit([log_path], alpha=0.25, v_crit=1.0)

        self.assertTrue(summary["all_checks_pass"])
        self.assertEqual(summary["capture_event_count"], 2)
        self.assertEqual(summary["transition_count"], 1)
        transition = summary["transitions"][0]
        self.assertEqual(transition["context_hash"], "ctx-a")
        self.assertEqual(transition["next_context_hash"], "ctx-b")
        self.assertEqual(transition["action_negative_count"], 1)
        self.assertTrue(transition["mode_switched"])
        self.assertIn("barrier_slack", transition)
        self.assertIn("v_t_components", transition)
        self.assertIn("state_t_mode", transition)

    def test_bad_capture_no_effect_flag_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "events.jsonl"
            records = [
                _capture(
                    1,
                    active_hash="active-a",
                    context_hash="ctx-a",
                    objective=100.0,
                    returned=[_journey([2], rc=-2.0)],
                    pool=[],
                    active_task_sets=[],
                    no_effect=False,
                ),
                _capture(
                    2,
                    active_hash="active-b",
                    context_hash="ctx-b",
                    objective=99.0,
                    returned=[],
                    pool=[],
                    active_task_sets=[],
                ),
            ]
            log_path.write_text(
                "\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n",
                encoding="utf-8",
            )

            summary = audit([log_path])

        self.assertFalse(summary["all_checks_pass"])
        self.assertEqual(summary["bad_capture_event_count"], 1)
        self.assertFalse(summary["checks"]["all_capture_events_no_certificate_effect"])


if __name__ == "__main__":
    unittest.main()

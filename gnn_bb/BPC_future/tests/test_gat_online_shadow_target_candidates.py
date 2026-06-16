from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.build_gat_online_shadow_target_candidates import (
    build_online_shadow_target_candidates,
)
from BPC_future.solver.gat_candidate_id import journey_gat_candidate_id_from_signature


def _signature(tasks: list[int], *, start: float = 11.0) -> list[list[object]]:
    arcs = ["0->2:low_time:0", "2->1:low_time:0", "1->0:low_time:0"]
    if tasks != [2, 1]:
        arcs = [f"0->{tasks[0]}:low_time:0", f"{tasks[-1]}->0:low_time:0"]
    return [[tasks, arcs, start]]


def _record(
    *,
    signature: list[list[object]],
    task_set: list[int],
    high_priority_label: bool,
    safe_source_decision: bool,
) -> dict[str, object]:
    signature_id = journey_gat_candidate_id_from_signature(signature)
    return {
        "candidate_signature_ids": [signature_id],
        "candidate_task_sets": [task_set],
        "high_priority_candidate_signature_ids": [signature_id] if safe_source_decision else [],
        "decision": 1 if safe_source_decision else 0,
        "decision_name": "HIGH_PRIORITY" if safe_source_decision else "DELAY_QUEUE",
        "label_high_priority": 1 if high_priority_label else 0,
        "instance_family": "sector-wave",
        "instance_task_count": 20,
        "context_hash": "offline-context",
    }


class GATOnlineShadowTargetCandidatesTests(unittest.TestCase):
    def test_builds_context_complete_candidates_and_preserves_target_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            safe_source = tmp / "safe_source.json"
            decision_records = tmp / "decision_records.jsonl"
            capture_dir = tmp / "logs"
            output_dir = tmp / "out"
            report = tmp / "report.md"
            capture_dir.mkdir()

            no_conflict_signature = _signature([2, 1])
            conflict_signature = _signature([3, 4], start=12.0)
            miss_signature = _signature([8, 9], start=13.0)
            safe_source.write_text(
                json.dumps({"safe_source_ready": True, "safe_candidate_ids": []}),
                encoding="utf-8",
            )
            rows = [
                _record(
                    signature=no_conflict_signature,
                    task_set=[1, 2],
                    high_priority_label=True,
                    safe_source_decision=True,
                ),
                _record(
                    signature=conflict_signature,
                    task_set=[3, 4],
                    high_priority_label=True,
                    safe_source_decision=True,
                ),
                _record(
                    signature=conflict_signature,
                    task_set=[3, 4],
                    high_priority_label=False,
                    safe_source_decision=False,
                ),
            ]
            decision_records.write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )

            event = {
                "event": "journey_counterfactual_replay_capture",
                "context_hash": "ctx-online",
                "instance_path": "BPC_future/logical_graph/tasks_020/sector-wave/demo.json",
                "task_count": 20,
                "pricing_state": "FOUND_NEGATIVE",
                "pricing_kind": "exact",
                "cg_iter": 7,
                "true_dual_hash": "dual",
                "cut_hash": "cuts",
                "branch_hash": "branch",
                "forbidden_signature_hash": "forbidden",
                "active_hash_before": "active",
                "pool_signature_hash": "pool-signature",
                "pool_task_set_hash": "pool-task-set",
                "source_log_path": "capture.jsonl",
                "returned_journeys": [
                    {
                        "task_set": [1, 2],
                        "signature": no_conflict_signature,
                        "true_reduced_cost": -20.0,
                        "trips": [
                            {
                                "tasks": [2, 1],
                                "start_time": 11.0,
                                "arc_option_ids": [
                                    "0->2:low_time:0",
                                    "2->1:low_time:0",
                                    "1->0:low_time:0",
                                ],
                            }
                        ],
                    },
                    {
                        "task_set": [3, 4],
                        "signature": conflict_signature,
                        "true_reduced_cost": -10.0,
                    },
                    {
                        "task_set": [8, 9],
                        "signature": miss_signature,
                        "true_reduced_cost": -5.0,
                    },
                ],
            }
            (capture_dir / "capture.jsonl").write_text(
                json.dumps(event) + "\n",
                encoding="utf-8",
            )

            summary = build_online_shadow_target_candidates(
                safe_source=safe_source,
                decision_records=decision_records,
                capture_log_dir=capture_dir,
                output_dir=output_dir,
                report=report,
                max_candidates=3,
                max_conflict_controls=1,
                max_miss_controls=1,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["selector_can_certificate"])
            self.assertEqual(summary["capture_candidate_count"], 3)
            self.assertEqual(summary["selected_candidate_count"], 3)
            self.assertEqual(
                summary["selected_category_counts"],
                {
                    "no_offline_task_set_overlap_control": 1,
                    "task_set_overlap_conflict_control": 1,
                    "task_set_overlap_no_conflict": 1,
                },
            )
            payload = json.loads((output_dir / "candidates.json").read_text(encoding="utf-8"))
            selected = payload["candidates"]
            first = selected[0]
            self.assertEqual(first["selection_category"], "task_set_overlap_no_conflict")
            self.assertEqual(first["target_task_set"], [1, 2])
            self.assertEqual(first["target_sequence"], [2, 1])
            self.assertEqual(first["target_sortie_traces"][0]["sequence"], [2, 1])
            for field in (
                "expected_context_hash",
                "true_dual_hash",
                "cut_hash",
                "branch_hash",
                "forbidden_signature_hash",
                "active_hash_before",
                "pool_signature_hash",
                "pool_task_set_hash",
            ):
                self.assertTrue(first[field])
            self.assertTrue(report.exists())


if __name__ == "__main__":
    unittest.main()

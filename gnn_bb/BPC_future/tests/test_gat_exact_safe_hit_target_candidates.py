from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.build_gat_exact_safe_hit_target_candidates import (
    build_exact_safe_hit_target_candidates,
)
from BPC_future.solver.gat_candidate_id import journey_gat_candidate_id_from_signature


class GATExactSafeHitTargetCandidatesTests(unittest.TestCase):
    def test_exports_only_exact_safe_hits_with_context_and_traces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            safe_source = root / "safe_source.json"
            capture_log_dir = root / "logs"
            model_evidence = root / "evidence.jsonl"
            output_dir = root / "out"
            report = root / "report.md"
            capture_log_dir.mkdir()

            hit_signature = [[[1, 5], ["0->1:a", "1->5:b", "5->0:c"], 0.0]]
            miss_signature = [[[2], ["0->2:a", "2->0:b"], 1.0]]
            hit_id = journey_gat_candidate_id_from_signature(hit_signature)
            miss_id = journey_gat_candidate_id_from_signature(miss_signature)
            safe_source.write_text(
                json.dumps({"safe_source_ready": True, "safe_candidate_ids": [hit_id]}) + "\n",
                encoding="utf-8",
            )
            model_evidence.write_text(
                json.dumps(
                    {
                        "candidate_id": hit_id,
                        "exact_safe_id_hit": True,
                        "admission_ready": False,
                        "admission_blocker": (
                            "exact_safe_id_hit_but_online_trajectory_roi_unverified"
                        ),
                        "evidence_score": 1.25,
                        "best_key_level": "route_no_start",
                        "offline_high_count": 3,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            capture = {
                "event": "journey_counterfactual_replay_capture",
                "pricing_state": "FOUND_NEGATIVE",
                "pricing_kind": "exact",
                "instance_path": "BPC_future/logical_graph/tasks_020/foo.json",
                "task_count": 20,
                "context_hash": "ctx-hit",
                "true_dual_hash": "dual",
                "cut_hash": "cut",
                "branch_hash": "branch",
                "forbidden_signature_hash": "forbidden",
                "active_hash_before": "active",
                "pool_signature_hash": "pool-sig",
                "pool_task_set_hash": "pool-task",
                "cg_iter": 7,
                "returned_journeys": [
                    {
                        "signature": hit_signature,
                        "task_set": [1, 5],
                        "true_reduced_cost": -3.0,
                    },
                    {
                        "signature": miss_signature,
                        "task_set": [2],
                        "true_reduced_cost": -4.0,
                    },
                ],
            }
            (capture_log_dir / "capture.jsonl").write_text(
                json.dumps(capture) + "\n",
                encoding="utf-8",
            )

            summary = build_exact_safe_hit_target_candidates(
                safe_source=safe_source,
                capture_log_dir=capture_log_dir,
                model_evidence=model_evidence,
                output_dir=output_dir,
                report=report,
                max_candidates=8,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["capture_exact_safe_hit_count"], 1)
            self.assertEqual(summary["selected_candidate_count"], 1)
            self.assertEqual(summary["selected_candidate_ids"], [hit_id])
            self.assertNotIn(miss_id, summary["selected_candidate_ids"])
            self.assertEqual(summary["selected_context_counts"], {"ctx-hit": 1})
            self.assertFalse(summary["stage4_mutating_admission_ready"])

            candidates = json.loads((output_dir / "candidates.json").read_text(encoding="utf-8"))
            candidate = candidates["candidates"][0]
            self.assertEqual(candidate["signature_id"], hit_id)
            self.assertTrue(candidate["exact_safe_id_hit"])
            self.assertFalse(candidate["admission_ready"])
            self.assertEqual(candidate["target_sequence"], [1, 5])
            self.assertEqual(candidate["target_arc_option_sequence"], ["0->1:a", "1->5:b", "5->0:c"])
            self.assertEqual(candidate["model_evidence_score"], 1.25)
            self.assertTrue(report.exists())


if __name__ == "__main__":
    unittest.main()

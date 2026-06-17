from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.select_gat_target_priority_worker_ab_runbook_subset import (
    select_runbook_subset,
)


class GATTargetPriorityWorkerABRunbookSubsetTests(unittest.TestCase):
    def test_selects_highest_priority_missed_high_roi_contexts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_file = root / "candidates.json"
            _write_candidates(
                candidates_file,
                [
                    _candidate("ctx-a", "a1", score=5.0, true_rc=-3.0),
                    _candidate("ctx-a", "a2", score=5.0, true_rc=-2.0, rank=2),
                    _candidate("ctx-b", "b1", score=9.0, true_rc=-1.0),
                    _candidate("ctx-b", "b2", score=9.0, true_rc=-0.5, rank=2),
                    _candidate("ctx-c", "c1", score=100.0, true_rc=-10.0, missed=False),
                    _candidate("ctx-c", "c2", score=100.0, true_rc=-9.0, rank=2, missed=False),
                ],
            )

            summary = select_runbook_subset(
                candidates_file=candidates_file,
                output_dir=root / "subset",
                report=root / "report.md",
                max_contexts=1,
                require_missed_high_roi=True,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["certificate_ready"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertEqual(summary["selected_context_count"], 1)
            self.assertEqual(summary["candidate_context_counts"], {"ctx-b": 2})
            self.assertEqual(summary["skipped_counts"], {"after_context_limit": 2, "not_missed_high_roi_context": 1})
            self.assertIn("build_gat_target_priority_worker_ab_runbook.py", summary["runbook_command"])

            payload = json.loads(
                (root / "subset" / "candidates.json").read_text(encoding="utf-8")
            )
            self.assertEqual([candidate["name"] for candidate in payload["candidates"]], ["b1", "b2"])
            self.assertTrue((root / "report.md").exists())
            self.assertTrue((root / "subset" / "runbook_command.txt").exists())

    def test_filters_task_family_and_caps_candidates_per_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_file = root / "candidates.json"
            _write_candidates(
                candidates_file,
                [
                    _candidate("ctx-20", "a1", score=4.0, true_rc=-3.0, family="sector-wave"),
                    _candidate(
                        "ctx-20",
                        "a2",
                        score=4.0,
                        true_rc=-2.0,
                        rank=2,
                        family="sector-wave",
                    ),
                    _candidate(
                        "ctx-20",
                        "a3",
                        score=4.0,
                        true_rc=-1.0,
                        rank=3,
                        family="sector-wave",
                    ),
                    _candidate(
                        "ctx-50",
                        "b1",
                        score=10.0,
                        true_rc=-5.0,
                        task_count=50,
                        family="random-wave",
                    ),
                    _candidate(
                        "ctx-50",
                        "b2",
                        score=10.0,
                        true_rc=-4.0,
                        rank=2,
                        task_count=50,
                        family="random-wave",
                    ),
                ],
            )

            summary = select_runbook_subset(
                candidates_file=candidates_file,
                output_dir=root / "subset",
                report=root / "report.md",
                max_contexts=2,
                max_candidates_per_context=2,
                include_task_counts=[20],
                families=["sector-wave"],
                require_missed_high_roi=True,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["candidate_count"], 2)
            self.assertEqual(summary["candidate_task_count_counts"], {"20": 2})
            self.assertEqual(summary["candidate_family_counts"], {"sector-wave": 2})
            self.assertEqual(summary["candidate_context_counts"], {"ctx-20": 2})
            self.assertEqual(summary["skipped_counts"], {"filtered_candidate": 2})

            payload = json.loads(
                (root / "subset" / "candidates.json").read_text(encoding="utf-8")
            )
            self.assertEqual([candidate["name"] for candidate in payload["candidates"]], ["a1", "a2"])

    def test_context_priority_score_overrides_plain_roi_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_file = root / "candidates.json"
            _write_candidates(
                candidates_file,
                [
                    _candidate("ctx-plain", "plain1", score=100.0, true_rc=-10.0),
                    _candidate("ctx-plain", "plain2", score=100.0, true_rc=-9.0, rank=2),
                    _candidate(
                        "ctx-structural",
                        "structural1",
                        score=1.0,
                        true_rc=-1.0,
                        context_priority_score=50.0,
                    ),
                    _candidate(
                        "ctx-structural",
                        "structural2",
                        score=1.0,
                        true_rc=-0.5,
                        rank=2,
                        context_priority_score=50.0,
                    ),
                ],
            )

            summary = select_runbook_subset(
                candidates_file=candidates_file,
                output_dir=root / "subset",
                report=root / "report.md",
                max_contexts=1,
                require_missed_high_roi=True,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["candidate_context_counts"], {"ctx-structural": 2})
            self.assertEqual(summary["contexts"][0]["max_context_priority_score"], 50.0)
            self.assertEqual(
                summary["contexts"][0]["context_priority_actions"],
                ["collect_same_context_positive_negative_contrast"],
            )

    def test_can_exclude_already_run_contexts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_file = root / "candidates.json"
            _write_candidates(
                candidates_file,
                [
                    _candidate("ctx-old", "old1", score=10.0, true_rc=-5.0),
                    _candidate("ctx-old", "old2", score=10.0, true_rc=-4.0, rank=2),
                    _candidate("ctx-new", "new1", score=5.0, true_rc=-3.0),
                    _candidate("ctx-new", "new2", score=5.0, true_rc=-2.0, rank=2),
                ],
            )

            summary = select_runbook_subset(
                candidates_file=candidates_file,
                output_dir=root / "subset",
                report=root / "report.md",
                max_contexts=1,
                exclude_context_hashes=["ctx-old"],
                require_missed_high_roi=True,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["exclude_context_hashes"], ["ctx-old"])
            self.assertEqual(summary["candidate_count"], 2)
            self.assertEqual(summary["candidate_context_counts"], {"ctx-new": 2})
            self.assertEqual(summary["skipped_counts"], {"excluded_context": 2})

            payload = json.loads(
                (root / "subset" / "candidates.json").read_text(encoding="utf-8")
            )
            self.assertEqual([candidate["name"] for candidate in payload["candidates"]], ["new1", "new2"])


def _write_candidates(path: Path, candidates: list[dict[str, object]]) -> None:
    path.write_text(json.dumps({"candidates": candidates}, indent=2) + "\n", encoding="utf-8")


def _candidate(
    context_hash: str,
    name: str,
    *,
    score: float,
    true_rc: float,
    rank: int = 1,
    missed: bool = True,
    task_count: int = 20,
    family: str = "sector-wave",
    context_priority_score: float | None = None,
) -> dict[str, object]:
    candidate: dict[str, object] = {
        "active_hash_before": "active",
        "best_true_reduced_cost": true_rc,
        "branch_hash": "branch",
        "certificate_effect": False,
        "context_hash": context_hash,
        "context_target_rank": rank,
        "cut_hash": "cut",
        "expected_context_hash": context_hash,
        "forbidden_signature_hash": "forbidden",
        "instance": (
            f"BPC_future/logical_graph/tasks_{task_count:03d}/{family}/"
            f"dummy_tasks{task_count:03d}_logical_graph.json"
        ),
        "instance_family": family,
        "instance_task_count": task_count,
        "name": name,
        "official_bound_effect": False,
        "opportunity_is_high_roi": True,
        "opportunity_is_missed_high_roi": missed,
        "opportunity_score": score,
        "pool_signature_hash": "pool-signature",
        "pool_task_set_hash": "pool-task-set",
        "requires_worker_target_causal_match": True,
        "target_arc_option_sequence": ["0->1:low_risk:0", "1->0:low_risk:0"],
        "target_sequence": [1],
        "target_task_set_new": True,
        "target_task_set_size": 1,
        "training_label_allowed_before_worker_reachability": False,
        "true_dual_hash": "dual",
    }
    if context_priority_score is not None:
        candidate["context_priority_action"] = "collect_same_context_positive_negative_contrast"
        candidate["context_priority_score"] = context_priority_score
    return candidate


if __name__ == "__main__":
    unittest.main()

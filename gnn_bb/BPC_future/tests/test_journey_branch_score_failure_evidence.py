from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_journey_branch_score_failure_evidence import build_failure_evidence


class JourneyBranchScoreFailureEvidenceTest(unittest.TestCase):
    def test_failed_scored_full_run_exports_overlay_and_tree_policy_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance = "BPC_future/logical_graph/tasks_020/fam/demo_seed61000_logical_graph.json"
            run_root = root / "runs"
            score_dir = run_root / "001_demo" / "score_horizon"
            _write_results(
                score_dir / "results.csv",
                [
                    {
                        "instance": instance,
                        "status": "EXTERNAL_TIME_LIMIT",
                        "wall_time": 600.0,
                        "primal_bound": 120.0,
                        "dual_bound": 115.0,
                        "gap": 0.041667,
                        "gap_available": "true",
                        "gap_source": "root_corrected_node_bound",
                    }
                ],
            )
            _write_log(
                score_dir / "logs" / f"{instance}.jsonl",
                [
                    {
                        "event": "journey_branch_candidates",
                        "node_id": 0,
                        "depth": 0,
                        "branch_state_key": "root",
                        "candidate_count": 2,
                        "eligible_count": 2,
                        "baseline_pair": [1, 2],
                        "selected_pair": [3, 4],
                        "selected_score": 0.82,
                        "top": [
                            {
                                "task_i": 3,
                                "task_j": 4,
                                "branch_score": 0.82,
                                "same_mass": 0.4,
                                "fractionality": 0.4,
                                "support_count": 3,
                                "pool_same_allowed": 10,
                                "pool_separate_allowed": 12,
                                "pool_max_child_width": 12,
                                "pool_total_child_width": 22,
                                "pool_balance_gap": 2,
                            }
                        ],
                    },
                    {
                        "event": "journey_branch",
                        "node_id": 0,
                        "depth": 0,
                        "branch_state_key": "root",
                        "candidate_count": 2,
                        "eligible_count": 2,
                        "baseline_pair": [1, 2],
                        "baseline_rank": 1,
                        "selected_pair": [3, 4],
                        "selected_pair_changed": True,
                        "selected_score": 0.82,
                        "selected_score_source": "state:root::node:0:depth:0:3,4",
                        "branch_score_selection_gate_passed": True,
                        "branch_score_selection_gate_reason": "disabled",
                    },
                    {"event": "journey_exact_pricing_retry"},
                    {"event": "journey_exact_pricing_completion_bound_retry"},
                ],
            )

            summary = build_failure_evidence(
                run_root=run_root,
                output_dir=root / "out",
                report=root / "report.md",
                source_experiment="unit",
            )

            self.assertEqual(summary["result_rows"], 1)
            self.assertEqual(summary["nonoptimal_result_rows"], 1)
            self.assertEqual(summary["hard_negative_rows"], 1)
            self.assertEqual(summary["tree_policy_rows"], 1)
            self.assertEqual(summary["completion_bound_retry_count"], 1)
            self.assertEqual(summary["ordinary_retry_count"], 1)
            hard_rows = _read_jsonl(root / "out" / "score_timeout_hard_negative_rows.jsonl")
            self.assertEqual(hard_rows[0]["selected_pair"], [3, 4])
            self.assertEqual(hard_rows[0]["y_branch_score_hard_negative"], 1.0)
            self.assertEqual(hard_rows[0]["run_completion_bound_retry_count"], 1)
            tree_rows = _read_jsonl(root / "out" / "tree_policy_event_rows.jsonl")
            self.assertEqual(tree_rows[0]["tree_policy_label_type"], "proof_tail_full_run_timeout_hard_negative")
            self.assertEqual(tree_rows[0]["y_tree_policy_hard_negative"], 1.0)
            self.assertTrue(tree_rows[0]["proof_tail_risk"])
            self.assertGreater(tree_rows[0]["event_loss_weight"], 0.0)

    def test_flat_batch_layout_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance = "BPC_future/logical_graph/tasks_020/fam/demo_seed61001_logical_graph.json"
            run_root = root / "flat"
            _write_results(
                run_root / "results.csv",
                [
                    {
                        "instance": instance,
                        "status": "EXTERNAL_TIME_LIMIT",
                        "wall_time": 600.0,
                        "primal_bound": 130.0,
                        "dual_bound": 120.0,
                        "gap": 0.076923,
                        "gap_available": "true",
                        "gap_source": "root_corrected_node_bound",
                    }
                ],
            )
            _write_log(
                run_root / "logs" / f"{instance}.jsonl",
                [
                    {
                        "event": "journey_branch_candidates",
                        "node_id": 7,
                        "depth": 3,
                        "branch_state_key": "RF(1,2)=same_vehicle",
                        "candidate_count": 4,
                        "eligible_count": 4,
                        "baseline_pair": [1, 3],
                        "selected_pair": [5, 6],
                        "selected_score": 0.77,
                        "top": [{"task_i": 5, "task_j": 6, "branch_score": 0.77}],
                    },
                    {
                        "event": "journey_branch",
                        "node_id": 7,
                        "depth": 3,
                        "branch_state_key": "RF(1,2)=same_vehicle",
                        "candidate_count": 4,
                        "eligible_count": 4,
                        "baseline_pair": [1, 3],
                        "selected_pair": [5, 6],
                        "selected_pair_changed": True,
                        "selected_score": 0.77,
                        "selected_score_source": "state:RF(1,2)=same_vehicle::node:7:depth:3:5,6",
                    },
                    {"event": "journey_exact_pricing_completion_bound_retry"},
                ],
            )

            summary = build_failure_evidence(
                run_root=run_root,
                output_dir=root / "out",
                report=root / "report.md",
                source_experiment="flat-unit",
            )

            self.assertEqual(summary["result_rows"], 1)
            self.assertEqual(summary["hard_negative_rows"], 1)
            self.assertEqual(summary["completion_bound_retry_count"], 1)
            rows = _read_jsonl(root / "out" / "score_timeout_hard_negative_rows.jsonl")
            self.assertEqual(rows[0]["node_id"], 7)
            self.assertEqual(rows[0]["depth"], 3)
            self.assertEqual(rows[0]["selected_pair"], [5, 6])


def _write_results(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "instance",
        "status",
        "wall_time",
        "primal_bound",
        "dual_bound",
        "gap",
        "gap_available",
        "gap_source",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _write_log(path: Path, events: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
        encoding="utf-8",
    )


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


if __name__ == "__main__":
    unittest.main()

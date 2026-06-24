from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_journey_branch_score_map import build_branch_score_map


class JourneyBranchScoreMapTests(unittest.TestCase):
    def test_builds_node_depth_score_map_from_ranking_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            ranking_dir = tmp_path / "ranking"
            ranking_dir.mkdir()
            rows = [
                _ranking_row(
                    node_id=0,
                    depth=0,
                    better_pair=[3, 18],
                    worse_pair=[5, 8],
                    wall_gap=120.0,
                    exact_gap=20.0,
                ),
                _ranking_row(
                    node_id=1,
                    depth=1,
                    better_pair=[1, 4],
                    worse_pair=[1, 7],
                    wall_gap=6.0,
                    exact_gap=2.0,
                ),
            ]
            (ranking_dir / "counterfactual_ranking_pair_rows.jsonl").write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

            summary = build_branch_score_map(
                [ranking_dir],
                tmp_path / "out",
                tmp_path / "report.md",
                key_scope="node_depth",
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertEqual(summary["ranking_pair_row_count"], 2)
            self.assertEqual(summary["branch_score_map_entry_count"], 4)
            self.assertEqual(summary["solver_priority_mode"], "branch_score")

            score_map = json.loads((tmp_path / "out" / "journey_branch_score_map.json").read_text())
            self.assertGreater(score_map["node:0:depth:0:3,18"], 0.0)
            self.assertLess(score_map["node:0:depth:0:5,8"], 0.0)
            self.assertGreater(score_map["node:1:depth:1:1,4"], 0.0)
            self.assertLess(score_map["node:1:depth:1:1,7"], 0.0)

            score_rows = json.loads((tmp_path / "out" / "journey_branch_score_rows.json").read_text())
            first = next(row for row in score_rows if row["key"] == "node:0:depth:0:3,18")
            self.assertEqual(first["task_i"], 3)
            self.assertEqual(first["task_j"], 18)
            self.assertEqual(first["win_count"], 1)
            self.assertEqual(first["loss_count"], 0)
            self.assertIn("official_bound_effect = False", (tmp_path / "report.md").read_text())

    def test_pair_scope_aggregates_repeated_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            rows_path = tmp_path / "ranking_rows.jsonl"
            rows = [
                _ranking_row(node_id=0, depth=0, better_pair=[2, 5], worse_pair=[3, 8], wall_gap=10.0),
                _ranking_row(node_id=1, depth=1, better_pair=[2, 5], worse_pair=[4, 8], wall_gap=20.0),
            ]
            rows_path.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

            summary = build_branch_score_map(
                [rows_path],
                tmp_path / "out",
                tmp_path / "report.md",
                key_scope="pair",
                wall_gap_scale=10.0,
                exact_gap_scale=10.0,
            )

            self.assertEqual(summary["branch_score_map_entry_count"], 3)
            score_rows = json.loads((tmp_path / "out" / "journey_branch_score_rows.json").read_text())
            row_25 = next(row for row in score_rows if row["key"] == "2,5")
            self.assertEqual(row_25["comparison_count"], 2)
            self.assertEqual(row_25["win_count"], 2)
            self.assertGreater(row_25["score"], 0.0)

    def test_instance_filters_support_leave_instance_out_maps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            rows_path = tmp_path / "ranking_rows.jsonl"
            rows = [
                _ranking_row(
                    instance="BPC_future/logical_graph/tasks_020/train/train_seed1.json",
                    better_pair=[2, 5],
                    worse_pair=[3, 8],
                    wall_gap=10.0,
                ),
                _ranking_row(
                    instance="BPC_future/logical_graph/tasks_020/holdout/holdout_seed2.json",
                    better_pair=[4, 5],
                    worse_pair=[4, 8],
                    wall_gap=20.0,
                ),
            ]
            rows_path.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

            summary = build_branch_score_map(
                [rows_path],
                tmp_path / "out",
                tmp_path / "report.md",
                key_scope="pair",
                exclude_instance_contains=("holdout_seed2",),
            )

            self.assertEqual(summary["raw_ranking_pair_row_count"], 2)
            self.assertEqual(summary["ranking_pair_row_count"], 1)
            self.assertEqual(summary["filtered_out_row_count"], 1)
            self.assertEqual(summary["exclude_instance_contains"], ["holdout_seed2"])
            score_map = json.loads((tmp_path / "out" / "journey_branch_score_map.json").read_text())
            self.assertIn("2,5", score_map)
            self.assertNotIn("4,5", score_map)

    def test_child_probe_rows_build_proof_cost_score_map(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            probe_dir = tmp_path / "probe"
            probe_dir.mkdir()
            rows = [
                _child_probe_row(
                    branch_node_id=0,
                    branch_depth=0,
                    pair=[2, 6],
                    child_node_id=1,
                    complete=True,
                    right_censored=False,
                    fathomed=True,
                    corrected_gain=5.0,
                    retries=2.0,
                    proof_cpu=20.0,
                ),
                _child_probe_row(
                    branch_node_id=0,
                    branch_depth=0,
                    pair=[2, 6],
                    child_node_id=2,
                    complete=True,
                    right_censored=False,
                    fathomed=False,
                    corrected_gain=0.0,
                    retries=0.0,
                    proof_cpu=5.0,
                ),
                _child_probe_row(
                    branch_node_id=0,
                    branch_depth=0,
                    pair=[2, 10],
                    child_node_id=3,
                    complete=False,
                    right_censored=True,
                    fathomed=False,
                    corrected_gain=0.0,
                    retries=3.0,
                    proof_cpu=30.0,
                ),
            ]
            (probe_dir / "child_probe_rows.jsonl").write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

            summary = build_branch_score_map(
                [probe_dir],
                tmp_path / "out",
                tmp_path / "report.md",
                key_scope="node_depth",
                include_child_probe=True,
            )

            self.assertEqual(summary["raw_ranking_pair_row_count"], 0)
            self.assertEqual(summary["raw_child_probe_row_count"], 3)
            self.assertEqual(summary["child_probe_branch_row_count"], 2)
            self.assertEqual(summary["branch_score_map_entry_count"], 2)
            self.assertEqual(summary["solver_priority_mode"], "branch_score_horizon")

            score_map = json.loads((tmp_path / "out" / "journey_branch_score_map.json").read_text())
            self.assertGreater(score_map["node:0:depth:0:2,6"], 0.0)
            self.assertLess(score_map["node:0:depth:0:2,10"], 0.0)

            score_rows = json.loads((tmp_path / "out" / "journey_branch_score_rows.json").read_text())
            positive = next(row for row in score_rows if row["key"] == "node:0:depth:0:2,6")
            self.assertEqual(positive["score_source"], "child_probe_proof_cost")
            self.assertEqual(positive["child_probe_branch_count"], 1)
            self.assertEqual(positive["complete_child_probe_branch_count"], 1)
            self.assertEqual(positive["right_censored_child_probe_branch_count"], 0)
            self.assertAlmostEqual(positive["child_probe_fathom_sum"], 1.0)

            negative = next(row for row in score_rows if row["key"] == "node:0:depth:0:2,10")
            self.assertEqual(negative["right_censored_child_probe_branch_count"], 1)
            self.assertIn("branch_score_horizon", (tmp_path / "report.md").read_text(encoding="utf-8"))

    def test_child_probe_log_filters_support_context_safe_maps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            probe_dir = tmp_path / "probe"
            probe_dir.mkdir()
            rows = [
                _child_probe_row(
                    log_file="greedy-anchor_seed1.jsonl",
                    branch_node_id=0,
                    branch_depth=0,
                    pair=[2, 6],
                    child_node_id=1,
                    complete=True,
                    right_censored=False,
                    fathomed=True,
                    corrected_gain=5.0,
                    retries=0.0,
                    proof_cpu=10.0,
                ),
                _child_probe_row(
                    log_file="random-wave_seed1.jsonl",
                    branch_node_id=0,
                    branch_depth=0,
                    pair=[2, 10],
                    child_node_id=2,
                    complete=False,
                    right_censored=True,
                    fathomed=False,
                    corrected_gain=0.0,
                    retries=2.0,
                    proof_cpu=20.0,
                ),
            ]
            (probe_dir / "child_probe_rows.jsonl").write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

            summary = build_branch_score_map(
                [probe_dir],
                tmp_path / "out",
                tmp_path / "report.md",
                key_scope="node_depth",
                include_child_probe=True,
                include_child_probe_log_contains=("greedy-anchor",),
            )

            self.assertEqual(summary["raw_child_probe_row_count"], 2)
            self.assertEqual(summary["child_probe_row_count"], 1)
            self.assertEqual(summary["filtered_out_child_probe_row_count"], 1)
            self.assertEqual(summary["include_child_probe_log_contains"], ["greedy-anchor"])
            score_map = json.loads((tmp_path / "out" / "journey_branch_score_map.json").read_text())
            self.assertIn("node:0:depth:0:2,6", score_map)
            self.assertNotIn("node:0:depth:0:2,10", score_map)
            report_text = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("include_child_probe_log_contains", report_text)


def _ranking_row(
    *,
    instance: str = "BPC_future/logical_graph/tasks_020/demo/demo.json",
    node_id: int = 0,
    depth: int = 0,
    better_pair: list[int],
    worse_pair: list[int],
    wall_gap: float = 1.0,
    exact_gap: float = 0.0,
) -> dict[str, object]:
    return {
        "schema_version": "journey_branch_counterfactual_ranking_pair_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "instance": instance,
        "node_id": node_id,
        "depth": depth,
        "baseline_pair": "2,5",
        "preference_reason": "wall_time_delta",
        "better": {
            "alternative_pair": better_pair,
            "wall_time_delta": -float(wall_gap),
            "exact_pricing_calls_delta": -float(exact_gap),
        },
        "worse": {
            "alternative_pair": worse_pair,
            "wall_time_delta": 0.0,
            "exact_pricing_calls_delta": 0.0,
        },
        "wall_delta_gap": float(wall_gap),
        "exact_pricing_calls_gap": float(exact_gap),
    }


def _child_probe_row(
    *,
    log_file: str = "demo.jsonl",
    branch_node_id: int,
    branch_depth: int,
    pair: list[int],
    child_node_id: int,
    complete: bool,
    right_censored: bool,
    fathomed: bool,
    corrected_gain: float,
    retries: float,
    proof_cpu: float,
) -> dict[str, object]:
    return {
        "schema_version": "journey_branch_child_probe_row_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "log_file": log_file,
        "run_status": "OPTIMAL" if complete else "NO_FINISH",
        "right_censored": bool(right_censored),
        "label_observation_complete": bool(complete),
        "branch_node_id": branch_node_id,
        "branch_depth": branch_depth,
        "task_i": pair[0],
        "task_j": pair[1],
        "child_node_id": child_node_id,
        "child_started": True,
        "child_label_schema": [
            "child_lower_bound_gain",
            "child_max_corrected_node_lb",
            "child_max_corrected_bound_gain",
            "child_pricing_event_count",
            "child_exact_pricing_event_count",
            "child_negative_pricing_event_count",
            "child_completion_bound_retry_count",
            "child_early_branch_trigger_count",
            "child_proof_cpu",
            "child_time_to_first_certificate",
            "child_time_to_fathom",
            "child_fathomed",
        ],
        "child_labels": {
            "child_lower_bound_gain": 0.0,
            "child_max_corrected_node_lb": 0.0,
            "child_max_corrected_bound_gain": float(corrected_gain),
            "child_pricing_event_count": 1.0,
            "child_exact_pricing_event_count": 1.0,
            "child_negative_pricing_event_count": 0.0,
            "child_completion_bound_retry_count": float(retries),
            "child_early_branch_trigger_count": 0.0,
            "child_proof_cpu": float(proof_cpu),
            "child_time_to_first_certificate": float(proof_cpu) if fathomed else -1.0,
            "child_time_to_fathom": float(proof_cpu) if fathomed else -1.0,
            "child_fathomed": 1.0 if fathomed else 0.0,
        },
    }


if __name__ == "__main__":
    unittest.main()

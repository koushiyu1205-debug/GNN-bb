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


if __name__ == "__main__":
    unittest.main()

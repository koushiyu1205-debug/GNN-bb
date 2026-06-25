from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_journey_branch_score_ab_runbook import build_runbook


class JourneyBranchScoreABRunbookTests(unittest.TestCase):
    def test_builds_paired_baseline_and_score_horizon_commands_for_near_threshold_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            first = (
                "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/"
                "apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json"
            )
            second = (
                "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/"
                "apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json"
            )
            score_path = tmp_path / "score_rows.json"
            score_path.write_text(
                json.dumps(
                    [
                        {
                            "instance": first,
                            "node_id": 0,
                            "depth": 0,
                            "pair": [6, 16],
                            "score": 1.9,
                        },
                        {
                            "instance": second,
                            "node_id": 0,
                            "depth": 0,
                            "pair": [12, 15],
                            "score": 3.4,
                        },
                    ],
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            results = tmp_path / "results.csv"
            self._write_results(
                results,
                [
                    {"instance": first, "status": "OPTIMAL", "wall_time": "220.0"},
                    {"instance": second, "status": "OPTIMAL", "wall_time": "180.0"},
                ],
            )

            summary = build_runbook(
                score_path=score_path,
                results_csv=[results],
                output_dir=tmp_path / "out",
                report=tmp_path / "report.md",
                target_wall=200.0,
                time_limit=600,
            )

            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertEqual(summary["raw_score_row_count"], 2)
            self.assertEqual(summary["score_instance_count"], 2)
            self.assertEqual(summary["entry_count"], 1)
            self.assertEqual(summary["command_count"], 2)
            self.assertEqual(summary["skipped_wall_count"], 1)
            self.assertEqual(summary["score_horizon_min_score"], 1.5)
            entry = summary["entries"][0]
            self.assertEqual(entry["instance"], first)
            self.assertEqual(entry["top_pair"], [6, 16])
            commands = (tmp_path / "out" / "commands.sh").read_text(encoding="utf-8")
            self.assertIn("journey_branch_candidate_log_top_n=200", commands)
            self.assertIn("journey_branch_candidate_priority=branch_score_horizon", commands)
            self.assertIn(f"journey_branch_candidate_score_path={score_path}", commands)
            self.assertIn("journey_tail_action_no_column_early_branch_enabled=False", commands)

    def test_can_build_without_result_csv_for_score_row_instances(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instance = "BPC_future/logical_graph/tasks_020/case/case_seed1.json"
            score_dir = tmp_path / "score_dir"
            score_dir.mkdir()
            (score_dir / "journey_branch_score_rows.jsonl").write_text(
                json.dumps(
                    {
                        "instance": instance,
                        "task_i": 2,
                        "task_j": 6,
                        "branch_score": 2.0,
                    },
                    sort_keys=True,
                )
                + "\n"
                + json.dumps(
                    {
                        "instance": "BPC_future/logical_graph/tasks_020/case/case_seed2.json",
                        "task_i": 3,
                        "task_j": 7,
                        "branch_score": -1.0,
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = build_runbook(
                score_path=score_dir,
                output_dir=tmp_path / "out",
                report=tmp_path / "report.md",
                score_horizon_min_score=0.0,
            )

            self.assertEqual(summary["entry_count"], 1)
            self.assertEqual(summary["entries"][0]["instance"], instance)
            self.assertEqual(summary["entries"][0]["top_pair"], [2, 6])
            self.assertTrue((tmp_path / "out" / "runbook.json").exists())
            self.assertIn("official_bound_effect = false", (tmp_path / "report.md").read_text())

    @staticmethod
    def _write_results(path: Path, rows: list[dict[str, str]]) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["instance", "status", "wall_time"])
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()

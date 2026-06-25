from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_journey_branch_cascade_plan import build_cascade_plan


class JourneyBranchCascadePlanTests(unittest.TestCase):
    def test_prefers_child_probe_for_near_threshold_context_with_candidate_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instance = (
                "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/"
                "apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json"
            )
            results = tmp_path / "results.csv"
            self._write_results(
                results,
                [
                    {
                        "instance": instance,
                        "status": "OPTIMAL",
                        "wall_time": "220.5",
                        "node_count": "7",
                        "pricing_calls": "75",
                        "exact_pricing_calls": "39",
                    }
                ],
            )
            log_path = (
                tmp_path
                / "logs"
                / "BPC_future"
                / "logical_graph"
                / "tasks_020"
                / "sector-wave"
                / "apollo15_20km"
                / "apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json.jsonl"
            )
            log_path.parent.mkdir(parents=True)
            log_path.write_text(
                json.dumps(
                    {
                        "event": "journey_branch_candidates",
                        "node_id": 0,
                        "depth": 0,
                        "candidate_count": 11,
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = build_cascade_plan(
                [results],
                tmp_path / "out",
                tmp_path / "report.md",
                log_paths=[log_path],
                target_wall=200.0,
                near_threshold_max_wall=260.0,
            )

            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertEqual(summary["context_count"], 1)
            row = summary["rows"][0]
            self.assertEqual(row["recommended_action"], "BUILD_CHILD_PROBE_RUNBOOK")
            self.assertIn("--probe-mode child_probe", row["recommended_command"])
            self.assertIn("--candidate-log-top-n 200", row["recommended_command"])

    def test_collects_top200_log_when_near_threshold_context_has_no_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instance = (
                "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/"
                "apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json"
            )
            results = tmp_path / "results.csv"
            self._write_results(
                results,
                [
                    {
                        "instance": instance,
                        "status": "OPTIMAL",
                        "wall_time": "240.0",
                        "node_count": "5",
                        "pricing_calls": "70",
                        "exact_pricing_calls": "30",
                    }
                ],
            )

            summary = build_cascade_plan(
                [results],
                tmp_path / "out",
                tmp_path / "report.md",
                target_wall=200.0,
                near_threshold_max_wall=260.0,
            )

            self.assertEqual(summary["context_count"], 1)
            row = summary["rows"][0]
            self.assertEqual(row["recommended_action"], "COLLECT_TOP200_DIAG_LOG")
            self.assertIn(
                "journey_branch_candidate_log_top_n=200",
                row["recommended_command"],
            )

    @staticmethod
    def _write_results(path: Path, rows: list[dict[str, str]]) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "instance",
                    "status",
                    "wall_time",
                    "node_count",
                    "pricing_calls",
                    "exact_pricing_calls",
                ],
            )
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()

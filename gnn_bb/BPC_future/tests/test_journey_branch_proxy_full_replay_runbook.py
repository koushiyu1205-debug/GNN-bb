from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_journey_branch_proxy_full_replay_runbook import build_runbook


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


class JourneyBranchProxyFullReplayRunbookTests(unittest.TestCase):
    def test_builds_root_forced_pair_commands_from_proxy_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            proxy_dir = tmp_path / "proxy"
            _write_jsonl(
                proxy_dir / "child_probe_proxy_branch_rows.jsonl",
                [
                    {
                        "instance": "BPC_future/logical_graph/tasks_020/random-wave/case_a.json",
                        "node_id": 3,
                        "depth": 0,
                        "pair": [5, 13],
                        "source_selected_pair": [1, 2],
                        "proxy_score": 2.5,
                        "right_censored": True,
                    },
                    {
                        "instance": "BPC_future/logical_graph/tasks_020/random-wave/case_b.json",
                        "depth": 0,
                        "task_i": 2,
                        "task_j": 7,
                        "proxy_score": 1.0,
                    },
                    {
                        "instance": "BPC_future/logical_graph/tasks_020/random-wave/case_c.json",
                        "depth": 1,
                        "pair": [1, 3],
                        "proxy_score": 9.0,
                    },
                ],
            )

            runbook = build_runbook(
                [proxy_dir],
                tmp_path / "out",
                tmp_path / "report.md",
                time_limit=260,
                limit=4,
                max_per_instance=1,
            )

            self.assertTrue(runbook["diagnostic_only"])
            self.assertFalse(runbook["runs_bpc_or_pricing"])
            self.assertFalse(runbook["official_bound_effect"])
            self.assertEqual(runbook["raw_proxy_row_count"], 3)
            self.assertEqual(runbook["skipped_non_root_depth"], 1)
            self.assertEqual(runbook["min_proxy_score"], 0.0)
            self.assertEqual(runbook["entry_count"], 2)
            self.assertEqual(runbook["entries"][0]["forced_pair"], [5, 13])
            self.assertEqual(runbook["entries"][0]["source_node_id"], 3)
            self.assertEqual(runbook["entries"][0]["source_depth"], 0)
            self.assertEqual(runbook["entries"][0]["source_selected_pair"], [1, 2])

            commands = (tmp_path / "out" / "commands.sh").read_text(encoding="utf-8")
            self.assertIn("journey_branch_candidate_priority=force_pair_path:0:5,13", commands)
            self.assertIn("--time-limit 260", commands)
            self.assertNotIn("journey_max_nodes", commands)
            self.assertIn("official_bound_effect = false", (tmp_path / "report.md").read_text(encoding="utf-8"))

    def test_respects_max_per_instance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            proxy = tmp_path / "rows.jsonl"
            _write_jsonl(
                proxy,
                [
                    {"instance": "case.json", "depth": 0, "pair": [1, 2], "proxy_score": 3.0},
                    {"instance": "case.json", "depth": 0, "pair": [1, 3], "proxy_score": 2.0},
                    {"instance": "other.json", "depth": 0, "pair": [4, 5], "proxy_score": 1.0},
                ],
            )

            runbook = build_runbook(
                [proxy],
                tmp_path / "out",
                tmp_path / "report.md",
                limit=5,
                max_per_instance=1,
            )

            self.assertEqual(runbook["entry_count"], 2)
            self.assertEqual(runbook["skipped_max_per_instance"], 1)
            self.assertEqual(
                [entry["forced_pair"] for entry in runbook["entries"]],
                [[1, 2], [4, 5]],
            )

    def test_default_promotion_gate_skips_negative_right_censored_proxy_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            proxy = tmp_path / "rows.jsonl"
            _write_jsonl(
                proxy,
                [
                    {
                        "instance": "seed61513.json",
                        "depth": 0,
                        "pair": [2, 3],
                        "proxy_score": -3.26736615,
                        "right_censored": True,
                        "fathom_count": 1.0,
                        "max_corrected_bound_gain": 22.621766,
                        "completion_bound_retry_count": 6.0,
                    },
                    {
                        "instance": "seed61410.json",
                        "depth": 0,
                        "pair": [4, 10],
                        "proxy_score": -4.283322117,
                        "right_censored": True,
                        "fathom_count": 0.0,
                        "max_corrected_bound_gain": 22.8516,
                        "completion_bound_retry_count": 6.0,
                    },
                ],
            )

            runbook = build_runbook(
                [proxy],
                tmp_path / "out",
                tmp_path / "report.md",
                limit=5,
                max_per_instance=1,
            )

            self.assertEqual(runbook["candidate_row_count"], 0)
            self.assertEqual(runbook["entry_count"], 0)
            self.assertEqual(runbook["skipped_score_threshold"], 2)
            commands = (tmp_path / "out" / "commands.sh").read_text(encoding="utf-8")
            self.assertNotIn("run_bpc_future_external_timeout_batch.py", commands)

    def test_can_explicitly_relax_proxy_score_gate_for_diagnostic_replay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            proxy = tmp_path / "rows.jsonl"
            _write_jsonl(
                proxy,
                [
                    {
                        "instance": "seed61513.json",
                        "depth": 0,
                        "pair": [2, 3],
                        "proxy_score": -3.26736615,
                        "right_censored": True,
                    }
                ],
            )

            runbook = build_runbook(
                [proxy],
                tmp_path / "out",
                tmp_path / "report.md",
                min_proxy_score=None,
            )

            self.assertEqual(runbook["entry_count"], 1)
            self.assertEqual(runbook["entries"][0]["forced_pair"], [2, 3])

    def test_optional_promotion_filters_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            proxy = tmp_path / "rows.jsonl"
            _write_jsonl(
                proxy,
                [
                    {
                        "instance": "low_fathom.json",
                        "depth": 0,
                        "pair": [1, 2],
                        "proxy_score": 3.0,
                        "fathom_count": 0.0,
                    },
                    {
                        "instance": "low_gain.json",
                        "depth": 0,
                        "pair": [1, 3],
                        "proxy_score": 3.0,
                        "fathom_count": 1.0,
                        "max_corrected_bound_gain": 1.0,
                    },
                    {
                        "instance": "retry_heavy.json",
                        "depth": 0,
                        "pair": [1, 4],
                        "proxy_score": 3.0,
                        "fathom_count": 1.0,
                        "max_corrected_bound_gain": 10.0,
                        "completion_bound_retry_count": 7.0,
                    },
                    {
                        "instance": "clean.json",
                        "depth": 0,
                        "pair": [1, 5],
                        "proxy_score": 3.0,
                        "fathom_count": 1.0,
                        "max_corrected_bound_gain": 10.0,
                        "completion_bound_retry_count": 2.0,
                    },
                ],
            )

            runbook = build_runbook(
                [proxy],
                tmp_path / "out",
                tmp_path / "report.md",
                min_fathom_count=1.0,
                min_corrected_bound_gain=5.0,
                max_completion_bound_retry_count=3.0,
            )

            self.assertEqual(runbook["entry_count"], 1)
            self.assertEqual(runbook["entries"][0]["forced_pair"], [1, 5])
            self.assertEqual(runbook["skipped_fathom_threshold"], 1)
            self.assertEqual(runbook["skipped_corrected_gain_threshold"], 1)
            self.assertEqual(runbook["skipped_completion_retry_threshold"], 1)
            report = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("min_fathom_count = 1.0", report)
            self.assertIn("max_completion_bound_retry_count = 3.0", report)

    def test_respects_explicit_promotion_ready_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            proxy = tmp_path / "rows.jsonl"
            _write_jsonl(
                proxy,
                [
                    {
                        "instance": "case.json",
                        "depth": 0,
                        "pair": [1, 2],
                        "proxy_score": 3.0,
                        "promotion_ready": False,
                    }
                ],
            )

            runbook = build_runbook(
                [proxy],
                tmp_path / "out",
                tmp_path / "report.md",
            )

            self.assertEqual(runbook["entry_count"], 0)
            self.assertEqual(runbook["skipped_promotion_unready"], 1)

    def test_can_allow_promotion_unready_for_manual_diagnostic_replay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            proxy = tmp_path / "rows.jsonl"
            _write_jsonl(
                proxy,
                [
                    {
                        "instance": "case.json",
                        "depth": 0,
                        "pair": [1, 2],
                        "proxy_score": 3.0,
                        "promotion_ready": False,
                    }
                ],
            )

            runbook = build_runbook(
                [proxy],
                tmp_path / "out",
                tmp_path / "report.md",
                require_promotion_ready=False,
            )

            self.assertEqual(runbook["entry_count"], 1)
            self.assertEqual(runbook["entries"][0]["forced_pair"], [1, 2])


if __name__ == "__main__":
    unittest.main()

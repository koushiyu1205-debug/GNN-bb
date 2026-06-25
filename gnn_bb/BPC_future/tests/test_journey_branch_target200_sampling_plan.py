from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_journey_branch_target200_sampling_plan import (
    build_target200_sampling_plan,
)


class JourneyBranchTarget200SamplingPlanTests(unittest.TestCase):
    def test_prioritizes_family_gap_and_uses_child_probe_when_log_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            results = tmp_path / "results.csv"
            random_instance = (
                "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/"
                "apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json"
            )
            random_no_log = (
                "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/"
                "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json"
            )
            known_instance = (
                "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/"
                "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json"
            )
            sector_instance = (
                "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/"
                "apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json"
            )
            _write_results(
                results,
                [
                    _result(random_instance, status="OPTIMAL", wall=215.0, nodes=4),
                    _result(random_no_log, status="TIME_LIMIT", wall=240.0, nodes=1),
                    _result(known_instance, status="OPTIMAL", wall=260.0, nodes=5),
                    _result(sector_instance, status="OPTIMAL", wall=230.0, nodes=3),
                    _result(
                        "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/"
                        "apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
                        status="OPTIMAL",
                        wall=180.0,
                        nodes=1,
                    ),
                ],
            )
            labels = tmp_path / "labels"
            labels.mkdir()
            (labels / "branch_training_readiness_rows.jsonl").write_text(
                json.dumps(
                    {
                        "instance": known_instance,
                        "target_200_positive": True,
                        "time_window_family": "greedy-anchor",
                    },
                    sort_keys=True,
                )
                + "\n"
                + json.dumps(
                    {
                        "instance": sector_instance,
                        "target_200_positive": True,
                        "time_window_family": "sector-wave",
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            log_dir = tmp_path / "logs"
            log_dir.mkdir()
            log_path = log_dir / "random.jsonl"
            log_path.write_text(
                json.dumps(
                    {
                        "event": "journey_branch_candidates",
                        "instance": random_instance,
                        "depth": 0,
                        "candidate_count": 20,
                        "logged_top_count": 20,
                        "priority_top": [{"task_i": 1, "task_j": 2}],
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = build_target200_sampling_plan(
                results_csv=[results],
                output_dir=tmp_path / "out",
                report=tmp_path / "report.md",
                known_label_inputs=[labels],
                log_paths=[log_dir],
                selected_limit=3,
                target_wall=200.0,
                near_wall=360.0,
                python="python3",
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertEqual(summary["known_target200_family_count"], 2)
            self.assertEqual(summary["selected_family_counts"], {"random-wave": 2})
            self.assertEqual(summary["selected_action_counts"]["BUILD_CHILD_PROBE_RUNBOOK"], 1)
            self.assertEqual(summary["selected_action_counts"]["COLLECT_TOP200_DIAG_LOG"], 1)
            selected = summary["rows"]
            self.assertEqual(selected[0]["instance"], random_instance)
            self.assertEqual(selected[0]["recommended_action"], "BUILD_CHILD_PROBE_RUNBOOK")
            self.assertIn("build_journey_branch_candidate_replay_runbook.py", selected[0]["recommended_command"])
            self.assertIn("--probe-mode child_probe", selected[0]["recommended_command"])
            self.assertEqual(selected[1]["instance"], random_no_log)
            self.assertEqual(selected[1]["recommended_action"], "COLLECT_TOP200_DIAG_LOG")
            self.assertIn("journey_branch_candidate_log_top_n=200", selected[1]["recommended_command"])
            all_rows = _read_jsonl(tmp_path / "out" / "target200_sampling_all_rows.jsonl")
            known_row = next(row for row in all_rows if row["instance"] == known_instance)
            self.assertEqual(known_row["recommended_action"], "SKIP_KNOWN_TARGET200_INSTANCE")
            self.assertTrue((tmp_path / "out" / "commands.sh").exists())
            self.assertIn("official_bound_effect = False", (tmp_path / "report.md").read_text())

    def test_routes_top200_no_branch_context_out_of_branch_sampling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instance = (
                "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/"
                "apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json"
            )
            results = tmp_path / "results.csv"
            _write_results(results, [_result(instance, status="OPTIMAL", wall=210.0, nodes=1)])
            log_dir = tmp_path / "logs"
            log_dir.mkdir()
            (log_dir / "root_tail.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps({"event": "journey_node_start", "instance": instance}, sort_keys=True),
                        json.dumps({"event": "journey_pricing", "instance": instance}, sort_keys=True),
                        json.dumps({"event": "finish", "instance": instance}, sort_keys=True),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            summary = build_target200_sampling_plan(
                results_csv=[results],
                output_dir=tmp_path / "out",
                report=tmp_path / "report.md",
                log_paths=[log_dir],
                selected_limit=4,
                target_wall=200.0,
                near_wall=360.0,
                python="python3",
            )

            all_rows = _read_jsonl(tmp_path / "out" / "target200_sampling_all_rows.jsonl")
            self.assertEqual(summary["actionable_context_count"], 0)
            self.assertEqual(summary["selected_context_count"], 0)
            self.assertEqual(all_rows[0]["recommended_action"], "ROUTE_TO_ROOT_PRICING_TAIL")
            self.assertEqual(all_rows[0]["branch_event_count"], 0)
            self.assertEqual(all_rows[0]["branch_candidate_event_count"], 0)
            self.assertEqual(all_rows[0]["recommended_command"], "")

    def test_collects_diag_when_branch_events_exist_without_candidate_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instance = (
                "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/"
                "apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json"
            )
            results = tmp_path / "results.csv"
            _write_results(results, [_result(instance, status="EXTERNAL_TIME_LIMIT", wall=600.0, nodes=0)])
            log_dir = tmp_path / "logs"
            log_dir.mkdir()
            (log_dir / "branch_without_candidates.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps({"event": "journey_node_start", "instance": instance}, sort_keys=True),
                        json.dumps(
                            {
                                "event": "journey_branch",
                                "instance": instance,
                                "node_id": 0,
                                "depth": 0,
                            },
                            sort_keys=True,
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            summary = build_target200_sampling_plan(
                results_csv=[results],
                output_dir=tmp_path / "out",
                report=tmp_path / "report.md",
                log_paths=[log_dir],
                selected_limit=4,
                target_wall=200.0,
                near_wall=360.0,
                python="python3",
            )

            all_rows = _read_jsonl(tmp_path / "out" / "target200_sampling_all_rows.jsonl")
            self.assertEqual(summary["actionable_context_count"], 1)
            self.assertEqual(summary["selected_context_count"], 1)
            self.assertEqual(all_rows[0]["recommended_action"], "COLLECT_BRANCH_CANDIDATE_DIAG_LOG")
            self.assertEqual(all_rows[0]["recommended_reason"], "branch_events_without_candidate_log")
            self.assertEqual(all_rows[0]["branch_event_count"], 1)
            self.assertEqual(all_rows[0]["branch_candidate_event_count"], 0)
            self.assertIn("journey_branch_candidate_log_top_n=200", all_rows[0]["recommended_command"])
            self.assertIn("run_bpc_future_external_timeout_batch.py", all_rows[0]["recommended_command"])
            self.assertIn("--time-limit 260", all_rows[0]["recommended_command"])

    def test_skips_attempted_context_without_target200_positive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            attempted_instance = (
                "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/"
                "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json"
            )
            fresh_instance = (
                "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/"
                "apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json"
            )
            results = tmp_path / "results.csv"
            _write_results(
                results,
                [
                    _result(attempted_instance, status="OPTIMAL", wall=288.0, nodes=7),
                    _result(fresh_instance, status="TIME_LIMIT", wall=240.0, nodes=2),
                ],
            )
            attempted = tmp_path / "attempted"
            attempted.mkdir()
            (attempted / "branch_impact_rows.jsonl").write_text(
                json.dumps(
                    {
                        "log_file": (
                            "tmp/logs/"
                            f"{attempted_instance}.jsonl"
                        ),
                        "right_censored": True,
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            log_dir = tmp_path / "logs"
            log_dir.mkdir()
            (log_dir / "attempted.jsonl").write_text(
                json.dumps(
                    {
                        "event": "journey_branch_candidates",
                        "instance": attempted_instance,
                        "depth": 0,
                        "candidate_count": 20,
                        "logged_top_count": 20,
                        "priority_top": [{"task_i": 5, "task_j": 13}],
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = build_target200_sampling_plan(
                results_csv=[results],
                output_dir=tmp_path / "out",
                report=tmp_path / "report.md",
                attempted_inputs=[attempted],
                log_paths=[log_dir],
                selected_limit=4,
                target_wall=200.0,
                near_wall=360.0,
                python="python3",
            )

            all_rows = _read_jsonl(tmp_path / "out" / "target200_sampling_all_rows.jsonl")
            attempted_row = next(row for row in all_rows if row["instance"] == attempted_instance)
            self.assertEqual(attempted_row["recommended_action"], "SKIP_ALREADY_ATTEMPTED_CONTEXT")
            self.assertEqual(attempted_row["recommended_command"], "")
            self.assertTrue(attempted_row["attempted_context"])
            self.assertEqual(summary["attempted_context_count"], 1)
            self.assertEqual(summary["selected_context_count"], 1)
            self.assertEqual(summary["rows"][0]["instance"], fresh_instance)
            self.assertEqual(summary["rows"][0]["recommended_action"], "COLLECT_TOP200_DIAG_LOG")

    def test_retry_budget_keeps_attempted_instance_and_passes_exclude_runbook(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instance = (
                "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/"
                "apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json"
            )
            results = tmp_path / "results.csv"
            _write_results(results, [_result(instance, status="OPTIMAL", wall=240.0, nodes=4)])
            attempted = tmp_path / "attempted_runbook"
            attempted.mkdir()
            (attempted / "runbook.json").write_text(
                json.dumps(
                    {
                        "entries": [
                            {
                                "instance": instance,
                                "source_node_id": 0,
                                "source_depth": 0,
                                "forced_pair": [1, 2],
                            }
                        ]
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            log_dir = tmp_path / "logs"
            log_dir.mkdir()
            (log_dir / "candidate.jsonl").write_text(
                json.dumps(
                    {
                        "event": "journey_branch_candidates",
                        "instance": instance,
                        "node_id": 0,
                        "depth": 0,
                        "candidate_count": 20,
                        "logged_top_count": 20,
                        "selected": {"task_i": 1, "task_j": 2, "fractionality": 0.5},
                        "priority_top": [
                            {"task_i": 1, "task_j": 2, "fractionality": 0.5},
                            {"task_i": 3, "task_j": 4, "fractionality": 0.49},
                        ],
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = build_target200_sampling_plan(
                results_csv=[results],
                output_dir=tmp_path / "out",
                report=tmp_path / "report.md",
                attempted_inputs=[attempted],
                log_paths=[log_dir],
                selected_limit=2,
                target_wall=200.0,
                near_wall=360.0,
                python="python3",
                max_attempted_probe_entries_per_instance=4,
            )

            self.assertEqual(summary["selected_context_count"], 1)
            row = summary["rows"][0]
            self.assertEqual(row["instance"], instance)
            self.assertEqual(row["recommended_action"], "BUILD_CHILD_PROBE_RUNBOOK")
            self.assertFalse(row["attempted_context"])
            self.assertEqual(row["attempted_probe_entry_count"], 1)
            self.assertEqual(row["max_attempted_probe_entries_per_instance"], 4)
            self.assertIn("--exclude-runbook", row["recommended_command"])
            self.assertIn(str(attempted), row["recommended_command"])

    def test_retry_budget_counts_nested_attempted_runbooks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instance = (
                "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/"
                "apollo15_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json"
            )
            results = tmp_path / "results.csv"
            _write_results(results, [_result(instance, status="OPTIMAL", wall=240.0, nodes=4)])
            attempted_root = tmp_path / "attempted_root"
            nested = attempted_root / "child_probe_runbooks" / "case"
            nested.mkdir(parents=True)
            (nested / "runbook.json").write_text(
                json.dumps(
                    {
                        "entries": [
                            {
                                "instance": instance,
                                "source_node_id": 0,
                                "source_depth": 0,
                                "forced_pair": [1, 2],
                            }
                        ]
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            log_dir = tmp_path / "logs"
            log_dir.mkdir()
            (log_dir / "candidate.jsonl").write_text(
                json.dumps(
                    {
                        "event": "journey_branch_candidates",
                        "instance": instance,
                        "node_id": 0,
                        "depth": 0,
                        "candidate_count": 20,
                        "logged_top_count": 20,
                        "selected": {"task_i": 1, "task_j": 2, "fractionality": 0.5},
                        "priority_top": [
                            {"task_i": 1, "task_j": 2, "fractionality": 0.5},
                            {"task_i": 3, "task_j": 4, "fractionality": 0.49},
                        ],
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = build_target200_sampling_plan(
                results_csv=[results],
                output_dir=tmp_path / "out",
                report=tmp_path / "report.md",
                attempted_inputs=[attempted_root],
                log_paths=[log_dir],
                selected_limit=2,
                target_wall=200.0,
                near_wall=360.0,
                python="python3",
                max_attempted_probe_entries_per_instance=4,
            )

            row = summary["rows"][0]
            self.assertEqual(row["recommended_action"], "BUILD_CHILD_PROBE_RUNBOOK")
            self.assertEqual(row["attempted_probe_entry_count"], 1)
            self.assertIn(str(attempted_root), row["recommended_command"])


def _result(instance: str, *, status: str, wall: float, nodes: int) -> dict[str, object]:
    return {
        "instance": instance,
        "status": status,
        "wall_time": wall,
        "node_count": nodes,
        "pricing_calls": 10,
        "exact_pricing_calls": 3,
    }


def _write_results(path: Path, rows: list[dict[str, object]]) -> None:
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


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


if __name__ == "__main__":
    unittest.main()

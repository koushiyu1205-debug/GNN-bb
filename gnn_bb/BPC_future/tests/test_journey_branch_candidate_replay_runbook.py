from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_journey_branch_candidate_replay_runbook import build_runbook


class JourneyBranchCandidateReplayRunbookTests(unittest.TestCase):
    def test_builds_forced_pair_path_commands_from_candidate_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_dir = tmp_path / "logs" / "BPC_future" / "logical_graph" / "tasks_020" / "case"
            log_dir.mkdir(parents=True)
            log_path = log_dir / "case_randomtw_tasks020_01_seed1_logical_graph.json.jsonl"
            records = [
                {"event": "journey_node_start", "node_id": 0, "depth": 0},
                {
                    "event": "journey_child_queued",
                    "parent_node_id": 0,
                    "child_node_id": 3,
                    "depth": 1,
                    "constraint": "RF(1,2)=same_vehicle",
                },
                {"event": "journey_node_start", "node_id": 3, "depth": 1},
                {
                    "event": "journey_branch_candidates",
                    "node_id": 3,
                    "depth": 1,
                    "priority_mode": "fractionality",
                    "candidate_count": 3,
                    "eligible_count": 3,
                    "selected": {"task_i": 2, "task_j": 5, "fractionality": 0.5},
                    "priority_top": [
                        {"task_i": 2, "task_j": 5, "fractionality": 0.5, "pool_max_child_width": 7},
                        {"task_i": 5, "task_j": 8, "fractionality": 0.5, "pool_max_child_width": 9},
                        {"task_i": 3, "task_j": 18, "fractionality": 0.45, "pool_max_child_width": 4},
                    ],
                },
            ]
            log_path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )

            runbook = build_runbook(
                [log_path],
                tmp_path / "out",
                tmp_path / "report.md",
                time_limit=200,
                limit=4,
                alt_pairs_per_event=2,
                candidate_log_top_n=200,
            )

            self.assertTrue(runbook["diagnostic_only"])
            self.assertFalse(runbook["runs_bpc_or_pricing"])
            self.assertFalse(runbook["official_bound_effect"])
            self.assertEqual(runbook["candidate_event_count_seen"], 1)
            self.assertEqual(runbook["candidate_event_count_with_replay_entries"], 1)
            self.assertFalse(runbook["entry_limit_reached"])
            self.assertEqual(runbook["entry_count"], 2)

            first = runbook["entries"][0]
            self.assertEqual(first["instance"], "BPC_future/logical_graph/tasks_020/case/case_randomtw_tasks020_01_seed1_logical_graph.json")
            self.assertEqual(first["source_node_id"], 3)
            self.assertEqual(first["source_depth"], 1)
            self.assertEqual(first["source_selected_pair"], [2, 5])
            self.assertEqual(first["forced_pair"], [3, 18])
            self.assertEqual(first["source_selected_fractionality"], 0.5)
            self.assertEqual(first["source_alt_fractionality"], 0.45)
            self.assertAlmostEqual(first["source_alt_required_tie_tolerance"], 0.05)
            self.assertEqual(first["source_alt_selection_reason"], "legacy_width_order")
            self.assertEqual(first["forced_pair_path_rule"], "force_pair_path:0:1,2=same_vehicle;1:3,18")
            self.assertIn(
                "journey_branch_candidate_log_top_n=200",
                (tmp_path / "out" / "commands.sh").read_text(encoding="utf-8"),
            )
            report = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("official_bound_effect = false", report)
            self.assertIn("source_alt_required_tie_tolerance = 0.05", report)

    def test_layered_candidate_selection_samples_distinct_strata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_dir = tmp_path / "logs" / "BPC_future" / "logical_graph" / "tasks_020" / "case"
            log_dir.mkdir(parents=True)
            log_path = log_dir / "case_randomtw_tasks020_11_seed11_logical_graph.json.jsonl"
            records = [
                {
                    "event": "journey_branch_candidates",
                    "node_id": 0,
                    "depth": 0,
                    "priority_mode": "fractionality",
                    "candidate_count": 7,
                    "eligible_count": 7,
                    "selected": {"task_i": 1, "task_j": 2, "fractionality": 0.5},
                    "priority_top": [
                        {"task_i": 1, "task_j": 2, "fractionality": 0.5, "pool_max_child_width": 10},
                        {
                            "task_i": 1,
                            "task_j": 3,
                            "fractionality": 0.49,
                            "pool_max_child_width": 100,
                            "pool_total_child_width": 190,
                            "pool_balance_gap": 80,
                        },
                        {
                            "task_i": 1,
                            "task_j": 4,
                            "fractionality": 0.48,
                            "pool_max_child_width": 90,
                            "pool_total_child_width": 170,
                            "pool_balance_gap": 70,
                        },
                        {
                            "task_i": 1,
                            "task_j": 5,
                            "fractionality": 0.20,
                            "pool_max_child_width": 2,
                            "pool_total_child_width": 150,
                            "pool_balance_gap": 50,
                        },
                        {
                            "task_i": 1,
                            "task_j": 6,
                            "fractionality": 0.20,
                            "pool_max_child_width": 50,
                            "pool_total_child_width": 100,
                            "pool_balance_gap": 0,
                        },
                        {
                            "task_i": 1,
                            "task_j": 7,
                            "fractionality": 0.20,
                            "pool_max_child_width": 60,
                            "pool_total_child_width": 120,
                            "pool_balance_gap": 30,
                            "branch_score": 3.0,
                            "branch_score_source": "unit",
                        },
                        {
                            "task_i": 1,
                            "task_j": 8,
                            "fractionality": 0.10,
                            "pool_max_child_width": 70,
                            "pool_total_child_width": 130,
                            "pool_balance_gap": 40,
                        },
                    ],
                },
            ]
            log_path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )

            runbook = build_runbook(
                [log_path],
                tmp_path / "out",
                tmp_path / "report.md",
                limit=10,
                alt_pairs_per_event=6,
                candidate_selection="layered",
            )

            self.assertEqual(runbook["candidate_selection"], "layered")
            self.assertEqual(runbook["entry_count"], 6)
            self.assertEqual(
                [entry["forced_pair"] for entry in runbook["entries"]],
                [[1, 3], [1, 4], [1, 5], [1, 6], [1, 7], [1, 8]],
            )
            self.assertEqual(
                [entry["source_alt_selection_reason"] for entry in runbook["entries"]],
                [
                    "highest_fractionality",
                    "near_tie",
                    "min_max_child_width",
                    "balanced_child_width",
                    "best_branch_score",
                    "rank_diversity",
                ],
            )
            report = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("candidate_selection = layered", report)
            self.assertIn("source_alt_selection_reason = best_branch_score", report)

    def test_positive_neighbor_selection_samples_v323_like_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_dir = tmp_path / "logs" / "BPC_future" / "logical_graph" / "tasks_020" / "case"
            log_dir.mkdir(parents=True)
            log_path = log_dir / "case_randomtw_tasks020_14_seed14_logical_graph.json.jsonl"
            records = [
                {
                    "event": "journey_branch_candidates",
                    "node_id": 0,
                    "depth": 0,
                    "priority_mode": "fractionality",
                    "candidate_count": 5,
                    "eligible_count": 5,
                    "selected": {"task_i": 13, "task_j": 16, "fractionality": 0.5},
                    "priority_top": [
                        {"task_i": 13, "task_j": 16, "fractionality": 0.5, "pool_max_child_width": 10},
                        {
                            "task_i": 2,
                            "task_j": 6,
                            "fractionality": 0.49,
                            "same_mass": 0.51,
                            "support_count": 3,
                            "incumbent_relation": False,
                            "pool_max_child_width": 30,
                            "pool_total_child_width": 52,
                            "pool_balance_gap": 8,
                        },
                        {
                            "task_i": 4,
                            "task_j": 9,
                            "fractionality": 0.48,
                            "same_mass": 0.52,
                            "support_count": 2,
                            "incumbent_relation": False,
                            "pool_max_child_width": 45,
                            "pool_total_child_width": 80,
                            "pool_balance_gap": 11,
                        },
                        {
                            "task_i": 6,
                            "task_j": 20,
                            "fractionality": 0.25,
                            "same_mass": 0.75,
                            "support_count": 1,
                            "incumbent_relation": True,
                            "pool_max_child_width": 425,
                            "pool_total_child_width": 801,
                            "pool_balance_gap": 49,
                        },
                    ],
                },
            ]
            log_path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )

            runbook = build_runbook(
                [log_path],
                tmp_path / "out",
                tmp_path / "report.md",
                limit=10,
                alt_pairs_per_event=1,
                candidate_selection="positive_neighbor",
            )

            self.assertEqual(runbook["candidate_selection"], "positive_neighbor")
            self.assertEqual(runbook["entry_count"], 1)
            entry = runbook["entries"][0]
            self.assertEqual(entry["forced_pair"], [6, 20])
            self.assertEqual(entry["source_alt_selection_reason"], "positive_neighbor")
            self.assertLess(float(entry["source_alt_positive_neighbor_score"]), 0.01)
            report = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("candidate_selection = positive_neighbor", report)
            self.assertIn("source_alt_positive_neighbor_score =", report)

    def test_branch_impact_input_prioritizes_risky_contexts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_dir = tmp_path / "logs" / "BPC_future" / "logical_graph" / "tasks_020" / "case"
            log_dir.mkdir(parents=True)
            log_path = log_dir / "case_randomtw_tasks020_02_seed2_logical_graph.json.jsonl"
            records = [
                {"event": "journey_node_start", "node_id": 0, "depth": 0},
                {
                    "event": "journey_branch_candidates",
                    "node_id": 0,
                    "depth": 0,
                    "priority_mode": "fractionality",
                    "candidate_count": 2,
                    "eligible_count": 2,
                    "selected": {"task_i": 1, "task_j": 2, "fractionality": 0.5},
                    "priority_top": [
                        {"task_i": 1, "task_j": 2, "fractionality": 0.5, "pool_max_child_width": 4},
                        {"task_i": 1, "task_j": 3, "fractionality": 0.5, "pool_max_child_width": 5},
                    ],
                },
                {
                    "event": "journey_branch_candidates",
                    "node_id": 7,
                    "depth": 1,
                    "priority_mode": "fractionality",
                    "candidate_count": 2,
                    "eligible_count": 2,
                    "selected": {"task_i": 4, "task_j": 5, "fractionality": 0.5},
                    "priority_top": [
                        {"task_i": 4, "task_j": 5, "fractionality": 0.5, "pool_max_child_width": 8},
                        {"task_i": 4, "task_j": 6, "fractionality": 0.5, "pool_max_child_width": 9},
                    ],
                },
            ]
            log_path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )
            impact_dir = tmp_path / "impact"
            impact_dir.mkdir()
            impact_rows = [
                self._impact_row(
                    log_file=str(log_path),
                    node_id=0,
                    depth=0,
                    pair=[1, 2],
                    active_touch=0.0,
                    retries=1.0,
                    negative_events=1.0,
                ),
                self._impact_row(
                    log_file=str(log_path),
                    node_id=7,
                    depth=1,
                    pair=[4, 5],
                    active_touch=1.0,
                    retries=8.0,
                    negative_events=17.0,
                ),
            ]
            (impact_dir / "branch_impact_rows.jsonl").write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in impact_rows),
                encoding="utf-8",
            )

            runbook = build_runbook(
                [log_path],
                tmp_path / "out",
                tmp_path / "report.md",
                limit=1,
                alt_pairs_per_event=1,
                branch_impact_inputs=[impact_dir],
            )

            self.assertEqual(runbook["branch_impact_priority_context_count"], 2)
            self.assertEqual(runbook["entry_count"], 1)
            entry = runbook["entries"][0]
            self.assertEqual(entry["source_node_id"], 7)
            self.assertEqual(entry["source_depth"], 1)
            self.assertEqual(entry["source_selected_pair"], [4, 5])
            self.assertEqual(entry["forced_pair"], [4, 6])
            self.assertGreater(float(entry["branch_impact_priority"]), 0.0)
            self.assertIn("active_touch=1", entry["branch_impact_priority_reason"])

    def test_source_depth_filter_keeps_root_events_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_dir = tmp_path / "logs" / "BPC_future" / "logical_graph" / "tasks_020" / "case"
            log_dir.mkdir(parents=True)
            log_path = log_dir / "case_randomtw_tasks020_06_seed6_logical_graph.json.jsonl"
            records = [
                {
                    "event": "journey_branch_candidates",
                    "node_id": 0,
                    "depth": 0,
                    "priority_mode": "fractionality",
                    "selected": {"task_i": 1, "task_j": 2, "fractionality": 0.5},
                    "priority_top": [
                        {"task_i": 1, "task_j": 2, "fractionality": 0.5, "pool_max_child_width": 3},
                        {"task_i": 1, "task_j": 3, "fractionality": 0.5, "pool_max_child_width": 4},
                    ],
                },
                {
                    "event": "journey_branch_candidates",
                    "node_id": 8,
                    "depth": 1,
                    "priority_mode": "fractionality",
                    "selected": {"task_i": 4, "task_j": 5, "fractionality": 0.5},
                    "priority_top": [
                        {"task_i": 4, "task_j": 5, "fractionality": 0.5, "pool_max_child_width": 5},
                        {"task_i": 4, "task_j": 6, "fractionality": 0.5, "pool_max_child_width": 6},
                    ],
                },
            ]
            log_path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )

            runbook = build_runbook(
                [log_path],
                tmp_path / "out",
                tmp_path / "report.md",
                limit=4,
                alt_pairs_per_event=1,
                max_source_depth=0,
            )

            self.assertEqual(runbook["candidate_event_count_seen"], 2)
            self.assertEqual(runbook["depth_filter_skip_count"], 1)
            self.assertEqual(runbook["candidate_event_count_with_replay_entries"], 1)
            self.assertEqual(runbook["max_source_depth"], 0)
            self.assertEqual(runbook["entry_count"], 1)
            entry = runbook["entries"][0]
            self.assertEqual(entry["source_depth"], 0)
            self.assertEqual(entry["source_selected_pair"], [1, 2])
            self.assertEqual(entry["forced_pair"], [1, 3])
            report = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("max_source_depth = 0", report)
            self.assertIn("depth_filter_skip_count = 1", report)

    def test_source_event_time_filter_skips_late_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_dir = tmp_path / "logs" / "BPC_future" / "logical_graph" / "tasks_020" / "case"
            log_dir.mkdir(parents=True)
            log_path = log_dir / "case_randomtw_tasks020_09_seed9_logical_graph.json.jsonl"
            records = [
                {
                    "event": "journey_branch_candidates",
                    "time": 48.5,
                    "node_id": 0,
                    "depth": 0,
                    "priority_mode": "fractionality",
                    "selected": {"task_i": 1, "task_j": 2, "fractionality": 0.5},
                    "priority_top": [
                        {"task_i": 1, "task_j": 2, "fractionality": 0.5, "pool_max_child_width": 3},
                        {"task_i": 1, "task_j": 3, "fractionality": 0.5, "pool_max_child_width": 4},
                    ],
                },
                {
                    "event": "journey_branch_candidates",
                    "time": 240.0,
                    "node_id": 9,
                    "depth": 1,
                    "priority_mode": "fractionality",
                    "selected": {"task_i": 4, "task_j": 5, "fractionality": 0.5},
                    "priority_top": [
                        {"task_i": 4, "task_j": 5, "fractionality": 0.5, "pool_max_child_width": 5},
                        {"task_i": 4, "task_j": 6, "fractionality": 0.5, "pool_max_child_width": 6},
                    ],
                },
            ]
            log_path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )

            runbook = build_runbook(
                [log_path],
                tmp_path / "out",
                tmp_path / "report.md",
                limit=4,
                alt_pairs_per_event=1,
                max_source_event_time=120.0,
            )

            self.assertEqual(runbook["candidate_event_count_seen"], 2)
            self.assertEqual(runbook["source_event_time_filter_skip_count"], 1)
            self.assertEqual(runbook["candidate_event_count_with_replay_entries"], 1)
            self.assertEqual(runbook["max_source_event_time"], 120.0)
            self.assertEqual(runbook["entry_count"], 1)
            entry = runbook["entries"][0]
            self.assertEqual(entry["source_event_time"], 48.5)
            self.assertEqual(entry["source_selected_pair"], [1, 2])
            self.assertEqual(entry["forced_pair"], [1, 3])
            report = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("max_source_event_time = 120.0", report)
            self.assertIn("source_event_time_filter_skip_count = 1", report)

    def test_exclude_runbook_skips_already_sampled_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_dir = tmp_path / "logs" / "BPC_future" / "logical_graph" / "tasks_020" / "case"
            log_dir.mkdir(parents=True)
            log_path = log_dir / "case_randomtw_tasks020_03_seed3_logical_graph.json.jsonl"
            records = [
                {"event": "journey_node_start", "node_id": 0, "depth": 0},
                {
                    "event": "journey_branch_candidates",
                    "node_id": 0,
                    "depth": 0,
                    "priority_mode": "fractionality",
                    "candidate_count": 4,
                    "eligible_count": 4,
                    "selected": {"task_i": 1, "task_j": 2, "fractionality": 0.5},
                    "priority_top": [
                        {"task_i": 1, "task_j": 2, "fractionality": 0.5, "pool_max_child_width": 2},
                        {"task_i": 1, "task_j": 3, "fractionality": 0.5, "pool_max_child_width": 3},
                        {"task_i": 1, "task_j": 4, "fractionality": 0.5, "pool_max_child_width": 4},
                        {"task_i": 1, "task_j": 5, "fractionality": 0.5, "pool_max_child_width": 5},
                    ],
                },
            ]
            log_path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )
            exclude_dir = tmp_path / "exclude"
            exclude_dir.mkdir()
            excluded_instance = (
                "BPC_future/logical_graph/tasks_020/case/"
                "case_randomtw_tasks020_03_seed3_logical_graph.json"
            )
            (exclude_dir / "runbook.json").write_text(
                json.dumps(
                    {
                        "entries": [
                            {
                                "instance": excluded_instance,
                                "source_node_id": 0,
                                "source_depth": 0,
                                "forced_pair": [1, 3],
                            },
                            {
                                "instance": excluded_instance,
                                "source_node_id": 0,
                                "source_depth": 0,
                                "forced_pair": [1, 4],
                            }
                        ]
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            runbook = build_runbook(
                [log_path],
                tmp_path / "out",
                tmp_path / "report.md",
                limit=1,
                alt_pairs_per_event=3,
                exclude_runbooks=[exclude_dir],
            )

            self.assertEqual(runbook["excluded_entry_key_count"], 2)
            self.assertEqual(runbook["excluded_entry_skip_count"], 2)
            self.assertEqual(runbook["entry_count"], 1)
            self.assertEqual(runbook["entries"][0]["forced_pair"], [1, 5])
            report = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("excluded_entry_skip_count = 2", report)

    def test_exclude_runbook_scans_nested_runbook_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_dir = tmp_path / "logs" / "BPC_future" / "logical_graph" / "tasks_020" / "case"
            log_dir.mkdir(parents=True)
            log_path = log_dir / "case_randomtw_tasks020_13_seed13_logical_graph.json.jsonl"
            records = [
                {
                    "event": "journey_branch_candidates",
                    "node_id": 0,
                    "depth": 0,
                    "priority_mode": "fractionality",
                    "candidate_count": 4,
                    "eligible_count": 4,
                    "selected": {"task_i": 1, "task_j": 2, "fractionality": 0.5},
                    "priority_top": [
                        {"task_i": 1, "task_j": 2, "fractionality": 0.5, "pool_max_child_width": 2},
                        {"task_i": 1, "task_j": 3, "fractionality": 0.5, "pool_max_child_width": 3},
                        {"task_i": 1, "task_j": 4, "fractionality": 0.5, "pool_max_child_width": 4},
                    ],
                },
            ]
            log_path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )
            exclude_root = tmp_path / "exclude_root"
            nested = exclude_root / "child_probe_runbooks" / "case"
            nested.mkdir(parents=True)
            instance = (
                "BPC_future/logical_graph/tasks_020/case/"
                "case_randomtw_tasks020_13_seed13_logical_graph.json"
            )
            (nested / "runbook.json").write_text(
                json.dumps(
                    {
                        "entries": [
                            {
                                "instance": instance,
                                "source_node_id": 0,
                                "source_depth": 0,
                                "forced_pair": [1, 3],
                            }
                        ]
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            runbook = build_runbook(
                [log_path],
                tmp_path / "out",
                tmp_path / "report.md",
                limit=2,
                alt_pairs_per_event=2,
                exclude_runbooks=[exclude_root],
            )

            self.assertEqual(runbook["excluded_entry_key_count"], 1)
            self.assertEqual(runbook["excluded_entry_skip_count"], 1)
            self.assertEqual(runbook["entry_count"], 1)
            self.assertEqual(runbook["entries"][0]["forced_pair"], [1, 4])

    def test_focus_delta_input_keeps_timeout_resolved_contexts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_dir = tmp_path / "logs" / "BPC_future" / "logical_graph" / "tasks_020" / "case"
            log_dir.mkdir(parents=True)
            log_path = log_dir / "case_randomtw_tasks020_04_seed4_logical_graph.json.jsonl"
            records = [
                {"event": "journey_node_start", "node_id": 0, "depth": 0},
                {
                    "event": "journey_branch_candidates",
                    "node_id": 0,
                    "depth": 0,
                    "priority_mode": "fractionality",
                    "selected": {"task_i": 1, "task_j": 2, "fractionality": 0.5},
                    "priority_top": [
                        {"task_i": 1, "task_j": 2, "fractionality": 0.5, "pool_max_child_width": 5},
                        {"task_i": 1, "task_j": 3, "fractionality": 0.5, "pool_max_child_width": 6},
                    ],
                },
                {
                    "event": "journey_branch_candidates",
                    "node_id": 4,
                    "depth": 1,
                    "priority_mode": "fractionality",
                    "selected": {"task_i": 5, "task_j": 6, "fractionality": 0.5},
                    "priority_top": [
                        {"task_i": 5, "task_j": 6, "fractionality": 0.5, "pool_max_child_width": 7},
                        {"task_i": 5, "task_j": 8, "fractionality": 0.5, "pool_max_child_width": 8},
                    ],
                },
            ]
            log_path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )
            delta_dir = tmp_path / "delta"
            delta_dir.mkdir()
            instance = (
                "BPC_future/logical_graph/tasks_020/case/"
                "case_randomtw_tasks020_04_seed4_logical_graph.json"
            )
            delta_rows = [
                {
                    "instance": instance,
                    "node_id": 4,
                    "depth": 1,
                    "baseline_pair": [5, 6],
                    "labels": {"y_counterfactual_timeout_resolved": 1.0},
                },
                {
                    "instance": instance,
                    "node_id": 0,
                    "depth": 0,
                    "baseline_pair": [1, 2],
                    "labels": {"y_counterfactual_right_censored": 1.0},
                },
            ]
            (delta_dir / "branch_counterfactual_delta_rows.jsonl").write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in delta_rows),
                encoding="utf-8",
            )

            runbook = build_runbook(
                [log_path],
                tmp_path / "out",
                tmp_path / "report.md",
                limit=4,
                alt_pairs_per_event=1,
                focus_delta_inputs=[delta_dir],
            )

            self.assertEqual(runbook["focus_context_count"], 1)
            self.assertEqual(runbook["focus_event_skip_count"], 1)
            self.assertEqual(runbook["entry_count"], 1)
            entry = runbook["entries"][0]
            self.assertEqual(entry["source_node_id"], 4)
            self.assertEqual(entry["source_depth"], 1)
            self.assertEqual(entry["source_selected_pair"], [5, 6])
            self.assertEqual(entry["forced_pair"], [5, 8])

    def test_focus_delta_input_prioritizes_logged_strong_positive_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_dir = tmp_path / "logs" / "BPC_future" / "logical_graph" / "tasks_020" / "case"
            log_dir.mkdir(parents=True)
            log_path = log_dir / "case_randomtw_tasks020_12_seed12_logical_graph.json.jsonl"
            records = [
                {
                    "event": "journey_branch_candidates",
                    "node_id": 0,
                    "depth": 0,
                    "priority_mode": "fractionality",
                    "selected": {"task_i": 1, "task_j": 2, "fractionality": 0.5},
                    "priority_top": [
                        {"task_i": 1, "task_j": 2, "fractionality": 0.5, "pool_max_child_width": 5},
                        {"task_i": 1, "task_j": 3, "fractionality": 0.49, "pool_max_child_width": 4},
                        {"task_i": 1, "task_j": 4, "fractionality": 0.48, "pool_max_child_width": 3},
                        {"task_i": 1, "task_j": 7, "fractionality": 0.20, "pool_max_child_width": 40},
                    ],
                },
            ]
            log_path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )
            delta_dir = tmp_path / "delta"
            delta_dir.mkdir()
            instance = (
                "BPC_future/logical_graph/tasks_020/case/"
                "case_randomtw_tasks020_12_seed12_logical_graph.json"
            )
            delta_rows = [
                {
                    "instance": instance,
                    "node_id": 0,
                    "depth": 0,
                    "baseline_pair": [1, 2],
                    "alternative_pair": [1, 7],
                    "counterfactual_label_type": "strong_positive",
                    "labels": {},
                },
                {
                    "instance": instance,
                    "node_id": 0,
                    "depth": 0,
                    "baseline_pair": [1, 2],
                    "alternative_pair": [1, 9],
                    "counterfactual_label_type": "strong_positive",
                    "labels": {},
                },
            ]
            (delta_dir / "branch_counterfactual_delta_rows.jsonl").write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in delta_rows),
                encoding="utf-8",
            )

            runbook = build_runbook(
                [log_path],
                tmp_path / "out",
                tmp_path / "report.md",
                limit=4,
                alt_pairs_per_event=1,
                candidate_selection="layered",
                focus_delta_inputs=[delta_dir],
            )

            self.assertEqual(runbook["focus_context_count"], 1)
            self.assertEqual(runbook["focus_strong_positive_pair_count"], 2)
            self.assertEqual(runbook["focus_strong_positive_pair_available_count"], 1)
            self.assertEqual(runbook["focus_strong_positive_pair_missing_count"], 1)
            self.assertEqual(runbook["focus_strong_positive_entry_count"], 1)
            self.assertEqual(runbook["entry_count"], 1)
            entry = runbook["entries"][0]
            self.assertEqual(entry["forced_pair"], [1, 7])
            self.assertEqual(entry["source_alt_selection_reason"], "focus_strong_positive")
            self.assertTrue(entry["source_alt_focus_strong_positive"])
            report = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("focus_strong_positive_pair_missing_count = 1", report)
            self.assertIn("source_alt_selection_reason = focus_strong_positive", report)

    def test_coverage_input_can_focus_score_gap_contexts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_dir = tmp_path / "logs" / "BPC_future" / "logical_graph" / "tasks_020" / "case"
            log_dir.mkdir(parents=True)
            log_path = log_dir / "case_randomtw_tasks020_05_seed5_logical_graph.json.jsonl"
            records = [
                {"event": "journey_node_start", "node_id": 0, "depth": 0},
                {
                    "event": "journey_branch_candidates",
                    "node_id": 0,
                    "depth": 0,
                    "priority_mode": "fractionality",
                    "selected": {"task_i": 1, "task_j": 2, "fractionality": 0.5},
                    "priority_top": [
                        {"task_i": 1, "task_j": 2, "fractionality": 0.5, "pool_max_child_width": 8},
                        {"task_i": 1, "task_j": 3, "fractionality": 0.5, "pool_max_child_width": 9},
                    ],
                },
                {
                    "event": "journey_branch_candidates",
                    "node_id": 9,
                    "depth": 1,
                    "priority_mode": "fractionality",
                    "selected": {"task_i": 4, "task_j": 5, "fractionality": 0.5},
                    "priority_top": [
                        {"task_i": 4, "task_j": 5, "fractionality": 0.5, "pool_max_child_width": 5},
                        {"task_i": 4, "task_j": 7, "fractionality": 0.5, "pool_max_child_width": 6},
                    ],
                },
            ]
            log_path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )
            coverage_dir = tmp_path / "coverage"
            coverage_dir.mkdir()
            coverage_rows = [
                {
                    "log_path": str(log_path),
                    "node_id": 0,
                    "depth": 0,
                    "selected_pair": "1,2",
                    "scored_candidate_count": 1,
                    "eligible_scored_candidate_count": 1,
                    "selected_is_unscored": True,
                    "full_logged_candidate_coverage": True,
                    "would_change_selected": True,
                    "would_change_selected_any_logged": True,
                    "best_scored_pair": "1,3",
                    "best_scored_required_tie_tolerance": 0.0,
                },
                {
                    "log_path": str(log_path),
                    "node_id": 9,
                    "depth": 1,
                    "selected_pair": "4,5",
                    "scored_candidate_count": 0,
                    "eligible_scored_candidate_count": 0,
                    "selected_is_unscored": True,
                    "full_logged_candidate_coverage": True,
                    "would_change_selected": False,
                    "would_change_selected_any_logged": False,
                    "best_scored_pair": None,
                    "best_scored_required_tie_tolerance": None,
                },
            ]
            (coverage_dir / "branch_score_candidate_coverage_rows.jsonl").write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in coverage_rows),
                encoding="utf-8",
            )

            runbook = build_runbook(
                [log_path],
                tmp_path / "out",
                tmp_path / "report.md",
                limit=4,
                alt_pairs_per_event=1,
                coverage_inputs=[coverage_dir],
                coverage_gap_only=True,
            )

            self.assertEqual(runbook["coverage_priority_context_count"], 2)
            self.assertEqual(runbook["coverage_gap_skip_count"], 1)
            self.assertTrue(runbook["coverage_gap_only"])
            self.assertEqual(runbook["entry_count"], 1)
            entry = runbook["entries"][0]
            self.assertEqual(entry["source_node_id"], 9)
            self.assertEqual(entry["source_depth"], 1)
            self.assertEqual(entry["source_selected_pair"], [4, 5])
            self.assertEqual(entry["forced_pair"], [4, 7])
            self.assertTrue(entry["coverage_gap_is_gap"])
            self.assertEqual(entry["coverage_scored_candidate_count"], 0)
            self.assertGreater(float(entry["coverage_gap_priority"]), 100.0)
            report = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("coverage_gap_only = True", report)
            self.assertIn("coverage_gap_skip_count = 1", report)

    def test_child_probe_mode_emits_fixed_budget_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_dir = tmp_path / "logs" / "BPC_future" / "logical_graph" / "tasks_020" / "case"
            log_dir.mkdir(parents=True)
            log_path = log_dir / "case_randomtw_tasks020_07_seed7_logical_graph.json.jsonl"
            records = [
                {"event": "journey_node_start", "node_id": 0, "depth": 0},
                {
                    "event": "journey_child_queued",
                    "parent_node_id": 0,
                    "child_node_id": 4,
                    "depth": 1,
                    "constraint": "RF(2,3)=same_vehicle",
                },
                {"event": "journey_node_start", "node_id": 4, "depth": 1},
                {
                    "event": "journey_branch_candidates",
                    "node_id": 4,
                    "depth": 1,
                    "priority_mode": "fractionality",
                    "candidate_count": 2,
                    "eligible_count": 2,
                    "selected": {"task_i": 4, "task_j": 9, "fractionality": 0.5},
                    "priority_top": [
                        {"task_i": 4, "task_j": 9, "fractionality": 0.5, "pool_max_child_width": 7},
                        {"task_i": 4, "task_j": 12, "fractionality": 0.5, "pool_max_child_width": 8},
                    ],
                },
            ]
            log_path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )

            runbook = build_runbook(
                [log_path],
                tmp_path / "out",
                tmp_path / "report.md",
                time_limit=45,
                limit=2,
                alt_pairs_per_event=1,
                probe_mode="child_probe",
                probe_max_cg_iterations=7,
            )

            self.assertEqual(runbook["probe_mode"], "child_probe")
            self.assertIsNone(runbook["probe_max_nodes"])
            self.assertEqual(runbook["probe_extra_nodes_after_branch"], 2)
            self.assertEqual(runbook["probe_max_cg_iterations"], 7)
            self.assertEqual(runbook["entry_count"], 1)
            entry = runbook["entries"][0]
            self.assertEqual(entry["probe_mode"], "child_probe")
            self.assertEqual(entry["probe_max_nodes"], 4)
            self.assertEqual(entry["probe_max_cg_iterations"], 7)
            self.assertEqual(
                entry["expected_label_source"],
                "fixed_budget_child_probe_then_audit_child_probe_rows",
            )
            command_text = " ".join(entry["command"])
            self.assertIn("max_nodes=4", command_text)
            self.assertIn("journey_max_nodes=4", command_text)
            self.assertIn("max_cg_iterations=7", command_text)
            self.assertIn("journey_max_cg_iterations=7", command_text)
            self.assertIn("journey_tail_action_audit_enabled=True", command_text)
            self.assertIn("journey_corrected_node_bound_audit_enabled=True", command_text)
            self.assertIn("journey_corrected_node_bound_fathom_enabled=False", command_text)
            self.assertIn("journey_tail_action_early_branch_enabled=False", command_text)
            self.assertIn("journey_tail_action_no_column_early_branch_enabled=False", command_text)
            report = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("probe_mode = child_probe", report)
            self.assertIn("probe_max_cg_iterations = 7", report)
            self.assertIn("fixed-budget diagnostic probes", report)

    def test_child_probe_mode_accepts_explicit_node_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            log_dir = tmp_path / "logs" / "BPC_future" / "logical_graph" / "tasks_020" / "case"
            log_dir.mkdir(parents=True)
            log_path = log_dir / "case_randomtw_tasks020_08_seed8_logical_graph.json.jsonl"
            records = [
                {
                    "event": "journey_branch_candidates",
                    "node_id": 0,
                    "depth": 0,
                    "priority_mode": "fractionality",
                    "selected": {"task_i": 1, "task_j": 2, "fractionality": 0.5},
                    "priority_top": [
                        {"task_i": 1, "task_j": 2, "fractionality": 0.5, "pool_max_child_width": 4},
                        {"task_i": 1, "task_j": 3, "fractionality": 0.5, "pool_max_child_width": 5},
                    ],
                },
            ]
            log_path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )

            runbook = build_runbook(
                [log_path],
                tmp_path / "out",
                tmp_path / "report.md",
                limit=1,
                alt_pairs_per_event=1,
                probe_mode="child_probe",
                probe_max_nodes=9,
            )

            self.assertEqual(runbook["probe_max_nodes"], 9)
            entry = runbook["entries"][0]
            self.assertEqual(entry["probe_max_nodes"], 9)
            command_text = " ".join(entry["command"])
            self.assertIn("max_nodes=9", command_text)
            self.assertIn("journey_max_nodes=9", command_text)

    @staticmethod
    def _impact_row(
        *,
        log_file: str,
        node_id: int,
        depth: int,
        pair: list[int],
        active_touch: float,
        retries: float,
        negative_events: float,
    ) -> dict[str, object]:
        return {
            "log_file": log_file,
            "branch_node_id": node_id,
            "depth": depth,
            "task_i": pair[0],
            "task_j": pair[1],
            "tail_class": "completion_bound_tail",
            "right_censored": True,
            "usable_for_branch_impact_training": False,
            "branch_labels": {
                "y_active_touch": active_touch,
                "y_child_completion_bound_retries": retries,
                "y_child_negative_pricing_events": negative_events,
            },
        }


if __name__ == "__main__":
    unittest.main()

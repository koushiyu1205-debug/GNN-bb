from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_journey_tail_minfill_ab_runbook import build_runbook


class JourneyTailMinfillABRunbookTests(unittest.TestCase):
    def test_build_runbook_pairs_baseline_and_optin_for_audit_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            summary_path = tmp_path / "summary.json"
            instance = (
                "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/"
                "demo_seed61921_logical_graph.json"
            )
            summary_path.write_text(
                json.dumps(
                    {
                        "records": [
                            {
                                "instance": instance,
                                "log_file": "logs/demo.jsonl",
                                "finish_status": "TIME_LIMIT",
                                "finish_solving_time": 153.0,
                                "completion_retry_class": (
                                    "completion_bound_time_limit_no_column_uncertified"
                                ),
                                "completion_retry_tail_min_fill_candidate_count": 1,
                                "completion_retry_tail_min_fill_optin_disabled_count": 1,
                                "completion_retry_tail_min_fill_reason_counts": {
                                    "optin_disabled": 1
                                },
                            },
                            {
                                "instance": (
                                    "BPC_future/logical_graph/tasks_020/sector-wave/"
                                    "not_candidate.json"
                                ),
                                "completion_retry_tail_min_fill_candidate_count": 0,
                                "completion_retry_tail_min_fill_optin_disabled_count": 0,
                            },
                        ]
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            runbook = build_runbook(
                profile_summaries=[summary_path],
                output_dir=tmp_path / "out",
                report=tmp_path / "report.md",
                time_limit=260,
                python="/usr/bin/python3",
            )

            self.assertTrue(runbook["diagnostic_only"])
            self.assertFalse(runbook["runs_bpc_or_pricing"])
            self.assertFalse(runbook["official_bound_effect"])
            self.assertEqual(runbook["raw_record_count"], 2)
            self.assertEqual(runbook["entry_count"], 1)
            self.assertEqual(runbook["command_count"], 2)
            entry = runbook["entries"][0]
            self.assertEqual(entry["instance"], instance)
            self.assertIn("journey_tail_action_audit_enabled=True", entry["baseline_command"])
            self.assertIn(
                "journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False",
                entry["baseline_command"],
            )
            self.assertIn(
                "journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=True",
                entry["optin_command"],
            )
            self.assertIn("journey_tail_action_early_branch_enabled=False", entry["optin_command"])
            self.assertIn(
                "journey_tail_action_no_column_early_branch_before_final_probe_enabled=False",
                entry["optin_command"],
            )
            self.assertIn("--time-limit 260", entry["optin_command"])
            self.assertTrue((tmp_path / "out" / "runbook.json").exists())
            self.assertTrue((tmp_path / "out" / "commands.sh").exists())
            report_text = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("runs_bpc_or_pricing = false", report_text)
            self.assertIn("entry_count = 1", report_text)

    def test_build_runbook_can_infer_instance_from_log_file_and_deduplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            summary_path = tmp_path / "summary.json"
            log_file = (
                "BPC_future/results/probe/logs/"
                "BPC_future/logical_graph/tasks_020/random-wave/apollo/"
                "demo_seed61102_logical_graph.json.jsonl"
            )
            summary_path.write_text(
                json.dumps(
                    {
                        "records": [
                            {
                                "log_file": log_file,
                                "finish_status": "OPTIMAL",
                                "finish_solving_time": 250.0,
                                "completion_retry_tail_min_fill_last": {
                                    "completion_bound_diverse_harvest_tail_min_fill_candidate": True,
                                    "completion_bound_diverse_harvest_tail_min_fill_reason": "optin_disabled",
                                },
                            },
                            {
                                "log_file": log_file,
                                "finish_status": "TIME_LIMIT",
                                "finish_solving_time": 150.0,
                                "completion_retry_tail_min_fill_candidate_count": 1,
                                "completion_retry_tail_min_fill_optin_disabled_count": 1,
                            },
                        ]
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            runbook = build_runbook(
                profile_summaries=[summary_path],
                output_dir=tmp_path / "out",
                report=tmp_path / "report.md",
                limit=10,
            )

            self.assertEqual(runbook["entry_count"], 1)
            self.assertEqual(
                runbook["entries"][0]["instance"],
                (
                    "BPC_future/logical_graph/tasks_020/random-wave/apollo/"
                    "demo_seed61102_logical_graph.json"
                ),
            )
            self.assertEqual(runbook["entries"][0]["source_finish_status"], "TIME_LIMIT")

    def test_build_runbook_prioritizes_incomplete_no_column_tail(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            summary_path = tmp_path / "summary.json"
            certified = (
                "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo/"
                "certified_seed1_logical_graph.json"
            )
            incomplete = (
                "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo/"
                "incomplete_seed2_logical_graph.json"
            )
            summary_path.write_text(
                json.dumps(
                    {
                        "records": [
                            {
                                "instance": certified,
                                "finish_status": "OPTIMAL",
                                "finish_solving_time": 300.0,
                                "completion_retry_class": "completion_bound_certified_no_negative",
                                "completion_retry_tail_min_fill_candidate_count": 4,
                                "completion_retry_tail_min_fill_optin_disabled_count": 4,
                            },
                            {
                                "instance": incomplete,
                                "finish_status": "TIME_LIMIT",
                                "finish_solving_time": 120.0,
                                "completion_retry_class": (
                                    "completion_bound_time_limit_no_column_uncertified"
                                ),
                                "completion_retry_tail_min_fill_candidate_count": 1,
                                "completion_retry_tail_min_fill_optin_disabled_count": 1,
                            },
                        ]
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            runbook = build_runbook(
                profile_summaries=[summary_path],
                output_dir=tmp_path / "out",
                report=tmp_path / "report.md",
                limit=2,
            )

            self.assertEqual(runbook["entry_count"], 2)
            self.assertEqual(runbook["entries"][0]["instance"], incomplete)
            self.assertEqual(
                runbook["entries"][0]["source_completion_retry_class"],
                "completion_bound_time_limit_no_column_uncertified",
            )

    def test_build_runbook_can_skip_source_target_optimal_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            summary_path = tmp_path / "summary.json"
            already_target = (
                "BPC_future/logical_graph/tasks_020/random-wave/apollo/"
                "already_target_seed1_logical_graph.json"
            )
            unresolved = (
                "BPC_future/logical_graph/tasks_020/random-wave/apollo/"
                "unresolved_seed2_logical_graph.json"
            )
            summary_path.write_text(
                json.dumps(
                    {
                        "records": [
                            {
                                "instance": already_target,
                                "finish_status": "OPTIMAL",
                                "finish_solving_time": 141.0,
                                "completion_retry_tail_min_fill_candidate_count": 1,
                                "completion_retry_tail_min_fill_optin_disabled_count": 1,
                            },
                            {
                                "instance": unresolved,
                                "finish_status": "TIME_LIMIT",
                                "finish_solving_time": 600.0,
                                "completion_retry_tail_min_fill_candidate_count": 1,
                                "completion_retry_tail_min_fill_optin_disabled_count": 1,
                            },
                        ]
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            runbook = build_runbook(
                profile_summaries=[summary_path],
                output_dir=tmp_path / "out",
                report=tmp_path / "report.md",
                require_source_outside_target_wall=True,
                target_wall=200.0,
            )

            self.assertTrue(runbook["require_source_outside_target_wall"])
            self.assertEqual(runbook["target_wall"], 200.0)
            self.assertEqual(runbook["selection_stats"]["skip_source_target_optimal"], 1)
            self.assertEqual(runbook["entry_count"], 1)
            self.assertEqual(runbook["entries"][0]["instance"], unresolved)
            report_text = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("require_source_outside_target_wall = True", report_text)

    def test_build_runbook_can_filter_candidates_by_tail_action_class(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            summary_path = tmp_path / "summary.json"
            tail_action_dir = tmp_path / "tail_action"
            tail_action_dir.mkdir()
            d_instance = (
                "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo/"
                "d_tail_seed1_logical_graph.json"
            )
            c_instance = (
                "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo/"
                "c_tail_seed2_logical_graph.json"
            )
            summary_path.write_text(
                json.dumps(
                    {
                        "records": [
                            {
                                "instance": d_instance,
                                "log_file": "logs/d_tail.jsonl",
                                "finish_status": "TIME_LIMIT",
                                "completion_retry_class": (
                                    "completion_bound_time_limit_no_column_uncertified"
                                ),
                                "completion_retry_tail_min_fill_candidate_count": 1,
                                "completion_retry_tail_min_fill_optin_disabled_count": 1,
                            },
                            {
                                "instance": c_instance,
                                "log_file": "logs/c_tail.jsonl",
                                "finish_status": "TIME_LIMIT",
                                "completion_retry_class": (
                                    "completion_bound_time_limit_no_column_uncertified"
                                ),
                                "completion_retry_tail_min_fill_candidate_count": 1,
                                "completion_retry_tail_min_fill_optin_disabled_count": 1,
                            },
                        ]
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            tail_rows = [
                {
                    "event": "journey_corrected_node_bound_audit",
                    "log_file": "logs/d_tail.jsonl",
                    "tail_action": "EARLY_BRANCH",
                    "tail_action_class": "D_EARLY_BRANCH",
                    "tail_action_productivity_class": "pricing_unproductive_no_negative_columns",
                },
                {
                    "event": "journey_corrected_node_bound_audit",
                    "log_file": "logs/c_tail.jsonl",
                    "tail_action": "CONTINUE_COLUMN_GENERATION",
                    "tail_action_class": "C_CONTINUE_CG",
                    "tail_action_productivity_class": "pricing_active_support_productive",
                },
            ]
            (tail_action_dir / "tail_action_rows.jsonl").write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in tail_rows),
                encoding="utf-8",
            )

            runbook = build_runbook(
                profile_summaries=[summary_path],
                tail_action_audits=[tail_action_dir],
                output_dir=tmp_path / "out",
                report=tmp_path / "report.md",
                require_tail_action_productivity_class=(
                    "pricing_unproductive_no_negative_columns",
                ),
            )

            self.assertTrue(runbook["tail_action_filter_enabled"])
            self.assertEqual(runbook["tail_action_filter_row_count"], 2)
            self.assertEqual(runbook["tail_action_filter_class_counts"]["D_EARLY_BRANCH"], 1)
            self.assertEqual(runbook["tail_action_filter_class_counts"]["C_CONTINUE_CG"], 1)
            self.assertEqual(runbook["selection_stats"]["skip_tail_action_filter_no_match"], 1)
            self.assertEqual(runbook["entry_count"], 1)
            self.assertEqual(runbook["entries"][0]["instance"], d_instance)
            self.assertEqual(
                runbook["entries"][0]["tail_action_filter_match"]["tail_action_class_counts"],
                {"D_EARLY_BRANCH": 1},
            )
            self.assertEqual(
                runbook["entries"][0]["tail_action_filter_match"][
                    "tail_action_productivity_class_counts"
                ],
                {"pricing_unproductive_no_negative_columns": 1},
            )
            report_text = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("tail_action_filter_enabled = True", report_text)


if __name__ == "__main__":
    unittest.main()

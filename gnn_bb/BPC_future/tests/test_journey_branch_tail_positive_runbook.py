from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_journey_branch_tail_positive_runbook import build_runbook


class JourneyBranchTailPositiveRunbookTests(unittest.TestCase):
    def test_build_runbook_uses_root_near_positive_force_pair(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            positive_gap = tmp_path / "positive_gap.json"
            positive_gap.write_text(
                json.dumps(
                    {
                        "near_positive_rows": [
                            {
                                "source_type": "branch_impact",
                                "depth": 0,
                                "task_i": 2,
                                "task_j": 13,
                                "tail_class": "early_branch_continues",
                                "tail_badness_score": 58.0,
                                "y_child_negative_pricing_events": 5.0,
                                "log_file": (
                                    "BPC_future/results/probe/logs/"
                                    "BPC_future/logical_graph/tasks_020/greedy-anchor/"
                                    "demo_instance.json.jsonl"
                                ),
                            },
                            {
                                "source_type": "branch_impact",
                                "depth": 1,
                                "task_i": 2,
                                "task_j": 3,
                                "tail_class": "early_branch_continues",
                                "log_file": (
                                    "BPC_future/results/probe/logs/"
                                    "BPC_future/logical_graph/tasks_020/greedy-anchor/"
                                    "demo_instance.json.jsonl"
                                ),
                            },
                        ]
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            runbook = build_runbook(
                positive_gap,
                tmp_path / "out",
                tmp_path / "report.md",
                time_limit=123,
            )

            self.assertTrue(runbook["diagnostic_only"])
            self.assertFalse(runbook["runs_bpc_or_pricing"])
            self.assertEqual(
                runbook["base_sample_strategy"],
                "extend_existing_5000_with_branch_tail_interventions",
            )
            self.assertEqual(runbook["entry_count"], 1)
            entry = runbook["entries"][0]
            self.assertEqual(entry["forced_pair"], [2, 13])
            self.assertEqual(
                entry["instance"],
                "BPC_future/logical_graph/tasks_020/greedy-anchor/demo_instance.json",
            )
            self.assertIn("journey_branch_candidate_priority=force_pair:2,13", entry["command"])
            self.assertIn("--time-limit", entry["command"])
            self.assertIn("123", entry["command"])
            self.assertTrue((tmp_path / "out" / "runbook.json").exists())
            self.assertTrue((tmp_path / "out" / "commands.sh").exists())
            self.assertIn("certificate_effect = false", (tmp_path / "report.md").read_text(encoding="utf-8"))

    def test_build_runbook_can_disable_root_near_positive_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            positive_gap = tmp_path / "positive_gap.json"
            positive_gap.write_text(
                json.dumps(
                    {
                        "near_positive_rows": [
                            {
                                "source_type": "branch_impact",
                                "depth": 0,
                                "task_i": 2,
                                "task_j": 13,
                                "log_file": (
                                    "BPC_future/results/probe/logs/"
                                    "BPC_future/logical_graph/tasks_020/greedy-anchor/"
                                    "demo_instance.json.jsonl"
                                ),
                            }
                        ]
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            runbook = build_runbook(
                positive_gap,
                tmp_path / "out",
                tmp_path / "report.md",
                include_root_near_positive=False,
            )

            self.assertFalse(runbook["include_root_near_positive"])
            self.assertEqual(runbook["entry_count"], 0)
            self.assertIn(
                "include_root_near_positive = False",
                (tmp_path / "report.md").read_text(encoding="utf-8"),
            )

    def test_build_runbook_uses_tail_action_rows_for_depth_child_ordering(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            positive_gap = tmp_path / "positive_gap.json"
            positive_gap.write_text(json.dumps({"near_positive_rows": []}) + "\n", encoding="utf-8")
            log_path = (
                tmp_path
                / "probe"
                / "logs"
                / "BPC_future"
                / "logical_graph"
                / "tasks_020"
                / "demo_instance.json.jsonl"
            )
            log_path.parent.mkdir(parents=True)
            log_rows = [
                {"event": "journey_node_start", "time": 1.0, "node_id": 0, "depth": 0},
                {
                    "event": "journey_child_queued",
                    "time": 2.0,
                    "parent_node_id": 0,
                    "child_node_id": 1,
                    "depth": 1,
                    "constraint": "RF(2,10)=same_vehicle",
                },
                {"event": "journey_node_start", "time": 3.0, "node_id": 1, "depth": 1},
                {
                    "event": "journey_child_queued",
                    "time": 4.0,
                    "parent_node_id": 1,
                    "child_node_id": 3,
                    "depth": 2,
                    "constraint": "RF(3,7)=separate_vehicle",
                },
                {"event": "journey_node_start", "time": 5.0, "node_id": 3, "depth": 2},
                {
                    "event": "journey_child_queued",
                    "time": 6.0,
                    "parent_node_id": 3,
                    "child_node_id": 5,
                    "depth": 3,
                    "constraint": "RF(4,12)=same_vehicle",
                },
                {
                    "event": "journey_child_queued",
                    "time": 7.0,
                    "parent_node_id": 3,
                    "child_node_id": 6,
                    "depth": 3,
                    "constraint": "RF(4,12)=separate_vehicle",
                },
                {"event": "journey_node_start", "time": 8.0, "node_id": 5, "depth": 3},
            ]
            log_path.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in log_rows),
                encoding="utf-8",
            )
            tail_dir = tmp_path / "tail"
            tail_dir.mkdir()
            tail_row = {
                "source_type": "tail_action_proof_cost",
                "log_file": str(log_path),
                "node_id": 3,
                "depth": 2,
                "task_i": 4,
                "task_j": 12,
                "tail_class": "tail_action_no_column",
                "labels": {"y_tail_risk": 1.0, "y_child_unstarted": 1.0},
            }
            (tail_dir / "tail_impact_training_rows.jsonl").write_text(
                json.dumps(tail_row, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            runbook = build_runbook(
                positive_gap,
                tmp_path / "out",
                tmp_path / "report.md",
                time_limit=111,
                tail_impact_inputs=[tail_dir],
            )

            self.assertEqual(runbook["entry_count"], 1)
            entry = runbook["entries"][0]
            self.assertEqual(entry["source_type"], "tail_action_proof_cost")
            self.assertEqual(entry["preferred_target_child_kind"], "separate_vehicle")
            self.assertEqual(
                entry["forced_pair_depth_rule"],
                "force_pair_path:0:2,10=same_vehicle;1:3,7=separate_vehicle;2:4,12",
            )
            self.assertEqual(
                entry["forced_pair_path_rule"],
                "force_pair_path:0:2,10=same_vehicle;1:3,7=separate_vehicle;2:4,12",
            )
            self.assertEqual(
                entry["forced_child_kind_depth_rule"],
                "force_child_kind_depth:0:same_vehicle;1:separate_vehicle;2:separate_vehicle",
            )
            self.assertIn(
                "journey_child_priority_mode=force_child_kind_depth:0:same_vehicle;1:separate_vehicle;2:separate_vehicle",
                entry["command"],
            )
            self.assertIn("tail_impact_input_paths", (tmp_path / "report.md").read_text(encoding="utf-8"))

    def test_build_runbook_can_use_before_final_probe_tail_action_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            positive_gap = tmp_path / "positive_gap.json"
            positive_gap.write_text(json.dumps({"near_positive_rows": []}) + "\n", encoding="utf-8")
            log_path = (
                tmp_path
                / "probe"
                / "logs"
                / "BPC_future"
                / "logical_graph"
                / "tasks_020"
                / "demo_instance.json.jsonl"
            )
            log_path.parent.mkdir(parents=True)
            log_rows = [
                {"event": "journey_node_start", "time": 1.0, "node_id": 0, "depth": 0},
                {
                    "event": "journey_child_queued",
                    "time": 2.0,
                    "parent_node_id": 0,
                    "child_node_id": 1,
                    "depth": 1,
                    "constraint": "RF(2,10)=same_vehicle",
                },
                {"event": "journey_node_start", "time": 3.0, "node_id": 1, "depth": 1},
                {
                    "event": "journey_child_queued",
                    "time": 4.0,
                    "parent_node_id": 1,
                    "child_node_id": 3,
                    "depth": 2,
                    "constraint": "RF(3,7)=separate_vehicle",
                },
                {"event": "journey_node_start", "time": 5.0, "node_id": 3, "depth": 2},
            ]
            log_path.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in log_rows),
                encoding="utf-8",
            )
            tail_dir = tmp_path / "tail"
            tail_dir.mkdir()
            tail_row = {
                "source_type": "tail_action_proof_cost",
                "log_file": str(log_path),
                "node_id": 3,
                "depth": 2,
                "task_i": 4,
                "task_j": 12,
                "tail_class": "tail_action_no_column",
                "labels": {"y_tail_risk": 1.0},
            }
            (tail_dir / "tail_impact_training_rows.jsonl").write_text(
                json.dumps(tail_row, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            runbook = build_runbook(
                positive_gap,
                tmp_path / "out",
                tmp_path / "report.md",
                tail_impact_inputs=[tail_dir],
                tail_action_profile="before_final_probe",
            )

            self.assertEqual(runbook["tail_action_profile"], "before_final_probe")
            entry = runbook["entries"][0]
            self.assertEqual(entry["tail_action_profile"], "before_final_probe")
            self.assertIn("journey_tail_action_audit_enabled=True", entry["command"])
            self.assertIn("journey_tail_action_early_branch_enabled=False", entry["command"])
            self.assertIn(
                "journey_tail_action_no_column_early_branch_before_final_probe_enabled=True",
                entry["command"],
            )
            self.assertIn(
                "journey_tail_action_no_column_early_branch_allow_incomplete_limit_before_final_probe=True",
                entry["command"],
            )
            self.assertIn("journey_tail_action_no_column_early_branch_min_tasks=20", entry["command"])
            self.assertIn("journey_tail_action_no_column_early_branch_min_depth=2", entry["command"])
            self.assertIn("journey_tail_action_no_column_early_branch_max_depth=2", entry["command"])
            self.assertNotIn("journey_tail_action_early_branch_enabled=True", entry["command"])
            self.assertIn("tail_action_profile = before_final_probe", (tmp_path / "report.md").read_text(encoding="utf-8"))

    def test_build_runbook_can_use_before_final_probe_gate_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            positive_gap = tmp_path / "positive_gap.json"
            positive_gap.write_text(json.dumps({"near_positive_rows": []}) + "\n", encoding="utf-8")
            log_path = (
                tmp_path
                / "probe"
                / "logs"
                / "BPC_future"
                / "logical_graph"
                / "tasks_020"
                / "demo_gate_instance.json.jsonl"
            )
            log_path.parent.mkdir(parents=True)
            log_rows = [
                {"event": "journey_node_start", "time": 1.0, "node_id": 0, "depth": 0},
                {
                    "event": "journey_branch_candidates",
                    "time": 11.0,
                    "node_id": 0,
                    "depth": 0,
                    "candidate_count": 3,
                    "eligible_count": 2,
                    "priority_mode": "fractionality",
                    "selected": {
                        "task_i": 2,
                        "task_j": 6,
                        "fractionality": 0.5,
                        "pool_balance_gap": 62,
                        "pool_max_child_width": 289,
                        "pool_total_child_width": 516,
                    },
                    "priority_top": [
                        {"task_i": 2, "task_j": 6, "fractionality": 0.5},
                        {"task_i": 1, "task_j": 5, "fractionality": 0.4},
                    ],
                },
            ]
            log_path.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in log_rows),
                encoding="utf-8",
            )
            tail_action_audit = tmp_path / "tail_action_audit"
            tail_action_audit.mkdir()
            gate_row = {
                "log_file": str(log_path),
                "node_id": 0,
                "depth": 0,
                "cg_iter": 22,
                "time": 12.0,
                "tail_action": "EARLY_BRANCH",
                "tail_action_before_final_probe": True,
                "tail_action_reason": "rmp_below_incumbent_pricing_unproductive_for_fathom",
                "gate_reason": "before_final_probe_disabled",
                "rmp_to_incumbent_gap": 12.5,
                "recent_true_rc_productivity": 0,
            }
            (tail_action_audit / "no_column_gate_rows.jsonl").write_text(
                json.dumps(gate_row, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            runbook = build_runbook(
                positive_gap,
                tmp_path / "out",
                tmp_path / "report.md",
                tail_impact_inputs=[tail_action_audit],
                tail_action_profile="before_final_probe",
            )

            self.assertEqual(runbook["entry_count"], 1)
            entry = runbook["entries"][0]
            self.assertEqual(entry["source_type"], "tail_action_gate_opportunity")
            self.assertEqual(entry["source_input_type"], "tail_action_gate_opportunity")
            self.assertEqual(entry["forced_pair"], [2, 6])
            self.assertEqual(entry["forced_pair_depth_rule"], "force_pair_path:0:2,6")
            self.assertEqual(entry["tail_action_profile"], "before_final_probe")
            self.assertIn("journey_tail_action_no_column_early_branch_before_final_probe_enabled=True", entry["command"])
            self.assertIn("journey_tail_action_no_column_early_branch_max_pool_child_width=289", entry["command"])
            self.assertIn("journey_tail_action_no_column_early_branch_max_pool_total_child_width=516", entry["command"])
            self.assertIn("journey_tail_action_no_column_early_branch_max_pool_balance_gap=180", entry["command"])
            self.assertIn("journey_tail_action_no_column_early_branch_min_depth=0", entry["command"])
            self.assertIn("journey_tail_action_no_column_early_branch_max_depth=0", entry["command"])
            self.assertTrue((tmp_path / "out" / "runbook.json").exists())

    def test_build_runbook_can_filter_gate_rows_by_tail_action_productivity(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            positive_gap = tmp_path / "positive_gap.json"
            positive_gap.write_text(json.dumps({"near_positive_rows": []}) + "\n", encoding="utf-8")
            tail_action_audit = tmp_path / "tail_action_audit"
            tail_action_audit.mkdir()
            gate_rows = []
            for stem, task_i, task_j, productivity in (
                ("strict_d", 2, 6, "pricing_unproductive_no_negative_columns"),
                ("productive_cg", 3, 7, "pricing_active_support_productive"),
            ):
                log_path = (
                    tmp_path
                    / "probe"
                    / "logs"
                    / "BPC_future"
                    / "logical_graph"
                    / "tasks_020"
                    / f"{stem}.json.jsonl"
                )
                log_path.parent.mkdir(parents=True, exist_ok=True)
                log_rows = [
                    {"event": "journey_node_start", "time": 1.0, "node_id": 0, "depth": 0},
                    {
                        "event": "journey_branch_candidates",
                        "time": 11.0,
                        "node_id": 0,
                        "depth": 0,
                        "candidate_count": 3,
                        "eligible_count": 2,
                        "priority_mode": "fractionality",
                        "selected": {
                            "task_i": task_i,
                            "task_j": task_j,
                            "fractionality": 0.5,
                            "pool_balance_gap": 62,
                            "pool_max_child_width": 289,
                            "pool_total_child_width": 516,
                        },
                    },
                ]
                log_path.write_text(
                    "".join(json.dumps(row, sort_keys=True) + "\n" for row in log_rows),
                    encoding="utf-8",
                )
                gate_rows.append(
                    {
                        "log_file": str(log_path),
                        "node_id": 0,
                        "depth": 0,
                        "tail_action": "EARLY_BRANCH",
                        "tail_action_class": "D_EARLY_BRANCH",
                        "tail_action_productivity_class": productivity,
                        "tail_action_before_final_probe": True,
                        "gate_reason": "before_final_probe_disabled",
                        "tail_action_reason": "rmp_below_incumbent_pricing_unproductive_for_fathom",
                    }
                )
            (tail_action_audit / "no_column_gate_rows.jsonl").write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in gate_rows),
                encoding="utf-8",
            )

            runbook = build_runbook(
                positive_gap,
                tmp_path / "out",
                tmp_path / "report.md",
                tail_impact_inputs=[tail_action_audit],
                tail_action_profile="before_final_probe",
                require_tail_action_productivity_class=(
                    "pricing_unproductive_no_negative_columns",
                ),
            )

            self.assertEqual(
                runbook["tail_action_productivity_filter"],
                ["pricing_unproductive_no_negative_columns"],
            )
            self.assertEqual(runbook["entry_count"], 1)
            entry = runbook["entries"][0]
            self.assertEqual(entry["forced_pair"], [2, 6])
            self.assertEqual(
                entry["source_tail_action_productivity_class"],
                "pricing_unproductive_no_negative_columns",
            )
            report = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn(
                "tail_action_productivity_filter = ['pricing_unproductive_no_negative_columns']",
                report,
            )

    def test_build_runbook_can_emit_tail_action_alternative_pairs(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            positive_gap = tmp_path / "positive_gap.json"
            positive_gap.write_text(json.dumps({"near_positive_rows": []}) + "\n", encoding="utf-8")
            log_path = (
                tmp_path
                / "probe"
                / "logs"
                / "BPC_future"
                / "logical_graph"
                / "tasks_020"
                / "demo_instance.json.jsonl"
            )
            log_path.parent.mkdir(parents=True)
            log_rows = [
                {"event": "journey_node_start", "time": 1.0, "node_id": 0, "depth": 0},
                {
                    "event": "journey_child_queued",
                    "time": 2.0,
                    "parent_node_id": 0,
                    "child_node_id": 1,
                    "depth": 1,
                    "constraint": "RF(2,10)=same_vehicle",
                },
                {"event": "journey_node_start", "time": 3.0, "node_id": 1, "depth": 1},
                {
                    "event": "journey_child_queued",
                    "time": 4.0,
                    "parent_node_id": 1,
                    "child_node_id": 3,
                    "depth": 2,
                    "constraint": "RF(3,7)=separate_vehicle",
                },
                {"event": "journey_node_start", "time": 5.0, "node_id": 3, "depth": 2},
                {
                    "event": "journey_branch_candidates",
                    "time": 6.0,
                    "node_id": 3,
                    "depth": 2,
                    "selected": {
                        "task_i": 4,
                        "task_j": 12,
                        "fractionality": 0.5,
                        "pool_max_child_width": 111,
                        "pool_total_child_width": 202,
                    },
                    "priority_top": [
                        {
                            "task_i": 4,
                            "task_j": 12,
                            "fractionality": 0.5,
                            "pool_max_child_width": 111,
                            "pool_total_child_width": 202,
                        },
                        {
                            "task_i": 9,
                            "task_j": 13,
                            "fractionality": 0.45,
                            "pool_max_child_width": 90,
                            "pool_total_child_width": 160,
                        },
                        {
                            "task_i": 2,
                            "task_j": 17,
                            "fractionality": 0.4,
                            "pool_max_child_width": 120,
                            "pool_total_child_width": 180,
                        },
                    ],
                },
                {
                    "event": "journey_child_queued",
                    "time": 7.0,
                    "parent_node_id": 3,
                    "child_node_id": 5,
                    "depth": 3,
                    "constraint": "RF(4,12)=same_vehicle",
                },
            ]
            log_path.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in log_rows),
                encoding="utf-8",
            )
            tail_dir = tmp_path / "tail"
            tail_dir.mkdir()
            tail_row = {
                "source_type": "tail_action_proof_cost",
                "log_file": str(log_path),
                "node_id": 3,
                "depth": 2,
                "task_i": 4,
                "task_j": 12,
                "tail_class": "tail_action_no_column",
                "labels": {"y_tail_risk": 1.0},
            }
            (tail_dir / "tail_impact_training_rows.jsonl").write_text(
                json.dumps(tail_row, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            runbook = build_runbook(
                positive_gap,
                tmp_path / "out",
                tmp_path / "report.md",
                time_limit=111,
                tail_impact_inputs=[tail_dir],
                tail_alt_pairs_per_node=1,
            )

            self.assertEqual(runbook["entry_count"], 2)
            alt_entry = runbook["entries"][1]
            self.assertEqual(alt_entry["source_type"], "tail_action_alt_pair")
            self.assertEqual(alt_entry["forced_pair"], [9, 13])
            self.assertEqual(alt_entry["source_original_forced_pair"], [4, 12])
            self.assertEqual(alt_entry["source_alt_rank"], 1)
            self.assertEqual(alt_entry["source_selected_fractionality"], 0.5)
            self.assertEqual(alt_entry["source_alt_fractionality"], 0.45)
            self.assertAlmostEqual(alt_entry["source_alt_fractionality_gap_to_selected"], 0.05)
            self.assertAlmostEqual(alt_entry["source_alt_required_tie_tolerance"], 0.05)
            self.assertEqual(alt_entry["source_alt_pool_max_child_width"], 90)
            self.assertEqual(alt_entry["source_selected_pool_max_child_width"], 111)
            self.assertEqual(
                alt_entry["forced_pair_depth_rule"],
                "force_pair_path:0:2,10=same_vehicle;1:3,7=separate_vehicle;2:9,13",
            )
            self.assertEqual(
                alt_entry["forced_pair_path_rule"],
                "force_pair_path:0:2,10=same_vehicle;1:3,7=separate_vehicle;2:9,13",
            )
            self.assertEqual(
                alt_entry["forced_child_kind_depth_rule"],
                "force_child_kind_depth:0:same_vehicle;1:separate_vehicle",
            )
            self.assertIn(
                "journey_branch_candidate_priority=force_pair_path:0:2,10=same_vehicle;1:3,7=separate_vehicle;2:9,13",
                alt_entry["command"],
            )
            report = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("tail_alt_pairs_per_node = 1", report)
            self.assertIn("source_alt_required_tie_tolerance = 0.05", report)


if __name__ == "__main__":
    unittest.main()

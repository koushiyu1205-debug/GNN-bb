from __future__ import annotations

import json
import shlex
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.build_gat_target_priority_worker_ab_runbook import (
    NO_LEARNING_OVERRIDES,
    REQUIRED_CANDIDATE_CONTEXT_FIELDS,
    WORKER_METHOD_TARGET_MATERIALIZATION_FIXED,
    build_runbook,
)


def _touch_instance(root: Path, *, scale: int, region: str, ordinal: int, seed: int) -> Path:
    path = (
        root
        / f"tasks_{scale:03d}"
        / "sector-wave"
        / region
        / (
            f"{region}_sector-wave_randomtw_tasks{scale:03d}_"
            f"{ordinal:02d}_seed{seed}_logical_graph.json"
        )
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")
    return path


def _context_fields(prefix: str = "ctx") -> dict[str, str]:
    return {
        "true_dual_hash": f"{prefix}-dual",
        "cut_hash": f"{prefix}-cuts",
        "branch_hash": f"{prefix}-branch",
        "forbidden_signature_hash": f"{prefix}-forbidden",
        "active_hash_before": f"{prefix}-active",
        "pool_signature_hash": f"{prefix}-pool-signature",
        "pool_task_set_hash": f"{prefix}-pool-task-set",
    }


class GATTargetPriorityWorkerABRunbookTests(unittest.TestCase):
    def test_runbook_keeps_gat_no_regression_and_builds_target_worker(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            logical_root = tmp / "logical_graph"
            for scale in (5, 10):
                for region in ("apollo15_20km", "tranquillitatis_balmer_like_20km"):
                    _touch_instance(logical_root, scale=scale, region=region, ordinal=1, seed=scale)
            candidate_instance = _touch_instance(
                logical_root,
                scale=20,
                region="apollo15_20km",
                ordinal=1,
                seed=20,
            )
            candidates_file = tmp / "candidates.json"
            candidates_file.write_text(
                json.dumps(
                    {
                        "candidates": [
                            {
                                "name": "apollo20_target",
                                "instance": str(candidate_instance),
                                "expected_context_hash": "c488c428ee5822de",
                                "source_file": "capture/log.jsonl",
                                **_context_fields("apollo20"),
                                "capture_pricing_kind": "exact",
                                "target_sequence": [20, 17, 16],
                                "target_arc_option_sequence": [
                                    "0->20:low_risk:2",
                                    "20->17:low_risk:2",
                                    "17->16:low_risk:2",
                                    "16->0:low_risk:2",
                                ],
                                "target_sortie_traces": [
                                    {
                                        "sequence": [20, 17, 16],
                                        "start_time": 12.0,
                                        "arc_option_sequence": [
                                            "0->20:low_risk:2",
                                            "20->17:low_risk:2",
                                            "17->16:low_risk:2",
                                            "16->0:low_risk:2",
                                        ],
                                    }
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            summary = build_runbook(
                logical_graph_root=logical_root,
                candidates_file=candidates_file,
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(
                set(summary["required_candidate_context_fields"]),
                set(REQUIRED_CANDIDATE_CONTEXT_FIELDS),
            )
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["default_enabled"])
            self.assertFalse(summary["certificate_ready"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertEqual(summary["worker_method"], WORKER_METHOD_TARGET_MATERIALIZATION_FIXED)
            self.assertTrue(summary["mainline_gat_kept_for_5_10"])
            self.assertTrue(summary["mainline_gat_kept_for_20_context_replay"])
            self.assertTrue(summary["candidate_runs"][0]["candidate_context_complete"])
            self.assertEqual(summary["candidate_runs"][0]["source_file"], "capture/log.jsonl")
            self.assertTrue((tmp / "out" / "summary.json").exists())
            self.assertTrue((tmp / "report.md").exists())
            self.assertEqual(len(summary["commands"]), 4)

            commands = {item["command_type"]: item["command"] for item in summary["commands"]}
            for key in (
                "task005_mainline_no_regression_gat_kept",
                "task010_mainline_no_regression_gat_kept",
            ):
                command = commands[key]
                self.assertIn("run_bpc_future_external_timeout_batch.py", command)
                self.assertNotIn("hidden_negative_worker_enabled=True", command)
                for override in NO_LEARNING_OVERRIDES:
                    self.assertNotIn(override, command)

            worker = commands["task020_apollo20_target_target_priority_worker"]
            self.assertIn("journey_sharded_pulse_hidden_negative_worker_enabled=True", worker)
            self.assertIn(
                "journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe",
                worker,
            )
            self.assertIn(
                "journey_sharded_pulse_worker_current_probe_enabled=True",
                worker,
            )
            self.assertIn(
                "journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True",
                worker,
            )
            self.assertIn(
                "journey_sharded_pulse_hidden_negative_worker_max_recursions=0",
                worker,
            )
            self.assertIn(
                "journey_sharded_pulse_worker_current_probe_max_recursions=0",
                worker,
            )
            self.assertIn(
                "journey_sharded_pulse_hidden_negative_worker_archive_enabled=False",
                worker,
            )
            self.assertIn(
                "journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False",
                worker,
            )
            self.assertIn(
                "journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False",
                worker,
            )
            self.assertIn(
                "journey_sharded_pulse_worker_current_probe_harvesting_enabled=False",
                worker,
            )
            self.assertIn(
                "journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False",
                worker,
            )
            self.assertIn(
                "journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False",
                worker,
            )
            self.assertIn(
                "journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False",
                worker,
            )
            self.assertIn(
                "journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True",
                worker,
            )
            self.assertIn(
                "journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=",
                worker,
            )
            self.assertIn(
                "journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False",
                worker,
            )
            self.assertIn(
                "journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True",
                worker,
            )
            self.assertIn("journey_sharded_pulse_hidden_negative_worker_expected_context_hash", worker)
            self.assertIn("c488c428ee5822de", worker)
            self.assertNotIn("--run-log-dir", worker)
            self.assertNotIn(
                "--run-log-dir",
                commands["task020_apollo20_target_mainline_baseline"],
            )
            for key in (
                "task020_apollo20_target_mainline_baseline",
                "task020_apollo20_target_target_priority_worker",
            ):
                for override in NO_LEARNING_OVERRIDES:
                    self.assertNotIn(override, commands[key])
                self.assertIn(
                    "journey_counterfactual_replay_capture_enabled=True",
                    commands[key],
                )
                self.assertIn(
                    "journey_counterfactual_replay_capture_active_basis_enabled=True",
                    commands[key],
                )
            self.assertTrue(
                summary["checks"]["task20_commands_keep_capture_learning_policy"]
            )
            self.assertTrue(summary["checks"]["task20_commands_capture_actual_contexts"])
            self.assertEqual(
                summary["candidate_policy"]["context_miss_policy"],
                "capture_actual_reached_contexts_for_next_iteration",
            )
            self.assertEqual(
                summary["candidate_policy"]["worker_method"],
                WORKER_METHOD_TARGET_MATERIALIZATION_FIXED,
            )
            self.assertTrue(summary["checks"]["worker_method_is_fixed_for_gat_roi"])
            self.assertTrue(summary["checks"]["fixed_worker_commands_disable_pulse_search"])

    def test_arc_option_target_is_shell_quoted_and_certificate_effect_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            logical_root = tmp / "logical_graph"
            for scale in (5, 10):
                for region in ("apollo15_20km", "tranquillitatis_balmer_like_20km"):
                    _touch_instance(logical_root, scale=scale, region=region, ordinal=1, seed=scale)
            candidate_instance = _touch_instance(
                logical_root,
                scale=20,
                region="tranquillitatis_balmer_like_20km",
                ordinal=1,
                seed=20,
            )
            candidates_file = tmp / "candidate.json"
            candidates_file.write_text(
                json.dumps(
                    {
                        "name": "tranq20_target",
                        "instance": str(candidate_instance),
                        "expected_context_hash": "abcd1234",
                        **_context_fields("tranq20"),
                        "capture_pricing_kind": "heuristic",
                        "target_sequence": "20,17,16",
                        "target_arc_option_sequence": (
                            "0->20:low_risk:2,"
                            "20->17:low_risk:2,"
                            "17->16:low_risk:2,"
                            "16->0:low_risk:2"
                        ),
                        "target_sortie_traces": [
                            {
                                "sequence": [20, 17, 16],
                                "start_time": 2.0,
                                "arc_option_sequence": [
                                    "0->20:low_risk:2",
                                    "20->17:low_risk:2",
                                    "17->16:low_risk:2",
                                    "16->0:low_risk:2",
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            summary = build_runbook(
                logical_graph_root=logical_root,
                candidates_file=candidates_file,
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

            commands = {item["command_type"]: item["command"] for item in summary["commands"]}
            worker = commands["task020_tranq20_target_target_priority_worker"]
            self.assertIn(
                "--set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=",
                worker,
            )
            self.assertIn(
                "journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=True",
                worker,
            )
            self.assertIn(
                "journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=False",
                worker,
            )
            split = shlex.split(worker)
            expected_token = (
                "journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence="
                "0->20:low_risk:2,20->17:low_risk:2,17->16:low_risk:2,16->0:low_risk:2"
            )
            self.assertIn(expected_token, split)
            self.assertIn(
                "journey_sharded_pulse_hidden_negative_worker_target_materialization_traces="
                "[{\"arc_option_sequence\":[\"0->20:low_risk:2\",\"20->17:low_risk:2\","
                "\"17->16:low_risk:2\",\"16->0:low_risk:2\"],\"sequence\":[20,17,16],"
                "\"start_time\":2.0}]",
                split,
            )
            forbidden = (
                "journey_final_judge_sharding_enabled=True",
                "journey_pulse_final_judge_enabled=True",
                "journey_sharded_pulse_audit_allow_certificate_effect=True",
                "allow_test_dummy_certificate=True",
                "dummy_certificate=True",
                "certificate_enabled=True",
                "official_bound_effect=True",
            )
            for command in commands.values():
                for token in forbidden:
                    self.assertNotIn(token, command)
            self.assertIn(
                "journey_counterfactual_replay_capture_enabled=True",
                commands["task020_tranq20_target_mainline_baseline"],
            )
            self.assertIn(
                "journey_counterfactual_replay_capture_enabled=True",
                worker,
            )
            self.assertTrue(summary["checks"]["arc_option_values_are_shell_quoted"])

    def test_missing_full_context_marks_runbook_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            logical_root = tmp / "logical_graph"
            for scale in (5, 10):
                for region in ("apollo15_20km", "tranquillitatis_balmer_like_20km"):
                    _touch_instance(logical_root, scale=scale, region=region, ordinal=1, seed=scale)
            candidate_instance = _touch_instance(
                logical_root,
                scale=20,
                region="apollo15_20km",
                ordinal=1,
                seed=20,
            )
            candidates_file = tmp / "candidate_missing_context.json"
            candidates_file.write_text(
                json.dumps(
                    {
                        "name": "missing_context_target",
                        "instance": str(candidate_instance),
                        "expected_context_hash": "ctx-only",
                        "target_sequence": [1],
                        "target_arc_option_sequence": ["0->1:a", "1->0:a"],
                    }
                ),
                encoding="utf-8",
            )

            summary = build_runbook(
                logical_graph_root=logical_root,
                candidates_file=candidates_file,
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

            self.assertFalse(summary["all_checks_pass"])
            self.assertFalse(summary["checks"]["all_candidates_have_full_context"])
            self.assertFalse(summary["candidate_runs"][0]["candidate_context_complete"])

    def test_worker_batch_size_groups_same_context_materialization_journeys(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            logical_root = tmp / "logical_graph"
            for scale in (5, 10):
                for region in ("apollo15_20km", "tranquillitatis_balmer_like_20km"):
                    _touch_instance(logical_root, scale=scale, region=region, ordinal=1, seed=scale)
            candidate_instance = _touch_instance(
                logical_root,
                scale=20,
                region="apollo15_20km",
                ordinal=1,
                seed=20,
            )

            def candidate(name: str, task: int) -> dict:
                return {
                    "name": name,
                    "instance": str(candidate_instance),
                    "expected_context_hash": "ctx-batch",
                    **_context_fields("batch"),
                    "capture_pricing_kind": "exact",
                    "target_sequence": [task],
                    "target_arc_option_sequence": [
                        f"0->{task}:low_risk:2",
                        f"{task}->0:low_risk:2",
                    ],
                    "target_sortie_traces": [
                        {
                            "sequence": [task],
                            "start_time": 0.0,
                            "arc_option_sequence": [
                                f"0->{task}:low_risk:2",
                                f"{task}->0:low_risk:2",
                            ],
                        }
                    ],
                }

            candidates_file = tmp / "batch_candidates.json"
            third = candidate("third", 3)
            third["expected_context_hash"] = "ctx-singleton"
            candidates_file.write_text(
                json.dumps(
                    {"candidates": [candidate("first", 1), candidate("second", 2), third]}
                ),
                encoding="utf-8",
            )

            summary = build_runbook(
                logical_graph_root=logical_root,
                candidates_file=candidates_file,
                output_dir=tmp / "out",
                report=tmp / "report.md",
                worker_batch_size=2,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["input_candidate_count"], 3)
            self.assertEqual(summary["candidate_group_count"], 2)
            self.assertEqual(summary["candidate_runs"][0]["candidate_batch_count"], 2)
            commands = {item["command_type"]: item["command"] for item in summary["commands"]}
            worker = next(
                command
                for key, command in commands.items()
                if key.endswith("_target_priority_worker")
            )
            self.assertIn(
                "journey_sharded_pulse_hidden_negative_worker_target_materialization_journeys=",
                worker,
            )
            self.assertNotIn(
                "journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=",
                worker,
            )
            singleton_worker = next(
                command
                for key, command in commands.items()
                if key.startswith("task020_third_") and key.endswith("_target_priority_worker")
            )
            self.assertIn(
                "journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=",
                singleton_worker,
            )
            self.assertNotIn(
                "journey_sharded_pulse_hidden_negative_worker_target_materialization_journeys=",
                singleton_worker,
            )
            self.assertTrue(summary["checks"]["batch_worker_commands_have_materialization_journeys"])
            self.assertTrue(summary["checks"]["fixed_worker_commands_have_materialization_payload"])


if __name__ == "__main__":
    unittest.main()

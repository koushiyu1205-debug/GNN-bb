from __future__ import annotations

import json
import shlex
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.build_gat_target_priority_worker_ab_runbook import (
    NO_LEARNING_OVERRIDES,
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
                                "target_sequence": [20, 17, 16],
                                "target_arc_option_sequence": [
                                    "0->20:low_risk:2",
                                    "20->17:low_risk:2",
                                    "17->16:low_risk:2",
                                    "16->0:low_risk:2",
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
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["default_enabled"])
            self.assertFalse(summary["certificate_ready"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertTrue(summary["mainline_gat_kept_for_5_10"])
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
            self.assertIn("journey_sharded_pulse_hidden_negative_worker_expected_context_hash", worker)
            self.assertIn("c488c428ee5822de", worker)
            self.assertNotIn("--run-log-dir", worker)
            self.assertNotIn(
                "--run-log-dir",
                commands["task020_apollo20_target_no_learning_baseline"],
            )
            for override in NO_LEARNING_OVERRIDES:
                self.assertIn(override, worker)

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
                        "target_sequence": "20,17,16",
                        "target_arc_option_sequence": (
                            "0->20:low_risk:2,"
                            "20->17:low_risk:2,"
                            "17->16:low_risk:2,"
                            "16->0:low_risk:2"
                        ),
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
            split = shlex.split(worker)
            expected_token = (
                "journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence="
                "0->20:low_risk:2,20->17:low_risk:2,17->16:low_risk:2,16->0:low_risk:2"
            )
            self.assertIn(expected_token, split)
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
            self.assertTrue(summary["checks"]["arc_option_values_are_shell_quoted"])


if __name__ == "__main__":
    unittest.main()

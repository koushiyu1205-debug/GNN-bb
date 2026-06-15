from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.build_gat_same_run_batch_impact_audit_ab_runbook import (
    CAPTURE_OVERRIDES,
    build_runbook,
)


class GATSameRunBatchImpactAuditABRunbookTests(unittest.TestCase):
    def test_runbook_keeps_mainline_gat_and_disables_online_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            root = tmp / "logical_graph"
            _write_instances(root)
            dataset = tmp / "dataset"
            checkpoint = tmp / "same_run_gat.pt"
            training = tmp / "training_summary.json"
            dataset.mkdir()
            checkpoint.write_text("placeholder", encoding="utf-8")
            training.write_text("{}", encoding="utf-8")

            summary = build_runbook(
                output_dir=tmp / "out",
                report=tmp / "report.md",
                logical_graph_root=root,
                dataset_dir=dataset,
                checkpoint=checkpoint,
                training_summary=training,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["active_worker_ready"])
            self.assertFalse(summary["certificate_ready"])
            self.assertFalse(summary["default_enabled"])
            self.assertTrue(summary["checks"]["mainline_learning_kept"])
            self.assertTrue(summary["checks"]["memory_guard_single_worker"])
            self.assertEqual(summary["audit_decision_scope"], "validation")
            solver_commands = [
                item["command"]
                for item in summary["commands"]
                if item["command_type"].startswith("task")
            ]
            self.assertTrue(solver_commands)
            for command in solver_commands:
                self.assertNotIn("journey_learning_enabled=False", command)
                self.assertNotIn("journey_sharded_pulse_hidden_negative_worker_enabled=True", command)
                self.assertIn("--max-workers 1", command)
            capture_commands = [
                item["command"]
                for item in summary["commands"]
                if item["command_type"].endswith("_capture")
            ]
            self.assertTrue(capture_commands)
            for command in capture_commands:
                for override in CAPTURE_OVERRIDES:
                    self.assertIn(override, command)
            audit_command = next(
                item["command"]
                for item in summary["commands"]
                if item["command_type"] == "same_run_gat_knn_ood_offline_audit"
            )
            self.assertIn("audit_gat_same_run_batch_impact_knn_ood.py", audit_command)
            self.assertIn(str(checkpoint), audit_command)
            self.assertIn(str(training), audit_command)
            self.assertIn("--decision-scope validation", audit_command)
            command_types = {item["command_type"] for item in summary["commands"]}
            self.assertIn("same_run_batch_impact_rows_build", command_types)
            self.assertIn("same_run_batch_impact_graph_dataset_build", command_types)
            self.assertIn("target_priority_candidate_extract", command_types)
            self.assertIn("delay_queue_candidate_extract", command_types)
            self.assertTrue(summary["checks"]["post_capture_pipeline_present"])
            self.assertTrue(summary["checks"]["candidate_extract_uses_audit_decision_records"])
            high_extract = next(
                item["command"]
                for item in summary["commands"]
                if item["command_type"] == "target_priority_candidate_extract"
            )
            delay_extract = next(
                item["command"]
                for item in summary["commands"]
                if item["command_type"] == "delay_queue_candidate_extract"
            )
            self.assertIn(str(summary["decision_records"]), high_extract)
            self.assertIn(str(summary["decision_records"]), delay_extract)
            self.assertIn("--delay-queue-only", delay_extract)
            self.assertNotIn("--delay-queue-only", high_extract)
            self.assertEqual(
                summary["candidate_policy"]["unsafe_negative_decision"],
                "DELAY_QUEUE",
            )
            self.assertFalse(
                summary["candidate_policy"]["permanent_negative_filter_allowed"]
            )
            loaded = json.loads((tmp / "out" / "summary.json").read_text())
            self.assertEqual(loaded["schema_version"], summary["schema_version"])
            self.assertTrue((tmp / "report.md").exists())

    def test_runbook_can_emit_all_scope_decisions_for_sampling_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            root = tmp / "logical_graph"
            _write_instances(root)
            dataset = tmp / "dataset"
            checkpoint = tmp / "same_run_gat.pt"
            training = tmp / "training_summary.json"
            dataset.mkdir()
            checkpoint.write_text("placeholder", encoding="utf-8")
            training.write_text("{}", encoding="utf-8")

            summary = build_runbook(
                output_dir=tmp / "out",
                report=tmp / "report.md",
                logical_graph_root=root,
                dataset_dir=dataset,
                checkpoint=checkpoint,
                training_summary=training,
                decision_scope="all",
            )

            audit_command = next(
                item["command"]
                for item in summary["commands"]
                if item["command_type"] == "same_run_gat_knn_ood_offline_audit"
            )
            self.assertEqual(summary["audit_decision_scope"], "all")
            self.assertIn("--decision-scope all", audit_command)
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["certificate_ready"])
            self.assertTrue(summary["checks"]["candidate_extract_uses_audit_decision_records"])

    def test_runbook_can_target_cross_family_twenty_sampling_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            root = tmp / "logical_graph"
            _write_instances(root)
            dataset = tmp / "dataset"
            checkpoint = tmp / "same_run_gat.pt"
            training = tmp / "training_summary.json"
            dataset.mkdir()
            checkpoint.write_text("placeholder", encoding="utf-8")
            training.write_text("{}", encoding="utf-8")

            summary = build_runbook(
                output_dir=tmp / "out",
                report=tmp / "report.md",
                logical_graph_root=root,
                dataset_dir=dataset,
                checkpoint=checkpoint,
                training_summary=training,
                twenty_families=("greedy-anchor", "random-wave"),
                twenty_ordinals=(1, 9),
                twenty_max_instances=8,
                decision_scope="all",
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(
                summary["requested_twenty_families"],
                ["greedy-anchor", "random-wave"],
            )
            self.assertEqual(
                summary["selected_families_by_scale"]["20"],
                ["greedy-anchor", "random-wave"],
            )
            self.assertTrue(summary["checks"]["selected_twenty_families_available"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["certificate_ready"])
            task20_capture = next(
                item["command"]
                for item in summary["commands"]
                if item["command_type"] == "task020_capture"
            )
            self.assertIn("greedy-anchor", task20_capture)
            self.assertIn("random-wave", task20_capture)
            self.assertIn("--max-workers 1", task20_capture)


def _write_instances(root: Path) -> None:
    for scale in (5, 10, 20):
        for family in ("sector-wave", "greedy-anchor", "random-wave"):
            for region, seed in (
                ("apollo15_20km", 100 + scale),
                ("tranquillitatis_balmer_like_20km", 200 + scale),
            ):
                path = (
                    root
                    / f"tasks_{scale:03d}"
                    / family
                    / region
                    / f"{region}_{family}_randomtw_tasks{scale:03d}_01_seed{seed}_logical_graph.json"
                )
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}", encoding="utf-8")
    for family in ("sector-wave", "greedy-anchor", "random-wave"):
        for region, seed in (
            ("apollo15_20km", 309),
            ("tranquillitatis_balmer_like_20km", 409),
        ):
            path = (
                root
                / "tasks_020"
                / family
                / region
                / f"{region}_{family}_randomtw_tasks020_09_seed{seed}_logical_graph.json"
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()

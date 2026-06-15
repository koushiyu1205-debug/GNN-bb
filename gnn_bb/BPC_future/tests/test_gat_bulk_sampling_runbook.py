from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.build_cbf_family_capture_worklist import CAPTURE_OVERRIDES
from BPC_future.scripts.build_gat_bulk_sampling_runbook import build_bulk_sampling_runbook


class GATBulkSamplingRunbookTests(unittest.TestCase):
    def test_builds_capture_only_twenty_waves_and_keeps_safety_guards(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            root = tmp / "logical_graph"
            _write_instances(root)
            existing_rows = [
                {
                    "instance_path": str(
                        root
                        / "tasks_020"
                        / "random-wave"
                        / "apollo15_20km"
                        / (
                            "apollo15_20km_random-wave_randomtw_tasks020_01_"
                            "seed61000_logical_graph.json"
                        )
                    ),
                    "label_objective_improved": 1,
                },
                {
                    "instance_path": str(
                        root
                        / "tasks_020"
                        / "greedy-anchor"
                        / "tranquillitatis_balmer_like_20km"
                        / (
                            "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_"
                            "seed61022_logical_graph.json"
                        )
                    ),
                    "label_objective_improved": 0,
                    "label_positive_trajectory_roi": 1,
                    "roi_class": "positive_retry_roi",
                },
                {
                    "instance_path": str(
                        root
                        / "tasks_020"
                        / "random-wave"
                        / "apollo15_20km"
                        / (
                            "apollo15_20km_random-wave_randomtw_tasks020_02_"
                            "seed61102_logical_graph.json"
                        )
                    ),
                    "label_objective_improved": 0,
                },
            ]
            row_jsonl = tmp / "rows.jsonl"
            row_jsonl.write_text(
                "\n".join(json.dumps(row, sort_keys=True) for row in existing_rows) + "\n",
                encoding="utf-8",
            )

            summary = build_bulk_sampling_runbook(
                output_dir=tmp / "out",
                report=tmp / "report.md",
                logical_graph_root=root,
                existing_row_jsonl=(row_jsonl,),
                families=("random-wave", "greedy-anchor"),
                bulk_scales=(20, 30),
                twenty_ordinals=(1, 2, 3, 4),
                target_total_samples=30,
                target_positive_samples=10,
                expected_rows_per_instance=5.0,
                expected_positive_per_instance=2.0,
                max_new_instances=6,
                instances_per_wave=3,
                max_workers=4,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["active_worker_ready"])
            self.assertFalse(summary["certificate_ready"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertEqual(summary["existing_row_count"], 3)
            self.assertEqual(summary["existing_positive_count"], 2)
            self.assertGreater(summary["selected_new_instance_count"], 0)
            self.assertGreaterEqual(summary["estimated_total_after"], 30)
            self.assertGreaterEqual(summary["estimated_positive_after"], 10)
            self.assertTrue(summary["checks"]["memory_guard_parallel_workers_bounded"])
            self.assertTrue(summary["checks"]["bulk_is_capture_only"])
            self.assertTrue(summary["checks"]["no_bulk_baseline_commands"])
            self.assertTrue(summary["checks"]["selected_instances_not_previously_sampled"])
            self.assertEqual(
                summary["bulk_sampling_policy"]["cheap_sampling"],
                "multi_scale_capture_only",
            )
            self.assertEqual(summary["bulk_sampling_policy"]["max_workers"], 4)
            self.assertEqual(summary["bulk_scales"], [20, 30])
            self.assertTrue(
                {20, 30}.issubset(
                    {int(item["task_count"]) for item in summary["selected_bulk_instances"]}
                )
            )
            self.assertFalse(
                summary["bulk_sampling_policy"]["permanent_negative_filter_allowed"]
            )
            commands = summary["commands"]
            command_types = {item["command_type"] for item in commands}
            self.assertIn("task005_baseline_sentinel", command_types)
            self.assertIn("task010_capture_sentinel", command_types)
            self.assertIn("same_run_gat_train_offline", command_types)
            self.assertIn("same_run_gat_knn_ood_offline_audit", command_types)
            self.assertIn("target_priority_candidate_extract", command_types)
            self.assertIn("delay_queue_candidate_extract", command_types)
            self.assertFalse(
                any(item["command_type"].startswith("task020_baseline") for item in commands)
            )
            task20_commands = [
                item["command"]
                for item in commands
                if "_bulk_capture_wave" in item["command_type"]
            ]
            self.assertTrue(task20_commands)
            for command in task20_commands:
                self.assertIn("--max-workers 4", command)
                for override in CAPTURE_OVERRIDES:
                    self.assertIn(override, command)
                self.assertNotIn("worker_enabled=True", command)
                self.assertNotIn("certificate_enabled=True", command)
            self.assertTrue((tmp / "out" / "summary.json").exists())
            self.assertTrue((tmp / "report.md").exists())


def _write_instances(root: Path) -> None:
    for scale in (5, 10):
        for region, seed in (
            ("apollo15_20km", 100 + scale),
            ("tranquillitatis_balmer_like_20km", 200 + scale),
        ):
            path = (
                root
                / f"tasks_{scale:03d}"
                / "random-wave"
                / region
                / f"{region}_random-wave_randomtw_tasks{scale:03d}_01_seed{seed}_logical_graph.json"
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}", encoding="utf-8")
    for scale in (20, 30):
        for family in ("random-wave", "greedy-anchor"):
            for ordinal in (1, 2, 3, 4):
                for region, seed_base in (
                    ("apollo15_20km", 61000),
                    ("tranquillitatis_balmer_like_20km", 61001),
                ):
                    seed = seed_base + ordinal + scale
                    path = (
                        root
                        / f"tasks_{scale:03d}"
                        / family
                        / region
                        / (
                            f"{region}_{family}_randomtw_tasks{scale:03d}_{ordinal:02d}_"
                            f"seed{seed}_logical_graph.json"
                        )
                    )
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("{}", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()

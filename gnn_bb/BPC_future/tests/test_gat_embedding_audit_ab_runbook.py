from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.build_cbf_family_capture_worklist import CAPTURE_OVERRIDES
from BPC_future.scripts.build_gat_embedding_audit_ab_runbook import (
    NO_GNN_BASELINE_OVERRIDES,
    build_runbook,
)


def _touch_instance(root: Path, *, scale: int, region: str, ordinal: int, seed: int) -> Path:
    family = "sector-wave"
    path = (
        root
        / f"tasks_{scale:03d}"
        / family
        / region
        / (
            f"{region}_{family}_randomtw_tasks{scale:03d}_"
            f"{ordinal:02d}_seed{seed}_logical_graph.json"
        )
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")
    return path


class GATEmbeddingAuditABRunbookTests(unittest.TestCase):
    def test_runbook_builds_5_10_20_pairs_without_online_effect(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            logical_root = tmp / "logical_graph"
            for scale in (5, 10, 20):
                for region in ("apollo15_20km", "tranquillitatis_balmer_like_20km"):
                    _touch_instance(logical_root, scale=scale, region=region, ordinal=1, seed=scale * 1000)
                    _touch_instance(logical_root, scale=scale, region=region, ordinal=5, seed=scale * 1000 + 5)

            summary = build_runbook(
                logical_graph_root=logical_root,
                output_dir=tmp / "out",
                report=tmp / "report.md",
                train_dataset_dir=tmp / "train_dataset",
                checkpoint=tmp / "gat.pt",
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["active_worker_ready"])
            self.assertFalse(summary["certificate_ready"])
            self.assertEqual({pair["task_count"] for pair in summary["result_pairs"]}, {5, 10, 20})
            self.assertEqual(len(summary["commands"]), 8)
            self.assertTrue((tmp / "out" / "summary.json").exists())
            self.assertTrue((tmp / "report.md").exists())
            for pair in summary["result_pairs"]:
                self.assertGreater(pair["instance_count"], 0)
                for item in pair["instances"]:
                    self.assertEqual(item["family"], "sector-wave")
                    self.assertTrue(Path(item["instance"]).exists())

    def test_commands_are_capture_only_and_validation_uses_gat_embedding(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            logical_root = tmp / "logical_graph"
            for scale in (5, 10, 20):
                for region in ("apollo15_20km", "tranquillitatis_balmer_like_20km"):
                    _touch_instance(logical_root, scale=scale, region=region, ordinal=1, seed=scale * 1000)
                    _touch_instance(logical_root, scale=scale, region=region, ordinal=5, seed=scale * 1000 + 5)

            checkpoint = tmp / "gat.pt"
            train_dir = tmp / "train_dataset"
            summary = build_runbook(
                logical_graph_root=logical_root,
                output_dir=tmp / "out",
                report=tmp / "report.md",
                train_dataset_dir=train_dir,
                checkpoint=checkpoint,
            )

            commands = {item["command_type"]: item["command"] for item in summary["commands"]}
            self.assertIn(
                "BPC_future/configs/moon_trek_5_journey.yaml",
                commands["task005_baseline"],
            )
            self.assertIn(
                "BPC_future/configs/moon_trek_5_journey.yaml",
                commands["task005_capture"],
            )
            self.assertIn(
                "BPC_future/configs/moon_trek_10_journey.yaml",
                commands["task010_baseline"],
            )
            self.assertIn(
                "BPC_future/configs/moon_trek_10_journey.yaml",
                commands["task010_capture"],
            )
            self.assertIn(
                "BPC_future/configs/moon_trek_20_smoke.yaml",
                commands["task020_baseline"],
            )
            self.assertIn(
                "BPC_future/configs/moon_trek_20_smoke.yaml",
                commands["task020_capture"],
            )
            for scale in (5, 10, 20):
                baseline = commands[f"task{scale:03d}_baseline"]
                capture = commands[f"task{scale:03d}_capture"]
                for override in NO_GNN_BASELINE_OVERRIDES:
                    self.assertIn(override, baseline)
                    self.assertIn(override, capture)
                self.assertNotIn("journey_final_judge_sharding_enabled=true", baseline)
                self.assertNotIn("journey_pulse_final_judge_enabled=true", baseline)
                self.assertNotIn("worker_enabled=true", baseline)
                self.assertFalse(any(override in baseline for override in CAPTURE_OVERRIDES))
                for override in CAPTURE_OVERRIDES:
                    self.assertIn(override, capture)
                self.assertNotIn("journey_final_judge_sharding_enabled=true", capture)
                self.assertNotIn("journey_pulse_final_judge_enabled=true", capture)
                self.assertNotIn("worker_enabled=true", capture)

            validation = commands["task020_gat_embedding_capture_validation"]
            self.assertIn("audit_gat_embedding_knn_ood_capture_validation.py", validation)
            self.assertIn(str(checkpoint), validation)
            self.assertIn(str(train_dir), validation)
            self.assertIn("--knn-k 3", validation)
            self.assertIn("--min-high-priority-threshold 0.750000", validation)
            self.assertTrue(summary["checks"]["validation_uses_gat_embedding_candidate"])
            self.assertFalse(summary["proof_budget_contract"]["delay_queue_can_extend_proof_budget"])
            self.assertFalse(summary["proof_budget_contract"]["delay_queue_runs_proof_sweep"])


if __name__ == "__main__":
    unittest.main()

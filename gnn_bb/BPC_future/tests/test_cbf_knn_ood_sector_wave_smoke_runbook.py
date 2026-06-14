from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.build_cbf_family_capture_worklist import CAPTURE_OVERRIDES
from BPC_future.scripts.build_cbf_knn_ood_sector_wave_smoke_runbook import (
    build_runbook,
)


def _touch_instance(root: Path, *, region: str, ordinal: int, seed: int) -> Path:
    path = (
        root
        / region
        / (
            f"{region}_sector-wave_randomtw_tasks020_"
            f"{ordinal:02d}_seed{seed}_logical_graph.json"
        )
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")
    return path


class CBFKNNOODSectorWaveSmokeRunbookTests(unittest.TestCase):
    def test_runbook_is_sector_wave_only_and_writes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            tasks_root = tmp / "tasks_020" / "sector-wave"
            for region in ("apollo15_20km", "tranquillitatis_balmer_like_20km"):
                _touch_instance(tasks_root, region=region, ordinal=1, seed=61000)
                _touch_instance(tasks_root, region=region, ordinal=5, seed=61410)
                _touch_instance(tasks_root, region=region, ordinal=9, seed=61821)
            train_dataset = tmp / "train.jsonl"
            train_dataset.write_text("", encoding="utf-8")
            output_dir = tmp / "out"
            report = tmp / "report.md"

            summary = build_runbook(
                tasks_root=tasks_root,
                train_dataset=train_dataset,
                output_dir=output_dir,
                report=report,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["target_task_family"], "20|sector-wave")
            self.assertEqual(summary["selected_instance_count"], 4)
            self.assertTrue((output_dir / "summary.json").exists())
            self.assertTrue(report.exists())
            saved = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["schema_version"], "cbf_knn_ood_sector_wave_smoke_runbook_v1")
            for item in summary["selected_instances"]:
                self.assertEqual(item["task_family"], "20|sector-wave")
                self.assertIn("/tasks_020/sector-wave/", item["instance"])
                self.assertIn(int(item["ordinal"]), {1, 5})
                self.assertTrue(Path(item["instance"]).exists())

    def test_commands_are_capture_only_and_validation_uses_k3_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            tasks_root = tmp / "tasks_020" / "sector-wave"
            for region in ("apollo15_20km", "tranquillitatis_balmer_like_20km"):
                _touch_instance(tasks_root, region=region, ordinal=1, seed=61000)
                _touch_instance(tasks_root, region=region, ordinal=5, seed=61410)
            summary = build_runbook(
                tasks_root=tasks_root,
                train_dataset=tmp / "train.jsonl",
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["active_worker_ready"])
            self.assertFalse(summary["certificate_ready"])
            self.assertEqual(len(summary["commands"]), 2)

            capture_command = summary["commands"][0]["command"]
            validation_command = summary["commands"][1]["command"]
            self.assertIn("run_bpc_future_external_timeout_batch.py", capture_command)
            for override in CAPTURE_OVERRIDES:
                self.assertIn(override, capture_command)
            self.assertNotIn("worker_enabled=true", capture_command)
            self.assertNotIn("journey_final_judge_sharding_enabled=true", capture_command)
            self.assertNotIn("journey_pulse_final_judge_enabled=true", capture_command)
            self.assertNotIn("certificate_enabled=true", capture_command)

            self.assertIn("audit_cbf_delay_queue_knn_ood_capture_validation.py", validation_command)
            self.assertIn("--knn-k 3", validation_command)
            self.assertIn("--min-high-priority-threshold 0.800000", validation_command)
            self.assertIn("--safe-radius-quantile 1.000000", validation_command)
            self.assertIn("--safe-radius-multiplier 1.000000", validation_command)
            self.assertTrue(summary["checks"]["validation_uses_k3_candidate"])
            self.assertFalse(summary["proof_budget_contract"]["delay_queue_can_extend_proof_budget"])
            self.assertFalse(summary["proof_budget_contract"]["delay_queue_runs_proof_sweep"])


if __name__ == "__main__":
    unittest.main()

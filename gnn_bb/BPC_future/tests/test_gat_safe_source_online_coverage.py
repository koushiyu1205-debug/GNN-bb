from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_gat_safe_source_online_coverage import (
    audit_safe_source_online_coverage,
    _infer_online_context_from_path,
)


class GATSafeSourceOnlineCoverageAuditTests(unittest.TestCase):
    def test_infers_online_context_from_legacy_family_folder(self) -> None:
        path = Path(
            "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/"
            "apollo15_20km_sector-wave_tasks020_01_logical_graph.json.jsonl"
        )

        self.assertEqual(_infer_online_context_from_path(path), ("sector-wave", "20"))

    def test_infers_online_context_from_balanced60_flat_task_folder(self) -> None:
        path = Path(
            "BPC_future/results/probe/logs_tasks5/BPC_future/data/generated/"
            "moon_trek_balanced_60_20260609/logical_graphs/apollo15_20km/tasks_05/"
            "apollo15_20km_balanced_tasks05_01_seed36000_logical_graph.json.jsonl"
        )

        self.assertEqual(_infer_online_context_from_path(path), ("balanced", "5"))

    def test_reports_exact_miss_task_set_hit_and_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            safe_source = root / "safe_source.json"
            decision_records = root / "decision_records.jsonl"
            log_dir = root / "logs"
            output_dir = root / "out"
            report = root / "report.md"
            log_dir.mkdir()

            safe_source.write_text(
                json.dumps(
                    {
                        "safe_source_ready": True,
                        "safe_candidate_ids": ["safe-a"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            records = [
                {
                    "candidate_signature_ids": ["safe-a"],
                    "candidate_task_sets": [[1, 2]],
                    "high_priority_candidate_signature_ids": ["safe-a"],
                    "label_high_priority": 1,
                    "decision_name": "HIGH_PRIORITY",
                    "instance_family": "sector-wave",
                    "instance_task_count": "20",
                },
                {
                    "candidate_signature_ids": ["delay-a"],
                    "candidate_task_sets": [[1, 2]],
                    "high_priority_candidate_signature_ids": [],
                    "label_high_priority": 0,
                    "decision_name": "DELAY_QUEUE",
                    "instance_family": "sector-wave",
                    "instance_task_count": "20",
                },
            ]
            decision_records.write_text(
                "\n".join(json.dumps(record) for record in records) + "\n",
                encoding="utf-8",
            )
            (log_dir / "probe.jsonl").write_text(
                json.dumps(
                    {
                        "event": "journey_gat_target_mode_shadow",
                        "status": "logged",
                        "pricing_kind": "heuristic",
                        "candidate_journeys": 1,
                        "decision_samples": [
                            {
                                "candidate_id": "online-a",
                                "decision": "DELAY_QUEUE",
                                "task_set": [1, 2],
                                "signature": [[[1, 2], ["0->1:a", "1->2:b", "2->0:c"], 0.0]],
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            summary = audit_safe_source_online_coverage(
                safe_source=safe_source,
                decision_records=decision_records,
                shadow_log_dir=log_dir,
                output_dir=output_dir,
                report=report,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["coverage_gate_pass"])
            self.assertEqual(summary["exact_safe_id_overlap_count"], 0)
            self.assertEqual(summary["online_sampled_candidate_journeys"], 1)
            self.assertTrue(summary["online_sample_coverage_complete"])
            self.assertEqual(summary["task_set_overlap"]["overlap_key_count"], 1)
            self.assertEqual(summary["task_set_overlap"]["online_candidate_hit_count"], 1)
            self.assertEqual(summary["task_set_overlap"]["offline_conflict_key_count"], 1)
            self.assertEqual(
                summary["task_set_overlap"]["online_conflict_candidate_hit_count"],
                1,
            )
            self.assertTrue(report.exists())
            self.assertTrue((output_dir / "summary.json").exists())


if __name__ == "__main__":
    unittest.main()

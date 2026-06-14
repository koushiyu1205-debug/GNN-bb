from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.build_cbf_family_capture_worklist import build_worklist


def _dataset_row(*, instance: str, task_count: int, family: str) -> dict[str, object]:
    return {
        "schema_version": "cbf_gate_dataset_row_v1",
        "diagnostic_only": True,
        "certificate_capable": False,
        "official_bound_effect": False,
        "instance": instance,
        "source_file": f"BPC_future/logical_graph/tasks_020/{family}/{instance}.json",
        "task_count": task_count,
        "label_cbf_feasible": 0,
    }


def _family_result(
    *,
    task_count: int,
    family: str,
    status: str,
    row_count: int,
    ready: bool = False,
) -> dict[str, object]:
    return {
        "task_count": task_count,
        "family": family,
        "status": status,
        "reason": "test",
        "row_count": row_count,
        "label_counts": {"0": row_count},
        "family_gate_candidate_ready": ready,
        "fold_summary": {
            "evaluated_count": 0,
            "false_positive_fold_count": 0,
            "productive_fold_count": 0,
        },
    }


class CBFFamilyCaptureWorklistTests(unittest.TestCase):
    def test_worklist_skips_small_and_ready_families(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            dataset = tmp / "rows.jsonl"
            dataset.write_text(
                json.dumps(_dataset_row(instance="random_inst_existing", task_count=20, family="random-wave"))
                + "\n",
                encoding="utf-8",
            )
            audit = tmp / "family_summary.json"
            audit.write_text(
                json.dumps(
                    {
                        "family_results": [
                            _family_result(task_count=10, family="moon_trek_tasks10", status="guarded_abstain_below_min_task_count", row_count=4),
                            _family_result(task_count=20, family="greedy-anchor", status="family_gate_candidate_ready", row_count=40, ready=True),
                            _family_result(task_count=20, family="random-wave", status="insufficient_family_rows", row_count=3),
                        ]
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            tasks_root = tmp / "tasks_020"
            for name in ("random_inst_01", "random_inst_02"):
                path = tasks_root / "random-wave" / "apollo15_20km" / f"{name}_logical_graph.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}", encoding="utf-8")

            summary = build_worklist(
                dataset_path=dataset,
                family_audit_path=audit,
                tasks_root=tasks_root,
                output_dir=tmp / "out",
                report=tmp / "report.md",
                min_family_rows=10,
                max_instances_per_family=2,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["work_item_count"], 1)
            item = summary["work_items"][0]
            self.assertEqual(item["family"], "random-wave")
            self.assertEqual(item["recommended_action"], "capture_family_context_rows")
            self.assertEqual(item["selected_instance_count"], 2)
            self.assertEqual(summary["command_count"], 1)
            self.assertIn("journey_counterfactual_replay_capture_enabled=true", summary["commands"][0]["command"])
            self.assertNotIn("moon_trek_tasks10", json.dumps(summary["work_items"]))
            self.assertNotIn("family_gate_candidate_ready", json.dumps(summary["work_items"]))

    def test_worklist_marks_unmapped_family_without_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            dataset = tmp / "rows.jsonl"
            dataset.write_text("", encoding="utf-8")
            audit = tmp / "family_summary.json"
            audit.write_text(
                json.dumps(
                    {
                        "family_results": [
                            _family_result(task_count=20, family="moon_trek_tasks20", status="insufficient_family_rows", row_count=3),
                        ]
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            tasks_root = tmp / "tasks_020"
            tasks_root.mkdir()

            summary = build_worklist(
                dataset_path=dataset,
                family_audit_path=audit,
                tasks_root=tasks_root,
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["command_count"], 0)
            self.assertEqual(summary["work_items"][0]["recommended_action"], "recover_family_mapping_before_capture")


if __name__ == "__main__":
    unittest.main()

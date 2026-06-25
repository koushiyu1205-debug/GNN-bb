from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_journey_tail_minfill_profile_runbook import build_profile_runbook


class JourneyTailMinfillProfileRunbookTests(unittest.TestCase):
    def test_profile_runbook_excludes_done_and_prioritizes_positive_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "tasks_020"
            positive_done = self._touch_instance(
                root,
                "greedy-anchor",
                "apollo15_20km",
                "apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
            )
            near_positive = self._touch_instance(
                root,
                "greedy-anchor",
                "apollo15_20km",
                "apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61820_logical_graph.json",
            )
            far_family = self._touch_instance(
                root,
                "sector-wave",
                "apollo15_20km",
                "apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
            )
            training_dir = tmp_path / "training"
            training_dir.mkdir()
            training_rows = [
                {
                    "instance": str(positive_done),
                    "labels": {"y_strict_positive": 1.0},
                },
                {
                    "instance": str(far_family),
                    "labels": {"y_hard_negative": 1.0},
                },
            ]
            (training_dir / "summary.json").write_text(
                json.dumps({"training_rows": training_rows}, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (training_dir / "tail_minfill_training_rows.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps(row, sort_keys=True)
                        for row in training_rows
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            exclude = tmp_path / "exclude" / "summary.json"
            exclude.parent.mkdir()
            exclude.write_text(
                json.dumps({"training_rows": [{"instance": str(positive_done)}]}, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )

            summary = build_profile_runbook(
                instances_root=root,
                training_rows=[training_dir],
                exclude_from=[exclude],
                output_dir=tmp_path / "out",
                report=tmp_path / "report.md",
                limit=2,
                python="/usr/bin/python3",
            )

            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["production_ready"])
            self.assertEqual(summary["raw_instance_count"], 3)
            self.assertEqual(summary["excluded_instance_count"], 1)
            self.assertEqual(summary["positive_template_count"], 1)
            self.assertEqual(summary["negative_template_count"], 1)
            self.assertEqual(summary["entry_count"], 2)
            self.assertEqual(summary["entries"][0]["instance"], str(near_positive))
            self.assertIn("same_positive_family", summary["entries"][0]["priority_reason"])
            self.assertNotIn(str(positive_done), (tmp_path / "out" / "commands.sh").read_text())
            self.assertIn(
                "journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False",
                summary["entries"][0]["command"],
            )
            self.assertTrue((tmp_path / "out" / "summary.json").exists())
            self.assertIn("entry_count = 2", (tmp_path / "report.md").read_text())

    @staticmethod
    def _touch_instance(root: Path, family: str, scenario: str, filename: str) -> Path:
        path = root / family / scenario / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
        return path


if __name__ == "__main__":
    unittest.main()

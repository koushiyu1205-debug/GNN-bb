from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.audit_journey_tail_action_counterfactual_delta import (
    audit_tail_action_counterfactual_delta,
)


class JourneyTailActionCounterfactualDeltaTests(unittest.TestCase):
    def _write_csv(self, path: Path, rows: list[dict[str, object]]) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["instance", "status", "wall_time"])
            writer.writeheader()
            writer.writerows(rows)

    def _write_tail_row(
        self,
        directory: Path,
        *,
        instance: str,
        node_id: int,
        depth: int,
        pair: tuple[int, int],
        pricing: int,
        negative: int,
        retries: int,
        no_column_chain: int,
    ) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        row = {
            "source_type": "tail_action_proof_cost",
            "log_file": f"/tmp/probe/logs/{instance}.jsonl",
            "node_id": node_id,
            "depth": depth,
            "task_i": pair[0],
            "task_j": pair[1],
            "raw_source": {
                "child_subtree_pricing_event_count": pricing,
                "child_subtree_negative_pricing_event_count": negative,
                "child_subtree_completion_retry_count": retries,
                "child_subtree_no_column_early_branch_trigger_count": no_column_chain,
            },
        }
        (directory / "tail_impact_training_rows.jsonl").write_text(
            json.dumps(row, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def test_labels_local_improvement_without_whole_run_improvement_as_hard_negative(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instance = "BPC_future/logical_graph/tasks_020/random-wave/demo.json"
            baseline_tail = tmp_path / "baseline_tail"
            alternative_tail = tmp_path / "alternative_tail"
            self._write_tail_row(
                baseline_tail,
                instance=instance,
                node_id=1,
                depth=1,
                pair=(4, 7),
                pricing=100,
                negative=30,
                retries=20,
                no_column_chain=5,
            )
            self._write_tail_row(
                alternative_tail,
                instance=instance,
                node_id=1,
                depth=1,
                pair=(1, 10),
                pricing=20,
                negative=10,
                retries=2,
                no_column_chain=0,
            )
            baseline_csv = tmp_path / "baseline.csv"
            alternative_csv = tmp_path / "alternative.csv"
            self._write_csv(
                baseline_csv,
                [{"instance": instance, "status": "EXTERNAL_TIME_LIMIT", "wall_time": 220.0}],
            )
            self._write_csv(
                alternative_csv,
                [{"instance": instance, "status": "EXTERNAL_TIME_LIMIT", "wall_time": 220.0}],
            )
            runbook = {
                "entries": [
                    {
                        "source_type": "tail_action_alt_pair",
                        "experiment": "demo_alt",
                        "instance": instance,
                        "source_node_id": 1,
                        "source_depth": 1,
                        "source_original_forced_pair": [4, 7],
                        "forced_pair": [1, 10],
                        "command": ["python", "x", "--results-csv", str(alternative_csv)],
                    }
                ]
            }
            runbook_path = tmp_path / "runbook.json"
            runbook_path.write_text(json.dumps(runbook, sort_keys=True), encoding="utf-8")

            summary = audit_tail_action_counterfactual_delta(
                runbook_path,
                [baseline_tail],
                [alternative_tail],
                [baseline_csv],
                tmp_path / "out",
                tmp_path / "report.md",
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["certificate_effect"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertEqual(summary["matched_counterfactual_count"], 1)
            self.assertEqual(summary["local_tail_improved_count"], 1)
            self.assertEqual(summary["whole_run_improved_count"], 0)
            self.assertEqual(summary["local_improved_but_whole_run_not_count"], 1)
            self.assertEqual(summary["right_censored_counterfactual_count"], 1)
            self.assertFalse(summary["whole_run_training_ready"])
            self.assertTrue(summary["hard_negative_catalog_ready"])
            row = summary["rows"][0]
            self.assertEqual(row["labels"]["y_local_tail_improved"], 1.0)
            self.assertEqual(row["labels"]["y_whole_run_improved"], 0.0)
            self.assertEqual(row["labels"]["y_local_improved_but_whole_run_not"], 1.0)
            self.assertEqual(row["labels"]["y_right_censored_counterfactual"], 1.0)
            self.assertLess(row["deltas"]["local_tail_cost_delta"], 0)
            self.assertTrue((tmp_path / "out" / "tail_action_counterfactual_delta_rows.jsonl").exists())
            self.assertTrue((tmp_path / "out" / "summary.json").exists())
            self.assertIn("certificate_effect = false", (tmp_path / "report.md").read_text(encoding="utf-8"))

    def test_labels_timeout_resolved_as_whole_run_positive(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instance = "BPC_future/logical_graph/tasks_020/sector-wave/demo.json"
            baseline_tail = tmp_path / "baseline_tail"
            alternative_tail = tmp_path / "alternative_tail"
            self._write_tail_row(
                baseline_tail,
                instance=instance,
                node_id=2,
                depth=2,
                pair=(3, 8),
                pricing=80,
                negative=30,
                retries=12,
                no_column_chain=3,
            )
            self._write_tail_row(
                alternative_tail,
                instance=instance,
                node_id=2,
                depth=2,
                pair=(6, 11),
                pricing=12,
                negative=4,
                retries=1,
                no_column_chain=0,
            )
            baseline_csv = tmp_path / "baseline.csv"
            alternative_csv = tmp_path / "alternative.csv"
            self._write_csv(
                baseline_csv,
                [{"instance": instance, "status": "EXTERNAL_TIME_LIMIT", "wall_time": 220.0}],
            )
            self._write_csv(
                alternative_csv,
                [{"instance": instance, "status": "OPTIMAL", "wall_time": 99.0}],
            )
            runbook = {
                "entries": [
                    {
                        "source_type": "tail_action_alt_pair",
                        "experiment": "resolved_alt",
                        "instance": instance,
                        "source_node_id": 2,
                        "source_depth": 2,
                        "source_original_forced_pair": [3, 8],
                        "forced_pair": [6, 11],
                        "command": ["python", "x", "--results-csv", str(alternative_csv)],
                    }
                ]
            }
            runbook_path = tmp_path / "runbook.json"
            runbook_path.write_text(json.dumps(runbook, sort_keys=True), encoding="utf-8")

            summary = audit_tail_action_counterfactual_delta(
                runbook_path,
                [baseline_tail],
                [alternative_tail],
                [baseline_csv],
                tmp_path / "out",
                tmp_path / "report.md",
            )

            self.assertEqual(summary["matched_counterfactual_count"], 1)
            self.assertEqual(summary["local_tail_improved_count"], 1)
            self.assertEqual(summary["whole_run_improved_count"], 1)
            self.assertEqual(summary["local_improved_but_whole_run_not_count"], 0)
            self.assertEqual(summary["right_censored_counterfactual_count"], 0)
            self.assertTrue(summary["whole_run_training_ready"])
            row = summary["rows"][0]
            self.assertEqual(row["labels"]["y_timeout_resolved"], 1.0)
            self.assertEqual(row["labels"]["y_whole_run_improved"], 1.0)
            self.assertEqual(row["alternative_status"], "OPTIMAL")


if __name__ == "__main__":
    unittest.main()

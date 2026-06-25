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
        fieldnames = ["instance", "status", "wall_time"]
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(str(key))
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
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
        log_file: str | None = None,
    ) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        row = {
            "source_type": "tail_action_proof_cost",
            "log_file": log_file or f"/tmp/probe/logs/{instance}.jsonl",
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

    def _write_solver_log(
        self,
        path: Path,
        *,
        completion_retry_count: int,
        retry_time: float,
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        rows: list[dict[str, object]] = []
        for index in range(completion_retry_count):
            rows.append(
                {
                    "event": "journey_exact_pricing_completion_bound_retry",
                    "node_id": index,
                    "time": float(index),
                    "trigger": "profile_exhausted_no_column",
                }
            )
            rows.append(
                {
                    "event": "journey_pricing",
                    "pricing_kind": "exact_completion_bound_retry",
                    "node_id": index,
                    "profile_generation_time": retry_time,
                    "profile_dp_time": retry_time / 2.0,
                    "bound_build_time": retry_time / 4.0,
                    "two_cycle_build_time": retry_time / 4.0,
                    "generated_sequences": 100 + index,
                    "evaluated_timed_trips": 50 + index,
                }
            )
        path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
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
            self.assertEqual(
                summary["counterfactual_label_type_counts"],
                {"local_only_hard_negative": 1},
            )
            self.assertFalse(summary["whole_run_training_ready"])
            self.assertTrue(summary["hard_negative_catalog_ready"])
            row = summary["rows"][0]
            self.assertEqual(row["counterfactual_label_type"], "local_only_hard_negative")
            self.assertEqual(row["labels"]["y_local_tail_improved"], 1.0)
            self.assertEqual(row["labels"]["y_whole_run_improved"], 0.0)
            self.assertEqual(row["labels"]["y_budget_dominant_improvement"], 0.0)
            self.assertEqual(row["labels"]["y_local_improved_but_whole_run_not"], 1.0)
            self.assertEqual(row["labels"]["y_right_censored_counterfactual"], 1.0)
            self.assertLess(row["deltas"]["local_tail_cost_delta"], 0)
            self.assertIsNone(row["deltas"]["exact_pricing_calls_delta"])
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
            self.assertEqual(row["labels"]["y_budget_dominant_improvement"], 0.0)
            self.assertEqual(row["alternative_status"], "OPTIMAL")

    def test_marks_budget_dominant_improvement_without_promoting_whole_run_positive(self):
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
                pricing=90,
                negative=20,
                retries=10,
                no_column_chain=2,
            )
            baseline_csv = tmp_path / "baseline.csv"
            alternative_csv = tmp_path / "alternative.csv"
            self._write_csv(
                baseline_csv,
                [
                    {
                        "instance": instance,
                        "status": "EXTERNAL_TIME_LIMIT",
                        "wall_time": 220.0,
                        "pricing_calls": 100,
                        "exact_pricing_calls": 80,
                        "node_count": 9,
                        "gap": 0.42,
                    }
                ],
            )
            self._write_csv(
                alternative_csv,
                [
                    {
                        "instance": instance,
                        "status": "EXTERNAL_TIME_LIMIT",
                        "wall_time": 220.0,
                        "pricing_calls": 72,
                        "exact_pricing_calls": 51,
                        "node_count": 8,
                        "gap": 0.41,
                    }
                ],
            )
            runbook = {
                "entries": [
                    {
                        "source_type": "tail_action_alt_pair",
                        "experiment": "budget_dominant_alt",
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

            self.assertEqual(summary["matched_counterfactual_count"], 1)
            self.assertEqual(summary["whole_run_improved_count"], 0)
            self.assertEqual(summary["budget_dominant_improvement_count"], 1)
            self.assertEqual(
                summary["counterfactual_label_type_counts"],
                {"budget_dominant_improvement": 1},
            )
            self.assertTrue(summary["budget_dominant_catalog_ready"])
            self.assertFalse(summary["whole_run_training_ready"])
            row = summary["rows"][0]
            self.assertEqual(row["labels"]["y_whole_run_improved"], 0.0)
            self.assertEqual(row["counterfactual_label_type"], "budget_dominant_improvement")
            self.assertEqual(row["labels"]["y_budget_dominant_improvement"], 1.0)
            self.assertEqual(row["labels"]["y_right_censored_counterfactual"], 1.0)
            self.assertEqual(row["deltas"]["pricing_calls_delta"], -28.0)
            self.assertEqual(row["deltas"]["exact_pricing_calls_delta"], -29.0)
            self.assertEqual(row["deltas"]["node_count_delta"], -1.0)
            self.assertEqual(row["deltas"]["gap_delta"], -0.01)
            self.assertFalse(row["proof_work_metrics_available"])
            self.assertTrue(row["retry_payback_absent"])

    def test_budget_dominant_rejected_when_completion_retry_payback_is_observed(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instance = "BPC_future/logical_graph/tasks_020/random-wave/demo.json"
            baseline_log = tmp_path / "baseline_logs" / f"{instance}.jsonl"
            alternative_log = tmp_path / "alternative_logs" / f"{instance}.jsonl"
            self._write_solver_log(
                baseline_log,
                completion_retry_count=2,
                retry_time=1.0,
            )
            self._write_solver_log(
                alternative_log,
                completion_retry_count=5,
                retry_time=2.0,
            )
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
                log_file=str(baseline_log),
            )
            self._write_tail_row(
                alternative_tail,
                instance=instance,
                node_id=1,
                depth=1,
                pair=(1, 10),
                pricing=80,
                negative=20,
                retries=10,
                no_column_chain=2,
                log_file=str(alternative_log),
            )
            baseline_csv = tmp_path / "baseline.csv"
            alternative_csv = tmp_path / "alternative.csv"
            self._write_csv(
                baseline_csv,
                [
                    {
                        "instance": instance,
                        "status": "EXTERNAL_TIME_LIMIT",
                        "wall_time": 220.0,
                        "pricing_calls": 100,
                        "exact_pricing_calls": 80,
                        "node_count": 9,
                        "gap": 0.42,
                    }
                ],
            )
            self._write_csv(
                alternative_csv,
                [
                    {
                        "instance": instance,
                        "status": "EXTERNAL_TIME_LIMIT",
                        "wall_time": 220.0,
                        "pricing_calls": 70,
                        "exact_pricing_calls": 50,
                        "node_count": 8,
                        "gap": 0.41,
                    }
                ],
            )
            runbook = {
                "entries": [
                    {
                        "source_type": "tail_action_alt_pair",
                        "experiment": "retry_payback_alt",
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

            self.assertEqual(summary["matched_counterfactual_count"], 1)
            self.assertEqual(summary["budget_dominant_improvement_count"], 0)
            self.assertEqual(
                summary["counterfactual_label_type_counts"],
                {"local_only_hard_negative": 1},
            )
            row = summary["rows"][0]
            self.assertTrue(row["proof_work_metrics_available"])
            self.assertFalse(row["retry_payback_absent"])
            self.assertEqual(row["labels"]["y_budget_dominant_improvement"], 0.0)
            self.assertEqual(row["deltas"]["completion_retry_pricing_count_delta"], 3.0)
            self.assertGreater(row["deltas"]["completion_retry_work_time_proxy_delta"], 0.0)

    def test_rejects_duplicate_baseline_result_rows_for_same_instance(self):
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
            baseline_a = tmp_path / "baseline_a.csv"
            baseline_b = tmp_path / "baseline_b.csv"
            alternative_csv = tmp_path / "alternative.csv"
            self._write_csv(
                baseline_a,
                [{"instance": instance, "status": "EXTERNAL_TIME_LIMIT", "wall_time": 220.0}],
            )
            self._write_csv(
                baseline_b,
                [{"instance": instance, "status": "OPTIMAL", "wall_time": 180.0}],
            )
            self._write_csv(
                alternative_csv,
                [{"instance": instance, "status": "OPTIMAL", "wall_time": 99.0}],
            )
            runbook = {
                "entries": [
                    {
                        "source_type": "tail_action_alt_pair",
                        "experiment": "duplicate_baseline",
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

            with self.assertRaisesRegex(ValueError, "duplicate baseline result row"):
                audit_tail_action_counterfactual_delta(
                    runbook_path,
                    [baseline_tail],
                    [alternative_tail],
                    [baseline_a, baseline_b],
                    tmp_path / "out",
                    tmp_path / "report.md",
                )

    def test_rejects_ambiguous_tail_row_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instance = "BPC_future/logical_graph/tasks_020/sector-wave/demo.json"
            baseline_tail = tmp_path / "baseline_tail"
            baseline_tail.mkdir()
            alternative_tail = tmp_path / "alternative_tail"
            row = {
                "source_type": "tail_action_proof_cost",
                "log_file": f"/tmp/probe/logs/{instance}.jsonl",
                "node_id": 2,
                "depth": 2,
                "task_i": 3,
                "task_j": 8,
                "raw_source": {
                    "child_subtree_pricing_event_count": 80,
                    "child_subtree_negative_pricing_event_count": 30,
                    "child_subtree_completion_retry_count": 12,
                    "child_subtree_no_column_early_branch_trigger_count": 3,
                },
            }
            duplicate = dict(row)
            duplicate["raw_source"] = dict(row["raw_source"], child_subtree_pricing_event_count=90)
            (baseline_tail / "tail_impact_training_rows.jsonl").write_text(
                json.dumps(row, sort_keys=True)
                + "\n"
                + json.dumps(duplicate, sort_keys=True)
                + "\n",
                encoding="utf-8",
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
                        "experiment": "ambiguous_tail",
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

            with self.assertRaisesRegex(ValueError, "ambiguous tail-action row match"):
                audit_tail_action_counterfactual_delta(
                    runbook_path,
                    [baseline_tail],
                    [alternative_tail],
                    [baseline_csv],
                    tmp_path / "out",
                    tmp_path / "report.md",
                )


if __name__ == "__main__":
    unittest.main()

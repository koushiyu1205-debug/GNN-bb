from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.audit_journey_branch_counterfactual_delta import build_counterfactual_delta


class JourneyBranchCounterfactualDeltaAuditTests(unittest.TestCase):
    def test_build_counterfactual_delta_labels_wall_improvement_and_regression(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runbook_path = tmp_path / "runbook.json"
            fast_result = tmp_path / "fast.csv"
            slow_result = tmp_path / "slow.csv"
            entries = [
                {
                    "experiment": "fast_alt",
                    "instance": "BPC_future/logical_graph/tasks_020/demo.json",
                    "source_node_id": 0,
                    "source_depth": 0,
                    "source_selected_pair": [1, 2],
                    "forced_pair": [1, 3],
                    "command": ["runner", "--results-csv", str(fast_result)],
                },
                {
                    "experiment": "slow_alt",
                    "instance": "BPC_future/logical_graph/tasks_020/demo.json",
                    "source_node_id": 0,
                    "source_depth": 0,
                    "source_selected_pair": [1, 2],
                    "forced_pair": [2, 3],
                    "command": ["runner", "--results-csv", str(slow_result)],
                },
            ]
            runbook_path.write_text(json.dumps({"entries": entries}, sort_keys=True) + "\n", encoding="utf-8")
            baseline_result = tmp_path / "baseline.csv"
            self._write_results(
                baseline_result,
                [
                    {
                        "instance": "BPC_future/logical_graph/tasks_020/demo.json",
                        "status": "OPTIMAL",
                        "wall_time": "40.0",
                        "solving_time": "38.0",
                        "node_count": "3",
                        "pricing_calls": "30",
                        "exact_pricing_calls": "10",
                    }
                ],
            )
            self._write_results(
                fast_result,
                [
                    {
                        "instance": "BPC_future/logical_graph/tasks_020/demo.json",
                        "status": "OPTIMAL",
                        "wall_time": "35.0",
                        "solving_time": "33.0",
                        "node_count": "3",
                        "pricing_calls": "29",
                        "exact_pricing_calls": "9",
                    }
                ],
            )
            self._write_results(
                slow_result,
                [
                    {
                        "instance": "BPC_future/logical_graph/tasks_020/demo.json",
                        "status": "OPTIMAL",
                        "wall_time": "45.0",
                        "solving_time": "43.0",
                        "node_count": "5",
                        "pricing_calls": "40",
                        "exact_pricing_calls": "14",
                    }
                ],
            )
            baseline_dir = tmp_path / "baseline_audit"
            alt_dir = tmp_path / "alt_audit"
            baseline_dir.mkdir()
            alt_dir.mkdir()
            baseline_row = self._branch_row(task_i=1, task_j=2, forced_pair=None, matched=None)
            fast_row = self._branch_row(task_i=1, task_j=3, forced_pair=[1, 3], matched=True)
            slow_row = self._branch_row(task_i=2, task_j=3, forced_pair=[2, 3], matched=True)
            (baseline_dir / "branch_impact_rows.jsonl").write_text(
                json.dumps(baseline_row, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (alt_dir / "branch_impact_rows.jsonl").write_text(
                json.dumps(fast_row, sort_keys=True) + "\n" + json.dumps(slow_row, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            summary = build_counterfactual_delta(
                runbook_path,
                [baseline_result],
                [baseline_dir],
                [alt_dir],
                tmp_path / "out",
                tmp_path / "report.md",
                min_wall_improvement=1.0,
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertEqual(summary["matched_counterfactual_count"], 2)
            self.assertEqual(summary["forced_pair_matched_count"], 2)
            self.assertTrue(summary["minimal_counterfactual_signal_ready"])
            self.assertFalse(summary["strict_counterfactual_training_ready"])
            self.assertFalse(summary["counterfactual_training_ready"])
            self.assertEqual(summary["strong_positive_count"], 1)
            self.assertEqual(summary["strong_positive_context_count"], 1)
            self.assertEqual(summary["positive_holdout_context_count"], 0)
            by_experiment = {row["experiment"]: row for row in summary["rows"]}
            self.assertEqual(by_experiment["fast_alt"]["deltas"]["wall_time_delta"], -5.0)
            self.assertEqual(by_experiment["fast_alt"]["counterfactual_label_type"], "strong_positive")
            self.assertEqual(by_experiment["fast_alt"]["labels"]["y_counterfactual_wall_improved"], 1.0)
            self.assertEqual(
                by_experiment["fast_alt"]["labels"]["y_counterfactual_proof_cost_improved"],
                1.0,
            )
            self.assertTrue(by_experiment["fast_alt"]["usable_for_counterfactual_training"])
            self.assertEqual(by_experiment["slow_alt"]["deltas"]["wall_time_delta"], 5.0)
            self.assertEqual(by_experiment["slow_alt"]["counterfactual_label_type"], "regression")
            self.assertEqual(by_experiment["slow_alt"]["labels"]["y_counterfactual_regression"], 1.0)
            self.assertTrue((tmp_path / "out" / "summary.json").exists())
            self.assertTrue((tmp_path / "out" / "branch_counterfactual_delta_rows.jsonl").exists())
            self.assertIn("official_bound_effect = false", (tmp_path / "report.md").read_text(encoding="utf-8"))

    def test_timeout_vs_timeout_only_sets_proxy_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runbook_path = tmp_path / "runbook.json"
            alt_result = tmp_path / "alt.csv"
            runbook_path.write_text(
                json.dumps(
                    {
                        "entries": [
                            {
                                "experiment": "timeout_alt",
                                "instance": "BPC_future/logical_graph/tasks_020/demo.json",
                                "source_node_id": 0,
                                "source_depth": 0,
                                "source_selected_pair": [1, 2],
                                "forced_pair": [1, 3],
                                "command": ["runner", "--results-csv", str(alt_result)],
                            }
                        ]
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            baseline_result = tmp_path / "baseline.csv"
            self._write_results(
                baseline_result,
                [
                    {
                        "instance": "BPC_future/logical_graph/tasks_020/demo.json",
                        "status": "EXTERNAL_TIME_LIMIT",
                        "wall_time": "220.0",
                        "solving_time": "",
                        "node_count": "",
                        "pricing_calls": "",
                        "exact_pricing_calls": "",
                    }
                ],
            )
            self._write_results(
                alt_result,
                [
                    {
                        "instance": "BPC_future/logical_graph/tasks_020/demo.json",
                        "status": "EXTERNAL_TIME_LIMIT",
                        "wall_time": "220.0",
                        "solving_time": "",
                        "node_count": "",
                        "pricing_calls": "",
                        "exact_pricing_calls": "",
                    }
                ],
            )
            baseline_dir = tmp_path / "baseline_audit"
            alt_dir = tmp_path / "alt_audit"
            baseline_dir.mkdir()
            alt_dir.mkdir()
            baseline_row = self._branch_row(
                task_i=1,
                task_j=2,
                forced_pair=None,
                matched=None,
                child_negative_pricing_events=4.0,
                child_completion_bound_retries=2.0,
            )
            alt_row = self._branch_row(
                task_i=1,
                task_j=3,
                forced_pair=[1, 3],
                matched=True,
                child_negative_pricing_events=3.0,
                child_completion_bound_retries=1.0,
            )
            (baseline_dir / "branch_impact_rows.jsonl").write_text(
                json.dumps(baseline_row, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (alt_dir / "branch_impact_rows.jsonl").write_text(
                json.dumps(alt_row, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            summary = build_counterfactual_delta(
                runbook_path,
                [baseline_result],
                [baseline_dir],
                [alt_dir],
                tmp_path / "out",
                tmp_path / "report.md",
            )

            self.assertFalse(summary["counterfactual_training_ready"])
            self.assertEqual(summary["right_censored_counterfactual_count"], 1)
            self.assertEqual(
                summary["counterfactual_label_type_counts"],
                {"local_only_hard_negative": 1},
            )
            self.assertEqual(summary["usable_counterfactual_training_count"], 0)
            row = summary["rows"][0]
            self.assertEqual(row["counterfactual_label_type"], "local_only_hard_negative")
            self.assertTrue(row["right_censored_counterfactual"])
            self.assertFalse(row["usable_for_counterfactual_training"])
            self.assertEqual(row["labels"]["y_counterfactual_proof_cost_improved"], 0.0)
            self.assertEqual(row["labels"]["y_counterfactual_proof_cost_proxy_improved"], 1.0)
            self.assertEqual(
                row["labels"]["y_counterfactual_local_improved_but_whole_run_not"],
                1.0,
            )
            self.assertEqual(row["labels"]["y_counterfactual_right_censored"], 1.0)

    def test_proxy_runbook_can_infer_unique_baseline_pair(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runbook_path = tmp_path / "proxy_runbook_summary.json"
            alt_result = tmp_path / "alt.csv"
            instance = "BPC_future/logical_graph/tasks_020/demo.json"
            runbook_path.write_text(
                json.dumps(
                    {
                        "entries": [
                            {
                                "experiment": "proxy_alt",
                                "instance": instance,
                                "source_node_id": 0,
                                "source_depth": 0,
                                "forced_pair": [1, 3],
                                "command": ["runner", "--results-csv", str(alt_result)],
                            }
                        ]
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            baseline_result = tmp_path / "baseline.csv"
            self._write_results(
                baseline_result,
                [
                    {
                        "instance": instance,
                        "status": "TIME_LIMIT",
                        "wall_time": "220.0",
                        "solving_time": "218.0",
                        "node_count": "9",
                        "pricing_calls": "90",
                        "exact_pricing_calls": "40",
                    }
                ],
            )
            self._write_results(
                alt_result,
                [
                    {
                        "instance": instance,
                        "status": "OPTIMAL",
                        "wall_time": "90.0",
                        "solving_time": "88.0",
                        "node_count": "3",
                        "pricing_calls": "30",
                        "exact_pricing_calls": "10",
                    }
                ],
            )
            baseline_dir = tmp_path / "baseline_audit"
            alt_dir = tmp_path / "alt_audit"
            baseline_dir.mkdir()
            alt_dir.mkdir()
            (baseline_dir / "branch_impact_rows.jsonl").write_text(
                json.dumps(
                    self._branch_row(task_i=1, task_j=2, forced_pair=None, matched=None),
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            (alt_dir / "branch_impact_rows.jsonl").write_text(
                json.dumps(
                    self._branch_row(task_i=1, task_j=3, forced_pair=[1, 3], matched=True),
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = build_counterfactual_delta(
                runbook_path,
                [baseline_result],
                [baseline_dir],
                [alt_dir],
                tmp_path / "out",
                tmp_path / "report.md",
            )

            self.assertEqual(summary["matched_counterfactual_count"], 1)
            self.assertEqual(summary["forced_pair_matched_count"], 1)
            self.assertEqual(summary["strong_positive_count"], 1)
            row = summary["rows"][0]
            self.assertEqual(row["baseline_pair"], [1, 2])
            self.assertEqual(row["alternative_pair"], [1, 3])
            self.assertEqual(row["counterfactual_label_type"], "strong_positive")

    def test_timeout_vs_timeout_budget_dominant_is_not_strong_positive(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runbook_path = tmp_path / "runbook.json"
            alt_result = tmp_path / "alt.csv"
            instance = "BPC_future/logical_graph/tasks_020/demo.json"
            runbook_path.write_text(
                json.dumps(
                    {
                        "entries": [
                            {
                                "experiment": "budget_dominant_alt",
                                "instance": instance,
                                "source_node_id": 0,
                                "source_depth": 0,
                                "source_selected_pair": [1, 2],
                                "forced_pair": [1, 3],
                                "command": ["runner", "--results-csv", str(alt_result)],
                            }
                        ]
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            baseline_result = tmp_path / "baseline.csv"
            self._write_results(
                baseline_result,
                [
                    {
                        "instance": instance,
                        "status": "TIME_LIMIT",
                        "wall_time": "220.0",
                        "solving_time": "218.0",
                        "node_count": "9",
                        "pricing_calls": "90",
                        "exact_pricing_calls": "40",
                        "gap": "0.030",
                    }
                ],
            )
            self._write_results(
                alt_result,
                [
                    {
                        "instance": instance,
                        "status": "TIME_LIMIT",
                        "wall_time": "220.0",
                        "solving_time": "215.0",
                        "node_count": "8",
                        "pricing_calls": "70",
                        "exact_pricing_calls": "30",
                        "gap": "0.020",
                    }
                ],
            )
            baseline_dir = tmp_path / "baseline_audit"
            alt_dir = tmp_path / "alt_audit"
            baseline_dir.mkdir()
            alt_dir.mkdir()
            (baseline_dir / "branch_impact_rows.jsonl").write_text(
                json.dumps(
                    self._branch_row(task_i=1, task_j=2, forced_pair=None, matched=None),
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            (alt_dir / "branch_impact_rows.jsonl").write_text(
                json.dumps(
                    self._branch_row(task_i=1, task_j=3, forced_pair=[1, 3], matched=True),
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = build_counterfactual_delta(
                runbook_path,
                [baseline_result],
                [baseline_dir],
                [alt_dir],
                tmp_path / "out",
                tmp_path / "report.md",
            )

            self.assertFalse(summary["counterfactual_training_ready"])
            self.assertEqual(summary["budget_dominant_improvement_count"], 1)
            self.assertEqual(
                summary["counterfactual_label_type_counts"],
                {"budget_dominant_improvement": 1},
            )
            row = summary["rows"][0]
            self.assertEqual(row["counterfactual_label_type"], "budget_dominant_improvement")
            self.assertEqual(
                row["labels"]["y_counterfactual_budget_dominant_improvement"],
                1.0,
            )
            self.assertEqual(row["labels"]["y_counterfactual_wall_improved"], 0.0)
            self.assertEqual(row["labels"]["y_counterfactual_timeout_resolved"], 0.0)
            self.assertEqual(row["labels"]["y_counterfactual_right_censored"], 1.0)
            self.assertEqual(row["labels"]["y_counterfactual_local_improved_but_whole_run_not"], 0.0)
            self.assertEqual(row["deltas"]["exact_pricing_calls_delta"], -10.0)
            self.assertEqual(row["deltas"]["gap_delta"], -0.01)

    def test_timeout_regression_with_missing_solver_metrics_does_not_set_proxy_positive(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runbook_path = tmp_path / "runbook.json"
            alt_result = tmp_path / "alt.csv"
            instance = "BPC_future/logical_graph/tasks_020/demo.json"
            runbook_path.write_text(
                json.dumps(
                    {
                        "entries": [
                            {
                                "experiment": "external_timeout_regression",
                                "instance": instance,
                                "source_node_id": 0,
                                "source_depth": 0,
                                "source_selected_pair": [1, 2],
                                "forced_pair": [1, 3],
                                "command": ["runner", "--results-csv", str(alt_result)],
                            }
                        ]
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            baseline_result = tmp_path / "baseline.csv"
            self._write_results(
                baseline_result,
                [
                    {
                        "instance": instance,
                        "status": "OPTIMAL",
                        "wall_time": "210.0",
                        "solving_time": "205.0",
                        "node_count": "7",
                        "pricing_calls": "75",
                        "exact_pricing_calls": "39",
                    }
                ],
            )
            self._write_results(
                alt_result,
                [
                    {
                        "instance": instance,
                        "status": "EXTERNAL_TIME_LIMIT",
                        "wall_time": "230.0",
                        "solving_time": "",
                        "node_count": "",
                        "pricing_calls": "",
                        "exact_pricing_calls": "",
                    }
                ],
            )
            baseline_dir = tmp_path / "baseline_audit"
            alt_dir = tmp_path / "alt_audit"
            baseline_dir.mkdir()
            alt_dir.mkdir()
            baseline_row = self._branch_row(
                task_i=1,
                task_j=2,
                forced_pair=None,
                matched=None,
                child_negative_pricing_events=8.0,
                child_completion_bound_retries=6.0,
            )
            alt_row = self._branch_row(
                task_i=1,
                task_j=3,
                forced_pair=[1, 3],
                matched=True,
                child_negative_pricing_events=2.0,
                child_completion_bound_retries=1.0,
            )
            (baseline_dir / "branch_impact_rows.jsonl").write_text(
                json.dumps(baseline_row, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (alt_dir / "branch_impact_rows.jsonl").write_text(
                json.dumps(alt_row, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            summary = build_counterfactual_delta(
                runbook_path,
                [baseline_result],
                [baseline_dir],
                [alt_dir],
                tmp_path / "out",
                tmp_path / "report.md",
            )

            self.assertEqual(summary["timeout_regression_count"], 1)
            self.assertEqual(
                summary["label_positive_counts"],
                {
                    "y_counterfactual_regression": 1,
                    "y_counterfactual_timeout_regression": 1,
                },
            )
            row = summary["rows"][0]
            self.assertEqual(row["deltas"]["exact_pricing_calls_delta"], None)
            self.assertEqual(row["deltas"]["node_count_delta"], None)
            self.assertEqual(row["labels"]["y_counterfactual_proof_cost_proxy_improved"], 0.0)
            self.assertEqual(row["labels"]["y_counterfactual_regression"], 1.0)

    def test_rejects_duplicate_baseline_result_rows_for_same_instance(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runbook_path, baseline_result, alt_result, baseline_dir, alt_dir = (
                self._minimal_counterfactual_fixture(tmp_path)
            )
            self._write_results(
                baseline_result,
                [
                    {
                        "instance": "BPC_future/logical_graph/tasks_020/demo.json",
                        "status": "OPTIMAL",
                        "wall_time": "40.0",
                        "solving_time": "38.0",
                        "node_count": "3",
                        "pricing_calls": "30",
                        "exact_pricing_calls": "10",
                    },
                    {
                        "instance": "BPC_future/logical_graph/tasks_020/demo.json",
                        "status": "TIME_LIMIT",
                        "wall_time": "220.0",
                        "solving_time": "",
                        "node_count": "",
                        "pricing_calls": "",
                        "exact_pricing_calls": "",
                    },
                ],
            )

            with self.assertRaisesRegex(ValueError, "duplicate baseline result row"):
                build_counterfactual_delta(
                    runbook_path,
                    [baseline_result],
                    [baseline_dir],
                    [alt_dir],
                    tmp_path / "out",
                    tmp_path / "report.md",
                )

    def test_rejects_ambiguous_baseline_branch_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runbook_path, baseline_result, alt_result, baseline_dir, alt_dir = (
                self._minimal_counterfactual_fixture(tmp_path)
            )
            self._write_results(
                baseline_result,
                [
                    {
                        "instance": "BPC_future/logical_graph/tasks_020/demo.json",
                        "status": "OPTIMAL",
                        "wall_time": "40.0",
                        "solving_time": "38.0",
                        "node_count": "3",
                        "pricing_calls": "30",
                        "exact_pricing_calls": "10",
                    }
                ],
            )
            row = self._branch_row(task_i=1, task_j=2, forced_pair=None, matched=None)
            duplicate = dict(row)
            duplicate["branch_labels"] = dict(row["branch_labels"], y_child_negative_pricing_events=9.0)
            (baseline_dir / "branch_impact_rows.jsonl").write_text(
                json.dumps(row, sort_keys=True)
                + "\n"
                + json.dumps(duplicate, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "ambiguous baseline branch row match"):
                build_counterfactual_delta(
                    runbook_path,
                    [baseline_result],
                    [baseline_dir],
                    [alt_dir],
                    tmp_path / "out",
                    tmp_path / "report.md",
                )

    def test_rejects_ambiguous_alternative_branch_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runbook_path, baseline_result, alt_result, baseline_dir, alt_dir = (
                self._minimal_counterfactual_fixture(tmp_path)
            )
            self._write_results(
                baseline_result,
                [
                    {
                        "instance": "BPC_future/logical_graph/tasks_020/demo.json",
                        "status": "OPTIMAL",
                        "wall_time": "40.0",
                        "solving_time": "38.0",
                        "node_count": "3",
                        "pricing_calls": "30",
                        "exact_pricing_calls": "10",
                    }
                ],
            )
            row = self._branch_row(task_i=1, task_j=3, forced_pair=[1, 3], matched=True)
            duplicate = dict(row)
            duplicate["branch_labels"] = dict(row["branch_labels"], y_child_negative_pricing_events=1.0)
            (alt_dir / "branch_impact_rows.jsonl").write_text(
                json.dumps(row, sort_keys=True)
                + "\n"
                + json.dumps(duplicate, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "ambiguous exact alternative branch row match"):
                build_counterfactual_delta(
                    runbook_path,
                    [baseline_result],
                    [baseline_dir],
                    [alt_dir],
                    tmp_path / "out",
                    tmp_path / "report.md",
                )

    @staticmethod
    def _write_results(path: Path, rows: list[dict[str, str]]) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "instance",
                    "status",
                    "wall_time",
                    "solving_time",
                    "node_count",
                    "pricing_calls",
                    "exact_pricing_calls",
                    "primal_bound",
                    "dual_bound",
                    "gap",
                ],
            )
            writer.writeheader()
            writer.writerows(rows)

    def _minimal_counterfactual_fixture(
        self,
        tmp_path: Path,
    ) -> tuple[Path, Path, Path, Path, Path]:
        runbook_path = tmp_path / "runbook.json"
        baseline_result = tmp_path / "baseline.csv"
        alt_result = tmp_path / "alt.csv"
        baseline_dir = tmp_path / "baseline_audit"
        alt_dir = tmp_path / "alt_audit"
        baseline_dir.mkdir()
        alt_dir.mkdir()
        instance = "BPC_future/logical_graph/tasks_020/demo.json"
        runbook_path.write_text(
            json.dumps(
                {
                    "entries": [
                        {
                            "experiment": "minimal_alt",
                            "instance": instance,
                            "source_node_id": 0,
                            "source_depth": 0,
                            "source_selected_pair": [1, 2],
                            "forced_pair": [1, 3],
                            "command": ["runner", "--results-csv", str(alt_result)],
                        }
                    ]
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        self._write_results(
            alt_result,
            [
                {
                    "instance": instance,
                    "status": "OPTIMAL",
                    "wall_time": "35.0",
                    "solving_time": "33.0",
                    "node_count": "3",
                    "pricing_calls": "29",
                    "exact_pricing_calls": "9",
                }
            ],
        )
        (baseline_dir / "branch_impact_rows.jsonl").write_text(
            json.dumps(
                self._branch_row(task_i=1, task_j=2, forced_pair=None, matched=None),
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (alt_dir / "branch_impact_rows.jsonl").write_text(
            json.dumps(
                self._branch_row(task_i=1, task_j=3, forced_pair=[1, 3], matched=True),
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return runbook_path, baseline_result, alt_result, baseline_dir, alt_dir

    @staticmethod
    def _branch_row(
        *,
        task_i: int,
        task_j: int,
        forced_pair: list[int] | None,
        matched: bool | None,
        child_negative_pricing_events: float = 4.0,
        child_completion_bound_retries: float = 2.0,
    ) -> dict[str, object]:
        return {
            "log_file": "BPC_future/results/logs/BPC_future/logical_graph/tasks_020/demo.json.jsonl",
            "branch_node_id": 0,
            "depth": 0,
            "task_i": task_i,
            "task_j": task_j,
            "forced_pair": forced_pair,
            "forced_pair_matched": matched,
            "tail_class": "completion_bound_tail",
            "branch_labels": {
                "y_child_negative_pricing_events": child_negative_pricing_events,
                "y_child_completion_bound_retries": child_completion_bound_retries,
                "y_child_early_branch_triggers": 0.0,
            },
        }


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.analyze_gat_fixed_worker_post_injection import (
    analyze_post_injection,
)


def _write_csv(path: Path, row: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)


def _write_jsonl_for_csv(path: Path, rows: list[dict[str, object]]) -> None:
    jsonl = path.parent / "logs" / "run.jsonl"
    jsonl.parent.mkdir(parents=True, exist_ok=True)
    jsonl.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


class GATFixedWorkerPostInjectionTests(unittest.TestCase):
    def test_analyzes_next_rmp_and_followup_pressure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            baseline_csv = tmp / "baseline" / "results.csv"
            worker_csv = tmp / "worker" / "results.csv"
            _write_csv(
                baseline_csv,
                {
                    "status": "TIME_LIMIT",
                    "solving_time": "40.0",
                    "rmp_solves": "4",
                    "pricing_calls": "7",
                    "exact_pricing_calls": "3",
                    "dual_bound": "",
                },
            )
            _write_csv(
                worker_csv,
                {
                    "status": "TIME_LIMIT",
                    "solving_time": "45.0",
                    "rmp_solves": "5",
                    "pricing_calls": "9",
                    "exact_pricing_calls": "4",
                    "dual_bound": "",
                },
            )
            _write_jsonl_for_csv(
                baseline_csv,
                [
                    {
                        "event": "journey_rmp_dual_diagnostics",
                        "cg_iter": 1,
                        "objective": 100.0,
                        "objective_delta": None,
                        "dual_l1_delta": None,
                    },
                    {
                        "event": "journey_rmp_dual_diagnostics",
                        "cg_iter": 2,
                        "objective": 95.0,
                        "objective_delta": -5.0,
                        "dual_l1_delta": 2.0,
                    },
                    {
                        "event": "finish",
                        "status": "TIME_LIMIT",
                        "solving_time": 40.0,
                        "rmp_solves": 4,
                        "pricing_calls": 7,
                        "exact_pricing_calls": 3,
                    },
                ],
            )
            _write_jsonl_for_csv(
                worker_csv,
                [
                    {
                        "event": "journey_rmp_dual_diagnostics",
                        "cg_iter": 1,
                        "objective": 100.0,
                        "objective_delta": None,
                        "dual_l1_delta": None,
                    },
                    {
                        "event": "journey_sharded_pulse_hidden_negative_worker",
                        "cg_iter": 1,
                        "time": 1.0,
                        "pulse_worker_status": "FOUND_NEGATIVE",
                        "pulse_worker_reason": "target_materialized_negative_true_rc",
                        "pulse_worker_context_hash": "ctx-a",
                        "pulse_worker_signal_source": "expected_context_current_probe",
                        "pulse_worker_returned_journeys": 4,
                        "pulse_worker_best_rc": -3.0,
                    },
                    {
                        "event": "journey_column_addition",
                        "cg_iter": 1,
                        "time": 1.1,
                        "pricing_kind": "sharded_pulse_hidden_negative_worker",
                        "pricing_reason": "target_materialized_negative_true_rc",
                        "pricing_state": "FOUND_NEGATIVE",
                        "added_journeys": 4,
                        "new_journeys": 4,
                        "replacement_journeys": 0,
                        "active_changed_task_set_count": 1,
                        "inactive_changed_task_set_count": 3,
                        "addition_productivity_class": "active_replacement_task_set",
                    },
                    {
                        "event": "journey_rmp_dual_diagnostics",
                        "cg_iter": 2,
                        "objective": 90.0,
                        "objective_delta": -10.0,
                        "dual_l1_delta": 8.0,
                        "active_support_hash": "support-b",
                    },
                    {
                        "event": "journey_sharded_pulse_hidden_negative_worker",
                        "cg_iter": 2,
                        "pulse_worker_status": "SKIPPED",
                        "pulse_worker_skip_reason": "residual_target_context_mismatch",
                        "pulse_worker_returned_journeys": 0,
                    },
                    {
                        "event": "journey_pricing",
                        "cg_iter": 2,
                        "pricing_kind": "exact",
                    },
                    {
                        "event": "journey_exact_pricing_completion_bound_retry",
                        "cg_iter": 2,
                    },
                    {
                        "event": "finish",
                        "status": "TIME_LIMIT",
                        "solving_time": 45.0,
                        "rmp_solves": 5,
                        "pricing_calls": 9,
                        "exact_pricing_calls": 4,
                    },
                ],
            )
            runbook = tmp / "summary.json"
            runbook.write_text(
                json.dumps(
                    {
                        "all_checks_pass": True,
                        "candidate_policy": {
                            "worker_method": "target_materialization_fixed",
                        },
                        "candidate_runs": [
                            {
                                "name": "candidate-a",
                                "instance": "instance.json",
                                "expected_context_hash": "ctx-a",
                                "candidate_batch_count": 4,
                                "baseline_csv": str(baseline_csv),
                                "worker_csv": str(worker_csv),
                            }
                        ],
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            summary = analyze_post_injection(
                runbook_summary=runbook,
                output_dir=tmp / "audit",
                report=tmp / "report.md",
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["target_injection_success_count"], 1)
            self.assertEqual(summary["target_returned_journeys_sum"], 4.0)
            self.assertEqual(summary["target_active_changed_task_set_sum"], 1.0)
            self.assertEqual(summary["target_inactive_changed_task_set_sum"], 3.0)
            self.assertEqual(summary["immediate_objective_improved_count"], 1)
            self.assertEqual(summary["immediate_vs_baseline_same_iter_improved_count"], 1)
            self.assertAlmostEqual(summary["worker_next_objective_delta_sum"], -10.0)
            self.assertAlmostEqual(
                summary["worker_next_objective_vs_baseline_same_iter_delta_sum"], -5.0
            )
            self.assertEqual(summary["followup_exact_event_sum"], 1.0)
            self.assertEqual(summary["followup_completion_retry_event_sum"], 1.0)
            self.assertEqual(summary["context_mismatch_skip_sum"], 1.0)
            record = summary["records"][0]
            self.assertEqual(record["target_addition_productivity_class"], "active_replacement_task_set")
            self.assertEqual(record["final_roi_class"], "negative_exact_roi")

    def test_allow_partial_audits_only_completed_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            baseline_csv = tmp / "baseline" / "results.csv"
            worker_csv = tmp / "worker" / "results.csv"
            _write_csv(
                baseline_csv,
                {
                    "status": "TIME_LIMIT",
                    "solving_time": "40.0",
                    "rmp_solves": "4",
                    "pricing_calls": "7",
                    "exact_pricing_calls": "3",
                    "dual_bound": "",
                },
            )
            _write_csv(
                worker_csv,
                {
                    "status": "TIME_LIMIT",
                    "solving_time": "45.0",
                    "rmp_solves": "5",
                    "pricing_calls": "9",
                    "exact_pricing_calls": "4",
                    "dual_bound": "",
                },
            )
            _write_jsonl_for_csv(
                baseline_csv,
                [
                    {
                        "event": "journey_rmp_dual_diagnostics",
                        "cg_iter": 2,
                        "objective": 95.0,
                        "objective_delta": -5.0,
                        "dual_l1_delta": 2.0,
                    }
                ],
            )
            _write_jsonl_for_csv(
                worker_csv,
                [
                    {
                        "event": "journey_sharded_pulse_hidden_negative_worker",
                        "cg_iter": 1,
                        "pulse_worker_status": "FOUND_NEGATIVE",
                        "pulse_worker_context_hash": "ctx-a",
                        "pulse_worker_returned_journeys": 1,
                    },
                    {
                        "event": "journey_column_addition",
                        "cg_iter": 1,
                        "pricing_kind": "sharded_pulse_hidden_negative_worker",
                        "added_journeys": 1,
                        "active_changed_task_set_count": 1,
                    },
                    {
                        "event": "journey_rmp_dual_diagnostics",
                        "cg_iter": 2,
                        "objective": 90.0,
                        "objective_delta": -10.0,
                        "dual_l1_delta": 8.0,
                    },
                ],
            )
            runbook = tmp / "summary.json"
            runbook.write_text(
                json.dumps(
                    {
                        "all_checks_pass": True,
                        "candidate_policy": {
                            "worker_method": "target_materialization_fixed",
                        },
                        "candidate_runs": [
                            {
                                "name": "completed",
                                "instance": "instance.json",
                                "expected_context_hash": "ctx-a",
                                "baseline_csv": str(baseline_csv),
                                "worker_csv": str(worker_csv),
                            },
                            {
                                "name": "not-yet-run",
                                "instance": "instance.json",
                                "expected_context_hash": "ctx-b",
                                "baseline_csv": str(tmp / "missing-baseline" / "results.csv"),
                                "worker_csv": str(tmp / "missing-worker" / "results.csv"),
                            },
                        ],
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            strict = analyze_post_injection(
                runbook_summary=runbook,
                output_dir=tmp / "strict",
                report=tmp / "strict.md",
            )
            partial = analyze_post_injection(
                runbook_summary=runbook,
                output_dir=tmp / "partial",
                report=tmp / "partial.md",
                allow_partial=True,
            )

            self.assertFalse(strict["all_checks_pass"])
            self.assertTrue(partial["all_checks_pass"])
            self.assertEqual(partial["runbook_candidate_count"], 2)
            self.assertEqual(partial["record_count"], 1)
            self.assertEqual(partial["skipped_missing_log_count"], 1)
            self.assertEqual(partial["records"][0]["name"], "completed")

    def test_strict_trajectory_label_rejects_worse_same_iter_objective(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            baseline_csv = tmp / "baseline" / "results.csv"
            worker_csv = tmp / "worker" / "results.csv"
            _write_csv(
                baseline_csv,
                {
                    "status": "TIME_LIMIT",
                    "solving_time": "90.0",
                    "rmp_solves": "10",
                    "pricing_calls": "20",
                    "exact_pricing_calls": "10",
                    "dual_bound": "",
                },
            )
            _write_csv(
                worker_csv,
                {
                    "status": "TIME_LIMIT",
                    "solving_time": "90.0",
                    "rmp_solves": "10",
                    "pricing_calls": "20",
                    "exact_pricing_calls": "8",
                    "dual_bound": "",
                },
            )
            _write_jsonl_for_csv(
                baseline_csv,
                [
                    {
                        "event": "journey_rmp_dual_diagnostics",
                        "cg_iter": 2,
                        "objective": 100.0,
                        "objective_delta": -10.0,
                        "dual_l1_delta": 1.0,
                    }
                ],
            )
            _write_jsonl_for_csv(
                worker_csv,
                [
                    {
                        "event": "journey_sharded_pulse_hidden_negative_worker",
                        "cg_iter": 1,
                        "pulse_worker_status": "FOUND_NEGATIVE",
                        "pulse_worker_context_hash": "ctx-a",
                        "pulse_worker_returned_journeys": 1,
                    },
                    {
                        "event": "journey_column_addition",
                        "cg_iter": 1,
                        "pricing_kind": "sharded_pulse_hidden_negative_worker",
                        "added_journeys": 1,
                        "active_changed_task_set_count": 1,
                    },
                    {
                        "event": "journey_rmp_dual_diagnostics",
                        "cg_iter": 2,
                        "objective": 105.0,
                        "objective_delta": -5.0,
                        "dual_l1_delta": 1.0,
                    },
                ],
            )
            runbook = tmp / "summary.json"
            runbook.write_text(
                json.dumps(
                    {
                        "all_checks_pass": True,
                        "candidate_policy": {
                            "worker_method": "target_materialization_fixed",
                        },
                        "candidate_runs": [
                            {
                                "name": "worse-same-iter",
                                "instance": "instance.json",
                                "expected_context_hash": "ctx-a",
                                "baseline_csv": str(baseline_csv),
                                "worker_csv": str(worker_csv),
                            }
                        ],
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            summary = analyze_post_injection(
                runbook_summary=runbook,
                output_dir=tmp / "audit",
                report=tmp / "report.md",
            )

            record = summary["records"][0]
            self.assertEqual(record["final_roi_class"], "positive_exact_roi")
            self.assertEqual(record["strict_trajectory_roi_label"], 0)
            self.assertEqual(
                record["strict_trajectory_roi_reason"],
                "worse_than_baseline_same_iter_objective",
            )
            self.assertEqual(summary["strict_trajectory_positive_count"], 0)
            self.assertEqual(summary["strict_trajectory_negative_count"], 1)


if __name__ == "__main__":
    unittest.main()

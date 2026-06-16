from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.build_gat_sequential_target_materialization_utility_rows import (
    build_rows,
)


class GATSequentialTargetMaterializationUtilityRowsTests(unittest.TestCase):
    def test_workload_worse_sequential_run_becomes_bad_mode_delay_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            capture = root / "capture.jsonl"
            candidate_json = root / "candidate.json"
            log_dir = root / "logs"
            log_dir.mkdir()
            results_csv = root / "results.csv"
            baseline_json = root / "baseline.json"
            target_trace = {
                "sequence": [1],
                "start_time": 0.0,
                "arc_option_sequence": ["0->1:a", "1->0:b"],
            }
            _write_jsonl(
                capture,
                [
                    {
                        "event": "journey_counterfactual_replay_capture",
                        "context_hash": "ctx",
                        "cg_iter": 3,
                        "pricing_kind": "exact",
                        "instance_path": "graph.json",
                        "returned_journeys": [
                            {
                                "task_set": [1],
                                "sequence": [[1]],
                                "true_reduced_cost": -2.0,
                                "signature": ["sig"],
                            }
                        ],
                    }
                ],
            )
            candidate_json.write_text(
                json.dumps(
                    {
                        "candidates": [
                            {
                                "name": "target",
                                "instance": "graph.json",
                                "expected_context_hash": "ctx",
                                "cg_iter": 3,
                                "capture_pricing_kind": "exact",
                                "source_file": str(capture),
                                "target_sequence": [1],
                                "target_sortie_traces": [target_trace],
                                "target_arc_option_sequence": target_trace["arc_option_sequence"],
                            }
                        ]
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            _write_jsonl(
                log_dir / "run.jsonl",
                [
                    {"event": "journey_rmp", "cg_iter": 3, "node_id": 0, "depth": 0, "objective": 100.0},
                    {
                        "event": "journey_sharded_pulse_hidden_negative_worker",
                        "cg_iter": 3,
                        "node_id": 0,
                        "depth": 0,
                        "pulse_worker_context_hash": "ctx",
                        "pulse_worker_skipped": False,
                        "pulse_worker_status": "FOUND_NEGATIVE",
                        "pulse_worker_target_sequence": [1],
                        "pulse_worker_target_sequence_materialized": True,
                        "pulse_worker_target_sequence_negative": True,
                        "pulse_worker_returned_journeys": 1,
                        "pulse_worker_best_rc": -2.0,
                    },
                    {
                        "event": "journey_column_addition",
                        "cg_iter": 3,
                        "node_id": 0,
                        "depth": 0,
                        "pricing_kind": "sharded_pulse_hidden_negative_worker",
                        "added_journeys": 1,
                        "new_journeys": 0,
                        "replacement_journeys": 1,
                        "new_task_set_count": 0,
                        "replacement_task_set_count": 1,
                        "active_changed_task_set_count": 1,
                        "addition_productivity_class": "active_replacement_task_set",
                    },
                    {"event": "journey_rmp", "cg_iter": 4, "node_id": 0, "depth": 0, "objective": 90.0},
                ],
            )
            _write_results_csv(
                results_csv,
                {
                    "status": "TIME_LIMIT",
                    "primal_bound": "100.0",
                    "rmp_solves": "10",
                    "pricing_calls": "20",
                    "exact_pricing_calls": "8",
                    "generated_sequences": "30000",
                    "evaluated_timed_trips": "60000",
                    "columns": "10",
                },
            )
            baseline_json.write_text(
                json.dumps(
                    {
                        "status": "TIME_LIMIT",
                        "primal_bound": 100.0,
                        "rmp_solves": 5,
                        "pricing_calls": 10,
                        "exact_pricing_calls": 3,
                        "generated_sequences": 10000,
                        "evaluated_timed_trips": 20000,
                        "columns": 8,
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = build_rows(
                candidate_jsons=[candidate_json],
                worker_log_dir=log_dir,
                worker_results_csv=results_csv,
                baseline_reference_json=baseline_json,
                output_dir=root / "out",
                report=root / "report.md",
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["row_count"], 1)
            self.assertEqual(summary["positive_utility_row_count"], 0)
            self.assertEqual(summary["negative_utility_row_count"], 1)
            self.assertEqual(summary["bad_mode_row_count"], 1)
            self.assertLess(summary["trajectory_utility"]["accepted_batch_roi_label"], 0.0)
            row = json.loads((root / "out" / "sequential_target_materialization_utility_rows.jsonl").read_text())
            self.assertEqual(row["label_objective_improved"], 1)
            self.assertEqual(row["label_batch_roi_positive"], 0)
            self.assertEqual(row["label_bad_mode_switch"], 1)
            self.assertLess(row["accepted_batch_roi_label"], 0.0)
            self.assertEqual(row["training_label_scope"], "sequential_target_materialization_workload_utility")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_results_csv(path: Path, row: dict[str, str]) -> None:
    fields = [
        "status",
        "primal_bound",
        "rmp_solves",
        "pricing_calls",
        "exact_pricing_calls",
        "generated_sequences",
        "evaluated_timed_trips",
        "columns",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(row)


if __name__ == "__main__":
    unittest.main()

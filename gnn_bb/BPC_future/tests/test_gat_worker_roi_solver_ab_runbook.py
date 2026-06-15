from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_gat_worker_roi_solver_ab_results import audit_results
from BPC_future.scripts.build_gat_worker_roi_solver_ab_runbook import build_runbook


def _write_csv(path: Path, row: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)


class GATWorkerROISolverABRunbookTests(unittest.TestCase):
    def test_runbook_uses_worker_roi_high_priority_without_certificate_effect(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            logical_root = tmp / "logical_graph"
            candidate_instance = _make_graph(
                logical_root,
                scale=20,
                family="greedy-anchor",
                region="apollo15_20km",
                ordinal=2,
            )
            _make_graph(logical_root, scale=5, family="sector-wave", region="apollo15_20km", ordinal=1)
            _make_graph(
                logical_root,
                scale=5,
                family="sector-wave",
                region="tranquillitatis_balmer_like_20km",
                ordinal=1,
            )
            _make_graph(logical_root, scale=10, family="sector-wave", region="apollo15_20km", ordinal=1)
            _make_graph(
                logical_root,
                scale=10,
                family="sector-wave",
                region="tranquillitatis_balmer_like_20km",
                ordinal=1,
            )
            decisions = tmp / "decisions.jsonl"
            decisions.write_text(
                json.dumps(
                    {
                        "decision_name": "HIGH_PRIORITY",
                        "decision_split": "validation",
                        "name": "candidate_a",
                        "instance": str(candidate_instance),
                        "expected_context_hash": "ctx-a",
                        "target_sequence": [1, 2],
                        "target_arc_option_sequence": ["0->1:low_risk:2", "1->0:low_risk:2"],
                        "target_sortie_traces": [
                            {
                                "sequence": [1],
                                "start_time": 0.0,
                                "arc_option_sequence": ["0->1:low_risk:2", "1->0:low_risk:2"],
                            }
                        ],
                        "capture_pricing_kind": "exact",
                        "true_dual_hash": "dual-a",
                        "cut_hash": "cut-a",
                        "branch_hash": "branch-a",
                        "forbidden_signature_hash": "forbidden-a",
                        "active_hash_before": "active-a",
                        "pool_signature_hash": "pool-signature-a",
                        "pool_task_set_hash": "pool-task-set-a",
                        "score": 0.8,
                        "neighbor_delay_fraction": 0.0,
                        "label_worker_roi_positive": 1,
                        "roi_class": "positive_primal_roi",
                        "row_index": 3,
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            ood_summary = tmp / "ood.json"
            ood_summary.write_text(
                json.dumps(
                    {
                        "validation_candidate_ready": True,
                        "validation_metrics": {"add_precision": 1.0, "add_recall": 1.0},
                    }
                ),
                encoding="utf-8",
            )
            summary = build_runbook(
                decision_records=decisions,
                ood_summary=ood_summary,
                output_dir=tmp / "runbook",
                report=tmp / "report.md",
                logical_graph_root=logical_root,
                max_workers=4,
                max_candidates=1,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["certificate_ready"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertEqual(len(summary["candidate_runs"]), 1)
            self.assertEqual(summary["candidate_runs"][0]["expected_context_hash"], "ctx-a")
            self.assertEqual(summary["candidate_runs"][0]["capture_pricing_kind"], "exact")
            self.assertTrue(summary["candidate_runs"][0]["candidate_context_complete"])
            self.assertTrue(summary["checks"]["max_workers_bounded"])
            self.assertTrue(summary["checks"]["all_candidates_have_capture_pricing_kind"])
            self.assertTrue(summary["checks"]["all_candidates_have_full_capture_context"])
            self.assertTrue(summary["checks"]["all_candidates_have_materialization_traces"])
            small_commands = [
                item["command"]
                for item in summary["commands"]
                if item["command_type"].startswith(("task005", "task010"))
            ]
            self.assertTrue(small_commands)
            self.assertFalse(any("hidden_negative_worker_enabled=True" in command for command in small_commands))
            worker_command = next(
                item["command"]
                for item in summary["commands"]
                if item["command_type"].endswith("_worker_roi_gat_priority")
            )
            self.assertIn("journey_sharded_pulse_hidden_negative_worker_enabled=True", worker_command)
            self.assertIn("ctx-a", worker_command)
            self.assertIn(
                "journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True",
                worker_command,
            )
            self.assertNotIn("journey_final_judge_sharding_enabled=True", worker_command)

    def test_runbook_can_target_delay_queue_positive_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            logical_root = tmp / "logical_graph"
            candidate_instance = _make_graph(
                logical_root,
                scale=20,
                family="sector-wave",
                region="apollo15_20km",
                ordinal=2,
            )
            _make_graph(logical_root, scale=5, family="sector-wave", region="apollo15_20km", ordinal=1)
            _make_graph(
                logical_root,
                scale=5,
                family="sector-wave",
                region="tranquillitatis_balmer_like_20km",
                ordinal=1,
            )
            _make_graph(logical_root, scale=10, family="sector-wave", region="apollo15_20km", ordinal=1)
            _make_graph(
                logical_root,
                scale=10,
                family="sector-wave",
                region="tranquillitatis_balmer_like_20km",
                ordinal=1,
            )
            decisions = tmp / "decisions.jsonl"
            rows = [
                {
                    "decision_name": "DELAY_QUEUE",
                    "decision_split": "train",
                    "name": "delay_positive",
                    "instance": str(candidate_instance),
                    "expected_context_hash": "ctx-delay",
                    "target_sequence": [1, 2],
                    "target_arc_option_sequence": ["0->1:low_risk:2", "1->0:low_risk:2"],
                    "target_sortie_traces": [
                        {
                            "sequence": [1],
                            "start_time": 0.0,
                            "arc_option_sequence": ["0->1:low_risk:2", "1->0:low_risk:2"],
                        }
                    ],
                    "capture_pricing_kind": "exact",
                    "true_dual_hash": "dual-a",
                    "cut_hash": "cut-a",
                    "branch_hash": "branch-a",
                    "forbidden_signature_hash": "forbidden-a",
                    "active_hash_before": "active-a",
                    "pool_signature_hash": "pool-signature-a",
                    "pool_task_set_hash": "pool-task-set-a",
                    "score": 0.7,
                    "neighbor_delay_fraction": 0.8,
                    "label_worker_roi_positive": 1,
                    "roi_class": "positive_primal_roi",
                    "row_index": 4,
                },
                {
                    "decision_name": "DELAY_QUEUE",
                    "decision_split": "train",
                    "name": "delay_negative",
                    "instance": str(candidate_instance),
                    "expected_context_hash": "ctx-negative",
                    "target_sequence": [2],
                    "target_arc_option_sequence": ["0->2:low_risk:2", "2->0:low_risk:2"],
                    "target_sortie_traces": [
                        {
                            "sequence": [2],
                            "start_time": 0.0,
                            "arc_option_sequence": ["0->2:low_risk:2", "2->0:low_risk:2"],
                        }
                    ],
                    "capture_pricing_kind": "exact",
                    "true_dual_hash": "dual-b",
                    "cut_hash": "cut-b",
                    "branch_hash": "branch-b",
                    "forbidden_signature_hash": "forbidden-b",
                    "active_hash_before": "active-b",
                    "pool_signature_hash": "pool-signature-b",
                    "pool_task_set_hash": "pool-task-set-b",
                    "score": 0.9,
                    "neighbor_delay_fraction": 0.9,
                    "label_worker_roi_positive": 0,
                    "roi_class": "no_observed_roi",
                    "row_index": 5,
                },
            ]
            decisions.write_text(
                "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
                encoding="utf-8",
            )
            ood_summary = tmp / "ood.json"
            ood_summary.write_text(
                json.dumps(
                    {
                        "validation_candidate_ready": True,
                        "validation_metrics": {"add_precision": 1.0, "add_recall": 1.0},
                    }
                ),
                encoding="utf-8",
            )

            summary = build_runbook(
                decision_records=decisions,
                ood_summary=ood_summary,
                output_dir=tmp / "runbook",
                report=tmp / "report.md",
                logical_graph_root=logical_root,
                max_workers=4,
                max_candidates=2,
                decision_split="train",
                decision_name="DELAY_QUEUE",
                positive_label_only=True,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["decision_name"], "DELAY_QUEUE")
            self.assertTrue(summary["positive_label_only"])
            self.assertEqual(len(summary["candidate_runs"]), 1)
            self.assertEqual(summary["candidate_runs"][0]["name"], "delay_positive")
            self.assertEqual(summary["candidate_runs"][0]["worker_roi_label_positive"], 1)
            self.assertTrue(summary["candidate_runs"][0]["candidate_unique_key"])

    def test_runbook_excludes_existing_candidate_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            logical_root = tmp / "logical_graph"
            candidate_instance = _make_graph(
                logical_root,
                scale=20,
                family="sector-wave",
                region="apollo15_20km",
                ordinal=2,
            )
            for scale in (5, 10):
                _make_graph(logical_root, scale=scale, family="sector-wave", region="apollo15_20km", ordinal=1)
                _make_graph(
                    logical_root,
                    scale=scale,
                    family="sector-wave",
                    region="tranquillitatis_balmer_like_20km",
                    ordinal=1,
                )
            common = {
                "decision_name": "DELAY_QUEUE",
                "decision_split": "train",
                "instance": str(candidate_instance),
                "target_arc_option_sequence": ["0->1:low_risk:2", "1->0:low_risk:2"],
                "target_sortie_traces": [
                    {
                        "sequence": [1],
                        "start_time": 0.0,
                        "arc_option_sequence": ["0->1:low_risk:2", "1->0:low_risk:2"],
                    }
                ],
                "capture_pricing_kind": "exact",
                "true_dual_hash": "dual-a",
                "cut_hash": "cut-a",
                "branch_hash": "branch-a",
                "forbidden_signature_hash": "forbidden-a",
                "active_hash_before": "active-a",
                "pool_signature_hash": "pool-signature-a",
                "pool_task_set_hash": "pool-task-set-a",
                "score": 0.9,
                "neighbor_delay_fraction": 0.8,
                "label_worker_roi_positive": 1,
                "roi_class": "positive_primal_roi",
            }
            already_done = {
                **common,
                "name": "already_done",
                "expected_context_hash": "ctx-a",
                "target_sequence": [1],
            }
            legacy_excluded = dict(already_done)
            legacy_excluded.pop("roi_candidate_key", None)
            already_done["roi_candidate_key"] = "|".join(
                [
                    str(candidate_instance),
                    "ctx-a",
                    "1",
                    "0->1:low_risk:2,1->0:low_risk:2",
                ]
            )
            rows = [
                already_done,
                {**common, "name": "new_candidate", "expected_context_hash": "ctx-b", "target_sequence": [2]},
            ]
            decisions = tmp / "decisions.jsonl"
            decisions.write_text(
                "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
                encoding="utf-8",
            )
            ood_summary = tmp / "ood.json"
            ood_summary.write_text(
                json.dumps({"validation_candidate_ready": True, "validation_metrics": {}}),
                encoding="utf-8",
            )
            excluded = tmp / "excluded_summary.json"
            excluded.write_text(json.dumps({"candidate_runs": [legacy_excluded]}), encoding="utf-8")

            summary = build_runbook(
                decision_records=decisions,
                ood_summary=ood_summary,
                output_dir=tmp / "runbook",
                report=tmp / "report.md",
                logical_graph_root=logical_root,
                max_workers=4,
                max_candidates=2,
                decision_split="train",
                decision_name="DELAY_QUEUE",
                positive_label_only=True,
                exclude_runbook_summaries=(excluded,),
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertGreaterEqual(summary["excluded_candidate_key_count"], 1)
            self.assertEqual(len(summary["candidate_runs"]), 1)
            self.assertEqual(summary["candidate_runs"][0]["name"], "new_candidate")

    def test_runbook_excludes_existing_candidate_jsonl_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            logical_root = tmp / "logical_graph"
            candidate_instance = _make_graph(
                logical_root,
                scale=20,
                family="sector-wave",
                region="apollo15_20km",
                ordinal=2,
            )
            for scale in (5, 10):
                _make_graph(logical_root, scale=scale, family="sector-wave", region="apollo15_20km", ordinal=1)
                _make_graph(
                    logical_root,
                    scale=scale,
                    family="sector-wave",
                    region="tranquillitatis_balmer_like_20km",
                    ordinal=1,
                )
            common = {
                "decision_name": "DELAY_QUEUE",
                "decision_split": "train",
                "instance": str(candidate_instance),
                "target_arc_option_sequence": ["0->1:low_risk:2", "1->0:low_risk:2"],
                "target_sortie_traces": [
                    {
                        "sequence": [1],
                        "start_time": 0.0,
                        "arc_option_sequence": ["0->1:low_risk:2", "1->0:low_risk:2"],
                    }
                ],
                "capture_pricing_kind": "exact",
                "true_dual_hash": "dual-a",
                "cut_hash": "cut-a",
                "branch_hash": "branch-a",
                "forbidden_signature_hash": "forbidden-a",
                "active_hash_before": "active-a",
                "pool_signature_hash": "pool-signature-a",
                "pool_task_set_hash": "pool-task-set-a",
                "score": 0.9,
                "neighbor_delay_fraction": 0.8,
                "label_worker_roi_positive": 1,
                "roi_class": "positive_primal_roi",
            }
            existing = {
                **common,
                "name": "existing_dataset_label",
                "expected_context_hash": "ctx-a",
                "target_sequence": [1],
            }
            new_candidate = {
                **common,
                "name": "new_candidate",
                "expected_context_hash": "ctx-b",
                "target_sequence": [2],
            }
            decisions = tmp / "decisions.jsonl"
            decisions.write_text(
                "\n".join(json.dumps(row, sort_keys=True) for row in [existing, new_candidate]) + "\n",
                encoding="utf-8",
            )
            existing_jsonl = tmp / "existing.jsonl"
            existing_jsonl.write_text(json.dumps(existing, sort_keys=True) + "\n", encoding="utf-8")
            ood_summary = tmp / "ood.json"
            ood_summary.write_text(
                json.dumps({"validation_candidate_ready": True, "validation_metrics": {}}),
                encoding="utf-8",
            )

            summary = build_runbook(
                decision_records=decisions,
                ood_summary=ood_summary,
                output_dir=tmp / "runbook",
                report=tmp / "report.md",
                logical_graph_root=logical_root,
                max_workers=4,
                max_candidates=2,
                decision_split="train",
                decision_name="DELAY_QUEUE",
                positive_label_only=True,
                exclude_candidate_jsonls=(existing_jsonl,),
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["exclude_candidate_jsonls"], [str(existing_jsonl)])
            self.assertEqual(len(summary["candidate_runs"]), 1)
            self.assertEqual(summary["candidate_runs"][0]["name"], "new_candidate")

    def test_solver_ab_audit_reads_small_and_candidate_csvs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            runbook = {
                "all_checks_pass": True,
                "certificate_ready": False,
                "official_bound_effect": False,
                "small_no_regression": [
                    {"task_count": 5, "results_csv": str(tmp / "task005" / "results.csv")},
                    {"task_count": 10, "results_csv": str(tmp / "task010" / "results.csv")},
                ],
                "candidate_runs": [
                    {
                        "name": "candidate_a",
                        "instance": "instance_a",
                        "expected_context_hash": "ctx-a",
                        "target_sequence": [1, 2],
                        "baseline_csv": str(tmp / "base" / "results.csv"),
                        "worker_csv": str(tmp / "worker" / "results.csv"),
                    }
                ],
            }
            runbook_path = tmp / "summary.json"
            runbook_path.write_text(json.dumps(runbook), encoding="utf-8")
            for item in runbook["small_no_regression"]:
                _write_csv(
                    Path(item["results_csv"]),
                    {
                        "status": "OPTIMAL",
                        "solving_time": 1.0,
                        "primal_bound": 10.0,
                        "dual_bound": 10.0,
                    },
                )
            _write_csv(
                tmp / "base" / "results.csv",
                {
                    "status": "TIME_LIMIT",
                    "primal_bound": 100.0,
                    "dual_bound": "",
                    "exact_pricing_calls": 5,
                    "pricing_calls": 20,
                    "solving_time": 30.0,
                },
            )
            _write_csv(
                tmp / "worker" / "results.csv",
                {
                    "status": "TIME_LIMIT",
                    "primal_bound": 90.0,
                    "dual_bound": "",
                    "exact_pricing_calls": 4,
                    "pricing_calls": 18,
                    "solving_time": 25.0,
                },
            )
            summary = audit_results(
                runbook_summary=runbook_path,
                output_dir=tmp / "audit",
                report=tmp / "audit.md",
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["roi_class_counts"], {"positive_primal_roi": 1})
            self.assertEqual(summary["positive_trajectory_roi_count"], 1)
            self.assertFalse(summary["official_bound_effect"])
            self.assertFalse(summary["certificate_ready"])


def _make_graph(
    root: Path,
    *,
    scale: int,
    family: str,
    region: str,
    ordinal: int,
) -> Path:
    path = (
        root
        / f"tasks_{int(scale):03d}"
        / family
        / region
        / f"{region}_{family}_randomtw_tasks{int(scale):03d}_{int(ordinal):02d}_seed61000_logical_graph.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")
    return path


if __name__ == "__main__":
    unittest.main()

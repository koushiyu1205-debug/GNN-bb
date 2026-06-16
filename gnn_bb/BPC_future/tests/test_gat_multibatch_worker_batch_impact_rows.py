from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

try:
    from BPC_future.scripts.build_gat_batch_impact_dataset import build_dataset
    from BPC_future.scripts.build_gat_multibatch_worker_batch_impact_rows import build_rows
    from BPC_future.tests.test_learning_components import _toy_payload

    HAS_LEARNING_STACK = True
except Exception:
    HAS_LEARNING_STACK = False


@unittest.skipUnless(HAS_LEARNING_STACK, "learning stack is not installed")
class GATMultiBatchWorkerBatchImpactRowsTests(unittest.TestCase):
    def test_worker_causal_rows_feed_pairwise_batch_impact_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            graph_path = _graph_path(root)
            context_hash = "ctx-shared"
            capture_log = root / "capture.jsonl"
            target_a = _trace([1, 2], "low_risk", 0.0)
            target_b = _trace([3], "low_time", 12.0)
            _write_jsonl(
                capture_log,
                [
                    _capture_event(
                        graph_path=graph_path,
                        context_hash=context_hash,
                        returned=[
                            _journey(target_a, -3.0),
                            _journey(target_b, -1.0),
                        ],
                    )
                ],
            )
            runbook = root / "runbook_summary.json"
            candidate_a = _candidate(
                root,
                name="target_a",
                graph_path=graph_path,
                capture_log=capture_log,
                context_hash=context_hash,
                trace=target_a,
            )
            candidate_b = _candidate(
                root,
                name="target_b",
                graph_path=graph_path,
                capture_log=capture_log,
                context_hash=context_hash,
                trace=target_b,
            )
            _write_worker_log(candidate_a, context_hash=context_hash, objective_after=90.0)
            _write_worker_log(candidate_b, context_hash=context_hash, objective_after=100.0)
            runbook.write_text(
                json.dumps(
                    {
                        "certificate_ready": False,
                        "official_bound_effect": False,
                        "candidate_runs": [candidate_a, candidate_b],
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            rows_summary = build_rows(
                runbook_summary=runbook,
                output_dir=root / "rows",
                report=root / "rows_report.md",
            )

            self.assertTrue(rows_summary["all_checks_pass"])
            self.assertEqual(rows_summary["row_count"], 2)
            self.assertEqual(rows_summary["positive_objective_improvement_count"], 1)
            self.assertEqual(rows_summary["non_improving_objective_count"], 1)
            self.assertEqual(rows_summary["pairwise_context_count"], 1)

            dataset_summary = build_dataset(
                input_jsonl=Path(rows_summary["jsonl_path"]),
                output_dir=root / "dataset",
                report=root / "dataset_report.md",
                min_samples_for_training=1,
                min_positive_batches_for_training=1,
                min_delay_candidates_for_training=1,
                min_same_context_pairs_for_ranking=1,
            )

            self.assertTrue(dataset_summary["all_checks_pass"])
            self.assertTrue(dataset_summary["ranking_ready"])
            self.assertEqual(dataset_summary["pairwise_context_stats"]["same_context_pair_count"], 1)
            self.assertEqual(dataset_summary["pairwise_context_stats"]["same_context_comparable_pair_count"], 1)
            self.assertEqual(dataset_summary["pairwise_context_stats"]["positive_negative_label_pair_count"], 1)
            self.assertEqual(dataset_summary["candidate_count"], 2)
            manifest = json.loads((root / "dataset" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual([sample["candidate_count"] for sample in manifest["samples"]], [1, 1])
            self.assertEqual(manifest["candidate_label_counts"], {"delay_queue": 1, "high_priority": 1})

    def test_missing_worker_logs_do_not_create_training_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            graph_path = _graph_path(root)
            capture_log = root / "capture.jsonl"
            context_hash = "ctx"
            trace = _trace([1], "low_risk", 0.0)
            _write_jsonl(
                capture_log,
                [
                    _capture_event(
                        graph_path=graph_path,
                        context_hash=context_hash,
                        returned=[_journey(trace, -1.0)],
                    )
                ],
            )
            runbook = root / "runbook_summary.json"
            runbook.write_text(
                json.dumps(
                    {
                        "certificate_ready": False,
                        "official_bound_effect": False,
                        "candidate_runs": [
                            _candidate(
                                root,
                                name="missing",
                                graph_path=graph_path,
                                capture_log=capture_log,
                                context_hash=context_hash,
                                trace=trace,
                            )
                        ],
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = build_rows(
                runbook_summary=runbook,
                output_dir=root / "rows",
                report=root / "rows_report.md",
            )

            self.assertFalse(summary["all_checks_pass"])
            self.assertEqual(summary["status"], "no_rows")
            self.assertEqual(summary["row_count"], 0)
            self.assertEqual(summary["skipped_counts"], {"missing_worker_logs": 1})

    def test_ab_audit_overrides_immediate_objective_and_keeps_batch_signatures(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            graph_path = _graph_path(root)
            context_hash = "ctx-shared"
            capture_log = root / "capture.jsonl"
            target_a = _trace([1, 2], "low_risk", 0.0)
            target_b = _trace([3], "low_time", 12.0)
            _write_jsonl(
                capture_log,
                [
                    _capture_event(
                        graph_path=graph_path,
                        context_hash=context_hash,
                        returned=[
                            _journey(target_a, -3.0),
                            _journey(target_b, -1.0),
                        ],
                    )
                ],
            )
            candidate_a = _candidate(
                root,
                name="target_a",
                graph_path=graph_path,
                capture_log=capture_log,
                context_hash=context_hash,
                trace=target_a,
            )
            candidate_b = _candidate(
                root,
                name="target_b",
                graph_path=graph_path,
                capture_log=capture_log,
                context_hash=context_hash,
                trace=target_b,
            )
            _write_worker_log(
                candidate_a,
                context_hash=context_hash,
                objective_after=90.0,
                returned_signature_samples=[_signature_sample(target_a), _signature_sample(target_b)],
            )
            _write_worker_log(
                candidate_b,
                context_hash=context_hash,
                objective_after=100.0,
                returned_signature_samples=[_signature_sample(target_b)],
            )
            runbook = root / "runbook_summary.json"
            runbook.write_text(
                json.dumps(
                    {
                        "certificate_ready": False,
                        "official_bound_effect": False,
                        "candidate_runs": [candidate_a, candidate_b],
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            audit = root / "ab_audit_summary.json"
            audit.write_text(
                json.dumps(
                    {
                        "certificate_ready": False,
                        "official_bound_effect": False,
                        "records": [
                            {
                                "name": "target_a",
                                "worker_csv": candidate_a["worker_csv"],
                                "roi_class": "negative_retry_roi",
                                "primal_improvement": 0.0,
                                "exact_pricing_calls_delta": 1,
                                "pricing_calls_delta": 2,
                                "rmp_solves_delta": 1,
                                "generated_sequences_delta": 100,
                                "solving_time_delta": 0.5,
                            },
                            {
                                "name": "target_b",
                                "worker_csv": candidate_b["worker_csv"],
                                "roi_class": "no_observed_roi",
                                "primal_improvement": 0.0,
                                "exact_pricing_calls_delta": 0,
                                "pricing_calls_delta": 0,
                                "rmp_solves_delta": 0,
                                "generated_sequences_delta": 0,
                                "solving_time_delta": 0.0,
                            },
                        ],
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            rows_summary = build_rows(
                runbook_summary=runbook,
                ab_audit_summary=audit,
                output_dir=root / "rows",
                report=root / "rows_report.md",
            )

            self.assertTrue(rows_summary["all_checks_pass"])
            self.assertEqual(rows_summary["row_count"], 2)
            self.assertEqual(rows_summary["positive_objective_improvement_count"], 1)
            self.assertEqual(rows_summary["positive_trajectory_roi_count"], 0)
            self.assertEqual(rows_summary["nonpositive_trajectory_roi_count"], 2)
            self.assertEqual(
                rows_summary["roi_class_counts"],
                {"negative_retry_roi": 1, "no_observed_roi": 1},
            )
            rows = [
                json.loads(line)
                for line in Path(rows_summary["jsonl_path"]).read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(rows[0]["label_objective_improved"], 1)
            self.assertEqual(rows[0]["label_batch_roi_positive"], 0)
            self.assertEqual(rows[0]["label_bad_mode_switch"], 1)
            self.assertLess(rows[0]["accepted_batch_roi_label"], 0.0)
            self.assertEqual(len(rows[0]["target_signature_samples"]), 2)

            dataset_summary = build_dataset(
                input_jsonl=Path(rows_summary["jsonl_path"]),
                output_dir=root / "dataset",
                report=root / "dataset_report.md",
                min_samples_for_training=1,
                min_positive_batches_for_training=0,
                min_delay_candidates_for_training=1,
                min_same_context_pairs_for_ranking=1,
            )

            self.assertTrue(dataset_summary["all_checks_pass"])
            self.assertEqual(dataset_summary["sample_count"], 2)
            self.assertEqual(dataset_summary["candidate_count"], 3)
            self.assertEqual(dataset_summary["batch_label_counts"], {"non_improving": 2})
            self.assertEqual(dataset_summary["candidate_label_counts"], {"delay_queue": 3})

    def test_reachability_summary_filters_invalid_ab_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            graph_path = _graph_path(root)
            context_hash = "ctx-shared"
            capture_log = root / "capture.jsonl"
            target_a = _trace([1, 2], "low_risk", 0.0)
            target_b = _trace([3], "low_time", 12.0)
            target_c = _trace([4], "low_risk", 18.0)
            _write_jsonl(
                capture_log,
                [
                    _capture_event(
                        graph_path=graph_path,
                        context_hash=context_hash,
                        returned=[
                            _journey(target_a, -3.0),
                            _journey(target_b, -1.0),
                            _journey(target_c, -0.5),
                        ],
                    )
                ],
            )
            candidate_a = _candidate(
                root,
                name="target_a",
                graph_path=graph_path,
                capture_log=capture_log,
                context_hash=context_hash,
                trace=target_a,
            )
            candidate_b = _candidate(
                root,
                name="target_b",
                graph_path=graph_path,
                capture_log=capture_log,
                context_hash=context_hash,
                trace=target_b,
            )
            candidate_c = _candidate(
                root,
                name="target_c",
                graph_path=graph_path,
                capture_log=capture_log,
                context_hash=context_hash,
                trace=target_c,
            )
            _write_worker_log(candidate_a, context_hash=context_hash, objective_after=90.0)
            _write_worker_log(candidate_b, context_hash=context_hash, objective_after=100.0)
            runbook = root / "runbook_summary.json"
            runbook.write_text(
                json.dumps(
                    {
                        "certificate_ready": False,
                        "official_bound_effect": False,
                        "candidate_runs": [candidate_a, candidate_b, candidate_c],
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            audit = root / "ab_audit_summary.json"
            audit.write_text(
                json.dumps(
                    {
                        "certificate_ready": False,
                        "official_bound_effect": False,
                        "records": [
                            {"name": "target_a", "worker_csv": candidate_a["worker_csv"], "roi_class": "positive_retry_roi"},
                            {"name": "target_b", "worker_csv": candidate_b["worker_csv"], "roi_class": "no_observed_roi"},
                            {"name": "target_c", "worker_csv": candidate_c["worker_csv"], "roi_class": "positive_primal_roi"},
                        ],
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            reachability = root / "reachability_summary.json"
            reachability.write_text(
                json.dumps(
                    {
                        "certificate_ready": False,
                        "official_bound_effect": False,
                        "records": [
                            {
                                "name": "target_a",
                                "worker_csv": candidate_a["worker_csv"],
                                "training_label_allowed": True,
                            },
                            {
                                "name": "target_b",
                                "worker_csv": candidate_b["worker_csv"],
                                "training_label_allowed": True,
                            },
                            {
                                "name": "target_c",
                                "worker_csv": candidate_c["worker_csv"],
                                "training_label_allowed": False,
                            },
                        ],
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            rows_summary = build_rows(
                runbook_summary=runbook,
                ab_audit_summary=audit,
                reachability_summary=reachability,
                output_dir=root / "rows",
                report=root / "rows_report.md",
            )

            self.assertTrue(rows_summary["all_checks_pass"])
            self.assertEqual(rows_summary["candidate_count"], 3)
            self.assertEqual(rows_summary["reachability_record_count"], 3)
            self.assertEqual(rows_summary["reachability_allowed_candidate_count"], 2)
            self.assertEqual(rows_summary["ab_audit_record_count"], 3)
            self.assertEqual(rows_summary["ab_audit_matched_row_count"], 2)
            self.assertEqual(rows_summary["row_count"], 2)
            self.assertEqual(rows_summary["skipped_counts"], {"reachability_not_training_label": 1})


def _graph_path(root: Path) -> Path:
    graph_path = (
        root
        / "tasks_020"
        / "sector-wave"
        / "apollo15_20km"
        / "apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json"
    )
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph_path.write_text(json.dumps(_toy_payload()), encoding="utf-8")
    return graph_path


def _trace(tasks: list[int], arc_kind: str, start_time: float) -> dict[str, object]:
    arcs = [f"0->{tasks[0]}:{arc_kind}:0"]
    arcs.extend(f"{left}->{right}:{arc_kind}:0" for left, right in zip(tasks, tasks[1:]))
    arcs.append(f"{tasks[-1]}->0:{arc_kind}:0")
    return {
        "sequence": list(tasks),
        "arc_option_sequence": arcs,
        "start_time": float(start_time),
    }


def _signature_sample(trace: dict[str, object]) -> str:
    return (
        f"{','.join(str(task) for task in trace['sequence'])}"
        f"@{float(trace['start_time'])}:"
        f"{','.join(str(arc) for arc in trace['arc_option_sequence'])}"
    )


def _journey(trace: dict[str, object], true_rc: float) -> dict[str, object]:
    tasks = list(trace["sequence"])
    arcs = list(trace["arc_option_sequence"])
    start_time = float(trace["start_time"])
    return {
        "task_set": tasks,
        "sequence": [tasks],
        "true_reduced_cost": true_rc,
        "cost": 10.0,
        "signature": [[tasks, arcs, start_time]],
        "trips": [
            {
                "tasks": tasks,
                "start_time": start_time,
                "arc_option_ids": arcs,
            }
        ],
    }


def _capture_event(
    *,
    graph_path: Path,
    context_hash: str,
    returned: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "event": "journey_counterfactual_replay_capture",
        "instance": graph_path.stem,
        "instance_path": str(graph_path),
        "context_hash": context_hash,
        "true_dual_hash": "dual",
        "cut_hash": "cut",
        "branch_hash": "branch",
        "forbidden_signature_hash": "forbidden",
        "active_hash_before": "active",
        "pool_signature_hash": "pool-sig",
        "pool_task_set_hash": "pool-task",
        "cg_iter": 7,
        "pricing_kind": "exact",
        "node_id": 0,
        "depth": 0,
        "pool_journey_count": 5,
        "active_basis_journey_count": 2,
        "active_task_set_count": 2,
        "active_basis_fractional_journey_count": 1,
        "true_dual_vector": [1.0, 2.0, 3.0],
        "true_duals": {"fleet_limit": 4.0},
        "cut_duals": {"cut-a": 0.5},
        "branch_constraints": [],
        "pool_task_sets": [[1]],
        "pool_signatures": [],
        "state_t_final_judge_retry_count": 0,
        "returned_journey_count": len(returned),
        "returned_journeys": returned,
    }


def _candidate(
    root: Path,
    *,
    name: str,
    graph_path: Path,
    capture_log: Path,
    context_hash: str,
    trace: dict[str, object],
) -> dict[str, object]:
    run_dir = root / "worker_ab" / name
    return {
        "name": name,
        "instance": str(graph_path),
        "expected_context_hash": context_hash,
        "true_dual_hash": "dual",
        "cut_hash": "cut",
        "branch_hash": "branch",
        "forbidden_signature_hash": "forbidden",
        "active_hash_before": "active",
        "pool_signature_hash": "pool-sig",
        "pool_task_set_hash": "pool-task",
        "target_sequence": list(trace["sequence"]),
        "target_priority_sequence": list(trace["sequence"]),
        "target_arc_option_sequence": list(trace["arc_option_sequence"]),
        "target_sortie_traces": [trace],
        "source_file": str(capture_log),
        "worker_csv": str(run_dir / "results.csv"),
    }


def _write_worker_log(
    candidate: dict[str, object],
    *,
    context_hash: str,
    objective_after: float,
    returned_signature_samples: list[str] | None = None,
) -> None:
    worker_csv = Path(str(candidate["worker_csv"]))
    log_path = worker_csv.parent / "logs" / "worker.jsonl"
    trace = list(candidate["target_sortie_traces"])[0]
    signature_samples = returned_signature_samples or [_signature_sample(trace)]
    _write_jsonl(
        log_path,
        [
            {"event": "journey_rmp", "cg_iter": 3, "node_id": 0, "depth": 0, "objective": 100.0},
            {
                "event": "journey_sharded_pulse_hidden_negative_worker",
                "cg_iter": 3,
                "node_id": 0,
                "depth": 0,
                "pulse_worker_skipped": False,
                "pulse_worker_context_hash": context_hash,
                "pulse_worker_true_dual_hash": "dual",
                "pulse_worker_cut_hash": "cut",
                "pulse_worker_branch_hash": "branch",
                "pulse_worker_forbidden_signature_hash": "forbidden",
                "pulse_worker_target_sequence": list(candidate["target_sequence"]),
                "pulse_worker_target_sequence_materialized": True,
                "pulse_worker_target_sequence_negative": True,
                "pulse_worker_returned_journeys": len(signature_samples),
                "pulse_worker_returned_candidate_signature_samples": signature_samples,
                "pulse_worker_best_rc": -1.0,
            },
            {
                "event": "journey_column_addition",
                "cg_iter": 3,
                "node_id": 0,
                "depth": 0,
                "pricing_kind": "sharded_pulse_hidden_negative_worker",
                "added_journeys": 1,
                "new_journeys": 1,
                "replacement_journeys": 0,
                "new_task_set_count": 1,
                "replacement_task_set_count": 0,
                "active_changed_task_set_count": int(list(trace["sequence"])[0] == 1),
                "addition_productivity_class": "active_new_task_set",
            },
            {"event": "journey_rmp", "cg_iter": 4, "node_id": 0, "depth": 0, "objective": objective_after},
        ],
    )


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.build_gat_batch_impact_multibatch_intervention_plan import (
    build_intervention_plan,
)
from BPC_future.scripts.build_gat_target_priority_worker_ab_runbook import (
    _normalized_candidate,
)


class GATBatchImpactMultiBatchInterventionPlanTests(unittest.TestCase):
    def test_builds_same_context_multibatch_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            graph_path = _graph_path(root)
            source_log = root / "capture.jsonl"
            dataset_dir = root / "dataset"
            opportunity_jsonl = root / "opportunities.jsonl"
            output_dir = root / "plan"
            report = root / "report.md"
            context_hash = "ctx-high-roi"

            _write_jsonl(
                source_log,
                [
                    _capture_event(
                        graph_path=graph_path,
                        context_hash=context_hash,
                        returned=[
                            _journey([1], -4.0, "low_risk"),
                            _journey([2, 3], -2.5, "low_time"),
                            _journey([4], -1.0, "low_energy"),
                            _journey([5], 0.5, "low_risk"),
                        ],
                    )
                ],
            )
            _write_manifest(
                dataset_dir,
                source_log=source_log,
                graph_path=graph_path,
                context_hash=context_hash,
                candidate_count=4,
                accepted_batch_roi=1.2,
            )
            _write_jsonl(
                opportunity_jsonl,
                [
                    {
                        "context_hash": context_hash,
                        "instance_path": str(graph_path),
                        "candidate_count": 4,
                        "accepted_batch_roi_label": 1.2,
                        "is_high_roi_opportunity": True,
                        "is_missed_high_roi_opportunity": True,
                        "task_count": 20,
                    }
                ],
            )

            summary = build_intervention_plan(
                dataset_dir=dataset_dir,
                opportunity_jsonl_paths=[opportunity_jsonl],
                output_dir=output_dir,
                report=report,
                max_contexts=1,
                targets_per_context=2,
                min_negative_targets_per_context=2,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["certificate_ready"])
            self.assertEqual(summary["selected_context_count"], 1)
            self.assertEqual(summary["pairwise_context_target_count"], 1)
            self.assertEqual(summary["candidate_count"], 2)
            self.assertEqual(summary["skipped_counts"], {})
            self.assertTrue((output_dir / "candidates.json").exists())
            self.assertTrue((output_dir / "runbook_command.txt").exists())
            self.assertTrue(report.exists())

            payload = json.loads((output_dir / "candidates.json").read_text(encoding="utf-8"))
            candidates = payload["candidates"]
            self.assertEqual(len(candidates), 2)
            self.assertEqual(
                {candidate["expected_context_hash"] for candidate in candidates},
                {context_hash},
            )
            self.assertTrue(
                all(float(candidate["best_true_reduced_cost"]) < 0.0 for candidate in candidates)
            )
            self.assertTrue(all(candidate["target_sortie_traces"] for candidate in candidates))
            self.assertTrue(all(candidate["target_arc_option_sequence"] for candidate in candidates))
            self.assertTrue(all(candidate["certificate_effect"] is False for candidate in candidates))
            self.assertTrue(all(candidate["official_bound_effect"] is False for candidate in candidates))

            normalized = _normalized_candidate(candidates[0], 1)
            self.assertTrue(normalized["candidate_context_complete"])
            self.assertEqual(normalized["expected_context_hash"], context_hash)

    def test_skips_context_without_enough_negative_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            graph_path = _graph_path(root)
            source_log = root / "capture.jsonl"
            dataset_dir = root / "dataset"
            opportunity_jsonl = root / "opportunities.jsonl"
            context_hash = "ctx-one-negative"

            _write_jsonl(
                source_log,
                [
                    _capture_event(
                        graph_path=graph_path,
                        context_hash=context_hash,
                        returned=[
                            _journey([1], -1.0, "low_risk"),
                            _journey([2], 0.1, "low_time"),
                        ],
                    )
                ],
            )
            _write_manifest(
                dataset_dir,
                source_log=source_log,
                graph_path=graph_path,
                context_hash=context_hash,
                candidate_count=2,
                accepted_batch_roi=0.9,
            )
            _write_jsonl(
                opportunity_jsonl,
                [
                    {
                        "context_hash": context_hash,
                        "instance_path": str(graph_path),
                        "candidate_count": 2,
                        "accepted_batch_roi_label": 0.9,
                        "is_high_roi_opportunity": True,
                    }
                ],
            )

            summary = build_intervention_plan(
                dataset_dir=dataset_dir,
                opportunity_jsonl_paths=[opportunity_jsonl],
                output_dir=root / "plan",
                report=root / "report.md",
                max_contexts=1,
                targets_per_context=2,
                min_negative_targets_per_context=2,
            )

            self.assertFalse(summary["all_checks_pass"])
            self.assertEqual(summary["status"], "no_candidates")
            self.assertEqual(summary["candidate_count"], 0)
            self.assertEqual(summary["selected_context_count"], 0)
            self.assertEqual(
                summary["skipped_counts"],
                {"not_enough_unique_negative_targets": 1},
            )

    def test_can_require_context_present_in_opportunity_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            graph_path = _graph_path(root)
            source_log = root / "capture.jsonl"
            dataset_dir = root / "dataset"
            opportunity_jsonl = root / "opportunities.jsonl"
            selected_context = "ctx-validation"
            fallback_context = "ctx-train-fallback"

            _write_jsonl(
                source_log,
                [
                    _capture_event(
                        graph_path=graph_path,
                        context_hash=selected_context,
                        returned=[
                            _journey([1], -4.0, "low_risk"),
                            _journey([2], -3.0, "low_time"),
                        ],
                    ),
                    _capture_event(
                        graph_path=graph_path,
                        context_hash=fallback_context,
                        returned=[
                            _journey([3], -6.0, "low_risk"),
                            _journey([4], -5.0, "low_time"),
                        ],
                    ),
                ],
            )
            _write_manifest(
                dataset_dir,
                source_log=source_log,
                graph_path=graph_path,
                context_hash=selected_context,
                candidate_count=2,
                accepted_batch_roi=1.0,
            )
            _append_manifest_sample(
                dataset_dir,
                source_log=source_log,
                graph_path=graph_path,
                context_hash=fallback_context,
                candidate_count=2,
                accepted_batch_roi=9.0,
            )
            _write_jsonl(
                opportunity_jsonl,
                [
                    {
                        "context_hash": selected_context,
                        "instance_path": str(graph_path),
                        "candidate_count": 2,
                        "accepted_batch_roi_label": 1.0,
                        "is_high_roi_opportunity": True,
                        "task_count": 20,
                    }
                ],
            )

            summary = build_intervention_plan(
                dataset_dir=dataset_dir,
                opportunity_jsonl_paths=[opportunity_jsonl],
                output_dir=root / "plan",
                report=root / "report.md",
                max_contexts=2,
                targets_per_context=2,
                min_negative_targets_per_context=2,
                require_opportunity_context=True,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertTrue(summary["require_opportunity_context"])
            self.assertEqual(summary["selected_context_count"], 1)
            self.assertEqual(summary["candidate_count"], 2)
            self.assertEqual(
                {candidate["expected_context_hash"] for candidate in summary["candidates"]},
                {selected_context},
            )

    def test_can_restrict_contexts_to_training_split(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            train_graph = _graph_path(root / "train")
            validation_graph = _graph_path(root / "validation")
            source_log = root / "capture.jsonl"
            dataset_dir = root / "dataset"
            split_summary = root / "metrics.json"
            train_context = "ctx-train"
            validation_context = "ctx-validation"

            _write_jsonl(
                source_log,
                [
                    _capture_event(
                        graph_path=train_graph,
                        context_hash=train_context,
                        returned=[
                            _journey([1], -4.0, "low_risk"),
                            _journey([2], -3.0, "low_time"),
                        ],
                    ),
                    _capture_event(
                        graph_path=validation_graph,
                        context_hash=validation_context,
                        returned=[
                            _journey([3], -8.0, "low_risk"),
                            _journey([4], -7.0, "low_time"),
                        ],
                    ),
                ],
            )
            _write_manifest(
                dataset_dir,
                source_log=source_log,
                graph_path=train_graph,
                context_hash=train_context,
                candidate_count=2,
                accepted_batch_roi=1.0,
            )
            _append_manifest_sample(
                dataset_dir,
                source_log=source_log,
                graph_path=validation_graph,
                context_hash=validation_context,
                candidate_count=2,
                accepted_batch_roi=9.0,
            )
            split_summary.write_text(
                json.dumps(
                    {
                        "split": {
                            "train_instances": [str(train_graph)],
                            "validation_instances": [str(validation_graph)],
                        }
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = build_intervention_plan(
                dataset_dir=dataset_dir,
                opportunity_jsonl_paths=[],
                output_dir=root / "plan",
                report=root / "report.md",
                max_contexts=2,
                targets_per_context=2,
                min_negative_targets_per_context=2,
                split_summary=split_summary,
                split_mode="train",
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["split_mode"], "train")
            self.assertEqual(summary["split_instance_count"], 1)
            self.assertEqual(summary["planned_context_count"], 1)
            self.assertEqual(summary["selected_context_count"], 1)
            self.assertEqual(summary["candidate_count"], 2)
            self.assertEqual(
                {candidate["expected_context_hash"] for candidate in summary["candidates"]},
                {train_context},
            )

    def test_can_filter_contexts_by_instance_family(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sector_graph = _graph_path(root / "sector")
            random_graph = (
                root
                / "random"
                / "tasks_020"
                / "random-wave"
                / "apollo15_20km"
                / "apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json"
            )
            random_graph.parent.mkdir(parents=True, exist_ok=True)
            random_graph.write_text(json.dumps({"tasks": []}), encoding="utf-8")
            source_log = root / "capture.jsonl"
            dataset_dir = root / "dataset"
            opportunity_jsonl = root / "opportunities.jsonl"
            sector_context = "ctx-sector"
            random_context = "ctx-random"

            _write_jsonl(
                source_log,
                [
                    _capture_event(
                        graph_path=sector_graph,
                        context_hash=sector_context,
                        returned=[
                            _journey([1], -4.0, "low_risk"),
                            _journey([2], -3.0, "low_time"),
                        ],
                    ),
                    _capture_event(
                        graph_path=random_graph,
                        context_hash=random_context,
                        returned=[
                            _journey([3], -9.0, "low_risk"),
                            _journey([4], -8.0, "low_time"),
                        ],
                    ),
                ],
            )
            _write_manifest(
                dataset_dir,
                source_log=source_log,
                graph_path=sector_graph,
                context_hash=sector_context,
                candidate_count=2,
                accepted_batch_roi=1.0,
            )
            _append_manifest_sample(
                dataset_dir,
                source_log=source_log,
                graph_path=random_graph,
                context_hash=random_context,
                candidate_count=2,
                accepted_batch_roi=9.0,
            )
            _write_jsonl(
                opportunity_jsonl,
                [
                    {
                        "context_hash": sector_context,
                        "instance_path": str(sector_graph),
                        "family": "sector-wave",
                        "candidate_count": 2,
                        "accepted_batch_roi_label": 1.0,
                        "is_high_roi_opportunity": True,
                        "task_count": 20,
                    },
                    {
                        "context_hash": random_context,
                        "instance_path": str(random_graph),
                        "family": "random-wave",
                        "candidate_count": 2,
                        "accepted_batch_roi_label": 9.0,
                        "is_high_roi_opportunity": True,
                        "task_count": 20,
                    },
                ],
            )

            summary = build_intervention_plan(
                dataset_dir=dataset_dir,
                opportunity_jsonl_paths=[opportunity_jsonl],
                output_dir=root / "plan",
                report=root / "report.md",
                max_contexts=2,
                targets_per_context=2,
                min_negative_targets_per_context=2,
                include_families=["sector-wave"],
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["include_families"], ["sector-wave"])
            self.assertEqual(summary["selected_context_count"], 1)
            self.assertEqual(summary["candidate_count"], 2)
            self.assertEqual(
                {candidate["expected_context_hash"] for candidate in summary["candidates"]},
                {sector_context},
            )


def _graph_path(root: Path) -> Path:
    graph_path = (
        root
        / "tasks_020"
        / "sector-wave"
        / "apollo15_20km"
        / "apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json"
    )
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph_path.write_text(json.dumps({"tasks": []}), encoding="utf-8")
    return graph_path


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
        "true_dual_hash": f"dual-{context_hash}",
        "cut_hash": f"cut-{context_hash}",
        "branch_hash": f"branch-{context_hash}",
        "forbidden_signature_hash": f"forbidden-{context_hash}",
        "active_hash_before": f"active-{context_hash}",
        "pool_signature_hash": f"pool-sig-{context_hash}",
        "pool_task_set_hash": f"pool-task-{context_hash}",
        "cg_iter": 3,
        "pricing_kind": "exact",
        "task_count": 20,
        "pool_task_sets": [[1, 2]],
        "active_task_sets": [[1], [4]],
        "returned_journey_count": len(returned),
        "returned_journeys": returned,
        "diagnostic_only": True,
        "official_bound_effect": False,
    }


def _journey(tasks: list[int], true_rc: float, arc_kind: str) -> dict[str, object]:
    arcs = [f"0->{tasks[0]}:{arc_kind}:0"]
    arcs.extend(f"{left}->{right}:{arc_kind}:0" for left, right in zip(tasks, tasks[1:]))
    arcs.append(f"{tasks[-1]}->0:{arc_kind}:0")
    return {
        "task_set": tasks,
        "sequence": [tasks],
        "true_reduced_cost": true_rc,
        "cost": 10.0,
        "signature": [[tasks, arcs, 0.0]],
        "trips": [
            {
                "tasks": tasks,
                "start_time": 0.0,
                "arc_option_ids": arcs,
            }
        ],
    }


def _write_manifest(
    dataset_dir: Path,
    *,
    source_log: Path,
    graph_path: Path,
    context_hash: str,
    candidate_count: int,
    accepted_batch_roi: float,
) -> None:
    dataset_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "gat_batch_impact_dataset_v1",
        "sample_count": 1,
        "samples": [
            {
                "path": "samples/sample_000000.pt",
                "row_index": 0,
                "source_file": str(source_log),
                "context_hash": context_hash,
                "instance": graph_path.stem,
                "instance_path": str(graph_path),
                "instance_family": "sector-wave",
                "instance_region": "apollo15_20km",
                "task_count": 20,
                "candidate_count": candidate_count,
                "accepted_batch_roi": accepted_batch_roi,
                "label_batch_roi_positive": 1,
            }
        ],
    }
    (dataset_dir / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _append_manifest_sample(
    dataset_dir: Path,
    *,
    source_log: Path,
    graph_path: Path,
    context_hash: str,
    candidate_count: int,
    accepted_batch_roi: float,
) -> None:
    manifest_path = dataset_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sample = dict(manifest["samples"][0])
    sample.update(
        {
            "path": f"samples/sample_{len(manifest['samples']):06d}.pt",
            "row_index": len(manifest["samples"]),
            "source_file": str(source_log),
            "context_hash": context_hash,
            "instance": graph_path.stem,
            "instance_path": str(graph_path),
            "candidate_count": candidate_count,
            "accepted_batch_roi": accepted_batch_roi,
        }
    )
    manifest["samples"].append(sample)
    manifest["sample_count"] = len(manifest["samples"])
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()

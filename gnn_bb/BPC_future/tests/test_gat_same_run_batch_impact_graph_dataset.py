from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

try:
    import torch

    from BPC_future.learning.column_selector import (
        SELECTOR_CLASS_ABSTAIN,
        SELECTOR_CLASS_ADD,
    )
    from BPC_future.scripts.build_gat_same_run_batch_impact_graph_dataset import (
        build_dataset,
    )
    from BPC_future.tests.test_learning_components import _toy_payload

    HAS_LEARNING_STACK = True
except Exception:
    HAS_LEARNING_STACK = False


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


@unittest.skipUnless(HAS_LEARNING_STACK, "learning stack is not installed")
class GATSameRunBatchImpactGraphDatasetTests(unittest.TestCase):
    def test_negative_non_improving_batch_becomes_delay_queue_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            graph_path = tmp / "toy_logical_graph.json"
            graph_path.write_text(json.dumps(_toy_payload()), encoding="utf-8")
            capture_path = tmp / "capture.jsonl"
            events = [
                _capture_event(
                    graph_path=graph_path,
                    context_hash="ctx-improve",
                    cg_iter=4,
                ),
                _capture_event(
                    graph_path=graph_path,
                    context_hash="ctx-delay",
                    cg_iter=5,
                ),
            ]
            _write_jsonl(capture_path, events)
            input_rows = tmp / "rows.jsonl"
            _write_jsonl(
                input_rows,
                [
                    _same_run_row(
                        capture_path=capture_path,
                        graph_path=graph_path,
                        context_hash="ctx-improve",
                        cg_iter=4,
                        improved=True,
                    ),
                    _same_run_row(
                        capture_path=capture_path,
                        graph_path=graph_path,
                        context_hash="ctx-delay",
                        cg_iter=5,
                        improved=False,
                    ),
                ],
            )

            summary = build_dataset(
                input_jsonl=input_rows,
                output_dir=tmp / "dataset",
                report=tmp / "report.md",
            )
            manifest = json.loads((tmp / "dataset" / "manifest.json").read_text())
            samples = [
                torch.load(
                    tmp / "dataset" / item["path"],
                    map_location="cpu",
                    weights_only=False,
                )
                for item in manifest["samples"]
            ]

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["sample_count"], 2)
            self.assertEqual(summary["batch_label_counts"], {"non_improving": 1, "objective_improved": 1})
            self.assertEqual(summary["candidate_label_counts"], {"abstain": 2, "add": 2})
            self.assertEqual(summary["delay_queue_label_count"], 2)
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["certificate_ready"])
            self.assertEqual(samples[0].y_selector.tolist(), [SELECTOR_CLASS_ADD, SELECTOR_CLASS_ADD])
            self.assertEqual(
                samples[1].y_selector.tolist(),
                [SELECTOR_CLASS_ABSTAIN, SELECTOR_CLASS_ABSTAIN],
            )


def _capture_event(*, graph_path: Path, context_hash: str, cg_iter: int) -> dict[str, object]:
    return {
        "event": "journey_counterfactual_replay_capture",
        "schema_version": "journey_counterfactual_replay_capture_v1",
        "diagnostic_only": True,
        "official_bound_effect": False,
        "instance": "toy_selector_instance",
        "instance_path": str(graph_path),
        "context_hash": context_hash,
        "true_dual_hash": "dual",
        "cut_hash": "cut",
        "branch_hash": "branch",
        "forbidden_signature_hash": "forbidden",
        "cg_iter": cg_iter,
        "pricing_kind": "exact",
        "node_id": 0,
        "depth": 0,
        "pool_journey_count": 4,
        "active_basis_journey_count": 2,
        "active_basis_fractional_journey_count": 1,
        "active_task_set_count": 2,
        "rmp_objective_before": 100.0,
        "true_dual_vector": [1.0, -2.0, 3.0],
        "pool_task_sets": [[2]],
        "pool_signatures": [],
        "returned_journey_count": 2,
        "returned_journeys": [
            {
                "id": "a",
                "task_set": [1, 3],
                "cost": 10.0,
                "true_reduced_cost": -4.0,
                "signature": [["a"]],
                "trips": [{"tasks": [1, 3]}],
            },
            {
                "id": "b",
                "task_set": [2],
                "cost": 8.0,
                "true_reduced_cost": -1.5,
                "signature": [["b"]],
                "trips": [{"tasks": [2]}],
            },
        ],
    }


def _same_run_row(
    *,
    capture_path: Path,
    graph_path: Path,
    context_hash: str,
    cg_iter: int,
    improved: bool,
) -> dict[str, object]:
    return {
        "schema_version": "gat_same_run_batch_impact_row_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "source_file": str(capture_path),
        "instance": "toy_selector_instance",
        "instance_path": str(graph_path),
        "instance_region": "toy_region",
        "cg_iter": cg_iter,
        "node_id": 0,
        "depth": 0,
        "pricing_kind": "exact",
        "context_hash": context_hash,
        "true_dual_hash": "dual",
        "cut_hash": "cut",
        "branch_hash": "branch",
        "forbidden_signature_hash": "forbidden",
        "returned_journey_count": 2,
        "added_journeys": 2,
        "new_journeys": 1,
        "replacement_journeys": 1,
        "new_task_set_count": 1,
        "active_changed_task_set_count": 1 if improved else 0,
        "addition_productivity_class": "active_replacement_task_set" if improved else "changed_inactive_only",
        "best_true_reduced_cost": -4.0,
        "objective_before": 100.0,
        "objective_after": 95.0 if improved else 100.0,
        "objective_delta": -5.0 if improved else 0.0,
        "objective_improvement": 5.0 if improved else 0.0,
        "label_objective_improved": 1 if improved else 0,
        "label_active_support_changing": 1 if improved else 0,
        "label_new_task_set_added": 1,
        "same_run_intervention_observed": True,
        "training_label_allowed": True,
        "training_label_scope": "same_run_returned_batch",
    }


if __name__ == "__main__":
    unittest.main()

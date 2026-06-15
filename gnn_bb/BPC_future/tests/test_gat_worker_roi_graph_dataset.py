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
    from BPC_future.scripts.build_gat_worker_roi_graph_dataset import build_dataset
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
class GATWorkerROIGraphDatasetTests(unittest.TestCase):
    def test_roi_labels_become_high_priority_or_delay_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            graph_path = tmp / "toy_logical_graph.json"
            graph_path.write_text(json.dumps(_toy_payload()), encoding="utf-8")
            capture_path = tmp / "capture.jsonl"
            _write_jsonl(
                capture_path,
                [
                    _capture_event(graph_path=graph_path, context_hash="ctx-pos", cg_iter=3),
                    _capture_event(graph_path=graph_path, context_hash="ctx-neg", cg_iter=4),
                    _capture_event(graph_path=graph_path, context_hash="ctx-columns", cg_iter=5),
                ],
            )
            rows_path = tmp / "roi_rows.jsonl"
            _write_jsonl(
                rows_path,
                [
                    _roi_row(
                        capture_path=capture_path,
                        graph_path=graph_path,
                        context_hash="ctx-pos",
                        roi_class="positive_primal_roi",
                        label=1,
                        training_eligible=True,
                    ),
                    _roi_row(
                        capture_path=capture_path,
                        graph_path=graph_path,
                        context_hash="ctx-neg",
                        roi_class="negative_primal_roi",
                        label=0,
                        training_eligible=True,
                    ),
                    _roi_row(
                        capture_path=capture_path,
                        graph_path=graph_path,
                        context_hash="ctx-columns",
                        roi_class="columns_only_roi",
                        label=None,
                        training_eligible=False,
                        exclusion="unsupported_roi_class:columns_only_roi",
                    ),
                ],
            )

            summary = build_dataset(
                input_jsonl=rows_path,
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
            self.assertEqual(summary["candidate_label_counts"], {"abstain": 1, "add": 1})
            self.assertEqual(
                summary["skipped_counts"],
                {"not_training_eligible:unsupported_roi_class:columns_only_roi": 1},
            )
            self.assertEqual(samples[0].y_selector.tolist(), [SELECTOR_CLASS_ADD])
            self.assertEqual(samples[1].y_selector.tolist(), [SELECTOR_CLASS_ABSTAIN])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["certificate_ready"])

    def test_retry_and_merged_trajectory_labels_are_used(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            graph_path = tmp / "toy_logical_graph.json"
            graph_path.write_text(json.dumps(_toy_payload()), encoding="utf-8")
            capture_path = tmp / "capture.jsonl"
            _write_jsonl(
                capture_path,
                [
                    _capture_event(graph_path=graph_path, context_hash="ctx-retry-pos", cg_iter=3),
                    _capture_event(graph_path=graph_path, context_hash="ctx-retry-neg", cg_iter=4),
                ],
            )
            positive = _roi_row(
                capture_path=capture_path,
                graph_path=graph_path,
                context_hash="ctx-retry-pos",
                roi_class="positive_retry_roi",
                label=None,
                training_eligible=True,
            )
            positive["label_positive_trajectory_roi_merged"] = 1
            negative = _roi_row(
                capture_path=capture_path,
                graph_path=graph_path,
                context_hash="ctx-retry-neg",
                roi_class="negative_retry_roi",
                label=None,
                training_eligible=True,
            )
            negative["label_positive_trajectory_roi_merged"] = 0
            rows_path = tmp / "roi_rows.jsonl"
            _write_jsonl(rows_path, [positive, negative])

            summary = build_dataset(
                input_jsonl=rows_path,
                output_dir=tmp / "dataset",
                report=tmp / "report.md",
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["candidate_label_counts"], {"abstain": 1, "add": 1})
            self.assertEqual(summary["roi_class_counts"], {"negative_retry_roi": 1, "positive_retry_roi": 1})

    def test_missing_source_file_skips_instead_of_opening_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            graph_path = tmp / "toy_logical_graph.json"
            graph_path.write_text(json.dumps(_toy_payload()), encoding="utf-8")
            rows_path = tmp / "roi_rows.jsonl"
            row = _roi_row(
                capture_path=tmp,
                graph_path=graph_path,
                context_hash="ctx-dir",
                roi_class="positive_primal_roi",
                label=1,
                training_eligible=True,
            )
            row["source_file"] = ""
            _write_jsonl(rows_path, [row])

            summary = build_dataset(
                input_jsonl=rows_path,
                output_dir=tmp / "dataset",
                report=tmp / "report.md",
            )

            self.assertFalse(summary["all_checks_pass"])
            self.assertEqual(summary["sample_count"], 0)
            self.assertEqual(summary["skipped_counts"], {"missing_source_file": 1})


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
        "returned_journey_count": 1,
        "returned_journeys": [
            {
                "id": "target",
                "task_set": [1, 3],
                "cost": 10.0,
                "true_reduced_cost": -4.0,
                "signature": [
                    [
                        [1, 3],
                        ["0->1:a", "1->3:b", "3->0:c"],
                        0.0,
                    ]
                ],
                "trips": [
                    {
                        "tasks": [1, 3],
                        "start_time": 0.0,
                        "arc_option_ids": ["0->1:a", "1->3:b", "3->0:c"],
                    }
                ],
            }
        ],
    }


def _roi_row(
    *,
    capture_path: Path,
    graph_path: Path,
    context_hash: str,
    roi_class: str,
    label: int | None,
    training_eligible: bool,
    exclusion: str = "",
) -> dict[str, object]:
    return {
        "schema_version": "gat_worker_roi_dataset_row_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "source_file": str(capture_path),
        "instance": str(graph_path),
        "instance_family": "toy-family",
        "instance_region": "toy-region",
        "name": f"toy-{context_hash}",
        "expected_context_hash": context_hash,
        "capture_cg_iter": 3,
        "target_sequence": [1, 3],
        "target_arc_option_sequence": ["0->1:a", "1->3:b", "3->0:c"],
        "best_true_reduced_cost": -4.0,
        "roi_class": roi_class,
        "label_worker_roi_positive": label,
        "training_eligible": training_eligible,
        "training_exclusion_reason": exclusion,
        "primal_improvement": 1.0 if label == 1 else 0.0,
    }


if __name__ == "__main__":
    unittest.main()

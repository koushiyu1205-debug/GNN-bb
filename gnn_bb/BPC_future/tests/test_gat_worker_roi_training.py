from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

try:
    import torch

    from BPC_future.scripts.build_gat_worker_roi_graph_dataset import build_dataset
    from BPC_future.scripts.train_gat_worker_roi import train_worker_roi
    from BPC_future.tests.test_gat_worker_roi_graph_dataset import _capture_event, _roi_row, _write_jsonl
    from BPC_future.tests.test_learning_components import _toy_payload

    HAS_LEARNING_STACK = True
except Exception:
    HAS_LEARNING_STACK = False


@unittest.skipUnless(HAS_LEARNING_STACK, "learning stack is not installed")
class GATWorkerROITrainingTests(unittest.TestCase):
    def test_training_writes_worker_roi_checkpoint_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            graph_paths = []
            for idx in range(2):
                graph_path = tmp / f"toy_logical_graph_{idx}.json"
                graph_path.write_text(json.dumps(_toy_payload()), encoding="utf-8")
                graph_paths.append(graph_path)
            capture_path = tmp / "capture.jsonl"
            _write_jsonl(
                capture_path,
                [
                    _capture_event(graph_path=graph_paths[0], context_hash="ctx-pos-0", cg_iter=3),
                    _capture_event(graph_path=graph_paths[0], context_hash="ctx-neg-0", cg_iter=4),
                    _capture_event(graph_path=graph_paths[1], context_hash="ctx-pos-1", cg_iter=5),
                    _capture_event(graph_path=graph_paths[1], context_hash="ctx-neg-1", cg_iter=6),
                ],
            )
            rows = [
                _roi_row(
                    capture_path=capture_path,
                    graph_path=graph_paths[0],
                    context_hash="ctx-pos-0",
                    roi_class="positive_primal_roi",
                    label=1,
                    training_eligible=True,
                ),
                _roi_row(
                    capture_path=capture_path,
                    graph_path=graph_paths[0],
                    context_hash="ctx-neg-0",
                    roi_class="negative_primal_roi",
                    label=0,
                    training_eligible=True,
                ),
                _roi_row(
                    capture_path=capture_path,
                    graph_path=graph_paths[1],
                    context_hash="ctx-pos-1",
                    roi_class="positive_retry_roi",
                    label=1,
                    training_eligible=True,
                ),
                _roi_row(
                    capture_path=capture_path,
                    graph_path=graph_paths[1],
                    context_hash="ctx-neg-1",
                    roi_class="negative_retry_roi",
                    label=0,
                    training_eligible=True,
                ),
            ]
            rows_path = tmp / "roi_rows.jsonl"
            _write_jsonl(rows_path, rows)
            dataset_dir = tmp / "dataset"
            build_dataset(
                input_jsonl=rows_path,
                output_dir=dataset_dir,
                report=tmp / "dataset_report.md",
            )

            args = SimpleNamespace(
                dataset_dir=dataset_dir,
                checkpoint_out=tmp / "worker_roi_gat.pt",
                metrics_out=tmp / "metrics.json",
                report=tmp / "report.md",
                device="cpu",
                epochs=2,
                lr=1.0e-3,
                weight_decay=1.0e-5,
                hidden_dim=16,
                option_hidden_dim=16,
                pair_edge_dim=16,
                selector_hidden_dim=16,
                num_gnn_layers=1,
                heads=4,
                dropout=0.0,
                validation_fraction=0.5,
                seed=7,
                min_samples=4,
                min_positive=2,
                min_negative=2,
            )
            summary = train_worker_roi(args)

            checkpoint = torch.load(args.checkpoint_out, map_location="cpu", weights_only=False)
            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["target_label"], "paired_worker_ab_trajectory_roi")
            self.assertFalse(summary["selector_can_certificate"])
            self.assertFalse(summary["selector_is_pricing_oracle"])
            self.assertFalse(summary["gate_can_permanently_discard_negative_columns"])
            self.assertIn("model_signal_ready", summary)
            self.assertIn("priority_scheduler_ready", summary)
            self.assertTrue(summary["requires_knn_ood_shell"])
            self.assertTrue(summary["requires_5_10_no_regression"])
            self.assertTrue(summary["requires_20_roi_ab"])
            self.assertFalse(summary["production_ready"])
            self.assertEqual(checkpoint["target_label"], "paired_worker_ab_trajectory_roi")
            self.assertFalse(checkpoint["trajectory_contract"]["certificate_source"])
            self.assertFalse(checkpoint["trajectory_contract"]["pricing_oracle"])
            self.assertFalse(checkpoint["trajectory_contract"]["labels_from_rc_or_gate"])
            self.assertEqual(
                checkpoint["deployment_guard"]["priority_scheduler_ready"],
                summary["priority_scheduler_ready"],
            )
            self.assertTrue(checkpoint["deployment_guard"]["requires_knn_ood_shell"])
            self.assertFalse(checkpoint["deployment_guard"]["default_enabled"])
            self.assertIn("cannot certify", checkpoint["exactness_contract"])
            self.assertTrue(args.metrics_out.exists())
            self.assertTrue(args.report.exists())


if __name__ == "__main__":
    unittest.main()

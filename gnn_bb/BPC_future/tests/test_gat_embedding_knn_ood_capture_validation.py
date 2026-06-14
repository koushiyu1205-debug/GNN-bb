from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

try:
    from BPC_future.scripts.audit_gat_embedding_knn_ood_capture_validation import (
        audit_gat_capture_validation,
    )
    from BPC_future.scripts.build_gat_trajectory_cbf_dataset import build_dataset
    from BPC_future.scripts.train_gat_trajectory_cbf import train_trajectory_cbf
    from BPC_future.tests.test_cbf_mode_transition_audit import _capture, _journey
    from BPC_future.tests.test_gat_embedding_knn_ood_external_validation import (
        _make_capture_and_rows,
    )
    from BPC_future.tests.test_learning_components import _toy_payload

    HAS_LEARNING_STACK = True
except Exception:
    HAS_LEARNING_STACK = False


@unittest.skipUnless(HAS_LEARNING_STACK, "learning stack is not installed")
class GATEmbeddingKNNOODCaptureValidationTests(unittest.TestCase):
    def test_capture_validation_builds_gat_dataset_and_preserves_guards(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            graph_path = tmp / "toy_selector_instance_logical_graph.json"
            graph_path.write_text(json.dumps(_toy_payload()), encoding="utf-8")

            _train_capture, train_trajectory = _make_capture_and_rows(
                root=tmp,
                graph_path=graph_path,
                name="train",
                labels=[1, 0, 1, 0],
            )
            train_dir = tmp / "train_dataset"
            build_dataset(trajectory_jsonl=train_trajectory, output_dir=train_dir)
            checkpoint = tmp / "trajectory_gat.pt"
            train_trajectory_cbf(
                SimpleNamespace(
                    dataset_dir=train_dir,
                    checkpoint_out=checkpoint,
                    metrics_out=tmp / "metrics.json",
                    report=tmp / "training_report.md",
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
                    seed=17,
                )
            )

            validation_log = tmp / "validation_capture.jsonl"
            events = [
                _capture(
                    1,
                    active_hash="active-a",
                    context_hash="ctx-a",
                    objective=100.0,
                    returned=[_journey([1, 3], rc=-2.0, sequence=[[1, 3]], signature="r1")],
                    pool=[_journey([1], rc=0.0, signature="p1")],
                    active_task_sets=[[1]],
                ),
                _capture(
                    2,
                    active_hash="active-b",
                    context_hash="ctx-b",
                    objective=99.0,
                    returned=[_journey([2], rc=-1.0, signature="r2")],
                    pool=[_journey([2], rc=-0.5, signature="p2")],
                    active_task_sets=[[2]],
                ),
                _capture(
                    3,
                    active_hash="active-c",
                    context_hash="ctx-c",
                    objective=97.0,
                    returned=[_journey([1, 2], rc=-1.5, sequence=[[1, 2]], signature="r3")],
                    pool=[_journey([3], rc=0.2, signature="p3")],
                    active_task_sets=[[3]],
                ),
            ]
            for event in events:
                event["instance"] = "toy_selector_instance"
                event["instance_path"] = str(graph_path)
            validation_log.write_text(
                "\n".join(json.dumps(event, sort_keys=True) for event in events) + "\n",
                encoding="utf-8",
            )

            summary = audit_gat_capture_validation(
                train_dataset_dir=train_dir,
                checkpoint=checkpoint,
                capture_paths=[validation_log],
                output_dir=tmp / "audit",
                report=tmp / "audit.md",
                device="cpu",
                min_validation_rows=1,
                min_validation_high_priority=0,
                min_high_priority_threshold=0.5,
                knn_k=1,
                max_neighbor_unsafe_fraction=1.0,
                safe_radius_quantile=1.0,
                safe_radius_multiplier=10.0,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["active_worker_effect"])
            self.assertFalse(summary["certificate_effect"])
            self.assertEqual(summary["validation_row_count"], 1)
            self.assertTrue(summary["checks"]["trajectory_dataset_checks_pass"])
            self.assertTrue(summary["checks"]["gat_dataset_checks_pass"])
            self.assertTrue(summary["checks"]["external_validation_checks_pass"])
            self.assertTrue(summary["checks"]["gate_cannot_permanently_discard_negative_columns"])
            self.assertTrue(summary["checks"]["delay_queue_proof_budget_guard_present"])
            self.assertTrue((tmp / "audit" / "trajectory_validation_dataset").exists())
            self.assertTrue((tmp / "audit" / "gat_validation_dataset" / "manifest.json").exists())
            self.assertTrue(
                (tmp / "audit" / "gat_embedding_external_validation" / "decision_records.jsonl").exists()
            )
            self.assertTrue((tmp / "audit.md").exists())


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

try:
    from BPC_future.scripts.audit_gat_same_run_batch_impact_knn_ood import (
        audit_same_run_gat_knn_ood,
    )
    from BPC_future.scripts.build_gat_same_run_batch_impact_graph_dataset import (
        build_dataset,
    )
    from BPC_future.scripts.train_gnn_column_selector import train_selector
    from BPC_future.tests.test_gat_same_run_batch_impact_graph_dataset import (
        _capture_event,
        _same_run_row,
        _write_jsonl,
    )
    from BPC_future.tests.test_learning_components import _toy_payload

    HAS_LEARNING_STACK = True
except Exception:
    HAS_LEARNING_STACK = False


@unittest.skipUnless(HAS_LEARNING_STACK, "learning stack is not installed")
class GATSameRunBatchImpactKNNOODTests(unittest.TestCase):
    def test_knn_ood_audit_keeps_delay_queue_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            graph_path = tmp / "toy_logical_graph.json"
            graph_path.write_text(json.dumps(_toy_payload()), encoding="utf-8")
            capture_path = tmp / "capture.jsonl"
            events = []
            rows = []
            for idx, improved in enumerate([True, False, True, False, True, False]):
                context_hash = f"ctx-{idx}"
                event = _capture_event(
                    graph_path=graph_path,
                    context_hash=context_hash,
                    cg_iter=idx + 1,
                )
                row = _same_run_row(
                    capture_path=capture_path,
                    graph_path=graph_path,
                    context_hash=context_hash,
                    cg_iter=idx + 1,
                    improved=improved,
                )
                event["instance"] = f"toy_selector_instance_{idx % 2}"
                row["instance"] = f"toy_selector_instance_{idx % 2}"
                events.append(event)
                rows.append(row)
            _write_jsonl(capture_path, events)
            input_rows = tmp / "rows.jsonl"
            _write_jsonl(input_rows, rows)
            dataset_dir = tmp / "dataset"
            build_dataset(input_jsonl=input_rows, output_dir=dataset_dir, report=tmp / "dataset.md")
            checkpoint = tmp / "same_run_gat.pt"
            metrics = tmp / "training_summary.json"
            train_selector(
                SimpleNamespace(
                    dataset_dir=dataset_dir,
                    checkpoint_out=checkpoint,
                    metrics_out=metrics,
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
                    seed=3,
                )
            )

            summary = audit_same_run_gat_knn_ood(
                dataset_dir=dataset_dir,
                checkpoint=checkpoint,
                training_summary=metrics,
                output_dir=tmp / "audit",
                report=tmp / "audit.md",
                device="cpu",
                knn_k=1,
                max_neighbor_delay_fraction=1.0,
                safe_radius_multiplier=10.0,
                min_validation_high_priority=0,
                min_delay_recall=0.0,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["selector_can_certificate"])
            self.assertFalse(summary["gate_can_permanently_discard_negative_columns"])
            self.assertTrue(summary["negative_columns_must_remain_eventually_reachable"])
            self.assertEqual(summary["unsafe_negative_decision"], "DELAY_QUEUE")
            self.assertIn("validation_metrics", summary)
            self.assertEqual(summary["decision_scope"], "validation")
            self.assertEqual(summary["decision_split_counts"], {"validation": summary["decision_record_count"]})
            decision_path = tmp / "audit" / "decision_records.jsonl"
            self.assertTrue(decision_path.exists())
            first_decision = json.loads(decision_path.read_text().splitlines()[0])
            self.assertEqual(first_decision["source_file"], str(capture_path))
            self.assertIn("sample_path", first_decision)
            self.assertIn("instance_path", first_decision)
            self.assertIsInstance(first_decision["row_index"], int)
            self.assertEqual(first_decision["decision_split"], "validation")

            all_scope = audit_same_run_gat_knn_ood(
                dataset_dir=dataset_dir,
                checkpoint=checkpoint,
                training_summary=metrics,
                output_dir=tmp / "audit_all",
                report=tmp / "audit_all.md",
                device="cpu",
                knn_k=1,
                max_neighbor_delay_fraction=1.0,
                safe_radius_multiplier=10.0,
                min_validation_high_priority=0,
                min_delay_recall=0.0,
                decision_scope="all",
            )
            self.assertEqual(all_scope["decision_scope"], "all")
            self.assertEqual(all_scope["decision_record_count"], all_scope["train_row_count"] + all_scope["validation_row_count"])
            self.assertIn("train", all_scope["decision_split_counts"])
            self.assertIn("validation", all_scope["decision_split_counts"])


if __name__ == "__main__":
    unittest.main()

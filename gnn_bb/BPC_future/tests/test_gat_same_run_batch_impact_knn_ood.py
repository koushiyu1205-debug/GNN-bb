from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

try:
    from BPC_future.scripts.audit_gat_same_run_batch_impact_knn_ood import (
        _build_guard_model,
        _guard_for_record,
        _record_group_key,
        _safety_shell_metrics,
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
    def test_safety_shell_metrics_are_computed_separately_from_classifier_f1(self) -> None:
        records = [
            {
                "decision": 1,
                "label_high_priority": 1,
                "is_ood": False,
                "is_knn_unsafe": False,
            },
            {
                "decision": 1,
                "label_high_priority": 0,
                "is_ood": True,
                "is_knn_unsafe": False,
            },
            {
                "decision": 0,
                "label_high_priority": 0,
                "is_ood": False,
                "is_knn_unsafe": True,
            },
            {
                "decision": 0,
                "label_high_priority": 1,
                "is_ood": True,
                "is_knn_unsafe": True,
            },
        ]

        metrics = _safety_shell_metrics(records)

        self.assertEqual(metrics["accepted_batch_count"], 2)
        self.assertEqual(metrics["accepted_batch_roi_positive_count"], 1)
        self.assertEqual(metrics["safe_precision"], 0.5)
        self.assertEqual(metrics["accepted_batch_roi"], 0.5)
        self.assertEqual(metrics["coverage_non_ood_count"], 2)
        self.assertEqual(metrics["coverage"], 0.5)
        self.assertEqual(metrics["delay_rate"], 0.5)
        self.assertEqual(metrics["false_safe_rate_ood"], 0.5)
        self.assertEqual(metrics["false_safe_rate_knn_unsafe"], 0.0)
        self.assertEqual(metrics["false_safe_rate_label_unsafe"], 0.5)
        self.assertEqual(metrics["false_safe_rate_union"], 1.0 / 3.0)

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
            self.assertIn("validation_safety_shell_metrics", summary)
            self.assertIn("decision_scope_safety_shell_metrics", summary)
            self.assertIn("validation_false_safe_rates", summary)
            self.assertIn("high_priority_f0p5", summary["validation_metrics"])
            for key in (
                "safe_precision",
                "false_safe_rate_ood",
                "false_safe_rate_knn_unsafe",
                "false_safe_rate_label_unsafe",
                "false_safe_rate_union",
                "false_positive_context_count",
                "coverage",
                "delay_rate",
                "accepted_batch_count",
                "accepted_batch_roi",
            ):
                self.assertIn(key, summary["validation_safety_shell_metrics"])
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
            self.assertIn("decision_name", first_decision)
            self.assertIn("is_ood", first_decision)
            self.assertIn("is_knn_unsafe", first_decision)
            self.assertIn("is_label_unsafe", first_decision)
            self.assertIn("instance_task_count", first_decision)
            self.assertIn("instance_family", first_decision)
            self.assertEqual(first_decision["threshold_scope"], "global")

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
            self.assertIn("accepted_batch_count", all_scope["decision_scope_safety_shell_metrics"])

    def test_grouped_threshold_guard_uses_sparse_group_fallback(self) -> None:
        def record(instance_path: str, label: int, probability: float, embedding: list[float]) -> dict:
            return {
                "instance": Path(instance_path).stem,
                "instance_path": instance_path,
                "context_hash": "ctx",
                "sample_path": "samples/sample.pt",
                "source_file": "source.jsonl",
                "row_index": 0,
                "label_high_priority": label,
                "probability": probability,
                "embedding": embedding,
            }

        good_group_pos = record(
            "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/a_tasks020_logical_graph.json",
            1,
            0.80,
            [0.0, 0.0],
        )
        good_group_neg = record(
            "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/b_tasks020_logical_graph.json",
            0,
            0.20,
            [1.0, 1.0],
        )
        sparse_group_pos = record(
            "BPC_future/logical_graph/tasks_050/sector-wave/apollo15_20km/c_tasks050_logical_graph.json",
            1,
            0.90,
            [2.0, 2.0],
        )
        model = _build_guard_model(
            train_records=[good_group_pos, good_group_neg, sparse_group_pos],
            threshold_grouping="scale_family",
            safe_radius_quantile=1.0,
            safe_radius_multiplier=10.0,
            knn_k=1,
        )

        self.assertEqual(_record_group_key(good_group_pos, "scale_family"), "020|random-wave")
        self.assertIn("020|random-wave", model["groups"])
        self.assertIn("050|sector-wave", model["skipped_groups"])
        self.assertIs(_guard_for_record(model, good_group_pos), model["groups"]["020|random-wave"])
        self.assertIs(_guard_for_record(model, sparse_group_pos), model["global"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

try:
    import torch

    from BPC_future.scripts.audit_gat_worker_roi_knn_ood import (
        _build_guard_model,
        _guard_for_record,
        _record_group_key,
        _safety_shell_metrics,
        audit_worker_roi_knn_ood,
    )
    from BPC_future.scripts.build_gat_worker_roi_graph_dataset import build_dataset
    from BPC_future.scripts.train_gat_worker_roi import train_worker_roi
    from BPC_future.tests.test_gat_worker_roi_graph_dataset import _capture_event, _roi_row, _write_jsonl
    from BPC_future.tests.test_learning_components import _toy_payload

    HAS_LEARNING_STACK = True
except Exception:
    HAS_LEARNING_STACK = False


@unittest.skipUnless(HAS_LEARNING_STACK, "learning stack is not installed")
class GATWorkerROIKNNOODTests(unittest.TestCase):
    def test_worker_roi_safety_shell_metrics_are_not_plain_f1(self) -> None:
        records = [
            {
                "decision": 1,
                "label_worker_roi_positive": 1,
                "is_ood": False,
                "is_knn_unsafe": False,
                "is_label_unsafe": False,
            },
            {
                "decision": 1,
                "label_worker_roi_positive": 0,
                "is_ood": True,
                "is_knn_unsafe": False,
                "is_label_unsafe": True,
            },
            {
                "decision": 0,
                "label_worker_roi_positive": 0,
                "is_ood": False,
                "is_knn_unsafe": True,
                "is_label_unsafe": True,
            },
            {
                "decision": 0,
                "label_worker_roi_positive": 1,
                "is_ood": True,
                "is_knn_unsafe": True,
                "is_label_unsafe": False,
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

    def test_worker_roi_knn_ood_preserves_delay_queue_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            graph_paths = []
            for idx in range(4):
                graph_path = tmp / f"toy_logical_graph_{idx}.json"
                graph_path.write_text(json.dumps(_toy_payload()), encoding="utf-8")
                graph_paths.append(graph_path)
            capture_path = tmp / "capture.jsonl"
            _write_jsonl(
                capture_path,
                [
                    _capture_event(graph_path=graph_paths[0], context_hash="ctx-pos-0", cg_iter=3),
                    _capture_event(graph_path=graph_paths[1], context_hash="ctx-neg-0", cg_iter=4),
                    _capture_event(graph_path=graph_paths[2], context_hash="ctx-pos-1", cg_iter=5),
                    _capture_event(graph_path=graph_paths[3], context_hash="ctx-neg-1", cg_iter=6),
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
                    graph_path=graph_paths[1],
                    context_hash="ctx-neg-0",
                    roi_class="negative_primal_roi",
                    label=0,
                    training_eligible=True,
                ),
                _roi_row(
                    capture_path=capture_path,
                    graph_path=graph_paths[2],
                    context_hash="ctx-pos-1",
                    roi_class="positive_retry_roi",
                    label=1,
                    training_eligible=True,
                ),
                _roi_row(
                    capture_path=capture_path,
                    graph_path=graph_paths[3],
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
            checkpoint = tmp / "worker_roi_gat.pt"
            training_summary = train_worker_roi(
                SimpleNamespace(
                    dataset_dir=dataset_dir,
                    checkpoint_out=checkpoint,
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
                    positive_loss_multiplier=1.0,
                )
            )
            summary = audit_worker_roi_knn_ood(
                dataset_dir=dataset_dir,
                checkpoint=checkpoint,
                training_summary=tmp / "metrics.json",
                output_dir=tmp / "audit",
                report=tmp / "audit.md",
                device="cpu",
                knn_k=1,
                max_neighbor_delay_fraction=1.0,
                safe_radius_quantile=1.0,
                safe_radius_multiplier=10.0,
                min_validation_high_priority=0,
                min_add_recall=0.0,
                max_false_high_priority_rate=1.0,
                max_validation_false_safe_rate=1.0,
                decision_scope="all",
            )

            self.assertTrue(training_summary["all_checks_pass"])
            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["selector_can_certificate"])
            self.assertFalse(summary["selector_is_pricing_oracle"])
            self.assertFalse(summary["gate_can_permanently_discard_negative_columns"])
            self.assertTrue(summary["negative_columns_must_remain_eventually_reachable"])
            self.assertEqual(summary["target_label"], "paired_worker_ab_trajectory_roi")
            self.assertIn("validation_safety_shell_metrics", summary)
            self.assertIn("decision_scope_safety_shell_metrics", summary)
            self.assertIn("validation_false_safe_rates", summary)
            self.assertIn("add_f0p5", summary["validation_metrics"])
            self.assertIn("false_positive_context_count", summary["validation_metrics"])
            for metrics in (
                summary["validation_safety_shell_metrics"],
                summary["decision_scope_safety_shell_metrics"],
            ):
                self.assertIn("safe_precision", metrics)
                self.assertIn("false_safe_rate_ood", metrics)
                self.assertIn("false_safe_rate_knn_unsafe", metrics)
                self.assertIn("false_safe_rate_label_unsafe", metrics)
                self.assertIn("false_safe_rate_union", metrics)
                self.assertIn("coverage", metrics)
                self.assertIn("delay_rate", metrics)
                self.assertIn("accepted_batch_count", metrics)
                self.assertIn("accepted_batch_roi", metrics)
                self.assertIn("harmful_batch_recall", metrics)
            self.assertTrue((tmp / "audit" / "decision_records.jsonl").exists())
            decision_records = [
                json.loads(line)
                for line in (tmp / "audit" / "decision_records.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertTrue(decision_records)
            self.assertIn("is_ood", decision_records[0])
            self.assertIn("is_knn_unsafe", decision_records[0])
            self.assertIn("is_label_unsafe", decision_records[0])
            self.assertIn("target_sequence", decision_records[0])
            self.assertIn("target_arc_option_sequence", decision_records[0])
            self.assertIn("expected_context_hash", decision_records[0])
            self.assertEqual(decision_records[0]["capture_pricing_kind"], "exact")
            self.assertEqual(decision_records[0]["true_dual_hash"], "dual")
            self.assertEqual(decision_records[0]["cut_hash"], "cut")
            self.assertEqual(decision_records[0]["branch_hash"], "branch")
            self.assertEqual(decision_records[0]["forbidden_signature_hash"], "forbidden")
            self.assertEqual(
                decision_records[0]["target_sortie_traces"],
                [
                    {
                        "sequence": [1, 3],
                        "start_time": 0.0,
                        "arc_option_sequence": ["0->1:a", "1->3:b", "3->0:c"],
                    }
                ],
            )
            self.assertTrue((tmp / "audit.md").exists())

    def test_worker_roi_knn_ood_rejects_non_worker_roi_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            dataset_dir = tmp / "dataset"
            dataset_dir.mkdir()
            (dataset_dir / "manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": "gat_worker_roi_graph_dataset_manifest_v1",
                        "samples": [],
                    }
                ),
                encoding="utf-8",
            )
            checkpoint = tmp / "bad.pt"
            torch.save(
                {
                    "target_label": "label_horizon_cbf_feasible",
                    "trajectory_contract": {
                        "labels_from_rc_or_gate": False,
                        "certificate_source": False,
                        "pricing_oracle": False,
                    },
                },
                checkpoint,
            )
            training_summary = tmp / "summary.json"
            training_summary.write_text(
                json.dumps(
                    {
                        "target_label": "paired_worker_ab_trajectory_roi",
                        "production_ready": False,
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "paired_worker_ab_trajectory_roi"):
                audit_worker_roi_knn_ood(
                    dataset_dir=dataset_dir,
                    checkpoint=checkpoint,
                    training_summary=training_summary,
                    output_dir=tmp / "audit",
                    report=tmp / "audit.md",
                    device="cpu",
                )

    def test_worker_roi_grouped_guard_uses_sparse_group_fallback(self) -> None:
        def record(source_file: str, family: str, label: int, score: float, embedding: list[float]) -> dict:
            return {
                "name": Path(source_file).stem,
                "instance": Path(source_file).stem,
                "source_file": source_file,
                "instance_family": family,
                "label_worker_roi_positive": label,
                "score": score,
                "embedding": embedding,
            }

        good_group_pos = record(
            "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/a_tasks020_logical_graph.json",
            "random-wave",
            1,
            0.80,
            [0.0, 0.0],
        )
        good_group_neg = record(
            "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/b_tasks020_logical_graph.json",
            "random-wave",
            0,
            0.20,
            [1.0, 1.0],
        )
        sparse_group_pos = record(
            "BPC_future/logical_graph/tasks_050/sector-wave/apollo15_20km/c_tasks050_logical_graph.json",
            "sector-wave",
            1,
            0.90,
            [2.0, 2.0],
        )
        model = _build_guard_model(
            train_records=[good_group_pos, good_group_neg, sparse_group_pos],
            threshold_grouping="scale_family",
            safe_radius_quantile=1.0,
            safe_radius_multiplier=10.0,
            fallback_threshold=0.5,
            threshold_selection="zero_fp",
            knn_k=1,
        )

        self.assertEqual(_record_group_key(good_group_pos, "scale_family"), "020|random-wave")
        self.assertIn("020|random-wave", model["groups"])
        self.assertIn("050|sector-wave", model["skipped_groups"])
        self.assertIs(_guard_for_record(model, good_group_pos), model["groups"]["020|random-wave"])
        self.assertIs(_guard_for_record(model, sparse_group_pos), model["global"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

try:
    from BPC_future.scripts.audit_gat_batch_impact_knn_ood import (
        _apply_threshold_overrides,
        _decision_metrics,
        _family_metrics,
        _neighbor_roi_stats,
        audit_batch_impact_knn_ood,
    )
    from BPC_future.scripts.build_gat_batch_impact_dataset import build_dataset
    from BPC_future.scripts.train_gat_batch_impact import train_batch_impact
    from BPC_future.tests.test_gat_batch_impact_dataset import (
        _capture_event,
        _journey,
        _row,
        _write_jsonl,
    )
    from BPC_future.tests.test_learning_components import _toy_payload

    HAS_LEARNING_STACK = True
except Exception:
    HAS_LEARNING_STACK = False


@unittest.skipUnless(HAS_LEARNING_STACK, "learning stack is not installed")
class GATBatchImpactKNNOODTests(unittest.TestCase):
    def test_threshold_overrides_support_rescue_window_audit(self) -> None:
        thresholds = {
            "batch_threshold": 0.8,
            "candidate_threshold": 0.7,
            "candidate_admission_score_mode": "risk_adjusted_product",
            "candidate_delay_score_penalty": 1.0,
            "candidate_delay_gate_enabled": False,
            "candidate_delay_risk_threshold": 1.0,
            "candidate_rescue_raw_score_threshold": 1.0,
            "candidate_rescue_delay_risk_threshold": 1.0,
            "candidate_rescue_delay_score_penalty": 0.0,
        }

        overridden = _apply_threshold_overrides(
            thresholds,
            {
                "candidate_admission_score_mode": "risk_adjusted_rescue_window",
                "candidate_delay_score_penalty": 0.75,
                "candidate_delay_gate_enabled": True,
                "candidate_delay_risk_threshold": 0.4,
                "candidate_rescue_raw_score_threshold": 0.3,
                "candidate_rescue_delay_risk_threshold": 1.5,
                "candidate_rescue_delay_score_penalty": -2.0,
            },
        )

        self.assertEqual(overridden["batch_threshold"], 0.8)
        self.assertEqual(overridden["candidate_threshold"], 0.7)
        self.assertEqual(overridden["candidate_admission_score_mode"], "risk_adjusted_rescue_window")
        self.assertEqual(overridden["candidate_delay_score_penalty"], 0.75)
        self.assertTrue(overridden["candidate_delay_gate_enabled"])
        self.assertEqual(overridden["candidate_delay_risk_threshold"], 0.4)
        self.assertEqual(overridden["candidate_rescue_raw_score_threshold"], 0.3)
        self.assertEqual(overridden["candidate_rescue_delay_risk_threshold"], 1.0)
        self.assertEqual(overridden["candidate_rescue_delay_score_penalty"], 0.0)

    def test_neighbor_roi_stats_uses_nearest_training_records(self) -> None:
        stats = _neighbor_roi_stats(
            [[0.0], [10.0], [0.2]],
            [4.0, -10.0, 2.0],
            [0.1],
            k=2,
        )

        self.assertEqual(stats["neighbor_accepted_batch_roi_count"], 2)
        self.assertEqual(stats["neighbor_accepted_batch_roi_mean"], 3.0)
        self.assertLess(stats["neighbor_accepted_batch_roi_ci_low"], 3.0)

    def test_decision_metrics_track_safety_shell_separately_from_roi(self) -> None:
        records = [
            {
                "decision": 1,
                "label_high_priority": 1,
                "accepted_batch_roi_label": 1.2,
                "is_ood": False,
                "is_knn_unsafe": False,
                "is_label_unsafe": False,
                "candidate_delay_label_count": 2,
                "candidate_false_high_priority_on_delay_count": 0,
            },
            {
                "decision": 1,
                "label_high_priority": 0,
                "accepted_batch_roi_label": -0.3,
                "is_ood": True,
                "is_knn_unsafe": False,
                "is_label_unsafe": True,
                "candidate_delay_label_count": 2,
                "candidate_false_high_priority_on_delay_count": 1,
                "context_hash": "bad",
            },
            {
                "decision": 0,
                "label_high_priority": 0,
                "accepted_batch_roi_label": 0.0,
                "is_ood": False,
                "is_knn_unsafe": True,
                "is_label_unsafe": True,
                "candidate_delay_label_count": 2,
                "candidate_false_high_priority_on_delay_count": 0,
            },
        ]

        metrics = _decision_metrics(records)

        self.assertEqual(metrics["accepted_batch_count"], 2)
        self.assertEqual(metrics["accepted_batch_roi_positive_count"], 1)
        self.assertAlmostEqual(metrics["accepted_batch_roi"], 0.45)
        self.assertEqual(metrics["safe_precision"], 0.5)
        self.assertLess(metrics["safe_precision_ci_low"], metrics["safe_precision"])
        self.assertLess(metrics["accepted_batch_roi_ci_low"], metrics["accepted_batch_roi"])
        self.assertEqual(metrics["false_safe_rate_label_unsafe"], 0.5)
        self.assertEqual(metrics["false_high_priority_on_delay"], 1.0 / 6.0)
        self.assertEqual(metrics["false_positive_contexts"], ["bad"])

    def test_family_metrics_distinguish_delay_fallback_from_missed_opportunity(self) -> None:
        def record(family: str, decision: int, roi: float) -> dict[str, object]:
            return {
                "instance_family": family,
                "decision": decision,
                "label_high_priority": 1,
                "accepted_batch_roi_label": roi,
                "is_ood": False,
                "is_knn_unsafe": False,
                "is_label_unsafe": False,
                "candidate_delay_label_count": 0,
                "candidate_false_high_priority_on_delay_count": 0,
            }

        metrics = _family_metrics(
            [
                record("greedy-anchor", 0, 0.05),
                record("random-wave", 1, 1.0),
                record("sector-wave", 0, 1.0),
            ],
            min_accepted_batch_roi=0.65,
        )

        self.assertEqual(metrics["missing_accepted_families"], ["greedy-anchor", "sector-wave"])
        self.assertEqual(metrics["family_specific_delay_fallback_families"], ["greedy-anchor"])
        self.assertEqual(metrics["missing_accepted_opportunity_families"], ["sector-wave"])
        self.assertEqual(metrics["oracle_high_roi_families"], ["random-wave", "sector-wave"])

    def test_knn_ood_audit_preserves_batch_impact_exactness_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            source_log = tmp / "events.jsonl"
            rows_jsonl = tmp / "rows.jsonl"
            graph_paths = []
            events = []
            rows = []
            for idx in range(4):
                family = "greedy-anchor" if idx % 2 == 0 else "random-wave"
                graph_path = tmp / "tasks_020" / family / "apollo" / f"graph_{idx}.json"
                graph_path.parent.mkdir(parents=True, exist_ok=True)
                graph_path.write_text(json.dumps(_toy_payload()), encoding="utf-8")
                graph_paths.append(graph_path)
                improved = idx != 1
                context_hash = f"ctx-{idx}"
                events.append(
                    _capture_event(
                        graph_path=graph_path,
                        context_hash=context_hash,
                        cg_iter=idx + 1,
                        instance=f"inst-{idx}",
                        returned=[
                            _journey(f"j{idx}a", [1, 3], -2.0, [[1, 3]]),
                            _journey(f"j{idx}b", [2], -0.5, [[2]]),
                        ],
                    )
                )
                rows.append(
                    _row(
                        source_file=source_log,
                        graph_path=graph_path,
                        context_hash=context_hash,
                        cg_iter=idx + 1,
                        instance=f"inst-{idx}",
                        region="apollo15_20km",
                        objective_improvement=4.0 if improved else 0.0,
                        label_objective_improved=1 if improved else 0,
                        active_changed_task_set_count=1,
                        new_task_set_count=1 if improved else 0,
                        replacement_journeys=0 if improved else 1,
                    )
                )
            _write_jsonl(source_log, events)
            _write_jsonl(rows_jsonl, rows)
            dataset_dir = tmp / "dataset"
            build_dataset(
                input_jsonl=rows_jsonl,
                output_dir=dataset_dir,
                report=tmp / "dataset.md",
                min_samples_for_training=1,
                min_positive_batches_for_training=1,
                min_delay_candidates_for_training=1,
            )
            checkpoint = tmp / "gat_batch_impact.pt"
            metrics = tmp / "training_summary.json"
            train_batch_impact(
                SimpleNamespace(
                    dataset_dir=dataset_dir,
                    checkpoint_out=checkpoint,
                    metrics_out=metrics,
                    report=tmp / "training.md",
                    device="cpu",
                    epochs=1,
                    lr=1.0e-3,
                    weight_decay=1.0e-5,
                    hidden_dim=16,
                    option_hidden_dim=16,
                    pair_edge_dim=16,
                    candidate_hidden_dim=12,
                    context_hidden_dim=8,
                    batch_hidden_dim=12,
                    impact_hidden_dim=10,
                    num_gnn_layers=1,
                    heads=4,
                    dropout=0.0,
                    validation_fraction=0.5,
                    seed=13,
                    min_samples=1,
                    stage3_min_samples=1,
                    min_roi_positive_batches=1,
                    min_delay_candidates=1,
                    min_major_families=1,
                    min_validation_high_priority_precision=0.0,
                    min_validation_safe_precision=0.0,
                    max_false_high_priority_on_delay=1.0,
                    max_false_safe_union_rate=1.0,
                    min_accepted_batch_count=0,
                    min_accepted_batch_rate=0.0,
                    min_accepted_batch_roi=0.0,
                    baseline_accepted_batch_roi=0.0,
                    min_roi_margin_over_baseline=0.0,
                    min_family_holdout_precision=0.0,
                    min_family_holdout_accepted_roi=-1.0,
                    false_high_priority_loss_multiplier=2.0,
                    bad_mode_loss_multiplier=1.0,
                    regression_loss_multiplier=0.05,
                    max_grad_norm=5.0,
                    max_nonfinite_skipped_update_rate=1.0,
                )
            )

            summary = audit_batch_impact_knn_ood(
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
                min_safe_precision=0.0,
                min_accepted_batch_count=0,
                min_accepted_batch_rate=0.0,
                min_accepted_batch_roi=-1.0,
                max_false_high_priority_on_delay=1.0,
                max_validation_false_safe_rate=1.0,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["default_enabled"])
            self.assertFalse(summary["selector_can_certificate"])
            self.assertFalse(summary["gate_can_permanently_discard_negative_columns"])
            self.assertTrue(summary["negative_columns_must_remain_eventually_reachable"])
            self.assertEqual(summary["target_label"], "same_context_batch_trajectory_roi")
            self.assertIn("validation_metrics", summary)
            self.assertIn("validation_false_safe_rates", summary)
            self.assertIn("validation_family_metrics", summary)
            self.assertIn("validation_safety_checks", summary)
            self.assertIsNone(summary["min_neighbor_accepted_batch_roi"])
            self.assertIsNone(summary["min_neighbor_accepted_batch_roi_ci_low"])
            decision_path = tmp / "audit" / "decision_records.jsonl"
            self.assertTrue(decision_path.exists())
            first_decision = json.loads(decision_path.read_text().splitlines()[0])
            self.assertIn("decision_name", first_decision)
            self.assertIn("is_ood", first_decision)
            self.assertIn("is_knn_unsafe", first_decision)
            self.assertIn("is_knn_roi_unsafe", first_decision)
            self.assertIn("neighbor_accepted_batch_roi_ci_low", first_decision)
            self.assertIn("candidate_false_high_priority_on_delay_count", first_decision)
            self.assertIn("candidate_signature_ids", first_decision)
            self.assertIn("high_priority_candidate_signature_ids", first_decision)
            self.assertTrue(first_decision["candidate_signature_ids_complete"])


if __name__ == "__main__":
    unittest.main()

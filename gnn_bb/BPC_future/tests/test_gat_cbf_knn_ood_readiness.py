from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_gat_cbf_knn_ood_readiness import (
    audit_gat_cbf_knn_ood_readiness,
)


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return path


def _checkpoint_metadata(*, horizon_target: bool = False) -> dict[str, object]:
    payload: dict[str, object] = {
        "version": "test_checkpoint_v1",
        "selector_class_names": ["skip", "add", "abstain"],
        "exactness_contract": (
            "Heuristic RMP-impact predictor only; never a pricing oracle, "
            "certificate source, or official lower-bound source."
        ),
        "model_config": {
            "node_dim": 9,
            "option_dim": 10,
            "candidate_feature_dim": 10,
            "context_feature_dim": 17,
        },
        "training": {
            "split": {
                "train_instances": ["train_instance"],
                "validation_instances": ["validation_instance"],
            }
        },
    }
    if horizon_target:
        payload["target_label"] = "label_horizon_cbf_feasible"
    return payload


def _trajectory_summary(*, rows: int = 120) -> dict[str, object]:
    return {
        "all_checks_pass": True,
        "diagnostic_only": True,
        "row_count": rows,
        "horizon_cbf_feasible_count": 12,
        "horizon_cbf_infeasible_count": 20,
        "production_ready": False,
        "checks": {
            "all_rows_no_certificate_effect": True,
            "diagnostic_only": True,
            "rows_require_full_horizon": True,
            "runs_bpc_or_pricing_false": True,
        },
    }


def _knn_ood_summary(*, predicted_positive: int) -> dict[str, object]:
    return {
        "all_checks_pass": True,
        "diagnostic_only": True,
        "production_ready": False,
        "checks": {
            "delay_queue_proof_budget_guard_present": True,
            "diagnostic_only": True,
            "external_validation_checks_pass": True,
            "no_certificate_effect": True,
            "runs_bpc_or_pricing_false": True,
            "trajectory_dataset_checks_pass": True,
        },
        "external_validation_summary": {
            "all_checks_pass": True,
            "validation_candidate_ready": predicted_positive > 0,
            "validation_row_count": 8,
            "production_ready": False,
            "validation_metrics": {
                "overall": {
                    "predicted_positive": predicted_positive,
                    "fp": 0,
                    "tp": predicted_positive,
                    "fn": 0,
                }
            },
            "checks": {
                "delay_queue_exactness_guard_present": True,
                "delay_queue_proof_budget_guard_present": True,
                "uses_horizon_labels": True,
                "validation_rows_no_certificate_effect": True,
            },
        },
    }


class GATCBFKNNOODReadinessTests(unittest.TestCase):
    def test_current_column_selector_contract_is_not_trajectory_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            manifest = _write_json(
                tmp / "manifest.json",
                {
                    "candidate_feature_schema": ["true_reduced_cost", "cost"],
                    "label_counts": {"add": 3, "skip": 2},
                    "sample_count": 5,
                    "instance_counts": {"i1": 5},
                },
            )
            selector_summary = _write_json(
                tmp / "selector_summary.json",
                {
                    "schema_version": "gnn_column_selector_dataset_summary_v1",
                    "diagnostic_only": True,
                    "runs_bpc_or_pricing": False,
                    "sample_count": 5,
                    "label_counts": {"add": 3, "skip": 2},
                },
            )
            checkpoint = _write_json(tmp / "checkpoint.json", _checkpoint_metadata())
            trajectory = _write_json(tmp / "trajectory.json", _trajectory_summary(rows=140))
            knn = _write_json(tmp / "knn.json", _knn_ood_summary(predicted_positive=0))
            gat_embedding = _write_json(
                tmp / "gat_embedding.json",
                {
                    "all_checks_pass": True,
                    "validation_candidate_ready": False,
                    "validation_row_count": 2,
                    "official_bound_effect": False,
                    "validation_metrics": {"overall": {"predicted_positive": 0, "fp": 0}},
                },
            )

            summary = audit_gat_cbf_knn_ood_readiness(
                selector_manifest=manifest,
                selector_summary=selector_summary,
                checkpoint=checkpoint,
                trajectory_summary=trajectory,
                knn_ood_summary=knn,
                gat_embedding_validation_summary=gat_embedding,
                gat_embedding_capture_validation_summary=tmp / "missing_capture_summary.json",
                output_dir=tmp / "out",
                report=tmp / "report.md",
                min_trajectory_rows=100,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["embedding_candidate_ready"])
            self.assertFalse(summary["production_ready"])
            self.assertTrue(summary["selector_dataset_contract"]["column_level_add_skip_dataset"])
            self.assertFalse(summary["selector_dataset_contract"]["has_horizon_cbf_label"])
            self.assertIn(
                "gat_checkpoint_is_column_level_add_skip_not_trajectory_cbf",
                summary["production_blockers"],
            )
            self.assertIn(
                "sector_wave_knn_ood_smoke_has_no_high_priority_productivity_signal",
                summary["production_blockers"],
            )
            self.assertFalse(summary["relationship"]["pricing_oracle"])
            self.assertFalse(summary["relationship"]["certificate_source"])
            self.assertTrue((tmp / "out" / "summary.json").exists())
            self.assertTrue((tmp / "report.md").exists())

    def test_trajectory_gat_can_only_be_embedding_candidate_under_safety_shell(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            manifest = _write_json(
                tmp / "manifest.json",
                {
                    "schema_version": "gat_trajectory_cbf_dataset_manifest_v1",
                    "label_schema": ["label_horizon_cbf_feasible"],
                    "sample_count": 120,
                    "instance_counts": {"i1": 60, "i2": 60},
                    "label_counts": {"add": 60, "skip": 60},
                },
            )
            selector_summary = _write_json(
                tmp / "selector_summary.json",
                {
                    "schema_version": "gat_trajectory_cbf_dataset_summary_v1",
                    "diagnostic_only": True,
                    "runs_bpc_or_pricing": False,
                    "sample_count": 120,
                    "instance_count": 2,
                },
            )
            checkpoint = _write_json(
                tmp / "checkpoint.json",
                _checkpoint_metadata(horizon_target=True),
            )
            trajectory = _write_json(tmp / "trajectory.json", _trajectory_summary(rows=120))
            knn = _write_json(tmp / "knn.json", _knn_ood_summary(predicted_positive=4))
            gat_embedding = _write_json(
                tmp / "gat_embedding.json",
                {
                    "all_checks_pass": True,
                    "validation_candidate_ready": True,
                    "validation_row_count": 4,
                    "official_bound_effect": False,
                    "delay_queue_can_extend_proof_budget": False,
                    "delay_queue_runs_proof_sweep": False,
                    "validation_metrics": {
                        "overall": {
                            "predicted_positive": 2,
                            "fp": 0,
                            "precision": 1.0,
                            "recall": 0.5,
                        }
                    },
                },
            )

            summary = audit_gat_cbf_knn_ood_readiness(
                selector_manifest=manifest,
                selector_summary=selector_summary,
                checkpoint=checkpoint,
                trajectory_summary=trajectory,
                knn_ood_summary=knn,
                gat_embedding_validation_summary=gat_embedding,
                gat_embedding_capture_validation_summary=tmp / "missing_capture_summary.json",
                output_dir=tmp / "out",
                report=tmp / "report.md",
                min_trajectory_rows=100,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertTrue(summary["embedding_candidate_ready"])
            self.assertFalse(summary["production_ready"])
            self.assertTrue(summary["selector_dataset_contract"]["ready_for_trajectory_gat_training"])
            self.assertTrue(summary["selector_dataset_contract"]["trajectory_horizon_cbf_dataset"])
            self.assertFalse(summary["selector_dataset_contract"]["column_level_add_skip_dataset"])
            self.assertTrue(summary["checkpoint_contract"]["has_horizon_cbf_target"])
            self.assertTrue(summary["knn_ood_shell_contract"]["has_productivity_signal"])
            self.assertTrue(summary["gat_embedding_validation_contract"]["validation_candidate_ready"])
            self.assertEqual(
                summary["gat_embedding_validation_contract"]["evidence_source"],
                "external_validation",
            )
            self.assertNotIn(
                "gat_checkpoint_is_column_level_add_skip_not_trajectory_cbf",
                summary["production_blockers"],
            )
            self.assertNotIn(
                "no_gat_embedding_knn_ood_external_validation_yet",
                summary["production_blockers"],
            )
            self.assertIn("no_5_10_no_regression_bpc_ab_yet", summary["production_blockers"])
            self.assertIn("no_20_task_wall_time_roi_ab_yet", summary["production_blockers"])

    def test_capture_validation_summary_is_stronger_gat_embedding_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            manifest = _write_json(
                tmp / "manifest.json",
                {
                    "schema_version": "gat_trajectory_cbf_dataset_manifest_v1",
                    "label_schema": ["label_horizon_cbf_feasible"],
                    "sample_count": 120,
                    "instance_counts": {"i1": 60, "i2": 60},
                    "label_counts": {"add": 60, "skip": 60},
                },
            )
            selector_summary = _write_json(
                tmp / "selector_summary.json",
                {
                    "schema_version": "gat_trajectory_cbf_dataset_summary_v1",
                    "diagnostic_only": True,
                    "runs_bpc_or_pricing": False,
                    "sample_count": 120,
                    "instance_count": 2,
                },
            )
            checkpoint = _write_json(
                tmp / "checkpoint.json",
                _checkpoint_metadata(horizon_target=True),
            )
            trajectory = _write_json(tmp / "trajectory.json", _trajectory_summary(rows=120))
            knn = _write_json(tmp / "knn.json", _knn_ood_summary(predicted_positive=0))
            stale_external = _write_json(
                tmp / "stale_external.json",
                {
                    "all_checks_pass": True,
                    "validation_candidate_ready": False,
                    "validation_row_count": 8,
                    "official_bound_effect": False,
                    "delay_queue_can_extend_proof_budget": False,
                    "delay_queue_runs_proof_sweep": False,
                    "validation_metrics": {"overall": {"predicted_positive": 0, "fp": 0}},
                },
            )
            capture_validation = _write_json(
                tmp / "capture_validation.json",
                {
                    "all_checks_pass": True,
                    "validation_candidate_ready": True,
                    "validation_row_count": 8,
                    "production_ready": False,
                    "official_bound_effect": False,
                    "delay_queue_can_extend_proof_budget": False,
                    "delay_queue_runs_proof_sweep": False,
                    "checks": {"delay_queue_proof_budget_guard_present": True},
                    "external_validation_summary": {
                        "all_checks_pass": True,
                        "validation_candidate_ready": True,
                        "validation_row_count": 8,
                        "production_ready": False,
                        "official_bound_effect": False,
                        "validation_metrics": {
                            "overall": {
                                "predicted_positive": 4,
                                "fp": 0,
                                "precision": 1.0,
                                "recall": 0.8,
                            }
                        },
                        "checks": {
                            "delay_queue_proof_budget_guard_present": True,
                            "delay_queue_exactness_guard_present": True,
                        },
                    },
                },
            )

            summary = audit_gat_cbf_knn_ood_readiness(
                selector_manifest=manifest,
                selector_summary=selector_summary,
                checkpoint=checkpoint,
                trajectory_summary=trajectory,
                knn_ood_summary=knn,
                gat_embedding_validation_summary=stale_external,
                gat_embedding_capture_validation_summary=capture_validation,
                output_dir=tmp / "out",
                report=tmp / "report.md",
                min_trajectory_rows=100,
            )

            self.assertTrue(summary["embedding_candidate_ready"])
            contract = summary["gat_embedding_validation_contract"]
            self.assertEqual(contract["evidence_source"], "capture_validation")
            self.assertTrue(contract["capture_validation_available"])
            self.assertTrue(contract["validation_candidate_ready"])
            self.assertEqual(contract["predicted_positive"], 4)
            self.assertEqual(contract["false_positive"], 0)
            self.assertNotIn(
                "sector_wave_knn_ood_smoke_has_no_high_priority_productivity_signal",
                summary["production_blockers"],
            )


if __name__ == "__main__":
    unittest.main()

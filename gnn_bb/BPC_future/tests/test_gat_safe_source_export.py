from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.export_gat_batch_impact_safe_source import export_safe_source


class GATSafeSourceExportTests(unittest.TestCase):
    def test_current_like_blocked_artifacts_do_not_export_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            training = _write_json(tmp / "training.json", _training_summary(gate_pass=False))
            knn = _write_json(tmp / "knn.json", _knn_summary(ready=False))
            decisions = _write_jsonl(
                tmp / "decisions.jsonl",
                [_decision_record(ids_complete=False)],
            )

            summary = export_safe_source(
                training_summary=training,
                knn_ood_summary=knn,
                decision_records=decisions,
                output_dir=tmp / "export",
                report=tmp / "report.md",
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["safe_source_ready"])
            self.assertFalse(summary["safe_ids_exportable"])
            self.assertEqual(summary["safe_candidate_ids"], [])
            self.assertFalse(summary["config_snippet"]["journey_gat_admission_scheduler_enabled"])
            self.assertIn("training_validation_local_gate_not_passed", summary["blockers"])
            self.assertIn("knn_ood_validation_candidate_not_ready", summary["blockers"])
            self.assertIn("candidate_signature_ids_missing_or_incomplete", summary["blockers"])

    def test_ready_artifacts_export_safe_signature_ids_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            training = _write_json(tmp / "training.json", _training_summary(gate_pass=True))
            knn = _write_json(tmp / "knn.json", _knn_summary(ready=True))
            decisions = _write_jsonl(
                tmp / "decisions.jsonl",
                [
                    _decision_record(ids_complete=True, ids=["b", "a"]),
                    _decision_record(decision=0, ids_complete=True, ids=["delayed"]),
                ],
            )

            summary = export_safe_source(
                training_summary=training,
                knn_ood_summary=knn,
                decision_records=decisions,
                output_dir=tmp / "export",
                report=tmp / "report.md",
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertTrue(summary["safe_source_ready"])
            self.assertTrue(summary["safe_ids_exportable"])
            self.assertEqual(summary["safe_candidate_ids"], ["a", "b"])
            self.assertTrue(summary["config_snippet"]["journey_gat_admission_scheduler_enabled"])
            self.assertTrue(summary["config_snippet"]["journey_gat_admission_safe_source_ready"])
            self.assertFalse(summary["config_snippet"]["journey_gat_admission_allow_unsourced_delay"])
            self.assertFalse(summary["selector_can_certificate"])
            self.assertFalse(summary["gate_can_permanently_discard_negative_columns"])

    def test_ready_gates_still_block_when_signature_ids_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            training = _write_json(tmp / "training.json", _training_summary(gate_pass=True))
            knn = _write_json(tmp / "knn.json", _knn_summary(ready=True))
            decisions = _write_jsonl(
                tmp / "decisions.jsonl",
                [_decision_record(ids_complete=False)],
            )

            summary = export_safe_source(
                training_summary=training,
                knn_ood_summary=knn,
                decision_records=decisions,
                output_dir=tmp / "export",
                report=tmp / "report.md",
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["safe_source_ready"])
            self.assertIn("candidate_signature_ids_missing_or_incomplete", summary["blockers"])
            self.assertEqual(summary["safe_candidate_ids"], [])

    def test_knn_ood_can_repair_raw_false_safe_training_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            training = _write_json(
                tmp / "training.json",
                _training_summary(
                    gate_pass=False,
                    reject_reasons=[
                        "false_high_priority_on_delay_too_high",
                        "false_safe_rate_union_too_high",
                        "knn_ood_audit_missing",
                    ],
                ),
            )
            knn = _write_json(tmp / "knn.json", _knn_summary(ready=True))
            decisions = _write_jsonl(
                tmp / "decisions.jsonl",
                [_decision_record(ids_complete=True, ids=["safe-a"])],
            )

            summary = export_safe_source(
                training_summary=training,
                knn_ood_summary=knn,
                decision_records=decisions,
                output_dir=tmp / "export",
                report=tmp / "report.md",
            )

            self.assertTrue(summary["safe_source_ready"])
            self.assertTrue(summary["checks"]["training_gate_repaired_by_knn_ood"])
            self.assertFalse(summary["checks"]["training_validation_raw_gate_pass"])
            self.assertEqual(summary["safe_candidate_ids"], ["safe-a"])
            self.assertNotIn("training_validation_local_gate_not_passed", summary["blockers"])

    def test_knn_ood_cannot_repair_roi_or_family_training_gate_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            training = _write_json(
                tmp / "training.json",
                _training_summary(
                    gate_pass=False,
                    reject_reasons=[
                        "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable",
                    ],
                ),
            )
            knn = _write_json(tmp / "knn.json", _knn_summary(ready=True))
            decisions = _write_jsonl(
                tmp / "decisions.jsonl",
                [_decision_record(ids_complete=True, ids=["unsafe-a"])],
            )

            summary = export_safe_source(
                training_summary=training,
                knn_ood_summary=knn,
                decision_records=decisions,
                output_dir=tmp / "export",
                report=tmp / "report.md",
            )

            self.assertFalse(summary["safe_source_ready"])
            self.assertFalse(summary["checks"]["training_gate_repaired_by_knn_ood"])
            self.assertIn("training_validation_local_gate_not_passed", summary["blockers"])
            self.assertIn("training_validation_non_knn_repairable_reject_reasons", summary["blockers"])
            self.assertEqual(summary["safe_candidate_ids"], [])


def _training_summary(
    *,
    gate_pass: bool,
    reject_reasons: list[str] | None = None,
) -> dict[str, object]:
    reject_reasons = list(reject_reasons or [])
    return {
        "schema_version": "gat_batch_impact_training_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "default_enabled": False,
        "selector_can_certificate": False,
        "gate_can_permanently_discard_negative_columns": False,
        "validation_deployment_metrics": {
            "threshold_local_gate_pass": gate_pass,
            "checkpoint_gate_pass": gate_pass,
            "high_priority_precision_ci_low": 0.93,
            "safe_precision_ci_low": 0.88,
            "accepted_batch_roi_ci_low": 0.75,
            "accepted_batch_roi_over_baseline_ci_low": 0.25,
            "threshold_local_reject_reasons": reject_reasons,
            "checkpoint_gate_reject_reasons": reject_reasons,
        },
        "rejected_checkpoint_reasons": reject_reasons,
    }


def _knn_summary(*, ready: bool) -> dict[str, object]:
    return {
        "schema_version": "gat_batch_impact_knn_ood_audit_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "default_enabled": False,
        "official_bound_effect": False,
        "selector_can_certificate": False,
        "gate_can_permanently_discard_negative_columns": False,
        "validation_candidate_ready": ready,
        "validation_safety_ready": ready,
        "validation_safety_checks": {
            "min_high_priority_met": ready,
            "safe_precision_met": ready,
            "safe_precision_ci_low_met": ready,
            "accepted_batch_count_met": ready,
            "accepted_batch_rate_met": ready,
            "accepted_batch_roi_met": ready,
            "accepted_batch_roi_ci_low_met": ready,
            "false_high_priority_on_delay_met": ready,
            "false_safe_rate_met": ready,
            "coverage_met": ready,
            "family_holdout_all_high_roi_opportunity_families_accepted": ready,
        },
    }


def _decision_record(
    *,
    decision: int = 1,
    ids_complete: bool,
    ids: list[str] | None = None,
) -> dict[str, object]:
    ids = list(ids or ["id-a", "id-b"])
    return {
        "decision": decision,
        "decision_name": "HIGH_PRIORITY" if decision else "DELAY_QUEUE",
        "decision_reason": "high_priority" if decision else "below_batch_threshold_delay_queue",
        "candidate_predicted_high_priority_count": len(ids) if decision else 0,
        "candidate_signature_ids": ids if ids_complete else [],
        "high_priority_candidate_signature_ids": ids if decision and ids_complete else [],
        "candidate_signature_ids_complete": ids_complete,
    }


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_jsonl(path: Path, payloads: list[dict[str, object]]) -> Path:
    path.write_text(
        "".join(json.dumps(payload, sort_keys=True) + "\n" for payload in payloads),
        encoding="utf-8",
    )
    return path


if __name__ == "__main__":
    unittest.main()

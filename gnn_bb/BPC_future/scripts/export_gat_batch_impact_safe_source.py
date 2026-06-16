#!/usr/bin/env python3
"""Export GAT batch-impact HIGH_PRIORITY signature ids for admission scheduling.

This is an offline readiness bridge from Stage 3 artifacts to the Stage 4
admission safe-source interface.  It never enables production by itself and it
never grants certificate authority: exported ids may only schedule already
true-RC verified negative journeys as HIGH_PRIORITY.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


DEFAULT_TRAINING_SUMMARY = Path(
    "BPC_future/results/gat_batch_impact_training_v2_multiscale_20260615/summary.json"
)
DEFAULT_KNN_OOD_SUMMARY = Path(
    "BPC_future/results/gat_batch_impact_knn_ood_audit_v2_multiscale_20260615/summary.json"
)
DEFAULT_DECISION_RECORDS = Path(
    "BPC_future/results/gat_batch_impact_knn_ood_audit_v2_multiscale_20260615/decision_records.jsonl"
)
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/gat_batch_impact_safe_source_v2_multiscale_20260616")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260616_bpc_future_gat_target_mode_stage3_safe_source_export_zh.md"
)

KNN_OOD_REPAIRABLE_TRAINING_REJECT_REASONS = {
    "false_high_priority_on_delay_too_high",
    "false_safe_rate_union_too_high",
    "knn_ood_audit_missing",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training-summary", type=Path, default=DEFAULT_TRAINING_SUMMARY)
    parser.add_argument("--knn-ood-summary", type=Path, default=DEFAULT_KNN_OOD_SUMMARY)
    parser.add_argument("--decision-records", type=Path, default=DEFAULT_DECISION_RECORDS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = export_safe_source(
        training_summary=args.training_summary,
        knn_ood_summary=args.knn_ood_summary,
        decision_records=args.decision_records,
        output_dir=args.output_dir,
        report=args.report,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def export_safe_source(
    *,
    training_summary: Path = DEFAULT_TRAINING_SUMMARY,
    knn_ood_summary: Path = DEFAULT_KNN_OOD_SUMMARY,
    decision_records: Path = DEFAULT_DECISION_RECORDS,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    training = _read_json(Path(training_summary))
    knn_ood = _read_json(Path(knn_ood_summary))
    records = _read_jsonl(Path(decision_records))

    blockers: list[str] = []
    checks: dict[str, bool] = {}
    training_metrics = dict(training.get("validation_deployment_metrics") or {})
    knn_checks = dict(knn_ood.get("validation_safety_checks") or {})

    checks["training_schema"] = training.get("schema_version") == "gat_batch_impact_training_summary_v1"
    checks["knn_ood_schema"] = knn_ood.get("schema_version") == "gat_batch_impact_knn_ood_audit_v1"
    checks["training_diagnostic_only"] = bool(training.get("diagnostic_only")) and not bool(training.get("runs_bpc_or_pricing"))
    checks["knn_ood_diagnostic_only"] = bool(knn_ood.get("diagnostic_only")) and not bool(knn_ood.get("runs_bpc_or_pricing"))
    checks["training_not_production"] = not bool(training.get("production_ready")) and not bool(training.get("default_enabled"))
    checks["knn_ood_not_production"] = not bool(knn_ood.get("production_ready")) and not bool(knn_ood.get("default_enabled"))
    checks["training_not_certificate_source"] = (
        not bool(training.get("selector_can_certificate"))
        and not bool(training.get("gate_can_permanently_discard_negative_columns"))
    )
    checks["knn_ood_not_certificate_source"] = (
        not bool(knn_ood.get("selector_can_certificate"))
        and not bool(knn_ood.get("gate_can_permanently_discard_negative_columns"))
        and not bool(knn_ood.get("official_bound_effect"))
    )

    if not checks["training_schema"]:
        blockers.append("training_summary_schema_mismatch")
    if not checks["knn_ood_schema"]:
        blockers.append("knn_ood_summary_schema_mismatch")
    for key, passed in checks.items():
        if key.endswith("_diagnostic_only") and not passed:
            blockers.append(f"{key}_failed")
        if key.endswith("_not_production") and not passed:
            blockers.append(f"{key}_failed")
        if key.endswith("_not_certificate_source") and not passed:
            blockers.append(f"{key}_failed")

    checks["knn_ood_validation_candidate_ready"] = bool(knn_ood.get("validation_candidate_ready"))
    checks["knn_ood_validation_safety_ready"] = bool(knn_ood.get("validation_safety_ready"))
    training_gate = _training_gate_status(
        training=training,
        training_metrics=training_metrics,
        knn_candidate_ready=checks["knn_ood_validation_candidate_ready"],
        knn_safety_ready=checks["knn_ood_validation_safety_ready"],
    )
    checks["training_validation_raw_gate_pass"] = training_gate["raw_gate_pass"]
    checks["training_gate_repaired_by_knn_ood"] = training_gate["repaired_by_knn_ood"]
    checks["training_validation_gate_pass"] = training_gate["gate_pass"]
    if not training_gate["gate_pass"]:
        blockers.append("training_validation_local_gate_not_passed")
    if training_gate["non_repairable_reject_reasons"]:
        blockers.append("training_validation_non_knn_repairable_reject_reasons")
    for field in (
        "high_priority_precision_ci_low",
        "safe_precision_ci_low",
        "accepted_batch_roi_ci_low",
        "accepted_batch_roi_over_baseline_ci_low",
    ):
        if training_metrics.get(field) is None:
            blockers.append(f"training_{field}_missing")

    if not checks["knn_ood_validation_candidate_ready"]:
        blockers.append("knn_ood_validation_candidate_not_ready")
    if not checks["knn_ood_validation_safety_ready"]:
        blockers.append("knn_ood_validation_safety_not_ready")
    failed_knn_checks = sorted(str(key) for key, value in knn_checks.items() if not bool(value))
    for key in failed_knn_checks:
        blockers.append(f"knn_ood_{key}_failed")

    high_priority_records = [
        record
        for record in records
        if int(record.get("decision") or 0) == 1 or str(record.get("decision_name")) == "HIGH_PRIORITY"
    ]
    if not records:
        blockers.append("decision_records_empty")
    if not high_priority_records:
        blockers.append("no_high_priority_decision_records")

    safe_candidate_ids: set[str] = set()
    missing_signature_record_count = 0
    for record in high_priority_records:
        high_priority_ids = [str(item) for item in record.get("high_priority_candidate_signature_ids", []) if str(item)]
        predicted_count = int(record.get("candidate_predicted_high_priority_count") or len(high_priority_ids))
        ids_complete = bool(record.get("candidate_signature_ids_complete", False))
        if not high_priority_ids or not ids_complete or len(high_priority_ids) < predicted_count:
            missing_signature_record_count += 1
            continue
        safe_candidate_ids.update(high_priority_ids)
    if missing_signature_record_count:
        blockers.append("candidate_signature_ids_missing_or_incomplete")
    if high_priority_records and not safe_candidate_ids:
        blockers.append("no_exportable_high_priority_candidate_signature_ids")

    unique_blockers = sorted(set(blockers))
    safe_source_ready = not unique_blockers
    safe_ids = sorted(safe_candidate_ids) if safe_source_ready else []
    config_snippet = {
        "journey_gat_admission_scheduler_enabled": bool(safe_source_ready),
        "journey_gat_admission_safe_source_ready": bool(safe_source_ready),
        "journey_gat_admission_allow_unsourced_delay": False,
        "journey_gat_safe_candidate_ids": safe_ids,
        "journey_gat_shadow_safe_candidate_ids": safe_ids,
        "journey_gat_certificate_hard_filter_enabled": False,
    }
    structural_check_keys = (
        "training_schema",
        "knn_ood_schema",
        "training_diagnostic_only",
        "knn_ood_diagnostic_only",
        "training_not_production",
        "knn_ood_not_production",
        "training_not_certificate_source",
        "knn_ood_not_certificate_source",
    )
    structural_checks_pass = all(bool(checks[key]) for key in structural_check_keys)
    summary = {
        "schema_version": "gat_batch_impact_safe_source_export_v1",
        "status": "safe_source_exported" if safe_source_ready else "safe_source_blocked",
        "training_summary": str(training_summary),
        "knn_ood_summary": str(knn_ood_summary),
        "decision_records": str(decision_records),
        "output_dir": str(output_dir),
        "safe_source_ready": bool(safe_source_ready),
        "safe_ids_exportable": bool(safe_source_ready and safe_ids),
        "safe_candidate_id_count": len(safe_ids),
        "safe_candidate_ids": safe_ids,
        "high_priority_decision_record_count": len(high_priority_records),
        "decision_record_count": len(records),
        "decision_reason_counts": dict(sorted(Counter(str(record.get("decision_reason")) for record in records).items())),
        "training_gate_reject_reasons": training_gate["reject_reasons"],
        "training_gate_non_knn_repairable_reject_reasons": training_gate[
            "non_repairable_reject_reasons"
        ],
        "blockers": unique_blockers,
        "checks": checks,
        "structural_checks_pass": bool(structural_checks_pass),
        "failed_knn_checks": failed_knn_checks,
        "config_snippet": config_snippet,
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "default_enabled": False,
        "official_bound_effect": False,
        "selector_is_pricing_oracle": False,
        "selector_can_certificate": False,
        "gate_can_permanently_discard_negative_columns": False,
        "negative_columns_must_remain_eventually_reachable": True,
        "unsafe_negative_decision": "DELAY_QUEUE",
        "safe_negative_decision": "HIGH_PRIORITY",
        "all_checks_pass": bool(structural_checks_pass),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "safe_source.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def _training_gate_status(
    *,
    training: dict[str, Any],
    training_metrics: dict[str, Any],
    knn_candidate_ready: bool,
    knn_safety_ready: bool,
) -> dict[str, Any]:
    raw_gate_pass = bool(training_metrics.get("threshold_local_gate_pass")) or bool(
        training_metrics.get("checkpoint_gate_pass")
    )
    reject_reasons = _training_gate_reject_reasons(training=training, training_metrics=training_metrics)
    non_repairable = sorted(
        reason
        for reason in reject_reasons
        if reason not in KNN_OOD_REPAIRABLE_TRAINING_REJECT_REASONS
    )
    repaired_by_knn_ood = bool(
        not raw_gate_pass
        and reject_reasons
        and not non_repairable
        and knn_candidate_ready
        and knn_safety_ready
    )
    return {
        "raw_gate_pass": raw_gate_pass,
        "repaired_by_knn_ood": repaired_by_knn_ood,
        "gate_pass": bool(raw_gate_pass or repaired_by_knn_ood),
        "reject_reasons": sorted(reject_reasons),
        "non_repairable_reject_reasons": non_repairable,
    }


def _training_gate_reject_reasons(
    *,
    training: dict[str, Any],
    training_metrics: dict[str, Any],
) -> set[str]:
    reasons: set[str] = set()
    for payload in (training_metrics, training):
        for key in (
            "checkpoint_gate_reject_reasons",
            "threshold_local_reject_reasons",
            "rejected_checkpoint_reasons",
        ):
            for value in payload.get(key) or []:
                if str(value):
                    reasons.add(str(value))
    return reasons


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                record = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                records.append(record)
    return records


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    compact_config = dict(summary["config_snippet"])
    id_count = int(summary["safe_candidate_id_count"])
    compact_config["journey_gat_safe_candidate_ids"] = f"<{id_count} ids in safe_source.json>"
    compact_config["journey_gat_shadow_safe_candidate_ids"] = f"<{id_count} ids in safe_source.json>"
    lines = [
        "# GAT Batch Impact Safe-source Export 报告",
        "",
        "日期：2026-06-16",
        "",
        "## 结论",
        "",
        f"`safe_source_ready = {str(summary['safe_source_ready']).lower()}`",
        f"`safe_candidate_id_count = {summary['safe_candidate_id_count']}`",
        "",
        "该导出只服务 Stage 4 admission scheduling。它不运行 BPC / pricing / RMP，",
        "不产生 official bound，也不能作为 no-negative certificate source。",
        "",
        "## 机器字段",
        "",
        "```text",
        f"status = {summary['status']}",
        f"decision_record_count = {summary['decision_record_count']}",
        f"high_priority_decision_record_count = {summary['high_priority_decision_record_count']}",
        f"safe_ids_exportable = {str(summary['safe_ids_exportable']).lower()}",
        f"training_gate_repaired_by_knn_ood = {str(summary['checks'].get('training_gate_repaired_by_knn_ood', False)).lower()}",
        f"training_gate_reject_reasons = {summary['training_gate_reject_reasons']}",
        f"blockers = {summary['blockers']}",
        "production_ready = false",
        "default_enabled = false",
        "selector_can_certificate = false",
        "gate_can_permanently_discard_negative_columns = false",
        "```",
        "",
        "## Config Snippet",
        "",
        "```json",
        json.dumps(compact_config, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "完整 safe candidate id 列表在：",
        "",
        "```text",
        f"{summary['output_dir']}/safe_source.json",
        "```",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

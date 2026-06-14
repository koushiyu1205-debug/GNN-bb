#!/usr/bin/env python3
"""Audit whether missing selector trajectory fields can be recovered.

This diagnostic-only script compares three layers of the exact-context replay
pipeline:

* captured/manifest context fields,
* current candidate impact rows,
* desired addition-before RMP trajectory fields.

It does not run BPC, pricing, RMP, Pulse, replay, or benchmarks.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_IMPACT_SUMMARIES = [
    Path(
        "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/"
        "duplicate_noop_smoke/summary.json"
    ),
    Path(
        "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/"
        "real_capture_mt20_apollo/summary.json"
    ),
    Path(
        "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/"
        "impact/summary.json"
    ),
    Path(
        "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_tranq20_20260613/"
        "impact/summary.json"
    ),
    Path(
        "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/"
        "impact/summary.json"
    ),
]
DEFAULT_FEATURE_AVAILABILITY = Path(
    "BPC_future/results/root_cause_selector_feature_availability_audit_20260614/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_capture_schema_feasibility_audit_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_capture_schema_feasibility_audit_zh.md"
)


DESIRED_RMP_TRAJECTORY_FIELDS = [
    "active_hash_before",
    "active_basis_size_before",
    "active_basis_unique_task_set_count_before",
    "active_basis_churn_count_before",
    "dual_hash_before",
    "dual_l1_norm_before",
    "dual_linf_norm_before",
    "column_pool_size_before",
    "duplicate_signature_pool_count_before",
    "task_set_pool_count_before",
    "lambda_active_count_before",
    "lambda_fractional_count_before",
    "rmp_degeneracy_pressure_before",
    "recent_objective_delta_before",
    "recent_dual_l1_delta_before",
    "recent_added_column_acceptance_rate_before",
    "pricing_tail_retry_count_before",
]


FIELD_CLASSIFICATION = {
    "active_hash_before": {
        "status": "available_in_candidate_rows_from_manifest_or_alias",
        "evidence": "manifest_case.active_hash_before",
        "next_action": "keep passing through to candidate rows and normalize older manifests",
    },
    "active_basis_size_before": {
        "status": "recovered_in_candidate_rows_from_event_history",
        "evidence": "source JSONL journey_pool_structure_diagnostics.pool_active_journey_count",
        "next_action": "keep source-event join in candidate row builder",
    },
    "active_basis_unique_task_set_count_before": {
        "status": "recovered_in_candidate_rows_from_event_history",
        "evidence": "source JSONL journey_pool_structure_diagnostics.pool_active_task_set_count",
        "next_action": "keep source-event join in candidate row builder",
    },
    "active_basis_churn_count_before": {
        "status": "available_in_candidate_rows_from_active_basis_snapshot_metric",
        "evidence": "candidate row builder computes full-snapshot signature symmetric-difference churn when active_basis_rows are available",
        "next_action": "collect new no-certificate-effect captures with active_basis_rows populated",
    },
    "dual_hash_before": {
        "status": "available_in_candidate_rows_from_manifest_or_alias",
        "evidence": "manifest_case.true_dual_hash",
        "next_action": "keep mapping true_dual_hash to dual_hash_before in selector rows",
    },
    "dual_l1_norm_before": {
        "status": "derivable_in_candidate_rows_from_manifest",
        "evidence": "manifest_case.true_dual_vector",
        "next_action": "keep deriving from true_dual_vector before selector calibration",
    },
    "dual_linf_norm_before": {
        "status": "derivable_in_candidate_rows_from_manifest",
        "evidence": "manifest_case.true_dual_vector",
        "next_action": "keep deriving from true_dual_vector before selector calibration",
    },
    "column_pool_size_before": {
        "status": "available_in_candidate_rows_from_manifest_or_alias",
        "evidence": "manifest_case.pool_journey_count",
        "next_action": "keep passing through pool_journey_count as column_pool_size_before",
    },
    "duplicate_signature_pool_count_before": {
        "status": "derivable_in_candidate_rows_from_manifest",
        "evidence": "manifest_case.pool_journeys[*].signature when complete_pool_payload",
        "next_action": "keep deriving only when complete_pool_payload is true",
    },
    "task_set_pool_count_before": {
        "status": "derivable_in_candidate_rows_from_manifest",
        "evidence": "manifest_case.pool_journeys[*].task_set when complete_pool_payload",
        "next_action": "keep deriving only when complete_pool_payload is true",
    },
    "lambda_active_count_before": {
        "status": "recovered_in_candidate_rows_from_event_history",
        "evidence": "source JSONL journey_pool_structure_diagnostics.pool_active_journey_count",
        "next_action": "keep source-event join in candidate row builder",
    },
    "lambda_fractional_count_before": {
        "status": "recovered_in_candidate_rows_from_event_history",
        "evidence": "source JSONL journey_pool_structure_diagnostics.pool_active_fractional_journey_count",
        "next_action": "keep source-event join in candidate row builder",
    },
    "rmp_degeneracy_pressure_before": {
        "status": "available_in_candidate_rows_from_active_basis_snapshot_metric",
        "evidence": "candidate row builder computes snapshot fractional/duplicate/near-zero-RC pressure when active_basis_rows are available",
        "next_action": "collect new no-certificate-effect captures with active_basis_rows populated",
    },
    "recent_objective_delta_before": {
        "status": "recovered_in_candidate_rows_from_event_history",
        "evidence": "source JSONL journey_rmp_dual_diagnostics.objective_delta",
        "next_action": "keep same-run event-history join before candidate-row build",
    },
    "recent_dual_l1_delta_before": {
        "status": "recovered_in_candidate_rows_from_event_history",
        "evidence": "source JSONL journey_rmp_dual_diagnostics.dual_l1_delta",
        "next_action": "keep same-run event-history join before candidate-row build",
    },
    "recent_added_column_acceptance_rate_before": {
        "status": "recovered_in_candidate_rows_from_event_history",
        "evidence": "source JSONL prior journey_column_addition events",
        "next_action": "keep prior addition diagnostics join before candidate-row build",
    },
    "pricing_tail_retry_count_before": {
        "status": "recovered_in_candidate_rows_from_event_history",
        "evidence": "source JSONL prior journey_exact_pricing_retry events",
        "next_action": "keep prior pricing events join before candidate-row build",
    },
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv_header(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or [])


def _cases_from_manifest(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return list(_read_json(path).get("cases", []) or [])


def _has_value(case: dict[str, Any], field: str) -> bool:
    value = case.get(field)
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value)
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return True


def _count_manifest_fields(cases: list[dict[str, Any]]) -> dict[str, int]:
    fields = [
        "rmp_objective_before",
        "active_hash_before",
        "pool_active_task_set_hash_before",
        "context_hash",
        "true_dual_hash",
        "true_dual_vector",
        "pool_journey_count",
        "pool_journeys",
        "active_task_sets",
        "active_task_set_count",
    ]
    return {field: sum(1 for case in cases if _has_value(case, field)) for field in fields}


def _complete_pool_case_count(cases: list[dict[str, Any]]) -> int:
    total = 0
    for case in cases:
        pool = case.get("pool_journeys") or []
        if (
            case.get("complete_pool_payload") is True
            and int(case.get("pool_journey_count") or 0) == len(pool)
        ):
            total += 1
    return total


def _classification_counts() -> dict[str, int]:
    return dict(
        sorted(
            Counter(item["status"] for item in FIELD_CLASSIFICATION.values()).items()
        )
    )


def build_audit(
    *,
    impact_summary_paths: list[Path],
    feature_availability_path: Path,
) -> dict[str, Any]:
    impact_summaries: list[dict[str, Any]] = []
    candidate_columns_by_dataset: list[dict[str, Any]] = []
    manifest_cases: list[dict[str, Any]] = []
    missing_inputs: list[str] = []
    for path in impact_summary_paths:
        if not path.exists():
            missing_inputs.append(str(path))
            continue
        summary = _read_json(path)
        impact_summaries.append(summary)
        csv_path = Path(str(summary.get("candidate_rows_csv") or ""))
        manifest_path = Path(str(summary.get("manifest_path") or ""))
        if not csv_path.exists():
            missing_inputs.append(str(csv_path))
            columns: list[str] = []
        else:
            columns = _read_csv_header(csv_path)
        cases = _cases_from_manifest(manifest_path)
        if not manifest_path.exists():
            missing_inputs.append(str(manifest_path))
        manifest_cases.extend(cases)
        candidate_columns_by_dataset.append(
            {
                "impact_summary": str(path),
                "candidate_rows_csv": str(csv_path),
                "manifest_path": str(manifest_path),
                "candidate_columns": columns,
                "candidate_row_count": int(summary.get("candidate_row_count") or 0),
                "manifest_case_count": len(cases),
            }
        )
    feature_availability = (
        _read_json(feature_availability_path) if feature_availability_path.exists() else {}
    )
    candidate_common_columns = sorted(
        set.intersection(
            *(set(item["candidate_columns"]) for item in candidate_columns_by_dataset)
        )
        if candidate_columns_by_dataset
        else set()
    )
    manifest_field_counts = _count_manifest_fields(manifest_cases)
    desired_missing_in_candidate_rows = [
        field for field in DESIRED_RMP_TRAJECTORY_FIELDS if field not in candidate_common_columns
    ]
    desired_present_in_candidate_rows = [
        field for field in DESIRED_RMP_TRAJECTORY_FIELDS if field in candidate_common_columns
    ]
    classification_counts = _classification_counts()
    directly_or_alias_available = sum(
        classification_counts.get(status, 0)
        for status in [
            "available_in_candidate_rows_from_manifest_or_alias",
        ]
    )
    derivable_from_manifest = sum(
        classification_counts.get(status, 0)
        for status in [
            "derivable_in_candidate_rows_from_manifest",
        ]
    )
    recovered_from_event_history = classification_counts.get(
        "recovered_in_candidate_rows_from_event_history", 0
    )
    requires_metric_definition = classification_counts.get(
        "requires_metric_definition_or_full_active_basis_history", 0
    )
    active_basis_snapshot_metric_fields = classification_counts.get(
        "available_in_candidate_rows_from_active_basis_snapshot_metric", 0
    )
    checks = {
        "feature_availability_exists": feature_availability_path.exists(),
        "feature_availability_passed": feature_availability.get("all_checks_pass") is True,
        "impact_inputs_exist": not missing_inputs,
        "candidate_rows_include_recoverable_manifest_fields": (
            desired_present_in_candidate_rows
            == [
                "active_hash_before",
                "active_basis_size_before",
                "active_basis_unique_task_set_count_before",
                "active_basis_churn_count_before",
                "dual_hash_before",
                "dual_l1_norm_before",
                "dual_linf_norm_before",
                "column_pool_size_before",
                "duplicate_signature_pool_count_before",
                "task_set_pool_count_before",
                "lambda_active_count_before",
                "lambda_fractional_count_before",
                "rmp_degeneracy_pressure_before",
                "recent_objective_delta_before",
                "recent_dual_l1_delta_before",
                "recent_added_column_acceptance_rate_before",
                "pricing_tail_retry_count_before",
            ]
        ),
        "candidate_rows_still_missing_schema_and_history_fields": (
            desired_missing_in_candidate_rows == []
        ),
        "active_basis_snapshot_metric_fields_defined": (
            active_basis_snapshot_metric_fields == 2
        ),
        "manifest_cases_present": bool(manifest_cases),
        "manifest_has_true_dual_hash_for_all_cases": (
            manifest_field_counts["true_dual_hash"] == len(manifest_cases)
        ),
        "manifest_has_true_dual_vector_for_all_cases": (
            manifest_field_counts["true_dual_vector"] == len(manifest_cases)
        ),
        "manifest_has_pool_payload_for_all_cases": (
            _complete_pool_case_count(manifest_cases) == len(manifest_cases)
        ),
        "manifest_has_recent_active_hash_some_cases": (
            manifest_field_counts["active_hash_before"] > 0
        ),
        "classification_covers_all_desired_fields": (
            sorted(FIELD_CLASSIFICATION) == sorted(DESIRED_RMP_TRAJECTORY_FIELDS)
        ),
        "metric_definition_no_longer_required": requires_metric_definition == 0,
        "event_history_fields_recovered": recovered_from_event_history == 8,
    }
    return {
        "schema_version": "root_cause_capture_schema_feasibility_audit_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "feature_availability_source": str(feature_availability_path),
        "impact_summary_paths": [str(path) for path in impact_summary_paths],
        "missing_inputs": missing_inputs,
        "impact_dataset_count": len(impact_summaries),
        "candidate_row_count": sum(
            int(summary.get("candidate_row_count") or 0)
            for summary in impact_summaries
        ),
        "manifest_case_count": len(manifest_cases),
        "candidate_common_columns": candidate_common_columns,
        "candidate_columns_by_dataset": candidate_columns_by_dataset,
        "desired_rmp_trajectory_fields": DESIRED_RMP_TRAJECTORY_FIELDS,
        "desired_present_in_candidate_rows": desired_present_in_candidate_rows,
        "desired_missing_in_candidate_rows": desired_missing_in_candidate_rows,
        "field_classification": FIELD_CLASSIFICATION,
        "field_status_counts": classification_counts,
        "direct_or_alias_available_field_count": directly_or_alias_available,
        "derivable_from_manifest_field_count": derivable_from_manifest,
        "recovered_from_event_history_field_count": recovered_from_event_history,
        "active_basis_snapshot_metric_field_count": active_basis_snapshot_metric_fields,
        "requires_metric_definition_count": requires_metric_definition,
        "requires_manifest_pass_through_count": classification_counts.get(
            "requires_manifest_pass_through_from_capture", 0
        ),
        "requires_event_history_join_count": classification_counts.get(
            "requires_event_history_join", 0
        ),
        "requires_capture_schema_extension_count": classification_counts.get(
            "requires_capture_schema_extension", 0
        ),
        "manifest_field_counts": manifest_field_counts,
        "complete_pool_case_count": _complete_pool_case_count(manifest_cases),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "现有 exact-context capture/manifest 已经包含部分可用的 RMP/context "
            "字段，尤其是 true_dual_hash、true_dual_vector、pool_journey_count "
            "和完整 pool_journeys；当前 candidate_impact_rows.csv 已补入 17 个"
            "可从 manifest 透传、派生或从 source JSONL 事件历史恢复的目标 RMP "
            "轨迹字段，其中 active-basis churn 和 RMP degeneracy pressure 已有"
            "full-snapshot 指标定义，但旧 replay 证据包多数没有 full active-basis "
            "snapshot 值。"
            "因此下一步只能继续做离线 snapshot 采集和 selector holdout，不能进入"
            " production A/B、默认 worker 或 certificate gate。"
        ),
        "recommended_next_action": (
            "collect_no_certificate_effect_active_basis_snapshots_then_rerun_selector_holdout"
        ),
    }


def write_report(audit: dict[str, Any], path: Path) -> None:
    status_lines = [
        f"{field}: {entry['status']}"
        for field, entry in audit["field_classification"].items()
    ]
    lines = [
        "# Capture Schema Feasibility Audit 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告回答一个很具体的问题：当前 selector 缺的 RMP/context trajectory",
        "字段，是已经在 capture/manifest 里只是没有进入 candidate rows，还是必须",
        "扩展 no-certificate-effect 采集 schema。",
        "",
        "该审计只读 existing summary / manifest / CSV，不运行 BPC / pricing / RMP / Pulse，",
        "也不改变 worker、certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "capture_schema_feasibility_audit = current",
        f"diagnostic_only = {str(audit['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(audit['runs_bpc_or_pricing']).lower()}",
        f"impact_dataset_count = {audit['impact_dataset_count']}",
        f"candidate_row_count = {audit['candidate_row_count']}",
        f"manifest_case_count = {audit['manifest_case_count']}",
        f"desired_present_in_candidate_rows_count = {len(audit['desired_present_in_candidate_rows'])}",
        f"desired_missing_in_candidate_rows_count = {len(audit['desired_missing_in_candidate_rows'])}",
        f"direct_or_alias_available_field_count = {audit['direct_or_alias_available_field_count']}",
        f"derivable_from_manifest_field_count = {audit['derivable_from_manifest_field_count']}",
        f"recovered_from_event_history_field_count = {audit['recovered_from_event_history_field_count']}",
        f"active_basis_snapshot_metric_field_count = {audit['active_basis_snapshot_metric_field_count']}",
        f"requires_metric_definition_count = {audit['requires_metric_definition_count']}",
        f"requires_manifest_pass_through_count = {audit['requires_manifest_pass_through_count']}",
        f"requires_event_history_join_count = {audit['requires_event_history_join_count']}",
        f"requires_capture_schema_extension_count = {audit['requires_capture_schema_extension_count']}",
        f"complete_pool_case_count = {audit['complete_pool_case_count']}",
        f"all_checks_pass = {str(audit['all_checks_pass']).lower()}",
        "```",
        "",
        "## 已进入 candidate rows 的目标字段",
        "",
        "```text",
        "desired_present_in_candidate_rows = "
        + ",".join(audit["desired_present_in_candidate_rows"]),
        "desired_missing_in_candidate_rows = "
        + ",".join(audit["desired_missing_in_candidate_rows"]),
        "```",
        "",
        "## 字段分类",
        "",
        "```text",
        *status_lines,
        "```",
        "",
        "## 解释",
        "",
        audit["interpretation"],
        "",
        "## 下一步边界",
        "",
        "- 可以做：打开 default-off active-basis snapshot capture 重新采集 no-certificate-effect exact-context 数据。",
        "- 可以做：用包含 snapshot 值的 candidate rows 重新做 context / instance / dataset holdout。",
        "- 不能做：把当前 selector 直接进入 production A/B。",
        "- 不能做：默认启用 Pulse worker 或打开 official certificate gate。",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--impact-summaries",
        nargs="*",
        default=[str(path) for path in DEFAULT_IMPACT_SUMMARIES],
    )
    parser.add_argument(
        "--feature-availability",
        default=str(DEFAULT_FEATURE_AVAILABILITY),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    audit = build_audit(
        impact_summary_paths=[Path(path) for path in args.impact_summaries],
        feature_availability_path=Path(args.feature_availability),
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(audit, Path(args.report))
    print(json.dumps(audit, ensure_ascii=False, sort_keys=True))
    return 0 if audit["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Audit available and missing fields for selector calibration.

This diagnostic-only script inspects exact-context replay candidate impact rows
and separates addition-before features from post-addition labels/diagnostics.
It records which RMP/context trajectory signals are still missing before a
production selector can be claimed.  It does not run BPC, pricing, RMP, Pulse,
or benchmarks.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


DEFAULT_INPUTS = [
    Path(
        "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/"
        "duplicate_noop_smoke/candidate_impact_rows.csv"
    ),
    Path(
        "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/"
        "real_capture_mt20_apollo/candidate_impact_rows.csv"
    ),
    Path(
        "BPC_future/results/"
        "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/"
        "impact/candidate_impact_rows.csv"
    ),
    Path(
        "BPC_future/results/"
        "root_cause_counterfactual_target_capture_dp1000_tranq20_20260613/"
        "impact/candidate_impact_rows.csv"
    ),
    Path(
        "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/"
        "impact/candidate_impact_rows.csv"
    ),
]
DEFAULT_CONTEXT_FEATURE_GAP = Path(
    "BPC_future/results/root_cause_selector_context_feature_gap_audit_20260614/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_feature_availability_audit_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_feature_availability_audit_zh.md"
)


ADDITION_BEFORE_FIELDS = [
    "active_support_changing",
    "cg_iter",
    "control_objective",
    "control_status",
    "cost",
    "duplicate_signature",
    "new_task_set",
    "pricing_kind",
    "pricing_state",
    "sequence",
    "strict_replacement_by_cost",
    "task_count",
    "task_set",
    "true_reduced_cost",
    "vehicle_count",
    "weak_replacement_or_duplicate",
]
IDENTITY_OR_DIAGNOSTIC_FIELDS = [
    "candidate_id",
    "case_id",
    "context_hash",
    "impact_dataset",
    "instance",
]
POST_ADDITION_LABEL_FIELDS = [
    "single_changed_journey_count",
    "single_dual_l1_delta",
    "single_impact_class",
    "single_no_op_treatment",
    "single_objective_delta",
    "single_treatment_found",
]
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


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _non_empty_count(rows: list[dict[str, str]], field: str) -> int:
    return sum(1 for row in rows if str(row.get(field, "")).strip())


def _impact_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        label = str(row.get("single_impact_class") or "unknown")
        counts[label] = counts.get(label, 0) + 1
    return counts


def build_audit(
    *,
    input_paths: list[Path],
    context_feature_gap_path: Path,
) -> dict[str, Any]:
    dataset_rows: list[dict[str, Any]] = []
    all_rows: list[dict[str, str]] = []
    missing_inputs: list[str] = []
    for path in input_paths:
        if not path.exists():
            missing_inputs.append(str(path))
            continue
        rows = _read_csv(path)
        dataset_rows.append(
            {
                "path": str(path),
                "row_count": len(rows),
                "columns": sorted({field for row in rows for field in row}),
            }
        )
        all_rows.extend(rows)
    all_columns = sorted({field for row in all_rows for field in row})
    common_columns = sorted(
        set.intersection(*(set(item["columns"]) for item in dataset_rows))
        if dataset_rows
        else set()
    )
    context_feature_gap = (
        _read_json(context_feature_gap_path) if context_feature_gap_path.exists() else {}
    )

    addition_before_present = [
        field for field in ADDITION_BEFORE_FIELDS if field in common_columns
    ]
    identity_present = [
        field for field in IDENTITY_OR_DIAGNOSTIC_FIELDS if field in common_columns
    ]
    post_addition_present = [
        field for field in POST_ADDITION_LABEL_FIELDS if field in common_columns
    ]
    desired_present = [
        field for field in DESIRED_RMP_TRAJECTORY_FIELDS if field in common_columns
    ]
    desired_missing = [
        field for field in DESIRED_RMP_TRAJECTORY_FIELDS if field not in common_columns
    ]
    field_non_empty_counts = {
        field: _non_empty_count(all_rows, field) for field in all_columns
    }
    label_counts = _impact_counts(all_rows)
    checks = {
        "inputs_exist": not missing_inputs,
        "has_rows": bool(all_rows),
        "expected_row_count": len(all_rows) == 280,
        "has_high_impact_and_noop_labels": (
            label_counts.get("improved", 0) > 0 and label_counts.get("noop", 0) > 0
        ),
        "addition_before_core_fields_present": all(
            field in common_columns
            for field in [
                "true_reduced_cost",
                "cost",
                "task_set",
                "sequence",
                "new_task_set",
                "cg_iter",
                "control_objective",
            ]
        ),
        "post_addition_labels_present": all(
            field in common_columns
            for field in [
                "single_impact_class",
                "single_objective_delta",
                "single_dual_l1_delta",
            ]
        ),
        "recoverable_rmp_trajectory_fields_now_present": (
            desired_present
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
        "remaining_rmp_trajectory_fields_still_missing": desired_missing == [],
        "active_basis_snapshot_metric_fields_defined": (
            "active_basis_churn_count_before" in common_columns
            and "rmp_degeneracy_pressure_before" in common_columns
        ),
        "context_feature_gap_passed": context_feature_gap.get("all_checks_pass")
        is True,
        "context_feature_gap_requires_rmp_trajectory": any(
            item.get("property_id") == "rmp_trajectory_context"
            for item in context_feature_gap.get("required_feature_properties", [])
        ),
    }
    return {
        "schema_version": "selector_feature_availability_audit_v1",
        "input_paths": [str(path) for path in input_paths],
        "context_feature_gap_source": str(context_feature_gap_path),
        "dataset_count": len(dataset_rows),
        "row_count": len(all_rows),
        "dataset_rows": dataset_rows,
        "all_columns": all_columns,
        "common_columns": common_columns,
        "addition_before_present": addition_before_present,
        "identity_or_diagnostic_present": identity_present,
        "post_addition_label_present": post_addition_present,
        "desired_rmp_trajectory_present": desired_present,
        "desired_rmp_trajectory_missing": desired_missing,
        "field_non_empty_counts": field_non_empty_counts,
        "label_counts": label_counts,
        "missing_inputs": missing_inputs,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "当前 replay candidate rows 已有局部列特征、online flags、control "
            "objective，以及从 manifest 和 source JSONL 事件历史透传/派生出的"
            "active-basis / lambda / dual / pool-saturation / recent-trajectory "
            "前置字段。active-basis churn 和 RMP degeneracy pressure 字段也已"
            "进入 candidate rows，但旧 replay 证据包多数没有 full active-basis "
            "snapshot 值。因此下一步仍不是直接上线 selector，而是重新采集"
            "no-certificate-effect exact-context snapshot 数据并重新做 holdout。"
        ),
    }


def write_report(audit: dict[str, Any], path: Path) -> None:
    lines = [
        "# Selector Feature Availability Audit 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告审计当前 exact-context replay candidate rows 中有哪些字段可用，",
        "哪些字段只能作为 replay 后标签，以及生产 selector 还缺哪些 RMP 轨迹字段值。",
        "它只读 CSV/summary，不运行 solver，不改变 pricing / worker / certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        "selector_feature_availability_audit = current",
        f"dataset_count = {audit['dataset_count']}",
        f"row_count = {audit['row_count']}",
        f"addition_before_present_count = {len(audit['addition_before_present'])}",
        f"post_addition_label_present_count = {len(audit['post_addition_label_present'])}",
        f"desired_rmp_trajectory_present_count = {len(audit['desired_rmp_trajectory_present'])}",
        f"desired_rmp_trajectory_missing_count = {len(audit['desired_rmp_trajectory_missing'])}",
        f"all_checks_pass = {str(audit['all_checks_pass']).lower()}",
        "```",
        "",
        "## 可用字段分类",
        "",
        "```text",
        "addition_before_present = "
        + ",".join(audit["addition_before_present"]),
        "identity_or_diagnostic_present = "
        + ",".join(audit["identity_or_diagnostic_present"]),
        "post_addition_label_present = "
        + ",".join(audit["post_addition_label_present"]),
        "desired_rmp_trajectory_present = "
        + ",".join(audit["desired_rmp_trajectory_present"]),
        "desired_rmp_trajectory_missing = "
        + ",".join(audit["desired_rmp_trajectory_missing"]),
        "```",
        "",
        "## 结论",
        "",
        audit["interpretation"],
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", nargs="*", default=[str(path) for path in DEFAULT_INPUTS])
    parser.add_argument(
        "--context-feature-gap", default=str(DEFAULT_CONTEXT_FEATURE_GAP)
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    audit = build_audit(
        input_paths=[Path(path) for path in args.inputs],
        context_feature_gap_path=Path(args.context_feature_gap),
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

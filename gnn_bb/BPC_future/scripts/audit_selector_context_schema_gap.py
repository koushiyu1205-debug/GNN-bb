#!/usr/bin/env python3
"""Audit addition-before context schema gaps for the root-cause selector.

This diagnostic is read-only with respect to solver behavior.  It inspects
existing candidate impact rows, replay manifests, and selector summaries to
separate three cases:

* fields already present but empirically insufficient as production selectors,
* fields derivable from current manifests but not persisted in candidate rows,
* fields not captured with enough explicit structure for selector calibration.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_context_schema_gap_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_context_schema_gap_zh.md"
)
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
        "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/"
        "impact/candidate_impact_rows.csv"
    ),
    Path(
        "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_tranq20_20260613/"
        "impact/candidate_impact_rows.csv"
    ),
    Path(
        "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/"
        "impact/candidate_impact_rows.csv"
    ),
]
DEFAULT_MANIFEST_GLOB = "BPC_future/results/**/replay_cases.json"
NEXT_FEATURE_GATE = Path(
    "BPC_future/results/root_cause_selector_next_feature_gate_20260614/summary.json"
)
POOL_OVERLAP_PROBE = Path(
    "BPC_future/results/root_cause_selector_pool_overlap_feature_probe_20260614/"
    "summary.json"
)

LOCAL_COLUMN_FIELDS = (
    "true_reduced_cost",
    "cost",
    "task_set",
    "sequence",
    "new_task_set",
    "duplicate_signature",
    "strict_replacement_by_cost",
    "weak_replacement_or_duplicate",
)
RMP_AGGREGATE_FIELDS = (
    "active_hash_before",
    "rmp_objective_before",
    "dual_hash_before",
    "dual_l1_norm_before",
    "dual_linf_norm_before",
    "column_pool_size_before",
    "duplicate_signature_pool_count_before",
    "task_set_pool_count_before",
    "pricing_tail_retry_count_before",
    "recent_objective_delta_before",
    "recent_dual_l1_delta_before",
    "recent_added_column_acceptance_rate_before",
)
ACTIVE_BASIS_FIELDS = (
    "active_basis_snapshot_complete_before",
    "active_basis_snapshot_hash_before",
    "active_basis_churn_count_before",
    "active_basis_journey_count_before",
    "active_basis_fractional_journey_count_before",
    "active_basis_unique_task_set_count_before",
    "rmp_degeneracy_pressure_before",
)
DERIVED_OVERLAP_FIELDS = (
    "pool_candidate_task_freq_sum",
    "pool_candidate_task_set_max_jaccard",
    "pool_candidate_same_task_set_best_cost_delta",
    "returned_batch_size",
    "returned_batch_new_task_set_count",
    "returned_candidate_true_rc_rank",
    "returned_batch_true_rc_gap_from_best",
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _dataset_name(path: Path) -> str:
    if path.name == "candidate_impact_rows.csv" and path.parent.name == "impact":
        return path.parent.parent.name
    if path.name == "candidate_impact_rows.csv":
        return path.parent.name
    return path.stem


def _read_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        if not path.exists():
            continue
        dataset = _dataset_name(path)
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("single_impact_class") not in {"improved", "noop"}:
                    continue
                copied = dict(row)
                copied["impact_dataset"] = dataset
                rows.append(copied)
    return rows


def _manifest_cases(manifest_glob: str) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for path in sorted(Path().glob(manifest_glob)):
        payload = _read_json(path)
        raw_cases = payload.get("cases", payload if isinstance(payload, list) else [])
        for case in raw_cases:
            if isinstance(case, dict):
                copied = dict(case)
                copied["_manifest_path"] = str(path)
                cases.append(copied)
    return cases


def _field_nonempty(rows: list[dict[str, str]], fields: tuple[str, ...]) -> dict[str, int]:
    return {
        field: sum(1 for row in rows if str(row.get(field, "")).strip())
        for field in fields
    }


def _field_truthy(rows: list[dict[str, str]], field: str) -> int:
    return sum(
        1
        for row in rows
        if str(row.get(field, "")).strip().lower() in {"1", "true", "yes"}
    )


def _candidate_case_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        str(row.get("source_file", "")),
        str(row.get("case_id", "")),
        str(row.get("context_hash", "")),
    )


def _case_index(cases: list[dict[str, Any]]) -> set[tuple[str, str, str]]:
    return {
        (
            str(case.get("source_file", "")),
            str(case.get("case_id", "")),
            str(case.get("context_hash", "")),
        )
        for case in cases
        if case.get("source_file") and case.get("case_id") and case.get("context_hash")
    }


def audit(
    *,
    input_paths: list[Path],
    manifest_glob: str,
    next_feature_gate_path: Path,
    pool_overlap_probe_path: Path,
) -> dict[str, Any]:
    rows = _read_rows(input_paths)
    cases = _manifest_cases(manifest_glob)
    case_keys = _case_index(cases)
    joined_count = sum(1 for row in rows if _candidate_case_key(row) in case_keys)
    next_gate = _read_json(next_feature_gate_path)
    pool_probe = _read_json(pool_overlap_probe_path)

    row_fields = sorted({field for row in rows for field in row})
    manifest_keys = sorted({key for case in cases for key in case})
    local_nonempty = _field_nonempty(rows, LOCAL_COLUMN_FIELDS)
    rmp_nonempty = _field_nonempty(rows, RMP_AGGREGATE_FIELDS)
    active_basis_nonempty = _field_nonempty(rows, ACTIVE_BASIS_FIELDS)
    active_basis_snapshot_complete_true = _field_truthy(
        rows, "active_basis_snapshot_complete_before"
    )
    derived_overlap_in_rows = _field_nonempty(rows, DERIVED_OVERLAP_FIELDS)
    label_counts = dict(Counter(row.get("single_impact_class", "") for row in rows))

    complete_pool_cases = sum(1 for case in cases if case.get("complete_pool_payload"))
    complete_returned_cases = sum(
        1 for case in cases if case.get("complete_returned_batch")
    )
    cases_with_pool_journeys = sum(1 for case in cases if case.get("pool_journeys"))
    cases_with_returned_journeys = sum(
        1 for case in cases if case.get("returned_journeys")
    )
    cases_with_forbidden_hash = sum(
        1 for case in cases if case.get("forbidden_signature_hash")
    )
    cases_with_forbidden_count = sum(
        1 for case in cases if "forbidden_signature_count" in case
    )
    cases_with_explicit_forbidden = sum(
        1
        for case in cases
        if case.get("forbidden_signatures") or case.get("forbidden_journey_signatures")
    )
    cases_with_active_hash = sum(
        1
        for case in cases
        if case.get("active_hash_before") or case.get("pool_active_task_set_hash_before")
    )

    blocked_families = [
        item.get("family")
        for item in next_gate.get("blocked_feature_families", []) or []
        if isinstance(item, dict)
    ]
    required_families = [
        item.get("family")
        for item in next_gate.get("missing_or_required_feature_families", []) or []
        if isinstance(item, dict)
    ]

    feature_family_status = [
        {
            "family": "local_column_geometry",
            "status": "available_but_blocked_as_production_selector_alone",
            "evidence": {
                "nonempty_counts": local_nonempty,
                "blocked_families": [
                    family
                    for family in blocked_families
                    if family in {"true_rc_threshold", "new_task_set_only"}
                ],
            },
        },
        {
            "family": "rmp_aggregate_context",
            "status": "available_but_insufficient",
            "evidence": {
                "nonempty_counts": rmp_nonempty,
                "blocked_families": [
                    family
                    for family in blocked_families
                    if family
                    in {
                        "active_basis_scalar_only",
                        "current_enriched_single_or_multifeature_selector",
                    }
                ],
            },
        },
        {
            "family": "active_basis_full_snapshot_features",
            "status": "missing_from_current_replay_selector_rows",
            "evidence": {
                "nonempty_counts": active_basis_nonempty,
                "active_basis_snapshot_complete_true_count": (
                    active_basis_snapshot_complete_true
                ),
                "row_count": len(rows),
            },
        },
        {
            "family": "pool_signature_composition_features",
            "status": "derivable_from_manifest_not_persisted_in_candidate_rows",
            "evidence": {
                "complete_pool_cases": complete_pool_cases,
                "cases_with_pool_journeys": cases_with_pool_journeys,
                "row_nonempty_overlap_fields": derived_overlap_in_rows,
            },
        },
        {
            "family": "returned_batch_vs_pool_overlap_features",
            "status": "derivable_but_not_production_validated",
            "evidence": {
                "complete_returned_cases": complete_returned_cases,
                "cases_with_returned_journeys": cases_with_returned_journeys,
                "derived_feature_count": pool_probe.get("derived_feature_count"),
                "robust_all_holdout_derived_feature_count": pool_probe.get(
                    "robust_all_holdout_derived_feature_count"
                ),
                "robust_all_holdout_model_count": pool_probe.get(
                    "robust_all_holdout_model_count"
                ),
            },
        },
        {
            "family": "forbidden_signature_pressure_features",
            "status": "explicit_payload_available_not_production_validated",
            "evidence": {
                "cases_with_forbidden_hash": cases_with_forbidden_hash,
                "cases_with_forbidden_count_field": cases_with_forbidden_count,
                "cases_with_explicit_forbidden_signature_list": (
                    cases_with_explicit_forbidden
                ),
            },
        },
    ]

    checks = {
        "candidate_rows_exist": len(rows) > 0,
        "manifest_cases_exist": len(cases) > 0,
        "candidate_rows_join_manifest": joined_count == len(rows),
        "pool_payload_available": complete_pool_cases > 0 and cases_with_pool_journeys > 0,
        "returned_payload_available": (
            complete_returned_cases > 0 and cases_with_returned_journeys > 0
        ),
        "local_features_present": all(count > 0 for count in local_nonempty.values()),
        "rmp_aggregate_features_present": any(count > 0 for count in rmp_nonempty.values()),
        "active_basis_snapshot_missing_from_current_replay_rows": (
            active_basis_snapshot_complete_true == 0
        ),
        "derived_overlap_not_persisted_in_candidate_rows": all(
            count == 0 for count in derived_overlap_in_rows.values()
        ),
        "pool_overlap_probe_not_robust": (
            pool_probe.get("all_checks_pass") is True
            and pool_probe.get("robust_all_holdout_derived_feature_count") == 0
            and pool_probe.get("robust_all_holdout_model_count") == 0
        ),
        "explicit_forbidden_signature_payload_observed": (
            cases_with_forbidden_hash > 0 and cases_with_explicit_forbidden > 0
        ),
        "next_gate_blocks_production_shortcuts": (
            next_gate.get("all_checks_pass") is True
            and next_gate.get("selector_next_feature_gate_status")
            == "blocked_until_extended_context_features_and_holdout"
        ),
        "diagnostic_not_production_selector": True,
    }
    return {
        "schema_version": "root_cause_selector_context_schema_gap_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "selector_context_schema_gap_audited",
        "input_paths": [str(path) for path in input_paths],
        "manifest_glob": manifest_glob,
        "candidate_row_count": len(rows),
        "candidate_field_count": len(row_fields),
        "candidate_label_counts": label_counts,
        "manifest_case_count": len(cases),
        "manifest_key_count": len(manifest_keys),
        "manifest_joined_row_count": joined_count,
        "complete_pool_payload_case_count": complete_pool_cases,
        "complete_returned_batch_case_count": complete_returned_cases,
        "cases_with_pool_journeys": cases_with_pool_journeys,
        "cases_with_returned_journeys": cases_with_returned_journeys,
        "cases_with_active_hash": cases_with_active_hash,
        "cases_with_forbidden_signature_hash": cases_with_forbidden_hash,
        "cases_with_forbidden_signature_count_field": cases_with_forbidden_count,
        "cases_with_explicit_forbidden_signature_list": cases_with_explicit_forbidden,
        "local_column_field_nonempty_counts": local_nonempty,
        "rmp_aggregate_field_nonempty_counts": rmp_nonempty,
        "active_basis_field_nonempty_counts": active_basis_nonempty,
        "active_basis_snapshot_complete_true_count": (
            active_basis_snapshot_complete_true
        ),
        "derived_overlap_field_nonempty_in_candidate_rows": derived_overlap_in_rows,
        "blocked_feature_families": blocked_families,
        "required_feature_families": required_families,
        "feature_family_status": feature_family_status,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "现有 rows 已包含 true-RC、task-set、RMP aggregate、active-basis "
            "snapshot 与 recent trajectory 字段，但这些字段已被 holdout / 反例证明"
            "不能单独构成 production selector；当前 280 行 replay selector 数据里 "
            "full active-basis snapshot 仍未真正填充。pool/returned-batch composition 可以"
            "从 manifest 派生，但尚未持久化进 candidate rows，且派生后仍无 robust "
            "holdout selector。forbidden pressure 只有 hash/count，没有显式 forbidden "
            "signature list 的旧缺口已经被 targeted component payload 部分补上；"
            "但这些 payload 还没有合入并通过 production selector holdout。"
        ),
    }


def write_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Root Cause Selector Context Schema Gap 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告只读现有 candidate impact rows、replay manifests 与 selector summary，",
        "审计 addition-before selector 还缺哪些上下文字段。它不运行 BPC / pricing / RMP / Pulse。",
        "",
        "## 机器字段",
        "",
        "```text",
        "root_cause_selector_context_schema_gap = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        f"candidate_row_count = {summary['candidate_row_count']}",
        f"manifest_case_count = {summary['manifest_case_count']}",
        f"manifest_joined_row_count = {summary['manifest_joined_row_count']}",
        f"complete_pool_payload_case_count = {summary['complete_pool_payload_case_count']}",
        f"complete_returned_batch_case_count = {summary['complete_returned_batch_case_count']}",
        "cases_with_explicit_forbidden_signature_list = "
        f"{summary['cases_with_explicit_forbidden_signature_list']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 结论",
        "",
        summary["interpretation"],
        "",
        "## Feature Family Status",
        "",
        "```json",
        json.dumps(
            summary["feature_family_status"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Checks",
        "",
        "```json",
        json.dumps(summary["checks"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--manifest-glob", default=DEFAULT_MANIFEST_GLOB)
    parser.add_argument("--input", action="append", dest="inputs")
    parser.add_argument("--next-feature-gate", default=str(NEXT_FEATURE_GATE))
    parser.add_argument("--pool-overlap-probe", default=str(POOL_OVERLAP_PROBE))
    args = parser.parse_args()

    input_paths = [Path(path) for path in args.inputs] if args.inputs else DEFAULT_INPUTS
    summary = audit(
        input_paths=input_paths,
        manifest_glob=str(args.manifest_glob),
        next_feature_gate_path=Path(args.next_feature_gate),
        pool_overlap_probe_path=Path(args.pool_overlap_probe),
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(summary, Path(args.report))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

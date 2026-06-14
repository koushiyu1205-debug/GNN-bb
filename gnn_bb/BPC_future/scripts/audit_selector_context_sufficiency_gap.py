#!/usr/bin/env python3
"""Audit whether current selector context features are sufficient.

This read-only diagnostic connects the target002 same-active trajectory branch
evidence with the current selector feature availability and holdout results.
It does not run BPC, pricing, RMP, Pulse, replay, or benchmarks.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_TRAJECTORY_BRANCH = Path(
    "BPC_future/results/root_cause_selector_holdout_target002_trajectory_branch_20260614/"
    "summary.json"
)
DEFAULT_FEATURE_AVAILABILITY = Path(
    "BPC_future/results/root_cause_selector_feature_availability_audit_20260614/"
    "summary.json"
)
DEFAULT_ENRICHED_FEATURE_HOLDOUT = Path(
    "BPC_future/results/root_cause_selector_enriched_rmp_feature_holdout_20260614/"
    "summary.json"
)
DEFAULT_ENRICHED_MODEL_HOLDOUT = Path(
    "BPC_future/results/root_cause_selector_enriched_multifeature_model_holdout_20260614/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_context_sufficiency_gap_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_context_sufficiency_gap_zh.md"
)

EXACT_DISAMBIGUATOR_FIELDS = [
    "pool_signature_hash",
    "forbidden_signature_hash",
    "pool_task_set_hash",
]
AGGREGATE_PROXY_FIELDS = [
    "active_hash_before",
    "rmp_objective_before",
    "column_pool_size_before",
    "duplicate_signature_pool_count_before",
    "task_set_pool_count_before",
    "active_basis_size_before",
    "active_basis_unique_task_set_count_before",
    "active_basis_churn_count_before",
    "rmp_degeneracy_pressure_before",
]
REQUIRED_NEXT_FEATURE_FAMILIES = [
    "pool_signature_composition_features",
    "forbidden_signature_pressure_features",
    "returned_batch_vs_pool_overlap_features",
    "active_basis_full_snapshot_features",
    "recent_rmp_trajectory_features",
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def audit(
    *,
    trajectory_branch_path: Path,
    feature_availability_path: Path,
    enriched_feature_holdout_path: Path,
    enriched_model_holdout_path: Path,
) -> dict[str, Any]:
    trajectory = _read_json(trajectory_branch_path)
    feature_availability = _read_json(feature_availability_path)
    enriched_feature = _read_json(enriched_feature_holdout_path)
    enriched_model = _read_json(enriched_model_holdout_path)

    common_columns = set(feature_availability.get("common_columns", []) or [])
    all_columns = set(feature_availability.get("all_columns", []) or [])
    exact_present_common = [
        field for field in EXACT_DISAMBIGUATOR_FIELDS if field in common_columns
    ]
    exact_present_any = [
        field for field in EXACT_DISAMBIGUATOR_FIELDS if field in all_columns
    ]
    exact_missing_common = [
        field for field in EXACT_DISAMBIGUATOR_FIELDS if field not in common_columns
    ]
    aggregate_present = [
        field for field in AGGREGATE_PROXY_FIELDS if field in common_columns
    ]
    aggregate_missing = [
        field for field in AGGREGATE_PROXY_FIELDS if field not in common_columns
    ]
    trajectory_checks = trajectory.get("checks", {}) or {}
    same_active_context_hashes = list(trajectory.get("same_active_context_hashes", []) or [])
    robust_single_features = list(
        enriched_feature.get("robust_all_holdout_numeric_features", []) or []
    ) + list(enriched_feature.get("robust_all_holdout_enriched_features", []) or [])
    robust_models = list(enriched_model.get("robust_all_holdout_models", []) or [])
    checks = {
        "trajectory_branch_passed": trajectory.get("all_checks_pass") is True,
        "same_active_not_context_sufficient": (
            trajectory.get("same_active_event_count", 0) >= 2
            and len(set(same_active_context_hashes)) >= 2
        ),
        "pool_or_forbidden_signature_drift_present": trajectory_checks.get(
            "same_active_has_pool_or_forbidden_signature_drift"
        )
        is True,
        "objective_or_batch_drift_present": trajectory_checks.get(
            "same_active_has_objective_or_batch_drift"
        )
        is True,
        "aggregate_proxy_fields_present": len(aggregate_present) >= 7,
        "exact_disambiguators_absent_from_candidate_rows": not exact_present_any,
        "single_feature_holdout_has_no_robust_selector": not robust_single_features,
        "multifeature_holdout_has_no_robust_selector": not robust_models,
        "diagnostic_not_production_selector": True,
    }
    return {
        "schema_version": "root_cause_selector_context_sufficiency_gap_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "selector_context_sufficiency_gap_audited",
        "trajectory_branch_source": str(trajectory_branch_path),
        "feature_availability_source": str(feature_availability_path),
        "enriched_feature_holdout_source": str(enriched_feature_holdout_path),
        "enriched_model_holdout_source": str(enriched_model_holdout_path),
        "same_active_event_count": trajectory.get("same_active_event_count"),
        "same_active_context_hash_count": len(set(same_active_context_hashes)),
        "same_active_context_hashes": same_active_context_hashes,
        "non_source_same_active_event_count": trajectory.get(
            "non_source_same_active_event_count"
        ),
        "aggregate_proxy_fields_present": aggregate_present,
        "aggregate_proxy_fields_missing": aggregate_missing,
        "exact_disambiguator_fields_present_common": exact_present_common,
        "exact_disambiguator_fields_present_any": exact_present_any,
        "exact_disambiguator_fields_missing_common": exact_missing_common,
        "robust_single_feature_selector_count": len(robust_single_features),
        "robust_multifeature_model_count": len(robust_models),
        "required_next_feature_families": REQUIRED_NEXT_FEATURE_FAMILIES,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "selector_context_status": "insufficient_for_production_selector",
        "interpretation": (
            "target002 same-active 分叉证明 active_hash 和当前 aggregate/proxy "
            "RMP 特征还不足以定义 production selector。candidate rows 已有若干 "
            "addition-before proxy，但缺少能概括 pool/forbidden signature composition "
            "和 returned-batch-vs-pool overlap 的可泛化特征；现有 enriched single-feature "
            "和 multifeature holdout 也没有 robust all-holdout selector。"
        ),
    }


def write_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Root Cause Selector Context Sufficiency Gap 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告只读 target002 trajectory branch、feature availability 和 enriched",
        " holdout summary，审计当前 selector 上下文是否足够。它不运行 BPC /",
        " pricing / RMP / Pulse，也不改变 worker、certificate 或 solver 默认行为。",
        "",
        "## 机器字段",
        "",
        "```text",
        "root_cause_selector_context_sufficiency_gap = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        f"selector_context_status = {summary['selector_context_status']}",
        f"same_active_event_count = {summary['same_active_event_count']}",
        f"same_active_context_hash_count = {summary['same_active_context_hash_count']}",
        "non_source_same_active_event_count = "
        f"{summary['non_source_same_active_event_count']}",
        "exact_disambiguator_fields_present_any = "
        f"{','.join(summary['exact_disambiguator_fields_present_any'])}",
        "robust_single_feature_selector_count = "
        f"{summary['robust_single_feature_selector_count']}",
        "robust_multifeature_model_count = "
        f"{summary['robust_multifeature_model_count']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 结论",
        "",
        summary["interpretation"],
        "",
        "## Aggregate Proxy Fields Present",
        "",
        "```json",
        json.dumps(
            summary["aggregate_proxy_fields_present"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Required Next Feature Families",
        "",
        "```json",
        json.dumps(
            summary["required_next_feature_families"],
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
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trajectory-branch", default=str(DEFAULT_TRAJECTORY_BRANCH))
    parser.add_argument("--feature-availability", default=str(DEFAULT_FEATURE_AVAILABILITY))
    parser.add_argument(
        "--enriched-feature-holdout", default=str(DEFAULT_ENRICHED_FEATURE_HOLDOUT)
    )
    parser.add_argument(
        "--enriched-model-holdout", default=str(DEFAULT_ENRICHED_MODEL_HOLDOUT)
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    summary = audit(
        trajectory_branch_path=Path(args.trajectory_branch),
        feature_availability_path=Path(args.feature_availability),
        enriched_feature_holdout_path=Path(args.enriched_feature_holdout),
        enriched_model_holdout_path=Path(args.enriched_model_holdout),
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

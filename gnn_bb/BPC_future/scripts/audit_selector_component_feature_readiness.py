#!/usr/bin/env python3
"""Consolidate component-feature readiness for the root-cause selector.

This diagnostic answers a narrow question: after target002 showed that
active-hash-only context is insufficient, are pool / forbidden / returned-batch
component features already ready to serve as a production addition-before
selector?  It only reads existing summaries and does not run BPC, pricing, RMP,
Pulse, replay, or benchmarks.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_CONTEXT_SCHEMA_GAP = Path(
    "BPC_future/results/root_cause_selector_context_schema_gap_20260614/summary.json"
)
DEFAULT_POOL_OVERLAP_PROBE = Path(
    "BPC_future/results/root_cause_selector_pool_overlap_feature_probe_20260614/"
    "summary.json"
)
DEFAULT_MISSING_CONTEXT = Path(
    "BPC_future/results/root_cause_selector_holdout_missing_context_diagnosis_20260614/"
    "summary.json"
)
DEFAULT_COMPONENT_DRIFT = Path(
    "BPC_future/results/root_cause_selector_holdout_target002_component_drift_20260614/"
    "summary.json"
)
DEFAULT_NEXT_FEATURE_GATE = Path(
    "BPC_future/results/root_cause_selector_next_feature_gate_20260614/summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_component_feature_readiness_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_component_feature_readiness_zh.md"
)

CORE_DERIVED_FIELDS = [
    "pool_candidate_task_freq_sum",
    "pool_candidate_task_set_max_jaccard",
    "returned_batch_size",
    "returned_batch_new_task_set_count",
    "returned_batch_min_true_rc",
    "returned_batch_true_rc_gap_from_best",
    "root_forbidden_signature_count",
    "root_forbidden_candidate_task_set_max_jaccard",
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def build_summary(
    *,
    context_schema_gap_path: Path,
    pool_overlap_probe_path: Path,
    missing_context_path: Path,
    component_drift_path: Path,
    next_feature_gate_path: Path,
) -> dict[str, Any]:
    schema_gap = _read_json(context_schema_gap_path)
    pool_probe = _read_json(pool_overlap_probe_path)
    missing_context = _read_json(missing_context_path)
    component_drift = _read_json(component_drift_path)
    next_gate = _read_json(next_feature_gate_path)

    nonempty_counts = pool_probe.get("derived_feature_nonempty_counts", {})
    row_count = _as_int(pool_probe.get("row_count"))
    core_field_nonempty_counts = {
        field: _as_int(nonempty_counts.get(field)) for field in CORE_DERIVED_FIELDS
    }
    core_fields_populated_for_all_rows = all(
        count == row_count and row_count > 0
        for count in core_field_nonempty_counts.values()
    )
    required_families = [
        item.get("family")
        for item in next_gate.get("missing_or_required_feature_families", [])
    ]

    readiness_items = [
        {
            "item": "pool_returned_overlap_features",
            "status": "available_but_not_production_validated",
            "evidence": {
                "row_count": row_count,
                "derived_feature_count": pool_probe.get("derived_feature_count"),
                "core_field_nonempty_counts": core_field_nonempty_counts,
                "robust_all_holdout_derived_feature_count": pool_probe.get(
                    "robust_all_holdout_derived_feature_count"
                ),
                "robust_all_holdout_model_count": pool_probe.get(
                    "robust_all_holdout_model_count"
                ),
            },
        },
        {
            "item": "forbidden_signature_pressure",
            "status": "explicit_payload_available_not_production_validated",
            "evidence": {
                "forbidden_manifest_case_count": pool_probe.get(
                    "forbidden_manifest_case_count"
                ),
                "explicit_forbidden_signature_list_available_count": pool_probe.get(
                    "explicit_forbidden_signature_list_available_count"
                ),
            },
        },
        {
            "item": "active_hash_only_context",
            "status": "insufficient",
            "evidence": {
                "target_context_hash": component_drift.get("target_context_hash"),
                "target_active_hash": component_drift.get("target_active_hash"),
                "non_source_same_active_event_count": component_drift.get(
                    "non_source_same_active_event_count"
                ),
                "pool_signature_hash_same_count": (
                    component_drift.get("field_same_counts", {}).get(
                        "pool_signature_hash"
                    )
                ),
                "forbidden_signature_hash_same_count": (
                    component_drift.get("field_same_counts", {}).get(
                        "forbidden_signature_hash"
                    )
                ),
                "config_matched_exact_returned_task_sets_same_count": (
                    component_drift.get(
                        "config_matched_exact_returned_task_sets_same_count"
                    )
                ),
            },
        },
        {
            "item": "selector_holdout_dataset",
            "status": "not_ready",
            "evidence": {
                "ready_for_selector_holdout": missing_context.get(
                    "ready_for_selector_holdout"
                ),
                "missing_context_hashes": missing_context.get(
                    "missing_context_hashes"
                ),
                "target002_target_recovered_probe_count": missing_context.get(
                    "target002_target_recovered_probe_count"
                ),
            },
        },
    ]

    checks = {
        "context_schema_gap_passed": schema_gap.get("all_checks_pass") is True,
        "pool_overlap_probe_passed": pool_probe.get("all_checks_pass") is True,
        "missing_context_diagnosis_passed": missing_context.get("all_checks_pass")
        is True,
        "component_drift_passed": component_drift.get("all_checks_pass") is True,
        "next_feature_gate_passed": next_gate.get("all_checks_pass") is True,
        "core_pool_returned_features_populated": core_fields_populated_for_all_rows,
        "pool_returned_features_not_robust": (
            _as_int(pool_probe.get("robust_all_holdout_derived_feature_count")) == 0
            and _as_int(pool_probe.get("robust_all_holdout_model_count")) == 0
        ),
        "explicit_forbidden_signature_payload_accounted": _as_int(
            pool_probe.get("explicit_forbidden_signature_list_available_count")
        )
        > 0,
        "active_hash_only_insufficient": (
            component_drift.get("target_active_hash") == "f0b96be45c5015c9"
            and component_drift.get("target_context_hash") == "3f914a0d2b97fd27"
            and _as_int(
                component_drift.get("field_same_counts", {}).get(
                    "pool_signature_hash"
                )
            )
            == 0
            and _as_int(
                component_drift.get("field_same_counts", {}).get(
                    "forbidden_signature_hash"
                )
            )
            == 0
        ),
        "selector_holdout_not_ready": missing_context.get(
            "ready_for_selector_holdout"
        )
        is False,
        "required_feature_families_listed": all(
            family in required_families
            for family in [
                "pool_signature_composition_features",
                "forbidden_signature_pressure_features",
                "returned_batch_vs_pool_overlap_features",
            ]
        ),
    }

    return {
        "schema_version": "root_cause_selector_component_feature_readiness_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "selector_component_features_not_production_ready",
        "source_context_schema_gap": str(context_schema_gap_path),
        "source_pool_overlap_probe": str(pool_overlap_probe_path),
        "source_missing_context": str(missing_context_path),
        "source_component_drift": str(component_drift_path),
        "source_next_feature_gate": str(next_feature_gate_path),
        "row_count": row_count,
        "derived_feature_count": pool_probe.get("derived_feature_count"),
        "core_field_nonempty_counts": core_field_nonempty_counts,
        "robust_all_holdout_derived_feature_count": pool_probe.get(
            "robust_all_holdout_derived_feature_count"
        ),
        "robust_all_holdout_model_count": pool_probe.get(
            "robust_all_holdout_model_count"
        ),
        "explicit_forbidden_signature_list_available_count": pool_probe.get(
            "explicit_forbidden_signature_list_available_count"
        ),
        "target002_context_hash": component_drift.get("target_context_hash"),
        "target002_active_hash": component_drift.get("target_active_hash"),
        "target002_pool_signature_same_count": component_drift.get(
            "field_same_counts", {}
        ).get("pool_signature_hash"),
        "target002_forbidden_signature_same_count": component_drift.get(
            "field_same_counts", {}
        ).get("forbidden_signature_hash"),
        "target002_config_matched_exact_returned_task_sets_same_count": (
            component_drift.get("config_matched_exact_returned_task_sets_same_count")
        ),
        "ready_for_selector_holdout": missing_context.get(
            "ready_for_selector_holdout"
        ),
        "missing_context_hashes": missing_context.get("missing_context_hashes"),
        "required_feature_families": required_families,
        "readiness_items": readiness_items,
        "interpretation": (
            "Pool/returned overlap features are derivable and populated on the "
            "current 280 replay rows, but they still fail robust holdout.  "
            "The targeted component payload now exposes explicit forbidden "
            "signatures, but those rows are still single-context calibration "
            "evidence rather than a broad production selector holdout.  target002 "
            "proves active hash alone is insufficient.  Therefore component "
            "features remain a wider holdout/data-collection direction, not a "
            "production optimization direction yet."
        ),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# Root Cause Selector Component Feature Readiness 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告合并 context schema gap、pool overlap probe、target002 missing-context",
        "和 component drift 证据，判断 pool / forbidden / returned-batch component",
        "特征是否已经能作为 production addition-before selector。",
        "",
        "它只读已有 summary，不运行 BPC / pricing / RMP / Pulse，也不改变 solver 行为。",
        "",
        "## 机器字段",
        "",
        "```text",
        "selector_component_feature_readiness = current",
        "diagnostic_only = true",
        "runs_bpc_or_pricing = false",
        f"status = {summary['status']}",
        f"row_count = {summary['row_count']}",
        f"derived_feature_count = {summary['derived_feature_count']}",
        f"robust_all_holdout_derived_feature_count = {summary['robust_all_holdout_derived_feature_count']}",
        f"robust_all_holdout_model_count = {summary['robust_all_holdout_model_count']}",
        f"explicit_forbidden_signature_list_available_count = {summary['explicit_forbidden_signature_list_available_count']}",
        f"target002_pool_signature_same_count = {summary['target002_pool_signature_same_count']}",
        f"target002_forbidden_signature_same_count = {summary['target002_forbidden_signature_same_count']}",
        f"ready_for_selector_holdout = {str(summary['ready_for_selector_holdout']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 结论",
        "",
        summary["interpretation"],
        "",
        "所以当前方向不是上线 component selector，而是补齐 no-certificate-effect",
        "component-context 采集，并重新做 context / instance / dataset holdout。",
        "",
        "## Readiness Items",
        "",
        "```json",
        json.dumps(
            summary["readiness_items"],
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
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--context-schema-gap", type=Path, default=DEFAULT_CONTEXT_SCHEMA_GAP
    )
    parser.add_argument(
        "--pool-overlap-probe", type=Path, default=DEFAULT_POOL_OVERLAP_PROBE
    )
    parser.add_argument("--missing-context", type=Path, default=DEFAULT_MISSING_CONTEXT)
    parser.add_argument("--component-drift", type=Path, default=DEFAULT_COMPONENT_DRIFT)
    parser.add_argument("--next-feature-gate", type=Path, default=DEFAULT_NEXT_FEATURE_GATE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    summary = build_summary(
        context_schema_gap_path=args.context_schema_gap,
        pool_overlap_probe_path=args.pool_overlap_probe,
        missing_context_path=args.missing_context,
        component_drift_path=args.component_drift,
        next_feature_gate_path=args.next_feature_gate,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(summary, args.report)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Audit whether component-payload rows move the selector holdout forward.

This is a diagnostic-only extension of
``audit_selector_pool_overlap_feature_probe.py``.  It compares the existing
base selector impact rows, the targeted component-payload addition-before rows,
and their union under the same context/instance/dataset holdout checks.

It does not run BPC, pricing, RMP, Pulse, workers, replay, or benchmarks.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from BPC_future.scripts import audit_selector_pool_overlap_feature_probe as pool_probe


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/"
    "root_cause_component_payload_selector_holdout_extension_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_component_payload_selector_holdout_extension_zh.md"
)
DEFAULT_COMPONENT_ROWS = Path(
    "BPC_future/results/root_cause_component_payload_addition_before_rows_20260614/"
    "impact/candidate_impact_rows.csv"
)


def _as_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _load_base_rows() -> tuple[list[dict[str, str]], int]:
    rows = pool_probe._read_rows(list(pool_probe.DEFAULT_INPUTS))
    cases = pool_probe._manifest_cases(pool_probe.DEFAULT_MANIFEST_GLOB)
    enriched, missing = pool_probe._enrich_rows(rows, cases)
    for row in enriched:
        row["selector_extension_source"] = "base_selector_rows"
    return enriched, missing


def _normalize_component_rows(path: Path) -> list[dict[str, str]]:
    rows = pool_probe._read_rows([path])
    for row in rows:
        row["selector_extension_source"] = "component_payload_rows"
        if not row.get("root_forbidden_signature_count"):
            row["root_forbidden_signature_count"] = row.get(
                "forbidden_signature_count_before", ""
            )
        if not row.get("root_forbidden_candidate_task_set_max_jaccard"):
            row["root_forbidden_candidate_task_set_max_jaccard"] = row.get(
                "pool_candidate_task_set_max_jaccard", ""
            )
        row.setdefault("manifest_joined", "1.0")
    return rows


def _label_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    return dict(Counter(row.get("single_impact_class", "") for row in rows))


def _source_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    return dict(Counter(row.get("selector_extension_source", "") for row in rows))


def _group_counts(rows: list[dict[str, str]], key: str) -> int:
    return len({str(row.get(key, "")) for row in rows if str(row.get(key, "")).strip()})


def _feature_nonempty_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    return {
        feature: sum(1 for row in rows if str(row.get(feature, "")).strip())
        for feature in pool_probe.DERIVED_NUMERIC_FEATURES
    }


def _evaluate_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    label_counts = _label_counts(rows)
    single = pool_probe._evaluate_single_features(rows)
    models = pool_probe._evaluate_models(rows)
    return {
        "row_count": len(rows),
        "label_counts": label_counts,
        "positive_count": _as_int(label_counts.get("improved")),
        "noop_count": _as_int(label_counts.get("noop")),
        "context_hash_count": _group_counts(rows, "context_hash"),
        "instance_count": _group_counts(rows, "instance"),
        "impact_dataset_count": _group_counts(rows, "impact_dataset"),
        "source_counts": _source_counts(rows),
        "derived_feature_nonempty_counts": _feature_nonempty_counts(rows),
        "robust_all_holdout_derived_feature_count": single[
            "robust_all_holdout_derived_feature_count"
        ],
        "robust_all_holdout_derived_features": single[
            "robust_all_holdout_derived_features"
        ],
        "top_derived_feature_summaries": single["feature_summaries"][:10],
        "robust_all_holdout_model_count": models["robust_all_holdout_model_count"],
        "robust_all_holdout_models": models["robust_all_holdout_models"],
        "best_context_model": models["best_context_model"],
        "best_context_model_context_folds": models[
            "best_context_model_context_folds"
        ],
        "best_context_model_instance_folds": models[
            "best_context_model_instance_folds"
        ],
        "best_context_model_dataset_folds": models[
            "best_context_model_dataset_folds"
        ],
    }


def build_extension(component_rows_path: Path) -> dict[str, Any]:
    base_rows, base_missing_manifest = _load_base_rows()
    component_rows = _normalize_component_rows(component_rows_path)
    combined_rows = base_rows + component_rows

    base_eval = _evaluate_rows(base_rows)
    component_eval = _evaluate_rows(component_rows)
    combined_eval = _evaluate_rows(combined_rows)
    component_contexts = {
        str(row.get("context_hash", ""))
        for row in component_rows
        if str(row.get("context_hash", "")).strip()
    }
    base_contexts = {
        str(row.get("context_hash", ""))
        for row in base_rows
        if str(row.get("context_hash", "")).strip()
    }
    component_dataset_names = sorted(
        {
            str(row.get("impact_dataset", ""))
            for row in component_rows
            if str(row.get("impact_dataset", "")).strip()
        }
    )
    component_positive_only = (
        component_eval["positive_count"] == component_eval["row_count"]
        and component_eval["row_count"] > 0
    )
    combined_has_no_robust_selector = (
        combined_eval["robust_all_holdout_derived_feature_count"] == 0
        and combined_eval["robust_all_holdout_model_count"] == 0
    )
    checks = {
        "base_rows_present": base_eval["row_count"] == 280,
        "component_rows_present": component_eval["row_count"] == 48,
        "combined_rows_expected": combined_eval["row_count"] == 328,
        "base_rows_joined_to_manifest": base_missing_manifest == 0,
        "component_rows_are_positive_only": component_positive_only,
        "component_rows_have_explicit_forbidden_payload": all(
            str(row.get("explicit_forbidden_signature_list_available", "")).strip()
            in {"1", "1.0", "true", "True"}
            for row in component_rows
        ),
        "combined_has_no_robust_all_holdout_selector": combined_has_no_robust_selector,
        "diagnostic_not_production_selector": True,
        "runs_bpc_or_pricing_false": True,
    }
    return {
        "schema_version": "component_payload_selector_holdout_extension_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "component_payload_selector_holdout_extension_audited",
        "component_rows_path": str(component_rows_path),
        "base_missing_manifest_join_count": base_missing_manifest,
        "base": base_eval,
        "component_only": component_eval,
        "combined": combined_eval,
        "component_context_overlap_with_base_count": len(
            component_contexts & base_contexts
        ),
        "component_context_new_count": len(component_contexts - base_contexts),
        "component_context_hash_count": len(component_contexts),
        "component_impact_dataset_names": component_dataset_names,
        "component_positive_only": component_positive_only,
        "combined_has_no_robust_selector": combined_has_no_robust_selector,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "Targeted component-payload rows 新增了 48 行显式 forbidden-signature "
            "payload 完整的 addition-before 正样本校准行；但把它们与 base 280 行 "
            "selector rows 合并后，仍没有产生任何通过 context / instance / dataset "
            "all-holdout 的单特征或多特征 selector。它们降低了 schema gap，但还没有"
            "形成 production selector，也没有证明 solver speedup。"
        ),
    }


def write_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Root Cause Component Payload Selector Holdout Extension 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告把 targeted component-payload addition-before rows 合入既有",
        " selector holdout 口径，检查它是否已经足以产生 production selector。",
        "",
        "它只读 CSV / JSON summary，不运行 BPC / pricing / RMP / Pulse / replay，",
        "也不改变 solver 默认行为。",
        "",
        "## 机器字段",
        "",
        "```text",
        "root_cause_component_payload_selector_holdout_extension = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        f"base_row_count = {summary['base']['row_count']}",
        f"component_row_count = {summary['component_only']['row_count']}",
        f"combined_row_count = {summary['combined']['row_count']}",
        "component_positive_only = "
        f"{str(summary['component_positive_only']).lower()}",
        "combined_robust_all_holdout_derived_feature_count = "
        f"{summary['combined']['robust_all_holdout_derived_feature_count']}",
        "combined_robust_all_holdout_model_count = "
        f"{summary['combined']['robust_all_holdout_model_count']}",
        "combined_best_context_model = "
        f"{summary['combined']['best_context_model']}",
        "combined_best_context_model_context_folds = "
        f"{summary['combined']['best_context_model_context_folds']}",
        "component_context_overlap_with_base_count = "
        f"{summary['component_context_overlap_with_base_count']}",
        "component_context_new_count = "
        f"{summary['component_context_new_count']}",
        "combined_has_no_robust_selector = "
        f"{str(summary['combined_has_no_robust_selector']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 结论",
        "",
        summary["interpretation"],
        "",
        "## Label Counts",
        "",
        "```json",
        json.dumps(
            {
                "base": summary["base"]["label_counts"],
                "component_only": summary["component_only"]["label_counts"],
                "combined": summary["combined"]["label_counts"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Holdout Summary",
        "",
        "```json",
        json.dumps(
            {
                "base": {
                    "robust_features": summary["base"][
                        "robust_all_holdout_derived_feature_count"
                    ],
                    "robust_models": summary["base"][
                        "robust_all_holdout_model_count"
                    ],
                    "best_context": summary["base"][
                        "best_context_model_context_folds"
                    ],
                },
                "component_only": {
                    "robust_features": summary["component_only"][
                        "robust_all_holdout_derived_feature_count"
                    ],
                    "robust_models": summary["component_only"][
                        "robust_all_holdout_model_count"
                    ],
                    "best_context": summary["component_only"][
                        "best_context_model_context_folds"
                    ],
                },
                "combined": {
                    "robust_features": summary["combined"][
                        "robust_all_holdout_derived_feature_count"
                    ],
                    "robust_models": summary["combined"][
                        "robust_all_holdout_model_count"
                    ],
                    "best_context": summary["combined"][
                        "best_context_model_context_folds"
                    ],
                },
            },
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
    parser.add_argument("--component-rows", default=str(DEFAULT_COMPONENT_ROWS))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    summary = build_extension(Path(args.component_rows))
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

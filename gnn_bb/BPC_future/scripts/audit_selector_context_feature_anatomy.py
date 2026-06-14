#!/usr/bin/env python3
"""Summarize context-level feature anatomy for selector failures.

This read-only audit connects context-fold selector failures to context/RMP
trajectory features.  It aggregates exact replay candidate rows by context hash
and checks whether low/high impact contexts coexist inside the same instance or
dataset, which rules out a purely instance-level or dataset-level explanation.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_context_feature_anatomy_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_context_feature_anatomy_zh.md"
)
DEFAULT_INPUTS = (
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
)
DEFAULT_CONTEXT_ANATOMY = Path(
    "BPC_future/results/root_cause_selector_context_fold_anatomy_20260614/"
    "summary.json"
)


def _dataset_name(path: Path) -> str:
    if path.name == "candidate_impact_rows.csv":
        if path.parent.name == "impact":
            return path.parent.parent.name
        return path.parent.name
    return path.stem


def _candidate_csv(path: Path) -> Path:
    if path.is_dir():
        return path / "candidate_impact_rows.csv"
    return path


def _as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _read_rows(paths: list[Path], task_count_filter: int | None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw_path in paths:
        path = _candidate_csv(raw_path)
        dataset = _dataset_name(path)
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("single_impact_class") not in {"improved", "noop"}:
                    continue
                if not _as_bool(row.get("single_treatment_found")):
                    continue
                if task_count_filter is not None and _as_float(row.get("task_count")) != float(task_count_filter):
                    continue
                copied = dict(row)
                copied["impact_dataset"] = dataset
                copied["impact_source"] = str(path)
                rows.append(copied)
    return rows


def _context_failure_map(context_anatomy_path: Path) -> dict[str, str]:
    if not context_anatomy_path.exists():
        return {}
    summary = json.loads(context_anatomy_path.read_text(encoding="utf-8"))
    result: dict[str, str] = {}
    for fold in summary.get("twenty_only", {}).get("failed_context_samples", []):
        result[str(fold.get("holdout"))] = str(fold.get("failure_kind"))
    return result


def _range(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"min": None, "max": None, "mean": None}
    return {"min": min(values), "max": max(values), "mean": mean(values)}


def _context_rows_summary(rows: list[dict[str, str]], failure_by_context: dict[str, str]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("context_hash", ""))].append(row)
    summaries: list[dict[str, Any]] = []
    for context_hash, group in grouped.items():
        label_counts = Counter(row["single_impact_class"] for row in group)
        total = len(group)
        true_rc_values = [
            value
            for row in group
            for value in [_as_float(row.get("true_reduced_cost"))]
            if value is not None
        ]
        cost_values = [
            value
            for row in group
            for value in [_as_float(row.get("cost"))]
            if value is not None
        ]
        control_objectives = sorted(
            {
                value
                for row in group
                for value in [_as_float(row.get("control_objective"))]
                if value is not None
            }
        )
        summaries.append(
            {
                "context_hash": context_hash,
                "row_count": total,
                "improved_count": label_counts["improved"],
                "noop_count": label_counts["noop"],
                "positive_rate": None
                if total <= 0
                else label_counts["improved"] / float(total),
                "instance": Counter(row.get("instance", "") for row in group).most_common(1)[0][0],
                "impact_dataset": Counter(row.get("impact_dataset", "") for row in group).most_common(1)[0][0],
                "control_objective_values": control_objectives,
                "true_rc": _range(true_rc_values),
                "cost": _range(cost_values),
                "failure_kind": failure_by_context.get(context_hash, "material_pass_or_not_failed"),
            }
        )
    return sorted(summaries, key=lambda item: (item["positive_rate"], item["row_count"]))


def _mixed_context_groups(
    context_summaries: list[dict[str, Any]], group_key: str
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in context_summaries:
        grouped[str(item.get(group_key, ""))].append(item)
    mixed = []
    for value, items in grouped.items():
        rates = [
            float(item["positive_rate"])
            for item in items
            if item.get("positive_rate") is not None
        ]
        if not rates:
            continue
        has_low = any(rate <= 0.2 for rate in rates)
        has_high = any(rate >= 0.8 for rate in rates)
        if not (has_low and has_high):
            continue
        mixed.append(
            {
                group_key: value,
                "context_count": len(items),
                "min_positive_rate": min(rates),
                "max_positive_rate": max(rates),
                "low_context_count": sum(1 for rate in rates if rate <= 0.2),
                "high_context_count": sum(1 for rate in rates if rate >= 0.8),
                "sample_contexts": [
                    {
                        "context_hash": item["context_hash"],
                        "positive_rate": item["positive_rate"],
                        "row_count": item["row_count"],
                        "control_objective_values": item["control_objective_values"],
                        "failure_kind": item["failure_kind"],
                    }
                    for item in sorted(items, key=lambda row: row["positive_rate"])[:3]
                ]
                + [
                    {
                        "context_hash": item["context_hash"],
                        "positive_rate": item["positive_rate"],
                        "row_count": item["row_count"],
                        "control_objective_values": item["control_objective_values"],
                        "failure_kind": item["failure_kind"],
                    }
                    for item in sorted(items, key=lambda row: row["positive_rate"], reverse=True)[:3]
                ],
            }
        )
    return sorted(mixed, key=lambda item: (-item["max_positive_rate"] + item["min_positive_rate"], item[group_key]))


def build_summary(
    input_paths: list[Path],
    context_anatomy_path: Path,
    task_count_filter: int | None = 20,
) -> dict[str, Any]:
    rows = _read_rows(input_paths, task_count_filter)
    failure_by_context = _context_failure_map(context_anatomy_path)
    context_summaries = _context_rows_summary(rows, failure_by_context)
    low_contexts = [
        item for item in context_summaries if (item["positive_rate"] or 0.0) <= 0.2
    ]
    high_contexts = [
        item for item in context_summaries if (item["positive_rate"] or 0.0) >= 0.8
    ]
    mixed_by_instance = _mixed_context_groups(context_summaries, "instance")
    mixed_by_dataset = _mixed_context_groups(context_summaries, "impact_dataset")
    failure_counts = Counter(item["failure_kind"] for item in context_summaries)
    checks = {
        "has_twenty_rows": len(rows) == 279 if task_count_filter == 20 else bool(rows),
        "has_low_and_high_contexts": bool(low_contexts and high_contexts),
        "same_instance_has_low_and_high_contexts": bool(mixed_by_instance),
        "same_dataset_has_low_and_high_contexts": bool(mixed_by_dataset),
        "has_false_positive_and_missed_positive_failures": (
            failure_counts["false_positive_no_positive_context"] > 0
            and failure_counts["missed_positive_context"] > 0
        ),
    }
    return {
        "schema_version": "selector_context_feature_anatomy_v1",
        "input_paths": [str(path) for path in input_paths],
        "context_anatomy_source": str(context_anatomy_path),
        "row_filter": {"task_count": task_count_filter},
        "row_count": len(rows),
        "context_count": len(context_summaries),
        "low_positive_context_count": len(low_contexts),
        "high_positive_context_count": len(high_contexts),
        "failure_kind_counts": dict(failure_counts),
        "mixed_instance_group_count": len(mixed_by_instance),
        "mixed_dataset_group_count": len(mixed_by_dataset),
        "mixed_by_instance": mixed_by_instance,
        "mixed_by_dataset": mixed_by_dataset,
        "lowest_positive_contexts": low_contexts[:8],
        "highest_positive_contexts": list(reversed(high_contexts[-8:])),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "Low-impact and high-impact contexts coexist within the same "
            "instance and dataset. Selector failures therefore require context/RMP "
            "trajectory features rather than only instance, dataset, or local "
            "column features."
        ),
    }


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# Selector Context Feature Anatomy 审计",
        "",
        "日期：2026-06-14",
        "",
        "## 目标",
        "",
        "按 context 汇总 exact replay rows 的正例率、实例、数据集、control objective、",
        "true-RC/cost 范围，并与 context fold failure kind 对齐。",
        "该审计只读已有 replay 与 selector summary，不运行求解器。",
        "",
        "## 结论",
        "",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "selector_context_feature_anatomy = current",
        f"row_count = {summary['row_count']}",
        f"context_count = {summary['context_count']}",
        f"low_positive_context_count = {summary['low_positive_context_count']}",
        f"high_positive_context_count = {summary['high_positive_context_count']}",
        f"mixed_instance_group_count = {summary['mixed_instance_group_count']}",
        f"mixed_dataset_group_count = {summary['mixed_dataset_group_count']}",
        f"failure_kind_counts = {summary['failure_kind_counts']}",
        "production_validated_selector = false",
        "",
        "解释：同一 instance / dataset 内同时存在 low-positive 与 high-positive context，",
        "所以失败不能归因到实例或数据集粗粒度差异。context/RMP trajectory 本身必须",
        "进入 selector 解释。",
        "",
        "## Mixed Instance Groups",
        "",
        "| Instance | Contexts | Min Rate | Max Rate | Low | High |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in summary["mixed_by_instance"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(item["instance"]),
                    str(item["context_count"]),
                    f"{item['min_positive_rate']:.6f}",
                    f"{item['max_positive_rate']:.6f}",
                    str(item["low_context_count"]),
                    str(item["high_context_count"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Low Positive Context Samples",
            "",
            "| Context | Rate | Rows | Instance | Dataset | Control Objective | Failure |",
            "|---|---:|---:|---|---|---|---|",
        ]
    )
    for item in summary["lowest_positive_contexts"][:8]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(item["context_hash"]),
                    f"{item['positive_rate']:.6f}",
                    str(item["row_count"]),
                    str(item["instance"]),
                    str(item["impact_dataset"]),
                    str(item["control_objective_values"]),
                    str(item["failure_kind"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## High Positive Context Samples",
            "",
            "| Context | Rate | Rows | Instance | Dataset | Control Objective | Failure |",
            "|---|---:|---:|---|---|---|---|",
        ]
    )
    for item in summary["highest_positive_contexts"][:8]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(item["context_hash"]),
                    f"{item['positive_rate']:.6f}",
                    str(item["row_count"]),
                    str(item["instance"]),
                    str(item["impact_dataset"]),
                    str(item["control_objective_values"]),
                    str(item["failure_kind"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "这进一步说明：当前 selector 失败不是因为 Apollo/Tranq 或某个 replay dataset",
            "整体难，而是同一粗粒度分组内部的 context 状态已经改变了 returned batch",
            "的 downstream impact。下一步证据应聚焦 addition-before 的 RMP/context",
            "trajectory 特征，而不是继续堆 true-RC/cost/new-task-set 局部规则。",
            "",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputs",
        nargs="*",
        type=Path,
        default=list(DEFAULT_INPUTS),
    )
    parser.add_argument(
        "--context-anatomy",
        type=Path,
        default=DEFAULT_CONTEXT_ANATOMY,
    )
    parser.add_argument("--task-count-filter", type=int, default=20)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    summary = build_summary(
        list(args.inputs),
        args.context_anatomy,
        task_count_filter=args.task_count_filter,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(summary, args.report)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

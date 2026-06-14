#!/usr/bin/env python3
"""Audit local feature direction inside mixed replay candidate groups.

This read-only script extends the context-collision audit. It asks whether a
simple monotone column-local feature, such as lower true reduced cost or lower
journey cost, can separate improved from noop rows inside mixed task-set or
task-sequence groups. Direction flips across groups indicate that these local
features are not stable enough to define a production addition-before selector.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_local_feature_direction_20260613"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_selector_local_feature_direction_zh.md"
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


def _dataset_name(path: Path) -> str:
    if path.name == "candidate_impact_rows.csv":
        if path.parent.name == "impact":
            return path.parent.parent.name
        return path.parent.name
    return path.stem


def _as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _read_rows(paths: tuple[Path, ...]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        if not path.exists():
            continue
        dataset = _dataset_name(path)
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("single_impact_class") not in {"improved", "noop"}:
                    continue
                if not _as_bool(row.get("single_treatment_found")):
                    continue
                copied = dict(row)
                copied["impact_dataset"] = dataset
                copied["impact_source"] = str(path)
                rows.append(copied)
    return rows


def _mean(values: list[float]) -> float:
    return sum(values) / float(len(values))


def _direction_for_group(rows: list[dict[str, str]], feature: str) -> dict[str, Any]:
    improved = [
        value
        for value in (_as_float(row.get(feature)) for row in rows if row.get("single_impact_class") == "improved")
        if value is not None
    ]
    noop = [
        value
        for value in (_as_float(row.get(feature)) for row in rows if row.get("single_impact_class") == "noop")
        if value is not None
    ]
    if not improved or not noop:
        return {"direction": "missing", "overlap": False}
    improved_mean = _mean(improved)
    noop_mean = _mean(noop)
    if improved_mean < noop_mean:
        direction = "improved_lower_mean"
    elif noop_mean < improved_mean:
        direction = "noop_lower_mean"
    else:
        direction = "equal_mean"
    overlap = max(min(improved), min(noop)) <= min(max(improved), max(noop))
    return {
        "direction": direction,
        "overlap": overlap,
        "improved_mean": improved_mean,
        "noop_mean": noop_mean,
        "improved_min": min(improved),
        "improved_max": max(improved),
        "noop_min": min(noop),
        "noop_max": max(noop),
    }


def _group_rows(
    rows: list[dict[str, str]], fields: tuple[str, ...]
) -> list[tuple[tuple[str, ...], list[dict[str, str]], Counter[str]]]:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(str(row.get(field, "")) for field in fields)].append(row)
    mixed: list[tuple[tuple[str, ...], list[dict[str, str]], Counter[str]]] = []
    for key, group_rows in grouped.items():
        labels = Counter(row.get("single_impact_class", "") for row in group_rows)
        if labels.get("improved", 0) > 0 and labels.get("noop", 0) > 0:
            mixed.append((key, group_rows, labels))
    mixed.sort(key=lambda item: (-len(item[1]), item[0]))
    return mixed


def _direction_summary(
    rows: list[dict[str, str]], fields: tuple[str, ...]
) -> dict[str, Any]:
    mixed = _group_rows(rows, fields)
    feature_stats: dict[str, Any] = {}
    for feature in ("true_reduced_cost", "cost"):
        directions: Counter[str] = Counter()
        overlap_group_count = 0
        examples: list[dict[str, Any]] = []
        for key, group_rows, labels in mixed:
            detail = _direction_for_group(group_rows, feature)
            directions[detail["direction"]] += 1
            if detail.get("overlap"):
                overlap_group_count += 1
            examples.append(
                {
                    "key": list(key),
                    "label_counts": dict(labels),
                    "direction": detail["direction"],
                    "overlap": detail.get("overlap", False),
                    "improved_mean": detail.get("improved_mean"),
                    "noop_mean": detail.get("noop_mean"),
                    "improved_range": [
                        detail.get("improved_min"),
                        detail.get("improved_max"),
                    ],
                    "noop_range": [
                        detail.get("noop_min"),
                        detail.get("noop_max"),
                    ],
                    "context_count": len(
                        {row.get("context_hash", "") for row in group_rows}
                    ),
                    "dataset_count": len(
                        {row.get("impact_dataset", "") for row in group_rows}
                    ),
                }
            )
        nonzero_directions = {
            name: count for name, count in directions.items() if count > 0
        }
        feature_stats[feature] = {
            "direction_counts": dict(directions),
            "nonzero_direction_count": len(nonzero_directions),
            "overlap_group_count": overlap_group_count,
            "examples": examples[:8],
        }
    return {
        "fields": list(fields),
        "mixed_group_count": len(mixed),
        "mixed_row_count": sum(len(group_rows) for _, group_rows, _ in mixed),
        "feature_stats": feature_stats,
    }


def build_summary(inputs: tuple[Path, ...]) -> dict[str, Any]:
    rows = _read_rows(inputs)
    group_summaries = {
        "task_set": _direction_summary(rows, ("task_set",)),
        "task_sequence": _direction_summary(rows, ("task_set", "sequence")),
        "task_flags": _direction_summary(
            rows,
            (
                "task_set",
                "new_task_set",
                "strict_replacement_by_cost",
                "active_support_changing",
            ),
        ),
    }

    def _has_direction_flip(group_name: str, feature: str) -> bool:
        counts = group_summaries[group_name]["feature_stats"][feature][
            "direction_counts"
        ]
        return counts.get("improved_lower_mean", 0) > 0 and counts.get(
            "noop_lower_mean", 0
        ) > 0

    checks = {
        "has_expected_rows": len(rows) == 280,
        "task_set_true_rc_direction_flips": _has_direction_flip(
            "task_set", "true_reduced_cost"
        ),
        "task_sequence_true_rc_direction_flips": _has_direction_flip(
            "task_sequence", "true_reduced_cost"
        ),
        "task_set_cost_direction_not_constant": (
            group_summaries["task_set"]["feature_stats"]["cost"][
                "nonzero_direction_count"
            ]
            > 1
        ),
        "task_sequence_cost_direction_not_constant": (
            group_summaries["task_sequence"]["feature_stats"]["cost"][
                "nonzero_direction_count"
            ]
            > 1
        ),
    }
    return {
        "schema_version": "selector_local_feature_direction_v1",
        "sources": {
            "candidate_inputs": [str(path) for path in inputs],
        },
        "row_count": len(rows),
        "label_counts": dict(
            Counter(row.get("single_impact_class", "") for row in rows)
        ),
        "group_summaries": group_summaries,
        "interpretation": (
            "在 mixed task-set / sequence groups 内，true-RC 与 cost 的方向并不稳定："
            "有些组 improved row 的 true-RC 更低，有些组 noop row 的 true-RC 更低。"
            "因此不能通过一个简单的列局部单调规则修复 selector。"
        ),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    groups = summary["group_summaries"]
    lines = [
        "# Root Cause Selector Local Feature Direction 报告",
        "",
        "日期：2026-06-13",
        "",
        "## 目标",
        "",
        "本报告只读分析 context-collision mixed groups 内部的列局部特征方向，",
        "检查是否可以用“true-RC 更低”或“cost 更低”这类简单单调规则分开",
        "improved 与 noop。不运行 BPC，不修改 solver。",
        "",
        "## 关键结果",
        "",
        "```text",
        f"row_count = {summary['row_count']}",
        "task_set_true_rc_direction_counts = "
        f"{groups['task_set']['feature_stats']['true_reduced_cost']['direction_counts']}",
        "task_sequence_true_rc_direction_counts = "
        f"{groups['task_sequence']['feature_stats']['true_reduced_cost']['direction_counts']}",
        "task_set_cost_direction_counts = "
        f"{groups['task_set']['feature_stats']['cost']['direction_counts']}",
        "task_sequence_cost_direction_counts = "
        f"{groups['task_sequence']['feature_stats']['cost']['direction_counts']}",
        "```",
        "",
        "## 示例",
        "",
        "```json",
        json.dumps(
            {
                name: group["feature_stats"]["true_reduced_cost"]["examples"][:5]
                for name, group in groups.items()
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 解释",
        "",
        summary["interpretation"],
        "",
        "注意：把 exact task-set / sequence / true-RC / cost 全部作为 lookup key 时",
        "可以减少混合，但那等价于 replay-context 记忆，不是 production selector。",
        "总 threshold frontier 也已经显示没有单一 true-RC 阈值能同时消除 false",
        "positive 与 false negative。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="*", type=Path, default=list(DEFAULT_INPUTS))
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    inputs = tuple(args.inputs or DEFAULT_INPUTS)
    summary = build_summary(inputs)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(args.report, summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Audit context collisions for replay candidate impact labels.

This script is read-only with respect to solver state. It consumes exact-context
replay candidate rows and checks whether column-local shapes, such as task set
or task sequence, receive mixed improved/noop labels across contexts. Mixed
labels mean a production addition-before selector cannot rely on the local
column shape alone.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_context_collision_20260613"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_selector_context_collision_zh.md"
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


def _bool_token(value: Any) -> str:
    return "true" if _as_bool(value) else "false"


def _float_token(value: Any) -> str:
    parsed = _as_float(value)
    if parsed is None:
        return "missing"
    return f"{parsed:.12g}"


def _key_for(row: dict[str, str], fields: tuple[str, ...]) -> tuple[str, ...]:
    tokens: list[str] = []
    for field in fields:
        if field in {
            "new_task_set",
            "strict_replacement_by_cost",
            "active_support_changing",
        }:
            tokens.append(_bool_token(row.get(field)))
        elif field in {"true_reduced_cost", "cost"}:
            tokens.append(_float_token(row.get(field)))
        else:
            tokens.append(str(row.get(field, "")))
    return tuple(tokens)


def _compact_example(
    key: tuple[str, ...],
    labels: Counter[str],
    group_rows: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "key": list(key),
        "label_counts": dict(labels),
        "row_count": len(group_rows),
        "context_count": len({row.get("context_hash", "") for row in group_rows}),
        "dataset_count": len({row.get("impact_dataset", "") for row in group_rows}),
        "datasets": sorted({row.get("impact_dataset", "") for row in group_rows}),
        "instances": sorted({row.get("instance", "") for row in group_rows})[:8],
        "example_rows": [
            {
                "impact_dataset": row.get("impact_dataset", ""),
                "case_id": row.get("case_id", ""),
                "candidate_id": row.get("candidate_id", ""),
                "instance": row.get("instance", ""),
                "context_hash": row.get("context_hash", ""),
                "task_set": row.get("task_set", ""),
                "sequence": row.get("sequence", ""),
                "true_reduced_cost": _as_float(row.get("true_reduced_cost")),
                "cost": _as_float(row.get("cost")),
                "single_objective_delta": _as_float(
                    row.get("single_objective_delta")
                ),
                "single_impact_class": row.get("single_impact_class", ""),
                "new_task_set": _as_bool(row.get("new_task_set")),
                "strict_replacement_by_cost": _as_bool(
                    row.get("strict_replacement_by_cost")
                ),
                "active_support_changing": _as_bool(
                    row.get("active_support_changing")
                ),
            }
            for row in group_rows[:4]
        ],
    }


def _group_collision_summary(
    rows: list[dict[str, str]],
    fields: tuple[str, ...],
    example_limit: int = 8,
) -> dict[str, Any]:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[_key_for(row, fields)].append(row)
    mixed: list[tuple[tuple[str, ...], Counter[str], list[dict[str, str]]]] = []
    for key, group_rows in grouped.items():
        labels = Counter(row.get("single_impact_class", "") for row in group_rows)
        if labels.get("improved", 0) > 0 and labels.get("noop", 0) > 0:
            mixed.append((key, labels, group_rows))
    mixed.sort(
        key=lambda item: (
            -len(item[2]),
            -len({row.get("context_hash", "") for row in item[2]}),
            item[0],
        )
    )
    return {
        "fields": list(fields),
        "group_count": len(grouped),
        "mixed_group_count": len(mixed),
        "mixed_row_count": sum(len(item[2]) for item in mixed),
        "mixed_examples": [
            _compact_example(key, labels, group_rows)
            for key, labels, group_rows in mixed[:example_limit]
        ],
    }


def build_summary(inputs: tuple[Path, ...]) -> dict[str, Any]:
    rows = _read_rows(inputs)
    label_counts = Counter(row.get("single_impact_class", "") for row in rows)
    group_specs = {
        "task_set": ("task_set",),
        "task_sequence": ("task_set", "sequence"),
        "task_sequence_rc_cost": (
            "task_set",
            "sequence",
            "true_reduced_cost",
            "cost",
        ),
        "online_flags": (
            "new_task_set",
            "strict_replacement_by_cost",
            "active_support_changing",
        ),
        "task_flags": (
            "task_set",
            "new_task_set",
            "strict_replacement_by_cost",
            "active_support_changing",
        ),
    }
    group_summaries = {
        name: _group_collision_summary(rows, fields)
        for name, fields in group_specs.items()
    }
    checks = {
        "has_expected_rows": len(rows) == 280,
        "task_set_has_mixed_labels": (
            group_summaries["task_set"]["mixed_group_count"] > 0
        ),
        "task_sequence_has_mixed_labels": (
            group_summaries["task_sequence"]["mixed_group_count"] > 0
        ),
        "online_flags_have_mixed_labels": (
            group_summaries["online_flags"]["mixed_group_count"] > 0
        ),
        "task_flags_have_mixed_labels": (
            group_summaries["task_flags"]["mixed_group_count"] > 0
        ),
    }
    return {
        "schema_version": "selector_context_collision_v1",
        "sources": {
            "candidate_inputs": [str(path) for path in inputs],
        },
        "row_count": len(rows),
        "label_counts": dict(label_counts),
        "group_summaries": group_summaries,
        "interpretation": (
            "相同 task-set / sequence / online flag 形态在不同 context 中同时出现 "
            "improved 和 noop label，说明列局部形态不足以决定 addition-before "
            "impact。selector 必须显式处理 context / RMP trajectory。"
        ),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def _write_examples(path: Path, summary: dict[str, Any]) -> None:
    fieldnames = [
        "group_name",
        "key",
        "label_counts",
        "row_count",
        "context_count",
        "dataset_count",
        "datasets",
        "instances",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for group_name, group_summary in summary["group_summaries"].items():
            for example in group_summary.get("mixed_examples", []):
                writer.writerow(
                    {
                        "group_name": group_name,
                        "key": "|".join(example["key"]),
                        "label_counts": json.dumps(
                            example["label_counts"],
                            ensure_ascii=False,
                            sort_keys=True,
                        ),
                        "row_count": example["row_count"],
                        "context_count": example["context_count"],
                        "dataset_count": example["dataset_count"],
                        "datasets": "|".join(example["datasets"]),
                        "instances": "|".join(example["instances"]),
                    }
                )


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    groups = summary["group_summaries"]
    lines = [
        "# Root Cause Selector Context Collision 报告",
        "",
        "日期：2026-06-13",
        "",
        "## 目标",
        "",
        "本报告只读分析 exact-context replay candidate rows，检查相同列局部形态",
        "是否在不同 context 下同时出现 improved 与 noop 标签。不运行 BPC，",
        "不修改 solver，不产生 certificate 或 lower-bound effect。",
        "",
        "## 关键结果",
        "",
        "```text",
        f"row_count = {summary['row_count']}",
        f"label_counts = {summary['label_counts']}",
        f"task_set_group_count = {groups['task_set']['group_count']}",
        f"task_set_mixed_group_count = {groups['task_set']['mixed_group_count']}",
        f"task_set_mixed_row_count = {groups['task_set']['mixed_row_count']}",
        f"task_sequence_group_count = {groups['task_sequence']['group_count']}",
        f"task_sequence_mixed_group_count = {groups['task_sequence']['mixed_group_count']}",
        f"task_sequence_mixed_row_count = {groups['task_sequence']['mixed_row_count']}",
        f"online_flags_group_count = {groups['online_flags']['group_count']}",
        f"online_flags_mixed_group_count = {groups['online_flags']['mixed_group_count']}",
        f"online_flags_mixed_row_count = {groups['online_flags']['mixed_row_count']}",
        f"task_flags_group_count = {groups['task_flags']['group_count']}",
        f"task_flags_mixed_group_count = {groups['task_flags']['mixed_group_count']}",
        f"task_flags_mixed_row_count = {groups['task_flags']['mixed_row_count']}",
        "```",
        "",
        "## 混合标签示例",
        "",
        "```json",
        json.dumps(
            {
                name: group.get("mixed_examples", [])[:3]
                for name, group in groups.items()
                if group.get("mixed_group_count", 0) > 0
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
        "因此，根因不能简化成“某类 task-set 或 sequence 一定有用”。",
        "同一列形态在不同 context / dataset 下会变成不同 impact label，",
        "production selector 必须通过 context / instance / dataset holdout，",
        "且不能只依赖列局部特征。",
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
    _write_examples(args.output_dir / "mixed_group_examples.csv", summary)
    _write_report(args.report, summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

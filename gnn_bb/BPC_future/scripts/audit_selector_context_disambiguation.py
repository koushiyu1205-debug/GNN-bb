#!/usr/bin/env python3
"""Audit which context dimensions disambiguate replay candidate impact labels.

This script is read-only. It consumes exact-context replay candidate rows and
checks a feature ladder from local column shape to exact context hash. The goal
is to distinguish "context matters" from "we already have a production selector".
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_context_disambiguation_20260613"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_selector_context_disambiguation_zh.md"
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


LADDERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("local_task_set", ("task_set",)),
    ("local_sequence", ("task_set", "sequence")),
    (
        "local_sequence_online_flags",
        (
            "task_set",
            "sequence",
            "new_task_set",
            "strict_replacement_by_cost",
            "active_support_changing",
        ),
    ),
    (
        "local_sequence_online_instance",
        (
            "task_set",
            "sequence",
            "new_task_set",
            "strict_replacement_by_cost",
            "active_support_changing",
            "instance",
        ),
    ),
    (
        "local_sequence_online_pricing",
        (
            "task_set",
            "sequence",
            "new_task_set",
            "strict_replacement_by_cost",
            "active_support_changing",
            "pricing_kind",
            "pricing_state",
        ),
    ),
    (
        "local_sequence_online_cg_iter",
        (
            "task_set",
            "sequence",
            "new_task_set",
            "strict_replacement_by_cost",
            "active_support_changing",
            "cg_iter",
        ),
    ),
    (
        "local_sequence_online_dataset",
        (
            "task_set",
            "sequence",
            "new_task_set",
            "strict_replacement_by_cost",
            "active_support_changing",
            "impact_dataset",
        ),
    ),
    (
        "local_sequence_online_context_hash",
        (
            "task_set",
            "sequence",
            "new_task_set",
            "strict_replacement_by_cost",
            "active_support_changing",
            "context_hash",
        ),
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


def _key(row: dict[str, str], fields: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(row.get(field, "")) for field in fields)


def _ladder_summary(
    rows: list[dict[str, str]], fields: tuple[str, ...]
) -> dict[str, Any]:
    groups: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[_key(row, fields)].append(row)
    mixed: list[tuple[tuple[str, ...], Counter[str], list[dict[str, str]]]] = []
    for key, group_rows in groups.items():
        labels = Counter(row.get("single_impact_class", "") for row in group_rows)
        if labels.get("improved", 0) > 0 and labels.get("noop", 0) > 0:
            mixed.append((key, labels, group_rows))
    mixed.sort(key=lambda item: (-len(item[2]), item[0]))
    return {
        "fields": list(fields),
        "group_count": len(groups),
        "mixed_group_count": len(mixed),
        "mixed_row_count": sum(len(item[2]) for item in mixed),
        "max_mixed_group_rows": max((len(item[2]) for item in mixed), default=0),
        "mixed_examples": [
            {
                "key": list(key),
                "label_counts": dict(labels),
                "row_count": len(group_rows),
                "contexts": sorted({row.get("context_hash", "") for row in group_rows}),
                "datasets": sorted({row.get("impact_dataset", "") for row in group_rows}),
                "instances": sorted({row.get("instance", "") for row in group_rows}),
            }
            for key, labels, group_rows in mixed[:5]
        ],
    }


def build_summary(inputs: tuple[Path, ...]) -> dict[str, Any]:
    rows = _read_rows(inputs)
    label_counts = Counter(row.get("single_impact_class", "") for row in rows)
    ladder = {
        name: _ladder_summary(rows, fields)
        for name, fields in LADDERS
    }
    local_sequence = ladder["local_sequence"]
    online_instance = ladder["local_sequence_online_instance"]
    dataset = ladder["local_sequence_online_dataset"]
    context_hash = ladder["local_sequence_online_context_hash"]
    checks = {
        "has_rows": len(rows) == 280,
        "local_sequence_still_mixed": (
            int(local_sequence["mixed_group_count"]) == 5
            and int(local_sequence["mixed_row_count"]) == 30
        ),
        "online_flags_and_instance_do_not_disambiguate": (
            int(online_instance["mixed_group_count"]) == 5
            and int(online_instance["mixed_row_count"]) == 30
        ),
        "dataset_reduces_but_does_not_eliminate_mixing": (
            int(dataset["mixed_group_count"]) == 1
            and int(dataset["mixed_row_count"]) == 6
        ),
        "exact_context_hash_disambiguates_current_rows": (
            int(context_hash["mixed_group_count"]) == 0
            and int(context_hash["mixed_row_count"]) == 0
        ),
        "context_hash_is_more_specific_than_local_sequence": (
            int(context_hash["group_count"]) > int(local_sequence["group_count"])
        ),
    }
    return {
        "schema_version": "selector_context_disambiguation_v1",
        "inputs": [str(path) for path in inputs],
        "row_count": len(rows),
        "label_counts": dict(label_counts),
        "ladder": ladder,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "Local column shape and online flags do not disambiguate replay impact. "
            "Exact context hash disambiguates the current sample, which supports the "
            "RMP-trajectory/context-coupling root cause, but a hash is too specific "
            "to be a production selector without holdout-stable context features."
        ),
    }


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    ladder = summary["ladder"]
    lines = [
        "# Selector Context Disambiguation 审计",
        "",
        "日期：2026-06-13",
        "",
        "## 目标",
        "",
        "检查哪些 context 维度能消除 replay candidate impact 的 mixed labels。",
        "本审计只读现有 exact-context replay candidate rows，不运行求解器。",
        "",
        "## 结论",
        "",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        f"row_count = {summary['row_count']}",
        f"label_counts = {summary['label_counts']}",
        "",
        "关键结果：",
        "",
        f"- local_sequence_mixed_group_count = {ladder['local_sequence']['mixed_group_count']}",
        f"- local_sequence_online_instance_mixed_group_count = {ladder['local_sequence_online_instance']['mixed_group_count']}",
        f"- local_sequence_online_dataset_mixed_group_count = {ladder['local_sequence_online_dataset']['mixed_group_count']}",
        f"- local_sequence_online_context_hash_mixed_group_count = {ladder['local_sequence_online_context_hash']['mixed_group_count']}",
        f"- local_sequence_group_count = {ladder['local_sequence']['group_count']}",
        f"- context_hash_group_count = {ladder['local_sequence_online_context_hash']['group_count']}",
        "",
        "解释：task-set / sequence / online flags / instance 都不足以消除 mixed labels；",
        "dataset 维度能减少但不能消除；只有 exact context_hash 在当前样本中消除了 mixed labels。",
        "这支持 RMP trajectory / context coupling 根因，但 context_hash 本身太具体，",
        "不能直接作为 production addition-before selector。",
        "",
        "## Ladder",
        "",
        "| Ladder | Groups | Mixed Groups | Mixed Rows |",
        "|---|---:|---:|---:|",
    ]
    for name, _fields in LADDERS:
        item = ladder[name]
        lines.append(
            f"| {name} | {item['group_count']} | {item['mixed_group_count']} | {item['mixed_row_count']} |"
        )
    lines.extend(
        [
            "",
            "## 下一步含义",
            "",
            "当前不应把 context_hash 当作 selector。正确下一步是继续 no-certificate-effect",
            "exact-context capture / replay，并寻找可泛化、addition-before 可见、且通过",
            "context / instance / dataset holdout 的 context/RMP trajectory 特征。",
            "",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    summary = build_summary(DEFAULT_INPUTS)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    write_report(summary, args.report)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Audit addition-before context scalar candidates for selector calibration.

This script is read-only. It checks whether cheap context scalar fields in the
exact replay candidate rows can disambiguate impact labels after local column
shape still fails. Passing this audit is only calibration evidence, not a
production selector proof.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_context_scalar_candidates_20260613"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_selector_context_scalar_candidates_zh.md"
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

BASE_FIELDS = (
    "task_set",
    "sequence",
    "new_task_set",
    "strict_replacement_by_cost",
    "active_support_changing",
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


def _objective_bin(value: Any, width: float) -> str:
    parsed = _as_float(value)
    if parsed is None:
        return "missing"
    return str(int(math.floor(parsed / width) * width))


def _key(row: dict[str, str], feature_set: str) -> tuple[str, ...]:
    tokens = [str(row.get(field, "")) for field in BASE_FIELDS]
    if feature_set == "base":
        return tuple(tokens)
    if feature_set == "base_instance_cg_pricing":
        tokens.extend(
            [
                str(row.get("instance", "")),
                str(row.get("cg_iter", "")),
                str(row.get("pricing_kind", "")),
                str(row.get("pricing_state", "")),
            ]
        )
        return tuple(tokens)
    if feature_set == "base_control_objective_exact":
        tokens.append(str(row.get("control_objective", "")))
        return tuple(tokens)
    if feature_set == "base_control_objective_bin_100":
        tokens.append(_objective_bin(row.get("control_objective"), 100.0))
        return tuple(tokens)
    if feature_set == "base_context_hash":
        tokens.append(str(row.get("context_hash", "")))
        return tuple(tokens)
    raise ValueError(f"Unknown feature set: {feature_set}")


def _group_summary(rows: list[dict[str, str]], feature_set: str) -> dict[str, Any]:
    groups: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[_key(row, feature_set)].append(row)
    mixed: list[tuple[tuple[str, ...], Counter[str], list[dict[str, str]]]] = []
    for key, group_rows in groups.items():
        labels = Counter(row.get("single_impact_class", "") for row in group_rows)
        if labels.get("improved", 0) > 0 and labels.get("noop", 0) > 0:
            mixed.append((key, labels, group_rows))
    mixed.sort(key=lambda item: (-len(item[2]), item[0]))
    return {
        "feature_set": feature_set,
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
                "control_objectives": sorted(
                    {row.get("control_objective", "") for row in group_rows}
                ),
                "instances": sorted({row.get("instance", "") for row in group_rows}),
            }
            for key, labels, group_rows in mixed[:5]
        ],
    }


def build_summary(inputs: tuple[Path, ...]) -> dict[str, Any]:
    rows = _read_rows(inputs)
    label_counts = Counter(row.get("single_impact_class", "") for row in rows)
    feature_sets = (
        "base",
        "base_instance_cg_pricing",
        "base_control_objective_exact",
        "base_control_objective_bin_100",
        "base_context_hash",
    )
    groups = {name: _group_summary(rows, name) for name in feature_sets}
    checks = {
        "has_rows": len(rows) == 280,
        "base_still_mixed": (
            int(groups["base"]["mixed_group_count"]) == 5
            and int(groups["base"]["mixed_row_count"]) == 30
        ),
        "cheap_identity_scalars_still_mixed": (
            int(groups["base_instance_cg_pricing"]["mixed_group_count"]) == 3
            and int(groups["base_instance_cg_pricing"]["mixed_row_count"]) == 18
        ),
        "control_objective_exact_disambiguates_current_sample": (
            int(groups["base_control_objective_exact"]["mixed_group_count"]) == 0
            and int(groups["base_control_objective_exact"]["mixed_row_count"]) == 0
        ),
        "control_objective_bin_100_disambiguates_current_sample": (
            int(groups["base_control_objective_bin_100"]["mixed_group_count"]) == 0
            and int(groups["base_control_objective_bin_100"]["mixed_row_count"]) == 0
        ),
        "context_hash_disambiguates_current_sample": (
            int(groups["base_context_hash"]["mixed_group_count"]) == 0
            and int(groups["base_context_hash"]["mixed_row_count"]) == 0
        ),
        "control_objective_bin_is_less_specific_than_context_hash": (
            int(groups["base_control_objective_bin_100"]["group_count"])
            < int(groups["base_context_hash"]["group_count"])
        ),
    }
    return {
        "schema_version": "selector_context_scalar_candidates_v1",
        "inputs": [str(path) for path in inputs],
        "row_count": len(rows),
        "label_counts": dict(label_counts),
        "groups": groups,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "control_objective is an addition-before context scalar candidate: "
            "it disambiguates the current replay sample even with a coarse bin, "
            "while cheaper identity/pricing scalars do not. This is only a "
            "calibration lead; it still requires holdout and full BPC A/B."
        ),
    }


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    groups = summary["groups"]
    lines = [
        "# Selector Context Scalar Candidate 审计",
        "",
        "日期：2026-06-13",
        "",
        "## 目标",
        "",
        "检查 addition-before 可见的 context scalar 是否能替代 exact context_hash。",
        "本审计只读 replay candidate rows，不运行求解器。",
        "",
        "## 结论",
        "",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        f"row_count = {summary['row_count']}",
        f"label_counts = {summary['label_counts']}",
        "",
        "关键结果：",
        "",
        f"- base_mixed_group_count = {groups['base']['mixed_group_count']}",
        f"- base_instance_cg_pricing_mixed_group_count = {groups['base_instance_cg_pricing']['mixed_group_count']}",
        f"- control_objective_exact_mixed_group_count = {groups['base_control_objective_exact']['mixed_group_count']}",
        f"- control_objective_bin_100_mixed_group_count = {groups['base_control_objective_bin_100']['mixed_group_count']}",
        f"- context_hash_mixed_group_count = {groups['base_context_hash']['mixed_group_count']}",
        f"- control_objective_bin_100_group_count = {groups['base_control_objective_bin_100']['group_count']}",
        f"- context_hash_group_count = {groups['base_context_hash']['group_count']}",
        "",
        "解释：`instance + cg_iter + pricing_kind/state` 仍然无法消除 mixed labels；",
        "`control_objective` 精确值和 100-bin 都能在当前样本中消除 mixed labels；",
        "它比 exact context_hash 更粗，因此是一个值得继续 holdout 的 context scalar 候选。",
        "",
        "但这不是 production selector 证明。`control_objective` 可能只是当前 replay 样本的",
        "context surrogate；必须先通过 context / instance / dataset holdout，再进入 full BPC A/B。",
        "",
        "## Feature Sets",
        "",
        "| Feature Set | Groups | Mixed Groups | Mixed Rows |",
        "|---|---:|---:|---:|",
    ]
    for name in (
        "base",
        "base_instance_cg_pricing",
        "base_control_objective_exact",
        "base_control_objective_bin_100",
        "base_context_hash",
    ):
        item = groups[name]
        lines.append(
            f"| {name} | {item['group_count']} | {item['mixed_group_count']} | {item['mixed_row_count']} |"
        )
    lines.extend(
        [
            "",
            "## 下一步含义",
            "",
            "下一步应优先做 calibration-only selector holdout，把 `control_objective` /",
            "`rmp_objective_before` 与列局部特征、context family 特征组合起来测试。",
            "在 holdout 和 full BPC A/B 之前，不应把它接成生产 selector。",
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

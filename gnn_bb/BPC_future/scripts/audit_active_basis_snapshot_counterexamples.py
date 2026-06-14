#!/usr/bin/env python3
"""Build concrete counterexamples from active-basis snapshot impact rows.

This diagnostic-only script reads already generated no-certificate-effect
snapshot impact rows.  It does not run BPC, pricing, RMP, replay, workers, or
certificates.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


DEFAULT_INPUTS = [
    Path(
        "BPC_future/results/root_cause_active_basis_snapshot_smoke_20260614/"
        "impact/candidate_impact_rows.csv"
    ),
    Path(
        "BPC_future/results/root_cause_active_basis_snapshot_mt20_smoke_20260614/"
        "impact/candidate_impact_rows.csv"
    ),
    Path(
        "BPC_future/results/root_cause_active_basis_snapshot_multi20_smoke_20260614/"
        "impact/candidate_impact_rows.csv"
    ),
    Path(
        "BPC_future/results/"
        "root_cause_active_basis_snapshot_greedy_apollo20_02_smoke_20260614/"
        "impact/candidate_impact_rows.csv"
    ),
    Path(
        "BPC_future/results/root_cause_active_basis_snapshot_greedy20_pair_smoke_20260614/"
        "impact/candidate_impact_rows.csv"
    ),
]
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_active_basis_snapshot_counterexamples_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_active_basis_snapshot_counterexamples_zh.md"
)
TRUE_RC_THRESHOLD = -12.430587


def _dataset_name(path: Path) -> str:
    parts = list(path.parts)
    try:
        index = parts.index("results")
        return parts[index + 1]
    except (ValueError, IndexError):
        return path.parent.name


def _as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _read_rows(paths: list[Path]) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    missing: list[str] = []
    for path in paths:
        if not path.exists():
            missing.append(str(path))
            continue
        dataset = _dataset_name(path)
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("single_impact_class") not in {"improved", "noop"}:
                    continue
                copied = dict(row)
                copied["snapshot_dataset"] = dataset
                rows.append(copied)
    return rows, missing


def _label_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        label = row.get("single_impact_class") or "unknown"
        counts[label] = counts.get(label, 0) + 1
    return counts


def _row_digest(row: dict[str, str]) -> dict[str, Any]:
    return {
        "snapshot_dataset": row.get("snapshot_dataset"),
        "instance": row.get("instance"),
        "cg_iter": _as_int(row.get("cg_iter")),
        "task_count": _as_int(row.get("task_count")),
        "task_set": row.get("task_set"),
        "sequence": row.get("sequence"),
        "true_reduced_cost": _as_float(row.get("true_reduced_cost")),
        "single_impact_class": row.get("single_impact_class"),
        "single_objective_delta": _as_float(row.get("single_objective_delta")),
        "new_task_set": _as_bool(row.get("new_task_set")),
        "active_basis_journey_count_before": _as_int(
            row.get("active_basis_journey_count_before")
        ),
        "active_basis_churn_count_before": _as_int(
            row.get("active_basis_churn_count_before")
        ),
        "rmp_degeneracy_pressure_before": _as_float(
            row.get("rmp_degeneracy_pressure_before")
        ),
        "control_objective": _as_float(row.get("control_objective")),
        "column_pool_size_before": _as_int(row.get("column_pool_size_before")),
        "context_hash": row.get("context_hash"),
    }


def _mixed_groups(
    rows: list[dict[str, str]], key_field: str, *, task20_only: bool = False
) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        if task20_only and _as_int(row.get("task_count")) != 20:
            continue
        key = str(row.get(key_field) or "")
        groups.setdefault(key, []).append(row)
    mixed: list[dict[str, Any]] = []
    for key, group in sorted(groups.items()):
        counts = _label_counts(group)
        if counts.get("improved", 0) > 0 and counts.get("noop", 0) > 0:
            mixed.append(
                {
                    key_field: key,
                    "row_count": len(group),
                    "label_counts": counts,
                    "rows": [_row_digest(row) for row in group],
                }
            )
    return mixed


def build_audit(input_paths: list[Path]) -> dict[str, Any]:
    rows, missing_inputs = _read_rows(input_paths)
    task20_rows = [row for row in rows if _as_int(row.get("task_count")) == 20]
    task20_new_task_rows = [
        row for row in task20_rows if _as_bool(row.get("new_task_set"))
    ]
    false_positive_rows = [
        row
        for row in task20_rows
        if row.get("single_impact_class") == "noop"
        and (_as_float(row.get("true_reduced_cost")) or 0.0) <= TRUE_RC_THRESHOLD
    ]
    improved_rows = [
        row for row in task20_rows if row.get("single_impact_class") == "improved"
    ]
    noops = [
        row for row in task20_rows if row.get("single_impact_class") == "noop"
    ]
    strongest_noop = min(
        noops,
        key=lambda row: _as_float(row.get("true_reduced_cost")) or float("inf"),
        default=None,
    )
    weaker_improved_than_strongest_noop: list[dict[str, str]] = []
    if strongest_noop is not None:
        noop_rc = _as_float(strongest_noop.get("true_reduced_cost"))
        if noop_rc is not None:
            weaker_improved_than_strongest_noop = [
                row
                for row in improved_rows
                if (_as_float(row.get("true_reduced_cost")) or float("-inf")) > noop_rc
            ]

    positive_churn_rows = [
        row
        for row in task20_rows
        if _as_int(row.get("active_basis_churn_count_before")) > 0
    ]
    degeneracy_one_rows = [
        row
        for row in task20_rows
        if abs((_as_float(row.get("rmp_degeneracy_pressure_before")) or 0.0) - 1.0)
        <= 1.0e-9
    ]
    mixed_instance_groups = _mixed_groups(rows, "instance", task20_only=True)
    mixed_degeneracy_groups = _mixed_groups(
        task20_rows, "rmp_degeneracy_pressure_before"
    )

    checks = {
        "inputs_exist": not missing_inputs,
        "has_rows": bool(rows),
        "has_task20_rows": bool(task20_rows),
        "task20_rows_are_all_new_task_set": len(task20_rows)
        == len(task20_new_task_rows),
        "task20_has_high_impact_and_noop": (
            _label_counts(task20_rows).get("improved", 0) > 0
            and _label_counts(task20_rows).get("noop", 0) > 0
        ),
        "true_rc_threshold_has_task20_false_positives": bool(false_positive_rows),
        "strongest_noop_more_negative_than_some_improved": (
            strongest_noop is not None and bool(weaker_improved_than_strongest_noop)
        ),
        "positive_churn_contains_high_and_noop": (
            _label_counts(positive_churn_rows).get("improved", 0) > 0
            and _label_counts(positive_churn_rows).get("noop", 0) > 0
        ),
        "degeneracy_one_contains_high_and_noop": (
            _label_counts(degeneracy_one_rows).get("improved", 0) > 0
            and _label_counts(degeneracy_one_rows).get("noop", 0) > 0
        ),
        "has_mixed_task20_instance_group": bool(mixed_instance_groups),
    }
    return {
        "schema_version": "active_basis_snapshot_counterexamples_v1",
        "runs_bpc_or_pricing": False,
        "input_paths": [str(path) for path in input_paths],
        "missing_inputs": missing_inputs,
        "row_count": len(rows),
        "task20_row_count": len(task20_rows),
        "label_counts": _label_counts(rows),
        "task20_label_counts": _label_counts(task20_rows),
        "task20_new_task_set_row_count": len(task20_new_task_rows),
        "false_positive_rows": [_row_digest(row) for row in false_positive_rows],
        "strongest_noop": (
            _row_digest(strongest_noop) if strongest_noop is not None else None
        ),
        "weaker_improved_than_strongest_noop_count": len(
            weaker_improved_than_strongest_noop
        ),
        "weaker_improved_than_strongest_noop_examples": [
            _row_digest(row) for row in weaker_improved_than_strongest_noop[:6]
        ],
        "positive_churn_label_counts": _label_counts(positive_churn_rows),
        "degeneracy_one_label_counts": _label_counts(degeneracy_one_rows),
        "mixed_instance_groups": mixed_instance_groups,
        "mixed_degeneracy_groups": mixed_degeneracy_groups,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "Concrete no-certificate-effect snapshot rows show that task20 "
            "new-task-set true-RC negative candidates can be either high-impact "
            "or noop depending on RMP/active-basis context.  This is evidence "
            "against a production selector based only on true-RC, new-task-set, "
            "or a single scalar snapshot feature."
        ),
    }


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# Active-basis Snapshot Counterexamples 审计报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目标",
        "",
        "本报告只读 no-certificate-effect active-basis snapshot impact rows，列出当前根因判断所依赖的具体反例。",
        "",
        "它不运行 BPC / pricing / RMP / replay / worker / certificate。",
        "",
        "## 关键结果",
        "",
        "```text",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        f"row_count = {summary['row_count']}",
        f"task20_row_count = {summary['task20_row_count']}",
        f"label_counts = {summary['label_counts']}",
        f"task20_label_counts = {summary['task20_label_counts']}",
        f"task20_new_task_set_row_count = {summary['task20_new_task_set_row_count']}",
        f"false_positive_count = {len(summary['false_positive_rows'])}",
        f"weaker_improved_than_strongest_noop_count = {summary['weaker_improved_than_strongest_noop_count']}",
        f"positive_churn_label_counts = {summary['positive_churn_label_counts']}",
        f"degeneracy_one_label_counts = {summary['degeneracy_one_label_counts']}",
        "```",
        "",
        "## False-positive Rows",
        "",
        "```json",
        json.dumps(
            summary["false_positive_rows"],
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        ),
        "```",
        "",
        "## Strongest Noop",
        "",
        "```json",
        json.dumps(
            summary["strongest_noop"],
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        ),
        "```",
        "",
        "## Weaker Improved Examples",
        "",
        "```json",
        json.dumps(
            summary["weaker_improved_than_strongest_noop_examples"],
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        ),
        "```",
        "",
        "## Mixed Task20 Instance Groups",
        "",
        "```json",
        json.dumps(
            summary["mixed_instance_groups"],
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        ),
        "```",
        "",
        "## Checks",
        "",
        "```json",
        json.dumps(summary["checks"], indent=2, ensure_ascii=False, sort_keys=True),
        "```",
        "",
        "## 解释",
        "",
        "这些反例说明：即使候选列是 20-task、new-task-set、true-RC negative，并且 active-basis snapshot 字段完整，它仍可能是 noop。",
        "",
        "最强 noop 的 true-RC 比多个 improved rows 更负，因此“更负 true-RC 更值得加”的单调假设不成立。",
        "",
        "positive active-basis churn 和 `rmp_degeneracy_pressure_before = 1.0` 都同时包含 improved 与 noop；单个 snapshot scalar 也不能解释 production selector。",
        "",
        "因此当前根因仍是 returned column batch 与 RMP/active-basis context trajectory 耦合，而不是 Pulse 单组件或负列数量不足。",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    input_paths = args.input if args.input is not None else DEFAULT_INPUTS
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = build_audit(input_paths)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_report(summary, args.report)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

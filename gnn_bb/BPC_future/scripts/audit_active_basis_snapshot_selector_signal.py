#!/usr/bin/env python3
"""Audit selector signal in active-basis snapshot smoke rows.

This diagnostic-only script reads already generated no-certificate-effect
active-basis snapshot smoke impact rows.  It does not run BPC, pricing, RMP,
Pulse, replay, workers, or certificates.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Callable


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
DEFAULT_AUDIT_SUMMARIES = [
    Path(
        "BPC_future/results/root_cause_active_basis_snapshot_smoke_audit_20260614/"
        "summary.json"
    ),
    Path(
        "BPC_future/results/root_cause_active_basis_snapshot_mt20_smoke_audit_20260614/"
        "summary.json"
    ),
    Path(
        "BPC_future/results/root_cause_active_basis_snapshot_multi20_smoke_audit_20260614/"
        "summary.json"
    ),
    Path(
        "BPC_future/results/"
        "root_cause_active_basis_snapshot_greedy_apollo20_02_smoke_audit_20260614/"
        "summary.json"
    ),
    Path(
        "BPC_future/results/"
        "root_cause_active_basis_snapshot_greedy20_pair_smoke_audit_20260614/"
        "summary.json"
    ),
]
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_active_basis_snapshot_selector_signal_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_active_basis_snapshot_selector_signal_zh.md"
)
NUMERIC_FEATURES = (
    "true_reduced_cost",
    "active_basis_journey_count_before",
    "active_basis_churn_count_before",
    "rmp_degeneracy_pressure_before",
    "column_pool_size_before",
    "task_set_pool_count_before",
)

Predicate = Callable[[dict[str, str]], bool]


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


def _read_audit_summaries(paths: list[Path]) -> tuple[list[dict[str, Any]], list[str]]:
    summaries: list[dict[str, Any]] = []
    missing: list[str] = []
    for path in paths:
        if not path.exists():
            missing.append(str(path))
            continue
        summary = json.loads(path.read_text(encoding="utf-8"))
        summary["source"] = str(path)
        summaries.append(summary)
    return summaries, missing


def _label_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        label = str(row.get("single_impact_class") or "unknown")
        counts[label] = counts.get(label, 0) + 1
    return counts


def _metrics(rows: list[dict[str, str]], predicate: Predicate) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    for row in rows:
        predicted = bool(predicate(row))
        positive = row.get("single_impact_class") == "improved"
        if predicted and positive:
            tp += 1
        elif predicted and not positive:
            fp += 1
        elif not predicted and positive:
            fn += 1
        else:
            tn += 1
    precision = None if tp + fp <= 0 else tp / float(tp + fp)
    recall = None if tp + fn <= 0 else tp / float(tp + fn)
    return {
        "total": len(rows),
        "predicted_positive": tp + fp,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "accuracy": None if not rows else (tp + tn) / float(len(rows)),
    }


def _numeric_rule(feature: str, op: str, threshold: float) -> Predicate:
    def predicate(row: dict[str, str]) -> bool:
        value = _as_float(row.get(feature))
        if value is None:
            return False
        if op == "<=":
            return value <= threshold + 1.0e-12
        return value >= threshold - 1.0e-12

    return predicate


def _score(metrics: dict[str, Any]) -> tuple[float, float, float, int, int]:
    precision = float(metrics.get("precision") or 0.0)
    recall = float(metrics.get("recall") or 0.0)
    f1 = 0.0 if precision + recall <= 0.0 else 2.0 * precision * recall / (precision + recall)
    return (f1, precision, recall, int(metrics.get("tp") or 0), -int(metrics.get("fp") or 0))


def _best_single_feature_rules(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for feature in NUMERIC_FEATURES:
        values = sorted(
            {
                value
                for row in rows
                for value in [_as_float(row.get(feature))]
                if value is not None
            }
        )
        best: dict[str, Any] | None = None
        for op in ("<=", ">="):
            for threshold in values:
                metrics = _metrics(rows, _numeric_rule(feature, op, threshold))
                if metrics["predicted_positive"] <= 0:
                    continue
                candidate = {
                    "feature": feature,
                    "operator": op,
                    "threshold": threshold,
                    "metrics": metrics,
                }
                if best is None or _score(metrics) > _score(best["metrics"]):
                    best = candidate
        if best is not None:
            rules.append(best)
    rules.sort(key=lambda item: _score(item["metrics"]), reverse=True)
    return rules


def _mixed_instance_groups(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("instance") or ""), []).append(row)
    mixed: list[dict[str, Any]] = []
    for instance, group in sorted(grouped.items()):
        counts = _label_counts(group)
        if counts.get("improved", 0) > 0 and counts.get("noop", 0) > 0:
            mixed.append(
                {
                    "instance": instance,
                    "row_count": len(group),
                    "label_counts": counts,
                    "task_sets": [row.get("task_set") for row in group],
                    "true_reduced_costs": [
                        _as_float(row.get("true_reduced_cost")) for row in group
                    ],
                    "active_basis_churn": [
                        _as_float(row.get("active_basis_churn_count_before"))
                        for row in group
                    ],
                }
            )
    return mixed


def build_audit(
    input_paths: list[Path], audit_summary_paths: list[Path]
) -> dict[str, Any]:
    rows, missing_inputs = _read_rows(input_paths)
    audit_summaries, missing_audit_summaries = _read_audit_summaries(
        audit_summary_paths
    )
    label_counts = _label_counts(rows)
    task20_rows = [row for row in rows if _as_int(row.get("task_count")) == 20]
    task20_label_counts = _label_counts(task20_rows)
    task20_new_task_rows = [
        row for row in task20_rows if _as_bool(row.get("new_task_set"))
    ]
    task20_true_rc_threshold_metrics = _metrics(
        task20_rows,
        lambda row: (_as_float(row.get("true_reduced_cost")) or 0.0) <= -12.430587,
    )
    snapshot_complete_count = sum(
        1 for row in rows if _as_bool(row.get("active_basis_snapshot_complete_before"))
    )
    active_basis_churn_nonempty = sum(
        1 for row in rows if row.get("active_basis_churn_count_before") not in {"", None}
    )
    degeneracy_nonempty = sum(
        1 for row in rows if row.get("rmp_degeneracy_pressure_before") not in {"", None}
    )
    no_certificate_effect_summary_count = sum(
        1
        for summary in audit_summaries
        if summary.get("all_checks_pass") is True
        and _as_int(summary.get("official_effect_count")) == 0
        and (summary.get("checks") or {}).get("all_capture_events_no_certificate_effect")
        is True
    )
    best_rules = _best_single_feature_rules(rows)
    perfect_single_feature_rule_count = sum(
        1
        for rule in best_rules
        if _as_int(rule["metrics"].get("fp")) == 0
        and _as_int(rule["metrics"].get("fn")) == 0
    )
    checks = {
        "inputs_exist": not missing_inputs,
        "audit_summaries_exist": not missing_audit_summaries,
        "has_snapshot_rows": bool(rows),
        "all_audit_summaries_no_certificate_effect": (
            bool(audit_summaries)
            and no_certificate_effect_summary_count == len(audit_summaries)
        ),
        "all_rows_have_active_basis_snapshot": bool(rows)
        and snapshot_complete_count == len(rows),
        "active_basis_churn_populated": bool(rows)
        and active_basis_churn_nonempty == len(rows),
        "rmp_degeneracy_pressure_populated": bool(rows)
        and degeneracy_nonempty == len(rows),
        "has_high_impact_and_noop_rows": (
            label_counts.get("improved", 0) > 0 and label_counts.get("noop", 0) > 0
        ),
        "has_twenty_scale_rows": bool(task20_rows),
        "twenty_new_task_set_contains_high_and_noop": (
            len(task20_new_task_rows) == len(task20_rows)
            and task20_label_counts.get("improved", 0) > 0
            and task20_label_counts.get("noop", 0) > 0
        ),
        "true_rc_threshold_has_false_positive_on_twenty": (
            _as_int(task20_true_rc_threshold_metrics.get("fp")) > 0
        ),
        "dataset_is_too_small_for_production_holdout": len(rows) < 30,
    }
    return {
        "schema_version": "active_basis_snapshot_selector_signal_v1",
        "runs_bpc_or_pricing": False,
        "input_paths": [str(path) for path in input_paths],
        "audit_summary_paths": [str(path) for path in audit_summary_paths],
        "missing_inputs": missing_inputs,
        "missing_audit_summaries": missing_audit_summaries,
        "row_count": len(rows),
        "task20_row_count": len(task20_rows),
        "label_counts": label_counts,
        "task20_label_counts": task20_label_counts,
        "task20_new_task_set_row_count": len(task20_new_task_rows),
        "snapshot_complete_count": snapshot_complete_count,
        "active_basis_churn_nonempty_count": active_basis_churn_nonempty,
        "rmp_degeneracy_pressure_nonempty_count": degeneracy_nonempty,
        "no_certificate_effect_summary_count": no_certificate_effect_summary_count,
        "mixed_instance_groups": _mixed_instance_groups(rows),
        "task20_true_rc_threshold_metrics": task20_true_rc_threshold_metrics,
        "best_single_feature_rules": best_rules[:5],
        "perfect_single_feature_rule_count": perfect_single_feature_rule_count,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "Snapshot rows show that full active-basis features are available and "
            "that true-RC/new-task-set alone is not sufficient on 20-task rows. "
            "The sample is intentionally small and is not a production selector "
            "or speedup proof."
        ),
    }


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# Active-basis Snapshot Selector Signal 审计报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目标",
        "",
        "本报告只读已经生成的 active-basis snapshot smoke impact rows，检查这些新字段是否已经进入 selector 数据层，以及当前小样本是否足以支持 production selector。",
        "",
        "它不运行 BPC / pricing / replay / worker / certificate。",
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
        f"snapshot_complete_count = {summary['snapshot_complete_count']}",
        f"active_basis_churn_nonempty_count = {summary['active_basis_churn_nonempty_count']}",
        f"rmp_degeneracy_pressure_nonempty_count = {summary['rmp_degeneracy_pressure_nonempty_count']}",
        f"perfect_single_feature_rule_count = {summary['perfect_single_feature_rule_count']}",
        "```",
        "",
        "## 20-task True-RC Threshold",
        "",
        "```json",
        json.dumps(
            summary["task20_true_rc_threshold_metrics"],
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        ),
        "```",
        "",
        "## Mixed Instance Groups",
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
        "## Best Single Feature Rules",
        "",
        "```json",
        json.dumps(
            summary["best_single_feature_rules"],
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
        f"这 {summary['row_count']} 行 snapshot rows 证明 full active-basis 字段已经能进入 candidate impact rows；其中 {summary['task20_row_count']} 行是 20-task，全部是 new task-set，且 true-RC 都明显为负。",
        "",
        "但 20-task 行中同时存在 high-impact 和 noop，`true_reduced_cost <= -12.430587` 在这个小样本上已有 false positive。因此不能把 true-RC 阈值、new-task-set 或任意单个 snapshot scalar 当成 production selector。",
        "",
        "这个报告支持当前根因判断：下一步仍需要扩展 no-certificate-effect exact-context snapshot 数据，并在 context / instance / dataset holdout 上验证 addition-before selector；它本身不是 5/10 no-regression 或 20-task speedup 证明。",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", type=Path, default=None)
    parser.add_argument(
        "--audit-summary", action="append", type=Path, default=None
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    input_paths = args.input if args.input is not None else DEFAULT_INPUTS
    audit_summary_paths = (
        args.audit_summary
        if args.audit_summary is not None
        else DEFAULT_AUDIT_SUMMARIES
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = build_audit(input_paths, audit_summary_paths)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_report(summary, args.report)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

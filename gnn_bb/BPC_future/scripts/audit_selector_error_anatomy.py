#!/usr/bin/env python3
"""Audit false-positive/false-negative anatomy for the replay selector.

This script is read-only with respect to solver state. It consumes existing
exact-context replay candidate rows and the replay-calibrated selector summary,
then explains where the current recommended addition-before selector fails.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_error_anatomy_20260613"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_selector_error_anatomy_zh.md"
)
REPLAY_SELECTOR_SUMMARY = Path(
    "BPC_future/results/root_cause_replay_calibrated_selector_candidate_20260613/"
    "summary.json"
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


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


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


def _predict(row: dict[str, str], rule: dict[str, Any]) -> bool:
    feature = str(rule.get("feature", ""))
    if str(rule.get("type", "")) == "numeric":
        value = _as_float(row.get(feature))
        if value is None:
            return False
        threshold = float(rule.get("threshold", 0.0))
        if str(rule.get("operator", "")) == "<=":
            return value <= threshold + 1.0e-12
        return value >= threshold - 1.0e-12
    return _as_bool(row.get(feature)) is bool(rule.get("value"))


def _counter(rows: list[dict[str, str]], key: str) -> dict[str, int]:
    return dict(Counter(str(row.get(key, "")) for row in rows))


def _top_counter(rows: list[dict[str, str]], key: str, limit: int = 12) -> list[dict[str, Any]]:
    return [
        {"value": value, "count": count}
        for value, count in Counter(str(row.get(key, "")) for row in rows).most_common(limit)
    ]


def _flag_counts(rows: list[dict[str, str]]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for field in (
        "new_task_set",
        "strict_replacement_by_cost",
        "active_support_changing",
        "weak_replacement_or_duplicate",
        "duplicate_signature",
    ):
        if not any(field in row for row in rows):
            continue
        result[field] = dict(
            Counter("true" if _as_bool(row.get(field)) else "false" for row in rows)
        )
    return result


def _true_rc_bucket(value: float | None) -> str:
    if value is None:
        return "missing"
    if value <= -100.0:
        return "<=-100"
    if value <= -50.0:
        return "(-100,-50]"
    if value <= -12.430587:
        return "(-50,-12.430587]"
    if value < 0.0:
        return "(-12.430587,0)"
    return ">=0"


def _objective_delta_stats(rows: list[dict[str, str]]) -> dict[str, Any]:
    values = [
        value
        for value in (_as_float(row.get("single_objective_delta")) for row in rows)
        if value is not None
    ]
    if not values:
        return {"count": 0}
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / float(len(values)),
    }


def _compact_row(row: dict[str, str]) -> dict[str, Any]:
    return {
        "impact_dataset": row.get("impact_dataset", ""),
        "case_id": row.get("case_id", ""),
        "candidate_id": row.get("candidate_id", ""),
        "instance": row.get("instance", ""),
        "context_hash": row.get("context_hash", ""),
        "task_set": row.get("task_set", ""),
        "sequence": row.get("sequence", ""),
        "true_reduced_cost": _as_float(row.get("true_reduced_cost")),
        "single_objective_delta": _as_float(row.get("single_objective_delta")),
        "single_impact_class": row.get("single_impact_class", ""),
        "new_task_set": _as_bool(row.get("new_task_set")),
        "strict_replacement_by_cost": _as_bool(row.get("strict_replacement_by_cost")),
        "active_support_changing": _as_bool(row.get("active_support_changing")),
    }


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "impact_dataset",
        "case_id",
        "candidate_id",
        "instance",
        "context_hash",
        "task_set",
        "sequence",
        "true_reduced_cost",
        "cost",
        "new_task_set",
        "strict_replacement_by_cost",
        "active_support_changing",
        "single_objective_delta",
        "single_impact_class",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _anatomy(rows: list[dict[str, str]], rule: dict[str, Any]) -> dict[str, Any]:
    false_positives = [
        row
        for row in rows
        if _predict(row, rule) and row.get("single_impact_class") == "noop"
    ]
    false_negatives = [
        row
        for row in rows
        if not _predict(row, rule) and row.get("single_impact_class") == "improved"
    ]
    selected = [row for row in rows if _predict(row, rule)]
    positives = [row for row in rows if row.get("single_impact_class") == "improved"]
    fp_new_task_set_noop = [
        row for row in false_positives if _as_bool(row.get("new_task_set"))
    ]
    fn_new_task_set_improved = [
        row for row in false_negatives if _as_bool(row.get("new_task_set"))
    ]
    return {
        "row_count": len(rows),
        "selected_count": len(selected),
        "positive_count": len(positives),
        "false_positive_count": len(false_positives),
        "false_negative_count": len(false_negatives),
        "false_positive_by_dataset": _counter(false_positives, "impact_dataset"),
        "false_negative_by_dataset": _counter(false_negatives, "impact_dataset"),
        "false_positive_by_instance": _top_counter(false_positives, "instance"),
        "false_negative_by_instance": _top_counter(false_negatives, "instance"),
        "false_positive_by_context": _top_counter(false_positives, "context_hash"),
        "false_negative_by_context": _top_counter(false_negatives, "context_hash"),
        "false_positive_flag_counts": _flag_counts(false_positives),
        "false_negative_flag_counts": _flag_counts(false_negatives),
        "false_positive_true_rc_buckets": dict(
            Counter(_true_rc_bucket(_as_float(row.get("true_reduced_cost"))) for row in false_positives)
        ),
        "false_negative_true_rc_buckets": dict(
            Counter(_true_rc_bucket(_as_float(row.get("true_reduced_cost"))) for row in false_negatives)
        ),
        "false_positive_objective_delta": _objective_delta_stats(false_positives),
        "false_negative_objective_delta": _objective_delta_stats(false_negatives),
        "false_positive_new_task_set_noop_count": len(fp_new_task_set_noop),
        "false_negative_new_task_set_improved_count": len(fn_new_task_set_improved),
        "false_positive_examples": [_compact_row(row) for row in false_positives[:12]],
        "false_negative_examples": [_compact_row(row) for row in false_negatives[:12]],
    }


def build_summary(inputs: tuple[Path, ...]) -> dict[str, Any]:
    selector = _read_json(REPLAY_SELECTOR_SUMMARY)
    rule = dict(selector.get("recommended_selector_rule") or {})
    rows = _read_rows(inputs)
    anatomy = _anatomy(rows, rule)
    checks = {
        "has_expected_row_count": anatomy["row_count"] == 280,
        "uses_true_rc_recommended_rule": rule.get("feature") == "true_reduced_cost",
        "has_false_positives": anatomy["false_positive_count"] > 0,
        "has_false_negatives": anatomy["false_negative_count"] > 0,
        "false_positives_include_new_task_set_noops": (
            anatomy["false_positive_new_task_set_noop_count"] > 0
        ),
        "false_negatives_include_new_task_set_improvements": (
            anatomy["false_negative_new_task_set_improved_count"] > 0
        ),
        "selector_still_not_production_validated": (
            selector.get("production_validation", {}).get("production_validated_selector")
            is False
        ),
    }
    return {
        "schema_version": "selector_error_anatomy_v1",
        "sources": {
            "replay_selector_summary": str(REPLAY_SELECTOR_SUMMARY),
            "candidate_inputs": [str(path) for path in inputs],
        },
        "recommended_selector_candidate": selector.get("recommended_selector_candidate"),
        "recommended_selector_rule": rule,
        "anatomy": anatomy,
        "interpretation": (
            "The recommended true-RC threshold has both false positives and false "
            "negatives. Some false positives are new task-set negative columns with "
            "zero replay impact, and some false negatives are new task-set columns "
            "with positive replay impact. Therefore true-RC and new-task-set signals "
            "are insufficient as a production addition-before selector."
        ),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    anatomy = summary["anatomy"]
    lines = [
        "# Root Cause Selector Error Anatomy 报告",
        "",
        "日期：2026-06-13",
        "",
        "## 目标",
        "",
        "本报告只读分析当前 replay-calibrated addition-before selector 的错误分布，",
        "不运行 BPC、不修改 solver、不产生 certificate 或 lower-bound effect。",
        "",
        "## 当前推荐规则",
        "",
        "```text",
        f"recommended_selector_candidate = {summary.get('recommended_selector_candidate')}",
        f"recommended_selector_rule = {summary.get('recommended_selector_rule')}",
        "```",
        "",
        "## 错误总览",
        "",
        "```text",
        f"row_count = {anatomy['row_count']}",
        f"selected_count = {anatomy['selected_count']}",
        f"positive_count = {anatomy['positive_count']}",
        f"false_positive_count = {anatomy['false_positive_count']}",
        f"false_negative_count = {anatomy['false_negative_count']}",
        f"false_positive_new_task_set_noop_count = {anatomy['false_positive_new_task_set_noop_count']}",
        f"false_negative_new_task_set_improved_count = {anatomy['false_negative_new_task_set_improved_count']}",
        "```",
        "",
        "## 数据集分布",
        "",
        "```json",
        json.dumps(
            {
                "false_positive_by_dataset": anatomy["false_positive_by_dataset"],
                "false_negative_by_dataset": anatomy["false_negative_by_dataset"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 解释",
        "",
        "当前 true-RC 阈值规则同时存在 false positive 和 false negative：",
        "一部分 false positive 是 new task-set 负列，但 replay impact 为 0；",
        "一部分 false negative 是 new task-set 列，却有正向 replay impact。",
        "因此 true-RC 和 new-task-set 信号不足以作为 production addition-before selector。",
        "",
        "这说明当前规则只能作为 calibration signal，不能作为 production selector。",
        "下一步仍必须要求 context / instance / dataset holdout 与 full BPC A/B。",
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
    false_positives = summary["anatomy"]["false_positive_examples"]
    false_negatives = summary["anatomy"]["false_negative_examples"]
    _write_rows(args.output_dir / "false_positive_examples.csv", false_positives)
    _write_rows(args.output_dir / "false_negative_examples.csv", false_negatives)
    _write_report(args.report, summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

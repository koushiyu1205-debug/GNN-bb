#!/usr/bin/env python3
"""Audit the true-RC threshold frontier for the replay selector.

This script is read-only. It checks whether any true-reduced-cost threshold can
simultaneously avoid false positives and false negatives on the exact-context
replay candidate rows.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_threshold_frontier_20260613"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_selector_threshold_frontier_zh.md"
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
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("single_impact_class") not in {"improved", "noop"}:
                    continue
                if not _as_bool(row.get("single_treatment_found")):
                    continue
                if _as_float(row.get("true_reduced_cost")) is None:
                    continue
                rows.append(dict(row))
    return rows


def _evaluate_threshold(rows: list[dict[str, str]], threshold: float) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    for row in rows:
        pred = float(row["true_reduced_cost"]) <= float(threshold)
        positive = row.get("single_impact_class") == "improved"
        if pred and positive:
            tp += 1
        elif pred and not positive:
            fp += 1
        elif not pred and positive:
            fn += 1
        else:
            tn += 1
    precision = None if tp + fp <= 0 else tp / float(tp + fp)
    recall = None if tp + fn <= 0 else tp / float(tp + fn)
    accuracy = None if tp + fp + tn + fn <= 0 else (tp + tn) / float(tp + fp + tn + fn)
    f1 = 0.0
    if precision and recall:
        f1 = 2.0 * precision * recall / (precision + recall)
    return {
        "threshold": threshold,
        "total": tp + fp + tn + fn,
        "predicted_positive": tp + fp,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "accuracy": accuracy,
        "f1": f1,
    }


def _rounded_metric(metric: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in metric.items():
        if isinstance(value, float):
            result[key] = round(value, 12)
        else:
            result[key] = value
    return result


def build_summary(inputs: tuple[Path, ...]) -> dict[str, Any]:
    rows = _read_rows(inputs)
    selector = _read_json(REPLAY_SELECTOR_SUMMARY)
    recommended_rule = dict(selector.get("recommended_selector_rule") or {})
    recommended_threshold = float(recommended_rule.get("threshold", -12.430587))
    values = sorted({float(row["true_reduced_cost"]) for row in rows})
    thresholds = list(values)
    if values:
        thresholds.append(min(values) - 1.0e-6)
    metrics = [_evaluate_threshold(rows, threshold) for threshold in thresholds]
    best_f1 = max(metrics, key=lambda item: item["f1"]) if metrics else {}
    zero_fp = [item for item in metrics if item["fp"] == 0]
    zero_fn = [item for item in metrics if item["fn"] == 0]
    perfect = [item for item in metrics if item["fp"] == 0 and item["fn"] == 0]
    strict = [
        item
        for item in metrics
        if (item.get("precision") or 0.0) >= 0.75
        and (item.get("recall") or 0.0) >= 0.5
    ]
    best_zero_fp = (
        max(zero_fp, key=lambda item: item.get("recall") or 0.0) if zero_fp else {}
    )
    best_zero_fn = (
        max(zero_fn, key=lambda item: item.get("precision") or -1.0) if zero_fn else {}
    )
    recommended = _evaluate_threshold(rows, recommended_threshold)
    label_counts = {
        "improved": sum(1 for row in rows if row.get("single_impact_class") == "improved"),
        "noop": sum(1 for row in rows if row.get("single_impact_class") == "noop"),
    }
    checks = {
        "has_expected_rows": len(rows) == 280,
        "no_perfect_true_rc_threshold": not perfect,
        "zero_fp_recall_too_low": (best_zero_fp.get("recall") or 0.0) < 0.5,
        "zero_fn_has_many_false_positives": int(best_zero_fn.get("fp", 0)) > 0,
        "recommended_has_both_error_types": recommended["fp"] > 0
        and recommended["fn"] > 0,
        "best_f1_still_has_both_error_types": best_f1.get("fp", 0) > 0
        and best_f1.get("fn", 0) > 0,
    }
    return {
        "schema_version": "selector_threshold_frontier_v1",
        "sources": {
            "replay_selector_summary": str(REPLAY_SELECTOR_SUMMARY),
            "candidate_inputs": [str(path) for path in inputs],
        },
        "row_count": len(rows),
        "label_counts": label_counts,
        "threshold_count": len(metrics),
        "recommended_threshold_metrics": _rounded_metric(recommended),
        "best_f1_threshold_metrics": _rounded_metric(best_f1),
        "best_zero_false_positive_threshold_metrics": _rounded_metric(best_zero_fp),
        "best_zero_false_negative_threshold_metrics": _rounded_metric(best_zero_fn),
        "perfect_threshold_count": len(perfect),
        "strict_gate_threshold_count": len(strict),
        "interpretation": (
            "没有任何 true-RC 阈值能把 improved 与 noop replay candidates 完美分开。"
            "零 false-positive 阈值会损失太多 recall；零 false-negative 阈值会放入"
            "大量 no-op columns。"
        ),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Root Cause Selector Threshold Frontier 报告",
        "",
        "日期：2026-06-13",
        "",
        "## 目标",
        "",
        "本报告只读分析 true-RC 阈值前沿，验证是否存在另一个阈值可以同时消除",
        "false positive 和 false negative。不运行 BPC，不修改 solver。",
        "",
        "## 关键结果",
        "",
        "```text",
        f"row_count = {summary['row_count']}",
        f"threshold_count = {summary['threshold_count']}",
        f"perfect_threshold_count = {summary['perfect_threshold_count']}",
        f"strict_gate_threshold_count = {summary['strict_gate_threshold_count']}",
        f"recommended_threshold_metrics = {summary['recommended_threshold_metrics']}",
        f"best_f1_threshold_metrics = {summary['best_f1_threshold_metrics']}",
        f"best_zero_false_positive_threshold_metrics = {summary['best_zero_false_positive_threshold_metrics']}",
        f"best_zero_false_negative_threshold_metrics = {summary['best_zero_false_negative_threshold_metrics']}",
        "```",
        "",
        "## 解释",
        "",
        summary["interpretation"],
        "",
        "因此，当前问题不是简单调 true-RC 阈值即可解决；仍需要更强的",
        "addition-before selector，并通过 context / instance / dataset holdout。",
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

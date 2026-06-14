#!/usr/bin/env python3
"""Analyze failed context folds for addition-before selector audits.

This read-only audit consumes train-holdout selector summaries and classifies
why context folds fail: missed positive contexts, false positives in no-positive
contexts, or mixed precision/recall failures.  It is intended to pin the root
cause more tightly to context/RMP trajectory variation rather than generic
instance or dataset effects.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_TRAIN_HOLDOUT = Path(
    "BPC_future/results/root_cause_selector_rule_family_train_holdout_20260614/"
    "summary.json"
)
DEFAULT_TRAIN_HOLDOUT_20ONLY = Path(
    "BPC_future/results/root_cause_selector_rule_family_train_holdout_20only_20260614/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_context_fold_anatomy_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_context_fold_anatomy_zh.md"
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _failure_kind(fold: dict[str, Any]) -> str:
    metrics = fold.get("test", {})
    tp = int(metrics.get("tp") or 0)
    fp = int(metrics.get("fp") or 0)
    fn = int(metrics.get("fn") or 0)
    predicted = int(metrics.get("predicted_positive") or 0)
    positive_count = tp + fn
    if fold.get("material_pass"):
        return "material_pass"
    if positive_count <= 0 and fp > 0:
        return "false_positive_no_positive_context"
    if positive_count > 0 and predicted <= 0:
        return "missed_positive_context"
    if positive_count > 0 and fp > 0:
        return "mixed_low_precision_or_recall_context"
    return "other_material_failure"


def _context_summary(summary: dict[str, Any]) -> dict[str, Any]:
    context = summary.get("holdout_summaries", {}).get("context_hash", {})
    folds = list(context.get("folds", []) or [])
    enriched = []
    for fold in folds:
        metrics = dict(fold.get("test", {}) or {})
        tp = int(metrics.get("tp") or 0)
        fp = int(metrics.get("fp") or 0)
        fn = int(metrics.get("fn") or 0)
        tn = int(metrics.get("tn") or 0)
        total = int(metrics.get("total") or 0)
        positive_count = tp + fn
        noop_count = fp + tn
        positive_rate = None if total <= 0 else positive_count / float(total)
        enriched.append(
            {
                "holdout": fold.get("holdout"),
                "selected_rule": fold.get("selected_rule"),
                "material_pass": bool(fold.get("material_pass")),
                "strict_pass": bool(fold.get("strict_pass")),
                "failure_kind": _failure_kind(fold),
                "total": total,
                "positive_count": positive_count,
                "noop_count": noop_count,
                "positive_rate": positive_rate,
                "metrics": metrics,
            }
        )
    failures = [fold for fold in enriched if not fold["material_pass"]]
    failure_counts = Counter(fold["failure_kind"] for fold in failures)
    low_positive_contexts = [
        fold
        for fold in enriched
        if fold["positive_rate"] is not None and fold["positive_rate"] <= 0.2
    ]
    high_positive_contexts = [
        fold
        for fold in enriched
        if fold["positive_rate"] is not None and fold["positive_rate"] >= 0.8
    ]
    return {
        "row_count": int(summary.get("row_count") or 0),
        "row_filter": summary.get("row_filter", {}),
        "context_fold_count": int(context.get("fold_count") or 0),
        "context_material_passing_fold_count": int(
            context.get("material_passing_fold_count") or 0
        ),
        "context_strict_passing_fold_count": int(
            context.get("strict_passing_fold_count") or 0
        ),
        "context_failure_count": len(failures),
        "context_failure_kind_counts": dict(failure_counts),
        "low_positive_context_count": len(low_positive_contexts),
        "high_positive_context_count": len(high_positive_contexts),
        "low_positive_fail_count": sum(
            1 for fold in low_positive_contexts if not fold["material_pass"]
        ),
        "high_positive_fail_count": sum(
            1 for fold in high_positive_contexts if not fold["material_pass"]
        ),
        "failed_context_samples": failures[:12],
        "low_positive_samples": low_positive_contexts[:8],
        "high_positive_samples": high_positive_contexts[:8],
    }


def build_summary(all_path: Path, twenty_path: Path) -> dict[str, Any]:
    all_summary = _read_json(all_path)
    twenty_summary = _read_json(twenty_path)
    all_context = _context_summary(all_summary)
    twenty_context = _context_summary(twenty_summary)
    checks = {
        "all_rows_context_has_failures": all_context["context_failure_count"] > 0,
        "twenty_only_context_has_failures": twenty_context["context_failure_count"] > 0,
        "twenty_only_failure_not_from_small_instance": (
            twenty_context["row_filter"].get("task_count") == 20
            and twenty_context["context_failure_count"] > 0
        ),
        "has_false_positive_no_positive_contexts": (
            twenty_context["context_failure_kind_counts"].get(
                "false_positive_no_positive_context", 0
            )
            > 0
        ),
        "has_missed_positive_contexts": (
            twenty_context["context_failure_kind_counts"].get(
                "missed_positive_context", 0
            )
            > 0
        ),
        "context_rate_extremes_present": (
            twenty_context["low_positive_context_count"] > 0
            and twenty_context["high_positive_context_count"] > 0
        ),
    }
    return {
        "schema_version": "selector_context_fold_anatomy_v1",
        "sources": {
            "all_rows": str(all_path),
            "twenty_only": str(twenty_path),
        },
        "all_rows": all_context,
        "twenty_only": twenty_context,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "Context-fold failures include both false positives in no-positive "
            "contexts and missed positive contexts. This supports the current "
            "root-cause diagnosis that selector stability depends on context/RMP "
            "trajectory, not just local column features."
        ),
    }


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    all_rows = summary["all_rows"]
    twenty = summary["twenty_only"]
    lines = [
        "# Selector Context Fold Anatomy 审计",
        "",
        "日期：2026-06-14",
        "",
        "## 目标",
        "",
        "复查 train-holdout rule-family 审计中失败的 context folds，区分失败来自",
        "全 noop context 的 false positive，还是有正例 context 的 missed positive。",
        "该审计只读已有 replay 与 selector summary，不运行求解器。",
        "",
        "## 结论",
        "",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "selector_context_fold_anatomy = current",
        "all_context_material_passing_folds = "
        f"{all_rows['context_material_passing_fold_count']}/{all_rows['context_fold_count']}",
        "twenty_context_material_passing_folds = "
        f"{twenty['context_material_passing_fold_count']}/{twenty['context_fold_count']}",
        f"twenty_context_failure_kind_counts = {twenty['context_failure_kind_counts']}",
        f"twenty_low_positive_context_count = {twenty['low_positive_context_count']}",
        f"twenty_high_positive_context_count = {twenty['high_positive_context_count']}",
        "production_validated_selector = false",
        "",
        "解释：20-only 下仍有 context fold 失败，且失败同时包含两类相反形态：",
        "某些 context 几乎全是 noop 但规则仍选中 false positive；另一些 context",
        "存在正例但训练集选出的规则完全漏掉正例。这说明问题不是单一阈值偏松或",
        "偏紧，而是 context/RMP trajectory 改变了 returned batch 的有效性。",
        "",
        "## 20-only Failed Context Samples",
        "",
        "| Context | Failure Kind | Total | Pos | Noop | Rule | Test TP/FP/FN |",
        "|---|---|---:|---:|---:|---|---:|",
    ]
    for fold in twenty["failed_context_samples"][:10]:
        metrics = fold["metrics"]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(fold["holdout"]),
                    str(fold["failure_kind"]),
                    str(fold["total"]),
                    str(fold["positive_count"]),
                    str(fold["noop_count"]),
                    str(fold["selected_rule"]),
                    f"{metrics.get('tp')}/{metrics.get('fp')}/{metrics.get('fn')}",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "这进一步收紧当前根因：selector 不稳主要发生在 context 维度，",
            "而不是 instance/dataset 粗粒度。下一步若继续 selector 路线，必须找",
            "addition-before 的 RMP/context trajectory 特征；继续只调 true-RC / cost /",
            "new-task-set 规则无法解释这些相反失败形态。",
            "",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all-summary", type=Path, default=DEFAULT_TRAIN_HOLDOUT)
    parser.add_argument(
        "--twenty-summary", type=Path, default=DEFAULT_TRAIN_HOLDOUT_20ONLY
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    summary = build_summary(args.all_summary, args.twenty_summary)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(summary, args.report)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

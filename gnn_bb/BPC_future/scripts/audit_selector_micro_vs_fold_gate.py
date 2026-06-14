#!/usr/bin/env python3
"""Audit micro-average selector gates against fold-level robustness.

The exact replay selector gate can report micro-average passing features. This
read-only audit checks whether those features also pass every context,
instance, and dataset fold. A production selector must not rely on aggregate
micro averages that hide bad held-out contexts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path(
    "BPC_future/results/"
    "root_cause_counterfactual_replay_selector_gate_with_target002_pt03_20260613/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_micro_vs_fold_gate_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_micro_vs_fold_gate_zh.md"
)

HOLDOUT_KEYS = ("context_hash", "instance", "impact_dataset")


def _as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _passes(metrics: dict[str, Any]) -> bool:
    precision = _as_float(metrics.get("precision"))
    recall = _as_float(metrics.get("recall"))
    return (
        precision is not None
        and recall is not None
        and precision >= 0.75
        and recall >= 0.5
    )


def _fold_failure_reason(metrics: dict[str, Any]) -> str:
    precision = _as_float(metrics.get("precision"))
    recall = _as_float(metrics.get("recall"))
    predicted = int(metrics.get("predicted_positive") or 0)
    fp = int(metrics.get("fp") or 0)
    fn = int(metrics.get("fn") or 0)
    if predicted == 0 and fn > 0:
        return "missed_positive_fold"
    if fp > 0 and (precision is None or precision < 0.75):
        return "low_precision_false_positive_fold"
    if recall is not None and recall < 0.5:
        return "low_recall_fold"
    if precision is None:
        return "no_positive_predictions"
    return "strict_gate_failed"


def build_summary(input_path: Path) -> dict[str, Any]:
    source = json.loads(input_path.read_text(encoding="utf-8"))
    micro_features = list(source.get("passing_features_all_holdouts", []) or [])
    holdout_by_feature = source.get("holdout_by_feature", {})
    feature_summaries: dict[str, Any] = {}
    for feature in micro_features:
        per_holdout: dict[str, Any] = {}
        for holdout_key in HOLDOUT_KEYS:
            payload = holdout_by_feature.get(holdout_key, {}).get(feature, {})
            fold_count = int(payload.get("fold_count") or 0)
            passing_fold_count = int(payload.get("passing_fold_count") or 0)
            worst_folds = list(payload.get("worst_folds", []) or [])
            failing_examples: list[dict[str, Any]] = []
            for fold in worst_folds[:5]:
                metrics = dict(fold.get("test", {}) or {})
                if _passes(metrics):
                    continue
                failing_examples.append(
                    {
                        "holdout": fold.get("holdout"),
                        "reason": _fold_failure_reason(metrics),
                        "test": metrics,
                        "rule": fold.get("rule"),
                    }
                )
            micro = dict(payload.get("micro", {}) or {})
            per_holdout[holdout_key] = {
                "micro": micro,
                "micro_passes_strict": bool(payload.get("passes_strict_gate")),
                "fold_count": fold_count,
                "passing_fold_count": passing_fold_count,
                "all_folds_pass": fold_count > 0 and passing_fold_count == fold_count,
                "failing_fold_count": max(fold_count - passing_fold_count, 0),
                "failing_examples": failing_examples,
            }
        feature_summaries[feature] = {
            "passes_micro_all_holdouts": all(
                per_holdout[key]["micro_passes_strict"] for key in HOLDOUT_KEYS
            ),
            "passes_all_folds_all_holdouts": all(
                per_holdout[key]["all_folds_pass"] for key in HOLDOUT_KEYS
            ),
            "holdouts": per_holdout,
        }
    robust_features = [
        feature
        for feature, payload in feature_summaries.items()
        if payload["passes_all_folds_all_holdouts"]
    ]
    checks = {
        "has_micro_passing_features": bool(micro_features),
        "no_micro_feature_passes_all_fold_gates": not robust_features,
        "true_rc_micro_passes_but_context_folds_fail": (
            "true_reduced_cost" in feature_summaries
            and feature_summaries["true_reduced_cost"]["holdouts"]["context_hash"][
                "micro_passes_strict"
            ]
            and not feature_summaries["true_reduced_cost"]["holdouts"][
                "context_hash"
            ]["all_folds_pass"]
        ),
        "new_task_set_micro_passes_but_dataset_folds_fail": (
            "new_task_set" in feature_summaries
            and feature_summaries["new_task_set"]["holdouts"]["impact_dataset"][
                "micro_passes_strict"
            ]
            and not feature_summaries["new_task_set"]["holdouts"][
                "impact_dataset"
            ]["all_folds_pass"]
        ),
    }
    return {
        "schema_version": "selector_micro_vs_fold_gate_v1",
        "source": str(input_path),
        "row_count": int(source.get("row_count") or 0),
        "label_counts": dict(source.get("label_counts", {}) or {}),
        "micro_passing_features": micro_features,
        "robust_all_fold_passing_features": robust_features,
        "feature_summaries": feature_summaries,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "Micro-average selector gates can hide context or dataset folds "
            "where a rule either predicts no useful columns or produces false "
            "positives. The current exact replay passing features are "
            "calibration signals, not production selectors."
        ),
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "None"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    features = summary["feature_summaries"]
    lines = [
        "# Selector Micro-vs-Fold Gate 审计",
        "",
        "日期：2026-06-14",
        "",
        "## 目标",
        "",
        "复查 exact replay selector gate 中看似通过的单特征规则，确认它们是否只是",
        "micro-average 通过，还是每个 context / instance / dataset fold 都稳定通过。",
        "本脚本只读已有 selector gate summary，不运行求解器。",
        "",
        "## 结论",
        "",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "selector_micro_vs_fold_gate = current",
        f"row_count = {summary['row_count']}",
        f"label_counts = {summary['label_counts']}",
        f"micro_passing_features = {summary['micro_passing_features']}",
        "robust_all_fold_passing_feature_count = "
        f"{len(summary['robust_all_fold_passing_features'])}",
        "",
        "关键结论：旧 gate 的 `passing_features_all_holdouts` 是 micro-average 通过；",
        "这些特征没有一个能在所有 held-out folds 上都过严格门槛。",
        "",
        "## Feature Fold Summary",
        "",
        "| Feature | Holdout | Micro P/R | Passing Folds | All Folds Pass | Failing Folds |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for feature, payload in features.items():
        for holdout_key in HOLDOUT_KEYS:
            holdout = payload["holdouts"][holdout_key]
            micro = holdout["micro"]
            lines.append(
                "| "
                + " | ".join(
                    [
                        feature,
                        holdout_key,
                        f"{_fmt(micro.get('precision'))}/{_fmt(micro.get('recall'))}",
                        f"{holdout['passing_fold_count']}/{holdout['fold_count']}",
                        str(holdout["all_folds_pass"]).lower(),
                        str(holdout["failing_fold_count"]),
                    ]
                )
                + " |"
            )
    true_rc_context = features["true_reduced_cost"]["holdouts"]["context_hash"]
    new_task_dataset = features["new_task_set"]["holdouts"]["impact_dataset"]
    lines.extend(
        [
            "",
            "## 关键失败模式",
            "",
            "```text",
            "true_rc_context_micro_precision = "
            f"{_fmt(true_rc_context['micro'].get('precision'))}",
            "true_rc_context_micro_recall = "
            f"{_fmt(true_rc_context['micro'].get('recall'))}",
            "true_rc_context_passing_folds = "
            f"{true_rc_context['passing_fold_count']}/{true_rc_context['fold_count']}",
            "new_task_set_dataset_micro_precision = "
            f"{_fmt(new_task_dataset['micro'].get('precision'))}",
            "new_task_set_dataset_micro_recall = "
            f"{_fmt(new_task_dataset['micro'].get('recall'))}",
            "new_task_set_dataset_passing_folds = "
            f"{new_task_dataset['passing_fold_count']}/{new_task_dataset['fold_count']}",
            "robust_all_fold_passing_feature_count = "
            f"{len(summary['robust_all_fold_passing_features'])}",
            "production_validated_selector = false",
            "```",
            "",
            "解释：row-level micro average 会被大 fold 和重复 candidate rows 主导；",
            "但生产 selector 要面对的是新的 context / instance / dataset，不应依赖某些",
            "held-out folds 失败后仍被总体 micro average 掩盖的规则。",
            "",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    summary = build_summary(args.input)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    write_report(summary, args.report)
    compact = {
        "all_checks_pass": summary["all_checks_pass"],
        "micro_passing_features": summary["micro_passing_features"],
        "robust_all_fold_passing_features": summary[
            "robust_all_fold_passing_features"
        ],
        "checks": summary["checks"],
        "summary": str(summary_path),
        "report": str(args.report),
    }
    print(json.dumps(compact, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

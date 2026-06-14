#!/usr/bin/env python3
"""Audit aggregate model selector gates against fold-level robustness.

This read-only audit checks whether exact replay model selector candidates that
pass aggregate leave-one-context/instance/dataset metrics also pass every held
out fold. It does not train new models or run BPC; it reads the existing model
selector gate summary.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path(
    "BPC_future/results/"
    "root_cause_counterfactual_replay_model_selector_gate_with_target002_pt03_20260613/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_model_micro_vs_fold_gate_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_model_micro_vs_fold_gate_zh.md"
)

HOLDOUT_KEYS = ("leave_one_context", "leave_one_instance", "leave_one_dataset")


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
    fp = int(metrics.get("fp") or 0)
    fn = int(metrics.get("fn") or 0)
    tp = int(metrics.get("tp") or 0)
    if tp == 0 and fn > 0:
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
    aggregate_passing_by_holdout: dict[str, list[str]] = {}
    model_names = sorted(
        {
            model_name
            for holdout_key in HOLDOUT_KEYS
            for model_name in source.get(holdout_key, {}).get("models", {})
        }
    )
    model_summaries: dict[str, Any] = {}
    for model_name in model_names:
        holdouts: dict[str, Any] = {}
        for holdout_key in HOLDOUT_KEYS:
            holdout = source.get(holdout_key, {})
            model = dict(holdout.get("models", {}).get(model_name, {}) or {})
            groups = list(model.get("groups", []) or [])
            passing_groups = [group for group in groups if _passes(group)]
            failing_groups = [group for group in groups if not _passes(group)]
            aggregate_passes = _passes(model)
            if aggregate_passes:
                aggregate_passing_by_holdout.setdefault(holdout_key, []).append(
                    model_name
                )
            holdouts[holdout_key] = {
                "aggregate": {
                    key: model.get(key)
                    for key in (
                        "total",
                        "accuracy",
                        "precision",
                        "recall",
                        "tp",
                        "fp",
                        "tn",
                        "fn",
                    )
                },
                "aggregate_passes_strict": aggregate_passes,
                "fold_count": len(groups),
                "passing_fold_count": len(passing_groups),
                "all_folds_pass": bool(groups) and len(passing_groups) == len(groups),
                "failing_fold_count": len(failing_groups),
                "failing_examples": [
                    {
                        "held_out": group.get("held_out"),
                        "reason": _fold_failure_reason(group),
                        "metrics": {
                            key: group.get(key)
                            for key in (
                                "total",
                                "accuracy",
                                "precision",
                                "recall",
                                "tp",
                                "fp",
                                "tn",
                                "fn",
                            )
                        },
                    }
                    for group in failing_groups[:5]
                ],
            }
        model_summaries[model_name] = {
            "aggregate_passes_all_holdouts": all(
                holdouts[key]["aggregate_passes_strict"] for key in HOLDOUT_KEYS
            ),
            "passes_all_folds_all_holdouts": all(
                holdouts[key]["all_folds_pass"] for key in HOLDOUT_KEYS
            ),
            "holdouts": holdouts,
        }
    aggregate_all_holdout_models = [
        model
        for model, payload in model_summaries.items()
        if payload["aggregate_passes_all_holdouts"]
    ]
    robust_all_fold_models = [
        model
        for model, payload in model_summaries.items()
        if payload["passes_all_folds_all_holdouts"]
    ]
    checks = {
        "has_aggregate_all_holdout_models": bool(aggregate_all_holdout_models),
        "no_aggregate_model_passes_all_fold_gates": not robust_all_fold_models,
        "nearest_centroid_context_folds_fail": (
            "nearest_centroid" in model_summaries
            and model_summaries["nearest_centroid"]["holdouts"][
                "leave_one_context"
            ]["aggregate_passes_strict"]
            and not model_summaries["nearest_centroid"]["holdouts"][
                "leave_one_context"
            ]["all_folds_pass"]
        ),
        "shallow_tree_dataset_folds_fail": (
            "shallow_tree_depth3" in model_summaries
            and model_summaries["shallow_tree_depth3"]["holdouts"][
                "leave_one_dataset"
            ]["aggregate_passes_strict"]
            and not model_summaries["shallow_tree_depth3"]["holdouts"][
                "leave_one_dataset"
            ]["all_folds_pass"]
        ),
    }
    return {
        "schema_version": "selector_model_micro_vs_fold_gate_v1",
        "source": str(input_path),
        "row_count": int(source.get("row_count") or 0),
        "label_counts": dict(source.get("label_counts", {}) or {}),
        "aggregate_passing_by_holdout": aggregate_passing_by_holdout,
        "aggregate_all_holdout_models": aggregate_all_holdout_models,
        "robust_all_fold_passing_models": robust_all_fold_models,
        "model_summaries": model_summaries,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "Aggregate model selector gates have calibration signal, but no "
            "model passes every context, instance, and dataset fold. These "
            "models are not production selectors."
        ),
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "None"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    models = summary["model_summaries"]
    lines = [
        "# Selector Model Micro-vs-Fold Gate 审计",
        "",
        "日期：2026-06-14",
        "",
        "## 目标",
        "",
        "复查 exact replay model selector gate 中看似通过的简单模型，确认它们是否",
        "只是 aggregate micro 通过，还是每个 context / instance / dataset fold 都稳定通过。",
        "本脚本只读已有 model selector gate summary，不重新运行求解器。",
        "",
        "## 结论",
        "",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "selector_model_micro_vs_fold_gate = current",
        f"row_count = {summary['row_count']}",
        f"label_counts = {summary['label_counts']}",
        f"aggregate_all_holdout_models = {summary['aggregate_all_holdout_models']}",
        "robust_all_fold_passing_model_count = "
        f"{len(summary['robust_all_fold_passing_models'])}",
        "",
        "关键结论：`nearest_centroid` / `shallow_tree_depth3` 等模型有 aggregate",
        " calibration signal，但没有任何模型能在所有 held-out folds 上都过严格门槛。",
        "",
        "## Model Fold Summary",
        "",
        "| Model | Holdout | Aggregate P/R | Passing Folds | All Folds Pass | Failing Folds |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for model_name, payload in models.items():
        for holdout_key in HOLDOUT_KEYS:
            holdout = payload["holdouts"][holdout_key]
            aggregate = holdout["aggregate"]
            lines.append(
                "| "
                + " | ".join(
                    [
                        model_name,
                        holdout_key,
                        f"{_fmt(aggregate.get('precision'))}/{_fmt(aggregate.get('recall'))}",
                        f"{holdout['passing_fold_count']}/{holdout['fold_count']}",
                        str(holdout["all_folds_pass"]).lower(),
                        str(holdout["failing_fold_count"]),
                    ]
                )
                + " |"
            )
    nearest_context = models["nearest_centroid"]["holdouts"]["leave_one_context"]
    shallow_dataset = models["shallow_tree_depth3"]["holdouts"]["leave_one_dataset"]
    lines.extend(
        [
            "",
            "## 关键失败模式",
            "",
            "```text",
            "nearest_centroid_context_aggregate_precision = "
            f"{_fmt(nearest_context['aggregate'].get('precision'))}",
            "nearest_centroid_context_aggregate_recall = "
            f"{_fmt(nearest_context['aggregate'].get('recall'))}",
            "nearest_centroid_context_passing_folds = "
            f"{nearest_context['passing_fold_count']}/{nearest_context['fold_count']}",
            "shallow_tree_dataset_aggregate_precision = "
            f"{_fmt(shallow_dataset['aggregate'].get('precision'))}",
            "shallow_tree_dataset_aggregate_recall = "
            f"{_fmt(shallow_dataset['aggregate'].get('recall'))}",
            "shallow_tree_dataset_passing_folds = "
            f"{shallow_dataset['passing_fold_count']}/{shallow_dataset['fold_count']}",
            "robust_all_fold_passing_model_count = "
            f"{len(summary['robust_all_fold_passing_models'])}",
            "production_validated_selector = false",
            "```",
            "",
            "解释：模型 gate 的 aggregate P/R 能说明当前 replay 样本里有 signal，",
            "但不能证明 selector 在新 context / instance / dataset 上稳定。生产化需要",
            "每个 held-out fold 或更严格外部 A/B 都稳定，而当前没有达到。",
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
        "aggregate_all_holdout_models": summary["aggregate_all_holdout_models"],
        "robust_all_fold_passing_models": summary[
            "robust_all_fold_passing_models"
        ],
        "checks": summary["checks"],
        "summary": str(summary_path),
        "report": str(args.report),
    }
    print(json.dumps(compact, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

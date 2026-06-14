#!/usr/bin/env python3
"""Audit CBF gate robustness with instance/task holdouts.

The audit is read-only and offline.  It retrains a small linear CBF/RMP-impact
gate on non-held-out rows, calibrates a conservative threshold on that training
side only, and evaluates whether the held-out rows produce unsafe false
positives.  It never runs BPC/pricing/RMP and never produces certificates.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any

from BPC_future.scripts.train_cbf_gate import (
    _features,
    _is_no_effect_row,
    _labels,
    _metrics,
    _predict_probabilities,
    _select_conservative_threshold,
    _standardize,
    _standardize_fit,
    _train_logistic,
    cbf_gate_feature_names,
    load_rows,
)


DEFAULT_DATASET = Path("BPC_future/results/cbf_gate_dataset_global_available_20260614/cbf_gate_transitions.jsonl")
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/cbf_gate_holdout_audit_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_cbf_gate_holdout_audit_zh.md"
)


def _group_rows(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(key, ""))].append(row)
    return dict(sorted(groups.items()))


def _can_train(rows: list[dict[str, Any]]) -> bool:
    labels = _labels(rows)
    return bool(rows and sum(labels) > 0 and sum(labels) < len(labels))


def _fold_audit(
    *,
    fold_kind: str,
    holdout_name: str,
    train_rows: list[dict[str, Any]],
    holdout_rows: list[dict[str, Any]],
    epochs: int,
    lr: float,
    l2: float,
    min_precision: float,
    max_false_positive_rate: float,
) -> dict[str, Any]:
    if not train_rows or not holdout_rows:
        return {
            "fold_kind": fold_kind,
            "holdout_name": holdout_name,
            "status": "skipped_empty_fold",
            "train_count": len(train_rows),
            "holdout_count": len(holdout_rows),
            "strict_safety_pass": False,
        }
    if not _can_train(train_rows):
        return {
            "fold_kind": fold_kind,
            "holdout_name": holdout_name,
            "status": "skipped_train_single_label",
            "train_count": len(train_rows),
            "holdout_count": len(holdout_rows),
            "train_label_counts": dict(Counter(str(label) for label in _labels(train_rows))),
            "holdout_label_counts": dict(Counter(str(label) for label in _labels(holdout_rows))),
            "strict_safety_pass": False,
        }
    feature_names = cbf_gate_feature_names(train_rows)
    if not feature_names:
        return {
            "fold_kind": fold_kind,
            "holdout_name": holdout_name,
            "status": "skipped_no_features",
            "train_count": len(train_rows),
            "holdout_count": len(holdout_rows),
            "strict_safety_pass": False,
        }

    train_x_raw = [_features(row, feature_names) for row in train_rows]
    holdout_x_raw = [_features(row, feature_names) for row in holdout_rows]
    train_y = _labels(train_rows)
    holdout_y = _labels(holdout_rows)
    means, stds = _standardize_fit(train_x_raw)
    train_x = _standardize(train_x_raw, means, stds)
    holdout_x = _standardize(holdout_x_raw, means, stds)
    weights = _train_logistic(train_x, train_y, epochs=epochs, lr=lr, l2=l2)
    train_prob = _predict_probabilities(train_x, weights)
    holdout_prob = _predict_probabilities(holdout_x, weights)
    chosen_gate = _select_conservative_threshold(
        train_prob,
        train_y,
        min_precision=min_precision,
        max_false_positive_rate=max_false_positive_rate,
    )
    threshold = float(chosen_gate["threshold"])
    train_metrics = _metrics(train_prob, train_y, threshold)
    holdout_metrics = _metrics(holdout_prob, holdout_y, threshold)
    strict_safety_pass = bool(holdout_metrics["fp"] == 0)
    return {
        "fold_kind": fold_kind,
        "holdout_name": holdout_name,
        "status": "evaluated",
        "train_count": len(train_rows),
        "holdout_count": len(holdout_rows),
        "train_label_counts": dict(Counter(str(label) for label in train_y)),
        "holdout_label_counts": dict(Counter(str(label) for label in holdout_y)),
        "feature_count": len(feature_names),
        "threshold": threshold,
        "chosen_gate": chosen_gate,
        "train_metrics": train_metrics,
        "holdout_metrics": holdout_metrics,
        "strict_safety_pass": strict_safety_pass,
        "productive_holdout_adds": bool(holdout_metrics["predicted_positive"] > 0),
    }


def _audit_group_holdout(
    rows: list[dict[str, Any]],
    *,
    key: str,
    fold_kind: str,
    min_holdout_rows: int,
    epochs: int,
    lr: float,
    l2: float,
    min_precision: float,
    max_false_positive_rate: float,
) -> list[dict[str, Any]]:
    groups = _group_rows(rows, key)
    folds: list[dict[str, Any]] = []
    for name, holdout_rows in groups.items():
        if len(holdout_rows) < int(min_holdout_rows):
            folds.append(
                {
                    "fold_kind": fold_kind,
                    "holdout_name": name,
                    "status": "skipped_too_few_holdout_rows",
                    "holdout_count": len(holdout_rows),
                    "strict_safety_pass": False,
                }
            )
            continue
        train_rows = [row for row in rows if row not in holdout_rows]
        folds.append(
            _fold_audit(
                fold_kind=fold_kind,
                holdout_name=name,
                train_rows=train_rows,
                holdout_rows=holdout_rows,
                epochs=epochs,
                lr=lr,
                l2=l2,
                min_precision=min_precision,
                max_false_positive_rate=max_false_positive_rate,
            )
        )
    return folds


def _fold_summary(folds: list[dict[str, Any]]) -> dict[str, Any]:
    evaluated = [fold for fold in folds if fold.get("status") == "evaluated"]
    skipped = [fold for fold in folds if fold.get("status") != "evaluated"]
    false_positive_folds = [
        fold
        for fold in evaluated
        if int(fold.get("holdout_metrics", {}).get("fp", 0)) > 0
    ]
    productive_folds = [fold for fold in evaluated if fold.get("productive_holdout_adds") is True]
    return {
        "fold_count": len(folds),
        "evaluated_count": len(evaluated),
        "skipped_count": len(skipped),
        "false_positive_fold_count": len(false_positive_folds),
        "productive_fold_count": len(productive_folds),
        "all_evaluated_folds_no_false_positive": bool(evaluated and not false_positive_folds),
        "all_folds_evaluated": len(evaluated) == len(folds) and bool(folds),
        "skipped_status_counts": dict(Counter(str(fold.get("status")) for fold in skipped)),
    }


def audit_cbf_gate_holdout(
    dataset: Path,
    *,
    output_dir: Path,
    report: Path,
    min_holdout_rows: int = 2,
    epochs: int = 500,
    lr: float = 0.05,
    l2: float = 1.0e-4,
    min_precision: float = 0.8,
    max_false_positive_rate: float = 0.05,
) -> dict[str, Any]:
    rows = load_rows(dataset)
    no_effect_count = sum(1 for row in rows if _is_no_effect_row(row))
    base_feature_names = cbf_gate_feature_names(rows)
    instance_folds = _audit_group_holdout(
        rows,
        key="instance",
        fold_kind="leave_one_instance",
        min_holdout_rows=min_holdout_rows,
        epochs=epochs,
        lr=lr,
        l2=l2,
        min_precision=min_precision,
        max_false_positive_rate=max_false_positive_rate,
    )
    task_count_folds = _audit_group_holdout(
        rows,
        key="task_count",
        fold_kind="leave_one_task_count",
        min_holdout_rows=min_holdout_rows,
        epochs=epochs,
        lr=lr,
        l2=l2,
        min_precision=min_precision,
        max_false_positive_rate=max_false_positive_rate,
    )
    instance_summary = _fold_summary(instance_folds)
    task_count_summary = _fold_summary(task_count_folds)
    checks = {
        "all_rows_no_certificate_effect": bool(rows and no_effect_count == len(rows)),
        "has_current_state_features": bool(base_feature_names),
        "instance_holdout_has_evaluated_folds": instance_summary["evaluated_count"] > 0,
        "task_count_holdout_has_evaluated_folds": task_count_summary["evaluated_count"] > 0,
    }
    holdout_safety_pass = bool(
        instance_summary["all_evaluated_folds_no_false_positive"]
        and task_count_summary["all_evaluated_folds_no_false_positive"]
    )
    production_gate_ready = bool(
        holdout_safety_pass
        and instance_summary["all_folds_evaluated"]
        and task_count_summary["all_folds_evaluated"]
        and instance_summary["productive_fold_count"] > 0
        and task_count_summary["productive_fold_count"] > 0
    )
    summary = {
        "schema_version": "cbf_gate_holdout_audit_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "cbf_gate_holdout_audited",
        "dataset": str(dataset),
        "row_count": len(rows),
        "no_effect_row_count": no_effect_count,
        "feature_count": len(base_feature_names),
        "base_feature_names": base_feature_names,
        "label_counts": dict(Counter(str(label) for label in _labels(rows))),
        "min_holdout_rows": int(min_holdout_rows),
        "min_precision": float(min_precision),
        "max_false_positive_rate": float(max_false_positive_rate),
        "instance_holdout_summary": instance_summary,
        "task_count_holdout_summary": task_count_summary,
        "instance_folds": instance_folds,
        "task_count_folds": task_count_folds,
        "holdout_safety_pass": holdout_safety_pass,
        "production_gate_ready": production_gate_ready,
        "production_ready": False,
        "selector_is_pricing_oracle": False,
        "selector_can_certificate": False,
        "official_bound_effect": False,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "goal_complete": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CBF Gate Holdout 稳健性审计报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "按 instance 与 task_count 做 leave-one holdout，审计离线 CBF/RMP-impact gate",
        "是否在留出上下文中保持低误放。该脚本只读已构建数据，不运行 BPC / pricing / RMP，",
        "不生成列，不产生 certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "cbf_gate_holdout_audit = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"holdout_safety_pass = {str(summary['holdout_safety_pass']).lower()}",
        f"production_gate_ready = {str(summary['production_gate_ready']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 摘要",
        "",
        "```json",
        json.dumps(
            {
                "row_count": summary["row_count"],
                "label_counts": summary["label_counts"],
                "feature_count": summary["feature_count"],
                "instance_holdout_summary": summary["instance_holdout_summary"],
                "task_count_holdout_summary": summary["task_count_holdout_summary"],
                "holdout_safety_pass": summary["holdout_safety_pass"],
                "production_gate_ready": summary["production_gate_ready"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 解释",
        "",
        "- `holdout_safety_pass=true` 只表示已评估 folds 没有 false positive；",
        "- `production_gate_ready=false` 表示仍不能接 production worker；",
        "- skipped fold 通常意味着该 instance/task_count 样本太少或训练侧单标签；",
        "- 下一步必须补齐留出覆盖和做 5/10 no-regression + 20-task A/B。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-holdout-rows", type=int, default=2)
    parser.add_argument("--epochs", type=int, default=500)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--l2", type=float, default=1.0e-4)
    parser.add_argument("--min-precision", type=float, default=0.8)
    parser.add_argument("--max-false-positive-rate", type=float, default=0.05)
    args = parser.parse_args(argv)
    summary = audit_cbf_gate_holdout(
        args.dataset,
        output_dir=args.output_dir,
        report=args.report,
        min_holdout_rows=args.min_holdout_rows,
        epochs=args.epochs,
        lr=args.lr,
        l2=args.l2,
        min_precision=args.min_precision,
        max_false_positive_rate=args.max_false_positive_rate,
    )
    print(
        json.dumps(
            {
                "summary": str(args.output_dir / "summary.json"),
                "report": str(args.report),
                "all_checks_pass": summary["all_checks_pass"],
                "holdout_safety_pass": summary["holdout_safety_pass"],
                "production_gate_ready": summary["production_gate_ready"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

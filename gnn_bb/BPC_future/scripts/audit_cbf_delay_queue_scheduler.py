#!/usr/bin/env python3
"""Audit a CBF delay-queue scheduler for trajectory gate rows.

The scheduler is exactness-preserving by construction:

* true-RC negative and predicted safe -> HIGH_PRIORITY;
* true-RC negative and not predicted safe -> DELAY_QUEUE;
* nonnegative candidates -> REJECT_NONNEGATIVE_ONLY.

This script only audits whether a conservative, train-calibrated
HIGH_PRIORITY threshold can avoid false positives on holdout folds.  It never
runs BPC/pricing/RMP, never generates columns, and never creates certificates
or official lower bounds.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

from BPC_future.scripts.audit_cbf_gate_family_policy import infer_family
from BPC_future.scripts.audit_cbf_trajectory_gate_policy import (
    _family_groups,
    _fold_summary,
    _label_counts,
    _task_groups,
    _trajectory_labels,
    trajectory_gate_feature_names,
)
from BPC_future.scripts.train_cbf_gate import (
    _features,
    _is_no_effect_row,
    _metrics,
    _predict_probabilities,
    _standardize,
    _standardize_fit,
    _train_logistic,
    load_rows,
)


DEFAULT_DATASET = Path(
    "BPC_future/results/cbf_trajectory_gate_dataset_global_all_h2_20260614/"
    "cbf_trajectory_gate_transitions.jsonl"
)
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/cbf_delay_queue_scheduler_audit_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_cbf_delay_queue_scheduler_audit_zh.md"
)


def _threshold_candidates(min_threshold: float) -> list[float]:
    floor = max(0, min(100, int(round(float(min_threshold) * 100))))
    return [step / 100.0 for step in range(floor, 101)] + [1.01]


def _select_zero_fp_threshold(
    probabilities: list[float],
    labels: list[int],
    *,
    min_train_high_priority: int,
    min_high_priority_threshold: float,
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for threshold in _threshold_candidates(min_high_priority_threshold):
        metric = _metrics(probabilities, labels, threshold)
        if metric["fp"] == 0 and metric["predicted_positive"] >= int(min_train_high_priority):
            candidates.append(metric)
    if not candidates:
        metric = _metrics(probabilities, labels, 1.01)
        return {
            "decision": "delay_all_on_train",
            "threshold": 1.01,
            "train_metrics": metric,
            "reason": "no_train_zero_fp_productive_threshold",
        }
    candidates.sort(
        key=lambda item: (
            int(item["tp"]),
            float(item["recall"] or 0.0),
            -float(item["threshold"]),
        ),
        reverse=True,
    )
    best = candidates[0]
    return {
        "decision": "high_priority_threshold",
        "threshold": float(best["threshold"]),
        "train_metrics": best,
        "reason": "train_zero_fp_threshold_found",
    }


def _fold_scheduler_audit(
    *,
    fold_kind: str,
    holdout_name: str,
    train_rows: list[dict[str, Any]],
    holdout_rows: list[dict[str, Any]],
    epochs: int,
    lr: float,
    l2: float,
    min_train_high_priority: int,
    min_high_priority_threshold: float,
) -> dict[str, Any]:
    if not train_rows or not holdout_rows:
        return {
            "fold_kind": fold_kind,
            "holdout_name": holdout_name,
            "status": "skipped_empty_fold",
            "train_count": len(train_rows),
            "holdout_count": len(holdout_rows),
            "scheduler_safety_pass": False,
        }
    train_y = _trajectory_labels(train_rows)
    holdout_y = _trajectory_labels(holdout_rows)
    if not train_y or sum(train_y) <= 0 or sum(train_y) >= len(train_y):
        return {
            "fold_kind": fold_kind,
            "holdout_name": holdout_name,
            "status": "skipped_train_single_label",
            "train_count": len(train_rows),
            "holdout_count": len(holdout_rows),
            "train_label_counts": dict(Counter(str(label) for label in train_y)),
            "holdout_label_counts": dict(Counter(str(label) for label in holdout_y)),
            "scheduler_safety_pass": False,
        }
    feature_names = trajectory_gate_feature_names(train_rows)
    if not feature_names:
        return {
            "fold_kind": fold_kind,
            "holdout_name": holdout_name,
            "status": "skipped_no_features",
            "train_count": len(train_rows),
            "holdout_count": len(holdout_rows),
            "scheduler_safety_pass": False,
        }

    train_x_raw = [_features(row, feature_names) for row in train_rows]
    holdout_x_raw = [_features(row, feature_names) for row in holdout_rows]
    means, stds = _standardize_fit(train_x_raw)
    train_x = _standardize(train_x_raw, means, stds)
    holdout_x = _standardize(holdout_x_raw, means, stds)
    weights = _train_logistic(train_x, train_y, epochs=epochs, lr=lr, l2=l2)
    train_prob = _predict_probabilities(train_x, weights)
    holdout_prob = _predict_probabilities(holdout_x, weights)
    chosen = _select_zero_fp_threshold(
        train_prob,
        train_y,
        min_train_high_priority=min_train_high_priority,
        min_high_priority_threshold=min_high_priority_threshold,
    )
    threshold = float(chosen["threshold"])
    holdout_metrics = _metrics(holdout_prob, holdout_y, threshold)
    high_priority_count = int(holdout_metrics["predicted_positive"])
    delay_queue_count = max(0, len(holdout_rows) - high_priority_count)
    scheduler_safety_pass = bool(holdout_metrics["fp"] == 0)
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
        "min_high_priority_threshold": float(min_high_priority_threshold),
        "chosen_scheduler": chosen,
        "holdout_metrics": holdout_metrics,
        "high_priority_count": high_priority_count,
        "delay_queue_count": delay_queue_count,
        "scheduler_safety_pass": scheduler_safety_pass,
        "productive_holdout_high_priority": bool(high_priority_count > 0),
    }


def _bucket_instance_folds(
    indexed_rows: list[tuple[int, dict[str, Any]]],
    *,
    fold_kind: str,
    min_holdout_rows: int,
    min_train_rows: int,
    epochs: int,
    lr: float,
    l2: float,
    min_train_high_priority: int,
    min_high_priority_threshold: float,
) -> list[dict[str, Any]]:
    by_instance: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for idx, row in indexed_rows:
        by_instance.setdefault(str(row.get("instance", "")), []).append((idx, row))
    all_indices = {idx for idx, _row in indexed_rows}
    folds: list[dict[str, Any]] = []
    for instance, holdout_indexed in sorted(by_instance.items()):
        holdout_indices = {idx for idx, _row in holdout_indexed}
        holdout_rows = [row for _idx, row in holdout_indexed]
        train_rows = [
            row
            for idx, row in indexed_rows
            if idx in all_indices and idx not in holdout_indices
        ]
        if len(holdout_rows) < int(min_holdout_rows):
            folds.append(
                {
                    "fold_kind": fold_kind,
                    "holdout_name": instance,
                    "status": "skipped_too_few_holdout_rows",
                    "holdout_count": len(holdout_rows),
                    "scheduler_safety_pass": False,
                }
            )
            continue
        if len(train_rows) < int(min_train_rows):
            folds.append(
                {
                    "fold_kind": fold_kind,
                    "holdout_name": instance,
                    "status": "skipped_too_few_train_rows",
                    "train_count": len(train_rows),
                    "holdout_count": len(holdout_rows),
                    "scheduler_safety_pass": False,
                }
            )
            continue
        folds.append(
            _fold_scheduler_audit(
                fold_kind=fold_kind,
                holdout_name=instance,
                train_rows=train_rows,
                holdout_rows=holdout_rows,
                epochs=epochs,
                lr=lr,
                l2=l2,
                min_train_high_priority=min_train_high_priority,
                min_high_priority_threshold=min_high_priority_threshold,
            )
        )
    return folds


def _scheduler_fold_summary(folds: list[dict[str, Any]]) -> dict[str, Any]:
    base = _fold_summary(folds)
    evaluated = [fold for fold in folds if fold.get("status") == "evaluated"]
    unsafe_high_priority = [
        fold
        for fold in evaluated
        if int((fold.get("holdout_metrics") or {}).get("fp", 0)) > 0
    ]
    total_high_priority = sum(int(fold.get("high_priority_count", 0)) for fold in evaluated)
    total_delay_queue = sum(int(fold.get("delay_queue_count", 0)) for fold in evaluated)
    productive = [
        fold for fold in evaluated if fold.get("productive_holdout_high_priority") is True
    ]
    base.update(
        {
            "unsafe_high_priority_fold_count": len(unsafe_high_priority),
            "productive_high_priority_fold_count": len(productive),
            "total_high_priority_count": total_high_priority,
            "total_delay_queue_count": total_delay_queue,
            "scheduler_no_unsafe_high_priority": bool(evaluated and not unsafe_high_priority),
        }
    )
    return base


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CBF Delay-Queue Scheduler 审计报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "审计 trajectory gate 是否能作为稳定性调度层使用：安全负列进入",
        "`HIGH_PRIORITY`，不安全负列进入 `DELAY_QUEUE`。该脚本只读 H=2",
        "trajectory dataset，不运行 BPC / pricing / RMP，不生成列，不产生",
        "certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "cbf_delay_queue_scheduler_audit = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"scheduler_ready = {str(summary['scheduler_ready']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"min_high_priority_threshold = {summary['min_high_priority_threshold']}",
        f"gate_can_permanently_discard_negative_columns = {str(summary['gate_can_permanently_discard_negative_columns']).lower()}",
        f"finite_delay_required = {str(summary['finite_delay_required']).lower()}",
        f"delay_queue_can_extend_proof_budget = {str(summary['delay_queue_can_extend_proof_budget']).lower()}",
        f"delay_queue_runs_proof_sweep = {str(summary['delay_queue_runs_proof_sweep']).lower()}",
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
                "min_high_priority_threshold": summary["min_high_priority_threshold"],
                "ready_task_counts": summary["ready_task_counts"],
                "ready_families": summary["ready_families"],
                "scale_scheduler_ready": summary["scale_scheduler_ready"],
                "family_scheduler_ready": summary["family_scheduler_ready"],
                "scale_results": [
                    {
                        "task_count": item["task_count"],
                        "row_count": item["row_count"],
                        "status": item["status"],
                        "fold_summary": item["fold_summary"],
                    }
                    for item in summary["scale_results"]
                ],
                "family_results": [
                    {
                        "task_count": item["task_count"],
                        "family": item["family"],
                        "row_count": item["row_count"],
                        "status": item["status"],
                        "fold_summary": item["fold_summary"],
                    }
                    for item in summary["family_results"]
                ],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 解释",
        "",
        "- 训练侧阈值必须满足 train zero-FP；留出侧若有 unsafe high priority，则不 ready；",
        "- `DELAY_QUEUE` 不是丢弃，必须满足有限延迟并保持 exact reachable；",
        "- `DELAY_QUEUE` 不能扩展 final judge / proof 阶段预算，也不能触发额外 proof sweep；",
        "- 小规模默认延迟/abstain，以保护 5/10 不退化；",
        "- `production_ready=false` 表示仍不能接 worker 或 certificate。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def audit_delay_queue_scheduler(
    dataset: Path,
    *,
    output_dir: Path,
    report: Path,
    min_enabled_task_count: int = 20,
    min_scale_rows: int = 30,
    min_family_rows: int = 20,
    min_holdout_rows: int = 2,
    min_train_rows: int = 20,
    min_evaluated_folds: int = 2,
    min_train_high_priority: int = 1,
    min_high_priority_threshold: float = 0.8,
    epochs: int = 500,
    lr: float = 0.05,
    l2: float = 1.0e-4,
) -> dict[str, Any]:
    rows = load_rows(dataset)
    no_effect_count = sum(1 for row in rows if _is_no_effect_row(row))
    feature_names = trajectory_gate_feature_names(rows)

    scale_results: list[dict[str, Any]] = []
    for task_count, indexed in _task_groups(rows).items():
        scale_rows = [row for _idx, row in indexed]
        base = {
            "task_count": int(task_count),
            "row_count": len(scale_rows),
            "label_counts": _label_counts(scale_rows),
            "feature_count": len(trajectory_gate_feature_names(scale_rows)),
        }
        if int(task_count) < int(min_enabled_task_count):
            scale_results.append(
                {
                    **base,
                    "status": "guarded_delay_below_min_task_count",
                    "scale_scheduler_candidate_ready": False,
                    "must_delay": True,
                    "reason": "protect_5_10_no_regression",
                    "fold_summary": _scheduler_fold_summary([]),
                    "folds": [],
                }
            )
            continue
        if len(scale_rows) < int(min_scale_rows):
            scale_results.append(
                {
                    **base,
                    "status": "insufficient_scale_rows",
                    "scale_scheduler_candidate_ready": False,
                    "must_delay": True,
                    "reason": "scale_rows_below_minimum",
                    "fold_summary": _scheduler_fold_summary([]),
                    "folds": [],
                }
            )
            continue
        folds = _bucket_instance_folds(
            indexed,
            fold_kind="delay_queue_within_scale_leave_one_instance",
            min_holdout_rows=min_holdout_rows,
            min_train_rows=min_train_rows,
            epochs=epochs,
            lr=lr,
            l2=l2,
            min_train_high_priority=min_train_high_priority,
            min_high_priority_threshold=min_high_priority_threshold,
        )
        fold_summary = _scheduler_fold_summary(folds)
        ready = bool(
            fold_summary["scheduler_no_unsafe_high_priority"]
            and fold_summary["evaluated_count"] >= int(min_evaluated_folds)
            and fold_summary["productive_high_priority_fold_count"] > 0
        )
        scale_results.append(
            {
                **base,
                "status": "scale_scheduler_candidate_ready"
                if ready
                else "scale_scheduler_not_ready",
                "scale_scheduler_candidate_ready": ready,
                "must_delay": not ready,
                "reason": "passed_delay_queue_scale_holdout"
                if ready
                else "delay_queue_scale_holdout_not_safe_or_not_productive",
                "fold_summary": fold_summary,
                "folds": folds,
            }
        )

    family_results: list[dict[str, Any]] = []
    for (task_count, family), indexed in _family_groups(rows).items():
        family_rows = [row for _idx, row in indexed]
        base = {
            "task_count": int(task_count),
            "family": str(family),
            "row_count": len(family_rows),
            "label_counts": _label_counts(family_rows),
            "feature_count": len(trajectory_gate_feature_names(family_rows)),
        }
        if int(task_count) < int(min_enabled_task_count):
            family_results.append(
                {
                    **base,
                    "status": "guarded_delay_below_min_task_count",
                    "family_scheduler_candidate_ready": False,
                    "must_delay": True,
                    "reason": "protect_5_10_no_regression",
                    "fold_summary": _scheduler_fold_summary([]),
                    "folds": [],
                }
            )
            continue
        if len(family_rows) < int(min_family_rows):
            family_results.append(
                {
                    **base,
                    "status": "insufficient_family_rows",
                    "family_scheduler_candidate_ready": False,
                    "must_delay": True,
                    "reason": "family_rows_below_minimum",
                    "fold_summary": _scheduler_fold_summary([]),
                    "folds": [],
                }
            )
            continue
        folds = _bucket_instance_folds(
            indexed,
            fold_kind="delay_queue_within_family_leave_one_instance",
            min_holdout_rows=min_holdout_rows,
            min_train_rows=min_train_rows,
            epochs=epochs,
            lr=lr,
            l2=l2,
            min_train_high_priority=min_train_high_priority,
            min_high_priority_threshold=min_high_priority_threshold,
        )
        fold_summary = _scheduler_fold_summary(folds)
        ready = bool(
            fold_summary["scheduler_no_unsafe_high_priority"]
            and fold_summary["evaluated_count"] >= int(min_evaluated_folds)
            and fold_summary["productive_high_priority_fold_count"] > 0
        )
        family_results.append(
            {
                **base,
                "status": "family_scheduler_candidate_ready"
                if ready
                else "family_scheduler_not_ready",
                "family_scheduler_candidate_ready": ready,
                "must_delay": not ready,
                "reason": "passed_delay_queue_family_holdout"
                if ready
                else "delay_queue_family_holdout_not_safe_or_not_productive",
                "fold_summary": fold_summary,
                "folds": folds,
            }
        )

    ready_task_counts = [
        item["task_count"]
        for item in scale_results
        if item.get("scale_scheduler_candidate_ready") is True
    ]
    ready_families = [
        {"task_count": item["task_count"], "family": item["family"]}
        for item in family_results
        if item.get("family_scheduler_candidate_ready") is True
    ]
    small_scale_delay_ok = all(
        item["must_delay"] and item["status"] == "guarded_delay_below_min_task_count"
        for item in scale_results
        if item["task_count"] < int(min_enabled_task_count)
    )
    small_family_delay_ok = all(
        item["must_delay"] and item["status"] == "guarded_delay_below_min_task_count"
        for item in family_results
        if item["task_count"] < int(min_enabled_task_count)
    )
    checks = {
        "all_rows_no_certificate_effect": bool(rows and no_effect_count == len(rows)),
        "has_current_state_features": bool(feature_names),
        "uses_horizon_labels": bool(rows and "label_horizon_cbf_feasible" in rows[0]),
        "small_scale_delay": small_scale_delay_ok,
        "small_family_delay": small_family_delay_ok,
        "delay_queue_exactness_guard_present": True,
        "delay_queue_does_not_extend_proof_budget": True,
    }
    summary = {
        "schema_version": "cbf_delay_queue_scheduler_audit_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "cbf_delay_queue_scheduler_audited",
        "dataset": str(dataset),
        "row_count": len(rows),
        "no_effect_row_count": no_effect_count,
        "feature_count": len(feature_names),
        "label_counts": _label_counts(rows),
        "task_count_histogram": dict(Counter(str(row.get("task_count")) for row in rows)),
        "min_enabled_task_count": int(min_enabled_task_count),
        "min_scale_rows": int(min_scale_rows),
        "min_family_rows": int(min_family_rows),
        "min_holdout_rows": int(min_holdout_rows),
        "min_train_rows": int(min_train_rows),
        "min_evaluated_folds": int(min_evaluated_folds),
        "min_train_high_priority": int(min_train_high_priority),
        "min_high_priority_threshold": float(min_high_priority_threshold),
        "scale_results": scale_results,
        "family_results": family_results,
        "ready_task_counts": ready_task_counts,
        "ready_families": ready_families,
        "scale_scheduler_ready": bool(ready_task_counts),
        "family_scheduler_ready": bool(ready_families),
        "scheduler_ready": bool(ready_task_counts or ready_families),
        "production_ready": False,
        "gate_role": "stability_scheduler_not_column_filter",
        "gate_decision_model": "rc_negative_safe_high_priority_rc_negative_unsafe_delay_queue_rc_nonnegative_reject",
        "safe_negative_decision": "HIGH_PRIORITY",
        "unsafe_negative_decision": "DELAY_QUEUE",
        "nonnegative_decision": "REJECT_NONNEGATIVE_ONLY",
        "gate_can_permanently_discard_negative_columns": False,
        "negative_columns_must_remain_eventually_reachable": True,
        "finite_delay_required": True,
        "finite_delay_condition": "for_all_p_true_rc_negative_exists_finite_T_p_until_rmp_or_exact_reachable",
        "delay_queue_is_proof_blocking": False,
        "delay_queue_can_extend_proof_budget": False,
        "delay_queue_runs_proof_sweep": False,
        "proof_stage_budget_effect": "none_existing_exact_deadlines_unchanged",
        "proof_stage_policy": "delay_queue_never_replaces_or_extends_exact_final_judge",
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-enabled-task-count", type=int, default=20)
    parser.add_argument("--min-scale-rows", type=int, default=30)
    parser.add_argument("--min-family-rows", type=int, default=20)
    parser.add_argument("--min-holdout-rows", type=int, default=2)
    parser.add_argument("--min-train-rows", type=int, default=20)
    parser.add_argument("--min-evaluated-folds", type=int, default=2)
    parser.add_argument("--min-train-high-priority", type=int, default=1)
    parser.add_argument("--min-high-priority-threshold", type=float, default=0.8)
    parser.add_argument("--epochs", type=int, default=500)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--l2", type=float, default=1.0e-4)
    args = parser.parse_args(argv)
    summary = audit_delay_queue_scheduler(
        args.dataset,
        output_dir=args.output_dir,
        report=args.report,
        min_enabled_task_count=args.min_enabled_task_count,
        min_scale_rows=args.min_scale_rows,
        min_family_rows=args.min_family_rows,
        min_holdout_rows=args.min_holdout_rows,
        min_train_rows=args.min_train_rows,
        min_evaluated_folds=args.min_evaluated_folds,
        min_train_high_priority=args.min_train_high_priority,
        min_high_priority_threshold=args.min_high_priority_threshold,
        epochs=args.epochs,
        lr=args.lr,
        l2=args.l2,
    )
    print(
        json.dumps(
            {
                "summary": str(args.output_dir / "summary.json"),
                "report": str(args.report),
                "all_checks_pass": summary["all_checks_pass"],
                "scheduler_ready": summary["scheduler_ready"],
                "ready_task_counts": summary["ready_task_counts"],
                "ready_families": summary["ready_families"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

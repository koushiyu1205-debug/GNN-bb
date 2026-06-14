#!/usr/bin/env python3
"""Audit a kNN-risk plus safe-radius OOD CBF delay-queue scheduler.

This extends the offline kNN-risk scheduler with an OOD guard: a row can enter
``HIGH_PRIORITY`` only if it is close enough to the training safe manifold.
The safe radius is estimated inside each training fold from nearest-safe
distances among training positives.  True-RC negative rows that fail the guard
remain in ``DELAY_QUEUE``.

The script is diagnostic-only.  It never runs BPC/pricing/RMP, never generates
columns, and never creates certificates or official lower bounds.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
from typing import Any

from BPC_future.scripts.audit_cbf_delay_queue_scheduler import (
    DEFAULT_DATASET,
    _scheduler_fold_summary,
    _select_zero_fp_threshold,
)
from BPC_future.scripts.audit_cbf_trajectory_gate_policy import (
    _family_groups,
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


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/cbf_delay_queue_knn_ood_scheduler_audit_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_cbf_delay_queue_knn_ood_scheduler_audit_zh.md"
)


def _distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = max(0.0, min(1.0, float(q))) * (len(ordered) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return ordered[lo]
    frac = pos - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def _neighbor_unsafe_fraction(
    train_x: list[list[float]],
    train_y: list[int],
    row_x: list[float],
    *,
    k: int,
) -> float:
    if not train_x:
        return 1.0
    neighbors = sorted(
        ((_distance(row_x, x), label) for x, label in zip(train_x, train_y)),
        key=lambda item: item[0],
    )[: max(1, int(k))]
    if not neighbors:
        return 1.0
    unsafe_count = sum(1 for _dist, label in neighbors if int(label) == 0)
    return unsafe_count / float(len(neighbors))


def _nearest_safe_distance(
    train_x: list[list[float]],
    train_y: list[int],
    row_x: list[float],
) -> float | None:
    safe = [x for x, y in zip(train_x, train_y) if int(y) == 1]
    if not safe:
        return None
    return min(_distance(row_x, safe_x) for safe_x in safe)


def _safe_radius_threshold(
    train_x: list[list[float]],
    train_y: list[int],
    *,
    quantile: float,
    multiplier: float,
) -> float | None:
    safe = [x for x, y in zip(train_x, train_y) if int(y) == 1]
    if len(safe) < 2:
        return None
    nearest_distances: list[float] = []
    for idx, x in enumerate(safe):
        others = [candidate for other_idx, candidate in enumerate(safe) if other_idx != idx]
        nearest_distances.append(min(_distance(x, other) for other in others))
    q = _quantile(nearest_distances, quantile)
    if q is None:
        return None
    return float(q) * float(multiplier)


def _fold_ood_audit(
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
    knn_k: int,
    max_neighbor_unsafe_fraction: float,
    safe_radius_quantile: float,
    safe_radius_multiplier: float,
) -> dict[str, Any]:
    train_y = _trajectory_labels(train_rows)
    holdout_y = _trajectory_labels(holdout_rows)
    if not train_rows or not holdout_rows:
        return {
            "fold_kind": fold_kind,
            "holdout_name": holdout_name,
            "status": "skipped_empty_fold",
            "train_count": len(train_rows),
            "holdout_count": len(holdout_rows),
            "scheduler_safety_pass": False,
        }
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
    radius = _safe_radius_threshold(
        train_x,
        train_y,
        quantile=safe_radius_quantile,
        multiplier=safe_radius_multiplier,
    )
    raw_holdout_metrics = _metrics(holdout_prob, holdout_y, threshold)
    decisions: list[int] = []
    neighbor_risks: list[float] = []
    nearest_safe_distances: list[float] = []
    for row_x, prob in zip(holdout_x, holdout_prob):
        risk = _neighbor_unsafe_fraction(train_x, train_y, row_x, k=knn_k)
        nearest_safe = _nearest_safe_distance(train_x, train_y, row_x)
        neighbor_risks.append(risk)
        if nearest_safe is not None:
            nearest_safe_distances.append(nearest_safe)
        in_safe_radius = bool(radius is not None and nearest_safe is not None and nearest_safe <= radius)
        decisions.append(
            1
            if float(prob) >= threshold
            and risk <= float(max_neighbor_unsafe_fraction)
            and in_safe_radius
            else 0
        )
    tp = sum(1 for pred, label in zip(decisions, holdout_y) if pred == 1 and label == 1)
    fp = sum(1 for pred, label in zip(decisions, holdout_y) if pred == 1 and label == 0)
    tn = sum(1 for pred, label in zip(decisions, holdout_y) if pred == 0 and label == 0)
    fn = sum(1 for pred, label in zip(decisions, holdout_y) if pred == 0 and label == 1)
    predicted_positive = tp + fp
    positives = tp + fn
    negatives = tn + fp
    holdout_metrics = {
        "threshold": threshold,
        "total": len(holdout_y),
        "positive_count": positives,
        "negative_count": negatives,
        "predicted_positive": predicted_positive,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": None if predicted_positive == 0 else tp / float(predicted_positive),
        "recall": None if positives == 0 else tp / float(positives),
        "false_positive_rate": None if negatives == 0 else fp / float(negatives),
    }
    high_priority_count = int(predicted_positive)
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
        "chosen_scheduler": chosen,
        "raw_holdout_metrics_before_ood": raw_holdout_metrics,
        "holdout_metrics": holdout_metrics,
        "knn_k": int(knn_k),
        "max_neighbor_unsafe_fraction": float(max_neighbor_unsafe_fraction),
        "safe_radius_quantile": float(safe_radius_quantile),
        "safe_radius_multiplier": float(safe_radius_multiplier),
        "safe_radius": radius,
        "nearest_safe_distance_min": min(nearest_safe_distances) if nearest_safe_distances else None,
        "nearest_safe_distance_max": max(nearest_safe_distances) if nearest_safe_distances else None,
        "neighbor_unsafe_fraction_min": min(neighbor_risks) if neighbor_risks else None,
        "neighbor_unsafe_fraction_max": max(neighbor_risks) if neighbor_risks else None,
        "high_priority_count": high_priority_count,
        "delay_queue_count": max(0, len(holdout_rows) - high_priority_count),
        "scheduler_safety_pass": bool(fp == 0),
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
    knn_k: int,
    max_neighbor_unsafe_fraction: float,
    safe_radius_quantile: float,
    safe_radius_multiplier: float,
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
            _fold_ood_audit(
                fold_kind=fold_kind,
                holdout_name=instance,
                train_rows=train_rows,
                holdout_rows=holdout_rows,
                epochs=epochs,
                lr=lr,
                l2=l2,
                min_train_high_priority=min_train_high_priority,
                min_high_priority_threshold=min_high_priority_threshold,
                knn_k=knn_k,
                max_neighbor_unsafe_fraction=max_neighbor_unsafe_fraction,
                safe_radius_quantile=safe_radius_quantile,
                safe_radius_multiplier=safe_radius_multiplier,
            )
        )
    return folds


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CBF Delay-Queue kNN+OOD Scheduler 审计报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "在 kNN unsafe density 外叠加 safe-manifold radius guard，检查是否能",
        "挡住 family-level residual false-positive。该脚本只读 H=2 dataset，不运行",
        "BPC / pricing / RMP，不生成列，不产生 certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "cbf_delay_queue_knn_ood_scheduler_audit = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"scheduler_ready = {str(summary['scheduler_ready']).lower()}",
        f"production_candidate_ready = {str(summary['production_candidate_ready']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"knn_k = {summary['knn_k']}",
        f"max_neighbor_unsafe_fraction = {summary['max_neighbor_unsafe_fraction']}",
        f"safe_radius_quantile = {summary['safe_radius_quantile']}",
        f"safe_radius_multiplier = {summary['safe_radius_multiplier']}",
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
                "ready_task_counts": summary["ready_task_counts"],
                "ready_families": summary["ready_families"],
                "scale_scheduler_ready": summary["scale_scheduler_ready"],
                "family_scheduler_ready": summary["family_scheduler_ready"],
                "production_candidate_ready": summary["production_candidate_ready"],
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
        "- OOD radius 只能把 true-RC negative 退回 delay queue，不能 discard；",
        "- delay queue 不能扩展 final judge / proof 阶段预算，也不能触发额外 proof sweep；",
        "- family-ready 之前不能接 production；",
        "- 若 OOD guard 压没所有 high-priority，说明当前特征空间仍无 ROI。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def audit_knn_ood_scheduler(
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
    knn_k: int = 5,
    max_neighbor_unsafe_fraction: float = 0.0,
    safe_radius_quantile: float = 0.9,
    safe_radius_multiplier: float = 1.0,
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
            fold_kind="knn_ood_delay_queue_within_scale_leave_one_instance",
            min_holdout_rows=min_holdout_rows,
            min_train_rows=min_train_rows,
            epochs=epochs,
            lr=lr,
            l2=l2,
            min_train_high_priority=min_train_high_priority,
            min_high_priority_threshold=min_high_priority_threshold,
            knn_k=knn_k,
            max_neighbor_unsafe_fraction=max_neighbor_unsafe_fraction,
            safe_radius_quantile=safe_radius_quantile,
            safe_radius_multiplier=safe_radius_multiplier,
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
                "reason": "passed_knn_ood_delay_queue_scale_holdout"
                if ready
                else "knn_ood_delay_queue_scale_holdout_not_safe_or_not_productive",
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
            fold_kind="knn_ood_delay_queue_within_family_leave_one_instance",
            min_holdout_rows=min_holdout_rows,
            min_train_rows=min_train_rows,
            epochs=epochs,
            lr=lr,
            l2=l2,
            min_train_high_priority=min_train_high_priority,
            min_high_priority_threshold=min_high_priority_threshold,
            knn_k=knn_k,
            max_neighbor_unsafe_fraction=max_neighbor_unsafe_fraction,
            safe_radius_quantile=safe_radius_quantile,
            safe_radius_multiplier=safe_radius_multiplier,
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
                "reason": "passed_knn_ood_delay_queue_family_holdout"
                if ready
                else "knn_ood_delay_queue_family_holdout_not_safe_or_not_productive",
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
    checks = {
        "all_rows_no_certificate_effect": bool(rows and no_effect_count == len(rows)),
        "has_current_state_features": bool(feature_names),
        "uses_horizon_labels": bool(rows and "label_horizon_cbf_feasible" in rows[0]),
        "delay_queue_exactness_guard_present": True,
        "delay_queue_does_not_extend_proof_budget": True,
    }
    summary = {
        "schema_version": "cbf_delay_queue_knn_ood_scheduler_audit_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "cbf_delay_queue_knn_ood_scheduler_audited",
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
        "knn_k": int(knn_k),
        "max_neighbor_unsafe_fraction": float(max_neighbor_unsafe_fraction),
        "safe_radius_quantile": float(safe_radius_quantile),
        "safe_radius_multiplier": float(safe_radius_multiplier),
        "scale_results": scale_results,
        "family_results": family_results,
        "ready_task_counts": ready_task_counts,
        "ready_families": ready_families,
        "scale_scheduler_ready": bool(ready_task_counts),
        "family_scheduler_ready": bool(ready_families),
        "scheduler_ready": bool(ready_task_counts or ready_families),
        "family_holdout_required_for_production": True,
        "production_candidate_ready": bool(ready_task_counts and ready_families),
        "production_ready": False,
        "gate_role": "stability_scheduler_not_column_filter",
        "safe_negative_decision": "HIGH_PRIORITY",
        "unsafe_negative_decision": "DELAY_QUEUE",
        "nonnegative_decision": "REJECT_NONNEGATIVE_ONLY",
        "gate_can_permanently_discard_negative_columns": False,
        "negative_columns_must_remain_eventually_reachable": True,
        "finite_delay_required": True,
        "delay_queue_is_proof_blocking": False,
        "delay_queue_can_extend_proof_budget": False,
        "delay_queue_runs_proof_sweep": False,
        "proof_stage_budget_effect": "none_existing_exact_deadlines_unchanged",
        "proof_stage_policy": "delay_queue_never_replaces_or_extends_exact_final_judge",
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
    parser.add_argument("--knn-k", type=int, default=5)
    parser.add_argument("--max-neighbor-unsafe-fraction", type=float, default=0.0)
    parser.add_argument("--safe-radius-quantile", type=float, default=0.9)
    parser.add_argument("--safe-radius-multiplier", type=float, default=1.0)
    parser.add_argument("--epochs", type=int, default=500)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--l2", type=float, default=1.0e-4)
    args = parser.parse_args(argv)
    summary = audit_knn_ood_scheduler(
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
        knn_k=args.knn_k,
        max_neighbor_unsafe_fraction=args.max_neighbor_unsafe_fraction,
        safe_radius_quantile=args.safe_radius_quantile,
        safe_radius_multiplier=args.safe_radius_multiplier,
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
                "production_candidate_ready": summary["production_candidate_ready"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

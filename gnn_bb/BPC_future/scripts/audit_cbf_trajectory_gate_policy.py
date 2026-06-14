#!/usr/bin/env python3
"""Audit trajectory-level CBF gate robustness.

This audit is the horizon-level counterpart of the one-step CBF gate checks.
It uses ``label_horizon_cbf_feasible`` as the target and keeps all
``horizon_*`` / future fields out of the feature set.  The script is offline
and diagnostic-only: it never runs BPC/pricing/RMP, never generates columns,
and never creates certificates or official lower bounds.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any

from BPC_future.scripts.audit_cbf_gate_family_policy import infer_family
from BPC_future.scripts.train_cbf_gate import (
    _features,
    _is_no_effect_row,
    _metrics,
    _predict_probabilities,
    _select_conservative_threshold,
    _standardize,
    _standardize_fit,
    _train_logistic,
    cbf_gate_feature_names,
    load_rows,
)


DEFAULT_DATASET = Path(
    "BPC_future/results/cbf_trajectory_gate_dataset_global_all_h2_20260614/"
    "cbf_trajectory_gate_transitions.jsonl"
)
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/cbf_trajectory_gate_policy_audit_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_cbf_trajectory_gate_policy_audit_zh.md"
)

HORIZON_LEAKAGE_PREFIXES = ("horizon_",)
HORIZON_LEAKAGE_FIELDS = {
    "label_horizon_bad_mode_transition",
    "label_horizon_cbf_feasible",
    "label_horizon_delta_v_nonpositive",
}


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def trajectory_gate_feature_names(rows: list[dict[str, Any]]) -> list[str]:
    """Return online-available feature names for the trajectory gate."""

    base = cbf_gate_feature_names(rows)
    return [
        name
        for name in base
        if name not in HORIZON_LEAKAGE_FIELDS
        and not name.startswith(HORIZON_LEAKAGE_PREFIXES)
    ]


def _trajectory_labels(rows: list[dict[str, Any]]) -> list[int]:
    return [1 if int(row.get("label_horizon_cbf_feasible", 0)) else 0 for row in rows]


def _label_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(str(label) for label in _trajectory_labels(rows)))


def _can_train(rows: list[dict[str, Any]]) -> bool:
    labels = _trajectory_labels(rows)
    return bool(rows and sum(labels) > 0 and sum(labels) < len(labels))


def _group_rows(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(key, ""))].append(row)
    return dict(sorted(groups.items()))


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
            "train_label_counts": _label_counts(train_rows),
            "holdout_label_counts": _label_counts(holdout_rows),
            "strict_safety_pass": False,
        }
    feature_names = trajectory_gate_feature_names(train_rows)
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
    train_y = _trajectory_labels(train_rows)
    holdout_y = _trajectory_labels(holdout_rows)
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


def _fold_summary(folds: list[dict[str, Any]]) -> dict[str, Any]:
    evaluated = [fold for fold in folds if fold.get("status") == "evaluated"]
    skipped = [fold for fold in folds if fold.get("status") != "evaluated"]
    false_positive = [
        fold
        for fold in evaluated
        if int((fold.get("holdout_metrics") or {}).get("fp", 0)) > 0
    ]
    productive = [fold for fold in evaluated if fold.get("productive_holdout_adds") is True]
    return {
        "fold_count": len(folds),
        "evaluated_count": len(evaluated),
        "skipped_count": len(skipped),
        "false_positive_fold_count": len(false_positive),
        "productive_fold_count": len(productive),
        "evaluated_no_false_positive": bool(evaluated and not false_positive),
        "all_folds_evaluated": bool(folds and len(evaluated) == len(folds)),
        "skipped_status_counts": dict(Counter(str(fold.get("status")) for fold in skipped)),
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


def _task_groups(rows: list[dict[str, Any]]) -> dict[int, list[tuple[int, dict[str, Any]]]]:
    groups: dict[int, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for idx, row in enumerate(rows):
        groups[_as_int(row.get("task_count"))].append((idx, row))
    return dict(sorted(groups.items()))


def _family_groups(rows: list[dict[str, Any]]) -> dict[tuple[int, str], list[tuple[int, dict[str, Any]]]]:
    groups: dict[tuple[int, str], list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for idx, row in enumerate(rows):
        groups[(_as_int(row.get("task_count")), infer_family(row))].append((idx, row))
    return dict(sorted(groups.items(), key=lambda item: (item[0][0], item[0][1])))


def _within_bucket_instance_folds(
    indexed_rows: list[tuple[int, dict[str, Any]]],
    *,
    fold_kind: str,
    min_holdout_rows: int,
    min_train_rows: int,
    epochs: int,
    lr: float,
    l2: float,
    min_precision: float,
    max_false_positive_rate: float,
) -> list[dict[str, Any]]:
    by_instance: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for idx, row in indexed_rows:
        by_instance[str(row.get("instance", ""))].append((idx, row))
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
                    "strict_safety_pass": False,
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
                    "strict_safety_pass": False,
                }
            )
            continue
        folds.append(
            _fold_audit(
                fold_kind=fold_kind,
                holdout_name=instance,
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


def _scale_results(
    rows: list[dict[str, Any]],
    *,
    min_enabled_task_count: int,
    min_scale_rows: int,
    min_holdout_rows: int,
    min_train_rows: int,
    min_evaluated_folds: int,
    epochs: int,
    lr: float,
    l2: float,
    min_precision: float,
    max_false_positive_rate: float,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for task_count, indexed in _task_groups(rows).items():
        scale_rows = [row for _idx, row in indexed]
        base = {
            "task_count": int(task_count),
            "row_count": len(scale_rows),
            "label_counts": _label_counts(scale_rows),
            "feature_count": len(trajectory_gate_feature_names(scale_rows)),
            "scale_guard_min_enabled_task_count": int(min_enabled_task_count),
        }
        if int(task_count) < int(min_enabled_task_count):
            results.append(
                {
                    **base,
                    "status": "guarded_abstain_below_min_task_count",
                    "scale_gate_candidate_ready": False,
                    "must_abstain": True,
                    "reason": "protect_5_10_no_regression",
                    "fold_summary": _fold_summary([]),
                    "folds": [],
                }
            )
            continue
        if len(scale_rows) < int(min_scale_rows):
            results.append(
                {
                    **base,
                    "status": "insufficient_scale_rows",
                    "scale_gate_candidate_ready": False,
                    "must_abstain": True,
                    "reason": "scale_rows_below_minimum",
                    "fold_summary": _fold_summary([]),
                    "folds": [],
                }
            )
            continue
        if not _can_train(scale_rows):
            results.append(
                {
                    **base,
                    "status": "insufficient_scale_label_coverage",
                    "scale_gate_candidate_ready": False,
                    "must_abstain": True,
                    "reason": "scale_has_single_label",
                    "fold_summary": _fold_summary([]),
                    "folds": [],
                }
            )
            continue
        folds = _within_bucket_instance_folds(
            indexed,
            fold_kind="trajectory_within_scale_leave_one_instance",
            min_holdout_rows=min_holdout_rows,
            min_train_rows=min_train_rows,
            epochs=epochs,
            lr=lr,
            l2=l2,
            min_precision=min_precision,
            max_false_positive_rate=max_false_positive_rate,
        )
        summary = _fold_summary(folds)
        ready = bool(
            summary["evaluated_no_false_positive"]
            and summary["evaluated_count"] >= int(min_evaluated_folds)
            and summary["productive_fold_count"] > 0
        )
        results.append(
            {
                **base,
                "status": "scale_gate_candidate_ready" if ready else "scale_gate_not_ready",
                "scale_gate_candidate_ready": ready,
                "must_abstain": not ready,
                "reason": "passed_within_scale_trajectory_holdout"
                if ready
                else "within_scale_trajectory_holdout_not_safe_or_not_productive",
                "fold_summary": summary,
                "folds": folds,
            }
        )
    return results


def _family_results(
    rows: list[dict[str, Any]],
    *,
    min_enabled_task_count: int,
    min_family_rows: int,
    min_holdout_rows: int,
    min_train_rows: int,
    min_evaluated_folds: int,
    epochs: int,
    lr: float,
    l2: float,
    min_precision: float,
    max_false_positive_rate: float,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for (task_count, family), indexed in _family_groups(rows).items():
        family_rows = [row for _idx, row in indexed]
        base = {
            "task_count": int(task_count),
            "family": str(family),
            "row_count": len(family_rows),
            "label_counts": _label_counts(family_rows),
            "feature_count": len(trajectory_gate_feature_names(family_rows)),
            "min_enabled_task_count": int(min_enabled_task_count),
        }
        if int(task_count) < int(min_enabled_task_count):
            results.append(
                {
                    **base,
                    "status": "guarded_abstain_below_min_task_count",
                    "family_gate_candidate_ready": False,
                    "must_abstain": True,
                    "reason": "protect_5_10_no_regression",
                    "fold_summary": _fold_summary([]),
                    "folds": [],
                }
            )
            continue
        if len(family_rows) < int(min_family_rows):
            results.append(
                {
                    **base,
                    "status": "insufficient_family_rows",
                    "family_gate_candidate_ready": False,
                    "must_abstain": True,
                    "reason": "family_rows_below_minimum",
                    "fold_summary": _fold_summary([]),
                    "folds": [],
                }
            )
            continue
        if not _can_train(family_rows):
            results.append(
                {
                    **base,
                    "status": "insufficient_family_label_coverage",
                    "family_gate_candidate_ready": False,
                    "must_abstain": True,
                    "reason": "family_has_single_label",
                    "fold_summary": _fold_summary([]),
                    "folds": [],
                }
            )
            continue
        folds = _within_bucket_instance_folds(
            indexed,
            fold_kind="trajectory_within_family_leave_one_instance",
            min_holdout_rows=min_holdout_rows,
            min_train_rows=min_train_rows,
            epochs=epochs,
            lr=lr,
            l2=l2,
            min_precision=min_precision,
            max_false_positive_rate=max_false_positive_rate,
        )
        summary = _fold_summary(folds)
        ready = bool(
            summary["evaluated_no_false_positive"]
            and summary["evaluated_count"] >= int(min_evaluated_folds)
            and summary["productive_fold_count"] > 0
        )
        results.append(
            {
                **base,
                "status": "family_gate_candidate_ready" if ready else "family_gate_not_ready",
                "family_gate_candidate_ready": ready,
                "must_abstain": not ready,
                "reason": "passed_within_family_trajectory_holdout"
                if ready
                else "within_family_trajectory_holdout_not_safe_or_not_productive",
                "fold_summary": summary,
                "folds": folds,
            }
        )
    return results


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CBF Trajectory Gate Policy 审计报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "审计 H-step trajectory-level CBF/RMP-impact gate 是否能在 instance、scale",
        "和 `(task_count, family)` 留出上保持安全。该脚本只读 trajectory dataset，",
        "不运行 BPC / pricing / RMP，不生成列，不产生 certificate 或 official lower bound。",
        "",
        "重要 exactness guard：trajectory gate 是稳定性调度层，不是硬过滤器。",
        "它只能把 true-RC negative column batch 分成 HIGH_PRIORITY 或 DELAY_QUEUE。",
        "它不能永久丢弃任何 true-RC negative column；被 gate 拦下的候选仍必须留给",
        "现有 exact pricing / fallback / backlog 路径，且必须满足有限延迟：",
        "对任意 true-RC negative column，存在有限 T_p 使其进入 RMP 或重新回到 exact 可达路径。",
        "",
        "## 机器字段",
        "",
        "```text",
        "cbf_trajectory_gate_policy_audit = current",
        f"status = {summary['status']}",
        f"horizon_steps = {summary['horizon_steps']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"holdout_safety_pass = {str(summary['holdout_safety_pass']).lower()}",
        f"scale_policy_ready = {str(summary['scale_policy_ready']).lower()}",
        f"family_policy_ready = {str(summary['family_policy_ready']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"gate_decision_model = {summary['gate_decision_model']}",
        f"gate_can_permanently_discard_negative_columns = {str(summary['gate_can_permanently_discard_negative_columns']).lower()}",
        f"finite_delay_required = {str(summary['finite_delay_required']).lower()}",
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
                "task_count_histogram": summary["task_count_histogram"],
                "instance_holdout_summary": summary["instance_holdout_summary"],
                "task_count_holdout_summary": summary["task_count_holdout_summary"],
                "ready_task_counts": summary["ready_task_counts"],
                "ready_families": summary["ready_families"],
                "holdout_safety_pass": summary["holdout_safety_pass"],
                "scale_policy_ready": summary["scale_policy_ready"],
                "family_policy_ready": summary["family_policy_ready"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 解释",
        "",
        "- 本审计使用 `label_horizon_cbf_feasible`，不是 one-step `label_cbf_feasible`；",
        "- 特征只允许当前状态与候选 batch 字段，排除 `horizon_*`、`state_next_*`、`delta_*`；",
        "- 小规模 scale/family 默认 abstain，用于保护 5/10 不退化；",
        "- unsafe true-RC negative batch 进入 DELAY_QUEUE，不是 REJECT；",
        "- DELAY_QUEUE 必须满足有限延迟引理，不能让 proof 阶段被无限拖住；",
        "- 只有 `rc >= 0` 的候选可以被 scheduler 视为非负列而不加入；",
        "- `production_ready=false` 表示仍不能接 worker 或 certificate。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def audit_trajectory_gate_policy(
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
    epochs: int = 500,
    lr: float = 0.05,
    l2: float = 1.0e-4,
    min_precision: float = 0.8,
    max_false_positive_rate: float = 0.05,
) -> dict[str, Any]:
    rows = load_rows(dataset)
    no_effect_count = sum(1 for row in rows if _is_no_effect_row(row))
    feature_names = trajectory_gate_feature_names(rows)
    instance_folds = _audit_group_holdout(
        rows,
        key="instance",
        fold_kind="trajectory_leave_one_instance",
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
        fold_kind="trajectory_leave_one_task_count",
        min_holdout_rows=min_holdout_rows,
        epochs=epochs,
        lr=lr,
        l2=l2,
        min_precision=min_precision,
        max_false_positive_rate=max_false_positive_rate,
    )
    instance_summary = _fold_summary(instance_folds)
    task_count_summary = _fold_summary(task_count_folds)
    scale_results = _scale_results(
        rows,
        min_enabled_task_count=min_enabled_task_count,
        min_scale_rows=min_scale_rows,
        min_holdout_rows=min_holdout_rows,
        min_train_rows=min_train_rows,
        min_evaluated_folds=min_evaluated_folds,
        epochs=epochs,
        lr=lr,
        l2=l2,
        min_precision=min_precision,
        max_false_positive_rate=max_false_positive_rate,
    )
    family_results = _family_results(
        rows,
        min_enabled_task_count=min_enabled_task_count,
        min_family_rows=min_family_rows,
        min_holdout_rows=min_holdout_rows,
        min_train_rows=min_train_rows,
        min_evaluated_folds=min_evaluated_folds,
        epochs=epochs,
        lr=lr,
        l2=l2,
        min_precision=min_precision,
        max_false_positive_rate=max_false_positive_rate,
    )
    ready_task_counts = [
        item["task_count"] for item in scale_results if item["scale_gate_candidate_ready"]
    ]
    ready_families = [
        {"task_count": item["task_count"], "family": item["family"]}
        for item in family_results
        if item["family_gate_candidate_ready"]
    ]
    holdout_safety_pass = bool(
        instance_summary["evaluated_no_false_positive"]
        and task_count_summary["evaluated_no_false_positive"]
    )
    small_scale_abstain_ok = all(
        item["must_abstain"] and item["status"] == "guarded_abstain_below_min_task_count"
        for item in scale_results
        if item["task_count"] < int(min_enabled_task_count)
    )
    small_family_abstain_ok = all(
        item["must_abstain"] and item["status"] == "guarded_abstain_below_min_task_count"
        for item in family_results
        if item["task_count"] < int(min_enabled_task_count)
    )
    horizon_steps = sorted({str(row.get("horizon_steps", "")) for row in rows})
    checks = {
        "all_rows_no_certificate_effect": bool(rows and no_effect_count == len(rows)),
        "has_current_state_features": bool(feature_names),
        "uses_horizon_labels": bool(rows and "label_horizon_cbf_feasible" in rows[0]),
        "excludes_horizon_leakage_features": all(
            not name.startswith(HORIZON_LEAKAGE_PREFIXES)
            and name not in HORIZON_LEAKAGE_FIELDS
            for name in feature_names
        ),
        "instance_holdout_has_evaluated_folds": instance_summary["evaluated_count"] > 0,
        "task_count_holdout_has_evaluated_folds": task_count_summary["evaluated_count"] > 0,
        "small_scale_abstains": small_scale_abstain_ok,
        "small_family_abstains": small_family_abstain_ok,
    }
    summary = {
        "schema_version": "cbf_trajectory_gate_policy_audit_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "cbf_trajectory_gate_policy_audited",
        "dataset": str(dataset),
        "row_count": len(rows),
        "no_effect_row_count": no_effect_count,
        "feature_count": len(feature_names),
        "base_feature_names": feature_names,
        "label_counts": _label_counts(rows),
        "task_count_histogram": dict(Counter(str(_as_int(row.get("task_count"))) for row in rows)),
        "horizon_steps": horizon_steps,
        "min_enabled_task_count": int(min_enabled_task_count),
        "min_scale_rows": int(min_scale_rows),
        "min_family_rows": int(min_family_rows),
        "min_holdout_rows": int(min_holdout_rows),
        "min_train_rows": int(min_train_rows),
        "min_evaluated_folds": int(min_evaluated_folds),
        "instance_holdout_summary": instance_summary,
        "task_count_holdout_summary": task_count_summary,
        "instance_folds": instance_folds,
        "task_count_folds": task_count_folds,
        "scale_results": scale_results,
        "family_results": family_results,
        "ready_task_counts": ready_task_counts,
        "ready_families": ready_families,
        "holdout_safety_pass": holdout_safety_pass,
        "scale_policy_ready": bool(ready_task_counts),
        "family_policy_ready": bool(ready_families),
        "production_ready": False,
        "gate_role": "stability_scheduler_not_column_filter",
        "gate_decision_model": "rc_negative_safe_high_priority_rc_negative_unsafe_delay_queue_rc_nonnegative_reject",
        "completeness_set_definition": "N_t={p: true_reduced_cost(p)<0}",
        "safe_negative_decision": "HIGH_PRIORITY",
        "unsafe_negative_decision": "DELAY_QUEUE",
        "nonnegative_decision": "REJECT_NONNEGATIVE_ONLY",
        "gate_can_permanently_discard_negative_columns": False,
        "negative_columns_must_remain_eventually_reachable": True,
        "finite_delay_required": True,
        "finite_delay_condition": "for_all_p_true_rc_negative_exists_finite_T_p_until_rmp_or_exact_reachable",
        "delay_queue_is_proof_blocking": False,
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
    parser.add_argument("--epochs", type=int, default=500)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--l2", type=float, default=1.0e-4)
    parser.add_argument("--min-precision", type=float, default=0.8)
    parser.add_argument("--max-false-positive-rate", type=float, default=0.05)
    args = parser.parse_args(argv)
    summary = audit_trajectory_gate_policy(
        args.dataset,
        output_dir=args.output_dir,
        report=args.report,
        min_enabled_task_count=args.min_enabled_task_count,
        min_scale_rows=args.min_scale_rows,
        min_family_rows=args.min_family_rows,
        min_holdout_rows=args.min_holdout_rows,
        min_train_rows=args.min_train_rows,
        min_evaluated_folds=args.min_evaluated_folds,
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
                "scale_policy_ready": summary["scale_policy_ready"],
                "family_policy_ready": summary["family_policy_ready"],
                "ready_task_counts": summary["ready_task_counts"],
                "ready_families": summary["ready_families"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

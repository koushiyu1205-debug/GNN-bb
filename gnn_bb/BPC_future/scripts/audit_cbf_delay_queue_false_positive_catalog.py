#!/usr/bin/env python3
"""Catalog unsafe high-priority errors from the CBF delay-queue scheduler.

This script reproduces the offline leave-one-instance folds used by
``audit_cbf_delay_queue_scheduler.py`` and writes every holdout row whose
H=2 label is unsafe but whose predicted probability crosses the calibrated
``HIGH_PRIORITY`` threshold.

The catalog is diagnostic-only.  It never runs BPC/pricing/RMP, never creates
columns, and never changes certificate or official lower-bound semantics.
False positives in this catalog mean the corresponding bucket must remain
``DELAY_QUEUE`` / abstain, not that the row should be discarded.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

from BPC_future.scripts.audit_cbf_delay_queue_scheduler import (
    DEFAULT_DATASET,
    _select_zero_fp_threshold,
)
from BPC_future.scripts.audit_cbf_gate_family_policy import infer_family
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
    _predict_probabilities,
    _standardize,
    _standardize_fit,
    _train_logistic,
    load_rows,
)


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/cbf_delay_queue_false_positive_catalog_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_cbf_delay_queue_false_positive_catalog_zh.md"
)


ONLINE_SNAPSHOT_FIELDS = (
    "v_t",
    "h_t",
    "cg_iter",
    "depth",
    "action_returned_count",
    "action_negative_count",
    "action_unique_task_set_count",
    "action_avg_task_set_size",
    "action_duplicate_task_set_count",
    "action_first_task_entropy",
    "action_second_action_entropy",
    "state_t_dual_l1_delta",
    "state_t_hidden_negative_count",
    "state_t_basis_turnover",
    "state_t_replacement_ratio",
    "state_t_support_changing_progress",
    "state_t_mode_negative_count",
    "state_t_mode_returned_journey_count",
    "state_t_mode_replacement_ratio",
    "state_t_mode_support_changing_ratio",
    "state_t_residual_mode_entropy",
)
LABEL_SNAPSHOT_FIELDS = (
    "horizon_delta_v",
    "horizon_barrier_slack",
    "horizon_mode_switched",
    "horizon_active_hash_switched",
    "label_horizon_cbf_feasible",
    "label_horizon_bad_mode_transition",
    "label_horizon_delta_v_nonpositive",
)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _snapshot(row: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: row.get(field) for field in fields if field in row}


def _record_false_positive(
    *,
    scope: str,
    task_count: int,
    family: str | None,
    holdout_name: str,
    row_index: int,
    row: dict[str, Any],
    probability: float,
    threshold: float,
    feature_names: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": "cbf_delay_queue_false_positive_record_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "official_bound_effect": False,
        "scope": scope,
        "task_count": int(task_count),
        "family": str(family or infer_family(row)),
        "holdout_name": str(holdout_name),
        "row_index": int(row_index),
        "instance": str(row.get("instance", "")),
        "source_file": str(row.get("source_file", "")),
        "context_hash": row.get("context_hash"),
        "state_t_z_hash": row.get("state_t_z_hash"),
        "probability": float(probability),
        "threshold": float(threshold),
        "margin_above_threshold": float(probability) - float(threshold),
        "label": 0,
        "predicted_decision": "HIGH_PRIORITY",
        "required_safe_decision": "DELAY_QUEUE",
        "exactness_action": "force_delay_not_discard",
        "negative_column_eventually_reachable_required": True,
        "finite_delay_required": True,
        "delay_queue_is_proof_blocking": False,
        "online_snapshot": _snapshot(row, ONLINE_SNAPSHOT_FIELDS),
        "label_snapshot": _snapshot(row, LABEL_SNAPSHOT_FIELDS),
        "feature_names": list(feature_names),
    }


def _fold_catalog(
    *,
    scope: str,
    task_count: int,
    family: str | None,
    holdout_name: str,
    train_indexed: list[tuple[int, dict[str, Any]]],
    holdout_indexed: list[tuple[int, dict[str, Any]]],
    epochs: int,
    lr: float,
    l2: float,
    min_train_high_priority: int,
    min_high_priority_threshold: float,
) -> dict[str, Any]:
    train_rows = [row for _idx, row in train_indexed]
    holdout_rows = [row for _idx, row in holdout_indexed]
    train_y = _trajectory_labels(train_rows)
    holdout_y = _trajectory_labels(holdout_rows)
    if not train_y or sum(train_y) <= 0 or sum(train_y) >= len(train_y):
        return {
            "scope": scope,
            "task_count": int(task_count),
            "family": None if family is None else str(family),
            "holdout_name": str(holdout_name),
            "status": "skipped_train_single_label",
            "train_count": len(train_rows),
            "holdout_count": len(holdout_rows),
            "false_positive_count": 0,
            "records": [],
        }
    feature_names = trajectory_gate_feature_names(train_rows)
    if not feature_names:
        return {
            "scope": scope,
            "task_count": int(task_count),
            "family": None if family is None else str(family),
            "holdout_name": str(holdout_name),
            "status": "skipped_no_features",
            "train_count": len(train_rows),
            "holdout_count": len(holdout_rows),
            "false_positive_count": 0,
            "records": [],
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
    records: list[dict[str, Any]] = []
    for (row_index, row), prob, label in zip(holdout_indexed, holdout_prob, holdout_y):
        if int(label) == 0 and float(prob) >= threshold:
            records.append(
                _record_false_positive(
                    scope=scope,
                    task_count=task_count,
                    family=family,
                    holdout_name=holdout_name,
                    row_index=row_index,
                    row=row,
                    probability=float(prob),
                    threshold=threshold,
                    feature_names=feature_names,
                )
            )
    return {
        "scope": scope,
        "task_count": int(task_count),
        "family": None if family is None else str(family),
        "holdout_name": str(holdout_name),
        "status": "evaluated",
        "train_count": len(train_rows),
        "holdout_count": len(holdout_rows),
        "train_label_counts": dict(Counter(str(label) for label in train_y)),
        "holdout_label_counts": dict(Counter(str(label) for label in holdout_y)),
        "threshold": threshold,
        "chosen_scheduler": chosen,
        "false_positive_count": len(records),
        "records": records,
    }


def _instance_folds(
    indexed_rows: list[tuple[int, dict[str, Any]]],
    *,
    scope: str,
    task_count: int,
    family: str | None,
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
        train_indexed = [
            (idx, row)
            for idx, row in indexed_rows
            if idx in all_indices and idx not in holdout_indices
        ]
        if len(holdout_indexed) < int(min_holdout_rows):
            folds.append(
                {
                    "scope": scope,
                    "task_count": int(task_count),
                    "family": None if family is None else str(family),
                    "holdout_name": instance,
                    "status": "skipped_too_few_holdout_rows",
                    "holdout_count": len(holdout_indexed),
                    "false_positive_count": 0,
                    "records": [],
                }
            )
            continue
        if len(train_indexed) < int(min_train_rows):
            folds.append(
                {
                    "scope": scope,
                    "task_count": int(task_count),
                    "family": None if family is None else str(family),
                    "holdout_name": instance,
                    "status": "skipped_too_few_train_rows",
                    "train_count": len(train_indexed),
                    "holdout_count": len(holdout_indexed),
                    "false_positive_count": 0,
                    "records": [],
                }
            )
            continue
        folds.append(
            _fold_catalog(
                scope=scope,
                task_count=task_count,
                family=family,
                holdout_name=instance,
                train_indexed=train_indexed,
                holdout_indexed=holdout_indexed,
                epochs=epochs,
                lr=lr,
                l2=l2,
                min_train_high_priority=min_train_high_priority,
                min_high_priority_threshold=min_high_priority_threshold,
            )
        )
    return folds


def _fold_count_summary(folds: list[dict[str, Any]]) -> dict[str, Any]:
    evaluated = [fold for fold in folds if fold.get("status") == "evaluated"]
    skipped = [fold for fold in folds if fold.get("status") != "evaluated"]
    fp_count = sum(int(fold.get("false_positive_count", 0)) for fold in evaluated)
    return {
        "fold_count": len(folds),
        "evaluated_count": len(evaluated),
        "skipped_count": len(skipped),
        "false_positive_count": fp_count,
        "has_false_positive": bool(fp_count > 0),
        "skipped_status_counts": dict(Counter(str(fold.get("status")) for fold in skipped)),
    }


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    preview = summary["false_positive_records"][:10]
    lines = [
        "# CBF Delay-Queue False Positive 目录",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告列出 H=2 delay scheduler 中被误放入 `HIGH_PRIORITY` 的",
        "unsafe transition。它只读离线 dataset，不运行 BPC / pricing / RMP，",
        "不生成列，不产生 certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "cbf_delay_queue_false_positive_catalog = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"false_positive_record_count = {summary['false_positive_record_count']}",
        f"catalog_requires_force_delay = {str(summary['catalog_requires_force_delay']).lower()}",
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
                "false_positive_record_count": summary["false_positive_record_count"],
                "false_positive_by_scope": summary["false_positive_by_scope"],
                "false_positive_by_family": summary["false_positive_by_family"],
                "false_positive_by_instance": summary["false_positive_by_instance"],
                "min_high_priority_threshold": summary["min_high_priority_threshold"],
                "scale_summaries": summary["scale_summaries"],
                "family_summaries": summary["family_summaries"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 前 10 条误判记录",
        "",
        "```json",
        json.dumps(preview, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## 结论",
        "",
        "- 这些记录是 `HIGH_PRIORITY` 风险样本；正确动作是 force delay，不是 discard；",
        "- 该目录用于补采数据 / 增加 online state 特征 / 收紧 abstain 策略；",
        "- 在 false-positive 未消除前，scheduler 不能接 worker、certificate 或 official bound。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_false_positive_catalog(
    dataset: Path,
    *,
    output_dir: Path,
    report: Path,
    min_enabled_task_count: int = 20,
    min_scale_rows: int = 30,
    min_family_rows: int = 20,
    min_holdout_rows: int = 2,
    min_train_rows: int = 20,
    min_train_high_priority: int = 1,
    min_high_priority_threshold: float = 0.8,
    epochs: int = 500,
    lr: float = 0.05,
    l2: float = 1.0e-4,
) -> dict[str, Any]:
    rows = load_rows(dataset)
    no_effect_count = sum(1 for row in rows if _is_no_effect_row(row))
    scale_folds: list[dict[str, Any]] = []
    family_folds: list[dict[str, Any]] = []

    for task_count, indexed in _task_groups(rows).items():
        scale_rows = [row for _idx, row in indexed]
        if int(task_count) < int(min_enabled_task_count) or len(scale_rows) < int(min_scale_rows):
            continue
        scale_folds.extend(
            _instance_folds(
                indexed,
                scope="scale",
                task_count=task_count,
                family=None,
                min_holdout_rows=min_holdout_rows,
                min_train_rows=min_train_rows,
                epochs=epochs,
                lr=lr,
                l2=l2,
                min_train_high_priority=min_train_high_priority,
                min_high_priority_threshold=min_high_priority_threshold,
            )
        )

    for (task_count, family), indexed in _family_groups(rows).items():
        family_rows = [row for _idx, row in indexed]
        if int(task_count) < int(min_enabled_task_count) or len(family_rows) < int(min_family_rows):
            continue
        family_folds.extend(
            _instance_folds(
                indexed,
                scope="family",
                task_count=task_count,
                family=family,
                min_holdout_rows=min_holdout_rows,
                min_train_rows=min_train_rows,
                epochs=epochs,
                lr=lr,
                l2=l2,
                min_train_high_priority=min_train_high_priority,
                min_high_priority_threshold=min_high_priority_threshold,
            )
        )

    false_positive_records: list[dict[str, Any]] = []
    for fold in [*scale_folds, *family_folds]:
        false_positive_records.extend(fold.get("records", []))
    false_positive_records.sort(
        key=lambda row: (
            str(row.get("scope")),
            int(row.get("task_count", 0)),
            str(row.get("family")),
            -_safe_float(row.get("margin_above_threshold")),
            str(row.get("instance")),
        )
    )

    scale_summaries = _fold_count_summary(scale_folds)
    family_summaries = _fold_count_summary(family_folds)
    by_scope = Counter(str(row.get("scope")) for row in false_positive_records)
    by_family = Counter(
        f"{row.get('task_count')}|{row.get('family')}"
        for row in false_positive_records
    )
    by_instance = Counter(str(row.get("instance")) for row in false_positive_records)
    checks = {
        "all_rows_no_certificate_effect": bool(rows and no_effect_count == len(rows)),
        "uses_horizon_labels": bool(rows and "label_horizon_cbf_feasible" in rows[0]),
        "catalog_records_are_force_delay": all(
            row.get("required_safe_decision") == "DELAY_QUEUE"
            and row.get("exactness_action") == "force_delay_not_discard"
            for row in false_positive_records
        ),
        "catalog_has_no_official_effect": all(
            row.get("official_bound_effect") is False for row in false_positive_records
        ),
    }
    summary = {
        "schema_version": "cbf_delay_queue_false_positive_catalog_v1",
        "status": "cbf_delay_queue_false_positive_catalog_built",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "dataset": str(dataset),
        "row_count": len(rows),
        "label_counts": _label_counts(rows),
        "no_effect_row_count": no_effect_count,
        "min_enabled_task_count": int(min_enabled_task_count),
        "min_scale_rows": int(min_scale_rows),
        "min_family_rows": int(min_family_rows),
        "min_holdout_rows": int(min_holdout_rows),
        "min_train_rows": int(min_train_rows),
        "min_train_high_priority": int(min_train_high_priority),
        "min_high_priority_threshold": float(min_high_priority_threshold),
        "scale_summaries": scale_summaries,
        "family_summaries": family_summaries,
        "false_positive_record_count": len(false_positive_records),
        "false_positive_by_scope": dict(sorted(by_scope.items())),
        "false_positive_by_family": dict(sorted(by_family.items())),
        "false_positive_by_instance": dict(by_instance.most_common()),
        "false_positive_records": false_positive_records,
        "catalog_requires_force_delay": bool(false_positive_records),
        "recommended_action": "keep_scheduler_audit_only_and_force_delay_affected_buckets",
        "gate_can_permanently_discard_negative_columns": False,
        "negative_columns_must_remain_eventually_reachable": True,
        "finite_delay_required": True,
        "delay_queue_is_proof_blocking": False,
        "production_ready": False,
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
    records_path = output_dir / "false_positive_records.jsonl"
    records_path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in false_positive_records
        ),
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
    parser.add_argument("--min-train-high-priority", type=int, default=1)
    parser.add_argument("--min-high-priority-threshold", type=float, default=0.8)
    parser.add_argument("--epochs", type=int, default=500)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--l2", type=float, default=1.0e-4)
    args = parser.parse_args(argv)
    summary = build_false_positive_catalog(
        args.dataset,
        output_dir=args.output_dir,
        report=args.report,
        min_enabled_task_count=args.min_enabled_task_count,
        min_scale_rows=args.min_scale_rows,
        min_family_rows=args.min_family_rows,
        min_holdout_rows=args.min_holdout_rows,
        min_train_rows=args.min_train_rows,
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
                "records": str(args.output_dir / "false_positive_records.jsonl"),
                "report": str(args.report),
                "all_checks_pass": summary["all_checks_pass"],
                "false_positive_record_count": summary["false_positive_record_count"],
                "false_positive_by_family": summary["false_positive_by_family"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

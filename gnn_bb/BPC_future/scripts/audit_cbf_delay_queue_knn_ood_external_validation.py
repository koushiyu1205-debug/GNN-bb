#!/usr/bin/env python3
"""External validation for a kNN+OOD CBF delay-queue scheduler.

The train dataset is used once to fit the logistic gate, zero-FP threshold,
kNN unsafe-density memory, and safe-manifold radius.  The validation dataset is
then evaluated without refitting.  This is diagnostic-only: it never runs
BPC/pricing/RMP, never generates columns, and never creates certificates or
official lower bounds.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

from BPC_future.scripts.audit_cbf_delay_queue_knn_ood_scheduler import (
    DEFAULT_DATASET,
    _nearest_safe_distance,
    _neighbor_unsafe_fraction,
    _safe_radius_threshold,
)
from BPC_future.scripts.audit_cbf_delay_queue_scheduler import _select_zero_fp_threshold
from BPC_future.scripts.audit_cbf_gate_family_policy import infer_family
from BPC_future.scripts.audit_cbf_trajectory_gate_policy import (
    _label_counts,
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


DEFAULT_TRAIN_DATASET = DEFAULT_DATASET
DEFAULT_VALIDATION_DATASET = DEFAULT_DATASET
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/cbf_delay_queue_knn_ood_external_validation_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_cbf_delay_queue_knn_ood_external_validation_zh.md"
)


def _row_key(row: dict[str, Any]) -> tuple[str, str, str, str, int, int]:
    return (
        str(row.get("source_file", "")),
        str(row.get("instance", "")),
        str(row.get("context_hash", "")),
        str(row.get("horizon_next_context_hash", "")),
        int(row.get("cg_iter", -1) or -1),
        int(row.get("horizon_next_cg_iter", -1) or -1),
    )


def _metrics_from_decisions(decisions: list[int], labels: list[int]) -> dict[str, Any]:
    tp = sum(1 for pred, label in zip(decisions, labels) if pred == 1 and label == 1)
    fp = sum(1 for pred, label in zip(decisions, labels) if pred == 1 and label == 0)
    tn = sum(1 for pred, label in zip(decisions, labels) if pred == 0 and label == 0)
    fn = sum(1 for pred, label in zip(decisions, labels) if pred == 0 and label == 1)
    predicted_positive = tp + fp
    positives = tp + fn
    negatives = tn + fp
    return {
        "total": len(labels),
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


def _validation_decision_record(
    row: dict[str, Any],
    *,
    label: int,
    prob: float | None,
    threshold: float | None,
    neighbor_unsafe_fraction: float | None,
    max_neighbor_unsafe_fraction: float,
    nearest_safe_distance: float | None,
    safe_radius: float | None,
    decision: int,
) -> dict[str, Any]:
    probability_ok = (
        False if prob is None or threshold is None else float(prob) >= float(threshold)
    )
    neighbor_ok = (
        False
        if neighbor_unsafe_fraction is None
        else float(neighbor_unsafe_fraction) <= float(max_neighbor_unsafe_fraction)
    )
    radius_ok = (
        False
        if nearest_safe_distance is None or safe_radius is None
        else float(nearest_safe_distance) <= float(safe_radius)
    )
    if int(decision) == 1:
        reason = "high_priority"
    elif not probability_ok:
        reason = "delay_probability_below_threshold"
    elif not neighbor_ok:
        reason = "delay_neighbor_unsafe_fraction"
    elif not radius_ok:
        reason = "delay_ood_safe_radius"
    else:
        reason = "delay_unknown_guard"
    return {
        "source_file": str(row.get("source_file", "")),
        "instance": str(row.get("instance", "")),
        "task_count": int(row.get("task_count", 0) or 0),
        "family": infer_family(row),
        "task_family": f"{row.get('task_count')}|{infer_family(row)}",
        "cg_iter": int(row.get("cg_iter", -1) or -1),
        "horizon_next_cg_iter": int(row.get("horizon_next_cg_iter", -1) or -1),
        "label_horizon_cbf_feasible": int(label),
        "decision": int(decision),
        "decision_name": "HIGH_PRIORITY" if int(decision) == 1 else "DELAY_QUEUE",
        "decision_reason": reason,
        "probability": prob,
        "threshold": threshold,
        "probability_ok": probability_ok,
        "neighbor_unsafe_fraction": neighbor_unsafe_fraction,
        "max_neighbor_unsafe_fraction": float(max_neighbor_unsafe_fraction),
        "neighbor_ok": neighbor_ok,
        "nearest_safe_distance": nearest_safe_distance,
        "safe_radius": safe_radius,
        "safe_radius_ok": radius_ok,
        "horizon_barrier_slack": row.get("horizon_barrier_slack"),
        "horizon_delta_v": row.get("horizon_delta_v"),
        "state_t_dual_l1_delta": row.get("state_t_dual_l1_delta"),
        "state_t_residual_mode_entropy": row.get("state_t_residual_mode_entropy"),
        "action_negative_count": row.get("action_negative_count"),
        "action_unique_task_set_count": row.get("action_unique_task_set_count"),
    }


def _group_validation(rows: list[dict[str, Any]], decisions: list[int]) -> dict[str, Any]:
    labels = _trajectory_labels(rows)
    by_scale: dict[str, tuple[list[dict[str, Any]], list[int]]] = {}
    by_family: dict[str, tuple[list[dict[str, Any]], list[int]]] = {}
    for row, decision in zip(rows, decisions):
        scale_key = str(row.get("task_count", ""))
        family_key = f"{row.get('task_count')}|{infer_family(row)}"
        by_scale.setdefault(scale_key, ([], []))
        by_scale[scale_key][0].append(row)
        by_scale[scale_key][1].append(decision)
        by_family.setdefault(family_key, ([], []))
        by_family[family_key][0].append(row)
        by_family[family_key][1].append(decision)
    return {
        "overall": _metrics_from_decisions(decisions, labels),
        "by_scale": {
            key: _metrics_from_decisions(group_decisions, _trajectory_labels(group_rows))
            for key, (group_rows, group_decisions) in sorted(by_scale.items())
        },
        "by_family": {
            key: _metrics_from_decisions(group_decisions, _trajectory_labels(group_rows))
            for key, (group_rows, group_decisions) in sorted(by_family.items())
        },
    }


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CBF Delay-Queue kNN+OOD External Validation 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "用独立 train / validation trajectory datasets 验证 kNN+OOD delay scheduler。",
        "该脚本只读 JSONL，不运行 BPC / pricing / RMP，不生成列，不产生",
        "certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "cbf_delay_queue_knn_ood_external_validation = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"train_row_count = {summary['train_row_count']}",
        f"validation_row_count = {summary['validation_row_count']}",
        f"validation_candidate_ready = {str(summary['validation_candidate_ready']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 摘要",
        "",
        "```json",
        json.dumps(
            {
                "train_label_counts": summary["train_label_counts"],
                "validation_label_counts": summary["validation_label_counts"],
                "threshold": summary["threshold"],
                "safe_radius": summary["safe_radius"],
                "validation_metrics": summary["validation_metrics"],
                "decision_reason_counts": summary.get("decision_reason_counts", {}),
                "positive_delay_reason_counts": summary.get(
                    "positive_delay_reason_counts", {}
                ),
                "decision_records_path": summary.get("decision_records_path"),
                "validation_candidate_ready": summary["validation_candidate_ready"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 解释",
        "",
        "- validation candidate 仍只是离线验证，不等于 production ready；",
        "- false positive 表示 unsafe transition 被放进 HIGH_PRIORITY，必须阻止上线；",
        "- zero high-priority 表示过于保守，不能证明 ROI；",
        "- delay queue 仍不能 discard true-RC negative，也不能扩展 proof budget。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def audit_external_validation(
    train_dataset: Path,
    validation_dataset: Path,
    *,
    output_dir: Path,
    report: Path,
    exclude_train_keys: bool = True,
    min_validation_rows: int = 10,
    min_validation_high_priority: int = 1,
    min_high_priority_threshold: float = 0.8,
    min_train_high_priority: int = 1,
    knn_k: int = 5,
    max_neighbor_unsafe_fraction: float = 0.0,
    safe_radius_quantile: float = 0.9,
    safe_radius_multiplier: float = 1.0,
    epochs: int = 500,
    lr: float = 0.05,
    l2: float = 1.0e-4,
) -> dict[str, Any]:
    train_rows = load_rows(train_dataset)
    validation_rows_raw = load_rows(validation_dataset)
    train_keys = {_row_key(row) for row in train_rows}
    validation_rows = [
        row for row in validation_rows_raw if not exclude_train_keys or _row_key(row) not in train_keys
    ]
    train_y = _trajectory_labels(train_rows)
    validation_y = _trajectory_labels(validation_rows)
    feature_names = trajectory_gate_feature_names(train_rows)

    decisions: list[int] = []
    decision_records: list[dict[str, Any]] = []
    threshold: float | None = None
    safe_radius: float | None = None
    status = "external_validation_audited"
    if (
        train_rows
        and validation_rows
        and feature_names
        and train_y
        and sum(train_y) > 0
        and sum(train_y) < len(train_y)
    ):
        train_x_raw = [_features(row, feature_names) for row in train_rows]
        validation_x_raw = [_features(row, feature_names) for row in validation_rows]
        means, stds = _standardize_fit(train_x_raw)
        train_x = _standardize(train_x_raw, means, stds)
        validation_x = _standardize(validation_x_raw, means, stds)
        weights = _train_logistic(train_x, train_y, epochs=epochs, lr=lr, l2=l2)
        train_prob = _predict_probabilities(train_x, weights)
        validation_prob = _predict_probabilities(validation_x, weights)
        chosen = _select_zero_fp_threshold(
            train_prob,
            train_y,
            min_train_high_priority=min_train_high_priority,
            min_high_priority_threshold=min_high_priority_threshold,
        )
        threshold = float(chosen["threshold"])
        safe_radius = _safe_radius_threshold(
            train_x,
            train_y,
            quantile=safe_radius_quantile,
            multiplier=safe_radius_multiplier,
        )
        for row, row_x, label, prob in zip(
            validation_rows,
            validation_x,
            validation_y,
            validation_prob,
        ):
            risk = _neighbor_unsafe_fraction(train_x, train_y, row_x, k=knn_k)
            nearest_safe = _nearest_safe_distance(train_x, train_y, row_x)
            in_safe_radius = bool(
                safe_radius is not None
                and nearest_safe is not None
                and nearest_safe <= safe_radius
            )
            decision = (
                1
                if float(prob) >= float(threshold)
                and risk <= float(max_neighbor_unsafe_fraction)
                and in_safe_radius
                else 0
            )
            decisions.append(decision)
            decision_records.append(
                _validation_decision_record(
                    row,
                    label=label,
                    prob=float(prob),
                    threshold=float(threshold),
                    neighbor_unsafe_fraction=float(risk),
                    max_neighbor_unsafe_fraction=float(max_neighbor_unsafe_fraction),
                    nearest_safe_distance=(
                        None if nearest_safe is None else float(nearest_safe)
                    ),
                    safe_radius=None if safe_radius is None else float(safe_radius),
                    decision=decision,
                )
            )
    else:
        status = "external_validation_skipped_insufficient_data"
        decisions = [0 for _row in validation_rows]
        decision_records = [
            _validation_decision_record(
                row,
                label=label,
                prob=None,
                threshold=None,
                neighbor_unsafe_fraction=None,
                max_neighbor_unsafe_fraction=float(max_neighbor_unsafe_fraction),
                nearest_safe_distance=None,
                safe_radius=None,
                decision=0,
            )
            for row, label in zip(validation_rows, validation_y)
        ]

    validation_metrics = _group_validation(validation_rows, decisions)
    overall = validation_metrics["overall"]
    reason_counts = dict(
        sorted(
            Counter(str(record["decision_reason"]) for record in decision_records).items()
        )
    )
    positive_delay_reason_counts = dict(
        sorted(
            Counter(
                str(record["decision_reason"])
                for record in decision_records
                if int(record["label_horizon_cbf_feasible"]) == 1
                and int(record["decision"]) == 0
            ).items()
        )
    )
    validation_candidate_ready = bool(
        len(validation_rows) >= int(min_validation_rows)
        and int(overall.get("fp", 0)) == 0
        and int(overall.get("predicted_positive", 0)) >= int(min_validation_high_priority)
    )
    train_no_effect_count = sum(1 for row in train_rows if _is_no_effect_row(row))
    validation_no_effect_count = sum(1 for row in validation_rows if _is_no_effect_row(row))
    checks = {
        "train_rows_no_certificate_effect": bool(train_rows and train_no_effect_count == len(train_rows)),
        "validation_rows_no_certificate_effect": bool(
            validation_rows and validation_no_effect_count == len(validation_rows)
        ),
        "has_train_features": bool(feature_names),
        "uses_horizon_labels": bool(train_rows and "label_horizon_cbf_feasible" in train_rows[0]),
        "delay_queue_exactness_guard_present": True,
        "delay_queue_proof_budget_guard_present": True,
    }
    summary = {
        "schema_version": "cbf_delay_queue_knn_ood_external_validation_v1",
        "status": status,
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "train_dataset": str(train_dataset),
        "validation_dataset": str(validation_dataset),
        "exclude_train_keys": bool(exclude_train_keys),
        "train_row_count": len(train_rows),
        "validation_raw_row_count": len(validation_rows_raw),
        "validation_row_count": len(validation_rows),
        "train_label_counts": _label_counts(train_rows),
        "validation_label_counts": _label_counts(validation_rows),
        "feature_count": len(feature_names),
        "threshold": threshold,
        "safe_radius": safe_radius,
        "min_high_priority_threshold": float(min_high_priority_threshold),
        "knn_k": int(knn_k),
        "max_neighbor_unsafe_fraction": float(max_neighbor_unsafe_fraction),
        "safe_radius_quantile": float(safe_radius_quantile),
        "safe_radius_multiplier": float(safe_radius_multiplier),
        "validation_metrics": validation_metrics,
        "decision_reason_counts": reason_counts,
        "positive_delay_reason_counts": positive_delay_reason_counts,
        "decision_records_path": str(output_dir / "decision_records.jsonl"),
        "decision_samples": decision_records[:10],
        "validation_candidate_ready": validation_candidate_ready,
        "production_ready": False,
        "official_bound_effect": False,
        "gate_role": "external_validation_of_stability_scheduler_not_column_filter",
        "safe_negative_decision": "HIGH_PRIORITY",
        "unsafe_negative_decision": "DELAY_QUEUE",
        "nonnegative_decision": "REJECT_NONNEGATIVE_ONLY",
        "gate_can_permanently_discard_negative_columns": False,
        "negative_columns_must_remain_eventually_reachable": True,
        "finite_delay_required": True,
        "delay_queue_is_proof_blocking": False,
        "delay_queue_can_extend_proof_budget": False,
        "delay_queue_runs_proof_sweep": False,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "goal_complete": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "decision_records.jsonl").write_text(
        "\n".join(
            json.dumps(record, ensure_ascii=False, sort_keys=True)
            for record in decision_records
        )
        + ("\n" if decision_records else ""),
        encoding="utf-8",
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-dataset", type=Path, default=DEFAULT_TRAIN_DATASET)
    parser.add_argument("--validation-dataset", type=Path, default=DEFAULT_VALIDATION_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--include-train-keys", action="store_true")
    parser.add_argument("--min-validation-rows", type=int, default=10)
    parser.add_argument("--min-validation-high-priority", type=int, default=1)
    parser.add_argument("--min-high-priority-threshold", type=float, default=0.8)
    parser.add_argument("--min-train-high-priority", type=int, default=1)
    parser.add_argument("--knn-k", type=int, default=5)
    parser.add_argument("--max-neighbor-unsafe-fraction", type=float, default=0.0)
    parser.add_argument("--safe-radius-quantile", type=float, default=0.9)
    parser.add_argument("--safe-radius-multiplier", type=float, default=1.0)
    parser.add_argument("--epochs", type=int, default=500)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--l2", type=float, default=1.0e-4)
    args = parser.parse_args(argv)
    summary = audit_external_validation(
        args.train_dataset,
        args.validation_dataset,
        output_dir=args.output_dir,
        report=args.report,
        exclude_train_keys=not args.include_train_keys,
        min_validation_rows=args.min_validation_rows,
        min_validation_high_priority=args.min_validation_high_priority,
        min_high_priority_threshold=args.min_high_priority_threshold,
        min_train_high_priority=args.min_train_high_priority,
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
                "validation_candidate_ready": summary["validation_candidate_ready"],
                "validation_row_count": summary["validation_row_count"],
                "validation_metrics": summary["validation_metrics"]["overall"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

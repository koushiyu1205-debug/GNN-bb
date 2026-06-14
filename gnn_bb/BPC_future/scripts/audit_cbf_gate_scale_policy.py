#!/usr/bin/env python3
"""Audit a scale-aware CBF gate policy.

The global CBF gate can look good on a random validation split while failing
across task-count or instance holdouts.  This audit evaluates the conservative
alternative: task counts below a configured minimum must abstain, and every
enabled task-count bucket must pass within-scale leave-one-instance safety
before it may be considered for later production A/B.

The script is diagnostic-only.  It never runs BPC/pricing/RMP, never generates
columns, and never creates certificates or official lower bounds.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any

from BPC_future.scripts.audit_cbf_gate_holdout import _fold_audit
from BPC_future.scripts.train_cbf_gate import (
    _is_no_effect_row,
    _labels,
    cbf_gate_feature_names,
    load_rows,
)


DEFAULT_DATASET = Path("BPC_future/results/cbf_gate_dataset_global_available_20260614/cbf_gate_transitions.jsonl")
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/cbf_gate_scale_policy_audit_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_cbf_gate_scale_policy_audit_zh.md"
)


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _task_groups(rows: list[dict[str, Any]]) -> dict[int, list[tuple[int, dict[str, Any]]]]:
    groups: dict[int, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for idx, row in enumerate(rows):
        groups[_as_int(row.get("task_count"))].append((idx, row))
    return dict(sorted(groups.items()))


def _label_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(str(label) for label in _labels(rows)))


def _can_train(rows: list[dict[str, Any]]) -> bool:
    labels = _labels(rows)
    return bool(rows and sum(labels) > 0 and sum(labels) < len(labels))


def _within_scale_instance_folds(
    indexed_rows: list[tuple[int, dict[str, Any]]],
    *,
    task_count: int,
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
    folds: list[dict[str, Any]] = []
    all_indices = {idx for idx, _row in indexed_rows}
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
                    "fold_kind": "within_scale_leave_one_instance",
                    "task_count": int(task_count),
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
                    "fold_kind": "within_scale_leave_one_instance",
                    "task_count": int(task_count),
                    "holdout_name": instance,
                    "status": "skipped_too_few_train_rows",
                    "train_count": len(train_rows),
                    "holdout_count": len(holdout_rows),
                    "strict_safety_pass": False,
                }
            )
            continue
        if not _can_train(train_rows):
            folds.append(
                {
                    "fold_kind": "within_scale_leave_one_instance",
                    "task_count": int(task_count),
                    "holdout_name": instance,
                    "status": "skipped_train_single_label",
                    "train_count": len(train_rows),
                    "holdout_count": len(holdout_rows),
                    "train_label_counts": _label_counts(train_rows),
                    "holdout_label_counts": _label_counts(holdout_rows),
                    "strict_safety_pass": False,
                }
            )
            continue
        fold = _fold_audit(
            fold_kind="within_scale_leave_one_instance",
            holdout_name=instance,
            train_rows=train_rows,
            holdout_rows=holdout_rows,
            epochs=epochs,
            lr=lr,
            l2=l2,
            min_precision=min_precision,
            max_false_positive_rate=max_false_positive_rate,
        )
        fold["task_count"] = int(task_count)
        folds.append(fold)
    return folds


def _fold_summary(folds: list[dict[str, Any]]) -> dict[str, Any]:
    evaluated = [fold for fold in folds if fold.get("status") == "evaluated"]
    skipped = [fold for fold in folds if fold.get("status") != "evaluated"]
    false_positive = [
        fold
        for fold in evaluated
        if int((fold.get("holdout_metrics") or {}).get("fp", 0)) > 0
    ]
    productive = [
        fold for fold in evaluated if fold.get("productive_holdout_adds") is True
    ]
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


def audit_scale_policy(
    dataset: Path,
    *,
    output_dir: Path,
    report: Path,
    min_enabled_task_count: int = 20,
    min_scale_rows: int = 30,
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
    feature_names = cbf_gate_feature_names(rows)
    scale_results: list[dict[str, Any]] = []
    for task_count, indexed in _task_groups(rows).items():
        scale_rows = [row for _idx, row in indexed]
        feature_count = len(cbf_gate_feature_names(scale_rows))
        base = {
            "task_count": int(task_count),
            "row_count": len(scale_rows),
            "label_counts": _label_counts(scale_rows),
            "feature_count": feature_count,
            "scale_guard_min_enabled_task_count": int(min_enabled_task_count),
        }
        if int(task_count) < int(min_enabled_task_count):
            scale_results.append(
                {
                    **base,
                    "status": "guarded_abstain_below_min_task_count",
                    "scale_gate_candidate_ready": False,
                    "must_abstain": True,
                    "reason": "protect_5_10_no_regression",
                    "fold_summary": {
                        "fold_count": 0,
                        "evaluated_count": 0,
                        "skipped_count": 0,
                        "false_positive_fold_count": 0,
                        "productive_fold_count": 0,
                    },
                    "folds": [],
                }
            )
            continue
        if len(scale_rows) < int(min_scale_rows):
            scale_results.append(
                {
                    **base,
                    "status": "insufficient_scale_rows",
                    "scale_gate_candidate_ready": False,
                    "must_abstain": True,
                    "reason": "scale_rows_below_minimum",
                    "fold_summary": {
                        "fold_count": 0,
                        "evaluated_count": 0,
                        "skipped_count": 0,
                        "false_positive_fold_count": 0,
                        "productive_fold_count": 0,
                    },
                    "folds": [],
                }
            )
            continue
        if not _can_train(scale_rows):
            scale_results.append(
                {
                    **base,
                    "status": "insufficient_scale_label_coverage",
                    "scale_gate_candidate_ready": False,
                    "must_abstain": True,
                    "reason": "scale_has_single_label",
                    "fold_summary": {
                        "fold_count": 0,
                        "evaluated_count": 0,
                        "skipped_count": 0,
                        "false_positive_fold_count": 0,
                        "productive_fold_count": 0,
                    },
                    "folds": [],
                }
            )
            continue
        folds = _within_scale_instance_folds(
            indexed,
            task_count=task_count,
            min_holdout_rows=min_holdout_rows,
            min_train_rows=min_train_rows,
            epochs=epochs,
            lr=lr,
            l2=l2,
            min_precision=min_precision,
            max_false_positive_rate=max_false_positive_rate,
        )
        fold_summary = _fold_summary(folds)
        candidate_ready = bool(
            fold_summary["evaluated_no_false_positive"]
            and fold_summary["evaluated_count"] >= int(min_evaluated_folds)
            and fold_summary["productive_fold_count"] > 0
        )
        scale_results.append(
            {
                **base,
                "status": "scale_gate_candidate_ready"
                if candidate_ready
                else "scale_gate_not_ready",
                "scale_gate_candidate_ready": candidate_ready,
                "must_abstain": not candidate_ready,
                "reason": "passed_within_scale_holdout"
                if candidate_ready
                else "within_scale_holdout_not_safe_or_not_productive",
                "fold_summary": fold_summary,
                "folds": folds,
            }
        )

    ready_task_counts = [
        item["task_count"] for item in scale_results if item["scale_gate_candidate_ready"]
    ]
    below_min_abstain_ok = all(
        item["must_abstain"] and item["status"] == "guarded_abstain_below_min_task_count"
        for item in scale_results
        if item["task_count"] < int(min_enabled_task_count)
    )
    checks = {
        "all_rows_no_certificate_effect": bool(rows and no_effect_count == len(rows)),
        "has_current_state_features": bool(feature_names),
        "below_min_task_counts_abstain": below_min_abstain_ok,
        "scale_results_present": bool(scale_results),
    }
    summary = {
        "schema_version": "cbf_gate_scale_policy_audit_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "cbf_gate_scale_policy_audited",
        "dataset": str(dataset),
        "row_count": len(rows),
        "no_effect_row_count": no_effect_count,
        "feature_count": len(feature_names),
        "label_counts": _label_counts(rows),
        "task_count_histogram": dict(Counter(str(_as_int(row.get("task_count"))) for row in rows)),
        "min_enabled_task_count": int(min_enabled_task_count),
        "min_scale_rows": int(min_scale_rows),
        "min_holdout_rows": int(min_holdout_rows),
        "min_train_rows": int(min_train_rows),
        "min_evaluated_folds": int(min_evaluated_folds),
        "ready_task_counts": ready_task_counts,
        "scale_results": scale_results,
        "scale_policy_ready": bool(ready_task_counts),
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
        "# CBF Gate Scale-aware Policy 审计报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "审计一个分 scale 的 CBF/RMP-impact gate 策略：小于阈值的 task_count",
        "必须 abstain，以保护 5/10 不退化；被允许的 scale 仍需通过本 scale",
        "leave-one-instance 安全审计。该脚本只读离线数据，不运行 BPC / pricing / RMP。",
        "",
        "## 机器字段",
        "",
        "```text",
        "cbf_gate_scale_policy_audit = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"scale_policy_ready = {str(summary['scale_policy_ready']).lower()}",
        f"ready_task_counts = {','.join(str(v) for v in summary['ready_task_counts'])}",
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
                "task_count_histogram": summary["task_count_histogram"],
                "min_enabled_task_count": summary["min_enabled_task_count"],
                "ready_task_counts": summary["ready_task_counts"],
                "scale_policy_ready": summary["scale_policy_ready"],
                "scale_results": [
                    {
                        "task_count": item["task_count"],
                        "row_count": item["row_count"],
                        "status": item["status"],
                        "must_abstain": item["must_abstain"],
                        "scale_gate_candidate_ready": item["scale_gate_candidate_ready"],
                        "fold_summary": item["fold_summary"],
                    }
                    for item in summary["scale_results"]
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
        "- `task_count < min_enabled_task_count` 的 scale 会强制 abstain，避免 5/10 退化；",
        "- `scale_policy_ready=false` 表示当前没有任何 scale 可以进入 production A/B；",
        "- 即使某个 scale ready，也仍需 full BPC A/B 才能接 production worker；",
        "- 该策略不影响 certificate，也不能证明 no-negative。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-enabled-task-count", type=int, default=20)
    parser.add_argument("--min-scale-rows", type=int, default=30)
    parser.add_argument("--min-holdout-rows", type=int, default=2)
    parser.add_argument("--min-train-rows", type=int, default=20)
    parser.add_argument("--min-evaluated-folds", type=int, default=2)
    parser.add_argument("--epochs", type=int, default=500)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--l2", type=float, default=1.0e-4)
    parser.add_argument("--min-precision", type=float, default=0.8)
    parser.add_argument("--max-false-positive-rate", type=float, default=0.05)
    args = parser.parse_args(argv)
    summary = audit_scale_policy(
        args.dataset,
        output_dir=args.output_dir,
        report=args.report,
        min_enabled_task_count=args.min_enabled_task_count,
        min_scale_rows=args.min_scale_rows,
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
                "scale_policy_ready": summary["scale_policy_ready"],
                "ready_task_counts": summary["ready_task_counts"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

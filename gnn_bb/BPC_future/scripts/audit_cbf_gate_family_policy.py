#!/usr/bin/env python3
"""Audit a family-aware CBF gate policy.

Scale-only CBF gating can still mix incompatible residual-family regimes.  This
audit splits rows by ``(task_count, family)`` and requires each enabled family
to pass within-family leave-one-instance safety before it may be considered for
future production A/B.  Small task counts remain guarded-abstain to protect
5/10 no-regression.

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
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/cbf_gate_family_policy_audit_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_cbf_gate_family_policy_audit_zh.md"
)


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def infer_family(row: dict[str, Any]) -> str:
    """Infer a coarse residual-family bucket from stable log metadata."""

    text = f"{row.get('instance', '')} {row.get('source_file', '')}".lower()
    for family in ("greedy-anchor", "random-wave", "sector-wave"):
        if family in text:
            return family
    if "very_small" in text:
        return "very_small"
    if "tasks10" in text:
        return "moon_trek_tasks10"
    if "tasks20" in text:
        return "moon_trek_tasks20"
    return "unknown"


def _label_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(str(label) for label in _labels(rows)))


def _can_train(rows: list[dict[str, Any]]) -> bool:
    labels = _labels(rows)
    return bool(rows and sum(labels) > 0 and sum(labels) < len(labels))


def _family_groups(rows: list[dict[str, Any]]) -> dict[tuple[int, str], list[tuple[int, dict[str, Any]]]]:
    groups: dict[tuple[int, str], list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for idx, row in enumerate(rows):
        groups[(_as_int(row.get("task_count")), infer_family(row))].append((idx, row))
    return dict(sorted(groups.items(), key=lambda item: (item[0][0], item[0][1])))


def _within_family_instance_folds(
    indexed_rows: list[tuple[int, dict[str, Any]]],
    *,
    task_count: int,
    family: str,
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
                    "fold_kind": "within_family_leave_one_instance",
                    "task_count": int(task_count),
                    "family": str(family),
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
                    "fold_kind": "within_family_leave_one_instance",
                    "task_count": int(task_count),
                    "family": str(family),
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
                    "fold_kind": "within_family_leave_one_instance",
                    "task_count": int(task_count),
                    "family": str(family),
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
            fold_kind="within_family_leave_one_instance",
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
        fold["family"] = str(family)
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


def audit_family_policy(
    dataset: Path,
    *,
    output_dir: Path,
    report: Path,
    min_enabled_task_count: int = 20,
    min_family_rows: int = 20,
    min_holdout_rows: int = 2,
    min_train_rows: int = 10,
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
    family_results: list[dict[str, Any]] = []
    for (task_count, family), indexed in _family_groups(rows).items():
        family_rows = [row for _idx, row in indexed]
        base = {
            "task_count": int(task_count),
            "family": str(family),
            "row_count": len(family_rows),
            "label_counts": _label_counts(family_rows),
            "feature_count": len(cbf_gate_feature_names(family_rows)),
            "min_enabled_task_count": int(min_enabled_task_count),
        }
        if int(task_count) < int(min_enabled_task_count):
            family_results.append(
                {
                    **base,
                    "status": "guarded_abstain_below_min_task_count",
                    "family_gate_candidate_ready": False,
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
        if len(family_rows) < int(min_family_rows):
            family_results.append(
                {
                    **base,
                    "status": "insufficient_family_rows",
                    "family_gate_candidate_ready": False,
                    "must_abstain": True,
                    "reason": "family_rows_below_minimum",
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
        if not _can_train(family_rows):
            family_results.append(
                {
                    **base,
                    "status": "insufficient_family_label_coverage",
                    "family_gate_candidate_ready": False,
                    "must_abstain": True,
                    "reason": "family_has_single_label",
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
        folds = _within_family_instance_folds(
            indexed,
            task_count=task_count,
            family=family,
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
        family_results.append(
            {
                **base,
                "status": "family_gate_candidate_ready"
                if candidate_ready
                else "family_gate_not_ready",
                "family_gate_candidate_ready": candidate_ready,
                "must_abstain": not candidate_ready,
                "reason": "passed_within_family_holdout"
                if candidate_ready
                else "within_family_holdout_not_safe_or_not_productive",
                "fold_summary": fold_summary,
                "folds": folds,
            }
        )

    ready_families = [
        {"task_count": item["task_count"], "family": item["family"]}
        for item in family_results
        if item["family_gate_candidate_ready"]
    ]
    small_abstain_ok = all(
        item["must_abstain"] and item["status"] == "guarded_abstain_below_min_task_count"
        for item in family_results
        if item["task_count"] < int(min_enabled_task_count)
    )
    checks = {
        "all_rows_no_certificate_effect": bool(rows and no_effect_count == len(rows)),
        "has_current_state_features": bool(feature_names),
        "below_min_task_counts_abstain": small_abstain_ok,
        "family_results_present": bool(family_results),
    }
    summary = {
        "schema_version": "cbf_gate_family_policy_audit_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "cbf_gate_family_policy_audited",
        "dataset": str(dataset),
        "row_count": len(rows),
        "no_effect_row_count": no_effect_count,
        "feature_count": len(feature_names),
        "label_counts": _label_counts(rows),
        "task_family_histogram": {
            f"{item['task_count']}|{item['family']}": item["row_count"]
            for item in family_results
        },
        "min_enabled_task_count": int(min_enabled_task_count),
        "min_family_rows": int(min_family_rows),
        "min_holdout_rows": int(min_holdout_rows),
        "min_train_rows": int(min_train_rows),
        "min_evaluated_folds": int(min_evaluated_folds),
        "ready_families": ready_families,
        "family_policy_ready": bool(ready_families),
        "family_results": family_results,
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
        "# CBF Gate Family-aware Policy 审计报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "审计 `(task_count, family)` 分层的 CBF/RMP-impact gate。小规模仍强制",
        "abstain；20 规模内每个 family 必须通过 within-family leave-one-instance",
        "安全审计，才能作为后续 production A/B 候选。本脚本只读离线数据。",
        "",
        "## 机器字段",
        "",
        "```text",
        "cbf_gate_family_policy_audit = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"family_policy_ready = {str(summary['family_policy_ready']).lower()}",
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
                "task_family_histogram": summary["task_family_histogram"],
                "ready_families": summary["ready_families"],
                "family_policy_ready": summary["family_policy_ready"],
                "family_results": [
                    {
                        "task_count": item["task_count"],
                        "family": item["family"],
                        "row_count": item["row_count"],
                        "status": item["status"],
                        "must_abstain": item["must_abstain"],
                        "family_gate_candidate_ready": item["family_gate_candidate_ready"],
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
        "- family-aware gate 是比 scale-aware 更细的离线审计，不是 production 接入；",
        "- `family_policy_ready=false` 表示当前没有 family 可进入 production A/B；",
        "- 小规模 family 强制 abstain 是为了保护 5/10 不退化；",
        "- 该策略不影响 certificate，也不能证明 no-negative。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-enabled-task-count", type=int, default=20)
    parser.add_argument("--min-family-rows", type=int, default=20)
    parser.add_argument("--min-holdout-rows", type=int, default=2)
    parser.add_argument("--min-train-rows", type=int, default=10)
    parser.add_argument("--min-evaluated-folds", type=int, default=2)
    parser.add_argument("--epochs", type=int, default=500)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--l2", type=float, default=1.0e-4)
    parser.add_argument("--min-precision", type=float, default=0.8)
    parser.add_argument("--max-false-positive-rate", type=float, default=0.05)
    args = parser.parse_args(argv)
    summary = audit_family_policy(
        args.dataset,
        output_dir=args.output_dir,
        report=args.report,
        min_enabled_task_count=args.min_enabled_task_count,
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
                "family_policy_ready": summary["family_policy_ready"],
                "ready_families": summary["ready_families"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

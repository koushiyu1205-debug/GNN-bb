#!/usr/bin/env python3
"""Grid-search diagnostic for kNN-risk CBF delay-queue schedulers.

The grid runs the offline kNN-risk scheduler over several ``k`` /
neighbor-risk / threshold combinations and summarizes which combinations are
scale-safe, family-safe, and still productive.  It is diagnostic-only: no
BPC/pricing/RMP run is triggered and no certificate or official lower bound is
produced.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from BPC_future.scripts.audit_cbf_delay_queue_knn_risk_scheduler import (
    DEFAULT_DATASET,
    audit_knn_risk_scheduler,
)


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/cbf_delay_queue_knn_risk_grid_audit_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_cbf_delay_queue_knn_risk_grid_audit_zh.md"
)


def _parse_int_list(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def _parse_float_list(value: str) -> list[float]:
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def _metric_totals(results: list[dict[str, Any]]) -> dict[str, Any]:
    summaries = [item.get("fold_summary") or {} for item in results]
    return {
        "unsafe_high_priority_fold_count": sum(
            int(summary.get("unsafe_high_priority_fold_count", 0))
            for summary in summaries
        ),
        "total_high_priority_count": sum(
            int(summary.get("total_high_priority_count", 0))
            for summary in summaries
        ),
        "total_delay_queue_count": sum(
            int(summary.get("total_delay_queue_count", 0))
            for summary in summaries
        ),
        "productive_high_priority_fold_count": sum(
            int(summary.get("productive_high_priority_fold_count", 0))
            for summary in summaries
        ),
        "evaluated_count": sum(
            int(summary.get("evaluated_count", 0))
            for summary in summaries
        ),
    }


def _compact_trial(summary: dict[str, Any]) -> dict[str, Any]:
    scale20 = [
        item
        for item in summary.get("scale_results", [])
        if int(item.get("task_count", -1)) == 20
    ]
    family20 = [
        item
        for item in summary.get("family_results", [])
        if int(item.get("task_count", -1)) == 20
    ]
    scale_totals = _metric_totals(scale20)
    family_totals = _metric_totals(family20)
    sector = [
        item for item in family20 if str(item.get("family")) == "sector-wave"
    ]
    sector_totals = _metric_totals(sector)
    return {
        "knn_k": int(summary["knn_k"]),
        "max_neighbor_unsafe_fraction": float(summary["max_neighbor_unsafe_fraction"]),
        "min_high_priority_threshold": float(summary["min_high_priority_threshold"]),
        "scheduler_ready": bool(summary["scheduler_ready"]),
        "scale_scheduler_ready": bool(summary["scale_scheduler_ready"]),
        "family_scheduler_ready": bool(summary["family_scheduler_ready"]),
        "production_candidate_ready": bool(summary["production_candidate_ready"]),
        "ready_task_counts": summary["ready_task_counts"],
        "ready_families": summary["ready_families"],
        "scale20_totals": scale_totals,
        "family20_totals": family_totals,
        "sector_wave_totals": sector_totals,
        "all_checks_pass": bool(summary["all_checks_pass"]),
    }


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CBF Delay-Queue kNN Risk Grid 审计报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "枚举 kNN-risk scheduler 的 `k / neighbor risk / threshold` 组合，寻找",
        "是否存在 family-safe 且仍有 high-priority 的保守区域。该脚本只读 H=2",
        "dataset，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "cbf_delay_queue_knn_risk_grid_audit = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"trial_count = {summary['trial_count']}",
        f"best_production_candidate_ready = {str(summary['best_production_candidate_ready']).lower()}",
        f"best_scale_ready_count = {summary['best_scale_ready_count']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 摘要",
        "",
        "```json",
        json.dumps(
            {
                "trial_count": summary["trial_count"],
                "best_production_candidate_ready": summary["best_production_candidate_ready"],
                "best_scale_ready_count": summary["best_scale_ready_count"],
                "production_candidates": summary["production_candidates"],
                "scale_ready_trials": summary["scale_ready_trials"][:10],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 结论",
        "",
        "- production candidate 必须同时 scale-ready 与 family-ready；",
        "- scale-only ready 只能作为继续补采/建模信号，不能接 production；",
        "- 所有 trial 都保持 delay-queue exactness guard。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def audit_knn_risk_grid(
    dataset: Path,
    *,
    output_dir: Path,
    report: Path,
    k_values: list[int],
    max_neighbor_unsafe_fractions: list[float],
    min_high_priority_thresholds: list[float],
    min_enabled_task_count: int = 20,
    min_scale_rows: int = 30,
    min_family_rows: int = 20,
    min_holdout_rows: int = 2,
    min_train_rows: int = 20,
    min_evaluated_folds: int = 2,
    min_train_high_priority: int = 1,
    epochs: int = 500,
    lr: float = 0.05,
    l2: float = 1.0e-4,
) -> dict[str, Any]:
    trials: list[dict[str, Any]] = []
    trial_summaries: list[dict[str, Any]] = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for k in k_values:
        for max_risk in max_neighbor_unsafe_fractions:
            for threshold in min_high_priority_thresholds:
                trial_dir = (
                    output_dir
                    / f"k{k}_risk{str(max_risk).replace('.', 'p')}_thr{str(threshold).replace('.', 'p')}"
                )
                trial_summary = audit_knn_risk_scheduler(
                    dataset,
                    output_dir=trial_dir,
                    report=trial_dir / "report.md",
                    min_enabled_task_count=min_enabled_task_count,
                    min_scale_rows=min_scale_rows,
                    min_family_rows=min_family_rows,
                    min_holdout_rows=min_holdout_rows,
                    min_train_rows=min_train_rows,
                    min_evaluated_folds=min_evaluated_folds,
                    min_train_high_priority=min_train_high_priority,
                    min_high_priority_threshold=threshold,
                    knn_k=k,
                    max_neighbor_unsafe_fraction=max_risk,
                    epochs=epochs,
                    lr=lr,
                    l2=l2,
                )
                compact = _compact_trial(trial_summary)
                trials.append(compact)
                trial_summaries.append(trial_summary)
    production_candidates = [
        trial for trial in trials if trial["production_candidate_ready"] is True
    ]
    scale_ready_trials = [
        trial for trial in trials if trial["scale_scheduler_ready"] is True
    ]
    scale_ready_trials.sort(
        key=lambda item: (
            int(item["scale20_totals"]["total_high_priority_count"]),
            -int(item["family20_totals"]["unsafe_high_priority_fold_count"]),
        ),
        reverse=True,
    )
    checks = {
        "trial_count_positive": bool(trials),
        "all_trials_no_official_effect": all(
            summary.get("official_bound_effect") is False
            and summary.get("production_ready") is False
            for summary in trial_summaries
        ),
        "all_trials_checks_pass": all(summary.get("all_checks_pass") is True for summary in trial_summaries),
        "delay_queue_exactness_guard_present": all(
            summary.get("gate_can_permanently_discard_negative_columns") is False
            and summary.get("negative_columns_must_remain_eventually_reachable") is True
            and summary.get("finite_delay_required") is True
            for summary in trial_summaries
        ),
    }
    summary = {
        "schema_version": "cbf_delay_queue_knn_risk_grid_audit_v1",
        "status": "cbf_delay_queue_knn_risk_grid_audited",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "dataset": str(dataset),
        "k_values": list(k_values),
        "max_neighbor_unsafe_fractions": list(max_neighbor_unsafe_fractions),
        "min_high_priority_thresholds": list(min_high_priority_thresholds),
        "trial_count": len(trials),
        "trials": trials,
        "production_candidates": production_candidates,
        "best_production_candidate_ready": bool(production_candidates),
        "scale_ready_trials": scale_ready_trials,
        "best_scale_ready_count": len(scale_ready_trials),
        "production_ready": False,
        "official_bound_effect": False,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "goal_complete": False,
    }
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
    parser.add_argument("--k-values", type=_parse_int_list, default=_parse_int_list("1,3,5,7,10"))
    parser.add_argument(
        "--max-neighbor-unsafe-fractions",
        type=_parse_float_list,
        default=_parse_float_list("0.0,0.2"),
    )
    parser.add_argument(
        "--min-high-priority-thresholds",
        type=_parse_float_list,
        default=_parse_float_list("0.8,0.85,0.9,0.95"),
    )
    parser.add_argument("--min-enabled-task-count", type=int, default=20)
    parser.add_argument("--min-scale-rows", type=int, default=30)
    parser.add_argument("--min-family-rows", type=int, default=20)
    parser.add_argument("--min-holdout-rows", type=int, default=2)
    parser.add_argument("--min-train-rows", type=int, default=20)
    parser.add_argument("--min-evaluated-folds", type=int, default=2)
    parser.add_argument("--min-train-high-priority", type=int, default=1)
    parser.add_argument("--epochs", type=int, default=500)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--l2", type=float, default=1.0e-4)
    args = parser.parse_args(argv)
    summary = audit_knn_risk_grid(
        args.dataset,
        output_dir=args.output_dir,
        report=args.report,
        k_values=args.k_values,
        max_neighbor_unsafe_fractions=args.max_neighbor_unsafe_fractions,
        min_high_priority_thresholds=args.min_high_priority_thresholds,
        min_enabled_task_count=args.min_enabled_task_count,
        min_scale_rows=args.min_scale_rows,
        min_family_rows=args.min_family_rows,
        min_holdout_rows=args.min_holdout_rows,
        min_train_rows=args.min_train_rows,
        min_evaluated_folds=args.min_evaluated_folds,
        min_train_high_priority=args.min_train_high_priority,
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
                "trial_count": summary["trial_count"],
                "best_production_candidate_ready": summary["best_production_candidate_ready"],
                "best_scale_ready_count": summary["best_scale_ready_count"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

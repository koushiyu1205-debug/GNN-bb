#!/usr/bin/env python3
"""Grid-search diagnostic for kNN+OOD CBF delay-queue schedulers.

This grid checks whether the first kNN+safe-radius production-candidate signal
is robust to nearby scheduler parameters.  It is diagnostic-only: no
BPC/pricing/RMP run is triggered and no certificate or official lower bound is
produced.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

from BPC_future.scripts.audit_cbf_delay_queue_knn_ood_scheduler import (
    DEFAULT_DATASET,
    audit_knn_ood_scheduler,
)
from BPC_future.scripts.audit_cbf_delay_queue_knn_risk_grid import (
    _metric_totals,
    _parse_float_list,
    _parse_int_list,
)


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/cbf_delay_queue_knn_ood_grid_audit_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_cbf_delay_queue_knn_ood_grid_audit_zh.md"
)


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
    sector = [
        item for item in family20 if str(item.get("family")) == "sector-wave"
    ]
    return {
        "knn_k": int(summary["knn_k"]),
        "max_neighbor_unsafe_fraction": float(summary["max_neighbor_unsafe_fraction"]),
        "min_high_priority_threshold": float(summary["min_high_priority_threshold"]),
        "safe_radius_quantile": float(summary["safe_radius_quantile"]),
        "safe_radius_multiplier": float(summary["safe_radius_multiplier"]),
        "scheduler_ready": bool(summary["scheduler_ready"]),
        "scale_scheduler_ready": bool(summary["scale_scheduler_ready"]),
        "family_scheduler_ready": bool(summary["family_scheduler_ready"]),
        "production_candidate_ready": bool(summary["production_candidate_ready"]),
        "ready_task_counts": summary["ready_task_counts"],
        "ready_families": summary["ready_families"],
        "scale20_totals": _metric_totals(scale20),
        "family20_totals": _metric_totals(family20),
        "sector_wave_totals": _metric_totals(sector),
        "all_checks_pass": bool(summary["all_checks_pass"]),
    }


def _trial_sort_key(trial: dict[str, Any]) -> tuple[int, int, int, int, float, float]:
    return (
        int(trial["production_candidate_ready"]),
        int(trial["scale_scheduler_ready"]),
        int(trial["family_scheduler_ready"]),
        int(trial["sector_wave_totals"]["total_high_priority_count"]),
        -float(trial["safe_radius_multiplier"]),
        -float(trial["min_high_priority_threshold"]),
    )


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CBF Delay-Queue kNN+OOD Grid 审计报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "枚举 kNN+safe-radius OOD scheduler 的参数组合，检查第一个",
        "production-candidate 信号是否是稳健区域，而不是单点参数偶然通过。",
        "该脚本只读 H=2 dataset，不运行 BPC / pricing / RMP，不产生",
        "certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "cbf_delay_queue_knn_ood_grid_audit = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"trial_count = {summary['trial_count']}",
        f"production_candidate_count = {summary['production_candidate_count']}",
        f"robust_candidate_ready = {str(summary['robust_candidate_ready']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 摘要",
        "",
        "```json",
        json.dumps(
            {
                "trial_count": summary["trial_count"],
                "production_candidate_count": summary["production_candidate_count"],
                "robust_candidate_ready": summary["robust_candidate_ready"],
                "best_candidates": summary["production_candidates"][:10],
                "radius_candidate_histogram": summary["radius_candidate_histogram"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 解释",
        "",
        "- production candidate 仍只是离线候选，不等于 production ready；",
        "- robust candidate 要求候选不只出现在一个 safe-radius 参数点；",
        "- 所有 trial 必须保持 delay-queue exactness guard 和 proof-budget guard；",
        "- 下一步仍只能做独立验证或 audit-only smoke，不能接 worker/certificate。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def audit_knn_ood_grid(
    dataset: Path,
    *,
    output_dir: Path,
    report: Path,
    k_values: list[int],
    max_neighbor_unsafe_fractions: list[float],
    min_high_priority_thresholds: list[float],
    safe_radius_quantiles: list[float],
    safe_radius_multipliers: list[float],
    min_enabled_task_count: int = 20,
    min_scale_rows: int = 30,
    min_family_rows: int = 20,
    min_holdout_rows: int = 2,
    min_train_rows: int = 20,
    min_evaluated_folds: int = 2,
    min_train_high_priority: int = 1,
    min_robust_candidate_count: int = 2,
    epochs: int = 500,
    lr: float = 0.05,
    l2: float = 1.0e-4,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    trials: list[dict[str, Any]] = []
    trial_summaries: list[dict[str, Any]] = []
    for k in k_values:
        for max_risk in max_neighbor_unsafe_fractions:
            for threshold in min_high_priority_thresholds:
                for quantile in safe_radius_quantiles:
                    for multiplier in safe_radius_multipliers:
                        trial_dir = (
                            output_dir
                            / f"k{k}_risk{str(max_risk).replace('.', 'p')}"
                            / f"thr{str(threshold).replace('.', 'p')}"
                            / f"q{str(quantile).replace('.', 'p')}_m{str(multiplier).replace('.', 'p')}"
                        )
                        trial_summary = audit_knn_ood_scheduler(
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
                            safe_radius_quantile=quantile,
                            safe_radius_multiplier=multiplier,
                            epochs=epochs,
                            lr=lr,
                            l2=l2,
                        )
                        trials.append(_compact_trial(trial_summary))
                        trial_summaries.append(trial_summary)

    production_candidates = [
        trial for trial in trials if trial["production_candidate_ready"] is True
    ]
    production_candidates.sort(key=_trial_sort_key, reverse=True)
    scale_ready_trials = [
        trial for trial in trials if trial["scale_scheduler_ready"] is True
    ]
    family_ready_trials = [
        trial for trial in trials if trial["family_scheduler_ready"] is True
    ]
    radius_candidate_histogram = dict(
        Counter(
            f"q={trial['safe_radius_quantile']},m={trial['safe_radius_multiplier']}"
            for trial in production_candidates
        )
    )
    robust_candidate_ready = bool(
        len(production_candidates) >= int(min_robust_candidate_count)
        and len(radius_candidate_histogram) >= 2
    )
    checks = {
        "trial_count_positive": bool(trials),
        "all_trials_no_official_effect": all(
            summary.get("official_bound_effect") is False
            and summary.get("production_ready") is False
            for summary in trial_summaries
        ),
        "all_trials_checks_pass": all(
            summary.get("all_checks_pass") is True for summary in trial_summaries
        ),
        "delay_queue_exactness_guard_present": all(
            summary.get("gate_can_permanently_discard_negative_columns") is False
            and summary.get("negative_columns_must_remain_eventually_reachable") is True
            and summary.get("finite_delay_required") is True
            for summary in trial_summaries
        ),
        "delay_queue_proof_budget_guard_present": all(
            summary.get("delay_queue_can_extend_proof_budget") is False
            and summary.get("delay_queue_runs_proof_sweep") is False
            for summary in trial_summaries
        ),
    }
    summary = {
        "schema_version": "cbf_delay_queue_knn_ood_grid_audit_v1",
        "status": "cbf_delay_queue_knn_ood_grid_audited",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "dataset": str(dataset),
        "k_values": list(k_values),
        "max_neighbor_unsafe_fractions": list(max_neighbor_unsafe_fractions),
        "min_high_priority_thresholds": list(min_high_priority_thresholds),
        "safe_radius_quantiles": list(safe_radius_quantiles),
        "safe_radius_multipliers": list(safe_radius_multipliers),
        "min_robust_candidate_count": int(min_robust_candidate_count),
        "trial_count": len(trials),
        "trials": trials,
        "scale_ready_trials": scale_ready_trials,
        "family_ready_trials": family_ready_trials,
        "production_candidates": production_candidates,
        "production_candidate_count": len(production_candidates),
        "radius_candidate_histogram": radius_candidate_histogram,
        "robust_candidate_ready": robust_candidate_ready,
        "production_ready": False,
        "official_bound_effect": False,
        "delay_queue_can_extend_proof_budget": False,
        "delay_queue_runs_proof_sweep": False,
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
    parser.add_argument("--k-values", type=_parse_int_list, default=_parse_int_list("3,5,7"))
    parser.add_argument(
        "--max-neighbor-unsafe-fractions",
        type=_parse_float_list,
        default=_parse_float_list("0.0"),
    )
    parser.add_argument(
        "--min-high-priority-thresholds",
        type=_parse_float_list,
        default=_parse_float_list("0.8,0.85,0.9"),
    )
    parser.add_argument(
        "--safe-radius-quantiles",
        type=_parse_float_list,
        default=_parse_float_list("0.8,0.9,1.0"),
    )
    parser.add_argument(
        "--safe-radius-multipliers",
        type=_parse_float_list,
        default=_parse_float_list("0.75,1.0,1.25"),
    )
    parser.add_argument("--min-enabled-task-count", type=int, default=20)
    parser.add_argument("--min-scale-rows", type=int, default=30)
    parser.add_argument("--min-family-rows", type=int, default=20)
    parser.add_argument("--min-holdout-rows", type=int, default=2)
    parser.add_argument("--min-train-rows", type=int, default=20)
    parser.add_argument("--min-evaluated-folds", type=int, default=2)
    parser.add_argument("--min-train-high-priority", type=int, default=1)
    parser.add_argument("--min-robust-candidate-count", type=int, default=2)
    parser.add_argument("--epochs", type=int, default=500)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--l2", type=float, default=1.0e-4)
    args = parser.parse_args(argv)
    summary = audit_knn_ood_grid(
        args.dataset,
        output_dir=args.output_dir,
        report=args.report,
        k_values=args.k_values,
        max_neighbor_unsafe_fractions=args.max_neighbor_unsafe_fractions,
        min_high_priority_thresholds=args.min_high_priority_thresholds,
        safe_radius_quantiles=args.safe_radius_quantiles,
        safe_radius_multipliers=args.safe_radius_multipliers,
        min_enabled_task_count=args.min_enabled_task_count,
        min_scale_rows=args.min_scale_rows,
        min_family_rows=args.min_family_rows,
        min_holdout_rows=args.min_holdout_rows,
        min_train_rows=args.min_train_rows,
        min_evaluated_folds=args.min_evaluated_folds,
        min_train_high_priority=args.min_train_high_priority,
        min_robust_candidate_count=args.min_robust_candidate_count,
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
                "production_candidate_count": summary["production_candidate_count"],
                "robust_candidate_ready": summary["robust_candidate_ready"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

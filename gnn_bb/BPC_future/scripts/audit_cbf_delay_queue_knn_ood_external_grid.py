#!/usr/bin/env python3
"""Grid-search external validation for kNN+OOD CBF delay schedulers.

Unlike the in-dataset grid, this script fits the scheduler on a train
trajectory dataset and evaluates it on a separate validation dataset.  It is
diagnostic-only: no BPC/pricing/RMP run is triggered and no certificate or
official lower bound is produced.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

from BPC_future.scripts.audit_cbf_delay_queue_knn_ood_external_validation import (
    DEFAULT_TRAIN_DATASET,
    DEFAULT_VALIDATION_DATASET,
    audit_external_validation,
)
from BPC_future.scripts.audit_cbf_delay_queue_knn_risk_grid import (
    _parse_float_list,
    _parse_int_list,
)


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/cbf_delay_queue_knn_ood_external_grid_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_cbf_delay_queue_knn_ood_external_grid_zh.md"
)


def _compact_trial(summary: dict[str, Any]) -> dict[str, Any]:
    overall = (summary.get("validation_metrics") or {}).get("overall") or {}
    by_scale = (summary.get("validation_metrics") or {}).get("by_scale") or {}
    by_family = (summary.get("validation_metrics") or {}).get("by_family") or {}
    return {
        "knn_k": int(summary["knn_k"]),
        "max_neighbor_unsafe_fraction": float(summary["max_neighbor_unsafe_fraction"]),
        "min_high_priority_threshold": float(summary["min_high_priority_threshold"]),
        "safe_radius_quantile": float(summary["safe_radius_quantile"]),
        "safe_radius_multiplier": float(summary["safe_radius_multiplier"]),
        "threshold": summary.get("threshold"),
        "safe_radius": summary.get("safe_radius"),
        "validation_candidate_ready": bool(summary.get("validation_candidate_ready")),
        "validation_overall": overall,
        "validation_by_scale": by_scale,
        "validation_by_family": by_family,
        "all_checks_pass": bool(summary.get("all_checks_pass")),
    }


def _trial_sort_key(trial: dict[str, Any]) -> tuple[int, int, int, float, float]:
    metrics = trial["validation_overall"]
    return (
        int(trial["validation_candidate_ready"]),
        -int(metrics.get("fp", 0)),
        int(metrics.get("predicted_positive", 0)),
        -float(trial["safe_radius_multiplier"]),
        -float(trial["min_high_priority_threshold"]),
    )


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CBF Delay-Queue kNN+OOD External Grid 审计报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "在显式 train / validation 分离下枚举 kNN+OOD scheduler 参数，检查是否存在",
        "zero-FP 且有 high-priority 的外部验证候选。该脚本只读 JSONL，不运行",
        "BPC / pricing / RMP，不生成列，不产生 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "cbf_delay_queue_knn_ood_external_grid = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"trial_count = {summary['trial_count']}",
        f"external_candidate_count = {summary['external_candidate_count']}",
        f"external_candidate_ready = {str(summary['external_candidate_ready']).lower()}",
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
                "external_candidate_count": summary["external_candidate_count"],
                "external_candidate_ready": summary["external_candidate_ready"],
                "best_trials": summary["best_trials"][:10],
                "predicted_positive_histogram": summary["predicted_positive_histogram"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 解释",
        "",
        "- external candidate 仍只是离线验证，不等于 production ready；",
        "- 如果所有 trial predicted_positive=0，则当前 gate 外部验证过度保守；",
        "- 如果任何 trial fp>0，则该参数不安全；",
        "- 所有 trial 都必须保持 delay-queue exactness guard 和 proof-budget guard。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def audit_external_grid(
    train_dataset: Path,
    validation_dataset: Path,
    *,
    output_dir: Path,
    report: Path,
    k_values: list[int],
    max_neighbor_unsafe_fractions: list[float],
    min_high_priority_thresholds: list[float],
    safe_radius_quantiles: list[float],
    safe_radius_multipliers: list[float],
    exclude_train_keys: bool = True,
    min_validation_rows: int = 10,
    min_validation_high_priority: int = 1,
    min_train_high_priority: int = 1,
    min_external_candidate_count: int = 1,
    epochs: int = 500,
    lr: float = 0.05,
    l2: float = 1.0e-4,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    trials: list[dict[str, Any]] = []
    raw_summaries: list[dict[str, Any]] = []
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
                        trial_summary = audit_external_validation(
                            train_dataset,
                            validation_dataset,
                            output_dir=trial_dir,
                            report=trial_dir / "report.md",
                            exclude_train_keys=exclude_train_keys,
                            min_validation_rows=min_validation_rows,
                            min_validation_high_priority=min_validation_high_priority,
                            min_high_priority_threshold=threshold,
                            min_train_high_priority=min_train_high_priority,
                            knn_k=k,
                            max_neighbor_unsafe_fraction=max_risk,
                            safe_radius_quantile=quantile,
                            safe_radius_multiplier=multiplier,
                            epochs=epochs,
                            lr=lr,
                            l2=l2,
                        )
                        raw_summaries.append(trial_summary)
                        trials.append(_compact_trial(trial_summary))

    external_candidates = [
        trial for trial in trials if trial["validation_candidate_ready"] is True
    ]
    best_trials = sorted(trials, key=_trial_sort_key, reverse=True)
    predicted_positive_histogram = dict(
        Counter(
            str(int((trial["validation_overall"] or {}).get("predicted_positive", 0)))
            for trial in trials
        )
    )
    false_positive_histogram = dict(
        Counter(str(int((trial["validation_overall"] or {}).get("fp", 0))) for trial in trials)
    )
    external_candidate_ready = bool(
        len(external_candidates) >= int(min_external_candidate_count)
    )
    checks = {
        "trial_count_positive": bool(trials),
        "all_trials_no_official_effect": all(
            summary.get("official_bound_effect") is False
            and summary.get("production_ready") is False
            for summary in raw_summaries
        ),
        "all_trials_checks_pass": all(summary.get("all_checks_pass") is True for summary in raw_summaries),
        "delay_queue_exactness_guard_present": all(
            summary.get("gate_can_permanently_discard_negative_columns") is False
            and summary.get("negative_columns_must_remain_eventually_reachable") is True
            and summary.get("finite_delay_required") is True
            for summary in raw_summaries
        ),
        "delay_queue_proof_budget_guard_present": all(
            summary.get("delay_queue_can_extend_proof_budget") is False
            and summary.get("delay_queue_runs_proof_sweep") is False
            for summary in raw_summaries
        ),
    }
    summary = {
        "schema_version": "cbf_delay_queue_knn_ood_external_grid_v1",
        "status": "cbf_delay_queue_knn_ood_external_grid_audited",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "train_dataset": str(train_dataset),
        "validation_dataset": str(validation_dataset),
        "exclude_train_keys": bool(exclude_train_keys),
        "k_values": list(k_values),
        "max_neighbor_unsafe_fractions": list(max_neighbor_unsafe_fractions),
        "min_high_priority_thresholds": list(min_high_priority_thresholds),
        "safe_radius_quantiles": list(safe_radius_quantiles),
        "safe_radius_multipliers": list(safe_radius_multipliers),
        "trial_count": len(trials),
        "trials": trials,
        "external_candidates": external_candidates,
        "external_candidate_count": len(external_candidates),
        "external_candidate_ready": external_candidate_ready,
        "best_trials": best_trials,
        "predicted_positive_histogram": predicted_positive_histogram,
        "false_positive_histogram": false_positive_histogram,
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
    parser.add_argument("--train-dataset", type=Path, default=DEFAULT_TRAIN_DATASET)
    parser.add_argument("--validation-dataset", type=Path, default=DEFAULT_VALIDATION_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--include-train-keys", action="store_true")
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
    parser.add_argument("--min-validation-rows", type=int, default=10)
    parser.add_argument("--min-validation-high-priority", type=int, default=1)
    parser.add_argument("--min-train-high-priority", type=int, default=1)
    parser.add_argument("--min-external-candidate-count", type=int, default=1)
    parser.add_argument("--epochs", type=int, default=500)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--l2", type=float, default=1.0e-4)
    args = parser.parse_args(argv)
    summary = audit_external_grid(
        args.train_dataset,
        args.validation_dataset,
        output_dir=args.output_dir,
        report=args.report,
        k_values=args.k_values,
        max_neighbor_unsafe_fractions=args.max_neighbor_unsafe_fractions,
        min_high_priority_thresholds=args.min_high_priority_thresholds,
        safe_radius_quantiles=args.safe_radius_quantiles,
        safe_radius_multipliers=args.safe_radius_multipliers,
        exclude_train_keys=not args.include_train_keys,
        min_validation_rows=args.min_validation_rows,
        min_validation_high_priority=args.min_validation_high_priority,
        min_train_high_priority=args.min_train_high_priority,
        min_external_candidate_count=args.min_external_candidate_count,
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
                "external_candidate_count": summary["external_candidate_count"],
                "external_candidate_ready": summary["external_candidate_ready"],
                "predicted_positive_histogram": summary["predicted_positive_histogram"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

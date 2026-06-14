#!/usr/bin/env python3
"""Validate kNN+OOD CBF delay scheduler on existing capture logs.

This helper composes two read-only steps:

1. build a trajectory-level validation dataset from capture JSONL logs;
2. evaluate a train-dataset-fitted kNN+OOD delay scheduler on that validation
   dataset.

It never runs BPC/pricing/RMP, never generates columns, and never creates
certificates or official lower bounds.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from BPC_future.scripts.audit_cbf_delay_queue_knn_ood_external_validation import (
    DEFAULT_TRAIN_DATASET,
    audit_external_validation,
)
from BPC_future.scripts.build_cbf_trajectory_gate_dataset import build_trajectory_dataset


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/cbf_delay_queue_knn_ood_capture_validation_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_cbf_delay_queue_knn_ood_capture_validation_zh.md"
)


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    validation = summary["external_validation_summary"]
    lines = [
        "# CBF Delay-Queue kNN+OOD Capture Validation 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "把现有 capture JSONL 日志转成 trajectory validation dataset，然后用",
        "训练集拟合的 kNN+OOD delay scheduler 做外部验证。该脚本只读日志，不运行",
        "BPC / pricing / RMP，不生成列，不产生 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "cbf_delay_queue_knn_ood_capture_validation = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"validation_row_count = {summary['validation_row_count']}",
        f"validation_candidate_ready = {str(validation['validation_candidate_ready']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 摘要",
        "",
        "```json",
        json.dumps(
            {
                "capture_paths": summary["capture_paths"],
                "trajectory_dataset": summary["trajectory_dataset"],
                "validation_row_count": summary["validation_row_count"],
                "validation_candidate_ready": validation["validation_candidate_ready"],
                "validation_metrics": validation["validation_metrics"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 解释",
        "",
        "- validation candidate 仍只是只读日志验证，不等于 production ready；",
        "- 如果 predicted_positive=0，说明当前 scheduler 对真实日志过于保守；",
        "- 如果 fp>0，说明 scheduler 不安全，不能接 worker；",
        "- 即使 validation 通过，下一步仍只能做 opt-in audit-only smoke。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def audit_capture_validation(
    train_dataset: Path,
    capture_paths: list[Path],
    *,
    output_dir: Path,
    report: Path,
    horizon_steps: int = 2,
    alpha: float = 0.25,
    v_crit: float = 1.0,
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
    output_dir.mkdir(parents=True, exist_ok=True)
    trajectory_dir = output_dir / "trajectory_validation_dataset"
    validation_report = output_dir / "trajectory_validation_dataset_report.md"
    trajectory_summary = build_trajectory_dataset(
        capture_paths,
        output_dir=trajectory_dir,
        report=validation_report,
        horizon_steps=horizon_steps,
        alpha=alpha,
        v_crit=v_crit,
        min_rows_for_training=1,
    )
    validation_dataset = Path(trajectory_summary["jsonl_path"])
    external_dir = output_dir / "external_validation"
    external_report = output_dir / "external_validation_report.md"
    external_summary = audit_external_validation(
        train_dataset,
        validation_dataset,
        output_dir=external_dir,
        report=external_report,
        exclude_train_keys=exclude_train_keys,
        min_validation_rows=min_validation_rows,
        min_validation_high_priority=min_validation_high_priority,
        min_high_priority_threshold=min_high_priority_threshold,
        min_train_high_priority=min_train_high_priority,
        knn_k=knn_k,
        max_neighbor_unsafe_fraction=max_neighbor_unsafe_fraction,
        safe_radius_quantile=safe_radius_quantile,
        safe_radius_multiplier=safe_radius_multiplier,
        epochs=epochs,
        lr=lr,
        l2=l2,
    )
    checks = {
        "trajectory_dataset_checks_pass": trajectory_summary.get("all_checks_pass") is True,
        "external_validation_checks_pass": external_summary.get("all_checks_pass") is True,
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "no_certificate_effect": external_summary.get("official_bound_effect") is False,
        "delay_queue_proof_budget_guard_present": (
            external_summary.get("delay_queue_can_extend_proof_budget") is False
            and external_summary.get("delay_queue_runs_proof_sweep") is False
        ),
    }
    summary = {
        "schema_version": "cbf_delay_queue_knn_ood_capture_validation_v1",
        "status": "cbf_delay_queue_knn_ood_capture_validation_audited",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "train_dataset": str(train_dataset),
        "capture_paths": [str(path) for path in capture_paths],
        "trajectory_dataset": str(validation_dataset),
        "trajectory_summary": trajectory_summary,
        "external_validation_summary": external_summary,
        "validation_row_count": int(external_summary.get("validation_row_count", 0)),
        "validation_candidate_ready": bool(external_summary.get("validation_candidate_ready")),
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
    parser.add_argument("capture_paths", nargs="+", type=Path)
    parser.add_argument("--train-dataset", type=Path, default=DEFAULT_TRAIN_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--horizon-steps", type=int, default=2)
    parser.add_argument("--alpha", type=float, default=0.25)
    parser.add_argument("--v-crit", type=float, default=1.0)
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
    summary = audit_capture_validation(
        args.train_dataset,
        list(args.capture_paths),
        output_dir=args.output_dir,
        report=args.report,
        horizon_steps=args.horizon_steps,
        alpha=args.alpha,
        v_crit=args.v_crit,
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
                "validation_metrics": summary["external_validation_summary"]["validation_metrics"]["overall"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

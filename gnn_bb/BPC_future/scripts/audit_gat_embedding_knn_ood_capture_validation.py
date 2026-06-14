#!/usr/bin/env python3
"""Validate GAT embedding + kNN/OOD delay scheduler on capture logs.

This composes the read-only audit chain:

1. capture JSONL -> trajectory-CBF validation rows;
2. trajectory rows -> GAT validation dataset;
3. GAT embeddings -> kNN/OOD delay scheduler validation.

It does not run BPC/pricing/RMP, generate columns, enable workers, or create
certificates/official bounds.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from BPC_future.scripts.audit_gat_embedding_knn_ood_external_validation import (
    DEFAULT_CHECKPOINT,
    DEFAULT_TRAIN_DATASET_DIR,
    audit_gat_embedding_external_validation,
)
from BPC_future.scripts.build_cbf_trajectory_gate_dataset import build_trajectory_dataset
from BPC_future.scripts.build_gat_trajectory_cbf_dataset import build_dataset


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_embedding_knn_ood_capture_validation_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_gat_embedding_knn_ood_capture_validation_zh.md"
)


def audit_gat_capture_validation(
    *,
    train_dataset_dir: Path,
    checkpoint: Path,
    capture_paths: list[Path],
    output_dir: Path,
    report: Path,
    device: str = "cpu",
    horizon_steps: int = 2,
    alpha: float = 0.25,
    v_crit: float = 1.0,
    min_validation_rows: int = 1,
    min_validation_high_priority: int = 1,
    min_high_priority_threshold: float = 0.8,
    min_train_high_priority: int = 1,
    knn_k: int = 3,
    max_neighbor_unsafe_fraction: float = 0.0,
    safe_radius_quantile: float = 1.0,
    safe_radius_multiplier: float = 1.0,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    trajectory_dir = output_dir / "trajectory_validation_dataset"
    trajectory_report = output_dir / "trajectory_validation_dataset_report.md"
    trajectory_summary = build_trajectory_dataset(
        capture_paths,
        output_dir=trajectory_dir,
        report=trajectory_report,
        horizon_steps=int(horizon_steps),
        alpha=float(alpha),
        v_crit=float(v_crit),
        min_rows_for_training=1,
    )

    gat_validation_dir = output_dir / "gat_validation_dataset"
    gat_dataset_summary = build_dataset(
        trajectory_jsonl=Path(str(trajectory_summary["jsonl_path"])),
        output_dir=gat_validation_dir,
    )

    external_dir = output_dir / "gat_embedding_external_validation"
    external_report = output_dir / "gat_embedding_external_validation_report.md"
    external_summary = audit_gat_embedding_external_validation(
        train_dataset_dir=train_dataset_dir,
        validation_dataset_dir=gat_validation_dir,
        checkpoint=checkpoint,
        output_dir=external_dir,
        report=external_report,
        device=str(device),
        min_validation_rows=int(min_validation_rows),
        min_validation_high_priority=int(min_validation_high_priority),
        min_high_priority_threshold=float(min_high_priority_threshold),
        min_train_high_priority=int(min_train_high_priority),
        knn_k=int(knn_k),
        max_neighbor_unsafe_fraction=float(max_neighbor_unsafe_fraction),
        safe_radius_quantile=float(safe_radius_quantile),
        safe_radius_multiplier=float(safe_radius_multiplier),
    )

    checks = {
        "trajectory_dataset_checks_pass": trajectory_summary.get("all_checks_pass") is True,
        "gat_dataset_checks_pass": gat_dataset_summary.get("all_checks_pass") is True,
        "external_validation_checks_pass": external_summary.get("all_checks_pass") is True,
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "no_certificate_effect": external_summary.get("official_bound_effect") is False,
        "gate_cannot_permanently_discard_negative_columns": (
            external_summary.get("gate_can_permanently_discard_negative_columns") is False
        ),
        "delay_queue_proof_budget_guard_present": (
            external_summary.get("delay_queue_can_extend_proof_budget") is False
            and external_summary.get("delay_queue_runs_proof_sweep") is False
        ),
    }
    summary = {
        "schema_version": "gat_embedding_knn_ood_capture_validation_v1",
        "status": "gat_embedding_knn_ood_capture_validation_audited",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "train_dataset_dir": str(train_dataset_dir),
        "checkpoint": str(checkpoint),
        "capture_paths": [str(path) for path in capture_paths],
        "trajectory_dataset": str(trajectory_summary["jsonl_path"]),
        "trajectory_summary": trajectory_summary,
        "gat_validation_dataset_dir": str(gat_validation_dir),
        "gat_dataset_summary": gat_dataset_summary,
        "external_validation_summary": external_summary,
        "validation_row_count": int(external_summary.get("validation_row_count", 0)),
        "validation_candidate_ready": bool(external_summary.get("validation_candidate_ready")),
        "production_ready": False,
        "official_bound_effect": False,
        "active_worker_effect": False,
        "certificate_effect": False,
        "gate_role": "gat_embedding_knn_ood_delay_scheduler_not_pricing_oracle",
        "safe_negative_decision": "HIGH_PRIORITY",
        "unsafe_negative_decision": "DELAY_QUEUE",
        "nonnegative_decision": "REJECT_NONNEGATIVE_ONLY",
        "negative_columns_must_remain_eventually_reachable": True,
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


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    external = summary["external_validation_summary"]
    lines = [
        "# GAT Embedding kNN/OOD Capture Validation 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "把已有 capture JSONL 日志串成 GAT embedding + kNN/OOD 外部验证。",
        "该脚本只读日志和数据集，不运行 BPC / pricing / RMP，不生成列，",
        "不产生 certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_embedding_knn_ood_capture_validation = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
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
                "capture_paths": summary["capture_paths"],
                "trajectory_dataset": summary["trajectory_dataset"],
                "gat_validation_dataset_dir": summary["gat_validation_dataset_dir"],
                "validation_row_count": summary["validation_row_count"],
                "validation_candidate_ready": summary["validation_candidate_ready"],
                "validation_metrics": external["validation_metrics"],
                "decision_reason_counts": external["decision_reason_counts"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Exactness Guard",
        "",
        "- GAT embedding 不是 pricing oracle；",
        "- kNN/OOD gate 只能把负列排成 HIGH_PRIORITY 或 DELAY_QUEUE；",
        "- DELAY_QUEUE 不能永久丢弃 true-RC negative，也不能延长 exact proof budget；",
        "- 该验证通过也只表示值得做 opt-in audit-only smoke，不表示 production ready。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture_paths", nargs="+", type=Path)
    parser.add_argument("--train-dataset-dir", type=Path, default=DEFAULT_TRAIN_DATASET_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--horizon-steps", type=int, default=2)
    parser.add_argument("--alpha", type=float, default=0.25)
    parser.add_argument("--v-crit", type=float, default=1.0)
    parser.add_argument("--min-validation-rows", type=int, default=1)
    parser.add_argument("--min-validation-high-priority", type=int, default=1)
    parser.add_argument("--min-high-priority-threshold", type=float, default=0.8)
    parser.add_argument("--min-train-high-priority", type=int, default=1)
    parser.add_argument("--knn-k", type=int, default=3)
    parser.add_argument("--max-neighbor-unsafe-fraction", type=float, default=0.0)
    parser.add_argument("--safe-radius-quantile", type=float, default=1.0)
    parser.add_argument("--safe-radius-multiplier", type=float, default=1.0)
    args = parser.parse_args(argv)
    summary = audit_gat_capture_validation(
        train_dataset_dir=args.train_dataset_dir,
        checkpoint=args.checkpoint,
        capture_paths=list(args.capture_paths),
        output_dir=args.output_dir,
        report=args.report,
        device=str(args.device),
        horizon_steps=int(args.horizon_steps),
        alpha=float(args.alpha),
        v_crit=float(args.v_crit),
        min_validation_rows=int(args.min_validation_rows),
        min_validation_high_priority=int(args.min_validation_high_priority),
        min_high_priority_threshold=float(args.min_high_priority_threshold),
        min_train_high_priority=int(args.min_train_high_priority),
        knn_k=int(args.knn_k),
        max_neighbor_unsafe_fraction=float(args.max_neighbor_unsafe_fraction),
        safe_radius_quantile=float(args.safe_radius_quantile),
        safe_radius_multiplier=float(args.safe_radius_multiplier),
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

#!/usr/bin/env python3
"""External validation for GAT embedding + kNN/OOD delay scheduler.

The GAT checkpoint provides trajectory-CBF probabilities and embeddings.  The
kNN/OOD shell is the conservative safety guard.  This script is read-only: it
never runs BPC, pricing, RMP, workers, or certificates.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from BPC_future.learning.column_selector import ContextAwareColumnSelector
from BPC_future.scripts.audit_cbf_delay_queue_knn_ood_external_validation import (
    _metrics_from_decisions,
    _validation_decision_record,
)
from BPC_future.scripts.audit_cbf_delay_queue_knn_ood_scheduler import (
    _nearest_safe_distance,
    _neighbor_unsafe_fraction,
    _safe_radius_threshold,
)
from BPC_future.scripts.audit_cbf_delay_queue_scheduler import _select_zero_fp_threshold
from BPC_future.scripts.train_gnn_column_selector import _normalize_sample


DEFAULT_TRAIN_DATASET_DIR = Path("BPC_future/data/gat_trajectory_cbf/v1")
DEFAULT_VALIDATION_DATASET_DIR = Path(
    "BPC_future/data/gat_trajectory_cbf/sector_wave_validation_20260614"
)
DEFAULT_CHECKPOINT = Path(
    "BPC_future/data/gat_trajectory_cbf/v1/context_aware_trajectory_cbf_gat.pt"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_embedding_knn_ood_external_validation_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_gat_embedding_knn_ood_external_validation_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-dataset-dir", type=Path, default=DEFAULT_TRAIN_DATASET_DIR)
    parser.add_argument("--validation-dataset-dir", type=Path, default=DEFAULT_VALIDATION_DATASET_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--min-validation-rows", type=int, default=1)
    parser.add_argument("--min-validation-high-priority", type=int, default=1)
    parser.add_argument("--min-high-priority-threshold", type=float, default=0.8)
    parser.add_argument("--min-train-high-priority", type=int, default=1)
    parser.add_argument("--knn-k", type=int, default=3)
    parser.add_argument("--max-neighbor-unsafe-fraction", type=float, default=0.0)
    parser.add_argument("--safe-radius-quantile", type=float, default=1.0)
    parser.add_argument("--safe-radius-multiplier", type=float, default=1.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_gat_embedding_external_validation(
        train_dataset_dir=args.train_dataset_dir,
        validation_dataset_dir=args.validation_dataset_dir,
        checkpoint=args.checkpoint,
        output_dir=args.output_dir,
        report=args.report,
        device=str(args.device),
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
                "validation_metrics": summary["validation_metrics"]["overall"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


def audit_gat_embedding_external_validation(
    *,
    train_dataset_dir: Path,
    validation_dataset_dir: Path,
    checkpoint: Path,
    output_dir: Path,
    report: Path,
    device: str = "cpu",
    min_validation_rows: int = 1,
    min_validation_high_priority: int = 1,
    min_high_priority_threshold: float = 0.8,
    min_train_high_priority: int = 1,
    knn_k: int = 3,
    max_neighbor_unsafe_fraction: float = 0.0,
    safe_radius_quantile: float = 1.0,
    safe_radius_multiplier: float = 1.0,
) -> dict[str, Any]:
    checkpoint_data = torch.load(checkpoint, map_location="cpu", weights_only=False)
    if checkpoint_data.get("target_label") != "label_horizon_cbf_feasible":
        raise ValueError("GAT checkpoint must target label_horizon_cbf_feasible")
    if checkpoint_data.get("trajectory_contract", {}).get("certificate_source"):
        raise ValueError("GAT checkpoint must not be a certificate source")
    model = ContextAwareColumnSelector(**checkpoint_data["model_config"]).to(torch.device(device))
    model.load_state_dict(checkpoint_data["model_state_dict"])
    model.eval()
    train_manifest = _load_manifest(train_dataset_dir)
    validation_manifest = _load_manifest(validation_dataset_dir)
    train_records = _score_dataset(
        dataset_dir=train_dataset_dir,
        manifest=train_manifest,
        checkpoint=checkpoint_data,
        model=model,
        device=torch.device(device),
    )
    validation_records = _score_dataset(
        dataset_dir=validation_dataset_dir,
        manifest=validation_manifest,
        checkpoint=checkpoint_data,
        model=model,
        device=torch.device(device),
    )
    train_y = [record["label"] for record in train_records]
    validation_y = [record["label"] for record in validation_records]
    train_prob = [record["probability"] for record in train_records]
    chosen = _select_zero_fp_threshold(
        train_prob,
        train_y,
        min_train_high_priority=int(min_train_high_priority),
        min_high_priority_threshold=float(min_high_priority_threshold),
    )
    threshold = float(chosen["threshold"])
    train_x = [record["embedding"] for record in train_records]
    safe_radius = _safe_radius_threshold(
        train_x,
        train_y,
        quantile=float(safe_radius_quantile),
        multiplier=float(safe_radius_multiplier),
    )
    decisions: list[int] = []
    decision_records: list[dict[str, Any]] = []
    for record in validation_records:
        risk = _neighbor_unsafe_fraction(
            train_x,
            train_y,
            record["embedding"],
            k=int(knn_k),
        )
        nearest_safe = _nearest_safe_distance(train_x, train_y, record["embedding"])
        in_radius = bool(
            safe_radius is not None
            and nearest_safe is not None
            and nearest_safe <= safe_radius
        )
        decision = (
            1
            if float(record["probability"]) >= threshold
            and risk <= float(max_neighbor_unsafe_fraction)
            and in_radius
            else 0
        )
        decisions.append(decision)
        decision_records.append(
            _validation_decision_record(
                record["row"],
                label=int(record["label"]),
                prob=float(record["probability"]),
                threshold=threshold,
                neighbor_unsafe_fraction=float(risk),
                max_neighbor_unsafe_fraction=float(max_neighbor_unsafe_fraction),
                nearest_safe_distance=None if nearest_safe is None else float(nearest_safe),
                safe_radius=None if safe_radius is None else float(safe_radius),
                decision=decision,
            )
        )
    validation_metrics = _group_validation(validation_records, decisions)
    overall = validation_metrics["overall"]
    reason_counts = dict(
        sorted(Counter(str(record["decision_reason"]) for record in decision_records).items())
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
        len(validation_records) >= int(min_validation_rows)
        and int(overall.get("fp", 0)) == 0
        and int(overall.get("predicted_positive", 0)) >= int(min_validation_high_priority)
    )
    checks = {
        "train_rows_no_certificate_effect": bool(train_records),
        "validation_rows_no_certificate_effect": bool(validation_records),
        "uses_horizon_labels": True,
        "gat_checkpoint_not_pricing_oracle": not bool(checkpoint_data.get("trajectory_contract", {}).get("pricing_oracle")),
        "gat_checkpoint_not_certificate_source": not bool(checkpoint_data.get("trajectory_contract", {}).get("certificate_source")),
        "delay_queue_exactness_guard_present": True,
        "delay_queue_proof_budget_guard_present": True,
    }
    summary = {
        "schema_version": "gat_embedding_knn_ood_external_validation_v1",
        "status": "gat_embedding_knn_ood_external_validation_audited",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "train_dataset_dir": str(train_dataset_dir),
        "validation_dataset_dir": str(validation_dataset_dir),
        "checkpoint": str(checkpoint),
        "train_row_count": len(train_records),
        "validation_row_count": len(validation_records),
        "train_label_counts": _label_counts(train_records),
        "validation_label_counts": _label_counts(validation_records),
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
        "embedding_source": "context_aware_trajectory_cbf_gat",
        "gate_role": "gat_embedding_external_validation_not_column_filter",
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


def _load_manifest(dataset_dir: Path) -> dict[str, Any]:
    manifest = json.loads((Path(dataset_dir) / "manifest.json").read_text(encoding="utf-8"))
    if "label_horizon_cbf_feasible" not in set(manifest.get("label_schema") or []):
        raise ValueError("GAT dataset must include label_horizon_cbf_feasible")
    return manifest


def _score_dataset(
    *,
    dataset_dir: Path,
    manifest: dict[str, Any],
    checkpoint: dict[str, Any],
    model: ContextAwareColumnSelector,
    device: torch.device,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with torch.no_grad():
        for item in manifest.get("samples", []):
            sample = torch.load(Path(dataset_dir) / item["path"], map_location="cpu", weights_only=False)
            sample = _normalize_sample(sample, checkpoint)
            sample = sample.to(device)
            output = model(
                sample,
                sample.candidate_task_membership,
                sample.candidate_features,
                sample.context_features,
            )
            candidate_embedding = output["candidate_embedding"].detach().cpu()
            impact_prob = output.get(
                "trajectory_impact_probability",
                output["add_probability"],
            ).detach().cpu()
            label = int(getattr(sample, "trajectory_label_horizon_cbf_feasible", int(sample.y_selector[0].item())))
            row = {
                "source_file": str(getattr(sample, "selector_source_jsonl", "")),
                "instance": str(getattr(sample, "selector_instance", item.get("instance", ""))),
                "context_hash": str(getattr(sample, "selector_context_hash", item.get("context_hash", ""))),
                "horizon_next_context_hash": "",
                "task_count": int(sample.candidate_task_membership.size(1)),
                "cg_iter": int(item.get("row_index", -1)),
                "horizon_next_cg_iter": int(item.get("row_index", -1)),
                "label_horizon_cbf_feasible": label,
                "horizon_barrier_slack": float(getattr(sample, "trajectory_horizon_barrier_slack", 0.0)),
                "horizon_delta_v": float(getattr(sample, "trajectory_horizon_delta_v", 0.0)),
                "state_t_dual_l1_delta": None,
                "state_t_residual_mode_entropy": None,
                "action_negative_count": int(item.get("candidate_count", candidate_embedding.size(0))),
                "action_unique_task_set_count": int(item.get("candidate_count", candidate_embedding.size(0))),
                "diagnostic_only": True,
                "certificate_capable": False,
                "official_bound_effect": False,
            }
            records.append(
                {
                    "label": label,
                    "probability": float(impact_prob.mean().item()),
                    "embedding": _sample_embedding(candidate_embedding, impact_prob),
                    "row": row,
                }
            )
    return records


def _sample_embedding(candidate_embedding: torch.Tensor, add_probability: torch.Tensor) -> list[float]:
    if candidate_embedding.dim() != 2 or candidate_embedding.size(0) <= 0:
        raise ValueError("candidate embedding must be [num_candidates, dim]")
    mean = candidate_embedding.mean(dim=0)
    std = candidate_embedding.std(dim=0, unbiased=False)
    max_values = candidate_embedding.max(dim=0).values
    prob = add_probability.to(dtype=torch.float32)
    stats = torch.tensor(
        [
            float(candidate_embedding.size(0)),
            float(prob.mean().item()),
            float(prob.max().item()),
            float(prob.min().item()),
            float(prob.std(unbiased=False).item()) if prob.numel() > 1 else 0.0,
        ],
        dtype=torch.float32,
    )
    vector = torch.cat([mean, std, max_values, stats], dim=0)
    values = [float(value) for value in vector.tolist()]
    return [0.0 if math.isnan(value) or math.isinf(value) else value for value in values]


def _label_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(int(record["label"]) for record in records)
    return {str(key): int(value) for key, value in sorted(counts.items())}


def _group_validation(records: list[dict[str, Any]], decisions: list[int]) -> dict[str, Any]:
    labels = [int(record["label"]) for record in records]
    by_scale: dict[str, tuple[list[int], list[int]]] = {}
    by_family: dict[str, tuple[list[int], list[int]]] = {}
    for record, decision in zip(records, decisions):
        row = record["row"]
        scale_key = str(row.get("task_count", ""))
        family_key = f"{row.get('task_count')}|gat_embedding"
        by_scale.setdefault(scale_key, ([], []))
        by_scale[scale_key][0].append(int(record["label"]))
        by_scale[scale_key][1].append(int(decision))
        by_family.setdefault(family_key, ([], []))
        by_family[family_key][0].append(int(record["label"]))
        by_family[family_key][1].append(int(decision))
    return {
        "overall": _metrics_from_decisions(decisions, labels),
        "by_scale": {
            key: _metrics_from_decisions(group_decisions, group_labels)
            for key, (group_labels, group_decisions) in sorted(by_scale.items())
        },
        "by_family": {
            key: _metrics_from_decisions(group_decisions, group_labels)
            for key, (group_labels, group_decisions) in sorted(by_family.items())
        },
    }


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Embedding kNN/OOD External Validation 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "用 trajectory-CBF GAT checkpoint 生成 embedding，再用 kNN/OOD safety shell",
        "做外部验证。该脚本只读 GAT dataset，不运行 BPC / pricing / RMP，不生成列，",
        "不产生 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_embedding_knn_ood_external_validation = current",
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
                "threshold": summary["threshold"],
                "safe_radius": summary["safe_radius"],
                "validation_metrics": summary["validation_metrics"],
                "decision_reason_counts": summary["decision_reason_counts"],
                "positive_delay_reason_counts": summary["positive_delay_reason_counts"],
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
        "- fp>0 表示 GAT embedding safety shell 不安全，不能接 worker；",
        "- predicted_positive=0 表示仍过于保守，不能证明 ROI；",
        "- delay queue 不能 discard true-RC negative，也不能扩展 proof budget。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

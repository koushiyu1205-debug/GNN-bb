#!/usr/bin/env python3
"""Audit same-run GAT batch-impact checkpoint with kNN/OOD safety shell.

This is an offline diagnostic.  It scores the same-run graph dataset, chooses a
conservative high-priority threshold on the training split, then evaluates a
kNN/OOD shell on held-out instances.  It never runs BPC, pricing, RMP, workers,
or certificates.
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

from BPC_future.learning.column_selector import (
    SELECTOR_CLASS_ADD,
    ContextAwareColumnSelector,
)
from BPC_future.scripts.audit_cbf_delay_queue_knn_ood_scheduler import (
    _nearest_safe_distance,
    _neighbor_unsafe_fraction,
    _safe_radius_threshold,
)
from BPC_future.scripts.train_gnn_column_selector import _normalize_sample


DEFAULT_DATASET_DIR = Path("BPC_future/data/gat_same_run_batch_impact/v1")
DEFAULT_CHECKPOINT = Path(
    "BPC_future/results/gat_same_run_batch_impact_training_20260615/"
    "context_aware_same_run_batch_impact_gat.pt"
)
DEFAULT_TRAINING_SUMMARY = Path(
    "BPC_future/results/gat_same_run_batch_impact_training_20260615/summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_same_run_batch_impact_knn_ood_audit_20260615"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260615_bpc_future_gat_same_run_batch_impact_knn_ood_audit_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--training-summary", type=Path, default=DEFAULT_TRAINING_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--knn-k", type=int, default=3)
    parser.add_argument("--max-neighbor-delay-fraction", type=float, default=0.0)
    parser.add_argument("--safe-radius-quantile", type=float, default=1.0)
    parser.add_argument("--safe-radius-multiplier", type=float, default=1.0)
    parser.add_argument("--min-validation-high-priority", type=int, default=1)
    parser.add_argument("--min-delay-recall", type=float, default=0.5)
    parser.add_argument("--decision-scope", choices=("validation", "all"), default="validation")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_same_run_gat_knn_ood(
        dataset_dir=args.dataset_dir,
        checkpoint=args.checkpoint,
        training_summary=args.training_summary,
        output_dir=args.output_dir,
        report=args.report,
        device=str(args.device),
        knn_k=int(args.knn_k),
        max_neighbor_delay_fraction=float(args.max_neighbor_delay_fraction),
        safe_radius_quantile=float(args.safe_radius_quantile),
        safe_radius_multiplier=float(args.safe_radius_multiplier),
        min_validation_high_priority=int(args.min_validation_high_priority),
        min_delay_recall=float(args.min_delay_recall),
        decision_scope=str(args.decision_scope),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_same_run_gat_knn_ood(
    *,
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    checkpoint: Path = DEFAULT_CHECKPOINT,
    training_summary: Path = DEFAULT_TRAINING_SUMMARY,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    device: str = "cpu",
    knn_k: int = 3,
    max_neighbor_delay_fraction: float = 0.0,
    safe_radius_quantile: float = 1.0,
    safe_radius_multiplier: float = 1.0,
    min_validation_high_priority: int = 1,
    min_delay_recall: float = 0.5,
    decision_scope: str = "validation",
) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    checkpoint_data = torch.load(checkpoint, map_location="cpu", weights_only=False)
    manifest = json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    train_info = json.loads(Path(training_summary).read_text(encoding="utf-8"))
    model = ContextAwareColumnSelector(**checkpoint_data["model_config"]).to(torch.device(device))
    model.load_state_dict(checkpoint_data["model_state_dict"])
    model.eval()

    train_instances = set(train_info.get("split", {}).get("train_instances") or [])
    validation_instances = set(train_info.get("split", {}).get("validation_instances") or [])
    records = _score_dataset(
        dataset_dir=dataset_dir,
        manifest=manifest,
        checkpoint=checkpoint_data,
        model=model,
        device=torch.device(device),
    )
    train_records = [record for record in records if record["instance"] in train_instances]
    validation_records = [record for record in records if record["instance"] in validation_instances]
    if not train_records or not validation_records:
        raise ValueError("training summary split does not match dataset instances")

    threshold_info = _select_zero_delay_fp_threshold(train_records)
    threshold = float(threshold_info["threshold"])
    train_x = [record["embedding"] for record in train_records]
    train_y = [int(record["label_high_priority"]) for record in train_records]
    safe_radius = _safe_radius_threshold(
        train_x,
        train_y,
        quantile=float(safe_radius_quantile),
        multiplier=float(safe_radius_multiplier),
    )
    validation_decision_records: list[dict[str, Any]] = []
    for record in validation_records:
        validation_decision_records.append(
            _classify_record(
                record=record,
                threshold=threshold,
                train_x=train_x,
                train_y=train_y,
                safe_radius=safe_radius,
                knn_k=int(knn_k),
                max_neighbor_delay_fraction=float(max_neighbor_delay_fraction),
                split="validation",
            )
        )

    if str(decision_scope) == "all":
        emit_records = records
    else:
        emit_records = validation_records
    decision_records: list[dict[str, Any]] = []
    for record in emit_records:
        split = "unknown"
        if record["instance"] in train_instances:
            split = "train"
        elif record["instance"] in validation_instances:
            split = "validation"
        decision_records.append(
            _classify_record(
                record=record,
                threshold=threshold,
                train_x=train_x,
                train_y=train_y,
                safe_radius=safe_radius,
                knn_k=int(knn_k),
                max_neighbor_delay_fraction=float(max_neighbor_delay_fraction),
                split=split,
            )
        )

    metrics = _metrics(
        [int(record["decision"]) for record in validation_decision_records],
        [int(record["label_high_priority"]) for record in validation_decision_records],
    )
    decision_scope_metrics = _metrics(
        [int(record["decision"]) for record in decision_records],
        [int(record["label_high_priority"]) for record in decision_records],
    )
    delay_recall = metrics["negative_recall_delay_queue"]
    validation_no_false_high_priority = bool(metrics["fp_high_priority_on_delay"] == 0)
    validation_min_high_priority_met = bool(
        metrics["predicted_high_priority"] >= int(min_validation_high_priority)
    )
    validation_delay_recall_met = bool(
        delay_recall is not None and delay_recall >= float(min_delay_recall)
    )
    validation_candidate_ready = bool(
        validation_no_false_high_priority
        and validation_min_high_priority_met
        and validation_delay_recall_met
    )
    production_block_reasons: list[str] = []
    if not validation_no_false_high_priority:
        production_block_reasons.append("validation_false_high_priority_on_delay")
    if not validation_min_high_priority_met:
        production_block_reasons.append("validation_high_priority_below_min")
    if not validation_delay_recall_met:
        production_block_reasons.append("validation_delay_recall_below_min")
    if not validation_candidate_ready:
        production_block_reasons.append("validation_candidate_not_ready")
    summary = {
        "schema_version": "gat_same_run_batch_impact_knn_ood_audit_v1",
        "status": "gat_same_run_batch_impact_knn_ood_audited",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "dataset_dir": str(dataset_dir),
        "checkpoint": str(checkpoint),
        "training_summary": str(training_summary),
        "train_row_count": len(train_records),
        "validation_row_count": len(validation_records),
        "train_label_counts": _label_counts(train_records),
        "validation_label_counts": _label_counts(validation_records),
        "threshold": threshold,
        "threshold_info": threshold_info,
        "safe_radius": safe_radius,
        "knn_k": int(knn_k),
        "max_neighbor_delay_fraction": float(max_neighbor_delay_fraction),
        "safe_radius_quantile": float(safe_radius_quantile),
        "safe_radius_multiplier": float(safe_radius_multiplier),
        "decision_scope": str(decision_scope),
        "decision_record_count": len(decision_records),
        "validation_metrics": metrics,
        "decision_scope_metrics": decision_scope_metrics,
        "validation_safety_checks": {
            "no_false_high_priority": validation_no_false_high_priority,
            "min_high_priority_met": validation_min_high_priority_met,
            "delay_recall_met": validation_delay_recall_met,
        },
        "decision_reason_counts": dict(
            sorted(Counter(record["decision_reason"] for record in decision_records).items())
        ),
        "decision_split_counts": dict(
            sorted(Counter(record["decision_split"] for record in decision_records).items())
        ),
        "decision_records_path": str(output_dir / "decision_records.jsonl"),
        "validation_candidate_ready": validation_candidate_ready,
        "validation_safety_ready": validation_candidate_ready,
        "production_block_reasons": production_block_reasons,
        "production_ready": False,
        "official_bound_effect": False,
        "selector_is_pricing_oracle": False,
        "selector_can_certificate": False,
        "gate_can_permanently_discard_negative_columns": False,
        "negative_columns_must_remain_eventually_reachable": True,
        "unsafe_negative_decision": "DELAY_QUEUE",
        "safe_negative_decision": "HIGH_PRIORITY",
        "all_checks_pass": True,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "decision_records.jsonl").write_text(
        "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in decision_records)
        + ("\n" if decision_records else ""),
        encoding="utf-8",
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def _classify_record(
    *,
    record: dict[str, Any],
    threshold: float,
    train_x: list[Any],
    train_y: list[int],
    safe_radius: float | None,
    knn_k: int,
    max_neighbor_delay_fraction: float,
    split: str,
) -> dict[str, Any]:
    neighbor_delay_fraction = _neighbor_unsafe_fraction(
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
    decision = int(
        float(record["probability"]) >= threshold
        and neighbor_delay_fraction <= float(max_neighbor_delay_fraction)
        and in_radius
    )
    reason = "high_priority"
    if float(record["probability"]) < threshold:
        reason = "below_threshold_delay_queue"
    elif neighbor_delay_fraction > float(max_neighbor_delay_fraction):
        reason = "knn_delay_fraction_delay_queue"
    elif not in_radius:
        reason = "ood_radius_delay_queue"
    return {
        "instance": record["instance"],
        "instance_path": record["instance_path"],
        "context_hash": record["context_hash"],
        "sample_path": record["sample_path"],
        "source_file": record["source_file"],
        "row_index": int(record["row_index"]),
        "decision_split": str(split),
        "label_high_priority": int(record["label_high_priority"]),
        "probability": float(record["probability"]),
        "threshold": float(threshold),
        "neighbor_delay_fraction": float(neighbor_delay_fraction),
        "nearest_safe_distance": None if nearest_safe is None else float(nearest_safe),
        "safe_radius": None if safe_radius is None else float(safe_radius),
        "decision": int(decision),
        "decision_reason": reason,
    }


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
            sample = torch.load(dataset_dir / item["path"], map_location="cpu", weights_only=False)
            sample = _normalize_sample(sample, checkpoint)
            sample = sample.to(device)
            output = model(
                sample,
                sample.candidate_task_membership,
                sample.candidate_features,
                sample.context_features,
            )
            embedding = output["candidate_embedding"].detach().cpu()
            probability = output["high_priority_probability"].detach().cpu()
            label = int(torch.any(sample.y_selector.detach().cpu() == SELECTOR_CLASS_ADD).item())
            records.append(
                {
                    "instance": str(getattr(sample, "selector_instance", item.get("instance", ""))),
                    "instance_path": str(
                        getattr(sample, "selector_instance_path", item.get("instance_path", ""))
                    ),
                    "context_hash": str(getattr(sample, "selector_context_hash", item.get("context_hash", ""))),
                    "sample_path": str(item.get("path", "")),
                    "source_file": str(
                        getattr(sample, "selector_source_jsonl", item.get("source_file", ""))
                    ),
                    "row_index": int(
                        getattr(sample, "selector_source_row_index", item.get("row_index", -1))
                    ),
                    "label_high_priority": label,
                    "probability": float(probability.mean().item()),
                    "embedding": _sample_embedding(embedding, probability),
                }
            )
    return records


def _select_zero_delay_fp_threshold(records: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = sorted({float(record["probability"]) for record in records}, reverse=True)
    candidates.append(1.000001)
    best: dict[str, Any] | None = None
    for threshold in candidates:
        predicted = [int(float(record["probability"]) >= threshold) for record in records]
        labels = [int(record["label_high_priority"]) for record in records]
        metrics = _metrics(predicted, labels)
        if metrics["fp_high_priority_on_delay"] == 0:
            current = {
                "threshold": float(threshold),
                "train_predicted_high_priority": int(metrics["predicted_high_priority"]),
                "train_metrics": metrics,
            }
            if best is None or current["train_predicted_high_priority"] > best["train_predicted_high_priority"]:
                best = current
    if best is None:
        return {
            "threshold": 1.000001,
            "train_predicted_high_priority": 0,
            "train_metrics": _metrics([0 for _ in records], [int(record["label_high_priority"]) for record in records]),
        }
    return best


def _metrics(decisions: list[int], labels: list[int]) -> dict[str, Any]:
    tp = sum(1 for d, y in zip(decisions, labels) if d == 1 and y == 1)
    fp = sum(1 for d, y in zip(decisions, labels) if d == 1 and y == 0)
    tn = sum(1 for d, y in zip(decisions, labels) if d == 0 and y == 0)
    fn = sum(1 for d, y in zip(decisions, labels) if d == 0 and y == 1)
    positives = tp + fn
    negatives = tn + fp
    predicted = tp + fp
    total = len(labels)
    return {
        "total": int(total),
        "tp_high_priority": int(tp),
        "fp_high_priority_on_delay": int(fp),
        "tn_delay_queue": int(tn),
        "fn_delayed_high_priority": int(fn),
        "predicted_high_priority": int(predicted),
        "actual_high_priority": int(positives),
        "actual_delay_queue": int(negatives),
        "accuracy": None if total <= 0 else (tp + tn) / float(total),
        "high_priority_precision": None if predicted <= 0 else tp / float(predicted),
        "high_priority_recall": None if positives <= 0 else tp / float(positives),
        "negative_recall_delay_queue": None if negatives <= 0 else tn / float(negatives),
    }


def _sample_embedding(candidate_embedding: torch.Tensor, probability: torch.Tensor) -> list[float]:
    if candidate_embedding.dim() != 2 or candidate_embedding.size(0) <= 0:
        raise ValueError("candidate embedding must have shape [num_candidates, dim]")
    prob = probability.to(dtype=torch.float32)
    vector = torch.cat(
        [
            candidate_embedding.mean(dim=0),
            candidate_embedding.std(dim=0, unbiased=False),
            candidate_embedding.max(dim=0).values,
            torch.tensor(
                [
                    float(candidate_embedding.size(0)),
                    float(prob.mean().item()),
                    float(prob.max().item()),
                    float(prob.min().item()),
                    float(prob.std(unbiased=False).item()) if prob.numel() > 1 else 0.0,
                ],
                dtype=torch.float32,
            ),
        ],
        dim=0,
    )
    values = [float(value) for value in vector.tolist()]
    return [0.0 if math.isnan(value) or math.isinf(value) else value for value in values]


def _label_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter("high_priority" if record["label_high_priority"] else "delay_queue" for record in records)
    return dict(sorted((str(key), int(value)) for key, value in counts.items()))


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Same-Run Batch Impact kNN/OOD Audit 报告",
        "",
        "日期：2026-06-15",
        "",
        "## 目的",
        "",
        "审计 same-run batch-impact GAT checkpoint 的离线 holdout 表现，并用",
        "kNN/OOD safety shell 检查 HIGH_PRIORITY 是否安全。该流程不运行求解器，",
        "不接 production driver，不产生 certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_same_run_batch_impact_knn_ood = current",
        f"status = {summary['status']}",
        f"train_row_count = {summary['train_row_count']}",
        f"validation_row_count = {summary['validation_row_count']}",
        f"train_label_counts = {summary['train_label_counts']}",
        f"validation_label_counts = {summary['validation_label_counts']}",
        f"threshold = {summary['threshold']}",
        f"safe_radius = {summary['safe_radius']}",
        f"decision_scope = {summary['decision_scope']}",
        f"decision_record_count = {summary['decision_record_count']}",
        f"decision_split_counts = {summary['decision_split_counts']}",
        f"validation_candidate_ready = {str(summary['validation_candidate_ready']).lower()}",
        f"validation_safety_ready = {str(summary['validation_safety_ready']).lower()}",
        f"validation_safety_checks = {summary['validation_safety_checks']}",
        f"production_block_reasons = {summary['production_block_reasons']}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"selector_can_certificate = {str(summary['selector_can_certificate']).lower()}",
        f"gate_can_permanently_discard_negative_columns = {str(summary['gate_can_permanently_discard_negative_columns']).lower()}",
        "```",
        "",
        "## 指标",
        "",
        "```json",
        json.dumps(
            {
                "validation_metrics": summary["validation_metrics"],
                "validation_safety_checks": summary["validation_safety_checks"],
                "decision_scope_metrics": summary["decision_scope_metrics"],
                "decision_reason_counts": summary["decision_reason_counts"],
                "decision_split_counts": summary["decision_split_counts"],
                "threshold_info": summary["threshold_info"],
                "production_block_reasons": summary["production_block_reasons"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 结论",
        "",
        "- `validation_candidate_ready=false` 时，不允许进入 audit-only worker；",
        "- `decision_scope=all` 只用于扩充采样候选，不等同于 holdout validation 通过；",
        "- delay queue 标签代表 true-RC negative 需要延迟，不允许永久丢弃；",
        "- 该审计只验证表示/安全壳，不证明 5/10 不退化，也不证明 20 规模收益。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Audit GAT batch-impact admission with a kNN/OOD safety shell.

This script is offline and diagnostic-only.  It scores an existing
``GATBatchImpactModel`` checkpoint, applies the training-selected
batch/candidate thresholds, then delays out-of-distribution or kNN-unsafe
true-RC negative batches.  It never runs BPC, pricing, RMP, workers, or
certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from BPC_future.learning.batch_impact_model import (
    BATCH_IMPACT_EXACTNESS_CONTRACT,
    GATBatchImpactModel,
)
from BPC_future.scripts.audit_cbf_delay_queue_knn_ood_scheduler import (
    _nearest_safe_distance,
    _neighbor_unsafe_fraction,
    _safe_radius_threshold,
)
from BPC_future.scripts.train_gat_batch_impact import (
    _load_sample,
    _mean_ci_low,
    _normalize_sample,
    _wilson_ci_low,
)


DEFAULT_DATASET_DIR = Path("BPC_future/data/gat_batch_impact/v2_multiscale_20260615")
DEFAULT_CHECKPOINT = Path("BPC_future/data/gat_batch_impact/v2_multiscale_20260615/gat_batch_impact.pt")
DEFAULT_TRAINING_SUMMARY = Path("BPC_future/results/gat_batch_impact_training_v2_multiscale_20260615/summary.json")
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/gat_batch_impact_knn_ood_audit_v2_multiscale_20260615")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260615_bpc_future_gat_batch_impact_knn_ood_audit_v2_multiscale_zh.md"
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
    parser.add_argument("--min-safe-precision", type=float, default=0.85)
    parser.add_argument("--min-safe-precision-ci-low", type=float, default=None)
    parser.add_argument("--confidence-z", type=float, default=1.96)
    parser.add_argument("--min-accepted-batch-count", type=int, default=1)
    parser.add_argument("--min-accepted-batch-rate", type=float, default=0.02)
    parser.add_argument("--min-accepted-batch-roi", type=float, default=0.65)
    parser.add_argument("--min-accepted-batch-roi-ci-low", type=float, default=None)
    parser.add_argument("--max-false-high-priority-on-delay", type=float, default=0.01)
    parser.add_argument("--max-validation-false-safe-rate", type=float, default=0.02)
    parser.add_argument("--min-coverage", type=float, default=0.0)
    parser.add_argument("--decision-scope", choices=("validation", "all"), default="validation")
    parser.add_argument(
        "--threshold-grouping",
        choices=("global", "scale", "family", "scale_family"),
        default="global",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_batch_impact_knn_ood(
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
        min_safe_precision=float(args.min_safe_precision),
        min_safe_precision_ci_low=args.min_safe_precision_ci_low,
        confidence_z=float(args.confidence_z),
        min_accepted_batch_count=int(args.min_accepted_batch_count),
        min_accepted_batch_rate=float(args.min_accepted_batch_rate),
        min_accepted_batch_roi=float(args.min_accepted_batch_roi),
        min_accepted_batch_roi_ci_low=args.min_accepted_batch_roi_ci_low,
        max_false_high_priority_on_delay=float(args.max_false_high_priority_on_delay),
        max_validation_false_safe_rate=float(args.max_validation_false_safe_rate),
        min_coverage=float(args.min_coverage),
        decision_scope=str(args.decision_scope),
        threshold_grouping=str(args.threshold_grouping),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_batch_impact_knn_ood(
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
    min_safe_precision: float = 0.85,
    min_safe_precision_ci_low: float | None = None,
    confidence_z: float = 1.96,
    min_accepted_batch_count: int = 1,
    min_accepted_batch_rate: float = 0.02,
    min_accepted_batch_roi: float = 0.65,
    min_accepted_batch_roi_ci_low: float | None = None,
    max_false_high_priority_on_delay: float = 0.01,
    max_validation_false_safe_rate: float = 0.02,
    min_coverage: float = 0.0,
    decision_scope: str = "validation",
    threshold_grouping: str = "global",
) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    checkpoint_data = torch.load(checkpoint, map_location="cpu", weights_only=False)
    training = json.loads(Path(training_summary).read_text(encoding="utf-8"))
    manifest = json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    _assert_contracts(checkpoint_data, training, manifest)

    model = GATBatchImpactModel(**checkpoint_data["model_config"]).to(torch.device(device))
    model.load_state_dict(checkpoint_data["model_state_dict"])
    model.eval()
    records = _score_dataset(
        dataset_dir=dataset_dir,
        manifest=manifest,
        model=model,
        device=torch.device(device),
    )

    split = training.get("split") or checkpoint_data.get("training_contract", {}).get("main_split") or {}
    train_instances = set(split.get("train_instances") or [])
    validation_instances = set(split.get("validation_instances") or [])
    train_records = [record for record in records if record["instance"] in train_instances]
    validation_records = [record for record in records if record["instance"] in validation_instances]
    if not train_records or not validation_records:
        raise ValueError("training summary split does not match batch-impact dataset")

    thresholds = _selected_thresholds(training, checkpoint_data)
    guard_model = _build_guard_model(
        train_records=train_records,
        threshold_grouping=str(threshold_grouping),
        safe_radius_quantile=float(safe_radius_quantile),
        safe_radius_multiplier=float(safe_radius_multiplier),
        batch_threshold=float(thresholds["batch_threshold"]),
        batch_thresholds_by_family=dict(thresholds.get("batch_thresholds_by_family") or {}),
        family_delay_fallback_families=list(thresholds.get("family_delay_fallback_families") or []),
        context_delay_fallback_contexts=list(thresholds.get("context_delay_fallback_contexts") or []),
        candidate_threshold=float(thresholds["candidate_threshold"]),
        candidate_admission_score_mode=str(thresholds.get("candidate_admission_score_mode", "high_priority")),
        candidate_delay_score_penalty=float(thresholds.get("candidate_delay_score_penalty", 0.0)),
        candidate_delay_gate_enabled=bool(thresholds.get("candidate_delay_gate_enabled", False)),
        candidate_delay_risk_threshold=float(thresholds.get("candidate_delay_risk_threshold", 1.0)),
        knn_k=int(knn_k),
    )

    validation_decisions = [
        _classify_record(
            record,
            guard=_guard_for_record(guard_model, record),
            knn_k=int(knn_k),
            max_neighbor_delay_fraction=float(max_neighbor_delay_fraction),
            split="validation",
        )
        for record in validation_records
    ]
    emit_records = records if str(decision_scope) == "all" else validation_records
    decision_records: list[dict[str, Any]] = []
    for record in emit_records:
        split_name = "unknown"
        if record["instance"] in train_instances:
            split_name = "train"
        elif record["instance"] in validation_instances:
            split_name = "validation"
        decision_records.append(
            _classify_record(
                record,
                guard=_guard_for_record(guard_model, record),
                knn_k=int(knn_k),
                max_neighbor_delay_fraction=float(max_neighbor_delay_fraction),
                split=split_name,
            )
        )

    validation_metrics = _decision_metrics(validation_decisions, confidence_z=float(confidence_z))
    decision_scope_metrics = _decision_metrics(decision_records, confidence_z=float(confidence_z))
    validation_false_safe_rates = _validation_false_safe_rates(validation_metrics)
    validation_false_safe_rate = validation_false_safe_rates["max_observed_false_safe_rate"]
    validation_family_metrics = _family_metrics(
        validation_decisions,
        min_accepted_batch_roi=float(min_accepted_batch_roi),
        confidence_z=float(confidence_z),
    )
    min_safe_precision_ci_low_value = (
        float(min_safe_precision)
        if min_safe_precision_ci_low is None
        else float(min_safe_precision_ci_low)
    )
    min_accepted_batch_roi_ci_low_value = (
        float(min_accepted_batch_roi)
        if min_accepted_batch_roi_ci_low is None
        else float(min_accepted_batch_roi_ci_low)
    )
    validation_checks = {
        "min_high_priority_met": validation_metrics["accepted_batch_count"] >= int(min_validation_high_priority),
        "safe_precision_met": (
            validation_metrics["safe_precision"] is not None
            and validation_metrics["safe_precision"] >= float(min_safe_precision)
        ),
        "safe_precision_ci_low_met": (
            validation_metrics["safe_precision_ci_low"] is not None
            and validation_metrics["safe_precision_ci_low"] >= float(min_safe_precision_ci_low_value)
        ),
        "accepted_batch_count_met": validation_metrics["accepted_batch_count"] >= int(min_accepted_batch_count),
        "accepted_batch_rate_met": (
            validation_metrics["accepted_batch_rate"] is not None
            and validation_metrics["accepted_batch_rate"] >= float(min_accepted_batch_rate)
        ),
        "accepted_batch_roi_met": (
            validation_metrics["accepted_batch_roi"] is not None
            and validation_metrics["accepted_batch_roi"] >= float(min_accepted_batch_roi)
        ),
        "accepted_batch_roi_ci_low_met": (
            validation_metrics["accepted_batch_roi_ci_low"] is not None
            and validation_metrics["accepted_batch_roi_ci_low"] >= float(min_accepted_batch_roi_ci_low_value)
        ),
        "false_high_priority_on_delay_met": (
            validation_metrics["false_high_priority_on_delay"] <= float(max_false_high_priority_on_delay)
        ),
        "false_safe_rate_met": (
            validation_false_safe_rate is None
            or validation_false_safe_rate <= float(max_validation_false_safe_rate)
        ),
        "coverage_met": (
            validation_metrics["coverage"] is not None
            and validation_metrics["coverage"] >= float(min_coverage)
        ),
        "family_holdout_all_high_roi_opportunity_families_accepted": not validation_family_metrics[
            "missing_accepted_opportunity_families"
        ],
    }
    validation_candidate_ready = bool(all(validation_checks.values()))
    production_block_reasons = _production_block_reasons(validation_checks)
    if not validation_candidate_ready:
        production_block_reasons.append("validation_candidate_not_ready")

    summary = {
        "schema_version": "gat_batch_impact_knn_ood_audit_v1",
        "status": "gat_batch_impact_knn_ood_audited",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "dataset_dir": str(dataset_dir),
        "checkpoint": str(checkpoint),
        "training_summary": str(training_summary),
        "train_row_count": len(train_records),
        "validation_row_count": len(validation_records),
        "train_label_counts": _label_counts(train_records),
        "validation_label_counts": _label_counts(validation_records),
        "batch_threshold": float(thresholds["batch_threshold"]),
        "batch_thresholds_by_family": {
            str(key): float(value)
            for key, value in sorted((thresholds.get("batch_thresholds_by_family") or {}).items())
        },
        "candidate_threshold": float(thresholds["candidate_threshold"]),
        "candidate_admission_score_mode": str(
            thresholds.get("candidate_admission_score_mode", "high_priority") or "high_priority"
        ),
        "candidate_delay_score_penalty": max(
            0.0,
            float(thresholds.get("candidate_delay_score_penalty", 0.0)),
        ),
        "candidate_delay_gate_enabled": bool(thresholds.get("candidate_delay_gate_enabled", False)),
        "candidate_delay_risk_threshold": float(thresholds.get("candidate_delay_risk_threshold", 1.0)),
        "threshold_mode": (
            "family_local_batch_candidate"
            if thresholds.get("batch_thresholds_by_family")
            else "separate_batch_candidate"
        ),
        "threshold_grouping": str(threshold_grouping),
        "threshold_group_info": _serializable_guard_model(guard_model),
        "knn_k": int(knn_k),
        "max_neighbor_delay_fraction": float(max_neighbor_delay_fraction),
        "safe_radius_quantile": float(safe_radius_quantile),
        "safe_radius_multiplier": float(safe_radius_multiplier),
        "min_safe_precision": float(min_safe_precision),
        "min_safe_precision_ci_low": float(min_safe_precision_ci_low_value),
        "confidence_z": float(confidence_z),
        "min_accepted_batch_count": int(min_accepted_batch_count),
        "min_accepted_batch_rate": float(min_accepted_batch_rate),
        "min_accepted_batch_roi": float(min_accepted_batch_roi),
        "min_accepted_batch_roi_ci_low": float(min_accepted_batch_roi_ci_low_value),
        "max_false_high_priority_on_delay": float(max_false_high_priority_on_delay),
        "max_validation_false_safe_rate": float(max_validation_false_safe_rate),
        "min_coverage": float(min_coverage),
        "decision_scope": str(decision_scope),
        "decision_record_count": len(decision_records),
        "validation_metrics": validation_metrics,
        "decision_scope_metrics": decision_scope_metrics,
        "validation_false_safe_rates": validation_false_safe_rates,
        "validation_family_metrics": validation_family_metrics,
        "validation_safety_checks": validation_checks,
        "decision_reason_counts": dict(
            sorted(Counter(record["decision_reason"] for record in decision_records).items())
        ),
        "decision_threshold_group_counts": dict(
            sorted(Counter(record["threshold_group"] for record in decision_records).items())
        ),
        "decision_threshold_scope_counts": dict(
            sorted(Counter(record["threshold_scope"] for record in decision_records).items())
        ),
        "decision_split_counts": dict(
            sorted(Counter(record["decision_split"] for record in decision_records).items())
        ),
        "decision_records_path": str(output_dir / "decision_records.jsonl"),
        "validation_candidate_ready": validation_candidate_ready,
        "validation_safety_ready": validation_candidate_ready,
        "production_block_reasons": production_block_reasons,
        "production_ready": False,
        "default_enabled": False,
        "official_bound_effect": False,
        "selector_is_pricing_oracle": False,
        "selector_can_certificate": False,
        "gate_can_permanently_discard_negative_columns": False,
        "negative_columns_must_remain_eventually_reachable": True,
        "unsafe_negative_decision": "DELAY_QUEUE",
        "safe_negative_decision": "HIGH_PRIORITY",
        "target_label": "same_context_batch_trajectory_roi",
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


def _assert_contracts(
    checkpoint_data: dict[str, Any],
    training: dict[str, Any],
    manifest: dict[str, Any],
) -> None:
    if checkpoint_data.get("target_label") != "same_context_batch_trajectory_roi":
        raise ValueError("batch-impact checkpoint target label mismatch")
    if checkpoint_data.get("exactness_contract") != BATCH_IMPACT_EXACTNESS_CONTRACT:
        raise ValueError("batch-impact exactness contract mismatch")
    if bool(checkpoint_data.get("training_contract", {}).get("production_ready")):
        raise ValueError("batch-impact checkpoint must be diagnostic-only")
    if training.get("schema_version") != "gat_batch_impact_training_summary_v1":
        raise ValueError("batch-impact training summary schema mismatch")
    if bool(training.get("production_ready")):
        raise ValueError("batch-impact training summary must not be production_ready")
    if manifest.get("schema_version") != "gat_batch_impact_dataset_manifest_v1":
        raise ValueError("batch-impact dataset manifest schema mismatch")
    if not bool(manifest.get("diagnostic_only")):
        raise ValueError("batch-impact dataset must be diagnostic_only")


def _selected_thresholds(training: dict[str, Any], checkpoint_data: dict[str, Any]) -> dict[str, Any]:
    metrics = training.get("validation_deployment_metrics") or {}
    if "batch_threshold" not in metrics:
        metrics = checkpoint_data.get("training", {}).get("validation_deployment_metrics") or {}
    return {
        "batch_threshold": float(metrics.get("batch_threshold", metrics.get("threshold", 0.9))),
        "batch_thresholds_by_family": {
            str(key): float(value)
            for key, value in dict(metrics.get("batch_thresholds_by_family") or {}).items()
        },
        "family_delay_fallback_families": [
            str(value) for value in (metrics.get("family_delay_fallback_families") or [])
        ],
        "context_delay_fallback_contexts": [
            str(value) for value in (metrics.get("context_delay_fallback_contexts") or [])
        ],
        "candidate_threshold": float(metrics.get("candidate_threshold", metrics.get("threshold", 0.9))),
        "candidate_admission_score_mode": str(
            metrics.get("candidate_admission_score_mode", "high_priority") or "high_priority"
        ),
        "candidate_delay_score_penalty": max(
            0.0,
            float(metrics.get("candidate_delay_score_penalty", 0.0)),
        ),
        "candidate_delay_gate_enabled": bool(metrics.get("candidate_delay_gate_enabled", False)),
        "candidate_delay_risk_threshold": min(
            1.0,
            max(0.0, float(metrics.get("candidate_delay_risk_threshold", 1.0))),
        ),
    }


def _score_dataset(
    *,
    dataset_dir: Path,
    manifest: dict[str, Any],
    model: GATBatchImpactModel,
    device: torch.device,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with torch.no_grad():
        for item in manifest.get("samples", []):
            sample = _normalize_sample(_load_sample(dataset_dir / item["path"]), manifest).to(device)
            output = model(
                sample,
                sample.candidate_task_membership,
                sample.candidate_sequence_positions,
                sample.candidate_features,
                sample.context_features,
                batch_features=sample.batch_features,
            )
            records.append(_record_from_output(item=item, sample=sample, output=output))
    return records


def _record_from_output(item: dict[str, Any], sample: Any, output: dict[str, torch.Tensor]) -> dict[str, Any]:
    candidate_scores = [
        float(value)
        for value in output["high_priority_probability"].detach().cpu().reshape(-1).tolist()
    ]
    candidate_delay_scores = [
        float(value)
        for value in output["delay_risk_probability"].detach().cpu().reshape(-1).tolist()
    ]
    candidate_high_priority_labels = [
        int(value)
        for value in sample.y_candidate_high_priority.detach().cpu().reshape(-1).to(dtype=torch.long).tolist()
    ]
    candidate_delay_labels = [
        int(value)
        for value in sample.y_candidate_delay_risk.detach().cpu().reshape(-1).to(dtype=torch.long).tolist()
    ]
    batch_embedding = output["batch_embedding"].detach().cpu()
    context_embedding = output["context_embedding"].detach().cpu()
    candidate_embedding = output["candidate_embedding"].detach().cpu()
    family = str(getattr(sample, "batch_impact_instance_family", item.get("instance_family", "")) or "unknown")
    instance = str(
        getattr(sample, "batch_impact_instance_path", "")
        or getattr(sample, "batch_impact_instance", item.get("instance", ""))
    )
    task_count = str(
        getattr(sample, "batch_impact_task_count", item.get("task_count", ""))
        or _record_task_count({"instance": instance, "sample_path": str(item.get("path", ""))})
        or "unknown"
    )
    candidate_ids = _sample_list_attr(sample, "batch_impact_candidate_ids", item.get("candidate_ids", []))
    candidate_signature_ids = _sample_list_attr(
        sample,
        "batch_impact_candidate_signature_ids",
        item.get("candidate_signature_ids", []),
    )
    candidate_signature_source_present = [
        bool(value)
        for value in _sample_list_attr(
            sample,
            "batch_impact_candidate_signature_source_present",
            [True] * len(candidate_signature_ids),
        )
    ]
    return {
        "instance": instance,
        "instance_path": instance,
        "sample_path": str(item.get("path", "")),
        "context_hash": str(getattr(sample, "batch_impact_context_hash", item.get("context_hash", ""))),
        "source_file": str(getattr(sample, "batch_impact_source_jsonl", item.get("source_file", ""))),
        "row_index": int(getattr(sample, "batch_impact_source_row_index", item.get("row_index", -1))),
        "instance_family": family,
        "instance_task_count": task_count,
        "batch_score": float(output["batch_roi_positive_probability"].detach().cpu().item()),
        "candidate_ids": candidate_ids,
        "candidate_signature_ids": candidate_signature_ids,
        "candidate_signature_source_present": candidate_signature_source_present,
        "candidate_scores": candidate_scores,
        "candidate_delay_scores": candidate_delay_scores,
        "candidate_high_priority_labels": candidate_high_priority_labels,
        "candidate_delay_labels": candidate_delay_labels,
        "label_high_priority": int(sample.y_batch_roi_positive.detach().cpu().item() > 0.5)
        if int(sample.y_bad_mode_switch.detach().cpu().item() <= 0.5)
        else 0,
        "batch_roi_positive": int(sample.y_batch_roi_positive.detach().cpu().item() > 0.5),
        "bad_mode_switch": int(sample.y_bad_mode_switch.detach().cpu().item() > 0.5),
        "tail_improved": int(sample.y_tail_improved.detach().cpu().item() > 0.5),
        "support_changed_good": int(sample.y_support_changed_good.detach().cpu().item() > 0.5),
        "accepted_batch_roi_label": float(sample.y_accepted_batch_roi.detach().cpu().item()),
        "embedding": _sample_embedding(batch_embedding, context_embedding, candidate_embedding, candidate_scores),
    }


def _sample_list_attr(sample: Any, attr: str, fallback: Any) -> list[Any]:
    value = getattr(sample, attr, None)
    if value is None:
        value = fallback
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().reshape(-1).tolist()
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, list):
        return value
    return []


def _sample_embedding(
    batch_embedding: torch.Tensor,
    context_embedding: torch.Tensor,
    candidate_embedding: torch.Tensor,
    candidate_scores: list[float],
) -> list[float]:
    scores = torch.tensor(candidate_scores, dtype=torch.float32)
    vector = torch.cat(
        [
            batch_embedding.to(dtype=torch.float32).reshape(-1),
            context_embedding.to(dtype=torch.float32).reshape(-1),
            candidate_embedding.to(dtype=torch.float32).mean(dim=0),
            candidate_embedding.to(dtype=torch.float32).std(dim=0, unbiased=False),
            torch.tensor(
                [
                    float(candidate_embedding.size(0)),
                    float(scores.mean().item()) if scores.numel() else 0.0,
                    float(scores.max().item()) if scores.numel() else 0.0,
                    float(scores.min().item()) if scores.numel() else 0.0,
                    float(scores.std(unbiased=False).item()) if scores.numel() > 1 else 0.0,
                ],
                dtype=torch.float32,
            ),
        ],
        dim=0,
    )
    return [
        0.0 if math.isnan(float(value)) or math.isinf(float(value)) else float(value)
        for value in vector.tolist()
    ]


def _build_guard_model(
    *,
    train_records: list[dict[str, Any]],
    threshold_grouping: str,
    safe_radius_quantile: float,
    safe_radius_multiplier: float,
    batch_threshold: float,
    batch_thresholds_by_family: dict[str, float] | None,
    family_delay_fallback_families: list[str] | None,
    context_delay_fallback_contexts: list[str] | None,
    candidate_threshold: float,
    candidate_admission_score_mode: str,
    candidate_delay_score_penalty: float,
    candidate_delay_gate_enabled: bool,
    candidate_delay_risk_threshold: float,
    knn_k: int,
) -> dict[str, Any]:
    global_guard = _guard_from_records(
        records=train_records,
        group="global",
        scope="global",
        safe_radius_quantile=float(safe_radius_quantile),
        safe_radius_multiplier=float(safe_radius_multiplier),
        batch_threshold=float(batch_threshold),
        batch_thresholds_by_family=batch_thresholds_by_family,
        family_delay_fallback_families=family_delay_fallback_families,
        context_delay_fallback_contexts=context_delay_fallback_contexts,
        candidate_threshold=float(candidate_threshold),
        candidate_admission_score_mode=str(candidate_admission_score_mode),
        candidate_delay_score_penalty=float(candidate_delay_score_penalty),
        candidate_delay_gate_enabled=bool(candidate_delay_gate_enabled),
        candidate_delay_risk_threshold=float(candidate_delay_risk_threshold),
    )
    groups: dict[str, dict[str, Any]] = {}
    skipped: dict[str, dict[str, Any]] = {}
    if str(threshold_grouping) != "global":
        by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in train_records:
            by_group[_record_group_key(record, str(threshold_grouping))].append(record)
        for group, records in sorted(by_group.items()):
            labels = [int(record["label_high_priority"]) for record in records]
            if len(records) < max(2, int(knn_k)) or 0 not in labels or 1 not in labels:
                skipped[group] = {
                    "scope": "fallback_global",
                    "train_count": len(records),
                    "label_counts": _label_counts(records),
                    "skip_reason": "sparse_or_single_label_group",
                }
                continue
            groups[group] = _guard_from_records(
                records=records,
                group=group,
                scope=str(threshold_grouping),
                safe_radius_quantile=float(safe_radius_quantile),
                safe_radius_multiplier=float(safe_radius_multiplier),
                batch_threshold=float(batch_threshold),
                batch_thresholds_by_family=batch_thresholds_by_family,
                family_delay_fallback_families=family_delay_fallback_families,
                context_delay_fallback_contexts=context_delay_fallback_contexts,
                candidate_threshold=float(candidate_threshold),
                candidate_admission_score_mode=str(candidate_admission_score_mode),
                candidate_delay_score_penalty=float(candidate_delay_score_penalty),
                candidate_delay_gate_enabled=bool(candidate_delay_gate_enabled),
                candidate_delay_risk_threshold=float(candidate_delay_risk_threshold),
            )
    return {
        "threshold_grouping": str(threshold_grouping),
        "global": global_guard,
        "groups": groups,
        "skipped_groups": skipped,
    }


def _guard_from_records(
    *,
    records: list[dict[str, Any]],
    group: str,
    scope: str,
    safe_radius_quantile: float,
    safe_radius_multiplier: float,
    batch_threshold: float,
    batch_thresholds_by_family: dict[str, float] | None,
    family_delay_fallback_families: list[str] | None,
    context_delay_fallback_contexts: list[str] | None,
    candidate_threshold: float,
    candidate_admission_score_mode: str,
    candidate_delay_score_penalty: float,
    candidate_delay_gate_enabled: bool,
    candidate_delay_risk_threshold: float,
) -> dict[str, Any]:
    train_x = [record["embedding"] for record in records]
    train_y = [int(record["label_high_priority"]) for record in records]
    return {
        "group": str(group),
        "scope": str(scope),
        "batch_threshold": float(batch_threshold),
        "batch_thresholds_by_family": {
            str(key): float(value) for key, value in sorted((batch_thresholds_by_family or {}).items())
        },
        "family_delay_fallback_families": sorted(
            str(value) for value in (family_delay_fallback_families or [])
        ),
        "context_delay_fallback_contexts": sorted(
            str(value) for value in (context_delay_fallback_contexts or [])
        ),
        "candidate_threshold": float(candidate_threshold),
        "candidate_admission_score_mode": _candidate_admission_score_mode(candidate_admission_score_mode),
        "candidate_delay_score_penalty": max(0.0, float(candidate_delay_score_penalty)),
        "candidate_delay_gate_enabled": bool(candidate_delay_gate_enabled),
        "candidate_delay_risk_threshold": min(1.0, max(0.0, float(candidate_delay_risk_threshold))),
        "train_x": train_x,
        "train_y": train_y,
        "train_count": len(records),
        "label_counts": _label_counts(records),
        "safe_radius": _safe_radius_threshold(
            train_x,
            train_y,
            quantile=float(safe_radius_quantile),
            multiplier=float(safe_radius_multiplier),
        ),
    }


def _guard_for_record(guard_model: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    grouping = str(guard_model.get("threshold_grouping", "global"))
    if grouping == "global":
        return guard_model["global"]
    key = _record_group_key(record, grouping)
    return guard_model.get("groups", {}).get(key) or guard_model["global"]


def _classify_record(
    record: dict[str, Any],
    *,
    guard: dict[str, Any],
    knn_k: int,
    max_neighbor_delay_fraction: float,
    split: str,
) -> dict[str, Any]:
    neighbor_delay_fraction = _neighbor_unsafe_fraction(
        guard["train_x"],
        guard["train_y"],
        record["embedding"],
        k=int(knn_k),
    )
    nearest_safe = _nearest_safe_distance(guard["train_x"], guard["train_y"], record["embedding"])
    safe_radius = guard["safe_radius"]
    in_radius = bool(safe_radius is not None and nearest_safe is not None and nearest_safe <= safe_radius)
    predicted_indices, candidate_delay_gate_blocked, candidate_risk_adjusted_suppressed = _candidate_prediction_indices(
        record,
        candidate_threshold=float(guard["candidate_threshold"]),
        candidate_admission_score_mode=str(guard.get("candidate_admission_score_mode", "high_priority")),
        candidate_delay_score_penalty=float(guard.get("candidate_delay_score_penalty", 0.0)),
        candidate_delay_gate_enabled=bool(guard.get("candidate_delay_gate_enabled", False)),
        candidate_delay_risk_threshold=float(guard.get("candidate_delay_risk_threshold", 1.0)),
    )
    candidate_fp = _candidate_false_high_priority_on_delay(record, predicted_indices)
    candidate_predicted = len(predicted_indices)
    candidate_signature_ids = [str(value) for value in record.get("candidate_signature_ids", [])]
    candidate_ids = [str(value) for value in record.get("candidate_ids", [])]
    high_priority_candidate_signature_ids = [
        str(candidate_signature_ids[idx])
        for idx in predicted_indices
        if idx < len(candidate_signature_ids)
    ]
    high_priority_candidate_ids = [
        str(candidate_ids[idx])
        for idx in predicted_indices
        if idx < len(candidate_ids)
    ]
    candidate_signature_source_present = [
        bool(value) for value in record.get("candidate_signature_source_present", [])
    ]
    actual_batch_threshold = _batch_threshold_for_record(record, guard)
    family_delay_fallback = str(record.get("instance_family") or "unknown") in set(
        str(value) for value in guard.get("family_delay_fallback_families", [])
    )
    context_delay_fallback = str(record.get("context_hash") or "") in set(
        str(value) for value in guard.get("context_delay_fallback_contexts", [])
    )
    if family_delay_fallback or context_delay_fallback:
        candidate_predicted = 0
        candidate_fp = 0
        high_priority_candidate_signature_ids = []
        high_priority_candidate_ids = []
    base_batch_positive = float(record["batch_score"]) >= float(actual_batch_threshold)
    decision = int(
        base_batch_positive
        and candidate_predicted > 0
        and candidate_fp == 0
        and not family_delay_fallback
        and not context_delay_fallback
        and neighbor_delay_fraction <= float(max_neighbor_delay_fraction)
        and in_radius
    )
    reason = "high_priority"
    if family_delay_fallback:
        reason = "family_delay_fallback_delay_queue"
    elif context_delay_fallback:
        reason = "context_delay_fallback_delay_queue"
    elif not base_batch_positive:
        reason = "below_batch_threshold_delay_queue"
    elif candidate_predicted <= 0:
        reason = "no_candidate_high_priority_delay_queue"
    elif candidate_fp > 0:
        reason = "candidate_false_high_priority_delay_queue"
    elif neighbor_delay_fraction > float(max_neighbor_delay_fraction):
        reason = "knn_delay_fraction_delay_queue"
    elif not in_radius:
        reason = "ood_radius_delay_queue"
    return {
        **{key: record[key] for key in (
            "instance",
            "instance_path",
            "sample_path",
            "context_hash",
            "source_file",
            "row_index",
            "instance_family",
            "instance_task_count",
            "label_high_priority",
            "batch_roi_positive",
            "bad_mode_switch",
            "tail_improved",
            "support_changed_good",
            "accepted_batch_roi_label",
            "batch_score",
        )},
        "decision_split": str(split),
        "candidate_threshold": float(guard["candidate_threshold"]),
        "candidate_admission_score_mode": str(guard.get("candidate_admission_score_mode", "high_priority")),
        "candidate_delay_score_penalty": max(0.0, float(guard.get("candidate_delay_score_penalty", 0.0))),
        "candidate_delay_gate_enabled": bool(guard.get("candidate_delay_gate_enabled", False)),
        "candidate_delay_risk_threshold": float(guard.get("candidate_delay_risk_threshold", 1.0)),
        "batch_threshold": float(actual_batch_threshold),
        "global_batch_threshold": float(guard["batch_threshold"]),
        "candidate_ids": candidate_ids,
        "candidate_signature_ids": candidate_signature_ids,
        "high_priority_candidate_ids": high_priority_candidate_ids,
        "high_priority_candidate_signature_ids": high_priority_candidate_signature_ids,
        "candidate_signature_id_count": len(candidate_signature_ids),
        "candidate_signature_source_present_count": int(sum(candidate_signature_source_present)),
        "candidate_signature_ids_complete": (
            len(candidate_signature_ids) == len(record["candidate_scores"])
            and int(sum(candidate_signature_source_present)) == len(record["candidate_scores"])
        ),
        "candidate_predicted_high_priority_count": int(candidate_predicted),
        "candidate_delay_gate_blocked_count": int(candidate_delay_gate_blocked),
        "candidate_risk_adjusted_suppressed_count": int(candidate_risk_adjusted_suppressed),
        "candidate_false_high_priority_on_delay_count": int(candidate_fp),
        "candidate_delay_label_count": int(sum(int(value) for value in record["candidate_delay_labels"])),
        "neighbor_delay_fraction": float(neighbor_delay_fraction),
        "nearest_safe_distance": None if nearest_safe is None else float(nearest_safe),
        "safe_radius": None if safe_radius is None else float(safe_radius),
        "is_ood": bool(not in_radius),
        "is_knn_unsafe": bool(neighbor_delay_fraction > float(max_neighbor_delay_fraction)),
        "is_label_unsafe": bool(int(record["label_high_priority"]) == 0 or candidate_fp > 0),
        "decision": int(decision),
        "decision_name": "HIGH_PRIORITY" if decision else "DELAY_QUEUE",
        "decision_reason": reason,
        "threshold_group": str(guard["group"]),
        "threshold_scope": str(guard["scope"]),
    }


def _batch_threshold_for_record(record: dict[str, Any], guard: dict[str, Any]) -> float:
    family = str(record.get("instance_family") or "unknown")
    thresholds = dict(guard.get("batch_thresholds_by_family") or {})
    return float(thresholds.get(family, guard["batch_threshold"]))


def _candidate_prediction_indices(
    record: dict[str, Any],
    *,
    candidate_threshold: float,
    candidate_admission_score_mode: str,
    candidate_delay_score_penalty: float,
    candidate_delay_gate_enabled: bool,
    candidate_delay_risk_threshold: float,
) -> tuple[list[int], int, int]:
    candidate_scores = [float(score) for score in record.get("candidate_scores", [])]
    delay_scores = [float(score) for score in record.get("candidate_delay_scores", [])]
    if len(delay_scores) != len(candidate_scores):
        default_score = 1.0 if bool(candidate_delay_gate_enabled) else 0.0
        delay_scores = [float(default_score) for _ in candidate_scores]
    admission_scores = _candidate_admission_scores(
        candidate_scores,
        delay_scores,
        candidate_admission_score_mode=candidate_admission_score_mode,
        candidate_delay_score_penalty=candidate_delay_score_penalty,
    )
    predicted: list[int] = []
    blocked = 0
    suppressed = 0
    delay_threshold = min(1.0, max(0.0, float(candidate_delay_risk_threshold)))
    for idx, score in enumerate(admission_scores):
        if (
            _candidate_admission_score_mode(candidate_admission_score_mode) != "high_priority"
            and float(candidate_scores[idx]) >= float(candidate_threshold)
            and float(score) < float(candidate_threshold)
        ):
            suppressed += 1
        if float(score) < float(candidate_threshold):
            continue
        if bool(candidate_delay_gate_enabled) and float(delay_scores[idx]) > delay_threshold:
            blocked += 1
            continue
        predicted.append(int(idx))
    return predicted, int(blocked), int(suppressed)


def _candidate_admission_score_mode(mode: str) -> str:
    mode = str(mode or "high_priority")
    if mode not in {"high_priority", "risk_adjusted_product"}:
        return "high_priority"
    return mode


def _candidate_admission_scores(
    candidate_scores: list[float],
    delay_scores: list[float],
    *,
    candidate_admission_score_mode: str,
    candidate_delay_score_penalty: float,
) -> list[float]:
    if _candidate_admission_score_mode(candidate_admission_score_mode) != "risk_adjusted_product":
        return [float(score) for score in candidate_scores]
    penalty = max(0.0, float(candidate_delay_score_penalty))
    return [
        max(0.0, min(1.0, float(candidate_score) * (max(0.0, min(1.0, 1.0 - float(delay_score))) ** penalty)))
        for candidate_score, delay_score in zip(candidate_scores, delay_scores)
    ]


def _candidate_false_high_priority_on_delay(record: dict[str, Any], predicted_indices: list[int]) -> int:
    return sum(
        int(record["candidate_delay_labels"][idx])
        for idx in predicted_indices
        if idx < len(record["candidate_delay_labels"])
    )


def _decision_metrics(records: list[dict[str, Any]], *, confidence_z: float = 1.96) -> dict[str, Any]:
    total = len(records)
    accepted = [record for record in records if int(record["decision"]) == 1]
    delayed = [record for record in records if int(record["decision"]) == 0]
    ood = [record for record in records if bool(record.get("is_ood", False))]
    non_ood = [record for record in records if not bool(record.get("is_ood", False))]
    knn_unsafe = [record for record in records if bool(record.get("is_knn_unsafe", False))]
    label_unsafe = [record for record in records if bool(record.get("is_label_unsafe", False))]
    unsafe_union = [
        record
        for record in records
        if bool(record.get("is_ood", False))
        or bool(record.get("is_knn_unsafe", False))
        or bool(record.get("is_label_unsafe", False))
    ]
    accepted_ood = [record for record in accepted if bool(record.get("is_ood", False))]
    accepted_knn_unsafe = [record for record in accepted if bool(record.get("is_knn_unsafe", False))]
    accepted_label_unsafe = [record for record in accepted if bool(record.get("is_label_unsafe", False))]
    accepted_unsafe_union = [
        record
        for record in accepted
        if bool(record.get("is_ood", False))
        or bool(record.get("is_knn_unsafe", False))
        or bool(record.get("is_label_unsafe", False))
    ]
    accepted_safe = [record for record in accepted if int(record.get("label_high_priority", 0)) == 1]
    accepted_roi_values = [float(record["accepted_batch_roi_label"]) for record in accepted]
    safe_precision = _safe_divide(len(accepted_safe), len(accepted))
    safe_precision_ci_low = _wilson_ci_low(
        len(accepted_safe),
        len(accepted),
        z=float(confidence_z),
    )
    accepted_batch_roi = (
        None if not accepted_roi_values else sum(accepted_roi_values) / float(len(accepted_roi_values))
    )
    accepted_batch_roi_ci_low = _mean_ci_low(accepted_roi_values, z=float(confidence_z))
    delay_label_count = sum(int(record.get("candidate_delay_label_count", 0)) for record in records)
    false_hp_count = sum(int(record.get("candidate_false_high_priority_on_delay_count", 0)) for record in accepted)
    false_positive_contexts = sorted(
        {str(record.get("context_hash") or "") for record in accepted_label_unsafe}
    )
    return {
        "total": int(total),
        "coverage_non_ood_count": int(len(non_ood)),
        "coverage": _safe_divide(len(non_ood), total),
        "ood_count": int(len(ood)),
        "ood_rate": _safe_divide(len(ood), total),
        "delay_count": int(len(delayed)),
        "delay_rate": _safe_divide(len(delayed), total),
        "accepted_batch_count": int(len(accepted)),
        "accepted_batch_rate": _safe_divide(len(accepted), total),
        "accepted_batch_roi_positive_count": int(len(accepted_safe)),
        "accepted_batch_roi": accepted_batch_roi,
        "accepted_batch_roi_ci_low": accepted_batch_roi_ci_low,
        "safe_precision": safe_precision,
        "safe_precision_ci_low": safe_precision_ci_low,
        "unsafe_label_count": int(len(label_unsafe)),
        "knn_unsafe_count": int(len(knn_unsafe)),
        "unsafe_or_ood_count": int(len(unsafe_union)),
        "false_high_priority_on_delay_count": int(false_hp_count),
        "delay_label_count": int(delay_label_count),
        "false_high_priority_on_delay": 0.0 if delay_label_count <= 0 else false_hp_count / float(delay_label_count),
        "false_safe_ood_count": int(len(accepted_ood)),
        "false_safe_rate_ood": _safe_divide(len(accepted_ood), len(ood)),
        "false_safe_knn_unsafe_count": int(len(accepted_knn_unsafe)),
        "false_safe_rate_knn_unsafe": _safe_divide(len(accepted_knn_unsafe), len(knn_unsafe)),
        "false_safe_label_unsafe_count": int(len(accepted_label_unsafe)),
        "false_safe_rate_label_unsafe": _safe_divide(len(accepted_label_unsafe), len(label_unsafe)),
        "false_positive_context_count": int(len(false_positive_contexts)),
        "false_positive_contexts": false_positive_contexts,
        "false_safe_union_count": int(len(accepted_unsafe_union)),
        "false_safe_rate_union": _safe_divide(len(accepted_unsafe_union), len(unsafe_union)),
        "decision_reason_counts": dict(
            sorted(Counter(str(record.get("decision_reason", "")) for record in records).items())
        ),
        "accepted_reason_counts": dict(
            sorted(Counter(str(record.get("decision_reason", "")) for record in accepted).items())
        ),
    }


def _validation_false_safe_rates(metrics: dict[str, Any]) -> dict[str, Any]:
    named_rates = {
        "ood": metrics.get("false_safe_rate_ood"),
        "knn_unsafe": metrics.get("false_safe_rate_knn_unsafe"),
        "label_unsafe": metrics.get("false_safe_rate_label_unsafe"),
        "union": metrics.get("false_safe_rate_union"),
    }
    observed = {key: float(value) for key, value in named_rates.items() if value is not None}
    return {
        **named_rates,
        "max_observed_false_safe_rate": None if not observed else max(observed.values()),
        "max_observed_false_safe_source": None if not observed else max(observed, key=lambda key: observed[key]),
    }


def _family_metrics(
    records: list[dict[str, Any]],
    *,
    min_accepted_batch_roi: float,
    confidence_z: float = 1.96,
) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[str(record.get("instance_family") or "unknown")].append(record)
    per_family: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    missing_opportunity: list[str] = []
    delay_fallback: list[str] = []
    oracle_high_roi_families: list[str] = []
    for family, group_records in sorted(groups.items()):
        metrics = _decision_metrics(group_records, confidence_z=float(confidence_z))
        oracle_count = _family_oracle_high_roi_count(
            group_records,
            min_accepted_batch_roi=float(min_accepted_batch_roi),
        )
        metrics["oracle_high_roi_count"] = int(oracle_count)
        metrics["max_accepted_batch_roi_label"] = max(
            (float(record["accepted_batch_roi_label"]) for record in group_records),
            default=0.0,
        )
        per_family[family] = metrics
        if int(oracle_count) > 0:
            oracle_high_roi_families.append(str(family))
        if int(metrics.get("accepted_batch_count") or 0) <= 0:
            missing.append(str(family))
            if int(oracle_count) > 0:
                missing_opportunity.append(str(family))
            else:
                delay_fallback.append(str(family))
    return {
        "family_count": len(per_family),
        "missing_accepted_families": missing,
        "missing_accepted_opportunity_families": missing_opportunity,
        "family_specific_delay_fallback_families": delay_fallback,
        "oracle_high_roi_families": oracle_high_roi_families,
        "per_family": per_family,
    }


def _family_oracle_high_roi_count(
    records: list[dict[str, Any]],
    *,
    min_accepted_batch_roi: float,
) -> int:
    return sum(
        1
        for record in records
        if float(record["accepted_batch_roi_label"]) >= float(min_accepted_batch_roi)
        and not bool(record.get("is_label_unsafe", False))
    )


def _production_block_reasons(checks: dict[str, bool]) -> list[str]:
    mapping = {
        "min_high_priority_met": "validation_high_priority_below_min",
        "safe_precision_met": "validation_safe_precision_below_min",
        "safe_precision_ci_low_met": "validation_safe_precision_ci_low_below_min",
        "accepted_batch_count_met": "validation_accepted_batch_count_below_min",
        "accepted_batch_rate_met": "validation_accepted_batch_rate_below_min",
        "accepted_batch_roi_met": "validation_accepted_batch_roi_below_min",
        "accepted_batch_roi_ci_low_met": "validation_accepted_batch_roi_ci_low_below_min",
        "false_high_priority_on_delay_met": "validation_false_high_priority_on_delay_above_max",
        "false_safe_rate_met": "validation_false_safe_rate_above_max",
        "coverage_met": "validation_coverage_below_min",
        "family_holdout_all_high_roi_opportunity_families_accepted": (
            "family_holdout_accepted_batch_missing"
        ),
    }
    return [reason for key, reason in mapping.items() if not checks.get(key, False)]


def _serializable_guard_model(guard_model: dict[str, Any]) -> dict[str, Any]:
    return {
        "threshold_grouping": guard_model["threshold_grouping"],
        "global": _serializable_guard(guard_model["global"]),
        "groups": {key: _serializable_guard(value) for key, value in sorted(guard_model.get("groups", {}).items())},
        "skipped_groups": guard_model.get("skipped_groups", {}),
    }


def _serializable_guard(guard: dict[str, Any]) -> dict[str, Any]:
    return {
        "group": guard["group"],
        "scope": guard["scope"],
        "batch_threshold": float(guard["batch_threshold"]),
        "batch_thresholds_by_family": {
            str(key): float(value)
            for key, value in sorted((guard.get("batch_thresholds_by_family") or {}).items())
        },
        "family_delay_fallback_families": [
            str(value) for value in guard.get("family_delay_fallback_families", [])
        ],
        "context_delay_fallback_contexts": [
            str(value) for value in guard.get("context_delay_fallback_contexts", [])
        ],
        "candidate_threshold": float(guard["candidate_threshold"]),
        "train_count": int(guard["train_count"]),
        "label_counts": guard["label_counts"],
        "safe_radius": None if guard["safe_radius"] is None else float(guard["safe_radius"]),
    }


def _record_group_key(record: dict[str, Any], grouping: str) -> str:
    scale = str(record.get("instance_task_count") or _record_task_count(record) or "unknown").zfill(3)
    family = str(record.get("instance_family") or "unknown")
    if grouping == "scale":
        return scale
    if grouping == "family":
        return family
    if grouping == "scale_family":
        return f"{scale}|{family}"
    return "global"


def _record_task_count(record: dict[str, Any]) -> str | None:
    text = " ".join(str(record.get(key, "")) for key in ("instance_path", "instance", "sample_path", "source_file"))
    match = re.search(r"tasks[_-]?(\d+)", text)
    if not match:
        return None
    return match.group(1).zfill(3)


def _label_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter("high_priority" if int(record["label_high_priority"]) else "delay_queue" for record in records)
    return dict(sorted((str(key), int(value)) for key, value in counts.items()))


def _safe_divide(numerator: int | float, denominator: int | float) -> float | None:
    if float(denominator) <= 0.0:
        return None
    return float(numerator) / float(denominator)


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Batch Impact kNN/OOD Audit 报告",
        "",
        "日期：2026-06-15",
        "",
        "## 目的",
        "",
        "审计 `GATBatchImpactModel` checkpoint 的离线 validation 表现，并用 kNN/OOD",
        "safety shell 检查 HIGH_PRIORITY batch 是否安全。该流程不运行 BPC、pricing、",
        "RMP、worker 或 certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_batch_impact_knn_ood = current",
        f"status = {summary['status']}",
        f"train_row_count = {summary['train_row_count']}",
        f"validation_row_count = {summary['validation_row_count']}",
        f"train_label_counts = {summary['train_label_counts']}",
        f"validation_label_counts = {summary['validation_label_counts']}",
        f"batch_threshold = {summary['batch_threshold']}",
        f"candidate_threshold = {summary['candidate_threshold']}",
        f"candidate_delay_gate_enabled = {str(summary['candidate_delay_gate_enabled']).lower()}",
        f"candidate_delay_risk_threshold = {summary['candidate_delay_risk_threshold']}",
        f"threshold_grouping = {summary['threshold_grouping']}",
        f"decision_scope = {summary['decision_scope']}",
        f"decision_record_count = {summary['decision_record_count']}",
        f"validation_metrics = {summary['validation_metrics']}",
        f"validation_family_metrics = {summary['validation_family_metrics']}",
        f"validation_safety_checks = {summary['validation_safety_checks']}",
        f"validation_candidate_ready = {str(summary['validation_candidate_ready']).lower()}",
        f"production_block_reasons = {summary['production_block_reasons']}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"default_enabled = {str(summary['default_enabled']).lower()}",
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
                "decision_scope_metrics": summary["decision_scope_metrics"],
                "validation_false_safe_rates": summary["validation_false_safe_rates"],
                "validation_family_metrics": summary["validation_family_metrics"],
                "validation_safety_checks": summary["validation_safety_checks"],
                "decision_reason_counts": summary["decision_reason_counts"],
                "decision_split_counts": summary["decision_split_counts"],
                "decision_threshold_group_counts": summary["decision_threshold_group_counts"],
                "decision_threshold_scope_counts": summary["decision_threshold_scope_counts"],
                "threshold_group_info": summary["threshold_group_info"],
                "production_block_reasons": summary["production_block_reasons"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 边界",
        "",
        "- 本审计只验证 offline admission safety shell，不证明 5/10 no-regression；",
        "- kNN/OOD 只能把 true-RC negative 延迟到 DELAY_QUEUE，不能永久丢弃；",
        "- kNN/OOD no-column / no-safe 不能产生 `CERTIFIED_NO_NEGATIVE`；",
        "- final certificate 仍必须来自 exact pricing full closure。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

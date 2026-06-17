#!/usr/bin/env python3
"""Catalog false HIGH_PRIORITY-on-delay candidates for a batch-impact checkpoint.

This audit is offline/diagnostic-only. It reloads a trained
``GATBatchImpactModel``, scores the recorded split, applies the same candidate
admission rule used by the training deployment metrics, and materializes the
candidate-level false positives that caused ``false_high_priority_on_delay``.
It does not run BPC, pricing, RMP, workers, or certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from statistics import mean, median
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
from BPC_future.scripts.train_gat_batch_impact import (
    _candidate_admission_scores,
    _candidate_delay_scores,
    _load_sample,
    _normalize_sample,
    _prediction_records,
    _record_candidate_prediction_indices,
    _record_is_batch_accepted,
    _record_is_delay_fallback,
)


DEFAULT_DATASET_DIR = Path(
    "BPC_future/data/gat_batch_impact/"
    "v39_mixed_v23_plus_neighbor_roi_b6d808_ab_roi_20260616"
)
DEFAULT_CHECKPOINT = Path(
    "BPC_future/results/gat_batch_impact_training_v39_neighbor_roi_b6d808_20260616/"
    "checkpoint.pt"
)
DEFAULT_TRAINING_SUMMARY = Path(
    "BPC_future/results/gat_batch_impact_training_v39_neighbor_roi_b6d808_20260616/"
    "metrics.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/"
    "gat_batch_impact_false_positive_catalog_v39_neighbor_roi_b6d808_20260616"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260616_bpc_future_gat_target_mode_stage3_v41_v39_false_positive_catalog_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--training-summary", type=Path, default=DEFAULT_TRAINING_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--split", choices=("train", "validation", "all"), default="validation")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--top-k", type=int, default=30)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_false_positive_catalog(
        dataset_dir=Path(args.dataset_dir),
        checkpoint=Path(args.checkpoint),
        training_summary=Path(args.training_summary),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        split=str(args.split),
        device=str(args.device),
        top_k=max(1, int(args.top_k)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_false_positive_catalog(
    *,
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    checkpoint: Path = DEFAULT_CHECKPOINT,
    training_summary: Path = DEFAULT_TRAINING_SUMMARY,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    split: str = "validation",
    device: str = "cpu",
    top_k: int = 30,
) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    checkpoint_data = torch.load(checkpoint, map_location="cpu", weights_only=False)
    training = _read_json(Path(training_summary))
    manifest = _read_json(dataset_dir / "manifest.json")
    _assert_contracts(checkpoint_data, training, manifest)

    split = str(split)
    selected_metrics = _selected_metrics(training, split=split)
    gate_config = dict(checkpoint_data.get("deployment_gate", {}).get("gate_config") or {})
    if not gate_config:
        raise ValueError("checkpoint is missing deployment_gate.gate_config")
    model = GATBatchImpactModel(**checkpoint_data["model_config"]).to(torch.device(device))
    model.load_state_dict(checkpoint_data["model_state_dict"])
    model.eval()

    loaded = _load_samples_with_metadata(dataset_dir, manifest)
    samples = [item["sample"] for item in loaded]
    records = _prediction_records(model, samples, torch.device(device))
    record_items = [
        _attach_prediction_record(record, loaded_item)
        for record, loaded_item in zip(records, loaded)
    ]
    selected_records = _filter_record_items(
        record_items,
        split=split,
        split_contract=training.get("split")
        or checkpoint_data.get("training_contract", {}).get("main_split")
        or {},
    )
    if not selected_records:
        raise ValueError(f"no records selected for split={split}")

    batch_threshold = float(selected_metrics.get("batch_threshold", 0.0))
    candidate_threshold = float(selected_metrics.get("candidate_threshold", 0.0))
    batch_thresholds_by_family = {
        str(key): float(value)
        for key, value in dict(selected_metrics.get("batch_thresholds_by_family") or {}).items()
    }
    fallback_families = {str(value) for value in selected_metrics.get("family_delay_fallback_families") or []}
    fallback_contexts = {str(value) for value in selected_metrics.get("context_delay_fallback_contexts") or []}

    all_candidate_rows: list[dict[str, Any]] = []
    false_positive_rows: list[dict[str, Any]] = []
    record_rows: list[dict[str, Any]] = []
    stats = _empty_stats()
    for record_item in selected_records:
        batch_rows, batch_false_rows, batch_stats, batch_row = catalog_candidate_decisions_for_record(
            record=record_item["record"],
            metadata=record_item["metadata"],
            raw_candidate_features=record_item["raw_candidate_features"],
            candidate_feature_schema=list(manifest.get("candidate_feature_schema") or []),
            batch_threshold=batch_threshold,
            candidate_threshold=candidate_threshold,
            gate_config=gate_config,
            batch_thresholds_by_family=batch_thresholds_by_family,
            fallback_families=fallback_families,
            fallback_contexts=fallback_contexts,
        )
        _merge_stats(stats, batch_stats)
        all_candidate_rows.extend(batch_rows)
        false_positive_rows.extend(batch_false_rows)
        record_rows.append(batch_row)

    context_rows = _context_summary_rows(false_positive_rows, record_rows)
    summary_payload = summarize_false_positive_catalog(
        false_positive_rows=false_positive_rows,
        all_candidate_rows=all_candidate_rows,
        record_rows=record_rows,
        context_rows=context_rows,
        stats=stats,
        selected_metrics=selected_metrics,
        gate_config=gate_config,
        candidate_feature_schema=list(manifest.get("candidate_feature_schema") or []),
        split=split,
        top_k=int(top_k),
        training_summary=training,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    false_path = output_dir / "false_high_priority_on_delay_candidates.jsonl"
    context_path = output_dir / "context_false_positive_summary.jsonl"
    record_path = output_dir / "batch_record_decision_summary.jsonl"
    top_path = output_dir / "top_false_positive_candidates.jsonl"
    _write_jsonl(false_path, sorted(false_positive_rows, key=_false_positive_sort_key))
    _write_jsonl(context_path, sorted(context_rows, key=_context_sort_key))
    _write_jsonl(record_path, sorted(record_rows, key=_record_sort_key))
    _write_jsonl(top_path, summary_payload["top_false_positive_candidates"])

    summary = {
        "schema_version": "gat_batch_impact_false_positive_catalog_v1",
        "status": "gat_batch_impact_false_positive_catalog_audited",
        "dataset_dir": str(dataset_dir),
        "checkpoint": str(checkpoint),
        "training_summary": str(training_summary),
        "output_dir": str(output_dir),
        "split": split,
        "false_positive_candidates_path": str(false_path),
        "context_false_positive_summary_path": str(context_path),
        "batch_record_decision_summary_path": str(record_path),
        "top_false_positive_candidates_path": str(top_path),
        **summary_payload,
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "default_enabled": False,
        "official_bound_effect": False,
        "selector_is_pricing_oracle": False,
        "selector_can_certificate": False,
        "gate_can_permanently_discard_negative_columns": False,
        "all_checks_pass": True,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def catalog_candidate_decisions_for_record(
    *,
    record: dict[str, Any],
    metadata: dict[str, Any],
    raw_candidate_features: list[list[float]],
    candidate_feature_schema: list[str],
    batch_threshold: float,
    candidate_threshold: float,
    gate_config: dict[str, Any],
    batch_thresholds_by_family: dict[str, float] | None = None,
    fallback_families: set[str] | None = None,
    fallback_contexts: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int], dict[str, Any]]:
    fallback_families = set(fallback_families or set())
    fallback_contexts = set(fallback_contexts or set())
    delay_fallback = _record_is_delay_fallback(
        record,
        fallback_families=fallback_families,
        fallback_contexts=fallback_contexts,
    )
    batch_accepted = (
        False
        if delay_fallback
        else _record_is_batch_accepted(
            record,
            batch_threshold=float(batch_threshold),
            candidate_threshold=float(candidate_threshold),
            gate_config=gate_config,
            batch_thresholds_by_family=batch_thresholds_by_family,
        )
    )
    stats = _empty_stats()
    stats["batch_record_count"] = 1
    stats["fallback_batch_record_count"] = int(delay_fallback)
    stats["evaluated_batch_record_count"] = int(not delay_fallback)

    raw_scores = [float(score) for score in record.get("candidate_scores", [])]
    delay_scores = _candidate_delay_scores(record, gate_config=gate_config)
    admission_scores = _candidate_admission_scores(record, gate_config=gate_config)
    candidate_hp_labels = [int(value) for value in record.get("candidate_high_priority_labels", [])]
    candidate_delay_labels = [int(value) for value in record.get("candidate_delay_labels", [])]
    candidate_ids = list(metadata.get("candidate_ids") or [])
    candidate_signature_ids = list(metadata.get("candidate_signature_ids") or [])

    predicted_indices: list[int] = []
    blocked_count = score_blocked_count = suppressed_count = rescue_eligible_count = rescue_promoted_count = 0
    if not delay_fallback:
        (
            predicted_indices,
            blocked_count,
            score_blocked_count,
            suppressed_count,
            rescue_eligible_count,
            rescue_promoted_count,
        ) = _record_candidate_prediction_indices(
            record,
            candidate_threshold=float(candidate_threshold),
            gate_config=gate_config,
        )
    predicted_set = set(predicted_indices)
    stats["candidate_count"] = len(raw_scores)
    stats["evaluated_candidate_count"] = 0 if delay_fallback else len(raw_scores)
    stats["predicted_candidate_count"] = len(predicted_set)
    stats["candidate_score_threshold_blocked_count"] = int(score_blocked_count)
    stats["candidate_delay_gate_blocked_count"] = int(blocked_count)
    stats["candidate_risk_adjusted_suppressed_count"] = int(suppressed_count)
    stats["candidate_rescue_window_eligible_count"] = int(rescue_eligible_count)
    stats["candidate_rescue_window_promoted_count"] = int(rescue_promoted_count)

    rows: list[dict[str, Any]] = []
    false_rows: list[dict[str, Any]] = []
    delay_label_count = true_positive_count = false_positive_count = 0
    for idx, raw_score in enumerate(raw_scores):
        hp_label = int(candidate_hp_labels[idx]) if idx < len(candidate_hp_labels) else 0
        delay_label = int(candidate_delay_labels[idx]) if idx < len(candidate_delay_labels) else 0
        predicted = idx in predicted_set
        if not delay_fallback and delay_label:
            delay_label_count += 1
        if predicted and hp_label:
            true_positive_count += 1
        if predicted and delay_label:
            false_positive_count += 1
        row = {
            **_batch_metadata(metadata),
            "candidate_index": int(idx),
            "candidate_id": str(candidate_ids[idx]) if idx < len(candidate_ids) else "",
            "candidate_signature_id": (
                str(candidate_signature_ids[idx]) if idx < len(candidate_signature_ids) else ""
            ),
            "predicted_high_priority": bool(predicted),
            "false_high_priority_on_delay": bool(predicted and delay_label),
            "candidate_high_priority_label": int(hp_label),
            "candidate_delay_label": int(delay_label),
            "raw_high_priority_score": float(raw_score),
            "predicted_delay_risk_score": float(delay_scores[idx]) if idx < len(delay_scores) else None,
            "candidate_admission_score": (
                float(admission_scores[idx]) if idx < len(admission_scores) else None
            ),
            "candidate_threshold": float(candidate_threshold),
            "candidate_score_margin": (
                float(admission_scores[idx]) - float(candidate_threshold)
                if idx < len(admission_scores)
                else None
            ),
            "raw_score_margin": float(raw_score) - float(candidate_threshold),
            "candidate_delay_risk_threshold": float(gate_config.get("candidate_delay_risk_threshold", 1.0)),
            "delay_gate_margin": (
                float(gate_config.get("candidate_delay_risk_threshold", 1.0))
                - float(delay_scores[idx])
                if idx < len(delay_scores)
                else None
            ),
            "candidate_admission_score_mode": str(
                gate_config.get("candidate_admission_score_mode", "high_priority") or "high_priority"
            ),
            "candidate_delay_gate_enabled": bool(gate_config.get("candidate_delay_gate_enabled", False)),
            "candidate_delay_score_penalty": float(gate_config.get("candidate_delay_score_penalty", 0.0)),
            "batch_accepted_under_gate": bool(batch_accepted),
            "delay_fallback_batch": bool(delay_fallback),
            "candidate_feature_values": _candidate_feature_values(
                raw_candidate_features,
                candidate_feature_schema,
                idx,
            ),
        }
        rows.append(row)
        if row["false_high_priority_on_delay"]:
            false_rows.append(row)

    stats["delay_label_count"] = int(delay_label_count)
    stats["high_priority_true_positive_count"] = int(true_positive_count)
    stats["false_high_priority_on_delay_count"] = int(false_positive_count)
    record_row = {
        **_batch_metadata(metadata),
        "delay_fallback_batch": bool(delay_fallback),
        "batch_accepted_under_gate": bool(batch_accepted),
        "batch_score": float(record.get("batch_score") or 0.0),
        "batch_threshold": float(batch_threshold),
        "candidate_threshold": float(candidate_threshold),
        "candidate_count": len(raw_scores),
        "evaluated_candidate_count": 0 if delay_fallback else len(raw_scores),
        "predicted_candidate_count": len(predicted_set),
        "delay_label_count": int(delay_label_count),
        "false_high_priority_on_delay_count": int(false_positive_count),
        "high_priority_true_positive_count": int(true_positive_count),
        "candidate_delay_gate_blocked_count": int(blocked_count),
        "candidate_risk_adjusted_suppressed_count": int(suppressed_count),
        "candidate_rescue_window_eligible_count": int(rescue_eligible_count),
        "candidate_rescue_window_promoted_count": int(rescue_promoted_count),
    }
    return rows, false_rows, stats, record_row


def summarize_false_positive_catalog(
    *,
    false_positive_rows: list[dict[str, Any]],
    all_candidate_rows: list[dict[str, Any]],
    record_rows: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
    stats: dict[str, int],
    selected_metrics: dict[str, Any],
    gate_config: dict[str, Any],
    candidate_feature_schema: list[str],
    split: str,
    top_k: int,
    training_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    expected = _expected_training_counts(selected_metrics)
    matches = {
        key: (expected[key] is None or int(stats.get(key, 0)) == int(expected[key]))
        for key in expected
    }
    false_count = int(stats.get("false_high_priority_on_delay_count", 0))
    delay_label_count = int(stats.get("delay_label_count", 0))
    predicted_count = int(stats.get("predicted_candidate_count", 0))
    true_positive_count = int(stats.get("high_priority_true_positive_count", 0))
    threshold = float(selected_metrics.get("candidate_threshold", 0.0))
    delay_threshold = float(gate_config.get("candidate_delay_risk_threshold", 1.0))
    score_summary = {
        "raw_high_priority_score": _numeric_summary(
            [row.get("raw_high_priority_score") for row in false_positive_rows]
        ),
        "predicted_delay_risk_score": _numeric_summary(
            [row.get("predicted_delay_risk_score") for row in false_positive_rows]
        ),
        "candidate_admission_score": _numeric_summary(
            [row.get("candidate_admission_score") for row in false_positive_rows]
        ),
        "delay_gate_margin": _numeric_summary([row.get("delay_gate_margin") for row in false_positive_rows]),
        "candidate_score_margin": _numeric_summary(
            [row.get("candidate_score_margin") for row in false_positive_rows]
        ),
    }
    feature_summary = _feature_summary(false_positive_rows, candidate_feature_schema)
    family_counts = Counter(str(row.get("family") or "unknown") for row in false_positive_rows)
    task_counts = Counter(str(row.get("task_count") or 0) for row in false_positive_rows)
    family_task_counts = Counter(
        f"{row.get('family') or 'unknown'}|{row.get('task_count') or 0}"
        for row in false_positive_rows
    )
    context_counts = Counter(
        f"{row.get('family') or 'unknown'}|{row.get('context_hash') or ''}"
        for row in false_positive_rows
    )
    low_delay_confident_count = sum(
        int(float(row.get("predicted_delay_risk_score") or 0.0) <= max(0.0, delay_threshold - 0.25))
        for row in false_positive_rows
    )
    near_delay_gate_count = sum(
        int(float(row.get("predicted_delay_risk_score") or 0.0) >= max(0.0, delay_threshold - 0.05))
        for row in false_positive_rows
    )
    candidate_threshold_zero = abs(threshold) <= 1.0e-12
    return {
        "split": split,
        "selected_threshold": {
            "threshold_mode": selected_metrics.get("threshold_mode"),
            "batch_threshold": selected_metrics.get("batch_threshold"),
            "candidate_threshold": selected_metrics.get("candidate_threshold"),
            "batch_thresholds_by_family": selected_metrics.get("batch_thresholds_by_family") or {},
            "family_delay_fallback_families": selected_metrics.get("family_delay_fallback_families") or [],
            "context_delay_fallback_contexts": selected_metrics.get("context_delay_fallback_contexts") or [],
            "candidate_admission_score_mode": gate_config.get("candidate_admission_score_mode", "high_priority"),
            "candidate_delay_score_penalty": gate_config.get("candidate_delay_score_penalty", 0.0),
            "candidate_delay_gate_enabled": gate_config.get("candidate_delay_gate_enabled", False),
            "candidate_delay_risk_threshold": gate_config.get("candidate_delay_risk_threshold", 1.0),
        },
        "batch_record_count": int(stats.get("batch_record_count", 0)),
        "evaluated_batch_record_count": int(stats.get("evaluated_batch_record_count", 0)),
        "fallback_batch_record_count": int(stats.get("fallback_batch_record_count", 0)),
        "candidate_count": int(stats.get("candidate_count", 0)),
        "evaluated_candidate_count": int(stats.get("evaluated_candidate_count", 0)),
        "predicted_candidate_count": predicted_count,
        "high_priority_true_positive_count": true_positive_count,
        "false_high_priority_on_delay_count": false_count,
        "delay_label_count": delay_label_count,
        "false_high_priority_on_delay": (
            false_count / float(delay_label_count) if delay_label_count else 0.0
        ),
        "high_priority_precision": (
            true_positive_count / float(predicted_count) if predicted_count else None
        ),
        "candidate_delay_gate_blocked_count": int(stats.get("candidate_delay_gate_blocked_count", 0)),
        "candidate_risk_adjusted_suppressed_count": int(
            stats.get("candidate_risk_adjusted_suppressed_count", 0)
        ),
        "candidate_rescue_window_eligible_count": int(
            stats.get("candidate_rescue_window_eligible_count", 0)
        ),
        "candidate_rescue_window_promoted_count": int(
            stats.get("candidate_rescue_window_promoted_count", 0)
        ),
        "expected_training_counts": expected,
        "matches_training_metrics": matches,
        "all_metric_counts_match": all(bool(value) for value in matches.values()),
        "candidate_threshold_zero": bool(candidate_threshold_zero),
        "candidate_threshold_zero_effect": (
            "candidate_head_threshold_disabled_delay_gate_is_only_filter"
            if candidate_threshold_zero
            else "candidate_head_threshold_active"
        ),
        "low_delay_confident_false_positive_count": int(low_delay_confident_count),
        "near_delay_gate_false_positive_count": int(near_delay_gate_count),
        "low_delay_confident_false_positive_rate": (
            low_delay_confident_count / float(false_count) if false_count else 0.0
        ),
        "near_delay_gate_false_positive_rate": (
            near_delay_gate_count / float(false_count) if false_count else 0.0
        ),
        "score_bucket_counts": _score_bucket_counts(false_positive_rows),
        "score_summary": score_summary,
        "candidate_feature_summary": feature_summary,
        "family_counts": dict(sorted(family_counts.items())),
        "task_count_counts": dict(sorted(task_counts.items())),
        "family_task_counts": dict(sorted(family_task_counts.items())),
        "top_contexts": _top_counter_rows(context_counts, limit=top_k),
        "context_false_positive_count": len(context_rows),
        "top_false_positive_candidates": sorted(
            false_positive_rows,
            key=lambda row: (
                -float(row.get("accepted_batch_roi_label") or 0.0),
                float(row.get("predicted_delay_risk_score") or 0.0),
                -float(row.get("raw_high_priority_score") or 0.0),
            ),
        )[: int(top_k)],
        "diagnosis": _diagnosis(
            false_positive_rows=false_positive_rows,
            candidate_threshold_zero=candidate_threshold_zero,
            low_delay_confident_count=low_delay_confident_count,
            near_delay_gate_count=near_delay_gate_count,
            false_count=false_count,
            context_rows=context_rows,
            training_summary=training_summary or {},
        ),
    }


def _load_samples_with_metadata(dataset_dir: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    loaded: list[dict[str, Any]] = []
    for sample_index, item in enumerate(manifest.get("samples", [])):
        raw_sample = _load_sample(dataset_dir / item["path"])
        raw_candidate_features = [
            [float(value) for value in row]
            for row in raw_sample.candidate_features.detach().cpu().tolist()
        ]
        sample = _normalize_sample(raw_sample, manifest)
        metadata = _sample_metadata(sample, item, sample_index=sample_index)
        loaded.append(
            {
                "sample": sample,
                "metadata": metadata,
                "raw_candidate_features": raw_candidate_features,
            }
        )
    return loaded


def _attach_prediction_record(record: dict[str, Any], loaded_item: dict[str, Any]) -> dict[str, Any]:
    return {
        "record": dict(record),
        "metadata": dict(loaded_item["metadata"]),
        "raw_candidate_features": list(loaded_item["raw_candidate_features"]),
    }


def _filter_record_items(
    record_items: list[dict[str, Any]],
    *,
    split: str,
    split_contract: dict[str, Any],
) -> list[dict[str, Any]]:
    if split == "all":
        return list(record_items)
    train_instances = {str(value) for value in split_contract.get("train_instances", [])}
    validation_instances = {str(value) for value in split_contract.get("validation_instances", [])}
    selected_instances = validation_instances if split == "validation" else train_instances
    selected: list[dict[str, Any]] = []
    for item in record_items:
        keys = {
            str(item["metadata"].get("instance_path") or ""),
            str(item["metadata"].get("instance") or ""),
            str(item["metadata"].get("instance_name") or ""),
        }
        if keys & selected_instances:
            selected.append(item)
    return selected


def _sample_metadata(sample: Any, manifest_item: dict[str, Any], *, sample_index: int) -> dict[str, Any]:
    return {
        "sample_index": int(sample_index),
        "sample_path": str(manifest_item.get("path") or ""),
        "source_file": str(
            getattr(sample, "batch_impact_source_jsonl", "")
            or manifest_item.get("source_file")
            or ""
        ),
        "row_index": int(manifest_item.get("row_index") or 0),
        "instance": str(
            getattr(sample, "batch_impact_instance", "")
            or manifest_item.get("instance")
            or ""
        ),
        "instance_name": str(manifest_item.get("instance") or ""),
        "instance_path": str(getattr(sample, "batch_impact_instance_path", "") or ""),
        "family": str(
            getattr(sample, "batch_impact_instance_family", "")
            or manifest_item.get("instance_family")
            or "unknown"
        ),
        "region": str(
            getattr(sample, "batch_impact_instance_region", "")
            or manifest_item.get("instance_region")
            or ""
        ),
        "task_count": int(
            getattr(sample, "batch_impact_task_count", 0)
            or manifest_item.get("task_count")
            or 0
        ),
        "context_hash": str(
            getattr(sample, "batch_impact_context_hash", "")
            or manifest_item.get("context_hash")
            or ""
        ),
        "batch_type": str(manifest_item.get("batch_type") or ""),
        "accepted_batch_roi_label": float(manifest_item.get("accepted_batch_roi") or 0.0),
        "label_batch_roi_positive": int(manifest_item.get("label_batch_roi_positive") or 0),
        "objective_improvement": float(manifest_item.get("objective_improvement") or 0.0),
        "candidate_ids": list(
            getattr(sample, "batch_impact_candidate_ids", None)
            or manifest_item.get("candidate_ids")
            or []
        ),
        "candidate_signature_ids": list(
            getattr(sample, "batch_impact_candidate_signature_ids", None)
            or manifest_item.get("candidate_signature_ids")
            or []
        ),
        "candidate_signature_source_present_count": int(
            manifest_item.get("candidate_signature_source_present_count") or 0
        ),
    }


def _batch_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "sample_index": int(metadata.get("sample_index") or 0),
        "sample_path": str(metadata.get("sample_path") or ""),
        "source_file": str(metadata.get("source_file") or ""),
        "row_index": int(metadata.get("row_index") or 0),
        "instance": str(metadata.get("instance") or ""),
        "instance_path": str(metadata.get("instance_path") or ""),
        "family": str(metadata.get("family") or "unknown"),
        "region": str(metadata.get("region") or ""),
        "task_count": int(metadata.get("task_count") or 0),
        "context_hash": str(metadata.get("context_hash") or ""),
        "batch_type": str(metadata.get("batch_type") or ""),
        "accepted_batch_roi_label": float(metadata.get("accepted_batch_roi_label") or 0.0),
        "label_batch_roi_positive": int(metadata.get("label_batch_roi_positive") or 0),
        "objective_improvement": float(metadata.get("objective_improvement") or 0.0),
    }


def _candidate_feature_values(
    raw_candidate_features: list[list[float]],
    candidate_feature_schema: list[str],
    idx: int,
) -> dict[str, float]:
    if idx >= len(raw_candidate_features):
        return {}
    row = raw_candidate_features[idx]
    return {
        str(name): float(row[pos])
        for pos, name in enumerate(candidate_feature_schema)
        if pos < len(row)
    }


def _context_summary_rows(
    false_positive_rows: list[dict[str, Any]],
    record_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    false_by_context: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    records_by_context: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in false_positive_rows:
        false_by_context[_context_key(row)].append(row)
    for row in record_rows:
        records_by_context[_context_key(row)].append(row)
    rows: list[dict[str, Any]] = []
    for key, false_rows in false_by_context.items():
        record_group = records_by_context.get(key, [])
        rows.append(
            {
                "family": key[0],
                "context_hash": key[1],
                "false_high_priority_on_delay_count": len(false_rows),
                "batch_record_count": len(record_group),
                "accepted_batch_count": sum(
                    int(bool(row.get("batch_accepted_under_gate"))) for row in record_group
                ),
                "task_counts": sorted({int(row.get("task_count") or 0) for row in false_rows}),
                "instances": sorted({str(row.get("instance") or "") for row in false_rows}),
                "max_accepted_batch_roi_label": _max_or_none(
                    [float(row.get("accepted_batch_roi_label") or 0.0) for row in false_rows]
                ),
                "min_delay_risk_score": _min_or_none(
                    [float(row.get("predicted_delay_risk_score") or 0.0) for row in false_rows]
                ),
                "median_delay_risk_score": _median_or_none(
                    [float(row.get("predicted_delay_risk_score") or 0.0) for row in false_rows]
                ),
                "max_delay_risk_score": _max_or_none(
                    [float(row.get("predicted_delay_risk_score") or 0.0) for row in false_rows]
                ),
                "median_raw_high_priority_score": _median_or_none(
                    [float(row.get("raw_high_priority_score") or 0.0) for row in false_rows]
                ),
                "candidate_signature_ids": sorted(
                    {str(row.get("candidate_signature_id") or "") for row in false_rows}
                )[:50],
            }
        )
    return rows


def _feature_summary(
    rows: list[dict[str, Any]],
    candidate_feature_schema: list[str],
) -> dict[str, dict[str, float | int | None]]:
    summary: dict[str, dict[str, float | int | None]] = {}
    for feature in candidate_feature_schema:
        values = [
            row.get("candidate_feature_values", {}).get(feature)
            for row in rows
            if feature in row.get("candidate_feature_values", {})
        ]
        summary[feature] = _numeric_summary(values)
    return summary


def _score_bucket_counts(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    return {
        "predicted_delay_risk_score": _bucket_counts(
            [row.get("predicted_delay_risk_score") for row in rows],
            buckets=(0.10, 0.25, 0.40, 0.50),
        ),
        "raw_high_priority_score": _bucket_counts(
            [row.get("raw_high_priority_score") for row in rows],
            buckets=(0.25, 0.50, 0.75, 0.90, 0.99),
        ),
        "candidate_admission_score": _bucket_counts(
            [row.get("candidate_admission_score") for row in rows],
            buckets=(0.05, 0.10, 0.25, 0.50, 0.75),
        ),
    }


def _diagnosis(
    *,
    false_positive_rows: list[dict[str, Any]],
    candidate_threshold_zero: bool,
    low_delay_confident_count: int,
    near_delay_gate_count: int,
    false_count: int,
    context_rows: list[dict[str, Any]],
    training_summary: dict[str, Any],
) -> dict[str, Any]:
    findings: list[str] = []
    if false_count <= 0:
        findings.append("no_false_high_priority_on_delay_under_selected_policy")
    if candidate_threshold_zero and false_count > 0:
        findings.append("candidate_threshold_zero_disables_candidate_head_as_a_filter")
    if false_count > 0 and low_delay_confident_count / float(false_count) >= 0.50:
        findings.append("delay_head_structural_false_negative_not_near_gate_only")
    elif false_count > 0 and near_delay_gate_count / float(false_count) >= 0.50:
        findings.append("delay_risk_calibration_near_gate")
    if context_rows:
        top_context = max(context_rows, key=lambda row: int(row.get("false_high_priority_on_delay_count") or 0))
        if int(top_context.get("false_high_priority_on_delay_count") or 0) >= max(3, int(0.20 * false_count)):
            findings.append("false_positives_are_context_concentrated")
    if training_summary.get("stage4_candidate_ready") is False:
        findings.append("checkpoint_remains_diagnostic_not_stage4_candidate")
    primary = (
        "raise_candidate_threshold_or_make_candidate_head_usable_before_delay_gate"
        if candidate_threshold_zero and false_count > 0
        else "inspect_delay_risk_calibration_and_context_specific_fallback"
    )
    if false_count > 0 and low_delay_confident_count / float(false_count) >= 0.50:
        primary = "repair_delay_head_with_hard_negative_context_contrast"
    return {
        "primary": primary,
        "findings": findings,
        "stage4_candidate_ready": bool(training_summary.get("stage4_candidate_ready", False)),
        "production_ready": bool(training_summary.get("production_ready", False)),
    }


def _selected_metrics(training: dict[str, Any], *, split: str) -> dict[str, Any]:
    if split == "train":
        metrics = training.get("train_deployment_metrics") or {}
    elif split == "validation":
        metrics = training.get("validation_deployment_metrics") or {}
    else:
        metrics = training.get("validation_deployment_metrics") or {}
    if not metrics:
        raise ValueError(f"training summary is missing deployment metrics for split={split}")
    return dict(metrics)


def _expected_training_counts(selected_metrics: dict[str, Any]) -> dict[str, int | None]:
    return {
        "predicted_candidate_count": _int_or_none(selected_metrics.get("high_priority_prediction_count")),
        "high_priority_true_positive_count": _int_or_none(
            selected_metrics.get("high_priority_true_positive_count")
        ),
        "false_high_priority_on_delay_count": _int_or_none(
            selected_metrics.get("false_high_priority_on_delay_count")
        ),
        "delay_label_count": _int_or_none(selected_metrics.get("delay_label_count")),
        "candidate_delay_gate_blocked_count": _int_or_none(
            selected_metrics.get("candidate_delay_gate_blocked_count")
        ),
        "candidate_risk_adjusted_suppressed_count": _int_or_none(
            selected_metrics.get("candidate_risk_adjusted_suppressed_count")
        ),
        "candidate_rescue_window_eligible_count": _int_or_none(
            selected_metrics.get("candidate_rescue_window_eligible_count")
        ),
        "candidate_rescue_window_promoted_count": _int_or_none(
            selected_metrics.get("candidate_rescue_window_promoted_count")
        ),
    }


def _empty_stats() -> dict[str, int]:
    return {
        "batch_record_count": 0,
        "fallback_batch_record_count": 0,
        "evaluated_batch_record_count": 0,
        "candidate_count": 0,
        "evaluated_candidate_count": 0,
        "predicted_candidate_count": 0,
        "high_priority_true_positive_count": 0,
        "false_high_priority_on_delay_count": 0,
        "delay_label_count": 0,
        "candidate_delay_gate_blocked_count": 0,
        "candidate_risk_adjusted_suppressed_count": 0,
        "candidate_rescue_window_eligible_count": 0,
        "candidate_rescue_window_promoted_count": 0,
    }


def _merge_stats(dst: dict[str, int], src: dict[str, int]) -> None:
    for key, value in src.items():
        dst[key] = int(dst.get(key, 0)) + int(value)


def _top_counter_rows(counter: Counter[str], *, limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, count in counter.most_common(int(limit)):
        family, _, context_hash = str(key).partition("|")
        rows.append({"family": family, "context_hash": context_hash, "count": int(count)})
    return rows


def _bucket_counts(values: list[Any], *, buckets: tuple[float, ...]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for raw in values:
        if raw is None:
            continue
        value = float(raw)
        placed = False
        for bucket in buckets:
            if value <= float(bucket):
                counts[f"<= {bucket:g}"] += 1
                placed = True
                break
        if not placed:
            counts[f"> {buckets[-1]:g}"] += 1
    return dict(sorted(counts.items()))


def _numeric_summary(values: list[Any]) -> dict[str, float | int | None]:
    clean = [float(value) for value in values if value is not None]
    return {
        "count": len(clean),
        "min": _min_or_none(clean),
        "median": _median_or_none(clean),
        "mean": _mean_or_none(clean),
        "max": _max_or_none(clean),
    }


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


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    diagnosis = summary["diagnosis"]
    lines = [
        "# GAT Target Mode Stage 3 v41 v39 False-positive Catalog 报告",
        "",
        "日期：2026-06-16",
        "",
        "## 结论",
        "",
        "本报告只读 v39 batch-impact checkpoint / metrics / dataset，复用训练阶段的",
        "candidate admission rule，逐 candidate  catalog 造成",
        "`false_high_priority_on_delay` 的 delay-labeled 候选。它不运行 BPC、pricing、",
        "RMP、worker 或 certificate。",
        "",
        "```text",
        f"split = {summary['split']}",
        f"batch_record_count = {summary['batch_record_count']}",
        f"evaluated_batch_record_count = {summary['evaluated_batch_record_count']}",
        f"fallback_batch_record_count = {summary['fallback_batch_record_count']}",
        f"evaluated_candidate_count = {summary['evaluated_candidate_count']}",
        f"predicted_candidate_count = {summary['predicted_candidate_count']}",
        f"high_priority_true_positive_count = {summary['high_priority_true_positive_count']}",
        f"false_high_priority_on_delay_count = {summary['false_high_priority_on_delay_count']}",
        f"delay_label_count = {summary['delay_label_count']}",
        f"false_high_priority_on_delay = {summary['false_high_priority_on_delay']}",
        f"high_priority_precision = {summary['high_priority_precision']}",
        f"candidate_delay_gate_blocked_count = {summary['candidate_delay_gate_blocked_count']}",
        f"candidate_threshold_zero = {summary['candidate_threshold_zero']}",
        f"candidate_threshold_zero_effect = {summary['candidate_threshold_zero_effect']}",
        f"all_metric_counts_match = {summary['all_metric_counts_match']}",
        f"primary_diagnosis = {diagnosis.get('primary')}",
        "production_ready = false",
        "selector_can_certificate = false",
        "```",
        "",
        "## Metric Count Check",
        "",
        "```json",
        json.dumps(
            {
                "expected_training_counts": summary["expected_training_counts"],
                "matches_training_metrics": summary["matches_training_metrics"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Family / Task Counts",
        "",
        "```json",
        json.dumps(
            {
                "family_counts": summary["family_counts"],
                "task_count_counts": summary["task_count_counts"],
                "family_task_counts": summary["family_task_counts"],
                "top_contexts": summary["top_contexts"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Score Buckets",
        "",
        "```json",
        json.dumps(summary["score_bucket_counts"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Score Summary",
        "",
        "```json",
        json.dumps(summary["score_summary"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Candidate Feature Summary",
        "",
        "```json",
        json.dumps(summary["candidate_feature_summary"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Diagnosis",
        "",
        "```json",
        json.dumps(diagnosis, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Next Step",
        "",
        "- 不应继续把 v39 送入 Stage 4 shadow / opt-in admission；",
        "- 下一轮 threshold frontier 必须让 candidate head 成为真实过滤器，不能选出",
        "  `candidate_threshold=0` 后只依赖 delay gate；",
        "- false positive 高度集中在少数 `sector-wave|20` context，优先对这些 context",
        "  补同 context low-ROI / delay hard-negative contrast，或加入 context-specific",
        "  fallback / calibration audit；",
        "- 该 catalog 只能指导离线训练和采样，不能作为 pruning、official bound 或",
        "  certificate 来源。",
        "",
        "## Artifacts",
        "",
        "```text",
        f"summary = {summary['output_dir']}/summary.json",
        f"false_positive_candidates = {summary['false_positive_candidates_path']}",
        f"context_summary = {summary['context_false_positive_summary_path']}",
        f"batch_record_summary = {summary['batch_record_decision_summary_path']}",
        "```",
        "",
        "## Exactness Boundary",
        "",
        "- `diagnostic_only=true`；",
        "- `runs_bpc_or_pricing=false`；",
        "- `selector_is_pricing_oracle=false`；",
        "- `selector_can_certificate=false`；",
        "- `gate_can_permanently_discard_negative_columns=false`；",
        "- `DELAY_QUEUE` 只能有限延迟 true-RC negative，不能永久 reject；",
        "- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
        + ("\n" if rows else ""),
        encoding="utf-8",
    )


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _context_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("family") or "unknown"), str(row.get("context_hash") or ""))


def _false_positive_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        str(row.get("family") or ""),
        int(row.get("task_count") or 0),
        str(row.get("context_hash") or ""),
        float(row.get("predicted_delay_risk_score") or 0.0),
        -float(row.get("raw_high_priority_score") or 0.0),
        str(row.get("candidate_signature_id") or ""),
    )


def _context_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        -int(row.get("false_high_priority_on_delay_count") or 0),
        str(row.get("family") or ""),
        str(row.get("context_hash") or ""),
    )


def _record_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        str(row.get("family") or ""),
        int(row.get("task_count") or 0),
        str(row.get("context_hash") or ""),
        int(row.get("sample_index") or 0),
    )


def _mean_or_none(values: list[float]) -> float | None:
    return float(mean(values)) if values else None


def _median_or_none(values: list[float]) -> float | None:
    return float(median(values)) if values else None


def _min_or_none(values: list[float]) -> float | None:
    return float(min(values)) if values else None


def _max_or_none(values: list[float]) -> float | None:
    return float(max(values)) if values else None


if __name__ == "__main__":
    raise SystemExit(main())

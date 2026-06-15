#!/usr/bin/env python3
"""Audit worker-ROI GAT with a kNN/OOD safety shell.

This offline diagnostic is for the paired worker A/B trajectory-ROI target.
It never runs BPC, pricing, RMP, workers, or certificates.  The learned model
may only nominate HIGH_PRIORITY candidates; non-nominated true-RC negative
candidates must remain reachable through DELAY_QUEUE.
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

from BPC_future.learning.column_selector import (
    SELECTOR_CLASS_ABSTAIN,
    SELECTOR_CLASS_ADD,
    ContextAwareColumnSelector,
)
from BPC_future.scripts.audit_cbf_delay_queue_knn_ood_scheduler import (
    _nearest_safe_distance,
    _neighbor_unsafe_fraction,
    _safe_radius_threshold,
)
from BPC_future.scripts.train_gnn_column_selector import _load_sample, _normalize_sample


DEFAULT_DATASET_DIR = Path("BPC_future/data/gat_worker_roi/v31_source_recovered_20260615")
DEFAULT_CHECKPOINT = Path("BPC_future/data/gat_worker_roi/v31_source_recovered_20260615/gat_worker_roi.pt")
DEFAULT_TRAINING_SUMMARY = Path("BPC_future/results/gat_worker_roi_training_v31_20260615/summary.json")
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/gat_worker_roi_knn_ood_audit_v31_20260615")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/20260615_bpc_future_gat_worker_roi_knn_ood_audit_v31_zh.md"
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
    parser.add_argument("--min-add-precision", type=float, default=0.95)
    parser.add_argument("--min-add-recall", type=float, default=0.65)
    parser.add_argument("--min-add-f0p5", type=float, default=0.90)
    parser.add_argument("--max-false-high-priority-rate", type=float, default=0.02)
    parser.add_argument("--max-false-positive-contexts", type=int, default=0)
    parser.add_argument("--max-validation-false-safe-rate", type=float, default=0.02)
    parser.add_argument("--min-coverage", type=float, default=0.0)
    parser.add_argument("--decision-scope", choices=("validation", "all"), default="validation")
    parser.add_argument(
        "--threshold-selection",
        choices=("calibrated", "zero_fp"),
        default="calibrated",
        help="Use the training calibrated threshold by default; zero_fp is stricter and optional.",
    )
    parser.add_argument(
        "--threshold-grouping",
        choices=("global", "scale", "family", "scale_family"),
        default="global",
        help=(
            "Calibrate the probability threshold and kNN/OOD shell globally or "
            "inside scale/family groups. Sparse or single-label groups fall back "
            "to the global shell."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_worker_roi_knn_ood(
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
        min_add_precision=float(args.min_add_precision),
        min_add_recall=float(args.min_add_recall),
        min_add_f0p5=float(args.min_add_f0p5),
        max_false_high_priority_rate=float(args.max_false_high_priority_rate),
        max_false_positive_contexts=int(args.max_false_positive_contexts),
        max_validation_false_safe_rate=float(args.max_validation_false_safe_rate),
        min_coverage=float(args.min_coverage),
        decision_scope=str(args.decision_scope),
        threshold_selection=str(args.threshold_selection),
        threshold_grouping=str(args.threshold_grouping),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_worker_roi_knn_ood(
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
    min_add_precision: float = 0.95,
    min_add_recall: float = 0.65,
    min_add_f0p5: float = 0.90,
    max_false_high_priority_rate: float = 0.02,
    max_false_positive_contexts: int = 0,
    max_validation_false_safe_rate: float = 0.02,
    min_coverage: float = 0.0,
    decision_scope: str = "validation",
    threshold_selection: str = "calibrated",
    threshold_grouping: str = "global",
) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    checkpoint_data = torch.load(checkpoint, map_location="cpu", weights_only=False)
    training = json.loads(Path(training_summary).read_text(encoding="utf-8"))
    manifest = json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    _assert_contracts(checkpoint_data, training, manifest)

    model = ContextAwareColumnSelector(**checkpoint_data["model_config"]).to(torch.device(device))
    model.load_state_dict(checkpoint_data["model_state_dict"])
    model.eval()
    records = _score_dataset(
        dataset_dir=dataset_dir,
        manifest=manifest,
        model=model,
        device=torch.device(device),
    )
    split = training.get("split") or checkpoint_data.get("training", {}).get("split") or {}
    train_instances = set(split.get("train_instances") or [])
    validation_instances = set(split.get("validation_instances") or [])
    train_records = [record for record in records if record["instance"] in train_instances]
    validation_records = [record for record in records if record["instance"] in validation_instances]
    if not train_records or not validation_records:
        raise ValueError("training summary split does not match worker ROI dataset")

    fallback_threshold = float(
        training.get("calibrated_add_threshold")
        or checkpoint_data.get("deployment_guard", {}).get("calibrated_add_threshold")
        or 0.5
    )
    guard_model = _build_guard_model(
        train_records=train_records,
        threshold_grouping=str(threshold_grouping),
        safe_radius_quantile=float(safe_radius_quantile),
        safe_radius_multiplier=float(safe_radius_multiplier),
        fallback_threshold=fallback_threshold,
        threshold_selection=str(threshold_selection),
        knn_k=int(knn_k),
    )
    global_guard = guard_model["global"]
    threshold = float(global_guard["threshold"])
    safe_radius = global_guard["safe_radius"]
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
    if str(decision_scope) == "all":
        emit_records = records
    else:
        emit_records = validation_records
    decision_records = []
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
    validation_metrics = _metrics(validation_decisions)
    decision_scope_metrics = _metrics(decision_records)
    validation_safety_shell_metrics = _safety_shell_metrics(validation_decisions)
    decision_scope_safety_shell_metrics = _safety_shell_metrics(decision_records)
    false_rate = validation_metrics["false_high_priority_rate"]
    validation_false_safe_rates = _validation_false_safe_rates(validation_safety_shell_metrics)
    validation_false_safe_rate = validation_false_safe_rates["max_observed_false_safe_rate"]
    validation_coverage = validation_safety_shell_metrics["coverage"]
    validation_candidate_ready = bool(
        validation_metrics["predicted_high_priority"] >= int(min_validation_high_priority)
        and (validation_metrics["add_precision"] is not None)
        and validation_metrics["add_precision"] >= float(min_add_precision)
        and (validation_metrics["add_recall"] is not None)
        and validation_metrics["add_recall"] >= float(min_add_recall)
        and (validation_metrics["add_f0p5"] is not None)
        and validation_metrics["add_f0p5"] >= float(min_add_f0p5)
        and false_rate <= float(max_false_high_priority_rate)
        and validation_metrics["false_positive_context_count"] <= int(max_false_positive_contexts)
        and (
            validation_false_safe_rate is None
            or validation_false_safe_rate <= float(max_validation_false_safe_rate)
        )
        and (validation_coverage is not None)
        and validation_coverage >= float(min_coverage)
    )
    production_block_reasons: list[str] = []
    if validation_metrics["predicted_high_priority"] < int(min_validation_high_priority):
        production_block_reasons.append("validation_high_priority_below_min")
    if (
        validation_metrics["add_precision"] is None
        or validation_metrics["add_precision"] < float(min_add_precision)
    ):
        production_block_reasons.append("validation_add_precision_below_min")
    if validation_metrics["add_recall"] is None or validation_metrics["add_recall"] < float(min_add_recall):
        production_block_reasons.append("validation_add_recall_below_min")
    if validation_metrics["add_f0p5"] is None or validation_metrics["add_f0p5"] < float(min_add_f0p5):
        production_block_reasons.append("validation_add_f0p5_below_min")
    if false_rate > float(max_false_high_priority_rate):
        production_block_reasons.append("validation_false_high_priority_rate_above_max")
    if validation_metrics["false_positive_context_count"] > int(max_false_positive_contexts):
        production_block_reasons.append("validation_false_positive_contexts_above_max")
    if (
        validation_false_safe_rate is not None
        and validation_false_safe_rate > float(max_validation_false_safe_rate)
    ):
        production_block_reasons.append("validation_false_safe_rate_above_max")
    if validation_coverage is None or validation_coverage < float(min_coverage):
        production_block_reasons.append("validation_coverage_below_min")
    if not validation_candidate_ready:
        production_block_reasons.append("validation_candidate_not_ready")

    summary = {
        "schema_version": "gat_worker_roi_knn_ood_audit_v1",
        "status": "gat_worker_roi_knn_ood_audited",
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
        "safe_radius": safe_radius,
        "threshold_selection": str(threshold_selection),
        "threshold_grouping": str(threshold_grouping),
        "threshold_group_info": _serializable_guard_model(guard_model),
        "knn_k": int(knn_k),
        "max_neighbor_delay_fraction": float(max_neighbor_delay_fraction),
        "safe_radius_quantile": float(safe_radius_quantile),
        "safe_radius_multiplier": float(safe_radius_multiplier),
        "min_add_precision": float(min_add_precision),
        "min_add_recall": float(min_add_recall),
        "min_add_f0p5": float(min_add_f0p5),
        "max_false_high_priority_rate": float(max_false_high_priority_rate),
        "max_false_positive_contexts": int(max_false_positive_contexts),
        "max_validation_false_safe_rate": float(max_validation_false_safe_rate),
        "min_coverage": float(min_coverage),
        "decision_scope": str(decision_scope),
        "decision_record_count": len(decision_records),
        "validation_metrics": validation_metrics,
        "decision_scope_metrics": decision_scope_metrics,
        "validation_safety_shell_metrics": validation_safety_shell_metrics,
        "decision_scope_safety_shell_metrics": decision_scope_safety_shell_metrics,
        "validation_false_safe_rates": validation_false_safe_rates,
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
        "official_bound_effect": False,
        "selector_is_pricing_oracle": False,
        "selector_can_certificate": False,
        "gate_can_permanently_discard_negative_columns": False,
        "negative_columns_must_remain_eventually_reachable": True,
        "unsafe_negative_decision": "DELAY_QUEUE",
        "safe_negative_decision": "HIGH_PRIORITY",
        "target_label": "paired_worker_ab_trajectory_roi",
        "all_checks_pass": True,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "decision_records.jsonl").write_text(
        "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in decision_records) + "\n",
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
    if checkpoint_data.get("target_label") != "paired_worker_ab_trajectory_roi":
        raise ValueError("worker ROI checkpoint must target paired_worker_ab_trajectory_roi")
    if checkpoint_data.get("trajectory_contract", {}).get("labels_from_rc_or_gate"):
        raise ValueError("worker ROI checkpoint labels must not come from rc or gates")
    if checkpoint_data.get("trajectory_contract", {}).get("certificate_source"):
        raise ValueError("worker ROI checkpoint must not be a certificate source")
    if checkpoint_data.get("trajectory_contract", {}).get("pricing_oracle"):
        raise ValueError("worker ROI checkpoint must not be a pricing oracle")
    if manifest.get("schema_version") != "gat_worker_roi_graph_dataset_manifest_v1":
        raise ValueError("worker ROI dataset manifest schema mismatch")
    if training.get("target_label") != "paired_worker_ab_trajectory_roi":
        raise ValueError("worker ROI training summary target label mismatch")
    if training.get("production_ready"):
        raise ValueError("worker ROI audit expects a non-production diagnostic checkpoint")


def _score_dataset(
    *,
    dataset_dir: Path,
    manifest: dict[str, Any],
    model: ContextAwareColumnSelector,
    device: torch.device,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    source_rows = _load_source_rows(manifest)
    capture_context_cache: dict[tuple[str, str], dict[str, Any]] = {}
    with torch.no_grad():
        for item in manifest.get("samples", []):
            source_row = source_rows.get(int(item.get("row_index", -1)), {})
            capture_context = _capture_context_for_source_row(
                source_row,
                fallback_context_hash=str(item.get("context_hash") or ""),
                cache=capture_context_cache,
            )
            sample = _normalize_sample(_load_sample(dataset_dir / item["path"]), manifest).to(device)
            output = model(
                sample,
                sample.candidate_task_membership,
                sample.candidate_features,
                sample.context_features,
            )
            logits = output["logits"]
            add_margin = logits[:, SELECTOR_CLASS_ADD] - logits[:, SELECTOR_CLASS_ABSTAIN]
            score = torch.sigmoid(add_margin).detach().cpu()
            embedding = output["candidate_embedding"].detach().cpu()
            labels = sample.y_selector.detach().cpu().long()
            for idx in range(int(labels.numel())):
                label_positive = 1 if int(labels[idx].item()) == SELECTOR_CLASS_ADD else 0
                records.append(
                    {
                        "row_index": int(item.get("row_index", len(records))),
                        "name": str(item.get("name", "")),
                        "instance": str(item.get("instance", "")),
                        "instance_family": str(item.get("instance_family", "")),
                        "instance_region": str(item.get("instance_region", "")),
                        "instance_task_count": _record_task_count(
                            {
                                "name": str(item.get("name", "")),
                                "source_file": str(source_row.get("source_file") or ""),
                                "instance": str(item.get("instance", "")),
                            }
                        ),
                        "roi_class": str(item.get("roi_class", "")),
                        "context_hash": str(item.get("context_hash", "")),
                        "expected_context_hash": str(
                            source_row.get("expected_context_hash")
                            or item.get("context_hash")
                            or ""
                        ),
                        "capture_pricing_kind": str(
                            source_row.get("capture_pricing_kind")
                            or capture_context.get("pricing_kind")
                            or ""
                        ),
                        "true_dual_hash": str(
                            source_row.get("true_dual_hash")
                            or capture_context.get("true_dual_hash")
                            or ""
                        ),
                        "cut_hash": str(
                            source_row.get("cut_hash") or capture_context.get("cut_hash") or ""
                        ),
                        "branch_hash": str(
                            source_row.get("branch_hash") or capture_context.get("branch_hash") or ""
                        ),
                        "forbidden_signature_hash": str(
                            source_row.get("forbidden_signature_hash")
                            or capture_context.get("forbidden_signature_hash")
                            or ""
                        ),
                        "active_hash_before": str(
                            source_row.get("active_hash_before")
                            or capture_context.get("active_hash_before")
                            or ""
                        ),
                        "active_task_set_hash": str(
                            source_row.get("active_task_set_hash")
                            or capture_context.get("active_task_set_hash")
                            or ""
                        ),
                        "active_basis_snapshot_hash": str(
                            source_row.get("active_basis_snapshot_hash")
                            or capture_context.get("active_basis_snapshot_hash")
                            or ""
                        ),
                        "pool_signature_hash": str(
                            source_row.get("pool_signature_hash")
                            or capture_context.get("pool_signature_hash")
                            or ""
                        ),
                        "pool_task_set_hash": str(
                            source_row.get("pool_task_set_hash")
                            or capture_context.get("pool_task_set_hash")
                            or ""
                        ),
                        "pool_active_task_set_hash_before": str(
                            source_row.get("pool_active_task_set_hash_before")
                            or capture_context.get("pool_active_task_set_hash_before")
                            or ""
                        ),
                        "target_sequence": _int_list(source_row.get("target_sequence")),
                        "target_arc_option_sequence": _str_list(
                            source_row.get("target_arc_option_sequence")
                        ),
                        "target_sortie_traces": _materialization_traces_for_source_row(
                            source_row,
                            capture_context,
                        ),
                        "source_file": str(source_row.get("source_file") or ""),
                        "roi_candidate_key": str(source_row.get("roi_candidate_key") or ""),
                        "worker_target_sequence_negative": bool(
                            source_row.get("worker_target_sequence_negative")
                        ),
                        "worker_target_sequence_materialized": bool(
                            source_row.get("worker_target_sequence_materialized")
                        ),
                        "label_worker_roi_positive": label_positive,
                        "score": float(score[idx].item()),
                        "embedding": [float(v) for v in embedding[idx].tolist()],
                    }
                )
    return records


def _capture_context_for_source_row(
    source_row: dict[str, Any],
    *,
    fallback_context_hash: str,
    cache: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    source_file = str(source_row.get("source_file") or "").strip()
    context_hash = str(
        source_row.get("expected_context_hash")
        or source_row.get("context_hash")
        or fallback_context_hash
        or ""
    ).strip()
    if not source_file or not context_hash:
        return {}
    key = (source_file, context_hash)
    if key in cache:
        return cache[key]
    path = Path(source_file)
    if not path.is_file():
        cache[key] = {}
        return {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("event") != "journey_counterfactual_replay_capture":
            continue
        if str(event.get("context_hash") or "").strip() != context_hash:
            continue
        cache[key] = event
        return event
    cache[key] = {}
    return {}


def _materialization_traces_for_source_row(
    source_row: dict[str, Any],
    capture_context: dict[str, Any],
) -> list[dict[str, Any]]:
    explicit = source_row.get("target_sortie_traces")
    if _is_materialization_trace_list(explicit):
        return list(explicit)
    samples = source_row.get("worker_returned_candidate_sequence_samples") or []
    target_sequence = _int_list(source_row.get("target_sequence"))
    for journey in capture_context.get("returned_journeys") or []:
        if not isinstance(journey, dict):
            continue
        if not _journey_matches_source_target(journey, samples=samples, target_sequence=target_sequence):
            continue
        traces = _materialization_traces_from_journey(journey)
        if traces:
            return traces
    return []


def _is_materialization_trace_list(value: Any) -> bool:
    if not isinstance(value, list):
        return False
    return all(
        isinstance(item, dict)
        and isinstance(item.get("sequence"), list)
        and "start_time" in item
        and isinstance(item.get("arc_option_sequence"), list)
        for item in value
    )


def _journey_matches_source_target(
    journey: dict[str, Any],
    *,
    samples: Any,
    target_sequence: list[int],
) -> bool:
    sequence = journey.get("sequence")
    if isinstance(samples, list):
        for sample in samples:
            if sequence == sample:
                return True
    flat_sequence: list[int] = []
    if isinstance(sequence, list):
        for sortie in sequence:
            if isinstance(sortie, list):
                flat_sequence.extend(_int_list(sortie))
    if target_sequence and flat_sequence == target_sequence:
        return True
    trip_sequence: list[int] = []
    for trip in journey.get("trips") or []:
        if isinstance(trip, dict):
            trip_sequence.extend(_int_list(trip.get("tasks")))
    return bool(target_sequence and trip_sequence == target_sequence)


def _materialization_traces_from_journey(journey: dict[str, Any]) -> list[dict[str, Any]]:
    traces: list[dict[str, Any]] = []
    for trip in journey.get("trips") or []:
        if not isinstance(trip, dict):
            continue
        sequence = _int_list(trip.get("tasks"))
        arc_options = _str_list(trip.get("arc_option_ids"))
        if not sequence or len(arc_options) != len(sequence) + 1:
            return []
        if "start_time" not in trip:
            return []
        traces.append(
            {
                "sequence": sequence,
                "start_time": float(trip.get("start_time")),
                "arc_option_sequence": arc_options,
            }
        )
    if traces:
        return traces
    for signature in journey.get("signature") or []:
        if not isinstance(signature, list) or len(signature) < 3:
            continue
        sequence = _int_list(signature[0])
        arc_options = _str_list(signature[1])
        if not sequence or len(arc_options) != len(sequence) + 1:
            return []
        traces.append(
            {
                "sequence": sequence,
                "start_time": float(signature[2]),
                "arc_option_sequence": arc_options,
            }
        )
    return traces


def _load_source_rows(manifest: dict[str, Any]) -> dict[int, dict[str, Any]]:
    source = manifest.get("source_jsonl")
    if not source:
        return {}
    path = Path(str(source))
    if not path.is_file():
        return {}
    rows: dict[int, dict[str, Any]] = {}
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        row = json.loads(line)
        rows[int(row.get("row_index", idx))] = row
    return rows


def _int_list(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    result: list[int] = []
    for item in value:
        try:
            result.append(int(item))
        except (TypeError, ValueError):
            continue
    return result


def _str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _classify_record(
    record: dict[str, Any],
    *,
    guard: dict[str, Any],
    knn_k: int,
    max_neighbor_delay_fraction: float,
    split: str,
) -> dict[str, Any]:
    train_x = guard["train_x"]
    train_y = guard["train_y"]
    threshold = float(guard["threshold"])
    safe_radius = guard["safe_radius"]
    risk = _neighbor_unsafe_fraction(train_x, train_y, record["embedding"], k=int(knn_k))
    nearest_safe = _nearest_safe_distance(train_x, train_y, record["embedding"])
    in_radius = bool(
        safe_radius is not None
        and nearest_safe is not None
        and nearest_safe <= float(safe_radius)
    )
    score_pass = float(record["score"]) >= float(threshold)
    neighbor_pass = float(risk) <= float(max_neighbor_delay_fraction)
    decision = 1 if score_pass and neighbor_pass and in_radius else 0
    reason = "high_priority"
    if not score_pass:
        reason = "score_below_threshold"
    elif not neighbor_pass:
        reason = "neighbor_delay_fraction_too_high"
    elif not in_radius:
        reason = "outside_safe_radius"
    return {
        **{key: value for key, value in record.items() if key != "embedding"},
        "decision_split": split,
        "decision": decision,
        "decision_name": "HIGH_PRIORITY" if decision else "DELAY_QUEUE",
        "decision_reason": reason,
        "threshold": float(threshold),
        "threshold_group": str(guard["group"]),
        "threshold_scope": str(guard["scope"]),
        "neighbor_delay_fraction": float(risk),
        "max_neighbor_delay_fraction": float(max_neighbor_delay_fraction),
        "nearest_safe_distance": None if nearest_safe is None else float(nearest_safe),
        "safe_radius": None if safe_radius is None else float(safe_radius),
        "in_safe_radius": in_radius,
        "is_ood": bool(not in_radius),
        "is_knn_unsafe": bool(float(risk) > float(max_neighbor_delay_fraction)),
        "is_label_unsafe": bool(int(record["label_worker_roi_positive"]) == 0),
    }


def _build_guard_model(
    *,
    train_records: list[dict[str, Any]],
    threshold_grouping: str,
    safe_radius_quantile: float,
    safe_radius_multiplier: float,
    fallback_threshold: float,
    threshold_selection: str,
    knn_k: int,
) -> dict[str, Any]:
    global_guard = _guard_from_records(
        records=train_records,
        group="global",
        scope="global",
        safe_radius_quantile=float(safe_radius_quantile),
        safe_radius_multiplier=float(safe_radius_multiplier),
        fallback_threshold=float(fallback_threshold),
        threshold_selection=str(threshold_selection),
    )
    groups: dict[str, dict[str, Any]] = {}
    skipped: dict[str, dict[str, Any]] = {}
    if str(threshold_grouping) != "global":
        by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in train_records:
            by_group[_record_group_key(record, str(threshold_grouping))].append(record)
        for group, records in sorted(by_group.items()):
            labels = [int(record["label_worker_roi_positive"]) for record in records]
            label_set = set(labels)
            if (
                len(records) < max(2, int(knn_k))
                or 0 not in label_set
                or 1 not in label_set
            ):
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
                fallback_threshold=float(fallback_threshold),
                threshold_selection=str(threshold_selection),
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
    fallback_threshold: float,
    threshold_selection: str,
) -> dict[str, Any]:
    if str(threshold_selection) == "zero_fp":
        threshold_info = _select_zero_fp_threshold(records, fallback_threshold=float(fallback_threshold))
    else:
        threshold_info = _fixed_threshold_info(records, threshold=float(fallback_threshold))
    train_x = [record["embedding"] for record in records]
    train_y = [int(record["label_worker_roi_positive"]) for record in records]
    safe_radius = _safe_radius_threshold(
        train_x,
        train_y,
        quantile=float(safe_radius_quantile),
        multiplier=float(safe_radius_multiplier),
    )
    return {
        "group": str(group),
        "scope": str(scope),
        "threshold": float(threshold_info["threshold"]),
        "threshold_info": threshold_info,
        "train_x": train_x,
        "train_y": train_y,
        "train_count": len(records),
        "label_counts": _label_counts(records),
        "safe_radius": safe_radius,
    }


def _select_zero_fp_threshold(records: list[dict[str, Any]], *, fallback_threshold: float) -> dict[str, Any]:
    candidates = sorted({float(record["score"]) for record in records}, reverse=True)
    candidates.extend([float(fallback_threshold), 1.000001])
    best: dict[str, Any] | None = None
    for threshold in candidates:
        scored_records = [
            {
                **record,
                "decision": 1 if float(record["score"]) >= float(threshold) else 0,
            }
            for record in records
        ]
        metrics = _metrics(scored_records)
        if metrics["false_positive_high_priority"] == 0:
            current = {
                "threshold": float(threshold),
                "train_predicted_high_priority": int(metrics["predicted_high_priority"]),
                "train_metrics": metrics,
            }
            if best is None or current["train_predicted_high_priority"] > best["train_predicted_high_priority"]:
                best = current
    if best is not None:
        return best
    metrics = _metrics([{**record, "decision": 0} for record in records])
    return {
        "threshold": 1.000001,
        "train_predicted_high_priority": 0,
        "train_metrics": metrics,
    }


def _fixed_threshold_info(records: list[dict[str, Any]], *, threshold: float) -> dict[str, Any]:
    scored_records = [
        {
            **record,
            "decision": 1 if float(record["score"]) >= float(threshold) else 0,
        }
        for record in records
    ]
    metrics = _metrics(scored_records)
    return {
        "threshold": float(threshold),
        "train_predicted_high_priority": int(metrics["predicted_high_priority"]),
        "train_metrics": metrics,
    }


def _guard_for_record(guard_model: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    grouping = str(guard_model.get("threshold_grouping", "global"))
    if grouping == "global":
        return guard_model["global"]
    key = _record_group_key(record, grouping)
    return guard_model.get("groups", {}).get(key) or guard_model["global"]


def _serializable_guard_model(guard_model: dict[str, Any]) -> dict[str, Any]:
    return {
        "threshold_grouping": guard_model["threshold_grouping"],
        "global": _serializable_guard(guard_model["global"]),
        "groups": {
            key: _serializable_guard(value)
            for key, value in sorted(guard_model.get("groups", {}).items())
        },
        "skipped_groups": guard_model.get("skipped_groups", {}),
    }


def _serializable_guard(guard: dict[str, Any]) -> dict[str, Any]:
    return {
        "group": guard["group"],
        "scope": guard["scope"],
        "threshold": float(guard["threshold"]),
        "threshold_info": guard["threshold_info"],
        "train_count": int(guard["train_count"]),
        "label_counts": guard["label_counts"],
        "safe_radius": None if guard["safe_radius"] is None else float(guard["safe_radius"]),
    }


def _record_group_key(record: dict[str, Any], grouping: str) -> str:
    scale = _record_task_count(record) or "unknown"
    family = _record_family(record)
    if grouping == "scale":
        return str(scale)
    if grouping == "family":
        return str(family)
    if grouping == "scale_family":
        return f"{scale}|{family}"
    return "global"


def _record_task_count(record: dict[str, Any]) -> str | None:
    explicit = record.get("instance_task_count")
    if explicit not in (None, ""):
        try:
            return str(int(explicit)).zfill(3)
        except (TypeError, ValueError):
            text_explicit = str(explicit)
            if text_explicit.isdigit():
                return text_explicit.zfill(3)
    text = " ".join(
        str(record.get(key, ""))
        for key in ("name", "instance", "source_file", "roi_candidate_key")
    )
    match = re.search(r"tasks[_-]?(\d+)", text)
    if match:
        return match.group(1).zfill(3)
    return None


def _record_family(record: dict[str, Any]) -> str:
    family = str(record.get("instance_family") or "").strip()
    if family:
        return family
    source_file = str(record.get("source_file", ""))
    parts = Path(source_file).parts
    if "logical_graph" in parts:
        try:
            idx = parts.index("logical_graph")
            if idx + 2 < len(parts) and parts[idx + 1].startswith("tasks_"):
                return str(parts[idx + 2])
        except ValueError:
            pass
    text = " ".join(str(record.get(key, "")) for key in ("name", "instance", "source_file"))
    match = re.search(r"_20km_([a-zA-Z0-9-]+)_randomtw", text)
    if match:
        return match.group(1)
    return "unknown"


def _metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    for record in records:
        pred = int(record["decision"])
        label = int(record["label_worker_roi_positive"])
        if pred == 1 and label == 1:
            tp += 1
        elif pred == 1 and label == 0:
            fp += 1
        elif pred == 0 and label == 0:
            tn += 1
        else:
            fn += 1
    total = tp + fp + tn + fn
    add_precision = None if tp + fp <= 0 else tp / float(tp + fp)
    add_recall = None if tp + fn <= 0 else tp / float(tp + fn)
    add_f0p5 = _fbeta(add_precision, add_recall, beta=0.5)
    false_rate = 0.0 if fp + tn <= 0 else fp / float(fp + tn)
    false_positive_contexts = sorted(
        {
            str(record.get("expected_context_hash") or record.get("context_hash") or "")
            for record in records
            if int(record["decision"]) == 1
            and int(record["label_worker_roi_positive"]) == 0
        }
    )
    return {
        "total": total,
        "true_positive_high_priority": tp,
        "false_positive_high_priority": fp,
        "true_negative_delay_queue": tn,
        "false_negative_delay_queue": fn,
        "predicted_high_priority": tp + fp,
        "predicted_delay_queue": tn + fn,
        "add_precision": add_precision,
        "add_recall": add_recall,
        "add_f0p5": add_f0p5,
        "false_high_priority_rate": false_rate,
        "false_positive_context_count": len(false_positive_contexts),
        "false_positive_contexts": false_positive_contexts,
        "accuracy": None if total <= 0 else (tp + tn) / float(total),
    }


def _fbeta(precision: float | None, recall: float | None, *, beta: float) -> float | None:
    if precision is None or recall is None:
        return None
    if precision <= 0.0 and recall <= 0.0:
        return 0.0
    beta_sq = float(beta) * float(beta)
    denominator = beta_sq * precision + recall
    if denominator <= 0.0:
        return None
    return (1.0 + beta_sq) * precision * recall / denominator


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return numerator / float(denominator)


def _safety_shell_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(records)
    ood_records = [record for record in records if record.get("is_ood")]
    knn_unsafe_records = [record for record in records if record.get("is_knn_unsafe")]
    label_unsafe_records = [record for record in records if record.get("is_label_unsafe")]
    union_unsafe_records = [
        record
        for record in records
        if record.get("is_ood") or record.get("is_knn_unsafe") or record.get("is_label_unsafe")
    ]
    accepted_records = [record for record in records if int(record.get("decision") or 0) == 1]
    delay_records = [record for record in records if int(record.get("decision") or 0) == 0]
    accepted_positive = [
        record for record in accepted_records if int(record.get("label_worker_roi_positive") or 0) == 1
    ]
    harmful_delayed = [
        record for record in label_unsafe_records if int(record.get("decision") or 0) == 0
    ]
    false_safe_ood = [record for record in ood_records if int(record.get("decision") or 0) == 1]
    false_safe_knn = [
        record for record in knn_unsafe_records if int(record.get("decision") or 0) == 1
    ]
    false_safe_label = [
        record for record in label_unsafe_records if int(record.get("decision") or 0) == 1
    ]
    false_safe_union = [
        record for record in union_unsafe_records if int(record.get("decision") or 0) == 1
    ]
    coverage_non_ood_count = total - len(ood_records)
    return {
        "total": total,
        "coverage_non_ood_count": coverage_non_ood_count,
        "coverage": _rate(coverage_non_ood_count, total),
        "ood_count": len(ood_records),
        "ood_rate": _rate(len(ood_records), total),
        "delay_count": len(delay_records),
        "delay_rate": _rate(len(delay_records), total),
        "accepted_batch_count": len(accepted_records),
        "accepted_batch_rate": _rate(len(accepted_records), total),
        "accepted_batch_roi_positive_count": len(accepted_positive),
        "accepted_batch_roi": _rate(len(accepted_positive), len(accepted_records)),
        "safe_precision": _rate(len(accepted_positive), len(accepted_records)),
        "unsafe_label_count": len(label_unsafe_records),
        "harmful_batch_recall": _rate(len(harmful_delayed), len(label_unsafe_records)),
        "knn_unsafe_count": len(knn_unsafe_records),
        "unsafe_or_ood_count": len(union_unsafe_records),
        "false_safe_ood_count": len(false_safe_ood),
        "false_safe_rate_ood": _rate(len(false_safe_ood), len(ood_records)),
        "false_safe_knn_unsafe_count": len(false_safe_knn),
        "false_safe_rate_knn_unsafe": _rate(len(false_safe_knn), len(knn_unsafe_records)),
        "false_safe_label_unsafe_count": len(false_safe_label),
        "false_safe_rate_label_unsafe": _rate(len(false_safe_label), len(label_unsafe_records)),
        "false_safe_union_count": len(false_safe_union),
        "false_safe_rate_union": _rate(len(false_safe_union), len(union_unsafe_records)),
        "decision_reason_counts": dict(
            sorted(Counter(str(record.get("decision_reason") or "") for record in records).items())
        ),
        "accepted_reason_counts": dict(
            sorted(Counter(str(record.get("decision_reason") or "") for record in accepted_records).items())
        ),
    }


def _validation_false_safe_rates(metrics: dict[str, Any]) -> dict[str, Any]:
    named_rates = {
        "ood": metrics.get("false_safe_rate_ood"),
        "knn_unsafe": metrics.get("false_safe_rate_knn_unsafe"),
        "label_unsafe": metrics.get("false_safe_rate_label_unsafe"),
        "union": metrics.get("false_safe_rate_union"),
    }
    observed = {
        key: float(value)
        for key, value in named_rates.items()
        if value is not None
    }
    return {
        **named_rates,
        "max_observed_false_safe_rate": None if not observed else max(observed.values()),
        "max_observed_false_safe_source": None
        if not observed
        else max(observed, key=lambda key: observed[key]),
    }


def _label_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    return dict(
        sorted(
            Counter("add" if int(record["label_worker_roi_positive"]) else "abstain" for record in records).items()
        )
    )


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Worker ROI kNN/OOD Audit 报告",
        "",
        "日期：2026-06-15",
        "",
        "## 目的",
        "",
        "本报告只做离线审计：GAT 负责 trajectory ROI 表达，kNN/OOD 负责安全壳。",
        "通过者只能进入 HIGH_PRIORITY；未通过者进入 DELAY_QUEUE，不能永久丢弃。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_worker_roi_knn_ood_audit = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"target_label = {summary['target_label']}",
        f"train_row_count = {summary['train_row_count']}",
        f"validation_row_count = {summary['validation_row_count']}",
        f"validation_candidate_ready = {str(summary['validation_candidate_ready']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"selector_can_certificate = {str(summary['selector_can_certificate']).lower()}",
        f"gate_can_permanently_discard_negative_columns = {str(summary['gate_can_permanently_discard_negative_columns']).lower()}",
        "```",
        "",
        "## 验证指标",
        "",
        "```json",
        json.dumps(
            {
                "threshold": summary["threshold"],
                "safe_radius": summary["safe_radius"],
                "validation_metrics": summary["validation_metrics"],
                "validation_safety_shell_metrics": summary["validation_safety_shell_metrics"],
                "validation_false_safe_rates": summary["validation_false_safe_rates"],
                "decision_reason_counts": summary["decision_reason_counts"],
                "decision_scope_safety_shell_metrics": summary[
                    "decision_scope_safety_shell_metrics"
                ],
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
        "- 不运行 BPC / pricing / RMP / worker；",
        "- 不产生 certificate，也不影响 official lower bound；",
        "- HIGH_PRIORITY 只是调度优先级；",
        "- DELAY_QUEUE 只是延迟队列，不能永久拒绝 true-RC negative；",
        "- 生产化前仍需 5/10 no-regression 和 20-task ROI A/B。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

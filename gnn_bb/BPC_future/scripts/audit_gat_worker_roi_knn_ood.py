#!/usr/bin/env python3
"""Audit worker-ROI GAT with a kNN/OOD safety shell.

This offline diagnostic is for the paired worker A/B trajectory-ROI target.
It never runs BPC, pricing, RMP, workers, or certificates.  The learned model
may only nominate HIGH_PRIORITY candidates; non-nominated true-RC negative
candidates must remain reachable through DELAY_QUEUE.
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
    parser.add_argument("--min-add-recall", type=float, default=0.25)
    parser.add_argument("--max-false-high-priority-rate", type=float, default=0.25)
    parser.add_argument("--decision-scope", choices=("validation", "all"), default="validation")
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
        min_add_recall=float(args.min_add_recall),
        max_false_high_priority_rate=float(args.max_false_high_priority_rate),
        decision_scope=str(args.decision_scope),
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
    min_add_recall: float = 0.25,
    max_false_high_priority_rate: float = 0.25,
    decision_scope: str = "validation",
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

    threshold = float(
        training.get("calibrated_add_threshold")
        or checkpoint_data.get("deployment_guard", {}).get("calibrated_add_threshold")
        or 0.5
    )
    train_x = [record["embedding"] for record in train_records]
    train_y = [record["label_worker_roi_positive"] for record in train_records]
    safe_radius = _safe_radius_threshold(
        train_x,
        train_y,
        quantile=float(safe_radius_quantile),
        multiplier=float(safe_radius_multiplier),
    )
    validation_decisions = [
        _classify_record(
            record,
            threshold=threshold,
            train_x=train_x,
            train_y=train_y,
            safe_radius=safe_radius,
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
                threshold=threshold,
                train_x=train_x,
                train_y=train_y,
                safe_radius=safe_radius,
                knn_k=int(knn_k),
                max_neighbor_delay_fraction=float(max_neighbor_delay_fraction),
                split=split_name,
            )
        )
    validation_metrics = _metrics(validation_decisions)
    decision_scope_metrics = _metrics(decision_records)
    false_rate = validation_metrics["false_high_priority_rate"]
    validation_candidate_ready = bool(
        validation_metrics["predicted_high_priority"] >= int(min_validation_high_priority)
        and (validation_metrics["add_recall"] is not None)
        and validation_metrics["add_recall"] >= float(min_add_recall)
        and false_rate <= float(max_false_high_priority_rate)
    )
    production_block_reasons: list[str] = []
    if validation_metrics["predicted_high_priority"] < int(min_validation_high_priority):
        production_block_reasons.append("validation_high_priority_below_min")
    if validation_metrics["add_recall"] is None or validation_metrics["add_recall"] < float(min_add_recall):
        production_block_reasons.append("validation_add_recall_below_min")
    if false_rate > float(max_false_high_priority_rate):
        production_block_reasons.append("validation_false_high_priority_rate_above_max")
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
        "knn_k": int(knn_k),
        "max_neighbor_delay_fraction": float(max_neighbor_delay_fraction),
        "safe_radius_quantile": float(safe_radius_quantile),
        "safe_radius_multiplier": float(safe_radius_multiplier),
        "decision_scope": str(decision_scope),
        "decision_record_count": len(decision_records),
        "validation_metrics": validation_metrics,
        "decision_scope_metrics": decision_scope_metrics,
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
    threshold: float,
    train_x: list[list[float]],
    train_y: list[int],
    safe_radius: float | None,
    knn_k: int,
    max_neighbor_delay_fraction: float,
    split: str,
) -> dict[str, Any]:
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
        "neighbor_delay_fraction": float(risk),
        "max_neighbor_delay_fraction": float(max_neighbor_delay_fraction),
        "nearest_safe_distance": None if nearest_safe is None else float(nearest_safe),
        "safe_radius": None if safe_radius is None else float(safe_radius),
        "in_safe_radius": in_radius,
    }


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
    false_rate = 0.0 if fp + tn <= 0 else fp / float(fp + tn)
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
        "false_high_priority_rate": false_rate,
        "accuracy": None if total <= 0 else (tp + tn) / float(total),
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
                "decision_reason_counts": summary["decision_reason_counts"],
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

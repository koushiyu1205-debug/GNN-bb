#!/usr/bin/env python3
"""Audit same-run GAT batch-impact checkpoint with kNN/OOD safety shell.

This is an offline diagnostic.  It scores the same-run graph dataset, chooses a
conservative high-priority threshold on the training split, then evaluates a
kNN/OOD shell on held-out instances.  It never runs BPC, pricing, RMP, workers,
or certificates.
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
    parser.add_argument("--min-high-priority-precision", type=float, default=0.95)
    parser.add_argument("--min-high-priority-recall", type=float, default=0.65)
    parser.add_argument("--min-high-priority-f0p5", type=float, default=0.90)
    parser.add_argument("--min-delay-recall", type=float, default=0.5)
    parser.add_argument("--max-false-positive-contexts", type=int, default=0)
    parser.add_argument("--max-validation-false-safe-rate", type=float, default=0.02)
    parser.add_argument("--min-coverage", type=float, default=0.0)
    parser.add_argument("--decision-scope", choices=("validation", "all"), default="validation")
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
        min_high_priority_precision=float(args.min_high_priority_precision),
        min_high_priority_recall=float(args.min_high_priority_recall),
        min_high_priority_f0p5=float(args.min_high_priority_f0p5),
        min_delay_recall=float(args.min_delay_recall),
        max_false_positive_contexts=int(args.max_false_positive_contexts),
        max_validation_false_safe_rate=float(args.max_validation_false_safe_rate),
        min_coverage=float(args.min_coverage),
        decision_scope=str(args.decision_scope),
        threshold_grouping=str(args.threshold_grouping),
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
    min_high_priority_precision: float = 0.95,
    min_high_priority_recall: float = 0.65,
    min_high_priority_f0p5: float = 0.90,
    min_delay_recall: float = 0.5,
    max_false_positive_contexts: int = 0,
    max_validation_false_safe_rate: float = 0.02,
    min_coverage: float = 0.0,
    decision_scope: str = "validation",
    threshold_grouping: str = "global",
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

    guard_model = _build_guard_model(
        train_records=train_records,
        threshold_grouping=str(threshold_grouping),
        safe_radius_quantile=float(safe_radius_quantile),
        safe_radius_multiplier=float(safe_radius_multiplier),
        knn_k=int(knn_k),
    )
    global_guard = guard_model["global"]
    threshold_info = global_guard["threshold_info"]
    threshold = float(global_guard["threshold"])
    safe_radius = global_guard["safe_radius"]
    validation_decision_records: list[dict[str, Any]] = []
    for record in validation_records:
        validation_decision_records.append(
            _classify_record(
                record=record,
                guard=_guard_for_record(guard_model, record),
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
                guard=_guard_for_record(guard_model, record),
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
    validation_safety_shell_metrics = _safety_shell_metrics(validation_decision_records)
    decision_scope_safety_shell_metrics = _safety_shell_metrics(decision_records)
    delay_recall = metrics["negative_recall_delay_queue"]
    validation_false_safe_rates = _validation_false_safe_rates(validation_safety_shell_metrics)
    validation_false_safe_rate = validation_false_safe_rates["max_observed_false_safe_rate"]
    validation_coverage = validation_safety_shell_metrics["coverage"]
    validation_no_false_high_priority = bool(metrics["fp_high_priority_on_delay"] == 0)
    validation_min_high_priority_met = bool(
        metrics["predicted_high_priority"] >= int(min_validation_high_priority)
    )
    validation_precision_met = bool(
        metrics["high_priority_precision"] is not None
        and metrics["high_priority_precision"] >= float(min_high_priority_precision)
    )
    validation_recall_met = bool(
        metrics["high_priority_recall"] is not None
        and metrics["high_priority_recall"] >= float(min_high_priority_recall)
    )
    validation_f0p5_met = bool(
        metrics["high_priority_f0p5"] is not None
        and metrics["high_priority_f0p5"] >= float(min_high_priority_f0p5)
    )
    validation_delay_recall_met = bool(
        delay_recall is not None and delay_recall >= float(min_delay_recall)
    )
    validation_false_positive_contexts_met = bool(
        validation_safety_shell_metrics["false_positive_context_count"]
        <= int(max_false_positive_contexts)
    )
    validation_false_safe_rate_met = bool(
        validation_false_safe_rate is None
        or validation_false_safe_rate <= float(max_validation_false_safe_rate)
    )
    validation_coverage_met = bool(
        validation_coverage is not None and validation_coverage >= float(min_coverage)
    )
    validation_candidate_ready = bool(
        validation_no_false_high_priority
        and validation_min_high_priority_met
        and validation_precision_met
        and validation_recall_met
        and validation_f0p5_met
        and validation_delay_recall_met
        and validation_false_positive_contexts_met
        and validation_false_safe_rate_met
        and validation_coverage_met
    )
    production_block_reasons: list[str] = []
    if not validation_no_false_high_priority:
        production_block_reasons.append("validation_false_high_priority_on_delay")
    if not validation_min_high_priority_met:
        production_block_reasons.append("validation_high_priority_below_min")
    if not validation_precision_met:
        production_block_reasons.append("validation_high_priority_precision_below_min")
    if not validation_recall_met:
        production_block_reasons.append("validation_high_priority_recall_below_min")
    if not validation_f0p5_met:
        production_block_reasons.append("validation_high_priority_f0p5_below_min")
    if not validation_delay_recall_met:
        production_block_reasons.append("validation_delay_recall_below_min")
    if not validation_false_positive_contexts_met:
        production_block_reasons.append("validation_false_positive_contexts_above_max")
    if not validation_false_safe_rate_met:
        production_block_reasons.append("validation_false_safe_rate_above_max")
    if not validation_coverage_met:
        production_block_reasons.append("validation_coverage_below_min")
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
        "threshold_grouping": str(threshold_grouping),
        "threshold_group_info": _serializable_guard_model(guard_model),
        "knn_k": int(knn_k),
        "max_neighbor_delay_fraction": float(max_neighbor_delay_fraction),
        "safe_radius_quantile": float(safe_radius_quantile),
        "safe_radius_multiplier": float(safe_radius_multiplier),
        "min_high_priority_precision": float(min_high_priority_precision),
        "min_high_priority_recall": float(min_high_priority_recall),
        "min_high_priority_f0p5": float(min_high_priority_f0p5),
        "max_validation_false_safe_rate": float(max_validation_false_safe_rate),
        "max_false_positive_contexts": int(max_false_positive_contexts),
        "min_coverage": float(min_coverage),
        "decision_scope": str(decision_scope),
        "decision_record_count": len(decision_records),
        "validation_metrics": metrics,
        "decision_scope_metrics": decision_scope_metrics,
        "validation_safety_shell_metrics": validation_safety_shell_metrics,
        "decision_scope_safety_shell_metrics": decision_scope_safety_shell_metrics,
        "validation_false_safe_rates": validation_false_safe_rates,
        "validation_safety_checks": {
            "no_false_high_priority": validation_no_false_high_priority,
            "min_high_priority_met": validation_min_high_priority_met,
            "precision_met": validation_precision_met,
            "recall_met": validation_recall_met,
            "f0p5_met": validation_f0p5_met,
            "delay_recall_met": validation_delay_recall_met,
            "false_positive_contexts_met": validation_false_positive_contexts_met,
            "false_safe_rate_met": validation_false_safe_rate_met,
            "coverage_met": validation_coverage_met,
        },
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
    guard: dict[str, Any],
    knn_k: int,
    max_neighbor_delay_fraction: float,
    split: str,
) -> dict[str, Any]:
    train_x = guard["train_x"]
    train_y = guard["train_y"]
    threshold = float(guard["threshold"])
    safe_radius = guard["safe_radius"]
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
        "instance_task_count": _record_task_count(record),
        "instance_family": _record_family(record),
        "label_high_priority": int(record["label_high_priority"]),
        "probability": float(record["probability"]),
        "threshold": float(threshold),
        "threshold_group": str(guard["group"]),
        "threshold_scope": str(guard["scope"]),
        "neighbor_delay_fraction": float(neighbor_delay_fraction),
        "nearest_safe_distance": None if nearest_safe is None else float(nearest_safe),
        "safe_radius": None if safe_radius is None else float(safe_radius),
        "is_ood": bool(not in_radius),
        "is_knn_unsafe": bool(
            neighbor_delay_fraction > float(max_neighbor_delay_fraction)
        ),
        "is_label_unsafe": bool(int(record["label_high_priority"]) == 0),
        "decision": int(decision),
        "decision_name": "HIGH_PRIORITY" if decision else "DELAY_QUEUE",
        "decision_reason": reason,
    }


def _build_guard_model(
    *,
    train_records: list[dict[str, Any]],
    threshold_grouping: str,
    safe_radius_quantile: float,
    safe_radius_multiplier: float,
    knn_k: int,
) -> dict[str, Any]:
    global_guard = _guard_from_records(
        records=train_records,
        group="global",
        scope="global",
        safe_radius_quantile=float(safe_radius_quantile),
        safe_radius_multiplier=float(safe_radius_multiplier),
    )
    groups: dict[str, dict[str, Any]] = {}
    skipped: dict[str, dict[str, Any]] = {}
    if str(threshold_grouping) != "global":
        by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in train_records:
            by_group[_record_group_key(record, str(threshold_grouping))].append(record)
        for group, records in sorted(by_group.items()):
            labels = [int(record["label_high_priority"]) for record in records]
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
) -> dict[str, Any]:
    threshold_info = _select_zero_delay_fp_threshold(records)
    train_x = [record["embedding"] for record in records]
    train_y = [int(record["label_high_priority"]) for record in records]
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
    text = " ".join(
        str(record.get(key, ""))
        for key in ("instance_path", "instance", "sample_path", "source_file")
    )
    match = re.search(r"tasks[_-]?(\d+)", text)
    if not match:
        return None
    return match.group(1).zfill(3)


def _record_family(record: dict[str, Any]) -> str:
    instance_path = str(record.get("instance_path", ""))
    parts = Path(instance_path).parts
    if "logical_graph" in parts:
        try:
            idx = parts.index("logical_graph")
            if idx + 2 < len(parts) and parts[idx + 1].startswith("tasks_"):
                return str(parts[idx + 2])
        except ValueError:
            pass
    instance = str(record.get("instance", ""))
    match = re.search(r"_20km_([a-zA-Z0-9-]+)_randomtw", instance)
    if match:
        return match.group(1)
    return "unknown"


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
    precision = None if predicted <= 0 else tp / float(predicted)
    recall = None if positives <= 0 else tp / float(positives)
    f0p5 = _fbeta(precision, recall, beta=0.5)
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
        "high_priority_precision": precision,
        "high_priority_recall": recall,
        "high_priority_f0p5": f0p5,
        "negative_recall_delay_queue": None if negatives <= 0 else tn / float(negatives),
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


def _safe_divide(numerator: int | float, denominator: int | float) -> float | None:
    if float(denominator) <= 0.0:
        return None
    return float(numerator) / float(denominator)


def _safety_shell_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(records)
    accepted = [record for record in records if int(record["decision"]) == 1]
    delayed = [record for record in records if int(record["decision"]) == 0]
    ood = [record for record in records if bool(record.get("is_ood", False))]
    non_ood = [record for record in records if not bool(record.get("is_ood", False))]
    knn_unsafe = [record for record in records if bool(record.get("is_knn_unsafe", False))]
    label_unsafe = [
        record for record in records if int(record.get("label_high_priority", 0)) == 0
    ]
    unsafe_union = [
        record
        for record in records
        if bool(record.get("is_ood", False))
        or bool(record.get("is_knn_unsafe", False))
        or int(record.get("label_high_priority", 0)) == 0
    ]
    accepted_ood = [record for record in accepted if bool(record.get("is_ood", False))]
    accepted_knn_unsafe = [
        record for record in accepted if bool(record.get("is_knn_unsafe", False))
    ]
    accepted_label_unsafe = [
        record for record in accepted if int(record.get("label_high_priority", 0)) == 0
    ]
    accepted_unsafe_union = [
        record
        for record in accepted
        if bool(record.get("is_ood", False))
        or bool(record.get("is_knn_unsafe", False))
        or int(record.get("label_high_priority", 0)) == 0
    ]
    accepted_roi_positive = [
        record for record in accepted if int(record.get("label_high_priority", 0)) == 1
    ]
    false_positive_contexts = sorted(
        {
            str(record.get("context_hash") or "")
            for record in accepted_label_unsafe
        }
    )
    reason_counts = Counter(str(record.get("decision_reason", "")) for record in records)
    accepted_reason_counts = Counter(
        str(record.get("decision_reason", "")) for record in accepted
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
        "accepted_batch_roi_positive_count": int(len(accepted_roi_positive)),
        "accepted_batch_roi": _safe_divide(len(accepted_roi_positive), len(accepted)),
        "safe_precision": _safe_divide(len(accepted_roi_positive), len(accepted)),
        "unsafe_label_count": int(len(label_unsafe)),
        "knn_unsafe_count": int(len(knn_unsafe)),
        "unsafe_or_ood_count": int(len(unsafe_union)),
        "false_safe_ood_count": int(len(accepted_ood)),
        "false_safe_rate_ood": _safe_divide(len(accepted_ood), len(ood)),
        "false_safe_knn_unsafe_count": int(len(accepted_knn_unsafe)),
        "false_safe_rate_knn_unsafe": _safe_divide(
            len(accepted_knn_unsafe), len(knn_unsafe)
        ),
        "false_safe_label_unsafe_count": int(len(accepted_label_unsafe)),
        "false_safe_rate_label_unsafe": _safe_divide(
            len(accepted_label_unsafe), len(label_unsafe)
        ),
        "false_positive_context_count": int(len(false_positive_contexts)),
        "false_positive_contexts": false_positive_contexts,
        "false_safe_union_count": int(len(accepted_unsafe_union)),
        "false_safe_rate_union": _safe_divide(
            len(accepted_unsafe_union), len(unsafe_union)
        ),
        "decision_reason_counts": dict(
            sorted((str(key), int(value)) for key, value in reason_counts.items())
        ),
        "accepted_reason_counts": dict(
            sorted((str(key), int(value)) for key, value in accepted_reason_counts.items())
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
        f"threshold_grouping = {summary['threshold_grouping']}",
        f"decision_scope = {summary['decision_scope']}",
        f"decision_record_count = {summary['decision_record_count']}",
        f"decision_split_counts = {summary['decision_split_counts']}",
        f"decision_threshold_group_counts = {summary['decision_threshold_group_counts']}",
        f"decision_threshold_scope_counts = {summary['decision_threshold_scope_counts']}",
        f"validation_safety_shell_metrics = {summary['validation_safety_shell_metrics']}",
        f"decision_scope_safety_shell_metrics = {summary['decision_scope_safety_shell_metrics']}",
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
                "validation_safety_shell_metrics": summary["validation_safety_shell_metrics"],
                "decision_scope_safety_shell_metrics": summary["decision_scope_safety_shell_metrics"],
                "validation_false_safe_rates": summary["validation_false_safe_rates"],
                "validation_metrics": summary["validation_metrics"],
                "validation_safety_checks": summary["validation_safety_checks"],
                "decision_scope_metrics": summary["decision_scope_metrics"],
                "decision_reason_counts": summary["decision_reason_counts"],
                "decision_split_counts": summary["decision_split_counts"],
                "decision_threshold_group_counts": summary["decision_threshold_group_counts"],
                "decision_threshold_scope_counts": summary["decision_threshold_scope_counts"],
                "threshold_info": summary["threshold_info"],
                "threshold_group_info": summary["threshold_group_info"],
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

#!/usr/bin/env python3
"""Audit label provenance and action-consequence fields for unresolved pairs.

This is an offline diagnostic for focused same-context pair failures. It reads
an existing GAT batch-impact dataset plus a pair-row JSONL emitted by a focused
pair/comparator audit. It does not run BPC, pricing, RMP, workers, or
certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date
import json
import math
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch


DEFAULT_DATASET_DIR = Path(
    "BPC_future/data/gat_batch_impact/"
    "v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622"
)
DEFAULT_PAIR_ROWS = Path(
    "BPC_future/results/"
    "gat_batch_impact_context_pair_comparator_audit_v131_v130_epoch004_20260623/"
    "context_pair_comparator_pair_rows.jsonl"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/"
    "gat_batch_impact_unresolved_context_label_action_audit_v132_v131_20260623"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260623_bpc_future_gat_target_mode_stage3_v132_"
    "unresolved_context_label_action_audit_zh.md"
)

CAUSAL_SUPPORT_FIELDS: tuple[str, ...] = (
    "training_label_allowed",
    "same_context_target_intervention_observed",
    "worker_target_causal_match",
)
ACTION_FIELDS: tuple[str, ...] = (
    "added_journeys",
    "replacement_journeys",
    "active_changed_task_set_count",
    "new_task_set_count",
    "replacement_task_set_count",
    "returned_journey_count",
    "best_true_reduced_cost",
    "pricing_kind",
)
CONSEQUENCE_FIELDS: tuple[str, ...] = (
    "objective_improvement",
    "objective_delta",
    "accepted_batch_roi_label",
    "trajectory_accepted_batch_roi",
    "accepted_batch_roi",
    "label_objective_improved",
    "label_batch_roi_positive",
    "label_tail_improved",
    "label_support_changed_good",
    "label_bad_mode_switch",
    "delta_v_label",
    "trajectory_delta_v_label",
    "barrier_slack_label",
    "trajectory_barrier_slack_label",
    "final_judge_retry_delta",
    "pricing_tail_retry_delta",
    "hidden_negative_delta",
    "pricing_calls_delta",
    "solving_time_delta",
    "generated_sequences_delta",
)
SIGNATURE_FIELDS: tuple[str, ...] = (
    "target_signature_samples",
    "target_materialized_signature_samples",
    "worker_returned_candidate_signature_samples",
)
SAMPLE_LABEL_ATTRS: tuple[str, ...] = (
    "y_batch_roi_positive",
    "y_objective_progress",
    "y_tail_improved",
    "y_bad_mode_switch",
    "y_support_changed_good",
    "y_delta_v",
    "y_barrier_slack",
    "y_accepted_batch_roi",
    "y_candidate_high_priority",
    "y_candidate_delay_risk",
    "y_candidate_true_rc_negative",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--pair-rows", type=Path, default=DEFAULT_PAIR_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--top-contexts", type=int, default=20)
    parser.add_argument(
        "--weak-positive-roi-threshold",
        type=float,
        default=1.0,
        help="Positive ROI below this value is marked as weak-margin evidence.",
    )
    parser.add_argument(
        "--include-existing-pass-conflicts",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include pairs where the comparator conflicts with an existing pass.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_unresolved_context_label_action(
        dataset_dir=Path(args.dataset_dir),
        pair_rows_path=Path(args.pair_rows),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        top_contexts=max(1, int(args.top_contexts)),
        weak_positive_roi_threshold=float(args.weak_positive_roi_threshold),
        include_existing_pass_conflicts=bool(args.include_existing_pass_conflicts),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if bool(summary["all_checks_pass"]) else 1


def audit_unresolved_context_label_action(
    *,
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    pair_rows_path: Path = DEFAULT_PAIR_ROWS,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    top_contexts: int = 20,
    weak_positive_roi_threshold: float = 1.0,
    include_existing_pass_conflicts: bool = True,
) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    manifest = _read_json(dataset_dir / "manifest.json")
    manifest_rows = {
        int(item.get("row_index")): item
        for item in manifest.get("samples", [])
        if item.get("row_index") is not None
    }
    source_rows = _load_source_rows(manifest)
    pair_rows = list(_read_jsonl(pair_rows_path))
    selected_pairs = [
        dict(row)
        for row in pair_rows
        if _select_pair(row, include_existing_pass_conflicts=include_existing_pass_conflicts)
    ]

    row_roles = _row_roles(selected_pairs)
    row_records: dict[int, dict[str, Any]] = {}
    missing_counts: Counter[str] = Counter()
    for row_index in sorted(row_roles):
        manifest_item = manifest_rows.get(int(row_index))
        if manifest_item is None:
            missing_counts["missing_manifest_row"] += 1
            continue
        sample = _load_sample(dataset_dir, manifest_item, missing_counts)
        source_row = source_rows[row_index] if 0 <= row_index < len(source_rows) else {}
        if not source_row:
            missing_counts["missing_source_row"] += 1
        row_records[row_index] = _build_row_record(
            row_index=row_index,
            manifest_item=manifest_item,
            source_row=source_row,
            sample=sample,
            role=row_roles[row_index],
            manifest=manifest,
        )

    pair_records: list[dict[str, Any]] = []
    for pair in selected_pairs:
        positive_index = _int_or_none(pair.get("positive_row_index"))
        negative_index = _int_or_none(pair.get("negative_row_index"))
        if positive_index is None or negative_index is None:
            missing_counts["pair_missing_row_index"] += 1
            continue
        positive = row_records.get(positive_index)
        negative = row_records.get(negative_index)
        if positive is None or negative is None:
            missing_counts["pair_row_record_missing"] += 1
            continue
        pair_records.append(
            _build_pair_record(
                pair=pair,
                positive=positive,
                negative=negative,
                manifest=manifest,
                weak_positive_roi_threshold=weak_positive_roi_threshold,
            )
        )

    context_records = _context_records(pair_records)
    summary_stats = _summary_stats(
        pair_records=pair_records,
        row_records=list(row_records.values()),
        context_records=context_records,
    )
    recommendation = _recommend_next_step(summary_stats)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    row_path = output_dir / "unresolved_context_label_action_rows.jsonl"
    pair_path = output_dir / "unresolved_context_label_action_pairs.jsonl"
    context_path = output_dir / "unresolved_context_label_action_contexts.jsonl"
    summary_path = output_dir / "summary.json"
    _write_jsonl(row_path, sorted(row_records.values(), key=lambda row: int(row["row_index"])))
    _write_jsonl(pair_path, pair_records)
    _write_jsonl(context_path, context_records)

    summary = {
        "schema_version": "gat_batch_impact_unresolved_context_label_action_audit_v1",
        "status": "gat_batch_impact_unresolved_context_label_action_audited",
        "dataset_dir": str(dataset_dir),
        "pair_rows_path": str(pair_rows_path),
        "output_dir": str(output_dir),
        "summary_path": str(summary_path),
        "row_records_path": str(row_path),
        "pair_records_path": str(pair_path),
        "context_records_path": str(context_path),
        "report": str(report),
        "manifest_sample_count": int(manifest.get("sample_count") or len(manifest.get("samples", []))),
        "source_row_count": len(source_rows),
        "input_pair_count": len(pair_rows),
        "selected_pair_count": len(selected_pairs),
        "audited_pair_count": len(pair_records),
        "audited_row_count": len(row_records),
        "audited_context_count": len(context_records),
        "top_contexts": int(top_contexts),
        "weak_positive_roi_threshold": float(weak_positive_roi_threshold),
        "include_existing_pass_conflicts": bool(include_existing_pass_conflicts),
        "missing_counts": dict(sorted(missing_counts.items())),
        "summary": summary_stats,
        "top_contexts_by_unresolved": sorted(
            context_records,
            key=lambda row: (
                int(row["unresolved_existing_failure_pair_count"]),
                int(row["comparator_conflict_pair_count"]),
                int(row["pair_count"]),
            ),
            reverse=True,
        )[: int(top_contexts)],
        "recommended_next_step": recommendation,
        "stage3_completed": False,
        "stage4_candidate_ready": False,
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "runs_rmp": False,
        "production_ready": False,
        "default_enabled": False,
        "official_bound_effect": False,
        "selector_is_pricing_oracle": False,
        "selector_can_certificate": False,
        "gate_can_permanently_discard_negative_columns": False,
        "all_checks_pass": True,
    }
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary, context_records)
    return summary


def _select_pair(row: dict[str, Any], *, include_existing_pass_conflicts: bool) -> bool:
    if bool(row.get("comparator_unresolved_existing_failure")):
        return True
    if include_existing_pass_conflicts and bool(row.get("comparator_conflicts_existing_pass")):
        return True
    return False


def _row_roles(pair_rows: list[dict[str, Any]]) -> dict[int, dict[str, int]]:
    roles: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for pair in pair_rows:
        positive = _int_or_none(pair.get("positive_row_index"))
        negative = _int_or_none(pair.get("negative_row_index"))
        pair_is_unresolved = int(bool(pair.get("comparator_unresolved_existing_failure")))
        pair_is_conflict = int(bool(pair.get("comparator_conflicts_existing_pass")))
        if positive is not None:
            roles[positive]["appears_as_positive_count"] += 1
            roles[positive]["unresolved_pair_count"] += pair_is_unresolved
            roles[positive]["comparator_conflict_pair_count"] += pair_is_conflict
        if negative is not None:
            roles[negative]["appears_as_negative_count"] += 1
            roles[negative]["unresolved_pair_count"] += pair_is_unresolved
            roles[negative]["comparator_conflict_pair_count"] += pair_is_conflict
    return {key: dict(value) for key, value in roles.items()}


def _build_row_record(
    *,
    row_index: int,
    manifest_item: dict[str, Any],
    source_row: dict[str, Any],
    sample: Any,
    role: dict[str, int],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    causal_values = {field: _bool_or_none(source_row.get(field)) for field in CAUSAL_SUPPORT_FIELDS}
    causal_supported = all(value is True for value in causal_values.values())
    action_values = {field: _json_safe(source_row.get(field)) for field in ACTION_FIELDS if field in source_row}
    consequence_values = {
        field: _json_safe(source_row.get(field)) for field in CONSEQUENCE_FIELDS if field in source_row
    }
    source_signatures = _first_nonempty_list(source_row, SIGNATURE_FIELDS)
    candidate_signature_ids = [str(value) for value in manifest_item.get("candidate_signature_ids") or []]
    sample_labels = {
        name: _tensor_json_value(_sample_attr(sample, name)) for name in SAMPLE_LABEL_ATTRS
    }
    accepted_roi = _first_finite(
        manifest_item.get("accepted_batch_roi"),
        source_row.get("accepted_batch_roi_label"),
        source_row.get("trajectory_accepted_batch_roi"),
        source_row.get("accepted_batch_roi"),
        source_row.get("objective_improvement"),
    )
    manifest_positive = int(manifest_item.get("label_batch_roi_positive") or 0)
    label_polarity_consistent = (
        (manifest_positive == 1 and accepted_roi is not None and accepted_roi > 0.0)
        or (manifest_positive == 0 and (accepted_roi is None or accepted_roi <= 0.0))
    )
    source_context_hash = str(source_row.get("context_hash") or "")
    manifest_context_hash = str(manifest_item.get("context_hash") or "")
    return {
        "row_index": int(row_index),
        "path": str(manifest_item.get("path") or ""),
        "instance": str(manifest_item.get("instance") or source_row.get("instance") or ""),
        "instance_family": str(manifest_item.get("instance_family") or ""),
        "task_count": int(manifest_item.get("task_count") or 0),
        "context_hash": manifest_context_hash,
        "source_context_hash": source_context_hash,
        "source_context_matches_manifest": bool(
            not source_context_hash or source_context_hash == manifest_context_hash
        ),
        "accepted_batch_roi": accepted_roi,
        "manifest_label_batch_roi_positive": manifest_positive,
        "label_polarity_consistent": bool(label_polarity_consistent),
        "causal_support_values": causal_values,
        "causal_label_supported": bool(causal_supported),
        "causal_support_missing_fields": [
            field for field, value in causal_values.items() if value is not True
        ],
        "source_has_explicit_consequence_label": any(
            field in source_row and source_row.get(field) not in (None, "")
            for field in CONSEQUENCE_FIELDS
        ),
        "consequence_field_count": len(consequence_values),
        "action_field_count": len(action_values),
        "action_values": action_values,
        "consequence_values": consequence_values,
        "candidate_signature_ids": candidate_signature_ids,
        "source_signature_samples": source_signatures[:5],
        "signature_sample_count": len(source_signatures),
        "sample_labels": sample_labels,
        "context_feature_summary": _feature_summary(
            _sample_attr(sample, "context_features"),
            list(manifest.get("context_feature_schema") or []),
            limit=12,
        ),
        "batch_feature_summary": _feature_summary(
            _sample_attr(sample, "batch_features"),
            list(manifest.get("batch_feature_schema") or []),
            limit=18,
        ),
        "candidate_feature_summary": _feature_summary(
            _candidate_feature_mean(_sample_attr(sample, "candidate_features")),
            list(manifest.get("candidate_feature_schema") or []),
            limit=20,
        ),
        "role": {
            "appears_as_positive_count": int(role.get("appears_as_positive_count", 0)),
            "appears_as_negative_count": int(role.get("appears_as_negative_count", 0)),
            "unresolved_pair_count": int(role.get("unresolved_pair_count", 0)),
            "comparator_conflict_pair_count": int(role.get("comparator_conflict_pair_count", 0)),
        },
        "diagnostic_only": True,
        "official_bound_effect": False,
    }


def _build_pair_record(
    *,
    pair: dict[str, Any],
    positive: dict[str, Any],
    negative: dict[str, Any],
    manifest: dict[str, Any],
    weak_positive_roi_threshold: float,
) -> dict[str, Any]:
    positive_roi = _finite_or_default(positive.get("accepted_batch_roi"), 0.0)
    negative_roi = _finite_or_default(negative.get("accepted_batch_roi"), 0.0)
    causal_pair_supported = bool(
        positive["causal_label_supported"] and negative["causal_label_supported"]
    )
    label_polarity_valid = bool(
        positive["label_polarity_consistent"] and negative["label_polarity_consistent"]
    )
    action_type_same = (
        _action_type_signature(positive.get("action_values") or {})
        == _action_type_signature(negative.get("action_values") or {})
    )
    batch_feature_delta = _feature_delta(
        positive.get("batch_feature_summary") or {},
        negative.get("batch_feature_summary") or {},
        list(manifest.get("batch_feature_schema") or []),
    )
    candidate_feature_delta = _feature_delta(
        positive.get("candidate_feature_summary") or {},
        negative.get("candidate_feature_summary") or {},
        list(manifest.get("candidate_feature_schema") or []),
    )
    context_feature_delta = _feature_delta(
        positive.get("context_feature_summary") or {},
        negative.get("context_feature_summary") or {},
        list(manifest.get("context_feature_schema") or []),
    )
    diagnosis = _pair_diagnosis(
        pair=pair,
        causal_pair_supported=causal_pair_supported,
        label_polarity_valid=label_polarity_valid,
        positive_roi=positive_roi,
        negative_roi=negative_roi,
        action_type_same=action_type_same,
        weak_positive_roi_threshold=weak_positive_roi_threshold,
    )
    return {
        "context_hash": str(pair.get("context_hash") or positive.get("context_hash") or ""),
        "context_key": str(pair.get("context_key") or ""),
        "family": str(pair.get("family") or positive.get("instance_family") or ""),
        "positive_row_index": int(positive["row_index"]),
        "negative_row_index": int(negative["row_index"]),
        "positive_roi": positive_roi,
        "negative_roi": negative_roi,
        "roi_delta": positive_roi - negative_roi,
        "existing_pair_pass": bool(pair.get("existing_pair_pass", pair.get("pair_pass"))),
        "comparator_pair_pass": bool(pair.get("comparator_pair_pass")),
        "comparator_unresolved_existing_failure": bool(
            pair.get("comparator_unresolved_existing_failure")
        ),
        "comparator_conflicts_existing_pass": bool(pair.get("comparator_conflicts_existing_pass")),
        "raw_margin": _float_or_none(pair.get("raw_margin")),
        "admission_margin": _float_or_none(pair.get("admission_margin")),
        "delay_risk_margin": _float_or_none(pair.get("delay_risk_margin")),
        "positive_lower_delay_risk": _bool_or_none(pair.get("positive_lower_delay_risk")),
        "causal_pair_supported": causal_pair_supported,
        "label_polarity_valid": label_polarity_valid,
        "source_contexts_match": bool(
            positive["source_context_matches_manifest"]
            and negative["source_context_matches_manifest"]
            and positive["context_hash"] == negative["context_hash"]
        ),
        "same_action_type": bool(action_type_same),
        "same_action_signature_hash": bool(
            _stable_hash(positive.get("source_signature_samples") or [])
            == _stable_hash(negative.get("source_signature_samples") or [])
        ),
        "positive_causal_missing_fields": positive["causal_support_missing_fields"],
        "negative_causal_missing_fields": negative["causal_support_missing_fields"],
        "positive_consequence_values": positive.get("consequence_values") or {},
        "negative_consequence_values": negative.get("consequence_values") or {},
        "positive_action_values": positive.get("action_values") or {},
        "negative_action_values": negative.get("action_values") or {},
        "batch_feature_l1": batch_feature_delta["l1"],
        "candidate_feature_l1": candidate_feature_delta["l1"],
        "context_feature_l1": context_feature_delta["l1"],
        "top_batch_feature_deltas": batch_feature_delta["top_deltas"],
        "top_candidate_feature_deltas": candidate_feature_delta["top_deltas"],
        "diagnosis": diagnosis,
        "diagnostic_only": True,
        "official_bound_effect": False,
    }


def _pair_diagnosis(
    *,
    pair: dict[str, Any],
    causal_pair_supported: bool,
    label_polarity_valid: bool,
    positive_roi: float,
    negative_roi: float,
    action_type_same: bool,
    weak_positive_roi_threshold: float,
) -> str:
    if not causal_pair_supported:
        return "causal_label_provenance_gap"
    if not label_polarity_valid:
        return "label_polarity_or_roi_conflict"
    if bool(pair.get("comparator_conflicts_existing_pass")):
        return "comparator_conflicts_supported_existing_pass"
    if _bool_or_none(pair.get("positive_lower_delay_risk")) is False:
        return "delay_risk_order_contradicts_positive"
    if positive_roi <= float(weak_positive_roi_threshold) and negative_roi <= 0.0:
        return "weak_positive_roi_margin_against_zero_negative"
    if action_type_same:
        return "supported_labels_same_action_type_needs_visible_contrast"
    return "supported_labels_model_score_ordering_failure"


def _context_records(pair_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pair_records:
        grouped[str(row.get("context_hash") or "")].append(row)
    records: list[dict[str, Any]] = []
    for context_hash, rows in sorted(grouped.items()):
        diagnosis_counts = Counter(str(row["diagnosis"]) for row in rows)
        families = sorted({str(row.get("family") or "") for row in rows})
        records.append(
            {
                "context_hash": context_hash,
                "families": families,
                "pair_count": len(rows),
                "unresolved_existing_failure_pair_count": sum(
                    int(bool(row.get("comparator_unresolved_existing_failure"))) for row in rows
                ),
                "comparator_conflict_pair_count": sum(
                    int(bool(row.get("comparator_conflicts_existing_pass"))) for row in rows
                ),
                "causal_pair_supported_count": sum(
                    int(bool(row.get("causal_pair_supported"))) for row in rows
                ),
                "label_polarity_valid_count": sum(
                    int(bool(row.get("label_polarity_valid"))) for row in rows
                ),
                "diagnosis_counts": dict(sorted(diagnosis_counts.items())),
                "positive_roi_min": min(float(row["positive_roi"]) for row in rows),
                "positive_roi_max": max(float(row["positive_roi"]) for row in rows),
                "negative_roi_min": min(float(row["negative_roi"]) for row in rows),
                "negative_roi_max": max(float(row["negative_roi"]) for row in rows),
                "max_batch_feature_l1": max(float(row["batch_feature_l1"]) for row in rows),
                "max_candidate_feature_l1": max(
                    float(row["candidate_feature_l1"]) for row in rows
                ),
                "row_indices": sorted(
                    {
                        int(row["positive_row_index"])
                        for row in rows
                    }
                    | {int(row["negative_row_index"]) for row in rows}
                ),
            }
        )
    return records


def _summary_stats(
    *,
    pair_records: list[dict[str, Any]],
    row_records: list[dict[str, Any]],
    context_records: list[dict[str, Any]],
) -> dict[str, Any]:
    diagnosis_counts = Counter(str(row["diagnosis"]) for row in pair_records)
    unresolved_count = sum(
        int(bool(row.get("comparator_unresolved_existing_failure"))) for row in pair_records
    )
    conflict_count = sum(
        int(bool(row.get("comparator_conflicts_existing_pass"))) for row in pair_records
    )
    causal_pair_supported_count = sum(
        int(bool(row.get("causal_pair_supported"))) for row in pair_records
    )
    label_polarity_valid_count = sum(
        int(bool(row.get("label_polarity_valid"))) for row in pair_records
    )
    row_causal_supported_count = sum(
        int(bool(row.get("causal_label_supported"))) for row in row_records
    )
    row_label_polarity_valid_count = sum(
        int(bool(row.get("label_polarity_consistent"))) for row in row_records
    )
    primary = _primary_summary(
        pair_count=len(pair_records),
        diagnosis_counts=diagnosis_counts,
        causal_pair_supported_count=causal_pair_supported_count,
        label_polarity_valid_count=label_polarity_valid_count,
    )
    return {
        "primary": primary,
        "unresolved_existing_failure_pair_count": int(unresolved_count),
        "comparator_conflict_pair_count": int(conflict_count),
        "causal_pair_supported_count": int(causal_pair_supported_count),
        "causal_pair_supported_rate": _rate(causal_pair_supported_count, len(pair_records)),
        "label_polarity_valid_pair_count": int(label_polarity_valid_count),
        "label_polarity_valid_pair_rate": _rate(label_polarity_valid_count, len(pair_records)),
        "causal_label_supported_row_count": int(row_causal_supported_count),
        "causal_label_supported_row_rate": _rate(row_causal_supported_count, len(row_records)),
        "label_polarity_consistent_row_count": int(row_label_polarity_valid_count),
        "label_polarity_consistent_row_rate": _rate(
            row_label_polarity_valid_count,
            len(row_records),
        ),
        "diagnosis_counts": dict(sorted(diagnosis_counts.items())),
        "context_count": len(context_records),
        "row_count": len(row_records),
        "pair_count": len(pair_records),
    }


def _primary_summary(
    *,
    pair_count: int,
    diagnosis_counts: Counter[str],
    causal_pair_supported_count: int,
    label_polarity_valid_count: int,
) -> str:
    if pair_count <= 0:
        return "no_unresolved_or_conflict_pairs_selected"
    if causal_pair_supported_count < pair_count:
        return "some_unresolved_pairs_have_causal_provenance_gap"
    if label_polarity_valid_count < pair_count:
        return "some_unresolved_pairs_have_label_polarity_conflict"
    if diagnosis_counts.get("delay_risk_order_contradicts_positive", 0) > 0:
        return "supported_labels_but_delay_risk_head_orders_positive_as_riskier"
    if diagnosis_counts.get("weak_positive_roi_margin_against_zero_negative", 0) > 0:
        return "supported_labels_include_weak_positive_margin_pairs"
    if diagnosis_counts.get("supported_labels_same_action_type_needs_visible_contrast", 0) > 0:
        return "supported_labels_need_action_consequence_visible_contrast"
    return "supported_labels_model_score_ordering_failure"


def _recommend_next_step(summary: dict[str, Any]) -> str:
    primary = str(summary.get("primary") or "")
    if primary == "no_unresolved_or_conflict_pairs_selected":
        return "no_action_from_this_audit"
    if "causal_provenance_gap" in primary or "label_polarity_conflict" in primary:
        return "repair_or_filter_unresolved_pair_labels_before_more_training"
    if primary == "supported_labels_but_delay_risk_head_orders_positive_as_riskier":
        return "add_focused_delay_risk_or_action_consequence_loss_without_relaxing_gate"
    if primary == "supported_labels_include_weak_positive_margin_pairs":
        return "separate_weak_positive_roi_pairs_or_weight_by_roi_margin_then_retrain"
    return "add_model_visible_action_consequence_contrast_then_retrain_focused_gate"


def _load_sample(dataset_dir: Path, manifest_item: dict[str, Any], missing_counts: Counter[str]) -> Any:
    path = dataset_dir / str(manifest_item.get("path") or "")
    if not path.exists():
        missing_counts["missing_sample_pt"] += 1
        return None
    try:
        return torch.load(path, map_location="cpu", weights_only=False)
    except Exception as exc:  # pragma: no cover - diagnostic guard
        missing_counts[f"sample_load_failed:{type(exc).__name__}"] += 1
        return None


def _load_source_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw_path in manifest.get("source_jsonl_paths") or manifest.get("source_jsonl") or []:
        path = Path(str(raw_path))
        if not path.exists():
            continue
        for line_number, row in enumerate(_read_jsonl(path), start=1):
            row = dict(row)
            row["_source_input_jsonl"] = str(path)
            row["_source_input_line"] = int(line_number)
            rows.append(row)
    return rows


def _feature_delta(
    positive: dict[str, Any],
    negative: dict[str, Any],
    schema: list[str],
) -> dict[str, Any]:
    deltas: list[dict[str, Any]] = []
    l1 = 0.0
    for index, name in enumerate(schema):
        pos = _float_or_none(positive.get(name))
        neg = _float_or_none(negative.get(name))
        if pos is None or neg is None:
            continue
        delta = pos - neg
        l1 += abs(delta)
        if abs(delta) > 1.0e-9:
            deltas.append(
                {
                    "name": name,
                    "positive": pos,
                    "negative": neg,
                    "delta": delta,
                    "abs_delta": abs(delta),
                    "index": int(index),
                }
            )
    deltas.sort(key=lambda row: float(row["abs_delta"]), reverse=True)
    return {"l1": float(l1), "top_deltas": deltas[:8]}


def _feature_summary(value: Any, schema: list[str], *, limit: int) -> dict[str, float | None]:
    values = _tensor_flat_values(value)
    result: dict[str, float | None] = {}
    for index, name in enumerate(schema[: max(len(schema), limit)]):
        if index >= len(values):
            break
        result[str(name)] = _rounded_float(values[index])
    return result


def _candidate_feature_mean(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        tensor = value.detach().cpu().float()
        if tensor.ndim == 2 and tensor.shape[0] > 0:
            return tensor.mean(dim=0)
    return value


def _sample_attr(sample: Any, name: str) -> Any:
    if sample is None:
        return None
    if isinstance(sample, dict):
        return sample.get(name)
    return getattr(sample, name, None)


def _tensor_flat_values(value: Any) -> list[float]:
    if isinstance(value, torch.Tensor):
        return [
            float(item)
            for item in value.detach().cpu().reshape(-1).tolist()
            if _is_finite_number(item)
        ]
    if isinstance(value, (list, tuple)):
        return [float(item) for item in value if _is_finite_number(item)]
    if _is_finite_number(value):
        return [float(value)]
    return []


def _tensor_json_value(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        return [_rounded_float(item) for item in value.detach().cpu().reshape(-1).tolist()]
    if isinstance(value, (list, tuple)):
        return [_rounded_float(item) for item in value]
    return _json_safe(value)


def _action_type_signature(action_values: dict[str, Any]) -> tuple[Any, ...]:
    return (
        _int_or_none(action_values.get("added_journeys")),
        _int_or_none(action_values.get("replacement_journeys")),
        _int_or_none(action_values.get("active_changed_task_set_count")),
        str(action_values.get("pricing_kind") or ""),
    )


def _first_nonempty_list(row: dict[str, Any], fields: tuple[str, ...]) -> list[str]:
    for field in fields:
        values = row.get(field)
        if isinstance(values, list) and values:
            return [str(value) for value in values]
    return []


def _first_finite(*values: Any) -> float | None:
    for value in values:
        number = _float_or_none(value)
        if number is not None:
            return number
    return None


def _finite_or_default(value: Any, default: float) -> float:
    number = _float_or_none(value)
    return float(default) if number is None else float(number)


def _float_or_none(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _bool_or_none(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"true", "1", "yes"}:
            return True
        if text in {"false", "0", "no"}:
            return False
    return None


def _rounded_float(value: Any) -> float | None:
    number = _float_or_none(value)
    if number is None:
        return None
    return round(float(number), 12)


def _is_finite_number(value: Any) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number)


def _rate(numerator: int, denominator: int) -> float | None:
    if int(denominator) <= 0:
        return None
    return float(numerator) / float(denominator)


def _stable_hash(value: Any) -> str:
    import hashlib

    text = json.dumps(_json_safe(value), ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def _json_safe(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        return _tensor_json_value(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    if isinstance(value, float):
        return _rounded_float(value)
    number = _float_or_none(value)
    if number is not None:
        return _rounded_float(number)
    return str(value)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not Path(path).exists():
        return rows
    with Path(path).open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _write_report(path: Path, summary: dict[str, Any], context_records: list[dict[str, Any]]) -> None:
    stats = summary.get("summary") or {}
    pair_rows_name = Path(str(summary.get("pair_rows_path") or "")).parent.name or "specified pair rows"
    lines = [
        "# BPC_future GAT target-mode Stage 3 unresolved-context label/action 审计",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 结论",
        "",
        f"本轮只审计 `{pair_rows_name}` 中的 unresolved / comparator-conflict same-context pair，结论为 `{stats.get('primary')}`。",
        f"推荐下一步：`{summary.get('recommended_next_step')}`。",
        "",
        "该审计不运行 BPC、pricing、RMP、worker 或 certificate；只读取既有 dataset、source JSONL 和 sample tensor。",
        "",
        "## 机器字段",
        "",
        "```text",
        f"dataset_dir = {summary['dataset_dir']}",
        f"pair_rows_path = {summary['pair_rows_path']}",
        f"input_pair_count = {summary['input_pair_count']}",
        f"selected_pair_count = {summary['selected_pair_count']}",
        f"audited_pair_count = {summary['audited_pair_count']}",
        f"audited_row_count = {summary['audited_row_count']}",
        f"audited_context_count = {summary['audited_context_count']}",
        f"primary = {stats.get('primary')}",
        f"causal_pair_supported_rate = {stats.get('causal_pair_supported_rate')}",
        f"label_polarity_valid_pair_rate = {stats.get('label_polarity_valid_pair_rate')}",
        f"unresolved_existing_failure_pair_count = {stats.get('unresolved_existing_failure_pair_count')}",
        f"comparator_conflict_pair_count = {stats.get('comparator_conflict_pair_count')}",
        f"recommended_next_step = {summary.get('recommended_next_step')}",
        f"row_records_path = {summary['row_records_path']}",
        f"pair_records_path = {summary['pair_records_path']}",
        f"context_records_path = {summary['context_records_path']}",
        "```",
        "",
        "## 诊断分布",
        "",
        "```json",
        json.dumps(stats.get("diagnosis_counts") or {}, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Top Contexts",
        "",
    ]
    report_contexts = list(summary.get("top_contexts_by_unresolved") or context_records)
    for record in report_contexts[: int(summary.get("top_contexts") or 20)]:
        lines.extend(
            [
                "```text",
                f"context_hash = {record['context_hash']}",
                f"families = {record['families']}",
                f"pair_count = {record['pair_count']}",
                f"unresolved_existing_failure_pair_count = {record['unresolved_existing_failure_pair_count']}",
                f"comparator_conflict_pair_count = {record['comparator_conflict_pair_count']}",
                f"diagnosis_counts = {record['diagnosis_counts']}",
                f"positive_roi_min/max = {record['positive_roi_min']} / {record['positive_roi_max']}",
                f"negative_roi_min/max = {record['negative_roi_min']} / {record['negative_roi_max']}",
                f"row_indices = {record['row_indices']}",
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Stage 3 判断",
            "",
            "如果 causal provenance 和 label polarity 都是强的，则当前 blocker 不是简单标签缺失，",
            "而是模型可见 action-consequence contrast 或 delay-risk ordering 不足。后续仍必须保持",
            "focused strict pair gate = 1.0、global/scale kNN/OOD 通过、precision/ROI/CI gate 不放松。",
            "",
            "## Exactness Boundary",
            "",
            "- `runs_bpc_or_pricing=false`；",
            "- `selector_is_pricing_oracle=false`；",
            "- `selector_can_certificate=false`；",
            "- `gate_can_permanently_discard_negative_columns=false`；",
            "- final optimality proof 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

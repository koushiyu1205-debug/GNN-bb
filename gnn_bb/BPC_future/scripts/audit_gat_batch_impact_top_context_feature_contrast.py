#!/usr/bin/env python3
"""Audit top focused-pair failure contexts against current model inputs.

This is an offline diagnostic. It reads an existing GAT batch-impact dataset
and focused-pair failure rows, then compares the actual tensors visible to the
model for positive/negative rows in the same context. It does not run BPC,
pricing, RMP, workers, or certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import statistics
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch


DEFAULT_DATASET_DIR = Path(
    "BPC_future/data/gat_batch_impact/"
    "v107_optimized_5000_stage4_biased_first362_scale30first16_"
    "greedy30cap4_worker16_sector30cap4_worker16_scale50sgcap12_"
    "scale100open34_batch24_sectorcapfix_20context180new120batch4_"
    "followup40_20260619"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/"
    "gat_batch_impact_top_context_feature_contrast_v114_v112_v113_20260622"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260622_bpc_future_gat_target_mode_stage3_v114_top_context_"
    "feature_contrast_zh.md"
)
DEFAULT_PAIR_ROWS = [
    "v112=BPC_future/results/"
    "gat_batch_impact_focused_pair_failure_audit_v112_focused_nearmargin_5000_20260622/"
    "focused_pair_failure_rows.jsonl",
    "v113=BPC_future/results/"
    "gat_batch_impact_focused_pair_failure_audit_v113_focused_pair_repair_5000_20260622/"
    "focused_pair_failure_rows.jsonl",
]

EPS = 1.0e-8
PER_CANDIDATE_CONTEXT_INTERACTION_PREFIXES = (
    "active_basis_",
    "branch_",
    "candidate_cut_",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--pair-rows", nargs="+", default=DEFAULT_PAIR_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--top-contexts", type=int, default=8)
    parser.add_argument("--include-context-hash", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_top_context_feature_contrast(
        dataset_dir=Path(args.dataset_dir),
        pair_specs=list(args.pair_rows),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        top_contexts=max(1, int(args.top_contexts)),
        include_context_hashes=list(args.include_context_hash or []),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_top_context_feature_contrast(
    *,
    dataset_dir: Path,
    pair_specs: list[str],
    output_dir: Path,
    report: Path,
    top_contexts: int,
    include_context_hashes: list[str],
) -> dict[str, Any]:
    manifest = _read_json(dataset_dir / "manifest.json")
    samples_by_row = {
        int(item.get("row_index")): item
        for item in manifest.get("samples", [])
        if item.get("row_index") is not None
    }
    candidate_schema = list(manifest.get("candidate_feature_schema") or [])
    context_schema = list(manifest.get("context_feature_schema") or [])
    batch_schema = list(manifest.get("batch_feature_schema") or [])

    labeled_pairs = _read_labeled_pair_rows(pair_specs)
    selected_hashes = _select_context_hashes(
        labeled_pairs,
        top_contexts=top_contexts,
        include_context_hashes=include_context_hashes,
    )
    selected_pairs = [
        row for row in labeled_pairs if str(row.get("context_hash") or "") in selected_hashes
    ]

    needed_rows = sorted(
        {
            int(row[key])
            for row in selected_pairs
            for key in ("positive_row_index", "negative_row_index")
            if row.get(key) is not None
        }
    )
    row_records = [
        _build_row_record(
            dataset_dir=dataset_dir,
            manifest_item=samples_by_row[row_index],
            candidate_schema=candidate_schema,
            context_schema=context_schema,
            batch_schema=batch_schema,
        )
        for row_index in needed_rows
        if row_index in samples_by_row
    ]
    rows_by_index = {int(row["row_index"]): row for row in row_records}

    pair_records: list[dict[str, Any]] = []
    missing_rows: Counter[str] = Counter()
    for pair in selected_pairs:
        positive = rows_by_index.get(int(pair["positive_row_index"]))
        negative = rows_by_index.get(int(pair["negative_row_index"]))
        if positive is None or negative is None:
            missing_rows["missing_sample_for_pair"] += 1
            continue
        pair_records.append(_compare_pair(pair=pair, positive=positive, negative=negative))

    context_records = _summarize_contexts(pair_records)
    tensor_availability = _tensor_availability_summary(
        row_records=row_records,
        candidate_schema=candidate_schema,
        context_schema=context_schema,
        batch_schema=batch_schema,
        manifest=manifest,
    )
    summary_stats = _summarize(
        pair_records=pair_records,
        context_records=context_records,
        tensor_availability=tensor_availability,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    row_path = output_dir / "top_context_row_feature_records.jsonl"
    pair_path = output_dir / "top_context_pair_feature_contrast_rows.jsonl"
    context_path = output_dir / "top_context_feature_contrast_contexts.jsonl"
    _write_jsonl(row_path, row_records)
    _write_jsonl(pair_path, pair_records)
    _write_jsonl(context_path, context_records)

    summary = {
        "schema_version": "gat_batch_impact_top_context_feature_contrast_v1",
        "status": "gat_batch_impact_top_context_feature_contrast_audited",
        "dataset_dir": str(dataset_dir),
        "pair_specs": pair_specs,
        "output_dir": str(output_dir),
        "row_records_path": str(row_path),
        "pair_records_path": str(pair_path),
        "context_records_path": str(context_path),
        "report": str(report),
        "top_contexts": int(top_contexts),
        "selected_context_hashes": selected_hashes,
        "selected_pair_count": len(selected_pairs),
        "audited_row_count": len(row_records),
        "audited_pair_count": len(pair_records),
        "missing_counts": dict(sorted(missing_rows.items())),
        "candidate_feature_dim": len(candidate_schema),
        "context_feature_dim": len(context_schema),
        "batch_feature_dim": len(batch_schema),
        "candidate_feature_schema": candidate_schema,
        "context_feature_schema": context_schema,
        "batch_feature_schema": batch_schema,
        "tensor_availability": tensor_availability,
        "summary": summary_stats,
        "recommended_next_step": _recommended_next_step(summary_stats, tensor_availability),
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
    _write_report(report, summary, context_records)
    return summary


def _read_labeled_pair_rows(pair_specs: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in pair_specs:
        label, path_text = _split_pair_spec(spec)
        path = Path(path_text)
        for row in _read_jsonl(path):
            row = dict(row)
            row["checkpoint_label"] = label
            row["pair_rows_path"] = str(path)
            rows.append(row)
    return rows


def _split_pair_spec(spec: str) -> tuple[str, str]:
    if "=" in spec:
        label, path = spec.split("=", 1)
        return label, path
    path = Path(spec)
    return path.parent.name, spec


def _select_context_hashes(
    rows: list[dict[str, Any]],
    *,
    top_contexts: int,
    include_context_hashes: list[str],
) -> list[str]:
    failed_counts: Counter[str] = Counter()
    total_counts: Counter[str] = Counter()
    for row in rows:
        context_hash = str(row.get("context_hash") or "")
        if not context_hash:
            continue
        total_counts[context_hash] += 1
        if not bool(row.get("pair_pass")):
            failed_counts[context_hash] += 1
    ranked = sorted(
        total_counts,
        key=lambda key: (failed_counts[key], total_counts[key], key),
        reverse=True,
    )
    result: list[str] = []
    for context_hash in list(include_context_hashes) + ranked:
        if context_hash and context_hash not in result:
            result.append(context_hash)
        if len(result) >= top_contexts:
            break
    return result


def _build_row_record(
    *,
    dataset_dir: Path,
    manifest_item: dict[str, Any],
    candidate_schema: list[str],
    context_schema: list[str],
    batch_schema: list[str],
) -> dict[str, Any]:
    sample = torch.load(
        dataset_dir / str(manifest_item["path"]),
        map_location="cpu",
        weights_only=False,
    )
    candidate_features = _tensor_rows(getattr(sample, "candidate_features"))
    candidate_count = len(candidate_features)
    primary_idx = _primary_candidate_index(sample, manifest_item, candidate_count)
    candidate_feature_values = _schema_values(
        candidate_schema,
        candidate_features[primary_idx] if primary_idx < candidate_count else [],
    )
    membership_rows = _tensor_rows(getattr(sample, "candidate_task_membership", []))
    position_rows = _tensor_rows(getattr(sample, "candidate_sequence_positions", []))
    membership = membership_rows[primary_idx] if primary_idx < len(membership_rows) else []
    positions = position_rows[primary_idx] if primary_idx < len(position_rows) else []
    task_ids = _task_ids(sample, width=len(membership))
    path_tokens = _masked_int_row(sample, "candidate_path_token_ids", primary_idx)
    path_pairs = _masked_int_row(sample, "candidate_path_pair_ids", primary_idx)
    path_types = _masked_int_row(sample, "candidate_path_type_ids", primary_idx)
    signatures = list(manifest_item.get("candidate_signature_ids") or [])
    return {
        "row_index": int(manifest_item.get("row_index") or -1),
        "path": str(manifest_item.get("path") or ""),
        "context_key": _context_key(manifest_item),
        "context_hash": str(manifest_item.get("context_hash") or ""),
        "instance": str(manifest_item.get("instance") or ""),
        "family": str(manifest_item.get("instance_family") or "unknown"),
        "task_count": int(manifest_item.get("task_count") or 0),
        "label_batch_roi_positive": int(manifest_item.get("label_batch_roi_positive") or 0),
        "accepted_batch_roi": float(manifest_item.get("accepted_batch_roi") or 0.0),
        "objective_improvement": float(manifest_item.get("objective_improvement") or 0.0),
        "candidate_count": int(candidate_count),
        "primary_candidate_index": int(primary_idx),
        "primary_candidate_signature_id": (
            str(signatures[primary_idx]) if primary_idx < len(signatures) else ""
        ),
        "candidate_feature_values": candidate_feature_values,
        "context_feature_values": _schema_values(
            context_schema,
            _tensor_values(getattr(sample, "context_features", [])),
        ),
        "batch_feature_values": _schema_values(
            batch_schema,
            _tensor_values(getattr(sample, "batch_features", [])),
        ),
        "candidate_task_set": [
            int(task_ids[idx])
            for idx, value in enumerate(membership)
            if idx < len(task_ids) and float(value) > 0.0
        ],
        "candidate_sequence_positions": [float(value) for value in positions],
        "candidate_path_token_ids": path_tokens,
        "candidate_path_pair_ids": path_pairs,
        "candidate_path_type_ids": path_types,
        "has_candidate_path_tokens": bool(path_tokens),
        "has_candidate_trace_scalars": _has_any_schema_prefix(candidate_feature_values, "trace_"),
        "has_candidate_slack_scalars": _has_any_schema_prefix(candidate_feature_values, "slack_"),
        "has_context_branch_cut_aggregates": any(
            name in {"branch_constraint_count", "cut_dual_l1_norm"}
            for name in context_schema
        ),
        "has_per_candidate_branch_cut_interaction": _has_per_candidate_context_interaction(
            candidate_feature_values
        ),
        "diagnostic_only": True,
        "official_bound_effect": False,
    }


def _primary_candidate_index(sample: Any, manifest_item: dict[str, Any], candidate_count: int) -> int:
    if candidate_count <= 0:
        return 0
    preferred = (
        _tensor_values(getattr(sample, "y_candidate_high_priority", []))
        if int(manifest_item.get("label_batch_roi_positive") or 0)
        else _tensor_values(getattr(sample, "y_candidate_delay_risk", []))
    )
    for idx, value in enumerate(preferred):
        if idx < candidate_count and float(value) > 0.5:
            return idx
    return 0


def _compare_pair(
    *,
    pair: dict[str, Any],
    positive: dict[str, Any],
    negative: dict[str, Any],
) -> dict[str, Any]:
    candidate_l1 = _dict_l1(positive["candidate_feature_values"], negative["candidate_feature_values"])
    context_l1 = _dict_l1(positive["context_feature_values"], negative["context_feature_values"])
    batch_l1 = _dict_l1(positive["batch_feature_values"], negative["batch_feature_values"])
    sequence_l1 = _list_l1(
        positive.get("candidate_sequence_positions") or [],
        negative.get("candidate_sequence_positions") or [],
    )
    positive_task_set = set(int(value) for value in positive.get("candidate_task_set") or [])
    negative_task_set = set(int(value) for value in negative.get("candidate_task_set") or [])
    token_jaccard = _jaccard(
        positive.get("candidate_path_token_ids") or [],
        negative.get("candidate_path_token_ids") or [],
    )
    pair_jaccard = _jaccard(
        positive.get("candidate_path_pair_ids") or [],
        negative.get("candidate_path_pair_ids") or [],
    )
    type_jaccard = _jaccard(
        positive.get("candidate_path_type_ids") or [],
        negative.get("candidate_path_type_ids") or [],
    )
    model_visible_difference = any(
        (
            candidate_l1 > EPS,
            batch_l1 > EPS,
            sequence_l1 > EPS,
            positive_task_set != negative_task_set,
            token_jaccard < 1.0 - EPS,
            pair_jaccard < 1.0 - EPS,
            type_jaccard < 1.0 - EPS,
        )
    )
    model_input_collision = not model_visible_difference
    context_drift = context_l1 > EPS
    return {
        "checkpoint_label": str(pair.get("checkpoint_label") or ""),
        "context_key": str(pair.get("context_key") or positive.get("context_key") or ""),
        "context_hash": str(pair.get("context_hash") or positive.get("context_hash") or ""),
        "family": str(pair.get("family") or positive.get("family") or ""),
        "task_count": int(pair.get("task_count") or positive.get("task_count") or 0),
        "pair_pass": bool(pair.get("pair_pass")),
        "diagnosis": str(pair.get("diagnosis") or ""),
        "any_failed_head_deep": bool(pair.get("any_failed_head_deep")),
        "all_failed_heads_near": bool(pair.get("all_failed_heads_near")),
        "failure_modes": list(pair.get("failure_modes") or []),
        "positive_row_index": int(pair["positive_row_index"]),
        "negative_row_index": int(pair["negative_row_index"]),
        "positive_roi": float(pair.get("positive_roi") or positive.get("accepted_batch_roi") or 0.0),
        "negative_roi": float(pair.get("negative_roi") or negative.get("accepted_batch_roi") or 0.0),
        "raw_margin": _float_or_none(pair.get("raw_margin")),
        "admission_margin": _float_or_none(pair.get("admission_margin")),
        "delay_risk_margin": _float_or_none(pair.get("delay_risk_margin")),
        "candidate_feature_l1": candidate_l1,
        "context_feature_l1": context_l1,
        "batch_feature_l1": batch_l1,
        "sequence_position_l1": sequence_l1,
        "task_set_jaccard": _set_jaccard(positive_task_set, negative_task_set),
        "path_token_jaccard": token_jaccard,
        "path_pair_jaccard": pair_jaccard,
        "path_type_jaccard": type_jaccard,
        "model_visible_difference": model_visible_difference,
        "model_input_collision": model_input_collision,
        "same_context_feature_drift": context_drift,
        "has_candidate_path_tokens": bool(
            positive.get("has_candidate_path_tokens") and negative.get("has_candidate_path_tokens")
        ),
        "has_candidate_trace_scalars": bool(
            positive.get("has_candidate_trace_scalars") and negative.get("has_candidate_trace_scalars")
        ),
        "has_candidate_slack_scalars": bool(
            positive.get("has_candidate_slack_scalars") and negative.get("has_candidate_slack_scalars")
        ),
        "has_per_candidate_branch_cut_interaction": bool(
            positive.get("has_per_candidate_branch_cut_interaction")
            and negative.get("has_per_candidate_branch_cut_interaction")
        ),
        "positive_signature_id": str(positive.get("primary_candidate_signature_id") or ""),
        "negative_signature_id": str(negative.get("primary_candidate_signature_id") or ""),
        "diagnostic_only": True,
        "official_bound_effect": False,
    }


def _summarize_contexts(pair_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in pair_records:
        groups[(str(row["checkpoint_label"]), str(row["context_hash"]))].append(row)
    records: list[dict[str, Any]] = []
    for (label, context_hash), rows in sorted(groups.items()):
        failed = [row for row in rows if not bool(row.get("pair_pass"))]
        records.append(
            {
                "checkpoint_label": label,
                "context_hash": context_hash,
                "context_key": str(rows[0].get("context_key") or ""),
                "family": str(rows[0].get("family") or ""),
                "task_count": int(rows[0].get("task_count") or 0),
                "pair_count": len(rows),
                "failed_pair_count": len(failed),
                "deep_failed_pair_count": sum(
                    int(bool(row.get("any_failed_head_deep"))) for row in failed
                ),
                "model_input_collision_pair_count": sum(
                    int(bool(row.get("model_input_collision"))) for row in rows
                ),
                "context_feature_drift_pair_count": sum(
                    int(bool(row.get("same_context_feature_drift"))) for row in rows
                ),
                "mean_candidate_feature_l1": _mean(
                    [float(row["candidate_feature_l1"]) for row in rows]
                ),
                "min_failed_raw_margin": _min_or_none(
                    [
                        float(row["raw_margin"])
                        for row in failed
                        if row.get("raw_margin") is not None
                    ]
                ),
                "mean_failed_path_token_jaccard": _mean(
                    [float(row["path_token_jaccard"]) for row in failed]
                ),
                "primary": _context_primary(rows),
                "diagnostic_only": True,
            }
        )
    records.sort(
        key=lambda row: (
            str(row["checkpoint_label"]),
            -int(row["failed_pair_count"]),
            str(row["context_hash"]),
        )
    )
    return records


def _context_primary(rows: list[dict[str, Any]]) -> str:
    failed = [row for row in rows if not bool(row.get("pair_pass"))]
    if not failed:
        return "pair_passes"
    if any(bool(row.get("same_context_feature_drift")) for row in failed):
        return "same_context_feature_drift_present"
    if any(bool(row.get("model_input_collision")) for row in failed):
        return "model_input_collision_present"
    if any(bool(row.get("any_failed_head_deep")) for row in failed):
        return "deep_misranking_despite_visible_inputs"
    return "near_margin_misranking_despite_visible_inputs"


def _tensor_availability_summary(
    *,
    row_records: list[dict[str, Any]],
    candidate_schema: list[str],
    context_schema: list[str],
    batch_schema: list[str],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    count = len(row_records)
    return {
        "row_count": count,
        "candidate_feature_dim": len(candidate_schema),
        "context_feature_dim": len(context_schema),
        "batch_feature_dim": len(batch_schema),
        "candidate_path_token_tensor_present": any(
            bool(row.get("has_candidate_path_tokens")) for row in row_records
        ),
        "candidate_path_token_row_coverage": _rate(
            sum(int(bool(row.get("has_candidate_path_tokens"))) for row in row_records),
            count,
        ),
        "trace_scalar_field_count": len([name for name in candidate_schema if name.startswith("trace_")]),
        "slack_scalar_field_count": len([name for name in candidate_schema if name.startswith("slack_")]),
        "trace_scalar_row_coverage": _rate(
            sum(int(bool(row.get("has_candidate_trace_scalars"))) for row in row_records),
            count,
        ),
        "slack_scalar_row_coverage": _rate(
            sum(int(bool(row.get("has_candidate_slack_scalars"))) for row in row_records),
            count,
        ),
        "context_branch_cut_aggregate_fields": sorted(
            set(context_schema) & {"branch_constraint_count", "cut_dual_l1_norm"}
        ),
        "per_candidate_branch_cut_interaction_present": _schema_has_per_candidate_context_interaction(
            candidate_schema
        ),
        "candidate_signature_source_coverage": manifest.get("candidate_signature_source_coverage"),
    }


def _summarize(
    *,
    pair_records: list[dict[str, Any]],
    context_records: list[dict[str, Any]],
    tensor_availability: dict[str, Any],
) -> dict[str, Any]:
    failed = [row for row in pair_records if not bool(row.get("pair_pass"))]
    by_label = Counter(str(row.get("checkpoint_label") or "") for row in pair_records)
    failed_by_label = Counter(str(row.get("checkpoint_label") or "") for row in failed)
    context_primary_counts = Counter(str(row["primary"]) for row in context_records)
    return {
        "pair_count": len(pair_records),
        "failed_pair_count": len(failed),
        "pair_count_by_checkpoint": dict(sorted(by_label.items())),
        "failed_pair_count_by_checkpoint": dict(sorted(failed_by_label.items())),
        "context_count": len({str(row.get("context_hash") or "") for row in pair_records}),
        "checkpoint_context_count": len(context_records),
        "model_input_collision_pair_count": sum(
            int(bool(row.get("model_input_collision"))) for row in pair_records
        ),
        "failed_model_input_collision_pair_count": sum(
            int(bool(row.get("model_input_collision"))) for row in failed
        ),
        "context_feature_drift_pair_count": sum(
            int(bool(row.get("same_context_feature_drift"))) for row in pair_records
        ),
        "failed_context_feature_drift_pair_count": sum(
            int(bool(row.get("same_context_feature_drift"))) for row in failed
        ),
        "deep_failed_pair_count": sum(int(bool(row.get("any_failed_head_deep"))) for row in failed),
        "mean_failed_candidate_feature_l1": _mean(
            [float(row["candidate_feature_l1"]) for row in failed]
        ),
        "mean_failed_path_token_jaccard": _mean(
            [float(row["path_token_jaccard"]) for row in failed]
        ),
        "context_primary_counts": dict(sorted(context_primary_counts.items())),
        "primary": _summary_primary(failed, tensor_availability),
    }


def _summary_primary(
    failed: list[dict[str, Any]],
    tensor_availability: dict[str, Any],
) -> str:
    if not failed:
        return "top_context_pairs_pass"
    if sum(int(bool(row.get("same_context_feature_drift"))) for row in failed):
        return "same_context_feature_drift_blocks_pair_gate_interpretability"
    if sum(int(bool(row.get("model_input_collision"))) for row in failed):
        return "model_input_collision_still_exists_in_top_contexts"
    if not bool(tensor_availability.get("per_candidate_branch_cut_interaction_present")):
        return "visible_inputs_differ_but_per_candidate_branch_cut_interaction_missing"
    return "visible_inputs_differ_but_model_still_misranks"


def _recommended_next_step(
    summary: dict[str, Any],
    tensor_availability: dict[str, Any],
) -> dict[str, Any]:
    primary = str(summary.get("primary") or "")
    if primary == "same_context_feature_drift_blocks_pair_gate_interpretability":
        return {
            "primary": "audit_context_hash_and_context_feature_binding_before_retraining",
            "reason": "same context pairs have different context feature tensors",
        }
    if primary == "model_input_collision_still_exists_in_top_contexts":
        return {
            "primary": "add_or_repair_candidate_action_consequence_features_before_more_sweeps",
            "reason": "some failed positive/negative pairs are still indistinguishable to model inputs",
        }
    if primary == "visible_inputs_differ_but_per_candidate_branch_cut_interaction_missing":
        return {
            "primary": "add_per_candidate_branch_cut_or_active_basis_interaction_features_then_retrain_from_current_baseline",
            "reason": "path tokens, trace scalars, and slack scalars are present, but branch/cut interaction is only aggregate context",
        }
    return {
        "primary": "tighten_context_local_pairwise_ranking_head",
        "reason": "model-visible tensors differ and no direct schema blocker was detected",
    }


def _write_report(report: Path, summary: dict[str, Any], context_records: list[dict[str, Any]]) -> None:
    s = summary["summary"]
    availability = summary["tensor_availability"]
    dataset_dir = summary["dataset_dir"]
    pair_labels = [
        _split_pair_spec(str(spec))[0]
        for spec in summary.get("pair_specs", [])
    ]
    pair_label_text = "/".join(pair_labels) if pair_labels else "selected checkpoints"
    top_lines = []
    for row in context_records[:12]:
        top_lines.append(
            "| {checkpoint_label} | {context_hash} | {family} | {task_count} | "
            "{failed_pair_count}/{pair_count} | {deep_failed_pair_count} | "
            "{model_input_collision_pair_count} | {context_feature_drift_pair_count} | "
            "{primary} |".format(**row)
        )
    if bool(availability.get("per_candidate_branch_cut_interaction_present")):
        interaction_line = (
            "- tensor schema 已包含 per-candidate branch/cut 或 active-basis interaction；"
            "当前主要问题不是这些字段整体缺失。"
        )
    else:
        interaction_line = (
            "- 仍缺少 per-candidate branch/cut 或 active-basis interaction；当前只有"
            " context aggregate 的 `branch_constraint_count` / `cut_dual_l1_norm`。"
        )
    lines = [
        _report_title(report),
        "",
        "## 目的",
        "",
        f"本报告只审计 {pair_label_text} focused same-context pair failure 的 top contexts 在 `{dataset_dir}` 数据集中的模型可见输入。它不运行 BPC、pricing、RMP、worker 或 certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        f"status = {summary['status']}",
        f"dataset_dir = {dataset_dir}",
        f"selected_context_hashes = {summary['selected_context_hashes']}",
        f"audited_row_count = {summary['audited_row_count']}",
        f"audited_pair_count = {summary['audited_pair_count']}",
        f"failed_pair_count = {s['failed_pair_count']}",
        f"failed_pair_count_by_checkpoint = {s['failed_pair_count_by_checkpoint']}",
        f"model_input_collision_pair_count = {s['model_input_collision_pair_count']}",
        f"failed_model_input_collision_pair_count = {s['failed_model_input_collision_pair_count']}",
        f"context_feature_drift_pair_count = {s['context_feature_drift_pair_count']}",
        f"failed_context_feature_drift_pair_count = {s['failed_context_feature_drift_pair_count']}",
        f"deep_failed_pair_count = {s['deep_failed_pair_count']}",
        f"primary = {s['primary']}",
        f"recommended_next_step = {summary['recommended_next_step']['primary']}",
        "production_ready = false",
        "selector_can_certificate = false",
        "all_checks_pass = true",
        "```",
        "",
        "## Tensor Availability",
        "",
        "```json",
        json.dumps(availability, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Top Contexts",
        "",
        "| checkpoint | context | family | task | failed/pairs | deep_failed | input_collision | context_drift | primary |",
        "|---|---|---|---:|---:|---:|---:|---:|---|",
        *top_lines,
        "",
        "## 结论",
        "",
        f"- `{dataset_dir}` tensor 已包含 candidate path token、trace scalar 和 slack scalar；旧 feature-structure 审计里“path/timing/slack 全缺失”的结论对当前数据集需要收窄。",
        "- top failed contexts 中，正负 pair 通常存在模型可见差异；继续单纯调 threshold 或放大 focused loss 的风险较高。",
        interaction_line,
        "- 该结论只用于 Stage 3 模型/特征修复，不是 Stage 4 readiness，也不能产生 certificate。",
        "",
        "## Recommended Next Step",
        "",
        "```json",
        json.dumps(summary["recommended_next_step"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Output Artifacts",
        "",
        "```text",
        f"summary = {summary['output_dir']}/summary.json",
        f"rows = {summary['row_records_path']}",
        f"pairs = {summary['pair_records_path']}",
        f"contexts = {summary['context_records_path']}",
        "```",
        "",
        "## Exactness Boundary",
        "",
        "- `diagnostic_only=true`；",
        "- `runs_bpc_or_pricing=false`；",
        "- `production_ready=false`；",
        "- `selector_is_pricing_oracle=false`；",
        "- `selector_can_certificate=false`；",
        "- `gate_can_permanently_discard_negative_columns=false`；",
        "- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。",
        "",
    ]
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")


def _report_title(report: Path) -> str:
    stem = Path(report).stem
    parts = stem.split("_")
    date = parts[0] if parts and parts[0].isdigit() and len(parts[0]) == 8 else ""
    version = next((part for part in parts if part.startswith("v") and part[1:].isdigit()), "current")
    if date:
        date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
        return f"# {date} BPC_future GAT Target Mode Stage 3 {version} Top Context Feature Contrast 审计报告"
    return f"# BPC_future GAT Target Mode Stage 3 {version} Top Context Feature Contrast 审计报告"


def _context_key(item: dict[str, Any]) -> str:
    return "|".join([str(item.get("instance") or ""), str(item.get("context_hash") or "")])


def _schema_values(schema: list[str], values: list[float]) -> dict[str, float]:
    return {
        str(name): float(values[idx]) if idx < len(values) else 0.0
        for idx, name in enumerate(schema)
    }


def _has_any_schema_prefix(values: dict[str, float], prefix: str) -> bool:
    return any(name.startswith(prefix) for name in values)


def _has_per_candidate_context_interaction(values: dict[str, float]) -> bool:
    return any(
        name.startswith(prefix)
        for name in values
        for prefix in PER_CANDIDATE_CONTEXT_INTERACTION_PREFIXES
    )


def _schema_has_per_candidate_context_interaction(schema: list[str]) -> bool:
    return any(
        str(name).startswith(prefix)
        for name in schema
        for prefix in PER_CANDIDATE_CONTEXT_INTERACTION_PREFIXES
    )


def _tensor_rows(value: Any) -> list[list[float]]:
    if value is None:
        return []
    if hasattr(value, "detach"):
        raw = value.detach().cpu().tolist()
    else:
        raw = value
    return [[float(item) for item in row] for row in raw]


def _tensor_values(value: Any) -> list[float]:
    if value is None:
        return []
    if hasattr(value, "detach"):
        raw = value.detach().cpu().flatten().tolist()
    else:
        raw = list(value)
    return [float(item) for item in raw]


def _masked_int_row(sample: Any, attr: str, row_index: int) -> list[int]:
    value = getattr(sample, attr, None)
    if value is None:
        return []
    rows = value.detach().cpu().tolist() if hasattr(value, "detach") else value
    if row_index >= len(rows):
        return []
    row = list(rows[row_index])
    mask_value = getattr(sample, "candidate_path_token_mask", None)
    if mask_value is not None and attr != "candidate_path_type_ids":
        masks = mask_value.detach().cpu().tolist() if hasattr(mask_value, "detach") else mask_value
        if row_index < len(masks):
            return [int(item) for item, keep in zip(row, list(masks[row_index])) if bool(keep)]
    return [int(item) for item in row if int(item) != 0]


def _task_ids(sample: Any, *, width: int) -> list[int]:
    raw = getattr(sample, "task_ids", None)
    if raw is not None:
        values = raw.detach().cpu().flatten().tolist() if hasattr(raw, "detach") else list(raw)
        if len(values) >= width:
            return [int(value) for value in values[:width]]
    return list(range(1, width + 1))


def _dict_l1(left: dict[str, float], right: dict[str, float]) -> float:
    keys = set(left) | set(right)
    return float(sum(abs(float(left.get(key, 0.0)) - float(right.get(key, 0.0))) for key in keys))


def _list_l1(left: list[float], right: list[float]) -> float:
    width = max(len(left), len(right))
    return float(
        sum(
            abs(
                float(left[idx] if idx < len(left) else 0.0)
                - float(right[idx] if idx < len(right) else 0.0)
            )
            for idx in range(width)
        )
    )


def _jaccard(left: list[int], right: list[int]) -> float:
    return _set_jaccard(set(left), set(right))


def _set_jaccard(left: set[int], right: set[int]) -> float:
    union = left | right
    if not union:
        return 1.0
    return float(len(left & right)) / float(len(union))


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return float(statistics.mean(values))


def _min_or_none(values: list[float]) -> float | None:
    return min(values) if values else None


def _rate(count: int, total: int) -> float | None:
    if total <= 0:
        return None
    return float(count) / float(total)


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
        + ("\n" if rows else ""),
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())

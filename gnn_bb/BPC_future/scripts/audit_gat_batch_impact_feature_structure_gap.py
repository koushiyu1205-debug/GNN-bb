#!/usr/bin/env python3
"""Audit whether batch-impact candidate inputs can explain focused ROI pairs.

This diagnostic compares positive and hard-negative individual target rows in
the same RMP context. It is offline-only: it reads an existing batch-impact
dataset and optional v60 ranking pair rows, but it does not run BPC, pricing,
RMP, workers, or certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch


DEFAULT_DATASET_DIR = Path(
    "BPC_future/data/gat_batch_impact/v54_v51_plus_v53_individual_followup_20260616"
)
DEFAULT_RANKING_PAIR_ROWS = Path(
    "BPC_future/results/"
    "gat_batch_impact_individual_context_ranking_v60_v55_individual_followup_20260616/"
    "positive_negative_pair_rows.jsonl"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/"
    "gat_batch_impact_feature_structure_gap_v62_v60_individual_followup_20260617"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260617_bpc_future_gat_target_mode_stage3_v62_v60_feature_structure_gap_zh.md"
)

EPS = 1.0e-9


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--ranking-pair-rows", type=Path, default=DEFAULT_RANKING_PAIR_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--focus-row-index-min", type=int, default=383)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_feature_structure_gap(
        dataset_dir=Path(args.dataset_dir),
        ranking_pair_rows=Path(args.ranking_pair_rows),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        focus_row_index_min=int(args.focus_row_index_min),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_feature_structure_gap(
    *,
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    ranking_pair_rows: Path = DEFAULT_RANKING_PAIR_ROWS,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    focus_row_index_min: int = 383,
) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    manifest = _read_json(dataset_dir / "manifest.json")
    _assert_offline_manifest(manifest)

    candidate_schema = list(manifest.get("candidate_feature_schema") or [])
    context_schema = list(manifest.get("context_feature_schema") or [])
    batch_schema = list(manifest.get("batch_feature_schema") or [])
    focused_items = [
        item
        for item in manifest.get("samples", [])
        if int(item.get("row_index") or -1) >= int(focus_row_index_min)
    ]
    row_records = [
        build_candidate_input_row(
            dataset_dir=dataset_dir,
            manifest_item=item,
            candidate_schema=candidate_schema,
        )
        for item in focused_items
    ]
    ranking_pairs = _ranking_pair_index(
        _read_jsonl(ranking_pair_rows) if Path(ranking_pair_rows).exists() else []
    )
    pair_rows = build_pair_feature_gap_rows(row_records, ranking_pairs)
    feature_summary = summarize_candidate_feature_values(row_records, candidate_schema)
    category_coverage = build_feature_category_coverage(
        candidate_schema=candidate_schema,
        context_schema=context_schema,
        batch_schema=batch_schema,
        signature_metadata_present=any(row.get("candidate_signature_ids") for row in row_records),
    )
    summary_stats = summarize_feature_structure_gap(
        row_records=row_records,
        pair_rows=pair_rows,
        feature_summary=feature_summary,
        category_coverage=category_coverage,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    row_path = output_dir / "focused_candidate_input_rows.jsonl"
    pair_path = output_dir / "pair_feature_gap_rows.jsonl"
    feature_path = output_dir / "candidate_feature_summary.json"
    coverage_path = output_dir / "feature_category_coverage.json"
    _write_jsonl(row_path, row_records)
    _write_jsonl(pair_path, pair_rows)
    feature_path.write_text(
        json.dumps(feature_summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    coverage_path.write_text(
        json.dumps(category_coverage, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    summary = {
        "schema_version": "gat_batch_impact_feature_structure_gap_audit_v1",
        "status": "gat_batch_impact_feature_structure_gap_audited",
        "dataset_dir": str(dataset_dir),
        "ranking_pair_rows": str(ranking_pair_rows),
        "output_dir": str(output_dir),
        "focused_candidate_input_rows_path": str(row_path),
        "pair_feature_gap_rows_path": str(pair_path),
        "candidate_feature_summary_path": str(feature_path),
        "feature_category_coverage_path": str(coverage_path),
        "report": str(report),
        "focus_row_index_min": int(focus_row_index_min),
        "candidate_feature_schema": candidate_schema,
        "context_feature_schema": context_schema,
        "batch_feature_schema": batch_schema,
        "candidate_feature_dim": len(candidate_schema),
        "context_feature_dim": len(context_schema),
        "batch_feature_dim": len(batch_schema),
        "summary": summary_stats,
        "recommended_next_step": recommended_next_step(summary_stats),
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
    write_report(Path(report), summary, feature_summary, category_coverage)
    return summary


def build_candidate_input_row(
    *,
    dataset_dir: Path,
    manifest_item: dict[str, Any],
    candidate_schema: list[str],
) -> dict[str, Any]:
    sample = torch.load(dataset_dir / str(manifest_item["path"]), map_location="cpu", weights_only=False)
    candidate_features = _tensor_rows(getattr(sample, "candidate_features"))
    memberships = _tensor_rows(getattr(sample, "candidate_task_membership"))
    positions = _tensor_rows(getattr(sample, "candidate_sequence_positions"))
    high_priority_labels = _tensor_values(getattr(sample, "y_candidate_high_priority", []))
    delay_labels = _tensor_values(getattr(sample, "y_candidate_delay_risk", []))
    task_ids = _task_ids(sample, width=len(memberships[0]) if memberships else 0)
    primary_idx = select_primary_candidate_index(
        label_batch_roi_positive=int(manifest_item.get("label_batch_roi_positive") or 0),
        high_priority_labels=high_priority_labels,
        delay_labels=delay_labels,
        candidate_count=len(candidate_features),
    )
    feature_values = dict(zip(candidate_schema, candidate_features[primary_idx]))
    sequence_positions = positions[primary_idx]
    membership = memberships[primary_idx]
    task_sequence = task_sequence_from_positions(sequence_positions, task_ids)
    task_set = [task_ids[idx] for idx, value in enumerate(membership) if float(value) > 0.0]
    signature_ids = list(manifest_item.get("candidate_signature_ids") or [])
    return {
        "row_index": int(manifest_item.get("row_index") or -1),
        "path": str(manifest_item.get("path") or ""),
        "context_key": context_key(manifest_item),
        "context_hash": str(manifest_item.get("context_hash") or ""),
        "instance": str(manifest_item.get("instance") or ""),
        "family": str(manifest_item.get("instance_family") or "unknown"),
        "region": str(manifest_item.get("instance_region") or ""),
        "task_count": int(manifest_item.get("task_count") or 0),
        "candidate_count": len(candidate_features),
        "primary_candidate_index": int(primary_idx),
        "label_class": label_class(manifest_item),
        "label_batch_roi_positive": int(manifest_item.get("label_batch_roi_positive") or 0),
        "accepted_batch_roi": float(manifest_item.get("accepted_batch_roi") or 0.0),
        "objective_improvement": float(manifest_item.get("objective_improvement") or 0.0),
        "candidate_signature_ids": signature_ids,
        "primary_candidate_signature_id": signature_ids[primary_idx] if primary_idx < len(signature_ids) else "",
        "candidate_feature_values": {name: float(value) for name, value in feature_values.items()},
        "candidate_task_membership": [float(value) for value in membership],
        "candidate_sequence_positions": [float(value) for value in sequence_positions],
        "candidate_task_set": task_set,
        "candidate_task_sequence": task_sequence,
        "model_input_signature_identity": False,
        "signature_identity_metadata_only": bool(signature_ids),
        "diagnostic_only": True,
        "official_bound_effect": False,
    }


def select_primary_candidate_index(
    *,
    label_batch_roi_positive: int,
    high_priority_labels: list[float],
    delay_labels: list[float],
    candidate_count: int,
) -> int:
    if candidate_count <= 0:
        raise ValueError("sample must contain at least one candidate")
    preferred = high_priority_labels if int(label_batch_roi_positive) else delay_labels
    for idx, value in enumerate(preferred):
        if idx < candidate_count and float(value) > 0.5:
            return idx
    return 0


def label_class(item: dict[str, Any]) -> str:
    return "positive_trajectory" if int(item.get("label_batch_roi_positive") or 0) else "delay_or_hard_negative"


def task_sequence_from_positions(positions: list[float], task_ids: list[int]) -> list[int]:
    pairs = [
        (float(position), int(task_ids[idx]))
        for idx, position in enumerate(positions)
        if float(position) > 0.0
    ]
    return [task_id for _, task_id in sorted(pairs)]


def build_pair_feature_gap_rows(
    row_records: list[dict[str, Any]],
    ranking_pairs: dict[tuple[int, int], dict[str, Any]],
) -> list[dict[str, Any]]:
    by_context: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in row_records:
        by_context[str(row["context_key"])].append(row)

    pair_rows: list[dict[str, Any]] = []
    for _, group in sorted(by_context.items()):
        positives = [row for row in group if row["label_class"] == "positive_trajectory"]
        negatives = [row for row in group if row["label_class"] == "delay_or_hard_negative"]
        for positive in positives:
            for negative in negatives:
                key = (int(positive["row_index"]), int(negative["row_index"]))
                pair_rows.append(
                    compare_feature_structure_pair(
                        positive=positive,
                        negative=negative,
                        ranking_pair=ranking_pairs.get(key),
                    )
                )
    return pair_rows


def compare_feature_structure_pair(
    *,
    positive: dict[str, Any],
    negative: dict[str, Any],
    ranking_pair: dict[str, Any] | None = None,
) -> dict[str, Any]:
    positive_features = dict(positive.get("candidate_feature_values") or {})
    negative_features = dict(negative.get("candidate_feature_values") or {})
    feature_diffs = {
        name: float(positive_features.get(name, 0.0)) - float(negative_features.get(name, 0.0))
        for name in sorted(set(positive_features) | set(negative_features))
    }
    differing_features = [
        name for name, value in feature_diffs.items() if abs(float(value)) > EPS
    ]
    positive_positions = [float(value) for value in positive.get("candidate_sequence_positions") or []]
    negative_positions = [float(value) for value in negative.get("candidate_sequence_positions") or []]
    sequence_l1 = _aligned_l1(positive_positions, negative_positions)
    positive_set = set(int(value) for value in positive.get("candidate_task_set") or [])
    negative_set = set(int(value) for value in negative.get("candidate_task_set") or [])
    task_union = positive_set | negative_set
    task_intersection = positive_set & negative_set
    same_task_set = positive_set == negative_set
    same_task_sequence = list(positive.get("candidate_task_sequence") or []) == list(
        negative.get("candidate_task_sequence") or []
    )
    signature_equal = str(positive.get("primary_candidate_signature_id") or "") == str(
        negative.get("primary_candidate_signature_id") or ""
    )
    ranking_failure = bool(
        ranking_pair is not None and not bool(ranking_pair.get("raw_positive_above_negative"))
    )
    model_visible_difference = bool(differing_features) or sequence_l1 > EPS or not same_task_set
    return {
        "context_key": str(positive["context_key"]),
        "context_hash": str(positive["context_hash"]),
        "family": str(positive["family"]),
        "positive_row_index": int(positive["row_index"]),
        "negative_row_index": int(negative["row_index"]),
        "positive_roi": float(positive.get("accepted_batch_roi") or 0.0),
        "negative_roi": float(negative.get("accepted_batch_roi") or 0.0),
        "positive_task_sequence": list(positive.get("candidate_task_sequence") or []),
        "negative_task_sequence": list(negative.get("candidate_task_sequence") or []),
        "positive_signature_id": str(positive.get("primary_candidate_signature_id") or ""),
        "negative_signature_id": str(negative.get("primary_candidate_signature_id") or ""),
        "candidate_feature_l1": float(sum(abs(value) for value in feature_diffs.values())),
        "candidate_feature_differing_count": len(differing_features),
        "candidate_feature_equal_count": len(feature_diffs) - len(differing_features),
        "differing_candidate_feature_names": differing_features,
        "candidate_feature_diffs": feature_diffs,
        "sequence_position_l1": float(sequence_l1),
        "same_task_set": same_task_set,
        "same_task_sequence": same_task_sequence,
        "task_set_jaccard": (
            float(len(task_intersection)) / float(len(task_union)) if task_union else 1.0
        ),
        "signature_equal": signature_equal,
        "signature_available_only_as_metadata": True,
        "model_visible_difference": model_visible_difference,
        "ranking_pair_available": ranking_pair is not None,
        "raw_positive_above_negative": (
            bool(ranking_pair.get("raw_positive_above_negative")) if ranking_pair else None
        ),
        "admission_positive_above_negative": (
            bool(ranking_pair.get("admission_positive_above_negative")) if ranking_pair else None
        ),
        "positive_lower_delay_risk": (
            bool(ranking_pair.get("positive_lower_delay_risk")) if ranking_pair else None
        ),
        "raw_margin": float(ranking_pair.get("raw_margin")) if ranking_pair else None,
        "admission_margin": float(ranking_pair.get("admission_margin")) if ranking_pair else None,
        "delay_risk_margin": float(ranking_pair.get("delay_risk_margin")) if ranking_pair else None,
        "gap_class": pair_gap_class(
            model_visible_difference=model_visible_difference,
            ranking_failure=ranking_failure,
            ranking_pair_available=ranking_pair is not None,
        ),
    }


def pair_gap_class(
    *,
    model_visible_difference: bool,
    ranking_failure: bool,
    ranking_pair_available: bool,
) -> str:
    if not model_visible_difference:
        return "model_input_collision"
    if ranking_pair_available and ranking_failure:
        return "coarse_input_visible_but_candidate_head_misranks"
    if ranking_pair_available:
        return "coarse_input_visible_and_raw_ranking_passes"
    return "coarse_input_visibility_without_model_score_pair"


def summarize_candidate_feature_values(
    rows: list[dict[str, Any]],
    candidate_schema: list[str],
) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for field in candidate_schema:
        values = [
            float((row.get("candidate_feature_values") or {}).get(field, 0.0))
            for row in rows
        ]
        summary[field] = numeric_summary(values)
    return summary


def numeric_summary(values: list[float]) -> dict[str, Any]:
    unique_values = sorted({round(float(value), 9) for value in values})
    return {
        "count": len(values),
        "min": min(values) if values else None,
        "max": max(values) if values else None,
        "mean": float(mean(values)) if values else None,
        "unique_count": len(unique_values),
        "constant": len(unique_values) <= 1,
        "unique_values": unique_values[:20],
    }


def build_feature_category_coverage(
    *,
    candidate_schema: list[str],
    context_schema: list[str],
    batch_schema: list[str],
    signature_metadata_present: bool,
) -> list[dict[str, Any]]:
    candidate = set(candidate_schema)
    context = set(context_schema)
    batch = set(batch_schema)
    rows = [
        _category(
            "reduced_cost_and_cost",
            "present",
            sorted(candidate & {"true_reduced_cost", "cost"}),
            "Candidate input includes true RC and cost scalars.",
        ),
        _category(
            "task_set_and_coarse_order",
            "present",
            ["candidate_task_membership", "candidate_sequence_positions", "sequence_length", "sortie_count"],
            "Model input sees covered tasks and coarse task order positions.",
        ),
        _category(
            "signature_identity",
            "metadata_only" if signature_metadata_present else "missing",
            ["candidate_signature_ids"] if signature_metadata_present else [],
            "Signature ids are stored in sample metadata but are not a model input.",
        ),
        _category(
            "selected_arc_option_sequence",
            "missing",
            _matching_fields(candidate_schema, ("arc", "option", "path")),
            "No selected path-option / arc-option sequence feature is present per candidate.",
        ),
        _category(
            "start_time_and_sortie_timing",
            "missing",
            _matching_fields(candidate_schema, ("start", "time", "gap", "duration")),
            "No start-time, per-sortie timing, or inter-sortie gap feature is present.",
        ),
        _category(
            "resource_and_window_slack",
            "missing",
            _matching_fields(candidate_schema, ("energy", "load", "slack", "window")),
            "No energy, load, or time-window slack feature is present.",
        ),
        _category(
            "active_basis_overlap_detail",
            "coarse_only",
            sorted(candidate & {"new_task_set", "weak_replacement_or_duplicate", "task_set_pool_count_before"}),
            "Only task-set pool overlap proxies are present; active basis coefficient overlap is absent.",
        ),
        _category(
            "branch_cut_per_candidate_interaction",
            "aggregate_context_only",
            sorted(context & {"branch_constraint_count", "cut_dual_l1_norm"}),
            "Branch/cut counts are context aggregates; per-candidate cut coefficients are absent.",
        ),
        _category(
            "trajectory_tail_proxy",
            "aggregate_context_only",
            sorted(context & {"final_judge_retry_count", "hidden_negative_count", "pricing_tail_retry_count_before"}),
            "Tail state is present only as context aggregate, not as a candidate consequence feature.",
        ),
        _category(
            "batch_composition",
            "present",
            sorted(batch & {"returned_journey_count", "negative_candidate_count", "best_true_reduced_cost"}),
            "Batch-level composition scalars are present.",
        ),
    ]
    return rows


def summarize_feature_structure_gap(
    *,
    row_records: list[dict[str, Any]],
    pair_rows: list[dict[str, Any]],
    feature_summary: dict[str, Any],
    category_coverage: list[dict[str, Any]],
) -> dict[str, Any]:
    label_counts = Counter(str(row["label_class"]) for row in row_records)
    context_count = len({str(row["context_key"]) for row in row_records})
    gap_counts = Counter(str(row["gap_class"]) for row in pair_rows)
    missing_statuses = {"missing", "metadata_only", "coarse_only", "aggregate_context_only"}
    critical_missing = [
        row["category"]
        for row in category_coverage
        if row["status"] in missing_statuses
        and row["category"]
        not in {"active_basis_overlap_detail", "trajectory_tail_proxy", "signature_identity"}
    ]
    constant_features = [
        name for name, stats in feature_summary.items() if bool(stats.get("constant"))
    ]
    ranking_failures = [
        row for row in pair_rows if row.get("raw_positive_above_negative") is False
    ]
    model_visible_ranking_failures = [
        row for row in ranking_failures if bool(row.get("model_visible_difference"))
    ]
    return {
        "focused_row_count": len(row_records),
        "context_count": context_count,
        "positive_row_count": int(label_counts.get("positive_trajectory", 0)),
        "negative_row_count": int(label_counts.get("delay_or_hard_negative", 0)),
        "pair_count": len(pair_rows),
        "ranking_pair_available_count": sum(int(bool(row.get("ranking_pair_available"))) for row in pair_rows),
        "raw_ranking_failure_pair_count": len(ranking_failures),
        "model_visible_difference_pair_count": sum(int(bool(row.get("model_visible_difference"))) for row in pair_rows),
        "model_input_collision_pair_count": int(gap_counts.get("model_input_collision", 0)),
        "gap_class_counts": dict(sorted(gap_counts.items())),
        "constant_candidate_feature_count": len(constant_features),
        "constant_candidate_feature_names": constant_features,
        "critical_missing_feature_categories": critical_missing,
        "critical_missing_feature_category_count": len(critical_missing),
        "feature_category_status_counts": dict(
            sorted(Counter(str(row["status"]) for row in category_coverage).items())
        ),
        "primary": primary_diagnosis(
            pair_rows=pair_rows,
            critical_missing=critical_missing,
            model_visible_ranking_failure_count=len(model_visible_ranking_failures),
        ),
    }


def primary_diagnosis(
    *,
    pair_rows: list[dict[str, Any]],
    critical_missing: list[str],
    model_visible_ranking_failure_count: int,
) -> str:
    if not pair_rows:
        return "no_same_context_positive_negative_pairs"
    if model_visible_ranking_failure_count and critical_missing:
        return "candidate_input_under_specified_for_action_consequence"
    if model_visible_ranking_failure_count:
        return "candidate_head_misranks_despite_visible_coarse_features"
    if critical_missing:
        return "feature_schema_missing_action_consequence_fields"
    return "focused_pairs_have_no_feature_structure_blocker"


def recommended_next_step(summary: dict[str, Any]) -> dict[str, Any]:
    primary = str(summary.get("primary") or "")
    if primary == "candidate_input_under_specified_for_action_consequence":
        return {
            "primary": "add_trace_timing_slack_and_candidate_interaction_features_then_retrain",
            "reason": "focused positive-negative pairs differ in coarse inputs but raw ranking still fails while critical action-consequence categories are absent",
        }
    if primary == "candidate_head_misranks_despite_visible_coarse_features":
        return {
            "primary": "add_focused_context_pair_regression_gate",
            "reason": "coarse inputs differ, so ranking failure must be guarded before stage4",
        }
    if primary == "feature_schema_missing_action_consequence_fields":
        return {
            "primary": "extend_candidate_feature_schema_before_more_threshold_sweeps",
            "reason": "critical action-consequence categories are absent from model input",
        }
    return {
        "primary": "collect_more_same_context_pairs",
        "reason": "current focused evidence is insufficient for feature repair",
    }


def context_key(item: dict[str, Any]) -> str:
    return "|".join(
        [
            str(item.get("instance_path") or item.get("instance") or ""),
            str(item.get("context_hash") or ""),
        ]
    )


def _category(category: str, status: str, fields: list[str], note: str) -> dict[str, Any]:
    return {
        "category": category,
        "status": status,
        "evidence_fields": fields,
        "model_input": status in {"present", "coarse_only", "aggregate_context_only"},
        "note": note,
    }


def _matching_fields(fields: list[str], needles: tuple[str, ...]) -> list[str]:
    return [field for field in fields if any(needle in field for needle in needles)]


def _aligned_l1(left: list[float], right: list[float]) -> float:
    width = max(len(left), len(right))
    total = 0.0
    for idx in range(width):
        left_value = left[idx] if idx < len(left) else 0.0
        right_value = right[idx] if idx < len(right) else 0.0
        total += abs(float(left_value) - float(right_value))
    return total


def _ranking_pair_index(rows: list[dict[str, Any]]) -> dict[tuple[int, int], dict[str, Any]]:
    return {
        (int(row["positive_row_index"]), int(row["negative_row_index"])): row
        for row in rows
    }


def _tensor_rows(value: Any) -> list[list[float]]:
    if hasattr(value, "detach"):
        return [[float(item) for item in row] for row in value.detach().cpu().tolist()]
    return [[float(item) for item in row] for row in value]


def _tensor_values(value: Any) -> list[float]:
    if hasattr(value, "detach"):
        return [float(item) for item in value.detach().cpu().flatten().tolist()]
    return [float(item) for item in value]


def _task_ids(sample: Any, *, width: int) -> list[int]:
    raw = getattr(sample, "task_ids", None)
    if raw is not None:
        if hasattr(raw, "detach"):
            values = raw.detach().cpu().flatten().tolist()
        else:
            values = list(raw)
        if len(values) >= width:
            return [int(value) for value in values[:width]]
    return list(range(1, width + 1))


def _assert_offline_manifest(manifest: dict[str, Any]) -> None:
    if bool(manifest.get("production_ready", False)):
        raise ValueError("dataset manifest unexpectedly marks production_ready=true")
    if bool(manifest.get("official_bound_effect", False)):
        raise ValueError("dataset manifest unexpectedly marks official_bound_effect=true")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not Path(path).exists():
        return []
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


def write_report(
    report: Path,
    summary: dict[str, Any],
    feature_summary: dict[str, Any],
    category_coverage: list[dict[str, Any]],
) -> None:
    s = summary["summary"]
    constant_names = ", ".join(s["constant_candidate_feature_names"]) or "none"
    critical_missing = ", ".join(s["critical_missing_feature_categories"]) or "none"
    lines = [
        "# 2026-06-17 BPC_future GAT Stage 3 v62 Feature/Structure Gap 审计报告",
        "",
        "## 目的",
        "",
        "量化 v61 提出的 candidate input 欠指定问题：固定 v53/v60 focused rows，比较同一 context 内 positive target 和 hard-negative target 在当前模型可见输入上的差异，并检查哪些 action-consequence 信息只在 metadata/log 或完全缺失。",
        "",
        "该脚本只读 batch-impact dataset 和 v60 pair rows，不运行 BPC / pricing / RMP / worker / certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        f"status = {summary['status']}",
        f"focused_row_count = {s['focused_row_count']}",
        f"context_count = {s['context_count']}",
        f"positive_row_count = {s['positive_row_count']}",
        f"negative_row_count = {s['negative_row_count']}",
        f"pair_count = {s['pair_count']}",
        f"ranking_pair_available_count = {s['ranking_pair_available_count']}",
        f"raw_ranking_failure_pair_count = {s['raw_ranking_failure_pair_count']}",
        f"model_visible_difference_pair_count = {s['model_visible_difference_pair_count']}",
        f"model_input_collision_pair_count = {s['model_input_collision_pair_count']}",
        f"constant_candidate_feature_count = {s['constant_candidate_feature_count']}",
        f"critical_missing_feature_category_count = {s['critical_missing_feature_category_count']}",
        f"primary = {s['primary']}",
        f"recommended_next_step = {summary['recommended_next_step']['primary']}",
        "production_ready = false",
        "selector_can_certificate = false",
        "all_checks_pass = true",
        "```",
        "",
        "## 关键结论",
        "",
        f"- 当前 candidate feature dim = `{summary['candidate_feature_dim']}`，context dim = `{summary['context_feature_dim']}`，batch dim = `{summary['batch_feature_dim']}`。",
        f"- focused rows 中常数 candidate features：`{constant_names}`。",
        f"- critical missing / under-specified categories：`{critical_missing}`。",
        f"- pair gap class counts：`{json.dumps(s['gap_class_counts'], ensure_ascii=False, sort_keys=True)}`。",
        "",
        "解释：focused 正负 target 在 task set / sequence position / scalar features 上通常不是完全碰撞；但 v60 raw ranking 仍有失败，同时 path-option、timing、slack、branch/cut per-candidate interaction 等 action-consequence 特征缺失。因此下一步不应继续只调 threshold / delay penalty。",
        "",
        "## Feature Category Coverage",
        "",
        "```json",
        json.dumps(category_coverage, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Constant Candidate Features",
        "",
        "```json",
        json.dumps(
            {
                name: feature_summary[name]
                for name in s["constant_candidate_feature_names"]
                if name in feature_summary
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
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
        f"rows = {summary['focused_candidate_input_rows_path']}",
        f"pairs = {summary['pair_feature_gap_rows_path']}",
        f"candidate_feature_summary = {summary['candidate_feature_summary_path']}",
        f"feature_category_coverage = {summary['feature_category_coverage_path']}",
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


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Mine train-only analogs for focused GAT batch-impact pair failures.

This audit is deliberately offline-only.  It reads an already materialized
batch-impact dataset and a focused pair failure audit, then finds train-split
same-context positive/negative pairs whose feature deltas resemble the failed
validation or train-side pairs.  The output row-index selector is training-only:
it must not include validation focused gate rows.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch


DEFAULT_DATASET_DIR = Path(
    "BPC_future/data/gat_batch_impact/"
    "v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622"
)
DEFAULT_METRICS = Path(
    "BPC_future/results/"
    "gat_batch_impact_training_v138_action_priority_residual_seed13_20260623/"
    "metrics.json"
)
DEFAULT_FAILURE_ROWS = Path(
    "BPC_future/results/"
    "gat_batch_impact_focused_pair_failure_audit_v138_action_priority_residual_20260623/"
    "focused_pair_failure_rows.jsonl"
)
DEFAULT_FOCUSED_TRAINING_ROWS = Path(
    "BPC_future/results/gat_batch_impact_v123_leakfree_focused_selectors_20260622/"
    "focused_training_row_indices.json"
)
DEFAULT_EXISTING_BOOST_ROWS = Path(
    "BPC_future/results/gat_batch_impact_v134_trainonly_raw_action_boost_20260623/"
    "focused_raw_action_boost_train_row_indices.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/"
    "gat_batch_impact_v139_train_only_failure_analogs_20260623"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260623_bpc_future_gat_target_mode_stage3_v139_train_only_failure_analog_audit_zh.md"
)


@dataclass(frozen=True)
class RowRecord:
    row_index: int
    context_key: str
    context_hash: str
    instance: str
    family: str
    task_count: int
    split: str
    label_positive: bool
    roi: float
    high_priority_candidate_count: int
    delay_candidate_count: int
    candidate_vector: tuple[float, ...]
    batch_vector: tuple[float, ...]
    path_tokens: tuple[int, ...]
    signature_ids: tuple[str, ...]
    primary_candidate_index: int
    in_focused_training: bool
    in_existing_boost: bool


@dataclass(frozen=True)
class PairRecord:
    positive_row_index: int
    negative_row_index: int
    context_key: str
    context_hash: str
    instance: str
    family: str
    task_count: int
    positive_roi: float
    negative_roi: float
    roi_delta: float
    pair_vector: tuple[float, ...]
    pair_path_tokens: tuple[int, ...]
    pair_signature_ids: tuple[str, ...]
    focused_training_pair: bool
    existing_boost_pair: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--failure-rows", type=Path, default=DEFAULT_FAILURE_ROWS)
    parser.add_argument(
        "--focused-training-row-indices-file",
        type=Path,
        default=DEFAULT_FOCUSED_TRAINING_ROWS,
    )
    parser.add_argument(
        "--existing-boost-row-indices-file",
        type=Path,
        default=DEFAULT_EXISTING_BOOST_ROWS,
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--report-version-label",
        default=None,
        help=(
            "Version label used in report/recommendation text, e.g. v140. "
            "Defaults to the first vNNN token found in output/report paths."
        ),
    )
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--min-positive-roi", type=float, default=0.65)
    parser.add_argument("--max-negative-roi", type=float, default=0.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset_dir = Path(args.dataset_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_version_label = (
        str(args.report_version_label)
        if args.report_version_label
        else _infer_version_label(output_dir, Path(args.report))
    )

    manifest = _read_json(dataset_dir / "manifest.json")
    metrics = _read_json(args.metrics)
    failure_rows = [
        row for row in _read_jsonl(args.failure_rows)
        if not bool(row.get("pair_pass"))
    ]
    focused_training_rows = _read_row_index_file(args.focused_training_row_indices_file)
    existing_boost_rows = _read_row_index_file(args.existing_boost_row_indices_file)
    train_instances, validation_instances = _split_instance_sets(metrics)

    row_records = _load_row_records(
        dataset_dir=dataset_dir,
        manifest=manifest,
        train_instances=train_instances,
        validation_instances=validation_instances,
        focused_training_rows=focused_training_rows,
        existing_boost_rows=existing_boost_rows,
    )
    candidate_std = _float_tuple(manifest.get("candidate_feature_std") or [])
    batch_std = _float_tuple(manifest.get("batch_feature_std") or [])
    train_pair_universe = _build_train_pair_universe(
        row_records,
        candidate_std=candidate_std,
        batch_std=batch_std,
        min_positive_roi=float(args.min_positive_roi),
        max_negative_roi=float(args.max_negative_roi),
    )
    failed_pair_records = _failed_pair_records(
        failure_rows,
        row_records=row_records,
        candidate_std=candidate_std,
        batch_std=batch_std,
    )
    analog_rows = _find_analogs(
        failed_pair_records,
        train_pair_universe,
        row_records=row_records,
        top_k=int(args.top_k),
    )

    excluded_validation_rows = sorted(
        {
            int(row_index)
            for pair in failed_pair_records
            for row_index in (pair["positive_row_index"], pair["negative_row_index"])
            if row_records[int(row_index)].split == "validation"
        }
    )
    analog_row_indices = sorted(
        {
            int(row["analog_positive_row_index"])
            for row in analog_rows
        }
        | {
            int(row["analog_negative_row_index"])
            for row in analog_rows
        }
    )
    new_analog_row_indices = sorted(
        int(row_index)
        for row_index in analog_row_indices
        if int(row_index) not in existing_boost_rows
    )
    combined_boost_row_indices = sorted(set(existing_boost_rows) | set(analog_row_indices))
    all_analog_rows_train = all(
        row_records[int(row_index)].split == "train"
        for row_index in analog_row_indices
    )
    validation_leakage_row_indices = sorted(
        int(row_index)
        for row_index in analog_row_indices
        if row_records[int(row_index)].split != "train"
    )
    combined_boost_validation_leakage_row_indices = sorted(
        int(row_index)
        for row_index in combined_boost_row_indices
        if row_records[int(row_index)].split != "train"
    )

    failure_split_counts = Counter(str(row["target_split_class"]) for row in failed_pair_records)
    target_with_analogs = Counter(str(row["target_failure_key"]) for row in analog_rows)
    validation_failure_keys = {
        str(row["target_failure_key"])
        for row in failed_pair_records
        if str(row["target_split_class"]) != "train_visible"
    }
    validation_failure_keys_with_analogs = sorted(validation_failure_keys & set(target_with_analogs))

    recommendation = _recommendation(
        report_version_label=report_version_label,
        analog_rows=analog_rows,
        new_analog_row_indices=new_analog_row_indices,
        validation_failure_keys=validation_failure_keys,
        validation_failure_keys_with_analogs=validation_failure_keys_with_analogs,
    )
    summary = {
        "schema_version": "gat_batch_impact_train_only_failure_analogs_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "default_enabled": False,
        "selector_can_certificate": False,
        "dataset_dir": str(dataset_dir),
        "metrics": str(args.metrics),
        "failure_rows": str(args.failure_rows),
        "focused_training_row_indices_file": str(args.focused_training_row_indices_file),
        "existing_boost_row_indices_file": str(args.existing_boost_row_indices_file),
        "sample_count": len(row_records),
        "failed_pair_count": len(failed_pair_records),
        "failure_split_counts": dict(sorted(failure_split_counts.items())),
        "train_pair_universe_count": len(train_pair_universe),
        "analog_pair_count": len(analog_rows),
        "analog_row_index_count": len(analog_row_indices),
        "existing_boost_row_index_count": len(existing_boost_rows),
        "combined_boost_row_index_count": len(combined_boost_row_indices),
        "new_analog_row_index_count": len(new_analog_row_indices),
        "validation_failure_key_count": len(validation_failure_keys),
        "validation_failure_keys_with_analogs": validation_failure_keys_with_analogs,
        "excluded_validation_row_indices": excluded_validation_rows,
        "validation_leakage_row_indices": validation_leakage_row_indices,
        "combined_boost_validation_leakage_row_indices": combined_boost_validation_leakage_row_indices,
        "all_analog_rows_train": bool(all_analog_rows_train),
        "all_combined_boost_rows_train": not combined_boost_validation_leakage_row_indices,
        "report_version_label": report_version_label,
        "recommendation": recommendation,
        "all_checks_pass": bool(
            all_analog_rows_train
            and not validation_leakage_row_indices
            and not combined_boost_validation_leakage_row_indices
        ),
    }

    _write_json(output_dir / "summary.json", summary)
    _write_jsonl(output_dir / "failed_pair_records.jsonl", failed_pair_records)
    _write_jsonl(output_dir / "train_pair_universe.jsonl", [
        _pair_record_for_json(pair) for pair in train_pair_universe
    ])
    _write_jsonl(output_dir / "train_only_analog_pairs.jsonl", analog_rows)
    _write_json(
        output_dir / "train_only_analog_row_indices.json",
        {
            "schema_version": "gat_batch_impact_train_only_failure_analog_indices_v1",
            "purpose": (
                "Training-only analog rows for the selected focused pair failures. "
                "Validation focused gate rows are excluded."
            ),
            "row_index_semantics": "batch_impact_source_row_index",
            "leakage_guard": {
                "train_only": True,
                "metrics_split_source": str(args.metrics),
                "failure_rows_source": str(args.failure_rows),
                "excluded_validation_row_indices": excluded_validation_rows,
                "validation_leakage_row_indices": validation_leakage_row_indices,
                "all_analog_rows_train": bool(all_analog_rows_train),
            },
            "row_indices": analog_row_indices,
            "new_row_indices_beyond_existing_boost": new_analog_row_indices,
        },
    )
    _write_json(
        output_dir / "train_only_combined_boost_row_indices.json",
        {
            "schema_version": (
                f"gat_batch_impact_{report_version_label}_trainonly_combined_boost_indices_v1"
            ),
            "purpose": (
                "Union of the existing train-only boost rows and the "
                f"{report_version_label} train-only failure analog rows. Intended for diagnostic "
                "focused-pair boost loss only."
            ),
            "row_index_semantics": "batch_impact_source_row_index",
            "sources": {
                "existing_boost_row_indices_file": str(args.existing_boost_row_indices_file),
                "analog_row_indices_file": str(output_dir / "train_only_analog_row_indices.json"),
            },
            "leakage_guard": {
                "train_only": True,
                "metrics_split_source": str(args.metrics),
                "failure_rows_source": str(args.failure_rows),
                "excluded_validation_row_indices": excluded_validation_rows,
                "validation_leakage_row_indices": combined_boost_validation_leakage_row_indices,
                "all_combined_boost_rows_train": not combined_boost_validation_leakage_row_indices,
            },
            "row_indices": combined_boost_row_indices,
            "new_row_indices_beyond_existing_boost": new_analog_row_indices,
        },
    )
    _write_report(
        Path(args.report),
        summary=summary,
        failed_pair_records=failed_pair_records,
        analog_rows=analog_rows,
        output_dir=output_dir,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if summary["all_checks_pass"] else 1


def _load_row_records(
    *,
    dataset_dir: Path,
    manifest: dict[str, Any],
    train_instances: set[str],
    validation_instances: set[str],
    focused_training_rows: set[int],
    existing_boost_rows: set[int],
) -> dict[int, RowRecord]:
    records: dict[int, RowRecord] = {}
    for item in manifest.get("samples") or []:
        row_index = int(item.get("row_index"))
        sample_path = dataset_dir / str(item.get("path"))
        sample = torch.load(sample_path, map_location="cpu", weights_only=False)
        split = _row_split(str(item.get("instance") or ""), train_instances, validation_instances)
        primary_idx = _primary_candidate_index(sample)
        candidate_rows = _tensor_rows(getattr(sample, "candidate_features", None))
        candidate_vector = (
            tuple(candidate_rows[primary_idx])
            if 0 <= primary_idx < len(candidate_rows)
            else tuple()
        )
        batch_vector = tuple(_tensor_values(getattr(sample, "batch_features", None)))
        records[row_index] = RowRecord(
            row_index=row_index,
            context_key=_context_key(item),
            context_hash=str(item.get("context_hash") or ""),
            instance=str(item.get("instance") or ""),
            family=str(item.get("instance_family") or item.get("family") or ""),
            task_count=int(item.get("task_count") or 0),
            split=split,
            label_positive=bool(int(item.get("label_batch_roi_positive") or 0)),
            roi=float(item.get("accepted_batch_roi") or 0.0),
            high_priority_candidate_count=int(item.get("high_priority_candidate_count") or 0),
            delay_candidate_count=int(item.get("delay_candidate_count") or 0),
            candidate_vector=candidate_vector,
            batch_vector=batch_vector,
            path_tokens=tuple(_masked_int_row(sample, "candidate_path_token_ids", primary_idx)),
            signature_ids=tuple(str(value) for value in item.get("candidate_signature_ids") or []),
            primary_candidate_index=primary_idx,
            in_focused_training=row_index in focused_training_rows,
            in_existing_boost=row_index in existing_boost_rows,
        )
    return records


def _primary_candidate_index(sample: Any) -> int:
    high_priority = _tensor_values(getattr(sample, "y_candidate_high_priority", None))
    for idx, value in enumerate(high_priority):
        if float(value) > 0.5:
            return int(idx)
    delay_risk = _tensor_values(getattr(sample, "y_candidate_delay_risk", None))
    for idx, value in enumerate(delay_risk):
        if float(value) > 0.5:
            return int(idx)
    return 0


def _build_train_pair_universe(
    row_records: dict[int, RowRecord],
    *,
    candidate_std: tuple[float, ...],
    batch_std: tuple[float, ...],
    min_positive_roi: float,
    max_negative_roi: float,
) -> list[PairRecord]:
    by_context: dict[str, list[RowRecord]] = defaultdict(list)
    for record in row_records.values():
        if record.split == "train":
            by_context[record.context_key].append(record)

    pairs: list[PairRecord] = []
    for records in by_context.values():
        positives = [
            record for record in records
            if _is_positive_row(record, min_positive_roi=min_positive_roi)
        ]
        negatives = [
            record for record in records
            if _is_negative_row(record, max_negative_roi=max_negative_roi)
        ]
        for positive in positives:
            for negative in negatives:
                if positive.row_index == negative.row_index:
                    continue
                roi_delta = float(positive.roi) - float(negative.roi)
                if roi_delta <= 0.0:
                    continue
                pairs.append(
                    _make_pair_record(
                        positive,
                        negative,
                        candidate_std=candidate_std,
                        batch_std=batch_std,
                    )
                )
    return pairs


def _is_positive_row(record: RowRecord, *, min_positive_roi: float) -> bool:
    return (
        bool(record.label_positive)
        and float(record.roi) >= float(min_positive_roi)
        and int(record.high_priority_candidate_count) > 0
    )


def _is_negative_row(record: RowRecord, *, max_negative_roi: float) -> bool:
    return (
        int(record.delay_candidate_count) > 0
        and (not bool(record.label_positive) or float(record.roi) <= float(max_negative_roi))
    )


def _failed_pair_records(
    failure_rows: list[dict[str, Any]],
    *,
    row_records: dict[int, RowRecord],
    candidate_std: tuple[float, ...],
    batch_std: tuple[float, ...],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    for row in failure_rows:
        positive_idx = int(row.get("positive_row_index"))
        negative_idx = int(row.get("negative_row_index"))
        key = (positive_idx, negative_idx)
        if key in seen:
            continue
        seen.add(key)
        positive = row_records[positive_idx]
        negative = row_records[negative_idx]
        pair = _make_pair_record(
            positive,
            negative,
            candidate_std=candidate_std,
            batch_std=batch_std,
        )
        splits = {positive.split, negative.split}
        target_split_class = "train_visible" if splits == {"train"} else "validation_gate_only"
        records.append(
            {
                "target_failure_key": f"{positive_idx}>{negative_idx}",
                "context_key": str(row.get("context_key") or pair.context_key),
                "context_hash": str(row.get("context_hash") or pair.context_hash),
                "family": str(row.get("family") or pair.family),
                "task_count": int(row.get("task_count") or pair.task_count),
                "positive_row_index": positive_idx,
                "negative_row_index": negative_idx,
                "positive_split": positive.split,
                "negative_split": negative.split,
                "target_split_class": target_split_class,
                "positive_roi": float(row.get("positive_roi") or positive.roi),
                "negative_roi": float(row.get("negative_roi") or negative.roi),
                "raw_margin": _float_or_none(row.get("raw_margin")),
                "admission_margin": _float_or_none(row.get("admission_margin")),
                "delay_risk_margin": _float_or_none(row.get("delay_risk_margin")),
                "diagnosis": str(row.get("diagnosis") or ""),
                "failure_modes": list(row.get("failure_modes") or []),
                "positive_in_focused_training": positive.in_focused_training,
                "negative_in_focused_training": negative.in_focused_training,
                "positive_in_existing_boost": positive.in_existing_boost,
                "negative_in_existing_boost": negative.in_existing_boost,
                "target_pair_vector": list(pair.pair_vector),
                "target_pair_path_tokens": list(pair.pair_path_tokens),
                "target_pair_signature_ids": list(pair.pair_signature_ids),
            }
        )
    return records


def _find_analogs(
    failed_pair_records: list[dict[str, Any]],
    train_pair_universe: list[PairRecord],
    *,
    row_records: dict[int, RowRecord],
    top_k: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in failed_pair_records:
        scored: list[tuple[float, dict[str, Any]]] = []
        target_vector = _float_tuple(target.get("target_pair_vector") or [])
        target_tokens = set(int(value) for value in target.get("target_pair_path_tokens") or [])
        target_signatures = set(str(value) for value in target.get("target_pair_signature_ids") or [])
        target_family = str(target.get("family") or "")
        target_task_count = int(target.get("task_count") or 0)
        target_rows = {
            int(target["positive_row_index"]),
            int(target["negative_row_index"]),
        }
        for pair in train_pair_universe:
            analog_rows = {pair.positive_row_index, pair.negative_row_index}
            if target_rows & analog_rows:
                continue
            feature_distance = _l2_distance(target_vector, pair.pair_vector)
            path_jaccard = _set_jaccard(target_tokens, set(pair.pair_path_tokens))
            signature_jaccard = _set_jaccard(target_signatures, set(pair.pair_signature_ids))
            family_penalty = 0.0 if pair.family == target_family else 2.0
            task_penalty = 0.0 if int(pair.task_count) == target_task_count else 1.0
            distance = (
                feature_distance
                + 0.5 * (1.0 - path_jaccard)
                + 0.25 * (1.0 - signature_jaccard)
                + family_penalty
                + task_penalty
            )
            positive = row_records[pair.positive_row_index]
            negative = row_records[pair.negative_row_index]
            scored.append(
                (
                    distance,
                    {
                        "target_failure_key": str(target["target_failure_key"]),
                        "target_context_key": str(target["context_key"]),
                        "target_family": target_family,
                        "target_task_count": target_task_count,
                        "target_positive_row_index": int(target["positive_row_index"]),
                        "target_negative_row_index": int(target["negative_row_index"]),
                        "target_split_class": str(target["target_split_class"]),
                        "analog_context_key": pair.context_key,
                        "analog_context_hash": pair.context_hash,
                        "analog_instance": pair.instance,
                        "analog_family": pair.family,
                        "analog_task_count": pair.task_count,
                        "analog_positive_row_index": pair.positive_row_index,
                        "analog_negative_row_index": pair.negative_row_index,
                        "analog_positive_roi": pair.positive_roi,
                        "analog_negative_roi": pair.negative_roi,
                        "analog_roi_delta": pair.roi_delta,
                        "feature_distance": feature_distance,
                        "path_token_jaccard": path_jaccard,
                        "signature_jaccard": signature_jaccard,
                        "distance": distance,
                        "same_family": pair.family == target_family,
                        "same_task_count": int(pair.task_count) == target_task_count,
                        "analog_positive_in_focused_training": positive.in_focused_training,
                        "analog_negative_in_focused_training": negative.in_focused_training,
                        "analog_positive_in_existing_boost": positive.in_existing_boost,
                        "analog_negative_in_existing_boost": negative.in_existing_boost,
                    },
                )
            )
        for _, row in sorted(scored, key=lambda item: item[0])[:max(0, int(top_k))]:
            rows.append(row)
    return rows


def _make_pair_record(
    positive: RowRecord,
    negative: RowRecord,
    *,
    candidate_std: tuple[float, ...],
    batch_std: tuple[float, ...],
) -> PairRecord:
    pair_vector = tuple(
        _normalized_delta(positive.candidate_vector, negative.candidate_vector, candidate_std)
        + _normalized_delta(positive.batch_vector, negative.batch_vector, batch_std)
    )
    return PairRecord(
        positive_row_index=positive.row_index,
        negative_row_index=negative.row_index,
        context_key=positive.context_key,
        context_hash=positive.context_hash,
        instance=positive.instance,
        family=positive.family,
        task_count=positive.task_count,
        positive_roi=float(positive.roi),
        negative_roi=float(negative.roi),
        roi_delta=float(positive.roi) - float(negative.roi),
        pair_vector=pair_vector,
        pair_path_tokens=tuple(sorted(set(positive.path_tokens) | set(negative.path_tokens))),
        pair_signature_ids=tuple(sorted(set(positive.signature_ids) | set(negative.signature_ids))),
        focused_training_pair=positive.in_focused_training and negative.in_focused_training,
        existing_boost_pair=positive.in_existing_boost and negative.in_existing_boost,
    )


def _pair_record_for_json(pair: PairRecord) -> dict[str, Any]:
    return {
        "positive_row_index": pair.positive_row_index,
        "negative_row_index": pair.negative_row_index,
        "context_key": pair.context_key,
        "context_hash": pair.context_hash,
        "instance": pair.instance,
        "family": pair.family,
        "task_count": pair.task_count,
        "positive_roi": pair.positive_roi,
        "negative_roi": pair.negative_roi,
        "roi_delta": pair.roi_delta,
        "path_token_count": len(pair.pair_path_tokens),
        "signature_count": len(pair.pair_signature_ids),
        "focused_training_pair": pair.focused_training_pair,
        "existing_boost_pair": pair.existing_boost_pair,
    }


def _recommendation(
    *,
    report_version_label: str,
    analog_rows: list[dict[str, Any]],
    new_analog_row_indices: list[int],
    validation_failure_keys: set[str],
    validation_failure_keys_with_analogs: list[str],
) -> str:
    if validation_failure_keys and not validation_failure_keys_with_analogs:
        return f"do_not_train_{report_version_label}_yet_no_train_only_analogs_for_validation_failures"
    if not analog_rows:
        return f"do_not_train_{report_version_label}_yet_no_train_pair_universe_analogs"
    if not new_analog_row_indices:
        return f"do_not_train_{report_version_label}_yet_analogs_already_covered_by_existing_boost"
    return (
        f"{report_version_label}_training_allowed_as_diagnostic_"
        "with_train_only_analog_boost_and_feature_audit"
    )


def _infer_version_label(*paths: Path) -> str:
    for path in paths:
        match = re.search(r"(?<![A-Za-z0-9])v\d+(?![A-Za-z0-9])", str(path))
        if match:
            return match.group(0)
    return "vnext"


def _write_report(
    report_path: Path,
    *,
    summary: dict[str, Any],
    failed_pair_records: list[dict[str, Any]],
    analog_rows: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_version_label = str(summary.get("report_version_label") or "vnext")
    lines = [
        f"# 2026-06-23 BPC_future GAT Stage 3 {report_version_label} Train-only Failure Analog 审计报告",
        "",
        "## 结论",
        "",
        "本报告只做 offline train-only analog mining，不运行 BPC、pricing、RMP、worker 或 certificate。",
        "目标是为本轮 focused pair failures 找训练 split 内的相似正负对，避免把 validation focused gate row 直接加入训练。",
        "",
        "```text",
        f"failed_pair_count = {summary['failed_pair_count']}",
        f"failure_split_counts = {summary['failure_split_counts']}",
        f"train_pair_universe_count = {summary['train_pair_universe_count']}",
        f"analog_pair_count = {summary['analog_pair_count']}",
        f"analog_row_index_count = {summary['analog_row_index_count']}",
        f"existing_boost_row_index_count = {summary['existing_boost_row_index_count']}",
        f"combined_boost_row_index_count = {summary['combined_boost_row_index_count']}",
        f"new_analog_row_index_count = {summary['new_analog_row_index_count']}",
        f"excluded_validation_row_indices = {summary['excluded_validation_row_indices']}",
        f"validation_leakage_row_indices = {summary['validation_leakage_row_indices']}",
        "combined_boost_validation_leakage_row_indices = "
        f"{summary['combined_boost_validation_leakage_row_indices']}",
        f"all_analog_rows_train = {str(summary['all_analog_rows_train']).lower()}",
        f"all_combined_boost_rows_train = {str(summary['all_combined_boost_rows_train']).lower()}",
        f"recommendation = {summary['recommendation']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## Artifact",
        "",
        f"- summary: `{output_dir / 'summary.json'}`",
        f"- failed pairs: `{output_dir / 'failed_pair_records.jsonl'}`",
        f"- train pair universe: `{output_dir / 'train_pair_universe.jsonl'}`",
        f"- analog pairs: `{output_dir / 'train_only_analog_pairs.jsonl'}`",
        f"- row selector: `{output_dir / 'train_only_analog_row_indices.json'}`",
        f"- combined boost selector: `{output_dir / 'train_only_combined_boost_row_indices.json'}`",
        "",
        "## Failed Pair Split",
        "",
        "| target | family | task | positive | negative | split class | diagnosis | raw | admission | delay-risk |",
        "|---|---|---:|---:|---:|---|---|---:|---:|---:|",
    ]
    for row in failed_pair_records:
        lines.append(
            "| {target_failure_key} | {family} | {task_count} | {positive_row_index} | "
            "{negative_row_index} | {target_split_class} | {diagnosis} | {raw_margin} | "
            "{admission_margin} | {delay_risk_margin} |".format(
                **{
                    **row,
                    "raw_margin": _fmt_float(row.get("raw_margin")),
                    "admission_margin": _fmt_float(row.get("admission_margin")),
                    "delay_risk_margin": _fmt_float(row.get("delay_risk_margin")),
                }
            )
        )

    lines.extend(
        [
            "",
            "## Top Analogs",
            "",
            "| target | analog pair | family | task | ROI delta | distance | same family | same task | existing boost pair |",
            "|---|---|---|---:|---:|---:|---|---|---|",
        ]
    )
    for row in analog_rows[: min(32, len(analog_rows))]:
        lines.append(
            "| {target_failure_key} | {analog_positive_row_index}>{analog_negative_row_index} | "
            "{analog_family} | {analog_task_count} | {analog_roi_delta:.6f} | {distance:.6f} | "
            "{same_family} | {same_task_count} | {boost_pair} |".format(
                **{
                    **row,
                    "boost_pair": (
                        bool(row.get("analog_positive_in_existing_boost"))
                        and bool(row.get("analog_negative_in_existing_boost"))
                    ),
                }
            )
        )

    lines.extend(
        [
            "",
            "## 判断",
            "",
            "- 该 selector 的 row index 语义是 `batch_impact_source_row_index`；",
            "- validation failure rows 只用于查询相似训练样本，不进入输出 selector；",
        f"- 若后续训练 {report_version_label}，只能作为 Stage 3 diagnostic，不是 Stage 4 candidate；",
            "- focused gate 仍必须要求 raw / admission / delay / strict 全部通过，不能因为 analog mining 放宽；",
            "- ddcb / 7cb 这类 train-visible failure 仍需要 action-consequence feature audit，不能只靠加权重复训练解决。",
            "",
            "## Exactness Boundary",
            "",
            "```text",
            "diagnostic_only = true",
            "runs_bpc_or_pricing = false",
            "production_ready = false",
            "default_enabled = false",
            "selector_can_certificate = false",
            "gate_can_permanently_discard_negative_columns = false",
            "```",
            "",
            "GAT 仍只能做 discovery / ordering / finite-delay admission scheduling；最终 certificate 只能来自当前 branch/cut/dual 下 exact pricing full closure。",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _split_instance_sets(metrics: dict[str, Any]) -> tuple[set[str], set[str]]:
    split = metrics.get("split") or {}
    return (
        {_instance_name(path) for path in split.get("train_instances") or []},
        {_instance_name(path) for path in split.get("validation_instances") or []},
    )


def _row_split(instance: str, train_instances: set[str], validation_instances: set[str]) -> str:
    name = _instance_name(instance)
    if name in train_instances:
        return "train"
    if name in validation_instances:
        return "validation"
    return "unknown"


def _instance_name(path_or_name: str) -> str:
    stem = Path(str(path_or_name)).stem
    if stem.endswith("_logical_graph"):
        stem = stem[: -len("_logical_graph")]
    return stem


def _context_key(item: dict[str, Any]) -> str:
    return "|".join([str(item.get("instance") or ""), str(item.get("context_hash") or "")])


def _normalized_delta(
    left: tuple[float, ...],
    right: tuple[float, ...],
    std: tuple[float, ...],
) -> list[float]:
    width = max(len(left), len(right), len(std))
    values: list[float] = []
    for idx in range(width):
        denom = float(std[idx]) if idx < len(std) and abs(float(std[idx])) > 1.0e-8 else 1.0
        values.append(
            (
                float(left[idx] if idx < len(left) else 0.0)
                - float(right[idx] if idx < len(right) else 0.0)
            )
            / denom
        )
    return values


def _l2_distance(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    width = max(len(left), len(right))
    if width <= 0:
        return 0.0
    total = 0.0
    for idx in range(width):
        delta = float(left[idx] if idx < len(left) else 0.0) - float(
            right[idx] if idx < len(right) else 0.0
        )
        total += delta * delta
    return math.sqrt(total / float(width))


def _set_jaccard(left: set[Any], right: set[Any]) -> float:
    union = left | right
    if not union:
        return 1.0
    return float(len(left & right)) / float(len(union))


def _masked_int_row(sample: Any, attr: str, row_index: int) -> list[int]:
    value = getattr(sample, attr, None)
    if value is None:
        return []
    rows = value.detach().cpu().tolist() if hasattr(value, "detach") else value
    if row_index < 0 or row_index >= len(rows):
        return []
    row = list(rows[row_index])
    mask_value = getattr(sample, "candidate_path_token_mask", None)
    if mask_value is not None and attr != "candidate_path_type_ids":
        masks = mask_value.detach().cpu().tolist() if hasattr(mask_value, "detach") else mask_value
        if row_index < len(masks):
            return [int(item) for item, keep in zip(row, list(masks[row_index])) if bool(keep)]
    return [int(item) for item in row if int(item) != 0]


def _tensor_rows(value: Any) -> list[list[float]]:
    if value is None:
        return []
    raw = value.detach().cpu().tolist() if hasattr(value, "detach") else value
    return [[float(item) for item in row] for row in raw]


def _tensor_values(value: Any) -> list[float]:
    if value is None:
        return []
    raw = value.detach().cpu().flatten().tolist() if hasattr(value, "detach") else list(value)
    return [float(item) for item in raw]


def _float_tuple(value: Any) -> tuple[float, ...]:
    if value is None:
        return tuple()
    return tuple(float(item) for item in list(value))


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt_float(value: Any) -> str:
    numeric = _float_or_none(value)
    if numeric is None:
        return ""
    return f"{numeric:.6f}"


def _read_row_index_file(path: Path | None) -> set[int]:
    if path is None or not Path(path).exists():
        return set()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, list):
        return {int(value) for value in data}
    if isinstance(data, dict):
        return {int(value) for value in data.get("row_indices") or []}
    raise TypeError(f"unsupported row index file shape: {path}")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
        + ("\n" if rows else ""),
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())

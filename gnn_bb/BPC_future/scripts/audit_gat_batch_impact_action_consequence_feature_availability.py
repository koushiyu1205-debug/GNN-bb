#!/usr/bin/env python3
"""Audit action-consequence feature availability for GAT batch-impact rows.

This offline diagnostic checks whether the next candidate representation
features proposed after the focused-pair gate failure are recoverable from the
existing batch-impact rows and replay capture payloads. It does not rebuild a
dataset, train a model, run BPC/pricing/RMP, or affect certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
import math
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from BPC_future.learning.graph_builder import FutureGraphBuilder
from BPC_future.scripts.build_gat_batch_impact_dataset import (
    _finite_float,
    _input_jsonl_paths,
    _journey_arc_option_ids,
    _journey_sequence,
    _journey_signature_sample_text,
    _journey_trace_key,
    _load_capture_events,
    _read_jsonl,
    _row_target_signature_samples,
    _row_target_trace_key,
    _task_set,
)


DEFAULT_DATASET_DIR = Path("BPC_future/data/gat_batch_impact/v66_v54_trace_features_20260617")
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/"
    "gat_batch_impact_action_consequence_feature_availability_v73_v66_20260617"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260617_bpc_future_gat_target_mode_stage3_v73_action_consequence_feature_"
    "availability_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--focus-row-index-min",
        type=int,
        default=None,
        help="Restrict audit to manifest samples with row_index >= this value.",
    )
    parser.add_argument("--max-samples", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_action_consequence_feature_availability(
        dataset_dir=Path(args.dataset_dir),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        focus_row_index_min=args.focus_row_index_min,
        max_samples=max(0, int(args.max_samples)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_action_consequence_feature_availability(
    *,
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    focus_row_index_min: int | None = None,
    max_samples: int = 0,
) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    manifest = _read_json(dataset_dir / "manifest.json")
    samples = [
        item
        for item in manifest.get("samples", [])
        if focus_row_index_min is None
        or _int_or_default(item.get("row_index"), -1) >= int(focus_row_index_min)
    ]
    if max_samples:
        samples = samples[: int(max_samples)]

    source_rows = _load_manifest_source_rows(manifest)
    builder = FutureGraphBuilder()
    graph_window_cache: dict[str, dict[int, tuple[float, float]]] = {}
    capture_cache: dict[str, dict[tuple[str, int, str, int, int], dict[str, Any]]] = {}

    candidate_rows: list[dict[str, Any]] = []
    sample_rows: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    task_count_counts: Counter[str] = Counter()

    for sample in samples:
        row_index = _int_or_default(sample.get("row_index"), -1)
        row = source_rows[row_index] if 0 <= row_index < len(source_rows) else None
        if row is None:
            skipped["missing_source_row"] += 1
            continue
        source_file = Path(str(row.get("source_file") or ""))
        if not source_file.exists():
            skipped["missing_capture_file"] += 1
            continue
        events = capture_cache.get(str(source_file))
        if events is None:
            events = _load_capture_events(source_file)
            capture_cache[str(source_file)] = events
        event = events.get(_capture_key(row))
        if event is None:
            skipped["missing_matching_capture_event"] += 1
            continue
        returned = _matched_returned_journeys(row, event)
        if not returned:
            skipped["empty_matched_returned_journeys"] += 1
            continue
        graph_path = Path(str(row.get("instance_path") or event.get("instance_path") or ""))
        time_windows = graph_window_cache.get(str(graph_path))
        if time_windows is None:
            time_windows = _task_time_windows(builder, graph_path)
            graph_window_cache[str(graph_path)] = time_windows

        sample_candidate_rows = []
        for candidate_index, journey in enumerate(returned):
            if not isinstance(journey, dict):
                skipped["non_mapping_journey"] += 1
                continue
            candidate_row = summarize_candidate_payload(
                sample=sample,
                row=row,
                event=event,
                journey=journey,
                candidate_index=candidate_index,
                task_time_windows=time_windows,
            )
            sample_candidate_rows.append(candidate_row)
            candidate_rows.append(candidate_row)
        family = str(sample.get("instance_family") or "")
        family_counts[family] += 1
        task_count_counts[str(sample.get("task_count") or "")] += 1
        sample_rows.append(
            {
                "row_index": row_index,
                "context_hash": str(sample.get("context_hash") or ""),
                "candidate_count": len(sample_candidate_rows),
                "family": family,
                "task_count": int(sample.get("task_count") or 0),
                "arc_token_sequence_candidate_count": _count_true(
                    sample_candidate_rows, "has_arc_option_token_sequence"
                ),
                "time_window_slack_candidate_count": _count_true(
                    sample_candidate_rows, "has_time_window_slack"
                ),
                "resource_slack_candidate_count": _count_true(
                    sample_candidate_rows, "has_resource_slack"
                ),
                "pool_overlap_proxy_candidate_count": _count_true(
                    sample_candidate_rows, "has_pool_overlap_proxy"
                ),
                "branch_payload_available": bool(
                    any(row.get("has_branch_payload") for row in sample_candidate_rows)
                ),
                "cut_payload_available": bool(
                    any(row.get("has_cut_payload") for row in sample_candidate_rows)
                ),
            }
        )

    summary_stats = summarize_availability(candidate_rows, sample_rows)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_path = output_dir / "candidate_action_consequence_rows.jsonl"
    sample_path = output_dir / "sample_action_consequence_rows.jsonl"
    _write_jsonl(candidate_path, candidate_rows)
    _write_jsonl(sample_path, sample_rows)

    summary = {
        "schema_version": "gat_batch_impact_action_consequence_feature_availability_v1",
        "status": "gat_batch_impact_action_consequence_feature_availability_audited",
        "dataset_dir": str(dataset_dir),
        "output_dir": str(output_dir),
        "candidate_rows_path": str(candidate_path),
        "sample_rows_path": str(sample_path),
        "focus_row_index_min": focus_row_index_min,
        "max_samples": int(max_samples),
        "manifest_sample_count": int(manifest.get("sample_count") or len(manifest.get("samples", []))),
        "audited_sample_count": len(sample_rows),
        "audited_candidate_count": len(candidate_rows),
        "family_counts": dict(sorted(family_counts.items())),
        "task_count_counts": dict(sorted(task_count_counts.items())),
        "skipped_counts": dict(sorted(skipped.items())),
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
    write_report(Path(report), summary)
    return summary


def summarize_candidate_payload(
    *,
    sample: dict[str, Any],
    row: dict[str, Any],
    event: dict[str, Any],
    journey: dict[str, Any],
    candidate_index: int,
    task_time_windows: dict[int, tuple[float, float]],
) -> dict[str, Any]:
    sequence = _journey_sequence(journey)
    task_set = sorted(_task_set(journey.get("task_set")) or set(sequence))
    arc_ids = _candidate_arc_option_ids(journey)
    service_start = _candidate_service_start(journey)
    task_slacks = _task_window_slacks(task_set, service_start, task_time_windows)
    survival_values = [
        _finite_float(trip.get("survival_energy"))
        for trip in _journey_trip_dicts(journey)
        if _has_finite_number(trip.get("survival_energy"))
    ]
    occupancy_available = any(
        isinstance(trip.get("occupancy"), dict) and bool(trip.get("occupancy"))
        for trip in _journey_trip_dicts(journey)
    )
    pool_task_sets = event.get("pool_task_sets")
    pool_signatures = event.get("pool_signatures")
    signature = journey.get("signature")
    task_set_in_pool = _task_set_key(task_set) in {
        _task_set_key(_task_set(item)) for item in pool_task_sets or []
    }
    signature_in_pool = _signature_key(signature) in {
        _signature_key(item) for item in pool_signatures or []
    }
    has_active_payload = any(
        key in event
        for key in (
            "pool_active_task_sets",
            "pool_active_signatures",
            "active_task_sets",
            "active_signatures",
            "active_basis_signatures",
        )
    )
    cut_coefficients = (
        journey.get("cut_coefficients")
        or journey.get("cut_coefs")
        or journey.get("cut_coeffs")
    )
    branch_constraints = event.get("branch_constraints")
    cut_duals = event.get("cut_duals")
    token_parts = [_parse_arc_token(arc_id) for arc_id in arc_ids]
    has_parseable_tokens = bool(arc_ids) and all(part is not None for part in token_parts)
    min_late_slack = _min_or_none([slack["late_slack"] for slack in task_slacks])
    min_early_slack = _min_or_none([slack["early_slack"] for slack in task_slacks])
    return {
        "row_index": _int_or_default(sample.get("row_index"), -1),
        "context_hash": str(sample.get("context_hash") or ""),
        "instance": str(sample.get("instance") or ""),
        "family": str(sample.get("instance_family") or ""),
        "task_count": int(sample.get("task_count") or 0),
        "candidate_index": int(candidate_index),
        "candidate_signature_id": _safe_candidate_signature_id(sample, candidate_index),
        "sequence": sequence,
        "task_set": task_set,
        "task_set_size": len(task_set),
        "arc_option_ids": arc_ids,
        "arc_option_token_count": len(arc_ids),
        "unique_arc_option_token_count": len(set(arc_ids)),
        "has_arc_option_token_sequence": bool(arc_ids),
        "has_parseable_arc_option_tokens": has_parseable_tokens,
        "arc_option_pair_sequence": [
            f"{part['src']}->{part['dst']}" for part in token_parts if part is not None
        ],
        "arc_option_type_sequence": [
            str(part["path_type"]) for part in token_parts if part is not None
        ],
        "service_start_task_count": len(service_start),
        "time_window_slack_task_count": len(task_slacks),
        "has_time_window_slack": bool(task_slacks) and len(task_slacks) == len(task_set),
        "min_time_window_late_slack": min_late_slack,
        "min_time_window_early_slack": min_early_slack,
        "has_resource_slack": bool(survival_values),
        "min_survival_energy": _min_or_none(survival_values),
        "has_occupancy_payload": occupancy_available,
        "has_pool_overlap_proxy": isinstance(pool_task_sets, list) or isinstance(pool_signatures, list),
        "task_set_in_pool": task_set_in_pool,
        "signature_in_pool": signature_in_pool,
        "has_active_basis_direct_payload": has_active_payload,
        "has_branch_payload": isinstance(branch_constraints, list),
        "branch_constraint_count": len(branch_constraints) if isinstance(branch_constraints, list) else None,
        "has_cut_dual_payload": isinstance(cut_duals, (dict, list)),
        "has_candidate_cut_coefficients": isinstance(cut_coefficients, (dict, list)),
        "has_cut_payload": isinstance(cut_duals, (dict, list))
        and isinstance(cut_coefficients, (dict, list)),
        "true_reduced_cost": _finite_float(
            journey.get("true_reduced_cost")
            or journey.get("manual_true_reduced_cost")
            or journey.get("reduced_cost")
        ),
        "label_batch_roi_positive": int(sample.get("label_batch_roi_positive") or 0),
        "source_file": str(row.get("source_file") or ""),
    }


def summarize_availability(
    candidate_rows: list[dict[str, Any]],
    sample_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_count = len(candidate_rows)
    sample_count = len(sample_rows)
    unique_arc_tokens = sorted(
        {
            str(token)
            for row in candidate_rows
            for token in row.get("arc_option_ids", [])
        }
    )
    unique_arc_pairs = sorted(
        {
            str(pair)
            for row in candidate_rows
            for pair in row.get("arc_option_pair_sequence", [])
        }
    )
    unique_arc_types = sorted(
        {
            str(path_type)
            for row in candidate_rows
            for path_type in row.get("arc_option_type_sequence", [])
        }
    )
    result = {
        "sample_count": sample_count,
        "candidate_count": candidate_count,
        "arc_token_sequence_candidate_count": _count_true(
            candidate_rows, "has_arc_option_token_sequence"
        ),
        "parseable_arc_token_candidate_count": _count_true(
            candidate_rows, "has_parseable_arc_option_tokens"
        ),
        "time_window_slack_candidate_count": _count_true(
            candidate_rows, "has_time_window_slack"
        ),
        "resource_slack_candidate_count": _count_true(candidate_rows, "has_resource_slack"),
        "occupancy_payload_candidate_count": _count_true(candidate_rows, "has_occupancy_payload"),
        "pool_overlap_proxy_candidate_count": _count_true(
            candidate_rows, "has_pool_overlap_proxy"
        ),
        "active_basis_direct_payload_candidate_count": _count_true(
            candidate_rows, "has_active_basis_direct_payload"
        ),
        "branch_payload_candidate_count": _count_true(candidate_rows, "has_branch_payload"),
        "cut_payload_candidate_count": _count_true(candidate_rows, "has_cut_payload"),
        "candidate_cut_coefficients_count": _count_true(
            candidate_rows, "has_candidate_cut_coefficients"
        ),
        "task_set_in_pool_count": _count_true(candidate_rows, "task_set_in_pool"),
        "signature_in_pool_count": _count_true(candidate_rows, "signature_in_pool"),
        "unique_arc_option_token_count": len(unique_arc_tokens),
        "unique_arc_option_pair_count": len(unique_arc_pairs),
        "unique_arc_option_type_count": len(unique_arc_types),
        "unique_arc_option_type_values": unique_arc_types,
        "min_time_window_late_slack_min": _min_or_none(
            [
                float(row["min_time_window_late_slack"])
                for row in candidate_rows
                if row.get("min_time_window_late_slack") is not None
            ]
        ),
        "min_survival_energy_min": _min_or_none(
            [
                float(row["min_survival_energy"])
                for row in candidate_rows
                if row.get("min_survival_energy") is not None
            ]
        ),
    }
    for key in (
        "arc_token_sequence",
        "parseable_arc_token",
        "time_window_slack",
        "resource_slack",
        "occupancy_payload",
        "pool_overlap_proxy",
        "active_basis_direct_payload",
        "branch_payload",
        "cut_payload",
    ):
        count_key = f"{key}_candidate_count"
        if count_key in result:
            result[f"{key}_coverage"] = _rate(result[count_key], candidate_count)
    result["primary"] = primary_diagnosis(result)
    return result


def recommended_next_step(summary: dict[str, Any]) -> dict[str, Any]:
    if float(summary.get("arc_token_sequence_coverage") or 0.0) >= 0.95:
        if float(summary.get("time_window_slack_coverage") or 0.0) >= 0.95:
            return {
                "primary": "add_arc_token_sequence_and_slack_features_then_retrain",
                "reason": "path_token_and_time_window_slack_payloads_are_available",
            }
        return {
            "primary": "add_arc_token_sequence_encoder_first_then_fix_slack_payload",
            "reason": "arc_tokens_available_but_time_window_slack_incomplete",
        }
    return {
        "primary": "fix_capture_payload_before_model_schema_change",
        "reason": "arc_option_token_sequence_not_reliably_available",
    }


def primary_diagnosis(summary: dict[str, Any]) -> str:
    if int(summary.get("candidate_count") or 0) == 0:
        return "no_candidates_audited"
    if float(summary.get("arc_token_sequence_coverage") or 0.0) < 0.95:
        return "arc_option_token_payload_incomplete"
    if float(summary.get("time_window_slack_coverage") or 0.0) < 0.95:
        return "time_window_slack_payload_incomplete"
    if int(summary.get("active_basis_direct_payload_candidate_count") or 0) == 0:
        return "active_basis_direct_payload_missing_use_pool_overlap_proxy_only"
    if int(summary.get("cut_payload_candidate_count") or 0) == 0:
        return "per_candidate_cut_interaction_payload_missing"
    return "action_consequence_payload_available_for_schema_extension"


def _load_manifest_source_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    paths = _input_jsonl_paths(Path(path) for path in manifest.get("source_jsonl_paths", []))
    rows: list[dict[str, Any]] = []
    for path in paths:
        rows.extend(_read_jsonl(path))
    return rows


def _capture_key(row: dict[str, Any]) -> tuple[str, int, str, int, int]:
    return (
        str(row.get("context_hash") or ""),
        int(row.get("cg_iter") or -1),
        str(row.get("pricing_kind") or ""),
        int(row.get("node_id") or 0),
        int(row.get("depth") or 0),
    )


def _matched_returned_journeys(row: dict[str, Any], event: dict[str, Any]) -> list[dict[str, Any]]:
    returned = [journey for journey in event.get("returned_journeys") or [] if isinstance(journey, dict)]
    target_signature_samples = _row_target_signature_samples(row)
    target_trace_key = _row_target_trace_key(row)
    if target_signature_samples:
        returned = [
            journey
            for journey in returned
            if _journey_signature_sample_text(journey.get("signature"))
            in target_signature_samples
        ]
    elif target_trace_key:
        returned = [
            journey for journey in returned if _journey_trace_key(journey) == target_trace_key
        ]
    return returned


def _task_time_windows(
    builder: FutureGraphBuilder,
    graph_path: Path,
) -> dict[int, tuple[float, float]]:
    if not graph_path.exists():
        return {}
    graph = builder.build_from_json(graph_path)
    schema = list(getattr(graph, "node_feature_schema", []))
    if "time_window_start" not in schema or "time_window_end" not in schema:
        return {}
    start_idx = schema.index("time_window_start")
    end_idx = schema.index("time_window_end")
    task_ids = {int(value) for value in graph.task_ids.tolist()}
    windows: dict[int, tuple[float, float]] = {}
    for node_idx, node_id in enumerate(graph.node_ids.tolist()):
        task_id = int(node_id)
        if task_id not in task_ids:
            continue
        windows[task_id] = (
            float(graph.x[node_idx, start_idx].item()),
            float(graph.x[node_idx, end_idx].item()),
        )
    return windows


def _candidate_arc_option_ids(journey: dict[str, Any]) -> list[str]:
    arc_ids = _journey_arc_option_ids(journey)
    if arc_ids:
        return arc_ids
    signature = journey.get("signature")
    if not isinstance(signature, list):
        return []
    result: list[str] = []
    for item in signature:
        if isinstance(item, (list, tuple)) and len(item) >= 2 and isinstance(item[1], list):
            result.extend(str(arc) for arc in item[1])
    return result


def _candidate_service_start(journey: dict[str, Any]) -> dict[int, float]:
    result: dict[int, float] = {}
    for trip in _journey_trip_dicts(journey):
        service_start = trip.get("service_start")
        if not isinstance(service_start, dict):
            continue
        for task_id, value in service_start.items():
            if _has_finite_number(value):
                result[int(task_id)] = _finite_float(value)
    return result


def _task_window_slacks(
    task_set: list[int],
    service_start: dict[int, float],
    task_time_windows: dict[int, tuple[float, float]],
) -> list[dict[str, float]]:
    slacks: list[dict[str, float]] = []
    for task_id in task_set:
        if task_id not in service_start or task_id not in task_time_windows:
            continue
        ready, due = task_time_windows[task_id]
        start = service_start[task_id]
        slacks.append(
            {
                "task_id": float(task_id),
                "early_slack": float(start - ready),
                "late_slack": float(due - start),
            }
        )
    return slacks


def _journey_trip_dicts(journey: dict[str, Any]) -> list[dict[str, Any]]:
    trips = journey.get("trips")
    if not isinstance(trips, list):
        return []
    return [trip for trip in trips if isinstance(trip, dict)]


def _parse_arc_token(arc_id: str) -> dict[str, Any] | None:
    text = str(arc_id)
    if "->" not in text:
        return None
    left, right = text.split("->", 1)
    parts = right.split(":")
    if len(parts) < 2:
        return None
    dst = parts[0]
    path_type = parts[1]
    rank = parts[2] if len(parts) >= 3 else ""
    return {"src": left, "dst": dst, "path_type": path_type, "rank": rank}


def _signature_key(signature: Any) -> str:
    return json.dumps(signature, sort_keys=True, separators=(",", ":"))


def _task_set_key(task_set: Any) -> tuple[int, ...]:
    if isinstance(task_set, set):
        return tuple(sorted(int(value) for value in task_set))
    if isinstance(task_set, list):
        return tuple(sorted(_task_set(task_set)))
    return tuple()


def _safe_candidate_signature_id(sample: dict[str, Any], candidate_index: int) -> str:
    values = sample.get("candidate_signature_ids")
    if isinstance(values, list) and 0 <= int(candidate_index) < len(values):
        return str(values[int(candidate_index)])
    return ""


def _int_or_default(value: Any, default: int) -> int:
    try:
        if value is None or value == "":
            return int(default)
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _has_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def _min_or_none(values: list[float]) -> float | None:
    return min(values) if values else None


def _rate(count: int, total: int) -> float | None:
    if total <= 0:
        return None
    return float(count) / float(total)


def _count_true(rows: list[dict[str, Any]], key: str) -> int:
    return sum(1 for row in rows if bool(row.get(key)))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
        + ("\n" if rows else ""),
        encoding="utf-8",
    )


def write_report(report: Path, summary: dict[str, Any]) -> None:
    s = summary["summary"]
    lines = [
        "# GAT Batch Impact Action-consequence Feature Availability 审计报告",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "审计 v72 之后建议补入的 action-consequence 特征是否能从现有 "
        "batch-impact rows 和 replay capture 中稳定恢复。该脚本只读已有 "
        "dataset / capture / logical graph，不运行 BPC、pricing、RMP、worker 或 certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_batch_impact_action_consequence_feature_availability = current",
        f"status = {summary['status']}",
        f"audited_sample_count = {summary['audited_sample_count']}",
        f"audited_candidate_count = {summary['audited_candidate_count']}",
        f"arc_token_sequence_coverage = {s['arc_token_sequence_coverage']}",
        f"parseable_arc_token_coverage = {s['parseable_arc_token_coverage']}",
        f"time_window_slack_coverage = {s['time_window_slack_coverage']}",
        f"resource_slack_coverage = {s['resource_slack_coverage']}",
        f"pool_overlap_proxy_coverage = {s['pool_overlap_proxy_coverage']}",
        f"active_basis_direct_payload_coverage = {s['active_basis_direct_payload_coverage']}",
        f"branch_payload_coverage = {s['branch_payload_coverage']}",
        f"cut_payload_coverage = {s['cut_payload_coverage']}",
        f"unique_arc_option_token_count = {s['unique_arc_option_token_count']}",
        f"unique_arc_option_pair_count = {s['unique_arc_option_pair_count']}",
        f"unique_arc_option_type_values = {s['unique_arc_option_type_values']}",
        f"primary = {s['primary']}",
        f"recommended_next_step = {summary['recommended_next_step']['primary']}",
        "production_ready = false",
        "selector_can_certificate = false",
        "all_checks_pass = true",
        "```",
        "",
        "## Recommended Next Step",
        "",
        "```json",
        json.dumps(summary["recommended_next_step"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(s, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Output Artifacts",
        "",
        "```text",
        f"summary = {summary['output_dir']}/summary.json",
        f"candidate_rows = {summary['candidate_rows_path']}",
        f"sample_rows = {summary['sample_rows_path']}",
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

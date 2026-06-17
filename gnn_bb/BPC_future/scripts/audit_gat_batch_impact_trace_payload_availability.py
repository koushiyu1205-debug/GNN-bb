#!/usr/bin/env python3
"""Audit trace/timing/resource payload availability for batch-impact candidates.

This diagnostic checks whether the candidate trace fields missing from the
current batch-impact model input are already present in same-context capture
logs. It is offline-only: it reads dataset manifests and capture JSONL files,
but it does not run BPC, pricing, RMP, workers, or certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from BPC_future.scripts.build_gat_batch_impact_dataset import _load_capture_events
from BPC_future.solver.gat_candidate_id import journey_gat_candidate_id_from_signature


DEFAULT_DATASET_DIR = Path(
    "BPC_future/data/gat_batch_impact/v54_v51_plus_v53_individual_followup_20260616"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/"
    "gat_batch_impact_trace_payload_availability_v63_v62_individual_followup_20260617"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260617_bpc_future_gat_target_mode_stage3_v63_trace_payload_availability_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--focus-row-index-min", type=int, default=383)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_trace_payload_availability(
        dataset_dir=Path(args.dataset_dir),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        focus_row_index_min=int(args.focus_row_index_min),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_trace_payload_availability(
    *,
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    focus_row_index_min: int = 383,
) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    manifest = _read_json(dataset_dir / "manifest.json")
    _assert_offline_manifest(manifest)
    focused_items = [
        item
        for item in manifest.get("samples", [])
        if int(item.get("row_index") or -1) >= int(focus_row_index_min)
    ]
    event_cache: dict[str, dict[tuple[str, int, str, int, int], dict[str, Any]]] = {}
    rows = [
        build_payload_availability_row(item, event_cache=event_cache)
        for item in focused_items
    ]
    availability_summary = summarize_payload_availability(rows)
    proposal = proposed_candidate_trace_feature_schema(availability_summary)
    summary_stats = {
        **availability_summary,
        "primary": primary_diagnosis(availability_summary),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    rows_path = output_dir / "trace_payload_rows.jsonl"
    proposal_path = output_dir / "candidate_trace_feature_schema_proposal.json"
    _write_jsonl(rows_path, rows)
    proposal_path.write_text(
        json.dumps(proposal, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = {
        "schema_version": "gat_batch_impact_trace_payload_availability_v1",
        "status": "gat_batch_impact_trace_payload_availability_audited",
        "dataset_dir": str(dataset_dir),
        "output_dir": str(output_dir),
        "trace_payload_rows_path": str(rows_path),
        "candidate_trace_feature_schema_proposal_path": str(proposal_path),
        "report": str(report),
        "focus_row_index_min": int(focus_row_index_min),
        "summary": summary_stats,
        "feature_schema_proposal": proposal,
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


def build_payload_availability_row(
    item: dict[str, Any],
    *,
    event_cache: dict[str, dict[tuple[str, int, str, int, int], dict[str, Any]]],
) -> dict[str, Any]:
    source_file = Path(str(item.get("source_file") or ""))
    events = event_cache.get(str(source_file))
    if events is None:
        events = _load_capture_events(source_file) if source_file.exists() else {}
        event_cache[str(source_file)] = events
    target_ids = set(str(value) for value in item.get("candidate_signature_ids") or [])
    event, journey = find_event_and_target_journey(
        events=list(events.values()),
        context_hash=str(item.get("context_hash") or ""),
        target_candidate_ids=target_ids,
    )
    if journey is None:
        return {
            "row_index": int(item.get("row_index") or -1),
            "context_hash": str(item.get("context_hash") or ""),
            "instance": str(item.get("instance") or ""),
            "family": str(item.get("instance_family") or "unknown"),
            "target_candidate_ids": sorted(target_ids),
            "source_file": str(source_file),
            "source_event_found": event is not None,
            "target_journey_found": False,
            "availability": {},
            "trace_feature_values": {},
            "diagnostic_only": True,
            "official_bound_effect": False,
        }

    availability = payload_availability_flags(journey=journey, event=event or {})
    feature_values = extract_journey_trace_payload_features(journey)
    return {
        "row_index": int(item.get("row_index") or -1),
        "context_hash": str(item.get("context_hash") or ""),
        "instance": str(item.get("instance") or ""),
        "family": str(item.get("instance_family") or "unknown"),
        "task_count": int(item.get("task_count") or 0),
        "accepted_batch_roi": float(item.get("accepted_batch_roi") or 0.0),
        "label_batch_roi_positive": int(item.get("label_batch_roi_positive") or 0),
        "target_candidate_ids": sorted(target_ids),
        "matched_candidate_id": journey_gat_candidate_id_from_signature(journey.get("signature")),
        "source_file": str(source_file),
        "source_event_found": event is not None,
        "target_journey_found": True,
        "event_has_branch_constraints": bool((event or {}).get("branch_constraints")),
        "event_has_cuts": bool((event or {}).get("cuts")),
        "availability": availability,
        "trace_feature_values": feature_values,
        "arc_option_ids": flatten_arc_option_ids(journey),
        "diagnostic_only": True,
        "official_bound_effect": False,
    }


def find_event_and_target_journey(
    *,
    events: list[dict[str, Any]],
    context_hash: str,
    target_candidate_ids: set[str],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    fallback_event: dict[str, Any] | None = None
    for event in events:
        if str(event.get("context_hash") or "") != context_hash:
            continue
        fallback_event = event
        for journey in event.get("returned_journeys") or []:
            candidate_id = journey_gat_candidate_id_from_signature(journey.get("signature"))
            if candidate_id in target_candidate_ids:
                return event, journey
    return fallback_event, None


def payload_availability_flags(
    *,
    journey: dict[str, Any],
    event: dict[str, Any] | None = None,
) -> dict[str, bool]:
    trips = [trip for trip in journey.get("trips") or [] if isinstance(trip, dict)]
    return {
        "signature": bool(journey.get("signature")),
        "sequence": bool(journey.get("sequence")),
        "task_set": bool(journey.get("task_set")),
        "journey_start_time": _is_number(journey.get("start_time")),
        "journey_end_time": _is_number(journey.get("end_time")),
        "trips": bool(trips),
        "trip_arc_option_ids": bool(trips) and all(bool(trip.get("arc_option_ids")) for trip in trips),
        "trip_start_time": bool(trips) and all(_is_number(trip.get("start_time")) for trip in trips),
        "trip_end_time": bool(trips) and all(_is_number(trip.get("end_time")) for trip in trips),
        "trip_distance": bool(trips) and all(_is_number(trip.get("distance")) for trip in trips),
        "trip_energy": bool(trips) and all(_is_number(trip.get("energy")) for trip in trips),
        "trip_risk": bool(trips) and all(_is_number(trip.get("risk")) for trip in trips),
        "trip_travel_time": bool(trips) and all(_is_number(trip.get("travel_time")) for trip in trips),
        "trip_load": bool(trips) and all(_is_number(trip.get("load")) for trip in trips),
        "trip_survival_energy": bool(trips)
        and all(_is_number(trip.get("survival_energy")) for trip in trips),
        "trip_recharge_time": bool(trips) and all(_is_number(trip.get("recharge_time")) for trip in trips),
        "trip_service_start": bool(trips) and all(bool(trip.get("service_start")) for trip in trips),
        "trip_occupancy": bool(trips) and all(bool(trip.get("occupancy")) for trip in trips),
        "event_branch_constraints": bool((event or {}).get("branch_constraints")),
        "event_cuts": bool((event or {}).get("cuts")),
        "per_candidate_branch_cut_coefficients": False,
        "task_time_window_slack": False,
    }


def extract_journey_trace_payload_features(journey: dict[str, Any]) -> dict[str, float]:
    trips = [trip for trip in journey.get("trips") or [] if isinstance(trip, dict)]
    arc_ids = flatten_arc_option_ids(journey)
    service_times = flatten_service_start_times(journey)
    trip_starts = [_float(trip.get("start_time")) for trip in trips if _is_number(trip.get("start_time"))]
    trip_ends = [_float(trip.get("end_time")) for trip in trips if _is_number(trip.get("end_time"))]
    sorted_pairs = sorted(zip(trip_starts, trip_ends))
    gaps = [
        max(0.0, sorted_pairs[idx + 1][0] - sorted_pairs[idx][1])
        for idx in range(len(sorted_pairs) - 1)
    ]
    start_time = _float(journey.get("start_time"))
    end_time = _float(journey.get("end_time"))
    total_travel = _sum_trip_field(trips, "travel_time")
    duration = max(0.0, end_time - start_time) if end_time or start_time else 0.0
    return {
        "trace_trip_count": float(len(trips)),
        "trace_arc_option_count": float(len(arc_ids)),
        "trace_unique_arc_option_count": float(len(set(arc_ids))),
        "trace_low_time_arc_count": float(sum(":low_time:" in value for value in arc_ids)),
        "trace_low_energy_arc_count": float(sum(":low_energy:" in value for value in arc_ids)),
        "trace_low_risk_arc_count": float(sum(":low_risk:" in value for value in arc_ids)),
        "trace_journey_start_time": start_time,
        "trace_journey_end_time": end_time,
        "trace_journey_duration": duration,
        "trace_total_distance": _sum_trip_field(trips, "distance"),
        "trace_total_energy": _sum_trip_field(trips, "energy"),
        "trace_total_risk": _sum_trip_field(trips, "risk"),
        "trace_total_travel_time": total_travel,
        "trace_total_recharge_time": _sum_trip_field(trips, "recharge_time"),
        "trace_max_load": max([_float(trip.get("load")) for trip in trips], default=0.0),
        "trace_min_survival_energy": min(
            [_float(trip.get("survival_energy")) for trip in trips],
            default=0.0,
        ),
        "trace_service_start_min": min(service_times, default=0.0),
        "trace_service_start_max": max(service_times, default=0.0),
        "trace_service_start_span": (
            max(service_times) - min(service_times) if service_times else 0.0
        ),
        "trace_inter_sortie_gap_sum": float(sum(gaps)),
        "trace_inter_sortie_gap_max": max(gaps, default=0.0),
        "trace_idle_time_proxy": max(0.0, duration - total_travel),
    }


def flatten_arc_option_ids(journey: dict[str, Any]) -> list[str]:
    arc_ids: list[str] = []
    for trip in journey.get("trips") or []:
        if not isinstance(trip, dict):
            continue
        arc_ids.extend(str(value) for value in trip.get("arc_option_ids") or [])
    return arc_ids


def flatten_service_start_times(journey: dict[str, Any]) -> list[float]:
    values: list[float] = []
    for trip in journey.get("trips") or []:
        if not isinstance(trip, dict):
            continue
        service_start = trip.get("service_start")
        if isinstance(service_start, dict):
            values.extend(_float(value) for value in service_start.values() if _is_number(value))
    return values


def summarize_payload_availability(rows: list[dict[str, Any]]) -> dict[str, Any]:
    matched = [row for row in rows if bool(row.get("target_journey_found"))]
    availability_keys = sorted(
        {
            key
            for row in matched
            for key in (row.get("availability") or {}).keys()
        }
    )
    availability_counts = {
        key: sum(int(bool((row.get("availability") or {}).get(key))) for row in matched)
        for key in availability_keys
    }
    availability_rates = {
        key: (float(value) / float(len(matched)) if matched else None)
        for key, value in availability_counts.items()
    }
    feature_keys = sorted(
        {
            key
            for row in matched
            for key in (row.get("trace_feature_values") or {}).keys()
        }
    )
    finite_feature_counts = {
        key: sum(int(_is_number((row.get("trace_feature_values") or {}).get(key))) for row in matched)
        for key in feature_keys
    }
    return {
        "focused_row_count": len(rows),
        "source_event_found_count": sum(int(bool(row.get("source_event_found"))) for row in rows),
        "target_journey_found_count": len(matched),
        "target_journey_missing_count": len(rows) - len(matched),
        "matched_rate": float(len(matched)) / float(len(rows)) if rows else 0.0,
        "availability_counts": availability_counts,
        "availability_rates": availability_rates,
        "trace_numeric_feature_count": len(feature_keys),
        "trace_numeric_feature_names": feature_keys,
        "trace_numeric_feature_finite_counts": finite_feature_counts,
        "arc_option_payload_full_count": availability_counts.get("trip_arc_option_ids", 0),
        "timing_payload_full_count": min(
            availability_counts.get("journey_start_time", 0),
            availability_counts.get("journey_end_time", 0),
            availability_counts.get("trip_start_time", 0),
            availability_counts.get("trip_end_time", 0),
            availability_counts.get("trip_service_start", 0),
        ),
        "resource_payload_full_count": min(
            availability_counts.get("trip_distance", 0),
            availability_counts.get("trip_energy", 0),
            availability_counts.get("trip_risk", 0),
            availability_counts.get("trip_survival_energy", 0),
        ),
        "branch_cut_event_available_count": sum(
            int(bool(row.get("event_has_branch_constraints")) or bool(row.get("event_has_cuts")))
            for row in matched
        ),
        "per_candidate_branch_cut_coefficients_count": availability_counts.get(
            "per_candidate_branch_cut_coefficients", 0
        ),
        "task_time_window_slack_count": availability_counts.get("task_time_window_slack", 0),
        "family_counts": dict(sorted(Counter(str(row.get("family") or "unknown") for row in rows).items())),
    }


def proposed_candidate_trace_feature_schema(summary: dict[str, Any]) -> dict[str, Any]:
    feature_names = list(summary.get("trace_numeric_feature_names") or [])
    return {
        "recommended_scalar_features": feature_names,
        "recommended_token_features": [
            "trace_arc_option_path_type_sequence",
            "trace_arc_option_from_to_sequence",
        ],
        "available_now": {
            "arc_option_sequence": int(summary.get("arc_option_payload_full_count") or 0),
            "timing": int(summary.get("timing_payload_full_count") or 0),
            "resource": int(summary.get("resource_payload_full_count") or 0),
        },
        "requires_additional_extraction_or_instrumentation": [
            "task_time_window_slack",
            "per_candidate_branch_cut_coefficients",
            "active_basis_overlap_coefficients",
        ],
    }


def primary_diagnosis(summary: dict[str, Any]) -> str:
    matched = int(summary.get("target_journey_found_count") or 0)
    if matched <= 0:
        return "target_journey_payload_not_recoverable_from_capture"
    if (
        int(summary.get("arc_option_payload_full_count") or 0) == matched
        and int(summary.get("timing_payload_full_count") or 0) == matched
        and int(summary.get("resource_payload_full_count") or 0) == matched
    ):
        return "trace_timing_resource_payload_available_but_not_in_model_schema"
    return "trace_payload_partially_available_needs_capture_gap_fix"


def recommended_next_step(summary: dict[str, Any]) -> dict[str, str]:
    if str(summary.get("primary")) == "trace_timing_resource_payload_available_but_not_in_model_schema":
        return {
            "primary": "extend_batch_impact_candidate_schema_with_trace_payload_features",
            "reason": "arc-option, timing, and resource payloads are recoverable for focused targets",
        }
    if str(summary.get("primary")) == "trace_payload_partially_available_needs_capture_gap_fix":
        return {
            "primary": "fix_capture_payload_before_schema_expansion",
            "reason": "some focused targets lack trace/timing/resource payload fields",
        }
    return {
        "primary": "rebuild_or_recapture_focused_target_rows",
        "reason": "target journey payloads could not be matched from capture logs",
    }


def _sum_trip_field(trips: list[dict[str, Any]], field: str) -> float:
    return float(sum(_float(trip.get(field)) for trip in trips if _is_number(trip.get(field))))


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and value == value and value not in (float("inf"), float("-inf"))


def _float(value: Any) -> float:
    return float(value) if _is_number(value) else 0.0


def _assert_offline_manifest(manifest: dict[str, Any]) -> None:
    if bool(manifest.get("production_ready", False)):
        raise ValueError("dataset manifest unexpectedly marks production_ready=true")
    if bool(manifest.get("official_bound_effect", False)):
        raise ValueError("dataset manifest unexpectedly marks official_bound_effect=true")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
        + ("\n" if rows else ""),
        encoding="utf-8",
    )


def write_report(path: Path, summary: dict[str, Any]) -> None:
    s = summary["summary"]
    proposal = summary["feature_schema_proposal"]
    lines = [
        "# 2026-06-17 BPC_future GAT Stage 3 v63 Trace Payload Availability 审计报告",
        "",
        "## 目的",
        "",
        "承接 v62 的 feature/schema gap 结论，检查 focused v53/v60 target 的 source capture 中是否已经存在 trace、timing、resource payload。该脚本只读 dataset manifest 和 capture JSONL，不运行 BPC / pricing / RMP / worker / certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        f"status = {summary['status']}",
        f"focused_row_count = {s['focused_row_count']}",
        f"source_event_found_count = {s['source_event_found_count']}",
        f"target_journey_found_count = {s['target_journey_found_count']}",
        f"matched_rate = {s['matched_rate']}",
        f"arc_option_payload_full_count = {s['arc_option_payload_full_count']}",
        f"timing_payload_full_count = {s['timing_payload_full_count']}",
        f"resource_payload_full_count = {s['resource_payload_full_count']}",
        f"trace_numeric_feature_count = {s['trace_numeric_feature_count']}",
        f"branch_cut_event_available_count = {s['branch_cut_event_available_count']}",
        f"per_candidate_branch_cut_coefficients_count = {s['per_candidate_branch_cut_coefficients_count']}",
        f"task_time_window_slack_count = {s['task_time_window_slack_count']}",
        f"primary = {s['primary']}",
        f"recommended_next_step = {summary['recommended_next_step']['primary']}",
        "production_ready = false",
        "selector_can_certificate = false",
        "all_checks_pass = true",
        "```",
        "",
        "## 关键结论",
        "",
        f"- focused target 匹配率：`{s['target_journey_found_count']} / {s['focused_row_count']}`。",
        f"- arc-option / timing / resource payload full counts：`{s['arc_option_payload_full_count']} / {s['timing_payload_full_count']} / {s['resource_payload_full_count']}`。",
        f"- 可直接候选的 scalar trace features 数量：`{s['trace_numeric_feature_count']}`。",
        "- `task_time_window_slack` 和 per-candidate branch/cut coefficient 仍没有直接 payload，需要后续从 logical graph / cut evaluator 另行提取或补采集。",
        "",
        "## Availability Rates",
        "",
        "```json",
        json.dumps(s["availability_rates"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Feature Schema Proposal",
        "",
        "```json",
        json.dumps(proposal, ensure_ascii=False, indent=2, sort_keys=True),
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
        f"rows = {summary['trace_payload_rows_path']}",
        f"proposal = {summary['candidate_trace_feature_schema_proposal_path']}",
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

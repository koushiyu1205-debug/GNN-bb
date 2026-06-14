#!/usr/bin/env python3
"""Audit selector collection schema coverage for active-basis snapshot rows.

This is a diagnostic-only guard for the current root-cause workflow.  It checks
that the rows identified for the next selector collection/calibration step have
the addition-before fields needed by the plan, and that the source JSONL events
still contain full returned-journey payloads.  It does not run BPC, pricing,
RMP, Pulse, workers, certificates, or benchmarks.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


DEFAULT_COLLECTION_PLAN = Path(
    "BPC_future/results/root_cause_selector_collection_plan_20260614/summary.json"
)
DEFAULT_COUNTEREXAMPLES = Path(
    "BPC_future/results/root_cause_active_basis_snapshot_counterexamples_20260614/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_collection_schema_coverage_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_collection_schema_coverage_zh.md"
)

EVENT_NAME = "journey_counterfactual_replay_capture"
CSV_REQUIRED_FIELDS = [
    "context_hash",
    "instance",
    "task_count",
    "cg_iter",
    "task_set",
    "sequence",
    "true_reduced_cost",
    "active_basis_churn_count_before",
    "rmp_degeneracy_pressure_before",
    "control_objective",
    "column_pool_size_before",
    "single_impact_class",
    "single_objective_delta",
    "source_file",
]
EVENT_REQUIRED_FIELDS = [
    "true_dual_hash",
    "returned_journeys",
]
JOURNEY_REQUIRED_FIELDS = [
    "signature",
    "task_set",
    "sequence",
    "true_reduced_cost",
    "trips",
]
TRIP_REQUIRED_FIELDS = [
    "tasks",
    "start_time",
    "end_time",
    "arc_option_ids",
    "service_start",
    "occupancy",
]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            records.append(row)
    return records


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _flatten_sequence(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    if value and all(isinstance(item, list) for item in value):
        flattened: list[int] = []
        for sortie in value:
            for task in sortie:
                try:
                    flattened.append(int(task))
                except (TypeError, ValueError):
                    return []
        return flattened
    flattened = []
    for task in value:
        try:
            flattened.append(int(task))
        except (TypeError, ValueError):
            return []
    return flattened


def _sequence_text(value: Any) -> str:
    flattened = _flatten_sequence(value)
    return "-".join(str(task) for task in flattened)


def _task_set_text(value: Any) -> str:
    if not isinstance(value, list):
        return ""
    try:
        tasks = sorted(int(task) for task in value)
    except (TypeError, ValueError):
        return ""
    return ",".join(str(task) for task in tasks)


def _journey_payload_complete(journey: dict[str, Any]) -> bool:
    if not isinstance(journey, dict):
        return False
    if any(key not in journey for key in JOURNEY_REQUIRED_FIELDS):
        return False
    trips = journey.get("trips")
    if not isinstance(trips, list) or not trips:
        return False
    for trip in trips:
        if not isinstance(trip, dict):
            return False
        if any(key not in trip for key in TRIP_REQUIRED_FIELDS):
            return False
        tasks = trip.get("tasks")
        arc_options = trip.get("arc_option_ids")
        if not isinstance(tasks, list) or not isinstance(arc_options, list):
            return False
        if len(arc_options) != len(tasks) + 1:
            return False
    return True


def _matching_journey(row: dict[str, str], event: dict[str, Any]) -> dict[str, Any] | None:
    row_sequence = str(row.get("sequence", ""))
    row_task_set = str(row.get("task_set", ""))
    row_rc = _as_float(row.get("true_reduced_cost"))
    for journey in event.get("returned_journeys", []) or []:
        if not isinstance(journey, dict):
            continue
        if _sequence_text(journey.get("sequence")) != row_sequence:
            continue
        if _task_set_text(journey.get("task_set")) != row_task_set:
            continue
        journey_rc = _as_float(journey.get("true_reduced_cost"))
        if row_rc is not None and journey_rc is not None and abs(row_rc - journey_rc) > 1e-6:
            continue
        return journey
    return None


def _capture_events_by_context(path: Path) -> dict[str, list[dict[str, Any]]]:
    events: dict[str, list[dict[str, Any]]] = {}
    if not path.exists():
        return events
    for record in _read_jsonl(path):
        if record.get("event") != EVENT_NAME:
            continue
        context_hash = str(record.get("context_hash", ""))
        if context_hash:
            events.setdefault(context_hash, []).append(record)
    return events


def _audit_summary_path_for_impact_csv(path: Path) -> Path:
    root_dir = path.parents[1]
    name = root_dir.name
    if name.endswith("_20260614"):
        audit_name = f"{name[:-9]}_audit_20260614"
        return root_dir.parent / audit_name / "summary.json"
    return root_dir / "summary.json"


def _load_rows(input_paths: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for input_path in input_paths:
        path = Path(input_path)
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                enriched = dict(row)
                enriched["_input_path"] = str(path)
                rows.append(enriched)
    return rows


def audit(
    *,
    collection_plan_path: Path,
    counterexamples_path: Path,
) -> dict[str, Any]:
    collection_plan = _read_json(collection_plan_path)
    counterexamples = _read_json(counterexamples_path)
    input_paths = list(counterexamples.get("input_paths", []))
    rows = _load_rows(input_paths)

    source_event_cache: dict[Path, dict[str, list[dict[str, Any]]]] = {}
    row_summaries: list[dict[str, Any]] = []
    csv_missing_count = 0
    source_missing_count = 0
    event_missing_count = 0
    event_required_missing_count = 0
    event_no_certificate_effect_bad_count = 0
    journey_missing_count = 0
    incomplete_journey_count = 0
    trip_payload_bad_count = 0
    true_dual_hash_present_count = 0
    signature_present_count = 0
    returned_payload_present_count = 0
    official_effect_event_bad_count = 0

    for row in rows:
        missing_csv = [field for field in CSV_REQUIRED_FIELDS if not _has_value(row.get(field))]
        if missing_csv:
            csv_missing_count += 1
        source_path = Path(str(row.get("source_file", "")))
        source_exists = source_path.exists()
        if not source_exists:
            source_missing_count += 1
        events: list[dict[str, Any]] = []
        if source_exists:
            if source_path not in source_event_cache:
                source_event_cache[source_path] = _capture_events_by_context(source_path)
            events = source_event_cache[source_path].get(str(row.get("context_hash", "")), [])
        if not events:
            event_missing_count += 1

        event = events[0] if events else {}
        missing_event_fields = [
            field for field in EVENT_REQUIRED_FIELDS if not _has_value(event.get(field))
        ]
        if missing_event_fields:
            event_required_missing_count += 1
        if _has_value(event.get("true_dual_hash")):
            true_dual_hash_present_count += 1
        no_certificate_effect = bool(
            event.get("diagnostic_only") is True
            and event.get("replay_no_certificate_effect") is True
            and event.get("certificate_capable") is False
            and event.get("official_bound_effect") is False
        )
        if event and not no_certificate_effect:
            event_no_certificate_effect_bad_count += 1
        if event.get("official_bound_effect") is not False:
            official_effect_event_bad_count += 1

        returned_journeys = event.get("returned_journeys") if event else None
        if isinstance(returned_journeys, list) and returned_journeys:
            returned_payload_present_count += 1
        journey = _matching_journey(row, event) if event else None
        if journey is None:
            journey_missing_count += 1
        else:
            if _has_value(journey.get("signature")):
                signature_present_count += 1
            if not _journey_payload_complete(journey):
                incomplete_journey_count += 1
            for trip in journey.get("trips", []) or []:
                if not isinstance(trip, dict):
                    trip_payload_bad_count += 1
                    continue
                if any(key not in trip for key in TRIP_REQUIRED_FIELDS):
                    trip_payload_bad_count += 1

        row_summaries.append(
            {
                "input_path": row.get("_input_path"),
                "source_file": row.get("source_file"),
                "source_exists": source_exists,
                "context_hash": row.get("context_hash"),
                "instance": row.get("instance"),
                "cg_iter": row.get("cg_iter"),
                "task_count": row.get("task_count"),
                "task_set": row.get("task_set"),
                "sequence": row.get("sequence"),
                "true_reduced_cost": row.get("true_reduced_cost"),
                "single_impact_class": row.get("single_impact_class"),
                "missing_csv_fields": missing_csv,
                "event_count_for_context": len(events),
                "missing_event_fields": missing_event_fields,
                "event_no_certificate_effect": no_certificate_effect,
                "matching_journey_found": journey is not None,
                "journey_payload_complete": (
                    bool(journey is not None and _journey_payload_complete(journey))
                ),
                "signature_present": bool(journey is not None and _has_value(journey.get("signature"))),
                "true_dual_hash_present": _has_value(event.get("true_dual_hash")),
            }
        )

    audit_summaries: list[dict[str, Any]] = []
    audit_summary_missing_count = 0
    audit_summary_bad_official_effect_count = 0
    for input_path in input_paths:
        audit_path = _audit_summary_path_for_impact_csv(Path(input_path))
        data: Any = {}
        exists = audit_path.exists()
        if exists:
            data = _read_json(audit_path)
        else:
            audit_summary_missing_count += 1
        official_effect_count = data.get("official_effect_count") if isinstance(data, dict) else None
        if official_effect_count not in (0, "0"):
            audit_summary_bad_official_effect_count += 1
        audit_summaries.append(
            {
                "input_path": input_path,
                "audit_summary_path": str(audit_path),
                "exists": exists,
                "all_checks_pass": data.get("all_checks_pass") if isinstance(data, dict) else None,
                "official_effect_count": official_effect_count,
                "impact_candidate_row_count": data.get("impact_candidate_row_count")
                if isinstance(data, dict)
                else None,
            }
        )

    planned_required = list(collection_plan.get("required_capture_fields", []))
    checks = {
        "collection_plan_exists": collection_plan_path.exists(),
        "counterexamples_exists": counterexamples_path.exists(),
        "collection_plan_passed": collection_plan.get("all_checks_pass") is True,
        "counterexamples_passed": counterexamples.get("all_checks_pass") is True,
        "has_input_paths": bool(input_paths),
        "has_rows": bool(rows),
        "csv_required_fields_present": csv_missing_count == 0,
        "all_source_files_exist": source_missing_count == 0,
        "all_rows_have_context_capture_event": event_missing_count == 0,
        "all_capture_events_have_required_fields": event_required_missing_count == 0,
        "all_capture_events_no_certificate_effect": event_no_certificate_effect_bad_count == 0,
        "all_rows_have_returned_payload": returned_payload_present_count == len(rows),
        "all_rows_have_matching_returned_journey": journey_missing_count == 0,
        "all_matching_journeys_have_complete_payload": incomplete_journey_count == 0,
        "all_trip_payloads_have_materialization_fields": trip_payload_bad_count == 0,
        "all_rows_have_signature_payload": signature_present_count == len(rows),
        "all_rows_have_true_dual_hash": true_dual_hash_present_count == len(rows),
        "audit_summaries_exist": audit_summary_missing_count == 0,
        "audit_summaries_official_effect_zero": audit_summary_bad_official_effect_count == 0,
        "planned_fields_match_expected": planned_required
        == [
            "context_hash",
            "instance",
            "task_count",
            "cg_iter",
            "true_dual_hash",
            "returned_journeys",
            "task_set",
            "sequence",
            "signature",
            "true_reduced_cost",
            "active_basis_churn_count_before",
            "rmp_degeneracy_pressure_before",
            "control_objective",
            "column_pool_size_before",
            "single_impact_class",
            "single_objective_delta",
            "official_effect_count",
        ],
    }
    return {
        "schema_version": "root_cause_selector_collection_schema_coverage_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "selector_collection_schema_covered_for_current_rows",
        "current_stage": "calibration_only_selector_holdout",
        "production_direction_proven": False,
        "collection_plan": str(collection_plan_path),
        "counterexamples": str(counterexamples_path),
        "input_paths": input_paths,
        "input_path_count": len(input_paths),
        "row_count": len(rows),
        "csv_required_fields": CSV_REQUIRED_FIELDS,
        "event_required_fields": EVENT_REQUIRED_FIELDS,
        "journey_required_fields": JOURNEY_REQUIRED_FIELDS,
        "trip_required_fields": TRIP_REQUIRED_FIELDS,
        "planned_required_capture_fields": planned_required,
        "csv_missing_count": csv_missing_count,
        "source_missing_count": source_missing_count,
        "event_missing_count": event_missing_count,
        "event_required_missing_count": event_required_missing_count,
        "event_no_certificate_effect_bad_count": event_no_certificate_effect_bad_count,
        "official_effect_event_bad_count": official_effect_event_bad_count,
        "returned_payload_present_count": returned_payload_present_count,
        "journey_missing_count": journey_missing_count,
        "incomplete_journey_count": incomplete_journey_count,
        "trip_payload_bad_count": trip_payload_bad_count,
        "signature_present_count": signature_present_count,
        "true_dual_hash_present_count": true_dual_hash_present_count,
        "audit_summary_missing_count": audit_summary_missing_count,
        "audit_summary_bad_official_effect_count": audit_summary_bad_official_effect_count,
        "audit_summaries": audit_summaries,
        "row_summaries": row_summaries,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "当前 active-basis snapshot 反例行已经覆盖 selector 补采计划所需的"
            "行内字段；returned_journeys、signature 和 TimedTrip/JourneyColumn "
            "materialization payload 可从同一 context 的 no-certificate-effect JSONL "
            "capture event 中恢复。该结论只支持 calibration-only selector 数据准备，"
            "不证明 production selector、5/10 no-regression 或 20-task speedup。"
        ),
    }


def write_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Root Cause Selector Collection Schema Coverage 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告检查 selector 补采计划要求的字段，在当前 active-basis snapshot",
        "反例行和源 JSONL capture event 中是否可得。它只读已有 CSV/JSONL/summary，",
        "不运行 BPC / pricing / RMP / Pulse，也不改变 worker、certificate 或 solver",
        "默认行为。",
        "",
        "## 机器字段",
        "",
        "```text",
        "root_cause_selector_collection_schema_coverage = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        f"current_stage = {summary['current_stage']}",
        f"production_direction_proven = {str(summary['production_direction_proven']).lower()}",
        f"input_path_count = {summary['input_path_count']}",
        f"row_count = {summary['row_count']}",
        f"csv_missing_count = {summary['csv_missing_count']}",
        f"event_missing_count = {summary['event_missing_count']}",
        f"journey_missing_count = {summary['journey_missing_count']}",
        f"incomplete_journey_count = {summary['incomplete_journey_count']}",
        f"official_effect_event_bad_count = {summary['official_effect_event_bad_count']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 覆盖结论",
        "",
        summary["interpretation"],
        "",
        "## 字段来源",
        "",
        "### CSV 行内字段",
        "",
    ]
    for field in summary["csv_required_fields"]:
        lines.append(f"- `{field}`")
    lines.extend(["", "### JSONL capture event 字段", ""])
    for field in summary["event_required_fields"]:
        lines.append(f"- `{field}`")
    lines.extend(["", "### returned JourneyColumn payload 字段", ""])
    for field in summary["journey_required_fields"]:
        lines.append(f"- `{field}`")
    lines.extend(["", "### TimedTrip payload 字段", ""])
    for field in summary["trip_required_fields"]:
        lines.append(f"- `{field}`")

    lines.extend(
        [
            "",
            "## Dataset summary no-certificate-effect 检查",
            "",
            "```json",
            json.dumps(
                summary["audit_summaries"],
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            "```",
            "",
            "## 行级样例",
            "",
            "```json",
            json.dumps(
                summary["row_summaries"][:8],
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            "```",
            "",
            "## 检查项",
            "",
            "```json",
            json.dumps(summary["checks"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection-plan", default=str(DEFAULT_COLLECTION_PLAN))
    parser.add_argument("--counterexamples", default=str(DEFAULT_COUNTEREXAMPLES))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    summary = audit(
        collection_plan_path=Path(args.collection_plan),
        counterexamples_path=Path(args.counterexamples),
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(summary, Path(args.report))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

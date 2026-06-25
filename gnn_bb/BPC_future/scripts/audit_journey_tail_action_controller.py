#!/usr/bin/env python3
"""Audit Journey Tail Action Controller decisions from solver JSONL logs."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_tail_action_controller_audit_20260623")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260623_bpc_future_journey_tail_action_controller_audit_zh.md"
)


ROW_FIELDS = [
    "log_file",
    "time",
    "node_id",
    "depth",
    "cg_iter",
    "pricing_kind",
    "pricing_status",
    "pricing_reason",
    "valid",
    "reason",
    "rmp_objective",
    "incumbent",
    "rmp_to_incumbent_gap",
    "tail_action",
    "tail_action_class",
    "tail_action_reason",
    "tail_action_productivity_class",
    "fathom_possible_if_rc_zero",
    "recent_active_support_additions",
    "recent_rmp_objective_progress",
    "recent_true_rc_productivity",
    "global_remaining_rc_lb",
    "corrected_node_lb",
    "frontier_fathom_rc_target",
    "frontier_critical_token_count",
    "frontier_floor_multiplicity",
    "frontier_floor_band_count_0_1",
    "frontier_floor_band_count_1",
    "frontier_floor_band_count_5",
    "frontier_floor_band_count_10",
    "frontier_target_band_count",
    "frontier_region_count",
    "frontier_micro_expansion_attempted",
    "frontier_micro_expansion_expanded",
    "frontier_micro_expansion_children",
    "frontier_micro_expansion_reason",
]


EARLY_BRANCH_FIELDS = [
    "log_file",
    "time",
    "node_id",
    "depth",
    "cg_iter",
    "trigger",
    "tail_action",
    "tail_action_class",
    "tail_action_productivity_class",
    "tail_action_no_column",
    "reason",
    "added_journeys",
    "inherited_lower_bound",
    "rmp_objective",
    "rmp_to_incumbent_gap",
    "recent_active_support_additions",
    "recent_rmp_objective_progress",
    "recent_true_rc_productivity",
    "previous_status",
    "previous_reason",
    "previous_pricing_state",
    "previous_best_reduced_cost",
    "remaining",
    "certificate_candidate",
    "no_column_branch_task_i",
    "no_column_branch_task_j",
    "no_column_branch_pool_same_allowed",
    "no_column_branch_pool_separate_allowed",
    "no_column_branch_pool_max_child_width",
    "no_column_branch_pool_total_child_width",
    "no_column_branch_pool_balance_gap",
    "no_column_branch_width_guard_reason",
    "exact_bound_available",
    "child_lower_bound_exact",
    "queued_child_count",
    "queued_child_ids",
    "queued_child_lower_bound_exact_count",
    "queued_child_nonexact_count",
    "queued_child_min_allowed_current_journeys",
    "queued_child_max_allowed_current_journeys",
    "queued_child_min_queue_priority_width",
    "queued_child_max_queue_priority_width",
    "observed_child_audit_count",
    "observed_child_actions",
    "observed_child_pricing_kinds",
    "child_direct_started_count",
    "child_direct_unstarted_count",
    "child_first_start_delay",
    "child_subtree_node_count",
    "child_subtree_node_start_count",
    "child_subtree_max_depth",
    "child_subtree_pricing_event_count",
    "child_subtree_negative_pricing_event_count",
    "child_subtree_completion_retry_count",
    "child_subtree_completion_retry_pricing_event_count",
    "child_subtree_completion_retry_low_min_fill_count",
    "child_subtree_completion_retry_min_harvest_min_fill",
    "child_subtree_completion_retry_max_harvest_min_fill",
    "child_subtree_completion_retry_harvest_min_fill_values",
    "child_subtree_completion_retry_found_negative_count",
    "child_subtree_completion_retry_certified_no_negative_count",
    "child_subtree_completion_retry_incomplete_count",
    "child_subtree_early_branch_trigger_count",
    "child_subtree_no_column_early_branch_trigger_count",
    "child_subtree_tail_action_audit_count",
    "child_subtree_last_event_time",
    "child_subtree_observed_wall_span",
]

NO_COLUMN_GATE_FIELDS = [
    "log_file",
    "time",
    "node_id",
    "depth",
    "cg_iter",
    "gate_passed",
    "gate_reason",
    "tail_action",
    "tail_action_class",
    "tail_action_reason",
    "tail_action_productivity_class",
    "tail_action_before_final_probe",
    "rmp_objective",
    "inherited_lower_bound",
    "rmp_to_incumbent_gap",
    "fathom_possible_if_rc_zero",
    "recent_active_support_additions",
    "recent_rmp_objective_progress",
    "recent_true_rc_productivity",
    "previous_status",
    "previous_reason",
    "previous_pricing_state",
    "previous_best_reduced_cost",
    "remaining",
    "certificate_candidate",
    "no_column_branch_task_i",
    "no_column_branch_task_j",
    "no_column_branch_pool_same_allowed",
    "no_column_branch_pool_separate_allowed",
    "no_column_branch_pool_max_child_width",
    "no_column_branch_pool_total_child_width",
    "no_column_branch_pool_balance_gap",
    "no_column_branch_width_guard_reason",
    "exact_bound_available",
    "child_lower_bound_exact",
]


def _iter_jsonl(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_file() and path.suffix == ".jsonl":
            yield path
        elif path.is_dir():
            yield from sorted(path.rglob("*.jsonl"))


def _read_events(path: Path) -> Iterable[dict[str, Any]]:
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            yield record


def _tail_action_class_from_action(action: Any) -> str:
    return {
        "FRONTIER_REFINEMENT": "A_FRONTIER_REFINEMENT",
        "BROAD_PLATEAU_FALLBACK": "B_BROAD_PLATEAU",
        "CONTINUE_COLUMN_GENERATION": "C_CONTINUE_CG",
        "EARLY_BRANCH": "D_EARLY_BRANCH",
    }.get(str(action or ""), "UNKNOWN")


def _fill_tail_action_derived_fields(row: dict[str, Any]) -> dict[str, Any]:
    if not row.get("tail_action_class"):
        row["tail_action_class"] = _tail_action_class_from_action(row.get("tail_action"))
    if not row.get("tail_action_productivity_class"):
        row["tail_action_productivity_class"] = "unknown"
    return row


def _tail_action_row(path: Path, record: dict[str, Any]) -> dict[str, Any] | None:
    if record.get("event") != "journey_corrected_node_bound_audit":
        return None
    row = {"log_file": str(path)}
    for key in ROW_FIELDS:
        if key == "log_file":
            continue
        row[key] = record.get(key)
    return _fill_tail_action_derived_fields(row)


def _early_branch_trigger_row(path: Path, record: dict[str, Any]) -> dict[str, Any] | None:
    if record.get("event") != "journey_early_branch_trigger":
        return None
    row = {"log_file": str(path)}
    for key in EARLY_BRANCH_FIELDS:
        if key == "log_file":
            continue
        row[key] = record.get(key)
    return _fill_tail_action_derived_fields(row)


def _no_column_gate_row(path: Path, record: dict[str, Any]) -> dict[str, Any] | None:
    if record.get("event") != "journey_tail_action_no_column_early_branch_gate":
        return None
    row = {"log_file": str(path)}
    for key in NO_COLUMN_GATE_FIELDS:
        if key == "log_file":
            continue
        row[key] = record.get(key)
    return _fill_tail_action_derived_fields(row)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ROW_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in ROW_FIELDS})


def _write_early_branch_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EARLY_BRANCH_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in EARLY_BRANCH_FIELDS})


def _write_no_column_gate_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=NO_COLUMN_GATE_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in NO_COLUMN_GATE_FIELDS})


def _child_queue_summary(children: list[dict[str, Any]]) -> dict[str, Any]:
    child_ids = [
        str(child.get("child_node_id"))
        for child in children
        if child.get("child_node_id") is not None
    ]
    exact_flags = [bool(child.get("lower_bound_exact")) for child in children]
    allowed = [
        int(child.get("allowed_current_journeys"))
        for child in children
        if child.get("allowed_current_journeys") is not None
    ]
    queue_priorities = [
        int(child.get("queue_priority_width"))
        for child in children
        if child.get("queue_priority_width") is not None
    ]
    return {
        "queued_child_count": len(children),
        "queued_child_ids": ",".join(child_ids),
        "queued_child_lower_bound_exact_count": sum(1 for flag in exact_flags if flag),
        "queued_child_nonexact_count": sum(1 for flag in exact_flags if not flag),
        "queued_child_min_allowed_current_journeys": min(allowed) if allowed else None,
        "queued_child_max_allowed_current_journeys": max(allowed) if allowed else None,
        "queued_child_min_queue_priority_width": min(queue_priorities) if queue_priorities else None,
        "queued_child_max_queue_priority_width": max(queue_priorities) if queue_priorities else None,
    }


def _observed_child_summary(
    children: list[dict[str, Any]],
    audit_rows_by_node: dict[tuple[str, int], list[dict[str, Any]]],
) -> dict[str, Any]:
    observed_rows: list[dict[str, Any]] = []
    actions: Counter[str] = Counter()
    pricing_kinds: Counter[str] = Counter()
    for child in children:
        child_id = child.get("child_node_id")
        if child_id is None:
            continue
        try:
            node_id = int(child_id)
        except (TypeError, ValueError):
            continue
        rows = audit_rows_by_node.get((str(child.get("log_file")), node_id), [])
        if not rows:
            continue
        observed_rows.extend(rows)
        for row in rows:
            actions[str(row.get("tail_action") or "")] += 1
            pricing_kinds[str(row.get("pricing_kind") or "")] += 1
    return {
        "observed_child_audit_count": len(observed_rows),
        "observed_child_actions": ",".join(f"{key}:{value}" for key, value in sorted(actions.items())),
        "observed_child_pricing_kinds": ",".join(
            f"{key}:{value}" for key, value in sorted(pricing_kinds.items())
        ),
    }


def _node_id_from_record(record: dict[str, Any]) -> int | None:
    node_id = record.get("node_id")
    if node_id is None:
        node_id = record.get("child_node_id")
    if node_id is None:
        return None
    try:
        return int(node_id)
    except (TypeError, ValueError):
        return None


def _event_time(record: dict[str, Any]) -> float | None:
    try:
        return float(record.get("time"))
    except (TypeError, ValueError):
        return None


def _pricing_event_has_negative_signal(event: dict[str, Any]) -> bool:
    if str(event.get("pricing_state") or "") == "FOUND_NEGATIVE":
        return True
    best_reduced_cost = event.get("best_reduced_cost")
    if best_reduced_cost is not None:
        try:
            if float(best_reduced_cost) < -1.0e-9:
                return True
        except (TypeError, ValueError):
            pass
    reason = str(event.get("reason") or "")
    if "no_negative" in reason:
        return False
    return "negative_journey" in reason or "weak_negative" in reason


def _is_completion_retry_pricing_event(event: dict[str, Any]) -> bool:
    return (
        event.get("event") == "journey_pricing"
        and str(event.get("pricing_kind") or "").startswith("exact_completion_bound")
    )


def _int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _completion_retry_min_fill_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    values = [
        int(value)
        for value in (_int_or_none(event.get("direct_label_harvest_min_fill")) for event in events)
        if value is not None
    ]
    value_counts = Counter(values)
    pricing_events = [event for event in events if _is_completion_retry_pricing_event(event)]
    found_negative = 0
    certified_no_negative = 0
    incomplete = 0
    for event in pricing_events:
        state = str(event.get("pricing_state") or event.get("status") or "")
        reason = str(event.get("reason") or "")
        negative_journeys = _int_or_none(event.get("negative_journeys")) or 0
        selected_trips = _int_or_none(event.get("selected_trips")) or 0
        if state == "FOUND_NEGATIVE" or negative_journeys > 0 or selected_trips > 0:
            found_negative += 1
        elif (
            state in {"OPTIMAL", "CERTIFIED_NO_NEGATIVE"}
            and bool(event.get("global_certificate") or event.get("global_certificate_capable"))
            and bool(event.get("exhausted"))
        ):
            certified_no_negative += 1
        elif state in {"INCOMPLETE", "INCOMPLETE_LIMIT"} or reason == "time_limit":
            incomplete += 1
    return {
        "child_subtree_completion_retry_pricing_event_count": len(pricing_events),
        "child_subtree_completion_retry_low_min_fill_count": sum(1 for value in values if value < 10),
        "child_subtree_completion_retry_min_harvest_min_fill": min(values) if values else None,
        "child_subtree_completion_retry_max_harvest_min_fill": max(values) if values else None,
        "child_subtree_completion_retry_harvest_min_fill_values": ",".join(
            f"{value}:{count}" for value, count in sorted(value_counts.items())
        ),
        "child_subtree_completion_retry_found_negative_count": int(found_negative),
        "child_subtree_completion_retry_certified_no_negative_count": int(certified_no_negative),
        "child_subtree_completion_retry_incomplete_count": int(incomplete),
    }


def _descendant_node_ids(
    log_file: str,
    roots: list[int],
    child_queued_by_parent: dict[tuple[str, int], list[dict[str, Any]]],
) -> set[int]:
    seen: set[int] = set()
    pending = list(roots)
    while pending:
        node_id = int(pending.pop(0))
        if node_id in seen:
            continue
        seen.add(node_id)
        for child in child_queued_by_parent.get((log_file, node_id), []):
            child_id = child.get("child_node_id")
            if child_id is None:
                continue
            try:
                parsed = int(child_id)
            except (TypeError, ValueError):
                continue
            if parsed not in seen:
                pending.append(parsed)
    return seen


def _subtree_activity_summary(
    trigger_row: dict[str, Any],
    children: list[dict[str, Any]],
    child_queued_by_parent: dict[tuple[str, int], list[dict[str, Any]]],
    events_by_node: dict[tuple[str, int], list[dict[str, Any]]],
    audit_rows_by_node: dict[tuple[str, int], list[dict[str, Any]]],
) -> dict[str, Any]:
    log_file = str(trigger_row.get("log_file"))
    direct_child_ids: list[int] = []
    for child in children:
        child_id = child.get("child_node_id")
        if child_id is None:
            continue
        try:
            direct_child_ids.append(int(child_id))
        except (TypeError, ValueError):
            continue
    subtree_ids = _descendant_node_ids(log_file, direct_child_ids, child_queued_by_parent)
    direct_start_times: list[float] = []
    all_events: list[dict[str, Any]] = []
    depths: list[int] = []
    for node_id in sorted(subtree_ids):
        node_events = events_by_node.get((log_file, int(node_id)), [])
        all_events.extend(node_events)
        for event in node_events:
            if event.get("event") == "journey_node_start":
                time_value = _event_time(event)
                if int(node_id) in direct_child_ids and time_value is not None:
                    direct_start_times.append(time_value)
            if event.get("depth") is not None:
                try:
                    depths.append(int(event.get("depth")))
                except (TypeError, ValueError):
                    pass
        for row in audit_rows_by_node.get((log_file, int(node_id)), []):
            if row.get("depth") is not None:
                try:
                    depths.append(int(row.get("depth")))
                except (TypeError, ValueError):
                    pass
    for child in children:
        if child.get("depth") is not None:
            try:
                depths.append(int(child.get("depth")))
            except (TypeError, ValueError):
                pass
    pricing_events = [event for event in all_events if event.get("event") == "journey_pricing"]
    negative_pricing_events = [
        event
        for event in pricing_events
        if _pricing_event_has_negative_signal(event)
    ]
    completion_retry_events = [
        event
        for event in all_events
        if event.get("event") == "journey_exact_pricing_completion_bound_retry"
        or str(event.get("pricing_kind") or "") == "exact_completion_bound_retry"
    ]
    subtree_early_branch_events = [
        event for event in all_events if event.get("event") == "journey_early_branch_trigger"
    ]
    no_column_subtree_early_branch_events = [
        event for event in subtree_early_branch_events if bool(event.get("tail_action_no_column"))
    ]
    node_start_count = sum(1 for event in all_events if event.get("event") == "journey_node_start")
    audit_count = sum(
        len(audit_rows_by_node.get((log_file, int(node_id)), []))
        for node_id in subtree_ids
    )
    event_times = [
        time_value
        for time_value in (_event_time(event) for event in all_events)
        if time_value is not None
    ]
    trigger_time = _event_time(trigger_row)
    first_start_delay = None
    if direct_start_times and trigger_time is not None:
        first_start_delay = min(direct_start_times) - trigger_time
    observed_span = None
    last_event_time = max(event_times) if event_times else None
    if last_event_time is not None and trigger_time is not None:
        observed_span = last_event_time - trigger_time
    return {
        "child_direct_started_count": len(set(int(node_id) for node_id in direct_child_ids if any(
            event.get("event") == "journey_node_start"
            for event in events_by_node.get((log_file, int(node_id)), [])
        ))),
        "child_direct_unstarted_count": max(
            0,
            len(set(direct_child_ids))
            - len(set(int(node_id) for node_id in direct_child_ids if any(
                event.get("event") == "journey_node_start"
                for event in events_by_node.get((log_file, int(node_id)), [])
            ))),
        ),
        "child_first_start_delay": None if first_start_delay is None else round(float(first_start_delay), 6),
        "child_subtree_node_count": len(subtree_ids),
        "child_subtree_node_start_count": int(node_start_count),
        "child_subtree_max_depth": max(depths) if depths else None,
        "child_subtree_pricing_event_count": len(pricing_events),
        "child_subtree_negative_pricing_event_count": len(negative_pricing_events),
        "child_subtree_completion_retry_count": len(completion_retry_events),
        **_completion_retry_min_fill_summary(completion_retry_events),
        "child_subtree_early_branch_trigger_count": len(subtree_early_branch_events),
        "child_subtree_no_column_early_branch_trigger_count": len(no_column_subtree_early_branch_events),
        "child_subtree_tail_action_audit_count": int(audit_count),
        "child_subtree_last_event_time": None if last_event_time is None else round(float(last_event_time), 6),
        "child_subtree_observed_wall_span": None if observed_span is None else round(float(observed_span), 6),
    }


def audit_tail_actions(
    paths: list[Path],
    output_dir: Path,
    report: Path,
    *,
    sample_limit: int = 20,
) -> dict[str, Any]:
    log_paths = list(_iter_jsonl(paths))
    rows: list[dict[str, Any]] = []
    early_branch_rows: list[dict[str, Any]] = []
    no_column_gate_rows: list[dict[str, Any]] = []
    child_queued_by_parent: dict[tuple[str, int], list[dict[str, Any]]] = {}
    audit_rows_by_node: dict[tuple[str, int], list[dict[str, Any]]] = {}
    events_by_node: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for path in log_paths:
        for record in _read_events(path):
            event_node_id = _node_id_from_record(record)
            if event_node_id is not None:
                events_by_node.setdefault((str(path), int(event_node_id)), []).append(
                    {"log_file": str(path), **record}
                )
            row = _tail_action_row(path, record)
            if row is not None:
                rows.append(row)
                node_id = row.get("node_id")
                if node_id is not None:
                    try:
                        audit_rows_by_node.setdefault((str(path), int(node_id)), []).append(row)
                    except (TypeError, ValueError):
                        pass
            branch_row = _early_branch_trigger_row(path, record)
            if branch_row is not None:
                early_branch_rows.append(branch_row)
            gate_row = _no_column_gate_row(path, record)
            if gate_row is not None:
                no_column_gate_rows.append(gate_row)
            if record.get("event") == "journey_child_queued":
                parent_id = record.get("parent_node_id")
                if parent_id is not None:
                    child_row = {"log_file": str(path), **record}
                    try:
                        child_queued_by_parent.setdefault((str(path), int(parent_id)), []).append(child_row)
                    except (TypeError, ValueError):
                        pass

    for row in early_branch_rows:
        node_id = row.get("node_id")
        children: list[dict[str, Any]] = []
        if node_id is not None:
            try:
                children = child_queued_by_parent.get((str(row.get("log_file")), int(node_id)), [])
            except (TypeError, ValueError):
                children = []
        row.update(_child_queue_summary(children))
        row.update(_observed_child_summary(children, audit_rows_by_node))
        row.update(
            _subtree_activity_summary(
                row,
                children,
                child_queued_by_parent,
                events_by_node,
                audit_rows_by_node,
            )
        )

    action_counts = Counter(str(row.get("tail_action") or "") for row in rows)
    action_class_counts = Counter(str(row.get("tail_action_class") or "") for row in rows)
    reason_counts = Counter(str(row.get("tail_action_reason") or "") for row in rows)
    productivity_class_counts = Counter(
        str(row.get("tail_action_productivity_class") or "") for row in rows
    )
    pricing_kind_counts = Counter(str(row.get("pricing_kind") or "") for row in rows)
    node_counts = Counter(f"depth={row.get('depth')}|node={row.get('node_id')}" for row in rows)
    fathom_possible_count = sum(1 for row in rows if bool(row.get("fathom_possible_if_rc_zero")))
    micro_attempt_rows = [
        row for row in rows
        if int(row.get("frontier_micro_expansion_attempted") or 0) > 0
    ]
    active_support_rows = [
        row for row in rows
        if int(row.get("recent_active_support_additions") or 0) > 0
    ]
    rmp_progress_rows = [
        row for row in rows
        if float(row.get("recent_rmp_objective_progress") or 0.0) > 0.0
    ]
    a_class_rows = [row for row in rows if row.get("tail_action") == "FRONTIER_REFINEMENT"]
    b_class_rows = [row for row in rows if row.get("tail_action") == "BROAD_PLATEAU_FALLBACK"]
    c_class_rows = [row for row in rows if row.get("tail_action") == "CONTINUE_COLUMN_GENERATION"]
    d_class_rows = [row for row in rows if row.get("tail_action") == "EARLY_BRANCH"]
    unknown_rows = [row for row in rows if row.get("tail_action") in (None, "", "UNKNOWN")]
    tail_action_early_branch_rows = [
        row for row in early_branch_rows
        if row.get("trigger") == "tail_action_controller"
    ]
    tail_action_no_column_early_branch_rows = [
        row for row in tail_action_early_branch_rows
        if bool(row.get("tail_action_no_column"))
    ]
    nonexact_branch_rows = [
        row for row in early_branch_rows
        if not bool(row.get("exact_bound_available")) and not bool(row.get("child_lower_bound_exact"))
    ]
    gate_reason_counts = Counter(str(row.get("gate_reason") or "") for row in no_column_gate_rows)
    gate_action_counts = Counter(str(row.get("tail_action") or "") for row in no_column_gate_rows)
    gate_action_class_counts = Counter(str(row.get("tail_action_class") or "") for row in no_column_gate_rows)
    gate_productivity_class_counts = Counter(
        str(row.get("tail_action_productivity_class") or "") for row in no_column_gate_rows
    )
    gate_pricing_state_counts = Counter(
        str(row.get("previous_pricing_state") or "") for row in no_column_gate_rows
    )
    before_final_probe_gate_rows = [
        row for row in no_column_gate_rows if bool(row.get("tail_action_before_final_probe"))
    ]
    before_final_probe_disabled_gate_rows = [
        row for row in before_final_probe_gate_rows
        if row.get("gate_reason") == "before_final_probe_disabled"
    ]
    no_column_gate_d_rows = [
        row for row in no_column_gate_rows if row.get("tail_action") == "EARLY_BRANCH"
    ]
    no_column_gate_before_final_probe_disabled_d_rows = [
        row for row in before_final_probe_disabled_gate_rows
        if row.get("tail_action") == "EARLY_BRANCH"
    ]
    tail_action_child_count = sum(int(row.get("queued_child_count") or 0) for row in tail_action_early_branch_rows)
    tail_action_nonexact_child_count = sum(
        int(row.get("queued_child_nonexact_count") or 0)
        for row in tail_action_early_branch_rows
    )
    observed_tail_action_child_count = sum(
        int(row.get("observed_child_audit_count") or 0)
        for row in tail_action_early_branch_rows
    )
    tail_action_completion_retry_low_min_fill_count = sum(
        int(row.get("child_subtree_completion_retry_low_min_fill_count") or 0)
        for row in tail_action_early_branch_rows
    )
    tail_action_completion_retry_found_negative_count = sum(
        int(row.get("child_subtree_completion_retry_found_negative_count") or 0)
        for row in tail_action_early_branch_rows
    )
    tail_action_completion_retry_certified_no_negative_count = sum(
        int(row.get("child_subtree_completion_retry_certified_no_negative_count") or 0)
        for row in tail_action_early_branch_rows
    )
    tail_action_completion_retry_incomplete_count = sum(
        int(row.get("child_subtree_completion_retry_incomplete_count") or 0)
        for row in tail_action_early_branch_rows
    )
    tail_action_queue_priorities = [
        int(row.get(field))
        for row in tail_action_early_branch_rows
        for field in ("queued_child_min_queue_priority_width", "queued_child_max_queue_priority_width")
        if row.get(field) is not None
    ]
    summary = {
        "schema_version": "journey_tail_action_controller_audit_v2",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "input_paths": [str(path) for path in paths],
        "log_file_count": len(log_paths),
        "row_count": len(rows),
        "tail_action_counts": dict(sorted(action_counts.items())),
        "tail_action_class_counts": dict(sorted(action_class_counts.items())),
        "tail_action_reason_counts": dict(sorted(reason_counts.items())),
        "tail_action_productivity_class_counts": dict(sorted(productivity_class_counts.items())),
        "pricing_kind_counts": dict(sorted(pricing_kind_counts.items())),
        "node_counts": dict(sorted(node_counts.items())),
        "fathom_possible_if_rc_zero_count": int(fathom_possible_count),
        "a_frontier_refinement_count": len(a_class_rows),
        "b_broad_plateau_count": len(b_class_rows),
        "c_continue_cg_count": len(c_class_rows),
        "d_early_branch_count": len(d_class_rows),
        "unknown_action_count": len(unknown_rows),
        "micro_expansion_attempt_row_count": len(micro_attempt_rows),
        "recent_active_support_addition_row_count": len(active_support_rows),
        "recent_rmp_objective_progress_row_count": len(rmp_progress_rows),
        "early_branch_trigger_count": len(early_branch_rows),
        "tail_action_early_branch_trigger_count": len(tail_action_early_branch_rows),
        "tail_action_no_column_early_branch_trigger_count": len(
            tail_action_no_column_early_branch_rows
        ),
        "nonexact_early_branch_trigger_count": len(nonexact_branch_rows),
        "no_column_gate_row_count": len(no_column_gate_rows),
        "no_column_gate_reason_counts": dict(sorted(gate_reason_counts.items())),
        "no_column_gate_tail_action_counts": dict(sorted(gate_action_counts.items())),
        "no_column_gate_tail_action_class_counts": dict(sorted(gate_action_class_counts.items())),
        "no_column_gate_tail_action_productivity_class_counts": dict(
            sorted(gate_productivity_class_counts.items())
        ),
        "no_column_gate_previous_pricing_state_counts": dict(sorted(gate_pricing_state_counts.items())),
        "no_column_gate_before_final_probe_count": len(before_final_probe_gate_rows),
        "no_column_gate_before_final_probe_disabled_count": len(before_final_probe_disabled_gate_rows),
        "no_column_gate_d_early_branch_count": len(no_column_gate_d_rows),
        "no_column_gate_before_final_probe_disabled_d_count": len(
            no_column_gate_before_final_probe_disabled_d_rows
        ),
        "tail_action_queued_child_count": int(tail_action_child_count),
        "tail_action_nonexact_queued_child_count": int(tail_action_nonexact_child_count),
        "tail_action_observed_child_audit_count": int(observed_tail_action_child_count),
        "tail_action_completion_retry_low_min_fill_count": int(
            tail_action_completion_retry_low_min_fill_count
        ),
        "tail_action_completion_retry_found_negative_count": int(
            tail_action_completion_retry_found_negative_count
        ),
        "tail_action_completion_retry_certified_no_negative_count": int(
            tail_action_completion_retry_certified_no_negative_count
        ),
        "tail_action_completion_retry_incomplete_count": int(
            tail_action_completion_retry_incomplete_count
        ),
        "tail_action_child_min_queue_priority_width": (
            min(tail_action_queue_priorities) if tail_action_queue_priorities else None
        ),
        "tail_action_child_max_queue_priority_width": (
            max(tail_action_queue_priorities) if tail_action_queue_priorities else None
        ),
        "rows_jsonl": str(output_dir / "tail_action_rows.jsonl"),
        "rows_csv": str(output_dir / "tail_action_rows.csv"),
        "early_branch_rows_jsonl": str(output_dir / "early_branch_trigger_rows.jsonl"),
        "early_branch_rows_csv": str(output_dir / "early_branch_trigger_rows.csv"),
        "no_column_gate_rows_jsonl": str(output_dir / "no_column_gate_rows.jsonl"),
        "no_column_gate_rows_csv": str(output_dir / "no_column_gate_rows.csv"),
        "sample_rows": rows[:sample_limit],
        "sample_early_branch_rows": early_branch_rows[:sample_limit],
        "sample_no_column_gate_rows": no_column_gate_rows[:sample_limit],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "summary.json", summary)
    _write_jsonl(output_dir / "tail_action_rows.jsonl", rows)
    _write_csv(output_dir / "tail_action_rows.csv", rows)
    _write_jsonl(output_dir / "early_branch_trigger_rows.jsonl", early_branch_rows)
    _write_early_branch_csv(output_dir / "early_branch_trigger_rows.csv", early_branch_rows)
    _write_jsonl(output_dir / "no_column_gate_rows.jsonl", no_column_gate_rows)
    _write_no_column_gate_csv(output_dir / "no_column_gate_rows.csv", no_column_gate_rows)
    _write_report(report, summary)
    return summary


def _write_report(report: Path, summary: dict[str, Any]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Journey Tail Action Controller 审计",
        "",
        "## 元信息",
        "",
        f"- diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"- runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"- certificate_effect = {str(summary['certificate_effect']).lower()}",
        f"- official_bound_effect = {str(summary['official_bound_effect']).lower()}",
        f"- log_file_count = {summary['log_file_count']}",
        f"- row_count = {summary['row_count']}",
        "",
        "## Tail Action Counts",
        "",
    ]
    for action, count in summary["tail_action_counts"].items():
        lines.append(f"- `{action}`: {count}")
    if summary.get("tail_action_class_counts"):
        lines.extend(["", "## Tail Action Classes", ""])
        for action_class, count in summary["tail_action_class_counts"].items():
            lines.append(f"- `{action_class}`: {count}")
    if summary.get("tail_action_productivity_class_counts"):
        lines.extend(["", "## Tail Action Productivity Classes", ""])
        for productivity_class, count in summary["tail_action_productivity_class_counts"].items():
            lines.append(f"- `{productivity_class}`: {count}")
    lines.extend(
        [
            "",
            "## 关键计数",
            "",
            f"- A/frontier refinement: {summary['a_frontier_refinement_count']}",
            f"- B/broad plateau: {summary['b_broad_plateau_count']}",
            f"- C/continue CG: {summary['c_continue_cg_count']}",
            f"- D/early branch: {summary['d_early_branch_count']}",
            f"- unknown action: {summary['unknown_action_count']}",
            f"- fathom_possible_if_rc_zero: {summary['fathom_possible_if_rc_zero_count']}",
            f"- micro expansion attempted rows: {summary['micro_expansion_attempt_row_count']}",
            f"- recent active-support addition rows: {summary['recent_active_support_addition_row_count']}",
            f"- recent RMP objective progress rows: {summary['recent_rmp_objective_progress_row_count']}",
            f"- early branch triggers: {summary['early_branch_trigger_count']}",
            f"- tail-action early branch triggers: {summary['tail_action_early_branch_trigger_count']}",
            f"- tail-action no-column early branch triggers: {summary['tail_action_no_column_early_branch_trigger_count']}",
            f"- non-exact early branch triggers: {summary['nonexact_early_branch_trigger_count']}",
            f"- no-column gate rows: {summary['no_column_gate_row_count']}",
            f"- no-column before-final-probe gate rows: {summary['no_column_gate_before_final_probe_count']}",
            f"- no-column before-final-probe disabled rows: {summary['no_column_gate_before_final_probe_disabled_count']}",
            f"- no-column gate D/early-branch rows: {summary['no_column_gate_d_early_branch_count']}",
            f"- no-column before-final-probe disabled D rows: {summary['no_column_gate_before_final_probe_disabled_d_count']}",
            f"- tail-action queued children: {summary['tail_action_queued_child_count']}",
            f"- tail-action non-exact queued children: {summary['tail_action_nonexact_queued_child_count']}",
            f"- observed tail-action child audit rows: {summary['tail_action_observed_child_audit_count']}",
            f"- tail-action low min-fill completion retries: {summary['tail_action_completion_retry_low_min_fill_count']}",
            f"- tail-action completion retry found-negative rows: {summary['tail_action_completion_retry_found_negative_count']}",
            f"- tail-action completion retry certified no-negative rows: {summary['tail_action_completion_retry_certified_no_negative_count']}",
            f"- tail-action completion retry incomplete rows: {summary['tail_action_completion_retry_incomplete_count']}",
            f"- tail-action child min queue priority width: {summary['tail_action_child_min_queue_priority_width']}",
            f"- tail-action child max queue priority width: {summary['tail_action_child_max_queue_priority_width']}",
            "",
            "## 输出",
            "",
            f"- summary: `{summary.get('rows_jsonl', '')}` 的同目录 `summary.json`",
            f"- rows jsonl: `{summary['rows_jsonl']}`",
            f"- rows csv: `{summary['rows_csv']}`",
            f"- early branch rows jsonl: `{summary['early_branch_rows_jsonl']}`",
            f"- early branch rows csv: `{summary['early_branch_rows_csv']}`",
            f"- no-column gate rows jsonl: `{summary['no_column_gate_rows_jsonl']}`",
            f"- no-column gate rows csv: `{summary['no_column_gate_rows_csv']}`",
            "",
        ]
    )
    if summary.get("no_column_gate_reason_counts"):
        lines.extend(["## No-column Gate Counts", ""])
        lines.append("按 gate_reason:")
        for reason, count in summary["no_column_gate_reason_counts"].items():
            lines.append(f"- `{reason}`: {count}")
        lines.append("")
        lines.append("按 tail_action:")
        for action, count in summary["no_column_gate_tail_action_counts"].items():
            lines.append(f"- `{action}`: {count}")
        lines.append("")
        if summary.get("no_column_gate_tail_action_class_counts"):
            lines.append("按 tail_action_class:")
            for action_class, count in summary["no_column_gate_tail_action_class_counts"].items():
                lines.append(f"- `{action_class}`: {count}")
            lines.append("")
        if summary.get("no_column_gate_tail_action_productivity_class_counts"):
            lines.append("按 tail_action_productivity_class:")
            for productivity_class, count in summary[
                "no_column_gate_tail_action_productivity_class_counts"
            ].items():
                lines.append(f"- `{productivity_class}`: {count}")
            lines.append("")
    if summary.get("sample_early_branch_rows"):
        lines.extend(
            [
                "## Early Branch Child Activity",
                "",
            ]
        )
        for row in summary.get("sample_early_branch_rows", []):
            lines.append(
                "- "
                f"node={row.get('node_id')} depth={row.get('depth')} cg={row.get('cg_iter')} "
                f"no_column={str(bool(row.get('tail_action_no_column'))).lower()} "
                f"children=`{row.get('queued_child_ids') or ''}` "
                f"started={row.get('child_direct_started_count')}/"
                f"{int(row.get('queued_child_count') or 0)} "
                f"subtree_nodes={row.get('child_subtree_node_count')} "
                f"pricing={row.get('child_subtree_pricing_event_count')} "
                f"negative_pricing={row.get('child_subtree_negative_pricing_event_count')} "
                f"cb_retry={row.get('child_subtree_completion_retry_count')} "
                f"cb_low_min_fill={row.get('child_subtree_completion_retry_low_min_fill_count')} "
                f"cb_min_fill_values=`{row.get('child_subtree_completion_retry_harvest_min_fill_values') or ''}` "
                f"subtree_early_branch={row.get('child_subtree_early_branch_trigger_count')} "
                f"subtree_no_column={row.get('child_subtree_no_column_early_branch_trigger_count')} "
                f"span={row.get('child_subtree_observed_wall_span')}"
            )
        lines.append("")
    report.write_text("\n".join(lines), encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--sample-limit", type=int, default=20)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    audit_tail_actions(
        list(args.paths),
        args.output_dir,
        args.report,
        sample_limit=max(0, int(args.sample_limit)),
    )


if __name__ == "__main__":
    main()

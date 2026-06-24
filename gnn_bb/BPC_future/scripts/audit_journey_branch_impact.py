#!/usr/bin/env python3
"""Audit Journey branch-impact behavior from JSONL solver logs.

The script is diagnostic-only: it reads JSONL logs and summarizes what happens
after each Journey branch.  It does not run BPC, pricing, or RMP.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
import re
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_branch_impact_audit_20260623")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260623_bpc_future_journey_branch_impact_audit_zh.md"
)

_RF_RE = re.compile(r"RF\((?P<i>\d+),(?P<j>\d+)\)=(?P<kind>same_vehicle|separate_vehicle)")

BRANCH_IMPACT_FEATURE_SCHEMA: tuple[str, ...] = (
    "depth",
    "candidate_count",
    "eligible_count",
    "has_candidate_log",
    "branch_rank_in_top",
    "branch_rank_in_priority_top",
    "same_mass",
    "fractionality",
    "support_count",
    "incumbent_relation_known",
    "incumbent_relation_same",
    "incumbent_disagreement",
    "pool_same_allowed",
    "pool_separate_allowed",
    "pool_max_child_width",
    "pool_total_child_width",
    "pool_balance_gap",
)

BRANCH_IMPACT_LABEL_SCHEMA: tuple[str, ...] = (
    "y_tail_improved",
    "y_completion_bound_tail",
    "y_early_branch_continues",
    "y_negative_chain_continues",
    "y_active_touch",
    "y_inactive_only",
    "y_child_negative_pricing_events",
    "y_child_completion_bound_retries",
    "y_child_early_branch_triggers",
)


def _iter_jsonl(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_file() and path.suffix == ".jsonl":
            yield path
        elif path.is_dir():
            yield from sorted(path.rglob("*.jsonl"))


def _read_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            events.append(record)
    return events


def _float(record: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = record.get(key, default)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(record: dict[str, Any], key: str, default: int = 0) -> int:
    value = record.get(key, default)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_rf(text: Any) -> dict[str, Any] | None:
    if not isinstance(text, str):
        return None
    match = _RF_RE.search(text)
    if match is None:
        return None
    return {
        "task_i": int(match.group("i")),
        "task_j": int(match.group("j")),
        "kind": match.group("kind"),
    }


def _branch_pair(record: dict[str, Any]) -> tuple[int, int] | None:
    parsed = _parse_rf(record.get("left")) or _parse_rf(record.get("right"))
    if parsed is None:
        return None
    return tuple(sorted((int(parsed["task_i"]), int(parsed["task_j"]))))


def _candidate_payload(candidate: Any) -> dict[str, Any] | None:
    if not isinstance(candidate, dict):
        return None
    keys = [
        "task_i",
        "task_j",
        "same_mass",
        "fractionality",
        "support_count",
        "incumbent_relation",
        "incumbent_disagreement",
        "pool_same_allowed",
        "pool_separate_allowed",
        "pool_max_child_width",
        "pool_total_child_width",
        "pool_balance_gap",
    ]
    return {key: candidate.get(key) for key in keys if key in candidate}


def _candidate_matches_branch(candidate: Any, branch: dict[str, Any]) -> bool | None:
    if not isinstance(candidate, dict):
        return None
    pair = _branch_pair(branch)
    if pair is None:
        return None
    if "task_i" not in candidate or "task_j" not in candidate:
        return None
    candidate_pair = tuple(sorted((int(candidate["task_i"]), int(candidate["task_j"]))))
    return candidate_pair == pair


def _candidate_for_branch(candidate_log: dict[str, Any] | None, branch: dict[str, Any]) -> dict[str, Any] | None:
    if candidate_log is None:
        return None
    selected = candidate_log.get("selected")
    if _candidate_matches_branch(selected, branch):
        payload = _candidate_payload(selected)
        if payload is not None:
            return payload
    for key in ("priority_top", "top"):
        for candidate in candidate_log.get(key, []):
            if _candidate_matches_branch(candidate, branch):
                payload = _candidate_payload(candidate)
                if payload is not None:
                    return payload
    return None


def _branch_rank(candidates: Any, branch: dict[str, Any]) -> int | None:
    if not isinstance(candidates, list):
        return None
    for index, candidate in enumerate(candidates):
        if _candidate_matches_branch(candidate, branch):
            return index
    return None


def _find_candidate_log(
    events: list[dict[str, Any]],
    branch_index: int,
    branch: dict[str, Any],
) -> dict[str, Any] | None:
    branch_node_id = branch.get("node_id")
    branch_depth = branch.get("depth")
    for record in reversed(events[:branch_index]):
        if record.get("event") != "journey_branch_candidates":
            continue
        if record.get("node_id") != branch_node_id:
            continue
        if record.get("depth") != branch_depth:
            continue
        return record
    return None


def _is_negative_pricing(record: dict[str, Any]) -> bool:
    return (
        _int(record, "negative_journeys") > 0
        or _int(record, "selected_trips") > 0
        or str(record.get("pricing_state") or "") == "FOUND_NEGATIVE"
        or _float(record, "best_reduced_cost", 0.0) < -1.0e-9
    )


def _is_completion_bound_retry(record: dict[str, Any]) -> bool:
    event = str(record.get("event") or "")
    pricing_kind = str(record.get("pricing_kind") or "")
    return (
        event in {"journey_exact_pricing_completion_bound_retry", "journey_exact_pricing_retry"}
        or pricing_kind.startswith("exact_completion_bound")
    )


def _summarize_child(
    child: dict[str, Any],
    by_node: dict[int, list[dict[str, Any]]],
) -> dict[str, Any]:
    child_id = _int(child, "child_node_id", -1)
    node_events = by_node.get(child_id, [])
    node_start = next((record for record in node_events if record.get("event") == "journey_node_start"), None)
    pricing_events = [record for record in node_events if record.get("event") == "journey_pricing"]
    addition_events = [record for record in node_events if record.get("event") == "journey_column_addition"]
    incomplete = next(
        (record for record in reversed(node_events) if record.get("event") == "journey_node_incomplete"),
        None,
    )
    start_time = _float(node_start or child, "time", 0.0)
    last_time = max((_float(record, "time", start_time) for record in node_events), default=start_time)
    best_values = [
        _float(record, "best_reduced_cost")
        for record in pricing_events
        if record.get("best_reduced_cost") is not None
    ]
    productivity_counts = Counter(
        str(record.get("addition_productivity_class") or "unknown")
        for record in addition_events
    )
    return {
        "child_node_id": child_id,
        "constraint": child.get("constraint"),
        "constraint_kind": None if _parse_rf(child.get("constraint")) is None else _parse_rf(child.get("constraint"))["kind"],
        "branch_same_mass": child.get("branch_same_mass"),
        "depth": child.get("depth"),
        "allowed_current_journeys": child.get("allowed_current_journeys"),
        "lower_bound": child.get("lower_bound"),
        "lower_bound_exact": child.get("lower_bound_exact"),
        "started": node_start is not None,
        "start_time": round(start_time, 6),
        "last_time": round(last_time, 6),
        "time_span": round(max(0.0, last_time - start_time), 6),
        "pricing_event_count": len(pricing_events),
        "negative_pricing_event_count": sum(1 for record in pricing_events if _is_negative_pricing(record)),
        "negative_journeys_total": int(sum(_int(record, "negative_journeys") for record in pricing_events)),
        "selected_trips_total": int(sum(_int(record, "selected_trips") for record in pricing_events)),
        "min_best_reduced_cost": None if not best_values else round(min(best_values), 9),
        "column_addition_count": len(addition_events),
        "added_journeys": int(sum(_int(record, "added_journeys") for record in addition_events)),
        "new_journeys": int(sum(_int(record, "new_journeys") for record in addition_events)),
        "replacement_journeys": int(sum(_int(record, "replacement_journeys") for record in addition_events)),
        "active_new_task_set_count": int(
            sum(_int(record, "active_new_task_set_count") for record in addition_events)
        ),
        "active_replacement_task_set_count": int(
            sum(_int(record, "active_replacement_task_set_count") for record in addition_events)
        ),
        "inactive_changed_task_set_count": int(
            sum(_int(record, "inactive_changed_task_set_count") for record in addition_events)
        ),
        "addition_productivity_class_counts": dict(sorted(productivity_counts.items())),
        "completion_bound_retry_count": sum(1 for record in node_events if _is_completion_bound_retry(record)),
        "early_branch_trigger_count": sum(
            1 for record in node_events if record.get("event") == "journey_early_branch_trigger"
        ),
        "branch_triggered": any(record.get("event") == "journey_branch" for record in node_events),
        "node_incomplete_reason": None if incomplete is None else incomplete.get("reason"),
    }


def _tail_class(children: list[dict[str, Any]]) -> str:
    if not children:
        return "no_children_logged"
    processed = [child for child in children if bool(child.get("started"))]
    if any(int(child.get("completion_bound_retry_count") or 0) > 0 for child in processed):
        return "completion_bound_tail"
    if any(int(child.get("early_branch_trigger_count") or 0) > 0 for child in processed):
        return "early_branch_continues"
    if any(int(child.get("negative_pricing_event_count") or 0) > 0 for child in processed):
        return "negative_chain_continues"
    if any(child.get("node_incomplete_reason") for child in processed):
        return "node_incomplete_tail"
    if any(not bool(child.get("started")) for child in children):
        return "unprocessed_children"
    return "no_negative_or_unknown"


def _summarize_branch(
    path: Path,
    events: list[dict[str, Any]],
    branch_index: int,
    branch: dict[str, Any],
    children_by_parent: dict[int, list[dict[str, Any]]],
    by_node: dict[int, list[dict[str, Any]]],
    *,
    run_status: str,
    log_has_finish: bool,
    run_end_time: float,
) -> dict[str, Any]:
    branch_node_id = _int(branch, "node_id", -1)
    candidate_log = _find_candidate_log(events, branch_index, branch)
    branch_time = _float(branch, "time", 0.0)
    children = [
        _summarize_child(child, by_node)
        for child in children_by_parent.get(branch_node_id, [])
        if child.get("time", 0.0) >= branch_time
    ]
    started_children = [child for child in children if bool(child.get("started"))]
    first_started_child = min(
        started_children,
        key=lambda child: float(child.get("start_time") or 0.0),
        default=None,
    )
    selected = None if candidate_log is None else _candidate_payload(candidate_log.get("selected"))
    observed_candidate = _candidate_for_branch(candidate_log, branch)
    priority_top = [] if candidate_log is None else [
        payload for payload in (_candidate_payload(candidate) for candidate in candidate_log.get("priority_top", [])) if payload
    ]
    top = [] if candidate_log is None else [
        payload for payload in (_candidate_payload(candidate) for candidate in candidate_log.get("top", [])) if payload
    ]
    left = _parse_rf(branch.get("left"))
    right = _parse_rf(branch.get("right"))
    child_widths = [
        int(child["allowed_current_journeys"])
        for child in children
        if child.get("allowed_current_journeys") is not None
    ]
    unprocessed_child_count = len(children) - len(started_children)
    label_observation_complete = (
        bool(log_has_finish)
        and str(run_status) == "OPTIMAL"
        and int(unprocessed_child_count) <= 0
    )
    right_censored = not bool(label_observation_complete)
    row = {
        "log_file": str(path),
        "run_status": str(run_status),
        "log_has_finish": bool(log_has_finish),
        "log_end_time": round(float(run_end_time), 6),
        "branch_node_id": branch_node_id,
        "depth": branch.get("depth"),
        "branch_time": round(float(branch_time), 6),
        "branch_observation_window": round(max(0.0, float(run_end_time) - float(branch_time)), 6),
        "left": branch.get("left"),
        "right": branch.get("right"),
        "task_i": None if left is None else left["task_i"],
        "task_j": None if left is None else left["task_j"],
        "child_lower_bound_exact": all(bool(child.get("lower_bound_exact")) for child in children) if children else False,
        "exact_bound_available": bool(branch.get("lower_bound_exact", False)),
        "candidate_count": None if candidate_log is None else candidate_log.get("candidate_count"),
        "eligible_count": None if candidate_log is None else candidate_log.get("eligible_count"),
        "priority_mode": None if candidate_log is None else candidate_log.get("priority_mode"),
        "forced_pair": None if candidate_log is None else candidate_log.get("forced_pair"),
        "forced_pair_matched": None if candidate_log is None else candidate_log.get("forced_pair_matched"),
        "selected": selected,
        "observed_branch_candidate": observed_candidate,
        "selected_matches_branch": None
        if candidate_log is None
        else _candidate_matches_branch(candidate_log.get("selected"), branch),
        "branch_rank_in_top": None if candidate_log is None else _branch_rank(candidate_log.get("top"), branch),
        "branch_rank_in_priority_top": None
        if candidate_log is None
        else _branch_rank(candidate_log.get("priority_top"), branch),
        "top": top,
        "priority_top": priority_top,
        "processed_child_count": len(started_children),
        "unprocessed_child_count": int(unprocessed_child_count),
        "child_count": len(children),
        "all_children_started": bool(children and int(unprocessed_child_count) <= 0),
        "right_censored": bool(right_censored),
        "label_observation_complete": bool(label_observation_complete),
        "min_child_allowed_current_journeys": min(child_widths) if child_widths else None,
        "max_child_allowed_current_journeys": max(child_widths) if child_widths else None,
        "sum_child_negative_pricing_event_count": int(
            sum(int(child.get("negative_pricing_event_count") or 0) for child in children)
        ),
        "sum_child_column_additions": int(
            sum(int(child.get("column_addition_count") or 0) for child in children)
        ),
        "sum_child_added_journeys": int(sum(int(child.get("added_journeys") or 0) for child in children)),
        "sum_child_active_new_task_set_count": int(
            sum(int(child.get("active_new_task_set_count") or 0) for child in children)
        ),
        "sum_child_active_replacement_task_set_count": int(
            sum(int(child.get("active_replacement_task_set_count") or 0) for child in children)
        ),
        "sum_child_inactive_changed_task_set_count": int(
            sum(int(child.get("inactive_changed_task_set_count") or 0) for child in children)
        ),
        "sum_child_completion_bound_retry_count": int(
            sum(int(child.get("completion_bound_retry_count") or 0) for child in children)
        ),
        "sum_child_early_branch_trigger_count": int(
            sum(int(child.get("early_branch_trigger_count") or 0) for child in children)
        ),
        "first_started_child_node_id": None if first_started_child is None else first_started_child["child_node_id"],
        "first_child_allowed_current_journeys": None
        if first_started_child is None
        else first_started_child.get("allowed_current_journeys"),
        "first_child_negative_pricing_event_count": None
        if first_started_child is None
        else first_started_child.get("negative_pricing_event_count"),
        "first_child_column_additions": None
        if first_started_child is None
        else first_started_child.get("column_addition_count"),
        "first_child_completion_bound_retry_count": None
        if first_started_child is None
        else first_started_child.get("completion_bound_retry_count"),
        "first_child_early_branch_trigger_count": None
        if first_started_child is None
        else first_started_child.get("early_branch_trigger_count"),
        "first_child_time_span": None if first_started_child is None else first_started_child.get("time_span"),
        "tail_class": _tail_class(children),
        "children": children,
        "right_kind": None if right is None else right["kind"],
    }
    feature_source = "candidate_log" if observed_candidate is not None else "child_width_fallback"
    row["branch_feature_source"] = feature_source
    row["usable_for_branch_impact_training"] = bool(
        row["label_observation_complete"] and feature_source == "candidate_log"
    )
    row["branch_feature_vector"] = _branch_feature_vector(row, observed_candidate)
    row["branch_labels"] = _branch_labels(row)
    return row


def _branch_feature_vector(
    row: dict[str, Any],
    observed_candidate: dict[str, Any] | None,
) -> list[float]:
    candidate = observed_candidate or _fallback_candidate_from_children(row)
    relation = candidate.get("incumbent_relation") if candidate else None
    features = {
        "depth": _number(row.get("depth")),
        "candidate_count": _number(row.get("candidate_count")),
        "eligible_count": _number(row.get("eligible_count")),
        "has_candidate_log": 1.0 if row.get("candidate_count") is not None else 0.0,
        "branch_rank_in_top": _rank_feature(row.get("branch_rank_in_top")),
        "branch_rank_in_priority_top": _rank_feature(row.get("branch_rank_in_priority_top")),
        "same_mass": _number(None if candidate is None else candidate.get("same_mass")),
        "fractionality": _number(None if candidate is None else candidate.get("fractionality")),
        "support_count": _number(None if candidate is None else candidate.get("support_count")),
        "incumbent_relation_known": 1.0 if relation is not None else 0.0,
        "incumbent_relation_same": 1.0 if relation is True else 0.0,
        "incumbent_disagreement": _number(None if candidate is None else candidate.get("incumbent_disagreement")),
        "pool_same_allowed": _number(None if candidate is None else candidate.get("pool_same_allowed")),
        "pool_separate_allowed": _number(None if candidate is None else candidate.get("pool_separate_allowed")),
        "pool_max_child_width": _number(None if candidate is None else candidate.get("pool_max_child_width")),
        "pool_total_child_width": _number(None if candidate is None else candidate.get("pool_total_child_width")),
        "pool_balance_gap": _number(None if candidate is None else candidate.get("pool_balance_gap")),
    }
    return [float(features[name]) for name in BRANCH_IMPACT_FEATURE_SCHEMA]


def _fallback_candidate_from_children(row: dict[str, Any]) -> dict[str, Any] | None:
    children = row.get("children") or []
    if not isinstance(children, list) or not children:
        return None
    same_allowed: int | None = None
    separate_allowed: int | None = None
    same_mass: float | None = None
    for child in children:
        if not isinstance(child, dict):
            continue
        if child.get("branch_same_mass") is not None and same_mass is None:
            same_mass = _number(child.get("branch_same_mass"))
        if child.get("constraint_kind") == "same_vehicle":
            same_allowed = _optional_int(child.get("allowed_current_journeys"))
        if child.get("constraint_kind") == "separate_vehicle":
            separate_allowed = _optional_int(child.get("allowed_current_journeys"))
    widths = [width for width in (same_allowed, separate_allowed) if width is not None]
    if not widths:
        return None
    if same_mass is None:
        same_mass = 0.0
    return {
        "same_mass": float(same_mass),
        "fractionality": abs(float(same_mass) - round(float(same_mass))),
        "support_count": 0,
        "incumbent_relation": None,
        "incumbent_disagreement": 0.0,
        "pool_same_allowed": same_allowed,
        "pool_separate_allowed": separate_allowed,
        "pool_max_child_width": max(widths),
        "pool_total_child_width": sum(widths),
        "pool_balance_gap": abs(int((same_allowed or 0) - (separate_allowed or 0)))
        if same_allowed is not None and separate_allowed is not None
        else 0,
    }


def _branch_labels(row: dict[str, Any]) -> dict[str, float]:
    tail_class = str(row.get("tail_class") or "")
    active_touch_count = int(row.get("sum_child_active_new_task_set_count") or 0) + int(
        row.get("sum_child_active_replacement_task_set_count") or 0
    )
    inactive_count = int(row.get("sum_child_inactive_changed_task_set_count") or 0)
    labels = {
        "y_tail_improved": 1.0 if tail_class == "no_negative_or_unknown" and active_touch_count > 0 else 0.0,
        "y_completion_bound_tail": 1.0 if tail_class == "completion_bound_tail" else 0.0,
        "y_early_branch_continues": 1.0 if tail_class == "early_branch_continues" else 0.0,
        "y_negative_chain_continues": 1.0 if tail_class == "negative_chain_continues" else 0.0,
        "y_active_touch": 1.0 if active_touch_count > 0 else 0.0,
        "y_inactive_only": 1.0 if inactive_count > 0 and active_touch_count == 0 else 0.0,
        "y_child_negative_pricing_events": float(row.get("sum_child_negative_pricing_event_count") or 0),
        "y_child_completion_bound_retries": float(row.get("sum_child_completion_bound_retry_count") or 0),
        "y_child_early_branch_triggers": float(row.get("sum_child_early_branch_trigger_count") or 0),
    }
    return {name: float(labels[name]) for name in BRANCH_IMPACT_LABEL_SCHEMA}


def _training_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "journey_branch_impact_training_row_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "log_file": row.get("log_file"),
        "branch_node_id": row.get("branch_node_id"),
        "depth": row.get("depth"),
        "task_i": row.get("task_i"),
        "task_j": row.get("task_j"),
        "branch_feature_source": row.get("branch_feature_source"),
        "forced_pair": row.get("forced_pair"),
        "forced_pair_matched": row.get("forced_pair_matched"),
        "run_status": row.get("run_status"),
        "right_censored": bool(row.get("right_censored")),
        "label_observation_complete": bool(row.get("label_observation_complete")),
        "usable_for_branch_impact_training": bool(row.get("usable_for_branch_impact_training")),
        "branch_feature_schema": list(BRANCH_IMPACT_FEATURE_SCHEMA),
        "branch_features": row.get("branch_feature_vector"),
        "branch_label_schema": list(BRANCH_IMPACT_LABEL_SCHEMA),
        "branch_labels": row.get("branch_labels"),
        "tail_class": row.get("tail_class"),
    }


def _number(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return float(default)
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float(default)
    if result != result:
        return float(default)
    return float(result)


def _rank_feature(value: Any) -> float:
    if value is None:
        return -1.0
    return _number(value, -1.0)


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _summarize_log(path: Path) -> list[dict[str, Any]]:
    events = _read_events(path)
    finish_events = [record for record in events if record.get("event") == "finish"]
    log_has_finish = bool(finish_events)
    run_status = str(finish_events[-1].get("status") or "UNKNOWN") if finish_events else "NO_FINISH"
    run_end_time = max((_float(record, "time", 0.0) for record in events), default=0.0)
    by_node: dict[int, list[dict[str, Any]]] = {}
    children_by_parent: dict[int, list[dict[str, Any]]] = {}
    for record in events:
        node_id = record.get("node_id")
        if isinstance(node_id, int):
            by_node.setdefault(node_id, []).append(record)
        if record.get("event") == "journey_child_queued":
            parent = record.get("parent_node_id")
            if isinstance(parent, int):
                children_by_parent.setdefault(parent, []).append(record)
    rows: list[dict[str, Any]] = []
    for index, record in enumerate(events):
        if record.get("event") == "journey_branch":
            rows.append(
                _summarize_branch(
                    path,
                    events,
                    index,
                    record,
                    children_by_parent,
                    by_node,
                    run_status=run_status,
                    log_has_finish=log_has_finish,
                    run_end_time=run_end_time,
                )
            )
    return rows


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tail_class_counts = Counter(str(row.get("tail_class") or "") for row in rows)
    priority_mode_counts = Counter(str(row.get("priority_mode") or "not_logged") for row in rows)
    selected_match_rows = [row for row in rows if row.get("selected_matches_branch") is True]
    top_contains_branch_rows = [row for row in rows if row.get("branch_rank_in_top") is not None]
    top_first_branch_rows = [row for row in rows if row.get("branch_rank_in_top") == 0]
    priority_top_first_branch_rows = [row for row in rows if row.get("branch_rank_in_priority_top") == 0]
    candidate_log_rows = [row for row in rows if row.get("branch_feature_source") == "candidate_log"]
    forced_pair_rows = [row for row in rows if row.get("forced_pair") is not None]
    forced_pair_matched_rows = [row for row in rows if row.get("forced_pair_matched") is True]
    right_censored_rows = [row for row in rows if bool(row.get("right_censored"))]
    complete_label_rows = [row for row in rows if bool(row.get("label_observation_complete"))]
    usable_training_rows = [row for row in rows if bool(row.get("usable_for_branch_impact_training"))]
    run_status_counts = Counter(str(row.get("run_status") or "UNKNOWN") for row in rows)
    active_touch_rows = [
        row
        for row in rows
        if int(row.get("sum_child_active_new_task_set_count") or 0)
        + int(row.get("sum_child_active_replacement_task_set_count") or 0)
        > 0
    ]
    inactive_only_rows = [
        row
        for row in rows
        if int(row.get("sum_child_inactive_changed_task_set_count") or 0) > 0
        and row not in active_touch_rows
    ]
    return {
        "branch_count": len(rows),
        "tail_class_counts": dict(sorted(tail_class_counts.items())),
        "priority_mode_counts": dict(sorted(priority_mode_counts.items())),
        "selected_match_count": len(selected_match_rows),
        "top_contains_branch_count": len(top_contains_branch_rows),
        "top_first_branch_count": len(top_first_branch_rows),
        "priority_top_first_branch_count": len(priority_top_first_branch_rows),
        "candidate_log_branch_count": len(candidate_log_rows),
        "forced_pair_branch_count": len(forced_pair_rows),
        "forced_pair_matched_branch_count": len(forced_pair_matched_rows),
        "right_censored_branch_count": len(right_censored_rows),
        "complete_label_branch_count": len(complete_label_rows),
        "usable_branch_impact_training_count": len(usable_training_rows),
        "run_status_counts": dict(sorted(run_status_counts.items())),
        "active_touch_branch_count": len(active_touch_rows),
        "inactive_only_branch_count": len(inactive_only_rows),
        "unprocessed_child_count": int(sum(int(row.get("unprocessed_child_count") or 0) for row in rows)),
        "total_child_negative_pricing_events": int(
            sum(int(row.get("sum_child_negative_pricing_event_count") or 0) for row in rows)
        ),
        "total_child_column_additions": int(
            sum(int(row.get("sum_child_column_additions") or 0) for row in rows)
        ),
        "total_child_added_journeys": int(
            sum(int(row.get("sum_child_added_journeys") or 0) for row in rows)
        ),
        "total_child_completion_bound_retries": int(
            sum(int(row.get("sum_child_completion_bound_retry_count") or 0) for row in rows)
        ),
        "total_child_early_branch_triggers": int(
            sum(int(row.get("sum_child_early_branch_trigger_count") or 0) for row in rows)
        ),
        "interpretation": _interpret(rows),
    }


def _interpret(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "没有找到 journey_branch 事件。"
    tail_counts = Counter(str(row.get("tail_class") or "") for row in rows)
    candidate_log_count = sum(1 for row in rows if row.get("branch_feature_source") == "candidate_log")
    usable_count = sum(1 for row in rows if bool(row.get("usable_for_branch_impact_training")))
    right_censored_count = sum(1 for row in rows if bool(row.get("right_censored")))
    if usable_count <= 0:
        if candidate_log_count <= 0:
            return (
                "本批 branch row 没有 branch-candidate feature log，只能使用 child-width fallback；"
                "再加上右删失 row 较多，因此只能做 proof-tail 诊断，不能直接作为 GAT branch-impact 正例训练集。"
            )
        if right_censored_count:
            return (
                "本批 branch row 存在右删失，子树未完整观测；可以做 hard-negative/风险诊断，"
                "但不能把未处理 child 当成稳定 branch-impact 标签。"
            )
    inactive_only = sum(
        1
        for row in rows
        if int(row.get("sum_child_inactive_changed_task_set_count") or 0) > 0
        and int(row.get("sum_child_active_new_task_set_count") or 0)
        + int(row.get("sum_child_active_replacement_task_set_count") or 0)
        == 0
    )
    if tail_counts.get("early_branch_continues", 0) or tail_counts.get("negative_chain_continues", 0):
        return (
            "分支后子节点仍继续发现负列或继续触发 early-branch，说明当前策略只把弱/边界负列尾巴"
            "移动到更深节点，并没有让 GAT 直接学到 branch-impact / active-support / proof-tail 缩短标签。"
        )
    if tail_counts.get("completion_bound_tail", 0):
        return (
            "分支后主要瓶颈进入 completion-bound 证明尾段；GAT 不能替代证书，只能作为候选列发现器，"
            "需要另行优化 exact final judge 或训练能减少证书尾部状态空间的标签。"
        )
    if inactive_only:
        return (
            "分支后的列添加主要停留在 inactive-only 改变；GAT 找到真负列，但没有稳定改变 LP active support。"
        )
    return "分支影响类型混合，需要结合 records 逐条查看。"


def build_branch_impact(paths: list[Path], output_dir: Path, report: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    log_files = list(_iter_jsonl(paths))
    for path in log_files:
        rows.extend(_summarize_log(path))
    training_rows = [_training_row(row) for row in rows]
    summary = {
        "schema_version": "journey_branch_impact_audit_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "input_paths": [str(path) for path in paths],
        "log_count": len(log_files),
        "branch_feature_schema": list(BRANCH_IMPACT_FEATURE_SCHEMA),
        "branch_label_schema": list(BRANCH_IMPACT_LABEL_SCHEMA),
        "branch_training_row_count": len(training_rows),
        "aggregate": _aggregate(rows),
        "records": rows,
        "branch_training_rows": training_rows,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "branch_impact_rows.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    (output_dir / "branch_training_rows.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in training_rows),
        encoding="utf-8",
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    aggregate = summary["aggregate"]
    lines = [
        "# Journey Branch-Impact Audit",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "读取 solver JSONL 日志，聚合每次 Journey 分支后的子节点负列、列添加、active-support 和证明尾段行为。"
        "该脚本只读日志，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "journey_branch_impact_audit = current",
        f"log_count = {summary['log_count']}",
        f"branch_count = {aggregate['branch_count']}",
        f"branch_training_row_count = {summary['branch_training_row_count']}",
        f"tail_class_counts = {aggregate['tail_class_counts']}",
        f"priority_mode_counts = {aggregate['priority_mode_counts']}",
        f"selected_match_count = {aggregate['selected_match_count']}",
        f"top_contains_branch_count = {aggregate['top_contains_branch_count']}",
        f"top_first_branch_count = {aggregate['top_first_branch_count']}",
        f"priority_top_first_branch_count = {aggregate['priority_top_first_branch_count']}",
        f"candidate_log_branch_count = {aggregate['candidate_log_branch_count']}",
        f"forced_pair_branch_count = {aggregate['forced_pair_branch_count']}",
        f"forced_pair_matched_branch_count = {aggregate['forced_pair_matched_branch_count']}",
        f"right_censored_branch_count = {aggregate['right_censored_branch_count']}",
        f"complete_label_branch_count = {aggregate['complete_label_branch_count']}",
        f"usable_branch_impact_training_count = {aggregate['usable_branch_impact_training_count']}",
        f"run_status_counts = {aggregate['run_status_counts']}",
        f"active_touch_branch_count = {aggregate['active_touch_branch_count']}",
        f"inactive_only_branch_count = {aggregate['inactive_only_branch_count']}",
        f"unprocessed_child_count = {aggregate['unprocessed_child_count']}",
        f"total_child_negative_pricing_events = {aggregate['total_child_negative_pricing_events']}",
        f"total_child_column_additions = {aggregate['total_child_column_additions']}",
        f"total_child_added_journeys = {aggregate['total_child_added_journeys']}",
        f"total_child_completion_bound_retries = {aggregate['total_child_completion_bound_retries']}",
        f"total_child_early_branch_triggers = {aggregate['total_child_early_branch_triggers']}",
        "production_ready = false",
        "certificate_effect = false",
        "official_bound_effect = false",
        "```",
        "",
        "## 解释",
        "",
        aggregate["interpretation"],
        "",
        "## Feature / Label Schema",
        "",
        "```json",
        json.dumps(
            {
                "branch_feature_schema": summary["branch_feature_schema"],
                "branch_label_schema": summary["branch_label_schema"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 注意",
        "",
        "若 `selected_match_count = 0` 但 `top_contains_branch_count > 0`，通常表示输入日志生成于 "
        "`selected` / `priority_top` 字段加入之前；此时只能从 `top` 中反推实际分支候选位置，"
        "不能把 `selected_match_count = 0` 解读为分支选择错误。",
        "",
        "若 `candidate_log_branch_count = 0`，说明该批日志完全缺少 branch-candidate 特征；"
        "这些 rows 只能作为 proof-cost / tail-risk 诊断，不能作为 GAT branch-impact 排序训练 row。",
        "",
        "## Records",
        "",
        "```json",
        json.dumps(summary["records"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = build_branch_impact(args.paths, args.output_dir, args.report)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

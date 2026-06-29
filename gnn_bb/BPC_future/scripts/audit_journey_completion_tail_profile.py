#!/usr/bin/env python3
"""Audit Journey completion-bound tail behavior from JSONL solver logs.

The script is diagnostic-only: it reads JSONL logs and summarizes the final
true-dual completion-bound judge.  It does not run BPC, pricing, or RMP.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_completion_tail_profile_20260623")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260623_bpc_future_journey_completion_tail_profile_zh.md"
)

PROFILE_TIME_FIELDS = (
    "direct_label_profile_next_sortie_total_time",
    "direct_label_profile_resource_precheck_time",
    "direct_label_profile_extend_time",
    "direct_label_profile_bound_check_time",
    "direct_label_profile_pre_dominance_time",
    "direct_label_profile_dominance_time",
    "direct_label_profile_completion_time",
    "direct_label_profile_task_filter_time",
    "direct_label_profile_option_lookup_time",
    "direct_label_profile_label_create_time",
    "direct_label_profile_priority_queue_time",
    "direct_label_profile_completed_process_time",
    "direct_label_profile_completed_dedup_time",
    "direct_label_profile_stream_callback_time",
    "direct_label_profile_partial_bound_dual_sum_time",
    "direct_label_profile_partial_bound_unique_task_time",
    "direct_label_profile_partial_bound_unique_route_time",
    "direct_label_profile_partial_bound_completion_route_time",
    "direct_label_profile_partial_bound_resource_pareto_time",
    "direct_label_profile_partial_bound_cut_time",
)

PROFILE_COUNT_FIELDS = (
    "direct_label_profile_next_sortie_calls",
    "direct_label_profile_partial_heap_pops",
    "direct_label_profile_extension_attempts",
    "direct_label_profile_option_attempts",
    "direct_label_profile_bound_checks",
    "direct_label_profile_dominance_checks",
    "direct_label_profile_completion_calls",
    "direct_label_profile_pre_dominance_checks",
    "direct_label_profile_pre_dominance_pruned",
    "direct_label_profile_partial_bucket_count",
    "direct_label_profile_partial_bucket_label_count",
)

PROFILE_MAX_FIELDS = (
    "direct_label_profile_partial_bucket_max_size",
)

CACHE_COUNT_FIELDS = (
    "direct_next_sortie_cache_hits",
    "direct_next_sortie_cache_misses",
    "generated_next_sorties_before_bound",
    "generated_next_sorties_after_bound",
)

HARVEST_COUNT_FIELDS = (
    "harvest_candidate_negative_count",
    "harvest_selected_count",
    "harvest_candidate_new_task_set_count",
    "harvest_selected_new_task_set_count",
    "harvest_selected_replacement_task_set_count",
    "harvest_candidate_priority_task_set_count",
    "harvest_selected_priority_task_set_count",
    "harvest_candidate_support_changing_count",
    "harvest_selected_support_changing_count",
    "harvest_fallback_fill_count",
    "harvest_fallback_fill_new_mask_count",
    "harvest_fallback_fill_replacement_count",
    "harvest_selected_weak_replacement_count",
)

TAIL_MIN_FILL_MODE_FIELDS = (
    "completion_bound_diverse_harvest_tail_min_fill_enabled",
    "completion_bound_diverse_harvest_tail_min_fill_audit_enabled",
    "completion_bound_diverse_harvest_tail_min_fill_candidate",
    "completion_bound_diverse_harvest_tail_min_fill_applied",
    "completion_bound_diverse_harvest_tail_min_fill_base",
    "completion_bound_diverse_harvest_tail_min_fill_target",
    "completion_bound_diverse_harvest_tail_min_fill_max_depth",
    "completion_bound_diverse_harvest_tail_min_fill_final_probe_only",
    "completion_bound_diverse_harvest_tail_min_fill_reason",
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


def _is_completion_retry(record: dict[str, Any]) -> bool:
    return (
        record.get("event") == "journey_pricing"
        and str(record.get("pricing_kind") or "").startswith("exact_completion_bound")
    )


def _classify_completion_retry(record: dict[str, Any] | None) -> str:
    if record is None:
        return "no_completion_bound_retry"
    state = str(record.get("pricing_state") or record.get("status") or "")
    reason = str(record.get("reason") or "")
    negative_journeys = _int(record, "negative_journeys")
    selected_trips = _int(record, "selected_trips")
    global_certificate = bool(record.get("global_certificate") or record.get("global_certificate_capable"))
    exhausted = bool(record.get("exhausted"))
    if negative_journeys > 0 or selected_trips > 0:
        return "completion_bound_found_negative"
    if global_certificate and exhausted and state in {"OPTIMAL", "CERTIFIED_NO_NEGATIVE"}:
        return "completion_bound_certified_no_negative"
    if state in {"INCOMPLETE_LIMIT", "INCOMPLETE"} and reason == "time_limit":
        return "completion_bound_time_limit_no_column_uncertified"
    if state in {"INCOMPLETE_LIMIT", "INCOMPLETE"}:
        return f"completion_bound_incomplete_{reason or 'unknown'}"
    if exhausted and not negative_journeys:
        return "completion_bound_exhausted_no_negative_unclear_certificate"
    return "completion_bound_other"


def _sum(records: Iterable[dict[str, Any]], key: str) -> float:
    return sum(_float(record, key) for record in records)


def _sum_float_fields(records: Iterable[dict[str, Any]], fields: Iterable[str]) -> dict[str, float]:
    materialized = list(records)
    return {
        field: round(sum(_float(record, field) for record in materialized), 6)
        for field in fields
    }


def _sum_int_fields(records: Iterable[dict[str, Any]], fields: Iterable[str]) -> dict[str, int]:
    materialized = list(records)
    return {
        field: int(sum(_int(record, field) for record in materialized))
        for field in fields
    }


def _sum_harvest_count_fields(records: Iterable[dict[str, Any]]) -> dict[str, int]:
    materialized = list(records)
    totals: dict[str, int] = {}
    for field in HARVEST_COUNT_FIELDS:
        direct_field = f"direct_label_{field}"
        totals[field] = int(
            sum(
                max(_int(record, field), _int(record, direct_field))
                for record in materialized
            )
        )
    return totals


def _max_int_fields(records: Iterable[dict[str, Any]], fields: Iterable[str]) -> dict[str, int]:
    materialized = list(records)
    return {
        field: int(max((_int(record, field) for record in materialized), default=0))
        for field in fields
    }


def _top_float_fields(totals: dict[str, float], limit: int = 8) -> dict[str, float]:
    return dict(
        sorted(
            ((field, value) for field, value in totals.items() if abs(float(value)) > 0.0),
            key=lambda item: (-float(item[1]), item[0]),
        )[:limit]
    )


def _time_share_top(
    totals: dict[str, float],
    *,
    denominator: float,
    limit: int = 8,
) -> dict[str, float]:
    if float(denominator) <= 0.0:
        return {}
    shares = {
        field: round(float(value) / float(denominator), 6)
        for field, value in totals.items()
        if abs(float(value)) > 0.0
    }
    return dict(sorted(shares.items(), key=lambda item: (-float(item[1]), item[0]))[:limit])


def _completion_retry_mode_rows(trigger_events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in trigger_events:
        mode = event.get("retry_mode")
        if not isinstance(mode, dict):
            continue
        row = {
            key: mode.get(key)
            for key in TAIL_MIN_FILL_MODE_FIELDS
            if key in mode
        }
        if row:
            rows.append(row)
    return rows


def _tail_min_fill_summary(mode_rows: list[dict[str, Any]]) -> dict[str, Any]:
    reason_counts = Counter(
        str(row.get("completion_bound_diverse_harvest_tail_min_fill_reason") or "")
        for row in mode_rows
        if "completion_bound_diverse_harvest_tail_min_fill_reason" in row
    )
    return {
        "completion_retry_tail_min_fill_mode_count": len(mode_rows),
        "completion_retry_tail_min_fill_candidate_count": int(
            sum(1 for row in mode_rows if bool(row.get("completion_bound_diverse_harvest_tail_min_fill_candidate")))
        ),
        "completion_retry_tail_min_fill_applied_count": int(
            sum(1 for row in mode_rows if bool(row.get("completion_bound_diverse_harvest_tail_min_fill_applied")))
        ),
        "completion_retry_tail_min_fill_optin_disabled_count": int(
            sum(
                1
                for row in mode_rows
                if row.get("completion_bound_diverse_harvest_tail_min_fill_reason") == "optin_disabled"
            )
        ),
        "completion_retry_tail_min_fill_reason_counts": dict(sorted(reason_counts.items())),
        "completion_retry_tail_min_fill_last": mode_rows[-1] if mode_rows else None,
    }


def _classify_harvest_tail(
    completion_retries: list[dict[str, Any]],
    *,
    total_profile_generation_time: float,
) -> str:
    if not completion_retries:
        return "no_completion_bound_retry"
    totals = _sum_harvest_count_fields(completion_retries)
    candidate = int(totals.get("harvest_candidate_negative_count", 0))
    selected = int(totals.get("harvest_selected_count", 0))
    candidate_new = int(totals.get("harvest_candidate_new_task_set_count", 0))
    selected_new = int(totals.get("harvest_selected_new_task_set_count", 0))
    selected_replacement = int(totals.get("harvest_selected_replacement_task_set_count", 0))
    support_changing = int(totals.get("harvest_selected_support_changing_count", 0))
    if selected_new > 0:
        return "harvest_returned_new_task_set"
    if support_changing > 0:
        return "harvest_returned_support_changing"
    if selected_replacement > 0:
        return "harvest_replacement_only_selected"
    if candidate_new > 0 and selected <= 0:
        return "harvest_new_task_set_candidate_not_returned"
    if candidate > 0 and candidate_new <= 0:
        return "harvest_replacement_only_candidates"
    if candidate > 0:
        return "harvest_candidate_not_returned"
    if float(total_profile_generation_time) >= 30.0:
        return "expensive_no_harvest_candidate"
    return "no_harvest_candidate"


def _summarize_log(path: Path) -> dict[str, Any]:
    events = _read_events(path)
    pricing_events = [record for record in events if record.get("event") == "journey_pricing"]
    completion_retries = [record for record in pricing_events if _is_completion_retry(record)]
    trigger_events = [
        record
        for record in events
        if record.get("event") == "journey_exact_pricing_completion_bound_retry"
    ]
    addition_events = [record for record in events if record.get("event") == "journey_column_addition"]
    finish = next((record for record in reversed(events) if record.get("event") == "finish"), None)
    last_retry = completion_retries[-1] if completion_retries else None
    pricing_kind_counts = Counter(str(record.get("pricing_kind") or "") for record in pricing_events)
    state_counts = Counter(
        f"{record.get('pricing_kind')}:{record.get('pricing_state')}:{record.get('reason')}"
        for record in pricing_events
    )
    profile_time_totals = _sum_float_fields(completion_retries, PROFILE_TIME_FIELDS)
    profile_count_totals = _sum_int_fields(completion_retries, PROFILE_COUNT_FIELDS)
    profile_count_totals.update(_max_int_fields(completion_retries, PROFILE_MAX_FIELDS))
    tail_min_fill_mode_rows = _completion_retry_mode_rows(trigger_events)
    total_profile_generation_time = round(
        _sum(completion_retries, "profile_generation_time"),
        6,
    )
    harvest_count_totals = _sum_harvest_count_fields(completion_retries)
    cache_disabled_reason_counts = Counter(
        str(record.get("direct_next_sortie_cache_disabled_reason") or "")
        for record in completion_retries
        if str(record.get("direct_next_sortie_cache_disabled_reason") or "")
    )
    return {
        "log_file": str(path),
        "instance": None if finish is None else finish.get("instance"),
        "finish_status": None if finish is None else finish.get("status"),
        "finish_solving_time": None if finish is None else finish.get("solving_time"),
        "finish_primal_bound": None if finish is None else finish.get("primal_bound"),
        "finish_columns": None if finish is None else finish.get("columns"),
        "finish_pricing_calls": None if finish is None else finish.get("pricing_calls"),
        "finish_exact_pricing_calls": None if finish is None else finish.get("exact_pricing_calls"),
        "finish_rmp_solves": None if finish is None else finish.get("rmp_solves"),
        "finish_pricing_incomplete_nodes": None
        if finish is None
        else finish.get("pricing_incomplete_nodes"),
        "pricing_event_count": len(pricing_events),
        "completion_retry_trigger_count": len(trigger_events),
        "completion_retry_count": len(completion_retries),
        "completion_retry_class": _classify_completion_retry(last_retry),
        "pricing_kind_counts": dict(sorted(pricing_kind_counts.items())),
        "pricing_state_counts": dict(sorted(state_counts.items())),
        "completion_retry_total_profile_generation_time": total_profile_generation_time,
        "completion_retry_total_generated_sequences": int(
            sum(_int(record, "generated_sequences") for record in completion_retries)
        ),
        "completion_retry_total_evaluated_timed_trips": int(
            sum(_int(record, "evaluated_timed_trips") for record in completion_retries)
        ),
        "completion_retry_total_negative_journeys": int(
            sum(_int(record, "negative_journeys") for record in completion_retries)
        ),
        "completion_retry_total_selected_trips": int(
            sum(_int(record, "selected_trips") for record in completion_retries)
        ),
        "completion_retry_total_expanded_before_bound": int(
            sum(_int(record, "expanded_labels_before_bound") for record in completion_retries)
        ),
        "completion_retry_total_expanded_after_bound": int(
            sum(_int(record, "expanded_labels_after_bound") for record in completion_retries)
        ),
        "completion_retry_total_lb_pruned": int(
            sum(_int(record, "lb_pruned_labels") for record in completion_retries)
        ),
        "completion_retry_total_two_cycle_build_time": round(
            _sum(completion_retries, "two_cycle_build_time"),
            6,
        ),
        "completion_retry_total_bound_build_time": round(
            _sum(completion_retries, "bound_build_time"),
            6,
        ),
        "completion_retry_profile_timing_enabled_count": int(
            sum(1 for record in completion_retries if bool(record.get("direct_label_profile_timing_enabled")))
        ),
        "completion_retry_profile_time_totals": profile_time_totals,
        "completion_retry_profile_time_top": _top_float_fields(profile_time_totals),
        "completion_retry_profile_time_share_top": _time_share_top(
            profile_time_totals,
            denominator=total_profile_generation_time,
        ),
        "completion_retry_profile_count_totals": profile_count_totals,
        "completion_retry_cache_count_totals": _sum_int_fields(
            completion_retries,
            CACHE_COUNT_FIELDS,
        ),
        "completion_retry_cache_requested_count": int(
            sum(1 for record in completion_retries if bool(record.get("direct_next_sortie_cache_requested")))
        ),
        "completion_retry_cache_effective_count": int(
            sum(1 for record in completion_retries if bool(record.get("direct_next_sortie_cache_effective_enabled")))
        ),
        "completion_retry_cache_disabled_reason_counts": dict(sorted(cache_disabled_reason_counts.items())),
        "completion_retry_harvest_count_totals": harvest_count_totals,
        "completion_retry_harvest_tail_class": _classify_harvest_tail(
            completion_retries,
            total_profile_generation_time=total_profile_generation_time,
        ),
        **_tail_min_fill_summary(tail_min_fill_mode_rows),
        "completion_retry_last": _compact_completion_retry(last_retry),
        "addition_event_count": len(addition_events),
        "added_journeys": int(sum(_int(record, "added_journeys") for record in addition_events)),
        "new_journeys": int(sum(_int(record, "new_journeys") for record in addition_events)),
        "replacement_journeys": int(
            sum(_int(record, "replacement_journeys") for record in addition_events)
        ),
    }


def _compact_completion_retry(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if record is None:
        return None
    keys = [
        "cg_iter",
        "pricing_kind",
        "pricing_state",
        "reason",
        "pricing_time_limit",
        "profile_generation_time",
        "generated_sequences",
        "evaluated_timed_trips",
        "candidate_trips",
        "state_count",
        "negative_journeys",
        "selected_trips",
        "best_reduced_cost",
        "completion_bound_enabled",
        "bound_build_time",
        "lb_state_count",
        "lb_negative_state_count",
        "lb_min_value",
        "lb_mean_value",
        "expanded_labels_before_bound",
        "expanded_labels_after_bound",
        "lb_pruned_labels",
        "two_cycle_enabled",
        "two_cycle_table_complete",
        "two_cycle_state_count",
        "two_cycle_blocked_extensions",
        "two_cycle_second_best_queries",
        "two_cycle_incompatible_queries",
        "two_cycle_top2_replacements",
        "two_cycle_build_time",
        "direct_label_harvest_candidate_count",
        "direct_label_harvest_selected_count",
        "direct_label_harvest_selected_new_task_set_count",
        "direct_label_harvest_selected_replacement_task_set_count",
        "harvest_candidate_negative_count",
        "harvest_selected_count",
        "harvest_candidate_new_task_set_count",
        "harvest_selected_new_task_set_count",
        "harvest_selected_replacement_task_set_count",
        "harvest_candidate_priority_task_set_count",
        "harvest_selected_priority_task_set_count",
        "harvest_candidate_support_changing_count",
        "harvest_selected_support_changing_count",
        "harvest_fallback_fill_count",
        "harvest_fallback_fill_new_mask_count",
        "harvest_fallback_fill_replacement_count",
        "harvest_selected_weak_replacement_count",
        "global_certificate",
        "global_certificate_capable",
        "exhausted",
    ]
    keys.extend(PROFILE_TIME_FIELDS)
    keys.extend(PROFILE_COUNT_FIELDS)
    keys.extend(PROFILE_MAX_FIELDS)
    keys.extend(CACHE_COUNT_FIELDS)
    keys.extend(
        [
            "direct_next_sortie_cache_requested",
            "direct_next_sortie_cache_effective_enabled",
            "direct_next_sortie_cache_disabled_reason",
            "direct_label_profile_timing_enabled",
            "direct_journey_label_next_sortie_cache_enabled",
            "direct_label_harvest_min_fill",
            "direct_label_profile_partial_bucket_mean_size",
        ]
    )
    return {key: record.get(key) for key in keys if key in record}


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    class_counts = Counter(str(row.get("completion_retry_class") or "") for row in rows)
    harvest_tail_class_counts = Counter(
        str(row.get("completion_retry_harvest_tail_class") or "") for row in rows
    )
    incomplete_tail_rows = [
        row
        for row in rows
        if row.get("completion_retry_class") == "completion_bound_time_limit_no_column_uncertified"
    ]
    profile_time_totals = {
        field: round(
            sum(
                float((row.get("completion_retry_profile_time_totals") or {}).get(field) or 0.0)
                for row in rows
            ),
            6,
        )
        for field in PROFILE_TIME_FIELDS
    }
    profile_count_totals = {
        field: int(
            sum(
                int((row.get("completion_retry_profile_count_totals") or {}).get(field) or 0)
                for row in rows
            )
        )
        for field in PROFILE_COUNT_FIELDS
    }
    profile_count_totals.update(
        {
            field: int(
                max(
                    (
                        int((row.get("completion_retry_profile_count_totals") or {}).get(field) or 0)
                        for row in rows
                    ),
                    default=0,
                )
            )
            for field in PROFILE_MAX_FIELDS
        }
    )
    cache_count_totals = {
        field: int(
            sum(
                int((row.get("completion_retry_cache_count_totals") or {}).get(field) or 0)
                for row in rows
            )
        )
        for field in CACHE_COUNT_FIELDS
    }
    cache_disabled_reason_counts: Counter[str] = Counter()
    for row in rows:
        cache_disabled_reason_counts.update(
            {
                str(key): int(value)
                for key, value in (row.get("completion_retry_cache_disabled_reason_counts") or {}).items()
            }
        )
    harvest_count_totals = {
        field: int(
            sum(
                int((row.get("completion_retry_harvest_count_totals") or {}).get(field) or 0)
                for row in rows
            )
        )
        for field in HARVEST_COUNT_FIELDS
    }
    total_profile_generation_time = round(
        sum(float(row.get("completion_retry_total_profile_generation_time") or 0.0) for row in rows),
        6,
    )
    tail_min_fill_reason_counts: Counter[str] = Counter()
    for row in rows:
        tail_min_fill_reason_counts.update(
            {
                str(key): int(value)
                for key, value in (row.get("completion_retry_tail_min_fill_reason_counts") or {}).items()
            }
        )
    return {
        "log_count": len(rows),
        "completion_retry_class_counts": dict(sorted(class_counts.items())),
        "incomplete_tail_count": len(incomplete_tail_rows),
        "completion_retry_profile_timing_enabled_count": int(
            sum(int(row.get("completion_retry_profile_timing_enabled_count") or 0) for row in rows)
        ),
        "completion_retry_profile_time_totals": profile_time_totals,
        "completion_retry_profile_time_top": _top_float_fields(profile_time_totals),
        "completion_retry_profile_time_share_top": _time_share_top(
            profile_time_totals,
            denominator=total_profile_generation_time,
        ),
        "completion_retry_profile_count_totals": profile_count_totals,
        "completion_retry_cache_count_totals": cache_count_totals,
        "completion_retry_cache_requested_count": int(
            sum(int(row.get("completion_retry_cache_requested_count") or 0) for row in rows)
        ),
        "completion_retry_cache_effective_count": int(
            sum(int(row.get("completion_retry_cache_effective_count") or 0) for row in rows)
        ),
        "completion_retry_cache_disabled_reason_counts": dict(sorted(cache_disabled_reason_counts.items())),
        "completion_retry_harvest_count_totals": harvest_count_totals,
        "completion_retry_harvest_tail_class_counts": dict(sorted(harvest_tail_class_counts.items())),
        "completion_retry_harvest_top_profile_records": _top_harvest_profile_records(rows),
        "completion_retry_total_profile_generation_time": total_profile_generation_time,
        "completion_retry_total_generated_sequences": int(
            sum(int(row.get("completion_retry_total_generated_sequences") or 0) for row in rows)
        ),
        "completion_retry_total_evaluated_timed_trips": int(
            sum(int(row.get("completion_retry_total_evaluated_timed_trips") or 0) for row in rows)
        ),
        "completion_retry_total_negative_journeys": int(
            sum(int(row.get("completion_retry_total_negative_journeys") or 0) for row in rows)
        ),
        "completion_retry_total_selected_trips": int(
            sum(int(row.get("completion_retry_total_selected_trips") or 0) for row in rows)
        ),
        "completion_retry_tail_min_fill_mode_count": int(
            sum(int(row.get("completion_retry_tail_min_fill_mode_count") or 0) for row in rows)
        ),
        "completion_retry_tail_min_fill_candidate_count": int(
            sum(int(row.get("completion_retry_tail_min_fill_candidate_count") or 0) for row in rows)
        ),
        "completion_retry_tail_min_fill_applied_count": int(
            sum(int(row.get("completion_retry_tail_min_fill_applied_count") or 0) for row in rows)
        ),
        "completion_retry_tail_min_fill_optin_disabled_count": int(
            sum(int(row.get("completion_retry_tail_min_fill_optin_disabled_count") or 0) for row in rows)
        ),
        "completion_retry_tail_min_fill_reason_counts": dict(sorted(tail_min_fill_reason_counts.items())),
        "interpretation": _interpret(rows),
    }


def _top_harvest_profile_records(rows: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
    selected = sorted(
        rows,
        key=lambda row: float(row.get("completion_retry_total_profile_generation_time") or 0.0),
        reverse=True,
    )[:limit]
    compact: list[dict[str, Any]] = []
    for row in selected:
        harvest = row.get("completion_retry_harvest_count_totals") or {}
        compact.append(
            {
                "instance": row.get("instance"),
                "log_file": row.get("log_file"),
                "finish_status": row.get("finish_status"),
                "completion_retry_class": row.get("completion_retry_class"),
                "harvest_tail_class": row.get("completion_retry_harvest_tail_class"),
                "profile_generation_time": row.get("completion_retry_total_profile_generation_time"),
                "harvest_candidate_negative_count": harvest.get("harvest_candidate_negative_count", 0),
                "harvest_selected_count": harvest.get("harvest_selected_count", 0),
                "harvest_candidate_new_task_set_count": harvest.get(
                    "harvest_candidate_new_task_set_count",
                    0,
                ),
                "harvest_selected_new_task_set_count": harvest.get(
                    "harvest_selected_new_task_set_count",
                    0,
                ),
                "harvest_selected_replacement_task_set_count": harvest.get(
                    "harvest_selected_replacement_task_set_count",
                    0,
                ),
            }
        )
    return compact


def _interpret(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "没有找到可审计日志。"
    class_counts = Counter(str(row.get("completion_retry_class") or "") for row in rows)
    no_column_timeouts = class_counts.get("completion_bound_time_limit_no_column_uncertified", 0)
    found_negative = class_counts.get("completion_bound_found_negative", 0)
    certified = class_counts.get("completion_bound_certified_no_negative", 0)
    harvest_tail_counts = Counter(str(row.get("completion_retry_harvest_tail_class") or "") for row in rows)
    expensive_no_candidate = harvest_tail_counts.get("expensive_no_harvest_candidate", 0)
    new_candidate_not_returned = harvest_tail_counts.get("harvest_new_task_set_candidate_not_returned", 0)
    if expensive_no_candidate > 0 and expensive_no_candidate >= new_candidate_not_returned:
        return (
            "completion-bound tail 主要表现为高 profile-generation 时间但没有可 harvest 的 "
            "true-RC 负列候选。下一步优先看 direct-label proof loop / completion-bound "
            "剪枝成本，而不是降低返回门槛。"
        )
    if new_candidate_not_returned > 0:
        return (
            "日志中存在新 task-set 候选但没有被返回的 harvest tail。下一步优先检查 "
            "diverse-harvest selection、min-fill 与 priority/support 约束。"
        )
    if no_column_timeouts and no_column_timeouts >= found_negative + certified:
        return (
            "主要瓶颈是 completion-bound final judge 在无负列尾部耗尽时间，"
            "不是 GAT/worker 没触发。下一步应做 final-judge budget/profiling "
            "和 direct-label loop 剪枝优化。"
        )
    if found_negative > 0:
        return (
            "final judge 仍在承担昂贵 worker 职责，找到负列后应优先检查 "
            "harvesting 是否一次性返回足够正交列。"
        )
    if certified > 0:
        return "已有 certified no-negative 样本，可对比成功证书与失败尾部的剪枝字段。"
    return "completion-bound tail 类型混合，需要按 records 逐条查看。"


def build_profile(paths: list[Path], output_dir: Path, report: Path) -> dict[str, Any]:
    rows = [_summarize_log(path) for path in _iter_jsonl(paths)]
    summary = {
        "schema_version": "journey_completion_tail_profile_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "input_paths": [str(path) for path in paths],
        "aggregate": _aggregate(rows),
        "records": rows,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    aggregate = summary["aggregate"]
    lines = [
        "# Journey Completion-Bound Tail Profile",
        "",
        "日期：2026-06-23",
        "",
        "## 目的",
        "",
        "读取 solver JSONL 日志，聚合 true-dual completion-bound final judge 的尾部状态。"
        "该脚本只读日志，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "journey_completion_tail_profile = current",
        f"log_count = {aggregate['log_count']}",
        f"completion_retry_class_counts = {aggregate['completion_retry_class_counts']}",
        f"incomplete_tail_count = {aggregate['incomplete_tail_count']}",
        "completion_retry_total_profile_generation_time = "
        f"{aggregate['completion_retry_total_profile_generation_time']}",
        "completion_retry_profile_timing_enabled_count = "
        f"{aggregate['completion_retry_profile_timing_enabled_count']}",
        "completion_retry_profile_time_top = "
        f"{aggregate['completion_retry_profile_time_top']}",
        "completion_retry_profile_time_share_top = "
        f"{aggregate['completion_retry_profile_time_share_top']}",
        "completion_retry_cache_count_totals = "
        f"{aggregate['completion_retry_cache_count_totals']}",
        "completion_retry_cache_requested_count = "
        f"{aggregate['completion_retry_cache_requested_count']}",
        "completion_retry_cache_effective_count = "
        f"{aggregate['completion_retry_cache_effective_count']}",
        "completion_retry_cache_disabled_reason_counts = "
        f"{aggregate['completion_retry_cache_disabled_reason_counts']}",
        "completion_retry_harvest_count_totals = "
        f"{aggregate['completion_retry_harvest_count_totals']}",
        "completion_retry_harvest_tail_class_counts = "
        f"{aggregate['completion_retry_harvest_tail_class_counts']}",
        "completion_retry_total_generated_sequences = "
        f"{aggregate['completion_retry_total_generated_sequences']}",
        "completion_retry_total_evaluated_timed_trips = "
        f"{aggregate['completion_retry_total_evaluated_timed_trips']}",
        "completion_retry_total_negative_journeys = "
        f"{aggregate['completion_retry_total_negative_journeys']}",
        "completion_retry_total_selected_trips = "
        f"{aggregate['completion_retry_total_selected_trips']}",
        "completion_retry_tail_min_fill_mode_count = "
        f"{aggregate['completion_retry_tail_min_fill_mode_count']}",
        "completion_retry_tail_min_fill_candidate_count = "
        f"{aggregate['completion_retry_tail_min_fill_candidate_count']}",
        "completion_retry_tail_min_fill_applied_count = "
        f"{aggregate['completion_retry_tail_min_fill_applied_count']}",
        "completion_retry_tail_min_fill_optin_disabled_count = "
        f"{aggregate['completion_retry_tail_min_fill_optin_disabled_count']}",
        "completion_retry_tail_min_fill_reason_counts = "
        f"{aggregate['completion_retry_tail_min_fill_reason_counts']}",
        "completion_retry_harvest_top_profile_records = "
        f"{json.dumps(aggregate['completion_retry_harvest_top_profile_records'], ensure_ascii=False)}",
        "production_ready = false",
        "certificate_effect = false",
        "official_bound_effect = false",
        "```",
        "",
        "## 解释",
        "",
        aggregate["interpretation"],
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
    summary = build_profile(args.paths, args.output_dir, args.report)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

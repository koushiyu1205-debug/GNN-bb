#!/usr/bin/env python3
"""Build a calibration-only impact dataset from exact-context replay outputs.

The input is a replay manifest plus the corresponding replay result.  The
analysis joins candidate descriptors from the manifest with local RMP treatment
effects from the replay runner.  It is diagnostic-only: it does not solve,
price, add columns, or affect certificates.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def _as_float(value: Any, default: float | None = None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value)
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return True


def _json_path(path: Path, default_name: str) -> Path:
    if path.is_dir():
        return path / default_name
    return path


def _load_json(path: Path, default_name: str) -> dict[str, Any]:
    json_path = _json_path(path, default_name)
    return json.loads(json_path.read_text(encoding="utf-8"))


def _task_set_text(value: Any) -> str:
    if not isinstance(value, (list, tuple, set, frozenset)):
        return ""
    return ",".join(str(int(task)) for task in sorted(value))


def _sequence_text(value: Any) -> str:
    if not isinstance(value, (list, tuple)):
        return ""
    sorties: list[str] = []
    for sortie in value:
        if isinstance(sortie, (list, tuple)):
            sorties.append("-".join(str(int(task)) for task in sortie))
    return "|".join(sorties)


def _signature_key(value: Any) -> str:
    return repr(value)


def _task_tuple(value: Any) -> tuple[int, ...]:
    if isinstance(value, str):
        raw = [item for item in value.replace("-", ",").split(",") if item.strip()]
        try:
            return tuple(sorted(int(item) for item in raw))
        except ValueError:
            return tuple()
    if not isinstance(value, (list, tuple, set, frozenset)):
        return tuple()
    try:
        return tuple(sorted(int(task) for task in value))
    except (TypeError, ValueError):
        return tuple()


def _jaccard(left: set[int], right: set[int]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / float(len(union))


def _rank(values: list[float], value: float | None) -> int | None:
    if value is None or not values:
        return None
    ordered = sorted(values)
    for idx, current in enumerate(ordered, 1):
        if abs(float(current) - float(value)) <= 1.0e-12:
            return idx
    return len(values) + 1


def _average(values: list[float] | list[int]) -> float:
    return 0.0 if not values else sum(float(value) for value in values) / float(len(values))


def _dual_norms(value: Any) -> tuple[float | None, float | None]:
    if not isinstance(value, (list, tuple)):
        return None, None
    duals: list[float] = []
    for item in value:
        converted = _as_float(item)
        if converted is not None:
            duals.append(float(converted))
    if not duals:
        return None, None
    return sum(abs(item) for item in duals), max(abs(item) for item in duals)


def _pool_signature_duplicate_count(pool_journeys: Any) -> int | None:
    if not isinstance(pool_journeys, list):
        return None
    signatures = [
        _signature_key(journey.get("signature"))
        for journey in pool_journeys
        if isinstance(journey, dict) and journey.get("signature") is not None
    ]
    if not signatures:
        return None
    return max(0, len(signatures) - len(set(signatures)))


def _pool_task_set_count(pool_journeys: Any) -> int | None:
    if not isinstance(pool_journeys, list):
        return None
    task_sets = {
        _task_set_text(journey.get("task_set"))
        for journey in pool_journeys
        if isinstance(journey, dict) and journey.get("task_set") is not None
    }
    task_sets.discard("")
    if not task_sets:
        return None
    return len(task_sets)


def _active_basis_rows(snapshot_owner: dict[str, Any]) -> list[dict[str, Any]]:
    if snapshot_owner.get("active_basis_snapshot_complete") is not True:
        return []
    rows = snapshot_owner.get("active_basis_rows")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _active_basis_row_signature(row: dict[str, Any]) -> str:
    signature = row.get("active_journey_signature")
    if signature is not None:
        return _signature_key(signature)
    task_set = row.get("active_journey_task_set")
    if task_set is not None:
        return f"task_set:{_task_set_text(task_set)}"
    return ""


def _active_basis_signature_set(rows: list[dict[str, Any]]) -> set[str]:
    signatures = {_active_basis_row_signature(row) for row in rows}
    signatures.discard("")
    return signatures


def _previous_active_basis_snapshot(
    events: list[dict[str, Any]], *, cg_iter: int
) -> dict[str, Any]:
    candidates = [
        event
        for event in _events_named(
            events, "journey_counterfactual_replay_capture", before_cg_iter=cg_iter
        )
        if event.get("active_basis_snapshot_complete") is True
        and isinstance(event.get("active_basis_rows"), list)
    ]
    return candidates[-1] if candidates else {}


def _active_basis_churn_count(
    manifest_case: dict[str, Any], events: list[dict[str, Any]], *, cg_iter: int
) -> tuple[int | None, str]:
    current_rows = _active_basis_rows(manifest_case)
    if not current_rows:
        return None, "missing_current_active_basis_snapshot"
    previous = _previous_active_basis_snapshot(events, cg_iter=cg_iter)
    previous_rows = _active_basis_rows(previous)
    if not previous_rows:
        if cg_iter <= 1:
            return 0, "initial_active_basis_snapshot"
        return None, "missing_previous_active_basis_snapshot"
    current_signatures = _active_basis_signature_set(current_rows)
    previous_signatures = _active_basis_signature_set(previous_rows)
    if not current_signatures or not previous_signatures:
        return None, "missing_active_basis_signature_keys"
    return len(current_signatures.symmetric_difference(previous_signatures)), (
        "full_active_basis_signature_symmetric_difference"
    )


def _active_basis_duplicate_task_set_ratio(rows: list[dict[str, Any]]) -> float | None:
    task_sets = [
        _task_set_text(row.get("active_journey_task_set"))
        for row in rows
        if row.get("active_journey_task_set") is not None
    ]
    task_sets = [item for item in task_sets if item]
    if not task_sets:
        return None
    return max(0.0, (len(task_sets) - len(set(task_sets))) / float(len(task_sets)))


def _active_basis_fractional_ratio(rows: list[dict[str, Any]]) -> float | None:
    if not rows:
        return None
    fractional = 0
    active = 0
    for row in rows:
        value = _as_float(row.get("active_lambda_value"))
        if value is None or value <= 1.0e-9:
            continue
        active += 1
        if value < 1.0 - 1.0e-9:
            fractional += 1
    if active <= 0:
        return None
    return fractional / float(active)


def _active_basis_near_zero_reduced_cost_ratio(
    rows: list[dict[str, Any]], *, eps: float = 1.0e-7
) -> float | None:
    values: list[float] = []
    for row in rows:
        value = _as_float(row.get("active_journey_solver_reduced_cost"))
        if value is None:
            value = _as_float(row.get("active_journey_true_reduced_cost"))
        if value is not None:
            values.append(float(value))
    if not values:
        return None
    return sum(1 for value in values if abs(value) <= eps) / float(len(values))


def _active_basis_degeneracy_pressure(
    manifest_case: dict[str, Any]
) -> tuple[float | None, str]:
    rows = _active_basis_rows(manifest_case)
    if not rows:
        return None, "missing_current_active_basis_snapshot"
    components = [
        value
        for value in (
            _active_basis_fractional_ratio(rows),
            _active_basis_duplicate_task_set_ratio(rows),
            _active_basis_near_zero_reduced_cost_ratio(rows),
        )
        if value is not None
    ]
    if not components:
        return None, "missing_active_basis_pressure_components"
    return round(sum(float(value) for value in components), 9), (
        "active_basis_snapshot_fractional_duplicate_near_zero_rc_sum"
    )


def _read_jsonl_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or not path.is_file():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def _events_named(
    events: list[dict[str, Any]],
    event_name: str,
    *,
    cg_iter: int | None = None,
    before_cg_iter: int | None = None,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for event in events:
        if event.get("event") != event_name:
            continue
        event_cg = _as_int(event.get("cg_iter"), default=-1)
        if cg_iter is not None and event_cg != cg_iter:
            continue
        if before_cg_iter is not None and event_cg >= before_cg_iter:
            continue
        selected.append(event)
    return selected


def _events_named_through(
    events: list[dict[str, Any]], event_name: str, *, cg_iter: int
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for event in events:
        if event.get("event") != event_name:
            continue
        event_cg = _as_int(event.get("cg_iter"), default=-1)
        if event_cg <= int(cg_iter):
            selected.append(event)
    return selected


def _latest_named(
    events: list[dict[str, Any]], event_name: str, *, cg_iter: int
) -> dict[str, Any]:
    selected = _events_named(events, event_name, cg_iter=cg_iter)
    return selected[-1] if selected else {}


def _active_basis_hash_churn(events: list[dict[str, Any]], *, cg_iter: int) -> tuple[int | None, int | None]:
    pool_records = _events_named_through(
        events, "journey_pool_structure_diagnostics", cg_iter=cg_iter
    )
    hashes = [
        str(record.get("pool_active_task_set_hash") or "")
        for record in pool_records
        if record.get("pool_active_task_set_hash")
    ]
    if not hashes:
        return None, None
    churn = 0
    previous = None
    for value in hashes:
        if previous is not None and value != previous:
            churn += 1
        previous = value
    return churn, len(set(hashes))


def _ratio(numerator: Any, denominator: Any) -> float | None:
    top = _as_float(numerator)
    bottom = _as_float(denominator)
    if top is None or bottom is None or abs(bottom) <= 1.0e-12:
        return None
    return float(top) / float(bottom)


def _rmp_degeneracy_proxy_score(
    *,
    pool: dict[str, Any],
    dual: dict[str, Any],
    additions: list[dict[str, Any]],
    retries: list[dict[str, Any]],
) -> float | None:
    fractional_ratio = _as_float(pool.get("pool_active_fractional_ratio"))
    if fractional_ratio is None:
        fractional_ratio = _ratio(
            pool.get("pool_active_fractional_journey_count"),
            pool.get("pool_active_journey_count"),
        )
    duplicate_ratio = _as_float(pool.get("pool_active_duplicate_task_set_ratio"))
    if duplicate_ratio is None:
        duplicate_ratio = _as_float(pool.get("pool_duplicate_task_set_ratio"))
    objective_delta = _as_float(dual.get("objective_delta"))
    dual_l1_delta = _as_float(dual.get("dual_l1_delta"))
    flat_dual_move = 0.0
    if objective_delta is not None and dual_l1_delta is not None:
        if abs(float(objective_delta)) <= 1.0e-6 and float(dual_l1_delta) > 1.0e-6:
            flat_dual_move = 1.0
    requested = sum(_as_int(event.get("requested_journeys")) for event in additions)
    added = sum(
        _as_int(
            event.get("added_journeys")
            if "added_journeys" in event
            else event.get("new_journeys")
        )
        for event in additions
    )
    rejection_ratio = 0.0
    if requested > 0:
        rejection_ratio = max(0.0, 1.0 - added / float(requested))
    retry_pressure = min(float(len(retries)), 3.0) / 3.0
    components = [
        value
        for value in (
            fractional_ratio,
            duplicate_ratio,
            flat_dual_move,
            rejection_ratio,
            retry_pressure,
        )
        if value is not None
    ]
    if not components:
        return None
    return round(sum(float(value) for value in components), 9)


def _event_history_context_features(
    manifest_case: dict[str, Any], events: list[dict[str, Any]]
) -> dict[str, Any]:
    cg_iter = _as_int(manifest_case.get("cg_iter"), default=-1)
    pool = _latest_named(events, "journey_pool_structure_diagnostics", cg_iter=cg_iter)
    dual = _latest_named(events, "journey_rmp_dual_diagnostics", cg_iter=cg_iter)
    additions = _events_named(events, "journey_column_addition", before_cg_iter=cg_iter)
    retries = _events_named(events, "journey_exact_pricing_retry", before_cg_iter=cg_iter)

    active_basis_size = pool.get("pool_active_journey_count")
    if not _has_value(active_basis_size):
        active_basis_size = dual.get("active_journeys")
    requested = sum(_as_int(event.get("requested_journeys")) for event in additions)
    added = sum(
        _as_int(
            event.get("added_journeys")
            if "added_journeys" in event
            else event.get("new_journeys")
        )
        for event in additions
    )
    if requested > 0:
        acceptance_rate: float | None = added / float(requested)
    elif not additions:
        acceptance_rate = 0.0
    else:
        acceptance_rate = None
    objective_delta = dual.get("objective_delta")
    dual_l1_delta = dual.get("dual_l1_delta")
    if cg_iter <= 1:
        if objective_delta is None:
            objective_delta = 0.0
        if dual_l1_delta is None:
            dual_l1_delta = 0.0
    churn_count, unique_count = _active_basis_hash_churn(events, cg_iter=cg_iter)
    exact_churn_count, exact_churn_source = _active_basis_churn_count(
        manifest_case, events, cg_iter=cg_iter
    )
    degeneracy_proxy_score = _rmp_degeneracy_proxy_score(
        pool=pool,
        dual=dual,
        additions=additions,
        retries=retries,
    )
    degeneracy_pressure, degeneracy_pressure_source = _active_basis_degeneracy_pressure(
        manifest_case
    )
    return {
        "source_file": str(manifest_case.get("source_file") or ""),
        "active_basis_size_before": active_basis_size,
        "active_basis_unique_task_set_count_before": pool.get(
            "pool_active_task_set_count"
        ),
        "active_basis_churn_count_before": exact_churn_count,
        "active_basis_churn_source_before": exact_churn_source,
        "active_basis_hash_churn_count_before": churn_count,
        "active_basis_hash_unique_count_before": unique_count,
        "lambda_active_count_before": active_basis_size,
        "lambda_fractional_count_before": pool.get(
            "pool_active_fractional_journey_count"
        ),
        "rmp_degeneracy_pressure_before": degeneracy_pressure,
        "rmp_degeneracy_pressure_source_before": degeneracy_pressure_source,
        "rmp_degeneracy_proxy_score_before": degeneracy_proxy_score,
        "recent_objective_delta_before": objective_delta,
        "recent_dual_l1_delta_before": dual_l1_delta,
        "recent_added_column_acceptance_rate_before": acceptance_rate,
        "pricing_tail_retry_count_before": len(retries),
    }


def _manifest_context_features(manifest_case: dict[str, Any]) -> dict[str, Any]:
    dual_l1, dual_linf = _dual_norms(manifest_case.get("true_dual_vector"))
    return {
        "active_hash_before": manifest_case.get("active_hash_before") or "",
        "dual_hash_before": manifest_case.get("true_dual_hash") or "",
        "dual_l1_norm_before": None if dual_l1 is None else round(float(dual_l1), 9),
        "dual_linf_norm_before": None if dual_linf is None else round(float(dual_linf), 9),
        "column_pool_size_before": manifest_case.get("pool_journey_count"),
        "duplicate_signature_pool_count_before": _pool_signature_duplicate_count(
            manifest_case.get("pool_journeys")
        ),
        "task_set_pool_count_before": _pool_task_set_count(
            manifest_case.get("pool_journeys")
        ),
        "active_basis_snapshot_enabled_before": bool(
            manifest_case.get("active_basis_snapshot_enabled")
        ),
        "active_basis_snapshot_complete_before": bool(
            manifest_case.get("active_basis_snapshot_complete")
        ),
        "active_basis_snapshot_hash_before": (
            manifest_case.get("active_basis_snapshot_hash") or ""
        ),
        "active_basis_journey_count_before": manifest_case.get(
            "active_basis_journey_count"
        ),
        "active_basis_payload_count_before": manifest_case.get(
            "active_basis_payload_count"
        ),
        "active_basis_fractional_journey_count_before": manifest_case.get(
            "active_basis_fractional_journey_count"
        ),
        "active_basis_lambda_sum_before": manifest_case.get(
            "active_basis_lambda_sum"
        ),
        "rmp_objective_before": manifest_case.get("rmp_objective_before"),
    }


def _candidate_component_context_features(
    manifest_case: dict[str, Any], candidate: dict[str, Any]
) -> dict[str, Any]:
    candidate_task_set = set(_task_tuple(candidate.get("task_set")))
    candidate_signature_key = _signature_key(candidate.get("signature"))
    candidate_cost = _as_float(candidate.get("cost"))
    candidate_true_rc = _as_float(candidate.get("true_reduced_cost"))

    pool_journeys = [
        journey
        for journey in (manifest_case.get("pool_journeys") or [])
        if isinstance(journey, dict)
    ]
    pool_sets = [
        set(_task_tuple(journey.get("task_set")))
        for journey in pool_journeys
        if _task_tuple(journey.get("task_set"))
    ]
    pool_signatures = {
        _signature_key(journey.get("signature"))
        for journey in pool_journeys
        if journey.get("signature") is not None
    }
    pool_signatures.update(
        _signature_key(signature)
        for signature in (manifest_case.get("pool_signatures") or [])
        if signature is not None
    )

    pool_task_counts: dict[int, int] = {}
    for task_set in pool_sets:
        for task in task_set:
            pool_task_counts[task] = pool_task_counts.get(task, 0) + 1
    task_freqs = [pool_task_counts.get(task, 0) for task in sorted(candidate_task_set)]
    pool_count = max(1, len(pool_sets))
    jaccards = [_jaccard(candidate_task_set, task_set) for task_set in pool_sets]
    exact_task_set_costs = [
        cost
        for journey, task_set in zip(pool_journeys, pool_sets)
        for cost in [_as_float(journey.get("cost"))]
        if task_set == candidate_task_set and cost is not None
    ]
    same_size_overlaps = [
        len(candidate_task_set & task_set)
        for task_set in pool_sets
        if len(task_set) == len(candidate_task_set)
    ]

    returned_candidates = [
        item for item in (manifest_case.get("candidates") or []) if isinstance(item, dict)
    ]
    returned_sets = [
        set(_task_tuple(item.get("task_set")))
        for item in returned_candidates
        if _task_tuple(item.get("task_set"))
    ]
    returned_task_union: set[int] = set()
    returned_task_counts: dict[int, int] = {}
    for task_set in returned_sets:
        returned_task_union.update(task_set)
        for task in task_set:
            returned_task_counts[task] = returned_task_counts.get(task, 0) + 1
    returned_other_jaccards = [
        _jaccard(candidate_task_set, task_set)
        for other, task_set in zip(returned_candidates, returned_sets)
        if str(other.get("candidate_id", "")) != str(candidate.get("candidate_id", ""))
    ]
    returned_true_rcs = [
        value
        for item in returned_candidates
        for value in [_as_float(item.get("true_reduced_cost"))]
        if value is not None
    ]
    returned_costs = [
        value
        for item in returned_candidates
        for value in [_as_float(item.get("cost"))]
        if value is not None
    ]
    returned_ids = [str(item.get("candidate_id", "")) for item in returned_candidates]
    candidate_id = str(candidate.get("candidate_id", ""))
    returned_index = returned_ids.index(candidate_id) if candidate_id in returned_ids else -1
    returned_task_freqs = [
        returned_task_counts.get(task, 0) for task in sorted(candidate_task_set)
    ]
    returned_forbidden_count = sum(
        int(bool(item.get("forbidden_signature"))) for item in returned_candidates
    )

    forbidden_signatures = {
        _signature_key(signature)
        for signature in (
            manifest_case.get("forbidden_signatures")
            or manifest_case.get("forbidden_journey_signatures")
            or []
        )
        if signature is not None
    }
    forbidden_payload_count = manifest_case.get("forbidden_signature_payload_count")
    forbidden_count = manifest_case.get("forbidden_signature_count")
    if forbidden_count is None:
        forbidden_count = len(forbidden_signatures)
    same_task_set_best_cost_delta = None
    if candidate_cost is not None and exact_task_set_costs:
        same_task_set_best_cost_delta = candidate_cost - min(exact_task_set_costs)
    min_true_rc = min(returned_true_rcs) if returned_true_rcs else None
    true_rc_gap = None
    if candidate_true_rc is not None and min_true_rc is not None:
        true_rc_gap = candidate_true_rc - min_true_rc
    return {
        "pool_candidate_task_freq_sum": sum(task_freqs),
        "pool_candidate_task_freq_mean": _average(task_freqs),
        "pool_candidate_task_freq_min": min(task_freqs) if task_freqs else 0,
        "pool_candidate_task_freq_max": max(task_freqs) if task_freqs else 0,
        "pool_candidate_task_freq_mean_fraction": _average(task_freqs) / pool_count,
        "pool_candidate_task_set_exact_count": sum(
            1 for task_set in pool_sets if task_set == candidate_task_set
        ),
        "pool_candidate_task_set_max_jaccard": max(jaccards) if jaccards else 0.0,
        "pool_candidate_task_set_mean_jaccard": _average(jaccards),
        "pool_candidate_task_set_near_050_count": sum(1 for value in jaccards if value >= 0.5),
        "pool_candidate_task_set_near_067_count": sum(
            1 for value in jaccards if value >= 2.0 / 3.0
        ),
        "pool_candidate_task_set_near_075_count": sum(1 for value in jaccards if value >= 0.75),
        "pool_candidate_task_set_same_size_overlap_max": (
            max(same_size_overlaps) if same_size_overlaps else 0
        ),
        "pool_candidate_same_task_set_best_cost_delta": same_task_set_best_cost_delta,
        "candidate_signature_in_pool": candidate_signature_key in pool_signatures,
        "candidate_forbidden_signature": bool(candidate.get("forbidden_signature"))
        or candidate_signature_key in forbidden_signatures,
        "forbidden_signature_count_before": forbidden_count,
        "forbidden_signature_payload_count_before": forbidden_payload_count,
        "forbidden_signature_payload_complete_before": bool(
            manifest_case.get("forbidden_signature_payload_complete")
        ),
        "forbidden_signature_payload_truncated_before": bool(
            manifest_case.get("forbidden_signature_payload_truncated")
        ),
        "explicit_forbidden_signature_list_available": bool(forbidden_signatures),
        "returned_batch_size": len(returned_candidates),
        "returned_batch_new_task_set_count": sum(
            int(bool(item.get("new_task_set"))) for item in returned_candidates
        ),
        "returned_batch_duplicate_signature_count": sum(
            int(bool(item.get("duplicate_signature"))) for item in returned_candidates
        ),
        "returned_batch_forbidden_signature_count": returned_forbidden_count,
        "returned_batch_forbidden_signature_fraction": (
            0.0
            if not returned_candidates
            else returned_forbidden_count / float(len(returned_candidates))
        ),
        "returned_batch_task_union_size": len(returned_task_union),
        "returned_candidate_index": returned_index,
        "returned_candidate_true_rc_rank": _rank(returned_true_rcs, candidate_true_rc),
        "returned_candidate_cost_rank": _rank(returned_costs, candidate_cost),
        "returned_candidate_task_freq_sum": sum(returned_task_freqs),
        "returned_candidate_task_freq_mean": _average(returned_task_freqs),
        "returned_candidate_task_set_max_jaccard_other": (
            max(returned_other_jaccards) if returned_other_jaccards else 0.0
        ),
        "returned_candidate_task_set_mean_jaccard_other": _average(
            returned_other_jaccards
        ),
        "returned_candidate_task_set_near_050_other_count": sum(
            1 for value in returned_other_jaccards if value >= 0.5
        ),
        "returned_candidate_task_set_near_067_other_count": sum(
            1 for value in returned_other_jaccards if value >= 2.0 / 3.0
        ),
        "returned_batch_min_true_rc": min_true_rc,
        "returned_batch_mean_true_rc": (
            None if not returned_true_rcs else _average(returned_true_rcs)
        ),
        "returned_batch_true_rc_gap_from_best": true_rc_gap,
    }


def _impact_class(delta: Any, *, eps: float = 1.0e-9) -> str:
    value = _as_float(delta)
    if value is None:
        return "unknown"
    if value < -eps:
        return "improved"
    if value > eps:
        return "worsened"
    return "noop"


def _manifest_cases(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(case.get("case_id", "")): case
        for case in manifest.get("cases", []) or []
        if case.get("case_id")
    }


def _replay_cases(replay: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(case.get("case_id", "")): case
        for case in replay.get("cases", []) or []
        if case.get("case_id")
    }


def _treatments_by_id(case: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(treatment.get("treatment_id", "")): treatment
        for treatment in case.get("treatments", []) or []
        if treatment.get("treatment_id")
    }


def _candidate_row(
    *,
    manifest_case: dict[str, Any],
    replay_case: dict[str, Any] | None,
    candidate: dict[str, Any],
    event_history_features: dict[str, Any],
) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_id", ""))
    treatments = _treatments_by_id(replay_case or {})
    single = treatments.get(f"single_{candidate_id}", {})
    delta = single.get("objective_delta_vs_control")
    context_features = _manifest_context_features(manifest_case)
    component_context_features = _candidate_component_context_features(
        manifest_case, candidate
    )
    return {
        "case_id": manifest_case.get("case_id", ""),
        "instance": manifest_case.get("instance", ""),
        "task_count": manifest_case.get("task_count"),
        "vehicle_count": manifest_case.get("vehicle_count"),
        "cg_iter": manifest_case.get("cg_iter"),
        "pricing_kind": manifest_case.get("pricing_kind", ""),
        "pricing_state": manifest_case.get("pricing_state", ""),
        "context_hash": manifest_case.get("context_hash", ""),
        **context_features,
        **event_history_features,
        "control_status": (replay_case or {}).get("control", {}).get("status", ""),
        "control_objective": (replay_case or {}).get("control", {}).get("objective"),
        "candidate_id": candidate_id,
        "task_set": _task_set_text(candidate.get("task_set")),
        "sequence": _sequence_text(candidate.get("sequence")),
        "true_reduced_cost": candidate.get("true_reduced_cost"),
        "cost": candidate.get("cost"),
        "new_task_set": bool(candidate.get("new_task_set")),
        "duplicate_signature": bool(candidate.get("duplicate_signature")),
        "forbidden_signature": bool(candidate.get("forbidden_signature")),
        "strict_replacement_by_cost": bool(candidate.get("strict_replacement_by_cost")),
        "active_support_changing": bool(candidate.get("active_support_changing")),
        "weak_replacement_or_duplicate": bool(candidate.get("weak_replacement_or_duplicate")),
        **component_context_features,
        "single_treatment_found": bool(single),
        "single_changed_journey_count": single.get("changed_journey_count"),
        "single_objective_delta": delta,
        "single_dual_l1_delta": single.get("dual_l1_delta_vs_control"),
        "single_no_op_treatment": single.get("no_op_treatment"),
        "single_impact_class": _impact_class(delta),
    }


def _treatment_rows(
    *,
    manifest_case: dict[str, Any],
    replay_case: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not replay_case:
        return rows
    for treatment in replay_case.get("treatments", []) or []:
        candidate_ids = list(treatment.get("candidate_ids", []) or [])
        delta = treatment.get("objective_delta_vs_control")
        rows.append(
            {
                "case_id": manifest_case.get("case_id", ""),
                "instance": manifest_case.get("instance", ""),
                "task_count": manifest_case.get("task_count"),
                "pricing_kind": manifest_case.get("pricing_kind", ""),
                "context_hash": manifest_case.get("context_hash", ""),
                "treatment_id": treatment.get("treatment_id", ""),
                "candidate_ids": ",".join(str(item) for item in candidate_ids),
                "candidate_count": len(candidate_ids),
                "changed_journey_count": treatment.get("changed_journey_count"),
                "objective": treatment.get("objective"),
                "objective_delta": delta,
                "dual_l1_delta": treatment.get("dual_l1_delta_vs_control"),
                "no_op_treatment": treatment.get("no_op_treatment"),
                "impact_class": _impact_class(delta),
            }
        )
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def analyze_replay_impact(
    manifest_path: Path,
    replay_result_path: Path,
    *,
    impact_eps: float = 1.0e-9,
) -> dict[str, Any]:
    manifest = _load_json(manifest_path, "replay_cases.json")
    replay = _load_json(replay_result_path, "replay_results.json")
    manifest_cases = _manifest_cases(manifest)
    replay_cases = _replay_cases(replay)
    candidate_rows: list[dict[str, Any]] = []
    treatment_rows: list[dict[str, Any]] = []
    missing_replay_case_ids: list[str] = []
    event_cache: dict[str, list[dict[str, Any]]] = {}
    for case_id, manifest_case in manifest_cases.items():
        replay_case = replay_cases.get(case_id)
        if replay_case is None:
            missing_replay_case_ids.append(case_id)
        source_file = Path(str(manifest_case.get("source_file") or ""))
        source_key = str(source_file)
        if source_key not in event_cache:
            event_cache[source_key] = _read_jsonl_events(source_file)
        event_history_features = _event_history_context_features(
            manifest_case, event_cache[source_key]
        )
        for candidate in manifest_case.get("candidates", []) or []:
            candidate_rows.append(
                _candidate_row(
                    manifest_case=manifest_case,
                    replay_case=replay_case,
                    candidate=candidate,
                    event_history_features=event_history_features,
                )
            )
        treatment_rows.extend(
            _treatment_rows(manifest_case=manifest_case, replay_case=replay_case)
        )

    single_rows = [row for row in candidate_rows if row.get("single_treatment_found")]
    high_impact_rows = [
        row
        for row in single_rows
        if (_as_float(row.get("single_objective_delta"), 0.0) or 0.0) < -impact_eps
    ]
    noop_rows = [row for row in single_rows if row.get("single_impact_class") == "noop"]
    worsened_rows = [row for row in single_rows if row.get("single_impact_class") == "worsened"]
    unknown_rows = [row for row in single_rows if row.get("single_impact_class") == "unknown"]
    full_batch_rows = [
        row for row in treatment_rows if row.get("treatment_id") == "full_returned_batch"
    ]
    full_batch_improved = [
        row
        for row in full_batch_rows
        if (_as_float(row.get("objective_delta"), 0.0) or 0.0) < -impact_eps
    ]
    deltas = [
        _as_float(row.get("objective_delta"))
        for row in treatment_rows
        if row.get("treatment_id") != "control_no_addition"
    ]
    finite_deltas = [value for value in deltas if value is not None]
    replay_control_statuses = [
        str(case.get("control", {}).get("status", ""))
        for case in replay_cases.values()
    ]
    control_solved_case_count = sum(
        1 for status in replay_control_statuses if status == "OPTIMAL"
    )
    checks = {
        "has_manifest_cases": bool(manifest_cases),
        "has_replay_cases": bool(replay_cases),
        "all_manifest_cases_have_replay_case": not missing_replay_case_ids,
        "all_replay_controls_solved": (
            bool(replay_cases) and control_solved_case_count == len(replay_cases)
        ),
        "has_candidate_rows": bool(candidate_rows),
        "all_single_candidates_have_treatment": len(single_rows) == len(candidate_rows),
        "all_single_candidates_have_finite_delta": (
            len(single_rows) == len(candidate_rows) and not unknown_rows
        ),
        "replay_is_no_certificate_effect": bool(
            (replay.get("checks") or {}).get("all_replay_is_no_certificate_effect", False)
        ),
    }
    summary = {
        "schema_version": "counterfactual_replay_impact_dataset_v1",
        "manifest_path": str(_json_path(manifest_path, "replay_cases.json")),
        "replay_result_path": str(_json_path(replay_result_path, "replay_results.json")),
        "case_count": len(manifest_cases),
        "replay_case_count": len(replay_cases),
        "candidate_row_count": len(candidate_rows),
        "single_candidate_with_replay_count": len(single_rows),
        "high_impact_candidate_count": len(high_impact_rows),
        "noop_candidate_count": len(noop_rows),
        "worsened_candidate_count": len(worsened_rows),
        "unknown_candidate_count": len(unknown_rows),
        "control_solved_case_count": control_solved_case_count,
        "control_unsolved_case_count": max(0, len(replay_cases) - control_solved_case_count),
        "full_batch_count": len(full_batch_rows),
        "full_batch_improved_count": len(full_batch_improved),
        "best_objective_delta": None if not finite_deltas else min(finite_deltas),
        "missing_replay_case_ids": missing_replay_case_ids,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "interpretation": (
            "This dataset measures local RMP treatment impact for captured exact "
            "contexts only. It is not a certificate, solver speedup proof, or "
            "production selector."
        ),
        "candidate_rows": candidate_rows,
        "treatment_rows": treatment_rows,
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True, help="replay_cases.json or its directory.")
    parser.add_argument(
        "--replay-result",
        type=Path,
        required=True,
        help="replay_results.json or its directory.",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    result = analyze_replay_impact(args.manifest, args.replay_result)
    candidate_rows = list(result.pop("candidate_rows"))
    treatment_rows = list(result.pop("treatment_rows"))
    result["candidate_rows_csv"] = str(args.output_dir / "candidate_impact_rows.csv")
    result["treatment_rows_csv"] = str(args.output_dir / "treatment_impact_rows.csv")
    _write_csv(args.output_dir / "candidate_impact_rows.csv", candidate_rows)
    _write_csv(args.output_dir / "treatment_impact_rows.csv", treatment_rows)
    (args.output_dir / "summary.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

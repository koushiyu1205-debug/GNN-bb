#!/usr/bin/env python3
"""Build a read-only returned-batch trajectory dataset from existing run logs.

The script intentionally does not call the solver.  It reads summary rows plus
JSONL events and emits stage-level features/labels for calibration-only selector
analysis.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


DEFAULT_RESULT_DIRS = (
    "BPC_future/results/sharded_pulse_phase10b_profile_dp_state_cap_sensitivity_smoke_20260613",
    "BPC_future/results/sharded_pulse_phase10d_profile_dp_mask_hotspot_repeat_smoke_20260613",
    "BPC_future/results/sharded_pulse_phase10e_profile_dp_ordering_attribution_smoke_20260613",
    "BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613",
    "BPC_future/results/sharded_pulse_phase11a_profile_pricing_time_sensitivity_smoke_20260613",
    "BPC_future/results/sharded_pulse_phase9j_rmp_dual_stabilization_repeat_ab_smoke_20260613",
    "BPC_future/results/sharded_pulse_phase9k_rmp_dual_stabilization_hardset_ab_smoke_20260613",
)


FIELDNAMES = (
    "dataset",
    "instance",
    "scale",
    "profile",
    "repeat_index",
    "run_improvement_class",
    "run_status",
    "run_primal",
    "run_wall_time",
    "cg_iter",
    "pricing_kind",
    "pricing_state",
    "pricing_reason",
    "best_rc",
    "selected_count",
    "materialized_count",
    "returned_count",
    "unmaterialized_count",
    "negative_sample_count",
    "returned_union_size",
    "returned_avg_size",
    "returned_pair_overlap",
    "returned_pair_jaccard",
    "active_sample_count_before",
    "active_avg_overlap",
    "active_avg_jaccard",
    "active_redundant_frac",
    "active_bridge_frac",
    "active_disjoint_frac",
    "active_hash_before",
    "active_fractional_sum_before",
    "active_fractional_count_before",
    "addition_requested_count",
    "addition_changed_count",
    "addition_new_count",
    "addition_replacement_count",
    "addition_active_changed_count",
    "addition_inactive_changed_count",
    "addition_productivity_class",
    "rmp_objective_before",
    "rmp_objective_after",
    "next_rmp_objective_delta",
    "active_hash_after",
    "active_hash_changed_after",
    "zero_fractional_within2",
    "incumbent_within2",
    "next_negative_count",
    "next_incomplete_count",
    "returned_sequence_count",
    "returned_avg_sequence_len",
    "returned_first_task_unique_count",
    "returned_avg_start_time",
    "returned_start_time_zero_frac",
    "returned_arc_count",
    "returned_low_time_arc_frac",
    "returned_low_risk_arc_frac",
    "returned_low_energy_arc_frac",
    "returned_sequences",
    "returned_arc_families",
    "returned_task_sets",
)

CANDIDATE_FIELDNAMES = (
    "dataset",
    "instance",
    "scale",
    "profile",
    "repeat_index",
    "run_improvement_class",
    "run_status",
    "run_primal",
    "run_wall_time",
    "cg_iter",
    "candidate_index",
    "candidate_position_frac",
    "candidate_task_set",
    "candidate_sequence",
    "candidate_first_task",
    "candidate_sequence_len",
    "candidate_start_time",
    "candidate_arc_count",
    "candidate_low_time_arc_frac",
    "candidate_low_risk_arc_frac",
    "candidate_low_energy_arc_frac",
    "candidate_arc_families",
    "batch_returned_count",
    "batch_pair_overlap",
    "batch_pair_jaccard",
    "batch_active_avg_overlap",
    "batch_active_redundant_frac",
    "batch_active_bridge_frac",
    "candidate_active_overlap",
    "candidate_active_jaccard",
    "candidate_active_relation",
    "candidate_added",
    "candidate_new_task_set",
    "candidate_replacement_task_set",
    "candidate_active_changed",
    "candidate_inactive_changed",
    "candidate_future_active_within2",
    "candidate_future_active_value",
    "incumbent_within2",
    "zero_fractional_within2",
    "next_negative_count",
    "next_incomplete_count",
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                records.append(record)
    return records


def _as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number):
        return None
    return number


def _as_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _normalize_task_set(value: Any) -> tuple[int, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return ()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            text = text.strip("[](){}")
            if not text:
                return ()
            parts = [part.strip() for part in text.replace("|", ",").split(",")]
            return tuple(sorted(int(part) for part in parts if part))
        return _normalize_task_set(parsed)
    if isinstance(value, dict):
        for key in ("tasks", "task_set", "taskSet"):
            if key in value:
                return _normalize_task_set(value[key])
        return ()
    if isinstance(value, (list, tuple)):
        if len(value) == 3 and isinstance(value[2], (list, tuple)):
            return _normalize_task_set(value[2])
        items: list[int] = []
        for item in value:
            if isinstance(item, bool):
                continue
            if isinstance(item, (int, float)) and float(item).is_integer():
                items.append(int(item))
            elif isinstance(item, str) and item.strip().lstrip("-").isdigit():
                items.append(int(item.strip()))
        return tuple(sorted(set(items)))
    return ()


def _task_sets(raw: Any) -> list[tuple[int, ...]]:
    if not isinstance(raw, (list, tuple)):
        return []
    result: list[tuple[int, ...]] = []
    for item in raw:
        task_set = _normalize_task_set(item)
        if task_set:
            result.append(task_set)
    return result


def _task_set_string(task_set: tuple[int, ...]) -> str:
    return ",".join(str(task) for task in task_set)


def _task_sets_string(task_sets: Iterable[tuple[int, ...]]) -> str:
    return "|".join(_task_set_string(task_set) for task_set in task_sets)


def _parse_signature_samples(raw: Any) -> dict[str, Any]:
    candidates = _parse_signature_candidates(raw)
    if not candidates:
        return _empty_signature_features()
    sequence_strings: list[str] = []
    arc_family_strings: list[str] = []
    sequence_lengths: list[float] = []
    first_tasks: set[int] = set()
    start_times: list[float] = []
    arc_families: list[str] = []
    for candidate in candidates:
        sequence = candidate["sequence"]
        families = candidate["arc_families"]
        sequence_strings.append(_task_set_string(sequence))
        arc_family_strings.append(",".join(families))
        sequence_lengths.append(float(len(sequence)))
        if sequence:
            first_tasks.add(sequence[0])
        start_time = _as_float(candidate["start_time"])
        if start_time is not None:
            start_times.append(start_time)
        arc_families.extend(families)
    arc_count = len(arc_families)
    family_counts = Counter(arc_families)
    zero_starts = sum(1 for value in start_times if abs(value) <= 1e-9)
    return {
        "returned_sequence_count": len(sequence_strings),
        "returned_avg_sequence_len": _mean(sequence_lengths),
        "returned_first_task_unique_count": len(first_tasks),
        "returned_avg_start_time": _mean(start_times),
        "returned_start_time_zero_frac": 0.0 if not start_times else zero_starts / len(start_times),
        "returned_arc_count": arc_count,
        "returned_low_time_arc_frac": 0.0 if arc_count <= 0 else family_counts["low_time"] / arc_count,
        "returned_low_risk_arc_frac": 0.0 if arc_count <= 0 else family_counts["low_risk"] / arc_count,
        "returned_low_energy_arc_frac": 0.0 if arc_count <= 0 else family_counts["low_energy"] / arc_count,
        "returned_sequences": "|".join(sequence_strings[:8]),
        "returned_arc_families": "|".join(arc_family_strings[:8]),
    }


def _parse_signature_candidates(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, (list, tuple)):
        return []
    candidates: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            continue
        try:
            parsed = ast.literal_eval(item)
        except (SyntaxError, ValueError):
            continue
        if not isinstance(parsed, (list, tuple)):
            continue
        journey_sequence: list[int] = []
        journey_families: list[str] = []
        start_times: list[float] = []
        for trip in parsed:
            if not isinstance(trip, (list, tuple)) or len(trip) < 3:
                continue
            sequence = [int(task) for task in trip[0] if isinstance(task, int)]
            arcs = [str(arc) for arc in trip[1] if isinstance(arc, str)]
            start_time = _as_float(trip[2])
            if sequence:
                journey_sequence.extend(sequence)
            if start_time is not None:
                start_times.append(start_time)
            for arc in arcs:
                family = _arc_family(arc)
                if family:
                    journey_families.append(family)
        if journey_sequence:
            candidates.append(
                {
                    "sequence": tuple(journey_sequence),
                    "task_set": tuple(sorted(set(journey_sequence))),
                    "start_time": _mean(start_times),
                    "arc_families": tuple(journey_families),
                }
            )
    return candidates


def _empty_signature_features() -> dict[str, Any]:
    return {
        "returned_sequence_count": 0,
        "returned_avg_sequence_len": 0.0,
        "returned_first_task_unique_count": 0,
        "returned_avg_start_time": 0.0,
        "returned_start_time_zero_frac": 0.0,
        "returned_arc_count": 0,
        "returned_low_time_arc_frac": 0.0,
        "returned_low_risk_arc_frac": 0.0,
        "returned_low_energy_arc_frac": 0.0,
        "returned_sequences": "",
        "returned_arc_families": "",
    }


def _arc_family(arc: str) -> str:
    parts = arc.split(":")
    if len(parts) >= 2:
        return parts[-2]
    return ""


def _overlap(a: tuple[int, ...], b: tuple[int, ...]) -> tuple[int, float]:
    if not a or not b:
        return (0, 0.0)
    set_a = set(a)
    set_b = set(b)
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return (inter, 0.0 if union <= 0 else inter / union)


def _pair_metrics(task_sets: list[tuple[int, ...]]) -> tuple[float, float]:
    if len(task_sets) < 2:
        return (0.0, 0.0)
    overlaps: list[float] = []
    jaccards: list[float] = []
    for i, left in enumerate(task_sets):
        for right in task_sets[i + 1 :]:
            overlap, jaccard = _overlap(left, right)
            overlaps.append(float(overlap) / max(1.0, float(min(len(left), len(right)))))
            jaccards.append(jaccard)
    return (_mean(overlaps), _mean(jaccards))


def _mean(values: Iterable[float]) -> float:
    items = list(values)
    if not items:
        return 0.0
    return sum(items) / len(items)


def _active_relation_features(
    returned: list[tuple[int, ...]], active: list[tuple[int, ...]]
) -> dict[str, float]:
    if not returned:
        return {
            "active_avg_overlap": 0.0,
            "active_avg_jaccard": 0.0,
            "active_redundant_frac": 0.0,
            "active_bridge_frac": 0.0,
            "active_disjoint_frac": 0.0,
        }
    best_overlaps: list[float] = []
    best_jaccards: list[float] = []
    redundant = 0
    bridge = 0
    disjoint = 0
    for task_set in returned:
        best_overlap = 0
        best_jaccard = 0.0
        exact = False
        for active_set in active:
            overlap, jaccard = _overlap(task_set, active_set)
            if overlap > best_overlap or (overlap == best_overlap and jaccard > best_jaccard):
                best_overlap = overlap
                best_jaccard = jaccard
            if task_set == active_set:
                exact = True
        best_overlaps.append(best_overlap / max(1.0, float(len(task_set))))
        best_jaccards.append(best_jaccard)
        if exact:
            redundant += 1
        elif best_overlap > 0:
            bridge += 1
        else:
            disjoint += 1
    denom = float(len(returned))
    return {
        "active_avg_overlap": _mean(best_overlaps),
        "active_avg_jaccard": _mean(best_jaccards),
        "active_redundant_frac": redundant / denom,
        "active_bridge_frac": bridge / denom,
        "active_disjoint_frac": disjoint / denom,
    }


def _active_relation_for_task_set(
    task_set: tuple[int, ...], active: list[tuple[int, ...]]
) -> dict[str, Any]:
    best_overlap = 0
    best_jaccard = 0.0
    exact = False
    for active_set in active:
        overlap, jaccard = _overlap(task_set, active_set)
        if overlap > best_overlap or (overlap == best_overlap and jaccard > best_jaccard):
            best_overlap = overlap
            best_jaccard = jaccard
        if task_set == active_set:
            exact = True
    if exact:
        relation = "same_task_set"
    elif best_overlap > 0:
        relation = "overlapping_task_set"
    else:
        relation = "disjoint_task_set"
    return {
        "candidate_active_overlap": best_overlap / max(1.0, float(len(task_set))),
        "candidate_active_jaccard": best_jaccard,
        "candidate_active_relation": relation,
    }


def _events_by_iter(records: list[dict[str, Any]], event: str) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record.get("event") != event:
            continue
        grouped[_as_int(record.get("cg_iter"))].append(record)
    return grouped


def _first_event_after(
    grouped: dict[int, list[dict[str, Any]]], cg_iter: int, max_offset: int
) -> dict[str, Any] | None:
    for offset in range(1, max_offset + 1):
        items = grouped.get(cg_iter + offset, [])
        if items:
            return items[0]
    return None


def _pool_before(pool_by_iter: dict[int, list[dict[str, Any]]], cg_iter: int) -> dict[str, Any]:
    items = pool_by_iter.get(cg_iter, [])
    return items[-1] if items else {}


def _pool_after(pool_by_iter: dict[int, list[dict[str, Any]]], cg_iter: int) -> dict[str, Any]:
    for next_iter in range(cg_iter + 1, cg_iter + 4):
        items = pool_by_iter.get(next_iter, [])
        if items:
            return items[-1]
    return {}


def _addition_for_iter(additions_by_iter: dict[int, list[dict[str, Any]]], cg_iter: int) -> dict[str, Any]:
    items = additions_by_iter.get(cg_iter, [])
    return items[0] if items else {}


def _addition_task_set_labels(addition: dict[str, Any], task_set: tuple[int, ...]) -> dict[str, bool]:
    changed = set(_task_sets(addition.get("changed_task_set_samples")))
    new = set(_task_sets(addition.get("new_task_set_samples")))
    replacement = set(_task_sets(addition.get("replacement_task_set_samples")))
    active_changed = set(_task_sets(addition.get("active_changed_task_set_samples")))
    inactive_changed = set(_task_sets(addition.get("inactive_changed_task_set_samples")))
    return {
        "candidate_added": task_set in changed,
        "candidate_new_task_set": task_set in new,
        "candidate_replacement_task_set": task_set in replacement,
        "candidate_active_changed": task_set in active_changed,
        "candidate_inactive_changed": task_set in inactive_changed,
    }


def _future_active_label(
    pool_by_iter: dict[int, list[dict[str, Any]]],
    cg_iter: int,
    task_set: tuple[int, ...],
    max_offset: int = 2,
) -> dict[str, Any]:
    best_value: float | None = None
    for offset in range(1, max_offset + 1):
        for record in pool_by_iter.get(cg_iter + offset, []):
            for item in record.get("pool_active_top_task_set_value_samples", []) or []:
                active_task_set = _normalize_task_set(item)
                if active_task_set != task_set:
                    continue
                value = _as_float(item[0] if isinstance(item, (list, tuple)) and item else None)
                if best_value is None or (value is not None and value > best_value):
                    best_value = value
    return {
        "candidate_future_active_within2": best_value is not None,
        "candidate_future_active_value": "" if best_value is None else best_value,
    }


def _count_future_pricing(
    pricing_by_iter: dict[int, list[dict[str, Any]]], cg_iter: int, max_offset: int
) -> tuple[int, int]:
    negative = 0
    incomplete = 0
    for offset in range(1, max_offset + 1):
        for record in pricing_by_iter.get(cg_iter + offset, []):
            state = str(record.get("pricing_state") or "")
            status = str(record.get("status") or "")
            if state == "FOUND_NEGATIVE":
                negative += 1
            if "INCOMPLETE" in state or status == "INCOMPLETE":
                incomplete += 1
    return negative, incomplete


def _has_incumbent_within(records: list[dict[str, Any]], cg_iter: int, max_offset: int) -> bool:
    for record in records:
        if record.get("event") != "journey_certificate_candidate_updated":
            continue
        record_iter = _as_int(record.get("cg_iter"))
        if cg_iter < record_iter <= cg_iter + max_offset:
            return True
    return False


def _has_zero_fractional_within(
    pool_by_iter: dict[int, list[dict[str, Any]]], cg_iter: int, max_offset: int
) -> bool:
    for offset in range(1, max_offset + 1):
        for record in pool_by_iter.get(cg_iter + offset, []):
            value = _as_float(record.get("pool_active_fractional_value_sum"))
            if value is not None and abs(value) <= 1e-9:
                return True
    return False


def _extract_rows_from_run(
    *,
    dataset: str,
    summary_row: dict[str, str],
    records: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rmp_by_iter = _events_by_iter(records, "journey_rmp")
    pool_by_iter = _events_by_iter(records, "journey_pool_structure_diagnostics")
    pricing_by_iter = _events_by_iter(records, "journey_pricing")
    additions_by_iter = _events_by_iter(records, "journey_column_addition")
    rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    for pricing in records:
        if pricing.get("event") != "journey_pricing":
            continue
        if str(pricing.get("pricing_kind") or "") != "heuristic":
            continue
        returned = _task_sets(
            pricing.get("diagnostic_selected_returned_task_set_samples")
            or pricing.get("negative_journey_task_set_samples")
        )
        if not returned:
            continue
        cg_iter = _as_int(pricing.get("cg_iter"))
        pool_before = _pool_before(pool_by_iter, cg_iter)
        pool_after = _pool_after(pool_by_iter, cg_iter)
        active = _task_sets(pool_before.get("pool_active_top_task_set_value_samples"))
        active_features = _active_relation_features(returned, active)
        signature_features = _parse_signature_samples(pricing.get("negative_journey_signature_samples"))
        signature_candidates = _parse_signature_candidates(pricing.get("negative_journey_signature_samples"))
        pair_overlap, pair_jaccard = _pair_metrics(returned)
        addition = _addition_for_iter(additions_by_iter, cg_iter)
        rmp_before = rmp_by_iter.get(cg_iter, [{}])[0]
        rmp_after = _first_event_after(rmp_by_iter, cg_iter, 2) or {}
        before_obj = _as_float(rmp_before.get("objective"))
        after_obj = _as_float(rmp_after.get("objective"))
        negative_count, incomplete_count = _count_future_pricing(pricing_by_iter, cg_iter, 2)
        union = sorted({task for task_set in returned for task in task_set})
        rows.append(
            {
                "dataset": dataset,
                "instance": summary_row.get("instance", ""),
                "scale": summary_row.get("scale", ""),
                "profile": summary_row.get("profile", ""),
                "repeat_index": summary_row.get("repeat_index", ""),
                "run_improvement_class": summary_row.get("improvement_class", ""),
                "run_status": summary_row.get("status", ""),
                "run_primal": summary_row.get("primal", ""),
                "run_wall_time": summary_row.get("wall_time", ""),
                "cg_iter": cg_iter,
                "pricing_kind": pricing.get("pricing_kind", ""),
                "pricing_state": pricing.get("pricing_state", ""),
                "pricing_reason": pricing.get("reason", ""),
                "best_rc": pricing.get("best_reduced_cost", ""),
                "selected_count": len(_task_sets(pricing.get("diagnostic_selected_task_set_samples"))),
                "materialized_count": len(
                    _task_sets(pricing.get("diagnostic_selected_materialized_task_set_samples"))
                ),
                "returned_count": len(returned),
                "unmaterialized_count": len(
                    _task_sets(pricing.get("diagnostic_selected_unmaterialized_task_set_samples"))
                ),
                "negative_sample_count": len(_task_sets(pricing.get("negative_journey_task_set_samples"))),
                "returned_union_size": len(union),
                "returned_avg_size": _mean(float(len(task_set)) for task_set in returned),
                "returned_pair_overlap": pair_overlap,
                "returned_pair_jaccard": pair_jaccard,
                "active_sample_count_before": len(active),
                **active_features,
                "active_hash_before": pool_before.get("pool_active_task_set_hash", ""),
                "active_fractional_sum_before": pool_before.get("pool_active_fractional_value_sum", ""),
                "active_fractional_count_before": pool_before.get("pool_active_fractional_journey_count", ""),
                "addition_requested_count": addition.get("requested_task_set_count", ""),
                "addition_changed_count": addition.get("changed_task_set_count", ""),
                "addition_new_count": addition.get("new_task_set_count", ""),
                "addition_replacement_count": addition.get("replacement_task_set_count", ""),
                "addition_active_changed_count": addition.get("active_changed_task_set_count", ""),
                "addition_inactive_changed_count": addition.get("inactive_changed_task_set_count", ""),
                "addition_productivity_class": addition.get("addition_productivity_class", ""),
                "rmp_objective_before": "" if before_obj is None else before_obj,
                "rmp_objective_after": "" if after_obj is None else after_obj,
                "next_rmp_objective_delta": ""
                if before_obj is None or after_obj is None
                else after_obj - before_obj,
                "active_hash_after": pool_after.get("pool_active_task_set_hash", ""),
                "active_hash_changed_after": bool(
                    pool_before.get("pool_active_task_set_hash")
                    and pool_after.get("pool_active_task_set_hash")
                    and pool_before.get("pool_active_task_set_hash") != pool_after.get("pool_active_task_set_hash")
                ),
                "zero_fractional_within2": _has_zero_fractional_within(pool_by_iter, cg_iter, 2),
                "incumbent_within2": _has_incumbent_within(records, cg_iter, 2),
                "next_negative_count": negative_count,
                "next_incomplete_count": incomplete_count,
                **signature_features,
                "returned_task_sets": _task_sets_string(returned),
            }
        )
        candidate_rows.extend(
            _candidate_rows_for_stage(
                dataset=dataset,
                summary_row=summary_row,
                pricing=pricing,
                candidates=signature_candidates,
                active=active,
                addition=addition,
                pool_by_iter=pool_by_iter,
                cg_iter=cg_iter,
                incumbent_within2=_has_incumbent_within(records, cg_iter, 2),
                zero_fractional_within2=_has_zero_fractional_within(pool_by_iter, cg_iter, 2),
                next_negative_count=negative_count,
                next_incomplete_count=incomplete_count,
                batch_returned_count=len(signature_candidates),
                batch_pair_overlap=pair_overlap,
                batch_pair_jaccard=pair_jaccard,
                batch_active_features=active_features,
            )
        )
    return rows, candidate_rows


def _candidate_rows_for_stage(
    *,
    dataset: str,
    summary_row: dict[str, str],
    pricing: dict[str, Any],
    candidates: list[dict[str, Any]],
    active: list[tuple[int, ...]],
    addition: dict[str, Any],
    pool_by_iter: dict[int, list[dict[str, Any]]],
    cg_iter: int,
    incumbent_within2: bool,
    zero_fractional_within2: bool,
    next_negative_count: int,
    next_incomplete_count: int,
    batch_returned_count: int,
    batch_pair_overlap: float,
    batch_pair_jaccard: float,
    batch_active_features: dict[str, float],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates):
        sequence = tuple(candidate.get("sequence") or ())
        task_set = tuple(candidate.get("task_set") or ())
        if not task_set:
            continue
        families = tuple(candidate.get("arc_families") or ())
        family_counts = Counter(families)
        arc_count = len(families)
        row: dict[str, Any] = {
            "dataset": dataset,
            "instance": summary_row.get("instance", ""),
            "scale": summary_row.get("scale", ""),
            "profile": summary_row.get("profile", ""),
            "repeat_index": summary_row.get("repeat_index", ""),
            "run_improvement_class": summary_row.get("improvement_class", ""),
            "run_status": summary_row.get("status", ""),
            "run_primal": summary_row.get("primal", ""),
            "run_wall_time": summary_row.get("wall_time", ""),
            "cg_iter": cg_iter,
            "candidate_index": index,
            "candidate_position_frac": 0.0
            if batch_returned_count <= 1
            else index / float(batch_returned_count - 1),
            "candidate_task_set": _task_set_string(task_set),
            "candidate_sequence": _task_set_string(sequence),
            "candidate_first_task": sequence[0] if sequence else "",
            "candidate_sequence_len": len(sequence),
            "candidate_start_time": candidate.get("start_time", ""),
            "candidate_arc_count": arc_count,
            "candidate_low_time_arc_frac": 0.0 if arc_count <= 0 else family_counts["low_time"] / arc_count,
            "candidate_low_risk_arc_frac": 0.0 if arc_count <= 0 else family_counts["low_risk"] / arc_count,
            "candidate_low_energy_arc_frac": 0.0 if arc_count <= 0 else family_counts["low_energy"] / arc_count,
            "candidate_arc_families": ",".join(families),
            "batch_returned_count": batch_returned_count,
            "batch_pair_overlap": batch_pair_overlap,
            "batch_pair_jaccard": batch_pair_jaccard,
            "batch_active_avg_overlap": batch_active_features.get("active_avg_overlap", 0.0),
            "batch_active_redundant_frac": batch_active_features.get("active_redundant_frac", 0.0),
            "batch_active_bridge_frac": batch_active_features.get("active_bridge_frac", 0.0),
            "incumbent_within2": incumbent_within2,
            "zero_fractional_within2": zero_fractional_within2,
            "next_negative_count": next_negative_count,
            "next_incomplete_count": next_incomplete_count,
        }
        row.update(_active_relation_for_task_set(task_set, active))
        row.update(_addition_task_set_labels(addition, task_set))
        row.update(_future_active_label(pool_by_iter, cg_iter, task_set, 2))
        rows.append(row)
    return rows


def _iter_summary_rows(result_dirs: list[Path]) -> Iterable[tuple[str, dict[str, str]]]:
    for result_dir in result_dirs:
        summary_path = result_dir / "summary.csv"
        if not summary_path.exists():
            continue
        dataset = result_dir.name
        for row in _read_csv(summary_path):
            yield dataset, row


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    label_counts = Counter(str(row.get("run_improvement_class", "")) for row in rows)
    dataset_counts = Counter(str(row.get("dataset", "")) for row in rows)
    scale_counts = Counter(str(row.get("scale", "")) for row in rows)
    improved = [row for row in rows if row.get("run_improvement_class") == "improved"]
    worsened = [row for row in rows if row.get("run_improvement_class") == "worsened"]
    twenty = [row for row in rows if str(row.get("scale", "")) == "20"]
    small = [row for row in rows if str(row.get("scale", "")) in {"5", "10"}]
    twenty_strict = [
        row for row in twenty if row.get("run_improvement_class") in {"improved", "worsened"}
    ]
    twenty_improved = [row for row in twenty_strict if row.get("run_improvement_class") == "improved"]
    twenty_worsened = [row for row in twenty_strict if row.get("run_improvement_class") == "worsened"]

    def avg(group: list[dict[str, Any]], key: str) -> float | None:
        values = [_as_float(row.get(key)) for row in group]
        clean = [value for value in values if value is not None]
        return None if not clean else sum(clean) / len(clean)

    def feature_avg(group: list[dict[str, Any]]) -> dict[str, float | None]:
        return {
            "returned_count": avg(group, "returned_count"),
            "active_avg_overlap": avg(group, "active_avg_overlap"),
            "active_redundant_frac": avg(group, "active_redundant_frac"),
            "active_bridge_frac": avg(group, "active_bridge_frac"),
            "returned_pair_overlap": avg(group, "returned_pair_overlap"),
            "returned_avg_sequence_len": avg(group, "returned_avg_sequence_len"),
            "returned_first_task_unique_count": avg(group, "returned_first_task_unique_count"),
            "returned_avg_start_time": avg(group, "returned_avg_start_time"),
            "returned_start_time_zero_frac": avg(group, "returned_start_time_zero_frac"),
            "returned_low_time_arc_frac": avg(group, "returned_low_time_arc_frac"),
            "returned_low_risk_arc_frac": avg(group, "returned_low_risk_arc_frac"),
            "returned_low_energy_arc_frac": avg(group, "returned_low_energy_arc_frac"),
            "next_incomplete_count": avg(group, "next_incomplete_count"),
            "incumbent_within2": avg(group, "incumbent_within2"),
            "zero_fractional_within2": avg(group, "zero_fractional_within2"),
        }

    validation = _leave_one_dataset_validation(twenty_strict)
    return {
        "stage_rows": len(rows),
        "datasets": dict(sorted(dataset_counts.items())),
        "scales": dict(sorted(scale_counts.items())),
        "run_improvement_class_counts": dict(sorted(label_counts.items())),
        "improved_feature_avg": feature_avg(improved),
        "worsened_feature_avg": feature_avg(worsened),
        "small_stage_rows": len(small),
        "small_label_counts": dict(
            sorted(Counter(str(row.get("run_improvement_class", "")) for row in small).items())
        ),
        "twenty_stage_rows": len(twenty),
        "twenty_label_counts": dict(
            sorted(Counter(str(row.get("run_improvement_class", "")) for row in twenty).items())
        ),
        "twenty_strict_stage_rows": len(twenty_strict),
        "twenty_strict_label_counts": dict(
            sorted(Counter(str(row.get("run_improvement_class", "")) for row in twenty_strict).items())
        ),
        "twenty_strict_improved_feature_avg": feature_avg(twenty_improved),
        "twenty_strict_worsened_feature_avg": feature_avg(twenty_worsened),
        "twenty_strict_leave_one_dataset_validation": validation,
    }


def _leave_one_dataset_validation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    features = (
        "returned_count",
        "active_avg_overlap",
        "active_avg_jaccard",
        "active_redundant_frac",
        "active_bridge_frac",
        "returned_pair_overlap",
        "returned_pair_jaccard",
        "returned_avg_sequence_len",
        "returned_first_task_unique_count",
        "returned_start_time_zero_frac",
        "returned_low_time_arc_frac",
        "returned_low_risk_arc_frac",
        "returned_low_energy_arc_frac",
    )
    datasets = sorted({str(row.get("dataset", "")) for row in rows if row.get("dataset")})
    total = tp = fp = tn = fn = 0
    rules: list[dict[str, Any]] = []
    for held_out in datasets:
        train = [row for row in rows if row.get("dataset") != held_out]
        test = [row for row in rows if row.get("dataset") == held_out]
        rule = _best_threshold_rule(train, features)
        if rule is None:
            continue
        metrics = _score_threshold_rule(test, rule)
        total += metrics["n"]
        tp += metrics["tp"]
        fp += metrics["fp"]
        tn += metrics["tn"]
        fn += metrics["fn"]
        rules.append({"held_out": held_out, **rule, **metrics})
    accuracy = None if total <= 0 else (tp + tn) / total
    return {
        "total": total,
        "accuracy": accuracy,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "rules": rules,
    }


def _best_threshold_rule(rows: list[dict[str, Any]], features: tuple[str, ...]) -> dict[str, Any] | None:
    best: tuple[float, int, int, int, int, str, str, float] | None = None
    for feature in features:
        values = sorted(
            {
                value
                for row in rows
                for value in [_as_float(row.get(feature))]
                if value is not None
            }
        )
        for threshold in values:
            for operator in ("<=", ">="):
                metrics = _score_threshold_rule(rows, {"feature": feature, "operator": operator, "threshold": threshold})
                if metrics["n"] <= 0:
                    continue
                score = metrics["accuracy"]
                candidate = (
                    score,
                    metrics["tp"],
                    metrics["tn"],
                    -metrics["fp"],
                    -metrics["fn"],
                    feature,
                    operator,
                    threshold,
                )
                if best is None or candidate > best:
                    best = candidate
    if best is None:
        return None
    _, _, _, _, _, feature, operator, threshold = best
    return {"feature": feature, "operator": operator, "threshold": threshold}


def _score_threshold_rule(rows: list[dict[str, Any]], rule: dict[str, Any]) -> dict[str, Any]:
    feature = str(rule["feature"])
    operator = str(rule["operator"])
    threshold = float(rule["threshold"])
    tp = fp = tn = fn = 0
    for row in rows:
        value = _as_float(row.get(feature))
        if value is None:
            continue
        prediction = value <= threshold if operator == "<=" else value >= threshold
        actual = row.get("run_improvement_class") == "improved"
        if prediction and actual:
            tp += 1
        elif prediction and not actual:
            fp += 1
        elif not prediction and not actual:
            tn += 1
        else:
            fn += 1
    n = tp + fp + tn + fn
    accuracy = 0.0 if n <= 0 else (tp + tn) / n
    return {"n": n, "accuracy": accuracy, "tp": tp, "fp": fp, "tn": tn, "fn": fn}


def _capped_threshold_values(values: list[float], max_values: int = 17) -> list[float]:
    if len(values) <= max_values:
        return values
    selected: list[float] = []
    for index in range(max_values):
        position = round(index * (len(values) - 1) / (max_values - 1))
        selected.append(values[position])
    return sorted(set(selected))


def _candidate_selector_features() -> tuple[str, ...]:
    return (
        "candidate_position_frac",
        "candidate_sequence_len",
        "candidate_start_time",
        "candidate_arc_count",
        "candidate_low_time_arc_frac",
        "candidate_low_risk_arc_frac",
        "candidate_low_energy_arc_frac",
        "candidate_active_overlap",
        "candidate_active_jaccard",
        "batch_returned_count",
        "batch_pair_overlap",
        "batch_pair_jaccard",
        "batch_active_avg_overlap",
        "batch_active_redundant_frac",
        "batch_active_bridge_frac",
    )


def _candidate_leave_one_dataset_validation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return _leave_one_group_validation_for_features(rows, _candidate_selector_features(), "dataset")


def _candidate_two_feature_leave_one_dataset_validation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return _leave_one_group_two_feature_validation(rows, _candidate_selector_features(), "dataset")


def _candidate_leave_one_instance_validation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return _leave_one_group_validation_for_features(rows, _candidate_selector_features(), "instance")


def _candidate_two_feature_leave_one_instance_validation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return _leave_one_group_two_feature_validation(rows, _candidate_selector_features(), "instance")


def _leave_one_dataset_validation_for_features(
    rows: list[dict[str, Any]], features: tuple[str, ...]
) -> dict[str, Any]:
    return _leave_one_group_validation_for_features(rows, features, "dataset")


def _leave_one_group_validation_for_features(
    rows: list[dict[str, Any]], features: tuple[str, ...], group_key: str
) -> dict[str, Any]:
    groups = sorted({str(row.get(group_key, "")) for row in rows if row.get(group_key)})
    total = tp = fp = tn = fn = 0
    rules: list[dict[str, Any]] = []
    for held_out in groups:
        train = [row for row in rows if row.get(group_key) != held_out]
        test = [row for row in rows if row.get(group_key) == held_out]
        rule = _best_threshold_rule(train, features)
        if rule is None:
            continue
        metrics = _score_threshold_rule(test, rule)
        total += metrics["n"]
        tp += metrics["tp"]
        fp += metrics["fp"]
        tn += metrics["tn"]
        fn += metrics["fn"]
        rules.append({"held_out": held_out, **rule, **metrics})
    accuracy = None if total <= 0 else (tp + tn) / total
    return {
        "group_key": group_key,
        "total": total,
        "accuracy": accuracy,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "rules": rules,
    }


def _leave_one_dataset_two_feature_validation(
    rows: list[dict[str, Any]], features: tuple[str, ...]
) -> dict[str, Any]:
    return _leave_one_group_two_feature_validation(rows, features, "dataset")


def _leave_one_group_two_feature_validation(
    rows: list[dict[str, Any]], features: tuple[str, ...], group_key: str
) -> dict[str, Any]:
    groups = sorted({str(row.get(group_key, "")) for row in rows if row.get(group_key)})
    total = tp = fp = tn = fn = 0
    rules: list[dict[str, Any]] = []
    for held_out in groups:
        train = [row for row in rows if row.get(group_key) != held_out]
        test = [row for row in rows if row.get(group_key) == held_out]
        rule = _best_two_feature_rule(train, features)
        if rule is None:
            continue
        metrics = _score_two_feature_rule(test, rule)
        total += metrics["n"]
        tp += metrics["tp"]
        fp += metrics["fp"]
        tn += metrics["tn"]
        fn += metrics["fn"]
        rules.append({"held_out": held_out, **rule, **metrics})
    accuracy = None if total <= 0 else (tp + tn) / total
    precision = None if tp + fp <= 0 else tp / (tp + fp)
    recall = None if tp + fn <= 0 else tp / (tp + fn)
    return {
        "group_key": group_key,
        "total": total,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "rules": rules,
    }


def _best_two_feature_rule(rows: list[dict[str, Any]], features: tuple[str, ...]) -> dict[str, Any] | None:
    simple_rules: list[dict[str, Any]] = []
    for feature in features:
        values = _capped_threshold_values(
            sorted(
                {
                    value
                    for row in rows
                    for value in [_as_float(row.get(feature))]
                    if value is not None
                }
            )
        )
        for threshold in values:
            for operator in ("<=", ">="):
                simple_rules.append({"feature": feature, "operator": operator, "threshold": threshold})
    best: tuple[float, float, float, float, int, int, int, int, int, int] | None = None
    best_rule: dict[str, Any] | None = None
    for i, left in enumerate(simple_rules):
        for j, right in enumerate(simple_rules[i:], start=i):
            rule = {"left": left, "right": right}
            metrics = _score_two_feature_rule(rows, rule)
            if metrics["n"] <= 0:
                continue
            precision = 0.0 if metrics["tp"] + metrics["fp"] <= 0 else metrics["tp"] / (metrics["tp"] + metrics["fp"])
            recall = 0.0 if metrics["tp"] + metrics["fn"] <= 0 else metrics["tp"] / (metrics["tp"] + metrics["fn"])
            f1 = 0.0 if precision + recall <= 0.0 else 2.0 * precision * recall / (precision + recall)
            accuracy = metrics["accuracy"]
            candidate = (
                f1,
                precision,
                recall,
                accuracy,
                metrics["tp"],
                metrics["tn"],
                -metrics["fp"],
                -metrics["fn"],
                -i,
                -j,
            )
            if best is None or candidate > best:
                best = candidate
                best_rule = rule
    return best_rule


def _score_two_feature_rule(rows: list[dict[str, Any]], rule: dict[str, Any]) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    for row in rows:
        left = _eval_threshold(row, rule["left"])
        right = _eval_threshold(row, rule["right"])
        if left is None or right is None:
            continue
        prediction = bool(left and right)
        actual = row.get("run_improvement_class") == "improved"
        if prediction and actual:
            tp += 1
        elif prediction and not actual:
            fp += 1
        elif not prediction and not actual:
            tn += 1
        else:
            fn += 1
    n = tp + fp + tn + fn
    accuracy = 0.0 if n <= 0 else (tp + tn) / n
    return {"n": n, "accuracy": accuracy, "tp": tp, "fp": fp, "tn": tn, "fn": fn}


def _eval_threshold(row: dict[str, Any], rule: dict[str, Any]) -> bool | None:
    value = _as_float(row.get(str(rule["feature"])))
    if value is None:
        return None
    operator = str(rule["operator"])
    threshold = float(rule["threshold"])
    return value <= threshold if operator == "<=" else value >= threshold


def _summarize_candidates(candidate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    label_counts = Counter(str(row.get("run_improvement_class", "")) for row in candidate_rows)
    twenty = [row for row in candidate_rows if str(row.get("scale", "")) == "20"]
    twenty_strict = [
        row for row in twenty if row.get("run_improvement_class") in {"improved", "worsened"}
    ]
    improved = [row for row in twenty_strict if row.get("run_improvement_class") == "improved"]
    worsened = [row for row in twenty_strict if row.get("run_improvement_class") == "worsened"]

    def avg(group: list[dict[str, Any]], key: str) -> float | None:
        values = [_as_float(row.get(key)) for row in group]
        clean = [value for value in values if value is not None]
        return None if not clean else sum(clean) / len(clean)

    def feature_avg(group: list[dict[str, Any]]) -> dict[str, float | None]:
        return {
            "candidate_sequence_len": avg(group, "candidate_sequence_len"),
            "candidate_position_frac": avg(group, "candidate_position_frac"),
            "candidate_start_time": avg(group, "candidate_start_time"),
            "candidate_low_time_arc_frac": avg(group, "candidate_low_time_arc_frac"),
            "candidate_low_risk_arc_frac": avg(group, "candidate_low_risk_arc_frac"),
            "candidate_low_energy_arc_frac": avg(group, "candidate_low_energy_arc_frac"),
            "candidate_active_overlap": avg(group, "candidate_active_overlap"),
            "candidate_active_jaccard": avg(group, "candidate_active_jaccard"),
            "batch_returned_count": avg(group, "batch_returned_count"),
            "batch_pair_overlap": avg(group, "batch_pair_overlap"),
            "batch_pair_jaccard": avg(group, "batch_pair_jaccard"),
            "batch_active_avg_overlap": avg(group, "batch_active_avg_overlap"),
            "batch_active_redundant_frac": avg(group, "batch_active_redundant_frac"),
            "batch_active_bridge_frac": avg(group, "batch_active_bridge_frac"),
            "candidate_added": avg(group, "candidate_added"),
            "candidate_new_task_set": avg(group, "candidate_new_task_set"),
            "candidate_future_active_within2": avg(group, "candidate_future_active_within2"),
            "incumbent_within2": avg(group, "incumbent_within2"),
            "next_incomplete_count": avg(group, "next_incomplete_count"),
        }

    return {
        "candidate_rows": len(candidate_rows),
        "candidate_label_counts": dict(sorted(label_counts.items())),
        "twenty_candidate_rows": len(twenty),
        "twenty_strict_candidate_rows": len(twenty_strict),
        "twenty_strict_candidate_label_counts": dict(
            sorted(Counter(str(row.get("run_improvement_class", "")) for row in twenty_strict).items())
        ),
        "twenty_strict_improved_candidate_feature_avg": feature_avg(improved),
        "twenty_strict_worsened_candidate_feature_avg": feature_avg(worsened),
        "twenty_strict_candidate_leave_one_dataset_validation": _candidate_leave_one_dataset_validation(
            twenty_strict
        ),
        "twenty_strict_candidate_two_feature_leave_one_dataset_validation": _candidate_two_feature_leave_one_dataset_validation(
            twenty_strict
        ),
        "twenty_strict_candidate_leave_one_instance_validation": _candidate_leave_one_instance_validation(
            twenty_strict
        ),
        "twenty_strict_candidate_two_feature_leave_one_instance_validation": _candidate_two_feature_leave_one_instance_validation(
            twenty_strict
        ),
    }


def build_dataset(result_dirs: list[Path]) -> list[dict[str, Any]]:
    rows, _ = build_datasets(result_dirs)
    return rows


def build_datasets(result_dirs: list[Path]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    for dataset, summary_row in _iter_summary_rows(result_dirs):
        log_text = summary_row.get("log_path") or ""
        if not log_text:
            continue
        log_path = Path(log_text)
        if not log_path.exists():
            continue
        records = _load_jsonl(log_path)
        stage_rows, run_candidate_rows = _extract_rows_from_run(
            dataset=dataset,
            summary_row=summary_row,
            records=records,
        )
        rows.extend(stage_rows)
        candidate_rows.extend(run_candidate_rows)
    return rows, candidate_rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in FIELDNAMES})


def _write_candidate_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANDIDATE_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in CANDIDATE_FIELDNAMES})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--result-dir",
        action="append",
        dest="result_dirs",
        default=[],
        help="Result directory containing summary.csv. Can be repeated.",
    )
    parser.add_argument(
        "--output-dir",
        default="BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613",
        help="Output directory for stage_rows.csv and summary.json.",
    )
    args = parser.parse_args()
    result_dirs = [Path(path) for path in (args.result_dirs or DEFAULT_RESULT_DIRS)]
    if not result_dirs:
        result_dirs = [Path(path) for path in DEFAULT_RESULT_DIRS]
    rows, candidate_rows = build_datasets(result_dirs)
    output_dir = Path(args.output_dir)
    _write_csv(output_dir / "stage_rows.csv", rows)
    _write_candidate_csv(output_dir / "candidate_rows.csv", candidate_rows)
    summary = _summarize(rows)
    summary["candidate_summary"] = _summarize_candidates(candidate_rows)
    summary["result_dirs"] = [str(path) for path in result_dirs]
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Extract target-priority worker candidates from same-run GAT decisions.

This is a bridge from the same-context batch-impact GAT+kNN/OOD audit to
explicit opt-in worker intervention runs.  It is read-only: it consumes
decision records and capture JSONL logs, and never runs BPC, pricing, RMP,
workers, or certificates.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
from typing import Any, Iterable


DEFAULT_DECISION_RECORDS = Path(
    "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_20260615/"
    "same_run_gat_knn_ood_audit/decision_records.jsonl"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_same_run_target_priority_candidates_20260615"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260615_bpc_future_gat_same_run_target_priority_candidates_zh.md"
)

REQUIRED_CAPTURE_CONTEXT_FIELDS = [
    "context_hash",
    "true_dual_hash",
    "cut_hash",
    "branch_hash",
    "forbidden_signature_hash",
    "active_hash_before",
    "pool_signature_hash",
    "pool_task_set_hash",
]

SUPPORTED_CANDIDATE_RANKINGS = {"best_rc", "impact", "active_replacement"}
DEFAULT_SUPPORT_CHANGE_JACCARD_THRESHOLD = 0.6


def _parse_filter_values(values: Iterable[str] | None) -> tuple[str, ...]:
    if values is None:
        return tuple()
    parsed: list[str] = []
    for value in values:
        for item in str(value).split(","):
            item = item.strip()
            if item:
                parsed.append(item)
    return tuple(parsed)


def _normal_filter_text(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")


def _filter_matches(value: Any, allowed: Iterable[str] | None) -> bool:
    allowed_tuple = tuple(str(item) for item in (allowed or tuple()) if str(item).strip())
    if not allowed_tuple:
        return True
    normalized_value = _normal_filter_text(value)
    for item in allowed_tuple:
        normalized_item = _normal_filter_text(item)
        if (
            normalized_value == normalized_item
            or normalized_item in normalized_value
            or normalized_value in normalized_item
        ):
            return True
    return False


def _instance_metadata(instance_path: str) -> dict[str, Any]:
    path = Path(str(instance_path))
    task_count: int | None = None
    family = "unknown"
    region = "unknown"
    for idx, part in enumerate(path.parts):
        match = re.fullmatch(r"tasks_(\d+)", part)
        if not match:
            continue
        task_count = int(match.group(1))
        if idx + 1 < len(path.parts):
            family = str(path.parts[idx + 1])
        if idx + 2 < len(path.parts):
            region = str(path.parts[idx + 2])
        break
    ordinal_match = re.search(r"_tasks\d{3}_(\d+)_seed", path.name)
    return {
        "instance_task_count": task_count,
        "instance_family": family,
        "instance_region": region,
        "instance_ordinal": int(ordinal_match.group(1)) if ordinal_match else None,
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def _existing_roi_targets(path: Path | None) -> set[tuple[str, tuple[int, ...]]]:
    if path is None:
        return set()
    target_path = Path(path)
    if not target_path.exists():
        raise FileNotFoundError(target_path)
    existing: set[tuple[str, tuple[int, ...]]] = set()
    for row in _read_jsonl(target_path):
        context_hash = str(row.get("expected_context_hash") or row.get("context_hash") or "")
        sequence = tuple(int(task) for task in (row.get("target_sequence") or []))
        if context_hash and sequence:
            existing.add((context_hash, sequence))
    return existing


def _capture_events_by_context(path: Path) -> dict[str, dict[str, Any]]:
    events: dict[str, dict[str, Any]] = {}
    with Path(path).open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                event = json.loads(text)
            except json.JSONDecodeError:
                continue
            if event.get("event") != "journey_counterfactual_replay_capture":
                continue
            context_hash = str(event.get("context_hash") or "")
            if context_hash:
                events[context_hash] = event
    return events


def _true_reduced_cost(journey: dict[str, Any]) -> float | None:
    for key in ("true_reduced_cost", "manual_true_reduced_cost", "reduced_cost"):
        value = journey.get(key)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _first_sortie_target(journey: dict[str, Any]) -> tuple[tuple[int, ...], tuple[str, ...]]:
    signature = journey.get("signature")
    if isinstance(signature, list) and signature:
        first = signature[0]
        if isinstance(first, (list, tuple)) and len(first) >= 2:
            try:
                sequence = tuple(int(task) for task in (first[0] or []))
            except (TypeError, ValueError):
                sequence = tuple()
            arcs = tuple(str(arc) for arc in (first[1] or []))
            if sequence and arcs:
                return sequence, arcs
    sequence_payload = journey.get("sequence")
    if isinstance(sequence_payload, list) and sequence_payload:
        try:
            sequence = tuple(int(task) for task in (sequence_payload[0] or []))
        except (TypeError, ValueError):
            sequence = tuple()
        trips = journey.get("trips")
        if isinstance(trips, list) and trips:
            arcs = tuple(str(arc) for arc in (trips[0].get("arc_option_ids") or []))
            if sequence and arcs:
                return sequence, arcs
    return tuple(), tuple()


def _journey_sortie_traces(journey: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    traces: list[dict[str, Any]] = []
    trips = journey.get("trips")
    if isinstance(trips, list) and trips:
        for trip in trips:
            if not isinstance(trip, dict):
                return tuple()
            try:
                sequence = tuple(int(task) for task in (trip.get("tasks") or []))
                start_time = float(trip.get("start_time"))
            except (TypeError, ValueError):
                return tuple()
            arcs = tuple(str(arc) for arc in (trip.get("arc_option_ids") or []))
            if not sequence or len(arcs) != len(sequence) + 1:
                return tuple()
            traces.append(
                {
                    "sequence": list(sequence),
                    "start_time": start_time,
                    "arc_option_sequence": list(arcs),
                }
            )
        return tuple(traces)
    signature = journey.get("signature")
    if isinstance(signature, list) and signature:
        for item in signature:
            if not isinstance(item, (list, tuple)) or len(item) < 3:
                return tuple()
            try:
                sequence = tuple(int(task) for task in (item[0] or []))
                arcs = tuple(str(arc) for arc in (item[1] or []))
                start_time = float(item[2])
            except (TypeError, ValueError):
                return tuple()
            if not sequence or len(arcs) != len(sequence) + 1:
                return tuple()
            traces.append(
                {
                    "sequence": list(sequence),
                    "start_time": start_time,
                    "arc_option_sequence": list(arcs),
                }
            )
        return tuple(traces)
    return tuple()


def _flatten_trace_sequence(traces: tuple[dict[str, Any], ...]) -> tuple[int, ...]:
    flattened: list[int] = []
    for trace in traces:
        flattened.extend(int(task) for task in trace.get("sequence") or [])
    return tuple(flattened)


def _normalized_task_set(value: Any) -> frozenset[int]:
    if value is None:
        return frozenset()
    try:
        return frozenset(int(task) for task in value)
    except (TypeError, ValueError):
        return frozenset()


def _task_sets_from_payload(value: Any) -> set[frozenset[int]]:
    if not isinstance(value, list):
        return set()
    task_sets: set[frozenset[int]] = set()
    for item in value:
        task_set = _normalized_task_set(item)
        if task_set:
            task_sets.add(task_set)
    return task_sets


def _journey_task_set(journey: dict[str, Any], traces: tuple[dict[str, Any], ...]) -> frozenset[int]:
    task_set = _normalized_task_set(journey.get("task_set"))
    if task_set:
        return task_set
    return frozenset(_flatten_trace_sequence(traces))


def _jaccard(left: frozenset[int], right: frozenset[int]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    if not union:
        return 0.0
    return float(len(left & right)) / float(len(union))


def _max_jaccard(task_set: frozenset[int], others: set[frozenset[int]]) -> float:
    if not task_set or not others:
        return 0.0
    return max(_jaccard(task_set, other) for other in others)


def _candidate_impact_features(
    event: dict[str, Any],
    journey: dict[str, Any],
    traces: tuple[dict[str, Any], ...],
    *,
    support_change_jaccard_threshold: float = DEFAULT_SUPPORT_CHANGE_JACCARD_THRESHOLD,
) -> dict[str, Any]:
    task_set = _journey_task_set(journey, traces)
    pool_task_sets = _task_sets_from_payload(event.get("pool_task_sets"))
    active_task_sets = _task_sets_from_payload(event.get("active_task_sets"))
    active_jaccard = _max_jaccard(task_set, active_task_sets)
    in_pool = bool(task_set and task_set in pool_task_sets)
    in_active = bool(task_set and task_set in active_task_sets)
    support_changing = bool(
        task_set
        and not in_active
        and (
            not active_task_sets
            or active_jaccard <= float(support_change_jaccard_threshold)
        )
    )
    new_task_set = bool(task_set and not in_pool)
    if new_task_set and support_changing:
        impact_bucket = "new_support_changing"
    elif new_task_set:
        impact_bucket = "new_task_set"
    elif support_changing:
        impact_bucket = "support_changing"
    else:
        impact_bucket = "replacement_like"
    return {
        "target_task_set": sorted(int(task) for task in task_set),
        "target_task_set_size": len(task_set),
        "target_task_set_in_pool": in_pool,
        "target_task_set_in_active": in_active,
        "target_task_set_new": new_task_set,
        "target_max_active_jaccard": round(float(active_jaccard), 9),
        "target_support_changing_proxy": support_changing,
        "target_replacement_like_proxy": impact_bucket == "replacement_like",
        "target_impact_bucket": impact_bucket,
    }


def _impact_bucket_rank(bucket: str) -> int:
    return {
        "new_support_changing": 0,
        "new_task_set": 1,
        "support_changing": 2,
        "replacement_like": 3,
    }.get(str(bucket), 4)


def _active_replacement_rank(impact: dict[str, Any]) -> int:
    if bool(impact.get("target_task_set_in_active")):
        return 0
    if str(impact.get("target_impact_bucket")) == "replacement_like":
        return 1
    if bool(impact.get("target_support_changing_proxy")):
        return 2
    if bool(impact.get("target_task_set_new")):
        return 3
    return 4


def _negative_journey_candidates(
    event: dict[str, Any],
    *,
    candidate_ranking: str = "best_rc",
    support_change_jaccard_threshold: float = DEFAULT_SUPPORT_CHANGE_JACCARD_THRESHOLD,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    negatives: list[tuple[tuple[float, ...], int, dict[str, Any], dict[str, Any]]] = []
    for idx, journey in enumerate(event.get("returned_journeys") or []):
        if not isinstance(journey, dict):
            continue
        true_rc = _true_reduced_cost(journey)
        if true_rc is None or true_rc >= 0.0:
            continue
        sequence, arcs = _first_sortie_target(journey)
        if not sequence or not arcs:
            continue
        if not _journey_sortie_traces(journey):
            continue
        traces = _journey_sortie_traces(journey)
        impact = _candidate_impact_features(
            event,
            journey,
            traces,
            support_change_jaccard_threshold=support_change_jaccard_threshold,
        )
        if candidate_ranking == "impact":
            sort_key = (
                float(_impact_bucket_rank(str(impact["target_impact_bucket"]))),
                -float(len(impact["target_task_set"])),
                float(true_rc),
            )
        elif candidate_ranking == "active_replacement":
            sort_key = (
                float(_active_replacement_rank(impact)),
                -float(len(impact["target_task_set"])),
                float(true_rc),
            )
        else:
            sort_key = (float(true_rc),)
        negatives.append((sort_key, idx, journey, impact))
    if not negatives:
        return []
    negatives.sort(key=lambda item: (item[0], item[1]))
    return [(item[2], item[3]) for item in negatives]


def _best_negative_journey(
    event: dict[str, Any],
    *,
    candidate_ranking: str = "best_rc",
    support_change_jaccard_threshold: float = DEFAULT_SUPPORT_CHANGE_JACCARD_THRESHOLD,
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    candidates = _negative_journey_candidates(
        event,
        candidate_ranking=candidate_ranking,
        support_change_jaccard_threshold=support_change_jaccard_threshold,
    )
    return candidates[0] if candidates else None


def _missing_capture_context_fields(event: dict[str, Any]) -> list[str]:
    return [
        field
        for field in REQUIRED_CAPTURE_CONTEXT_FIELDS
        if str(event.get(field) or "").strip() == ""
    ]


def _safe_name(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_]+", "_", text).strip("_")
    return text[:180] or "candidate"


def extract_candidates(
    *,
    decision_records_path: Path = DEFAULT_DECISION_RECORDS,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    max_candidates: int = 8,
    min_probability: float = 0.0,
    decision_reason: str = "high_priority",
    include_delay_queue: bool = False,
    delay_queue_only: bool = False,
    candidate_ranking: str = "best_rc",
    support_change_jaccard_threshold: float = DEFAULT_SUPPORT_CHANGE_JACCARD_THRESHOLD,
    exclude_existing_roi_jsonl: Path | None = None,
    include_families: Iterable[str] | None = None,
    include_regions: Iterable[str] | None = None,
    include_ordinals: Iterable[int] | None = None,
    include_task_counts: Iterable[int] | None = None,
    max_targets_per_context: int = 1,
) -> dict[str, Any]:
    if candidate_ranking not in SUPPORTED_CANDIDATE_RANKINGS:
        raise ValueError(
            f"unsupported candidate_ranking={candidate_ranking!r}; "
            f"expected one of {sorted(SUPPORTED_CANDIDATE_RANKINGS)}"
        )
    decisions = _read_jsonl(Path(decision_records_path))
    capture_cache: dict[str, dict[str, dict[str, Any]]] = {}
    skipped: Counter[str] = Counter()
    candidates: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str, tuple[int, ...], tuple[str, ...]]] = set()
    existing_roi_targets = _existing_roi_targets(exclude_existing_roi_jsonl)
    family_filter = _parse_filter_values(include_families)
    region_filter = _parse_filter_values(include_regions)
    ordinal_filter = {int(value) for value in (include_ordinals or tuple())}
    task_count_filter = {int(value) for value in (include_task_counts or tuple())}

    for index, decision in enumerate(decisions):
        if len(candidates) >= int(max_candidates):
            break
        reason = str(decision.get("decision_reason") or "")
        is_high_priority = int(decision.get("decision") or 0) == 1 and reason == "high_priority"
        is_delay_queue = reason in {
            "below_threshold_delay_queue",
            "knn_delay_fraction_delay_queue",
        }
        if delay_queue_only:
            if not is_delay_queue:
                skipped["decision_not_delay_queue"] += 1
                continue
        elif include_delay_queue:
            if not (is_high_priority or is_delay_queue):
                skipped["decision_not_selected"] += 1
                continue
        elif int(decision.get("decision") or 0) != 1:
            skipped["decision_not_high_priority"] += 1
            continue
        elif reason != str(decision_reason):
            skipped["decision_reason_not_selected"] += 1
            continue
        if float(decision.get("probability") or 0.0) < float(min_probability):
            skipped["probability_below_min"] += 1
            continue
        source_file = Path(str(decision.get("source_file") or ""))
        if not source_file.exists():
            skipped["missing_source_file"] += 1
            continue
        context_hash = str(decision.get("context_hash") or "")
        if not context_hash:
            skipped["missing_context_hash"] += 1
            continue
        events = capture_cache.get(str(source_file))
        if events is None:
            events = _capture_events_by_context(source_file)
            capture_cache[str(source_file)] = events
        event = events.get(context_hash)
        if event is None:
            skipped["missing_capture_event"] += 1
            continue
        missing_context = _missing_capture_context_fields(event)
        if missing_context:
            skipped["missing_capture_context_fields"] += 1
            continue
        selected_items = _negative_journey_candidates(
            event,
            candidate_ranking=candidate_ranking,
            support_change_jaccard_threshold=float(support_change_jaccard_threshold),
        )
        if not selected_items:
            skipped["no_negative_journey_with_materialized_signature"] += 1
            continue
        instance_path = str(event.get("instance_path") or decision.get("instance_path") or "")
        if not instance_path or not Path(instance_path).exists():
            skipped["missing_instance_path"] += 1
            continue
        instance_metadata = _instance_metadata(instance_path)
        if (
            task_count_filter
            and instance_metadata["instance_task_count"] not in task_count_filter
        ):
            skipped["task_count_not_selected"] += 1
            continue
        if not _filter_matches(instance_metadata["instance_family"], family_filter):
            skipped["family_not_selected"] += 1
            continue
        if not _filter_matches(instance_metadata["instance_region"], region_filter):
            skipped["region_not_selected"] += 1
            continue
        if ordinal_filter and instance_metadata["instance_ordinal"] not in ordinal_filter:
            skipped["ordinal_not_selected"] += 1
            continue
        accepted_in_context = 0
        for context_rank, (journey, impact_features) in enumerate(selected_items, start=1):
            if len(candidates) >= int(max_candidates):
                break
            if accepted_in_context >= max(1, int(max_targets_per_context)):
                break
            sequence, arcs = _first_sortie_target(journey)
            traces = _journey_sortie_traces(journey)
            flattened_sequence = _flatten_trace_sequence(traces)
            key = (
                instance_path,
                context_hash,
                flattened_sequence,
                tuple(
                    str(arc)
                    for trace in traces
                    for arc in (trace.get("arc_option_sequence") or [])
                ),
            )
            if key in seen_keys:
                skipped["duplicate_candidate"] += 1
                continue
            if (context_hash, flattened_sequence) in existing_roi_targets:
                skipped["existing_roi_target"] += 1
                continue
            seen_keys.add(key)
            true_rc = _true_reduced_cost(journey)
            instance_name = str(
                event.get("instance") or decision.get("instance") or Path(instance_path).stem
            )
            name = _safe_name(
                f"{instance_name}_{context_hash}_rank{context_rank}_"
                f"{'_'.join(str(task) for task in flattened_sequence)}"
            )
            decision_name = "HIGH_PRIORITY" if is_high_priority else "DELAY_QUEUE"
            candidates.append(
                {
                    "schema_version": "gat_same_run_target_priority_candidate_v1",
                    "name": name,
                    "instance": instance_path,
                    **instance_metadata,
                    "context_hash": context_hash,
                    "expected_context_hash": context_hash,
                    "true_dual_hash": str(event.get("true_dual_hash") or ""),
                    "cut_hash": str(event.get("cut_hash") or ""),
                    "branch_hash": str(event.get("branch_hash") or ""),
                    "forbidden_signature_hash": str(event.get("forbidden_signature_hash") or ""),
                    "active_hash_before": str(event.get("active_hash_before") or ""),
                    "pool_signature_hash": str(event.get("pool_signature_hash") or ""),
                    "pool_task_set_hash": str(event.get("pool_task_set_hash") or ""),
                    "target_sequence": list(flattened_sequence),
                    "target_priority_sequence": list(sequence),
                    "target_arc_option_sequence": list(arcs),
                    "target_sortie_traces": list(traces),
                    "best_true_reduced_cost": true_rc,
                    "decision_name": decision_name,
                    "decision_probability": float(decision.get("probability") or 0.0),
                    "decision_reason": str(decision.get("decision_reason") or ""),
                    "source_file": str(source_file),
                    "sample_path": str(decision.get("sample_path") or ""),
                    "source_row_index": int(decision.get("row_index") or -1),
                    "decision_record_index": int(index),
                    "context_target_rank": int(context_rank),
                    "capture_cg_iter": int(event.get("cg_iter") or -1),
                    "capture_pricing_kind": str(event.get("pricing_kind") or ""),
                    "capture_returned_journey_count": int(event.get("returned_journey_count") or 0),
                    "candidate_ranking": str(candidate_ranking),
                    "support_change_jaccard_threshold": float(support_change_jaccard_threshold),
                    **impact_features,
                    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
                    "worker_role": "explicit_opt_in_same_context_target_intervention_probe",
                    "training_label_allowed_before_worker_reachability": False,
                    "requires_worker_target_causal_match": True,
                    "certificate_effect": False,
                    "official_bound_effect": False,
                }
            )
            accepted_in_context += 1

    all_candidates_high_priority = all(
        item["decision_name"] == "HIGH_PRIORITY" for item in candidates
    )
    all_candidates_high_or_delay = all(
        item["decision_name"] in {"HIGH_PRIORITY", "DELAY_QUEUE"} for item in candidates
    )
    checks = {
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "no_certificate_effect": True,
        "has_candidate": bool(candidates),
        "candidate_decision_scope_valid": all_candidates_high_or_delay
        if (include_delay_queue or delay_queue_only)
        else all_candidates_high_priority,
        "all_candidates_true_rc_negative": all(
            float(item["best_true_reduced_cost"]) < 0.0 for item in candidates
        ),
        "all_candidate_instances_exist": all(
            Path(str(item["instance"])).exists() for item in candidates
        ),
        "all_candidates_have_arc_targets": all(
            bool(item["target_arc_option_sequence"]) for item in candidates
        ),
        "all_candidates_have_full_sortie_traces": all(
            bool(item.get("target_sortie_traces")) for item in candidates
        ),
        "all_candidates_have_full_capture_context": all(
            all(str(item.get(field) or "").strip() for field in REQUIRED_CAPTURE_CONTEXT_FIELDS)
            for item in candidates
        ),
        "labels_blocked_until_worker_reachability": all(
            item["training_label_allowed_before_worker_reachability"] is False
            and item["requires_worker_target_causal_match"] is True
            for item in candidates
        ),
    }
    summary = {
        "schema_version": "gat_same_run_target_priority_candidates_v1",
        "status": "ready" if candidates else "no_candidates",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "decision_records_path": str(decision_records_path),
        "decision_count": len(decisions),
        "include_delay_queue": bool(include_delay_queue),
        "delay_queue_only": bool(delay_queue_only),
        "candidate_ranking": str(candidate_ranking),
        "support_change_jaccard_threshold": float(support_change_jaccard_threshold),
        "max_targets_per_context": max(1, int(max_targets_per_context)),
        "exclude_existing_roi_jsonl": ""
        if exclude_existing_roi_jsonl is None
        else str(exclude_existing_roi_jsonl),
        "include_families": list(family_filter),
        "include_regions": list(region_filter),
        "include_ordinals": sorted(int(value) for value in ordinal_filter),
        "include_task_counts": sorted(int(value) for value in task_count_filter),
        "existing_roi_target_count": len(existing_roi_targets),
        "candidate_count": len(candidates),
        "skipped_counts": dict(sorted(skipped.items())),
        "candidate_task_count_counts": {
            str(task_count): count
            for task_count, count in sorted(
                Counter(item.get("instance_task_count") for item in candidates).items(),
                key=lambda item: (-1 if item[0] is None else int(item[0])),
            )
        },
        "candidate_family_region_counts": {
            f"{family}|{region}": count
            for (family, region), count in sorted(
                Counter(
                    (
                        str(item.get("instance_family") or "unknown"),
                        str(item.get("instance_region") or "unknown"),
                    )
                    for item in candidates
                ).items()
            )
        },
        "candidate_impact_bucket_counts": dict(
            sorted(Counter(str(item.get("target_impact_bucket") or "") for item in candidates).items())
        ),
        "candidate_new_task_set_count": sum(
            1 for item in candidates if bool(item.get("target_task_set_new"))
        ),
        "candidate_support_changing_proxy_count": sum(
            1 for item in candidates if bool(item.get("target_support_changing_proxy"))
        ),
        "candidate_replacement_like_proxy_count": sum(
            1 for item in candidates if bool(item.get("target_replacement_like_proxy"))
        ),
        "candidates": candidates,
        "required_capture_context_fields": REQUIRED_CAPTURE_CONTEXT_FIELDS,
        "output_candidates_json": str(output_dir / "candidates.json"),
        "production_ready": False,
        "default_enabled": False,
        "certificate_ready": False,
        "official_bound_effect": False,
        "candidate_policy": {
            "safe_negative_decision": "HIGH_PRIORITY",
            "unsafe_negative_decision": "DELAY_QUEUE",
            "permanent_negative_filter_allowed": False,
            "training_label_requires_worker_target_causal_match": True,
        },
        "checks": checks,
        "all_candidates_high_priority": all_candidates_high_priority,
        "all_candidates_high_or_delay": all_candidates_high_or_delay,
        "all_checks_pass": all(bool(value) for value in checks.values()),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "candidates.json").write_text(
        json.dumps({"candidates": candidates}, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Same-Run Target-Priority Candidates 报告",
        "",
        "日期：2026-06-15",
        "",
        "## 目的",
        "",
        "从 same-run GAT+kNN/OOD 决策中抽取 target-priority worker 候选。",
        "该脚本只读 decision_records 与 capture JSONL，不运行 BPC / pricing / RMP / worker，",
        "不产生 certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_same_run_target_priority_candidates = current",
        f"status = {summary['status']}",
        f"candidate_count = {summary['candidate_count']}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"default_enabled = {str(summary['default_enabled']).lower()}",
        f"certificate_ready = {str(summary['certificate_ready']).lower()}",
        f"official_bound_effect = {str(summary['official_bound_effect']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 关键约束",
        "",
        "- 默认候选来自 same-context batch-impact 的 HIGH_PRIORITY 决策；",
        "- 显式 `include_delay_queue` 时可纳入 DELAY_QUEUE 候选做离线探索采样；",
        "- `best_true_reduced_cost < 0` 才能成为 worker target；",
        "- 当前仍不能直接作为训练标签，必须先通过 worker reachability / target causal match 审计；",
        "- 不通过的 true-RC negative 只能进入 DELAY_QUEUE，不能永久丢弃。",
        "",
        "## 摘要",
        "",
        "```json",
        json.dumps(
            {
                "candidate_count": summary["candidate_count"],
                "include_delay_queue": summary["include_delay_queue"],
                "delay_queue_only": summary["delay_queue_only"],
                "candidate_ranking": summary["candidate_ranking"],
                "max_targets_per_context": summary["max_targets_per_context"],
                "exclude_existing_roi_jsonl": summary["exclude_existing_roi_jsonl"],
                "include_families": summary["include_families"],
                "include_regions": summary["include_regions"],
                "include_ordinals": summary["include_ordinals"],
                "include_task_counts": summary["include_task_counts"],
                "existing_roi_target_count": summary["existing_roi_target_count"],
                "candidate_task_count_counts": summary["candidate_task_count_counts"],
                "candidate_family_region_counts": summary["candidate_family_region_counts"],
                "candidate_impact_bucket_counts": summary["candidate_impact_bucket_counts"],
                "candidate_new_task_set_count": summary["candidate_new_task_set_count"],
                "candidate_support_changing_proxy_count": summary["candidate_support_changing_proxy_count"],
                "candidate_replacement_like_proxy_count": summary["candidate_replacement_like_proxy_count"],
                "skipped_counts": summary["skipped_counts"],
                "candidate_policy": summary["candidate_policy"],
                "checks": summary["checks"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision-records", type=Path, default=DEFAULT_DECISION_RECORDS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--max-candidates", type=int, default=8)
    parser.add_argument("--min-probability", type=float, default=0.0)
    parser.add_argument("--decision-reason", default="high_priority")
    parser.add_argument("--include-delay-queue", action="store_true")
    parser.add_argument("--delay-queue-only", action="store_true")
    parser.add_argument(
        "--candidate-ranking",
        choices=sorted(SUPPORTED_CANDIDATE_RANKINGS),
        default="best_rc",
        help="best_rc preserves the old behavior; impact prioritizes new/support-changing task sets.",
    )
    parser.add_argument(
        "--support-change-jaccard-threshold",
        type=float,
        default=DEFAULT_SUPPORT_CHANGE_JACCARD_THRESHOLD,
    )
    parser.add_argument("--max-targets-per-context", type=int, default=1)
    parser.add_argument("--exclude-existing-roi-jsonl", type=Path, default=None)
    parser.add_argument(
        "--include-families",
        nargs="*",
        default=None,
        help="Optional family allow-list, e.g. greedy-anchor random-wave.",
    )
    parser.add_argument(
        "--include-regions",
        nargs="*",
        default=None,
        help="Optional region allow-list; substring matches are accepted.",
    )
    parser.add_argument(
        "--include-ordinals",
        nargs="*",
        type=int,
        default=None,
        help="Optional instance ordinal allow-list.",
    )
    parser.add_argument(
        "--include-task-counts",
        nargs="*",
        type=int,
        default=None,
        help="Optional task-count allow-list, e.g. 20 to avoid 5/10 label pollution.",
    )
    args = parser.parse_args(argv)
    summary = extract_candidates(
        decision_records_path=args.decision_records,
        output_dir=args.output_dir,
        report=args.report,
        max_candidates=max(0, int(args.max_candidates)),
        min_probability=float(args.min_probability),
        decision_reason=str(args.decision_reason),
        include_delay_queue=bool(args.include_delay_queue),
        delay_queue_only=bool(args.delay_queue_only),
        candidate_ranking=str(args.candidate_ranking),
        support_change_jaccard_threshold=float(args.support_change_jaccard_threshold),
        max_targets_per_context=max(1, int(args.max_targets_per_context)),
        exclude_existing_roi_jsonl=args.exclude_existing_roi_jsonl,
        include_families=args.include_families,
        include_regions=args.include_regions,
        include_ordinals=args.include_ordinals,
        include_task_counts=args.include_task_counts,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

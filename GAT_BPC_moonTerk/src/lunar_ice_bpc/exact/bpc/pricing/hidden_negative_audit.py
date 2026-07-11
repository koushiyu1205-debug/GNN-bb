"""Hidden-negative diagnostics for worker misses."""

from __future__ import annotations

from typing import Iterable

from lunar_ice_bpc.exact.bpc.core.column_signature import column_signature_from_journey
from lunar_ice_bpc.exact.core.journey import JourneyColumn


HIDDEN_NEGATIVE_MISS_REASONS = (
    "worker_not_generated",
    "pruned_by_task_bound",
    "pruned_by_resource_bound",
    "pruned_by_dominance",
    "duplicate_filtered",
    "reduced_cost_mismatch",
    "pricing_timeout_only",
    "unknown",
)


def build_hidden_negative_audit(
    *,
    worker_payload: dict | None,
    final_judge_payload: dict,
    negative_candidates: Iterable[tuple[float, JourneyColumn]],
    node_id: str = "root",
    cg_iter: int = 0,
) -> dict:
    worker_payload = worker_payload or {}
    worker_state = str(worker_payload.get("pricing_state") or worker_payload.get("status") or "")
    final_state = str(final_judge_payload.get("pricing_state") or final_judge_payload.get("status") or "")
    triggered = bool(worker_state == "LOCAL_NO_COLUMN_UNCERTIFIED" and final_state == "FOUND_NEGATIVE")
    rows = []
    if triggered:
        for true_rc, column in negative_candidates:
            signature = column_signature_from_journey(column)
            task_set = tuple(sorted(str(task_id) for task_id in signature.task_set))
            worker_seen_same_task_set = _worker_seen_same_task_set(worker_payload, task_set)
            source_match = _worker_priced_candidate_source_match(worker_payload, task_set)
            refinement_coverage = _refinement_coverage_from_source_match(source_match)
            miss_reason = _classify_miss_reason(
                worker_payload,
                final_judge_payload,
                worker_seen_same_task_set=worker_seen_same_task_set,
            )
            rows.append(
                {
                    "node_id": str(node_id),
                    "cg_iter": int(cg_iter),
                    "worker_kind": str(worker_payload.get("worker_kind") or "unknown"),
                    "hidden_task_set": list(signature.task_set),
                    "hidden_negative_task_set": list(task_set),
                    "hidden_negative_task_set_size": len(task_set),
                    "hidden_sequence": [list(row) for row in signature.ordered_task_sequences],
                    "hidden_path_signature": [list(row) for row in signature.path_option_signature],
                    "hidden_true_rc": round(float(true_rc), 9),
                    "hidden_negative_true_rc": round(float(true_rc), 9),
                    "hidden_negative_source_phase": str(
                        final_judge_payload.get("compact_pricing_phase")
                        or final_judge_payload.get("hidden_negative_source_phase")
                        or "final_judge"
                    ),
                    "hidden_column_signature": repr(signature),
                    "worker_seen_same_task_set": bool(worker_seen_same_task_set),
                    "worker_priced_candidate_seen_same_task_set": bool(
                        source_match["match"] == "exact"
                    ),
                    "worker_priced_candidate_seen_superset_task_set": bool(
                        source_match["match"] == "superset"
                    ),
                    "worker_priced_candidate_seed_sources": list(source_match["sources"]),
                    "worker_priced_candidate_source_match": source_match["match"],
                    "worker_priced_candidate_matched_task_set": list(source_match["matched_task_set"]),
                    "worker_priced_candidate_refinement_source": bool(
                        refinement_coverage["is_refinement_source"]
                    ),
                    "worker_priced_candidate_refinement_coverage": refinement_coverage["coverage"],
                    "worker_best_rc_before_judge": _first_float(
                        worker_payload.get("best_reduced_cost"),
                        worker_payload.get("worker_best_rc"),
                        worker_payload.get("pricing_best_reduced_cost"),
                    ),
                    "replacement_or_new_task_set": "replacement" if worker_seen_same_task_set else "new_task_set",
                    "miss_reason": miss_reason,
                    "miss_reason_guess": miss_reason,
                    "worker_candidate_budget": int(worker_payload.get("worker_candidate_budget") or 0),
                    "worker_generated_count": int(worker_payload.get("worker_generated_count") or 0),
                    "final_judge_generated_count": int(final_judge_payload.get("candidate_round_count") or 0),
                }
            )
    miss_reason_counts = _miss_reason_counts(rows)
    source_counts = _priced_candidate_source_counts(rows)
    refinement_counts = _refinement_coverage_counts(rows)
    return {
        "schema_version": "lunar_ice_bpc.b2_hidden_negative_audit.v1",
        "status": "HIDDEN_NEGATIVE_FOUND" if rows else "NO_HIDDEN_NEGATIVE",
        "hidden_negative_count": len(rows),
        "miss_reason_counts": miss_reason_counts,
        "hidden_negative_miss_reason_counts": miss_reason_counts,
        "hidden_negative_priced_candidate_source_counts": source_counts,
        "hidden_negative_priced_candidate_exact_count": sum(
            1 for row in rows if row.get("worker_priced_candidate_source_match") == "exact"
        ),
        "hidden_negative_priced_candidate_superset_count": sum(
            1 for row in rows if row.get("worker_priced_candidate_source_match") == "superset"
        ),
        "hidden_negative_priced_candidate_unseen_count": sum(
            1 for row in rows if row.get("worker_priced_candidate_source_match") == "none"
        ),
        "hidden_negative_refinement_coverage_counts": refinement_counts,
        "hidden_negative_refinement_exact_count": refinement_counts.get("exact", 0),
        "hidden_negative_refinement_superset_count": refinement_counts.get("superset", 0),
        "hidden_negative_refinement_covered_count": int(refinement_counts.get("exact", 0))
        + int(refinement_counts.get("superset", 0)),
        "hidden_negative_refinement_uncovered_count": refinement_counts.get("uncovered", 0),
        "top_miss_reason": _top_miss_reason(miss_reason_counts),
        "hidden_negative_top_miss_reason": _top_miss_reason(miss_reason_counts),
        "mutates_solver": False,
        "changes_certificate_semantics": False,
        "rows": rows,
    }


def _classify_miss_reason(
    worker_payload: dict,
    final_judge_payload: dict,
    *,
    worker_seen_same_task_set: bool,
) -> str:
    explicit = str(worker_payload.get("miss_reason") or worker_payload.get("miss_reason_guess") or "").strip()
    if explicit in HIDDEN_NEGATIVE_MISS_REASONS:
        return explicit
    if not bool(worker_seen_same_task_set):
        if worker_payload.get("pricing_timeout") or str(worker_payload.get("status") or "").endswith("TIME_LIMIT"):
            return "pricing_timeout_only"
        if final_judge_payload.get("pricing_state") == "FOUND_NEGATIVE":
            return "worker_not_generated"
    if worker_payload.get("pruned_by_task_bound") or worker_payload.get("task_bound_pruned_count"):
        return "pruned_by_task_bound"
    if worker_payload.get("pruned_by_resource_bound") or worker_payload.get("resource_bound_pruned_count"):
        return "pruned_by_resource_bound"
    if worker_payload.get("pruned_by_dominance") or worker_payload.get("dominance_filtered_count"):
        return "pruned_by_dominance"
    if worker_payload.get("duplicate_filtered") or worker_payload.get("duplicate_filtered_count"):
        return "duplicate_filtered"
    if worker_payload.get("reduced_cost_mismatch") or worker_payload.get("pricing_rc_audit_pass") is False:
        return "reduced_cost_mismatch"
    if worker_payload.get("pricing_timeout") or str(worker_payload.get("status") or "").endswith("TIME_LIMIT"):
        return "pricing_timeout_only"
    if final_judge_payload.get("pricing_state") == "FOUND_NEGATIVE":
        return "worker_not_generated"
    return "unknown"


def _worker_seen_same_task_set(worker_payload: dict, task_set: tuple[str, ...]) -> bool:
    expected = tuple(task_set)
    actual_keys = (
        "worker_generated_column_task_sets",
        "worker_seen_task_sets",
        "seen_task_sets",
    )
    for key in actual_keys:
        raw_sets = worker_payload.get(key) or ()
        for raw in raw_sets:
            if tuple(sorted(str(item) for item in raw)) == expected:
                return True

    # Older worker payloads did not distinguish actual generated columns from
    # candidate universes.  Use the legacy fields only when no exact actual-set
    # telemetry is present; new payloads should rely on priced-candidate source
    # matching for coverage diagnostics instead of replacement classification.
    if any(worker_payload.get(key) is not None for key in actual_keys):
        return False
    for key in ("active_task_sets", "generated_task_sets"):
        raw_sets = worker_payload.get(key) or ()
        for raw in raw_sets:
            if tuple(sorted(str(item) for item in raw)) == expected:
                return True
    return False


def _worker_priced_candidate_source_match(worker_payload: dict, task_set: tuple[str, ...]) -> dict:
    expected = tuple(sorted(str(task_id) for task_id in task_set))
    rows = _priced_candidate_source_rows(worker_payload)
    if not rows:
        return {"match": "none", "sources": ("unknown",), "matched_task_set": tuple()}

    expected_set = set(expected)
    for row_task_set, sources in rows:
        if row_task_set == expected:
            return {
                "match": "exact",
                "sources": sources,
                "matched_task_set": row_task_set,
            }
    for row_task_set, sources in rows:
        if expected_set.issubset(set(row_task_set)):
            return {
                "match": "superset",
                "sources": sources,
                "matched_task_set": row_task_set,
            }
    return {"match": "none", "sources": ("unknown",), "matched_task_set": tuple()}


def _priced_candidate_source_rows(worker_payload: dict) -> tuple[tuple[tuple[str, ...], tuple[str, ...]], ...]:
    priced_rows: list[tuple[tuple[str, ...], tuple[str, ...]]] = []
    active_seed_rows: list[tuple[tuple[str, ...], tuple[str, ...]]] = []
    for container in _worker_payload_containers(worker_payload):
        priced_rows.extend(_source_rows_from_container(container, "priced_candidate_task_set_sources"))
        active_seed_rows.extend(_source_rows_from_container(container, "active_seed_task_set_sources"))
    return _dedupe_source_rows(priced_rows or active_seed_rows)


def _refinement_coverage_from_source_match(source_match: dict) -> dict:
    sources = tuple(str(source) for source in source_match.get("sources") or tuple())
    is_refinement = any(source.startswith("hidden_negative_refinement") for source in sources)
    match = str(source_match.get("match") or "none")
    if is_refinement and match in {"exact", "superset"}:
        coverage = match
    else:
        coverage = "uncovered"
    return {
        "is_refinement_source": is_refinement,
        "coverage": coverage,
    }


def _source_rows_from_container(
    container: dict,
    key: str,
) -> tuple[tuple[tuple[str, ...], tuple[str, ...]], ...]:
    rows: list[tuple[tuple[str, ...], tuple[str, ...]]] = []
    for raw_row in container.get(key) or ():
        if not isinstance(raw_row, dict):
            continue
        task_set = _normalize_task_set(raw_row.get("task_set") or ())
        if not task_set:
            continue
        sources = tuple(sorted({str(source) for source in raw_row.get("sources") or ("unknown",)}))
        rows.append((task_set, sources or ("unknown",)))
    return tuple(rows)


def _worker_payload_containers(worker_payload: dict) -> tuple[dict, ...]:
    containers = [worker_payload]
    nested = worker_payload.get("pricing_payload")
    if isinstance(nested, dict):
        containers.append(nested)
    return tuple(containers)


def _normalize_task_set(raw: object) -> tuple[str, ...]:
    try:
        return tuple(sorted({str(task_id) for task_id in raw if str(task_id)}))
    except TypeError:
        return tuple()


def _dedupe_source_rows(
    rows: Iterable[tuple[tuple[str, ...], tuple[str, ...]]],
) -> tuple[tuple[tuple[str, ...], tuple[str, ...]], ...]:
    merged: dict[tuple[str, ...], set[str]] = {}
    for task_set, sources in rows:
        if not task_set:
            continue
        merged.setdefault(task_set, set()).update(str(source) for source in sources)
    return tuple((task_set, tuple(sorted(sources))) for task_set, sources in sorted(merged.items()))


def _first_float(*values: object) -> float | None:
    for value in values:
        if value is None:
            continue
        try:
            return round(float(value), 9)
        except (TypeError, ValueError):
            continue
    return None


def _miss_reason_counts(rows: list[dict]) -> dict[str, int]:
    counts = {reason: 0 for reason in HIDDEN_NEGATIVE_MISS_REASONS}
    for row in rows:
        reason = str(row.get("miss_reason") or "unknown")
        if reason not in counts:
            reason = "unknown"
        counts[reason] += 1
    return {reason: count for reason, count in counts.items() if count > 0}


def _priced_candidate_source_counts(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for source in row.get("worker_priced_candidate_seed_sources") or ("unknown",):
            source_key = str(source or "unknown")
            counts[source_key] = counts.get(source_key, 0) + 1
    return dict(sorted(counts.items()))


def _refinement_coverage_counts(rows: list[dict]) -> dict[str, int]:
    counts = {"exact": 0, "superset": 0, "uncovered": 0}
    for row in rows:
        coverage = str(row.get("worker_priced_candidate_refinement_coverage") or "uncovered")
        if coverage not in counts:
            coverage = "uncovered"
        counts[coverage] += 1
    return {key: value for key, value in counts.items() if value > 0}


def _top_miss_reason(counts: dict[str, int]) -> str:
    if not counts:
        return ""
    return max(
        counts,
        key=lambda reason: (
            int(counts.get(reason, 0)),
            -HIDDEN_NEGATIVE_MISS_REASONS.index(reason)
            if reason in HIDDEN_NEGATIVE_MISS_REASONS
            else -len(HIDDEN_NEGATIVE_MISS_REASONS),
        ),
    )

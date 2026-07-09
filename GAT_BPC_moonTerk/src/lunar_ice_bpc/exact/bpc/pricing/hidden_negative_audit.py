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
            miss_reason = _classify_miss_reason(worker_payload, final_judge_payload)
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
    return {
        "schema_version": "lunar_ice_bpc.b2_hidden_negative_audit.v1",
        "status": "HIDDEN_NEGATIVE_FOUND" if rows else "NO_HIDDEN_NEGATIVE",
        "hidden_negative_count": len(rows),
        "miss_reason_counts": miss_reason_counts,
        "hidden_negative_miss_reason_counts": miss_reason_counts,
        "top_miss_reason": _top_miss_reason(miss_reason_counts),
        "hidden_negative_top_miss_reason": _top_miss_reason(miss_reason_counts),
        "mutates_solver": False,
        "changes_certificate_semantics": False,
        "rows": rows,
    }


def _classify_miss_reason(worker_payload: dict, final_judge_payload: dict) -> str:
    explicit = str(worker_payload.get("miss_reason") or worker_payload.get("miss_reason_guess") or "").strip()
    if explicit in HIDDEN_NEGATIVE_MISS_REASONS:
        return explicit
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
    for key in ("worker_seen_task_sets", "seen_task_sets", "active_task_sets", "generated_task_sets"):
        raw_sets = worker_payload.get(key) or ()
        for raw in raw_sets:
            if tuple(sorted(str(item) for item in raw)) == expected:
                return True
    return False


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

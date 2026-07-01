"""Hidden-negative diagnostics for worker misses."""

from __future__ import annotations

from typing import Iterable

from lunar_ice_bpc.exact.bpc.core.column_signature import column_signature_from_journey
from lunar_ice_bpc.exact.core.journey import JourneyColumn


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
            rows.append(
                {
                    "node_id": str(node_id),
                    "cg_iter": int(cg_iter),
                    "worker_kind": str(worker_payload.get("worker_kind") or "unknown"),
                    "hidden_task_set": list(signature.task_set),
                    "hidden_sequence": [list(row) for row in signature.ordered_task_sequences],
                    "hidden_path_signature": [list(row) for row in signature.path_option_signature],
                    "hidden_true_rc": round(float(true_rc), 9),
                    "hidden_column_signature": repr(signature),
                    "miss_reason_guess": str(worker_payload.get("miss_reason_guess") or "worker_candidate_budget"),
                    "worker_candidate_budget": int(worker_payload.get("worker_candidate_budget") or 0),
                    "worker_generated_count": int(worker_payload.get("worker_generated_count") or 0),
                    "final_judge_generated_count": int(final_judge_payload.get("candidate_round_count") or 0),
                }
            )
    return {
        "schema_version": "lunar_ice_bpc.b2_hidden_negative_audit.v1",
        "status": "HIDDEN_NEGATIVE_FOUND" if rows else "NO_HIDDEN_NEGATIVE",
        "hidden_negative_count": len(rows),
        "mutates_solver": False,
        "changes_certificate_semantics": False,
        "rows": rows,
    }


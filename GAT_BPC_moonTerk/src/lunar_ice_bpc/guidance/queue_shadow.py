"""Diagnostic-only proof-queue keys.

These functions are intentionally not imported by the Native exact solver.
They support snapshot replay for Q1--Q4 while online proof ordering stays Q0.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class QueueShadowState:
    partial_rc: float
    guidance_score: float
    creation_sequence_id: int
    heuristic_completion_priority: float = 0.0
    heuristic_proof_risk: float = 0.0
    canonical_state_signature: str = ""
    canonical_path_signature: str = ""
    terminal_reduced_cost: float | None = None


def queue_shadow_key(policy_id: str, state: QueueShadowState) -> tuple[Any, ...]:
    policy = str(policy_id)
    if policy == "Q0":
        return (float(state.partial_rc), int(state.creation_sequence_id))
    if policy == "Q1":
        return (
            float(state.partial_rc),
            -float(state.guidance_score),
            int(state.creation_sequence_id),
        )
    if policy == "Q2":
        return (
            float(state.heuristic_completion_priority),
            float(state.partial_rc),
            -float(state.guidance_score),
            int(state.creation_sequence_id),
        )
    if policy == "Q3":
        return (
            float(state.heuristic_proof_risk),
            float(state.partial_rc),
            -float(state.guidance_score),
            int(state.creation_sequence_id),
        )
    if policy == "Q4":
        return (
            float(state.heuristic_completion_priority),
            float(state.heuristic_proof_risk),
            float(state.partial_rc),
            -float(state.guidance_score),
            int(state.creation_sequence_id),
        )
    raise ValueError(f"unsupported queue shadow policy {policy!r}")


def cross_policy_alignment_key(state: QueueShadowState) -> tuple[str, str]:
    if not state.canonical_state_signature or not state.canonical_path_signature:
        raise ValueError("cross-policy replay requires canonical signatures")
    return state.canonical_state_signature, state.canonical_path_signature


def exhaustive_queue_policy_differential(
    states: tuple[QueueShadowState, ...],
    *,
    threshold: float,
) -> dict[str, Any]:
    """Audit all shadow keys against one fully observed terminal universe."""

    if not states:
        raise ValueError("queue differential requires at least one state")
    signatures = [cross_policy_alignment_key(state) for state in states]
    if len(signatures) != len(set(signatures)):
        raise ValueError("queue differential state signatures must be unique")
    terminal_values = [
        float(state.terminal_reduced_cost)
        for state in states
        if state.terminal_reduced_cost is not None
    ]
    if not terminal_values:
        raise ValueError("queue differential requires terminal RC observations")
    expected_global_min = min(terminal_values)
    expected_below = any(value < float(threshold) for value in terminal_values)
    policies = {}
    for policy in ("Q0", "Q1", "Q2", "Q3", "Q4"):
        ordered = tuple(sorted(states, key=lambda state: queue_shadow_key(policy, state)))
        observed = [
            float(state.terminal_reduced_cost)
            for state in ordered
            if state.terminal_reduced_cost is not None
        ]
        policies[policy] = {
            "ordering": [
                list(cross_policy_alignment_key(state))
                for state in ordered
            ],
            "global_min_rc": min(observed),
            "has_rc_below_threshold": any(
                value < float(threshold) for value in observed
            ),
            "global_min_matches": min(observed) == expected_global_min,
            "threshold_result_matches": (
                any(value < float(threshold) for value in observed)
                == expected_below
            ),
        }
    return {
        "mode": "shadow_exhaustive_differential_only",
        "expected_global_min_rc": expected_global_min,
        "expected_has_rc_below_threshold": expected_below,
        "all_policies_match": all(
            row["global_min_matches"] and row["threshold_result_matches"]
            for row in policies.values()
        ),
        "policies": policies,
        "mutates_solver": False,
        "can_certify": False,
    }

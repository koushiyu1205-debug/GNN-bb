"""B2 completion-bound policy boundary."""

from __future__ import annotations


def build_completion_bound_tail_policy(
    *,
    ordering_enabled: bool = True,
    audit_enabled: bool = True,
    pruning_opt_in: bool = False,
    branch_context_active: bool = False,
    cut_context_active: bool = False,
) -> dict:
    pruning_enabled = bool(pruning_opt_in) and not bool(branch_context_active) and not bool(cut_context_active)
    return {
        "schema_version": "lunar_ice_bpc.b2_completion_bound_policy.v1",
        "ordering_enabled": bool(ordering_enabled),
        "audit_enabled": bool(audit_enabled),
        "pruning_opt_in": bool(pruning_opt_in),
        "pruning_enabled": pruning_enabled,
        "branch_context_active": bool(branch_context_active),
        "cut_context_active": bool(cut_context_active),
        "can_certify_no_negative": False,
        "note": (
            "Completion-bound pruning is disabled because branch/cut context is active."
            if bool(pruning_opt_in) and not pruning_enabled
            else "B2 completion-bound structure is ordering/audit by default."
        ),
    }


"""Exact-safe validation helpers for development branch snapshots."""

from __future__ import annotations


def deep_target_node_exact_safe(payload: dict) -> bool:
    """Validate a certified, actionable tree node before its P0 branch.

    Legacy tree snapshots expose branch/cut proof evidence through the bound
    final-judge payload.  New snapshots also carry explicit audit booleans.
    Both schemas must satisfy the same mathematical gates.
    """

    final_judge = payload.get("final_judge") or {}
    ledger = payload.get("certificate_ledger") or {}
    probe = payload.get("fractional_branch_probe") or {}
    candidates = list(probe.get("candidates") or ())
    branch_pricing_pass = (
        payload.get("branch_pricing_audit_pass") is True
        if "branch_pricing_audit_pass" in payload
        else (
            payload.get(
                "all_priced_columns_satisfy_branch_context"
            )
            is True
            and final_judge.get(
                "all_priced_columns_satisfy_branch_context"
            )
            is True
        )
    )
    cut_count = int(payload.get("cut_count") or 0)
    cut_pricing_pass = (
        payload.get("cut_pricing_audit_pass") is True
        if "cut_pricing_audit_pass" in payload
        else bool(
            cut_count == 0
            or (
                final_judge.get("cut_context_active") is True
                and final_judge.get(
                    "live_cut_certificate_supported"
                )
                is True
                and str(
                    final_judge.get("pricing_cut_context_hash") or ""
                )
                == str(
                    payload.get("active_cut_context_hash") or ""
                )
            )
        )
    )
    before_hash = str(
        payload.get("legal_branch_shortlist_hash_before_sort") or ""
    )
    after_hash = str(
        payload.get("legal_branch_shortlist_hash_after_sort") or ""
    )
    return bool(
        payload.get("node_status") == "NODE_LP_CERTIFIED"
        and payload.get("certificate_scope")
        == "BPC_NODE_LP_CERTIFIED"
        and payload.get("pricing_state") == "CERTIFIED_NO_NEGATIVE"
        and payload.get("node_lp_bound_official")
        and payload.get("uses_true_dual_bpc_certificate")
        and ledger.get("valid")
        and payload.get("manual_rc_audit_pass")
        and payload.get("pricing_rc_audit_pass")
        and payload.get("final_judge_certifying_proof_kind")
        and branch_pricing_pass
        and cut_pricing_pass
        and payload.get("fractional_branch_probe_status")
        == "FRACTIONAL_BRANCH_PROBE_READY"
        and len(candidates) >= 3
        and before_hash
        and before_hash == after_hash
        and int(
            payload.get("guidance_branch_pair_drop_count") or 0
        )
        == 0
    )


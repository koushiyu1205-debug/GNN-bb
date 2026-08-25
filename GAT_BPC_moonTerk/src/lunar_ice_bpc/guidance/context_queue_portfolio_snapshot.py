"""Reconstruct a literal-Q0 request from one frozen V5 fallback snapshot."""

from __future__ import annotations

from lunar_ice_bpc.exact.bpc.pricing.backends.base import BackendPricingRequest
from lunar_ice_bpc.exact.core.branching import branch_context_from_payload
from lunar_ice_bpc.exact.core.cuts import cut_context_from_payload
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals


def literal_q0_request_from_snapshot(data, snapshot: dict) -> BackendPricingRequest:
    if data.instance_content_hash != str(snapshot.get("instance_content_hash") or ""):
        raise ValueError("portfolio snapshot instance binding mismatch")
    duals = dict(snapshot.get("true_duals") or {})
    trajectory = dict(snapshot.get("trajectory_features") or {})
    previous_policy = str(trajectory.get("previous_queue_policy_id") or "")
    previous_q0 = previous_policy == "Q0"
    return BackendPricingRequest(
        data=data,
        true_duals=JourneyDuals(
            cover=dict(duals.get("task_duals") or duals.get("cover") or {}),
            fleet_limit=float(
                duals.get("fleet_dual")
                if duals.get("fleet_dual") is not None
                else duals.get("fleet_limit") or 0.0
            ),
            cuts=dict(duals.get("cut_duals") or duals.get("cuts") or {}),
        ),
        mode="exact_proof",
        objective_mode="official",
        pricing_lifecycle_scope=str(
            snapshot.get("pricing_lifecycle_scope") or "root_cg"
        ),
        branch_context=branch_context_from_payload(
            snapshot.get("branch_context") or {}
        ),
        cut_context=cut_context_from_payload(snapshot.get("cut_context") or {}),
        proof_queue_policy_id="Q0",
        proof_tail_fallback_context=True,
        proof_tail_active_column_count=_optional_int(
            snapshot.get("active_column_count")
        ),
        proof_tail_active_task_sets=(
            None if snapshot.get("active_task_sets") is None else
            tuple(
                tuple(str(value) for value in row)
                for row in snapshot["active_task_sets"]
            )
        ),
        proof_tail_active_column_signature_hashes=(
            None if snapshot.get("active_column_signature_hashes") is None else
            tuple(str(value) for value in snapshot["active_column_signature_hashes"])
        ),
        proof_tail_round_index=_optional_int(snapshot.get("round")),
        proof_tail_previous_queue_policy_id=previous_policy,
        proof_tail_previous_proof_wall_sec=(
            _optional_float(trajectory.get("previous_proof_pass_wall_time"))
            if previous_q0 else None
        ),
        proof_tail_previous_processed_labels=(
            _optional_int(trajectory.get("previous_proof_processed_labels"))
            if previous_q0 else None
        ),
        proof_tail_previous_dominance_candidate_checks=(
            _optional_int(trajectory.get("previous_dominance_candidate_checks"))
            if previous_q0 else None
        ),
        proof_tail_previous_dominance_wall_sec=(
            _optional_float(trajectory.get("previous_dominance_wall_sec"))
            if previous_q0 else None
        ),
        proof_tail_previous_max_visited_bucket_size=(
            _optional_int(trajectory.get("previous_max_visited_bucket_size"))
            if previous_q0 else None
        ),
        proof_tail_dual_delta_l1=_optional_float(
            trajectory.get("dual_l1_delta_from_previous")
        ),
        proof_tail_v5_midpoint_wall_sec=_optional_float(
            snapshot.get("bidirectional_midpoint_prepass_wall_sec")
        ),
        proof_tail_v5_midpoint_reason=str(
            snapshot.get("bidirectional_midpoint_fallback_reason")
            or "snapshot_replay"
        ),
        instance_hash=data.instance_content_hash,
        config_hash=str(snapshot["config_hash"]),
        engine_hash=str(snapshot["engine_hash"]),
        rmp_iteration_id=str(snapshot.get("rmp_iteration_id") or ""),
        cut_lineage_hash=str(
            dict(snapshot.get("cut_lineage") or {}).get("cut_lineage_hash") or ""
        ),
        live_cut_policy_hash=str(snapshot.get("live_cut_policy_hash") or ""),
        separator_policy_version=str(snapshot.get("separator_policy_version") or ""),
    )


def _optional_int(value):
    return None if value is None else int(value)


def _optional_float(value):
    return None if value is None else float(value)

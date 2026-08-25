#!/usr/bin/env python3
"""Fresh-process replay of one P0V5 fallback snapshot under Q0/QG2 arms."""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from math import isfinite, log1p
from pathlib import Path
import random
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.bpc.guidance.contracts import (  # noqa: E402
    CanonicalSolveBindingV2,
    GUIDANCE_MODE_TASK_ARC,
    PricingOrderingHintsV2,
    QG2_LABEL_STATE_SCHEMA_V1,
    canonical_arc_candidate_id,
)
from lunar_ice_bpc.exact.bpc.pricing.backends import (  # noqa: E402
    BackendPricingRequest,
    NATIVE_BIDIRECTIONAL_ROOT_PARTIAL_HYBRID_BACKEND_ID,
    NativeRcsppInprocessBackend,
)
from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import (  # noqa: E402
    NATIVE_INPROCESS_BACKEND_ID,
    _native_request_payload,
    run_native_counterfactual_prefix_raw,
)
from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (  # noqa: E402
    spprc_engine_build_hash,
)
from lunar_ice_bpc.exact.bpc.core.column_signature import (  # noqa: E402
    column_semantic_signature_hash,
)
from lunar_ice_bpc.exact.core.branching import branch_context_from_payload  # noqa: E402
from lunar_ice_bpc.exact.core.cuts import (  # noqa: E402
    cut_context_from_payload,
    stable_payload_hash,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals  # noqa: E402
from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (  # noqa: E402
    qg2_exact_action_policy_hash_from_snapshot,
)
from lunar_ice_bpc.guidance.qg2_admission_supervision import (  # noqa: E402
    QG2_QUEUE_ACTION_SURFACE_V1,
    QG2_SUPERVISION_SCHEMA_V2,
)
from lunar_ice_bpc.guidance.qg2_admission_supervision_v3 import (  # noqa: E402
    QG2_V3_SUPERVISION_SCHEMA,
)
from lunar_ice_bpc.guidance.qgr1_supervision import (  # noqa: E402
    QGR1_ACTION_SURFACE_V1,
    QGR1_SUPERVISION_SCHEMA_V1,
)


SNAPSHOT_SCHEMAS = {
    "lunar_ice_bpc.p0v3_root_policy_state_snapshot.v1",
    "lunar_ice_bpc.p0v5_proof_tail_fallback_snapshot.v1",
    "lunar_ice_bpc.p0v5_proof_tail_fallback_snapshot.v2",
}
POTENTIAL_SCHEMA = "lunar_ice_bpc.p0v5_qg2_label_state_potential.v2"
QGR1_POTENTIAL_SCHEMA = (
    "lunar_ice_bpc.p0v5_qgr1_depth_residual_potential.v1"
)
OUTPUT_SCHEMA = "lunar_ice_bpc.p0v5_qg2_snapshot_replay.v3"
TRAJECTORY_FEATURE_SEMANTICS = (
    "p0v5_qg2_preaction_trajectory_missingness.v2"
)
POLICIES = (
    "Q0", "QD1", "QB1", "QG2", "QGR1", "QPF0", "QPD1",
    "Q0_PREFIX", "QD1_PREFIX", "QT_COLLECT", "QT_CONTINUE", "QT_REVERT",
    "QT_MODEL",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--policy", choices=POLICIES, required=True)
    parser.add_argument("--potential")
    parser.add_argument("--random-seed", type=int)
    parser.add_argument("--repeat-index", type=int, default=1)
    parser.add_argument("--guidance-bucket-width", type=float, default=1.0e-3)
    parser.add_argument("--wall-time-limit-sec", type=float, default=300.0)
    parser.add_argument("--memory-limit-gb", type=float, default=10.867)
    parser.add_argument("--label-trace", action="store_true")
    parser.add_argument("--label-trace-max-rows", type=int, default=50_000)
    parser.add_argument(
        "--label-trace-sampling-mode",
        choices=("prefix_v1", "qgr1_stratified_reservoir_v1"),
        default="prefix_v1",
    )
    parser.add_argument("--label-trace-seed", type=int)
    parser.add_argument("--preference-cap-per-family", type=int, default=12_500)
    parser.add_argument("--surface-reservoir-count", type=int, default=3_125)
    parser.add_argument("--surface-labels-per-bucket", type=int, default=8)
    parser.add_argument("--witness-route-cap", type=int, default=512)
    parser.add_argument("--witness-ancestor-cap", type=int, default=25_000)
    parser.add_argument(
        "--frontier-probe-boundary",
        type=int,
        choices=(4096, 8192, 16384),
        default=4096,
    )
    parser.add_argument(
        "--frontier-observation-boundaries",
        type=int,
        nargs="*",
        default=(),
        help=(
            "Canonical temporal snapshot prefix, for example "
            "4096 8192 16384. Empty preserves the legacy V7 probe."
        ),
    )
    parser.add_argument(
        "--counterfactual-max-rollout-budget",
        type=int,
        choices=(128, 512, 2048),
        default=2048,
    )
    parser.add_argument(
        "--frontier-trial-pop-budget",
        type=int,
        choices=(128, 512, 2048),
        default=128,
    )
    parser.add_argument(
        "--source-backend-id",
        default=NATIVE_BIDIRECTIONAL_ROOT_PARTIAL_HYBRID_BACKEND_ID,
    )
    parser.add_argument(
        "--diagnostic-rebind-source-engine",
        action="store_true",
        help="V7 overhead-only rebind; forbidden for learned/performance outcomes.",
    )
    args = parser.parse_args()

    data = load_lunar_ice_data(_load(_resolve(args.instance)))
    snapshot_path = _resolve(args.snapshot)
    snapshot = _load(snapshot_path)
    original_snapshot_binding = {
        "engine_hash": str(snapshot.get("engine_hash") or ""),
        "state_hash": str(snapshot.get("state_hash") or ""),
    }
    if args.diagnostic_rebind_source_engine:
        if args.policy not in {"Q0", "QPF0", "Q0_PREFIX", "QD1_PREFIX"}:
            raise SystemExit(
                "diagnostic engine rebind is limited to outcome-free Q0/prefix diagnostics"
            )
        snapshot = dict(snapshot)
        snapshot["engine_hash"] = spprc_engine_build_hash(str(args.source_backend_id))
        snapshot.pop("state_hash", None)
        snapshot["state_hash"] = _hash(snapshot)
    _validate_snapshot(
        data,
        snapshot,
        source_backend_id=str(args.source_backend_id),
    )
    source_exact_action_policy_hash = (
        qg2_exact_action_policy_hash_from_snapshot(snapshot)
    )
    recorded_action_policy_hash = str(
        snapshot.get("exact_action_policy_hash") or ""
    )
    if (
        recorded_action_policy_hash
        and recorded_action_policy_hash != source_exact_action_policy_hash
    ):
        raise SystemExit("snapshot exact action policy hash mismatch")
    if int(data.scale) not in {30, 50}:
        raise SystemExit("QG2 oracle replay accepts only scale30/50")
    if args.policy == "QG2" and not args.potential and args.random_seed is None:
        raise SystemExit("QG2 requires --potential or --random-seed")
    if args.policy == "QGR1" and not args.potential:
        raise SystemExit("QGR1 requires a frozen trained potential")
    if args.policy == "QGR1" and args.random_seed is not None:
        raise SystemExit("QGR1 random potential is forbidden")
    if args.policy not in {"QG2", "QGR1"} and (
        args.potential or args.random_seed is not None
    ):
        raise SystemExit("potential/random guidance requires QG2 or QGR1")
    if args.policy == "QGR1" and float(args.guidance_bucket_width) != 1.0e-4:
        raise SystemExit("QGR1 bucket width is frozen at 1e-4")

    true_duals = dict(snapshot.get("true_duals") or {})
    trajectory = dict(snapshot.get("trajectory_features") or {})
    previous_policy = str(trajectory.get("previous_queue_policy_id") or "")
    previous_is_literal_q0 = previous_policy == "Q0"
    admission_target = int(
        snapshot.get("exact_admission_batch_size")
        or (64 if int(data.scale) == 30 else 128)
    )
    raw_negative_pool_target = int(
        snapshot.get("exact_raw_negative_pool_size")
        or 4 * admission_target
    )
    trace_seed = (
        int(args.label_trace_seed)
        if args.label_trace_seed is not None
        else int(hashlib.sha256(
            str(snapshot["state_hash"]).encode("utf-8")
        ).hexdigest()[:16], 16)
    )
    frontier_probe_mode = {
        "QPF0": "collect_force_q0",
        "QPD1": "force_qd1",
        "QT_COLLECT": "collect_trial",
        "QT_CONTINUE": "force_trial_continue",
        "QT_REVERT": "force_trial_revert",
    }.get(str(args.policy), "disabled")
    counterfactual_prefix_mode = {
        "Q0_PREFIX": "counterfactual_q0_prefix",
        "QD1_PREFIX": "counterfactual_qd1_prefix",
    }.get(str(args.policy), "disabled")
    frontier_context = _frontier_preaction_context(snapshot, trajectory)
    request = BackendPricingRequest(
        data=data,
        true_duals=JourneyDuals(
            cover=dict(true_duals.get("task_duals") or true_duals.get("cover") or {}),
            fleet_limit=float(
                true_duals.get("fleet_dual")
                if true_duals.get("fleet_dual") is not None
                else true_duals.get("fleet_limit") or 0.0
            ),
            cuts=dict(true_duals.get("cut_duals") or true_duals.get("cuts") or {}),
        ),
        mode="exact_proof",
        objective_mode="official",
        pricing_lifecycle_scope=str(
            snapshot.get("pricing_lifecycle_scope") or "root_cg"
        ),
        branch_context=branch_context_from_payload(snapshot.get("branch_context") or {}),
        cut_context=cut_context_from_payload(snapshot.get("cut_context") or {}),
        wall_time_limit_sec=max(0.001, float(args.wall_time_limit_sec)),
        memory_limit_gb=max(0.0, float(args.memory_limit_gb)),
        completion_bound_enabled=False,
        subset_dominance_enabled=True,
        exact_negative_escape_enabled=(
            False
            if counterfactual_prefix_mode != "disabled"
            else bool(snapshot.get("exact_negative_escape_enabled", True))
        ),
        exact_admission_batch_size=admission_target,
        exact_raw_negative_pool_size=raw_negative_pool_target,
        exact_negative_escape_policy_id=str(
            snapshot.get("exact_negative_escape_policy_id")
            or "diverse_raw_4x_then_p0v4_selector_v1"
        ),
        proof_queue_policy_id=(
            "Q0"
            if args.policy in {
                "QPF0", "QPD1", "Q0_PREFIX", "QD1_PREFIX",
                "QT_COLLECT", "QT_CONTINUE", "QT_REVERT",
                "QT_MODEL",
            }
            else str(args.policy)
        ),
        proof_queue_guidance_bucket_width=float(args.guidance_bucket_width),
        proof_tail_fallback_context=True,
        proof_tail_label_trace_enabled=bool(args.label_trace),
        proof_tail_label_trace_max_rows=max(
            1, min(100_000, int(args.label_trace_max_rows))
        ),
        proof_tail_label_trace_sampling_mode=str(
            args.label_trace_sampling_mode
        ),
        proof_tail_label_trace_seed=trace_seed,
        proof_tail_preference_cap_per_family=max(
            1, int(args.preference_cap_per_family)
        ),
        proof_tail_surface_reservoir_count=max(
            1, int(args.surface_reservoir_count)
        ),
        proof_tail_surface_labels_per_bucket=max(
            2, int(args.surface_labels_per_bucket)
        ),
        proof_tail_witness_route_cap=max(1, int(args.witness_route_cap)),
        proof_tail_witness_ancestor_cap=max(
            1, int(args.witness_ancestor_cap)
        ),
        proof_tail_active_column_count=_optional_int(
            snapshot.get("active_column_count")
        ),
        proof_tail_active_task_sets=_active_task_sets(
            snapshot.get("active_task_sets")
        ),
        proof_tail_active_column_signature_hashes=(
            None
            if snapshot.get("active_column_signature_hashes") is None
            else tuple(
                str(value)
                for value in snapshot.get("active_column_signature_hashes")
            )
        ),
        proof_tail_round_index=_optional_int(snapshot.get("round")),
        proof_tail_previous_queue_policy_id=previous_policy,
        proof_tail_previous_proof_wall_sec=(
            _optional_float(trajectory.get("previous_proof_pass_wall_time"))
            if previous_is_literal_q0 else None
        ),
        proof_tail_previous_processed_labels=(
            _optional_int(
                trajectory.get("previous_proof_processed_labels")
                if trajectory.get("previous_proof_processed_labels") is not None
                else trajectory.get("previous_harvest_processed_labels")
            ) if previous_is_literal_q0 else None
        ),
        proof_tail_previous_dominance_candidate_checks=(
            _optional_int(trajectory.get("previous_dominance_candidate_checks"))
            if previous_is_literal_q0 else None
        ),
        proof_tail_previous_dominance_wall_sec=(
            _optional_float(trajectory.get("previous_dominance_wall_sec"))
            if previous_is_literal_q0 else None
        ),
        proof_tail_previous_max_visited_bucket_size=(
            _optional_int(trajectory.get("previous_max_visited_bucket_size"))
            if previous_is_literal_q0 else None
        ),
        proof_tail_dual_delta_l1=_optional_float(
            trajectory.get("dual_l1_delta_from_previous")
        ),
        proof_tail_v5_midpoint_wall_sec=_optional_float(
            snapshot.get("bidirectional_midpoint_prepass_wall_sec")
            if snapshot.get("bidirectional_midpoint_prepass_wall_sec") is not None
            else trajectory.get("v5_midpoint_wall_sec")
        ),
        proof_tail_v5_midpoint_reason=str(
            snapshot.get("bidirectional_midpoint_fallback_reason") or "snapshot_replay"
        ),
        proof_tail_frontier_probe_mode=frontier_probe_mode,
        proof_tail_frontier_probe_boundary=int(args.frontier_probe_boundary),
        proof_tail_frontier_trial_pop_budget=(
            int(args.frontier_trial_pop_budget)
            if str(args.policy).startswith("QT_") else 0
        ),
        proof_tail_frontier_observation_boundaries=tuple(
            args.frontier_observation_boundaries
        ),
        proof_tail_frontier_context_features=frontier_context,
        proof_tail_counterfactual_prefix_mode=counterfactual_prefix_mode,
        proof_tail_counterfactual_prefix_boundary=4096,
        proof_tail_counterfactual_rollout_checkpoints=(128, 512, 2048),
        proof_tail_counterfactual_max_rollout_budget=int(
            args.counterfactual_max_rollout_budget
        ),
        proof_tail_counterfactual_label_sample_cap=256,
        proof_tail_counterfactual_sampling_seed=trace_seed,
        instance_hash=data.instance_content_hash,
        config_hash=stable_payload_hash(
            {
                "schema_version": "lunar_ice_bpc.p0v5_qg2_replay_config.v1",
                "source_state_hash": str(snapshot["state_hash"]),
                "policy": str(args.policy),
                "bucket_width": float(args.guidance_bucket_width),
                "label_trace": bool(args.label_trace),
                "label_trace_sampling_mode": str(
                    args.label_trace_sampling_mode
                ),
                "label_trace_seed": trace_seed,
                "counterfactual_max_rollout_budget": int(
                    args.counterfactual_max_rollout_budget
                ),
                "frontier_probe_boundary": int(args.frontier_probe_boundary),
                "frontier_observation_boundaries": list(
                    args.frontier_observation_boundaries
                ),
            }
        ),
        # The live QG2 binding is created on the outer V5 hybrid request and
        # is intentionally preserved when that request enters P0V4 fallback.
        # Keep that exact composite hash here; record the concrete in-process
        # implementation hash separately in replay telemetry below.
        engine_hash=str(snapshot["engine_hash"]),
        rmp_iteration_id=str(snapshot.get("rmp_iteration_id") or ""),
        cut_lineage_hash=stable_payload_hash(snapshot.get("cut_lineage") or {}),
        live_cut_policy_hash=str(snapshot.get("live_cut_policy_hash") or ""),
        separator_policy_version=str(snapshot.get("separator_policy_version") or ""),
    )

    potential_payload: dict = {}
    if args.policy in {"QG2", "QGR1"}:
        task, arc, coefficients, potential_payload = _guidance(
            data=data,
            snapshot=snapshot,
            path=None if not args.potential else _resolve(args.potential),
            random_seed=args.random_seed,
            policy=str(args.policy),
        )
        request = replace(
            request,
            guidance_mode=GUIDANCE_MODE_TASK_ARC,
            guidance_feature_schema_version=str(
                potential_payload.get("feature_schema_version")
                or "lunar_ice_bpc.p0v5_qg2_features.v1"
            ),
            guidance_normalization_version=str(
                potential_payload.get("normalization_version")
                or "development_qg2_potential.v1"
            ),
            guidance_checkpoint_id=str(
                potential_payload.get("potential_id")
                or _hash(potential_payload)
            ),
            guidance_ood_policy_version="exact_state_hash_only.v1",
        )

    temporal_runtime_telemetry = {}
    if args.policy == "QT_MODEL":
        from lunar_ice_bpc.guidance.temporal_frontier_gat_runtime_v1 import (
            prepare_temporal_frontier_request_from_environment,
        )

        request, temporal_runtime_telemetry = (
            prepare_temporal_frontier_request_from_environment(request)
        )

    if counterfactual_prefix_mode != "disabled":
        started = perf_counter()
        raw = run_native_counterfactual_prefix_raw(request)
        fresh_wall = perf_counter() - started
        prefix = dict(
            (raw.get("telemetry") or {}).get(
                "proof_queue_counterfactual_prefix"
            )
            or {}
        )
        native_request_payload = _native_request_payload(request)
        output = {
            "schema_version": (
                "lunar_ice_bpc.p0v5_counterfactual_prefix_replay.v1"
            ),
            "development_only": True,
            "performance_authority": False,
            "truncated_diagnostic": True,
            "exact": False,
            "certificate": None,
            "routes": [],
            "instance_id": data.instance_id,
            "instance_content_hash": data.instance_content_hash,
            "scale": int(data.scale),
            "source_snapshot_path": str(snapshot_path),
            "source_state_hash": str(snapshot["state_hash"]),
            "source_config_hash": str(snapshot["config_hash"]),
            "source_engine_hash": str(snapshot["engine_hash"]),
            "policy": str(args.policy),
            "repeat_index": int(args.repeat_index),
            "requested_wall_time_limit_sec": float(args.wall_time_limit_sec),
            "requested_memory_limit_gb": float(args.memory_limit_gb),
            "engine_status": str(raw.get("status") or "UNKNOWN"),
            "search_exhaustive": False,
            "frontier_empty": False,
            "labels_dropped": bool(raw.get("labels_dropped")),
            "prefix": prefix,
            "native_wall_sec": float(
                (raw.get("telemetry") or {}).get("wall_time_seconds") or 0.0
            ),
            "total_fresh_process_wall_sec": fresh_wall,
            "replay_engine_hash": spprc_engine_build_hash(
                NATIVE_INPROCESS_BACKEND_ID
            ),
            "replay_binding": (
                CanonicalSolveBindingV2.from_backend_request(request).to_payload()
            ),
            "request_bindings": dict(raw.get("request_bindings") or {}),
            "native_build_info": dict(raw.get("build_info") or {}),
            "graph_inputs": {
                "tasks": native_request_payload["tasks"],
                "arcs": native_request_payload["arcs"],
                "true_task_duals": {
                    str(row["id"]): float(row["dual"])
                    for row in native_request_payload["tasks"]
                },
                "branch_pairs": [
                    [str(row["task_a"]), str(row["task_b"])]
                    for row in native_request_payload.get("branch_decisions") or ()
                ],
                "cut_task_sets": [
                    list(map(str, row.get("tasks") or ()))
                    for row in native_request_payload.get("cuts") or ()
                ],
            },
        }
        target = _resolve(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        print(json.dumps({
            "status": "COMPLETE" if bool(prefix.get("complete")) else "INCOMPLETE",
            "policy": str(args.policy),
            "wall_sec": fresh_wall,
            "output": str(target),
        }, sort_keys=True))
        return 0

    started = perf_counter()
    result = NativeRcsppInprocessBackend().solve(request)
    backend_solve_wall = perf_counter() - started
    diversity_audit = _diversity_milestone_audit(
        result=result,
        request=request,
        admission_target=admission_target,
    )
    admission_milestone_wall = perf_counter() - started
    wall = perf_counter() - started
    telemetry = dict(result.telemetry or {})
    negative_escape_triggered = bool(
        telemetry.get("negative_escape_triggered")
    )
    selected_diverse_count = int(
        diversity_audit.get("selected_diverse_negative_count") or 0
    )
    master_entry_audit_available = bool(
        diversity_audit.get("selected_master_entry_audit_available")
    )
    selected_master_ready_count = int(
        diversity_audit.get("selected_master_ready_negative_count") or 0
    )
    escape_milestone_reached = bool(
        negative_escape_triggered
        and (
            selected_master_ready_count >= admission_target
            if master_entry_audit_available
            else selected_diverse_count >= admission_target
        )
    )
    proof_milestone_reached = bool(
        result.search_exhaustive
        and result.frontier_empty
        and not result.labels_dropped
    )
    milestone_kind = (
        "ADMISSION_BATCH_READY"
        if escape_milestone_reached
        else "EXACT_PROOF_COMPLETION"
        if proof_milestone_reached
        else "RIGHT_CENSORED"
    )
    native_search_wall = float(telemetry.get("wall_time_seconds") or 0.0)
    backend_reconstruction_audit_wall = max(
        0.0, backend_solve_wall - native_search_wall
    )
    true_rc_reaudit_wall = float(
        diversity_audit.get("true_rc_audit_wall_time_sec") or 0.0
    )
    diversity_selector_wall = float(
        diversity_audit.get("diversity_selection_wall_time_sec") or 0.0
    )
    master_entry_audit_wall = float(
        diversity_audit.get(
            "selected_master_entry_audit_wall_time_sec"
        ) or 0.0
    )
    admission_audit_wall = (
        backend_reconstruction_audit_wall
        + true_rc_reaudit_wall
        + master_entry_audit_wall
    )
    admission_unattributed_wall = max(
        0.0,
        admission_milestone_wall
        - native_search_wall
        - admission_audit_wall
        - diversity_selector_wall,
    )
    raw_negative_milestone_wall = telemetry.get(
        "first_true_negative_wall_time_seconds"
    )
    post_native_fixed_pipeline_wall = (
        max(0.0, admission_milestone_wall - native_search_wall)
        if escape_milestone_reached
        else None
    )
    raw_to_native_harvest_wall = (
        max(0.0, native_search_wall - float(raw_negative_milestone_wall))
        if escape_milestone_reached
        and raw_negative_milestone_wall is not None
        else None
    )
    output = {
        "schema_version": OUTPUT_SCHEMA,
        "development_only": True,
        "deployable": False,
        "ordering_only": True,
        "can_filter": False,
        "can_prune": False,
        "can_change_reduced_cost": False,
        "can_certify_from_guidance": False,
        "instance_id": data.instance_id,
        "instance_content_hash": data.instance_content_hash,
        "scale": int(data.scale),
        "source_snapshot_path": str(snapshot_path),
        "diagnostic_engine_rebind": bool(args.diagnostic_rebind_source_engine),
        "original_snapshot_binding": original_snapshot_binding,
        "source_state_hash": str(snapshot["state_hash"]),
        "source_backend_id": str(args.source_backend_id),
        "source_engine_hash": str(snapshot["engine_hash"]),
        "source_config_hash": str(snapshot["config_hash"]),
        "source_exact_action_policy_hash": (
            source_exact_action_policy_hash
        ),
        "replay_backend_id": NATIVE_INPROCESS_BACKEND_ID,
        "replay_engine_hash": spprc_engine_build_hash(
            NATIVE_INPROCESS_BACKEND_ID
        ),
        "source_round": int(snapshot.get("round") or 0),
        "policy": str(args.policy),
        "potential_id": potential_payload.get("potential_id"),
        "potential_file_sha256": (
            _sha256_file(_resolve(args.potential))
            if args.potential
            else ""
        ),
        "random_seed": (
            int(args.random_seed)
            if args.random_seed is not None
            else None
        ),
        "repeat_index": int(args.repeat_index),
        "guidance_bucket_width": float(args.guidance_bucket_width),
        "requested_wall_time_limit_sec": float(
            args.wall_time_limit_sec
        ),
        "requested_memory_limit_gb": float(args.memory_limit_gb),
        "requested_label_trace": bool(args.label_trace),
        "requested_label_trace_max_rows": int(
            args.label_trace_max_rows
        ),
        "fresh_process_arm": True,
        "replay_binding": CanonicalSolveBindingV2.from_backend_request(request).to_payload(),
        "engine_status": result.engine_status,
        "search_exhaustive": bool(result.search_exhaustive),
        "frontier_empty": bool(result.frontier_empty),
        "labels_dropped": bool(result.labels_dropped),
        "best_found_rc": result.best_found_rc,
        "global_min_rc": result.global_min_rc,
        "global_min_rc_is_exact": bool(result.global_min_rc_is_exact),
        "proved_no_rc_below": result.proved_no_rc_below,
        "certificate_blockers": list(result.certificate_blockers),
        "column_count": len(result.columns),
        "exact_admission_batch_size": admission_target,
        "exact_raw_negative_pool_size": raw_negative_pool_target,
        "negative_escape_triggered": negative_escape_triggered,
        "raw_unique_negative_count": int(
            telemetry.get("raw_unique_negative_count") or 0
        ),
        "selected_diverse_negative_count": selected_diverse_count,
        "selected_master_ready_negative_count": (
            selected_master_ready_count
            if master_entry_audit_available
            else None
        ),
        "diversity_milestone_audit": diversity_audit,
        "milestone_kind": milestone_kind,
        "milestone_reached": bool(
            escape_milestone_reached or proof_milestone_reached
        ),
        "milestone_wall_sec": round(
            admission_milestone_wall
            if escape_milestone_reached
            else wall,
            9,
        ),
        "raw_negative_milestone_wall_sec": raw_negative_milestone_wall,
        "admission_milestone_wall_sec": (
            round(admission_milestone_wall, 9)
            if escape_milestone_reached
            else None
        ),
        "admission_time_objective": "min_time_to_master_ready_frozen_batch",
        "backend_solve_wall_sec": round(backend_solve_wall, 9),
        "native_search_wall_sec": round(native_search_wall, 9),
        "backend_reconstruction_audit_wall_sec": round(
            backend_reconstruction_audit_wall, 9
        ),
        "true_rc_reaudit_wall_sec": round(true_rc_reaudit_wall, 9),
        "diversity_selector_wall_sec": round(
            diversity_selector_wall, 9
        ),
        "master_entry_audit_wall_sec": round(
            master_entry_audit_wall, 9
        ),
        "admission_audit_wall_sec": round(admission_audit_wall, 9),
        "admission_selector_wall_sec": round(
            diversity_selector_wall, 9
        ),
        "admission_unattributed_wall_sec": round(
            admission_unattributed_wall, 9
        ),
        "post_native_fixed_pipeline_wall_sec": (
            round(post_native_fixed_pipeline_wall, 9)
            if post_native_fixed_pipeline_wall is not None
            else None
        ),
        "post_native_fixed_pipeline_ratio": (
            post_native_fixed_pipeline_wall / admission_milestone_wall
            if post_native_fixed_pipeline_wall is not None
            and admission_milestone_wall > 0.0
            else None
        ),
        "raw_to_native_harvest_wall_sec": (
            round(raw_to_native_harvest_wall, 9)
            if raw_to_native_harvest_wall is not None
            else None
        ),
        "raw_to_native_harvest_ratio": (
            raw_to_native_harvest_wall / admission_milestone_wall
            if raw_to_native_harvest_wall is not None
            and admission_milestone_wall > 0.0
            else None
        ),
        "total_fresh_process_wall_sec": round(wall, 9),
        "first_true_negative_wall_sec": telemetry.get(
            "first_true_negative_wall_time_seconds"
        ),
        "first_audited_negative_wall_sec": telemetry.get(
            "first_audited_true_negative_wall_time_seconds"
        ),
        "first_addable_negative_wall_sec": diversity_audit.get(
            "first_selected_master_ready_native_discovery_wall_sec"
        ),
        "admission_batch_last_selected_native_discovery_wall_sec": (
            diversity_audit.get(
                "selected_master_ready_batch_native_discovery_wall_sec"
            )
        ),
        "proof_completion_wall_sec": telemetry.get(
            "proof_completion_wall_time_seconds"
        ),
        "proof_telemetry": telemetry,
        "temporal_runtime_telemetry": temporal_runtime_telemetry,
        "route_audit": list(telemetry.get("reconstruction_audit") or ()),
        "native_build_info": dict(telemetry.get("native_build_info") or {}),
    }
    target = _resolve(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "policy": args.policy,
        "wall_sec": output["total_fresh_process_wall_sec"],
        "status": result.engine_status,
        "processed_labels": telemetry.get("processed_labels"),
        "output": str(target),
    }, sort_keys=True))
    return 0


def _diversity_milestone_audit(*, result, request, admission_target: int):
    if not bool(request.exact_negative_escape_enabled):
        return {
            "selected_diverse_negative_count": 0,
            "reason": "negative_escape_disabled",
        }
    from lunar_ice_bpc.exact.bpc.pricing.labeling_pricer import (
        _audit_columns_with_true_dual,
    )

    audit = _audit_columns_with_true_dual(
        result.columns,
        request.true_duals,
        branch_context=request.branch_context,
        cut_context=request.cut_context,
        task_set_sources={},
        candidate_search_duals=request.true_duals,
        existing_task_sets=request.proof_tail_active_task_sets or tuple(),
        support_task_sets=tuple(),
        negative_eps=request.negative_eps,
        harvest_target=max(1, int(admission_target)),
        support_aware_harvest_enabled=True,
        support_overlap_threshold=0.6,
        max_selected_jaccard=0.5,
        max_selected_containment=0.8,
        weak_replacement_cap=8,
        strong_replacement_threshold=-1.0e-4,
        unique_task_sets_only=True,
        candidate_order_limit=max(1, int(admission_target)),
    )
    selected = tuple(audit.pop("_selected_internal", tuple()))
    audit.pop("_ordered_negative_internal", None)
    reconstruction_rows = tuple(
        dict(row)
        for row in (result.telemetry or {}).get("reconstruction_audit") or ()
        if bool(row.get("accepted"))
        and row.get("python_manual_rc") is not None
        and float(row["python_manual_rc"]) < -abs(float(request.negative_eps))
    )
    route_mapping_complete = bool(
        len(reconstruction_rows) == len(result.columns)
        and all(row.get("native_route_index") is not None for row in reconstruction_rows)
    )
    backend_index_by_identity = {
        id(column): index for index, column in enumerate(result.columns)
    }
    active_signature_hashes = (
        None
        if request.proof_tail_active_column_signature_hashes is None
        else set(request.proof_tail_active_column_signature_hashes)
    )
    negative_witness_rows = {
        int(row["solution_index"]): dict(row)
        for row in (result.telemetry or {}).get(
            "proof_queue_negative_witness_trace"
        ) or ()
        if row.get("solution_index") is not None
    }
    label_trace_ids = {
        int(row["label_id"])
        for row in (result.telemetry or {}).get(
            "proof_queue_label_state_trace"
        ) or ()
        if row.get("label_id") is not None
    }
    master_entry_audit_started = perf_counter()
    selected_witnesses = []
    for selected_rank, row in enumerate(selected, start=1):
        backend_index = backend_index_by_identity.get(id(row["column"]))
        reconstruction = (
            reconstruction_rows[backend_index]
            if route_mapping_complete
            and backend_index is not None
            and 0 <= backend_index < len(reconstruction_rows)
            else {}
        )
        native_solution_index = reconstruction.get("native_route_index")
        witness = (
            negative_witness_rows.get(int(native_solution_index), {})
            if native_solution_index is not None
            else {}
        )
        ancestor_label_ids = tuple(
            int(value)
            for value in witness.get("ancestor_label_ids") or ()
        )
        signature_hash = column_semantic_signature_hash(row["signature"])
        master_ready = (
            None
            if active_signature_hashes is None
            else signature_hash not in active_signature_hashes
        )
        selected_witnesses.append({
            "selected_rank": int(selected_rank),
            "backend_column_index": backend_index,
            "native_solution_index": native_solution_index,
            "selector_signature_hash": signature_hash,
            "backend_column_signature_hash": reconstruction.get(
                "column_signature"
            ),
            "task_set": list(row["task_set"]),
            "true_reduced_cost": round(
                float(row["true_reduced_cost"]), 9
            ),
            "task_set_harvest_bucket": str(
                row.get("task_set_harvest_bucket") or ""
            ),
            "would_enter_master": master_ready,
            "master_entry_reason": (
                "active_semantic_signature_duplicate"
                if master_ready is False
                else "not_active_in_current_master"
                if master_ready is True
                else "active_signature_context_unavailable"
            ),
            "negative_witness_trace_present": bool(
                native_solution_index is not None
                and int(native_solution_index) in negative_witness_rows
            ),
            "native_discovery_wall_sec": witness.get(
                "elapsed_seconds"
            ),
            "ancestor_label_count": len(ancestor_label_ids),
            "ancestor_label_trace_complete": bool(
                ancestor_label_ids
                and all(
                    label_id in label_trace_ids
                    for label_id in ancestor_label_ids
                )
            ),
        })
    route_mapping_complete = bool(
        route_mapping_complete
        and len(selected_witnesses) == len(selected)
        and all(
            row["backend_column_index"] is not None
            and row["native_solution_index"] is not None
            for row in selected_witnesses
        )
    )
    witness_mapping_complete = bool(
        route_mapping_complete
        and bool((result.telemetry or {}).get("proof_queue_label_trace_enabled"))
        and all(
            row["negative_witness_trace_present"]
            and row["ancestor_label_trace_complete"]
            for row in selected_witnesses
        )
    )
    master_entry_audit_available = active_signature_hashes is not None
    master_entry_audit_wall = perf_counter() - master_entry_audit_started
    selected_native_indices = tuple(
        int(row["native_solution_index"])
        for row in selected_witnesses
        if row["native_solution_index"] is not None
    )
    master_ready_native_indices = tuple(
        int(row["native_solution_index"])
        for row in selected_witnesses
        if row["native_solution_index"] is not None
        and row["would_enter_master"] is True
    )
    master_rejected_native_indices = tuple(
        int(row["native_solution_index"])
        for row in selected_witnesses
        if row["native_solution_index"] is not None
        and row["would_enter_master"] is False
    )
    master_ready_discovery_walls = tuple(
        float(row["native_discovery_wall_sec"])
        for row in selected_witnesses
        if row["would_enter_master"] is True
        and row.get("native_discovery_wall_sec") is not None
    )
    return {
        **audit,
        "selected_diverse_negative_count": len(selected),
        "selected_route_mapping_complete": route_mapping_complete,
        "selected_witness_mapping_complete": witness_mapping_complete,
        "selected_native_solution_indices": list(selected_native_indices),
        "selected_admission_witnesses": selected_witnesses,
        "selected_master_entry_audit_available": (
            master_entry_audit_available
        ),
        "selected_master_entry_audit_wall_time_sec": round(
            master_entry_audit_wall, 9
        ),
        "selected_master_ready_negative_count": (
            len(master_ready_native_indices)
            if master_entry_audit_available
            else None
        ),
        "selected_master_ready_native_solution_indices": list(
            master_ready_native_indices
        ),
        "first_selected_master_ready_native_discovery_wall_sec": (
            min(master_ready_discovery_walls)
            if master_ready_discovery_walls
            else None
        ),
        "selected_master_ready_batch_native_discovery_wall_sec": (
            max(master_ready_discovery_walls)
            if len(master_ready_discovery_walls) >= admission_target
            else None
        ),
        "selected_master_rejected_native_solution_indices": list(
            master_rejected_native_indices
        ),
        "label_supervision_target_scope": (
            "master_admission"
            if master_entry_audit_available
            else "selector_selected_only"
        ),
        "selector_policy_id": "p0v4_diverse_selector_v1",
        "admission_target": int(admission_target),
    }


def _guidance(
    *, data, snapshot: dict, path: Path | None,
    random_seed: int | None, policy: str = "QG2",
):
    legal_arcs = tuple(
        canonical_arc_candidate_id(source, target, path_type)
        for (source, target), by_type in sorted(data.arcs.items())
        for path_type in sorted(by_type)
    )
    if path is None:
        rng = random.Random(int(random_seed))
        payload = {
            "schema_version": POTENTIAL_SCHEMA,
            "source_kind": "fixed_hash_random_qg2",
            "supervision_schema_version": QG2_SUPERVISION_SCHEMA_V2,
            "queue_action_surface": QG2_QUEUE_ACTION_SURFACE_V1,
            "instance_content_hash": data.instance_content_hash,
            "source_state_hash": snapshot["state_hash"],
            "source_engine_hash": snapshot["engine_hash"],
            "source_config_hash": snapshot["config_hash"],
            "source_exact_action_policy_hash": snapshot[
                "exact_action_policy_hash"
            ],
            "task_potentials": {task_id: rng.uniform(-1.0, 1.0) for task_id in data.task_ids},
            "arc_potentials": {arc_id: rng.uniform(-1.0, 1.0) for arc_id in legal_arcs},
            "label_state_coefficients": [rng.uniform(-1.0, 1.0) for _ in range(15)],
            "random_seed": int(random_seed),
        }
        payload["potential_id"] = _hash(payload)
    else:
        payload = _load(path)
    expected_schema = (
        QGR1_POTENTIAL_SCHEMA if policy == "QGR1" else POTENTIAL_SCHEMA
    )
    if payload.get("schema_version") != expected_schema:
        raise SystemExit(f"{policy} potential schema mismatch")
    if policy == "QGR1":
        valid_contract = bool(
            payload.get("supervision_schema_version")
            == QGR1_SUPERVISION_SCHEMA_V1
            and payload.get("queue_action_surface")
            == QGR1_ACTION_SURFACE_V1
            and not bool(payload.get("activation_authority"))
        )
    else:
        valid_contract = bool(
            payload.get("supervision_schema_version")
            in {QG2_SUPERVISION_SCHEMA_V2, QG2_V3_SUPERVISION_SCHEMA}
            and payload.get("queue_action_surface")
            == QG2_QUEUE_ACTION_SURFACE_V1
        )
    if not valid_contract:
        raise SystemExit(f"{policy} potential action-surface contract mismatch")
    if payload.get("instance_content_hash") != data.instance_content_hash:
        raise SystemExit("QG2 potential instance mismatch")
    if payload.get("source_state_hash") != snapshot.get("state_hash"):
        raise SystemExit("QG2 potential snapshot mismatch")
    for key in (
        "source_engine_hash",
        "source_config_hash",
        "source_exact_action_policy_hash",
    ):
        if str(payload.get(key) or "") != str(snapshot.get(
            key.removeprefix("source_")
            if key != "source_exact_action_policy_hash"
            else "exact_action_policy_hash"
        ) or ""):
            raise SystemExit(f"QG2 potential {key} mismatch")
    task = {str(key): float(value) for key, value in dict(payload.get("task_potentials") or {}).items()}
    arc = {str(key): float(value) for key, value in dict(payload.get("arc_potentials") or {}).items()}
    coefficients = tuple(float(value) for value in payload.get("label_state_coefficients") or ())
    if set(task) != set(data.task_ids) or set(arc) != set(legal_arcs):
        raise SystemExit("QG2 potential legal universe mismatch")
    if len(coefficients) != 15:
        raise SystemExit("QG2 potential must contain 15 state coefficients")
    if any(not isfinite(value) for value in (*task.values(), *arc.values(), *coefficients)):
        raise SystemExit("QG2 potential contains NaN/Inf")
    return task, arc, coefficients, payload


def _validate_snapshot(
    data,
    snapshot: dict,
    *,
    source_backend_id: str,
) -> None:
    if snapshot.get("schema_version") not in SNAPSHOT_SCHEMAS:
        raise SystemExit("P0V5 snapshot schema mismatch")
    if not bool(snapshot.get("development_only")) or bool(snapshot.get("deployable")):
        raise SystemExit("snapshot must be development-only")
    if snapshot.get("instance_content_hash") != data.instance_content_hash:
        raise SystemExit("snapshot instance hash mismatch")
    expected_engine_hash = spprc_engine_build_hash(
        source_backend_id
    )
    if str(snapshot.get("engine_hash") or "") != expected_engine_hash:
        raise SystemExit("snapshot source engine hash mismatch")
    if snapshot.get("schema_version") == (
        "lunar_ice_bpc.p0v5_proof_tail_fallback_snapshot.v2"
    ) and str(
        snapshot.get("trajectory_feature_semantics_version") or ""
    ) != TRAJECTORY_FEATURE_SEMANTICS:
        raise SystemExit("snapshot trajectory feature semantics mismatch")
    recorded = str(snapshot.get("state_hash") or "")
    payload = dict(snapshot)
    payload.pop("state_hash", None)
    if recorded != _hash(payload):
        raise SystemExit("snapshot state hash mismatch")


def _frontier_preaction_context(snapshot: dict, trajectory: dict) -> tuple[float, ...]:
    """Return the six pre-action fields that Native cannot reconstruct.

    Native overwrites the other context positions from the first 4096 literal-Q0
    pops.  Presence bits are explicit so a missing value cannot be confused with
    a measured zero.
    """

    values = [0.0] * 28
    active_columns = snapshot.get("active_column_count")
    if active_columns is not None:
        values[15] = log1p(max(0, int(active_columns)))
        values[16] = 1.0
    round_index = snapshot.get("round")
    if round_index is not None:
        values[17] = log1p(max(0, int(round_index)))
        values[18] = 1.0
    dual_delta = trajectory.get("dual_l1_delta_from_previous")
    if dual_delta is not None:
        values[19] = max(0.0, float(dual_delta))
        values[20] = 1.0
    midpoint_wall = (
        snapshot.get("bidirectional_midpoint_prepass_wall_sec")
        if snapshot.get("bidirectional_midpoint_prepass_wall_sec") is not None
        else trajectory.get("v5_midpoint_wall_sec")
    )
    if midpoint_wall is not None:
        values[24] = log1p(max(0.0, float(midpoint_wall)))
        values[25] = 1.0
    return tuple(values)


def _optional_int(value):
    return None if value is None else max(0, int(value))


def _optional_float(value):
    return None if value is None else max(0.0, float(value))


def _active_task_sets(value):
    if value is None:
        return None
    return tuple(tuple(str(task_id) for task_id in row) for row in value)


def _resolve(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _hash(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

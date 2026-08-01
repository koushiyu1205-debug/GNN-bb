#!/usr/bin/env python3
"""Replay one frozen mathematical pricing context with a selected backend.

This is a diagnostic runner.  It binds a fresh request to the snapshot's true
dual, branch context, and full cut context, but no result can certify another
run or mutate the production policy.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import perf_counter

from lunar_ice_bpc.exact.bpc.guidance.replay import load_pricing_snapshot
from lunar_ice_bpc.exact.bpc.pricing.backends import (
    NATIVE_BIDIRECTIONAL_MIDPOINT_HYBRID_BACKEND_ID,
    NATIVE_BIDIRECTIONAL_MIDPOINT_PARTIAL_HYBRID_BACKEND_ID,
    NATIVE_BIDIRECTIONAL_ROOT_PARTIAL_HYBRID_BACKEND_ID,
    NATIVE_HOST_BACKEND_ID,
    PRICING_LIFECYCLE_SCOPES,
    PRICING_LIFECYCLE_SCOPE_UNSPECIFIED,
    BackendPricingRequest,
    BackendRegistry,
    NativeRcsppHostBackend,
)
from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (
    spprc_engine_build_hash,
)
from lunar_ice_bpc.exact.core.branching import (
    branch_context_from_payload,
)
from lunar_ice_bpc.exact.core.cuts import (
    cut_context_from_payload,
    stable_payload_hash,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals


SCHEMA = "lunar_ice_bpc.p0v4_bidirectional_snapshot_replay.v2"
BACKENDS = (
    NATIVE_HOST_BACKEND_ID,
    NATIVE_BIDIRECTIONAL_MIDPOINT_HYBRID_BACKEND_ID,
    NATIVE_BIDIRECTIONAL_MIDPOINT_PARTIAL_HYBRID_BACKEND_ID,
    NATIVE_BIDIRECTIONAL_ROOT_PARTIAL_HYBRID_BACKEND_ID,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--backend", choices=BACKENDS, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--wall-time-limit-sec", type=float, default=30.0)
    parser.add_argument("--memory-limit-gb", type=float, default=None)
    parser.add_argument(
        "--pricing-lifecycle-scope",
        choices=tuple(sorted(PRICING_LIFECYCLE_SCOPES)),
        default=PRICING_LIFECYCLE_SCOPE_UNSPECIFIED,
    )
    parser.add_argument(
        "--negative-escape-batch-size",
        type=int,
        choices=(0, 64, 128, 256),
        default=128,
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    snapshot = load_pricing_snapshot(args.snapshot)
    if snapshot.objective_mode != "official":
        raise SystemExit("snapshot replay requires the official objective")
    data = load_lunar_ice_data(
        json.loads(args.instance.read_text(encoding="utf-8"))
    )
    if data.instance_content_hash != snapshot.instance_content_hash:
        raise SystemExit("instance/snapshot content hash mismatch")
    batch_size = int(args.negative_escape_batch_size)
    escape_enabled = batch_size > 0
    engine_hash = spprc_engine_build_hash(args.backend)
    policy = {
        "schema_version": SCHEMA,
        "backend": args.backend,
        "pricing_lifecycle_scope": (
            args.pricing_lifecycle_scope
        ),
        "negative_escape_batch_size": batch_size,
        "wall_time_limit_sec": max(
            0.001, float(args.wall_time_limit_sec)
        ),
    }
    request = BackendPricingRequest(
        data=data,
        true_duals=JourneyDuals(
            cover=dict(snapshot.true_duals.get("cover") or {}),
            fleet_limit=float(
                snapshot.true_duals.get("fleet_limit") or 0.0
            ),
            cuts=dict(snapshot.true_duals.get("cuts") or {}),
        ),
        mode="exact_proof",
        objective_mode="official",
        pricing_lifecycle_scope=args.pricing_lifecycle_scope,
        branch_context=branch_context_from_payload(
            snapshot.branch_context
        ),
        cut_context=cut_context_from_payload(
            snapshot.full_cut_context
        ),
        wall_time_limit_sec=max(
            0.001, float(args.wall_time_limit_sec)
        ),
        memory_limit_gb=float(
            args.memory_limit_gb
            if args.memory_limit_gb is not None
            else snapshot.memory_limit_gb
        ),
        exact_negative_escape_enabled=escape_enabled,
        exact_admission_batch_size=max(1, batch_size),
        exact_raw_negative_pool_size=max(4, 4 * batch_size),
        exact_negative_escape_policy_id=(
            "diverse_raw_4x_then_p0v4_selector_v1"
        ),
        subset_dominance_enabled=True,
        instance_hash=data.instance_content_hash,
        config_hash=stable_payload_hash(policy),
        engine_hash=engine_hash,
        dual_binding_hash=snapshot.binding.mathematical_dual_hash,
        branch_context_hash=snapshot.binding.branch_context_hash,
        cut_context_hash=snapshot.binding.full_cut_context_hash,
        cut_lineage_hash=snapshot.binding.cut_lineage_hash,
        live_cut_policy_hash=snapshot.binding.live_cut_policy_hash,
        rmp_iteration_id=(
            f"{snapshot.binding.rmp_iteration_id}:"
            f"bidirectional-replay:{args.backend}"
        ),
        separator_policy_version=(
            snapshot.binding.separator_policy_version
        ),
    )
    backend = BackendRegistry.create(args.backend)
    started = perf_counter()
    try:
        result = backend.solve(request)
    finally:
        NativeRcsppHostBackend.close()
    elapsed = perf_counter() - started
    telemetry = dict(result.telemetry or {})
    telemetry_keys = (
        "bidirectional_midpoint_hybrid_attempted",
        "bidirectional_midpoint_hybrid_accepted",
        "bidirectional_midpoint_hybrid_fallback_used",
        "bidirectional_midpoint_hybrid_fallback_reason",
        "bidirectional_midpoint_hybrid_policy_id",
        "pricing_lifecycle_scope",
        "bidirectional_midpoint_partial_scope_policy",
        "bidirectional_midpoint_partial_allowed_for_scope",
        "bidirectional_midpoint_partial_witness_accepted",
        "bidirectional_midpoint_raw_status",
        "bidirectional_midpoint_raw_search_exhaustive",
        "bidirectional_midpoint_raw_route_count",
        "bidirectional_midpoint_prepass_wall_sec",
        "negative_escape_triggered",
        "negative_escape_termination_reason",
        "raw_unique_negative_count",
        "host_peak_rss_bytes",
        "host_memory_killed",
        "host_timed_out",
        "wall_time_seconds",
    )
    payload = {
        "schema_version": SCHEMA,
        "instance": str(args.instance.resolve()),
        "snapshot": str(args.snapshot.resolve()),
        "snapshot_hash": snapshot.snapshot_hash,
        "source_binding_hash": snapshot.binding.binding_hash,
        "backend_id": result.backend_id,
        "engine_hash": engine_hash,
        "elapsed_wall_sec": elapsed,
        "engine_status": result.engine_status,
        "search_exhaustive": bool(result.search_exhaustive),
        "frontier_empty": bool(result.frontier_empty),
        "partial_columns_valid": bool(result.partial_columns_valid),
        "column_count": len(result.columns),
        "best_found_rc": result.best_found_rc,
        "can_enter_certificate_audit": bool(
            result.can_enter_certificate_audit
        ),
        "certificate_blockers": list(result.certificate_blockers),
        "telemetry": {
            key: telemetry.get(key)
            for key in telemetry_keys
            if key in telemetry
        },
        "mutates_production_policy": False,
        "can_certify_another_run": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(str(args.output.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Replay one frozen exact-proof context under a deterministic proof policy.

Each invocation runs one arm in a fresh process.  The output is diagnostic:
only matching exhaustive results may be compared, and this script never
changes the production/default policy or emits a certificate for another run.
"""

from __future__ import annotations

import argparse
import json
from math import sqrt
from pathlib import Path
import re
from time import perf_counter

from lunar_ice_bpc.exact.bpc.guidance.replay import load_pricing_snapshot
from lunar_ice_bpc.exact.bpc.pricing.backends import (
    BackendPricingRequest,
    NativeRcsppHostBackend,
)
from lunar_ice_bpc.exact.bpc.guidance.contracts import CanonicalSolveBindingV2
from lunar_ice_bpc.exact.core.branching import branch_context_from_payload
from lunar_ice_bpc.exact.core.cuts import (
    cut_context_from_payload,
    stable_payload_hash,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals


SCHEMA = "lunar_ice_bpc.proof_tail_snapshot_replay.v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--source-role",
        choices=("exact_control", "mathematical_context"),
        default="exact_control",
        help=(
            "exact_control requires a complete exact source result; "
            "mathematical_context reuses only its bound dual/branch/cut "
            "context and establishes a new exact control."
        ),
    )
    parser.add_argument(
        "--completion-bound",
        choices=("off", "on"),
        required=True,
    )
    parser.add_argument(
        "--subset-dominance",
        choices=("off", "on"),
        required=True,
    )
    parser.add_argument(
        "--proof-queue-policy",
        choices=("Q0", "QC0", "QD1", "QB1"),
        default="Q0",
    )
    parser.add_argument("--wall-time-limit-sec", type=float, default=120.0)
    parser.add_argument("--negative-eps", type=float, default=1.0e-6)
    parser.add_argument("--dominance-eps", type=float, default=1.0e-12)
    parser.add_argument("--resource-eps", type=float, default=1.0e-9)
    args = parser.parse_args()

    snapshot = load_pricing_snapshot(args.snapshot)
    exact_control_source = args.source_role == "exact_control"
    if exact_control_source and snapshot.pricing_mode != "exact_proof":
        raise SystemExit("proof-tail replay requires an exact-proof snapshot")
    if snapshot.objective_mode != "official":
        raise SystemExit("proof-tail replay currently requires official mode")
    if exact_control_source and snapshot.censored:
        raise SystemExit(
            "proof-tail policy differential requires a complete P0 control"
        )
    if exact_control_source and (
        not bool(snapshot.result_summary.get("search_exhaustive"))
        or not bool(snapshot.result_summary.get("frontier_empty"))
    ):
        raise SystemExit("proof-tail P0 control is not exhaustive")
    data = load_lunar_ice_data(
        json.loads(Path(args.instance).read_text(encoding="utf-8"))
    )
    if data.instance_content_hash != snapshot.instance_content_hash:
        raise SystemExit("instance/snapshot content hash mismatch")
    cut_context = cut_context_from_payload(snapshot.full_cut_context)
    completion_bound = args.completion_bound == "on"
    if completion_bound and not cut_context.empty:
        raise SystemExit(
            "completion-bound proof differential is disabled with live cuts"
        )
    subset_dominance = args.subset_dominance == "on"
    policy_id = (
        f"queue_{args.proof_queue_policy}."
        f"completion_bound_{args.completion_bound}."
        f"subset_dominance_{args.subset_dominance}"
    )
    config_hash = stable_payload_hash(
        {
            "schema_version": (
                "lunar_ice_bpc.proof_tail_replay_policy.v1"
            ),
            "source_config_hash": snapshot.binding.config_hash,
            "policy_id": policy_id,
            "negative_eps": abs(float(args.negative_eps)),
            "dominance_eps": abs(float(args.dominance_eps)),
            "resource_eps": abs(float(args.resource_eps)),
        }
    )
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
        branch_context=branch_context_from_payload(snapshot.branch_context),
        cut_context=cut_context,
        wall_time_limit_sec=max(0.001, float(args.wall_time_limit_sec)),
        memory_limit_gb=float(snapshot.memory_limit_gb),
        negative_eps=abs(float(args.negative_eps)),
        dominance_eps=abs(float(args.dominance_eps)),
        resource_eps=abs(float(args.resource_eps)),
        completion_bound_enabled=completion_bound,
        subset_dominance_enabled=subset_dominance,
        proof_queue_policy_id=args.proof_queue_policy,
        instance_hash=data.instance_content_hash,
        config_hash=config_hash,
        engine_hash=snapshot.binding.engine_hash,
        dual_binding_hash=snapshot.binding.mathematical_dual_hash,
        branch_context_hash=snapshot.binding.branch_context_hash,
        cut_context_hash=snapshot.binding.full_cut_context_hash,
        cut_lineage_hash=snapshot.binding.cut_lineage_hash,
        live_cut_policy_hash=snapshot.binding.live_cut_policy_hash,
        rmp_iteration_id=(
            f"{snapshot.binding.rmp_iteration_id}:proof-replay:{policy_id}"
        ),
        separator_policy_version=(
            snapshot.binding.separator_policy_version
        ),
    )
    replay_binding = CanonicalSolveBindingV2.from_backend_request(request)
    pre_call_features = _pre_call_features(
        snapshot=snapshot,
        data=data,
        completion_bound=completion_bound,
        subset_dominance=subset_dominance,
        wall_time_limit_sec=max(
            0.001, float(args.wall_time_limit_sec)
        ),
    )
    backend = NativeRcsppHostBackend()
    started = perf_counter()
    try:
        result = backend.solve(request)
    finally:
        backend.close()
    total_wall = perf_counter() - started
    telemetry = dict(result.telemetry or {})
    payload = {
        "schema_version": SCHEMA,
        "source_snapshot": str(Path(args.snapshot).resolve()),
        "source_snapshot_hash": snapshot.snapshot_hash,
        "source_binding_hash": snapshot.binding.binding_hash,
        "source_role": args.source_role,
        "source_pricing_mode": snapshot.pricing_mode,
        "pre_call_features": pre_call_features,
        "replay_binding": replay_binding.to_payload(),
        "instance_content_hash": data.instance_content_hash,
        "scale": data.scale,
        "policy_id": policy_id,
        "proof_queue_policy_id": args.proof_queue_policy,
        "completion_bound_enabled": completion_bound,
        "subset_dominance_enabled": subset_dominance,
        "negative_eps": abs(float(args.negative_eps)),
        "dominance_eps": abs(float(args.dominance_eps)),
        "resource_eps": abs(float(args.resource_eps)),
        "wall_time_limit_sec": max(
            0.001, float(args.wall_time_limit_sec)
        ),
        "memory_limit_gb": float(snapshot.memory_limit_gb),
        "fresh_process_arm": True,
        "engine_status": result.engine_status,
        "search_exhaustive": bool(result.search_exhaustive),
        "frontier_empty": bool(result.frontier_empty),
        "labels_dropped": bool(result.labels_dropped),
        "best_found_rc": result.best_found_rc,
        "global_min_rc": result.global_min_rc,
        "global_min_rc_is_exact": bool(result.global_min_rc_is_exact),
        "proved_no_rc_below": result.proved_no_rc_below,
        "certificate_blockers": list(result.certificate_blockers),
        "can_enter_certificate_audit": bool(
            result.can_enter_certificate_audit
        ),
        "column_count": len(result.columns),
        "total_fresh_process_wall_sec": total_wall,
        "proof_telemetry": {
            key: telemetry.get(key)
            for key in (
                "extended_labels",
                "dominated_labels",
                "dominance_candidate_checks",
                "max_visited_bucket_size",
                "solution_count",
                "completion_bound_evaluated_labels",
                "completion_bound_pruned_labels",
                "subset_dominance_rejected_labels",
                "subset_dominance_candidate_checks",
                "subset_dominance_key_lookups",
                "subset_dominance_nonempty_buckets",
                "subset_dominance_summary_skipped_buckets",
                "extension_wall_time_seconds",
                "dominance_wall_time_seconds",
                "wall_time_seconds",
                "native_engine_build_hash",
                "proof_queue_policy_id",
                "memory_pressure_triggered",
                "host_timed_out",
                "host_memory_killed",
            )
        },
        "same_mathematical_request_as_source": {
            "instance": (
                replay_binding.instance_hash
                == snapshot.binding.instance_hash
            ),
            "objective_mode": (
                replay_binding.objective_mode
                == snapshot.binding.objective_mode
            ),
            "mathematical_dual": (
                replay_binding.mathematical_dual_hash
                == snapshot.binding.mathematical_dual_hash
            ),
            "branch_context": (
                replay_binding.branch_context_hash
                == snapshot.binding.branch_context_hash
            ),
            "full_cut_context": (
                replay_binding.full_cut_context_hash
                == snapshot.binding.full_cut_context_hash
            ),
        },
        "mutates_production_policy": False,
        "can_certify_another_run": False,
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(str(target.resolve()))
    return 0


def _pre_call_features(
    *,
    snapshot,
    data,
    completion_bound: bool,
    subset_dominance: bool,
    wall_time_limit_sec: float,
) -> dict:
    """Return cheap context features available before the exact call."""

    cover = tuple(
        float(value)
        for _, value in sorted(
            (snapshot.true_duals.get("cover") or {}).items()
        )
    )
    count = len(cover)
    mean_value = sum(cover) / float(max(1, count))
    variance = (
        sum((value - mean_value) ** 2 for value in cover)
        / float(max(1, count))
    )
    iteration_text = str(snapshot.binding.rmp_iteration_id)
    match = re.search(r"-(\d+)$", iteration_text)
    return {
        "feature_schema_version": (
            "lunar_ice_bpc.proof_tail_pre_call_features.v1"
        ),
        "scale": int(data.scale),
        "task_count": len(data.task_ids),
        "source_pricing_mode_exact": int(
            snapshot.pricing_mode == "exact_proof"
        ),
        "rmp_iteration_ordinal": (
            int(match.group(1)) if match is not None else -1
        ),
        "branch_pair_decision_count": len(
            tuple(
                snapshot.branch_context.get("pair_decisions") or ()
            )
        ),
        "full_cut_count": len(
            tuple(snapshot.full_cut_context.get("cuts") or ())
        ),
        "projected_pricing_cut_count": len(
            tuple(
                snapshot.projected_pricing_cut_context.get("cuts")
                or ()
            )
        ),
        "cover_dual_mean": mean_value,
        "cover_dual_std": sqrt(max(0.0, variance)),
        "cover_dual_min": min(cover, default=0.0),
        "cover_dual_max": max(cover, default=0.0),
        "cover_dual_l1": sum(abs(value) for value in cover),
        "cover_positive_fraction": (
            sum(value > 0.0 for value in cover)
            / float(max(1, count))
        ),
        "fleet_dual": float(
            snapshot.true_duals.get("fleet_limit") or 0.0
        ),
        "completion_bound_enabled": int(completion_bound),
        "subset_dominance_enabled": int(subset_dominance),
        "wall_time_limit_sec": float(wall_time_limit_sec),
        "memory_limit_gb": float(snapshot.memory_limit_gb),
    }


if __name__ == "__main__":
    raise SystemExit(main())

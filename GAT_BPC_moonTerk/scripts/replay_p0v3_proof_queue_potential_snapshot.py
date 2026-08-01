#!/usr/bin/env python3
"""Replay one frozen P0 V3 proof call under QC0, QD1, or QG1.

QG1 is an exact-safe ordering diagnostic.  It installs one finite task/arc
potential vector before Native search and then uses the accumulated path
potential as the queue key after terminal eligibility.  It never filters,
prunes, changes reduced cost, or contributes to a certificate.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from math import isfinite
from pathlib import Path
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.bpc.guidance.contracts import (  # noqa: E402
    CanonicalSolveBindingV2,
    GUIDANCE_MODE_TASK_ARC,
    PricingOrderingHintsV2,
    canonical_arc_candidate_id,
)
from lunar_ice_bpc.exact.bpc.pricing.backends import (  # noqa: E402
    BackendPricingRequest,
    NativeRcsppInprocessBackend,
)
from lunar_ice_bpc.exact.core.branching import (  # noqa: E402
    branch_context_from_payload,
)
from lunar_ice_bpc.exact.core.cuts import (  # noqa: E402
    cut_context_from_payload,
    stable_payload_hash,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals  # noqa: E402


SNAPSHOT_SCHEMA = "lunar_ice_bpc.p0v3_root_policy_state_snapshot.v1"
POTENTIAL_SCHEMA = "lunar_ice_bpc.p0v3_proof_queue_potential.v1"
OUTPUT_SCHEMA = "lunar_ice_bpc.p0v3_proof_queue_potential_replay.v1"
POLICIES = ("Q0", "QC0", "QD1", "QG1")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_json(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _validate_snapshot(data, snapshot: dict) -> None:
    if snapshot.get("schema_version") != SNAPSHOT_SCHEMA:
        raise SystemExit("root policy snapshot schema mismatch")
    if (
        not bool(snapshot.get("development_only"))
        or bool(snapshot.get("deployable"))
        or bool(snapshot.get("can_certify"))
    ):
        raise SystemExit("snapshot must be frozen development-only context")
    if snapshot.get("instance_content_hash") != data.instance_content_hash:
        raise SystemExit("instance/snapshot content hash mismatch")
    if snapshot.get("service_timing_policy_id") != data.service_timing_policy_id:
        raise SystemExit("snapshot service-timing policy mismatch")
    recorded_hash = str(snapshot.get("state_hash") or "")
    payload = dict(snapshot)
    payload.pop("state_hash", None)
    if recorded_hash != _sha256_json(payload):
        raise SystemExit("snapshot state hash mismatch")


def _load_potential(
    *,
    path: Path,
    data,
    snapshot: dict,
) -> tuple[dict[str, float], dict[str, float], dict]:
    payload = _load(path)
    if payload.get("schema_version") != POTENTIAL_SCHEMA:
        raise SystemExit("proof queue potential schema mismatch")
    if bool(payload.get("deployable")):
        raise SystemExit("oracle/replay potential cannot be deployable")
    if payload.get("instance_content_hash") != data.instance_content_hash:
        raise SystemExit("potential instance content hash mismatch")
    if payload.get("source_state_hash") != snapshot.get("state_hash"):
        raise SystemExit("potential source state hash mismatch")
    task = {
        str(key): float(value)
        for key, value in dict(payload.get("task_potentials") or {}).items()
    }
    arc = {
        str(key): float(value)
        for key, value in dict(payload.get("arc_potentials") or {}).items()
    }
    if not set(task).issubset(set(data.task_ids)):
        raise SystemExit("task potential universe mismatch")
    legal_arcs = {
        canonical_arc_candidate_id(source, target, path_type)
        for (source, target), by_type in data.arcs.items()
        for path_type in by_type
    }
    if not set(arc).issubset(legal_arcs):
        raise SystemExit("arc potential universe mismatch")
    if any(not isfinite(value) for value in (*task.values(), *arc.values())):
        raise SystemExit("potential contains NaN/Inf")
    task = {task_id: float(task.get(task_id, 0.0)) for task_id in data.task_ids}
    return task, arc, payload


def _result_route_rows(result) -> list[dict]:
    rows = list((result.telemetry or {}).get("reconstruction_audit") or ())
    return [
        {
            "task_set": list(row.get("task_set") or ()),
            "native_rc": row.get("native_rc"),
            "python_manual_rc": row.get("python_manual_rc"),
            "accepted": bool(row.get("accepted")),
            "native_route_sorties": list(
                row.get("native_route_sorties") or ()
            ),
        }
        for row in rows
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--policy", choices=POLICIES, required=True)
    parser.add_argument("--potential")
    parser.add_argument("--repeat-index", type=int, default=1)
    parser.add_argument(
        "--guidance-bucket-width",
        type=float,
        default=0.01,
    )
    parser.add_argument("--wall-time-limit-sec", type=float, default=600.0)
    parser.add_argument("--memory-limit-gb", type=float, default=8.0)
    parser.add_argument("--negative-eps", type=float, default=1.0e-6)
    parser.add_argument("--dominance-eps", type=float, default=1.0e-12)
    parser.add_argument("--resource-eps", type=float, default=1.0e-9)
    args = parser.parse_args()

    instance_path = (ROOT / args.instance).resolve()
    snapshot_path = (ROOT / args.snapshot).resolve()
    output_path = (ROOT / args.output).resolve()
    data = load_lunar_ice_data(_load(instance_path))
    snapshot = _load(snapshot_path)
    _validate_snapshot(data, snapshot)
    if args.policy == "QG1" and not args.potential:
        raise SystemExit("QG1 requires --potential")
    if args.policy != "QG1" and args.potential:
        raise SystemExit("--potential is accepted only by QG1")

    true_duals = dict(snapshot.get("true_duals") or {})
    request = BackendPricingRequest(
        data=data,
        true_duals=JourneyDuals(
            cover=dict(true_duals.get("task_duals") or {}),
            fleet_limit=float(true_duals.get("fleet_dual") or 0.0),
            cuts=dict(true_duals.get("cut_duals") or {}),
        ),
        mode="exact_proof",
        objective_mode="official",
        branch_context=branch_context_from_payload(
            snapshot.get("branch_context") or {}
        ),
        cut_context=cut_context_from_payload(
            snapshot.get("cut_context") or {}
        ),
        wall_time_limit_sec=max(0.001, float(args.wall_time_limit_sec)),
        memory_limit_gb=max(0.0, float(args.memory_limit_gb)),
        negative_eps=abs(float(args.negative_eps)),
        dominance_eps=abs(float(args.dominance_eps)),
        resource_eps=abs(float(args.resource_eps)),
        completion_bound_enabled=False,
        subset_dominance_enabled=True,
        proof_queue_policy_id=str(args.policy),
        proof_queue_guidance_bucket_width=float(
            args.guidance_bucket_width
        ),
        instance_hash=data.instance_content_hash,
        config_hash=stable_payload_hash(
            {
                "schema_version": (
                    "lunar_ice_bpc.p0v3_proof_queue_potential_policy.v1"
                ),
                "source_state_hash": str(snapshot["state_hash"]),
                "policy": str(args.policy),
                "proof_queue_guidance_bucket_width": float(
                    args.guidance_bucket_width
                ),
            }
        ),
        rmp_iteration_id=str(snapshot.get("rmp_iteration_id") or ""),
        cut_lineage_hash=stable_payload_hash(
            snapshot.get("cut_lineage") or {}
        ),
        live_cut_policy_hash=str(
            snapshot.get("live_cut_policy_hash") or ""
        ),
        separator_policy_version=str(
            snapshot.get("separator_policy_version") or ""
        ),
    )

    potential_payload: dict = {}
    if args.policy == "QG1":
        task_potentials, arc_potentials, potential_payload = _load_potential(
            path=(ROOT / str(args.potential)).resolve(),
            data=data,
            snapshot=snapshot,
        )
        request = replace(
            request,
            guidance_mode=GUIDANCE_MODE_TASK_ARC,
            guidance_feature_schema_version=str(
                potential_payload.get("feature_schema_version")
                or "p0v3_proof_queue_potential_oracle.v1"
            ),
            guidance_normalization_version=str(
                potential_payload.get("normalization_version")
                or "centered_maxabs.v1"
            ),
            guidance_checkpoint_id=str(
                potential_payload.get("potential_id")
                or _sha256_json(potential_payload)
            ),
            guidance_ood_policy_version=str(
                potential_payload.get("ood_policy_version")
                or "exact_state_hash_only.v1"
            ),
            guidance_lifecycle_telemetry=(
                ("guidance_import_sec", 0.0),
                ("guidance_checkpoint_load_sec", 0.0),
                ("guidance_tensorize_sec", 0.0),
                ("guidance_forward_total_sec", 0.0),
                ("guidance_call_count", 1),
                ("guidance_binding_validation_sec", 0.0),
                ("guidance_native_install_sec", 0.0),
                ("guidance_total_wall_sec", 0.0),
                ("guidance_total_wall_ratio", None),
                ("bypassed_before_import", False),
                ("bypass_reason", ""),
            ),
        )
        binding = CanonicalSolveBindingV2.from_backend_request(request)
        request = replace(
            request,
            guidance_hints=PricingOrderingHintsV2(
                binding_hash=binding.binding_hash,
                task_priorities=tuple(sorted(task_potentials.items())),
                arc_priorities=tuple(sorted(arc_potentials.items())),
                source=str(
                    potential_payload.get("source_kind")
                    or "development_oracle"
                ),
                diagnostic_only=True,
            ),
        )

    replay_binding = CanonicalSolveBindingV2.from_backend_request(request)
    started = perf_counter()
    result = NativeRcsppInprocessBackend().solve(request)
    total_wall_sec = perf_counter() - started
    telemetry = dict(result.telemetry or {})
    output = {
        "schema_version": OUTPUT_SCHEMA,
        "development_only": True,
        "deployable": False,
        "can_certify_source_solve": False,
        "mutates_p0": False,
        "instance_id": data.instance_id,
        "instance_content_hash": data.instance_content_hash,
        "scale": int(data.scale),
        "source_snapshot_path": str(snapshot_path),
        "source_state_hash": str(snapshot["state_hash"]),
        "source_round": int(snapshot["round"]),
        "policy": str(args.policy),
        "potential_path": (
            str((ROOT / str(args.potential)).resolve())
            if args.potential
            else None
        ),
        "potential_id": potential_payload.get("potential_id"),
        "repeat_index": int(args.repeat_index),
        "guidance_bucket_width": float(args.guidance_bucket_width),
        "fresh_process_arm": True,
        "replay_binding": replay_binding.to_payload(),
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
        "total_fresh_process_wall_sec": round(total_wall_sec, 9),
        "route_rows": _result_route_rows(result),
        "proof_telemetry": {
            key: telemetry.get(key)
            for key in (
                "processed_labels",
                "extended_labels",
                "dominated_labels",
                "dominance_candidate_checks",
                "max_visited_bucket_size",
                "solution_count",
                "subset_dominance_rejected_labels",
                "extension_wall_time_seconds",
                "dominance_wall_time_seconds",
                "wall_time_seconds",
                "proof_queue_policy_id",
                "proof_queue_potential_trace_enabled",
                "proof_queue_potential_trace",
                "proof_queue_arc_potential_trace",
                "guidance_effective_mode",
                "guidance_task_arc_enabled",
                "guidance_filter_count",
                "guidance_arc_drop_count",
                "guidance_label_drop_count",
                "guidance_branch_pair_drop_count",
                "legal_action_universe_hash_before_sort",
                "legal_arc_universe_hash_before_sort",
                "request_bindings_match",
                "memory_pressure_triggered",
            )
        },
        "exact_safe_ordering_audit": {
            "passed": bool(
                result.search_exhaustive
                and result.frontier_empty
                and not result.labels_dropped
                and int(telemetry.get("guidance_filter_count") or 0) == 0
                and int(telemetry.get("guidance_arc_drop_count") or 0) == 0
                and int(telemetry.get("guidance_label_drop_count") or 0) == 0
                and int(
                    telemetry.get("guidance_branch_pair_drop_count") or 0
                )
                == 0
                and bool(telemetry.get("request_bindings_match"))
            ),
            "ordering_only": True,
            "guidance_can_filter": False,
            "guidance_can_prune": False,
            "guidance_can_change_reduced_cost": False,
            "guidance_can_certify": False,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(output_path)
    print(str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Replay a persisted BPC tail dual against P0 and the DSSR pricer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import monotonic

from lunar_ice_bpc.exact.bpc.pricing.backends import (
    NATIVE_DSSR_HOST_BACKEND_ID,
    NATIVE_DSSR_INPROCESS_BACKEND_ID,
    NATIVE_DSSR_V2_HOST_BACKEND_ID,
    NATIVE_DSSR_V2_INPROCESS_BACKEND_ID,
    NATIVE_HOST_BACKEND_ID,
    NATIVE_INPROCESS_BACKEND_ID,
    NATIVE_NG_DSSR_V3_HOST_BACKEND_ID,
    NATIVE_NG_DSSR_V3_INPROCESS_BACKEND_ID,
    BackendPricingRequest,
    BackendRegistry,
)
from lunar_ice_bpc.exact.bpc.cuts.cut_audit import (
    cut_aware_column_signature_from_journey,
)
from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (
    spprc_engine_build_hash,
    spprc_instance_hash,
)
from lunar_ice_bpc.exact.core.branching import (
    BranchContext,
    branch_context_from_payload,
)
from lunar_ice_bpc.exact.core.cuts import (
    CutContext,
    cut_context_from_payload,
    stable_payload_hash,
    true_dual_binding_hash,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.core.journey import (
    journey_column_from_solution_payload,
)
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe-json", type=Path, required=True)
    parser.add_argument("--time-limit-sec", type=float, default=3600.0)
    parser.add_argument(
        "--candidate-time-limit-sec",
        type=float,
        default=None,
        help=(
            "Optional candidate-only limit; useful for matched P0 runtime "
            "diagnostics without spending the full candidate budget."
        ),
    )
    parser.add_argument("--memory-limit-gb", type=float, default=8.0)
    parser.add_argument(
        "--execution-mode",
        choices=("auto", "inprocess", "host"),
        default="auto",
        help=(
            "auto preserves the historical scale-based backend choice; "
            "host provides isolated fresh-runtime/RSS measurements"
        ),
    )
    parser.add_argument(
        "--dssr-policy",
        choices=("v1", "v2", "ng-v3"),
        default="v2",
    )
    parser.add_argument("--dssr-negative-batch-target", type=int, default=16)
    parser.add_argument(
        "--dssr-pressure-max-bucket-size",
        type=int,
        default=8192,
    )
    parser.add_argument(
        "--dssr-pressure-max-candidate-checks",
        type=int,
        default=200_000_000,
    )
    parser.add_argument(
        "--ng-dssr-initial-neighborhood-size",
        type=int,
        default=10,
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def _context_payload(probe: dict, name: str) -> dict:
    final_judge = dict(probe.get("final_judge") or {})
    value = final_judge.get(name)
    if isinstance(value, dict):
        return value
    value = probe.get(name)
    return value if isinstance(value, dict) else {}


def _summarize(
    result,
    elapsed: float,
    *,
    active_task_sets: set[frozenset[str]],
    active_signatures: set,
    branch_context: BranchContext,
    cut_context: CutContext,
) -> dict:
    telemetry = dict(result.telemetry or {})
    candidate_task_sets = [
        frozenset(str(task_id) for task_id in column.task_set)
        for column in result.columns
    ]
    candidate_signatures = [
        cut_aware_column_signature_from_journey(
            column,
            cut_context=cut_context,
            branch_context=branch_context,
        )
        for column in result.columns
    ]
    return {
        "backend_id": result.backend_id,
        "elapsed_wall_sec": elapsed,
        "engine_status": result.engine_status,
        "search_exhaustive": result.search_exhaustive,
        "frontier_empty": result.frontier_empty,
        "labels_dropped": result.labels_dropped,
        "partial_columns_valid": result.partial_columns_valid,
        "column_count": len(result.columns),
        "column_task_sets": [
            sorted(str(task_id) for task_id in column.task_set)
            for column in result.columns
        ],
        "active_task_set_novel_column_count": sum(
            task_set not in active_task_sets
            for task_set in candidate_task_sets
        ),
        "active_task_set_duplicate_column_count": sum(
            task_set in active_task_sets
            for task_set in candidate_task_sets
        ),
        "active_semantic_signature_novel_column_count": sum(
            signature not in active_signatures
            for signature in candidate_signatures
        ),
        "active_semantic_signature_duplicate_column_count": sum(
            signature in active_signatures
            for signature in candidate_signatures
        ),
        "best_found_rc": result.best_found_rc,
        "global_min_rc": result.global_min_rc,
        "global_min_rc_is_exact": result.global_min_rc_is_exact,
        "proved_no_rc_below": result.proved_no_rc_below,
        "can_enter_certificate_audit": (
            result.can_enter_certificate_audit
        ),
        "certificate_blockers": list(result.certificate_blockers),
        "telemetry": {
            key: telemetry.get(key)
            for key in (
                "host_peak_rss_bytes",
                "native_memory_limit_bytes",
                "host_memory_watchdog_limit_bytes",
                "host_partial_result_received",
                "host_proof_state_discarded",
                "processed_labels",
                "extended_labels",
                "dominated_labels",
                "max_visited_bucket_size",
                "wall_time_seconds",
                "request_bindings_match",
                "rc_mismatch_count",
                "max_abs_rc_delta",
                "native_raw_best_found_rc",
                "reconstruction_audit",
                "dssr_enabled",
                "dssr_policy_attempted",
                "dssr_boundary_audit_fallback_used",
                "dssr_boundary_attempt",
                "dssr_policy_version",
                "dssr_iteration_count",
                "dssr_refinement_count",
                "dssr_final_critical_task_count",
                "dssr_repeated_witness_count",
                "dssr_elementary_witness_returned",
                "dssr_relaxation_no_negative_certificate",
                "dssr_elementary_batch_count",
                "dssr_raw_solution_count",
                "dssr_pressure_refinement_count",
                "dssr_pressure_split_task_ids",
                "dssr_pressure_abandoned_iteration_count",
                "dssr_max_bucket_size",
                "dssr_dominance_candidate_checks",
                "ng_dssr_enabled",
                "ng_dssr_initial_neighborhood_size",
                "ng_dssr_initial_relation_count",
                "ng_dssr_final_relation_count",
                "ng_dssr_relation_add_count",
                "ng_dssr_forbidden_cycle_count",
                "ng_dssr_full_elementary_fallback_count",
                "dssr_iteration_trace",
            )
        },
    }


def main() -> int:
    args = parse_args()
    probe = json.loads(args.probe_json.read_text(encoding="utf-8"))
    history = list(probe.get("history") or [])
    if not history:
        raise RuntimeError("probe has no persisted pricing history")
    final_round = dict(history[-1])
    dual_context = dict(final_round.get("dual_context") or {})
    instance_path = Path(str(probe["instance_path"]))
    data = load_lunar_ice_data(
        json.loads(instance_path.read_text(encoding="utf-8"))
    )
    duals = JourneyDuals(
        cover={
            str(key): float(value)
            for key, value in dict(
                dual_context.get("task_duals") or {}
            ).items()
        },
        fleet_limit=float(dual_context.get("fleet_dual") or 0.0),
        cuts={
            str(key): float(value)
            for key, value in dict(
                dual_context.get("cut_duals") or {}
            ).items()
        },
    )
    branch_payload = _context_payload(probe, "branch_context")
    cut_payload = _context_payload(probe, "cut_context")
    branch_context = (
        branch_context_from_payload(branch_payload)
        if branch_payload
        else BranchContext()
    )
    cut_context = (
        cut_context_from_payload(cut_payload)
        if cut_payload
        else CutContext()
    )
    active_columns = tuple(
        journey_column_from_solution_payload(data, dict(payload))
        for payload in (probe.get("active_columns") or [])
    )
    active_task_sets = {
        frozenset(str(task_id) for task_id in column.task_set)
        for column in active_columns
    }
    active_signatures = {
        cut_aware_column_signature_from_journey(
            column,
            cut_context=cut_context,
            branch_context=branch_context,
        )
        for column in active_columns
    }
    use_host = (
        args.execution_mode == "host"
        or (
            args.execution_mode == "auto"
            and int(data.scale) > 30
        )
    )
    if not use_host:
        p0_backend_id = NATIVE_INPROCESS_BACKEND_ID
        if args.dssr_policy == "ng-v3":
            dssr_backend_id = NATIVE_NG_DSSR_V3_INPROCESS_BACKEND_ID
        elif args.dssr_policy == "v2":
            dssr_backend_id = NATIVE_DSSR_V2_INPROCESS_BACKEND_ID
        else:
            dssr_backend_id = NATIVE_DSSR_INPROCESS_BACKEND_ID
        execution_mode = "matched_inprocess"
    else:
        p0_backend_id = NATIVE_HOST_BACKEND_ID
        if args.dssr_policy == "ng-v3":
            dssr_backend_id = NATIVE_NG_DSSR_V3_HOST_BACKEND_ID
        elif args.dssr_policy == "v2":
            dssr_backend_id = NATIVE_DSSR_V2_HOST_BACKEND_ID
        else:
            dssr_backend_id = NATIVE_DSSR_HOST_BACKEND_ID
        execution_mode = "matched_host"
    rows = {}
    for backend_id in (
        p0_backend_id,
        dssr_backend_id,
    ):
        backend = BackendRegistry.create(backend_id)
        effective_time_limit_sec = (
            float(args.candidate_time_limit_sec)
            if (
                backend_id == dssr_backend_id
                and args.candidate_time_limit_sec is not None
            )
            else float(args.time_limit_sec)
        )
        request = BackendPricingRequest(
            data=data,
            true_duals=duals,
            branch_context=branch_context,
            cut_context=cut_context,
            wall_time_limit_sec=effective_time_limit_sec,
            memory_limit_gb=float(args.memory_limit_gb),
            dssr_negative_batch_target=max(
                1,
                min(64, int(args.dssr_negative_batch_target)),
            ),
            dssr_pressure_max_bucket_size=max(
                1,
                int(args.dssr_pressure_max_bucket_size),
            ),
            dssr_pressure_max_candidate_checks=max(
                1,
                int(args.dssr_pressure_max_candidate_checks),
            ),
            ng_dssr_initial_neighborhood_size=max(
                1,
                min(
                    int(data.scale),
                    int(args.ng_dssr_initial_neighborhood_size),
                ),
            ),
            instance_hash=spprc_instance_hash(data),
            config_hash=stable_payload_hash(
                {
                    "schema_version": (
                        "lunar_ice_bpc.large_exact_tail_replay.v1"
                    ),
                    "source_probe": str(args.probe_json),
                    "source_dual_fingerprint": str(
                        dual_context.get("dual_fingerprint") or ""
                    ),
                    "rmp_iteration_id": str(
                        dual_context.get("rmp_iteration_id") or ""
                    ),
                    "backend_id": backend_id,
                    "time_limit_sec": float(args.time_limit_sec),
                    "effective_time_limit_sec": (
                        effective_time_limit_sec
                    ),
                    "memory_limit_gb": float(args.memory_limit_gb),
                    "dssr_policy": str(args.dssr_policy),
                    "dssr_negative_batch_target": int(
                        args.dssr_negative_batch_target
                    ),
                    "dssr_pressure_max_bucket_size": int(
                        args.dssr_pressure_max_bucket_size
                    ),
                    "dssr_pressure_max_candidate_checks": int(
                        args.dssr_pressure_max_candidate_checks
                    ),
                    "ng_dssr_initial_neighborhood_size": int(
                        args.ng_dssr_initial_neighborhood_size
                    ),
                }
            ),
            engine_hash=spprc_engine_build_hash(backend_id),
            dual_binding_hash=true_dual_binding_hash(
                duals.cover,
                fleet_limit=duals.fleet_limit,
                cuts=duals.cuts,
            ),
            branch_context_hash=stable_payload_hash(
                branch_context.to_payload()
            ),
            cut_context_hash=cut_context.active_cut_context_hash,
            rmp_iteration_id=str(
                dual_context.get("rmp_iteration_id") or ""
            ),
        )
        started = monotonic()
        try:
            result = backend.solve(request)
        finally:
            close = getattr(type(backend), "close", None)
            if callable(close):
                close()
        rows[backend_id] = _summarize(
            result,
            monotonic() - started,
            active_task_sets=active_task_sets,
            active_signatures=active_signatures,
            branch_context=branch_context,
            cut_context=cut_context,
        )
    p0 = rows[p0_backend_id]
    dssr = rows[dssr_backend_id]
    output = {
        "schema_version": "lunar_ice_bpc.large_exact_tail_replay.v1",
        "source_probe_json": str(args.probe_json),
        "source_probe_instance_id": str(probe.get("instance_id") or ""),
        "source_probe_status": str(
            probe.get("algorithm_status") or ""
        ),
        "source_probe_final_judge_status": str(
            dict(probe.get("final_judge") or {}).get(
                "engine_status"
            )
            or ""
        ),
        "source_probe_final_judge_rss_bytes": dict(
            dict(probe.get("final_judge") or {}).get("telemetry") or {}
        ).get("host_peak_rss_bytes"),
        "instance_path": str(instance_path),
        "instance_id": data.instance_id,
        "scale": int(data.scale),
        "instance_content_hash": data.instance_content_hash,
        "source_history_round": int(final_round.get("round") or 0),
        "source_dual_fingerprint": str(
            dual_context.get("dual_fingerprint") or ""
        ),
        "rmp_iteration_id": str(
            dual_context.get("rmp_iteration_id") or ""
        ),
        "branch_context": branch_context.to_payload(),
        "cut_context": cut_context.to_payload(),
        "time_limit_sec": float(args.time_limit_sec),
        "candidate_time_limit_sec": (
            None
            if args.candidate_time_limit_sec is None
            else float(args.candidate_time_limit_sec)
        ),
        "memory_limit_gb": float(args.memory_limit_gb),
        "execution_mode": execution_mode,
        "p0_backend_id": p0_backend_id,
        "dssr_backend_id": dssr_backend_id,
        "source_active_column_count": len(active_columns),
        "source_active_task_set_count": len(active_task_sets),
        "source_active_semantic_signature_count": len(
            active_signatures
        ),
        "p0": p0,
        "dssr": dssr,
        "audit": {
            "instance_id_matches": bool(
                data.instance_id
                == str(probe.get("instance_id") or "")
            ),
            "both_bindings_match": bool(
                p0["telemetry"]["request_bindings_match"]
                and dssr["telemetry"]["request_bindings_match"]
            ),
            "both_labels_dropped_zero": bool(
                not p0["labels_dropped"]
                and not dssr["labels_dropped"]
            ),
            "dssr_returns_audited_negative_or_exact_certificate": bool(
                (
                    dssr["column_count"] > 0
                    and dssr["partial_columns_valid"]
                    and dssr["best_found_rc"] is not None
                    and dssr["best_found_rc"] < -1.0e-6
                )
                or dssr["can_enter_certificate_audit"]
            ),
            "dssr_returns_active_master_novel_audited_negative": bool(
                dssr["column_count"] > 0
                and dssr["partial_columns_valid"]
                and dssr["best_found_rc"] is not None
                and dssr["best_found_rc"] < -1.0e-6
                and dssr[
                    "active_semantic_signature_novel_column_count"
                ]
                > 0
            ),
            "dssr_progresses_farther_than_p0": bool(
                (
                    dssr["column_count"] > 0
                    or dssr["can_enter_certificate_audit"]
                )
                and not (
                    p0["column_count"] > 0
                    or p0["can_enter_certificate_audit"]
                )
            ),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "p0_status": p0["engine_status"],
                "p0_columns": p0["column_count"],
                "dssr_status": dssr["engine_status"],
                "dssr_columns": dssr["column_count"],
                "dssr_certificate": dssr[
                    "can_enter_certificate_audit"
                ],
                "dssr_refinements": dssr["telemetry"][
                    "dssr_refinement_count"
                ],
                "audit": output["audit"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

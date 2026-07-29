#!/usr/bin/env python3
"""Replay one certified V3 root-final dual under a Native pricing policy arm.

This is a development-only action-headroom diagnostic.  It reuses only the
mathematical dual/context from a certified root source and runs a fresh Native
pricing request.  A replay result cannot certify the source solve or mutate P0.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.bpc.pricing.backends import (  # noqa: E402
    BACKEND_MODE_EXACT_PROOF,
    BACKEND_MODE_NEGATIVE_HARVEST,
    BackendPricingRequest,
    NativeRcsppInprocessBackend,
)
from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (  # noqa: E402
    spprc_engine_build_hash,
)
from lunar_ice_bpc.exact.core.branching import BranchContext  # noqa: E402
from lunar_ice_bpc.exact.core.cuts import (  # noqa: E402
    CutContext,
    stable_payload_hash,
    true_dual_binding_hash,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals  # noqa: E402


SCHEMA = "lunar_ice_bpc.p0v3_root_final_policy_replay.v1"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _certified_root_source(source: dict, *, data) -> dict:
    if source.get("instance_content_hash") != data.instance_content_hash:
        raise SystemExit("root source instance content hash mismatch")
    if source.get("service_timing_policy_id") != data.service_timing_policy_id:
        raise SystemExit("root source service-timing policy mismatch")
    if not bool(source.get("development_only")) or bool(
        source.get("deployable")
    ):
        raise SystemExit("root policy replay accepts development sources only")
    result = dict(source.get("result") or {})
    final_judge = dict(result.get("final_judge") or {})
    if not (
        bool(source.get("root_exact_safe"))
        and result.get("pricing_state") == "CERTIFIED_NO_NEGATIVE"
        and result.get("certificate_scope") == "BPC_NODE_LP_CERTIFIED"
        and bool(result.get("uses_true_dual_bpc_certificate"))
        and bool(final_judge.get("pricing_rc_audit_pass"))
    ):
        raise SystemExit("root source is not an exact-safe certified closure")
    return result


def _history_duals(
    result: dict,
    *,
    history_index: int,
) -> tuple[JourneyDuals, str, int, int]:
    history = list(result.get("history") or ())
    if not history:
        raise SystemExit("root source has no pricing history")
    try:
        row = history[int(history_index)]
    except IndexError as exc:
        raise SystemExit("root history index is out of range") from exc
    context = dict(row.get("dual_context") or {})
    cover = context.get("task_duals")
    if not isinstance(cover, dict) or not cover:
        raise SystemExit("root final dual context is missing task duals")
    return (
        JourneyDuals(
            cover={
                str(task_id): float(value)
                for task_id, value in cover.items()
            },
            fleet_limit=float(context.get("fleet_dual") or 0.0),
            cuts={
                str(cut_id): float(value)
                for cut_id, value in (
                    context.get("cut_duals") or {}
                ).items()
            },
        ),
        str(context.get("rmp_iteration_id") or ""),
        int(history_index),
        int(row.get("round") or 0),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--root-source", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--mode",
        choices=("negative_harvest", "exact_proof"),
        required=True,
    )
    parser.add_argument(
        "--subset-dominance",
        choices=("off", "on"),
        default="off",
    )
    parser.add_argument("--harvest-target", type=int, default=64)
    parser.add_argument(
        "--harvest-max-processed-labels",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--history-index",
        type=int,
        default=-1,
        help=(
            "Python-style index into the certified root pricing history. "
            "The default replays the final no-negative context."
        ),
    )
    parser.add_argument("--wall-time-limit-sec", type=float, default=120.0)
    parser.add_argument("--memory-limit-gb", type=float, default=10.0)
    args = parser.parse_args()

    instance_path = (ROOT / args.instance).resolve()
    source_path = (ROOT / args.root_source).resolve()
    data = load_lunar_ice_data(_load_json(instance_path))
    source = _load_json(source_path)
    result = _certified_root_source(source, data=data)
    (
        duals,
        source_iteration_id,
        source_history_index,
        source_round,
    ) = _history_duals(
        result,
        history_index=int(args.history_index),
    )
    branch_context = BranchContext()
    cut_context = CutContext()
    mode = (
        BACKEND_MODE_EXACT_PROOF
        if args.mode == "exact_proof"
        else BACKEND_MODE_NEGATIVE_HARVEST
    )
    subset_dominance = args.subset_dominance == "on"
    if mode != BACKEND_MODE_EXACT_PROOF and subset_dominance:
        raise SystemExit(
            "subset dominance is an exact-proof arm; harvest must use off"
        )
    if int(args.harvest_max_processed_labels) < 0:
        raise SystemExit(
            "harvest processed-label budget must be nonnegative"
        )
    if (
        mode == BACKEND_MODE_EXACT_PROOF
        and int(args.harvest_max_processed_labels) > 0
    ):
        raise SystemExit(
            "harvest processed-label budget cannot truncate exact proof"
        )
    policy = {
        "schema_version": SCHEMA,
        "source_root_binding_hash": str(
            (source.get("solver_binding") or {}).get("binding_hash") or ""
        ),
        "mode": mode,
        "subset_dominance_enabled": subset_dominance,
        "harvest_target": max(1, int(args.harvest_target)),
        "harvest_max_processed_labels": int(
            args.harvest_max_processed_labels
        ),
    }
    engine_hash = spprc_engine_build_hash("native_rcspp_inprocess")
    request = BackendPricingRequest(
        data=data,
        true_duals=duals,
        mode=mode,
        objective_mode="official",
        branch_context=branch_context,
        cut_context=cut_context,
        harvest_target=max(1, int(args.harvest_target)),
        harvest_max_processed_labels=int(
            args.harvest_max_processed_labels
        ),
        wall_time_limit_sec=max(
            0.001, float(args.wall_time_limit_sec)
        ),
        memory_limit_gb=max(0.0, float(args.memory_limit_gb)),
        completion_bound_enabled=False,
        subset_dominance_enabled=subset_dominance,
        proof_queue_policy_id="Q0",
        instance_hash=data.instance_content_hash,
        config_hash=stable_payload_hash(policy),
        engine_hash=engine_hash,
        dual_binding_hash=true_dual_binding_hash(
            duals.cover,
            fleet_limit=duals.fleet_limit,
            cuts=duals.cuts,
        ),
        branch_context_hash=stable_payload_hash(
            branch_context.to_payload()
        ),
        cut_context_hash=cut_context.active_cut_context_hash,
        rmp_iteration_id=(
            f"{source_iteration_id}:p0v3-root-final-policy-replay"
        ),
    )
    backend = NativeRcsppInprocessBackend()
    started = perf_counter()
    replay = backend.solve(request)
    total_wall = perf_counter() - started
    telemetry = dict(replay.telemetry or {})
    payload = {
        "schema_version": SCHEMA,
        "development_only": True,
        "deployable": False,
        "can_certify_source_solve": False,
        "mutates_p0": False,
        "instance_id": data.instance_id,
        "instance_content_hash": data.instance_content_hash,
        "source_root": str(source_path),
        "source_root_binding_hash": policy[
            "source_root_binding_hash"
        ],
        "source_rmp_iteration_id": source_iteration_id,
        "source_history_index": source_history_index,
        "source_round": source_round,
        "mode": mode,
        "subset_dominance_enabled": subset_dominance,
        "harvest_max_processed_labels": int(
            args.harvest_max_processed_labels
        ),
        "engine_hash": engine_hash,
        "engine_status": replay.engine_status,
        "search_exhaustive": bool(replay.search_exhaustive),
        "frontier_empty": bool(replay.frontier_empty),
        "labels_dropped": bool(replay.labels_dropped),
        "global_min_rc": replay.global_min_rc,
        "global_min_rc_is_exact": bool(
            replay.global_min_rc_is_exact
        ),
        "proved_no_rc_below": replay.proved_no_rc_below,
        "column_count": len(replay.columns),
        "certificate_blockers": list(replay.certificate_blockers),
        "can_enter_certificate_audit": bool(
            replay.can_enter_certificate_audit
        ),
        "total_fresh_process_wall_sec": round(total_wall, 9),
        "telemetry": {
            key: telemetry.get(key)
            for key in (
                "extended_labels",
                "processed_labels",
                "dominated_labels",
                "dominance_candidate_checks",
                "subset_dominance_key_lookups",
                "subset_dominance_candidate_checks",
                "subset_dominance_rejected_labels",
                "extension_wall_time_seconds",
                "dominance_wall_time_seconds",
                "wall_time_seconds",
                "memory_pressure_triggered",
                "proof_queue_policy_id",
            )
        },
    }
    _write_json((ROOT / args.output).resolve(), payload)
    print(
        json.dumps(
            {
                "mode": mode,
                "subset_dominance_enabled": subset_dominance,
                "wall_sec": round(total_wall, 6),
                "search_exhaustive": bool(replay.search_exhaustive),
                "frontier_empty": bool(replay.frontier_empty),
                "labels_dropped": bool(replay.labels_dropped),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Replay one P0V4/V5 true-dual pricing context with a sparse escape.

This is a development-only headroom probe.  It reconstructs a mathematical
root-pricing context from a persisted ``probe.json`` round and runs one fresh
Native process.  Because the historical probe does not persist a complete RMP
basis/cut-lineage state, this script never exports a certificate, even when the
fresh pricing call happens to exhaust its frontier.

The deviation changes only the partial-negative return target for one call:

* ``P0``: use the frozen scale admission target and its 4K raw pool;
* ``S1``: return after one audited raw negative;
* ``S4``: return after four audited raw negatives.

All arms retain the same true dual, legal route universe, dominance, bounds,
branch context (root/empty only here), and Native backend.  A partial arm can
only produce negative columns; it cannot certify no-negative pricing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.bpc.pricing.backends import (  # noqa: E402
    BACKEND_MODE_EXACT_PROOF,
    BACKEND_OBJECTIVE_OFFICIAL,
    PRICING_LIFECYCLE_SCOPE_ROOT_CG,
    BackendPricingRequest,
    BackendRegistry,
)
from lunar_ice_bpc.exact.bpc.pricing.backends.base import (  # noqa: E402
    EXACT_NEGATIVE_ESCAPE_POLICY_V1,
)
from lunar_ice_bpc.exact.core.branching import BranchContext  # noqa: E402
from lunar_ice_bpc.exact.core.cuts import (  # noqa: E402
    CutContext,
    stable_payload_hash,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals  # noqa: E402


SCHEMA = "lunar_ice_bpc.p0v4_sparse_tail_deviation_replay.v1"
ACTION_POLICY_ID = "one_round_sparse_true_dual_escape_v1"
DEFAULT_BACKEND = "native_rcspp_bidirectional_root_partial_hybrid_v3"
ACTION_TARGETS = {
    "S1": (1, 1),
    "S4": (4, 4),
}
OFFICIAL_NEGATIVE_EPS = 1.0e-6
DEFAULT_SPARSE_DISCOVERY_NEGATIVE_EPS = 3.0e-6


def _load_json(path: Path) -> dict:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _round_row(probe: dict, round_index: int) -> dict:
    matches = [
        dict(row)
        for row in probe.get("history", ())
        if int(row.get("round") or -1) == int(round_index)
    ]
    if len(matches) != 1:
        raise ValueError(
            f"probe must contain exactly one round {round_index}; "
            f"found {len(matches)}"
        )
    row = matches[0]
    if str(row.get("node_id") or "root") != "root":
        raise ValueError("sparse-tail replay currently accepts root rounds only")
    if bool(row.get("branch_context_active")):
        raise ValueError(
            "probe round has an active branch context that was not persisted"
        )
    dual_context = dict(row.get("dual_context") or {})
    if not dual_context:
        raise ValueError("probe round is missing its true-dual context")
    if dict(dual_context.get("cut_duals") or {}):
        raise ValueError(
            "probe round has cut duals but lacks the complete cut context"
        )
    if not dict(dual_context.get("task_duals") or {}):
        raise ValueError("probe round has no task duals")
    return row


def _frozen_batch_size(row: dict, *, scale: int) -> int:
    recorded = int(
        row.get("labeling_final_judge_effective_exact_harvest_target")
        or 0
    )
    expected = {30: 64, 50: 128}.get(int(scale))
    if expected is None:
        raise ValueError("sparse-tail headroom replay is limited to scale30/50")
    if recorded and recorded != expected:
        raise ValueError(
            "probe frozen admission target differs from the V5 scale binding"
        )
    return expected


def _action_targets(action: str, *, frozen_batch_size: int) -> tuple[int, int]:
    normalized = str(action).strip().upper()
    if normalized == "P0":
        return int(frozen_batch_size), 4 * int(frozen_batch_size)
    try:
        return ACTION_TARGETS[normalized]
    except KeyError as exc:
        raise ValueError(f"unsupported sparse-tail action {action!r}") from exc


def _context_from_probe(
    *,
    probe_path: Path,
    instance_path: Path,
    round_index: int,
    action: str,
) -> dict:
    probe = _load_json(probe_path)
    row = _round_row(probe, round_index)
    data = load_lunar_ice_data(_load_json(instance_path))
    probe_hash = str(probe.get("instance_id") or "")
    if probe_hash and probe_hash != data.instance_id:
        raise ValueError("probe and instance id differ")
    scale = int(data.scale)
    frozen_batch = _frozen_batch_size(row, scale=scale)
    admission_batch, raw_pool = _action_targets(
        action,
        frozen_batch_size=frozen_batch,
    )
    dual_context = dict(row["dual_context"])
    return {
        "probe": probe,
        "row": row,
        "data": data,
        "scale": scale,
        "frozen_batch_size": frozen_batch,
        "admission_batch_size": admission_batch,
        "raw_negative_pool_size": raw_pool,
        "duals": JourneyDuals(
            cover={
                str(key): float(value)
                for key, value in dict(
                    dual_context.get("task_duals") or {}
                ).items()
            },
            fleet_limit=float(dual_context.get("fleet_dual") or 0.0),
            cuts={},
        ),
        "source_rmp_iteration_id": str(
            dual_context.get("rmp_iteration_id") or ""
        ),
        "source_dual_fingerprint": str(
            dual_context.get("dual_fingerprint") or ""
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", required=True)
    parser.add_argument("--instance", required=True)
    parser.add_argument("--round", type=int, required=True)
    parser.add_argument("--action", choices=("P0", "S1", "S4"), required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--backend-id", default=DEFAULT_BACKEND)
    parser.add_argument("--wall-time-limit-sec", type=float, required=True)
    parser.add_argument("--memory-limit-gb", type=float, default=10.0)
    parser.add_argument(
        "--sparse-discovery-negative-eps",
        type=float,
        default=DEFAULT_SPARSE_DISCOVERY_NEGATIVE_EPS,
        help=(
            "Heuristic-only threshold for S1/S4. It must be at least the "
            "official epsilon; exhaustion at this stricter threshold has no "
            "certificate authority and requires the frozen P0 proof."
        ),
    )
    args = parser.parse_args()

    probe_path = Path(args.probe).resolve()
    instance_path = Path(args.instance).resolve()
    output_path = Path(args.output).resolve()
    context = _context_from_probe(
        probe_path=probe_path,
        instance_path=instance_path,
        round_index=int(args.round),
        action=str(args.action),
    )
    data = context["data"]
    row = context["row"]
    action = str(args.action).upper()
    sparse_discovery_eps = abs(
        float(args.sparse_discovery_negative_eps)
    )
    if sparse_discovery_eps < OFFICIAL_NEGATIVE_EPS:
        raise SystemExit(
            "sparse discovery epsilon cannot be weaker than the official "
            "negative epsilon"
        )
    request_negative_eps = (
        OFFICIAL_NEGATIVE_EPS
        if action == "P0"
        else sparse_discovery_eps
    )
    config_hash = stable_payload_hash(
        {
            "schema_version": SCHEMA,
            "action_policy_id": ACTION_POLICY_ID,
            "source_probe_sha256": _sha256(probe_path),
            "source_round": int(args.round),
            "source_dual_fingerprint": context[
                "source_dual_fingerprint"
            ],
            "action": action,
            "backend_id": str(args.backend_id),
            "admission_batch_size": context["admission_batch_size"],
            "raw_negative_pool_size": context[
                "raw_negative_pool_size"
            ],
            "official_negative_eps": OFFICIAL_NEGATIVE_EPS,
            "request_negative_eps": request_negative_eps,
        }
    )
    request = BackendPricingRequest(
        data=data,
        true_duals=context["duals"],
        mode=BACKEND_MODE_EXACT_PROOF,
        objective_mode=BACKEND_OBJECTIVE_OFFICIAL,
        pricing_lifecycle_scope=PRICING_LIFECYCLE_SCOPE_ROOT_CG,
        branch_context=BranchContext(),
        cut_context=CutContext(),
        wall_time_limit_sec=max(0.001, float(args.wall_time_limit_sec)),
        memory_limit_gb=max(0.0, float(args.memory_limit_gb)),
        exact_negative_escape_enabled=True,
        exact_admission_batch_size=int(
            context["admission_batch_size"]
        ),
        exact_raw_negative_pool_size=int(
            context["raw_negative_pool_size"]
        ),
        exact_negative_escape_policy_id=(
            EXACT_NEGATIVE_ESCAPE_POLICY_V1
        ),
        negative_eps=request_negative_eps,
        subset_dominance_enabled=True,
        cut_state_enabled=True,
        instance_hash=data.instance_content_hash,
        config_hash=config_hash,
        rmp_iteration_id=(
            f"{context['source_rmp_iteration_id']}:"
            f"sparse-tail-replay:{action.lower()}"
        ),
    )
    backend = BackendRegistry.create(str(args.backend_id))
    started = perf_counter()
    try:
        result = backend.solve(request)
    finally:
        close = getattr(backend, "close", None)
        if callable(close):
            close()
    wall = perf_counter() - started
    telemetry = dict(result.telemetry or {})
    negative_escape_triggered = bool(
        telemetry.get("negative_escape_triggered")
    )
    safety_issues = []
    if negative_escape_triggered:
        if bool(result.search_exhaustive):
            safety_issues.append("partial_escape_marked_exhaustive")
        if bool(result.frontier_empty):
            safety_issues.append("partial_escape_marked_frontier_empty")
        if result.can_enter_certificate_audit:
            safety_issues.append("partial_escape_entered_certificate_audit")
        if "native_exact_negative_escape_partial" not in set(
            result.certificate_blockers
        ):
            safety_issues.append("partial_escape_blocker_missing")
        if not bool(result.partial_columns_valid):
            safety_issues.append("partial_escape_columns_not_fully_audited")
        if not result.columns:
            safety_issues.append("partial_escape_has_no_true_negative_column")
        if result.best_found_rc is None:
            safety_issues.append("partial_escape_has_no_audited_best_rc")
        elif float(result.best_found_rc) >= -OFFICIAL_NEGATIVE_EPS:
            safety_issues.append(
                "partial_escape_best_rc_not_officially_negative"
            )
    reconstruction_rows = tuple(
        dict(value)
        for value in telemetry.get("reconstruction_audit", ())
    )
    payload = {
        "schema_version": SCHEMA,
        "status": (
            "SAFE_REPLAY_COMPLETE"
            if not safety_issues
            else "SAFETY_REDLINE"
        ),
        "action_policy_id": ACTION_POLICY_ID,
        "action": action,
        "source_role": "mathematical_context_only",
        "source_probe": str(probe_path),
        "source_probe_sha256": _sha256(probe_path),
        "source_round": int(args.round),
        "source_round_pricing_state": str(
            row.get("pricing_state") or ""
        ),
        "source_round_raw_unique_negative_count": int(
            row.get("raw_unique_negative_count") or 0
        ),
        "source_round_selected_diverse_negative_count": int(
            row.get("selected_diverse_negative_count") or 0
        ),
        "source_round_proof_wall_sec": float(
            row.get("labeling_final_judge_proof_pass_wall_time")
            or 0.0
        ),
        "source_dual_fingerprint": context[
            "source_dual_fingerprint"
        ],
        "instance": str(instance_path),
        "instance_sha256": _sha256(instance_path),
        "instance_content_hash": data.instance_content_hash,
        "scale": int(data.scale),
        "backend_id": str(args.backend_id),
        "config_hash": config_hash,
        "frozen_admission_batch_size": int(
            context["frozen_batch_size"]
        ),
        "action_admission_batch_size": int(
            context["admission_batch_size"]
        ),
        "action_raw_negative_pool_size": int(
            context["raw_negative_pool_size"]
        ),
        "wall_time_limit_sec": max(
            0.001, float(args.wall_time_limit_sec)
        ),
        "memory_limit_gb": max(0.0, float(args.memory_limit_gb)),
        "official_negative_eps": OFFICIAL_NEGATIVE_EPS,
        "request_negative_eps": request_negative_eps,
        "sparse_discovery_threshold_is_heuristic_only": bool(
            action != "P0"
            and request_negative_eps != OFFICIAL_NEGATIVE_EPS
        ),
        "fresh_process_wall_sec": float(wall),
        "engine_status": str(result.engine_status),
        "search_exhaustive": bool(result.search_exhaustive),
        "frontier_empty": bool(result.frontier_empty),
        "labels_dropped": bool(result.labels_dropped),
        "partial_columns_valid": bool(result.partial_columns_valid),
        "column_count": len(result.columns),
        "best_found_rc": result.best_found_rc,
        "global_min_rc": result.global_min_rc,
        "global_min_rc_is_exact": bool(result.global_min_rc_is_exact),
        "certificate_blockers": list(result.certificate_blockers),
        "backend_can_enter_certificate_audit": bool(
            result.can_enter_certificate_audit
        ),
        "negative_escape_triggered": negative_escape_triggered,
        "negative_escape_termination_reason": str(
            telemetry.get("negative_escape_termination_reason") or ""
        ),
        "raw_unique_negative_count": int(
            telemetry.get("raw_unique_negative_count") or len(result.columns)
        ),
        "native_wall_time_sec": float(
            telemetry.get("wall_time_seconds") or 0.0
        ),
        "host_peak_rss_bytes": int(
            telemetry.get("host_peak_rss_bytes") or 0
        ),
        "reconstruction_audit": {
            "row_count": len(reconstruction_rows),
            "accepted_count": sum(
                bool(value.get("accepted"))
                for value in reconstruction_rows
            ),
            "true_negative_column_count": len(result.columns),
            "rows": list(reconstruction_rows[:16]),
        },
        "safety": {
            "issues": safety_issues,
            "legal_candidate_universe_mutated": False,
            "reduced_cost_definition_mutated": False,
            "partial_discovery_threshold_stricter_than_official": bool(
                request_negative_eps > OFFICIAL_NEGATIVE_EPS
            ),
            "dominance_or_bound_mutated": False,
            "pruning_path_mutated": False,
            "certificate_path_mutated": False,
            "replay_certificate_authority": "none",
            "can_certify_from_replay": False,
            "next_round_policy": "restore_frozen_v5",
            "exhaustive_sparse_miss_policy": (
                "run_frozen_v5_official_epsilon_proof"
            ),
        },
        "telemetry": {
            key: telemetry.get(key)
            for key in (
                "native_engine_build_hash",
                "processed_labels",
                "extended_labels",
                "dominated_labels",
                "dominance_candidate_checks",
                "max_visited_bucket_size",
                "solution_count",
                "negative_escape_enabled",
                "negative_escape_triggered",
                "exact_admission_batch_size",
                "exact_raw_negative_pool_size",
                "raw_unique_negative_count",
                "negative_escape_termination_reason",
                "memory_pressure_triggered",
                "host_timed_out",
                "host_memory_killed",
                "bidirectional_midpoint_hybrid_attempted",
                "bidirectional_midpoint_hybrid_accepted",
                "bidirectional_midpoint_hybrid_fallback_used",
                "bidirectional_midpoint_hybrid_fallback_reason",
                "bidirectional_midpoint_prepass_wall_sec",
                "wall_time_seconds",
            )
        },
    }
    _write_json(output_path, payload)
    return 0 if not safety_issues else 2


if __name__ == "__main__":
    raise SystemExit(main())

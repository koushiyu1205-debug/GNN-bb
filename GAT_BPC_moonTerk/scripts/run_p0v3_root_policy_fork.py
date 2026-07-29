#!/usr/bin/env python3
"""Fork one saved P0 V3 root state under an exact pass-policy arm.

The state contains the complete active master column set immediately before a
pricing action.  Each fork rebuilds that RMP, validates the source dual/bound,
then closes the root independently.  The result is a development-only
cost-to-closure label; it never reuses or certifies the source solve.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import (  # noqa: E402
    RELAXED_LABELING_WORKER,
    solve_node_pricing_with_b2b_r3,
)
from lunar_ice_bpc.exact.core.branching import (  # noqa: E402
    branch_context_from_payload,
)
from lunar_ice_bpc.exact.core.cuts import (  # noqa: E402
    CutContext,
    CutLineage,
    cut_context_from_payload,
    cut_lineage_from_payload,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.exact.core.journey import (  # noqa: E402
    journey_column_from_solution_payload,
)
from lunar_ice_bpc.runners.b4_1_true_dual_proof_tail import (  # noqa: E402
    _diagnostic_b0_placeholder,
)


SNAPSHOT_SCHEMA = "lunar_ice_bpc.p0v3_root_policy_state_snapshot.v1"
CATALOG_SCHEMA = "lunar_ice_bpc.p0v3_root_policy_column_catalog.v1"
OUTPUT_SCHEMA = "lunar_ice_bpc.p0v3_root_policy_fork.v1"
POLICIES = (
    "harvest_then_proof",
    "adaptive_sparse_harvest_v1",
    "proof_only",
)
FIRST_PASS_STRATEGIES = (
    "policy_default",
    "harvest_then_proof",
    "proof_only",
)
MAX_ROUNDS_BY_SCALE = {5: 20, 10: 40, 20: 80, 30: 120}
MEMORY_GB_BY_SCALE = {5: 2.0, 10: 4.0, 20: 8.0, 30: 10.0}


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


def _sha256_json(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _validated_inputs(
    *,
    data,
    snapshot: dict,
    catalog: dict,
) -> None:
    if snapshot.get("schema_version") != SNAPSHOT_SCHEMA:
        raise SystemExit("root policy snapshot schema mismatch")
    if catalog.get("schema_version") != CATALOG_SCHEMA:
        raise SystemExit("root policy column catalog schema mismatch")
    if (
        not bool(snapshot.get("development_only"))
        or bool(snapshot.get("deployable"))
        or bool(snapshot.get("can_certify"))
    ):
        raise SystemExit("root policy snapshot is not development-only")
    for payload, label in ((snapshot, "snapshot"), (catalog, "catalog")):
        if payload.get("instance_content_hash") != data.instance_content_hash:
            raise SystemExit(f"{label} instance content hash mismatch")
    if (
        snapshot.get("service_timing_policy_id")
        != data.service_timing_policy_id
    ):
        raise SystemExit("snapshot service-timing policy mismatch")
    recorded_state_hash = str(snapshot.get("state_hash") or "")
    state_payload = dict(snapshot)
    state_payload.pop("state_hash", None)
    if recorded_state_hash != _sha256_json(state_payload):
        raise SystemExit("root policy snapshot content hash mismatch")
    recorded_catalog_hash = str(catalog.get("catalog_hash") or "")
    catalog_payload = dict(catalog)
    catalog_payload.pop("catalog_hash", None)
    if recorded_catalog_hash != _sha256_json(catalog_payload):
        raise SystemExit("root policy column catalog content hash mismatch")
    columns = dict(catalog.get("columns") or {})
    missing = [
        column_id
        for column_id in snapshot.get("active_column_ids", ())
        if column_id not in columns
    ]
    if missing:
        raise SystemExit("root policy snapshot references missing columns")


def _configure_environment(
    *,
    policy: str,
    adaptive_harvest_cap_sec: float,
    adaptive_harvest_max_processed_labels: int,
    memory_limit_gb: float,
) -> None:
    os.environ["LUNAR_ICE_EXACT_FINAL_JUDGE_FIRST"] = "1"
    os.environ["LUNAR_ICE_SPPRC_EXACT_BACKEND"] = (
        "native_rcspp_inprocess"
    )
    os.environ["LUNAR_ICE_SPPRC_MEMORY_LIMIT_GB"] = str(
        float(memory_limit_gb)
    )
    os.environ["LUNAR_ICE_SPPRC_GRAPH_CACHE_ENTRIES"] = "1"
    os.environ["LUNAR_ICE_SPPRC_COMPLETION_BOUND"] = "0"
    os.environ["LUNAR_ICE_SPPRC_SUBSET_DOMINANCE"] = "1"
    os.environ["LUNAR_ICE_SPPRC_CUT_STATE"] = "1"
    os.environ["LUNAR_ICE_LABELING_FINAL_JUDGE_PASS_POLICY"] = policy
    if (
        policy == "adaptive_sparse_harvest_v1"
        and int(adaptive_harvest_max_processed_labels) <= 0
    ):
        os.environ[
            "LUNAR_ICE_LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_CAP_SEC"
        ] = str(float(adaptive_harvest_cap_sec))
    else:
        os.environ.pop(
            "LUNAR_ICE_LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_CAP_SEC",
            None,
        )


def _exact_safe(result: dict) -> bool:
    final_judge = dict(result.get("final_judge") or {})
    return bool(
        result.get("node_status") == "NODE_LP_CERTIFIED"
        and result.get("pricing_state") == "CERTIFIED_NO_NEGATIVE"
        and result.get("certificate_scope") == "BPC_NODE_LP_CERTIFIED"
        and result.get("node_lp_bound_official")
        and result.get("uses_true_dual_bpc_certificate")
        and result.get("manual_rc_audit_pass")
        and result.get("pricing_rc_audit_pass")
        and result.get("final_judge_certifying_proof_kind")
        and (result.get("certificate_ledger") or {}).get("valid")
        and not bool(final_judge.get("labels_dropped"))
    )


def _legal_censored_incomplete(result: dict) -> bool:
    final_judge = dict(result.get("final_judge") or {})
    ledger = dict(result.get("certificate_ledger") or {})
    return bool(
        result.get("node_status") == "NODE_INCOMPLETE"
        and result.get("pricing_state") == "INCOMPLETE_LIMIT"
        and result.get("certificate_scope")
        == "DIAGNOSTIC_PRICING_FRONTIER"
        and not bool(result.get("node_lp_bound_official"))
        and not bool(result.get("uses_true_dual_bpc_certificate"))
        and not bool(ledger.get("uses_true_dual_bpc_certificate"))
        and not bool(final_judge.get("labels_dropped"))
    )


def _universe_safe(result: dict) -> bool:
    for row in result.get("history", ()):
        if int(row.get("deferred_permanent_drop_count") or 0) != 0:
            return False
        if int(row.get("entry_audit_rejected_selected_count") or 0) != 0:
            return False
        if not bool(row.get("selected_column_entry_audit_pass", True)):
            return False
    final_judge = dict(result.get("final_judge") or {})
    telemetry = dict(final_judge.get("telemetry") or {})
    return bool(
        int(telemetry.get("guidance_filter_count") or 0) == 0
        and int(telemetry.get("guidance_arc_drop_count") or 0) == 0
        and int(telemetry.get("guidance_label_drop_count") or 0) == 0
        and int(telemetry.get("guidance_branch_pair_drop_count") or 0) == 0
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--column-catalog", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--policy", choices=POLICIES, required=True)
    parser.add_argument(
        "--first-pass-strategy",
        choices=FIRST_PASS_STRATEGIES,
        default="policy_default",
        help=(
            "Development-only one-step action override. Later rounds return "
            "to the selected policy."
        ),
    )
    parser.add_argument("--adaptive-harvest-cap-sec", type=float, default=0.25)
    parser.add_argument(
        "--adaptive-harvest-max-processed-labels",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--adaptive-sparse-harvest-strikes-before-proof",
        type=int,
        default=1,
    )
    parser.add_argument("--wall-time-limit-sec", type=float, default=600.0)
    parser.add_argument("--memory-limit-gb", type=float, default=None)
    parser.add_argument("--max-rounds", type=int, default=None)
    args = parser.parse_args()

    if (
        not math.isfinite(float(args.adaptive_harvest_cap_sec))
        or float(args.adaptive_harvest_cap_sec) <= 0.0
    ):
        raise SystemExit("adaptive harvest cap must be finite and positive")
    if int(args.adaptive_harvest_max_processed_labels) < 0:
        raise SystemExit(
            "adaptive harvest processed-label budget must be nonnegative"
        )
    if int(args.adaptive_sparse_harvest_strikes_before_proof) < 1:
        raise SystemExit(
            "adaptive sparse-harvest strikes before proof must be at least one"
        )
    instance_path = (ROOT / args.instance).resolve()
    snapshot_path = (ROOT / args.snapshot).resolve()
    catalog_path = (ROOT / args.column_catalog).resolve()
    data = load_lunar_ice_data(_load_json(instance_path))
    snapshot = _load_json(snapshot_path)
    catalog = _load_json(catalog_path)
    _validated_inputs(data=data, snapshot=snapshot, catalog=catalog)
    source_sparse_harvest_strikes = int(
        snapshot.get("required_sparse_harvest_strikes") or 1
    )
    if (
        int(args.adaptive_sparse_harvest_strikes_before_proof)
        != source_sparse_harvest_strikes
    ):
        raise SystemExit(
            "fork/source sparse-harvest strike policy mismatch"
        )

    scale = int(data.scale)
    if scale not in MAX_ROUNDS_BY_SCALE:
        raise SystemExit("root policy fork accepts scale5/10/20/30 only")
    memory_limit_gb = (
        MEMORY_GB_BY_SCALE[scale]
        if args.memory_limit_gb is None
        else float(args.memory_limit_gb)
    )
    max_rounds = (
        MAX_ROUNDS_BY_SCALE[scale]
        if args.max_rounds is None
        else max(1, int(args.max_rounds))
    )
    _configure_environment(
        policy=str(args.policy),
        adaptive_harvest_cap_sec=float(
            args.adaptive_harvest_cap_sec
        ),
        adaptive_harvest_max_processed_labels=int(
            args.adaptive_harvest_max_processed_labels
        ),
        memory_limit_gb=memory_limit_gb,
    )

    catalog_columns = dict(catalog["columns"])
    initial_columns = tuple(
        journey_column_from_solution_payload(
            data, catalog_columns[column_id]
        )
        for column_id in snapshot["active_column_ids"]
    )
    branch_context = branch_context_from_payload(
        snapshot.get("branch_context") or {}
    )
    cut_context = cut_context_from_payload(
        snapshot.get("cut_context") or {}
    )
    cut_lineage = cut_lineage_from_payload(
        snapshot.get("cut_lineage") or {}
    )
    started = perf_counter()
    result = solve_node_pricing_with_b2b_r3(
        data,
        branch_context=branch_context,
        cut_context=cut_context,
        cut_lineage=cut_lineage,
        live_cut_policy_hash=str(
            snapshot.get("live_cut_policy_hash") or ""
        ),
        separator_policy_version=str(
            snapshot.get("separator_policy_version") or ""
        ),
        node_id=str(snapshot.get("node_id") or "root"),
        initial_columns=initial_columns,
        max_direct_tasks=len(data.task_ids),
        max_rounds=max_rounds,
        wall_time_limit_sec=float(args.wall_time_limit_sec),
        max_columns_per_round=int(
            snapshot["max_columns_per_round"]
        ),
        b0_direct=_diagnostic_b0_placeholder(data),
        tail_dual_stabilization_enabled=True,
        tail_dual_stabilization_alpha=0.7,
        tail_dual_stabilization_window=5,
        worker_pricer_kind=RELAXED_LABELING_WORKER,
        labeling_final_judge_enabled=True,
        labeling_final_judge_max_exact_tasks=len(data.task_ids),
        labeling_final_judge_exact_harvest_target=int(
            snapshot["effective_harvest_target"]
        ),
        labeling_final_judge_harvest_max_processed_labels=int(
            args.adaptive_harvest_max_processed_labels
        ),
        return_active_columns_payload=False,
        development_initial_final_judge_pass_strategy=(
            None
            if args.first_pass_strategy == "policy_default"
            else str(args.first_pass_strategy)
        ),
        development_sparse_harvest_strikes_before_proof=int(
            args.adaptive_sparse_harvest_strikes_before_proof
        ),
    )
    wall_sec = perf_counter() - started
    history = list(result.get("history") or ())
    first = dict(history[0]) if history else {}
    source_duals = dict(snapshot.get("true_duals") or {})
    fork_duals = dict(first.get("dual_context") or {})
    source_task_duals = dict(source_duals.get("task_duals") or {})
    fork_task_duals = dict(fork_duals.get("task_duals") or {})
    source_cut_duals = dict(source_duals.get("cut_duals") or {})
    fork_cut_duals = dict(fork_duals.get("cut_duals") or {})
    dual_keys = set(source_task_duals) | set(fork_task_duals)
    cut_keys = set(source_cut_duals) | set(fork_cut_duals)
    max_abs_dual_delta = max(
        [
            abs(
                float(source_task_duals.get(key, 0.0))
                - float(fork_task_duals.get(key, 0.0))
            )
            for key in dual_keys
        ]
        + [
            abs(
                float(source_cut_duals.get(key, 0.0))
                - float(fork_cut_duals.get(key, 0.0))
            )
            for key in cut_keys
        ]
        + [
            abs(
                float(source_duals.get("fleet_dual") or 0.0)
                - float(fork_duals.get("fleet_dual") or 0.0)
            )
        ],
        default=0.0,
    )
    bound_delta = (
        None
        if first.get("node_lp_bound") is None
        else float(first["node_lp_bound"])
        - float(snapshot["node_lp_bound"])
    )
    state_rebuild_match = bool(
        bound_delta is not None
        and abs(bound_delta) <= 1.0e-9
        and max_abs_dual_delta <= 1.0e-9
    )
    output = {
        "schema_version": OUTPUT_SCHEMA,
        "development_only": True,
        "deployable": False,
        "can_certify_source_solve": False,
        "mutates_p0": False,
        "instance_id": data.instance_id,
        "instance_content_hash": data.instance_content_hash,
        "source_snapshot_path": str(snapshot_path),
        "source_state_hash": str(snapshot["state_hash"]),
        "source_round": int(snapshot["round"]),
        "source_active_column_count": len(initial_columns),
        "source_pass_policy": str(
            snapshot.get("source_pass_policy") or ""
        ),
        "source_pass_strategy": str(
            snapshot.get("source_pass_strategy") or ""
        ),
        "policy": str(args.policy),
        "requested_first_pass_strategy": str(
            args.first_pass_strategy
        ),
        "adaptive_harvest_cap_sec": (
            float(args.adaptive_harvest_cap_sec)
            if args.policy == "adaptive_sparse_harvest_v1"
            and int(args.adaptive_harvest_max_processed_labels) <= 0
            else None
        ),
        "adaptive_harvest_max_processed_labels": int(
            args.adaptive_harvest_max_processed_labels
        ),
        "sparse_harvest_strikes_before_proof": int(
            args.adaptive_sparse_harvest_strikes_before_proof
        ),
        "state_rebuild_match": state_rebuild_match,
        "state_rebuild_bound_delta": bound_delta,
        "state_rebuild_max_abs_dual_delta": max_abs_dual_delta,
        "state_rebuild_diagnostic_fingerprint_match": (
            str(fork_duals.get("dual_fingerprint") or "")
            == str(source_duals.get("dual_fingerprint") or "")
        ),
        "fork_exact_safe": _exact_safe(result),
        "fork_legal_censored_incomplete": (
            _legal_censored_incomplete(result)
        ),
        "fork_outcome": (
            "EXACT_CLOSURE"
            if _exact_safe(result)
            else "LEGAL_CENSORED_INCOMPLETE"
            if _legal_censored_incomplete(result)
            else "INVALID_OR_UNSAFE"
        ),
        "fork_universe_safe": _universe_safe(result),
        "fork_wall_sec": round(float(wall_sec), 9),
        "fork_observed_cost_lower_bound_sec": (
            round(float(wall_sec), 9)
            if _legal_censored_incomplete(result)
            else None
        ),
        "fork_censoring_wall_time_limit_sec": (
            float(args.wall_time_limit_sec)
            if _legal_censored_incomplete(result)
            else None
        ),
        "fork_censoring_memory_limit_gb": (
            float(memory_limit_gb)
            if _legal_censored_incomplete(result)
            else None
        ),
        "fork_pricing_round_count": int(
            result.get("pricing_round_count") or 0
        ),
        "fork_final_judge_wall_sec": float(
            result.get("final_judge_wall_time") or 0.0
        ),
        "fork_node_lp_bound": result.get("node_lp_bound"),
        "fork_added_column_count": int(
            result.get("added_column_count") or 0
        ),
        "first_action_pass_strategy": first.get(
            "labeling_final_judge_pass_strategy"
        ),
        "first_action_wall_sec": first.get(
            "final_judge_wall_time"
        ),
        "first_action_added_column_count": first.get(
            "added_column_count"
        ),
        "first_action_pricing_state": first.get("pricing_state"),
        "terminal_pricing_state": result.get("pricing_state"),
        "terminal_node_status": result.get("node_status"),
        "terminal_certificate_scope": result.get(
            "certificate_scope"
        ),
        "terminal_node_lp_bound_official": bool(
            result.get("node_lp_bound_official")
        ),
        "terminal_uses_true_dual_bpc_certificate": bool(
            result.get("uses_true_dual_bpc_certificate")
        ),
        "terminal_labels_dropped": bool(
            (result.get("final_judge") or {}).get("labels_dropped")
        ),
        "trajectory_features": dict(
            snapshot.get("trajectory_features") or {}
        ),
    }
    output_payload = {
        **output,
        "fork_hash": _sha256_json(output),
    }
    _write_json((ROOT / args.output).resolve(), output_payload)
    print(
        json.dumps(
            {
                "policy": str(args.policy),
                "requested_first_pass_strategy": str(
                    args.first_pass_strategy
                ),
                "source_round": int(snapshot["round"]),
                "state_rebuild_match": state_rebuild_match,
                "fork_exact_safe": output["fork_exact_safe"],
                "fork_wall_sec": round(float(wall_sec), 6),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Replay a fixed group of valid live-SRI candidates with exact pricing.

This is a diagnostic counterfactual, not a certificate shortcut.  It starts
from a persisted root column pool, activates only mathematically valid SRI
rows selected from the current fractional RMP, and then runs the unchanged
true-dual node-pricing and live-SRI closure loop.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sys
from time import perf_counter
from typing import Iterator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.bpc.cuts.live_sri import (  # noqa: E402
    LiveSriPolicy,
    separate_live_sri,
)
from lunar_ice_bpc.exact.bpc.master.journey_master import (  # noqa: E402
    solve_root_journey_master,
)
from lunar_ice_bpc.exact.bpc.pricing.backends import (  # noqa: E402
    PRICING_LIFECYCLE_SCOPE_TREE_NODE,
)
from lunar_ice_bpc.exact.bpc.pricing.backends.native_bidirectional_hybrid import (  # noqa: E402
    NATIVE_BIDIRECTIONAL_ROOT_PARTIAL_HYBRID_BACKEND_ID,
)
from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (  # noqa: E402
    spprc_engine_build_hash,
)
from lunar_ice_bpc.exact.bpc.solver.live_sri_solver import (  # noqa: E402
    solve_node_pricing_with_live_sri,
)
from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import (  # noqa: E402
    RELAXED_LABELING_WORKER,
)
from lunar_ice_bpc.exact.bpc.solver.root_node_solver import (  # noqa: E402
    _reference_seed_direct_placeholder,
)
from lunar_ice_bpc.exact.core.branching import BranchContext  # noqa: E402
from lunar_ice_bpc.exact.core.cuts import (  # noqa: E402
    CutContext,
    CutLineage,
    CutLineageEntry,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.exact.core.journey import (  # noqa: E402
    journey_column_from_solution_payload,
)


SCHEMA_VERSION = "p0v4_sri_candidate_group_fixed_cut_replay.v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root-probe", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--candidate-ranks",
        default="7",
        help="Comma-separated, one-based ranks in the full violated SRI list.",
    )
    parser.add_argument("--time-limit-sec", type=float, default=900.0)
    parser.add_argument("--max-rounds", type=int, default=16)
    parser.add_argument("--max-columns-per-round", type=int, default=128)
    parser.add_argument("--incumbent-objective", type=float, default=None)
    parser.add_argument("--memory-limit-gb", type=float, default=10.867122)
    parser.add_argument(
        "--backend-id",
        default=NATIVE_BIDIRECTIONAL_ROOT_PARTIAL_HYBRID_BACKEND_ID,
    )
    args = parser.parse_args()

    ranks = _parse_ranks(args.candidate_ranks)
    probe_path = Path(args.root_probe).resolve()
    output_path = Path(args.output).resolve()
    probe = _read_json(probe_path)
    if str(probe.get("pricing_state") or "") != "CERTIFIED_NO_NEGATIVE":
        raise ValueError("source root probe is not exact-pricing closed")
    if not bool((probe.get("final_judge") or {}).get("can_certify_no_negative")):
        raise ValueError("source root probe lacks a no-negative certificate")

    instance_path = Path(str(probe["instance_path"])).resolve()
    data = load_lunar_ice_data(_read_json(instance_path))
    active_payloads = tuple(probe.get("active_columns") or ())
    if not active_payloads:
        raise ValueError("source root probe has no active columns")
    columns = tuple(
        journey_column_from_solution_payload(data, row)
        for row in active_payloads
    )

    base = solve_root_journey_master(
        data,
        columns,
        rmp_iteration_id="p0v4-sri-group-base",
    )
    if base.rmp.status != "RESTRICTED_RMP_OPTIMAL":
        raise ValueError("source root pool RMP is not optimal")
    separated = separate_live_sri(
        data.task_ids,
        base.rmp.primal_columns,
        subset_sizes=(3,),
        selection_capacity=100_000,
        existing_cut_context=CutContext(),
        violation_eps=1.0e-6,
    )
    if not separated.full_enumeration_completed:
        raise ValueError("live-SRI candidate enumeration was incomplete")
    if max(ranks) > len(separated.selected):
        raise ValueError(
            "candidate rank exceeds violated SRI count: "
            f"{max(ranks)} > {len(separated.selected)}"
        )

    selected = tuple(separated.selected[rank - 1] for rank in ranks)
    cut_context = CutContext(tuple(row.cut for row in selected))
    policy = LiveSriPolicy.named("P0")
    cut_lineage = CutLineage(
        entries=tuple(
            CutLineageEntry(
                cut_id=row.cut.cut_id,
                scope="global",
                origin_node_id="node_000",
                ancestor_path=tuple(),
                policy_version=policy.version,
            )
            for row in selected
        ),
        policy_version=policy.version,
    )
    screened = solve_root_journey_master(
        data,
        columns,
        cut_context=cut_context,
        cut_lineage=cut_lineage,
        live_cut_policy_hash=policy.policy_hash,
        rmp_iteration_id="p0v4-sri-group-screen",
    )
    if screened.rmp.status != "RESTRICTED_RMP_OPTIMAL":
        raise ValueError("fixed-cut restricted RMP is not optimal")

    backend_id = str(args.backend_id)
    environment = {
        "LUNAR_ICE_SPPRC_EXACT_BACKEND": backend_id,
        "LUNAR_ICE_SPPRC_MEMORY_LIMIT_GB": str(args.memory_limit_gb),
        "LUNAR_ICE_SPPRC_GRAPH_CACHE_ENTRIES": "1",
        "LUNAR_ICE_SPPRC_COMPLETION_BOUND": "0",
        "LUNAR_ICE_SPPRC_SUBSET_DOMINANCE": "1",
        "LUNAR_ICE_SPPRC_CUT_STATE": "1",
        "LUNAR_ICE_EXACT_NEGATIVE_ESCAPE_ENABLED": "1",
        "LUNAR_ICE_BATCH_MASTER_ADMISSION_ENABLED": "1",
        "LUNAR_ICE_LABELING_WORKER_NG_SIZES": "8,16,32,50",
        "LUNAR_ICE_LABELING_WORKER_HARD_TIME_CAP_SEC": "300",
        "LUNAR_ICE_EXACT_FINAL_JUDGE_FIRST": "1",
        "LUNAR_ICE_LABELING_FINAL_JUDGE_PASS_POLICY": (
            "harvest_then_proof"
        ),
        "LUNAR_ICE_ONE_DEVIATION_MANIFEST": None,
        "LUNAR_ICE_GAT_GUIDANCE_MODE": "off",
    }
    engine_hash_at_start = spprc_engine_build_hash(backend_id)
    started = perf_counter()
    with _temporary_environment(environment):
        result = solve_node_pricing_with_live_sri(
            data,
            policy=policy,
            depth=0,
            branch_context=BranchContext(),
            cut_context=cut_context,
            cut_lineage=cut_lineage,
            node_id="node_000_sri_candidate_group_replay",
            ancestor_path=tuple(),
            pricing_lifecycle_scope=PRICING_LIFECYCLE_SCOPE_TREE_NODE,
            initial_columns=columns,
            incumbent_objective=args.incumbent_objective,
            max_direct_tasks=len(data.task_ids),
            max_rounds=max(1, int(args.max_rounds)),
            wall_time_limit_sec=max(0.001, float(args.time_limit_sec)),
            max_columns_per_round=max(
                1,
                int(args.max_columns_per_round),
            ),
            b0_direct=_reference_seed_direct_placeholder(data),
            tail_dual_stabilization_enabled=True,
            tail_dual_stabilization_alpha=0.7,
            tail_dual_stabilization_window=5,
            worker_pricer_kind=RELAXED_LABELING_WORKER,
            labeling_final_judge_enabled=True,
            labeling_final_judge_max_exact_tasks=len(data.task_ids),
            labeling_final_judge_exact_harvest_target=max(
                1,
                int(args.max_columns_per_round),
            ),
        )
    elapsed_sec = perf_counter() - started
    engine_hash_at_end = spprc_engine_build_hash(backend_id)

    master = result.get("_master")
    primal_columns = (
        []
        if master is None
        else list(master.rmp.primal_columns)
    )
    primal_integral = _primal_integral(primal_columns)
    certificate_ledger = dict(result.get("certificate_ledger") or {})
    exact_safe = bool(
        str(result.get("node_status") or "") == "NODE_LP_CERTIFIED"
        and str(result.get("pricing_state") or "")
        == "CERTIFIED_NO_NEGATIVE"
        and bool(result.get("node_lp_bound_official"))
        and bool(result.get("manual_rc_audit_pass"))
        and bool(result.get("pricing_rc_audit_pass"))
        and bool(certificate_ledger.get("valid"))
        and engine_hash_at_start == engine_hash_at_end
    )
    live_sri = dict(result.get("live_sri") or {})
    payload = {
        "schema_version": SCHEMA_VERSION,
        "source_probe": str(probe_path),
        "source_probe_sha256": _sha256_bytes(probe_path.read_bytes()),
        "source_active_columns_sha256": _sha256_json(active_payloads),
        "instance_path": str(instance_path),
        "backend_id": backend_id,
        "pricing_lifecycle_scope": PRICING_LIFECYCLE_SCOPE_TREE_NODE,
        "engine_hash_at_start": engine_hash_at_start,
        "engine_hash_at_end": engine_hash_at_end,
        "engine_hash_valid": (
            engine_hash_at_start == engine_hash_at_end
        ),
        "initial_column_count": len(columns),
        "base_rmp_bound": base.rmp.objective_bound,
        "base_primal_column_count": len(base.rmp.primal_columns),
        "violated_sri_count": separated.violated_candidate_count,
        "candidate_ranks_1based": list(ranks),
        "candidate_rows": [
            {
                "rank_1based": rank,
                "cut": row.cut.to_payload(),
                "activity": row.activity,
                "violation": row.violation,
            }
            for rank, row in zip(ranks, selected)
        ],
        "fixed_cut_screen_bound": screened.rmp.objective_bound,
        "fixed_cut_screen_gain": (
            None
            if (
                base.rmp.objective_bound is None
                or screened.rmp.objective_bound is None
            )
            else float(screened.rmp.objective_bound)
            - float(base.rmp.objective_bound)
        ),
        "wall_time_limit_sec": float(args.time_limit_sec),
        "elapsed_sec": elapsed_sec,
        "node_status": result.get("node_status"),
        "pricing_state": result.get("pricing_state"),
        "certificate_scope": result.get("certificate_scope"),
        "node_lp_bound": result.get("node_lp_bound"),
        "node_lp_bound_official": result.get(
            "node_lp_bound_official"
        ),
        "pricing_round_count": result.get("pricing_round_count"),
        "added_column_count": result.get("added_column_count"),
        "active_column_count": len(
            tuple(result.get("_active_columns") or ())
        ),
        "primal_integral": primal_integral,
        "primal_columns": primal_columns,
        "active_cut_count": live_sri.get("active_cut_count"),
        "live_sri_terminal_reason": live_sri.get(
            "terminal_reason"
        ),
        "live_sri_separation_history": live_sri.get(
            "separation_history"
        ),
        "final_judge_can_certify_no_negative": (
            result.get("final_judge") or {}
        ).get("can_certify_no_negative"),
        "manual_rc_audit_pass": result.get(
            "manual_rc_audit_pass"
        ),
        "pricing_rc_audit_pass": result.get(
            "pricing_rc_audit_pass"
        ),
        "certificate_ledger": certificate_ledger,
        "exact_safe": exact_safe,
        "history_summary": [
            {
                key: row.get(key)
                for key in (
                    "round",
                    "node_lp_bound",
                    "added_column_count",
                    "raw_unique_negative_count",
                    "negative_escape_triggered",
                    "negative_escape_termination_reason",
                    "pricing_state",
                    "can_certify_no_negative",
                    "round_elapsed_wall_time_sec",
                )
            }
            for row in result.get("history") or ()
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                key: payload[key]
                for key in (
                    "elapsed_sec",
                    "node_status",
                    "pricing_state",
                    "node_lp_bound",
                    "pricing_round_count",
                    "added_column_count",
                    "active_column_count",
                    "primal_integral",
                    "active_cut_count",
                    "live_sri_terminal_reason",
                    "exact_safe",
                )
            },
            sort_keys=True,
        )
    )
    print(output_path)
    return 0 if exact_safe else 1


def _parse_ranks(raw: str) -> tuple[int, ...]:
    ranks = tuple(int(value.strip()) for value in raw.split(",") if value.strip())
    if not ranks or any(rank <= 0 for rank in ranks):
        raise ValueError("candidate ranks must be positive")
    if len(set(ranks)) != len(ranks):
        raise ValueError("candidate ranks must be unique")
    return ranks


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _primal_integral(rows: list[dict]) -> bool:
    return bool(rows) and all(
        abs(float(row.get("lambda_value") or 0.0) - round(
            float(row.get("lambda_value") or 0.0)
        ))
        <= 1.0e-7
        for row in rows
    )


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_json(value: object) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256_bytes(raw)


@contextmanager
def _temporary_environment(
    updates: dict[str, str | None],
) -> Iterator[None]:
    previous = {key: os.environ.get(key) for key in updates}
    try:
        for key, value in updates.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = str(value)
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


if __name__ == "__main__":
    raise SystemExit(main())

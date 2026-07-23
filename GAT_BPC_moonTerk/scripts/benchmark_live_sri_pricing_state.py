#!/usr/bin/env python3
"""Replay real Live-SRI node duals against exact Native pricing variants.

The benchmark disables the Native graph cache and alternates AB/BA order.  It
compares the engine-reported solve time and exact result for nonzero-dual cut
projection enabled versus the full active-cut pricing context.  The same script
can be rerun before and after Native state-layout changes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from statistics import mean, median
from time import perf_counter

from lunar_ice_bpc.exact.bpc.core.column_signature import (
    column_signature_from_journey,
)
from lunar_ice_bpc.exact.bpc.pricing.backends import (
    BackendPricingRequest,
    NativeRcsppInprocessBackend,
)
from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (
    spprc_engine_build_hash,
    spprc_instance_hash,
)
from lunar_ice_bpc.exact.core.branching import (
    branch_context_from_payload,
)
from lunar_ice_bpc.exact.core.cuts import (
    cut_context_from_payload,
    stable_payload_hash,
    true_dual_binding_hash,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals


SCHEMA_VERSION = "lunar_ice_bpc.live_sri_pricing_state_benchmark.v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", type=Path, required=True)
    parser.add_argument("--tree-evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=10)
    parser.add_argument("--warmups", type=int, default=1)
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def optional_float_equal(left, right, *, tolerance: float = 1.0e-8) -> bool:
    if left is None or right is None:
        return left is right
    return abs(float(left) - float(right)) <= tolerance


def column_signatures(result) -> tuple[str, ...]:
    return tuple(
        sorted(repr(column_signature_from_journey(column)) for column in result.columns)
    )


def request_for(
    *,
    data,
    dual_context: dict,
    branch_context,
    cut_context,
    node: dict,
    projection_enabled: bool,
) -> BackendPricingRequest:
    duals = JourneyDuals(
        cover={
            str(task_id): float(value)
            for task_id, value in (dual_context.get("task_duals") or {}).items()
        },
        fleet_limit=float(dual_context.get("fleet_dual") or 0.0),
        cuts={
            str(cut_id): float(value)
            for cut_id, value in (dual_context.get("cut_duals") or {}).items()
        },
    )
    config_payload = {
        "benchmark_schema": SCHEMA_VERSION,
        "subset_dominance_enabled": True,
        "graph_cache_entries": 0,
    }
    return BackendPricingRequest(
        data=data,
        true_duals=duals,
        branch_context=branch_context,
        cut_context=cut_context,
        subset_dominance_enabled=True,
        completion_bound_enabled=False,
        cut_dual_projection_enabled=projection_enabled,
        instance_hash=spprc_instance_hash(data),
        config_hash=stable_payload_hash(config_payload),
        dual_binding_hash=true_dual_binding_hash(
            duals.cover,
            fleet_limit=duals.fleet_limit,
            cuts=duals.cuts,
        ),
        branch_context_hash=stable_payload_hash(branch_context.to_payload()),
        cut_context_hash=cut_context.active_cut_context_hash,
        cut_lineage_hash=str(node.get("cut_lineage_hash") or ""),
        live_cut_policy_hash=str(node.get("live_cut_policy_hash") or ""),
        rmp_iteration_id=str(dual_context.get("rmp_iteration_id") or ""),
        separator_policy_version=str(
            (node.get("live_sri") or {}).get("separator_policy_version") or ""
        ),
    )


def run_once(request: BackendPricingRequest) -> tuple[dict, object]:
    started = perf_counter()
    result = NativeRcsppInprocessBackend().solve(request)
    process_wall = perf_counter() - started
    row = {
        "projection_enabled": bool(request.cut_dual_projection_enabled),
        "engine_status": result.engine_status,
        "search_exhaustive": result.search_exhaustive,
        "frontier_empty": result.frontier_empty,
        "labels_dropped": result.labels_dropped,
        "certificate_blockers": list(result.certificate_blockers),
        "can_enter_certificate_audit": result.can_enter_certificate_audit,
        "best_found_rc": result.best_found_rc,
        "proved_no_rc_below": result.proved_no_rc_below,
        "column_count": len(result.columns),
        "column_signatures": list(column_signatures(result)),
        "engine_wall_time_sec": float(result.telemetry["wall_time_seconds"]),
        "process_wall_time_sec": process_wall,
        "extended_labels": int(result.telemetry["extended_labels"]),
        "dominated_labels": int(result.telemetry["dominated_labels"]),
        "active_cut_count": int(result.telemetry["active_cut_count"]),
        "pricing_cut_count": int(result.telemetry["pricing_cut_count"]),
        "projected_zero_dual_cut_count": int(
            result.telemetry["projected_zero_dual_cut_count"]
        ),
        "active_cut_context_hash": result.telemetry["active_cut_context_hash"],
        "pricing_cut_context_hash": result.telemetry["pricing_cut_context_hash"],
        "rc_mismatch_count": int(result.telemetry["rc_mismatch_count"]),
        "max_abs_rc_delta": float(result.telemetry["max_abs_rc_delta"]),
        "native_build_info": result.telemetry["native_build_info"],
    }
    return row, result


def assert_equivalent(projected: object, full: object) -> None:
    # Exact subset dominance is allowed to suppress different dominated,
    # suboptimal negative columns when the pricing state is smaller.  Those
    # harvested column surfaces therefore need not be identical.  The exact
    # contract is the same global best/no-negative proof, exhaustive status,
    # and successful per-column reduced-cost audits.
    checks = {
        "engine_status": projected.engine_status == full.engine_status,
        "search_exhaustive": projected.search_exhaustive == full.search_exhaustive,
        "frontier_empty": projected.frontier_empty == full.frontier_empty,
        "labels_dropped": projected.labels_dropped == full.labels_dropped,
        "certificate_blockers": (
            tuple(projected.certificate_blockers)
            == tuple(full.certificate_blockers)
        ),
        "best_found_rc": optional_float_equal(
            projected.best_found_rc,
            full.best_found_rc,
        ),
        "proved_no_rc_below": optional_float_equal(
            projected.proved_no_rc_below,
            full.proved_no_rc_below,
        ),
        "projected_rc_audit": projected.telemetry["rc_mismatch_count"] == 0,
        "full_rc_audit": full.telemetry["rc_mismatch_count"] == 0,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise RuntimeError("projection/full exact result mismatch: " + ",".join(failed))


def aggregate(rows: list[dict]) -> dict:
    by_mode = {}
    for enabled in (False, True):
        selected = [row for row in rows if row["projection_enabled"] is enabled]
        by_mode["projected" if enabled else "full"] = {
            "count": len(selected),
            "engine_wall_mean_sec": mean(
                row["engine_wall_time_sec"] for row in selected
            ),
            "engine_wall_p50_sec": median(
                row["engine_wall_time_sec"] for row in selected
            ),
            "process_wall_mean_sec": mean(
                row["process_wall_time_sec"] for row in selected
            ),
            "extended_labels_mean": mean(
                row["extended_labels"] for row in selected
            ),
            "dominated_labels_mean": mean(
                row["dominated_labels"] for row in selected
            ),
        }
    full = by_mode["full"]
    projected = by_mode["projected"]
    return {
        "by_mode": by_mode,
        "projected_full_engine_wall_mean_ratio": (
            projected["engine_wall_mean_sec"] / full["engine_wall_mean_sec"]
        ),
        "projected_full_engine_wall_p50_ratio": (
            projected["engine_wall_p50_sec"] / full["engine_wall_p50_sec"]
        ),
        "projected_full_extended_labels_ratio": (
            projected["extended_labels_mean"] / full["extended_labels_mean"]
        ),
    }


def main() -> int:
    args = parse_args()
    repetitions = max(1, int(args.repetitions))
    warmups = max(0, int(args.warmups))
    os.environ["LUNAR_ICE_SPPRC_GRAPH_CACHE_ENTRIES"] = "0"

    data = load_lunar_ice_data(json.loads(args.instance.read_text(encoding="utf-8")))
    tree = json.loads(args.tree_evidence.read_text(encoding="utf-8"))
    nodes = tuple(tree.get("nodes") or ())
    if not nodes:
        raise RuntimeError("tree evidence has no nodes")
    node = nodes[0]
    cut_context = cut_context_from_payload(node.get("cut_context"))
    branch_context = branch_context_from_payload(node.get("branch_context"))
    snapshots = tuple(
        row["dual_context"]
        for row in (node.get("history") or ())
        if isinstance(row.get("dual_context"), dict)
    )
    if not snapshots:
        raise RuntimeError("tree evidence has no dual-context snapshots")
    if cut_context.empty:
        raise RuntimeError("tree evidence has no active cuts")

    snapshot_payloads = []
    all_rows = []
    for snapshot_index, dual_context in enumerate(snapshots, start=1):
        requests = {
            enabled: request_for(
                data=data,
                dual_context=dual_context,
                branch_context=branch_context,
                cut_context=cut_context,
                node=node,
                projection_enabled=enabled,
            )
            for enabled in (False, True)
        }
        for _ in range(warmups):
            projected_row, projected = run_once(requests[True])
            full_row, full = run_once(requests[False])
            assert_equivalent(projected, full)

        rows = []
        for repetition in range(1, repetitions + 1):
            order = (False, True) if repetition % 2 else (True, False)
            pair = {}
            for order_index, enabled in enumerate(order, start=1):
                row, result = run_once(requests[enabled])
                row.update(
                    {
                        "snapshot_index": snapshot_index,
                        "repetition": repetition,
                        "order_index": order_index,
                        "order": "full/projected" if order == (False, True) else "projected/full",
                        "rmp_iteration_id": str(
                            dual_context.get("rmp_iteration_id") or ""
                        ),
                    }
                )
                rows.append(row)
                pair[enabled] = result
            assert_equivalent(pair[True], pair[False])
        summary = aggregate(rows)
        snapshot_payloads.append(
            {
                "snapshot_index": snapshot_index,
                "rmp_iteration_id": str(
                    dual_context.get("rmp_iteration_id") or ""
                ),
                "full_active_cut_count": len(cut_context.cuts),
                "nonzero_cut_dual_count": sum(
                    float(value) != 0.0
                    for value in (dual_context.get("cut_duals") or {}).values()
                ),
                "summary": summary,
                "rows": rows,
            }
        )
        all_rows.extend(rows)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "instance": str(args.instance),
        "instance_sha256": sha256(args.instance),
        "tree_evidence": str(args.tree_evidence),
        "tree_evidence_sha256": sha256(args.tree_evidence),
        "engine_build_hash": spprc_engine_build_hash("native_rcspp_inprocess"),
        "graph_cache_entries": 0,
        "subset_dominance_enabled": True,
        "repetitions_per_snapshot_per_mode": repetitions,
        "warmups_per_snapshot_per_mode": warmups,
        "snapshot_count": len(snapshot_payloads),
        "all_exact_result_pairs_equivalent": True,
        "aggregate": aggregate(all_rows),
        "snapshots": snapshot_payloads,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload["aggregate"], indent=2, sort_keys=True))
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

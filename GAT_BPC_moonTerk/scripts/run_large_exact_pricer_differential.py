#!/usr/bin/env python3
"""Run sequential P0-vs-DSSR exact-pricing differentials by scale."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import monotonic

from lunar_ice_bpc.exact.bpc.pricing.backends import (
    NATIVE_DSSR_HOST_BACKEND_ID,
    NATIVE_HOST_BACKEND_ID,
    BackendPricingRequest,
    BackendRegistry,
)
from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (
    spprc_engine_build_hash,
    spprc_instance_hash,
)
from lunar_ice_bpc.exact.core.cuts import (
    stable_payload_hash,
    true_dual_binding_hash,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scales",
        type=int,
        nargs="+",
        default=(5, 10, 20, 30, 50),
    )
    parser.add_argument("--instance-index", type=int, default=1)
    parser.add_argument("--cover-dual", type=float, default=0.0)
    parser.add_argument("--time-limit-sec", type=float, default=60.0)
    parser.add_argument("--memory-limit-gb", type=float, default=4.0)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def instance_path(scale: int, index: int) -> Path:
    return Path(
        f"data/instances/lunar_ice_sp50_{scale:03d}/"
        f"instance_{index:03d}_logical_graph.json"
    )


def summarize(result, elapsed: float) -> dict:
    telemetry = dict(result.telemetry or {})
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
                "dssr_enabled",
                "dssr_exact_proof_eligible",
                "dssr_non_exact_bypassed",
                "dssr_bypass_reason",
                "dssr_policy_version",
                "dssr_iteration_count",
                "dssr_refinement_count",
                "dssr_final_critical_task_count",
                "dssr_repeated_witness_count",
                "dssr_elementary_witness_returned",
                "dssr_relaxation_no_negative_certificate",
                "dssr_iteration_trace",
            )
        },
    }


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for scale in args.scales:
        path = instance_path(int(scale), int(args.instance_index))
        data = load_lunar_ice_data(
            json.loads(path.read_text(encoding="utf-8"))
        )
        duals = JourneyDuals(
            cover={
                task_id: float(args.cover_dual)
                for task_id in data.task_ids
            }
        )
        pair = {}
        for backend_id in (
            NATIVE_HOST_BACKEND_ID,
            NATIVE_DSSR_HOST_BACKEND_ID,
        ):
            backend = BackendRegistry.create(backend_id)
            request = BackendPricingRequest(
                data=data,
                true_duals=duals,
                wall_time_limit_sec=float(args.time_limit_sec),
                memory_limit_gb=float(args.memory_limit_gb),
                instance_hash=spprc_instance_hash(data),
                config_hash=stable_payload_hash(
                    {
                        "schema_version": (
                            "lunar_ice_bpc.large_exact_differential.v1"
                        ),
                        "scale": int(scale),
                        "cover_dual": float(args.cover_dual),
                        "time_limit_sec": float(args.time_limit_sec),
                        "memory_limit_gb": float(args.memory_limit_gb),
                        "backend_id": backend_id,
                    }
                ),
                engine_hash=spprc_engine_build_hash(backend_id),
                dual_binding_hash=true_dual_binding_hash(
                    duals.cover,
                    fleet_limit=duals.fleet_limit,
                    cuts=duals.cuts,
                ),
            )
            started = monotonic()
            try:
                result = backend.solve(request)
            finally:
                close = getattr(type(backend), "close", None)
                if callable(close):
                    close()
            pair[backend_id] = summarize(
                result,
                monotonic() - started,
            )
        p0 = pair[NATIVE_HOST_BACKEND_ID]
        dssr = pair[NATIVE_DSSR_HOST_BACKEND_ID]
        row = {
            "scale": int(scale),
            "instance_index": int(args.instance_index),
            "instance_id": data.instance_id,
            "instance_content_hash": data.instance_content_hash,
            "instance_path": str(path),
            "p0": p0,
            "dssr": dssr,
            "audit": {
                "both_labels_dropped_zero": bool(
                    not p0["labels_dropped"]
                    and not dssr["labels_dropped"]
                ),
                "both_bindings_match": bool(
                    p0["telemetry"]["request_bindings_match"]
                    and dssr["telemetry"]["request_bindings_match"]
                ),
                "both_exact_no_negative": bool(
                    p0["can_enter_certificate_audit"]
                    and dssr["can_enter_certificate_audit"]
                    and p0["proved_no_rc_below"]
                    == dssr["proved_no_rc_below"]
                ),
                "dssr_progresses_farther": bool(
                    dssr["can_enter_certificate_audit"]
                    and not p0["can_enter_certificate_audit"]
                ),
            },
        }
        rows.append(row)
        (args.output_dir / f"scale{scale:03d}_pair.json").write_text(
            json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
    manifest = {
        "schema_version": (
            "lunar_ice_bpc.large_exact_pricer_differential.v1"
        ),
        "scales": [int(scale) for scale in args.scales],
        "instance_index": int(args.instance_index),
        "cover_dual": float(args.cover_dual),
        "time_limit_sec": float(args.time_limit_sec),
        "memory_limit_gb": float(args.memory_limit_gb),
        "rows": rows,
        "all_small_scale_exact_agree": all(
            row["audit"]["both_exact_no_negative"]
            for row in rows
            if row["scale"] in {5, 10}
        ),
        "all_completed_pair_exact_agree": all(
            row["audit"]["both_exact_no_negative"]
            for row in rows
            if row["p0"]["can_enter_certificate_audit"]
        ),
        "all_bindings_match": all(
            row["audit"]["both_bindings_match"] for row in rows
        ),
        "all_labels_dropped_zero": all(
            row["audit"]["both_labels_dropped_zero"] for row in rows
        ),
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(
            manifest,
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
                key: manifest[key]
                for key in (
                    "schema_version",
                    "scales",
                    "all_small_scale_exact_agree",
                    "all_completed_pair_exact_agree",
                    "all_bindings_match",
                    "all_labels_dropped_zero",
                )
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run one isolated Native exact-pricing probe with audited JSON output."""

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
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", type=Path, required=True)
    parser.add_argument(
        "--backend",
        choices=(NATIVE_HOST_BACKEND_ID, NATIVE_DSSR_HOST_BACKEND_ID),
        default=NATIVE_DSSR_HOST_BACKEND_ID,
    )
    parser.add_argument("--cover-dual", type=float, default=0.0)
    parser.add_argument("--fleet-dual", type=float, default=0.0)
    parser.add_argument("--time-limit-sec", type=float, default=60.0)
    parser.add_argument("--memory-limit-gb", type=float, default=2.0)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = load_lunar_ice_data(
        json.loads(args.instance.read_text(encoding="utf-8"))
    )
    backend = BackendRegistry.create(args.backend)
    started = monotonic()
    try:
        result = backend.solve(
            BackendPricingRequest(
                data=data,
                true_duals=JourneyDuals(
                    cover={
                        task_id: float(args.cover_dual)
                        for task_id in data.task_ids
                    },
                    fleet_limit=float(args.fleet_dual),
                ),
                wall_time_limit_sec=float(args.time_limit_sec),
                memory_limit_gb=float(args.memory_limit_gb),
            )
        )
    finally:
        close = getattr(type(backend), "close", None)
        if callable(close):
            close()
    telemetry = dict(result.telemetry or {})
    payload = {
        "schema_version": "lunar_ice_bpc.large_exact_pricer_probe.v1",
        "instance": str(args.instance),
        "instance_id": data.instance_id,
        "scale": int(data.scale),
        "backend_id": result.backend_id,
        "elapsed_wall_sec": monotonic() - started,
        "engine_status": result.engine_status,
        "search_exhaustive": result.search_exhaustive,
        "frontier_empty": result.frontier_empty,
        "labels_dropped": result.labels_dropped,
        "column_count": len(result.columns),
        "best_found_rc": result.best_found_rc,
        "proved_no_rc_below": result.proved_no_rc_below,
        "can_enter_certificate_audit": result.can_enter_certificate_audit,
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
                "dssr_enabled",
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
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

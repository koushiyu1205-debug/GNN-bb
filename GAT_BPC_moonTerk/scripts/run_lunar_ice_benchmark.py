#!/usr/bin/env python3
"""Run a batch lunar-ice benchmark from a manifest or explicit instances."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.io.config import apply_overrides, load_config
from lunar_ice_bpc.runners.benchmark import run_benchmark


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    parser.add_argument("--manifest", default=None)
    parser.add_argument("--instances", nargs="*", default=None)
    parser.add_argument("--scales", default=None)
    parser.add_argument("--max-workers", type=int, default=None)
    parser.add_argument("--results-csv", default=None)
    parser.add_argument("--solution-dir", default=None)
    parser.add_argument("--summary-json", default=None)
    parser.add_argument("--canonical-dp-max-tasks", type=int, default=None)
    parser.add_argument("--direct-baseline-max-tasks", type=int, default=None)
    parser.add_argument("--direct-baseline-time-limit", type=float, default=None)
    parser.add_argument("--no-restricted-rmp", action="store_true")
    parser.add_argument("--no-direct-pricing", action="store_true")
    parser.add_argument("--direct-pricing-max-tasks", type=int, default=None)
    parser.add_argument("--direct-pricing-cg-rounds", type=int, default=None)
    parser.add_argument("--time-limit", type=float, default=None)
    parser.add_argument("--set", dest="overrides", action="append", default=[])
    args = parser.parse_args()
    config = apply_overrides(load_config(ROOT / args.config), args.overrides) if args.config else apply_overrides({}, args.overrides)
    master_mode = str(config.get("master_mode", "journey"))
    if master_mode != "journey":
        parser.error(f"unsupported master_mode={master_mode!r}; this runner implements the journey main line")

    manifest_value = args.manifest if args.manifest is not None else config.get("manifest", config.get("manifest_path"))
    if manifest_value is None and args.instances is None and not config.get("instances"):
        manifest_value = "data/manifests/lunar_ice_benchmark_manifest.json"
    manifest = _root_path(manifest_value) if manifest_value else None
    instances = args.instances if args.instances is not None else (config.get("instances") or None)
    scales = _parse_scales(args.scales if args.scales is not None else config.get("scales"))
    time_limit = args.time_limit if args.time_limit is not None else config.get("time_limit")
    summary = run_benchmark(
        project_root=ROOT,
        instances=instances,
        manifest_path=manifest,
        scales=scales,
        max_workers=int(args.max_workers if args.max_workers is not None else config.get("max_workers", 4)),
        results_csv=args.results_csv or config.get("results_csv", "runs/csv/lunar_ice_benchmark.csv"),
        solution_dir=args.solution_dir or config.get("solution_dir", "runs/solutions/benchmark"),
        summary_json=args.summary_json or config.get("summary_json", "runs/csv/lunar_ice_benchmark_summary.json"),
        canonical_dp_max_tasks=int(
            args.canonical_dp_max_tasks
            if args.canonical_dp_max_tasks is not None
            else config.get("canonical_dp_max_tasks", config.get("exact_max_tasks", 10))
        ),
        direct_baseline_max_tasks=int(
            args.direct_baseline_max_tasks
            if args.direct_baseline_max_tasks is not None
            else config.get("direct_baseline_max_tasks", 10)
        ),
        direct_baseline_time_limit_sec=(
            float(args.direct_baseline_time_limit)
            if args.direct_baseline_time_limit is not None
            else (
                float(config["direct_baseline_time_limit"])
                if config.get("direct_baseline_time_limit") is not None
                else None
            )
        ),
        restricted_rmp_enabled=bool(config.get("restricted_rmp_enabled", True)) and not args.no_restricted_rmp,
        direct_pricing_enabled=bool(config.get("direct_pricing_enabled", True)) and not args.no_direct_pricing,
        direct_pricing_max_tasks=int(
            args.direct_pricing_max_tasks if args.direct_pricing_max_tasks is not None else config.get("direct_pricing_max_tasks", 5)
        ),
        direct_pricing_cg_rounds=int(
            args.direct_pricing_cg_rounds if args.direct_pricing_cg_rounds is not None else config.get("direct_pricing_cg_rounds", 1)
        ),
        time_limit_sec=float(time_limit) if time_limit is not None else None,
    )
    print(
        "ran {run_count} instances; statuses={status_counts}; exact={exact_status_counts}; csv={results_csv}".format(
            **summary
        )
    )
    return 0


def _root_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def _parse_scales(value) -> list[int] | None:
    if value is None or value == "":
        return None
    if isinstance(value, (list, tuple)):
        return [int(item) for item in value]
    return [int(item.strip()) for item in str(value).split(",") if item.strip()]


if __name__ == "__main__":
    raise SystemExit(main())

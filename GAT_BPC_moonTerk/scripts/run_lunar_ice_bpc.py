#!/usr/bin/env python3
"""Run the current exact-safe lunar-ice solver scaffold."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.io.config import apply_overrides, load_config
from lunar_ice_bpc.runners.solve import solve_reference


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    parser.add_argument("--instance", default=None)
    parser.add_argument("--instances", nargs="*", default=None)
    parser.add_argument("--solution", default=None)
    parser.add_argument("--solution-dir", default="runs/solutions")
    parser.add_argument("--canonical-dp-max-tasks", type=int, default=None)
    parser.add_argument("--direct-baseline-max-tasks", type=int, default=None)
    parser.add_argument("--direct-baseline-time-limit", type=float, default=None)
    parser.add_argument("--no-restricted-rmp", action="store_true")
    parser.add_argument("--no-direct-pricing", action="store_true")
    parser.add_argument("--direct-pricing-max-tasks", type=int, default=None)
    parser.add_argument("--direct-pricing-cg-rounds", type=int, default=None)
    parser.add_argument("--set", dest="overrides", action="append", default=[])
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    config = apply_overrides(load_config(ROOT / args.config), args.overrides) if args.config else apply_overrides({}, args.overrides)
    instance_values = []
    if args.instance:
        instance_values.append(args.instance)
    if args.instances:
        instance_values.extend(args.instances)
    instance_values.extend(str(item) for item in config.get("instances", []) or [])
    if not instance_values:
        parser.error("provide --instance, --instances, or a config with instances")

    canonical_dp_max_tasks = int(
        args.canonical_dp_max_tasks
        if args.canonical_dp_max_tasks is not None
        else config.get("canonical_dp_max_tasks", config.get("exact_max_tasks", 10))
    )
    direct_baseline_max_tasks = int(
        args.direct_baseline_max_tasks
        if args.direct_baseline_max_tasks is not None
        else config.get("direct_baseline_max_tasks", 10)
    )
    direct_baseline_time_limit = (
        float(args.direct_baseline_time_limit)
        if args.direct_baseline_time_limit is not None
        else (
            float(config["direct_baseline_time_limit"])
            if config.get("direct_baseline_time_limit") is not None
            else None
        )
    )
    restricted_rmp_enabled = bool(config.get("restricted_rmp_enabled", True)) and not args.no_restricted_rmp
    direct_pricing_enabled = bool(config.get("direct_pricing_enabled", True)) and not args.no_direct_pricing
    direct_pricing_max_tasks = int(
        args.direct_pricing_max_tasks
        if args.direct_pricing_max_tasks is not None
        else config.get("direct_pricing_max_tasks", 5)
    )
    direct_pricing_cg_rounds = int(
        args.direct_pricing_cg_rounds
        if args.direct_pricing_cg_rounds is not None
        else config.get("direct_pricing_cg_rounds", 1)
    )
    solution_dir = Path(args.solution_dir or config.get("solution_dir", "runs/solutions"))
    if not solution_dir.is_absolute():
        solution_dir = ROOT / solution_dir
    failed = 0
    for raw_instance in instance_values:
        instance_path = Path(raw_instance)
        if not instance_path.is_absolute():
            instance_dir = Path(str(config.get("instance_dir", ".")))
            if not instance_dir.is_absolute():
                instance_dir = ROOT / instance_dir
            candidate = instance_dir / instance_path
            instance_path = candidate if candidate.exists() else ROOT / instance_path
        if args.solution and len(instance_values) == 1:
            solution_path = Path(args.solution)
            if not solution_path.is_absolute():
                solution_path = ROOT / solution_path
        else:
            solution_path = solution_dir / instance_path.parent.name / f"{instance_path.stem}_solution.json"
        result = solve_reference(
            instance_path,
            solution_path,
            canonical_dp_max_tasks=canonical_dp_max_tasks,
            direct_baseline_max_tasks=direct_baseline_max_tasks,
            direct_baseline_time_limit_sec=direct_baseline_time_limit,
            restricted_rmp_enabled=restricted_rmp_enabled,
            direct_pricing_enabled=direct_pricing_enabled,
            direct_pricing_max_tasks=direct_pricing_max_tasks,
            direct_pricing_cg_rounds=direct_pricing_cg_rounds,
        )
        if not args.quiet:
            print(f"{result['status']} exact_status={result['exact_status']} -> {solution_path}")
        if result["status"] == "INVALID_INSTANCE":
            failed += 1
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

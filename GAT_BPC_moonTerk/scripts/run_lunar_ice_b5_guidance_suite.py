#!/usr/bin/env python3
"""Run the B5 exact-safe guidance do-no-harm suite."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.io.config import apply_overrides, load_config
from lunar_ice_bpc.runners.gat_b5_suite import run_b5_guidance_suite, validate_b5_suite_config


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    parser.add_argument("--manifest", default=None)
    parser.add_argument("--instances", nargs="*", default=None)
    parser.add_argument("--scales", default=None)
    parser.add_argument("--output-json", default=None)
    parser.add_argument("--max-direct-tasks", type=int, default=None)
    parser.add_argument("--max-rounds", type=int, default=None)
    parser.add_argument("--negative-eps", type=float, default=None)
    parser.add_argument("--set", dest="overrides", action="append", default=[])
    args = parser.parse_args()
    config = apply_overrides(load_config(ROOT / args.config), args.overrides) if args.config else apply_overrides({}, args.overrides)
    issues = validate_b5_suite_config(config)
    if issues:
        parser.error("; ".join(issues))
    manifest_value = args.manifest if args.manifest is not None else config.get("manifest", config.get("manifest_path"))
    instances = args.instances if args.instances is not None else (config.get("instances") or None)
    if manifest_value is None and instances is None:
        manifest_value = "data/manifests/lunar_ice_sp50_real_benchmark_manifest.json"
    suite = run_b5_guidance_suite(
        project_root=ROOT,
        instances=[str(item) for item in instances] if instances else None,
        manifest_path=manifest_value,
        scales=_parse_scales(args.scales if args.scales is not None else config.get("scales")),
        output_json=args.output_json or config.get("output_json", "runs/logs/b5_guidance_suite_summary.json"),
        guidance_mode=str(config.get("guidance_mode", "shadow_only")),
        enabled_ordering_modes=_parse_modes(config.get("enabled_ordering_modes")),
        max_direct_tasks=int(args.max_direct_tasks if args.max_direct_tasks is not None else config.get("max_direct_tasks", 5)),
        max_rounds=int(args.max_rounds if args.max_rounds is not None else config.get("max_rounds", 8)),
        negative_eps=float(args.negative_eps if args.negative_eps is not None else config.get("negative_eps", 1.0e-6)),
        diagnostic_policy_version=str(config.get("diagnostic_policy_version", "deterministic_shadow_policy_v1")),
    )
    print(
        "ran {row_count} B5 guidance rows; do_no_harm={suite_do_no_harm_pass}; "
        "performance_success_count={suite_performance_success_count}; output={output}".format(
            row_count=suite["row_count"],
            suite_do_no_harm_pass=suite["suite_do_no_harm_pass"],
            suite_performance_success_count=suite["suite_performance_success_count"],
            output=suite["runner"].get("output_json", ""),
        )
    )
    return 0


def _parse_scales(value) -> list[int] | None:
    if value is None or value == "":
        return None
    if isinstance(value, (list, tuple)):
        return [int(item) for item in value]
    return [int(item.strip()) for item in str(value).split(",") if item.strip()]


def _parse_modes(value) -> list[str] | None:
    if value is None or value == "":
        return None
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    return [item.strip() for item in str(value).split(",") if item.strip()]


if __name__ == "__main__":
    raise SystemExit(main())

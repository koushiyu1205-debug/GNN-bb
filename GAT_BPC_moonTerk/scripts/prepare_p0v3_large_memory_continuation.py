#!/usr/bin/env python3
"""Prepare or launch the scale-50/100 continuation on a large-memory host.

This entry point deliberately refuses the current 15.5 GiB WSL environment.
It preserves the frozen P0 V3 solver and the completed scale-5--30 rows, while
changing only the resource envelope used by the scale-50/100 host backend.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Mapping

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "runs" / "p0v3_six_scale_full120_baseline_20260727"
DEFAULT_CONFIG = ROOT / "configs" / "native_live_sri_p0_full120_v1.yaml"
RUNNER = ROOT / "scripts" / "run_p0v3_six_scale_full120_baseline.py"
FROZEN_NATIVE = (
    ROOT
    / "runs"
    / "frozen_native_live_sri_p0_no_task_wait_baseline_v3_20260725"
    / "native"
)
FORMAL_LARGE_SCALES = (50, 100)
FORMAL_SMALL_SCALES = (5, 10, 20, 30)
EXPECTED_PER_SCALE = 20


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source-config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--minimum-total-memory-gb", type=float, default=360.0)
    parser.add_argument(
        "--recommended-total-memory-gb", type=float, default=380.0
    )
    parser.add_argument("--system-reserve-gb", type=float, default=48.0)
    parser.add_argument("--native-cap-fraction", type=float, default=0.875)
    parser.add_argument("--heartbeat-interval-sec", type=float, default=30.0)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    output = args.output_dir.resolve()
    source_config = args.source_config.resolve()
    require_inside_workspace(output)
    require_inside_workspace(source_config)
    output.mkdir(parents=True, exist_ok=True)

    total_memory_gb = linux_total_memory_gb()
    progress_issues, progress = validate_existing_progress(output)
    resource_plan = derive_resource_plan(
        total_memory_gb=total_memory_gb,
        minimum_total_memory_gb=float(args.minimum_total_memory_gb),
        recommended_total_memory_gb=float(args.recommended_total_memory_gb),
        system_reserve_gb=float(args.system_reserve_gb),
        native_cap_fraction=float(args.native_cap_fraction),
    )
    issues = list(progress_issues)
    if not resource_plan["host_qualified"]:
        issues.append("host_total_memory_below_required_minimum")
    if not source_config.is_file():
        issues.append("source_config_missing")
    frozen_modules = tuple(FROZEN_NATIVE.glob("lunar_spprc_native*.so"))
    if len(frozen_modules) != 1:
        issues.append("frozen_native_module_count_not_one")

    report_path = output / "large_memory_continuation_preflight.json"
    preflight = {
        "schema_version": (
            "lunar_ice_bpc.p0v3_large_memory_continuation.v1.preflight"
        ),
        "created_at_utc": utc_now(),
        "status": "FAILED" if issues else "PASS",
        "issues": sorted(set(issues)),
        "output_dir": str(output),
        "source_config": str(source_config),
        "frozen_native_dir": str(FROZEN_NATIVE),
        "completed_progress": progress,
        "resource_plan": resource_plan,
        "solver_change": False,
        "resource_envelope_change_only": True,
        "scale_5_30_rows_reused": True,
        "scale_50_100_legal_incomplete_rows_retried": True,
    }
    atomic_write_json(report_path, preflight)
    if issues:
        print(json.dumps(preflight, ensure_ascii=False, indent=2))
        return 2

    runtime_config_path = (
        output / "native_live_sri_p0_full120_large_memory_runtime.yaml"
    )
    source_payload = yaml.safe_load(
        source_config.read_text(encoding="utf-8")
    )
    runtime_payload = build_runtime_config(
        source_payload,
        native_memory_limit_gb=float(
            resource_plan["native_cooperative_memory_limit_gb"]
        ),
        resource_plan=resource_plan,
    )
    runtime_config_path.write_text(
        yaml.safe_dump(runtime_payload, sort_keys=False),
        encoding="utf-8",
    )

    command = continuation_command(
        output=output,
        runtime_config_path=runtime_config_path,
        resource_plan=resource_plan,
        heartbeat_interval_sec=float(args.heartbeat_interval_sec),
    )
    launch_manifest = {
        "schema_version": (
            "lunar_ice_bpc.p0v3_large_memory_continuation.v1.launch"
        ),
        "created_at_utc": utc_now(),
        "preflight": str(report_path),
        "runtime_config": str(runtime_config_path),
        "command": command,
        "environment": {
            "PYTHONPATH": os.pathsep.join(
                (str(ROOT / "src"), str(FROZEN_NATIVE))
            )
        },
    }
    atomic_write_json(
        output / "large_memory_continuation_launch.json",
        launch_manifest,
    )
    print(json.dumps(launch_manifest, ensure_ascii=False, indent=2))
    if not args.execute:
        return 0

    environment = dict(os.environ)
    environment.update(launch_manifest["environment"])
    return subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        check=False,
    ).returncode


def derive_resource_plan(
    *,
    total_memory_gb: float,
    minimum_total_memory_gb: float,
    recommended_total_memory_gb: float,
    system_reserve_gb: float,
    native_cap_fraction: float,
) -> dict:
    if minimum_total_memory_gb <= 0.0:
        raise ValueError("minimum_total_memory_gb must be positive")
    if recommended_total_memory_gb < minimum_total_memory_gb:
        raise ValueError(
            "recommended_total_memory_gb must be at least the minimum"
        )
    if system_reserve_gb < 16.0:
        raise ValueError("system_reserve_gb must be at least 16")
    if not 0.5 <= native_cap_fraction < 1.0:
        raise ValueError("native_cap_fraction must be in [0.5, 1.0)")

    # Native host watchdog adds at most 2 GiB and the outer launcher adds
    # another 2 GiB.  Reserve those four GiB before assigning the exact label
    # frontier.  Floor to whole GiB so all three independently calculated
    # limits remain deterministic.
    native_limit = math.floor(
        min(
            total_memory_gb * native_cap_fraction,
            total_memory_gb - system_reserve_gb - 4.0,
        )
    )
    native_limit = max(0, native_limit)
    host_watchdog_limit = native_limit + 2.0
    outer_process_tree_limit = host_watchdog_limit + 2.0
    minimum_start_available = outer_process_tree_limit + 8.0
    host_qualified = bool(
        total_memory_gb >= minimum_total_memory_gb
        and native_limit >= 64.0
        and minimum_start_available <= total_memory_gb
    )
    return {
        "total_memory_gb": round(total_memory_gb, 6),
        "minimum_required_total_memory_gb": minimum_total_memory_gb,
        "recommended_total_memory_gb": recommended_total_memory_gb,
        "recommendation_met": total_memory_gb >= recommended_total_memory_gb,
        "host_qualified": host_qualified,
        "system_reserve_gb": system_reserve_gb,
        "native_cap_fraction": native_cap_fraction,
        "native_cooperative_memory_limit_gb": float(native_limit),
        "host_emergency_watchdog_limit_gb": host_watchdog_limit,
        "outer_process_tree_emergency_cap_gb": outer_process_tree_limit,
        "minimum_start_available_memory_gb": minimum_start_available,
        "minimum_runtime_available_memory_gb": 16.0,
        "row_time_limit_sec": 3600.0,
    }


def build_runtime_config(
    source: Mapping,
    *,
    native_memory_limit_gb: float,
    resource_plan: Mapping,
) -> dict:
    payload = deepcopy(dict(source))
    profiles = payload.get("profiles")
    if not isinstance(profiles, dict):
        raise ValueError("source config profiles must be a mapping")
    for scale in FORMAL_LARGE_SCALES:
        profile = profiles.get(str(scale))
        if not isinstance(profile, dict):
            raise ValueError(f"source config is missing scale {scale}")
        profile["memory_limit_gb"] = native_memory_limit_gb
        profile["row_time_limit_sec"] = 3600
    payload["large_scale_execution_class"] = (
        "qualified_time_limit_benchmark_v1"
    )
    payload["large_scale_resource_plan"] = dict(resource_plan)
    return payload


def continuation_command(
    *,
    output: Path,
    runtime_config_path: Path,
    resource_plan: Mapping,
    heartbeat_interval_sec: float,
) -> list[str]:
    return [
        sys.executable,
        str(RUNNER),
        "--config",
        str(runtime_config_path),
        "--output-dir",
        str(output),
        "--heartbeat-interval-sec",
        str(heartbeat_interval_sec),
        "--monitor-memory-cap-gb",
        str(resource_plan["outer_process_tree_emergency_cap_gb"]),
        "--min-available-memory-gb",
        str(resource_plan["minimum_runtime_available_memory_gb"]),
        "--large-scale-min-start-available-memory-gb",
        str(resource_plan["minimum_start_available_memory_gb"]),
        "--large-scale-memory-recovery-timeout-sec",
        "1800",
        "--recover-completed-slots",
        "--retry-unsafe-recovered-slots",
        "--retry-resource-censored-recovered-slots",
        "--retry-memory-censored-recovered-slots",
    ]


def validate_existing_progress(output: Path) -> tuple[list[str], dict]:
    path = output / "full120_rows.json"
    if not path.is_file():
        return ["existing_full120_rows_missing"], {}
    rows = json.loads(path.read_text(encoding="utf-8"))
    issues: list[str] = []
    exact_by_scale: dict[int, int] = {}
    terminal_by_scale: dict[int, dict[str, int]] = {}
    for row in rows:
        scale = int(row.get("scale") or 0)
        terminal = str(row.get("terminal_class") or "")
        terminal_by_scale.setdefault(scale, {})
        terminal_by_scale[scale][terminal] = (
            terminal_by_scale[scale].get(terminal, 0) + 1
        )
        if terminal == "EXACT":
            exact_by_scale[scale] = exact_by_scale.get(scale, 0) + 1
    for scale in FORMAL_SMALL_SCALES:
        if exact_by_scale.get(scale, 0) != EXPECTED_PER_SCALE:
            issues.append(f"scale_{scale}_exact_count_not_20")
        nonexact = sum(
            count
            for terminal, count in terminal_by_scale.get(scale, {}).items()
            if terminal != "EXACT"
        )
        if nonexact:
            issues.append(f"scale_{scale}_contains_nonexact_rows")
    for scale in FORMAL_LARGE_SCALES:
        unsafe = terminal_by_scale.get(scale, {}).get(
            "UNSAFE_FAILURE", 0
        )
        if unsafe:
            issues.append(f"scale_{scale}_contains_unsafe_rows")
    return sorted(set(issues)), {
        "row_count": len(rows),
        "exact_by_scale": {
            str(scale): exact_by_scale.get(scale, 0)
            for scale in (*FORMAL_SMALL_SCALES, *FORMAL_LARGE_SCALES)
        },
        "terminal_by_scale": {
            str(scale): terminal_by_scale.get(scale, {})
            for scale in (*FORMAL_SMALL_SCALES, *FORMAL_LARGE_SCALES)
        },
    }


def linux_total_memory_gb() -> float:
    for line in Path("/proc/meminfo").read_text(
        encoding="utf-8"
    ).splitlines():
        if line.startswith("MemTotal:"):
            return float(line.split()[1]) * 1024.0 / (1024.0**3)
    raise RuntimeError("MemTotal is missing from /proc/meminfo")


def require_inside_workspace(path: Path) -> None:
    try:
        path.relative_to(ROOT)
    except ValueError as exc:
        raise SystemExit(f"path must be inside workspace: {path}") from exc


def atomic_write_json(path: Path, payload: Mapping) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run the active P0 V3 baseline on all formal scale 5--100 instances.

The frozen P0 V3 native extension is used deliberately.  Later GAT diagnostic
work enlarged the development native label state, so using ``build/`` would
silently include non-baseline memory and timing overhead even when guidance is
disabled.

Every instance runs in a fresh process.  Scales 50/100 are always serial and
resource-censored outcomes remain legal incomplete results; they can never be
reported as exact certificates.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
from time import perf_counter, sleep
from typing import Iterable, Mapping

import yaml


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
FREEZE_DIR = (
    ROOT
    / "runs"
    / "frozen_native_live_sri_p0_no_task_wait_baseline_v3_20260725"
)
FROZEN_NATIVE = FREEZE_DIR / "native"
for path in (str(SRC), str(FROZEN_NATIVE)):
    if path not in sys.path:
        sys.path.insert(0, path)

from run_live_sri_paired_promotion import (
    atomic_write_json,
    config_profile,
    discover_instances,
    effective_memory_limit_gb,
    next_attempt_dir,
    read_run_result,
    run_monitored,
    sha256_file,
    stable_payload_hash,
)

from lunar_ice_bpc.domain.scenario import SERVICE_TIMING_POLICY_ID
from lunar_ice_bpc.exact.bpc.cuts.live_sri import LiveSriPolicy
from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import (
    host_memory_watchdog_limit_gb,
)
from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (
    spprc_engine_build_hash,
)
SCHEMA_VERSION = "lunar_ice_bpc.p0v3_six_scale_full120_baseline.v1"
BASELINE_ID = "FROZEN_NATIVE_LIVE_SRI_P0_NO_TASK_WAIT_BASELINE_V3"
FORMAL_SCALES = (5, 10, 20, 30, 50, 100)
SMALL_EXACT_SCALES = frozenset({5, 10, 20, 30})
LARGE_SHADOW_SCALES = frozenset({50, 100})
EXPECTED_PER_SCALE = 20
ACCEPTANCE_RUNNER = ROOT / "scripts" / "run_lunar_ice_native_spprc_acceptance.py"
REGISTRY_PATH = ROOT / "runs" / "native_bpc_baseline_registry.json"
FREEZE_MANIFEST_PATH = FREEZE_DIR / "baseline_freeze_manifest.json"
FREEZE_CANDIDATE_PATH = FREEZE_DIR / "candidate_preflight_snapshot.json"
FROZEN_CONFIG_PATH = FREEZE_DIR / "frozen_config.yaml"
DEFAULT_CONFIG_PATH = ROOT / "configs" / "native_live_sri_p0_full120_v1.yaml"
FROZEN_ROWS_PATH = FREEZE_DIR / "performance" / "full80_rows_snapshot.json"
FORMAL_INSTANCE_MANIFEST_PATH = (
    ROOT / "data" / "manifests" / "lunar_ice_sp50_real_benchmark_manifest.json"
)

EXPERIMENT_ENV_PREFIXES = (
    "LUNAR_ICE_GAT_",
)
EXPERIMENT_ENV_KEYS = frozenset(
    {
        "LUNAR_ICE_ADAPTIVE_TAIL_HARVEST_MAX",
        "LUNAR_ICE_ADAPTIVE_TAIL_HARVEST_TRIGGER_SEC",
        "LUNAR_ICE_DEVELOPMENT_ORACLE_TASK_PRIORITY_JSON",
        "LUNAR_ICE_DUAL_CENTER_TRAJECTORY_COLLECTION",
        "LUNAR_ICE_EXPERIMENTAL_PROOF_QUEUE_POLICY",
        "LUNAR_ICE_PROOF_QUEUE_POTENTIAL_TRACE",
    }
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--scales", nargs="+", type=int, default=list(FORMAL_SCALES)
    )
    parser.add_argument("--instance", action="append", default=[])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--heartbeat-interval-sec", type=float, default=30.0)
    parser.add_argument("--launcher-timeout-grace-sec", type=float, default=120.0)
    parser.add_argument("--monitor-memory-cap-gb", type=float, default=12.0)
    parser.add_argument("--min-available-memory-gb", type=float, default=1.0)
    parser.add_argument(
        "--large-scale-min-start-available-memory-gb",
        type=float,
        default=12.0,
    )
    parser.add_argument(
        "--large-scale-memory-recovery-timeout-sec",
        type=float,
        default=300.0,
    )
    parser.add_argument("--recover-completed-slots", action="store_true")
    parser.add_argument(
        "--retry-unsafe-recovered-slots",
        action="store_true",
    )
    parser.add_argument(
        "--retry-resource-censored-recovered-slots",
        action="store_true",
    )
    parser.add_argument(
        "--retry-legal-incomplete-recovered-slots",
        action="store_true",
        help=(
            "Discard recovered LEGAL_INCOMPLETE rows and rerun those slots. "
            "This is required when moving an 8 GiB diagnostic run to a "
            "qualified large-memory host."
        ),
    )
    parser.add_argument(
        "--retry-memory-censored-recovered-slots",
        action="store_true",
        help=(
            "Discard recovered MEMORY_CENSORED_INCOMPLETE rows and rerun "
            "those slots with the current resource envelope."
        ),
    )
    parser.add_argument("--keep-going-on-unsafe-failure", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    scales = tuple(int(value) for value in args.scales)
    if len(set(scales)) != len(scales):
        raise SystemExit("duplicate scale")
    if any(scale not in FORMAL_SCALES for scale in scales):
        raise SystemExit(f"scales must be a subset of {FORMAL_SCALES}")

    config_path = args.config.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    previous_preflight_path = output / "full120_preflight.json"
    previous_preflight = (
        read_json(previous_preflight_path)
        if previous_preflight_path.is_file()
        else {}
    )
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if str(config.get("live_sri_policy")) != "P0":
        raise SystemExit("baseline config must select live_sri_policy=P0")
    if float(args.monitor_memory_cap_gb) <= 0.0:
        raise SystemExit("--monitor-memory-cap-gb must be positive")
    for scale in scales:
        if scale not in LARGE_SHADOW_SCALES:
            continue
        profile = config_profile(config_path, scale)
        native_limit = effective_memory_limit_gb(
            float(profile["memory_limit_gb"])
        )
        required_outer_limit = (
            host_memory_watchdog_limit_gb(native_limit) + 1.0
        )
        if float(args.monitor_memory_cap_gb) < required_outer_limit:
            raise SystemExit(
                "--monitor-memory-cap-gb is too low for graceful Native "
                f"memory limiting at scale {scale}: need at least "
                f"{required_outer_limit:.3f} GiB for native={native_limit:.3f} "
                "GiB plus the host watchdog and launcher"
            )

    removed_env = sanitize_experiment_environment()
    required_pythonpath = os.pathsep.join((str(SRC), str(FROZEN_NATIVE)))
    os.environ["PYTHONPATH"] = required_pythonpath
    import lunar_spprc_native

    selected = discover_instances(scales, args.instance, limit=args.limit)
    schedule = build_schedule(
        selected, output=output, config_path=config_path
    )
    formal_full120 = bool(
        not args.limit
        and scales == FORMAL_SCALES
        and all(
            len(selected.get(scale, ())) == EXPECTED_PER_SCALE
            for scale in FORMAL_SCALES
        )
    )
    freeze_manifest = read_json(FREEZE_MANIFEST_PATH)
    frozen_candidate = read_json(FREEZE_CANDIDATE_PATH)
    registry = read_json(REGISTRY_PATH)
    preflight_issues = validate_preflight(
        config_path=config_path,
        config=config,
        selected=selected,
        freeze_manifest=freeze_manifest,
        frozen_candidate=frozen_candidate,
        registry=registry,
        native_build_info=dict(lunar_spprc_native.build_info()),
    )
    if preflight_issues:
        atomic_write_json(
            output / "full120_preflight.json",
            {
                "schema_version": f"{SCHEMA_VERSION}.preflight",
                "created_at_utc": utc_now(),
                "baseline_id": BASELINE_ID,
                "status": "FAILED",
                "issues": preflight_issues,
            },
        )
        raise SystemExit("preflight failed: " + ",".join(preflight_issues))

    execution_bundle = execution_bundle_rows(config_path)
    execution_bundle_hash = stable_payload_hash(execution_bundle)
    engine_hashes = {
        backend: spprc_engine_build_hash(backend)
        for backend in ("native_rcspp_inprocess", "native_rcspp_host")
    }
    frozen_source_drift = frozen_source_mismatches(frozen_candidate)
    preflight = {
        "schema_version": f"{SCHEMA_VERSION}.preflight",
        "created_at_utc": utc_now(),
        "baseline_id": BASELINE_ID,
        "status": "PASS",
        "formal_full120": formal_full120,
        "selected_instance_count": len(schedule),
        "scales": list(scales),
        "instances_per_scale": {
            str(scale): len(selected.get(scale, ())) for scale in scales
        },
        "service_timing_policy_id": SERVICE_TIMING_POLICY_ID,
        "config": str(config_path),
        "config_sha256": sha256_file(config_path),
        "frozen_config_5_30_profiles_equal": True,
        "frozen_native_path": str(next(FROZEN_NATIVE.glob("lunar_spprc_native*.so"))),
        "frozen_native_sha256": freeze_manifest["native_binary_snapshot"]["sha256"],
        "frozen_native_build_info": dict(lunar_spprc_native.build_info()),
        "runtime_engine_hashes": engine_hashes,
        "runtime_engine_hash_note": (
            "Engine hashes include the current Python/native source shell. "
            "Frozen .so identity is bound separately by SHA-256."
        ),
        "frozen_source_bundle_mismatch_count": len(frozen_source_drift),
        "frozen_source_bundle_mismatches": frozen_source_drift,
        "source_shell_classification": (
            "frozen_native_with_current_baseline_compatible_python_shell"
            if frozen_source_drift
            else "fully_frozen_source_and_native"
        ),
        "guidance_disabled": True,
        "proof_queue_policy": "Q0",
        "trace_disabled": True,
        "removed_experiment_environment": removed_env,
        "strict_cold_start": True,
        "fresh_python_native_runtime_per_slot": True,
        "solver_resume": False,
        "serial_execution": True,
        "large_scale_resource_policy": {
            "scales": sorted(LARGE_SHADOW_SCALES),
            "host_backend": True,
            "native_cooperative_memory_limit_gb": {
                str(scale): effective_memory_limit_gb(
                    float(config_profile(config_path, scale)["memory_limit_gb"])
                )
                for scale in sorted(LARGE_SHADOW_SCALES)
            },
            "native_host_emergency_watchdog_limit_gb": {
                str(scale): host_memory_watchdog_limit_gb(
                    effective_memory_limit_gb(
                        float(
                            config_profile(config_path, scale)[
                                "memory_limit_gb"
                            ]
                        )
                    )
                )
                for scale in sorted(LARGE_SHADOW_SCALES)
            },
            "outer_process_tree_emergency_cap_gb": float(
                args.monitor_memory_cap_gb
            ),
            "min_start_available_memory_gb": float(
                args.large_scale_min_start_available_memory_gb
            ),
            "memory_recovery_timeout_sec": float(
                args.large_scale_memory_recovery_timeout_sec
            ),
            "legal_incomplete_is_not_certificate": True,
            "expected_normal_memory_limit_path": (
                "native_MEMORY_LIMIT_return_without_SIGTERM"
            ),
        },
        "execution_bundle_hash": execution_bundle_hash,
        "execution_bundle": execution_bundle,
        "recovered_previous_execution_bundle_hash": str(
            previous_preflight.get("execution_bundle_hash") or ""
        ),
    }
    atomic_write_json(output / "full120_preflight.json", preflight)
    atomic_write_json(
        output / "full120_schedule.json",
        {
            "schema_version": f"{SCHEMA_VERSION}.schedule",
            "created_at_utc": utc_now(),
            "slots": schedule,
        },
    )

    rows_path = output / "full120_rows.json"
    rows: list[dict] = []
    if rows_path.exists():
        if not args.recover_completed_slots:
            raise SystemExit(
                "full120_rows.json exists; use a new output or "
                "--recover-completed-slots"
            )
        rows = list(read_json(rows_path))
        previous_bundle_hash = str(
            previous_preflight.get("execution_bundle_hash") or ""
        )
        for row in rows:
            row.setdefault(
                "execution_bundle_hash",
                previous_bundle_hash or "legacy_unbound",
            )
            row.setdefault("requested_live_sri_policy", "P0")
            if row.get("run_dir"):
                row.update(
                    large_scale_incomplete_detail(
                        Path(str(row["run_dir"])),
                        int(row.get("scale") or 0),
                    )
                )
            issues = safety_issues(row)
            row["safety_issues"] = issues
            row["safety_pass"] = not issues
            row["terminal_class"] = terminal_class(row)
        rows = filter_recovered_rows_for_retry(
            rows,
            retry_unsafe=bool(args.retry_unsafe_recovered_slots),
            retry_resource_censored=bool(
                args.retry_resource_censored_recovered_slots
            ),
            retry_legal_incomplete=bool(
                args.retry_legal_incomplete_recovered_slots
            ),
            retry_memory_censored=bool(
                args.retry_memory_censored_recovered_slots
            ),
        )
        if (
            args.retry_unsafe_recovered_slots
            or args.retry_resource_censored_recovered_slots
            or args.retry_legal_incomplete_recovered_slots
            or args.retry_memory_censored_recovered_slots
        ):
            write_rows(rows_path, output / "full120_rows.csv", rows)
    completed = recovered_rows(rows, schedule)
    reference_objectives = frozen_reference_objectives()
    stopped_reason = ""
    started = perf_counter()

    for spec in schedule:
        slot_id = str(spec["slot_id"])
        if slot_id in completed:
            continue
        if stable_payload_hash(execution_bundle_rows(config_path)) != execution_bundle_hash:
            stopped_reason = "EXECUTION_BUNDLE_DRIFT"
            break

        row = dict(spec)
        row["execution_bundle_hash"] = execution_bundle_hash
        if int(spec["scale"]) in LARGE_SHADOW_SCALES:
            recovery = wait_for_large_scale_memory(
                min_available_gb=float(
                    args.large_scale_min_start_available_memory_gb
                ),
                timeout_sec=max(
                    0.0,
                    float(args.large_scale_memory_recovery_timeout_sec),
                ),
            )
            row.update(recovery)
            if not recovery["memory_recovery_pass"]:
                stopped_reason = (
                    "LARGE_SCALE_MEMORY_RECOVERY_TIMEOUT:" + slot_id
                )
                break
        row.update(
            {
                "baseline_id": BASELINE_ID,
                "config": str(config_path),
                "config_sha256": sha256_file(config_path),
                "frozen_native_sha256": preflight["frozen_native_sha256"],
                "expected_engine_hash": engine_hashes[
                    str(spec["backend_id"])
                ],
                "expected_p0_policy_hash": LiveSriPolicy.named("P0").policy_hash,
                "requested_live_sri_policy": "P0",
                "reference_frozen_objective": reference_objectives.get(
                    (int(spec["scale"]), str(spec["instance_key"]))
                ),
            }
        )
        print(
            f"[START] {slot_id} "
            f"completed={len(completed)}/{len(schedule)} "
            f"backend={spec['backend_id']}",
            flush=True,
        )
        if args.dry_run:
            row.update(
                {
                    "status": "DRY_RUN",
                    "returncode": 0,
                    "exact": False,
                    "safety_pass": True,
                    "terminal_class": "DRY_RUN",
                    "completed_at_utc": utc_now(),
                }
            )
        else:
            run_dir, attempt = next_attempt_dir(Path(spec["slot_dir"]))
            run_dir.mkdir(parents=True, exist_ok=False)
            row["run_dir"] = str(run_dir)
            row["attempt_number"] = attempt
            command = [
                sys.executable,
                str(ACCEPTANCE_RUNNER),
                "--config",
                str(config_path),
                "--scales",
                str(spec["scale"]),
                "--instance",
                str(spec["instance"]),
                "--output-dir",
                str(run_dir),
                "--no-resume",
            ]
            row["command"] = command
            profile = config_profile(config_path, int(spec["scale"]))
            native_internal_memory_limit = effective_memory_limit_gb(
                float(profile["memory_limit_gb"])
            )
            host_watchdog_limit = (
                host_memory_watchdog_limit_gb(native_internal_memory_limit)
                if str(spec["backend_id"]) == "native_rcspp_host"
                else native_internal_memory_limit
            )
            # This final process-tree limit protects the workstation if both
            # cooperative native stopping and the host emergency watchdog
            # fail.  It must not race either inner layer during normal use.
            monitor_limit = min(
                host_watchdog_limit + (
                    2.0
                    if str(spec["backend_id"]) == "native_rcspp_host"
                    else 0.0
                ),
                max(0.5, float(args.monitor_memory_cap_gb)),
            )
            row["native_internal_memory_limit_gb"] = (
                native_internal_memory_limit
            )
            row["native_host_watchdog_memory_limit_gb"] = (
                host_watchdog_limit
            )
            row["monitor_memory_limit_gb"] = monitor_limit
            run_started = perf_counter()
            monitor = run_monitored(
                command,
                cwd=ROOT,
                run_dir=run_dir,
                slot_id=slot_id,
                heartbeat_csv=output / "resource_heartbeat.csv",
                heartbeat_interval_sec=max(
                    1.0, float(args.heartbeat_interval_sec)
                ),
                timeout_sec=float(profile["row_time_limit_sec"])
                + max(0.0, float(args.launcher_timeout_grace_sec)),
                effective_memory_limit_gb=monitor_limit,
                min_available_memory_gb=max(
                    0.0, float(args.min_available_memory_gb)
                ),
                low_memory_consecutive_samples=2,
            )
            row.update(
                read_run_result(
                    run_dir,
                    scale=int(spec["scale"]),
                    returncode=int(monitor["returncode"]),
                )
            )
            row.update(monitor)
            row["acceptance_summary_present"] = (
                run_dir / "native_spprc_acceptance_summary.json"
            ).is_file()
            row["launcher_wall_time_sec"] = round(
                perf_counter() - run_started, 6
            )
            tree = read_tree(run_dir, int(spec["scale"]))
            row["tree_result_present"] = bool(tree)
            row.update(
                large_scale_incomplete_detail(
                    run_dir,
                    int(spec["scale"]),
                )
            )
            row.update(
                {
                    "algorithm_status": tree.get("algorithm_status"),
                    "exact_status": tree.get("exact_status"),
                    "observed_instance_content_hash": str(
                        tree.get("instance_content_hash") or ""
                    ),
                    "observed_service_timing_policy_id": str(
                        tree.get("service_timing_policy_id") or ""
                    ),
                }
            )
            if row["observed_instance_content_hash"]:
                row["instance_content_hash"] = row[
                    "observed_instance_content_hash"
                ]
            issues = safety_issues(row)
            row["safety_issues"] = issues
            row["safety_pass"] = not issues
            row["objective_match_frozen"] = objective_matches_reference(row)
            row["terminal_class"] = terminal_class(row)
            row["completed_at_utc"] = utc_now()

        rows.append(row)
        completed[slot_id] = row
        write_rows(rows_path, output / "full120_rows.csv", rows)
        atomic_write_json(
            output / "full120_progress.json",
            {
                "schema_version": f"{SCHEMA_VERSION}.progress",
                "updated_at_utc": utc_now(),
                "expected_slot_count": len(schedule),
                "completed_slot_count": len(completed),
                "last_slot_id": slot_id,
                "last_status": row.get("status"),
                "last_terminal_class": row.get("terminal_class"),
                "last_exact": row.get("exact"),
                "last_safety_pass": row.get("safety_pass"),
                "solver_resume": False,
            },
        )
        print(
            f"[DONE] {slot_id} class={row.get('terminal_class')} "
            f"status={row.get('status')} exact={row.get('exact')} "
            f"sec={row.get('cold_start_total_sec')} "
            f"rss={row.get('peak_process_tree_rss_gb')} "
            f"completed={len(completed)}/{len(schedule)}",
            flush=True,
        )
        if (
            not args.dry_run
            and row.get("terminal_class") == "UNSAFE_FAILURE"
            and not args.keep_going_on_unsafe_failure
        ):
            stopped_reason = f"UNSAFE_FAILURE:{slot_id}"
            break

    end_bundle_hash = stable_payload_hash(execution_bundle_rows(config_path))
    if end_bundle_hash != execution_bundle_hash and not stopped_reason:
        stopped_reason = "EXECUTION_BUNDLE_DRIFT_AT_END"
    summary = summarize(
        rows,
        schedule=schedule,
        formal_full120=formal_full120,
        dry_run=bool(args.dry_run),
        stopped_reason=stopped_reason,
        execution_bundle_hash=execution_bundle_hash,
        execution_bundle_hash_at_end=end_bundle_hash,
        wall_time_sec=perf_counter() - started,
        preflight=preflight,
    )
    atomic_write_json(output / "full120_summary.json", summary)
    (output / "full120_report_zh.md").write_text(
        render_report(summary), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["status"] in {"COMPLETE", "DRY_RUN"} else 1


def sanitize_experiment_environment() -> dict[str, str]:
    removed: dict[str, str] = {}
    for key in tuple(os.environ):
        if key in EXPERIMENT_ENV_KEYS or any(
            key.startswith(prefix) for prefix in EXPERIMENT_ENV_PREFIXES
        ):
            removed[key] = os.environ.pop(key)
    os.environ["LUNAR_ICE_EXPERIMENTAL_PROOF_QUEUE_POLICY"] = "off"
    os.environ["LUNAR_ICE_PROOF_QUEUE_POTENTIAL_TRACE"] = "0"
    os.environ["LUNAR_ICE_GAT_GUIDANCE_MODE"] = "off"
    return removed


def wait_for_large_scale_memory(
    *, min_available_gb: float, timeout_sec: float
) -> dict[str, float | bool]:
    started = perf_counter()
    initial = available_memory_gb()
    current = initial
    while current < float(min_available_gb):
        if perf_counter() - started >= float(timeout_sec):
            return {
                "memory_recovery_pass": False,
                "memory_recovery_wait_sec": round(
                    perf_counter() - started, 6
                ),
                "memory_available_gb_before_wait": round(initial, 6),
                "memory_available_gb_after_wait": round(current, 6),
                "memory_recovery_required_gb": float(min_available_gb),
            }
        sleep(1.0)
        current = available_memory_gb()
    return {
        "memory_recovery_pass": True,
        "memory_recovery_wait_sec": round(perf_counter() - started, 6),
        "memory_available_gb_before_wait": round(initial, 6),
        "memory_available_gb_after_wait": round(current, 6),
        "memory_recovery_required_gb": float(min_available_gb),
    }


def available_memory_gb() -> float:
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        if line.startswith("MemAvailable:"):
            return float(line.split()[1]) * 1024.0 / (1024.0 ** 3)
    return 0.0


def build_schedule(
    selected: Mapping[int, tuple[Path, ...]],
    *,
    output: Path,
    config_path: Path,
) -> list[dict]:
    schedule: list[dict] = []
    for scale in sorted(selected):
        profile = config_profile(config_path, scale)
        for path in selected[scale]:
            key = path.stem.removesuffix("_logical_graph")
            schedule.append(
                {
                    "slot_id": f"s{scale:03d}_{key}",
                    "scale": scale,
                    "backend_id": str(profile["backend_id"]),
                    "instance": str(path.resolve()),
                    "instance_key": key,
                    "instance_sha256": sha256_file(path),
                    "instance_content_hash": "",
                    "service_timing_policy_id": SERVICE_TIMING_POLICY_ID,
                    "slot_dir": str(
                        output / "slots" / f"scale_{scale:03d}" / key
                    ),
                }
            )
    return schedule


def validate_preflight(
    *,
    config_path: Path,
    config: Mapping,
    selected: Mapping[int, tuple[Path, ...]],
    freeze_manifest: Mapping,
    frozen_candidate: Mapping,
    registry: Mapping,
    native_build_info: Mapping,
) -> list[str]:
    issues: list[str] = []
    if registry.get("active_experiment_baseline_id") != BASELINE_ID:
        issues.append("active_baseline_id_mismatch")
    if freeze_manifest.get("freeze_id") != BASELINE_ID:
        issues.append("freeze_manifest_id_mismatch")
    native_rows = list(FROZEN_NATIVE.glob("lunar_spprc_native*.so"))
    if len(native_rows) != 1:
        issues.append("frozen_native_module_count_not_one")
    elif sha256_file(native_rows[0]) != (
        freeze_manifest.get("native_binary_snapshot") or {}
    ).get("sha256"):
        issues.append("frozen_native_sha256_mismatch")
    if dict(native_build_info) != dict(
        frozen_candidate.get("native_build_info") or {}
    ):
        issues.append("frozen_native_build_info_mismatch")
    frozen_config = yaml.safe_load(
        FROZEN_CONFIG_PATH.read_text(encoding="utf-8")
    )
    for key in (
        "live_sri_policy",
        "native_completion_bound_enabled",
        "native_subset_dominance_enabled",
        "native_cut_state_enabled",
        "native_final_judge_pass_policy",
        "native_final_judge_pass_policy_by_scale",
        "native_adaptive_harvest_cap_sec_by_scale",
    ):
        if config.get(key) != frozen_config.get(key):
            issues.append(f"frozen_config_field_mismatch:{key}")
    for scale in SMALL_EXACT_SCALES:
        if (config.get("profiles") or {}).get(str(scale)) != (
            frozen_config.get("profiles") or {}
        ).get(str(scale)):
            issues.append(f"frozen_profile_mismatch:{scale}")
    formal_manifest = read_json(FORMAL_INSTANCE_MANIFEST_PATH)
    formal_paths = {
        str((ROOT / str(row["path"])).resolve()): int(row["scale"])
        for row in formal_manifest.get("instances") or []
    }
    for scale, paths in selected.items():
        if not paths:
            issues.append(f"no_instances:{scale}")
        for path in paths:
            formal_scale = formal_paths.get(str(path.resolve()))
            if formal_scale is None:
                issues.append(f"instance_not_in_formal_manifest:{path}")
            elif formal_scale != int(scale):
                issues.append(f"instance_scale_mismatch:{path}")
    if not config_path.is_file():
        issues.append("config_missing")
    return sorted(set(issues))


def frozen_source_mismatches(candidate: Mapping) -> list[str]:
    mismatches: list[str] = []
    for row in candidate.get("source_bundle") or []:
        path = ROOT / str(row["path"])
        if not path.is_file() or sha256_file(path) != str(row["sha256"]):
            mismatches.append(str(row["path"]))
    return mismatches


def execution_bundle_rows(config_path: Path) -> list[dict[str, str]]:
    frozen_candidate = read_json(FREEZE_CANDIDATE_PATH)
    paths = {
        ROOT / str(row["path"])
        for row in frozen_candidate.get("source_bundle") or []
    }
    paths.update(
        {
            Path(__file__).resolve(),
            config_path.resolve(),
            FREEZE_MANIFEST_PATH.resolve(),
            FREEZE_CANDIDATE_PATH.resolve(),
            next(FROZEN_NATIVE.glob("lunar_spprc_native*.so")).resolve(),
        }
    )
    return [
        {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256_file(path),
        }
        for path in sorted(paths, key=lambda value: str(value))
    ]


def recovered_rows(
    rows: Iterable[dict], schedule: Iterable[dict]
) -> dict[str, dict]:
    expected = {str(row["slot_id"]): row for row in schedule}
    result: dict[str, dict] = {}
    for row in rows:
        slot_id = str(row.get("slot_id") or "")
        if slot_id not in expected or slot_id in result:
            raise ValueError(f"invalid recovered slot {slot_id!r}")
        for key in (
            "scale",
            "backend_id",
            "instance_sha256",
            "service_timing_policy_id",
        ):
            if row.get(key) != expected[slot_id].get(key):
                raise ValueError(
                    f"recovered slot binding mismatch {slot_id}:{key}"
                )
        result[slot_id] = row
    return result


def filter_recovered_rows_for_retry(
    rows: Iterable[dict],
    *,
    retry_unsafe: bool,
    retry_resource_censored: bool,
    retry_legal_incomplete: bool,
    retry_memory_censored: bool,
) -> list[dict]:
    retried_classes = set()
    if retry_unsafe:
        retried_classes.add("UNSAFE_FAILURE")
    if retry_resource_censored:
        retried_classes.add("RESOURCE_CENSORED_INCOMPLETE")
    if retry_legal_incomplete:
        retried_classes.add("LEGAL_INCOMPLETE")
    if retry_memory_censored:
        retried_classes.add("MEMORY_CENSORED_INCOMPLETE")
    return [
        row
        for row in rows
        if str(row.get("terminal_class") or "") not in retried_classes
    ]


def frozen_reference_objectives() -> dict[tuple[int, str], float]:
    rows = read_json(FROZEN_ROWS_PATH)
    return {
        (int(row["scale"]), str(row["instance_key"])): float(row["objective"])
        for row in rows
        if row.get("objective") is not None
    }


def read_tree(run_dir: Path, scale: int) -> dict:
    paths = sorted(
        (run_dir / f"scale_{scale:03d}").glob("**/tree_closure_001.json")
    )
    return read_json(paths[-1]) if paths else {}


def large_scale_incomplete_detail(run_dir: Path, scale: int) -> dict:
    if scale not in LARGE_SHADOW_SCALES or not run_dir.is_dir():
        return {}
    probes = sorted(run_dir.glob(f"scale_{scale:03d}/**/probe.json"))
    if not probes:
        return {}
    try:
        payload = read_json(probes[-1])
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return {}
    final_judge = payload.get("final_judge") or {}
    telemetry = final_judge.get("telemetry") or {}
    engine_status = str(final_judge.get("engine_status") or "")
    host_exitcode_present = "host_exitcode" in telemetry
    return {
        "incomplete_detail_probe": str(probes[-1]),
        "incomplete_pricing_state": str(
            payload.get("pricing_state") or ""
        ),
        "incomplete_native_engine_status": engine_status,
        "incomplete_certificate_blockers": list(
            final_judge.get("certificate_blockers") or []
        ),
        "incomplete_can_enter_certificate_audit": bool(
            final_judge.get("can_enter_certificate_audit")
        ),
        "incomplete_search_exhaustive": bool(
            final_judge.get("search_exhaustive")
        ),
        "incomplete_frontier_empty": bool(
            final_judge.get("frontier_empty")
        ),
        "incomplete_labels_dropped": bool(
            final_judge.get("labels_dropped")
        ),
        "native_memory_limit_returned_without_host_kill": bool(
            engine_status == "MEMORY_LIMIT" and not host_exitcode_present
        ),
        "native_host_exitcode_present": host_exitcode_present,
        "native_memory_limit_bytes_observed": int(
            telemetry.get("native_memory_limit_bytes") or 0
        ),
        "native_host_watchdog_limit_bytes_observed": int(
            telemetry.get("host_memory_watchdog_limit_bytes") or 0
        ),
    }


def safety_issues(row: Mapping) -> list[str]:
    issues: list[str] = []
    launcher_reason = str(row.get("launcher_termination_reason") or "")
    censored = bool(launcher_reason)
    audited_fail_closed = bool(
        row.get("acceptance_summary_present")
        and str(row.get("status") or "") == "FAIL_CLOSED"
        and not row.get("exact")
        and row.get("redlines_zero") is True
        and int(row.get("certificate_leak") or 0) == 0
    )
    if (
        not censored
        and int(row.get("returncode") or 0) != 0
        and not audited_fail_closed
    ):
        issues.append("returncode_nonzero")
    summary_present = bool(row.get("acceptance_summary_present"))
    if row.get("redlines_zero") is False and (not censored or summary_present):
        issues.append("redlines_nonzero")
    if row.get("engine_hash_valid") is False and (not censored or summary_present):
        issues.append("engine_binding_invalid")
    if (
        row.get("incomplete_native_engine_status") == "MEMORY_LIMIT"
        and row.get("native_memory_limit_returned_without_host_kill")
        is not True
    ):
        issues.append("native_memory_limit_used_host_kill")
    if row.get("engine_build_hash") and (
        str(row.get("engine_build_hash"))
        != str(row.get("expected_engine_hash"))
    ):
        issues.append("engine_hash_mismatch")
    # A root-pricing incomplete run never reaches the live-cut tree.  Its
    # diagnostic payload may carry the no-cut default even though the bound
    # acceptance command and config requested P0.  Validate an observed live
    # policy only when a tree result actually exists.
    if (
        row.get("tree_result_present")
        and row.get("live_sri_policy_name") not in {None, "", "P0"}
    ):
        issues.append("p0_policy_name_mismatch")
    if row.get("live_cut_policy_hash") and (
        str(row.get("live_cut_policy_hash"))
        != str(row.get("expected_p0_policy_hash"))
    ):
        issues.append("p0_policy_hash_mismatch")
    if (
        row.get("observed_instance_content_hash")
        and row.get("instance_content_hash")
        and (
        str(row.get("observed_instance_content_hash"))
        != str(row.get("instance_content_hash"))
        )
    ):
        issues.append("instance_content_hash_mismatch")
    if row.get("observed_service_timing_policy_id") and (
        str(row.get("observed_service_timing_policy_id"))
        != SERVICE_TIMING_POLICY_ID
    ):
        issues.append("service_timing_policy_mismatch")
    for field in (
        "certificate_leak",
        "pricing_rc_fail",
        "manual_rc_fail",
    ):
        if int(row.get(field) or 0) != 0:
            issues.append(f"{field}_nonzero")
    for field in (
        "same_run_checkpoint_resume_used",
        "external_probe_used",
        "mature_pool_used",
        "manual_columns_used",
    ):
        if bool(row.get(field)):
            issues.append(field)
    if row.get("no_cheat_pass") is False and (not censored or summary_present):
        issues.append("no_cheat_failed")
    if censored and bool(row.get("exact")):
        issues.append("censored_run_claimed_exact")
    if bool(row.get("exact")):
        if row.get("certificate_scope") != "BPC_TREE_OPTIMAL":
            issues.append("exact_certificate_scope_invalid")
        if row.get("all_certificate_ledgers_valid") is not True:
            issues.append("exact_ledger_invalid")
        if row.get("all_node_lower_bounds_official") is not True:
            issues.append("exact_node_bound_invalid")
        if row.get("all_node_pricing_proofs_certifying") is not True:
            issues.append("exact_pricing_proof_invalid")
        if row.get("tree_certificate_gate_issues"):
            issues.append("exact_tree_certificate_gate_issues")
    return sorted(set(issues))


def objective_matches_reference(row: Mapping) -> bool | None:
    reference = row.get("reference_frozen_objective")
    objective = row.get("objective")
    if reference is None or not row.get("exact"):
        return None
    if objective is None:
        return False
    return abs(float(objective) - float(reference)) <= 1.0e-6


def terminal_class(row: Mapping) -> str:
    if row.get("safety_issues"):
        return "UNSAFE_FAILURE"
    if row.get("exact"):
        if row.get("objective_match_frozen") is False:
            return "UNSAFE_FAILURE"
        return "EXACT"
    if row.get("launcher_termination_reason"):
        return "RESOURCE_CENSORED_INCOMPLETE"
    if str(row.get("incomplete_native_engine_status") or "") == (
        "MEMORY_LIMIT"
    ):
        return "MEMORY_CENSORED_INCOMPLETE"
    return "LEGAL_INCOMPLETE"


def summarize(
    rows: list[dict],
    *,
    schedule: list[dict],
    formal_full120: bool,
    dry_run: bool,
    stopped_reason: str,
    execution_bundle_hash: str,
    execution_bundle_hash_at_end: str,
    wall_time_sec: float,
    preflight: Mapping,
) -> dict:
    row_execution_bundle_hashes = sorted(
        {
            str(row.get("execution_bundle_hash") or "legacy_unbound")
            for row in rows
        }
    )
    by_scale: dict[str, dict] = {}
    for scale in sorted({int(row["scale"]) for row in schedule}):
        scale_rows = [
            row for row in rows if int(row.get("scale") or 0) == scale
        ]
        times = [
            float(row["cold_start_total_sec"])
            for row in scale_rows
            if row.get("cold_start_total_sec") is not None
        ]
        classes = [
            str(row.get("terminal_class") or "") for row in scale_rows
        ]
        by_scale[str(scale)] = {
            "expected_count": sum(
                int(spec["scale"]) == scale for spec in schedule
            ),
            "completed_count": len(scale_rows),
            "exact_count": classes.count("EXACT"),
            "legal_incomplete_count": classes.count("LEGAL_INCOMPLETE"),
            "resource_censored_incomplete_count": classes.count(
                "RESOURCE_CENSORED_INCOMPLETE"
            ),
            "memory_censored_incomplete_count": classes.count(
                "MEMORY_CENSORED_INCOMPLETE"
            ),
            "unsafe_failure_count": classes.count("UNSAFE_FAILURE"),
            "safety_pass_count": sum(
                bool(row.get("safety_pass")) for row in scale_rows
            ),
            "objective_match_frozen_count": sum(
                row.get("objective_match_frozen") is True
                for row in scale_rows
            ),
            "mean_sec": statistics.fmean(times) if times else None,
            "p50_sec": statistics.median(times) if times else None,
            "max_sec": max(times) if times else None,
            "peak_process_tree_rss_gb": max(
                (
                    float(row.get("peak_process_tree_rss_gb") or 0.0)
                    for row in scale_rows
                ),
                default=0.0,
            ),
        }
    safe_classes = {
        "EXACT",
        "LEGAL_INCOMPLETE",
        "RESOURCE_CENSORED_INCOMPLETE",
        "MEMORY_CENSORED_INCOMPLETE",
    }
    memory_censored_count = sum(
        str(row.get("terminal_class")) == "MEMORY_CENSORED_INCOMPLETE"
        for row in rows
    )
    resource_censored_count = sum(
        str(row.get("terminal_class")) == "RESOURCE_CENSORED_INCOMPLETE"
        for row in rows
    )
    complete = bool(
        len(rows) == len(schedule)
        and all(
            str(row.get("terminal_class")) in safe_classes for row in rows
        )
        and execution_bundle_hash == execution_bundle_hash_at_end
        and memory_censored_count == 0
        and resource_censored_count == 0
        and not stopped_reason
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "baseline_id": BASELINE_ID,
        "status": (
            "DRY_RUN" if dry_run else "COMPLETE" if complete else "INCOMPLETE"
        ),
        "created_at_utc": utc_now(),
        "formal_full120": formal_full120,
        "strict_cold_start": True,
        "fresh_python_native_runtime_per_slot": True,
        "solver_resume": False,
        "serial_execution": True,
        "expected_slot_count": len(schedule),
        "completed_slot_count": len(rows),
        "exact_count": sum(
            str(row.get("terminal_class")) == "EXACT" for row in rows
        ),
        "legal_incomplete_count": sum(
            str(row.get("terminal_class")) == "LEGAL_INCOMPLETE"
            for row in rows
        ),
        "resource_censored_incomplete_count": resource_censored_count,
        "memory_censored_incomplete_count": memory_censored_count,
        "unsafe_failure_count": sum(
            str(row.get("terminal_class")) == "UNSAFE_FAILURE"
            for row in rows
        ),
        "all_exact": bool(
            rows
            and len(rows) == len(schedule)
            and all(str(row.get("terminal_class")) == "EXACT" for row in rows)
        ),
        "stopped_reason": stopped_reason,
        "execution_bundle_hash": execution_bundle_hash,
        "execution_bundle_hash_at_end": execution_bundle_hash_at_end,
        "execution_bundle_stable": (
            execution_bundle_hash == execution_bundle_hash_at_end
        ),
        "row_execution_bundle_hashes": row_execution_bundle_hashes,
        "row_execution_bundle_uniform": (
            len(row_execution_bundle_hashes) <= 1
        ),
        "execution_bundle_transition_note": (
            "Recovered 5-30 rows may carry the earlier harness bundle; "
            "the frozen native binary and config are unchanged. The later "
            "bundle only separates the host emergency RSS watchdog from the "
            "native cooperative memory limit for scale 50/100."
            if len(row_execution_bundle_hashes) > 1
            else ""
        ),
        "preflight": dict(preflight),
        "scale_summary": by_scale,
        "wall_time_sec": round(float(wall_time_sec), 6),
    }


def render_report(summary: Mapping) -> str:
    lines = [
        "# P0 V3 六规模全量冷启动复测",
        "",
        f"- 状态：`{summary['status']}`",
        f"- 完成 / 计划：{summary['completed_slot_count']} / "
        f"{summary['expected_slot_count']}",
        f"- exact：{summary['exact_count']}",
        f"- legal incomplete：{summary['legal_incomplete_count']}",
        "- resource-censored incomplete："
        f"{summary['resource_censored_incomplete_count']}",
        "- memory-censored incomplete："
        f"{summary['memory_censored_incomplete_count']}",
        f"- unsafe failure：{summary['unsafe_failure_count']}",
        f"- 全部 exact：`{summary['all_exact']}`",
        "",
        "| scale | 完成 | exact | legal inc | resource censored | "
        "memory censored | unsafe | mean s | p50 s | max s | "
        "peak RSS GiB |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for scale, row in summary["scale_summary"].items():
        lines.append(
            f"| {scale} | {row['completed_count']} | {row['exact_count']} | "
            f"{row['legal_incomplete_count']} | "
            f"{row['resource_censored_incomplete_count']} | "
            f"{row['memory_censored_incomplete_count']} | "
            f"{row['unsafe_failure_count']} | "
            f"{format_number(row['mean_sec'])} | "
            f"{format_number(row['p50_sec'])} | "
            f"{format_number(row['max_sec'])} | "
            f"{format_number(row['peak_process_tree_rss_gb'])} |"
        )
    lines.extend(
        [
            "",
            "50/100 的 legal、resource-censored 或 memory-censored "
            "incomplete只表示安全地没有给出exact证书，不能解释为"
            "最优解或完整BPC closure。memory-censored不能计为正式"
            "3600秒time-limit完成行。",
            "所有实例均从实例 JSON 冷启动；不使用 checkpoint、外部列池、"
            "人工列或 GAT guidance。",
            "",
        ]
    )
    if summary.get("execution_bundle_transition_note"):
        lines.extend(
            [
                "执行束说明："
                + str(summary["execution_bundle_transition_note"]),
                "",
            ]
        )
    return "\n".join(lines)


def write_rows(json_path: Path, csv_path: Path, rows: list[dict]) -> None:
    atomic_write_json(json_path, rows)
    fields = [
        "slot_id",
        "scale",
        "instance_key",
        "backend_id",
        "execution_bundle_hash",
        "terminal_class",
        "status",
        "returncode",
        "cold_start_total_sec",
        "root_cg_sec",
        "tree_sec",
        "exact",
        "safety_pass",
        "objective",
        "reference_frozen_objective",
        "objective_match_frozen",
        "algorithm_status",
        "exact_status",
        "row_budget_exhausted",
        "peak_process_tree_rss_gb",
        "minimum_available_memory_gb",
        "launcher_termination_reason",
        "engine_build_hash",
        "instance_content_hash",
        "service_timing_policy_id",
        "run_dir",
    ]
    temporary = csv_path.with_suffix(csv_path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})
    os.replace(temporary, csv_path)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def format_number(value) -> str:
    return "" if value is None else f"{float(value):.6f}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())

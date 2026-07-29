#!/usr/bin/env python3
"""Run the frozen all-scale DSSR candidate on formal scales 5--50.

Each instance receives a fresh Python/native runtime.  The runner never stops
an instance for RSS alone: Native keeps its cooperative memory limit and the
host backend keeps its fail-closed watchdog, while this launcher only enforces
the row deadline plus an explicit grace period.  Results are persisted after
every slot and can be resumed without reusing solver state.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import signal
import statistics
import subprocess
import sys
from time import monotonic, sleep
from typing import Iterable, Mapping

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from run_live_sri_paired_promotion import (  # noqa: E402
    atomic_write_json,
    config_profile,
    read_run_result,
    sha256_file,
    stable_payload_hash,
)


SCHEMA_VERSION = "lunar_ice_bpc.dssr_all_scale_full100_validation.v1"
CANDIDATE_ID = "LARGE_EXACT_DSSR_ALL_SCALE_CANDIDATE_V1_20260727"
FORMAL_SCALES = (5, 10, 20, 30, 50)
EXPECTED_PER_SCALE = 20
BACKEND_BY_SCALE = {
    5: "native_rcspp_dssr_inprocess",
    10: "native_rcspp_dssr_inprocess",
    20: "native_rcspp_dssr_inprocess",
    30: "native_rcspp_dssr_inprocess",
    50: "native_rcspp_dssr_host",
}
DEFAULT_CONFIG = ROOT / "configs" / "native_live_sri_p0_full120_v1.yaml"
DEFAULT_FREEZE = (
    ROOT
    / "runs"
    / "frozen_large_exact_dssr_all_scale_candidate_v1_20260727"
    / "candidate_freeze_manifest.json"
)
ACCEPTANCE_RUNNER = ROOT / "scripts" / "run_lunar_ice_native_spprc_acceptance.py"
FORMAL_MANIFEST = (
    ROOT
    / "data"
    / "manifests"
    / "lunar_ice_sp50_real_benchmark_manifest.json"
)
P0_ROWS = (
    ROOT
    / "runs"
    / "p0v3_six_scale_full120_baseline_20260727"
    / "full120_rows.json"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--freeze-manifest", type=Path, default=DEFAULT_FREEZE)
    parser.add_argument(
        "--scales", nargs="+", type=int, default=list(FORMAL_SCALES)
    )
    parser.add_argument("--instance", action="append", default=[])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--recover-completed-slots", action="store_true")
    parser.add_argument("--heartbeat-interval-sec", type=float, default=30.0)
    parser.add_argument("--outer-timeout-grace-sec", type=float, default=300.0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    scales = tuple(int(value) for value in args.scales)
    if len(scales) != len(set(scales)):
        raise SystemExit("duplicate scale")
    if any(scale not in FORMAL_SCALES for scale in scales):
        raise SystemExit(f"scales must be a subset of {FORMAL_SCALES}")

    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    config_path = args.config.resolve()
    freeze_path = args.freeze_manifest.resolve()
    freeze = read_json(freeze_path)
    issues = validate_freeze(freeze, config_path=config_path)
    if issues:
        atomic_write_json(
            output / "preflight.json",
            {
                "schema_version": f"{SCHEMA_VERSION}.preflight",
                "status": "FAILED",
                "issues": issues,
            },
        )
        raise SystemExit("candidate freeze validation failed: " + ",".join(issues))

    selected = discover_instances(
        scales,
        explicit=args.instance,
        limit=max(0, int(args.limit)),
    )
    instance_issues = validate_formal_instances(selected)
    if instance_issues:
        raise SystemExit("formal instance validation failed: " + ",".join(instance_issues))
    schedule = build_schedule(selected, output=output)
    formal_full100 = bool(
        not args.limit
        and not args.instance
        and scales == FORMAL_SCALES
        and all(len(selected[scale]) == EXPECTED_PER_SCALE for scale in scales)
    )
    environment, removed_environment = solver_environment(freeze)
    execution_hash = current_execution_bundle_hash(freeze)
    preflight = {
        "schema_version": f"{SCHEMA_VERSION}.preflight",
        "created_at_utc": utc_now(),
        "status": "PASS",
        "candidate_id": CANDIDATE_ID,
        "freeze_manifest": str(freeze_path),
        "freeze_manifest_sha256": sha256_file(freeze_path),
        "candidate_content_bundle_hash": freeze["content_bundle_hash"],
        "execution_bundle_hash": execution_hash,
        "config": str(config_path),
        "config_sha256": sha256_file(config_path),
        "formal_full100": formal_full100,
        "selected_slot_count": len(schedule),
        "instances_per_scale": {
            str(scale): len(selected[scale]) for scale in scales
        },
        "backend_by_scale": {
            str(scale): BACKEND_BY_SCALE[scale] for scale in scales
        },
        "same_dssr_algorithm_all_scales": True,
        "execution_form_note": (
            "5--30 use in-process for matched P0 timing; scale50 uses host "
            "isolation. Both call the same DSSR exact-proof policy."
        ),
        "fresh_python_native_runtime_per_slot": True,
        "solver_resume": False,
        "guidance_disabled": True,
        "torch_expected_imported": False,
        "rss_alone_never_terminates_launcher": True,
        "outer_timeout_grace_sec": float(args.outer_timeout_grace_sec),
        "removed_environment": removed_environment,
    }
    atomic_write_json(output / "preflight.json", preflight)
    atomic_write_json(
        output / "schedule.json",
        {
            "schema_version": f"{SCHEMA_VERSION}.schedule",
            "created_at_utc": utc_now(),
            "slots": schedule,
        },
    )

    rows_path = output / "rows.json"
    rows: list[dict] = []
    if rows_path.is_file():
        if not args.recover_completed_slots:
            raise SystemExit(
                "rows.json already exists; pass --recover-completed-slots "
                "or choose a new output directory"
            )
        rows = list(read_json(rows_path))
    completed = validate_recovered_rows(rows, schedule, execution_hash)
    stopped_reason = ""
    started = monotonic()

    for spec in schedule:
        slot_id = str(spec["slot_id"])
        if slot_id in completed:
            continue
        if current_execution_bundle_hash(freeze) != execution_hash:
            stopped_reason = f"EXECUTION_BUNDLE_DRIFT_BEFORE:{slot_id}"
            break

        run_dir = Path(str(spec["slot_dir"])) / "attempt_01"
        if run_dir.exists():
            stopped_reason = f"UNBOUND_EXISTING_ATTEMPT:{slot_id}"
            break
        run_dir.mkdir(parents=True, exist_ok=False)
        command = [
            sys.executable,
            str(ACCEPTANCE_RUNNER),
            "--config",
            str(config_path),
            "--scales",
            str(spec["scale"]),
            "--backend",
            str(spec["backend_id"]),
            "--instance",
            str(spec["instance"]),
            "--output-dir",
            str(run_dir),
            "--no-resume",
        ]
        row = {
            **spec,
            "candidate_id": CANDIDATE_ID,
            "execution_bundle_hash": execution_hash,
            "expected_engine_hash": freeze["engine_hashes"][
                str(spec["backend_id"])
            ],
            "run_dir": str(run_dir),
            "command": command,
            "started_at_utc": utc_now(),
        }
        print(
            f"[START] {slot_id} completed={len(completed)}/{len(schedule)} "
            f"backend={spec['backend_id']}",
            flush=True,
        )
        if args.dry_run:
            observed = {
                "returncode": 0,
                "launcher_wall_time_sec": 0.0,
                "peak_process_tree_rss_gb": 0.0,
                "minimum_available_memory_gb": available_memory_gb(),
                "launcher_termination_reason": "",
            }
            result = {
                "status": "DRY_RUN",
                "exact": False,
                "redlines_zero": True,
            }
        else:
            profile = config_profile(config_path, int(spec["scale"]))
            observed = run_observed(
                command,
                cwd=ROOT,
                environment=environment,
                stdout_path=run_dir / "launcher_stdout.txt",
                stderr_path=run_dir / "launcher_stderr.txt",
                heartbeat_path=output / "resource_heartbeat.csv",
                slot_id=slot_id,
                timeout_sec=(
                    float(profile["row_time_limit_sec"])
                    + max(0.0, float(args.outer_timeout_grace_sec))
                ),
                heartbeat_interval_sec=max(
                    1.0, float(args.heartbeat_interval_sec)
                ),
            )
            result = read_run_result(
                run_dir,
                scale=int(spec["scale"]),
                returncode=int(observed["returncode"]),
            )
        row.update(result)
        row.update(observed)
        row["acceptance_summary_present"] = (
            run_dir / "native_spprc_acceptance_summary.json"
        ).is_file()
        row["torch_import_audit"] = "not_instrumented_dssr_no_guidance"
        row["objective_match_p0"] = objective_match_p0(row)
        row["safety_issues"] = safety_issues(row)
        row["safety_pass"] = not row["safety_issues"]
        row["terminal_class"] = terminal_class(row)
        row["completed_at_utc"] = utc_now()
        rows.append(row)
        completed[slot_id] = row
        write_rows(rows_path, output / "rows.csv", rows)
        atomic_write_json(
            output / "progress.json",
            {
                "schema_version": f"{SCHEMA_VERSION}.progress",
                "updated_at_utc": utc_now(),
                "completed_slot_count": len(completed),
                "expected_slot_count": len(schedule),
                "last_slot_id": slot_id,
                "last_terminal_class": row["terminal_class"],
                "last_exact": bool(row.get("exact")),
                "last_wall_sec": row.get("cold_start_total_sec"),
                "last_peak_rss_gb": row.get("peak_process_tree_rss_gb"),
            },
        )
        print(
            f"[DONE] {slot_id} class={row['terminal_class']} "
            f"exact={row.get('exact')} sec={row.get('cold_start_total_sec')} "
            f"rss={row.get('peak_process_tree_rss_gb')} "
            f"completed={len(completed)}/{len(schedule)}",
            flush=True,
        )
        if not row["safety_pass"]:
            stopped_reason = f"UNSAFE_FAILURE:{slot_id}"
            break

    if (
        current_execution_bundle_hash(freeze) != execution_hash
        and not stopped_reason
    ):
        stopped_reason = "EXECUTION_BUNDLE_DRIFT_AT_END"
    summary = summarize(
        rows,
        schedule=schedule,
        formal_full100=formal_full100,
        stopped_reason=stopped_reason,
        wall_time_sec=monotonic() - started,
    )
    atomic_write_json(output / "summary.json", summary)
    (output / "report_zh.md").write_text(
        render_report(summary), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["status"] in {"COMPLETE", "DRY_RUN"} else 1


def discover_instances(
    scales: Iterable[int], *, explicit: Iterable[str], limit: int
) -> dict[int, tuple[Path, ...]]:
    selected = {int(scale): [] for scale in scales}
    for raw in explicit:
        path = Path(raw).resolve()
        payload = read_json(path)
        scale = int(payload["scale"])
        if scale not in selected:
            raise ValueError(f"explicit instance scale {scale} not selected")
        selected[scale].append(path)
    for scale in selected:
        if not selected[scale]:
            selected[scale] = sorted(
                (
                    ROOT
                    / "data"
                    / "instances"
                    / f"lunar_ice_sp50_{scale:03d}"
                ).glob("instance_*_logical_graph.json")
            )
        if limit:
            selected[scale] = selected[scale][:limit]
    return {scale: tuple(paths) for scale, paths in selected.items()}


def validate_formal_instances(
    selected: Mapping[int, tuple[Path, ...]]
) -> list[str]:
    manifest = read_json(FORMAL_MANIFEST)
    formal = {
        str((ROOT / str(row["path"])).resolve()): int(row["scale"])
        for row in manifest.get("instances") or []
    }
    issues: list[str] = []
    for scale, paths in selected.items():
        if not paths:
            issues.append(f"no_instances:{scale}")
        for path in paths:
            observed = formal.get(str(path.resolve()))
            if observed is None:
                issues.append(f"not_formal:{path}")
            elif observed != int(scale):
                issues.append(f"scale_mismatch:{path}")
    return sorted(set(issues))


def build_schedule(
    selected: Mapping[int, tuple[Path, ...]], *, output: Path
) -> list[dict]:
    rows: list[dict] = []
    for scale in sorted(selected):
        for path in selected[scale]:
            key = path.stem.removesuffix("_logical_graph")
            rows.append(
                {
                    "slot_id": f"s{scale:03d}_{key}",
                    "scale": int(scale),
                    "backend_id": BACKEND_BY_SCALE[int(scale)],
                    "instance": str(path.resolve()),
                    "instance_key": key,
                    "instance_sha256": sha256_file(path),
                    "slot_dir": str(
                        output / "slots" / f"scale_{scale:03d}" / key
                    ),
                }
            )
    return rows


def validate_freeze(freeze: Mapping, *, config_path: Path) -> list[str]:
    issues: list[str] = []
    if freeze.get("candidate_id") != CANDIDATE_ID:
        issues.append("candidate_id_mismatch")
    if sha256_file(config_path) != freeze.get("config_sha256"):
        issues.append("config_sha256_mismatch")
    frozen_config = ROOT / str(freeze.get("frozen_config") or "")
    if not frozen_config.is_file():
        issues.append("frozen_config_missing")
    elif sha256_file(frozen_config) != freeze.get("frozen_config_sha256"):
        issues.append("frozen_config_sha256_mismatch")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if str(config.get("live_sri_policy")) != "P0":
        issues.append("live_sri_policy_not_p0")
    frozen_native = ROOT / str(freeze.get("frozen_native_module") or "")
    if not frozen_native.is_file():
        issues.append("frozen_native_missing")
    elif sha256_file(frozen_native) != freeze.get("native_module_sha256"):
        issues.append("frozen_native_sha256_mismatch")
    rows = list(freeze.get("source_bundle") or [])
    if not rows:
        issues.append("source_bundle_missing")
    for row in rows:
        path = ROOT / str(row.get("path") or "")
        if not path.is_file():
            issues.append(f"source_missing:{row.get('path')}")
        elif sha256_file(path) != row.get("sha256"):
            issues.append(f"source_sha256_mismatch:{row.get('path')}")
    if rows and stable_payload_hash(rows) != freeze.get("content_bundle_hash"):
        issues.append("content_bundle_hash_mismatch")
    formal = freeze.get("formal_instance_manifest") or {}
    if sha256_file(FORMAL_MANIFEST) != formal.get("sha256"):
        issues.append("formal_instance_manifest_sha256_mismatch")
    registry = freeze.get("p0_registry") or {}
    if sha256_file(P0_ROWS.parents[1] / "native_bpc_baseline_registry.json") != (
        registry.get("sha256")
    ):
        issues.append("p0_registry_sha256_mismatch")
    return sorted(set(issues))


def current_execution_bundle_hash(freeze: Mapping) -> str:
    rows = []
    for frozen in freeze.get("source_bundle") or []:
        path = ROOT / str(frozen["path"])
        rows.append({"path": str(frozen["path"]), "sha256": sha256_file(path)})
    return stable_payload_hash(rows)


def solver_environment(freeze: Mapping) -> tuple[dict[str, str], dict[str, str]]:
    environment = dict(os.environ)
    removed: dict[str, str] = {}
    for key in tuple(environment):
        if (
            key.startswith("LUNAR_ICE_GAT_")
            or key.startswith("LUNAR_ICE_PRE_SOLVE_")
            or key
            in {
                "LUNAR_ICE_DEVELOPMENT_ORACLE_TASK_PRIORITY_JSON",
                "LUNAR_ICE_EXPERIMENTAL_PROOF_QUEUE_POLICY",
                "LUNAR_ICE_PROOF_QUEUE_POTENTIAL_TRACE",
            }
        ):
            removed[key] = environment.pop(key)
    environment["LUNAR_ICE_GAT_GUIDANCE_MODE"] = "off"
    environment["LUNAR_ICE_EXPERIMENTAL_PROOF_QUEUE_POLICY"] = "off"
    environment["LUNAR_ICE_PROOF_QUEUE_POTENTIAL_TRACE"] = "0"
    frozen_native = ROOT / str(freeze["frozen_native_module"])
    environment["PYTHONPATH"] = os.pathsep.join(
        (str(ROOT / "src"), str(frozen_native.parent))
    )
    return environment, removed


def run_observed(
    command: list[str],
    *,
    cwd: Path,
    environment: Mapping[str, str],
    stdout_path: Path,
    stderr_path: Path,
    heartbeat_path: Path,
    slot_id: str,
    timeout_sec: float,
    heartbeat_interval_sec: float,
) -> dict:
    started = monotonic()
    peak_rss = 0
    minimum_available = available_memory_gb()
    termination_reason = ""
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open(
        "w", encoding="utf-8"
    ) as stderr:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=dict(environment),
            stdout=stdout,
            stderr=stderr,
            text=True,
            start_new_session=True,
        )
        next_heartbeat = started
        while process.poll() is None:
            now = monotonic()
            rss = process_tree_rss_bytes(process.pid)
            peak_rss = max(peak_rss, rss)
            minimum_available = min(minimum_available, available_memory_gb())
            if now >= next_heartbeat:
                append_heartbeat(
                    heartbeat_path,
                    {
                        "utc": utc_now(),
                        "slot_id": slot_id,
                        "elapsed_sec": round(now - started, 3),
                        "process_tree_rss_gb": round(
                            rss / (1024.0 ** 3), 6
                        ),
                        "available_memory_gb": round(
                            available_memory_gb(), 6
                        ),
                    },
                )
                next_heartbeat = now + heartbeat_interval_sec
            if now - started >= timeout_sec:
                termination_reason = "OUTER_DEADLINE_AFTER_ROW_GRACE"
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10.0)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5.0)
                break
            sleep(1.0)
        returncode = int(process.wait())
    return {
        "returncode": returncode,
        "launcher_wall_time_sec": round(monotonic() - started, 6),
        "peak_process_tree_rss_gb": round(peak_rss / (1024.0 ** 3), 6),
        "minimum_available_memory_gb": round(minimum_available, 6),
        "launcher_termination_reason": termination_reason,
        "resource_heartbeat_path": str(heartbeat_path),
    }


def process_tree_rss_bytes(root_pid: int) -> int:
    children: dict[int, list[int]] = {}
    rss: dict[int, int] = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        try:
            fields = (entry / "status").read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()
        except OSError:
            continue
        parent = 0
        resident = 0
        for line in fields:
            if line.startswith("PPid:"):
                parent = int(line.split()[1])
            elif line.startswith("VmRSS:"):
                resident = int(line.split()[1]) * 1024
        children.setdefault(parent, []).append(pid)
        rss[pid] = resident
    total = 0
    stack = [int(root_pid)]
    seen: set[int] = set()
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        total += rss.get(pid, 0)
        stack.extend(children.get(pid, ()))
    return total


def available_memory_gb() -> float:
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) * 1024.0 / (1024.0 ** 3)
    return 0.0


def append_heartbeat(path: Path, row: Mapping) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.is_file()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def validate_recovered_rows(
    rows: Iterable[dict], schedule: Iterable[dict], execution_hash: str
) -> dict[str, dict]:
    expected = {str(row["slot_id"]): row for row in schedule}
    completed: dict[str, dict] = {}
    for row in rows:
        slot_id = str(row.get("slot_id") or "")
        if slot_id not in expected or slot_id in completed:
            raise ValueError(f"invalid recovered slot {slot_id!r}")
        for key in ("scale", "backend_id", "instance_sha256"):
            if row.get(key) != expected[slot_id].get(key):
                raise ValueError(f"recovered binding mismatch {slot_id}:{key}")
        if row.get("execution_bundle_hash") != execution_hash:
            raise ValueError(f"recovered execution drift {slot_id}")
        completed[slot_id] = row
    return completed


def p0_reference_rows() -> dict[tuple[int, str], dict]:
    if not P0_ROWS.is_file():
        return {}
    return {
        (int(row["scale"]), str(row["instance_key"])): row
        for row in read_json(P0_ROWS)
        if int(row.get("scale") or 0) in FORMAL_SCALES
    }


def objective_match_p0(row: Mapping) -> bool | None:
    reference = p0_reference_rows().get(
        (int(row["scale"]), str(row["instance_key"]))
    )
    if reference is None or not row.get("exact") or not reference.get("exact"):
        return None
    actual = row.get("objective")
    expected = reference.get("objective")
    if actual is None or expected is None:
        return False
    return math.isclose(
        float(actual), float(expected), rel_tol=0.0, abs_tol=1.0e-6
    )


def safety_issues(row: Mapping) -> list[str]:
    if row.get("status") == "DRY_RUN":
        return []
    issues: list[str] = []
    if not row.get("acceptance_summary_present"):
        issues.append("acceptance_summary_missing")
    if row.get("launcher_termination_reason"):
        issues.append("outer_launcher_terminated")
    if row.get("redlines_zero") is not True:
        issues.append("redlines_nonzero_or_unknown")
    if row.get("engine_hash_valid") is not True:
        issues.append("engine_hash_invalid")
    if str(row.get("engine_build_hash") or "") != str(
        row.get("expected_engine_hash") or ""
    ):
        issues.append("engine_hash_mismatch_frozen_candidate")
    if row.get("no_cheat_pass") is not True:
        issues.append("no_cheat_failed")
    for field in ("certificate_leak", "pricing_rc_fail", "manual_rc_fail"):
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
    if row.get("exact"):
        if row.get("certificate_scope") != "BPC_TREE_OPTIMAL":
            issues.append("exact_certificate_scope_invalid")
        for field in (
            "all_certificate_ledgers_valid",
            "all_node_lower_bounds_official",
            "all_node_pricing_proofs_certifying",
        ):
            if row.get(field) is not True:
                issues.append(f"{field}_false")
        if row.get("tree_certificate_gate_issues"):
            issues.append("tree_certificate_gate_issues")
        if row.get("objective_match_p0") is False:
            issues.append("objective_mismatch_p0")
    return sorted(set(issues))


def terminal_class(row: Mapping) -> str:
    if not row.get("safety_pass"):
        return "UNSAFE_FAILURE"
    if row.get("exact"):
        return "EXACT_CLOSED"
    if row.get("status") in {"FAIL_CLOSED", "INCOMPLETE"}:
        return "LEGAL_INCOMPLETE"
    if row.get("status") == "DRY_RUN":
        return "DRY_RUN"
    return "UNSAFE_FAILURE"


def summarize(
    rows: list[dict],
    *,
    schedule: list[dict],
    formal_full100: bool,
    stopped_reason: str,
    wall_time_sec: float,
) -> dict:
    by_scale = {}
    reference = p0_reference_rows()
    for scale in FORMAL_SCALES:
        scale_rows = [row for row in rows if int(row["scale"]) == scale]
        ratios = []
        for row in scale_rows:
            p0 = reference.get((scale, str(row["instance_key"])))
            if (
                row.get("exact")
                and p0
                and p0.get("exact")
                and row.get("cold_start_total_sec")
                and p0.get("cold_start_total_sec")
            ):
                ratios.append(
                    float(row["cold_start_total_sec"])
                    / float(p0["cold_start_total_sec"])
                )
        by_scale[str(scale)] = {
            "row_count": len(scale_rows),
            "exact_count": sum(bool(row.get("exact")) for row in scale_rows),
            "legal_incomplete_count": sum(
                row.get("terminal_class") == "LEGAL_INCOMPLETE"
                for row in scale_rows
            ),
            "unsafe_count": sum(
                row.get("terminal_class") == "UNSAFE_FAILURE"
                for row in scale_rows
            ),
            "objective_match_count": sum(
                row.get("objective_match_p0") is True for row in scale_rows
            ),
            "mean_sec": mean(
                row.get("cold_start_total_sec") for row in scale_rows
            ),
            "p50_sec": median(
                row.get("cold_start_total_sec") for row in scale_rows
            ),
            "max_peak_process_tree_rss_gb": maximum(
                row.get("peak_process_tree_rss_gb") for row in scale_rows
            ),
            "paired_p0_count": len(ratios),
            "paired_ratio_geomean": (
                math.exp(statistics.fmean(math.log(value) for value in ratios))
                if ratios
                else None
            ),
            "paired_ratio_p50": statistics.median(ratios) if ratios else None,
            "paired_ratio_mean": statistics.fmean(ratios) if ratios else None,
        }
    completed = len(rows) == len(schedule)
    dry_run = bool(rows and all(row.get("status") == "DRY_RUN" for row in rows))
    small_gate = all(
        by_scale[str(scale)]["row_count"] == EXPECTED_PER_SCALE
        and by_scale[str(scale)]["exact_count"] == EXPECTED_PER_SCALE
        and by_scale[str(scale)]["objective_match_count"] == EXPECTED_PER_SCALE
        and by_scale[str(scale)]["unsafe_count"] == 0
        for scale in (5, 10, 20, 30)
    )
    scale50_safety = bool(
        by_scale["50"]["row_count"] == EXPECTED_PER_SCALE
        and by_scale["50"]["unsafe_count"] == 0
    )
    status = (
        "DRY_RUN"
        if dry_run and completed
        else "COMPLETE"
        if completed and not stopped_reason and all(
            row.get("safety_pass") for row in rows
        )
        else "INCOMPLETE"
    )
    return {
        "schema_version": f"{SCHEMA_VERSION}.summary",
        "created_at_utc": utc_now(),
        "status": status,
        "candidate_id": CANDIDATE_ID,
        "formal_full100": formal_full100,
        "expected_slot_count": len(schedule),
        "completed_slot_count": len(rows),
        "stopped_reason": stopped_reason,
        "wall_time_sec": round(wall_time_sec, 6),
        "by_scale": by_scale,
        "safety_gate": all(row.get("safety_pass") for row in rows),
        "scale5_30_exact_nonregression_gate": small_gate,
        "scale50_safety_gate": scale50_safety,
        "baseline_promotion_evaluable": bool(
            formal_full100 and completed and small_gate and scale50_safety
        ),
        "baseline_promotion_decision": "PENDING_PERFORMANCE_AUDIT",
    }


def render_report(summary: Mapping) -> str:
    lines = [
        "# 全规模 DSSR 候选验证",
        "",
        f"- candidate: `{summary['candidate_id']}`",
        f"- status: `{summary['status']}`",
        (
            f"- slots: `{summary['completed_slot_count']}/"
            f"{summary['expected_slot_count']}`"
        ),
        (
            "- 5--30 exact/non-regression gate: "
            f"`{summary['scale5_30_exact_nonregression_gate']}`"
        ),
        f"- scale50 safety gate: `{summary['scale50_safety_gate']}`",
        "",
        "| scale | rows | exact | incomplete | unsafe | p50 sec | mean sec | paired P0 geomean | peak RSS GiB |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for scale, row in summary["by_scale"].items():
        lines.append(
            f"| {scale} | {row['row_count']} | {row['exact_count']} | "
            f"{row['legal_incomplete_count']} | {row['unsafe_count']} | "
            f"{row['p50_sec']} | {row['mean_sec']} | "
            f"{row['paired_ratio_geomean']} | "
            f"{row['max_peak_process_tree_rss_gb']} |"
        )
    return "\n".join(lines) + "\n"


def write_rows(json_path: Path, csv_path: Path, rows: list[dict]) -> None:
    atomic_write_json(json_path, rows)
    fields = [
        "slot_id",
        "scale",
        "instance_key",
        "backend_id",
        "terminal_class",
        "status",
        "exact",
        "objective",
        "objective_match_p0",
        "cold_start_total_sec",
        "launcher_wall_time_sec",
        "peak_process_tree_rss_gb",
        "minimum_available_memory_gb",
        "safety_pass",
        "safety_issues",
        "run_dir",
    ]
    temporary = csv_path.with_suffix(csv_path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            serialized = dict(row)
            serialized["safety_issues"] = json.dumps(
                row.get("safety_issues") or [], ensure_ascii=False
            )
            writer.writerow(serialized)
    os.replace(temporary, csv_path)


def mean(values: Iterable[object]) -> float | None:
    rows = [float(value) for value in values if value is not None]
    return statistics.fmean(rows) if rows else None


def median(values: Iterable[object]) -> float | None:
    rows = [float(value) for value in values if value is not None]
    return statistics.median(rows) if rows else None


def maximum(values: Iterable[object]) -> float | None:
    rows = [float(value) for value in values if value is not None]
    return max(rows) if rows else None


def read_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())

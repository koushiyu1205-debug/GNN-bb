#!/usr/bin/env python3
"""Run the frozen 5/10/20/30 no-cut baseline one instance per process."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import statistics
import subprocess
import sys
import time


RUN_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = RUN_ROOT.parents[1]
PYTHON = Path("/home/kai/miniconda3/bin/python")
CONFIG = RUN_ROOT / "frozen_config.yaml"
SCALES = (5, 10, 20, 30)
EXPECTED_ENGINE_HASH = "66ab52c9b33b4551"
EXPECTED_COMMIT = "ee2f853c003589cb717399209fe232dc793a854b"
EFFECTIVE_MEMORY_GB = {5: 2.0, 10: 4.0, 20: 8.0, 30: 10.867124557495117}
HISTORICAL = {
    5: {"mean": 0.406318, "p50": 0.406548, "mean_ratio_cap": 1.05, "p50_ratio_cap": 1.05},
    10: {"mean": 0.828971, "p50": 0.761838, "mean_ratio_cap": 1.05, "p50_ratio_cap": 1.05},
    20: {"mean": 31.171581, "p50": 17.648412, "mean_ratio_cap": 1.15, "p50_ratio_cap": 1.10},
    30: {"mean": 453.915594, "p50": 327.598609, "mean_ratio_cap": 1.15, "p50_ratio_cap": 1.10},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_text(command: list[str]) -> str:
    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()


def run_capture(command: list[str]) -> dict:
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.splitlines(),
        "stderr": completed.stderr.splitlines(),
    }


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".new")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def process_tree_rss_kb(root_pid: int) -> int:
    completed = subprocess.run(
        ["ps", "-e", "-o", "pid=,ppid=,rss="],
        check=False,
        text=True,
        capture_output=True,
    )
    rows: dict[int, tuple[int, int]] = {}
    children: dict[int, list[int]] = {}
    for raw in completed.stdout.splitlines():
        fields = raw.split()
        if len(fields) != 3:
            continue
        pid, ppid, rss = map(int, fields)
        rows[pid] = (ppid, rss)
        children.setdefault(ppid, []).append(pid)
    pending = [root_pid]
    seen: set[int] = set()
    rss_total = 0
    while pending:
        pid = pending.pop()
        if pid in seen:
            continue
        seen.add(pid)
        rss_total += rows.get(pid, (0, 0))[1]
        pending.extend(children.get(pid, ()))
    return rss_total


def memory_snapshot() -> dict[str, int]:
    values: dict[str, int] = {}
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        key, raw = line.split(":", 1)
        values[key] = int(raw.strip().split()[0])
    return {
        "mem_available_kb": values.get("MemAvailable", 0),
        "swap_free_kb": values.get("SwapFree", 0),
        "swap_total_kb": values.get("SwapTotal", 0),
    }


def heartbeat_writer(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    handle = path.open("a", encoding="utf-8", newline="")
    fields = (
        "timestamp_utc",
        "scale",
        "instance_id",
        "attempt",
        "root_pid",
        "tree_rss_kb",
        "mem_available_kb",
        "swap_free_kb",
        "swap_total_kb",
        "disk_free_bytes",
    )
    writer = csv.DictWriter(handle, fieldnames=fields)
    if not exists:
        writer.writeheader()
        handle.flush()
    return handle, writer


def append_heartbeat(writer, handle, *, scale: int, instance_id: str, attempt: int, pid: int) -> dict:
    memory = memory_snapshot()
    row = {
        "timestamp_utc": utc_now(),
        "scale": scale,
        "instance_id": instance_id,
        "attempt": attempt,
        "root_pid": pid,
        "tree_rss_kb": process_tree_rss_kb(pid),
        **memory,
        "disk_free_bytes": shutil.disk_usage(PROJECT_ROOT).free,
    }
    writer.writerow(row)
    handle.flush()
    return row


def terminate_process_group(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=10)


def successful_attempt(instance_root: Path) -> Path | None:
    for attempt in sorted(instance_root.glob("attempt_*"), reverse=True):
        summary = read_json(attempt / "native_spprc_acceptance_summary.json")
        if summary.get("all_available_runs_succeeded") is True:
            return attempt
    return None


def next_attempt(instance_root: Path) -> tuple[int, Path]:
    existing = sorted(instance_root.glob("attempt_*"))
    number = 1
    if existing:
        try:
            number = max(int(path.name.split("_")[-1]) for path in existing) + 1
        except ValueError:
            number = len(existing) + 1
    return number, instance_root / f"attempt_{number:03d}"


def extract_attempt(scale: int, instance: Path, attempt: Path) -> dict:
    summary = read_json(attempt / "native_spprc_acceptance_summary.json")
    acceptance_row = next(iter(summary.get("rows") or ()), {})
    state = read_json(attempt / f"scale_{scale:03d}" / "b4_2_cold_exact_state.json")
    solver_row = next(iter(state.get("rows") or ()), {})
    tree_result = read_json(
        attempt
        / f"scale_{scale:03d}"
        / "proofs"
        / f"scale_{scale:03d}"
        / instance.stem.replace("_logical_graph", "")
        / "tree_closure_results"
        / "tree_closure_001.json"
    )
    instance_payload = read_json(instance)
    reference = instance_payload.get("reference_solution") or {}
    incumbent_objective = tree_result.get("incumbent_objective")
    global_lower_bound = tree_result.get("global_lower_bound")
    objective_closure_match = bool(
        incumbent_objective is not None
        and global_lower_bound is not None
        and abs(float(incumbent_objective) - float(global_lower_bound)) <= 5.0e-6
    )
    return {
        "scale": scale,
        "instance_id": instance.stem.replace("_logical_graph", ""),
        "instance_path": str(instance),
        "instance_sha256": sha256_file(instance),
        "attempt_dir": str(attempt.relative_to(RUN_ROOT)),
        "runner_status": acceptance_row.get("status"),
        "algorithm_status": solver_row.get("algorithm_status"),
        "exact": bool(solver_row.get("bpc_tree_optimal")),
        "no_cheat": bool(solver_row.get("no_cheat_pass")),
        "cold_start_total_sec": solver_row.get("cold_start_total_sec"),
        "root_cg_sec": solver_row.get("root_cg_sec"),
        "tree_sec": solver_row.get("tree_sec"),
        "pricing_proof_sec": solver_row.get("pricing_proof_sec"),
        "incumbent_objective": incumbent_objective,
        "global_lower_bound": global_lower_bound,
        "objective_closure_match": objective_closure_match,
        "instance_reference_exact_status": reference.get("exact_status"),
        "instance_reference_objective": reference.get("objective"),
        "fail_reason": solver_row.get("fail_reason"),
        "certificate_scope": solver_row.get("certificate_scope"),
        "certificate_leak": solver_row.get("certificate_leak"),
        "pricing_rc_fail": solver_row.get("pricing_rc_fail"),
        "manual_rc_fail": solver_row.get("manual_rc_fail"),
        "row_budget_exhausted": solver_row.get("row_budget_exhausted"),
        "same_run_checkpoint_resume_used": solver_row.get("same_run_checkpoint_resume_used"),
        "engine_hash_valid": (acceptance_row.get("engine_binding") or {}).get("valid"),
        "redlines_zero": acceptance_row.get("redlines_zero"),
        "returncode": acceptance_row.get("returncode"),
    }


def aggregate(instances: dict[int, list[Path]]) -> dict:
    rows: list[dict] = []
    for scale in SCALES:
        for instance in instances[scale]:
            attempt = successful_attempt(RUN_ROOT / "rows" / f"scale_{scale:03d}" / instance.stem)
            if attempt is not None:
                rows.append(extract_attempt(scale, instance, attempt))
    by_scale = {}
    for scale in SCALES:
        scale_rows = [row for row in rows if row["scale"] == scale]
        timings = [float(row["cold_start_total_sec"]) for row in scale_rows if row["cold_start_total_sec"] is not None]
        history = HISTORICAL[scale]
        mean = statistics.fmean(timings) if timings else None
        p50 = statistics.median(timings) if timings else None
        by_scale[str(scale)] = {
            "row_count": len(scale_rows),
            "exact_count": sum(bool(row["exact"]) for row in scale_rows),
            "no_cheat_count": sum(bool(row["no_cheat"]) for row in scale_rows),
            "mean_cold_start_total_sec": mean,
            "p50_cold_start_total_sec": p50,
            "max_cold_start_total_sec": max(timings) if timings else None,
            "mean_ratio_vs_historical": mean / history["mean"] if mean is not None else None,
            "p50_ratio_vs_historical": p50 / history["p50"] if p50 is not None else None,
            "restoration_gate_pass": bool(
                len(scale_rows) == 20
                and all(row["exact"] and row["no_cheat"] for row in scale_rows)
                and all(row["redlines_zero"] is True and row["engine_hash_valid"] is True for row in scale_rows)
                and all(float(row["cold_start_total_sec"] or float("inf")) <= 3600.0 for row in scale_rows)
                and mean is not None
                and p50 is not None
                and mean <= history["mean"] * history["mean_ratio_cap"]
                and p50 <= history["p50"] * history["p50_ratio_cap"]
            ),
        }
    payload = {
        "schema_version": "lunar_ice_bpc.frozen_no_cut_baseline.v1",
        "freeze_id": "FROZEN_NATIVE_NO_CUT_BASELINE_V1",
        "updated_at_utc": utc_now(),
        "expected_commit": EXPECTED_COMMIT,
        "expected_engine_hash": EXPECTED_ENGINE_HASH,
        "rows": rows,
        "by_scale": by_scale,
        "all_80_exact": len(rows) == 80 and all(row["exact"] for row in rows),
        "all_80_objectives_closed": len(rows) == 80 and all(
            row["objective_closure_match"] for row in rows
        ),
        "exact_reference_solution_count": sum(
            row["instance_reference_exact_status"] not in {None, "", "NOT_SOLVED"}
            for row in rows
        ),
        "all_restoration_gates_pass": all(row["restoration_gate_pass"] for row in by_scale.values()),
    }
    write_json(RUN_ROOT / "baseline_summary.json", payload)
    if rows:
        with (RUN_ROOT / "baseline_rows.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=tuple(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    return payload


def freeze_manifest(instances: dict[int, list[Path]]) -> None:
    native_module = PROJECT_ROOT / "build/native-spprc/lunar_spprc_native.cpython-313-x86_64-linux-gnu.so"
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        (str(PROJECT_ROOT / "src"), str(PROJECT_ROOT / "build/native-spprc"), env.get("PYTHONPATH", ""))
    ).rstrip(os.pathsep)
    engine_hash = subprocess.run(
        [str(PYTHON), "-c", "from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import spprc_engine_build_hash; print(spprc_engine_build_hash('native_rcspp_inprocess'))"],
        cwd=PROJECT_ROOT,
        env=env,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    commit = run_text(["git", "rev-parse", "HEAD"])
    if commit != EXPECTED_COMMIT:
        raise RuntimeError(f"baseline commit mismatch: {commit} != {EXPECTED_COMMIT}")
    if engine_hash != EXPECTED_ENGINE_HASH:
        raise RuntimeError(f"engine hash mismatch: {engine_hash} != {EXPECTED_ENGINE_HASH}")
    pip_freeze = run_capture([str(PYTHON), "-m", "pip", "freeze"])
    package_inventory = run_capture(
        [
            str(PYTHON),
            "-c",
            (
                "import importlib.metadata as m,json;"
                "rows=[];"
                "[(rows.append({'name':d.metadata.get('Name') or '',"
                "'version':d.metadata.get('Version') or ''})) for d in m.distributions()];"
                "print(json.dumps(sorted(rows,key=lambda r:(r['name'].lower(),r['version']))))"
            ),
        ]
    )
    cmake_cache = PROJECT_ROOT / "build/native-spprc/CMakeCache.txt"
    manifest = {
        "schema_version": "lunar_ice_bpc.baseline_freeze_manifest.v1",
        "freeze_id": "FROZEN_NATIVE_NO_CUT_BASELINE_V1",
        "created_at_utc": utc_now(),
        "project_root": str(PROJECT_ROOT),
        "git_commit": commit,
        "git_status_short": run_text(["git", "status", "--short", "--", "GAT_BPC_moonTerk"]),
        "python_executable": str(PYTHON),
        "python_version": run_text([str(PYTHON), "--version"]),
        "config_path": str(CONFIG.relative_to(PROJECT_ROOT)),
        "config_sha256": sha256_file(CONFIG),
        "native_module_path": str(native_module.relative_to(PROJECT_ROOT)),
        "native_module_sha256": sha256_file(native_module),
        "native_engine_hash": engine_hash,
        "scales": list(SCALES),
        "instance_count": sum(len(paths) for paths in instances.values()),
        "instances": {
            str(scale): [
                {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": sha256_file(path)}
                for path in paths
            ]
            for scale, paths in instances.items()
        },
        "pip_freeze": pip_freeze,
        "package_inventory_fallback": package_inventory,
        "build_reproduction": {
            "cmake_version": run_text(["cmake", "--version"]).splitlines()[0],
            "cxx_version": run_text(["c++", "--version"]).splitlines()[0],
            "cmake_cache_path": str(cmake_cache.relative_to(PROJECT_ROOT)),
            "cmake_cache_sha256": sha256_file(cmake_cache),
            "cmake_build_type": "RelWithDebInfo",
            "cmake_source_dir": "native/lunar_spprc",
            "cmake_build_dir": "build/native-spprc",
            "build_command": ["cmake", "--build", "build/native-spprc", "-j2"],
            "test_command": ["ctest", "--test-dir", "build/native-spprc", "--output-on-failure"],
        },
        "uname": run_text(["uname", "-a"]),
        "lscpu": run_text(["lscpu"]).splitlines(),
    }
    write_json(RUN_ROOT / "baseline_freeze_manifest.json", manifest)


def main() -> int:
    instances = {
        scale: sorted((PROJECT_ROOT / "data/instances" / f"lunar_ice_sp50_{scale:03d}").glob("instance_*_logical_graph.json"))
        for scale in SCALES
    }
    bad_counts = {scale: len(paths) for scale, paths in instances.items() if len(paths) != 20}
    if bad_counts:
        raise RuntimeError(f"expected 20 instances per scale, got {bad_counts}")
    freeze_manifest(instances)
    heartbeat_handle, heartbeat = heartbeat_writer(RUN_ROOT / "resource_heartbeat.csv")
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        (str(PROJECT_ROOT / "src"), str(PROJECT_ROOT / "build/native-spprc"), env.get("PYTHONPATH", ""))
    ).rstrip(os.pathsep)
    try:
        for scale in SCALES:
            for instance in instances[scale]:
                instance_root = RUN_ROOT / "rows" / f"scale_{scale:03d}" / instance.stem
                if successful_attempt(instance_root) is not None:
                    continue
                attempt_number, attempt = next_attempt(instance_root)
                attempt.mkdir(parents=True, exist_ok=False)
                command = [
                    str(PYTHON),
                    str(PROJECT_ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"),
                    "--config", str(CONFIG),
                    "--scales", str(scale),
                    "--backend", "native_rcspp_inprocess",
                    "--instance", str(instance),
                    "--output-dir", str(attempt),
                    "--no-resume",
                ]
                write_json(attempt / "launcher.json", {"started_at_utc": utc_now(), "command": command})
                with (attempt / "launcher_stdout.log").open("w", encoding="utf-8") as stdout, (attempt / "launcher_stderr.log").open("w", encoding="utf-8") as stderr:
                    process = subprocess.Popen(
                        command,
                        cwd=PROJECT_ROOT,
                        env=env,
                        text=True,
                        stdout=stdout,
                        stderr=stderr,
                        start_new_session=True,
                    )
                    low_memory_since: float | None = None
                    last_heartbeat = 0.0
                    abort_reason = ""
                    while process.poll() is None:
                        now = time.monotonic()
                        if now - last_heartbeat >= 60.0 or last_heartbeat == 0.0:
                            sample = append_heartbeat(
                                heartbeat,
                                heartbeat_handle,
                                scale=scale,
                                instance_id=instance.stem,
                                attempt=attempt_number,
                                pid=process.pid,
                            )
                            last_heartbeat = now
                            rss_cap_kb = int(EFFECTIVE_MEMORY_GB[scale] * 1024 * 1024)
                            if int(sample["tree_rss_kb"]) > rss_cap_kb:
                                abort_reason = "PROCESS_TREE_RSS_LIMIT"
                            if int(sample["mem_available_kb"]) < 1024 * 1024:
                                low_memory_since = low_memory_since or now
                                if now - low_memory_since >= 30.0:
                                    abort_reason = "SYSTEM_AVAILABLE_MEMORY_LIMIT"
                            else:
                                low_memory_since = None
                            if abort_reason:
                                terminate_process_group(process)
                                break
                        time.sleep(1.0)
                    returncode = process.wait()
                    append_heartbeat(
                        heartbeat,
                        heartbeat_handle,
                        scale=scale,
                        instance_id=instance.stem,
                        attempt=attempt_number,
                        pid=process.pid,
                    )
                launcher = read_json(attempt / "launcher.json")
                launcher.update({"finished_at_utc": utc_now(), "returncode": returncode, "abort_reason": abort_reason})
                write_json(attempt / "launcher.json", launcher)
                aggregate(instances)
                if abort_reason:
                    return 2
                if returncode != 0:
                    return returncode
    finally:
        heartbeat_handle.close()
    summary = aggregate(instances)
    return 0 if summary["all_restoration_gates_pass"] else 3


if __name__ == "__main__":
    raise SystemExit(main())

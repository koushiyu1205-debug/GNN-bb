#!/usr/bin/env python3
"""Collect natural post-fixed-K route opportunities without extra pricing."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from time import monotonic, sleep

import yaml


ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE_RUNNER = (
    ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixed-k-selection", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--scales",
        nargs="+",
        type=int,
        choices=(30, 50),
        default=(30,),
    )
    parser.add_argument("--limit-per-scale", type=int, default=5)
    parser.add_argument(
        "--scale30-instance-dir",
        default=(
            "data/p0v4_fixed_k_gat_development_v1/scale_030"
        ),
    )
    parser.add_argument(
        "--scale50-instance-dir",
        default=(
            "data/p0v4_fixed_k_gat_development_v1/scale_050"
        ),
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--full-exact-solves",
        action="store_true",
        default=False,
        help=(
            "Continue through exact tree closure after collection. The "
            "default collection-only scope stops after the natural root pool."
        ),
    )
    parser.add_argument(
        "--root-pool-time-cap-sec",
        type=float,
        default=300.0,
        help=(
            "Per-instance wall cap for diagnostic root-trajectory "
            "collection. Ignored with --full-exact-solves."
        ),
    )
    parser.add_argument(
        "--native-build-dir",
        default="",
        help=(
            "Native extension directory.  When omitted, infer the build "
            "family from the frozen selected Exact config."
        ),
    )
    args = parser.parse_args()
    fixed_path = _resolve(args.fixed_k_selection)
    output = _resolve(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    fixed = _load_json(fixed_path)
    if str(fixed.get("status")) != "FIXED_K_SELECTED":
        raise SystemExit(
            "route opportunity collection requires frozen fixed E_K"
        )
    selected_config = Path(str(fixed["selected_config"])).resolve()
    if (
        not selected_config.is_file()
        or _sha256(selected_config)
        != str(fixed["selected_config_sha256"])
    ):
        raise SystemExit("selected Exact config hash mismatch")
    native_build_dir = _resolve_native_build_dir(
        args.native_build_dir,
        selected_config=selected_config,
    )
    limit = max(1, int(args.limit_per_scale))
    rows = []
    for scale in tuple(dict.fromkeys(int(value) for value in args.scales)):
        instance_dir = _resolve(
            args.scale30_instance_dir
            if scale == 30
            else args.scale50_instance_dir
        )
        run_dir = output / "exact_runs" / f"scale_{scale:03d}"
        snapshot_dir = output / "route_opportunity_rows"
        command = [
            sys.executable,
            str(ACCEPTANCE_RUNNER),
            "--config",
            str(selected_config),
            "--scales",
            str(scale),
            "--instance-dir",
            str(instance_dir),
            "--limit",
            str(limit),
            "--output-dir",
            str(run_dir),
            "--resume" if args.resume else "--no-resume",
        ]
        if not bool(args.full_exact_solves):
            command.extend(
                (
                    "--route-opportunity-collection-only-root-pool",
                    "--route-opportunity-collection-root-pool-time-cap-sec",
                    str(max(1.0, float(args.root_pool_time_cap_sec))),
                )
            )
        row = {
            "scale": scale,
            "command": command,
            "run_dir": str(run_dir.resolve()),
            "route_opportunity_rows_dir": str(
                snapshot_dir.resolve()
            ),
            "execution_scope": (
                "full_exact_solve"
                if bool(args.full_exact_solves)
                else "diagnostic_root_pool_collection_only"
            ),
            "root_pool_time_cap_sec": (
                None
                if bool(args.full_exact_solves)
                else max(1.0, float(args.root_pool_time_cap_sec))
            ),
        }
        if not args.dry_run:
            row.update(
                _run_observed(
                    command,
                    run_dir=run_dir,
                    timeout_sec=limit * 3720.0,
                    snapshot_dir=snapshot_dir,
                    native_build_dir=native_build_dir,
                )
            )
        rows.append(row)
        _write_json(output / "collection_rows.json", rows)
    snapshot_count = len(
        tuple(
            (output / "route_opportunity_rows").rglob(
                "route_admission_snapshot.json"
            )
        )
    )
    execution_succeeded = bool(args.dry_run) or all(
        int(row.get("returncode") or 0) == 0 for row in rows
    )
    manifest = {
        "schema_version": (
            "lunar_ice_bpc.p0v4_route_opportunity_collection.v1"
        ),
        "status": (
            "DRY_RUN"
            if args.dry_run
            else "NATURAL_OPPORTUNITIES_COLLECTED"
            if snapshot_count and execution_succeeded
            else "PARTIAL_NATURAL_OPPORTUNITIES_COLLECTED"
            if snapshot_count
            else "NO_NATURAL_OPPORTUNITIES_OBSERVED"
        ),
        "fixed_k_selection": str(fixed_path.resolve()),
        "fixed_k_selection_sha256": _sha256(fixed_path),
        "selected_config": str(selected_config),
        "selected_config_sha256": _sha256(selected_config),
        "native_build_dir": str(native_build_dir.resolve()),
        "native_build_binding_policy": (
            "explicit_or_selected_exact_backend_family_v1"
        ),
        "scales": list(dict.fromkeys(int(value) for value in args.scales)),
        "instance_limit_per_scale": limit,
        "route_admission_snapshot_count": snapshot_count,
        "route_opportunity_rows_dir": str(
            (output / "route_opportunity_rows").resolve()
        ),
        "native_search_extended_to_manufacture_candidates": False,
        "execution_scope": (
            "full_exact_solve"
            if bool(args.full_exact_solves)
            else "diagnostic_root_pool_collection_only"
        ),
        "tree_closure_required_for_collection": bool(
            args.full_exact_solves
        ),
        "root_pool_time_cap_sec": (
            None
            if bool(args.full_exact_solves)
            else max(1.0, float(args.root_pool_time_cap_sec))
        ),
        "collection_only_can_issue_certificate": False,
        "execution_succeeded": execution_succeeded,
        "large_scale_concurrency": 1,
        "rows": rows,
    }
    _write_json(output / "collection_manifest.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    if args.dry_run:
        return 0
    return 0 if snapshot_count and execution_succeeded else 3


def _run_observed(
    command: list[str],
    *,
    run_dir: Path,
    timeout_sec: float,
    snapshot_dir: Path,
    native_build_dir: Path,
) -> dict:
    run_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = run_dir / "collector_stdout.log"
    stderr_path = run_dir / "collector_stderr.log"
    environment = dict(os.environ)
    pythonpath = [
        str(ROOT / "src"),
        str(native_build_dir.resolve()),
    ]
    if environment.get("PYTHONPATH"):
        pythonpath.append(environment["PYTHONPATH"])
    environment["PYTHONPATH"] = os.pathsep.join(pythonpath)
    environment["LUNAR_ICE_GAT_TRAINING_ROWS_DIR"] = str(
        snapshot_dir.resolve()
    )
    started = monotonic()
    peak_rss = 0
    termination_reason = ""
    with stdout_path.open("w", encoding="utf-8") as stdout, (
        stderr_path.open("w", encoding="utf-8")
    ) as stderr:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=environment,
            stdout=stdout,
            stderr=stderr,
            text=True,
            start_new_session=True,
        )
        try:
            while process.poll() is None:
                peak_rss = max(
                    peak_rss, _process_tree_rss_bytes(process.pid)
                )
                if monotonic() - started >= float(timeout_sec):
                    termination_reason = "COLLECTION_OUTER_DEADLINE"
                    _terminate_process_group(process)
                    break
                sleep(1.0)
        except BaseException:
            _terminate_process_group(process)
            raise
        returncode = int(process.wait())
    return {
        "returncode": returncode,
        "wall_time_sec": monotonic() - started,
        "peak_process_tree_rss_gb": peak_rss / (1024.0**3),
        "termination_reason": termination_reason,
        "stdout": str(stdout_path.resolve()),
        "stderr": str(stderr_path.resolve()),
        "native_build_dir": str(native_build_dir.resolve()),
    }


def _resolve_native_build_dir(
    requested: str,
    *,
    selected_config: Path,
) -> Path:
    if str(requested).strip():
        build_dir = _resolve(requested)
    else:
        payload = yaml.safe_load(
            selected_config.read_text(encoding="utf-8")
        ) or {}
        backend_ids = {
            str(row.get("backend_id") or "")
            for row in dict(payload.get("profiles") or {}).values()
            if isinstance(row, dict)
        }
        if any("bidirectional" in value for value in backend_ids):
            build_dir = (
                ROOT / "build/native-spprc-bidirectional-feasibility-v1"
            )
        else:
            build_dir = ROOT / "build/native-spprc-memory-opt-v2"
    if not build_dir.is_dir():
        raise SystemExit(f"Native build directory is missing: {build_dir}")
    if not any(build_dir.glob("lunar_spprc_native*.so")):
        raise SystemExit(
            "Native build directory does not contain lunar_spprc_native: "
            f"{build_dir}"
        )
    return build_dir.resolve()


def _terminate_process_group(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=10.0)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    process.wait(timeout=5.0)


def _process_tree_rss_bytes(root_pid: int) -> int:
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


def _resolve(value: object) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else ROOT / path


def _load_json(path: Path) -> dict:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


if __name__ == "__main__":
    raise SystemExit(main())

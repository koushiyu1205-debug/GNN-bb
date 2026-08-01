#!/usr/bin/env python3
"""Run paired V5 Exact/GAT held-out solves before deployment promotion."""

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
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE_RUNNER = (
    ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"
)
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.one_deviation_rollout import (  # noqa: E402
    selected_exact_runtime_binding,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixed-k-selection", required=True)
    parser.add_argument("--training-manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--scale30-instance-dir",
        default="data/instances/lunar_ice_sp50_030",
    )
    parser.add_argument(
        "--scale50-instance-dir",
        default="data/instances/lunar_ice_sp50_050",
    )
    parser.add_argument("--minimum-instances-per-scale", type=int, default=10)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    fixed_path = _resolve(args.fixed_k_selection)
    training_path = _resolve(args.training_manifest)
    output = _resolve(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    fixed = _load_json(fixed_path)
    training = _load_json(training_path)
    if str(fixed.get("status") or "") != "FIXED_K_SELECTED":
        raise SystemExit("held-out evaluation requires frozen fixed E_K")
    if not bool(training.get("evaluation_authorized")):
        raise SystemExit("GAT training did not authorize held-out evaluation")
    if bool(training.get("deployment_authorized")):
        raise SystemExit("use the pre-deployment training manifest")
    if str(training.get("fixed_k_selection_sha256") or "") != _sha256(
        fixed_path
    ):
        raise SystemExit("training manifest/fixed E_K hash mismatch")
    selected_config = Path(str(fixed.get("selected_config") or "")).resolve()
    if (
        not selected_config.is_file()
        or _sha256(selected_config)
        != str(fixed.get("selected_config_sha256") or "")
    ):
        raise SystemExit("selected Exact config hash mismatch")
    exact_config = dict(
        yaml.safe_load(selected_config.read_text(encoding="utf-8")) or {}
    )
    control_config, candidate_config = _materialize_configs(
        exact_config,
        training_path=training_path,
        output=output,
    )
    excluded_hashes = {
        str(value)
        for key in ("train_instance_hashes", "calibration_instance_hashes")
        for value in training.get(key, ())
    }
    minimum = max(1, int(args.minimum_instances_per_scale))
    selected_instances = {
        30: _select_heldout_instances(
            _resolve(args.scale30_instance_dir),
            excluded_hashes=excluded_hashes,
            limit=minimum,
        ),
        50: _select_heldout_instances(
            _resolve(args.scale50_instance_dir),
            excluded_hashes=excluded_hashes,
            limit=minimum,
        ),
    }
    for scale, values in selected_instances.items():
        if len(values) < minimum:
            raise SystemExit(
                f"scale{scale} has only {len(values)} independent held-out instances"
            )
    exact_runtime_by_scale = {
        str(scale): selected_exact_runtime_binding(fixed, scale=scale)
        for scale in (30, 50)
    }
    allowed_runtime_hashes = {
        str(value)
        for value in training.get(
            "allowed_exact_runtime_binding_hashes", ()
        )
    }
    for scale, runtime in exact_runtime_by_scale.items():
        if str(runtime["runtime_binding_hash"]) not in allowed_runtime_hashes:
            raise SystemExit(
                f"scale{scale} held-out Exact runtime was not used for training"
            )
    native_build_dir = _native_build_dir(exact_runtime_by_scale)
    rows = []
    failures = 0
    for scale in (30, 50):
        for instance_index, (instance_path, instance_hash) in enumerate(
            selected_instances[scale]
        ):
            arm_order = (
                ("control", "candidate")
                if instance_index % 2 == 0
                else ("candidate", "control")
            )
            arms = {}
            for arm in arm_order:
                config_path = (
                    control_config if arm == "control" else candidate_config
                )
                arm_output = (
                    output
                    / "paired_runs"
                    / f"scale_{scale:03d}"
                    / instance_hash
                    / arm
                )
                command = [
                    sys.executable,
                    str(ACCEPTANCE_RUNNER),
                    "--config",
                    str(config_path),
                    "--scales",
                    str(scale),
                    "--instance",
                    str(instance_path),
                    "--output-dir",
                    str(arm_output),
                    "--resume" if args.resume else "--no-resume",
                ]
                if args.dry_run:
                    command.append("--dry-run")
                observed = _run_or_reuse(
                    command,
                    arm_output=arm_output,
                    scale=scale,
                    resume=bool(args.resume),
                    dry_run=bool(args.dry_run),
                    native_build_dir=native_build_dir,
                )
                arms[arm] = observed
                _write_json(
                    output / "heldout_execution_state.json",
                    {
                        "schema_version": (
                            "lunar_ice_bpc.one_deviation_heldout_execution.v1"
                        ),
                        "rows": rows,
                        "current": {
                            "scale": scale,
                            "instance_content_hash": instance_hash,
                            "arm": arm,
                            **observed,
                        },
                    },
                )
            if args.dry_run:
                rows.append(
                    {
                        "scale": scale,
                        "instance_content_hash": instance_hash,
                        "instance": str(instance_path),
                        "status": "DRY_RUN",
                        "arm_order": list(arm_order),
                        "arms": arms,
                    }
                )
                continue
            try:
                control = _read_arm_result(
                    arms["control"],
                    scale=scale,
                    expected_manifest_sha256="",
                    expected_runtime_binding_hash=str(
                        exact_runtime_by_scale[str(scale)][
                            "runtime_binding_hash"
                        ]
                    ),
                    candidate=False,
                )
                candidate = _read_arm_result(
                    arms["candidate"],
                    scale=scale,
                    expected_manifest_sha256=_sha256(training_path),
                    expected_runtime_binding_hash=str(
                        exact_runtime_by_scale[str(scale)][
                            "runtime_binding_hash"
                        ]
                    ),
                    candidate=True,
                )
                redline_count = int(control["redline_count"]) + int(
                    candidate["redline_count"]
                )
                rows.append(
                    {
                        "schema_version": (
                            "lunar_ice_bpc.one_deviation_heldout_pair.v1"
                        ),
                        "scale": scale,
                        "instance_content_hash": instance_hash,
                        "instance": str(instance_path.resolve()),
                        "arm_order": list(arm_order),
                        "control_exact": bool(control["exact"]),
                        "candidate_exact": bool(candidate["exact"]),
                        "control_time_sec": float(control["time_sec"]),
                        "candidate_time_sec": float(candidate["time_sec"]),
                        "redline_count": redline_count,
                        "candidate_runtime_call_count": int(
                            candidate["runtime_call_count"]
                        ),
                        "candidate_promotion_count": int(
                            candidate["promotion_count"]
                        ),
                        "candidate_noop_count": int(
                            candidate["noop_count"]
                        ),
                        "candidate_runtime_error_count": int(
                            candidate["runtime_error_count"]
                        ),
                        "candidate_ood_noop_count": int(
                            candidate["ood_noop_count"]
                        ),
                        "candidate_inference_latencies_ms": list(
                            candidate["inference_latencies_ms"]
                        ),
                        "candidate_evaluation_mode": True,
                        "training_manifest_sha256": _sha256(training_path),
                        "fixed_k_selection_sha256": _sha256(fixed_path),
                        "exact_runtime_binding_hash": str(
                            exact_runtime_by_scale[str(scale)][
                                "runtime_binding_hash"
                            ]
                        ),
                        "control": control,
                        "candidate": candidate,
                    }
                )
            except Exception as exc:
                failures += 1
                rows.append(
                    {
                        "scale": scale,
                        "instance_content_hash": instance_hash,
                        "instance": str(instance_path.resolve()),
                        "status": "PAIR_VALIDATION_FAILED",
                        "reason": repr(exc),
                        "redline_count": 1,
                    }
                )
            _write_jsonl(output / "heldout_pairs.jsonl", rows)

    manifest = {
        "schema_version": (
            "lunar_ice_bpc.one_deviation_heldout_run_manifest.v1"
        ),
        "status": (
            "DRY_RUN"
            if args.dry_run
            else "COMPLETE" if failures == 0 else "COMPLETE_WITH_FAILURES"
        ),
        "fixed_k_selection": str(fixed_path.resolve()),
        "fixed_k_selection_sha256": _sha256(fixed_path),
        "training_manifest": str(training_path.resolve()),
        "training_manifest_sha256": _sha256(training_path),
        "control_config": str(control_config.resolve()),
        "control_config_sha256": _sha256(control_config),
        "candidate_config": str(candidate_config.resolve()),
        "candidate_config_sha256": _sha256(candidate_config),
        "exact_runtime_bindings": exact_runtime_by_scale,
        "native_build_dir": str(native_build_dir.resolve()),
        "instance_count_by_scale": {
            str(scale): len(values)
            for scale, values in selected_instances.items()
        },
        "instance_selection_policy": (
            "sorted_official_instances_excluding_train_and_calibration_v1"
        ),
        "arm_order_policy": "instance_index_alternating_control_candidate_v1",
        "large_scale_concurrency": 1,
        "failure_count": failures,
        "paired_result_count": len(rows),
        "rows": rows,
    }
    _write_json(output / "heldout_run_manifest.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    if args.dry_run:
        return 0
    return 0 if failures == 0 and len(rows) == 2 * minimum else 3


def _materialize_configs(
    selected: dict,
    *,
    training_path: Path,
    output: Path,
) -> tuple[Path, Path]:
    config_dir = output / "configs"
    config_dir.mkdir(parents=True, exist_ok=True)
    control = json.loads(json.dumps(selected))
    control["model_id"] = "P0V4_V5_ONE_DEVIATION_HELDOUT_CONTROL"
    control["one_deviation_gat_deployment_manifest"] = ""
    control["one_deviation_gat_evaluation_mode"] = False
    candidate = json.loads(json.dumps(selected))
    candidate["model_id"] = "P0V4_V5_ONE_DEVIATION_HELDOUT_CANDIDATE"
    candidate["one_deviation_gat_deployment_manifest"] = str(
        training_path.resolve()
    )
    candidate["one_deviation_gat_deployment_manifest_sha256"] = _sha256(
        training_path
    )
    candidate["one_deviation_gat_evaluation_mode"] = True
    control_path = config_dir / "control.yaml"
    candidate_path = config_dir / "candidate_evaluation.yaml"
    _write_yaml(control_path, control)
    _write_yaml(candidate_path, candidate)
    return control_path, candidate_path


def _select_heldout_instances(
    root: Path,
    *,
    excluded_hashes: set[str],
    limit: int,
) -> list[tuple[Path, str]]:
    selected = []
    seen = set()
    for path in sorted(root.glob("instance_*_logical_graph.json")):
        data = load_lunar_ice_data(
            json.loads(path.read_text(encoding="utf-8"))
        )
        instance_hash = str(data.instance_content_hash)
        if instance_hash in excluded_hashes or instance_hash in seen:
            continue
        seen.add(instance_hash)
        selected.append((path.resolve(), instance_hash))
        if len(selected) >= max(1, int(limit)):
            break
    return selected


def _run_or_reuse(
    command: list[str],
    *,
    arm_output: Path,
    scale: int,
    resume: bool,
    dry_run: bool,
    native_build_dir: Path,
) -> dict[str, Any]:
    state_path = (
        arm_output
        / f"scale_{int(scale):03d}"
        / "b4_2_cold_exact_state.json"
    )
    if resume and _state_has_one_row(state_path):
        return {
            "status": "REUSED",
            "returncode": 0,
            "command": command,
            "state": str(state_path.resolve()),
        }
    if dry_run:
        return {
            "status": "DRY_RUN",
            "returncode": 0,
            "command": command,
            "state": str(state_path.resolve()),
        }
    arm_output.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ)
    pythonpath = [str(ROOT / "src"), str(native_build_dir.resolve())]
    if environment.get("PYTHONPATH"):
        pythonpath.append(environment["PYTHONPATH"])
    environment["PYTHONPATH"] = os.pathsep.join(pythonpath)
    stdout_path = arm_output / "heldout_stdout.log"
    stderr_path = arm_output / "heldout_stderr.log"
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
                peak_rss = max(peak_rss, _process_tree_rss_bytes(process.pid))
                if monotonic() - started >= 3720.0:
                    termination_reason = "HELDOUT_OUTER_DEADLINE"
                    _terminate_process_group(process)
                    break
                sleep(1.0)
        except BaseException:
            _terminate_process_group(process)
            raise
        returncode = int(process.wait())
    return {
        "status": "COMPLETED" if state_path.is_file() else "FAILED",
        "returncode": returncode,
        "command": command,
        "state": str(state_path.resolve()),
        "wall_time_sec": monotonic() - started,
        "peak_process_tree_rss_gb": peak_rss / (1024.0**3),
        "termination_reason": termination_reason,
        "stdout": str(stdout_path.resolve()),
        "stderr": str(stderr_path.resolve()),
    }


def _read_arm_result(
    observed: dict,
    *,
    scale: int,
    expected_manifest_sha256: str,
    expected_runtime_binding_hash: str,
    candidate: bool,
) -> dict:
    state_path = Path(str(observed["state"]))
    state = _load_json(state_path)
    rows = [dict(value) for value in state.get("rows", ())]
    if len(rows) != 1:
        raise ValueError("held-out arm state does not contain one row")
    row = rows[0]
    time_sec = float(row.get("cold_start_total_sec") or 0.0)
    if time_sec <= 0.0:
        raise ValueError("held-out arm lacks a positive solve time")
    exact = bool(
        str(row.get("algorithm_status") or "") == "BPC_OPTIMAL"
        and row.get("exact_certificate")
        and row.get("no_cheat_pass")
    )
    redlines = _row_redline_count(row)
    gat = {
        "runtime_call_count": 0,
        "promotion_count": 0,
        "noop_count": 0,
        "runtime_error_count": 0,
        "ood_noop_count": 0,
        "manifest_mismatch_count": 0,
        "runtime_binding_mismatch_count": 0,
        "evaluation_mode_mismatch_count": 0,
        "inference_latencies_ms": [],
    }
    probe_path = Path(str(row.get("root_pool_latest_probe_json") or ""))
    if probe_path.is_file():
        gat = _audit_probe_history(
            _load_json(probe_path),
            expected_manifest_sha256=expected_manifest_sha256,
            expected_runtime_binding_hash=expected_runtime_binding_hash,
            candidate=candidate,
        )
    elif candidate:
        gat["runtime_error_count"] += 1
    redlines += int(gat["runtime_error_count"])
    redlines += int(gat["manifest_mismatch_count"])
    redlines += int(gat["runtime_binding_mismatch_count"])
    redlines += int(gat["evaluation_mode_mismatch_count"])
    return {
        "scale": int(scale),
        "exact": exact,
        "time_sec": time_sec,
        "redline_count": redlines,
        "algorithm_status": str(row.get("algorithm_status") or ""),
        "objective": row.get("objective"),
        "pricing_state": str(row.get("pricing_state") or ""),
        "returncode": int(observed.get("returncode") or 0),
        "state": str(state_path.resolve()),
        **gat,
    }


def _audit_probe_history(
    probe: dict,
    *,
    expected_manifest_sha256: str,
    expected_runtime_binding_hash: str,
    candidate: bool,
) -> dict[str, Any]:
    rows = [dict(value) for value in probe.get("history", ())]
    runtime_rows = [
        row
        for row in rows
        if bool(row.get("one_deviation_runtime_enabled"))
        or bool(row.get("one_deviation_fallback_to_noop"))
        or str(row.get("one_deviation_runtime_error") or "")
    ]
    result = {
        "runtime_call_count": len(runtime_rows),
        "promotion_count": sum(
            int(bool(row.get("one_deviation_executed")))
            for row in rows
        ),
        "noop_count": sum(
            int(
                bool(row.get("one_deviation_runtime_enabled"))
                and not bool(row.get("one_deviation_executed"))
            )
            for row in rows
        ),
        "runtime_error_count": sum(
            int(bool(str(row.get("one_deviation_runtime_error") or "")))
            for row in rows
        ),
        "ood_noop_count": sum(
            int(bool(row.get("one_deviation_ood"))) for row in rows
        ),
        "manifest_mismatch_count": 0,
        "runtime_binding_mismatch_count": 0,
        "evaluation_mode_mismatch_count": 0,
        "inference_latencies_ms": [
            float(row["one_deviation_inference_wall_ms"])
            for row in runtime_rows
            if row.get("one_deviation_inference_wall_ms") is not None
        ],
    }
    if candidate:
        result["manifest_mismatch_count"] = sum(
            int(
                str(row.get("one_deviation_manifest_sha256") or "")
                != expected_manifest_sha256
            )
            for row in runtime_rows
        )
        result["runtime_binding_mismatch_count"] = sum(
            int(
                str(
                    row.get(
                        "one_deviation_exact_runtime_binding_hash"
                    )
                    or ""
                )
                != expected_runtime_binding_hash
            )
            for row in runtime_rows
        )
        result["evaluation_mode_mismatch_count"] = sum(
            int(not bool(row.get("one_deviation_evaluation_mode")))
            for row in runtime_rows
        )
    elif runtime_rows:
        result["runtime_error_count"] += len(runtime_rows)
    return result


def _row_redline_count(row: dict) -> int:
    count = sum(
        int(row.get(key) or 0)
        for key in (
            "manual_rc_fail",
            "pricing_rc_fail",
            "certificate_leak",
        )
    )
    count += int(not bool(row.get("no_cheat_pass")))
    count += int(bool(row.get("manual_columns_used")))
    count += int(bool(row.get("external_probe_used")))
    count += int(bool(row.get("mature_pool_used")))
    count += int(bool(row.get("per_instance_override_used")))
    return count


def _native_build_dir(bindings: dict[str, dict]) -> Path:
    backends = {str(value["backend_id"]) for value in bindings.values()}
    if any("bidirectional" in value for value in backends):
        result = ROOT / "build/native-spprc-bidirectional-feasibility-v1"
    else:
        result = ROOT / "build/native-spprc-memory-opt-v2"
    if not result.is_dir() or not any(result.glob("lunar_spprc_native*.so")):
        raise SystemExit(f"Native build is missing: {result}")
    return result.resolve()


def _state_has_one_row(path: Path) -> bool:
    try:
        return len(_load_json(path).get("rows", ())) == 1
    except Exception:
        return False


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
    seen = set()
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        total += rss.get(pid, 0)
        stack.extend(children.get(pid, ()))
    return total


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


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _write_yaml(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )
    os.replace(temporary, path)


if __name__ == "__main__":
    raise SystemExit(main())

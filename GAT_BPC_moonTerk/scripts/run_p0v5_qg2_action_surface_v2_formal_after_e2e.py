#!/usr/bin/env python3
"""Run formal action-surface-v2 full20 only after development E2E passes.

The calibrated report and manifest are taken from the hash-bound E2E state,
so the strict and relaxed-training paths cannot be mixed accidentally.  This
controller is inert until its post-E2E freeze is created.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
FREEZE = RUN_ROOT / "qg2_action_surface_v2_formal_controller_freeze.json"
E2E_STATE = RUN_ROOT / "qg2_action_surface_v2_e2e_controller_state.json"
E2E_RESULT = RUN_ROOT / "e2e_development_acceptance_qg2_action_surface_v2.json"
OUTPUT_ROOT = RUN_ROOT / "formal_full20_qg2_action_surface_v2"
CONTROL_ROOT = OUTPUT_ROOT / "control"
GUIDED_ROOT = OUTPUT_ROOT / "guided"
RESULT = RUN_ROOT / "formal_full20_acceptance_qg2_action_surface_v2.json"
STATE = RUN_ROOT / "qg2_action_surface_v2_formal_controller_state.json"
BUILD = ROOT / "build/native-spprc-bidirectional-feasibility-v1"
CONFIG = ROOT / "runs/p0v4_v5_exact_gat_binding_20260731/selected_exact_v5.yaml"

CALIBRATION_SCHEMA = "lunar_ice_bpc.p0v5_qg2_fresh_process_calibration.v4"
GUIDANCE_ENV_KEYS = (
    "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST",
    "LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE",
    "LUNAR_ICE_PROOF_QUEUE_GAT_MANIFEST",
    "LUNAR_ICE_PROOF_QUEUE_GAT_EVALUATION_MODE",
    "LUNAR_ICE_BIDIRECTIONAL_GATE_GAT_MANIFEST",
    "LUNAR_ICE_BIDIRECTIONAL_GATE_GAT_EVALUATION_MODE",
    "LUNAR_ICE_GAT_DEPLOYMENT_MANIFEST",
    "LUNAR_ICE_GAT_GUIDANCE_MODE",
    "LUNAR_ICE_GAT_TRAINING_ROWS_DIR",
    "LUNAR_ICE_P0V5_QG2_SNAPSHOT_GLOBAL_STORAGE_CAP",
    "LUNAR_ICE_P0V5_QG2_SNAPSHOT_PER_SCALE_STORAGE_CAP",
    "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR",
    "LUNAR_ICE_P0V5_QG2_SNAPSHOT_MAX_PER_INSTANCE",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-for-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = max(1.0, min(60.0, float(args.poll_sec)))
    _validate_freeze()
    _state("WAITING_FOR_DEVELOPMENT_E2E_GATE", wait_for_pid=args.wait_for_pid)
    while _matching_e2e_controller_alive(args.wait_for_pid):
        print(json.dumps({
            "status": "waiting_for_development_e2e_gate",
            "pid": int(args.wait_for_pid),
        }, sort_keys=True), flush=True)
        time.sleep(poll)

    if not E2E_STATE.is_file() or not E2E_RESULT.is_file():
        _state("NOT_STARTED_DEVELOPMENT_E2E_EVIDENCE_MISSING")
        return 2
    e2e_state = _load(E2E_STATE)
    e2e = _load(E2E_RESULT)
    if not _valid_e2e_result(e2e, e2e_state):
        _state("NOT_STARTED_DEVELOPMENT_E2E_EVIDENCE_INVALID")
        return 2

    calibration_path = Path(
        str(e2e_state.get("calibration_report") or "")
    ).resolve()
    if (
        not calibration_path.is_file()
        or _sha256(calibration_path)
        != str(e2e_state.get("calibration_report_sha256") or "")
    ):
        raise SystemExit("QG2 formal calibration report binding mismatch")
    calibration = _load(calibration_path)
    if not bool(
        calibration.get("schema_version") == CALIBRATION_SCHEMA
        and calibration.get("gate_pass")
        and calibration.get("deployment_authorized")
    ):
        _state("NOT_STARTED_CALIBRATION_NOT_AUTHORIZED")
        return 2
    manifest = _validated_manifest(calibration, e2e_state)
    if OUTPUT_ROOT.exists() or RESULT.exists():
        raise SystemExit("QG2 action-surface-v2 formal refuses overwrite or resume")

    _state(
        "RUNNING_FORMAL_EXACT_CONTROL",
        authority=e2e_state.get("authority"),
        calibration_report=str(calibration_path),
    )
    control_code = _run_acceptance(output=CONTROL_ROOT, manifest=None)
    if control_code not in {0, 1}:
        _state("CONTROL_EXECUTION_ERROR", returncode=control_code)
        return control_code
    _state("RUNNING_FORMAL_QG2_GUIDED")
    guided_code = _run_acceptance(output=GUIDED_ROOT, manifest=manifest)
    if guided_code not in {0, 1}:
        _state("GUIDED_EXECUTION_ERROR", returncode=guided_code)
        return guided_code

    analyzed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/analyze_p0v5_qg2_paired_acceptance.py"),
            "--control-root", str(CONTROL_ROOT),
            "--guided-root", str(GUIDED_ROOT),
            "--output", str(RESULT),
            "--mode", "formal",
        ],
        cwd=ROOT,
        env=_environment(manifest=None),
        check=False,
    )
    if analyzed.returncode not in {0, 2}:
        _state("ANALYZER_EXECUTION_ERROR", returncode=analyzed.returncode)
        return analyzed.returncode
    result = _load(RESULT)
    passed = bool(result.get("passed"))
    _state(
        "FORMAL_FULL20_PASSED" if passed else "FORMAL_FULL20_GATE_FAILED",
        authority=e2e_state.get("authority"),
        calibration_report=str(calibration_path),
        manifest=str(manifest),
        manifest_sha256=_sha256(manifest),
        result=str(RESULT),
        result_sha256=_sha256(RESULT),
        violations=result.get("violations"),
        candidate_freeze_permitted=passed,
        production_switch_performed=False,
    )
    return 0 if passed else 2


def _run_acceptance(*, output: Path, manifest: Path | None) -> int:
    return subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"),
            "--config", str(CONFIG),
            "--scales", "5", "10", "20", "30", "50",
            "--limit", "20",
            "--output-dir", str(output),
            "--no-resume",
        ],
        cwd=ROOT,
        env=_environment(manifest=manifest),
        check=False,
    ).returncode


def _environment(*, manifest: Path | None) -> dict[str, str]:
    env = dict(os.environ)
    for key in GUIDANCE_ENV_KEYS:
        env.pop(key, None)
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{BUILD}"
    if manifest is not None:
        env["LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST"] = str(manifest)
    return env


def _valid_e2e_result(payload: dict, state: dict) -> bool:
    if not bool(
        str(state.get("status") or "") == "E2E_PASSED"
        and payload.get("schema_version")
        == "lunar_ice_bpc.p0v5_qg2_paired_acceptance.v1"
        and payload.get("mode") == "development"
        and payload.get("passed")
        and int(payload.get("violation_count") or 0) == 0
        and {int(value) for value in (payload.get("by_scale") or {})}
        == {30, 50}
        and _sha256(E2E_RESULT) == str(state.get("result_sha256") or "")
    ):
        return False
    for prefix in ("control", "guided"):
        root = _resolve(payload.get(f"{prefix}_root") or "")
        if (
            not root.is_dir()
            or _acceptance_artifact_hash(root)
            != str(payload.get(f"{prefix}_root_hash") or "")
        ):
            return False
    return True


def _validated_manifest(calibration: dict, e2e_state: dict) -> Path:
    manifest = Path(str(calibration.get("manifest_path") or "")).resolve()
    if (
        not manifest.is_file()
        or _sha256(manifest) != str(calibration.get("manifest_sha256") or "")
        or str(manifest) != str(Path(str(e2e_state.get("manifest") or "")).resolve())
        or _sha256(manifest) != str(e2e_state.get("manifest_sha256") or "")
    ):
        raise SystemExit("QG2 formal calibrated manifest binding mismatch")
    return manifest


def _acceptance_artifact_hash(root: Path) -> str:
    digest = hashlib.sha256()
    paths = set()
    for pattern in (
        "**/b4_2_cold_exact_rows.csv",
        "**/b4_2_cold_exact_state.json",
        "**/b4_2_cold_exact_summary.json",
        "**/tree_closure_001.json",
    ):
        paths.update(root.glob(pattern))
    if not paths:
        return ""
    for path in sorted(paths):
        digest.update(str(path.relative_to(root)).encode("utf-8"))
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _matching_e2e_controller_alive(pid: int) -> bool:
    path = Path(f"/proc/{int(pid)}/cmdline")
    try:
        command = path.read_bytes().replace(b"\0", b" ").decode(
            "utf-8", errors="replace"
        )
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return "run_p0v5_qg2_action_surface_v2_e2e_after_calibration.py" in command


def _validate_freeze() -> dict:
    payload = _load(FREEZE)
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_formal_controller_freeze.v1"
    ):
        raise SystemExit("QG2 action-surface-v2 formal freeze schema mismatch")
    if not bool(payload.get("development_only")) or bool(
        payload.get("production_default")
    ):
        raise SystemExit("QG2 action-surface-v2 formal freeze safety mismatch")
    for raw_path, expected in dict(
        payload.get("frozen_file_sha256") or {}
    ).items():
        path = _resolve(raw_path)
        if not path.is_file() or _sha256(path) != str(expected):
            raise SystemExit(f"QG2 formal frozen file drift: {path}")
    return payload


def _state(status: str, **extra) -> None:
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_formal_controller_state.v1",
        "status": str(status),
        **extra,
    }
    _write(STATE, payload)


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

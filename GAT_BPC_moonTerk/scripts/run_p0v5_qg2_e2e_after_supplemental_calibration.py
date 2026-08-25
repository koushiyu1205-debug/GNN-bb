#!/usr/bin/env python3
"""Run the frozen QG2 development E2E after supplemental calibration."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_p0v5_qg2_action_surface_v2_e2e_after_calibration as base  # noqa: E402


RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
FREEZE = RUN_ROOT / "qg2_supplemental_e2e_controller_freeze.json"
SUPPLEMENT_STATE = RUN_ROOT / "qg2_supplemental_calibration_controller_state.json"
SUPPLEMENT_BINDING = (
    RUN_ROOT
    / "calibration_qg2_action_surface_v2_supplemental/"
    "supplemental_calibration_binding.json"
)
STATE = RUN_ROOT / "qg2_supplemental_e2e_controller_state.json"
RESULT = RUN_ROOT / "e2e_development_acceptance_qg2_action_surface_v2.json"
OUTPUT_ROOT = RUN_ROOT / "e2e_qg2_action_surface_v2"
CONTROL_ROOT = OUTPUT_ROOT / "control"
GUIDED_ROOT = OUTPUT_ROOT / "guided"
BINDING_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_supplemental_calibration_binding.v1"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-for-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = max(1.0, min(60.0, float(args.poll_sec)))
    _validate_freeze()
    _state("WAITING_FOR_SUPPLEMENTAL_CALIBRATION", wait_for_pid=args.wait_for_pid)
    while _matching_supplemental_controller_alive(args.wait_for_pid):
        time.sleep(poll)

    authority = _validated_supplemental_authority()
    if authority is None:
        _state("NOT_STARTED_SUPPLEMENTAL_CALIBRATION_NOT_AUTHORIZED")
        return 0
    if RESULT.exists() or OUTPUT_ROOT.exists():
        if RESULT.is_file() and bool(_load(RESULT).get("passed")):
            _state(
                "NOT_NEEDED_DEVELOPMENT_E2E_ALREADY_PASSED",
                result=str(RESULT),
                result_sha256=_sha256(RESULT),
            )
            return 0
        raise SystemExit("supplemental QG2 E2E refuses partial/failed output")

    training = _load(authority["training_view"])
    calibration = _load(authority["calibration_report"])
    if not base._authorized_reports(
        training,
        calibration,
        training_path=authority["training_view"],
    ):
        raise SystemExit("supplemental QG2 E2E report authority mismatch")
    manifest = base._validated_manifest(calibration)
    instances = base._heldout_instances(training)
    _state(
        "RUNNING_SUPPLEMENTAL_EXACT_CONTROL",
        instances=[str(path) for path in instances],
        calibration_report=str(authority["calibration_report"]),
    )
    control_code = base._run_acceptance(
        output=CONTROL_ROOT,
        instances=instances,
        manifest=None,
    )
    if control_code not in {0, 1}:
        _state("CONTROL_EXECUTION_ERROR", returncode=control_code)
        return control_code
    _state("RUNNING_SUPPLEMENTAL_QG2_GUIDED")
    guided_code = base._run_acceptance(
        output=GUIDED_ROOT,
        instances=instances,
        manifest=manifest,
    )
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
            "--mode", "development",
        ],
        cwd=ROOT,
        env=base._environment(manifest=None),
        check=False,
    )
    if analyzed.returncode not in {0, 2} or not RESULT.is_file():
        _state("ANALYZER_EXECUTION_ERROR", returncode=analyzed.returncode)
        return int(analyzed.returncode or 3)
    result = _load(RESULT)
    passed = bool(result.get("passed"))
    _state(
        "E2E_PASSED" if passed else "E2E_GATE_FAILED",
        authority="supplemental_calibration_hash_bound",
        supplemental_binding=str(SUPPLEMENT_BINDING),
        supplemental_binding_sha256=_sha256(SUPPLEMENT_BINDING),
        calibration_report=str(authority["calibration_report"]),
        calibration_report_sha256=_sha256(authority["calibration_report"]),
        manifest=str(manifest),
        manifest_sha256=_sha256(manifest),
        result=str(RESULT),
        result_sha256=_sha256(RESULT),
        violations=result.get("violations"),
    )
    return 0 if passed else 2


def _validated_supplemental_authority() -> dict[str, Path] | None:
    if not SUPPLEMENT_STATE.is_file() or not SUPPLEMENT_BINDING.is_file():
        return None
    state = _load(SUPPLEMENT_STATE)
    if state.get("status") != "SUPPLEMENTAL_CALIBRATION_PASSED_PENDING_E2E":
        return None
    binding = _load(SUPPLEMENT_BINDING)
    if (
        binding.get("schema_version") != BINDING_SCHEMA
        or int(binding.get("training_rows_added", -1)) != 0
        or not bool(binding.get("gate_pass"))
        or not bool(binding.get("deployment_authorized"))
    ):
        return None
    result = {}
    for path_key, hash_key in (
        ("training_view", "training_view_sha256"),
        ("oracle_view", "oracle_view_sha256"),
        ("split_view", "split_view_sha256"),
        ("calibration_report", "calibration_report_sha256"),
        ("supplemental_manifest", "supplemental_manifest_sha256"),
    ):
        path = _resolve(binding.get(path_key) or "")
        if (
            not path.is_file()
            or _sha256(path) != str(binding.get(hash_key) or "")
        ):
            return None
        result[path_key] = path
    return result


def _matching_supplemental_controller_alive(pid: int) -> bool:
    try:
        command = Path(f"/proc/{int(pid)}/cmdline").read_bytes().replace(
            b"\0", b" "
        ).decode("utf-8", errors="replace")
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return "run_p0v5_qg2_supplemental_calibration_after_training.py" in command


def _validate_freeze() -> None:
    payload = _load(FREEZE)
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_supplemental_e2e_controller_freeze.v1"
    ):
        raise SystemExit("supplemental E2E freeze schema mismatch")
    if not bool(payload.get("development_only")) or bool(payload.get("deployable")):
        raise SystemExit("supplemental E2E freeze safety mismatch")
    if str(payload.get("controller_sha256") or "") != _sha256(
        Path(__file__).resolve()
    ):
        raise SystemExit("supplemental E2E controller drift")
    for raw_path, expected in dict(payload.get("frozen_file_sha256") or {}).items():
        path = _resolve(raw_path)
        if not path.is_file() or _sha256(path) != str(expected):
            raise SystemExit(f"supplemental E2E frozen drift: {path}")


def _state(status: str, **extra: Any) -> None:
    _write(STATE, {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_supplemental_e2e_controller_state.v1"
        ),
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": status,
        **extra,
    })


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

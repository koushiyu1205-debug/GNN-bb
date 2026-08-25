#!/usr/bin/env python3
"""Run paired scale5--50 full20 only after clean-v2 development E2E passes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from continue_p0v5_qg2_clean_v2_collection import GUIDANCE_ENV_KEYS


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
FREEZE = (
    RUN_ROOT / "qg2_clean_v2_formal_controller_freeze_storage_cap_v3.json"
)
E2E_STATE = RUN_ROOT / "qg2_clean_v2_e2e_controller_state.json"
E2E_RESULT = RUN_ROOT / "e2e_development_acceptance_qg2_clean_v2.json"
CALIBRATION_REPORT = RUN_ROOT / "calibration_qg2_clean_v2/calibration_report.json"
OUTPUT_ROOT = RUN_ROOT / "formal_full20_qg2_clean_v2"
CONTROL_ROOT = OUTPUT_ROOT / "control"
GUIDED_ROOT = OUTPUT_ROOT / "guided"
RESULT = RUN_ROOT / "formal_full20_acceptance_qg2_clean_v2.json"
STATE = RUN_ROOT / "qg2_clean_v2_formal_controller_state.json"
BUILD = ROOT / "build/native-spprc-bidirectional-feasibility-v1"
CONFIG = ROOT / "runs/p0v4_v5_exact_gat_binding_20260731/selected_exact_v5.yaml"


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
            "pid": args.wait_for_pid,
        }, sort_keys=True), flush=True)
        time.sleep(poll)

    e2e_state = _load(E2E_STATE)
    if str(e2e_state.get("status") or "") != "E2E_PASSED":
        _state(
            "NOT_STARTED_DEVELOPMENT_E2E_GATE_FAILED",
            e2e_status=e2e_state.get("status"),
        )
        return 2
    e2e = _load(E2E_RESULT)
    if not _valid_e2e_result(e2e, e2e_state):
        _state("NOT_STARTED_DEVELOPMENT_E2E_EVIDENCE_INVALID")
        return 2

    calibration = _load(CALIBRATION_REPORT)
    if not bool(
        calibration.get("gate_pass")
        and calibration.get("deployment_authorized")
    ):
        _state("NOT_STARTED_CALIBRATION_NOT_AUTHORIZED")
        return 2
    manifest = Path(str(calibration.get("manifest_path") or "")).resolve()
    if (
        not manifest.is_file()
        or _sha256(manifest) != str(calibration.get("manifest_sha256") or "")
    ):
        raise SystemExit("QG2 formal calibrated manifest binding mismatch")
    if OUTPUT_ROOT.exists() or RESULT.exists():
        raise SystemExit("QG2 formal controller refuses overwrite or resume")

    _state("RUNNING_FORMAL_EXACT_CONTROL")
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
        result=str(RESULT),
        result_sha256=_sha256(RESULT),
        violations=result.get("violations"),
        candidate_freeze_permitted=passed,
        production_switch_performed=False,
    )
    return 0 if passed else 2


def _acceptance_command(*, output: Path) -> list[str]:
    return [
        sys.executable,
        str(ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"),
        "--config", str(CONFIG),
        "--scales", "5", "10", "20", "30", "50",
        "--limit", "20",
        "--output-dir", str(output),
        "--no-resume",
    ]


def _run_acceptance(*, output: Path, manifest: Path | None) -> int:
    return subprocess.run(
        _acceptance_command(output=output),
        cwd=ROOT,
        env=_environment(manifest=manifest),
        check=False,
    ).returncode


def _environment(*, manifest: Path | None) -> dict[str, str]:
    env = dict(os.environ)
    for key in GUIDANCE_ENV_KEYS:
        env.pop(key, None)
    env.pop("LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR", None)
    env.pop("LUNAR_ICE_P0V5_QG2_SNAPSHOT_MAX_PER_INSTANCE", None)
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{BUILD}"
    if manifest is not None:
        env["LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST"] = str(manifest)
    return env


def _valid_e2e_result(payload: dict, state: dict) -> bool:
    return bool(
        payload.get("schema_version")
        == "lunar_ice_bpc.p0v5_qg2_paired_acceptance.v1"
        and payload.get("mode") == "development"
        and payload.get("passed")
        and int(payload.get("violation_count") or 0) == 0
        and _sha256(E2E_RESULT) == str(state.get("result_sha256") or "")
    )


def _matching_e2e_controller_alive(pid: int) -> bool:
    path = Path(f"/proc/{int(pid)}/cmdline")
    try:
        command = path.read_bytes().replace(b"\0", b" ").decode(
            "utf-8", errors="replace"
        )
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return "run_p0v5_qg2_clean_v2_e2e_after_calibration.py" in command


def _validate_freeze() -> None:
    payload = _load(FREEZE)
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_formal_controller_freeze.v1"
    ):
        raise SystemExit("QG2 formal controller freeze schema mismatch")
    if not bool(payload.get("development_only")) or bool(
        payload.get("production_default")
    ):
        raise SystemExit("QG2 formal controller freeze safety mismatch")
    for raw_path, expected in dict(
        payload.get("frozen_file_sha256") or {}
    ).items():
        path = Path(raw_path)
        path = path if path.is_absolute() else ROOT / path
        if not path.is_file() or _sha256(path) != str(expected):
            raise SystemExit(f"QG2 formal frozen file drift: {path}")


def _state(status: str, **extra) -> None:
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_formal_controller_state.v1",
        "status": status,
        **extra,
    }
    temporary = STATE.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, STATE)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

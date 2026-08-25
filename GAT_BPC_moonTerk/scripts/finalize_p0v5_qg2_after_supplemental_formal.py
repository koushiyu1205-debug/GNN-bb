#!/usr/bin/env python3
"""Invoke the frozen candidate finalizer with supplemental stage bindings."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "scripts/finalize_p0v5_qg2_action_surface_v2_candidate.py"
SPEC = importlib.util.spec_from_file_location("qg2_finalizer_base", BASE_PATH)
assert SPEC is not None and SPEC.loader is not None
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)


RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
FREEZE = RUN_ROOT / "qg2_supplemental_candidate_finalizer_freeze.json"
FORMAL_STATE = RUN_ROOT / "qg2_supplemental_formal_controller_state.json"
E2E_STATE = RUN_ROOT / "qg2_supplemental_e2e_controller_state.json"
E2E_FREEZE = RUN_ROOT / "qg2_supplemental_e2e_controller_freeze.json"
FORMAL_FREEZE = RUN_ROOT / "qg2_supplemental_formal_controller_freeze.json"
STATE = RUN_ROOT / "qg2_supplemental_candidate_finalizer_state.json"
STANDARD_FORMAL_STATE = RUN_ROOT / "qg2_action_surface_v2_formal_controller_state.json"
STANDARD_E2E_STATE = RUN_ROOT / "qg2_action_surface_v2_e2e_controller_state.json"
STANDARD_FORMAL_FREEZE = RUN_ROOT / "qg2_action_surface_v2_formal_controller_freeze.json"
STANDARD_E2E_FREEZE = RUN_ROOT / "qg2_action_surface_v2_e2e_controller_freeze.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-for-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = max(1.0, min(60.0, float(args.poll_sec)))
    _validate_freeze()
    _state("WAITING_FOR_SUPPLEMENTAL_FORMAL_FULL20", args.wait_for_pid)
    while _matching_supplemental_formal_alive(args.wait_for_pid):
        time.sleep(poll)
    if not FORMAL_STATE.is_file():
        _state("NOT_STARTED_SUPPLEMENTAL_FORMAL_STATE_MISSING")
        return 0
    formal_state = _load(FORMAL_STATE)
    if formal_state.get("status") not in {
        "FORMAL_FULL20_PASSED",
        "NOT_NEEDED_FORMAL_FULL20_ALREADY_PASSED",
    }:
        _state("NOT_STARTED_SUPPLEMENTAL_FORMAL_GATE_FAILED")
        return 0
    if _existing_candidate_complete():
        _state("NOT_NEEDED_CANDIDATE_ALREADY_FROZEN")
        return 0
    selected = _selected_stage_binding(formal_state)
    if selected is None:
        _state("NOT_STARTED_FINALIZER_STAGE_BINDING_INVALID")
        return 2
    base.FREEZE = FREEZE
    base.FORMAL_STATE = selected["formal_state"]
    base.E2E_STATE = selected["e2e_state"]
    base.E2E_FREEZE = selected["e2e_freeze"]
    base.FORMAL_FREEZE = selected["formal_freeze"]
    base.STATE = STATE
    original = list(sys.argv)
    try:
        sys.argv = [
            str(BASE_PATH),
            "--wait-for-pid", str(args.wait_for_pid),
            "--poll-sec", str(poll),
        ]
        return int(base.main())
    finally:
        sys.argv = original


def _selected_stage_binding(formal_state: dict) -> dict[str, Path] | None:
    if str(formal_state.get("status") or "") == "FORMAL_FULL20_PASSED":
        if not E2E_STATE.is_file():
            return None
        e2e_state = _load(E2E_STATE)
        if str(e2e_state.get("status") or "") != "E2E_PASSED":
            return None
        if not _state_result_bound(formal_state, base.FORMAL_RESULT):
            return None
        if not _state_result_bound(e2e_state, base.E2E_RESULT):
            return None
        return {
            "formal_state": FORMAL_STATE,
            "e2e_state": E2E_STATE,
            "formal_freeze": FORMAL_FREEZE,
            "e2e_freeze": E2E_FREEZE,
        }
    if not STANDARD_FORMAL_STATE.is_file() or not STANDARD_E2E_STATE.is_file():
        return None
    standard_formal = _load(STANDARD_FORMAL_STATE)
    standard_e2e = _load(STANDARD_E2E_STATE)
    if str(standard_formal.get("status") or "") != "FORMAL_FULL20_PASSED":
        return None
    if str(standard_e2e.get("status") or "") != "E2E_PASSED":
        return None
    if not _state_result_bound(standard_formal, base.FORMAL_RESULT):
        return None
    if not _state_result_bound(standard_e2e, base.E2E_RESULT):
        return None
    return {
        "formal_state": STANDARD_FORMAL_STATE,
        "e2e_state": STANDARD_E2E_STATE,
        "formal_freeze": STANDARD_FORMAL_FREEZE,
        "e2e_freeze": STANDARD_E2E_FREEZE,
    }


def _state_result_bound(state: dict, result: Path) -> bool:
    return bool(
        result.is_file()
        and str(state.get("result_sha256") or "") == _sha256(result)
    )


def _existing_candidate_complete() -> bool:
    if not base.CANDIDATE.is_file() or not base.FINAL_AUDIT.is_file():
        return False
    candidate = _load(base.CANDIDATE)
    audit = _load(base.FINAL_AUDIT)
    return bool(
        candidate.get("schema_version")
        == "lunar_ice_bpc.p0v5_qg2_action_surface_v2_candidate_freeze.v1"
        and candidate.get("status") == "FROZEN_EXPERIMENT_CANDIDATE"
        and not bool(candidate.get("production_default"))
        and audit.get("complete")
        and int(audit.get("failed_check_count") or 0) == 0
        and int(audit.get("incomplete_check_count") or 0) == 0
    )


def _matching_supplemental_formal_alive(pid: int) -> bool:
    try:
        command = Path(f"/proc/{int(pid)}/cmdline").read_bytes().replace(
            b"\0", b" "
        ).decode("utf-8", errors="replace")
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return "run_p0v5_qg2_formal_after_supplemental_e2e.py" in command


def _validate_freeze() -> None:
    payload = _load(FREEZE)
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_candidate_finalizer_freeze.v1"
    ):
        raise SystemExit("supplemental candidate finalizer freeze mismatch")
    if bool(payload.get("production_default")) or not bool(
        payload.get("development_only")
    ):
        raise SystemExit("supplemental finalizer cannot change production")
    for raw_path, expected in dict(payload.get("frozen_file_sha256") or {}).items():
        path = _resolve(raw_path)
        if not path.is_file() or _sha256(path) != str(expected):
            raise SystemExit(f"supplemental finalizer frozen drift: {path}")


def _state(status: str, wait_for_pid: int | None = None) -> None:
    payload = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_supplemental_candidate_finalizer_state.v1"
        ),
        "status": status,
    }
    if wait_for_pid is not None:
        payload["wait_for_pid"] = int(wait_for_pid)
    temporary = STATE.with_suffix(STATE.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(STATE)


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

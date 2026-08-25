#!/usr/bin/env python3
"""Run formal full20 only after selective-runtime development E2E passes."""

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
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import run_p0v5_qg2_action_surface_v2_formal_after_e2e as base  # noqa: E402

from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (  # noqa: E402
    QG2_RUNTIME_POLICY_ID,
    qg2_runtime_implementation_hash,
)
from lunar_ice_bpc.guidance.qg2_oracle_evidence import (  # noqa: E402
    SELECTIVE_TRAINING_ONLY_MODE,
)
from lunar_ice_bpc.guidance.qg2_runtime_oracle_authority import (  # noqa: E402
    validate_qg2_runtime_oracle_authority,
)


RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
E2E_STATE = RUN_ROOT / "qg2_selective_runtime_e2e_state.json"
E2E_RESULT = RUN_ROOT / "e2e_qg2_selective_runtime_v1_acceptance.json"
OUTPUT_ROOT = RUN_ROOT / "formal_full20_qg2_selective_runtime_v1"
CONTROL_ROOT = OUTPUT_ROOT / "control"
GUIDED_ROOT = OUTPUT_ROOT / "guided"
RESULT = RUN_ROOT / "formal_full20_qg2_selective_runtime_v1_acceptance.json"
STATE = RUN_ROOT / "qg2_selective_runtime_formal_state.json"

E2E_STATE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_selective_runtime_e2e_state.v1"
ACCEPTANCE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_paired_acceptance.v1"
MANIFEST_SCHEMA = "lunar_ice_bpc.p0v5_qg2_manifest.v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-for-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = max(1.0, min(60.0, float(args.poll_sec)))
    _state("WAITING_FOR_SELECTIVE_RUNTIME_DEVELOPMENT_E2E", wait_for_pid=args.wait_for_pid)
    while _matching_e2e_controller(args.wait_for_pid):
        time.sleep(poll)

    if not E2E_STATE.is_file() or not E2E_RESULT.is_file():
        _state("NOT_STARTED_SELECTIVE_RUNTIME_E2E_EVIDENCE_MISSING")
        return 2
    e2e_state = _load(E2E_STATE)
    e2e_result = _load(E2E_RESULT)
    try:
        manifest = validate_selective_runtime_formal_authority(
            e2e_state,
            e2e_state_path=E2E_STATE,
            e2e_result=e2e_result,
            e2e_result_path=E2E_RESULT,
        )
    except Exception as exc:
        _state(
            "NOT_STARTED_SELECTIVE_RUNTIME_E2E_EVIDENCE_INVALID",
            error=f"{type(exc).__name__}:{exc}",
        )
        return 3
    if OUTPUT_ROOT.exists() or RESULT.exists():
        _state("REFUSED_EXISTING_SELECTIVE_RUNTIME_FORMAL_OUTPUT")
        return 3

    _state("RUNNING_SELECTIVE_RUNTIME_FORMAL_EXACT_CONTROL")
    control_code = base._run_acceptance(output=CONTROL_ROOT, manifest=None)
    if control_code not in {0, 1}:
        _state("CONTROL_EXECUTION_ERROR", returncode=int(control_code))
        return int(control_code)
    _state("RUNNING_SELECTIVE_RUNTIME_FORMAL_QG2", manifest=str(manifest))
    guided_code = base._run_acceptance(output=GUIDED_ROOT, manifest=manifest)
    if guided_code not in {0, 1}:
        _state("GUIDED_EXECUTION_ERROR", returncode=int(guided_code))
        return int(guided_code)

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
        env=base._environment(manifest=None),
        check=False,
    )
    if analyzed.returncode not in {0, 2} or not RESULT.is_file():
        _state("ANALYZER_EXECUTION_ERROR", returncode=int(analyzed.returncode))
        return int(analyzed.returncode or 3)
    result = _load(RESULT)
    passed = bool(
        result.get("schema_version") == ACCEPTANCE_SCHEMA
        and result.get("mode") == "formal"
        and result.get("passed")
        and int(result.get("violation_count") or 0) == 0
        and {int(value) for value in (result.get("by_scale") or {})}
        == {5, 10, 20, 30, 50}
    )
    _state(
        (
            "SELECTIVE_RUNTIME_FORMAL_FULL20_PASSED"
            if passed
            else "SELECTIVE_RUNTIME_FORMAL_FULL20_GATE_FAILED"
        ),
        e2e_state=str(E2E_STATE),
        e2e_state_sha256=_sha256(E2E_STATE),
        e2e_result=str(E2E_RESULT),
        e2e_result_sha256=_sha256(E2E_RESULT),
        manifest=str(manifest),
        manifest_sha256=_sha256(manifest),
        result=str(RESULT),
        result_sha256=_sha256(RESULT),
        violations=result.get("violations"),
        candidate_freeze_permitted=passed,
        production_switch_performed=False,
        fallback_action="Q0",
    )
    return 0 if passed else 2


def validate_selective_runtime_formal_authority(
    state: Mapping[str, Any],
    *,
    e2e_state_path: Path,
    e2e_result: Mapping[str, Any],
    e2e_result_path: Path,
) -> Path:
    errors: list[str] = []
    if state.get("schema_version") != E2E_STATE_SCHEMA:
        errors.append("e2e_state_schema_mismatch")
    if str(state.get("status") or "") != (
        "SELECTIVE_RUNTIME_E2E_PASSED_PENDING_FORMAL"
    ):
        errors.append("e2e_state_not_authorized")
    if not bool(state.get("formal_experiment_authorized")):
        errors.append("formal_experiment_not_authorized")
    if bool(state.get("production_switch_authorized")):
        errors.append("production_scope_expansion")
    if str(state.get("fallback_action") or "") != "Q0":
        errors.append("literal_q0_fallback_mismatch")
    if str(state.get("result_sha256") or "") != _sha256(e2e_result_path):
        errors.append("e2e_result_hash_mismatch")
    if not bool(
        e2e_result.get("schema_version") == ACCEPTANCE_SCHEMA
        and e2e_result.get("mode") == "development"
        and e2e_result.get("passed")
        and int(e2e_result.get("violation_count") or 0) == 0
        and {int(value) for value in (e2e_result.get("by_scale") or {})}
        == {30, 50}
    ):
        errors.append("development_e2e_acceptance_mismatch")
    for prefix in ("control", "guided"):
        root = _resolve_relative(
            e2e_result_path,
            e2e_result.get(f"{prefix}_root") or "",
        )
        if (
            not root.is_dir()
            or base._acceptance_artifact_hash(root)
            != str(e2e_result.get(f"{prefix}_root_hash") or "")
        ):
            errors.append(f"development_{prefix}_artifact_hash_mismatch")
    manifest = _resolve_relative(
        e2e_state_path,
        state.get("manifest") or "",
    )
    if not manifest.is_file():
        errors.append("runtime_manifest_missing")
    elif str(state.get("manifest_sha256") or "") != _sha256(manifest):
        errors.append("runtime_manifest_hash_mismatch")
    else:
        payload = _load(manifest)
        try:
            evidence_mode = validate_qg2_runtime_oracle_authority(payload)
        except Exception as exc:
            errors.append(
                f"runtime_oracle_authority:{type(exc).__name__}:{exc}"
            )
            evidence_mode = ""
        if evidence_mode != SELECTIVE_TRAINING_ONLY_MODE:
            errors.append("runtime_oracle_authority_mode_mismatch")
        if payload.get("schema_version") != MANIFEST_SCHEMA:
            errors.append("runtime_manifest_schema_mismatch")
        if str(payload.get("runtime_policy_id") or "") != QG2_RUNTIME_POLICY_ID:
            errors.append("runtime_policy_mismatch")
        if str(payload.get("runtime_implementation_hash") or "") != (
            qg2_runtime_implementation_hash()
        ):
            errors.append("runtime_implementation_drift")
        if not bool(payload.get("deployment_authorized")):
            errors.append("runtime_manifest_not_calibration_authorized")
        if not bool(payload.get("ordering_only")):
            errors.append("ordering_only_contract_missing")
        if str(payload.get("fallback") or "") != "P0V4_V5_Q0":
            errors.append("runtime_manifest_literal_q0_fallback_mismatch")
        if {int(value) for value in payload.get("allowed_scales") or ()} != {
            30, 50
        }:
            errors.append("runtime_manifest_allowed_scales_mismatch")
        if not list(payload.get("allowed_exact_engine_hashes") or ()):
            errors.append("runtime_manifest_engine_allowlist_missing")
        if not list(payload.get("allowed_exact_action_policy_hashes") or ()):
            errors.append("runtime_manifest_action_policy_allowlist_missing")
        checkpoint = _resolve_relative(
            manifest,
            payload.get("checkpoint_path") or "",
        )
        if not checkpoint.is_file():
            errors.append("runtime_manifest_checkpoint_missing")
        elif str(payload.get("checkpoint_sha256") or "") != _sha256(
            checkpoint
        ):
            errors.append("runtime_manifest_checkpoint_hash_mismatch")
        for key in ("can_filter", "can_prune", "can_change_bound", "can_certify"):
            if bool(payload.get(key)):
                errors.append(f"runtime_manifest_forbidden_authority:{key}")
    if errors:
        raise ValueError(
            "selective runtime formal authority failed: "
            + ",".join(sorted(set(errors)))
        )
    return manifest


def _resolve_relative(source: Path, value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (source.parent / path).resolve()


def _matching_e2e_controller(pid: int) -> bool:
    try:
        command = Path(f"/proc/{int(pid)}/cmdline").read_bytes().replace(
            b"\0", b" "
        ).decode("utf-8", errors="replace")
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return "run_p0v5_qg2_selective_runtime_e2e_after_binding.py" in command


def _state(status: str, **extra: Any) -> None:
    _write(STATE, {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_selective_runtime_formal_state.v1",
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": str(status),
        **extra,
    })


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

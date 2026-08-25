#!/usr/bin/env python3
"""Freeze the selective QG2 experiment candidate after every gate passes.

This finalizer is intentionally downstream of the read-only QD1/QB1 selector,
fresh-process calibration and risk audit, selective runtime binding,
development E2E, and formal full20.  It never changes production defaults or
the frozen P0V4/P0V5 Exact control.  Any binding or safety mismatch fails
closed before a candidate is written.
"""

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

import run_p0v5_qg2_selective_runtime_binding_after_calibration as binding  # noqa: E402
import run_p0v5_qg2_selective_runtime_e2e_after_binding as e2e  # noqa: E402
import run_p0v5_qg2_selective_runtime_formal_after_e2e as formal  # noqa: E402

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
BUILD = ROOT / "build/native-spprc-bidirectional-feasibility-v1"
CONFIG = ROOT / "runs/p0v4_v5_exact_gat_binding_20260731/selected_exact_v5.yaml"

ORACLE_FREEZE = RUN_ROOT / "qg2_action_surface_v2_oracle_execution_freeze.json"
ORACLE = RUN_ROOT / "oracle_qg2_action_surface_v2_stage1.json"
TRAINING = (
    RUN_ROOT
    / "training_qg2_action_surface_v2_training_only_v2/training_report.json"
)
SELECTOR = RUN_ROOT / "context_arm_selector_feasibility_v1/selector_report.json"
CALIBRATION_STATE = RUN_ROOT / "qg2_training_only_v2_calibration_controller_state.json"
CALIBRATION = (
    RUN_ROOT
    / "calibration_qg2_action_surface_v2_training_only_v2/calibration_report.json"
)
RISK = RUN_ROOT / "qg2_training_only_v2_calibration_risk_audit.json"
EVIDENCE_STATE = RUN_ROOT / "qg2_selective_oracle_evidence_controller_state.json"
EVIDENCE = RUN_ROOT / "qg2_training_only_v2_selective_oracle_evidence.json"
MANIFEST = RUN_ROOT / "qg2_training_only_v2_selective_runtime_manifest.json"
AUTHORITY = RUN_ROOT / "qg2_training_only_v2_selective_runtime_authority.json"
E2E_STATE = RUN_ROOT / "qg2_selective_runtime_e2e_state.json"
E2E_RESULT = RUN_ROOT / "e2e_qg2_selective_runtime_v1_acceptance.json"
FORMAL_STATE = RUN_ROOT / "qg2_selective_runtime_formal_state.json"
FORMAL_RESULT = RUN_ROOT / "formal_full20_qg2_selective_runtime_v1_acceptance.json"

CANDIDATE = (
    RUN_ROOT / "P0V5_QG2_LABEL_STATE_GAT_SELECTIVE_RUNTIME_V1_candidate_freeze.json"
)
AUDIT = RUN_ROOT / "qg2_selective_runtime_completion_audit.json"
STATE = RUN_ROOT / "qg2_selective_runtime_candidate_finalizer_state.json"

RUNTIME_SOURCE = ROOT / "src/lunar_ice_bpc/guidance/proof_queue_label_state_runtime.py"
MODEL_SOURCE = ROOT / "src/lunar_ice_bpc/guidance/proof_queue_label_state_gat.py"
AUTHORITY_SOURCE = ROOT / "src/lunar_ice_bpc/guidance/qg2_runtime_oracle_authority.py"
EVIDENCE_SOURCE = ROOT / "src/lunar_ice_bpc/guidance/qg2_oracle_evidence.py"
CALIBRATION_AUTHORITY_SOURCE = (
    ROOT / "src/lunar_ice_bpc/guidance/qg2_calibration_authority.py"
)
BINDER_SOURCE = ROOT / "scripts/bind_p0v5_qg2_selective_runtime_manifest.py"
BINDING_SOURCE = (
    ROOT / "scripts/run_p0v5_qg2_selective_runtime_binding_after_calibration.py"
)
E2E_SOURCE = ROOT / "scripts/run_p0v5_qg2_selective_runtime_e2e_after_binding.py"
FORMAL_SOURCE = ROOT / "scripts/run_p0v5_qg2_selective_runtime_formal_after_e2e.py"
NATIVE_EXTENSIONS = tuple(sorted(BUILD.glob("lunar_spprc_native*.so")))

CANDIDATE_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_selective_runtime_candidate_freeze.v1"
)
AUDIT_SCHEMA = "lunar_ice_bpc.p0v5_qg2_selective_runtime_completion_audit.v1"
ACCEPTANCE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_paired_acceptance.v1"
FORMAL_STATE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_selective_runtime_formal_state.v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-for-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = max(1.0, min(60.0, float(args.poll_sec)))
    _state("WAITING_FOR_SELECTIVE_RUNTIME_FORMAL", wait_for_pid=args.wait_for_pid)
    while _matching_formal_controller(args.wait_for_pid):
        time.sleep(poll)

    required = (
        ORACLE_FREEZE, ORACLE, TRAINING, SELECTOR, CALIBRATION_STATE,
        CALIBRATION, RISK, EVIDENCE_STATE, EVIDENCE, MANIFEST, AUTHORITY,
        E2E_STATE, E2E_RESULT, FORMAL_STATE, FORMAL_RESULT,
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        _state("NOT_STARTED_REQUIRED_EVIDENCE_MISSING", missing=missing)
        return 2
    if CANDIDATE.exists() or AUDIT.exists():
        _state("REFUSED_EXISTING_SELECTIVE_RUNTIME_CANDIDATE_OUTPUT")
        return 3
    try:
        manifest = validate_selective_candidate_authority()
    except Exception as exc:
        _state(
            "NOT_STARTED_SELECTIVE_RUNTIME_AUTHORITY_INVALID",
            error=f"{type(exc).__name__}:{exc}",
        )
        return 3

    _state("RUNNING_FINAL_REGRESSION_AND_NATIVE_TESTS")
    tests = _run_tests()
    if not bool(tests.get("passed")):
        _write_audit(False, ["regression_or_native_tests_failed"], tests=tests)
        _state("FINAL_REGRESSION_OR_NATIVE_TESTS_FAILED", tests=tests)
        return 2

    try:
        payload = build_selective_candidate_payload(manifest, tests=tests)
    except Exception as exc:
        _state(
            "SELECTIVE_RUNTIME_CANDIDATE_BUILD_FAILED",
            error=f"{type(exc).__name__}:{exc}",
        )
        return 3
    _write(CANDIDATE, payload)
    issues = audit_selective_candidate_payload(payload)
    _write_audit(not issues, issues, tests=tests)
    if issues:
        _state(
            "SELECTIVE_RUNTIME_CANDIDATE_AUDIT_FAILED",
            candidate=str(CANDIDATE),
            candidate_sha256=_sha256(CANDIDATE),
            issues=issues,
        )
        return 2
    _state(
        "SELECTIVE_RUNTIME_CANDIDATE_FROZEN_AND_AUDITED",
        candidate=str(CANDIDATE),
        candidate_sha256=_sha256(CANDIDATE),
        completion_audit=str(AUDIT),
        completion_audit_sha256=_sha256(AUDIT),
        production_switch_performed=False,
        historical_baselines_unchanged=True,
        fallback_action="Q0",
    )
    return 0


def validate_selective_candidate_authority() -> Path:
    authority = _load(AUTHORITY)
    training = _load(TRAINING)
    bound_manifest = e2e.validate_selective_runtime_e2e_authority(
        authority,
        authority_path=AUTHORITY,
        training=training,
        training_path=TRAINING,
    )
    if bound_manifest != MANIFEST.resolve():
        raise ValueError("selective runtime manifest path mismatch")

    rebuilt = binding.build_selective_runtime_e2e_authority(
        calibration_state_path=CALIBRATION_STATE,
        calibration_report_path=CALIBRATION,
        risk_audit_path=RISK,
        selective_evidence_state_path=EVIDENCE_STATE,
        selective_evidence_path=EVIDENCE,
        selector_report_path=SELECTOR,
        bound_manifest_path=MANIFEST,
    )
    _compare_authority_payloads(authority, rebuilt)

    e2e_state = _load(E2E_STATE)
    e2e_result = _load(E2E_RESULT)
    if str(e2e_state.get("authority_sha256") or "") != _sha256(AUTHORITY):
        raise ValueError("development E2E authority hash mismatch")
    formal_manifest = formal.validate_selective_runtime_formal_authority(
        e2e_state,
        e2e_state_path=E2E_STATE,
        e2e_result=e2e_result,
        e2e_result_path=E2E_RESULT,
    )
    if formal_manifest != bound_manifest:
        raise ValueError("development E2E manifest drift")

    formal_state = _load(FORMAL_STATE)
    formal_result = _load(FORMAL_RESULT)
    if not bool(
        formal_state.get("schema_version") == FORMAL_STATE_SCHEMA
        and formal_state.get("status")
        == "SELECTIVE_RUNTIME_FORMAL_FULL20_PASSED"
        and formal_state.get("candidate_freeze_permitted")
        and not formal_state.get("production_switch_performed")
        and formal_state.get("fallback_action") == "Q0"
        and str(formal_state.get("result_sha256") or "")
        == _sha256(FORMAL_RESULT)
        and str(formal_state.get("manifest_sha256") or "")
        == _sha256(bound_manifest)
        and _resolve_from(FORMAL_STATE, formal_state.get("manifest") or "")
        == bound_manifest
    ):
        raise ValueError("formal controller authority mismatch")
    if not _valid_acceptance(
        formal_result,
        path=FORMAL_RESULT,
        mode="formal",
        scales={5, 10, 20, 30, 50},
    ):
        raise ValueError("formal full20 acceptance mismatch")

    manifest_payload = _load(bound_manifest)
    if validate_qg2_runtime_oracle_authority(manifest_payload) != (
        SELECTIVE_TRAINING_ONLY_MODE
    ):
        raise ValueError("selective runtime Oracle evidence mode mismatch")
    if str(manifest_payload.get("runtime_policy_id") or "") != (
        QG2_RUNTIME_POLICY_ID
    ):
        raise ValueError("selective runtime policy mismatch")
    if str(manifest_payload.get("runtime_implementation_hash") or "") != (
        qg2_runtime_implementation_hash()
    ):
        raise ValueError("selective runtime implementation drift")
    return bound_manifest


def build_selective_candidate_payload(
    manifest: Path,
    *,
    tests: Mapping[str, Any],
) -> dict[str, Any]:
    if len(NATIVE_EXTENSIONS) != 1:
        raise ValueError("selective finalizer requires one Native extension")
    manifest_payload = _load(manifest)
    checkpoint = _bound_manifest_path(
        manifest,
        manifest_payload.get("checkpoint_path") or "",
        manifest_payload.get("checkpoint_sha256") or "",
        "checkpoint",
    )
    oracle_freeze = _load(ORACLE_FREEZE)
    action_hashes = {
        str(scale): str(value)
        for scale, value in dict(
            oracle_freeze.get("required_exact_action_policy_hashes_by_scale")
            or {}
        ).items()
        if str(value)
    }
    if set(action_hashes) != {"30", "50"}:
        raise ValueError("scale30/50 exact action policy hashes missing")
    frozen_paths = (
        CONFIG, ORACLE_FREEZE, ORACLE, TRAINING, SELECTOR,
        CALIBRATION_STATE, CALIBRATION, RISK, EVIDENCE_STATE, EVIDENCE,
        MANIFEST, AUTHORITY, E2E_STATE, E2E_RESULT, FORMAL_STATE,
        FORMAL_RESULT, RUNTIME_SOURCE, MODEL_SOURCE, AUTHORITY_SOURCE,
        EVIDENCE_SOURCE, CALIBRATION_AUTHORITY_SOURCE, BINDER_SOURCE,
        BINDING_SOURCE, E2E_SOURCE,
        FORMAL_SOURCE, Path(__file__).resolve(),
        checkpoint, NATIVE_EXTENSIONS[0],
    )
    frozen = {_relative(path): _sha256(path) for path in frozen_paths}
    return {
        "schema_version": CANDIDATE_SCHEMA,
        "status": "FROZEN_EXPERIMENT_CANDIDATE",
        "model_id": "P0V5_QG2_LABEL_STATE_GAT_SELECTIVE_RUNTIME_V1",
        "frozen_at_local": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "production_default": False,
        "production_switch_performed": False,
        "historical_baselines_unchanged": True,
        "p0v4_changed": False,
        "p0v5_exact_control_changed": False,
        "exact_control_freeze_id": (
            "P0V4_V5_BIDIRECTIONAL_EXACT_FINAL_CANDIDATE"
        ),
        "selected_exact_config": _relative(CONFIG),
        "selected_exact_config_sha256": _sha256(CONFIG),
        "source_engine_hash": str(
            oracle_freeze.get("source_exact_engine_hash") or ""
        ),
        "exact_action_policy_hashes_by_scale": action_hashes,
        "runtime_policy_id": QG2_RUNTIME_POLICY_ID,
        "runtime_implementation_hash": qg2_runtime_implementation_hash(),
        "oracle_evidence_mode": SELECTIVE_TRAINING_ONLY_MODE,
        "fixed_arm_geomean_and_bootstrap_report_only": True,
        "allowed_scales": list(manifest_payload.get("allowed_scales") or ()),
        "scale5_10_20_runtime_bypass": True,
        "fallback_action": "Q0",
        "all_arms_rejected_action": "Q0",
        "context_selector_in_final_runtime": False,
        "ordering_only": True,
        "can_filter": False,
        "can_prune": False,
        "can_change_bound": False,
        "can_certify": False,
        "guidance_bucket_width": float(
            manifest_payload["guidance_bucket_width"]
        ),
        "manifest_path": _relative(manifest),
        "manifest_sha256": _sha256(manifest),
        "checkpoint_path": _relative(checkpoint),
        "checkpoint_sha256": _sha256(checkpoint),
        "oracle_summary": _relative(ORACLE),
        "oracle_summary_sha256": _sha256(ORACLE),
        "training_report": _relative(TRAINING),
        "training_report_sha256": _sha256(TRAINING),
        "selector_report": _relative(SELECTOR),
        "selector_report_sha256": _sha256(SELECTOR),
        "calibration_report": _relative(CALIBRATION),
        "calibration_report_sha256": _sha256(CALIBRATION),
        "calibration_risk_audit": _relative(RISK),
        "calibration_risk_audit_sha256": _sha256(RISK),
        "selective_oracle_evidence": _relative(EVIDENCE),
        "selective_oracle_evidence_sha256": _sha256(EVIDENCE),
        "development_acceptance": _relative(E2E_RESULT),
        "development_acceptance_sha256": _sha256(E2E_RESULT),
        "formal_acceptance": _relative(FORMAL_RESULT),
        "formal_acceptance_sha256": _sha256(FORMAL_RESULT),
        "regression_and_native_tests": dict(tests),
        "development_e2e_passed": True,
        "formal_full20_passed": True,
        "frozen_file_sha256": frozen,
    }


def audit_selective_candidate_payload(payload: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    if payload.get("schema_version") != CANDIDATE_SCHEMA:
        issues.append("candidate_schema_mismatch")
    if payload.get("status") != "FROZEN_EXPERIMENT_CANDIDATE":
        issues.append("candidate_status_mismatch")
    if bool(payload.get("production_default")) or bool(
        payload.get("production_switch_performed")
    ):
        issues.append("production_scope_expansion")
    if not bool(
        payload.get("historical_baselines_unchanged")
        and not payload.get("p0v4_changed")
        and not payload.get("p0v5_exact_control_changed")
        and payload.get("exact_control_freeze_id")
        == "P0V4_V5_BIDIRECTIONAL_EXACT_FINAL_CANDIDATE"
        and payload.get("scale5_10_20_runtime_bypass")
        and set(payload.get("allowed_scales") or ()) == {30, 50}
        and payload.get("fallback_action") == "Q0"
        and payload.get("all_arms_rejected_action") == "Q0"
        and not payload.get("context_selector_in_final_runtime")
        and payload.get("ordering_only")
        and not payload.get("can_filter")
        and not payload.get("can_prune")
        and not payload.get("can_change_bound")
        and not payload.get("can_certify")
        and payload.get("development_e2e_passed")
        and payload.get("formal_full20_passed")
        and bool((payload.get("regression_and_native_tests") or {}).get("passed"))
    ):
        issues.append("candidate_exact_safe_acceptance_contract_mismatch")
    if str(payload.get("runtime_policy_id") or "") != QG2_RUNTIME_POLICY_ID:
        issues.append("candidate_runtime_policy_mismatch")
    if str(payload.get("runtime_implementation_hash") or "") != (
        qg2_runtime_implementation_hash()
    ):
        issues.append("candidate_runtime_implementation_drift")
    if set(payload.get("exact_action_policy_hashes_by_scale") or {}) != {
        "30", "50"
    }:
        issues.append("candidate_action_policy_binding_mismatch")
    for path_key, hash_key in (
        ("selected_exact_config", "selected_exact_config_sha256"),
        ("manifest_path", "manifest_sha256"),
        ("checkpoint_path", "checkpoint_sha256"),
        ("oracle_summary", "oracle_summary_sha256"),
        ("training_report", "training_report_sha256"),
        ("selector_report", "selector_report_sha256"),
        ("calibration_report", "calibration_report_sha256"),
        ("calibration_risk_audit", "calibration_risk_audit_sha256"),
        ("selective_oracle_evidence", "selective_oracle_evidence_sha256"),
        ("development_acceptance", "development_acceptance_sha256"),
        ("formal_acceptance", "formal_acceptance_sha256"),
    ):
        path = _resolve(payload.get(path_key) or "")
        if not path.is_file() or _sha256(path) != str(payload.get(hash_key) or ""):
            issues.append(f"candidate_direct_binding_failed:{path_key}")
    frozen = dict(payload.get("frozen_file_sha256") or {})
    if not frozen:
        issues.append("candidate_frozen_universe_empty")
    for raw_path, expected in frozen.items():
        path = _resolve(raw_path)
        if not path.is_file() or _sha256(path) != str(expected):
            issues.append(f"candidate_frozen_drift:{raw_path}")
    return sorted(set(issues))


def _compare_authority_payloads(
    observed: Mapping[str, Any],
    rebuilt: Mapping[str, Any],
) -> None:
    keys = (set(observed) | set(rebuilt)) - {"generated_at"}
    mismatches = [key for key in sorted(keys) if observed.get(key) != rebuilt.get(key)]
    if mismatches:
        raise ValueError(
            "selective runtime authority reconstruction mismatch:"
            + ",".join(mismatches)
        )


def _valid_acceptance(
    payload: Mapping[str, Any],
    *,
    path: Path,
    mode: str,
    scales: set[int],
) -> bool:
    if not bool(
        path.is_file()
        and payload.get("schema_version") == ACCEPTANCE_SCHEMA
        and payload.get("mode") == mode
        and payload.get("passed")
        and int(payload.get("violation_count") or 0) == 0
        and {int(value) for value in (payload.get("by_scale") or {})} == scales
    ):
        return False
    for prefix in ("control", "guided"):
        root = _resolve_from(path, payload.get(f"{prefix}_root") or "")
        if (
            not root.is_dir()
            or formal.base._acceptance_artifact_hash(root)
            != str(payload.get(f"{prefix}_root_hash") or "")
        ):
            return False
    return True


def _run_tests() -> dict[str, Any]:
    commands = (
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            *(str(path) for path in sorted(ROOT.glob("tests/test_p0v5_qg2_*.py"))),
        ],
        ["ctest", "--test-dir", str(BUILD), "--output-on-failure"],
    )
    rows = []
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        rows.append({
            "command": command,
            "returncode": int(completed.returncode),
            "stdout_tail": completed.stdout[-4000:],
            "stderr_tail": completed.stderr[-4000:],
        })
    return {
        "passed": all(row["returncode"] == 0 for row in rows),
        "commands": rows,
    }


def _write_audit(
    complete: bool,
    issues: list[str],
    *,
    tests: Mapping[str, Any],
) -> None:
    _write(AUDIT, {
        "schema_version": AUDIT_SCHEMA,
        "objective": "P0V5 Proof-Tail GAT V2 Q0-Anchored Label-State Guidance",
        "complete": bool(complete),
        "issue_count": len(issues),
        "issues": list(issues),
        "candidate": str(CANDIDATE) if CANDIDATE.is_file() else None,
        "candidate_sha256": _sha256(CANDIDATE) if CANDIDATE.is_file() else None,
        "regression_and_native_tests": dict(tests),
        "production_switch_performed": False,
        "fallback_action": "Q0",
    })


def _bound_manifest_path(
    source: Path,
    raw_path: str | Path,
    expected_sha256: str,
    label: str,
) -> Path:
    path = _resolve_from(source, raw_path)
    if not path.is_file() or _sha256(path) != str(expected_sha256):
        raise ValueError(f"selective candidate {label} binding mismatch")
    return path


def _matching_formal_controller(pid: int) -> bool:
    try:
        command = Path(f"/proc/{int(pid)}/cmdline").read_bytes().replace(
            b"\0", b" "
        ).decode("utf-8", errors="replace")
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return "run_p0v5_qg2_selective_runtime_formal_after_e2e.py" in command


def _state(status: str, **extra: Any) -> None:
    _write(STATE, {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_selective_runtime_candidate_finalizer_state.v1"
        ),
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": str(status),
        **extra,
    })


def _resolve_from(source: Path, value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (source.parent / path).resolve()


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: Mapping[str, Any]) -> None:
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

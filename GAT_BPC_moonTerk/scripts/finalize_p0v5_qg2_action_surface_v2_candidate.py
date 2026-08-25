#!/usr/bin/env python3
"""Freeze the action-surface-v2 candidate only after every gate passes."""

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


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
FREEZE = RUN_ROOT / "qg2_action_surface_v2_candidate_finalizer_freeze.json"
FORMAL_STATE = RUN_ROOT / "qg2_action_surface_v2_formal_controller_state.json"
FORMAL_RESULT = RUN_ROOT / "formal_full20_acceptance_qg2_action_surface_v2.json"
E2E_STATE = RUN_ROOT / "qg2_action_surface_v2_e2e_controller_state.json"
E2E_RESULT = RUN_ROOT / "e2e_development_acceptance_qg2_action_surface_v2.json"
ORACLE_FREEZE = RUN_ROOT / "qg2_action_surface_v2_oracle_execution_freeze.json"
STRICT_POST_FREEZE = RUN_ROOT / "qg2_action_surface_v2_post_oracle_freeze.json"
RELAXED_FREEZE = RUN_ROOT / "qg2_action_surface_v2_relaxed_training_freeze.json"
E2E_FREEZE = RUN_ROOT / "qg2_action_surface_v2_e2e_controller_freeze.json"
FORMAL_FREEZE = RUN_ROOT / "qg2_action_surface_v2_formal_controller_freeze.json"
PRE_FREEZE_AUDIT = (
    RUN_ROOT / "p0v5_qg2_action_surface_v2_pre_freeze_audit.json"
)
FINAL_AUDIT = RUN_ROOT / "p0v5_qg2_action_surface_v2_completion_audit.json"
CANDIDATE = (
    RUN_ROOT
    / "P0V5_QG2_ACTION_SURFACE_V2_LABEL_STATE_GAT_candidate_freeze.json"
)
STATE = RUN_ROOT / "qg2_action_surface_v2_candidate_finalizer_state.json"
CONFIG = ROOT / "runs/p0v4_v5_exact_gat_binding_20260731/selected_exact_v5.yaml"
RUNTIME_SOURCE = (
    ROOT / "src/lunar_ice_bpc/guidance/proof_queue_label_state_runtime.py"
)
MODEL_SOURCE = ROOT / "src/lunar_ice_bpc/guidance/proof_queue_label_state_gat.py"
NATIVE_EXTENSIONS = tuple(sorted(
    (ROOT / "build/native-spprc-bidirectional-feasibility-v1").glob(
        "lunar_spprc_native*.so"
    )
))

CALIBRATION_SCHEMA = "lunar_ice_bpc.p0v5_qg2_fresh_process_calibration.v4"
MANIFEST_SCHEMA = "lunar_ice_bpc.p0v5_qg2_manifest.v1"
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
    _state("WAITING_FOR_FORMAL_FULL20_GATE", wait_for_pid=args.wait_for_pid)
    while _matching_formal_controller_alive(args.wait_for_pid):
        print(json.dumps({
            "status": "waiting_for_formal_full20_gate",
            "pid": int(args.wait_for_pid),
        }, sort_keys=True), flush=True)
        time.sleep(poll)

    if not all(path.is_file() for path in (
        FORMAL_STATE,
        FORMAL_RESULT,
        E2E_STATE,
        E2E_RESULT,
    )):
        _state("NOT_STARTED_REQUIRED_ACCEPTANCE_EVIDENCE_MISSING")
        return 2
    formal_state = _load(FORMAL_STATE)
    e2e_state = _load(E2E_STATE)
    formal = _load(FORMAL_RESULT)
    e2e = _load(E2E_RESULT)
    if str(formal_state.get("status") or "") != "FORMAL_FULL20_PASSED":
        _state(
            "NOT_STARTED_FORMAL_FULL20_GATE_FAILED",
            formal_status=formal_state.get("status"),
        )
        return 2
    if not _valid_acceptance(
        formal,
        mode="formal",
        scales={5, 10, 20, 30, 50},
        expected_sha256=str(formal_state.get("result_sha256") or ""),
        path=FORMAL_RESULT,
    ):
        _state("NOT_STARTED_FORMAL_EVIDENCE_INVALID")
        return 2
    if not _valid_acceptance(
        e2e,
        mode="development",
        scales={30, 50},
        expected_sha256=str(e2e_state.get("result_sha256") or ""),
        path=E2E_RESULT,
    ):
        _state("NOT_STARTED_DEVELOPMENT_E2E_EVIDENCE_INVALID")
        return 2

    calibration = _bound_file(
        e2e_state.get("calibration_report"),
        e2e_state.get("calibration_report_sha256"),
        "calibration report",
    )
    if str(calibration) != str(
        Path(str(formal_state.get("calibration_report") or "")).resolve()
    ):
        raise SystemExit("QG2 finalizer calibration authority drift")
    calibration_payload = _load(calibration)
    if not bool(
        calibration_payload.get("schema_version") == CALIBRATION_SCHEMA
        and calibration_payload.get("gate_pass")
        and calibration_payload.get("deployment_authorized")
    ):
        _state("NOT_STARTED_CALIBRATION_NOT_AUTHORIZED")
        return 2
    manifest = _bound_file(
        calibration_payload.get("manifest_path"),
        calibration_payload.get("manifest_sha256"),
        "calibrated manifest",
    )
    if not bool(
        str(manifest) == str(Path(str(e2e_state.get("manifest") or "")).resolve())
        and _sha256(manifest) == str(e2e_state.get("manifest_sha256") or "")
        and str(manifest) == str(Path(str(formal_state.get("manifest") or "")).resolve())
        and _sha256(manifest) == str(formal_state.get("manifest_sha256") or "")
    ):
        raise SystemExit("QG2 finalizer cross-stage manifest drift")
    manifest_payload = _load(manifest)
    if not bool(
        manifest_payload.get("schema_version") == MANIFEST_SCHEMA
        and manifest_payload.get("deployment_authorized")
        and manifest_payload.get("ordering_only")
        and not manifest_payload.get("can_filter")
        and not manifest_payload.get("can_prune")
        and not manifest_payload.get("can_change_bound")
        and not manifest_payload.get("can_certify")
    ):
        raise SystemExit("QG2 finalizer manifest safety contract failed")
    checkpoint = _bound_file(
        manifest_payload.get("checkpoint_path"),
        manifest_payload.get("checkpoint_sha256"),
        "GAT checkpoint",
    )
    if CANDIDATE.exists() or PRE_FREEZE_AUDIT.exists():
        raise SystemExit("QG2 action-surface-v2 finalizer refuses overwrite")

    _state("RUNNING_PRE_FREEZE_COMPLETION_AUDIT")
    preflight = _run_audit(output=PRE_FREEZE_AUDIT, pre_final_freeze=True)
    if preflight != 0:
        _state("PRE_FREEZE_COMPLETION_AUDIT_FAILED", returncode=preflight)
        return preflight
    audit = _load(PRE_FREEZE_AUDIT)
    if not bool(
        audit.get("complete")
        and audit.get("pre_final_freeze")
        and int(audit.get("failed_check_count") or 0) == 0
        and int(audit.get("incomplete_check_count") or 0) == 0
    ):
        _state("PRE_FREEZE_COMPLETION_EVIDENCE_INVALID")
        return 2

    _state("WRITING_INDEPENDENT_EXPERIMENT_CANDIDATE")
    payload = _candidate_payload(
        calibration=calibration,
        calibration_payload=calibration_payload,
        manifest=manifest,
        manifest_payload=manifest_payload,
        checkpoint=checkpoint,
    )
    _write(CANDIDATE, payload)

    _state("RUNNING_FINAL_COMPLETION_AUDIT")
    final_code = _run_audit(output=FINAL_AUDIT, pre_final_freeze=False)
    final = _load(FINAL_AUDIT)
    if final_code != 0 or not bool(final.get("complete")):
        _state(
            "FINAL_COMPLETION_AUDIT_FAILED",
            returncode=final_code,
            candidate=str(CANDIDATE),
        )
        return final_code or 2
    _state(
        "CANDIDATE_FROZEN_AND_AUDIT_COMPLETE",
        candidate=str(CANDIDATE),
        candidate_sha256=_sha256(CANDIDATE),
        completion_audit=str(FINAL_AUDIT),
        completion_audit_sha256=_sha256(FINAL_AUDIT),
        production_switch_performed=False,
        historical_baselines_unchanged=True,
    )
    return 0


def _candidate_payload(
    *,
    calibration: Path,
    calibration_payload: dict,
    manifest: Path,
    manifest_payload: dict,
    checkpoint: Path,
) -> dict:
    if len(NATIVE_EXTENSIONS) != 1:
        raise SystemExit("QG2 finalizer requires exactly one Native extension")
    native = NATIVE_EXTENSIONS[0]
    frozen_paths = (
        FREEZE,
        CONFIG,
        ORACLE_FREEZE,
        STRICT_POST_FREEZE,
        RELAXED_FREEZE,
        E2E_FREEZE,
        FORMAL_FREEZE,
        RUNTIME_SOURCE,
        MODEL_SOURCE,
        calibration,
        manifest,
        checkpoint,
        E2E_STATE,
        E2E_RESULT,
        FORMAL_STATE,
        FORMAL_RESULT,
        PRE_FREEZE_AUDIT,
        native,
    )
    frozen = {_relative(path): _sha256(path) for path in frozen_paths}
    oracle_freeze = _load(ORACLE_FREEZE)
    action_hashes = {
        str(scale): str(digest)
        for scale, digest in dict(
            oracle_freeze.get("required_exact_action_policy_hashes_by_scale")
            or {}
        ).items()
        if str(digest)
    }
    if set(action_hashes) != {"30", "50"}:
        raise SystemExit("QG2 finalizer requires scale30/50 action hashes")
    return {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_action_surface_v2_candidate_freeze.v1"
        ),
        "status": "FROZEN_EXPERIMENT_CANDIDATE",
        "model_id": "P0V5_QG2_ACTION_SURFACE_V2_LABEL_STATE_GAT",
        "collection_id": "qg2_action_surface_v2",
        "frozen_at_local": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "production_default": False,
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
        "exact_action_policy_hashes_by_scale": {
            key: action_hashes[key]
            for key in sorted(action_hashes, key=int)
        },
        "runtime_implementation_hash": str(
            manifest_payload.get("runtime_implementation_hash") or ""
        ),
        "guidance_bucket_width": float(
            manifest_payload["guidance_bucket_width"]
        ),
        "allowed_scales": list(manifest_payload.get("allowed_scales") or ()),
        "scale5_10_20_runtime_bypass": True,
        "manifest_path": _relative(manifest),
        "manifest_sha256": _sha256(manifest),
        "checkpoint_path": _relative(checkpoint),
        "checkpoint_sha256": _sha256(checkpoint),
        "calibration_report": _relative(calibration),
        "calibration_report_sha256": _sha256(calibration),
        "deployment_authorized": bool(
            calibration_payload.get("deployment_authorized")
        ),
        "development_e2e_passed": True,
        "formal_full20_passed": True,
        "pre_freeze_completion_audit": _relative(PRE_FREEZE_AUDIT),
        "pre_freeze_completion_audit_sha256": _sha256(PRE_FREEZE_AUDIT),
        "frozen_file_sha256": frozen,
        "production_switch_performed": False,
    }


def _valid_acceptance(
    payload: dict,
    *,
    mode: str,
    scales: set[int],
    path: Path,
    expected_sha256: str = "",
) -> bool:
    if not bool(
        payload.get("schema_version")
        == "lunar_ice_bpc.p0v5_qg2_paired_acceptance.v1"
        and payload.get("mode") == mode
        and payload.get("passed")
        and int(payload.get("violation_count") or 0) == 0
        and {int(value) for value in (payload.get("by_scale") or {})} == scales
        and (not expected_sha256 or _sha256(path) == expected_sha256)
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


def _run_audit(*, output: Path, pre_final_freeze: bool) -> int:
    command = [
        sys.executable,
        str(ROOT / "scripts/audit_p0v5_qg2_action_surface_v2_completion.py"),
        "--run-tests",
        "--output", str(output),
    ]
    if pre_final_freeze:
        command.append("--pre-final-freeze")
    return subprocess.run(
        command,
        cwd=ROOT,
        env=_python_env(),
        check=False,
    ).returncode


def _bound_file(raw_path, expected_sha256, label: str) -> Path:
    path = _resolve(raw_path or "")
    if not path.is_file() or _sha256(path) != str(expected_sha256 or ""):
        raise SystemExit(f"QG2 finalizer {label} binding mismatch")
    return path


def _matching_formal_controller_alive(pid: int) -> bool:
    path = Path(f"/proc/{int(pid)}/cmdline")
    try:
        command = path.read_bytes().replace(b"\0", b" ").decode(
            "utf-8", errors="replace"
        )
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return "run_p0v5_qg2_action_surface_v2_formal_after_e2e.py" in command


def _python_env() -> dict[str, str]:
    env = dict(os.environ)
    for key in GUIDANCE_ENV_KEYS:
        env.pop(key, None)
    env["PYTHONPATH"] = (
        f"{ROOT / 'src'}:"
        f"{ROOT / 'build/native-spprc-bidirectional-feasibility-v1'}"
    )
    return env


def _validate_freeze() -> dict:
    payload = _load(FREEZE)
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_candidate_finalizer_freeze.v1"
    ):
        raise SystemExit("QG2 action-surface-v2 finalizer freeze mismatch")
    if bool(payload.get("production_default")) or not bool(
        payload.get("development_only")
    ):
        raise SystemExit("QG2 finalizer cannot change production")
    for raw_path, expected in dict(
        payload.get("frozen_file_sha256") or {}
    ).items():
        path = _resolve(raw_path)
        if not path.is_file() or _sha256(path) != str(expected):
            raise SystemExit(f"QG2 finalizer frozen file drift: {path}")
    return payload


def _relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _state(status: str, **extra) -> None:
    payload = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_action_surface_v2_candidate_finalizer_state.v1"
        ),
        "status": str(status),
        **extra,
    }
    _write(STATE, payload)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


if __name__ == "__main__":
    raise SystemExit(main())

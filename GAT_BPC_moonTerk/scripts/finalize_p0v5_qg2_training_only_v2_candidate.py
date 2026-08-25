#!/usr/bin/env python3
"""Freeze training-only-v2 QG2 only after all independent gates pass.

This finalizer is deliberately separate from the historical QG2 controllers.
It waits for the training-only-v2 formal controller, revalidates every
persistent artifact through the dedicated completion audit, writes an
immutable experiment-candidate registry, and reruns the audit including that
registry.  It never changes the P0V4/P0V5 exact control or production default.
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


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
BUILD = ROOT / "build/native-spprc-bidirectional-feasibility-v1"

FREEZE = RUN_ROOT / "qg2_training_only_v2_candidate_finalizer_freeze.json"
STATE = RUN_ROOT / "qg2_training_only_v2_candidate_finalizer_state.json"
PRE_FREEZE_AUDIT = RUN_ROOT / "qg2_training_only_v2_pre_freeze_audit.json"
FINAL_AUDIT = RUN_ROOT / "qg2_training_only_v2_completion_audit.json"
CANDIDATE = (
    RUN_ROOT
    / "P0V5_QG2_LABEL_STATE_GAT_TRAINING_ONLY_V2_candidate_freeze.json"
)

ORACLE_FREEZE = RUN_ROOT / "qg2_action_surface_v2_oracle_execution_freeze.json"
ORACLE = RUN_ROOT / "oracle_qg2_action_surface_v2_stage1.json"
TRAINING_FREEZE = RUN_ROOT / "qg2_action_surface_v2_training_only_v2_freeze.json"
TRAINING_GATE = RUN_ROOT / "qg2_action_surface_v2_training_only_gate_v2.json"
AUTHORIZED_ORACLE = RUN_ROOT / "oracle_qg2_action_surface_v2_training_only_v2_view.json"
TRAINING = RUN_ROOT / "training_qg2_action_surface_v2_training_only_v2/training_report.json"
SELECTOR_FREEZE = RUN_ROOT / "qg2_context_arm_selector_controller_freeze.json"
SELECTOR_STATE = RUN_ROOT / "qg2_context_arm_selector_controller_state.json"
SELECTOR = RUN_ROOT / "context_arm_selector_feasibility_v1/selector_report.json"
CALIBRATION_FREEZE = RUN_ROOT / "qg2_training_only_v2_calibration_controller_freeze.json"
CALIBRATION_STATE = RUN_ROOT / "qg2_training_only_v2_calibration_controller_state.json"
CALIBRATION = RUN_ROOT / "calibration_qg2_action_surface_v2_training_only_v2/calibration_report.json"
RISK_FREEZE = RUN_ROOT / "qg2_calibration_risk_v2_freeze.json"
RISK = RUN_ROOT / "qg2_training_only_v2_calibration_risk_audit.json"
E2E_FREEZE = RUN_ROOT / "qg2_training_only_v2_e2e_controller_freeze.json"
E2E_STATE = RUN_ROOT / "qg2_training_only_v2_e2e_controller_state.json"
E2E = RUN_ROOT / "e2e_training_only_v2_development_acceptance.json"
FORMAL_FREEZE = RUN_ROOT / "qg2_training_only_v2_formal_controller_freeze.json"
FORMAL_STATE = RUN_ROOT / "qg2_training_only_v2_formal_controller_state.json"
FORMAL = RUN_ROOT / "formal_full20_acceptance_qg2_training_only_v2.json"

CONFIG = ROOT / "runs/p0v4_v5_exact_gat_binding_20260731/selected_exact_v5.yaml"
RUNTIME_SOURCE = ROOT / "src/lunar_ice_bpc/guidance/proof_queue_label_state_runtime.py"
MODEL_SOURCE = ROOT / "src/lunar_ice_bpc/guidance/proof_queue_label_state_gat.py"
AUDIT_SCRIPT = ROOT / "scripts/audit_p0v5_qg2_training_only_v2_completion.py"
NATIVE_EXTENSIONS = tuple(sorted(BUILD.glob("lunar_spprc_native*.so")))

ACCEPTANCE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_paired_acceptance.v1"
CALIBRATION_SCHEMA = "lunar_ice_bpc.p0v5_qg2_fresh_process_calibration.v4"
RISK_SCHEMA = "lunar_ice_bpc.p0v5_qg2_calibration_risk_audit.v2"
MANIFEST_SCHEMA = "lunar_ice_bpc.p0v5_qg2_manifest.v1"
TRAINING_SCHEMA = "lunar_ice_bpc.p0v5_qg2_model_comparison.v3"
SELECTOR_SCHEMA = "lunar_ice_bpc.p0v5_qg2_context_arm_selector_feasibility.v1"

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
    _state("WAITING_FOR_TRAINING_ONLY_V2_FORMAL", wait_for_pid=args.wait_for_pid)
    while _matching_formal_controller_alive(args.wait_for_pid):
        print(json.dumps({
            "status": "waiting_for_training_only_v2_formal",
            "pid": int(args.wait_for_pid),
        }, sort_keys=True), flush=True)
        time.sleep(poll)

    required = (
        FORMAL_STATE, FORMAL, E2E_STATE, E2E, CALIBRATION_STATE,
        CALIBRATION, RISK, TRAINING, SELECTOR_STATE, SELECTOR,
    )
    if not all(path.is_file() for path in required):
        _state("NOT_STARTED_REQUIRED_EVIDENCE_MISSING")
        return 2
    if not _preflight_stage_bindings():
        _state("NOT_STARTED_STAGE_BINDING_OR_GATE_FAILED")
        return 2
    if any(path.exists() for path in (CANDIDATE, PRE_FREEZE_AUDIT, FINAL_AUDIT)):
        raise SystemExit("training-only-v2 finalizer refuses overwrite")

    _state("RUNNING_PRE_FREEZE_COMPLETION_AUDIT")
    code = _run_audit(PRE_FREEZE_AUDIT, pre_final_freeze=True)
    if code != 0 or not _audit_passed(PRE_FREEZE_AUDIT, pre_final_freeze=True):
        _state("PRE_FREEZE_COMPLETION_AUDIT_FAILED", returncode=int(code))
        return int(code or 2)

    calibration = _load(CALIBRATION)
    manifest = _bound_file(
        calibration.get("manifest_path"),
        calibration.get("manifest_sha256"),
        "calibrated manifest",
    )
    manifest_payload = _load(manifest)
    checkpoint = _bound_file(
        manifest_payload.get("checkpoint_path"),
        manifest_payload.get("checkpoint_sha256"),
        "GAT checkpoint",
    )
    _state("WRITING_INDEPENDENT_EXPERIMENT_CANDIDATE")
    _write(CANDIDATE, _candidate_payload(
        calibration=calibration,
        manifest=manifest,
        manifest_payload=manifest_payload,
        checkpoint=checkpoint,
    ))

    _state("RUNNING_FINAL_COMPLETION_AUDIT")
    final_code = _run_audit(FINAL_AUDIT, pre_final_freeze=False)
    if final_code != 0 or not _audit_passed(FINAL_AUDIT, pre_final_freeze=False):
        _state(
            "FINAL_COMPLETION_AUDIT_FAILED",
            returncode=int(final_code),
            candidate=str(CANDIDATE),
        )
        return int(final_code or 2)
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


def _preflight_stage_bindings() -> bool:
    formal_state = _load(FORMAL_STATE)
    e2e_state = _load(E2E_STATE)
    calibration_state = _load(CALIBRATION_STATE)
    formal = _load(FORMAL)
    e2e = _load(E2E)
    calibration = _load(CALIBRATION)
    risk = _load(RISK)
    selector = _load(SELECTOR)
    if not bool(
        formal_state.get("status") == "FORMAL_FULL20_PASSED"
        and formal_state.get("result_sha256") == _sha256(FORMAL)
        and formal_state.get("calibration_report_sha256") == _sha256(CALIBRATION)
        and formal_state.get("risk_audit_sha256") == _sha256(RISK)
        and formal_state.get("fallback_action") == "Q0"
        and not bool(formal_state.get("production_switch_performed"))
        and e2e_state.get("status") == "E2E_PASSED_PENDING_FORMAL_FULL20"
        and e2e_state.get("result_sha256") == _sha256(E2E)
        and e2e_state.get("calibration_report_sha256") == _sha256(CALIBRATION)
        and e2e_state.get("risk_audit_sha256") == _sha256(RISK)
        and e2e_state.get("fallback_action") == "Q0"
        and calibration_state.get("status")
        == "CALIBRATION_AND_RISK_AUDIT_PASSED_PENDING_E2E"
        and calibration_state.get("calibration_report_sha256") == _sha256(CALIBRATION)
        and calibration_state.get("risk_audit_sha256") == _sha256(RISK)
        and calibration_state.get("fallback_action") == "Q0"
    ):
        return False
    if not _valid_acceptance(formal, mode="formal", scales={5, 10, 20, 30, 50}):
        return False
    if not _valid_acceptance(e2e, mode="development", scales={30, 50}):
        return False
    if not bool(
        calibration.get("schema_version") == CALIBRATION_SCHEMA
        and calibration.get("gate_pass")
        and calibration.get("deployment_authorized")
        and risk.get("schema_version") == RISK_SCHEMA
        and risk.get("passed")
        and risk.get("deployment_authorized")
        and risk.get("calibration_report_sha256") == _sha256(CALIBRATION)
        and selector.get("schema_version") == SELECTOR_SCHEMA
        and not bool(selector.get("continued_development_recommended"))
        and not bool(selector.get("deployable"))
        and selector.get("fallback_action") == "Q0"
        and selector.get("all_arms_rejected_action") == "Q0"
    ):
        return False
    manifest = _bound_file(
        calibration.get("manifest_path"),
        calibration.get("manifest_sha256"),
        "calibrated manifest",
    )
    if not bool(
        str(manifest) == str(_resolve(e2e_state.get("manifest") or ""))
        and _sha256(manifest) == str(e2e_state.get("manifest_sha256") or "")
        and str(manifest) == str(_resolve(formal_state.get("manifest") or ""))
        and _sha256(manifest) == str(formal_state.get("manifest_sha256") or "")
    ):
        return False
    payload = _load(manifest)
    return bool(
        payload.get("schema_version") == MANIFEST_SCHEMA
        and payload.get("deployment_authorized")
        and payload.get("ordering_only")
        and not payload.get("can_filter")
        and not payload.get("can_prune")
        and not payload.get("can_change_bound")
        and not payload.get("can_certify")
        and payload.get("fallback") == "P0V4_V5_Q0"
        and set(payload.get("allowed_scales") or ()) == {30, 50}
        and _bound_file(
            payload.get("checkpoint_path"),
            payload.get("checkpoint_sha256"),
            "GAT checkpoint",
        ).is_file()
    )


def _candidate_payload(
    *,
    calibration: dict,
    manifest: Path,
    manifest_payload: dict,
    checkpoint: Path,
) -> dict:
    if len(NATIVE_EXTENSIONS) != 1:
        raise SystemExit("training-only-v2 finalizer requires exactly one Native extension")
    oracle_freeze = _load(ORACLE_FREEZE)
    action_hashes = {
        str(scale): str(digest)
        for scale, digest in dict(
            oracle_freeze.get("required_exact_action_policy_hashes_by_scale") or {}
        ).items()
        if str(digest)
    }
    if set(action_hashes) != {"30", "50"}:
        raise SystemExit("training-only-v2 finalizer requires scale30/50 action hashes")
    frozen_paths = (
        FREEZE, CONFIG, ORACLE_FREEZE, ORACLE, TRAINING_FREEZE,
        TRAINING_GATE, AUTHORIZED_ORACLE, TRAINING, SELECTOR_FREEZE,
        SELECTOR_STATE, SELECTOR, CALIBRATION_FREEZE, CALIBRATION_STATE,
        CALIBRATION, RISK_FREEZE, RISK, E2E_FREEZE, E2E_STATE, E2E,
        FORMAL_FREEZE, FORMAL_STATE, FORMAL, RUNTIME_SOURCE, MODEL_SOURCE,
        AUDIT_SCRIPT, manifest, checkpoint, PRE_FREEZE_AUDIT,
        NATIVE_EXTENSIONS[0],
    )
    frozen = {_relative(path): _sha256(path) for path in frozen_paths}
    return {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_training_only_v2_candidate_freeze.v1"
        ),
        "status": "FROZEN_EXPERIMENT_CANDIDATE",
        "model_id": "P0V5_QG2_LABEL_STATE_GAT_TRAINING_ONLY_V2",
        "collection_id": "qg2_action_surface_v2_training_only_v2",
        "frozen_at_local": datetime.now().astimezone().isoformat(timespec="seconds"),
        "production_default": False,
        "production_switch_performed": False,
        "historical_baselines_unchanged": True,
        "p0v4_changed": False,
        "p0v5_exact_control_changed": False,
        "exact_control_freeze_id": "P0V4_V5_BIDIRECTIONAL_EXACT_FINAL_CANDIDATE",
        "selected_exact_config": _relative(CONFIG),
        "selected_exact_config_sha256": _sha256(CONFIG),
        "source_engine_hash": str(oracle_freeze.get("source_exact_engine_hash") or ""),
        "exact_action_policy_hashes_by_scale": {
            key: action_hashes[key] for key in sorted(action_hashes, key=int)
        },
        "guidance_bucket_width": float(manifest_payload["guidance_bucket_width"]),
        "runtime_implementation_hash": str(
            manifest_payload.get("runtime_implementation_hash") or ""
        ),
        "allowed_scales": list(manifest_payload.get("allowed_scales") or ()),
        "scale5_10_20_runtime_bypass": True,
        "fallback_action": "Q0",
        "selector_in_final_runtime": False,
        "selector_report": _relative(SELECTOR),
        "selector_report_sha256": _sha256(SELECTOR),
        "oracle_summary": _relative(ORACLE),
        "oracle_summary_sha256": _sha256(ORACLE),
        "training_report": _relative(TRAINING),
        "training_report_sha256": _sha256(TRAINING),
        "manifest_path": _relative(manifest),
        "manifest_sha256": _sha256(manifest),
        "checkpoint_path": _relative(checkpoint),
        "checkpoint_sha256": _sha256(checkpoint),
        "calibration_report": _relative(CALIBRATION),
        "calibration_report_sha256": _sha256(CALIBRATION),
        "calibration_risk_audit": _relative(RISK),
        "calibration_risk_audit_sha256": _sha256(RISK),
        "deployment_authorized": bool(calibration.get("deployment_authorized")),
        "development_e2e_passed": True,
        "formal_full20_passed": True,
        "development_acceptance": _relative(E2E),
        "development_acceptance_sha256": _sha256(E2E),
        "formal_acceptance": _relative(FORMAL),
        "formal_acceptance_sha256": _sha256(FORMAL),
        "pre_freeze_completion_audit": _relative(PRE_FREEZE_AUDIT),
        "pre_freeze_completion_audit_sha256": _sha256(PRE_FREEZE_AUDIT),
        "frozen_file_sha256": frozen,
    }


def _valid_acceptance(payload: dict, *, mode: str, scales: set[int]) -> bool:
    if not bool(
        payload.get("schema_version") == ACCEPTANCE_SCHEMA
        and payload.get("mode") == mode
        and payload.get("passed")
        and int(payload.get("violation_count") or 0) == 0
        and {int(value) for value in (payload.get("by_scale") or {})} == scales
    ):
        return False
    for prefix in ("control", "guided"):
        root = _resolve(payload.get(f"{prefix}_root") or "")
        observed = _artifact_hash(root) if root.is_dir() else ""
        if not observed or observed != str(payload.get(f"{prefix}_root_hash") or ""):
            return False
    return True


def _artifact_hash(root: Path) -> str:
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


def _run_audit(output: Path, *, pre_final_freeze: bool) -> int:
    command = [
        sys.executable,
        str(AUDIT_SCRIPT),
        "--run-tests",
        "--output", str(output),
    ]
    if pre_final_freeze:
        command.append("--pre-final-freeze")
    return subprocess.run(command, cwd=ROOT, env=_python_env(), check=False).returncode


def _audit_passed(path: Path, *, pre_final_freeze: bool) -> bool:
    if not path.is_file():
        return False
    payload = _load(path)
    return bool(
        payload.get("complete")
        and bool(payload.get("pre_final_freeze")) == pre_final_freeze
        and int(payload.get("failed_check_count") or 0) == 0
        and int(payload.get("incomplete_check_count") or 0) == 0
    )


def _validate_freeze() -> None:
    if not FREEZE.is_file():
        raise SystemExit("training-only-v2 finalizer freeze missing")
    payload = _load(FREEZE)
    if payload.get("schema_version") != "lunar_ice_bpc.p0v5_qg2_training_only_v2_candidate_finalizer_freeze.v1":
        raise SystemExit("training-only-v2 finalizer freeze schema mismatch")
    if not bool(
        payload.get("development_only")
        and not payload.get("deployable")
        and not payload.get("production_default")
        and payload.get("fallback_action") == "Q0"
        and payload.get("historical_baselines_unchanged")
    ):
        raise SystemExit("training-only-v2 finalizer safety mismatch")
    if str(payload.get("formal_controller_freeze_sha256") or "") != _sha256(FORMAL_FREEZE):
        raise SystemExit("training-only-v2 formal-controller freeze drift")
    for raw_path, expected in dict(payload.get("frozen_file_sha256") or {}).items():
        path = _resolve(raw_path)
        if not path.is_file() or _sha256(path) != str(expected):
            raise SystemExit(f"training-only-v2 finalizer frozen drift: {path}")


def _matching_formal_controller_alive(pid: int) -> bool:
    try:
        command = Path(f"/proc/{int(pid)}/cmdline").read_bytes().replace(
            b"\0", b" "
        ).decode("utf-8", errors="replace")
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return "run_p0v5_qg2_training_only_v2_formal_after_e2e.py" in command


def _bound_file(raw_path, expected_sha256, label: str) -> Path:
    path = _resolve(raw_path or "")
    if not path.is_file() or _sha256(path) != str(expected_sha256 or ""):
        raise SystemExit(f"training-only-v2 finalizer {label} binding mismatch")
    return path


def _python_env() -> dict[str, str]:
    env = dict(os.environ)
    for key in GUIDANCE_ENV_KEYS:
        env.pop(key, None)
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{BUILD}"
    return env


def _state(status: str, **extra) -> None:
    _write(STATE, {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_training_only_v2_candidate_finalizer_state.v1",
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": status,
        "production_switch_performed": False,
        **extra,
    })


def _relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


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

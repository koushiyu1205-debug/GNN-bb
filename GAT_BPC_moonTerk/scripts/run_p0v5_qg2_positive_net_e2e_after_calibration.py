#!/usr/bin/env python3
"""Run reversible Q0/GAT E2E after positive-net fresh calibration.

The controller waits for the currently frozen supplemental calibration, emits
the independent positive-net evaluation authority, and runs paired scale30/50
development solves.  It can authorize a formal experiment, never a production
switch.  Every rejected or invalid learned action remains literal Q0.
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

import run_p0v5_qg2_action_surface_v2_e2e_after_calibration as base  # noqa: E402

from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (  # noqa: E402
    QG2_POSITIVE_NET_EVALUATION_GATE_V1,
    qg2_runtime_implementation_hash,
)
from lunar_ice_bpc.guidance.qg2_oracle_evidence import (  # noqa: E402
    SELECTIVE_TRAINING_ONLY_MODE,
)
from lunar_ice_bpc.guidance.qg2_runtime_oracle_authority import (  # noqa: E402
    validate_qg2_runtime_oracle_authority,
)


RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
FREEZE = RUN_ROOT / "qg2_positive_net_e2e_controller_freeze_v2.json"
CALIBRATION_REPORT = (
    RUN_ROOT / "calibration_qg2_combined_v1_base/calibration_report.json"
)
SELECTIVE_EVIDENCE = (
    RUN_ROOT / "qg2_training_only_v2_selective_oracle_evidence.json"
)
POSITIVE_REPORT = RUN_ROOT / "qg2_positive_net_calibration_report.json"
MANIFEST = RUN_ROOT / "qg2_positive_net_evaluation_manifest.json"
TRAINING_REPORT = (
    RUN_ROOT
    / "training_qg2_action_surface_v2_training_only_v2/training_report.json"
)
OUTPUT_ROOT = RUN_ROOT / "e2e_qg2_positive_net_v1"
CONTROL_ROOT = OUTPUT_ROOT / "control"
GUIDED_ROOT = OUTPUT_ROOT / "guided"
RESULT = RUN_ROOT / "e2e_qg2_positive_net_v1_acceptance.json"
STATE = RUN_ROOT / "qg2_positive_net_e2e_state.json"
SIDECAR = ROOT / "scripts/evaluate_p0v5_qg2_positive_net_calibration.py"
ANALYZER = ROOT / "scripts/analyze_p0v5_qg2_positive_net_acceptance.py"

FREEZE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_positive_net_e2e_freeze.v2"
STATE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_positive_net_e2e_state.v1"
POSITIVE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_positive_net_calibration.v1"
MANIFEST_SCHEMA = "lunar_ice_bpc.p0v5_qg2_manifest.v1"
TRAINING_SCHEMA = "lunar_ice_bpc.p0v5_qg2_model_comparison.v3"
ACCEPTANCE_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_positive_net_paired_acceptance.v1"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-for-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = max(1.0, min(60.0, float(args.poll_sec)))
    _validate_freeze()
    _state(
        "WAITING_FOR_COMBINED_FRESH_CALIBRATION",
        wait_for_pid=int(args.wait_for_pid),
    )
    while _matching_calibration_process(args.wait_for_pid):
        time.sleep(poll)

    if not CALIBRATION_REPORT.is_file():
        _state("NOT_STARTED_CALIBRATION_REPORT_MISSING")
        return 2
    try:
        manifest = _ensure_positive_authority()
    except Exception as exc:
        _state(
            "NOT_STARTED_POSITIVE_NET_AUTHORITY_INVALID",
            error=f"{type(exc).__name__}:{exc}",
        )
        return 3
    if manifest is None:
        _state(
            "NOT_STARTED_GAT_POSITIVE_NET_GATE_FAILED",
            positive_report=str(POSITIVE_REPORT),
            positive_report_sha256=(
                _sha256(POSITIVE_REPORT) if POSITIVE_REPORT.is_file() else ""
            ),
            production_switch_authorized=False,
            fallback_action="Q0",
        )
        return 2
    if OUTPUT_ROOT.exists() or RESULT.exists():
        _state("REFUSED_EXISTING_POSITIVE_NET_E2E_OUTPUT")
        return 3

    training = _load(TRAINING_REPORT)
    if (
        training.get("schema_version") != TRAINING_SCHEMA
        or not bool(training.get("oracle_gate_passed"))
        or bool(training.get("deployable"))
    ):
        _state("NOT_STARTED_TRAINING_AUTHORITY_INVALID")
        return 3
    instances = base._heldout_instances(training)
    _state(
        "RUNNING_POSITIVE_NET_EXACT_CONTROL",
        instances=[str(path) for path in instances],
        manifest=str(manifest),
    )
    control_code = _run_acceptance(
        output=CONTROL_ROOT,
        instances=instances,
        manifest=None,
    )
    if control_code not in {0, 1}:
        _state("CONTROL_EXECUTION_ERROR", returncode=int(control_code))
        return int(control_code)

    _state("RUNNING_POSITIVE_NET_QG2", manifest=str(manifest))
    guided_code = _run_acceptance(
        output=GUIDED_ROOT,
        instances=instances,
        manifest=manifest,
    )
    if guided_code not in {0, 1}:
        _state("GUIDED_EXECUTION_ERROR", returncode=int(guided_code))
        return int(guided_code)

    analyzed = subprocess.run(
        [
            sys.executable,
            str(ANALYZER),
            "--control-root", str(CONTROL_ROOT),
            "--guided-root", str(GUIDED_ROOT),
            "--output", str(RESULT),
            "--mode", "development",
        ],
        cwd=ROOT,
        env=_environment(manifest=None),
        check=False,
    )
    if analyzed.returncode not in {0, 2} or not RESULT.is_file():
        _state("ANALYZER_EXECUTION_ERROR", returncode=int(analyzed.returncode))
        return int(analyzed.returncode or 3)
    result = _load(RESULT)
    passed = bool(
        result.get("schema_version") == ACCEPTANCE_SCHEMA
        and result.get("mode") == "positive_net_development"
        and result.get("passed")
        and int(result.get("violation_count") or 0) == 0
    )
    _state(
        (
            "POSITIVE_NET_E2E_PASSED_PENDING_FORMAL"
            if passed
            else "POSITIVE_NET_E2E_GATE_FAILED"
        ),
        positive_report=str(POSITIVE_REPORT),
        positive_report_sha256=_sha256(POSITIVE_REPORT),
        manifest=str(manifest),
        manifest_sha256=_sha256(manifest),
        result=str(RESULT),
        result_sha256=_sha256(RESULT),
        violations=result.get("violations"),
        scale30_50_combined_geomean_wall_ratio=result.get(
            "scale30_50_combined_geomean_wall_ratio"
        ),
        formal_experiment_authorized=passed,
        production_switch_authorized=False,
        fallback_action="Q0",
    )
    return 0 if passed else 2


def _ensure_positive_authority() -> Path | None:
    if not POSITIVE_REPORT.is_file():
        completed = subprocess.run(
            [
                sys.executable,
                str(SIDECAR),
                "--calibration-report", str(CALIBRATION_REPORT),
                "--selective-oracle-evidence", str(SELECTIVE_EVIDENCE),
                "--output", str(POSITIVE_REPORT),
                "--manifest-output", str(MANIFEST),
            ],
            cwd=ROOT,
            env=_environment(manifest=None),
            check=False,
        )
        if completed.returncode not in {0, 2} or not POSITIVE_REPORT.is_file():
            raise ValueError(
                f"positive-net sidecar failed:{completed.returncode}"
            )
    report = _load(POSITIVE_REPORT)
    if report.get("schema_version") != POSITIVE_SCHEMA:
        raise ValueError("positive-net report schema mismatch")
    if (
        not bool(report.get("development_only"))
        or bool(report.get("deployable"))
        or bool(report.get("deployment_authorized"))
        or bool(report.get("production_switch_authorized"))
        or str(report.get("fallback_action") or "") != "Q0"
        or str(report.get("evaluation_gate_policy") or "")
        != QG2_POSITIVE_NET_EVALUATION_GATE_V1
    ):
        raise ValueError("positive-net report safety scope mismatch")
    if str(report.get("calibration_report_sha256") or "") != _sha256(
        CALIBRATION_REPORT
    ):
        raise ValueError("positive-net calibration binding mismatch")
    if str(report.get("selective_oracle_evidence_sha256") or "") != _sha256(
        SELECTIVE_EVIDENCE
    ):
        raise ValueError("positive-net Oracle evidence binding mismatch")
    if not bool(report.get("gat_positive_net_exact_safe_gate_passed")):
        return None
    if not MANIFEST.is_file() or str(
        report.get("evaluation_manifest_sha256") or ""
    ) != _sha256(MANIFEST):
        raise ValueError("positive-net manifest binding mismatch")
    _validate_manifest(_load(MANIFEST))
    return MANIFEST


def _validate_manifest(manifest: Mapping[str, Any]) -> None:
    errors = []
    if manifest.get("schema_version") != MANIFEST_SCHEMA:
        errors.append("manifest_schema_mismatch")
    if str(manifest.get("evaluation_gate_policy") or "") != (
        QG2_POSITIVE_NET_EVALUATION_GATE_V1
    ):
        errors.append("evaluation_gate_policy_mismatch")
    if not bool(manifest.get("evaluation_authorized")) or not bool(
        manifest.get("development_e2e_authorized")
    ):
        errors.append("evaluation_authority_missing")
    if bool(manifest.get("deployment_authorized")) or bool(
        manifest.get("production_switch_authorized")
    ):
        errors.append("production_authority_forbidden")
    if str(manifest.get("fallback") or "") != "P0V4_V5_Q0":
        errors.append("literal_q0_fallback_mismatch")
    if str(manifest.get("runtime_implementation_hash") or "") != (
        qg2_runtime_implementation_hash()
    ):
        errors.append("runtime_implementation_drift")
    if not bool(manifest.get("ordering_only")):
        errors.append("ordering_only_contract_missing")
    for key in ("can_filter", "can_prune", "can_change_bound", "can_certify"):
        if bool(manifest.get(key)):
            errors.append(f"forbidden_authority:{key}")
    try:
        mode = validate_qg2_runtime_oracle_authority(manifest)
    except Exception as exc:
        errors.append(f"runtime_oracle_authority:{type(exc).__name__}:{exc}")
        mode = ""
    if mode != SELECTIVE_TRAINING_ONLY_MODE:
        errors.append("runtime_oracle_mode_mismatch")
    if errors:
        raise ValueError(
            "positive-net manifest validation failed:"
            + ",".join(sorted(set(errors)))
        )


def _run_acceptance(
    *,
    output: Path,
    instances: tuple[Path, ...],
    manifest: Path | None,
) -> int:
    command = [
        sys.executable,
        str(ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"),
        "--config", str(base.CONFIG),
        "--scales", "30", "50",
    ]
    for path in instances:
        command.extend(("--instance", str(path)))
    command.extend(("--output-dir", str(output), "--no-resume"))
    return subprocess.run(
        command,
        cwd=ROOT,
        env=_environment(manifest=manifest),
        check=False,
    ).returncode


def _environment(*, manifest: Path | None) -> dict[str, str]:
    env = dict(os.environ)
    for key in base.GUIDANCE_ENV_KEYS:
        env.pop(key, None)
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{base.BUILD}"
    if manifest is not None:
        env["LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST"] = str(manifest)
        env["LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE"] = "1"
    return env


def _matching_calibration_process(pid: int) -> bool:
    try:
        command = Path(f"/proc/{int(pid)}/cmdline").read_bytes().replace(
            b"\0", b" "
        ).decode("utf-8", errors="replace")
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return bool(
        "run_p0v5_qg2_supplemental_calibration.py" in command
        or "calibrate_p0v5_qg2_models.py" in command
    )


def _validate_freeze() -> None:
    payload = _load(FREEZE)
    if payload.get("schema_version") != FREEZE_SCHEMA:
        raise ValueError("positive-net E2E freeze schema mismatch")
    if (
        not bool(payload.get("development_only"))
        or bool(payload.get("deployable"))
        or bool(payload.get("production_switch_authorized"))
        or str(payload.get("fallback_action") or "") != "Q0"
        or str(payload.get("evaluation_gate_policy") or "")
        != QG2_POSITIVE_NET_EVALUATION_GATE_V1
    ):
        raise ValueError("positive-net E2E freeze safety mismatch")
    for raw_path, expected in dict(payload.get("frozen_file_sha256") or {}).items():
        path = _resolve(raw_path)
        if not path.is_file() or _sha256(path) != str(expected):
            raise ValueError(f"positive-net E2E frozen drift:{path}")


def _state(status: str, **extra: Any) -> None:
    _write(STATE, {
        "schema_version": STATE_SCHEMA,
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": str(status),
        **extra,
    })


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


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

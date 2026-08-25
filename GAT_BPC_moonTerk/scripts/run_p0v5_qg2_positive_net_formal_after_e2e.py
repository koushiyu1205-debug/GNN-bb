#!/usr/bin/env python3
"""Run positive-net formal full20 only after development E2E passes."""

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
import run_p0v5_qg2_positive_net_e2e_after_calibration as e2e  # noqa: E402


RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
FREEZE = RUN_ROOT / "qg2_positive_net_formal_controller_freeze.json"
E2E_STATE = RUN_ROOT / "qg2_positive_net_e2e_state.json"
E2E_RESULT = RUN_ROOT / "e2e_qg2_positive_net_v1_acceptance.json"
OUTPUT_ROOT = RUN_ROOT / "formal_full20_qg2_positive_net_v1"
CONTROL_ROOT = OUTPUT_ROOT / "control"
GUIDED_ROOT = OUTPUT_ROOT / "guided"
RESULT = RUN_ROOT / "formal_full20_qg2_positive_net_v1_acceptance.json"
STATE = RUN_ROOT / "qg2_positive_net_formal_state.json"
ANALYZER = ROOT / "scripts/analyze_p0v5_qg2_positive_net_acceptance.py"

FREEZE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_positive_net_formal_freeze.v1"
STATE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_positive_net_formal_state.v1"
E2E_STATE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_positive_net_e2e_state.v1"
E2E_ACCEPTANCE_SCHEMA = (
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
        "WAITING_FOR_POSITIVE_NET_DEVELOPMENT_E2E",
        wait_for_pid=int(args.wait_for_pid),
    )
    while _matching_e2e_controller(args.wait_for_pid):
        time.sleep(poll)

    if not E2E_STATE.is_file() or not E2E_RESULT.is_file():
        _state("NOT_STARTED_POSITIVE_NET_E2E_EVIDENCE_MISSING")
        return 2
    try:
        manifest = _validate_e2e_authority(
            state=_load(E2E_STATE),
            result=_load(E2E_RESULT),
        )
    except Exception as exc:
        _state(
            "NOT_STARTED_POSITIVE_NET_E2E_EVIDENCE_INVALID",
            error=f"{type(exc).__name__}:{exc}",
        )
        return 3
    if OUTPUT_ROOT.exists() or RESULT.exists():
        _state("REFUSED_EXISTING_POSITIVE_NET_FORMAL_OUTPUT")
        return 3

    _state("RUNNING_POSITIVE_NET_FORMAL_EXACT_CONTROL")
    control_code = _run_acceptance(output=CONTROL_ROOT, manifest=None)
    if control_code not in {0, 1}:
        _state("CONTROL_EXECUTION_ERROR", returncode=int(control_code))
        return int(control_code)
    _state("RUNNING_POSITIVE_NET_FORMAL_QG2", manifest=str(manifest))
    guided_code = _run_acceptance(output=GUIDED_ROOT, manifest=manifest)
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
            "--mode", "formal",
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
        result.get("schema_version") == E2E_ACCEPTANCE_SCHEMA
        and result.get("mode") == "positive_net_formal"
        and result.get("passed")
        and int(result.get("violation_count") or 0) == 0
        and {int(value) for value in (result.get("by_scale") or {})}
        == {5, 10, 20, 30, 50}
    )
    _state(
        (
            "POSITIVE_NET_FORMAL_FULL20_PASSED"
            if passed
            else "POSITIVE_NET_FORMAL_FULL20_GATE_FAILED"
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
        scale30_50_combined_geomean_wall_ratio=result.get(
            "scale30_50_combined_geomean_wall_ratio"
        ),
        candidate_freeze_permitted=passed,
        production_switch_performed=False,
        fallback_action="Q0",
    )
    return 0 if passed else 2


def _validate_e2e_authority(
    *, state: Mapping[str, Any], result: Mapping[str, Any]
) -> Path:
    errors = []
    if state.get("schema_version") != E2E_STATE_SCHEMA:
        errors.append("e2e_state_schema_mismatch")
    if str(state.get("status") or "") != (
        "POSITIVE_NET_E2E_PASSED_PENDING_FORMAL"
    ):
        errors.append("e2e_state_not_authorized")
    if not bool(state.get("formal_experiment_authorized")):
        errors.append("formal_experiment_not_authorized")
    if bool(state.get("production_switch_authorized")):
        errors.append("production_scope_expansion")
    if str(state.get("fallback_action") or "") != "Q0":
        errors.append("literal_q0_fallback_mismatch")
    if str(state.get("result_sha256") or "") != _sha256(E2E_RESULT):
        errors.append("e2e_result_hash_mismatch")
    if not bool(
        result.get("schema_version") == E2E_ACCEPTANCE_SCHEMA
        and result.get("mode") == "positive_net_development"
        and result.get("passed")
        and int(result.get("violation_count") or 0) == 0
        and {int(value) for value in (result.get("by_scale") or {})}
        == {30, 50}
    ):
        errors.append("development_e2e_acceptance_mismatch")
    for prefix in ("control", "guided"):
        root = _resolve_relative(
            E2E_RESULT, result.get(f"{prefix}_root") or ""
        )
        if (
            not root.is_dir()
            or base._acceptance_artifact_hash(root)
            != str(result.get(f"{prefix}_root_hash") or "")
        ):
            errors.append(f"development_{prefix}_artifact_hash_mismatch")
    manifest = _resolve_relative(
        E2E_STATE, state.get("manifest") or ""
    )
    if not manifest.is_file():
        errors.append("evaluation_manifest_missing")
    elif str(state.get("manifest_sha256") or "") != _sha256(manifest):
        errors.append("evaluation_manifest_hash_mismatch")
    else:
        payload = _load(manifest)
        try:
            e2e._validate_manifest(payload)
        except Exception as exc:
            errors.append(f"evaluation_manifest:{type(exc).__name__}:{exc}")
        if {int(value) for value in payload.get("allowed_scales") or ()} != {
            30, 50
        }:
            errors.append("evaluation_manifest_allowed_scales_mismatch")
        if not list(payload.get("allowed_exact_engine_hashes") or ()):
            errors.append("evaluation_manifest_engine_allowlist_missing")
        if not list(payload.get("allowed_exact_action_policy_hashes") or ()):
            errors.append("evaluation_manifest_action_policy_allowlist_missing")
        checkpoint = _resolve_relative(
            manifest, payload.get("checkpoint_path") or ""
        )
        if not checkpoint.is_file():
            errors.append("evaluation_manifest_checkpoint_missing")
        elif str(payload.get("checkpoint_sha256") or "") != _sha256(
            checkpoint
        ):
            errors.append("evaluation_manifest_checkpoint_hash_mismatch")
    if errors:
        raise ValueError(
            "positive-net formal authority failed:"
            + ",".join(sorted(set(errors)))
        )
    return manifest


def _run_acceptance(*, output: Path, manifest: Path | None) -> int:
    return subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"),
            "--config", str(base.CONFIG),
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
    for key in base.GUIDANCE_ENV_KEYS:
        env.pop(key, None)
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{base.BUILD}"
    if manifest is not None:
        env["LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST"] = str(manifest)
        env["LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE"] = "1"
    return env


def _matching_e2e_controller(pid: int) -> bool:
    try:
        command = Path(f"/proc/{int(pid)}/cmdline").read_bytes().replace(
            b"\0", b" "
        ).decode("utf-8", errors="replace")
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return "run_p0v5_qg2_positive_net_e2e_after_calibration.py" in command


def _validate_freeze() -> None:
    payload = _load(FREEZE)
    if payload.get("schema_version") != FREEZE_SCHEMA:
        raise ValueError("positive-net formal freeze schema mismatch")
    if (
        not bool(payload.get("development_only"))
        or bool(payload.get("production_default"))
        or str(payload.get("fallback_action") or "") != "Q0"
        or not bool(payload.get("positive_net_e2e_required"))
    ):
        raise ValueError("positive-net formal freeze safety mismatch")
    for raw_path, expected in dict(payload.get("frozen_file_sha256") or {}).items():
        path = _resolve(raw_path)
        if not path.is_file() or _sha256(path) != str(expected):
            raise ValueError(f"positive-net formal frozen drift:{path}")


def _resolve_relative(source: Path, value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (
        source.parent / path
    ).resolve()


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _state(status: str, **extra: Any) -> None:
    _write(STATE, {
        "schema_version": STATE_SCHEMA,
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

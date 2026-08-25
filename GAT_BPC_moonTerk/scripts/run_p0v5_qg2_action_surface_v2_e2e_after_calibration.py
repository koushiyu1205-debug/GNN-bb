#!/usr/bin/env python3
"""Run action-surface-v2 development E2E after an authorized calibration.

The strict Oracle path is preferred.  The relaxed path is eligible only when
it has independently passed the unchanged calibration report gate.  This file
is inert until a post-calibration freeze containing its final hash is created.
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
FREEZE = RUN_ROOT / "qg2_action_surface_v2_e2e_controller_freeze.json"
STRICT_STATE = RUN_ROOT / "qg2_action_surface_v2_post_oracle_state.json"
RELAXED_STATE = (
    RUN_ROOT / "qg2_action_surface_v2_relaxed_post_oracle_state.json"
)
STRICT_TRAINING = RUN_ROOT / "training_qg2_action_surface_v2/training_report.json"
RELAXED_TRAINING = (
    RUN_ROOT / "training_qg2_action_surface_v2_relaxed/training_report.json"
)
STRICT_CALIBRATION = (
    RUN_ROOT / "calibration_qg2_action_surface_v2/calibration_report.json"
)
RELAXED_CALIBRATION = (
    RUN_ROOT
    / "calibration_qg2_action_surface_v2_relaxed/calibration_report.json"
)
CORPUS_MANIFEST = ROOT / "data/p0v5_qg2_oracle_development_v3/manifest.json"
OUTPUT_ROOT = RUN_ROOT / "e2e_qg2_action_surface_v2"
CONTROL_ROOT = OUTPUT_ROOT / "control"
GUIDED_ROOT = OUTPUT_ROOT / "guided"
RESULT = RUN_ROOT / "e2e_development_acceptance_qg2_action_surface_v2.json"
STATE = RUN_ROOT / "qg2_action_surface_v2_e2e_controller_state.json"
BUILD = ROOT / "build/native-spprc-bidirectional-feasibility-v1"
CONFIG = ROOT / "runs/p0v4_v5_exact_gat_binding_20260731/selected_exact_v5.yaml"

TRAINING_SCHEMA = "lunar_ice_bpc.p0v5_qg2_model_comparison.v3"
CALIBRATION_SCHEMA = "lunar_ice_bpc.p0v5_qg2_fresh_process_calibration.v4"
SUPERVISION_SCHEMA = "lunar_ice_bpc.p0v5_qg2_action_reachable_supervision.v2"
ACTION_SURFACE = "same_terminal_class_and_reduced_cost_bucket.v1"
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
    parser.add_argument(
        "--wait-for-pid",
        type=int,
        action="append",
        required=True,
        help="Repeat for every strict/relaxed post-Oracle controller.",
    )
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = max(1.0, min(60.0, float(args.poll_sec)))
    _validate_freeze()
    wait_pids = tuple(dict.fromkeys(int(pid) for pid in args.wait_for_pid))
    _state("WAITING_FOR_CALIBRATION_GATE", wait_for_pids=list(wait_pids))
    while any(_matching_post_controller_alive(pid) for pid in wait_pids):
        print(json.dumps({
            "status": "waiting_for_calibration_gate",
            "pids": list(wait_pids),
        }, sort_keys=True), flush=True)
        time.sleep(poll)

    authority = _select_calibration_authority()
    if authority is None:
        _state("NOT_STARTED_CALIBRATION_GATE_FAILED")
        return 2
    calibration = _load(authority["calibration_report"])
    training = _load(authority["training_report"])
    manifest = _validated_manifest(calibration)
    if OUTPUT_ROOT.exists() or RESULT.exists():
        raise SystemExit("QG2 action-surface-v2 E2E refuses overwrite or resume")
    instances = _heldout_instances(training)

    _state(
        "RUNNING_EXACT_CONTROL",
        authority=authority["authority"],
        training_report=str(authority["training_report"]),
        calibration_report=str(authority["calibration_report"]),
        instances=[str(path) for path in instances],
    )
    control_code = _run_acceptance(
        output=CONTROL_ROOT,
        instances=instances,
        manifest=None,
    )
    if control_code not in {0, 1}:
        _state("CONTROL_EXECUTION_ERROR", returncode=control_code)
        return control_code
    _state("RUNNING_QG2_GUIDED", authority=authority["authority"])
    guided_code = _run_acceptance(
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
        env=_environment(manifest=None),
        check=False,
    )
    if analyzed.returncode not in {0, 2}:
        _state("ANALYZER_EXECUTION_ERROR", returncode=analyzed.returncode)
        return analyzed.returncode
    result = _load(RESULT)
    passed = bool(result.get("passed"))
    _state(
        "E2E_PASSED" if passed else "E2E_GATE_FAILED",
        authority=authority["authority"],
        calibration_report=str(authority["calibration_report"]),
        calibration_report_sha256=_sha256(authority["calibration_report"]),
        manifest=str(manifest),
        manifest_sha256=_sha256(manifest),
        result=str(RESULT),
        result_sha256=_sha256(RESULT),
        violations=result.get("violations"),
    )
    return 0 if passed else 2


def _select_calibration_authority() -> dict | None:
    candidates = (
        {
            "authority": "strict_oracle_gate",
            "state": STRICT_STATE,
            "required_status": "CALIBRATION_PASSED",
            "training_report": STRICT_TRAINING,
            "calibration_report": STRICT_CALIBRATION,
        },
        {
            "authority": "relaxed_training_gate_strict_calibration",
            "state": RELAXED_STATE,
            "required_status": "CALIBRATION_PASSED_PENDING_HELDOUT_E2E",
            "training_report": RELAXED_TRAINING,
            "calibration_report": RELAXED_CALIBRATION,
        },
    )
    for candidate in candidates:
        if not all(Path(candidate[key]).is_file() for key in (
            "state", "training_report", "calibration_report"
        )):
            continue
        state = _load(candidate["state"])
        training = _load(candidate["training_report"])
        calibration = _load(candidate["calibration_report"])
        if str(state.get("status") or "") != candidate["required_status"]:
            continue
        if _authorized_reports(
            training,
            calibration,
            training_path=candidate["training_report"],
        ):
            return candidate
    return None


def _authorized_reports(
    training: dict,
    calibration: dict,
    *,
    training_path: Path,
) -> bool:
    return bool(
        training.get("schema_version") == TRAINING_SCHEMA
        and training.get("oracle_gate_passed")
        and training.get("supervision_schema_version") == SUPERVISION_SCHEMA
        and training.get("queue_action_surface") == ACTION_SURFACE
        and not bool(training.get("deployable"))
        and calibration.get("schema_version") == CALIBRATION_SCHEMA
        and calibration.get("gate_pass")
        and calibration.get("deployment_authorized")
        and str(calibration.get("training_report_sha256") or "")
        == _sha256(training_path)
    )


def _validated_manifest(calibration: dict) -> Path:
    manifest = Path(str(calibration.get("manifest_path") or "")).resolve()
    if (
        not manifest.is_file()
        or _sha256(manifest) != str(calibration.get("manifest_sha256") or "")
    ):
        raise SystemExit("QG2 calibrated manifest binding mismatch")
    return manifest


def _heldout_instances(training: dict) -> tuple[Path, ...]:
    split_path = Path(str(training.get("split_path") or "")).resolve()
    if (
        not split_path.is_file()
        or _sha256(split_path) != str(training.get("split_sha256") or "")
    ):
        raise SystemExit("QG2 E2E instance split binding mismatch")
    assignments = dict(_load(split_path).get("assignments") or {})
    corpus = _load(CORPUS_MANIFEST)
    selected = []
    for scale in (30, 50):
        rows = [
            row for row in corpus.get("rows") or ()
            if int(row["scale"]) == scale
            and assignments.get(str(row["instance_content_hash"])) == "heldout"
        ]
        rows.sort(key=lambda row: int(row["index"]))
        if len(rows) < 5:
            raise SystemExit(
                f"QG2 E2E has fewer than five heldout scale{scale} instances"
            )
        selected.extend(_resolve(row["path"]) for row in rows[:5])
    return tuple(selected)


def _run_acceptance(
    *,
    output: Path,
    instances: tuple[Path, ...],
    manifest: Path | None,
) -> int:
    command = [
        sys.executable,
        str(ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"),
        "--config", str(CONFIG),
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
    for key in GUIDANCE_ENV_KEYS:
        env.pop(key, None)
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{BUILD}"
    if manifest is not None:
        env["LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST"] = str(manifest)
    return env


def _matching_post_controller_alive(pid: int) -> bool:
    path = Path(f"/proc/{int(pid)}/cmdline")
    try:
        command = path.read_bytes().replace(b"\0", b" ").decode(
            "utf-8", errors="replace"
        )
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return bool(
        "run_p0v5_qg2_action_surface_v2_training_after_oracle.py" in command
        or "run_p0v5_qg2_relaxed_training_after_oracle.py" in command
    )


def _validate_freeze() -> dict:
    payload = _load(FREEZE)
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_e2e_controller_freeze.v1"
    ):
        raise SystemExit("QG2 action-surface-v2 E2E freeze schema mismatch")
    if not bool(payload.get("development_only")) or bool(
        payload.get("deployable")
    ):
        raise SystemExit("QG2 action-surface-v2 E2E freeze safety mismatch")
    for raw_path, expected in dict(
        payload.get("frozen_file_sha256") or {}
    ).items():
        path = _resolve(raw_path)
        if not path.is_file() or _sha256(path) != str(expected):
            raise SystemExit(f"QG2 E2E frozen file drift: {path}")
    return payload


def _state(status: str, **extra) -> None:
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_e2e_controller_state.v1",
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

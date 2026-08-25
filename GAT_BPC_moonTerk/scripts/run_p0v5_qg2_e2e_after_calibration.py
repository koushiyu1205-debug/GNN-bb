#!/usr/bin/env python3
"""Run paired scale30/50 development E2E only after QG2 calibration passes."""

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
FREEZE = RUN_ROOT / "qg2_clean_v1_e2e_controller_freeze.json"
POST_STATE = RUN_ROOT / "qg2_clean_v1_post_oracle_controller_state.json"
TRAINING_REPORT = RUN_ROOT / "training_qg2_clean_v1/training_report.json"
CALIBRATION_REPORT = RUN_ROOT / "calibration_qg2_clean_v1/calibration_report.json"
CORPUS_MANIFEST = ROOT / "data/p0v5_qg2_oracle_development_v3/manifest.json"
OUTPUT_ROOT = RUN_ROOT / "e2e_qg2_clean_v1"
CONTROL_ROOT = OUTPUT_ROOT / "control"
GUIDED_ROOT = OUTPUT_ROOT / "guided"
RESULT = RUN_ROOT / "e2e_development_acceptance.json"
STATE = RUN_ROOT / "qg2_clean_v1_e2e_controller_state.json"
BUILD = ROOT / "build/native-spprc-bidirectional-feasibility-v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-for-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = max(1.0, min(60.0, float(args.poll_sec)))
    _validate_freeze()
    _state("WAITING_FOR_CALIBRATION_GATE", wait_for_pid=args.wait_for_pid)
    while _matching_post_controller_alive(args.wait_for_pid):
        print(json.dumps({
            "status": "waiting_for_calibration_gate",
            "pid": args.wait_for_pid,
        }, sort_keys=True), flush=True)
        time.sleep(poll)
    post = _load(POST_STATE)
    if str(post.get("status") or "") != "CALIBRATION_PASSED":
        _state(
            "NOT_STARTED_CALIBRATION_GATE_FAILED",
            calibration_status=post.get("status"),
        )
        return 2
    calibration = _load(CALIBRATION_REPORT)
    if not bool(
        calibration.get("gate_pass")
        and calibration.get("deployment_authorized")
    ):
        _state("NOT_STARTED_CALIBRATION_REPORT_NOT_AUTHORIZED")
        return 2
    manifest = Path(str(calibration.get("manifest_path") or "")).resolve()
    if (
        not manifest.is_file()
        or _sha256(manifest) != str(calibration.get("manifest_sha256") or "")
    ):
        raise SystemExit("QG2 calibrated manifest binding mismatch")
    if OUTPUT_ROOT.exists() or RESULT.exists():
        raise SystemExit("QG2 E2E controller refuses overwrite or resume")
    instances = _heldout_instances()

    _state("RUNNING_EXACT_CONTROL", instances=[str(path) for path in instances])
    control_code = _run_acceptance(
        output=CONTROL_ROOT,
        instances=instances,
        manifest=None,
    )
    if control_code not in {0, 1}:
        _state("CONTROL_EXECUTION_ERROR", returncode=control_code)
        return control_code
    _state("RUNNING_QG2_GUIDED")
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
        result=str(RESULT),
        result_sha256=_sha256(RESULT),
        violations=result.get("violations"),
    )
    return 0 if passed else 2


def _heldout_instances() -> tuple[Path, ...]:
    training = _load(TRAINING_REPORT)
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
            raise SystemExit(f"QG2 E2E has fewer than five heldout scale{scale} instances")
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
        "--config",
        str(ROOT / "runs/p0v4_v5_exact_gat_binding_20260731/selected_exact_v5.yaml"),
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
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{BUILD}"
    env.pop("LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR", None)
    env.pop("LUNAR_ICE_P0V5_QG2_SNAPSHOT_MAX_PER_INSTANCE", None)
    env.pop("LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST", None)
    env.pop("LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE", None)
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
    return "run_p0v5_qg2_training_after_oracle.py" in command


def _validate_freeze() -> None:
    payload = _load(FREEZE)
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_e2e_controller_freeze.v1"
    ):
        raise SystemExit("QG2 E2E controller freeze schema mismatch")
    for raw_path, expected in dict(
        payload.get("frozen_file_sha256") or {}
    ).items():
        path = _resolve(raw_path)
        if not path.is_file() or _sha256(path) != str(expected):
            raise SystemExit(f"QG2 E2E frozen file drift: {path}")


def _state(status: str, **extra) -> None:
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_e2e_controller_state.v1",
        "status": status,
        **extra,
    }
    temporary = STATE.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, STATE)


def _resolve(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

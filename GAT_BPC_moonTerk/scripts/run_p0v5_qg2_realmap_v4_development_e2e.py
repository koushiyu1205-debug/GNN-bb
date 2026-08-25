#!/usr/bin/env python3
"""Freeze and run paired V4 development E2E on heldout real-map instances."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/p0v5_qg2_v4_realmap_gat_first_20260806"
BUILD = ROOT / "build/native-spprc-bidirectional-feasibility-v1"
CONFIG = ROOT / "runs/p0v4_v5_exact_gat_binding_20260731/selected_exact_v5.yaml"
SPLIT = RUN / "realmap_v4_instance_split.json"
CONTROLS_STATE = RUN / "realmap_v4_controls_state.json"
COMPARISON = RUN / "gat_mlp_linear_comparison_v4.json"
ORACLE_EXECUTION_FREEZE = RUN / "realmap_v4_oracle_execution_freeze.json"
SELECTOR = RUN / "selector_gat_v4/training_report.json"
FRESH = RUN / "selector_gat_fresh_heldout_v4/fresh_heldout.json"
MANIFEST = RUN / "p0v5_qg2_v4_gat_development_manifest.json"
FREEZE = RUN / "realmap_v4_development_e2e_freeze.json"
OUTPUT = RUN / "development_e2e_v4"
CONTROL = OUTPUT / "control"
GUIDED = OUTPUT / "guided"
RESULT = RUN / "development_e2e_v4_acceptance.json"
STATE = RUN / "realmap_v4_development_e2e_state.json"

GUIDANCE_ENV_KEYS = (
    "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST",
    "LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE",
    "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_MANIFEST",
    "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_EVALUATION_MODE",
    "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR",
)


def main() -> int:
    _validate_execution_freeze()
    _validate_controls()
    if not MANIFEST.is_file():
        code = _run([
            sys.executable,
            str(ROOT / "scripts/freeze_p0v5_qg2_v3_selector_candidate.py"),
            "--selector-training-report", str(SELECTOR),
            "--fresh-report", str(FRESH),
            "--output", str(MANIFEST),
        ], env=_environment(None))
        if code != 0 or not MANIFEST.is_file():
            return _stop("GAT_CANDIDATE_MANIFEST_FREEZE_FAILED", code)
    manifest = _load(MANIFEST)
    _validate_manifest(manifest)
    instances = _heldout_instances()
    _freeze(instances)

    _state("RUNNING_DEVELOPMENT_EXACT_CONTROL", instances=[str(x) for x in instances])
    control = _run_acceptance(CONTROL, instances, manifest=None)
    if control not in {0, 1}:
        return _stop("DEVELOPMENT_CONTROL_EXECUTION_ERROR", control)
    _state("RUNNING_DEVELOPMENT_GAT_SELECTOR", manifest=str(MANIFEST))
    guided = _run_acceptance(GUIDED, instances, manifest=MANIFEST)
    if guided not in {0, 1}:
        return _stop("DEVELOPMENT_GUIDED_EXECUTION_ERROR", guided)
    analyzed = _run([
        sys.executable,
        str(ROOT / "scripts/analyze_p0v5_qg2_realmap_v4_acceptance.py"),
        "--control-root", str(CONTROL),
        "--guided-root", str(GUIDED),
        "--output", str(RESULT),
        "--mode", "development",
        "--gate-profile", "v4_positive_net",
    ], env=_environment(None))
    if analyzed not in {0, 2} or not RESULT.is_file():
        return _stop("DEVELOPMENT_ANALYZER_ERROR", analyzed)
    result = _load(RESULT)
    passed = bool(result.get("passed"))
    _state(
        "DEVELOPMENT_E2E_PASSED_PENDING_FORMAL"
        if passed else "DEVELOPMENT_E2E_GATE_FAILED",
        manifest=str(MANIFEST),
        manifest_sha256=_sha256(MANIFEST),
        result=str(RESULT),
        result_sha256=_sha256(RESULT),
        violations=result.get("violations"),
        production_switch_performed=False,
    )
    return 0 if passed else 2


def _validate_controls() -> None:
    state = _load_required(CONTROLS_STATE)
    comparison = _load_required(COMPARISON)
    if not (
        str(state.get("status") or "")
        == "CONTROLS_COMPLETE_GAT_E2E_MAY_START"
        and str(state.get("comparison_sha256") or "") == _sha256(COMPARISON)
        and bool(comparison.get("all_controls_safe"))
        and not bool(comparison.get("deployment_authorized"))
    ):
        raise SystemExit("V4 controls are not complete and safe")


def _validate_manifest(payload) -> None:
    if not (
        bool(payload.get("development_only"))
        and not bool(payload.get("deployable"))
        and bool(payload.get("development_e2e_authorized"))
        and not bool(payload.get("deployment_authorized"))
        and str(payload.get("fallback_action") or "") == "Q0"
        and str(payload.get("selector_training_report_sha256") or "")
        == _sha256(SELECTOR)
        and str(payload.get("fresh_report_sha256") or "") == _sha256(FRESH)
    ):
        raise SystemExit("V4 development manifest authority invalid")


def _heldout_instances() -> tuple[Path, ...]:
    split = _load_required(SPLIT)
    rows = [
        dict(row) for row in split.get("rows") or ()
        if str(row.get("partition") or "") == "heldout"
    ]
    counts = {
        scale: sum(int(row["scale"]) == scale for row in rows)
        for scale in (30, 50)
    }
    if counts != {30: 4, 50: 4}:
        raise SystemExit(f"V4 heldout split must be 4+4: {counts}")
    paths = tuple(
        Path(str(row["instance_path"])).resolve()
        for row in sorted(rows, key=lambda x: (int(x["scale"]), str(x["instance_content_hash"])))
    )
    if any(not path.is_file() for path in paths):
        raise SystemExit("V4 heldout instance missing")
    return paths


def _freeze(instances: tuple[Path, ...]) -> None:
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_realmap_v4_development_e2e_freeze.v1",
        "development_only": True,
        "deployable": False,
        "fallback_action": "Q0",
        "instance_paths": [str(path) for path in instances],
        "manifest": str(MANIFEST),
        "manifest_sha256": _sha256(MANIFEST),
        "split": str(SPLIT),
        "split_sha256": _sha256(SPLIT),
        "comparison": str(COMPARISON),
        "comparison_sha256": _sha256(COMPARISON),
        "oracle_execution_freeze": str(ORACLE_EXECUTION_FREEZE),
        "oracle_execution_freeze_sha256": _sha256(ORACLE_EXECUTION_FREEZE),
        "config": str(CONFIG),
        "config_sha256": _sha256(CONFIG),
        "frozen_file_sha256": {
            str(path.relative_to(ROOT)): _sha256(path)
            for path in (
                ROOT / "scripts/run_p0v5_qg2_realmap_v4_development_e2e.py",
                ROOT / "scripts/analyze_p0v5_qg2_realmap_v4_acceptance.py",
                ROOT / "scripts/analyze_p0v5_qg2_paired_acceptance.py",
                ROOT / "scripts/freeze_p0v5_qg2_v3_selector_candidate.py",
                ROOT / "src/lunar_ice_bpc/guidance/qg2_v3_selector_runtime.py",
            )
        },
        "production_switch_authorized": False,
    }
    if FREEZE.is_file():
        if _load(FREEZE) != payload:
            raise SystemExit("V4 development E2E freeze drift")
    else:
        _write(FREEZE, payload)


def _run_acceptance(output, instances, *, manifest) -> int:
    command = [
        sys.executable,
        str(ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"),
        "--config", str(CONFIG),
        "--scales", "30", "50",
    ]
    for path in instances:
        command.extend(("--instance", str(path)))
    command.extend(("--output-dir", str(output), "--resume"))
    return _run(command, env=_environment(manifest))


def _validate_execution_freeze() -> None:
    payload = _load_required(ORACLE_EXECUTION_FREEZE)
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_oracle_execution_freeze.v2"
    ):
        raise SystemExit("V4 Oracle execution freeze schema mismatch")
    for raw_path, expected in dict(
        payload.get("frozen_file_sha256") or {}
    ).items():
        path = Path(str(raw_path))
        path = path if path.is_absolute() else ROOT / path
        if not path.is_file() or _sha256(path) != str(expected):
            raise SystemExit(f"V4 Oracle execution source drift: {path}")


def _environment(manifest) -> dict[str, str]:
    env = dict(os.environ)
    for key in GUIDANCE_ENV_KEYS:
        env.pop(key, None)
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{BUILD}"
    if manifest is not None:
        env["LUNAR_ICE_P0V5_QG2_V3_SELECTOR_MANIFEST"] = str(manifest)
        env["LUNAR_ICE_P0V5_QG2_V3_SELECTOR_EVALUATION_MODE"] = "1"
    return env


def _run(command, *, env) -> int:
    return subprocess.run(command, cwd=ROOT, env=env, check=False).returncode


def _stop(status, code) -> int:
    _state(status, returncode=int(code or 2))
    return int(code or 2)


def _state(status, **extra) -> None:
    _write(STATE, {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_realmap_v4_development_e2e_state.v1",
        "status": str(status),
        **extra,
    })


def _load_required(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"required V4 artifact missing: {path}")
    return _load(path)


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

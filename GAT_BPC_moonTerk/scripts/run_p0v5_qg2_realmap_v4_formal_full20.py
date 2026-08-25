#!/usr/bin/env python3
"""Run paired scale5/10/20/30/50 full20 after V4 development E2E passes."""

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
MANIFEST = RUN / "p0v5_qg2_v4_gat_development_manifest.json"
E2E_FREEZE = RUN / "realmap_v4_development_e2e_freeze.json"
E2E_STATE = RUN / "realmap_v4_development_e2e_state.json"
E2E_RESULT = RUN / "development_e2e_v4_acceptance.json"
ORACLE_EXECUTION_FREEZE = RUN / "realmap_v4_oracle_execution_freeze.json"
FREEZE = RUN / "realmap_v4_formal_full20_freeze.json"
OUTPUT = RUN / "formal_full20_v4"
CONTROL = OUTPUT / "control"
GUIDED = OUTPUT / "guided"
RESULT = RUN / "formal_full20_v4_acceptance.json"
STATE = RUN / "realmap_v4_formal_full20_state.json"
ACCEPTANCE_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_realmap_v4_paired_acceptance.v1"
)

GUIDANCE_ENV_KEYS = (
    "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST",
    "LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE",
    "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_MANIFEST",
    "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_EVALUATION_MODE",
    "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR",
)


def main() -> int:
    _validate_execution_freeze()
    _validate_e2e()
    _freeze()
    _state("RUNNING_FORMAL_FULL20_EXACT_CONTROL")
    control = _run_acceptance(CONTROL, manifest=None)
    if control not in {0, 1}:
        return _stop("FORMAL_CONTROL_EXECUTION_ERROR", control)
    _state("RUNNING_FORMAL_FULL20_GAT_SELECTOR", manifest=str(MANIFEST))
    guided = _run_acceptance(GUIDED, manifest=MANIFEST)
    if guided not in {0, 1}:
        return _stop("FORMAL_GUIDED_EXECUTION_ERROR", guided)
    analyzed = _run([
        sys.executable,
        str(ROOT / "scripts/analyze_p0v5_qg2_realmap_v4_acceptance.py"),
        "--control-root", str(CONTROL),
        "--guided-root", str(GUIDED),
        "--output", str(RESULT),
        "--mode", "formal",
        "--gate-profile", "v4_positive_net",
    ], env=_environment(None))
    if analyzed not in {0, 2} or not RESULT.is_file():
        return _stop("FORMAL_ANALYZER_ERROR", analyzed)
    result = _load(RESULT)
    passed = bool(result.get("passed"))
    _state(
        "FORMAL_FULL20_PASSED_CANDIDATE_MAY_FREEZE"
        if passed else "FORMAL_FULL20_GATE_FAILED",
        manifest=str(MANIFEST),
        manifest_sha256=_sha256(MANIFEST),
        result=str(RESULT),
        result_sha256=_sha256(RESULT),
        violations=result.get("violations"),
        candidate_freeze_permitted=passed,
        production_switch_performed=False,
    )
    return 0 if passed else 2


def _validate_e2e() -> None:
    state = _load_required(E2E_STATE)
    result = _load_required(E2E_RESULT)
    if not (
        str(state.get("status") or "")
        == "DEVELOPMENT_E2E_PASSED_PENDING_FORMAL"
        and str(state.get("manifest_sha256") or "") == _sha256(MANIFEST)
        and str(state.get("result_sha256") or "") == _sha256(E2E_RESULT)
        and bool(result.get("passed"))
        and str(result.get("schema_version") or "") == ACCEPTANCE_SCHEMA
        and str(result.get("mode") or "") == "development"
        and str(result.get("gate_profile") or "") == "v4_positive_net"
        and int(result.get("violation_count") or 0) == 0
        and _load_required(E2E_FREEZE).get("manifest_sha256")
        == _sha256(MANIFEST)
        and _load_required(E2E_FREEZE).get(
            "oracle_execution_freeze_sha256"
        ) == _sha256(ORACLE_EXECUTION_FREEZE)
    ):
        raise SystemExit("V4 formal full20 lacks bound development E2E authority")


def _freeze() -> None:
    extension = tuple(sorted(BUILD.glob("lunar_spprc_native*.so")))
    if len(extension) != 1:
        raise SystemExit("V4 formal full20 requires one Native extension")
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_realmap_v4_formal_freeze.v1",
        "development_only": False,
        "production_default": False,
        "fallback_action": "Q0",
        "formal_scales": [5, 10, 20, 30, 50],
        "formal_instances_per_scale": 20,
        "manifest": str(MANIFEST),
        "manifest_sha256": _sha256(MANIFEST),
        "development_e2e_result": str(E2E_RESULT),
        "development_e2e_result_sha256": _sha256(E2E_RESULT),
        "development_e2e_freeze_sha256": _sha256(E2E_FREEZE),
        "oracle_execution_freeze": str(ORACLE_EXECUTION_FREEZE),
        "oracle_execution_freeze_sha256": _sha256(ORACLE_EXECUTION_FREEZE),
        "config": str(CONFIG),
        "config_sha256": _sha256(CONFIG),
        "native_extension_sha256": _sha256(extension[0]),
        "frozen_file_sha256": {
            str(path.relative_to(ROOT)): _sha256(path)
            for path in (
                ROOT / "scripts/run_p0v5_qg2_realmap_v4_formal_full20.py",
                ROOT / "scripts/analyze_p0v5_qg2_realmap_v4_acceptance.py",
                ROOT / "scripts/analyze_p0v5_qg2_paired_acceptance.py",
                ROOT / "src/lunar_ice_bpc/guidance/qg2_v3_selector_runtime.py",
            )
        },
        "production_switch_authorized": False,
    }
    if FREEZE.is_file():
        if _load(FREEZE) != payload:
            raise SystemExit("V4 formal full20 freeze drift")
    else:
        _write(FREEZE, payload)


def _run_acceptance(output, *, manifest) -> int:
    return _run([
        sys.executable,
        str(ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"),
        "--config", str(CONFIG),
        "--scales", "5", "10", "20", "30", "50",
        "--limit", "20",
        "--output-dir", str(output),
        "--resume",
    ], env=_environment(manifest))


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
        "schema_version": "lunar_ice_bpc.p0v5_qg2_realmap_v4_formal_state.v1",
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

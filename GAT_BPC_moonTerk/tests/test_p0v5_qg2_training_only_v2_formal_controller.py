from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_p0v5_qg2_training_only_v2_formal_after_e2e.py"
SPEC = importlib.util.spec_from_file_location(
    "qg2_training_only_v2_formal_controller", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _configure(monkeypatch, tmp_path: Path):
    run = tmp_path / "run"
    e2e_state = run / "e2e_state.json"
    e2e_result = run / "e2e_result.json"
    risk = run / "risk.json"
    calibration = run / "calibration.json"
    manifest = run / "manifest.json"
    control_e2e = run / "development/control"
    guided_e2e = run / "development/guided"
    output_root = run / "formal"
    control = output_root / "control"
    guided = output_root / "guided"
    result = run / "formal_result.json"
    state = run / "formal_state.json"
    _write(control_e2e / "b4_2_cold_exact_state.json", {"arm": "control"})
    _write(guided_e2e / "b4_2_cold_exact_state.json", {"arm": "guided"})
    _write(manifest, {"schema_version": "manifest.v1"})
    _write(calibration, {
        "schema_version": MODULE.base.CALIBRATION_SCHEMA,
        "gate_pass": True,
        "deployment_authorized": True,
        "manifest_path": str(manifest),
        "manifest_sha256": MODULE._sha256(manifest),
    })
    _write(risk, {
        "schema_version": MODULE.RISK_SCHEMA,
        "passed": True,
        "deployment_authorized": True,
        "calibration_report_sha256": MODULE._sha256(calibration),
    })
    _write(e2e_result, {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_paired_acceptance.v1",
        "mode": "development",
        "passed": True,
        "violation_count": 0,
        "violations": [],
        "by_scale": {"30": {}, "50": {}},
        "control_root": str(control_e2e),
        "guided_root": str(guided_e2e),
        "control_root_hash": MODULE.base._acceptance_artifact_hash(control_e2e),
        "guided_root_hash": MODULE.base._acceptance_artifact_hash(guided_e2e),
    })
    _write(e2e_state, {
        "status": "E2E_PASSED_PENDING_FORMAL_FULL20",
        "result_sha256": MODULE._sha256(e2e_result),
        "calibration_report": str(calibration),
        "calibration_report_sha256": MODULE._sha256(calibration),
        "risk_audit_sha256": MODULE._sha256(risk),
        "manifest": str(manifest),
        "manifest_sha256": MODULE._sha256(manifest),
        "deployment_authorized": False,
        "fallback_action": "Q0",
    })
    for name, value in {
        "E2E_STATE": e2e_state,
        "E2E_RESULT": e2e_result,
        "RISK_AUDIT": risk,
        "OUTPUT_ROOT": output_root,
        "CONTROL_ROOT": control,
        "GUIDED_ROOT": guided,
        "RESULT": result,
        "STATE": state,
    }.items():
        monkeypatch.setattr(MODULE, name, value)
    monkeypatch.setattr(MODULE, "_validate_freeze", lambda: None)
    monkeypatch.setattr(MODULE, "_matching_e2e_controller_alive", lambda _pid: False)
    monkeypatch.setattr(
        sys,
        "argv",
        ["formal-controller", "--wait-for-pid", "123"],
    )
    return {
        "e2e_state": e2e_state,
        "e2e_result": e2e_result,
        "risk": risk,
        "calibration": calibration,
        "manifest": manifest,
        "result": result,
        "state": state,
    }


def test_freeze_preserves_full20_scope_and_no_production_switch() -> None:
    MODULE._validate_freeze()
    freeze = json.loads(MODULE.FREEZE.read_text(encoding="utf-8"))
    assert freeze["scales"] == [5, 10, 20, 30, 50]
    assert freeze["instances_per_scale"] == 20
    assert freeze["small_scale_gat_inference_required_zero"]
    assert freeze["production_switch_forbidden"]
    assert freeze["fallback_action"] == "Q0"


def test_valid_development_e2e_binding_requires_literal_q0_state(
    monkeypatch,
    tmp_path: Path,
) -> None:
    paths = _configure(monkeypatch, tmp_path)
    payload = json.loads(paths["e2e_result"].read_text(encoding="utf-8"))
    state = json.loads(paths["e2e_state"].read_text(encoding="utf-8"))
    assert MODULE._valid_e2e_result(payload, state)
    state["fallback_action"] = "QB1"
    assert not MODULE._valid_e2e_result(payload, state)


def test_authorized_formal_path_runs_control_guided_and_only_permits_freeze(
    monkeypatch,
    tmp_path: Path,
) -> None:
    paths = _configure(monkeypatch, tmp_path)
    calls = []

    def fake_acceptance(**kwargs):
        calls.append(kwargs)
        return 0

    monkeypatch.setattr(MODULE.base, "_run_acceptance", fake_acceptance)

    def fake_run(command, **_kwargs):
        assert "analyze_p0v5_qg2_paired_acceptance.py" in command[1]
        _write(paths["result"], {"passed": True, "violations": []})
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(MODULE.subprocess, "run", fake_run)

    assert MODULE.main() == 0
    assert len(calls) == 2
    assert calls[0]["manifest"] is None
    assert calls[1]["manifest"] == paths["manifest"]
    state = json.loads(paths["state"].read_text(encoding="utf-8"))
    assert state["status"] == "FORMAL_FULL20_PASSED"
    assert state["candidate_freeze_permitted"]
    assert state["production_switch_performed"] is False
    assert state["fallback_action"] == "Q0"

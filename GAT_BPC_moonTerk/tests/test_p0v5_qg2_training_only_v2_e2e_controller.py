from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_p0v5_qg2_training_only_v2_e2e_after_calibration.py"
SPEC = importlib.util.spec_from_file_location(
    "qg2_training_only_v2_e2e_controller", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _configure(monkeypatch, tmp_path: Path, *, selector_recommended: bool):
    run = tmp_path / "run"
    training = run / "training.json"
    manifest = run / "manifest.json"
    calibration = run / "calibration.json"
    risk = run / "risk.json"
    selector = run / "selector.json"
    calibration_state = run / "calibration_state.json"
    output_root = run / "e2e"
    control = output_root / "control"
    guided = output_root / "guided"
    result = run / "result.json"
    state = run / "state.json"
    _write(training, {
        "schema_version": MODULE.TRAINING_SCHEMA,
        "oracle_gate_passed": True,
        "supervision_schema_version": MODULE.base.SUPERVISION_SCHEMA,
        "queue_action_surface": MODULE.base.ACTION_SURFACE,
        "deployable": False,
    })
    _write(manifest, {"schema_version": "manifest.v1"})
    _write(calibration, {
        "schema_version": MODULE.CALIBRATION_SCHEMA,
        "gate_pass": True,
        "deployment_authorized": True,
        "training_report_sha256": MODULE._sha256(training),
        "manifest_path": str(manifest),
        "manifest_sha256": MODULE._sha256(manifest),
    })
    _write(risk, {
        "schema_version": MODULE.RISK_SCHEMA,
        "passed": True,
        "deployment_authorized": True,
        "calibration_report_sha256": MODULE._sha256(calibration),
    })
    _write(selector, {
        "schema_version": MODULE.SELECTOR_SCHEMA,
        "continued_development_recommended": selector_recommended,
        "fallback_action": "Q0",
        "deployable": False,
    })
    _write(calibration_state, {
        "status": "CALIBRATION_AND_RISK_AUDIT_PASSED_PENDING_E2E",
        "calibration_report_sha256": MODULE._sha256(calibration),
        "risk_audit_sha256": MODULE._sha256(risk),
        "deployment_authorized": False,
    })
    for name, value in {
        "CALIBRATION_STATE": calibration_state,
        "TRAINING_REPORT": training,
        "CALIBRATION_REPORT": calibration,
        "RISK_AUDIT": risk,
        "SELECTOR_REPORT": selector,
        "OUTPUT_ROOT": output_root,
        "CONTROL_ROOT": control,
        "GUIDED_ROOT": guided,
        "RESULT": result,
        "STATE": state,
    }.items():
        monkeypatch.setattr(MODULE, name, value)
    monkeypatch.setattr(MODULE, "_validate_freeze", lambda: None)
    monkeypatch.setattr(
        MODULE, "_matching_calibration_controller_alive", lambda _pid: False
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["e2e-controller", "--wait-for-pid", "123"],
    )
    return {
        "training": training,
        "manifest": manifest,
        "calibration": calibration,
        "risk": risk,
        "selector": selector,
        "result": result,
        "state": state,
    }


def test_freeze_requires_calibration_risk_and_q0_fallback() -> None:
    MODULE._validate_freeze()
    freeze = json.loads(MODULE.FREEZE.read_text(encoding="utf-8"))
    assert freeze["risk_audit_required"]
    assert freeze["fallback_action"] == "Q0"
    assert freeze["deployable"] is False


def test_selector_recommendation_blocks_qg2_only_e2e(
    monkeypatch,
    tmp_path: Path,
) -> None:
    paths = _configure(monkeypatch, tmp_path, selector_recommended=True)
    calls = []
    monkeypatch.setattr(
        MODULE.base,
        "_run_acceptance",
        lambda **kwargs: calls.append(kwargs) or 0,
    )

    assert MODULE.main() == 2
    assert calls == []
    state = json.loads(paths["state"].read_text(encoding="utf-8"))
    assert state["status"] == "NOT_STARTED_CALIBRATION_OR_RISK_GATE_FAILED"


def test_authorized_path_runs_paired_control_then_guided_and_stays_nondeployable(
    monkeypatch,
    tmp_path: Path,
) -> None:
    paths = _configure(monkeypatch, tmp_path, selector_recommended=False)
    instances = (tmp_path / "scale30.json", tmp_path / "scale50.json")
    calls = []
    monkeypatch.setattr(
        MODULE.base, "_heldout_instances", lambda _training: instances
    )

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
    assert state["status"] == "E2E_PASSED_PENDING_FORMAL_FULL20"
    assert state["deployment_authorized"] is False
    assert state["fallback_action"] == "Q0"

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "scripts/run_p0v5_qg2_training_only_v2_calibration_after_selector.py"
)
SPEC = importlib.util.spec_from_file_location(
    "qg2_training_only_v2_calibration_controller", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _configure(monkeypatch, tmp_path: Path, *, recommended: bool) -> dict:
    run = tmp_path / "run"
    oracle = run / "oracle.json"
    index = run / "index.json"
    training = run / "training/training_report.json"
    selector = run / "selector/selector_report.json"
    selector_state = run / "selector_state.json"
    manifest = run / "supplement.json"
    output_dir = run / "calibration"
    output = output_dir / "calibration_report.json"
    risk = run / "risk.json"
    state = run / "state.json"
    _write(index, {"schema_version": "index.v1", "rows": []})
    _write(oracle, {
        "schema_version": MODULE.ORACLE_SCHEMA,
        "oracle_gate": {"passed": True},
        "deployable": False,
        "source_state_index": str(index),
        "source_state_index_sha256": MODULE._sha256(index),
    })
    _write(training, {
        "schema_version": MODULE.TRAINING_SCHEMA,
        "oracle_gate_passed": True,
        "deployable": False,
        "oracle_summary": str(oracle),
        "oracle_summary_sha256": MODULE._sha256(oracle),
    })
    _write(selector, {
        "schema_version": MODULE.SELECTOR_SCHEMA,
        "deployable": False,
        "starts_solver_process": False,
        "changes_qg2": False,
        "fallback_action": "Q0",
        "all_arms_rejected_action": "Q0",
        "training_report_sha256": MODULE._sha256(training),
        "oracle_summary_sha256": MODULE._sha256(oracle),
        "continued_development_recommended": recommended,
    })
    _write(selector_state, {
        "selector_report_sha256": MODULE._sha256(selector),
        "deployment_authorized": False,
    })
    for name, value in {
        "STATE": state,
        "SELECTOR_REPORT": selector,
        "SELECTOR_STATE": selector_state,
        "TRAINING_REPORT": training,
        "MANIFEST": manifest,
        "OUTPUT_DIR": output_dir,
        "OUTPUT": output,
        "RISK_AUDIT": risk,
    }.items():
        monkeypatch.setattr(MODULE, name, value)
    monkeypatch.setattr(MODULE, "_validate_freeze", lambda: None)
    monkeypatch.setattr(
        MODULE, "_matching_selector_controller_alive", lambda _pid: False
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["calibration-controller", "--wait-for-pid", "123"],
    )
    return {
        "run": run,
        "oracle": oracle,
        "index": index,
        "training": training,
        "selector": selector,
        "manifest": manifest,
        "output": output,
        "risk": risk,
        "state": state,
    }


def test_freeze_binds_selector_before_calibration_and_literal_q0() -> None:
    MODULE._validate_freeze()
    freeze = json.loads(MODULE.FREEZE.read_text(encoding="utf-8"))
    assert freeze["selector_precedes_calibration"]
    assert freeze["fallback_action"] == "Q0"
    assert freeze["deployable"] is False


def test_recommended_selector_stops_before_wrong_action_surface_calibration(
    monkeypatch,
    tmp_path: Path,
) -> None:
    paths = _configure(monkeypatch, tmp_path, recommended=True)
    calls = []
    monkeypatch.setattr(
        MODULE.subprocess,
        "run",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    assert MODULE.main() == 0
    assert calls == []
    state = json.loads(paths["state"].read_text(encoding="utf-8"))
    assert state["status"] == (
        "PENDING_COMBINED_QG2_CONTEXT_SELECTOR_IMPLEMENTATION"
    )
    assert state["calibration_started"] is False
    assert state["deployment_authorized"] is False
    assert state["fallback_action"] == "Q0"


def test_nonrecommended_selector_runs_base_calibration_and_risk_veto(
    monkeypatch,
    tmp_path: Path,
) -> None:
    paths = _configure(monkeypatch, tmp_path, recommended=False)
    calls = []

    def fake_run(command, **_kwargs):
        calls.append(command)
        if "build_p0v5_qg2_supplemental_calibration_manifest.py" in command[1]:
            _write(paths["manifest"], {
                "sufficient": True,
                "rows": [{
                    "source_engine_hash": "engine",
                    "source_exact_action_policy_hash": "policy",
                }],
            })
        elif "run_p0v5_qg2_supplemental_calibration.py" in command[1]:
            _write(paths["output"], {
                "schema_version": MODULE.CALIBRATION_SCHEMA,
                "gate_pass": True,
                "deployment_authorized": True,
            })
        else:
            assert "audit_p0v5_qg2_calibration_risk_v2.py" in command[1]
            _write(paths["risk"], {
                "schema_version": MODULE.RISK_AUDIT_SCHEMA,
                "passed": True,
                "deployment_authorized": True,
                "calibration_report_sha256": MODULE._sha256(paths["output"]),
            })
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(MODULE.subprocess, "run", fake_run)

    assert MODULE.main() == 0
    assert len(calls) == 3
    state = json.loads(paths["state"].read_text(encoding="utf-8"))
    assert state["status"] == (
        "CALIBRATION_AND_RISK_AUDIT_PASSED_PENDING_E2E"
    )
    assert state["base_calibration_passed"]
    assert state["risk_audit_passed"]
    assert state["deployment_authorized"] is False
    assert state["fallback_action"] == "Q0"

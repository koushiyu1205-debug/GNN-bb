from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_p0v5_qg2_positive_net_e2e_after_calibration.py"
SPEC = importlib.util.spec_from_file_location("qg2_positive_net_e2e", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_positive_net_e2e_freeze_is_current_and_nondeployable() -> None:
    MODULE._validate_freeze()
    freeze = json.loads(MODULE.FREEZE.read_text(encoding="utf-8"))
    assert freeze["minimum_speedup_gate_enabled"] is False
    assert freeze["combined_scale30_50_ratio_must_be_below"] == 1.0
    assert freeze["deployable"] is False
    assert freeze["production_switch_authorized"] is False
    assert freeze["fallback_action"] == "Q0"


def test_positive_net_e2e_environment_is_evaluation_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "manifest.json"
    _write(manifest, {})
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST", "stale")
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE", "1")

    control = MODULE._environment(manifest=None)
    guided = MODULE._environment(manifest=manifest)

    assert "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST" not in control
    assert "LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE" not in control
    assert guided["LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST"] == str(manifest)
    assert guided["LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE"] == "1"


def test_positive_net_manifest_forbids_production_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        MODULE,
        "validate_qg2_runtime_oracle_authority",
        lambda _manifest: MODULE.SELECTIVE_TRAINING_ONLY_MODE,
    )
    manifest = {
        "schema_version": MODULE.MANIFEST_SCHEMA,
        "evaluation_gate_policy": MODULE.QG2_POSITIVE_NET_EVALUATION_GATE_V1,
        "evaluation_authorized": True,
        "development_e2e_authorized": True,
        "deployment_authorized": False,
        "production_switch_authorized": False,
        "fallback": "P0V4_V5_Q0",
        "runtime_implementation_hash": MODULE.qg2_runtime_implementation_hash(),
        "ordering_only": True,
        "can_filter": False,
        "can_prune": False,
        "can_change_bound": False,
        "can_certify": False,
    }
    MODULE._validate_manifest(manifest)
    manifest["deployment_authorized"] = True
    with pytest.raises(ValueError, match="production_authority_forbidden"):
        MODULE._validate_manifest(manifest)


def test_positive_net_e2e_runs_control_then_evaluation_guided(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    run = tmp_path / "run"
    calibration = run / "calibration.json"
    evidence = run / "evidence.json"
    positive = run / "positive.json"
    manifest = run / "manifest.json"
    training = run / "training.json"
    output_root = run / "e2e"
    control = output_root / "control"
    guided = output_root / "guided"
    result = run / "acceptance.json"
    state = run / "state.json"
    for path in (calibration, evidence, positive, manifest):
        _write(path, {})
    _write(training, {
        "schema_version": MODULE.TRAINING_SCHEMA,
        "oracle_gate_passed": True,
        "deployable": False,
    })
    for name, value in {
        "CALIBRATION_REPORT": calibration,
        "SELECTIVE_EVIDENCE": evidence,
        "POSITIVE_REPORT": positive,
        "MANIFEST": manifest,
        "TRAINING_REPORT": training,
        "OUTPUT_ROOT": output_root,
        "CONTROL_ROOT": control,
        "GUIDED_ROOT": guided,
        "RESULT": result,
        "STATE": state,
    }.items():
        monkeypatch.setattr(MODULE, name, value)
    monkeypatch.setattr(MODULE, "_validate_freeze", lambda: None)
    monkeypatch.setattr(MODULE, "_matching_calibration_process", lambda _pid: False)
    monkeypatch.setattr(MODULE, "_ensure_positive_authority", lambda: manifest)
    instances = (tmp_path / "scale30.json", tmp_path / "scale50.json")
    monkeypatch.setattr(MODULE.base, "_heldout_instances", lambda _training: instances)
    calls = []
    monkeypatch.setattr(
        MODULE,
        "_run_acceptance",
        lambda **kwargs: calls.append(kwargs) or 0,
    )

    def fake_run(command, **_kwargs):
        assert command[-2:] == ["--mode", "development"]
        _write(result, {
            "schema_version": MODULE.ACCEPTANCE_SCHEMA,
            "mode": "positive_net_development",
            "passed": True,
            "violation_count": 0,
            "violations": [],
            "scale30_50_combined_geomean_wall_ratio": 0.999,
        })
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(MODULE.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys, "argv", ["positive-net-e2e", "--wait-for-pid", "123"]
    )

    assert MODULE.main() == 0
    assert [row["manifest"] for row in calls] == [None, manifest]
    payload = json.loads(state.read_text(encoding="utf-8"))
    assert payload["status"] == "POSITIVE_NET_E2E_PASSED_PENDING_FORMAL"
    assert payload["formal_experiment_authorized"] is True
    assert payload["production_switch_authorized"] is False
    assert payload["fallback_action"] == "Q0"

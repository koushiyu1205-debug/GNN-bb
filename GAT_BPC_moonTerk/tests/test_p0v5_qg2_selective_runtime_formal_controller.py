from __future__ import annotations

import hashlib
import json
from pathlib import Path
import runpy
from types import SimpleNamespace

import pytest

from lunar_ice_bpc.guidance.qg2_oracle_evidence import (
    attach_selective_oracle_evidence_to_manifest,
    build_selective_training_only_evidence,
)


ROOT = Path(__file__).resolve().parents[1]
MODULE = runpy.run_path(str(
    ROOT / "scripts/run_p0v5_qg2_selective_runtime_formal_after_e2e.py"
))
validate_authority = MODULE["validate_selective_runtime_formal_authority"]
GLOBALS = MODULE["main"].__globals__


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _fixture(tmp_path: Path) -> tuple[Path, Path, dict, dict, Path]:
    manifest = tmp_path / "runtime_manifest.json"
    checkpoint = tmp_path / "model.pt"
    checkpoint.write_bytes(b"checkpoint")
    scale = {
        "passed": True,
        "determined_context_count": 30,
        "determined_instance_count": 20,
        "gain_5pct_context_count": 10,
        "positive_instance_count": 8,
        "nonpositive_context_count": 10,
        "harmful_instance_count": 5,
    }
    evidence = build_selective_training_only_evidence(
        {
            "point_geomean_is_report_only": True,
            "instance_bootstrap_is_report_only": True,
            "gate": {
                "passed": True,
                "all_exact_safe": True,
                "contract_errors": [],
                "maximum_instance_saved_wall_fraction": 0.20,
                "scale30": dict(scale),
                "scale50": dict(scale),
            },
        },
        source_oracle_sha256="a" * 64,
        source_gate_sha256="b" * 64,
        context_count=60,
    )
    manifest_payload = attach_selective_oracle_evidence_to_manifest(
        {
            "schema_version": MODULE["MANIFEST_SCHEMA"],
            "runtime_policy_id": MODULE["QG2_RUNTIME_POLICY_ID"],
            "runtime_implementation_hash": MODULE[
                "qg2_runtime_implementation_hash"
            ](),
            "deployment_authorized": True,
            "ordering_only": True,
            "fallback": "P0V4_V5_Q0",
            "allowed_scales": [30, 50],
            "allowed_exact_engine_hashes": ["engine"],
            "allowed_exact_action_policy_hashes": ["action"],
            "checkpoint_path": str(checkpoint),
            "checkpoint_sha256": _sha256(checkpoint),
            "can_filter": False,
            "can_prune": False,
            "can_change_bound": False,
            "can_certify": False,
            "oracle_gate": {
                "passed": True,
                "all_exact_safe": evidence["all_exact_safe"],
                "contract_errors": evidence["contract_errors"],
                "maximum_instance_saved_wall_fraction": (
                    evidence["maximum_instance_saved_wall_fraction"]
                ),
                "scale30": evidence["by_scale"]["30"],
                "scale50": evidence["by_scale"]["50"],
            },
        },
        evidence,
    )
    _write(manifest, manifest_payload)
    control = tmp_path / "development/control"
    guided = tmp_path / "development/guided"
    _write(control / "b4_2_cold_exact_state.json", {"arm": "Q0"})
    _write(guided / "b4_2_cold_exact_state.json", {"arm": "QG2"})

    result_path = tmp_path / "development_acceptance.json"
    result = {
        "schema_version": MODULE["ACCEPTANCE_SCHEMA"],
        "mode": "development",
        "passed": True,
        "violation_count": 0,
        "violations": [],
        "by_scale": {"30": {}, "50": {}},
        "control_root": str(control),
        "guided_root": str(guided),
        "control_root_hash": MODULE["base"]._acceptance_artifact_hash(control),
        "guided_root_hash": MODULE["base"]._acceptance_artifact_hash(guided),
    }
    _write(result_path, result)

    state_path = tmp_path / "development_e2e_state.json"
    state = {
        "schema_version": MODULE["E2E_STATE_SCHEMA"],
        "status": "SELECTIVE_RUNTIME_E2E_PASSED_PENDING_FORMAL",
        "formal_experiment_authorized": True,
        "production_switch_authorized": False,
        "fallback_action": "Q0",
        "result_sha256": _sha256(result_path),
        "manifest": str(manifest),
        "manifest_sha256": _sha256(manifest),
    }
    _write(state_path, state)
    return state_path, result_path, state, result, manifest


def _validate(
    state_path: Path,
    result_path: Path,
    state: dict,
    result: dict,
) -> Path:
    return validate_authority(
        state,
        e2e_state_path=state_path,
        e2e_result=result,
        e2e_result_path=result_path,
    )


def test_formal_authority_accepts_hash_bound_development_e2e(
    tmp_path: Path,
) -> None:
    state_path, result_path, state, result, manifest = _fixture(tmp_path)
    assert _validate(state_path, result_path, state, result) == manifest


def test_formal_authority_rejects_result_or_artifact_hash_drift(
    tmp_path: Path,
) -> None:
    state_path, result_path, state, result, _manifest = _fixture(tmp_path)
    state["result_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="e2e_result_hash_mismatch"):
        _validate(state_path, result_path, state, result)

    state["result_sha256"] = _sha256(result_path)
    result["guided_root_hash"] = "0" * 64
    with pytest.raises(
        ValueError,
        match="development_guided_artifact_hash_mismatch",
    ):
        _validate(state_path, result_path, state, result)


@pytest.mark.parametrize(
    ("key", "value", "error"),
    (
        (
            "runtime_implementation_hash",
            "0" * 64,
            "runtime_implementation_drift",
        ),
        ("can_filter", True, "runtime_manifest_forbidden_authority:can_filter"),
        ("fallback", "QB1", "runtime_manifest_literal_q0_fallback_mismatch"),
    ),
)
def test_formal_authority_revalidates_runtime_manifest_safety(
    tmp_path: Path,
    key: str,
    value: object,
    error: str,
) -> None:
    state_path, result_path, state, result, manifest = _fixture(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload[key] = value
    _write(manifest, payload)
    state["manifest_sha256"] = _sha256(manifest)
    with pytest.raises(ValueError, match=error):
        _validate(state_path, result_path, state, result)


@pytest.mark.parametrize(
    ("key", "value", "error"),
    (
        ("production_switch_authorized", True, "production_scope_expansion"),
        ("fallback_action", "QB1", "literal_q0_fallback_mismatch"),
        ("formal_experiment_authorized", False, "formal_experiment_not_authorized"),
    ),
)
def test_formal_authority_rejects_scope_or_fallback_expansion(
    tmp_path: Path,
    key: str,
    value: object,
    error: str,
) -> None:
    state_path, result_path, state, result, _manifest = _fixture(tmp_path)
    state[key] = value
    with pytest.raises(ValueError, match=error):
        _validate(state_path, result_path, state, result)


def test_main_runs_paired_full20_and_only_permits_candidate_freeze(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    state_path, result_path, _state, _result, manifest = _fixture(tmp_path)
    output_root = tmp_path / "formal"
    formal_result = tmp_path / "formal_acceptance.json"
    formal_state = tmp_path / "formal_state.json"
    calls: list[dict] = []

    monkeypatch.setitem(GLOBALS, "E2E_STATE", state_path)
    monkeypatch.setitem(GLOBALS, "E2E_RESULT", result_path)
    monkeypatch.setitem(GLOBALS, "OUTPUT_ROOT", output_root)
    monkeypatch.setitem(GLOBALS, "CONTROL_ROOT", output_root / "control")
    monkeypatch.setitem(GLOBALS, "GUIDED_ROOT", output_root / "guided")
    monkeypatch.setitem(GLOBALS, "RESULT", formal_result)
    monkeypatch.setitem(GLOBALS, "STATE", formal_state)
    monkeypatch.setitem(GLOBALS, "_matching_e2e_controller", lambda _pid: False)
    monkeypatch.setattr(
        MODULE["sys"],
        "argv",
        ["formal-controller", "--wait-for-pid", "123"],
    )

    def fake_acceptance(**kwargs):
        calls.append(kwargs)
        return 0

    monkeypatch.setattr(MODULE["base"], "_run_acceptance", fake_acceptance)

    def fake_analyzer(command, **_kwargs):
        assert "analyze_p0v5_qg2_paired_acceptance.py" in command[1]
        _write(formal_result, {
            "schema_version": MODULE["ACCEPTANCE_SCHEMA"],
            "mode": "formal",
            "passed": True,
            "violation_count": 0,
            "violations": [],
            "by_scale": {
                "5": {}, "10": {}, "20": {}, "30": {}, "50": {},
            },
        })
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(MODULE["subprocess"], "run", fake_analyzer)

    assert MODULE["main"]() == 0
    assert [call["manifest"] for call in calls] == [None, manifest]
    final = json.loads(formal_state.read_text(encoding="utf-8"))
    assert final["status"] == "SELECTIVE_RUNTIME_FORMAL_FULL20_PASSED"
    assert final["candidate_freeze_permitted"] is True
    assert final["production_switch_performed"] is False
    assert final["fallback_action"] == "Q0"

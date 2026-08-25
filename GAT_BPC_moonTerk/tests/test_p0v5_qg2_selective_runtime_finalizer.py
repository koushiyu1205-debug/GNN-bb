from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/finalize_p0v5_qg2_selective_runtime_candidate.py"
SPEC = importlib.util.spec_from_file_location(
    "qg2_selective_runtime_finalizer",
    SCRIPT,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_authority_reconstruction_ignores_only_timestamp() -> None:
    MODULE._compare_authority_payloads(
        {"generated_at": "old", "fallback_action": "Q0"},
        {"generated_at": "new", "fallback_action": "Q0"},
    )
    with pytest.raises(ValueError, match="fallback_action"):
        MODULE._compare_authority_payloads(
            {"generated_at": "old", "fallback_action": "Q0"},
            {"generated_at": "new", "fallback_action": "QB1"},
        )


def test_formal_acceptance_requires_hash_bound_full_artifacts(
    tmp_path: Path,
) -> None:
    control = tmp_path / "control"
    guided = tmp_path / "guided"
    _write(control / "b4_2_cold_exact_state.json", {"arm": "Q0"})
    guided_file = guided / "b4_2_cold_exact_state.json"
    _write(guided_file, {"arm": "QG2"})
    result_path = tmp_path / "formal.json"
    payload = {
        "schema_version": MODULE.ACCEPTANCE_SCHEMA,
        "mode": "formal",
        "passed": True,
        "violation_count": 0,
        "by_scale": {"5": {}, "10": {}, "20": {}, "30": {}, "50": {}},
        "control_root": str(control),
        "guided_root": str(guided),
        "control_root_hash": MODULE.formal.base._acceptance_artifact_hash(
            control
        ),
        "guided_root_hash": MODULE.formal.base._acceptance_artifact_hash(
            guided
        ),
    }
    _write(result_path, payload)
    assert MODULE._valid_acceptance(
        payload,
        path=result_path,
        mode="formal",
        scales={5, 10, 20, 30, 50},
    )

    _write(guided_file, {"arm": "drift"})
    assert not MODULE._valid_acceptance(
        payload,
        path=result_path,
        mode="formal",
        scales={5, 10, 20, 30, 50},
    )


def test_candidate_audit_enforces_literal_q0_and_all_hashes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "artifact.json"
    _write(artifact, {"stable": True})
    digest = _sha256(artifact)
    monkeypatch.setattr(
        MODULE,
        "qg2_runtime_implementation_hash",
        lambda: "runtime-hash",
    )
    payload = {
        "schema_version": MODULE.CANDIDATE_SCHEMA,
        "status": "FROZEN_EXPERIMENT_CANDIDATE",
        "production_default": False,
        "production_switch_performed": False,
        "historical_baselines_unchanged": True,
        "p0v4_changed": False,
        "p0v5_exact_control_changed": False,
        "exact_control_freeze_id": (
            "P0V4_V5_BIDIRECTIONAL_EXACT_FINAL_CANDIDATE"
        ),
        "scale5_10_20_runtime_bypass": True,
        "allowed_scales": [30, 50],
        "fallback_action": "Q0",
        "all_arms_rejected_action": "Q0",
        "context_selector_in_final_runtime": False,
        "ordering_only": True,
        "can_filter": False,
        "can_prune": False,
        "can_change_bound": False,
        "can_certify": False,
        "development_e2e_passed": True,
        "formal_full20_passed": True,
        "regression_and_native_tests": {"passed": True},
        "runtime_policy_id": MODULE.QG2_RUNTIME_POLICY_ID,
        "runtime_implementation_hash": "runtime-hash",
        "exact_action_policy_hashes_by_scale": {
            "30": "action30",
            "50": "action50",
        },
        "frozen_file_sha256": {str(artifact): digest},
    }
    for path_key, hash_key in (
        ("selected_exact_config", "selected_exact_config_sha256"),
        ("manifest_path", "manifest_sha256"),
        ("checkpoint_path", "checkpoint_sha256"),
        ("oracle_summary", "oracle_summary_sha256"),
        ("training_report", "training_report_sha256"),
        ("selector_report", "selector_report_sha256"),
        ("calibration_report", "calibration_report_sha256"),
        ("calibration_risk_audit", "calibration_risk_audit_sha256"),
        ("selective_oracle_evidence", "selective_oracle_evidence_sha256"),
        ("development_acceptance", "development_acceptance_sha256"),
        ("formal_acceptance", "formal_acceptance_sha256"),
    ):
        payload[path_key] = str(artifact)
        payload[hash_key] = digest
    assert MODULE.audit_selective_candidate_payload(payload) == []

    payload["all_arms_rejected_action"] = "QB1"
    issues = MODULE.audit_selective_candidate_payload(payload)
    assert "candidate_exact_safe_acceptance_contract_mismatch" in issues

    payload["all_arms_rejected_action"] = "Q0"
    _write(artifact, {"stable": False})
    issues = MODULE.audit_selective_candidate_payload(payload)
    assert any("candidate_direct_binding_failed" in issue for issue in issues)
    assert any("candidate_frozen_drift" in issue for issue in issues)


def test_candidate_authority_rechecks_e2e_formal_and_runtime_binding(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    authority_path = tmp_path / "authority.json"
    training_path = tmp_path / "training.json"
    manifest_path = tmp_path / "manifest.json"
    e2e_state_path = tmp_path / "e2e_state.json"
    e2e_result_path = tmp_path / "e2e_result.json"
    formal_state_path = tmp_path / "formal_state.json"
    formal_result_path = tmp_path / "formal_result.json"
    control = tmp_path / "formal/control"
    guided = tmp_path / "formal/guided"
    _write(control / "b4_2_cold_exact_state.json", {"arm": "Q0"})
    _write(guided / "b4_2_cold_exact_state.json", {"arm": "QG2"})

    authority = {"generated_at": "old", "fallback_action": "Q0"}
    _write(authority_path, authority)
    _write(training_path, {"schema_version": "training"})
    _write(manifest_path, {
        "runtime_policy_id": MODULE.QG2_RUNTIME_POLICY_ID,
        "runtime_implementation_hash": "runtime-hash",
    })
    _write(e2e_result_path, {"development": True})
    _write(e2e_state_path, {
        "authority_sha256": _sha256(authority_path),
    })
    formal_result = {
        "schema_version": MODULE.ACCEPTANCE_SCHEMA,
        "mode": "formal",
        "passed": True,
        "violation_count": 0,
        "by_scale": {"5": {}, "10": {}, "20": {}, "30": {}, "50": {}},
        "control_root": str(control),
        "guided_root": str(guided),
        "control_root_hash": MODULE.formal.base._acceptance_artifact_hash(
            control
        ),
        "guided_root_hash": MODULE.formal.base._acceptance_artifact_hash(
            guided
        ),
    }
    _write(formal_result_path, formal_result)
    _write(formal_state_path, {
        "schema_version": MODULE.FORMAL_STATE_SCHEMA,
        "status": "SELECTIVE_RUNTIME_FORMAL_FULL20_PASSED",
        "candidate_freeze_permitted": True,
        "production_switch_performed": False,
        "fallback_action": "Q0",
        "result_sha256": _sha256(formal_result_path),
        "manifest": str(manifest_path),
        "manifest_sha256": _sha256(manifest_path),
    })
    for name, path in {
        "AUTHORITY": authority_path,
        "TRAINING": training_path,
        "MANIFEST": manifest_path,
        "E2E_STATE": e2e_state_path,
        "E2E_RESULT": e2e_result_path,
        "FORMAL_STATE": formal_state_path,
        "FORMAL_RESULT": formal_result_path,
    }.items():
        monkeypatch.setattr(MODULE, name, path)
    monkeypatch.setattr(
        MODULE.e2e,
        "validate_selective_runtime_e2e_authority",
        lambda *_args, **_kwargs: manifest_path.resolve(),
    )
    monkeypatch.setattr(
        MODULE.binding,
        "build_selective_runtime_e2e_authority",
        lambda **_kwargs: {"generated_at": "new", "fallback_action": "Q0"},
    )
    monkeypatch.setattr(
        MODULE.formal,
        "validate_selective_runtime_formal_authority",
        lambda *_args, **_kwargs: manifest_path.resolve(),
    )
    monkeypatch.setattr(
        MODULE,
        "validate_qg2_runtime_oracle_authority",
        lambda _manifest: MODULE.SELECTIVE_TRAINING_ONLY_MODE,
    )
    monkeypatch.setattr(
        MODULE,
        "qg2_runtime_implementation_hash",
        lambda: "runtime-hash",
    )
    assert MODULE.validate_selective_candidate_authority() == (
        manifest_path.resolve()
    )

    formal_state = json.loads(formal_state_path.read_text(encoding="utf-8"))
    formal_state["production_switch_performed"] = True
    _write(formal_state_path, formal_state)
    with pytest.raises(ValueError, match="formal controller authority mismatch"):
        MODULE.validate_selective_candidate_authority()


def test_main_freezes_candidate_but_never_switches_production(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    evidence = tmp_path / "evidence.json"
    manifest = tmp_path / "manifest.json"
    _write(evidence, {"present": True})
    _write(manifest, {"manifest": True})
    for name in (
        "ORACLE_FREEZE", "ORACLE", "TRAINING", "SELECTOR",
        "CALIBRATION_STATE", "CALIBRATION", "RISK", "EVIDENCE_STATE",
        "EVIDENCE", "MANIFEST", "AUTHORITY", "E2E_STATE", "E2E_RESULT",
        "FORMAL_STATE", "FORMAL_RESULT",
    ):
        monkeypatch.setattr(
            MODULE,
            name,
            manifest if name == "MANIFEST" else evidence,
        )
    candidate = tmp_path / "candidate.json"
    audit = tmp_path / "audit.json"
    state = tmp_path / "state.json"
    monkeypatch.setattr(MODULE, "CANDIDATE", candidate)
    monkeypatch.setattr(MODULE, "AUDIT", audit)
    monkeypatch.setattr(MODULE, "STATE", state)
    monkeypatch.setattr(MODULE, "_matching_formal_controller", lambda _pid: False)
    monkeypatch.setattr(
        MODULE,
        "validate_selective_candidate_authority",
        lambda: manifest,
    )
    monkeypatch.setattr(
        MODULE,
        "_run_tests",
        lambda: {"passed": True, "commands": []},
    )
    payload = {
        "schema_version": MODULE.CANDIDATE_SCHEMA,
        "status": "FROZEN_EXPERIMENT_CANDIDATE",
        "production_default": False,
        "production_switch_performed": False,
        "fallback_action": "Q0",
    }
    monkeypatch.setattr(
        MODULE,
        "build_selective_candidate_payload",
        lambda _manifest, tests: {**payload, "tests": tests},
    )
    monkeypatch.setattr(
        MODULE,
        "audit_selective_candidate_payload",
        lambda _payload: [],
    )
    monkeypatch.setattr(
        MODULE.sys,
        "argv",
        ["selective-finalizer", "--wait-for-pid", "123"],
    )

    assert MODULE.main() == 0
    frozen = json.loads(candidate.read_text(encoding="utf-8"))
    assert frozen["production_default"] is False
    assert frozen["production_switch_performed"] is False
    assert frozen["fallback_action"] == "Q0"
    completion = json.loads(audit.read_text(encoding="utf-8"))
    assert completion["complete"] is True
    final_state = json.loads(state.read_text(encoding="utf-8"))
    assert final_state["status"] == (
        "SELECTIVE_RUNTIME_CANDIDATE_FROZEN_AND_AUDITED"
    )
    assert final_state["production_switch_performed"] is False
    assert final_state["fallback_action"] == "Q0"

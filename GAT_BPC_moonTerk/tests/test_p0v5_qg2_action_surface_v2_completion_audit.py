from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_p0v5_qg2_action_surface_v2_completion.py"
SPEC = importlib.util.spec_from_file_location("qg2_v2_completion_audit", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def test_current_action_surface_freezes_are_hash_clean() -> None:
    oracle = MODULE._audit_oracle_execution_provenance()
    relaxed = MODULE._audit_relaxed_freeze()
    assert oracle["status"] == "PASS"
    assert relaxed["status"] == "PASS"


def test_live_progress_can_never_authorize_training() -> None:
    progress = MODULE._oracle_progress()
    assert not progress["training_authorized"]
    assert progress["role"] == "live_progress_only_not_oracle_gate_evidence"
    assert progress["q0_trace_count"] >= progress["complete_future_trace_count"]
    assert (
        progress["complete_future_trace_count"]
        >= progress["full_initial_arm_context_count"]
    )
    if progress["full_initial_arm_context_count"]:
        assert progress["action_reachable_training_pair_count"] > 0
    live_gate = progress["relaxed_gate_live_diagnostic"]
    assert not live_gate["training_authorized"]
    assert set(live_gate["by_scale"]) == {"30", "50"}


def test_bucket_metrics_use_determined_outcomes_and_instance_bootstrap() -> None:
    rows = []
    for scale in (30, 50):
        for index in range(20):
            rows.append({
                "scale": scale,
                "instance_hash": f"{scale}-{index}",
                "ratio": 0.94,
                "saved_wall_sec": 6.0,
                "outcome_determined": True,
                "all_safe": True,
                "milestone_kind": "ADMISSION_BATCH_READY",
            })
    metrics = MODULE._bucket_metrics(rows)
    assert metrics["all_exact_safe"]
    for scale in (30, 50):
        row = metrics["by_scale"][str(scale)]
        assert row["determined_context_count"] == 20
        assert row["gain_5pct_context_count"] == 20
        assert row["gain_5pct_instance_count"] == 20
        assert row["paired_geomean_ratio"] == 0.94
        assert row["instance_bootstrap_95_upper"] == 0.94


def test_relaxed_authority_is_bound_to_exact_oracle_bytes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    oracle_path = tmp_path / "oracle.json"
    gate_path = tmp_path / "gate.json"
    oracle = {"schema_version": MODULE.ORACLE_SCHEMA}
    _write(oracle_path, oracle)
    gate = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_relaxed_training_gate.v1"
        ),
        "supervision_schema_version": MODULE.SUPERVISION_SCHEMA,
        "queue_action_surface": MODULE.ACTION_SURFACE,
        "oracle_summary_sha256": MODULE._sha256(oracle_path),
        "gate": {"passed": True},
        "training_authorized": True,
        "deployment_authorized": False,
        "paper_claim_authorized": False,
    }
    _write(gate_path, gate)
    monkeypatch.setattr(MODULE, "ORACLE_SUMMARY", oracle_path)
    monkeypatch.setattr(MODULE, "RELAXED_GATE", gate_path)
    assert MODULE._relaxed_training_authorized(oracle)

    gate["deployment_authorized"] = True
    _write(gate_path, gate)
    assert not MODULE._relaxed_training_authorized(oracle)


def test_acceptance_rechecks_persistent_run_hashes(tmp_path: Path) -> None:
    control = tmp_path / "control"
    guided = tmp_path / "guided"
    (control / "scale30").mkdir(parents=True)
    (guided / "scale30").mkdir(parents=True)
    (control / "scale30/b4_2_cold_exact_state.json").write_text(
        "{}\n", encoding="utf-8"
    )
    (guided / "scale30/b4_2_cold_exact_state.json").write_text(
        "{}\n", encoding="utf-8"
    )
    acceptance = tmp_path / "acceptance.json"
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_paired_acceptance.v1",
        "mode": "development",
        "passed": True,
        "violation_count": 0,
        "by_scale": {"30": {}},
        "control_root": str(control),
        "guided_root": str(guided),
        "control_root_hash": MODULE._acceptance_artifact_hash(control),
        "guided_root_hash": MODULE._acceptance_artifact_hash(guided),
    }
    _write(acceptance, payload)
    assert MODULE._audit_acceptance(
        acceptance,
        mode="development",
        scales={30},
    )["status"] == "PASS"

    (guided / "scale30/b4_2_cold_exact_state.json").write_text(
        '{"drift": true}\n', encoding="utf-8"
    )
    assert MODULE._audit_acceptance(
        acceptance,
        mode="development",
        scales={30},
    )["status"] == "FAIL"


def test_calibration_authority_can_use_hash_bound_supplement(
    tmp_path: Path,
    monkeypatch,
) -> None:
    strict = tmp_path / "strict.json"
    relaxed = tmp_path / "relaxed.json"
    supplement = tmp_path / "supplement.json"
    _write(strict, {
        "schema_version": MODULE.CALIBRATION_SCHEMA,
        "gate_pass": False,
        "deployment_authorized": False,
    })
    _write(supplement, {
        "schema_version": MODULE.CALIBRATION_SCHEMA,
        "gate_pass": True,
        "deployment_authorized": True,
    })
    monkeypatch.setattr(MODULE, "STRICT_CALIBRATION", strict)
    monkeypatch.setattr(MODULE, "RELAXED_CALIBRATION", relaxed)
    monkeypatch.setattr(MODULE, "SUPPLEMENTAL_CALIBRATION", supplement)
    monkeypatch.setattr(
        MODULE,
        "_audit_supplemental_calibration_binding",
        lambda: {"status": "PASS"},
    )

    assert MODULE._calibration_authority() == supplement


def test_supplemental_stage_state_requires_result_hash_binding(
    tmp_path: Path,
) -> None:
    state = tmp_path / "state.json"
    result = tmp_path / "result.json"
    standard = tmp_path / "standard.json"
    _write(result, {"passed": True})
    _write(state, {
        "schema_version": "test.state.v1",
        "status": "PASSED",
        "result_sha256": MODULE._sha256(result),
    })
    assert MODULE._supplemental_stage_state_issues(
        state_path=state,
        schema="test.state.v1",
        passed_status="PASSED",
        no_op_status="NO_OP",
        result_path=result,
        standard_state_path=standard,
        standard_passed_status="PASSED",
        prefix="stage",
    ) == []

    _write(result, {"passed": False})
    assert "stage_result_binding_mismatch" in (
        MODULE._supplemental_stage_state_issues(
            state_path=state,
            schema="test.state.v1",
            passed_status="PASSED",
            no_op_status="NO_OP",
            result_path=result,
            standard_state_path=standard,
            standard_passed_status="PASSED",
            prefix="stage",
        )
    )

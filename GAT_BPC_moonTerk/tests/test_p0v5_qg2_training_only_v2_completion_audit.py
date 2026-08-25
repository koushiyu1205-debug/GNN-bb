from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_p0v5_qg2_training_only_v2_completion.py"
SPEC = importlib.util.spec_from_file_location(
    "qg2_training_only_v2_completion_audit",
    SCRIPT,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def test_test_command_expands_qg2_files_before_subprocess() -> None:
    pytest_command = MODULE._test_commands()[0]
    assert "tests/test_p0v5_qg2*.py" not in pytest_command
    assert any(
        value.endswith("test_p0v5_qg2_label_state_gat.py")
        for value in pytest_command
    )
    assert all("*" not in value for value in pytest_command)


def test_empty_acceptance_tree_cannot_match_empty_hash(
    tmp_path: Path,
    monkeypatch,
) -> None:
    control = tmp_path / "control"
    guided = tmp_path / "guided"
    control.mkdir()
    guided.mkdir()
    freeze = tmp_path / "freeze.json"
    state = tmp_path / "state.json"
    result = tmp_path / "result.json"
    _write(freeze, {
        "schema_version": "test.freeze.v1",
        "development_only": True,
        "deployable": False,
        "frozen_file_sha256": {},
    })
    payload = {
        "schema_version": MODULE.ACCEPTANCE_SCHEMA,
        "mode": "development",
        "passed": True,
        "violation_count": 0,
        "by_scale": {"30": {}},
        "control_root": str(control),
        "guided_root": str(guided),
        "control_root_hash": "",
        "guided_root_hash": "",
    }
    _write(result, payload)
    _write(state, {
        "schema_version": "test.state.v1",
        "status": "PASSED",
        "result_sha256": hashlib.sha256(result.read_bytes()).hexdigest(),
    })

    row = MODULE._audit_acceptance_stage(
        freeze=freeze,
        state_path=state,
        result_path=result,
        freeze_schema="test.freeze.v1",
        state_schema="test.state.v1",
        passed_status="PASSED",
        mode="development",
        scales={30},
    )
    assert row["status"] == "FAIL"
    assert "control_artifact_binding_failed" in row["evidence"]["issues"]
    assert "guided_artifact_binding_failed" in row["evidence"]["issues"]


def test_freeze_recheck_detects_drift(tmp_path: Path) -> None:
    frozen = tmp_path / "frozen.py"
    frozen.write_text("before\n", encoding="utf-8")
    freeze = tmp_path / "freeze.json"
    _write(freeze, {
        "schema_version": "test.freeze.v1",
        "development_only": True,
        "deployable": False,
        "frozen_file_sha256": {
            str(frozen): hashlib.sha256(frozen.read_bytes()).hexdigest(),
        },
    })
    assert MODULE._freeze_issues(
        freeze,
        expected_schema="test.freeze.v1",
    ) == []

    frozen.write_text("after\n", encoding="utf-8")
    issues = MODULE._freeze_issues(freeze, expected_schema="test.freeze.v1")
    assert any(value.startswith("freeze_drift:") for value in issues)


def test_candidate_rejects_production_switch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    candidate = tmp_path / "candidate.json"
    _write(candidate, {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_training_only_v2_candidate_freeze.v1"
        ),
        "status": "FROZEN_EXPERIMENT_CANDIDATE",
        "production_default": True,
        "production_switch_performed": True,
        "historical_baselines_unchanged": True,
        "p0v4_changed": False,
        "p0v5_exact_control_changed": False,
        "development_e2e_passed": True,
        "formal_full20_passed": True,
        "frozen_file_sha256": {},
    })
    monkeypatch.setattr(MODULE, "CANDIDATE", candidate)
    row = MODULE._audit_candidate()
    assert row["status"] == "FAIL"
    assert "candidate_illegal_production_switch" in row["evidence"]["issues"]

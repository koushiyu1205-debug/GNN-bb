from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT / "scripts/run_p0v5_qg2_action_surface_v2_e2e_after_calibration.py"
)
SPEC = importlib.util.spec_from_file_location("qg2_action_v2_e2e", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
FORMAL_SCRIPT = (
    ROOT / "scripts/run_p0v5_qg2_action_surface_v2_formal_after_e2e.py"
)
FORMAL_SPEC = importlib.util.spec_from_file_location(
    "qg2_action_v2_formal",
    FORMAL_SCRIPT,
)
assert FORMAL_SPEC is not None and FORMAL_SPEC.loader is not None
FORMAL = importlib.util.module_from_spec(FORMAL_SPEC)
FORMAL_SPEC.loader.exec_module(FORMAL)
FINALIZER_SCRIPT = (
    ROOT / "scripts/finalize_p0v5_qg2_action_surface_v2_candidate.py"
)
FINALIZER_SPEC = importlib.util.spec_from_file_location(
    "qg2_action_v2_finalizer",
    FINALIZER_SCRIPT,
)
assert FINALIZER_SPEC is not None and FINALIZER_SPEC.loader is not None
FINALIZER = importlib.util.module_from_spec(FINALIZER_SPEC)
FINALIZER_SPEC.loader.exec_module(FINALIZER)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _reports(training_path: Path) -> tuple[dict, dict]:
    training = {
        "schema_version": MODULE.TRAINING_SCHEMA,
        "oracle_gate_passed": True,
        "supervision_schema_version": MODULE.SUPERVISION_SCHEMA,
        "queue_action_surface": MODULE.ACTION_SURFACE,
        "deployable": False,
    }
    _write(training_path, training)
    calibration = {
        "schema_version": MODULE.CALIBRATION_SCHEMA,
        "gate_pass": True,
        "deployment_authorized": True,
        "training_report_sha256": MODULE._sha256(training_path),
    }
    return training, calibration


def test_e2e_environment_removes_every_guidance_variable(monkeypatch) -> None:
    for key in MODULE.GUIDANCE_ENV_KEYS:
        monkeypatch.setenv(key, "must-not-leak")
    env = MODULE._environment(manifest=None)
    assert all(key not in env for key in MODULE.GUIDANCE_ENV_KEYS)

    manifest = Path("/tmp/frozen-qg2-manifest.json")
    guided = MODULE._environment(manifest=manifest)
    assert guided["LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST"] == str(manifest)
    assert all(
        key not in guided
        for key in MODULE.GUIDANCE_ENV_KEYS
        if key != "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST"
    )


def test_calibration_report_binding_fails_closed(tmp_path: Path) -> None:
    training_path = tmp_path / "training.json"
    training, calibration = _reports(training_path)
    assert MODULE._authorized_reports(
        training,
        calibration,
        training_path=training_path,
    )
    calibration["training_report_sha256"] = "drift"
    assert not MODULE._authorized_reports(
        training,
        calibration,
        training_path=training_path,
    )


def test_strict_authority_is_preferred_and_relaxed_is_valid_fallback(
    tmp_path: Path,
    monkeypatch,
) -> None:
    paths = {
        name: tmp_path / f"{name}.json"
        for name in (
            "strict_state",
            "relaxed_state",
            "strict_training",
            "relaxed_training",
            "strict_calibration",
            "relaxed_calibration",
        )
    }
    strict_training, strict_calibration = _reports(paths["strict_training"])
    relaxed_training, relaxed_calibration = _reports(paths["relaxed_training"])
    _write(paths["strict_calibration"], strict_calibration)
    _write(paths["relaxed_calibration"], relaxed_calibration)
    _write(paths["strict_state"], {"status": "CALIBRATION_GATE_FAILED"})
    _write(paths["relaxed_state"], {
        "status": "CALIBRATION_PASSED_PENDING_HELDOUT_E2E",
    })
    for name, constant in (
        ("strict_state", "STRICT_STATE"),
        ("relaxed_state", "RELAXED_STATE"),
        ("strict_training", "STRICT_TRAINING"),
        ("relaxed_training", "RELAXED_TRAINING"),
        ("strict_calibration", "STRICT_CALIBRATION"),
        ("relaxed_calibration", "RELAXED_CALIBRATION"),
    ):
        monkeypatch.setattr(MODULE, constant, paths[name])

    selected = MODULE._select_calibration_authority()
    assert selected is not None
    assert selected["authority"] == "relaxed_training_gate_strict_calibration"

    _write(paths["strict_state"], {"status": "CALIBRATION_PASSED"})
    selected = MODULE._select_calibration_authority()
    assert selected is not None
    assert selected["authority"] == "strict_oracle_gate"


def test_formal_environment_also_removes_every_guidance_variable(
    monkeypatch,
) -> None:
    for key in FORMAL.GUIDANCE_ENV_KEYS:
        monkeypatch.setenv(key, "must-not-leak")
    env = FORMAL._environment(manifest=None)
    assert all(key not in env for key in FORMAL.GUIDANCE_ENV_KEYS)


def test_formal_e2e_gate_rechecks_result_and_run_hashes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    control = tmp_path / "control"
    guided = tmp_path / "guided"
    (control / "scale30").mkdir(parents=True)
    (guided / "scale30").mkdir(parents=True)
    for root in (control, guided):
        (root / "scale30/b4_2_cold_exact_state.json").write_text(
            "{}\n", encoding="utf-8"
        )
    result_path = tmp_path / "e2e.json"
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_paired_acceptance.v1",
        "mode": "development",
        "passed": True,
        "violation_count": 0,
        "by_scale": {"30": {}, "50": {}},
        "control_root": str(control),
        "guided_root": str(guided),
        "control_root_hash": FORMAL._acceptance_artifact_hash(control),
        "guided_root_hash": FORMAL._acceptance_artifact_hash(guided),
    }
    _write(result_path, payload)
    monkeypatch.setattr(FORMAL, "E2E_RESULT", result_path)
    state = {
        "status": "E2E_PASSED",
        "result_sha256": FORMAL._sha256(result_path),
    }
    assert FORMAL._valid_e2e_result(payload, state)

    (guided / "scale30/b4_2_cold_exact_state.json").write_text(
        '{"drift": true}\n', encoding="utf-8"
    )
    assert not FORMAL._valid_e2e_result(payload, state)


def test_finalizer_environment_removes_every_guidance_variable(
    monkeypatch,
) -> None:
    for key in FINALIZER.GUIDANCE_ENV_KEYS:
        monkeypatch.setenv(key, "must-not-leak")
    env = FINALIZER._python_env()
    assert all(key not in env for key in FINALIZER.GUIDANCE_ENV_KEYS)


def test_finalizer_bound_file_and_acceptance_hash_fail_closed(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "manifest.json"
    artifact.write_text("{}\n", encoding="utf-8")
    assert FINALIZER._bound_file(
        artifact,
        FINALIZER._sha256(artifact),
        "test",
    ) == artifact

    control = tmp_path / "formal-control"
    guided = tmp_path / "formal-guided"
    for root in (control, guided):
        (root / "scale50").mkdir(parents=True)
        (root / "scale50/b4_2_cold_exact_state.json").write_text(
            "{}\n", encoding="utf-8"
        )
    result = tmp_path / "formal.json"
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_paired_acceptance.v1",
        "mode": "formal",
        "passed": True,
        "violation_count": 0,
        "by_scale": {str(scale): {} for scale in (5, 10, 20, 30, 50)},
        "control_root": str(control),
        "guided_root": str(guided),
        "control_root_hash": FINALIZER._acceptance_artifact_hash(control),
        "guided_root_hash": FINALIZER._acceptance_artifact_hash(guided),
    }
    _write(result, payload)
    assert FINALIZER._valid_acceptance(
        payload,
        mode="formal",
        scales={5, 10, 20, 30, 50},
        path=result,
        expected_sha256=FINALIZER._sha256(result),
    )
    payload["guided_root_hash"] = "drift"
    assert not FINALIZER._valid_acceptance(
        payload,
        mode="formal",
        scales={5, 10, 20, 30, 50},
        path=result,
        expected_sha256=FINALIZER._sha256(result),
    )

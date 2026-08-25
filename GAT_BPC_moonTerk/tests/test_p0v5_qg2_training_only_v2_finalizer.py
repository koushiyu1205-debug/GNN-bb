from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/finalize_p0v5_qg2_training_only_v2_candidate.py"
SPEC = importlib.util.spec_from_file_location(
    "qg2_training_only_v2_finalizer",
    SCRIPT,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def test_finalizer_uses_independent_training_only_v2_artifacts() -> None:
    assert MODULE.CANDIDATE.name == (
        "P0V5_QG2_LABEL_STATE_GAT_TRAINING_ONLY_V2_candidate_freeze.json"
    )
    assert MODULE.FORMAL_STATE.name == (
        "qg2_training_only_v2_formal_controller_state.json"
    )
    assert MODULE.FINAL_AUDIT.name == "qg2_training_only_v2_completion_audit.json"


def test_acceptance_requires_nonempty_hash_bound_artifacts(tmp_path: Path) -> None:
    control = tmp_path / "control"
    guided = tmp_path / "guided"
    (control / "scale30").mkdir(parents=True)
    (guided / "scale30").mkdir(parents=True)
    control_file = control / "scale30/b4_2_cold_exact_state.json"
    guided_file = guided / "scale30/b4_2_cold_exact_state.json"
    control_file.write_text("{}\n", encoding="utf-8")
    guided_file.write_text("{}\n", encoding="utf-8")
    payload = {
        "schema_version": MODULE.ACCEPTANCE_SCHEMA,
        "mode": "development",
        "passed": True,
        "violation_count": 0,
        "by_scale": {"30": {}},
        "control_root": str(control),
        "guided_root": str(guided),
        "control_root_hash": MODULE._artifact_hash(control),
        "guided_root_hash": MODULE._artifact_hash(guided),
    }
    assert MODULE._valid_acceptance(payload, mode="development", scales={30})

    guided_file.write_text('{"drift": true}\n', encoding="utf-8")
    assert not MODULE._valid_acceptance(
        payload,
        mode="development",
        scales={30},
    )


def test_finalizer_freeze_is_hash_bound_and_fail_closed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    formal_freeze = tmp_path / "formal_freeze.json"
    implementation = tmp_path / "finalizer.py"
    formal_freeze.write_text("{}\n", encoding="utf-8")
    implementation.write_text("stable\n", encoding="utf-8")
    freeze = tmp_path / "freeze.json"
    _write(freeze, {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_training_only_v2_candidate_finalizer_freeze.v1"
        ),
        "development_only": True,
        "deployable": False,
        "production_default": False,
        "fallback_action": "Q0",
        "historical_baselines_unchanged": True,
        "formal_controller_freeze_sha256": hashlib.sha256(
            formal_freeze.read_bytes()
        ).hexdigest(),
        "frozen_file_sha256": {
            str(implementation): hashlib.sha256(
                implementation.read_bytes()
            ).hexdigest(),
        },
    })
    monkeypatch.setattr(MODULE, "FREEZE", freeze)
    monkeypatch.setattr(MODULE, "FORMAL_FREEZE", formal_freeze)
    MODULE._validate_freeze()

    implementation.write_text("drift\n", encoding="utf-8")
    try:
        MODULE._validate_freeze()
    except SystemExit as exc:
        assert "frozen drift" in str(exc)
    else:
        raise AssertionError("finalizer must fail closed on frozen drift")


def test_audit_pass_requires_zero_failed_and_incomplete(tmp_path: Path) -> None:
    path = tmp_path / "audit.json"
    _write(path, {
        "complete": True,
        "pre_final_freeze": True,
        "failed_check_count": 0,
        "incomplete_check_count": 0,
    })
    assert MODULE._audit_passed(path, pre_final_freeze=True)
    assert not MODULE._audit_passed(path, pre_final_freeze=False)

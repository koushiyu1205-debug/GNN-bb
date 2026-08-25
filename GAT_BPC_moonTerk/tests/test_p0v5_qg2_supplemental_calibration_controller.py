from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_p0v5_qg2_supplemental_calibration_after_training.py"
SPEC = importlib.util.spec_from_file_location("qg2_supplement_controller", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_training_authority_prefers_valid_strict_then_relaxed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    strict = tmp_path / "strict.json"
    relaxed = tmp_path / "relaxed.json"
    monkeypatch.setattr(MODULE, "STRICT_TRAINING", strict)
    monkeypatch.setattr(MODULE, "RELAXED_TRAINING", relaxed)
    payload = {
        "schema_version": MODULE.TRAINING_SCHEMA,
        "oracle_gate_passed": True,
        "deployable": False,
    }
    _write(relaxed, payload)
    assert MODULE._training_authority() == relaxed
    _write(strict, payload)
    assert MODULE._training_authority() == strict


def test_passed_calibration_requires_deployment_authority(
    tmp_path: Path,
    monkeypatch,
) -> None:
    strict = tmp_path / "strict.json"
    relaxed = tmp_path / "relaxed.json"
    monkeypatch.setattr(MODULE, "STRICT_CALIBRATION", strict)
    monkeypatch.setattr(MODULE, "RELAXED_CALIBRATION", relaxed)
    _write(strict, {
        "schema_version": MODULE.CALIBRATION_SCHEMA,
        "gate_pass": True,
        "deployment_authorized": False,
    })
    assert MODULE._passed_calibration() is None
    _write(relaxed, {
        "schema_version": MODULE.CALIBRATION_SCHEMA,
        "gate_pass": True,
        "deployment_authorized": True,
    })
    assert MODULE._passed_calibration() == relaxed

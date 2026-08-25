from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_p0v5_qg2_e2e_after_supplemental_calibration.py"
SPEC = importlib.util.spec_from_file_location("qg2_supplement_e2e", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_supplemental_authority_requires_every_bound_view(
    tmp_path: Path,
    monkeypatch,
) -> None:
    state = tmp_path / "state.json"
    binding = tmp_path / "binding.json"
    monkeypatch.setattr(MODULE, "SUPPLEMENT_STATE", state)
    monkeypatch.setattr(MODULE, "SUPPLEMENT_BINDING", binding)
    _write(state, {
        "status": "SUPPLEMENTAL_CALIBRATION_PASSED_PENDING_E2E",
    })
    payload = {
        "schema_version": MODULE.BINDING_SCHEMA,
        "training_rows_added": 0,
        "gate_pass": True,
        "deployment_authorized": True,
    }
    for name in (
        "training_view", "oracle_view", "split_view",
        "calibration_report", "supplemental_manifest",
    ):
        path = tmp_path / f"{name}.json"
        _write(path, {})
        payload[name] = str(path)
        payload[f"{name}_sha256"] = _sha(path)
    _write(binding, payload)

    authority = MODULE._validated_supplemental_authority()
    assert authority is not None
    assert authority["training_view"].is_file()

    Path(payload["split_view"]).write_text('{"drift":true}', encoding="utf-8")
    assert MODULE._validated_supplemental_authority() is None

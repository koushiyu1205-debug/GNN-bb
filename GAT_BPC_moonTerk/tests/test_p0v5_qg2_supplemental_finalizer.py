from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/finalize_p0v5_qg2_after_supplemental_formal.py"
SPEC = importlib.util.spec_from_file_location("qg2_supplement_finalizer", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_supplemental_finalizer_binds_independent_stage_states() -> None:
    assert MODULE.FORMAL_STATE.name == "qg2_supplemental_formal_controller_state.json"
    assert MODULE.E2E_STATE.name == "qg2_supplemental_e2e_controller_state.json"
    assert MODULE.STATE.name == "qg2_supplemental_candidate_finalizer_state.json"


def test_stage_binding_accepts_hash_bound_supplemental_states(
    tmp_path: Path,
    monkeypatch,
) -> None:
    formal_result = tmp_path / "formal.json"
    e2e_result = tmp_path / "e2e.json"
    formal_result.write_text("{}\n", encoding="utf-8")
    e2e_result.write_text("{}\n", encoding="utf-8")
    formal_state_path = tmp_path / "formal_state.json"
    e2e_state_path = tmp_path / "e2e_state.json"
    formal = {
        "status": "FORMAL_FULL20_PASSED",
        "result_sha256": hashlib.sha256(formal_result.read_bytes()).hexdigest(),
    }
    e2e = {
        "status": "E2E_PASSED",
        "result_sha256": hashlib.sha256(e2e_result.read_bytes()).hexdigest(),
    }
    formal_state_path.write_text(json.dumps(formal), encoding="utf-8")
    e2e_state_path.write_text(json.dumps(e2e), encoding="utf-8")
    monkeypatch.setattr(MODULE, "FORMAL_STATE", formal_state_path)
    monkeypatch.setattr(MODULE, "E2E_STATE", e2e_state_path)
    monkeypatch.setattr(MODULE.base, "FORMAL_RESULT", formal_result)
    monkeypatch.setattr(MODULE.base, "E2E_RESULT", e2e_result)

    selected = MODULE._selected_stage_binding(formal)
    assert selected is not None
    assert selected["formal_state"] == formal_state_path

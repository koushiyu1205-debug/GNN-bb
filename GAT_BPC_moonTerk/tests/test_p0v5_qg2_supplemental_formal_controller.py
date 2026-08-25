from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_p0v5_qg2_formal_after_supplemental_e2e.py"
SPEC = importlib.util.spec_from_file_location("qg2_supplement_formal", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_supplemental_formal_state_is_independent_from_standard_state() -> None:
    assert MODULE.STATE.name == "qg2_supplemental_formal_controller_state.json"
    assert MODULE.RESULT.name == "formal_full20_acceptance_qg2_action_surface_v2.json"
    assert MODULE.E2E_STATE.name == "qg2_supplemental_e2e_controller_state.json"

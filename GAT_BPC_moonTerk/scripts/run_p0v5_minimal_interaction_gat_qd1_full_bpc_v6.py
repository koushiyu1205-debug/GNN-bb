#!/usr/bin/env python3
"""Run sequential V6 development-E2E or formal-full100 evidence."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from scripts.p0v5_minimal_interaction_gat_qd1_v6_common import (  # noqa: E402
    DEFAULT_RUN_ROOT, load, terminal, update_state, verify_freezes, write_once,
)
import scripts.run_p0v5_residual_gat_full_bpc_v4 as shared  # noqa: E402
from lunar_ice_bpc.guidance.interaction_gat_queue_runtime_v6 import (  # noqa: E402
    INTERACTION_GAT_EVALUATION_ENV_V6, INTERACTION_GAT_MANIFEST_ENV_V6,
)


BOOTSTRAP = ROOT / "scripts/run_lunar_ice_interaction_gat_acceptance_v6.py"
_SHARED_DEVELOPMENT_DECISION = shared._development_decision
_SHARED_FORMAL_DECISION = shared._formal_decision


def _verify(run_root, root):
    if Path(root).resolve() != ROOT:
        raise SystemExit("V6 full-BPC root mismatch")
    verify_freezes(Path(run_root).resolve())


def _terminal(run_root, reason, detail):
    return terminal(Path(run_root), reason, detail)


def _pass(run_root, detail):
    run_root = Path(run_root)
    write_once(run_root / "terminal_decision.json", {
        "schema_version": "lunar_ice_bpc.p0v5_minimal_interaction_gat_terminal.v6",
        "decision": "PASS", "reason": "FORMAL_FULL100_PASSED",
        "detail": detail, "development_only": True,
        "deployment_authorized": False, "production_switch_authorized": False,
    })
    state = load(run_root / "state.json")
    state.update({
        "current_stage": "TERMINAL", "status": "PASS", "terminal": True,
        "terminal_decision": str((run_root / "terminal_decision.json").resolve()),
    })
    from scripts.p0v5_minimal_interaction_gat_qd1_v6_common import write_mutable
    write_mutable(run_root / "state.json", state)


def _development_decision(payload):
    value = _SHARED_DEVELOPMENT_DECISION(payload)
    value["schema_version"] = (
        "lunar_ice_bpc.p0v5_interaction_gat_qd1_development_decision.v1"
    )
    return value


def _formal_decision(payload):
    value = _SHARED_FORMAL_DECISION(payload)
    value["schema_version"] = (
        "lunar_ice_bpc.p0v5_interaction_gat_qd1_formal_decision.v1"
    )
    return value


def main() -> int:
    shared.DEFAULT_RUN_ROOT = DEFAULT_RUN_ROOT
    shared.BOOTSTRAP = BOOTSTRAP
    shared.INTERACTION_GAT_MANIFEST_ENV_V4 = INTERACTION_GAT_MANIFEST_ENV_V6
    shared.INTERACTION_GAT_EVALUATION_ENV_V4 = INTERACTION_GAT_EVALUATION_ENV_V6
    shared.verify_portfolio_freezes = _verify
    shared._terminal = _terminal
    shared._pass = _pass
    shared._development_decision = _development_decision
    shared._formal_decision = _formal_decision
    # The imported runner mutates only the new V6 run root selected by argv.
    return int(shared.main())


if __name__ == "__main__":
    raise SystemExit(main())

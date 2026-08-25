#!/usr/bin/env python3
"""Terminal-aware V3 adapter for the audited fresh replay runner."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)

DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v3_20260814"


def main() -> int:
    run_root = _run_root(sys.argv[1:])
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        _terminal(run_root, "FREEZE_HASH_DRIFT", str(exc))
        raise SystemExit(str(exc)) from exc
    state = json.loads((run_root / "state.json").read_text(encoding="utf-8"))
    if bool(state.get("terminal")):
        raise SystemExit("terminal V3 chain forbids fresh replay artifact writers")
    import scripts.run_p0v5_context_queue_portfolio_matrix as runner
    return int(runner.main())


def _run_root(arguments):
    if "--run-root" not in arguments:
        return DEFAULT_RUN_ROOT.resolve()
    index = arguments.index("--run-root")
    if index + 1 >= len(arguments):
        raise SystemExit("--run-root requires a value")
    return Path(arguments[index + 1]).resolve()


def _terminal(run_root, reason, detail):
    path = run_root / "terminal_decision.json"
    if path.exists():
        return
    path.write_text(json.dumps({
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_terminal.v3",
        "decision": "FAIL", "reason": reason, "detail": detail,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

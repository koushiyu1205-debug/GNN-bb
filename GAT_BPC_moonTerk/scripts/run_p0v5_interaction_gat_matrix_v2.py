#!/usr/bin/env python3
"""Terminal-aware adapter for the audited V1 fresh replay runner."""

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


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v2_20260807"


def main() -> int:
    run_root = _run_root(sys.argv[1:])
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    if bool(json.loads((run_root / "state.json").read_text(encoding="utf-8")).get("terminal")):
        raise SystemExit("terminal V2 chain forbids fresh replay artifact writers")
    import scripts.run_p0v5_context_queue_portfolio_matrix as runner

    return int(runner.main())


def _run_root(arguments):
    if "--run-root" not in arguments:
        return DEFAULT_RUN_ROOT.resolve()
    index = arguments.index("--run-root")
    if index + 1 >= len(arguments):
        raise SystemExit("--run-root requires a value")
    return Path(arguments[index + 1]).resolve()


if __name__ == "__main__":
    raise SystemExit(main())

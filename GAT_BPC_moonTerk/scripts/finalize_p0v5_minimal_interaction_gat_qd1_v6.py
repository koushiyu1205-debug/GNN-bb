#!/usr/bin/env python3
"""Audit the V6 state machine without bypassing any stage gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.p0v5_minimal_interaction_gat_qd1_v6_common import (
    DEFAULT_RUN_ROOT, load, verify_freezes,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    verify_freezes(run_root)
    state = load(run_root / "state.json")
    prohibited = [
        name for name in (
            "qgr1_force_on.decision.json", "qgr1_ranker.pt",
            "qb1_outcomes.json",
        ) if (run_root / name).exists()
    ]
    if prohibited:
        raise SystemExit("V6 forbidden-arm artifact:" + ",".join(prohibited))
    decision_path = run_root / "terminal_decision.json"
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_minimal_interaction_gat_audit.v6",
        "state": state,
        "terminal_decision": load(decision_path) if decision_path.is_file() else None,
        "action_universe": ["Q0", "QD1"],
        "forbidden_arm_artifacts": prohibited,
        "v5_run_modified_by_v6": False,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

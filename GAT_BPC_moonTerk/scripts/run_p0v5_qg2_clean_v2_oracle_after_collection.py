#!/usr/bin/env python3
"""Run clean-v2 tree supplement and bounded QO2 Oracle after collection."""

from __future__ import annotations

import os
from pathlib import Path

from continue_p0v5_qg2_clean_v2_collection import GUIDANCE_ENV_KEYS
import run_p0v5_qg2_oracle_after_collection as controller


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
EXECUTION_FREEZE = (
    RUN_ROOT / "qg2_clean_v2_oracle_execution_freeze_storage_cap_v3.json"
)
COLLECTION_STATE = RUN_ROOT / "qg2_clean_v2_collection_controller_state.json"
INDEX = RUN_ROOT / "qg2_clean_v2_live_snapshot_index.json"
ORACLE_DIR = RUN_ROOT / "oracle_qg2_clean_v2_storage_cap_v2_stage1"
ORACLE_SUMMARY = RUN_ROOT / "oracle_qg2_clean_v2_storage_cap_v2_stage1.json"
STATE = RUN_ROOT / "qg2_clean_v2_oracle_storage_cap_v2_controller_state.json"
TREE_SUPPLEMENT = ROOT / "scripts/run_p0v5_qg2_clean_v2_tree_supplement.py"


def main() -> int:
    _bind_clean_v2_namespace()
    return int(controller.main())


def _bind_clean_v2_namespace() -> None:
    controller.EXECUTION_FREEZE = EXECUTION_FREEZE
    controller.COLLECTION_STATE = COLLECTION_STATE
    controller.INDEX = INDEX
    controller.ORACLE_DIR = ORACLE_DIR
    controller.ORACLE_SUMMARY = ORACLE_SUMMARY
    controller.STATE = STATE
    controller.TREE_SUPPLEMENT = TREE_SUPPLEMENT
    controller._matching_controller_alive = _matching_controller_alive
    controller._python_env = _python_env


def _matching_controller_alive(pid: int) -> bool:
    path = Path(f"/proc/{int(pid)}/cmdline")
    try:
        command = path.read_bytes().replace(b"\0", b" ").decode(
            "utf-8", errors="replace"
        )
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return (
        "continue_p0v5_qg2_clean_v2_scale_aware_resume.py" in command
    )


def _python_env() -> dict[str, str]:
    env = dict(os.environ)
    for key in GUIDANCE_ENV_KEYS:
        env.pop(key, None)
    env.pop("LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR", None)
    env.pop("LUNAR_ICE_P0V5_QG2_SNAPSHOT_MAX_PER_INSTANCE", None)
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{controller.BUILD}"
    return env


if __name__ == "__main__":
    raise SystemExit(main())

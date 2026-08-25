#!/usr/bin/env python3
"""Train and calibrate clean-v2 only after its bounded Oracle passes."""

from __future__ import annotations

import os
from pathlib import Path

from continue_p0v5_qg2_clean_v2_collection import GUIDANCE_ENV_KEYS
import run_p0v5_qg2_training_after_oracle as controller


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
FREEZE = (
    RUN_ROOT
    / "qg2_clean_v2_post_oracle_controller_freeze_storage_cap_v3.json"
)
ORACLE_STATE = (
    RUN_ROOT / "qg2_clean_v2_oracle_storage_cap_v2_controller_state.json"
)
ORACLE_SUMMARY = RUN_ROOT / "oracle_qg2_clean_v2_storage_cap_v2_stage1.json"
TRAINING_DIR = RUN_ROOT / "training_qg2_clean_v2"
TRAINING_REPORT = TRAINING_DIR / "training_report.json"
CALIBRATION_DIR = RUN_ROOT / "calibration_qg2_clean_v2"
CALIBRATION_REPORT = CALIBRATION_DIR / "calibration_report.json"
STATE = RUN_ROOT / "qg2_clean_v2_post_oracle_controller_state.json"


def main() -> int:
    _bind_clean_v2_namespace()
    return int(controller.main())


def _bind_clean_v2_namespace() -> None:
    controller.FREEZE = FREEZE
    controller.ORACLE_STATE = ORACLE_STATE
    controller.ORACLE_SUMMARY = ORACLE_SUMMARY
    controller.TRAINING_DIR = TRAINING_DIR
    controller.TRAINING_REPORT = TRAINING_REPORT
    controller.CALIBRATION_DIR = CALIBRATION_DIR
    controller.CALIBRATION_REPORT = CALIBRATION_REPORT
    controller.STATE = STATE
    controller._matching_oracle_controller_alive = (
        _matching_oracle_controller_alive
    )
    controller._python_env = _python_env


def _matching_oracle_controller_alive(pid: int) -> bool:
    path = Path(f"/proc/{int(pid)}/cmdline")
    try:
        command = path.read_bytes().replace(b"\0", b" ").decode(
            "utf-8", errors="replace"
        )
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return "run_p0v5_qg2_clean_v2_oracle_after_collection.py" in command


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

#!/usr/bin/env python3
"""Run clean-v2 paired development E2E only after calibration passes."""

from __future__ import annotations

from pathlib import Path

import run_p0v5_qg2_e2e_after_calibration as controller


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
FREEZE = RUN_ROOT / "qg2_clean_v2_e2e_controller_freeze_storage_cap_v3.json"
POST_STATE = RUN_ROOT / "qg2_clean_v2_post_oracle_controller_state.json"
TRAINING_REPORT = RUN_ROOT / "training_qg2_clean_v2/training_report.json"
CALIBRATION_REPORT = RUN_ROOT / "calibration_qg2_clean_v2/calibration_report.json"
OUTPUT_ROOT = RUN_ROOT / "e2e_qg2_clean_v2"
CONTROL_ROOT = OUTPUT_ROOT / "control"
GUIDED_ROOT = OUTPUT_ROOT / "guided"
RESULT = RUN_ROOT / "e2e_development_acceptance_qg2_clean_v2.json"
STATE = RUN_ROOT / "qg2_clean_v2_e2e_controller_state.json"


def main() -> int:
    _bind_clean_v2_namespace()
    return int(controller.main())


def _bind_clean_v2_namespace() -> None:
    controller.FREEZE = FREEZE
    controller.POST_STATE = POST_STATE
    controller.TRAINING_REPORT = TRAINING_REPORT
    controller.CALIBRATION_REPORT = CALIBRATION_REPORT
    controller.OUTPUT_ROOT = OUTPUT_ROOT
    controller.CONTROL_ROOT = CONTROL_ROOT
    controller.GUIDED_ROOT = GUIDED_ROOT
    controller.RESULT = RESULT
    controller.STATE = STATE
    controller._matching_post_controller_alive = _matching_post_controller_alive


def _matching_post_controller_alive(pid: int) -> bool:
    path = Path(f"/proc/{int(pid)}/cmdline")
    try:
        command = path.read_bytes().replace(b"\0", b" ").decode(
            "utf-8", errors="replace"
        )
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return "run_p0v5_qg2_clean_v2_training_after_oracle.py" in command


if __name__ == "__main__":
    raise SystemExit(main())

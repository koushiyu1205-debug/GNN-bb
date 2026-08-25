#!/usr/bin/env python3
"""Start the post-test QG2 admission-aware collection in a fresh namespace.

The frozen clean-v1 controller remains untouched.  This wrapper binds that
controller to clean-v2 paths, strips every learning-guidance environment
variable before any child process is created, and writes a separate Oracle
preflight artifact.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import continue_p0v5_qg2_admission_v4_collection as controller


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
COLLECTION_ID = "qg2_clean_v2"
SNAPSHOT_DIR = RUN_ROOT / "fallback_snapshots_qg2_clean_v2"
FREEZE = RUN_ROOT / "qg2_clean_v2_collection_freeze.json"
INDEX = RUN_ROOT / "qg2_clean_v2_live_snapshot_index.json"
STATE = RUN_ROOT / "qg2_clean_v2_collection_controller_state.json"

GUIDANCE_ENV_KEYS = (
    "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST",
    "LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE",
    "LUNAR_ICE_PROOF_QUEUE_GAT_MANIFEST",
    "LUNAR_ICE_PROOF_QUEUE_GAT_EVALUATION_MODE",
    "LUNAR_ICE_BIDIRECTIONAL_GATE_GAT_MANIFEST",
    "LUNAR_ICE_BIDIRECTIONAL_GATE_GAT_EVALUATION_MODE",
    "LUNAR_ICE_GAT_DEPLOYMENT_MANIFEST",
    "LUNAR_ICE_GAT_GUIDANCE_MODE",
    "LUNAR_ICE_GAT_TRAINING_ROWS_DIR",
    "LUNAR_ICE_P0V5_QG2_SNAPSHOT_GLOBAL_STORAGE_CAP",
    "LUNAR_ICE_P0V5_QG2_SNAPSHOT_PER_SCALE_STORAGE_CAP",
)


def main() -> int:
    _sanitize_environment()
    _bind_clean_v2_namespace()
    return int(controller.main())


def _sanitize_environment() -> None:
    for key in GUIDANCE_ENV_KEYS:
        os.environ.pop(key, None)


def _bind_clean_v2_namespace() -> None:
    controller.COLLECTION_ID = COLLECTION_ID
    controller.SNAPSHOT_DIR = SNAPSHOT_DIR
    controller.FREEZE = FREEZE
    controller.INDEX = INDEX
    controller.STATE = STATE
    controller._run_preflight = _run_preflight


def _run_preflight() -> int:
    output = RUN_ROOT / "oracle_qg2_clean_v2_preflight.json"
    command = [
        sys.executable,
        str(ROOT / "scripts/run_p0v5_qg2_bounded_oracle.py"),
        "--state-index", str(INDEX),
        "--output-dir", str(RUN_ROOT / "oracle_qg2_clean_v2"),
        "--output", str(output),
        "--preflight-only",
    ]
    return subprocess.run(
        command,
        cwd=ROOT,
        env=controller._python_env(),
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())

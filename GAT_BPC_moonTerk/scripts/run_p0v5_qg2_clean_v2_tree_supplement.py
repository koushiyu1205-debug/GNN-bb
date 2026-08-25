#!/usr/bin/env python3
"""Run the frozen clean-v2 bounded real-tree snapshot supplement."""

from __future__ import annotations

import os
from pathlib import Path

from continue_p0v5_qg2_clean_v2_collection import GUIDANCE_ENV_KEYS
import run_p0v5_qg2_clean_v1_tree_supplement as controller


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
PLAN = (
    RUN_ROOT / "qg2_clean_v2_tree_supplement_freeze_storage_cap_v3.json"
)
COLLECTION_FREEZE = (
    RUN_ROOT / "qg2_clean_v2_collection_freeze_storage_cap_v4.json"
)
SNAPSHOT_DIR = RUN_ROOT / "fallback_snapshots_qg2_clean_v2"
INDEX = RUN_ROOT / "qg2_clean_v2_live_snapshot_index.json"
STATE = RUN_ROOT / "qg2_clean_v2_tree_supplement_storage_cap_v2_state.json"


def main() -> int:
    _bind_clean_v2_namespace()
    return int(controller.main())


def _bind_clean_v2_namespace() -> None:
    controller.PLAN = PLAN
    controller.COLLECTION_FREEZE = COLLECTION_FREEZE
    controller.SNAPSHOT_DIR = SNAPSHOT_DIR
    controller.INDEX = INDEX
    controller.STATE = STATE
    controller._output_dir = _output_dir
    controller._environment = _environment


def _output_dir(scale: int) -> Path:
    return (
        RUN_ROOT
        / f"snapshot_collection_qg2_clean_v2_tree_storage_cap_v2_scale{scale}"
    )


def _environment() -> dict[str, str]:
    env = dict(os.environ)
    for key in GUIDANCE_ENV_KEYS:
        env.pop(key, None)
    env.update({
        "LUNAR_ICE_P0V5_QG2_SNAPSHOT_MAX_PER_INSTANCE": "15",
        "LUNAR_ICE_P0V5_QG2_SNAPSHOT_GLOBAL_STORAGE_CAP": "450",
        "LUNAR_ICE_P0V5_QG2_SNAPSHOT_PER_SCALE_STORAGE_CAP": "225",
        "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR": str(SNAPSHOT_DIR),
        "PYTHONPATH": f"{ROOT / 'src'}:{controller.BUILD}",
    })
    return env


if __name__ == "__main__":
    raise SystemExit(main())

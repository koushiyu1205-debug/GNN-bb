#!/usr/bin/env python3
"""Freeze the trace-view binding repair and resume Q0/QG2 force-on."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/p0v5_qg2_v5_trace_first_20260807"
SOURCE_RUN = ROOT / "runs/p0v5_qg2_v4_realmap_gat_first_20260806"
TRAINING_FREEZE = RUN / "label_gat_training_freeze.json"
TRAINING_REPORT = RUN / "label_gat/training_report.json"
TRAINING_VIEW = RUN / "trace_training_view.json"
SPLIT = SOURCE_RUN / "realmap_v4_instance_split.json"
REPAIR_FREEZE = RUN / "force_on_trace_view_binding_repair_freeze.json"
OUTPUT_DIR = RUN / "label_gat_force_on_train_screen"
OUTPUT = OUTPUT_DIR / "force_on_train.json"
WRAPPER = ROOT / "scripts/calibrate_p0v5_qg2_v5_trace_gat_force_on.py"


def main() -> int:
    _freeze_or_validate()
    completed = subprocess.run([
        sys.executable, str(WRAPPER),
        "--training-report", str(TRAINING_REPORT),
        "--oracle-summary", str(TRAINING_VIEW),
        "--output-dir", str(OUTPUT_DIR),
        "--output", str(OUTPUT),
        "--partition", "train",
        "--repeats", "3",
        "--maximum-contexts-per-scale", "5",
        "--scale30-wall-sec", "300",
        "--scale50-wall-sec", "600",
        "--memory-limit-gb", "10.867",
    ], cwd=ROOT, env=_environment(), check=False)
    if completed.returncode != 0 or not OUTPUT.is_file():
        return int(completed.returncode) or 2
    payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    if (
        bool(payload.get("identity_checks_relaxed"))
        or not bool(payload.get(
            "engine_config_action_policy_hash_checks_retained"
        ))
    ):
        raise SystemExit("force-on binding repair weakened identity checks")
    return 0


def _freeze_or_validate() -> None:
    training = json.loads(TRAINING_REPORT.read_text(encoding="utf-8"))
    gat = [
        dict(row) for row in training.get("models") or ()
        if str(row.get("model_kind") or "") == "gat"
    ]
    if len(gat) != 1:
        raise SystemExit("binding repair requires one frozen Label GAT")
    checkpoint = Path(gat[0]["checkpoint_path"])
    sources = (
        Path(__file__).resolve(), WRAPPER,
        ROOT / "scripts/calibrate_p0v5_qg2_v4_instance_balanced_gat_force_on.py",
        ROOT / "scripts/calibrate_p0v5_qg2_v3_gat_force_on.py",
        ROOT / "scripts/predict_p0v5_qg2_v3_potential.py",
        ROOT / "scripts/replay_p0v5_qg2_label_state_snapshot.py",
    )
    artifacts = (
        TRAINING_FREEZE, TRAINING_REPORT, TRAINING_VIEW, SPLIT, checkpoint,
    )
    payload = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_force_on_binding_repair_freeze.v1"
        ),
        "development_only": True,
        "deployable": False,
        "repair_scope": (
            "context_row_identity_restored_from_bound_snapshot_only"
        ),
        "identity_checks_relaxed": False,
        "source_sha256": {str(path): _sha256(path) for path in sources},
        "artifact_sha256": {str(path): _sha256(path) for path in artifacts},
        "production_switch_authorized": False,
    }
    if REPAIR_FREEZE.is_file():
        if json.loads(REPAIR_FREEZE.read_text(encoding="utf-8")) != payload:
            raise SystemExit("force-on binding repair freeze drift")
    else:
        _write(REPAIR_FREEZE, payload)


def _environment() -> dict[str, str]:
    env = dict(os.environ)
    build = ROOT / "build/native-spprc-bidirectional-feasibility-v1"
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{build}"
    for key in (
        "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST",
        "LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE",
        "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_MANIFEST",
        "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_EVALUATION_MODE",
    ):
        env.pop(key, None)
    return env


def _write(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

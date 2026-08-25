#!/usr/bin/env python3
"""Resume clean-v2 after the scale-specific action-hash amendment.

The original controller correctly collected scale30 and scale50/001, but its
single frozen action-policy hash represented only the scale30 admission
contract.  This fail-closed continuation preserves those immutable artifacts,
validates them with the amended per-scale contract, reruns only the interrupted
scale50 suffix, and then returns to the original bounded prefix extension.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

import continue_p0v5_qg2_admission_v4_collection as controller
from continue_p0v5_qg2_clean_v2_collection import GUIDANCE_ENV_KEYS


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
COLLECTION_ID = "qg2_clean_v2"
AMENDMENT_ID = "scale_aware_exact_action_policy_hash_v1"
SNAPSHOT_DIR = RUN_ROOT / "fallback_snapshots_qg2_clean_v2"
FREEZE = (
    RUN_ROOT / "qg2_clean_v2_collection_freeze_scale_aware_v3.json"
)
INDEX = RUN_ROOT / "qg2_clean_v2_live_snapshot_index.json"
STATE = RUN_ROOT / "qg2_clean_v2_collection_controller_state.json"
SCALE30_INITIAL = (
    RUN_ROOT
    / "snapshot_collection_qg2_clean_v2_scale30_batch01"
    / "scale_030"
    / "b4_2_cold_exact_rows.csv"
)
SCALE50_INTERRUPTED = (
    RUN_ROOT
    / "snapshot_collection_qg2_clean_v2_scale50_batch01"
    / "scale_050"
    / "b4_2_cold_exact_rows.csv"
)
SCALE50_RESUME_OUTPUT = (
    RUN_ROOT / "snapshot_collection_qg2_clean_v2_scale50_resume_batch01"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = max(1.0, min(60.0, float(args.poll_sec)))
    _sanitize_environment()
    _bind_namespace()
    _validate_amended_freeze()
    controller._wait_for_native_idle(poll)
    _validate_preserved_prefix()

    coverage = controller._build_index()
    _require_preserved_coverage(coverage)
    controller._state(
        "SCALE_HASH_CONTRACT_AMENDMENT_VALIDATED",
        amendment_id=AMENDMENT_ID,
        coverage=coverage,
        preserved_scale30_rows=30,
        preserved_scale50_rows=1,
    )

    if SCALE50_RESUME_OUTPUT.exists():
        raise SystemExit(
            "scale-aware continuation refuses implicit resume or overwrite: "
            f"{SCALE50_RESUME_OUTPUT}"
        )
    controller._state(
        "RUNNING_SCALE50_INTERRUPTED_SUFFIX",
        amendment_id=AMENDMENT_ID,
        coverage=coverage,
        instance_start=2,
        instance_stop=30,
    )
    controller._run_acceptance(
        scale=50,
        instances=controller._instances(controller.SCALE50_ROOT)[1:30],
        output_dir=SCALE50_RESUME_OUTPUT,
    )
    coverage = controller._build_index()
    coverage = controller._extend_frozen_prefix_until_target(coverage)

    preflight = controller._run_preflight()
    ready = controller._collection_target_ready(coverage)
    controller._state(
        "ORACLE_PREFLIGHT_READY" if ready and preflight == 0 else (
            "COVERAGE_INCOMPLETE"
        ),
        amendment_id=AMENDMENT_ID,
        coverage=coverage,
        preflight_exit_code=preflight,
        preserved_pre_amendment_data=True,
        scale30_recollection_performed=False,
    )
    return 0 if ready and preflight == 0 else 2


def _bind_namespace() -> None:
    controller.COLLECTION_ID = COLLECTION_ID
    controller.SNAPSHOT_DIR = SNAPSHOT_DIR
    controller.FREEZE = FREEZE
    controller.INDEX = INDEX
    controller.STATE = STATE
    controller._run_preflight = _run_preflight


def _sanitize_environment() -> None:
    for key in GUIDANCE_ENV_KEYS:
        os.environ.pop(key, None)


def _run_preflight() -> int:
    import subprocess
    import sys

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


def _validate_preserved_prefix() -> None:
    scale30_rows = _csv_row_count(SCALE30_INITIAL)
    scale50_rows = _csv_row_count(SCALE50_INTERRUPTED)
    if scale30_rows != 30 or scale50_rows != 1:
        raise SystemExit(
            "unexpected preserved clean-v2 prefix: "
            f"scale30_rows={scale30_rows}, scale50_rows={scale50_rows}"
        )
    interrupted_pool = (
        SCALE50_INTERRUPTED.parent
        / "pools"
        / "scale_050"
        / "instance_002"
    )
    if not interrupted_pool.exists():
        raise SystemExit("interrupted scale50/002 diagnostic pool is missing")


def _require_preserved_coverage(coverage: dict) -> None:
    scale30 = dict(coverage.get("30") or {})
    scale50 = dict(coverage.get("50") or {})
    if (
        int(scale30.get("context_count") or 0) != 34
        or int(scale30.get("instance_count") or 0) != 28
        or int(scale50.get("context_count") or 0) != 1
        or int(scale50.get("instance_count") or 0) != 1
    ):
        raise SystemExit(
            "amended strict index does not reproduce the preserved prefix: "
            f"coverage={coverage}"
        )
    payload = _load(INDEX)
    if int(payload.get("excluded_count") or 0) != 0:
        raise SystemExit("amended strict index contains excluded snapshots")


def _validate_amended_freeze() -> None:
    payload = _load(FREEZE)
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_clean_collection_freeze.v3"
    ):
        raise SystemExit("scale-aware collection freeze schema mismatch")
    if payload.get("amendment_id") != AMENDMENT_ID:
        raise SystemExit("scale-aware collection amendment id mismatch")
    expected = {
        "30": (
            "9dcedb7b74c0a9c20a3a64484067b873"
            "00b9267e8bd450fcfff74d2a8c7406ca"
        ),
        "50": (
            "b2f9eab6bd01d12a0f4319342550733d"
            "db0510e559d5e6a6abc119765d2203e2"
        ),
    }
    if dict(payload.get(
        "required_exact_action_policy_hashes_by_scale"
    ) or {}) != expected:
        raise SystemExit("scale-aware exact-action policy mapping mismatch")
    for raw_path, digest in dict(
        payload.get("frozen_file_sha256") or {}
    ).items():
        path = Path(raw_path)
        path = path if path.is_absolute() else ROOT / path
        if not path.is_file() or _sha256(path) != str(digest):
            raise SystemExit(f"scale-aware frozen file drift: {path}")


def _csv_row_count(path: Path) -> int:
    if not path.is_file():
        return -1
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _row in csv.DictReader(handle))


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

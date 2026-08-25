#!/usr/bin/env python3
"""Post-candidate formal ordering-safety audit for training-only-v2 QG2."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import audit_p0v5_qg2_formal_ordering_safety as base  # noqa: E402


RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
FREEZE = RUN_ROOT / "qg2_training_only_v2_formal_ordering_safety_freeze.json"
FINALIZER_FREEZE = (
    RUN_ROOT / "qg2_training_only_v2_candidate_finalizer_freeze.json"
)
ACCEPTANCE = RUN_ROOT / "formal_full20_acceptance_qg2_training_only_v2.json"
CANDIDATE = (
    RUN_ROOT
    / "P0V5_QG2_LABEL_STATE_GAT_TRAINING_ONLY_V2_candidate_freeze.json"
)
OUTPUT = RUN_ROOT / "qg2_training_only_v2_formal_ordering_safety_audit.json"
EXTENSION = (
    RUN_ROOT
    / "P0V5_QG2_LABEL_STATE_GAT_TRAINING_ONLY_V2_candidate_safety_extension.json"
)
STATE = RUN_ROOT / "qg2_training_only_v2_formal_ordering_safety_state.json"

ACCEPTANCE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_paired_acceptance.v1"
CANDIDATE_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_training_only_v2_candidate_freeze.v1"
)
SCALES = (5, 10, 20, 30, 50)
BYPASS_SCALES = (5, 10, 20)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-for-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    _validate_freeze()
    _state("WAITING_FOR_TRAINING_ONLY_V2_CANDIDATE_FINALIZER", wait_for_pid=args.wait_for_pid)
    poll = max(1.0, min(60.0, float(args.poll_sec)))
    while _matching_finalizer_alive(args.wait_for_pid):
        time.sleep(poll)
    if not ACCEPTANCE.is_file() or not CANDIDATE.is_file():
        _state("NOT_STARTED_FORMAL_ACCEPTANCE_OR_CANDIDATE_MISSING")
        return 2
    if OUTPUT.exists() or EXTENSION.exists():
        raise SystemExit("training-only-v2 formal safety audit refuses overwrite")

    _state("RUNNING_TRAINING_ONLY_V2_FORMAL_ORDERING_SAFETY_AUDIT")
    audit = audit_formal(acceptance_path=ACCEPTANCE, candidate_path=CANDIDATE)
    _write(OUTPUT, audit)
    if not bool(audit["passed"]):
        _state(
            "TRAINING_ONLY_V2_FORMAL_ORDERING_SAFETY_FAILED",
            audit=str(OUTPUT),
            audit_sha256=_sha256(OUTPUT),
            violations=audit["violations"],
        )
        return 2
    extension = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_training_only_v2_candidate_safety_extension.v1"
        ),
        "status": "FROZEN_FORMAL_ORDERING_SAFETY_EXTENSION",
        "frozen_at_local": datetime.now().astimezone().isoformat(timespec="seconds"),
        "development_only": True,
        "production_default": False,
        "production_switch_performed": False,
        "historical_baselines_unchanged": True,
        "base_candidate": _relative(CANDIDATE),
        "base_candidate_sha256": _sha256(CANDIDATE),
        "formal_acceptance": _relative(ACCEPTANCE),
        "formal_acceptance_sha256": _sha256(ACCEPTANCE),
        "ordering_safety_audit": _relative(OUTPUT),
        "ordering_safety_audit_sha256": _sha256(OUTPUT),
        "control_root_hash": audit["control_root_hash"],
        "guided_root_hash": audit["guided_root_hash"],
        "scale5_10_20_literal_q0_verified": True,
        "frozen_file_sha256": {
            _relative(Path(__file__).resolve()): _sha256(Path(__file__).resolve()),
            _relative(FREEZE): _sha256(FREEZE),
            _relative(FINALIZER_FREEZE): _sha256(FINALIZER_FREEZE),
            _relative(CANDIDATE): _sha256(CANDIDATE),
            _relative(ACCEPTANCE): _sha256(ACCEPTANCE),
            _relative(OUTPUT): _sha256(OUTPUT),
        },
    }
    _write(EXTENSION, extension)
    _state(
        "TRAINING_ONLY_V2_FORMAL_ORDERING_SAFETY_EXTENSION_FROZEN",
        audit=str(OUTPUT),
        audit_sha256=_sha256(OUTPUT),
        extension=str(EXTENSION),
        extension_sha256=_sha256(EXTENSION),
        production_switch_performed=False,
    )
    return 0


def audit_formal(*, acceptance_path: Path, candidate_path: Path) -> dict[str, Any]:
    acceptance = _load(acceptance_path)
    candidate = _load(candidate_path)
    violations: list[str] = []
    if not bool(
        acceptance.get("schema_version") == ACCEPTANCE_SCHEMA
        and acceptance.get("mode") == "formal"
        and acceptance.get("passed")
        and int(acceptance.get("violation_count") or 0) == 0
        and {int(value) for value in (acceptance.get("by_scale") or {})}
        == set(SCALES)
    ):
        violations.append("formal_acceptance_not_passed")
    if not bool(
        candidate.get("schema_version") == CANDIDATE_SCHEMA
        and candidate.get("status") == "FROZEN_EXPERIMENT_CANDIDATE"
        and not candidate.get("production_default")
        and not candidate.get("production_switch_performed")
        and candidate.get("historical_baselines_unchanged")
        and candidate.get("fallback_action") == "Q0"
    ):
        violations.append("candidate_not_frozen_or_safe")
    violations.extend(
        f"candidate_{value}" for value in base._frozen_file_drift(candidate)
    )

    root_rows: dict[str, dict[str, Any]] = {}
    for role in ("control", "guided"):
        root = _resolve(acceptance.get(f"{role}_root") or "")
        expected = str(acceptance.get(f"{role}_root_hash") or "")
        observed = base._artifact_tree_hash(root) if root.is_dir() else ""
        if not observed or observed != expected:
            violations.append(f"{role}_root_hash_mismatch")
        metrics = base.scan_tree_root(root, role=role)
        root_rows[role] = {
            "root": str(root),
            "expected_hash": expected,
            "observed_hash": observed,
            **metrics,
        }
    violations.extend(_runtime_violations(root_rows))
    return {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_training_only_v2_formal_ordering_safety_audit.v1"
        ),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "development_only": True,
        "formal_acceptance": str(acceptance_path),
        "formal_acceptance_sha256": _sha256(acceptance_path),
        "candidate": str(candidate_path),
        "candidate_sha256": _sha256(candidate_path),
        "control_root_hash": root_rows.get("control", {}).get("observed_hash", ""),
        "guided_root_hash": root_rows.get("guided", {}).get("observed_hash", ""),
        "roots": root_rows,
        "violations": violations,
        "violation_count": len(violations),
        "passed": not violations,
    }


def _runtime_violations(root_rows: dict[str, dict[str, Any]]) -> list[str]:
    violations = []
    zero_keys = (
        "drop_count_total",
        "labels_dropped_true_count",
        "forbidden_authority_true_count",
        "guidance_validation_issue_count",
        "hash_or_checkpoint_drift_count",
        "invalid_action_count",
        "qg2_action_runtime_disabled_count",
        "qg2_action_on_bypassed_scale_count",
    )
    for role in ("control", "guided"):
        metrics = dict(root_rows.get(role) or {})
        if int(metrics.get("tree_count") or 0) != 100:
            violations.append(f"{role}_tree_count_mismatch:{metrics.get('tree_count', 0)}")
        for key in zero_keys:
            if int(metrics.get(key) or 0) != 0:
                violations.append(f"{role}_{key}:{metrics.get(key)}")
        by_scale = dict(metrics.get("by_scale") or {})
        for scale in SCALES:
            row = dict(by_scale.get(str(scale)) or {})
            if int(row.get("tree_count") or 0) != 20:
                violations.append(
                    f"{role}_scale{scale}_tree_count_mismatch:{row.get('tree_count', 0)}"
                )
    control = dict(root_rows.get("control") or {})
    if int(control.get("qg2_action_count") or 0) != 0:
        violations.append("control_qg2_action_count_nonzero")
    if int(control.get("inference_event_count") or 0) != 0:
        violations.append("control_qg2_inference_event_count_nonzero")
    guided_scales = dict((root_rows.get("guided") or {}).get("by_scale") or {})
    for scale in BYPASS_SCALES:
        row = dict(guided_scales.get(str(scale)) or {})
        if int(row.get("qg2_action_count") or 0) != 0:
            violations.append(f"guided_scale{scale}_qg2_action_count_nonzero")
        if int(row.get("inference_event_count") or 0) != 0:
            violations.append(f"guided_scale{scale}_qg2_inference_event_count_nonzero")
    return violations


def _validate_freeze() -> None:
    payload = _load(FREEZE)
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_training_only_v2_formal_ordering_safety_freeze.v1"
    ):
        raise SystemExit("training-only-v2 formal safety freeze schema mismatch")
    if not bool(
        payload.get("development_only")
        and not payload.get("deployable")
        and not payload.get("production_default")
        and payload.get("fallback_action") == "Q0"
    ):
        raise SystemExit("training-only-v2 formal safety freeze policy mismatch")
    if str(payload.get("finalizer_freeze_sha256") or "") != _sha256(FINALIZER_FREEZE):
        raise SystemExit("training-only-v2 finalizer freeze drift")
    for raw_path, expected in dict(payload.get("frozen_file_sha256") or {}).items():
        path = _resolve(raw_path)
        if not path.is_file() or _sha256(path) != str(expected):
            raise SystemExit(f"training-only-v2 formal safety frozen drift: {path}")


def _matching_finalizer_alive(pid: int) -> bool:
    try:
        command = Path(f"/proc/{int(pid)}/cmdline").read_bytes().replace(
            b"\0", b" "
        ).decode("utf-8", errors="replace")
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return "finalize_p0v5_qg2_training_only_v2_candidate.py" in command


def _state(status: str, **extra: Any) -> None:
    _write(STATE, {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_training_only_v2_formal_ordering_safety_state.v1"
        ),
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": status,
        "production_switch_performed": False,
        **extra,
    })


def _relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

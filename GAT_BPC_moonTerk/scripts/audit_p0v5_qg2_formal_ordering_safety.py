#!/usr/bin/env python3
"""Bind the frozen QG2 candidate to a recursive formal ordering-safety audit.

The paired acceptance analyzer already owns objective, exact-count, timing, RC,
and certificate gates.  This read-only extension closes the remaining runtime
surface: every persisted tree telemetry payload must show zero label/filter
drops, zero forbidden guidance authority, and zero hash/schema/checkpoint drift.
It never starts a solver and never changes the historical candidate.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
FREEZE = RUN_ROOT / "qg2_formal_ordering_safety_controller_freeze.json"
ACCEPTANCE = RUN_ROOT / "formal_full20_acceptance_qg2_action_surface_v2.json"
CANDIDATE = (
    RUN_ROOT
    / "P0V5_QG2_ACTION_SURFACE_V2_LABEL_STATE_GAT_candidate_freeze.json"
)
OUTPUT = RUN_ROOT / "p0v5_qg2_formal_ordering_safety_audit.json"
EXTENSION = (
    RUN_ROOT
    / "P0V5_QG2_ACTION_SURFACE_V2_candidate_safety_extension.json"
)
STATE = RUN_ROOT / "qg2_formal_ordering_safety_controller_state.json"

ACCEPTANCE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_paired_acceptance.v1"
CANDIDATE_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_action_surface_v2_candidate_freeze.v1"
)
DROP_COUNT_KEYS = (
    "guidance_filter_count",
    "guidance_arc_drop_count",
    "guidance_label_drop_count",
    "guidance_branch_pair_drop_count",
)
FORBIDDEN_AUTHORITY_KEYS = (
    "guidance_can_filter",
    "guidance_can_prune",
    "guidance_can_change_bound",
    "guidance_can_certify",
)
DRIFT_TOKENS = (
    "hash_mismatch",
    "hash drift",
    "hash_drift",
    "checkpoint",
    "binding_mismatch",
    "schema_mismatch",
    "manifest_mismatch",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-for-pid", action="append", type=int, default=[])
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    _validate_freeze()
    wait_pids = tuple(dict.fromkeys(int(pid) for pid in args.wait_for_pid))
    _state("WAITING_FOR_CANDIDATE_FINALIZERS", wait_for_pids=list(wait_pids))
    poll = max(1.0, min(60.0, float(args.poll_sec)))
    while any(_matching_finalizer_alive(pid) for pid in wait_pids):
        time.sleep(poll)
    if not ACCEPTANCE.is_file() or not CANDIDATE.is_file():
        _state("NOT_STARTED_FORMAL_ACCEPTANCE_OR_CANDIDATE_MISSING")
        return 0
    if OUTPUT.exists() or EXTENSION.exists():
        raise SystemExit("QG2 formal ordering safety audit refuses overwrite")
    _state("RUNNING_RECURSIVE_FORMAL_ORDERING_SAFETY_AUDIT")
    audit = audit_formal(acceptance_path=ACCEPTANCE, candidate_path=CANDIDATE)
    _write(OUTPUT, audit)
    if not bool(audit["passed"]):
        _state(
            "FORMAL_ORDERING_SAFETY_FAILED",
            audit=str(OUTPUT),
            audit_sha256=_sha256(OUTPUT),
            violations=audit["violations"],
        )
        return 2
    extension = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_candidate_safety_extension.v1"
        ),
        "status": "FROZEN_FORMAL_ORDERING_SAFETY_EXTENSION",
        "frozen_at_local": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "development_only": True,
        "production_default": False,
        "historical_baselines_unchanged": True,
        "base_candidate": _relative(CANDIDATE),
        "base_candidate_sha256": _sha256(CANDIDATE),
        "formal_acceptance": _relative(ACCEPTANCE),
        "formal_acceptance_sha256": _sha256(ACCEPTANCE),
        "ordering_safety_audit": _relative(OUTPUT),
        "ordering_safety_audit_sha256": _sha256(OUTPUT),
        "control_root_hash": audit["control_root_hash"],
        "guided_root_hash": audit["guided_root_hash"],
        "frozen_file_sha256": {
            _relative(Path(__file__).resolve()): _sha256(Path(__file__).resolve()),
            _relative(FREEZE): _sha256(FREEZE),
            _relative(CANDIDATE): _sha256(CANDIDATE),
            _relative(ACCEPTANCE): _sha256(ACCEPTANCE),
            _relative(OUTPUT): _sha256(OUTPUT),
        },
    }
    _write(EXTENSION, extension)
    _state(
        "FORMAL_ORDERING_SAFETY_EXTENSION_FROZEN",
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
    violations = []
    if not bool(
        acceptance.get("schema_version") == ACCEPTANCE_SCHEMA
        and acceptance.get("mode") == "formal"
        and acceptance.get("passed")
        and int(acceptance.get("violation_count") or 0) == 0
    ):
        violations.append("formal_acceptance_not_passed")
    if not bool(
        candidate.get("schema_version") == CANDIDATE_SCHEMA
        and candidate.get("status") == "FROZEN_EXPERIMENT_CANDIDATE"
        and not candidate.get("production_default")
    ):
        violations.append("candidate_not_frozen_or_safe")
    candidate_drift = _frozen_file_drift(candidate)
    violations.extend(f"candidate_{value}" for value in candidate_drift)

    root_rows = {}
    for role in ("control", "guided"):
        root = _resolve(acceptance.get(f"{role}_root") or "")
        expected = str(acceptance.get(f"{role}_root_hash") or "")
        observed = _artifact_tree_hash(root) if root.is_dir() else ""
        if not observed or observed != expected:
            violations.append(f"{role}_root_hash_mismatch")
        metrics = scan_tree_root(root, role=role)
        root_rows[role] = {
            "root": str(root),
            "expected_hash": expected,
            "observed_hash": observed,
            **metrics,
        }
        if metrics["tree_count"] != 20 * 5:
            violations.append(
                f"{role}_tree_count_mismatch:{metrics['tree_count']}"
            )
        for key in (
            "drop_count_total",
            "labels_dropped_true_count",
            "forbidden_authority_true_count",
            "guidance_validation_issue_count",
            "hash_or_checkpoint_drift_count",
            "invalid_action_count",
            "qg2_action_runtime_disabled_count",
            "qg2_action_on_bypassed_scale_count",
        ):
            if int(metrics[key]) != 0:
                violations.append(f"{role}_{key}:{metrics[key]}")
    if int(root_rows.get("control", {}).get("qg2_action_count") or 0) != 0:
        violations.append("control_qg2_action_count_nonzero")
    return {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_formal_ordering_safety_audit.v1"
        ),
        "generated_at": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "development_only": True,
        "formal_acceptance": str(acceptance_path),
        "formal_acceptance_sha256": _sha256(acceptance_path),
        "candidate": str(candidate_path),
        "candidate_sha256": _sha256(candidate_path),
        "control_root_hash": root_rows.get("control", {}).get(
            "observed_hash", ""
        ),
        "guided_root_hash": root_rows.get("guided", {}).get(
            "observed_hash", ""
        ),
        "roots": root_rows,
        "violations": violations,
        "violation_count": len(violations),
        "passed": not violations,
    }


def scan_tree_root(root: Path, *, role: str) -> dict[str, Any]:
    totals = {
        "tree_count": 0,
        "dictionary_count": 0,
        "drop_count_total": 0,
        "labels_dropped_true_count": 0,
        "forbidden_authority_true_count": 0,
        "guidance_validation_issue_count": 0,
        "hash_or_checkpoint_drift_count": 0,
        "inference_event_count": 0,
        "qg2_action_count": 0,
        "invalid_action_count": 0,
        "qg2_action_runtime_disabled_count": 0,
        "qg2_action_on_bypassed_scale_count": 0,
    }
    by_scale: dict[str, dict[str, int]] = {}
    for path in sorted(root.rglob("tree_closure_001.json")):
        try:
            payload = _load(path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            totals["invalid_action_count"] += 1
            continue
        scale = _scale_from_path(path)
        row = _scan_payload(payload, role=role, scale=scale)
        totals["tree_count"] += 1
        for key, value in row.items():
            totals[key] += int(value)
        scale_row = by_scale.setdefault(str(scale), {
            "tree_count": 0,
            "qg2_action_count": 0,
            "inference_event_count": 0,
        })
        scale_row["tree_count"] += 1
        scale_row["qg2_action_count"] += row["qg2_action_count"]
        scale_row["inference_event_count"] += row["inference_event_count"]
    totals["by_scale"] = by_scale
    return totals


def _scan_payload(payload: object, *, role: str, scale: int) -> dict[str, int]:
    result = {
        "dictionary_count": 0,
        "drop_count_total": 0,
        "labels_dropped_true_count": 0,
        "forbidden_authority_true_count": 0,
        "guidance_validation_issue_count": 0,
        "hash_or_checkpoint_drift_count": 0,
        "inference_event_count": 0,
        "qg2_action_count": 0,
        "invalid_action_count": 0,
        "qg2_action_runtime_disabled_count": 0,
        "qg2_action_on_bypassed_scale_count": 0,
    }

    def visit(value: object) -> None:
        if isinstance(value, dict):
            result["dictionary_count"] += 1
            for key in DROP_COUNT_KEYS:
                result["drop_count_total"] += _nonnegative_int(value.get(key))
            if _truthy(value.get("labels_dropped")):
                result["labels_dropped_true_count"] += 1
            result["forbidden_authority_true_count"] += sum(
                _truthy(value.get(key)) for key in FORBIDDEN_AUTHORITY_KEYS
            )
            issues = value.get("guidance_validation_issues")
            if isinstance(issues, (list, tuple, dict, set)) and len(issues) > 0:
                result["guidance_validation_issue_count"] += 1
            elif isinstance(issues, str) and issues.strip():
                result["guidance_validation_issue_count"] += 1
            action = str(value.get("proof_tail_gat_action") or "")
            if action:
                if action not in {"Q0", "QG2"}:
                    result["invalid_action_count"] += 1
                if action == "QG2":
                    result["qg2_action_count"] += 1
                    if role != "guided":
                        result["invalid_action_count"] += 1
                    if scale not in {30, 50}:
                        result["qg2_action_on_bypassed_scale_count"] += 1
                    if not _truthy(value.get("proof_tail_gat_runtime_enabled")):
                        result["qg2_action_runtime_disabled_count"] += 1
            wall = _nonnegative_float(
                value.get("proof_tail_gat_inference_wall_ms")
            )
            if wall is not None and wall > 0.0:
                result["inference_event_count"] += 1
            reason = str(value.get("proof_tail_gat_fallback_reason") or "").lower()
            if role == "guided" and any(token in reason for token in DRIFT_TOKENS):
                result["hash_or_checkpoint_drift_count"] += 1
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(payload)
    return result


def _artifact_tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    paths = set()
    for pattern in (
        "**/b4_2_cold_exact_rows.csv",
        "**/b4_2_cold_exact_state.json",
        "**/b4_2_cold_exact_summary.json",
        "**/tree_closure_001.json",
    ):
        paths.update(root.glob(pattern))
    if not paths:
        return ""
    for path in sorted(paths):
        digest.update(str(path.relative_to(root)).encode("utf-8"))
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _frozen_file_drift(payload: dict) -> list[str]:
    issues = []
    for raw_path, expected in dict(payload.get("frozen_file_sha256") or {}).items():
        path = _resolve(raw_path)
        if not path.is_file() or _sha256(path) != str(expected):
            issues.append(f"frozen_file_drift:{raw_path}")
    return issues


def _scale_from_path(path: Path) -> int:
    for part in path.parts:
        if part.startswith("scale_"):
            try:
                return int(part.split("_", 1)[1])
            except ValueError:
                pass
        if part.startswith("scale") and part[5:].isdigit():
            return int(part[5:])
    return 0


def _validate_freeze() -> None:
    payload = _load(FREEZE)
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_formal_ordering_safety_freeze.v1"
    ):
        raise SystemExit("QG2 formal ordering safety freeze schema mismatch")
    if not bool(payload.get("development_only")) or bool(
        payload.get("production_default")
    ):
        raise SystemExit("QG2 formal ordering safety freeze policy mismatch")
    if str(payload.get("controller_sha256") or "") != _sha256(
        Path(__file__).resolve()
    ):
        raise SystemExit("QG2 formal ordering safety controller drift")
    for issue in _frozen_file_drift(payload):
        raise SystemExit(f"QG2 formal ordering safety {issue}")


def _matching_finalizer_alive(pid: int) -> bool:
    try:
        command = Path(f"/proc/{int(pid)}/cmdline").read_bytes().replace(
            b"\0", b" "
        ).decode("utf-8", errors="replace")
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return "finalize_p0v5_qg2" in command


def _state(status: str, **extra: Any) -> None:
    _write(STATE, {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_formal_ordering_safety_state.v1"
        ),
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": status,
        **extra,
    })


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _nonnegative_int(value: object) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 1


def _nonnegative_float(value: object) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, parsed)


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


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

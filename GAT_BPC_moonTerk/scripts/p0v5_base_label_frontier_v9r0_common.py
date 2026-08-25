#!/usr/bin/env python3
"""Immutable helpers for the base-label frontier observability chain."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/experiments/p0v5_base_label_frontier_observability_v9r0.json"
DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_base_label_frontier_observability_v9r0_20260818"


def load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode()).hexdigest()


def write_once(path: str | Path, payload: Any) -> None:
    target = Path(path)
    encoded = json.dumps(
        payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False
    ) + "\n"
    if target.exists():
        if target.read_text(encoding="utf-8") != encoded:
            raise SystemExit(f"immutable base-label artifact drift:{target}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(encoded, encoding="utf-8")


def write_mutable(path: str | Path, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(
            payload, indent=2, sort_keys=True, ensure_ascii=False,
            allow_nan=False,
        ) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)


def verify_freezes(run_root: Path) -> None:
    registry = load(run_root / "freeze.registry.json")
    for relative, digest in registry["artifact_sha256"].items():
        path = run_root / relative
        if not path.is_file() or sha256(path) != digest:
            raise SystemExit(f"FREEZE_HASH_DRIFT:{relative}")
    source = load(run_root / "source.freeze.json")
    for relative, digest in source["source_sha256"].items():
        path = ROOT / relative
        if not path.is_file() or sha256(path) != digest:
            raise SystemExit(f"FREEZE_HASH_DRIFT:{relative}")
    imported = load(run_root / "evidence_import.freeze.json")
    for root_key, rows in imported["source_artifacts"].items():
        root = Path(imported[root_key])
        for relative, digest in rows.items():
            path = root / relative
            if not path.is_file() or sha256(path) != digest:
                raise SystemExit(f"SOURCE_EVIDENCE_DRIFT:{relative}")


def assert_active(run_root: Path, stage: str) -> dict[str, Any]:
    verify_freezes(run_root)
    state = load(run_root / "state.json")
    if bool(state.get("terminal")):
        raise SystemExit("terminal base-label chain forbids writers")
    if state.get("current_stage") != stage:
        raise SystemExit(f"stage mismatch:{state.get('current_stage')} != {stage}")
    return state


def update_state(run_root: Path, stage: str, status: str, **detail: Any) -> None:
    state = load(run_root / "state.json")
    if bool(state.get("terminal")):
        raise SystemExit("terminal base-label chain forbids transition")
    state.update({"current_stage": stage, "status": status, **detail})
    write_mutable(run_root / "state.json", state)


def write_terminal(
    run_root: Path, *, reason: str, detail: Mapping[str, Any]
) -> None:
    write_once(run_root / "terminal_decision.json", {
        "schema_version": "lunar_ice_bpc.p0v5_base_label_frontier_terminal.v1",
        "decision": "FAIL", "reason": reason, "detail": dict(detail),
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    })
    state = load(run_root / "state.json")
    state.update({
        "current_stage": "TERMINAL", "status": "FAIL", "terminal": True,
        "terminal_reason": reason, "terminal_decision": "terminal_decision.json",
    })
    write_mutable(run_root / "state.json", state)


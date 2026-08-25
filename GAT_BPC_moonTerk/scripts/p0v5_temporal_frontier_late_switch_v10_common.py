#!/usr/bin/env python3
"""Immutable helpers for the V10 temporal-frontier late-switch oracle."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from math import exp, log
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = (
    ROOT / "configs/experiments/"
    "p0v5_temporal_frontier_late_switch_oracle_v10.json"
)
DEFAULT_RUN_ROOT = (
    ROOT / "runs/p0v5_temporal_frontier_late_switch_oracle_v10_20260818"
)

STAGES = (
    "NATIVE_DIFFERENTIAL",
    "PERFORMANCE_FREEZE",
    "LATE_SWITCH_MATRIX",
    "COMPLETE",
    "TERMINAL",
)


def load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")).hexdigest()


def write_once(path: str | Path, payload: Any) -> None:
    target = Path(path)
    encoded = json.dumps(
        payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False,
    ) + "\n"
    if target.exists():
        if target.read_text(encoding="utf-8") != encoded:
            raise SystemExit(f"immutable V10 artifact drift:{target}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(encoded, encoding="utf-8")


def write_mutable(path: str | Path, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True,
                   allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)


def geometric_mean(values: Iterable[float]) -> float:
    rows = tuple(float(value) for value in values)
    if not rows or any(value <= 0.0 for value in rows):
        raise ValueError("geometric mean requires positive values")
    return exp(sum(log(value) for value in rows) / len(rows))


def verify_bootstrap(run_root: Path) -> None:
    registry = load(run_root / "bootstrap.freeze.registry.json")
    for relative, digest in registry["artifact_sha256"].items():
        path = run_root / relative
        if not path.is_file() or sha256(path) != digest:
            raise SystemExit(f"FREEZE_HASH_DRIFT:{relative}")
    source = load(run_root / "source.freeze.json")
    for relative, digest in source["source_sha256"].items():
        path = ROOT / relative
        if not path.is_file() or sha256(path) != digest:
            raise SystemExit(f"FREEZE_HASH_DRIFT:{relative}")
    for key in ("reference_native_binary", "temporal_native_binary"):
        path = Path(source[key])
        if not path.is_file() or sha256(path) != source[f"{key}_sha256"]:
            raise SystemExit(f"FREEZE_HASH_DRIFT:{key}")
    imported = load(run_root / "preaction_source.freeze.json")
    source_root = Path(imported["source_run_root"])
    for relative, digest in imported["source_artifact_sha256"].items():
        path = source_root / relative
        if not path.is_file() or sha256(path) != digest:
            raise SystemExit(f"V10_PREACTION_IMPORT_DRIFT:{relative}")
    for row in imported["selected_rows"]:
        for field in ("instance_path", "source_snapshot_path"):
            path = Path(row[field])
            if not path.is_file() or sha256(path) != row[f"{field}_sha256"]:
                raise SystemExit(
                    f"V10_PREACTION_IMPORT_DRIFT:{field}:{row['context_id']}"
                )


def verify_performance_freeze(run_root: Path) -> None:
    verify_bootstrap(run_root)
    registry = load(run_root / "performance.freeze.registry.json")
    for relative, digest in registry["artifact_sha256"].items():
        path = run_root / relative
        if not path.is_file() or sha256(path) != digest:
            raise SystemExit(f"FREEZE_HASH_DRIFT:{relative}")
    corpus = load(run_root / "pilot_corpus.freeze.json")
    for row in corpus["rows"]:
        path = Path(row["snapshot_path"])
        if not path.is_file() or sha256(path) != row["snapshot_sha256"]:
            raise SystemExit(
                f"V10_REBOUND_SNAPSHOT_DRIFT:{row['context_id']}"
            )


def assert_active(run_root: Path, *stages: str,
                  performance: bool = False) -> dict[str, Any]:
    if performance:
        verify_performance_freeze(run_root)
    else:
        verify_bootstrap(run_root)
    state = load(run_root / "state.json")
    if state.get("terminal"):
        raise SystemExit("terminal V10 chain forbids artifact writers")
    if stages and state.get("current_stage") not in stages:
        raise SystemExit(
            f"V10 stage mismatch:{state.get('current_stage')} not in {stages}"
        )
    return state


def update_state(run_root: Path, stage: str, status: str = "READY",
                 **detail: Any) -> None:
    if stage not in STAGES:
        raise ValueError(stage)
    state = load(run_root / "state.json")
    if state.get("terminal"):
        raise SystemExit("terminal V10 chain forbids state transition")
    state.update({"current_stage": stage, "status": status, **detail})
    write_mutable(run_root / "state.json", state)


def write_terminal(run_root: Path, reason: str, stage: str,
                   detail: Mapping[str, Any] | None = None) -> None:
    payload = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_temporal_frontier_late_switch_terminal.v1"
        ),
        "decision": "FAIL",
        "reason": str(reason),
        "stage": str(stage),
        "detail": dict(detail or {}),
        "candidate_trained": False,
        "manifest_generated": False,
        "diagnostic_only": True,
        "development_only": True,
        "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    write_once(run_root / "terminal_decision.json", payload)
    state = load(run_root / "state.json")
    state.update({
        "current_stage": "TERMINAL",
        "status": "FAIL",
        "terminal": True,
        "terminal_reason": str(reason),
        "terminal_decision": "terminal_decision.json",
    })
    write_mutable(run_root / "state.json", state)


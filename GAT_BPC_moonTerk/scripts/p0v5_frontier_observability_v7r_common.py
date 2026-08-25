#!/usr/bin/env python3
"""Immutable helpers for the V7R frontier-observability root-cause audit."""

from __future__ import annotations

import hashlib
import json
from math import exp, log, sqrt
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/experiments/p0v5_frontier_observability_root_cause_v7r.json"
DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_frontier_observability_root_cause_v7r2_20260818"
V7_ROOT = ROOT / "runs/p0v5_native_frontier_gat_qd1_selector_v7_20260817"

STAGES = (
    "SWITCH_MATRIX",
    "COVERAGE_AUDIT",
    "FEATURE_SUFFICIENCY",
    "COMPLETE",
    "TERMINAL",
)


def load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")).hexdigest()


def write_once(path: str | Path, payload: Any) -> None:
    target = Path(path)
    encoded = json.dumps(
        payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False
    ) + "\n"
    if target.exists():
        if target.read_text(encoding="utf-8") != encoded:
            raise SystemExit(f"immutable V7R artifact drift:{target}")
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


def wilson_interval(successes: int, trials: int, confidence: float = 0.95) -> tuple[float, float]:
    if trials <= 0:
        raise ValueError("Wilson interval requires trials")
    # V7R freezes 95%; retaining the explicit argument prevents silent drift.
    if abs(float(confidence) - 0.95) > 1.0e-12:
        raise ValueError("V7R currently freezes confidence=0.95")
    z = 1.959963984540054
    p = successes / trials
    denominator = 1.0 + z * z / trials
    centre = (p + z * z / (2.0 * trials)) / denominator
    radius = z * sqrt(p * (1.0 - p) / trials + z * z / (4.0 * trials * trials)) / denominator
    return max(0.0, centre - radius), min(1.0, centre + radius)


def binomial_tail_at_least(trials: int, target: int, probability: float) -> float:
    from math import comb

    if target <= 0:
        return 1.0
    if trials < target:
        return 0.0
    return sum(
        comb(trials, k) * probability ** k * (1.0 - probability) ** (trials - k)
        for k in range(target, trials + 1)
    )


def candidate_cap(target: int, probability: float, confidence: float = 0.95,
                  maximum: int = 5000) -> int | None:
    for trials in range(target, maximum + 1):
        if binomial_tail_at_least(trials, target, probability) >= confidence:
            return trials
    return None


def verify_freezes(run_root: Path) -> None:
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
    imported = load(run_root / "v7_preaction_import.freeze.json")
    source_root = Path(imported["source_v7_run_root"])
    for relative, digest in imported["artifact_sha256"].items():
        path = source_root / relative
        if not path.is_file() or sha256(path) != digest:
            raise SystemExit(f"V7R_V7_IMPORT_HASH_DRIFT:{relative}")
    for row in imported["rows"]:
        for field in ("instance_path", "snapshot_path"):
            path = Path(row[field])
            expected = row[field.replace("path", "sha256")]
            if not path.is_file() or sha256(path) != expected:
                raise SystemExit(f"V7R_V7_IMPORT_HASH_DRIFT:{field}:{row['context_id']}")
        original = Path(row["original_snapshot_path"])
        if not original.is_file() or sha256(original) != row["original_snapshot_sha256"]:
            raise SystemExit(f"V7R_V7_IMPORT_HASH_DRIFT:original_snapshot:{row['context_id']}")
    coverage = load(run_root / "coverage_evidence.freeze.json")
    for path_text, digest in coverage["source_artifact_sha256"].items():
        path = Path(path_text)
        if not path.is_file() or sha256(path) != digest:
            raise SystemExit(f"V7R_COVERAGE_EVIDENCE_DRIFT:{path}")


def assert_active(run_root: Path, *stages: str) -> dict[str, Any]:
    verify_freezes(run_root)
    state = load(run_root / "state.json")
    if state.get("terminal"):
        raise SystemExit("terminal V7R chain forbids artifact writers")
    if stages and state.get("current_stage") not in stages:
        raise SystemExit(f"V7R stage mismatch:{state.get('current_stage')} not in {stages}")
    return state


def update_state(run_root: Path, stage: str, status: str = "READY", **detail: Any) -> None:
    if stage not in STAGES:
        raise ValueError(stage)
    state = load(run_root / "state.json")
    if state.get("terminal"):
        raise SystemExit("terminal V7R chain forbids state transition")
    state.update({"current_stage": stage, "status": status, **detail})
    write_mutable(run_root / "state.json", state)


def write_terminal(run_root: Path, reason: str, stage: str,
                   detail: Mapping[str, Any] | None = None,
                   *, decision: str = "FAIL") -> None:
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_observability_terminal.v1",
        "decision": decision,
        "reason": reason,
        "stage": stage,
        "detail": dict(detail or {}),
        "candidate_trained": False,
        "manifest_generated": False,
        "development_only": True,
        "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    write_once(run_root / "terminal_decision.json", payload)
    state = load(run_root / "state.json")
    state.update({
        "current_stage": "COMPLETE" if decision == "PASS" else "TERMINAL",
        "status": decision,
        "terminal": True,
        "terminal_reason": reason,
        "terminal_decision": "terminal_decision.json",
    })
    write_mutable(run_root / "state.json", state)

#!/usr/bin/env python3
"""Immutable evidence and state-machine helpers for Frontier-GAT V7."""

from __future__ import annotations

import hashlib
import json
from math import exp, log
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
CONFIG = ROOT / "configs/experiments/p0v5_native_frontier_gat_qd1_selector_v7.json"
DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_native_frontier_gat_qd1_selector_v7_20260817"
V6_ROOT = ROOT / "runs/p0v5_minimal_interaction_gat_qd1_selector_v6_20260817"

STAGE_ORDER = (
    "BOOTSTRAP_ENGINE",
    "PROBE_DIAGNOSTIC",
    "PILOT_CENSUS",
    "PILOT_MATRIX",
    "MAIN_CENSUS",
    "MAIN_MATRIX",
    "TRAINING",
    "CALIBRATION",
    "HELDOUT",
    "DEVELOPMENT_E2E",
    "FORMAL_FULL100",
    "COMPLETE",
    "TERMINAL",
)


def load(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256(path: Path | str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")).hexdigest()


def write_once(path: Path | str, payload: Any) -> None:
    target = Path(path)
    encoded = json.dumps(
        payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False
    ) + "\n"
    if target.exists():
        if target.read_text(encoding="utf-8") != encoded:
            raise SystemExit(f"immutable V7 artifact drift:{target}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(encoded, encoding="utf-8")


def write_mutable(path: Path | str, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)


def geometric_mean(values: Iterable[float]) -> float:
    rows = tuple(float(value) for value in values)
    if not rows or any(value <= 0.0 for value in rows):
        raise ValueError("geometric mean requires positive values")
    return exp(sum(log(value) for value in rows) / len(rows))


def verify_v6_terminal(config: dict[str, Any]) -> dict[str, Any]:
    root = (ROOT / str(config["v6_run_root"])).resolve()
    terminal_path = root / "terminal_decision.json"
    state_path = root / "state.json"
    if not terminal_path.is_file() or not state_path.is_file():
        raise SystemExit("V7_V6_TERMINAL_IMPORT_DRIFT:missing")
    terminal = load(terminal_path)
    state = load(state_path)
    if (
        terminal.get("decision") != "FAIL"
        or terminal.get("reason") != config["v6_terminal_reason"]
        or bool(terminal.get("deployment_authorized"))
        or bool(terminal.get("production_switch_authorized"))
        or not bool(state.get("terminal"))
    ):
        raise SystemExit("V7_V6_TERMINAL_IMPORT_DRIFT:contract")
    return {
        "run_root": str(root),
        "terminal": terminal,
        "terminal_sha256": sha256(terminal_path),
        "state_sha256": sha256(state_path),
        "closeout_sha256": sha256(
            ROOT / "plan/GAT/P0V5_MINIMAL_INTERACTION_GAT_QD1_SELECTOR_V6_CLOSEOUT_20260817_ZH.md"
        ),
        "all_outcomes_diagnostic_only": True,
        "training_rows_imported": 0,
        "calibration_rows_imported": 0,
        "heldout_rows_imported": 0,
    }


def verify_freezes(run_root: Path) -> None:
    registry = load(run_root / "bootstrap.freeze.registry.json")
    for relative, digest in registry["artifact_sha256"].items():
        path = run_root / relative
        if not path.is_file() or sha256(path) != str(digest):
            raise SystemExit(f"FREEZE_HASH_DRIFT:{relative}")
    source = load(run_root / "source.freeze.json")
    for relative, digest in source["source_sha256"].items():
        path = ROOT / relative
        if not path.is_file() or sha256(path) != str(digest):
            raise SystemExit(f"FREEZE_HASH_DRIFT:{relative}")
    v6 = load(run_root / "v6_diagnostic_import.freeze.json")
    for relative, digest in v6["artifact_sha256"].items():
        path = Path(v6["v6_run_root"]) / relative
        if not path.is_file() or sha256(path) != str(digest):
            raise SystemExit(f"V7_V6_TERMINAL_IMPORT_DRIFT:{relative}")


def assert_active(run_root: Path, *allowed_stages: str) -> dict[str, Any]:
    verify_freezes(run_root)
    state = load(run_root / "state.json")
    if bool(state.get("terminal")):
        raise SystemExit("terminal V7 chain forbids artifact writers")
    if allowed_stages and state.get("current_stage") not in allowed_stages:
        raise SystemExit(
            f"V7 stage mismatch:{state.get('current_stage')} not in {allowed_stages}"
        )
    return state


def update_state(run_root: Path, stage: str, status: str, **detail: Any) -> None:
    if stage not in STAGE_ORDER:
        raise ValueError(f"unknown V7 stage {stage}")
    state = load(run_root / "state.json")
    if bool(state.get("terminal")):
        raise SystemExit("terminal V7 chain forbids state transition")
    state.update({"current_stage": stage, "status": status, **detail})
    write_mutable(run_root / "state.json", state)


def write_terminal(
    run_root: Path,
    *,
    reason: str,
    stage: str,
    detail: Mapping[str, Any] | None = None,
) -> None:
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_native_frontier_gat_terminal.v7",
        "decision": "FAIL",
        "reason": str(reason),
        "failed_stage": str(stage),
        "detail": dict(detail or {}),
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
        "terminal_decision": "terminal_decision.json",
        "terminal_reason": str(reason),
    })
    write_mutable(run_root / "state.json", state)


def deterministic_seed(cohort: str, scale: int, index: int) -> int:
    digest = hashlib.sha256(
        f"p0v5-v7-{cohort}:{int(scale)}:{int(index)}".encode()
    ).digest()
    return int.from_bytes(digest[:4], "big") & 0x7FFF_FFFF


def collapse_matched_blocks(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse pre-matched QPF0/QPD1 rows with the frozen 2-of-3 rule."""

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for raw in rows:
        row = dict(raw)
        grouped.setdefault((str(row["context_id"]), str(row["block_id"])), []).append(row)
    by_context: dict[str, list[dict[str, Any]]] = {}
    for (context_id, block_id), block in grouped.items():
        by_arm = {str(row["arm"]): row for row in block}
        if set(by_arm) != {"QPF0", "QPD1"}:
            continue
        q0, arm = by_arm["QPF0"], by_arm["QPD1"]
        q0_complete = str(q0["status"]) == "COMPLETE"
        arm_complete = str(arm["status"]) == "COMPLETE"
        cap = float(arm["cap_seconds"])
        ratio = None
        adverse = False
        resource_positive = False
        if q0_complete and arm_complete:
            ratio = float(arm["wall_seconds"]) / float(q0["wall_seconds"])
        elif q0_complete and not arm_complete:
            ratio = cap / float(q0["wall_seconds"])
            adverse = resource_positive = True
        elif not q0_complete and arm_complete:
            ratio = float(arm["wall_seconds"]) / cap
        by_context.setdefault(context_id, []).append({
            "block_id": block_id,
            "ratio": ratio,
            "adverse": adverse,
            "resource_censor_positive": resource_positive,
            "correctness_redlines": sorted(set(
                q0.get("correctness_redlines", ())
            ) | set(arm.get("correctness_redlines", ()))),
            "metadata": dict(arm.get("metadata") or q0.get("metadata") or {}),
        })
    collapsed = []
    from statistics import median

    for context_id, blocks in sorted(by_context.items()):
        comparable = [row for row in blocks if row["ratio"] is not None]
        redlines = sorted({value for row in blocks for value in row["correctness_redlines"]})
        determined = len(comparable) >= 2
        ratio = median(row["ratio"] for row in comparable) if determined else None
        metadata = dict(blocks[0].get("metadata") or {})
        collapsed.append({
            "schema_version": "lunar_ice_bpc.p0v5_frontier_probe_matched_outcome.v1",
            "context_id": context_id,
            **metadata,
            "comparable_block_count": len(comparable),
            "determined": determined,
            "ratio": ratio,
            "benefit": bool(determined and ratio <= 0.98),
            "positive_gain": max(0.0, 1.0 - ratio) if determined else None,
            "adverse": bool(any(row["adverse"] for row in blocks) or (
                determined and ratio >= 1.05
            )),
            "resource_censor_positive": any(
                row["resource_censor_positive"] for row in blocks
            ),
            "correctness_redlines": redlines,
        })
    return collapsed

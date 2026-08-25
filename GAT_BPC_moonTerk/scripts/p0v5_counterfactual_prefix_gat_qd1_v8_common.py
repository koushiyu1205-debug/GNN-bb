#!/usr/bin/env python3
"""Immutable evidence and state-machine helpers for V8."""

from __future__ import annotations

import hashlib
import json
from math import exp, log
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
CONFIG = ROOT / "configs/experiments/p0v5_counterfactual_prefix_gat_qd1_selector_v8.json"
DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_counterfactual_prefix_gat_qd1_selector_v8_20260818"
V7R3_ROOT = ROOT / "runs/p0v5_frontier_observability_root_cause_v7r3_20260818"

STAGE_ORDER = (
    "BOOTSTRAP",
    "REPRESENTATION_PREFIX",
    "REPRESENTATION_TRAIN",
    "PILOT_CENSUS",
    "PILOT",
    "MAIN_CENSUS",
    "FRESH_TRAIN",
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
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")).hexdigest()


def write_once(path: Path | str, payload: Any) -> None:
    target = Path(path)
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"
    if target.exists():
        if target.read_text(encoding="utf-8") != encoded:
            raise SystemExit(f"immutable V8 artifact drift:{target}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(encoded, encoding="utf-8")


def write_mutable(path: Path | str, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        ) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)


def geometric_mean(values: Iterable[float]) -> float:
    rows = tuple(float(value) for value in values)
    if not rows or any(value <= 0.0 for value in rows):
        raise ValueError("geometric mean requires positive values")
    return exp(sum(log(value) for value in rows) / len(rows))


def verify_v7r3_import() -> dict[str, Any]:
    required = (
        "terminal_decision.json",
        "bootstrap.freeze.registry.json",
        "source.freeze.json",
        "v7_preaction_import.freeze.json",
        "v7r2_switch_evidence_import.freeze.json",
        "switch_matrix.collapsed.json",
        "switch_oracle.decision.json",
        "feature_sufficiency.report.json",
    )
    if any(not (V7R3_ROOT / name).is_file() for name in required):
        raise SystemExit("V8_V7R3_IMPORT_DRIFT:missing")
    terminal = load(V7R3_ROOT / "terminal_decision.json")
    preaction = load(V7R3_ROOT / "v7_preaction_import.freeze.json")
    switch = load(V7R3_ROOT / "v7r2_switch_evidence_import.freeze.json")
    collapsed = load(V7R3_ROOT / "switch_matrix.collapsed.json")
    if (
        terminal.get("decision") != "FAIL"
        or terminal.get("reason") != "SCALE50_BENEFIT_HARM_NOT_SEPARABLE"
        or len(preaction.get("rows") or ()) != 38
        or int(switch.get("raw_matched_task_count") or -1) != 228
        or int(switch.get("collapsed_context_count") or -1) != 38
        or len(collapsed.get("rows") or ()) != 38
        or bool(terminal.get("deployment_authorized"))
        or bool(terminal.get("production_switch_authorized"))
    ):
        raise SystemExit("V8_V7R3_IMPORT_DRIFT:contract")
    return {
        "schema_version": "lunar_ice_bpc.p0v5_v7r3_representation_import.v8",
        "source_run_root": str(V7R3_ROOT.resolve()),
        "source_remains_read_only": True,
        "source_terminal_reason": terminal["reason"],
        "contexts": 38,
        "raw_matched_tasks": 228,
        "collapsed_labels": 38,
        "performance_authority": False,
        "formal_authority": False,
        "artifact_sha256": {
            name: sha256(V7R3_ROOT / name) for name in required
        },
        "rows": preaction["rows"],
    }


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
    imported = load(run_root / "v7r3_representation_import.freeze.json")
    for relative, digest in imported["artifact_sha256"].items():
        path = V7R3_ROOT / relative
        if not path.is_file() or sha256(path) != digest:
            raise SystemExit(f"V8_V7R3_IMPORT_DRIFT:{relative}")
    repair_path = run_root / "v8_measurement_repair.freeze.json"
    if repair_path.is_file():
        repair = load(repair_path)
        source_root = Path(str(repair["source_run_root"]))
        for name, key in (
            ("terminal_decision.json", "source_terminal_sha256"),
            ("representation_development.report.json", "source_report_sha256"),
        ):
            path = source_root / name
            if not path.is_file() or sha256(path) != str(repair[key]):
                raise SystemExit(f"V8_REPAIR_SOURCE_DRIFT:{name}")


def assert_active(run_root: Path, *allowed_stages: str) -> dict[str, Any]:
    verify_freezes(run_root)
    state = load(run_root / "state.json")
    if bool(state.get("terminal")):
        raise SystemExit("terminal V8 chain forbids artifact writers")
    if allowed_stages and state.get("current_stage") not in allowed_stages:
        raise SystemExit(
            f"V8 stage mismatch:{state.get('current_stage')} not in {allowed_stages}"
        )
    return state


def update_state(run_root: Path, stage: str, status: str, **detail: Any) -> None:
    if stage not in STAGE_ORDER:
        raise ValueError(f"unknown V8 stage {stage}")
    state = load(run_root / "state.json")
    if bool(state.get("terminal")):
        raise SystemExit("terminal V8 chain forbids state transition")
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
        "schema_version": "lunar_ice_bpc.p0v5_counterfactual_prefix_terminal.v8",
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
        "terminal_reason": str(reason),
        "terminal_decision": "terminal_decision.json",
    })
    write_mutable(run_root / "state.json", state)


def deterministic_seed(cohort: str, scale: int, index: int) -> int:
    digest = hashlib.sha256(
        f"p0v5-v8-{cohort}:{int(scale)}:{int(index)}".encode()
    ).digest()
    return int.from_bytes(digest[:4], "big") & 0x7FFF_FFFF

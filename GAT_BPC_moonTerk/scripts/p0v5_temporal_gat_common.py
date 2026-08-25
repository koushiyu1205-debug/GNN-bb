"""Shared immutable state transitions for the Temporal-GAT experiment."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def load(path: str | Path) -> dict[str, Any]:
    return dict(json.loads(Path(path).read_text(encoding="utf-8")))


def load_frozen_config(
    candidate_path: str | Path, *, run_root: str | Path,
) -> tuple[dict[str, Any], Path]:
    """Load a config only when it matches the immutable run config."""
    candidate = load(candidate_path)
    frozen_path = Path(run_root).resolve() / "config.freeze.json"
    ensure_not_terminal(run_root)
    if not frozen_path.is_file():
        raise RuntimeError(f"Temporal-GAT config freeze is missing:{frozen_path}")
    frozen = load(frozen_path)
    if candidate != frozen:
        raise RuntimeError("Temporal-GAT experiment config drift after freeze")
    return frozen, frozen_path


def ensure_not_terminal(run_root: str | Path) -> None:
    root = Path(run_root).resolve()
    terminal = root / "terminal_decision.json"
    if terminal.is_file():
        payload = load(terminal)
        raise RuntimeError(
            "Temporal-GAT round is terminal and cannot continue:"
            f"{payload.get('reason') or terminal}"
        )


def write_once(path: str | Path, payload: object) -> None:
    target = Path(path)
    encoded = json.dumps(
        payload, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"
    if target.exists() and target.read_text(encoding="utf-8") != encoded:
        raise RuntimeError(f"immutable Temporal-GAT artifact drift:{target}")
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(encoded, encoding="utf-8")


def atomic_write(path: str | Path, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(
        payload, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n", encoding="utf-8")
    os.replace(temporary, target)


def update_state(
    run_root: str | Path, *, stage: str, status: str,
    detail: dict[str, Any] | None = None,
) -> None:
    """Advance the mutable stage pointer without changing frozen evidence."""
    root = Path(run_root).resolve()
    state_path = root / "state.json"
    if not state_path.is_file():
        raise RuntimeError(f"Temporal-GAT state is missing:{state_path}")
    state = load(state_path)
    if bool(state.get("terminal")):
        raise RuntimeError("terminal Temporal-GAT state cannot advance")
    state.update({"current_stage": str(stage), "status": str(status)})
    if detail:
        state.update(detail)
    atomic_write(state_path, state)


def mark_terminal_negative(
    run_root: str | Path, *, stage: str, reason: str, detail: object,
) -> Path:
    root = Path(run_root).resolve()
    decision = {
        "schema_version": "lunar_ice_bpc.p0v5_temporal_gat_terminal.v1",
        "status": "TERMINATED_NEGATIVE",
        "stage": str(stage), "reason": str(reason), "detail": detail,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    path = root / "terminal_decision.json"
    write_once(path, decision)
    state_path = root / "state.json"
    if state_path.is_file():
        state = load(state_path)
        state.update({
            "current_stage": "TERMINAL", "status": "TERMINATED_NEGATIVE",
            "terminal": True, "terminal_reason": str(reason),
            "terminal_decision": str(path),
            "deployment_authorized": False,
            "production_switch_authorized": False,
        })
        atomic_write(state_path, state)
    return path

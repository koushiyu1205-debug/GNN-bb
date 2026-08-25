"""Shared immutable-source verification for Context Queue Portfolio V1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def verify_portfolio_freezes(run_root: Path, project_root: Path) -> None:
    run_root = Path(run_root).resolve()
    project_root = Path(project_root).resolve()
    registry = _load(run_root / "freeze.registry.json")
    for name, expected in dict(registry["artifact_sha256"]).items():
        _require_hash(run_root / name, expected, name)
    source = _load(run_root / "source.freeze.json")
    for relative, expected in dict(source.get("source_sha256") or {}).items():
        _require_hash(project_root / relative, expected, relative)
    for relative, expected in dict(
        source.get("exact_execution_source_sha256") or {}
    ).items():
        _require_hash(project_root / relative, expected, relative)
    _require_hash(
        Path(source["selected_exact_config"]),
        source["selected_exact_config_sha256"],
        "selected_exact_config",
    )
    _require_hash(
        Path(source["native_binary"]),
        source["native_binary_sha256"],
        "native_binary",
    )
    if source.get("old_native_binary") or source.get("old_native_binary_sha256"):
        if not source.get("old_native_binary") or not source.get(
            "old_native_binary_sha256"
        ):
            raise RuntimeError("FREEZE_HASH_DRIFT:old_native_binary_binding")
        _require_hash(
            Path(str(source["old_native_binary"])),
            str(source["old_native_binary_sha256"]),
            "old_native_binary",
        )
    differential_path = source.get("old_new_native_differential_path")
    differential_hash = source.get("old_new_native_differential_sha256")
    if differential_path or differential_hash:
        if not differential_path or not differential_hash:
            raise RuntimeError("FREEZE_HASH_DRIFT:old_new_native_differential_binding")
        _require_hash(
            Path(str(differential_path)),
            str(differential_hash),
            "old_new_native_differential",
        )


def _require_hash(path: Path, expected: str, label: str) -> None:
    if not path.is_file() or _sha256(path) != str(expected):
        raise RuntimeError(f"FREEZE_HASH_DRIFT:{label}")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

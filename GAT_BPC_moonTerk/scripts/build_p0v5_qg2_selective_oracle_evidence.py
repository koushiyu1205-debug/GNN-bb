#!/usr/bin/env python3
"""Build a hash-bound selective QG2 Oracle-evidence sidecar.

The sidecar authorizes only model loading for calibration/evaluation.  It
does not alter the Oracle summary, lower any activation-risk gate, or grant
deployment authority.  Keeping it separate lets the currently running
bounded Oracle finish under its original execution freeze.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.qg2_oracle_evidence import (  # noqa: E402
    build_selective_training_only_evidence,
)


ORACLE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
GATE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_training_only_gate.v2"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle-summary", required=True)
    parser.add_argument("--authorized-oracle", required=True)
    parser.add_argument("--training-gate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output = _resolve(args.output)
    if output.exists():
        raise SystemExit("selective Oracle evidence refuses overwrite")
    payload = build_evidence_sidecar(
        oracle_path=_resolve(args.oracle_summary),
        authorized_oracle_path=_resolve(args.authorized_oracle),
        gate_path=_resolve(args.training_gate),
    )
    _write(output, payload)
    print(json.dumps({
        "status": "SELECTIVE_ORACLE_EVIDENCE_FROZEN",
        "context_count": payload["context_count"],
        "output": str(output),
    }, sort_keys=True), flush=True)
    return 0


def build_evidence_sidecar(
    *,
    oracle_path: Path,
    authorized_oracle_path: Path,
    gate_path: Path,
) -> dict:
    for path in (oracle_path, authorized_oracle_path, gate_path):
        if not path.is_file():
            raise ValueError(f"selective Oracle evidence input missing: {path}")
    oracle = _load(oracle_path)
    authorized = _load(authorized_oracle_path)
    gate = _load(gate_path)
    errors = []
    if oracle.get("schema_version") != ORACLE_SCHEMA:
        errors.append("oracle_schema_mismatch")
    if authorized.get("schema_version") != ORACLE_SCHEMA:
        errors.append("authorized_oracle_schema_mismatch")
    if gate.get("schema_version") != GATE_SCHEMA:
        errors.append("training_gate_schema_mismatch")
    if str(gate.get("oracle_summary_sha256") or "") != _sha256(oracle_path):
        errors.append("training_gate_oracle_hash_mismatch")
    if _resolve(gate.get("oracle_summary") or "") != oracle_path:
        errors.append("training_gate_oracle_path_mismatch")
    authority = dict(authorized.get("training_only_v2_authority") or {})
    if str(authority.get("gate_report_sha256") or "") != _sha256(gate_path):
        errors.append("authorized_oracle_gate_hash_mismatch")
    if _resolve(authority.get("gate_report") or "") != gate_path:
        errors.append("authorized_oracle_gate_path_mismatch")
    if dict(authorized.get("oracle_gate") or {}) != dict(gate.get("gate") or {}):
        errors.append("authorized_oracle_embedded_gate_mismatch")
    if dict(authorized.get("strict_oracle_gate") or {}) != dict(
        oracle.get("oracle_gate") or {}
    ):
        errors.append("authorized_oracle_strict_gate_provenance_mismatch")
    if not bool(authorized.get("training_permitted")):
        errors.append("authorized_oracle_training_not_permitted")
    if bool(authorized.get("deployable")) or bool(
        gate.get("deployment_authorized")
    ):
        errors.append("selective_evidence_deployment_authority_present")
    if errors:
        raise ValueError(
            "selective Oracle evidence contract failed: " + ",".join(errors)
        )

    evidence = build_selective_training_only_evidence(
        gate,
        source_oracle_sha256=_sha256(oracle_path),
        source_gate_sha256=_sha256(gate_path),
        context_count=len(authorized.get("context_rows") or ()),
    )
    return {
        **evidence,
        "source_oracle_summary": str(oracle_path),
        "source_training_gate": str(gate_path),
        "authorized_oracle": str(authorized_oracle_path),
        "authorized_oracle_sha256": _sha256(authorized_oracle_path),
        "authorized_oracle_role": "exploratory_model_fitting_only",
    }


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
    temporary.replace(path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

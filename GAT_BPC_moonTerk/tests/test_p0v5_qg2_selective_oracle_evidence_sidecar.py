from __future__ import annotations

import hashlib
import json
from pathlib import Path
import runpy

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE = runpy.run_path(
    str(ROOT / "scripts/build_p0v5_qg2_selective_oracle_evidence.py")
)
build_evidence_sidecar = MODULE["build_evidence_sidecar"]
CONTROLLER = runpy.run_path(
    str(
        ROOT
        / "scripts/run_p0v5_qg2_selective_oracle_evidence_after_training.py"
    )
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    oracle_path = tmp_path / "oracle.json"
    gate_path = tmp_path / "gate.json"
    authorized_path = tmp_path / "authorized.json"
    strict_gate = {"passed": False, "reason": "fixed_arm_bootstrap_failed"}
    oracle = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5",
        "oracle_gate": strict_gate,
        "context_rows": [{"state_hash": f"state-{index}"} for index in range(60)],
        "development_only": True,
        "deployable": False,
    }
    _write(oracle_path, oracle)
    scale = {
        "passed": True,
        "determined_context_count": 30,
        "determined_instance_count": 20,
        "gain_5pct_context_count": 10,
        "positive_instance_count": 8,
        "nonpositive_context_count": 10,
        "harmful_instance_count": 5,
        "paired_geomean_ratio_report_only": 1.04,
        "instance_bootstrap_95_upper_report_only": 1.25,
    }
    gate_row = {
        "passed": True,
        "all_exact_safe": True,
        "contract_errors": [],
        "maximum_instance_saved_wall_fraction": 0.2,
        "scale30": dict(scale),
        "scale50": dict(scale),
    }
    gate = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_training_only_gate.v2",
        "oracle_summary": str(oracle_path),
        "oracle_summary_sha256": _sha256(oracle_path),
        "point_geomean_is_report_only": True,
        "instance_bootstrap_is_report_only": True,
        "deployment_authorized": False,
        "gate": gate_row,
    }
    _write(gate_path, gate)
    authorized = {
        **oracle,
        "strict_oracle_gate": strict_gate,
        "oracle_gate": gate_row,
        "training_permitted": True,
        "deployable": False,
        "training_only_v2_authority": {
            "gate_report": str(gate_path),
            "gate_report_sha256": _sha256(gate_path),
        },
    }
    _write(authorized_path, authorized)
    return oracle_path, authorized_path, gate_path


def test_selective_oracle_sidecar_binds_all_three_sources(tmp_path: Path) -> None:
    oracle, authorized, gate = _inputs(tmp_path)
    payload = build_evidence_sidecar(
        oracle_path=oracle,
        authorized_oracle_path=authorized,
        gate_path=gate,
    )
    assert payload["passed"]
    assert payload["context_count"] == 60
    assert payload["source_oracle_sha256"] == _sha256(oracle)
    assert payload["source_gate_sha256"] == _sha256(gate)
    assert payload["authorized_oracle_sha256"] == _sha256(authorized)
    assert not payload["deployment_authorized"]


def test_selective_oracle_evidence_controller_freeze_is_current() -> None:
    CONTROLLER["_validate_freeze"]()


def test_selective_oracle_sidecar_rejects_authorized_gate_drift(
    tmp_path: Path,
) -> None:
    oracle, authorized, gate = _inputs(tmp_path)
    payload = json.loads(authorized.read_text(encoding="utf-8"))
    payload["oracle_gate"]["scale50"]["harmful_instance_count"] = 0
    _write(authorized, payload)
    with pytest.raises(ValueError, match="embedded_gate_mismatch"):
        build_evidence_sidecar(
            oracle_path=oracle,
            authorized_oracle_path=authorized,
            gate_path=gate,
        )


def test_selective_oracle_sidecar_rejects_deployment_authority(
    tmp_path: Path,
) -> None:
    oracle, authorized, gate = _inputs(tmp_path)
    payload = json.loads(gate.read_text(encoding="utf-8"))
    payload["deployment_authorized"] = True
    _write(gate, payload)
    authorized_payload = json.loads(authorized.read_text(encoding="utf-8"))
    authorized_payload["training_only_v2_authority"][
        "gate_report_sha256"
    ] = _sha256(gate)
    _write(authorized, authorized_payload)
    with pytest.raises(ValueError, match="deployment_authority_present"):
        build_evidence_sidecar(
            oracle_path=oracle,
            authorized_oracle_path=authorized,
            gate_path=gate,
        )

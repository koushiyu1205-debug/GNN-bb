from __future__ import annotations

import hashlib
import json
from pathlib import Path
import runpy

import pytest

from lunar_ice_bpc.guidance.qg2_oracle_evidence import (
    attach_selective_oracle_evidence_to_manifest,
    build_selective_training_only_evidence,
)


ROOT = Path(__file__).resolve().parents[1]
MODULE = runpy.run_path(str(
    ROOT / "scripts/run_p0v5_qg2_selective_runtime_e2e_after_binding.py"
))
validate_authority = MODULE["validate_selective_runtime_e2e_authority"]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _fixture(tmp_path: Path) -> tuple[Path, Path, dict, dict]:
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
    evidence = build_selective_training_only_evidence(
        {
            "point_geomean_is_report_only": True,
            "instance_bootstrap_is_report_only": True,
            "gate": {
                "passed": True,
                "all_exact_safe": True,
                "contract_errors": [],
                "maximum_instance_saved_wall_fraction": 0.20,
                "scale30": dict(scale),
                "scale50": dict(scale),
            },
        },
        source_oracle_sha256="a" * 64,
        source_gate_sha256="b" * 64,
        context_count=60,
    )
    manifest = attach_selective_oracle_evidence_to_manifest(
        {
            "oracle_gate": {
                "passed": True,
                "all_exact_safe": evidence["all_exact_safe"],
                "contract_errors": evidence["contract_errors"],
                "maximum_instance_saved_wall_fraction": (
                    evidence["maximum_instance_saved_wall_fraction"]
                ),
                "scale30": evidence["by_scale"]["30"],
                "scale50": evidence["by_scale"]["50"],
            },
            "deployment_authorized": True,
            "fallback": "P0V4_V5_Q0",
            "can_filter": False,
            "can_prune": False,
            "can_change_bound": False,
            "can_certify": False,
        },
        evidence,
    )
    artifact_payloads = {
        "manifest": manifest,
        "calibration": {"gate_pass": True},
        "risk": {"passed": True},
        "evidence": evidence,
        "selector": {
            "fallback_action": "Q0",
            "all_arms_rejected_action": "Q0",
        },
    }
    paths = {}
    for name, payload in artifact_payloads.items():
        path = tmp_path / f"{name}.json"
        _write(path, payload)
        paths[name] = path
    authority_path = tmp_path / "authority.json"
    authority = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_selective_runtime_e2e_authority.v1"
        ),
        "development_only": True,
        "development_e2e_authorized": True,
        "formal_experiment_authorized": False,
        "production_switch_authorized": False,
        "fallback_action": "Q0",
        "all_arms_rejected_action": "Q0",
        "oracle_evidence_mode": "selective_training_only",
        "ordering_only": True,
        "runtime_manifest": str(paths["manifest"]),
        "runtime_manifest_sha256": _sha256(paths["manifest"]),
        "calibration_report": str(paths["calibration"]),
        "calibration_report_sha256": _sha256(paths["calibration"]),
        "calibration_risk_audit": str(paths["risk"]),
        "calibration_risk_audit_sha256": _sha256(paths["risk"]),
        "selective_oracle_evidence": str(paths["evidence"]),
        "selective_oracle_evidence_sha256": _sha256(paths["evidence"]),
        "context_selector_report": str(paths["selector"]),
        "context_selector_report_sha256": _sha256(paths["selector"]),
    }
    _write(authority_path, authority)
    training_path = tmp_path / "training.json"
    training = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_model_comparison.v3",
        "oracle_gate_passed": True,
        "deployable": False,
    }
    _write(training_path, training)
    return authority_path, training_path, authority, training


def _validate(
    authority_path: Path,
    training_path: Path,
    authority: dict,
    training: dict,
) -> Path:
    return validate_authority(
        authority,
        authority_path=authority_path,
        training=training,
        training_path=training_path,
    )


def test_e2e_authority_accepts_only_development_scope(tmp_path: Path) -> None:
    authority_path, training_path, authority, training = _fixture(tmp_path)
    manifest = _validate(
        authority_path, training_path, authority, training
    )
    assert manifest == tmp_path / "manifest.json"


def test_e2e_authority_rejects_manifest_hash_drift(tmp_path: Path) -> None:
    authority_path, training_path, authority, training = _fixture(tmp_path)
    authority["runtime_manifest_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="runtime_manifest_hash_mismatch"):
        _validate(authority_path, training_path, authority, training)


def test_e2e_authority_rejects_formal_or_production_scope(
    tmp_path: Path,
) -> None:
    authority_path, training_path, authority, training = _fixture(tmp_path)
    authority["formal_experiment_authorized"] = True
    with pytest.raises(ValueError, match="authority_scope_expansion"):
        _validate(authority_path, training_path, authority, training)


def test_e2e_authority_requires_literal_q0(tmp_path: Path) -> None:
    authority_path, training_path, authority, training = _fixture(tmp_path)
    authority["all_arms_rejected_action"] = "QB1"
    with pytest.raises(ValueError, match="literal_q0_fallback"):
        _validate(authority_path, training_path, authority, training)

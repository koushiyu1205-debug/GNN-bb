from __future__ import annotations

import hashlib
import json
from pathlib import Path
import runpy

import pytest

from lunar_ice_bpc.guidance.qg2_oracle_evidence import (
    build_selective_training_only_evidence,
    validate_qg2_manifest_oracle_evidence,
)


ROOT = Path(__file__).resolve().parents[1]
MODULE = runpy.run_path(
    str(ROOT / "scripts/bind_p0v5_qg2_selective_runtime_manifest.py")
)
bind_selective_runtime_manifest = MODULE["bind_selective_runtime_manifest"]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
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
    gate_report = {
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
    }
    evidence = build_selective_training_only_evidence(
        gate_report,
        source_oracle_sha256="a" * 64,
        source_gate_sha256="b" * 64,
        context_count=60,
    )
    manifest_path = tmp_path / "base_manifest.json"
    evidence_path = tmp_path / "evidence.json"
    calibration_path = tmp_path / "calibration.json"
    risk_path = tmp_path / "risk.json"
    checkpoint_path = tmp_path / "checkpoint.pt"
    checkpoint_path.write_bytes(b"frozen-qg2-checkpoint")
    checkpoint_sha256 = _sha256(checkpoint_path)
    thresholds = {
        "probability_threshold": 0.70,
        "expected_gain_threshold": 0.10,
    }
    gat_calibration = {
        "passes_risk_precision_gate": True,
        "harmful_rate_95_upper": 0.01,
        "beneficial_precision_95_lower": 0.90,
    }
    gat_heldout = {"net_geomean_ratio": 0.85}
    manifest = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_manifest.v1",
        "evaluation_authorized": True,
        "deployment_authorized": True,
        "oracle_gate": dict(gate_report["gate"]),
        "calibration": {
            "gate_pass": True,
            **thresholds,
            "harmful_rate_95_upper": 0.01,
            "beneficial_precision_95_lower": 0.90,
            "heldout_tail_ratio": 0.85,
            "gat_vs_best_non_gat_ratio": 0.97,
        },
        "ordering_only": True,
        "can_filter": False,
        "can_prune": False,
        "can_change_bound": False,
        "can_certify": False,
        "fallback": "P0V4_V5_Q0",
        "checkpoint_path": checkpoint_path.name,
        "checkpoint_sha256": checkpoint_sha256,
    }
    _write(manifest_path, manifest)
    _write(evidence_path, evidence)
    calibration = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_fresh_process_calibration.v4"
        ),
        "gate_pass": True,
        "deployment_authorized": True,
        "manifest_path": str(manifest_path),
        "manifest_sha256": _sha256(manifest_path),
        "models": [
            {
                "model_kind": kind,
                "checkpoint_path": str(checkpoint_path),
                "checkpoint_sha256": checkpoint_sha256,
                "thresholds": dict(thresholds),
                "calibration": dict(gat_calibration),
                "heldout": dict(gat_heldout),
            }
            for kind in ("linear", "mlp", "gat")
        ],
        "gat_vs_best_non_gat_ratio": 0.97,
        "gat_inference_p99_ms": 5.0,
    }
    _write(calibration_path, calibration)
    risk = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_calibration_risk_audit.v2"
        ),
        "passed": True,
        "deployment_authorized": True,
        "issues": [],
        "calibration_report": str(calibration_path),
        "calibration_report_sha256": _sha256(calibration_path),
        "risk_policy": {
            "activated_right_censored_is_deployment_veto": True,
            "activated_unsafe_is_deployment_veto": True,
            "unselected_adverse_context_falls_back_to_literal_q0": True,
            "censored_outcome_is_not_relabeled_as_negative_training_data": True,
        },
        "counts": {
            "activated_right_censored_count": 0,
            "activated_unsafe_count": 0,
            "activated_memory_adverse_count": 0,
        },
    }
    _write(risk_path, risk)
    return manifest_path, calibration_path, risk_path, evidence_path


def test_binding_preserves_calibration_authority_and_binds_sources(
    tmp_path: Path,
) -> None:
    manifest, calibration, risk, evidence = _inputs(tmp_path)
    bound = bind_selective_runtime_manifest(
        base_manifest_path=manifest,
        calibration_report_path=calibration,
        risk_audit_path=risk,
        selective_evidence_path=evidence,
    )
    assert bound["deployment_authorized"]
    assert bound["deployment_authority_source"] == (
        "fresh_process_calibration_and_risk_audit_only"
    )
    assert bound["oracle_evidence_authority"] == (
        "model_fitting_and_evaluation_only"
    )
    assert bound["base_manifest_sha256"] == _sha256(manifest)
    assert bound["fresh_process_calibration_report_sha256"] == _sha256(
        calibration
    )
    assert bound["calibration_risk_audit_sha256"] == _sha256(risk)
    assert bound["checkpoint_path"] == str(
        (manifest.parent / "checkpoint.pt").resolve()
    )
    assert bound["selective_oracle_evidence_sha256"] == _sha256(evidence)
    assert validate_qg2_manifest_oracle_evidence(bound) == (
        "selective_training_only"
    )


def test_binding_rejects_failed_calibration(tmp_path: Path) -> None:
    manifest, calibration, risk, evidence = _inputs(tmp_path)
    payload = json.loads(calibration.read_text(encoding="utf-8"))
    payload["gate_pass"] = False
    payload["deployment_authorized"] = False
    _write(calibration, payload)
    with pytest.raises(ValueError, match="calibration_gate_not_passed"):
        bind_selective_runtime_manifest(
            base_manifest_path=manifest,
            calibration_report_path=calibration,
            risk_audit_path=risk,
            selective_evidence_path=evidence,
        )


def test_binding_recomputes_calibration_latency_gate(tmp_path: Path) -> None:
    manifest, calibration, risk, evidence = _inputs(tmp_path)
    payload = json.loads(calibration.read_text(encoding="utf-8"))
    payload["gat_inference_p99_ms"] = 10.01
    _write(calibration, payload)
    risk_payload = json.loads(risk.read_text(encoding="utf-8"))
    risk_payload["calibration_report_sha256"] = _sha256(calibration)
    _write(risk, risk_payload)
    with pytest.raises(ValueError, match="gat_inference_p99_exceeded"):
        bind_selective_runtime_manifest(
            base_manifest_path=manifest,
            calibration_report_path=calibration,
            risk_audit_path=risk,
            selective_evidence_path=evidence,
        )


def test_binding_rejects_calibration_manifest_hash_drift(
    tmp_path: Path,
) -> None:
    manifest, calibration, risk, evidence = _inputs(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["calibration"]["gate_pass"] = False
    _write(manifest, payload)
    with pytest.raises(ValueError, match="calibration_manifest_hash_mismatch"):
        bind_selective_runtime_manifest(
            base_manifest_path=manifest,
            calibration_report_path=calibration,
            risk_audit_path=risk,
            selective_evidence_path=evidence,
        )


def test_binding_rejects_oracle_evidence_deployment_authority(
    tmp_path: Path,
) -> None:
    manifest, calibration, risk, evidence = _inputs(tmp_path)
    payload = json.loads(evidence.read_text(encoding="utf-8"))
    payload["deployment_authorized"] = True
    _write(evidence, payload)
    with pytest.raises(ValueError, match="cannot authorize deployment"):
        bind_selective_runtime_manifest(
            base_manifest_path=manifest,
            calibration_report_path=calibration,
            risk_audit_path=risk,
            selective_evidence_path=evidence,
        )


def test_binding_rejects_checkpoint_hash_drift(tmp_path: Path) -> None:
    manifest, calibration, risk, evidence = _inputs(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["checkpoint_sha256"] = "0" * 64
    _write(manifest, payload)
    calibration_payload = json.loads(calibration.read_text(encoding="utf-8"))
    calibration_payload["manifest_sha256"] = _sha256(manifest)
    _write(calibration, calibration_payload)
    risk_payload = json.loads(risk.read_text(encoding="utf-8"))
    risk_payload["calibration_report_sha256"] = _sha256(calibration)
    _write(risk, risk_payload)
    with pytest.raises(ValueError, match="manifest_checkpoint_hash_mismatch"):
        bind_selective_runtime_manifest(
            base_manifest_path=manifest,
            calibration_report_path=calibration,
            risk_audit_path=risk,
            selective_evidence_path=evidence,
        )


def test_binding_rejects_failed_risk_audit(tmp_path: Path) -> None:
    manifest, calibration, risk, evidence = _inputs(tmp_path)
    payload = json.loads(risk.read_text(encoding="utf-8"))
    payload["passed"] = False
    payload["deployment_authorized"] = False
    payload["issues"] = ["activated_right_censored_context"]
    payload["counts"]["activated_right_censored_count"] = 1
    _write(risk, payload)
    with pytest.raises(ValueError, match="risk_audit_not_passed"):
        bind_selective_runtime_manifest(
            base_manifest_path=manifest,
            calibration_report_path=calibration,
            risk_audit_path=risk,
            selective_evidence_path=evidence,
        )


def test_binding_rejects_risk_audit_calibration_drift(
    tmp_path: Path,
) -> None:
    manifest, calibration, risk, evidence = _inputs(tmp_path)
    payload = json.loads(risk.read_text(encoding="utf-8"))
    payload["calibration_report_sha256"] = "0" * 64
    _write(risk, payload)
    with pytest.raises(ValueError, match="risk_audit_calibration_hash_mismatch"):
        bind_selective_runtime_manifest(
            base_manifest_path=manifest,
            calibration_report_path=calibration,
            risk_audit_path=risk,
            selective_evidence_path=evidence,
        )


@pytest.mark.parametrize(
    ("mutation", "expected"),
    (
        (
            lambda payload: payload["risk_policy"].update({
                "activated_unsafe_is_deployment_veto": False,
            }),
            "risk_policy_missing:activated_unsafe_is_deployment_veto",
        ),
        (
            lambda payload: payload["counts"].update({
                "activated_memory_adverse_count": 1,
            }),
            (
                "risk_audit_adverse_activation:"
                "activated_memory_adverse_count"
            ),
        ),
    ),
)
def test_binding_rejects_incomplete_risk_policy_or_adverse_activation(
    tmp_path: Path,
    mutation,
    expected: str,
) -> None:
    manifest, calibration, risk, evidence = _inputs(tmp_path)
    payload = json.loads(risk.read_text(encoding="utf-8"))
    mutation(payload)
    _write(risk, payload)
    with pytest.raises(ValueError, match=expected):
        bind_selective_runtime_manifest(
            base_manifest_path=manifest,
            calibration_report_path=calibration,
            risk_audit_path=risk,
            selective_evidence_path=evidence,
        )

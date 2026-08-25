from __future__ import annotations

from types import SimpleNamespace

import pytest

from lunar_ice_bpc.guidance.qg2_oracle_evidence import (
    SELECTIVE_TRAINING_ONLY_MODE,
    STRICT_FIXED_ARM_MODE,
    attach_selective_oracle_evidence_to_manifest,
    build_selective_training_only_evidence,
)
from lunar_ice_bpc.guidance.qg2_runtime_oracle_authority import (
    validate_qg2_runtime_oracle_authority,
)
from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (
    QG2_RUNTIME_POLICY_ID,
    _validate_manifest_before_model_load,
    qg2_runtime_implementation_hash,
)


SHA_A = "a" * 64
SHA_B = "b" * 64


def _selective_report() -> dict:
    scale = {
        "passed": True,
        "determined_context_count": 30,
        "determined_instance_count": 20,
        "gain_5pct_context_count": 10,
        "positive_instance_count": 8,
        "nonpositive_context_count": 10,
        "harmful_instance_count": 5,
        "paired_geomean_ratio_report_only": 1.08,
        "instance_bootstrap_95_upper_report_only": 1.31,
    }
    return {
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


def _strict_manifest() -> dict:
    scale = {
        "context_count": 30,
        "determined_context_count": 30,
        "positive_context_count": 24,
        "positive_instance_count": 12,
        "paired_geomean_ratio": 0.82,
        "bootstrap_95_upper": 0.89,
        "positive_fraction": 0.80,
    }
    return {
        "oracle_gate": {
            "passed": True,
            "context_count": 60,
            "net_gain_5pct_context_count": 50,
            "max_instance_saved_wall_fraction": 0.20,
            "scale30": dict(scale),
            "scale50": dict(scale),
        }
    }


def test_runtime_accepts_selective_evidence_with_bad_fixed_arm_ci() -> None:
    report = _selective_report()
    evidence = build_selective_training_only_evidence(
        report,
        source_oracle_sha256=SHA_A,
        source_gate_sha256=SHA_B,
        context_count=120,
    )
    manifest = attach_selective_oracle_evidence_to_manifest(
        {"oracle_gate": dict(report["gate"])}, evidence
    )
    assert validate_qg2_runtime_oracle_authority(manifest) == (
        SELECTIVE_TRAINING_ONLY_MODE
    )


def test_runtime_preserves_legacy_strict_fixed_arm_gate() -> None:
    manifest = _strict_manifest()
    assert validate_qg2_runtime_oracle_authority(manifest) == (
        STRICT_FIXED_ARM_MODE
    )
    manifest["oracle_gate"]["scale50"]["bootstrap_95_upper"] = 0.91
    with pytest.raises(ValueError, match="strict fixed-arm evidence"):
        validate_qg2_runtime_oracle_authority(manifest)


def test_runtime_rejects_unbounded_legacy_oracle() -> None:
    manifest = _strict_manifest()
    manifest["oracle_gate"]["context_count"] = 301
    with pytest.raises(ValueError, match="bounded context budget"):
        validate_qg2_runtime_oracle_authority(manifest)


def _runtime_fields() -> dict:
    return {
        "runtime_policy_id": QG2_RUNTIME_POLICY_ID,
        "runtime_implementation_hash": qg2_runtime_implementation_hash(),
        "feature_schema_version": "lunar_ice_bpc.p0v5_qg2_features.v1",
        "label_state_schema_version": "lunar_spprc.qg2_label_state.v1",
        "guidance_bucket_width": 0.001,
    }


def _bound_request() -> SimpleNamespace:
    return SimpleNamespace(
        instance_hash="instance-hash",
        config_hash="request-config-hash",
        engine_hash="exact-engine-hash",
    )


def test_model_load_validator_accepts_bound_selective_evidence() -> None:
    report = _selective_report()
    evidence = build_selective_training_only_evidence(
        report,
        source_oracle_sha256=SHA_A,
        source_gate_sha256=SHA_B,
        context_count=120,
    )
    manifest = attach_selective_oracle_evidence_to_manifest(
        {**_runtime_fields(), "oracle_gate": dict(report["gate"])},
        evidence,
    )
    _validate_manifest_before_model_load(_bound_request(), manifest)


def test_model_load_validator_preserves_legacy_strict_gate() -> None:
    manifest = {**_runtime_fields(), **_strict_manifest()}
    _validate_manifest_before_model_load(_bound_request(), manifest)


def test_model_load_validator_fails_closed_on_selective_evidence_drift() -> None:
    report = _selective_report()
    evidence = build_selective_training_only_evidence(
        report,
        source_oracle_sha256=SHA_A,
        source_gate_sha256=SHA_B,
        context_count=120,
    )
    manifest = attach_selective_oracle_evidence_to_manifest(
        {**_runtime_fields(), "oracle_gate": dict(report["gate"])},
        evidence,
    )
    manifest["oracle_gate"]["scale50"] = {}
    with pytest.raises(ValueError, match="scale50 Oracle evidence drift"):
        _validate_manifest_before_model_load(_bound_request(), manifest)


def test_model_load_validator_fails_closed_on_runtime_hash_drift() -> None:
    manifest = {**_runtime_fields(), **_strict_manifest()}
    manifest["runtime_implementation_hash"] = "0" * 64
    with pytest.raises(ValueError, match="runtime implementation drift"):
        _validate_manifest_before_model_load(_bound_request(), manifest)

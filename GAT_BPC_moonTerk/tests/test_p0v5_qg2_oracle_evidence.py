from __future__ import annotations

import pytest

from lunar_ice_bpc.guidance.qg2_oracle_evidence import (
    QG2_ORACLE_EVIDENCE_SCHEMA_V1,
    SELECTIVE_TRAINING_ONLY_MODE,
    SELECTIVE_MANIFEST_GATE_ROLE,
    STRICT_FIXED_ARM_MODE,
    attach_selective_oracle_evidence_to_manifest,
    build_selective_training_only_evidence,
    validate_qg2_manifest_oracle_evidence,
    validate_qg2_oracle_evidence,
)


SHA_A = "a" * 64
SHA_B = "b" * 64


def _training_gate() -> dict:
    row = {
        "passed": True,
        "determined_context_count": 24,
        "determined_instance_count": 18,
        "gain_5pct_context_count": 8,
        "positive_instance_count": 7,
        "nonpositive_context_count": 9,
        "harmful_instance_count": 5,
        # Deliberately poor fixed-arm statistics remain diagnostic only.
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
            "scale30": dict(row),
            "scale50": dict(row),
        },
    }


def test_selective_evidence_keeps_bad_fixed_arm_statistics_report_only() -> None:
    payload = build_selective_training_only_evidence(
        _training_gate(),
        source_oracle_sha256=SHA_A,
        source_gate_sha256=SHA_B,
        context_count=120,
    )
    assert validate_qg2_oracle_evidence(payload) == SELECTIVE_TRAINING_ONLY_MODE
    assert not payload["deployment_authorized"]
    assert payload["by_scale"]["50"][
        "instance_bootstrap_95_upper_report_only"
    ] == pytest.approx(1.31)


def test_selective_evidence_requires_harmful_and_noop_support() -> None:
    report = _training_gate()
    report["gate"]["scale50"]["harmful_instance_count"] = 0
    with pytest.raises(ValueError, match="selective data evidence"):
        build_selective_training_only_evidence(
            report,
            source_oracle_sha256=SHA_A,
            source_gate_sha256=SHA_B,
            context_count=120,
        )


def test_selective_evidence_can_never_grant_deployment() -> None:
    payload = build_selective_training_only_evidence(
        _training_gate(),
        source_oracle_sha256=SHA_A,
        source_gate_sha256=SHA_B,
        context_count=120,
    )
    payload["deployment_authorized"] = True
    with pytest.raises(ValueError, match="cannot authorize deployment"):
        validate_qg2_oracle_evidence(payload)


def test_strict_fixed_arm_mode_preserves_original_bootstrap_gate() -> None:
    row = {
        "context_count": 30,
        "determined_context_count": 30,
        "positive_context_count": 24,
        "positive_instance_count": 12,
        "paired_geomean_ratio": 0.82,
        "bootstrap_95_upper": 0.89,
        "positive_fraction": 0.80,
    }
    payload = {
        "schema_version": QG2_ORACLE_EVIDENCE_SCHEMA_V1,
        "mode": STRICT_FIXED_ARM_MODE,
        "scope": "model_fitting_and_evaluation_only",
        "passed": True,
        "deployment_authorized": False,
        "paper_claim_authorized": False,
        "source_oracle_sha256": SHA_A,
        "source_gate_sha256": SHA_B,
        "context_count": 60,
        "all_exact_safe": True,
        "contract_errors": [],
        "maximum_instance_saved_wall_fraction": 0.20,
        "by_scale": {"30": dict(row), "50": dict(row)},
    }
    assert validate_qg2_oracle_evidence(payload) == STRICT_FIXED_ARM_MODE

    payload["by_scale"]["50"]["bootstrap_95_upper"] = 0.91
    with pytest.raises(ValueError, match="strict fixed-arm evidence"):
        validate_qg2_oracle_evidence(payload)


def test_evidence_requires_hash_and_context_budget_bindings() -> None:
    payload = build_selective_training_only_evidence(
        _training_gate(),
        source_oracle_sha256=SHA_A,
        source_gate_sha256=SHA_B,
        context_count=120,
    )
    payload["source_gate_sha256"] = "not-a-hash"
    with pytest.raises(ValueError, match="source binding"):
        validate_qg2_oracle_evidence(payload)

    payload["source_gate_sha256"] = SHA_B
    payload["context_count"] = 301
    with pytest.raises(ValueError, match="bounded context budget"):
        validate_qg2_oracle_evidence(payload)


def test_selective_manifest_binds_embedded_gate_and_source_hashes() -> None:
    report = _training_gate()
    evidence = build_selective_training_only_evidence(
        report,
        source_oracle_sha256=SHA_A,
        source_gate_sha256=SHA_B,
        context_count=120,
    )
    manifest = {
        "source_oracle_summary_sha256": SHA_A,
        "source_training_gate_sha256": SHA_B,
        "oracle_gate_role": SELECTIVE_MANIFEST_GATE_ROLE,
        "oracle_evidence_deployment_authorized": False,
        "oracle_evidence": evidence,
        "oracle_gate": dict(report["gate"]),
    }
    assert validate_qg2_manifest_oracle_evidence(manifest) == (
        SELECTIVE_TRAINING_ONLY_MODE
    )

    manifest["source_training_gate_sha256"] = SHA_A
    with pytest.raises(ValueError, match="training-gate source hash"):
        validate_qg2_manifest_oracle_evidence(manifest)


def test_selective_manifest_rejects_gate_drift_and_deployment_authority() -> None:
    report = _training_gate()
    evidence = build_selective_training_only_evidence(
        report,
        source_oracle_sha256=SHA_A,
        source_gate_sha256=SHA_B,
        context_count=120,
    )
    manifest = {
        "source_oracle_summary_sha256": SHA_A,
        "source_training_gate_sha256": SHA_B,
        "oracle_gate_role": SELECTIVE_MANIFEST_GATE_ROLE,
        "oracle_evidence_deployment_authorized": False,
        "oracle_evidence": evidence,
        "oracle_gate": dict(report["gate"]),
    }
    manifest["oracle_gate"] = {
        **manifest["oracle_gate"],
        "scale50": {
            **manifest["oracle_gate"]["scale50"],
            "harmful_instance_count": 0,
        },
    }
    with pytest.raises(ValueError, match="scale50 Oracle evidence drift"):
        validate_qg2_manifest_oracle_evidence(manifest)

    manifest["oracle_gate"] = dict(report["gate"])
    manifest["oracle_evidence_deployment_authorized"] = True
    with pytest.raises(ValueError, match="cannot authorize deployment"):
        validate_qg2_manifest_oracle_evidence(manifest)


def test_attach_selective_evidence_preserves_calibration_authority_separation(
) -> None:
    report = _training_gate()
    evidence = build_selective_training_only_evidence(
        report,
        source_oracle_sha256=SHA_A,
        source_gate_sha256=SHA_B,
        context_count=120,
    )
    manifest = {
        "oracle_gate": dict(report["gate"]),
        # This flag may become true only after the independent calibration
        # gate; attaching Oracle evidence must neither grant nor revoke it.
        "deployment_authorized": True,
        "calibration": {"gate_pass": True},
    }
    attached = attach_selective_oracle_evidence_to_manifest(
        manifest, evidence
    )
    assert attached["deployment_authorized"] is True
    assert not attached["oracle_evidence_deployment_authorized"]
    assert attached["oracle_gate_role"] == SELECTIVE_MANIFEST_GATE_ROLE
    assert attached["source_oracle_summary_sha256"] == SHA_A
    assert attached["source_training_gate_sha256"] == SHA_B

    drifted = {**manifest, "oracle_gate": {**report["gate"], "scale50": {}}}
    with pytest.raises(ValueError, match="scale50 Oracle evidence drift"):
        attach_selective_oracle_evidence_to_manifest(drifted, evidence)


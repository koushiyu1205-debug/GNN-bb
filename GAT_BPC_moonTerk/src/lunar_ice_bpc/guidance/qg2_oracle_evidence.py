"""Versioned Oracle evidence contract for selective QG2 evaluation.

The original QG2 runtime used the performance of one unconditionally enabled
QO2 arm as both a model-fitting gate and a runtime loading gate.  That is a
valid strict experiment, but it is not the right statistical object for a
selective policy whose activation head may choose literal Q0.  This module
keeps both meanings explicit.  It grants no deployment, bound, pruning, or
certificate authority; those remain separate calibration and exact-solver
contracts.
"""

from __future__ import annotations

from typing import Any, Mapping


QG2_ORACLE_EVIDENCE_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_qg2_runtime_oracle_evidence.v1"
)
STRICT_FIXED_ARM_MODE = "strict_fixed_arm"
SELECTIVE_TRAINING_ONLY_MODE = "selective_training_only"
ALLOWED_MODES = frozenset({STRICT_FIXED_ARM_MODE, SELECTIVE_TRAINING_ONLY_MODE})
SCALES = (30, 50)
MAXIMUM_CONTEXTS = 300
SELECTIVE_MANIFEST_GATE_ROLE = (
    "selective_model_fitting_evidence_only"
)


def build_selective_training_only_evidence(
    gate_report: Mapping[str, Any],
    *,
    source_oracle_sha256: str,
    source_gate_sha256: str,
    context_count: int,
) -> dict[str, Any]:
    """Build model-load evidence without reinterpreting fixed-arm statistics."""

    gate = dict(gate_report.get("gate") or {})
    payload = {
        "schema_version": QG2_ORACLE_EVIDENCE_SCHEMA_V1,
        "mode": SELECTIVE_TRAINING_ONLY_MODE,
        "scope": "model_fitting_and_evaluation_only",
        "passed": bool(gate.get("passed")),
        "deployment_authorized": False,
        "paper_claim_authorized": False,
        "point_geomean_is_report_only": bool(
            gate_report.get("point_geomean_is_report_only")
        ),
        "instance_bootstrap_is_report_only": bool(
            gate_report.get("instance_bootstrap_is_report_only")
        ),
        "source_oracle_sha256": str(source_oracle_sha256),
        "source_gate_sha256": str(source_gate_sha256),
        "context_count": int(context_count),
        "all_exact_safe": bool(gate.get("all_exact_safe")),
        "contract_errors": list(gate.get("contract_errors") or ()),
        "maximum_instance_saved_wall_fraction": float(
            gate.get("maximum_instance_saved_wall_fraction", 1.0)
        ),
        "by_scale": {
            str(scale): dict(gate.get(f"scale{scale}") or {})
            for scale in SCALES
        },
    }
    validate_qg2_oracle_evidence(payload)
    return payload


def validate_qg2_oracle_evidence(payload: Mapping[str, Any]) -> str:
    """Return the evidence mode or raise on any incomplete/unsafe contract."""

    if payload.get("schema_version") != QG2_ORACLE_EVIDENCE_SCHEMA_V1:
        raise ValueError("QG2 Oracle evidence schema mismatch")
    mode = str(payload.get("mode") or "")
    if mode not in ALLOWED_MODES:
        raise ValueError("QG2 Oracle evidence mode mismatch")
    if not bool(payload.get("passed")):
        raise ValueError("QG2 Oracle evidence has not passed")
    if bool(payload.get("deployment_authorized")) or bool(
        payload.get("paper_claim_authorized")
    ):
        raise ValueError("QG2 Oracle evidence cannot authorize deployment")
    if not _sha256_like(payload.get("source_oracle_sha256")) or not _sha256_like(
        payload.get("source_gate_sha256")
    ):
        raise ValueError("QG2 Oracle evidence source binding is incomplete")
    context_count = int(payload.get("context_count") or 0)
    if context_count <= 0 or context_count > MAXIMUM_CONTEXTS:
        raise ValueError("QG2 Oracle evidence exceeded bounded context budget")
    if not bool(payload.get("all_exact_safe")):
        raise ValueError("QG2 Oracle evidence is not exact-safe")
    if list(payload.get("contract_errors") or ()):
        raise ValueError("QG2 Oracle evidence contract errors are nonempty")
    if float(payload.get("maximum_instance_saved_wall_fraction", 1.0)) > 0.35:
        raise ValueError("QG2 Oracle evidence is dominated by one instance")
    by_scale = dict(payload.get("by_scale") or {})
    for scale in SCALES:
        row = dict(by_scale.get(str(scale)) or {})
        if mode == STRICT_FIXED_ARM_MODE:
            _validate_strict_scale(scale, row)
        else:
            _validate_selective_scale(scale, row)
    if mode == SELECTIVE_TRAINING_ONLY_MODE:
        if not bool(payload.get("point_geomean_is_report_only")) or not bool(
            payload.get("instance_bootstrap_is_report_only")
        ):
            raise ValueError("QG2 selective evidence statistical role mismatch")
        if str(payload.get("scope") or "") != "model_fitting_and_evaluation_only":
            raise ValueError("QG2 selective evidence scope mismatch")
    return mode


def validate_qg2_manifest_oracle_evidence(
    manifest: Mapping[str, Any],
) -> str:
    """Validate the binding between a runtime manifest and Oracle evidence.

    This is intentionally separate from activation calibration.  Passing it
    means only that model fitting/evaluation was based on bounded, exact-safe
    evidence with both beneficial and harmful/no-op support.  It cannot make
    ``deployment_authorized`` true or replace heldout/E2E risk gates.
    """

    evidence = dict(manifest.get("oracle_evidence") or {})
    if not evidence:
        raise ValueError("QG2 manifest Oracle evidence is missing")
    mode = validate_qg2_oracle_evidence(evidence)
    source_oracle = str(
        manifest.get("source_oracle_summary_sha256") or ""
    )
    source_gate = str(
        manifest.get("source_training_gate_sha256") or ""
    )
    if source_oracle != str(evidence["source_oracle_sha256"]):
        raise ValueError("QG2 manifest Oracle source hash mismatch")
    if source_gate != str(evidence["source_gate_sha256"]):
        raise ValueError("QG2 manifest training-gate source hash mismatch")

    embedded = dict(manifest.get("oracle_gate") or {})
    if not bool(embedded.get("passed")):
        raise ValueError("QG2 manifest embedded Oracle gate has not passed")
    for scale in SCALES:
        if dict(embedded.get(f"scale{scale}") or {}) != dict(
            evidence["by_scale"][str(scale)]
        ):
            raise ValueError(
                f"QG2 manifest scale{scale} Oracle evidence drift"
            )
    if bool(embedded.get("all_exact_safe")) != bool(
        evidence.get("all_exact_safe")
    ):
        raise ValueError("QG2 manifest exact-safety evidence drift")
    if list(embedded.get("contract_errors") or ()) != list(
        evidence.get("contract_errors") or ()
    ):
        raise ValueError("QG2 manifest Oracle contract evidence drift")
    if abs(
        float(embedded.get("maximum_instance_saved_wall_fraction", 1.0))
        - float(evidence.get("maximum_instance_saved_wall_fraction", 1.0))
    ) > 1.0e-12:
        raise ValueError("QG2 manifest savings-concentration evidence drift")

    if mode == SELECTIVE_TRAINING_ONLY_MODE:
        if str(manifest.get("oracle_gate_role") or "") != (
            SELECTIVE_MANIFEST_GATE_ROLE
        ):
            raise ValueError("QG2 selective manifest gate role mismatch")
        if bool(manifest.get("oracle_evidence_deployment_authorized")):
            raise ValueError(
                "QG2 selective Oracle evidence cannot authorize deployment"
            )
    return mode


def attach_selective_oracle_evidence_to_manifest(
    manifest: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a manifest copy with a fully bound selective evidence block."""

    evidence_payload = dict(evidence)
    mode = validate_qg2_oracle_evidence(evidence_payload)
    if mode != SELECTIVE_TRAINING_ONLY_MODE:
        raise ValueError("QG2 manifest requires selective training-only evidence")
    result = dict(manifest)
    result.update({
        "source_oracle_summary_sha256": str(
            evidence_payload["source_oracle_sha256"]
        ),
        "source_training_gate_sha256": str(
            evidence_payload["source_gate_sha256"]
        ),
        "oracle_gate_role": SELECTIVE_MANIFEST_GATE_ROLE,
        "oracle_evidence_deployment_authorized": False,
        "oracle_evidence": evidence_payload,
    })
    validate_qg2_manifest_oracle_evidence(result)
    return result


def _validate_strict_scale(scale: int, row: Mapping[str, Any]) -> None:
    if not bool(
        int(row.get("context_count") or 0) >= 20
        and int(row.get("determined_context_count") or 0) >= 20
        and int(row.get("positive_context_count") or 0) >= 20
        and int(row.get("positive_instance_count") or 0) >= 5
        and float(row.get("paired_geomean_ratio", 1.0)) <= 0.85
        and float(row.get("bootstrap_95_upper", 1.0)) <= 0.90
        and float(row.get("positive_fraction", 0.0)) > 0.20
    ):
        raise ValueError(f"QG2 scale{scale} strict fixed-arm evidence mismatch")


def _validate_selective_scale(scale: int, row: Mapping[str, Any]) -> None:
    if not bool(
        row.get("passed")
        and int(row.get("determined_context_count") or 0) >= 20
        and int(row.get("determined_instance_count") or 0) >= 10
        and int(row.get("gain_5pct_context_count") or 0) >= 5
        and int(row.get("positive_instance_count") or 0) >= 5
        and int(row.get("nonpositive_context_count") or 0) >= 5
        and int(row.get("harmful_instance_count") or 0) >= 3
    ):
        raise ValueError(f"QG2 scale{scale} selective data evidence mismatch")


def _sha256_like(value: Any) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(character in "0123456789abcdef" for character in text)

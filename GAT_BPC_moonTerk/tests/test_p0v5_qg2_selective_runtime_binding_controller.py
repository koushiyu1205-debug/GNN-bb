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
from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (
    QG2_RUNTIME_POLICY_ID,
    qg2_runtime_implementation_hash,
)


ROOT = Path(__file__).resolve().parents[1]
MODULE = runpy.run_path(str(
    ROOT
    / "scripts/run_p0v5_qg2_selective_runtime_binding_after_calibration.py"
))
build_authority = MODULE["build_selective_runtime_e2e_authority"]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _inputs(tmp_path: Path) -> dict[str, Path]:
    paths = {
        name: tmp_path / f"{name}.json"
        for name in (
            "calibration_state",
            "calibration",
            "risk",
            "evidence_state",
            "evidence",
            "selector",
            "manifest",
        )
    }
    checkpoint = tmp_path / "qg2_gat.pt"
    checkpoint.write_bytes(b"bound-gat-checkpoint")
    checkpoint_sha256 = _sha256(checkpoint)
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
    _write(paths["calibration"], {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_fresh_process_calibration.v4"
        ),
        "gate_pass": True,
        "deployment_authorized": True,
        "models": [
            {
                "model_kind": kind,
                "checkpoint_path": str(checkpoint),
                "checkpoint_sha256": checkpoint_sha256,
                "thresholds": dict(thresholds),
                "calibration": dict(gat_calibration),
                "heldout": dict(gat_heldout),
            }
            for kind in ("linear", "mlp", "gat")
        ],
        "gat_vs_best_non_gat_ratio": 0.97,
        "gat_inference_p99_ms": 5.0,
    })
    _write(paths["risk"], {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_calibration_risk_audit.v2"
        ),
        "passed": True,
        "deployment_authorized": True,
        "calibration_report_sha256": _sha256(paths["calibration"]),
    })
    _write(paths["calibration_state"], {
        "status": "CALIBRATION_AND_RISK_AUDIT_PASSED_PENDING_E2E",
        "calibration_report_sha256": _sha256(paths["calibration"]),
        "risk_audit_sha256": _sha256(paths["risk"]),
    })
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
    report = {
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
        report,
        source_oracle_sha256="a" * 64,
        source_gate_sha256="b" * 64,
        context_count=60,
    )
    _write(paths["evidence"], evidence)
    _write(paths["evidence_state"], {
        "status": "SELECTIVE_ORACLE_EVIDENCE_FROZEN",
        "evidence_sha256": _sha256(paths["evidence"]),
    })
    _write(paths["selector"], {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_context_arm_selector_feasibility.v1"
        ),
        "continued_development_recommended": False,
        "deployable": False,
        "fallback_action": "Q0",
        "all_arms_rejected_action": "Q0",
    })
    embedded_gate = {
        "passed": True,
        "all_exact_safe": bool(evidence["all_exact_safe"]),
        "contract_errors": list(evidence["contract_errors"]),
        "maximum_instance_saved_wall_fraction": float(
            evidence["maximum_instance_saved_wall_fraction"]
        ),
        "scale30": dict(evidence["by_scale"]["30"]),
        "scale50": dict(evidence["by_scale"]["50"]),
    }
    manifest = attach_selective_oracle_evidence_to_manifest(
        {
            "schema_version": "lunar_ice_bpc.p0v5_qg2_manifest.v1",
            "runtime_policy_id": QG2_RUNTIME_POLICY_ID,
            "runtime_implementation_hash": qg2_runtime_implementation_hash(),
            "feature_schema_version": "lunar_ice_bpc.p0v5_qg2_features.v1",
            "label_state_schema_version": "lunar_spprc.qg2_label_state.v1",
            "allowed_scales": [30, 50],
            "allowed_exact_engine_hashes": ["engine"],
            "allowed_exact_action_policy_hashes": ["policy"],
            "checkpoint_path": str(checkpoint),
            "checkpoint_sha256": checkpoint_sha256,
            "evaluation_authorized": True,
            "deployment_authorized": True,
            "calibration": {
                "gate_pass": True,
                **thresholds,
                "harmful_rate_95_upper": 0.01,
                "beneficial_precision_95_lower": 0.90,
                "heldout_tail_ratio": 0.85,
                "gat_vs_best_non_gat_ratio": 0.97,
            },
            "oracle_gate": embedded_gate,
            "fallback": "P0V4_V5_Q0",
            "can_filter": False,
            "can_prune": False,
            "can_change_bound": False,
            "can_certify": False,
            "fresh_process_calibration_report_sha256": _sha256(
                paths["calibration"]
            ),
            "calibration_risk_audit_sha256": _sha256(paths["risk"]),
            "selective_oracle_evidence_sha256": _sha256(paths["evidence"]),
        },
        evidence,
    )
    _write(paths["manifest"], manifest)
    return paths


def _build(paths: dict[str, Path]) -> dict:
    return build_authority(
        calibration_state_path=paths["calibration_state"],
        calibration_report_path=paths["calibration"],
        risk_audit_path=paths["risk"],
        selective_evidence_state_path=paths["evidence_state"],
        selective_evidence_path=paths["evidence"],
        selector_report_path=paths["selector"],
        bound_manifest_path=paths["manifest"],
    )


def test_authority_binds_all_sources_and_keeps_production_disabled(
    tmp_path: Path,
) -> None:
    paths = _inputs(tmp_path)
    authority = _build(paths)
    assert authority["development_e2e_authorized"]
    assert not authority["formal_experiment_authorized"]
    assert not authority["production_switch_authorized"]
    assert authority["fallback_action"] == "Q0"
    assert authority["all_arms_rejected_action"] == "Q0"
    assert authority["runtime_manifest_sha256"] == _sha256(paths["manifest"])
    assert authority["calibration_risk_audit_sha256"] == _sha256(paths["risk"])


def test_authority_rejects_calibration_state_risk_hash_drift(
    tmp_path: Path,
) -> None:
    paths = _inputs(tmp_path)
    payload = json.loads(paths["calibration_state"].read_text())
    payload["risk_audit_sha256"] = "0" * 64
    _write(paths["calibration_state"], payload)
    with pytest.raises(ValueError, match="calibration_controller_risk_hash"):
        _build(paths)


def test_authority_stops_when_combined_selector_is_required(
    tmp_path: Path,
) -> None:
    paths = _inputs(tmp_path)
    payload = json.loads(paths["selector"].read_text())
    payload["continued_development_recommended"] = True
    _write(paths["selector"], payload)
    with pytest.raises(ValueError, match="combined_selector_implementation"):
        _build(paths)


def test_authority_requires_literal_q0_fallback(tmp_path: Path) -> None:
    paths = _inputs(tmp_path)
    payload = json.loads(paths["selector"].read_text())
    payload["all_arms_rejected_action"] = "QB1"
    _write(paths["selector"], payload)
    with pytest.raises(ValueError, match="literal_q0_fallback"):
        _build(paths)


def test_authority_rejects_runtime_or_checkpoint_drift(tmp_path: Path) -> None:
    paths = _inputs(tmp_path)
    payload = json.loads(paths["manifest"].read_text())
    payload["runtime_implementation_hash"] = "0" * 64
    payload["checkpoint_sha256"] = "1" * 64
    _write(paths["manifest"], payload)
    with pytest.raises(ValueError, match="runtime_implementation_drift"):
        _build(paths)

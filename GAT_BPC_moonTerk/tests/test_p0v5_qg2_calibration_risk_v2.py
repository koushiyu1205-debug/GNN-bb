from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _module():
    path = ROOT / "scripts/audit_p0v5_qg2_calibration_risk_v2.py"
    spec = importlib.util.spec_from_file_location("qg2_risk_v2_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDIT = _module()


def _payload(tmp_path: Path) -> tuple[dict, Path]:
    manifest = {
        "schema_version": AUDIT.MANIFEST_SCHEMA,
        "ordering_only": True,
        "can_filter": False,
        "can_prune": False,
        "can_change_bound": False,
        "can_certify": False,
        "fallback": "P0V4_V5_Q0",
        "deployment_authorized": True,
        "calibration": {
            "gate_pass": True,
            "probability_threshold": 0.8,
            "expected_gain_threshold": 2.0,
        },
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    report_path = tmp_path / "calibration.json"
    report = {
        "schema_version": AUDIT.CALIBRATION_SCHEMA,
        "development_only": True,
        "gate_pass": True,
        "deployment_authorized": True,
        "deployable": True,
        "models": [{
            "model_kind": "gat",
            "thresholds": {
                "probability_threshold": 0.8,
                "expected_gain_threshold": 2.0,
            },
        }],
        "records": [{
            "model_kind": "gat",
            "partition": "calibration",
            "state_hash": "beneficial",
            "action_eligible": True,
            "benefit_probability": 0.9,
            "expected_gain": 3.0,
            "outcome_determined": True,
            "right_censored": False,
            "safe": True,
        }],
        "manifest_path": str(manifest_path),
        "manifest_sha256": AUDIT._sha256(manifest_path),
    }
    return report, report_path


def test_risk_v2_accepts_only_determined_safe_activations(
    tmp_path: Path,
) -> None:
    report, report_path = _payload(tmp_path)
    result = AUDIT.audit_calibration_risk(
        report, report_path=report_path
    )

    assert result["passed"]
    assert result["deployment_authorized"]
    assert result["counts"]["activated_count"] == 1
    assert result["counts"]["activated_right_censored_count"] == 0


def test_risk_v2_vetoes_activated_right_censored_action(
    tmp_path: Path,
) -> None:
    report, report_path = _payload(tmp_path)
    report["records"][0].update({
        "state_hash": "timeout",
        "outcome_determined": False,
        "right_censored": True,
    })
    result = AUDIT.audit_calibration_risk(
        report, report_path=report_path
    )

    assert not result["passed"]
    assert not result["deployment_authorized"]
    assert "activated_right_censored_context" in result["issues"]
    assert result["activated_right_censored_state_hashes"] == ["timeout"]


def test_risk_v2_keeps_unselected_censored_context_as_q0(
    tmp_path: Path,
) -> None:
    report, report_path = _payload(tmp_path)
    report["records"].append({
        "model_kind": "gat",
        "partition": "heldout",
        "state_hash": "q0-fallback",
        "action_eligible": True,
        "benefit_probability": 0.4,
        "expected_gain": 3.0,
        "outcome_determined": False,
        "right_censored": True,
        "safe": True,
        "qg2_engine_status": "MEMORY_LIMIT",
    })
    result = AUDIT.audit_calibration_risk(
        report, report_path=report_path
    )

    assert result["passed"]
    assert result["counts"]["activated_count"] == 1
    assert result["counts"]["unselected_or_prethreshold_veto_count"] == 1


def test_risk_v2_vetoes_activated_memory_or_unsafe_action(
    tmp_path: Path,
) -> None:
    report, report_path = _payload(tmp_path)
    report["records"][0].update({
        "state_hash": "memory-unsafe",
        "safe": False,
        "memory_adverse": True,
    })
    result = AUDIT.audit_calibration_risk(
        report, report_path=report_path
    )

    assert not result["passed"]
    assert "activated_exact_unsafe_context" in result["issues"]
    assert "activated_memory_adverse_context" in result["issues"]


def test_risk_v2_requires_hash_bound_q0_only_manifest(
    tmp_path: Path,
) -> None:
    report, report_path = _payload(tmp_path)
    manifest_path = Path(report["manifest_path"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["can_certify"] = True
    manifest["fallback"] = "QB1"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    report["manifest_sha256"] = AUDIT._sha256(manifest_path)
    result = AUDIT.audit_calibration_risk(
        report, report_path=report_path
    )

    assert not result["passed"]
    assert "manifest_forbidden_authority:can_certify" in result["issues"]
    assert "manifest_literal_q0_fallback_mismatch" in result["issues"]


def test_risk_v2_fails_closed_on_manifest_threshold_drift(
    tmp_path: Path,
) -> None:
    report, report_path = _payload(tmp_path)
    manifest_path = Path(report["manifest_path"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["calibration"]["probability_threshold"] = 0.7
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    report["manifest_sha256"] = AUDIT._sha256(manifest_path)
    result = AUDIT.audit_calibration_risk(
        report, report_path=report_path
    )

    assert not result["passed"]
    assert "manifest_probability_threshold_mismatch" in result["issues"]


def test_risk_v2_freeze_binds_runtime_inputs() -> None:
    freeze_path = (
        ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
        / "qg2_calibration_risk_v2_freeze.json"
    )
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))

    assert freeze["development_only"]
    assert not freeze["deployable"]
    assert freeze["authority"] == "deployment_veto_only"
    assert freeze["base_calibrator_sha256"] == AUDIT._sha256(
        ROOT / "scripts/calibrate_p0v5_qg2_models.py"
    )
    assert freeze["oracle_execution_freeze_sha256"] == AUDIT._sha256(
        ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
        / "qg2_action_surface_v2_oracle_execution_freeze.json"
    )
    assert freeze["frozen_file_sha256"][
        "scripts/audit_p0v5_qg2_calibration_risk_v2.py"
    ] == AUDIT._sha256(
        ROOT / "scripts/audit_p0v5_qg2_calibration_risk_v2.py"
    )

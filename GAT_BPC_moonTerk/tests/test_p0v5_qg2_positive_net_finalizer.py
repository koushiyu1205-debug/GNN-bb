from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/finalize_p0v5_qg2_positive_net_candidate.py"
SPEC = importlib.util.spec_from_file_location("qg2_positive_net_finalizer", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_positive_net_finalizer_freeze_requires_formal_and_no_switch() -> None:
    MODULE._validate_freeze()
    freeze = json.loads(MODULE.FREEZE.read_text(encoding="utf-8"))
    assert freeze["formal_full20_required"] is True
    assert freeze["final_regression_and_native_tests_required"] is True
    assert freeze["production_switch_authorized"] is False
    assert freeze["fallback_action"] == "Q0"


def test_positive_net_candidate_audit_rejects_scope_expansion() -> None:
    payload = {
        "schema_version": MODULE.CANDIDATE_SCHEMA,
        "status": "FROZEN_EXPERIMENT_CANDIDATE",
        "production_default": True,
        "production_switch_performed": False,
        "evaluation_only": True,
        "fallback_action": "Q0",
        "all_arms_rejected_action": "Q0",
        "ordering_only": True,
        "can_filter": True,
        "can_prune": False,
        "can_change_bound": False,
        "can_certify": False,
        "development_e2e_passed": True,
        "formal_full20_passed": True,
        "regression_and_native_tests": {"passed": True},
        "frozen_file_sha256": {},
    }
    issues = MODULE.audit_positive_net_candidate_payload(payload)
    assert "production_scope_expansion" in issues
    assert "forbidden_authority:can_filter" in issues


def test_positive_net_report_recomputes_p99_censor_and_scale_gates(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "manifest.json"
    _write(manifest, {})
    metrics = {
        "net_geomean_ratio": 0.99,
        "activation_count": 2,
        "selected_right_censored_count": 0,
        "selected_unsafe_count": 0,
    }
    heldout = {
        **metrics,
        "per_scale": {
            "30": {"net_geomean_ratio": 0.99},
            "50": {"net_geomean_ratio": 1.01},
        },
    }
    report = {
        "schema_version": MODULE.e2e.POSITIVE_SCHEMA,
        "gat_positive_net_exact_safe_gate_passed": True,
        "development_e2e_authorized": True,
        "minimum_speedup_gate_enabled": False,
        "selected_censor_or_unsafe_is_hard_veto": True,
        "production_switch_authorized": False,
        "fallback_action": "Q0",
        "best_positive_net_model_kind": "gat",
        "evaluation_manifest_sha256": MODULE._sha256(manifest),
        "models": [{
            "model_kind": "gat",
            "positive_net_exact_safe_gate_passed": True,
            "all_replays_exact_safe": True,
            "inference_p99_ms": 9.9,
            "thresholds": {
                "probability_threshold": 0.8,
                "expected_gain_threshold": 1.0,
            },
            "calibration": metrics,
            "heldout": heldout,
        }],
    }
    assert MODULE._validate_positive_report(
        report, manifest=manifest
    )["model_kind"] == "gat"

    report["models"][0]["inference_p99_ms"] = 10.1
    with pytest.raises(ValueError, match="positive_net_gat_metrics_mismatch"):
        MODULE._validate_positive_report(report, manifest=manifest)


def test_final_acceptance_recomputes_actions_ratios_and_redlines(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    _write(acceptance, {})
    control = tmp_path / "control"
    guided = tmp_path / "guided"
    control.mkdir()
    guided.mkdir()
    monkeypatch.setattr(
        MODULE.formal.base, "_acceptance_artifact_hash", lambda _root: "hash"
    )
    by_scale = {}
    for scale in (5, 10, 20, 30, 50):
        exact = 15 if scale == 50 else 20
        by_scale[str(scale)] = {
            "instance_count": 20,
            "control_exact_count": exact,
            "guided_exact_count": exact,
            "paired_geomean_wall_ratio": 1.0 if scale < 30 else 0.99,
            "guided_qg2_inference_event_count": 0 if scale < 30 else 1,
            "guided_qg2_action_count": 0 if scale < 30 else 1,
        }
    payload = {
        "schema_version": MODULE.formal.E2E_ACCEPTANCE_SCHEMA,
        "mode": "positive_net_formal",
        "passed": True,
        "violation_count": 0,
        "by_scale": by_scale,
        "scale30_50_combined_geomean_wall_ratio": 0.99,
        "pairs": [{
            "objective_match": True,
            "control": {"redlines_zero": True},
            "guided": {"redlines_zero": True},
        }],
        "control_root": str(control),
        "guided_root": str(guided),
        "control_root_hash": "hash",
        "guided_root_hash": "hash",
    }
    assert MODULE._valid_acceptance(
        payload,
        path=acceptance,
        mode="positive_net_formal",
        scales={5, 10, 20, 30, 50},
    )
    by_scale["30"]["guided_qg2_action_count"] = 0
    by_scale["50"]["guided_qg2_action_count"] = 0
    assert not MODULE._valid_acceptance(
        payload,
        path=acceptance,
        mode="positive_net_formal",
        scales={5, 10, 20, 30, 50},
    )


def test_positive_net_finalizer_runs_only_after_formal_authority(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    required_names = (
        "ORACLE_FREEZE", "ORACLE", "TRAINING", "SELECTIVE_EVIDENCE",
        "CALIBRATION", "POSITIVE_REPORT", "MANIFEST", "E2E_STATE",
        "E2E_RESULT", "FORMAL_STATE", "FORMAL_RESULT",
    )
    for name in required_names:
        path = tmp_path / f"{name.lower()}.json"
        _write(path, {})
        monkeypatch.setattr(MODULE, name, path)
    candidate = tmp_path / "candidate.json"
    audit = tmp_path / "audit.json"
    state = tmp_path / "state.json"
    monkeypatch.setattr(MODULE, "CANDIDATE", candidate)
    monkeypatch.setattr(MODULE, "AUDIT", audit)
    monkeypatch.setattr(MODULE, "STATE", state)
    monkeypatch.setattr(MODULE, "_validate_freeze", lambda: None)
    monkeypatch.setattr(MODULE, "_matching_formal_controller", lambda _pid: False)
    monkeypatch.setattr(
        MODULE,
        "validate_positive_net_candidate_authority",
        lambda: MODULE.MANIFEST,
    )
    tests = {"passed": True, "commands": []}
    monkeypatch.setattr(MODULE, "_run_tests", lambda: tests)
    payload = {
        "schema_version": MODULE.CANDIDATE_SCHEMA,
        "status": "FROZEN_EXPERIMENT_CANDIDATE",
    }
    monkeypatch.setattr(
        MODULE,
        "build_positive_net_candidate_payload",
        lambda _manifest, tests: payload,
    )
    monkeypatch.setattr(
        MODULE, "audit_positive_net_candidate_payload", lambda _payload: []
    )
    monkeypatch.setattr(
        sys, "argv", ["positive-net-finalizer", "--wait-for-pid", "123"]
    )

    assert MODULE.main() == 0
    assert candidate.is_file()
    assert audit.is_file()
    final_state = json.loads(state.read_text(encoding="utf-8"))
    assert final_state["status"] == "POSITIVE_NET_CANDIDATE_FROZEN_AND_AUDITED"
    assert final_state["production_switch_performed"] is False
    assert final_state["historical_baselines_unchanged"] is True
    assert final_state["fallback_action"] == "Q0"

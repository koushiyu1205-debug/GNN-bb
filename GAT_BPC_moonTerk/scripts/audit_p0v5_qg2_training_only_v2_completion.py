#!/usr/bin/env python3
"""Completion audit for the P0V5 QG2 training-only-v2 pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
BUILD = ROOT / "build/native-spprc-bidirectional-feasibility-v1"

ORACLE_FREEZE = RUN_ROOT / "qg2_action_surface_v2_oracle_execution_freeze.json"
ORACLE = RUN_ROOT / "oracle_qg2_action_surface_v2_stage1.json"
TRAINING_FREEZE = RUN_ROOT / "qg2_action_surface_v2_training_only_v2_freeze.json"
TRAINING_GATE = RUN_ROOT / "qg2_action_surface_v2_training_only_gate_v2.json"
AUTHORIZED_ORACLE = RUN_ROOT / "oracle_qg2_action_surface_v2_training_only_v2_view.json"
TRAINING = RUN_ROOT / "training_qg2_action_surface_v2_training_only_v2/training_report.json"
SELECTOR_FREEZE = RUN_ROOT / "qg2_context_arm_selector_controller_freeze.json"
SELECTOR_STATE = RUN_ROOT / "qg2_context_arm_selector_controller_state.json"
SELECTOR = RUN_ROOT / "context_arm_selector_feasibility_v1/selector_report.json"
CALIBRATION_FREEZE = RUN_ROOT / "qg2_training_only_v2_calibration_controller_freeze.json"
CALIBRATION_STATE = RUN_ROOT / "qg2_training_only_v2_calibration_controller_state.json"
CALIBRATION = RUN_ROOT / "calibration_qg2_action_surface_v2_training_only_v2/calibration_report.json"
RISK_FREEZE = RUN_ROOT / "qg2_calibration_risk_v2_freeze.json"
RISK = RUN_ROOT / "qg2_training_only_v2_calibration_risk_audit.json"
E2E_FREEZE = RUN_ROOT / "qg2_training_only_v2_e2e_controller_freeze.json"
E2E_STATE = RUN_ROOT / "qg2_training_only_v2_e2e_controller_state.json"
E2E = RUN_ROOT / "e2e_training_only_v2_development_acceptance.json"
FORMAL_FREEZE = RUN_ROOT / "qg2_training_only_v2_formal_controller_freeze.json"
FORMAL_STATE = RUN_ROOT / "qg2_training_only_v2_formal_controller_state.json"
FORMAL = RUN_ROOT / "formal_full20_acceptance_qg2_training_only_v2.json"
CANDIDATE = RUN_ROOT / "P0V5_QG2_LABEL_STATE_GAT_TRAINING_ONLY_V2_candidate_freeze.json"

ORACLE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
TRAINING_GATE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_training_only_gate.v2"
TRAINING_SCHEMA = "lunar_ice_bpc.p0v5_qg2_model_comparison.v3"
SELECTOR_SCHEMA = "lunar_ice_bpc.p0v5_qg2_context_arm_selector_feasibility.v1"
CALIBRATION_SCHEMA = "lunar_ice_bpc.p0v5_qg2_fresh_process_calibration.v4"
RISK_SCHEMA = "lunar_ice_bpc.p0v5_qg2_calibration_risk_audit.v2"
ACCEPTANCE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_paired_acceptance.v1"
MANIFEST_SCHEMA = "lunar_ice_bpc.p0v5_qg2_manifest.v1"
SUPERVISION_SCHEMA = "lunar_ice_bpc.p0v5_qg2_action_reachable_supervision.v2"
ACTION_SURFACE = "same_terminal_class_and_reduced_cost_bucket.v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--run-tests", action="store_true")
    parser.add_argument("--pre-final-freeze", action="store_true")
    args = parser.parse_args()

    checks = {
        "oracle_and_training_authority": _audit_training_authority(),
        "linear_mlp_gat_training": _audit_training(),
        "context_selector_decision": _audit_selector(),
        "fresh_process_calibration": _audit_calibration(),
        "activated_risk_veto": _audit_risk(),
        "development_scale30_50_e2e": _audit_acceptance_stage(
            freeze=E2E_FREEZE,
            state_path=E2E_STATE,
            result_path=E2E,
            freeze_schema=(
                "lunar_ice_bpc.p0v5_qg2_training_only_v2_e2e_controller_freeze.v1"
            ),
            state_schema=(
                "lunar_ice_bpc.p0v5_qg2_training_only_v2_e2e_controller_state.v1"
            ),
            passed_status="E2E_PASSED_PENDING_FORMAL_FULL20",
            mode="development",
            scales={30, 50},
        ),
        "formal_scale5_to_50_full20": _audit_acceptance_stage(
            freeze=FORMAL_FREEZE,
            state_path=FORMAL_STATE,
            result_path=FORMAL,
            freeze_schema=(
                "lunar_ice_bpc.p0v5_qg2_training_only_v2_formal_controller_freeze.v1"
            ),
            state_schema=(
                "lunar_ice_bpc.p0v5_qg2_training_only_v2_formal_controller_state.v1"
            ),
            passed_status="FORMAL_FULL20_PASSED",
            mode="formal",
            scales={5, 10, 20, 30, 50},
        ),
    }
    if not args.pre_final_freeze:
        checks["independent_candidate_freeze"] = _audit_candidate()
    checks["regression_and_native_tests"] = (
        _run_tests()
        if args.run_tests
        else _check("INCOMPLETE", "tests not requested")
    )
    complete = all(row["status"] == "PASS" for row in checks.values())
    payload = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_training_only_v2_completion_audit.v1"
        ),
        "objective": "P0V5 Proof-Tail GAT V2 Q0-Anchored Label-State Guidance",
        "track": "training_only_v2_selective_qg2",
        "pre_final_freeze": bool(args.pre_final_freeze),
        "complete": complete,
        "checks": checks,
        "required_check_count": len(checks),
        "passed_check_count": sum(row["status"] == "PASS" for row in checks.values()),
        "failed_check_count": sum(row["status"] == "FAIL" for row in checks.values()),
        "incomplete_check_count": sum(
            row["status"] == "INCOMPLETE" for row in checks.values()
        ),
        "completion_rule": "all_required_checks_must_pass",
    }
    output = _resolve(args.output)
    _write(output, payload)
    print(json.dumps({
        "complete": complete,
        "passed": payload["passed_check_count"],
        "failed": payload["failed_check_count"],
        "incomplete": payload["incomplete_check_count"],
        "output": str(output),
    }, sort_keys=True), flush=True)
    return 0 if complete else 2


def _audit_training_authority() -> dict:
    required = (ORACLE_FREEZE, ORACLE, TRAINING_FREEZE, TRAINING_GATE, AUTHORIZED_ORACLE)
    if not all(path.is_file() for path in required):
        return _check("INCOMPLETE", "Oracle/training authority missing")
    issues = _freeze_issues(ORACLE_FREEZE) + _freeze_issues(TRAINING_FREEZE)
    oracle = _load(ORACLE)
    gate = _load(TRAINING_GATE)
    authorized = _load(AUTHORIZED_ORACLE)
    if oracle.get("schema_version") != ORACLE_SCHEMA:
        issues.append("oracle_schema_mismatch")
    if str(oracle.get("execution_freeze_sha256") or "") != _sha256(ORACLE_FREEZE):
        issues.append("oracle_execution_freeze_mismatch")
    if not bool(oracle.get("development_only")) or bool(oracle.get("deployable")):
        issues.append("oracle_safety_mismatch")
    if gate.get("schema_version") != TRAINING_GATE_SCHEMA:
        issues.append("training_gate_schema_mismatch")
    if str(gate.get("oracle_summary_sha256") or "") != _sha256(ORACLE):
        issues.append("training_gate_oracle_mismatch")
    if not bool((gate.get("gate") or {}).get("passed")) or not bool(
        gate.get("training_authorized")
    ):
        issues.append("training_data_gate_failed")
    if bool(gate.get("deployment_authorized")):
        issues.append("training_gate_illegal_deployment_authority")
    if not bool(gate.get("point_geomean_is_report_only")) or not bool(
        gate.get("instance_bootstrap_is_report_only")
    ):
        issues.append("training_only_statistical_role_mismatch")
    if not bool((authorized.get("oracle_gate") or {}).get("passed")) or not bool(
        authorized.get("training_permitted")
    ):
        issues.append("authorized_oracle_training_permission_missing")
    if bool(authorized.get("deployable")):
        issues.append("authorized_oracle_illegal_deployable")
    return _check("FAIL" if issues else "PASS", "bounded Oracle and data-only training authority", issues=issues)


def _audit_training() -> dict:
    if not TRAINING.is_file():
        return _check("INCOMPLETE", "Linear/MLP/GAT training report missing")
    report = _load(TRAINING)
    issues = []
    if report.get("schema_version") != TRAINING_SCHEMA:
        issues.append("training_schema_mismatch")
    if str(report.get("oracle_summary_sha256") or "") != _sha256(AUTHORIZED_ORACLE):
        issues.append("training_oracle_binding_mismatch")
    if report.get("supervision_schema_version") != SUPERVISION_SCHEMA:
        issues.append("supervision_schema_mismatch")
    if report.get("queue_action_surface") != ACTION_SURFACE:
        issues.append("queue_action_surface_mismatch")
    if bool(report.get("deployable")) or not bool(report.get("oracle_gate_passed")):
        issues.append("training_safety_or_authority_mismatch")
    split = _bound(report.get("split_path"), report.get("split_sha256"))
    if split is None:
        issues.append("instance_split_binding_failed")
    models = {str(row.get("model_kind") or ""): row for row in report.get("models") or ()}
    if set(models) != {"linear", "mlp", "gat"}:
        issues.append("model_comparison_universe_mismatch")
    for kind, row in models.items():
        if _bound(row.get("checkpoint_path"), row.get("checkpoint_sha256")) is None:
            issues.append(f"checkpoint_binding_failed:{kind}")
    return _check("FAIL" if issues else "PASS", "instance-isolated Linear/MLP/Tiny-GAT training", issues=issues)


def _audit_selector() -> dict:
    if not all(path.is_file() for path in (SELECTOR_FREEZE, SELECTOR_STATE, SELECTOR)):
        return _check("INCOMPLETE", "context selector decision missing")
    issues = _freeze_issues(SELECTOR_FREEZE)
    state = _load(SELECTOR_STATE)
    report = _load(SELECTOR)
    if report.get("schema_version") != SELECTOR_SCHEMA:
        issues.append("selector_schema_mismatch")
    if bool(report.get("deployable")) or bool(report.get("starts_solver_process")):
        issues.append("selector_safety_mismatch")
    if bool(report.get("changes_qg2")):
        issues.append("selector_illegally_changed_qg2")
    if str(report.get("fallback_action") or "") != "Q0" or str(
        report.get("all_arms_rejected_action") or ""
    ) != "Q0":
        issues.append("selector_literal_q0_fallback_mismatch")
    if bool(report.get("continued_development_recommended")):
        issues.append("combined_selector_recommended_but_not_implemented")
    if str(state.get("selector_report_sha256") or "") != _sha256(SELECTOR):
        issues.append("selector_state_report_binding_mismatch")
    return _check("FAIL" if issues else "PASS", "post-training context-selector decision", issues=issues)


def _audit_calibration() -> dict:
    if not all(path.is_file() for path in (CALIBRATION_FREEZE, CALIBRATION_STATE, CALIBRATION)):
        return _check("INCOMPLETE", "fresh-process calibration missing")
    issues = _freeze_issues(CALIBRATION_FREEZE)
    state = _load(CALIBRATION_STATE)
    report = _load(CALIBRATION)
    if str(state.get("status") or "") != "CALIBRATION_AND_RISK_AUDIT_PASSED_PENDING_E2E":
        issues.append("calibration_controller_not_passed")
    if str(state.get("calibration_report_sha256") or "") != _sha256(CALIBRATION):
        issues.append("calibration_state_binding_mismatch")
    if report.get("schema_version") != CALIBRATION_SCHEMA or not bool(
        report.get("gate_pass") and report.get("deployment_authorized")
    ):
        issues.append("calibration_gate_failed")
    models = {
        str(row.get("model_kind") or ""): row
        for row in report.get("models") or ()
    }
    gat = models.get("gat") or {}
    gat_calibration = gat.get("calibration") or {}
    gat_heldout = gat.get("heldout") or {}
    if not bool(gat_calibration.get("passes_risk_precision_gate")):
        issues.append("gat_calibration_risk_precision_gate_failed")
    if float(gat_calibration.get("harmful_rate_95_upper", 1.0)) > 0.05:
        issues.append("gat_harmful_rate_upper_exceeded")
    if float(gat_calibration.get("beneficial_precision_95_lower", 0.0)) < 0.80:
        issues.append("gat_beneficial_precision_lower_not_met")
    if float(gat_heldout.get("net_geomean_ratio", 1.0)) > 0.90:
        issues.append("gat_heldout_tail_ratio_not_met")
    if float(report.get("gat_vs_best_non_gat_ratio", 1.0)) > 0.98:
        issues.append("gat_advantage_over_non_gat_not_met")
    if float(report.get("gat_inference_p99_ms", 1.0e30)) > 10.0:
        issues.append("gat_inference_p99_exceeded")
    if str(report.get("training_report_sha256") or "") != _sha256(TRAINING):
        issues.append("calibration_training_binding_mismatch")
    manifest = _bound(report.get("manifest_path"), report.get("manifest_sha256"))
    if manifest is None:
        issues.append("calibration_manifest_binding_failed")
    else:
        payload = _load(manifest)
        if not bool(
            payload.get("schema_version") == MANIFEST_SCHEMA
            and payload.get("deployment_authorized")
            and payload.get("ordering_only")
            and not payload.get("can_filter")
            and not payload.get("can_prune")
            and not payload.get("can_change_bound")
            and not payload.get("can_certify")
            and str(payload.get("fallback") or "") == "P0V4_V5_Q0"
            and set(payload.get("allowed_scales") or ()) == {30, 50}
        ):
            issues.append("calibration_manifest_safety_failed")
    return _check("FAIL" if issues else "PASS", "fresh-process calibration and manifest", issues=issues)


def _audit_risk() -> dict:
    if not all(path.is_file() for path in (RISK_FREEZE, RISK)):
        return _check("INCOMPLETE", "activated-action risk audit missing")
    issues = _freeze_issues(RISK_FREEZE)
    risk = _load(RISK)
    if not bool(
        risk.get("schema_version") == RISK_SCHEMA
        and risk.get("passed")
        and risk.get("deployment_authorized")
        and str(risk.get("calibration_report_sha256") or "") == _sha256(CALIBRATION)
        and int((risk.get("counts") or {}).get("activated_right_censored_count") or 0) == 0
        and int((risk.get("counts") or {}).get("activated_unsafe_count") or 0) == 0
        and int((risk.get("counts") or {}).get("activated_memory_adverse_count") or 0) == 0
    ):
        issues.append("activated_action_risk_gate_failed")
    return _check("FAIL" if issues else "PASS", "censor, exact-safety, and memory deployment veto", issues=issues)


def _audit_acceptance_stage(
    *,
    freeze: Path,
    state_path: Path,
    result_path: Path,
    freeze_schema: str,
    state_schema: str,
    passed_status: str,
    mode: str,
    scales: set[int],
) -> dict:
    if not all(path.is_file() for path in (freeze, state_path, result_path)):
        return _check("INCOMPLETE", f"{mode} acceptance missing")
    issues = _freeze_issues(freeze, expected_schema=freeze_schema)
    state = _load(state_path)
    result = _load(result_path)
    if state.get("schema_version") != state_schema or str(state.get("status") or "") != passed_status:
        issues.append("controller_state_not_passed")
    if str(state.get("result_sha256") or "") != _sha256(result_path):
        issues.append("state_result_binding_mismatch")
    if not bool(
        result.get("schema_version") == ACCEPTANCE_SCHEMA
        and result.get("mode") == mode
        and result.get("passed")
        and int(result.get("violation_count") or 0) == 0
        and {int(value) for value in (result.get("by_scale") or {})} == scales
    ):
        issues.append("acceptance_gate_failed")
    for prefix in ("control", "guided"):
        root = _resolve(result.get(f"{prefix}_root") or "")
        observed_hash = _artifact_hash(root) if root.is_dir() else ""
        if (
            not observed_hash
            or observed_hash != str(result.get(f"{prefix}_root_hash") or "")
        ):
            issues.append(f"{prefix}_artifact_binding_failed")
    return _check("FAIL" if issues else "PASS", f"{mode} paired acceptance", issues=issues)


def _audit_candidate() -> dict:
    if not CANDIDATE.is_file():
        return _check("INCOMPLETE", "independent candidate freeze missing")
    payload = _load(CANDIDATE)
    issues = []
    if payload.get("schema_version") != "lunar_ice_bpc.p0v5_qg2_training_only_v2_candidate_freeze.v1":
        issues.append("candidate_schema_mismatch")
    if payload.get("status") != "FROZEN_EXPERIMENT_CANDIDATE":
        issues.append("candidate_status_mismatch")
    if bool(payload.get("production_default")) or bool(payload.get("production_switch_performed")):
        issues.append("candidate_illegal_production_switch")
    if not bool(
        payload.get("historical_baselines_unchanged")
        and not payload.get("p0v4_changed")
        and not payload.get("p0v5_exact_control_changed")
        and payload.get("exact_control_freeze_id")
        == "P0V4_V5_BIDIRECTIONAL_EXACT_FINAL_CANDIDATE"
        and payload.get("development_e2e_passed")
        and payload.get("formal_full20_passed")
        and payload.get("deployment_authorized")
        and payload.get("scale5_10_20_runtime_bypass")
        and set(payload.get("allowed_scales") or ()) == {30, 50}
        and payload.get("fallback_action") == "Q0"
        and not payload.get("selector_in_final_runtime")
        and bool(payload.get("source_engine_hash"))
        and bool(payload.get("runtime_implementation_hash"))
        and set(payload.get("exact_action_policy_hashes_by_scale") or {})
        == {"30", "50"}
    ):
        issues.append("candidate_acceptance_or_baseline_contract_failed")
    direct_bindings = {
        "selected_exact_config": "selected_exact_config_sha256",
        "selector_report": "selector_report_sha256",
        "oracle_summary": "oracle_summary_sha256",
        "training_report": "training_report_sha256",
        "manifest_path": "manifest_sha256",
        "checkpoint_path": "checkpoint_sha256",
        "calibration_report": "calibration_report_sha256",
        "calibration_risk_audit": "calibration_risk_audit_sha256",
        "development_acceptance": "development_acceptance_sha256",
        "formal_acceptance": "formal_acceptance_sha256",
        "pre_freeze_completion_audit": "pre_freeze_completion_audit_sha256",
    }
    for path_key, hash_key in direct_bindings.items():
        if _bound(payload.get(path_key), payload.get(hash_key)) is None:
            issues.append(f"candidate_direct_binding_failed:{path_key}")
    frozen_files = dict(payload.get("frozen_file_sha256") or {})
    if not frozen_files:
        issues.append("candidate_frozen_universe_empty")
    for raw_path, expected in frozen_files.items():
        path = _resolve(raw_path)
        if not path.is_file() or _sha256(path) != str(expected):
            issues.append(f"candidate_frozen_drift:{raw_path}")
    return _check("FAIL" if issues else "PASS", "independent frozen experiment candidate", issues=issues)


def _run_tests() -> dict:
    commands = _test_commands()
    rows = []
    for command in commands:
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        rows.append({
            "command": command,
            "returncode": int(completed.returncode),
            "stdout_tail": completed.stdout[-4000:],
            "stderr_tail": completed.stderr[-4000:],
        })
    return _check(
        "PASS" if all(row["returncode"] == 0 for row in rows) else "FAIL",
        "QG2 Python, Native CTest, State 176 B, and diff checks",
        commands=rows,
    )


def _test_commands() -> tuple[list[str], ...]:
    qg2_tests = sorted(ROOT.glob("tests/test_p0v5_qg2*.py"))
    return (
        [sys.executable, "-m", "pytest", "-q", *(str(path) for path in qg2_tests)],
        ["ctest", "--test-dir", str(BUILD), "--output-on-failure"],
        ["git", "diff", "--check"],
    )


def _freeze_issues(path: Path, *, expected_schema: str | None = None) -> list[str]:
    if not path.is_file():
        return [f"freeze_missing:{path.name}"]
    payload = _load(path)
    issues = []
    if expected_schema is not None and payload.get("schema_version") != expected_schema:
        issues.append(f"freeze_schema_mismatch:{path.name}")
    if bool(payload.get("deployable")) or bool(payload.get("production_default")):
        issues.append(f"freeze_safety_mismatch:{path.name}")
    for raw_path, expected in dict(payload.get("frozen_file_sha256") or {}).items():
        target = _resolve(raw_path)
        if not target.is_file() or _sha256(target) != str(expected):
            issues.append(f"freeze_drift:{path.name}:{raw_path}")
    return issues


def _bound(raw_path, expected) -> Path | None:
    path = _resolve(raw_path or "")
    return path if path.is_file() and _sha256(path) == str(expected or "") else None


def _artifact_hash(root: Path) -> str:
    digest = hashlib.sha256()
    paths = set()
    for pattern in (
        "**/b4_2_cold_exact_rows.csv",
        "**/b4_2_cold_exact_state.json",
        "**/b4_2_cold_exact_summary.json",
        "**/tree_closure_001.json",
    ):
        paths.update(root.glob(pattern))
    if not paths:
        return ""
    for path in sorted(paths):
        digest.update(str(path.relative_to(root)).encode("utf-8"))
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _check(status: str, note: str, **evidence) -> dict:
    return {"status": status, "note": note, "evidence": evidence}


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

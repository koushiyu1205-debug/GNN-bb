#!/usr/bin/env python3
"""Freeze and audit the positive-net QG2 experiment after formal full20."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import run_p0v5_qg2_positive_net_e2e_after_calibration as e2e  # noqa: E402
import run_p0v5_qg2_positive_net_formal_after_e2e as formal  # noqa: E402

from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (  # noqa: E402
    QG2_POSITIVE_NET_EVALUATION_GATE_V1,
    QG2_RUNTIME_POLICY_ID,
    qg2_runtime_implementation_hash,
)


RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
BUILD = ROOT / "build/native-spprc-bidirectional-feasibility-v1"
CONFIG = ROOT / "runs/p0v4_v5_exact_gat_binding_20260731/selected_exact_v5.yaml"
FREEZE = RUN_ROOT / "qg2_positive_net_candidate_finalizer_freeze_v3.json"
ORACLE_FREEZE = RUN_ROOT / "qg2_action_surface_v2_oracle_execution_freeze.json"
ORACLE = RUN_ROOT / "oracle_qg2_action_surface_v2_stage1.json"
TRAINING = (
    RUN_ROOT
    / "training_qg2_action_surface_v2_training_only_v2/training_report.json"
)
SELECTIVE_EVIDENCE = (
    RUN_ROOT / "qg2_training_only_v2_selective_oracle_evidence.json"
)
CALIBRATION = RUN_ROOT / "calibration_qg2_combined_v1_base/calibration_report.json"
POSITIVE_REPORT = RUN_ROOT / "qg2_positive_net_calibration_report.json"
MANIFEST = RUN_ROOT / "qg2_positive_net_evaluation_manifest.json"
E2E_STATE = RUN_ROOT / "qg2_positive_net_e2e_state.json"
E2E_RESULT = RUN_ROOT / "e2e_qg2_positive_net_v1_acceptance.json"
FORMAL_STATE = RUN_ROOT / "qg2_positive_net_formal_state.json"
FORMAL_RESULT = RUN_ROOT / "formal_full20_qg2_positive_net_v1_acceptance.json"
CANDIDATE = (
    RUN_ROOT / "P0V5_QG2_LABEL_STATE_GAT_POSITIVE_NET_V1_candidate_freeze.json"
)
AUDIT = RUN_ROOT / "qg2_positive_net_completion_audit.json"
STATE = RUN_ROOT / "qg2_positive_net_candidate_finalizer_state.json"

RUNTIME_SOURCE = ROOT / "src/lunar_ice_bpc/guidance/proof_queue_label_state_runtime.py"
MODEL_SOURCE = ROOT / "src/lunar_ice_bpc/guidance/proof_queue_label_state_gat.py"
EVIDENCE_SOURCE = ROOT / "src/lunar_ice_bpc/guidance/qg2_oracle_evidence.py"
AUTHORITY_SOURCE = ROOT / "src/lunar_ice_bpc/guidance/qg2_runtime_oracle_authority.py"
CALIBRATION_SOURCE = ROOT / "scripts/evaluate_p0v5_qg2_positive_net_calibration.py"
ANALYZER_SOURCE = ROOT / "scripts/analyze_p0v5_qg2_positive_net_acceptance.py"
E2E_SOURCE = ROOT / "scripts/run_p0v5_qg2_positive_net_e2e_after_calibration.py"
FORMAL_SOURCE = ROOT / "scripts/run_p0v5_qg2_positive_net_formal_after_e2e.py"
NATIVE_EXTENSIONS = tuple(sorted(BUILD.glob("lunar_spprc_native*.so")))

FREEZE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_positive_net_finalizer_freeze.v3"
CANDIDATE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_positive_net_candidate.v1"
AUDIT_SCHEMA = "lunar_ice_bpc.p0v5_qg2_positive_net_completion_audit.v1"
STATE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_positive_net_finalizer_state.v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-for-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = max(1.0, min(60.0, float(args.poll_sec)))
    _validate_freeze()
    _state(
        "WAITING_FOR_POSITIVE_NET_FORMAL_FULL20",
        wait_for_pid=int(args.wait_for_pid),
    )
    while _matching_formal_controller(args.wait_for_pid):
        time.sleep(poll)

    required = (
        ORACLE_FREEZE, ORACLE, TRAINING, SELECTIVE_EVIDENCE,
        CALIBRATION, POSITIVE_REPORT, MANIFEST, E2E_STATE, E2E_RESULT,
        FORMAL_STATE, FORMAL_RESULT,
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        _state("NOT_STARTED_REQUIRED_EVIDENCE_MISSING", missing=missing)
        return 2
    if CANDIDATE.exists() or AUDIT.exists():
        _state("REFUSED_EXISTING_POSITIVE_NET_CANDIDATE_OUTPUT")
        return 3
    try:
        manifest = validate_positive_net_candidate_authority()
    except Exception as exc:
        _state(
            "NOT_STARTED_POSITIVE_NET_AUTHORITY_INVALID",
            error=f"{type(exc).__name__}:{exc}",
        )
        return 3

    _state("RUNNING_FINAL_REGRESSION_AND_NATIVE_TESTS")
    tests = _run_tests()
    if not bool(tests.get("passed")):
        _write_audit(False, ["regression_or_native_tests_failed"], tests)
        _state("FINAL_REGRESSION_OR_NATIVE_TESTS_FAILED", tests=tests)
        return 2
    try:
        payload = build_positive_net_candidate_payload(manifest, tests=tests)
    except Exception as exc:
        _state(
            "POSITIVE_NET_CANDIDATE_BUILD_FAILED",
            error=f"{type(exc).__name__}:{exc}",
        )
        return 3
    _write(CANDIDATE, payload)
    issues = audit_positive_net_candidate_payload(payload)
    _write_audit(not issues, issues, tests)
    if issues:
        _state(
            "POSITIVE_NET_CANDIDATE_AUDIT_FAILED",
            candidate=str(CANDIDATE),
            candidate_sha256=_sha256(CANDIDATE),
            issues=issues,
        )
        return 2
    _state(
        "POSITIVE_NET_CANDIDATE_FROZEN_AND_AUDITED",
        candidate=str(CANDIDATE),
        candidate_sha256=_sha256(CANDIDATE),
        completion_audit=str(AUDIT),
        completion_audit_sha256=_sha256(AUDIT),
        production_switch_performed=False,
        historical_baselines_unchanged=True,
        fallback_action="Q0",
    )
    return 0


def validate_positive_net_candidate_authority() -> Path:
    e2e_state = _load(E2E_STATE)
    e2e_result = _load(E2E_RESULT)
    manifest = formal._validate_e2e_authority(
        state=e2e_state,
        result=e2e_result,
    )
    if manifest != MANIFEST.resolve():
        raise ValueError("positive-net evaluation manifest path mismatch")
    state = _load(FORMAL_STATE)
    result = _load(FORMAL_RESULT)
    if not bool(
        state.get("schema_version") == formal.STATE_SCHEMA
        and state.get("status") == "POSITIVE_NET_FORMAL_FULL20_PASSED"
        and state.get("candidate_freeze_permitted")
        and not state.get("production_switch_performed")
        and state.get("fallback_action") == "Q0"
        and str(state.get("manifest_sha256") or "") == _sha256(manifest)
        and _resolve_from(FORMAL_STATE, state.get("manifest") or "") == manifest
        and str(state.get("result_sha256") or "") == _sha256(FORMAL_RESULT)
    ):
        raise ValueError("positive-net formal controller authority mismatch")
    if not _valid_acceptance(
        result,
        path=FORMAL_RESULT,
        mode="positive_net_formal",
        scales={5, 10, 20, 30, 50},
    ):
        raise ValueError("positive-net formal full20 acceptance mismatch")
    positive = _load(POSITIVE_REPORT)
    gat = _validate_positive_report(positive, manifest=manifest)
    _validate_manifest_report_binding(_load(manifest), gat)
    return manifest


def _validate_positive_report(
    report: Mapping[str, Any], *, manifest: Path
) -> dict[str, Any]:
    models = [
        dict(row)
        for row in report.get("models") or ()
        if str(row.get("model_kind") or "") == "gat"
    ]
    errors = []
    if len(models) != 1:
        errors.append("gat_report_count_mismatch")
        gat = {}
    else:
        gat = models[0]
    if not bool(
        report.get("schema_version") == e2e.POSITIVE_SCHEMA
        and report.get("gat_positive_net_exact_safe_gate_passed")
        and report.get("development_e2e_authorized")
        and not report.get("minimum_speedup_gate_enabled")
        and report.get("selected_censor_or_unsafe_is_hard_veto")
        and not report.get("production_switch_authorized")
        and str(report.get("fallback_action") or "") == "Q0"
        and str(report.get("evaluation_manifest_sha256") or "")
        == _sha256(manifest)
    ):
        errors.append("positive_net_report_scope_mismatch")
    calibration = dict(gat.get("calibration") or {})
    heldout = dict(gat.get("heldout") or {})
    if not bool(
        gat.get("positive_net_exact_safe_gate_passed")
        and gat.get("all_replays_exact_safe")
        and 0.0 < float(calibration.get("net_geomean_ratio", 1.0)) < 1.0
        and 0.0 < float(heldout.get("net_geomean_ratio", 1.0)) < 1.0
        and int(calibration.get("activation_count") or 0) > 0
        and int(heldout.get("activation_count") or 0) > 0
        and int(calibration.get("selected_right_censored_count", 1)) == 0
        and int(heldout.get("selected_right_censored_count", 1)) == 0
        and int(calibration.get("selected_unsafe_count", 1)) == 0
        and int(heldout.get("selected_unsafe_count", 1)) == 0
        and 0.0 <= float(gat.get("inference_p99_ms", math.inf)) <= 10.0
    ):
        errors.append("positive_net_gat_metrics_mismatch")
    per_scale = dict(heldout.get("per_scale") or {})
    if set(str(key) for key in per_scale) != {"30", "50"} or any(
        not (
            0.0
            < float((per_scale.get(str(scale)) or {}).get(
                "net_geomean_ratio", 0.0
            ))
            <= 1.03
        )
        for scale in (30, 50)
    ):
        errors.append("positive_net_heldout_per_scale_mismatch")
    thresholds = dict(gat.get("thresholds") or {})
    if not bool(
        _finite(thresholds.get("probability_threshold"))
        and 0.0 <= float(thresholds["probability_threshold"]) <= 1.0
        and _finite(thresholds.get("expected_gain_threshold"))
    ):
        errors.append("positive_net_thresholds_invalid")
    eligible_models = [
        dict(row)
        for row in report.get("models") or ()
        if bool(row.get("positive_net_exact_safe_gate_passed"))
    ]
    expected_best = (
        min(
            eligible_models,
            key=lambda row: (
                float((row.get("heldout") or {}).get(
                    "net_geomean_ratio", math.inf
                )),
                str(row.get("model_kind") or ""),
            ),
        ).get("model_kind")
        if eligible_models
        else ""
    )
    if str(report.get("best_positive_net_model_kind") or "") != str(
        expected_best or ""
    ):
        errors.append("positive_net_best_model_mismatch")
    non_gat_ratios = [
        float((row.get("heldout") or {}).get("net_geomean_ratio"))
        for row in eligible_models
        if str(row.get("model_kind") or "") in {"linear", "mlp"}
        and _finite((row.get("heldout") or {}).get("net_geomean_ratio"))
    ]
    best_non_gat = min(non_gat_ratios) if non_gat_ratios else math.inf
    gat_ratio = float(heldout.get("net_geomean_ratio", math.inf))
    gat = {
        **gat,
        "positive_net_best_non_gat_heldout_ratio": best_non_gat,
        "positive_net_gat_vs_best_non_gat_ratio": (
            gat_ratio / best_non_gat
            if math.isfinite(best_non_gat) and best_non_gat > 0.0
            else None
        ),
    }
    if errors:
        raise ValueError(
            "positive-net calibration authority mismatch:"
            + ",".join(sorted(set(errors)))
        )
    return gat


def _validate_manifest_report_binding(
    manifest: Mapping[str, Any], gat: Mapping[str, Any]
) -> None:
    calibration = dict(manifest.get("calibration") or {})
    report_calibration = dict(gat.get("calibration") or {})
    report_heldout = dict(gat.get("heldout") or {})
    thresholds = dict(gat.get("thresholds") or {})
    checks = (
        abs(float(calibration.get("probability_threshold", math.inf))
            - float(thresholds.get("probability_threshold", -math.inf)))
        <= 1.0e-12,
        abs(float(calibration.get("expected_gain_threshold", math.inf))
            - float(thresholds.get("expected_gain_threshold", -math.inf)))
        <= 1.0e-12,
        abs(float(calibration.get("calibration_net_ratio", math.inf))
            - float(report_calibration.get("net_geomean_ratio", -math.inf)))
        <= 1.0e-12,
        abs(float(calibration.get("heldout_net_ratio", math.inf))
            - float(report_heldout.get("net_geomean_ratio", -math.inf)))
        <= 1.0e-12,
    )
    if not all(checks):
        raise ValueError("positive-net manifest/report calibration drift")


def build_positive_net_candidate_payload(
    manifest: Path,
    *,
    tests: Mapping[str, Any],
) -> dict[str, Any]:
    if len(NATIVE_EXTENSIONS) != 1:
        raise ValueError("positive-net finalizer requires one Native extension")
    manifest_payload = _load(manifest)
    e2e._validate_manifest(manifest_payload)
    checkpoint = _bound_path(
        manifest,
        manifest_payload.get("checkpoint_path") or "",
        manifest_payload.get("checkpoint_sha256") or "",
        "checkpoint",
    )
    formal_result = _load(FORMAL_RESULT)
    positive_report = _load(POSITIVE_REPORT)
    gat_report = _validate_positive_report(
        positive_report, manifest=manifest
    )
    frozen_paths = (
        CONFIG, ORACLE_FREEZE, ORACLE, TRAINING, SELECTIVE_EVIDENCE,
        CALIBRATION, POSITIVE_REPORT, MANIFEST, E2E_STATE, E2E_RESULT,
        FORMAL_STATE, FORMAL_RESULT, RUNTIME_SOURCE, MODEL_SOURCE,
        EVIDENCE_SOURCE, AUTHORITY_SOURCE, CALIBRATION_SOURCE,
        ANALYZER_SOURCE, E2E_SOURCE, FORMAL_SOURCE,
        Path(__file__).resolve(), checkpoint, NATIVE_EXTENSIONS[0],
    )
    return {
        "schema_version": CANDIDATE_SCHEMA,
        "status": "FROZEN_EXPERIMENT_CANDIDATE",
        "model_id": "P0V5_QG2_LABEL_STATE_GAT_POSITIVE_NET_V1",
        "frozen_at_local": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "production_default": False,
        "production_switch_performed": False,
        "evaluation_only": True,
        "historical_baselines_unchanged": True,
        "p0v4_changed": False,
        "p0v5_exact_control_changed": False,
        "exact_control_freeze_id": (
            "P0V4_V5_BIDIRECTIONAL_EXACT_FINAL_CANDIDATE"
        ),
        "selected_exact_config": _relative(CONFIG),
        "selected_exact_config_sha256": _sha256(CONFIG),
        "runtime_policy_id": QG2_RUNTIME_POLICY_ID,
        "runtime_implementation_hash": qg2_runtime_implementation_hash(),
        "evaluation_gate_policy": QG2_POSITIVE_NET_EVALUATION_GATE_V1,
        "minimum_speedup_gate_enabled": False,
        "allowed_scales": list(manifest_payload.get("allowed_scales") or ()),
        "scale5_10_20_runtime_bypass": True,
        "fallback_action": "Q0",
        "all_arms_rejected_action": "Q0",
        "ordering_only": True,
        "can_filter": False,
        "can_prune": False,
        "can_change_bound": False,
        "can_certify": False,
        "manifest_path": _relative(manifest),
        "manifest_sha256": _sha256(manifest),
        "checkpoint_path": _relative(checkpoint),
        "checkpoint_sha256": _sha256(checkpoint),
        "calibration_report": _relative(CALIBRATION),
        "calibration_report_sha256": _sha256(CALIBRATION),
        "positive_net_report": _relative(POSITIVE_REPORT),
        "positive_net_report_sha256": _sha256(POSITIVE_REPORT),
        "development_acceptance": _relative(E2E_RESULT),
        "development_acceptance_sha256": _sha256(E2E_RESULT),
        "formal_acceptance": _relative(FORMAL_RESULT),
        "formal_acceptance_sha256": _sha256(FORMAL_RESULT),
        "formal_scale30_50_combined_geomean_wall_ratio": (
            formal_result.get("scale30_50_combined_geomean_wall_ratio")
        ),
        "fresh_process_inference_p99_ms": float(
            gat_report["inference_p99_ms"]
        ),
        "fresh_process_calibration_net_ratio": float(
            gat_report["calibration"]["net_geomean_ratio"]
        ),
        "fresh_process_heldout_net_ratio": float(
            gat_report["heldout"]["net_geomean_ratio"]
        ),
        "positive_net_best_model_kind": str(
            positive_report.get("best_positive_net_model_kind") or ""
        ),
        "positive_net_gat_vs_best_non_gat_ratio": (
            float(gat_report["positive_net_gat_vs_best_non_gat_ratio"])
            if _finite(gat_report["positive_net_gat_vs_best_non_gat_ratio"])
            else None
        ),
        "gat_advantage_claim_authorized": bool(
            _finite(gat_report["positive_net_gat_vs_best_non_gat_ratio"])
            and float(gat_report["positive_net_gat_vs_best_non_gat_ratio"])
            <= 0.98
        ),
        "development_e2e_passed": True,
        "formal_full20_passed": True,
        "regression_and_native_tests": dict(tests),
        "frozen_file_sha256": {
            _relative(path): _sha256(path) for path in frozen_paths
        },
    }


def audit_positive_net_candidate_payload(payload: Mapping[str, Any]) -> list[str]:
    issues = []
    if payload.get("schema_version") != CANDIDATE_SCHEMA:
        issues.append("candidate_schema_mismatch")
    if payload.get("status") != "FROZEN_EXPERIMENT_CANDIDATE":
        issues.append("candidate_status_mismatch")
    if bool(payload.get("production_default")) or bool(
        payload.get("production_switch_performed")
    ):
        issues.append("production_scope_expansion")
    if not bool(payload.get("evaluation_only")):
        issues.append("evaluation_only_scope_missing")
    if str(payload.get("fallback_action") or "") != "Q0" or str(
        payload.get("all_arms_rejected_action") or ""
    ) != "Q0":
        issues.append("literal_q0_fallback_mismatch")
    if not bool(payload.get("ordering_only")):
        issues.append("ordering_only_contract_missing")
    for key in ("can_filter", "can_prune", "can_change_bound", "can_certify"):
        if bool(payload.get(key)):
            issues.append(f"forbidden_authority:{key}")
    if not bool(payload.get("development_e2e_passed")) or not bool(
        payload.get("formal_full20_passed")
    ):
        issues.append("acceptance_evidence_missing")
    if not bool((payload.get("regression_and_native_tests") or {}).get("passed")):
        issues.append("regression_or_native_tests_missing")
    if not bool(
        0.0 <= float(payload.get("fresh_process_inference_p99_ms", math.inf)) <= 10.0
        and 0.0 < float(payload.get("fresh_process_calibration_net_ratio", 1.0)) < 1.0
        and 0.0 < float(payload.get("fresh_process_heldout_net_ratio", 1.0)) < 1.0
        and 0.0 < float(
            payload.get("formal_scale30_50_combined_geomean_wall_ratio", 1.0)
        ) < 1.0
    ):
        issues.append("positive_net_performance_evidence_mismatch")
    for relative, expected in dict(payload.get("frozen_file_sha256") or {}).items():
        path = _resolve(relative)
        if not path.is_file() or _sha256(path) != str(expected):
            issues.append(f"frozen_file_drift:{relative}")
    for path_key, hash_key in (
        ("selected_exact_config", "selected_exact_config_sha256"),
        ("manifest_path", "manifest_sha256"),
        ("checkpoint_path", "checkpoint_sha256"),
        ("calibration_report", "calibration_report_sha256"),
        ("positive_net_report", "positive_net_report_sha256"),
        ("development_acceptance", "development_acceptance_sha256"),
        ("formal_acceptance", "formal_acceptance_sha256"),
    ):
        path = _resolve(payload.get(path_key) or "")
        if not path.is_file() or _sha256(path) != str(payload.get(hash_key) or ""):
            issues.append(f"candidate_binding_mismatch:{path_key}")
    positive_path = _resolve(payload.get("positive_net_report") or "")
    manifest_path = _resolve(payload.get("manifest_path") or "")
    if positive_path.is_file() and manifest_path.is_file():
        try:
            gat = _validate_positive_report(
                _load(positive_path), manifest=manifest_path
            )
            if any(
                abs(float(payload.get(candidate_key, math.inf)) - float(expected))
                > 1.0e-12
                for candidate_key, expected in (
                    ("fresh_process_inference_p99_ms", gat["inference_p99_ms"]),
                    (
                        "fresh_process_calibration_net_ratio",
                        gat["calibration"]["net_geomean_ratio"],
                    ),
                    (
                        "fresh_process_heldout_net_ratio",
                        gat["heldout"]["net_geomean_ratio"],
                    ),
                )
            ):
                issues.append("positive_net_candidate_metric_binding_mismatch")
            expected_raw = gat["positive_net_gat_vs_best_non_gat_ratio"]
            observed_raw = payload.get(
                "positive_net_gat_vs_best_non_gat_ratio"
            )
            ratios_match = bool(
                (expected_raw is None and observed_raw is None)
                or (
                    _finite(expected_raw)
                    and _finite(observed_raw)
                    and abs(float(observed_raw) - float(expected_raw))
                    <= 1.0e-12
                )
            )
            expected_claim = bool(
                _finite(expected_raw) and float(expected_raw) <= 0.98
            )
            if not (
                ratios_match
                and bool(payload.get("gat_advantage_claim_authorized"))
                == expected_claim
            ):
                issues.append("gat_advantage_claim_binding_mismatch")
        except Exception as exc:
            issues.append(f"positive_net_report_invalid:{type(exc).__name__}:{exc}")
    return sorted(set(issues))


def _valid_acceptance(
    payload: Mapping[str, Any],
    *, path: Path, mode: str, scales: set[int],
) -> bool:
    if not bool(
        path.is_file()
        and payload.get("schema_version") == formal.E2E_ACCEPTANCE_SCHEMA
        and payload.get("mode") == mode
        and payload.get("passed")
        and int(payload.get("violation_count") or 0) == 0
        and {int(value) for value in (payload.get("by_scale") or {})} == scales
    ):
        return False
    by_scale = dict(payload.get("by_scale") or {})
    high_scale_actions = 0
    for scale in scales:
        row = dict(by_scale.get(str(scale)) or {})
        if int(row.get("guided_exact_count") or 0) < int(
            row.get("control_exact_count") or 0
        ):
            return False
        ratio = row.get("paired_geomean_wall_ratio")
        if ratio is None:
            return False
        if scale in {5, 10, 20}:
            if (
                float(ratio) > 1.01
                or int(row.get("guided_exact_count") or 0) != 20
                or int(row.get("guided_qg2_inference_event_count") or 0) != 0
            ):
                return False
        else:
            if float(ratio) > 1.03:
                return False
            high_scale_actions += int(row.get("guided_qg2_action_count") or 0)
    if high_scale_actions <= 0:
        return False
    combined = payload.get("scale30_50_combined_geomean_wall_ratio")
    if combined is None or not (0.0 < float(combined) < 1.0):
        return False
    if any(
        not bool(row.get("objective_match"))
        or not bool((row.get("control") or {}).get("redlines_zero"))
        or not bool((row.get("guided") or {}).get("redlines_zero"))
        for row in payload.get("pairs") or ()
    ):
        return False
    for prefix in ("control", "guided"):
        root = _resolve_from(path, payload.get(f"{prefix}_root") or "")
        if (
            not root.is_dir()
            or formal.base._acceptance_artifact_hash(root)
            != str(payload.get(f"{prefix}_root_hash") or "")
        ):
            return False
    return True


def _run_tests() -> dict[str, Any]:
    commands = (
        [
            sys.executable, "-m", "pytest", "-q",
            *(str(path) for path in sorted(ROOT.glob("tests/test_p0v5_qg2_*.py"))),
        ],
        ["ctest", "--test-dir", str(BUILD), "--output-on-failure"],
    )
    rows = []
    for command in commands:
        completed = subprocess.run(
            command, cwd=ROOT, text=True, capture_output=True, check=False
        )
        rows.append({
            "command": command,
            "returncode": int(completed.returncode),
            "stdout_tail": completed.stdout[-4000:],
            "stderr_tail": completed.stderr[-4000:],
        })
    return {
        "passed": all(row["returncode"] == 0 for row in rows),
        "commands": rows,
    }


def _write_audit(
    complete: bool, issues: list[str], tests: Mapping[str, Any]
) -> None:
    _write(AUDIT, {
        "schema_version": AUDIT_SCHEMA,
        "objective": "P0V5 Proof-Tail GAT V2 Q0-Anchored Label-State Guidance",
        "complete": bool(complete),
        "issue_count": len(issues),
        "issues": list(issues),
        "candidate": str(CANDIDATE) if CANDIDATE.is_file() else None,
        "candidate_sha256": _sha256(CANDIDATE) if CANDIDATE.is_file() else None,
        "regression_and_native_tests": dict(tests),
        "production_switch_performed": False,
        "fallback_action": "Q0",
    })


def _bound_path(
    source: Path, raw: str | Path, expected: str, label: str
) -> Path:
    path = _resolve_from(source, raw)
    if not path.is_file() or _sha256(path) != str(expected):
        raise ValueError(f"positive-net candidate {label} binding mismatch")
    return path


def _matching_formal_controller(pid: int) -> bool:
    try:
        command = Path(f"/proc/{int(pid)}/cmdline").read_bytes().replace(
            b"\0", b" "
        ).decode("utf-8", errors="replace")
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return "run_p0v5_qg2_positive_net_formal_after_e2e.py" in command


def _validate_freeze() -> None:
    payload = _load(FREEZE)
    if payload.get("schema_version") != FREEZE_SCHEMA:
        raise ValueError("positive-net finalizer freeze schema mismatch")
    if (
        not bool(payload.get("development_only"))
        or bool(payload.get("production_switch_authorized"))
        or str(payload.get("fallback_action") or "") != "Q0"
        or not bool(payload.get("formal_full20_required"))
    ):
        raise ValueError("positive-net finalizer freeze safety mismatch")
    for raw_path, expected in dict(payload.get("frozen_file_sha256") or {}).items():
        path = _resolve(raw_path)
        if not path.is_file() or _sha256(path) != str(expected):
            raise ValueError(f"positive-net finalizer frozen drift:{path}")


def _resolve_from(source: Path, value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (
        source.parent / path
    ).resolve()


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def _state(status: str, **extra: Any) -> None:
    _write(STATE, {
        "schema_version": STATE_SCHEMA,
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": str(status),
        **extra,
    })


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


if __name__ == "__main__":
    raise SystemExit(main())

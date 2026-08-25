#!/usr/bin/env python3
"""Completion audit for the active QG2 action-surface-v2 experiment.

This audit intentionally does not reuse the historical clean-v2 output paths.
It accepts either the original strict Oracle training authority or the frozen
relaxed *training-only* authority, but every deployment, heldout, E2E, formal
full20, and candidate-freeze requirement remains unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
BUILD = ROOT / "build/native-spprc-bidirectional-feasibility-v1"

ORACLE_FREEZE = RUN_ROOT / "qg2_action_surface_v2_oracle_execution_freeze.json"
POST_ORACLE_RUNTIME_FREEZE = (
    RUN_ROOT / "qg2_post_oracle_selective_runtime_integration_freeze.json"
)
POSITIVE_NET_RUNTIME_FREEZE = (
    RUN_ROOT / "qg2_positive_net_evaluation_runtime_integration_freeze.json"
)
STRICT_POST_FREEZE = RUN_ROOT / "qg2_action_surface_v2_post_oracle_freeze.json"
RELAXED_TRAINING_FREEZE = (
    RUN_ROOT / "qg2_action_surface_v2_relaxed_training_freeze.json"
)
ORACLE_OUTPUT_DIR = RUN_ROOT / "oracle_qg2_action_surface_v2_stage1"
ORACLE_SUMMARY = RUN_ROOT / "oracle_qg2_action_surface_v2_stage1.json"
RELAXED_GATE = RUN_ROOT / "qg2_action_surface_v2_relaxed_training_gate.json"

STRICT_TRAINING = RUN_ROOT / "training_qg2_action_surface_v2/training_report.json"
RELAXED_TRAINING = (
    RUN_ROOT / "training_qg2_action_surface_v2_relaxed/training_report.json"
)
STRICT_CALIBRATION = (
    RUN_ROOT / "calibration_qg2_action_surface_v2/calibration_report.json"
)
RELAXED_CALIBRATION = (
    RUN_ROOT
    / "calibration_qg2_action_surface_v2_relaxed/calibration_report.json"
)
SUPPLEMENTAL_CALIBRATION_FREEZE = (
    RUN_ROOT / "qg2_supplemental_calibration_controller_freeze.json"
)
SUPPLEMENTAL_CALIBRATION = (
    RUN_ROOT
    / "calibration_qg2_action_surface_v2_supplemental/calibration_report.json"
)
SUPPLEMENTAL_CALIBRATION_BINDING = (
    RUN_ROOT
    / "calibration_qg2_action_surface_v2_supplemental/"
    "supplemental_calibration_binding.json"
)
SUPPLEMENTAL_E2E_FREEZE = (
    RUN_ROOT / "qg2_supplemental_e2e_controller_freeze.json"
)
SUPPLEMENTAL_E2E_STATE = (
    RUN_ROOT / "qg2_supplemental_e2e_controller_state.json"
)
SUPPLEMENTAL_FORMAL_FREEZE = (
    RUN_ROOT / "qg2_supplemental_formal_controller_freeze.json"
)
SUPPLEMENTAL_FORMAL_STATE = (
    RUN_ROOT / "qg2_supplemental_formal_controller_state.json"
)
STANDARD_E2E_STATE = RUN_ROOT / "qg2_action_surface_v2_e2e_controller_state.json"
STANDARD_FORMAL_STATE = (
    RUN_ROOT / "qg2_action_surface_v2_formal_controller_state.json"
)
E2E_FREEZE = RUN_ROOT / "qg2_action_surface_v2_e2e_controller_freeze.json"
FORMAL_FREEZE = RUN_ROOT / "qg2_action_surface_v2_formal_controller_freeze.json"
E2E_ACCEPTANCE = (
    RUN_ROOT / "e2e_development_acceptance_qg2_action_surface_v2.json"
)
FORMAL_ACCEPTANCE = (
    RUN_ROOT / "formal_full20_acceptance_qg2_action_surface_v2.json"
)
CANDIDATE_FREEZE = (
    RUN_ROOT
    / "P0V5_QG2_ACTION_SURFACE_V2_LABEL_STATE_GAT_candidate_freeze.json"
)

ORACLE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
SUPERVISION_SCHEMA = "lunar_ice_bpc.p0v5_qg2_action_reachable_supervision.v2"
ACTION_SURFACE = "same_terminal_class_and_reduced_cost_bucket.v1"
TRAINING_SCHEMA = "lunar_ice_bpc.p0v5_qg2_model_comparison.v3"
CALIBRATION_SCHEMA = "lunar_ice_bpc.p0v5_qg2_fresh_process_calibration.v4"
BUCKETS = (1.0e-4, 3.0e-4, 1.0e-3)
RELAXED_THRESHOLDS = {
    "minimum_determined_contexts_per_scale": 20,
    "minimum_gain_5pct_contexts_per_scale": 5,
    "minimum_positive_instances_per_scale": 5,
    "maximum_paired_geomean_ratio": 0.95,
    "maximum_instance_bootstrap_95_upper": 0.98,
    "maximum_instance_saved_wall_fraction": 0.35,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default=str(
            RUN_ROOT / "p0v5_qg2_action_surface_v2_completion_audit.json"
        ),
    )
    parser.add_argument("--run-tests", action="store_true")
    parser.add_argument("--pre-final-freeze", action="store_true")
    args = parser.parse_args()

    checks = {
        "action_surface_oracle_execution_freeze": (
            _audit_oracle_execution_provenance()
        ),
        "strict_post_oracle_controller_freeze": _audit_hash_freeze(
            STRICT_POST_FREEZE,
            {"lunar_ice_bpc.p0v5_qg2_post_oracle_controller_freeze.v3"},
            "strict Oracle-pass-only training controller freeze",
        ),
        "relaxed_training_only_freeze": _audit_relaxed_freeze(),
        "action_surface_contract": _audit_action_surface_contract(),
        "bounded_oracle": _audit_oracle(),
        "linear_mlp_gat_training": _audit_training(),
        "fresh_process_calibration": _audit_calibration(),
        "heldout_snapshot_replay": _audit_heldout(),
        "supplemental_calibration_binding": (
            _audit_supplemental_calibration_binding()
        ),
        "supplemental_e2e_formal_binding": (
            _audit_supplemental_e2e_formal_binding()
        ),
        "development_e2e_controller_freeze": _audit_hash_freeze(
            E2E_FREEZE,
            {"lunar_ice_bpc.p0v5_qg2_e2e_controller_freeze.v1"},
            "calibration-pass-only action-surface-v2 E2E freeze",
        ),
        "development_scale30_50_e2e": _audit_acceptance(
            E2E_ACCEPTANCE,
            mode="development",
            scales={30, 50},
        ),
        "formal_full20_controller_freeze": _audit_hash_freeze(
            FORMAL_FREEZE,
            {"lunar_ice_bpc.p0v5_qg2_formal_controller_freeze.v1"},
            "development-E2E-pass-only action-surface-v2 formal freeze",
        ),
        "formal_scale5_to_50_full20": _audit_acceptance(
            FORMAL_ACCEPTANCE,
            mode="formal",
            scales={5, 10, 20, 30, 50},
        ),
    }
    if not args.pre_final_freeze:
        checks["independent_experiment_candidate_freeze"] = (
            _audit_candidate_freeze()
        )
    checks["automated_regression_tests"] = (
        _run_tests()
        if args.run_tests
        else _check("INCOMPLETE", "not executed by this audit invocation")
    )

    complete = all(row["status"] == "PASS" for row in checks.values())
    payload = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_action_surface_v2_completion_audit.v1"
        ),
        "objective": "P0V5 QG2 Q0-Anchored Label-State Guidance",
        "track": "action_surface_v2",
        "complete": complete,
        "checks": checks,
        "required_check_count": len(checks),
        "passed_check_count": sum(
            row["status"] == "PASS" for row in checks.values()
        ),
        "failed_check_count": sum(
            row["status"] == "FAIL" for row in checks.values()
        ),
        "incomplete_check_count": sum(
            row["status"] == "INCOMPLETE" for row in checks.values()
        ),
        "completion_rule": "all_required_checks_must_pass",
        "pre_final_freeze": bool(args.pre_final_freeze),
    }
    output = _resolve(args.output)
    _write(output, payload)
    print(json.dumps({
        "complete": complete,
        "passed": payload["passed_check_count"],
        "failed": payload["failed_check_count"],
        "incomplete": payload["incomplete_check_count"],
        "output": str(output),
    }, sort_keys=True))
    return 0 if complete else 2


def _audit_hash_freeze(
    path: Path,
    schemas: set[str],
    note: str,
) -> dict:
    if not path.is_file():
        return _check("INCOMPLETE", f"{note} missing", freeze=str(path))
    payload = _load(path)
    issues = []
    if str(payload.get("schema_version") or "") not in schemas:
        issues.append("schema_mismatch")
    if not bool(payload.get("development_only")) or bool(
        payload.get("deployable")
    ):
        issues.append("development_safety_mismatch")
    for raw_path, expected in dict(
        payload.get("frozen_file_sha256") or {}
    ).items():
        target = _resolve(raw_path)
        if not target.is_file() or _sha256(target) != str(expected):
            issues.append(f"drift:{raw_path}")
    return _check(
        "FAIL" if issues else "PASS",
        note,
        freeze=str(path),
        issues=issues,
    )


def _audit_oracle_execution_provenance() -> dict:
    """Preserve historical Oracle bytes while binding post-Oracle runtime.

    The bounded Oracle intentionally froze the runtime used to create its
    traces.  After all 219 matched replicates were emitted, the runtime gained
    the selective-evidence validator required for model evaluation.  The old
    freeze must not be rewritten, so this audit permits exactly that one
    attested source drift and requires a second hash-clean freeze for the
    current runtime.  Any other drift remains a hard failure.
    """

    historical = _audit_hash_freeze(
        ORACLE_FREEZE,
        {"lunar_ice_bpc.p0v5_qg2_oracle_execution_freeze.v2"},
        "action-reachable Oracle execution freeze",
    )
    if historical["status"] == "PASS":
        return historical
    allowed_path = (
        "src/lunar_ice_bpc/guidance/proof_queue_label_state_runtime.py"
    )
    if set(historical["evidence"].get("issues") or ()) != {
        f"drift:{allowed_path}"
    }:
        return historical
    if not POST_ORACLE_RUNTIME_FREEZE.is_file() or not ORACLE_SUMMARY.is_file():
        return historical

    attestation = _load(POST_ORACLE_RUNTIME_FREEZE)
    oracle = _load(ORACLE_SUMMARY)
    original = _load(ORACLE_FREEZE)
    issues = []
    if attestation.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_post_oracle_runtime_integration_freeze.v1"
    ):
        issues.append("post_oracle_runtime_freeze_schema_mismatch")
    if not bool(attestation.get("development_only")) or bool(
        attestation.get("deployable")
    ):
        issues.append("post_oracle_runtime_freeze_safety_mismatch")
    if not bool(attestation.get("oracle_completed_before_runtime_integration")):
        issues.append("post_oracle_ordering_not_attested")
    if int(attestation.get("oracle_replicate_pair_count") or 0) != 219:
        issues.append("oracle_replicate_pair_count_mismatch")
    if len(oracle.get("replicate_rows") or ()) != 219:
        issues.append("oracle_summary_replicate_count_mismatch")
    if not bool((oracle.get("oracle_gate") or {}).get("all_exact_safe")):
        issues.append("oracle_summary_not_exact_safe")
    if str(attestation.get("oracle_execution_freeze_sha256") or "") != (
        _sha256(ORACLE_FREEZE)
    ):
        issues.append("post_oracle_execution_freeze_hash_mismatch")
    if str(attestation.get("oracle_summary_sha256") or "") != (
        _sha256(ORACLE_SUMMARY)
    ):
        issues.append("post_oracle_summary_hash_mismatch")
    if str(oracle.get("execution_freeze_sha256") or "") != (
        _sha256(ORACLE_FREEZE)
    ):
        issues.append("oracle_summary_execution_freeze_binding_mismatch")
    original_runtime_hash = str(
        (original.get("frozen_file_sha256") or {}).get(allowed_path) or ""
    )
    if str(attestation.get("historical_oracle_runtime_sha256") or "") != (
        original_runtime_hash
    ):
        issues.append("historical_oracle_runtime_hash_mismatch")
    if set(attestation.get("allowed_historical_freeze_drift") or ()) != {
        allowed_path
    }:
        issues.append("post_oracle_allowed_drift_scope_mismatch")
    if str(attestation.get("fallback_action") or "") != "Q0" or not bool(
        attestation.get("ordering_only")
    ):
        issues.append("post_oracle_runtime_scope_mismatch")
    if any(
        bool(attestation.get(field))
        for field in ("can_filter", "can_prune", "can_change_bound", "can_certify")
    ):
        issues.append("post_oracle_exact_authority_expansion")
    post_runtime_drift = []
    for raw_path, expected in dict(
        attestation.get("frozen_file_sha256") or {}
    ).items():
        target = _resolve(raw_path)
        if not target.is_file() or _sha256(target) != str(expected):
            post_runtime_drift.append(f"post_oracle_drift:{raw_path}")
    expected_second_stage_drift = {f"post_oracle_drift:{allowed_path}"}
    if set(post_runtime_drift) == expected_second_stage_drift:
        issues.extend(_audit_positive_net_runtime_freeze(allowed_path))
    elif post_runtime_drift:
        issues.extend(post_runtime_drift)

    return _check(
        "FAIL" if issues else "PASS",
        "historical Oracle provenance plus post-Oracle selective runtime freeze",
        oracle_freeze=str(ORACLE_FREEZE),
        post_oracle_runtime_freeze=str(POST_ORACLE_RUNTIME_FREEZE),
        positive_net_runtime_freeze=str(POSITIVE_NET_RUNTIME_FREEZE),
        historical_drift=[allowed_path],
        issues=issues,
    )


def _audit_positive_net_runtime_freeze(allowed_path: str) -> list[str]:
    """Bind the later evaluation-only gate without rewriting prior freezes."""

    if not POSITIVE_NET_RUNTIME_FREEZE.is_file():
        return ["positive_net_runtime_freeze_missing"]
    payload = _load(POSITIVE_NET_RUNTIME_FREEZE)
    issues = []
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_positive_net_evaluation_runtime_freeze.v1"
    ):
        issues.append("positive_net_runtime_freeze_schema_mismatch")
    if not bool(payload.get("development_only")) or bool(
        payload.get("deployable")
    ) or bool(payload.get("deployment_authorized")) or bool(
        payload.get("production_switch_authorized")
    ):
        issues.append("positive_net_runtime_freeze_safety_mismatch")
    if not bool(payload.get("development_e2e_only")):
        issues.append("positive_net_runtime_scope_mismatch")
    if str(payload.get("evaluation_gate_policy") or "") != (
        "positive_net_exact_safe.v1"
    ):
        issues.append("positive_net_gate_policy_mismatch")
    if bool(payload.get("minimum_speedup_gate_enabled")) or bool(
        payload.get("harmful_rate_confidence_gate_blocks_e2e")
    ):
        issues.append("positive_net_report_only_gate_mismatch")
    if not all(
        bool(payload.get(field))
        for field in (
            "positive_net_required_on_calibration_and_heldout",
            "right_censored_selected_action_is_veto",
            "selected_unsafe_action_is_veto",
            "ordering_only",
        )
    ):
        issues.append("positive_net_exact_safe_contract_missing")
    if str(payload.get("fallback_action") or "") != "Q0" or str(
        payload.get("all_arms_rejected_action") or ""
    ) != "Q0":
        issues.append("positive_net_literal_q0_fallback_mismatch")
    if any(
        bool(payload.get(field))
        for field in ("can_filter", "can_prune", "can_change_bound", "can_certify")
    ):
        issues.append("positive_net_exact_authority_expansion")
    if set(payload.get("allowed_prior_runtime_freeze_drift") or ()) != {
        allowed_path
    }:
        issues.append("positive_net_allowed_drift_scope_mismatch")
    if str(payload.get("prior_post_oracle_runtime_freeze_sha256") or "") != (
        _sha256(POST_ORACLE_RUNTIME_FREEZE)
    ):
        issues.append("positive_net_prior_freeze_hash_mismatch")
    try:
        from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (
            qg2_runtime_implementation_hash,
        )

        if str(payload.get("current_runtime_implementation_hash") or "") != (
            qg2_runtime_implementation_hash()
        ):
            issues.append("positive_net_runtime_implementation_hash_mismatch")
    except Exception as exc:
        issues.append(
            f"positive_net_runtime_hash_exception:{type(exc).__name__}"
        )
    for raw_path, expected in dict(payload.get("frozen_file_sha256") or {}).items():
        target = _resolve(raw_path)
        if not target.is_file() or _sha256(target) != str(expected):
            issues.append(f"positive_net_runtime_drift:{raw_path}")
    return issues


def _audit_relaxed_freeze() -> dict:
    result = _audit_hash_freeze(
        RELAXED_TRAINING_FREEZE,
        {"lunar_ice_bpc.p0v5_qg2_relaxed_training_freeze.v1"},
        "exploratory-training-only relaxed gate freeze",
    )
    if result["status"] != "PASS":
        return result
    payload = _load(RELAXED_TRAINING_FREEZE)
    issues = []
    if not bool(payload.get("deployment_gate_unchanged")):
        issues.append("deployment_gate_was_weakened")
    if not bool(payload.get("paper_claim_gate_unchanged")):
        issues.append("paper_claim_gate_was_weakened")
    if int(payload.get("minimum_strict_calibration_contexts") or 0) != 52:
        issues.append("strict_calibration_sample_gate_drift")
    if str(payload.get("oracle_execution_freeze_sha256") or "") != (
        _sha256(ORACLE_FREEZE) if ORACLE_FREEZE.is_file() else ""
    ):
        issues.append("oracle_freeze_binding_mismatch")
    result["status"] = "FAIL" if issues else "PASS"
    result["evidence"]["issues"].extend(issues)
    return result


def _audit_action_surface_contract() -> dict:
    if not ORACLE_FREEZE.is_file():
        return _check("INCOMPLETE", "Oracle execution freeze missing")
    payload = _load(ORACLE_FREEZE)
    valid = bool(
        payload.get("supervision_schema_version") == SUPERVISION_SCHEMA
        and payload.get("queue_action_surface") == ACTION_SURFACE
        and payload.get("oracle_schema") == ORACLE_SCHEMA
        and payload.get("training_before_oracle_pass") is False
        and payload.get("inherited_guidance_or_snapshot_environment_permitted")
        is False
        and int(payload.get("maximum_oracle_contexts") or 0) == 300
        and int(payload.get("maximum_oracle_contexts_per_scale") or 0) == 150
    )
    return _check(
        "PASS" if valid else "FAIL",
        "same-terminal-class and same-RC-bucket reachable action contract",
        supervision_schema_version=payload.get("supervision_schema_version"),
        queue_action_surface=payload.get("queue_action_surface"),
        preflight_coverage=payload.get("preflight_coverage"),
    )


def _audit_oracle() -> dict:
    if not ORACLE_SUMMARY.is_file():
        return _check(
            "INCOMPLETE",
            "bounded Oracle is still running or has not emitted its summary",
            summary=str(ORACLE_SUMMARY),
            progress=_oracle_progress(),
        )
    oracle = _load(ORACLE_SUMMARY)
    contract = bool(
        oracle.get("schema_version") == ORACLE_SCHEMA
        and oracle.get("supervision_schema_version") == SUPERVISION_SCHEMA
        and oracle.get("queue_action_surface") == ACTION_SURFACE
        and str(oracle.get("execution_freeze_sha256") or "")
        == _sha256(ORACLE_FREEZE)
        and bool(oracle.get("development_only"))
        and not bool(oracle.get("deployable"))
    )
    strict = bool(
        (oracle.get("oracle_gate") or {}).get("passed")
        and oracle.get("training_permitted")
    )
    relaxed = _relaxed_training_authorized(oracle)
    status = "PASS" if contract and (strict or relaxed) else "FAIL"
    return _check(
        status,
        "bounded cross-scale QO2 Oracle training authority",
        summary=str(ORACLE_SUMMARY),
        authority=("strict" if strict else "relaxed" if relaxed else "none"),
        strict_gate=oracle.get("oracle_gate"),
        progress=_oracle_progress(),
    )


def _relaxed_training_authorized(oracle: dict) -> bool:
    if not RELAXED_GATE.is_file():
        return False
    gate = _load(RELAXED_GATE)
    return bool(
        gate.get("schema_version")
        == "lunar_ice_bpc.p0v5_qg2_relaxed_training_gate.v1"
        and gate.get("supervision_schema_version") == SUPERVISION_SCHEMA
        and gate.get("queue_action_surface") == ACTION_SURFACE
        and str(gate.get("oracle_summary_sha256") or "")
        == _sha256(ORACLE_SUMMARY)
        and bool((gate.get("gate") or {}).get("passed"))
        and bool(gate.get("training_authorized"))
        and not bool(gate.get("deployment_authorized"))
        and not bool(gate.get("paper_claim_authorized"))
        and oracle.get("schema_version") == ORACLE_SCHEMA
    )


def _oracle_progress() -> dict:
    directories = [
        path for path in ORACLE_OUTPUT_DIR.iterdir() if path.is_dir()
    ] if ORACLE_OUTPUT_DIR.is_dir() else []
    trace_count = sum((path / "q0_trace.json").is_file() for path in directories)
    potential_count = sum(
        (path / "qo2_leaked_potential.json").is_file()
        for path in directories
    )
    full_count = sum(
        (path / "qo2_0.001_initial.json").is_file()
        for path in directories
    )
    by_scale = {}
    for scale in (30, 50):
        selected = [path for path in directories if path.name.startswith(f"{scale}_")]
        by_scale[str(scale)] = {
            "started_context_count": len(selected),
            "q0_trace_count": sum(
                (path / "q0_trace.json").is_file() for path in selected
            ),
            "complete_future_trace_count": sum(
                (path / "qo2_leaked_potential.json").is_file()
                for path in selected
            ),
            "full_initial_arm_context_count": sum(
                (path / "qo2_0.001_initial.json").is_file()
                for path in selected
            ),
        }
    metrics = _live_initial_metrics(directories)
    return {
        "started_context_count": len(directories),
        "q0_trace_count": trace_count,
        "complete_future_trace_count": potential_count,
        "right_censored_trace_count": max(0, trace_count - potential_count),
        "full_initial_arm_context_count": full_count,
        "by_scale": by_scale,
        "initial_screen_metrics_by_bucket": metrics["by_bucket"],
        "action_reachable_training_pair_count": metrics[
            "action_reachable_training_pair_count"
        ],
        "relaxed_gate_live_diagnostic": metrics[
            "relaxed_gate_live_diagnostic"
        ],
        "training_authorized": False,
        "role": "live_progress_only_not_oracle_gate_evidence",
    }


def _live_initial_metrics(directories: list[Path]) -> dict:
    required = (
        "q0_initial.json",
        "qd1_initial.json",
        "qb1_initial.json",
        "random_170141_initial.json",
        "random_61635_initial.json",
        "random_91267_initial.json",
        "qo2_0.0001_initial.json",
        "qo2_0.0003_initial.json",
        "qo2_0.001_initial.json",
        "qo2_leaked_potential.json",
    )
    complete = [
        path for path in directories
        if all((path / name).is_file() for name in required)
    ]
    pairs = 0
    for path in complete:
        potential = _load(path / "qo2_leaked_potential.json")
        pairs += int(potential.get("training_pair_count") or 0)

    by_bucket = {}
    rows_by_bucket: dict[str, list[dict]] = {}
    for bucket in BUCKETS:
        key = str(bucket)
        rows = []
        for path in complete:
            q0 = _load(path / "q0_initial.json")
            arm = _load(path / f"qo2_{bucket:g}_initial.json")
            budget = float(q0.get("requested_wall_time_limit_sec") or 0.0)
            q0_wall = _effective_wall(q0, budget)
            arm_wall = _effective_wall(arm, budget)
            rows.append({
                "scale": int(q0.get("scale") or 0),
                "instance_hash": str(q0.get("instance_content_hash") or ""),
                "ratio": arm_wall / q0_wall,
                "saved_wall_sec": max(0.0, q0_wall - arm_wall),
                "outcome_determined": _matched_milestone(q0, arm),
                "all_safe": _ordering_safe(q0, arm),
                "milestone_kind": str(q0.get("milestone_kind") or ""),
            })
        rows_by_bucket[key] = rows
        by_bucket[key] = _bucket_metrics(rows)

    preferred_key = str(1.0e-3)
    preferred = rows_by_bucket.get(preferred_key, [])
    saved_by_instance: dict[str, float] = {}
    for row in preferred:
        if row["outcome_determined"]:
            instance = row["instance_hash"]
            saved_by_instance[instance] = (
                saved_by_instance.get(instance, 0.0)
                + float(row["saved_wall_sec"])
            )
    total_saved = sum(saved_by_instance.values())
    max_fraction = (
        max(saved_by_instance.values(), default=0.0) / total_saved
        if total_saved > 0.0
        else 1.0
    )
    per_scale = {
        str(scale): by_bucket[preferred_key]["by_scale"][str(scale)]
        for scale in (30, 50)
    }
    relaxed_ready = bool(
        preferred
        and all(row["all_safe"] for row in preferred)
        and all(
            per_scale[str(scale)]["determined_context_count"]
            >= RELAXED_THRESHOLDS["minimum_determined_contexts_per_scale"]
            and per_scale[str(scale)]["gain_5pct_context_count"]
            >= RELAXED_THRESHOLDS["minimum_gain_5pct_contexts_per_scale"]
            and per_scale[str(scale)]["gain_5pct_instance_count"]
            >= RELAXED_THRESHOLDS["minimum_positive_instances_per_scale"]
            and per_scale[str(scale)]["paired_geomean_ratio"] is not None
            and per_scale[str(scale)]["paired_geomean_ratio"]
            <= RELAXED_THRESHOLDS["maximum_paired_geomean_ratio"]
            and per_scale[str(scale)]["instance_bootstrap_95_upper"] is not None
            and per_scale[str(scale)]["instance_bootstrap_95_upper"]
            <= RELAXED_THRESHOLDS["maximum_instance_bootstrap_95_upper"]
            for scale in (30, 50)
        )
        and max_fraction
        <= RELAXED_THRESHOLDS["maximum_instance_saved_wall_fraction"]
    )
    return {
        "by_bucket": by_bucket,
        "action_reachable_training_pair_count": pairs,
        "relaxed_gate_live_diagnostic": {
            "bucket_width": 1.0e-3,
            "thresholds": dict(RELAXED_THRESHOLDS),
            "by_scale": per_scale,
            "maximum_instance_saved_wall_fraction": max_fraction,
            "would_meet_numeric_gate_on_current_initial_screens": relaxed_ready,
            "training_authorized": False,
            "reason": "formal_oracle_summary_and_frozen_gate_are_authoritative",
        },
    }


def _bucket_metrics(rows: list[dict]) -> dict:
    result = {
        "context_count": len(rows),
        "all_exact_safe": bool(rows) and all(row["all_safe"] for row in rows),
        "by_scale": {},
    }
    for scale in (30, 50):
        selected = [row for row in rows if row["scale"] == scale]
        determined = [row for row in selected if row["outcome_determined"]]
        gain = [row for row in determined if float(row["ratio"]) <= 0.95]
        result["by_scale"][str(scale)] = {
            "context_count": len(selected),
            "determined_context_count": len(determined),
            "gain_5pct_context_count": len(gain),
            "gain_5pct_instance_count": len({
                row["instance_hash"] for row in gain
            }),
            "positive_context_count": sum(
                float(row["ratio"]) < 1.0 for row in determined
            ),
            "paired_geomean_ratio": _geomean_or_none([
                float(row["ratio"]) for row in determined
            ]),
            "instance_bootstrap_95_upper": _instance_bootstrap_upper(
                determined
            ),
            "milestone_counts": {
                kind: sum(row["milestone_kind"] == kind for row in determined)
                for kind in (
                    "ADMISSION_BATCH_READY",
                    "EXACT_PROOF_COMPLETION",
                )
            },
        }
    return result


def _matched_milestone(control: dict, arm: dict) -> bool:
    left = str(control.get("milestone_kind") or "")
    right = str(arm.get("milestone_kind") or "")
    return bool(
        control.get("milestone_reached")
        and arm.get("milestone_reached")
        and left == right
        and left in {"ADMISSION_BATCH_READY", "EXACT_PROOF_COMPLETION"}
    )


def _ordering_safe(control: dict, arm: dict) -> bool:
    left = dict(control.get("proof_telemetry") or {})
    right = dict(arm.get("proof_telemetry") or {})
    universe = all(
        left.get(key) == right.get(key)
        for key in (
            "legal_action_universe_hash_before_sort",
            "legal_arc_universe_hash_before_sort",
        )
    )
    no_drop = all(
        int(right.get(key) or 0) == 0
        for key in (
            "guidance_filter_count",
            "guidance_arc_drop_count",
            "guidance_label_drop_count",
            "guidance_branch_pair_drop_count",
        )
    )
    exact = True
    if control.get("search_exhaustive") and arm.get("search_exhaustive"):
        exact = _exact_match(control, arm)
    return bool(
        universe and no_drop and not arm.get("labels_dropped") and exact
    )


def _exact_match(left: dict, right: dict) -> bool:
    if (
        left.get("global_min_rc") is not None
        and right.get("global_min_rc") is not None
    ):
        return abs(
            float(left["global_min_rc"]) - float(right["global_min_rc"])
        ) <= 2.0e-6
    if (
        left.get("proved_no_rc_below") is not None
        and right.get("proved_no_rc_below") is not None
    ):
        return abs(
            float(left["proved_no_rc_below"])
            - float(right["proved_no_rc_below"])
        ) <= 1.0e-12
    return False


def _effective_wall(row: dict, budget: float) -> float:
    measured = max(
        1.0e-9,
        float(
            row.get("admission_milestone_wall_sec")
            or row.get("milestone_wall_sec")
            or row.get("total_fresh_process_wall_sec")
            or 0.0
        ),
    )
    return measured if row.get("milestone_reached") else max(
        measured,
        float(budget),
    )


def _instance_bootstrap_upper(rows: list[dict]) -> float | None:
    if not rows:
        return None
    groups: dict[str, list[float]] = {}
    for row in rows:
        groups.setdefault(row["instance_hash"], []).append(
            float(row["ratio"])
        )
    keys = sorted(groups)
    rng = random.Random(20260801)
    values = []
    for _ in range(10_000):
        draw = [keys[rng.randrange(len(keys))] for _ in keys]
        values.append(_geomean([
            value for key in draw for value in groups[key]
        ]))
    values.sort()
    return values[9750]


def _geomean_or_none(values: list[float]) -> float | None:
    return _geomean(values) if values else None


def _geomean(values: list[float]) -> float:
    return math.exp(statistics.fmean(
        math.log(max(1.0e-12, float(value))) for value in values
    ))


def _audit_training() -> dict:
    path = _first_existing(STRICT_TRAINING, RELAXED_TRAINING)
    if path is None:
        return _check("INCOMPLETE", "Linear/MLP/TinyGAT report missing")
    payload = _load(path)
    kinds = {
        str(row.get("model_kind") or "") for row in payload.get("models") or ()
    }
    valid = bool(
        payload.get("schema_version") == TRAINING_SCHEMA
        and payload.get("oracle_gate_passed")
        and kinds == {"linear", "mlp", "gat"}
        and payload.get("supervision_schema_version") == SUPERVISION_SCHEMA
        and payload.get("queue_action_surface") == ACTION_SURFACE
        and not bool(payload.get("deployable"))
    )
    return _check(
        "PASS" if valid else "FAIL",
        "single authorized Linear/MLP/TinyGAT comparison",
        report=str(path),
        authority="relaxed_training_only" if path == RELAXED_TRAINING else "strict",
        model_kinds=sorted(kinds),
        calibration_context_count=payload.get("calibration_context_count"),
    )


def _audit_calibration() -> dict:
    path = _calibration_authority()
    if path is None:
        return _check("INCOMPLETE", "fresh-process calibration report missing")
    payload = _load(path)
    valid = bool(
        payload.get("schema_version") == CALIBRATION_SCHEMA
        and payload.get("gate_pass")
        and payload.get("deployment_authorized")
    )
    return _check(
        "PASS" if valid else "FAIL",
        "unchanged risk, precision, OOD, inference, and GAT-advantage gate",
        report=str(path),
        manifest=payload.get("manifest_path"),
    )


def _audit_heldout() -> dict:
    path = _calibration_authority()
    if path is None:
        return _check("INCOMPLETE", "heldout fresh-process replay missing")
    payload = _load(path)
    gat = next(
        (
            row for row in payload.get("models") or ()
            if row.get("model_kind") == "gat"
        ),
        {},
    )
    heldout = dict(gat.get("heldout") or {})
    valid = bool(
        heldout.get("all_safe")
        and float(heldout.get("net_geomean_ratio", 1.0)) <= 0.90
        and float(payload.get("gat_inference_p99_ms", 1.0e30)) <= 10.0
    )
    return _check(
        "PASS" if valid else "FAIL",
        "unseen-snapshot three-repeat heldout and inference gate",
        report=str(path),
        heldout=heldout,
        gat_inference_p99_ms=payload.get("gat_inference_p99_ms"),
    )


def _calibration_authority() -> Path | None:
    for path in (
        STRICT_CALIBRATION,
        RELAXED_CALIBRATION,
        SUPPLEMENTAL_CALIBRATION,
    ):
        if not path.is_file():
            continue
        payload = _load(path)
        if (
            payload.get("schema_version") == CALIBRATION_SCHEMA
            and bool(payload.get("gate_pass"))
            and bool(payload.get("deployment_authorized"))
        ):
            if path != SUPPLEMENTAL_CALIBRATION or (
                _audit_supplemental_calibration_binding()["status"]
                == "PASS"
            ):
                return path
    return _first_existing(
        STRICT_CALIBRATION,
        RELAXED_CALIBRATION,
        SUPPLEMENTAL_CALIBRATION,
    )


def _audit_supplemental_calibration_binding() -> dict:
    artifacts = (
        SUPPLEMENTAL_CALIBRATION_BINDING,
        SUPPLEMENTAL_CALIBRATION,
    )
    if not any(path.exists() for path in artifacts):
        return _check(
            "PASS",
            "supplemental calibration path not used",
            used=False,
        )
    issues = []
    if not SUPPLEMENTAL_CALIBRATION_FREEZE.is_file():
        issues.append("supplemental_freeze_missing")
    else:
        freeze = _load(SUPPLEMENTAL_CALIBRATION_FREEZE)
        if freeze.get("schema_version") != (
            "lunar_ice_bpc.p0v5_qg2_supplemental_calibration_controller_freeze.v1"
        ):
            issues.append("supplemental_freeze_schema_mismatch")
        if (
            not bool(freeze.get("development_only"))
            or bool(freeze.get("deployable"))
            or int(freeze.get("training_rows_added", -1)) != 0
        ):
            issues.append("supplemental_freeze_safety_mismatch")
        controller = ROOT / (
            "scripts/run_p0v5_qg2_supplemental_calibration_after_training.py"
        )
        if str(freeze.get("controller_sha256") or "") != _sha256(
            controller
        ):
            issues.append("supplemental_controller_drift")
        for raw_path, expected in dict(
            freeze.get("frozen_file_sha256") or {}
        ).items():
            target = _resolve(raw_path)
            if not target.is_file() or _sha256(target) != str(expected):
                issues.append(f"supplemental_frozen_drift:{raw_path}")
    if not SUPPLEMENTAL_CALIBRATION_BINDING.is_file():
        issues.append("supplemental_binding_missing")
    else:
        binding = _load(SUPPLEMENTAL_CALIBRATION_BINDING)
        if binding.get("schema_version") != (
            "lunar_ice_bpc.p0v5_qg2_supplemental_calibration_binding.v1"
        ):
            issues.append("supplemental_binding_schema_mismatch")
        if int(binding.get("training_rows_added", -1)) != 0:
            issues.append("supplemental_training_leak")
        for path_key, hash_key in (
            ("training_report", "training_report_sha256"),
            ("oracle_summary", "oracle_summary_sha256"),
            ("supplemental_manifest", "supplemental_manifest_sha256"),
            ("training_view", "training_view_sha256"),
            ("oracle_view", "oracle_view_sha256"),
            ("split_view", "split_view_sha256"),
            ("calibrator", "calibrator_sha256"),
            ("calibration_report", "calibration_report_sha256"),
        ):
            target = _resolve(binding.get(path_key) or "")
            if (
                not target.is_file()
                or _sha256(target) != str(binding.get(hash_key) or "")
            ):
                issues.append(f"supplemental_binding_drift:{path_key}")
    return _check(
        "FAIL" if issues else "PASS",
        "leakage-safe supplemental calibration binding",
        used=True,
        issues=issues,
        binding=str(SUPPLEMENTAL_CALIBRATION_BINDING),
    )


def _audit_supplemental_e2e_formal_binding() -> dict:
    artifacts = (
        SUPPLEMENTAL_E2E_FREEZE,
        SUPPLEMENTAL_E2E_STATE,
        SUPPLEMENTAL_FORMAL_FREEZE,
        SUPPLEMENTAL_FORMAL_STATE,
    )
    if not any(path.exists() for path in artifacts):
        return _check(
            "PASS",
            "supplemental E2E/formal path not used",
            used=False,
        )
    issues = []
    issues.extend(_supplemental_controller_freeze_issues(
        freeze_path=SUPPLEMENTAL_E2E_FREEZE,
        schema=(
            "lunar_ice_bpc.p0v5_qg2_supplemental_e2e_controller_freeze.v1"
        ),
        controller=(
            ROOT / "scripts/run_p0v5_qg2_e2e_after_supplemental_calibration.py"
        ),
        prefix="e2e",
    ))
    issues.extend(_supplemental_controller_freeze_issues(
        freeze_path=SUPPLEMENTAL_FORMAL_FREEZE,
        schema=(
            "lunar_ice_bpc.p0v5_qg2_supplemental_formal_controller_freeze.v1"
        ),
        controller=(
            ROOT / "scripts/run_p0v5_qg2_formal_after_supplemental_e2e.py"
        ),
        prefix="formal",
    ))
    issues.extend(_supplemental_stage_state_issues(
        state_path=SUPPLEMENTAL_E2E_STATE,
        schema="lunar_ice_bpc.p0v5_qg2_supplemental_e2e_controller_state.v1",
        passed_status="E2E_PASSED",
        no_op_status="NOT_NEEDED_DEVELOPMENT_E2E_ALREADY_PASSED",
        result_path=E2E_ACCEPTANCE,
        standard_state_path=STANDARD_E2E_STATE,
        standard_passed_status="E2E_PASSED",
        prefix="e2e",
    ))
    issues.extend(_supplemental_stage_state_issues(
        state_path=SUPPLEMENTAL_FORMAL_STATE,
        schema=(
            "lunar_ice_bpc.p0v5_qg2_supplemental_formal_controller_state.v1"
        ),
        passed_status="FORMAL_FULL20_PASSED",
        no_op_status="NOT_NEEDED_FORMAL_FULL20_ALREADY_PASSED",
        result_path=FORMAL_ACCEPTANCE,
        standard_state_path=STANDARD_FORMAL_STATE,
        standard_passed_status="FORMAL_FULL20_PASSED",
        prefix="formal",
    ))
    return _check(
        "FAIL" if issues else "PASS",
        "hash-bound supplemental E2E and formal controller evidence",
        used=True,
        issues=issues,
        e2e_state=str(SUPPLEMENTAL_E2E_STATE),
        formal_state=str(SUPPLEMENTAL_FORMAL_STATE),
    )


def _supplemental_controller_freeze_issues(
    *,
    freeze_path: Path,
    schema: str,
    controller: Path,
    prefix: str,
) -> list[str]:
    if not freeze_path.is_file():
        return [f"{prefix}_freeze_missing"]
    freeze = _load(freeze_path)
    issues = []
    if freeze.get("schema_version") != schema:
        issues.append(f"{prefix}_freeze_schema_mismatch")
    if (
        not bool(freeze.get("development_only"))
        or bool(freeze.get("deployable"))
        or bool(freeze.get("production_default"))
    ):
        issues.append(f"{prefix}_freeze_safety_mismatch")
    if (
        not controller.is_file()
        or str(freeze.get("controller_sha256") or "") != _sha256(controller)
    ):
        issues.append(f"{prefix}_controller_drift")
    for raw_path, expected in dict(
        freeze.get("frozen_file_sha256") or {}
    ).items():
        target = _resolve(raw_path)
        if not target.is_file() or _sha256(target) != str(expected):
            issues.append(f"{prefix}_frozen_drift:{raw_path}")
    return issues


def _supplemental_stage_state_issues(
    *,
    state_path: Path,
    schema: str,
    passed_status: str,
    no_op_status: str,
    result_path: Path,
    standard_state_path: Path,
    standard_passed_status: str,
    prefix: str,
) -> list[str]:
    if not state_path.is_file():
        return [f"{prefix}_state_missing"]
    state = _load(state_path)
    issues = []
    if state.get("schema_version") != schema:
        issues.append(f"{prefix}_state_schema_mismatch")
    status = str(state.get("status") or "")
    if status not in {passed_status, no_op_status}:
        issues.append(f"{prefix}_state_not_passed:{status}")
    if (
        not result_path.is_file()
        or _sha256(result_path) != str(state.get("result_sha256") or "")
    ):
        issues.append(f"{prefix}_result_binding_mismatch")
    if status == no_op_status:
        if not standard_state_path.is_file():
            issues.append(f"{prefix}_standard_state_missing_for_no_op")
        else:
            standard = _load(standard_state_path)
            if str(standard.get("status") or "") != standard_passed_status:
                issues.append(f"{prefix}_standard_state_not_passed_for_no_op")
            if str(standard.get("result_sha256") or "") != str(
                state.get("result_sha256") or ""
            ):
                issues.append(f"{prefix}_standard_result_binding_mismatch")
    return issues


def _audit_acceptance(path: Path, *, mode: str, scales: set[int]) -> dict:
    if not path.is_file():
        return _check("INCOMPLETE", f"{mode} paired acceptance missing", evidence=str(path))
    payload = _load(path)
    roots_valid = True
    root_evidence = {}
    for prefix in ("control", "guided"):
        root = _resolve(payload.get(f"{prefix}_root") or "")
        observed = _acceptance_artifact_hash(root) if root.is_dir() else ""
        expected = str(payload.get(f"{prefix}_root_hash") or "")
        root_evidence[prefix] = {
            "root": str(root),
            "expected_hash": expected,
            "observed_hash": observed,
        }
        roots_valid = roots_valid and bool(observed and observed == expected)
    valid = bool(
        payload.get("schema_version")
        == "lunar_ice_bpc.p0v5_qg2_paired_acceptance.v1"
        and payload.get("mode") == mode
        and bool(payload.get("passed"))
        and int(payload.get("violation_count") or 0) == 0
        and {int(value) for value in (payload.get("by_scale") or {})} == scales
        and roots_valid
    )
    return _check(
        "PASS" if valid else "FAIL",
        f"{mode} paired acceptance",
        evidence=str(path),
        required_scales=sorted(scales),
        roots=root_evidence,
    )


def _audit_candidate_freeze() -> dict:
    if not CANDIDATE_FREEZE.is_file():
        return _check(
            "INCOMPLETE",
            "independent action-surface-v2 candidate freeze missing",
            freeze=str(CANDIDATE_FREEZE),
        )
    payload = _load(CANDIDATE_FREEZE)
    issues = []
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_action_surface_v2_candidate_freeze.v1"
    ):
        issues.append("schema_mismatch")
    if payload.get("status") != "FROZEN_EXPERIMENT_CANDIDATE":
        issues.append("status_mismatch")
    if bool(payload.get("production_default")):
        issues.append("production_default_changed")
    if not bool(payload.get("historical_baselines_unchanged")):
        issues.append("historical_baseline_safety_missing")
    if not all(bool(payload.get(key)) for key in (
        "deployment_authorized",
        "development_e2e_passed",
        "formal_full20_passed",
    )):
        issues.append("acceptance_or_deployment_gate_missing")
    for raw_path, expected in dict(
        payload.get("frozen_file_sha256") or {}
    ).items():
        target = _resolve(raw_path)
        if not target.is_file() or _sha256(target) != str(expected):
            issues.append(f"drift:{raw_path}")
    return _check(
        "FAIL" if issues else "PASS",
        "independent P0V5 QG2 action-surface-v2 experiment candidate",
        freeze=str(CANDIDATE_FREEZE),
        issues=issues,
    )


def _run_tests() -> dict:
    commands = (
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_p0v5_qg2_label_state_gat.py",
            "tests/test_p0v5_qg2_relaxed_training_gate.py",
            "tests/test_p0v5_qg2_relaxed_training_controller.py",
            "tests/test_p0v5_qg2_action_surface_v2_completion_audit.py",
            "tests/test_p0v5_qg2_action_surface_v2_controllers.py",
            "tests/test_p0v5_qg2_supplemental_calibration_manifest.py",
            "tests/test_p0v5_qg2_supplemental_calibration_runner.py",
            "tests/test_p0v5_qg2_supplemental_calibration_controller.py",
            "tests/test_p0v5_qg2_supplemental_e2e_controller.py",
            "tests/test_p0v5_qg2_supplemental_formal_controller.py",
            "tests/test_p0v5_qg2_supplemental_finalizer.py",
            "tests/test_p0v5_qg2_live_markdown.py",
            "tests/test_p0v5_qg2_measured_portfolio_oracle.py",
        ],
        ["ctest", "--test-dir", str(BUILD), "--output-on-failure"],
        ["git", "diff", "--check"],
    )
    rows = []
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        rows.append({
            "command": command,
            "returncode": completed.returncode,
            "stdout_tail": completed.stdout[-4000:],
            "stderr_tail": completed.stderr[-4000:],
        })
    return _check(
        "PASS" if all(row["returncode"] == 0 for row in rows) else "FAIL",
        "QG2 Python, Native CTest, and diff checks",
        commands=rows,
    )


def _first_existing(*paths: Path) -> Path | None:
    return next((path for path in paths if path.is_file()), None)


def _acceptance_artifact_hash(root: Path) -> str:
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
    if status not in {"PASS", "FAIL", "INCOMPLETE"}:
        raise ValueError(f"invalid audit status {status}")
    return {"status": status, "note": note, "evidence": evidence}


def _resolve(value) -> Path:
    path = Path(str(value))
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


if __name__ == "__main__":
    raise SystemExit(main())

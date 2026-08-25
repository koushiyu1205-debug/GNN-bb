#!/usr/bin/env python3
"""Finalize one pre-frozen Interaction-GAT V2 stage without reselection."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import verify_portfolio_freezes  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import (  # noqa: E402
    MatchedContextOutcome,
    assess_formal_full100,
    collapse_matched_matrix,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_gates_v2 import (  # noqa: E402
    assess_gat_heldout_advantage,
    assess_v2_arm_scale_admission,
    assess_v2_qgr1_force_on,
    measured_v2_portfolio_oracle,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v2_20260807"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=(
        "arm_admission", "qgr1_force_on", "portfolio_oracle",
        "heldout", "development_e2e", "formal_full100",
    ))
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    if bool(_load(run_root / "state.json").get("terminal")):
        raise SystemExit("terminal chain forbids later-stage artifact writers")
    payload_path = args.input.resolve()
    payload = _load(payload_path)
    config = _load(run_root / "config.freeze.json")
    if args.stage == "heldout":
        return _heldout(run_root, payload, payload_path)
    if args.stage == "development_e2e":
        return _development_e2e(run_root, payload, payload_path)
    if args.stage == "formal_full100":
        return _formal(run_root, payload, payload_path)

    outcomes = _outcomes(payload, config)
    _write_once(run_root / f"{args.stage}.collapsed.json", {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_collapsed_outcomes.v2",
        "source": str(payload_path), "source_sha256": _sha256(payload_path),
        "rows": [asdict(row) for row in outcomes],
    })
    if args.stage == "arm_admission":
        mask = {"QGR1": [], "QD1": [], "QB1": []}
        veto = {"30": [], "50": []}
        rows, correctness = [], False
        for arm in ("QD1", "QB1"):
            for scale in (30, 50):
                row = assess_v2_arm_scale_admission(outcomes, arm=arm, scale=scale)
                rows.append(row)
                correctness = correctness or bool(row["correctness_redlines"])
                if row["admitted"]:
                    mask[arm].append(scale)
                else:
                    veto[str(scale)].append(arm)
        decision = {
            "passed": not correctness, "correctness_chain_redline": correctness,
            "arm_scale_mask": mask, "forced_veto_arms_by_scale": veto,
            "rows": rows, "next_stage": "QGR1_TRAINING_AND_FORCE_ON",
        }
        if correctness:
            return _finish(run_root, args.stage, decision, terminal_reason="CORRECTNESS_REDLINE")
        return _finish(run_root, args.stage, decision, next_stage="QGR1_TRAINING_AND_FORCE_ON")
    if args.stage == "qgr1_force_on":
        decision = assess_v2_qgr1_force_on(
            outcomes,
            payload.get("qgr1_telemetry_by_context")
            or _derive_qgr1_telemetry(payload),
        )
        previous = _load(run_root / "arm_admission.decision.json")["decision"]
        mask = dict(previous["arm_scale_mask"])
        veto = {key: list(value) for key, value in previous["forced_veto_arms_by_scale"].items()}
        if decision["admitted"]:
            mask["QGR1"] = [30, 50]
        else:
            mask["QGR1"] = []
            for scale in ("30", "50"):
                veto[scale] = sorted(set((*veto[scale], "QGR1")))
        decision.update({
            "arm_scale_mask": mask, "forced_veto_arms_by_scale": veto,
            "performance_failure_is_permanent_arm_veto": True,
            "qgr1_hyperparameter_reselection_forbidden": True,
        })
        if decision["correctness_redlines"]:
            return _finish(run_root, args.stage, decision, terminal_reason="CORRECTNESS_REDLINE")
        return _finish(run_root, args.stage, decision, next_stage="COMPLETE_MATCHED_MATRIX_AND_ORACLE")
    if args.stage == "portfolio_oracle":
        admission = _load(run_root / "qgr1_force_on.decision.json")["decision"]
        decision = measured_v2_portfolio_oracle(
            outcomes,
            admitted_arms_by_scale={
                scale: [arm for arm, scales in admission["arm_scale_mask"].items() if scale in scales]
                for scale in (30, 50)
            },
        )
        if not decision["selector_training_authorized"]:
            return _finish(
                run_root, args.stage, decision,
                terminal_reason="+".join(decision["terminal_reasons"]),
            )
        return _finish(run_root, args.stage, decision, next_stage="GAT_TRAINING_CALIBRATION")
    raise AssertionError("unreachable")


def _heldout(run_root, payload, source):
    selection = _load(run_root / "selector_selection.decision.json")
    if selection.get("selected_model_kind") != "gat":
        return _finish(run_root, "heldout", {"error": "candidate_not_gat"}, terminal_reason="NO_GAT_ADVANTAGE")
    decision = assess_gat_heldout_advantage(
        payload["summaries"],
        preparation_p99_ms=float(payload["warm_graph_tensorization_inference_p99_ms"]),
    )
    decision.update({
        "source": str(source), "source_sha256": _sha256(source),
        "all_models_frozen_before_heldout": bool(payload.get("all_models_frozen_before_heldout")),
        "first_import_load_included_in_fresh_candidate_wall": bool(payload.get("first_import_load_included")),
    })
    if not decision["all_models_frozen_before_heldout"] or not decision["first_import_load_included_in_fresh_candidate_wall"]:
        decision["passed"] = False
        decision["violations"] = sorted(set((*decision["violations"], "HELDOUT_EXECUTION_CONTRACT_INCOMPLETE")))
        decision["terminal_reason"] = "HELDOUT_FRESH_FAILED"
    if not decision["passed"]:
        return _finish(run_root, "heldout", decision, terminal_reason=decision["terminal_reason"])
    heldout_manifest = run_root / "selector_heldout_candidate.manifest.json"
    # Freeze the byte-independent JSON payload under the stable full-BPC name.
    # This is a copy, not a reselection: checkpoint, calibration, thresholds,
    # arm masks, and all authority fields remain identical.
    _write_once(
        run_root / "research_candidate.manifest.json",
        _load(heldout_manifest),
    )
    decision["research_candidate_manifest"] = str(
        run_root / "research_candidate.manifest.json"
    )
    decision["research_candidate_manifest_sha256"] = _sha256(
        run_root / "research_candidate.manifest.json"
    )
    return _finish(run_root, "heldout", decision, next_stage="DEVELOPMENT_E2E")


def _development_e2e(run_root, payload, source):
    violations = []
    scales = {}
    for scale in (30, 50):
        row = dict(dict(payload.get("scales") or {}).get(str(scale)) or {})
        scales[str(scale)] = row
        if float(row.get("gm") or float("inf")) >= 1.0:
            violations.append(f"SCALE{scale}_E2E_GM_NOT_LT_1")
        if int(row.get("candidate_exact_count") or 0) < int(row.get("q0_exact_count") or 0):
            violations.append("DEVELOPMENT_E2E_EXACT_COUNT_DECREASED")
        if int(row.get("activation_instances") or 0) < 2:
            violations.append(f"SCALE{scale}_E2E_ACTIVATION_INSTANCES_LT_2")
        if float(row.get("worst_instance_median_ratio") or float("inf")) > 1.10:
            violations.append(f"SCALE{scale}_E2E_WORST_RATIO_GT_1_10")
        if int(row.get("tree_model_calls") or 0):
            violations.append(f"SCALE{scale}_TREE_MODEL_CALL")
        if row.get("correctness_redlines"):
            violations.append("CORRECTNESS_REDLINE")
    decision = {
        "passed": not violations, "scales": scales,
        "violations": sorted(set(violations)),
        "source": str(source), "source_sha256": _sha256(source),
    }
    if violations:
        reason = "DEVELOPMENT_E2E_EXACT_COUNT_DECREASED" if "DEVELOPMENT_E2E_EXACT_COUNT_DECREASED" in violations else "DEVELOPMENT_E2E_FAILED"
        return _finish(run_root, "development_e2e", decision, terminal_reason=reason)
    manifest = run_root / "research_candidate.manifest.json"
    _write_once(run_root / "research_candidate.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_research_candidate_freeze.v2",
        "status": "FROZEN_AFTER_DEVELOPMENT_E2E_BEFORE_FORMAL_FULL100",
        "manifest": str(manifest), "manifest_sha256": _sha256(manifest),
        "model_kind": "gat", "message_passing_required": True,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
        "formal_outcomes_may_not_change_candidate": True,
    })
    return _finish(run_root, "development_e2e", decision, next_stage="FORMAL_FULL100")


def _formal(run_root, payload, source):
    base = assess_formal_full100(payload["rows"])
    violations = list(base.get("violations") or ())
    counters = dict(payload.get("runtime_counters_by_scale") or {})
    for scale in (5, 10, 20):
        row = dict(counters.get(str(scale)) or {})
        if any(int(row.get(key) or 0) for key in (
            "manifest_reads", "torch_imports", "gat_calls", "ranker_calls"
        )):
            violations.append("FORMAL_SMALL_SCALE_MODEL_CALL")
    activations = dict(payload.get("activation_instances_by_scale") or {})
    for scale in (30, 50):
        if int(activations.get(str(scale)) or 0) < 5:
            violations.append(f"FORMAL_SCALE{scale}_GAT_ACTIVATION_INSTANCES_LT_5")
    decision = {
        **base, "passed": bool(base.get("passed")) and not violations,
        "violations": sorted(set(violations)),
        "runtime_counters_by_scale": counters,
        "activation_instances_by_scale": activations,
        "source": str(source), "source_sha256": _sha256(source),
        "candidate_retrained_after_formal": False,
    }
    reason = None if decision["passed"] else (
        "FORMAL_SMALL_SCALE_MODEL_CALL" if "FORMAL_SMALL_SCALE_MODEL_CALL" in violations
        else "FORMAL_FULL100_FAILED"
    )
    return _finish(run_root, "formal_full100", decision, terminal_reason=reason, terminal_pass=decision["passed"])


def _finish(run_root, stage, decision, *, next_stage=None, terminal_reason=None, terminal_pass=False):
    artifact = {
        "schema_version": f"lunar_ice_bpc.p0v5_interaction_gat_{stage}_decision.v2",
        "stage": stage, "decision": decision,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    _write_once(run_root / f"{stage}.decision.json", artifact)
    terminal = terminal_reason is not None or terminal_pass
    state_path = run_root / "state.json"
    state = _load(state_path)
    state.update({
        "current_stage": "TERMINAL" if terminal else next_stage,
        "status": "PASS" if terminal_pass else "FAIL" if terminal_reason else "READY",
        "terminal": terminal,
        "terminal_decision": "FORMAL_FULL100_PASS" if terminal_pass else terminal_reason,
    })
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if terminal:
        _write_once(run_root / "terminal_decision.json", {
            "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_terminal.v2",
            "decision": "PASS" if terminal_pass else "FAIL",
            "reason": "FORMAL_FULL100_PASS" if terminal_pass else terminal_reason,
            "stage": stage,
            "decision_artifact": str(run_root / f"{stage}.decision.json"),
            "development_only": True, "deployment_authorized": False,
            "production_switch_authorized": False,
        })
    return 0 if not terminal_reason else 2


def _outcomes(payload, config):
    if payload.get("schema_version") == (
        "lunar_ice_bpc.p0v5_interaction_gat_collapsed_outcome_bundle.v2"
    ):
        rows = []
        for raw in payload.get("rows") or ():
            row = dict(raw)
            row["correctness_redlines"] = tuple(row.get("correctness_redlines") or ())
            rows.append(MatchedContextOutcome(**row))
        return tuple(rows)
    return collapse_matched_matrix(
        payload["rows"],
        caps_by_scale=config["execution"]["replay_caps_sec"],
        required_repeats=config["execution"]["blocked_fresh_process_repeats"],
    )


def _derive_qgr1_telemetry(payload):
    grouped = {}
    for row in payload.get("rows") or ():
        if str(row.get("arm") or "") != "QGR1":
            continue
        grouped.setdefault(str(row["context_id"]), []).append(dict(row))
    result = {}
    for context_id, rows in grouped.items():
        scored = sum(int(row.get("guidance_scored_labels") or 0) for row in rows)
        scoring = sum(float(row.get("native_scoring_wall_sec") or 0.0) for row in rows)
        proof = sum(float(row.get("solver_wall_sec") or 0.0) for row in rows)
        reordered = covered = 0
        for row in rows:
            raw_path = Path(str(row.get("raw_path") or ""))
            if not raw_path.is_file():
                continue
            telemetry = dict(_load(raw_path).get("proof_telemetry") or {})
            reordered += int(
                telemetry.get("proof_queue_guidance_reordered_label_hash_count") or 0
            )
            covered += int(
                telemetry.get("proof_queue_guidance_covered_bucket_count") or 0
            )
        result[context_id] = {
            "reordered_label_fraction": reordered / max(1, scored),
            "reordered_label_hash_count": reordered,
            "scored_labels": scored,
            "covered_bucket_count": covered,
            "scoring_wall_sec": scoring,
            "proof_wall_sec": proof,
        }
    return result


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_once(path, payload):
    path = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable V2 stage decision drift:{path}")
    if not path.exists():
        path.write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

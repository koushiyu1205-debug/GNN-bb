#!/usr/bin/env python3
"""Apply V3 instance-first Go/No-Go gates and advance its state machine."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import (  # noqa: E402
    assess_formal_full100,
    collapse_matched_matrix,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_gates_v3 import (  # noqa: E402
    assess_v3_arm_scale_admission,
    assess_v3_qgr1_force_on,
    measured_v3_base_portfolio_oracle,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v3_20260814"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=(
        "arm_admission", "base_oracle", "qgr1_force_on",
        "development_e2e", "formal_full100",
    ))
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--matrix", type=Path)
    parser.add_argument("--telemetry", type=Path)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    _verify_active(run_root)
    config = _load(run_root / "config.freeze.json")
    matrix = (
        args.matrix.resolve() if args.matrix else run_root / "matched_matrix_rows.json"
    )
    if args.stage == "development_e2e":
        return _development_e2e(run_root, _load(matrix), matrix)
    if args.stage == "formal_full100":
        return _formal_full100(run_root, _load(matrix), matrix)
    outcomes = collapse_matched_matrix(
        _load(matrix)["rows"],
        caps_by_scale=config["execution"]["replay_caps_sec"],
        required_repeats=3,
    )
    if any(row.correctness_redlines for row in outcomes):
        _terminal(run_root, "CORRECTNESS_REDLINE", {
            "redlines": sorted({v for row in outcomes for v in row.correctness_redlines})
        })
        return 2
    if args.stage == "arm_admission":
        decision = {
            "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_arm_admission.v3",
            "source_matrix": str(matrix), "source_matrix_sha256": _sha256(matrix),
            "rows": [
                assess_v3_arm_scale_admission(outcomes, arm=arm, scale=scale)
                for scale in (30, 50) for arm in ("QD1", "QB1")
            ],
        }
        _write_once(run_root / "arm_admission.decision.json", decision)
        _set_state(run_root, "BASE_PORTFOLIO_HEADROOM", "READY")
    elif args.stage == "base_oracle":
        admission = _load(run_root / "arm_admission.decision.json")
        masks = {
            str(scale): [
                row["arm"] for row in admission["rows"]
                if int(row["scale"]) == scale and bool(row["admitted"])
            ] for scale in (30, 50)
        }
        decision = measured_v3_base_portfolio_oracle(
            outcomes, admitted_arms_by_scale=masks
        )
        decision.update({
            "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_base_oracle.v3",
            "source_matrix": str(matrix), "source_matrix_sha256": _sha256(matrix),
            "arm_scale_mask": masks,
        })
        _write_once(run_root / "base_portfolio_oracle.decision.json", decision)
        if decision["terminal_reasons"]:
            _terminal(run_root, decision["terminal_reasons"][0], decision)
            return 3
        _set_state(run_root, "OPTIONAL_QGR1_TRAINING", "READY")
    else:
        telemetry_path = args.telemetry.resolve() if args.telemetry else None
        telemetry = (
            dict(_load(telemetry_path).get("by_context") or {})
            if telemetry_path else _derive_qgr1_telemetry(_load(matrix))
        )
        decision = {
            "schema_version": "lunar_ice_bpc.p0v5_qgr1_force_on_decision.v3",
            "source_matrix": str(matrix), "source_matrix_sha256": _sha256(matrix),
            "source_telemetry": str(telemetry_path) if telemetry_path else "derived_from_matrix_raw",
            "source_telemetry_sha256": _sha256(telemetry_path) if telemetry_path else _sha256(matrix),
            "scales": {
                str(scale): assess_v3_qgr1_force_on(
                    outcomes, telemetry, scale=scale
                ) for scale in (30, 50)
            },
        }
        _write_once(run_root / "qgr1_force_on.decision.json", decision)
        _set_state(run_root, "QGR1_MATRIX_OR_SELECTOR_DATASET", "READY")
    print(json.dumps(decision, ensure_ascii=False, indent=2))
    return 0


def _derive_qgr1_telemetry(payload):
    grouped = {}
    for row in payload.get("rows") or ():
        if str(row.get("arm") or "") == "QGR1":
            grouped.setdefault(str(row["context_id"]), []).append(row)
    result = {}
    for context_id, rows in grouped.items():
        scored = sum(int(row.get("guidance_scored_labels") or 0) for row in rows)
        scoring = sum(float(row.get("native_scoring_wall_sec") or 0.0) for row in rows)
        proof = sum(float(row.get("solver_wall_sec") or 0.0) for row in rows)
        reordered = 0
        for row in rows:
            raw_path = Path(str(row.get("raw_path") or ""))
            if raw_path.is_file():
                telemetry = dict(_load(raw_path).get("proof_telemetry") or {})
                reordered += int(
                    telemetry.get("proof_queue_guidance_reordered_label_hash_count") or 0
                )
        result[context_id] = {
            "reordered_label_fraction": reordered / max(1, scored),
            "scored_labels": scored, "scoring_wall_sec": scoring,
            "proof_wall_sec": proof,
        }
    return result


def _development_e2e(run_root, payload, source):
    violations = []
    scales = {}
    for scale in (30, 50):
        row = dict(dict(payload.get("scales") or {}).get(str(scale)) or {})
        scales[str(scale)] = row
        if row.get("gm") is None or float(row["gm"]) >= 1.0:
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
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_development_e2e_decision.v3",
        "passed": not violations, "scales": scales,
        "violations": sorted(set(violations)),
        "source": str(source), "source_sha256": _sha256(source),
    }
    _write_once(run_root / "development_e2e.decision.json", decision)
    if violations:
        reason = (
            "DEVELOPMENT_E2E_EXACT_COUNT_DECREASED"
            if "DEVELOPMENT_E2E_EXACT_COUNT_DECREASED" in violations
            else "DEVELOPMENT_E2E_FAILED"
        )
        _terminal(run_root, reason, decision)
        return 2
    manifest = run_root / "research_candidate.manifest.json"
    _write_once(run_root / "research_candidate.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_research_candidate_freeze.v3",
        "status": "FROZEN_AFTER_DEVELOPMENT_E2E_BEFORE_FORMAL_FULL100",
        "manifest": str(manifest), "manifest_sha256": _sha256(manifest),
        "model_kind": "gat", "message_passing_required": True,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
        "formal_outcomes_may_not_change_candidate": True,
    })
    _set_state(run_root, "FORMAL_FULL100", "READY")
    return 0


def _formal_full100(run_root, payload, source):
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
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    _write_once(run_root / "formal_full100.decision.json", decision)
    reason = "FORMAL_FULL100_PASS" if decision["passed"] else (
        "FORMAL_SMALL_SCALE_MODEL_CALL"
        if "FORMAL_SMALL_SCALE_MODEL_CALL" in violations else "FORMAL_FULL100_FAILED"
    )
    _terminal(run_root, reason, decision, passed=bool(decision["passed"]))
    return 0 if decision["passed"] else 2


def _verify_active(run_root):
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        _terminal(run_root, "FREEZE_HASH_DRIFT", {"error": str(exc)})
        raise SystemExit(str(exc)) from exc
    if bool(_load(run_root / "state.json").get("terminal")):
        raise SystemExit("terminal V3 chain forbids stage finalizers")


def _set_state(run_root, stage, status):
    path = run_root / "state.json"
    state = _load(path)
    state.update({"current_stage": stage, "status": status})
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _terminal(run_root, reason, detail, *, passed=False):
    terminal = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_terminal.v3",
        "decision": "PASS" if passed else "FAIL", "reason": str(reason), "detail": detail,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    _write_once(run_root / "terminal_decision.json", terminal)
    state_path = run_root / "state.json"
    state = _load(state_path) if state_path.is_file() else {}
    state.update({
        "current_stage": "TERMINAL", "status": "PASS" if passed else "FAIL", "terminal": True,
        "terminal_decision": str(reason), "development_only": True,
        "deployment_authorized": False, "production_switch_authorized": False,
    })
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_once(path, payload):
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != encoded:
        raise SystemExit(f"immutable V3 decision already differs:{path}")
    if not path.exists():
        path.write_text(encoded, encoding="utf-8")


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

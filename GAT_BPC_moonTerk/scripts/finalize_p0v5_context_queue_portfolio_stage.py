#!/usr/bin/env python3
"""Finalize one pre-frozen portfolio stage without reopening earlier choices."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import (  # noqa: E402
    assess_arm_scale_admission,
    assess_development_e2e,
    assess_formal_full100,
    assess_heldout_fresh,
    assess_qgr1_force_on,
    collapse_matched_matrix,
    measured_portfolio_oracle,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_context_queue_portfolio_v1_20260807_r1"


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
    _verify_freezes(run_root)
    state = _load(run_root / "state.json")
    if bool(state.get("terminal")):
        raise SystemExit("experiment chain is already terminal")
    payload = _load(args.input.resolve())
    config = _load(run_root / "config.freeze.json")

    if args.stage == "formal_full100":
        decision = assess_formal_full100(payload["rows"])
        terminal_reason = None if decision["passed"] else "FORMAL_FULL100_FAILED"
        _finish(run_root, args.stage, decision, terminal=True, reason=terminal_reason)
        return 0 if decision["passed"] else 2

    outcomes = collapse_matched_matrix(
        payload["rows"],
        caps_by_scale=config["execution"]["replay_caps_sec"],
        required_repeats=config["execution"]["blocked_fresh_process_repeats"],
    )
    collapsed_payload = {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_collapsed_outcomes.v1",
        "source": str(args.input.resolve()),
        "source_sha256": _sha256(args.input.resolve()),
        "rows": [asdict(row) for row in outcomes],
    }
    _write_once(run_root / f"{args.stage}.collapsed.json", collapsed_payload)

    if args.stage == "arm_admission":
        rows = []
        mask = {"QGR1": [], "QD1": [], "QB1": []}
        veto_by_scale = {"30": [], "50": []}
        correctness = False
        for arm in ("QD1", "QB1"):
            for scale in (30, 50):
                row = assess_arm_scale_admission(outcomes, arm=arm, scale=scale)
                rows.append(row)
                correctness = correctness or bool(row["correctness_redlines"])
                if row["admitted"]:
                    mask[arm].append(scale)
                else:
                    veto_by_scale[str(scale)].append(arm)
        decision = {
            "passed": not correctness,
            "correctness_chain_redline": correctness,
            "arm_scale_mask": mask,
            "forced_veto_arms_by_scale": veto_by_scale,
            "rows": rows,
            "next_stage": "QGR1_TRAINING_AND_FORCE_ON",
        }
        if correctness:
            _finish(run_root, args.stage, decision, terminal=True, reason="CORRECTNESS_REDLINE")
            return 2
        _finish(run_root, args.stage, decision, terminal=False, reason=None,
                next_stage="QGR1_TRAINING_AND_FORCE_ON")
        return 0

    if args.stage == "qgr1_force_on":
        decision = assess_qgr1_force_on(outcomes)
        previous = _load(run_root / "arm_admission.decision.json")["decision"]
        mask = dict(previous["arm_scale_mask"])
        veto = dict(previous["forced_veto_arms_by_scale"])
        if decision["admitted"]:
            mask["QGR1"] = [30, 50]
        else:
            mask["QGR1"] = []
            veto["30"] = sorted(set((*veto["30"], "QGR1")))
            veto["50"] = sorted(set((*veto["50"], "QGR1")))
        decision.update({
            "arm_scale_mask": mask,
            "forced_veto_arms_by_scale": veto,
            "performance_failure_is_arm_veto_not_chain_failure": True,
            "next_stage": "COMPLETE_MATCHED_MATRIX_AND_ORACLE",
        })
        if decision["correctness_redlines"]:
            _finish(run_root, args.stage, decision, terminal=True, reason="CORRECTNESS_REDLINE")
            return 2
        _finish(run_root, args.stage, decision, terminal=False, reason=None,
                next_stage="COMPLETE_MATCHED_MATRIX_AND_ORACLE")
        return 0

    if args.stage == "portfolio_oracle":
        admission = _load(run_root / "qgr1_force_on.decision.json")["decision"]
        decision = measured_portfolio_oracle(
            outcomes, admitted_arms_by_scale={
                scale: [
                    arm for arm, scales in admission["arm_scale_mask"].items()
                    if int(scale) in {int(value) for value in scales}
                ]
                for scale in (30, 50)
            },
        )
        if not decision["selector_training_authorized"]:
            reason = "+".join(decision["terminal_reasons"])
            _finish(run_root, args.stage, decision, terminal=True, reason=reason)
            return 2
        _finish(run_root, args.stage, decision, terminal=False, reason=None,
                next_stage="SELECTOR_TRAINING_CALIBRATION")
        return 0

    if args.stage == "heldout":
        decision = assess_heldout_fresh(
            outcomes,
            preparation_p99_ms_by_scale=payload["preparation_p99_ms_by_scale"],
        )
        if not decision["passed"]:
            _finish(run_root, args.stage, decision, terminal=True,
                    reason="HELDOUT_FRESH_FAILED")
            return 2
        _finish(run_root, args.stage, decision, terminal=False, reason=None,
                next_stage="DEVELOPMENT_E2E")
        return 0

    if args.stage == "development_e2e":
        decision = assess_development_e2e(
            outcomes,
            q0_exact_count_by_scale=payload["q0_exact_count_by_scale"],
            candidate_exact_count_by_scale=payload["candidate_exact_count_by_scale"],
        )
        if not decision["passed"]:
            reason = (
                "DEVELOPMENT_E2E_EXACT_COUNT_DECREASED"
                if "DEVELOPMENT_E2E_EXACT_COUNT_DECREASED" in decision["violations"]
                else "DEVELOPMENT_E2E_FAILED"
            )
            _finish(run_root, args.stage, decision, terminal=True, reason=reason)
            return 2
        manifest = run_root / "research_candidate.manifest.json"
        _write_once(run_root / "research_candidate.freeze.json", {
            "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_research_candidate_freeze.v1",
            "status": "FROZEN_AFTER_DEVELOPMENT_E2E_BEFORE_FORMAL_FULL100",
            "manifest": str(manifest),
            "manifest_sha256": _sha256(manifest),
            "development_e2e_decision": str(
                run_root / "development_e2e.decision.json"
            ),
            "development_only": True,
            "deployment_authorized": False,
            "production_switch_authorized": False,
            "formal_outcomes_may_not_change_candidate": True,
        })
        _finish(run_root, args.stage, decision, terminal=False, reason=None,
                next_stage="FORMAL_FULL100")
        return 0
    raise AssertionError("unreachable")


def _finish(run_root, stage, decision, *, terminal, reason, next_stage=None):
    artifact = {
        "schema_version": f"lunar_ice_bpc.p0v5_context_queue_portfolio_{stage}_decision.v1",
        "stage": stage,
        "decision": decision,
        "development_only": True,
        "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    _write_once(run_root / f"{stage}.decision.json", artifact)
    state = _load(run_root / "state.json")
    state.update({
        "current_stage": "TERMINAL" if terminal else next_stage,
        "status": "FAIL" if terminal and reason else "PASS" if terminal else "READY",
        "terminal": terminal,
        "terminal_decision": reason if terminal else None,
    })
    (run_root / "state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if terminal:
        _write_once(run_root / "terminal_decision.json", {
            "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_terminal.v1",
            "decision": "FAIL" if reason else "PASS",
            "reason": reason or "FORMAL_FULL100_PASS",
            "stage": stage,
            "decision_artifact": str(run_root / f"{stage}.decision.json"),
            "development_only": True,
            "deployment_authorized": False,
            "production_switch_authorized": False,
        })


def _verify_freezes(run_root):
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_once(path, payload):
    path = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable decision drift: {path}")
    if not path.exists():
        path.write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

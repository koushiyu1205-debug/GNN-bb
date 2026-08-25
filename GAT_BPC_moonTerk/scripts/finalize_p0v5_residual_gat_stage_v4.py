#!/usr/bin/env python3
"""Apply immutable V4 Go/No-Go gates and write terminal decisions once."""

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
from lunar_ice_bpc.guidance.interaction_gat_queue_gates_v4 import (  # noqa: E402
    assess_v4_qd1_admission, collapse_censor_aware_matrix,
    measured_v4_oracle,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_residual_gat_censor_aware_selector_v4_20260815"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("qd1", "qgr1", "portfolio", "calibration",
                                           "heldout", "development_e2e", "formal"))
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--matrix", type=Path)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    try:
        verify_portfolio_freezes(run_root, ROOT)
        _verify_arm_registry(run_root)
    except (RuntimeError, ValueError) as exc:
        _terminal(run_root, "FREEZE_HASH_DRIFT", str(exc))
        return 1
    if bool(_load(run_root / "state.json").get("terminal")):
        raise SystemExit("terminal V4 chain forbids finalizer writers")
    if args.stage == "qd1":
        if args.matrix is None:
            raise SystemExit("qd1 finalizer requires --matrix")
        return _finalize_qd1(run_root, args.matrix.resolve())
    # Later-stage scripts must create an explicit decision payload and then
    # invoke this finalizer.  Absence is fail closed, never implicit PASS.
    decision = run_root / f"{args.stage}.decision.pending.json"
    if not decision.is_file():
        raise SystemExit(f"V4 {args.stage} pending decision is missing")
    payload = _load(decision)
    if not bool(payload.get("passed")):
        _terminal(run_root, str(payload.get("reason") or "V4_STAGE_FAILED"), payload)
        return 1
    _write_once(run_root / f"{args.stage}.decision.json", payload)
    _update_state(run_root, str(payload.get("next_stage") or "UNKNOWN"), "READY")
    return 0


def _finalize_qd1(run_root, matrix_path):
    config = _load(run_root / "config.freeze.json")
    payload = _load(matrix_path)
    rows = payload.get("rows") or ()
    try:
        outcomes = collapse_censor_aware_matrix(
            rows, caps_by_scale=config["execution"]["replay_caps_sec"],
            required_repeats=3, minimum_comparable_blocks=2,
        )
    except ValueError as exc:
        _terminal(run_root, "INSUFFICIENT_DETERMINED_COVERAGE", str(exc))
        return 1
    redlines = sorted({value for row in outcomes for value in row.correctness_redlines})
    if redlines:
        _terminal(run_root, "V4_NATIVE_TELEMETRY_REDLINE", {"redlines": redlines})
        return 1
    admissions = {str(scale): assess_v4_qd1_admission(outcomes, scale=scale)
                  for scale in (30, 50)}
    _write_once(run_root / "qd1_admission.decision.json", {
        "schema_version": "lunar_ice_bpc.p0v5_qd1_admission_decision.v4",
        "source_matrix": str(matrix_path), "source_matrix_sha256": _sha256(matrix_path),
        "scales": admissions,
    })
    coverage_failed = any(
        row["determined_instances"] < 11
        or row["determined_context_fraction"] < 0.75
        for row in admissions.values()
    )
    if coverage_failed:
        _terminal(run_root, "INSUFFICIENT_DETERMINED_COVERAGE", admissions)
        return 1
    if (
        not admissions["30"]["admitted"]
        or admissions["50"]["mode"] != "selective"
    ):
        _terminal(run_root, "NO_QD1_RESIDUAL_GAT_FEASIBILITY", admissions)
        return 1
    oracle = measured_v4_oracle(
        outcomes, admitted_arms_by_scale={30: ["QD1"], 50: ["QD1"]},
        required_gm=0.98, require_scale50_mixture=False,
    )
    _write_once(run_root / "qd1_base_oracle.decision.json", oracle)
    scale50 = oracle["scales"]["50"]
    if (
        scale50["instance_weighted_gm"] is None
        or float(scale50["instance_weighted_gm"]) > 0.98
        or int(scale50["non_q0_winner_instances"]) < 5
    ):
        _terminal(run_root, "NO_QD1_RESIDUAL_GAT_FEASIBILITY", oracle)
        return 1
    collapsed = {
        "schema_version": "lunar_ice_bpc.p0v5_censor_aware_matched_outcome.v1",
        "source_matrix_sha256": _sha256(matrix_path),
        "rows": [row.__dict__ for row in outcomes],
    }
    _write_once(run_root / "matched_qd1_collapsed.json", collapsed)
    _update_state(run_root, "QGR1_RESIDUAL_LABEL_GAT", "READY")
    print(json.dumps({
        "qd1_admission": admissions, "scale50_base_oracle": scale50,
        "status": "READY_FOR_QGR1_RESIDUAL_LABEL_GAT",
    }, ensure_ascii=False, indent=2))
    return 0


def _verify_arm_registry(run_root):
    path = run_root / "arm_execution.freeze.registry.json"
    if not path.is_file():
        return
    for name, expected in _load(path)["artifact_sha256"].items():
        if _sha256(run_root / name) != expected:
            raise ValueError(f"arm execution freeze drift:{name}")


def _terminal(run_root, reason, detail):
    path = run_root / "terminal_decision.json"
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_terminal.v4",
        "decision": "FAIL", "reason": str(reason), "detail": detail,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    if path.exists():
        if _load(path) != payload:
            raise SystemExit("immutable V4 terminal decision already differs")
    else:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2,
                                   sort_keys=True) + "\n", encoding="utf-8")
    state_path = run_root / "state.json"
    state = _load(state_path)
    state.update({"terminal": True, "terminal_decision": str(path),
                  "current_stage": "TERMINAL", "status": "FAIL"})
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2,
                                     sort_keys=True) + "\n", encoding="utf-8")


def _update_state(run_root, stage, status):
    path = run_root / "state.json"
    payload = _load(path)
    payload.update({"current_stage": stage, "status": status})
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2,
                               sort_keys=True) + "\n", encoding="utf-8")


def _write_once(path, payload):
    path = Path(path)
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != encoded:
        raise SystemExit(f"immutable V4 decision drift:{path}")
    if not path.exists():
        path.write_text(encoded, encoding="utf-8")


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

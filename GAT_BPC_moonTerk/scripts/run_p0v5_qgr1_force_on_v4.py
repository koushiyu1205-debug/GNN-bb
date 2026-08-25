#!/usr/bin/env python3
"""Freeze, export, execute and gate V4 QGR1 force-on evidence."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import verify_portfolio_freezes  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import (  # noqa: E402
    geometric_mean, rotate_blocked_arm_order,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_gates_v4 import (  # noqa: E402
    collapse_censor_aware_matrix,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_residual_gat_censor_aware_selector_v4_20260815"
PREDICTOR = ROOT / "scripts/predict_p0v5_qgr1_residual_potential_v2.py"
MATRIX = ROOT / "scripts/run_p0v5_context_queue_portfolio_matrix.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "export", "run", "analyze"))
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--checkpoint", type=Path)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    verify_portfolio_freezes(run_root, ROOT)
    _assert_active(run_root)
    if args.mode == "freeze":
        return _freeze(run_root)
    if args.checkpoint is None:
        raise SystemExit("QGR1 V4 export/run requires --checkpoint")
    checkpoint = args.checkpoint.resolve()
    if args.mode == "export":
        return _export(run_root, checkpoint)
    if args.mode == "run":
        return _run(run_root, checkpoint)
    return _analyze(run_root)


def _freeze(run_root):
    config = _load(run_root / "config.freeze.json")
    corpus = {row["context_id"]: row for row in _load(run_root / "corpus.freeze.json")["rows"]}
    milestone = _load(run_root / "q0_milestone.freeze.json")["by_context"]
    primary = _load(run_root / "qgr1_primary_context.freeze.json")["rows"]
    if len(primary) != 8 or any(not milestone[row["context_id"]]["replay_eligible"] for row in primary):
        _terminal(run_root, "INSUFFICIENT_DETERMINED_COVERAGE", "QGR1 primary context replay-ineligible")
        return 1
    tasks = []
    for chosen in primary:
        context = corpus[chosen["context_id"]]
        common = {
            "context_id": context["context_id"],
            "instance_hash": context["instance_content_hash"],
            "scale": context["scale"], "partition": "calibration",
            "state_hash": context["state_hash"],
            "cap_sec": config["execution"]["replay_caps_sec"][str(context["scale"])],
            "memory_limit_gb": config["execution"]["memory_limit_gb"],
        }
        for block, order in enumerate(rotate_blocked_arm_order(
            context["state_hash"], arms=("Q0", "QD1", "QGR1"), repeats=3
        )):
            for ordinal, arm in enumerate(order):
                tasks.append({**common, "arm": arm, "execution_policy": arm,
                              "block": block, "ordinal_in_block": ordinal})
    path = run_root / "qgr1_force_on_execution.freeze.json"
    _write_once(path, {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_matched_execution.v1",
        "status": "FROZEN_BEFORE_ANY_QGR1_WALL_OUTCOME", "mode": "qgr1_force_on",
        "single_native_process": True, "primary_contexts_per_scale": 4,
        "tasks": tasks,
    })
    _write_once(run_root / "qgr1_force_execution.registry.json", {
        "schema_version": "lunar_ice_bpc.p0v5_qgr1_force_execution_registry.v4",
        "frozen_before_qgr1_wall": True,
        "schedule_sha256": _sha256(path),
    })
    return 0


def _export(run_root, checkpoint):
    schedule = _load(run_root / "qgr1_force_on_execution.freeze.json")
    corpus = {row["context_id"]: row for row in _load(run_root / "corpus.freeze.json")["rows"]}
    output_dir = run_root / "qgr1_force_potentials"
    output_dir.mkdir(parents=True, exist_ok=True)
    index = {}
    for context_id in sorted({row["context_id"] for row in schedule["tasks"]
                              if row["arm"] == "QGR1"}):
        context = corpus[context_id]
        output = output_dir / f"{context['state_hash']}.json"
        if not output.is_file():
            completed = subprocess.run([
                sys.executable, str(PREDICTOR), "--instance", context["instance_path"],
                "--snapshot", context["snapshot_path"], "--checkpoint", str(checkpoint),
                "--output", str(output), "--run-root", str(run_root),
            ], cwd=ROOT, check=False)
            if completed.returncode != 0:
                raise SystemExit(f"QGR1 V4 potential export failed:{context_id}")
        if str(_load(output).get("source_state_hash")) != context["state_hash"]:
            raise SystemExit("QGR1 V4 potential state binding drift")
        index[context["state_hash"]] = str(output)
    path = output_dir / "potential_index.json"
    _write_once(path, {
        "schema_version": "lunar_ice_bpc.p0v5_qgr1_potential_index.v4",
        "source_schedule_sha256": _sha256(run_root / "qgr1_force_on_execution.freeze.json"),
        "checkpoint": str(checkpoint), "checkpoint_sha256": _sha256(checkpoint),
        "by_state_hash": index,
    })
    return 0


def _run(run_root, checkpoint):
    index = run_root / "qgr1_force_potentials/potential_index.json"
    if _load(index)["checkpoint_sha256"] != _sha256(checkpoint):
        raise SystemExit("QGR1 force-on checkpoint drift")
    completed = subprocess.run([
        sys.executable, str(MATRIX), "matrix", "--run-root", str(run_root),
        "--schedule", str(run_root / "qgr1_force_on_execution.freeze.json"),
        "--potential-index", str(index), "--output", str(run_root / "qgr1_force_rows.json"),
        "--raw-dir", str(run_root / "qgr1_force_raw"),
    ], cwd=ROOT, check=False)
    if completed.returncode != 0:
        return int(completed.returncode)
    return _analyze(run_root)


def _analyze(run_root):
    config = _load(run_root / "config.freeze.json")
    rows = _load(run_root / "qgr1_force_rows.json")["rows"]
    outcomes = collapse_censor_aware_matrix(
        rows, caps_by_scale=config["execution"]["replay_caps_sec"],
        required_repeats=3, minimum_comparable_blocks=2,
    )
    by_context_arm = {(row.context_id, row.arm): row for row in outcomes}
    raw_by_context_arm = defaultdict(list)
    for row in rows:
        raw_by_context_arm[(row["context_id"], row["arm"])].append(row)
    scales = {}
    for scale in (30, 50):
        qgr1 = [row for row in outcomes if row.scale == scale and row.arm == "QGR1"]
        ratios = [float(row.ratio) for row in qgr1 if row.determined]
        residual = []
        reordered_ok = True
        scoring_ok = True
        for row in qgr1:
            qd1 = by_context_arm.get((row.context_id, "QD1"))
            if row.determined and qd1 and qd1.determined:
                residual.append(float(row.ratio) / min(1.0, float(qd1.ratio)))
            values = raw_by_context_arm[(row.context_id, "QGR1")]
            for raw in values:
                processed = max(1, int(raw.get("processed_labels") or 0))
                reordered_ok &= (
                    int(raw.get("reordered_label_hash_count") or 0) / processed
                    <= 0.15
                )
                proof = max(1.0e-12, float(raw.get("solver_wall_sec") or 0.0))
                scoring_ok &= float(raw.get("native_scoring_wall_sec") or 0.0) / proof <= 0.02
        redlines = sorted({value for row in qgr1 for value in row.correctness_redlines})
        admitted = bool(
            len(ratios) == 4 and len({row.instance_hash for row in qgr1 if row.determined}) == 4
            and geometric_mean(tuple(ratios)) < 1.0
            and len({row.instance_hash for row in qgr1 if row.beneficial}) >= 2
            and not any(value >= 1.05 for value in ratios)
            and residual and min(residual) <= 0.97
            and reordered_ok and scoring_ok and not redlines
        )
        scales[str(scale)] = {
            "admitted": admitted, "hard_veto": not admitted,
            "determined_contexts": len(ratios), "gm": geometric_mean(tuple(ratios)),
            "beneficial_instances": len({row.instance_hash for row in qgr1 if row.beneficial}),
            "maximum_ratio": max(ratios) if ratios else None,
            "minimum_qgr1_over_best_q0_qd1": min(residual) if residual else None,
            "reordered_fraction_gate": reordered_ok, "scoring_fraction_gate": scoring_ok,
            "correctness_redlines": redlines,
        }
    decision = {
        "schema_version": "lunar_ice_bpc.p0v5_qgr1_force_on_decision.v4",
        "source_rows_sha256": _sha256(run_root / "qgr1_force_rows.json"),
        "scales": scales, "hyperparameter_reselection_forbidden": True,
    }
    _write_once(run_root / "qgr1_force_on.decision.json", decision)
    if any(row["correctness_redlines"] for row in scales.values()):
        _terminal(run_root, "V4_NATIVE_TELEMETRY_REDLINE", decision)
        return 1
    _set_state(run_root, "FINAL_PORTFOLIO_ORACLE", "READY")
    print(json.dumps(decision, ensure_ascii=False, indent=2))
    return 0


def _assert_active(run_root):
    if bool(_load(run_root / "state.json").get("terminal")):
        raise SystemExit("terminal V4 chain forbids QGR1 writer")


def _set_state(run_root, stage, status):
    path = run_root / "state.json"
    value = _load(path)
    value.update({"current_stage": stage, "status": status})
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2,
                               sort_keys=True) + "\n", encoding="utf-8")


def _terminal(run_root, reason, detail):
    path = run_root / "terminal_decision.json"
    if not path.exists():
        path.write_text(json.dumps({
            "schema_version": "lunar_ice_bpc.p0v5_residual_gat_terminal.v4",
            "decision": "FAIL", "reason": reason, "detail": detail,
            "development_only": True, "deployment_authorized": False,
            "production_switch_authorized": False,
        }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    value = _load(run_root / "state.json")
    value.update({"terminal": True, "terminal_decision": str(path),
                  "current_stage": "TERMINAL", "status": "FAIL"})
    (run_root / "state.json").write_text(json.dumps(
        value, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n", encoding="utf-8")


def _write_once(path, payload):
    path = Path(path)
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != encoded:
        raise SystemExit(f"immutable QGR1 V4 artifact drift:{path}")
    if not path.exists():
        path.write_text(encoded, encoding="utf-8")


def _load(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def _sha256(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Collect admitted QGR1 supplements and apply final V4 portfolio headroom."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import verify_portfolio_freezes  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import rotate_blocked_arm_order  # noqa: E402
from lunar_ice_bpc.guidance.interaction_gat_queue_gates_v4 import (  # noqa: E402
    CensorAwareContextOutcome, collapse_censor_aware_matrix, measured_v4_oracle,
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
    if bool(_load(run_root / "state.json").get("terminal")):
        raise SystemExit("terminal V4 chain forbids portfolio writer")
    if args.mode == "freeze": return _freeze(run_root)
    if args.mode == "analyze": return _analyze(run_root)
    if args.checkpoint is None: raise SystemExit("QGR1 supplement requires checkpoint")
    if args.mode == "export": return _export(run_root, args.checkpoint.resolve())
    return _run(run_root, args.checkpoint.resolve())


def _admitted(run_root):
    path = run_root / "qgr1_force_on.decision.json"
    if not path.is_file(): return set()
    return {int(scale) for scale, row in _load(path)["scales"].items()
            if bool(row["admitted"])}


def _freeze(run_root):
    admitted = _admitted(run_root)
    config = _load(run_root / "config.freeze.json")
    milestone = _load(run_root / "q0_milestone.freeze.json")["by_context"]
    tasks = []
    for context in _load(run_root / "corpus.freeze.json")["rows"]:
        if (context["partition"] not in {"train", "calibration"}
                or int(context["scale"]) not in admitted
                or not milestone[context["context_id"]]["replay_eligible"]):
            continue
        common = {
            "context_id": context["context_id"],
            "instance_hash": context["instance_content_hash"],
            "scale": context["scale"], "partition": context["partition"],
            "state_hash": context["state_hash"],
            "cap_sec": config["execution"]["replay_caps_sec"][str(context["scale"])],
            "memory_limit_gb": config["execution"]["memory_limit_gb"],
        }
        for block, order in enumerate(rotate_blocked_arm_order(
            context["state_hash"], arms=("Q0", "QGR1"), repeats=3
        )):
            for ordinal, arm in enumerate(order):
                tasks.append({**common, "arm": arm, "execution_policy": arm,
                              "block": block, "ordinal_in_block": ordinal})
    _write_once(run_root / "matched_qgr1_supplement_execution.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_matched_execution.v1",
        "status": "FROZEN_AFTER_FORCE_ON_BEFORE_QGR1_SUPPLEMENT_OUTCOMES",
        "mode": "qgr1_supplement", "admitted_scales": sorted(admitted),
        "single_native_process": True, "tasks": tasks,
    })
    if not admitted:
        return _analyze(run_root)
    return 0


def _export(run_root, checkpoint):
    schedule_path = run_root / "matched_qgr1_supplement_execution.freeze.json"
    schedule = _load(schedule_path)
    corpus = {row["context_id"]: row for row in _load(run_root / "corpus.freeze.json")["rows"]}
    directory = run_root / "qgr1_supplement_potentials"
    directory.mkdir(parents=True, exist_ok=True)
    index = {}
    for context_id in sorted({row["context_id"] for row in schedule["tasks"]
                              if row["arm"] == "QGR1"}):
        context = corpus[context_id]
        output = directory / f"{context['state_hash']}.json"
        if not output.is_file():
            completed = subprocess.run([
                sys.executable, str(PREDICTOR), "--instance", context["instance_path"],
                "--snapshot", context["snapshot_path"], "--checkpoint", str(checkpoint),
                "--output", str(output), "--run-root", str(run_root),
            ], cwd=ROOT, check=False)
            if completed.returncode != 0:
                raise SystemExit(f"QGR1 supplement potential failed:{context_id}")
        index[context["state_hash"]] = str(output)
    _write_once(directory / "potential_index.json", {
        "schema_version": "lunar_ice_bpc.p0v5_qgr1_potential_index.v4",
        "source_schedule_sha256": _sha256(schedule_path),
        "checkpoint": str(checkpoint), "checkpoint_sha256": _sha256(checkpoint),
        "by_state_hash": index,
    })
    return 0


def _run(run_root, checkpoint):
    index = run_root / "qgr1_supplement_potentials/potential_index.json"
    if _load(index)["checkpoint_sha256"] != _sha256(checkpoint):
        raise SystemExit("QGR1 supplement checkpoint drift")
    completed = subprocess.run([
        sys.executable, str(MATRIX), "matrix", "--run-root", str(run_root),
        "--schedule", str(run_root / "matched_qgr1_supplement_execution.freeze.json"),
        "--potential-index", str(index),
        "--output", str(run_root / "matched_qgr1_supplement_rows.json"),
        "--raw-dir", str(run_root / "matched_qgr1_supplement_raw"),
    ], cwd=ROOT, check=False)
    return int(completed.returncode) if completed.returncode else _analyze(run_root)


def _analyze(run_root):
    config = _load(run_root / "config.freeze.json")
    values = []
    for raw in _load(run_root / "matched_qd1_collapsed.json")["rows"]:
        row = dict(raw); row["correctness_redlines"] = tuple(row["correctness_redlines"])
        values.append(CensorAwareContextOutcome(**row))
    supplement = run_root / "matched_qgr1_supplement_rows.json"
    if supplement.is_file():
        values.extend(collapse_censor_aware_matrix(
            _load(supplement)["rows"], caps_by_scale=config["execution"]["replay_caps_sec"],
            required_repeats=3, minimum_comparable_blocks=2,
        ))
    admitted = _admitted(run_root)
    masks = {scale: ["QD1"] + (["QGR1"] if scale in admitted else [])
             for scale in (30, 50)}
    oracle = measured_v4_oracle(
        values, admitted_arms_by_scale=masks, required_gm=0.95,
        require_scale50_mixture=True,
    )
    _write_once(run_root / "portfolio_outcomes.collapsed.json", {
        "schema_version": "lunar_ice_bpc.p0v5_censor_aware_matched_outcome.v1",
        "rows": [row.__dict__ for row in values],
    })
    _write_once(run_root / "portfolio_oracle.decision.json", oracle)
    if not oracle["passed"]:
        failed = 30 if not oracle["scales"]["30"]["passed"] else 50
        _terminal(run_root, f"NO_SCALE{failed}_GAT_PORTFOLIO_HEADROOM", oracle)
        return 1
    _set_state(run_root, "CONTEXT_INTERACTION_GAT_TRAINING", "READY")
    print(json.dumps(oracle, ensure_ascii=False, indent=2))
    return 0


def _terminal(run_root, reason, detail):
    path = run_root / "terminal_decision.json"
    if not path.exists():
        path.write_text(json.dumps({
            "schema_version": "lunar_ice_bpc.p0v5_residual_gat_terminal.v4",
            "decision": "FAIL", "reason": reason, "detail": detail,
            "development_only": True, "deployment_authorized": False,
            "production_switch_authorized": False,
        }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    state = _load(run_root / "state.json")
    state.update({"terminal": True, "terminal_decision": str(path),
                  "current_stage": "TERMINAL", "status": "FAIL"})
    (run_root / "state.json").write_text(json.dumps(
        state, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n", encoding="utf-8")


def _set_state(run_root, stage, status):
    path = run_root / "state.json"; value = _load(path)
    value.update({"current_stage": stage, "status": status})
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2,
                               sort_keys=True) + "\n", encoding="utf-8")


def _write_once(path, payload):
    path = Path(path); encoded = json.dumps(payload, ensure_ascii=False,
                                             indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != encoded:
        raise SystemExit(f"immutable V4 portfolio artifact drift:{path}")
    if not path.exists(): path.write_text(encoded, encoding="utf-8")


def _load(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def _sha256(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__": raise SystemExit(main())

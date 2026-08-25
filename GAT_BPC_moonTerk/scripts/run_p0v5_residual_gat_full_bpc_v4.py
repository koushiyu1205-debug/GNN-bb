#!/usr/bin/env python3
"""Run sequential paired development/formal full-BPC evidence for V4."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from math import ceil
import os
from pathlib import Path
import statistics
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
import scripts.run_p0v5_context_queue_portfolio_full_bpc as base  # noqa: E402
import scripts.run_p0v5_interaction_gat_full_bpc_v2 as v2  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import verify_portfolio_freezes  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import geometric_mean  # noqa: E402
from lunar_ice_bpc.guidance.interaction_gat_queue_runtime_v4 import (  # noqa: E402
    INTERACTION_GAT_EVALUATION_ENV_V4, INTERACTION_GAT_MANIFEST_ENV_V4,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_residual_gat_censor_aware_selector_v4_20260815"
BOOTSTRAP = ROOT / "scripts/run_lunar_ice_interaction_gat_acceptance_v4.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("development_e2e", "formal_full100"))
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    verify_portfolio_freezes(run_root, ROOT)
    if bool(_load(run_root / "state.json").get("terminal")):
        raise SystemExit("terminal V4 chain forbids full-BPC writer")
    config = _load(run_root / "config.freeze.json")
    manifest = run_root / "research_candidate.manifest.json"
    if not manifest.is_file(): raise SystemExit("V4 research candidate missing")
    if args.mode == "development_e2e":
        if not bool(_load(run_root / "selector_heldout.decision.json").get("passed")):
            raise SystemExit("development E2E forbidden before heldout pass")
        instances = _development_instances(run_root); repeats = 3
    else:
        if not bool(_load(run_root / "development_e2e.decision.json").get("passed")):
            raise SystemExit("formal forbidden before development E2E pass")
        instances = base._formal_instances(config); repeats = 1
    schedule = base._schedule(
        args.mode, instances, repeats=repeats, cap_sec=3600.0,
        manifest=manifest, run_root=run_root,
    )
    schedule["schema_version"] = "lunar_ice_bpc.p0v5_residual_gat_full_bpc_execution.v4"
    schedule["runtime_bootstrap"] = str(BOOTSTRAP)
    schedule["runtime_bootstrap_sha256"] = base._sha256(BOOTSTRAP)
    freeze = run_root / f"{args.mode}_execution.freeze.json"
    base._write_once(freeze, schedule)
    v2.BOOTSTRAP = BOOTSTRAP
    v2.INTERACTION_GAT_MANIFEST_ENV = INTERACTION_GAT_MANIFEST_ENV_V4
    v2.INTERACTION_GAT_EVALUATION_ENV = INTERACTION_GAT_EVALUATION_ENV_V4
    evidence = []
    output_root = run_root / args.mode
    for task in schedule["tasks"]:
        task_root = output_root / task["task_id"]
        row_path = task_root / "canonical_instance_row.json"
        if not row_path.is_file():
            v2._run_one(task, task_root, config, manifest)
            base._write_once(row_path, v2._parse_one(task_root, task, cap_sec=3600.0))
        evidence.append(_load(row_path))
    if args.mode == "development_e2e":
        payload = v2._development_payload(evidence, freeze)
        payload["schema_version"] = "lunar_ice_bpc.p0v5_residual_gat_development_e2e.v4"
        decision = _development_decision(payload)
        _write_once(run_root / "development_e2e_rows.json", payload)
        _write_once(run_root / "development_e2e.decision.json", decision)
        if not decision["passed"]:
            return _terminal(run_root, "DEVELOPMENT_E2E_FAILED", decision)
        _set_state(run_root, "FORMAL_FULL100", "READY")
    else:
        payload = v2._formal_payload(evidence, freeze)
        payload["schema_version"] = "lunar_ice_bpc.p0v5_residual_gat_formal_full100.v4"
        decision = _formal_decision(payload)
        _write_once(run_root / "formal_full100_rows.json", payload)
        _write_once(run_root / "formal_full100.decision.json", decision)
        if not decision["passed"]:
            return _terminal(run_root, decision["reason"], decision)
        _pass(run_root, decision)
    return 0


def _development_decision(payload):
    scales = payload["scales"]
    passed = bool(
        not payload["correctness_redlines"]
        and all(float(scales[str(scale)]["gm"]) < 1.0
                and scales[str(scale)]["candidate_exact_count"]
                >= scales[str(scale)]["q0_exact_count"]
                and scales[str(scale)]["activation_instances"] >= 2
                and float(scales[str(scale)]["worst_instance_median_ratio"]) <= 1.10
                and int(scales[str(scale)]["tree_model_calls"]) == 0
                for scale in (30, 50))
    )
    return {"schema_version": "lunar_ice_bpc.p0v5_residual_gat_development_decision.v4",
            "passed": passed, "reason": None if passed else "DEVELOPMENT_E2E_FAILED",
            "scales": scales, "correctness_redlines": payload["correctness_redlines"]}


def _formal_decision(payload):
    grouped = defaultdict(dict)
    for row in payload["rows"]:
        grouped[(int(row["scale"]), row["instance_hash"])][row["side"]] = row
    scales = {}; redlines = []
    for scale in (5, 10, 20, 30, 50):
        pairs = [value for (value_scale, _), value in grouped.items() if value_scale == scale]
        ratios = []; common = []; q0_exact = candidate_exact = activations = 0
        q0_par2 = []; candidate_par2 = []; counters = defaultdict(int)
        for pair in pairs:
            q0, candidate = pair["Q0"], pair["candidate"]
            q0_exact += int(q0["exact"]); candidate_exact += int(candidate["exact"])
            ratio = float(candidate["par2_wall_sec"]) / float(q0["par2_wall_sec"])
            ratios.append(ratio); q0_par2.append(float(q0["par2_wall_sec"]))
            candidate_par2.append(float(candidate["par2_wall_sec"]))
            if q0["exact"] and candidate["exact"]: common.append(ratio)
            activations += int(any(action != "Q0" and int(count) > 0
                                   for action, count in candidate["selected_action_counts"].items()))
            for key in ("manifest_reads", "torch_imports", "model_calls", "ranker_calls"):
                counters[key] += int(candidate.get(key) or 0)
            redlines.extend(q0["correctness_redlines"]); redlines.extend(candidate["correctness_redlines"])
        ordered = sorted(ratios)
        scales[str(scale)] = {
            "q0_exact": q0_exact, "candidate_exact": candidate_exact,
            "gm": geometric_mean(tuple(ratios)),
            "common_exact_gm": geometric_mean(tuple(common)),
            "q0_par2_gm": geometric_mean(tuple(q0_par2)),
            "candidate_par2_gm": geometric_mean(tuple(candidate_par2)),
            "activation_instances": activations,
            "p90_ratio": ordered[min(len(ordered) - 1, max(0, ceil(0.9 * len(ordered)) - 1))],
            "worst_ratio": max(ordered), "runtime_counters": dict(counters),
        }
    small_ok = all(
        scales[str(scale)]["q0_exact"] == 20
        and scales[str(scale)]["candidate_exact"] == 20
        and scales[str(scale)]["gm"] <= 1.01
        and all(scales[str(scale)]["runtime_counters"].get(key, 0) == 0
                for key in ("manifest_reads", "torch_imports", "model_calls", "ranker_calls"))
        for scale in (5, 10, 20)
    )
    large_ok = bool(
        scales["30"]["candidate_exact"] == 20
        and scales["30"]["common_exact_gm"] < 1.0
        and scales["30"]["candidate_par2_gm"] <= scales["30"]["q0_par2_gm"]
        and scales["50"]["candidate_exact"] >= max(15, scales["50"]["q0_exact"])
        and scales["50"]["common_exact_gm"] < 1.0
        and scales["50"]["candidate_par2_gm"] <= scales["50"]["q0_par2_gm"]
        and all(scales[str(scale)]["activation_instances"] >= 5
                and scales[str(scale)]["p90_ratio"] <= 1.05
                and scales[str(scale)]["worst_ratio"] <= 1.20 for scale in (30, 50))
    )
    passed = bool(small_ok and large_ok and not redlines)
    small_model_calls = any(
        scales[str(scale)]["runtime_counters"].get(key, 0)
        for scale in (5, 10, 20)
        for key in ("manifest_reads", "torch_imports", "model_calls", "ranker_calls")
    )
    reason = None if passed else (
        "FORMAL_SMALL_SCALE_MODEL_CALL" if small_model_calls
        else "FORMAL_FULL100_FAILED"
    )
    return {"schema_version": "lunar_ice_bpc.p0v5_residual_gat_formal_decision.v4",
            "passed": passed, "reason": reason, "scales": scales,
            "correctness_redlines": sorted(set(redlines)),
            "strong_speedup": all(scales[str(scale)]["common_exact_gm"] <= 0.95
                                  for scale in (30, 50)),
            "production_review_authorized": False}


def _development_instances(run_root):
    values = {}
    for row in _load(run_root / "corpus.freeze.json")["rows"]:
        if row["partition"] == "development_e2e":
            values[row["instance_content_hash"]] = {
                "scale": row["scale"], "instance_path": row["instance_path"],
                "instance_content_hash": row["instance_content_hash"],
            }
    rows = list(values.values())
    if {scale: sum(row["scale"] == scale for row in rows) for scale in (30, 50)} != {30: 3, 50: 3}:
        raise SystemExit("V4 E2E split is not 3+3")
    return rows


def _terminal(run_root, reason, detail):
    path = run_root / "terminal_decision.json"
    if not path.exists(): path.write_text(json.dumps({
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_terminal.v4",
        "decision": "FAIL", "reason": reason, "detail": detail,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _set_state(run_root, "TERMINAL", "FAIL", terminal=True, decision=path); return 1


def _pass(run_root, detail):
    path = run_root / "terminal_decision.json"
    _write_once(path, {"schema_version": "lunar_ice_bpc.p0v5_residual_gat_terminal.v4",
                       "decision": "PASS", "reason": "FORMAL_FULL100_PASSED",
                       "detail": detail, "development_only": True,
                       "deployment_authorized": False,
                       "production_switch_authorized": False})
    _set_state(run_root, "TERMINAL", "PASS", terminal=True, decision=path)


def _set_state(run_root, stage, status, *, terminal=False, decision=None):
    path = run_root / "state.json"; value = _load(path)
    value.update({"current_stage": stage, "status": status, "terminal": terminal})
    if decision: value["terminal_decision"] = str(decision)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def _write_once(path, payload):
    path = Path(path); encoded = json.dumps(payload, ensure_ascii=False,
                                             indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != encoded:
        raise SystemExit(f"immutable V4 full-BPC artifact drift:{path}")
    if not path.exists(): path.parent.mkdir(parents=True, exist_ok=True); path.write_text(encoded, encoding="utf-8")


def _load(path): return json.loads(Path(path).read_text(encoding="utf-8"))


if __name__ == "__main__": raise SystemExit(main())

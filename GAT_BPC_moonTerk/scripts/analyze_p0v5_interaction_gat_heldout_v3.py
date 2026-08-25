#!/usr/bin/env python3
"""One-shot instance-first heldout decision for the frozen V3 models."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from statistics import median
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import verify_portfolio_freezes  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import collapse_matched_matrix  # noqa: E402
from lunar_ice_bpc.guidance.interaction_gat_queue_gates_v3 import (  # noqa: E402
    assess_v3_heldout_advantage, summarize_selected_actions_instance_first,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v3_20260814"
MODEL_KINDS = ("gat", "mlp", "linear", "no_message", "shuffled_topology")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    verify_portfolio_freezes(run_root, ROOT)
    if bool(_load(run_root / "state.json").get("terminal")):
        raise SystemExit("terminal V3 chain forbids heldout analyzer")
    config = _load(run_root / "config.freeze.json")
    action_path = run_root / "selector_heldout_actions.freeze.json"
    action_freeze = _load(action_path)
    outcome_path = run_root / "selector_heldout_matched_rows.json"
    raw = _load(outcome_path)["rows"]
    collapsed = collapse_matched_matrix(
        raw, caps_by_scale=config["execution"]["replay_caps_sec"], required_repeats=3
    )
    by_pair = {(row.context_id, row.arm): row for row in collapsed}
    q0_medians = _q0_medians(raw)
    summaries = {}
    selected_rows_by_model = {}
    for kind in MODEL_KINDS:
        selected_rows = []
        for context in action_freeze["rows"]:
            action_info = context["actions"][kind]
            action = str(action_info["action"])
            preparation_sec = float(action_info["total_preparation_ms"]) / 1000.0
            if action == "Q0":
                ratio = (q0_medians[context["context_id"]] + preparation_sec) / q0_medians[context["context_id"]]
                outcome = None
            else:
                outcome = by_pair.get((context["context_id"], action))
                ratio = (
                    None if outcome is None or not outcome.determined else
                    float(outcome.ratio) + preparation_sec / q0_medians[context["context_id"]]
                )
            selected_rows.append({
                "context_id": context["context_id"],
                "instance_hash": context["instance_hash"], "scale": context["scale"],
                "selected_action": action, "net_ratio": ratio,
                "adverse": bool(outcome and outcome.adverse),
                "censored": bool(action != "Q0" and (outcome is None or not outcome.determined)),
                "correctness_redlines": (
                    list(outcome.correctness_redlines) if outcome else []
                ),
            })
        selected_rows_by_model[kind] = selected_rows
        summaries[kind] = summarize_selected_actions_instance_first(selected_rows)
    warm_gat = [
        float(row["actions"]["gat"]["graph_build_ms"])
        + float(row["actions"]["gat"]["tensorization_ms"])
        + float(row["actions"]["gat"]["inference_ms"])
        for row in action_freeze["rows"]
    ]
    warm_p99 = _percentile(warm_gat, 0.99)
    gate = assess_v3_heldout_advantage(summaries, preparation_p99_ms=warm_p99)
    decision = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_heldout_decision.v3",
        "source_actions": str(action_path), "source_actions_sha256": _sha256(action_path),
        "source_outcomes": str(outcome_path), "source_outcomes_sha256": _sha256(outcome_path),
        "all_models_shared_matched_arm_outcomes": True,
        "first_checkpoint_load_included_in_net_wall": True,
        "warm_graph_tensorization_inference_p99_ms": warm_p99,
        "summaries": summaries, "selected_rows": selected_rows_by_model,
        "gate": gate,
    }
    if not gate["passed"]:
        _write_once(run_root / "selector_heldout.decision.json", decision)
        _terminal(run_root, gate["terminal_reason"], decision)
        return 2
    heldout_manifest = run_root / "selector_heldout_candidate.manifest.json"
    research_manifest = run_root / "research_candidate.manifest.json"
    _write_once(research_manifest, _load(heldout_manifest))
    decision["research_candidate_manifest"] = str(research_manifest)
    decision["research_candidate_manifest_sha256"] = _sha256(research_manifest)
    _write_once(run_root / "selector_heldout.decision.json", decision)
    _set_state(run_root, "DEVELOPMENT_E2E", "READY")
    print(json.dumps(decision, ensure_ascii=False, indent=2))
    return 0


def _q0_medians(rows):
    grouped = defaultdict(list)
    for row in rows:
        if row["arm"] == "Q0" and row["status"] == "COMPLETED":
            grouped[row["context_id"]].append(float(row["solver_wall_sec"]))
    if any(len(values) != 3 for values in grouped.values()):
        raise SystemExit("heldout requires three completed Q0 repeats per context")
    return {key: median(values) for key, values in grouped.items()}


def _percentile(values, quantile):
    ordered = sorted(values)
    if not ordered: return 0.0
    index = min(len(ordered) - 1, int((len(ordered) - 1) * quantile + 0.999999))
    return ordered[index]


def _set_state(run_root, stage, status):
    path = run_root / "state.json"; state = _load(path)
    state.update({"current_stage": stage, "status": status})
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _terminal(run_root, reason, detail):
    _write_once(run_root / "terminal_decision.json", {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_terminal.v3",
        "decision": "FAIL", "reason": reason, "detail": detail,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    })
    path = run_root / "state.json"; state = _load(path)
    state.update({"current_stage": "TERMINAL", "status": "FAIL", "terminal": True,
                  "terminal_decision": reason})
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_once(path, payload):
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != encoded:
        raise SystemExit(f"immutable V3 heldout decision differs:{path}")
    if not path.exists(): path.write_text(encoded, encoding="utf-8")


def _load(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def _sha256(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__": raise SystemExit(main())

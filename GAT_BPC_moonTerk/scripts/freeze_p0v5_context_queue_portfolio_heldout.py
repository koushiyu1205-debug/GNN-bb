#!/usr/bin/env python3
"""Freeze one fresh selector action per heldout context before wall outcomes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import (  # noqa: E402
    rotate_blocked_arm_order,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_context_queue_portfolio_v1_20260807_r1"
PREDICTOR = ROOT / "scripts/predict_p0v5_context_queue_portfolio_action.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    oracle = _load(run_root / "portfolio_oracle.decision.json")["decision"]
    if not bool(oracle.get("selector_training_authorized")):
        raise SystemExit("heldout selection forbidden before portfolio headroom")
    selection = _load(run_root / "selector_selection.decision.json")
    if not bool(selection.get("selector_frozen")):
        raise SystemExit("unique selector is not frozen")
    manifest = Path(selection["research_candidate_manifest"]).resolve()
    if _sha256(manifest) != _sha256(run_root / "research_candidate.manifest.json"):
        raise SystemExit("research candidate manifest binding drift")
    config = _load(run_root / "config.freeze.json")
    corpus = _load(run_root / "corpus.freeze.json")
    contexts = [
        dict(row) for row in corpus["rows"]
        if row["partition"] == "selector_heldout"
    ]
    if len({row["instance_content_hash"] for row in contexts}) != 6:
        raise SystemExit("heldout corpus must contain 3+3 distinct instances")
    decision_dir = run_root / "heldout_action_predictions"
    potential_dir = run_root / "heldout_qgr1_potentials"
    decisions, potential_index = [], {}
    for context in contexts:
        decision_path = decision_dir / f"{context['context_id']}.json"
        potential_path = potential_dir / f"{context['state_hash']}.json"
        if not decision_path.is_file():
            completed = subprocess.run([
                sys.executable, str(PREDICTOR),
                "--instance", str(context["instance_path"]),
                "--snapshot", str(context["snapshot_path"]),
                "--manifest", str(manifest),
                "--output", str(decision_path),
                "--potential-output", str(potential_path),
                "--run-root", str(run_root),
            ], cwd=ROOT, check=False)
            if completed.returncode != 0:
                raise SystemExit(f"fresh heldout selector failed:{context['context_id']}")
        decision = _load(decision_path)
        if (
            decision["instance_content_hash"] != context["instance_content_hash"]
            or decision["state_hash"] != context["state_hash"]
        ):
            raise SystemExit("heldout selector decision binding drift")
        decision.update({
            "context_id": context["context_id"],
            "scale": context["scale"],
            "decision_path": str(decision_path),
            "decision_sha256": _sha256(decision_path),
        })
        decisions.append(decision)
        if decision["selected_action"] == "QGR1":
            potential_index[context["state_hash"]] = decision["potential_path"]
    potential_payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qgr1_potential_index.v1",
        "mode": "selector_heldout",
        "frozen_before_corresponding_outcomes": True,
        "by_state_hash": dict(sorted(potential_index.items())),
    }
    potential_index_path = run_root / "heldout_potential_index.freeze.json"
    _write_once(potential_index_path, potential_payload)
    by_context = {row["context_id"]: row for row in contexts}
    tasks = []
    repeats = int(config["execution"]["blocked_fresh_process_repeats"])
    for decision in decisions:
        context = by_context[decision["context_id"]]
        action = str(decision["selected_action"])
        candidate_label = action if action != "Q0" else "Q0_SELECTED"
        for block, order in enumerate(rotate_blocked_arm_order(
            context["state_hash"], arms=("Q0", candidate_label), repeats=repeats
        )):
            for ordinal, arm in enumerate(order):
                candidate = arm != "Q0"
                tasks.append({
                    "context_id": context["context_id"],
                    "instance_content_hash": context["instance_content_hash"],
                    "scale": context["scale"], "partition": context["partition"],
                    "state_hash": context["state_hash"],
                    "block": block, "ordinal_in_block": ordinal,
                    "arm": arm,
                    "execution_policy": action if candidate else "Q0",
                    "selected_action": action,
                    "preparation_wall_sec": (
                        float(decision["preparation_wall_sec"]) if candidate else 0.0
                    ),
                    "cap_sec": float(config["execution"]["replay_caps_sec"][str(context["scale"])]),
                    "memory_limit_gb": float(config["execution"]["memory_limit_gb"]),
                    "fresh_process": True,
                })
    schedule = {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_matched_execution.v1",
        "mode": "selector_heldout",
        "status": "FROZEN_ONE_SHOT_BEFORE_HELDOUT_WALL_OUTCOMES",
        "selector_reselection_after_outcome_forbidden": True,
        "manifest": str(manifest), "manifest_sha256": _sha256(manifest),
        "potential_index": str(potential_index_path),
        "potential_index_sha256": _sha256(potential_index_path),
        "decisions": decisions,
        "tasks": tasks,
    }
    _write_once(run_root / "heldout_execution.freeze.json", schedule)
    _update_state(run_root, "SELECTOR_HELDOUT_FRESH", "READY")
    print(json.dumps({
        "context_count": len(contexts),
        "action_counts": {
            action: sum(row["selected_action"] == action for row in decisions)
            for action in ("Q0", "QD1", "QB1", "QGR1")
        },
        "task_count": len(tasks),
    }, ensure_ascii=False, indent=2))
    return 0


def _update_state(run_root, stage, status):
    path = run_root / "state.json"
    payload = _load(path)
    payload.update({"current_stage": stage, "status": status})
    path.write_text(json.dumps(
        payload, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n", encoding="utf-8")


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_once(path, payload):
    path = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable heldout freeze drift:{path}")
    if not path.exists():
        path.write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

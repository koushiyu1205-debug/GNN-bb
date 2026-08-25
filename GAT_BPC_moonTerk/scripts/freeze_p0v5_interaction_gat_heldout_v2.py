#!/usr/bin/env python3
"""Freeze five-model heldout decisions and a distinct-action replay schedule."""

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


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v2_20260807"
PREDICTOR = ROOT / "scripts/predict_p0v5_interaction_gat_heldout_action_v2.py"
VARIANTS = ("gat", "mlp", "linear", "no_message", "shuffled_topology")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    state = _load(run_root / "state.json")
    if bool(state.get("terminal")):
        raise SystemExit("terminal chain forbids heldout prediction")
    selection = _load(run_root / "selector_selection.decision.json")
    if (
        selection.get("decision") != "GAT_CANDIDATE_FROZEN"
        or selection.get("selected_model_kind") != "gat"
    ):
        raise SystemExit("heldout requires the uniquely frozen GAT candidate")
    manifest = run_root / "selector_heldout_candidate.manifest.json"
    if Path(selection["heldout_manifest"]).resolve() != manifest.resolve():
        raise SystemExit("heldout manifest path drift")
    manifest_payload = _load(manifest)
    if (
        str(manifest_payload.get("selector_checkpoint_sha256"))
        != str(selection["selected_checkpoint_sha256"])
    ):
        raise SystemExit("heldout manifest/checkpoint hash drift")
    config = _load(run_root / "config.freeze.json")
    corpus = _load(run_root / "corpus.freeze.json")
    contexts = [
        dict(row) for row in corpus["rows"]
        if row["partition"] == "selector_heldout"
    ]
    for scale in (30, 50):
        selected = [row for row in contexts if int(row["scale"]) == scale]
        if len(selected) != 8 or len({row["instance_content_hash"] for row in selected}) != 4:
            raise SystemExit(f"V2 heldout scale{scale} must be 8 contexts/4 instances")
    prediction_dir = run_root / "heldout_action_predictions"
    potential_dir = run_root / "heldout_qgr1_potentials"
    decisions = []
    potential_index = {}
    for context in sorted(contexts, key=lambda row: str(row["context_id"])):
        variants = {}
        potential_path = potential_dir / f"{context['state_hash']}.json"
        for variant in VARIANTS:
            output = prediction_dir / f"{context['context_id']}.{variant}.json"
            if not output.is_file():
                command = [
                    sys.executable, str(PREDICTOR),
                    "--instance", str(context["instance_path"]),
                    "--snapshot", str(context["snapshot_path"]),
                    "--manifest", str(manifest),
                    "--variant", variant,
                    "--output", str(output),
                    "--potential-output", str(potential_path),
                    "--run-root", str(run_root),
                ]
                completed = subprocess.run(command, cwd=ROOT, check=False)
                if completed.returncode != 0:
                    raise SystemExit(
                        f"fresh V2 heldout prediction failed:{context['context_id']}:{variant}"
                    )
            row = _load(output)
            if (
                row["variant"] != variant
                or row["instance_content_hash"] != context["instance_content_hash"]
                or row["state_hash"] != context["state_hash"]
            ):
                raise SystemExit("V2 heldout prediction binding drift")
            variants[variant] = {
                **row,
                "prediction_path": str(output),
                "prediction_sha256": _sha256(output),
            }
            if row["selected_action"] == "QGR1":
                if not potential_path.is_file() or _sha256(potential_path) != row["potential_sha256"]:
                    raise SystemExit("V2 heldout QGR1 potential binding drift")
                potential_index[context["state_hash"]] = str(potential_path)
        decisions.append({
            "context_id": context["context_id"],
            "instance_content_hash": context["instance_content_hash"],
            "scale": context["scale"],
            "state_hash": context["state_hash"],
            "variants": variants,
        })
    potential_payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qgr1_potential_index.v1",
        "mode": "interaction_gat_selector_heldout",
        "frozen_before_corresponding_outcomes": True,
        "by_state_hash": dict(sorted(potential_index.items())),
    }
    potential_index_path = run_root / "heldout_potential_index.freeze.json"
    _write_once(potential_index_path, potential_payload)
    by_context = {row["context_id"]: row for row in contexts}
    repeats = int(config["execution"]["blocked_fresh_process_repeats"])
    tasks = []
    for decision in decisions:
        context = by_context[decision["context_id"]]
        distinct = tuple(sorted({
            "Q0",
            *(str(row["selected_action"]) for row in decision["variants"].values()),
        }))
        for block, order in enumerate(rotate_blocked_arm_order(
            context["state_hash"], arms=distinct, repeats=repeats
        )):
            for ordinal, action in enumerate(order):
                tasks.append({
                    "context_id": context["context_id"],
                    "instance_content_hash": context["instance_content_hash"],
                    "scale": context["scale"],
                    "partition": context["partition"],
                    "state_hash": context["state_hash"],
                    "block": block,
                    "ordinal_in_block": ordinal,
                    "arm": action,
                    "execution_policy": action,
                    "selected_action": action,
                    # Model-specific preparation is applied by the heldout
                    # analyzer, so each distinct solver action is run only once.
                    "preparation_wall_sec": 0.0,
                    "cap_sec": float(config["execution"]["replay_caps_sec"][str(context["scale"])]),
                    "memory_limit_gb": float(config["execution"]["memory_limit_gb"]),
                    "fresh_process": True,
                })
    milestone_tasks = [{
        "context_id": context["context_id"],
        "instance_content_hash": context["instance_content_hash"],
        "scale": context["scale"],
        "partition": context["partition"],
        "state_hash": context["state_hash"],
        "arm": "Q0",
        "execution_policy": "Q0",
        "cap_sec": float(config["execution"]["replay_caps_sec"][str(context["scale"])]),
        "memory_limit_gb": float(config["execution"]["memory_limit_gb"]),
        "fresh_process": True,
    } for context in sorted(contexts, key=lambda row: str(row["context_id"]))]
    schedule = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_heldout_execution.v2",
        "mode": "selector_heldout",
        "status": "FROZEN_ONE_SHOT_BEFORE_HELDOUT_WALL_OUTCOMES",
        "all_models_frozen_before_heldout": True,
        "selector_reselection_after_outcome_forbidden": True,
        "manifest": str(manifest),
        "manifest_sha256": _sha256(manifest),
        "controls_freeze": str(run_root / "selector_controls.freeze.json"),
        "controls_freeze_sha256": _sha256(run_root / "selector_controls.freeze.json"),
        "potential_index": str(potential_index_path),
        "potential_index_sha256": _sha256(potential_index_path),
        "decisions": decisions,
        "milestone_tasks": milestone_tasks,
        "tasks": tasks,
    }
    _write_once(run_root / "heldout_execution.freeze.json", schedule)
    _update_state(run_root, "SELECTOR_HELDOUT_FRESH", "READY")
    print(json.dumps({
        "context_count": len(contexts),
        "prediction_count": len(contexts) * len(VARIANTS),
        "distinct_action_task_count": len(tasks),
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
        raise SystemExit(f"immutable V2 heldout freeze drift:{path}")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

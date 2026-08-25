#!/usr/bin/env python3
"""Run the one-shot heldout union after all five actions are frozen."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
import scripts.run_p0v5_context_queue_portfolio_matrix as generic  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import verify_portfolio_freezes  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import rotate_blocked_arm_order  # noqa: E402


REPLAY = ROOT / "scripts/replay_p0v5_qg2_label_state_snapshot.py"
DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v3_20260814"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--potential-index", type=Path)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    verify_portfolio_freezes(run_root, ROOT)
    if bool(_load(run_root / "state.json").get("terminal")):
        raise SystemExit("terminal V3 chain forbids heldout replay")
    action_path = run_root / "selector_heldout_actions.freeze.json"
    action_freeze = _load(action_path)
    if int(action_freeze.get("heldout_outcomes_read") or 0) != 0:
        raise SystemExit("heldout action freeze is outcome contaminated")
    corpus = _load(run_root / "corpus.freeze.json")
    by_context = {row["context_id"]: row for row in corpus["rows"]}
    config = _load(run_root / "config.freeze.json")
    potential = (
        {} if args.potential_index is None
        else dict(_load(args.potential_index.resolve()).get("by_state_hash") or {})
    )
    schedule = _schedule(action_freeze, config)
    schedule_path = run_root / "selector_heldout_execution.freeze.json"
    _write_once(schedule_path, schedule)
    raw_dir = run_root / "selector_heldout_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    targets = {}
    # The milestone screen occurs only after action freeze and is never fed
    # back to any model or threshold.
    for row in action_freeze["rows"]:
        context = by_context[row["context_id"]]
        raw_path = raw_dir / f"{row['context_id']}_milestone_Q0.json"
        if not raw_path.is_file():
            _run_replay(context, raw_path, "Q0", 0, config, None)
        raw = _load(raw_path)
        _validate_binding(raw, context)
        targets[row["context_id"]] = (
            str(raw["milestone_kind"]) if bool(raw["milestone_reached"])
            else "ANY_VALID_TERMINAL_MILESTONE"
        )
    canonical = []
    for task in schedule["tasks"]:
        context = by_context[task["context_id"]]
        raw_path = raw_dir / (
            f"{task['context_id']}_b{task['block']}_{task['ordinal_in_block']}_{task['arm']}.json"
        )
        ranker = potential.get(str(task["state_hash"])) if task["arm"] == "QGR1" else None
        if task["arm"] == "QGR1" and not ranker:
            raise SystemExit(f"heldout QGR1 potential missing:{task['state_hash']}")
        if not raw_path.is_file():
            _run_replay(
                context, raw_path, task["arm"], int(task["block"]) + 1,
                config, ranker,
            )
        raw = _load(raw_path)
        _validate_binding(raw, context)
        canonical.append(_canonical(task, context, raw, raw_path, targets[task["context_id"]]))
    generic._add_cross_arm_redlines(canonical)
    result = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_heldout_matched_rows.v3",
        "source_actions": str(action_path),
        "source_actions_sha256": _sha256(action_path),
        "source_schedule": str(schedule_path),
        "source_schedule_sha256": _sha256(schedule_path),
        "milestone_screen_not_used_by_models": True,
        "rows": canonical,
    }
    _write_once(run_root / "selector_heldout_matched_rows.json", result)
    _set_state(run_root, "HELDOUT_DECISION", "READY")
    print(json.dumps({"tasks": len(canonical), "single_native_process": True}, indent=2))
    return 0


def _schedule(action_freeze, config):
    tasks = []
    for row in action_freeze["rows"]:
        arms = tuple(row["distinct_action_union"])
        if "Q0" not in arms:
            raise SystemExit("heldout union lacks Q0")
        # The generic helper requires Q0 first; schedule each arm exactly once
        # per block while rotating order by frozen state hash.
        ordered = ("Q0", *sorted(set(arms) - {"Q0"}))
        for block, order in enumerate(rotate_blocked_arm_order(
            row["state_hash"], arms=ordered, repeats=3
        )):
            for ordinal, arm in enumerate(order):
                tasks.append({
                    "context_id": row["context_id"], "instance_hash": row["instance_hash"],
                    "scale": int(row["scale"]), "state_hash": row["state_hash"],
                    "arm": arm, "block": block, "ordinal_in_block": ordinal,
                    "cap_sec": float(config["execution"]["replay_caps_sec"][str(row["scale"])]),
                    "memory_limit_gb": float(config["execution"]["memory_limit_gb"]),
                })
    return {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_heldout_execution.v3",
        "status": "FROZEN_BEFORE_ANY_SELECTOR_HELDOUT_ARM_OUTCOME",
        "blocked_fresh_process_repeats": 3, "single_native_process": True,
        "tasks": tasks,
    }


def _run_replay(context, output, arm, repeat, config, ranker):
    command = [
        sys.executable, str(REPLAY), "--instance", str(context["instance_path"]),
        "--snapshot", str(context["snapshot_path"]), "--output", str(output),
        "--policy", arm, "--repeat-index", str(repeat),
        "--wall-time-limit-sec", str(config["execution"]["replay_caps_sec"][str(context["scale"])]),
        "--memory-limit-gb", str(config["execution"]["memory_limit_gb"]),
    ]
    if arm == "QGR1":
        command.extend(["--potential", str(Path(ranker).resolve()), "--guidance-bucket-width", "0.0001"])
    environment = dict(os.environ)
    native = str((ROOT / config["native_build_dir"]).resolve())
    source = str((ROOT / "src").resolve())
    environment["PYTHONPATH"] = os.pathsep.join(
        value for value in (native, source, environment.get("PYTHONPATH", "")) if value
    )
    for key in tuple(environment):
        if key.startswith("LUNAR_ICE_P0V5_") or key.startswith("LUNAR_ICE_PROOF_TAIL_GAT"):
            environment.pop(key, None)
    completed = subprocess.run(command, cwd=ROOT, env=environment, check=False)
    if completed.returncode != 0:
        raise SystemExit(f"heldout fresh replay failed:{completed.returncode}")


def _canonical(task, context, raw, raw_path, target):
    reached = bool(raw["milestone_reached"] and (
        str(raw["milestone_kind"]) == target or target == "ANY_VALID_TERMINAL_MILESTONE"
    ))
    status = "COMPLETED" if reached else (
        str(raw["engine_status"]) if str(raw["engine_status"]) in {"TIMEOUT", "MEMORY_LIMIT"}
        else "CENSORED"
    )
    redlines = generic._correctness_redlines(raw, context)
    return {
        "context_id": task["context_id"], "instance_hash": context["instance_content_hash"],
        "scale": int(context["scale"]), "partition": "selector_heldout",
        "state_hash": context["state_hash"], "arm": task["arm"],
        "repeat": task["block"], "block": task["block"],
        "ordinal_in_block": task["ordinal_in_block"], "status": status,
        "wall_sec": float(raw["milestone_wall_sec"]), "solver_wall_sec": float(raw["milestone_wall_sec"]),
        "milestone_reached": reached, "target_milestone_kind": target,
        "observed_milestone_kind": str(raw["milestone_kind"]),
        "fresh_process": True, "correctness_audit_complete": True,
        "correctness_redlines": sorted(set(redlines)), "raw_path": str(raw_path),
        "raw_sha256": _sha256(raw_path),
    }


def _validate_binding(raw, context):
    if (
        str(raw.get("state_hash")) != str(context["state_hash"])
        or str(raw.get("instance_content_hash")) != str(context["instance_content_hash"])
    ):
        raise SystemExit("heldout replay binding drift")


def _set_state(run_root, stage, status):
    path = run_root / "state.json"
    state = _load(path); state.update({"current_stage": stage, "status": status})
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_once(path, payload):
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != encoded:
        raise SystemExit(f"immutable V3 heldout replay artifact differs:{path}")
    if not path.exists(): path.write_text(encoded, encoding="utf-8")


def _load(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def _sha256(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__": raise SystemExit(main())

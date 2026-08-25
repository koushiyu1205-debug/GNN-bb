#!/usr/bin/env python3
"""Execute heldout Q0 milestones and frozen distinct arms sequentially."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
import scripts.run_p0v5_context_queue_portfolio_matrix as replay  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v2_20260807"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    if bool(_load(run_root / "state.json").get("terminal")):
        raise SystemExit("terminal chain forbids heldout replay")
    schedule_path = run_root / "heldout_execution.freeze.json"
    schedule = _load(schedule_path)
    if schedule.get("schema_version") != "lunar_ice_bpc.p0v5_interaction_gat_heldout_execution.v2":
        raise SystemExit("V2 heldout execution schema mismatch")
    if not bool(schedule.get("all_models_frozen_before_heldout")):
        raise SystemExit("V2 heldout models were not frozen before outcomes")
    config = _load(run_root / "config.freeze.json")
    corpus = _load(run_root / "corpus.freeze.json")
    contexts = {
        str(row["context_id"]): dict(row) for row in corpus["rows"]
        if row["partition"] == "selector_heldout"
    }
    if set(contexts) != {str(row["context_id"]) for row in schedule["decisions"]}:
        raise SystemExit("heldout schedule/corpus context drift")
    milestone_rows = _run_milestones(run_root, schedule, contexts, config)
    milestone_path = run_root / "heldout_q0_milestone.freeze.json"
    _write_once(milestone_path, {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_heldout_q0_milestone.v2",
        "status": "FROZEN_AFTER_GAT_AND_CONTROLS_BEFORE_DISTINCT_ARM_OUTCOMES",
        "heldout_models_already_frozen": True,
        "execution_freeze_sha256": _sha256(schedule_path),
        "by_context": {row["context_id"]: row for row in milestone_rows},
    })
    rows = _run_distinct_arms(
        run_root, schedule, contexts, config, _load(milestone_path)["by_context"]
    )
    replay._add_cross_arm_redlines(rows)
    output = run_root / "heldout_distinct_action_rows.json"
    _write_once(output, {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_heldout_distinct_action_rows.v2",
        "source_schedule": str(schedule_path),
        "source_schedule_sha256": _sha256(schedule_path),
        "source_milestone": str(milestone_path),
        "source_milestone_sha256": _sha256(milestone_path),
        "rows": rows,
    })
    _update_state(run_root, "HELDOUT_DECISION", "READY")
    print(json.dumps({
        "milestone_context_count": len(milestone_rows),
        "distinct_action_task_count": len(rows),
        "single_native_process": True,
        "output": str(output),
    }, ensure_ascii=False, indent=2))
    return 0


def _run_milestones(run_root, schedule, contexts, config):
    raw_dir = run_root / "heldout_q0_milestone_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for frozen in schedule["milestone_tasks"]:
        task = dict(frozen)
        context = contexts[str(task["context_id"])]
        raw_path = raw_dir / f"{task['context_id']}_q0.json"
        if not raw_path.is_file():
            command = [
                sys.executable, str(replay.REPLAY),
                "--instance", str(context["instance_path"]),
                "--snapshot", str(context["snapshot_path"]),
                "--output", str(raw_path),
                "--policy", "Q0", "--repeat-index", "0",
                "--wall-time-limit-sec", str(task["cap_sec"]),
                "--memory-limit-gb", str(task["memory_limit_gb"]),
            ]
            replay._run_one(command, config)
        raw = _load(raw_path)
        replay._validate_raw_binding(raw, task, context)
        rows.append(replay._milestone_row(task, context, raw, raw_path))
    return rows


def _run_distinct_arms(run_root, schedule, contexts, config, milestones):
    potentials = dict(_load(Path(schedule["potential_index"]))["by_state_hash"])
    raw_dir = run_root / "heldout_distinct_action_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for task in schedule["tasks"]:
        task = dict(task)
        context = contexts[str(task["context_id"])]
        action = str(task["arm"])
        raw_path = raw_dir / (
            f"{task['context_id']}_b{int(task['block'])}_"
            f"{int(task['ordinal_in_block'])}_{action}.json"
        )
        if not raw_path.is_file():
            command = [
                sys.executable, str(replay.REPLAY),
                "--instance", str(context["instance_path"]),
                "--snapshot", str(context["snapshot_path"]),
                "--output", str(raw_path),
                "--policy", action,
                "--repeat-index", str(int(task["block"]) + 1),
                "--wall-time-limit-sec", str(task["cap_sec"]),
                "--memory-limit-gb", str(task["memory_limit_gb"]),
            ]
            if action == "QGR1":
                potential = potentials.get(str(task["state_hash"]))
                if not potential:
                    raise SystemExit("heldout QGR1 potential missing")
                command.extend([
                    "--potential", str(Path(potential).resolve()),
                    "--guidance-bucket-width", "0.0001",
                ])
            replay._run_one(command, config)
        raw = _load(raw_path)
        replay._validate_raw_binding(raw, task, context)
        rows.append(replay._matrix_row(
            task, context, raw, raw_path, milestones[str(task["context_id"])]
        ))
    return rows


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
        raise SystemExit(f"immutable V2 heldout replay artifact drift:{path}")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Collect all V4 root contexts on the new engine and freeze the fresh corpus."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_residual_gat_censor_aware_selector_v4_20260815"
SNAPSHOT_ENV = "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR"
SNAPSHOT_CAP_ENV = "LUNAR_ICE_P0V5_QG2_SNAPSHOT_MAX_PER_INSTANCE"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("collect", "freeze"))
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    _verify_prearm(run_root)
    _assert_active(run_root)
    config = _load(run_root / "config.freeze.json")
    schedule = _load(run_root / "root_collection.execution.freeze.json")
    snapshot_dir = run_root / "fresh_root_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    if args.mode == "collect":
        for task in schedule["tasks"]:
            _collect_one(run_root, config, snapshot_dir, task)
    _freeze_corpus(run_root, config, schedule, snapshot_dir)
    return 0


def _collect_one(run_root, config, snapshot_dir, task):
    output = run_root / "fresh_root_runs" / (
        f"scale{int(task['scale'])}_{task['instance_content_hash']}"
    )
    done = output / "canonical_result.json"
    if done.is_file():
        return
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"partial V4 root run requires audit:{output}")
    command = [
        sys.executable, str(ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"),
        "--config", str(Path(config["selected_exact_config"]).resolve()),
        "--scales", str(int(task["scale"])),
        "--instance", str(Path(task["instance_path"]).resolve()),
        "--limit", "1", "--output-dir", str(output), "--no-resume",
        "--route-opportunity-collection-only-root-pool",
        "--route-opportunity-collection-root-pool-time-cap-sec", str(task["cap_sec"]),
    ]
    completed = subprocess.run(
        command, cwd=ROOT,
        env=_environment(config, snapshot_dir, int(task["snapshot_cap"])),
        check=False,
    )
    if completed.returncode not in {0, 1}:
        raise SystemExit(f"fresh V4 root collection failed:{task['instance_content_hash']}")
    # The acceptance runner does not promise a single filename across exact
    # statuses.  A marker records process completion without inventing a solve
    # outcome; the snapshot index remains the sole eligibility input.
    output.mkdir(parents=True, exist_ok=True)
    _write_once(done, {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_root_run_marker.v4",
        "instance_content_hash": task["instance_content_hash"],
        "returncode": completed.returncode, "q0_only": True,
    })


def _freeze_corpus(run_root, config, schedule, snapshot_dir):
    task_by_hash = {str(row["instance_content_hash"]): row for row in schedule["tasks"]}
    source = _load(run_root / "source.freeze.json")
    snapshots = defaultdict(list)
    for path in sorted(snapshot_dir.glob("scale*/*/*.json")):
        payload = _load(path)
        content_hash = str(payload.get("instance_content_hash") or "")
        if content_hash not in task_by_hash:
            _terminal(run_root, "INSTANCE_FEATURE_FOLD_OR_OUTCOME_LEAKAGE", "unknown snapshot instance")
            raise SystemExit("V4 root snapshot instance is outside frozen census")
        if str(payload.get("pricing_lifecycle_scope")) != "root_cg":
            _terminal(run_root, "INSTANCE_FEATURE_FOLD_OR_OUTCOME_LEAKAGE", "tree snapshot")
            raise SystemExit("V4 corpus is root-only")
        if str(payload.get("engine_hash")) != str(source["exact_engine_hash"]):
            _terminal(run_root, "FREEZE_HASH_DRIFT", "snapshot engine hash")
            raise SystemExit("fresh snapshot engine binding mismatch")
        if bool(payload.get("labels_dropped")):
            _terminal(run_root, "V4_NATIVE_TELEMETRY_REDLINE", "root snapshot labels dropped")
            raise SystemExit("V4 root snapshot reported label drop")
        snapshots[content_hash].append((path, payload))
    for content_hash in snapshots:
        dedup = {}
        for path, payload in snapshots[content_hash]:
            state_hash = str(payload.get("state_hash") or "")
            if state_hash in dedup and _sha256(path) != _sha256(dedup[state_hash][0]):
                raise SystemExit("duplicate V4 state hash has different snapshot payload")
            dedup[state_hash] = (path, payload)
        snapshots[content_hash] = [dedup[key] for key in sorted(dedup)][:3]

    fixed_by_scale_partition = defaultdict(list)
    candidates_by_scale = defaultdict(list)
    for task in schedule["tasks"]:
        if task["desired_partition"] == "candidate_pool":
            candidates_by_scale[int(task["scale"])].append(task)
        else:
            fixed_by_scale_partition[(int(task["scale"]), task["desired_partition"])].append(task)
    used = set()
    assignments = []
    deficits = []
    required = {"train": 14, "calibration": 4, "development_e2e": 3}
    for scale in (30, 50):
        available = [
            row for row in sorted(candidates_by_scale[scale], key=lambda value: value["instance_path"])
            if snapshots.get(str(row["instance_content_hash"]))
        ]
        cursor = 0
        for partition in ("train", "calibration", "development_e2e"):
            fixed = sorted(
                fixed_by_scale_partition[(scale, partition)],
                key=lambda value: value["instance_content_hash"],
            )
            selected = [row for row in fixed if snapshots.get(str(row["instance_content_hash"]))]
            while len(selected) < required[partition] and cursor < len(available):
                candidate = available[cursor]
                cursor += 1
                if candidate["instance_content_hash"] not in used:
                    selected.append(candidate)
            if len(selected) != required[partition]:
                deficits.append({"scale": scale, "partition": partition,
                                 "required": required[partition], "observed": len(selected)})
            for row in selected:
                used.add(row["instance_content_hash"])
                assignments.append((partition, row))
        heldout = []
        while len(heldout) < 4 and cursor < len(available):
            candidate = available[cursor]
            cursor += 1
            if candidate["instance_content_hash"] not in used:
                heldout.append(candidate)
        if len(heldout) != 4:
            deficits.append({"scale": scale, "partition": "selector_heldout",
                             "required": 4, "observed": len(heldout)})
        for row in heldout:
            used.add(row["instance_content_hash"])
            assignments.append(("selector_heldout", row))
    if deficits:
        _terminal(run_root, "INSUFFICIENT_FRESH_ROOT_COVERAGE", deficits)
        raise SystemExit("V4 fresh root coverage does not satisfy 14/4/4/3")

    corpus_rows = []
    for partition, task in assignments:
        rows = snapshots[str(task["instance_content_hash"])]
        for index, (path, payload) in enumerate(rows):
            trajectory = dict(payload.get("trajectory_features") or {})
            if str(trajectory.get("previous_queue_policy_id") or "Q0") != "Q0":
                for field in (
                    "previous_proof_pass_wall_time", "previous_proof_processed_labels",
                    "previous_dominance_candidate_checks", "previous_dominance_wall_time",
                    "previous_max_visited_bucket_size",
                ):
                    if trajectory.get(field) is not None:
                        raise SystemExit("non-Q0 previous trajectory leaked into V4 corpus")
            active_sets = payload.get("active_task_sets") or ()
            corpus_rows.append({
                "context_id": f"v4_s{int(task['scale'])}_{task['instance_content_hash']}_{index}",
                "scale": int(task["scale"]), "partition": partition,
                "instance_content_hash": task["instance_content_hash"],
                "instance_id": task["instance_id"],
                "instance_path": task["instance_path"],
                "source_cohort": task["source_cohort"],
                "snapshot_path": str(path.resolve()), "snapshot_sha256": _sha256(path),
                "state_hash": str(payload["state_hash"]),
                "source_state_hash": str(payload["state_hash"]),
                "source_engine_hash": str(payload["engine_hash"]),
                "source_config_hash": str(payload["config_hash"]),
                "source_exact_action_policy_hash": str(payload["exact_action_policy_hash"]),
                "pricing_lifecycle_scope": "root_cg",
                "round": int(payload.get("round") or 0),
                "active_task_set_count": len(active_sets),
                "active_column_signature_count": len(
                    payload.get("active_column_signature_hashes") or ()
                ),
                "context_weight": 1.0 / len(rows), "instance_total_weight": 1.0,
                "outcome_fields_present": [],
            })
    corpus = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_corpus_freeze.v4",
        "status": "FROZEN_BEFORE_ANY_V4_ARM_OUTCOME",
        "fresh_engine_only": True, "all_natural_contexts_up_to_cap_used": True,
        "instance_total_weight": 1.0,
        "context_weight_rule": "inverse_legal_context_count_within_instance",
        "rows": sorted(corpus_rows, key=lambda row: (
            row["scale"], row["partition"], row["instance_content_hash"], row["state_hash"]
        )),
    }
    split = {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_instance_split.v4",
        "status": "FROZEN_BEFORE_ANY_V4_ARM_OUTCOME",
        "instance_partition": {
            row["instance_content_hash"]: row["partition"] for row in corpus["rows"]
        },
        "counts": {
            str(scale): {
                partition: len({row["instance_content_hash"] for row in corpus["rows"]
                                if row["scale"] == scale and row["partition"] == partition})
                for partition in ("train", "calibration", "selector_heldout", "development_e2e")
            } for scale in (30, 50)
        },
    }
    folds = _folds(corpus)
    index = {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_root_snapshot_index.v4",
        "expected_engine_hash": source["exact_engine_hash"],
        "root_only": True, "outcome_fields_included": False,
        "rows": corpus["rows"],
    }
    replay_rows = [row for row in corpus["rows"] if row["partition"] in {"train", "calibration"}]
    milestone = {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_q0_milestone_execution.v4",
        "status": "FROZEN_BEFORE_ANY_V4_ARM_OUTCOME", "q0_only": True,
        "single_native_process": True,
        "tasks": [{
            "context_id": row["context_id"], "instance_hash": row["instance_content_hash"],
            "scale": row["scale"], "partition": row["partition"],
            "state_hash": row["state_hash"], "arm": "Q0", "execution_policy": "Q0",
            "cap_sec": config["execution"]["replay_caps_sec"][str(row["scale"])],
            "memory_limit_gb": config["execution"]["memory_limit_gb"],
        } for row in replay_rows],
    }
    primary = {
        "schema_version": "lunar_ice_bpc.p0v5_qgr1_primary_context.v4",
        "status": "FROZEN_BEFORE_ANY_QGR1_WALL_OUTCOME",
        "rows": [
            sorted(rows, key=lambda row: row["state_hash"])[0]
            for (_scale, _instance), rows in sorted(_group(
                [row for row in corpus["rows"] if row["partition"] == "calibration"]
            ).items())
        ],
    }
    artifacts = {
        "root_snapshot_index.freeze.json": index,
        "corpus.freeze.json": corpus, "instance_split.freeze.json": split,
        "grouped_cv_folds.freeze.json": folds,
        "qgr1_primary_context.freeze.json": primary,
        "q0_milestone_execution.freeze.json": milestone,
        "execution.freeze.json": {
            "schema_version": "lunar_ice_bpc.p0v5_residual_gat_execution_freeze.v4",
            "status": "FROZEN_BEFORE_ANY_V4_ARM_OUTCOME",
            "execution": config["execution"], "trace_reservoir": config["trace_reservoir"],
            "threshold_grid": config["threshold_grid"], "action_universe": config["action_universe"],
        },
        "acceptance.freeze.json": {
            "schema_version": "lunar_ice_bpc.p0v5_residual_gat_acceptance_freeze.v4",
            "status": "FROZEN_BEFORE_ANY_V4_ARM_OUTCOME",
            **{key: config[key] for key in (
                "qd1_admission", "qgr1_training", "qgr1_force_on",
                "portfolio_headroom", "calibration_gate", "heldout_gate",
                "development_e2e_gate", "formal_gate", "stop_reasons",
            )},
        },
    }
    for name, payload in artifacts.items():
        _write_once(run_root / name, payload)
    prearm = _load(run_root / "prearm.freeze.registry.json")
    registry_names = {
        **dict(prearm["artifact_sha256"]),
        **{name: _sha256(run_root / name) for name in artifacts},
    }
    _write_once(run_root / "freeze.registry.json", {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_freeze_registry.v4",
        "immutable": True, "arm_outcomes_present_at_freeze": 0,
        "artifact_sha256": registry_names,
    })
    verify_portfolio_freezes(run_root, ROOT)
    _update_state(run_root, "Q0_MILESTONE_AND_TRACE", "READY")
    print(json.dumps({
        "corpus_contexts": len(corpus_rows), "split_counts": split["counts"],
        "milestone_tasks": len(milestone["tasks"]),
        "engine_hash": source["exact_engine_hash"],
        "status": "READY_FOR_Q0_MILESTONE_AND_TRACE",
    }, ensure_ascii=False, indent=2))


def _folds(corpus):
    instances = sorted({
        (row["scale"], row["instance_content_hash"])
        for row in corpus["rows"] if row["partition"] == "train"
    })
    rows = []
    by_scale = defaultdict(list)
    for scale, instance in instances:
        by_scale[scale].append(instance)
    for scale in (30, 50):
        ordered = sorted(by_scale[scale], key=lambda value: hashlib.sha256(
            f"v4-fold:{scale}:{value}".encode()
        ).hexdigest())
        rows.extend({"scale": scale, "instance_hash": value, "fold": index % 5}
                    for index, value in enumerate(ordered))
    return {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_grouped_cv.v4",
        "status": "FROZEN_BEFORE_ANY_V4_ARM_OUTCOME", "fold_count": 5,
        "instance_grouped": True, "rows": rows,
    }


def _group(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["scale"], row["instance_content_hash"])].append(row)
    return grouped


def _environment(config, snapshot_dir, snapshot_cap):
    env = dict(os.environ)
    for key in tuple(env):
        if key.startswith("LUNAR_ICE_P0V5_") or key.startswith(
            "LUNAR_ICE_PROOF_TAIL_GAT"
        ) or key.startswith("LUNAR_ICE_GAT_"):
            env.pop(key, None)
    env[SNAPSHOT_ENV] = str(snapshot_dir)
    env[SNAPSHOT_CAP_ENV] = str(snapshot_cap)
    env["PYTHONPATH"] = os.pathsep.join((
        str((ROOT / config["native_build_dir"]).resolve()), str((ROOT / "src").resolve())
    ))
    return env


def _verify_prearm(run_root):
    registry = _load(run_root / "prearm.freeze.registry.json")
    for name, expected in registry["artifact_sha256"].items():
        if _sha256(run_root / name) != expected:
            raise SystemExit(f"FREEZE_HASH_DRIFT:{name}")
    source = _load(run_root / "source.freeze.json")
    for relative, expected in source["source_sha256"].items():
        if _sha256(ROOT / relative) != expected:
            raise SystemExit(f"FREEZE_HASH_DRIFT:{relative}")
    if _sha256(source["native_binary"]) != source["native_binary_sha256"]:
        raise SystemExit("FREEZE_HASH_DRIFT:native_binary")
    if _sha256(source["old_native_binary"]) != source["old_native_binary_sha256"]:
        raise SystemExit("FREEZE_HASH_DRIFT:old_native_binary")
    differential = source.get("old_new_native_differential_path")
    if (
        not differential
        or _sha256(differential)
        != str(source.get("old_new_native_differential_sha256") or "")
    ):
        raise SystemExit("FREEZE_HASH_DRIFT:old_new_native_differential")


def _assert_active(run_root):
    state = _load(run_root / "state.json")
    if bool(state.get("terminal")):
        raise SystemExit("terminal V4 chain forbids root corpus writer")


def _update_state(run_root, stage, status):
    path = run_root / "state.json"
    payload = _load(path)
    payload.update({"current_stage": stage, "status": status})
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def _terminal(run_root, reason, detail):
    path = run_root / "terminal_decision.json"
    if not path.exists():
        path.write_text(json.dumps({
            "schema_version": "lunar_ice_bpc.p0v5_residual_gat_terminal.v4",
            "decision": "FAIL", "reason": reason, "detail": detail,
            "development_only": True, "deployment_authorized": False,
            "production_switch_authorized": False,
        }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    state_path = run_root / "state.json"
    if state_path.is_file():
        state = _load(state_path)
        state.update({"terminal": True, "terminal_decision": str(path),
                      "current_stage": "TERMINAL", "status": "FAIL"})
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2,
                                         sort_keys=True) + "\n", encoding="utf-8")


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write_once(path, payload):
    path = Path(path)
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != encoded:
        raise SystemExit(f"immutable V4 artifact drift:{path}")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(encoded, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate and screen outcome-blind V2 root-context candidates sequentially."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import verify_portfolio_freezes  # noqa: E402


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v2_20260807"
SNAPSHOT_ENV = "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR"
SNAPSHOT_CAP_ENV = "LUNAR_ICE_P0V5_QG2_SNAPSHOT_MAX_PER_INSTANCE"
BACKEND_ID = "native_rcspp_bidirectional_root_partial_hybrid_v3"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("existing", "generate", "candidates", "index"))
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--per-scale-target", type=int)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    _assert_active(run_root)
    config = _load(run_root / "config.freeze.json")
    snapshot_dir = run_root / "root_screen_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    if args.mode == "generate":
        target = int(args.per_scale_target or 0)
        maximum = int(config["candidate_generation"]["maximum_new_instances_per_scale"])
        if target <= 0 or target > maximum:
            raise SystemExit(f"--per-scale-target must be in [1,{maximum}]")
        _generate(config, target)
        return 0
    if args.mode == "existing":
        tasks = list(_load(run_root / "candidate_census.initial.freeze.json")["root_screen_tasks"])
        schedule_name = "existing_root_screen.execution.json"
        cohort = "existing_realmap_development_v4"
    elif args.mode == "candidates":
        tasks = _candidate_tasks(config, run_root)
        generated = _generated_counts(config)
        schedule_name = (
            f"candidate_root_screen_g{generated[30]:02d}_"
            f"g{generated[50]:02d}.execution.json"
        )
        cohort = "generated_v2_candidate"
    else:
        output = _build_index(run_root, config, snapshot_dir)
        print(json.dumps({"snapshot_index": str(output), "sha256": _sha256(output)}, indent=2))
        return 0
    schedule = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_root_screen_execution.v2",
        "outcome_blind": True,
        "single_native_process": True,
        "tree_supplement": False,
        "source_cohort": cohort,
        "tasks": tasks,
    }
    schedule_path = run_root / schedule_name
    _write_once(schedule_path, schedule)
    for ordinal, task in enumerate(tasks):
        _screen_one(run_root, config, snapshot_dir, task, ordinal)
    output = _build_index(run_root, config, snapshot_dir)
    print(json.dumps({
        "screened_instances": len(tasks), "snapshot_index": str(output),
        "next": "manage_p0v5_interaction_gat_census_v2.py evaluate",
    }, ensure_ascii=False, indent=2))
    return 0


def _generate(config, target):
    root = (ROOT / config["candidate_instance_root"]).resolve()
    root.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable, str(ROOT / "scripts/generate_lunar_real_map_benchmark.py"),
        "--output-root", str(root),
        "--manifest", str(root / "manifest.json"),
        "--scales", "30,50", "--per-scale", str(target),
        "--seed-base", str(config["candidate_generation"]["seed_base"]),
        "--max-workers", "1", "--path-preview", "none", "--no-draw-figures",
    ]
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode != 0:
        raise SystemExit(f"candidate generation failed:{completed.returncode}")


def _candidate_tasks(config, run_root):
    formal = set(_load(
        run_root / "candidate_protected_blacklist.freeze.json"
    )["content_hashes"])
    initial = _load(run_root / "candidate_census.initial.freeze.json")["instances"]
    protected = {str(row["instance_content_hash"]) for row in initial}
    imported = _load(run_root / "r1_preaction_import.freeze.json")["rows"]
    counts = {}
    for row in imported:
        counts[str(row["instance_content_hash"])] = counts.get(str(row["instance_content_hash"]), 0) + 1
    index_path = run_root / "root_screen_snapshot_index.current.json"
    if index_path.is_file():
        for row in _load(index_path).get("rows") or ():
            counts[str(row["instance_content_hash"])] = counts.get(str(row["instance_content_hash"]), 0) + 1
    screened = set()
    for schedule_path in run_root.glob("candidate_root_screen_*.execution.json"):
        for row in _load(schedule_path).get("tasks") or ():
            screened.add(str(row["instance_content_hash"]))
    tasks = []
    candidate_root = (ROOT / config["candidate_instance_root"]).resolve()
    for scale in (30, 50):
        paths = sorted(candidate_root.rglob(f"*{scale:03d}*/instance_*_logical_graph.json"))
        if not paths:
            paths = sorted((candidate_root / f"lunar_ice_sp50_{scale:03d}").glob("instance_*_logical_graph.json"))
        maximum = int(config["candidate_generation"]["maximum_new_instances_per_scale"])
        if len(paths) > maximum:
            raise SystemExit(f"generated scale{scale} candidate count exceeds frozen maximum")
        for path in paths:
            data = load_lunar_ice_data(_load(path))
            content_hash = str(data.instance_content_hash)
            if content_hash in formal or content_hash in protected:
                raise SystemExit("generated candidate content hash overlaps protected corpus")
            protected.add(content_hash)
            # Every generated instance is screened exactly once.  An instance
            # that naturally yields fewer than two snapshots is ineligible;
            # rerunning it would violate the outcome-blind census protocol.
            if content_hash in screened or counts.get(content_hash, 0) >= 2:
                continue
            tasks.append({
                "scale": scale, "instance_content_hash": content_hash,
                "instance_id": data.instance_id, "instance_path": str(path.resolve()),
                "source_cohort": "generated_v2_candidate",
                "cap_sec": config["execution"]["replay_caps_sec"][str(scale)],
                "snapshot_cap": 3,
            })
    return tasks


def _screen_one(run_root, config, snapshot_dir, task, ordinal):
    output = run_root / "root_screen_runs" / f"{int(task['scale'])}_{task['instance_content_hash']}_{ordinal:03d}"
    if output.exists():
        raise SystemExit(f"root screen output already exists:{output}")
    command = [
        sys.executable, str(ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"),
        "--config", str((ROOT / config["selected_exact_config"]).resolve()),
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
        raise SystemExit(f"root screen failed:{task['instance_content_hash']}")


def _build_index(run_root, config, snapshot_dir):
    paths = _all_instance_paths(config)
    by_hash = {}
    formal = set(_load(run_root / "formal_blacklist.freeze.json")["content_hashes"])
    for cohort, path in paths:
        data = load_lunar_ice_data(_load(path))
        content_hash = str(data.instance_content_hash)
        if content_hash in formal or content_hash in by_hash:
            raise SystemExit("root screen index instance overlap")
        by_hash[content_hash] = (data, path, cohort)
    rows = []
    for snapshot_path in sorted(snapshot_dir.glob("scale*/*/*.json")):
        snapshot = _load(snapshot_path)
        if str(snapshot.get("pricing_lifecycle_scope")) != "root_cg":
            raise SystemExit("V2 root screen captured a non-root context")
        content_hash = str(snapshot.get("instance_content_hash") or "")
        if content_hash not in by_hash:
            raise SystemExit("root screen snapshot instance is unknown")
        data, instance_path, cohort = by_hash[content_hash]
        if str(snapshot.get("engine_hash")) != config["r1_expected_engine_hash"]:
            raise SystemExit("root screen engine hash drift")
        active_sets = snapshot.get("active_task_sets") or ()
        branch = dict(snapshot.get("branch_context") or {})
        cuts = dict(snapshot.get("cut_context") or {})
        rows.append({
            "scale": int(snapshot["scale"]),
            "instance_content_hash": content_hash,
            "instance_id": data.instance_id,
            "instance_path": str(instance_path.resolve()),
            "source_cohort": cohort,
            "snapshot_path": str(snapshot_path.resolve()),
            "snapshot_sha256": _sha256(snapshot_path),
            "state_hash": str(snapshot["state_hash"]),
            "source_state_hash": str(snapshot["state_hash"]),
            "source_engine_hash": str(snapshot["engine_hash"]),
            "source_config_hash": str(snapshot["config_hash"]),
            "source_exact_action_policy_hash": str(snapshot["exact_action_policy_hash"]),
            "pricing_lifecycle_scope": "root_cg",
            "round": int(snapshot.get("round") or 0),
            "active_task_set_count": len(active_sets),
            "active_task_coverage_count": len({value for row in active_sets for value in row}),
            "active_column_signature_count": len(snapshot.get("active_column_signature_hashes") or ()),
            "branch_pair_count": len(branch.get("pair_decisions") or ()),
            "active_cut_count": len(cuts.get("cuts") or ()),
            "previous_q0_wall_stratum": _previous_wall_stratum(snapshot),
        })
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_root_snapshot_index.v2",
        "root_only": True, "outcome_fields_included": False,
        "expected_engine_hash": config["r1_expected_engine_hash"],
        "rows": rows,
    }
    output = run_root / "root_screen_snapshot_index.current.json"
    # This current index is rebuildable prior to the immutable corpus freeze.
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def _all_instance_paths(config):
    result = []
    for cohort, root_key in (
        ("existing_realmap_development_v4", "existing_development_instance_root"),
        ("generated_v2_candidate", "candidate_instance_root"),
    ):
        root = (ROOT / config[root_key]).resolve()
        if root.is_dir():
            result.extend((cohort, path) for path in sorted(root.rglob("instance_*_logical_graph.json")))
    return result


def _generated_counts(config):
    root = (ROOT / config["candidate_instance_root"]).resolve()
    counts = {30: 0, 50: 0}
    if not root.is_dir():
        return counts
    for path in root.rglob("instance_*_logical_graph.json"):
        scale = int(load_lunar_ice_data(_load(path)).scale)
        if scale in counts:
            counts[scale] += 1
    return counts


def _previous_wall_stratum(snapshot):
    trajectory = dict(snapshot.get("trajectory_features") or {})
    if str(trajectory.get("previous_queue_policy_id") or "") != "Q0":
        return "missing"
    value = trajectory.get("previous_proof_pass_wall_time")
    if value is None:
        return "missing"
    value = float(value)
    return "low" if value < 10.0 else "medium" if value < 60.0 else "high"


def _environment(config, snapshot_dir, snapshot_cap):
    env = dict(os.environ)
    for key in tuple(env):
        if key.startswith("LUNAR_ICE_P0V5_") or key.startswith("LUNAR_ICE_PROOF_TAIL_GAT") or key.startswith("LUNAR_ICE_GAT_"):
            env.pop(key, None)
    env[SNAPSHOT_ENV] = str(snapshot_dir)
    env[SNAPSHOT_CAP_ENV] = str(snapshot_cap)
    env["PYTHONPATH"] = os.pathsep.join((
        str((ROOT / config["native_build_dir"]).resolve()),
        str((ROOT / "src").resolve()),
    ))
    return env


def _assert_active(run_root):
    state = _load(run_root / "state.json")
    if bool(state.get("terminal")):
        raise SystemExit("terminal chain forbids root census writer")


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_once(path, payload):
    path = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable root screen schedule drift:{path}")
    if not path.exists():
        path.write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Collect current-engine root contexts and one outcome-blind tree supplement."""

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
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_context_queue_portfolio_v1_20260807_r1"
BACKEND_ID = "native_rcspp_bidirectional_root_partial_hybrid_v3"
SNAPSHOT_ENV = "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR"
CAP_ENV = "LUNAR_ICE_P0V5_QG2_SNAPSHOT_MAX_PER_INSTANCE"
STRIP_ENV_PREFIXES = (
    "LUNAR_ICE_PROOF_TAIL_GAT", "LUNAR_ICE_PROOF_QUEUE_GAT",
    "LUNAR_ICE_BIDIRECTIONAL_GATE_GAT", "LUNAR_ICE_GAT_",
    "LUNAR_ICE_P0V5_QG2_V3_SELECTOR",
    "LUNAR_ICE_P0V5_CONTEXT_QUEUE_PORTFOLIO",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("root", "tree", "index"))
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    _verify_freezes(run_root)
    config = _load(run_root / "config.freeze.json")
    split = _load(run_root / "instance_split.freeze.json")
    snapshot_dir = run_root / "context_snapshots_current_engine"
    index_path = run_root / "context_snapshot_index.current.json"
    collection_freeze = run_root / "context_collection.freeze.json"

    if args.mode == "root":
        if snapshot_dir.exists() or collection_freeze.exists():
            raise SystemExit("root collection namespace is not fresh")
        _freeze_root_collection(run_root, config, split, collection_freeze)
        snapshot_dir.mkdir(parents=True, exist_ok=False)
        for scale in (30, 50):
            _run_acceptance(
                run_root, config, split, snapshot_dir,
                scale=scale, root_only=True, snapshot_cap=3,
            )
        _build_index(config, snapshot_dir, index_path)
        coverage = _coverage(index_path, split, config)
        _update_state(
            run_root,
            "CONTEXT_CORPUS_FREEZE" if coverage["passed"] else "TREE_SUPPLEMENT",
            "READY",
        )
        _write_once(run_root / "root_collection.coverage.json", coverage)
    elif args.mode == "tree":
        _verify_collection_freeze(run_root, collection_freeze)
        if not index_path.is_file():
            raise SystemExit("root snapshot index is missing")
        before = _coverage(index_path, split, config)
        if before["passed"]:
            raise SystemExit("tree supplement forbidden because root coverage passed")
        deficient = _deficient_scales(before)
        supplement = {
            "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_tree_supplement_freeze.v1",
            "status": "FROZEN_BEFORE_TREE_SUPPLEMENT_CONTEXTS",
            "selection_uses_arm_outcomes": False,
            "selection_input": "root_context_coverage_only",
            "selected_scales": deficient,
            "root_index_sha256": _sha256(index_path),
            "root_coverage": before,
            "snapshot_cap_after_supplement": 6,
            "full_fixed_eligible_instance_set": True,
            "row_cap_sec": float(config["execution"]["formal_bpc_cap_sec"]),
        }
        _write_once(run_root / "tree_supplement.freeze.json", supplement)
        for scale in deficient:
            _run_acceptance(
                run_root, config, split, snapshot_dir,
                scale=scale, root_only=False, snapshot_cap=6,
            )
        _build_index(config, snapshot_dir, index_path)
        coverage = _coverage(index_path, split, config)
        _write_once(run_root / "tree_collection.coverage.json", coverage)
        if not coverage["passed"]:
            _terminal(run_root, "INSUFFICIENT_CONTEXT_COVERAGE", coverage)
            return 2
        _update_state(run_root, "CONTEXT_CORPUS_FREEZE", "READY")
    else:
        _verify_collection_freeze(run_root, collection_freeze)
        _build_index(config, snapshot_dir, index_path)
        coverage = _coverage(index_path, split, config)

    print(json.dumps({
        "mode": args.mode,
        "snapshot_index": str(index_path),
        "snapshot_index_sha256": _sha256(index_path),
        "coverage": coverage,
        "next_command": (
            "freeze_p0v5_context_queue_portfolio_corpus.py --snapshot-index "
            + str(index_path)
            if coverage["passed"] else
            "collect_p0v5_context_queue_portfolio_contexts.py tree"
        ),
    }, ensure_ascii=False, indent=2))
    return 0 if coverage["passed"] else 2


def _freeze_root_collection(run_root, config, split, path):
    source = _load(run_root / "source.freeze.json")
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_context_collection_freeze.v1",
        "status": "FROZEN_BEFORE_CURRENT_ENGINE_CONTEXTS",
        "source_freeze_sha256": _sha256(run_root / "source.freeze.json"),
        "native_binary_sha256": source["native_binary_sha256"],
        "selected_exact_config_sha256": source["selected_exact_config_sha256"],
        "instance_split_sha256": _sha256(run_root / "instance_split.freeze.json"),
        "eligible_partitions": ["train", "calibration", "selector_heldout"],
        "development_e2e_instances_collected": False,
        "root_collection": "all_fixed_17_instances_per_scale_once",
        "root_caps_sec": config["execution"]["replay_caps_sec"],
        "root_snapshot_cap_per_instance": 3,
        "tree_supplement_policy": "coverage_deficient_scales_all_fixed_eligible_instances_once",
        "tree_snapshot_total_cap_per_instance": 6,
        "formal_benchmark_instances_used": False,
        "arm_outcomes_used": False,
        "split_instance_count": len(split["rows"]),
    }
    _write_once(path, payload)


def _run_acceptance(run_root, config, split, snapshot_dir, *, scale, root_only, snapshot_cap):
    rows = [
        row for row in split["rows"]
        if int(row["scale"]) == int(scale)
        and row["partition"] in {"train", "calibration", "selector_heldout"}
    ]
    if len(rows) != 17:
        raise SystemExit(f"scale{scale} current-engine collection instances != 17")
    phase = "root" if root_only else "tree"
    output = run_root / f"context_collection_{phase}_scale{scale}"
    if output.exists():
        raise SystemExit(f"collection output already exists:{output}")
    command = [
        sys.executable,
        str(ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"),
        "--config", str((ROOT / config["selected_exact_config"]).resolve()),
        "--scales", str(scale),
    ]
    for row in rows:
        command.extend(("--instance", str(row["instance_path"])))
    command.extend((
        "--limit", str(len(rows)), "--output-dir", str(output), "--no-resume",
    ))
    if root_only:
        command.extend((
            "--route-opportunity-collection-only-root-pool",
            "--route-opportunity-collection-root-pool-time-cap-sec",
            str(config["execution"]["replay_caps_sec"][str(scale)]),
        ))
    completed = subprocess.run(
        command, cwd=ROOT,
        env=_environment(config, snapshot_dir, snapshot_cap),
        check=False,
    )
    if completed.returncode not in {0, 1}:
        raise SystemExit(f"scale{scale} {phase} context collection failed")


def _build_index(config, snapshot_dir, output):
    command = [
        sys.executable, str(ROOT / "scripts/build_p0v5_qg2_fallback_snapshot_index.py"),
        "--snapshot-dir", str(snapshot_dir),
        "--instance-root", str((ROOT / config["development_instance_root"]).resolve()),
        "--output", str(output),
        "--native-build-dir", str((ROOT / config["native_build_dir"]).resolve()),
        "--source-backend-id", BACKEND_ID,
        "--require-exact-action-policy-hash",
    ]
    completed = subprocess.run(
        command, cwd=ROOT, env=_environment(config, snapshot_dir, 6), check=False
    )
    if completed.returncode != 0:
        raise SystemExit("current-engine snapshot index validation failed")
    payload = _load(output)
    if int(payload.get("excluded_count") or 0):
        raise SystemExit("current-engine snapshot index has exclusions")
    expected_engine = str(_load(output.parent / "source.freeze.json")["exact_engine_hash"])
    observed_engines = {
        str(row.get("source_engine_hash") or "")
        for row in payload.get("rows") or ()
    }
    if observed_engines and observed_engines != {expected_engine}:
        raise SystemExit("current-engine snapshot index engine binding drift")


def _coverage(index_path, split, config):
    index = _load(index_path)
    assignments = dict(split["assignments"])
    selected = []
    for instance_hash, partition in sorted(assignments.items()):
        if partition == "development_e2e":
            continue
        rows = [
            dict(row) for row in index.get("rows") or ()
            if str(row["instance_content_hash"]) == instance_hash
        ]
        rows.sort(key=lambda row: (
            _stratum(row), int(row.get("round") or 0), str(row["state_hash"])
        ))
        for row in rows[:int(config["context_coverage"]["maximum_per_instance"])]:
            selected.append({**row, "partition": partition})
    result, violations = {}, []
    for scale in (30, 50):
        result[str(scale)] = {}
        for partition in ("train", "calibration", "selector_heldout"):
            rows = [
                row for row in selected
                if int(row["scale"]) == scale and row["partition"] == partition
            ]
            gate = config["context_coverage"][partition]
            instances = len({row["instance_content_hash"] for row in rows})
            passed = (
                len(rows) >= int(gate["minimum_contexts"])
                and instances >= int(gate["minimum_instances"])
            )
            result[str(scale)][partition] = {
                "context_count": len(rows), "instance_count": instances,
                "minimum_contexts": int(gate["minimum_contexts"]),
                "minimum_instances": int(gate["minimum_instances"]),
                "passed": passed,
            }
            if not passed:
                violations.append(f"SCALE{scale}_{partition.upper()}_COVERAGE")
    return {"passed": not violations, "by_scale": result, "violations": violations}


def _stratum(row):
    lifecycle = "root" if str(row.get("pricing_lifecycle_scope")) == "root_cg" else "tree"
    structure = "branch_cut" if int(row.get("branch_pair_count") or 0) or int(row.get("active_cut_count") or 0) else "plain"
    round_index = int(row.get("round") or 0)
    band = "r0_9" if round_index < 10 else "r10_29" if round_index < 30 else "r30_plus"
    return f"{lifecycle}:{structure}:{band}:{row.get('previous_q0_wall_stratum') or 'missing'}"


def _deficient_scales(coverage):
    values = [
        scale for scale in (30, 50)
        if not all(
            bool(row["passed"])
            for row in coverage["by_scale"][str(scale)].values()
        )
    ]
    if not values:
        raise SystemExit("no structurally deficient scale")
    return values


def _environment(config, snapshot_dir, snapshot_cap):
    env = dict(os.environ)
    for key in tuple(env):
        if any(key.startswith(prefix) for prefix in STRIP_ENV_PREFIXES):
            env.pop(key, None)
    env[SNAPSHOT_ENV] = str(snapshot_dir)
    env[CAP_ENV] = str(int(snapshot_cap))
    env["PYTHONPATH"] = os.pathsep.join((
        str((ROOT / config["native_build_dir"]).resolve()),
        str((ROOT / "src").resolve()),
    ))
    return env


def _verify_collection_freeze(run_root, path):
    payload = _load(path)
    source = _load(run_root / "source.freeze.json")
    if (
        _sha256(run_root / "source.freeze.json") != payload["source_freeze_sha256"]
        or source["native_binary_sha256"] != payload["native_binary_sha256"]
        or _sha256(run_root / "instance_split.freeze.json") != payload["instance_split_sha256"]
    ):
        raise SystemExit("FREEZE_HASH_DRIFT:context_collection")


def _verify_freezes(run_root):
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc


def _terminal(run_root, reason, detail):
    _write_once(run_root / "terminal_decision.json", {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_terminal.v1",
        "decision": "FAIL", "reason": reason, "detail": detail,
        "deployment_authorized": False, "production_switch_authorized": False,
    })
    state = _load(run_root / "state.json")
    state.update({
        "current_stage": "TERMINAL", "status": "FAIL", "terminal": True,
        "terminal_decision": reason,
    })
    (run_root / "state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _update_state(run_root, stage, status):
    path = run_root / "state.json"
    state = _load(path)
    state.update({"current_stage": stage, "status": status})
    path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_once(path, payload):
    path = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable collection artifact drift:{path}")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

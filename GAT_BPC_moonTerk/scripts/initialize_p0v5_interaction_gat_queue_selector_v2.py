#!/usr/bin/env python3
"""Initialize the independent immutable Interaction-GAT V2 research chain."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import verify_portfolio_freezes  # noqa: E402
from lunar_ice_bpc.guidance.interaction_gat_queue_runtime_v2 import (  # noqa: E402
    INTERACTION_GAT_RUNTIME_POLICY_V2,
    interaction_gat_runtime_implementation_hash,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import (  # noqa: E402
    INTERACTION_CONTEXT_FEATURES,
    INTERACTION_EDGE_FEATURES,
    INTERACTION_FEATURE_SCHEMA_V2,
    INTERACTION_GRAPH_SCHEMA_V1,
    INTERACTION_NODE_FEATURES,
    interaction_graph_builder_hash,
)


CONFIG = ROOT / "configs/experiments/p0v5_interaction_gat_queue_selector_v2.json"
SOURCE_PATHS = (
    "src/lunar_ice_bpc/guidance/interaction_gat_queue_v2.py",
    "src/lunar_ice_bpc/guidance/interaction_gat_queue_runtime_v2.py",
    "src/lunar_ice_bpc/guidance/interaction_gat_queue_gates_v2.py",
    "src/lunar_ice_bpc/guidance/qgr1_residual_supervision_v2.py",
    "scripts/initialize_p0v5_interaction_gat_queue_selector_v2.py",
    "scripts/manage_p0v5_interaction_gat_census_v2.py",
    "scripts/run_p0v5_interaction_gat_root_screen_v2.py",
    "scripts/run_p0v5_interaction_gat_matrix_v2.py",
    "scripts/finalize_p0v5_interaction_gat_stage_v2.py",
    "scripts/build_p0v5_interaction_gat_training_dataset_v2.py",
    "scripts/train_p0v5_interaction_gat_selector_v2.py",
    "scripts/train_p0v5_qgr1_residual_gat_v2.py",
    "scripts/predict_p0v5_qgr1_residual_potential_v2.py",
    "scripts/freeze_p0v5_qgr1_execution_v2.py",
    "scripts/merge_p0v5_interaction_gat_outcomes_v2.py",
    "scripts/predict_p0v5_interaction_gat_heldout_action_v2.py",
    "scripts/freeze_p0v5_interaction_gat_heldout_v2.py",
    "scripts/analyze_p0v5_interaction_gat_heldout_v2.py",
    "scripts/run_p0v5_interaction_gat_heldout_replays_v2.py",
    "scripts/run_lunar_ice_interaction_gat_acceptance_v2.py",
    "scripts/run_p0v5_interaction_gat_full_bpc_v2.py",
    "scripts/run_p0v5_context_queue_portfolio_matrix.py",
    "scripts/replay_p0v5_qg2_label_state_snapshot.py",
    "scripts/run_p0v5_context_queue_portfolio_full_bpc.py",
    "scripts/run_lunar_ice_native_spprc_acceptance.py",
    "scripts/generate_lunar_real_map_benchmark.py",
    "configs/experiments/p0v5_interaction_gat_queue_selector_v2.json",
    "tests/test_p0v5_interaction_gat_queue_selector_v2.py",
    "plan/GAT/P0V5_INTERACTION_GAT_QUEUE_SELECTOR_V2_IMPLEMENTATION_20260807_ZH.md",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--run-root", type=Path)
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = _load(config_path)
    if config.get("schema_version") != "lunar_ice_bpc.p0v5_interaction_gat_experiment_config.v2":
        raise SystemExit("Interaction-GAT V2 config schema mismatch")
    run_root = args.run_root.resolve() if args.run_root else (ROOT / config["run_root"]).resolve()
    run_root.mkdir(parents=True, exist_ok=True)

    r1_root = (ROOT / config["r1_run_root"]).resolve()
    try:
        verify_portfolio_freezes(r1_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(f"r1 source/freeze drift forbids import:{exc}") from exc
    r1_terminal_path = r1_root / "terminal_decision.json"
    r1_terminal = _load(r1_terminal_path)
    if (
        r1_terminal.get("decision") != "FAIL"
        or r1_terminal.get("reason") != config["r1_expected_terminal_reason"]
    ):
        raise SystemExit("r1 terminal decision is not the immutable expected failure")

    native_binary = _single_native_binary(config)
    sys.path.insert(0, str(native_binary.parent))
    from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import spprc_engine_build_hash
    backend_id = "native_rcspp_bidirectional_root_partial_hybrid_v3"
    engine_hash = spprc_engine_build_hash(backend_id)
    if engine_hash != str(config["r1_expected_engine_hash"]):
        raise SystemExit("Native engine changed; r1 pre-action snapshot import is forbidden")
    selected_config = (ROOT / config["selected_exact_config"]).resolve()
    formal_hashes = _formal_hashes(config)
    candidate_protected = _candidate_protected_hashes(config, formal_hashes)
    imported = _r1_import(r1_root, config, formal_hashes)
    census = _initial_census(config, imported, formal_hashes)
    missing = [path for path in SOURCE_PATHS if not (ROOT / path).is_file()]
    if missing:
        raise SystemExit("V2 implementation source missing:" + ",".join(missing))
    exact_sources = _exact_execution_sources()
    git_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
        text=True, stdout=subprocess.PIPE,
    ).stdout.strip()

    config_freeze = {
        **config,
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_config_freeze.v2",
        "source_config": str(config_path),
        "source_config_sha256": _sha256(config_path),
        "status": "FROZEN_BEFORE_ANY_V2_ARM_OUTCOME",
    }
    source_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_source_freeze.v2",
        "status": "FROZEN_BEFORE_ANY_V2_ARM_OUTCOME",
        "git_commit": git_commit,
        "worktree_may_be_dirty": True,
        "source_sha256": {path: _sha256(ROOT / path) for path in SOURCE_PATHS},
        "exact_execution_source_sha256": {
            str(path.relative_to(ROOT)): _sha256(path) for path in exact_sources
        },
        "selected_exact_config": str(selected_config),
        "selected_exact_config_sha256": _sha256(selected_config),
        "native_binary": str(native_binary),
        "native_binary_sha256": _sha256(native_binary),
        "exact_engine_backend_id": backend_id,
        "exact_engine_hash": engine_hash,
        "native_source_modified_for_v2": False,
        "runtime_policy_id": INTERACTION_GAT_RUNTIME_POLICY_V2,
        "runtime_implementation_hash": interaction_gat_runtime_implementation_hash(),
        "graph_builder_hash": interaction_graph_builder_hash(),
    }
    execution_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_execution_freeze.v2",
        "status": "FROZEN_BEFORE_ANY_V2_ARM_OUTCOME",
        "action_universe": config["action_universe"],
        "lifecycle_authority": config["lifecycle_authority"],
        "execution": config["execution"],
        "candidate_generation": config["candidate_generation"],
        "threshold_grid": config["threshold_grid"],
        "selector_seeds": config["selector_training"]["seeds"],
        "qgr1_training": config["qgr1_training"],
        "formal_outcomes_may_not_reenter_training": True,
        "single_native_process": True,
    }
    acceptance_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_acceptance_freeze.v2",
        "status": "FROZEN_BEFORE_ANY_V2_ARM_OUTCOME",
        "arm_admission": config["arm_admission"],
        "qgr1_force_on": config["qgr1_force_on"],
        "portfolio_headroom_gate": config["portfolio_headroom_gate"],
        "gat_calibration_gate": config["gat_calibration_gate"],
        "heldout_gate": config["heldout_gate"],
        "development_e2e_gate": config["development_e2e_gate"],
        "formal_gate": config["formal_gate"],
        "stop_reasons": config["stop_reasons"],
        "gat_is_only_candidate": True,
    }
    graph_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_graph_freeze.v2",
        "status": "FROZEN_BEFORE_ANY_V2_ARM_OUTCOME",
        "feature_schema": INTERACTION_FEATURE_SCHEMA_V2,
        "graph_schema": INTERACTION_GRAPH_SCHEMA_V1,
        "graph_builder_hash": interaction_graph_builder_hash(),
        "top_k_cooccurrence": 4,
        "top_k_travel": 4,
        "node_feature_names": list(INTERACTION_NODE_FEATURES),
        "edge_feature_names": list(INTERACTION_EDGE_FEATURES),
        "context_feature_names": list(INTERACTION_CONTEXT_FEATURES),
        "forbidden_inputs": ["arm_outcome", "selected_action", "winner", "post_action_telemetry"],
    }
    formal_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_formal_blacklist.v2",
        "content_hashes": sorted(formal_hashes),
        "count": len(formal_hashes),
        "formal_outcomes_read": 0,
    }
    protected_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_candidate_protected_blacklist.v2",
        "status": "FROZEN_BEFORE_CANDIDATE_GENERATION",
        "content_hashes": sorted(candidate_protected["hashes"]),
        "count": len(candidate_protected["hashes"]),
        "source_artifacts": candidate_protected["sources"],
        "generated_candidate_overlap_allowed": 0,
    }
    artifacts = {
        "config.freeze.json": config_freeze,
        "source.freeze.json": source_freeze,
        "execution.freeze.json": execution_freeze,
        "acceptance.freeze.json": acceptance_freeze,
        "graph.freeze.json": graph_freeze,
        "r1_preaction_import.freeze.json": imported,
        "formal_blacklist.freeze.json": formal_freeze,
        "candidate_protected_blacklist.freeze.json": protected_freeze,
        "candidate_census.initial.freeze.json": census,
    }
    for name, payload in artifacts.items():
        _write_once(run_root / name, payload)
    registry = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_freeze_registry.v2",
        "immutable": True,
        "r1_modified": False,
        "historical_registry_modified": False,
        "artifact_sha256": {name: _sha256(run_root / name) for name in sorted(artifacts)},
    }
    _write_once(run_root / "freeze.registry.json", registry)
    state = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_state.v2",
        "experiment_id": config["experiment_id"],
        "current_stage": "OUTCOME_BLIND_ROOT_CENSUS",
        "status": "READY",
        "terminal": False,
        "terminal_decision": None,
        "development_only": True,
        "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    _write_once(run_root / "state.initial.json", state)
    _write_once(run_root / "state.json", state)
    print(json.dumps({
        "run_root": str(run_root),
        "r1_terminal_sha256": _sha256(r1_terminal_path),
        "r1_import_counts": imported["counts_by_scale"],
        "root_screen_task_count": len(census["root_screen_tasks"]),
        "status": "READY_FOR_OUTCOME_BLIND_ROOT_CENSUS",
    }, ensure_ascii=False, indent=2))
    return 0


def _r1_import(r1_root, config, formal_hashes):
    index_path = r1_root / "context_snapshot_index.current.json"
    index = _load(index_path)
    rows = []
    prohibited = {"wall_ratio", "selected_action", "winner", "arm_outcome"}
    for raw in index.get("rows") or ():
        if str(raw.get("pricing_lifecycle_scope")) != "root_cg":
            continue
        row = dict(raw)
        if prohibited.intersection(row):
            raise SystemExit("r1 import contains outcome-bearing index field")
        if str(row.get("source_engine_hash")) != config["r1_expected_engine_hash"]:
            raise SystemExit("r1 import engine mismatch")
        if str(row["instance_content_hash"]) in formal_hashes:
            raise SystemExit("r1 root snapshot overlaps formal blacklist")
        snapshot = Path(row["snapshot_path"]).resolve()
        if not snapshot.is_file() or _sha256(snapshot) != str(row["snapshot_sha256"]):
            raise SystemExit("r1 imported snapshot hash drift")
        payload = _load(snapshot)
        if str(payload.get("state_hash")) != str(row["state_hash"]):
            raise SystemExit("r1 imported snapshot state drift")
        rows.append(row)
    counts = {
        str(scale): {
            "snapshots": sum(int(row["scale"]) == scale for row in rows),
            "instances": len({row["instance_content_hash"] for row in rows if int(row["scale"]) == scale}),
        }
        for scale in (30, 50)
    }
    if counts != {
        "30": {"snapshots": 23, "instances": 11},
        "50": {"snapshots": 38, "instances": 17},
    }:
        raise SystemExit("r1 root snapshot census differs from frozen V2 plan")
    return {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_r1_preaction_import.v2",
        "source_r1_run_root": str(r1_root),
        "source_index": str(index_path),
        "source_index_sha256": _sha256(index_path),
        "source_terminal_decision": str(r1_root / "terminal_decision.json"),
        "source_terminal_decision_sha256": _sha256(r1_root / "terminal_decision.json"),
        "root_only": True,
        "q0_preaction_only": True,
        "arm_outcomes_imported": False,
        "tree_snapshots_imported": False,
        "expected_engine_hash": config["r1_expected_engine_hash"],
        "counts_by_scale": counts,
        "rows": sorted(rows, key=lambda row: (int(row["scale"]), str(row["instance_content_hash"]), str(row["state_hash"]))),
    }


def _initial_census(config, imported, formal_hashes):
    root = (ROOT / config["existing_development_instance_root"]).resolve()
    imported_counts = {}
    for row in imported["rows"]:
        imported_counts[str(row["instance_content_hash"])] = imported_counts.get(str(row["instance_content_hash"]), 0) + 1
    instances, tasks = [], []
    for scale in (30, 50):
        paths = sorted((root / f"lunar_ice_sp50_{scale:03d}").glob("instance_*_logical_graph.json"))
        if len(paths) != 20:
            raise SystemExit(f"existing V2 census scale{scale} instances != 20")
        for path in paths:
            data = load_lunar_ice_data(_load(path))
            content_hash = str(data.instance_content_hash)
            if content_hash in formal_hashes:
                raise SystemExit("existing development instance overlaps formal blacklist")
            count = imported_counts.get(content_hash, 0)
            row = {
                "scale": scale, "instance_content_hash": content_hash,
                "instance_id": data.instance_id, "instance_path": str(path.resolve()),
                "source_cohort": "existing_realmap_development_v4",
                "imported_root_snapshot_count": count,
            }
            instances.append(row)
            if count < 2:
                tasks.append({**row, "cap_sec": config["execution"]["replay_caps_sec"][str(scale)], "snapshot_cap": 3})
    return {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_candidate_census_initial.v2",
        "status": "FROZEN_BEFORE_NEW_ROOT_SCREENS",
        "outcome_blind": True,
        "formal_hash_blacklist_count": len(formal_hashes),
        "instances": instances,
        "root_screen_tasks": tasks,
        "new_candidate_seed_base": config["candidate_generation"]["seed_base"],
        "maximum_new_instances_per_scale": config["candidate_generation"]["maximum_new_instances_per_scale"],
    }


def _formal_hashes(config):
    root = (ROOT / config["formal_instance_root"]).resolve()
    result = set()
    for scale in (5, 10, 20, 30, 50):
        paths = sorted((root / f"lunar_ice_sp50_{scale:03d}").glob("instance_*_logical_graph.json"))[:20]
        if len(paths) != 20:
            raise SystemExit(f"formal scale{scale} instances != 20")
        result.update(str(load_lunar_ice_data(_load(path)).instance_content_hash) for path in paths)
    return result


def _candidate_protected_hashes(config, formal_hashes):
    hashes = set(formal_hashes)
    sources = []
    existing = (ROOT / config["existing_development_instance_root"]).resolve()
    for path in sorted(existing.rglob("instance_*_logical_graph.json")):
        data = load_lunar_ice_data(_load(path))
        if int(data.scale) in {30, 50}:
            hashes.add(str(data.instance_content_hash))
    sources.append({
        "kind": "current_development_root",
        "path": str(existing),
        "instance_count": 40,
    })
    for raw in config.get("protected_content_manifests") or ():
        path = (ROOT / str(raw)).resolve()
        payload = _load(path)
        rows = payload.get("rows") or payload.get("instances") or ()
        values = {
            str(row["instance_content_hash"])
            for row in rows if isinstance(row, dict) and row.get("instance_content_hash")
        }
        if not values:
            raise SystemExit(f"protected manifest has no content hashes:{path}")
        hashes.update(values)
        sources.append({
            "kind": "manifest",
            "path": str(path),
            "sha256": _sha256(path),
            "content_hash_count": len(values),
        })
    for raw in config.get("protected_instance_roots") or ():
        root = (ROOT / str(raw)).resolve()
        values = set()
        for path in sorted(root.rglob("instance_*_logical_graph.json")):
            data = load_lunar_ice_data(_load(path))
            if int(data.scale) in {30, 50}:
                values.add(str(data.instance_content_hash))
        hashes.update(values)
        sources.append({
            "kind": "instance_root",
            "path": str(root),
            "content_hash_count": len(values),
        })
    return {"hashes": hashes, "sources": sources}


def _single_native_binary(config):
    paths = sorted((ROOT / config["native_build_dir"]).resolve().glob("lunar_spprc_native*.so"))
    if len(paths) != 1:
        raise SystemExit("V2 requires exactly one frozen Native binary")
    return paths[0]


def _exact_execution_sources():
    values = {
        *tuple((ROOT / "src/lunar_ice_bpc/exact").rglob("*.py")),
        ROOT / "src/lunar_ice_bpc/runners/native_spprc_acceptance.py",
        ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py",
        ROOT / "scripts/run_lunar_ice_b4_2_cold_exact.py",
        ROOT / "scripts/run_lunar_ice_compact_pricing_staged_resume.py",
        ROOT / "scripts/run_lunar_ice_b4_1_true_dual_proof_tail.py",
    }
    return tuple(sorted(path for path in values if path.is_file()))


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_once(path, payload):
    path = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable V2 initialization artifact drift:{path}")
    if not path.exists():
        path.write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

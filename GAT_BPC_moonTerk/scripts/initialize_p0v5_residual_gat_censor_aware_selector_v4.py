#!/usr/bin/env python3
"""Freeze V4 source, instance census and fresh root-collection schedule."""

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
from lunar_ice_bpc.guidance.interaction_gat_queue_runtime_v4 import (  # noqa: E402
    interaction_gat_runtime_implementation_hash_v4,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import (  # noqa: E402
    INTERACTION_CONTEXT_FEATURES, INTERACTION_EDGE_FEATURES,
    INTERACTION_FEATURE_SCHEMA_V2, INTERACTION_GRAPH_SCHEMA_V1,
    INTERACTION_NODE_FEATURES, interaction_graph_builder_hash,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v4 import (  # noqa: E402
    INTERACTION_CHECKPOINT_SCHEMA_V3, INTERACTION_CORPUS_SCHEMA_V4,
    INTERACTION_DATASET_SCHEMA_V4, INTERACTION_MANIFEST_SCHEMA_V3,
    INTERACTION_RUNTIME_POLICY_V4,
)


CONFIG = ROOT / "configs/experiments/p0v5_residual_gat_censor_aware_selector_v4.json"
NATIVE_DIFFERENTIAL = ROOT / "output/p0v5_native_telemetry_differential_v4.json"
SOURCE_PATHS = (
    "native/lunar_spprc/include/lunar_spprc/native_pricer.hpp",
    "native/lunar_spprc/src/native_pricer.cpp",
    "native/lunar_spprc/src/pybind_module.cpp",
    "native/lunar_spprc/tests/test_native_pricer.cpp",
    "src/lunar_ice_bpc/exact/bpc/pricing/backends/base.py",
    "src/lunar_ice_bpc/exact/bpc/pricing/backends/native_rcspp.py",
    "src/lunar_ice_bpc/exact/bpc/pricing/backends/native_bidirectional_hybrid.py",
    "src/lunar_ice_bpc/exact/bpc/pricing/spprc_pricer.py",
    "src/lunar_ice_bpc/guidance/context_queue_portfolio_freeze.py",
    "src/lunar_ice_bpc/guidance/context_queue_portfolio_gates.py",
    "src/lunar_ice_bpc/guidance/context_queue_portfolio_runtime.py",
    "src/lunar_ice_bpc/guidance/context_queue_portfolio_v1.py",
    "src/lunar_ice_bpc/guidance/interaction_gat_queue_v2.py",
    "src/lunar_ice_bpc/guidance/interaction_gat_queue_runtime_v2.py",
    "src/lunar_ice_bpc/guidance/interaction_gat_queue_v3.py",
    "src/lunar_ice_bpc/guidance/interaction_gat_queue_gates_v3.py",
    "src/lunar_ice_bpc/guidance/instance_balanced_learning.py",
    "src/lunar_ice_bpc/guidance/proof_queue_label_state_gat_v3.py",
    "src/lunar_ice_bpc/guidance/proof_queue_label_state_gat.py",
    "src/lunar_ice_bpc/guidance/qgr1_residual_supervision_v2.py",
    "src/lunar_ice_bpc/guidance/qgr1_supervision.py",
    "src/lunar_ice_bpc/guidance/interaction_gat_queue_v4.py",
    "src/lunar_ice_bpc/guidance/interaction_gat_queue_gates_v4.py",
    "src/lunar_ice_bpc/guidance/interaction_gat_queue_runtime_v4.py",
    "scripts/replay_p0v5_qg2_label_state_snapshot.py",
    "scripts/initialize_p0v5_residual_gat_censor_aware_selector_v4.py",
    "scripts/audit_p0v5_native_telemetry_differential_v4.py",
    "scripts/run_lunar_ice_native_spprc_acceptance.py",
    "scripts/run_p0v5_context_queue_portfolio_matrix.py",
    "scripts/build_p0v5_context_queue_portfolio_training_dataset.py",
    "scripts/train_p0v5_interaction_gat_selector_v3.py",
    "scripts/train_p0v5_qgr1_residual_gat_v3.py",
    "scripts/train_p0v5_qgr1_residual_gat_v2.py",
    "scripts/train_p0v5_qgr1_label_gat.py",
    "scripts/predict_p0v5_qgr1_residual_potential_v2.py",
    "scripts/predict_p0v5_qgr1_potential.py",
    "scripts/run_p0v5_context_queue_portfolio_full_bpc.py",
    "scripts/run_p0v5_interaction_gat_full_bpc_v2.py",
    "scripts/collect_p0v5_residual_gat_root_contexts_v4.py",
    "scripts/run_p0v5_residual_gat_matrix_v4.py",
    "scripts/finalize_p0v5_residual_gat_stage_v4.py",
    "scripts/run_lunar_ice_interaction_gat_acceptance_v4.py",
    "scripts/build_p0v5_residual_gat_training_dataset_v4.py",
    "scripts/train_p0v5_qgr1_residual_gat_v4.py",
    "scripts/train_p0v5_residual_interaction_gat_selector_v4.py",
    "scripts/run_p0v5_qgr1_force_on_v4.py",
    "scripts/finalize_p0v5_residual_portfolio_v4.py",
    "scripts/run_p0v5_residual_gat_heldout_v4.py",
    "scripts/run_p0v5_residual_gat_full_bpc_v4.py",
    "configs/experiments/p0v5_residual_gat_censor_aware_selector_v4.json",
    "tests/test_p0v5_residual_gat_censor_aware_selector_v4.py",
    "plan/GAT/P0V5_RESIDUAL_GAT_CENSOR_AWARE_SELECTOR_V4_IMPLEMENTATION_20260815_ZH.md",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--run-root", type=Path)
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = _load(config_path)
    if config.get("schema_version") != "lunar_ice_bpc.p0v5_residual_gat_experiment_config.v4":
        raise SystemExit("V4 config schema mismatch")
    run_root = (
        args.run_root.resolve() if args.run_root
        else (ROOT / config["run_root"]).resolve()
    )
    if run_root.exists() and any(run_root.iterdir()):
        raise SystemExit("immutable V4 run root is not empty")
    run_root.mkdir(parents=True, exist_ok=True)

    v3_root = (ROOT / config["v3_run_root"]).resolve()
    v3_terminal_path = v3_root / "terminal_decision.json"
    v3_terminal = _load(v3_terminal_path)
    if (
        v3_terminal.get("decision") != "FAIL"
        or v3_terminal.get("reason") != config["v3_expected_terminal_reason"]
    ):
        raise SystemExit("V3 immutable terminal mismatch")
    missing = [path for path in SOURCE_PATHS if not (ROOT / path).is_file()]
    if missing:
        raise SystemExit("V4 implementation source missing:" + ",".join(missing))

    native_binary = _single_native_binary(config)
    differential = _load(NATIVE_DIFFERENTIAL)
    if (
        differential.get("schema_version")
        != "lunar_ice_bpc.p0v5_native_telemetry_differential.v4"
        or differential.get("status") != "PASS"
        or int(differential.get("case_count") or 0) != 500
        or int(differential.get("redline_count") or 0) != 0
        or differential.get("new_binary_sha256") != _sha256(native_binary)
        or not Path(str(differential.get("old_binary") or "")).is_file()
        or differential.get("old_binary_sha256")
        != _sha256(Path(str(differential.get("old_binary") or "")))
    ):
        raise SystemExit("V4 old/new Native 500-case differential is not PASS")
    selected_config = (ROOT / config["selected_exact_config"]).resolve()
    if not selected_config.is_file():
        raise SystemExit("selected exact V5 config missing")
    engine_hash = _engine_hash(config)
    formal_hashes = _formal_hashes(config)
    fixed = _fixed_instances(v3_root, config)
    candidate_pool = _candidate_instances(config)
    if any(row["instance_content_hash"] in formal_hashes for row in (*fixed, *candidate_pool)):
        raise SystemExit("V4 development/formal content hash overlap")
    all_hashes = [row["instance_content_hash"] for row in (*fixed, *candidate_pool)]
    if len(all_hashes) != len(set(all_hashes)):
        raise SystemExit("V4 instance census content hash overlap")
    if min(
        sum(row["scale"] == scale for row in candidate_pool) for scale in (30, 50)
    ) < int(config["candidate_generation"]["initial_heldout_instances_per_scale"]):
        raise SystemExit("generate at least four fresh candidates per scale before V4 init")

    git_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    source_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_source_freeze.v4",
        "status": "FROZEN_BEFORE_ANY_V4_ARM_OUTCOME",
        "git_commit": git_commit, "worktree_may_be_dirty": True,
        "source_sha256": {path: _sha256(ROOT / path) for path in SOURCE_PATHS},
        "exact_execution_source_sha256": {
            path: _sha256(ROOT / path) for path in SOURCE_PATHS
            if path.startswith("native/") or path.startswith(
                "src/lunar_ice_bpc/exact/bpc/pricing/"
            )
        },
        "selected_exact_config": str(selected_config),
        "selected_exact_config_sha256": _sha256(selected_config),
        "native_binary": str(native_binary),
        "native_binary_sha256": _sha256(native_binary),
        "old_native_binary": differential["old_binary"],
        "old_native_binary_sha256": differential["old_binary_sha256"],
        "native_build_dir": str((ROOT / config["native_build_dir"]).resolve()),
        "exact_engine_backend_id": "native_rcspp_bidirectional_root_partial_hybrid_v3",
        "exact_engine_hash": engine_hash,
        "native_telemetry_only_change": True,
        "old_new_native_differential_path": str(NATIVE_DIFFERENTIAL),
        "old_new_native_differential_sha256": _sha256(NATIVE_DIFFERENTIAL),
        "old_new_native_differential_case_count": 500,
        "old_snapshots_rebind_authorized": False,
        "runtime_policy_id": INTERACTION_RUNTIME_POLICY_V4,
        "runtime_implementation_hash": interaction_gat_runtime_implementation_hash_v4(),
        "graph_builder_hash": interaction_graph_builder_hash(),
    }
    census = {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_instance_census.v4",
        "status": "FROZEN_BEFORE_FRESH_ROOT_COLLECTION",
        "fixed_instances": fixed,
        "candidate_pool": candidate_pool,
        "candidate_order": "scale_then_instance_path_fixed_seed_order",
        "maximum_new_instances_per_scale": config["candidate_generation"][
            "maximum_new_instances_per_scale"
        ],
        "v3_calibration_instances_excluded": True,
        "v3_outcomes_training_authority": False,
    }
    tasks = []
    for ordinal, row in enumerate((*fixed, *candidate_pool)):
        tasks.append({
            **row, "ordinal": ordinal,
            "cap_sec": config["execution"]["replay_caps_sec"][str(row["scale"])],
            "snapshot_cap": config["split"]["maximum_natural_contexts_per_instance"],
        })
    root_schedule = {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_root_collection.v4",
        "status": "FROZEN_BEFORE_FRESH_ROOT_COLLECTION",
        "outcome_blind": True, "q0_only": True, "tree_supplement": False,
        "single_native_process": True, "engine_hash": engine_hash,
        "tasks": tasks,
    }
    graph_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_graph_freeze.v4",
        "feature_schema": INTERACTION_FEATURE_SCHEMA_V2,
        "graph_schema": INTERACTION_GRAPH_SCHEMA_V1,
        "graph_builder_hash": interaction_graph_builder_hash(),
        "top_k_cooccurrence": 4, "top_k_travel": 4,
        "node_feature_names": list(INTERACTION_NODE_FEATURES),
        "edge_feature_names": list(INTERACTION_EDGE_FEATURES),
        "context_feature_names": list(INTERACTION_CONTEXT_FEATURES),
        "forbidden_inputs": [
            "arm_outcome", "selected_action", "winner", "post_action_telemetry"
        ],
    }
    interface_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_interface_freeze.v4",
        "runtime_policy": INTERACTION_RUNTIME_POLICY_V4,
        "manifest_schema": INTERACTION_MANIFEST_SCHEMA_V3,
        "checkpoint_schema": INTERACTION_CHECKPOINT_SCHEMA_V3,
        "dataset_schema": INTERACTION_DATASET_SCHEMA_V4,
        "corpus_schema": INTERACTION_CORPUS_SCHEMA_V4,
        "action_universe": config["action_universe"],
        "permanent_forced_veto_arms": ["QB1"],
        "root_only_authority": True,
    }
    diagnostic = {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_v3_diagnostic_binding.v4",
        "v3_terminal_path": str(v3_terminal_path),
        "v3_terminal_sha256": _sha256(v3_terminal_path),
        "v3_outcomes_diagnostic_only": True,
        "v3_outcome_rows_imported": 0,
        "v3_snapshots_imported": 0,
        "qb1_forced_veto_both_scales": True,
    }
    artifacts = {
        "config.freeze.json": {
            **config,
            "schema_version": "lunar_ice_bpc.p0v5_residual_gat_config_freeze.v4",
            "source_config": str(config_path),
            "source_config_sha256": _sha256(config_path),
            "status": "FROZEN_BEFORE_ANY_V4_ARM_OUTCOME",
        },
        "source.freeze.json": source_freeze,
        "instance_census.freeze.json": census,
        "root_collection.execution.freeze.json": root_schedule,
        "graph.freeze.json": graph_freeze,
        "interface.freeze.json": interface_freeze,
        "v3_diagnostic_only.freeze.json": diagnostic,
        "formal_blacklist.freeze.json": {
            "schema_version": "lunar_ice_bpc.p0v5_residual_gat_formal_blacklist.v4",
            "content_hashes": sorted(formal_hashes), "formal_outcomes_read": 0,
        },
    }
    for name, payload in artifacts.items():
        _write_once(run_root / name, payload)
    _write_once(run_root / "prearm.freeze.registry.json", {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_prearm_registry.v4",
        "immutable": True, "arm_outcomes_present_at_freeze": 0,
        "artifact_sha256": {name: _sha256(run_root / name) for name in artifacts},
    })
    state = {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_state.v4",
        "experiment_id": config["experiment_id"], "current_stage": "FRESH_ROOT_COLLECTION",
        "status": "READY", "terminal": False, "terminal_decision": None,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    _write_once(run_root / "state.initial.json", state)
    _write_once(run_root / "state.json", state)
    print(json.dumps({
        "run_root": str(run_root), "engine_hash": engine_hash,
        "fixed_instances": len(fixed), "candidate_pool": len(candidate_pool),
        "root_tasks": len(tasks), "status": "READY_FOR_FRESH_ROOT_COLLECTION",
    }, ensure_ascii=False, indent=2))
    return 0


def _fixed_instances(v3_root, config):
    corpus = _load(v3_root / "corpus.freeze.json")
    mapping = {
        "train": "train", "selector_heldout": "calibration",
        "development_e2e": "development_e2e",
    }
    dedup = {}
    for row in corpus["rows"]:
        source = str(row["partition"])
        if source not in mapping:
            continue
        key = str(row["instance_content_hash"])
        dedup[key] = {
            "scale": int(row["scale"]), "instance_content_hash": key,
            "instance_id": str(row["instance_id"]),
            "instance_path": str(Path(row["instance_path"]).resolve()),
            "desired_partition": mapping[source],
            "source_cohort": f"v3_{source}_content_fresh_v4_execution",
        }
    rows = sorted(dedup.values(), key=lambda row: (
        row["scale"], row["desired_partition"], row["instance_content_hash"]
    ))
    expected = {"train": 14, "calibration": 4, "development_e2e": 3}
    for scale in (30, 50):
        counts = {
            part: sum(row["scale"] == scale and row["desired_partition"] == part for row in rows)
            for part in expected
        }
        if counts != expected:
            raise SystemExit(f"V3 fixed instance census mismatch scale{scale}:{counts}")
    return rows


def _candidate_instances(config):
    root = (ROOT / config["candidate_instance_root"]).resolve()
    rows = []
    for path in sorted(root.rglob("instance_*_logical_graph.json")):
        data = load_lunar_ice_data(_load(path))
        if int(data.scale) not in {30, 50}:
            continue
        rows.append({
            "scale": int(data.scale),
            "instance_content_hash": str(data.instance_content_hash),
            "instance_id": str(data.instance_id), "instance_path": str(path.resolve()),
            "desired_partition": "candidate_pool",
            "source_cohort": "fresh_generated_v4_candidate",
        })
    maximum = int(config["candidate_generation"]["maximum_new_instances_per_scale"])
    if any(sum(row["scale"] == scale for row in rows) > maximum for scale in (30, 50)):
        raise SystemExit("V4 candidate pool exceeds frozen maximum")
    return sorted(rows, key=lambda row: (row["scale"], row["instance_path"]))


def _formal_hashes(config):
    hashes = set()
    root = (ROOT / config["formal_instance_root"]).resolve()
    for scale in (5, 10, 20, 30, 50):
        directory = root / f"lunar_ice_sp50_{scale:03d}"
        for path in sorted(directory.glob("instance_*_logical_graph.json"))[:20]:
            hashes.add(str(load_lunar_ice_data(_load(path)).instance_content_hash))
    return hashes


def _single_native_binary(config):
    paths = list((ROOT / config["native_build_dir"]).glob("lunar_spprc_native*.so"))
    if len(paths) != 1:
        raise SystemExit("V4 build must contain exactly one native extension")
    return paths[0].resolve()


def _engine_hash(config):
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join((
        str((ROOT / config["native_build_dir"]).resolve()), str((ROOT / "src").resolve())
    ))
    code = (
        "from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import spprc_engine_build_hash;"
        "print(spprc_engine_build_hash('native_rcspp_bidirectional_root_partial_hybrid_v3'))"
    )
    return subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, env=environment, check=True,
        text=True, stdout=subprocess.PIPE,
    ).stdout.strip()


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write_once(path, payload):
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != encoded:
        raise SystemExit(f"immutable V4 artifact drift:{path}")
    if not path.exists():
        path.write_text(encoded, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Create the immutable bootstrap chain for Native-frontier GAT V7."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from scripts.p0v5_native_frontier_gat_qd1_v7_common import (  # noqa: E402
    CONFIG,
    load,
    sha256,
    stable_hash,
    verify_v6_terminal,
    write_once,
)
from lunar_ice_bpc.guidance.frontier_gat_qd1_v7 import (  # noqa: E402
    CONTEXT_FEATURE_NAMES,
    EDGE_FEATURE_NAMES,
    FRONTIER_BUNDLE_SCHEMA_V1,
    FRONTIER_CHECKPOINT_SCHEMA_V1,
    FRONTIER_DATASET_SCHEMA_V1,
    FRONTIER_FEATURE_SCHEMA_V1,
    FRONTIER_GRAPH_SCHEMA_V1,
    FRONTIER_MATCHED_SCHEMA_V1,
    FRONTIER_RUNTIME_POLICY_V7,
    MODEL_SEEDS,
    NODE_FEATURE_NAMES,
    PROBE_BOUNDARY,
)
from lunar_ice_bpc.guidance.frontier_gat_qd1_runtime_v7 import (  # noqa: E402
    MANIFEST_SCHEMA_V1,
)


SOURCE_PATHS = (
    "native/lunar_spprc/include/lunar_spprc/native_pricer.hpp",
    "native/lunar_spprc/src/native_pricer.cpp",
    "native/lunar_spprc/src/pybind_module.cpp",
    "native/lunar_spprc/tests/test_native_pricer.cpp",
    "src/lunar_ice_bpc/exact/bpc/pricing/backends/base.py",
    "src/lunar_ice_bpc/exact/bpc/pricing/backends/native_rcspp.py",
    "src/lunar_ice_bpc/exact/bpc/pricing/backends/native_bidirectional_hybrid.py",
    "src/lunar_ice_bpc/guidance/frontier_gat_qd1_v7.py",
    "src/lunar_ice_bpc/guidance/frontier_gat_qd1_runtime_v7.py",
    "src/lunar_ice_bpc/guidance/proof_queue_label_state_runtime.py",
    "scripts/p0v5_native_frontier_gat_qd1_v7_common.py",
    "scripts/initialize_p0v5_native_frontier_gat_qd1_selector_v7.py",
    "scripts/manage_p0v5_native_frontier_gat_corpus_v7.py",
    "scripts/run_p0v5_native_frontier_probe_matrix_v7.py",
    "scripts/build_p0v5_native_frontier_gat_dataset_v7.py",
    "scripts/train_p0v5_native_frontier_gat_selector_v7.py",
    "scripts/run_p0v5_native_frontier_gat_heldout_v7.py",
    "scripts/run_lunar_ice_frontier_gat_acceptance_v7.py",
    "scripts/run_p0v5_native_frontier_gat_full_bpc_v7.py",
    "scripts/replay_p0v5_qg2_label_state_snapshot.py",
    "scripts/run_lunar_ice_native_spprc_acceptance.py",
    "scripts/generate_lunar_real_map_benchmark.py",
    "scripts/run_p0v5_residual_gat_full_bpc_v4.py",
    "scripts/run_p0v5_interaction_gat_full_bpc_v2.py",
    "scripts/run_p0v5_context_queue_portfolio_full_bpc.py",
    "scripts/analyze_p0v5_qg2_paired_acceptance.py",
    "configs/experiments/p0v5_native_frontier_gat_qd1_selector_v7.json",
    "tests/test_p0v5_native_frontier_gat_qd1_selector_v7.py",
    "plan/GAT/P0V5_NATIVE_FRONTIER_INTERACTION_GAT_QD1_SELECTOR_V7_IMPLEMENTATION_20260817_ZH.md",
    "plan/GAT/P0V5_NATIVE_FRONTIER_INTERACTION_GAT_QD1_SELECTOR_V7_RUNBOOK_20260817_ZH.md",
)


def _blacklist() -> dict:
    hashes: set[str] = set()
    sources = []
    for relative in (
        "runs/p0v5_interaction_gat_queue_selector_v3_20260814/corpus.freeze.json",
        "runs/p0v5_residual_gat_censor_aware_selector_v4_20260815/corpus.freeze.json",
        "runs/p0v5_residual_gat_censor_aware_selector_v5_20260816/corpus.freeze.json",
        "runs/p0v5_minimal_interaction_gat_qd1_selector_v6_20260817/corpus.freeze.json",
    ):
        path = ROOT / relative
        if not path.is_file():
            continue
        payload = load(path)
        hashes.update(str(row["instance_content_hash"]) for row in payload["rows"])
        sources.append({"path": str(path), "sha256": sha256(path)})
    for relative in (
        "runs/p0v5_minimal_interaction_gat_qd1_selector_v6_20260817/formal_blacklist.freeze.json",
        "runs/p0v5_interaction_gat_queue_selector_v3_20260814/protected_blacklist.freeze.json",
    ):
        path = ROOT / relative
        if not path.is_file():
            continue
        payload = load(path)
        hashes.update(str(value) for value in payload.get("content_hashes", ()))
        sources.append({"path": str(path), "sha256": sha256(path)})
    return {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_gat_blacklist.v1",
        "historical_formal_protected_excluded": True,
        "content_hashes": sorted(hashes), "sources": sources,
    }


def _engine_bindings(build_dir: Path) -> dict:
    code = """
import json
from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import spprc_engine_build_hash
from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import NATIVE_INPROCESS_BACKEND_ID,NATIVE_HOST_BACKEND_ID
from lunar_ice_bpc.exact.bpc.pricing.backends.native_bidirectional_hybrid import NATIVE_BIDIRECTIONAL_ROOT_PARTIAL_HYBRID_BACKEND_ID
import lunar_spprc_native
print(json.dumps({
 'inprocess': spprc_engine_build_hash(NATIVE_INPROCESS_BACKEND_ID),
 'host': spprc_engine_build_hash(NATIVE_HOST_BACKEND_ID),
 'root_partial_hybrid': spprc_engine_build_hash(NATIVE_BIDIRECTIONAL_ROOT_PARTIAL_HYBRID_BACKEND_ID),
 'build_info': dict(lunar_spprc_native.build_info()),
 'module_path': lunar_spprc_native.__file__,
}, sort_keys=True))
"""
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        (str(build_dir), str(ROOT / "src"))
    )
    output = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, env=environment,
        check=True, text=True, stdout=subprocess.PIPE,
    ).stdout
    return json.loads(output)


def _diagnostic_contexts() -> dict:
    corpus_path = (
        ROOT
        / "runs/p0v5_minimal_interaction_gat_qd1_selector_v6_20260817/corpus.freeze.json"
    )
    corpus = load(corpus_path)
    rows = [
        dict(row) for row in corpus["rows"]
        if row["partition"] in {"train", "calibration"}
    ]
    selected = []
    for scale in (30, 50):
        candidates = sorted(
            (row for row in rows if int(row["scale"]) == scale),
            key=lambda row: stable_hash({
                "purpose": "v7_probe_overhead_diagnostic",
                "scale": scale,
                "instance": row["instance_content_hash"],
                "state": row["state_hash"],
            }),
        )
        if len(candidates) < 20:
            raise SystemExit(f"V7 diagnostic preaction coverage below 20:scale{scale}")
        for row in candidates[:20]:
            path = Path(str(row["snapshot_path"]))
            if not path.is_file() or sha256(path) != str(row["snapshot_sha256"]):
                raise SystemExit("V7_V6_PREACTION_DIAGNOSTIC_HASH_DRIFT")
            selected.append({
                "scale": scale,
                "context_id": row["context_id"],
                "instance_content_hash": row["instance_content_hash"],
                "instance_path": str(Path(row["instance_path"]).resolve()),
                "instance_sha256": sha256(Path(row["instance_path"])),
                "state_hash": row["state_hash"],
                "snapshot_path": str(path.resolve()),
                "snapshot_sha256": str(row["snapshot_sha256"]),
                "diagnostic_only": True,
                "arm_outcomes_imported": 0,
            })
    return {
        "schema_version": "lunar_ice_bpc.p0v5_v7_probe_diagnostic_index.v1",
        "source_v6_corpus_sha256": sha256(corpus_path),
        "selection_is_outcome_blind": True,
        "performance_authority": False,
        "rows": selected,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--run-root", type=Path)
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = load(config_path)
    if config.get("schema_version") != (
        "lunar_ice_bpc.p0v5_native_frontier_gat_qd1_config.v7"
    ):
        raise SystemExit("V7 config schema mismatch")
    run_root = (
        args.run_root.resolve()
        if args.run_root
        else (ROOT / str(config["run_root"])).resolve()
    )
    if run_root.exists() and any(run_root.iterdir()):
        raise SystemExit("immutable V7 run root is not empty")
    missing = [relative for relative in SOURCE_PATHS if not (ROOT / relative).is_file()]
    if missing:
        raise SystemExit("V7 implementation source missing:" + ",".join(missing))
    v6 = verify_v6_terminal(config)
    binary = (ROOT / str(config["native_binary"])).resolve()
    selected_config = (ROOT / str(config["selected_exact_config"])).resolve()
    if not binary.is_file() or not selected_config.is_file():
        raise SystemExit("V7 native binary or exact config missing")
    build_dir = (ROOT / str(config["native_build_dir"])).resolve()
    ctest = subprocess.run(
        ["ctest", "--test-dir", str(build_dir), "--output-on-failure"],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    if ctest.returncode:
        raise SystemExit("V7_NATIVE_DIFFERENTIAL_REDLINE:\n" + ctest.stdout)
    bindings = _engine_bindings(build_dir)
    build_info = dict(bindings["build_info"])
    if build_info.get("frontier_probe_policy") != (
        "native_q0_4096_inplace_qd1_switch_v7"
    ):
        raise SystemExit("V7 frontier Native capability missing")

    run_root.mkdir(parents=True, exist_ok=True)
    git_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    source_hashes = {relative: sha256(ROOT / relative) for relative in SOURCE_PATHS}
    config_freeze = {
        **config,
        "source_config": str(config_path),
        "source_config_sha256": sha256(config_path),
        "status": "BOOTSTRAP_FROZEN_BEFORE_DIAGNOSTIC_WALL_OUTCOMES",
    }
    source_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_native_frontier_gat_source_freeze.v7",
        "status": "BOOTSTRAP_FROZEN_BEFORE_DIAGNOSTIC_WALL_OUTCOMES",
        "git_commit": git_commit,
        "worktree_may_be_dirty": True,
        "source_sha256": source_hashes,
        "native_build_dir": str(build_dir),
        "native_binary": str(binary),
        "native_binary_sha256": sha256(binary),
        "selected_exact_config": str(selected_config),
        "selected_exact_config_sha256": sha256(selected_config),
        "engine_hashes": {
            name: bindings[name] for name in (
                "inprocess", "host", "root_partial_hybrid"
            )
        },
        "build_info": build_info,
        "v5_frozen_binary_preserved": {
            "path": str((ROOT / "build/native-spprc-residual-gat-v4/lunar_spprc_native.cpython-313-x86_64-linux-gnu.so").resolve()),
            "sha256": "c747bcdc674aabd7809b1b253300c033cfd37fad493f02bf3cf623136d2c42f4"
        },
    }
    differential = {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_native_differential.v7",
        "status": "PASS",
        "case_count": 500,
        "policies": ["Q0", "QPF0", "QPD1"],
        "comparisons": [
            "status", "search_exhaustive", "frontier_empty",
            "legal_route_reduced_cost_multiset", "migration_count",
            "creation_id_hash", "no_negative_certificate",
        ],
        "ctest_command": ["ctest", "--test-dir", str(build_dir), "--output-on-failure"],
        "ctest_stdout_sha256": stable_hash(ctest.stdout),
        "ctest_stdout": ctest.stdout,
        "state_size_bytes": int(build_info["label_state_bytes"]),
    }
    if differential["state_size_bytes"] != 176:
        raise SystemExit("V7 State ABI redline")
    interface = {
        "schema_version": "lunar_ice_bpc.p0v5_native_frontier_gat_interface.v7",
        "runtime_policy": FRONTIER_RUNTIME_POLICY_V7,
        "feature_schema": FRONTIER_FEATURE_SCHEMA_V1,
        "graph_schema": FRONTIER_GRAPH_SCHEMA_V1,
        "bundle_schema": FRONTIER_BUNDLE_SCHEMA_V1,
        "checkpoint_schema": FRONTIER_CHECKPOINT_SCHEMA_V1,
        "manifest_schema": MANIFEST_SCHEMA_V1,
        "dataset_schema": FRONTIER_DATASET_SCHEMA_V1,
        "matched_outcome_schema": FRONTIER_MATCHED_SCHEMA_V1,
        "probe_boundary": PROBE_BOUNDARY,
        "probe_modes": config["native_probe_modes"],
        "action_universe": config["action_universe"],
        "forced_veto_actions": config["permanent_forced_veto_arms"],
        "node_feature_names": list(NODE_FEATURE_NAMES),
        "edge_feature_names": list(EDGE_FEATURE_NAMES),
        "context_feature_names": list(CONTEXT_FEATURE_NAMES),
        "ensemble_seeds": list(MODEL_SEEDS),
        "python_callback_inside_native": False,
        "torch_inside_native": False,
        "state_modified": False,
        "root_only_authority": True,
    }
    v6_import = {
        "schema_version": "lunar_ice_bpc.p0v5_v6_diagnostic_import.v7",
        "v6_run_root": v6["run_root"],
        "v6_terminal_reason": v6["terminal"]["reason"],
        "artifact_sha256": {
            "terminal_decision.json": v6["terminal_sha256"],
            "state.json": v6["state_sha256"],
        },
        "v6_outcomes_diagnostic_only": True,
        "arm_outcomes_imported": 0,
        "training_rows_imported": 0,
    }
    graph = {
        "schema_version": FRONTIER_GRAPH_SCHEMA_V1,
        "node_count": 64,
        "depth_bins": [0.0, 0.05, 0.10, 0.20, 0.30, 0.40, 0.55, 0.75],
        "rc_bins": 8,
        "edge_types": ["self_loop", "depth_neighbor", "rc_neighbor", "parent_forward", "parent_reverse"],
        "deterministic_sort": ["source", "target", "type"],
        "post_action_features_forbidden": True,
    }
    diagnostic = _diagnostic_contexts()
    acceptance = {
        "schema_version": "lunar_ice_bpc.p0v5_native_frontier_gat_acceptance.v7",
        "gates": config["gates"],
        "threshold_grid": config["threshold_grid"],
        "correctness_redline_limit": 0,
        "heldout_one_shot": True,
        "controls_cannot_be_candidate": True,
        "production_review_separate": True,
    }
    artifacts = {
        "config.freeze.json": config_freeze,
        "source.freeze.json": source_freeze,
        "native_differential.report.json": differential,
        "interface.freeze.json": interface,
        "graph.freeze.json": graph,
        "v6_diagnostic_import.freeze.json": v6_import,
        "probe_diagnostic_contexts.freeze.json": diagnostic,
        "acceptance.freeze.json": acceptance,
        "blacklist.freeze.json": _blacklist(),
    }
    for name, payload in artifacts.items():
        write_once(run_root / name, payload)
    write_once(run_root / "bootstrap.freeze.registry.json", {
        "schema_version": "lunar_ice_bpc.p0v5_native_frontier_gat_bootstrap_registry.v7",
        "immutable": True,
        "frozen_before_wall_outcomes": True,
        "artifact_sha256": {
            name: sha256(run_root / name) for name in artifacts
        },
    })
    state = {
        "schema_version": "lunar_ice_bpc.p0v5_native_frontier_gat_state.v7",
        "experiment_id": config["experiment_id"],
        "current_stage": "PROBE_DIAGNOSTIC",
        "status": "READY",
        "terminal": False,
        "terminal_decision": None,
        "development_only": True,
        "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    write_once(run_root / "state.initial.json", state)
    write_once(run_root / "state.json", state)
    print(json.dumps({
        "run_root": str(run_root),
        "status": "READY_FOR_PROBE_DIAGNOSTIC",
        "native_binary_sha256": sha256(binary),
        "root_partial_hybrid_engine_hash": bindings["root_partial_hybrid"],
        "diagnostic_context_count": len(diagnostic["rows"]),
        "v5_binary_preserved": source_freeze["v5_frozen_binary_preserved"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Initialize the immutable V6 Q0/QD1 Interaction-GAT evidence chain."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from scripts.p0v5_minimal_interaction_gat_qd1_v6_common import (  # noqa: E402
    CONFIG, copied_corpus, load, sha256, validate_v5_import, write_once,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_runtime_v6 import (  # noqa: E402
    INTERACTION_GAT_RUNTIME_POLICY_V6,
    interaction_gat_runtime_implementation_hash_v6,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import (  # noqa: E402
    INTERACTION_FEATURE_SCHEMA_V2, INTERACTION_GRAPH_SCHEMA_V1,
    interaction_graph_builder_hash,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v6 import (  # noqa: E402
    INTERACTION_CHECKPOINT_SCHEMA_V6, INTERACTION_DATASET_SCHEMA_V6,
    INTERACTION_MANIFEST_SCHEMA_V6,
)


V6_SOURCE_PATHS = (
    "src/lunar_ice_bpc/guidance/interaction_gat_queue_v6.py",
    "src/lunar_ice_bpc/guidance/interaction_gat_queue_runtime_v6.py",
    "scripts/p0v5_minimal_interaction_gat_qd1_v6_common.py",
    "scripts/initialize_p0v5_minimal_interaction_gat_qd1_selector_v6.py",
    "scripts/build_p0v5_minimal_interaction_gat_qd1_dataset_v6.py",
    "scripts/train_p0v5_minimal_interaction_gat_qd1_selector_v6.py",
    "scripts/run_p0v5_minimal_interaction_gat_qd1_heldout_v6.py",
    "scripts/run_p0v5_minimal_interaction_gat_qd1_full_bpc_v6.py",
    "scripts/finalize_p0v5_minimal_interaction_gat_qd1_v6.py",
    "scripts/run_lunar_ice_interaction_gat_acceptance_v6.py",
    "scripts/run_p0v5_residual_gat_full_bpc_v4.py",
    "scripts/run_p0v5_interaction_gat_full_bpc_v2.py",
    "scripts/run_p0v5_context_queue_portfolio_full_bpc.py",
    "configs/experiments/p0v5_minimal_interaction_gat_qd1_selector_v6.json",
    "tests/test_p0v5_minimal_interaction_gat_qd1_selector_v6.py",
    "plan/GAT/P0V5_MINIMAL_INTERACTION_GAT_QD1_SELECTOR_V6_IMPLEMENTATION_20260817_ZH.md",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--run-root", type=Path)
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = load(config_path)
    if config.get("schema_version") != (
        "lunar_ice_bpc.p0v5_minimal_interaction_gat_qd1_config.v6"
    ):
        raise SystemExit("V6 config schema mismatch")
    run_root = (
        args.run_root.resolve() if args.run_root
        else (ROOT / str(config["run_root"])).resolve()
    )
    if run_root.exists() and any(run_root.iterdir()):
        raise SystemExit("immutable V6 run root is not empty")
    missing = [relative for relative in V6_SOURCE_PATHS if not (ROOT / relative).is_file()]
    if missing:
        raise SystemExit("V6 implementation source missing:" + ",".join(missing))

    imported = validate_v5_import(config)
    run_root.mkdir(parents=True, exist_ok=True)
    corpus = copied_corpus(run_root, imported)
    v5_root = Path(imported["v5_root"])
    git_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    source_hashes = {relative: sha256(ROOT / relative) for relative in V6_SOURCE_PATHS}
    source = imported["source"]
    source_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_minimal_interaction_gat_source_freeze.v6",
        "status": "FROZEN_BEFORE_V6_TRAINING",
        "git_commit": git_commit, "worktree_may_be_dirty": True,
        "source_sha256": source_hashes,
        "exact_engine_hash": source["exact_engine_hash"],
        "native_binary": source["native_binary"],
        "native_binary_sha256": source["native_binary_sha256"],
        "selected_exact_config": source["selected_exact_config"],
        "selected_exact_config_sha256": source["selected_exact_config_sha256"],
        "native_differential_path": imported["native_differential_path"],
        "native_differential_sha256": sha256(imported["native_differential_path"]),
        "runtime_policy_id": INTERACTION_GAT_RUNTIME_POLICY_V6,
        "runtime_implementation_hash": interaction_gat_runtime_implementation_hash_v6(),
        "graph_builder_hash": interaction_graph_builder_hash(),
        "native_or_exact_source_modified_by_v6": False,
    }
    evidence = {
        "schema_version": "lunar_ice_bpc.p0v5_v5_qd1_evidence_import.v6",
        "status": "FROZEN_BEFORE_V6_TRAINING",
        "v5_run_root": str(v5_root.resolve()),
        "v5_terminal_reason": imported["terminal"]["reason"],
        "v5_artifact_sha256": dict(config["expected_v5_artifact_sha256"]),
        "raw_matched_tasks": len(imported["raw"]["rows"]),
        "collapsed_qd1_outcomes": len(imported["collapsed"]["rows"]),
        "resource_failure_rows_folded_into_adverse": sum(
            bool(row.get("resource_censor_positive"))
            for row in imported["collapsed"]["rows"]
        ),
        "train_oracle": {
            scale: imported["train_oracle"]["scales"][scale]
            for scale in ("30", "50")
        },
        "calibration_oracle": imported["calibration_oracle"],
        "heldout_outcomes_imported": 0,
        "development_e2e_outcomes_imported": 0,
        "formal_outcomes_imported": 0,
        "qgr1_outcomes_imported": 0,
        "qgr1_trace_diagnostic_only": True,
    }
    interface = {
        "schema_version": "lunar_ice_bpc.p0v5_minimal_interaction_gat_interface.v6",
        "runtime_policy": INTERACTION_GAT_RUNTIME_POLICY_V6,
        "feature_schema": INTERACTION_FEATURE_SCHEMA_V2,
        "graph_schema": INTERACTION_GRAPH_SCHEMA_V1,
        "manifest_schema": INTERACTION_MANIFEST_SCHEMA_V6,
        "checkpoint_schema": INTERACTION_CHECKPOINT_SCHEMA_V6,
        "dataset_schema": INTERACTION_DATASET_SCHEMA_V6,
        "action_universe": ["Q0", "QD1"],
        "permanent_forced_veto_arms": ["QB1", "QGR1"],
        "model_outputs": [
            "benefit_probability", "conditional_positive_gain",
            "adverse_probability",
        ],
        "ranker_fields_forbidden": True,
        "root_only_authority": True,
    }
    graph = dict(imported["graph"])
    graph["schema_version"] = "lunar_ice_bpc.p0v5_interaction_graph_freeze.v6"
    graph["source_v5_graph_sha256"] = sha256(v5_root / "graph.freeze.json")
    split = dict(imported["split"])
    split["schema_version"] = "lunar_ice_bpc.p0v5_interaction_gat_qd1_split.v1"
    split["source_v5_split_sha256"] = sha256(v5_root / "instance_split.freeze.json")
    folds = dict(imported["folds"])
    folds["schema_version"] = "lunar_ice_bpc.p0v5_interaction_gat_qd1_cv_folds.v1"
    folds["source_v5_folds_sha256"] = sha256(v5_root / "grouped_cv_folds.freeze.json")
    formal = dict(imported["formal"])
    formal["formal_outcomes_read"] = 0
    formal["source_v5_formal_blacklist_sha256"] = sha256(
        v5_root / "formal_blacklist.freeze.json"
    )
    config_freeze = {
        **config,
        "source_config": str(config_path),
        "source_config_sha256": sha256(config_path),
        "status": "FROZEN_BEFORE_V6_TRAINING",
    }
    acceptance = {
        "schema_version": "lunar_ice_bpc.p0v5_minimal_interaction_gat_acceptance.v6",
        "calibration": config["calibration_gate"],
        "heldout": {
            "minimum_activation_instances_per_scale": 2,
            "net_gm_strictly_below": 1.0,
            "harmful_adverse_censor_limit": 0,
            "warm_preparation_p99_ms_at_most": 10.0,
            "one_shot_no_reselection": True,
        },
        "development_e2e": {
            "minimum_activation_instances_per_scale": 2,
            "net_gm_strictly_below": 1.0,
            "exact_count_may_not_decrease": True,
            "worst_instance_ratio_at_most": 1.10,
            "tree_model_calls_required": 0,
        },
        "formal": {
            "small_scale_model_calls_required": 0,
            "small_scale_gm_at_most": 1.01,
            "large_scale_gm_strictly_below": 1.0,
            "p90_ratio_at_most": 1.05,
            "worst_ratio_at_most": 1.20,
            "minimum_activation_instances_per_large_scale": 5,
        },
    }
    artifacts = {
        "config.freeze.json": config_freeze,
        "source.freeze.json": source_freeze,
        "v5_qd1_evidence_import.freeze.json": evidence,
        "corpus.freeze.json": corpus,
        "instance_split.freeze.json": split,
        "grouped_cv_folds.freeze.json": folds,
        "graph.freeze.json": graph,
        "interface.freeze.json": interface,
        "formal_blacklist.freeze.json": formal,
        "acceptance.freeze.json": acceptance,
    }
    for name, payload in artifacts.items():
        write_once(run_root / name, payload)
    snapshot_hashes = {
        str(Path(row["snapshot_path"]).relative_to(run_root)): row["snapshot_sha256"]
        for row in corpus["rows"]
    }
    write_once(run_root / "freeze.registry.json", {
        "schema_version": "lunar_ice_bpc.p0v5_minimal_interaction_gat_registry.v6",
        "immutable": True, "frozen_before_training": True,
        "artifact_sha256": {
            **{name: sha256(run_root / name) for name in artifacts},
            **snapshot_hashes,
        },
    })
    state = {
        "schema_version": "lunar_ice_bpc.p0v5_minimal_interaction_gat_state.v6",
        "experiment_id": config["experiment_id"],
        "current_stage": "DATASET_BUILD", "status": "READY",
        "terminal": False, "terminal_decision": None,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    write_once(run_root / "state.initial.json", state)
    write_once(run_root / "state.json", state)
    print(json.dumps({
        "run_root": str(run_root), "status": "READY_FOR_DATASET_BUILD",
        "copied_preaction_snapshots": len(corpus["rows"]),
        "raw_matched_tasks": len(imported["raw"]["rows"]),
        "collapsed_qd1_outcomes": len(imported["collapsed"]["rows"]),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

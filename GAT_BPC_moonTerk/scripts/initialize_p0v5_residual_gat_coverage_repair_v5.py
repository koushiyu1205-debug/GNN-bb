#!/usr/bin/env python3
"""Freeze the V5 coverage-repair bootstrap before new root screening."""

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
from scripts.p0v5_residual_gat_coverage_repair_v5_common import (  # noqa: E402
    CONFIG, copy_imported_snapshots, load, sha256, validate_v4_import,
    write_once,
)


V5_SOURCE_PATHS = (
    "scripts/p0v5_residual_gat_coverage_repair_v5_common.py",
    "scripts/initialize_p0v5_residual_gat_coverage_repair_v5.py",
    "scripts/manage_p0v5_residual_gat_coverage_census_v5.py",
    "scripts/generate_lunar_real_map_benchmark.py",
    "configs/experiments/p0v5_residual_gat_censor_aware_selector_v5.json",
    "tests/test_p0v5_residual_gat_coverage_repair_v5.py",
    "plan/GAT/P0V5_RESIDUAL_GAT_COVERAGE_REPAIR_V5_IMPLEMENTATION_20260816_ZH.md",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--run-root", type=Path)
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = load(config_path)
    if config.get("schema_version") != (
        "lunar_ice_bpc.p0v5_residual_gat_coverage_repair_config.v5"
    ):
        raise SystemExit("V5 coverage-repair config schema mismatch")
    run_root = (
        args.run_root.resolve() if args.run_root
        else (ROOT / str(config["run_root"])).resolve()
    )
    if run_root.exists() and any(run_root.iterdir()):
        raise SystemExit("immutable V5 run root is not empty")
    missing = [relative for relative in V5_SOURCE_PATHS if not (ROOT / relative).is_file()]
    if missing:
        raise SystemExit("V5 implementation source missing:" + ",".join(missing))

    import_data = validate_v4_import(config)
    run_root.mkdir(parents=True, exist_ok=True)
    imported_rows = copy_imported_snapshots(run_root, import_data)
    base_config_path = (ROOT / str(config["v4_runtime_config"])).resolve()
    base_config = load(base_config_path)
    full_config = {
        **base_config,
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_config_freeze.v4",
        "experiment_id": str(config["experiment_id"]),
        "run_root": str(config["run_root"]),
        "candidate_instance_root": str(config["candidate_instance_root"]),
        "candidate_generation": {
            "seed_base": int(config["candidate_seed_base"]),
            "maximum_new_instances_per_scale": int(config["maximum_new_candidates"]),
            "initial_heldout_instances_per_scale": 4,
            "outcome_blind_fixed_seed_order": True,
        },
        "coverage_repair_chain_version": "v5",
        "coverage_repair_source_v4_run_root": str(config["v4_run_root"]),
        "coverage_repair_required_new_scale30_eligible": int(
            config["required_new_eligible_candidates"]
        ),
        "source_config": str(config_path),
        "source_config_sha256": sha256(config_path),
        "source_runtime_config": str(base_config_path),
        "source_runtime_config_sha256": sha256(base_config_path),
        "status": "FROZEN_BEFORE_ANY_V5_ARM_OUTCOME",
    }

    engine_hash = _engine_hash(full_config)
    if engine_hash != str(config["expected_engine_hash"]):
        raise SystemExit(f"V5_PREACTION_IMPORT_HASH_DRIFT:engine:{engine_hash}")
    v4_source = dict(import_data["source"])
    source_hashes = dict(v4_source["source_sha256"])
    source_hashes.update({relative: sha256(ROOT / relative) for relative in V5_SOURCE_PATHS})
    git_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    source_freeze = {
        **v4_source,
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_source_freeze.v4",
        "status": "FROZEN_BEFORE_ANY_V5_ARM_OUTCOME",
        "git_commit": git_commit, "worktree_may_be_dirty": True,
        "source_sha256": source_hashes,
        "exact_engine_hash": engine_hash,
        "v4_preaction_import_authorized": True,
        "v4_source_freeze_path": str(Path(import_data["source_freeze_path"]).resolve()),
        "v4_source_freeze_sha256": sha256(import_data["source_freeze_path"]),
        "old_snapshots_rebind_authorized": False,
    }

    imported_by_hash = {}
    for row in imported_rows:
        imported_by_hash.setdefault(str(row["instance_content_hash"]), []).append(row)
    fixed = [dict(row) for row in import_data["fixed_instances"]]
    candidates = [dict(row) for row in import_data["eligible_candidate_instances"]]
    ineligible = [
        {
            **dict(row), "screened_ineligible": True,
            "reason": "NO_NATURAL_V5_ROOT_FALLBACK",
        }
        for row in import_data["screened_ineligible_instances"]
    ]
    candidate_sequence = [{
        "accepted_instance_index": index,
        "scale": int(config["candidate_scale"]),
        "selection_order": index,
        "status": "NOT_GENERATED",
    } for index in range(1, int(config["maximum_new_candidates"]) + 1)]

    import_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_v4_preaction_import.v5",
        "status": "FROZEN_BEFORE_NEW_V5_CANDIDATE_SCREEN",
        "v4_terminal_path": str(Path(import_data["terminal_path"]).resolve()),
        "v4_terminal_sha256": sha256(import_data["terminal_path"]),
        "v4_source_freeze_path": str(Path(import_data["source_freeze_path"]).resolve()),
        "v4_source_freeze_sha256": sha256(import_data["source_freeze_path"]),
        "v4_prearm_registry_path": str(Path(import_data["prearm_registry_path"]).resolve()),
        "v4_prearm_registry_sha256": sha256(import_data["prearm_registry_path"]),
        "v4_outcomes_imported": 0, "arm_outcomes_imported": 0,
        "fixed_instances": fixed,
        "eligible_candidate_instances": candidates,
        "screened_ineligible_instances": ineligible,
        "snapshot_rows": imported_rows,
        "observed_counts": import_data["observed_counts"],
    }
    census = {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_instance_census.v5",
        "status": "BOOTSTRAP_FROZEN_BEFORE_NEW_CANDIDATE_SCREEN",
        "fixed_instances": fixed,
        "v4_eligible_candidate_instances": candidates,
        "v4_screened_ineligible_instances": ineligible,
        "new_scale30_candidate_sequence": candidate_sequence,
        "selection_rule": "first_three_eligible_in_accepted_instance_index_order",
        "maximum_new_scale30_candidates": int(config["maximum_new_candidates"]),
        "required_new_scale30_eligible": int(config["required_new_eligible_candidates"]),
        "arm_outcomes_read": 0,
    }
    generation_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_candidate_generation.v5",
        "status": "FROZEN_BEFORE_NEW_CANDIDATE_GENERATION",
        "output_root": str((ROOT / str(config["candidate_instance_root"])).resolve()),
        "manifest": str((ROOT / str(config["candidate_instance_root"]) / "manifest.json").resolve()),
        "scale": int(config["candidate_scale"]),
        "seed_base": int(config["candidate_seed_base"]),
        "maximum_new_candidates": int(config["maximum_new_candidates"]),
        "required_new_eligible": int(config["required_new_eligible_candidates"]),
        "root_collection_cap_sec": int(config["root_collection_cap_sec"]),
        "snapshot_cap": int(config["maximum_natural_contexts_per_instance"]),
        "single_generator_process": True, "single_native_process": True,
        "outcome_blind": True, "arm_outcomes_read": 0,
        "generator": config["generator"],
    }
    graph = load(Path(import_data["v4_root"]) / "graph.freeze.json")
    interface = load(Path(import_data["v4_root"]) / "interface.freeze.json")
    formal = dict(import_data["formal_payload"])
    formal["formal_outcomes_read"] = 0

    artifacts = {
        "config.freeze.json": full_config,
        "source.freeze.json": source_freeze,
        "v4_preaction_import.freeze.json": import_freeze,
        "instance_census.freeze.json": census,
        "candidate_generation.freeze.json": generation_freeze,
        "graph.freeze.json": graph,
        "interface.freeze.json": interface,
        "formal_blacklist.freeze.json": formal,
    }
    for name, payload in artifacts.items():
        write_once(run_root / name, payload)
    imported_artifacts = {
        str(Path(row["snapshot_path"]).resolve().relative_to(run_root)): row["snapshot_sha256"]
        for row in imported_rows
    }
    write_once(run_root / "prearm.freeze.registry.json", {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_prearm_registry.v5",
        "immutable": True, "arm_outcomes_present_at_freeze": 0,
        "artifact_sha256": {
            **{name: sha256(run_root / name) for name in artifacts},
            **imported_artifacts,
        },
    })
    state = {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_state.v5",
        "experiment_id": str(config["experiment_id"]),
        "current_stage": "SCALE30_CANDIDATE_CENSUS", "status": "READY",
        "terminal": False, "terminal_decision": None,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    write_once(run_root / "state.initial.json", state)
    write_once(run_root / "state.json", state)
    write_once(run_root / "candidate_census.current.json", {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_candidate_census_status.v5",
        "status": "READY", "screened_new_candidates": 0,
        "eligible_new_candidates": 0,
        "required_eligible_new_candidates": int(config["required_new_eligible_candidates"]),
        "maximum_new_candidates": int(config["maximum_new_candidates"]),
        "rows": [], "arm_outcomes_read": 0,
    })
    print(json.dumps({
        "run_root": str(run_root), "engine_hash": engine_hash,
        "imported_snapshots": len(imported_rows),
        "fixed_instances": len(fixed),
        "v4_eligible_candidates": len(candidates),
        "v4_screened_ineligible": len(ineligible),
        "status": "READY_FOR_SCALE30_CANDIDATE_CENSUS",
    }, ensure_ascii=False, indent=2))
    return 0


def _engine_hash(config: dict) -> str:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join((
        str((ROOT / str(config["native_build_dir"])).resolve()),
        str((ROOT / "src").resolve()),
    ))
    code = (
        "from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import "
        "spprc_engine_build_hash;"
        "print(spprc_engine_build_hash("
        "'native_rcspp_bidirectional_root_partial_hybrid_v3'))"
    )
    return subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, env=environment,
        check=True, text=True, stdout=subprocess.PIPE,
    ).stdout.strip()


if __name__ == "__main__":
    raise SystemExit(main())

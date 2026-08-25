#!/usr/bin/env python3
"""Freeze V7R3 by hash-importing V7R2 switch evidence after analyzer overflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.p0v5_frontier_observability_v7r_common import (  # noqa: E402
    load, sha256, verify_freezes, write_once,
)


DEFAULT_CONFIG = ROOT / "configs/experiments/p0v5_frontier_observability_root_cause_v7r3.json"
DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_frontier_observability_root_cause_v7r3_20260818"
SOURCE_PATHS = (
    "configs/experiments/p0v5_frontier_observability_root_cause_v7r3.json",
    "scripts/p0v5_frontier_observability_v7r_common.py",
    "scripts/initialize_p0v5_frontier_observability_v7r3.py",
    "scripts/analyze_p0v5_frontier_coverage_v7r3.py",
    "scripts/run_p0v5_frontier_feature_sufficiency_v7r.py",
    "scripts/train_p0v5_native_frontier_gat_selector_v7.py",
    "src/lunar_ice_bpc/guidance/frontier_gat_qd1_v7.py",
    "tests/test_p0v5_frontier_observability_v7r3.py",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = load(config_path)
    run_root = args.run_root.resolve()
    source_root = (ROOT / config["source_v7r2_run_root"]).resolve()
    if run_root.exists() and any(run_root.iterdir()):
        raise SystemExit("immutable V7R3 run root is not empty")
    missing = [name for name in SOURCE_PATHS if not (ROOT / name).is_file()]
    if missing:
        raise SystemExit("V7R3 source missing:" + ",".join(missing))

    verify_freezes(source_root)
    terminal = load(source_root / "terminal_decision.json")
    if (terminal.get("decision"), terminal.get("reason")) != (
        "FAIL", "V7R_COVERAGE_ANALYZER_NUMERICAL_OVERFLOW"
    ):
        raise SystemExit("V7R3 source terminal drift")
    oracle = load(source_root / "switch_oracle.decision.json")
    if oracle.get("decision") != "PASS" or oracle.get("correctness_redline_count") != 0:
        raise SystemExit("V7R3 source oracle is not a correctness-clean PASS")
    raw_paths = sorted((source_root / "switch_matrix_raw").glob("*.json"))
    if len(raw_paths) != 228:
        raise SystemExit(f"V7R3 source raw task count drift:{len(raw_paths)}")

    run_root.mkdir(parents=True, exist_ok=True)
    copied_names = (
        "v7_preaction_import.freeze.json",
        "research_contract.freeze.json",
        "coverage_evidence.freeze.json",
        "switch_matrix.collapsed.json",
        "switch_oracle.decision.json",
    )
    for name in copied_names:
        write_once(run_root / name, load(source_root / name))

    source_v7r2 = load(source_root / "source.freeze.json")
    source = {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_observability_source_freeze.v2",
        "git_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip(),
        "worktree_may_be_dirty": True,
        "source_sha256": {name: sha256(ROOT / name) for name in SOURCE_PATHS},
        "native_binary": source_v7r2["native_binary"],
        "native_binary_sha256": source_v7r2["native_binary_sha256"],
        "engine_hashes": source_v7r2["engine_hashes"],
        "selected_exact_config": source_v7r2["selected_exact_config"],
        "selected_exact_config_sha256": source_v7r2["selected_exact_config_sha256"],
        "no_native_or_runtime_change_from_v7r2": True,
    }
    config_freeze = {
        **config,
        "source_config": str(config_path),
        "source_config_sha256": sha256(config_path),
        "frozen_before_coverage_repair_and_feature_diagnostic": True,
        "qpf0_qpd1_outcomes_imported_read_only": True,
    }
    outcome_import = {
        "schema_version": "lunar_ice_bpc.p0v5_v7r2_switch_evidence_import.v1",
        "source_run_root": str(source_root),
        "source_terminal_reason": terminal["reason"],
        "source_remains_read_only": True,
        "scientific_switch_gate": "PASS",
        "correctness_redline_count": 0,
        "raw_matched_task_count": len(raw_paths),
        "collapsed_context_count": len(load(source_root / "switch_matrix.collapsed.json")["rows"]),
        "artifact_sha256": {
            name: sha256(source_root / name) for name in (
                "terminal_decision.json",
                "bootstrap.freeze.registry.json",
                "source.freeze.json",
                "switch_matrix.execution.freeze.json",
                "switch_matrix.rows.json",
                "switch_matrix.collapsed.json",
                "switch_oracle.decision.json",
            )
        },
        "raw_task_sha256": {
            path.name: sha256(path) for path in raw_paths
        },
        "candidate_trained": False,
        "manifest_generated": False,
    }
    artifacts = {
        "config.freeze.json": config_freeze,
        "source.freeze.json": source,
        "v7r2_switch_evidence_import.freeze.json": outcome_import,
        **{name: load(run_root / name) for name in copied_names},
    }
    for name, payload in artifacts.items():
        write_once(run_root / name, payload)
    write_once(run_root / "bootstrap.freeze.registry.json", {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_observability_bootstrap.v2",
        "immutable": True,
        "artifact_sha256": {name: sha256(run_root / name) for name in artifacts},
        "repair_scope": "stable coverage arithmetic only; switch evidence imported read-only",
    })
    state = {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_observability_state.v1",
        "experiment_id": config["experiment_id"],
        "current_stage": "COVERAGE_AUDIT",
        "status": "READY",
        "terminal": False,
        "candidate_trained": False,
        "manifest_generated": False,
        "development_only": True,
        "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    write_once(run_root / "state.initial.json", state)
    write_once(run_root / "state.json", state)
    print(json.dumps({
        "status": "READY_FOR_STABLE_COVERAGE_AUDIT",
        "run_root": str(run_root),
        "raw_matched_tasks_imported": len(raw_paths),
        "switch_oracle": oracle["scales"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

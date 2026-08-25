#!/usr/bin/env python3
"""Freeze the V10 temporal-frontier bootstrap before any late-switch wall."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.p0v5_temporal_frontier_late_switch_v10_common import (  # noqa: E402
    DEFAULT_CONFIG, DEFAULT_RUN_ROOT, load, sha256, stable_hash, write_once,
)


SOURCE_PATHS = (
    "configs/experiments/p0v5_temporal_frontier_late_switch_oracle_v10.json",
    "native/lunar_spprc/include/lunar_spprc/native_pricer.hpp",
    "native/lunar_spprc/src/native_pricer.cpp",
    "native/lunar_spprc/src/pybind_module.cpp",
    "native/lunar_spprc/tests/test_native_pricer.cpp",
    "src/lunar_ice_bpc/exact/bpc/pricing/backends/base.py",
    "src/lunar_ice_bpc/exact/bpc/pricing/backends/native_rcspp.py",
    "src/lunar_ice_bpc/exact/bpc/pricing/backends/native_bidirectional_hybrid.py",
    "scripts/replay_p0v5_qg2_label_state_snapshot.py",
    "scripts/audit_p0v5_counterfactual_native_differential_v8.py",
    "scripts/p0v5_temporal_frontier_late_switch_v10_common.py",
    "scripts/initialize_p0v5_temporal_frontier_late_switch_oracle_v10.py",
    "scripts/audit_p0v5_temporal_frontier_native_differential_v10.py",
    "scripts/freeze_p0v5_temporal_frontier_late_switch_pilot_v10.py",
    "scripts/run_p0v5_temporal_frontier_late_switch_matrix_v10.py",
    "tests/test_p0v5_temporal_frontier_late_switch_v10.py",
    "plan/GAT/P0V5_TEMPORAL_FRONTIER_LATE_SWITCH_V10_20260818_ZH.md",
)


def _native_binary(build: Path) -> Path:
    rows = sorted(build.glob("lunar_spprc_native*.so"))
    if len(rows) != 1:
        raise SystemExit(f"expected one Native module in {build}, found {len(rows)}")
    return rows[0].resolve()


def _engine_hashes(build: Path) -> dict[str, str]:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join((str(build), str(ROOT / "src")))
    code = """
import json
from lunar_ice_bpc.exact.bpc.pricing.backends import (
    NATIVE_INPROCESS_BACKEND_ID,
    NATIVE_BIDIRECTIONAL_ROOT_PARTIAL_HYBRID_BACKEND_ID,
)
from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import spprc_engine_build_hash
print(json.dumps({
  'inprocess': spprc_engine_build_hash(NATIVE_INPROCESS_BACKEND_ID),
  'root_partial_hybrid': spprc_engine_build_hash(
      NATIVE_BIDIRECTIONAL_ROOT_PARTIAL_HYBRID_BACKEND_ID),
}, sort_keys=True))
"""
    completed = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, env=environment, check=True,
        text=True, stdout=subprocess.PIPE,
    )
    return json.loads(completed.stdout)


def _select_rows(rows: list[dict], count: int) -> list[dict]:
    by_scale_instance: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for row in rows:
        by_scale_instance[(int(row["scale"]), row["instance_content_hash"])].append(row)
    selected: list[dict] = []
    for scale in (30, 50):
        primaries = []
        for (row_scale, instance_hash), instance_rows in by_scale_instance.items():
            if row_scale != scale:
                continue
            primary = min(instance_rows, key=lambda row: stable_hash({
                "purpose": "v10-primary-context",
                "scale": scale,
                "instance_hash": instance_hash,
                "context_id": row["context_id"],
                "state_hash": row["state_hash"],
            }))
            primaries.append(primary)
        primaries.sort(key=lambda row: stable_hash({
            "purpose": "v10-pilot-instance",
            "scale": scale,
            "instance_hash": row["instance_content_hash"],
            "context_id": row["context_id"],
            "state_hash": row["state_hash"],
        }))
        if len(primaries) < count:
            raise SystemExit(f"V10 insufficient scale{scale} unique instances")
        selected.extend(primaries[:count])
    return selected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = load(config_path)
    run_root = args.run_root.resolve()
    if run_root.exists() and any(run_root.iterdir()):
        raise SystemExit("immutable V10 run root is not empty")
    missing = [name for name in SOURCE_PATHS if not (ROOT / name).is_file()]
    if missing:
        raise SystemExit("V10 source missing:" + ",".join(missing))

    source_root = (ROOT / config["source_preaction_run_root"]).resolve()
    source_terminal_root = (ROOT / config["source_terminal_run_root"]).resolve()
    source_import = load(source_root / "v7_preaction_import.freeze.json")
    source_rows = list(source_import["rows"])
    if source_import.get("arm_outcomes_imported") != 0 or len(source_rows) != 38:
        raise SystemExit("V10 preaction source count/outcome drift")
    prohibited = {
        "ratio", "winner", "selected_action", "arm_outcome", "wall_seconds",
    }
    if any(prohibited.intersection(row) for row in source_rows):
        raise SystemExit("V10 outcome field leaked into preaction import")
    selected = _select_rows(
        source_rows, int(config["pilot_instances_per_scale"])
    )
    if {str(scale): sum(int(row["scale"]) == scale for row in selected)
            for scale in (30, 50)} != {"30": 8, "50": 8}:
        raise SystemExit("V10 pilot selection count drift")

    terminal = load(source_terminal_root / "terminal_decision.json")
    if (terminal.get("decision"), terminal.get("reason")) != (
        "FAIL", "MULTIRES_FRONTIER_NOT_IDENTIFIABLE"
    ):
        raise SystemExit("V10 source terminal drift")

    reference_build = (ROOT / config["reference_native_build"]).resolve()
    temporal_build = (ROOT / config["temporal_native_build"]).resolve()
    reference_binary = _native_binary(reference_build)
    temporal_binary = _native_binary(temporal_build)
    temporal_engine_hashes = _engine_hashes(temporal_build)
    source_freeze = load(source_root / "source.freeze.json")
    selected_exact_config = Path(source_freeze["selected_exact_config"])
    if sha256(selected_exact_config) != source_freeze["selected_exact_config_sha256"]:
        raise SystemExit("V10 selected exact config drift")

    run_root.mkdir(parents=True, exist_ok=True)
    selected_rows = []
    for raw in selected:
        row = {
            "context_id": raw["context_id"],
            "scale": int(raw["scale"]),
            "instance_content_hash": raw["instance_content_hash"],
            "instance_path": str(Path(raw["instance_path"]).resolve()),
            "instance_path_sha256": sha256(raw["instance_path"]),
            "source_snapshot_path": str(Path(raw["snapshot_path"]).resolve()),
            "source_snapshot_path_sha256": sha256(raw["snapshot_path"]),
            "source_state_hash": raw["state_hash"],
            "target_milestone_kind": raw["target_milestone_kind"],
            "selection_used_arm_outcomes": False,
            "diagnostic_only": True,
        }
        selected_rows.append(row)

    source_artifacts = (
        "bootstrap.freeze.registry.json", "source.freeze.json",
        "v7_preaction_import.freeze.json", "terminal_decision.json",
    )
    preaction = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_temporal_frontier_preaction_import.v1"
        ),
        "source_run_root": str(source_root),
        "source_remains_read_only": True,
        "source_arm_outcomes_imported": 0,
        "old_qpf0_qpd1_outcomes_diagnostic_only": True,
        "selection_rule": config["instance_selection"],
        "selected_counts": {"30": 8, "50": 8},
        "selected_rows": selected_rows,
        "source_artifact_sha256": {
            name: sha256(source_root / name) for name in source_artifacts
        },
    }
    source = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_temporal_frontier_source_freeze.v1"
        ),
        "git_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip(),
        "worktree_may_be_dirty": True,
        "source_sha256": {name: sha256(ROOT / name) for name in SOURCE_PATHS},
        "reference_native_build": str(reference_build),
        "reference_native_binary": str(reference_binary),
        "reference_native_binary_sha256": sha256(reference_binary),
        "temporal_native_build": str(temporal_build),
        "temporal_native_binary": str(temporal_binary),
        "temporal_native_binary_sha256": sha256(temporal_binary),
        "temporal_engine_hashes": temporal_engine_hashes,
        "selected_exact_config": str(selected_exact_config.resolve()),
        "selected_exact_config_sha256": sha256(selected_exact_config),
    }
    config_freeze = {
        **config,
        "source_config": str(config_path),
        "source_config_sha256": sha256(config_path),
        "frozen_before_native_differential_and_late_switch_outcomes": True,
    }
    contract = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_temporal_frontier_research_contract.v1"
        ),
        "question": (
            "does a later in-request QD1 switch create scale50 oracle headroom "
            "without auxiliary prefix requests"
        ),
        "scale30_strategy": "high-activation QD1 at 4096",
        "scale50_strategy": "selective boundary from 4096/8192/16384",
        "qb1_forced_veto": True,
        "qgr1_forced_veto": True,
        "candidate_training_forbidden": True,
        "threshold_search_forbidden": True,
        "fresh_authorization_requires_new_instance_pilot_after_this_diagnostic": True,
    }
    artifacts = {
        "config.freeze.json": config_freeze,
        "source.freeze.json": source,
        "preaction_source.freeze.json": preaction,
        "research_contract.freeze.json": contract,
    }
    for name, payload in artifacts.items():
        write_once(run_root / name, payload)
    write_once(run_root / "bootstrap.freeze.registry.json", {
        "schema_version": (
            "lunar_ice_bpc.p0v5_temporal_frontier_bootstrap_freeze.v1"
        ),
        "immutable": True,
        "frozen_before_native_differential_and_late_switch_outcomes": True,
        "artifact_sha256": {
            name: sha256(run_root / name) for name in artifacts
        },
    })
    state = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_temporal_frontier_state.v1"
        ),
        "experiment_id": config["experiment_id"],
        "current_stage": "NATIVE_DIFFERENTIAL",
        "status": "READY",
        "terminal": False,
        "candidate_trained": False,
        "manifest_generated": False,
        "diagnostic_only": True,
        "development_only": True,
        "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    write_once(run_root / "state.initial.json", state)
    write_once(run_root / "state.json", state)
    print(json.dumps({
        "status": "READY_FOR_NATIVE_DIFFERENTIAL",
        "run_root": str(run_root),
        "selected_counts": preaction["selected_counts"],
        "temporal_engine_hashes": temporal_engine_hashes,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

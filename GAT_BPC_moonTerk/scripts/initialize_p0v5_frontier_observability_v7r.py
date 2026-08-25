#!/usr/bin/env python3
"""Freeze an independent, diagnostic-only V7R observability audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.p0v5_frontier_observability_v7r_common import (  # noqa: E402
    CONFIG, DEFAULT_RUN_ROOT, V7_ROOT, load, sha256, write_once,
)


SOURCE_PATHS = (
    "configs/experiments/p0v5_frontier_observability_root_cause_v7r.json",
    "scripts/p0v5_frontier_observability_v7r_common.py",
    "scripts/initialize_p0v5_frontier_observability_v7r.py",
    "scripts/run_p0v5_frontier_switch_matrix_v7r.py",
    "scripts/analyze_p0v5_frontier_coverage_v7r.py",
    "scripts/run_p0v5_frontier_feature_sufficiency_v7r.py",
    "scripts/replay_p0v5_qg2_label_state_snapshot.py",
    "scripts/train_p0v5_native_frontier_gat_selector_v7.py",
    "src/lunar_ice_bpc/guidance/frontier_gat_qd1_v7.py",
    "tests/test_p0v5_frontier_observability_v7r.py",
    "plan/GAT/P0V5_FRONTIER_OBSERVABILITY_ROOT_CAUSE_V7R_20260818_ZH.md",
)


def _coverage_evidence() -> dict:
    v2_root = ROOT / "runs/p0v5_interaction_gat_queue_selector_v2_20260807"
    v4_root = ROOT / "runs/p0v5_residual_gat_censor_aware_selector_v4_20260815"
    v5_root = ROOT / "runs/p0v5_residual_gat_censor_aware_selector_v5_20260816"
    v2_status_path = v2_root / "candidate_census.status.json"
    v2_index_path = v2_root / "root_screen_snapshot_index.current.json"
    v4_census_path = v4_root / "instance_census.freeze.json"
    v5_instance_path = v5_root / "instance_census.freeze.json"
    v5_status_path = v5_root / "candidate_census.current.json"
    v2_status = load(v2_status_path)
    v2_rows = load(v2_index_path)["rows"]
    v2_generated_success = {
        str(scale): len({row["instance_content_hash"] for row in v2_rows
                         if int(row["scale"]) == scale
                         and row.get("source_cohort") == "generated_v2_candidate"})
        for scale in (30, 50)
    }
    v5_instances = load(v5_instance_path)
    v4_eligible = v5_instances["v4_eligible_candidate_instances"]
    v4_ineligible = v5_instances["v4_screened_ineligible_instances"]
    v5_status = load(v5_status_path)
    v7_candidate_root = V7_ROOT / "census/pilot/scale30"
    v7_candidate_dirs = sorted(v7_candidate_root.glob("candidate_*"))
    v7_eligible = sum(any(path.glob("snapshots/scale30/*/*.json"))
                      for path in v7_candidate_dirs)
    source_paths = [
        v2_status_path, v2_index_path, v4_census_path,
        v5_instance_path, v5_status_path, V7_ROOT / "terminal_decision.json",
    ]
    source_paths.extend(path / "root_run.marker.json" for path in v7_candidate_dirs)
    source_paths.extend(
        snapshot for path in v7_candidate_dirs
        for snapshot in path.glob("snapshots/scale30/*/*.json")
    )
    cohorts = [
        {
            "cohort": "v2_generated_scale30", "scale": 30,
            "successes": v2_generated_success["30"],
            "trials": int(v2_status["generated_instances_by_scale"]["30"]),
            "eligibility": "at_least_one_natural_root_context",
        },
        {
            "cohort": "v2_generated_scale50", "scale": 50,
            "successes": v2_generated_success["50"],
            "trials": int(v2_status["generated_instances_by_scale"]["50"]),
            "eligibility": "at_least_one_natural_root_context",
        },
        {
            "cohort": "v4_candidate_scale30", "scale": 30,
            "successes": sum(int(row["scale"]) == 30 for row in v4_eligible),
            "trials": sum(int(row["scale"]) == 30 for row in v4_eligible + v4_ineligible),
            "eligibility": "at_least_one_natural_root_context",
        },
        {
            "cohort": "v4_candidate_scale50", "scale": 50,
            "successes": sum(int(row["scale"]) == 50 for row in v4_eligible),
            "trials": sum(int(row["scale"]) == 50 for row in v4_eligible + v4_ineligible),
            "eligibility": "at_least_one_natural_root_context",
        },
        {
            "cohort": "v5_repair_scale30", "scale": 30,
            "successes": int(v5_status["eligible_new_candidates"]),
            "trials": int(v5_status["screened_new_candidates"]),
            "eligibility": "at_least_one_natural_root_context",
        },
        {
            "cohort": "v7_pilot_scale30", "scale": 30,
            "successes": v7_eligible,
            "trials": len(v7_candidate_dirs),
            "eligibility": "at_least_one_natural_root_context_under_v7_generator_and_engine",
        },
    ]
    if cohorts[-1]["successes"] != 4 or cohorts[-1]["trials"] != 20:
        raise SystemExit(f"V7R V7 coverage count drift:{cohorts[-1]}")
    return {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_coverage_evidence.v1",
        "outcome_blind": True,
        "arm_outcomes_read": 0,
        "cohorts": cohorts,
        "source_artifact_sha256": {
            str(path.resolve()): sha256(path) for path in source_paths
        },
    }


def _snapshot_hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()).hexdigest()


def _freeze_rebound_snapshots(rows: list[dict], run_root: Path,
                              engine_hash: str) -> list[dict]:
    """Bind old pre-action state to the frozen V7 engine before any arm outcome."""

    output = []
    for raw in rows:
        source_path = Path(raw["snapshot_path"])
        snapshot = load(source_path)
        original_state_hash = str(snapshot["state_hash"])
        rebound = dict(snapshot)
        rebound["engine_hash"] = str(engine_hash)
        rebound.pop("state_hash", None)
        rebound["state_hash"] = _snapshot_hash(rebound)
        target = (
            run_root / "rebound_preaction_snapshots"
            / f"scale{int(raw['scale'])}" / raw["instance_content_hash"]
            / f"{rebound['state_hash']}.json"
        )
        write_once(target, rebound)
        row = dict(raw)
        row.update({
            "original_snapshot_path": str(source_path.resolve()),
            "original_snapshot_sha256": raw["snapshot_sha256"],
            "original_state_hash": original_state_hash,
            "snapshot_path": str(target.resolve()),
            "snapshot_sha256": sha256(target),
            "state_hash": rebound["state_hash"],
            "rebound_engine_hash": str(engine_hash),
            "rebound_frozen_before_arm_outcomes": True,
            "rebound_changes_only_engine_and_state_hash": True,
        })
        output.append(row)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    config = load(args.config.resolve())
    run_root = args.run_root.resolve()
    if run_root.exists() and any(run_root.iterdir()):
        raise SystemExit("immutable V7R run root is not empty")
    missing = [name for name in SOURCE_PATHS if not (ROOT / name).is_file()]
    if missing:
        raise SystemExit("V7R source missing:" + ",".join(missing))

    terminal_path = V7_ROOT / "terminal_decision.json"
    terminal = load(terminal_path)
    if terminal.get("decision") != "FAIL" or terminal.get("reason") != "NO_FRONTIER_SWITCH_HEADROOM":
        raise SystemExit("V7R_V7_TERMINAL_DRIFT")
    milestone_path = V7_ROOT / "diagnostic_q0_milestone.freeze.json"
    corpus_path = V7_ROOT / "probe_diagnostic_contexts.freeze.json"
    milestone = {row["context_id"]: row for row in load(milestone_path)["rows"]}
    rows = []
    for raw in load(corpus_path)["rows"]:
        frozen = milestone[raw["context_id"]]
        if not frozen["replay_eligible"]:
            continue
        row = dict(raw)
        row["target_milestone_kind"] = frozen["milestone_kind"]
        row["partition"] = "diagnostic_root_cause"
        rows.append(row)
    counts = {
        str(scale): {
            "contexts": sum(int(row["scale"]) == scale for row in rows),
            "instances": len({row["instance_content_hash"] for row in rows
                              if int(row["scale"]) == scale}),
        } for scale in (30, 50)
    }
    if counts != {"30": {"contexts": 19, "instances": 15},
                  "50": {"contexts": 19, "instances": 16}}:
        raise SystemExit(f"V7R fixed-context count drift:{counts}")
    prohibited = {"ratio", "winner", "selected_action", "arm_outcome", "wall_seconds"}
    if any(prohibited.intersection(row) for row in rows):
        raise SystemExit("V7R outcome field leaked into preaction import")

    source_v7 = load(V7_ROOT / "source.freeze.json")
    binary = Path(source_v7["native_binary"])
    if not binary.is_file() or sha256(binary) != source_v7["native_binary_sha256"]:
        raise SystemExit("V7R V7 Native binary drift")
    v7_artifacts = (
        "terminal_decision.json", "state.json", "source.freeze.json",
        "interface.freeze.json", "graph.freeze.json",
        "probe_diagnostic_contexts.freeze.json",
        "diagnostic_q0_milestone.freeze.json", "native_differential.report.json",
    )
    run_root.mkdir(parents=True, exist_ok=True)
    rows = _freeze_rebound_snapshots(
        rows, run_root, source_v7["engine_hashes"]["root_partial_hybrid"]
    )
    imported = {
        "schema_version": "lunar_ice_bpc.p0v5_v7_preaction_import.v7r1",
        "source_v7_run_root": str(V7_ROOT.resolve()),
        "source_v7_terminal_reason": terminal["reason"],
        "source_v7_remains_read_only": True,
        "arm_outcomes_imported": 0,
        "existing_qpf0_outcomes_imported": 0,
        "existing_qpd1_outcomes_imported": 0,
        "artifact_sha256": {name: sha256(V7_ROOT / name) for name in v7_artifacts},
        "counts": counts,
        "rows": rows,
    }
    source = {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_observability_source_freeze.v1",
        "git_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip(),
        "worktree_may_be_dirty": True,
        "source_sha256": {name: sha256(ROOT / name) for name in SOURCE_PATHS},
        "native_binary": str(binary.resolve()),
        "native_binary_sha256": sha256(binary),
        "engine_hashes": source_v7["engine_hashes"],
        "selected_exact_config": source_v7["selected_exact_config"],
        "selected_exact_config_sha256": source_v7["selected_exact_config_sha256"],
    }
    config_freeze = {
        **config,
        "source_config": str(args.config.resolve()),
        "source_config_sha256": sha256(args.config.resolve()),
        "frozen_before_qpd1_wall_outcomes": True,
    }
    contract = {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_observability_contract.v1",
        "question": "is exact-safe QD1 benefit predictable from the action-previsible frontier after 4096 literal-Q0 pops",
        "candidate_training_forbidden": True,
        "threshold_search_forbidden": True,
        "manifest_generation_forbidden": True,
        "instance_grouped_evaluation_required": True,
        "advancement_requires": [
            "post4096_switch_oracle_headroom",
            "natural_context_coverage_feasible",
            "frontier_feature_sufficiency",
            "scale50_benefit_harm_separability",
        ],
    }
    coverage = _coverage_evidence()
    artifacts = {
        "config.freeze.json": config_freeze,
        "source.freeze.json": source,
        "v7_preaction_import.freeze.json": imported,
        "research_contract.freeze.json": contract,
        "coverage_evidence.freeze.json": coverage,
    }
    for name, payload in artifacts.items():
        write_once(run_root / name, payload)
    write_once(run_root / "bootstrap.freeze.registry.json", {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_observability_bootstrap.v1",
        "immutable": True,
        "frozen_before_qpd1_wall_outcomes": True,
        "artifact_sha256": {name: sha256(run_root / name) for name in artifacts},
    })
    state = {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_observability_state.v1",
        "experiment_id": config["experiment_id"],
        "current_stage": "SWITCH_MATRIX",
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
    print(json.dumps({"status": "READY_FOR_SWITCH_MATRIX", "counts": counts,
                      "run_root": str(run_root)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

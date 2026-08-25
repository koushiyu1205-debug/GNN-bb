#!/usr/bin/env python3
"""Freeze the outcome-blind Interaction-GAT Queue Selector V3 chain."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from math import floor
from pathlib import Path
from statistics import median
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import (  # noqa: E402
    rotate_blocked_arm_order,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import (  # noqa: E402
    INTERACTION_CONTEXT_FEATURES,
    INTERACTION_EDGE_FEATURES,
    INTERACTION_FEATURE_SCHEMA_V2,
    INTERACTION_GRAPH_SCHEMA_V1,
    INTERACTION_NODE_FEATURES,
    interaction_graph_builder_hash,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v3 import (  # noqa: E402
    INTERACTION_CHECKPOINT_SCHEMA_V2,
    INTERACTION_CORPUS_SCHEMA_V3,
    INTERACTION_DATASET_SCHEMA_V3,
    INTERACTION_MANIFEST_SCHEMA_V2,
    INTERACTION_RUNTIME_POLICY_V3,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_runtime_v3 import (  # noqa: E402
    interaction_gat_runtime_implementation_hash_v3,
)


CONFIG = ROOT / "configs/experiments/p0v5_interaction_gat_queue_selector_v3.json"
SOURCE_PATHS = (
    "src/lunar_ice_bpc/guidance/models.py",
    "src/lunar_ice_bpc/guidance/context_queue_portfolio_freeze.py",
    "src/lunar_ice_bpc/guidance/context_queue_portfolio_gates.py",
    "src/lunar_ice_bpc/guidance/context_queue_portfolio_v1.py",
    "src/lunar_ice_bpc/guidance/interaction_gat_queue_v2.py",
    "src/lunar_ice_bpc/guidance/interaction_gat_queue_runtime_v2.py",
    "src/lunar_ice_bpc/guidance/qgr1_residual_supervision_v2.py",
    "src/lunar_ice_bpc/guidance/proof_queue_label_state_gat_v3.py",
    "src/lunar_ice_bpc/guidance/interaction_gat_queue_v3.py",
    "src/lunar_ice_bpc/guidance/interaction_gat_queue_gates_v3.py",
    "src/lunar_ice_bpc/guidance/interaction_gat_queue_runtime_v3.py",
    "scripts/initialize_p0v5_interaction_gat_queue_selector_v3.py",
    "scripts/run_p0v5_context_queue_portfolio_matrix.py",
    "scripts/replay_p0v5_qg2_label_state_snapshot.py",
    "scripts/build_p0v5_context_queue_portfolio_training_dataset.py",
    "scripts/run_p0v5_context_queue_portfolio_full_bpc.py",
    "scripts/run_lunar_ice_native_spprc_acceptance.py",
    "scripts/run_p0v5_interaction_gat_full_bpc_v2.py",
    "scripts/train_p0v5_qgr1_residual_gat_v2.py",
    "scripts/predict_p0v5_qgr1_residual_potential_v2.py",
    "scripts/run_p0v5_interaction_gat_matrix_v3.py",
    "scripts/finalize_p0v5_interaction_gat_stage_v3.py",
    "scripts/build_p0v5_interaction_gat_training_dataset_v3.py",
    "scripts/train_p0v5_interaction_gat_selector_v3.py",
    "scripts/train_p0v5_qgr1_residual_gat_v3.py",
    "scripts/freeze_p0v5_qgr1_supplement_v3.py",
    "scripts/export_p0v5_qgr1_potentials_v3.py",
    "scripts/merge_p0v5_interaction_gat_outcomes_v3.py",
    "scripts/predict_p0v5_interaction_gat_actions_v3.py",
    "scripts/run_p0v5_interaction_gat_heldout_replays_v3.py",
    "scripts/analyze_p0v5_interaction_gat_heldout_v3.py",
    "scripts/run_lunar_ice_interaction_gat_acceptance_v3.py",
    "scripts/run_p0v5_interaction_gat_full_bpc_v3.py",
    "configs/experiments/p0v5_interaction_gat_queue_selector_v3.json",
    "tests/test_p0v5_interaction_gat_queue_selector_v3.py",
    "plan/GAT/P0V5_INTERACTION_GAT_QUEUE_SELECTOR_V3_IMPLEMENTATION_20260814_ZH.md",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--run-root", type=Path)
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = _load(config_path)
    if config.get("schema_version") != "lunar_ice_bpc.p0v5_interaction_gat_experiment_config.v3":
        raise SystemExit("Interaction-GAT V3 config schema mismatch")
    run_root = (
        args.run_root.resolve() if args.run_root
        else (ROOT / str(config["run_root"])).resolve()
    )
    if run_root.exists() and any(run_root.iterdir()):
        raise SystemExit("V3 run root already contains artifacts; immutable initializer refuses overwrite")
    run_root.mkdir(parents=True, exist_ok=True)

    v2_root = (ROOT / str(config["v2_run_root"])).resolve()
    try:
        verify_portfolio_freezes(v2_root, ROOT)
        v2_terminal_path = v2_root / "terminal_decision.json"
        v2_terminal = _load(v2_terminal_path)
        if (
            v2_terminal.get("decision") != "FAIL"
            or v2_terminal.get("reason") != config["v2_expected_terminal_reason"]
        ):
            raise ValueError("V2 terminal is not expected immutable failure")
        combined = _combine_preaction_rows(v2_root, config)
        corpus, split, folds, primary = _freeze_instance_first_corpus(combined, config)
    except Exception as exc:
        _write_terminal(run_root, "V3_PREACTION_CORPUS_HASH_DRIFT", str(exc))
        raise SystemExit(f"V3 pre-action import failed:{exc}") from exc

    missing = [path for path in SOURCE_PATHS if not (ROOT / path).is_file()]
    if missing:
        raise SystemExit("V3 implementation source missing:" + ",".join(missing))
    v2_source = _load(v2_root / "source.freeze.json")
    if str(v2_source.get("exact_engine_hash")) != str(config["expected_engine_hash"]):
        _write_terminal(run_root, "V3_PREACTION_CORPUS_HASH_DRIFT", "engine hash mismatch")
        raise SystemExit("V3 expected exact engine changed")
    selected_config = Path(str(v2_source["selected_exact_config"])).resolve()
    native_binary = Path(str(v2_source["native_binary"])).resolve()
    for path, expected in (
        (selected_config, v2_source["selected_exact_config_sha256"]),
        (native_binary, v2_source["native_binary_sha256"]),
    ):
        if not path.is_file() or _sha256(path) != str(expected):
            _write_terminal(run_root, "FREEZE_HASH_DRIFT", str(path))
            raise SystemExit(f"V3 exact dependency drift:{path}")

    git_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    milestone_schedule, matrix_schedule = _execution_schedules(corpus, config)
    qgr1_force_schedule = _qgr1_force_schedule(primary, corpus, config)
    config_freeze = {
        **config,
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_config_freeze.v3",
        "source_config": str(config_path),
        "source_config_sha256": _sha256(config_path),
        "status": "FROZEN_BEFORE_ANY_V3_ARM_OUTCOME",
    }
    source_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_source_freeze.v3",
        "status": "FROZEN_BEFORE_ANY_V3_ARM_OUTCOME",
        "git_commit": git_commit,
        "worktree_may_be_dirty": True,
        "source_sha256": {path: _sha256(ROOT / path) for path in SOURCE_PATHS},
        "exact_execution_source_sha256": dict(v2_source["exact_execution_source_sha256"]),
        "selected_exact_config": str(selected_config),
        "selected_exact_config_sha256": _sha256(selected_config),
        "native_binary": str(native_binary),
        "native_binary_sha256": _sha256(native_binary),
        "exact_engine_backend_id": v2_source["exact_engine_backend_id"],
        "exact_engine_hash": v2_source["exact_engine_hash"],
        "native_source_modified_for_v3": False,
        "runtime_policy_id": INTERACTION_RUNTIME_POLICY_V3,
        "runtime_implementation_hash": interaction_gat_runtime_implementation_hash_v3(),
        "graph_builder_hash": interaction_graph_builder_hash(),
        "v2_source_freeze_sha256": _sha256(v2_root / "source.freeze.json"),
    }
    graph_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_graph_freeze.v3",
        "status": "FROZEN_BEFORE_ANY_V3_ARM_OUTCOME",
        "feature_schema": INTERACTION_FEATURE_SCHEMA_V2,
        "graph_schema": INTERACTION_GRAPH_SCHEMA_V1,
        "graph_builder_hash": interaction_graph_builder_hash(),
        "top_k_cooccurrence": 4,
        "top_k_travel": 4,
        "node_feature_names": list(INTERACTION_NODE_FEATURES),
        "edge_feature_names": list(INTERACTION_EDGE_FEATURES),
        "context_feature_names": list(INTERACTION_CONTEXT_FEATURES),
        "forbidden_inputs": [
            "arm_outcome", "selected_action", "winner", "post_action_telemetry"
        ],
    }
    execution_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_execution_freeze.v3",
        "status": "FROZEN_BEFORE_ANY_V3_ARM_OUTCOME",
        "action_universe": config["action_universe"],
        "lifecycle_authority": config["lifecycle_authority"],
        "execution": config["execution"],
        "threshold_grid": config["threshold_grid"],
        "selector_training": config["selector_training"],
        "qgr1_training": config["qgr1_training"],
        "formal_outcomes_may_not_reenter_training": True,
    }
    acceptance_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_acceptance_freeze.v3",
        "status": "FROZEN_BEFORE_ANY_V3_ARM_OUTCOME",
        **{key: config[key] for key in (
            "arm_admission", "base_portfolio_headroom", "qgr1_force_on",
            "gat_calibration_gate", "heldout_gate", "development_e2e_gate",
            "formal_gate", "stop_reasons",
        )},
    }
    interface_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_interface_freeze.v3",
        "feature_schema": INTERACTION_FEATURE_SCHEMA_V2,
        "graph_schema": INTERACTION_GRAPH_SCHEMA_V1,
        "runtime_policy": INTERACTION_RUNTIME_POLICY_V3,
        "manifest_schema": INTERACTION_MANIFEST_SCHEMA_V2,
        "checkpoint_schema": INTERACTION_CHECKPOINT_SCHEMA_V2,
        "dataset_schema": INTERACTION_DATASET_SCHEMA_V3,
        "corpus_schema": INTERACTION_CORPUS_SCHEMA_V3,
        "root_only_authority": True,
    }
    v2_import = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_v2_preaction_import.v3",
        "status": "FROZEN_BEFORE_ANY_V3_ARM_OUTCOME",
        "source_v2_root": str(v2_root),
        "source_r1_import": str(v2_root / "r1_preaction_import.freeze.json"),
        "source_r1_import_sha256": _sha256(v2_root / "r1_preaction_import.freeze.json"),
        "source_root_screen_index": str(v2_root / "root_screen_snapshot_index.current.json"),
        "source_root_screen_index_sha256": _sha256(v2_root / "root_screen_snapshot_index.current.json"),
        "source_v2_terminal": str(v2_terminal_path),
        "source_v2_terminal_sha256": _sha256(v2_terminal_path),
        "deduplication_key": ["instance_content_hash", "state_hash"],
        "arm_outcomes_imported": 0,
        "tree_snapshots_imported": 0,
        "new_candidates_generated": 0,
        "counts_by_scale": combined["counts_by_scale"],
    }
    formal_source = _load(v2_root / "formal_blacklist.freeze.json")
    protected_source = _load(v2_root / "candidate_protected_blacklist.freeze.json")
    formal_freeze = {
        **formal_source,
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_formal_blacklist.v3",
        "source_sha256": _sha256(v2_root / "formal_blacklist.freeze.json"),
        "formal_outcomes_read": 0,
    }
    protected_freeze = {
        **protected_source,
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_protected_blacklist.v3",
        "source_sha256": _sha256(v2_root / "candidate_protected_blacklist.freeze.json"),
        "applies_to_new_candidate_generation_only": True,
        "v3_new_candidate_generation_count": 0,
        "explicit_v2_r1_preaction_import_is_not_new_generation": True,
    }
    artifacts = {
        "config.freeze.json": config_freeze,
        "source.freeze.json": source_freeze,
        "execution.freeze.json": execution_freeze,
        "acceptance.freeze.json": acceptance_freeze,
        "graph.freeze.json": graph_freeze,
        "interface.freeze.json": interface_freeze,
        "v2_preaction_import.freeze.json": v2_import,
        "combined_preaction_index.freeze.json": combined,
        "corpus.freeze.json": corpus,
        "instance_split.freeze.json": split,
        "grouped_cv_folds.freeze.json": folds,
        "qgr1_primary_context.freeze.json": primary,
        "q0_milestone_execution.freeze.json": milestone_schedule,
        "matched_qd1_qb1_execution.freeze.json": matrix_schedule,
        "qgr1_force_on_execution.freeze.json": qgr1_force_schedule,
        "formal_blacklist.freeze.json": formal_freeze,
        "protected_blacklist.freeze.json": protected_freeze,
    }
    for name, payload in artifacts.items():
        _write_once(run_root / name, payload)
    registry = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_freeze_registry.v3",
        "immutable": True,
        "v2_modified": False,
        "arm_outcomes_present_at_freeze": 0,
        "artifact_sha256": {
            name: _sha256(run_root / name) for name in sorted(artifacts)
        },
    }
    _write_once(run_root / "freeze.registry.json", registry)
    state = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_state.v3",
        "experiment_id": config["experiment_id"],
        "current_stage": "Q0_MILESTONE_FREEZE",
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
        "v2_terminal_sha256": _sha256(v2_terminal_path),
        "counts_by_scale": combined["counts_by_scale"],
        "split_context_counts": split["context_counts_by_scale_partition"],
        "milestone_tasks": len(milestone_schedule["tasks"]),
        "matched_tasks": len(matrix_schedule["tasks"]),
        "status": "READY_FOR_Q0_MILESTONE_FREEZE",
    }, ensure_ascii=False, indent=2))
    return 0


def _combine_preaction_rows(v2_root: Path, config):
    sources = (
        ("r1_imported_root_q0", v2_root / "r1_preaction_import.freeze.json"),
        ("v2_root_screen_q0", v2_root / "root_screen_snapshot_index.current.json"),
    )
    formal = set(_load(v2_root / "formal_blacklist.freeze.json")["content_hashes"])
    protected = set(_load(v2_root / "candidate_protected_blacklist.freeze.json")["content_hashes"])
    prohibited = {
        "wall_ratio", "selected_action", "winner", "arm_outcome", "outcome",
        "qd1_wall", "qb1_wall", "qgr1_wall",
    }
    dedup = {}
    source_hashes = {}
    duplicate_count = 0
    legacy_generation_protected = set()
    for cohort, path in sources:
        source_hashes[str(path)] = _sha256(path)
        payload = _load(path)
        if int(payload.get("arm_outcomes_imported") or 0) != 0:
            raise ValueError("pre-action source imported arm outcomes")
        for raw in payload.get("rows") or ():
            if prohibited.intersection(raw):
                raise ValueError("pre-action row contains outcome field")
            row = dict(raw)
            if str(row.get("pricing_lifecycle_scope")) != "root_cg":
                continue
            if int(row.get("scale") or 0) not in {30, 50}:
                raise ValueError("pre-action row scale outside V3")
            if str(row.get("source_engine_hash")) != str(config["expected_engine_hash"]):
                raise ValueError("pre-action row engine hash drift")
            instance_hash = str(row.get("instance_content_hash") or "")
            state_hash = str(row.get("state_hash") or "")
            if not instance_hash or not state_hash:
                raise ValueError("pre-action row binding missing")
            if instance_hash in formal:
                raise ValueError("pre-action instance overlaps formal hash")
            if instance_hash in protected:
                # V2 named this the candidate-generation blacklist: it keeps
                # newly generated instances away from historical development
                # data.  V3 explicitly imports those already-audited V2/r1
                # rows, so this overlap is provenance, not a new-data leak.
                legacy_generation_protected.add(instance_hash)
            snapshot = Path(str(row["snapshot_path"])).resolve()
            if not snapshot.is_file() or _sha256(snapshot) != str(row["snapshot_sha256"]):
                raise ValueError("pre-action snapshot hash drift")
            snap = _load(snapshot)
            bindings = {
                "state_hash": state_hash,
                "instance_content_hash": instance_hash,
                "engine_hash": str(config["expected_engine_hash"]),
                "pricing_lifecycle_scope": "root_cg",
                "config_hash": str(row["source_config_hash"]),
                "exact_action_policy_hash": str(row["source_exact_action_policy_hash"]),
            }
            if any(str(snap.get(key)) != value for key, value in bindings.items()):
                raise ValueError(f"snapshot binding drift:{state_hash}")
            key = (instance_hash, state_hash)
            row["v3_source_cohort"] = (
                str(row.get("source_cohort") or cohort)
                if cohort != "r1_imported_root_q0" else cohort
            )
            if key in dedup:
                previous = dedup[key]
                if str(previous["snapshot_sha256"]) != str(row["snapshot_sha256"]):
                    raise ValueError("deduplicated snapshot payload drift")
                duplicate_count += 1
                continue
            dedup[key] = row
    rows = sorted(dedup.values(), key=lambda row: (
        int(row["scale"]), str(row["instance_content_hash"]),
        int(row.get("round") or 0), str(row["state_hash"]),
    ))
    counts = {}
    expected = config["preaction_corpus"]
    for scale in (30, 50):
        selected = [row for row in rows if int(row["scale"]) == scale]
        multiplicity = Counter(str(row["instance_content_hash"]) for row in selected)
        histogram = Counter(str(value) for value in multiplicity.values())
        counts[str(scale)] = {
            "instances": len(multiplicity),
            "contexts": len(selected),
            "multiplicity_histogram": dict(sorted(histogram.items())),
        }
        if len(multiplicity) != int(expected["expected_instances_per_scale"]):
            raise ValueError(f"scale{scale} instance count drift")
        if len(selected) != int(expected["expected_contexts"][str(scale)]):
            raise ValueError(f"scale{scale} context count drift")
        if dict(sorted(histogram.items())) != dict(sorted(
            expected["expected_context_multiplicity"][str(scale)].items()
        )):
            raise ValueError(f"scale{scale} multiplicity drift")
    return {
        "schema_version": INTERACTION_CORPUS_SCHEMA_V3,
        "status": "FROZEN_BEFORE_ANY_V3_ARM_OUTCOME",
        "deduplication_key": ["instance_content_hash", "state_hash"],
        "source_sha256": source_hashes,
        "duplicate_rows_removed": duplicate_count,
        "arm_outcomes_imported": 0,
        "tree_snapshots_imported": 0,
        "new_candidates_generated": 0,
        "formal_content_hash_overlap": 0,
        "legacy_candidate_generation_protected_overlap_count": len(
            legacy_generation_protected
        ),
        "legacy_candidate_generation_protected_overlap_semantics": (
            "explicit_v2_r1_import_only_not_new_candidate_generation"
        ),
        "expected_engine_hash": config["expected_engine_hash"],
        "counts_by_scale": counts,
        "rows": rows,
    }


def _freeze_instance_first_corpus(combined, config):
    rows = combined["rows"]
    context_strata = _context_strata(rows)
    assignment = {}
    instance_audit = {}
    for scale in (30, 50):
        scale_rows = [row for row in rows if int(row["scale"]) == scale]
        by_instance = defaultdict(list)
        for row in scale_rows:
            by_instance[str(row["instance_content_hash"])].append(row)
        descriptors = _instance_descriptors(by_instance)
        chosen = _balanced_assignment(
            descriptors, config["split"]["multiplicity_quota"][str(scale)],
            seed=int(config["split"]["seed"]), scale=scale,
        )
        assignment.update(chosen)
        instance_audit.update(descriptors)
    context_rows = []
    partition_instances = defaultdict(set)
    for raw in rows:
        row = dict(raw)
        instance_hash = str(row["instance_content_hash"])
        partition = assignment[instance_hash]
        partition_instances[(int(row["scale"]), partition)].add(instance_hash)
        natural_count = int(instance_audit[instance_hash]["context_multiplicity"])
        context_id = hashlib.sha256(
            f"interaction-gat-v3:{row['state_hash']}".encode("utf-8")
        ).hexdigest()[:24]
        row.update({
            "context_id": context_id,
            "partition": partition,
            "context_weight": 1.0 / natural_count,
            "instance_total_weight": 1.0,
            "context_multiplicity": natural_count,
            "round_band": instance_audit[instance_hash]["median_round_band"],
            "pressure_stratum": instance_audit[instance_hash]["previous_q0_pressure"],
            "active_column_density_band": instance_audit[instance_hash]["active_column_density_band"],
            "context_round_band": context_strata[row["state_hash"]]["round_band"],
            "context_pressure_stratum": str(
                row.get("previous_q0_wall_stratum") or "missing"
            ),
            "context_active_column_density_band": context_strata[row["state_hash"]]["density_band"],
            "outcome_fields_present": 0,
        })
        context_rows.append(row)
    expected_counts = config["split"]["expected_replay_contexts"]
    counts = {}
    for scale in (30, 50):
        counts[str(scale)] = {}
        for partition in ("train", "calibration", "selector_heldout", "development_e2e"):
            selected = [
                row for row in context_rows
                if int(row["scale"]) == scale and row["partition"] == partition
            ]
            counts[str(scale)][partition] = len(selected)
            expected_instances = int(config["split"]["instances_per_scale"][partition])
            if len(partition_instances[(scale, partition)]) != expected_instances:
                raise ValueError(f"scale{scale} {partition} instance quota drift")
            if partition != "development_e2e" and len(selected) != int(
                expected_counts[str(scale)][partition]
            ):
                raise ValueError(f"scale{scale} {partition} context count drift")
    corpus = {
        "schema_version": INTERACTION_CORPUS_SCHEMA_V3,
        "status": "FROZEN_BEFORE_ANY_V3_ARM_OUTCOME",
        "all_natural_contexts_used": True,
        "e2e_snapshots_excluded_from_replay_and_training": True,
        "instance_total_weight": 1.0,
        "context_weight_rule": "1/context_multiplicity_within_instance",
        "rows": sorted(context_rows, key=lambda row: (
            int(row["scale"]), row["partition"],
            str(row["instance_content_hash"]), str(row["state_hash"]),
        )),
    }
    split = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_instance_split.v3",
        "status": "FROZEN_BEFORE_ANY_V3_ARM_OUTCOME",
        "seed": int(config["split"]["seed"]),
        "assignment_algorithm": "deterministic_min_cost_categorical_balance_v1",
        "multiplicity_quota": config["split"]["multiplicity_quota"],
        "instance_partition": dict(sorted(assignment.items())),
        "instance_descriptors": instance_audit,
        "rows": [
            {
                "instance_content_hash": instance_hash,
                "scale": int(descriptor["scale"]),
                "partition": assignment[instance_hash],
                "context_multiplicity": int(descriptor["context_multiplicity"]),
                "instance_path": next(
                    row["instance_path"] for row in context_rows
                    if row["instance_content_hash"] == instance_hash
                ),
            }
            for instance_hash, descriptor in sorted(instance_audit.items())
        ],
        "context_counts_by_scale_partition": counts,
    }
    folds = _grouped_folds(split, config)
    primary_rows = []
    for scale in (30, 50):
        cal_by_instance = defaultdict(list)
        for row in corpus["rows"]:
            if int(row["scale"]) == scale and row["partition"] == "calibration":
                cal_by_instance[row["instance_content_hash"]].append(row)
        for instance_hash, values in sorted(cal_by_instance.items()):
            chosen = min(values, key=lambda row: hashlib.sha256(
                f"{config['split']['seed']}:{scale}:{row['context_round_band']}:{row['context_pressure_stratum']}:{row['context_active_column_density_band']}:{row['state_hash']}".encode("utf-8")
            ).hexdigest())
            primary_rows.append({
                "scale": scale, "instance_hash": instance_hash,
                "context_id": chosen["context_id"], "state_hash": chosen["state_hash"],
            })
    primary = {
        "schema_version": "lunar_ice_bpc.p0v5_qgr1_primary_context.v3",
        "status": "FROZEN_BEFORE_QGR1_OUTCOME",
        "selection": "strata_then_state_hash",
        "rows": primary_rows,
    }
    return corpus, split, folds, primary


def _context_strata(rows):
    result = {}
    for scale in (30, 50):
        values = [row for row in rows if int(row["scale"]) == scale]
        round_cuts = _tercile_cuts([int(row.get("round") or 0) for row in values])
        density_cuts = _tercile_cuts([
            int(row.get("active_task_set_count") or 0) for row in values
        ])
        for row in values:
            result[str(row["state_hash"])] = {
                "round_band": _band(int(row.get("round") or 0), round_cuts),
                "density_band": _band(
                    int(row.get("active_task_set_count") or 0), density_cuts
                ),
            }
    return result


def _instance_descriptors(by_instance):
    raw = {}
    round_values = []
    density_values = []
    for instance_hash, rows in by_instance.items():
        med_round = float(median(int(row.get("round") or 0) for row in rows))
        med_density = float(median(
            int(row.get("active_task_set_count") or 0) for row in rows
        ))
        round_values.append(med_round)
        density_values.append(med_density)
        raw[instance_hash] = {
            "scale": int(rows[0]["scale"]),
            "context_multiplicity": len(rows),
            "source_cohort": "+".join(sorted({str(row["v3_source_cohort"]) for row in rows})),
            "median_round": med_round,
            "previous_q0_pressure": "+".join(sorted({
                str(row.get("previous_q0_wall_stratum") or "missing") for row in rows
            })),
            "median_active_column_density": med_density,
        }
    round_cut = _tercile_cuts(round_values)
    density_cut = _tercile_cuts(density_values)
    for row in raw.values():
        row["median_round_band"] = _band(row["median_round"], round_cut)
        row["active_column_density_band"] = _band(
            row["median_active_column_density"], density_cut
        )
    return raw


def _tercile_cuts(values):
    ordered = sorted(float(value) for value in values)
    return ordered[floor((len(ordered) - 1) / 3)], ordered[floor(2 * (len(ordered) - 1) / 3)]


def _band(value, cuts):
    return "low" if value <= cuts[0] else "mid" if value <= cuts[1] else "high"


def _balanced_assignment(descriptors, quota, *, seed, scale):
    features = (
        "source_cohort", "median_round_band", "previous_q0_pressure",
        "active_column_density_band",
    )
    global_counts = {feature: Counter(
        str(row[feature]) for row in descriptors.values()
    ) for feature in features}
    partitions = tuple(quota)
    remaining = {
        partition: {int(mult): int(count) for mult, count in values.items()}
        for partition, values in quota.items()
    }
    assigned_counts = {
        partition: {feature: Counter() for feature in features}
        for partition in partitions
    }
    partition_sizes = {partition: sum(values.values()) for partition, values in remaining.items()}
    instances = sorted(descriptors, key=lambda instance_hash: (
        sum(1 for row in descriptors.values()
            if row["context_multiplicity"] == descriptors[instance_hash]["context_multiplicity"]),
        hashlib.sha256(f"{seed}:{scale}:{instance_hash}".encode()).hexdigest(),
    ))
    result = {}
    total = len(instances)
    for instance_hash in instances:
        row = descriptors[instance_hash]
        multiplicity = int(row["context_multiplicity"])
        candidates = []
        for partition in partitions:
            if remaining[partition].get(multiplicity, 0) <= 0:
                continue
            cost = 0.0
            for feature in features:
                category = str(row[feature])
                observed = assigned_counts[partition][feature][category] + 1
                target = global_counts[feature][category] * partition_sizes[partition] / total
                cost += (observed - target) ** 2 / max(1.0, target)
            tie = hashlib.sha256(
                f"{seed}:{scale}:{partition}:{instance_hash}".encode()
            ).hexdigest()
            candidates.append((cost, tie, partition))
        if not candidates:
            raise ValueError("multiplicity-constrained split assignment exhausted")
        partition = min(candidates)[2]
        result[instance_hash] = partition
        remaining[partition][multiplicity] -= 1
        for feature in features:
            assigned_counts[partition][feature][str(row[feature])] += 1
    if any(count for values in remaining.values() for count in values.values()):
        raise ValueError("multiplicity quota not fully assigned")
    return result


def _grouped_folds(split, config):
    fold_count = int(config["selector_training"]["fold_count"])
    seed = int(config["split"]["seed"])
    rows = []
    for scale in (30, 50):
        train = [
            (instance_hash, split["instance_descriptors"][instance_hash])
            for instance_hash, partition in split["instance_partition"].items()
            if partition == "train"
            and _instance_scale(instance_hash, split) == scale
        ]
        # Interleave multiplicities before round-robin to keep all five folds
        # populated on both scales without splitting an instance.
        train.sort(key=lambda item: (
            int(item[1]["context_multiplicity"]),
            hashlib.sha256(f"{seed}:fold:{scale}:{item[0]}".encode()).hexdigest(),
        ))
        for index, (instance_hash, descriptor) in enumerate(train):
            rows.append({
                "scale": scale, "instance_hash": instance_hash,
                "context_multiplicity": int(descriptor["context_multiplicity"]),
                "fold": index % fold_count,
            })
    for fold in range(fold_count):
        if {row["scale"] for row in rows if row["fold"] == fold} != {30, 50}:
            raise ValueError("grouped CV fold is missing a scale")
    return {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_grouped_cv.v3",
        "status": "FROZEN_BEFORE_ANY_V3_ARM_OUTCOME",
        "fold_count": fold_count,
        "assignment_unit": "instance_content_hash",
        "calibration_or_heldout_instances_in_folds": 0,
        "rows": sorted(rows, key=lambda row: (row["fold"], row["scale"], row["instance_hash"])),
    }


def _instance_scale(instance_hash, split):
    # Scale is implicit in the benchmark ID; retrieve it from descriptor
    # membership populated by _freeze_instance_first_corpus.
    descriptor = split["instance_descriptors"][instance_hash]
    value = descriptor.get("scale")
    if value is None:
        # Content hashes are unique across the two frozen scales.  Store scale
        # during caller-side validation before this helper is reached.
        raise ValueError("instance descriptor is missing scale")
    return int(value)


def _execution_schedules(corpus, config):
    contexts = [
        row for row in corpus["rows"]
        if row["partition"] in {"train", "calibration"}
    ]
    milestone_tasks = []
    matrix_tasks = []
    for context in contexts:
        cap = float(config["execution"]["replay_caps_sec"][str(context["scale"])])
        common = {
            "context_id": context["context_id"],
            "instance_hash": context["instance_content_hash"],
            "scale": int(context["scale"]),
            "partition": context["partition"],
            "state_hash": context["state_hash"],
            "cap_sec": cap,
            "memory_limit_gb": float(config["execution"]["memory_limit_gb"]),
        }
        milestone_tasks.append({**common, "arm": "Q0", "execution_policy": "Q0"})
        for block, order in enumerate(rotate_blocked_arm_order(
            context["state_hash"], arms=("Q0", "QD1", "QB1"), repeats=3
        )):
            for ordinal, arm in enumerate(order):
                matrix_tasks.append({
                    **common, "arm": arm, "execution_policy": arm,
                    "block": block, "ordinal_in_block": ordinal,
                })
    milestone = {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_q0_milestone_execution.v1",
        "status": "FROZEN_BEFORE_ANY_V3_ARM_OUTCOME",
        "mode": "q0_milestone",
        "single_native_process": True,
        "tasks": milestone_tasks,
    }
    matrix = {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_matched_execution.v1",
        "status": "FROZEN_BEFORE_ANY_V3_ARM_OUTCOME",
        "mode": "arm_admission",
        "single_native_process": True,
        "q0_repeated_in_each_block": True,
        "tasks": matrix_tasks,
    }
    return milestone, matrix


def _qgr1_force_schedule(primary, corpus, config):
    by_context = {row["context_id"]: row for row in corpus["rows"]}
    tasks = []
    for chosen in primary["rows"]:
        context = by_context[chosen["context_id"]]
        common = {
            "context_id": context["context_id"],
            "instance_hash": context["instance_content_hash"],
            "scale": int(context["scale"]), "partition": "calibration",
            "state_hash": context["state_hash"],
            "cap_sec": float(config["execution"]["replay_caps_sec"][str(context["scale"])]),
            "memory_limit_gb": float(config["execution"]["memory_limit_gb"]),
        }
        for block, order in enumerate(rotate_blocked_arm_order(
            context["state_hash"], arms=("Q0", "QGR1"), repeats=3
        )):
            for ordinal, arm in enumerate(order):
                tasks.append({
                    **common, "arm": arm, "execution_policy": arm,
                    "block": block, "ordinal_in_block": ordinal,
                })
    return {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_matched_execution.v1",
        "status": "FROZEN_BEFORE_ANY_QGR1_WALL_OUTCOME",
        "mode": "qgr1_force_on", "single_native_process": True,
        "primary_contexts_per_scale": 4, "tasks": tasks,
    }


def _write_terminal(run_root, reason, detail):
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_terminal.v3",
        "decision": "FAIL", "reason": str(reason), "detail": str(detail),
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    path = run_root / "terminal_decision.json"
    if not path.exists():
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_once(path, payload):
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != encoded:
            raise SystemExit(f"immutable V3 artifact already differs:{path}")
        return
    path.write_text(encoded, encoding="utf-8")


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

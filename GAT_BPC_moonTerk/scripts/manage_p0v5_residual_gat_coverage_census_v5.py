#!/usr/bin/env python3
"""Resume the V5 scale30 Q0-only census and freeze the repaired corpus."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)
from scripts.p0v5_residual_gat_coverage_repair_v5_common import (  # noqa: E402
    CONFIG, DEFAULT_RUN_ROOT, assert_active, load, sha256, terminal,
    update_state, validate_candidate_snapshot, validate_instance_file,
    verify_bootstrap, write_mutable_json, write_once,
)


SNAPSHOT_ENV = "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR"
SNAPSHOT_CAP_ENV = "LUNAR_ICE_P0V5_QG2_SNAPSHOT_MAX_PER_INSTANCE"
INSTANCE_PATTERN = re.compile(r"instance_(\d+)_logical_graph\.json$")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("status", "run", "finalize"))
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument(
        "--screen-limit", type=int, default=None,
        help="Maximum additional candidates to generate/screen in this invocation.",
    )
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    config = load(args.config.resolve())
    verify_bootstrap(run_root)
    state = load(run_root / "state.json")
    if args.mode == "status":
        print(json.dumps(_status_payload(run_root), ensure_ascii=False, indent=2))
        return 0
    assert_active(run_root)
    if state.get("current_stage") != "SCALE30_CANDIDATE_CENSUS":
        if args.mode == "finalize" and (run_root / "freeze.registry.json").is_file():
            verify_portfolio_freezes(run_root, ROOT)
            print(json.dumps(_status_payload(run_root), ensure_ascii=False, indent=2))
            return 0
        raise SystemExit("V5 census writer is not authorized in the current stage")

    rows = _load_rows(run_root)
    if args.mode == "run":
        rows = _run_census(run_root, config, rows, args.screen_limit)
    decision = coverage_decision(
        rows,
        maximum=int(config["maximum_new_candidates"]),
        required=int(config["required_new_eligible_candidates"]),
    )
    if decision == "READY":
        _freeze_performance_chain(run_root, config, rows)
    elif decision == "EXHAUSTED":
        terminal(run_root, "INSUFFICIENT_SCALE30_HELDOUT_COVERAGE", {
            "maximum_new_scale30_candidates": int(config["maximum_new_candidates"]),
            "screened_new_scale30_candidates": len(rows),
            "eligible_new_scale30_candidates": len(select_eligible_new_candidates(
                rows, int(config["required_new_eligible_candidates"])
            )),
            "required_new_scale30_eligible": int(
                config["required_new_eligible_candidates"]
            ),
        })
    elif args.mode == "finalize":
        raise SystemExit("V5 coverage is not ready for performance freeze")
    print(json.dumps(_status_payload(run_root), ensure_ascii=False, indent=2))
    return 0


def select_eligible_new_candidates(
    rows: list[dict[str, Any]], required: int = 3
) -> list[dict[str, Any]]:
    """Select by accepted index only; never inspect wall or context structure."""

    eligible = [
        dict(row) for row in rows
        if str(row.get("screen_status")) == "ELIGIBLE"
        and int(row.get("legal_snapshot_count") or 0) >= 1
    ]
    eligible.sort(key=lambda row: int(row["accepted_instance_index"]))
    return eligible[: int(required)]


def coverage_decision(
    rows: list[dict[str, Any]], *, maximum: int = 26, required: int = 3
) -> str:
    if len(select_eligible_new_candidates(rows, required)) >= required:
        return "READY"
    screened = {
        int(row["accepted_instance_index"]) for row in rows
        if str(row.get("screen_status")) in {"ELIGIBLE", "INELIGIBLE"}
    }
    if len(screened) >= maximum and screened == set(range(1, maximum + 1)):
        return "EXHAUSTED"
    return "CONTINUE"


def _run_census(
    run_root: Path, config: dict[str, Any], rows: list[dict[str, Any]],
    screen_limit: int | None,
) -> list[dict[str, Any]]:
    maximum = int(config["maximum_new_candidates"])
    required = int(config["required_new_eligible_candidates"])
    screened_this_call = 0
    while coverage_decision(rows, maximum=maximum, required=required) == "CONTINUE":
        if screen_limit is not None and screened_this_call >= int(screen_limit):
            break
        next_index = _next_unscreened_index(rows, maximum)
        if next_index is None:
            break
        instance_path = _ensure_generated_candidate(run_root, config, next_index)
        forbidden = _forbidden_instance_hashes(run_root, rows)
        task = validate_instance_file(
            instance_path, expected_scale=int(config["candidate_scale"]),
            forbidden_hashes=forbidden,
        )
        task["accepted_instance_index"] = next_index
        task["selection_order"] = next_index
        task["cap_sec"] = int(config["root_collection_cap_sec"])
        task["snapshot_cap"] = int(config["maximum_natural_contexts_per_instance"])
        row = _screen_candidate(run_root, config, task)
        rows.append(row)
        rows.sort(key=lambda value: int(value["accepted_instance_index"]))
        _write_census_status(run_root, config, rows)
        screened_this_call += 1
    return rows


def _ensure_generated_candidate(
    run_root: Path, config: dict[str, Any], accepted_index: int
) -> Path:
    candidate_root = (ROOT / str(config["candidate_instance_root"])).resolve()
    instance_path = (
        candidate_root / "lunar_ice_sp50_030"
        / f"instance_{accepted_index:03d}_logical_graph.json"
    )
    generator_returncode = None
    if not instance_path.is_file():
        generator = dict(config["generator"])
        command = [
            sys.executable, str(ROOT / "scripts/generate_lunar_real_map_benchmark.py"),
            "--output-root", str(candidate_root),
            "--manifest", str(candidate_root / "manifest.json"),
            "--scales", str(int(config["candidate_scale"])),
            "--per-scale", str(accepted_index),
            "--seed-base", str(int(config["candidate_seed_base"])),
            "--max-attempts-per-instance", str(int(generator["max_attempts_per_instance"])),
            "--max-workers", str(int(generator["max_workers"])),
            "--min-free-mem-gb", str(float(generator["min_free_mem_gb"])),
            "--worker-rss-budget-mb", str(int(generator["worker_rss_budget_mb"])),
            "--path-preview", str(generator["path_preview"]),
        ]
        if not bool(generator.get("draw_figures", False)):
            command.append("--no-draw-figures")
        if bool(generator.get("skip_preflight", False)):
            command.append("--skip-preflight")
        if bool(generator.get("skip_bpc_future_check", False)):
            command.append("--skip-bpc-future-check")
        if bool(generator.get("continue_after_timeout", False)):
            command.append("--continue-after-timeout")
        if bool(generator.get("allow_incomplete", False)):
            command.append("--allow-incomplete")
        completed = subprocess.run(command, cwd=ROOT, check=False)
        generator_returncode = completed.returncode
        if completed.returncode != 0 or not instance_path.is_file():
            raise SystemExit(
                f"V5 candidate generator did not produce accepted index {accepted_index}:"
                f"returncode={completed.returncode}"
            )
    marker = run_root / "candidate_generation_markers" / f"candidate_{accepted_index:03d}.json"
    write_once(marker, {
        "schema_version": "lunar_ice_bpc.p0v5_candidate_generation_marker.v5",
        "accepted_instance_index": accepted_index,
        "instance_path": str(instance_path),
        "instance_sha256": sha256(instance_path),
        "generator_returncode": generator_returncode,
        "resumed_after_generation": generator_returncode is None,
        "arm_model_ranker_calls": 0,
    })
    return instance_path


def _screen_candidate(
    run_root: Path, config: dict[str, Any], task: dict[str, Any]
) -> dict[str, Any]:
    index = int(task["accepted_instance_index"])
    output = run_root / "candidate_root_runs" / f"candidate_{index:03d}"
    marker = output / "canonical_result.json"
    snapshot_dir = run_root / "candidate_root_snapshots"
    if not marker.is_file():
        if output.exists() and any(output.iterdir()):
            raise SystemExit(f"partial V5 candidate root run requires audit:{output}")
        config_freeze = load(run_root / "config.freeze.json")
        command = [
            sys.executable,
            str(ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"),
            "--config", str(Path(config_freeze["selected_exact_config"]).resolve()),
            "--scales", "30", "--instance", str(task["instance_path"]),
            "--limit", "1", "--output-dir", str(output), "--no-resume",
            "--route-opportunity-collection-only-root-pool",
            "--route-opportunity-collection-root-pool-time-cap-sec",
            str(int(config["root_collection_cap_sec"])),
        ]
        completed = subprocess.run(
            command, cwd=ROOT,
            env=_root_environment(
                config_freeze, snapshot_dir,
                int(config["maximum_natural_contexts_per_instance"]),
            ),
            check=False,
        )
        if completed.returncode not in {0, 1}:
            raise SystemExit(f"fresh V5 Q0-only root collection failed:index={index}")
        output.mkdir(parents=True, exist_ok=True)
        write_once(marker, {
            "schema_version": "lunar_ice_bpc.p0v5_candidate_root_run_marker.v5",
            "accepted_instance_index": index,
            "instance_content_hash": task["instance_content_hash"],
            "returncode": completed.returncode, "q0_only": True,
            "arm_model_ranker_calls": 0,
        })
    source = load(run_root / "source.freeze.json")
    formal = set(load(run_root / "formal_blacklist.freeze.json")["content_hashes"])
    snapshots = []
    for path in sorted(snapshot_dir.glob("scale*/*/*.json")):
        payload = load(path)
        if str(payload.get("instance_content_hash")) != str(task["instance_content_hash"]):
            continue
        validate_candidate_snapshot(path, task, source, formal)
        snapshots.append((path, payload))
    dedup: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path, payload in snapshots:
        state_hash = str(payload["state_hash"])
        if state_hash in dedup and sha256(path) != sha256(dedup[state_hash][0]):
            raise SystemExit("duplicate V5 candidate state hash has different payload")
        dedup[state_hash] = (path, payload)
    selected = [dedup[key] for key in sorted(dedup)][
        : int(config["maximum_natural_contexts_per_instance"])
    ]
    return {
        **task,
        "screen_status": "ELIGIBLE" if selected else "INELIGIBLE",
        "screened_ineligible": not bool(selected),
        "reason": None if selected else "NO_NATURAL_V5_ROOT_FALLBACK",
        "legal_snapshot_count": len(selected),
        "snapshot_rows": [{
            "snapshot_path": str(path.resolve()), "snapshot_sha256": sha256(path),
            "state_hash": str(payload["state_hash"]),
        } for path, payload in selected],
        "selection_inputs": ["accepted_instance_index", "legal_snapshot_count_ge_1"],
        "arm_outcomes_read": 0, "model_calls": 0, "ranker_calls": 0,
    }


def _freeze_performance_chain(
    run_root: Path, config: dict[str, Any], candidate_rows: list[dict[str, Any]]
) -> None:
    selected_new = select_eligible_new_candidates(
        candidate_rows, int(config["required_new_eligible_candidates"])
    )
    if len(selected_new) != int(config["required_new_eligible_candidates"]):
        raise SystemExit("V5 performance freeze requires three new eligible candidates")
    import_freeze = load(run_root / "v4_preaction_import.freeze.json")
    imported_snapshots = list(import_freeze["snapshot_rows"])
    imported_by_instance: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in imported_snapshots:
        imported_by_instance[str(row["instance_content_hash"])].append(dict(row))

    assignments: list[tuple[str, dict[str, Any], list[dict[str, Any]]]] = []
    fixed = list(import_freeze["fixed_instances"])
    for task in fixed:
        instance_hash = str(task["instance_content_hash"])
        assignments.append((
            str(task["desired_partition"]), dict(task),
            sorted(imported_by_instance[instance_hash], key=lambda row: row["state_hash"]),
        ))
    v4_eligible = list(import_freeze["eligible_candidate_instances"])
    scale30_v4 = [row for row in v4_eligible if int(row["scale"]) == 30]
    scale50_v4 = [row for row in v4_eligible if int(row["scale"]) == 50]
    if len(scale30_v4) != 1 or len(scale50_v4) != 4:
        raise SystemExit("V5 imported heldout census drift")
    for task in (*scale30_v4, *scale50_v4):
        instance_hash = str(task["instance_content_hash"])
        assignments.append((
            "selector_heldout", dict(task),
            sorted(imported_by_instance[instance_hash], key=lambda row: row["state_hash"]),
        ))
    for task in selected_new:
        assignments.append((
            "selector_heldout", dict(task), list(task["snapshot_rows"])
        ))
    corpus_rows = _build_corpus_rows(assignments)
    corpus = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_corpus_freeze.v4",
        "status": "FROZEN_BEFORE_ANY_V5_ARM_OUTCOME",
        "fresh_engine_only": True,
        "v4_q0_preaction_import_authorized": True,
        "all_natural_contexts_up_to_cap_used": True,
        "instance_total_weight": 1.0,
        "context_weight_rule": "inverse_legal_context_count_within_instance",
        "rows": sorted(corpus_rows, key=lambda row: (
            row["scale"], row["partition"], row["instance_content_hash"], row["state_hash"]
        )),
    }
    split = _split_payload(corpus)
    required_counts = {
        str(scale): dict(config["final_partition_instances_per_scale"])
        for scale in (30, 50)
    }
    if split["counts"] != required_counts:
        raise SystemExit(f"V5 final split count mismatch:{split['counts']}")
    folds = _folds(corpus)
    source = load(run_root / "source.freeze.json")
    index = {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_root_snapshot_index.v4",
        "expected_engine_hash": source["exact_engine_hash"],
        "root_only": True, "outcome_fields_included": False,
        "coverage_repair_chain_version": "v5", "rows": corpus["rows"],
    }
    replay_rows = [
        row for row in corpus["rows"]
        if row["partition"] in {"train", "calibration"}
    ]
    runtime_config = load(run_root / "config.freeze.json")
    milestone = {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_q0_milestone_execution.v4",
        "status": "FROZEN_BEFORE_ANY_V5_ARM_OUTCOME", "q0_only": True,
        "single_native_process": True,
        "tasks": [{
            "context_id": row["context_id"],
            "instance_hash": row["instance_content_hash"],
            "scale": row["scale"], "partition": row["partition"],
            "state_hash": row["state_hash"], "arm": "Q0", "execution_policy": "Q0",
            "cap_sec": runtime_config["execution"]["replay_caps_sec"][str(row["scale"])],
            "memory_limit_gb": runtime_config["execution"]["memory_limit_gb"],
        } for row in replay_rows],
    }
    primary = {
        "schema_version": "lunar_ice_bpc.p0v5_qgr1_primary_context.v4",
        "status": "FROZEN_BEFORE_ANY_QGR1_WALL_OUTCOME",
        "rows": [
            sorted(rows, key=lambda row: row["state_hash"])[0]
            for (_scale, _instance), rows in sorted(_group([
                row for row in corpus["rows"] if row["partition"] == "calibration"
            ]).items())
        ],
    }
    selected_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_coverage_repair_candidate_selection.v5",
        "status": "FROZEN_BEFORE_ANY_V5_ARM_OUTCOME",
        "selection_rule": "first_three_eligible_in_accepted_instance_index_order",
        "v4_scale30_eligible": scale30_v4,
        "selected_new_scale30": selected_new,
        "v4_scale50_eligible": scale50_v4,
        "screened_new_candidates": candidate_rows,
        "arm_outcomes_read": 0,
    }
    artifacts = {
        "candidate_selection.freeze.json": selected_freeze,
        "root_snapshot_index.freeze.json": index,
        "corpus.freeze.json": corpus,
        "instance_split.freeze.json": split,
        "grouped_cv_folds.freeze.json": folds,
        "qgr1_primary_context.freeze.json": primary,
        "q0_milestone_execution.freeze.json": milestone,
        "execution.freeze.json": {
            "schema_version": "lunar_ice_bpc.p0v5_residual_gat_execution_freeze.v4",
            "status": "FROZEN_BEFORE_ANY_V5_ARM_OUTCOME",
            "execution": runtime_config["execution"],
            "trace_reservoir": runtime_config["trace_reservoir"],
            "threshold_grid": runtime_config["threshold_grid"],
            "action_universe": runtime_config["action_universe"],
        },
        "acceptance.freeze.json": {
            "schema_version": "lunar_ice_bpc.p0v5_residual_gat_acceptance_freeze.v4",
            "status": "FROZEN_BEFORE_ANY_V5_ARM_OUTCOME",
            **{key: runtime_config[key] for key in (
                "qd1_admission", "qgr1_training", "qgr1_force_on",
                "portfolio_headroom", "calibration_gate", "heldout_gate",
                "development_e2e_gate", "formal_gate", "stop_reasons",
            )},
        },
    }
    for name, payload in artifacts.items():
        write_once(run_root / name, payload)
    prearm = load(run_root / "prearm.freeze.registry.json")
    registry_names = {
        **dict(prearm["artifact_sha256"]),
        **{name: sha256(run_root / name) for name in artifacts},
    }
    for task in selected_new:
        for snapshot in task["snapshot_rows"]:
            path = Path(snapshot["snapshot_path"]).resolve()
            registry_names[str(path.relative_to(run_root))] = sha256(path)
    write_once(run_root / "freeze.registry.json", {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_freeze_registry.v4",
        "immutable": True, "arm_outcomes_present_at_freeze": 0,
        "coverage_repair_chain_version": "v5",
        "artifact_sha256": registry_names,
    })
    verify_portfolio_freezes(run_root, ROOT)
    update_state(run_root, "Q0_MILESTONE_AND_TRACE", "READY")


def _build_corpus_rows(
    assignments: list[tuple[str, dict[str, Any], list[dict[str, Any]]]]
) -> list[dict[str, Any]]:
    rows = []
    seen_instances: set[str] = set()
    for partition, task, snapshots in assignments:
        instance_hash = str(task["instance_content_hash"])
        if instance_hash in seen_instances:
            raise SystemExit("INSTANCE_FEATURE_FOLD_OR_OUTCOME_LEAKAGE:partition_overlap")
        seen_instances.add(instance_hash)
        if not snapshots:
            raise SystemExit("V5 final assignment contains zero-context instance")
        snapshots = sorted(snapshots, key=lambda row: str(row["state_hash"]))[:3]
        for index, raw in enumerate(snapshots):
            path = Path(str(raw["snapshot_path"])).resolve()
            payload = load(path)
            trajectory = dict(payload.get("trajectory_features") or {})
            if str(trajectory.get("previous_queue_policy_id") or "Q0") != "Q0":
                for field in (
                    "previous_proof_pass_wall_time", "previous_proof_processed_labels",
                    "previous_dominance_candidate_checks", "previous_dominance_wall_time",
                    "previous_max_visited_bucket_size",
                ):
                    if trajectory.get(field) is not None:
                        raise SystemExit("non-Q0 previous trajectory leaked into V5 corpus")
            active_sets = payload.get("active_task_sets") or ()
            rows.append({
                "context_id": f"v5_s{int(task['scale'])}_{instance_hash}_{index}",
                "scale": int(task["scale"]), "partition": partition,
                "instance_content_hash": instance_hash,
                "instance_id": str(task["instance_id"]),
                "instance_path": str(Path(task["instance_path"]).resolve()),
                "source_cohort": str(task["source_cohort"]),
                "snapshot_path": str(path), "snapshot_sha256": sha256(path),
                "state_hash": str(payload["state_hash"]),
                "source_state_hash": str(payload["state_hash"]),
                "source_engine_hash": str(payload["engine_hash"]),
                "source_config_hash": str(payload["config_hash"]),
                "source_exact_action_policy_hash": str(payload["exact_action_policy_hash"]),
                "pricing_lifecycle_scope": "root_cg",
                "round": int(payload.get("round") or 0),
                "active_task_set_count": len(active_sets),
                "active_column_signature_count": len(
                    payload.get("active_column_signature_hashes") or ()
                ),
                "context_weight": 1.0 / len(snapshots),
                "instance_total_weight": 1.0, "outcome_fields_present": [],
            })
    return rows


def _split_payload(corpus: dict[str, Any]) -> dict[str, Any]:
    mapping = {}
    for row in corpus["rows"]:
        old = mapping.setdefault(row["instance_content_hash"], row["partition"])
        if old != row["partition"]:
            raise SystemExit("INSTANCE_FEATURE_FOLD_OR_OUTCOME_LEAKAGE:split")
    return {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_instance_split.v4",
        "status": "FROZEN_BEFORE_ANY_V5_ARM_OUTCOME",
        "instance_partition": mapping,
        "counts": {
            str(scale): {
                partition: len({
                    row["instance_content_hash"] for row in corpus["rows"]
                    if row["scale"] == scale and row["partition"] == partition
                })
                for partition in (
                    "train", "calibration", "selector_heldout", "development_e2e"
                )
            } for scale in (30, 50)
        },
    }


def _folds(corpus: dict[str, Any]) -> dict[str, Any]:
    by_scale: dict[int, list[str]] = defaultdict(list)
    for scale, instance_hash in sorted({
        (row["scale"], row["instance_content_hash"])
        for row in corpus["rows"] if row["partition"] == "train"
    }):
        by_scale[int(scale)].append(str(instance_hash))
    rows = []
    for scale in (30, 50):
        ordered = sorted(by_scale[scale], key=lambda value: hashlib.sha256(
            f"v5-fold:{scale}:{value}".encode()
        ).hexdigest())
        rows.extend({
            "scale": scale, "instance_hash": value, "fold": index % 5,
        } for index, value in enumerate(ordered))
    return {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_grouped_cv.v4",
        "status": "FROZEN_BEFORE_ANY_V5_ARM_OUTCOME", "fold_count": 5,
        "instance_grouped": True, "rows": rows,
    }


def _group(rows: list[dict[str, Any]]) -> dict[tuple[Any, ...], list[dict[str, Any]]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["scale"], row["instance_content_hash"])].append(row)
    return grouped


def _next_unscreened_index(rows: list[dict[str, Any]], maximum: int) -> int | None:
    used = {int(row["accepted_instance_index"]) for row in rows}
    return next((index for index in range(1, maximum + 1) if index not in used), None)


def _load_rows(run_root: Path) -> list[dict[str, Any]]:
    return list(load(run_root / "candidate_census.current.json").get("rows") or [])


def _write_census_status(
    run_root: Path, config: dict[str, Any], rows: list[dict[str, Any]]
) -> None:
    selected = select_eligible_new_candidates(
        rows, int(config["required_new_eligible_candidates"])
    )
    write_mutable_json(run_root / "candidate_census.current.json", {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_candidate_census_status.v5",
        "status": coverage_decision(
            rows, maximum=int(config["maximum_new_candidates"]),
            required=int(config["required_new_eligible_candidates"]),
        ),
        "screened_new_candidates": len(rows),
        "eligible_new_candidates": sum(
            str(row.get("screen_status")) == "ELIGIBLE" for row in rows
        ),
        "selected_eligible_indices": [row["accepted_instance_index"] for row in selected],
        "required_eligible_new_candidates": int(config["required_new_eligible_candidates"]),
        "maximum_new_candidates": int(config["maximum_new_candidates"]),
        "rows": rows, "arm_outcomes_read": 0,
    })


def _forbidden_instance_hashes(
    run_root: Path, rows: list[dict[str, Any]]
) -> set[str]:
    forbidden = set(load(run_root / "formal_blacklist.freeze.json")["content_hashes"])
    imported = load(run_root / "v4_preaction_import.freeze.json")
    forbidden.update(
        str(row["instance_content_hash"])
        for category in (
            "fixed_instances", "eligible_candidate_instances", "screened_ineligible_instances"
        ) for row in imported[category]
    )
    forbidden.update(str(row["instance_content_hash"]) for row in rows)
    return forbidden


def _root_environment(
    config: dict[str, Any], snapshot_dir: Path, snapshot_cap: int
) -> dict[str, str]:
    environment = dict(os.environ)
    for key in tuple(environment):
        if (
            key.startswith("LUNAR_ICE_P0V5_")
            or key.startswith("LUNAR_ICE_PROOF_TAIL_GAT")
            or key.startswith("LUNAR_ICE_GAT_")
        ):
            environment.pop(key, None)
    environment[SNAPSHOT_ENV] = str(snapshot_dir)
    environment[SNAPSHOT_CAP_ENV] = str(snapshot_cap)
    environment["PYTHONPATH"] = os.pathsep.join((
        str((ROOT / str(config["native_build_dir"])).resolve()),
        str((ROOT / "src").resolve()),
    ))
    return environment


def _status_payload(run_root: Path) -> dict[str, Any]:
    state = load(run_root / "state.json")
    census = load(run_root / "candidate_census.current.json")
    return {
        "run_root": str(run_root), "current_stage": state["current_stage"],
        "status": state["status"], "terminal": bool(state["terminal"]),
        "terminal_decision": state.get("terminal_decision"),
        "screened_new_scale30_candidates": census["screened_new_candidates"],
        "eligible_new_scale30_candidates": census["eligible_new_candidates"],
        "selected_eligible_indices": census.get("selected_eligible_indices", []),
        "performance_freeze_present": (run_root / "freeze.registry.json").is_file(),
    }


if __name__ == "__main__":
    raise SystemExit(main())

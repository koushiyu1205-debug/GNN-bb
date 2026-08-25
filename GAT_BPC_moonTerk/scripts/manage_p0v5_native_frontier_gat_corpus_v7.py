#!/usr/bin/env python3
"""Outcome-blind fresh instance census and corpus freeze for V7."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from scripts.p0v5_native_frontier_gat_qd1_v7_common import (  # noqa: E402
    DEFAULT_RUN_ROOT,
    assert_active,
    deterministic_seed,
    load,
    sha256,
    stable_hash,
    update_state,
    write_once,
    write_terminal,
)


SNAPSHOT_ENV = "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR"
SNAPSHOT_CAP_ENV = "LUNAR_ICE_P0V5_QG2_SNAPSHOT_MAX_PER_INSTANCE"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cohort", choices=("pilot", "main"))
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--screen-limit", type=int)
    parser.add_argument("--status-only", action="store_true")
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    expected_stage = "PILOT_CENSUS" if args.cohort == "pilot" else "MAIN_CENSUS"
    assert_active(run_root, expected_stage)
    config = load(run_root / "config.freeze.json")
    required = 8 if args.cohort == "pilot" else 37
    maximum = (
        int(config["candidate_generation"]["pilot_maximum_generated_per_scale"])
        if args.cohort == "pilot"
        else int(config["candidate_generation"]["main_maximum_generated_per_scale"])
    )
    rows = _load_screen_rows(run_root, args.cohort)
    if not args.status_only:
        screened = 0
        for scale in (30, 50):
            while len(_eligible(rows, scale)) < required:
                if args.screen_limit is not None and screened >= args.screen_limit:
                    break
                index = _next_index(rows, scale, maximum)
                if index is None:
                    break
                current = _screen_one(run_root, config, args.cohort, scale, index)
                rows.append(current)
                rows.sort(key=lambda row: (int(row["scale"]), int(row["candidate_index"])))
                write_once(
                    run_root / "census" / args.cohort
                    / f"screen_scale{scale}_{index:03d}.json",
                    current,
                )
                screened += 1
            if args.screen_limit is not None and screened >= args.screen_limit:
                break
    selected = {scale: _eligible(rows, scale)[:required] for scale in (30, 50)}
    exhausted = {
        scale: len(_eligible(rows, scale)) < required
        and len([row for row in rows if int(row["scale"]) == scale]) >= maximum
        for scale in (30, 50)
    }
    if any(exhausted.values()):
        write_terminal(
            run_root,
            reason=("NO_FRONTIER_SWITCH_HEADROOM" if args.cohort == "pilot"
                    else "INSUFFICIENT_FRONTIER_GAT_TRAINING_SUPPORT"),
            stage=expected_stage,
            detail={"coverage_exhausted": exhausted, "required": required,
                    "maximum": maximum},
        )
    elif all(len(selected[scale]) == required for scale in (30, 50)):
        _freeze_corpus(run_root, config, args.cohort, selected)
    status = {
        "cohort": args.cohort,
        "required_eligible_per_scale": required,
        "maximum_candidates_per_scale": maximum,
        "screened": {str(scale): len([row for row in rows if int(row["scale"]) == scale])
                     for scale in (30, 50)},
        "eligible": {str(scale): len(_eligible(rows, scale)) for scale in (30, 50)},
        "selection_inputs": ["candidate_index", "legal_snapshot_count_ge_1"],
        "arm_outcomes_read": 0,
    }
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0


def _load_screen_rows(run_root: Path, cohort: str) -> list[dict[str, Any]]:
    directory = run_root / "census" / cohort
    if not directory.is_dir():
        return []
    return [load(path) for path in sorted(directory.glob("screen_scale*_*.json"))]


def _eligible(rows: list[dict[str, Any]], scale: int) -> list[dict[str, Any]]:
    return sorted(
        (row for row in rows if int(row["scale"]) == scale
         and row["screen_status"] == "ELIGIBLE"),
        key=lambda row: int(row["candidate_index"]),
    )


def _next_index(rows: list[dict[str, Any]], scale: int, maximum: int) -> int | None:
    used = {int(row["candidate_index"]) for row in rows if int(row["scale"]) == scale}
    return next((index for index in range(1, maximum + 1) if index not in used), None)


def _screen_one(
    run_root: Path, config: dict[str, Any], cohort: str, scale: int, index: int
) -> dict[str, Any]:
    instance = _ensure_instance(config, cohort, scale, index)
    data = load_lunar_ice_data(json.loads(instance.read_text(encoding="utf-8")))
    forbidden = set(load(run_root / "blacklist.freeze.json")["content_hashes"])
    if data.instance_content_hash in forbidden:
        raise SystemExit("V7 candidate overlaps historical/formal/protected corpus")
    base = run_root / "census" / cohort / f"scale{scale}" / f"candidate_{index:03d}"
    snapshots = base / "snapshots"
    marker = base / "root_run.marker.json"
    if not marker.is_file():
        output = base / "root_run"
        command = [
            sys.executable, str(ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"),
            "--config", str(Path(config["selected_exact_config"]).resolve()),
            "--scales", str(scale), "--instance", str(instance), "--limit", "1",
            "--output-dir", str(output), "--no-resume",
            "--route-opportunity-collection-only-root-pool",
            "--route-opportunity-collection-root-pool-time-cap-sec",
            str(config["execution"]["replay_caps_sec"][str(scale)]),
        ]
        completed = subprocess.run(
            command, cwd=ROOT, env=_native_environment(config, snapshots), check=False
        )
        if completed.returncode not in {0, 1}:
            raise SystemExit(f"V7 Q0 root collection failed:scale{scale}:candidate{index}")
        write_once(marker, {
            "schema_version": "lunar_ice_bpc.p0v5_v7_root_screen_marker.v1",
            "returncode": completed.returncode, "q0_only": True,
            "probe_calls": 0, "model_calls": 0, "arm_outcomes": 0,
        })
    source = load(run_root / "source.freeze.json")
    expected_engine = str(source["engine_hashes"]["root_partial_hybrid"])
    found: dict[str, dict[str, Any]] = {}
    for path in sorted(snapshots.glob("scale*/*/*.json")):
        payload = load(path)
        if str(payload.get("instance_content_hash")) != data.instance_content_hash:
            continue
        if str(payload.get("pricing_lifecycle_scope")) != "root_cg":
            raise SystemExit("V7 tree snapshot entered root-only census")
        if str(payload.get("engine_hash")) != expected_engine:
            raise SystemExit("V7 fresh snapshot engine binding drift")
        if bool(payload.get("labels_dropped")):
            raise SystemExit("V7 fresh snapshot reported label drop")
        forbidden_fields = {"winner", "wall_ratio", "selected_action", "arm_outcome"}
        if forbidden_fields.intersection(payload):
            raise SystemExit("V7 census observed outcome field")
        found[str(payload["state_hash"])] = {
            "snapshot_path": str(path.resolve()),
            "snapshot_sha256": sha256(path),
            "state_hash": str(payload["state_hash"]),
            "source_engine_hash": str(payload["engine_hash"]),
            "source_config_hash": str(payload["config_hash"]),
            "source_exact_action_policy_hash": str(payload["exact_action_policy_hash"]),
        }
    selected = [found[key] for key in sorted(found)[:3]]
    return {
        "schema_version": "lunar_ice_bpc.p0v5_v7_candidate_screen.v1",
        "cohort": cohort, "scale": scale, "candidate_index": index,
        "generation_seed": deterministic_seed(cohort, scale, index),
        "instance_id": data.instance_id,
        "instance_content_hash": data.instance_content_hash,
        "instance_path": str(instance.resolve()), "instance_sha256": sha256(instance),
        "screen_status": "ELIGIBLE" if selected else "INELIGIBLE",
        "reason": None if selected else "NO_NATURAL_V5_ROOT_FALLBACK",
        "legal_snapshot_count": len(selected), "snapshots": selected,
        "selection_inputs": ["candidate_index", "legal_snapshot_count_ge_1"],
        "root_wall_not_used": True, "arm_outcomes_read": 0,
    }


def _ensure_instance(
    config: dict[str, Any], cohort: str, scale: int, index: int
) -> Path:
    root = ROOT / str(config["candidate_generation"][f"{cohort}_instance_root"])
    candidate_root = root / f"scale{scale}" / f"candidate_{index:03d}"
    instance = candidate_root / f"lunar_ice_sp50_{scale:03d}" / "instance_001_logical_graph.json"
    if instance.is_file():
        return instance
    generator = config["candidate_generation"]["generator"]
    command = [
        sys.executable, str(ROOT / "scripts/generate_lunar_real_map_benchmark.py"),
        "--output-root", str(candidate_root),
        "--manifest", str(candidate_root / "manifest.json"),
        "--scales", str(scale), "--per-scale", "1",
        "--seed-base", str(deterministic_seed(cohort, scale, index)),
        "--max-attempts-per-instance", str(generator["max_attempts_per_instance"]),
        "--max-workers", "1", "--min-free-mem-gb", str(generator["min_free_mem_gb"]),
        "--worker-rss-budget-mb", str(generator["worker_rss_budget_mb"]),
        "--path-preview", str(generator["path_preview"]), "--no-draw-figures",
        "--skip-preflight", "--skip-bpc-future-check", "--continue-after-timeout",
    ]
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode or not instance.is_file():
        raise SystemExit(f"V7 generator failed:scale{scale}:candidate{index}")
    return instance


def _native_environment(config: dict[str, Any], snapshots: Path) -> dict[str, str]:
    environment = dict(os.environ)
    for key in tuple(environment):
        if key.startswith("LUNAR_ICE_P0V5_") or key.startswith("LUNAR_ICE_GAT_"):
            environment.pop(key, None)
    environment[SNAPSHOT_ENV] = str(snapshots)
    environment[SNAPSHOT_CAP_ENV] = "3"
    environment["PYTHONPATH"] = os.pathsep.join((
        str((ROOT / config["native_build_dir"]).resolve()), str((ROOT / "src").resolve())
    ))
    return environment


def _freeze_corpus(
    run_root: Path, config: dict[str, Any], cohort: str,
    selected: dict[int, list[dict[str, Any]]],
) -> None:
    rows: list[dict[str, Any]] = []
    if cohort == "pilot":
        partitions = [("pilot", 8)]
    else:
        partitions = [("train", 20), ("calibration", 8),
                      ("selector_heldout", 6), ("development_e2e", 3)]
    for scale in (30, 50):
        cursor = 0
        for partition, count in partitions:
            for instance in selected[scale][cursor:cursor + count]:
                snapshots = list(instance["snapshots"])
                cap = 2 if partition == "train" else 1
                chosen = snapshots[:cap]
                for position, snapshot in enumerate(chosen):
                    rows.append({
                        "context_id": f"v7_{cohort}_s{scale}_i{int(instance['candidate_index']):03d}_c{position}",
                        "cohort": cohort, "scale": scale, "partition": partition,
                        "candidate_index": int(instance["candidate_index"]),
                        "instance_id": instance["instance_id"],
                        "instance_content_hash": instance["instance_content_hash"],
                        "instance_path": instance["instance_path"],
                        "instance_sha256": instance["instance_sha256"],
                        **snapshot,
                        "context_weight": 1.0 / len(chosen),
                        "instance_total_weight": 1.0,
                        "outcome_fields_present": [],
                    })
            cursor += count
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_gat_corpus_freeze.v7",
        "cohort": cohort, "fresh_v7_engine_only": True,
        "selection_outcome_blind": True, "arm_outcomes_present_at_freeze": 0,
        "instance_total_weight": 1.0,
        "rows": rows,
    }
    name = f"{cohort}_corpus.freeze.json"
    write_once(run_root / name, payload)
    write_once(run_root / f"{cohort}_census.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_v7_candidate_census_freeze.v1",
        "cohort": cohort,
        "selected": {str(scale): selected[scale] for scale in (30, 50)},
        "corpus_sha256": stable_hash(payload),
    })
    if cohort == "pilot":
        update_state(run_root, "PILOT_MATRIX", "READY")
    else:
        write_once(run_root / "performance.freeze.registry.json", {
            "schema_version": "lunar_ice_bpc.p0v5_v7_performance_registry.v1",
            "frozen_before_main_arm_outcomes": True,
            "main_corpus_sha256": sha256(run_root / name),
            "config_sha256": sha256(run_root / "config.freeze.json"),
            "source_sha256": sha256(run_root / "source.freeze.json"),
        })
        update_state(run_root, "MAIN_MATRIX", "READY")


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run the fixed E64/E128/E256 P0V4 negative-escape oracle.

The harness is intentionally serial for scale 50.  It creates independent arm
configs and run directories, verifies the immutable P0V4 control before every
stage, and never changes production defaults or a frozen baseline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from math import exp, log
import os
from pathlib import Path
import signal
import subprocess
import sys
from time import monotonic, sleep
from typing import Iterable, Mapping

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = (
    ROOT
    / "configs/experiments/p0v4_diverse_negative_escape_oracle_v1.yaml"
)
ACCEPTANCE_RUNNER = (
    ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"
)
REPLAY_RUNNER = (
    ROOT / "scripts/replay_p0v2_gat_proof_tail_snapshot.py"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument(
        "--output-dir",
        default="runs/p0v4_diverse_negative_escape_oracle_v2",
    )
    parser.add_argument(
        "--stage",
        choices=(
            "prepare",
            "collect-snapshots",
            "snapshot",
            "development",
            "summarize",
            "select",
        ),
        default="prepare",
    )
    parser.add_argument("--arm", choices=("E64", "E128", "E256"))
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reuse a completed per-instance development run.",
    )
    args = parser.parse_args()
    config_path = _resolve(args.config)
    config = _load_yaml(config_path)
    _validate_experiment(config, config_path)
    output = _resolve(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    arm_configs = _materialize_arm_configs(config, output)
    _verify_control(config)

    if args.stage == "prepare":
        payload = {
            "schema_version": (
                "lunar_ice_bpc.p0v4_diverse_escape_prepare.v1"
            ),
            "status": "PREPARED",
            "experiment_config": str(config_path),
            "experiment_config_sha256": _sha256(config_path),
            "arm_configs": {
                arm: {
                    "path": str(path),
                    "sha256": _sha256(path),
                }
                for arm, path in arm_configs.items()
            },
            "frozen_control_verified": True,
            "production_default_changed": False,
        }
        _write_json(output / "prepare_manifest.json", payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    if args.stage == "collect-snapshots":
        return _collect_snapshot_stage(
            config,
            output,
            dry_run=bool(args.dry_run),
            resume=bool(args.resume),
        )
    if args.stage == "snapshot":
        return _run_snapshot_stage(
            config,
            output,
            arms=_selected_arms(args.arm),
            dry_run=bool(args.dry_run),
            resume=bool(args.resume),
        )
    if args.stage == "development":
        if not args.dry_run:
            _require_snapshot_stage_authorized(config, output)
        return _run_development_stage(
            config,
            output,
            arm_configs=arm_configs,
            arms=_selected_arms(args.arm),
            limit=max(0, int(args.limit)),
            dry_run=bool(args.dry_run),
            resume=bool(args.resume),
        )
    if args.stage == "summarize":
        _materialize_development_metrics(config, output)
        return 0
    return _select_fixed_k(config, output)


def _materialize_arm_configs(
    experiment: dict, output: Path
) -> dict[str, Path]:
    control = _load_yaml(_resolve(experiment["frozen_control_config"]))
    paths = {}
    for arm, row in experiment["arms"].items():
        batch_size = int(row["admission_batch_size"])
        raw_size = int(row["raw_negative_pool_size"])
        payload = json.loads(json.dumps(control))
        payload.update(
            {
                "model_id": f"P0V4_DIVERSE_ESCAPE_{arm}_BATCH_CANDIDATE",
                "baseline_parent": str(
                    experiment["frozen_control_config"]
                ),
                "exact_negative_escape_enabled": True,
                "exact_negative_escape_policy_id": str(
                    experiment["negative_escape_policy_id"]
                ),
                "exact_raw_negative_pool_multiplier": 4,
                "batch_master_admission_enabled": bool(
                    experiment["batch_master_admission_enabled"]
                ),
                "production_default": False,
            }
        )
        profile = payload["profiles"]["50"]
        profile["harvest_target"] = batch_size
        profile["tree_max_columns_per_round"] = batch_size
        profile["raw_negative_pool_size"] = raw_size
        profile["effective_native_memory_limit_gb"] = float(
            experiment["effective_native_memory_limit_gb"]
        )
        if batch_size > 128:
            # P0V4's legacy sparse-harvest schedule caps late batches at
            # 128 after the active pool grows.  E256 is a fixed K=256 arm,
            # not an adaptive arm, so explicitly disable that schedule only
            # where it would otherwise change the requested policy.
            payload["native_adaptive_harvest_schedule"] = "disabled"
        target = output / "arm_configs" / f"{arm}.yaml"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )
        paths[str(arm)] = target
    return paths


def _run_snapshot_stage(
    config: dict,
    output: Path,
    *,
    arms: tuple[str, ...],
    dry_run: bool,
    resume: bool,
) -> int:
    stage = dict(config["snapshot_stage"])
    snapshots = _registered_snapshots(stage, output)
    heavy = sum(str(row.get("role")) == "heavy" for row in snapshots)
    ordinary = sum(
        str(row.get("role")) == "ordinary" for row in snapshots
    )
    if (
        heavy != int(stage["required_heavy_snapshot_count"])
        or ordinary != int(stage["required_ordinary_snapshot_count"])
    ):
        _write_json(
            output / "snapshot_stage_gate.json",
            {
                "schema_version": (
                    "lunar_ice_bpc.p0v4_snapshot_stage_gate.v1"
                ),
                "status": (
                    "BLOCKED_INSUFFICIENT_UNIQUE_PROOF_CONTEXTS"
                ),
                "observed_heavy_snapshot_count": heavy,
                "required_heavy_snapshot_count": int(
                    stage["required_heavy_snapshot_count"]
                ),
                "observed_ordinary_snapshot_count": ordinary,
                "required_ordinary_snapshot_count": int(
                    stage["required_ordinary_snapshot_count"]
                ),
                "snapshot_registry": str(
                    (output / "snapshot_registry.json").resolve()
                ),
                "snapshot_registry_sha256": (
                    _sha256(output / "snapshot_registry.json")
                    if (output / "snapshot_registry.json").is_file()
                    else ""
                ),
                "downstream_fixed_k_selection_authorized": False,
                "downstream_gat_oracle_authorized": False,
            },
        )
        raise SystemExit(
            "snapshot stage requires exactly 4 heavy and 12 ordinary "
            "immutable P0V4 snapshot rows"
        )
    schedule_id = "snapshot_replicate_rotating_arm_blocks_v1"
    rows_path = (
        output / "snapshot_stage_rows_rotating_blocks_v1.json"
    )
    rows = (
        [
            dict(row)
            for row in json.loads(
                rows_path.read_text(encoding="utf-8")
            )
        ]
        if resume and rows_path.is_file()
        else []
    )
    completed = {
        (
            str(row.get("arm")),
            int(row.get("snapshot_index") or 0),
            int(row.get("replicate") or 0),
        )
        for row in rows
        if _snapshot_replay_row_reusable(row)
    }
    labels = ("P0V4", *arms)
    for snapshot_index, snapshot_row in enumerate(snapshots, start=1):
        snapshot = _resolve(snapshot_row["path"])
        if not snapshot.is_file():
            raise SystemExit(f"snapshot missing: {snapshot}")
        if snapshot_row.get("sha256") and _sha256(snapshot) != str(
            snapshot_row["sha256"]
        ):
            raise SystemExit(f"snapshot hash mismatch: {snapshot}")
        for replicate in range(
            1, int(stage["blocked_replicates"]) + 1
        ):
            block_order = _rotated_block_order(labels, replicate)
            for block_position, arm in enumerate(block_order, start=1):
                batch_size = (
                    0
                    if arm == "P0V4"
                    else int(
                        config["arms"][arm]["admission_batch_size"]
                    )
                )
                row_key = (arm, snapshot_index, replicate)
                if row_key in completed:
                    continue
                target = (
                    output
                    / "snapshot_replay_rotating_blocks_v1"
                    / arm
                    / f"snapshot_{snapshot_index:02d}"
                    / f"replicate_{replicate:02d}.json"
                )
                target.parent.mkdir(parents=True, exist_ok=True)
                command = [
                    sys.executable,
                    str(REPLAY_RUNNER),
                    "--instance",
                    str(_resolve(stage["source_instance"])),
                    "--snapshot",
                    str(snapshot),
                    "--output",
                    str(target),
                    "--source-role",
                    "mathematical_context",
                    "--completion-bound",
                    "off",
                    "--subset-dominance",
                    "on",
                    "--proof-queue-policy",
                    "Q0",
                    "--wall-time-limit-sec",
                    str(stage["replay_wall_time_limit_sec"]),
                    "--negative-escape-batch-size",
                    str(batch_size),
                ]
                row = {
                    "arm": arm,
                    "snapshot_index": snapshot_index,
                    "snapshot_role": snapshot_row["role"],
                    "replicate": replicate,
                    "blocked_schedule_id": schedule_id,
                    "blocked_arm_order": list(block_order),
                    "blocked_arm_position": block_position,
                    "command": command,
                    "output": str(target),
                }
                if not dry_run:
                    observed = _run_observed(
                        command,
                        run_dir=(
                            target.parent
                            / f"replicate_{replicate:02d}_launcher"
                        ),
                        timeout_sec=(
                            float(stage["replay_wall_time_limit_sec"])
                            + 120.0
                        ),
                    )
                    row.update(observed)
                    row["wall_time_sec"] = row[
                        "launcher_wall_time_sec"
                    ]
                    if int(observed["returncode"]) != 0:
                        rows.append(row)
                        _write_json(
                            rows_path, rows
                        )
                        return int(observed["returncode"])
                rows.append(row)
                _write_json(rows_path, rows)
    if not dry_run:
        _write_json(
            output / "snapshot_stage_summary.json",
            _summarize_snapshot_stage(
                rows,
                config=config,
                snapshots=snapshots,
                schedule_id=schedule_id,
            ),
        )
    return 0


def _rotated_block_order(
    labels: Iterable[str], replicate: int
) -> tuple[str, ...]:
    ordered = tuple(str(label) for label in labels)
    if not ordered:
        return tuple()
    offset = (max(1, int(replicate)) - 1) % len(ordered)
    return ordered[offset:] + ordered[:offset]


def _snapshot_replay_row_reusable(row: Mapping[str, object]) -> bool:
    output_value = str(row.get("output") or "")
    if int(row.get("returncode") or 0) != 0 or not output_value:
        return False
    path = Path(output_value)
    if not path.is_file():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return bool(
        str(payload.get("schema_version"))
        == "lunar_ice_bpc.proof_tail_snapshot_replay.v1"
        and bool(payload.get("fresh_process_arm"))
    )


def _collect_snapshot_stage(
    config: dict,
    output: Path,
    *,
    dry_run: bool,
    resume: bool,
) -> int:
    stage = dict(config["snapshot_stage"])
    source_config = _materialize_snapshot_source_config(
        config, output
    )
    source_instance = _resolve(stage["source_instance"])
    run_dir = output / "snapshot_source_run"
    command = [
        sys.executable,
        str(ACCEPTANCE_RUNNER),
        "--config",
        str(source_config),
        "--scales",
        str(int(stage["source_scale"])),
        "--output-dir",
        str(run_dir),
        "--no-resume",
        "--instance",
        str(source_instance),
    ]
    launch_manifest = {
        "schema_version": (
            "lunar_ice_bpc.p0v4_snapshot_source_launch.v1"
        ),
        "command": command,
        "source_config": str(source_config.resolve()),
        "source_config_sha256": _sha256(source_config),
        "source_instance": str(source_instance.resolve()),
        "source_instance_sha256": _sha256(source_instance),
        "p0v4_frozen_capsule_modified": False,
        "candidate_features_enabled": False,
        "production_default_changed": False,
    }
    state_path = (
        run_dir
        / f"scale_{int(stage['source_scale']):03d}"
        / "b4_2_cold_exact_state.json"
    )
    if not dry_run and not (resume and state_path.is_file()):
        launch_manifest.update(
            _run_observed(
                command,
                run_dir=run_dir,
                timeout_sec=(
                    float(
                        config["development_stage"][
                            "wall_time_limit_sec"
                        ]
                    )
                    + 120.0
                ),
            )
        )
    _write_json(
        output / "snapshot_source_launch_manifest.json",
        launch_manifest,
    )
    if dry_run:
        return 0
    return _materialize_snapshot_registry(
        config,
        output,
        source_config=source_config,
        run_dir=run_dir,
    )


def _materialize_snapshot_source_config(
    config: dict, output: Path
) -> Path:
    payload = json.loads(
        json.dumps(
            _load_yaml(_resolve(config["frozen_control_config"]))
        )
    )
    payload.update(
        {
            "model_id": "P0V4_CURRENT_ENGINE_NOOP_SNAPSHOT_SOURCE",
            "baseline_parent": str(config["frozen_control_config"]),
            "pre_solve_exact_snapshot_enabled": False,
            "pre_solve_pricing_snapshot_enabled": True,
            "exact_negative_escape_enabled": False,
            "batch_master_admission_enabled": False,
            "production_default": False,
        }
    )
    target = output / "snapshot_source" / "p0v4_noop_source.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )
    return target


def _materialize_snapshot_registry(
    config: dict,
    output: Path,
    *,
    source_config: Path,
    run_dir: Path,
) -> int:
    stage = dict(config["snapshot_stage"])
    scale_dir = (
        run_dir / f"scale_{int(stage['source_scale']):03d}"
    )
    result = _read_development_result(run_dir)
    if not bool(result.get("result_available")):
        _write_json(
            output / "snapshot_registry.json",
            {
                "schema_version": (
                    "lunar_ice_bpc.p0v4_snapshot_registry.v1"
                ),
                "status": "SOURCE_RESULT_UNAVAILABLE",
                "source_result": result,
                "snapshots": [],
            },
        )
        return 3
    source_row = dict(result["result_row"])
    probe_value = str(
        source_row.get("root_pool_latest_probe_json") or ""
    )
    probe_path = Path(probe_value) if probe_value else None
    probe = (
        json.loads(probe_path.read_text(encoding="utf-8"))
        if probe_path is not None and probe_path.is_file()
        else {}
    )
    wall_by_iteration = {}
    for history_row in probe.get("history", ()):
        history = dict(history_row)
        iteration = str(
            dict(history.get("dual_context") or {}).get(
                "rmp_iteration_id"
            )
            or ""
        )
        if not iteration:
            continue
        wall_by_iteration[iteration] = max(
            float(wall_by_iteration.get(iteration) or 0.0),
            float(history.get("final_judge_wall_time") or 0.0),
        )
    candidates_by_context_and_mode = {}
    snapshot_root = scale_dir / "pre_solve_pricing_snapshots"
    for path in sorted(snapshot_root.rglob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if (
                str(payload.get("schema_version"))
                != "lunar_ice_bpc.gat_pricing_snapshot.v1"
                or str(payload.get("pricing_mode"))
                not in {"exact_proof", "negative_harvest"}
                or str(payload.get("objective_mode")) != "official"
            ):
                continue
            binding = dict(payload["binding"])
            iteration = str(binding.get("rmp_iteration_id") or "")
            context_key = _payload_hash(
                {
                    "instance": payload["instance_content_hash"],
                    "dual": binding.get("mathematical_dual_hash"),
                    "branch": binding.get("branch_context_hash"),
                    "cut": binding.get("full_cut_context_hash"),
                    "iteration": iteration,
                }
            )
            row = {
                "path": str(path.resolve()),
                "sha256": _sha256(path),
                "snapshot_hash": str(payload["snapshot_hash"]),
                "binding_hash": str(binding["binding_hash"]),
                "mathematical_context_hash": context_key,
                "rmp_iteration_id": iteration,
                "source_pricing_mode": str(payload["pricing_mode"]),
                "source_final_judge_wall_time_sec": float(
                    wall_by_iteration.get(iteration) or 0.0
                ),
                "engine_hash": str(binding.get("engine_hash") or ""),
                "config_hash": str(binding.get("config_hash") or ""),
            }
            candidate_key = (
                context_key,
                str(payload["pricing_mode"]),
            )
            current = candidates_by_context_and_mode.get(candidate_key)
            if current is None or (
                row["source_final_judge_wall_time_sec"],
                row["sha256"],
            ) > (
                current["source_final_judge_wall_time_sec"],
                current["sha256"],
            ):
                candidates_by_context_and_mode[candidate_key] = row
        except Exception:
            continue
    candidates = list(candidates_by_context_and_mode.values())
    heavy_count = int(stage["required_heavy_snapshot_count"])
    ordinary_count = int(stage["required_ordinary_snapshot_count"])
    heavy, ordinary = _select_snapshot_rows(
        candidates,
        heavy_count=heavy_count,
        ordinary_count=ordinary_count,
    )
    proof_context_hashes = {
        str(row["mathematical_context_hash"])
        for row in candidates
        if str(row["source_pricing_mode"]) == "exact_proof"
    }
    selected = [
        {**row, "role": "heavy"} for row in heavy
    ] + [
        {**row, "role": "ordinary"} for row in ordinary
    ]
    sufficient = bool(
        len(heavy) == heavy_count
        and len(ordinary) == ordinary_count
    )
    registry = {
        "schema_version": (
            "lunar_ice_bpc.p0v4_snapshot_registry.v1"
        ),
        "status": (
            "IMMUTABLE_4_HEAVY_12_ORDINARY_REGISTERED"
            if sufficient
            else "INSUFFICIENT_UNIQUE_PROOF_CONTEXTS"
        ),
        "source_config": str(source_config.resolve()),
        "source_config_sha256": _sha256(source_config),
        "source_result_state": str(
            Path(str(result["result_state_path"])).resolve()
        ),
        "source_result_state_sha256": str(
            result["result_state_sha256"]
        ),
        "source_probe": (
            "" if probe_path is None else str(probe_path.resolve())
        ),
        "source_probe_sha256": (
            ""
            if probe_path is None or not probe_path.is_file()
            else _sha256(probe_path)
        ),
        "discovered_unique_context_count": len(
            {
                str(row["mathematical_context_hash"])
                for row in candidates
            }
        ),
        "discovered_heavy_proof_context_count": sum(
            str(row["source_pricing_mode"]) == "exact_proof"
            for row in candidates
        ),
        "discovered_ordinary_negative_harvest_context_count": sum(
            str(row["source_pricing_mode"]) == "negative_harvest"
            and str(row["mathematical_context_hash"])
            not in proof_context_hashes
            for row in candidates
        ),
        "required_heavy_snapshot_count": heavy_count,
        "required_ordinary_snapshot_count": ordinary_count,
        "snapshots": selected,
        "current_engine_p0v4_noop_compatibility_source": True,
        "frozen_p0v4_capsule_modified": False,
        "production_default_changed": False,
    }
    _write_json(output / "snapshot_registry.json", registry)
    return 0 if sufficient else 3


def _select_snapshot_rows(
    candidates: Iterable[Mapping[str, object]],
    *,
    heavy_count: int,
    ordinary_count: int,
) -> tuple[list[dict], list[dict]]:
    rows = [dict(row) for row in candidates]
    ranked = sorted(
        (
            row
            for row in rows
            if str(row["source_pricing_mode"]) == "exact_proof"
        ),
        key=lambda row: (
            -float(row["source_final_judge_wall_time_sec"]),
            str(row["mathematical_context_hash"]),
        ),
    )
    heavy = ranked[:heavy_count]
    proof_context_hashes = {
        str(row["mathematical_context_hash"])
        for row in rows
        if str(row["source_pricing_mode"]) == "exact_proof"
    }
    ordinary_pool = sorted(
        (
            row
            for row in rows
            if str(row["source_pricing_mode"]) == "negative_harvest"
            if str(row["mathematical_context_hash"])
            not in proof_context_hashes
        ),
        key=lambda row: (
            float(row["source_final_judge_wall_time_sec"]),
            str(row["mathematical_context_hash"]),
        ),
    )
    ordinary = _evenly_spaced_rows(ordinary_pool, ordinary_count)
    return heavy, ordinary


def _registered_snapshots(
    stage: Mapping[str, object], output: Path
) -> list[dict]:
    configured = [
        dict(row) for row in (stage.get("snapshots") or [])
    ]
    if configured:
        return configured
    registry_path = output / "snapshot_registry.json"
    if not registry_path.is_file():
        return []
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if str(registry.get("status")) not in {
        "IMMUTABLE_4_HEAVY_12_ORDINARY_REGISTERED",
        "INSUFFICIENT_UNIQUE_PROOF_CONTEXTS",
    }:
        return []
    return [dict(row) for row in registry.get("snapshots", ())]


def _run_development_stage(
    config: dict,
    output: Path,
    *,
    arm_configs: dict[str, Path],
    arms: tuple[str, ...],
    limit: int,
    dry_run: bool,
    resume: bool,
) -> int:
    instances = list(config["development_stage"]["instance_paths"])
    if limit:
        instances = instances[:limit]
    rows = _load_existing_development_rows(output) if resume else []
    ledger_path = output / (
        "development_stage_dry_run_rows.json"
        if dry_run
        else "development_stage_rows.json"
    )
    existing_by_key: dict[tuple[str, str], dict] = {}
    for row in rows:
        key = (str(row.get("arm")), str(row.get("instance_key")))
        if key in existing_by_key:
            raise SystemExit(
                f"duplicate development ledger row {key[0]}/{key[1]}"
            )
        existing_by_key[key] = row
    labels = ("P0V4", *arms)
    config_by_label = {
        "P0V4": _resolve(config["frozen_control_config"]),
        **{arm: arm_configs[arm] for arm in arms},
    }
    schedule_id = "development_instance_rotating_arm_blocks_v1"
    for instance_index, instance in enumerate(instances, start=1):
        instance_path = _resolve(instance)
        instance_key = _instance_key(instance_path)
        block_order = _rotated_block_order(labels, instance_index)
        for block_position, label in enumerate(block_order, start=1):
            instance_key = _instance_key(instance_path)
            key = (label, instance_key)
            label_config = config_by_label[label]
            existing = existing_by_key.get(key)
            if existing is not None:
                if _development_row_reusable(
                    existing,
                    label=label,
                    instance_path=instance_path,
                    config_path=label_config,
                    schedule_id=schedule_id,
                    block_order=block_order,
                    block_position=block_position,
                ):
                    continue
                raise SystemExit(
                    "development resume evidence mismatch for "
                    f"{label}/{instance_key}; use a new output directory"
                )
            run_dir = (
                output
                / "development"
                / label
                / instance_key
            )
            command = [
                sys.executable,
                str(ACCEPTANCE_RUNNER),
                "--config",
                str(label_config),
                "--scales",
                "50",
                "--output-dir",
                str(run_dir),
                "--no-resume",
                "--instance",
                str(instance_path),
            ]
            row = {
                "arm": label,
                "instance_key": instance_key,
                "instance_path": str(instance_path),
                "instance_sha256": _sha256(instance_path),
                "arm_config_path": str(label_config.resolve()),
                "arm_config_sha256": _sha256(label_config),
                "development_schedule_id": schedule_id,
                "blocked_arm_order": list(block_order),
                "blocked_arm_position": block_position,
                "command": command,
                "run_dir": str(run_dir),
                "route_opportunity_rows_dir": str(
                    (
                        run_dir / "route_opportunity_rows"
                    ).resolve()
                ),
            }
            if not dry_run:
                observed = _run_observed(
                    command,
                    run_dir=run_dir,
                    timeout_sec=(
                        float(
                            config["development_stage"][
                                "wall_time_limit_sec"
                            ]
                        )
                        + 120.0
                    ),
                    environment_overrides={
                        "LUNAR_ICE_GAT_TRAINING_ROWS_DIR": str(
                            (
                                run_dir / "route_opportunity_rows"
                            ).resolve()
                        )
                    },
                )
                row.update(observed)
                row.update(_read_development_result(run_dir))
            rows.append(row)
            existing_by_key[key] = row
            _write_json(ledger_path, rows)
    if dry_run:
        return 0
    if set(arms) == set(config["arms"]):
        _materialize_development_metrics(config, output)
    return (
        0
        if all(
            _development_row_has_result(row)
            for row in rows
            if str(row.get("arm")) in {"P0V4", *arms}
        )
        else 3
    )


def _select_fixed_k(config: dict, output: Path) -> int:
    all_metrics = _materialize_development_metrics(config, output)
    snapshot_eligible = _snapshot_eligible_arms(config, output)
    metrics = {}
    for arm in config["arms"]:
        path = output / "development" / arm / "oracle_metrics.json"
        row = all_metrics[arm]
        if int(row.get("development_instance_count") or 0) != 10:
            raise SystemExit(f"{arm} does not contain ten development instances")
        if int(row.get("correctness_redline_count") or 0) != 0:
            continue
        if arm not in snapshot_eligible:
            continue
        metrics[arm] = row
    if not metrics:
        raise SystemExit("every fixed-K arm failed correctness")
    keys = (
        lambda item: (
            -int(item[1]["exact_closure_count"]),
            -int(item[1]["root_closure_count"]),
            float(item[1]["commonly_closed_paired_geometric_mean"]),
            float(item[1]["root_gap_pricing_pressure_auc"]),
            float(item[1]["cg_round_count"]),
            float(item[1]["peak_rss_gb"]),
            item[0],
        )
    )
    selected_arm, selected_metrics = min(metrics.items(), key=keys)
    if int(selected_metrics["exact_closure_count"]) < 7:
        status = "BIDIRECTIONAL_FEASIBILITY_FALLBACK_TRIGGERED"
    else:
        status = "FIXED_K_SELECTED"
    selected_config = output / "arm_configs" / f"{selected_arm}.yaml"
    if not selected_config.is_file():
        raise SystemExit(
            f"selected fixed-K config is missing: {selected_config}"
        )
    payload = {
        "schema_version": "lunar_ice_bpc.p0v4_fixed_k_selection.v1",
        "status": status,
        "selected_arm": selected_arm,
        "selected_batch_size": int(
            config["arms"][selected_arm]["admission_batch_size"]
        ),
        "selected_raw_pool_size": int(
            config["arms"][selected_arm]["raw_negative_pool_size"]
        ),
        "selected_config": str(selected_config.resolve()),
        "selected_config_sha256": _sha256(selected_config),
        "admission_batch_size_by_scale": {
            "5": 8,
            "10": 16,
            "20": 32,
            "30": 64,
            "50": int(
                config["arms"][selected_arm][
                    "admission_batch_size"
                ]
            ),
            "100": 128,
        },
        "runtime_context_switching": False,
        "metrics": metrics,
        "p0v4_overwritten": False,
        "production_default_changed": False,
    }
    _write_json(output / "fixed_k_selection.json", payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _snapshot_eligible_arms(config: dict, output: Path) -> set[str]:
    if "snapshot_stage" not in config:
        return set(str(value) for value in config["arms"])
    summary_path = output / "snapshot_stage_summary.json"
    if not summary_path.is_file():
        raise SystemExit(
            "fixed-K selection requires completed snapshot replay"
        )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if (
        str(summary.get("status") or "") != "PASS"
        or not bool(
            summary.get("downstream_fixed_k_selection_authorized")
        )
        or int(summary.get("total_audit_failure_count") or 0) != 0
    ):
        raise SystemExit(
            "snapshot replay audit did not authorize fixed-K selection"
        )
    rows_per_arm = (
        int(config["snapshot_stage"]["required_heavy_snapshot_count"])
        + int(
            config["snapshot_stage"][
                "required_ordinary_snapshot_count"
            ]
        )
    ) * int(config["snapshot_stage"]["blocked_replicates"])
    arms = dict(summary.get("arms") or {})
    control = dict(arms.get("P0V4") or {})
    if (
        int(control.get("completed_count") or 0) != rows_per_arm
        or int(control.get("correctness_redline_count") or 0) != 0
    ):
        raise SystemExit("P0V4 snapshot replay control is incomplete")
    return {
        str(arm)
        for arm in config["arms"]
        for row in (dict(arms.get(str(arm)) or {}),)
        if int(row.get("completed_count") or 0) == rows_per_arm
        and int(row.get("correctness_redline_count") or 0) == 0
    }


def _require_snapshot_stage_authorized(
    config: Mapping[str, object], output: Path
) -> None:
    summary_path = output / "snapshot_stage_summary.json"
    if not summary_path.is_file():
        raise SystemExit(
            "development requires completed strict snapshot replay audit"
        )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    expected_rows = (
        int(
            dict(config["snapshot_stage"])[
                "required_heavy_snapshot_count"
            ]
        )
        + int(
            dict(config["snapshot_stage"])[
                "required_ordinary_snapshot_count"
            ]
        )
    ) * int(dict(config["snapshot_stage"])["blocked_replicates"]) * (
        1 + len(dict(config["arms"]))
    )
    if (
        str(summary.get("schema_version") or "")
        != "lunar_ice_bpc.p0v4_fixed_k_snapshot_summary.v2"
        or str(summary.get("status") or "") != "PASS"
        or int(summary.get("expected_row_count") or 0) != expected_rows
        or int(summary.get("observed_row_count") or 0) != expected_rows
        or int(summary.get("total_audit_failure_count") or 0) != 0
        or not bool(
            summary.get("downstream_fixed_k_selection_authorized")
        )
    ):
        raise SystemExit(
            "development blocked by strict snapshot replay audit"
        )


def _materialize_development_metrics(
    config: dict, output: Path
) -> dict[str, dict]:
    metric_horizon_sec = max(
        1.0,
        float(
            config["development_stage"].get(
                "wall_time_limit_sec", 3600.0
            )
        ),
    )
    expected_instance_paths = tuple(
        _resolve(value)
        for value in config["development_stage"]["instance_paths"]
    )
    expected_instances = tuple(
        _instance_key(path) for path in expected_instance_paths
    )
    rows = _load_existing_development_rows(output)
    by_label: dict[str, dict[str, dict]] = {}
    for row in rows:
        if not _development_row_has_result(row):
            continue
        label = str(row["arm"])
        instance_key = str(row["instance_key"])
        if instance_key in by_label.setdefault(label, {}):
            raise SystemExit(
                f"duplicate development result {label}/{instance_key}"
            )
        by_label[label][instance_key] = row
    required_labels = ("P0V4", *tuple(config["arms"]))
    for label in required_labels:
        observed = set(by_label.get(label, {}))
        missing = set(expected_instances) - observed
        extra = observed - set(expected_instances)
        if missing or extra:
            raise SystemExit(
                f"{label} development coverage mismatch "
                f"missing={sorted(missing)} extra={sorted(extra)}"
            )
    development_config_by_label = {
        "P0V4": _resolve(config["frozen_control_config"]),
        **{
            str(arm): output / "arm_configs" / f"{arm}.yaml"
            for arm in config["arms"]
        },
    }
    schedule_id = "development_instance_rotating_arm_blocks_v1"
    for instance_index, instance_path in enumerate(
        expected_instance_paths, start=1
    ):
        instance_key = _instance_key(instance_path)
        block_order = _rotated_block_order(
            required_labels, instance_index
        )
        for block_position, label in enumerate(block_order, start=1):
            config_path = development_config_by_label[label]
            if not config_path.is_file():
                raise SystemExit(
                    f"development config missing for {label}: "
                    f"{config_path}"
                )
            if not _development_row_reusable(
                by_label[label][instance_key],
                label=label,
                instance_path=instance_path,
                config_path=config_path,
                schedule_id=schedule_id,
                block_order=block_order,
                block_position=block_position,
            ):
                raise SystemExit(
                    "development evidence hash/schedule mismatch for "
                    f"{label}/{instance_key}"
                )

    records = {
        label: {
            instance_key: _development_record(
                by_label[label][instance_key],
                metric_horizon_sec=metric_horizon_sec,
            )
            for instance_key in expected_instances
        }
        for label in required_labels
    }
    for instance_key in expected_instances:
        observed_pressure_levels = [
            records[label][instance_key][
                "maximum_observed_pricing_pressure"
            ]
            for label in required_labels
            if records[label][instance_key][
                "maximum_observed_pricing_pressure"
            ]
            is not None
        ]
        unknown_pressure_penalty = (
            max(observed_pressure_levels)
            if observed_pressure_levels
            else None
        )
        for label in required_labels:
            record = records[label][instance_key]
            if unknown_pressure_penalty is None:
                record["pricing_pressure_auc"] = None
                continue
            record["pricing_pressure_auc"] = (
                float(record["observed_pricing_pressure_integral"])
                + float(
                    record["unknown_pricing_pressure_duration_sec"]
                )
                * unknown_pressure_penalty
            ) / metric_horizon_sec
            record["unknown_pricing_pressure_penalty"] = (
                unknown_pressure_penalty
            )
    best_terminal_bound = {}
    max_pressure_auc = {}
    for instance_key in expected_instances:
        bounds = [
            record["terminal_root_bound"]
            for label in required_labels
            for record in (records[label][instance_key],)
            if record["terminal_root_bound"] is not None
        ]
        best_terminal_bound[instance_key] = (
            min(bounds) if bounds else None
        )
        observed_pressure = [
            records[label][instance_key]["pricing_pressure_auc"]
            for label in required_labels
            if records[label][instance_key][
                "pricing_pressure_auc"
            ]
            is not None
        ]
        max_pressure_auc[instance_key] = (
            max(observed_pressure) if observed_pressure else None
        )

    metrics: dict[str, dict] = {}
    control = records["P0V4"]
    for label in required_labels:
        label_records = records[label]
        common = [
            instance_key
            for instance_key in expected_instances
            if control[instance_key]["exact"]
            and label_records[instance_key]["exact"]
        ]
        time_ratios = [
            label_records[key]["wall_time_sec"]
            / max(1.0e-9, control[key]["wall_time_sec"])
            for key in common
        ]
        combined_auc_values = []
        for instance_key in expected_instances:
            record = label_records[instance_key]
            best_bound = best_terminal_bound[instance_key]
            if (
                best_bound is None
                or record["terminal_root_bound"] is None
            ):
                root_gap_auc = 1.0
            else:
                root_gap_auc = _root_gap_auc(
                    record["root_bound_trace"],
                    best_bound=float(best_bound),
                    metric_horizon_sec=metric_horizon_sec,
                )
            pressure_denominator = max_pressure_auc[instance_key]
            normalized_pressure = (
                1.0
                if record["pricing_pressure_auc"] is None
                else 0.0
                if pressure_denominator is None
                or pressure_denominator <= 0.0
                else record["pricing_pressure_auc"]
                / pressure_denominator
            )
            combined_auc_values.append(
                0.5 * root_gap_auc + 0.5 * normalized_pressure
            )
        row = {
            "schema_version": (
                "lunar_ice_bpc.p0v4_fixed_k_oracle_metrics.v1"
            ),
            "arm": label,
            "development_instance_count": len(label_records),
            "exact_closure_count": sum(
                int(record["exact"])
                for record in label_records.values()
            ),
            "root_closure_count": sum(
                int(record["root_closed"])
                for record in label_records.values()
            ),
            "commonly_closed_instance_count": len(common),
            "commonly_closed_paired_geometric_mean": (
                _geometric_mean(time_ratios)
                if time_ratios
                else 1.0e12
            ),
            "root_gap_pricing_pressure_auc": _mean(
                combined_auc_values
            ),
            "cg_round_count": _mean(
                [
                    record["cg_round_count"]
                    for record in label_records.values()
                ]
            ),
            "peak_rss_gb": max(
                record["peak_rss_gb"]
                for record in label_records.values()
            ),
            "resource_adverse_count": sum(
                int(record["resource_adverse_event"])
                for record in label_records.values()
            ),
            "correctness_redline_count": sum(
                record["redline_count"]
                for record in label_records.values()
            ),
            "instance_records": [
                label_records[key] for key in expected_instances
            ],
            "metric_definition": {
                "paired_geometric_mean": (
                    "candidate_wall_time_divided_by_P0V4_wall_time_on_"
                    "commonly_exact_instances"
                ),
                "root_gap_pricing_pressure_auc": (
                    "mean_over_instances_of_half_normalized_root_bound_"
                    "trajectory_gap_to_best_observed_terminal_bound_plus_"
                    "half_normalized_true_negative_pressure_auc_on_a_"
                    "fixed_wall_clock_horizon"
                ),
                "metric_horizon_sec": metric_horizon_sec,
                "cg_round_count": "mean_final_judge_history_round_count",
                "peak_rss_gb": "maximum_observed_process_tree_rss",
                "resource_adverse_count": (
                    "native_memory_or_frontier_resource_failures"
                ),
                "lower_is_better_except_closure_counts": True,
            },
        }
        metrics[label] = row
        target = output / "development" / label / "oracle_metrics.json"
        _write_json(target, row)
    _write_json(
        output / "development_metrics_manifest.json",
        {
            "schema_version": (
                "lunar_ice_bpc.p0v4_development_metrics_manifest.v1"
            ),
            "labels": list(required_labels),
            "expected_instances": list(expected_instances),
            "metrics": {
                label: {
                    "path": str(
                        (
                            output
                            / "development"
                            / label
                            / "oracle_metrics.json"
                        ).resolve()
                    ),
                    "sha256": _sha256(
                        output
                        / "development"
                        / label
                        / "oracle_metrics.json"
                    ),
                }
                for label in required_labels
            },
        },
    )
    return metrics


def _load_existing_development_rows(output: Path) -> list[dict]:
    path = output / "development_stage_rows.json"
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise SystemExit(f"invalid development rows payload: {path}")
    return [dict(row) for row in payload]


def _development_row_has_result(row: Mapping[str, object]) -> bool:
    result = row.get("result_row")
    return bool(
        row.get("result_available")
        and isinstance(result, dict)
        and result.get("instance_key")
    )


def _development_row_reusable(
    row: Mapping[str, object],
    *,
    label: str,
    instance_path: Path,
    config_path: Path,
    schedule_id: str,
    block_order: tuple[str, ...],
    block_position: int,
) -> bool:
    if not _development_row_has_result(row):
        return False
    result = dict(row.get("result_row") or {})
    state_path = Path(str(row.get("result_state_path") or ""))
    return bool(
        str(row.get("arm") or "") == label
        and str(row.get("instance_key") or "")
        == _instance_key(instance_path)
        and Path(str(row.get("instance_path") or "")).resolve()
        == instance_path.resolve()
        and str(row.get("instance_sha256") or "")
        == _sha256(instance_path)
        and Path(str(row.get("arm_config_path") or "")).resolve()
        == config_path.resolve()
        and str(row.get("arm_config_sha256") or "")
        == _sha256(config_path)
        and str(row.get("development_schedule_id") or "")
        == schedule_id
        and tuple(row.get("blocked_arm_order") or ()) == block_order
        and int(row.get("blocked_arm_position") or 0)
        == int(block_position)
        and int(row.get("returncode") or 0) in {0, 1}
        and not str(row.get("launcher_termination_reason") or "")
        and str(result.get("instance_key") or "")
        == _instance_key(instance_path)
        and state_path.is_file()
        and str(row.get("result_state_sha256") or "")
        == _sha256(state_path)
        and _development_fixed_k_runtime_contract_valid(
            row,
            label=label,
            config_path=config_path,
        )
    )


def _development_fixed_k_runtime_contract_valid(
    row: Mapping[str, object],
    *,
    label: str,
    config_path: Path,
) -> bool:
    if label == "P0V4":
        return True
    try:
        config = _load_yaml(config_path)
        if not bool(config.get("exact_negative_escape_enabled")):
            return True
        profile = dict(
            dict(config.get("profiles") or {}).get("50") or {}
        )
        expected_batch = int(profile["harvest_target"])
        expected_raw = int(profile["raw_negative_pool_size"])
        if expected_raw != 4 * expected_batch:
            return False
        result = dict(row.get("result_row") or {})
        if (
            int(
                result.get(
                    "labeling_final_judge_exact_harvest_target"
                )
                or 0
            )
            != expected_batch
        ):
            return False
        probe_value = str(
            result.get("root_pool_latest_probe_json")
            or result.get("source_probe_json")
            or ""
        )
        probe_path = Path(probe_value)
        if not probe_path.is_file():
            return False
        history = list(
            json.loads(
                probe_path.read_text(encoding="utf-8")
            ).get("history")
            or []
        )
        if not history:
            return False
        for history_row_value in history:
            history_row = dict(history_row_value)
            effective = history_row.get(
                "labeling_final_judge_effective_exact_harvest_target"
            )
            if (
                effective is not None
                and int(effective) != expected_batch
            ):
                return False
            if bool(history_row.get("negative_escape_triggered")):
                native_raw = int(
                    history_row.get(
                        "native_raw_unique_negative_count"
                    )
                    or history_row.get(
                        "raw_unique_negative_count"
                    )
                    or 0
                )
                audited_raw = int(
                    history_row.get(
                        "audited_raw_unique_negative_count"
                    )
                    or history_row.get("raw_negative_count")
                    or native_raw
                )
                if (
                    str(
                        history_row.get(
                            "negative_escape_termination_reason"
                        )
                        or ""
                    )
                    != "RAW_TRUE_NEGATIVE_POOL_REACHED"
                    or native_raw != expected_raw
                    or audited_raw < expected_batch
                    or int(
                        history_row.get(
                            "selected_diverse_negative_count"
                        )
                        or 0
                    )
                    != expected_batch
                    or bool(
                        history_row.get("can_certify_no_negative")
                    )
                ):
                    return False
        return True
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError):
        return False


def _read_development_result(run_dir: Path) -> dict:
    state_path = (
        run_dir / "scale_050" / "b4_2_cold_exact_state.json"
    )
    if not state_path.is_file():
        return {
            "result_available": False,
            "result_state_path": str(state_path),
        }
    state = json.loads(state_path.read_text(encoding="utf-8"))
    rows = list(state.get("rows") or [])
    if len(rows) != 1:
        return {
            "result_available": False,
            "result_state_path": str(state_path),
            "result_row_count": len(rows),
        }
    return {
        "result_available": True,
        "result_state_path": str(state_path.resolve()),
        "result_state_sha256": _sha256(state_path),
        "result_row": dict(rows[0]),
    }


def _run_observed(
    command: list[str],
    *,
    run_dir: Path,
    timeout_sec: float,
    environment_overrides: Mapping[str, str] | None = None,
) -> dict:
    run_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = run_dir / "oracle_launcher_stdout.log"
    stderr_path = run_dir / "oracle_launcher_stderr.log"
    started = monotonic()
    peak_rss = 0
    termination_reason = ""
    with stdout_path.open("w", encoding="utf-8") as stdout, (
        stderr_path.open("w", encoding="utf-8")
    ) as stderr:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env={
                **_execution_env(),
                **dict(environment_overrides or {}),
            },
            stdout=stdout,
            stderr=stderr,
            text=True,
            start_new_session=True,
        )
        try:
            while process.poll() is None:
                peak_rss = max(
                    peak_rss, _process_tree_rss_bytes(process.pid)
                )
                if monotonic() - started >= float(timeout_sec):
                    termination_reason = "ORACLE_OUTER_DEADLINE"
                    _terminate_process_group(process)
                    break
                sleep(1.0)
        except BaseException:
            _terminate_process_group(process)
            raise
        returncode = int(process.wait())
    return {
        "returncode": returncode,
        "launcher_wall_time_sec": round(
            monotonic() - started, 6
        ),
        "peak_process_tree_rss_gb": round(
            peak_rss / (1024.0**3), 6
        ),
        "launcher_termination_reason": termination_reason,
        "launcher_stdout": str(stdout_path.resolve()),
        "launcher_stderr": str(stderr_path.resolve()),
    }


def _terminate_process_group(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=10.0)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    process.wait(timeout=5.0)


def _process_tree_rss_bytes(root_pid: int) -> int:
    children: dict[int, list[int]] = {}
    rss: dict[int, int] = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        try:
            fields = (entry / "status").read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()
        except OSError:
            continue
        parent = 0
        resident = 0
        for line in fields:
            if line.startswith("PPid:"):
                parent = int(line.split()[1])
            elif line.startswith("VmRSS:"):
                resident = int(line.split()[1]) * 1024
        children.setdefault(parent, []).append(pid)
        rss[pid] = resident
    total = 0
    stack = [int(root_pid)]
    seen: set[int] = set()
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        total += rss.get(pid, 0)
        stack.extend(children.get(pid, ()))
    return total


def _development_record(
    launcher_row: Mapping[str, object],
    *,
    metric_horizon_sec: float = 3600.0,
) -> dict:
    row = dict(launcher_row["result_row"])
    horizon = max(1.0, float(metric_horizon_sec))
    probe_path_value = str(
        row.get("root_pool_latest_probe_json")
        or row.get("source_probe_json")
        or ""
    )
    probe_path = Path(probe_path_value) if probe_path_value else None
    probe = (
        json.loads(probe_path.read_text(encoding="utf-8"))
        if probe_path is not None and probe_path.is_file()
        else {}
    )
    history = [
        dict(value) for value in (probe.get("history") or [])
    ]
    final_judge = dict(probe.get("final_judge") or {})
    native_backend = dict(
        final_judge.get("native_backend_result") or {}
    )
    native_engine_status = str(
        native_backend.get("engine_status")
        or final_judge.get("engine_status")
        or ""
    )
    resource_adverse_event = native_engine_status in {
        "MEMORY_LIMIT",
        "FRONTIER_LIMIT",
        "HOST_MEMORY_LIMIT",
    }
    root_trace = []
    cumulative = 0.0
    pressure_intervals: list[tuple[float, float | None]] = []
    observed_pressures: list[float] = []
    last_observed_pressure: float | None = None
    for history_row in history:
        recorded_elapsed = _optional_float(
            history_row.get("round_elapsed_wall_time_sec")
        )
        if recorded_elapsed is None:
            duration = max(
                1.0e-9,
                float(
                    history_row.get("round_wall_time_sec") or 0.0
                )
                or float(
                    history_row.get("final_judge_wall_time") or 0.0
                )
                or 1.0,
            )
            elapsed = min(horizon, cumulative + duration)
        else:
            elapsed = min(
                horizon, max(cumulative, recorded_elapsed)
            )
            duration = max(0.0, elapsed - cumulative)
        cumulative = elapsed
        bound = _optional_float(
            history_row.get("node_lp_bound")
        )
        if bound is not None:
            root_trace.append(
                {
                    "elapsed_sec": cumulative,
                    "root_bound": bound,
                }
            )
        negative_count = max(
            0,
            int(
                history_row.get("candidate_negative_count")
                or history_row.get("negative_column_count")
                or 0
            ),
        )
        best_rc = _optional_float(
            history_row.get("harvest_best_true_rc")
        )
        pricing_state = str(
            history_row.get("pricing_state") or ""
        )
        if pricing_state == "CERTIFIED_NO_NEGATIVE":
            pressure = 0.0
        elif pricing_state == "FOUND_NEGATIVE" or negative_count > 0:
            pressure = log(1.0 + negative_count) + max(
                0.0, -(best_rc or 0.0)
            )
        else:
            # No candidate from an incomplete call is not evidence of zero
            # remaining pressure.
            pressure = last_observed_pressure
        if pressure is not None:
            last_observed_pressure = pressure
            observed_pressures.append(pressure)
        pressure_intervals.append((duration, pressure))
        if cumulative >= horizon:
            break
    pressure_penalty = (
        max(observed_pressures) if observed_pressures else None
    )
    observed_pressure_integral = sum(
        duration * pressure
        for duration, pressure in pressure_intervals
        if pressure is not None
    )
    unknown_pressure_duration = sum(
        duration
        for duration, pressure in pressure_intervals
        if pressure is None
    )
    remaining_horizon = max(0.0, horizon - cumulative)
    terminal_pressure = (
        last_observed_pressure
        if last_observed_pressure is not None
        else pressure_penalty
    )
    if resource_adverse_event or terminal_pressure is None:
        unknown_pressure_duration += remaining_horizon
    else:
        observed_pressure_integral += (
            terminal_pressure * remaining_horizon
        )
    pressure_integral = (
        observed_pressure_integral
        + unknown_pressure_duration * float(pressure_penalty or 0.0)
    )
    redline_keys = (
        "certificate_leak",
        "manual_rc_fail",
        "pricing_rc_fail",
        "true_dual_rc_recompute_missing",
        "worker_certificate_leak",
        "tail_dual_certificate_leak",
        "root_pool_large_task_direct_worker_certificate_leak_count",
        "root_pool_support_continuation_certificate_leak_count",
        "root_pool_tail_dual_certificate_leak_count",
        "root_pool_true_dual_rc_recompute_missing_count",
        "root_pool_worker_certificate_leak_count",
    )
    exact = bool(
        row.get("bpc_tree_optimal")
        or str(row.get("algorithm_status")) == "BPC_OPTIMAL"
    )
    configured_batch = int(
        row.get("labeling_final_judge_exact_harvest_target") or 0
    )
    fixed_k_contract_enabled = bool(
        configured_batch > 0
        and any(
            bool(value.get("batch_master_admission_enabled"))
            for value in history
        )
    )
    fixed_k_contract_violation_count = 0
    if fixed_k_contract_enabled:
        expected_raw = 4 * configured_batch
        for history_row in history:
            effective = history_row.get(
                "labeling_final_judge_effective_exact_harvest_target"
            )
            if (
                effective is not None
                and int(effective) != configured_batch
            ):
                fixed_k_contract_violation_count += 1
            if bool(history_row.get("negative_escape_triggered")):
                native_raw = int(
                    history_row.get(
                        "native_raw_unique_negative_count"
                    )
                    or history_row.get(
                        "raw_unique_negative_count"
                    )
                    or 0
                )
                audited_raw = int(
                    history_row.get(
                        "audited_raw_unique_negative_count"
                    )
                    or history_row.get("raw_negative_count")
                    or native_raw
                )
                if (
                    str(
                        history_row.get(
                            "negative_escape_termination_reason"
                        )
                        or ""
                    )
                    != "RAW_TRUE_NEGATIVE_POOL_REACHED"
                    or native_raw != expected_raw
                    or audited_raw < configured_batch
                    or int(
                        history_row.get(
                            "selected_diverse_negative_count"
                        )
                        or 0
                    )
                    != configured_batch
                    or bool(
                        history_row.get("can_certify_no_negative")
                    )
                ):
                    fixed_k_contract_violation_count += 1
    return {
        "instance_key": str(row["instance_key"]),
        "exact": exact,
        "root_closed": bool(
            exact or row.get("root_pool_certified")
        ),
        "algorithm_status": str(
            row.get("algorithm_status") or ""
        ),
        "wall_time_sec": float(
            row.get("cold_start_total_sec") or 0.0
        ),
        "terminal_root_bound": _optional_float(
            probe.get("root_lp_bound")
            if probe
            else row.get("root_lp_bound")
        ),
        "root_bound_trace": root_trace,
        "pricing_pressure_auc": (
            None
            if pressure_penalty is None
            else pressure_integral / horizon
        ),
        "observed_pricing_pressure_integral": (
            observed_pressure_integral
        ),
        "unknown_pricing_pressure_duration_sec": (
            unknown_pressure_duration
        ),
        "maximum_observed_pricing_pressure": pressure_penalty,
        "unknown_pricing_pressure_penalty": pressure_penalty,
        "cg_round_count": int(
            row.get("root_pool_final_judge_history_round_count")
            or probe.get("pricing_round_count")
            or len(history)
        ),
        "peak_rss_gb": float(
            launcher_row.get("peak_process_tree_rss_gb") or 0.0
        ),
        "native_engine_status": native_engine_status,
        "resource_adverse_event": resource_adverse_event,
        "metric_horizon_sec": horizon,
        "redline_count": sum(
            int(row.get(key) or 0) for key in redline_keys
        )
        + int(not bool(row.get("no_cheat_pass", True)))
        + fixed_k_contract_violation_count,
        "fixed_k_contract_violation_count": (
            fixed_k_contract_violation_count
        ),
        "config_hash": str(row.get("config_hash") or ""),
        "probe_path": (
            "" if probe_path is None else str(probe_path.resolve())
        ),
        "probe_sha256": (
            ""
            if probe_path is None or not probe_path.is_file()
            else _sha256(probe_path)
        ),
        "result_state_path": str(
            launcher_row.get("result_state_path") or ""
        ),
        "result_state_sha256": str(
            launcher_row.get("result_state_sha256") or ""
        ),
    }


def _root_gap_auc(
    trace: list[dict],
    *,
    best_bound: float,
    metric_horizon_sec: float = 3600.0,
) -> float:
    if not trace:
        return 1.0
    horizon = max(1.0, float(metric_horizon_sec))
    denominator = max(1.0e-9, abs(float(best_bound)))
    total = 0.0
    weight = 0.0
    previous_elapsed = 0.0
    last_gap = 1.0
    for row in trace:
        elapsed = min(
            horizon,
            max(previous_elapsed, float(row["elapsed_sec"])),
        )
        duration = max(0.0, elapsed - previous_elapsed)
        gap = max(
            0.0,
            (float(row["root_bound"]) - float(best_bound))
            / denominator,
        )
        total += min(1.0e6, gap) * duration
        weight += duration
        previous_elapsed = elapsed
        last_gap = min(1.0e6, gap)
        if previous_elapsed >= horizon:
            break
    remaining = max(0.0, horizon - previous_elapsed)
    total += last_gap * remaining
    weight += remaining
    return total / max(1.0e-9, weight)


def _summarize_snapshot_stage(
    rows: list[dict],
    *,
    config: Mapping[str, object],
    snapshots: list[dict],
    schedule_id: str,
) -> dict:
    """Audit the complete blocked snapshot experiment before fixed-K use.

    A row being readable is not sufficient evidence.  This audit binds every
    arm/replicate to the immutable snapshot, checks the rotating blocked
    schedule, and verifies the exact fail-closed negative-escape contract.
    """

    stage = dict(config["snapshot_stage"])
    arm_configs = {
        str(key): dict(value)
        for key, value in dict(config["arms"]).items()
    }
    labels = ("P0V4", *arm_configs)
    blocked_replicates = int(stage["blocked_replicates"])
    expected_keys = {
        (arm, snapshot_index, replicate)
        for arm in labels
        for snapshot_index in range(1, len(snapshots) + 1)
        for replicate in range(1, blocked_replicates + 1)
    }
    rows_by_key: dict[tuple[str, int, int], list[dict]] = {}
    for row in rows:
        key = (
            str(row.get("arm") or ""),
            int(row.get("snapshot_index") or 0),
            int(row.get("replicate") or 0),
        )
        rows_by_key.setdefault(key, []).append(row)

    missing_keys = sorted(expected_keys - set(rows_by_key))
    unexpected_keys = sorted(set(rows_by_key) - expected_keys)
    duplicate_keys = sorted(
        key for key, values in rows_by_key.items() if len(values) != 1
    )
    global_failures = [
        *(f"missing_row:{key}" for key in missing_keys),
        *(f"unexpected_row:{key}" for key in unexpected_keys),
        *(f"duplicate_row:{key}" for key in duplicate_keys),
    ]
    failures_by_arm = {arm: [] for arm in labels}
    walls_by_arm = {arm: [] for arm in labels}
    trigger_count_by_arm = {arm: 0 for arm in labels}
    native_engine_hashes: set[str] = set()
    source_binding_hashes: dict[int, set[str]] = {
        index: set() for index in range(1, len(snapshots) + 1)
    }
    required_binding_fields = (
        "branch_context",
        "full_cut_context",
        "instance",
        "mathematical_dual",
        "objective_mode",
    )

    def fail(arm: str, key: tuple[str, int, int], reason: str) -> None:
        failures_by_arm.setdefault(arm, []).append(
            f"{key[0]}/snapshot_{key[1]:02d}/"
            f"replicate_{key[2]:02d}:{reason}"
        )

    for key in sorted(expected_keys):
        arm, snapshot_index, replicate = key
        candidates = rows_by_key.get(key) or []
        if len(candidates) != 1:
            continue
        row = candidates[0]
        snapshot_row = snapshots[snapshot_index - 1]
        expected_order = _rotated_block_order(labels, replicate)
        if str(row.get("snapshot_role") or "") != str(
            snapshot_row.get("role") or ""
        ):
            fail(arm, key, "snapshot_role_mismatch")
        if str(row.get("blocked_schedule_id") or "") != schedule_id:
            fail(arm, key, "blocked_schedule_id_mismatch")
        if tuple(row.get("blocked_arm_order") or ()) != expected_order:
            fail(arm, key, "blocked_arm_order_mismatch")
        if int(row.get("blocked_arm_position") or 0) != (
            expected_order.index(arm) + 1
        ):
            fail(arm, key, "blocked_arm_position_mismatch")
        if int(row.get("returncode") or 0) != 0:
            fail(arm, key, "nonzero_returncode")

        output = Path(str(row.get("output") or ""))
        if not output.is_file():
            fail(arm, key, "output_missing")
            continue
        try:
            payload = json.loads(output.read_text(encoding="utf-8"))
        except Exception:
            fail(arm, key, "output_unreadable")
            continue
        if (
            str(payload.get("schema_version"))
            != "lunar_ice_bpc.proof_tail_snapshot_replay.v1"
            or not bool(payload.get("fresh_process_arm"))
        ):
            fail(arm, key, "replay_schema_or_fresh_process_mismatch")
        walls_by_arm[arm].append(
            float(payload.get("total_fresh_process_wall_sec") or 0.0)
        )

        expected_snapshot = _resolve(snapshot_row["path"])
        registered_file_hash = str(
            snapshot_row.get("sha256") or _sha256(expected_snapshot)
        )
        if _sha256(expected_snapshot) != registered_file_hash:
            fail(arm, key, "registered_snapshot_file_hash_mismatch")
        try:
            snapshot_payload = json.loads(
                expected_snapshot.read_text(encoding="utf-8")
            )
        except Exception:
            snapshot_payload = {}
        expected_snapshot_hash = str(
            snapshot_row.get("snapshot_hash")
            or snapshot_payload.get("snapshot_hash")
            or registered_file_hash
        )
        if Path(str(payload.get("source_snapshot") or "")).resolve() != (
            expected_snapshot.resolve()
        ):
            fail(arm, key, "source_snapshot_path_mismatch")
        if str(payload.get("source_snapshot_hash") or "") != (
            expected_snapshot_hash
        ):
            fail(arm, key, "source_snapshot_hash_mismatch")
        if str(payload.get("source_role") or "") != "mathematical_context":
            fail(arm, key, "source_role_mismatch")

        binding = dict(
            payload.get("same_mathematical_request_as_source") or {}
        )
        if any(not bool(binding.get(name)) for name in required_binding_fields):
            fail(arm, key, "mathematical_request_binding_mismatch")
        source_binding_hash = str(payload.get("source_binding_hash") or "")
        if not source_binding_hash:
            fail(arm, key, "source_binding_hash_missing")
        else:
            source_binding_hashes[snapshot_index].add(source_binding_hash)
        telemetry = dict(payload.get("proof_telemetry") or {})
        native_engine_hash = str(
            telemetry.get("native_engine_build_hash") or ""
        )
        if not native_engine_hash:
            fail(arm, key, "native_engine_build_hash_missing")
        else:
            native_engine_hashes.add(native_engine_hash)
        if bool(payload.get("labels_dropped")):
            fail(arm, key, "labels_dropped")

        triggered = bool(telemetry.get("negative_escape_triggered"))
        trigger_count_by_arm[arm] += int(triggered)
        if arm == "P0V4":
            if (
                bool(payload.get("exact_negative_escape_enabled"))
                or int(payload.get("exact_admission_batch_size") or 0) != 0
                or int(payload.get("exact_raw_negative_pool_size") or 0) != 0
                or bool(telemetry.get("negative_escape_enabled"))
                or triggered
            ):
                fail(arm, key, "control_negative_escape_contract_mismatch")
            continue

        expected_batch = int(
            arm_configs[arm]["admission_batch_size"]
        )
        expected_raw = int(arm_configs[arm]["raw_negative_pool_size"])
        if expected_raw != 4 * expected_batch:
            fail(arm, key, "configured_raw_pool_not_4k")
        if (
            not bool(payload.get("exact_negative_escape_enabled"))
            or not bool(telemetry.get("negative_escape_enabled"))
            or int(payload.get("exact_admission_batch_size") or 0)
            != expected_batch
            or int(payload.get("exact_raw_negative_pool_size") or 0)
            != expected_raw
        ):
            fail(arm, key, "escape_k_or_4k_contract_mismatch")
        if triggered:
            blockers = {
                str(value)
                for value in payload.get("certificate_blockers") or ()
            }
            if (
                str(payload.get("engine_status"))
                != "FOUND_NEGATIVE_PARTIAL"
                or str(
                    telemetry.get("negative_escape_termination_reason")
                )
                != "RAW_TRUE_NEGATIVE_POOL_REACHED"
                or int(telemetry.get("raw_unique_negative_count") or 0)
                != expected_raw
                or int(payload.get("column_count") or 0) != expected_raw
                or bool(payload.get("frontier_empty"))
                or bool(payload.get("search_exhaustive"))
                or bool(payload.get("can_enter_certificate_audit"))
                or bool(payload.get("can_certify_another_run"))
                or "native_exact_negative_escape_partial" not in blockers
            ):
                fail(arm, key, "partial_escape_fail_closed_contract_mismatch")
        elif str(payload.get("engine_status")) == "FOUND_NEGATIVE_PARTIAL":
            fail(arm, key, "partial_status_without_escape_trigger")
        elif not (
            bool(payload.get("search_exhaustive"))
            and bool(payload.get("frontier_empty"))
        ):
            fail(
                arm,
                key,
                "escape_neither_4k_partial_nor_exhaustive",
            )

    for snapshot_index, hashes in source_binding_hashes.items():
        if hashes and len(hashes) != 1:
            global_failures.append(
                f"snapshot_{snapshot_index:02d}:"
                "cross_arm_source_binding_hash_mismatch"
            )
    if len(native_engine_hashes) != 1:
        global_failures.append("cross_row_native_engine_build_hash_mismatch")

    summaries = {}
    for arm in labels:
        arm_rows = [
            row for row in rows if str(row.get("arm") or "") == arm
        ]
        failures = failures_by_arm[arm]
        summaries[arm] = {
            "row_count": len(arm_rows),
            "completed_count": len(walls_by_arm[arm]),
            "negative_escape_trigger_count": trigger_count_by_arm[arm],
            "correctness_redline_count": len(failures),
            "audit_failures": failures,
            "median_wall_time_sec": _median(walls_by_arm[arm]),
            "mean_wall_time_sec": _mean(walls_by_arm[arm]),
        }
    total_failure_count = len(global_failures) + sum(
        len(values) for values in failures_by_arm.values()
    )
    return {
        "schema_version": (
            "lunar_ice_bpc.p0v4_fixed_k_snapshot_summary.v2"
        ),
        "status": "PASS" if total_failure_count == 0 else "FAIL",
        "blocked_schedule_id": schedule_id,
        "expected_row_count": len(expected_keys),
        "observed_row_count": len(rows),
        "missing_row_count": len(missing_keys),
        "unexpected_row_count": len(unexpected_keys),
        "duplicate_row_count": len(duplicate_keys),
        "native_engine_build_hashes": sorted(native_engine_hashes),
        "global_audit_failures": global_failures,
        "total_audit_failure_count": total_failure_count,
        "downstream_fixed_k_selection_authorized": (
            total_failure_count == 0
        ),
        "arms": summaries,
    }


def _instance_key(path: Path) -> str:
    stem = path.stem
    marker = "_logical_graph"
    return stem[: -len(marker)] if stem.endswith(marker) else stem


def _optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric


def _mean(values: list[float] | tuple[float, ...]) -> float:
    return (
        0.0
        if not values
        else sum(float(value) for value in values) / len(values)
    )


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return 0.5 * (ordered[middle - 1] + ordered[middle])


def _geometric_mean(values: list[float]) -> float:
    if not values:
        return 1.0e12
    return exp(
        sum(log(max(1.0e-12, float(value))) for value in values)
        / len(values)
    )


def _evenly_spaced_rows(
    rows: list[dict], count: int
) -> list[dict]:
    target = max(0, int(count))
    if target == 0:
        return []
    if len(rows) <= target:
        return list(rows)
    if target == 1:
        return [rows[len(rows) // 2]]
    indices = [
        round(index * (len(rows) - 1) / (target - 1))
        for index in range(target)
    ]
    return [rows[index] for index in indices]


def _payload_hash(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def _validate_experiment(config: dict, path: Path) -> None:
    if (
        str(config.get("schema_version"))
        != "lunar_ice_bpc.p0v4_diverse_escape_oracle.v1"
    ):
        raise SystemExit(f"experiment schema mismatch: {path}")
    for arm, row in config.get("arms", {}).items():
        batch = int(row["admission_batch_size"])
        raw = int(row["raw_negative_pool_size"])
        if arm != f"E{batch}" or raw != 4 * batch:
            raise SystemExit(f"invalid fixed escape arm {arm}")


def _verify_control(config: dict) -> None:
    for path_key, hash_key in (
        ("frozen_control_config", "frozen_control_config_sha256"),
        ("frozen_control_manifest", "frozen_control_manifest_sha256"),
    ):
        path = _resolve(config[path_key])
        if not path.is_file() or _sha256(path) != str(config[hash_key]):
            raise SystemExit(f"frozen P0V4 drift: {path}")
    verifier = (
        _resolve(config["frozen_control_manifest"]).parent
        / "verify_freeze.py"
    )
    completed = subprocess.run(
        [sys.executable, str(verifier)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise SystemExit(
            "P0V4 freeze verification failed: " + completed.stderr
        )


def _selected_arms(arm: str | None) -> tuple[str, ...]:
    return (str(arm),) if arm else ("E64", "E128", "E256")


def _execution_env() -> dict[str, str]:
    env = dict(os.environ)
    pythonpath = [
        str(ROOT / "src"),
        str(ROOT / "build/native-spprc-memory-opt-v2"),
    ]
    if env.get("PYTHONPATH"):
        pythonpath.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(pythonpath)
    return env


def _resolve(value: object) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else ROOT / path


def _load_yaml(path: Path) -> dict:
    return dict(yaml.safe_load(path.read_text(encoding="utf-8")) or {})


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Bounded scale30/50 reachable-oracle gate for P0V5 QG2."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.qg2_admission_supervision import (  # noqa: E402
    QG2_QUEUE_ACTION_SURFACE_V1,
    QG2_SUPERVISION_SCHEMA_V2,
)

REPLAY = ROOT / "scripts/replay_p0v5_qg2_label_state_snapshot.py"
FIT = ROOT / "scripts/fit_p0v5_qo2_leaked_label_state_oracle.py"
SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
REPLAY_SCHEMA = "lunar_ice_bpc.p0v5_qg2_snapshot_replay.v3"
POTENTIAL_SCHEMA = "lunar_ice_bpc.p0v5_qg2_label_state_potential.v2"
BUCKETS = (1.0e-4, 3.0e-4, 1.0e-3)
RANDOM_SEEDS = (61635, 91267, 170141)
FORMAL_END_TO_END_GAIN_TARGET = 0.05


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-index", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-contexts", type=int, default=300)
    parser.add_argument("--max-contexts-per-scale", type=int, default=150)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--scale30-wall-sec", type=float, default=180.0)
    parser.add_argument("--scale50-wall-sec", type=float, default=300.0)
    parser.add_argument("--memory-limit-gb", type=float, default=10.867)
    parser.add_argument(
        "--native-build-dir",
        default="build/native-spprc-bidirectional-feasibility-v1",
    )
    parser.add_argument("--execution-freeze")
    parser.add_argument(
        "--instance-split",
        help="optional pre-outcome split used only for coverage stratification",
    )
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()

    if int(args.max_contexts) > 300:
        raise SystemExit("QG2 oracle context budget cannot exceed 300")
    if int(args.max_contexts_per_scale) > 150:
        raise SystemExit("QG2 per-scale context budget cannot exceed 150")
    state_index = _resolve(args.state_index)
    output_dir = _resolve(args.output_dir)
    output_path = _resolve(args.output)
    execution_freeze = (
        None
        if not args.execution_freeze
        else _resolve(args.execution_freeze)
    )
    split_path = (
        None if not args.instance_split else _resolve(args.instance_split)
    )
    split_assignments = (
        None if split_path is None else _load_instance_split(split_path)
    )
    if execution_freeze is None and not args.preflight_only:
        raise SystemExit(
            "QG2 formal bounded oracle requires --execution-freeze"
        )
    if execution_freeze is not None:
        freeze_payload = _validate_execution_freeze(execution_freeze)
        if str(freeze_payload.get("source_state_index_sha256") or "") != (
            _sha256(state_index)
        ):
            raise SystemExit("QG2 execution freeze state-index mismatch")
        if split_path is not None and (
            str(freeze_payload.get("instance_split_sha256") or "")
            != _sha256(split_path)
        ):
            raise SystemExit("QG2 execution freeze instance-split mismatch")
    output_dir.mkdir(parents=True, exist_ok=True)
    terminal_stop = output_dir / "proof_tail_gat_terminal_stop.json"
    if terminal_stop.exists():
        terminal = _load(terminal_stop)
        raise SystemExit(
            "QG2 bounded oracle is terminally stopped: "
            f"{terminal.get('reason') or '300-context gate failure'}"
        )
    rows = _state_rows(_load(state_index))
    if split_assignments is not None:
        rows = _bind_preoutcome_partitions(rows, split_assignments)
    selected = _bounded_selection(
        rows,
        maximum=max(1, int(args.max_contexts)),
        per_scale=max(1, int(args.max_contexts_per_scale)),
    )
    coverage = _coverage(selected)
    preflight_pass = _preflight_coverage_passes(
        coverage, require_partitions=split_assignments is not None
    )
    if args.preflight_only or not preflight_pass:
        payload = {
            "schema_version": SCHEMA,
            "development_only": True,
            "deployable": False,
            "bounded_context_limit": int(args.max_contexts),
            "bounded_context_limit_per_scale": int(args.max_contexts_per_scale),
            "supervision_schema_version": QG2_SUPERVISION_SCHEMA_V2,
            "queue_action_surface": QG2_QUEUE_ACTION_SURFACE_V1,
            "source_state_index": str(state_index),
            "source_state_index_sha256": _sha256(state_index),
            "instance_split": None if split_path is None else str(split_path),
            "instance_split_sha256": (
                None if split_path is None else _sha256(split_path)
            ),
            "execution_freeze": (
                None if execution_freeze is None else str(execution_freeze)
            ),
            "execution_freeze_sha256": (
                None
                if execution_freeze is None
                else _sha256(execution_freeze)
            ),
            "coverage": coverage,
            "status": (
                "PREFLIGHT_ONLY"
                if args.preflight_only and preflight_pass
                else "INSUFFICIENT_SNAPSHOT_COVERAGE"
            ),
            "oracle_gate": {
                "passed": False,
                "reason": (
                    "execution_not_requested"
                    if preflight_pass
                    else (
                        "scale30_and_scale50_each_require_20_contexts_from_10_instances"
                        "_and_total_contexts_must_reach_50"
                    )
                ),
                "context_count": len(selected),
            },
            "training_permitted": False,
        }
        _write(output_path, payload)
        print(json.dumps(payload["oracle_gate"], sort_keys=True))
        return 0 if args.preflight_only else 2

    native_build = _resolve(args.native_build_dir)
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{native_build}"
    initial_rows = []
    compliant = []
    for index, row in enumerate(selected):
        context_dir = output_dir / f"{row['scale']}_{row['state_hash'][:16]}"
        context_dir.mkdir(parents=True, exist_ok=True)
        wall_limit = (
            float(args.scale30_wall_sec)
            if int(row["scale"]) == 30
            else float(args.scale50_wall_sec)
        )
        q0_trace = context_dir / "q0_trace.json"
        _replay(
            row=row,
            target=q0_trace,
            policy="Q0",
            wall_limit=wall_limit,
            memory_limit=float(args.memory_limit_gb),
            env=env,
            label_trace=True,
        )
        q0_trace_payload = _load(q0_trace)
        if not _complete_future_trace(q0_trace_payload):
            initial_rows.append({
                **_identity(row),
                "compliant_context": False,
                "exclusion_reason": "q0_future_trace_not_complete",
                "q0_trace_path": str(q0_trace),
            })
            continue
        potential = context_dir / "qo2_leaked_potential.json"
        _run([
            sys.executable,
            str(FIT),
            "--instance", row["instance_path"],
            "--q0-trace", str(q0_trace),
            "--output", str(potential),
        ], env=env)
        potential_payload = _load(potential)
        if (
            potential_payload.get("schema_version") != POTENTIAL_SCHEMA
            or potential_payload.get("supervision_schema_version")
            != QG2_SUPERVISION_SCHEMA_V2
            or potential_payload.get("queue_action_surface")
            != QG2_QUEUE_ACTION_SURFACE_V1
            or int(
                dict(potential_payload.get("supervision") or {}).get(
                    "action_reachable_pair_count"
                )
                or 0
            )
            != int(potential_payload.get("training_pair_count") or 0)
        ):
            raise SystemExit(
                "QO2 fitted potential action-surface contract mismatch"
            )
        # The trace replay is training-data collection, not a matched timing
        # arm.  Replay a literal Q0 without trace so Q0/QO2 initial screening
        # has identical instrumentation overhead.
        q0_initial = context_dir / "q0_initial.json"
        _replay(
            row=row,
            target=q0_initial,
            policy="Q0",
            wall_limit=wall_limit,
            memory_limit=float(args.memory_limit_gb),
            env=env,
        )
        q0 = _load(q0_initial)
        arms: dict[str, dict] = {"Q0": q0}
        for policy in ("QD1", "QB1"):
            target = context_dir / f"{policy.lower()}_initial.json"
            _replay(
                row=row, target=target, policy=policy,
                wall_limit=wall_limit,
                memory_limit=float(args.memory_limit_gb), env=env,
            )
            arms[policy] = _load(target)
        for seed in RANDOM_SEEDS:
            key = f"Random_{seed}"
            target = context_dir / f"random_{seed}_initial.json"
            _replay(
                row=row, target=target, policy="QG2",
                wall_limit=wall_limit,
                memory_limit=float(args.memory_limit_gb), env=env,
                random_seed=seed, bucket=1.0e-3,
            )
            arms[key] = _load(target)
        for bucket in BUCKETS:
            key = f"QO2_{bucket:g}"
            target = context_dir / f"qo2_{bucket:g}_initial.json"
            _replay(
                row=row, target=target, policy="QG2",
                wall_limit=wall_limit,
                memory_limit=float(args.memory_limit_gb), env=env,
                potential=potential, bucket=bucket,
            )
            arms[key] = _load(target)
        safe = all(_ordering_safe(q0, arm) for arm in arms.values())
        q0_wall = _effective_wall(q0, wall_limit)
        q0_timing = _timing_breakdown(q0)
        bucket_ratios = {
            str(bucket): _effective_wall(
                arms[f"QO2_{bucket:g}"], wall_limit
            ) / q0_wall
            for bucket in BUCKETS
        }
        qo2_walls = {
            str(bucket): _effective_wall(
                arms[f"QO2_{bucket:g}"], wall_limit
            )
            for bucket in BUCKETS
        }
        qo2_timing = {
            str(bucket): _timing_breakdown(arms[f"QO2_{bucket:g}"])
            for bucket in BUCKETS
        }
        qo2_exhaustive = {
            str(bucket): bool(arms[f"QO2_{bucket:g}"].get("search_exhaustive"))
            for bucket in BUCKETS
        }
        qo2_milestone_reached = {
            str(bucket): bool(
                arms[f"QO2_{bucket:g}"].get("milestone_reached")
            )
            for bucket in BUCKETS
        }
        initial = {
            **_identity(row),
            "compliant_context": True,
            "all_initial_arms_safe": safe,
            "q0_path": str(q0_initial),
            "q0_trace_path": str(q0_trace),
            "q0_trace_excluded_from_timing": True,
            "q0_search_exhaustive": bool(q0.get("search_exhaustive")),
            "q0_milestone_reached": bool(q0.get("milestone_reached")),
            "q0_milestone_kind": str(q0.get("milestone_kind") or ""),
            "qo2_potential_path": str(potential),
            "qo2_supervision": dict(
                potential_payload.get("supervision") or {}
            ),
            "q0_wall_sec": q0_wall,
            "q0_timing": q0_timing,
            "q0_queue_action_headroom": _queue_action_headroom(
                q0,
                target_gain=FORMAL_END_TO_END_GAIN_TARGET,
            ),
            "bucket_ratios": bucket_ratios,
            "qo2_wall_sec_by_bucket": qo2_walls,
            "qo2_timing_by_bucket": qo2_timing,
            "qo2_search_exhaustive_by_bucket": qo2_exhaustive,
            "qo2_milestone_reached_by_bucket": qo2_milestone_reached,
            "qo2_milestone_kind_by_bucket": {
                str(bucket): str(
                    arms[f"QO2_{bucket:g}"].get("milestone_kind") or ""
                )
                for bucket in BUCKETS
            },
            "arm_paths": {
                key: str(context_dir / (
                    f"{key.lower()}_initial.json"
                    if key in {"QD1", "QB1"}
                    else f"random_{key.split('_')[1]}_initial.json"
                    if key.startswith("Random_")
                    else f"qo2_{key.split('_')[1]}_initial.json"
                ))
                for key in arms if key != "Q0"
            },
        }
        initial_rows.append(initial)
        compliant.append((row, context_dir, potential, initial, wall_limit))
        print(json.dumps({
            "initial_completed": len(initial_rows),
            "scale": row["scale"],
            "state": row["state_hash"][:16],
            "bucket_ratios": bucket_ratios,
            "safe": safe,
        }, sort_keys=True), flush=True)

    frozen_bucket = _select_bucket(
        initial_rows,
        partition="train" if split_assignments is not None else None,
    )
    replicate_rows = []
    for context_index, (row, context_dir, potential, initial, wall_limit) in enumerate(compliant):
        if not initial["all_initial_arms_safe"]:
            continue
        if float(initial["bucket_ratios"][str(frozen_bucket)]) >= 1.0:
            continue
        for repeat in range(1, max(3, int(args.repeats)) + 1):
            order = ["Q0", "QO2"]
            random.Random(20260801 + context_index * 101 + repeat).shuffle(order)
            outputs = {}
            output_paths = {}
            for arm in order:
                target = context_dir / (
                    f"{arm.lower()}_{frozen_bucket:g}_rep{repeat}.json"
                )
                _replay(
                    row=row,
                    target=target,
                    policy="Q0" if arm == "Q0" else "QG2",
                    wall_limit=wall_limit,
                    memory_limit=float(args.memory_limit_gb),
                    env=env,
                    potential=None if arm == "Q0" else potential,
                    bucket=frozen_bucket,
                    repeat=repeat,
                )
                outputs[arm] = _load(target)
                output_paths[arm] = target
            safe = _ordering_safe(outputs["Q0"], outputs["QO2"])
            q0_wall = _effective_wall(outputs["Q0"], wall_limit)
            qo2_wall = _effective_wall(outputs["QO2"], wall_limit)
            replicate_rows.append({
                **_identity(row),
                "repeat": repeat,
                "blocked_order": order,
                "q0_wall_sec": q0_wall,
                "qo2_wall_sec": qo2_wall,
                "q0_timing": _timing_breakdown(outputs["Q0"]),
                "qo2_timing": _timing_breakdown(outputs["QO2"]),
                "ratio": qo2_wall / q0_wall,
                "saved_wall_sec": max(0.0, q0_wall - qo2_wall),
                "q0_milestone_reached": bool(
                    outputs["Q0"].get("milestone_reached")
                ),
                "qo2_milestone_reached": bool(
                    outputs["QO2"].get("milestone_reached")
                ),
                "q0_milestone_kind": str(
                    outputs["Q0"].get("milestone_kind") or ""
                ),
                "qo2_milestone_kind": str(
                    outputs["QO2"].get("milestone_kind") or ""
                ),
                "safe": safe,
                "q0_path": str(output_paths["Q0"]),
                "qo2_path": str(output_paths["QO2"]),
            })

    context_rows = _aggregate_contexts(
        initial_rows,
        replicate_rows,
        frozen_bucket,
    )
    queue_action_headroom = _summarize_queue_action_headroom(
        initial_rows,
        target_gain=FORMAL_END_TO_END_GAIN_TARGET,
    )
    oracle_gate = _gate(
        context_rows,
        initial_rows,
        frozen_bucket,
        queue_action_headroom=queue_action_headroom,
    )
    bounded_budget_exhausted = bool(
        int(args.max_contexts) == 300 and len(selected) >= 300
    )
    payload = {
        "schema_version": SCHEMA,
        "development_only": True,
        "deployable": False,
        "bounded_context_limit": int(args.max_contexts),
        "bounded_context_limit_per_scale": int(args.max_contexts_per_scale),
        "supervision_schema_version": QG2_SUPERVISION_SCHEMA_V2,
        "queue_action_surface": QG2_QUEUE_ACTION_SURFACE_V1,
        "source_state_index": str(state_index),
        "source_state_index_sha256": _sha256(state_index),
        "instance_split": None if split_path is None else str(split_path),
        "instance_split_sha256": (
            None if split_path is None else _sha256(split_path)
        ),
        "execution_freeze": str(execution_freeze),
        "execution_freeze_sha256": _sha256(execution_freeze),
        "coverage": coverage,
        "timing_objective": "min_admission_milestone_wall_sec",
        "raw_negative_milestone_role": "diagnostic_only",
        "queue_action_headroom": queue_action_headroom,
        "frozen_guidance_bucket_width": frozen_bucket,
        "initial_rows": initial_rows,
        "replicate_rows": replicate_rows,
        "context_rows": context_rows,
        "oracle_gate": oracle_gate,
        "training_permitted": bool(oracle_gate["passed"]),
        "status": (
            "PASSED"
            if oracle_gate["passed"]
            else "TERMINATED_AT_ORACLE_GATE"
            if bounded_budget_exhausted
            else "ORACLE_GATE_FAILED_WITH_BUDGET_REMAINING"
        ),
    }
    _write(output_path, payload)
    if not oracle_gate["passed"] and bounded_budget_exhausted:
        _write(terminal_stop, {
            "schema_version": "lunar_ice_bpc.p0v5_qg2_terminal_stop.v1",
            "development_only": True,
            "deployable": False,
            "reason": "bounded_300_context_oracle_gate_failed",
            "oracle_summary": str(output_path),
            "oracle_summary_sha256": _sha256(output_path),
            "source_state_index": str(state_index),
            "source_state_index_sha256": _sha256(state_index),
            "execution_freeze": str(execution_freeze),
            "execution_freeze_sha256": _sha256(execution_freeze),
            "model_training_permitted": False,
            "additional_sampling_permitted": False,
        })
    print(json.dumps(oracle_gate, sort_keys=True))
    return 0 if oracle_gate["passed"] else 2


def _state_rows(payload: dict) -> list[dict]:
    _validate_state_index_payload(payload)
    candidates = payload.get("rows") or payload.get("states") or ()
    rows = []
    for raw in candidates:
        row = dict(raw)
        scale = int(row.get("scale") or 0)
        if scale not in {30, 50}:
            continue
        instance_path = str(row.get("instance_path") or "")
        snapshot_path = str(row.get("snapshot_path") or row.get("source_snapshot_path") or "")
        state_hash = str(row.get("source_state_hash") or row.get("state_hash") or "")
        instance_hash = str(row.get("instance_content_hash") or row.get("instance_hash") or "")
        if not (
            instance_path and snapshot_path and state_hash and instance_hash
        ):
            raise ValueError("QG2 state index row has incomplete identity")
        if instance_path and snapshot_path and state_hash and instance_hash:
            resolved_snapshot = _resolve(snapshot_path)
            try:
                snapshot = _load(resolved_snapshot)
            except Exception as exc:
                raise ValueError(
                    f"QG2 state index snapshot cannot be read: {resolved_snapshot}"
                ) from exc
            source_backend_id = str(row.get("source_backend_id") or "")
            source_engine_hash = str(row.get("source_engine_hash") or "")
            source_config_hash = str(row.get("source_config_hash") or "")
            source_action_policy_hash = str(
                row.get("source_exact_action_policy_hash") or ""
            )
            if (
                snapshot.get("schema_version")
                != "lunar_ice_bpc.p0v5_proof_tail_fallback_snapshot.v2"
                or not bool(snapshot.get("proof_tail_fallback_context"))
                or snapshot.get("active_task_sets") is None
                or snapshot.get("active_column_signature_hashes") is None
                or len(snapshot.get("active_column_signature_hashes") or ())
                != int(snapshot.get("active_column_count") or 0)
                or str(snapshot.get("state_hash") or "") != state_hash
                or str(snapshot.get("instance_content_hash") or "")
                != instance_hash
                or not source_backend_id
                or not source_engine_hash
                or source_engine_hash
                != str(snapshot.get("engine_hash") or "")
                or not source_config_hash
                or source_config_hash
                != str(snapshot.get("config_hash") or "")
                or not source_action_policy_hash
                or source_action_policy_hash
                != str(snapshot.get("exact_action_policy_hash") or "")
                or str(snapshot.get("base_proof_queue_policy_id") or "")
                != "Q0"
                or str(row.get("snapshot_sha256") or "")
                != _sha256(resolved_snapshot)
            ):
                raise ValueError(
                    f"QG2 state index binding mismatch: {resolved_snapshot}"
                )
            unhashed = dict(snapshot)
            unhashed.pop("state_hash", None)
            if _stable_hash(unhashed) != state_hash:
                continue
            rows.append({
                "scale": scale,
                "instance_id": str(row.get("instance_id") or instance_hash[:16]),
                "instance_hash": instance_hash,
                "state_hash": state_hash,
                "instance_path": str(_resolve(instance_path)),
                "snapshot_path": str(resolved_snapshot),
                "source_backend_id": source_backend_id,
                "source_engine_hash": source_engine_hash,
                "source_config_hash": source_config_hash,
                "source_exact_action_policy_hash": (
                    source_action_policy_hash
                ),
                "round": _optional_int(row.get("round")),
                "pricing_lifecycle_scope": str(
                    row.get("pricing_lifecycle_scope") or ""
                ),
                "branch_pair_count": int(
                    row.get("branch_pair_count") or 0
                ),
                "active_cut_count": int(
                    row.get("active_cut_count") or 0
                ),
                "previous_q0_wall_stratum": str(
                    row.get("previous_q0_wall_stratum") or "missing"
                ),
            })
    unique = {row["state_hash"]: row for row in rows}
    if len(unique) != len(rows):
        raise ValueError("QG2 state index contains duplicate state hashes")
    return sorted(unique.values(), key=lambda row: (row["scale"], row["instance_hash"], row["state_hash"]))


def _load_instance_split(path: Path) -> dict[str, str]:
    payload = _load(path)
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_realmap_v4_instance_split.v1"
    ) or not bool(payload.get("frozen_before_matched_outcomes")):
        raise SystemExit("QG2 Oracle instance split is not pre-outcome frozen")
    assignments = {
        str(key): str(value)
        for key, value in dict(payload.get("assignments") or {}).items()
    }
    if not assignments or any(
        value not in {"train", "calibration", "heldout"}
        for value in assignments.values()
    ):
        raise SystemExit("QG2 Oracle instance split assignments are invalid")
    counts = dict(payload.get("partition_counts_by_scale") or {})
    expected = {
        "30": {"train": 12, "calibration": 4, "heldout": 4},
        "50": {"train": 12, "calibration": 4, "heldout": 4},
    }
    if counts != expected:
        raise SystemExit("QG2 Oracle real-map split counts drifted")
    return assignments


def _bind_preoutcome_partitions(rows, assignments):
    result = []
    missing = []
    for row in rows:
        instance = str(row["instance_hash"])
        if instance not in assignments:
            missing.append(instance)
            continue
        result.append({**row, "partition": assignments[instance]})
    if missing:
        raise SystemExit(
            "QG2 Oracle state index contains instances outside frozen split"
        )
    return result


def _validate_state_index_payload(payload: dict) -> None:
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_fallback_snapshot_index.v2"
    ):
        raise ValueError("QG2 state index schema mismatch")
    if not bool(payload.get("development_only")) or bool(
        payload.get("deployable")
    ):
        raise ValueError("QG2 state index safety contract mismatch")
    if int(payload.get("excluded_count") or 0) != 0:
        raise ValueError("QG2 state index contains excluded snapshots")
    if not bool(payload.get("exact_action_policy_hash_required")):
        raise ValueError("QG2 state index lacks strict action-policy binding")
    freeze_path = str(payload.get("collection_freeze") or "")
    freeze_hash = str(payload.get("collection_freeze_sha256") or "")
    if not freeze_path or not freeze_hash:
        raise ValueError("QG2 state index lacks collection freeze binding")
    resolved_freeze = _resolve(freeze_path)
    if not resolved_freeze.is_file() or _sha256(resolved_freeze) != freeze_hash:
        raise ValueError("QG2 collection freeze hash drift")
    collection_freeze = _load(resolved_freeze)
    required_by_scale = dict(collection_freeze.get(
        "required_exact_action_policy_hashes_by_scale"
    ) or {})
    expected_by_scale = dict(payload.get(
        "expected_exact_action_policy_hashes_by_scale"
    ) or {})
    observed = {
        str(value)
        for value in payload.get("observed_exact_action_policy_hashes") or ()
        if str(value)
    }
    if (
        set(required_by_scale) != {"30", "50"}
        or expected_by_scale != required_by_scale
        or observed != set(required_by_scale.values())
    ):
        raise ValueError(
            "QG2 state index scale-aware action-policy binding mismatch"
        )


def _bounded_selection(rows: list[dict], *, maximum: int, per_scale: int):
    selected = []
    for scale in (30, 50):
        scale_rows = [row for row in rows if row["scale"] == scale]
        # First make a deterministic instance-round-robin queue inside every
        # pre-action stratum, then round-robin those stratum queues.  Sorting
        # the combined ``(stratum, instance)`` key would exhaust the
        # lexicographically first stratum before a rare tree/branch-cut
        # stratum receives a slot when the physical pool exceeds the Oracle
        # budget.  Outcome strata remain unavailable until fresh replay and
        # are never used for snapshot selection.
        groups: dict[str, dict[str, list[dict]]] = {}
        for row in scale_rows:
            stratum = (
                f"{str(row.get('partition') or 'unassigned')}|"
                f"{_preaction_stratum(row)}"
            )
            instance = str(row["instance_hash"])
            groups.setdefault(stratum, {}).setdefault(instance, []).append(row)
        stratum_queues: dict[str, list[dict]] = {}
        for stratum, instance_groups in groups.items():
            for values in instance_groups.values():
                values.sort(key=lambda row: row["state_hash"])
            queue = []
            while instance_groups:
                for instance in sorted(tuple(instance_groups)):
                    queue.append(instance_groups[instance].pop(0))
                    if not instance_groups[instance]:
                        instance_groups.pop(instance, None)
            stratum_queues[stratum] = queue
        scale_selected = 0
        while stratum_queues and scale_selected < per_scale:
            progressed = False
            for stratum in sorted(tuple(stratum_queues)):
                if stratum_queues[stratum]:
                    selected.append(stratum_queues[stratum].pop(0))
                    scale_selected += 1
                    progressed = True
                if not stratum_queues[stratum]:
                    stratum_queues.pop(stratum, None)
                if scale_selected >= per_scale:
                    break
            if not progressed:
                break
    return selected[:maximum]


def _coverage(rows: list[dict]):
    return {
        str(scale): {
            "context_count": sum(row["scale"] == scale for row in rows),
            "instance_count": len({row["instance_hash"] for row in rows if row["scale"] == scale}),
            "preaction_stratum_counts": _counts(
                _preaction_stratum(row)
                for row in rows if row["scale"] == scale
            ),
            "partition_context_counts": _counts(
                str(row.get("partition") or "unassigned")
                for row in rows if row["scale"] == scale
            ),
            "partition_instance_counts": {
                partition: len({
                    row["instance_hash"] for row in rows
                    if row["scale"] == scale
                    and str(row.get("partition") or "unassigned") == partition
                })
                for partition in ("train", "calibration", "heldout")
            },
        }
        for scale in (30, 50)
    }


def _preflight_coverage_passes(
    coverage: dict, *, require_partitions: bool = False
) -> bool:
    ordinary = bool(
        all(
            int(coverage[str(scale)]["context_count"]) >= 20
            and int(coverage[str(scale)]["instance_count"]) >= 10
            for scale in (30, 50)
        )
        and sum(
            int(coverage[str(scale)]["context_count"])
            for scale in (30, 50)
        ) >= 50
    )
    if not ordinary or not require_partitions:
        return ordinary
    return all(
        int(coverage[str(scale)]["partition_context_counts"].get(
            "train", 0
        )) >= 10
        and int(coverage[str(scale)]["partition_instance_counts"].get(
            "train", 0
        )) >= 6
        and all(
            int(coverage[str(scale)]["partition_context_counts"].get(
                partition, 0
            )) >= 4
            and int(coverage[str(scale)]["partition_instance_counts"].get(
                partition, 0
            )) >= 2
            for partition in ("calibration", "heldout")
        )
        for scale in (30, 50)
    )


def _preaction_stratum(row: dict) -> str:
    scope = (
        "root"
        if str(row.get("pricing_lifecycle_scope") or "") == "root_cg"
        else "tree"
    )
    structural = (
        "branch_cut"
        if int(row.get("branch_pair_count") or 0) > 0
        or int(row.get("active_cut_count") or 0) > 0
        else "plain"
    )
    round_index = int(row.get("round") or 0)
    round_bucket = (
        "r0_9" if round_index < 10
        else "r10_29" if round_index < 30
        else "r30_plus"
    )
    previous = str(row.get("previous_q0_wall_stratum") or "missing")
    return f"{scope}:{structural}:{round_bucket}:{previous}"


def _replay(*, row, target, policy, wall_limit, memory_limit, env, potential=None, random_seed=None, bucket=1.0e-3, repeat=1, label_trace=False):
    expected_potential_sha256 = (
        _sha256(potential) if potential is not None else ""
    )
    if target.exists():
        existing = _load(target)
        telemetry = dict(existing.get("proof_telemetry") or {})
        if (
            existing.get("schema_version") != REPLAY_SCHEMA
            or str(existing.get("source_state_hash") or "")
            != str(row["state_hash"])
            or str(existing.get("policy") or "") != str(policy)
            or int(existing.get("repeat_index") or 0) != int(repeat)
            or str(existing.get("source_backend_id") or "")
            != str(
                row.get("source_backend_id")
                or "native_rcspp_bidirectional_root_partial_hybrid_v3"
            )
            or str(existing.get("source_engine_hash") or "")
            != str(row.get("source_engine_hash") or "")
            or str(existing.get("source_config_hash") or "")
            != str(row.get("source_config_hash") or "")
            or str(existing.get("source_exact_action_policy_hash") or "")
            != str(row.get("source_exact_action_policy_hash") or "")
            or float(existing.get("guidance_bucket_width") or 0.0)
            != float(bucket)
            or float(existing.get("requested_wall_time_limit_sec") or 0.0)
            != float(wall_limit)
            or float(existing.get("requested_memory_limit_gb") or 0.0)
            != float(memory_limit)
            or bool(existing.get("requested_label_trace"))
            != bool(label_trace)
            or str(existing.get("potential_file_sha256") or "")
            != expected_potential_sha256
            or existing.get("random_seed")
            != (
                int(random_seed)
                if random_seed is not None
                else None
            )
            or (
                label_trace
                and not bool(
                    telemetry.get("proof_queue_label_trace_enabled")
                )
            )
        ):
            raise SystemExit(
                f"stale or mismatched QG2 replay artifact: {target}"
            )
        return
    command = [
        sys.executable, str(REPLAY),
        "--instance", row["instance_path"],
        "--snapshot", row["snapshot_path"],
        "--output", str(target),
        "--policy", policy,
        "--repeat-index", str(repeat),
        "--wall-time-limit-sec", str(wall_limit),
        "--memory-limit-gb", str(memory_limit),
        "--guidance-bucket-width", str(bucket),
        "--source-backend-id", str(
            row.get("source_backend_id")
            or "native_rcspp_bidirectional_root_partial_hybrid_v3"
        ),
    ]
    if potential is not None:
        command.extend(["--potential", str(potential)])
    if random_seed is not None:
        command.extend(["--random-seed", str(random_seed)])
    if label_trace:
        command.append("--label-trace")
    _run(command, env=env)


def _run(command, *, env):
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def _complete_future_trace(row: dict) -> bool:
    telemetry = dict(row.get("proof_telemetry") or {})
    return bool(
        row.get("milestone_reached")
        and not row.get("labels_dropped")
        and telemetry.get("proof_queue_label_trace_enabled")
        and telemetry.get("proof_queue_label_state_trace")
    )


def _ordering_safe(control: dict, arm: dict) -> bool:
    left = dict(control.get("proof_telemetry") or {})
    right = dict(arm.get("proof_telemetry") or {})
    universe = all(
        left.get(key) == right.get(key)
        for key in (
            "legal_action_universe_hash_before_sort",
            "legal_arc_universe_hash_before_sort",
        )
    )
    no_drop = all(
        int(right.get(key) or 0) == 0
        for key in (
            "guidance_filter_count", "guidance_arc_drop_count",
            "guidance_label_drop_count", "guidance_branch_pair_drop_count",
        )
    )
    if control.get("search_exhaustive") and arm.get("search_exhaustive"):
        exact = _exact_match(control, arm)
    else:
        exact = True
    return bool(universe and no_drop and not arm.get("labels_dropped") and exact)


def _exact_match(left: dict, right: dict) -> bool:
    if left.get("global_min_rc") is not None and right.get("global_min_rc") is not None:
        return abs(float(left["global_min_rc"]) - float(right["global_min_rc"])) <= 2.0e-6
    if left.get("proved_no_rc_below") is not None and right.get("proved_no_rc_below") is not None:
        return abs(float(left["proved_no_rc_below"]) - float(right["proved_no_rc_below"])) <= 1.0e-12
    return False


def _effective_wall(row: dict, budget: float) -> float:
    measured = max(
        1.0e-9,
        float(
            row.get("admission_milestone_wall_sec")
            or row.get("milestone_wall_sec")
            or row.get("total_fresh_process_wall_sec")
            or 0.0
        ),
    )
    return measured if row.get("milestone_reached") else max(
        measured, float(budget)
    )


def _timing_breakdown(row: dict) -> dict:
    return {
        "t_raw_sec": row.get("raw_negative_milestone_wall_sec"),
        "t_first_addable_sec": row.get(
            "first_addable_negative_wall_sec"
        ),
        "t_selected_batch_last_discovery_sec": row.get(
            "admission_batch_last_selected_native_discovery_wall_sec"
        ),
        "t_admission_sec": row.get("admission_milestone_wall_sec"),
        "native_search_sec": row.get("native_search_wall_sec"),
        "backend_reconstruction_audit_sec": row.get(
            "backend_reconstruction_audit_wall_sec"
        ),
        "true_rc_reaudit_sec": row.get("true_rc_reaudit_wall_sec"),
        "diversity_selector_sec": row.get("diversity_selector_wall_sec"),
        "master_entry_audit_sec": row.get(
            "master_entry_audit_wall_sec"
        ),
        "t_audit_sec": row.get("admission_audit_wall_sec"),
        "t_selector_sec": row.get("admission_selector_wall_sec"),
        "unattributed_sec": row.get("admission_unattributed_wall_sec"),
        "post_native_fixed_pipeline_sec": row.get(
            "post_native_fixed_pipeline_wall_sec"
        ),
        "post_native_fixed_pipeline_ratio": row.get(
            "post_native_fixed_pipeline_ratio"
        ),
        "raw_to_native_harvest_sec": row.get(
            "raw_to_native_harvest_wall_sec"
        ),
        "raw_to_native_harvest_ratio": row.get(
            "raw_to_native_harvest_ratio"
        ),
    }


def _queue_action_headroom(
    row: dict,
    *,
    target_gain: float = FORMAL_END_TO_END_GAIN_TARGET,
) -> dict:
    """Decompose the admission milestone into queue-visible and fixed work.

    This is an Amdahl-style mechanism diagnostic, not an oracle substitute.
    It assumes the work after Native returns is invariant under queue ordering;
    the matched fresh-process QO2/Q0 replay remains the training gate.
    """

    milestone_kind = str(row.get("milestone_kind") or "")
    if not bool(row.get("milestone_reached")):
        return {
            "available": False,
            "reason": "milestone_not_reached",
            "target_end_to_end_gain": float(target_gain),
        }
    if milestone_kind != "ADMISSION_BATCH_READY":
        return {
            "available": False,
            "reason": "not_an_admission_milestone",
            "target_end_to_end_gain": float(target_gain),
        }
    t_admission = _positive_float(row.get("admission_milestone_wall_sec"))
    native_search = _nonnegative_float(row.get("native_search_wall_sec"))
    if t_admission is None or native_search is None:
        return {
            "available": False,
            "reason": "missing_admission_or_native_search_timing",
            "target_end_to_end_gain": float(target_gain),
        }
    tolerance = max(1.0e-6, t_admission * 1.0e-6)
    if native_search > t_admission + tolerance:
        return {
            "available": False,
            "reason": "native_search_exceeds_admission_milestone",
            "target_end_to_end_gain": float(target_gain),
            "t_admission_sec": t_admission,
            "native_search_sec": native_search,
        }

    fixed_pipeline = max(0.0, t_admission - native_search)
    native_search_share = native_search / t_admission
    fixed_pipeline_share = fixed_pipeline / t_admission
    required_search_reduction = (
        float(target_gain) * t_admission / native_search
        if native_search > 0.0
        else float("inf")
    )
    raw = _nonnegative_float(row.get("raw_negative_milestone_wall_sec"))
    raw_to_native = (
        max(0.0, native_search - raw)
        if raw is not None and raw <= native_search + tolerance
        else None
    )
    return {
        "available": True,
        "reason": "available",
        "assumption": "post_native_pipeline_invariant_under_queue_ordering",
        "target_end_to_end_gain": float(target_gain),
        "t_raw_sec": raw,
        "t_admission_sec": t_admission,
        "native_search_sec": native_search,
        "raw_to_native_harvest_sec": raw_to_native,
        "raw_to_native_harvest_share": (
            raw_to_native / t_admission if raw_to_native is not None else None
        ),
        "post_native_fixed_pipeline_sec": fixed_pipeline,
        "post_native_fixed_pipeline_share": fixed_pipeline_share,
        "queue_visible_native_search_share": native_search_share,
        "queue_zero_search_speedup_ceiling": native_search_share,
        "required_native_search_reduction_for_target": (
            required_search_reduction
        ),
        "target_feasible_under_fixed_pipeline_assumption": bool(
            required_search_reduction <= 1.0
        ),
    }


def _summarize_queue_action_headroom(
    rows: list[dict],
    *,
    target_gain: float = FORMAL_END_TO_END_GAIN_TARGET,
) -> dict:
    available = []
    unavailable_reasons: dict[str, int] = {}
    for row in rows:
        item = dict(
            row.get("q0_queue_action_headroom")
            or _queue_action_headroom(
                {
                    **dict(row.get("q0_timing") or {}),
                    "milestone_reached": row.get("q0_milestone_reached"),
                    "milestone_kind": row.get("q0_milestone_kind"),
                    "admission_milestone_wall_sec": (
                        row.get("q0_timing") or {}
                    ).get("t_admission_sec"),
                    "native_search_wall_sec": (
                        row.get("q0_timing") or {}
                    ).get("native_search_sec"),
                    "raw_negative_milestone_wall_sec": (
                        row.get("q0_timing") or {}
                    ).get("t_raw_sec"),
                },
                target_gain=target_gain,
            )
        )
        if item.get("available"):
            available.append((row, item))
        else:
            reason = str(item.get("reason") or "unknown")
            unavailable_reasons[reason] = unavailable_reasons.get(reason, 0) + 1

    per_scale = {}
    for scale in (30, 50):
        selected = [
            (row, item)
            for row, item in available
            if int(row.get("scale") or 0) == scale
        ]
        fixed_shares = [
            float(item["post_native_fixed_pipeline_share"])
            for _row, item in selected
        ]
        search_shares = [
            float(item["queue_visible_native_search_share"])
            for _row, item in selected
        ]
        required = [
            float(item["required_native_search_reduction_for_target"])
            for _row, item in selected
        ]
        harvest_shares = [
            float(item["raw_to_native_harvest_share"])
            for _row, item in selected
            if item.get("raw_to_native_harvest_share") is not None
        ]
        per_scale[f"scale{scale}"] = {
            "admission_context_count": len(selected),
            "instance_count": len(
                {str(row.get("instance_hash") or "") for row, _item in selected}
            ),
            "median_post_native_fixed_pipeline_share": _median_or_none(
                fixed_shares
            ),
            "maximum_post_native_fixed_pipeline_share": (
                max(fixed_shares) if fixed_shares else None
            ),
            "median_queue_visible_native_search_share": _median_or_none(
                search_shares
            ),
            "median_raw_to_native_harvest_share": _median_or_none(
                harvest_shares
            ),
            "median_required_native_search_reduction_for_target": (
                _median_or_none(required)
            ),
            "target_feasible_context_count": sum(
                bool(item["target_feasible_under_fixed_pipeline_assumption"])
                for _row, item in selected
            ),
            "fixed_pipeline_dominates_context_count": sum(
                float(item["post_native_fixed_pipeline_share"])
                >= 1.0 - float(target_gain)
                for _row, item in selected
            ),
        }
    return {
        "diagnostic_only": True,
        "training_authority": "none_use_matched_qo2_q0_oracle_gate",
        "assumption": "post_native_pipeline_invariant_under_queue_ordering",
        "target_end_to_end_gain": float(target_gain),
        "available_admission_context_count": len(available),
        "unavailable_context_count": len(rows) - len(available),
        "unavailable_reasons": unavailable_reasons,
        **per_scale,
    }


def _positive_float(value) -> float | None:
    parsed = _nonnegative_float(value)
    return parsed if parsed is not None and parsed > 0.0 else None


def _nonnegative_float(value) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) and parsed >= 0.0 else None


def _median_or_none(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def _select_bucket(
    rows: list[dict], *, partition: str | None = None,
) -> float:
    safe = [
        row for row in rows
        if row.get("compliant_context") and row.get("all_initial_arms_safe")
        and (
            partition is None
            or str(row.get("partition") or "") == str(partition)
        )
    ]
    if not safe:
        return 1.0e-3
    scores = {}
    for bucket in BUCKETS:
        comparable = [
            row for row in safe
            if _initial_bucket_outcome_determined(row, bucket)
        ]
        scores[bucket] = (
            _geomean(
                float(row["bucket_ratios"][str(bucket)])
                for row in comparable
            )
            if comparable
            else float("inf")
        )
    if all(not math.isfinite(value) for value in scores.values()):
        return 1.0e-3
    return min(BUCKETS, key=lambda bucket: scores[bucket])


def _initial_bucket_outcome_determined(row: dict, bucket: float) -> bool:
    q0_kind = str(row.get("q0_milestone_kind") or "")
    qo2_kind = str(
        (row.get("qo2_milestone_kind_by_bucket") or {}).get(
            str(bucket)
        )
        or ""
    )
    return bool(
        row.get("q0_milestone_reached")
        and (row.get("qo2_milestone_reached_by_bucket") or {}).get(
            str(bucket)
        )
        and q0_kind == qo2_kind
        and q0_kind in {"ADMISSION_BATCH_READY", "EXACT_PROOF_COMPLETION"}
    )


def _aggregate_contexts(
    initial_rows: list[dict],
    replicate_rows: list[dict],
    bucket: float,
):
    groups: dict[str, list[dict]] = {}
    for row in replicate_rows:
        groups.setdefault(row["state_hash"], []).append(row)
    result = []
    eligible = (
        row for row in initial_rows
        if row.get("compliant_context") and row.get("all_initial_arms_safe")
    )
    for initial in sorted(
        eligible,
        key=lambda row: (int(row["scale"]), str(row["state_hash"])),
    ):
        state = str(initial["state_hash"])
        values = groups.get(state, [])
        if values:
            q0 = statistics.median(row["q0_wall_sec"] for row in values)
            qo2 = statistics.median(row["qo2_wall_sec"] for row in values)
            safe = all(row["safe"] for row in values)
            q0_exhaustive = all(
                bool(_load(_resolve(row["q0_path"])).get("search_exhaustive"))
                for row in values
            )
            qo2_exhaustive = all(
                bool(_load(_resolve(row["qo2_path"])).get("search_exhaustive"))
                for row in values
            )
            q0_milestone_reached = all(
                bool(row.get("q0_milestone_reached")) for row in values
            )
            qo2_milestone_reached = all(
                bool(row.get("qo2_milestone_reached")) for row in values
            )
            q0_milestone_kind = _common_milestone_kind(
                row.get("q0_milestone_kind") for row in values
            )
            qo2_milestone_kind = _common_milestone_kind(
                row.get("qo2_milestone_kind") for row in values
            )
            source = "three_blocked_replicates"
            repeat_count = len(values)
        else:
            q0 = float(initial["q0_wall_sec"])
            qo2 = float(initial["qo2_wall_sec_by_bucket"][str(bucket)])
            safe = bool(initial["all_initial_arms_safe"])
            q0_exhaustive = bool(initial.get("q0_search_exhaustive"))
            qo2_exhaustive = bool(
                initial["qo2_search_exhaustive_by_bucket"][str(bucket)]
            )
            q0_milestone_reached = bool(
                initial.get("q0_milestone_reached")
            )
            qo2_milestone_reached = bool(
                initial["qo2_milestone_reached_by_bucket"][str(bucket)]
            )
            q0_milestone_kind = str(
                initial.get("q0_milestone_kind") or ""
            )
            qo2_milestone_kind = str(
                initial["qo2_milestone_kind_by_bucket"][str(bucket)] or ""
            )
            source = "single_initial_screen"
            repeat_count = 1
        result.append({
            **_identity(initial),
            "repeat_count": repeat_count,
            "outcome_source": source,
            "q0_median_wall_sec": q0,
            "qo2_median_wall_sec": qo2,
            "ratio": qo2 / q0,
            "saved_wall_sec": max(0.0, q0 - qo2),
            "q0_search_exhaustive": q0_exhaustive,
            "qo2_search_exhaustive": qo2_exhaustive,
            "q0_milestone_reached": q0_milestone_reached,
            "qo2_milestone_reached": qo2_milestone_reached,
            "q0_milestone_kind": q0_milestone_kind,
            "qo2_milestone_kind": qo2_milestone_kind,
            "outcome_determined": bool(
                q0_milestone_reached
                and qo2_milestone_reached
                and q0_milestone_kind == qo2_milestone_kind
                and q0_milestone_kind not in {"", "MIXED"}
            ),
            "all_safe": safe,
        })
    return result


def _common_milestone_kind(values) -> str:
    kinds = {str(value or "") for value in values}
    return next(iter(kinds)) if len(kinds) == 1 else "MIXED"


def _gate(
    rows: list[dict],
    initial_rows: list[dict],
    bucket: float,
    *,
    queue_action_headroom: dict | None = None,
):
    safe = bool(rows) and all(row["all_safe"] for row in rows) and all(
        row.get("all_initial_arms_safe") for row in initial_rows if row.get("compliant_context")
    )
    scale_payload = {}
    for scale in (30, 50):
        compliant = [row for row in rows if row["scale"] == scale]
        determined = [
            row for row in compliant if bool(row.get("outcome_determined"))
        ]
        ratios = [float(row["ratio"]) for row in determined]
        positive = [
            row for row in determined if float(row["ratio"]) <= 0.95
        ]
        ci = _instance_bootstrap(determined)
        scale_payload[f"scale{scale}"] = {
            "context_count": len(compliant),
            "determined_context_count": len(determined),
            "right_censored_or_mismatched_context_count": (
                len(compliant) - len(determined)
            ),
            "positive_context_count": len(positive),
            "positive_instance_count": len({row["instance_hash"] for row in positive}),
            "paired_geomean_ratio": _geomean(ratios),
            "bootstrap_95_upper": ci[1],
            "positive_fraction": len(positive) / max(1, len(determined)),
        }
    determined_rows = [
        row for row in rows if bool(row.get("outcome_determined"))
    ]
    all_positive = [
        row for row in determined_rows if float(row["ratio"]) <= 0.95
    ]
    saved_by_instance: dict[str, float] = {}
    for row in determined_rows:
        saved_by_instance[row["instance_hash"]] = saved_by_instance.get(row["instance_hash"], 0.0) + float(row["saved_wall_sec"])
    total_saved = sum(saved_by_instance.values())
    max_fraction = max(saved_by_instance.values(), default=0.0) / max(1.0e-12, total_saved)
    passed = bool(
        safe
        and all(
            scale_payload[f"scale{scale}"]["context_count"] >= 20
            and scale_payload[f"scale{scale}"]["determined_context_count"] >= 20
            and scale_payload[f"scale{scale}"]["positive_context_count"] >= 20
            and scale_payload[f"scale{scale}"]["positive_instance_count"] >= 5
            and scale_payload[f"scale{scale}"]["paired_geomean_ratio"] <= 0.85
            and scale_payload[f"scale{scale}"]["bootstrap_95_upper"] <= 0.90
            and scale_payload[f"scale{scale}"]["positive_fraction"] > 0.20
            for scale in (30, 50)
        )
        and len(all_positive) >= 50
        and max_fraction <= 0.35
    )
    return {
        "passed": passed,
        "reason": "all_predeclared_gates_passed" if passed else "bounded_oracle_gate_failed",
        "context_count": len(rows),
        "frozen_guidance_bucket_width": bucket,
        "all_exact_safe": safe,
        "net_gain_5pct_context_count": len(all_positive),
        "max_instance_saved_wall_fraction": max_fraction,
        "queue_action_headroom": dict(queue_action_headroom or {}),
        "queue_action_headroom_role": (
            "mechanism_diagnostic_only_matched_oracle_is_authoritative"
        ),
        **scale_payload,
    }


def _instance_bootstrap(rows: list[dict]):
    if not rows:
        return (float("inf"), float("inf"))
    groups: dict[str, list[float]] = {}
    for row in rows:
        groups.setdefault(row["instance_hash"], []).append(float(row["ratio"]))
    keys = sorted(groups)
    rng = random.Random(20260801)
    values = []
    for _ in range(10_000):
        draw = [keys[rng.randrange(len(keys))] for _ in keys]
        ratios = [value for key in draw for value in groups[key]]
        values.append(_geomean(ratios))
    values.sort()
    return values[250], values[9750]


def _geomean(values):
    return float("inf") if not values else math.exp(statistics.fmean(math.log(max(1.0e-12, float(value))) for value in values))


def _identity(row):
    payload = {
        "scale": int(row["scale"]),
        "instance_id": str(row["instance_id"]),
        "instance_hash": str(row["instance_hash"]),
        "state_hash": str(row["state_hash"]),
    }
    for key in (
        "instance_path",
        "snapshot_path",
        "source_backend_id",
        "source_engine_hash",
        "source_config_hash",
        "source_exact_action_policy_hash",
        "pricing_lifecycle_scope",
        "previous_q0_wall_stratum",
        "partition",
    ):
        if row.get(key):
            payload[key] = str(row[key])
    for key in ("round", "branch_pair_count", "active_cut_count"):
        if row.get(key) is not None:
            payload[key] = int(row[key])
    payload["preaction_stratum"] = _preaction_stratum(row)
    return payload


def _optional_int(value):
    return None if value is None else max(0, int(value))


def _counts(values):
    result = {}
    for value in values:
        result[str(value)] = result.get(str(value), 0) + 1
    return dict(sorted(result.items()))


def _resolve(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _validate_execution_freeze(path: Path) -> dict:
    payload = _load(path)
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_oracle_execution_freeze.v2"
    ):
        raise SystemExit("QG2 execution freeze schema mismatch")
    if not bool(payload.get("development_only")) or bool(
        payload.get("deployable")
    ):
        raise SystemExit("QG2 execution freeze safety mismatch")
    if (
        payload.get("oracle_schema") != SCHEMA
        or payload.get("potential_schema") != POTENTIAL_SCHEMA
        or payload.get("supervision_schema_version")
        != QG2_SUPERVISION_SCHEMA_V2
        or payload.get("queue_action_surface")
        != QG2_QUEUE_ACTION_SURFACE_V1
        or int(payload.get("maximum_oracle_contexts") or 0) != 300
        or int(payload.get("maximum_oracle_contexts_per_scale") or 0)
        != 150
    ):
        raise SystemExit("QG2 execution freeze contract mismatch")
    for raw_path, expected in dict(
        payload.get("frozen_file_sha256") or {}
    ).items():
        frozen = Path(raw_path)
        frozen = frozen if frozen.is_absolute() else ROOT / frozen
        if not frozen.is_file() or _sha256(frozen) != str(expected):
            raise SystemExit(f"QG2 execution frozen file drift: {frozen}")
    return payload


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_hash(payload):
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

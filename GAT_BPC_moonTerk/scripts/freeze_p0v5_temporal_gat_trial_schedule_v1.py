#!/usr/bin/env python3
"""Freeze outcome-blind blocked three-arm Temporal-GAT replay schedules."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.p0v5_temporal_gat_common import (  # noqa: E402
    load_frozen_config, mark_terminal_negative, write_once,
    update_state,
)


ARMS = (
    ("Q0", "Q0"),
    ("CONTINUE_QD1", "QT_CONTINUE"),
    ("MIGRATE_BACK_TO_Q0", "QT_REVERT"),
)
FORBIDDEN_SELECTION_FIELDS = {
    "wall_seconds", "ratio", "benefit", "adverse", "positive_gain",
    "selected_action", "model_action", "queue_outcome",
}


def determined_instance_capacity(contexts, *, partition):
    """Return the outcome-independent upper bound for determined instances."""
    by_scale = {}
    for raw in contexts["rows"]:
        if raw.get("partition") != partition:
            continue
        scale = int(raw["scale"])
        by_scale.setdefault(scale, set()).add(str(raw["instance_hash"]))
    return {
        str(scale): len(instance_hashes)
        for scale, instance_hashes in sorted(by_scale.items())
    }


def build_schedule(config, contexts, *, partition, selected_k=None):
    legal = []
    for raw in contexts["rows"]:
        row = dict(raw)
        if row.get("partition") != partition:
            continue
        if str(row.get("pricing_lifecycle_scope")) != "root_cg":
            raise ValueError("Temporal-GAT context schedule is root_cg only")
        if str(row.get("selection_policy")) != (
            "earliest_boundary_reaching_p0v4_fallback_request_v1"
        ):
            raise ValueError("context selection policy drift")
        if int(row.get("selection_rank_within_instance", -1)) not in {0, 1, 2}:
            raise ValueError("context selection rank drift")
        if any(name in row for name in FORBIDDEN_SELECTION_FIELDS):
            raise ValueError("queue outcome leaked into context freeze")
        legal.append(row)
    by_instance = {}
    for row in legal:
        key = (int(row["scale"]), str(row["instance_hash"]))
        by_instance.setdefault(key, []).append(row)
    for key, rows in by_instance.items():
        ranks = [int(row["selection_rank_within_instance"]) for row in rows]
        if ranks != sorted(set(ranks)) or len(rows) > int(
            config["maximum_contexts_per_instance"]
        ):
            raise ValueError(f"context rank/cap drift:{key}")
    tasks = []
    repeat_count = int(config["blocked_fresh_process_repeats"])
    for context in sorted(legal, key=lambda row: (
        int(row["scale"]), str(row["instance_hash"]),
        int(row["selection_rank_within_instance"]),
    )):
        scale = int(context["scale"])
        candidates = (
            [int(selected_k[str(scale)])] if selected_k is not None
            else [int(value) for value in config["trial_k_candidates"]]
        )
        for k in candidates:
            for repeat in range(repeat_count):
                digest = int(hashlib.sha256(
                    f"{context['context_id']}:{k}:{repeat}".encode()
                ).hexdigest()[:8], 16)
                order = list(ARMS)
                shift = digest % len(order)
                order = order[shift:] + order[:shift]
                block_id = f"{context['context_id']}:k{k}:r{repeat}"
                for ordinal, (arm, policy) in enumerate(order):
                    tasks.append({
                        "task_id": f"{block_id}:{ordinal}:{arm}",
                        "block_id": block_id, "ordinal_in_block": ordinal,
                        "context_id": context["context_id"],
                        "instance_hash": context["instance_hash"],
                        "scale": scale, "partition": partition,
                        "k": k, "repeat": repeat, "arm": arm,
                        "replay_policy": policy,
                        "boundary": int(config["boundary_by_scale"][str(scale)]),
                        "cap_seconds": float(config["execution"][
                            f"scale{scale}_task_cap_sec"
                        ]),
                        "memory_limit_gb": float(config["execution"][
                            "effective_native_memory_limit_gb"
                        ]),
                    })
    return {
        "schema_version": "lunar_ice_bpc.p0v5_temporal_trial_schedule.v1",
        "status": "FROZEN_BEFORE_ARM_OUTCOMES",
        "partition": partition, "single_host_instance": True,
        "fresh_process_per_task": True, "blocked_repeats": repeat_count,
        "memavailable_reserve_gb": float(
            config["execution"]["memavailable_reserve_gb"]
        ),
        "arm_order": "sha256_rotated_within_matched_block_v1",
        "task_count": len(tasks), "tasks": tasks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--contexts", type=Path, required=True)
    parser.add_argument(
        "--partition", choices=("train", "calibration"), required=True
    )
    parser.add_argument("--k-selection", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    candidate = json.loads(args.config.read_text(encoding="utf-8"))
    try:
        config, config_freeze = load_frozen_config(
            args.config, run_root=ROOT / candidate["run_root"]
        )
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    contexts = json.loads(args.contexts.read_text(encoding="utf-8"))
    canonical_contexts = (
        ROOT / config["run_root"] / "contexts.freeze.json"
    ).resolve()
    if (
        args.contexts.resolve() != canonical_contexts
        or contexts.get("status")
            != "FROZEN_BEFORE_CONTINUE_REVERT_OUTCOMES"
        or contexts.get("source_config_freeze_sha256")
            != hashlib.sha256(config_freeze.read_bytes()).hexdigest()
    ):
        raise SystemExit("Temporal-GAT context freeze binding drift")
    selected = None
    if args.k_selection:
        selection_payload = json.loads(
            args.k_selection.read_text(encoding="utf-8")
        )
        if (
            selection_payload.get("status")
                != "FIXED_BEFORE_CALIBRATION_AND_HELDOUT"
            or selection_payload.get("source_config_freeze_sha256")
                != hashlib.sha256(config_freeze.read_bytes()).hexdigest()
        ):
            raise SystemExit("Temporal-GAT K selection binding drift")
        selected = selection_payload["selected_k_by_scale"]
    if args.partition != "train" and selected is None:
        raise SystemExit("non-train schedule requires frozen K selection")
    if args.partition == "train" and selected is not None:
        raise SystemExit("train K grid must be frozen before K selection")
    if args.partition == "train":
        capacity = determined_instance_capacity(
            contexts, partition=args.partition
        )
        minimum = int(
            config["k_selection_gates"]["minimum_determined_instances"]
        )
        insufficient = {
            str(scale): int(capacity.get(str(scale), 0))
            for scale in map(int, config["scales"])
            if int(capacity.get(str(scale), 0)) < minimum
        }
        if insufficient:
            reason = (
                "TEMPORAL_TRAIN_CONTEXT_CAPACITY_BELOW_K_GATE_"
                + "_".join(
                    f"SCALE{scale}_{count}_LT_{minimum}"
                    for scale, count in sorted(insufficient.items())
                )
            )
            run_root = ROOT / config["run_root"]
            audit_path = run_root / "train_trial_preflight.audit.json"
            audit = {
                "schema_version": (
                    "lunar_ice_bpc.p0v5_temporal_trial_preflight_audit.v1"
                ),
                "decision": "FAIL",
                "reason": reason,
                "terminal_negative": True,
                "gate_is_outcome_independent": True,
                "minimum_determined_instances_gate": minimum,
                "maximum_determined_instances_by_scale": capacity,
                "insufficient_scales": insufficient,
                "source_config_freeze_sha256": hashlib.sha256(
                    config_freeze.read_bytes()
                ).hexdigest(),
                "source_contexts_sha256": hashlib.sha256(
                    args.contexts.read_bytes()
                ).hexdigest(),
                "arm_outcome_artifact_count_before_preflight": 0,
                "production_switch_authorized": False,
                "deployment_authorized": False,
            }
            write_once(audit_path, audit)
            mark_terminal_negative(
                run_root, stage="TRIAL_SCHEDULE_FREEZE", reason=reason,
                detail={
                    "audit": str(audit_path.resolve()),
                    "audit_sha256": hashlib.sha256(
                        audit_path.read_bytes()
                    ).hexdigest(),
                    "minimum_determined_instances_gate": minimum,
                    "maximum_determined_instances_by_scale": capacity,
                },
            )
            raise SystemExit(reason)
    payload = build_schedule(
        config, contexts, partition=args.partition, selected_k=selected
    )
    payload["source_config_freeze_sha256"] = hashlib.sha256(
        config_freeze.read_bytes()
    ).hexdigest()
    payload["source_contexts_sha256"] = hashlib.sha256(
        args.contexts.read_bytes()
    ).hexdigest()
    payload["source_k_selection_sha256"] = (
        hashlib.sha256(args.k_selection.read_bytes()).hexdigest()
        if args.k_selection else None
    )
    payload["source_k_selection_path"] = (
        str(args.k_selection.resolve()) if args.k_selection else None
    )
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output.exists() and args.output.read_text(encoding="utf-8") != encoded:
        raise SystemExit("immutable temporal schedule drift")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not args.output.exists():
        args.output.write_text(encoded, encoding="utf-8")
    update_state(
        ROOT / config["run_root"],
        stage=("TRAIN_TRIALS" if args.partition == "train"
               else "CALIBRATION_TRIALS"),
        status="READY",
        detail={
            f"{args.partition}_trial_task_count": int(payload["task_count"]),
            f"{args.partition}_trial_tasks_published": 0,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

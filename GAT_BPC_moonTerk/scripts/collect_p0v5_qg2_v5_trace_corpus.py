#!/usr/bin/env python3
"""Collect the minimal Q0 future-trace corpus needed by Label GAT.

This is deliberately not a performance Oracle.  It replays only literal Q0
with development label tracing enabled, validates the frozen Exact binding,
and emits a shape-compatible training view for the existing exact-safe ranker
trainer.  Random and leaked-QO2 arms are outside this critical path; the
trained QG2 action is judged later by fresh-process Q0/QG2 replay.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TRACE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_trace_supervision_corpus.v1"
COMPATIBLE_VIEW_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
SELECTION_FREEZE_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_trace_supervision_selection_freeze.v1"
)
REPLAY_SCHEMA = "lunar_ice_bpc.p0v5_qg2_snapshot_replay.v3"
BUCKET = 1.0e-3
PARTITIONS = ("train", "calibration", "heldout")
FROZEN_ORACLE = ROOT / "scripts/run_p0v5_qg2_bounded_oracle.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-index", required=True)
    parser.add_argument("--instance-split", required=True)
    parser.add_argument("--execution-freeze", required=True)
    parser.add_argument("--source-oracle-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--training-view-output", required=True)
    parser.add_argument("--selection-freeze", required=True)
    parser.add_argument("--scale30-contexts", type=int, default=33)
    parser.add_argument("--scale50-contexts", type=int, default=20)
    parser.add_argument("--scale30-wall-sec", type=float, default=300.0)
    parser.add_argument("--scale50-wall-sec", type=float, default=600.0)
    parser.add_argument("--memory-limit-gb", type=float, default=10.867)
    parser.add_argument(
        "--native-build-dir",
        default="build/native-spprc-bidirectional-feasibility-v1",
    )
    args = parser.parse_args()

    state_index = _resolve(args.state_index)
    split_path = _resolve(args.instance_split)
    execution_freeze = _resolve(args.execution_freeze)
    source_oracle_dir = _resolve(args.source_oracle_dir)
    output_dir = _resolve(args.output_dir)
    output = _resolve(args.output)
    training_view = _resolve(args.training_view_output)
    selection_freeze = _resolve(args.selection_freeze)
    native_build = _resolve(args.native_build_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    frozen = _load_frozen_oracle()
    freeze_payload = frozen._validate_execution_freeze(execution_freeze)
    if str(freeze_payload.get("source_state_index_sha256") or "") != _sha256(
        state_index
    ):
        raise SystemExit("trace corpus execution-freeze state-index drift")
    if str(freeze_payload.get("instance_split_sha256") or "") != _sha256(
        split_path
    ):
        raise SystemExit("trace corpus execution-freeze split drift")

    assignments = frozen._load_instance_split(split_path)
    rows = frozen._bind_preoutcome_partitions(
        frozen._state_rows(_load(state_index)), assignments
    )
    # Reuse the same fully pre-action ordering frozen for the old bounded
    # Oracle.  The first 33 scale30 states had already completed Q0 traces
    # before this redesign; no outcome is used to select either scale.
    ordered = frozen._bounded_selection(rows, maximum=120, per_scale=60)
    selected = []
    targets = {
        30: max(1, int(args.scale30_contexts)),
        50: max(1, int(args.scale50_contexts)),
    }
    for scale in (30, 50):
        candidates = [row for row in ordered if int(row["scale"]) == scale]
        if len(candidates) < targets[scale]:
            raise SystemExit(f"trace corpus scale{scale} lacks frozen contexts")
        selected.extend(candidates[: targets[scale]])

    budgets = {
        30: float(args.scale30_wall_sec),
        50: float(args.scale50_wall_sec),
    }
    selection_payload = _selection_payload(
        selected,
        state_index=state_index,
        split_path=split_path,
        execution_freeze=execution_freeze,
        source_oracle_dir=source_oracle_dir,
        budgets=budgets,
        memory_limit_gb=float(args.memory_limit_gb),
    )
    _freeze_or_validate(selection_freeze, selection_payload)

    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{native_build}"
    completed = []
    for index, row in enumerate(selected, start=1):
        scale = int(row["scale"])
        source = source_oracle_dir / (
            f"{scale}_{str(row['state_hash'])[:16]}/q0_trace.json"
        )
        target = (
            source if source.is_file() else output_dir / f"scale{scale}"
            / str(row["state_hash"])[:16] / "q0_trace.json"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        frozen._replay(
            row=row,
            target=target,
            policy="Q0",
            wall_limit=budgets[scale],
            memory_limit=float(args.memory_limit_gb),
            env=env,
            bucket=BUCKET,
            repeat=1,
            label_trace=True,
        )
        replay = _load(target)
        _validate_trace(
            replay,
            row=row,
            wall_sec=budgets[scale],
            memory_limit_gb=float(args.memory_limit_gb),
        )
        completed.append(_completed_row(row, target, replay))
        _atomic_write(output_dir / "progress.json", {
            "schema_version": (
                "lunar_ice_bpc.p0v5_qg2_trace_supervision_progress.v1"
            ),
            "completed_contexts": len(completed),
            "selected_contexts": len(selected),
            "completed_by_scale": {
                str(value): sum(
                    int(item["scale"]) == value for item in completed
                )
                for value in (30, 50)
            },
            "last_state_hash": str(row["state_hash"]),
            "random_or_leaked_qo2_replays": 0,
        })
        print(json.dumps({
            "completed": index,
            "total": len(selected),
            "scale": scale,
            "state": str(row["state_hash"])[:16],
            "milestone": replay.get("milestone_kind"),
            "reused": target == source,
        }, sort_keys=True), flush=True)

    coverage = _coverage(completed)
    gate = _supervision_gate(coverage)
    corpus = {
        "schema_version": TRACE_SCHEMA,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "development_only": True,
        "deployable": False,
        "training_authority_kind": "action_reachable_q0_future_trace_only",
        "performance_oracle": False,
        "random_or_leaked_qo2_outcomes_used": False,
        "source_state_index": str(state_index),
        "source_state_index_sha256": _sha256(state_index),
        "instance_split": str(split_path),
        "instance_split_sha256": _sha256(split_path),
        "execution_freeze": str(execution_freeze),
        "execution_freeze_sha256": _sha256(execution_freeze),
        "selection_freeze": str(selection_freeze),
        "selection_freeze_sha256": _sha256(selection_freeze),
        "frozen_guidance_bucket_width": BUCKET,
        "scale30_wall_sec": budgets[30],
        "scale50_wall_sec": budgets[50],
        "memory_limit_gb": float(args.memory_limit_gb),
        "coverage": coverage,
        "supervision_gate": gate,
        "rows": completed,
        "next_performance_authority": "fresh_process_q0_vs_qg2_force_on",
        "production_switch_authorized": False,
    }
    _atomic_write(output, corpus)

    initial_rows = []
    context_rows = []
    for row in completed:
        initial_rows.append({
            **{key: row[key] for key in (
                "scale", "instance_hash", "state_hash", "instance_path",
                "snapshot_path", "source_backend_id", "source_engine_hash",
                "source_config_hash", "source_exact_action_policy_hash",
                "partition",
            )},
            "instance_id": row["instance_id"],
            "q0_trace_path": row["q0_trace_path"],
            "q0_path": row["q0_trace_path"],
            "compliant_context": True,
            # In this view the only initial action is literal Q0.
            "all_initial_arms_safe": True,
            "initial_arm_scope": "q0_trace_only",
        })
        context_rows.append({
            "scale": row["scale"],
            "instance_hash": row["instance_hash"],
            "state_hash": row["state_hash"],
            "partition": row["partition"],
            "outcome_determined": True,
            "q0_milestone_kind": row["milestone_kind"],
        })
    view = {
        "schema_version": COMPATIBLE_VIEW_SCHEMA,
        "development_only": True,
        "deployable": False,
        "compatibility_view_role": "label_gat_trace_supervision_only",
        "source_trace_corpus": str(output),
        "source_trace_corpus_sha256": _sha256(output),
        "training_authority_kind": "action_reachable_q0_future_trace_only",
        "performance_oracle_gate_used": False,
        "random_or_leaked_qo2_outcomes_used": False,
        "frozen_guidance_bucket_width": BUCKET,
        "oracle_gate": {
            "passed": bool(gate["passed"]),
            "reason": str(gate["reason"]),
            "gate_kind": "trace_supervision_data_sufficiency",
        },
        "training_permitted": bool(gate["passed"]),
        "initial_rows": initial_rows,
        "context_rows": context_rows,
        "replicate_rows": [],
        "production_switch_authorized": False,
    }
    _atomic_write(training_view, view)
    return 0 if gate["passed"] else 2


def _selection_payload(
    rows,
    *,
    state_index: Path,
    split_path: Path,
    execution_freeze: Path,
    source_oracle_dir: Path,
    budgets: dict[int, float],
    memory_limit_gb: float,
) -> dict:
    return {
        "schema_version": SELECTION_FREEZE_SCHEMA,
        "development_only": True,
        "deployable": False,
        "selection_policy": "frozen_bounded_oracle_preaction_prefix.v1",
        "source_state_index_sha256": _sha256(state_index),
        "instance_split_sha256": _sha256(split_path),
        "execution_freeze_sha256": _sha256(execution_freeze),
        "collector_source_sha256": _sha256(Path(__file__).resolve()),
        "frozen_oracle_source_sha256": _sha256(FROZEN_ORACLE),
        "source_oracle_dir": str(source_oracle_dir),
        "scale30_wall_sec": budgets[30],
        "scale50_wall_sec": budgets[50],
        "memory_limit_gb": memory_limit_gb,
        "guidance_bucket_width": BUCKET,
        "selected_state_hashes_by_scale": {
            str(scale): [
                str(row["state_hash"])
                for row in rows if int(row["scale"]) == scale
            ]
            for scale in (30, 50)
        },
        "selection_uses_action_outcomes": False,
        "random_or_leaked_qo2_replays_per_context": 0,
    }


def _validate_trace(
    payload: dict,
    *,
    row: dict,
    wall_sec: float,
    memory_limit_gb: float,
) -> None:
    telemetry = dict(payload.get("proof_telemetry") or {})
    errors = []
    expected = {
        "schema_version": REPLAY_SCHEMA,
        "source_state_hash": str(row["state_hash"]),
        "source_engine_hash": str(row["source_engine_hash"]),
        "source_config_hash": str(row["source_config_hash"]),
        "source_exact_action_policy_hash": str(
            row["source_exact_action_policy_hash"]
        ),
        "policy": "Q0",
    }
    for key, value in expected.items():
        if str(payload.get(key) or "") != str(value):
            errors.append(key)
    if (
        int(payload.get("repeat_index") or 0) != 1
        or float(payload.get("guidance_bucket_width") or 0.0) != BUCKET
        or float(payload.get("requested_wall_time_limit_sec") or 0.0)
        != float(wall_sec)
        or float(payload.get("requested_memory_limit_gb") or 0.0)
        != float(memory_limit_gb)
        or not bool(payload.get("requested_label_trace"))
        or not bool(payload.get("milestone_reached"))
        or bool(payload.get("labels_dropped"))
        or not bool(telemetry.get("proof_queue_label_trace_enabled"))
        or not list(telemetry.get("proof_queue_label_state_trace") or ())
    ):
        errors.append("complete_future_trace")
    if any(int(telemetry.get(key) or 0) for key in (
        "guidance_filter_count", "guidance_arc_drop_count",
        "guidance_label_drop_count", "guidance_branch_pair_drop_count",
    )):
        errors.append("guidance_drop")
    if errors:
        raise SystemExit(
            "trace corpus replay contract failed:" + ",".join(sorted(set(errors)))
        )


def _completed_row(row: dict, path: Path, replay: dict) -> dict:
    return {
        "scale": int(row["scale"]),
        "instance_id": str(row["instance_id"]),
        "instance_hash": str(row["instance_hash"]),
        "state_hash": str(row["state_hash"]),
        "instance_path": str(row["instance_path"]),
        "snapshot_path": str(row["snapshot_path"]),
        "source_backend_id": str(row["source_backend_id"]),
        "source_engine_hash": str(row["source_engine_hash"]),
        "source_config_hash": str(row["source_config_hash"]),
        "source_exact_action_policy_hash": str(
            row["source_exact_action_policy_hash"]
        ),
        "partition": str(row["partition"]),
        "q0_trace_path": str(path),
        "q0_trace_sha256": _sha256(path),
        "milestone_kind": str(replay.get("milestone_kind") or ""),
        "label_trace_count": len(
            dict(replay.get("proof_telemetry") or {}).get(
                "proof_queue_label_state_trace"
            ) or ()
        ),
        "search_exhaustive": bool(replay.get("search_exhaustive")),
    }


def _coverage(rows: list[dict]) -> dict:
    result = {}
    for scale in (30, 50):
        selected = [row for row in rows if int(row["scale"]) == scale]
        result[str(scale)] = {
            "context_count": len(selected),
            "instance_count": len({row["instance_hash"] for row in selected}),
            "label_trace_count": sum(int(row["label_trace_count"]) for row in selected),
            "milestone_counts": {
                milestone: sum(
                    str(row["milestone_kind"]) == milestone for row in selected
                )
                for milestone in (
                    "ADMISSION_BATCH_READY", "EXACT_PROOF_COMPLETION"
                )
            },
            "partition_context_counts": {
                value: sum(row["partition"] == value for row in selected)
                for value in PARTITIONS
            },
            "partition_instance_counts": {
                value: len({
                    row["instance_hash"] for row in selected
                    if row["partition"] == value
                })
                for value in PARTITIONS
            },
        }
    return result


def _supervision_gate(coverage: dict) -> dict:
    passed = True
    errors = []
    for scale, minimum_contexts in ((30, 33), (50, 20)):
        row = dict(coverage[str(scale)])
        if int(row["context_count"]) < minimum_contexts:
            errors.append(f"scale{scale}_contexts")
        if int(row["instance_count"]) < 10:
            errors.append(f"scale{scale}_instances")
        if int(row["label_trace_count"]) <= 0:
            errors.append(f"scale{scale}_labels")
        for partition in PARTITIONS:
            if int(row["partition_context_counts"][partition]) < 2:
                errors.append(f"scale{scale}_{partition}_contexts")
            if int(row["partition_instance_counts"][partition]) < 2:
                errors.append(f"scale{scale}_{partition}_instances")
    if errors:
        passed = False
    return {
        "passed": passed,
        "reason": (
            "trace_supervision_data_sufficiency_passed"
            if passed else "trace_supervision_data_sufficiency_failed"
        ),
        "errors": errors,
        "performance_deployment_authority": False,
        "fresh_process_force_on_required": True,
    }


def _freeze_or_validate(path: Path, payload: dict) -> None:
    if path.is_file():
        if _load(path) != payload:
            raise SystemExit("trace corpus selection freeze drift")
        return
    _atomic_write(path, payload)


def _load_frozen_oracle():
    spec = importlib.util.spec_from_file_location(
        "p0v5_qg2_frozen_oracle_helpers", FROZEN_ORACLE
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen Oracle helpers")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _resolve(value) -> Path:
    path = Path(str(value)).expanduser()
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

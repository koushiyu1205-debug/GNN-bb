#!/usr/bin/env python3
"""Finalize a trace corpus under the pre-outcome 12/6 fitting-only gate.

The selected 20-state scale50 universe remains frozen.  A 600-second Q0 trace
censor is recorded, never converted into supervision.  If the independently
pre-outcome-frozen fitting minimum is already satisfied across partitions and
instances, the complete traces may authorize model fitting only; fresh-process
evaluation retains all performance and deployment authority.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/p0v5_qg2_v5_trace_first_20260807"
SOURCE_RUN = ROOT / "runs/p0v5_qg2_v4_realmap_gat_first_20260806"
INDEX = SOURCE_RUN / "realmap_v4_snapshot_index.json"
SPLIT = SOURCE_RUN / "realmap_v4_instance_split.json"
SOURCE_ORACLE_DIR = SOURCE_RUN / "oracle_realmap_v4"
FITTING_GATE_FREEZE = (
    SOURCE_RUN / "realmap_v4_instance_balanced_fitting_gate_freeze.json"
)
SELECTION_FREEZE = RUN / "trace_selection_freeze.json"
TRACE_DIR = RUN / "trace_corpus"
OUTPUT = RUN / "trace_supervision_corpus.json"
VIEW = RUN / "trace_training_view.json"
COLLECTOR = ROOT / "scripts/collect_p0v5_qg2_v5_trace_corpus.py"


def main() -> int:
    collector = _load_collector()
    selection = _load(SELECTION_FREEZE)
    gate_freeze = _load(FITTING_GATE_FREEZE)
    if (
        selection.get("schema_version")
        != collector.SELECTION_FREEZE_SCHEMA
        or str(selection.get("collector_source_sha256") or "")
        != _sha256(COLLECTOR)
        or bool(selection.get("selection_uses_action_outcomes"))
        or int(selection.get("random_or_leaked_qo2_replays_per_context") or 0)
        != 0
    ):
        raise SystemExit("bounded trace selection freeze drift")
    thresholds = dict(gate_freeze.get("thresholds") or {})
    partition_minimums = dict(gate_freeze.get("partition_minimums") or {})
    if (
        not bool(gate_freeze.get("frozen_before_scale50_oracle_outcomes"))
        or int(thresholds.get("minimum_determined_contexts_per_scale") or 0)
        != 12
        or int(thresholds.get("minimum_determined_instances_per_scale") or 0)
        != 6
        or partition_minimums != {
            "train": {"contexts": 4, "instances": 2},
            "calibration": {"contexts": 2, "instances": 2},
            "heldout": {"contexts": 2, "instances": 2},
        }
    ):
        raise SystemExit("bounded trace fitting gate is not pre-outcome frozen")

    index = _load(INDEX)
    split = _load(SPLIT)
    assignments = dict(split.get("assignments") or {})
    rows_by_state = {
        str(row["state_hash"]): dict(row) for row in index.get("rows") or ()
    }
    completed = []
    censored = []
    unrun = []
    for raw_scale in ("30", "50"):
        scale = int(raw_scale)
        for state in selection["selected_state_hashes_by_scale"][raw_scale]:
            row = dict(rows_by_state[str(state)])
            normalized = {
                "scale": scale,
                "instance_id": str(row.get("instance_id") or ""),
                "instance_hash": str(
                    row.get("instance_content_hash") or row.get("instance_hash")
                ),
                "state_hash": str(state),
                "instance_path": str(Path(row["instance_path"]).resolve()),
                "snapshot_path": str(Path(row["snapshot_path"]).resolve()),
                "source_backend_id": str(row["source_backend_id"]),
                "source_engine_hash": str(row["source_engine_hash"]),
                "source_config_hash": str(row["source_config_hash"]),
                "source_exact_action_policy_hash": str(
                    row["source_exact_action_policy_hash"]
                ),
                "partition": str(assignments[str(
                    row.get("instance_content_hash") or row.get("instance_hash")
                )]),
            }
            path = (
                SOURCE_ORACLE_DIR / f"30_{str(state)[:16]}/q0_trace.json"
                if scale == 30 else
                TRACE_DIR / "scale50" / str(state)[:16] / "q0_trace.json"
            )
            if not path.is_file():
                unrun.append({
                    "scale": scale,
                    "instance_hash": normalized["instance_hash"],
                    "state_hash": str(state),
                    "partition": normalized["partition"],
                    "reason": "not_run_after_bounded_censor_stop",
                })
                continue
            replay = _load(path)
            wall = 300.0 if scale == 30 else 600.0
            try:
                collector._validate_trace(
                    replay,
                    row=normalized,
                    wall_sec=wall,
                    memory_limit_gb=10.867,
                )
            except SystemExit:
                _validate_censor(replay, row=normalized, wall_sec=wall)
                censored.append({
                    "scale": scale,
                    "instance_hash": normalized["instance_hash"],
                    "state_hash": str(state),
                    "partition": normalized["partition"],
                    "q0_trace_path": str(path),
                    "q0_trace_sha256": _sha256(path),
                    "reason": "q0_future_trace_right_censored",
                    "status": str(
                        replay.get("engine_status") or "TIMEOUT"
                    ),
                    "wall_sec": float(
                        replay.get("total_fresh_process_wall_sec")
                        or replay.get("wall_sec") or wall
                    ),
                })
                continue
            completed.append(collector._completed_row(normalized, path, replay))

    coverage = collector._coverage(completed)
    errors = []
    for scale in (30, 50):
        row = dict(coverage[str(scale)])
        required_contexts = 33 if scale == 30 else int(
            thresholds["minimum_determined_contexts_per_scale"]
        )
        required_instances = 10 if scale == 30 else int(
            thresholds["minimum_determined_instances_per_scale"]
        )
        if int(row["context_count"]) < required_contexts:
            errors.append(f"scale{scale}_contexts")
        if int(row["instance_count"]) < required_instances:
            errors.append(f"scale{scale}_instances")
        for partition, minimum in partition_minimums.items():
            if int(row["partition_context_counts"][partition]) < int(
                minimum["contexts"]
            ):
                errors.append(f"scale{scale}_{partition}_contexts")
            if int(row["partition_instance_counts"][partition]) < int(
                minimum["instances"]
            ):
                errors.append(f"scale{scale}_{partition}_instances")
    if errors or not censored:
        raise SystemExit(
            "bounded trace fitting gate failed:" + ",".join(errors or [
                "missing_declared_censor"
            ])
        )

    corpus = {
        "schema_version": collector.TRACE_SCHEMA,
        "development_only": True,
        "deployable": False,
        "training_authority_kind": (
            "preoutcome_bounded_action_reachable_q0_future_trace_only"
        ),
        "performance_oracle": False,
        "random_or_leaked_qo2_outcomes_used": False,
        "source_state_index": str(INDEX),
        "source_state_index_sha256": _sha256(INDEX),
        "instance_split": str(SPLIT),
        "instance_split_sha256": _sha256(SPLIT),
        "selection_freeze": str(SELECTION_FREEZE),
        "selection_freeze_sha256": _sha256(SELECTION_FREEZE),
        "preoutcome_fitting_gate_freeze": str(FITTING_GATE_FREEZE),
        "preoutcome_fitting_gate_freeze_sha256": _sha256(FITTING_GATE_FREEZE),
        "frozen_guidance_bucket_width": collector.BUCKET,
        "scale30_wall_sec": 300.0,
        "scale50_wall_sec": 600.0,
        "memory_limit_gb": 10.867,
        "coverage": coverage,
        "supervision_gate": {
            "passed": True,
            "reason": "preoutcome_12_context_6_instance_fitting_gate_passed",
            "performance_deployment_authority": False,
            "fresh_process_force_on_required": True,
        },
        "selected_context_count": sum(
            len(values) for values in selection[
                "selected_state_hashes_by_scale"
            ].values()
        ),
        "complete_context_count": len(completed),
        "right_censored_contexts": censored,
        "unrun_selected_contexts": unrun,
        "bounded_stop_rule": (
            "stop_after_first_600s_q0_trace_censor_once_preoutcome_fitting_"
            "minimum_is_satisfied"
        ),
        "rows": completed,
        "next_performance_authority": "fresh_process_q0_vs_qg2_force_on",
        "production_switch_authorized": False,
    }
    collector._atomic_write(OUTPUT, corpus)

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
        "schema_version": collector.COMPATIBLE_VIEW_SCHEMA,
        "development_only": True,
        "deployable": False,
        "compatibility_view_role": "label_gat_trace_supervision_only",
        "source_trace_corpus": str(OUTPUT),
        "source_trace_corpus_sha256": _sha256(OUTPUT),
        "training_authority_kind": corpus["training_authority_kind"],
        "performance_oracle_gate_used": False,
        "random_or_leaked_qo2_outcomes_used": False,
        "frozen_guidance_bucket_width": collector.BUCKET,
        "oracle_gate": {
            "passed": True,
            "reason": corpus["supervision_gate"]["reason"],
            "gate_kind": "trace_supervision_data_sufficiency",
        },
        "training_permitted": True,
        "initial_rows": initial_rows,
        "context_rows": context_rows,
        "replicate_rows": [],
        "production_switch_authorized": False,
    }
    collector._atomic_write(VIEW, view)
    print(json.dumps({
        "complete": len(completed),
        "censored": len(censored),
        "unrun": len(unrun),
        "coverage": coverage,
    }, sort_keys=True))
    return 0


def _validate_censor(payload: dict, *, row: dict, wall_sec: float) -> None:
    telemetry = dict(payload.get("proof_telemetry") or {})
    if (
        payload.get("schema_version")
        != "lunar_ice_bpc.p0v5_qg2_snapshot_replay.v3"
        or str(payload.get("source_state_hash") or "") != row["state_hash"]
        or str(payload.get("source_engine_hash") or "")
        != row["source_engine_hash"]
        or str(payload.get("source_config_hash") or "")
        != row["source_config_hash"]
        or str(payload.get("source_exact_action_policy_hash") or "")
        != row["source_exact_action_policy_hash"]
        or str(payload.get("policy") or "") != "Q0"
        or str(payload.get("engine_status") or "") != "TIMEOUT"
        or not bool(payload.get("requested_label_trace"))
        or bool(payload.get("milestone_reached"))
        or float(payload.get("requested_wall_time_limit_sec") or 0.0)
        != float(wall_sec)
        or any(int(telemetry.get(key) or 0) for key in (
            "guidance_filter_count", "guidance_arc_drop_count",
            "guidance_label_drop_count", "guidance_branch_pair_drop_count",
        ))
    ):
        raise SystemExit("bounded trace censor binding failed")


def _load_collector():
    spec = importlib.util.spec_from_file_location(
        "p0v5_qg2_v5_frozen_trace_collector", COLLECTOR
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load trace collector")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Maintain a lightweight Markdown status page for the P0V5 QG2 pipeline.

The collector is deliberately read-only with respect to solver artifacts.  It
loads each completed replay JSON once, keeps only a compact projection in
memory, and atomically replaces the Markdown report.  It never invokes Native,
the completion audit, training, or a solver controller.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import statistics
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
DEFAULT_ORACLE_DIR = DEFAULT_RUN_ROOT / "oracle_qg2_action_surface_v2_stage1"
DEFAULT_OUTPUT = DEFAULT_RUN_ROOT / "P0V5_QG2_LIVE_RESULTS.md"
FRESH_CALIBRATION_DIR = "calibration_qg2_combined_v1_base"
FRESH_CALIBRATION_MANIFEST = "qg2_combined_v1_supplemental_manifest.json"
FRESH_CALIBRATION_MODELS = ("linear", "mlp", "gat")

ARM_FILES = {
    "Q0": "q0_initial.json",
    "QD1": "qd1_initial.json",
    "QB1": "qb1_initial.json",
    "Random61635": "random_61635_initial.json",
    "Random91267": "random_91267_initial.json",
    "Random170141": "random_170141_initial.json",
    "QO2-1e-4": "qo2_0.0001_initial.json",
    "QO2-3e-4": "qo2_0.0003_initial.json",
    "QO2-1e-3": "qo2_0.001_initial.json",
}
BUCKET_ARMS = ("QO2-1e-4", "QO2-3e-4", "QO2-1e-3")
BUCKET_LABELS = {
    "QO2-1e-4": "1e-4",
    "QO2-3e-4": "3e-4",
    "QO2-1e-3": "1e-3",
}
CONTROLLER_STATES = {
    "Strict post-Oracle": "qg2_action_surface_v2_post_oracle_state.json",
    "Relaxed training": "qg2_action_surface_v2_relaxed_post_oracle_state.json",
    "Training-only V2": (
        "qg2_action_surface_v2_training_only_v2_state.json"
    ),
    "Selective Oracle evidence": (
        "qg2_selective_oracle_evidence_controller_state.json"
    ),
    "Context arm selector": (
        "qg2_context_arm_selector_controller_state.json"
    ),
    "Training-only V2 calibration": (
        "qg2_training_only_v2_calibration_controller_state.json"
    ),
    "Training-only V2 E2E": (
        "qg2_training_only_v2_e2e_controller_state.json"
    ),
    "Training-only V2 formal full20": (
        "qg2_training_only_v2_formal_controller_state.json"
    ),
    "Training-only V2 candidate finalizer": (
        "qg2_training_only_v2_candidate_finalizer_state.json"
    ),
    "Training-only V2 formal ordering safety": (
        "qg2_training_only_v2_formal_ordering_safety_state.json"
    ),
    "Selective runtime binding": (
        "qg2_training_only_v2_selective_runtime_binding_state.json"
    ),
    "Selective runtime E2E": "qg2_selective_runtime_e2e_state.json",
    "Selective runtime formal full20": (
        "qg2_selective_runtime_formal_state.json"
    ),
    "Selective runtime candidate finalizer": (
        "qg2_selective_runtime_candidate_finalizer_state.json"
    ),
    "Supplemental calibration": (
        "qg2_supplemental_calibration_controller_state.json"
    ),
    "Supplemental E2E": "qg2_supplemental_e2e_controller_state.json",
    "Supplemental formal full20": (
        "qg2_supplemental_formal_controller_state.json"
    ),
    "Supplemental candidate finalizer": (
        "qg2_supplemental_candidate_finalizer_state.json"
    ),
    "Positive-net E2E": "qg2_positive_net_e2e_state.json",
    "Positive-net formal full20": "qg2_positive_net_formal_state.json",
    "Positive-net candidate finalizer": (
        "qg2_positive_net_candidate_finalizer_state.json"
    ),
    "Development E2E": "qg2_action_surface_v2_e2e_controller_state.json",
    "Formal full20": "qg2_action_surface_v2_formal_controller_state.json",
    "Candidate finalizer": "qg2_action_surface_v2_candidate_finalizer_state.json",
    "Formal ordering safety": (
        "qg2_formal_ordering_safety_controller_state.json"
    ),
}
PIPELINE_ARTIFACTS = {
    "Oracle summary": "oracle_qg2_action_surface_v2_stage1.json",
    "Strict training report": "training_qg2_action_surface_v2/training_report.json",
    "Relaxed training report": (
        "training_qg2_action_surface_v2_relaxed/training_report.json"
    ),
    "Training-only V2 freeze": (
        "qg2_action_surface_v2_training_only_v2_freeze.json"
    ),
    "Training-only V2 gate": (
        "qg2_action_surface_v2_training_only_gate_v2.json"
    ),
    "Training-only V2 report": (
        "training_qg2_action_surface_v2_training_only_v2/training_report.json"
    ),
    "Selective Oracle evidence freeze": (
        "qg2_selective_oracle_evidence_controller_freeze.json"
    ),
    "Selective Oracle evidence": (
        "qg2_training_only_v2_selective_oracle_evidence.json"
    ),
    "Context selector freeze": (
        "qg2_context_arm_selector_controller_freeze.json"
    ),
    "Context selector report": (
        "context_arm_selector_feasibility_v1/selector_report.json"
    ),
    "Training-only V2 calibration freeze": (
        "qg2_training_only_v2_calibration_controller_freeze.json"
    ),
    "Training-only V2 supplemental manifest": (
        "qg2_training_only_v2_supplemental_manifest.json"
    ),
    "Training-only V2 calibration": (
        "calibration_qg2_action_surface_v2_training_only_v2/calibration_report.json"
    ),
    "Training-only V2 risk audit": (
        "qg2_training_only_v2_calibration_risk_audit.json"
    ),
    "Training-only V2 E2E freeze": (
        "qg2_training_only_v2_e2e_controller_freeze.json"
    ),
    "Training-only V2 E2E acceptance": (
        "e2e_training_only_v2_development_acceptance.json"
    ),
    "Training-only V2 formal freeze": (
        "qg2_training_only_v2_formal_controller_freeze.json"
    ),
    "Training-only V2 formal acceptance": (
        "formal_full20_acceptance_qg2_training_only_v2.json"
    ),
    "Training-only V2 finalizer freeze": (
        "qg2_training_only_v2_candidate_finalizer_freeze.json"
    ),
    "Training-only V2 pre-freeze audit": (
        "qg2_training_only_v2_pre_freeze_audit.json"
    ),
    "Training-only V2 candidate": (
        "P0V5_QG2_LABEL_STATE_GAT_TRAINING_ONLY_V2_candidate_freeze.json"
    ),
    "Training-only V2 completion audit": (
        "qg2_training_only_v2_completion_audit.json"
    ),
    "Training-only V2 formal safety freeze": (
        "qg2_training_only_v2_formal_ordering_safety_freeze.json"
    ),
    "Training-only V2 formal safety audit": (
        "qg2_training_only_v2_formal_ordering_safety_audit.json"
    ),
    "Training-only V2 candidate safety extension": (
        "P0V5_QG2_LABEL_STATE_GAT_TRAINING_ONLY_V2_candidate_safety_extension.json"
    ),
    "Selective runtime manifest": (
        "qg2_training_only_v2_selective_runtime_manifest.json"
    ),
    "Selective runtime authority": (
        "qg2_training_only_v2_selective_runtime_authority.json"
    ),
    "Selective runtime E2E acceptance": (
        "e2e_qg2_selective_runtime_v1_acceptance.json"
    ),
    "Selective runtime formal acceptance": (
        "formal_full20_qg2_selective_runtime_v1_acceptance.json"
    ),
    "Selective runtime candidate": (
        "P0V5_QG2_LABEL_STATE_GAT_SELECTIVE_RUNTIME_V1_candidate_freeze.json"
    ),
    "Selective runtime completion audit": (
        "qg2_selective_runtime_completion_audit.json"
    ),
    "Strict calibration": (
        "calibration_qg2_action_surface_v2/calibration_report.json"
    ),
    "Relaxed calibration": (
        "calibration_qg2_action_surface_v2_relaxed/calibration_report.json"
    ),
    "Supplemental calibration freeze": (
        "qg2_supplemental_calibration_controller_freeze.json"
    ),
    "Supplemental calibration manifest": (
        "qg2_supplemental_calibration_manifest.json"
    ),
    "Supplemental calibration": (
        "calibration_qg2_action_surface_v2_supplemental/calibration_report.json"
    ),
    "Supplemental E2E freeze": (
        "qg2_supplemental_e2e_controller_freeze.json"
    ),
    "Supplemental formal freeze": (
        "qg2_supplemental_formal_controller_freeze.json"
    ),
    "Supplemental finalizer freeze": (
        "qg2_supplemental_candidate_finalizer_freeze.json"
    ),
    "Development E2E acceptance": (
        "e2e_development_acceptance_qg2_action_surface_v2.json"
    ),
    "Formal full20 acceptance": (
        "formal_full20_acceptance_qg2_action_surface_v2.json"
    ),
    "Final candidate freeze": (
        "P0V5_QG2_ACTION_SURFACE_V2_LABEL_STATE_GAT_candidate_freeze.json"
    ),
    "Completion audit": "p0v5_qg2_action_surface_v2_completion_audit.json",
    "Formal ordering safety freeze": (
        "qg2_formal_ordering_safety_controller_freeze.json"
    ),
    "Formal ordering safety audit": (
        "p0v5_qg2_formal_ordering_safety_audit.json"
    ),
    "Candidate safety extension": (
        "P0V5_QG2_ACTION_SURFACE_V2_candidate_safety_extension.json"
    ),
    "Calibration risk V2 freeze": "qg2_calibration_risk_v2_freeze.json",
    "Calibration risk V2 audit": "qg2_calibration_risk_v2_audit.json",
    "Positive-net runtime freeze": (
        "qg2_positive_net_evaluation_runtime_integration_freeze.json"
    ),
    "Combined fresh-process manifest": FRESH_CALIBRATION_MANIFEST,
    "Combined fresh-process calibration": (
        f"{FRESH_CALIBRATION_DIR}/calibration_report.json"
    ),
    "Positive-net calibration": "qg2_positive_net_calibration_report.json",
    "Positive-net evaluation manifest": (
        "qg2_positive_net_evaluation_manifest.json"
    ),
    "Positive-net E2E freeze": "qg2_positive_net_e2e_controller_freeze_v2.json",
    "Positive-net E2E acceptance": "e2e_qg2_positive_net_v1_acceptance.json",
    "Positive-net formal freeze": (
        "qg2_positive_net_formal_controller_freeze.json"
    ),
    "Positive-net formal acceptance": (
        "formal_full20_qg2_positive_net_v1_acceptance.json"
    ),
    "Positive-net finalizer freeze": (
        "qg2_positive_net_candidate_finalizer_freeze_v3.json"
    ),
    "Positive-net candidate": (
        "P0V5_QG2_LABEL_STATE_GAT_POSITIVE_NET_V1_candidate_freeze.json"
    ),
    "Positive-net completion audit": "qg2_positive_net_completion_audit.json",
}
COMPLETION_AUDIT_CANDIDATES = (
    # The immutable final audit is authoritative once it exists.  Before
    # finalization, prefer the explicitly refreshed live audit over older
    # pre-freeze/action-surface audits so the report cannot show stale counts.
    "qg2_selective_runtime_completion_audit.json",
    "qg2_training_only_v2_completion_audit.json",
    "qg2_training_only_v2_completion_audit_live.json",
    "qg2_training_only_v2_pre_freeze_audit.json",
    "p0v5_qg2_action_surface_v2_completion_audit.json",
)
RELAXED_THRESHOLDS = {
    "minimum_determined_contexts_per_scale": 20,
    "minimum_gain_5pct_contexts_per_scale": 5,
    "minimum_positive_instances_per_scale": 5,
    "maximum_paired_geomean_ratio": 0.95,
    "maximum_instance_bootstrap_95_upper": 0.98,
    "maximum_instance_saved_wall_fraction": 0.35,
}
TRAINING_ONLY_V2_THRESHOLDS = {
    "minimum_determined_contexts_per_scale": 20,
    "minimum_determined_instances_per_scale": 10,
    "minimum_gain_5pct_contexts_per_scale": 5,
    "minimum_positive_instances_per_scale": 5,
    "minimum_nonpositive_contexts_per_scale": 5,
    "minimum_harmful_instances_per_scale": 3,
    "maximum_instance_saved_wall_fraction": 0.35,
}
MINIMUM_CALIBRATION_CONTEXTS_FOR_HARMFUL_GATE = 52


class ProjectionCache:
    """Cache small projections so every poll does not reread large route audits."""

    def __init__(self) -> None:
        self._values: dict[tuple[str, str], tuple[int, int, Any]] = {}

    def replay(self, path: Path) -> dict[str, Any] | None:
        return self._project(path, "replay", _project_replay)

    def potential(self, path: Path) -> dict[str, Any] | None:
        return self._project(path, "potential", _project_potential)

    def binding(self, path: Path) -> dict[str, Any] | None:
        return self._project(path, "binding", _project_snapshot_binding)

    def small_json(self, path: Path) -> dict[str, Any] | None:
        return self._project(path, "small", lambda value: value)

    def _project(self, path: Path, kind: str, project):
        try:
            stat = path.stat()
        except FileNotFoundError:
            return None
        key = (str(path), kind)
        cached = self._values.get(key)
        signature = (stat.st_mtime_ns, stat.st_size)
        if cached is not None and cached[:2] == signature:
            return cached[2]
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            value = project(payload)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            return None
        self._values[key] = (signature[0], signature[1], value)
        return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", default=str(DEFAULT_RUN_ROOT))
    parser.add_argument("--oracle-dir")
    parser.add_argument("--output")
    parser.add_argument("--oracle-pid", type=int)
    parser.add_argument("--watch-pid", action="append", type=int, default=[])
    parser.add_argument("--max-contexts", type=int)
    parser.add_argument("--max-contexts-per-scale", type=int)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    run_root = _resolve(args.run_root)
    oracle_dir = (
        _resolve(args.oracle_dir)
        if args.oracle_dir
        else run_root / "oracle_qg2_action_surface_v2_stage1"
    )
    output = (
        _resolve(args.output)
        if args.output
        else run_root / "P0V5_QG2_LIVE_RESULTS.md"
    )
    poll = max(5.0, min(300.0, float(args.poll_sec)))
    watched = tuple(dict.fromkeys(int(value) for value in args.watch_pid))
    cache = ProjectionCache()

    while True:
        report = collect_report(
            run_root=run_root,
            oracle_dir=oracle_dir,
            oracle_pid=args.oracle_pid,
            watched_pids=watched,
            maximum_contexts=args.max_contexts,
            maximum_contexts_per_scale=args.max_contexts_per_scale,
            cache=cache,
        )
        _atomic_write(output, render_markdown(report))
        print(json.dumps({
            "status": "updated",
            "output": str(output),
            "updated_at": report["updated_at"],
            "full_contexts": len(report["contexts"]),
            "watched_alive": report["watched_alive"],
        }, sort_keys=True), flush=True)
        if args.once:
            return 0
        if watched and not any(_pid_alive(pid) for pid in watched):
            return 0
        time.sleep(poll)


def collect_report(
    *,
    run_root: Path,
    oracle_dir: Path,
    oracle_pid: int | None,
    watched_pids: tuple[int, ...],
    cache: ProjectionCache,
    maximum_contexts: int | None = None,
    maximum_contexts_per_scale: int | None = None,
) -> dict[str, Any]:
    contexts: list[dict[str, Any]] = []
    partial_contexts: list[dict[str, Any]] = []
    progress = {
        30: {
            "started": 0,
            "trace": 0,
            "future": 0,
            "full": 0,
            "instance_ids": set(),
        },
        50: {
            "started": 0,
            "trace": 0,
            "future": 0,
            "full": 0,
            "instance_ids": set(),
        },
    }
    pair_kinds: Counter[str] = Counter()
    supervision_totals: Counter[str] = Counter()
    index_payload = cache.small_json(
        run_root / "qg2_clean_v2_live_snapshot_index.json"
    )
    coverage = _index_coverage(index_payload)
    instance_by_state = _index_instance_by_state(index_payload)
    selected_state_prefixes = _bounded_selected_state_prefixes(
        index_payload,
        maximum=maximum_contexts,
        per_scale=maximum_contexts_per_scale,
    )
    binding_census = _snapshot_binding_census(
        index_payload,
        selected_state_prefixes=selected_state_prefixes,
        cache=cache,
    )

    for context_dir in sorted(oracle_dir.glob("[0-9][0-9]_*")):
        if not context_dir.is_dir():
            continue
        try:
            scale = int(context_dir.name.split("_", 1)[0])
        except (ValueError, IndexError):
            continue
        if scale not in progress:
            continue
        state_prefix = context_dir.name.split("_", 1)[1]
        if (
            selected_state_prefixes is not None
            and (scale, state_prefix) not in selected_state_prefixes
        ):
            continue
        q0_trace = context_dir / "q0_trace.json"
        potential_path = context_dir / "qo2_leaked_potential.json"
        _record_started_context(
            progress,
            scale=scale,
            state_prefix=state_prefix,
            instance_by_state=instance_by_state,
            q0_trace_exists=q0_trace.is_file(),
        )
        potential = cache.potential(potential_path)
        if potential is not None:
            progress[scale]["future"] += 1
        arms = {
            name: cache.replay(context_dir / filename)
            for name, filename in ARM_FILES.items()
        }
        if any(value is None for value in arms.values()):
            control = arms["Q0"]
            q0_wall = _wall(control)
            if (
                control is not None
                and q0_wall is not None
                and q0_wall > 0.0
                and bool(control.get("milestone_reached"))
            ):
                completed = []
                order_time = 0.0
                for name, filename in ARM_FILES.items():
                    value = arms[name]
                    path = context_dir / filename
                    if value is None:
                        continue
                    if path.is_file():
                        order_time = max(order_time, path.stat().st_mtime)
                    wall = (
                        q0_wall
                        if name == "Q0"
                        else _comparison_wall(value, q0_wall=q0_wall)
                    )
                    completed.append({
                        "arm": name,
                        "milestone": str(value.get("milestone_kind") or ""),
                        "milestone_reached": bool(
                            value.get("milestone_reached")
                        ),
                        "wall": wall,
                        "ratio": (
                            wall / q0_wall if wall is not None else None
                        ),
                        "raw_negative": int(
                            value.get("raw_unique_negative_count") or 0
                        ),
                        "master_ready": int(
                            value.get("selected_master_ready_negative_count")
                            or value.get("selected_diverse_negative_count")
                            or 0
                        ),
                        "processed_labels": int(
                            dict(value.get("proof_telemetry") or {}).get(
                                "processed_labels"
                            )
                            or 0
                        ),
                        "extended_labels": int(
                            dict(value.get("proof_telemetry") or {}).get(
                                "extended_labels"
                            )
                            or 0
                        ),
                        "safe": _partial_arm_safe(control, value),
                    })
                partial_contexts.append({
                    "order_time": order_time,
                    "scale": scale,
                    "state": state_prefix,
                    "completed": completed,
                })
            continue
        control = arms["Q0"]
        assert control is not None
        q0_wall = _wall(control)
        if (
            q0_wall is None
            or q0_wall <= 0.0
            or not bool(control.get("milestone_reached"))
        ):
            continue
        progress[scale]["full"] += 1
        comparison_walls = {
            name: _comparison_wall(value, q0_wall=q0_wall)
            for name, value in arms.items()
            if value is not None
        }
        ratios = {
            name: wall / q0_wall
            for name, wall in comparison_walls.items()
            if name != "Q0" and wall is not None
        }
        safe = all(
            _ordering_safe(control, value)
            for value in arms.values()
            if value is not None
        )
        trace_mtime = q0_trace.stat().st_mtime if q0_trace.is_file() else 0.0
        row = {
            "order_time": trace_mtime,
            "scale": scale,
            "state": state_prefix,
            "instance_id": str(control.get("instance_id") or ""),
            "instance_hash": str(
                control.get("instance_content_hash")
                or control.get("instance_hash")
                or control.get("instance_id")
                or ""
            ),
            "milestone": str(control.get("milestone_kind") or ""),
            "q0_wall": q0_wall,
            "walls": {
                name: wall
                for name, wall in comparison_walls.items()
                if wall is not None
            },
            "ratios": ratios,
            "right_censored_arms": sorted(
                name
                for name, value in arms.items()
                if name != "Q0"
                and value is not None
                and not bool(value.get("milestone_reached"))
            ),
            "safe": safe,
        }
        contexts.append(row)
        if potential is not None:
            supervision = dict(potential.get("supervision") or {})
            pair_kinds.update(supervision.get("pair_kind_counts") or {})
            for key in (
                "action_reachable_pair_count",
                "selected_master_ready_solution_count",
                "omitted_raw_negative_solution_count",
                "selected_admission_ancestor_count",
                "hard_negative_ancestor_count",
                "proof_terminal_parent_count",
                "proof_terminal_parent_pair_count",
            ):
                supervision_totals[key] += int(supervision.get(key) or 0)

    contexts.sort(key=lambda row: (row["order_time"], row["state"]))
    metrics = _arm_metrics(contexts)
    bucket_metrics = {
        arm: _bucket_metrics(contexts, arm) for arm in BUCKET_ARMS
    }
    bucket_metrics_by_scale = {
        scale: {
            arm: _bucket_metrics(
                [row for row in contexts if row["scale"] == scale], arm
            )
            for arm in BUCKET_ARMS
        }
        for scale in (30, 50)
    }
    concentration_by_arm = {
        arm: _saved_wall_concentration(contexts, arm) for arm in BUCKET_ARMS
    }
    split_projection = _instance_split_projection(contexts)
    supplemental_projection = _supplemental_pool_projection(
        contexts, index_payload
    )
    for scale in (30, 50):
        progress[scale]["instances"] = len(progress[scale].pop("instance_ids"))
    controllers = {
        label: cache.small_json(run_root / relative)
        for label, relative in CONTROLLER_STATES.items()
    }
    artifacts = {
        label: _artifact_row(run_root / relative, cache)
        for label, relative in PIPELINE_ARTIFACTS.items()
    }
    fresh_calibration = _collect_fresh_calibration_progress(
        run_root=run_root,
        cache=cache,
    )
    latest_audit = _latest_completion_audit(run_root, cache)
    oracle_summary = cache.small_json(
        run_root / "oracle_qg2_action_surface_v2_stage1.json"
    )
    frozen_bucket = (oracle_summary or {}).get(
        "frozen_guidance_bucket_width"
    )
    relaxed_gate_arm = _bucket_arm_from_width(frozen_bucket)
    relaxed_gate_frozen = relaxed_gate_arm is not None
    if relaxed_gate_arm is None:
        # Development-only preview while the bounded Oracle is still running.
        relaxed_gate_arm = "QO2-1e-3"
    measured_portfolio = cache.small_json(
        run_root / "qg2_measured_portfolio_oracle_live.json"
    )
    current_child = _current_child(oracle_pid)
    replicate_q0 = tuple(sorted(oracle_dir.glob("*/q0_*_rep*.json")))
    replicate_pairs = tuple(
        path
        for path in replicate_q0
        if path.with_name(path.name.replace("q0_", "qo2_", 1)).is_file()
    )
    replicate_bucket_arm = _replicate_bucket_arm(
        replicate_q0=replicate_q0,
        current_child=current_child,
        frozen_bucket=frozen_bucket,
    )
    replicate_expected_contexts = [
        row
        for row in contexts
        if replicate_bucket_arm in row["ratios"]
        and bool(row["safe"])
        and float(row["ratios"][replicate_bucket_arm]) < 1.0
    ] if replicate_bucket_arm else []
    initial_started = sum(
        progress[scale]["started"] for scale in (30, 50)
    )
    bounded_limit = int(
        maximum_contexts
        or (index_payload or {}).get("bounded_oracle_context_limit")
        or 0
    )
    oracle_phase = _oracle_phase(
        oracle_summary=oracle_summary,
        replicate_started=bool(replicate_q0),
        current_child=current_child,
        initial_started=initial_started,
        bounded_limit=bounded_limit,
    )
    return {
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "maintainer_pid": os.getpid(),
        "run_root": run_root,
        "oracle_dir": oracle_dir,
        "oracle_pid": oracle_pid,
        "oracle_alive": _pid_alive(oracle_pid),
        "watched_pids": watched_pids,
        "watched_alive": [pid for pid in watched_pids if _pid_alive(pid)],
        "current_child": current_child,
        "coverage": coverage,
        "binding_census": binding_census,
        "bounded_context_limit": bounded_limit,
        "oracle_phase": oracle_phase,
        "blocked_replicate_started_count": len(replicate_q0),
        "blocked_replicate_pair_count": len(replicate_pairs),
        "blocked_replicate_context_count": len({
            path.parent.name for path in replicate_pairs
        }),
        "blocked_replicate_bucket_arm": replicate_bucket_arm,
        "blocked_replicate_expected_context_count": len(
            replicate_expected_contexts
        ),
        "blocked_replicate_expected_pair_count": (
            3 * len(replicate_expected_contexts)
        ),
        "progress": progress,
        "partial_context": (
            max(partial_contexts, key=lambda row: row["order_time"])
            if partial_contexts else None
        ),
        "contexts": contexts,
        "metrics": metrics,
        "bucket_metrics": bucket_metrics,
        "bucket_metrics_by_scale": bucket_metrics_by_scale,
        "concentration": concentration_by_arm.get(relaxed_gate_arm),
        "concentration_by_arm": concentration_by_arm,
        "relaxed_gate_arm": relaxed_gate_arm,
        "relaxed_gate_frozen": relaxed_gate_frozen,
        "oracle_summary": oracle_summary,
        "split_projection": split_projection,
        "supplemental_projection": supplemental_projection,
        "pair_kinds": dict(sorted(pair_kinds.items())),
        "supervision_totals": dict(supervision_totals),
        "controllers": controllers,
        "artifacts": artifacts,
        "fresh_calibration": fresh_calibration,
        "latest_audit": latest_audit,
        "measured_portfolio": measured_portfolio,
    }


def _oracle_phase(
    *,
    oracle_summary: dict[str, Any] | None,
    replicate_started: bool,
    current_child: dict[str, Any] | None,
    initial_started: int,
    bounded_limit: int,
) -> str:
    if oracle_summary:
        return "ORACLE_SUMMARY_FROZEN"
    if replicate_started or (
        current_child and "_rep" in str(current_child)
    ):
        return "BLOCKED_REPLICATES"
    # Starting the bounded-limit-th context is not the same as completing its
    # Q0 trace and all initial arms.  An active non-replicate child is still
    # part of the initial screen even when initial_started == bounded_limit.
    if current_child:
        return "INITIAL_SCREEN"
    if bounded_limit and initial_started >= bounded_limit:
        return "INITIAL_SCREEN_COMPLETE_PENDING_REPLICATES"
    return "INITIAL_SCREEN"


def _replicate_bucket_arm(
    *,
    replicate_q0: tuple[Path, ...],
    current_child: dict[str, Any] | None,
    frozen_bucket: object,
) -> str | None:
    """Resolve the Oracle-frozen bucket from summary or replicate filenames."""

    arm = _bucket_arm_from_width(frozen_bucket)
    if arm is not None:
        return arm
    candidates = [path.name for path in replicate_q0]
    if current_child:
        candidates.append(Path(str(current_child.get("output") or "")).name)
    for name in candidates:
        match = re.fullmatch(r"(?:q0|qo2)_([^_]+)_rep\d+\.json", name)
        if not match:
            continue
        try:
            arm = _bucket_arm_from_width(float(match.group(1)))
        except ValueError:
            continue
        if arm is not None:
            return arm
    return None


def _record_started_context(
    progress: dict[int, dict[str, Any]],
    *,
    scale: int,
    state_prefix: str,
    instance_by_state: dict[tuple[int, str], str],
    q0_trace_exists: bool,
) -> None:
    progress[scale]["started"] += 1
    if q0_trace_exists:
        progress[scale]["trace"] += 1
    instance_id = instance_by_state.get((scale, state_prefix))
    if instance_id:
        progress[scale]["instance_ids"].add(instance_id)


def _latest_completion_audit(
    run_root: Path,
    cache: ProjectionCache,
) -> dict[str, Any] | None:
    for relative in COMPLETION_AUDIT_CANDIDATES:
        payload = cache.small_json(run_root / relative)
        if payload:
            return payload
    return None


def render_markdown(report: dict[str, Any]) -> str:
    contexts = list(report["contexts"])
    progress = report["progress"]
    lines = [
        "# P0V5 QG2 Action-Surface V2 实时结果",
        "",
        "> 本文件由 `scripts/maintain_p0v5_qg2_live_markdown.py` 自动生成；请勿手工编辑。",
        "> 当前 QO2 是使用完整未来 trace 的 development-only leaked reachable oracle，",
        "> 不是已训练 GAT 的正式性能。所有 live 指标只用于进度诊断，正式 gate 以冻结 summary/audit 为准。",
        "",
        f"- 更新时间：`{report['updated_at']}`",
        f"- Oracle PID：`{report['oracle_pid']}`（{'alive' if report['oracle_alive'] else 'not alive'}）",
        f"- Markdown维护器PID：`{report['maintainer_pid']}`",
        f"- 监控终止目标finalizer PID：`{', '.join(map(str, report['watched_pids'])) or 'none'}`",
        f"- 已完整计时 context：`{len(contexts)}`",
        (
            f"- Oracle阶段：`{report['oracle_phase']}`；blocked replicate "
            f"已完成 `{report['blocked_replicate_pair_count']}"
            f"/{report.get('blocked_replicate_expected_pair_count') or '—'}` 对，覆盖 "
            f"`{report['blocked_replicate_context_count']}"
            f"/{report.get('blocked_replicate_expected_context_count') or '—'}` 个context"
        ),
        (
            f"- 当前进度：已运行 `{sum(progress[scale]['started'] for scale in (30, 50))}"
            f"/{report.get('bounded_context_limit') or '—'}` 个fallback context，"
            f"来自 `{sum(progress[scale]['instances'] for scale in (30, 50))}` 个不同实例"
            f"（scale30：{progress[30]['started']} context/{progress[30]['instances']}实例；"
            f"scale50：{progress[50]['started']} context/{progress[50]['instances']}实例）；"
            f"其中 `{len(contexts)}` 个context已完成全部initial arms。"
        ),
        "",
        "## 当前执行状态",
        "",
        "| 项目 | scale30 | scale50 |",
        "|---|---:|---:|",
        f"| Snapshot池 | {report['coverage'].get(30, {}).get('contexts', 0)} | {report['coverage'].get(50, {}).get('contexts', 0)} |",
        f"| 覆盖实例 | {report['coverage'].get(30, {}).get('instances', 0)} | {report['coverage'].get(50, {}).get('instances', 0)} |",
        f"| 已生成Q0 trace | {progress[30]['trace']} | {progress[50]['trace']} |",
        f"| Q0 trace可拟合future potential | {progress[30]['future']} | {progress[50]['future']} |",
        f"| Q0 trace不可拟合/待生成（主要right-censored） | {max(0, progress[30]['started'] - progress[30]['future'])} | {max(0, progress[50]['started'] - progress[50]['future'])} |",
        f"| 完成全部initial arms | {progress[30]['full']} | {progress[50]['full']} |",
        "",
    ]
    child = report.get("current_child") or {}
    lines.extend([
        "### 当前Native arm",
        "",
        "| PID | Context | Policy/输出 | 状态 |",
        "|---:|---|---|---|",
        (
            f"| {child.get('pid', '—')} | {_escape(child.get('context', '—'))} | "
            f"{_escape(child.get('policy', '—'))} | "
            f"{'running' if child else 'idle/waiting'} |"
        ),
    ])
    lines.extend(_render_partial_context(report))
    lines.extend([
        "## Bucket累计统计",
        "",
        "`ratio = arm wall / Q0 wall`；小于1表示加速。",
        "",
        "| Bucket | Context | 正收益 | 至少快5% | 获益实例 | GM ratio | GM变化 | Bootstrap 95%上界 | Exact-safe |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ])
    for arm in BUCKET_ARMS:
        row = report["bucket_metrics"][arm]
        lines.append(
            f"| {BUCKET_LABELS[arm]} | {row['context_count']} | "
            f"{row['positive_context_count']} | {row['gain_5pct_context_count']} | "
            f"{row['gain_5pct_instance_count']} | {_fmt(row['gm'])} | "
            f"{_change(row['gm'])} | {_fmt(row['bootstrap_upper'])} | "
            f"{'yes' if row['all_safe'] else 'NO'} |"
        )
    lines.extend([
        "",
        f"- `{BUCKET_LABELS[report.get('relaxed_gate_arm', 'QO2-1e-3')]}` 当前收益集中度：`{_pct(report['concentration'])}`；relaxed上限为35%。",
        f"- 全局训练授权：`{'PENDING scale50' if progress[50]['full'] == 0 else '以最终Oracle summary为准'}`。",
    ])
    lines.extend(_render_bucket_scale_decomposition(report))
    lines.extend(_render_relaxed_gate(report))
    lines.extend(_render_training_only_v2_gate(report))
    lines.extend([
        "",
        "## 所有arm累计对比",
        "",
        "| Arm | 全部GM | GM变化 | 正收益 | 至少快5% | Admission GM | Proof GM | 总wall差 | 最好ratio | 最差ratio |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for arm in ARM_FILES:
        if arm == "Q0":
            continue
        row = report["metrics"].get(arm, {})
        lines.append(
            f"| {arm} | {_fmt(row.get('gm'))} | {_change(row.get('gm'))} | "
            f"{row.get('positive', 0)}/{row.get('count', 0)} | "
            f"{row.get('gain5', 0)}/{row.get('count', 0)} | "
            f"{_fmt(row.get('admission_gm'))} | {_fmt(row.get('proof_gm'))} | "
            f"{_signed_seconds(row.get('wall_delta'))} | "
            f"{_fmt(row.get('minimum'))} | {_fmt(row.get('maximum'))} |"
        )
    lines.extend(_render_scale50_fixed_arm_pilot(report))
    lines.extend(_render_milestone_breakdown(report))
    lines.extend(_render_measured_portfolio(report))
    lines.extend(_render_supervision(report))
    lines.extend(_render_binding_census(report))
    lines.extend(_render_split_projection(report))
    lines.extend(_render_bucket_contexts(contexts))
    lines.extend(_render_other_contexts(contexts))
    lines.extend(_render_fresh_calibration(report))
    lines.extend(_render_pipeline(report))
    lines.extend(_render_tests(report))
    return "\n".join(lines).rstrip() + "\n"


def _render_bucket_scale_decomposition(report: dict[str, Any]) -> list[str]:
    by_scale = dict(report.get("bucket_metrics_by_scale") or {})
    result = [
        "",
        "### Bucket按规模分解（固定arm，不做事后逐context选择）",
        "",
        "| Scale | Bucket | Context | GM ratio | Bootstrap 95%上界 | 至少快5% | 获益实例 | Exact-safe |",
        "|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for scale in (30, 50):
        rows = dict(by_scale.get(scale) or by_scale.get(str(scale)) or {})
        for arm in BUCKET_ARMS:
            metrics = dict(rows.get(arm) or {})
            result.append(
                f"| {scale} | {BUCKET_LABELS[arm]} | "
                f"{int(metrics.get('context_count') or 0)} | "
                f"{_fmt(metrics.get('gm'))} | "
                f"{_fmt(metrics.get('bootstrap_upper'))} | "
                f"{int(metrics.get('gain_5pct_context_count') or 0)} | "
                f"{int(metrics.get('gain_5pct_instance_count') or 0)} | "
                f"{'yes' if metrics.get('all_safe') else 'NO'} |"
            )
    result.extend([
        "",
        "- 该表用于识别scale异质性；正式运行仍只能使用Oracle结束后冻结的bucket策略。",
    ])
    return result


def _render_scale50_fixed_arm_pilot(report: dict[str, Any]) -> list[str]:
    rows = [row for row in report.get("contexts", ()) if row["scale"] == 50]
    result = [
        "",
        "## Scale50固定arm pilot（非事后选择）",
        "",
        "这里每一行都是同一个固定arm相对Q0的结果；right-censored按matched budget有效wall计入。",
        "",
        "| Arm | Context | 达到同里程碑 | GM ratio | 正收益 | 至少快5% | 最差ratio |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for arm in (
        "QD1",
        "QB1",
        "Random61635",
        "Random91267",
        "Random170141",
        "QO2-1e-4",
        "QO2-3e-4",
        "QO2-1e-3",
    ):
        arm_rows = [row for row in rows if arm in row["ratios"]]
        ratios = [row["ratios"][arm] for row in arm_rows]
        reached = sum(
            arm not in row.get("right_censored_arms", ()) for row in arm_rows
        )
        result.append(
            f"| {arm} | {len(arm_rows)} | {reached}/{len(arm_rows)} | "
            f"{_fmt(_geomean(ratios))} | "
            f"{sum(value < 1.0 for value in ratios)}/{len(ratios)} | "
            f"{sum(value <= 0.95 for value in ratios)}/{len(ratios)} | "
            f"{_fmt(max(ratios) if ratios else None)} |"
        )
    result.extend([
        "",
        "- 该表不是portfolio oracle：不会逐context选择最快arm。",
        "- 当前样本少且可能只覆盖Admission；达到20个pilot前不据此修改冻结动作面。",
    ])
    return result


def _render_partial_context(report: dict[str, Any]) -> list[str]:
    row = report.get("partial_context") or {}
    if not row:
        return [""]
    result = [
        "",
        "### 当前context已完成arm（尚未进入累计统计）",
        "",
        (
            f"`scale{int(row.get('scale') or 0)}/{_escape(row.get('state', ''))}`；"
            "只有全部initial arms结束后才进入GM和gate。"
        ),
        "",
        (
            "| Arm | 里程碑 | 比较wall | ratio | Raw negative | "
            "Master-ready | Processed labels | Extended labels | Safe |"
        ),
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for arm in row.get("completed", ()):
        milestone = str(arm.get("milestone") or "")
        if not bool(arm.get("milestone_reached")):
            milestone = milestone or "RIGHT_CENSORED"
        result.append(
            f"| {arm.get('arm', '—')} | {_escape(milestone)} | "
            f"{_seconds(arm.get('wall'))} | {_fmt(arm.get('ratio'))} | "
            f"{int(arm.get('raw_negative') or 0)} | "
            f"{int(arm.get('master_ready') or 0)} | "
            f"{int(arm.get('processed_labels') or 0):,} | "
            f"{int(arm.get('extended_labels') or 0):,} | "
            f"{'yes' if arm.get('safe') else 'NO'} |"
        )
    return result + [""]


def _render_relaxed_gate(report: dict[str, Any]) -> list[str]:
    by_scale = dict(report.get("bucket_metrics_by_scale") or {})
    arm = str(report.get("relaxed_gate_arm") or "QO2-1e-3")
    bucket = BUCKET_LABELS.get(arm, arm)
    frozen = bool(report.get("relaxed_gate_frozen"))
    result = [
        "",
        f"### `{bucket}` {'frozen' if frozen else 'provisional'} relaxed training gate（按scale）",
        "",
        "| Scale | Context | 至少快5% | 获益实例 | GM | Bootstrap 95%上界 | Exact-safe | 数字门槛 |",
        "|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    scale_passes = []
    for scale in (30, 50):
        metrics = dict(
            (by_scale.get(scale) or by_scale.get(str(scale)) or {}).get(
                arm, {}
            )
        )
        passed = _relaxed_scale_gate(metrics)
        scale_passes.append(passed)
        result.append(
            f"| {scale} | {int(metrics.get('context_count') or 0)}/20 | "
            f"{int(metrics.get('gain_5pct_context_count') or 0)}/5 | "
            f"{int(metrics.get('gain_5pct_instance_count') or 0)}/5 | "
            f"{_fmt(metrics.get('gm'))}/0.9500 | "
            f"{_fmt(metrics.get('bootstrap_upper'))}/0.9800 | "
            f"{'yes' if metrics.get('all_safe') else 'NO'} | "
            f"{'PASS' if passed else 'NOT YET'} |"
        )
    concentration = report.get("concentration")
    global_numeric = bool(
        all(scale_passes)
        and concentration is not None
        and float(concentration)
        <= RELAXED_THRESHOLDS["maximum_instance_saved_wall_fraction"]
    )
    result.extend([
        "",
        f"- 当前{'冻结' if frozen else '预览'}数字组合：`{'PASS' if global_numeric else 'NOT YET'}`；最终训练授权只能来自冻结Oracle summary和独立relaxed gate artifact。",
        *(
            []
            if frozen
            else [
                "- bounded Oracle尚未冻结bucket；当前`1e-3`只用于实时诊断，不能预判最终选中的bucket或训练授权。"
            ]
        ),
        "- relaxed gate只允许开始模型比较，不降低calibration、harmful-action、heldout或E2E部署门槛。",
    ])
    return result


def _render_training_only_v2_gate(report: dict[str, Any]) -> list[str]:
    by_scale = dict(report.get("bucket_metrics_by_scale") or {})
    arm = str(report.get("relaxed_gate_arm") or "QO2-1e-3")
    bucket = BUCKET_LABELS.get(arm, arm)
    frozen = bool(report.get("relaxed_gate_frozen"))
    result = [
        "",
        f"### `{bucket}` {'frozen' if frozen else 'provisional'} training-only V2 数据门（按scale）",
        "",
        "> 固定arm GM和bootstrap仅报告，不否决 selective model fitting；部署门槛不变。",
        "",
        "| Scale | Context | 实例 | 至少快5% | 获益实例 | Nonpositive | Harmful实例 | Exact-safe | 数据门 |",
        "|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    scale_passes = []
    for scale in (30, 50):
        metrics = dict(
            (by_scale.get(scale) or by_scale.get(str(scale)) or {}).get(
                arm, {}
            )
        )
        passed = _training_only_v2_scale_gate(metrics)
        scale_passes.append(passed)
        result.append(
            f"| {scale} | {int(metrics.get('context_count') or 0)}/20 | "
            f"{int(metrics.get('instance_count') or 0)}/10 | "
            f"{int(metrics.get('gain_5pct_context_count') or 0)}/5 | "
            f"{int(metrics.get('gain_5pct_instance_count') or 0)}/5 | "
            f"{int(metrics.get('nonpositive_context_count') or 0)}/5 | "
            f"{int(metrics.get('harmful_instance_count') or 0)}/3 | "
            f"{'yes' if metrics.get('all_safe') else 'NO'} | "
            f"{'PASS' if passed else 'NOT YET'} |"
        )
    concentration = report.get("concentration")
    global_pass = bool(
        all(scale_passes)
        and concentration is not None
        and float(concentration) <= TRAINING_ONLY_V2_THRESHOLDS[
            "maximum_instance_saved_wall_fraction"
        ]
    )
    result.extend([
        "",
        f"- 当前{'冻结' if frozen else '预览'} training-only V2 数据组合：`{'PASS' if global_pass else 'NOT YET'}`。",
        "- 只有最终Oracle summary、exact-safe/binding与独立training-only gate artifact才能正式启动训练。",
        "- 该门只授权Linear/MLP/Tiny GAT探索性拟合，不授权calibration、部署或论文结论。",
    ])
    return result


def _render_measured_portfolio(report: dict[str, Any]) -> list[str]:
    payload = report.get("measured_portfolio") or {}
    aggregate = dict(payload.get("aggregate") or {})
    result = [
        "",
        "## Measured best-of-arms portfolio（只读诊断）",
        "",
        "该统计只复用已经完成的exact-safe arm，不启动求解；它不是完美queue oracle，也不提供训练授权。",
        "",
        "| Scale/里程碑 | Context | QG2可达GM | Portfolio GM | QG2捕获收益 | 动作面损失 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for key in ("all", "scale30", "scale50", "admission", "proof"):
        row = dict(aggregate.get(key) or {})
        result.append(
            f"| {key} | {int(row.get('context_count') or 0)} | "
            f"{_fmt(row.get('qg2_gm'))} | {_fmt(row.get('portfolio_gm'))} | "
            f"{_pct(row.get('captured_savings_fraction'))} | "
            f"{_signed_seconds(row.get('qg2_action_surface_gap_sec'))} |"
        )
    result.extend([
        "",
        "- `GM`：先逐context计算 `arm wall / Q0 wall`，再取几何平均；小于1才表示加速。",
        "- `QG2可达GM`：Q0与三个QO2 bucket的逐context事后最小值之GM，包含leaked future trace和事后选bucket的乐观偏差。",
        "- `Portfolio GM`：额外纳入QD1/QB1后的逐context事后最小值之GM，用于诊断当前同bucket动作面遗漏的机会。",
        "- `QG2捕获收益`：`(Q0总wall-QG2总wall)/(Q0总wall-Portfolio总wall)`，不是GAT预测准确率。",
        "- `动作面损失`：`QG2总wall-Portfolio总wall`；它是当前QG2动作能力的缺口，不是模型误差。",
        "- Random、right-censored、里程碑/绑定不一致和exact-safe失败的arm均不参与。",
        "- QD1/QB1赢家不能直接转换成当前QG2的逐label训练标签。",
    ])
    return result


def _render_milestone_breakdown(report: dict[str, Any]) -> list[str]:
    contexts = report["contexts"]
    result = [
        "",
        "## `w=1e-3`按里程碑拆分",
        "",
        "| 里程碑 | Context | Q0总wall | QO2总wall | 总wall差 | GM ratio | 正收益 | 至少快5% | 退化至少5% |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for milestone, label in (
        ("ADMISSION_BATCH_READY", "Admission"),
        ("EXACT_PROOF_COMPLETION", "Exact proof"),
    ):
        rows = [row for row in contexts if row["milestone"] == milestone]
        ratios = [row["ratios"]["QO2-1e-3"] for row in rows]
        q0 = sum(row["q0_wall"] for row in rows)
        arm = sum(row["walls"]["QO2-1e-3"] for row in rows)
        result.append(
            f"| {label} | {len(rows)} | {q0:.2f}s | {arm:.2f}s | "
            f"{_signed_seconds(arm - q0)} | {_fmt(_geomean(ratios))} | "
            f"{sum(value < 1.0 for value in ratios)} | "
            f"{sum(value <= 0.95 for value in ratios)} | "
            f"{sum(value >= 1.05 for value in ratios)} |"
        )
    return result


def _render_supervision(report: dict[str, Any]) -> list[str]:
    kinds = report["pair_kinds"]
    totals = report["supervision_totals"]
    labels = {
        "admission_ancestor_vs_omitted_negative": (
            "Admission selected ancestor vs omitted raw-negative ancestor"
        ),
        "admission_ancestor": "Admission ancestor vs background",
        "existing_dominator": "Existing dominator",
        "incoming_dominator": "Incoming dominator",
        "proof_terminal_parent_progress": "Proof terminal-parent progress",
    }
    result = [
        "",
        "## 完整计时context的监督数据",
        "",
        "| Preference类型 | Pair数 |",
        "|---|---:|",
    ]
    for key in (
        "admission_ancestor_vs_omitted_negative",
        "admission_ancestor",
        "existing_dominator",
        "incoming_dominator",
        "proof_terminal_parent_progress",
    ):
        result.append(f"| {labels[key]} | {int(kinds.get(key, 0)):,} |")
    result.extend([
        f"| 合计 | **{sum(int(value) for value in kinds.values()):,}** |",
        "",
        "| Future监督对象 | 数量 |",
        "|---|---:|",
        f"| Selected master-ready routes | {int(totals.get('selected_master_ready_solution_count', 0)):,} |",
        f"| Omitted raw-negative routes | {int(totals.get('omitted_raw_negative_solution_count', 0)):,} |",
        f"| Selected route ancestor labels | {int(totals.get('selected_admission_ancestor_count', 0)):,} |",
        f"| Hard-negative ancestor labels | {int(totals.get('hard_negative_ancestor_count', 0)):,} |",
    ])
    return result


def _render_split_projection(report: dict[str, Any]) -> list[str]:
    projection = dict(report.get("split_projection") or {})
    supplemental = dict(report.get("supplemental_projection") or {})
    result = [
        "",
        "## 训练/校准实例隔离投影",
        "",
        "> 该表按当前已完整 context 临时模拟冻结 trainer 的60/20/20实例级划分；",
        "> Oracle完成后会用最终 trainable context 重新计算，因此这里只用于提前发现统计门槛不可达。",
        "",
        "| Scale | Train context/实例 | Calibration context/实例 | Heldout context/实例 |",
        "|---:|---:|---:|---:|",
    ]
    for scale in (30, 50):
        row = dict(projection.get(f"scale{scale}") or {})
        result.append(
            f"| {scale} | {row.get('train_context_count', 0)}/"
            f"{row.get('train_instance_count', 0)} | "
            f"{row.get('calibration_context_count', 0)}/"
            f"{row.get('calibration_instance_count', 0)} | "
            f"{row.get('heldout_context_count', 0)}/"
            f"{row.get('heldout_instance_count', 0)} |"
        )
    calibration = int(projection.get("calibration_context_count") or 0)
    required = int(
        projection.get("minimum_calibration_contexts")
        or MINIMUM_CALIBRATION_CONTEXTS_FOR_HARMFUL_GATE
    )
    shortfall = max(0, required - calibration)
    result.extend([
        "",
        f"- 当前投影 calibration context：`{calibration}/{required}`；"
        f"尚缺 `{shortfall}`。",
        "- 52来自零 harmful action 时单侧95% Wilson上界不超过5%的最小样本量；"
        "relaxed gate只允许先训练，不会降低正式部署风险门槛。",
        (
            "- 当前冻结 snapshot 池的临时可达上限：calibration "
            f"`{int(supplemental.get('calibration_context_count') or 0)}`，"
            "heldout "
            f"`{int(supplemental.get('heldout_context_count') or 0)}`；"
            f"状态为 `{supplemental.get('status') or 'unavailable'}`。"
        ),
        "- supplemental contexts只用于fresh-process calibration/heldout，"
        "不会加入训练；最终数量仍以Oracle完成后的冻结split为准。",
    ])
    return result


def _render_bucket_contexts(contexts: list[dict[str, Any]]) -> list[str]:
    result = [
        "",
        "## 逐context：三个QO2 bucket",
        "",
        "| # | Scale | 实例 | State | 里程碑 | Q0(s) | 1e-4 秒/ratio | 3e-4 秒/ratio | 1e-3 秒/ratio | 三者最佳 | Safe |",
        "|---:|---:|---|---|---|---:|---:|---:|---:|---|---|",
    ]
    for index, row in enumerate(contexts, 1):
        values = [(arm, row["walls"][arm]) for arm in BUCKET_ARMS]
        best_arm, _best_wall = min(values, key=lambda item: item[1])
        result.append(
            f"| {index} | {row['scale']} | {_escape(_short_instance(row['instance_id']))} | "
            f"{row['state'][:8]} | {_milestone(row['milestone'], row['scale'])} | "
            f"{row['q0_wall']:.2f} | "
            f"{row['walls']['QO2-1e-4']:.2f}/{row['ratios']['QO2-1e-4']:.3f} | "
            f"{row['walls']['QO2-3e-4']:.2f}/{row['ratios']['QO2-3e-4']:.3f} | "
            f"{row['walls']['QO2-1e-3']:.2f}/{row['ratios']['QO2-1e-3']:.3f} | "
            f"{BUCKET_LABELS[best_arm]} | {'yes' if row['safe'] else 'NO'} |"
        )
    return result


def _render_other_contexts(contexts: list[dict[str, Any]]) -> list[str]:
    result = [
        "",
        "## 逐context：Handcrafted与Random ratio",
        "",
        "| # | 实例 | 里程碑 | Q0(s) | QD1 | QB1 | R61635 | R91267 | R170141 |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(contexts, 1):
        result.append(
            f"| {index} | {_escape(_short_instance(row['instance_id']))} | "
            f"{_milestone(row['milestone'], row['scale'])} | {row['q0_wall']:.2f} | "
            f"{row['ratios']['QD1']:.3f} | {row['ratios']['QB1']:.3f} | "
            f"{row['ratios']['Random61635']:.3f} | "
            f"{row['ratios']['Random91267']:.3f} | "
            f"{row['ratios']['Random170141']:.3f} |"
        )
    return result


def _render_binding_census(report: dict[str, Any]) -> list[str]:
    census = dict(report.get("binding_census") or {})
    result = [
        "",
        "## Pre-action feature binding census",
        "",
        "> 统计 bounded Oracle 预选 snapshot；只检查干预前真实字段和显式missingness，不把缺失值补成零。",
        "",
        "| 项目 | scale30 | scale50 |",
        "|---|---:|---:|",
    ]
    rows = (
        ("预选snapshot", "snapshot_count"),
        ("结构绑定完整", "structural_binding_complete_count"),
        ("active-column incidence完整", "active_column_binding_complete_count"),
        ("round存在", "round_present_count"),
        ("previous-proof可用", "previous_proof_present_count"),
        ("previous-proof显式缺失", "previous_proof_missing_count"),
        ("dual-delta可用", "dual_delta_present_count"),
        ("root/tree", "root_count", "tree_count"),
        ("active branch/cut", "active_branch_count", "active_cut_count"),
        ("snapshot不可读", "unreadable_count"),
    )
    for row in rows:
        label = row[0]
        values = []
        for scale in (30, 50):
            current = dict(census.get(scale) or census.get(str(scale)) or {})
            if len(row) == 2:
                values.append(str(int(current.get(row[1]) or 0)))
            else:
                values.append(
                    f"{int(current.get(row[1]) or 0)}/"
                    f"{int(current.get(row[2]) or 0)}"
                )
        result.append(f"| {label} | {values[0]} | {values[1]} |")
    result.extend([
        "",
        "- `previous-proof` 在首次proof或此前未执行proof时允许为缺失；模型通过presence feature区分，不能解释为真实零。",
        "- active branch/cut 是数据覆盖诊断，不是结构绑定通过条件；未覆盖context在部署时仍受OOD/no-op门保护。",
    ])
    return result


def _collect_fresh_calibration_progress(
    *,
    run_root: Path,
    cache: ProjectionCache,
) -> dict[str, Any]:
    """Project the active fresh-process run without reading solver internals."""

    calibration_root = run_root / FRESH_CALIBRATION_DIR
    manifest = cache.small_json(run_root / FRESH_CALIBRATION_MANIFEST) or {}
    combined = dict(manifest.get("combined_counts") or {})
    rows: list[dict[str, Any]] = []
    for model in FRESH_CALIBRATION_MODELS:
        for partition in ("calibration", "heldout"):
            for scale in (30, 50):
                expected = int(
                    combined.get(
                        f"scale{scale}_{partition}_context_count"
                    )
                    or 0
                )
                context_dirs = tuple(sorted(
                    (calibration_root / model / partition).glob(
                        f"{scale}_*"
                    )
                ))
                started = 0
                finalized = 0
                vetoed = 0
                completed_pairs = 0
                for context_dir in context_dirs:
                    potential_path = context_dir / "potential.json"
                    if not potential_path.is_file():
                        continue
                    started += 1
                    potential = cache.small_json(potential_path) or {}
                    veto = bool(potential.get("runtime_prethreshold_veto"))
                    vetoed += int(veto)
                    q0_repeats = {
                        match.group(1)
                        for path in context_dir.glob("q0_*_rep*.json")
                        if (match := re.search(r"_rep(\d+)\.json$", path.name))
                    }
                    qg2_repeats = {
                        match.group(1)
                        for path in context_dir.glob("qg2_*_rep*.json")
                        if (match := re.search(r"_rep(\d+)\.json$", path.name))
                    }
                    pair_count = len(q0_repeats.intersection(qg2_repeats))
                    completed_pairs += pair_count
                    finalized += int(veto or pair_count >= 3)
                rows.append({
                    "model": model,
                    "partition": partition,
                    "scale": scale,
                    "expected_contexts": expected,
                    "started_contexts": started,
                    "finalized_contexts": finalized,
                    "vetoed_contexts": vetoed,
                    "completed_pairs": completed_pairs,
                })
    expected_total = sum(row["expected_contexts"] for row in rows)
    return {
        "root": str(calibration_root),
        "manifest_present": bool(manifest),
        "report_present": (
            calibration_root / "calibration_report.json"
        ).is_file(),
        "rows": rows,
        "expected_contexts": expected_total,
        "started_contexts": sum(row["started_contexts"] for row in rows),
        "finalized_contexts": sum(row["finalized_contexts"] for row in rows),
        "completed_pairs": sum(row["completed_pairs"] for row in rows),
        "vetoed_contexts": sum(row["vetoed_contexts"] for row in rows),
    }


def _render_fresh_calibration(report: dict[str, Any]) -> list[str]:
    progress = dict(report.get("fresh_calibration") or {})
    if not progress.get("manifest_present"):
        return []
    result = [
        "",
        "## Linear / MLP / Tiny GAT fresh-process calibration",
        "",
        (
            f"- 已最终计时 `{int(progress.get('finalized_contexts') or 0)}"
            f"/{int(progress.get('expected_contexts') or 0)}` 个model-context；"
            f"已完成 `{int(progress.get('completed_pairs') or 0)}` 对matched repeats；"
            f"模型外OOD/预阈值回退 `{int(progress.get('vetoed_contexts') or 0)}` 个。"
        ),
        (
            "- 最终汇总："
            + (
                "`calibration_report.json` 已生成。"
                if progress.get("report_present")
                else "仍在运行，尚未生成 `calibration_report.json`。"
            )
        ),
        "",
        "| Model | Split | Scale | 已启动context | 已完成context | OOD/no-op | Matched repeats |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in progress.get("rows") or ():
        result.append(
            f"| {row['model']} | {row['partition']} | {row['scale']} | "
            f"{row['started_contexts']}/{row['expected_contexts']} | "
            f"{row['finalized_contexts']}/{row['expected_contexts']} | "
            f"{row['vetoed_contexts']} | {row['completed_pairs']} |"
        )
    result.extend([
        "",
        "- 这里只统计已原子落盘的potential和Q0/QG2配对结果，不把正在运行的半个repeat计为完成。",
        "- 5%仅保留为报告指标；进入E2E要求calibration与heldout净GM均小于1、selected censor/unsafe为零，并保持Q0 fail-closed。",
    ])
    return result


def _render_pipeline(report: dict[str, Any]) -> list[str]:
    result = [
        "",
        "## 自动流水线状态",
        "",
        "| Controller | 状态 |",
        "|---|---|",
    ]
    for label, payload in report["controllers"].items():
        status = str((payload or {}).get("status") or "missing")
        result.append(f"| {label} | `{_escape(status)}` |")
    result.extend([
        "",
        "| Artifact | 是否存在 | 摘要状态 |",
        "|---|---|---|",
    ])
    for label, row in report["artifacts"].items():
        result.append(
            f"| {label} | {'yes' if row['exists'] else 'no'} | "
            f"`{_escape(row['status'])}` |"
        )
    return result


def _render_tests(report: dict[str, Any]) -> list[str]:
    audit = report.get("latest_audit") or {}
    checks = dict(audit.get("checks") or {})
    regression = dict(
        checks.get("regression_and_native_tests")
        or checks.get("automated_regression_tests")
        or {}
    )
    action = dict(
        checks.get("oracle_and_training_authority")
        or checks.get("action_surface_contract")
        or {}
    )
    return [
        "",
        "## 最近一次正式审计",
        "",
        "| 检查 | 状态 | 说明 |",
        "|---|---|---|",
        f"| Action surface contract | `{action.get('status', 'missing')}` | {_escape(action.get('note', ''))} |",
        f"| Automated regression tests | `{regression.get('status', 'missing')}` | {_escape(regression.get('note', ''))} |",
        f"| Completion audit | `{'complete' if audit.get('complete') else 'incomplete'}` | pass={audit.get('passed_check_count', 0)}, incomplete={audit.get('incomplete_check_count', 0)}, failed={audit.get('failed_check_count', 0)} |",
        "",
        "## 当前结论",
        "",
        "- QO2只证明当前动作面存在reachable ordering opportunity，不是GAT成绩。",
        "- Linear、MLP和Tiny GAT训练已完成；当前正在用fresh-process Q0/QG2三重复校准真实wall，临时单context结果不能替代最终activation gate。",
        "- Random整体退化且QD1/QB1对Admission/Proof呈互补；本轮最终动作仍是QG2或literal Q0，context selector尚未获得运行权限。",
        "- Positive-net路径只允许calibration和heldout净GM为正、censor/unsafe为零的GAT进入E2E；formal full20通过前不冻结候选，任何阶段都不切换production默认。",
    ]


def _project_replay(payload: dict[str, Any]) -> dict[str, Any]:
    telemetry = dict(payload.get("proof_telemetry") or {})
    return {
        key: payload.get(key)
        for key in (
            "instance_id",
            "instance_content_hash",
            "instance_hash",
            "milestone_kind",
            "milestone_reached",
            "milestone_wall_sec",
            "admission_milestone_wall_sec",
            "total_fresh_process_wall_sec",
            "requested_wall_time_limit_sec",
            "search_exhaustive",
            "labels_dropped",
            "can_filter",
            "can_prune",
            "can_change_reduced_cost",
            "can_certify_from_guidance",
            "global_min_rc",
            "proved_no_rc_below",
            "raw_unique_negative_count",
            "selected_diverse_negative_count",
            "selected_master_ready_negative_count",
        )
    } | {
        "proof_telemetry": {
            key: telemetry.get(key)
            for key in (
                "legal_action_universe_hash_before_sort",
                "legal_arc_universe_hash_before_sort",
                "guidance_filter_count",
                "guidance_arc_drop_count",
                "guidance_label_drop_count",
                "guidance_branch_pair_drop_count",
                "processed_labels",
                "extended_labels",
                "dominated_labels",
            )
        }
    }


def _partial_arm_safe(
    control: dict[str, Any],
    arm: dict[str, Any],
) -> bool:
    left = dict(control.get("proof_telemetry") or {})
    right = dict(arm.get("proof_telemetry") or {})
    hash_keys = (
        "legal_action_universe_hash_before_sort",
        "legal_arc_universe_hash_before_sort",
    )
    drop_keys = (
        "guidance_filter_count",
        "guidance_arc_drop_count",
        "guidance_label_drop_count",
        "guidance_branch_pair_drop_count",
    )
    return bool(
        all(left.get(key) and left.get(key) == right.get(key) for key in hash_keys)
        and all(int(right.get(key) or 0) == 0 for key in drop_keys)
        and not bool(arm.get("labels_dropped"))
        and not any(bool(arm.get(key)) for key in (
            "can_filter",
            "can_prune",
            "can_change_reduced_cost",
            "can_certify_from_guidance",
        ))
    )


def _project_potential(payload: dict[str, Any]) -> dict[str, Any]:
    return {"supervision": dict(payload.get("supervision") or {})}


def _wall(row: dict[str, Any] | None) -> float | None:
    if row is None:
        return None
    value = (
        row.get("admission_milestone_wall_sec")
        or row.get("milestone_wall_sec")
        or row.get("total_fresh_process_wall_sec")
    )
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) and numeric > 0.0 else None


def _comparison_wall(
    row: dict[str, Any] | None, *, q0_wall: float
) -> float | None:
    """Return matched-budget wall without rewarding a censored arm.

    The formal Oracle applies the same conservative rule through
    ``_effective_wall``.  If an arm does not reach Q0's milestone, an early
    partial return cannot be interpreted as a speedup; charge at least its
    declared matched budget and at least Q0 wall.
    """
    measured = _wall(row)
    if measured is None or row is None:
        return None
    if bool(row.get("milestone_reached")):
        return measured
    try:
        budget = float(row.get("requested_wall_time_limit_sec"))
    except (TypeError, ValueError):
        budget = 0.0
    if not math.isfinite(budget) or budget <= 0.0:
        budget = 0.0
    return max(measured, budget, float(q0_wall))


def _ordering_safe(control: dict[str, Any], arm: dict[str, Any]) -> bool:
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
            "guidance_filter_count",
            "guidance_arc_drop_count",
            "guidance_label_drop_count",
            "guidance_branch_pair_drop_count",
        )
    )
    exact = True
    if control.get("search_exhaustive") and arm.get("search_exhaustive"):
        exact = _exact_match(control, arm)
    return bool(universe and no_drop and not arm.get("labels_dropped") and exact)


def _exact_match(left: dict[str, Any], right: dict[str, Any]) -> bool:
    if left.get("global_min_rc") is not None and right.get("global_min_rc") is not None:
        return abs(float(left["global_min_rc"]) - float(right["global_min_rc"])) <= 2.0e-6
    if left.get("proved_no_rc_below") is not None and right.get("proved_no_rc_below") is not None:
        return abs(float(left["proved_no_rc_below"]) - float(right["proved_no_rc_below"])) <= 1.0e-12
    return False


def _arm_metrics(contexts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result = {}
    for arm in ARM_FILES:
        if arm == "Q0":
            continue
        rows = [row for row in contexts if arm in row["ratios"]]
        ratios = [row["ratios"][arm] for row in rows]
        admission = [
            row["ratios"][arm]
            for row in rows
            if row["milestone"] == "ADMISSION_BATCH_READY"
        ]
        proof = [
            row["ratios"][arm]
            for row in rows
            if row["milestone"] == "EXACT_PROOF_COMPLETION"
        ]
        result[arm] = {
            "count": len(rows),
            "gm": _geomean(ratios),
            "positive": sum(value < 1.0 for value in ratios),
            "gain5": sum(value <= 0.95 for value in ratios),
            "admission_gm": _geomean(admission),
            "proof_gm": _geomean(proof),
            "minimum": min(ratios) if ratios else None,
            "maximum": max(ratios) if ratios else None,
            "wall_delta": sum(row["walls"][arm] - row["q0_wall"] for row in rows),
        }
    return result


def _bucket_metrics(contexts: list[dict[str, Any]], arm: str) -> dict[str, Any]:
    rows = [row for row in contexts if arm in row["ratios"]]
    ratios = [row["ratios"][arm] for row in rows]
    gain_rows = [row for row in rows if row["ratios"][arm] <= 0.95]
    harmful_rows = [row for row in rows if row["ratios"][arm] >= 1.05]
    return {
        "context_count": len(rows),
        "instance_count": len({row["instance_hash"] for row in rows}),
        "positive_context_count": sum(value < 1.0 for value in ratios),
        "nonpositive_context_count": sum(value >= 1.0 for value in ratios),
        "harmful_context_count": len(harmful_rows),
        "harmful_instance_count": len({
            row["instance_hash"] for row in harmful_rows
        }),
        "gain_5pct_context_count": len(gain_rows),
        "gain_5pct_instance_count": len({row["instance_hash"] for row in gain_rows}),
        "gm": _geomean(ratios),
        "bootstrap_upper": _instance_bootstrap_upper(rows, arm),
        "all_safe": bool(rows) and all(row["safe"] for row in rows),
    }


def _training_only_v2_scale_gate(row: dict[str, Any]) -> bool:
    return bool(
        int(row.get("context_count") or 0)
        >= TRAINING_ONLY_V2_THRESHOLDS[
            "minimum_determined_contexts_per_scale"
        ]
        and int(row.get("instance_count") or 0)
        >= TRAINING_ONLY_V2_THRESHOLDS[
            "minimum_determined_instances_per_scale"
        ]
        and int(row.get("gain_5pct_context_count") or 0)
        >= TRAINING_ONLY_V2_THRESHOLDS[
            "minimum_gain_5pct_contexts_per_scale"
        ]
        and int(row.get("gain_5pct_instance_count") or 0)
        >= TRAINING_ONLY_V2_THRESHOLDS[
            "minimum_positive_instances_per_scale"
        ]
        and int(row.get("nonpositive_context_count") or 0)
        >= TRAINING_ONLY_V2_THRESHOLDS[
            "minimum_nonpositive_contexts_per_scale"
        ]
        and int(row.get("harmful_instance_count") or 0)
        >= TRAINING_ONLY_V2_THRESHOLDS[
            "minimum_harmful_instances_per_scale"
        ]
        and bool(row.get("all_safe"))
    )


def _instance_bootstrap_upper(
    rows: list[dict[str, Any]], arm: str
) -> float | None:
    if not rows:
        return None
    groups: dict[str, list[float]] = {}
    for row in rows:
        groups.setdefault(row["instance_hash"], []).append(row["ratios"][arm])
    keys = sorted(groups)
    rng = random.Random(20260801)
    values = []
    for _ in range(10_000):
        draw = [keys[rng.randrange(len(keys))] for _ in keys]
        values.append(_geomean([value for key in draw for value in groups[key]]))
    values.sort()
    return values[9750]


def _saved_wall_concentration(
    contexts: list[dict[str, Any]], arm: str
) -> float | None:
    saved: dict[str, float] = {}
    for row in contexts:
        value = max(0.0, row["q0_wall"] - row["walls"].get(arm, row["q0_wall"]))
        saved[row["instance_hash"]] = saved.get(row["instance_hash"], 0.0) + value
    total = sum(saved.values())
    return max(saved.values(), default=0.0) / total if total > 0.0 else None


def _instance_split_projection(
    contexts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Mirror the trainer's deterministic instance-level 60/20/20 split."""

    assignments: dict[str, str] = {}
    per_scale: dict[str, dict[str, int]] = {}
    for scale in (30, 50):
        instances = sorted(
            {
                str(row.get("instance_hash") or "")
                for row in contexts
                if int(row.get("scale") or 0) == scale
                and str(row.get("instance_hash") or "")
            },
            key=lambda value: hashlib.sha256(value.encode()).hexdigest(),
        )
        for index, instance in enumerate(instances):
            fraction = index / max(1, len(instances))
            assignments[instance] = (
                "train"
                if fraction < 0.60
                else "calibration"
                if fraction < 0.80
                else "heldout"
            )
        scale_rows = [
            row for row in contexts if int(row.get("scale") or 0) == scale
        ]
        metrics: dict[str, int] = {}
        for partition in ("train", "calibration", "heldout"):
            selected = [
                row
                for row in scale_rows
                if assignments.get(str(row.get("instance_hash") or ""))
                == partition
            ]
            metrics[f"{partition}_context_count"] = len(selected)
            metrics[f"{partition}_instance_count"] = len({
                str(row.get("instance_hash") or "") for row in selected
            })
        per_scale[f"scale{scale}"] = metrics
    calibration_count = sum(
        assignments.get(str(row.get("instance_hash") or ""))
        == "calibration"
        for row in contexts
    )
    return {
        **per_scale,
        "calibration_context_count": calibration_count,
        "minimum_calibration_contexts": (
            MINIMUM_CALIBRATION_CONTEXTS_FOR_HARMFUL_GATE
        ),
        "calibration_shortfall": max(
            0,
            MINIMUM_CALIBRATION_CONTEXTS_FOR_HARMFUL_GATE
            - calibration_count,
        ),
        "projection_only": True,
    }


def _supplemental_pool_projection(
    contexts: list[dict[str, Any]],
    index_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    """Project leakage-safe evaluation capacity in the frozen snapshot pool."""

    assignments: dict[tuple[int, str], str] = {}
    for scale in (30, 50):
        instances = sorted(
            {
                str(row.get("instance_hash") or "")
                for row in contexts
                if int(row.get("scale") or 0) == scale
                and str(row.get("instance_hash") or "")
            },
            key=lambda value: hashlib.sha256(value.encode()).hexdigest(),
        )
        for index, instance in enumerate(instances):
            fraction = index / max(1, len(instances))
            assignments[(scale, instance)] = (
                "train"
                if fraction < 0.60
                else "calibration"
                if fraction < 0.80
                else "heldout"
            )
    current_states = {
        (int(row["scale"]), str(row["state"])[:16]) for row in contexts
    }
    counts = Counter()
    seen_states: set[tuple[int, str]] = set()
    for raw in list((index_payload or {}).get("rows") or ()):
        scale = int(raw.get("scale") or 0)
        instance = str(
            raw.get("instance_content_hash")
            or raw.get("instance_hash")
            or ""
        )
        state = str(
            raw.get("source_state_hash") or raw.get("state_hash") or ""
        )
        if scale not in (30, 50) or not instance or not state:
            continue
        key = (scale, state[:16])
        if key in seen_states:
            continue
        seen_states.add(key)
        partition = assignments.get((scale, instance))
        if partition is None:
            partition = _stable_supplemental_partition(scale, instance)
        if partition not in {"calibration", "heldout"}:
            continue
        counts[f"scale{scale}_{partition}"] += 1
        counts[partition] += 1
        if key not in current_states:
            counts[f"supplemental_{partition}"] += 1
    sufficient = bool(
        counts["calibration"] >= MINIMUM_CALIBRATION_CONTEXTS_FOR_HARMFUL_GATE
        and all(counts[f"scale{scale}_calibration"] >= 20 for scale in (30, 50))
        and all(counts[f"scale{scale}_heldout"] >= 10 for scale in (30, 50))
    )
    return {
        "calibration_context_count": counts["calibration"],
        "heldout_context_count": counts["heldout"],
        "supplemental_calibration_context_count": counts[
            "supplemental_calibration"
        ],
        "supplemental_heldout_context_count": counts[
            "supplemental_heldout"
        ],
        "by_scale": {
            str(scale): {
                "calibration_context_count": counts[
                    f"scale{scale}_calibration"
                ],
                "heldout_context_count": counts[f"scale{scale}_heldout"],
            }
            for scale in (30, 50)
        },
        "sufficient": sufficient,
        "status": (
            "PROJECTED_SUFFICIENT"
            if sufficient
            else "PROJECTED_INSUFFICIENT"
        ),
        "projection_only": True,
    }


def _stable_supplemental_partition(scale: int, instance_hash: str) -> str:
    digest = hashlib.sha256(
        f"p0v5-qg2-instance-split-v1:{int(scale)}:{instance_hash}".encode()
    ).digest()
    fraction = int.from_bytes(digest, "big") / float(1 << 256)
    return (
        "train"
        if fraction < 0.60
        else "calibration"
        if fraction < 0.80
        else "heldout"
    )


def _bucket_arm_from_width(value: object) -> str | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    for arm, label in BUCKET_LABELS.items():
        if math.isclose(parsed, float(label), rel_tol=0.0, abs_tol=1.0e-12):
            return arm
    return None


def _relaxed_scale_gate(row: dict[str, Any]) -> bool:
    return bool(
        row
        and row.get("context_count", 0)
        >= RELAXED_THRESHOLDS["minimum_determined_contexts_per_scale"]
        and row.get("gain_5pct_context_count", 0)
        >= RELAXED_THRESHOLDS["minimum_gain_5pct_contexts_per_scale"]
        and row.get("gain_5pct_instance_count", 0)
        >= RELAXED_THRESHOLDS["minimum_positive_instances_per_scale"]
        and row.get("gm") is not None
        and row["gm"] <= RELAXED_THRESHOLDS["maximum_paired_geomean_ratio"]
        and row.get("bootstrap_upper") is not None
        and row["bootstrap_upper"]
        <= RELAXED_THRESHOLDS["maximum_instance_bootstrap_95_upper"]
    )


def _index_coverage(payload: dict[str, Any] | None) -> dict[int, dict[str, int]]:
    rows = list((payload or {}).get("rows") or ())
    return {
        scale: {
            "contexts": sum(int(row.get("scale") or 0) == scale for row in rows),
            "instances": len({
                str(row.get("instance_content_hash") or row.get("instance_hash") or "")
                for row in rows
                if int(row.get("scale") or 0) == scale
            }),
        }
        for scale in (30, 50)
    }


def _index_instance_by_state(
    payload: dict[str, Any] | None,
) -> dict[tuple[int, str], str]:
    mapping: dict[tuple[int, str], str] = {}
    ambiguous: set[tuple[int, str]] = set()
    for row in list((payload or {}).get("rows") or ()):
        scale = int(row.get("scale") or 0)
        state = str(row.get("state_hash") or row.get("source_state_hash") or "")
        instance = str(row.get("instance_id") or "")
        if scale not in (30, 50) or not state or not instance:
            continue
        key = (scale, state[:16])
        if key in mapping and mapping[key] != instance:
            ambiguous.add(key)
        else:
            mapping[key] = instance
    for key in ambiguous:
        mapping.pop(key, None)
    return mapping


def _bounded_selected_state_prefixes(
    payload: dict[str, Any] | None,
    *,
    maximum: int | None,
    per_scale: int | None,
) -> set[tuple[int, str]] | None:
    """Mirror the Oracle's deterministic pre-action bounded selection.

    A live directory can retain development contexts from an earlier budget.
    When an explicit live-run budget is supplied, only contexts selected by
    the current Oracle are included in progress and aggregate statistics.
    """
    if maximum is None and per_scale is None:
        return None
    maximum_value = max(0, int(maximum or (2 * int(per_scale or 0))))
    per_scale_value = max(0, int(per_scale or maximum_value))
    rows = sorted(
        list((payload or {}).get("rows") or ()),
        key=lambda row: (
            int(row.get("scale") or 0),
            str(
                row.get("instance_hash")
                or row.get("instance_content_hash")
                or ""
            ),
            str(row.get("state_hash") or row.get("source_state_hash") or ""),
        ),
    )
    selected: list[dict[str, Any]] = []
    for scale in (30, 50):
        groups: dict[str, dict[str, list[dict[str, Any]]]] = {}
        for row in rows:
            if int(row.get("scale") or 0) != scale:
                continue
            instance = str(
                row.get("instance_hash")
                or row.get("instance_content_hash")
                or ""
            )
            groups.setdefault(_preaction_stratum(row), {}).setdefault(
                instance, []
            ).append(row)
        queues: dict[str, list[dict[str, Any]]] = {}
        for stratum, instance_groups in groups.items():
            for values in instance_groups.values():
                values.sort(key=lambda row: str(
                    row.get("state_hash")
                    or row.get("source_state_hash")
                    or ""
                ))
            queue: list[dict[str, Any]] = []
            while instance_groups:
                for instance in sorted(tuple(instance_groups)):
                    queue.append(instance_groups[instance].pop(0))
                    if not instance_groups[instance]:
                        instance_groups.pop(instance, None)
            queues[stratum] = queue
        scale_count = 0
        while queues and scale_count < per_scale_value:
            progressed = False
            for stratum in sorted(tuple(queues)):
                if queues[stratum]:
                    selected.append(queues[stratum].pop(0))
                    scale_count += 1
                    progressed = True
                if not queues[stratum]:
                    queues.pop(stratum, None)
                if scale_count >= per_scale_value:
                    break
            if not progressed:
                break
    prefixes = set()
    for row in selected[:maximum_value]:
        scale = int(row.get("scale") or 0)
        state = str(row.get("state_hash") or row.get("source_state_hash") or "")
        if scale in (30, 50) and state:
            prefixes.add((scale, state[:16]))
    return prefixes


def _preaction_stratum(row: dict[str, Any]) -> str:
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
        "r0_9"
        if round_index < 10
        else "r10_29"
        if round_index < 30
        else "r30_plus"
    )
    previous = str(row.get("previous_q0_wall_stratum") or "missing")
    return f"{scope}:{structural}:{round_bucket}:{previous}"


def _project_snapshot_binding(payload: dict[str, Any]) -> dict[str, Any]:
    trajectory = payload.get("trajectory_features")
    branch = payload.get("branch_context")
    cut = payload.get("cut_context")
    duals = payload.get("true_duals")
    signatures = payload.get("active_column_signature_hashes")
    active_count = payload.get("active_column_count")
    signature_count = len(signatures) if isinstance(signatures, list) else -1
    previous_wall = (
        trajectory.get("previous_proof_pass_wall_time")
        if isinstance(trajectory, dict)
        else None
    )
    previous_labels = (
        trajectory.get("previous_proof_processed_labels")
        if isinstance(trajectory, dict)
        else None
    )
    trajectory_keys_complete = bool(
        isinstance(trajectory, dict)
        and {
            "previous_proof_pass_wall_time",
            "previous_proof_processed_labels",
            "dual_l1_delta_from_previous",
            "v5_midpoint_wall_sec",
        }.issubset(trajectory)
    )
    active_column_complete = bool(
        active_count is not None
        and int(active_count) >= 0
        and signature_count == int(active_count)
        and payload.get("active_task_sets") is not None
    )
    structural_complete = bool(
        active_column_complete
        and payload.get("round") is not None
        and isinstance(branch, dict)
        and isinstance(cut, dict)
        and isinstance(duals, dict)
        and isinstance(duals.get("task_duals"), dict)
        and len(duals.get("task_duals") or {}) == int(payload.get("scale") or 0)
        and "fleet_dual" in duals
        and isinstance(duals.get("cut_duals"), dict)
        and trajectory_keys_complete
        and str(payload.get("trajectory_feature_semantics_version") or "")
        == "p0v5_qg2_preaction_trajectory_missingness.v2"
        and str(payload.get("base_proof_queue_policy_id") or "") == "Q0"
        and bool(payload.get("config_hash"))
        and bool(payload.get("engine_hash"))
        and bool(payload.get("exact_action_policy_hash"))
    )
    return {
        "scale": int(payload.get("scale") or 0),
        "structural_complete": structural_complete,
        "active_column_complete": active_column_complete,
        "round_present": payload.get("round") is not None,
        "previous_proof_present": (
            previous_wall is not None and previous_labels is not None
        ),
        "previous_proof_missing": (
            previous_wall is None and previous_labels is None
        ),
        "previous_proof_pair_consistent": (
            (previous_wall is None) == (previous_labels is None)
        ),
        "dual_delta_present": bool(
            isinstance(trajectory, dict)
            and trajectory.get("dual_l1_delta_from_previous") is not None
        ),
        "root": str(payload.get("pricing_lifecycle_scope") or "") == "root_cg",
        "tree": str(payload.get("pricing_lifecycle_scope") or "") == "tree_node",
        "active_branch": int((branch or {}).get("pair_decision_count") or 0) > 0,
        "active_cut": int((cut or {}).get("cut_count") or 0) > 0,
    }


def _snapshot_binding_census(
    index_payload: dict[str, Any] | None,
    *,
    selected_state_prefixes: set[tuple[int, str]] | None,
    cache: ProjectionCache,
) -> dict[int, dict[str, int]]:
    result = {
        scale: {
            "snapshot_count": 0,
            "structural_binding_complete_count": 0,
            "active_column_binding_complete_count": 0,
            "round_present_count": 0,
            "previous_proof_present_count": 0,
            "previous_proof_missing_count": 0,
            "previous_proof_pair_inconsistent_count": 0,
            "dual_delta_present_count": 0,
            "root_count": 0,
            "tree_count": 0,
            "active_branch_count": 0,
            "active_cut_count": 0,
            "unreadable_count": 0,
        }
        for scale in (30, 50)
    }
    for row in (index_payload or {}).get("rows", ()):
        scale = int(row.get("scale") or 0)
        if scale not in result:
            continue
        state = str(row.get("state_hash") or row.get("source_state_hash") or "")[:16]
        if (
            selected_state_prefixes is not None
            and (scale, state) not in selected_state_prefixes
        ):
            continue
        current = result[scale]
        current["snapshot_count"] += 1
        path_value = str(row.get("snapshot_path") or "")
        binding = cache.binding(_resolve(path_value)) if path_value else None
        if binding is None:
            current["unreadable_count"] += 1
            continue
        for field, counter in (
            ("structural_complete", "structural_binding_complete_count"),
            ("active_column_complete", "active_column_binding_complete_count"),
            ("round_present", "round_present_count"),
            ("previous_proof_present", "previous_proof_present_count"),
            ("previous_proof_missing", "previous_proof_missing_count"),
            ("dual_delta_present", "dual_delta_present_count"),
            ("root", "root_count"),
            ("tree", "tree_count"),
            ("active_branch", "active_branch_count"),
            ("active_cut", "active_cut_count"),
        ):
            current[counter] += int(bool(binding.get(field)))
        current["previous_proof_pair_inconsistent_count"] += int(
            not bool(binding.get("previous_proof_pair_consistent"))
        )
    return result


def _artifact_row(path: Path, cache: ProjectionCache) -> dict[str, Any]:
    payload = cache.small_json(path)
    if payload is None:
        return {"exists": False, "status": "pending"}
    status = payload.get("status")
    if status is None and "complete" in payload:
        status = "complete" if payload.get("complete") else "incomplete"
    if status is None and "gate_pass" in payload:
        status = "gate_pass" if payload.get("gate_pass") else "gate_failed"
    if status is None and "passed" in payload:
        status = "passed" if payload.get("passed") else "not_passed"
    return {"exists": True, "status": str(status or "present")}


def _current_child(oracle_pid: int | None) -> dict[str, Any] | None:
    if not _pid_alive(oracle_pid):
        return None
    children_path = Path(f"/proc/{oracle_pid}/task/{oracle_pid}/children")
    try:
        children = [int(value) for value in children_path.read_text().split()]
    except (OSError, ValueError):
        return None
    for pid in children:
        argv = _cmdline(pid)
        if not argv:
            continue
        output = _arg_value(argv, "--output") or ""
        policy = _current_arm_name(
            output,
            _arg_value(argv, "--policy")
            or Path(argv[1] if len(argv) > 1 else argv[0]).name,
        )
        context = Path(output).parent.name if output else ""
        return {"pid": pid, "policy": policy, "context": context, "output": output}
    return None


def _current_arm_name(output: str, fallback: str) -> str:
    """Report the experiment arm, not the shared low-level QG2 policy id."""
    filename = Path(output).name if output else ""
    for arm, arm_filename in ARM_FILES.items():
        if filename == arm_filename:
            return arm
    if filename == "q0_trace.json":
        return "Q0 trace"
    if filename == "qo2_leaked_potential.json":
        return "QO2 leaked-potential fit"
    return fallback


def _pid_alive(pid: int | None) -> bool:
    return bool(pid is not None and Path(f"/proc/{int(pid)}").exists())


def _cmdline(pid: int) -> list[str]:
    try:
        return [
            value.decode("utf-8", errors="replace")
            for value in Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
            if value
        ]
    except OSError:
        return []


def _arg_value(argv: list[str], name: str) -> str | None:
    try:
        index = argv.index(name)
    except ValueError:
        return None
    return argv[index + 1] if index + 1 < len(argv) else None


def _geomean(values: list[float]) -> float | None:
    if not values:
        return None
    return math.exp(statistics.fmean(math.log(max(1.0e-12, value)) for value in values))


def _milestone(value: str, scale: int) -> str:
    if value == "ADMISSION_BATCH_READY":
        return "A64" if scale == 30 else "A128"
    if value == "EXACT_PROOF_COMPLETION":
        return "Proof"
    return value or "—"


def _short_instance(value: str) -> str:
    result = value.replace("lunar_ice_030_", "").replace("lunar_ice_050_", "")
    return result.replace("_logical_graph", "")


def _fmt(value: float | None) -> str:
    return "—" if value is None or not math.isfinite(value) else f"{value:.4f}"


def _change(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "—"
    percent = abs(1.0 - value) * 100.0
    return f"快{percent:.1f}%" if value <= 1.0 else f"慢{percent:.1f}%"


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100.0:.2f}%"


def _signed_seconds(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:+.2f}s"


def _seconds(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "—"
    return f"{value:.2f}s"


def _escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


if __name__ == "__main__":
    raise SystemExit(main())

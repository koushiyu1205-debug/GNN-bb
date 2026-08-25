#!/usr/bin/env python3
"""Execute one frozen Temporal-GAT schedule sequentially in fresh processes."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.p0v5_temporal_gat_common import (  # noqa: E402
    ensure_not_terminal, mark_terminal_negative, update_state, write_once,
)


ROOT = Path(__file__).resolve().parents[1]
REPLAY = ROOT / "scripts/replay_p0v5_qg2_label_state_snapshot.py"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mem_available_gb() -> float:
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        if line.startswith("MemAvailable:"):
            return float(line.split()[1]) / (1024.0 * 1024.0)
    raise RuntimeError("MemAvailable is unavailable")


def _environment(native_build: Path) -> dict[str, str]:
    value = dict(os.environ)
    for name in tuple(value):
        if (
            name.startswith("LUNAR_ICE_P0V5_")
            or name.startswith("LUNAR_ICE_PROOF_TAIL_GAT")
            or name.startswith("LUNAR_ICE_GAT_")
            or name == "LUNAR_ICE_PRODUCTION_POLICY_REGISTRY"
        ):
            value.pop(name, None)
    value["PYTHONPATH"] = os.pathsep.join((
        str(native_build.resolve()), str(ROOT / "src"),
    ))
    return value


def _run(task, context, output, environment):
    staging = output.with_suffix(output.suffix + ".partial")
    if staging.exists():
        raise SystemExit(f"partial temporal replay requires audit:{staging}")
    # A literal-Q0 control has the temporal probe disabled.  Its legacy
    # request field must therefore stay at the legacy 4096 sentinel even for
    # scale50; only the two temporal trial arms carry the 16384 decision
    # boundary into BackendPricingRequest.
    request_probe_boundary = (
        int(task["boundary"]) if task["arm"] != "Q0" else 4096
    )
    command = [
        sys.executable, str(REPLAY), "--instance", str(context["instance_path"]),
        "--snapshot", str(context["snapshot_path"]), "--output", str(staging),
        "--policy", task["replay_policy"], "--repeat-index",
        str(int(task["repeat"]) + 1), "--wall-time-limit-sec",
        str(task["cap_seconds"]), "--memory-limit-gb",
        str(task["memory_limit_gb"]), "--frontier-probe-boundary",
        str(request_probe_boundary), "--frontier-trial-pop-budget",
        str(task["k"]),
    ]
    completed = subprocess.run(command, cwd=ROOT, env=environment, check=False)
    if completed.returncode or not staging.is_file():
        raise SystemExit(f"temporal replay failed:{task['task_id']}")
    # Parse before publication so an interrupted/invalid writer can never be
    # mistaken for completed immutable task evidence on resume.
    json.loads(staging.read_text(encoding="utf-8"))
    os.replace(staging, output)


def _redlines(task, raw, frontier):
    values = []
    engine_status = str(raw.get("engine_status") or "UNKNOWN").upper()
    if engine_status not in {
        "COMPLETE", "FOUND_NEGATIVE_PARTIAL", "TIMEOUT", "MEMORY_LIMIT",
    } and not any(token in engine_status for token in ("INCOMPLETE", "LIMIT")):
        values.append(f"unexpected_engine_status:{engine_status}")
    if bool(raw.get("labels_dropped")):
        values.append("labels_dropped")
    if any(not bool(row.get("accepted")) for row in raw.get("route_audit") or ()):
        values.append("route_reduced_cost_reaudit_failed")
    if any(str(value).startswith("native_result_binding_mismatch:")
           for value in raw.get("certificate_blockers") or ()):
        values.append("native_result_binding_mismatch")
    if task["arm"] == "Q0":
        if bool(frontier.get("enabled")):
            values.append("literal_q0_has_temporal_probe")
        return values
    if not bool(frontier.get("trial_started")):
        values.append("trial_not_started")
        return values
    if (
        int(frontier.get("problem_scale") or -1) != int(task["scale"])
        or str(frontier.get("pricing_lifecycle") or "") != "root_cg"
        or not bool(frontier.get("require_root_cg"))
    ):
        values.append("temporal_trial_authorization_scope_mismatch")
    if not bool(frontier.get("trial_completed")):
        # Exact natural exhaustion inside K intentionally bypasses both the
        # model and action.  Dataset construction retains it for resource
        # audit but cannot create a supervised CONTINUE-vs-REVERT label.
        return values
    if int(frontier.get("trial_pops") or 0) != int(task["k"]):
        values.append("trial_pop_budget_mismatch")
    if not (
        bool(frontier.get("switched_to_qd1"))
        and int(frontier.get("frontier_before_migration") or 0)
            == int(frontier.get("migrated_count") or -1)
        and int(frontier.get("duplicate_count") or 0) == 0
        and int(frontier.get("creation_hash_before") or 0)
            == int(frontier.get("creation_hash_after") or -1)
    ):
        values.append("forward_migration_conservation_mismatch")
    start_snapshot = dict(frontier.get("trial_start_snapshot") or {})
    end_snapshot = dict(frontier.get("trial_end_snapshot") or {})
    start_graph = dict(frontier.get("trial_start_temporal_graph") or {})
    end_graph = dict(frontier.get("trial_end_temporal_graph") or {})
    if not start_graph.get("graph_hash"):
        values.append("t0_temporal_graph_missing")
    if not end_graph.get("graph_hash"):
        values.append("tk_temporal_graph_missing")
    if any(len(snapshot.get("node_features") or ()) != 64 for snapshot in (
        start_snapshot, end_snapshot,
    )):
        values.append("depth_rc_graph_not_64_cells")
    static_id = (1 << 64) - 1
    for name, graph in (("t0", start_graph), ("tk", end_graph)):
        nodes = list(graph.get("node_features") or ())
        creation_ids = list(graph.get("creation_sequence_ids") or ())
        label_count = sum(int(value) != static_id for value in creation_ids)
        task_count = len(creation_ids) - label_count
        if (
            len(nodes) != len(creation_ids)
            or label_count > 256
            or task_count != int(task["scale"])
        ):
            values.append(f"{name}_label_task_sampling_contract_mismatch")
    if len(frontier.get("temporal_counter_features") or ()) != 24:
        values.append("temporal_counter_shape_mismatch")
    if not str(frontier.get("temporal_counter_hash") or ""):
        values.append("temporal_counter_hash_missing")
    temporal_edges = list(frontier.get("temporal_edges") or ())
    if (
        not str(frontier.get("temporal_edge_hash") or "")
        or len(temporal_edges)
            != int(frontier.get("temporal_cell_edge_count") or 0)
                + int(frontier.get("temporal_label_edge_count") or 0)
        or int(frontier.get("temporal_cell_edge_count") or 0) != 64
        or int(frontier.get("temporal_label_edge_count") or 0)
            != int(frontier.get("temporal_surviving_label_count") or 0)
    ):
        values.append("temporal_edge_conservation_mismatch")
    if task["arm"] == "CONTINUE_QD1":
        if frontier.get("action") != "CONTINUE_QD1" or frontier.get(
            "migrated_back_to_q0"
        ):
            values.append("continue_arm_action_mismatch")
    else:
        before = int(frontier.get("reverse_frontier_before_migration") or 0)
        if not (
            frontier.get("action") == "MIGRATE_BACK_TO_Q0" and
            frontier.get("migrated_back_to_q0") and
            before == int(frontier.get("reverse_staged_count", -1)) and
            before == int(frontier.get("reverse_migrated_count", -1)) and
            int(frontier.get("reverse_duplicate_count") or 0) == 0 and
            int(frontier.get("reverse_creation_hash_before") or 0) ==
                int(frontier.get("reverse_creation_hash_after", -1))
        ):
            values.append("reverse_migration_conservation_mismatch")
    return values


def _deterministic_probe_hash(frontier, *, resource_censor=False):
    deadline_dependent = {"q0_post_probe_pops", "qd1_post_probe_pops"}

    def scrub(value):
        if isinstance(value, dict):
            return {
                key: scrub(child) for key, child in sorted(value.items())
                if "wall" not in str(key).lower()
                and not (resource_censor and key in deadline_dependent)
            }
        if isinstance(value, list):
            return [scrub(child) for child in value]
        return value
    return hashlib.sha256(json.dumps(
        scrub(frontier), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")).hexdigest()


def _outcome(task, context, path):
    raw = json.loads(path.read_text(encoding="utf-8"))
    if (
        str(raw.get("instance_content_hash") or "")
            != str(context["instance_hash"])
        or str(raw.get("source_state_hash") or "")
            != str(context["state_hash"])
        or str(raw.get("source_engine_hash") or "")
            != str(context["engine_hash"])
        or str(raw.get("source_config_hash") or "")
            != str(context["config_hash"])
        or str(raw.get("policy") or "") != str(task["replay_policy"])
        or int(raw.get("scale") or -1) != int(task["scale"])
    ):
        raise SystemExit(f"temporal replay output binding drift:{task['task_id']}")
    telemetry = dict(raw.get("proof_telemetry") or {})
    frontier = dict(telemetry.get("proof_queue_frontier_probe") or {})
    status = str(raw.get("engine_status") or "UNKNOWN").upper()
    resource_censor = any(value in status for value in (
        "TIMEOUT", "MEMORY", "INCOMPLETE", "LIMIT",
    ))
    redlines = _redlines(task, raw, frontier)
    complete = not resource_censor and not redlines
    return {
        "task_id": task["task_id"], "block_id": task["block_id"],
        "context_id": task["context_id"], "instance_hash": task["instance_hash"],
        "state_hash": context["state_hash"], "scale": int(task["scale"]),
        "partition": task["partition"], "k": int(task["k"]),
        "repeat": int(task["repeat"]), "arm": task["arm"],
        "status": "COMPLETE" if complete else status,
        "raw_engine_status": status,
        "wall_seconds": float(raw.get("backend_solve_wall_sec") or 0.0),
        "resource_censor": resource_censor,
        "trial_completed_for_action": bool(
            task["arm"] == "Q0" or frontier.get("trial_completed")
        ),
        "trial_natural_end_before_action": bool(
            task["arm"] != "Q0" and frontier.get("trial_started") and
            not frontier.get("trial_completed")
        ),
        "correctness_redlines": redlines,
        # The learned runtime is attached on the outer P0V5 hybrid request,
        # so production binding must retain that source engine hash.  The
        # concrete in-process replay engine remains separate audit evidence.
        "engine_hash": raw.get("source_engine_hash"),
        "replay_engine_hash": raw.get("replay_engine_hash"),
        "config_hash": raw.get("source_config_hash"),
        "replay_config_hash": raw.get("replay_binding", {}).get("config_hash"),
        "search_exhaustive": bool(raw.get("search_exhaustive")),
        "frontier_empty": bool(raw.get("frontier_empty")),
        "global_min_rc": raw.get("global_min_rc"),
        "global_min_rc_is_exact": bool(raw.get("global_min_rc_is_exact")),
        "certificate_blockers": raw.get("certificate_blockers") or [],
        "frontier_telemetry": frontier,
        "deterministic_frontier_telemetry_hash": (
            _deterministic_probe_hash(
                frontier, resource_censor=resource_censor
            )
        ),
        "raw_path": str(path), "raw_sha256": _sha(path),
    }


def _differential_redlines(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["block_id"]].append(row)
    values = []
    for block, members in grouped.items():
        if len(members) != 3:
            values.append(f"incomplete_block:{block}")
            continue
        complete = [row for row in members if row["status"] == "COMPLETE"]
        if len(complete) != 3:
            continue
        semantics = {(
            row["search_exhaustive"], row["frontier_empty"],
            row["global_min_rc_is_exact"], tuple(row["certificate_blockers"]),
        ) for row in complete}
        if len(semantics) != 1:
            values.append(f"exact_semantics_mismatch:{block}")
        exact_rc = [float(row["global_min_rc"]) for row in complete
                    if row["global_min_rc_is_exact"] and
                    row["global_min_rc"] is not None]
        if exact_rc and max(exact_rc) - min(exact_rc) > 1.0e-9:
            values.append(f"exact_objective_mismatch:{block}")
    repeated = defaultdict(set)
    for row in rows:
        repeated[(
            row["context_id"], int(row["scale"]), int(row["k"]), row["arm"]
        )].add(str(row["deterministic_frontier_telemetry_hash"]))
    for key, hashes in repeated.items():
        if len(hashes) != 1:
            values.append("nondeterministic_frontier_telemetry:" + ":".join(
                map(str, key)
            ))
    return values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schedule", type=Path, required=True)
    parser.add_argument("--contexts", type=Path, required=True)
    parser.add_argument("--native-build", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--task-limit", type=int)
    parser.add_argument("--memavailable-reserve-gb", type=float, default=2.0)
    args = parser.parse_args()
    schedule = json.loads(args.schedule.read_text(encoding="utf-8"))
    contexts_payload = json.loads(args.contexts.read_text(encoding="utf-8"))
    run_root = args.run_root.resolve()
    try:
        ensure_not_terminal(run_root)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    config_freeze = run_root / "config.freeze.json"
    source_freeze = run_root / "source.freeze.json"
    if not config_freeze.is_file() or not source_freeze.is_file():
        raise SystemExit("Temporal-GAT immutable run bindings are missing")
    source = json.loads(source_freeze.read_text(encoding="utf-8"))
    native_binaries = sorted(args.native_build.resolve().glob(
        "lunar_spprc_native*.so"
    ))
    if (
        schedule.get("source_config_freeze_sha256") != _sha(config_freeze)
        or schedule.get("source_contexts_sha256") != _sha(args.contexts)
        or len(native_binaries) != 1
        or Path(str(source.get("native_build_dir") or "")).resolve()
            != args.native_build.resolve()
        or str(source.get("native_binary_sha256") or "")
            != _sha(native_binaries[0])
        or abs(
            float(schedule.get("memavailable_reserve_gb") or -1.0)
            - float(args.memavailable_reserve_gb)
        ) > 1.0e-12
    ):
        raise SystemExit("Temporal-GAT schedule/source/native binding drift")
    k_selection_path = schedule.get("source_k_selection_path")
    if k_selection_path is not None and (
        not Path(str(k_selection_path)).is_file()
        or _sha(Path(str(k_selection_path)))
            != str(schedule.get("source_k_selection_sha256") or "")
    ):
        raise SystemExit("Temporal-GAT selected-K binding drift")
    contexts = {row["context_id"]: row for row in contexts_payload["rows"]}
    for context in contexts.values():
        snapshot_path = Path(str(context["snapshot_path"]))
        instance_path = Path(str(context["instance_path"]))
        if (
            not snapshot_path.is_file()
            or _sha(snapshot_path) != str(context["snapshot_sha256"])
            or not instance_path.is_file()
            or _sha(instance_path) != str(context["instance_file_sha256"])
        ):
            raise SystemExit("Temporal-GAT context input hash drift")
    output = args.output_dir.resolve()
    raw_dir = output / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    environment = _environment(args.native_build)
    completed_before = sum(
        (
            raw_dir /
            f"{hashlib.sha256(task['task_id'].encode()).hexdigest()}.json"
        ).is_file()
        for task in schedule["tasks"]
    )
    state_prefix = str(schedule["partition"])
    update_state(
        run_root,
        stage=("TRAIN_TRIALS" if schedule["partition"] == "train"
               else "CALIBRATION_TRIALS"),
        status="IN_PROGRESS",
        detail={
            f"{state_prefix}_trial_task_count": len(schedule["tasks"]),
            f"{state_prefix}_trial_tasks_published": completed_before,
        },
    )
    launched = 0
    for task in schedule["tasks"]:
        path = raw_dir / f"{hashlib.sha256(task['task_id'].encode()).hexdigest()}.json"
        if path.is_file():
            continue
        if args.task_limit is not None and launched >= args.task_limit:
            break
        if _mem_available_gb() < float(args.memavailable_reserve_gb):
            raise SystemExit("MemAvailable reserve would be violated")
        _run(task, contexts[task["context_id"]], path, environment)
        launched += 1
        update_state(
            run_root,
            stage=("TRAIN_TRIALS" if schedule["partition"] == "train"
                   else "CALIBRATION_TRIALS"),
            status="IN_PROGRESS",
            detail={
                f"{state_prefix}_trial_task_count": len(schedule["tasks"]),
                f"{state_prefix}_trial_tasks_published": (
                    completed_before + launched
                ),
            },
        )
    missing = [task for task in schedule["tasks"] if not (
        raw_dir / f"{hashlib.sha256(task['task_id'].encode()).hexdigest()}.json"
    ).is_file()]
    if missing:
        print(json.dumps({"status": "PARTIAL", "remaining": len(missing)}))
        return 0
    rows = []
    for task in schedule["tasks"]:
        path = raw_dir / f"{hashlib.sha256(task['task_id'].encode()).hexdigest()}.json"
        rows.append(_outcome(task, contexts[task["context_id"]], path))
    differential = _differential_redlines(rows)
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_temporal_trial_outcomes.v1",
        "partition": schedule["partition"], "single_host_instance": True,
        "source_schedule": str(args.schedule.resolve()),
        "source_schedule_sha256": _sha(args.schedule),
        "source_contexts": str(args.contexts.resolve()),
        "source_contexts_sha256": _sha(args.contexts),
        "source_config_freeze_sha256": _sha(config_freeze),
        "source_freeze_sha256": _sha(source_freeze),
        "native_binary_sha256": _sha(native_binaries[0]),
        "row_count": len(rows), "differential_redlines": differential,
        "rows": rows,
    }
    target = output / "outcomes.json"
    write_once(target, payload)
    if differential:
        mark_terminal_negative(
            args.run_root, stage=f"{schedule['partition'].upper()}_TRIALS",
            reason="TEMPORAL_TRIAL_EXACT_DIFFERENTIAL_REDLINE",
            detail={"differential_redlines": differential},
        )
        raise SystemExit("TEMPORAL_TRIAL_EXACT_DIFFERENTIAL_REDLINE")
    update_state(
        run_root,
        stage=("K_SELECTION" if schedule["partition"] == "train"
               else "DATASET_BUILD"),
        status="READY",
        detail={
            f"{state_prefix}_trial_task_count": len(schedule["tasks"]),
            f"{state_prefix}_trial_tasks_published": len(schedule["tasks"]),
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

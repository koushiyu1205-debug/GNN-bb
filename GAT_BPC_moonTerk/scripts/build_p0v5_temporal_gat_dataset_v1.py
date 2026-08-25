#!/usr/bin/env python3
"""Build immutable direct CONTINUE-vs-REVERT Temporal-GAT labels."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import statistics
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.p0v5_temporal_gat_common import (  # noqa: E402
    ensure_not_terminal, mark_terminal_negative,
)


def _canonical(payload: object) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")


def _graph_payload(frontier: Mapping[str, Any], scale: int) -> dict[str, Any]:
    start = dict(frontier["trial_start_snapshot"])
    end = dict(frontier["trial_end_snapshot"])
    return {
        "cell_t0": {
            "node_features": start["node_features"],
            "edges": start["edges"],
            "context_features": start["context_features"],
        },
        "cell_tk": {
            "node_features": end["node_features"],
            "edges": end["edges"],
            "context_features": end["context_features"],
        },
        "graph_t0": frontier["trial_start_temporal_graph"],
        "graph_tk": frontier["trial_end_temporal_graph"],
        "counter_features": frontier["temporal_counter_features"],
        "counter_hash": frontier.get("temporal_counter_hash") or "",
        "context_features": end["context_features"],
        "temporal_edges": frontier.get("temporal_edges") or [],
        "temporal_edge_hash": frontier.get("temporal_edge_hash") or "",
        "scale": int(scale),
    }


def _collapse_arm(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if len(rows) != 3 or {int(row["repeat"]) for row in rows} != {0, 1, 2}:
        return {"determined": False, "reason": "missing_blocked_repeat"}
    redlines = sorted({
        value for row in rows for value in row.get("correctness_redlines", ())
    })
    censor = any(bool(row.get("resource_censor")) for row in rows)
    complete = all(str(row.get("status")) == "COMPLETE" for row in rows)
    action_determined = all(bool(row.get(
        "trial_completed_for_action", row.get("arm") == "Q0"
    )) for row in rows)
    return {
        "determined": (
            complete and action_determined and not redlines and not censor
        ),
        "trial_completed_for_action": action_determined,
        "wall_seconds": statistics.median(
            float(row["wall_seconds"]) for row in rows
        ) if complete else None,
        "resource_censor": censor,
        "correctness_redlines": redlines,
        "rows": rows,
    }


def build_dataset(outcomes: Mapping[str, Any]) -> dict[str, Any]:
    grouped: dict[tuple[str, int, int], dict[str, list[dict[str, Any]]]] = (
        defaultdict(lambda: defaultdict(list))
    )
    for raw in outcomes.get("rows") or ():
        row = dict(raw)
        grouped[(
            str(row["context_id"]), int(row["scale"]), int(row["k"]),
        )][str(row["arm"])].append(row)
    output = []
    redline_rows = []
    for (context_id, scale, k), arms in sorted(grouped.items()):
        collapsed = {
            arm: _collapse_arm(list(arms.get(arm) or ()))
            for arm in ("Q0", "CONTINUE_QD1", "MIGRATE_BACK_TO_Q0")
        }
        all_redlines = sorted({
            value for row in collapsed.values()
            for value in row.get("correctness_redlines", ())
        })
        trial_rows = (
            list(arms.get("CONTINUE_QD1") or ()) +
            list(arms.get("MIGRATE_BACK_TO_Q0") or ())
        )
        telemetry_rows = [
            dict(row.get("frontier_telemetry") or {}) for row in trial_rows
            if bool(dict(row.get("frontier_telemetry") or {}).get("trial_completed"))
        ]
        representation = None
        representation_hash = ""
        if telemetry_rows:
            payloads = [_graph_payload(row, scale) for row in telemetry_rows]
            hashes = {hashlib.sha256(_canonical(row)).hexdigest() for row in payloads}
            if len(hashes) != 1:
                all_redlines.append("nondeterministic_temporal_representation")
            else:
                representation = payloads[0]
                representation_hash = next(iter(hashes))
        for binding in ("instance_hash", "state_hash", "engine_hash", "config_hash"):
            values = {str(row.get(binding) or "") for row in trial_rows}
            if len(values) != 1 or "" in values:
                all_redlines.append(f"trial_{binding}_binding_mismatch")
        continue_row = collapsed["CONTINUE_QD1"]
        revert_row = collapsed["MIGRATE_BACK_TO_Q0"]
        censored_after_continue_action = bool(
            continue_row.get("resource_censor") and
            continue_row.get("trial_completed_for_action")
        )
        supervised = bool(
            representation is not None and not all_redlines and
            (
                (continue_row["determined"] and revert_row["determined"])
                or (
                    censored_after_continue_action and
                    revert_row["determined"]
                )
            )
        )
        ratio = None
        benefit = 0
        adverse = 0
        positive_gain = 0.0
        if continue_row["determined"] and revert_row["determined"]:
            ratio = float(continue_row["wall_seconds"]) / float(
                revert_row["wall_seconds"]
            )
            benefit = int(ratio <= 0.98)
            adverse = int(ratio >= 1.05)
            positive_gain = max(0.0, 1.0 - ratio)
        elif censored_after_continue_action and revert_row["determined"]:
            adverse = 1
        all_redlines = sorted(set(all_redlines))
        if all_redlines:
            redline_rows.append({
                "context_id": context_id, "scale": scale, "k": k,
                "redlines": all_redlines,
            })
        source = next((row for row in trial_rows), None)
        if source is None:
            source = next(
                (row for arm_rows in arms.values() for row in arm_rows), {}
            )
        output.append({
            "context_id": context_id, "scale": scale, "k": k,
            "partition": source.get("partition"),
            "instance_hash": source.get("instance_hash"),
            "state_hash": source.get("state_hash"),
            "engine_hash": source.get("engine_hash"),
            "config_hash": source.get("config_hash"),
            "supervised": supervised,
            "model_eligible_after_trial": representation is not None,
            "benefit": benefit, "adverse": adverse,
            "positive_gain": positive_gain,
            "continue_vs_revert_ratio": ratio,
            "resource_censor": any(
                bool(row.get("resource_censor")) for row in collapsed.values()
            ),
            "correctness_redlines": all_redlines,
            "representation_hash": representation_hash,
            "temporal_graph": representation,
        })
    counts = defaultdict(int)
    contexts_by_instance = defaultdict(set)
    for row in output:
        counts[(int(row["scale"]), str(row["partition"]))] += 1
        contexts_by_instance[str(row["instance_hash"])].add(row["context_id"])
    for row in output:
        row["instance_balance_weight"] = 1.0 / max(
            1, len(contexts_by_instance[str(row["instance_hash"])])
        )
    return {
        "schema_version": "lunar_ice_bpc.p0v5_temporal_frontier_gat_dataset.v1",
        "label_contract": "direct_continue_vs_revert_0p98_1p05_v1",
        "both_incomplete_excluded_from_supervised_loss": True,
        "row_count": len(output),
        "supervised_row_count": sum(bool(row["supervised"]) for row in output),
        "correctness_redline_count": len(redline_rows),
        "redline_rows": redline_rows,
        "counts": {
            f"scale{scale}:{partition}": value
            for (scale, partition), value in sorted(counts.items())
        },
        "rows": output,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outcomes", type=Path, required=True, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args()
    sources = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in args.outcomes
    ]
    partitions = [str(source.get("partition") or "") for source in sources]
    if set(partitions) != {"train", "calibration"} or len(partitions) != 2:
        raise SystemExit("Temporal dataset requires exactly train and calibration")
    run_root = args.run_root.resolve()
    try:
        ensure_not_terminal(run_root)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    config_freeze = run_root / "config.freeze.json"
    source_freeze = run_root / "source.freeze.json"
    if not config_freeze.is_file() or not source_freeze.is_file():
        raise SystemExit("Temporal-GAT immutable run bindings are missing")
    config_sha256 = hashlib.sha256(config_freeze.read_bytes()).hexdigest()
    source_sha256 = hashlib.sha256(source_freeze.read_bytes()).hexdigest()
    source_binding = json.loads(source_freeze.read_text(encoding="utf-8"))
    if any(
        source.get("source_config_freeze_sha256") != config_sha256
        or source.get("source_freeze_sha256") != source_sha256
        or source.get("native_binary_sha256")
            != source_binding.get("native_binary_sha256")
        or bool(source.get("differential_redlines"))
        for source in sources
    ):
        raise SystemExit("Temporal outcome immutable binding drift")
    task_ids = [
        str(row["task_id"]) for source in sources
        for row in source.get("rows") or ()
    ]
    if len(task_ids) != len(set(task_ids)):
        raise SystemExit("Temporal outcome task IDs overlap across partitions")
    payload = build_dataset({
        "rows": [
            row for source in sources for row in source.get("rows") or ()
        ]
    })
    payload["source_partitions"] = partitions
    payload["source_outcome_sha256"] = {
        partition: hashlib.sha256(path.read_bytes()).hexdigest()
        for partition, path in zip(partitions, args.outcomes)
    }
    payload["source_config_freeze_sha256"] = config_sha256
    payload["source_freeze_sha256"] = source_sha256
    if payload["correctness_redline_count"]:
        mark_terminal_negative(
            args.run_root, stage="DATASET_BUILD",
            reason="TEMPORAL_DATASET_CORRECTNESS_REDLINE",
            detail=payload["redline_rows"],
        )
        raise SystemExit("TEMPORAL_DATASET_CORRECTNESS_REDLINE")
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output.exists() and args.output.read_text(encoding="utf-8") != encoded:
        raise SystemExit("immutable Temporal-GAT dataset drift")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not args.output.exists():
        args.output.write_text(encoded, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Merge a compact-pricing replay best column into a resumable probe payload."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-probe", required=True)
    parser.add_argument("--replay-json", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--vehicle-id", default="compact_replay_best")
    args = parser.parse_args()

    base_path = Path(args.base_probe)
    replay_path = Path(args.replay_json)
    output_path = Path(args.output_json)
    base = json.loads(base_path.read_text(encoding="utf-8"))
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    best_payload = (replay.get("result") or {}).get("best_solution_payload")
    if not isinstance(best_payload, dict):
        raise SystemExit("replay JSON has no result.best_solution_payload")
    if base.get("instance_id") not in {None, "", replay.get("instance_id")}:
        raise SystemExit(
            f"instance mismatch: base={base.get('instance_id')!r}, replay={replay.get('instance_id')!r}"
        )

    merged = dict(base)
    active_columns = list(base.get("active_columns") or [])
    normalized_best = dict(best_payload)
    normalized_best["vehicle_id"] = str(args.vehicle_id)
    before = len(active_columns)
    if not _contains_equivalent_column(active_columns, normalized_best):
        active_columns.append(normalized_best)
    merged["active_columns_payload_version"] = "journey_solution_payload.v1"
    merged["active_columns"] = active_columns
    merged["merged_replay_column"] = {
        "base_probe": str(base_path),
        "replay_json": str(replay_path),
        "before_active_column_count": before,
        "after_active_column_count": len(active_columns),
        "added": len(active_columns) > before,
        "replay_best_reduced_cost": (replay.get("result") or {}).get("best_reduced_cost"),
        "replay_dual_bound": (replay.get("result") or {}).get("dual_bound"),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(merged["merged_replay_column"], ensure_ascii=False))
    return 0


def _contains_equivalent_column(columns: list[dict], candidate: dict) -> bool:
    candidate_key = _column_key(candidate)
    return any(_column_key(column) == candidate_key for column in columns)


def _column_key(column: dict) -> tuple:
    sortie_keys = []
    for sortie in column.get("sorties") or []:
        tasks = tuple(str(task_id) for task_id in sortie.get("tasks") or [])
        legs = tuple(
            (str(leg.get("from")), str(leg.get("to")), str(leg.get("path_type")))
            for leg in sortie.get("legs") or []
        )
        start_time = round(float(sortie.get("start_time", 0.0)), 6)
        sortie_keys.append((tasks, legs, start_time))
    return tuple(sortie_keys)


if __name__ == "__main__":
    raise SystemExit(main())

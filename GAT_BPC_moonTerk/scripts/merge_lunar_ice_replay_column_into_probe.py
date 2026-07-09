#!/usr/bin/env python3
"""Merge a compact-pricing replay best column into a resumable probe payload."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-probe", required=True)
    parser.add_argument("--replay-json")
    parser.add_argument(
        "--targeted-json",
        help="Optional B4.1 targeted restricted-region probe JSON containing targeted_negative_solution_payload.",
    )
    parser.add_argument(
        "--targeted-row-index",
        type=int,
        default=-1,
        help="0-based targeted row index to merge; default selects the most negative addable payload row.",
    )
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--vehicle-id", default="compact_replay_best")
    args = parser.parse_args()

    base_path = Path(args.base_probe)
    output_path = Path(args.output_json)
    base = json.loads(base_path.read_text(encoding="utf-8"))
    source_path, source_payload = _load_source_payload(
        replay_json=args.replay_json,
        targeted_json=args.targeted_json,
    )
    best_payload, source_meta = _extract_best_payload(
        source_payload,
        source_path=source_path,
        targeted_row_index=int(args.targeted_row_index),
    )
    if not isinstance(best_payload, dict):
        raise SystemExit(
            "source JSON has no mergeable column payload "
            "(expected replay result.best_solution_payload or targeted_negative_solution_payload)"
        )
    if base.get("instance_id") not in {None, "", source_payload.get("instance_id")}:
        raise SystemExit(
            f"instance mismatch: base={base.get('instance_id')!r}, source={source_payload.get('instance_id')!r}"
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
        "replay_json": str(source_path),
        **source_meta,
        "before_active_column_count": before,
        "after_active_column_count": len(active_columns),
        "added": len(active_columns) > before,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(merged["merged_replay_column"], ensure_ascii=False))
    return 0


def _load_source_payload(*, replay_json: str | None, targeted_json: str | None) -> tuple[Path, dict]:
    provided = [path for path in (replay_json, targeted_json) if path]
    if len(provided) != 1:
        raise SystemExit("pass exactly one of --replay-json or --targeted-json")
    source_path = Path(provided[0])
    source_payload = json.loads(source_path.read_text(encoding="utf-8"))
    if not isinstance(source_payload, dict):
        raise SystemExit(f"source JSON must contain an object: {source_path}")
    return source_path, source_payload


def _extract_best_payload(
    source: dict,
    *,
    source_path: Path,
    targeted_row_index: int,
) -> tuple[dict | None, dict]:
    replay_payload = (source.get("result") or {}).get("best_solution_payload")
    if isinstance(replay_payload, dict):
        return replay_payload, {
            "source_kind": "compact_pricing_replay",
            "source_json": str(source_path),
            "replay_best_reduced_cost": (source.get("result") or {}).get("best_reduced_cost"),
            "replay_dual_bound": (source.get("result") or {}).get("dual_bound"),
        }

    rows = source.get("rows") if isinstance(source.get("rows"), list) else []
    candidates: list[tuple[int, dict]] = []
    for index, row in enumerate(rows):
        if isinstance(row, dict) and isinstance(row.get("targeted_negative_solution_payload"), dict):
            candidates.append((index, row))
    if not candidates:
        return None, {
            "source_kind": "b4_1_targeted_restricted_region_probe",
            "source_json": str(source_path),
        }
    if targeted_row_index >= 0:
        matching = [row for row in candidates if row[0] == targeted_row_index]
        if not matching:
            raise SystemExit(f"targeted row index {targeted_row_index} has no targeted_negative_solution_payload")
        selected_index, selected = matching[0]
    else:
        selected_index, selected = min(
            candidates,
            key=lambda item: (
                _float_or_inf(item[1].get("targeted_negative_true_rc")),
                item[0],
            ),
        )
    return selected.get("targeted_negative_solution_payload"), {
        "source_kind": "b4_1_targeted_restricted_region_probe",
        "source_json": str(source_path),
        "targeted_row_index": int(selected_index),
        "targeted_region_id": selected.get("region_id"),
        "targeted_variant": selected.get("variant"),
        "targeted_negative_task_set": selected.get("targeted_negative_task_set"),
        "targeted_negative_true_rc": selected.get("targeted_negative_true_rc"),
        "replay_best_reduced_cost": selected.get("targeted_negative_true_rc"),
        "replay_dual_bound": selected.get("dual_bound"),
    }


def _float_or_inf(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("inf")


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

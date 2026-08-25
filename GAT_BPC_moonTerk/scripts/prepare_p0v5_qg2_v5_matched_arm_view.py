#!/usr/bin/env python3
"""Freeze a partition-balanced QD1/QB1 matched-arm view before outcomes."""

from __future__ import annotations

import argparse
from collections import defaultdict, deque
import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = ROOT / "runs/p0v5_qg2_v5_trace_first_20260807"
ORACLE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
VIEW_SCHEMA = "lunar_ice_bpc.p0v5_qg2_v5_matched_arm_selection.v1"
PARTITIONS = ("train", "calibration", "heldout")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--training-view", default=str(DEFAULT_RUN / "trace_training_view.json")
    )
    parser.add_argument(
        "--output", default=str(DEFAULT_RUN / "matched_arm_selection_view.json")
    )
    parser.add_argument("--train-per-scale", type=int, default=5)
    parser.add_argument("--calibration-per-scale", type=int, default=5)
    parser.add_argument("--heldout-per-scale", type=int, default=2)
    parser.add_argument(
        "--force-compatible-order", action="store_true",
        help="use the same milestone/hash order as the frozen force-on screen",
    )
    parser.add_argument(
        "--instance-balanced-order", action="store_true",
        help="round-robin instances exactly as the frozen V4 force-on wrapper",
    )
    args = parser.parse_args()

    source_path = _resolve(args.training_view)
    target = _resolve(args.output)
    source = _load(source_path)
    if source.get("schema_version") != ORACLE_SCHEMA:
        raise SystemExit("matched-arm selection requires a V5 Oracle view")
    if bool(source.get("performance_oracle_gate_used")):
        raise SystemExit("matched-arm selection must be pre-outcome")
    requested = {
        "train": max(1, int(args.train_per_scale)),
        "calibration": max(1, int(args.calibration_per_scale)),
        "heldout": max(1, int(args.heldout_per_scale)),
    }
    selected = _select(
        source.get("initial_rows") or (), requested=requested,
        force_compatible_order=bool(args.force_compatible_order),
        instance_balanced_order=bool(args.instance_balanced_order),
    )
    payload = {
        **source,
        "initial_rows": selected,
        "context_rows": [
            row for row in source.get("context_rows") or ()
            if str(row.get("state_hash") or "") in {
                str(value["state_hash"]) for value in selected
            }
        ],
        "replicate_rows": [],
        "schema_version": ORACLE_SCHEMA,
        "selection_view_schema_version": VIEW_SCHEMA,
        "selection_policy": (
            "partition_balanced_hash_order_without_action_outcomes.v1"
        ),
        "selection_uses_action_outcomes": False,
        "source_training_view": str(source_path),
        "source_training_view_sha256": _sha256(source_path),
        "selected_context_count": len(selected),
        "selected_counts": _counts(selected),
        "requested_counts_per_scale": requested,
        "performance_oracle_gate_used": False,
        "production_switch_authorized": False,
        "deployable": False,
        "development_only": True,
    }
    if args.force_compatible_order:
        payload["force_compatible_order"] = True
    if args.instance_balanced_order:
        payload["instance_balanced_order"] = True
    _freeze_or_validate(target, payload)
    print(json.dumps({
        "output": str(target),
        "selected_context_count": len(selected),
        "selected_counts": payload["selected_counts"],
    }, sort_keys=True))
    return 0


def _select(
    rows, *, requested: dict[str, int],
    force_compatible_order: bool = False,
    instance_balanced_order: bool = False,
) -> list[dict]:
    values = [dict(row) for row in rows]
    selected = []
    for scale in (30, 50):
        for partition in PARTITIONS:
            candidates = [
                row for row in values
                if int(row.get("scale") or 0) == scale
                and str(row.get("partition") or "") == partition
                and bool(row.get("compliant_context"))
                and bool(row.get("all_initial_arms_safe"))
            ]
            if instance_balanced_order:
                candidates = _instance_balanced(candidates)
            else:
                candidates.sort(key=lambda row: _context_key(
                    row, force_compatible_order=force_compatible_order
                ))
            take = min(requested[partition], len(candidates))
            selected.extend(candidates[:take])
    if not selected:
        raise SystemExit("matched-arm selection has no compliant contexts")
    return selected


def _instance_balanced(rows: list[dict]) -> list[dict]:
    by_instance = defaultdict(list)
    for row in rows:
        by_instance[str(row.get("instance_hash") or "")].append(row)
    for values in by_instance.values():
        values.sort(key=lambda row: _context_key(
            row, force_compatible_order=True
        ))
    instance_order = sorted(
        by_instance, key=lambda value: hashlib.sha256(
            value.encode("utf-8")
        ).hexdigest(),
    )
    queues = {
        instance: deque(by_instance[instance]) for instance in instance_order
    }
    result = []
    while any(queues.values()):
        for instance in instance_order:
            if queues[instance]:
                result.append(queues[instance].popleft())
    return result


def _context_key(row: dict, *, force_compatible_order: bool):
    return (
        (
            str(row.get("q0_milestone_kind") or "")
            if force_compatible_order else ""
        ),
        hashlib.sha256(
            str(row.get("state_hash") or "").encode("utf-8")
        ).hexdigest(),
        str(row.get("state_hash") or ""),
    )


def _counts(rows) -> dict[str, dict[str, int]]:
    return {
        str(scale): {
            partition: sum(
                int(row.get("scale") or 0) == scale
                and str(row.get("partition") or "") == partition
                for row in rows
            )
            for partition in PARTITIONS
        }
        for scale in (30, 50)
    }


def _freeze_or_validate(path: Path, payload: dict) -> None:
    if path.is_file():
        if _load(path) != payload:
            raise SystemExit("matched-arm selection freeze drift")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _resolve(value) -> Path:
    path = Path(str(value)).expanduser()
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

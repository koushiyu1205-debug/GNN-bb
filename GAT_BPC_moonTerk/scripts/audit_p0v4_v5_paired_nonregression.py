#!/usr/bin/env python3
"""Audit blocked P0V4/V5 exact non-regression runs.

The runner deliberately consumes already completed acceptance directories.  It
does not launch solves, and it rejects incomplete, redlined, engine-unbound, or
unpaired rows before reporting a timing ratio.
"""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
from math import exp, log
from pathlib import Path
from statistics import median
from typing import Mapping


CONTROL = "P0V4"
CANDIDATE = "V5"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--scale", type=int, default=5)
    parser.add_argument("--minimum-blocks", type=int, default=3)
    parser.add_argument("--expected-instances", type=int, default=20)
    parser.add_argument("--ratio-max", type=float, default=1.03)
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    root = Path(args.run_root).resolve()
    output = (
        Path(args.output).resolve()
        if args.output
        else root / "paired_nonregression_audit.json"
    )
    audit = audit_blocked_pairs(
        root,
        scale=int(args.scale),
        minimum_blocks=int(args.minimum_blocks),
        expected_instances=int(args.expected_instances),
        ratio_max=float(args.ratio_max),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if audit["pass"] else 3


def audit_blocked_pairs(
    root: Path,
    *,
    scale: int,
    minimum_blocks: int,
    expected_instances: int,
    ratio_max: float,
) -> dict:
    issues: list[str] = []
    blocks: list[dict] = []
    pooled_ratios: list[float] = []
    block_ids = sorted(
        {
            path.name.split("_", 1)[0]
            for path in root.glob("block*_*" )
            if path.is_dir() and "_" in path.name
        }
    )
    if len(block_ids) < minimum_blocks:
        issues.append(
            f"blocked_replicate_count_{len(block_ids)}_lt_{minimum_blocks}"
        )
    for block_id in block_ids:
        arm_rows: dict[str, dict[str, float]] = {}
        arm_bindings: dict[str, dict] = {}
        arm_files: dict[str, dict] = {}
        block_issues: list[str] = []
        for arm in (CONTROL, CANDIDATE):
            arm_dir = root / f"{block_id}_{arm}"
            try:
                timings, binding, files = _read_arm(
                    arm_dir,
                    scale=scale,
                    expected_instances=expected_instances,
                )
            except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
                block_issues.append(f"{arm}:{type(exc).__name__}:{exc}")
                continue
            arm_rows[arm] = timings
            arm_bindings[arm] = binding
            arm_files[arm] = files
        ratios: list[float] = []
        if set(arm_rows) == {CONTROL, CANDIDATE}:
            control_keys = set(arm_rows[CONTROL])
            candidate_keys = set(arm_rows[CANDIDATE])
            if control_keys != candidate_keys:
                block_issues.append("instance_identity_mismatch")
            else:
                ratios = [
                    arm_rows[CANDIDATE][key] / arm_rows[CONTROL][key]
                    for key in sorted(control_keys)
                ]
                pooled_ratios.extend(ratios)
        if block_issues:
            issues.append(f"{block_id}:" + "|".join(block_issues))
        blocks.append(
            {
                "block_id": block_id,
                "paired_instance_count": len(ratios),
                "geometric_mean_ratio": _geometric_mean(ratios),
                "median_ratio": median(ratios) if ratios else None,
                "candidate_win_count": sum(value < 1.0 for value in ratios),
                "candidate_loss_count": sum(value > 1.0 for value in ratios),
                "issues": block_issues,
                "engine_bindings": arm_bindings,
                "source_files": arm_files,
            }
        )
    pooled_geometric = _geometric_mean(pooled_ratios)
    if not pooled_ratios:
        issues.append("no_valid_paired_timings")
    elif pooled_geometric > ratio_max:
        issues.append("paired_geometric_mean_ratio_gate_failed")
    return {
        "schema_version": "lunar_ice_bpc.p0v4_v5_paired_nonregression.v1",
        "run_root": str(root),
        "scale": scale,
        "control": CONTROL,
        "candidate": CANDIDATE,
        "minimum_blocks": minimum_blocks,
        "observed_block_count": len(blocks),
        "expected_instances_per_block": expected_instances,
        "paired_observation_count": len(pooled_ratios),
        "ratio_max": ratio_max,
        "pooled_geometric_mean_ratio": pooled_geometric,
        "pooled_relative_improvement": (
            None if not pooled_ratios else 1.0 - pooled_geometric
        ),
        "pooled_median_ratio": median(pooled_ratios) if pooled_ratios else None,
        "candidate_win_count": sum(value < 1.0 for value in pooled_ratios),
        "candidate_loss_count": sum(value > 1.0 for value in pooled_ratios),
        "blocks": blocks,
        "issues": issues,
        "pass": not issues,
    }


def _read_arm(
    arm_dir: Path,
    *,
    scale: int,
    expected_instances: int,
) -> tuple[dict[str, float], dict, dict]:
    summary_path = arm_dir / "native_spprc_acceptance_summary.json"
    rows_path = (
        arm_dir
        / f"scale_{scale:03d}"
        / "b4_2_cold_exact_rows.csv"
    )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    matching = [
        dict(row)
        for row in summary.get("rows", ())
        if int(row.get("scale") or 0) == scale
    ]
    if len(matching) != 1:
        raise ValueError("acceptance_summary_scale_row_count_ne_1")
    row = matching[0]
    gate = dict(row.get("profile_gate") or {})
    binding = dict(row.get("engine_binding") or {})
    if int(gate.get("row_count") or 0) != expected_instances:
        raise ValueError("acceptance_row_count_mismatch")
    if int(gate.get("exact_count") or 0) != expected_instances:
        raise ValueError("acceptance_exact_count_mismatch")
    if not bool(gate.get("all_no_cheat")):
        raise ValueError("no_cheat_gate_failed")
    if not bool(row.get("redlines_zero")):
        raise ValueError("correctness_redline")
    if not bool(binding.get("valid")):
        raise ValueError("engine_binding_invalid")
    timings: dict[str, float] = {}
    with rows_path.open(encoding="utf-8", newline="") as handle:
        for value in csv.DictReader(handle):
            key = str(value.get("instance_key") or "")
            wall = float(value.get("cold_start_total_sec") or 0.0)
            if not key or wall <= 0.0:
                raise ValueError("invalid_instance_timing")
            if key in timings:
                raise ValueError("duplicate_instance_key")
            if not _is_exact(value):
                raise ValueError("nonexact_ledger_row")
            timings[key] = wall
    if len(timings) != expected_instances:
        raise ValueError("ledger_row_count_mismatch")
    return (
        timings,
        {
            "expected_hash": binding.get("expected_hash"),
            "child_observed_hash": binding.get("child_observed_hash"),
            "end_hash": binding.get("end_hash"),
            "valid": True,
        },
        {
            "summary": str(summary_path.resolve()),
            "summary_sha256": _sha256(summary_path),
            "rows": str(rows_path.resolve()),
            "rows_sha256": _sha256(rows_path),
        },
    )


def _is_exact(row: Mapping[str, object]) -> bool:
    return bool(
        str(row.get("algorithm_status") or "") == "BPC_OPTIMAL"
        and str(row.get("certificate_scope") or "")
        == "BPC_TREE_OPTIMAL"
        and str(row.get("exact_certificate") or "").lower()
        in {"1", "true"}
    )


def _geometric_mean(values: list[float]) -> float | None:
    if not values:
        return None
    return exp(sum(log(value) for value in values) / len(values))


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

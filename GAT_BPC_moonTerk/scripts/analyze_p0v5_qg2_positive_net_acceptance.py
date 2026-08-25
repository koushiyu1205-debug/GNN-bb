#!/usr/bin/env python3
"""Analyze reversible QG2 trials without changing historical 5% gates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import analyze_p0v5_qg2_paired_acceptance as base  # noqa: E402


SCHEMA = "lunar_ice_bpc.p0v5_qg2_positive_net_paired_acceptance.v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control-root", required=True)
    parser.add_argument("--guided-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--mode", choices=("development", "formal"), required=True)
    args = parser.parse_args()
    control_root = base._resolve(args.control_root)
    guided_root = base._resolve(args.guided_root)
    control = base._rows(control_root)
    guided = base._rows(guided_root)
    if set(control) != set(guided):
        raise SystemExit("positive-net paired acceptance instance universe mismatch")
    pairs = []
    for instance_hash in sorted(control):
        left = control[instance_hash]
        right = guided[instance_hash]
        if left["scale"] != right["scale"]:
            raise SystemExit("positive-net paired acceptance scale mismatch")
        objective_match = bool(
            not (left["exact"] and right["exact"])
            or (
                left["objective"] is not None
                and right["objective"] is not None
                and abs(left["objective"] - right["objective"]) <= 2.0e-6
            )
        )
        ratio = (
            right["wall_sec"] / left["wall_sec"]
            if left["exact"] and right["exact"]
            else None
        )
        pairs.append({
            "instance_hash": instance_hash,
            "scale": left["scale"],
            "control": left,
            "guided": right,
            "common_exact": bool(left["exact"] and right["exact"]),
            "objective_match": objective_match,
            "wall_ratio": ratio,
        })
    by_scale = {
        str(scale): base._scale_metrics(
            [row for row in pairs if row["scale"] == scale]
        )
        for scale in sorted({row["scale"] for row in pairs})
    }
    combined_ratio = _positive_net_high_scale_ratio(pairs)
    violations = _positive_net_violations(
        mode=str(args.mode), pairs=pairs, by_scale=by_scale
    )
    payload = {
        "schema_version": SCHEMA,
        "mode": f"positive_net_{args.mode}",
        "historical_five_percent_analyzer_unchanged": True,
        "minimum_speedup_gate_enabled": False,
        "per_scale_maximum_ratio": 1.03,
        "combined_scale30_50_ratio_must_be_below": 1.0,
        "control_root": str(control_root),
        "guided_root": str(guided_root),
        "control_root_hash": base._artifact_tree_hash(control_root),
        "guided_root_hash": base._artifact_tree_hash(guided_root),
        "pairs": pairs,
        "by_scale": by_scale,
        "scale30_50_combined_geomean_wall_ratio": combined_ratio,
        "violation_count": len(violations),
        "violations": violations,
        "passed": not violations,
    }
    output = base._resolve(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "passed": payload["passed"],
        "ratio": combined_ratio,
        "violations": violations,
        "output": str(output),
    }, sort_keys=True))
    return 0 if payload["passed"] else 2


def _positive_net_violations(
    *, mode: str, pairs: list[dict], by_scale: dict
) -> list[str]:
    violations = []
    formal = mode == "formal"
    required = {5, 10, 20, 30, 50} if formal else {30, 50}
    observed = {int(value) for value in by_scale}
    if observed != required:
        violations.append(
            f"scale_universe_mismatch:expected={sorted(required)}:observed={sorted(observed)}"
        )
    if any(not row["objective_match"] for row in pairs):
        violations.append("objective_mismatch")
    if any(
        not row[arm]["redlines_zero"]
        for row in pairs for arm in ("control", "guided")
    ):
        violations.append("correctness_redline")
    for scale in sorted(required & observed):
        row = by_scale[str(scale)]
        if row["guided_exact_count"] < row["control_exact_count"]:
            violations.append(f"scale{scale}_exact_count_regression")
        ratio = row["paired_geomean_wall_ratio"]
        if scale in {5, 10, 20}:
            if formal and row["instance_count"] != 20:
                violations.append(f"scale{scale}_not_full20")
            if formal and row["guided_exact_count"] != 20:
                violations.append(f"scale{scale}_not_20_exact")
            if ratio is None or ratio > 1.01:
                violations.append(f"scale{scale}_time_ratio_above_1.01")
            if row["guided_qg2_inference_event_count"] != 0:
                violations.append(f"scale{scale}_qg2_inference_not_zero")
        elif scale == 30:
            if formal and row["instance_count"] != 20:
                violations.append("scale30_not_full20")
            if formal and row["guided_exact_count"] != 20:
                violations.append("scale30_not_20_exact")
            if ratio is None or ratio > 1.03:
                violations.append("scale30_time_ratio_above_1.03")
        elif scale == 50:
            if formal and row["instance_count"] != 20:
                violations.append("scale50_not_full20")
            if formal and row["guided_exact_count"] < 15:
                violations.append("scale50_exact_below_15")
            if ratio is None or ratio > 1.03:
                violations.append("scale50_time_ratio_above_1.03")
    combined_ratio = _positive_net_high_scale_ratio(pairs)
    if combined_ratio is None or combined_ratio >= 1.0:
        violations.append("scale30_50_combined_positive_net_not_observed")
    if sum(
        int((by_scale.get(str(scale)) or {}).get(
            "guided_qg2_action_count"
        ) or 0)
        for scale in (30, 50)
    ) <= 0:
        violations.append("qg2_action_not_observed")
    return violations


def _positive_net_high_scale_ratio(pairs: list[dict]) -> float | None:
    return base._geomean([
        float(row["wall_ratio"])
        for row in pairs
        if int(row.get("scale") or 0) in {30, 50}
        and bool(row.get("common_exact"))
        and row.get("wall_ratio") is not None
    ])


if __name__ == "__main__":
    raise SystemExit(main())

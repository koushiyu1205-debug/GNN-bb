#!/usr/bin/env python3
"""Analyze the V4 multi-arm GAT candidate without mutating legacy gates.

The historical paired analyzer is part of several immutable V2/V3 execution
freezes.  V4 therefore owns its selector telemetry and positive-net gate in a
separate source file.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import analyze_p0v5_qg2_paired_acceptance as base  # noqa: E402


SCHEMA = "lunar_ice_bpc.p0v5_qg2_realmap_v4_paired_acceptance.v1"
GATE_PROFILE = "v4_positive_net"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control-root", required=True)
    parser.add_argument("--guided-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--mode", choices=("development", "formal"), required=True
    )
    parser.add_argument(
        "--gate-profile", choices=(GATE_PROFILE,), default=GATE_PROFILE
    )
    args = parser.parse_args()
    control_root = base._resolve(args.control_root)
    guided_root = base._resolve(args.guided_root)
    control = _rows(control_root)
    guided = _rows(guided_root)
    if set(control) != set(guided):
        raise SystemExit("V4 paired acceptance instance universe mismatch")

    pairs = []
    for instance_hash in sorted(control):
        left = control[instance_hash]
        right = guided[instance_hash]
        if left["scale"] != right["scale"]:
            raise SystemExit("V4 paired acceptance scale mismatch")
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
        str(scale): _scale_metrics(
            [row for row in pairs if row["scale"] == scale]
        )
        for scale in sorted({row["scale"] for row in pairs})
    }
    violations = _violations(
        mode=str(args.mode), pairs=pairs, by_scale=by_scale,
        gate_profile=str(args.gate_profile),
    )
    payload = {
        "schema_version": SCHEMA,
        "mode": str(args.mode),
        "gate_profile": str(args.gate_profile),
        "legacy_analyzer_unchanged": True,
        "control_root": str(control_root),
        "guided_root": str(guided_root),
        "control_root_hash": base._artifact_tree_hash(control_root),
        "guided_root_hash": base._artifact_tree_hash(guided_root),
        "pairs": pairs,
        "by_scale": by_scale,
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
        "violations": violations,
        "output": str(output),
    }, sort_keys=True))
    return 0 if payload["passed"] else 2


def _rows(root: Path) -> dict[str, dict]:
    rows = base._rows(root)
    for row in rows.values():
        raw = str(row.get("tree_result") or "")
        payload = base._load(Path(raw)) if raw and Path(raw).is_file() else {}
        selector = _v4_selector_telemetry(payload)
        row.update({
            "selector_inference_event_count": selector[
                "inference_event_count"
            ],
            "selector_non_q0_action_count": selector[
                "non_q0_action_count"
            ],
            "selector_action_counts": selector["action_counts"],
            "selector_inference_wall_ms_values": selector[
                "inference_wall_ms_values"
            ],
        })
    return rows


def _v4_selector_telemetry(payload: object) -> dict:
    """Collect selector actions and combined selector plus QG2 ranker wall."""

    action_counts: dict[str, int] = {}
    inference_values: list[float] = []

    def visit(value: object) -> None:
        if isinstance(value, dict):
            action = str(
                value.get("proof_tail_selector_action")
                or value.get("proof_tail_gat_action")
                or ""
            )
            if action in {"Q0", "QG2", "QD1", "QB1"}:
                action_counts[action] = action_counts.get(action, 0) + 1
            selector = base._optional_float(
                value.get("proof_tail_selector_inference_wall_ms")
            )
            ranker = base._optional_float(
                value.get("proof_tail_selector_qg2_ranker_inference_wall_ms")
            )
            legacy = base._optional_float(
                value.get("proof_tail_gat_inference_wall_ms")
            )
            wall = (
                max(0.0, selector or 0.0) + max(0.0, ranker or 0.0)
                if selector is not None or ranker is not None
                else legacy
            )
            if wall is not None and wall > 0.0:
                inference_values.append(float(wall))
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(payload)
    return {
        "inference_event_count": len(inference_values),
        "non_q0_action_count": sum(
            count for action, count in action_counts.items() if action != "Q0"
        ),
        "action_counts": action_counts,
        "inference_wall_ms_values": inference_values,
    }


def _scale_metrics(rows: list[dict]) -> dict:
    result = base._scale_metrics(rows)
    selector_walls = [
        float(value)
        for row in rows
        for value in row["guided"].get(
            "selector_inference_wall_ms_values", ()
        )
    ]
    result.update({
        "guided_selector_inference_event_count": sum(
            int(row["guided"].get("selector_inference_event_count") or 0)
            for row in rows
        ),
        "guided_selector_non_q0_action_count": sum(
            int(row["guided"].get("selector_non_q0_action_count") or 0)
            for row in rows
        ),
        "guided_selector_inference_p99_ms": _quantile(selector_walls, 0.99),
    })
    return result


def _violations(
    *, mode: str, pairs: list[dict], by_scale: dict,
    gate_profile: str = GATE_PROFILE,
) -> list[str]:
    if gate_profile != GATE_PROFILE:
        return [f"unsupported_gate_profile:{gate_profile}"]
    violations = []
    required = {30, 50} if mode == "development" else {5, 10, 20, 30, 50}
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
            if mode == "formal" and row["instance_count"] != 20:
                violations.append(f"scale{scale}_not_full20")
            if mode == "formal" and row["guided_exact_count"] != 20:
                violations.append(f"scale{scale}_not_20_exact")
            if ratio is None or ratio > 1.01:
                violations.append(f"scale{scale}_time_ratio_above_1.01")
            if row["guided_qg2_inference_event_count"] != 0:
                violations.append(f"scale{scale}_qg2_inference_not_zero")
            if int(row.get("guided_selector_inference_event_count") or 0) != 0:
                violations.append(f"scale{scale}_selector_inference_not_zero")
        elif scale == 30:
            if mode == "formal" and row["instance_count"] != 20:
                violations.append("scale30_not_full20")
            if mode == "formal" and row["guided_exact_count"] != 20:
                violations.append("scale30_not_20_exact")
            if ratio is None or ratio >= 1.0:
                violations.append("scale30_not_net_positive")
        elif scale == 50:
            if mode == "formal" and row["instance_count"] != 20:
                violations.append("scale50_not_full20")
            if mode == "formal" and row["guided_exact_count"] < 15:
                violations.append("scale50_exact_below_15")
            if ratio is None or ratio >= 1.0:
                violations.append("scale50_not_net_positive")
        if scale in {30, 50}:
            p99 = row.get("guided_selector_inference_p99_ms")
            if p99 is None or float(p99) > 10.0:
                violations.append(
                    f"scale{scale}_selector_inference_p99_above_10ms"
                )
    if not any(
        int(row.get("guided_selector_non_q0_action_count") or 0) > 0
        for row in by_scale.values()
    ):
        violations.append("selector_non_q0_action_not_observed")
    return violations


def _quantile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    index = max(
        0,
        min(len(ordered) - 1, math.ceil(probability * len(ordered)) - 1),
    )
    return ordered[index]


if __name__ == "__main__":
    raise SystemExit(main())

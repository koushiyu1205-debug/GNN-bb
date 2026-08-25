#!/usr/bin/env python3
"""Recompute P0V5 Exact-control versus QG2 paired acceptance gates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402


SCHEMA = "lunar_ice_bpc.p0v5_qg2_paired_acceptance.v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control-root", required=True)
    parser.add_argument("--guided-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--mode", choices=("development", "formal"), required=True
    )
    args = parser.parse_args()
    control_root = _resolve(args.control_root)
    guided_root = _resolve(args.guided_root)
    control = _rows(control_root)
    guided = _rows(guided_root)
    if set(control) != set(guided):
        raise SystemExit("paired acceptance instance universe mismatch")
    pairs = []
    for instance_hash in sorted(control):
        left = control[instance_hash]
        right = guided[instance_hash]
        if left["scale"] != right["scale"]:
            raise SystemExit("paired acceptance scale mismatch")
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
    violations = _violations(mode=str(args.mode), pairs=pairs, by_scale=by_scale)
    payload = {
        "schema_version": SCHEMA,
        "mode": str(args.mode),
        "control_root": str(control_root),
        "guided_root": str(guided_root),
        "control_root_hash": _artifact_tree_hash(control_root),
        "guided_root_hash": _artifact_tree_hash(guided_root),
        "pairs": pairs,
        "by_scale": by_scale,
        "violation_count": len(violations),
        "violations": violations,
        "passed": not violations,
    }
    output = _resolve(args.output)
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
    result = {}
    for path in sorted(root.rglob("b4_2_cold_exact_rows.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            for raw in csv.DictReader(handle):
                instance_path = _resolve(raw["instance_path"])
                instance_hash = str(
                    load_lunar_ice_data(
                        json.loads(instance_path.read_text(encoding="utf-8"))
                    ).instance_content_hash
                )
                if instance_hash in result:
                    raise SystemExit(
                        f"duplicate paired acceptance instance: {instance_hash}"
                    )
                tree = (
                    path.parent
                    / "proofs"
                    / f"scale_{int(raw['scale']):03d}"
                    / str(raw["instance_key"])
                    / "tree_closure_results"
                    / "tree_closure_001.json"
                )
                tree_payload = _load(tree) if tree.is_file() else {}
                qg2 = _qg2_telemetry(tree_payload)
                result[instance_hash] = {
                    "scale": int(raw["scale"]),
                    "instance_key": str(raw["instance_key"]),
                    "instance_path": str(instance_path),
                    "algorithm_status": str(raw.get("algorithm_status") or ""),
                    "exact": bool(
                        str(raw.get("algorithm_status") or "") == "BPC_OPTIMAL"
                        and _boolean(raw.get("exact_certificate"))
                        and _boolean(raw.get("bpc_tree_optimal"))
                    ),
                    "objective": _optional_float(
                        tree_payload.get("incumbent_objective")
                    ),
                    "wall_sec": max(
                        1.0e-9,
                        float(raw.get("cold_start_total_sec") or 0.0),
                    ),
                    "redlines_zero": _redlines_zero(raw),
                    "qg2_inference_event_count": qg2["inference_event_count"],
                    "qg2_action_count": qg2["qg2_action_count"],
                    "qg2_total_inference_wall_ms": qg2[
                        "total_inference_wall_ms"
                    ],
                    "row_csv": str(path),
                    "tree_result": str(tree) if tree.is_file() else "",
                }
    if not result:
        raise SystemExit(f"no paired acceptance rows found under {root}")
    return result


def _redlines_zero(row: dict) -> bool:
    zero_fields = (
        "certificate_leak",
        "manual_rc_fail",
        "pricing_rc_fail",
        "tail_dual_certificate_leak",
        "worker_certificate_leak",
        "true_dual_rc_recompute_missing",
    )
    return bool(
        _boolean(row.get("no_cheat_pass"))
        and all(_zeroish(row.get(key)) for key in zero_fields)
    )


def _qg2_telemetry(payload: object) -> dict:
    inference_events = 0
    actions = 0
    inference_wall = 0.0

    def visit(value: object) -> None:
        nonlocal inference_events, actions, inference_wall
        if isinstance(value, dict):
            action = str(value.get("proof_tail_gat_action") or "")
            wall = _optional_float(
                value.get("proof_tail_gat_inference_wall_ms")
            )
            if action == "QG2":
                actions += 1
            if wall is not None and wall > 0.0:
                inference_events += 1
                inference_wall += wall
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(payload)
    return {
        "inference_event_count": inference_events,
        "qg2_action_count": actions,
        "total_inference_wall_ms": inference_wall,
    }


def _scale_metrics(rows: list[dict]) -> dict:
    common = [row for row in rows if row["common_exact"]]
    ratios = [float(row["wall_ratio"]) for row in common]
    return {
        "instance_count": len(rows),
        "control_exact_count": sum(row["control"]["exact"] for row in rows),
        "guided_exact_count": sum(row["guided"]["exact"] for row in rows),
        "common_exact_count": len(common),
        "paired_geomean_wall_ratio": _geomean(ratios),
        "objective_mismatch_count": sum(
            not row["objective_match"] for row in rows
        ),
        "control_redline_count": sum(
            not row["control"]["redlines_zero"] for row in rows
        ),
        "guided_redline_count": sum(
            not row["guided"]["redlines_zero"] for row in rows
        ),
        "guided_qg2_inference_event_count": sum(
            row["guided"]["qg2_inference_event_count"] for row in rows
        ),
        "guided_qg2_action_count": sum(
            row["guided"]["qg2_action_count"] for row in rows
        ),
    }


def _violations(*, mode: str, pairs: list[dict], by_scale: dict) -> list[str]:
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
        elif scale == 30:
            if mode == "formal" and row["instance_count"] != 20:
                violations.append("scale30_not_full20")
            if mode == "formal" and row["guided_exact_count"] != 20:
                violations.append("scale30_not_20_exact")
            if ratio is None or ratio > 0.95:
                violations.append("scale30_speedup_below_5pct")
        elif scale == 50:
            if mode == "formal" and row["instance_count"] != 20:
                violations.append("scale50_not_full20")
            if mode == "formal" and row["guided_exact_count"] < 15:
                violations.append("scale50_exact_below_15")
            if ratio is None or ratio > 0.95:
                violations.append("scale50_speedup_below_5pct")
    return violations


def _artifact_tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    paths = set()
    for pattern in (
        "**/b4_2_cold_exact_rows.csv",
        "**/b4_2_cold_exact_state.json",
        "**/b4_2_cold_exact_summary.json",
        "**/tree_closure_001.json",
    ):
        paths.update(root.glob(pattern))
    for path in sorted(paths):
        digest.update(str(path.relative_to(root)).encode("utf-8"))
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _geomean(values: list[float]) -> float | None:
    if not values:
        return None
    return math.exp(
        statistics.fmean(math.log(max(1.0e-12, value)) for value in values)
    )


def _boolean(value) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _zeroish(value) -> bool:
    normalized = str(value or "").strip().lower()
    if normalized in {"", "false", "no", "off"}:
        return True
    try:
        return float(normalized) == 0.0
    except ValueError:
        return False


def _optional_float(value) -> float | None:
    if value is None or value == "":
        return None
    parsed = float(value)
    return parsed if math.isfinite(parsed) else None


def _resolve(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())

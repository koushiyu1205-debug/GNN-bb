#!/usr/bin/env python3
"""Evaluate a development-only gate for starting QG2 model training.

This gate deliberately authorizes *training only*.  It cannot authorize model
deployment, exact certificates, or a paper-level GAT claim.  The stricter
calibration, heldout, and end-to-end gates remain downstream requirements.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import statistics


ROOT = Path(__file__).resolve().parents[1]
ORACLE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
GATE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_relaxed_training_gate.v1"
SUPERVISION_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_action_reachable_supervision.v2"
)
ACTION_SURFACE = "same_terminal_class_and_reduced_cost_bucket.v1"
SCALES = (30, 50)

DEFAULT_THRESHOLDS = {
    "minimum_determined_contexts_per_scale": 20,
    "minimum_gain_5pct_contexts_per_scale": 5,
    "minimum_positive_instances_per_scale": 5,
    "maximum_paired_geomean_ratio": 0.95,
    "maximum_instance_bootstrap_95_upper": 0.98,
    "maximum_instance_saved_wall_fraction": 0.35,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle-summary", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    oracle_path = _resolve(args.oracle_summary)
    output_path = _resolve(args.output)
    oracle = _load(oracle_path)
    result = evaluate_relaxed_training_gate(oracle)
    payload = {
        "schema_version": GATE_SCHEMA,
        "development_only": True,
        "deployable": False,
        "authority": "exploratory_model_training_only",
        "deployment_authorized": False,
        "paper_claim_authorized": False,
        "oracle_summary": str(oracle_path),
        "oracle_summary_sha256": _sha256(oracle_path),
        **result,
    }
    _write(output_path, payload)
    print(json.dumps(payload["gate"], sort_keys=True), flush=True)
    return 0 if payload["training_authorized"] else 2


def evaluate_relaxed_training_gate(
    oracle: dict,
    *,
    thresholds: dict | None = None,
) -> dict:
    limits = dict(DEFAULT_THRESHOLDS)
    limits.update(dict(thresholds or {}))
    contract_errors = _contract_errors(oracle)
    rows = [dict(row) for row in oracle.get("context_rows") or ()]
    initial_rows = [dict(row) for row in oracle.get("initial_rows") or ()]
    all_safe = bool(rows) and all(
        bool(row.get("all_safe")) for row in rows
    ) and all(
        bool(row.get("all_initial_arms_safe"))
        for row in initial_rows
        if row.get("compliant_context")
    )

    per_scale = {}
    for scale in SCALES:
        determined = [
            row for row in rows
            if int(row.get("scale") or 0) == scale
            and bool(row.get("outcome_determined"))
        ]
        gain_rows = [
            row for row in determined if float(row["ratio"]) <= 0.95
        ]
        ratios = [float(row["ratio"]) for row in determined]
        bootstrap_upper = _instance_bootstrap_upper(determined)
        metrics = {
            "determined_context_count": len(determined),
            "determined_instance_count": len({
                str(row["instance_hash"]) for row in determined
            }),
            "gain_5pct_context_count": len(gain_rows),
            "positive_instance_count": len({
                str(row["instance_hash"]) for row in gain_rows
            }),
            "paired_geomean_ratio": _geomean_or_none(ratios),
            "instance_bootstrap_95_upper": bootstrap_upper,
            "positive_fraction": (
                sum(float(row["ratio"]) < 1.0 for row in determined)
                / max(1, len(determined))
            ),
        }
        metrics["passed"] = bool(
            len(determined)
            >= int(limits["minimum_determined_contexts_per_scale"])
            and len(gain_rows)
            >= int(limits["minimum_gain_5pct_contexts_per_scale"])
            and metrics["positive_instance_count"]
            >= int(limits["minimum_positive_instances_per_scale"])
            and metrics["paired_geomean_ratio"] is not None
            and float(metrics["paired_geomean_ratio"])
            <= float(limits["maximum_paired_geomean_ratio"])
            and bootstrap_upper is not None
            and float(bootstrap_upper)
            <= float(limits["maximum_instance_bootstrap_95_upper"])
        )
        per_scale[f"scale{scale}"] = metrics

    saved_by_instance: dict[str, float] = {}
    for row in rows:
        if not bool(row.get("outcome_determined")):
            continue
        key = str(row["instance_hash"])
        saved_by_instance[key] = saved_by_instance.get(key, 0.0) + max(
            0.0, float(row.get("saved_wall_sec") or 0.0)
        )
    total_saved = sum(saved_by_instance.values())
    max_saved_fraction = (
        max(saved_by_instance.values(), default=0.0) / total_saved
        if total_saved > 0.0
        else 1.0
    )
    passed = bool(
        not contract_errors
        and all_safe
        and all(per_scale[f"scale{scale}"]["passed"] for scale in SCALES)
        and max_saved_fraction
        <= float(limits["maximum_instance_saved_wall_fraction"])
    )
    return {
        "supervision_schema_version": SUPERVISION_SCHEMA,
        "queue_action_surface": ACTION_SURFACE,
        "thresholds": limits,
        "strict_oracle_gate": dict(oracle.get("oracle_gate") or {}),
        "gate": {
            "passed": passed,
            "reason": (
                "relaxed_training_gate_passed"
                if passed
                else "relaxed_training_gate_failed"
            ),
            "all_exact_safe": all_safe,
            "contract_errors": contract_errors,
            "maximum_instance_saved_wall_fraction": max_saved_fraction,
            **per_scale,
        },
        "training_authorized": passed,
    }


def _contract_errors(oracle: dict) -> list[str]:
    errors = []
    if oracle.get("schema_version") != ORACLE_SCHEMA:
        errors.append("oracle_schema_mismatch")
    if not bool(oracle.get("development_only")) or bool(
        oracle.get("deployable")
    ):
        errors.append("oracle_safety_contract_mismatch")
    if oracle.get("supervision_schema_version") != SUPERVISION_SCHEMA:
        errors.append("supervision_schema_mismatch")
    if oracle.get("queue_action_surface") != ACTION_SURFACE:
        errors.append("queue_action_surface_mismatch")
    freeze_path = str(oracle.get("execution_freeze") or "")
    freeze_sha = str(oracle.get("execution_freeze_sha256") or "")
    if not freeze_path or not freeze_sha:
        errors.append("execution_freeze_binding_missing")
    else:
        resolved = _resolve(freeze_path)
        if not resolved.is_file() or _sha256(resolved) != freeze_sha:
            errors.append("execution_freeze_hash_mismatch")
    return errors


def _instance_bootstrap_upper(rows: list[dict]) -> float | None:
    if not rows:
        return None
    groups: dict[str, list[float]] = {}
    for row in rows:
        groups.setdefault(str(row["instance_hash"]), []).append(
            float(row["ratio"])
        )
    keys = sorted(groups)
    rng = random.Random(20260801)
    values = []
    for _ in range(10_000):
        draw = [keys[rng.randrange(len(keys))] for _ in keys]
        ratios = [value for key in draw for value in groups[key]]
        values.append(_geomean(ratios))
    values.sort()
    return values[9750]


def _geomean_or_none(values: list[float]) -> float | None:
    return _geomean(values) if values else None


def _geomean(values: list[float]) -> float:
    return math.exp(statistics.fmean(
        math.log(max(1.0e-12, float(value))) for value in values
    ))


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

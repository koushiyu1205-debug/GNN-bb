#!/usr/bin/env python3
"""Bind matched exact P0/action wall-time evidence to opportunity rows."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path

from lunar_ice_bpc.guidance.opportunity_gate import (
    attach_matched_end_to_end_benefit,
    validate_opportunity_observation,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--observations-jsonl", required=True)
    parser.add_argument("--measurements-jsonl", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--risk-kappa", type=float, default=1.96)
    parser.add_argument("--objective-tolerance", type=float, default=1.0e-8)
    parser.add_argument(
        "--require-every-identifiable-positive",
        action="store_true",
        help=(
            "Fail instead of leaving a positive pressure observation without "
            "matched end-to-end timing evidence."
        ),
    )
    args = parser.parse_args()

    observations = [
        validate_opportunity_observation(json.loads(line))
        for line in Path(args.observations_jsonl)
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    by_observation = defaultdict(list)
    for line in Path(args.measurements_jsonl).read_text(
        encoding="utf-8"
    ).splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        by_observation[str(row.get("observation_id") or "")].append(row)

    output_rows = []
    missing = []
    used_measurement_ids: set[str] = set()
    for row in observations:
        observation_id = str(row["observation_id"])
        measurements = by_observation.get(observation_id, [])
        needs_measurement = bool(
            row["formal_label_available"]
            and row["action_value_identifiable"]
            and float(row["oracle_solver_gain"]) > 0.0
        )
        if measurements:
            row = attach_matched_end_to_end_benefit(
                row,
                measurements,
                risk_kappa=float(args.risk_kappa),
                objective_tolerance=float(args.objective_tolerance),
            )
            used_measurement_ids.add(observation_id)
        elif needs_measurement:
            missing.append(observation_id)
        output_rows.append(row)
    unknown_measurements = sorted(
        set(by_observation).difference(
            str(row["observation_id"]) for row in observations
        )
    )
    if unknown_measurements:
        raise SystemExit(
            "measurements reference unknown observations: "
            + ",".join(unknown_measurements[:5])
        )
    if args.require_every_identifiable_positive and missing:
        raise SystemExit(
            "positive observations lack end-to-end measurements: "
            + ",".join(missing[:5])
        )

    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in output_rows
        ),
        encoding="utf-8",
    )
    report = {
        "schema_version": (
            "lunar_ice_bpc.gat_end_to_end_benefit_binding_report.v1"
        ),
        "observation_count": len(output_rows),
        "benefit_bound_count": len(used_measurement_ids),
        "missing_positive_measurement_count": len(missing),
        "unknown_measurement_count": 0,
        "risk_kappa": float(args.risk_kappa),
        "objective_tolerance": float(args.objective_tolerance),
        "model_cost_kept_separate": True,
        "output": str(target.resolve()),
    }
    target.with_suffix(target.suffix + ".report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(str(target.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

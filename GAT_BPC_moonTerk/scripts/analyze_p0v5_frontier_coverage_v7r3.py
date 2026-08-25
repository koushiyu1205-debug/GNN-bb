#!/usr/bin/env python3
"""Stable natural-frontier coverage audit for the V7R3 repair chain."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.p0v5_frontier_observability_v7r_common import (  # noqa: E402
    assert_active, load, update_state, wilson_interval, write_once, write_terminal,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_frontier_observability_root_cause_v7r3_20260818"


def stable_binomial_tail_at_least(trials: int, target: int, probability: float) -> float:
    """Return P[X>=target] without materializing huge binomial coefficients."""

    if target <= 0:
        return 1.0
    if trials < target or probability <= 0.0:
        return 0.0
    if probability >= 1.0:
        return 1.0
    q = 1.0 - probability
    term = q ** trials
    lower_cdf = term
    odds = probability / q
    for k in range(target - 1):
        term *= (trials - k) / (k + 1) * odds
        lower_cdf += term
    return min(1.0, max(0.0, 1.0 - lower_cdf))


def stable_candidate_cap(target: int, probability: float, confidence: float = 0.95,
                         maximum: int = 5000) -> int | None:
    for trials in range(target, maximum + 1):
        if stable_binomial_tail_at_least(trials, target, probability) >= confidence:
            return trials
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    assert_active(run_root, "COVERAGE_AUDIT")
    config = load(run_root / "config.freeze.json")
    evidence = load(run_root / "coverage_evidence.freeze.json")
    confidence = float(config["coverage_audit"]["confidence"])
    targets = list(map(int, config["coverage_audit"]["target_eligible_instances"]))
    rows = []
    for raw in evidence["cohorts"]:
        successes, trials = int(raw["successes"]), int(raw["trials"])
        lower, upper = wilson_interval(successes, trials, confidence)
        mle = successes / trials
        rows.append({
            **raw,
            "hit_rate": mle,
            "wilson95_lower": lower,
            "wilson95_upper": upper,
            "candidate_caps": {
                str(target): {
                    "mle_probability_cap": stable_candidate_cap(target, mle, confidence),
                    "wilson_lower_probability_cap": stable_candidate_cap(
                        target, lower, confidence
                    ),
                } for target in targets
            },
        })
    primary_name = config["coverage_audit"]["primary_cohort"]
    primary = next(row for row in rows if row["cohort"] == primary_name)
    maximum = int(config["coverage_audit"]["maximum_repaired_candidate_cap"])
    required = primary["candidate_caps"][str(max(targets))][
        "wilson_lower_probability_cap"
    ]
    feasible = required is not None and required <= maximum
    report = {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_coverage_audit.v2",
        "decision": "PASS" if feasible else "FAIL",
        "reason": None if feasible else "INSUFFICIENT_NATURAL_CONTEXT_COVERAGE",
        "primary_cohort": primary_name,
        "primary_interpretation": (
            "V7 generator/engine scale30 is the conservative planning cohort; "
            "the Wilson-lower cap controls a future census."
        ),
        "binomial_tail_algorithm": "stable_lower_cdf_recurrence_v1",
        "maximum_repaired_candidate_cap": maximum,
        "required_cap_for_largest_target": required,
        "rows": rows,
        "candidate_outcomes_read": 0,
    }
    write_once(run_root / "coverage_hit_rate.report.json", report)
    if not feasible:
        write_terminal(run_root, report["reason"], "COVERAGE_AUDIT", report)
    else:
        update_state(run_root, "FEATURE_SUFFICIENCY")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Estimate natural-frontier hit rates and honest candidate caps for V7R."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.p0v5_frontier_observability_v7r_common import (  # noqa: E402
    DEFAULT_RUN_ROOT, assert_active, candidate_cap, load, update_state,
    wilson_interval, write_once, write_terminal,
)


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
                    "mle_probability_cap": candidate_cap(target, mle, confidence),
                    "wilson_lower_probability_cap": candidate_cap(target, lower, confidence),
                } for target in targets
            },
        })
    primary_name = config["coverage_audit"]["primary_cohort"]
    primary = next(row for row in rows if row["cohort"] == primary_name)
    maximum = int(config["coverage_audit"]["maximum_repaired_candidate_cap"])
    required = primary["candidate_caps"][str(max(targets))]["wilson_lower_probability_cap"]
    feasible = required is not None and required <= maximum
    report = {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_coverage_audit.v1",
        "decision": "PASS" if feasible else "FAIL",
        "reason": None if feasible else "INSUFFICIENT_NATURAL_CONTEXT_COVERAGE",
        "primary_cohort": primary_name,
        "primary_interpretation": (
            "V7 generator/engine scale30 is the conservative planning cohort; "
            "the Wilson-lower cap, not the observed-rate cap, controls a future census."
        ),
        "maximum_repaired_candidate_cap": maximum,
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

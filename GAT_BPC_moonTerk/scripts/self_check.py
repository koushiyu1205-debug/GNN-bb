#!/usr/bin/env python3
"""Generate, validate, solve, and draw one 5-target lunar-ice instance."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.domain.scheduling import generate_instance
from lunar_ice_bpc.domain.visualization import write_svg
from lunar_ice_bpc.io.instance_io import validate_instance, write_json
from lunar_ice_bpc.runners.solve import solve_reference


def main() -> int:
    instance = generate_instance(5, seed=629001, index=1)
    issues = validate_instance(instance)
    if issues:
        print("validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 2
    instance_path = ROOT / "runs" / "self_check" / "instance_005_seed629001_logical_graph.json"
    solution_path = ROOT / "runs" / "self_check" / "instance_005_seed629001_solution.json"
    figure_path = ROOT / "runs" / "self_check" / "instance_005_seed629001.svg"
    write_json(instance_path, instance)
    result = solve_reference(instance_path, solution_path)
    write_svg(instance_path, figure_path, solution_path=solution_path)
    print(f"instance={instance_path}")
    print(f"solution={solution_path}")
    print(f"figure={figure_path}")
    print(f"status={result['status']} exact_status={result['exact_status']}")
    return 0 if result["status"] in {"FEASIBLE_REFERENCE", "CANONICAL_DP_BASELINE_OPTIMAL", "DIRECT_DP_BASELINE_OPTIMAL"} else 3


if __name__ == "__main__":
    raise SystemExit(main())

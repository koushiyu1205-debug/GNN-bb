#!/usr/bin/env python3
"""Materialize the one grid-selected DSSR V2 development configuration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = ROOT / "configs" / "dssr_v2_candidate_base.yaml"
DEFAULT_GRID = (
    ROOT
    / "runs"
    / "dssr_v2_development_20260729"
    / "sentinel_grid"
    / "summary.json"
)
DEFAULT_OUTPUT = ROOT / "configs" / "dssr_v2_selected.yaml"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-config", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--grid-summary", type=Path, default=DEFAULT_GRID)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    grid = json.loads(
        args.grid_summary.read_text(encoding="utf-8")
    )
    if not grid.get("freeze_allowed"):
        raise SystemExit(
            "sentinel grid did not pass; selected config cannot be materialized"
        )
    selected = dict(grid.get("selected_configuration") or {})
    if not selected:
        raise SystemExit("sentinel grid has no selected configuration")
    config = yaml.safe_load(
        args.base_config.read_text(encoding="utf-8")
    )
    config["model_id"] = "DSSR_V2_GRID_SELECTED_CANDIDATE"
    config["dssr_pressure_max_bucket_size"] = int(
        selected["bucket_limit"]
    )
    config["dssr_pressure_max_candidate_checks"] = int(
        selected["candidate_check_limit"]
    )
    config["dssr_grid_binding"] = {
        "schema_version": grid["schema_version"],
        "config_id": selected["config_id"],
        "regression_gate_pass": True,
        "selection_order": list(grid["selection_order"]),
    }
    output = args.output.resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite selected config: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        yaml.safe_dump(
            config,
            handle,
            allow_unicode=True,
            sort_keys=False,
        )
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())

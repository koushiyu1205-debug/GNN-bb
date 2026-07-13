#!/usr/bin/env python3
"""Generate one reproducible synthetic lunar-ice acceptance instance."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.domain.scheduling import generate_instance
from lunar_ice_bpc.io.instance_io import validate_instance, write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--index", type=int, default=1)
    parser.add_argument("--output", default=None)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    output = _project_path(args.output) if args.output else _project_path(
        f"data/instances/lunar_ice_sp50_{args.scale:03d}/"
        f"instance_{args.index:03d}_logical_graph.json"
    )
    instance = generate_instance(int(args.scale), seed=int(args.seed), index=int(args.index))
    write_json(output, instance)
    issues = validate_instance(instance)
    accepted = bool((instance.get("validation") or {}).get("accepted"))
    print(f"wrote {output}")
    print("generator: lunar_ice_bpc.domain.scheduling.generate_instance")
    print(f"validation_reason: {(instance.get('validation') or {}).get('reason')}")
    print(f"schema_issues: {len(issues)}")
    if issues:
        for issue in issues[:10]:
            print(f"- {issue}")
    if args.strict and (issues or not accepted):
        return 2
    return 0


def _project_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())

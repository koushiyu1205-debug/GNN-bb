#!/usr/bin/env python3
"""Audit the current lunar-ice refactor state."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.runners.refactor_audit import audit_refactor_state


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=str(ROOT))
    parser.add_argument("--manifest", default=None)
    parser.add_argument("--output-json", default=None)
    parser.add_argument("--validate-all-instances", action="store_true")
    parser.add_argument("--instance-samples-per-scale", type=int, default=1)
    parser.add_argument("--strict-final", action="store_true")
    args = parser.parse_args()

    payload = audit_refactor_state(
        args.project_root,
        manifest_path=args.manifest,
        output_json=args.output_json,
        validate_all_instances=bool(args.validate_all_instances),
        instance_samples_per_scale=int(args.instance_samples_per_scale),
    )
    print(
        "refactor audit {status}; hard_failures={hard}; incomplete={incomplete}; output={output}".format(
            status=payload["overall_status"],
            hard=len(payload["hard_failure_sections"]),
            incomplete=len(payload["incomplete_sections"]),
            output=args.output_json or "<none>",
        )
    )
    if payload["overall_status"] == "FAIL":
        return 1
    if args.strict_final and payload["overall_status"] != "COMPLETE":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

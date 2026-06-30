#!/usr/bin/env python3
"""Audit lunar-ice benchmark CSV results against scale acceptance targets."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.runners.audit import audit_benchmark_csv


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-csv", required=True)
    parser.add_argument("--output-json", default=None)
    parser.add_argument("--scales", default=None)
    parser.add_argument("--expected-per-scale", type=int, default=20)
    args = parser.parse_args()
    payload = audit_benchmark_csv(
        _root_path(args.results_csv),
        output_json=_root_path(args.output_json) if args.output_json else None,
        scales=_parse_scales(args.scales),
        expected_per_scale=int(args.expected_per_scale),
    )
    print(
        "audit {overall_status}; scales={scale_labels}; output={output}".format(
            overall_status=payload["overall_status"],
            scale_labels=payload["scale_labels"],
            output=args.output_json or "<none>",
        )
    )
    return 0 if payload["overall_status"] == "PASS" else 1


def _root_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def _parse_scales(value: str | None) -> list[int] | None:
    if value is None or not str(value).strip():
        return None
    return [int(item.strip()) for item in str(value).split(",") if item.strip()]


if __name__ == "__main__":
    raise SystemExit(main())

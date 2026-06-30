#!/usr/bin/env python3
"""Draw a lunar-ice instance as an SVG resource/solution map."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.domain.visualization import write_svg


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--solution", default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    instance_path = Path(args.instance)
    if not instance_path.is_absolute():
        instance_path = ROOT / instance_path
    solution_path = Path(args.solution) if args.solution else None
    if solution_path is not None and not solution_path.is_absolute():
        solution_path = ROOT / solution_path
    output = Path(args.output) if args.output else ROOT / "runs" / "figures" / f"{instance_path.stem}.svg"
    if not output.is_absolute():
        output = ROOT / output
    path = write_svg(instance_path, output, solution_path=solution_path)
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


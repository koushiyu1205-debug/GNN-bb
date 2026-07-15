#!/usr/bin/env python3
"""Draw publication-style lunar south-pole base maps from a preview JSON."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.domain.scientific_visualization import draw_real_map_basemaps


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Draw DEM, risk, resource, illumination, and atlas base maps without graph overlays."
    )
    parser.add_argument(
        "--preview-json",
        default="data/processed/real_maps/south_pole_sp50_preview.json",
        help="real-map preview JSON (default: current SP50 benchmark preview)",
    )
    parser.add_argument("--output-dir", default="runs/figures/basemaps")
    parser.add_argument("--prefix", default=None)
    args = parser.parse_args()

    preview_path = _project_path(args.preview_json)
    output_dir = _project_path(args.output_dir)
    written = draw_real_map_basemaps(preview_path, output_dir, prefix=args.prefix)
    for label, path in written.items():
        print(f"{label}: {path}")
    return 0


def _project_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())

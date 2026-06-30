#!/usr/bin/env python3
"""Draw a real lunar south-pole raster preview when local GeoTIFFs are ready."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.domain.real_maps import (
    DEFAULT_SP50_DEPOT_CENTER_KM,
    build_real_map_preview,
    real_map_source_catalog,
    select_south_pole_depot_center,
    write_real_map_dem_svg,
    write_real_map_preview_svg,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-map-dir", default="data/raw_maps")
    parser.add_argument("--output-json", default="data/processed/real_maps/south_pole_sp50_preview.json")
    parser.add_argument("--output-svg", default="runs/figures/lunar_real_map_sp50_preview.svg")
    parser.add_argument("--output-dem-svg", default="runs/figures/lunar_real_map_sp50_dem.svg")
    parser.add_argument("--source-catalog-output", default="data/manifests/lunar_real_map_source_catalog.json")
    parser.add_argument("--center-x-km", type=float, default=None)
    parser.add_argument("--center-y-km", type=float, default=None)
    parser.add_argument("--extent-km", type=float, default=50.0)
    parser.add_argument("--cells", type=int, default=500)
    parser.add_argument("--target-count", type=int, default=100)
    parser.add_argument("--path-target-count", type=int, default=3)
    parser.add_argument("--active-footprint-km", type=float, default=50.0)
    parser.add_argument("--fixed-south-pole-center", action="store_true")
    parser.add_argument("--auto-select-depot", action="store_true")
    parser.add_argument("--allow-remote", action="store_true")
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    raw_map_dir = _project_path(args.raw_map_dir)
    output_json = _project_path(args.output_json)
    output_svg = _project_path(args.output_svg)
    output_dem_svg = _project_path(args.output_dem_svg)
    source_catalog_output = _project_path(args.source_catalog_output)
    center_x = args.center_x_km
    center_y = args.center_y_km
    depot_selection = None
    if args.auto_select_depot and not args.fixed_south_pole_center and (center_x is None or center_y is None):
        depot_selection = select_south_pole_depot_center(raw_map_dir=raw_map_dir)
        if depot_selection.get("status") == "DEPOT_SELECTED":
            center_x, center_y = depot_selection["global_xy_km"]
    elif not args.fixed_south_pole_center and (center_x is None or center_y is None):
        center_x, center_y = DEFAULT_SP50_DEPOT_CENTER_KM
        depot_selection = {
            "status": "DEPOT_DEFAULT_DENSE_WATER_ICE_RIDGE",
            "global_xy_km": [round(float(center_x), 6), round(float(center_y), 6)],
            "selection_policy": "fixed_sp50_dense_water_ice_depot_v1",
        }
    if center_x is None:
        center_x = 0.0
    if center_y is None:
        center_y = 0.0

    catalog = real_map_source_catalog(raw_map_dir)
    _write_json(source_catalog_output, catalog)
    preview = build_real_map_preview(
        raw_map_dir=raw_map_dir,
        center_x_km=float(center_x),
        center_y_km=float(center_y),
        extent_km=args.extent_km,
        output_cells=args.cells,
        target_count=args.target_count,
        path_target_count=args.path_target_count,
        active_footprint_km=args.active_footprint_km,
        allow_remote=args.allow_remote,
        allow_partial=args.allow_partial,
    )
    if depot_selection is not None:
        preview["depot_selection"] = depot_selection
    preview["depot"]["global_xy_km"] = [round(float(center_x), 6), round(float(center_y), 6)]
    _write_json(output_json, preview)
    write_real_map_preview_svg(preview, output_svg)
    write_real_map_dem_svg(preview, output_dem_svg)

    print(f"status: {preview['status']}")
    print(f"source catalog: {source_catalog_output}")
    print(f"preview json: {output_json}")
    print(f"preview svg: {output_svg}")
    print(f"dem svg: {output_dem_svg}")
    print(f"center_xy_km: {float(center_x):.6f}, {float(center_y):.6f}")
    missing = preview.get("missing_required_lola_layers") or []
    if missing:
        print("missing required LOLA layers: " + ", ".join(missing))
    if args.strict and preview["status"] != "REAL_MAP_PREVIEW_READY":
        return 2
    return 0


def _project_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

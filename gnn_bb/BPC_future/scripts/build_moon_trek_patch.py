#!/usr/bin/env python3
"""Download a Moon Trek patch and build deterministic risk rasters."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from BPC_future.preprocess.moon_trek_client import (  # noqa: E402
    PatchSpec,
    SITE_PRESETS,
    download_export_image,
    fetch_image_service_metadata,
    write_json,
)
from BPC_future.preprocess.risk_model import (  # noqa: E402
    RiskModelConfig,
    build_risk_layer,
    derive_slope_from_dem,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a deterministic Moon Trek risk patch.")
    parser.add_argument("--site", choices=sorted(SITE_PRESETS.keys()), default="apollo15")
    parser.add_argument("--output-dir")
    parser.add_argument("--center-lon", type=float)
    parser.add_argument("--center-lat", type=float)
    parser.add_argument("--width-km", type=float)
    parser.add_argument("--height-km", type=float)
    parser.add_argument("--pixels", type=int)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--impassable-slope-deg", type=float, default=30.0)
    parser.add_argument("--high-risk-slope-deg", type=float, default=20.0)
    parser.add_argument("--roughness-reference-m", type=float, default=5.0)
    parser.add_argument("--slope-weight", type=float, default=0.75)
    parser.add_argument("--roughness-weight", type=float, default=0.25)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dem_layer, slope_layer, default_patch, site_note, derive_slope = SITE_PRESETS[str(args.site)]
    output = Path(args.output_dir or f"BPC_future/data/moon_trek/{default_patch.name}")
    raw = output / "raw"
    metadata_dir = output / "metadata"
    processed = output / "processed"
    patch = PatchSpec(
        name=output.name,
        center_lon=float(args.center_lon if args.center_lon is not None else default_patch.center_lon),
        center_lat=float(args.center_lat if args.center_lat is not None else default_patch.center_lat),
        width_km=float(args.width_km if args.width_km is not None else default_patch.width_km),
        height_km=float(args.height_km if args.height_km is not None else default_patch.height_km),
        pixels=int(args.pixels if args.pixels is not None else default_patch.pixels),
    )
    metadata_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        metadata_dir / "bbox.json",
        {
            "patch": asdict(patch),
            "bbox": patch.bbox,
            "approximate_pixel_size_m": patch.approximate_pixel_size_m,
            "site": str(args.site),
            "site_note": site_note,
        },
    )

    print(f"Downloading Moon Trek {args.site} patch to {output}")
    print(f"bbox={patch.bbox}, pixels={patch.pixels}, approx_pixel={patch.approximate_pixel_size_m:.3f}m")
    service_metadata = {
        "site": str(args.site),
        "site_note": site_note,
        "dem": fetch_image_service_metadata(dem_layer),
        "slope": (
            fetch_image_service_metadata(slope_layer)
            if slope_layer is not None
            else {"derived_from_dem": True, "method": "central_gradient_slope_from_dem"}
        ),
    }
    write_json(metadata_dir / "moon_trek_sources.json", service_metadata)

    started = time.time()
    dem_info = download_export_image(dem_layer, patch, raw / "dem.tif", force=bool(args.force))
    if slope_layer is not None:
        slope_info = download_export_image(slope_layer, patch, raw / "slope.tif", force=bool(args.force))
    elif derive_slope:
        slope_info = derive_slope_from_dem(
            raw / "dem.tif",
            raw / "slope.tif",
            width_km=patch.width_km,
            height_km=patch.height_km,
        )
    else:
        raise ValueError(f"site {args.site!r} has no slope layer and derive_slope_from_dem is disabled")
    manifest = {
        "site": str(args.site),
        "site_note": site_note,
        "patch": asdict(patch),
        "bbox": patch.bbox,
        "approximate_pixel_size_m": patch.approximate_pixel_size_m,
        "downloads": {
            "dem": dem_info,
            "slope": slope_info,
        },
        "elapsed_download_seconds": round(time.time() - started, 3),
    }
    write_json(metadata_dir / "download_manifest.json", manifest)

    risk_config = RiskModelConfig(
        impassable_slope_deg=float(args.impassable_slope_deg),
        high_risk_slope_deg=float(args.high_risk_slope_deg),
        roughness_reference_m=float(args.roughness_reference_m),
        slope_weight=float(args.slope_weight),
        roughness_weight=float(args.roughness_weight),
    )
    risk_metadata = build_risk_layer(raw / "dem.tif", raw / "slope.tif", processed, config=risk_config)
    print(json.dumps(risk_metadata["statistics"], indent=2, sort_keys=True))
    print(f"Wrote risk layer: {processed / 'risk_grid.npz'}")
    print(f"Wrote manifest: {metadata_dir / 'download_manifest.json'}")


if __name__ == "__main__":
    main()

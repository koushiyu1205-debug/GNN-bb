"""Deterministic physical-risk model for Moon Trek raster patches."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

import numpy as np
import rasterio


@dataclass(frozen=True)
class RiskModelConfig:
    version: str = "slope_roughness_v1"
    impassable_slope_deg: float = 30.0
    high_risk_slope_deg: float = 20.0
    roughness_reference_m: float = 5.0
    slope_weight: float = 0.75
    roughness_weight: float = 0.25


def derive_slope_from_dem(
    dem_path: str | Path,
    slope_path: str | Path,
    *,
    width_km: float,
    height_km: float,
) -> dict[str, Any]:
    """Derive a deterministic slope raster from a DEM export.

    Moon Trek does not expose matched slope products for every lower-resolution
    continuous DEM. For those sites we compute slope once during preprocessing,
    write it as `raw/slope.tif`, and then treat it exactly like a downloaded
    fixed slope layer.
    """

    target = Path(slope_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(dem_path) as dem_src:
        dem = dem_src.read(1).astype("float32")
        profile = dem_src.profile.copy()
        dem_nodata = dem_src.nodata

    valid = np.isfinite(dem)
    valid &= dem > -1.0e20
    if dem_nodata is not None:
        valid &= dem != np.float32(dem_nodata)
    if not valid.any():
        raise ValueError(f"cannot derive slope from DEM with no valid cells: {dem_path}")

    fill_value = float(np.nanmedian(np.where(valid, dem, np.nan)))
    dem_for_gradient = np.where(valid, dem, fill_value).astype("float32")
    rows, cols = dem_for_gradient.shape
    dy_m = float(height_km) * 1000.0 / float(rows)
    dx_m = float(width_km) * 1000.0 / float(cols)
    grad_y, grad_x = np.gradient(dem_for_gradient, dy_m, dx_m)
    slope = np.degrees(np.arctan(np.sqrt(grad_x * grad_x + grad_y * grad_y))).astype("float32")
    slope[~valid] = np.nan

    slope_profile = profile.copy()
    slope_profile.update(dtype="float32", count=1, nodata=np.nan, compress="deflate")
    with rasterio.open(target, "w", **slope_profile) as dst:
        dst.write(slope, 1)

    return {
        "derived_from": str(dem_path),
        "path": str(target),
        "method": "central_gradient_slope_from_dem",
        "width_km": float(width_km),
        "height_km": float(height_km),
        "valid_cells": int(valid.sum()),
        "statistics": {
            "slope_deg": _array_stats(slope, valid),
        },
    }


def build_risk_layer(
    dem_path: str | Path,
    slope_path: str | Path,
    output_dir: str | Path,
    *,
    config: RiskModelConfig = RiskModelConfig(),
) -> dict[str, Any]:
    """Build a deterministic risk grid from co-registered DEM and slope rasters."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    with rasterio.open(dem_path) as dem_src, rasterio.open(slope_path) as slope_src:
        dem = dem_src.read(1).astype("float32")
        slope = slope_src.read(1).astype("float32")
        dem_profile = dem_src.profile.copy()
        slope_profile = slope_src.profile.copy()
        transform = dem_src.transform
        crs = dem_src.crs
        if dem.shape != slope.shape:
            raise ValueError(f"DEM and slope shapes differ: {dem.shape} != {slope.shape}")
        dem_nodata = dem_src.nodata
        slope_nodata = slope_src.nodata

    valid = np.isfinite(dem) & np.isfinite(slope)
    # ArcGIS ImageServer exports may carry float32 sentinel values without
    # populating the GeoTIFF nodata tag.
    valid &= dem > -1.0e20
    valid &= slope > -1.0e20
    if dem_nodata is not None:
        valid &= dem != np.float32(dem_nodata)
    if slope_nodata is not None:
        valid &= slope != np.float32(slope_nodata)
    valid &= slope >= 0.0

    roughness = local_std_3x3(dem, valid)
    slope_penalty = np.clip(slope / float(config.impassable_slope_deg), 0.0, 1.0) ** 2
    roughness_penalty = np.clip(roughness / float(config.roughness_reference_m), 0.0, 1.0)
    risk = config.slope_weight * slope_penalty + config.roughness_weight * roughness_penalty
    risk = np.clip(risk, 0.0, 1.0).astype("float32")
    impassable = (~valid) | (slope >= float(config.impassable_slope_deg))
    risk[~valid] = np.nan

    npz_path = output / "risk_grid.npz"
    np.savez_compressed(
        npz_path,
        dem=dem.astype("float32"),
        slope=slope.astype("float32"),
        roughness=roughness.astype("float32"),
        risk=risk,
        impassable=impassable.astype("uint8"),
        valid=valid.astype("uint8"),
    )

    risk_tif = output / "risk.tif"
    profile = dem_profile.copy()
    profile.update(dtype="float32", count=1, nodata=np.nan, compress="deflate")
    with rasterio.open(risk_tif, "w", **profile) as dst:
        dst.write(risk, 1)

    impassable_tif = output / "impassable.tif"
    mask_profile = dem_profile.copy()
    mask_profile.update(dtype="uint8", count=1, nodata=255, compress="deflate")
    with rasterio.open(impassable_tif, "w", **mask_profile) as dst:
        dst.write(impassable.astype("uint8"), 1)

    metadata = {
        "risk_model": asdict(config),
        "inputs": {
            "dem_path": str(dem_path),
            "slope_path": str(slope_path),
            "dem_profile": _json_safe_profile(dem_profile),
            "slope_profile": _json_safe_profile(slope_profile),
        },
        "grid": {
            "shape": list(dem.shape),
            "crs": str(crs),
            "transform": list(transform),
        },
        "outputs": {
            "risk_grid_npz": str(npz_path),
            "risk_tif": str(risk_tif),
            "impassable_tif": str(impassable_tif),
        },
        "statistics": {
            "valid_cells": int(valid.sum()),
            "impassable_cells": int(impassable.sum()),
            "impassable_fraction": float(impassable.mean()),
            "slope_deg": _array_stats(slope, valid),
            "roughness_m": _array_stats(roughness, valid),
            "risk": _array_stats(risk, valid),
        },
    }
    metadata_path = output / "risk_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return metadata


def local_std_3x3(values: np.ndarray, valid: np.ndarray) -> np.ndarray:
    filled = np.where(valid, values, 0.0).astype("float64")
    valid_float = valid.astype("float64")
    padded_values = np.pad(filled, 1, mode="edge")
    padded_valid = np.pad(valid_float, 1, mode="constant", constant_values=0.0)
    sum_values = np.zeros(values.shape, dtype="float64")
    sum_squares = np.zeros(values.shape, dtype="float64")
    counts = np.zeros(values.shape, dtype="float64")
    for row_offset in range(3):
        for col_offset in range(3):
            window = padded_values[row_offset : row_offset + values.shape[0], col_offset : col_offset + values.shape[1]]
            window_valid = padded_valid[row_offset : row_offset + values.shape[0], col_offset : col_offset + values.shape[1]]
            sum_values += window * window_valid
            sum_squares += window * window * window_valid
            counts += window_valid
    counts = np.maximum(counts, 1.0)
    mean = sum_values / counts
    variance = np.maximum(0.0, sum_squares / counts - mean * mean)
    roughness = np.sqrt(variance).astype("float32")
    roughness[~valid] = np.nan
    return roughness


def _array_stats(values: np.ndarray, valid: np.ndarray) -> dict[str, float | None]:
    sample = values[valid & np.isfinite(values)]
    if sample.size == 0:
        return {"min": None, "max": None, "mean": None, "p50": None, "p95": None}
    return {
        "min": float(np.min(sample)),
        "max": float(np.max(sample)),
        "mean": float(np.mean(sample)),
        "p50": float(np.percentile(sample, 50)),
        "p95": float(np.percentile(sample, 95)),
    }


def _json_safe_profile(profile: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in profile.items():
        if key in {"transform", "crs"}:
            safe[key] = str(value)
        elif isinstance(value, np.generic):
            safe[key] = value.item()
        else:
            safe[key] = value
    return safe

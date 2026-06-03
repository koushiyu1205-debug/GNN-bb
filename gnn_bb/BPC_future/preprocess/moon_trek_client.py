"""NASA Moon Trek raster download helpers.

This module keeps the physical data acquisition layer separate from the BPC
solver. It downloads fixed deterministic raster products and writes enough
metadata for later reproducibility audits.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any

import requests


MOON_RADIUS_M = 1_737_400.0
MOON_DEGREE_M = math.pi * MOON_RADIUS_M / 180.0


@dataclass(frozen=True)
class LayerSpec:
    name: str
    layer_id: str
    item_uuid: str
    endpoint: str
    service_type: str = "ArcGISImageService"
    spatial_reference: int = 104903


@dataclass(frozen=True)
class PatchSpec:
    name: str
    center_lon: float
    center_lat: float
    width_km: float
    height_km: float
    pixels: int
    spatial_reference: int = 104903

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        half_lat = (self.height_km * 1000.0) / (2.0 * MOON_DEGREE_M)
        lon_degree_m = MOON_DEGREE_M * math.cos(math.radians(self.center_lat))
        half_lon = (self.width_km * 1000.0) / (2.0 * lon_degree_m)
        return (
            self.center_lon - half_lon,
            self.center_lat - half_lat,
            self.center_lon + half_lon,
            self.center_lat + half_lat,
        )

    @property
    def approximate_pixel_size_m(self) -> float:
        return max(self.width_km, self.height_km) * 1000.0 / float(self.pixels)


APOLLO15_DEM_15M = LayerSpec(
    name="dem",
    layer_id="LRO_NAC_DEM_26N004E_150cmp",
    item_uuid="2a5e4224-e5d7-4c39-8700-cc9ab2e0869d",
    endpoint="https://trek.nasa.gov/moon/trekarcgis/rest/services/LRO_NAC_DEM_26N004E_150cmp/ImageServer",
)

APOLLO15_SLOPE_15M = LayerSpec(
    name="slope",
    layer_id="LRO_NAC_Slope_15m_26N004E_150cmp",
    item_uuid="c3b00a71-07a5-4bca-aba8-e8a6377bbef8",
    endpoint="https://trek.nasa.gov/moon/trekarcgis2/rest/services/LRO_NAC_Slope_15m_26N004E_150cmp/ImageServer",
)

DEFAULT_APOLLO15_PATCH = PatchSpec(
    name="apollo15_20km",
    center_lon=3.4384,
    center_lat=26.10935,
    width_km=20.0,
    height_km=20.0,
    pixels=2048,
)

BALMER_DEM_15M = LayerSpec(
    name="dem",
    layer_id="LRO_NAC_DEM_19S070E_150cmp",
    item_uuid="6e5e54ca-3831-4a29-83eb-4f3fd9b80116",
    endpoint="https://trek.nasa.gov/moon/trekarcgis/rest/services/LRO_NAC_DEM_19S070E_150cmp/ImageServer",
)

BALMER_SLOPE_15M = LayerSpec(
    name="slope",
    layer_id="LRO_NAC_Slope_15m_19S070E_150cmp",
    item_uuid="5d784675-f8d9-442a-8eaf-734d798aa749",
    endpoint="https://trek.nasa.gov/moon/trekarcgis2/rest/services/LRO_NAC_Slope_15m_19S070E_150cmp/ImageServer",
)

DEFAULT_BALMER_FLAT_PATCH = PatchSpec(
    name="balmer_flat_20km",
    center_lon=69.849846,
    center_lat=-18.610287,
    width_km=20.0,
    height_km=20.0,
    pixels=2048,
)

APOLLOZONE_DEM_1024PPD = LayerSpec(
    name="dem",
    layer_id="ApolloZone_MetricCam_DEM_Global_1024ppd",
    item_uuid="service:ApolloZone_MetricCam_DEM_Global_1024ppd",
    endpoint="https://trek.nasa.gov/moon/trekarcgis/rest/services/ApolloZone_MetricCam_DEM_Global_1024ppd/ImageServer",
)

DEFAULT_CRISIUM_SMOOTH_PATCH = PatchSpec(
    name="crisium_smooth_20km",
    center_lon=58.75,
    center_lat=17.25,
    width_km=20.0,
    height_km=20.0,
    pixels=1024,
)

DEFAULT_TRANQUILLITATIS_BALMER_LIKE_PATCH = PatchSpec(
    name="tranquillitatis_balmer_like_20km",
    center_lon=30.50,
    center_lat=7.65,
    width_km=20.0,
    height_km=20.0,
    pixels=1024,
)

SITE_PRESETS: dict[str, tuple[LayerSpec, LayerSpec | None, PatchSpec, str, bool]] = {
    "apollo15": (
        APOLLO15_DEM_15M,
        APOLLO15_SLOPE_15M,
        DEFAULT_APOLLO15_PATCH,
        "Apollo 15 rille-rich 20km patch",
        False,
    ),
    "balmer_flat": (
        BALMER_DEM_15M,
        BALMER_SLOPE_15M,
        DEFAULT_BALMER_FLAT_PATCH,
        "Balmer Basin flatter 20km patch selected by coarse slope scan",
        False,
    ),
    "crisium_smooth": (
        APOLLOZONE_DEM_1024PPD,
        None,
        DEFAULT_CRISIUM_SMOOTH_PATCH,
        "Mare Crisium smooth 20km patch; slope is deterministically derived from ApolloZone DEM",
        True,
    ),
    "tranquillitatis_balmer_like": (
        APOLLOZONE_DEM_1024PPD,
        None,
        DEFAULT_TRANQUILLITATIS_BALMER_LIKE_PATCH,
        "Mare Tranquillitatis 20km patch with Balmer-like slope statistics and continuous ApolloZone coverage",
        True,
    ),
}


def fetch_image_service_metadata(layer: LayerSpec, *, timeout: float = 60.0) -> dict[str, Any]:
    response = requests.get(f"{layer.endpoint}?f=pjson", timeout=timeout)
    response.raise_for_status()
    return response.json()


def download_export_image(
    layer: LayerSpec,
    patch: PatchSpec,
    target: str | Path,
    *,
    timeout: float = 180.0,
    force: bool = False,
) -> dict[str, Any]:
    target_path = Path(target)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    bbox = patch.bbox
    params = {
        "bbox": ",".join(f"{value:.12f}" for value in bbox),
        "bboxSR": str(patch.spatial_reference),
        "imageSR": str(patch.spatial_reference),
        "size": f"{patch.pixels},{patch.pixels}",
        "format": "tiff",
        "pixelType": "F32",
        "f": "image",
    }
    url = f"{layer.endpoint}/exportImage"
    if force or not target_path.exists():
        with requests.get(url, params=params, timeout=timeout, stream=True) as response:
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "tiff" not in content_type.lower() and "image" not in content_type.lower():
                raise RuntimeError(f"unexpected Moon Trek response for {layer.layer_id}: {content_type}")
            with target_path.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
    return {
        "layer": asdict(layer),
        "patch": asdict(patch),
        "bbox": bbox,
        "request_url": requests.Request("GET", url, params=params).prepare().url,
        "path": str(target_path),
        "sha256": sha256_file(target_path),
        "bytes": target_path.stat().st_size,
        "downloaded_at_unix": time.time(),
    }


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

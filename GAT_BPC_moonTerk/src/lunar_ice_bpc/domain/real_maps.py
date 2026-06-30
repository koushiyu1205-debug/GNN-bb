"""Real lunar south-pole raster source catalog and preview helpers."""

from __future__ import annotations

from dataclasses import dataclass
import heapq
import math
from pathlib import Path
from typing import Any

from lunar_ice_bpc.domain.scenario import LunarIceConfig


REAL_MAP_PREVIEW_SCHEMA_VERSION = "lunar_ice_bpc.real_map_preview.v1"
REAL_MAP_SOURCE_CATALOG_SCHEMA_VERSION = "lunar_ice_bpc.real_map_sources.v1"
REAL_MAP_GENERATOR_ID = "real_lunar_south_pole_raster_preview_v1"
REAL_MAP_REQUIRED_LOLA_LAYERS = ("lola_slope", "lola_roughness", "lola_psr")
PATH_TYPES = ("low_time", "low_energy", "low_risk")
DEFAULT_SP50_DEPOT_CENTER_KM = (-9.9, -19.1)
WONG_BLUE = "#2271B2"
WONG_CYAN = "#3DB7E9"
WONG_MAGENTA = "#F748A5"
WONG_GREEN = "#359B73"
WONG_ORANGE = "#D55E00"
WONG_GOLD = "#E69F00"
WONG_YELLOW = "#F0E442"


@dataclass(frozen=True)
class RealMapLayerSource:
    key: str
    title: str
    local_filename: str
    role: str
    source_url: str
    source_page: str
    native_resolution_m: float | None
    required_for_lola_preview: bool
    notes: str

    def to_payload(self, raw_map_dir: Path) -> dict[str, Any]:
        local_path = raw_map_dir / self.local_filename
        return {
            "key": self.key,
            "title": self.title,
            "role": self.role,
            "local_filename": self.local_filename,
            "local_path": str(local_path),
            "local_exists": local_path.exists(),
            "source_url": self.source_url,
            "source_page": self.source_page,
            "native_resolution_m": self.native_resolution_m,
            "required_for_lola_preview": self.required_for_lola_preview,
            "notes": self.notes,
        }


REAL_MAP_SOURCE_CATALOG: tuple[RealMapLayerSource, ...] = (
    RealMapLayerSource(
        key="lola_dem",
        title="LOLA south-pole digital elevation model",
        local_filename="LOLA_80S_dem_80m.tif",
        role="directional_elevation_optional",
        source_url="https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_80MPP_ADJ.TIF",
        source_page="https://pgda.gsfc.nasa.gov/products/90",
        native_resolution_m=80.0,
        required_for_lola_preview=False,
        notes="Optional elevation layer. When present, directed path search distinguishes uphill and downhill traversal.",
    ),
    RealMapLayerSource(
        key="lola_hillshade",
        title="LOLA south-pole adjusted hillshade",
        local_filename="LOLA_80S_hillshade.tif",
        role="context_background",
        source_url="https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_80MPP_ADJ_HILL.TIF",
        source_page="https://pgda.gsfc.nasa.gov/products/90",
        native_resolution_m=80.0,
        required_for_lola_preview=False,
        notes="Visual terrain context only; not used as a physical objective layer.",
    ),
    RealMapLayerSource(
        key="lola_slope",
        title="LOLA south-pole slope",
        local_filename="LOLA_80S_slope_100m.tif",
        role="terrain_risk",
        source_url="https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDRM_80S_1000MPP_ADJ_SLP_100M.TIF",
        source_page="https://pgda.gsfc.nasa.gov/products/90",
        native_resolution_m=1000.0,
        required_for_lola_preview=True,
        notes="Required for first real-map terrain risk preview; PGDA GeoTIFF reports 1000 m pixels.",
    ),
    RealMapLayerSource(
        key="lola_roughness",
        title="LOLA south-pole roughness",
        local_filename="LOLA_80S_roughness_100m.tif",
        role="terrain_risk",
        source_url="https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDRM_80S_1000MPP_ADJ_ROUGH_100M.TIF",
        source_page="https://pgda.gsfc.nasa.gov/products/90",
        native_resolution_m=1000.0,
        required_for_lola_preview=True,
        notes="Required for first real-map terrain risk preview; PGDA GeoTIFF reports 1000 m pixels.",
    ),
    RealMapLayerSource(
        key="lola_psr",
        title="LOLA south-pole permanently shadowed regions",
        local_filename="LOLA_80S_psr_20m.tif",
        role="shadow_and_psr",
        source_url="https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LPSR_80S_20MPP_ADJ.TIF",
        source_page="https://pgda.gsfc.nasa.gov/products/90",
        native_resolution_m=20.0,
        required_for_lola_preview=True,
        notes="Required for PSR exposure and water-ice resource proxy preview.",
    ),
    RealMapLayerSource(
        key="lola_avg_solar_visibility",
        title="LOLA south-pole average solar visibility",
        local_filename="AVGVISIB_85S_060M_201608.tif",
        role="illumination_optional",
        source_url="https://pgda.gsfc.nasa.gov/data/MoonIllumination/AVGVISIB_85S_060M_201608.TIF",
        source_page="https://pgda.gsfc.nasa.gov/products/69",
        native_resolution_m=60.0,
        required_for_lola_preview=False,
        notes="Optional but preferred illumination layer for peak-of-eternal-light depot scoring.",
    ),
    RealMapLayerSource(
        key="diviner_temperature",
        title="Diviner polar temperature layer",
        local_filename="DIVINER_south_pole_temperature.tif",
        role="thermal_risk_optional",
        source_url="https://pds-geosciences.wustl.edu/missions/lro/diviner.htm",
        source_page="https://pds-geosciences.wustl.edu/missions/lro/diviner.htm",
        native_resolution_m=500.0,
        required_for_lola_preview=False,
        notes="Optional thermal layer. Record native resolution; do not treat as 100 m measurement.",
    ),
    RealMapLayerSource(
        key="m3_water",
        title="M3 OH/H2O surface water proxy",
        local_filename="M3_water_proxy_south_pole.tif",
        role="surface_water_proxy_optional",
        source_url="https://astrogeology.usgs.gov/search/map/lunar_m3_water_map_pds4_archive",
        source_page="https://astrogeology.usgs.gov/search/map/lunar_m3_water_map_pds4_archive",
        native_resolution_m=None,
        required_for_lola_preview=False,
        notes="Optional science-weight proxy; OH and H2O absorption overlap must be documented.",
    ),
    RealMapLayerSource(
        key="lend_hydrogen",
        title="LEND hydrogen/neutron proxy",
        local_filename="LEND_hydrogen_proxy_south_pole.tif",
        role="subsurface_hydrogen_proxy_optional",
        source_url="https://arcnav.psi.edu/urn%3Anasa%3Apds%3Acontext%3Ainstrument%3Alend.lro",
        source_page="https://arcnav.psi.edu/urn%3Anasa%3Apds%3Acontext%3Ainstrument%3Alend.lro",
        native_resolution_m=5000.0,
        required_for_lola_preview=False,
        notes="Optional coarse background proxy; keep native resolution explicit.",
    ),
)


def real_map_source_catalog(raw_map_dir: str | Path) -> dict[str, Any]:
    raw_dir = Path(raw_map_dir)
    layers = [source.to_payload(raw_dir) for source in REAL_MAP_SOURCE_CATALOG]
    return {
        "schema_version": REAL_MAP_SOURCE_CATALOG_SCHEMA_VERSION,
        "catalog_id": "lunar_south_pole_real_map_sources_v1",
        "raw_map_dir": str(raw_dir),
        "required_lola_layers": list(REAL_MAP_REQUIRED_LOLA_LAYERS),
        "layers": layers,
        "local_ready": all(item["local_exists"] for item in layers if item["required_for_lola_preview"]),
    }


def build_real_map_surface_context(
    *,
    raw_map_dir: str | Path,
    center_x_km: float = 0.0,
    center_y_km: float = 0.0,
    extent_km: float = 30.0,
    output_cells: int = 300,
    allow_remote: bool = False,
    allow_partial: bool = False,
) -> dict[str, Any]:
    """Read real raster layers and return normalized arrays for path building."""

    raw_dir = Path(raw_map_dir)
    catalog = real_map_source_catalog(raw_dir)
    missing_required = [
        item["key"] for item in catalog["layers"] if item["required_for_lola_preview"] and not item["local_exists"]
    ]
    if missing_required and not allow_remote and not allow_partial:
        return {
            "status": "MISSING_REQUIRED_REAL_MAP_LAYERS",
            "source_catalog": catalog,
            "layer_status": {},
            "ready_required_lola_layers": [],
            "missing_required_lola_layers": missing_required,
            "roi": _roi_payload(center_x_km, center_y_km, extent_km, output_cells),
        }
    try:
        import numpy as np
        import rasterio
    except Exception as exc:  # pragma: no cover - exercised only when optional deps are absent.
        return {
            "status": "RASTER_DEPENDENCY_MISSING",
            "source_catalog": catalog,
            "layer_status": {},
            "ready_required_lola_layers": [],
            "missing_required_lola_layers": list(REAL_MAP_REQUIRED_LOLA_LAYERS),
            "roi": _roi_payload(center_x_km, center_y_km, extent_km, output_cells),
            "error": f"{type(exc).__name__}: {exc}",
        }

    layer_arrays: dict[str, Any] = {}
    layer_status: dict[str, dict[str, Any]] = {}
    for item in catalog["layers"]:
        if not item["local_exists"] and not allow_remote:
            layer_status[item["key"]] = {"status": "missing_local_file", "path": item["local_path"]}
            continue
        source_path = item["local_path"] if item["local_exists"] else item["source_url"]
        try:
            array, meta = _read_raster_window(
                rasterio=rasterio,
                np=np,
                source_path=source_path,
                layer_key=item["key"],
                center_x_km=center_x_km,
                center_y_km=center_y_km,
                extent_km=extent_km,
                output_cells=output_cells,
            )
        except Exception as exc:
            layer_status[item["key"]] = {
                "status": "read_failed",
                "source": source_path,
                "error": f"{type(exc).__name__}: {exc}",
            }
            continue
        layer_arrays[item["key"]] = array
        layer_status[item["key"]] = {
            "status": "ready",
            "source": source_path,
            "meta": meta,
            "stats": _array_stats(np, array),
        }
    ready_required = [key for key in REAL_MAP_REQUIRED_LOLA_LAYERS if key in layer_arrays]
    missing_after_read = [key for key in REAL_MAP_REQUIRED_LOLA_LAYERS if key not in layer_arrays]
    if missing_after_read and not allow_partial:
        return {
            "status": "MISSING_REQUIRED_REAL_MAP_LAYERS",
            "source_catalog": catalog,
            "layer_status": layer_status,
            "ready_required_lola_layers": ready_required,
            "missing_required_lola_layers": missing_after_read,
            "roi": _roi_payload(center_x_km, center_y_km, extent_km, output_cells),
        }
    if not layer_arrays:
        return {
            "status": "NO_READABLE_REAL_MAP_LAYERS",
            "source_catalog": catalog,
            "layer_status": layer_status,
            "ready_required_lola_layers": ready_required,
            "missing_required_lola_layers": missing_after_read,
            "roi": _roi_payload(center_x_km, center_y_km, extent_km, output_cells),
        }
    normalized = {key: _normalize(np, array) for key, array in layer_arrays.items()}
    resource, risk, surfaces = _build_resource_and_risk_surfaces(np, normalized, output_cells, raw_layers=layer_arrays)
    return {
        "status": "REAL_MAP_SURFACES_READY" if not missing_after_read else "PARTIAL_REAL_MAP_SURFACES_READY",
        "source_catalog": catalog,
        "layer_status": layer_status,
        "ready_required_lola_layers": ready_required,
        "missing_required_lola_layers": missing_after_read,
        "roi": _roi_payload(center_x_km, center_y_km, extent_km, output_cells),
        "resource": resource,
        "risk": risk,
        "surfaces": surfaces,
    }


def select_south_pole_depot_center(
    *,
    raw_map_dir: str | Path,
    search_center_x_km: float = 0.0,
    search_center_y_km: float = 0.0,
    search_extent_km: float = 80.0,
    output_cells: int = 800,
    central_search_radius_km: float = 25.0,
    benchmark_extent_km: float = 50.0,
    roi_edge_guard_km: float = 4.0,
) -> dict[str, Any]:
    """Select a defensible peak-of-eternal-light proxy near the lunar south pole."""

    np = __import__("numpy")
    context = build_real_map_surface_context(
        raw_map_dir=raw_map_dir,
        center_x_km=search_center_x_km,
        center_y_km=search_center_y_km,
        extent_km=search_extent_km,
        output_cells=output_cells,
    )
    if context["status"] != "REAL_MAP_SURFACES_READY":
        return {
            "status": "DEPOT_SELECTION_FAILED",
            "reason": context["status"],
            "center_x_km": float(search_center_x_km),
            "center_y_km": float(search_center_y_km),
            "source_context": {key: context.get(key) for key in ("status", "missing_required_lola_layers", "ready_required_lola_layers")},
        }
    surfaces = context["surfaces"]
    local = _select_depot_candidate(
        np,
        surfaces,
        extent_km=search_extent_km,
        search_radius_km=central_search_radius_km,
        boundary_margin_km=2.0,
        benchmark_extent_km=benchmark_extent_km,
        roi_edge_guard_km=roi_edge_guard_km,
    )
    bounds = context["roi"]["bounds_km"]
    local_x, local_y = float(local["xy_km"][0]), float(local["xy_km"][1])
    global_x = float(bounds[0]) + local_x
    global_y = float(bounds[1]) + local_y
    local.update(
        {
            "status": "DEPOT_SELECTED",
            "global_xy_km": [round(global_x, 6), round(global_y, 6)],
            "search_center_xy_km": [float(search_center_x_km), float(search_center_y_km)],
            "search_extent_km": float(search_extent_km),
            "central_search_radius_km": float(central_search_radius_km),
            "benchmark_extent_km": float(benchmark_extent_km),
            "roi_edge_guard_km": float(roi_edge_guard_km),
            "literature_region_comparison": _named_region_comparison(global_x, global_y),
        }
    )
    return local


def build_real_map_edge_options(
    *,
    raw_map_dir: str | Path,
    nodes: dict[str, tuple[float, float]],
    center_x_km: float = 0.0,
    center_y_km: float = 0.0,
    extent_km: float = 30.0,
    output_cells: int = 300,
    allow_remote: bool = False,
) -> list[dict[str, Any]]:
    """Build fixed three-path logical edges from real raster cost surfaces."""

    context = build_real_map_surface_context(
        raw_map_dir=raw_map_dir,
        center_x_km=center_x_km,
        center_y_km=center_y_km,
        extent_km=extent_km,
        output_cells=output_cells,
        allow_remote=allow_remote,
    )
    if context["status"] != "REAL_MAP_SURFACES_READY":
        raise ValueError(f"real map surfaces are not ready: {context['status']}")
    surfaces = context["surfaces"]
    cells = int(surfaces["resource"].shape[0])
    cost_surfaces = _preview_cost_surfaces(surfaces)
    np = __import__("numpy")
    edges: list[dict[str, Any]] = []
    node_cells = {
        node_id: _xy_to_cell([xy[0], xy[1]], cells, extent_km)
        for node_id, xy in nodes.items()
    }
    for source_id, start in node_cells.items():
        low_time_paths = _dijkstra_grid_paths_to_goals(
            cost_surfaces["low_time"],
            start,
            [goal for target_id, goal in node_cells.items() if target_id != source_id],
            elevation=surfaces.get("elevation_m"),
            elevation_available=bool(surfaces.get("elevation_available", False)),
            path_type="low_time",
            extent_km=extent_km,
        )
        for target_id, goal in node_cells.items():
            if source_id == target_id:
                continue
            options = _build_directed_path_options(
                np=np,
                cost_surfaces=cost_surfaces,
                surfaces=surfaces,
                start=start,
                goal=goal,
                extent_km=extent_km,
                first_path_override=low_time_paths.get(goal),
            )
            edges.append({"from": source_id, "to": target_id, "path_options": options})
    return edges


def build_real_map_preview(
    *,
    raw_map_dir: str | Path,
    center_x_km: float = 0.0,
    center_y_km: float = 0.0,
    extent_km: float = 30.0,
    output_cells: int = 300,
    target_count: int = 12,
    path_target_count: int = 3,
    active_footprint_km: float | None = None,
    allow_remote: bool = False,
    allow_partial: bool = False,
) -> dict[str, Any]:
    """Build a fail-closed real-map preview payload.

    The default mode reads only local GeoTIFF files. Remote URLs are retained as
    provenance and are used only when allow_remote=True.
    """

    raw_dir = Path(raw_map_dir)
    catalog = real_map_source_catalog(raw_dir)
    missing_required = [
        item["key"] for item in catalog["layers"] if item["required_for_lola_preview"] and not item["local_exists"]
    ]
    if missing_required and not allow_remote and not allow_partial:
        return _missing_preview_payload(
            catalog=catalog,
            center_x_km=center_x_km,
            center_y_km=center_y_km,
            extent_km=extent_km,
            output_cells=output_cells,
            missing_required=missing_required,
            note="Required local LOLA layers are missing. No synthetic fallback was used.",
            active_footprint_km=active_footprint_km,
        )

    try:
        import numpy as np
        import rasterio
    except Exception as exc:  # pragma: no cover - exercised only when optional deps are absent.
        return _missing_preview_payload(
            catalog=catalog,
            center_x_km=center_x_km,
            center_y_km=center_y_km,
            extent_km=extent_km,
            output_cells=output_cells,
            missing_required=list(REAL_MAP_REQUIRED_LOLA_LAYERS),
            note=f"Optional raster dependencies are unavailable: {type(exc).__name__}: {exc}",
            active_footprint_km=active_footprint_km,
        )

    layer_arrays: dict[str, Any] = {}
    layer_status: dict[str, dict[str, Any]] = {}
    for item in catalog["layers"]:
        if not item["local_exists"] and not allow_remote:
            layer_status[item["key"]] = {"status": "missing_local_file", "path": item["local_path"]}
            continue
        source_path = item["local_path"] if item["local_exists"] else item["source_url"]
        try:
            array, meta = _read_raster_window(
                rasterio=rasterio,
                np=np,
                source_path=source_path,
                layer_key=item["key"],
                center_x_km=center_x_km,
                center_y_km=center_y_km,
                extent_km=extent_km,
                output_cells=output_cells,
            )
        except Exception as exc:
            layer_status[item["key"]] = {
                "status": "read_failed",
                "source": source_path,
                "error": f"{type(exc).__name__}: {exc}",
            }
            continue
        layer_arrays[item["key"]] = array
        layer_status[item["key"]] = {
            "status": "ready",
            "source": source_path,
            "meta": meta,
            "stats": _array_stats(np, array),
        }

    ready_required = [key for key in REAL_MAP_REQUIRED_LOLA_LAYERS if key in layer_arrays]
    missing_after_read = [key for key in REAL_MAP_REQUIRED_LOLA_LAYERS if key not in layer_arrays]
    if missing_after_read and not allow_partial:
        return _missing_preview_payload(
            catalog=catalog,
            center_x_km=center_x_km,
            center_y_km=center_y_km,
            extent_km=extent_km,
            output_cells=output_cells,
            missing_required=missing_after_read,
            note="At least one required LOLA layer could not be read. No synthetic fallback was used.",
            layer_status=layer_status,
            active_footprint_km=active_footprint_km,
        )
    if not layer_arrays:
        return _missing_preview_payload(
            catalog=catalog,
            center_x_km=center_x_km,
            center_y_km=center_y_km,
            extent_km=extent_km,
            output_cells=output_cells,
            missing_required=missing_after_read,
            note="No readable real raster layers were found. No synthetic fallback was used.",
            layer_status=layer_status,
            active_footprint_km=active_footprint_km,
        )

    normalized = {key: _normalize(np, array) for key, array in layer_arrays.items()}
    resource, risk, surfaces = _build_resource_and_risk_surfaces(np, normalized, output_cells, raw_layers=layer_arrays)
    depot = _center_depot_payload(surfaces, extent_km=extent_km)
    targets = _select_candidate_targets(
        np,
        resource,
        risk,
        surfaces,
        extent_km=extent_km,
        count=target_count,
        active_footprint_km=active_footprint_km,
        depot_xy=depot["xy_km"],
        sector_count=8,
        boundary_margin_km=4.0,
    )
    path_options = _build_preview_path_options(
        np=np,
        surfaces=surfaces,
        targets=targets[: max(0, path_target_count)],
        depot_xy=depot["xy_km"],
        extent_km=extent_km,
    )
    return {
        "schema_version": REAL_MAP_PREVIEW_SCHEMA_VERSION,
        "generator": REAL_MAP_GENERATOR_ID,
        "status": "REAL_MAP_PREVIEW_READY" if not missing_after_read else "PARTIAL_REAL_MAP_PREVIEW_READY",
        "uses_synthetic_fallback": False,
        "source_catalog": catalog,
        "layer_status": layer_status,
        "ready_required_lola_layers": ready_required,
        "missing_required_lola_layers": missing_after_read,
        "roi": _roi_payload(center_x_km, center_y_km, extent_km, output_cells),
        "candidate_selection": {
            "target_count": int(target_count),
            "path_target_count": int(path_target_count),
            "active_footprint_km": active_footprint_km,
            "spatial_policy": "water_ice_hotspot_directional_v1",
            "sector_count": 8,
            "boundary_margin_km": 4.0,
        },
        "depot": depot,
        "targets": targets,
        "path_options": path_options,
        "preview_layers": {
            "resource_index": _round_matrix(resource),
            "risk_index": _round_matrix(risk),
            "illumination_index": _round_matrix(surfaces["illumination"]),
            "psr_boundary_index": _round_matrix(surfaces["psr_boundary"]),
            "psr_interior_index": _round_matrix(surfaces["psr_interior"]),
            "elevation_index": _round_matrix(normalized["lola_dem"]) if "lola_dem" in normalized else [],
            "elevation_m": _round_matrix(surfaces["elevation_m"]) if bool(surfaces.get("elevation_available", False)) else [],
        },
        "notes": [
            "Preview uses local projected south-pole km coordinates inside the selected ROI.",
            "This artifact is a map/data readiness preview, not a CVRPTW instance and not an exact certificate.",
        ],
    }


def write_real_map_preview_svg(preview: dict[str, Any], output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    size = 920
    pad = 58
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">',
        '<rect width="100%" height="100%" fill="#fffdf6"/>',
    ]
    status = preview.get("status", "UNKNOWN")
    extent = float((preview.get("roi") or {}).get("extent_km", 30.0))
    resource = (preview.get("preview_layers") or {}).get("resource_index") or []
    risk = (preview.get("preview_layers") or {}).get("risk_index") or []
    if resource:
        resource_render = _downsample_grid(resource, max_cells=360)
        risk_render = _downsample_grid(risk, max_cells=360) if risk else []
        cell_count = len(resource_render)
        cell_size = (size - 2 * pad) / float(cell_count)
        for row, values in enumerate(resource_render):
            for col, value in enumerate(values):
                v = max(0.0, min(1.0, float(value)))
                r = max(0.0, min(1.0, float(risk_render[row][col] if risk_render else 0.0)))
                color = _resource_risk_color(v, r)
                x = pad + col * cell_size
                y = pad + row * cell_size
                parts.append(
                    f'<rect x="{x:.2f}" y="{y:.2f}" width="{cell_size + 0.2:.2f}" '
                    f'height="{cell_size + 0.2:.2f}" fill="{color}"/>'
                )
    else:
        parts.append(f'<rect x="{pad}" y="{pad}" width="{size - 2 * pad}" height="{size - 2 * pad}" fill="#f0f0eb"/>')
        missing = ", ".join(preview.get("missing_required_lola_layers") or [])
        note = _xml_escape(preview.get("note") or "Real raster layers are not ready.")
        parts.append(f'<text x="{pad + 24}" y="{pad + 80}" fill="#111827" font-size="22">real-map preview not ready</text>')
        parts.append(f'<text x="{pad + 24}" y="{pad + 118}" fill="#374151" font-size="15">{_xml_escape(status)}</text>')
        parts.append(f'<text x="{pad + 24}" y="{pad + 150}" fill="{WONG_ORANGE}" font-size="14">missing: {_xml_escape(missing)}</text>')
        parts.append(f'<text x="{pad + 24}" y="{pad + 182}" fill="#374151" font-size="13">{note}</text>')
    parts.append(f'<rect x="{pad}" y="{pad}" width="{size - 2 * pad}" height="{size - 2 * pad}" fill="none" stroke="#202020" stroke-width="1.2"/>')
    for option in preview.get("path_options", []):
        color = _path_color(str(option.get("path_type")))
        points = _polyline_svg(option.get("path_xy", []), extent, size, pad)
        if points:
            parts.append(f'<polyline points="{points}" fill="none" stroke="#202020" stroke-width="2.5" opacity="0.28"/>')
            parts.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.0" opacity="0.92"/>')
    depot = preview.get("depot") or {}
    if depot.get("xy_km"):
        x, y = _scale_xy(depot["xy_km"][0], depot["xy_km"][1], extent, size, pad)
        parts.append(_star_svg(x, y, outer=11.0, inner=4.3, fill=WONG_YELLOW, stroke="#202020", stroke_width=1.4))
        parts.append(f'<text x="{x + 10:.2f}" y="{y - 10:.2f}" fill="#111827" stroke="#fbfbf8" stroke-width="3" paint-order="stroke" font-size="14">depot</text>')
    for target in preview.get("targets", []):
        x, y = _scale_xy(target["xy_km"][0], target["xy_km"][1], extent, size, pad)
        color = _candidate_marker_color(target)
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4.8" fill="{color}" stroke="#202020" stroke-width="0.9" opacity="0.96"/>')
    _add_resource_risk_legend(parts, x=size - pad - 234, y=pad + 14)
    _add_svg_scale_bar(parts, size=size, pad=pad, extent=extent)
    title = f"real lunar south-pole map preview | {status}"
    parts.append(f'<text x="{pad}" y="32" fill="#111827" font-size="18" font-family="monospace">{_xml_escape(title)}</text>')
    parts.append('<text x="58" y="890" fill="#5a4326" font-size="13">background: warm remote-sensing resource/risk composite; blue/green/amber: low_time/low_energy/low_risk raster paths</text>')
    parts.append("</svg>")
    output.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return output


def write_real_map_dem_svg(preview: dict[str, Any], output_path: str | Path) -> Path:
    """Write a terrain-elevation SVG for the same real-map preview ROI."""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    size = 920
    pad = 58
    status = preview.get("status", "UNKNOWN")
    extent = float((preview.get("roi") or {}).get("extent_km", 50.0))
    elevation = (preview.get("preview_layers") or {}).get("elevation_index") or []
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">',
        '<rect width="100%" height="100%" fill="#fffdf6"/>',
    ]
    if elevation:
        render = _downsample_grid(elevation, max_cells=360)
        cell_count = len(render)
        cell_size = (size - 2 * pad) / float(cell_count)
        for row, values in enumerate(render):
            for col, value in enumerate(values):
                v = max(0.0, min(1.0, float(value)))
                color = _dem_color(v)
                x = pad + col * cell_size
                y = pad + row * cell_size
                parts.append(
                    f'<rect x="{x:.2f}" y="{y:.2f}" width="{cell_size + 0.2:.2f}" '
                    f'height="{cell_size + 0.2:.2f}" fill="{color}"/>'
                )
    else:
        parts.append(f'<rect x="{pad}" y="{pad}" width="{size - 2 * pad}" height="{size - 2 * pad}" fill="#f0f0eb"/>')
        parts.append(f'<text x="{pad + 24}" y="{pad + 84}" fill="#111827" font-size="22">DEM layer not ready</text>')
        parts.append(f'<text x="{pad + 24}" y="{pad + 122}" fill="#374151" font-size="15">{_xml_escape(status)}</text>')
    parts.append(f'<rect x="{pad}" y="{pad}" width="{size - 2 * pad}" height="{size - 2 * pad}" fill="none" stroke="#202020" stroke-width="1.2"/>')
    depot = preview.get("depot") or {}
    if depot.get("xy_km"):
        x, y = _scale_xy(depot["xy_km"][0], depot["xy_km"][1], extent, size, pad)
        parts.append(_star_svg(x, y, outer=11.0, inner=4.3, fill=WONG_YELLOW, stroke="#202020", stroke_width=1.4))
        parts.append(f'<text x="{x + 12:.2f}" y="{y - 12:.2f}" fill="#111827" stroke="#fbfbf8" stroke-width="3" paint-order="stroke" font-size="14">depot</text>')
    for target in preview.get("targets", []):
        x, y = _scale_xy(target["xy_km"][0], target["xy_km"][1], extent, size, pad)
        color = _candidate_marker_color(target)
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4.4" fill="{color}" stroke="#202020" stroke-width="0.9" opacity="0.96"/>')
    _add_dem_legend(parts, x=size - pad - 218, y=pad + 14)
    _add_svg_scale_bar(parts, size=size, pad=pad, extent=extent)
    parts.append(f'<text x="{pad}" y="32" fill="#111827" font-size="18" font-family="monospace">LOLA DEM centered on selected depot | {extent:.0f} km x {extent:.0f} km</text>')
    parts.append('<text x="58" y="890" fill="#374151" font-size="13">background: normalized elevation; star: selected peak-of-eternal-light depot; points: sampled high-value target candidates</text>')
    parts.append("</svg>")
    output.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return output


def _missing_preview_payload(
    *,
    catalog: dict[str, Any],
    center_x_km: float,
    center_y_km: float,
    extent_km: float,
    output_cells: int,
    missing_required: list[str],
    note: str,
    layer_status: dict[str, Any] | None = None,
    active_footprint_km: float | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": REAL_MAP_PREVIEW_SCHEMA_VERSION,
        "generator": REAL_MAP_GENERATOR_ID,
        "status": "MISSING_REQUIRED_REAL_MAP_LAYERS",
        "uses_synthetic_fallback": False,
        "source_catalog": catalog,
        "layer_status": layer_status or {},
        "ready_required_lola_layers": [],
        "missing_required_lola_layers": list(missing_required),
        "roi": _roi_payload(center_x_km, center_y_km, extent_km, output_cells),
        "candidate_selection": {
            "target_count": 0,
            "path_target_count": 0,
            "active_footprint_km": active_footprint_km,
        },
        "depot": {"id": "depot", "kind": "peak_of_eternal_light_candidate", "xy_km": [extent_km / 2.0, extent_km / 2.0]},
        "targets": [],
        "path_options": [],
        "preview_layers": {},
        "note": note,
    }


def _roi_payload(center_x_km: float, center_y_km: float, extent_km: float, output_cells: int) -> dict[str, Any]:
    half = float(extent_km) / 2.0
    return {
        "crs_hint": "lunar south-pole projected x/y kilometers; matches source GeoTIFF CRS units after km-to-m conversion",
        "center_x_km": float(center_x_km),
        "center_y_km": float(center_y_km),
        "extent_km": float(extent_km),
        "bounds_km": [float(center_x_km) - half, float(center_y_km) - half, float(center_x_km) + half, float(center_y_km) + half],
        "output_cells": int(output_cells),
        "output_resolution_m": float(extent_km) * 1000.0 / float(output_cells),
    }


def _read_raster_window(
    *,
    rasterio: Any,
    np: Any,
    source_path: str,
    layer_key: str,
    center_x_km: float,
    center_y_km: float,
    extent_km: float,
    output_cells: int,
) -> tuple[Any, dict[str, Any]]:
    from rasterio.windows import from_bounds
    from rasterio.enums import Resampling

    half_m = float(extent_km) * 500.0
    center_x_m = float(center_x_km) * 1000.0
    center_y_m = float(center_y_km) * 1000.0
    left, right = center_x_m - half_m, center_x_m + half_m
    bottom, top = center_y_m - half_m, center_y_m + half_m
    env_kwargs = {"GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR"} if str(source_path).startswith("http") else {}
    with rasterio.Env(**env_kwargs):
        with rasterio.open(source_path) as dataset:
            window = from_bounds(left, bottom, right, top, transform=dataset.transform)
            dtype_name = str(dataset.dtypes[0]).lower()
            integer_dtype = any(token in dtype_name for token in ("int", "uint"))
            fill_value = dataset.nodata if dataset.nodata is not None else (0 if integer_dtype else np.nan)
            data = dataset.read(
                1,
                window=window,
                out_shape=(int(output_cells), int(output_cells)),
                boundless=True,
                fill_value=fill_value,
                masked=True,
                resampling=Resampling.nearest if str(layer_key) == "lola_psr" else Resampling.bilinear,
            )
            mask = np.ma.getmaskarray(data)
            array = np.asarray(data.filled(fill_value), dtype=float)
            if mask is not None:
                array[mask] = np.nan
            if dataset.nodata is not None:
                array[np.isclose(array, float(dataset.nodata), equal_nan=False)] = np.nan
            meta = {
                "driver": dataset.driver,
                "width": dataset.width,
                "height": dataset.height,
                "crs": str(dataset.crs),
                "bounds": [float(dataset.bounds.left), float(dataset.bounds.bottom), float(dataset.bounds.right), float(dataset.bounds.top)],
                "nodata": dataset.nodata,
                "dtype": dataset.dtypes[0],
                "pixel_size_m": [float(dataset.res[0]), float(abs(dataset.res[1]))],
                "resampling": "nearest" if str(layer_key) == "lola_psr" else "bilinear",
            }
    return array, meta


def _array_stats(np: Any, array: Any) -> dict[str, Any]:
    finite = array[np.isfinite(array)]
    if finite.size == 0:
        return {"valid_count": 0}
    return {
        "valid_count": int(finite.size),
        "min": float(np.min(finite)),
        "max": float(np.max(finite)),
        "mean": float(np.mean(finite)),
        "p02": float(np.percentile(finite, 2)),
        "p98": float(np.percentile(finite, 98)),
    }


def _normalize(np: Any, array: Any) -> Any:
    finite = array[np.isfinite(array)]
    if finite.size == 0:
        return np.zeros_like(array, dtype=float)
    low = float(np.percentile(finite, 2))
    high = float(np.percentile(finite, 98))
    if high <= low + 1.0e-12:
        return np.zeros_like(array, dtype=float)
    values = (array - low) / (high - low)
    values = np.where(np.isfinite(values), values, 0.0)
    return np.clip(values, 0.0, 1.0)


def _build_resource_and_risk_surfaces(
    np: Any,
    layers: dict[str, Any],
    cells: int,
    *,
    raw_layers: dict[str, Any] | None = None,
) -> tuple[Any, Any, dict[str, Any]]:
    shape = (int(cells), int(cells))

    def layer(key: str) -> Any:
        return layers[key] if key in layers else np.zeros(shape, dtype=float)

    hillshade = layer("lola_hillshade")
    slope = layer("lola_slope")
    roughness = layer("lola_roughness")
    shadow = layer("lola_psr")
    illumination = layer("lola_avg_solar_visibility") if "lola_avg_solar_visibility" in layers else np.clip(1.0 - shadow, 0.0, 1.0)
    diviner = layer("diviner_temperature")
    m3_water = layer("m3_water")
    lend = layer("lend_hydrogen")
    thermal_cold = 1.0 - diviner if "diviner_temperature" in layers else shadow
    low_illumination = np.clip(1.0 - illumination, 0.0, 1.0)
    water_proxy = 0.40 * shadow + 0.25 * thermal_cold + 0.15 * low_illumination + 0.12 * m3_water + 0.08 * lend
    psr_boundary = _boundary_score(np, shadow)
    psr_interior = np.clip(shadow * (1.0 - psr_boundary), 0.0, 1.0)
    steep_slope = np.power(np.clip(slope, 0.0, 1.0), 1.75)
    rough_block = np.power(np.clip(roughness, 0.0, 1.0), 1.45)
    crater_edge_risk = np.clip(0.62 * psr_boundary + 0.24 * steep_slope + 0.14 * rough_block, 0.0, 1.0)
    terrain_risk = np.clip(0.45 * slope + 0.25 * roughness + 0.30 * steep_slope, 0.0, 1.0)
    risk = np.clip(
        0.32 * terrain_risk
        + 0.28 * shadow
        + 0.18 * psr_boundary
        + 0.12 * psr_interior
        + 0.10 * (1.0 - hillshade),
        0.0,
        1.0,
    )
    resource = np.clip(0.70 * water_proxy + 0.20 * (1.0 - terrain_risk) + 0.10 * hillshade, 0.0, 1.0)
    raw = raw_layers or {}
    elevation_available = "lola_dem" in raw
    elevation = _clean_elevation_surface(np, raw.get("lola_dem"), shape) if elevation_available else np.zeros(shape, dtype=float)
    surfaces = {
        "hillshade": hillshade,
        "slope": slope,
        "roughness": roughness,
        "shadow": shadow,
        "illumination": illumination,
        "low_illumination": low_illumination,
        "resource": resource,
        "risk": risk,
        "psr_boundary": psr_boundary,
        "psr_interior": psr_interior,
        "crater_edge_risk": crater_edge_risk,
        "steep_slope": steep_slope,
        "rough_block": rough_block,
        "terrain_risk": terrain_risk,
        "elevation_m": elevation,
        "elevation_available": elevation_available,
    }
    return resource, risk, surfaces


def _boundary_score(np: Any, shadow: Any) -> Any:
    values = np.asarray(shadow, dtype=float)
    gy, gx = np.gradient(values)
    grad = np.sqrt(gx * gx + gy * gy)
    finite = grad[np.isfinite(grad)]
    if finite.size == 0:
        return np.zeros_like(values)
    high = float(np.percentile(finite, 98))
    if high <= 1.0e-12:
        return np.zeros_like(values)
    return np.clip(grad / high, 0.0, 1.0)


def _clean_elevation_surface(np: Any, elevation: Any, shape: tuple[int, int]) -> Any:
    if elevation is None:
        return np.zeros(shape, dtype=float)
    values = np.asarray(elevation, dtype=float)
    if values.shape != shape:
        values = np.resize(values, shape)
    finite = values[np.isfinite(values)]
    fill = float(np.median(finite)) if finite.size else 0.0
    return np.where(np.isfinite(values), values, fill)


def _center_depot_payload(surfaces: dict[str, Any], *, extent_km: float) -> dict[str, Any]:
    cells = int(surfaces["resource"].shape[0])
    row = col = cells // 2
    if cells % 2 == 0:
        row = col = cells // 2 - 1
    return {
        "id": "depot",
        "kind": "peak_of_eternal_light",
        "xy_km": [float(extent_km) / 2.0, float(extent_km) / 2.0],
        "selection_policy": "sp50_depot_centered_on_selected_global_peak_v1",
        "elevation_m": round(float(surfaces["elevation_m"][row, col]), 6),
        "elevation_available": bool(surfaces.get("elevation_available", False)),
        "local_shadow_score": round(float(surfaces["shadow"][row, col]), 6),
        "local_illumination_score": round(float(surfaces["illumination"][row, col]), 6),
        "local_terrain_risk": round(float(surfaces["terrain_risk"][row, col]), 6),
    }


def _named_region_comparison(global_x_km: float, global_y_km: float) -> list[dict[str, Any]]:
    # Approximate south-pole literature anchors in local polar stereographic km.
    # These are used only as descriptive proximity evidence; raster scoring remains
    # data-driven from LOLA/illumination layers.
    anchors = {
        "south_pole_center": (0.0, 0.0),
        "shackleton_rim_proxy": (0.0, -6.0),
        "shackleton_de_gerlache_ridge_proxy": (-8.0, 6.0),
        "de_gerlache_rim_proxy": (-18.0, 8.0),
    }
    comparison = []
    for name, xy in anchors.items():
        comparison.append(
            {
                "region": name,
                "anchor_xy_km": [xy[0], xy[1]],
                "distance_to_selected_depot_km": round(math.hypot(float(global_x_km) - xy[0], float(global_y_km) - xy[1]), 6),
                "anchor_status": "approximate_literature_proxy",
            }
        )
    comparison.sort(key=lambda item: float(item["distance_to_selected_depot_km"]))
    return comparison


def _select_depot_candidate(
    np: Any,
    surfaces: dict[str, Any],
    *,
    extent_km: float,
    search_radius_km: float,
    boundary_margin_km: float,
    benchmark_extent_km: float,
    roi_edge_guard_km: float,
) -> dict[str, Any]:
    cells = int(surfaces["resource"].shape[0])
    center_xy = float(extent_km) / 2.0
    elevation = surfaces["elevation_m"]
    elevation_index = _normalize(np, elevation) if bool(surfaces.get("elevation_available", False)) else np.zeros_like(elevation)
    terrain = np.clip(0.55 * surfaces["slope"] + 0.45 * surfaces["roughness"], 0.0, 1.0)
    shadow = surfaces["shadow"]
    illumination = surfaces["illumination"]
    interest = np.clip(
        0.45 * surfaces["resource"] + 0.30 * surfaces["psr_boundary"] + 0.25 * surfaces["psr_interior"],
        0.0,
        1.0,
    )
    interest_integral = _integral_image(np, interest * interest)
    cell_km = float(extent_km) / float(cells)
    boundary_margin_cells = max(0, int(round(float(boundary_margin_km) / cell_km)))
    roi_half_cells = max(1, int(round(float(benchmark_extent_km) * 0.5 / cell_km)))
    edge_guard_cells = max(1, int(round(float(roi_edge_guard_km) / cell_km)))
    best: tuple[float, float, float, float, float, float, int, int] | None = None
    for row in range(boundary_margin_cells, cells - boundary_margin_cells):
        for col in range(boundary_margin_cells, cells - boundary_margin_cells):
            xy = _cell_to_xy(row, col, cells, extent_km)
            distance_from_center = math.hypot(float(xy[0]) - center_xy, float(xy[1]) - center_xy)
            if distance_from_center > float(search_radius_km):
                continue
            edge_fraction = _roi_edge_interest_fraction(
                interest_integral,
                row=row,
                col=col,
                half_cells=roi_half_cells,
                edge_guard_cells=edge_guard_cells,
            )
            if edge_fraction is None:
                continue
            edge_safety = 1.0 - edge_fraction
            score = (
                0.36 * float(elevation_index[row, col])
                + 0.30 * float(illumination[row, col])
                + 0.10 * (1.0 - float(shadow[row, col]))
                + 0.09 * (1.0 - float(terrain[row, col]))
                + 0.15 * edge_safety
            )
            candidate = (
                score,
                float(illumination[row, col]),
                float(elevation[row, col]),
                edge_safety,
                -float(shadow[row, col]),
                -float(terrain[row, col]),
                row,
                col,
            )
            if best is None or candidate > best:
                best = candidate
    if best is None:
        row = col = cells // 2
        status = "fallback_center"
        edge_fraction = None
    else:
        row, col = int(best[6]), int(best[7])
        edge_fraction = 1.0 - float(best[3])
        status = "illumination_dem_high_non_psr_edge_safe_central_peak"
    return {
        "id": "depot",
        "kind": "peak_of_eternal_light_candidate",
        "xy_km": _cell_to_xy(row, col, cells, extent_km),
        "selection_policy": "central_dem_illumination_non_psr_edge_safe_v1",
        "selection_status": status,
        "selection_search_radius_km": float(search_radius_km),
        "benchmark_extent_km": float(benchmark_extent_km),
        "roi_edge_guard_km": float(roi_edge_guard_km),
        "roi_science_interest_edge_fraction": None if edge_fraction is None else round(float(edge_fraction), 6),
        "elevation_m": round(float(elevation[row, col]), 6),
        "elevation_index": round(float(elevation_index[row, col]), 6),
        "local_shadow_score": round(float(shadow[row, col]), 6),
        "local_illumination_score": round(float(illumination[row, col]), 6),
        "local_terrain_risk": round(float(terrain[row, col]), 6),
    }


def _select_candidate_targets(
    np: Any,
    resource: Any,
    risk: Any,
    surfaces: dict[str, Any],
    *,
    extent_km: float,
    count: int,
    active_footprint_km: float | None,
    depot_xy: list[float],
    sector_count: int,
    boundary_margin_km: float,
) -> list[dict[str, Any]]:
    boundary = surfaces["psr_boundary"]
    interior = surfaces["psr_interior"]
    shadow = surfaces["shadow"]
    terrain = surfaces["terrain_risk"]
    accessibility = np.clip(1.0 - terrain, 0.0, 1.0)
    score = np.clip(0.44 * resource + 0.34 * interior + 0.16 * boundary + 0.06 * accessibility - 0.08 * risk, 0.0, 1.0)
    cells = int(score.shape[0])
    depot_row, depot_col = _xy_to_cell(depot_xy, cells, extent_km)
    cell_km = float(extent_km) / float(cells)
    min_depot_dist = max(4, int(round(3.0 / cell_km)))
    min_target_dist = max(2, int(round(1.6 / cell_km)))
    hotspot_separation = max(min_target_dist * 3, int(round(7.5 / cell_km)))
    hotspot_radius = max(min_target_dist * 3, int(round(7.5 / cell_km)))
    full_footprint = active_footprint_km is not None and float(active_footprint_km) >= float(extent_km) - 1.0e-9
    footprint_half_km = (
        float(active_footprint_km) / 2.0
        if active_footprint_km is not None and not full_footprint
        else None
    )
    boundary_margin_cells = max(0, int(round(float(boundary_margin_km) / cell_km)))
    order = np.argsort(score, axis=None)[::-1]
    depot_x = float(depot_xy[0])
    depot_y = float(depot_xy[1])
    all_candidates: list[tuple[int, int]] = []
    for flat_index in order:
        row, col = (int(flat_index) // cells, int(flat_index) % cells)
        if (
            row < boundary_margin_cells
            or row >= cells - boundary_margin_cells
            or col < boundary_margin_cells
            or col >= cells - boundary_margin_cells
        ):
            continue
        xy = _cell_to_xy(row, col, cells, extent_km)
        if footprint_half_km is not None:
            if abs(float(xy[0]) - depot_x) > footprint_half_km or abs(float(xy[1]) - depot_y) > footprint_half_km:
                continue
        if math.hypot(row - depot_row, col - depot_col) < min_depot_dist:
            continue
        all_candidates.append((row, col))
    desired_hotspots = min(
        len(all_candidates),
        max(int(sector_count), min(30, max(8, int(math.ceil(float(count) / 4.0))))),
    )
    hotspots = _select_water_ice_hotspots(
        all_candidates,
        score,
        cells=cells,
        extent_km=extent_km,
        depot_xy=depot_xy,
        sector_count=int(sector_count),
        desired_count=desired_hotspots,
        min_distance_cells=hotspot_separation,
    )
    if not hotspots:
        hotspots = all_candidates[: max(1, min(int(count), len(all_candidates)))]
    hotspot_buckets = _bucket_candidates_by_hotspot(
        all_candidates,
        hotspots,
        max_radius_cells=hotspot_radius,
    )
    if int(count) <= int(sector_count):
        hotspot_quota = max(1, int(math.ceil(0.60 * float(count))))
    else:
        hotspot_quota = min(int(count), max(int(sector_count), int(math.ceil(0.65 * float(count)))))
    exploration_quota = max(0, int(count) - hotspot_quota)
    hotspot_edge_quota = max(1, min(hotspot_quota, int(round(0.35 * float(hotspot_quota)))))
    hotspot_core_quota = max(0, hotspot_quota - hotspot_edge_quota)
    selected: list[tuple[int, int]] = []
    selected_hotspot: dict[tuple[int, int], int] = {}
    selected_role: dict[tuple[int, int], str] = {}
    hotspot_order = list(range(len(hotspots)))
    _select_from_hotspot_buckets(
        selected,
        selected_hotspot,
        selected_role,
        hotspot_buckets,
        hotspots,
        hotspot_order=hotspot_order,
        quota=hotspot_core_quota,
        min_spacing_cells=min_target_dist,
        role="hotspot_core",
        edge_mode=False,
        boundary=boundary,
        interior=interior,
        resource=resource,
    )
    _select_from_hotspot_buckets(
        selected,
        selected_hotspot,
        selected_role,
        hotspot_buckets,
        hotspots,
        hotspot_order=hotspot_order,
        quota=hotspot_edge_quota,
        min_spacing_cells=min_target_dist,
        role="hotspot_edge",
        edge_mode=True,
        boundary=boundary,
        interior=interior,
        resource=resource,
    )
    while len(selected) < hotspot_quota:
        progressed = False
        for hotspot_index in hotspot_order:
            bucket = hotspot_buckets.get(hotspot_index, [])
            while bucket:
                row, col = bucket.pop(0)
                if any(math.hypot(row - r, col - c) < min_target_dist for r, c in selected):
                    continue
                selected.append((row, col))
                selected_hotspot[(row, col)] = hotspot_index
                selected_role[(row, col)] = "hotspot_edge" if _is_hotspot_edge_cell(row, col, boundary=boundary, interior=interior, resource=resource) else "hotspot_core"
                progressed = True
                break
            if len(selected) >= hotspot_quota:
                break
        if not progressed:
            break
    exploration_pool = sorted(
        all_candidates,
        key=lambda item: _exploration_candidate_score(
            item,
            resource=resource,
            boundary=boundary,
            interior=interior,
            shadow=shadow,
            terrain=terrain,
            score=score,
        ),
        reverse=True,
    )
    exploration_spacing = max(min_target_dist * 2, int(round(4.0 / cell_km)))
    for row, col in exploration_pool:
        if len(selected) >= hotspot_quota + exploration_quota:
            break
        if any(row == r and col == c for r, c in selected):
            continue
        if any(math.hypot(row - r, col - c) < exploration_spacing for r, c in selected):
            continue
        selected.append((row, col))
        selected_hotspot[(row, col)] = _nearest_hotspot_index((row, col), hotspots)
        selected_role[(row, col)] = "exploration"
    for row, col in all_candidates:
        if len(selected) >= int(count):
            break
        if any(row == r and col == c for r, c in selected):
            continue
        if any(math.hypot(row - r, col - c) < max(1, min_target_dist // 2) for r, c in selected):
            continue
        selected.append((row, col))
        selected_hotspot[(row, col)] = _nearest_hotspot_index((row, col), hotspots)
        selected_role[(row, col)] = "hotspot_fill"
    targets: list[dict[str, Any]] = []
    for index, (row, col) in enumerate(selected, start=1):
        hotspot_index = selected_hotspot.get((row, col), _nearest_hotspot_index((row, col), hotspots))
        hotspot_row, hotspot_col = hotspots[hotspot_index] if hotspots else (row, col)
        hotspot_xy = _cell_to_xy(hotspot_row, hotspot_col, cells, extent_km)
        targets.append(
            {
                "id": f"candidate_{index:03d}",
                "xy_km": _cell_to_xy(row, col, cells, extent_km),
                "hotspot_id": f"hotspot_{hotspot_index + 1:02d}",
                "hotspot_rank": int(hotspot_index + 1),
                "hotspot_xy_km": hotspot_xy,
                "hotspot_score": round(float(score[hotspot_row, hotspot_col]), 6),
                "hotspot_distance_km": round(float(math.hypot(row - hotspot_row, col - hotspot_col) * cell_km), 6),
                "candidate_role": selected_role.get((row, col), "hotspot"),
                "direction_sector": _direction_sector(
                    _cell_to_xy(row, col, cells, extent_km),
                    depot_xy,
                    sector_count=int(sector_count),
                ),
                "resource_score": round(float(resource[row, col]), 6),
                "risk_score": round(float(risk[row, col]), 6),
                "selection_score": round(float(score[row, col]), 6),
                "psr_boundary_score": round(float(boundary[row, col]), 6),
                "psr_interior_score": round(float(interior[row, col]), 6),
                "local_shadow_score": round(float(shadow[row, col]), 6),
                "local_terrain_risk": round(float(terrain[row, col]), 6),
                "science_zone": _science_zone(float(boundary[row, col]), float(interior[row, col]), float(shadow[row, col])),
                "recommended_operation_mode": _recommended_operation_mode(
                    boundary_score=float(boundary[row, col]),
                    interior_score=float(interior[row, col]),
                    resource_score=float(resource[row, col]),
                ),
            }
        )
    return targets


def _select_water_ice_hotspots(
    candidates: list[tuple[int, int]],
    score: Any,
    *,
    cells: int,
    extent_km: float,
    depot_xy: list[float],
    sector_count: int,
    desired_count: int,
    min_distance_cells: int,
) -> list[tuple[int, int]]:
    if not candidates or desired_count <= 0:
        return []
    search_pool = candidates[: min(len(candidates), 9000)]
    selected: list[tuple[int, int]] = []
    selected_sectors: list[int] = []
    depot_x = float(depot_xy[0])
    depot_y = float(depot_xy[1])
    for _ in range(int(desired_count)):
        best: tuple[float, float, float, float, int, int, int] | None = None
        for row, col in search_pool:
            if any(math.hypot(row - r, col - c) < min_distance_cells for r, c in selected):
                continue
            xy = _cell_to_xy(row, col, cells, extent_km)
            sector = _direction_sector(xy, depot_xy, sector_count=sector_count)
            diversity = _sector_diversity_score(sector, selected_sectors, sector_count=sector_count) if selected_sectors else 1.0
            distance_km = math.hypot(float(xy[0]) - depot_x, float(xy[1]) - depot_y)
            radial = min(1.0, distance_km / max(1.0, 0.45 * float(extent_km)))
            local_score = float(score[row, col])
            value = local_score + 0.16 * diversity + 0.04 * radial
            candidate = (value, local_score, diversity, radial, -sector, row, col)
            if best is None or candidate > best:
                best = candidate
        if best is None:
            break
        row, col = int(best[5]), int(best[6])
        selected.append((row, col))
        selected_sectors.append(_direction_sector(_cell_to_xy(row, col, cells, extent_km), depot_xy, sector_count=sector_count))
    return selected


def _exploration_candidate_score(
    candidate: tuple[int, int],
    *,
    resource: Any,
    boundary: Any,
    interior: Any,
    shadow: Any,
    terrain: Any,
    score: Any,
) -> float:
    row, col = candidate
    resource_value = float(resource[row, col])
    boundary_value = float(boundary[row, col])
    interior_value = float(interior[row, col])
    shadow_value = float(shadow[row, col])
    terrain_value = float(terrain[row, col])
    moderate_resource = max(0.0, 1.0 - abs(resource_value - 0.38) / 0.38)
    uncertainty = max(0.0, 1.0 - abs(interior_value - 0.25) / 0.75)
    return (
        0.30 * boundary_value
        + 0.22 * moderate_resource
        + 0.18 * uncertainty
        + 0.14 * max(0.0, 1.0 - terrain_value)
        + 0.10 * shadow_value
        + 0.06 * float(score[row, col])
    )


def _bucket_candidates_by_hotspot(
    candidates: list[tuple[int, int]],
    hotspots: list[tuple[int, int]],
    *,
    max_radius_cells: int,
) -> dict[int, list[tuple[int, int]]]:
    buckets: dict[int, list[tuple[int, int]]] = {index: [] for index in range(len(hotspots))}
    if not hotspots:
        return buckets
    for row, col in candidates:
        hotspot_index = _nearest_hotspot_index((row, col), hotspots)
        hotspot_row, hotspot_col = hotspots[hotspot_index]
        if math.hypot(row - hotspot_row, col - hotspot_col) <= float(max_radius_cells):
            buckets[hotspot_index].append((row, col))
    return buckets


def _select_from_hotspot_buckets(
    selected: list[tuple[int, int]],
    selected_hotspot: dict[tuple[int, int], int],
    selected_role: dict[tuple[int, int], str],
    hotspot_buckets: dict[int, list[tuple[int, int]]],
    hotspots: list[tuple[int, int]],
    *,
    hotspot_order: list[int],
    quota: int,
    min_spacing_cells: int,
    role: str,
    edge_mode: bool,
    boundary: Any,
    interior: Any,
    resource: Any,
) -> None:
    if quota <= 0:
        return
    target_total = len(selected) + int(quota)
    while len(selected) < target_total:
        progressed = False
        for hotspot_index in hotspot_order:
            bucket = hotspot_buckets.get(hotspot_index, [])
            chosen_index: int | None = None
            for index, (row, col) in enumerate(bucket):
                if _is_hotspot_edge_cell(row, col, boundary=boundary, interior=interior, resource=resource) != edge_mode:
                    continue
                if any(math.hypot(row - r, col - c) < min_spacing_cells for r, c in selected):
                    continue
                chosen_index = index
                break
            if chosen_index is None:
                continue
            row, col = bucket.pop(chosen_index)
            selected.append((row, col))
            selected_hotspot[(row, col)] = hotspot_index if 0 <= hotspot_index < len(hotspots) else 0
            selected_role[(row, col)] = role
            progressed = True
            if len(selected) >= target_total:
                break
        if not progressed:
            break


def _is_hotspot_edge_cell(
    row: int,
    col: int,
    *,
    boundary: Any,
    interior: Any,
    resource: Any,
) -> bool:
    boundary_value = float(boundary[row, col])
    interior_value = float(interior[row, col])
    resource_value = float(resource[row, col])
    if interior_value >= 0.75 and boundary_value < 0.12:
        return False
    return (
        boundary_value >= 0.25
        or (0.18 <= interior_value <= 0.60 and resource_value >= 0.32)
        or (resource_value >= 0.50 and boundary_value >= 0.12)
    )


def _nearest_hotspot_index(candidate: tuple[int, int], hotspots: list[tuple[int, int]]) -> int:
    if not hotspots:
        return 0
    row, col = candidate
    return min(
        range(len(hotspots)),
        key=lambda index: math.hypot(row - hotspots[index][0], col - hotspots[index][1]),
    )


def _direction_sector(xy_km: list[float], depot_xy: list[float], *, sector_count: int) -> int:
    angle = math.atan2(float(xy_km[1]) - float(depot_xy[1]), float(xy_km[0]) - float(depot_xy[0]))
    return int(((angle + math.pi) / (2.0 * math.pi)) * int(sector_count)) % int(sector_count)


def _science_zone(boundary_score: float, interior_score: float, shadow_score: float) -> str:
    if interior_score >= 0.45:
        return "psr_interior"
    if boundary_score >= 0.25:
        return "psr_boundary"
    if shadow_score >= 0.35:
        return "shallow_shadow"
    return "access_corridor"


def _recommended_operation_mode(*, boundary_score: float, interior_score: float, resource_score: float) -> str:
    if interior_score >= 0.55 and resource_score >= 0.55:
        return "drill"
    if interior_score >= 0.35 or resource_score >= 0.60:
        return "sample"
    if boundary_score >= 0.20:
        return "detect"
    return "detect"


def _quality_spread_sector_order(sector_best: dict[int, float], *, sector_count: int) -> list[int]:
    remaining = {sector for sector, value in sector_best.items() if math.isfinite(value)}
    order: list[int] = []
    while remaining:
        if not order:
            chosen = max(remaining, key=lambda sector: (sector_best[sector], -sector))
        else:
            chosen = max(
                remaining,
                key=lambda sector: (
                    sector_best[sector] + 0.25 * _sector_diversity_score(sector, order, sector_count=sector_count),
                    sector_best[sector],
                    -sector,
                ),
            )
        order.append(chosen)
        remaining.remove(chosen)
    return order


def _sector_diversity_score(sector: int, selected: list[int], *, sector_count: int) -> float:
    if not selected:
        return 1.0
    half = max(1.0, float(sector_count) / 2.0)
    min_distance = min(min(abs(sector - other), sector_count - abs(sector - other)) for other in selected)
    return min(1.0, float(min_distance) / half)


def _build_preview_path_options(
    *,
    np: Any,
    surfaces: dict[str, Any],
    targets: list[dict[str, Any]],
    depot_xy: list[float],
    extent_km: float,
) -> list[dict[str, Any]]:
    cells = int(surfaces["resource"].shape[0])
    start = _xy_to_cell(depot_xy, cells, extent_km)
    cost_surfaces = _preview_cost_surfaces(surfaces)
    options: list[dict[str, Any]] = []
    for target in targets:
        goal = _xy_to_cell(target["xy_km"], cells, extent_km)
        for option in _build_directed_path_options(
            np=np,
            cost_surfaces=cost_surfaces,
            surfaces=surfaces,
            start=start,
            goal=goal,
            extent_km=extent_km,
        ):
            preview_option = {
                "target_id": target["id"],
                "from": "depot",
                "to": target["id"],
            }
            preview_option.update(option)
            options.append(preview_option)
    return options


def _build_directed_path_options(
    *,
    np: Any,
    cost_surfaces: dict[str, Any],
    surfaces: dict[str, Any],
    start: tuple[int, int],
    goal: tuple[int, int],
    extent_km: float,
    first_path_override: list[tuple[int, int]] | None = None,
) -> list[dict[str, Any]]:
    cells = int(surfaces["resource"].shape[0])
    prior_paths: list[list[tuple[int, int]]] = []
    options: list[dict[str, Any]] = []
    for path_type in PATH_TYPES:
        cost = _cost_with_diversity_penalty(np, cost_surfaces[path_type], prior_paths, path_type=path_type)
        if path_type == "low_time" and first_path_override is not None:
            cells_path = first_path_override
        else:
            cells_path = _dijkstra_grid_path(
                cost,
                start,
                goal,
                elevation=surfaces.get("elevation_m"),
                elevation_available=bool(surfaces.get("elevation_available", False)),
                path_type=path_type,
                extent_km=extent_km,
            )
        points = [_cell_to_xy(row, col, cells, extent_km) for row, col in _thin_path(cells_path, max_points=80)]
        metrics = _path_metrics(cells_path, surfaces=surfaces, extent_km=extent_km)
        generalized = {
            "low_time": metrics["travel_time_min"],
            "low_energy": metrics["energy_proxy"],
            "low_risk": metrics["risk_integral"],
        }[path_type]
        option = {
            "path_type": path_type,
            "aliases": [path_type],
            "generalized_cost": round(generalized, 6),
            "path_cells": [],
            "path_xy": points,
            "diversity_penalty_applied": bool(prior_paths),
        }
        option.update(metrics)
        options.append(option)
        prior_paths.append(cells_path)
    return options


def _cost_with_diversity_penalty(np: Any, base_cost: Any, prior_paths: list[list[tuple[int, int]]], *, path_type: str) -> Any:
    if not prior_paths:
        return base_cost
    penalty = {"low_time": 0.0, "low_energy": 0.35, "low_risk": 0.55}.get(path_type, 0.35)
    if penalty <= 0.0:
        return base_cost
    adjusted = np.array(base_cost, dtype=float, copy=True)
    rows, cols = int(adjusted.shape[0]), int(adjusted.shape[1])
    radius = {"low_energy": 2, "low_risk": 3}.get(path_type, 2)
    offsets = [
        (dr, dc, math.hypot(dr, dc))
        for dr in range(-radius, radius + 1)
        for dc in range(-radius, radius + 1)
        if math.hypot(dr, dc) <= float(radius)
    ]
    for path in prior_paths:
        for row, col in path:
            for dr, dc, dist in offsets:
                rr, cc = row + dr, col + dc
                if rr < 0 or rr >= rows or cc < 0 or cc >= cols:
                    continue
                decay = 1.0 / (1.0 + dist)
                adjusted[rr, cc] += penalty * decay
    return adjusted


def _preview_cost_surfaces(surfaces: dict[str, Any]) -> dict[str, Any]:
    np = __import__("numpy")
    slope = surfaces["slope"]
    roughness = surfaces["roughness"]
    shadow = surfaces["shadow"]
    boundary = surfaces["psr_boundary"]
    interior = surfaces["psr_interior"]
    crater_edge = surfaces.get("crater_edge_risk", boundary)
    steep = surfaces.get("steep_slope", np.power(np.clip(slope, 0.0, 1.0), 1.75))
    rough_block = surfaces.get("rough_block", np.power(np.clip(roughness, 0.0, 1.0), 1.45))
    return {
        "low_time": np.clip(
            1.0
            + 0.55 * slope
            + 0.25 * roughness
            + 0.18 * shadow
            + 0.22 * crater_edge
            + 0.40 * steep,
            0.05,
            None,
        ),
        "low_energy": np.clip(
            1.0
            + 0.95 * slope
            + 0.46 * roughness
            + 0.62 * shadow
            + 0.42 * boundary
            + 0.38 * interior
            + 1.05 * steep
            + 0.34 * rough_block,
            0.05,
            None,
        ),
        "low_risk": np.clip(
            1.0
            + 1.18 * slope
            + 0.82 * roughness
            + 1.72 * shadow
            + 1.12 * boundary
            + 1.28 * interior
            + 1.85 * steep
            + 0.74 * rough_block
            + 0.62 * crater_edge,
            0.05,
            None,
        ),
    }


def _path_metrics(path: list[tuple[int, int]], *, surfaces: dict[str, Any], extent_km: float) -> dict[str, float]:
    config = LunarIceConfig()
    cells = int(surfaces["resource"].shape[0])
    cell_km = float(extent_km) / float(cells)
    distance = 0.0
    for index in range(1, len(path)):
        r0, c0 = path[index - 1]
        r1, c1 = path[index]
        distance += math.hypot(r1 - r0, c1 - c0) * cell_km
    if not path:
        return {
            "path_distance_km": 0.0,
            "travel_time_min": 0.0,
            "energy_proxy": 0.0,
            "risk_integral": 0.0,
            "shadow_exposure_min": 0.0,
            "climb_energy_proxy": 0.0,
            "descent_control_energy_proxy": 0.0,
            "positive_elevation_gain_m": 0.0,
            "negative_elevation_loss_m": 0.0,
            "avg_uphill_grade": 0.0,
            "avg_downhill_grade": 0.0,
            "directional_elevation_status": "unavailable",
            "avg_slope_risk": 0.0,
            "avg_roughness_risk": 0.0,
            "avg_shadow": 0.0,
            "avg_psr_boundary": 0.0,
            "avg_psr_interior": 0.0,
            "avg_crater_edge_risk": 0.0,
            "avg_steep_slope": 0.0,
            "avg_lunar_ice_risk": 0.0,
            "avg_resource_index": 0.0,
        }
    slope = _sample_surface(surfaces["slope"], path)
    roughness = _sample_surface(surfaces["roughness"], path)
    shadow = _sample_surface(surfaces["shadow"], path)
    resource = _sample_surface(surfaces["resource"], path)
    boundary = _sample_surface(surfaces["psr_boundary"], path)
    interior = _sample_surface(surfaces["psr_interior"], path)
    crater_edge = _sample_surface(surfaces.get("crater_edge_risk", surfaces["psr_boundary"]), path)
    steep = _sample_surface(surfaces.get("steep_slope", surfaces["slope"]), path)
    elevation_stats = _path_elevation_stats(
        surfaces.get("elevation_m"),
        path,
        extent_km=extent_km,
        elevation_available=bool(surfaces.get("elevation_available", False)),
    )
    uphill_grade = elevation_stats["avg_uphill_grade"]
    downhill_grade = elevation_stats["avg_downhill_grade"]
    lunar_ice_risk = min(
        1.0,
        max(
            0.0,
            0.24 * slope
            + 0.16 * roughness
            + 0.28 * shadow
            + 0.14 * boundary
            + 0.10 * interior
            + 0.08 * steep,
        ),
    )
    speed = config.rover_max_speed_kmh / (
        1.0
        + 0.55 * lunar_ice_risk
        + 0.42 * shadow
        + 0.24 * slope
        + 0.18 * boundary
        + 0.16 * interior
        + 0.32 * steep
        + 1.10 * uphill_grade
        + 0.35 * downhill_grade
    )
    speed = max(8.0, min(config.rover_max_speed_kmh, speed))
    travel_time = 60.0 * distance / max(1.0e-9, speed)
    shadow_exposure = travel_time * shadow
    thermal_survival_energy = shadow_exposure * 0.08
    climb_energy = 0.035 * elevation_stats["positive_elevation_gain_m"]
    descent_control_energy = 0.010 * elevation_stats["negative_elevation_loss_m"]
    terrain_energy = distance * (0.36 * crater_edge + 0.28 * steep + 0.18 * interior)
    energy = (
        1.60 * distance
        + 2.20 * distance * lunar_ice_risk
        + terrain_energy
        + thermal_survival_energy
        + climb_energy
        + descent_control_energy
    )
    risk_integral = distance * (
        0.26 * lunar_ice_risk
        + 0.22 * shadow
        + 0.16 * roughness
        + 0.16 * slope
        + 0.12 * boundary
        + 0.10 * interior
        + 0.10 * steep
        + 0.18 * uphill_grade
        + 0.12 * downhill_grade
    )
    return {
        "path_distance_km": round(distance, 6),
        "travel_time_min": round(travel_time, 6),
        "energy_proxy": round(energy, 6),
        "risk_integral": round(risk_integral, 6),
        "shadow_exposure_min": round(shadow_exposure, 6),
        "thermal_survival_energy_proxy": round(thermal_survival_energy, 6),
        "climb_energy_proxy": round(climb_energy, 6),
        "descent_control_energy_proxy": round(descent_control_energy, 6),
        "positive_elevation_gain_m": round(elevation_stats["positive_elevation_gain_m"], 6),
        "negative_elevation_loss_m": round(elevation_stats["negative_elevation_loss_m"], 6),
        "avg_uphill_grade": round(uphill_grade, 6),
        "avg_downhill_grade": round(downhill_grade, 6),
        "directional_elevation_status": elevation_stats["status"],
        "avg_slope_risk": round(slope, 6),
        "avg_roughness_risk": round(roughness, 6),
        "avg_shadow": round(shadow, 6),
        "avg_psr_boundary": round(boundary, 6),
        "avg_psr_interior": round(interior, 6),
        "avg_crater_edge_risk": round(crater_edge, 6),
        "avg_steep_slope": round(steep, 6),
        "avg_lunar_ice_risk": round(lunar_ice_risk, 6),
        "avg_resource_index": round(resource, 6),
    }


def _path_elevation_stats(
    elevation: Any,
    path: list[tuple[int, int]],
    *,
    extent_km: float,
    elevation_available: bool,
) -> dict[str, Any]:
    if not elevation_available or elevation is None or len(path) < 2:
        return {
            "status": "unavailable",
            "positive_elevation_gain_m": 0.0,
            "negative_elevation_loss_m": 0.0,
            "avg_uphill_grade": 0.0,
            "avg_downhill_grade": 0.0,
        }
    cells = int(elevation.shape[0])
    cell_km = float(extent_km) / float(cells)
    climb = 0.0
    descent = 0.0
    distance_m = 0.0
    for index in range(1, len(path)):
        r0, c0 = path[index - 1]
        r1, c1 = path[index]
        e0 = float(elevation[r0, c0])
        e1 = float(elevation[r1, c1])
        if not math.isfinite(e0) or not math.isfinite(e1):
            continue
        delta = e1 - e0
        step_m = math.hypot(r1 - r0, c1 - c0) * cell_km * 1000.0
        distance_m += step_m
        if delta > 0.0:
            climb += delta
        else:
            descent += -delta
    if distance_m <= 1.0e-9:
        uphill_grade = 0.0
        downhill_grade = 0.0
    else:
        uphill_grade = min(0.35, climb / distance_m)
        downhill_grade = min(0.35, descent / distance_m)
    return {
        "status": "available",
        "positive_elevation_gain_m": climb,
        "negative_elevation_loss_m": descent,
        "avg_uphill_grade": uphill_grade,
        "avg_downhill_grade": downhill_grade,
    }


def _sample_surface(surface: Any, path: list[tuple[int, int]]) -> float:
    if not path:
        return 0.0
    total = 0.0
    for row, col in path:
        total += float(surface[row, col])
    return total / float(len(path))


def _dijkstra_grid_path(
    cost: Any,
    start: tuple[int, int],
    goal: tuple[int, int],
    *,
    elevation: Any | None = None,
    elevation_available: bool = False,
    path_type: str = "low_time",
    extent_km: float = 30.0,
) -> list[tuple[int, int]]:
    rows, cols = int(cost.shape[0]), int(cost.shape[1])
    cell_km = float(extent_km) / float(max(rows, 1))
    try:
        min_cost = max(1.0e-9, float(__import__("numpy").nanmin(cost)))
    except Exception:
        min_cost = 1.0e-9
    def heuristic(cell: tuple[int, int]) -> float:
        return min_cost * math.hypot(goal[0] - cell[0], goal[1] - cell[1])

    queue: list[tuple[float, float, tuple[int, int]]] = [(heuristic(start), 0.0, start)]
    dist = {start: 0.0}
    prev: dict[tuple[int, int], tuple[int, int]] = {}
    neighbors = ((-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0), (-1, -1, math.sqrt(2.0)), (-1, 1, math.sqrt(2.0)), (1, -1, math.sqrt(2.0)), (1, 1, math.sqrt(2.0)))
    while queue:
        _, current_dist, current = heapq.heappop(queue)
        if current == goal:
            break
        if current_dist > dist.get(current, math.inf) + 1.0e-12:
            continue
        row, col = current
        for dr, dc, step in neighbors:
            nr, nc = row + dr, col + dc
            if nr < 0 or nr >= rows or nc < 0 or nc >= cols:
                continue
            directional = _directional_grade_multiplier(
                elevation,
                row,
                col,
                nr,
                nc,
                step_cells=step,
                cell_km=cell_km,
                path_type=path_type,
                elevation_available=elevation_available,
            )
            move = step * 0.5 * (float(cost[row, col]) + float(cost[nr, nc])) * directional
            new_dist = current_dist + move
            nxt = (nr, nc)
            if new_dist + 1.0e-12 < dist.get(nxt, math.inf):
                dist[nxt] = new_dist
                prev[nxt] = current
                heapq.heappush(queue, (new_dist + heuristic(nxt), new_dist, nxt))
    if goal not in dist:
        return [start, goal]
    path = [goal]
    while path[-1] != start:
        path.append(prev[path[-1]])
    path.reverse()
    return path


def _dijkstra_grid_paths_to_goals(
    cost: Any,
    start: tuple[int, int],
    goals: list[tuple[int, int]],
    *,
    elevation: Any | None = None,
    elevation_available: bool = False,
    path_type: str = "low_time",
    extent_km: float = 30.0,
) -> dict[tuple[int, int], list[tuple[int, int]]]:
    unique_goals = {goal for goal in goals if goal != start}
    if not unique_goals:
        return {}
    rows, cols = int(cost.shape[0]), int(cost.shape[1])
    cell_km = float(extent_km) / float(max(rows, 1))
    queue: list[tuple[float, tuple[int, int]]] = [(0.0, start)]
    dist = {start: 0.0}
    prev: dict[tuple[int, int], tuple[int, int]] = {}
    settled_goals: set[tuple[int, int]] = set()
    neighbors = ((-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0), (-1, -1, math.sqrt(2.0)), (-1, 1, math.sqrt(2.0)), (1, -1, math.sqrt(2.0)), (1, 1, math.sqrt(2.0)))
    while queue and len(settled_goals) < len(unique_goals):
        current_dist, current = heapq.heappop(queue)
        if current_dist > dist.get(current, math.inf) + 1.0e-12:
            continue
        if current in unique_goals:
            settled_goals.add(current)
            if len(settled_goals) >= len(unique_goals):
                break
        row, col = current
        for dr, dc, step in neighbors:
            nr, nc = row + dr, col + dc
            if nr < 0 or nr >= rows or nc < 0 or nc >= cols:
                continue
            directional = _directional_grade_multiplier(
                elevation,
                row,
                col,
                nr,
                nc,
                step_cells=step,
                cell_km=cell_km,
                path_type=path_type,
                elevation_available=elevation_available,
            )
            move = step * 0.5 * (float(cost[row, col]) + float(cost[nr, nc])) * directional
            new_dist = current_dist + move
            nxt = (nr, nc)
            if new_dist + 1.0e-12 < dist.get(nxt, math.inf):
                dist[nxt] = new_dist
                prev[nxt] = current
                heapq.heappush(queue, (new_dist, nxt))
    paths: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for goal in unique_goals:
        if goal not in dist:
            paths[goal] = [start, goal]
            continue
        path = [goal]
        while path[-1] != start:
            path.append(prev[path[-1]])
        path.reverse()
        paths[goal] = path
    return paths


def _directional_grade_multiplier(
    elevation: Any | None,
    row: int,
    col: int,
    nr: int,
    nc: int,
    *,
    step_cells: float,
    cell_km: float,
    path_type: str,
    elevation_available: bool,
) -> float:
    if not elevation_available or elevation is None:
        return 1.0
    e0 = float(elevation[row, col])
    e1 = float(elevation[nr, nc])
    if not math.isfinite(e0) or not math.isfinite(e1):
        return 1.0
    step_m = max(1.0e-9, float(step_cells) * float(cell_km) * 1000.0)
    grade = (e1 - e0) / step_m
    uphill = min(0.35, max(0.0, grade))
    downhill = min(0.35, max(0.0, -grade))
    uphill_weight, downhill_weight = {
        "low_time": (0.90, 0.30),
        "low_energy": (2.40, 0.18),
        "low_risk": (1.15, 0.85),
    }.get(path_type, (1.0, 0.35))
    return 1.0 + uphill_weight * uphill + downhill_weight * downhill


def _thin_path(path: list[tuple[int, int]], *, max_points: int) -> list[tuple[int, int]]:
    if len(path) <= max_points:
        return path
    step = max(1, int(math.ceil(len(path) / float(max_points - 1))))
    thinned = path[::step]
    if thinned[-1] != path[-1]:
        thinned.append(path[-1])
    return thinned


def _cell_to_xy(row: int, col: int, cells: int, extent_km: float) -> list[float]:
    x = (float(col) + 0.5) / float(cells) * float(extent_km)
    y = (1.0 - (float(row) + 0.5) / float(cells)) * float(extent_km)
    return [round(x, 6), round(y, 6)]


def _xy_to_cell(xy_km: list[float], cells: int, extent_km: float) -> tuple[int, int]:
    col = int(max(0, min(cells - 1, math.floor(float(xy_km[0]) / float(extent_km) * cells))))
    row = int(max(0, min(cells - 1, math.floor((1.0 - float(xy_km[1]) / float(extent_km)) * cells))))
    return row, col


def _round_matrix(array: Any) -> list[list[float]]:
    return [[round(float(value), 4) for value in row] for row in array.tolist()]


def _integral_image(np: Any, values: Any) -> Any:
    clean = np.where(np.isfinite(values), values, 0.0)
    padded = np.pad(clean, ((1, 0), (1, 0)), mode="constant", constant_values=0.0)
    return padded.cumsum(axis=0).cumsum(axis=1)


def _roi_edge_interest_fraction(
    integral: Any,
    *,
    row: int,
    col: int,
    half_cells: int,
    edge_guard_cells: int,
) -> float | None:
    rows = int(integral.shape[0]) - 1
    cols = int(integral.shape[1]) - 1
    row0, row1 = int(row) - int(half_cells), int(row) + int(half_cells)
    col0, col1 = int(col) - int(half_cells), int(col) + int(half_cells)
    if row0 < 0 or col0 < 0 or row1 > rows or col1 > cols:
        return None
    total = _rect_sum(integral, row0, col0, row1, col1)
    if total <= 1.0e-12:
        return 1.0
    inner_half = max(1, int(half_cells) - int(edge_guard_cells))
    inner_row0, inner_row1 = int(row) - inner_half, int(row) + inner_half
    inner_col0, inner_col1 = int(col) - inner_half, int(col) + inner_half
    inner = _rect_sum(integral, inner_row0, inner_col0, inner_row1, inner_col1)
    return max(0.0, min(1.0, (total - inner) / total))


def _rect_sum(integral: Any, row0: int, col0: int, row1: int, col1: int) -> float:
    return float(integral[row1, col1] - integral[row0, col1] - integral[row1, col0] + integral[row0, col0])


def _downsample_grid(matrix: list[list[float]], *, max_cells: int) -> list[list[float]]:
    rows = len(matrix)
    cols = len(matrix[0]) if rows else 0
    if rows <= max_cells and cols <= max_cells:
        return matrix
    result: list[list[float]] = []
    for row_idx in range(max_cells):
        src_row = min(rows - 1, int(row_idx * rows / max_cells))
        row: list[float] = []
        for col_idx in range(max_cells):
            src_col = min(cols - 1, int(col_idx * cols / max_cells))
            row.append(float(matrix[src_row][src_col]))
        result.append(row)
    return result


def _resource_risk_color(resource: float, risk: float) -> str:
    resource_v = _smoothstep(_clamp(resource))
    risk_v = _smoothstep(_clamp(risk))
    base = _blend_rgb((239, 222, 181), (219, 194, 151), 0.24 * risk_v)
    basin_blue = (92, 130, 151)
    ice_blue = (153, 184, 196)
    risk_warm = (190, 128, 98)
    color = _blend_rgb(base, basin_blue, 0.54 * resource_v)
    color = _blend_rgb(color, ice_blue, 0.22 * _smoothstep(resource_v))
    color = _blend_rgb(color, risk_warm, 0.17 * risk_v)
    return _rgb_hex(color)


def _dem_color(value: float) -> str:
    v = _clamp(value)
    if v < 0.34:
        return _rgb_hex(_blend_rgb((78, 111, 130), (137, 158, 156), _smoothstep(v / 0.34)))
    if v < 0.66:
        return _rgb_hex(_blend_rgb((137, 158, 156), (219, 197, 151), _smoothstep((v - 0.34) / 0.32)))
    if v < 0.86:
        return _rgb_hex(_blend_rgb((219, 197, 151), (203, 141, 111), _smoothstep((v - 0.66) / 0.20)))
    return _rgb_hex(_blend_rgb((203, 141, 111), (248, 234, 195), _smoothstep((v - 0.86) / 0.14)))


def _path_color(path_type: str) -> str:
    return {
        "low_time": "#5A91B1",
        "low_energy": "#6D9A72",
        "low_risk": "#C79A4A",
    }.get(path_type, "#f8fafc")


def _science_zone_color(zone: str) -> str:
    return {
        "psr_boundary": "#9BC3D4",
        "psr_interior": "#6F92B3",
        "shallow_shadow": "#B8C8C9",
        "access_corridor": "#E4CB86",
    }.get(zone, "#f8fafc")


def _candidate_marker_color(target: dict[str, Any]) -> str:
    return _operation_mode_color(str(target.get("recommended_operation_mode", "detect")))


def _operation_mode_color(mode: str) -> str:
    return {
        "detect": "#9BC3D4",
        "sample": "#7EA67E",
        "drill": "#6F92B3",
    }.get(mode, "#f8fafc")


def _add_resource_risk_legend(parts: list[str], *, x: float, y: float) -> None:
    parts.append(
        f'<rect x="{x:.2f}" y="{y:.2f}" width="224" height="174" rx="5" '
        'fill="#fff2cf" opacity="0.90" stroke="#7a5a2a" stroke-width="0.8"/>'
    )
    parts.append(f'<text x="{x + 12:.2f}" y="{y + 21:.2f}" fill="#332719" font-size="12" font-weight="700">legend</text>')
    _add_colorbar(parts, x=x + 12, y=y + 35, width=126, height=10, color_at=lambda t: _resource_risk_color(t, 0.10))
    parts.append(f'<text x="{x + 145:.2f}" y="{y + 44:.2f}" fill="#332719" font-size="10">ice/resource</text>')
    _add_colorbar(parts, x=x + 12, y=y + 58, width=126, height=10, color_at=lambda t: _resource_risk_color(0.30, t))
    parts.append(f'<text x="{x + 145:.2f}" y="{y + 67:.2f}" fill="#332719" font-size="10">risk</text>')
    legend_rows = [
        ("low_time path", _path_color("low_time"), "line"),
        ("low_energy path", _path_color("low_energy"), "line"),
        ("low_risk path", _path_color("low_risk"), "line"),
        ("detect candidate", _operation_mode_color("detect"), "dot"),
        ("sample candidate", _operation_mode_color("sample"), "dot"),
        ("drill candidate", _operation_mode_color("drill"), "dot"),
    ]
    row_y = y + 91
    for label, color, kind in legend_rows:
        if kind == "line":
            parts.append(
                f'<line x1="{x + 14:.2f}" y1="{row_y - 4:.2f}" x2="{x + 43:.2f}" y2="{row_y - 4:.2f}" '
                f'stroke="{color}" stroke-width="3.0" stroke-linecap="round"/>'
            )
        else:
            parts.append(f'<circle cx="{x + 28:.2f}" cy="{row_y - 4:.2f}" r="4.2" fill="{color}" stroke="#332719" stroke-width="0.6"/>')
        parts.append(f'<text x="{x + 52:.2f}" y="{row_y:.2f}" fill="#332719" font-size="10">{_xml_escape(label)}</text>')
        row_y += 15


def _add_dem_legend(parts: list[str], *, x: float, y: float) -> None:
    parts.append(
        f'<rect x="{x:.2f}" y="{y:.2f}" width="208" height="116" rx="5" '
        'fill="#fff2cf" opacity="0.90" stroke="#7a5a2a" stroke-width="0.8"/>'
    )
    parts.append(f'<text x="{x + 12:.2f}" y="{y + 21:.2f}" fill="#332719" font-size="12" font-weight="700">DEM legend</text>')
    _add_colorbar(parts, x=x + 12, y=y + 36, width=132, height=11, color_at=_dem_color)
    parts.append(f'<text x="{x + 12:.2f}" y="{y + 62:.2f}" fill="#332719" font-size="10">low basin</text>')
    parts.append(f'<text x="{x + 103:.2f}" y="{y + 62:.2f}" fill="#332719" font-size="10">high ridge</text>')
    zone_rows = [
        ("detect candidate", _operation_mode_color("detect")),
        ("sample candidate", _operation_mode_color("sample")),
        ("drill candidate", _operation_mode_color("drill")),
    ]
    row_y = y + 83
    for label, color in zone_rows:
        parts.append(f'<circle cx="{x + 19:.2f}" cy="{row_y - 4:.2f}" r="4.2" fill="{color}" stroke="#332719" stroke-width="0.6"/>')
        parts.append(f'<text x="{x + 31:.2f}" y="{row_y:.2f}" fill="#332719" font-size="10">{_xml_escape(label)}</text>')
        row_y += 15


def _add_colorbar(parts: list[str], *, x: float, y: float, width: float, height: float, color_at: Any) -> None:
    steps = 40
    step_width = width / float(steps)
    for idx in range(steps):
        value = idx / float(steps - 1)
        parts.append(
            f'<rect x="{x + idx * step_width:.2f}" y="{y:.2f}" width="{step_width + 0.2:.2f}" '
            f'height="{height:.2f}" fill="{color_at(value)}"/>'
        )
    parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{width:.2f}" height="{height:.2f}" fill="none" stroke="#332719" stroke-width="0.5"/>')


def _star_svg(x: float, y: float, *, outer: float, inner: float, fill: str, stroke: str, stroke_width: float) -> str:
    points = []
    for idx in range(16):
        angle = -math.pi / 2.0 + idx * math.pi / 8.0
        radius = outer if idx % 2 == 0 else inner
        points.append(f"{x + radius * math.cos(angle):.2f},{y + radius * math.sin(angle):.2f}")
    return f'<polygon points="{" ".join(points)}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width:.2f}"/>'


def _add_svg_scale_bar(parts: list[str], *, size: int, pad: int, extent: float) -> None:
    bar_km = 10.0 if extent >= 40.0 else 5.0
    x0 = pad + 0.06 * (size - 2 * pad)
    y0 = size - pad - 24.0
    length = bar_km / float(extent) * (size - 2 * pad)
    parts.append(f'<line x1="{x0:.2f}" y1="{y0:.2f}" x2="{x0 + length:.2f}" y2="{y0:.2f}" stroke="#202020" stroke-width="1.8" stroke-linecap="butt"/>')
    parts.append(f'<text x="{x0 + 0.5 * length:.2f}" y="{y0 - 8.0:.2f}" fill="#111827" stroke="#fbfbf8" stroke-width="2.5" paint-order="stroke" font-size="12" text-anchor="middle">{bar_km:.0f} km</text>')


def _blend_rgb(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    u = _clamp(t)
    return (
        int(round(a[0] + (b[0] - a[0]) * u)),
        int(round(a[1] + (b[1] - a[1]) * u)),
        int(round(a[2] + (b[2] - a[2]) * u)),
    )


def _rgb_hex(color: tuple[int, int, int]) -> str:
    return f"#{max(0, min(255, color[0])):02x}{max(0, min(255, color[1])):02x}{max(0, min(255, color[2])):02x}"


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _smoothstep(value: float) -> float:
    v = _clamp(value)
    return v * v * (3.0 - 2.0 * v)


def _scale_xy(x: float, y: float, extent: float, size: int, pad: int) -> tuple[float, float]:
    sx = pad + float(x) / float(extent) * (size - 2 * pad)
    sy = pad + (1.0 - float(y) / float(extent)) * (size - 2 * pad)
    return sx, sy


def _polyline_svg(points: list[list[float]], extent: float, size: int, pad: int) -> str:
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in (_scale_xy(p[0], p[1], extent, size, pad) for p in points))


def _xml_escape(value: Any) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

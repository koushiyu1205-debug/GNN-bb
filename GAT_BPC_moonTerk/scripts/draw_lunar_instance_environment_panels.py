#!/usr/bin/env python3
"""Draw four real-data environment panels for one lunar mission instance.

The default figure overlays only task sites and the depot.  An optional
schematic-v5 mode adds the same seven typed task sites and the complete set of
low-time, low-energy, and low-risk candidate paths used by the paper figure.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, LinearSegmentedColormap, Normalize, PowerNorm
from matplotlib.lines import Line2D
import numpy as np

from lunar_ice_bpc.domain.real_maps import build_real_map_surface_context, _read_raster_window
from lunar_ice_bpc.domain.scientific_visualization import configure_scientific_style
from lunar_ice_bpc.io.instance_io import read_json


DEFAULT_INSTANCE = "data/instances/lunar_ice_sp50_020/instance_001_logical_graph.json"
DEFAULT_RAW_MAP_DIR = "data/raw_maps"
DEFAULT_OUTPUT = "output/data_figures/lunar_sp50_020_instance_001_environment_panels.png"
DEFAULT_SCHEMATIC_V5_PATH_OUTPUT = (
    "output/data_figures/"
    "lunar_sp50_020_instance_001_environment_panels_schematic_v5_paths.png"
)

SCHEMATIC_V5_TASK_IDS = (
    "ice_site_001",
    "ice_site_003",
    "ice_site_004",
    "ice_site_006",
    "ice_site_007",
    "ice_site_009",
    "ice_site_018",
)
SCHEMATIC_V5_TASK_MARKERS = {
    "detect": "o",
    "sample": "^",
    "drill": "s",
}
SCHEMATIC_V5_PATH_COLORS = {
    "low_time": "#3E78B2",
    "low_energy": "#D79A24",
    "low_risk": "#B04A7A",
}
PANEL_PATH_TYPES = {
    "elevation_m": ("low_time",),
    "illumination": ("low_energy",),
    "risk": ("low_risk",),
    "roughness": ("low_time", "low_energy", "low_risk"),
}
SCHEMATIC_V5_PANEL_TITLES = {
    "elevation_m": "DEM elevation and low-time candidate paths",
    "illumination": "Solar visibility and low-energy candidate paths",
    "risk": "Traversal risk and low-risk candidate paths",
    "roughness": "LOLA roughness and all candidate paths",
}

# Presentation-only position requested for the figure. The source instance remains unchanged.
DISPLAY_TASK_POSITION_OVERRIDES = {
    "ice_site_006": (45.0, 41.0),
}

PANEL_SPECS = (
    {
        "key": "elevation_m",
        "title": "DEM elevation",
        "cmap": "reference_lunar_terrain",
        "colorbar": "elevation (m)",
        "limits": "p01_p99",
        "gamma": 1.15,
        "display_sigma_cells": 0.60,
        "relief_strength": 0.32,
        "detail_strength": 0.04,
    },
    {
        "key": "illumination",
        "title": "Average solar visibility",
        "cmap": "reference_panel_a_visibility",
        "colorbar": "visibility index",
        "limits": (0.0, 1.0),
        "gamma": 1.08,
        "display_sigma_cells": 10.00,
        "relief_strength": 0.32,
        "detail_strength": 0.20,
    },
    {
        "key": "risk",
        "title": "Deterministic traversal risk",
        "cmap": "reference_guidance_risk",
        "colorbar": "risk index",
        "limits": (0.1, 0.9),
        "gamma": 1.0,
        "display_sigma_cells": 10.00,
        "relief_strength": 0.23,
        "detail_strength": 0.17,
    },
    {
        "key": "roughness",
        "title": "LOLA local roughness",
        "cmap": "editorial_roughness",
        "colorbar": "roughness index",
        "limits": (0.0, 1.0),
        "gamma": 1.0,
        "display_sigma_cells": 1.80,
        "relief_strength": 0.06,
        "detail_strength": 0.24,
    },
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Draw DEM, illumination, deterministic risk, and roughness from real "
            "lunar rasters with one instance's task sites and depot."
        )
    )
    parser.add_argument("--instance", default=DEFAULT_INSTANCE)
    parser.add_argument("--raw-map-dir", default=DEFAULT_RAW_MAP_DIR)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--hide-sites",
        action="store_true",
        help="omit task sites, depot, and their legend from the rendered figure",
    )
    parser.add_argument(
        "--schematic-v5-path-panels",
        action="store_true",
        help=(
            "draw the schematic-v5 depot and seven typed task sites; overlay "
            "low-time paths on DEM, low-energy paths on illumination, low-risk "
            "paths on risk, and all three path types on roughness"
        ),
    )
    parser.add_argument(
        "--output-cells",
        type=int,
        default=800,
        help="square raster sampling resolution used by the SP50 preview",
    )
    args = parser.parse_args()
    if args.hide_sites and args.schematic_v5_path_panels:
        parser.error("--hide-sites and --schematic-v5-path-panels are exclusive")

    instance_path = _project_path(args.instance)
    raw_map_dir = _project_path(args.raw_map_dir)
    output_value = args.output
    if args.schematic_v5_path_panels and output_value == DEFAULT_OUTPUT:
        output_value = DEFAULT_SCHEMATIC_V5_PATH_OUTPUT
    output_path = _project_path(output_value).with_suffix(".png")
    instance = read_json(instance_path)
    resource_map = instance.get("resource_map") or {}
    center_x_km = float(resource_map["center_x_km"])
    center_y_km = float(resource_map["center_y_km"])
    extent_km = float(resource_map["extent_km"])

    context = build_real_map_surface_context(
        raw_map_dir=raw_map_dir,
        center_x_km=center_x_km,
        center_y_km=center_y_km,
        extent_km=extent_km,
        output_cells=int(args.output_cells),
        allow_remote=False,
        allow_partial=False,
    )
    if context.get("status") != "REAL_MAP_SURFACES_READY":
        raise RuntimeError(
            "real raster surface construction failed: "
            f"status={context.get('status')} "
            f"missing={context.get('missing_required_lola_layers')}"
        )

    all_tasks = instance.get("tasks") or {}
    if args.schematic_v5_path_panels:
        missing_task_ids = [
            task_id for task_id in SCHEMATIC_V5_TASK_IDS if task_id not in all_tasks
        ]
        if missing_task_ids:
            raise KeyError(f"missing schematic-v5 task sites: {missing_task_ids}")
        tasks = [all_tasks[task_id] for task_id in SCHEMATIC_V5_TASK_IDS]
    else:
        tasks = list(all_tasks.values())
    if not tasks:
        raise ValueError("instance does not contain task sites")
    depot = instance.get("depot") or {}
    depot_xy = depot.get("xy_km")
    if not isinstance(depot_xy, list) or len(depot_xy) != 2:
        raise ValueError("instance depot does not define xy_km")
    _validate_site_coordinates(tasks, depot_xy, extent_km=extent_km)

    candidate_legs: list[tuple[str, str]] = []
    edge_lookup: dict[tuple[str, str, str], dict[str, Any]] = {}
    if args.schematic_v5_path_panels:
        node_ids = (str(depot["id"]), *SCHEMATIC_V5_TASK_IDS)
        candidate_legs = [
            (source, target)
            for source in node_ids
            for target in node_ids
            if source != target
        ]
        edge_lookup = {
            (str(edge["from"]), str(edge["to"]), str(option["path_type"])): option
            for edge in instance["logical_graph"]["edges"]
            for option in edge.get("path_options", [])
        }
        _validate_candidate_paths(edge_lookup, candidate_legs)

    surfaces = context["surfaces"]
    raw_layers = _read_raw_display_layers(
        context,
        center_x_km=center_x_km,
        center_y_km=center_y_km,
        extent_km=extent_km,
        output_cells=int(args.output_cells),
    )
    layer_values = {
        "elevation_m": np.asarray(surfaces["elevation_m"], dtype="float64"),
        "illumination": _robust_unit_index(
            raw_layers["lola_avg_solar_visibility"],
            lower_percentile=0.0,
            upper_percentile=99.5,
        ),
        "risk": np.asarray(context["risk"], dtype="float64"),
        "roughness": _robust_unit_index(
            raw_layers["lola_roughness"],
            lower_percentile=1.0,
            upper_percentile=99.0,
        ),
    }
    _validate_layer_shapes(layer_values, expected_cells=int(args.output_cells))
    hillshade = _build_hillshade(layer_values["elevation_m"], extent_km=extent_km)
    detail_texture = _build_detail_texture(
        layer_values["elevation_m"],
        extent_km=extent_km,
    )

    configure_scientific_style()
    mpl.rcParams.update(
        {
            "figure.dpi": 180,
            "savefig.dpi": 400,
            "axes.titlesize": 10.2,
            "axes.titleweight": "semibold",
            "figure.facecolor": (
                "white" if args.schematic_v5_path_panels else "#fbfbfa"
            ),
            "axes.facecolor": "#fbfbfa",
        }
    )
    fig, axes = plt.subplots(
        2,
        2,
        figsize=(10.8, 8.6 if args.schematic_v5_path_panels else 8.8),
        constrained_layout=True,
        sharex=True,
        sharey=True,
        facecolor="white" if args.schematic_v5_path_panels else "#fbfbfa",
    )
    if args.schematic_v5_path_panels:
        fig.set_constrained_layout_pads(
            w_pad=0.0,
            h_pad=0.025,
            wspace=-0.04,
            hspace=0.02,
        )
    extent = (0.0, extent_km, 0.0, extent_km)
    for panel_index, (ax, spec) in enumerate(zip(axes.flat, PANEL_SPECS)):
        display_values = _gaussian_smooth(
            layer_values[spec["key"]],
            sigma_cells=float(spec["display_sigma_cells"]),
        )
        matrix = np.flipud(np.ma.masked_invalid(display_values))
        cmap = _resolve_colormap(str(spec["cmap"]))
        norm = _build_norm(
            display_values,
            limits=spec["limits"],
            gamma=float(spec["gamma"]),
        )
        rgba = cmap(norm(matrix.filled(np.nan)))
        rgba = _apply_relief_shading(
            rgba,
            hillshade,
            valid_mask=~np.ma.getmaskarray(matrix),
            strength=float(spec["relief_strength"]),
        )
        rgba = _apply_detail_texture(
            rgba,
            detail_texture,
            valid_mask=~np.ma.getmaskarray(matrix),
            strength=float(spec["detail_strength"]),
        )
        image = ax.imshow(
            rgba,
            extent=extent,
            origin="lower",
            interpolation="lanczos",
            resample=True,
            zorder=0,
        )
        if args.schematic_v5_path_panels:
            _overlay_candidate_paths(
                ax,
                edge_lookup=edge_lookup,
                candidate_legs=candidate_legs,
                path_types=PANEL_PATH_TYPES[str(spec["key"])],
                extent_km=extent_km,
            )
            _overlay_schematic_v5_sites(ax, tasks, depot_xy)
        elif not args.hide_sites:
            _overlay_sites(ax, tasks, depot_xy)
        panel_title = (
            SCHEMATIC_V5_PANEL_TITLES[str(spec["key"])]
            if args.schematic_v5_path_panels
            else str(spec["title"])
        )
        if args.schematic_v5_path_panels:
            panel_letter = chr(ord("a") + panel_index)
            caption_y = -0.105 if panel_index < 2 else -0.175
            ax.set_title("")
            ax.text(
                0.5,
                caption_y,
                f"({panel_letter}) {panel_title}",
                transform=ax.transAxes,
                ha="center",
                va="top",
                fontsize=9.2,
                fontweight="semibold",
                color="#11181D",
                clip_on=False,
            )
        else:
            letter = chr(ord("A") + panel_index)
            ax.set_title(f"{letter}   {panel_title}", loc="left")
        ax.set_xlim(0.0, extent_km)
        ax.set_ylim(0.0, extent_km)
        ax.set_aspect("equal")
        coordinate_ticks = np.linspace(0.0, extent_km, 6)
        ax.set_xticks(coordinate_ticks)
        ax.set_yticks(coordinate_ticks)
        ax.tick_params(axis="both", labelbottom=True, labelleft=True)
        ax.grid(color="white", alpha=0.08, linewidth=0.38)
        scalar_mappable = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
        scalar_mappable.set_array([])
        colorbar = fig.colorbar(
            scalar_mappable,
            ax=ax,
            fraction=0.032 if args.schematic_v5_path_panels else 0.036,
            pad=0.012 if args.schematic_v5_path_panels else 0.022,
            aspect=30,
            shrink=0.96,
        )
        colorbar.set_label(spec["colorbar"])

    for ax in axes[1, :]:
        ax.set_xlabel("east-west distance (km)")
    for ax in axes[:, 0]:
        ax.set_ylabel("south-north distance (km)")
    if args.schematic_v5_path_panels:
        fig.legend(
            handles=_build_schematic_v5_legend_handles(),
            loc="lower center",
            bbox_to_anchor=(0.5, -0.040),
            ncol=7,
            fontsize=8.0,
            columnspacing=1.25,
            handlelength=2.6,
            frameon=True,
            framealpha=0.94,
            edgecolor="#d5d5d2",
        )
    elif not args.hide_sites:
        fig.legend(
            handles=[
                Line2D(
                    [0],
                    [0],
                    marker="o",
                    linestyle="none",
                    markerfacecolor="#ffe45e",
                    markeredgecolor="black",
                    markeredgewidth=0.8,
                    markersize=7.6,
                    label=f"task sites (n={len(tasks)})",
                ),
                Line2D(
                    [0],
                    [0],
                    marker="*",
                    linestyle="none",
                    markerfacecolor="#43d9c0",
                    markeredgecolor="black",
                    markeredgewidth=0.9,
                    markersize=13.5,
                    label="depot",
                ),
            ],
            loc="upper center",
            bbox_to_anchor=(0.5, 1.055),
            ncol=2,
            frameon=True,
            framealpha=0.90,
            edgecolor="#d5d5d2",
        )
    instance_id = str(instance.get("instance_id", instance_path.stem))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        output_path,
        bbox_inches="tight",
        facecolor="white" if args.schematic_v5_path_panels else fig.get_facecolor(),
        transparent=False,
        metadata={
            "Title": f"Real-raster environment panels for {instance_id}",
            "Description": (
                f"Instance={instance_path.relative_to(ROOT)}; "
                f"raw_maps={raw_map_dir.relative_to(ROOT)}; "
                "layers=DEM, average solar visibility, deterministic traversal risk, "
                "LOLA roughness; editorial presentation-first smoothing and restrained relief; "
                "overlays="
                + (
                    "schematic-v5 depot, seven typed task sites, and complete "
                    "candidate-path graph by path type"
                    if args.schematic_v5_path_panels
                    else "none"
                    if args.hide_sites
                    else "task sites and depot only"
                )
                + "; "
                + (
                    "candidate paths are illustrative model inputs, not a solution route."
                    if args.schematic_v5_path_panels
                    else "no graph or route lines."
                )
            ),
            "Software": "lunar-ice-bpc deterministic Matplotlib renderer",
        },
    )
    plt.close(fig)

    print(f"wrote {output_path}")
    print(f"instance_id={instance_id} task_count={len(tasks)} depot_xy_km={depot_xy}")
    print(
        "roi_center_km=({:.3f},{:.3f}) extent_km={:.1f} cells={}".format(
            center_x_km,
            center_y_km,
            extent_km,
            int(args.output_cells),
        )
    )
    for spec in PANEL_SPECS:
        values = layer_values[spec["key"]]
        finite = values[np.isfinite(values)]
        print(
            "{} source_range=[{:.6g},{:.6g}] cmap={}".format(
                spec["key"],
                float(np.min(finite)),
                float(np.max(finite)),
                spec["cmap"],
            )
        )
    return 0


def _read_raw_display_layers(
    context: dict[str, Any],
    *,
    center_x_km: float,
    center_y_km: float,
    extent_km: float,
    output_cells: int,
) -> dict[str, np.ndarray]:
    """Read the two raw rasters whose normalized context copies clip visible tails."""
    import rasterio

    arrays: dict[str, np.ndarray] = {}
    for layer_key in ("lola_avg_solar_visibility", "lola_roughness"):
        status = (context.get("layer_status") or {}).get(layer_key) or {}
        if status.get("status") != "ready" or not status.get("source"):
            raise RuntimeError(f"raw display layer is unavailable: {layer_key}")
        array, _meta = _read_raster_window(
            rasterio=rasterio,
            np=np,
            source_path=status["source"],
            layer_key=layer_key,
            center_x_km=center_x_km,
            center_y_km=center_y_km,
            extent_km=extent_km,
            output_cells=output_cells,
        )
        arrays[layer_key] = np.asarray(array, dtype="float64")
    return arrays


def _robust_unit_index(
    values: np.ndarray,
    *,
    lower_percentile: float,
    upper_percentile: float,
) -> np.ndarray:
    """Build a continuous display index while clipping only the extreme tails."""
    matrix = np.asarray(values, dtype="float64")
    finite = matrix[np.isfinite(matrix)]
    if finite.size == 0:
        raise ValueError("cannot normalize a raster without finite values")
    low = float(np.percentile(finite, lower_percentile))
    high = float(np.percentile(finite, upper_percentile))
    if high <= low + 1.0e-12:
        raise ValueError(f"degenerate display range: low={low} high={high}")
    return np.clip((matrix - low) / (high - low), 0.0, 1.0)


def _resolve_colormap(name: str) -> mpl.colors.Colormap:
    if name == "reference_lunar_terrain":
        return LinearSegmentedColormap.from_list(
            name,
            (
                (0.00, "#27205e"),
                (0.09, "#1b4f91"),
                (0.22, "#238bb4"),
                (0.36, "#49a88e"),
                (0.50, "#83b582"),
                (0.62, "#bdc487"),
                (0.72, "#d8d27d"),
                (0.82, "#e7cf82"),
                (0.91, "#efdfad"),
                (1.00, "#f5f1e7"),
            ),
            N=1024,
        )
    if name == "reference_panel_a_visibility":
        return LinearSegmentedColormap.from_list(
            name,
            (
                "#153a55",
                "#2d617a",
                "#588594",
                "#86a3a3",
                "#adb9aa",
                "#ccc9ae",
                "#ddd2b9",
                "#eee7d8",
            ),
            N=1024,
        )
    if name == "reference_guidance_risk":
        return LinearSegmentedColormap.from_list(
            name,
            (
                "#251f4e",
                "#38226c",
                "#5a2878",
                "#7c3375",
                "#a84470",
                "#ce5c6c",
                "#e87f68",
                "#ecaa72",
                "#ecd692",
                "#f0e8c4",
            ),
            N=1024,
        )
    if name == "editorial_dem":
        return LinearSegmentedColormap.from_list(
            name,
            (
                "#153954",
                "#2d6684",
                "#5f929f",
                "#98b3ae",
                "#c9c9ad",
                "#dfc8ad",
                "#f3eee5",
            ),
            N=512,
        )
    if name == "editorial_roughness":
        return LinearSegmentedColormap.from_list(
            name,
            (
                "#f4f1eb",
                "#ddd8cf",
                "#b7b0a6",
                "#8a8279",
                "#5c5650",
                "#292725",
            ),
            N=512,
        )
    if name == "editorial_illumination":
        return LinearSegmentedColormap.from_list(
            name,
            (
                "#17374e",
                "#345f73",
                "#718f94",
                "#adb6a7",
                "#d9d1b5",
                "#f3edda",
            ),
            N=512,
        )
    if name == "editorial_risk":
        return LinearSegmentedColormap.from_list(
            name,
            (
                "#215b4f",
                "#3f7f59",
                "#6da064",
                "#a6bb6b",
                "#d3ca70",
                "#e5b661",
                "#da8a50",
                "#bd6448",
            ),
            N=512,
        )
    return mpl.colormaps.get_cmap(name)


def _build_norm(
    values: np.ndarray,
    *,
    limits: tuple[float, float] | str,
    gamma: float,
) -> Normalize:
    finite = np.asarray(values, dtype="float64")
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        raise ValueError("cannot build a color normalization without finite values")
    if limits == "p01_p99":
        vmin, vmax = (float(item) for item in np.percentile(finite, (1.0, 99.0)))
    else:
        vmin, vmax = float(limits[0]), float(limits[1])
    if gamma == 1.0:
        return Normalize(vmin=vmin, vmax=vmax, clip=True)
    return PowerNorm(gamma=gamma, vmin=vmin, vmax=vmax, clip=True)


def _build_hillshade(elevation_m: np.ndarray, *, extent_km: float) -> np.ndarray:
    display_elevation = np.flipud(
        _gaussian_smooth(np.asarray(elevation_m, dtype="float64"), sigma_cells=2.00)
    )
    cell_size_m = extent_km * 1000.0 / float(display_elevation.shape[0])
    return LightSource(azdeg=315.0, altdeg=46.0).hillshade(
        display_elevation,
        vert_exag=0.35,
        dx=cell_size_m,
        dy=cell_size_m,
    )


def _build_detail_texture(elevation_m: np.ndarray, *, extent_km: float) -> np.ndarray:
    """Extract crisp, high-frequency lunar relief without changing panel colors."""
    display_elevation = np.flipud(
        _gaussian_smooth(np.asarray(elevation_m, dtype="float64"), sigma_cells=0.45)
    )
    cell_size_m = extent_km * 1000.0 / float(display_elevation.shape[0])
    sharp_shade = LightSource(azdeg=315.0, altdeg=32.0).hillshade(
        display_elevation,
        vert_exag=0.90,
        dx=cell_size_m,
        dy=cell_size_m,
    )
    local_relief = sharp_shade - _gaussian_smooth(sharp_shade, sigma_cells=5.0)
    finite = np.abs(local_relief[np.isfinite(local_relief)])
    if finite.size == 0:
        return np.zeros_like(local_relief)
    scale = float(np.percentile(finite, 98.5))
    if scale <= 1.0e-12:
        return np.zeros_like(local_relief)
    return np.clip(local_relief / scale, -1.0, 1.0)


def _apply_relief_shading(
    rgba: np.ndarray,
    hillshade: np.ndarray,
    *,
    valid_mask: np.ndarray,
    strength: float,
) -> np.ndarray:
    shaded = np.asarray(rgba, dtype="float64").copy()
    relief = 2.0 * np.asarray(hillshade, dtype="float64") - 1.0
    factor = 1.0 + strength * relief
    shaded[..., :3] = np.clip(shaded[..., :3] * factor[..., None], 0.0, 1.0)
    shaded[..., 3] = np.where(valid_mask, 1.0, 0.0)
    return shaded


def _apply_detail_texture(
    rgba: np.ndarray,
    detail_texture: np.ndarray,
    *,
    valid_mask: np.ndarray,
    strength: float,
) -> np.ndarray:
    textured = np.asarray(rgba, dtype="float64").copy()
    factor = 1.0 + strength * np.asarray(detail_texture, dtype="float64")
    textured[..., :3] = np.clip(textured[..., :3] * factor[..., None], 0.0, 1.0)
    textured[..., 3] = np.where(valid_mask, 1.0, 0.0)
    return textured


def _gaussian_smooth(values: np.ndarray, *, sigma_cells: float) -> np.ndarray:
    matrix = np.asarray(values, dtype="float64")
    if sigma_cells <= 0.0:
        return matrix.copy()
    radius = max(1, int(np.ceil(3.0 * sigma_cells)))
    offsets = np.arange(-radius, radius + 1, dtype="float64")
    kernel = np.exp(-0.5 * np.square(offsets / sigma_cells))
    kernel /= np.sum(kernel)
    finite = np.isfinite(matrix)
    numerator = np.where(finite, matrix, 0.0)
    denominator = finite.astype("float64")
    for axis in (0, 1):
        numerator = _convolve_reflect(numerator, kernel, axis=axis)
        denominator = _convolve_reflect(denominator, kernel, axis=axis)
    return np.divide(
        numerator,
        denominator,
        out=np.full_like(numerator, np.nan),
        where=denominator > 1.0e-12,
    )


def _convolve_reflect(values: np.ndarray, kernel: np.ndarray, *, axis: int) -> np.ndarray:
    radius = int(kernel.size // 2)
    padding = [(0, 0)] * values.ndim
    padding[axis] = (radius, radius)
    padded = np.pad(values, padding, mode="reflect")
    windows = np.lib.stride_tricks.sliding_window_view(padded, kernel.size, axis=axis)
    return np.tensordot(windows, kernel, axes=([-1], [0]))


def _project_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def _validate_site_coordinates(
    tasks: list[dict[str, Any]],
    depot_xy: list[Any],
    *,
    extent_km: float,
) -> None:
    coordinates = [("depot", depot_xy)] + [
        (str(task.get("id", "task")), task.get("xy_km")) for task in tasks
    ]
    for site_id, xy in coordinates:
        if not isinstance(xy, list) or len(xy) != 2:
            raise ValueError(f"site {site_id} does not define xy_km")
        x, y = float(xy[0]), float(xy[1])
        if not (0.0 <= x <= extent_km and 0.0 <= y <= extent_km):
            raise ValueError(f"site {site_id} lies outside the {extent_km:g} km ROI: {xy}")


def _validate_layer_shapes(
    layers: dict[str, np.ndarray],
    *,
    expected_cells: int,
) -> None:
    expected_shape = (expected_cells, expected_cells)
    for key, matrix in layers.items():
        if matrix.shape != expected_shape:
            raise ValueError(f"layer {key} has shape {matrix.shape}, expected {expected_shape}")
        if not np.isfinite(matrix).any():
            raise ValueError(f"layer {key} contains no finite values")


def _validate_candidate_paths(
    edge_lookup: dict[tuple[str, str, str], dict[str, Any]],
    candidate_legs: list[tuple[str, str]],
) -> None:
    node_ids = {
        node_id for source, target in candidate_legs for node_id in (source, target)
    }
    expected_leg_count = len(node_ids) * (len(node_ids) - 1)
    if len(candidate_legs) != expected_leg_count:
        raise ValueError(
            f"expected {expected_leg_count} directed candidate legs, "
            f"found {len(candidate_legs)}"
        )
    missing = [
        (source, target, path_type)
        for source, target in candidate_legs
        for path_type in SCHEMATIC_V5_PATH_COLORS
        if (source, target, path_type) not in edge_lookup
    ]
    if missing:
        raise KeyError(f"candidate-path options are missing: {missing[:8]}")


def _overlay_candidate_paths(
    ax: plt.Axes,
    *,
    edge_lookup: dict[tuple[str, str, str], dict[str, Any]],
    candidate_legs: list[tuple[str, str]],
    path_types: tuple[str, ...],
    extent_km: float,
) -> None:
    combined_panel = len(path_types) > 1
    for source, target in candidate_legs:
        for path_type in path_types:
            option = edge_lookup[(source, target, path_type)]
            points = _stylize_candidate_path(
                np.asarray(option["path_xy"], dtype="float64"),
                path_type=path_type,
                source=source,
                target=target,
                extent_km=extent_km,
            )
            ax.plot(
                points[:, 0],
                points[:, 1],
                color=SCHEMATIC_V5_PATH_COLORS[path_type],
                linewidth=1.44 if combined_panel else 1.64,
                alpha=0.34 if combined_panel else 0.52,
                solid_capstyle="round",
                zorder=3.8,
            )


def _stylize_candidate_path(
    raw_points: np.ndarray,
    *,
    path_type: str,
    source: str,
    target: str,
    extent_km: float,
) -> np.ndarray:
    """Enhance existing path curvature while preserving its two endpoints."""
    points = np.asarray(raw_points, dtype="float64")
    if points.ndim != 2 or points.shape[0] < 2 or points.shape[1] != 2:
        raise ValueError("candidate path must be an n-by-2 polyline")
    segment_lengths = np.linalg.norm(np.diff(points, axis=0), axis=1)
    cumulative = np.concatenate(([0.0], np.cumsum(segment_lengths)))
    total_length = float(cumulative[-1])
    if total_length <= 1.0e-12:
        return points.copy()
    parameter = cumulative / total_length
    start = points[0]
    end = points[-1]
    delta = end - start
    direct_length = float(np.linalg.norm(delta))
    if direct_length <= 1.0e-12:
        return points.copy()

    baseline = (1.0 - parameter[:, None]) * start + parameter[:, None] * end
    normal = np.asarray((-delta[1], delta[0]), dtype="float64") / direct_length
    amplitude_by_type = {
        "low_time": 0.55,
        "low_energy": 0.90,
        "low_risk": 1.25,
    }
    cycles_by_type = {
        "low_time": 1.20,
        "low_energy": 1.75,
        "low_risk": 2.30,
    }
    amplitude = min(
        amplitude_by_type[path_type],
        max(0.18, 0.055 * direct_length),
    )
    path_key = f"{source}>{target}"
    path_seed = sum(
        (index + 1) * ord(character)
        for index, character in enumerate(path_key)
    )
    amplitude *= 0.88 + 0.08 * float(path_seed % 4)
    direction_sign = -1.0 if path_seed % 2 else 1.0
    phase = 0.42 * float(path_seed % 5)
    envelope = np.power(np.sin(np.pi * parameter), 1.15)
    wave = np.sin(2.0 * np.pi * cycles_by_type[path_type] * parameter + phase)
    lateral_offset = direction_sign * amplitude * envelope * (0.40 + 0.60 * wave)
    if source == "depot" and target == "ice_site_009":
        lateral_offset += {
            "low_time": -1.60,
            "low_energy": 0.00,
            "low_risk": 1.60,
        }[path_type] * envelope
    elif source == "ice_site_009" and target == "depot":
        lateral_offset += {
            "low_time": -3.20,
            "low_energy": -4.00,
            "low_risk": -4.80,
        }[path_type] * envelope
    styled = baseline + 1.35 * (points - baseline)
    styled += lateral_offset[:, None] * normal
    styled[0] = start
    styled[-1] = end
    return np.clip(styled, 0.0, float(extent_km))


def _overlay_schematic_v5_sites(
    ax: plt.Axes,
    tasks: list[dict[str, Any]],
    depot_xy: list[Any],
) -> None:
    for operation_mode, marker in SCHEMATIC_V5_TASK_MARKERS.items():
        mode_tasks = [
            task
            for task in tasks
            if str(task.get("operation_mode", "")) == operation_mode
        ]
        if not mode_tasks:
            continue
        ax.scatter(
            [float(task["xy_km"][0]) for task in mode_tasks],
            [float(task["xy_km"][1]) for task in mode_tasks],
            s=96,
            c="#FFE16A",
            edgecolors="#11181D",
            linewidths=0.95,
            marker=marker,
            zorder=5.5,
        )
    ax.scatter(
        [float(depot_xy[0])],
        [float(depot_xy[1])],
        s=384,
        c="white",
        edgecolors="#11181D",
        linewidths=1.25,
        marker="*",
        zorder=6,
    )


def _build_schematic_v5_legend_handles() -> list[Line2D]:
    handles = [
        Line2D(
            [0],
            [0],
            color=SCHEMATIC_V5_PATH_COLORS[path_type],
            linewidth=3.6,
            label=label,
        )
        for path_type, label in (
            ("low_time", "low-time candidate path"),
            ("low_energy", "low-energy candidate path"),
            ("low_risk", "low-risk candidate path"),
        )
    ]
    handles.extend(
        Line2D(
            [0],
            [0],
            marker=marker,
            linestyle="none",
            markerfacecolor="#FFE16A",
            markeredgecolor="#11181D",
            markeredgewidth=0.8,
            markersize=7.2,
            label=label,
        )
        for marker, label in (("o", "detection"), ("^", "sampling"), ("s", "drilling"))
    )
    handles.append(
        Line2D(
            [0],
            [0],
            marker="*",
            linestyle="none",
            markerfacecolor="white",
            markeredgecolor="#11181D",
            markeredgewidth=0.9,
            markersize=10.0,
            label="depot",
        )
    )
    return handles


def _overlay_sites(
    ax: plt.Axes,
    tasks: list[dict[str, Any]],
    depot_xy: list[Any],
) -> None:
    task_coordinates = [
        DISPLAY_TASK_POSITION_OVERRIDES.get(
            str(task.get("id", "")),
            (float(task["xy_km"][0]), float(task["xy_km"][1])),
        )
        for task in tasks
    ]
    ax.scatter(
        [coordinate[0] for coordinate in task_coordinates],
        [coordinate[1] for coordinate in task_coordinates],
        s=52,
        c="#ffe45e",
        edgecolors="black",
        linewidths=0.82,
        marker="o",
        zorder=5,
    )
    ax.scatter(
        [float(depot_xy[0])],
        [float(depot_xy[1])],
        s=210,
        c="#43d9c0",
        edgecolors="black",
        linewidths=1.05,
        marker="*",
        zorder=6,
    )


def _add_scale_bar(ax: plt.Axes, *, extent_km: float) -> None:
    length_km = 5.0
    x0 = 0.075 * extent_km
    y0 = 0.075 * extent_km
    ax.plot(
        [x0, x0 + length_km],
        [y0, y0],
        color="white",
        linewidth=3.0,
        solid_capstyle="butt",
        zorder=7,
    )
    ax.plot(
        [x0, x0 + length_km],
        [y0, y0],
        color="black",
        linewidth=1.0,
        solid_capstyle="butt",
        zorder=8,
    )
    ax.text(
        x0 + length_km / 2.0,
        y0 + 0.35,
        "5 km",
        ha="center",
        va="bottom",
        fontsize=8,
        color="black",
        bbox={"facecolor": "white", "alpha": 0.76, "edgecolor": "none", "pad": 1.2},
        zorder=9,
    )


if __name__ == "__main__":
    raise SystemExit(main())

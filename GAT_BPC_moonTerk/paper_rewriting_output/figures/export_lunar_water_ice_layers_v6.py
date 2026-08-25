#!/usr/bin/env python3
"""Export every pseudo-3D lunar layer as an aligned transparent PNG."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Callable


ROOT = Path(__file__).resolve().parents[2]
FIGURE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = FIGURE_DIR / "lunar_water_ice_layers_v6"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(FIGURE_DIR))

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

import draw_lunar_water_ice_exploration_schematic_v5 as v5
import draw_lunar_water_ice_exploration_schematic_v6 as v6
from draw_lunar_real_environment_task_sites import _build_official_lola_hillshade_rgb
from lunar_ice_bpc.domain.scientific_visualization import configure_scientific_style
from lunar_ice_bpc.io.instance_io import read_json


CANVAS_SIZE_IN = (12.8, 8.8)
OUTPUT_DPI = 300

LAYER_FILES = {
    "regional": OUTPUT_DIR / "layer01_regional_context_200km.png",
    "guides": OUTPUT_DIR / "layer01b_registration_guides.png",
    "terrain": OUTPUT_DIR / "layer02_local_terrain_50km.png",
    "risk": OUTPUT_DIR / "layer03_traversal_risk.png",
    "illumination": OUTPUT_DIR / "layer04_illumination.png",
    "routes": OUTPUT_DIR / "layer05_logical_routes.png",
    "routes_blank": OUTPUT_DIR / "layer05_logical_routes_blank.png",
}
PREVIEW_PATH = OUTPUT_DIR / "stack_preview.png"


def main() -> int:
    instance = read_json(v6.INSTANCE_PATH)
    resource_map = instance["resource_map"]
    center_x_km = float(resource_map["center_x_km"])
    center_y_km = float(resource_map["center_y_km"])

    local_context = v6._build_context(
        center_x_km=center_x_km,
        center_y_km=center_y_km,
        extent_km=v6.LOCAL_EXTENT_KM,
        output_cells=800,
    )
    regional_context = v6._build_context(
        center_x_km=center_x_km,
        center_y_km=center_y_km,
        extent_km=v6.REGIONAL_EXTENT_KM,
        output_cells=1000,
    )
    regional_rgba = _build_official_lola_hillshade_rgb(
        official_hillshade=np.asarray(
            regional_context["surfaces"]["hillshade"],
            dtype="float64",
        )
    )
    local_rgba, _mappables = v5._build_environment_layers(
        local_context,
        center_x_km=center_x_km,
        center_y_km=center_y_km,
        extent_km=v6.LOCAL_EXTENT_KM,
    )

    edge_lookup = {
        (str(edge["from"]), str(edge["to"]), str(option["path_type"])): option
        for edge in instance["logical_graph"]["edges"]
        for option in edge.get("path_options", [])
    }
    trips = [
        v5._resolve_trip(instance, edge_lookup, spec)
        for spec in v5.ROUTE_TRIP_SPECS
    ]
    v5._validate_candidate_edge(edge_lookup)
    selected_task_ids = {
        task_id
        for trip in trips
        for task_id in trip["task_ids"]
    }
    display_instance, display_edge_lookup, display_trips = v6._build_enlarged_route_inputs(
        instance=instance,
        edge_lookup=edge_lookup,
        trips=trips,
    )

    v5.LAYER_Z.clear()
    v5.LAYER_Z.update(
        {
            "terrain": v6.LAYER_Z["terrain"],
            "risk": v6.LAYER_Z["risk"],
            "illumination": v6.LAYER_Z["illumination"],
            "routes": v6.LAYER_Z["routes"],
        }
    )

    configure_scientific_style()
    mpl.rcParams.update(
        {
            "figure.dpi": 180,
            "savefig.dpi": OUTPUT_DPI,
            "font.family": "DejaVu Sans",
            "figure.facecolor": "none",
            "axes.facecolor": "none",
        }
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    _render_layer(
        LAYER_FILES["regional"],
        lambda ax: _draw_regional_layer(ax, regional_rgba),
        title="Layer 1: 200 km regional LOLA context",
    )
    _render_layer(
        LAYER_FILES["guides"],
        _draw_guides_layer,
        title="Registration guides between regional and enlarged local layers",
    )
    _render_layer(
        LAYER_FILES["terrain"],
        lambda ax: v6._plot_local_plane(
            ax,
            local_rgba["terrain"],
            z=v6.LAYER_Z["terrain"],
        ),
        title="Layer 2: 50 km local terrain",
    )
    _render_layer(
        LAYER_FILES["risk"],
        lambda ax: v6._plot_local_plane(
            ax,
            local_rgba["risk"],
            z=v6.LAYER_Z["risk"],
        ),
        title="Layer 3: deterministic traversal risk",
    )
    _render_layer(
        LAYER_FILES["illumination"],
        lambda ax: v6._plot_local_plane(
            ax,
            local_rgba["illumination"],
            z=v6.LAYER_Z["illumination"],
        ),
        title="Layer 4: average solar visibility",
    )
    _render_layer(
        LAYER_FILES["routes_blank"],
        _draw_blank_route_layer,
        title="Layer 5: blank logical-route drawing plane",
    )
    _render_layer(
        LAYER_FILES["routes"],
        lambda ax: _draw_route_layer(
            ax,
            instance=display_instance,
            edge_lookup=display_edge_lookup,
            trips=display_trips,
            selected_task_ids=selected_task_ids,
        ),
        title="Layer 5: sparse logical routes",
    )

    _build_preview()
    _validate_outputs()

    print(f"output_dir={OUTPUT_DIR}")
    for key in ("regional", "guides", "terrain", "risk", "illumination", "routes", "routes_blank"):
        print(f"{key}={LAYER_FILES[key]}")
    print(f"preview={PREVIEW_PATH}")
    print("stack_order=regional,guides,terrain,risk,illumination,routes")
    return 0


def _render_layer(
    output_path: Path,
    draw: Callable[[plt.Axes], None],
    *,
    title: str,
) -> None:
    fig = plt.figure(figsize=CANVAS_SIZE_IN, facecolor=(1.0, 1.0, 1.0, 0.0))
    ax = fig.add_axes(
        (0.0, 0.0, 1.0, 1.0),
        projection="3d",
        computed_zorder=False,
    )
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    draw(ax)
    _format_export_axis(ax)
    fig.savefig(
        output_path,
        dpi=OUTPUT_DPI,
        transparent=True,
        facecolor=(1.0, 1.0, 1.0, 0.0),
        edgecolor="none",
        metadata={
            "Title": title,
            "Description": (
                "Aligned transparent component for the regional-to-local pseudo-3D "
                "lunar planning stack; same canvas, projection, scale, and camera as "
                "the other exported components; no title or legend baked into pixels."
            ),
            "Software": "lunar-ice-bpc deterministic Matplotlib 3D layer exporter",
        },
    )
    plt.close(fig)


def _draw_regional_layer(ax: plt.Axes, regional_rgba: np.ndarray) -> None:
    v6._draw_regional_plane(
        ax,
        regional_rgba,
        z=v6.LAYER_Z["regional"],
    )


def _draw_guides_layer(ax: plt.Axes) -> None:
    v6._draw_regional_to_local_guides(ax)
    for x, y in (
        (v6.LOCAL_DISPLAY_MIN_KM, v6.LOCAL_DISPLAY_MIN_KM),
        (v6.LOCAL_DISPLAY_MAX_KM, v6.LOCAL_DISPLAY_MIN_KM),
        (v6.LOCAL_DISPLAY_MAX_KM, v6.LOCAL_DISPLAY_MAX_KM),
        (v6.LOCAL_DISPLAY_MIN_KM, v6.LOCAL_DISPLAY_MAX_KM),
    ):
        ax.plot(
            [x, x],
            [y, y],
            [v6.LAYER_Z["terrain"], v6.LAYER_Z["routes"]],
            color="#7C868C",
            linewidth=0.65,
            linestyle=(0, (1.5, 3.0)),
            alpha=0.55,
            zorder=1.6,
        )


def _draw_route_layer(
    ax: plt.Axes,
    *,
    instance: dict,
    edge_lookup: dict,
    trips: list[dict],
    selected_task_ids: set[str],
) -> None:
    route_rgba = np.ones((120, 120, 4), dtype="float64")
    route_rgba[..., :3] = np.asarray((0.90, 0.93, 0.94), dtype="float64")
    route_rgba[..., 3] = 0.55
    v6._plot_local_plane(
        ax,
        route_rgba,
        z=v6.LAYER_Z["routes"],
    )
    v5._draw_route_layer(
        ax,
        instance=instance,
        edge_lookup=edge_lookup,
        trips=trips,
        selected_task_ids=selected_task_ids,
    )


def _draw_blank_route_layer(ax: plt.Axes) -> None:
    route_rgba = np.ones((120, 120, 4), dtype="float64")
    route_rgba[..., :3] = np.asarray((0.90, 0.93, 0.94), dtype="float64")
    route_rgba[..., 3] = 0.55
    v6._plot_local_plane(
        ax,
        route_rgba,
        z=v6.LAYER_Z["routes"],
    )


def _format_export_axis(ax: plt.Axes) -> None:
    ax.set_xlim(v6.REGIONAL_MIN_KM - 4.0, v6.REGIONAL_MAX_KM + 4.0)
    ax.set_ylim(v6.REGIONAL_MIN_KM - 4.0, v6.REGIONAL_MAX_KM + 4.0)
    ax.set_zlim(-2.0, v6.LAYER_Z["routes"] + 12.0)
    ax.set_box_aspect((1.08, 1.08, 0.62))
    ax.view_init(elev=28.0, azim=-57.0)
    ax.set_proj_type("persp", focal_length=0.90)
    ax.set_axis_off()


def _build_preview() -> None:
    order = ("regional", "guides", "terrain", "risk", "illumination", "routes")
    layers = [Image.open(LAYER_FILES[key]).convert("RGBA") for key in order]
    try:
        size = layers[0].size
        if any(layer.size != size for layer in layers):
            raise ValueError("exported layers do not share one canvas size")
        composite = Image.new("RGBA", size, (255, 255, 255, 255))
        for layer in layers:
            composite.alpha_composite(layer)
        composite.convert("RGB").save(PREVIEW_PATH, dpi=(OUTPUT_DPI, OUTPUT_DPI))
    finally:
        for layer in layers:
            layer.close()


def _validate_outputs() -> None:
    expected_size = (
        int(round(CANVAS_SIZE_IN[0] * OUTPUT_DPI)),
        int(round(CANVAS_SIZE_IN[1] * OUTPUT_DPI)),
    )
    for key, path in LAYER_FILES.items():
        with Image.open(path) as image:
            if image.mode != "RGBA":
                raise ValueError(f"{key} is not RGBA: mode={image.mode}")
            if image.size != expected_size:
                raise ValueError(
                    f"{key} has unexpected size {image.size}; expected {expected_size}"
                )
            alpha = np.asarray(image.getchannel("A"), dtype="uint8")
            if int(alpha[0, 0]) != 0:
                raise ValueError(f"{key} does not have a transparent canvas corner")
            nonzero = int(np.count_nonzero(alpha))
            if nonzero == 0:
                raise ValueError(f"{key} contains no visible pixels")
            print(
                f"validated {key}: size={image.size} mode={image.mode} "
                f"visible_alpha_pixels={nonzero}"
            )


if __name__ == "__main__":
    raise SystemExit(main())
